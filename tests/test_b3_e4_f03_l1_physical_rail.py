"""Bounded mechanics checks for the unqualified physical-width shell rail."""

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from anysolver.corotational import rotation_matrix_from_vector
from anysolver.elements import create_shell_element
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts.b3_e4_f03_plate_patch_work import raw_e4_tangent
from scripts.b3_e4_f03_l1_physical_rail import (
    FlatQ4PhysicalRail, RailL1LogConnection, transverse_shape_integrals,
)


def _rail():
    y = np.array((-.1, 0., .1))
    reference = np.array([[(x, value, 0.) for value in y]
                          for x in (.9, 1.)])
    return FlatQ4PhysicalRail.from_reference(reference, y, (-.05, .05), .035)


def test_transverse_integral_is_width_owned_and_not_centerline_sampling():
    rail = _rail()
    np.testing.assert_allclose(rail.weights, (.125, .75, .125), atol=1e-15)
    assert not rail.weights.flags.writeable
    y = np.array((-.1, 0., .1))
    weights = transverse_shape_integrals(y, (-.025, .05))
    gauss, gauss_weights = np.polynomial.legendre.leggauss(3)
    independent = np.zeros(3)
    for lo, hi in ((-.025, 0.), (0., .05)):
        for point, weight in zip(gauss, gauss_weights):
            at = (lo+hi)/2.+point*(hi-lo)/2.
            if at < 0.:
                shape = ((-at)/.1, 1.+at/.1, 0.)
            else:
                shape = (0., 1.-at/.1, at/.1)
            independent += weight*(hi-lo)/2.*np.asarray(shape)/.075
    np.testing.assert_allclose(weights, independent, rtol=0., atol=1e-14)
    original = rail.reference.copy()
    with pytest.raises(ValueError, match="strip"):
        transverse_shape_integrals(y, (-.11, .05))
    np.testing.assert_array_equal(rail.reference, original)


def test_virgin_rail_variation_matches_owned_e4_q4_shape_field():
    """Check first-order compatibility, not a finite interior director claim."""
    rail = _rail()
    element = create_shell_element(
        1, [1, 2, 3, 4], "shell", formulation="e4-pl",
        thickness=rail.thickness, reference_normal=(0., 0., 1.))
    rng = np.random.default_rng(619)
    direction = rng.normal(scale=.2, size=(2, 3, 6))
    station = .29
    zero = np.zeros_like(direction)
    _, _, center_step, frame_step = rail.pose(
        zero, station=station, direction=direction)
    integrated_top = np.zeros(3)
    integrated_director = np.zeros(3)
    integrated_top_gradient = np.zeros(3)
    abscissae, gauss_weights = np.polynomial.legendre.leggauss(3)
    ez = np.array((0., 0., 1.))
    width = rail.bounds[1]-rail.bounds[0]
    for cell, (a, b) in enumerate(zip(rail.y_cuts[:-1], rail.y_cuts[1:])):
        lo, hi = max(a, rail.bounds[0]), min(b, rail.bounds[1])
        if hi <= lo:
            continue
        nodal = direction[[0, 1, 1, 0],
                          [cell, cell, cell+1, cell+1]]
        for point, weight in zip(abscissae, gauss_weights):
            y = .5*(lo+hi)+.5*(hi-lo)*point
            xi, eta = 2*station-1., 2*(y-a)/(b-a)-1.
            shape, dshape_xi, _ = element.compute_shape_functions(xi, eta)
            translation = shape@nodal[:, :3]
            rotation = shape@nodal[:, 3:]
            director = np.cross(rotation, ez)
            top_nodal = nodal[:, :3]+.5*rail.thickness*np.cross(
                nodal[:, 3:], ez)
            factor = .5*(hi-lo)*weight/width
            integrated_top += factor*(translation+.5*rail.thickness*director)
            integrated_director += factor*director
            integrated_top_gradient += factor*2/(rail.reference[1, 0, 0]-
                                                 rail.reference[0, 0, 0]) * (
                dshape_xi@top_nodal)
    np.testing.assert_allclose(center_step, integrated_top,
                               rtol=0., atol=2e-14)
    np.testing.assert_allclose(frame_step[:, 2], integrated_director,
                               rtol=0., atol=2e-14)
    ex = np.array((1., 0., 0.))
    tangent_step = integrated_top_gradient-ez*(
        ez@integrated_top_gradient+integrated_director@ex)
    tangent_step -= ex*(ex@tangent_step)
    side_step = (np.cross(integrated_director, ex)+
                 np.cross(ez, tangent_step))
    np.testing.assert_allclose(frame_step[:, 0], tangent_step,
                               rtol=0., atol=2e-14)
    np.testing.assert_allclose(frame_step[:, 1], side_step,
                               rtol=0., atol=2e-14)


def test_common_finite_rigid_motion_is_objective():
    rail = _rail()
    initial = np.zeros((2, 3, 6))
    c0, r0, _, _ = rail.pose(initial, station=.37)
    axis = np.array((.3, -.4, .5))
    axis /= np.linalg.norm(axis)
    angle = .42
    vector = axis*angle
    rotation = rotation_matrix_from_vector(vector)
    translation = np.array((.04, -.03, .07))
    total = initial.copy()
    total[:, :, :3] = (rail.reference@rotation.T+translation-
                       rail.reference)
    total[:, :, 3:] = vector
    center, frame, _, _ = rail.pose(total, station=.37)
    np.testing.assert_allclose(center, rotation@c0+translation,
                               rtol=0., atol=3e-14)
    np.testing.assert_allclose(frame, rotation@r0, rtol=0., atol=3e-14)

    deformed = np.random.default_rng(81).normal(scale=.004, size=(2, 3, 6))
    old_center, old_frame, _, _ = rail.pose(deformed, station=.37)
    transformed = deformed.copy()
    transformed[:, :, :3] = (
        (rail.reference+deformed[:, :, :3])@rotation.T + translation -
        rail.reference)
    for i in range(2):
        for j in range(3):
            local = rotation_matrix_from_vector(deformed[i, j, 3:])
            transformed[i, j, 3:] = Rotation.from_matrix(
                rotation@local).as_rotvec()
    new_center, new_frame, _, _ = rail.pose(transformed, station=.37)
    np.testing.assert_allclose(new_center, rotation@old_center+translation,
                               rtol=0., atol=3e-14)
    np.testing.assert_allclose(new_frame, rotation@old_frame,
                               rtol=0., atol=3e-14)


def test_finite_pose_matches_independent_width_quadrature():
    rail = _rail()
    random = np.random.default_rng(109)
    total = random.normal(scale=.015, size=(2, 3, 6))
    station = .31
    center, frame, _, _ = rail.pose(total, station=station)
    nodal_director = np.array([
        [rotation_matrix_from_vector(total[i, j, 3:])[:, 2]
         for j in range(3)] for i in range(2)])
    nodal_top = rail.reference+total[:, :, :3]+.5*rail.thickness*nodal_director
    average_top, average_director = np.zeros((2, 3)), np.zeros((2, 3))
    gauss, quadrature = np.polynomial.legendre.leggauss(4)
    for cell, (lo, hi) in enumerate(((-.05, 0.), (0., .05))):
        for point, weight in zip(gauss, quadrature):
            y = (lo+hi)/2.+point*(hi-lo)/2.
            local = (y-rail.y_cuts[cell])/(rail.y_cuts[cell+1]-rail.y_cuts[cell])
            shape = np.array((1.-local, local))
            average_top += (weight*(hi-lo)/2./.1 *
                            np.einsum("j,ijk->ik", shape,
                                      nodal_top[:, cell:cell+2]))
            average_director += (weight*(hi-lo)/2./.1 *
                                 np.einsum("j,ijk->ik", shape,
                                           nodal_director[:, cell:cell+2]))
    expected_center = ((1.-station)*average_top[0]+station*average_top[1])
    normal = ((1.-station)*average_director[0]+
              station*average_director[1])
    normal /= np.linalg.norm(normal)
    raw = average_top[1]-average_top[0]
    tangent = raw-normal*(normal@raw)
    tangent /= np.linalg.norm(tangent)
    expected_frame = np.column_stack((tangent, np.cross(normal, tangent), normal))
    np.testing.assert_allclose(center, expected_center, rtol=0., atol=2e-14)
    np.testing.assert_allclose(frame, expected_frame, rtol=0., atol=2e-14)


def test_actual_chart_derivative_and_shear_drill_freedom():
    rail = _rail()
    random = np.random.default_rng(919)
    total = random.normal(scale=.003, size=(2, 3, 6))
    direction = random.normal(scale=.06, size=(2, 3, 6))
    center, frame, dc, dr = rail.pose(total, station=.29,
                                       direction=direction)
    h = 1e-6
    plus_c, plus_r, _, _ = rail.pose(total+h*direction, station=.29)
    minus_c, minus_r, _, _ = rail.pose(total-h*direction, station=.29)
    np.testing.assert_allclose(dc, (plus_c-minus_c)/(2*h),
                               rtol=2e-7, atol=2e-9)
    np.testing.assert_allclose(dr, (plus_r-minus_r)/(2*h),
                               rtol=2e-7, atol=2e-9)
    np.testing.assert_allclose(frame.T@frame, np.eye(3), atol=2e-14)

    zero = np.zeros_like(total)
    drill = zero.copy()
    drill[:, :, 5] = 1.
    _, _, drill_center, drill_frame = rail.pose(zero, direction=drill)
    np.testing.assert_allclose(drill_center, 0., atol=1e-15)
    np.testing.assert_allclose(drill_frame, 0., atol=1e-15)
    shear = zero.copy()
    shear[1, :, 2] = .1
    _, _, _, shear_frame = rail.pose(zero, direction=shear)
    np.testing.assert_allclose(shear_frame, 0., atol=1e-14)
    assert np.linalg.norm(rail.pose(zero, direction=shear)[2]) > 0.


def test_yaw_work_uses_width_average_and_director_rotation_port():
    rail = _rail()
    zero = np.zeros((2, 3, 6))
    lateral = zero.copy()
    lateral[1, :, 1] = (0., 1., 0.)
    yaw = rail.spin(zero, lateral)[2]
    assert yaw == pytest.approx(.75/.1, abs=1e-13)
    roll = zero.copy()
    roll[:, :, 3] = 1.
    assert rail.spin(zero, roll)[0] == pytest.approx(1., abs=1e-13)


def test_native_six_channel_reference_and_actual_update_derivative():
    rail = _rail()
    beam = build(4, z_offset=.0675, assemble=False)
    element, cell, weight, _ = beam._locate(.95)
    port = NativeHalfCellSpatialPort(beam.context, element, cell, weight)
    state = beam.context.initial.mechanical
    zero = np.zeros((2, 3, 6))
    connection = RailL1LogConnection.at_reference(rail, zero, port, state)
    np.testing.assert_allclose(connection.evaluate(zero, state)[0],
                               0., atol=3e-15)
    wrong_element, wrong_cell, wrong_weight, _ = beam._locate(.925)
    wrong_port = NativeHalfCellSpatialPort(
        beam.context, wrong_element, wrong_cell, wrong_weight)
    with pytest.raises(ValueError, match="reference station/offset"):
        RailL1LogConnection.at_reference(rail, zero, wrong_port, state)
    nonvirgin_shell = zero.copy()
    nonvirgin_shell[1, 1, 1] = 1e-3
    with pytest.raises(ValueError, match="virgin"):
        RailL1LogConnection.at_reference(
            rail, nonvirgin_shell, port, state)
    changed = np.zeros(beam.context.count)
    changed[6] = 1e-4
    with pytest.raises(ValueError, match="virgin"):
        RailL1LogConnection.at_reference(
            rail, zero, port,
            beam.context.advance(state, changed))
    eccentric = RailL1LogConnection.at_reference(
        rail, zero, port, state, beam_offset=(0., 0., -.04),
        expected_reference_offset_shell=(0., 0., .01))
    np.testing.assert_allclose(eccentric.evaluate(zero, state)[0],
                               0., atol=3e-15)

    columns = []
    beam_zero = np.zeros(beam.context.count)
    for axis in range(3):
        direction = zero.copy()
        direction[:, :, axis] = 1.
        columns.append(connection.evaluate(
            zero, state, shell_direction=direction,
            beam_direction=beam_zero)[1])
    for axis in (3, 4):
        direction = zero.copy()
        direction[:, :, axis] = 1.
        columns.append(connection.evaluate(
            zero, state, shell_direction=direction,
            beam_direction=beam_zero)[1])
    lateral = zero.copy()
    lateral[1, 1, 1] = .1
    columns.append(connection.evaluate(
        zero, state, shell_direction=lateral,
        beam_direction=beam_zero)[1])
    assert np.linalg.matrix_rank(np.column_stack(columns), tol=1e-10) == 6

    rng = np.random.default_rng(127)
    total = rng.normal(scale=.002, size=(2, 3, 6))
    shell_direction = rng.normal(scale=.01, size=(2, 3, 6))
    beam_direction = rng.normal(scale=1e-3, size=beam.context.count)
    beam_direction[:6] = 0.
    native_increment = rng.normal(scale=1e-4, size=beam.context.count)
    native_increment[:6] = 0.
    moved = beam.context.advance(state, native_increment)
    gap, derivative = connection.evaluate(
        total, moved, shell_direction=shell_direction,
        beam_direction=beam_direction)
    assert np.linalg.norm(gap) > 0.
    h = 1e-5
    plus = connection.evaluate(
        total+h*shell_direction,
        beam.context.advance(moved, h*beam_direction))[0]
    minus = connection.evaluate(
        total-h*shell_direction,
        beam.context.advance(moved, -h*beam_direction))[0]
    np.testing.assert_allclose(derivative, (plus-minus)/(2*h),
                               rtol=3e-7, atol=3e-9)


def test_roll_and_yaw_ports_have_physical_shell_energy_without_drilling():
    xs = np.array((0., .45, .9, 1.))
    ys = np.array((-.1, 0., .1))
    _, physical = raw_e4_tangent(xs, ys, thickness=.035)
    count = physical.shape[0]
    roll, yaw, drill = (np.zeros(count) for _ in range(3))
    for j in range(len(ys)):
        for i in (2, 3):
            roll[6*(j*len(xs)+i)+3] = 1.
            drill[6*(j*len(xs)+i)+5] = 1.
    yaw[6*(1*len(xs)+3)+1] = 1.
    assert float(roll@physical@roll) > 0.
    assert float(yaw@physical@yaw) > 0.
    assert abs(float(drill@physical@drill)) < 1e-8*float(roll@physical@roll)


def test_normal_moment_virtual_work_is_width_distributed():
    rail = _rail()
    beam = build(4, z_offset=.0675, assemble=False)
    element, cell, weight, _ = beam._locate(.95)
    port = NativeHalfCellSpatialPort(beam.context, element, cell, weight)
    state = beam.context.initial.mechanical
    zero = np.zeros((2, 3, 6))
    connection = RailL1LogConnection.at_reference(rail, zero, port, state)
    beam_zero = np.zeros(beam.context.count)
    shell_y_forces = np.zeros((2, 3))
    for i in range(2):
        for j in range(3):
            direction = zero.copy()
            direction[i, j, 1] = 1.
            shell_y_forces[i, j] = connection.evaluate(
                zero, state, shell_direction=direction,
                beam_direction=beam_zero)[1][5]
    np.testing.assert_allclose(shell_y_forces.sum(axis=1),
                               (10., -10.), atol=2e-13)
    np.testing.assert_allclose(shell_y_forces.sum(axis=0), 0., atol=2e-13)
    np.testing.assert_allclose(shell_y_forces[0]/10., rail.weights,
                               atol=2e-14)
    x = rail.reference[:, :, 0]
    assert np.sum(x*shell_y_forces) == pytest.approx(-1., abs=2e-14)
    beam_spin = np.zeros(beam.context.count)
    column = beam.context.nodal_count+24*element+3*cell+2
    beam_spin[column] = 1.
    assert connection.evaluate(
        zero, state, shell_direction=zero,
        beam_direction=beam_spin)[1][5] == pytest.approx(1., abs=2e-13)


@pytest.mark.parametrize("shell_scale,native_scale",
                         ((.001, 2e-4), (.06, .01)))
def test_multiplier_work_gradient_and_curvature_follow_actual_updates(
        shell_scale, native_scale):
    rail = _rail()
    beam = build(4, z_offset=.0675, assemble=False)
    element, cell, weight, _ = beam._locate(.95)
    port = NativeHalfCellSpatialPort(beam.context, element, cell, weight)
    state = beam.context.initial.mechanical
    zero = np.zeros((2, 3, 6))
    connection = RailL1LogConnection.at_reference(rail, zero, port, state)
    rng = np.random.default_rng(510)
    total = rng.normal(scale=shell_scale, size=zero.shape)
    native_step = rng.normal(scale=native_scale, size=beam.context.count)
    native_step[:6] = 0.
    moved = beam.context.advance(state, native_step)
    shell_direction = rng.normal(scale=.02, size=zero.shape)
    beam_direction = rng.normal(scale=.002, size=beam.context.count)
    beam_direction[:6] = 0.
    multiplier = np.array((1.1, -.8, .7, .4, -.3, .6))

    work, gap, gradient, hessian = connection.work_tangent(
        total, moved, multiplier)
    expected_gap, derivative = connection.evaluate(
        total, moved, shell_direction=shell_direction,
        beam_direction=beam_direction)
    direction = np.r_[shell_direction.ravel(), beam_direction]
    np.testing.assert_allclose(gap, expected_gap, rtol=0., atol=2e-12)
    assert work == pytest.approx(multiplier@gap, rel=2e-12, abs=2e-12)
    np.testing.assert_allclose(gradient@direction, multiplier@derivative,
                               rtol=3e-9, atol=3e-11)
    np.testing.assert_allclose(hessian, hessian.T, rtol=0., atol=2e-10)
    assert not np.any(gradient[total.size+beam.context.nodal_count:
                               total.size+beam.context.nodal_count+
                               24*element])

    for step_size in (2e-4, 1e-4):
        plus = connection.evaluate(
            total+step_size*shell_direction,
            beam.context.advance(moved, step_size*beam_direction))[0]
        minus = connection.evaluate(
            total-step_size*shell_direction,
            beam.context.advance(moved, -step_size*beam_direction))[0]
        curvature_fd = multiplier@(plus-2*gap+minus)/step_size**2
        np.testing.assert_allclose(direction@hessian@direction,
                                   curvature_fd, rtol=2e-4, atol=2e-5)

    step_size = 1e-4
    mixed = np.empty((2, 2))
    for i, shell_sign in enumerate((-1., 1.)):
        for j, beam_sign in enumerate((-1., 1.)):
            candidate = beam.context.advance(
                moved, beam_sign*step_size*beam_direction)
            mixed[i, j] = multiplier@connection.evaluate(
                total+shell_sign*step_size*shell_direction, candidate)[0]
    cross_fd = (mixed[1, 1]-mixed[1, 0]-mixed[0, 1]+mixed[0, 0]) / (
        4*step_size**2)
    cross_exact = (shell_direction.ravel()@hessian[:total.size, total.size:]@
                   beam_direction)
    np.testing.assert_allclose(cross_exact, cross_fd,
                               rtol=2e-4, atol=2e-5)
