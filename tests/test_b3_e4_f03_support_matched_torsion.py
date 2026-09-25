"""Physical torque and linear work controls for the bounded F03 screen."""

import numpy as np
import pytest

from scripts.b3_e4_f03_weak_line_resolution_screen import one_case
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


@pytest.mark.parametrize("topology,n_y", (("Q4", 4), ("S3-V2D", 8)))
def test_both_edge_supports_transfer_tip_torque_and_balance_work(topology, n_y):
    result = one_case(topology, 4, "continuous_linear", n_s=4,
                      native_half_cells=16, n_y=n_y,
                      shell_support_policy="both_xy_edges")
    assert result["applied_torque_x_n_m"] == 100.
    assert result["shell_support_reaction_torque_x_n_m"] < -1.
    assert result["beam_root_reaction_torque_x_n_m"] < -1.
    assert abs(result["global_torque_x_balance_n_m"]) < 1e-7
    np.testing.assert_allclose(
        result["shell_energy_j"]+result["beam_energy_j"],
        .5*result["applied_torque_x_n_m"]*result["tip_rx_rad"],
        rtol=1e-9, atol=1e-12)
    assert result["scaled_equilibrium_residual"] < 1e-12


@pytest.mark.parametrize("topology", ("Q4", "S3-V2D"))
def test_offset_root_torque_uses_force_lever_about_common_origin(topology):
    offset = .0675
    result = one_case(
        topology, 2, "piecewise_constant", n_s=2, n_y=4,
        native_half_cells=4, thickness=.035,
        beam_z_offset=offset,
        beam_torsion_constant=square_torsion_constant(),
        shell_port="physical_strip_005_005",
        shell_support_policy="full_left_edge")
    assert result["beam_reference_z_m"] == offset
    assert result["beam_torsion_constant_m4"] == pytest.approx(
        square_torsion_constant())
    assert result["beam_root_reaction_torque_x_about_origin_n_m"] == pytest.approx(
        result["beam_root_reaction_torque_x_n_m"]
        - offset * result["beam_root_reaction_fy_n"], abs=1e-11)
    assert abs(result["global_torque_x_balance_n_m"]) < 1e-8
    assert result["scaled_equilibrium_residual"] < 1e-11
