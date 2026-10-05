"""Exact-represented linear observable bounds for the Q6 diagnostic.

The input state error must come from a bound certificate for the same scaled
KKT system. This only bounds linear recovery from the represented binary64
operators; it says nothing about discretization or native F03 mechanics.
"""

from __future__ import annotations

from fractions import Fraction
import math

import numpy as np

from scripts._b3_e4_f03_sparse_certificate import _up


def _upper(value: Fraction) -> float:
    if value < 0:
        raise ValueError("nonnegative observable bound required")
    result = float(value)
    if not math.isfinite(result):
        raise ArithmeticError("observable bound overflow")
    return float(_up(result)) if value else 0.


def bound_linear_rows(rows: np.ndarray, scales: np.ndarray,
                      candidate: np.ndarray, component_error_upper: float,
                      reported: np.ndarray) -> dict:
    """Enclose each exact output about its reported binary64 value.

    For row ``a``, true scaled state ``z``, and candidate ``zhat``, the
    certificate supplies ``|z_i-zhat_i| <= delta``. The exact represented
    observable is ``sum(a_i * scale_i * z_i)``. Fractions evaluate both the
    candidate and its row-one-norm exactly from input binary64 values, so the
    returned radius also includes rounding in the supplied reported output.
    """
    rows = np.asarray(rows)
    scales = np.asarray(scales)
    candidate = np.asarray(candidate)
    reported = np.asarray(reported)
    n = candidate.size
    if (rows.ndim != 2 or rows.shape[1] != n or not 1 <= rows.shape[0] <= 16
            or not 1 <= n <= 6000 or scales.shape != (n,)
            or candidate.shape != (n,) or reported.shape != (rows.shape[0],)
            or any(v.dtype != np.float64 or not np.isfinite(v).all()
                   for v in (rows, scales, candidate, reported))
            or np.any(scales <= 0) or not math.isfinite(component_error_upper)
            or component_error_upper < 0):
        raise ValueError("invalid bounded Q6 linear observable inputs")
    delta = Fraction.from_float(component_error_upper)
    state_radii = []
    rounding_radii = []
    total_radii = []
    for row, observed in zip(rows, reported):
        exact_candidate = Fraction(0)
        absolute_row = Fraction(0)
        for coefficient, scale, value in zip(row, scales, candidate):
            if coefficient == 0:
                continue
            product = (Fraction.from_float(float(coefficient)) *
                       Fraction.from_float(float(scale)))
            absolute_row += abs(product)
            exact_candidate += product * Fraction.from_float(float(value))
        state_radius = delta * absolute_row
        rounding_radius = abs(Fraction.from_float(float(observed))-
                              exact_candidate)
        state_radii.append(_upper(state_radius))
        rounding_radii.append(_upper(rounding_radius))
        total_radii.append(_upper(state_radius+rounding_radius))
    return {
        "state_propagation_upper": state_radii,
        "reported_rounding_upper": rounding_radii,
        "total_error_upper": total_radii,
        "scope": "exact linear recovery from represented binary64 inputs",
    }


def bound_q6_observables(operators, displacement_scale: np.ndarray,
                         multiplier_scale: np.ndarray, candidate: np.ndarray,
                         component_error_upper: float, physical: dict) -> dict:
    """Bound Q6 tip pose, external work and three root multipliers."""
    n = operators.dof_count
    if (displacement_scale.shape != (n,) or multiplier_scale.shape != (3,)
            or candidate.shape != (n+3,) or
            operators.tip_pose.shape != (3, n) or
            operators.load.shape != (n,)):
        raise ValueError("Q6 observable/operator shape mismatch")
    rows = np.zeros((7, n+3), dtype=np.float64)
    rows[:3, :n] = operators.tip_pose
    rows[3, :n] = operators.load
    rows[4:, n:] = np.eye(3)
    scales = np.r_[displacement_scale, multiplier_scale]
    signed = physical["signed"]
    reported = np.r_[signed["tip_pose"], signed["external_work_j"],
                     signed["eta"]].astype(np.float64)
    result = bound_linear_rows(rows, scales, candidate,
                               component_error_upper, reported)
    result["observable_order"] = ["tip_ux_m", "tip_uy_m", "tip_yaw_rad",
                                  "external_work_j", "root_fx_n", "root_fy_n",
                                  "root_mz_nm"]
    return result
