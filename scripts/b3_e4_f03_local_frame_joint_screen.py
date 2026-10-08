"""Bounded joint-resolution diagnostic for the local six-channel line frame.

Development comparison only. The independent reference covers the physical
in-plane three-channel subsystem; the native route has six channels and E4
numerical completion. Neither result selects a multiplier space.
"""

from __future__ import annotations

import argparse
import json
from time import perf_counter

import numpy as np

from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_shell_spatial_linear_port import physical_shell_stiffness
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts._b3_e4_f03_weak_line_candidate import (
    LineMultiplierSpace, assemble_reference_kkt,
)
from scripts.b3_e4_f03_independent_yaw_reference import (
    interface_stability, solve,
)
from scripts.b3_e4_f03_independent_transverse_reference import (
    solve as solve_transverse,
)
from scripts.b3_e4_f03_weak_line_resolution_screen import one_case


CASES = ((4, 2, 4, 2), (8, 4, 8, 4), (16, 8, 16, 8))


def physical_only_yaw(topology: str, kind: str, *,
                      n_s: int = 4, n_y: int = 4,
                      half_cells: int = 8, intervals: int = 4) -> dict:
    """Remove E4 numerical completion in the loaded in-plane subsystem.

    Retain the actual native B3 saddle tangent and same six-channel trace,
    but keep only shell ux/uy coordinates and Fx/Fy/Mz weak constraints.
    This is an attribution diagnostic, not a replacement shell formulation.
    """
    shell = FlatE4TrialPanel(make_shell(n_s, topology, n_y=n_y))
    beam = build(half_cells)
    space = LineMultiplierSpace(kind, tuple(np.linspace(0., 1., intervals+1)))
    kkt = assemble_reference_kkt(
        shell, beam, space, shell_port="local_frame",
        shell_support_policy="full_left_edge")
    shell_size = 6*shell.panel.node_count
    original_free = kkt.free_primal
    selected = np.array([index for index in original_free
                         if index >= shell_size or index % 6 in (0, 1)],
                        dtype=int)
    shell_free = selected[selected < shell_size]
    full_shell_physical = physical_shell_stiffness(shell.panel).toarray()
    tangent = kkt.primal_tangent[np.ix_(selected, selected)].copy()
    tangent[:len(shell_free), :len(shell_free)] = full_shell_physical[
        np.ix_(shell_free, shell_free)]
    constraint = kkt.constraint_jacobian.reshape(
        space.count, 6, -1)[:, (0, 1, 5), :][:, :, selected].reshape(
            3*space.count, len(selected))
    system = np.block([[tangent, constraint.T],
                       [constraint, np.zeros((len(constraint),)*2)]])
    positions = np.searchsorted(original_free, selected)
    if not np.array_equal(original_free[positions], selected):
        raise ArithmeticError("selected free coordinates changed")
    qscale = kkt.coordinate_scale[positions]
    multiplier_scale = kkt.coordinate_scale[len(original_free)]
    scale = np.r_[qscale, np.full(len(constraint), multiplier_scale)]
    scaled = scale[:, None]*system*scale[None, :]/kkt.energy_scale
    tip = shell_size+6*half_cells+5
    force = np.zeros(len(selected))
    force[np.flatnonzero(selected == tip)[0]] = 100.
    rhs = np.r_[force*qscale/kkt.energy_scale,
                np.zeros(len(constraint))]
    solution = scale*np.linalg.solve(scaled, rhs)
    q = solution[:len(selected)]
    physical_energy = float(.5*q[:len(shell_free)]@tangent[
        :len(shell_free), :len(shell_free)]@q[:len(shell_free)])
    work = float(force@q)
    residual = float(np.linalg.norm(scaled@(solution/scale)-rhs))
    return {
        "tip_rz_rad": float(q[np.flatnonzero(selected == tip)[0]]),
        "shell_physical_energy_j": physical_energy,
        "work_error_j": float(q@tangent@q-work),
        "scaled_residual": residual,
        "constraints": len(constraint),
        "free_primal": len(selected),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spaces", action="store_true",
                        help="compare P0, P1 and dual on one physical mesh")
    parser.add_argument("--transverse", action="store_true",
                        help="compare physical shear and torque channels")
    parser.add_argument("--beam-ratio", action="store_true",
                        help="vary beam resolution at fixed shell and line")
    parser.add_argument("--physical-only", action="store_true",
                        help="attribute yaw to physical versus E4 numerical shell stiffness")
    args = parser.parse_args()
    if args.physical_only:
        for topology in ("Q4", "S3-V2D"):
            for kind in ("piecewise_constant", "continuous_linear",
                         "dual_linear"):
                physical = physical_only_yaw(topology, kind)
                full = one_case(
                    topology, 4, kind, shell_port="local_frame",
                    load_kind="yaw_torque_z", n_s=4, n_y=4,
                    native_half_cells=8,
                    shell_support_policy="full_left_edge")
                print(json.dumps({
                    "topology": topology, "kind": kind,
                    "physical_only_tip_rz_rad": physical["tip_rz_rad"],
                    "full_e4_tip_rz_rad": full["tip_rz_rad"],
                    "relative_tip_change_full_over_physical": (
                        full["tip_rz_rad"]/physical["tip_rz_rad"]-1),
                    "physical_only_shell_energy_j": physical[
                        "shell_physical_energy_j"],
                    "full_shell_numerical_energy_fraction": full[
                        "shell_numerical_energy_fraction"],
                    "physical_only_work_error_j": physical["work_error_j"],
                    "physical_only_scaled_residual": physical["scaled_residual"],
                }), flush=True)
        return
    if args.beam_ratio:
        for half_cells in (4, 8, 16):
            independent = solve(8, 4, half_cells, 4)
            native = one_case(
                "Q4", 4, "piecewise_constant",
                shell_port="local_frame", load_kind="yaw_torque_z",
                n_s=4, n_y=4, native_half_cells=half_cells,
                shell_support_policy="full_left_edge")
            print(json.dumps({
                "beam_half_cells": half_cells,
                "beam_elements": half_cells//2,
                "shell_line_elements": 4,
                "independent_tip_rz_rad": independent["tip_rz_rad"],
                "native_tip_rz_rad": native["tip_rz_rad"],
                "native_support_mz_n_m": native[
                    "shell_support_reaction_mz_about_origin_n_m"],
                "native_numerical_energy_fraction": native[
                    "shell_numerical_energy_fraction"],
            }), flush=True)
        return
    if args.transverse:
        for topology in ("Q4", "S3-V2D"):
            for load_kind, force, torque in (
                    ("transverse_force_z", 1000., 0.),
                    ("torsion", 0., 100.)):
                native = one_case(
                    topology, 4, "piecewise_constant",
                    shell_port="local_frame", load_kind=load_kind,
                    n_s=4, n_y=4, native_half_cells=8,
                    shell_support_policy="full_left_edge")
                independent = solve_transverse(
                    8, 4, 8, 4, origin="local", director="local",
                    multiplier="p0", basis="spline",
                    tip_force_z=force, tip_torque_x=torque)
                print(json.dumps({
                    "topology": topology, "load": load_kind,
                    "native_tip_z_m": native["beam_tip_uz_m"],
                    "independent_tip_z_m": independent["tip_z_m"],
                    "native_tip_rx_rad": native["tip_rx_rad"],
                    "independent_tip_rx_rad": independent["tip_rx_rad"],
                    "native_shell_numerical_energy_fraction": native[
                        "shell_numerical_energy_fraction"],
                    "native_force_balance_n": native[
                        "global_force_z_balance_n"],
                    "native_torque_balance_n_m": native[
                        "global_torque_x_balance_n_m"],
                    "independent_work_error_j": independent["work_error_j"],
                }), flush=True)
        return
    if args.spaces:
        for topology in ("Q4", "S3-V2D"):
            for kind in ("piecewise_constant", "continuous_linear",
                         "dual_linear"):
                started = perf_counter()
                native = one_case(
                    topology, 4, kind, shell_port="local_frame",
                    load_kind="yaw_torque_z", n_s=4, n_y=4,
                    native_half_cells=8,
                    shell_support_policy="full_left_edge")
                print(json.dumps({
                    "topology": topology, "kind": kind,
                    "tip_rz_rad": native["tip_rz_rad"],
                    "shell_support_mz_n_m": native[
                        "shell_support_reaction_mz_about_origin_n_m"],
                    "shell_physical_inplane_energy_j": native[
                        "shell_physical_inplane_energy_j"],
                    "shell_numerical_energy_fraction": native[
                        "shell_numerical_energy_fraction"],
                    "global_moment_balance_n_m": native[
                        "global_moment_z_balance_n_m"],
                    "weak_gap_max_m": native["gap_max_m"],
                    "seconds": perf_counter()-started,
                }), flush=True)
        return
    for nx, ny, nb, intervals in CASES:
        started = perf_counter()
        independent = solve(nx, ny, nb, intervals)
        stability = interface_stability(nx, ny, nb, intervals)
        native = one_case(
            "Q4", intervals, "piecewise_constant",
            shell_port="local_frame", load_kind="yaw_torque_z",
            n_s=nx//2, n_y=ny, native_half_cells=nb,
            shell_support_policy="full_left_edge")
        print(json.dumps({
            "nx": nx, "ny": ny, "nb": nb, "intervals": intervals,
            "independent_tip_rz_rad": independent["tip_rz_rad"],
            "native_tip_rz_rad": native["tip_rz_rad"],
            "independent_shell_support_mz_n_m": independent["shell_support_mz_n_m"],
            "native_shell_support_mz_n_m": native[
                "shell_support_reaction_mz_about_origin_n_m"],
            "independent_physical_beta": stability["normalized_beta_min"],
            "independent_rank": stability["rank"],
            "independent_rows": stability["rows"],
            "native_shell_numerical_energy_fraction": native[
                "shell_numerical_energy_fraction"],
            "native_global_moment_balance_n_m": native[
                "global_moment_z_balance_n_m"],
            "seconds": perf_counter()-started,
        }), flush=True)


if __name__ == "__main__":
    main()
