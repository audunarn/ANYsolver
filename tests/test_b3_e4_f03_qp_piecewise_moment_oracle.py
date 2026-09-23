"""Fixed, bounded F03 Qp pad-moment comparisons; no equilibrium solve."""

import numpy as np
import pytest

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_qp_piecewise_moment_oracle import (
    PiecewisePadMomentOracle, REPRESENTED_J,
)


GRIDS = (
    (None, None),
    ((-.5, -.35, -.11, .08, .31, .67, .94, 1.23, 1.5),
     (-.5, -.31, -.09, .11, .31, .5)),
    ((-.5, -.22, .02, .24, .51, .76, 1.03, 1.28, 1.5),
     (-.5, -.29, 0., .26, .5)),
)


def _nodes(oracle):
    x = [oracle.x[i]+(oracle.x[i+1]-oracle.x[i])*a/oracle.p
         for i in range(len(oracle.x)-1) for a in range(oracle.p)]
    y = [oracle.y[k]+(oracle.y[k+1]-oracle.y[k])*b/oracle.p
         for k in range(len(oracle.y)-1) for b in range(oracle.p)]
    return np.meshgrid((*x, oracle.x[-1]), (*y, oracle.y[-1]), indexing="ij")


@pytest.mark.parametrize("degree", (1, 2, 3))
@pytest.mark.parametrize("grid", GRIDS)
def test_piecewise_random_fields_and_one_sided_events(degree, grid):
    x, y = grid
    trace = FinitePadQpTrace(degree, x=x, y=y)
    oracle = PiecewisePadMomentOracle(degree, x=x, y=y)
    assert (oracle.x, oracle.y, oracle.n, oracle.j) == (
        trace.x, trace.y, trace.n, trace.j)
    rng = np.random.default_rng(9100+100*degree+len(trace.x))
    q = rng.standard_normal(2*trace.n)
    coeff = oracle.coefficients(q)
    # The Vandermonde reconstruction must retain the *piecewise* nodal data,
    # including independent higher modes, before it is used as a reference.
    for i, k in ((0, 0), (len(oracle.x)-2, len(oracle.y)-2)):
        for a in range(degree+1):
            for b in range(degree+1):
                t, v = 2*a/degree-1, 2*b/degree-1
                powers = np.outer(t**np.arange(degree+1),
                                  v**np.arange(degree+1))
                index = (i*degree+a)*oracle.ny+k*degree+b
                np.testing.assert_allclose(
                    np.einsum("cik,ik->c", coeff[:, i, k], powers),
                    (q[index], q[oracle.n+index]), rtol=0, atol=2e-13)

    events = trace.station_breakpoints()
    ordinary = (.137, .413, .779)
    interior = [event for event in events[1:-1]
                if .02 < event < .98]
    # Select the first, middle, and last crossings, retaining exact binary64
    # stations rather than rounding nominal decimals.
    selected = tuple(dict.fromkeys((interior[0],
                                    interior[len(interior)//2], interior[-1])))
    stations = [(s, "right") for s in ordinary]
    stations += [(s, side) for s in selected for side in ("left", "right")]
    for station, side in stations:
        actual = tuple(matrix@q for matrix in trace.matrices(station, side=side))
        expected = oracle.evaluate(coeff, station, side=side)
        # Local t,v powers are integrated exactly. The allowances cover the
        # Q3 Vandermonde solve and subtraction of nearby edge/area moments;
        # the second derivative has the larger cancellation factor.
        for order, tolerance in enumerate((2e-12, 5e-12, 2e-11)):
            np.testing.assert_allclose(actual[order], expected[order],
                                       rtol=0, atol=tolerance,
                                       err_msg=f"p={degree}, s={station}, side={side}, order={order}")


@pytest.mark.parametrize("degree", (1, 2, 3))
@pytest.mark.parametrize("j", (REPRESENTED_J, 1.07*REPRESENTED_J))
def test_physical_yaw_work_and_represented_gamma(degree, j):
    trace = FinitePadQpTrace(degree, j=j)
    oracle = PiecewisePadMomentOracle(degree, j=j)
    xx, yy = _nodes(oracle)
    q = np.r_[(.7-.4*yy).ravel(), (-.3+.4*xx).ravel()]
    station = .137
    pose = oracle.moments(q, station)[0]
    j_geom = sum(dx*dx+dy*dy+2*oracle.a**2/3
                 for dx, dy in oracle.offsets)/4
    gamma = j_geom/j
    np.testing.assert_allclose(pose, (.7, -.3+.4*station, .4*gamma),
                               rtol=0, atol=2e-13)
    rng = np.random.default_rng(712+degree)
    random_q = rng.standard_normal(2*trace.n)
    wrench = np.array((.6, -.2, .9))
    # The third wrench component acts on the physical finite-pad yaw, with
    # the requested J. The shifted-J case detects silently replacing J by
    # the geometric second moment. Check each station derivative's work too.
    matrices = trace.matrices(station)
    direct = oracle.moments(random_q, station)
    for order, tolerance in enumerate((2e-12, 5e-12, 2e-11)):
        direct_work = wrench@direct[order]
        matrix_work = random_q@(matrices[order].T@wrench)
        assert abs(direct_work-matrix_work) < tolerance


def test_bounded_geometry_and_input():
    with pytest.raises(ValueError, match="degree"):
        PiecewisePadMomentOracle(4)
    oracle = PiecewisePadMomentOracle(3)
    with pytest.raises(ValueError, match="q must"):
        oracle.coefficients(np.zeros(2*oracle.n-1))
    with pytest.raises(ValueError, match="station"):
        oracle.moments(np.zeros(2*oracle.n), -1e-3)
