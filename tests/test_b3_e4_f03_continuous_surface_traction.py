"""Physical wrench and objective-work checks for the bounded traction screen."""

import numpy as np
import pytest

from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_continuous_surface_traction import (
    _common_rigid_direction, continuous_traction_rows,
)
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def test_continuous_traction_spans_six_wrenches_without_drilling():
    xs = np.linspace(-.5, 1.5, 9)
    ys = np.linspace(-.5, .5, 9)
    beam = build(8, z_offset=.0675,
                 torsion_constant=square_torsion_constant())
    rows, wrench, meta = continuous_traction_rows(xs, ys, beam, intervals=2)
    shell_size = 6 * len(xs) * len(ys)
    assert meta["bond_area_m2"] == pytest.approx(.1, abs=1e-12)
    assert meta["reference_gap_m"] < 1e-11
    assert rows.shape == (12, shell_size + beam.context.count)
    assert np.max(np.abs(rows[:, 5:shell_size:6])) == 0.
    assert np.linalg.matrix_rank(wrench) == 6
    for station in range(3):
        assert wrench[:, 4 * station + 3] == pytest.approx(
            [0., 0., 0., 1., 0., 0.], abs=1e-12)
    direction = _common_rigid_direction(
        xs, ys, beam, np.array((.02, -.03, .04)),
        np.array((.003, -.005, .007)))
    assert np.max(np.abs(rows @ direction)) < 1e-11


def test_section_traction_has_only_four_independent_local_wrenches():
    """Six integrated resultants do not imply six poses at every section.

    This uses the physical 100 mm strip at the B3 bottom surface, 50 mm
    below its centroid, and independently integrates the four force profiles
    used by the candidate. Moment is taken about that section centroid.
    """
    points, weights = np.polynomial.legendre.leggauss(3)
    section = np.zeros((6, 4))
    for point, weight in zip(points, weights):
        y = .05 * point
        traction = np.array(((1., 0., 0.), (0., 1., 0.),
                             (0., 0., 1.), (0., 0., y)))
        lever = np.array((0., y, -.05))
        section[:3] += .05 * weight * traction.T
        section[3:] += .05 * weight * np.cross(lever, traction).T
    scales = np.array((.1, .1, .1, .005, .005, .005))
    assert np.linalg.matrix_rank(section / scales[:, None]) == 4
    assert section[4] == pytest.approx(-.05 * section[0], abs=1e-15)
    assert section[5] == pytest.approx(np.zeros(4), abs=1e-15)

    yaw = np.zeros(6)
    for point, weight in zip(points, weights):
        y = .05 * point
        force = np.array((-y, 0., 0.))
        yaw[:3] += .05 * weight * force
        yaw[3:] += .05 * weight * np.cross((0., y, -.05), force)
    five = np.column_stack((section, yaw))
    assert np.linalg.matrix_rank(five / scales[:, None]) == 5
    assert yaw[:5] == pytest.approx(np.zeros(5), abs=1e-15)
    assert yaw[5] == pytest.approx(.1**3 / 12, abs=1e-15)


def test_local_yaw_dipole_adds_physical_mz_without_changing_four_rows():
    xs = np.linspace(-.5, 1.5, 9)
    ys = np.linspace(-.5, .5, 9)
    beam = build(8, z_offset=.0675,
                 torsion_constant=square_torsion_constant())
    four, _, _ = continuous_traction_rows(xs, ys, beam, intervals=2)
    five, wrench, meta = continuous_traction_rows(
        xs, ys, beam, intervals=2, local_yaw=True)
    assert five.shape[0] == 15
    assert meta["local_section_wrench_rank"] == 5
    for station in range(3):
        assert five[5 * station:5 * station + 4] == pytest.approx(
            four[4 * station:4 * station + 4], abs=1e-12)
        assert wrench[:, 5 * station + 4] == pytest.approx(
            [0., 0., 0., 0., 0., 1.], abs=1e-12)
        assert np.max(np.abs(five[5 * station + 4, 5::6])) == 0.
