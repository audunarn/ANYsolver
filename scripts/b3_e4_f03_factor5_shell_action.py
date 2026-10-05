"""Apply saved F5 solid bond actions to the matched E4 shell alone.

The Q20 bond nodal action is pulled back by the E4 top-surface virtual
displacement map. This separates a shell response check from the native
six-channel connection. Development diagnostic; no G0B acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy import linalg

from scripts.b3_e4_f03_c3d20r_bond_force_recovery import wrench
from scripts.b3_e4_f03_local_footprint_work import structured_q4_point_shape
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_saved_six_gap_replay import _lookup, _solid_face_sample
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u
from scripts.b3_e4_f03_torque_weak_work_split import _action


STATIONS = (.9, .95, 1.)
Y = (-.05, -.025, 0., .025, .05)
WEIGHTS = np.array((.125, .25, .25, .25, .125))
FAMILIES = ("line_hybrid_p0_weighted", "line_hybrid_p1_weighted",
            "line_hybrid_dual_p1_weighted")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _generalized_wrench(rows: np.ndarray, positions: np.ndarray) -> np.ndarray:
    if rows.shape != (len(positions), 6):
        raise ValueError("nodal force/moment layout required")
    return np.r_[rows[:, :3].sum(axis=0),
                 (np.cross(positions, rows[:, :3])+rows[:, 3:]).sum(axis=0)]


def _top_response(displacements: np.ndarray, xs: np.ndarray,
                  ys: np.ndarray, x: float, y: float) -> np.ndarray:
    nodes, shape = structured_q4_point_shape(xs, ys, x, y)
    position = shape @ displacements[nodes]
    return position[:3] + np.array((.0175*position[4],
                                    -.0175*position[3], 0.))


def _project_solid_action(xyz: np.ndarray, seam: np.ndarray,
                          action: np.ndarray, xs: np.ndarray,
                          ys: np.ndarray) -> np.ndarray:
    projected = np.zeros((len(xs)*len(ys), 6))
    for node, force in zip(seam, action):
        x, y, z = xyz[node]
        if (not .9-1e-12 <= x <= 1.+1e-12 or
                not -.05-1e-12 <= y <= .05+1e-12 or
                abs(z-.0175) > 1e-12):
            raise ValueError("solid action lies outside matched E4 top patch")
        host, shape = structured_q4_point_shape(xs, ys, float(x), float(y))
        projected[host, :3] += shape[:, None]*force
        projected[host, 3] -= shape*.0175*force[1]
        projected[host, 4] += shape*.0175*force[0]
    return projected


def _solve_shell(tangent: np.ndarray, physical: np.ndarray,
                 rhs: np.ndarray, free: np.ndarray,
                 factor: tuple[np.ndarray, np.ndarray]) -> tuple[np.ndarray, dict]:
    load = rhs.ravel()
    state = np.zeros_like(load)
    state[free] = linalg.lu_solve(factor, load[free], check_finite=True)
    residual = tangent @ state - load
    relative = float(np.linalg.norm(residual[free]) /
                     max(1., np.linalg.norm(load[free])))
    if not np.isfinite(state).all() or relative > 1e-9:
        raise ArithmeticError("E4 shell-only equilibrium failed")
    physical_work = float(state @ physical @ state)
    total_work = float(load @ state)
    return state.reshape(-1, 6), {
        "free_relative_residual": relative,
        "applied_final_state_work_j": total_work,
        "physical_shell_work_j": physical_work,
        "numerical_shell_work_j": float(state @ tangent @ state-physical_work),
        "support_rows": residual.reshape(-1, 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.evidence_root.resolve()
    if root.exists():
        raise FileExistsError(root)
    base = root.parent
    combined = base / "f03-c1-factor5-stiffener-ip-stress-dev-20260926-v1/solid-5-tip_mx"
    opening = base / "f03-c1-factor5-opening-ip-stress-dev-20260926-v1/solid-5-tip_fz"
    torque = base / "f03-ccx-c1-factor5-torque-influence-dev-20260926-v1/solid-5-tip_mx/solid-5-tip_mx"
    opening_field = base / "f03-ccx-c1-factor5-opening-influence-dev-20260926-v1/solid-5-tip_fz/solid-5-tip_fz"
    combined_model_path = base / "f03-ccx-c1-preopen-combined-factor5-dev-20260926-v1/solid-5-tip_mx/model.json"
    opening_model_path = base / "f03-ccx-c1-factor5-opening-influence-dev-20260926-v1/solid-5-tip_fz/model.json"
    native_path = base / "f03-c1-factor5-matched-tip-ports-dev-20260926-v2/native-loaded.json"
    torque_recovery = base / "f03-c1-factor5-torque-weak-work-dev-20260926-v1/result.json"
    opening_recovery = base / "f03-c1-factor5-opening-weak-work-dev-20260926-v2/result.json"
    native = json.loads(native_path.read_text())
    models = [json.loads(path.read_text()) for path in
              (combined_model_path, opening_model_path)]
    recovered = [json.loads(path.read_text()) for path in
                 (torque_recovery, opening_recovery)]
    if (native["beam_half_cells"] != 12 or native["bond_x_cells"] != 2 or
            native["bond_y_cells"] != 4 or native["plate_thickness_m"] != .035 or
            any(model["shared_interface_nodes"] != 181 or
                model["bond_policy"] != "terminal" for model in models)):
        raise ValueError("saved F5/native geometry or material identity differs")
    xyz_c, action_c, elements_c = _action(combined, models[0])
    xyz_o, action_o, elements_o = _action(opening, models[1])
    if (not np.array_equal(xyz_c, xyz_o) or
            any(not np.array_equal(elements_c[k], elements_o[k])
                for k in elements_c)):
        raise ValueError("solid influence fields have different meshes")
    seam = np.array(models[0]["shared_interface_node_ids"], dtype=int)
    if seam.tolist() != models[1]["shared_interface_node_ids"]:
        raise ValueError("solid influence seam inventory differs")
    xs, ys = local_grid(2, transverse_cells=4)
    tangent, physical = raw_e4_tangent(xs, ys, thickness=.035)
    shell_nodes = np.array([(x, y, 0.) for y in ys for x in xs])
    fixed = {6*j*len(xs)+axis for j in range(len(ys)) for axis in range(6)}
    free = np.array([i for i in range(len(tangent)) if i not in fixed])
    factor = linalg.lu_factor(tangent[np.ix_(free, free)], check_finite=True)
    paths = [combined.with_suffix(s) for s in (".inp", ".dat")]
    paths += [opening.with_suffix(s) for s in (".inp", ".dat")]
    paths += [torque.with_suffix(".frd"), opening_field.with_suffix(".frd"),
              combined_model_path, opening_model_path, native_path,
              torque_recovery, opening_recovery]
    results = {}
    for label, action, field, prior in (
            ("tip_mx", action_c-action_o, torque, recovered[0]),
            ("tip_fz", action_o, opening_field, recovered[1])):
        applied = np.zeros_like(xyz_c)
        applied[seam] = action
        solid_wrench = wrench(applied, xyz_c, seam)
        expected = (prior["torque_bar_on_plate_wrench_from_independent_support_N_Nm"]
                    if label == "tip_mx" else
                    prior["opening_bar_on_plate_wrench_from_independent_support_N_Nm"])
        if np.max(np.abs(solid_wrench-expected)) > 1e-3:
            raise ArithmeticError("recovered solid bond action changed")
        projected = _project_solid_action(xyz_c, seam, action, xs, ys)
        projected_wrench = _generalized_wrench(projected, shell_nodes)
        if np.max(np.abs(projected_wrench-solid_wrench)) > 1e-7:
            raise ArithmeticError("E4 top-surface work map lost physical wrench")
        state, shell = _solve_shell(tangent, physical, projected, free, factor)
        support_wrench = _generalized_wrench(shell.pop("support_rows"),
                                             shell_nodes)
        u = _read_frd_u(field.with_suffix(".frd"))
        if set(u) != set(range(1, len(xyz_c))):
            raise ValueError("saved solid displacement field incomplete")
        node = _lookup({i: xyz_c[i] for i in range(1, len(xyz_c))})
        station_results = {}
        for x in STATIONS:
            e4 = np.array([_top_response(state, xs, ys, x, y) for y in Y])
            solid = np.array([_solid_face_sample(node, u, x, y, .0175)
                              for y in Y])
            key = str(round(x*1000))
            station_results[key] = {
                "e4_face_mean_translation_m": np.average(e4, axis=0,
                                                          weights=WEIGHTS).tolist(),
                "solid_face_mean_translation_m": np.average(solid, axis=0,
                                                             weights=WEIGHTS).tolist(),
                "e4_minus_solid_face_rms_m": float(np.sqrt(np.mean(
                    np.sum((e4-solid)**2, axis=1)))),
                "e4_face_slope_z_y_rad": float((e4[-1, 2]-e4[0, 2])/.1),
                "solid_face_slope_z_y_rad": float((solid[-1, 2]-solid[0, 2])/.1),
            }
        parity = {}
        for family in FAMILIES:
            case = native["results"][family]["cases"][label]
            native_force = np.zeros_like(projected)
            for row in case["active_shell_nodes"]:
                native_force[row["node_row"]] = row["force_moment_N_Nm"]
            native_state, _ = _solve_shell(tangent, physical, native_force,
                                           free, factor)
            errors = []
            for x in STATIONS:
                observed = np.average([_top_response(native_state, xs, ys,
                                                       x, y) for y in Y],
                                      axis=0, weights=WEIGHTS)
                saved = np.asarray(case["terminal_station_kinematics"][
                    str(round(x*1000))]["shell_top_edge_mean_translation_m"])
                errors.append(float(np.max(np.abs(observed-saved))))
            parity[family] = max(errors)
        if max(parity.values()) > 1e-8:
            raise ArithmeticError("native shell-action replay lost saved face motion")
        results[label] = {
            "solid_bar_on_plate_wrench_N_Nm": solid_wrench.tolist(),
            "e4_projected_wrench_N_Nm": projected_wrench.tolist(),
            "e4_support_wrench_N_Nm": support_wrench.tolist(),
            "shell_work": shell,
            "station_faces": station_results,
            "native_action_shell_replay_max_difference_m": parity,
        }
        print(label, "max native shell replay error", max(parity.values()),
              "tip mean E4-solid", np.array(station_results["1000"][
                  "e4_face_mean_translation_m"])-np.array(station_results["1000"][
                  "solid_face_mean_translation_m"]), flush=True)
    result = {
        "classification": "bounded F5 solid-action-to-E4 shell-only work diagnostic; no G0B acceptance",
        "question": "Does E4 under the same recovered solid bond action reproduce solid plate-face motion, or does the shell idealization contribute to the coupled discrepancy?",
        "outcome_rule": "Close shell-only face agreement shifts the next discriminator to native retained line trace/enforcement; material shell-only disagreement requires shell idealization review before changing that law. Neither selects P0/P1/dual.",
        "work_map": "Q20 solid bond nodal action pulled back by E4 Q4 top-surface δu=(δux+zδry,δuy-zδrx,δuz), z=.0175 m",
        "geometry": "C1 F5 35mm solid plate and native Q4 x2/y4 E4 shell, left edge fixed, terminal x=.9–1m y=±.05m bond action; torque is combined-minus-opening linear influence",
        "results": results,
        "limits": ["F5 solid and E4 shell differ in kinematics and mesh; one solid level",
                   "pure torque is a contact-inadmissible influence, not standalone contact",
                   "solid weak nodal action is not pointwise traction density",
                   "linearized shell-only response is diagnostic, not coupled mechanics acceptance"],
        "inputs_sha256": {str(path.relative_to(base)): _sha(path) for path in paths},
        "runner_sha256": _sha(Path(__file__)),
    }
    root.mkdir(parents=True)
    (root / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
