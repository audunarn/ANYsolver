"""Bounded native B3/E4 six-channel interface compliance screen.

The Schur action C K^-1 C.T uses the complete native retained tangent, whose
primal block is indefinite. Its H^(-1/2)-normalized eigenvalues are useful
finite-dimensional diagnostics, but are not a positive-energy inf-sup proof
or a qualification decision for a multiplier space.
"""

from __future__ import annotations

import argparse
import json

import numpy as np
from scipy import linalg

from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_p0_dual_norm import p0_dual_gram
from scripts._b3_e4_f03_p1_dual_norm import p1_dual_gram
from scripts._b3_e4_f03_dual_linear_norm import dual_linear_gram
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts._b3_e4_f03_weak_line_candidate import (
    LineMultiplierSpace, assemble_reference_kkt)


def absolute_primal_action(tangent: np.ndarray,
                           right: np.ndarray) -> tuple[np.ndarray, float, float]:
    """Apply the inverse spectral absolute of a bounded symmetric tangent.

    This positive diagnostic norm is not native strain energy or a production
    operator.
    """
    a = np.asarray(tangent, dtype=np.float64)
    b = np.asarray(right, dtype=np.float64)
    if (a.ndim != 2 or a.shape[0] != a.shape[1] or
            not 1 <= len(a) <= 1024 or b.ndim != 2 or
            b.shape[0] != len(a) or not 1 <= b.shape[1] <= 128 or
            not np.isfinite(a).all() or not np.isfinite(b).all()):
        raise ValueError("bounded finite primal action required")
    norm = np.linalg.norm(a)
    if norm == 0. or np.linalg.norm(b) == 0.:
        raise ValueError("zero primal tangent or interface action")
    skew = float(np.linalg.norm(a-a.T)/norm)
    if skew > 1e-8:
        raise ValueError("absolute-primal diagnostic requires symmetric tangent")
    values, vectors = linalg.eigh((a+a.T)/2, check_finite=True)
    absolute = np.abs(values)
    minimum = float(np.min(absolute))
    maximum = float(np.max(absolute))
    if minimum <= np.finfo(float).eps*len(a)*maximum:
        raise ValueError("absolute-primal diagnostic has unresolved null mode")
    projection = vectors.T@b
    action = vectors@(projection/absolute[:, None])
    residual = float(np.linalg.norm(
        absolute[:, None]*(vectors.T@action)-projection)/
        np.linalg.norm(b))
    if residual > 1e-8:
        raise ArithmeticError("absolute-primal action residual too large")
    return action, residual, minimum/maximum


def one_case(topology: str, n_s: int, kind: str, *,
             n_intervals: int | None = None,
             shell_port: str = "rail",
             absolute_primal: bool = False) -> dict:
    """Return full-retained compliance eigenvalues on a fixed paired grid."""
    if n_intervals is None:
        n_intervals = 2*n_s
    shell = FlatE4TrialPanel(make_shell(n_s, topology))
    beam = build(4*n_s)
    space = LineMultiplierSpace(
        kind, tuple(np.linspace(0., 1., n_intervals+1)))
    kkt = assemble_reference_kkt(
        shell, beam, space, shell_port=shell_port)
    free = kkt.free_primal
    n_free = len(free)
    tangent = kkt.primal_tangent[np.ix_(free, free)]
    rows = kkt.constraint_jacobian[:, free]
    qscale = kkt.coordinate_scale[:n_free]
    scaled_tangent = (((qscale[:, None]*tangent)*qscale[None, :])/
                      kkt.energy_scale)
    scaled_rows = rows*qscale[None, :]
    if absolute_primal:
        inverse_action, solve_residual, absolute_eigen_ratio = (
            absolute_primal_action(scaled_tangent, scaled_rows.T))
    else:
        inverse_action = np.linalg.solve(scaled_tangent, scaled_rows.T)
        solve_residual = np.linalg.norm(
            scaled_tangent@inverse_action-scaled_rows.T)/np.linalg.norm(
                scaled_rows)
        absolute_eigen_ratio = None
    compliance = scaled_rows@inverse_action/kkt.energy_scale
    shell_free = int(np.count_nonzero(free < 6*shell.panel.node_count))
    shell_compliance = (scaled_rows[:, :shell_free]@
                        inverse_action[:shell_free])/kkt.energy_scale
    beam_compliance = (scaled_rows[:, shell_free:]@
                       inverse_action[shell_free:])/kkt.energy_scale
    if np.linalg.norm(compliance-shell_compliance-beam_compliance) > (
            1e-10*np.linalg.norm(compliance)):
        raise ArithmeticError("native interface domain split inconsistent")
    skew = np.linalg.norm(compliance-compliance.T)/np.linalg.norm(compliance)
    if skew > 1e-8 or solve_residual > 1e-8:
        raise ArithmeticError("native interface compliance solve inconsistent")
    compliance = (compliance+compliance.T)/2

    # The six rows are [translations in m, rotations in rad]. Convert each
    # moment-density coefficient to force density by a fixed 1 m length.
    length_m = 1.
    moment_to_force = np.tile(
        np.r_[np.ones(3), np.full(3, length_m)], space.count)
    shell_row_singulars = linalg.svdvals(
        moment_to_force[:, None]*scaled_rows[:, :shell_free],
        check_finite=True)
    shell_rank_tolerance = 1e-10*shell_row_singulars[0]
    shell_row_rank = int(np.count_nonzero(
        shell_row_singulars > shell_rank_tolerance))
    force_compliance = ((moment_to_force[:, None]*compliance)*
                        moment_to_force[None, :])
    if kind == "piecewise_constant":
        lower, upper = p0_dual_gram(n_intervals, length_m, 4095)
    elif kind == "continuous_linear":
        lower, upper = p1_dual_gram(n_intervals, length_m, 4095)
    else:
        lower, upper = dual_linear_gram(n_intervals, length_m, 4095)
    dual_lower = np.kron(lower, np.eye(6))
    dual_upper = np.kron(upper, np.eye(6))
    # E*t converts the compliance/force-dual-norm quotient to a dimensionless
    # reference number. It is held fixed across this screen, not fitted.
    reference_stiffness_n_per_m = 210e9*.07
    scaled_compliance = reference_stiffness_n_per_m*force_compliance
    with_upper, vectors = linalg.eigh(
        scaled_compliance, dual_upper, check_finite=True)
    with_lower = linalg.eigh(
        scaled_compliance, dual_lower, eigvals_only=True, check_finite=True)
    if absolute_primal:
        scaled_shell_compliance = (reference_stiffness_n_per_m*
            ((moment_to_force[:, None]*shell_compliance)*
             moment_to_force[None, :]))
        scaled_beam_compliance = (reference_stiffness_n_per_m*
            ((moment_to_force[:, None]*beam_compliance)*
             moment_to_force[None, :]))
        shell_only, shell_vectors = linalg.eigh(
            scaled_shell_compliance, dual_upper, check_finite=True)
        beam_only = linalg.eigh(scaled_beam_compliance, dual_upper,
                                eigvals_only=True, check_finite=True)
        if (shell_only[0] < -1e-8 or beam_only[0] < -1e-8 or
                with_upper[0] < shell_only[0]+beam_only[0]-1e-8):
            raise ArithmeticError("absolute-primal domain spectrum inconsistent")
        shell_only_minimum = float(shell_only[0])
        beam_only_minimum = float(beam_only[0])
        shell_zero = shell_only <= 1e-8*max(1., abs(shell_only[-1]))
        shell_zero_count = int(np.count_nonzero(shell_zero))
        shell_subspace = (shell_vectors[:, shell_zero] if shell_zero_count else
                          shell_vectors[:, :1]).reshape(space.count, 6, -1)
        shell_channel_fractions = [float(sum(
            shell_subspace[:, channel, column]@upper@
            shell_subspace[:, channel, column]
            for column in range(shell_subspace.shape[2]))/
            shell_subspace.shape[2]) for channel in range(6)]
        if abs(sum(shell_channel_fractions)-1.) > 1e-8:
            raise ArithmeticError("shell-only subspace dual normalization lost")
    else:
        shell_only_minimum = beam_only_minimum = None
        shell_zero_count = None
        shell_channel_fractions = None
    minimum_mode = vectors[:, 0].reshape(space.count, 6)
    minimum_force_mode = moment_to_force*vectors[:, 0]
    shell_mode_quotient = float(reference_stiffness_n_per_m*
        minimum_force_mode@shell_compliance@minimum_force_mode)
    beam_mode_quotient = float(reference_stiffness_n_per_m*
        minimum_force_mode@beam_compliance@minimum_force_mode)
    if abs(shell_mode_quotient+beam_mode_quotient-with_upper[0]) > (
            1e-8*max(1., abs(with_upper[0]))):
        raise ArithmeticError("native minimum-mode work split inconsistent")
    channel_fractions = np.array([
        minimum_mode[:, channel]@upper@minimum_mode[:, channel]
        for channel in range(6)])
    if abs(float(np.sum(channel_fractions))-1.) > 1e-8:
        raise ArithmeticError("minimum mode lost dual normalization")
    strongest = int(np.argmax(channel_fractions))
    coefficients = minimum_mode[:, strongest]
    signs = np.sign(coefficients[
        np.abs(coefficients) > 1e-8*np.max(np.abs(coefficients))])
    return {
        "topology": topology,
        "n_s": n_s,
        "native_half_cells": beam.n_half_cells,
        "kind": kind,
        "primal_metric": "spectral_absolute" if absolute_primal else "signed",
        "absolute_minimum_eigen_ratio": absolute_eigen_ratio,
        "shell_port": shell_port,
        "multiplier_intervals": n_intervals,
        "free_primal": n_free,
        "multiplier_rows": len(rows),
        "scaled_primal_negative_modes": int(np.count_nonzero(
            np.linalg.eigvalsh((scaled_tangent+scaled_tangent.T)/2) < 0.)),
        "schur_skew": float(skew),
        "scaled_solve_residual": float(solve_residual),
        "dual_tail_relative": float(np.linalg.norm(upper-lower)/
                                    np.linalg.norm(lower)),
        "minimum_quotient_lower": float(with_upper[0]),
        "minimum_quotient_upper": float(with_lower[0]),
        "maximum_quotient_lower": float(with_upper[-1]),
        "maximum_quotient_upper": float(with_lower[-1]),
        "minimum_mode_channel_fractions": [float(x) for x in channel_fractions],
        "minimum_mode_dominant_channel": (
            "Fx", "Fy", "Fz", "Mx", "My", "Mz")[strongest],
        "minimum_mode_dominant_sign_changes": int(np.count_nonzero(
            signs[:-1]*signs[1:] < 0)),
        "minimum_mode_shell_quotient": shell_mode_quotient,
        "minimum_mode_beam_quotient": beam_mode_quotient,
        "shell_row_rank": shell_row_rank,
        "shell_row_count": len(shell_row_singulars),
        "shell_row_minimum_singular": float(shell_row_singulars[-1]),
        "shell_row_rank_relative_tolerance": 1e-10,
        "minimum_shell_only_quotient_lower": shell_only_minimum,
        "minimum_beam_only_quotient_lower": beam_only_minimum,
        "shell_only_zero_mode_count": shell_zero_count,
        "shell_only_minimum_subspace_channel_fractions": shell_channel_fractions,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixed-primal", action="store_true")
    parser.add_argument("--local-translation", action="store_true")
    parser.add_argument("--absolute-primal", action="store_true")
    parser.add_argument("--multiplier-intervals-per-shell", type=int,
                        choices=(1, 2), default=2)
    parser.add_argument("--include-dual", action="store_true")
    arguments = parser.parse_args()
    fixed = arguments.fixed_primal
    shell_port = "local_translation" if arguments.local_translation else "rail"
    kinds = (("piecewise_constant", "continuous_linear", "dual_linear")
             if arguments.include_dual else
             ("piecewise_constant", "continuous_linear"))
    if fixed:
        rows = [one_case(topology, 4, kind, n_intervals=intervals,
                         shell_port=shell_port,
                         absolute_primal=arguments.absolute_primal)
                for topology in ("Q4", "S3-V2D")
                for kind in kinds
                for intervals in (2, 4, 8)]
    else:
        rows = [one_case(topology, n_s, kind,
                         n_intervals=arguments.multiplier_intervals_per_shell*n_s,
                         shell_port=shell_port,
                         absolute_primal=arguments.absolute_primal)
                for topology in ("Q4", "S3-V2D")
                for kind in kinds
                for n_s in (1, 2, 4)]
    print(json.dumps({"status": "UNREGISTERED_COMPLIANCE_DIAGNOSTIC",
                      "screen": "fixed_primal" if fixed else "paired_refinement",
                      "shell_port": shell_port,
                      "primal_metric": ("spectral_absolute" if
                                        arguments.absolute_primal else "signed"),
                      "multiplier_intervals_per_shell":
                          arguments.multiplier_intervals_per_shell,
                      "cases": rows}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
