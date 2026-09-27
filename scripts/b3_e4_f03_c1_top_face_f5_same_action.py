"""Bounded F5/segmented-top-face shell-action replay; not G0 acceptance.

Only saved F5 stresses and displacements are read. No external solver runs.
The same E4 x4/y4 shell receives either validated F5 bar-on-plate action
or the native two-interval top-face action from the saved coupled solve.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import linalg

from scripts.b3_e4_f03_c3d20r_bond_force_recovery import wrench
from scripts.b3_e4_f03_c1_factor5_common_weak_work import _native_family, _project
from scripts.b3_e4_f03_factor5_shell_action import (
    STATIONS, WEIGHTS, Y, _generalized_wrench, _project_solid_action,
    _solve_shell, _top_response,
)
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_saved_six_gap_replay import _lookup, _solid_face_sample
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u
from scripts.b3_e4_f03_torque_weak_work_split import _action


BASE = Path(".qualification/b3-ge-e4-pl")
NATIVE = Path(
    "docs/agent_plans/B3_GE_E4_PL_F03_C1_TOP_FACE_SEGMENTED_DEV_20260927.json")
F5_COMMON = BASE / "f03-c1-factor5-common-weak-work-dev-20260926-v2/result.json"
F5_STRESS = BASE / "f03-c1-factor5-stiffener-ip-stress-dev-20260926-v1/solid-5-tip_mx"
F5_FIELD = BASE / "f03-ccx-c1-preopen-combined-factor5-dev-20260926-v1/solid-5-tip_mx"


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def evaluate() -> dict:
    common = json.loads(F5_COMMON.read_text())
    if "validated saved-F5 common continuous weak-action" not in common["classification"]:
        raise ValueError("validated F5 common action required")
    for name, expected in common["inputs_sha256"].items():
        if _sha(Path(name)) != expected:
            raise ValueError(f"saved F5 input changed: {name}")
    source = json.loads(NATIVE.read_text())
    native = source["result"]
    if (native["shell_nodes"] != 165 or native["e4_elements"] != 140 or
            native["beam_half_cells"] != 12 or
            (native["bond_x_cells"], native["bond_y_cells"]) != (4, 4) or
            native["plate_thickness_m"] != .035):
        raise ValueError("native x4 top-face comparison changed")
    model_path = F5_FIELD / "model.json"
    model = json.loads(model_path.read_text())
    if (model["plate_thickness_m"] != .035 or
            model["bar_tip_axis_z_m"] != .0675 or
            model["bond_interval_m"] != [.9, 1.] or
            model["bond_policy"] != "terminal" or
            model["boundary_policy"] != "left_root" or
            model["shared_interface_nodes"] != 181 or
            not model["torque_with_opening_fz"] or
            model["reverse_tip_fz"]):
        raise ValueError("F5 physical model changed")
    field_result = json.loads((F5_FIELD / "result.json").read_text())
    for name in ("model.json", "solid-5-tip_mx.frd"):
        path = F5_FIELD / name
        if _sha(path) != field_result["files_sha256"][name]:
            raise ValueError(f"saved F5 field changed: {name}")

    xyz, solid_force, elements = _action(F5_STRESS, model)
    if len(elements["Stiffener"]) != 3000:
        raise ValueError("F5 section mesh changed")
    seam = np.asarray(model["shared_interface_node_ids"], dtype=int)
    full_force = np.zeros_like(xyz)
    full_force[seam] = solid_force
    solid_wrench = wrench(full_force, xyz, seam)
    if not np.allclose(solid_wrench, common["solid_wrench_N_Nm"],
                       rtol=0., atol=1e-7):
        raise ArithmeticError("F5 recovered action changed")

    xs, ys = local_grid(4, transverse_cells=4)
    nodes = np.array([(x, y, 0.) for y in ys for x in xs])
    tangent, physical = raw_e4_tangent(xs, ys, thickness=.035)
    fixed = {6*j*len(xs)+axis for j in range(len(ys)) for axis in range(6)}
    free = np.array([i for i in range(len(tangent)) if i not in fixed])
    factor = linalg.lu_factor(tangent[np.ix_(free, free)], check_finite=True)
    solid_rows = _project_solid_action(xyz, seam, solid_force, xs, ys)
    if not np.allclose(_generalized_wrench(solid_rows, nodes), solid_wrench,
                       rtol=0., atol=1e-7):
        raise ArithmeticError("F5 top-face projection lost physical wrench")
    native_xyz, native_force, native_wrench = _native_family(
        native, "top_face_two_intervals")
    native_hat = _project(native_xyz, native_force, shell=True)
    physical_common = np.array((native_wrench[1], native_wrench[2],
                                native_wrench[3]+.0675*native_wrench[1]))
    if not np.allclose(native_hat.sum(axis=0), physical_common,
                       rtol=0., atol=1e-7):
        raise ArithmeticError("native common action lost physical work")
    native_rows = np.zeros_like(solid_rows)
    for case in native["results"]["top_face_two_intervals"]["cases"].values():
        for row in case["active_shell_nodes"]:
            index = int(row["node_row"])
            if not np.allclose(row["xyz_m"], nodes[index], rtol=0., atol=1e-12):
                raise ValueError("native shell node identity changed")
            native_rows[index] += row["force_moment_N_Nm"]
    if not np.allclose(_generalized_wrench(native_rows, nodes), native_wrench,
                       rtol=0., atol=1e-7):
        raise ArithmeticError("native top-face action lost physical wrench")

    responses = {}
    states = {}
    for label, rows in (("F5_action", solid_rows),
                        ("native_action", native_rows)):
        state, shell = _solve_shell(tangent, physical, rows, free, factor)
        shell["support_wrench_N_Nm"] = _generalized_wrench(
            shell.pop("support_rows"), nodes).tolist()
        states[label] = state
        responses[label] = shell
    cross_a = float(solid_rows.ravel() @ states["native_action"].ravel())
    cross_b = float(native_rows.ravel() @ states["F5_action"].ravel())
    if abs(cross_a-cross_b) > 1e-7:
        raise ArithmeticError("same-shell reciprocal work failed")

    u = _read_frd_u(F5_FIELD / "solid-5-tip_mx.frd")
    if set(u) != set(range(1, len(xyz))):
        raise ValueError("saved F5 face field incomplete")
    lookup = _lookup({i: xyz[i] for i in range(1, len(xyz))})
    stations = {}
    for x in STATIONS:
        solid = np.array([_solid_face_sample(lookup, u, x, y, .0175)
                          for y in Y])
        faces = {label: np.array([_top_response(state, xs, ys, x, y)
                                  for y in Y])
                 for label, state in states.items()}
        stations[str(round(x*1000))] = {
            "solid_mean_m": np.average(solid, axis=0, weights=WEIGHTS).tolist(),
            "solid_slope_z_y_rad": float((solid[-1, 2]-solid[0, 2])/.1),
            "routes": {label: {
                "mean_m": np.average(face, axis=0, weights=WEIGHTS).tolist(),
                "rms_minus_solid_m": float(np.sqrt(np.mean(np.sum(
                    (face-solid)**2, axis=1)))),
                "slope_z_y_rad": float((face[-1, 2]-face[0, 2])/.1),
            } for label, face in faces.items()},
            "native_minus_F5_action_rms_m": float(np.sqrt(np.mean(np.sum(
                (faces["native_action"]-faces["F5_action"])**2, axis=1)))),
        }
    return {
        "classification": "saved-F5/new-top-face same-Q4-shell development diagnostic; not G0B acceptance",
        "question": "Does shell idealization or connection transfer dominate the saved combined-load face difference?",
        "geometry": "same 35 mm plate, tapered C1 B3-12 axis, terminal x=.9–1 m bond and left/root supports; F5 C3D20R versus E4 Q4 x4/y4",
        "loading": "pre-opened combined +100 N m Mx -1000 N Fz; native linear influences superposed",
        "responses": responses,
        "stations": stations,
        "solid_wrench_N_Nm": solid_wrench.tolist(),
        "native_wrench_N_Nm": native_wrench.tolist(),
        "native_two_hat_action_N_N_Nm": native_hat.tolist(),
        "reciprocal_cross_work_difference_J": cross_a-cross_b,
        "limitations": [
            "F5 uses pointwise shared top-face nodes; native uses projected six-moment weak work",
            "one solid and one native grid, not convergence or connection-law acceptance",
            "F5 solid face and E4 top-face have distinct element kinematics",
            "pure torque is only a linear influence of the pre-opened combined case",
            "same-shell response separates actions but cannot alone allocate beam versus joint law",
        ],
        "inputs_sha256": {str(p): _sha(p) for p in
                          (F5_COMMON, NATIVE, model_path,
                           F5_STRESS.with_suffix(".inp"),
                           F5_STRESS.with_suffix(".dat"),
                           F5_FIELD / "solid-5-tip_mx.frd")},
        "source_sha256": _sha(Path(__file__)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"station_950": result["stations"]["950"],
                      "cross_work_error_J": result["reciprocal_cross_work_difference_J"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
