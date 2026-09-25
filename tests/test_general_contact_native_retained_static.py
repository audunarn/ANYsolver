"""Development checks for one coupled native retained beam and fixed plane."""

import numpy as np
import pytest

from anysolver._ge_beam3_native_definition import NativeBeamDefinition
from anysolver._ge_beam3_native_generalized_loading import DistributedPattern
from anysolver._ge_beam3_native_line_loading import LinePattern
from anysolver._ge_beam3_retained_nodal_loading import NodalDeadForces, Program
from anysolver.general_contact.native_retained_line_plane import (
    NativeRetainedRoundLinePlane,
)
from anysolver.general_contact.native_retained_static import (
    NativeRetainedRoundPlaneAnalysis,
)
from test_ge_beam3_native_generalized_modal import make


def _analysis(*, curved=True, targets=(1.0,), iterations=24,
              plane_z=-0.05, contact_element_id=1):
    model, _, inertias = make(curved, clamped=True)
    element = model.mesh.elements[1]
    definition = NativeBeamDefinition.capture(element, inertias[1])
    program = Program(
        targets,
        DistributedPattern(LinePattern(()), ()),
        NodalDeadForces(((3, 0.0, 0.0, -0.005),)),
        max_iterations=iterations,
    )
    kernel = NativeRetainedRoundLinePlane(
        contact_element_id, element.operator.reference,
        radius_m=0.05,
        plane_origin_m=np.array((0.0, 0.0, plane_z)),
        plane_normal=np.array((0.0, 0.0, 1.0)),
        line_stiffness_n_per_m2=100.0,
        energy_tolerance_j=1e-10,
        force_tolerance_n=1e-9,
        tangent_tolerance_n_per_m=1e-8,
        maximum_intervals=64,
    )
    return NativeRetainedRoundPlaneAnalysis(
        (definition,), tuple(model.boundary_conditions), program, kernel,
        gap_tolerance_m=1e-3, equilibrium_tolerance=1e-8,
    )


def test_coupled_retained_beam_contact_moves_internal_coordinates():
    owner = _analysis()
    result = owner.solve()
    assert result.status == "completed", result.failure
    assert result.accepted.completed_targets == 1
    assert result.accepted.contact.beam_force_n[2] > 0.0
    assert result.accepted.contact.minimum_gap_m >= -owner.gap_tolerance
    assert np.linalg.norm(result.accepted.contact.residual[18:24]) > 1e-5
    assert np.linalg.norm(
        result.accepted.mechanical.cell_rotations
        - owner.initial.mechanical.cell_rotations
    ) > 0.0
    residual, jacobian, metrics, _, _ = owner._assemble(
        result.accepted.mechanical, 1.0, result.accepted.histories,
    )
    assert max(metrics) < owner.equilibrium_tolerance
    assert np.linalg.norm(residual[owner.context.free]) < 1e-8
    direction = np.zeros(owner.context.count)
    direction[14] = -0.01
    direction[18] = 0.002
    direction[21] = -0.002
    step = 1e-5
    plus = owner.context.advance(result.accepted.mechanical, step*direction)
    minus = owner.context.advance(result.accepted.mechanical, -step*direction)
    positive = owner._assemble(plus, 1.0, result.accepted.histories)[0]
    negative = owner._assemble(minus, 1.0, result.accepted.histories)[0]
    observed = (positive-negative)/(2.0*step)
    predicted = jacobian @ direction
    assert np.linalg.norm(observed-predicted)/max(1.0, np.linalg.norm(predicted)) < 1e-5


def test_initial_interference_is_rejected():
    with pytest.raises(ValueError, match="initial native contact penetration"):
        _analysis(plane_z=0.0)


def test_contact_definition_must_bind_native_element():
    with pytest.raises(ValueError, match="does not bind"):
        _analysis(contact_element_id=2)


def test_iteration_failure_preserves_virgin_accepted_state():
    owner = _analysis(iterations=1)
    result = owner.solve()
    assert result.status == "failed"
    assert result.accepted.completed_targets == 0
    np.testing.assert_array_equal(
        result.accepted.mechanical.positions, owner.initial.mechanical.positions,
    )


def test_failed_second_target_preserves_accepted_prefix():
    owner = _analysis(targets=(0.0, 1.0), iterations=1)
    result = owner.solve()
    assert result.status == "failed"
    assert result.accepted.completed_targets == 1
    np.testing.assert_array_equal(
        result.accepted.mechanical.positions, owner.initial.mechanical.positions,
    )
