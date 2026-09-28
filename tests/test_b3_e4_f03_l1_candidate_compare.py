"""Focused A/B virgin KKT screen, not a registered F03 assessment."""

import numpy as np
import pytest

from scripts.b3_e4_f03_l1_candidate_compare import LOADS, SPACES, evaluate_level


@pytest.mark.parametrize("segments", (2, 4))
def test_same_physical_actions_supported_kkt_and_interface_work(segments):
    result = evaluate_level(segments)
    assert result["line_interval_m"] == [.5, 1.]
    assert result["shell_grid_y_m"] == [-.1, 0., .1]
    assert result["shell_thickness_m"] == .035
    assert result["beam_axis_z_m"] == .0675
    assert result["line_section_offset_z_m"] == -.05
    assert result["loads"] == {"shell_fy_N": 1000., "beam_tip_mx_Nm": 100.}
    assert result["native_half_cells"] == 2*segments
    assert result["completion_non_drill_relative"] > 0.
    assert set(result["candidates"]) == set(SPACES)

    for name in SPACES:
        candidates = result["candidates"][name]
        for variant in ("actual_PL", "actual_PL_drill_frozen",
                        "E4_physical_component"):
            solved = candidates[variant]
            assert solved["dual_rows"] == (6*segments+4 if name == SPACES[0]
                                           else 5*segments)
            assert solved["resultant_dofs"] == 18*segments
            assert solved["equilibrium_relative"] < 2e-8
            assert solved["compatibility_relative"] < 2e-8
            assert solved["scaled_constraint_schur_min_eigen"] > 0.
            assert set(solved["cases"]) == set(LOADS)
            for case in solved["cases"].values():
                assert case["external_work_Nm"] > 0.
                np.testing.assert_allclose(
                    case["shell_operator_work_Nm"],
                    case["shell_physical_component_work_Nm"]+
                    case["shell_completion_work_Nm"], rtol=1e-8, atol=1e-11)
                np.testing.assert_allclose(
                    case["external_work_Nm"],
                    case["shell_operator_work_Nm"]+
                    case["native_retained_operator_work_Nm"],
                    rtol=1e-8, atol=1e-11)
                np.testing.assert_allclose(
                    case["shell_interface_work_Nm"]+
                    case["native_interface_work_Nm"], 0., atol=2e-8)
                assert case["interface_force_N"] > 0.
                assert case["interface_origin_moment_Nm"] > 0.
                assert case["force_balance_N"] < 2e-8*max(
                    1., case["interface_force_N"])
                assert case["origin_moment_balance_Nm"] < 2e-8*max(
                    1., case["interface_origin_moment_Nm"])

            fy = solved["cases"]["shell_fy"]
            torque = solved["cases"]["beam_tip_mx"]
            # Maxwell reciprocity for the two physical work-conjugate loads.
            np.testing.assert_allclose(torque["shell_tip_y_m"]/100.,
                                       fy["native_tip_twist_rad"]/1000.,
                                       rtol=3e-7, atol=1e-13)
        assert candidates["PL_completion_removal_work_change_relative"]["shell_fy"] > 0.
        assert np.isfinite(candidates["drill_coordinate_freeze_work_change_relative"][
            "shell_fy"])
