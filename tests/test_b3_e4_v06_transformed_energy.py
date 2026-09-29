"""Analytical elastic transformed-section patch for the experimental GE owner."""

import pytest

from scripts.b3_e4_v06_transformed_energy_patch_dev import evaluate


@pytest.mark.parametrize("intervals", (2, 4, 8))
@pytest.mark.parametrize("sign", (-1, 1))
def test_eccentric_axial_bending_energy_and_signed_cross_term(intervals, sign):
    result = evaluate(intervals, sign)
    assert result["max_point_gap"] < 1e-10
    assert result["max_retained_stationarity"] < 1e-6
    assert result["axial_relative_error"] < 1e-10
    assert abs(result["curvature_relative_excess"]) < 1e-9
    assert result["relative_cross_error"] < 1e-10
    assert result["normalized_skew"] < 1e-10
    assert abs(result["shell_cross_energy_j"]) < 1e-9
    loaded = result["loaded_patch"]
    assert loaded["status"] == "completed"
    assert loaded["point_transfer_fit_stop_code"] in (1, 2)
    assert loaded["exact_field_free_ratio_after_point_transfer"] < 1e-10
    assert loaded["max_translation_error_m"] < 1e-9
    assert loaded["max_rotation_error_rad"] < 1e-9
    assert loaded["max_retained_scale_error"] < 1e-7
    assert loaded["constraint_max"] < 1e-9
    assert loaded["free_equilibrium_ratio"] < 1e-8
    assert loaded["support_force_error_n"] < 1e-4
    assert loaded["support_moment_error_nm"] < 1e-4
    assert loaded["relative_energy_error"] < 1e-8
