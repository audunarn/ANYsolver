"""One bounded finite-chart gate for the six-resultant surface candidate."""

from scripts.b3_e4_f03_distributed_surface_finite import finite_chart_screen


def test_actual_e4_b3_surface_work_has_consistent_finite_derivatives():
    result = finite_chart_screen()
    assert result["reference_gap_max_m_rad"] < 1e-12
    assert result["reference_jacobian_direction_error"] < 1e-12
    assert result["nonzero_gap_norm_m_rad"] > 1e-4
    assert abs(result["nonzero_multiplier_mixed_work_j"]) > 1e-3
    assert result["first_direction_error_j"] < 1e-7
    assert result["mixed_direction_error_j"] < 1e-6
    assert result["finite_common_rigid_gap_error"] < 1e-12
    assert abs(result["common_rigid_virtual_work_j"]) < 1e-9
    assert result["quadrature_points"] == 18
