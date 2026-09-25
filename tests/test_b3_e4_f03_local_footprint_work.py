"""Bounded actual E4/B3 footprint mechanics checks, not G0 acceptance."""

import pytest

from scripts.b3_e4_f03_local_footprint_work import case


@pytest.mark.parametrize("topology", ["Q4", "S3-V2D"])
def test_distinct_footprint_work_and_finite_rigid_pullback(topology):
    result = case(topology)
    mode = result["supported_shell_transverse_shear_mode"]
    chart = result["finite_rigid_chart"]
    distributing = result["finite_distributing_chart"]
    assert mode["distributing_gap_max_m_rad"] < 2e-12
    assert mode["rigid_gap_l2_m"] > 1e-5
    assert abs(result["paired_shell_my_nm"]["rigid"] - 100.) < 1e-8
    assert abs(chart["mixed_hessian_j"]) > 1e-3
    assert chart["mixed_error_j"] < 1e-5
    assert chart["objective_gap_work_error"] < 1e-10
    assert chart["force_balance_n"] < 1e-9
    assert chart["moment_balance_nm"] < 1e-9
    assert chart["physical_work_error_j"] < 1e-9
    assert abs(distributing["mixed_hessian_j"]) > 1e-3
    assert distributing["first_error_j"] < 1e-6
    assert distributing["mixed_error_j"] < 1e-5
    assert distributing["force_balance_n"] < 1e-9
    assert distributing["moment_balance_nm"] < 1e-9
    assert distributing["physical_work_error_j"] < 1e-9
