"""Three bounded whole-panel L1 development levels, not F03 qualification."""

import numpy as np
import pytest

from scripts.b3_e4_f03_l1_candidate_compare import SPACES, evaluate_level


@pytest.mark.parametrize("segments", (2, 4, 8))
def test_whole_panel_and_native_refine_under_the_same_line_law(segments):
    result = evaluate_level(segments, globally_refined=True)
    assert result["grid_policy"] == "whole_shell_and_beam"
    assert result["line_interval_m"] == [.5, 1.]
    np.testing.assert_allclose(result["shell_grid_x_m"],
                               np.linspace(0., 1., 2*segments+1),
                               rtol=0., atol=0.)
    np.testing.assert_allclose(result["shell_grid_y_m"],
                               np.linspace(-.1, .1, segments+1),
                               rtol=0., atol=0.)
    assert result["native_half_cells"] == 2*segments
    assert result["loads"] == {"shell_fy_N": 1000.,
                               "beam_tip_mx_Nm": 100.}
    assert set(result["candidates"]) == set(SPACES)
    for candidate in result["candidates"].values():
        actual = candidate["actual_PL"]
        assert actual["resultant_dofs"] == 18*segments
        assert actual["equilibrium_relative"] < 2e-8
        assert actual["compatibility_relative"] < 2e-8
        for case in actual["cases"].values():
            assert case["external_work_Nm"] > 0.
            np.testing.assert_allclose(
                case["shell_operator_work_Nm"]+
                case["native_retained_operator_work_Nm"],
                case["external_work_Nm"], rtol=1e-8, atol=1e-11)
            assert case["force_balance_N"] < 2e-8*max(
                1., case["interface_force_N"])
            assert case["origin_moment_balance_Nm"] < 2e-8*max(
                1., case["interface_origin_moment_Nm"])
