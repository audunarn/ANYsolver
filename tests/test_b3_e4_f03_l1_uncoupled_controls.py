"""Matched uncoupled controls for the bounded whole-panel L1 screen."""

import numpy as np
import pytest

from scripts.b3_e4_f03_l1_uncoupled_controls import evaluate


@pytest.mark.parametrize("segments", (2, 4, 8))
def test_uncoupled_shell_and_native_controls(segments):
    result = evaluate(segments)
    assert result["shell_nodes"] == (2*segments+1)*(segments+1)
    assert result["native_half_cells"] == 2*segments
    assert result["shell_free_equilibrium_relative"] < 2e-8
    assert result["native_free_equilibrium_relative"] < 2e-8
    assert result["shell_only_fy_load_displacement_work_Nm"] > 0.
    np.testing.assert_allclose(
        result["shell_only_physical_work_Nm"]+
        result["shell_only_completion_work_Nm"],
        result["shell_only_fy_load_displacement_work_Nm"],
        rtol=1e-8, atol=1e-11)
    assert result["native_only_torque_load_displacement_work_Nm"] > 0.
    np.testing.assert_allclose(result["native_only_torque_tip_twist_rad"],
                               result["native_uniform_torsion_oracle_rad"],
                               rtol=1e-6, atol=1e-10)
