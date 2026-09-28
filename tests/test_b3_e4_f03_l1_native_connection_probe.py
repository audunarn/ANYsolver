"""Bounded L1 kinematics only; no formal F03 execution or acceptance."""

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from anysolver.corotational import rotation_matrix_from_vector
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts.b3_e4_f03_l1_native_connection_probe import (
    L1LogConnection, shell_trace, six_gap, spatial_gap,
)


def _case():
    beam = build(4, z_offset=.0675, assemble=False)
    element, cell, weight, _ = beam._locate(.95)
    port = NativeHalfCellSpatialPort(beam.context, element, cell, weight)
    reference = np.array(((.9, 0., 0.), (1., 0., 0.)))
    return beam, port, reference


def test_reference_six_rows_and_native_half_cell_identity():
    beam, port, reference = _case()
    state = beam.context.initial.mechanical
    assert port.cell == 1
    assert 0. < port.weight < 1.
    gap, _ = six_gap(reference, np.zeros((2, 6)), .035, port, state)
    np.testing.assert_allclose(gap, 0., atol=2e-16)

    # The line carries an independent transverse shear channel, while the
    # shell-normal angular row is retained as the sixth physical point row.
    total = np.zeros((2, 6))
    total[:, 1] = 1e-4
    shear, _ = six_gap(reference, total, .035, port, state)
    np.testing.assert_allclose(shear[1], 1e-4, atol=1e-15)
    total = np.zeros((2, 6))
    total[1, 1] = 1e-4
    yaw, _ = six_gap(reference, total, .035, port, state)
    assert abs(yaw[5]) > 9e-4


def test_objective_physical_pose_work_pairing():
    beam, port, reference = _case()
    total = np.array(((.001, -.002, .0004, .03, -.02, .01),
                      (.002, .001, -.0003, -.01, .02, -.015)))
    shell, frame, _, _ = shell_trace(reference, total, .035)
    high, low, beam_frame = port.pose_pair(beam.context.initial.mechanical)
    beam_position = high+low+beam_frame@np.array((0., 0., -.05))
    original = spatial_gap(shell, frame, beam_position, beam_frame)
    rigid = rotation_matrix_from_vector(np.array((.2, -.15, .12)))
    shift = np.array((.3, -.7, .2))
    transformed = spatial_gap(rigid@shell+shift, rigid@frame,
                              rigid@beam_position+shift, rigid@beam_frame)
    np.testing.assert_allclose(transformed, original, atol=3e-16)
    dual = np.array((3., -5., 7., 11., -13., 17.))
    np.testing.assert_allclose(dual@transformed, dual@original, atol=1e-14)


def test_actual_e4_total_and_native_advance_directional_work():
    beam, port, reference = _case()
    rng = np.random.default_rng(761)
    base = rng.normal(size=beam.context.count)*2e-4
    base[:6] = 0.
    state = beam.context.advance(beam.context.initial.mechanical, base)
    total = rng.normal(size=(2, 6))*np.array((.001, .001, .001, .04, .04, .04))
    shell_direction = rng.normal(size=(2, 6))*np.array((.001, .001, .001, .03, .03, .03))
    beam_direction = rng.normal(size=beam.context.count)*.001
    beam_direction[:6] = 0.
    dual = np.array((2., -3., 5., 7., -11., 13.))
    gap, derivative = six_gap(reference, total, .035, port, state,
                              shell_direction=shell_direction,
                              beam_direction=beam_direction)
    assert np.linalg.norm(gap) > 1e-6
    step = 1e-5

    def actual_update(sign):
        trial = beam.context.advance(state, sign*step*beam_direction)
        return six_gap(reference, total+sign*step*shell_direction,
                       .035, port, trial)[0]

    finite = (actual_update(1.)-actual_update(-1.))/(2*step)
    np.testing.assert_allclose(derivative, finite, rtol=2e-7, atol=2e-10)
    np.testing.assert_allclose(dual@derivative, dual@finite,
                               rtol=2e-7, atol=2e-9)


def test_all_six_local_channels_have_independent_physical_variations():
    beam, port, reference = _case()
    state = beam.context.initial.mechanical
    zero = np.zeros((2, 6))
    beam_zero = np.zeros(beam.context.count)
    columns = []
    for axis in range(3):
        direction = np.zeros((2, 6))
        direction[:, axis] = 1.
        columns.append(six_gap(reference, zero, .035, port, state,
                               shell_direction=direction,
                               beam_direction=beam_zero)[1])
    for axis in (3, 4):
        direction = np.zeros((2, 6))
        direction[:, axis] = 1.
        columns.append(six_gap(reference, zero, .035, port, state,
                               shell_direction=direction,
                               beam_direction=beam_zero)[1])
    yaw = np.zeros((2, 6))
    yaw[0, 1], yaw[1, 1] = -.05, .05
    columns.append(six_gap(reference, zero, .035, port, state,
                           shell_direction=yaw, beam_direction=beam_zero)[1])
    assert np.linalg.matrix_rank(np.column_stack(columns), tol=1e-9) == 6


def test_degenerate_projected_material_tangent_fails_closed():
    reference = np.array(((0., 0., 0.), (0., 0., 1.)))
    with pytest.raises(ValueError, match="projected E4 material-line tangent"):
        shell_trace(reference, np.zeros((2, 6)), .035)


def test_reference_offset_log_is_stress_free_at_nontrivial_reference():
    beam, port, reference = _case()
    base = np.zeros(beam.context.count)
    base[6:9] = np.array((.002, -.001, .0005))
    state = beam.context.advance(beam.context.initial.mechanical, base)
    total = np.array(((.001, .002, .0003, .02, -.01, .03),
                      (.002, -.001, -.0004, -.01, .025, -.015)))
    connection = L1LogConnection.at_reference(reference, total, .035, port, state)
    gap, derivative = connection.evaluate(total, state)
    np.testing.assert_allclose(gap, 0., atol=2e-15)
    assert derivative is None
    assert np.linalg.norm(connection.joint._offset) > 0.
    assert np.linalg.norm(connection.joint._relative-np.eye(3)) > 1e-4


def test_log_connection_owns_immutable_reference_geometry():
    beam, port, reference = _case()
    state = beam.context.initial.mechanical
    connection = L1LogConnection.at_reference(
        reference, np.zeros((2, 6)), .035, port, state)
    expected = connection.evaluate(np.zeros((2, 6)), state)[0]
    reference[0, 0] += .1
    np.testing.assert_array_equal(
        connection.evaluate(np.zeros((2, 6)), state)[0], expected)
    with pytest.raises(ValueError):
        connection.reference.setflags(write=True)


def test_log_first_variation_at_nonzero_relative_rotation_actual_updates():
    beam, port, reference = _case()
    state = beam.context.initial.mechanical
    connection = L1LogConnection.at_reference(
        reference, np.zeros((2, 6)), .035, port, state)
    rng = np.random.default_rng(832)
    base = rng.normal(size=beam.context.count)*4e-4
    base[:6] = 0.
    trial_state = beam.context.advance(state, base)
    total = np.array(((.001, -.002, .0003, .23, -.12, .05),
                      (.002, .001, -.0004, .18, .09, -.02)))
    shell_direction = rng.normal(size=(2, 6))*np.array((.001, .001, .001, .04, .04, .04))
    beam_direction = rng.normal(size=beam.context.count)*.001
    beam_direction[:6] = 0.
    gap, derivative = connection.evaluate(
        total, trial_state, shell_direction=shell_direction,
        beam_direction=beam_direction)
    assert np.linalg.norm(gap[3:]) > .1
    dual = np.array((2., -3., 5., 7., -11., 13.))
    step = 2e-5

    def actual_update(sign):
        updated = beam.context.advance(trial_state, sign*step*beam_direction)
        return connection.evaluate(total+sign*step*shell_direction, updated)[0]

    finite = (actual_update(1.)-actual_update(-1.))/(2*step)
    np.testing.assert_allclose(derivative, finite, rtol=4e-7, atol=2e-10)
    np.testing.assert_allclose(dual@derivative, dual@finite,
                               rtol=4e-7, atol=2e-9)


def test_reference_offset_log_is_objective_under_common_rigid_motion():
    beam, port, reference = _case()
    state = beam.context.initial.mechanical
    connection = L1LogConnection.at_reference(
        reference, np.zeros((2, 6)), .035, port, state)
    total = np.array(((.001, -.002, .0003, .14, -.07, .03),
                      (.002, .001, -.0004, .11, .06, -.02)))
    shell, shell_frame, _, _ = shell_trace(reference, total, .035)
    high, low, beam_frame = port.pose_pair(state)
    beam_position = high+low+beam_frame@np.array((0., 0., -.05))
    positions = np.array((shell, beam_position))
    frames = np.array((shell_frame, beam_frame))
    original = connection.joint.evaluate(positions, frames, np.zeros(6))
    rigid = rotation_matrix_from_vector(np.array((.3, -.2, .1)))
    shift = np.array((.4, -.7, .2))
    transformed = connection.joint.evaluate(positions@rigid.T+shift,
                                            rigid@frames, np.zeros(6))
    np.testing.assert_allclose(transformed.constraints,
                               original.constraints, atol=2e-14)
    np.testing.assert_allclose(connection.evaluate(total, state)[0],
                               original.constraints, atol=2e-14)


def test_log_rejects_relative_rotation_outside_chart():
    beam, port, reference = _case()
    state = beam.context.initial.mechanical
    connection = L1LogConnection.at_reference(
        reference, np.zeros((2, 6)), .035, port, state)
    reversed_line = np.zeros((2, 6))
    reversed_line[0, 0] = -.8
    reversed_line[1, 0] = -1.0
    with pytest.raises(ValueError, match="relative rotation must remain below"):
        connection.evaluate(reversed_line, state)


@pytest.mark.parametrize("angle", (np.pi/2, np.pi))
def test_local_angular_chart_rejects_singular_relative_rotations(angle):
    rotated = rotation_matrix_from_vector(np.array((angle, 0., 0.)))
    with pytest.raises(ValueError, match="outside the local probe chart"):
        spatial_gap(np.zeros(3), np.eye(3), np.zeros(3), rotated)


def test_composed_nonzero_multiplier_work_tangent_and_second_plateau():
    beam, port, reference = _case()
    initial = beam.context.initial.mechanical
    connection = L1LogConnection.at_reference(reference, np.zeros((2, 6)),
                                               .035, port, initial)
    rng = np.random.default_rng(517)
    beam_base = rng.normal(size=beam.context.count)*.002
    beam_base[:6] = 0.
    state = beam.context.advance(initial, beam_base)
    total = np.array(((.002, -.001, .0003, .2, -.1, .04),
                      (.003, .002, -.0004, .13, .09, -.03)))
    dual = np.array((120., -85., 150., 5., -7., 11.))
    value, gap, residual, hessian = connection.work_tangent(total, state, dual)
    np.testing.assert_allclose(gap, connection.evaluate(total, state)[0], atol=2e-14)
    np.testing.assert_allclose(value, dual@gap, atol=2e-13)
    np.testing.assert_allclose(hessian, hessian.T, atol=2e-12)

    shell_direction = rng.normal(size=(2, 6))*np.array((.03, .03, .03, .2, .2, .2))
    beam_direction = rng.normal(size=beam.context.count)*.03
    beam_direction[:6] = 0.
    for element in range(len(beam.context.elements)):
        begin = beam.context.nodal_count+24*element
        beam_direction[begin:begin+6] *= 5.
    direction = np.r_[shell_direction.ravel(), beam_direction]
    analytic_first = float(residual@direction)
    analytic_second = float(direction@hessian@direction)
    assert abs(analytic_second) > 1e-5
    first_gap = connection.evaluate(total, state,
                                    shell_direction=shell_direction,
                                    beam_direction=beam_direction)[1]
    np.testing.assert_allclose(analytic_first, dual@first_gap, atol=3e-11)

    def work(step):
        updated = beam.context.advance(state, step*beam_direction)
        return float(dual@connection.evaluate(total+step*shell_direction, updated)[0])

    errors = []
    for step in (.02, .01, .005):
        finite = (work(step)-2*value+work(-step))/(step*step)
        errors.append(abs(finite-analytic_second))
    finite_first = (work(.005)-work(-.005))/.01
    np.testing.assert_allclose(finite_first, analytic_first,
                               rtol=3e-5, atol=2e-7)
    assert errors[1] < .4*errors[0]
    assert errors[2] < .4*errors[1]
    assert errors[2] <= 3e-6*max(1., abs(analytic_second))

    shell_second = rng.normal(size=(2, 6))*np.array((.02, .02, .02, .1, .1, .1))
    beam_second = rng.normal(size=beam.context.count)*.02
    beam_second[:6] = 0.
    mixed = float(direction@hessian@np.r_[shell_second.ravel(), beam_second])

    def work_mixed(first, second):
        updated = beam.context.advance(
            state, first*beam_direction+second*beam_second)
        trial = total+first*shell_direction+second*shell_second
        return float(dual@connection.evaluate(trial, updated)[0])

    mixed_errors = []
    for step in (.02, .01, .005):
        finite = (work_mixed(step, step)-work_mixed(step, -step)-
                  work_mixed(-step, step)+work_mixed(-step, -step))/(4*step*step)
        mixed_errors.append(abs(finite-mixed))
    assert mixed_errors[1] < .4*mixed_errors[0]
    assert mixed_errors[2] < .4*mixed_errors[1]
    assert mixed_errors[2] <= 2e-6*max(1., abs(mixed))

    # Only the two endpoint translations and one retained half-cell rotation
    # can carry B3 point work; the 18 resultants per element have zero columns.
    for element in range(len(beam.context.elements)):
        begin = 12+beam.context.nodal_count+24*element+6
        np.testing.assert_array_equal(residual[begin:begin+18], 0.)
        np.testing.assert_array_equal(hessian[begin:begin+18], 0.)


def test_log_work_objectivity_and_reference_ownership():
    beam, port, reference = _case()
    initial = beam.context.initial.mechanical
    connection = L1LogConnection.at_reference(reference, np.zeros((2, 6)),
                                               .035, port, initial)
    total = np.array(((.001, -.002, .0003, .12, -.08, .04),
                      (.002, .001, -.0004, .09, .05, -.02)))
    dual = np.array((2., -3., 5., 7., -11., 13.))
    original = connection.work_tangent(total, initial, dual)
    rigid_vector = np.array((.2, -.12, .08))
    rigid = rotation_matrix_from_vector(rigid_vector)
    shift = np.array((.3, -.2, .1))
    transformed_total = total.copy()
    for node in range(2):
        transformed_total[node, :3] = (
            rigid@(reference[node]+total[node, :3])+shift-reference[node])
        transformed_total[node, 3:] = Rotation.from_matrix(
            rigid@rotation_matrix_from_vector(total[node, 3:])).as_rotvec()
    step = np.zeros(beam.context.count)
    for node, position in enumerate(initial.positions):
        if node == 0:  # the fixed support is outside the sampled half-cell
            continue
        step[6*node:6*node+3] = rigid@position+shift-position
        step[6*node+3:6*node+6] = rigid_vector
    for element in range(len(beam.context.elements)):
        begin = beam.context.nodal_count+24*element
        step[begin:begin+6] = np.tile(rigid_vector, 2)
    transformed_state = beam.context.advance(initial, step)
    transformed = connection.work_tangent(transformed_total, transformed_state, dual)
    np.testing.assert_allclose(transformed[0], original[0], atol=4e-13)
    np.testing.assert_allclose(transformed[1], original[1], atol=4e-14)
    assert not connection.reference.flags.writeable
    reference[0, 0] = -4.
    np.testing.assert_allclose(connection.work_tangent(total, initial, dual)[0],
                               original[0], atol=1e-14)
    with pytest.raises(TypeError, match="retained native mechanical state"):
        connection.work_tangent(total, object(), dual)
