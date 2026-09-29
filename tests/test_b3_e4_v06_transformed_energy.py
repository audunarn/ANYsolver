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
