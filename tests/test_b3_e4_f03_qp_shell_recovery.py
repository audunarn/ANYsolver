"""Algebraic, fixed-quadrature shell recovery checks; no equilibrium solve."""

import numpy as np
import pytest

from scripts._b3_e4_f03_conforming_qp_energy import _shell
from scripts._b3_e4_f03_conforming_qp_trace import FinitePadQpTrace
from scripts._b3_e4_f03_primal_ritz import PLANE, THICKNESS
from scripts._b3_e4_f03_qp_shell_recovery import PiecewiseQpShellRecovery


X = (-.5, -.12, .29, .81, 1.5)
Y = (-.5, -.08, .18, .5)


def _trace(p):
    return FinitePadQpTrace(p, x=X, y=Y)


def _nodal(trace, ux, uy):
    xx, yy = np.meshgrid(trace.nodes_x, trace.nodes_y, indexing="ij")
    return np.r_[ux(xx, yy).ravel(), uy(xx, yy).ravel()]


def _scale(*values):
    return max(1., *(abs(float(v)) for v in values))


@pytest.mark.parametrize("p", (1, 2, 3))
def test_cell_state_and_outer_normal_orientation(p):
    trace = _trace(p)
    recovery = PiecewiseQpShellRecovery(trace)
    q = _nodal(trace, lambda x, y: .2+.3*x-.4*y,
                     lambda x, y: -.1+.7*x+.5*y)
    coeff = recovery.coefficients(q)
    strain = np.array((.3, .5, .3))
    resultant = THICKNESS*(PLANE@strain)
    tensor = np.array(((resultant[0], resultant[2]),
                       (resultant[2], resultant[1])))
    for i, k in ((0, 0), (1, 1), (len(X)-2, len(Y)-2)):
        x, y = (X[i]+X[i+1])/2, (Y[k]+Y[k+1])/2
        u, actual_strain, actual_tensor, divergence = recovery.state(
            coeff, i, k, x, y)
        np.testing.assert_allclose(u, (.2+.3*x-.4*y, -.1+.7*x+.5*y),
                                   rtol=0, atol=2e-14)
        np.testing.assert_allclose(actual_strain, strain, rtol=0, atol=2e-13)
        np.testing.assert_allclose(actual_tensor, tensor, rtol=0,
                                   atol=3e-13*_scale(*tensor.ravel()))
        np.testing.assert_allclose(divergence, 0, rtol=0,
                                   atol=4e-12*_scale(*tensor.ravel()))
    for side in (-1, 1):
        np.testing.assert_allclose(recovery.outer_traction(
            coeff, "x", side, 1, 0.), side*tensor[:, 0], rtol=0,
            atol=3e-13*_scale(*tensor.ravel()))
        np.testing.assert_allclose(recovery.outer_traction(
            coeff, "y", side, 1, 0.), side*tensor[:, 1], rtol=0,
            atol=3e-13*_scale(*tensor.ravel()))


@pytest.mark.parametrize("p", (1, 2, 3))
def test_signed_green_identity_and_sparse_shell_work(p):
    trace = _trace(p)
    recovery = PiecewiseQpShellRecovery(trace)
    rng = np.random.default_rng(4400+p)
    q = 1e-5*rng.standard_normal(2*trace.n)
    z = 1e-5*rng.standard_normal(2*trace.n)
    channels = recovery.integration_by_parts(q, z)
    direct = recovery.energy_work(q, z)
    assert abs(channels.total-direct) <= 4e-11*_scale(direct)
    assert abs(channels.interior) > 1e-5*_scale(direct)
    assert abs(channels.support) > 1e-5*_scale(direct)
    assert abs(channels.free) > 1e-5*_scale(direct)

    # Essential x-edge values are zero for the sparse shell assembly.
    free = trace.free_columns
    q0, z0 = np.zeros(2*trace.n), np.zeros(2*trace.n)
    q0[free], z0[free] = q[free], z[free]
    sparse_work = q0[free]@(_shell(trace, free)@z0[free])
    polynomial_work = recovery.energy_work(q0, z0)
    assert abs(polynomial_work-sparse_work) <= 4e-11*_scale(sparse_work)
    supported = recovery.integration_by_parts(q0, z0)
    assert abs(supported.support) <= 3e-12*_scale(sparse_work)
    assert abs(supported.total-sparse_work) <= 4e-11*_scale(sparse_work)


@pytest.mark.parametrize("p", (1, 2, 3))
def test_edge_jump_both_orientations_and_force_moment_channels(p):
    trace = _trace(p)
    recovery = PiecewiseQpShellRecovery(trace)
    rng = np.random.default_rng(5700+p)
    q = 1e-5*rng.standard_normal(2*trace.n)
    coeff = recovery.coefficients(q)
    for axis, edge, segment, coordinate in (
            ("x", 1, 1, .03), ("x", 2, 0, -.31),
            ("y", 1, 1, .02), ("y", 2, 2, .54)):
        forward = recovery.interior_jump(coeff, axis, edge, segment, coordinate)
        backward = recovery.interior_jump(
            coeff, axis, edge, segment, coordinate, reverse=True)
        if axis == "x":
            low = recovery.state(coeff, edge-1, segment,
                                 trace.x[edge], coordinate)[2]
            high = recovery.state(coeff, edge, segment,
                                  trace.x[edge], coordinate)[2]
            expected = low@np.array((1., 0.))+high@np.array((-1., 0.))
        else:
            low = recovery.state(coeff, segment, edge-1,
                                 coordinate, trace.y[edge])[2]
            high = recovery.state(coeff, segment, edge,
                                  coordinate, trace.y[edge])[2]
            expected = low@np.array((0., 1.))+high@np.array((0., -1.))
        np.testing.assert_allclose(forward, expected, rtol=0,
                                   atol=2e-13*_scale(*forward))
        np.testing.assert_allclose(backward, forward, rtol=0,
                                   atol=2e-13*_scale(*forward))
        assert np.linalg.norm(forward) > 0

    channels = recovery.force_moment_channels(q)
    assert set(channels) == {"volume", "support", "free", "interior"}
    total = sum(channels.values())
    largest = max(np.linalg.norm(item) for item in channels.values())
    np.testing.assert_allclose(total, 0, rtol=0,
                               atol=5e-11*max(1., largest))
    assert np.linalg.norm(channels["support"]) > 0
    assert np.linalg.norm(channels["free"]) > 0
    assert np.linalg.norm(channels["interior"]) > 0


def test_bounded_input_rejection():
    with pytest.raises(TypeError, match="trace"):
        PiecewiseQpShellRecovery(object())
    recovery = PiecewiseQpShellRecovery(_trace(2))
    with pytest.raises(ValueError, match="coefficients"):
        recovery.state(np.zeros((2, 2)), 0, 0, -.3, -.3)
    coeff = recovery.coefficients(np.zeros(2*recovery.trace.n))
    with pytest.raises(ValueError, match="outside selected"):
        recovery.state(coeff, 0, 0, .5, -.3)
    with pytest.raises(ValueError, match="interior"):
        recovery.interior_jump(coeff, "x", 0, 0, -.3)
