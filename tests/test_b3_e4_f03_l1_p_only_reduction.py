"""One unregistered supported L1 p-only stationary-reduction check."""

from scripts.b3_e4_f03_l1_p_only_reduction import evaluate


def test_supported_virgin_l1_resultant_only_reduction():
    result = evaluate()
    assert result["dual_rows"] == 18
    assert result["resultant_dofs"] == 72
    assert result["free_shell_drill_coordinates"] > 0
    assert result["max_free_shell_drill_stiffness"] > 0.
    assert result["max_free_shell_drill_action"] == 0.
    assert result["max_resultant_action"] == 0.
    assert result["retained_cell_rotation_action"] > 0.
    assert result["stationary_backward_residual"] < 1e-10
    assert result["compliance_parity_relative"] < 1e-8
    assert result["physical_component_quotient_positive"]
    assert result["physical_component_compliance_parity_relative"] < 1e-8
