"""Derive one bounded separate-node terminal bond/contact reference deck.

This is an external-reference diagnostic, not a native coupling law or G0
qualification. It preserves the pinned factor-1 C3D8 terminal torque geometry,
material, supports, and bar-tip nodal wrench. The terminal bond is represented
by a matching-surface *TIE instead of shared node numbers. The unbonded contact
surface remains complete; no contact face is trimmed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


SOURCE_SHA256 = "80990241096a94322c01be732e208855751b12fee2bcf7d3211e098e4db0b64c"
PLATE_FACE = (4, 5, 6, 7)  # C3D8 S2, zero based
BAR_FACE = (0, 1, 2, 3)  # C3D8 S1, zero based


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _elements(lines: list[str], card: str) -> dict[int, tuple[int, ...]]:
    start = lines.index(card) + 1
    end = next(i for i in range(start, len(lines)) if lines[i].startswith("*"))
    return {int(fields[0]): tuple(map(int, fields[1:]))
            for fields in (line.split(",") for line in lines[start:end])}


def prepare(source: Path, root: Path) -> dict:
    if _digest(source) != SOURCE_SHA256:
        raise ValueError("source contact deck identity changed")
    if root.exists():
        raise FileExistsError(root)
    lines = source.read_text(encoding="utf-8").splitlines()
    node_start = lines.index("*NODE,NSET=AllNodes") + 1
    node_end = lines.index("*ELEMENT,TYPE=C3D8,ELSET=Plate")
    nodes = {int(fields[0]): tuple(map(float, fields[1:]))
             for fields in (line.split(",") for line in lines[node_start:node_end])}
    plate = _elements(lines, "*ELEMENT,TYPE=C3D8,ELSET=Plate")
    bar = _elements(lines, "*ELEMENT,TYPE=C3D8,ELSET=Stiffener")
    plate_ids = {n for cell in plate.values() for n in cell}
    bar_ids = {n for cell in bar.values() for n in cell}
    shared = sorted(plate_ids & bar_ids)
    if len(shared) != 6 or any(
        not (.9 - 1e-12 <= nodes[n][0] <= 1. + 1e-12 and
             abs(nodes[n][2] - .035) < 1e-12)
        for n in shared
    ):
        raise AssertionError("terminal shared-node inventory changed")
    duplicated = {old: max(nodes) + i + 1 for i, old in enumerate(shared)}
    new_nodes = {**nodes, **{new: nodes[old] for old, new in duplicated.items()}}
    new_bar = {eid: tuple(duplicated.get(n, n) for n in cell)
               for eid, cell in bar.items()}

    def bonded_faces(elements: dict[int, tuple[int, ...]], face: tuple[int, ...]) -> list[int]:
        return [eid for eid, cell in elements.items()
                if all(abs(new_nodes[cell[i]][2] - .035) < 1e-12 for i in face)
                and min(new_nodes[cell[i]][0] for i in face) >= .9 - 1e-12
                and max(new_nodes[cell[i]][0] for i in face) <= 1. + 1e-12
                and min(new_nodes[cell[i]][1] for i in face) >= -.05 - 1e-12
                and max(new_nodes[cell[i]][1] for i in face) <= .05 + 1e-12]

    plate_bond = bonded_faces(plate, PLATE_FACE)
    bar_bond = bonded_faces(new_bar, BAR_FACE)
    if len(plate_bond) != 2 or len(bar_bond) != 2:
        raise AssertionError("bonded face inventory changed")
    plate_bond_nodes = {plate[e][i] for e in plate_bond for i in PLATE_FACE}
    bar_bond_nodes = {new_bar[e][i] for e in bar_bond for i in BAR_FACE}
    if ({new_nodes[n] for n in plate_bond_nodes} !=
            {new_nodes[n] for n in bar_bond_nodes}):
        raise AssertionError("terminal tie surfaces do not match exactly")
    if (plate_ids & {n for cell in new_bar.values() for n in cell}):
        raise AssertionError("separate bodies still share element nodes")

    contact_start = lines.index("*ELSET,ELSET=PlateUnbondedFaces")
    contact_end = lines.index("*MATERIAL,NAME=Isotropic")
    if lines[contact_start + 1] != "75,76,77,78,84,85,86,87" or lines[contact_start + 3] != "109,110,111,112,114,115,116,117":
        raise AssertionError("full unbonded contact coverage changed")
    if lines[contact_end - 1] != "BarBottomUnbonded,PlateTopUnbonded":
        raise AssertionError("contact surface order changed")
    if plate_bond_nodes & bar_bond_nodes:
        raise AssertionError("tie surfaces still share node identities")
    if any(e in plate_bond for e in (75, 76, 77, 78, 84, 85, 86, 87)):
        raise AssertionError("plate contact and bond face elements overlap")
    if any(e in bar_bond for e in (109, 110, 111, 112, 114, 115, 116, 117)):
        raise AssertionError("bar contact and bond face elements overlap")
    tie_cards = [
        "*ELSET,ELSET=PlateTerminalBondFaces", ",".join(map(str, plate_bond)),
        "*ELSET,ELSET=BarTerminalBondFaces", ",".join(map(str, bar_bond)),
        "*SURFACE,NAME=PlateTopTerminalBond,TYPE=ELEMENT",
        "PlateTerminalBondFaces,S2",
        "*SURFACE,NAME=BarBottomTerminalBond,TYPE=ELEMENT",
        "BarTerminalBondFaces,S1",
        "*TIE,NAME=TerminalBond,ADJUST=NO,POSITION TOLERANCE=1e-8",
        "PlateTopTerminalBond,BarBottomTerminalBond",
    ]
    support_start = lines.index("*NSET,NSET=Supports") + 1
    step_start = lines.index("*STEP")
    supports = {int(n) for line in lines[support_start:step_start]
                for n in line.split(",")}
    if plate_bond_nodes & supports:
        raise AssertionError("dependent tie nodes are directly supported")
    cload_start = lines.index("*CLOAD") + 1
    cload_end = lines.index("*NODE PRINT,NSET=Probe")
    old_loads = [line.split(",") for line in lines[cload_start:cload_end]]
    if any(int(fields[0]) in plate_bond_nodes - set(duplicated) for fields in old_loads):
        raise AssertionError("unexpected plate-side terminal load")
    load_ids = {duplicated.get(int(fields[0]), int(fields[0])) for fields in old_loads}
    if load_ids & plate_bond_nodes:
        raise AssertionError("load remains on a dependent tie node")

    root.mkdir(parents=True)
    outputs = {}
    for with_contact in (False, True):
        result: list[str] = []
        in_bar_elements = False
        in_cload = False
        for index, line in enumerate(lines):
            if index == node_end:
                result.extend(f"{new},{','.join(format(v, '.12g') for v in nodes[old])}"
                              for old, new in duplicated.items())
            if index == contact_start:
                if with_contact:
                    result.extend(lines[contact_start:contact_end])
                result.extend(tie_cards)
            if contact_start <= index < contact_end:
                continue
            if line == "*ELEMENT,TYPE=C3D8,ELSET=Stiffener":
                in_bar_elements = True
            elif in_bar_elements and line.startswith("*"):
                in_bar_elements = False
            if in_bar_elements and not line.startswith("*"):
                fields = line.split(",")
                line = ",".join((fields[0], *(str(duplicated.get(int(n), int(n)))
                                               for n in fields[1:])))
            if index == lines.index("*NSET,NSET=Supports"):
                result.append(",".join(map(str, duplicated.values())))
            if line == "*CLOAD":
                in_cload = True
            elif in_cload and line.startswith("*"):
                in_cload = False
            if in_cload and not line.startswith("*"):
                fields = line.split(",")
                fields[0] = str(duplicated.get(int(fields[0]), int(fields[0])))
                line = ",".join(fields)
            if line == "*END STEP":
                if with_contact:
                    result.extend(("*CONTACT PRINT,FREQUENCY=9999", "CDIS,CSTR,CNUM"))
                result.extend(("*NODE FILE,OUTPUT=3D", "U"))
            result.append(line)
        name = "terminal-tie-contact" if with_contact else "terminal-tie-only"
        deck = root / f"{name}.inp"
        deck.write_text("\n".join(result) + "\n", encoding="utf-8", newline="\n")
        outputs[name] = {"path": deck.name, "sha256": _digest(deck)}
    metadata = {
        "status": "EXPLORATORY_NOT_G0_ACCEPTANCE",
        "question": "Does a separate-node, exactly matching terminal tie restore full unbonded hard-mortar contact execution and an admissible physical reference?",
        "source_deck_sha256": SOURCE_SHA256,
        "change": "duplicate six terminal interface nodes on bar only; tie plate slave to bar master over the complete terminal patch; retain complete unbonded bar-slave contact and remap bar tip loads/probes",
        "original_node_count": len(nodes), "new_node_count": len(new_nodes),
        "terminal_node_map": {str(k): v for k, v in duplicated.items()},
        "plate_bonded_face_elements": plate_bond,
        "bar_bonded_face_elements": bar_bond,
        "contact_face_counts": [8, 8],
        "tie_slave_support_overlap": sorted(plate_bond_nodes & supports),
        "tie_slave_load_overlap": sorted(plate_bond_nodes & load_ids),
        "deck_outputs": outputs,
        "formal_f03_authority_consumed": False,
    }
    (root / "preflight.json").write_text(json.dumps(metadata, indent=2) + "\n",
                                           encoding="utf-8")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.root), indent=2))
