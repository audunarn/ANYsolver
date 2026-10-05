"""Bounds on represented Q6 linear outputs; no physical qualification."""

from fractions import Fraction
from types import SimpleNamespace

import numpy as np
import pytest

from scripts._b3_e4_f03_q6_observable_bound import (
    bound_linear_rows, bound_q6_observables)


def _exact_output(row, scales, state):
    return sum((Fraction.from_float(float(a)) *
                Fraction.from_float(float(d)) * z
                for a, d, z in zip(row, scales, state)), Fraction(0))


def test_linear_bound_contains_perturbed_state_and_reported_rounding():
    rows = np.array([[1.e12, -1.e12, .125],
                     [-3., 0., 2.]])
    scales = np.array([.1, .2, 4.])
    candidate = np.array([1., .5, -3.])
    delta = 2.e-7
    reported = np.array([float(rows[0] @ (scales*candidate)) + .25,
                         float(rows[1] @ (scales*candidate))])
    result = bound_linear_rows(rows, scales, candidate, delta, reported)
    for signs in ((1., -1., 1.), (-1., 1., -1.), (1., 1., 1.)):
        true_state = [Fraction.from_float(float(z)) +
                      Fraction.from_float(delta)*int(sign)
                      for z, sign in zip(candidate, signs)]
        for i, row in enumerate(rows):
            difference = abs(_exact_output(row, scales, true_state) -
                             Fraction.from_float(float(reported[i])))
            assert difference <= Fraction.from_float(
                result["total_error_upper"][i])
    assert result["reported_rounding_upper"][0] > .2
    assert result["total_error_upper"][0] > result[
        "state_propagation_upper"][0]


def test_zero_row_has_exact_zero_radius_when_reported_zero():
    result = bound_linear_rows(np.zeros((1, 2)), np.ones(2),
                               np.array([4., -8.]), .1, np.zeros(1))
    assert result["total_error_upper"] == [0.]


def test_q6_named_outputs_bind_tip_work_and_root_multipliers():
    operators = SimpleNamespace(
        dof_count=2, tip_pose=np.array([[1., 0.], [0., 1.], [1., -1.]]),
        load=np.array([2., -3.]))
    state = np.array([.5, -.25, 4., -5., 6.])
    scales = np.array([2., 4.])
    root_scales = np.array([10., 20., 30.])
    physical = {"signed": {
        "tip_pose": [1., -1., 2.], "external_work_j": 5.,
        "eta": [40., -100., 180.]}}
    result = bound_q6_observables(operators, scales, root_scales,
                                  state, 1.e-6, physical)
    assert result["observable_order"] == [
        "tip_ux_m", "tip_uy_m", "tip_yaw_rad", "external_work_j",
        "root_fx_n", "root_fy_n", "root_mz_nm"]
    assert len(result["total_error_upper"]) == 7
    assert result["reported_rounding_upper"] == [0.]*7
    assert result["total_error_upper"][6] >= 30.e-6


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1.])
def test_invalid_state_bound_rejected(bad):
    with pytest.raises(ValueError, match="invalid bounded"):
        bound_linear_rows(np.ones((1, 2)), np.ones(2),
                          np.ones(2), bad, np.ones(1))
