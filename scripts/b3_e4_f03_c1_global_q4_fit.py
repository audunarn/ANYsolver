"""Fit saved solid plate faces to one clamped Q4 shell field, then audit line work.

Development diagnostic only. The least-squares displacement fit is not
an energy projection and does not establish an interface law or inf-sup.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import lsqr, splu

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts.b3_e4_f03_c1_material_line_p0_reference import integrated_rows
from scripts.b3_e4_f03_ccx_six_channel_compliance import _source
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_local_footprint_work import structured_q4_point_shape
from scripts.b3_e4_f03_material_line_position import MaterialLinePosition
from scripts.b3_e4_f03_material_line_space_screen import _rows
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


THICKNESS = .035
CHANNELS = ("Fx", "Fy", "Fz", "Mx", "My", "Mz")


def fit_matrix(coords, face_nodes, xs, ys):
    """Map free Q4 translations and thickness-scaled rx/ry to face u."""
    free = {(j*len(xs)+i, c): 5*index+c
            for index, (j, i) in enumerate(
                (j, i) for j in range(len(ys))
                for i, x in enumerate(xs) if abs(x+.5) >= 1e-12)
            for c in range(5)}
    rr, cc, vv = [], [], []
    for index, node in enumerate(face_nodes):
        x, y, z = coords[node]
        support, shape = structured_q4_point_shape(xs, ys, x, y)
        for shell_node, weight in zip(support, shape):
            shell_node = int(shell_node)
            terms = (
                ((0, 0, weight), (0, 4, weight*z/THICKNESS)),
                ((1, 1, weight), (1, 3, -weight*z/THICKNESS)),
                ((2, 2, weight),),
            )
            for row_terms in terms:
                for row_component, q_component, value in row_terms:
                    key = (shell_node, q_component)
                    if key in free:
                        rr.append(3*index+row_component)
                        cc.append(free[key])
                        vv.append(float(value))
    matrix = sparse.coo_matrix((vv, (rr, cc)),
                               shape=(3*len(face_nodes), len(free))).tocsr()
    if matrix.shape[1] != 5*(len(xs)-1)*len(ys):
        raise ArithmeticError("clamped Q4 fit layout changed")
    return matrix, free


def fit_field(matrix, free, displacement, shell_count):
    target = np.asarray(displacement).ravel()
    if target.shape != (matrix.shape[0],) or not np.isfinite(target).all():
        raise ValueError("finite full face displacement required")
    fit = lsqr(matrix, target, atol=1e-12, btol=1e-12, iter_lim=2000)
    if fit[1] not in (1, 2) or not np.isfinite(fit[0]).all():
        raise ArithmeticError(f"global Q4 fit did not converge: {fit[1:4]}")
    q = np.zeros((shell_count, 6))
    for (node, component), column in free.items():
        q[node, component if component < 3 else component] = (
            fit[0][column] if component < 3 else fit[0][column]/THICKNESS)
    error = (matrix@fit[0]-target).reshape(-1, 3)
    return q.ravel(), {
        "iterations": int(fit[2]),
        "lsqr_status": int(fit[1]),
        "face_displacement_rms_m": float(np.sqrt(np.mean(target**2))),
        "fit_component_rms_m": float(np.sqrt(np.mean(error**2))),
        "fit_component_max_abs_m": float(np.max(np.abs(error))),
        "fitted_free_variables": matrix.shape[1],
        "face_displacement_components": matrix.shape[0],
    }


def trace_matrices(position, orientation, stations, free, shell_size):
    """Pointwise and integrated native shell trace maps in fit coordinates."""
    point = np.zeros((len(stations), 6, len(free)))
    for j in range(len(stations)):
        jacobian = np.vstack((position[j, :, :shell_size],
                              orientation[j, :, :shell_size]))
        for (node, component), column in free.items():
            point[j, :, column] = jacobian[:, 6*node+component]/(
                THICKNESS if component >= 3 else 1.)
    integrated = np.zeros((4, 6, len(free)))
    for j, station in enumerate(stations):
        integrated[j//3] += station.weight*point[j]
    return point.reshape(-1, len(free)), integrated.reshape(-1, len(free))


def constrained_trace_fit(matrix, free, q, solid_points, stations,
                          station_matrix, integrated_matrix, face_u, dual):
    """Compare exact weak-row matching with best station trace residual."""
    p0 = np.zeros(len(free))
    for (node, component), column in free.items():
        p0[column] = q[6*node+component]*(
            THICKNESS if component >= 3 else 1.)
    target = np.asarray(face_u).ravel()
    solid_integrated = np.zeros((4, 6))
    for j, value in enumerate(solid_points):
        solid_integrated[j//3] += stations[j].weight*value
    length = .1
    row_scale = np.tile((1., 1., 1., length, length, length), 4)
    constraint = integrated_matrix*row_scale[:, None]
    gap = solid_integrated.ravel()*row_scale
    left, singular_weak, _ = np.linalg.svd(constraint, full_matrices=False)
    weak_rank = int(np.sum(singular_weak > 1e-10))
    if weak_rank <= 0:
        raise ArithmeticError("zero native shell weak-row rank")
    reachable = left[:, :weak_rank]
    unreachable = left[:, weak_rank:]@(
        left[:, weak_rank:].T@gap)
    independent = reachable.T@constraint
    independent_gap = reachable.T@gap
    normal = (matrix.T@matrix).tocsc()
    factor = splu(normal)
    influence = factor.solve(independent.T)
    schur = independent@influence
    correction = influence@np.linalg.solve(
        schur, independent_gap-independent@p0)
    constrained = p0+correction
    weak_residual = constraint@constrained-gap
    if np.max(np.abs(weak_residual+unreachable)) > 1e-10:
        raise ArithmeticError("reachable Q4 weak rows did not match")
    initial_face_error = matrix@p0-target
    constrained_face_error = matrix@constrained-target
    point_scale = np.tile((1., 1., 1., length, length, length),
                          len(stations))
    point_operator = station_matrix*point_scale[:, None]
    point_target = np.asarray(solid_points).ravel()*point_scale
    best, _, rank, singular = np.linalg.lstsq(
        point_operator, point_target, rcond=1e-10)
    best_residual = (point_operator@best-point_target).reshape(-1, 6)
    constrained_residual = (
        point_operator@constrained-point_target).reshape(-1, 6)
    physical_weak_residual = weak_residual/row_scale
    if np.asarray(dual).shape != (24,):
        raise ValueError("fixed 24-row physical dual required")
    return {
        "weak_row_constrained_face_rms_m": float(np.sqrt(np.mean(
            constrained_face_error**2))),
        "unconstrained_face_rms_m": float(np.sqrt(np.mean(initial_face_error**2))),
        "weak_row_constrained_face_max_abs_m": float(np.max(np.abs(
            constrained_face_error))),
        "weak_row_rank": weak_rank,
        "weak_row_count": int(constraint.shape[0]),
        "weak_row_rank_tolerance_m": 1e-10,
        "scaled_weak_unreachable_component_rms_m2": float(np.sqrt(
            np.mean(unreachable**2))),
        "scaled_weak_unreachable_component_max_abs_m2": float(np.max(
            np.abs(unreachable))),
        "scaled_weak_row_actual_max_defect_m2": float(np.max(
            np.abs(weak_residual))),
        "scaled_reachable_weak_row_max_defect_m2": float(np.max(np.abs(
            weak_residual+unreachable))),
        "physical_integrated_weak_row_residual": physical_weak_residual.tolist(),
        "physical_integrated_weak_row_units": ["m2", "m2", "m2",
                                               "rad_m", "rad_m", "rad_m"]*4,
        "native_minus_solid_weak_work_J": float(
            -np.asarray(dual)@physical_weak_residual),
        "weak_row_schur_condition": float(np.linalg.cond(schur)),
        "station_map_rank": int(rank),
        "station_map_rows": int(point_operator.shape[0]),
        "station_map_smallest_nonzero_singular": float(singular[rank-1]),
        "minimum_scaled_station_component_rms_m": float(np.sqrt(np.mean(
            best_residual**2))),
        "minimum_scaled_station_component_max_abs_m": float(np.max(np.abs(
            best_residual))),
        "weak_constrained_scaled_station_component_rms_m": float(np.sqrt(
            np.mean(constrained_residual**2))),
        "minimum_scaled_station_abs_max_by_channel_m": np.max(
            np.abs(best_residual), axis=0).tolist(),
    }


def evaluate(reconstruction_path: Path, same_action_path: Path,
             prior_projection_path: Path) -> dict:
    reconstruction = json.loads(reconstruction_path.read_text())
    same_action = json.loads(same_action_path.read_text())
    prior = json.loads(prior_projection_path.read_text())
    if (reconstruction["status"] != "EXPLORATORY_COMPLETE" or
            same_action["solid_reconstruction_sha256"] != digest(reconstruction_path) or
            prior["solid_reconstruction_sha256"] != digest(reconstruction_path) or
            prior["same_action_sha256"] != digest(same_action_path)):
        raise ValueError("saved reference identities changed")
    deck, _, coords, _, _, _ = _source(Path(reconstruction["source_root"])/"tip_mx")
    if digest(deck) != same_action["solid_source_deck_sha256"]:
        raise ValueError("saved solid deck changed")
    plate, bar = _element_domain_nodes(deck)
    solid_nodes, solid_rows, point_ports = integrated_rows(coords, plate, bar)
    face_nodes = tuple(sorted(node for node in plate
                              if abs(abs(coords[node][2])-THICKNESS/2) < 1e-10))
    if not face_nodes or not set(solid_nodes)&set(face_nodes):
        raise ValueError("solid plate faces missing")
    all_nodes = tuple(sorted(set(face_nodes)|set(solid_nodes)))
    all_index = {node: i for i, node in enumerate(all_nodes)}
    xs, ys = local_grid(4, transverse_cells=4)
    matrix, free = fit_matrix(coords, face_nodes, xs, ys)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um", assemble=False)
    line = MaterialLinePosition(xs, ys, beam)
    if len(line.stations) != 12:
        raise ValueError("native Gauss inventory changed")
    count = len(line.stations)
    position = line.reference_jacobian().reshape(count, 3, -1)
    orientation = line.reference_orientation_jacobian().reshape(count, 3, -1)
    shell_size = 6*line.shell_count
    native_rows, interval_measure = _rows(
        line, LineMultiplierSpace("piecewise_constant", tuple(np.linspace(0., 1., 5))))
    station_matrix, integrated_matrix = trace_matrices(
        position, orientation, line.stations, free, shell_size)
    dual = {label: np.asarray(reconstruction["cases"][label][
        "dual_physical_line_density"]) for label in ("tip_mx", "tip_fz")}
    scale = np.array([40000. if j%6 < 3 else 4000. for j in range(24)])
    responses = {label: np.zeros((len(all_nodes), 3)) for label in dual}
    for j, record in enumerate(reconstruction["unit_records"]):
        if record["channel"] != j:
            raise ValueError("unit response order changed")
        frd = Path(reconstruction["response_root"])/f"channel-{j}"/f"material-line-p0-{j}.frd"
        if digest(frd) != record["frd_sha256"]:
            raise ValueError("unit response changed")
        field = _read_frd_u(frd)
        if not set(all_nodes) <= set(field):
            raise ValueError("unit response is missing face nodes")
        values = np.array([field[node] for node in all_nodes])
        for label in dual:
            responses[label] -= (dual[label][j]/scale[j])*values
    cases = {}
    for label, displacement in responses.items():
        face_u = np.array([displacement[all_index[node]] for node in face_nodes])
        q, fit = fit_field(matrix, free, face_u, line.shell_count)
        solid_rows_integrated = np.zeros((4, 6))
        native_rows_integrated = np.zeros((4, 6))
        maximum_pointwise = np.zeros(6)
        station_rows = []
        solid_points = []
        for interval_index, interval in enumerate(point_ports):
            for local_index, (weight, port) in enumerate(interval):
                j = 3*interval_index+local_index
                if (abs(port.station_x_m-line.stations[j].x) > 1e-12 or
                        abs(weight-line.stations[j].weight) > 1e-12):
                    raise ArithmeticError("solid/native quadrature differs")
                port_u = np.array([displacement[all_index[node]]
                                   for node in port.node_ids]).ravel()
                solid_trace = np.r_[port.shell_top_jacobian@port_u,
                                    -port.shell_orientation_jacobian@port_u]
                solid_points.append(solid_trace)
                native_trace = np.r_[position[j, :, :shell_size]@q,
                                     orientation[j, :, :shell_size]@q]
                residual = solid_trace-native_trace
                maximum_pointwise = np.maximum(maximum_pointwise, np.abs(residual))
                solid_rows_integrated[interval_index] += weight*solid_trace
                native_rows_integrated[interval_index] += weight*native_trace
                station_rows.append({"x_m": float(port.station_x_m),
                                     "six_channel_solid_minus_native": residual.tolist()})
        solid_work = float(-np.sum(dual[label].reshape(4, 6)*solid_rows_integrated))
        fitted_work = float(-np.sum(dual[label].reshape(4, 6)*native_rows_integrated))
        native_force = -(native_rows.T@(
            dual[label].reshape(4, 6)*interval_measure[:, None]).ravel())[:shell_size]
        if abs(fitted_work-float(native_force@q)) > 1e-9:
            raise ArithmeticError("native station work does not match assembled rows")
        saved_work = same_action["cases"][label]["solid_shell_action_only_work_J"]
        if abs(solid_work-saved_work) > 1e-9:
            raise ArithmeticError("solid station work does not reproduce saved plate work")
        by_channel = -np.sum(dual[label].reshape(4, 6)*(
            solid_rows_integrated-native_rows_integrated), axis=0)
        if abs(float(np.sum(by_channel))-(solid_work-fitted_work)) > 1e-10:
            raise ArithmeticError("station work decomposition failed")
        trace_fit = constrained_trace_fit(
            matrix, free, q, solid_points, line.stations,
            station_matrix, integrated_matrix, face_u, dual[label])
        cases[label] = {
            "fit": fit,
            "trace_fit": trace_fit,
            "solid_plate_work_J": solid_work,
            "fitted_Q4_trace_work_J": fitted_work,
            "solid_minus_fitted_work_J": solid_work-fitted_work,
            "solid_minus_fitted_work_by_channel_J": by_channel.tolist(),
            "maximum_abs_pointwise_trace_residual_by_channel": maximum_pointwise.tolist(),
            "integrated_solid_trace": solid_rows_integrated.tolist(),
            "integrated_fitted_Q4_trace": native_rows_integrated.tolist(),
            "gauss_station_residuals": station_rows,
            "five_node_sample_work_J": prior["cases"][label][
                "solid_to_native_trace_projection"]["full_action"][
                    "projected_native_trace_action_work_J"],
        }
    return {
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "classification": "global displacement-fit and station-wise line-trace work",
        "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                                 text=True).strip(),
        "solid_reconstruction_sha256": digest(reconstruction_path),
        "same_action_sha256": digest(same_action_path),
        "prior_projection_sha256": digest(prior_projection_path),
        "solid_source_deck_sha256": digest(deck),
        "face_node_count": len(face_nodes),
        "fit_matrix_nnz": matrix.nnz,
        "channel_order": CHANNELS,
        "cases": cases,
        "limitations": [
            "equal face-node least squares is not an area- or energy-weighted projection",
            "only saved linear plate responses and the bounded Q4 candidate",
            "station trace/work differences do not establish the physical connection law",
            "not F03, G0B or multiplier-space acceptance",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reconstruction", type=Path, required=True)
    parser.add_argument("--same-action", type=Path, required=True)
    parser.add_argument("--prior-projection", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve prior global fit result")
    result = evaluate(args.reconstruction.resolve(), args.same_action.resolve(),
                      args.prior_projection.resolve())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({key: {"work_J": value["solid_minus_fitted_work_J"],
                            "fit_rms_m": value["fit"]["fit_component_rms_m"]}
                      for key, value in result["cases"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
