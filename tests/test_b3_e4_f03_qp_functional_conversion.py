"""Preparatory Qp coefficient recovery checks without a scientific solve."""

import numpy as np
import pytest
from numpy.polynomial.legendre import leggauss, legval

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_qp_beam_recovery import recover_interface
from scripts._b3_e4_f03_qp_functional_conversion import (
    FIT_TOLERANCE, from_qp_recovery,
)
from scripts import _b3_e4_f03_qp_functional_conversion as conversion
from scripts._b3_e4_f03_qp_piecewise_functional import norm_squared


CUSTOM_X = (-.5, -.35, -.11, .08, .31, .67, .94, 1.23, 1.5)
CUSTOM_Y = (-.5, -.31, -.09, .11, .31, .5)
ETA = np.array((1.6e5, -2.2e5, 7.1e4))


def state(degree, custom):
    x, y = (CUSTOM_X, CUSTOM_Y) if custom else (None, None)
    trace = FinitePadQpTrace(degree, x=x, y=y)
    rng = np.random.default_rng(900+degree+10*custom)
    # The Q6 rough random field is ten times larger than the solved-state
    # curvature scale and can exceed the unchanged direct-recovery guard
    # solely from floating-point cancellation.
    amplitude = 2e-5 if degree == 6 else 2e-4
    q = rng.normal(size=2*trace.n)*amplitude
    q[np.setdiff1d(np.arange(2*trace.n), trace.free_columns)] = 0.
    return trace, q


def represented_density(functional, interval, fractions):
    left, right = functional.breaks[interval:interval+2]
    s = left+(right-left)*fractions
    polynomial = np.moveaxis(legval(2*fractions-1,
        functional.coefficients[interval]), 0, -1)
    return polynomial+np.cos(2*np.pi*s)[:, None]*functional.cosine


@pytest.mark.parametrize("degree", (1, 2, 3, 4, 5, 6))
@pytest.mark.parametrize("custom", (False, True))
def test_qp_fit_preserves_intervals_and_validates_held_points(degree, custom):
    trace, q = state(degree, custom)
    audit = from_qp_recovery(trace, q, ETA)
    f = audit.functional
    np.testing.assert_array_equal(f.breaks, trace.station_breakpoints())
    assert f.coefficients.shape == (len(trace.station_intervals()), degree+3, 3)
    np.testing.assert_array_equal(f.cosine, (0., .25e6, 0.))
    assert audit.max_oracle_fit_defect <= FIT_TOLERANCE
    assert audit.max_direct_recovery_defect <= FIT_TOLERANCE
    assert audit.max_atom_defect <= FIT_TOLERANCE
    if custom:
        assert audit.fallback_intervals == 0
        assert audit.no_binary64_interior_intervals == 0
        assert audit.fallback_total_width == 0.
    else:
        assert audit.fallback_intervals == 3
        assert audit.no_binary64_interior_intervals == 3
        assert 0. < audit.fallback_total_width < 1e-14
        assert audit.max_fallback_endpoint_spread > 0.
        for i, (left, right) in enumerate(trace.station_intervals()):
            if np.nextafter(left, np.inf) == right:
                assert np.all(f.coefficients[i, 1:] == 0.)
    direct_ends = recover_interface(trace, q, ETA, np.array((0., 1.)))
    np.testing.assert_allclose(f.atoms[0], direct_ends["root_atom"],
                               atol=2e-7, rtol=2e-13)
    np.testing.assert_allclose(f.atoms[1], direct_ends["tip_atom"],
                               atol=2e-7, rtol=2e-13)
    norm = norm_squared(f)
    assert norm.squared_total > 0.
    assert np.max(norm.density_order_discrepancy) <= 1e-10
    assert np.max(norm.cross_order_discrepancy) <= 1e-10


@pytest.mark.parametrize("degree", (1, 2, 3, 4, 5, 6))
def test_total_virtual_work_matches_direct_density_and_endpoint_atoms(degree):
    trace, q = state(degree, True)  # all intervals are sampleable
    f = from_qp_recovery(trace, q, ETA).functional
    roots, weights = leggauss(12)
    fractions = (roots+1.)/2.
    weights = weights/2.
    fitted_work = direct_work = 0.
    # An unrestricted smooth pose test has nonzero root and tip values.
    def pose(s):
        return np.stack((1+s, 1-s*s, s+.25), axis=-1)
    for i, (left, right) in enumerate(trace.station_intervals()):
        s = left+(right-left)*fractions
        fitted = represented_density(f, i, fractions)
        direct = recover_interface(trace, q, ETA, s)["density"]
        fitted_work += (right-left)*np.einsum("i,ij,ij->", weights,
                                             fitted, pose(s))
        direct_work += (right-left)*np.einsum("i,ij,ij->", weights,
                                             direct, pose(s))
    endpoints = pose(np.array((0., 1.)))
    fitted_work += np.einsum("ij,ij->", f.atoms, endpoints)
    recovered = recover_interface(trace, q, ETA, np.array((0., 1.)))
    direct_work += recovered["root_atom"]@endpoints[0]
    direct_work += recovered["tip_atom"]@endpoints[1]
    assert abs(fitted_work-direct_work)/max(1e6, abs(direct_work)) < 1e-10


def test_rejects_invalid_state_without_fitting():
    trace, q = state(1, True)
    with pytest.raises(ValueError, match="state"):
        from_qp_recovery(trace, q[:-1], ETA)
    with pytest.raises(ValueError, match="state"):
        from_qp_recovery(trace, q, np.array((0., 0., np.nan)))


def test_declared_degree_mismatch_is_reported(monkeypatch):
    trace, q = state(1, True)
    original = conversion._section_density
    def higher_degree(oracle, coefficients, station, side):
        result = original(oracle, coefficients, station, side)
        result[0] += 1e9*station**4  # p+3, beyond declared p+2
        return result
    monkeypatch.setattr(conversion, "_section_density", higher_degree)
    with pytest.raises(conversion.PolynomialDegreeMismatch, match=r"p\+2"):
        from_qp_recovery(trace, q, ETA)
