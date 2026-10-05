"""Native retained-coordinate round-surface work without condensation."""

import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from anysolver._ge_beam3_centered_reference import (
    CenteredCurvedBeam3ReferenceGeometry,
)
from anysolver._ge_beam3_fibre_line_work import evaluate as native_line_work
from anysolver.general_contact.native_retained_station import (
    NativeRetainedRoundStation,
)


def _reference(curved: bool):
    coordinates = np.array(((-1.0, 0.0, 0.0),
                            (0.0, 0.2 if curved else 0.0, 0.0),
                            (1.0, 0.0, 0.0)))
    frames = []
    for slope in ((0.4, 0.0, -0.4) if curved else (0.0, 0.0, 0.0)):
        tangent = np.array((1.0, slope, 0.0))
        tangent /= np.linalg.norm(tangent)
        normal = np.array((-tangent[1], tangent[0], 0.0))
        frames.append(np.column_stack((tangent, normal, (0.0, 0.0, 1.0))))
    return CenteredCurvedBeam3ReferenceGeometry(coordinates, np.array(frames))


@pytest.mark.parametrize("curved", (False, True))
def test_native_round_station_virgin_geometry_and_internal_motion(curved):
    reference = _reference(curved)
    station = NativeRetainedRoundStation(7, reference, -0.5, 0.03, 0.4)
    high = reference.coordinates
    low = np.zeros((3, 3))
    rotations = np.tile(np.eye(3), (2, 1, 1))
    state = station.evaluate(high, low, rotations)
    radial = 0.03*(np.cos(0.4)*reference.frame(-0.5)[:, 1]
                   + np.sin(0.4)*reference.frame(-0.5)[:, 2])
    np.testing.assert_allclose(state.centerline_position,
                               reference.position(-0.5), atol=2e-15)
    np.testing.assert_allclose(state.surface_position,
                               reference.position(-0.5)+radial, atol=2e-15)
    moved = rotations.copy()
    moved[0] = Rotation.from_rotvec((0.1, -0.05, 0.02)).as_matrix()
    changed = station.evaluate(high, low, moved)
    assert np.linalg.norm(changed.surface_position-state.surface_position) > 1e-4
    if curved:
        assert np.linalg.norm(changed.centerline_position-state.centerline_position) > 1e-4
    else:
        np.testing.assert_allclose(changed.centerline_position,
                                   state.centerline_position, atol=2e-15)
    assert np.linalg.norm(state.surface_geometric_jacobian[:, 18:21]) > 0.0
    for node in range(3):
        np.testing.assert_array_equal(
            state.surface_geometric_jacobian[:, 6*node+3:6*node+6], 0.0,
        )
    np.testing.assert_array_equal(state.surface_geometric_jacobian[:, 21:24], 0.0)
    np.testing.assert_array_equal(state.generalized_surface_jacobian()[:, 24:], 0.0)


def test_native_round_station_virtual_work_and_rigid_covariance():
    reference = _reference(True)
    station = NativeRetainedRoundStation(9, reference, 0.37, 0.04, 1.2)
    high = reference.coordinates.copy()
    high[1] += (0.01, -0.02, 0.005)
    low = np.zeros((3, 3))
    rotations = np.stack((Rotation.from_rotvec((0.02, 0.01, -0.03)).as_matrix(),
                          Rotation.from_rotvec((-0.04, 0.02, 0.01)).as_matrix()))
    state = station.evaluate(high, low, rotations)
    direction = np.zeros(24)
    direction[0:3] = (0.3, -0.2, 0.1)
    direction[6:9] = (-0.1, 0.15, 0.05)
    direction[12:15] = (0.2, 0.1, -0.1)
    direction[21:24] = (0.25, -0.3, 0.2)
    step = 1e-6

    def moved(sign):
        positions = high.copy()
        for node in range(3):
            positions[node] += sign*step*direction[6*node:6*node+3]
        cells = rotations.copy()
        cells[1] = (Rotation.from_rotvec(sign*step*direction[21:24]).as_matrix()
                    @ cells[1])
        return station.evaluate(positions, low, cells).surface_position

    numerical = (moved(1)-moved(-1))/(2*step)
    np.testing.assert_allclose(state.surface_geometric_jacobian @ direction,
                               numerical, rtol=2e-8, atol=1e-9)
    physical_force = np.array((0.3, -0.4, 0.7))
    work = state.generalized_surface_work(physical_force)
    np.testing.assert_allclose(work[:24] @ direction,
                               physical_force @ numerical, rtol=2e-8, atol=1e-9)
    np.testing.assert_array_equal(work[24:], 0.0)

    rigid = Rotation.from_rotvec((0.3, -0.1, 0.2)).as_matrix()
    translation = np.array((1.3, -0.7, 0.4))
    transformed = station.evaluate(high@rigid.T+translation, low,
                                   rigid@rotations)
    np.testing.assert_allclose(transformed.surface_position,
                               rigid@state.surface_position+translation,
                               atol=2e-14)


def test_native_round_station_centerline_work_matches_retained_line_map():
    reference = _reference(True)
    high = reference.coordinates.copy()
    high[1] += (0.01, 0.005, -0.003)
    low = np.zeros((3, 3))
    rotations = np.stack((Rotation.from_rotvec((0.01, 0.02, -0.01)).as_matrix(),
                          Rotation.from_rotvec((-0.03, 0.01, 0.02)).as_matrix()))
    force = np.array((0.2, -0.3, 0.4))
    native = native_line_work(reference, high, low, rotations, force, order=4)
    points, weights = np.polynomial.legendre.leggauss(4)
    assembled = np.zeros(24)
    for cell in (0, 1):
        for point, weight in zip(points, weights):
            t = float((point+1.0)/2.0)
            xi = cell-1+t
            station = NativeRetainedRoundStation(5, reference, xi, 0.02, 0.0)
            state = station.evaluate(high, low, rotations)
            measure = float(weight*reference.jacobian(xi)/2.0)
            assembled += measure*state.centerline_geometric_jacobian.T @ force
    np.testing.assert_allclose(assembled, native.gradient[:24],
                               rtol=0.0, atol=2e-13)
    np.testing.assert_array_equal(native.gradient[24:], 0.0)


def test_native_round_station_rejects_ambiguous_or_invalid_geometry():
    reference = _reference(False)
    for xi in (-1.0, 0.0, 1.0):
        with pytest.raises(ValueError, match="interior"):
            NativeRetainedRoundStation(1, reference, xi, 0.02, 0.0)
    with pytest.raises(ValueError, match="positive radius"):
        NativeRetainedRoundStation(1, reference, -0.5, 0.0, 0.0)
    with pytest.raises(ValueError, match="angle"):
        NativeRetainedRoundStation(1, reference, -0.5, 0.02, 2*np.pi)
    station = NativeRetainedRoundStation(1, reference, -0.5, 0.02, 0.0)
    invalid = np.tile(np.eye(3), (2, 1, 1))
    invalid[0, 0, 0] = -1.0
    with pytest.raises(ValueError, match="proper rotations"):
        station.evaluate(reference.coordinates, np.zeros((3, 3)), invalid)
