"""Bounded Qp trace checks; no energy, solve, or scientific claim."""

import math

import numpy as np
import pytest

from scripts._b3_e4_f03_conforming_q1_trace import FinitePadQ1Trace
from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace


def _nodal_field(trace, ux, uy):
    xx, yy = np.meshgrid(trace.nodes_x, trace.nodes_y, indexing="ij")
    return np.r_[ux(xx, yy).ravel(), uy(xx, yy).ravel()]


def _physical_pose(trace, station, ux, uy):
    """Independent integration of global polynomial physical fields."""
    roots, weights = np.polynomial.legendre.leggauss(10)
    result = np.zeros(3)
    for ox, oy in trace.offsets:
        for gx, wx in zip(roots, weights):
            xi = ox+trace.a*gx
            for gy, wy in zip(roots, weights):
                eta = oy+trace.a*gy
                vx, vy = ux(station+xi, eta), uy(station+xi, eta)
                result += trace.a**2*wx*wy*np.array(
                    (vx, vy, (xi*vy-eta*vx)/trace.j))
    return result/trace.area


@pytest.mark.parametrize("degree,expected", [
    (1, 96), (2, 374), (3, 832), (4, 1470), (5, 2288), (6, 3286),
])
def test_shared_nodes_essential_edges_and_exact_polynomial_work(degree, expected):
    trace = FinitePadQpTrace(degree)
    assert len(trace.free_columns) == expected
    assert len(np.unique(trace.free_columns)) == expected
    assert len(trace.station_intervals()) == len(trace.station_breakpoints())-1
    assert all(b > a for a, b in trace.station_intervals())
    assert sum(b-a for a, b in trace.station_intervals()) == pytest.approx(1.)
    ux = lambda x, y: .3+x**degree*y-.2*y**degree
    uy = lambda x, y: -.4+x**degree+.7*x*y**degree
    q = _nodal_field(trace, ux, uy)
    s = .137
    matrix = trace.matrices(s)[0]
    pose = _physical_pose(trace, s, ux, uy)
    assert np.allclose(matrix@q, pose, atol=3e-13)
    wrench = np.array((.6, -.2, .9))
    assert abs(wrench@pose-q@(matrix.T@wrench)) < 3e-13


@pytest.mark.parametrize("degree", (1, 2, 3, 4, 5, 6))
def test_rigid_gain_root_rank_and_derivative_plateau(degree):
    trace = FinitePadQpTrace(degree)
    jgeom = sum(dx*dx+dy*dy+2*trace.a**2/3
        for dx, dy in trace.offsets)/4
    q = _nodal_field(trace,
        lambda x, y: .7-.4*y, lambda x, y: -.3+.4*x)
    s = .137
    a0, a1, a2 = trace.matrices(s)
    assert np.allclose(a0@q, (.7, -.3+.4*s, .4*jgeom/trace.j), atol=2e-13)
    assert np.allclose(a1@q, (0., .4, 0.), atol=2e-12)
    assert np.allclose(a2@q, 0., atol=3e-11)
    root, slope, _ = trace.matrices(0.)
    rows = np.vstack((root[:, trace.free_columns],
        slope[:, trace.free_columns]))
    singular = np.linalg.svd(np.diag((1., 1., .46, 1., 1., .46))@rows,
        compute_uv=False)
    assert singular[-1] > 1e-4*singular[0]
    # Q4/Q5 curvature increases the O(h²) truncation term; the measured
    # 1e-5, 5e-6, 2.5e-6 plateau supports the smaller high-order step.
    h = 1e-5 if degree <= 3 else 2.5e-6
    lm = trace.matrices(s-h)
    rm = trace.matrices(s+h)
    assert np.linalg.norm((rm[0]-lm[0])/(2*h)-a1) < 2e-7
    assert np.linalg.norm((rm[1]-lm[1])/(2*h)-a2) < 2e-6
    # A' is continuous and A'' is piecewise bounded, the numerical H2 check.
    events = trace.station_breakpoints()[1:-1]
    assert events
    jumps = []
    for station in events:
        left, right = (trace.matrices(station, side=side)
            for side in ("left", "right"))
        assert np.linalg.norm(left[0]-right[0]) < 3e-12
        assert np.linalg.norm(left[1]-right[1]) < 3e-11
        assert np.isfinite(left[2]).all() and np.isfinite(right[2]).all()
        jumps.append(np.linalg.norm(left[2]-right[2]))
    # A'' may jump: at least one actual pad/cell crossing has distinct
    # one-sided curvatures while A and A' retain a common trace.
    assert max(jumps) > 1e-7


def test_p1_matrices_match_existing_q1_reference():
    qp, q1 = FinitePadQpTrace(1), FinitePadQ1Trace()
    assert qp.x == q1.x and qp.y == q1.y
    assert qp.station_breakpoints() == q1.station_breakpoints()
    for station, side in ((0., "right"), (.137, "right"),
                          (.43, "right"), (1., "left")):
        for generic, reference in zip(qp.matrices(station, side=side),
                                      q1.matrices(station, side=side)):
            assert np.linalg.norm(generic-reference) < 5e-12


def test_near_duplicate_represented_events_retain_measure_and_sides():
    trace = FinitePadQpTrace(2)
    intervals = trace.station_intervals()
    tiny = [(a, b) for a, b in intervals if 0 < b-a < 1e-14]
    assert tiny, "represented binary64 crossings should remain distinct"
    assert all(b > a for a, b in tiny)
    for a, b in tiny:
        assert math.nextafter(a, math.inf) <= b
        assert b-a > 0
    # At an ordinary station one ulp away from a crossing, no event snap is
    # applied. The limiting second derivative remains finite on both sides.
    a, b = tiny[0]
    for station in (a, b):
        for side in ("left", "right"):
            assert np.isfinite(trace.matrices(station, side=side)[2]).all()


def test_bad_geometry_and_degree():
    with pytest.raises(ValueError, match="degree"):
        FinitePadQpTrace(7)
    with pytest.raises(ValueError, match="leaves"):
        FinitePadQpTrace(2, halfwidth=.3)
    with pytest.raises(ValueError, match="station"):
        FinitePadQpTrace(1).matrices(-.1)
