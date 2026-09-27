"""One contact-seam discriminator on the failed matched C1 mortar deck.

Only the seam-adjacent final column is removed from the two contact sets.
The resulting field cannot serve as a physical accuracy reference.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

import numpy as np

from scripts.b3_e4_f03_c1_hard_mortar_screen import ROOT, SOURCE
from scripts.b3_e4_f03_ccx_six_channel_compliance import EXE, EXE_SHA, _run
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_deck_nodes


FAILED = (ROOT / ".qualification/b3-ge-e4-pl/"
          "f03-c1-hard-mortar-dev-20260927-v1/c1-hard-mortar-tip-mx.inp")
EXPECTED_FAILED = "7e0d1d32acd322d7a3a3a36418b6da0f07bb02349faac3197c8b90ba1d2651ce"


def _elements(deck: str, name: str):
    lines = deck.splitlines()
    header = f"*ELEMENT,TYPE=C3D20R,ELSET={name}"
    if lines.count(header) != 1:
        raise ValueError("one C3D20R domain required")
    start = lines.index(header)+1
    cells = {}
    for first, second in zip(lines[start::2], lines[start+1::2]):
        if first.startswith("*"):
            break
        a = [int(value) for value in first.split(",")]
        b = [int(value) for value in second.split(",")]
        if len(a) != 16 or len(b) != 5 or a[0] in cells:
            raise ValueError("unexpected quadratic element record")
        cells[a[0]] = a[1:]+b
    return cells


def _face_ids(cells, contact_ids, face_slots):
    by_nodes = {}
    for eid in contact_ids:
        nodes = frozenset(cells[eid][slot] for slot in face_slots)
        if len(nodes) != 8 or nodes in by_nodes:
            raise ValueError("ambiguous quadratic contact face")
        by_nodes[nodes] = eid
    return by_nodes


def _set_lines(ids):
    ordered = sorted(ids)
    return [",".join(str(value) for value in ordered[i:i+12])
            for i in range(0, len(ordered), 12)]


def _replace_set(deck, label, old, new):
    header = f"*ELSET,ELSET={label}\n"
    if deck.count(header) != 1:
        raise ValueError("contact set header changed")
    start = deck.index(header)+len(header)
    end = deck.index("\n*", start)
    original = deck[start:end].splitlines()
    parsed = {int(value) for line in original for value in line.split(",")}
    if parsed != set(old) or len(parsed) != len(old):
        raise ValueError("contact set inventory changed")
    replacement = "\n".join(_set_lines(new))
    result = deck[:start]+replacement+deck[end:]
    if result.replace(replacement+deck[end:end+1],
                      deck[start:end]+deck[end:end+1], 1) != deck:
        # The stronger source-diff check below also catches formatting drift.
        raise ArithmeticError("contact-set edit cannot be reversed")
    return result


def prepare():
    if digest(FAILED) != EXPECTED_FAILED or digest(EXE) != EXE_SHA:
        raise ValueError("failed mortar source or solver identity changed")
    deck = FAILED.read_text()
    model = json.loads((SOURCE / "model.json").read_text())
    coords = _read_deck_nodes(FAILED)
    plate_contact = list(map(int, model["plate_contact_face_element_ids"]))
    bar_contact = list(map(int, model["bar_contact_face_element_ids"]))
    plate_faces = _face_ids(_elements(deck, "Plate"), plate_contact,
                            (4, 5, 6, 7, 12, 13, 14, 15))
    bar_faces = _face_ids(_elements(deck, "Stiffener"), bar_contact,
                          (0, 1, 2, 3, 8, 9, 10, 11))
    pairs = model["unbonded_face_pairs"]
    if len(pairs) != 128 or len(plate_faces) != 128 or len(bar_faces) != 128:
        raise ValueError("complete paired contact inventory required")
    selected = {"plate": [], "bar": []}
    removed = {"plate": [], "bar": []}
    for index, face in enumerate(pairs):
        plate_nodes = frozenset(int(pair[0]) for pair in face)
        bar_nodes = frozenset(int(pair[1]) for pair in face)
        if plate_nodes not in plate_faces or bar_nodes not in bar_faces:
            raise ValueError("paired face cannot map to contact element")
        xyz = np.array([coords[node] for node in plate_nodes])
        x0, x1 = float(xyz[:, 0].min()), float(xyz[:, 0].max())
        final = index >= 120
        if (final and (abs(x0-.8625) > 1e-10 or abs(x1-.9) > 1e-10)
                or not final and x1 > .8625+1e-10):
            raise ValueError("final contact column geometry changed")
        target = removed if final else selected
        target["plate"].append(plate_faces[plate_nodes])
        target["bar"].append(bar_faces[bar_nodes])
    if any(len(group[side]) != count for group, count in
           ((selected, 120), (removed, 8)) for side in ("plate", "bar")):
        raise ValueError("seam trim count changed")
    candidate = _replace_set(deck, "PlateUnbondedFaces", plate_contact,
                             selected["plate"])
    candidate = _replace_set(candidate, "BarUnbondedFaces", bar_contact,
                             selected["bar"])
    return candidate, selected, removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    output = args.output_root.resolve()
    if output.exists():
        raise FileExistsError("preserve prior seam screen")
    candidate, selected, removed = prepare()
    output.mkdir(parents=True)
    stem = "c1-hard-mortar-trim-seam"
    deck = output / f"{stem}.inp"
    deck.write_text(candidate)
    code, stdout, stderr, elapsed, peak, failure = _run(stem, output)
    (output / "stdout.log").write_bytes(stdout)
    (output / "stderr.log").write_bytes(stderr)
    report = {
        "classification": "seam-deleted contact feasibility only; untreated strip bars physical accuracy use",
        "source_deck_sha256": digest(FAILED),
        "candidate_deck_sha256": digest(deck),
        "runner_sha256": digest(Path(__file__)),
        "solver_sha256": EXE_SHA,
        "retained_contact_faces": {side: len(ids) for side, ids in selected.items()},
        "removed_contact_element_ids": removed,
        "removed_plate_x_interval_m": [.8625, .9],
        "elapsed_seconds": elapsed, "peak_solver_rss_bytes": peak,
        "exit_code": code, "failure": failure,
        "status": "EXPLORATORY_FAILURE",
        "limitations": ["final eight paired faces have no contact law",
                        "no complete physical gap or balance comparison",
                        "not F03/G0B or native accuracy acceptance"],
    }
    if failure is None:
        if code != 0:
            failure = f"CALCULIX_EXIT_{code}"
        else:
            stdout_text = stdout.decode(errors="replace")
            cvg = (output / f"{stem}.cvg").read_text(errors="replace")
            if stdout_text.count("Job finished") == 1 and "S T E P" in cvg:
                report["status"] = "EXPLORATORY_COMPLETED_UNTREATED_COLUMN"
            else:
                failure = "INCOMPLETE_JOB_OR_CONVERGENCE_LOG"
    report["failure"] = failure
    report["raw_files_sha256"] = {
        path.name: digest(path) for path in sorted(output.iterdir())
        if path.is_file() and path.name != "result.json"}
    (output / "result.json").write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False)+"\n")
    print(json.dumps({key: report[key] for key in
                      ("status", "failure", "elapsed_seconds",
                       "peak_solver_rss_bytes")}), flush=True)
    return 0 if report["status"] == "EXPLORATORY_COMPLETED_UNTREATED_COLUMN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
