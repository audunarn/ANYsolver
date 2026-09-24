"""Loaded native line work must not borrow Q4/S3 drilling completion."""

import pytest

from scripts.b3_e4_f03_weak_line_resolution_screen import one_case


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
@pytest.mark.parametrize("load,thickness", (
    ("torsion", .07), ("transverse_force_z", .07), ("torsion", .035)))
def test_loaded_torque_and_shear_have_physical_shell_work(
        topology, load, thickness):
    result = one_case(
        topology, 2, "piecewise_constant",
        shell_port="local_translation", load_kind=load,
        n_s=2, n_y=2, native_half_cells=8, thickness=thickness,
        shell_support_policy="full_left_edge")
    physical = result["shell_component_physical_energy_j"]
    assert physical > 0.
    assert result["shell_physical_energy_j"] == pytest.approx(physical, rel=1e-9)
    assert abs(result["shell_numerical_energy_j"]) < 1e-10*physical
    assert abs(result["shell_component_closure_error_j"]) < 1e-9*physical
    if load == "torsion":
        assert abs(result["global_torque_x_balance_n_m"]) < 1e-7
        assert abs(result["shell_support_minus_interface_torque_x_n_m"]) < 1e-7
    else:
        assert abs(result["global_force_z_balance_n"]) < 1e-7
        assert abs(result["shell_support_minus_interface_fz_n"]) < 1e-7
