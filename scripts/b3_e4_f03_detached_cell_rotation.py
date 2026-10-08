"""Compare retained B3 cell rotations with saved detached-solid cell averages.

This is a representation diagnostic, not a section or connection acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from scripts.b3_e4_f03_c1_detached_port_screen import _solid_section_fits
from scripts.b3_e4_f03_c3d20r_bond_force_recovery import read_deck
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


STATIONS = (.9, .925, .95, .975, 1.)
CELLS = (("900", "925", "950"), ("950", "975", "1000"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.evidence_root.resolve()
    if root.exists():
        raise FileExistsError(root)
    base = root.parent
    original = base / "f03-c1-detached-port-dev-20260926-v2"
    result_path = original / "result.json"
    manifest_path = original / "manifest.json"
    stem = original / "tip_mx/c1-detached-tip_mx"
    record = json.loads(result_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    native = record["tip_mx"]["native"]
    solid = record["tip_mx"]["solid"]
    if (solid["status"] != "EXPLORATORY_COMPLETE" or
            solid["model"]["shared_interface_nodes"] != 0 or
            solid["model"]["factor"] != 4 or
            solid["model"]["bond_policy"] != "detached" or
            manifest["load_cases"] != ["tip_mx", "tip_fz"] or
            abs(native["tip_work_j"]-solid["tip_work_j"]) > 1e-4):
        raise ValueError("saved detached C1 torque case is incompatible")
    xyz, elements = read_deck(stem.with_suffix(".inp"))
    u = _read_frd_u(stem.with_suffix(".frd"))
    if set(u) != set(range(1, len(xyz))):
        raise ValueError("saved detached solid field incomplete")
    fits = _solid_section_fits(xyz, u, elements, stations=STATIONS)
    cells = []
    for start, middle, stop in CELLS:
        average = (fits[start]["rotation_rad"][0] +
                   4 * fits[middle]["rotation_rad"][0] +
                   fits[stop]["rotation_rad"][0]) / 6
        retained = native["stations"][start]["rx_rad"]
        endpoint = fits[start]["rotation_rad"][0]
        cells.append({"interval_m": [int(start)/1000, int(stop)/1000],
                      "solid_section_simpson_mean_rx_rad": average,
                      "native_retained_cell_rx_rad": retained,
                      "native_minus_solid_cell_mean_rad": retained-average,
                      "native_minus_solid_left_endpoint_rad": retained-endpoint,
                      "solid_section_midpoint_rx_rad": fits[middle]["rotation_rad"][0]})
    paths = [result_path, manifest_path, stem.with_suffix(".inp"),
             stem.with_suffix(".frd")]
    result = {
        "classification": "bounded saved detached-bar representation diagnostic; no G0B acceptance",
        "question": "Does the apparent native retained-pose/solid-section torque mismatch survive comparison at the same B3 half-cell measure?",
        "outcome_rule": "If the solid cell mean approaches retained B3 rotations while endpoint comparisons differ, treat endpoint mismatch mainly as representation; a material cell-mean mismatch keeps section/warping in focus. Neither outcome proves a connection law.",
        "cell_measure": "Simpson average of nodal least-squares Q20 section Rx at actual factor-four x planes; B3 retained cell rotation is constant per half-cell",
        "solid_section_planes": fits,
        "cells": cells,
        "limits": ["Simpson average is a bounded diagnostic, not exact beam-section integration",
                   "native retained cell frame and solid fitted physical section are different formulations",
                   "detached bare bar has no shell connection", "one 3D mesh level"],
        "inputs_sha256": {str(path.relative_to(base)): _sha(path) for path in paths},
        "section_fitter_sha256": _sha(
            Path(__file__).resolve().parents[1] /
            "scripts/b3_e4_f03_c1_detached_port_screen.py"),
        "runner_sha256": _sha(Path(__file__)),
    }
    root.mkdir(parents=True)
    (root / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    for cell in cells:
        print(cell["interval_m"], "retained minus solid mean µrad",
              round(cell["native_minus_solid_cell_mean_rad"] * 1e6, 4))


if __name__ == "__main__":
    main()
