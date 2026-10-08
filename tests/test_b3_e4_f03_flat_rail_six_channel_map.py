"""Independent flat-reference checks for the unqualified six-row shell rail."""

import numpy as np

from scripts.b3_e4_f03_flat_rail_six_channel_map import (
    flat_rail_p0_shell_pose_action,
)
from scripts.b3_e4_f03_l1_physical_rail import FlatQ4PhysicalRail
from scripts.b3_e4_f03_l1_physical_rail import SegmentedRailWeakWork
from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts.b3_e4_f03_plate_patch_work import raw_e4_tangent


def _fixture():
    return (np.linspace(.5, 1., 5), np.array((-.1, 0., .1)),
            (-.047, .046), .035)


def test_six_channel_rows_match_actual_pose_derivatives_at_gauss_stations():
    xs, ys, bounds, thickness = _fixture()
    action = flat_rail_p0_shell_pose_action(xs, ys, bounds, thickness)
    rng = np.random.default_rng(2249)
    q = rng.normal(scale=.02, size=(len(ys), len(xs), 6))
    expected = []
    gauss = (.5-.5/np.sqrt(3.), .5+.5/np.sqrt(3.))
    for i, h in enumerate(np.diff(xs)):
        reference = np.array([[(x, y, 0.) for y in ys]
                              for x in xs[i:i+2]])
        rail = FlatQ4PhysicalRail.from_reference(
            reference, ys, bounds, thickness)
        direction = q[:, i:i+2, :].transpose(1, 0, 2)
        integrated = np.zeros(6)
        for station in gauss:
            _, frame, center_step, frame_step = rail.pose(
                np.zeros_like(direction), station=station,
                direction=direction)
            skew = frame_step@frame.T
            spin = np.array((skew[2, 1], skew[0, 2], skew[1, 0]))
            integrated += .5*h*np.r_[center_step, spin]
        expected.append(integrated)
    np.testing.assert_allclose(action@q.ravel(), expected,
                               rtol=0., atol=2e-14)
    np.testing.assert_array_equal(action[:, :, 5::6], 0.)
    assert not action.flags.writeable


def test_six_channel_common_rigid_motion_and_admissible_shear():
    xs, ys, bounds, thickness = _fixture()
    action = flat_rail_p0_shell_pose_action(xs, ys, bounds, thickness)
    omega = np.array((.02, -.03, .04))
    q = np.zeros((len(ys), len(xs), 6))
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            q[j, i, :3] = np.cross(omega, (x, y, 0.))
            q[j, i, 3:] = omega
    spin_and_motion = action@q.ravel()
    reference_y = np.dot(
        FlatQ4PhysicalRail.from_reference(
            np.array([[(x, y, 0.) for y in ys]
                      for x in xs[:2]]), ys, bounds, thickness).weights, ys)
    for i, h in enumerate(np.diff(xs)):
        top_midpoint = np.array(((xs[i]+xs[i+1])/2., reference_y,
                                 thickness/2.))
        np.testing.assert_allclose(spin_and_motion[i, :3],
                                   h*np.cross(omega, top_midpoint),
                                   rtol=0., atol=2e-15)
        np.testing.assert_allclose(spin_and_motion[i, 3:], h*omega,
                                   rtol=0., atol=2e-15)

    shear = np.zeros_like(q)
    shear[:, :, 2] = xs[None, :]
    response = action@shear.ravel()
    np.testing.assert_allclose(response[:, 4:], 0., rtol=0., atol=2e-15)
    np.testing.assert_allclose(response[:, 2],
                               np.diff(xs)*(xs[:-1]+xs[1:])/2.,
                               rtol=0., atol=2e-15)


def test_six_channel_shell_rows_match_native_relative_gap_at_reference():
    """Keep the six shell rows tied to the actual native pose-joint contract."""
    xs, ys, _, thickness = _fixture()
    bounds = (-.05, .05)  # Centred strip: the native axis projects to y=0.
    action = flat_rail_p0_shell_pose_action(xs, ys, bounds, thickness)
    reference = np.array([[(x, y, 0.) for y in ys] for x in xs])
    beam = build(4, z_offset=.0675, assemble=False)
    state = beam.context.initial.mechanical

    def port_at(station):
        element, cell, weight, _ = beam._locate(station)
        return NativeHalfCellSpatialPort(beam.context, element, cell, weight)

    line = SegmentedRailWeakWork.at_reference(
        reference, ys, bounds, thickness, port_at, state,
        beam_offset=(0., 0., -.05),
        expected_reference_offset_shell=(0., 0., 0.))
    rng = np.random.default_rng(2250)
    q = rng.normal(scale=.01, size=(len(ys), len(xs), 6))
    native_zero = np.zeros(beam.context.count)
    integrated = np.zeros((len(xs)-1, 6))
    for sample, connection in enumerate(line.connections):
        segment = sample//2
        local = q[:, segment:segment+2, :].transpose(1, 0, 2)
        gap, direction = connection.evaluate(
            np.zeros_like(local), state, shell_direction=local,
            beam_direction=native_zero)
        np.testing.assert_allclose(gap, 0., rtol=0., atol=2e-14)
        integrated[segment] += line.weights[sample]*direction
    np.testing.assert_allclose(integrated, -action@q.ravel(),
                               rtol=0., atol=3e-13)

    native_direction = np.zeros(beam.context.count)
    native_direction[beam.context.nodal_count:] = rng.normal(
        scale=.01, size=beam.context.count-beam.context.nodal_count)
    native_integrated = np.zeros_like(integrated)
    combined = np.zeros_like(integrated)
    for sample, connection in enumerate(line.connections):
        segment = sample//2
        local = q[:, segment:segment+2, :].transpose(1, 0, 2)
        _, derivative = connection.evaluate(
            np.zeros_like(local), state, shell_direction=local,
            beam_direction=native_direction)
        spatial = connection.port.tangent(state)@native_direction
        _, _, beam_frame = connection.port.pose_pair(state)
        arm = beam_frame@np.array((0., 0., -.05))
        native_pose = np.r_[spatial[:3]+np.cross(spatial[3:], arm),
                            spatial[3:]]
        weight = line.weights[sample]
        combined[segment] += weight*derivative
        native_integrated[segment] += weight*native_pose
    assert np.linalg.norm(native_integrated) > 0.
    np.testing.assert_allclose(combined,
                               -action@q.ravel()+native_integrated,
                               rtol=0., atol=3e-13)


def test_current_rail_admits_supported_even_transverse_slip():
    """Classify this rail's continuous law, not only the older C1 hybrid."""
    xs = np.linspace(.5, 1., 5)
    ys = np.array((-.1, -.05, 0., .05, .1))
    bounds = (-.05, .05)
    thickness = .035
    reference = np.array([[(x, y, 0.) for y in ys] for x in xs])
    beam = build(4, z_offset=.0675, assemble=False)
    state = beam.context.initial.mechanical

    def port_at(station):
        element, cell, weight, _ = beam._locate(station)
        return NativeHalfCellSpatialPort(beam.context, element, cell, weight)

    line = SegmentedRailWeakWork.at_reference(
        reference, ys, bounds, thickness, port_at, state,
        beam_offset=(0., 0., -.05),
        expected_reference_offset_shell=(0., 0., 0.))
    shell = np.zeros((len(ys), len(xs), 6))
    even = np.array((0., 1., -1., 1., 0.))
    longitudinal = np.array((0., 0., 0., .5, 1.))
    shell[:, :, 2] = 1e-5*even[:, None]*longitudinal[None, :]
    np.testing.assert_allclose(line.connections[0].rail.weights@even,
                               0., rtol=0., atol=1e-15)
    assert shell[2, -1, 2] == -1e-5  # Local shell-top/beam-surface slip.
    assert not np.any(shell[:, 0, :])  # The supported end remains fixed.

    gaps = []
    for sample, connection in enumerate(line.connections):
        segment = sample//2
        local = shell[:, segment:segment+2, :].transpose(1, 0, 2)
        gap, _ = connection.evaluate(local, state)
        gaps.append(gap)
    gaps = np.asarray(gaps)
    np.testing.assert_allclose(gaps, 0., rtol=0., atol=2e-14)
    for kind in ("piecewise_constant", "continuous_linear", "dual_linear"):
        for intervals in (2, 4, 8):
            space = LineMultiplierSpace(
                kind, tuple(np.linspace(0., 1., intervals+1)))
            projected = np.zeros((space.count, 6))
            for x, weight, gap in zip(line.stations, line.weights, gaps):
                projected += weight*space.values(2.*(x-.5))[:, None]*gap
            np.testing.assert_allclose(projected, 0., rtol=0., atol=2e-14)

    _, physical = raw_e4_tangent(xs, ys, thickness=thickness)
    energy = .5*shell.ravel()@physical@shell.ravel()
    assert np.isfinite(energy) and energy > 0.
