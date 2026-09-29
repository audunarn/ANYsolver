"""Development checks for an unselected line-indexed finite shell patch."""

import numpy as np
import pytest

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts.b3_e4_f03_finite_patch_line_work import (
    FinitePatchLineFirstVariation,
)
from scripts.b3_e4_f03_finite_patch_pose import FlatQ4FiniteSupportPose
from scripts.b3_e4_f03_l1_physical_rail import transverse_shape_integrals
from scripts.b3_e4_f03_plate_patch_work import raw_e4_tangent


def _line():
    x = np.linspace(.5, 1., 5)
    y = np.array((-.1, 0., .1))
    reference = np.array([[(a, b, 0.) for b in y] for a in x])
    beam = build(8, z_offset=.0675, assemble=False)
    state = beam.context.initial.mechanical

    def port_at(station):
        element, cell, weight, _ = beam._locate(station)
        return NativeHalfCellSpatialPort(beam.context, element, cell, weight)

    line = FinitePatchLineFirstVariation.at_reference(
        reference, x, y, port_at, state,
        longitudinal_width=.1, transverse_bounds=(-.05, .05),
        thickness=.035)
    return line, reference, beam, state


def test_patch_line_reference_and_all_six_physical_wrench_channels():
    line, reference, beam, state = _line()
    zero = np.zeros(line.shell_shape)
    db = np.zeros(line.beam_size)
    assert line.segment_count == 4
    assert len(line.stations) == 8
    for channel in range(6):
        density = np.zeros((line.segment_count, 6))
        density[:, channel] = 1.
        gaps, idle = line.evaluate(zero, state, zero, db, density)
        np.testing.assert_allclose(gaps, 0., rtol=0., atol=2e-13)
        assert idle == pytest.approx(0., abs=2e-14)

        translation = np.array((.13, -.07, .11))
        shift = np.zeros_like(zero)
        shift[:, :, :3] = translation
        _, shifted_work = line.evaluate(zero, state, shift, db, density)
        assert shifted_work == pytest.approx(
            -.5*translation[channel] if channel < 3 else 0.,
            abs=3e-13)

        spin = np.array((.05, -.03, .09))
        rigid = np.zeros_like(zero)
        rigid[:, :, :3] = np.cross(spin, reference)
        rigid[:, :, 3:] = spin
        _, rotational_work = line.evaluate(zero, state, rigid, db, density)
        force = density[0, :3]
        couple = density[0, 3:]
        mean_rail = np.array((.75, 0., .0175))
        expected = -.5*spin@(np.cross(mean_rail, force)+couple)
        assert rotational_work == pytest.approx(expected, abs=3e-12)

    density = np.ones((line.segment_count, 6))
    translation = np.array((.03, -.02, .04))
    shell_step = np.zeros_like(zero)
    shell_step[:, :, :3] = translation
    beam_step = np.zeros(line.beam_size)
    for node in range(beam.context.nodal_count//6):
        beam_step[6*node:6*node+3] = translation
    _, common_work = line.evaluate(
        zero, state, shell_step, beam_step, density)
    assert common_work == pytest.approx(0., abs=3e-12)


def test_patch_line_rejects_a_rebased_native_reference():
    _, reference, beam, state = _line()
    x = reference[:, 0, 0]
    y = reference[0, :, 1]

    def port_at(station):
        element, cell, weight, _ = beam._locate(station)
        return NativeHalfCellSpatialPort(beam.context, element, cell, weight)

    same_pose_new_predecessor = beam.context.advance(
        state, np.zeros(beam.context.count))
    assert same_pose_new_predecessor is not state
    with pytest.raises(ValueError, match="virgin native state"):
        FinitePatchLineFirstVariation.at_reference(
            reference, x, y, port_at, same_pose_new_predecessor,
            longitudinal_width=.1, transverse_bounds=(-.05, .05),
            thickness=.035)


def test_line_integrated_patch_filters_the_known_endpoint_yaw_field():
    y = np.array((-.1, 0., .1))
    bounds = (-.05, .05)
    phi = np.array((1., -1., 1.))
    rail_work = float(transverse_shape_integrals(y, bounds)@phi)
    assert rail_work == pytest.approx(-.5, abs=2e-14)
    ratios = []
    patch_work = []
    for segments in (8, 16, 32, 64):
        cuts = np.linspace(.5, 1., segments+1)
        reference = np.array([[(x, value, 0.) for value in y]
                              for x in cuts])
        zero = np.zeros((len(cuts), len(y), 6))
        direction = np.zeros_like(zero)
        direction[-1, :, 1] = phi
        work = 0.
        gauss = (.5-.5/np.sqrt(3.), .5+.5/np.sqrt(3.))
        for left, right in zip(cuts[:-1], cuts[1:]):
            for alpha in gauss:
                station = left+(right-left)*alpha
                patch = FlatQ4FiniteSupportPose.at_reference(
                    reference, cuts, y, station=station, line_y=0.,
                    longitudinal_width=.1, transverse_bounds=bounds,
                    thickness=.035)
                _, frame, _, frame_step = patch.directional(zero, direction)
                spatial = frame_step@frame.T
                yaw = spatial[1, 0]
                work += .5*(right-left)*yaw
        full_x = np.r_[(0., .25), cuts]
        _, physical = raw_e4_tangent(full_x, y, thickness=.035)
        full = np.zeros(len(physical))
        for j, amplitude in enumerate(phi):
            full[6*(j*len(full_x)+len(full_x)-1)+1] = amplitude
        energy = float(full@physical@full)
        assert energy > 0.
        patch_work.append(abs(work))
        ratios.append(abs(work)/np.sqrt(energy))
    assert patch_work[0] > patch_work[1] > patch_work[2]
    assert patch_work[2] > patch_work[3]
    # At eight segments the fixed-width support is barely resolved. The
    # supported work/energy ratio enters its decreasing regime thereafter.
    assert ratios[1] > ratios[2] > ratios[3]
    assert ratios[3] < ratios[0]
