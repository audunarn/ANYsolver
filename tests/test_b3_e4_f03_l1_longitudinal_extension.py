"""One directed 16-edge coupled extension, not reference convergence."""

import numpy as np

from scripts.b3_e4_f03_l1_candidate_compare import SPACES, evaluate_level


def test_longitudinal_shell_and_native_extension_under_same_l1_law():
    result = evaluate_level(16, globally_refined=True,
                            transverse_segments=8, actual_only=True)
    assert result["grid_policy"] == "longitudinal_shell_and_beam"
    assert result["line_interval_m"] == [.5, 1.]
    np.testing.assert_allclose(result["shell_grid_x_m"],
                               np.linspace(0., 1., 33), rtol=0., atol=0.)
    np.testing.assert_allclose(result["shell_grid_y_m"],
                               np.linspace(-.1, .1, 9), rtol=0., atol=0.)
    assert result["native_half_cells"] == 32
    assert result["loads"] == {"shell_fy_N": 1000.,
                               "beam_tip_mx_Nm": 100.}
    assert set(result["candidates"]) == set(SPACES)
    for candidate in result["candidates"].values():
        assert set(candidate) == {"actual_PL"}
        solved = candidate["actual_PL"]
        assert solved["resultant_dofs"] == 288
        assert solved["equilibrium_relative"] < 2e-8
        assert solved["compatibility_relative"] < 2e-8
        for case in solved["cases"].values():
            assert case["external_work_Nm"] > 0.
            np.testing.assert_allclose(
                case["shell_operator_work_Nm"]+
                case["native_retained_operator_work_Nm"],
                case["external_work_Nm"], rtol=1e-8, atol=1e-11)
            assert case["force_balance_N"] < 2e-8*max(
                1., case["interface_force_N"])
            assert case["origin_moment_balance_Nm"] < 2e-8*max(
                1., case["interface_origin_moment_Nm"])
