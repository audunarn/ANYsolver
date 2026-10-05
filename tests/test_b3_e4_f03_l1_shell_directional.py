"""Directional shell-only resolution check around the eight-edge control."""

import numpy as np
import pytest

from scripts.b3_e4_f03_l1_uncoupled_controls import directional_shell_control


@pytest.mark.parametrize("axis,nx,ny", (("longitudinal", 33, 9),
                                        ("transverse", 17, 17)))
def test_one_direction_shell_refinement(axis, nx, ny):
    result = directional_shell_control(axis)
    assert result["shell_nodes"] == nx*ny
    assert result["shell_dofs"] == 6*nx*ny < 1800
    assert result["shell_free_equilibrium_relative"] < 2e-8
    assert result["shell_only_fy_load_displacement_work_Nm"] > 0.
    np.testing.assert_allclose(
        result["shell_only_physical_work_Nm"]+
        result["shell_only_completion_work_Nm"],
        result["shell_only_fy_load_displacement_work_Nm"],
        rtol=1e-8, atol=1e-11)
