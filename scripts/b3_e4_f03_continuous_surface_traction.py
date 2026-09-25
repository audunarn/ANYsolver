"""Bounded physical-traction screen for the native B3/E4 surface line.

The multiplier is a continuous P1 force traction along the bonded length,
constant across its width, plus a P1 transverse antisymmetric traction that
can carry torque. Its global wrench span has six channels. This is a position-
work diagnostic, not a selected six-component local pose or multiplier space.
"""

from __future__ import annotations

import numpy as np
from scipy import linalg

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts.b3_e4_f03_local_footprint_work import (
    bond_x_segments, distributed_surface_patch_trace, skew,
    structured_q4_point_shape,
)
from scripts.b3_e4_f03_plate_patch_work import raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


WIDTH = .1
HALF_WIDTH = WIDTH / 2


def continuous_traction_rows(xs: np.ndarray, ys: np.ndarray, beam, *,
                             plate_thickness: float = .035,
                             intervals: int = 4,
                             local_yaw: bool = False,
                             six_local_resultants: bool = False,
                             line_kind: str = "continuous_linear"
                             ) -> tuple[np.ndarray, np.ndarray, dict]:
    """Integrate work rows and their physical six-resultant wrench map.

    A row dual is a physical force or torque at one line basis station. The
    direct traction field is applied to E4 top-surface positions and the same
    field, with opposite sign, to native retained B3 bottom-surface positions.
    The two line-hat force tractions vary continuously in x; the transverse
    antisymmetric z traction is normalized to one unit Mx. Bending/yaw moments
    are available through distributed force resultants, not independent local
    moment rows. ``local_yaw`` adds one physical in-plane force dipole.
    ``six_local_resultants`` instead adds independent longitudinal Fz and
    balanced in-plane polar force couples, giving local My and Mz. Their
    moments are normalized about each line-hat's physical area centroid.
    No E4 drilling coordinate participates.
    """
    xs, ys = np.asarray(xs, dtype=float), np.asarray(ys, dtype=float)
    if (plate_thickness != .035 or type(intervals) is not int or
            type(local_yaw) is not bool or
            type(six_local_resultants) is not bool or
            (local_yaw and six_local_resultants) or
            line_kind not in ("continuous_linear", "piecewise_constant") or
            (line_kind == "piecewise_constant" and
             not six_local_resultants) or
            intervals not in (2, 4, 8) or xs.ndim != 1 or ys.ndim != 1 or
            not np.isfinite(xs).all() or not np.isfinite(ys).all() or
            not np.all(np.diff(xs) > 0) or not np.all(np.diff(ys) > 0) or
            xs[0] > 0 or xs[-1] < 1 or ys[0] > -HALF_WIDTH or
            ys[-1] < HALF_WIDTH):
        raise ValueError("bounded, covered 35 mm physical strip required")
    shell_size = 6 * len(xs) * len(ys)
    total = shell_size + beam.context.count
    channels = 6 if six_local_resultants else 5 if local_yaw else 4
    station_count = (intervals if line_kind == "piecewise_constant"
                     else intervals + 1)
    count = channels * station_count
    rows = np.zeros((count, total))
    wrench = np.zeros((6, count))
    reference_gap = 0.
    area = 0.
    base = beam.context.initial.mechanical
    roots, weights = np.polynomial.legendre.leggauss(3)
    x_cuts = sorted({0., 1., *(float(x) for x in xs if 0 < x < 1),
                     *(k / beam.n_half_cells for k in range(1, beam.n_half_cells)),
                     *(k / intervals for k in range(1, intervals))})
    y_cuts = sorted({-HALF_WIDTH, HALF_WIDTH,
                     *(float(y) for y in ys if -HALF_WIDTH < y < HALF_WIDTH)})
    station_length = np.full(station_count, 1 / intervals)
    if line_kind == "continuous_linear":
        station_length[[0, -1]] *= .5
    station_area = WIDTH * station_length
    station_y_inertia = WIDTH**3 / 12 * station_length
    interval_length = 1 / intervals
    if line_kind == "piecewise_constant":
        station_x_centroid = ((np.arange(intervals) + .5) /
                              intervals)
        station_x_variance = np.full(intervals, interval_length**2 / 12)
    else:
        station_x_centroid = np.linspace(0., 1., intervals + 1)
        station_x_centroid[0] = interval_length / 3
        station_x_centroid[-1] = 1 - interval_length / 3
        station_x_variance = np.full(intervals + 1,
                                     interval_length**2 / 6)
        station_x_variance[[0, -1]] = interval_length**2 / 18
    station_x_inertia = station_area * station_x_variance
    station_polar_inertia = station_x_inertia + station_y_inertia

    for x0, x1 in zip(x_cuts[:-1], x_cuts[1:]):
        if x1 <= x0:
            continue
        # Retain the native segmentation guard even when cuts coincide.
        for bx0, bx1 in bond_x_segments(x0, x1, beam.n_half_cells):
            for xi, wx in zip(roots, weights):
                x = (bx0 + bx1) / 2 + float(xi) * (bx1 - bx0) / 2
                cell = min(int(x * intervals), intervals - 1)
                tau = intervals * x - cell
                hats = (((cell, 1.),) if line_kind == "piecewise_constant"
                        else ((cell, 1 - tau), (cell + 1, tau)))
                element, half, fraction, _ = beam._locate(x)
                port = NativeHalfCellSpatialPort(
                    beam.context, element, half, fraction)
                high, low, frame = port.pose_pair(base)
                center = high + low
                tangent = port.tangent(base)
                for y0, y1 in zip(y_cuts[:-1], y_cuts[1:]):
                    for eta, wy in zip(roots, weights):
                        y = (y0 + y1) / 2 + float(eta) * (y1 - y0) / 2
                        weight = float(wx * wy) * (bx1 - bx0) * (y1 - y0) / 4
                        shell_nodes, shape = structured_q4_point_shape(xs, ys, x, y)
                        shell_point = np.array((x, y, plate_thickness / 2))
                        offset = np.array((0., y, -HALF_WIDTH))
                        beam_point = center + frame @ offset
                        reference_gap = max(reference_gap, float(
                            np.linalg.norm(shell_point - beam_point)))
                        dg = np.zeros((3, total))
                        for node, value in zip(shell_nodes, shape):
                            start = 6 * int(node)
                            dg[:, start:start + 3] += value * np.eye(3)
                            dg[:, start + 3:start + 6] -= (
                                value * plate_thickness / 2 *
                                skew(np.array((0., 0., 1.))))
                        dg[:, shell_size:] -= (
                            np.column_stack((np.eye(3), -skew(offset))) @ tangent)
                        for station, hat in hats:
                            profiles = (np.array((1., 0., 0.)) * hat / station_area[station],
                                        np.array((0., 1., 0.)) * hat / station_area[station],
                                        np.array((0., 0., 1.)) * hat / station_area[station],
                                        np.array((0., 0., 1.)) *
                                        hat * y / station_y_inertia[station])
                            if local_yaw:
                                profiles += (np.array((-1., 0., 0.)) *
                                             hat * y / station_y_inertia[station],)
                            if six_local_resultants:
                                dx = x - station_x_centroid[station]
                                profiles += (
                                    np.array((0., 0., -1.)) * hat * dx /
                                    station_x_inertia[station],
                                    np.array((-y, dx, 0.)) * hat /
                                    station_polar_inertia[station],
                                )
                            for channel, traction in enumerate(profiles):
                                row = channels * station + channel
                                rows[row] += weight * traction @ dg
                                wrench[:3, row] += weight * traction
                                wrench[3:, row] += weight * np.cross(shell_point, traction)
                        area += weight
    wrench_scales = np.array((1000., 1000., 1000., 100., 100., 100.))
    if (abs(area - WIDTH) > 1e-12 or reference_gap > 1e-11 or
            np.max(np.abs(rows[:, 5:shell_size:6])) > 1e-14 or
            np.linalg.matrix_rank(wrench / wrench_scales[:, None]) != 6):
        raise ArithmeticError("physical traction reference, drilling or wrench span failed")
    local_wrench_error = None
    if six_local_resultants:
        local_wrench_error = 0.
        for station in range(station_count):
            local = wrench[:, 6*station:6*station+6].copy()
            center = np.array((station_x_centroid[station], 0.,
                               plate_thickness / 2))
            local[3:] -= np.cross(center, local[:3].T).T
            local_wrench_error = max(local_wrench_error, float(
                np.max(np.abs(local - np.eye(6)))))
        if local_wrench_error > 1e-10:
            raise ArithmeticError("six local physical wrenches failed")
    return rows, wrench, {"reference_gap_m": reference_gap,
                          "bond_area_m2": area,
                          "global_wrench_rank": 6,
                          "local_section_wrench_rank": channels,
                          "local_yaw_force_dipole": local_yaw,
                          "six_local_resultants": six_local_resultants,
                          "line_kind": line_kind,
                          "six_local_wrench_identity_error": local_wrench_error,
                          "wrench_scales_N_Nm": wrench_scales.tolist(),
                          "row_count": count,
                          "station_area_m2": station_area.tolist(),
                          "station_y_inertia_m4": station_y_inertia.tolist(),
                          "station_x_centroid_m": station_x_centroid.tolist(),
                          "station_x_inertia_m4": station_x_inertia.tolist()}


def _common_rigid_direction(xs: np.ndarray, ys: np.ndarray, beam,
                            translation: np.ndarray,
                            rotation: np.ndarray) -> np.ndarray:
    shell_count = len(xs) * len(ys)
    shell = np.zeros((shell_count, 6))
    for node, (x, y) in enumerate((x, y) for y in ys for x in xs):
        shell[node, :3] = translation + np.cross(rotation, (x, y, 0.))
        shell[node, 3:] = rotation
    retained = np.zeros(beam.context.count)
    state = beam.context.initial.mechanical
    for node, position in enumerate(state.positions + state.position_low):
        retained[6 * node:6 * node + 3] = translation + np.cross(rotation, position)
        retained[6 * node + 3:6 * node + 6] = rotation
    for element in range(len(beam.context.elements)):
        start = beam.context.nodal_count + 24 * element
        retained[start:start + 6] = np.tile(rotation, 2)
    return np.concatenate((shell.reshape(-1), retained))


def bounded_continuous_traction_screen(*, shell_x: int = 8,
                                       shell_y: int = 8,
                                       beam_half_cells: int = 16,
                                       intervals: tuple[int, ...] = (2, 4, 8),
                                       local_yaw: bool = False,
                                       six_local_resultants: bool = False,
                                       line_kind: str = "continuous_linear"
                                       ) -> list[dict]:
    """Solve the same native torque/shear case with a distinct traction basis."""
    if (shell_x not in (8, 16) or shell_y not in (4, 8, 16) or
            beam_half_cells not in (8, 16) or type(local_yaw) is not bool or
            type(six_local_resultants) is not bool or
            (local_yaw and six_local_resultants) or
            line_kind not in ("continuous_linear", "piecewise_constant") or
            (line_kind == "piecewise_constant" and
             not six_local_resultants) or
            not intervals or
            any(n not in (2, 4, 8) for n in intervals)):
        raise ValueError("bounded shell, beam and line resolutions required")
    xs = np.linspace(-.5, 1.5, shell_x + 1)
    ys = np.linspace(-.5, .5, shell_y + 1)
    shell_k, shell_physical = raw_e4_tangent(xs, ys, thickness=.035)
    beam = build(beam_half_cells, z_offset=.0675,
                 torsion_constant=square_torsion_constant())
    beam_k = beam.tangent.toarray()
    shell_size = len(shell_k)
    total = shell_size + beam.context.count
    if total > 1900:
        raise ValueError("dense traction oracle exceeds 1900 primal rows")
    primal = linalg.block_diag(shell_k, beam_k)
    fixed_shell = {6 * j * (shell_x + 1) + axis for j in range(shell_y + 1)
                   for axis in range(6)}
    fixed_beam = {shell_size + index for index in beam.context.fixed}
    free = np.array([i for i in range(total)
                     if i not in fixed_shell and i not in fixed_beam])
    factor = linalg.lu_factor(primal[np.ix_(free, free)])
    tip = shell_size + 6 * beam_half_cells
    shell_nodes = np.array([(x, y, 0.) for y in ys for x in xs])
    beam_root = np.array((0., 0., .0675))
    rigid = _common_rigid_direction(xs, ys, beam,
                                    np.array((.02, -.03, .04)),
                                    np.array((.003, -.005, .007)))
    results = []
    for n in intervals:
        rows, wrench, meta = continuous_traction_rows(
            xs, ys, beam, intervals=n, local_yaw=local_yaw,
            six_local_resultants=six_local_resultants,
            line_kind=line_kind)
        rigid_gap = float(np.max(np.abs(rows @ rigid)))
        global_rows, _ = distributed_surface_patch_trace(
            xs, ys, beam, plate_thickness=.035, x_interval=(0., 1.))
        partition = np.array(meta["station_area_m2"]) / WIDTH
        inertia = np.array(meta["station_y_inertia_m4"])
        inertia /= inertia.sum()
        channels = meta["local_section_wrench_rank"]
        reconstructed = np.vstack((
            *(sum(partition[j] * rows[channels * j + channel]
                   for j in range(len(partition))) for channel in range(3)),
            sum(inertia[j] * rows[channels * j + 3]
                for j in range(len(partition))),
        ))
        global_row_error = float(np.max(np.abs(reconstructed - global_rows[:4])))
        if rigid_gap > 1e-10 or global_row_error > 1e-10:
            raise ArithmeticError("traction work disagrees with rigid/global oracle")
        constrained = rows[:, free]
        rank = int(np.linalg.matrix_rank(constrained))
        if rank != len(rows):
            results.append({"status": "RANK_DEFICIENT_NO_SOLVE",
                            "shell_elements_xy": [shell_x, shell_y],
                            "beam_half_cells": beam_half_cells,
                            "line_intervals": n,
                            "constraint_rank": rank,
                            "constraint_rows": len(rows),
                            "rigid_gap": rigid_gap,
                            "global_row_error": global_row_error,
                            **meta})
            continue
        inverse_rows = linalg.lu_solve(factor, constrained.T)
        compliance = constrained @ inverse_rows
        skew_error = float(np.linalg.norm(compliance - compliance.T) /
                           max(np.linalg.norm(compliance), 1e-30))
        if skew_error > 1e-8:
            raise ArithmeticError("traction compliance is nonsymmetric")
        loaded = {}
        for name, dof, amplitude in (("torque_mx_100nm", tip + 3, 100.),
                                     ("shear_fz_1000n", tip + 2, 1000.)):
            force = np.zeros(total)
            force[dof] = amplitude
            unconstrained = linalg.lu_solve(factor, force[free])
            multiplier = linalg.solve(
                compliance, constrained @ unconstrained, assume_a="gen")
            displacement = np.zeros(total)
            displacement[free] = (unconstrained - inverse_rows @ multiplier)
            residual = primal @ displacement + rows.T @ multiplier - force
            gap = rows @ displacement
            work = float(force @ displacement)
            stiffness_work = float(displacement @ primal @ displacement)
            shell_work = float(displacement[:shell_size] @ shell_k @
                               displacement[:shell_size])
            physical_shell_work = float(displacement[:shell_size] @
                                        shell_physical @ displacement[:shell_size])
            shell_reactions = residual[:shell_size].reshape(-1, 6)
            root_reaction = residual[shell_size:shell_size + 6]
            support_force = shell_reactions[:, :3].sum(axis=0) + root_reaction[:3]
            support_moment = (
                (np.cross(shell_nodes, shell_reactions[:, :3]) +
                 shell_reactions[:, 3:]).sum(axis=0) +
                np.cross(beam_root, root_reaction[:3]) + root_reaction[3:])
            external_force = np.array((0., 0., amplitude)) if dof == tip + 2 else np.zeros(3)
            external_moment = (np.cross((1., 0., .0675), external_force)
                               if dof == tip + 2 else np.array((amplitude, 0., 0.)))
            balance = max(float(np.linalg.norm(support_force + external_force)),
                          float(np.linalg.norm(support_moment + external_moment)))
            shell_covector = (rows[:, :shell_size].T @ multiplier).reshape(-1, 6)
            covector_wrench = np.concatenate((
                shell_covector[:, :3].sum(axis=0),
                (np.cross(shell_nodes, shell_covector[:, :3]) +
                 shell_covector[:, 3:]).sum(axis=0)))
            traction_wrench = wrench @ multiplier
            transfer_error = float(np.linalg.norm(covector_wrench - traction_wrench))
            if (np.linalg.norm(residual[free]) / amplitude > 1e-8 or
                    np.max(np.abs(gap)) > 1e-8 or
                    abs(work - stiffness_work) > 1e-7 or work <= 0 or
                    physical_shell_work <= 0 or balance > 1e-6 or
                    transfer_error > 1e-8):
                raise ArithmeticError("traction line mechanics failed")
            loaded[name] = {
                "tip_rx_rad": float(displacement[tip + 3]),
                "tip_uz_m": float(displacement[tip + 2]),
                "shell_support_mx_nm": float((
                    shell_reactions[:, 3] +
                    shell_nodes[:, 1] * shell_reactions[:, 2]).sum()),
                "shell_support_fz_n": float(shell_reactions[:, 2].sum()),
                "total_external_work_j": work,
                "physical_shell_work_j": physical_shell_work,
                "numerical_shell_work_j": shell_work - physical_shell_work,
                "scaled_equilibrium_error": float(np.linalg.norm(residual[free]) / amplitude),
                "max_weak_gap_m": float(np.max(np.abs(gap))),
                "global_balance_n_nm": balance,
                "interface_wrench_N_Nm": traction_wrench.tolist(),
                "interface_wrench_work_error": transfer_error,
            }
        results.append({"status": "SOLVED_BOUNDED_DIAGNOSTIC",
                        "shell_elements_xy": [shell_x, shell_y],
                        "beam_half_cells": beam_half_cells,
                        "line_intervals": n,
                        "constraint_rank": rank,
                        "rigid_gap": rigid_gap,
                        "global_row_error": global_row_error,
                        "compliance_relative_skew": skew_error,
                        "loaded": loaded,
                        "interpretation": ("Six independent local finite-width physical traction resultants; bounded Q4 linearized work only, not a selected nonlinear line or interface-stability acceptance" if six_local_resultants else
                                           "Continuous physical-traction work with six global wrench directions; four or five local channels, not a selected six-channel pose or interface-stability acceptance"),
                        **meta})
    return results


def run_six_local_decision(output_dir) -> None:
    """Save the bounded P1/P0 six-resultant comparison with its failures."""
    import hashlib
    import json
    import platform
    import subprocess
    from pathlib import Path

    from threadpoolctl import threadpool_info, threadpool_limits

    output_dir = Path(output_dir)
    source = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                     text=True).strip()
    if subprocess.check_output(["git", "status", "--porcelain"],
                               text=True).strip():
        raise RuntimeError("run requires clean source")
    output_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "status": "EXPLORATORY_NOT_G0_ACCEPTANCE",
        "question": "Does adding six independent local finite-width traction resultants give a rank-stable, physically credible native torque/shear line at matched geometry?",
        "outcome_rule": "P1 or P0 must pass full row rank, work, loaded torque/shear transfer and shell/beam partition before stability and mesh-ratio qualification. Rank or local wrench identity alone cannot select a line law.",
        "source_head": source,
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "comparison": "f03-matched-native-full-bond-dev-20260925-v2 and f03-ccx-full-bond-quadratic-face-dev-20260925-v1",
        "physical_scope": "Q4 E4 plate x[-.5,1.5] y[-.5,.5] t=.035 m; B3 x[0,1] axis z=.0675 m, square Saint-Venant J; full shell left-edge and beam root fixed; separate +100 N m tip Mx and +1000 N tip Fz",
        "connection": "finite-width .1 m physical top/bottom traction with six independent local force/moment resultants, P1 and P0 rows, 2/4/8 intervals; bounded linearized Q4 diagnostic only",
        "mesh": "shell x8/y4, native B3 16 half-cells; fixed while line rows change",
        "requested_blas_threads": 1,
        "python": platform.python_version(),
    }
    with threadpool_limits(limits=1):
        manifest["effective_threadpools"] = threadpool_info()
        results = {}
        for kind in ("continuous_linear", "piecewise_constant"):
            rows = bounded_continuous_traction_screen(
                shell_x=8, shell_y=4, beam_half_cells=16,
                intervals=(2, 4, 8), six_local_resultants=True,
                line_kind=kind)
            results[kind] = rows
            for row in rows:
                print(kind, row["line_intervals"], row["status"],
                      row["constraint_rank"],
                      row.get("loaded", {}).get("torque_mx_100nm", {}).get(
                          "tip_rx_rad"), flush=True)
        (output_dir / "results.json").write_text(
            json.dumps(results, indent=2, allow_nan=False) + "\n")
        manifest["results_sha256"] = hashlib.sha256(
            (output_dir / "results.json").read_bytes()).hexdigest()
        (output_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--six-local-decision", action="store_true",
                        required=True)
    parser.add_argument("output_dir")
    run_six_local_decision(parser.parse_args().output_dir)
