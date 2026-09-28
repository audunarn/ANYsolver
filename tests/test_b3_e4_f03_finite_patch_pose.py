"""Development checks for a finite-support line-indexed shell pose."""

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from scripts.b3_e4_f03_finite_patch_pose import FlatQ4FiniteSupportPose
from scripts.b3_e4_f03_plate_patch_work import raw_e4_tangent


def _patch(segments: int, *, station=1.):
    x = np.r_[(0., .25), np.linspace(.5, 1., segments+1)]
    y = np.array((-.1, 0., .1))
    reference = np.array([[(xi, yi, 0.) for yi in y] for xi in x])
    patch = FlatQ4FiniteSupportPose.at_reference(
        reference, x, y, station=station, line_y=0.,
        longitudinal_width=.2, transverse_bounds=(-.05, .05),
        thickness=.035)
    return patch, x, y


@pytest.mark.parametrize("station", (.5, .83, 1.))
def test_finite_patch_reference_and_rigid_motion_are_objective(station):
    patch, x, _ = _patch(8, station=station)
    q = np.zeros((*patch.reference.shape[:2], 6))
    point, frame = patch.pose(q)
    np.testing.assert_allclose(point, (station, 0., .0175),
                               rtol=0., atol=2e-14)
    np.testing.assert_allclose(frame, np.eye(3), rtol=0., atol=2e-14)
    assert patch.x_window[1]-patch.x_window[0] >= .1-1e-14
    assert patch.covariance > 0.
    np.testing.assert_allclose(patch.weights.sum(), 1., atol=2e-14)
    np.testing.assert_allclose(patch.moments.sum(), 0., atol=2e-14)

    turn = np.array((.24, -.17, .31))
    rotation = Rotation.from_rotvec(turn).as_matrix()
    shift = np.array((.4, -.2, .7))
    q[:, :, :3] = np.einsum(
        "ab,ijb->ija", rotation, patch.reference)+shift-patch.reference
    q[:, :, 3:] = turn
    moved, moved_frame = patch.pose(q)
    np.testing.assert_allclose(moved, rotation@point+shift,
                               rtol=0., atol=2e-13)
    np.testing.assert_allclose(moved_frame, rotation@frame,
                               rtol=0., atol=2e-13)

    x[-1] = 20.
    np.testing.assert_allclose(patch.pose(np.zeros_like(q))[0], point,
                               rtol=0., atol=2e-14)


def test_finite_patch_endpoint_yaw_filters_physical_core_witness():
    ratios = []
    energies = []
    for segments in (8, 16):
        patch, x, y = _patch(segments)
        q = np.zeros((*patch.reference.shape[:2], 6))
        q[-1, :, 1] = (1., -1., 1.)
        expected_yaw = float(np.dot(
            patch.moments[-1], (1., -1., 1.))/patch.covariance)
        step = 1e-6
        _, plus = patch.pose(step*q)
        _, minus = patch.pose(-step*q)
        measured_yaw = Rotation.from_matrix(
            minus.T@plus).as_rotvec()[2]/(2*step)
        assert measured_yaw == pytest.approx(
            expected_yaw, rel=2e-10, abs=2e-10)
        assert abs(measured_yaw) <= (.5/segments)/(8*patch.covariance)

        _, physical = raw_e4_tangent(x, y, thickness=.035)
        full = np.zeros(len(physical))
        for j in range(len(y)):
            full[6*(j*len(x)+len(x)-1)+1] = q[-1, j, 1]
        energy = float(full@physical@full)
        assert energy > 0.
        energies.append(energy)
        ratios.append(abs(measured_yaw)/np.sqrt(energy))
    assert energies[0]/energies[1] == pytest.approx(2., rel=2e-12)
    assert ratios[1] < ratios[0]
