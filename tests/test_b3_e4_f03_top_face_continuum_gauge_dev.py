"""Independent continuous-action check for the private top-face line candidate.

These checks do not qualify an attachment or a multiplier space. They expose
the coefficient gauge of a one-sided affine surface-traction representation.
"""

import numpy as np
import pytest


WIDTH_M = 0.1
LOW_M, HIGH_M = 0.9, 1.0
CENTER_M = 0.95


def _traction(x, y, force, moment):
    arm = np.array((x-CENTER_M, y, 0.0))
    return (np.asarray(force)+np.cross(moment, arm))/WIDTH_M


def test_nonzero_continuous_force_moment_coefficients_have_zero_surface_action():
    roots, weights = np.polynomial.legendre.leggauss(5)
    work = 0.0
    for xi, wx in zip(roots, weights):
        x = (LOW_M+HIGH_M)/2+(HIGH_M-LOW_M)*xi/2
        mu = 2.0+0.3*(x-CENTER_M)/WIDTH_M
        force = np.array((0.0, 0.0, (x-CENTER_M)*mu))
        moment = np.array((0.0, mu, 0.0))
        assert np.linalg.norm(np.r_[force, moment]) > 1.0
        for eta, wy in zip(roots, weights):
            y = WIDTH_M*eta/2
            traction = _traction(x, y, force, moment)
            np.testing.assert_allclose(traction, 0.0, rtol=0.0, atol=2e-15)
            virtual_gap = np.array((1+x*x, y+x*y, x-LOW_M+y*y))
            work += wx*wy*(HIGH_M-LOW_M)*WIDTH_M/4*traction@virtual_gap
    assert abs(work) < 1e-15


@pytest.mark.parametrize("x", (LOW_M, CENTER_M, HIGH_M))
def test_local_traction_action_has_exactly_five_independent_fields(x):
    columns = np.eye(6)
    map_rows = np.vstack([
        np.column_stack([
            _traction(x, y, column[:3], column[3:])
            for column in columns
        ])
        for y in (-WIDTH_M/2, 0.0, WIDTH_M/2)
    ])
    singular = np.linalg.svd(map_rows, compute_uv=False)
    assert np.count_nonzero(singular > 1e-12*singular[0]) == 5
    gauge = np.array((0.0, 0.0, x-CENTER_M, 0.0, 1.0, 0.0))
    np.testing.assert_allclose(map_rows@gauge, 0.0, rtol=0.0, atol=2e-15)


@pytest.mark.parametrize("intervals", (2, 4, 8, 16))
def test_midpoint_p0_approximation_of_gauge_has_exact_h_squared_work(intervals):
    length = HIGH_M-LOW_M
    h = length/intervals
    roots, weights = np.polynomial.legendre.leggauss(3)
    traction_square = 0.0
    supported_virtual_work = 0.0
    for i in range(intervals):
        center = LOW_M+(i+0.5)*h
        force = (0.0, 0.0, center-CENTER_M)
        moment = (0.0, 1.0, 0.0)
        for xi, wx in zip(roots, weights):
            x = center+h*xi/2
            for eta, wy in zip(roots, weights):
                y = WIDTH_M*eta/2
                traction = _traction(x, y, force, moment)
                area = wx*wy*h*WIDTH_M/4
                traction_square += area*(traction@traction)
                supported_virtual_work += area*traction[2]*(x-LOW_M)
    np.testing.assert_allclose(
        traction_square, length*h*h/(12*WIDTH_M), rtol=2e-12, atol=1e-18)
    np.testing.assert_allclose(
        supported_virtual_work, -length*h*h/12, rtol=2e-12, atol=1e-18)
