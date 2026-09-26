"""Independent projected-root controls for a many-mode pressure proposal."""

import numpy as np
import pytest

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
