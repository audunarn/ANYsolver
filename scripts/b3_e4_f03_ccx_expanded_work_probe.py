"""Probe source-bound expanded-shell side work with one seven-coordinate hat.

Development diagnostic only: the welded S4 seam is not the native L1 law.
"""

from __future__ import annotations

import argparse
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path

from scripts.b3_e4_f03_ccx_expanded_solid_replay import (
    element_energies, expanded_bricks, replay_deck, replay_node_forces,
)
from scripts.b3_e4_f03_ccx_matched_t_reference import _FRD_NUMBER, _frd_fields


REFERENCE = (0.5, 0.0, 0.0175)
TRANSLATION = (0.0, 0.001, 0.0)  # metres
ROTATION = (0.001, 0.0, 0.0)  # radians
EXPANSION = 0.001  # dimensionless
AMPLITUDES = (0.01, 0.001)


def hat_displacements(coordinates: dict[int, tuple], nodes: list[int]
                      ) -> dict[int, tuple[float, float, float]]:
    if len(nodes) != 2 or len(set(nodes)) != 2:
        raise ValueError("one expanded seam face pair required")
    result = {}
    for node in nodes:
        xyz = coordinates[node]
        r = tuple(xyz[j] - REFERENCE[j] for j in range(3))
        cross = (ROTATION[1]*r[2] - ROTATION[2]*r[1],
                 ROTATION[2]*r[0] - ROTATION[0]*r[2],
                 ROTATION[0]*r[1] - ROTATION[1]*r[0])
        result[node] = tuple(TRANSLATION[j] + cross[j] + EXPANSION*r[j]
                             for j in range(3))
    return result


def build_probe_inputs(frd_bytes: bytes, base_bytes: bytes,
                       bound_report_bytes: bytes) -> tuple[dict[str, str], dict]:
    frd = frd_bytes.decode("ascii")
    base, _ = replay_deck(frd)
    report = json.loads(bound_report_bytes)
    if (base.encode("ascii") != base_bytes or
            sha256(base_bytes).hexdigest() != report["replay_deck_sha256"] or
            sha256(frd_bytes).hexdigest() != report["source_frd_sha256"]):
        raise ValueError("source replay/report/FRD identity mismatch")
    coordinates, _ = _frd_fields(frd)
    station = report["unloaded_seam_actions"]["0.5"]
    side_hats = {}
    for side in ("plate", "web"):
        nodes = station[side]["nodes"]
        side_hats[side] = hat_displacements(coordinates, nodes)
    if set(side_hats["plate"]) & set(side_hats["web"]):
        raise ValueError("the two replay walls must have distinct exterior nodes")
    decks = {}
    for side in ("plate", "web"):
        for amplitude in AMPLITUDES:
            for sign, label in ((1., "plus"), (-1., "minus")):
                offsets = {node: tuple(sign*amplitude*v for v in vector)
                           for node, vector in side_hats[side].items()}
                name = f"{side}_{label}_{str(amplitude).replace('.', 'p')}"
                decks[name], _ = replay_deck(frd, offsets)
    combined = dict(side_hats["plate"])
    combined.update(side_hats["web"])
    decks["combined_unit_hat"], _ = replay_deck(frd, combined)
    manifest = {
        "classification": "development_welded_S4_seven_coordinate_work_probe_not_F03",
        "base_replay_sha256": sha256(base_bytes).hexdigest(),
        "source_frd_sha256": sha256(frd_bytes).hexdigest(),
        "bound_report_sha256": sha256(bound_report_bytes).hexdigest(),
        "station_x_m": REFERENCE[0],
        "root_virtual_motion": "zero",
        "all_other_nodes_virtual_motion": "zero",
        "translation_hat_m": list(TRANSLATION),
        "rotation_hat_rad": list(ROTATION),
        "expansion_hat": EXPANSION,
        "amplitudes": list(AMPLITUDES),
        "side_nodes": {side: station[side]["nodes"] for side in side_hats},
        "decks": {name: sha256(deck.encode("ascii")).hexdigest()
                  for name, deck in decks.items()},
    }
    return decks, manifest


def displacement_print_quantum(frd: str) -> dict[int, tuple[float, ...]]:
    """One last-place unit for each printed ASCII FRD displacement value."""
    lines = frd.splitlines()
    starts = [i for i, line in enumerate(lines) if line.startswith(" -4  DISP")]
    if len(starts) != 1:
        raise ValueError("one ASCII FRD displacement block required")
    result = {}
    for line in lines[starts[0] + 1:]:
        if line.startswith(" -3"):
            break
        if line.startswith(" -1"):
            node = int(line[3:13])
            tokens = _FRD_NUMBER.findall(line[13:])
            if node in result or len(tokens) != 3:
                raise ValueError("incomplete FRD displacement precision")
            result[node] = tuple(float(Decimal(1).scaleb(
                Decimal(token).as_tuple().exponent)) for token in tokens)
    if len(result) != 100:
        raise ValueError("expected complete expanded displacement precision")
    return result


def assess_probe(directory: Path, frd_bytes: bytes, base_deck_bytes: bytes,
                 base_dat_bytes: bytes, bound_report_bytes: bytes) -> dict:
    manifest_bytes = (directory / "probe_manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    expected_decks, expected_manifest = build_probe_inputs(
        frd_bytes, base_deck_bytes, bound_report_bytes,
    )
    report = json.loads(bound_report_bytes)
    if (manifest != expected_manifest or
            manifest["bound_report_sha256"] != sha256(bound_report_bytes).hexdigest()
            or manifest["source_frd_sha256"] != sha256(frd_bytes).hexdigest()
            or report["replay_dat_sha256"] != sha256(base_dat_bytes).hexdigest()):
        raise ValueError("probe source identity changed")
    frd = frd_bytes.decode("ascii")
    coordinates, _ = _frd_fields(frd)
    bricks = expanded_bricks(frd, set(coordinates))
    side_nodes = {
        "plate": set().union(*(set(bricks[i]) for i in range(1, 17))),
        "web": set().union(*(set(bricks[i]) for i in range(17, 33))),
    }
    base_forces = replay_node_forces(base_dat_bytes.decode("ascii"),
                                     set(coordinates))
    quantum = displacement_print_quantum(frd)
    energies = {}
    output_hashes = {}
    for name, deck_hash in manifest["decks"].items():
        if ((directory / f"{name}.inp").read_bytes() !=
                expected_decks[name].encode("ascii") or
                sha256(expected_decks[name].encode("ascii")).hexdigest() != deck_hash):
            raise ValueError("probe deck identity changed")
        stdout = (directory / f"{name}.stdout").read_bytes()
        stderr = (directory / f"{name}.stderr").read_bytes()
        if (b"Job finished" not in stdout or b"Using 1 cpu for spooles" not in stdout
                or stderr):
            raise ValueError("probe completion or effective thread setting missing")
        dat_bytes = (directory / f"{name}.dat").read_bytes()
        energies[name] = element_energies(dat_bytes.decode("ascii"))
        output_hashes[name] = {"dat": sha256(dat_bytes).hexdigest(),
                               "stdout": sha256(stdout).hexdigest()}
    stationary = report["unloaded_seam_actions"]["0.5"]
    comparisons = {}
    for side, ids in (("plate", range(1, 17)), ("web", range(17, 33))):
        action = stationary[side]
        predicted = (sum(action["force_n"][j]*TRANSLATION[j]
                         for j in range(3)) +
                     sum(action["moment_nm"][j]*ROTATION[j]
                         for j in range(3)) +
                     action["expansion_work_j_per_unit_e"]*EXPANSION)
        derivatives = {}
        for amplitude in AMPLITUDES:
            label = str(amplitude).replace(".", "p")
            plus = sum(energies[f"{side}_plus_{label}"][i] for i in ids)
            minus = sum(energies[f"{side}_minus_{label}"][i] for i in ids)
            derivative = (plus-minus)/(2*amplitude)
            derivatives[label] = {
                "centered_energy_derivative_j": derivative,
                "relative_to_replay_action": abs(derivative-predicted)/abs(predicted),
            }
        comparisons[side] = {"replay_RF_dot_hat_j": predicted,
                             "derivatives": derivatives}
    combined = replay_node_forces(
        (directory / "combined_unit_hat.dat").read_text(), set(coordinates))
    bounds = {}
    for side, nodes in side_nodes.items():
        all_printed = 0.
        for node in nodes:
            for axis in range(3):
                influence = abs(combined[node][axis]-base_forces[node][axis])
                contribution = influence*quantum[node][axis]
                all_printed += contribution
        bounds[side] = {
            "full_last_place_quantum_bound_j": all_printed,
        }
    return {
        "classification": "development_seven_coordinate_work_and_print_precision_not_F03",
        "probe_manifest_sha256": sha256(manifest_bytes).hexdigest(),
        "source_frd_sha256": sha256(frd_bytes).hexdigest(),
        "base_replay_dat_sha256": sha256(base_dat_bytes).hexdigest(),
        "output_hashes": output_hashes,
        "station_x_m": REFERENCE[0],
        "supported_virtual_field": "one seven-coordinate seam hat at x=0.5; "
                                   "root and all other original nodes zero",
        "wall_work": comparisons,
        "frd_print_precision_sensitivity": bounds,
        "limitation": "Last-place bounds cover printed displacement rounding in the "
                      "replayed linear operator only; they do not bound the "
                      "S4-to-solid operator difference or native L1 law error.",
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--frd", type=Path, required=True)
    p.add_argument("--base-deck", type=Path, required=True)
    p.add_argument("--bound-report", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--assess", action="store_true")
    p.add_argument("--report-name", default="work_assessment.json")
    args = p.parse_args()
    if args.assess:
        if (Path(args.report_name).name != args.report_name or
                not args.report_name.endswith(".json")):
            raise ValueError("plain JSON report name required")
        report_path = args.out_dir / args.report_name
        if report_path.exists():
            raise FileExistsError("work assessment is immutable")
        base_dat = args.base_deck.with_suffix(".dat")
        assessment = assess_probe(args.out_dir, args.frd.read_bytes(),
                                  args.base_deck.read_bytes(), base_dat.read_bytes(),
                                  args.bound_report.read_bytes())
        report_path.write_text(json.dumps(assessment, indent=2, sort_keys=True) + "\n",
                               encoding="ascii", newline="\n")
        print(json.dumps({"report": str(report_path),
                          "wall_work": assessment["wall_work"],
                          "print_bounds": assessment["frd_print_precision_sensitivity"]}))
        return
    decks, manifest = build_probe_inputs(
        args.frd.read_bytes(), args.base_deck.read_bytes(),
        args.bound_report.read_bytes(),
    )
    if not args.out_dir.is_dir() or any(args.out_dir.iterdir()):
        raise ValueError("new empty versioned probe directory required")
    for name, deck in decks.items():
        (args.out_dir / f"{name}.inp").write_text(
            deck, encoding="ascii", newline="\n",
        )
    (args.out_dir / "probe_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="ascii", newline="\n",
    )
    print(json.dumps({"input_count": len(decks),
                      "source_frd_sha256": manifest["source_frd_sha256"],
                      "station_x_m": REFERENCE[0]}))


if __name__ == "__main__":
    main()
