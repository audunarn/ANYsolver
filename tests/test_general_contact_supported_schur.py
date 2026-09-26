"""Independent projected-root controls for a many-mode pressure proposal."""

import numpy as np
import pytest
import json

from anysolver.general_contact.supported_schur import propose_supported_schur_step


def test_nineteen_supported_active_modes_take_a_bounded_projected_root_step():
    count = 19
    pressure = np.ones(count)
    gap = -0.1*np.ones(count)
    response = 0.1*np.eye(count)
    proposal = propose_supported_schur_step(
        pressure, gap, np.ones(count, dtype=bool), response,
        normal_stiffness=100.0, maximum_pressure=5.0,
        maximum_pressure_step=2.0, maximum_modes=32,
    )
    assert proposal is not None
    assert len(proposal.active_indices) == count
    np.testing.assert_allclose(proposal.multipliers, 2.0)
    assert proposal.predicted_residual_after < 1.0e-12


def test_projected_derivative_sign_matches_independent_directional_difference():
    pressure = np.array([1.0, 2.0, 0.0])
    gap = np.array([-0.1, -0.2, 0.3])
    response = np.array([[0.2, 0.03, 0.0],
                         [0.01, 0.3, 0.0],
                         [0.0, 0.0, 0.4]])
    direction = np.array([0.4, -0.2, 0.0])

    def residual(value):
        updated_gap = gap + response @ (value-pressure)
        return np.maximum(0.0, value-10.0*updated_gap)-value

    step = 1.0e-6
    derivative = (residual(pressure+step*direction)
                  - residual(pressure-step*direction))/(2.0*step)
    np.testing.assert_allclose(derivative, -10.0*response @ direction,
                               rtol=1.0e-8, atol=1.0e-9)


def test_singular_or_resource_exhausted_schur_does_not_soften_law():
    arguments = (np.ones(3), -np.ones(3), np.ones(3, dtype=bool))
    assert propose_supported_schur_step(
        *arguments, np.zeros((3, 3)), normal_stiffness=1.0,
        maximum_pressure=10.0, maximum_pressure_step=10.0,
        maximum_modes=3,
    ) is None
    with pytest.raises(MemoryError, match="Schur cap"):
        propose_supported_schur_step(
            *arguments, np.eye(3), normal_stiffness=1.0,
            maximum_pressure=10.0, maximum_pressure_step=10.0,
            maximum_modes=2,
        )


def test_rank_revealing_step_only_corrects_responsive_pressure_modes():
    pressure = np.ones(3)
    gap = np.array([-0.1, -0.1, -0.01])
    response = np.diag([0.1, 0.1, 0.0])
    diagnostics = {}
    proposal = propose_supported_schur_step(
        pressure, gap, np.ones(3, dtype=bool), response,
        normal_stiffness=10.0, maximum_pressure=5.0,
        maximum_pressure_step=2.0, maximum_modes=3,
        diagnostics=diagnostics,
    )
    assert proposal is not None
    assert diagnostics["schur_effective_rank"] == 2
    assert diagnostics["schur_truncated_response"] is True
    assert diagnostics["schur_scaled_condition"] is None
    assert proposal.scaled_condition is None
    json.dumps(diagnostics, allow_nan=False)
    np.testing.assert_allclose(proposal.multipliers, [2.0, 2.0, 1.0])
    equilibrated_gap = gap + response @ (proposal.multipliers-pressure)
    actual_residual = (np.maximum(0.0, proposal.multipliers
                                  - 10.0*equilibrated_gap)
                       - proposal.multipliers)
    assert np.linalg.norm(actual_residual, ord=np.inf) < 0.11


def test_bounded_step_below_verification_reduction_is_declined():
    diagnostics = {}
    proposal = propose_supported_schur_step(
        np.array([1.0]), np.array([-0.1]), np.array([True]),
        np.array([[0.1]]), normal_stiffness=10.0,
        maximum_pressure=5.0, maximum_pressure_step=0.05,
        maximum_modes=1, diagnostics=diagnostics,
    )
    assert proposal is None
    assert diagnostics["schur_ineligible"] == (
        "bounded_step_or_predicted_merit_failed"
    )
    assert diagnostics["schur_full_step_max_pa"] == pytest.approx(1.0)
    assert diagnostics["schur_best_fixed_branch_fraction"] == pytest.approx(1.0/32.0)
    assert diagnostics["schur_best_fixed_branch_residual_pa"] == pytest.approx(0.96875)
    assert diagnostics["schur_best_projected_fraction"] == pytest.approx(1.0/32.0)
    assert diagnostics["schur_best_projected_residual_pa"] == pytest.approx(0.96875)
    assert diagnostics["schur_backtrack_rejections"] == {
        "step_cap": 5,
        "negative_pressure": 0,
        "pressure_cap": 0,
        "active_branch": 0,
        "predicted_merit": 4,
    }


def test_projected_active_set_can_drop_a_nonnegative_pressure_mode():
    diagnostics = {}
    proposal = propose_supported_schur_step(
        np.array([0.04, 0.04]), np.array([-0.1, 0.001]),
        np.array([True, True]), np.diag([0.1, 0.01]),
        normal_stiffness=10.0, maximum_pressure=5.0,
        maximum_pressure_step=2.0, maximum_modes=2,
        diagnostics=diagnostics,
    )
    assert proposal is not None
    assert diagnostics["schur_proposal_kind"] == "projected_active_set"
    assert proposal.active_indices == (0,)
    np.testing.assert_allclose(proposal.multipliers, [1.04, 0.0])
    assert proposal.predicted_residual_after < 1.0e-12
