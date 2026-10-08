"""Build a bounded displacement replay of a saved expanded S4 web/plate case.

This is an energy-parity diagnostic, not a native line-connection reference.
FRD exterior-node displacements are rounded; incompatible modes re-equilibrate.
"""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from math import isfinite, ulp
from pathlib import Path
import re

from scripts.b3_e4_f03_ccx_matched_t_reference import _frd_fields, build_bundle


_ENERGY_HEADER = re.compile(
    r"^\s*internal energy \(element, energy\) for set (PLATE|WEB) "
    r"and time\s+([0-9.E+-]+)\s*$", re.I,
)


def element_energies(dat: str) -> dict[int, float]:
    if type(dat) is not str or len(dat) > 8 * 1024 * 1024:
        raise ValueError("bounded CalculiX DAT required")
    lines = dat.splitlines()
    result = {}
    blocks = set()
    times = set()
    for i, line in enumerate(lines):
        match = _ENERGY_HEADER.match(line)
        if not match:
            continue
        name = match.group(1).lower()
        if name in blocks:
            raise ValueError("repeated energy block")
        blocks.add(name)
        time = float(match.group(2))
        if not isfinite(time):
            raise ValueError("nonfinite energy output time")
        times.add(time)
        expected = range(1, 17) if name == "plate" else range(17, 33)
        rows = {}
        for candidate in lines[i + 1:]:
            parts = candidate.split()
            if len(parts) == 2 and parts[0].isdigit():
                number = int(parts[0])
                value = float(parts[1].replace("D", "E"))
                if (number in rows or number not in expected or
                        not isfinite(value) or value < 0):
                    raise ValueError("invalid energy row")
                rows[number] = value
            elif rows:
                break
        if set(rows) != set(expected):
            raise ValueError("incomplete energy block")
        result.update(rows)
    if blocks != {"plate", "web"} or times != {1.0}:
        raise ValueError("matching plate/web energy blocks at unit time required")
    return result


def compare_element_energies(original_dat: str, replay_dat: str) -> dict:
    original = element_energies(original_dat)
    replay = element_energies(replay_dat)
    result = {}
    for name, ids in (("plate", range(1, 17)), ("web", range(17, 33))):
        source_sum = sum(original[i] for i in ids)
        replay_sum = sum(replay[i] for i in ids)
        result[name] = {
            "source_j": source_sum,
            "replay_j": replay_sum,
            "sum_relative_difference": abs(source_sum - replay_sum) / source_sum,
            "max_element_relative_difference": max(
                abs(original[i] - replay[i]) / original[i] for i in ids
            ),
        }
    return result


def replay_node_forces(dat: str, nodes: set[int]) -> dict[int, tuple[float, ...]]:
    if type(dat) is not str or len(dat) > 8 * 1024 * 1024:
        raise ValueError("bounded replay DAT required")
    lines = dat.splitlines()
    starts = [i for i, line in enumerate(lines) if re.match(
        r"^\s*forces \(fx,fy,fz\) for set ALLEXTERIOR and time\b", line,
        re.I,
    )]
    if len(starts) != 1:
        raise ValueError("one exterior-node force block required")
    result = {}
    for line in lines[starts[0] + 1:]:
        parts = line.split()
        if len(parts) == 4 and parts[0].isdigit():
            node = int(parts[0])
            force = tuple(float(v.replace("D", "E")) for v in parts[1:])
            if node in result or not all(isfinite(v) for v in force):
                raise ValueError("duplicate exterior-node force")
            result[node] = force
        elif result:
            break
    if set(result) != nodes:
        raise ValueError("incomplete exterior-node force inventory")
    return result


def knot_action(points: list[tuple[float, ...]],
                forces: list[tuple[float, ...]],
                reference: tuple[float, float, float]) -> tuple[float, ...]:
    """Pull exterior force rows to translation, rotation and uniform expansion."""
    if len(points) != len(forces) or not points:
        raise ValueError("matching nonempty knot points and forces required")
    result = [0.0] * 7
    for xyz, f in zip(points, forces):
        r = tuple(xyz[j] - reference[j] for j in range(3))
        for j in range(3):
            result[j] += f[j]
        result[3] += r[1] * f[2] - r[2] * f[1]
        result[4] += r[2] * f[0] - r[0] * f[2]
        result[5] += r[0] * f[1] - r[1] * f[0]
        result[6] += sum(r[j] * f[j] for j in range(3))
    return tuple(result)


def seam_side_actions(frd: str, replay_dat: str) -> dict:
    """Return reference-pullback diagnostics at four *unloaded* seam knots.

    Uses the seven-coordinate linear knot map from CalculiX ``knotmpc.f``:
    u_a = t + theta cross r_a + e r_a. Root x=0 is excluded because supported.
    This is not a native L1 connection-law comparison.
    """
    coordinates, _ = _frd_fields(frd)
    bricks = expanded_bricks(frd, set(coordinates))
    sides = {
        "plate": set().union(*(set(bricks[i]) for i in range(1, 17))),
        "web": set().union(*(set(bricks[i]) for i in range(17, 33))),
    }
    if sides["plate"] & sides["web"]:
        raise ValueError("replay sides share exterior node IDs")
    forces = replay_node_forces(replay_dat, set(coordinates))
    stations = {}
    for x in (0.25, 0.5, 0.75, 1.0):
        station = {}
        for side, node_set in sides.items():
            if side == "plate":
                selected = [n for n in node_set if
                            abs(coordinates[n][0] - x) < 1e-9 and
                            abs(coordinates[n][1]) < 1e-9]
            else:
                selected = [n for n in node_set if
                            abs(coordinates[n][0] - x) < 1e-9 and
                            abs(coordinates[n][2] - 0.0175) < 1e-9]
            if len(selected) != 2:
                raise ValueError("expected one expanded face pair per seam side")
            resultants = knot_action(
                [coordinates[n] for n in selected],
                [forces[n] for n in selected],
                (x, 0.0, 0.0175),
            )
            station[side] = {"nodes": sorted(selected),
                             "force_n": resultants[:3],
                             "moment_nm": resultants[3:6],
                             "expansion_work_j_per_unit_e": resultants[6]}
        station["sum"] = {
            "force_n": [station["plate"]["force_n"][j] +
                        station["web"]["force_n"][j] for j in range(3)],
            "moment_nm": [station["plate"]["moment_nm"][j] +
                          station["web"]["moment_nm"][j] for j in range(3)],
            "expansion_work_j_per_unit_e":
                station["plate"]["expansion_work_j_per_unit_e"] +
                station["web"]["expansion_work_j_per_unit_e"],
        }
        stations[str(x)] = station
    return stations


def expanded_bricks(frd: str, nodes: set[int]) -> dict[int, tuple[int, ...]]:
    lines = frd.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith("    3C")]
    if len(starts) != 1 or len(lines[starts[0]].split()) < 2:
        raise ValueError("one expanded FRD connectivity block required")
    count = int(lines[starts[0]].split()[1])
    if count != 32:
        raise ValueError("expected the bounded 32-element plate/web mesh")
    bricks = {}
    i = starts[0] + 1
    while i < len(lines) and not lines[i].startswith(" -3"):
        header = lines[i].split()
        if len(header) != 5 or header[0] != "-1":
            raise ValueError("invalid FRD element header")
        element = int(header[1])
        if i + 1 >= len(lines):
            raise ValueError("missing FRD element connectivity")
        record = lines[i + 1].split()
        if len(record) != 9 or record[0] != "-2":
            raise ValueError("expected eight exterior brick nodes")
        connected = tuple(map(int, record[1:]))
        if (element in bricks or len(set(connected)) != 8 or
                not set(connected) <= nodes):
            raise ValueError("duplicate or invalid brick connectivity")
        bricks[element] = connected
        i += 2
    if (i >= len(lines) or set(bricks) != set(range(1, 33)) or
            set.union(*(set(c) for c in bricks.values())) != nodes):
        raise ValueError("incomplete expanded plate/web mesh")
    return bricks


def replay_deck(frd: str, offsets: dict[int, tuple[float, float, float]] | None = None
                ) -> tuple[str, dict]:
    coordinates, displacement = _frd_fields(frd)
    if set(coordinates) != set(displacement) or len(coordinates) != 100:
        raise ValueError("expected 100 complete expanded exterior nodes")
    bricks = expanded_bricks(frd, set(coordinates))
    offsets = {} if offsets is None else offsets
    if not set(offsets) <= set(coordinates) or any(
            len(v) != 3 or not all(isfinite(x) for x in v)
            for v in offsets.values()):
        raise ValueError("invalid bounded displacement offsets")
    lines = [
        "** DEVELOPMENT ENERGY-PARITY REPLAY: expanded S4 exterior U, not F03 acceptance",
        "*NODE,NSET=AllExterior",
    ]
    for node, xyz in sorted(coordinates.items()):
        lines.append(f"{node}," + ",".join(f"{v:.17g}" for v in xyz))
    lines.append("*ELEMENT,TYPE=C3D8I,ELSET=Plate")
    for element in range(1, 17):
        lines.append(f"{element}," + ",".join(map(str, bricks[element])))
    lines.append("*ELEMENT,TYPE=C3D8I,ELSET=Web")
    for element in range(17, 33):
        lines.append(f"{element}," + ",".join(map(str, bricks[element])))
    lines += [
        "*MATERIAL,NAME=Steel", "*ELASTIC", "210000000000,0.3",
        "*SOLID SECTION,ELSET=Plate,MATERIAL=Steel",
        "*SOLID SECTION,ELSET=Web,MATERIAL=Steel",
        "*STEP", "*STATIC", "*BOUNDARY",
    ]
    for node, vector in sorted(displacement.items()):
        for axis, value in enumerate(vector, 1):
            # FRD carries about six significant digits; short numeric fields
            # also fit CalculiX's bounded input-card parser.
            if node in offsets:
                value += offsets[node][axis-1]
            lines.append(f"{node},{axis},{axis},{value:.8E}")
    lines += [
        "*NODE PRINT,NSET=AllExterior", "RF",
        "*EL PRINT,ELSET=Plate", "ELSE",
        "*EL PRINT,ELSET=Web", "ELSE",
        "*END STEP",
    ]
    return "\n".join(lines) + "\n", {
        "exterior_nodes": len(coordinates),
        "plate_elements": 16,
        "web_elements": 16,
        "boundary_scalars": 3 * len(displacement),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--energy-deck", type=Path, required=True)
    p.add_argument("--frd", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--source-dat", type=Path)
    p.add_argument("--replay-dat", type=Path)
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    manifest_bytes = args.manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    original, expected = build_bundle(
        manifest["variant"], manifest["case"], manifest["nx"],
        manifest["root"], manifest["profile"],
        manifest.get("domain", "coupled"),
    )
    # The saved section J can differ by one binary64 ulp across Python math
    # runtimes. Keep every other manifest field and the regenerated deck exact.
    source_section = manifest["section"]
    expected_section = expected["section"]
    j_source = source_section["J_rect_m4"]
    j_expected = expected_section["J_rect_m4"]
    if abs(j_source - j_expected) <= ulp(j_source):
        for key in ("section", "web_only_section"):
            manifest[key] = dict(manifest[key], J_rect_m4=j_expected)
    if (manifest != expected or manifest["case"] != "web_mx" or
            manifest.get("domain", "coupled") != "coupled"):
        raise ValueError("only source-bound coupled web_mx is admitted")
    energy = original.replace(
        "*END STEP\n", "*EL PRINT,ELSET=Plate\nELSE\n"
        "*EL PRINT,ELSET=Web\nELSE\n*END STEP\n",
    )
    if args.energy_deck.read_bytes() != energy.encode("ascii"):
        raise ValueError("saved energy deck differs from regenerated source")
    frd_bytes = args.frd.read_bytes()
    deck, inventory = replay_deck(frd_bytes.decode("ascii"))
    identity = {
        "classification": "development_expanded_solid_energy_parity_only",
        "source_manifest_sha256": sha256(manifest_bytes).hexdigest(),
        "source_energy_deck_sha256": sha256(args.energy_deck.read_bytes()).hexdigest(),
        "source_frd_sha256": sha256(frd_bytes).hexdigest(),
        "replay_deck_sha256": sha256(deck.encode("ascii")).hexdigest(),
        **inventory,
    }
    if args.report is None:
        if args.out.exists():
            raise FileExistsError("replay output is immutable; choose a new file")
        args.out.write_text(deck, encoding="ascii", newline="\n")
        print(json.dumps(identity, indent=2, sort_keys=True))
        return
    if (args.source_dat is None or args.replay_dat is None or
            args.report.exists() or args.out.read_bytes() != deck.encode("ascii")):
        raise ValueError("complete immutable replay and source DAT required")
    source_dat = args.source_dat.read_bytes()
    replay_dat = args.replay_dat.read_bytes()
    identity.update({
        "source_dat_sha256": sha256(source_dat).hexdigest(),
        "replay_dat_sha256": sha256(replay_dat).hexdigest(),
        "energy_parity": compare_element_energies(
            source_dat.decode("ascii"), replay_dat.decode("ascii")),
        "unloaded_seam_actions": seam_side_actions(
            frd_bytes.decode("ascii"), replay_dat.decode("ascii")),
        "limitations": [
            "FRD exterior displacements carry about six significant digits; "
            "reaction imbalance is not an exact S4 knot residual.",
            "The seven-coordinate map is a reference linearization. The "
            "equilibrated expansion sensitivity is not inferred from its "
            "small observed value.",
            "The welded S4 seam and its web-force couple differ from native "
            "L1 and a B3 rotational moment; this is no F03 acceptance score.",
        ],
    })
    args.report.write_text(json.dumps(identity, indent=2, sort_keys=True) + "\n",
                           encoding="ascii", newline="\n")
    print(json.dumps({"report": str(args.report),
                      "plate_sum_error": identity["energy_parity"]["plate"]["sum_relative_difference"],
                      "web_sum_error": identity["energy_parity"]["web"]["sum_relative_difference"]}))


if __name__ == "__main__":
    main()
