"""Independent finite-dimensional checks of the diagnostic primal norm."""

import numpy as np
import pytest

from scripts.b3_e4_f03_native_line_compliance_screen import (
    absolute_primal_action, one_case)


def test_indefinite_two_mode_action_uses_absolute_spectrum():
    tangent = np.diag([-2., 3.])
    right = np.array([[1., 0.], [0., 1.]])
    action, residual, ratio = absolute_primal_action(tangent, right)
    np.testing.assert_allclose(action, np.diag([.5, 1/3]), rtol=1e-14)
    assert residual < 1e-14
    assert ratio == pytest.approx(2/3)
    signed = np.array([1., 1.])@np.linalg.solve(tangent, [1., 1.])
    absolute = np.array([1., 1.])@action@np.array([1., 1.])
    assert signed < 0 < absolute


def test_absolute_action_rejects_asymmetry_and_null_mode():
    with pytest.raises(ValueError, match="symmetric"):
        absolute_primal_action(np.array([[1., 1.], [0., 2.]]),
                               np.ones((2, 1)))
    with pytest.raises(ValueError, match="null mode"):
        absolute_primal_action(np.diag([1., 0.]), np.ones((2, 1)))


def test_native_case_keeps_signed_result_and_exposes_distinct_norm():
    signed = one_case("Q4", 1, "piecewise_constant")
    absolute = one_case("Q4", 1, "piecewise_constant",
                        absolute_primal=True)
    assert signed["primal_metric"] == "signed"
    assert absolute["primal_metric"] == "spectral_absolute"
    assert signed["free_primal"] == absolute["free_primal"]
    assert absolute["minimum_quotient_lower"] > 0.
    assert absolute["scaled_solve_residual"] < 1e-8


def test_q4_shell_trace_loses_rows_at_two_multipliers_per_host():
    one_per_host = one_case("Q4", 4, "piecewise_constant",
                            n_intervals=4, absolute_primal=True)
    two_per_host = one_case("Q4", 4, "piecewise_constant",
                            n_intervals=8, absolute_primal=True)
    assert (one_per_host["shell_row_rank"],
            one_per_host["shell_row_count"]) == (24, 24)
    assert (two_per_host["shell_row_rank"],
            two_per_host["shell_row_count"]) == (42, 48)
    assert two_per_host["minimum_shell_only_quotient_lower"] < 1e-8
    assert two_per_host["minimum_beam_only_quotient_lower"] > 1.
