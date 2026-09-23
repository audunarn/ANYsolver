"""Bounded mechanics checks for the unregistered conforming Q1 candidate."""

from dataclasses import replace
import math

import numpy as np
import pytest
from numpy.polynomial.legendre import leggauss
from scipy import sparse

from scripts._b3_e4_f03_conforming_q1_energy import (
    _station_rule, assemble, scaled_root_singular_values, solve,
)
from scripts._b3_e4_f03_primal_ritz import (
    E0, F0, PLANE, SECTION, THICKNESS, U0, YAW_LENGTH,
)


@pytest.fixture(scope="module")
def operators():
    return assemble()


def _full(operators, q):
    full = np.zeros(2*operators.trace.n)
    full[operators.free_columns] = q
    return full


def _field(trace, full, x, y):
    """Independent scalar Q1 interpolation, without helper shape rows."""
    i = min(np.searchsorted(trace.x, x, side="right")-1, len(trace.x)-2)
    k = min(np.searchsorted(trace.y, y, side="right")-1, len(trace.y)-2)
    assert i >= 0 and k >= 0
    x0, x1 = trace.x[i:i+2]
    y0, y1 = trace.y[k:k+2]
    tx, ty = (x-x0)/(x1-x0), (y-y0)/(y1-y0)
    ny = len(trace.y)
    nodes = (i*ny+k, (i+1)*ny+k, i*ny+k+1, (i+1)*ny+k+1)
    shape = np.array(((1-tx)*(1-ty), tx*(1-ty),
                      (1-tx)*ty, tx*ty))
    dx = np.array((-(1-ty), 1-ty, -ty, ty))/(x1-x0)
    dy = np.array((-(1-tx), -tx, 1-tx, tx))/(y1-y0)
    coefficients = np.array((full[list(nodes)], full[trace.n+np.array(nodes)]))
    return coefficients@shape, coefficients@dx, coefficients@dy


def _overlaps(edges, low, high):
    for a, b in zip(edges, edges[1:]):
        left, right = max(a, low), min(b, high)
        if right > left:
            yield left, right


def _independent_rule(left, right, order):
    roots, weights = leggauss(order)
    return (left+right)/2+(right-left)*roots/2, (right-left)*weights/2


def _independent_pose_and_derivative(trace, full, station):
    """Cell moments and moving-edge Leibniz terms, assembled from field values."""
    pose, derivative = np.zeros(3), np.zeros(3)
    roots, weights = leggauss(2)
    for ox, oy in trace.offsets:
        l, r = ox-trace.a, ox+trace.a
        low, high = station+l, station+r
        bottom, top = oy-trace.a, oy+trace.a
        pad_integral_y = 0.
        for xl, xr in _overlaps(trace.x, low, high):
            for yl, yr in _overlaps(trace.y, bottom, top):
                for gx, wx in zip(roots, weights):
                    x = (xl+xr+(xr-xl)*gx)/2
                    for gy, wy in zip(roots, weights):
                        y = (yl+yr+(yr-yl)*gy)/2
                        weight = (xr-xl)*(yr-yl)*wx*wy/4
                        value = _field(trace, full, x, y)[0]
                        pose += weight*np.array((value[0], value[1],
                                                 ((x-station)*value[1]-y*value[0])/trace.j))
                        pad_integral_y += weight*value[1]
        derivative[2] -= pad_integral_y/trace.j
        for yl, yr in _overlaps(trace.y, bottom, top):
            for gy, wy in zip(roots, weights):
                y = (yl+yr+(yr-yl)*gy)/2
                left = _field(trace, full, low, y)[0]
                right = _field(trace, full, high, y)[0]
                weight = (yr-yl)*wy/2
                derivative[:2] += weight*(right-left)
                derivative[2] += weight*(r*right[1]-l*left[1]
                                         -y*(right[0]-left[0]))/trace.j
    return pose/trace.area, derivative/trace.area


def _independent_shell_energy(trace, full):
    roots, weights = leggauss(3)
    energy = 0.
    for xl, xr in zip(trace.x, trace.x[1:]):
        for yl, yr in zip(trace.y, trace.y[1:]):
            for gx, wx in zip(roots, weights):
                x = (xl+xr+(xr-xl)*gx)/2
                for gy, wy in zip(roots, weights):
                    y = (yl+yr+(yr-yl)*gy)/2
                    _, dx, dy = _field(trace, full, x, y)
                    strain = np.array((dx[0], dy[1], dy[0]+dx[1]))
                    energy += (xr-xl)*(yr-yl)*wx*wy*THICKNESS/4 * strain@PLANE@strain
    return energy


def test_support_continuity_and_sparse_energy(operators):
    trace = operators.trace
    assert operators.dof_count == 96
    assert operators.station_intervals == 11
    rng = np.random.default_rng(3021)
    q = U0*rng.normal(size=operators.dof_count)
    full = _full(operators, q)
    ny = len(trace.y)
    assert np.count_nonzero(full[:ny]) == 0
    assert np.count_nonzero(full[(len(trace.x)-1)*ny:trace.n]) == 0
    for x in trace.x[1:-1]:
        for y in (-.31, .015, .29):
            left = _field(trace, full, np.nextafter(x, -np.inf), y)[0]
            right = _field(trace, full, np.nextafter(x, np.inf), y)[0]
            assert np.allclose(left, right, rtol=0, atol=1.e-17)
    for y in trace.y[1:-1]:
        for x in (-.33, .28, 1.14):
            low = _field(trace, full, x, np.nextafter(y, -np.inf))[0]
            high = _field(trace, full, x, np.nextafter(y, np.inf))[0]
            assert np.allclose(low, high, rtol=0, atol=1.e-17)
    shell = float(q@operators.shell_stiffness@q)
    independent = _independent_shell_energy(trace, full)
    assert shell > 0
    assert abs(shell-independent) < 2.e-11*independent
    assert np.max(np.abs((operators.shell_stiffness-operators.shell_stiffness.T).data)) < 1.e-5
    assert np.max(np.abs((operators.beam_stiffness-operators.beam_stiffness.T).data)) < 1.e-5


def test_independent_beam_energy_pose_and_load(operators):
    rng = np.random.default_rng(2026)
    q = U0*rng.normal(size=operators.dof_count)
    full = _full(operators, q)
    trace = operators.trace
    root = _independent_pose_and_derivative(trace, full, 0.)[0]
    tip = _independent_pose_and_derivative(trace, full, 1.)[0]
    assert np.allclose(root, operators.root_constraint@q, atol=2.e-17, rtol=2.e-11)
    assert np.allclose(tip, operators.tip_pose@q, atol=2.e-17, rtol=2.e-11)
    beam, load = 0., 0.
    for left, right in zip(trace.station_breakpoints(), trace.station_breakpoints()[1:]):
        stations, weights = _independent_rule(left, right, 8)
        for s, weight in zip(stations, weights):
            pose, derivative = _independent_pose_and_derivative(trace, full, float(s))
            strain = np.array((derivative[0], derivative[2], derivative[1]-pose[2]))
            beam += weight*strain@SECTION@strain
        stations, weights = _independent_rule(left, right, 64)
        for s, weight in zip(stations, weights):
            pose = _independent_pose_and_derivative(trace, full, float(s))[0]
            load += weight*F0*(1+.25*math.cos(2*math.pi*s))*pose[1]
    assembled_beam = float(q@operators.beam_stiffness@q)
    assembled_load = float(operators.load@q)
    assert abs(beam-assembled_beam) < 2.e-10*max(beam, 1.)
    assert abs(load-assembled_load) < 2.e-10*max(abs(load), 1.)
    assert operators.beam_discrepancy_relative < 1.e-12
    assert operators.load_discrepancy_scaled < 1.e-10


def test_dimensionless_root_rank_and_bounded_solve(operators):
    singulars = scaled_root_singular_values(operators)
    assert singulars[-1] > 1.e-5*singulars[0]
    diagonal = (operators.shell_stiffness+operators.beam_stiffness).diagonal()
    d = np.sqrt(E0/diagonal)
    shell_scaled = d[:, None]*operators.shell_stiffness.toarray()*d[None, :]/E0
    assert np.linalg.eigvalsh(shell_scaled)[0] > 1.e-5
    pose, derivative, _ = operators.trace.matrices(0.)
    root_scale = np.diag((1/U0, 1/U0, YAW_LENGTH/U0))
    stacked = np.vstack((root_scale@pose[:, operators.free_columns],
                         root_scale@derivative[:, operators.free_columns]))@np.diag(d)
    six = np.linalg.svd(stacked, compute_uv=False)
    assert six[-1] > 1.e-5*six[0]
    q, multiplier, metrics = solve(operators)
    assert np.isfinite(q).all() and np.isfinite(multiplier).all()
    assert metrics["root_compatibility_scaled"] < 1.e-11
    assert metrics["equilibrium_scaled"] < 1.e-11
    total = metrics["shell_energy_j"]+metrics["beam_energy_j"]
    assert abs(2*total-metrics["external_work_j"]) < 1.e-10*E0
    assert metrics["shell_nnz"] < operators.dof_count**2
    # Algebraic sign convention only: a unit root-y lifting measures the
    # signed residual, so the root reaction is the negative multiplier.
    # This is not independent physical support-reaction recovery.
    root = operators.root_constraint
    lifting = root.T@np.linalg.solve(root@root.T, np.array((0., 1., 0.)))
    assert np.allclose(root@lifting, (0., 1., 0.), atol=1.e-12)
    stiffness = operators.shell_stiffness+operators.beam_stiffness
    support_y = lifting@(stiffness@q-operators.load)
    assert np.isclose(support_y, -multiplier[1], rtol=1.e-10, atol=1.e-6)
    assert np.isclose(support_y, metrics["root_reaction_physical"][1],
                      rtol=1.e-10, atol=1.e-6)


def test_solve_rejects_missing_nonfinite_or_excessive_comparison(operators):
    unchecked = assemble(compare_quadrature=False)
    with pytest.raises(ValueError, match="quadrature comparison"):
        solve(unchecked)
    for changes in (
        {"beam_discrepancy_relative": float("inf")},
        {"load_discrepancy_scaled": float("nan")},
        {"beam_discrepancy_relative": 1.e-6},
        {"load_discrepancy_scaled": 1.e-6},
    ):
        with pytest.raises(ValueError, match="quadrature comparison"):
            solve(replace(operators, **changes))


def test_solve_rejects_indefinite_shell_even_with_positive_diagonal(operators):
    diagonal = operators.shell_stiffness.diagonal()
    direction = np.sqrt(diagonal)
    indefinite = (sparse.diags(diagonal) -
                  sparse.csr_matrix(2*np.outer(direction, direction)/len(diagonal)))
    assert np.all(indefinite.diagonal() > 0)
    with pytest.raises(ValueError, match="shell lacks positive energy"):
        solve(replace(operators, shell_stiffness=indefinite))


def test_solve_rejects_asymmetric_shell(operators):
    asymmetric = operators.shell_stiffness.tolil(copy=True)
    asymmetric[0, 1] += 1.e6
    with pytest.raises(ValueError, match="asymmetric Q1 shell"):
        solve(replace(operators, shell_stiffness=asymmetric.tocsr()))


def test_solve_rejects_lost_root_derivative_channels(operators):
    class LostDerivative:
        def matrices(self, station):
            pose, derivative, second = operators.trace.matrices(station)
            return pose, np.zeros_like(derivative), second

    with pytest.raises(ValueError, match="six independent channels"):
        solve(replace(operators, trace=LostDerivative()))


def test_represented_single_ulp_interval_keeps_weight(operators):
    pairs = list(zip(operators.trace.station_breakpoints(),
                     operators.trace.station_breakpoints()[1:]))
    tiny = [(left, right) for left, right in pairs
            if np.nextafter(left, right) >= right]
    assert tiny
    for left, right in tiny:
        for order in (4, 6, 48, 64):
            stations, weights = _station_rule(left, right, order)
            assert len(stations) == order
            assert np.isfinite(stations).all()
            assert math.isclose(float(sum(weights)), right-left, rel_tol=1.e-15)
