"""Project the saved C1 F5 opening bond action onto rigid solid sections.

The opening force is a standalone separated-face linear reference. This
final-state force/displacement pairing is not path-integrated energy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c3d20r_bond_force_recovery import wrench
from scripts.b3_e4_f03_saved_six_gap_replay import _ports
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u
from scripts.b3_e4_f03_torque_weak_work_split import _action, _predict, _work


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
    stem = base / "f03-c1-factor5-opening-ip-stress-dev-20260926-v1/solid-5-tip_fz"
    model_path = base / "f03-ccx-c1-factor5-opening-influence-dev-20260926-v1/solid-5-tip_fz/model.json"
    result_path = base / "f03-ccx-c1-factor5-opening-influence-dev-20260926-v1/result.json"
    recovery_path = base / "f03-c1-factor5-opening-stress-force-recovery-dev-20260926-v1/result.json"
    model = json.loads(model_path.read_text())
    saved = json.loads(result_path.read_text())[0]
    recovery = json.loads(recovery_path.read_text())
    definition = saved["model"]
    if (saved["status"] != "EXPLORATORY_COMPLETE" or
            recovery["validation"]["status"] != "PASSED_SAVED_STATE_AND_WEAK_FORCE_CHECKS" or
            definition["factor"] != 5 or
            definition["plate_thickness_m"] != .035 or
            definition["bond_interval_m"] != [.9, 1.] or
            definition["boundary_policy"] != "left_root" or
            definition["bond_policy"] != "terminal" or
            definition["contact_policy"] != "none" or
            definition["bar_reference_profile"] != "C1_TWO_QUADRATIC_TANGENT_ALIGNED_V1" or
            definition["tip_load_map"] != "quadratic_face" or
            definition["bar_clearance_um"] != 2 or
            definition["element_family"] != "C3D20R" or
            np.max(np.abs(np.asarray(saved["response"]["applied_wrench_N_Nm"])-
                          np.array((0., 0., -1000., 0., 1000., 0.)))) > 1e-9):
        raise ValueError("unmatched validated C1 F5 opening reference")
    xyz, action, elements = _action(stem, model)
    seam = np.array(model["shared_interface_node_ids"], dtype=int)
    complete_action = np.zeros_like(xyz)
    complete_action[seam] = action
    integrated = wrench(complete_action, xyz, seam)
    reference = np.asarray(recovery["reconstruction"]["bar_on_plate_support_wrench_N_Nm"])
    difference = float(np.max(np.abs(integrated-reference)))
    if difference >= 1e-3:
        raise ArithmeticError("opening bond action differs from independent support")
    u = _read_frd_u(stem.with_suffix(".frd"))
    if set(u) != set(range(1, len(xyz))):
        raise ValueError("saved opening displacement inventory incomplete")
    actual = np.array([u[int(node)] for node in seam])
    coords = {node: xyz[node] for node in range(1, len(xyz))}
    reports = {}
    for method in ("area", "nonbond"):
        translation, rotation, fit_rms = _ports(coords, u, elements, method=method)
        projected = _predict(xyz[seam], translation, rotation)
        reports[method] = {"work": _work(action, actual, projected),
                           "section_vector_rms_fit_m": fit_rms.tolist()}
    paths = [stem.with_suffix(suffix) for suffix in (".inp", ".dat", ".frd")]
    paths += [model_path, result_path, recovery_path]
    result = {
        "classification": "bounded saved opening weak-action and port projection; no G0B acceptance",
        "question": "Is the rigid-section projection remainder specific to torque or also material under the physically opening transverse force?",
        "outcome_rule": "A small opening remainder relative to torque narrows the next section check to torsion/end loading; a similar remainder points to a broader section/port reduction. Neither outcome selects a line multiplier space.",
        "case": "C1 F5 35 mm plate, 100 mm square bar, terminal x=.9–1 m bond, −1000 N opening end-face Fz, left plate-edge and beam-root supports; its +1000 Nm My wrench about the global origin comes from the load lever arm, not an additional couple",
        "opening_bar_on_plate_wrench_from_stress_N_Nm": integrated.tolist(),
        "opening_bar_on_plate_wrench_from_independent_support_N_Nm": reference.tolist(),
        "maximum_wrench_difference_N_Nm": difference,
        "projection": reports,
        "limits": ["final-state bilinear pairing, not path energy",
                   "solid rigid-section fit is not the native B3 retained port",
                   "one F5 mesh and one opening load do not qualify a law"],
        "inputs_sha256": {str(path.relative_to(base)): _sha(path) for path in paths},
        "runner_sha256": _sha(Path(__file__)),
    }
    root.mkdir(parents=True)
    (root / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    for method, report in reports.items():
        print(method, report["work"])


if __name__ == "__main__":
    main()
