"""Six-channel native retained half-cell pose and chart derivatives."""

from dataclasses import replace

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from anysolver.boundary import BoundaryCondition
from anysolver.fe_core import FEModel
from anysolver._ge_beam3_centered_reference import CenteredCurvedBeam3ReferenceGeometry
from anysolver._ge_beam3_generalized_ellipsoid_section import EllipsoidalGeneralizedSection
from anysolver._ge_beam3_native_generalized_element import NativeGeneralizedStaticElement
from anysolver._ge_beam3_native_generalized_loading import DistributedPattern
from anysolver._ge_beam3_native_line_loading import LinePattern
from anysolver._ge_beam3_retained_generalized_state import Context, Program

from scripts._b3_e4_f03_native_fixture import SECTION_DIAGONAL, build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort


def _curved_context():
    model = FEModel("f03-curved-pre-rotated-station-port")
    coordinates, frames = [], []
    for node, x in enumerate((0., .5, 1.), 1):
        y = .08*x*(1-x)
        model.add_node(node, x, y, 0.)
        coordinates.append((x, y, 0.))
        tangent = np.array((1., .08*(1-2*x), 0.))
        tangent /= np.linalg.norm(tangent)
        transverse = np.array((-tangent[1], tangent[0], 0.))
        frame = np.column_stack((tangent, transverse, (0., 0., 1.)))
        frames.append(Rotation.from_rotvec(.12*x*tangent).as_matrix()@frame)
    reference = CenteredCurvedBeam3ReferenceGeometry(
        np.array(coordinates), np.array(frames))
    section = EllipsoidalGeneralizedSection(
        np.diag(SECTION_DIAGONAL), np.eye(6), 1e20, 1e9)
    native = NativeGeneralizedStaticElement(
        1, (1, 2, 3), reference, section, order=4)
    model.add_element(1, native)
    model.materials[native.material_name] = native.section
    model.add_boundary_condition(BoundaryCondition(
        "root", [1], {dof: 0. for dof in
                      ("ux", "uy", "uz", "rx", "ry", "rz")}))
    context = Context(model, Program(
        (1.,), DistributedPattern(LinePattern(()), ())))
    return context, reference


def test_straight_native_port_matches_existing_planar_trace():
    fixture = build(4)
    state = fixture.context.initial.mechanical
    for station in (0., .25, .32, .75, 1.):
        element, cell, weight, _ = fixture._locate(station)
        port = NativeHalfCellSpatialPort(
            fixture.context, element, cell, weight)
        position, frame = port.pose(state)
        old_position, old_frame = fixture.pose(station)
        np.testing.assert_allclose(position, old_position, rtol=0, atol=1e-14)
        np.testing.assert_allclose(frame, old_frame, rtol=0, atol=1e-14)
        np.testing.assert_allclose(
            port.tangent(state)[[0, 1, 5]],
            fixture.planar_trace_jacobian(station), rtol=0, atol=1e-14)


def test_curved_pre_rotated_port_first_second_and_work_variations():
    context, reference = _curved_context()
    original = context.initial.mechanical
    port = NativeHalfCellSpatialPort(context, 0, 0, .37)
    position, frame = port.pose(original)
    np.testing.assert_allclose(position, reference.position(-.63),
                               rtol=0, atol=2e-15)
    np.testing.assert_allclose(frame, reference.frame(-.63),
                               rtol=0, atol=2e-15)
    base = np.zeros(context.count)
    base[6:9] = (.002, -.003, .001)
    base[12:15] = (-.001, .002, .001)
    base[context.nodal_count:context.nodal_count+6] = (
        .04, -.03, .02, -.02, .01, .03)
    state = context.advance(original, base)
    first, second = np.zeros(context.count), np.zeros(context.count)
    first[6:12] = (.2, -.15, .07, .1, -.2, .15)
    first[12:15] = (-.12, .06, .08)
    first[context.nodal_count:context.nodal_count+6] = (
        .23, -.18, .13, .04, .01, -.02)
    second[6:9] = (.07, .04, -.06)
    second[context.nodal_count:context.nodal_count+6] = (
        -.14, .11, .09, .02, -.03, .01)
    h = 1e-5
    plus = port.pose(context.advance(state, h*first))
    minus = port.pose(context.advance(state, -h*first))
    numerical = np.r_[
        (plus[0]-minus[0])/(2*h),
        Rotation.from_matrix(plus[1]@minus[1].T).as_rotvec()/(2*h)]
    np.testing.assert_allclose(port.tangent(state)@first, numerical,
                               rtol=2e-7, atol=2e-9)
    wrench = np.array((18., -25., 31., 7., -9., 13.))
    assert abs(port.pullback(state, wrench)@first-wrench@numerical) < 2e-7
    lever = state.cell_rotations[0, 0]@reference.half_cell_lift(0, .37)
    cell_column = context.nodal_count
    np.testing.assert_allclose(
        port.pullback(state, wrench)[cell_column:cell_column+3],
        np.cross(lever, wrench[:3])+wrench[3:], rtol=0, atol=1e-13)
    pure_rotation = np.zeros(context.count)
    pure_rotation[cell_column:cell_column+3] = (.12, -.07, .04)
    h_rotation = 1e-5
    plus_position = port.pose(context.advance(state, h_rotation*pure_rotation))[0]
    minus_position = port.pose(context.advance(state, -h_rotation*pure_rotation))[0]
    force_work = wrench[:3]@(plus_position-minus_position)/(2*h_rotation)
    moment_work = wrench[3:]@pure_rotation[cell_column:cell_column+3]
    assert abs((force_work+moment_work)-
               port.pullback(state, wrench)@pure_rotation) < 2e-9

    h = 2e-3
    pp = port.pose(context.advance(state, h*(first+second)))
    pm = port.pose(context.advance(state, h*(first-second)))
    mp = port.pose(context.advance(state, h*(-first+second)))
    mm = port.pose(context.advance(state, -h*(first+second)))
    position_second, frame_second = port.second_variation(
        state, first, second)
    np.testing.assert_allclose(
        position_second, (pp[0]-pm[0]-mp[0]+mm[0])/(4*h*h),
        rtol=2e-5, atol=2e-8)
    np.testing.assert_allclose(
        frame_second, (pp[1]-pm[1]-mp[1]+mm[1])/(4*h*h),
        rtol=2e-5, atol=2e-8)
    numerical_force_curvature = wrench[:3]@(
        pp[0]-pm[0]-mp[0]+mm[0])/(4*h*h)
    assert abs(numerical_force_curvature-wrench[:3]@position_second) < 1e-6


def test_half_cell_boundary_has_explicit_two_sides():
    context, reference = _curved_context()
    original = context.initial.mechanical
    left = NativeHalfCellSpatialPort(context, 0, 0, 1.)
    right = NativeHalfCellSpatialPort(context, 0, 1, 0.)
    for a, b in zip(left.pose(original), right.pose(original)):
        np.testing.assert_allclose(a, b, rtol=0, atol=1e-14)
    np.testing.assert_allclose(left.pose(original)[1], reference.frame(0.),
                               rtol=0, atol=1e-14)
    assert not np.array_equal(left.tangent(original)[3:],
                              right.tangent(original)[3:])
    different_cells = np.zeros(context.count)
    different_cells[context.nodal_count:context.nodal_count+3] = (.13, -.06, .03)
    different_cells[context.nodal_count+3:context.nodal_count+6] = (
        -.04, .11, -.08)
    deformed = context.advance(original, different_cells)
    left_position, left_frame = left.pose(deformed)
    right_position, right_frame = right.pose(deformed)
    np.testing.assert_allclose(left_position, right_position,
                               rtol=0, atol=1e-14)
    assert np.linalg.norm(left_frame-right_frame) > .1
    assert not np.array_equal(left.tangent(deformed)[3:],
                              right.tangent(deformed)[3:])


def test_pose_pair_retains_subulp_native_translation_and_owns_arrays():
    context, _ = _curved_context()
    delta = np.zeros(context.count)
    delta[6] = 2.**-60
    state = context.advance(context.initial.mechanical, delta)
    port = NativeHalfCellSpatialPort(context, 0, 0, 1.)
    high, low, frame = port.pose_pair(state)
    assert high[0] == .5
    assert low[0] == delta[6]
    high[0], low[0], frame[0, 0] = 99., 99., 99.
    again = port.pose_pair(state)
    assert again[0][0] == .5 and again[1][0] == delta[6]
    assert again[2][0, 0] != 99.


def test_pose_pair_preserves_low_part_at_large_native_coordinate():
    context, _ = _curved_context()
    port = NativeHalfCellSpatialPort(context, 0, 0, 1.)
    large_step = np.zeros(context.count)
    large_step[6] = 1e16
    large = context.advance(context.initial.mechanical, large_step)
    small_step = np.zeros(context.count)
    small_step[6] = .25
    shifted = context.advance(large, small_step)
    high, low, _ = port.pose_pair(shifted)
    assert high[0] == shifted.positions[1, 0]
    assert low[0] == .75
    assert port.pose(shifted)[0][0] == high[0]


def test_interior_affine_station_preserves_large_origin_fraction():
    context, reference = _curved_context()
    original = context.initial.mechanical
    positions = original.positions.copy()
    positions[1, 0], positions[2, 0] = 1e16, 1e16+2.
    state = context.make(replace(original, positions=positions).descriptor())
    port = NativeHalfCellSpatialPort(context, 0, 1, .37)
    assert reference.half_cell_lift(1, .37)[0] == 0.
    high, low, _ = port.pose_pair(state)
    assert high[0] == 1e16
    assert low[0] == .74
    lows = state.position_low.copy()
    lows[2, 0] = .125
    shifted = context.make(replace(state, position_low=lows).descriptor())
    high, low, _ = port.pose_pair(shifted)
    assert high[0] == 1e16
    assert abs(low[0]-(.74+.37*.125)) < 1e-16


def test_port_rejects_malformed_trial_mechanics():
    context, _ = _curved_context()
    port = NativeHalfCellSpatialPort(context, 0, 0, .37)
    original = context.initial.mechanical
    bad_positions = original.positions.copy()
    bad_positions[1, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        port.pose(replace(original, positions=bad_positions))
    bad_rotation = original.cell_rotations.copy()
    bad_rotation[0, 0, 0, 0] = 2.
    with pytest.raises(ValueError, match="frame"):
        port.tangent(replace(original, cell_rotations=bad_rotation))
    with pytest.raises(ValueError, match="strict mechanical shape"):
        port.pose(replace(original, positions=original.positions[:2]))


@pytest.mark.parametrize("cell,weight", [(2, .5), (0, -1.), (1, 1.01)])
def test_invalid_half_cell_or_weight_rejected(cell, weight):
    context, _ = _curved_context()
    with pytest.raises(ValueError, match="valid native element"):
        NativeHalfCellSpatialPort(context, 0, cell, weight)
