"""Screen the saved linear C1 torque field at full and half load.

The half-load field scales only the saved displacement; initial clearance,
shared bond, geometry and supports are unchanged. Interior samples cannot
certify continuous separation or native beam-shell accuracy.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c1_hard_mortar_screen import _all_same_xy_gap
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_solid_bond_pose_projection import (
    _read_deck_nodes, _read_frd_u,
)


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / ".qualification/b3-ge-e4-pl/f03-ccx-c1-tangent-terminal-torque-full-u-dev-20260925-v1/solid-4-tip_mx"


def evaluate():
    record_path = CASE.parent / "result.json"
    records = json.loads(record_path.read_text())
    record = next((item for item in records if item.get("case") == CASE.name), None)
    if record is None or record.get("exit_code") != 0:
        raise ValueError("completed saved C1 torque response required")
    if not np.allclose(record["response"]["applied_wrench_N_Nm"],
                       (0., 0., 0., 100., 0., 0.), rtol=0., atol=1e-10):
        raise ValueError("saved physical torque load changed")
    model_path = CASE / "model.json"
    deck = CASE / f"{CASE.name}.inp"
    frd = CASE / f"{CASE.name}.frd"
    for path in (model_path, deck, frd):
        if digest(path) != record["files_sha256"][path.name]:
            raise ValueError(f"saved torque identity changed: {path.name}")
    model = json.loads(model_path.read_text())
    if (model.get("factor") != 4 or model.get("contact_policy") != "none" or
            model.get("bond_policy") != "terminal" or
            model.get("bar_clearance_um") != 2 or
            model.get("bar_reference_profile") !=
            "C1_TWO_QUADRATIC_TANGENT_ALIGNED_V1" or
            model.get("full_displacement_output") is not True or
            len(model.get("unbonded_face_pairs", [])) != 128 or
            model.get("shear") != "tip_mx"):
        raise ValueError("saved C1 torque model contract changed")
    coordinates = _read_deck_nodes(deck)
    field = _read_frd_u(frd)
    if set(field) != set(coordinates) or len(field) != model["node_count"]:
        raise ValueError("incomplete saved C1 torque field")
    faces = [np.asarray(face, dtype=int) for face in model["unbonded_face_pairs"]]
    full = _all_same_xy_gap(coordinates, field, faces)
    if full["unresolved"] or full["negative"] == 0 or full["samples"] != 128*81:
        raise ValueError("historical full-load overlap witness not reproduced")
    half = _all_same_xy_gap(coordinates,
                            {node: 0.5*value for node, value in field.items()},
                            faces)
    return {
        "status": "EXPLORATORY_COMPLETE", "classification": "saved-field linear half-load C1 torque surface-order screen",
        "saved_input_sha256": {path.name: digest(path) for path in
                               (record_path, model_path, deck, frd)},
        "source_sha256": digest(Path(__file__)),
        "full_load_Nm": 100., "half_load_Nm": 50.,
        "full_load": full, "half_load": half,
        "limitations": ["linear superposition on one fixed C1 solid geometry",
                        "interior same-paired-face sampling only",
                        "not a continuous nonintersection certificate or mesh convergence",
                        "no native accuracy or F03/G0B acceptance"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve prior torque screen")
    result = evaluate()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False) + "\n")
    print(json.dumps({key: result[key] for key in ("full_load", "half_load")},
                     sort_keys=True))


if __name__ == "__main__":
    main()
