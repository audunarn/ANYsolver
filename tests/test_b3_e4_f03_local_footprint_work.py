"""Bounded actual E4/B3 footprint mechanics checks, not G0 acceptance."""

import numpy as np
import pytest

from scripts._b3_e4_f03_shell_strip_pose_candidate import reference_spatial_trace_strip
from scripts._b3_e4_f03_shell_trace import make_shell
from scripts.b3_e4_f03_local_footprint_work import (
    case, structured_q4_patch_trace, structured_q4_point_shape,
)


def test_structured_patch_trace_matches_existing_uniform_native_rows():
    panel=make_shell(8,"Q4",n_y=8)
    xs=np.linspace(-.5,1.5,17)
    ys=np.linspace(-.5,.5,9)
    trace=structured_q4_patch_trace(xs,ys)
    native=reference_spatial_trace_strip(
        panel,.95,half_length=.05,half_width=.05)
    assert np.max(np.abs(trace-native))<1e-12
    for x in (.9,1.):
        for y in (-.05,.05):
            nodes,values=structured_q4_point_shape(xs,ys,x,y)
            expected_nodes,expected_values=panel._shape(x,y)
            observed=np.bincount(nodes,weights=values,
                                 minlength=panel.node_count)
            expected=np.bincount(expected_nodes,weights=expected_values,
                                 minlength=panel.node_count)
            assert np.max(np.abs(observed-expected))<1e-12


@pytest.mark.parametrize("topology", ["Q4", "S3-V2D"])
def test_distinct_footprint_work_and_finite_rigid_pullback(topology):
    result = case(topology)
    mode = result["supported_shell_transverse_shear_mode"]
    chart = result["finite_rigid_chart"]
    distributing = result["finite_distributing_chart"]
    termination = result["tip_termination_local"]
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
    assert termination["rows_and_supported_ranks"] == {
        "distributing": [6, 6], "rigid": [12, 12]}
    assert termination["reference_gap_max"] < 1e-12
    assert abs(termination["shell_my_nm"]["distributing"]-100.) < 1e-8
    assert abs(termination["shell_my_nm"]["rigid"]-100.) < 1e-8
    loaded = termination["loaded_linear_reference"]
    for family in ("distributing", "rigid"):
        for action in ("torque_mx_100nm", "shear_fz_1000n"):
            response = loaded[family][action]
            assert response["scaled_equilibrium_residual"] < 1e-9
            assert response["weak_gap_norm"] < 1e-9
            assert response["work_error_j"] < 1e-9
            assert response["global_force_balance_n"] < 1e-7
            assert response["global_moment_balance_nm"] < 1e-7
    assert abs(loaded["distributing"]["torque_mx_100nm"]["tip_rx_rad"] -
               loaded["rigid"]["torque_mx_100nm"]["tip_rx_rad"]) > 1e-7
    assert abs(loaded["distributing"]["shear_fz_1000n"]["tip_uz_m"] -
               loaded["rigid"]["shear_fz_1000n"]["tip_uz_m"]) > 1e-7
