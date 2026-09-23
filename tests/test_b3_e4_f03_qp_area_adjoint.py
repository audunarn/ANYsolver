"""Bounded independent area-work checks for the classical finite-pad push."""

import math

import numpy as np
import pytest

from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_primal_ritz import E0, F0
from scripts._b3_e4_f03_qp_area_adjoint import FinitePadAreaAdjoint
from scripts._b3_e4_f03_qp_beam_recovery import recover_interface
from scripts._b3_e4_f03_qp_piecewise_moment_oracle import PiecewisePadMomentOracle
from scripts._b3_e4_f03_qp_shell_recovery import PiecewiseQpShellRecovery


X = (-.5, -.12, .29, .81, 1.5)
Y = (-.5, -.08, .18, .5)


def _area_rule(trace):
    # Split the area integral where the moving pad edge crosses a shell
    # cell or a beam station event. This rule is independent of the
    # adjoint's station-primitive partition.
    x_edges = {trace.x[0], trace.x[-1]}
    y_edges = {*trace.y}
    for ox, oy in trace.offsets:
        y_edges.update((oy-trace.a, oy+trace.a))
        for station in (*trace.station_breakpoints(), 0., 1.):
            x_edges.update((station+ox-trace.a,
                            station+ox+trace.a))
    x_edges.update(trace.x)
    roots_x, weights_x = np.polynomial.legendre.leggauss(4)
    roots_y, weights_y = np.polynomial.legendre.leggauss(2)
    for xl, xr in zip(sorted(x_edges), sorted(x_edges)[1:]):
        if xr <= xl:
            continue
        for yb, yt in zip(sorted(y_edges), sorted(y_edges)[1:]):
            if yt <= yb:
                continue
            for rx, wx in zip(roots_x, weights_x):
                x = (xl+xr)/2+(xr-xl)*rx/2
                for ry, wy in zip(roots_y, weights_y):
                    y = (yb+yt)/2+(yt-yb)*ry/2
                    yield x, y, wx*wy*(xr-xl)*(yt-yb)/4


@pytest.mark.parametrize("p", (1, 2, 3))
def test_dead_load_and_root_atom_have_physical_area_density(p):
    trace = FinitePadQpTrace(p, x=X, y=Y)
    q = np.zeros(2*trace.n)
    eta = np.array((130., -75., 24.))
    pushed = FinitePadAreaAdjoint(trace, q, eta)
    with pytest.raises(ValueError):
        pushed.q[0] = 1.
    with pytest.raises(ValueError):
        pushed.eta[0] = 1.
    with pytest.raises(ValueError):
        pushed.atoms[0][0] = 1.
    np.testing.assert_allclose(pushed.integrated_line(0., 1.),
                               (0., F0, 0., F0/2, 0.), rtol=0,
                               atol=2e-10*max(1., F0))
    # The analytic cosine primitive is separately compared with both
    # registered fixed quadrature orders on a nontrivial station interval.
    left, right = .123, .876
    analytic = pushed.integrated_line(left, right)
    for order in (48, 64):
        roots, weights = np.polynomial.legendre.leggauss(order)
        stations = (left+right)/2+(right-left)*roots/2
        load = 1+.25*np.cos(2*math.pi*stations)
        numeric = (right-left)/2*F0*np.dot(weights, load)
        first_moment = (right-left)/2*F0*np.dot(
            weights, stations*load)
        assert abs(analytic[1]-numeric) <= 2e-13*max(1., F0)
        assert abs(analytic[3]-first_moment) <= 2e-13*max(1., F0)
    gamma = sum(ox*ox+oy*oy+2*trace.a**2/3
                for ox, oy in trace.offsets)/(len(trace.offsets)*trace.j)
    np.testing.assert_allclose(pushed.line_wrench(),
                               (-eta[0], F0-eta[1], F0/2-gamma*eta[2]),
                               rtol=0, atol=2e-10*max(1., F0))
    quarters = [(a/4, (a+1)/4) for a in range(4)]
    np.testing.assert_allclose(
        sum((pushed.band_wrench(left, right) for left, right in quarters)),
        pushed.line_wrench(), rtol=0, atol=2e-10*max(1., F0))
    np.testing.assert_allclose(
        pushed.band_wrench(0., 1., include_atoms=False),
        (0., F0, F0/2), rtol=0, atol=2e-10*max(1., F0))
    x, y = trace.offsets[0]
    without_atom = FinitePadAreaAdjoint(trace, q, np.zeros(3))
    difference = pushed.area_force(x, y)-without_atom.area_force(x, y)
    np.testing.assert_allclose(difference,
                               np.array((-eta[0]+y*eta[2]/trace.j,
                                         -eta[1]-x*eta[2]/trace.j))/trace.area,
                               rtol=0, atol=1e-10*max(1., np.linalg.norm(difference)))
    points = np.array(((x, y), (x, y+.01), (-.5, .45)))
    np.testing.assert_allclose(pushed.area_forces(points),
                               np.array([pushed.area_force(*point)
                                         for point in points]),
                               rtol=0, atol=1e-10)
    assert np.array_equal(pushed.area_force(-.5, .45), np.zeros(2))

    shifted = tuple((ox+.017, oy-.013) for ox, oy in trace.offsets)
    shifted_trace = FinitePadQpTrace(p, x=X, y=Y, offsets=shifted)
    shifted_push = FinitePadAreaAdjoint(
        shifted_trace, np.zeros(2*shifted_trace.n), eta)
    shifted_gamma = sum(ox*ox+oy*oy+2*trace.a**2/3
                        for ox, oy in shifted)/(len(shifted)*trace.j)
    expected_moment = F0*(.5+.017)-.017*eta[1]-.013*eta[0]
    expected_moment -= shifted_gamma*eta[2]
    np.testing.assert_allclose(shifted_push.line_wrench()[2], expected_moment,
                               rtol=0, atol=2e-10*max(1., F0))


def test_area_push_preserves_force_moment_and_nonrigid_virtual_work():
    trace = FinitePadQpTrace(1, x=X, y=Y, j=1.07*FinitePadQpTrace(1, x=X, y=Y).j)
    rng = np.random.default_rng(1606)
    q = 2e-5*rng.normal(size=2*trace.n)
    z = 3e-5*rng.normal(size=2*trace.n)
    eta = np.array((1.3e4, -8.2e3, 2.1e3))
    pushed = FinitePadAreaAdjoint(trace, q, eta)
    quarter_wrenches = [pushed.band_wrench(i/4, (i+1)/4)
                        for i in range(4)]
    np.testing.assert_allclose(np.sum(quarter_wrenches, axis=0),
                               pushed.line_wrench(), rtol=0, atol=2e-8)
    mean_x = np.mean([ox for ox, _ in trace.offsets])
    mean_y = np.mean([oy for _, oy in trace.offsets])
    gamma = np.mean([ox*ox+oy*oy+2*trace.a**2/3
                     for ox, oy in trace.offsets])/trace.j
    for index, (left, right) in enumerate(
            ((0., .25), (.25, .5), (.75, 1.))):
        allocated = (pushed.band_wrench(left, right)-
                     pushed.band_wrench(left, right,
                                        include_atoms=False))
        atom = pushed.atoms[0] if index == 0 else (
            pushed.atoms[1] if index == 2 else np.zeros(3))
        endpoint = 1 if index == 2 else 0
        expected = np.array((atom[0], atom[1],
                             (endpoint+mean_x)*atom[1]-mean_y*atom[0]
                             +gamma*atom[2]))
        np.testing.assert_allclose(allocated, expected, rtol=0, atol=2e-8)
    shell = PiecewiseQpShellRecovery(trace)
    z_coeff = shell.coefficients(z)
    area_wrench = np.zeros(3)
    area_work = 0.
    area_rule = tuple(_area_rule(trace))
    forces = pushed.area_forces(np.array([(x, y) for x, y, _ in area_rule]))
    for (x, y, weight), f in zip(area_rule, forces):
        area_wrench += weight*np.array((f[0], f[1], x*f[1]-y*f[0]))
        i = min(np.searchsorted(trace.x, x, side="right")-1,
                len(trace.x)-2)
        k = min(np.searchsorted(trace.y, y, side="right")-1,
                len(trace.y)-2)
        area_work += weight*(f@shell.state(z_coeff, i, k, x, y)[0])
    np.testing.assert_allclose(area_wrench, pushed.line_wrench(),
                               rtol=2e-10, atol=2e-8)

    oracle = PiecewisePadMomentOracle(1, x=X, y=Y, j=trace.j)
    z_oracle = oracle.coefficients(z)
    roots, weights = np.polynomial.legendre.leggauss(12)
    line_work = 0.
    for left, right in trace.station_intervals():
        stations = (left+right)/2+(right-left)*roots/2
        density = recover_interface(trace, q, eta, stations)["density"]
        pose = np.array([oracle.evaluate(z_oracle, float(s))[0]
                         for s in stations])
        line_work += (right-left)/2*np.einsum("i,ij,ij->",
                                               weights, density, pose)
    root, tip = pushed.atoms
    line_work += root@oracle.evaluate(z_oracle, 0., side="right")[0]
    line_work += tip@oracle.evaluate(z_oracle, 1., side="left")[0]
    assert abs(area_work-line_work)/max(E0, abs(area_work), abs(line_work)) < 2e-9
