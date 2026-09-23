"""Independent sub-binary64 polynomial reconstruction checks."""

from decimal import localcontext

import numpy as np
import pytest
from numpy.polynomial.legendre import legval

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_primal_ritz import F0
from scripts._b3_e4_f03_qp_functional_conversion import (
    NORMALIZATION, _section_density,
)
from scripts._b3_e4_f03_qp_piecewise_moment_oracle import PiecewisePadMomentOracle
from scripts._b3_e4_f03_qp_subulp_density import (
    _d, _density, reconstruct_subulp_polynomial,
)


@pytest.mark.parametrize("degree", (1, 2, 3))
def test_subulp_polynomial_is_stable_and_checks_held_points(degree):
    trace = FinitePadQpTrace(degree)
    oracle = PiecewisePadMomentOracle(degree, x=trace.x, y=trace.y,
        offsets=trace.offsets, halfwidth=trace.a, j=trace.j)
    q = np.random.default_rng(71+degree).normal(size=2*trace.n)*2e-4
    coeff = oracle.coefficients(q)
    intervals = [(left, right) for left, right in trace.station_intervals()
                 if np.nextafter(left, np.inf) >= right]
    assert len(intervals) == 3
    for left, right in intervals:
        coarse, held = reconstruct_subulp_polynomial(oracle, coeff,
            left, right, degree+2, precision=90)
        precise, precise_held = reconstruct_subulp_polynomial(oracle, coeff,
            left, right, degree+2, precision=120)
        assert held/max(NORMALIZATION) < 1e-55
        assert precise_held/max(NORMALIZATION) < 1e-80
        assert np.max(np.abs(coarse-precise)/NORMALIZATION) < 1e-13
        assert np.isfinite(coarse).all()
        # A one-sided constant is not assumed: retain resolved higher order.
        assert np.max(np.abs(coarse[1:])) > 0.


@pytest.mark.parametrize("degree", (1, 2, 3))
def test_decimal_density_matches_separate_float_oracle_away_from_events(degree):
    trace = FinitePadQpTrace(degree)
    oracle = PiecewisePadMomentOracle(degree, x=trace.x, y=trace.y,
        offsets=trace.offsets, halfwidth=trace.a, j=trace.j)
    q = np.random.default_rng(91+degree).normal(size=2*trace.n)*2e-4
    coeff = oracle.coefficients(q)
    with localcontext() as ctx:
        ctx.prec = 90
        exact_coeff = [[[[[_d(v) for v in row] for row in plane]
                        for plane in cell] for cell in field] for field in coeff]
        for station in (.173, .422, .733):
            exact = np.asarray([float(v) for v in _density(
                oracle, exact_coeff, _d(station))])
            direct = _section_density(oracle, coeff, station, "right")
            direct[1] -= .25*F0*np.cos(2*np.pi*station)
            assert np.max(np.abs(exact-direct)/NORMALIZATION) < 1e-10


def test_crossing_inside_an_interval_is_rejected():
    trace = FinitePadQpTrace(1)
    oracle = PiecewisePadMomentOracle(1, x=trace.x, y=trace.y,
        offsets=trace.offsets, halfwidth=trace.a, j=trace.j)
    q = np.zeros(2*trace.n)
    with pytest.raises(ArithmeticError, match="crossing"):
        reconstruct_subulp_polynomial(oracle, oracle.coefficients(q),
                                      .55, .65, 3)
