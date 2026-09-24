"""Unregistered small-system F03 multiplier-resolution diagnostic.

This reuses the bounded native B3/E4 reference KKT oracle. It compares
multiplier spaces on identical physical meshes; its pointwise gaps and
linearized responses are descriptive, not a stability or accuracy gate.
"""

from __future__ import annotations

import argparse
import json

import numpy as np

from anysolver._ge_beam3_pose_joint import RigidPoseJoint

from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts._b3_e4_f03_shell_finite_pose_candidate import pose_from_e4_total
from scripts._b3_e4_f03_shell_local_translation_candidate import (
    pose_from_e4_total_local_translation)
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts._b3_e4_f03_weak_line_candidate import (
    LineMultiplierSpace, assemble_reference_kkt)


def sinusoidal_axial_density_load(beam, *, amplitude_n_per_m=1e5):
    """Integrate one fixed physical line density through native station work."""
    if (isinstance(amplitude_n_per_m, (bool, str)) or
            not isinstance(amplitude_n_per_m,
                           (int, float, np.integer, np.floating)) or
            not np.isfinite(amplitude_n_per_m) or
            amplitude_n_per_m <= 0.):
        raise ValueError("positive finite axial line-load amplitude required")
    points, weights = np.polynomial.legendre.leggauss(8)
    load = np.zeros(beam.context.count)
    for half_cell in range(beam.n_half_cells):
        left = half_cell/beam.n_half_cells
        right = (half_cell+1)/beam.n_half_cells
        for point, weight in zip(points, weights):
            station = (left+right)/2+(right-left)*point/2
            element, cell, fraction, _ = beam._locate(float(station))
            port = NativeHalfCellSpatialPort(
                beam.context, element, cell, fraction)
            wrench = np.array((amplitude_n_per_m*np.sin(2*np.pi*station),
                               0., 0., 0., 0., 0.))
            load += (right-left)*weight/2*port.pullback(
                beam.context.initial.mechanical, wrench)
    return load


def one_case(topology: str, intervals: int, kind: str, *,
             shell_port: str = "rail",
             load_kind: str = "torsion", n_s: int = 4,
             native_half_cells: int = 16) -> dict:
    """Solve a bounded torsion or alternating axial case at one resolution."""
    shell = FlatE4TrialPanel(make_shell(n_s, topology))
    beam = build(native_half_cells)
    space = LineMultiplierSpace(
        kind, tuple(np.linspace(0., 1., intervals+1)))
    kkt = assemble_reference_kkt(
        shell, beam, space, shell_port=shell_port)
    pose_map = (pose_from_e4_total if shell_port == "rail" else
                pose_from_e4_total_local_translation)
    shell_size = 6*shell.panel.node_count
    tip_rx = shell_size+6*beam.n_half_cells+3
    load = np.zeros(shell_size+beam.context.count)
    if load_kind == "torsion":
        load[tip_rx] = 100.
    elif load_kind == "axial_wave":
        positions = (beam.context.initial.mechanical.positions+
                     beam.context.initial.mechanical.position_low)
        axial = 1e5*np.sin(8*np.pi*positions[:, 0])
        axial[np.abs(axial) < 1e-8] = 0.
        load[shell_size:shell_size+beam.context.nodal_count:6] = axial
    elif load_kind == "sinusoidal_axial_density":
        load[shell_size:] = sinusoidal_axial_density_load(beam)
    else:
        raise ValueError("unknown bounded line load kind")
    free_count = len(kkt.free_primal)
    rhs = np.r_[load[kkt.free_primal]*
                kkt.coordinate_scale[:free_count]/kkt.energy_scale,
                np.zeros(6*space.count)]
    scaled_solution = np.linalg.solve(kkt.scaled_system, rhs)
    scaled_residual = kkt.scaled_system@scaled_solution-rhs
    physical_solution = kkt.coordinate_scale*scaled_solution
    full = np.zeros(len(load))
    full[kkt.free_primal] = physical_solution[:free_count]
    multipliers = physical_solution[free_count:]
    physical_residual = (kkt.primal_tangent@full+
                         kkt.constraint_jacobian.T@multipliers-load)
    shell_total = full[:shell_size]
    beam_state = beam.context.advance(
        beam.context.initial.mechanical, full[shell_size:])
    shell_reference = np.zeros(shell_size)
    gap_norms = []
    axial_gaps = []
    for station in np.linspace(0., 1., 129):
        element, cell, fraction, _ = beam._locate(float(station))
        port = NativeHalfCellSpatialPort(
            beam.context, element, cell, fraction)
        shell_ref_position, shell_ref_frame = pose_map(
            shell.panel, float(station), shell_reference)
        beam_ref_high, beam_ref_low, beam_ref_frame = port.pose_pair(
            beam.context.initial.mechanical)
        joint = RigidPoseJoint(
            np.array((shell_ref_position, beam_ref_high+beam_ref_low)),
            np.array((shell_ref_frame, beam_ref_frame)))
        shell_position, shell_frame = pose_map(
            shell.panel, float(station), shell_total)
        beam_high, beam_low, beam_frame = port.pose_pair(beam_state)
        gap = joint.evaluate(
            np.array((shell_position, beam_high)),
            np.array((shell_frame, beam_frame)), np.zeros(6),
            position_low=np.array((np.zeros(3), beam_low))).constraints
        gap_norms.append(float(np.linalg.norm(np.r_[gap[:3], gap[3:]*1.])))
        axial_gaps.append(float(gap[0]))
    gaps = np.asarray(gap_norms)
    axial_gap = np.asarray(axial_gaps)
    beam_nodal = full[
        shell_size:shell_size+beam.context.nodal_count].reshape(-1, 6)
    return {
        "topology": topology,
        "kind": kind,
        "shell_port": shell_port,
        "load_kind": load_kind,
        "intervals": intervals,
        "shell_host_intervals": n_s,
        "native_half_cells": native_half_cells,
        "shell_elements": shell.panel.element_count,
        "native_elements": beam.n_half_cells//2,
        "tip_rx_rad": float(full[tip_rx]),
        "beam_tip_ux_m": float(beam_nodal[-1, 0]),
        "beam_max_abs_ux_m": float(np.max(np.abs(beam_nodal[:, 0]))),
        "shell_max_abs_ux_m": float(np.max(np.abs(
            full[:shell_size].reshape(-1, 6)[:, 0]))),
        "applied_axial_force_n": float(np.sum(
            load[shell_size:shell_size+beam.context.nodal_count:6])),
        "applied_axial_first_moment_n_m": float(np.dot(
            np.arange(native_half_cells+1)/native_half_cells,
            load[shell_size:shell_size+beam.context.nodal_count:6])),
        "shell_energy_j": float(.5*shell_total@kkt.primal_tangent[
            :shell_size, :shell_size]@shell_total),
        "gap_l2_m": float(np.sqrt(np.trapezoid(gaps*gaps, dx=1./128))),
        "gap_max_m": float(np.max(gaps)),
        "gap_axial_l2_m": float(np.sqrt(np.trapezoid(
            axial_gap*axial_gap, dx=1./128))),
        "gap_axial_max_m": float(np.max(np.abs(axial_gap))),
        "scaled_equilibrium_residual": float(np.linalg.norm(scaled_residual)),
        "free_primal_residual_mixed_l2": float(np.linalg.norm(
            physical_residual[kkt.free_primal])),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-translation", action="store_true")
    parser.add_argument("--axial-wave", action="store_true")
    parser.add_argument("--include-dual", action="store_true")
    parser.add_argument("--paired-refinement", action="store_true")
    parser.add_argument("--sinusoidal-axial-density", action="store_true")
    arguments = parser.parse_args()
    if arguments.axial_wave and arguments.sinusoidal_axial_density:
        parser.error("select only one axial load")
    shell_port = ("local_translation" if arguments.local_translation
                  else "rail")
    load_kind = ("sinusoidal_axial_density" if arguments.sinusoidal_axial_density
                 else "axial_wave" if arguments.axial_wave else "torsion")
    kinds = ("piecewise_constant", "continuous_linear")
    if arguments.include_dual:
        kinds += ("dual_linear",)
    grids = ((n_s, 4*n_s, n_s) for n_s in (1, 2, 4)) if (
        arguments.paired_refinement) else ((4, 16, intervals)
                                          for intervals in (2, 4, 8))
    grids = tuple(grids)
    rows = [one_case(topology, intervals, kind, shell_port=shell_port,
                     load_kind=load_kind, n_s=n_s,
                     native_half_cells=native_half_cells)
            for topology in ("Q4", "S3-V2D")
            for kind in kinds
            for n_s, native_half_cells, intervals in grids]
    print(json.dumps({"status": "UNREGISTERED_DIAGNOSTIC",
                      "screen": "paired_refinement" if arguments.paired_refinement
                      else "fixed_primal",
                      "shell_port": shell_port, "load_kind": load_kind,
                      "cases": rows},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
