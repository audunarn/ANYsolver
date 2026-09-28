"""Bounded L1 kinematics only; no formal F03 execution or acceptance."""

import numpy as np
import pytest

from anysolver.corotational import rotation_matrix_from_vector
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts.b3_e4_f03_l1_native_connection_probe import (
    shell_trace, six_gap, spatial_gap,
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


@pytest.mark.parametrize("angle", (np.pi/2, np.pi))
def test_local_angular_chart_rejects_singular_relative_rotations(angle):
    rotated = rotation_matrix_from_vector(np.array((angle, 0., 0.)))
    with pytest.raises(ValueError, match="outside the local probe chart"):
        spatial_gap(np.zeros(3), np.eye(3), np.zeros(3), rotated)
