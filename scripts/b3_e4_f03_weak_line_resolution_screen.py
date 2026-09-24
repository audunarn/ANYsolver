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


def one_case(topology: str, intervals: int, kind: str, *,
             shell_port: str = "rail") -> dict:
    """Solve the same +100 Nm torsion case at one multiplier resolution."""
    shell = FlatE4TrialPanel(make_shell(4, topology))
    beam = build(16)
    space = LineMultiplierSpace(
        kind, tuple(np.linspace(0., 1., intervals+1)))
    kkt = assemble_reference_kkt(
        shell, beam, space, shell_port=shell_port)
    pose_map = (pose_from_e4_total if shell_port == "rail" else
                pose_from_e4_total_local_translation)
    shell_size = 6*shell.panel.node_count
    tip_rx = shell_size+6*beam.n_half_cells+3
    load = np.zeros(shell_size+beam.context.count)
    load[tip_rx] = 100.
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
    gaps = np.asarray(gap_norms)
    return {
        "topology": topology,
        "kind": kind,
        "shell_port": shell_port,
        "intervals": intervals,
        "shell_elements": shell.panel.element_count,
        "native_elements": beam.n_half_cells//2,
        "tip_rx_rad": float(full[tip_rx]),
        "shell_energy_j": float(.5*shell_total@kkt.primal_tangent[
            :shell_size, :shell_size]@shell_total),
        "gap_l2_m": float(np.sqrt(np.trapezoid(gaps*gaps, dx=1./128))),
        "gap_max_m": float(np.max(gaps)),
        "scaled_equilibrium_residual": float(np.linalg.norm(scaled_residual)),
        "free_primal_residual_mixed_l2": float(np.linalg.norm(
            physical_residual[kkt.free_primal])),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--local-translation", action="store_true")
    shell_port = ("local_translation" if parser.parse_args().local_translation
                  else "rail")
    rows = [one_case(topology, intervals, kind, shell_port=shell_port)
            for topology in ("Q4", "S3-V2D")
            for kind in ("piecewise_constant", "continuous_linear")
            for intervals in (2, 4, 8)]
    print(json.dumps({"status": "UNREGISTERED_DIAGNOSTIC",
                      "shell_port": shell_port, "cases": rows},
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
