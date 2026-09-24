"""Bounded native B3/E4 six-channel interface compliance screen.

The Schur action C K^-1 C.T uses the complete native retained tangent, whose
primal block is indefinite. Its H^(-1/2)-normalized eigenvalues are useful
finite-dimensional diagnostics, but are not a positive-energy inf-sup proof
or a qualification decision for a multiplier space.
"""

from __future__ import annotations

import json

import numpy as np
from scipy import linalg

from scripts._b3_e4_f03_e4_trial_panel import FlatE4TrialPanel
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_p0_dual_norm import p0_dual_gram
from scripts._b3_e4_f03_p1_dual_norm import p1_dual_gram
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts._b3_e4_f03_weak_line_candidate import (
    LineMultiplierSpace, assemble_reference_kkt)


def one_case(topology: str, n_s: int, kind: str) -> dict:
    """Return full-retained compliance eigenvalues on a fixed paired grid."""
    n_intervals = 2*n_s
    shell = FlatE4TrialPanel(make_shell(n_s, topology))
    beam = build(4*n_s)
    space = LineMultiplierSpace(
        kind, tuple(np.linspace(0., 1., n_intervals+1)))
    kkt = assemble_reference_kkt(shell, beam, space)
    free = kkt.free_primal
    n_free = len(free)
    tangent = kkt.primal_tangent[np.ix_(free, free)]
    rows = kkt.constraint_jacobian[:, free]
    qscale = kkt.coordinate_scale[:n_free]
    scaled_tangent = (((qscale[:, None]*tangent)*qscale[None, :])/
                      kkt.energy_scale)
    scaled_rows = rows*qscale[None, :]
    inverse_action = np.linalg.solve(scaled_tangent, scaled_rows.T)
    solve_residual = np.linalg.norm(
        scaled_tangent@inverse_action-scaled_rows.T)/np.linalg.norm(
            scaled_rows)
    compliance = scaled_rows@inverse_action/kkt.energy_scale
    skew = np.linalg.norm(compliance-compliance.T)/np.linalg.norm(compliance)
    if skew > 1e-8 or solve_residual > 1e-8:
        raise ArithmeticError("native interface compliance solve inconsistent")
    compliance = (compliance+compliance.T)/2

    # The six rows are [translations in m, rotations in rad]. Convert each
    # moment-density coefficient to force density by a fixed 1 m length.
    length_m = 1.
    moment_to_force = np.tile(
        np.r_[np.ones(3), np.full(3, length_m)], space.count)
    force_compliance = ((moment_to_force[:, None]*compliance)*
                        moment_to_force[None, :])
    if kind == "piecewise_constant":
        lower, upper = p0_dual_gram(n_intervals, length_m, 4095)
    else:
        lower, upper = p1_dual_gram(n_intervals, length_m, 4095)
    dual_lower = np.kron(lower, np.eye(6))
    dual_upper = np.kron(upper, np.eye(6))
    # E*t converts the compliance/force-dual-norm quotient to a dimensionless
    # reference number. It is held fixed across this screen, not fitted.
    reference_stiffness_n_per_m = 210e9*.07
    scaled_compliance = reference_stiffness_n_per_m*force_compliance
    with_upper = linalg.eigh(
        scaled_compliance, dual_upper, eigvals_only=True, check_finite=True)
    with_lower = linalg.eigh(
        scaled_compliance, dual_lower, eigvals_only=True, check_finite=True)
    return {
        "topology": topology,
        "n_s": n_s,
        "native_half_cells": beam.n_half_cells,
        "kind": kind,
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
    }


def main() -> None:
    rows = [one_case(topology, n_s, kind)
            for topology in ("Q4", "S3-V2D")
            for kind in ("piecewise_constant", "continuous_linear")
            for n_s in (1, 2, 4)]
    print(json.dumps({"status": "UNREGISTERED_COMPLIANCE_DIAGNOSTIC",
                      "cases": rows}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
