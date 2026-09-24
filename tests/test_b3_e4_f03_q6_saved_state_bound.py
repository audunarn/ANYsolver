"""Saved Q6 component-error diagnostic; no G0 qualification implied."""

from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

from scripts._b3_e4_f03_q6_saved_state_bound import (
    bound_components, evaluate_saved)


def test_component_error_encloses_known_small_solution():
    matrix = sparse.diags([2., 3., 4., 5.], format="csc")
    exact = np.array([1., -2., 0.5, -0.25])
    candidate = exact + np.array([1e-7, -2e-7, 3e-7, -4e-7])
    rhs = matrix@exact
    result = bound_components(matrix, rhs, candidate, 0.5,
                              np.array([2.]), np.array([3., 4., 5.]))
    assert np.max(np.abs(exact-candidate)) <= result[
        "scaled_state_component_error_upper"]
    assert abs(2*(exact[0]-candidate[0])) <= result[
        "physical_displacement_component_error_upper"]
    assert np.max(np.abs(np.array([3., 4.])*(
        exact[-3:-1]-candidate[-3:-1]))) <= result[
            "physical_root_force_component_error_upper"]
    assert abs(5*(exact[-1]-candidate[-1])) <= result[
        "physical_root_moment_component_error_upper"]


@pytest.mark.parametrize("inverse_bound", [0., -1., float("nan")])
def test_invalid_inverse_bound_rejected(inverse_bound):
    matrix = sparse.eye(4, format="csc")
    with pytest.raises(ValueError, match="invalid saved"):
        bound_components(matrix, np.ones(4), np.ones(4), inverse_bound,
                         np.ones(1), np.ones(3))


def test_x2_saved_certificate_residual_and_component_bounds():
    certificate_dir = (Path(__file__).parents[1]/"docs"/"agent_plans"/
        "B3_GE_E4_PL_G0_F03_Q6_X2_SHARED_ASSEMBLY_REHEARSAL_20260924"/
        "certificate")
    if not (certificate_dir/"scaled_system.npz").exists():
        pytest.skip("local ignored X2 archive is unavailable")
    result = evaluate_saved(certificate_dir)
    assert result["case_id"] == "X2"
    assert result["residual_two_upper_recomputed"] < 3e-13
    assert result["physical_displacement_component_error_upper"] < 6e-14
    assert result["physical_root_force_component_error_upper"] < 7e-4
    assert result["physical_root_moment_component_error_upper"] < 3e-4
    assert result["scientific_registration"] is False
