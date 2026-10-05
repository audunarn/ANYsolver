"""Algebraic F03 Q1 trace preflight, not physical convergence evidence."""

import numpy as np
import pytest

from scripts._b3_e4_f03_conforming_q1_trace import FinitePadQ1Trace


@pytest.fixture(scope="module")
def trace():
    return FinitePadQ1Trace()


def _affine(trace, tx=0., ty=0., yaw=0.):
    x, y = np.meshgrid(trace.x, trace.y, indexing="ij")
    ux = tx-yaw*y
    uy = ty+yaw*x
    return np.r_[ux.ravel(), uy.ravel()]


def _independent_pose_moments(trace, station, q):
    """Integrate global monomials of each Q1 cell, without trace matrices."""
    result = np.zeros(3)
    ny = len(trace.y)
    def moment(xl, xr, yl, yr, ix, iy):
        return ((xr**(ix+1)-xl**(ix+1))/(ix+1)*
                (yr**(iy+1)-yl**(iy+1))/(iy+1))
    for ox, oy in trace.offsets:
        for i, (x0, x1) in enumerate(zip(trace.x, trace.x[1:])):
            xl, xr = max(x0, station+ox-trace.a), min(x1, station+ox+trace.a)
            if xr <= xl:
                continue
            for k, (y0, y1) in enumerate(zip(trace.y, trace.y[1:])):
                yl, yr = max(y0, oy-trace.a), min(y1, oy+trace.a)
                if yr <= yl:
                    continue
                indices = (i*ny+k, (i+1)*ny+k, i*ny+k+1, (i+1)*ny+k+1)
                fields = []
                for shift in (0, trace.n):
                    u00, u10, u01, u11 = q[np.array(indices)+shift]
                    c11 = (u11-u10-u01+u00)/((x1-x0)*(y1-y0))
                    c10 = (u10-u00)/(x1-x0)-c11*y0
                    c01 = (u01-u00)/(y1-y0)-c11*x0
                    c00 = u00-c10*x0-c01*y0-c11*x0*y0
                    fields.append((c00, c10, c01, c11))
                ux, uy = fields
                def integral(c, px=0, py=0):
                    return (c[0]*moment(xl,xr,yl,yr,px,py)+
                        c[1]*moment(xl,xr,yl,yr,px+1,py)+
                        c[2]*moment(xl,xr,yl,yr,px,py+1)+
                        c[3]*moment(xl,xr,yl,yr,px+1,py+1))
                result[0] += integral(ux)
                result[1] += integral(uy)
                result[2] += (integral(uy,px=1)-station*integral(uy)-
                    integral(ux,py=1))/trace.j
    return result/trace.area


@pytest.mark.parametrize("station", [0., .137, .43, .83, 1.])
def test_exact_degree_rigid_fields(trace, station):
    a0, a1, a2 = trace.matrices(station,
        side="right" if station < 1 else "left")
    assert np.allclose(a0@_affine(trace, tx=.7), (.7, 0., 0.), atol=1.e-14)
    assert np.allclose(a0@_affine(trace, ty=-.3), (0., -.3, 0.), atol=1.e-14)
    assert np.allclose(a1@_affine(trace, tx=.7, ty=-.3), 0., atol=1.e-14)
    yaw = _affine(trace, yaw=.4)
    # The represented binary64 J and pad geometry are checked independently.
    a = trace.a
    jgeom = sum(dx*dx+dy*dy+2*a*a/3 for dx, dy in trace.offsets)/4
    gamma = jgeom/trace.j
    assert np.allclose(a0@yaw, (0., .4*station, .4*gamma), atol=2.e-14)
    assert np.allclose(a1@yaw, (0., .4, 0.), atol=2.e-14)
    assert np.allclose(a2@yaw, 0., atol=2.e-13)


def test_root_pose_and_all_derivatives_are_independent(trace):
    a0, a1, _ = trace.matrices(0., side="right")
    # Convert rotation to an equivalent length and derivatives to their
    # value over the 1 m beam span before using singular values.
    rows = np.vstack((a0[:, trace.free_columns],
        a1[:, trace.free_columns]))
    scaled = np.diag((1., 1., .46, 1., 1., .46))@rows
    singular = np.linalg.svd(scaled, compute_uv=False)
    assert singular.shape == (6,) and singular[-1] > 1.e-4*singular[0]


@pytest.mark.parametrize("station", [0., .137, .43, 1.])
def test_independent_cell_moments_and_adjoint_work(trace, station):
    rng = np.random.default_rng(20260923)
    q = rng.standard_normal(2*trace.n)
    wrench = rng.standard_normal(3)
    a0 = trace.matrices(station,
        side="right" if station < 1 else "left")[0]
    pose = _independent_pose_moments(trace, station, q)
    assert np.linalg.norm(pose-a0@q) < 2.e-12
    assert abs(wrench@pose-q@(a0.T@wrench)) < 2.e-12


@pytest.mark.parametrize("station", [.137, .43, .83])
def test_leibniz_derivatives_match_independent_station_differences(trace, station):
    h = 1.e-5
    a0, a1, a2 = trace.matrices(station)
    left0, left1, _ = trace.matrices(station-h)
    right0, right1, _ = trace.matrices(station+h)
    assert np.linalg.norm((right0-left0)/(2*h)-a1) < 2.e-8
    assert np.linalg.norm((right1-left1)/(2*h)-a2) < 2.e-8
    # A direct second difference loses digits at the first-derivative step.
    h2 = 1.e-3
    outer_left = trace.matrices(station-h2)[0]
    outer_right = trace.matrices(station+h2)[0]
    assert np.linalg.norm((outer_right-2*a0+outer_left)/(h2*h2)-a2) < 1.e-7


def test_all_represented_pad_crossings_preserve_pose_and_first_derivative(trace):
    assert len(trace.x) == 10 and len(trace.y) == 6
    for dx, dy in trace.offsets:
        assert dx-trace.a in trace.x and 1+dx+trace.a in trace.x
        assert dy-trace.a in trace.y and dy+trace.a in trace.y
    events = trace.station_breakpoints()
    assert len(events) >= 10 and events[0] == 0. and events[-1] == 1.
    jumps = []
    for station in events[1:-1]:
        left = trace.matrices(station, side="left")
        right = trace.matrices(station, side="right")
        assert np.allclose(left[0], right[0], atol=2.e-14)
        assert np.allclose(left[1], right[1], atol=2.e-14)
        assert np.isfinite(left[2]).all() and np.isfinite(right[2]).all()
        jumps.append(np.linalg.norm(left[2]-right[2]))
    assert max(jumps) > 1.e-6


def test_geometry_rejection(trace):
    with pytest.raises(ValueError, match="leaves"):
        FinitePadQ1Trace(halfwidth=.3)
    with pytest.raises(ValueError, match="station"):
        trace.matrices(-.001)
    with pytest.raises(ValueError, match="one-sided"):
        trace.matrices(.5, side="both")
