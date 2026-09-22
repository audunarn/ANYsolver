"""Bounded, independently interpolated trace checks for the F03 comparator.

The manufactured field diagnoses reference hosts and pose derivatives. It is
not the solved loaded state or a native shell/beam qualification.
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell


AMPLITUDE = 1e-3


def _field(x, y):
    # Coordinates are metres divided by L0=W0=1 m.
    return AMPLITUDE * (x*x + .4*x*y*y)


def _nodal(model):
    q = np.zeros(model.dof_count)
    q[1::2] = _field(model.nodes[:, 0], model.nodes[:, 1])
    return q


def _independent_sample(model, x, y, q):
    """Grid-local Q4 tensor product or geometric triangle barycentrics.

    Deliberately does not call the production comparator's sample/shape/pose.
    """
    i = min(max(int(np.floor((x + .5)*model.n_s)), 0), 2*model.n_s-1)
    j = min(max(int(np.floor((y + .5)*model.n_y)), 0), model.n_y-1)
    x0 = -.5+i/model.n_s
    y0 = -.5+j/model.n_y
    a = (x-x0)*model.n_s
    b = (y-y0)*model.n_y
    bl = j*(2*model.n_s+1)+i
    br = bl+1
    tl = bl+2*model.n_s+1
    tr = tl+1
    if model.topology == "Q4":
        ids = (bl,br,tr,tl)
        weights = np.array(((1-a)*(1-b), a*(1-b), a*b, (1-a)*b))
        deriv = model.n_s*np.array((-(1-b), 1-b, b, -b))
    else:
        candidates = ((bl,br,tl),(br,tr,tl)) if (i+j)%2 else (
            (bl,br,tr),(bl,tr,tl))
        for ids in candidates:
            xyz = model.nodes[list(ids)]
            basis = np.column_stack((np.ones(3), xyz))
            coefficients = np.linalg.solve(basis, q[2*np.array(ids)+1])
            weights = np.linalg.solve(basis.T, [1., x, y])
            if min(weights) >= -1e-10:
                return float(coefficients @ [1., x, y]), float(coefficients[1])
        raise AssertionError("manufactured sample has no triangle host")
    values = q[2*np.array(ids)+1]
    return float(weights@values), float(deriv@values)


def _independent_pose(model, s, q):
    displacements = []
    derivatives = []
    for dx, dy in shell.OFFSETS:
        value, derivative = _independent_sample(model, s+dx, dy, q)
        displacements.append(value)
        derivatives.append(derivative)
    values = np.asarray(displacements)
    gradients = np.asarray(derivatives)
    offsets_x = np.asarray(shell.OFFSETS)[:, 0]
    return (np.array((0., np.mean(values),
                      offsets_x@values/shell.YAW_DENOMINATOR)),
            np.array((0., np.mean(gradients),
                      offsets_x@gradients/shell.YAW_DENOMINATOR)))


@pytest.mark.parametrize("topology", ("Q4", "CST-CB"))
def test_manufactured_nonaffine_pose_hosts_and_branch_derivatives(topology):
    model = shell.panel(4, 16, topology)
    q = _nodal(model)
    breaks = line.overlay(model, 8, 4)
    for left, right in zip(breaks[:-1], breaks[1:]):
        s = .5*(left+right)
        expected, derivative = _independent_pose(model, s, q)
        np.testing.assert_allclose(shell.pose(model, s)@q, expected,
                                   rtol=2e-11, atol=1e-13)
        step = min(1e-6, (right-left)*.1)
        centered = (shell.pose(model, s+step)@q-
                    shell.pose(model, s-step)@q)/(2*step)
        np.testing.assert_allclose(centered, derivative,
                                   rtol=2e-8, atol=2e-12)

    # Evaluate both one-sided limits at every host/diagonal crossing. A
    # piecewise derivative may jump, but the interpolated field must be C0.
    for s in breaks[1:-1]:
        epsilon = min(1e-8, .1*float(np.min(np.diff(breaks))))
        minus = shell.pose(model, s-epsilon)@q
        plus = shell.pose(model, s+epsilon)@q
        at = shell.pose(model, s)@q
        np.testing.assert_allclose(minus, at, rtol=0, atol=2e-10)
        np.testing.assert_allclose(plus, at, rtol=0, atol=2e-10)


@pytest.mark.parametrize("topology", ("Q4", "CST-CB"))
def test_affine_exactness_and_nonaffine_refinement(topology):
    errors = []
    energies = []
    for ns, ny in ((2, 8), (4, 16), (8, 32)):
        model = shell.panel(ns, ny, topology)
        x, y = model.nodes.T
        affine = np.zeros(model.dof_count)
        affine[::2] = .2e-3 - .3e-3*y
        affine[1::2] = -.1e-3 + .3e-3*x + .07e-3*x - .02e-3*y
        for s in (.13, .37, .67, .93):
            actual = shell.pose(model, s)@affine
            # Four exact samples, independently reduced by centered fit.
            samples = np.array([(-.1e-3+.3e-3*(s+dx)+.07e-3*(s+dx)-.02e-3*dy)
                                for dx, dy in shell.OFFSETS])
            expected_y = np.mean(samples)
            expected_x = np.mean([.2e-3-.3e-3*dy for _, dy in shell.OFFSETS])
            expected_yaw = (.3e-3*sum(dy*dy for _, dy in shell.OFFSETS)+
                            (.3e-3+.07e-3)*sum(dx*dx for dx, _ in shell.OFFSETS)) / shell.YAW_DENOMINATOR
            np.testing.assert_allclose(actual, (expected_x, expected_y, expected_yaw),
                                       rtol=0, atol=2e-14)
        q = _nodal(model)
        energies.append(float(q@(shell.stiffness(model)@q)))
        differences = []
        for s in np.linspace(.037, .963, 53):
            values = np.array([_field(s+dx, dy) for dx,dy in shell.OFFSETS])
            continuous = np.array((0., np.mean(values),
                                   np.asarray(shell.OFFSETS)[:,0]@values/shell.YAW_DENOMINATOR))
            differences.append(np.linalg.norm(shell.pose(model, float(s))@q-continuous))
        errors.append(float(np.sqrt(np.mean(np.square(differences)))))
    assert all(np.isfinite(energies)) and min(energies) > 0
    assert errors[0] > errors[1] > errors[2] > 0
    assert errors[2] < .3*errors[0]


@pytest.mark.parametrize("ny", (16,32,64))
@pytest.mark.parametrize("ns", (64,128))
@pytest.mark.parametrize("topology", ("Q4", "CST-CB"))
def test_hand_located_host_crossings_at_loaded_resolutions(topology,ns,ny):
    """No overlay-derived breakpoint is used for these one-sided checks."""
    model = shell.panel(ns,ny,topology)
    q = _nodal(model)
    for dx,dy in shell.OFFSETS:
        j = int(np.floor((dy+.5)*ny))
        fraction = (dy+.5)*ny-j
        assert 0 < fraction < 1
        for i in (int(.75*ns),ns,int(1.25*ns)):
            crossings = (0.,) if topology == "Q4" else (
                0., (1-fraction if (i+j)%2 else fraction))
            for crossing in crossings:
                # crossing=0 is an x-grid boundary; the second, if present,
                # is the diagonal defined by the documented checkerboard.
                s = -.5+(i+crossing)/ns-dx
                assert 0 < s < 1
                step = min(1e-7, .01*min(fraction,1-fraction)/ns)
                left = shell.pose(model,s-step)@q
                at = shell.pose(model,s)@q
                right = shell.pose(model,s+step)@q
                expected_left, slope_left = _independent_pose(model,s-step/2,q)
                expected_right, slope_right = _independent_pose(model,s+step/2,q)
                np.testing.assert_allclose((left+at)/2,expected_left,
                                           rtol=0,atol=2e-12)
                np.testing.assert_allclose((right+at)/2,expected_right,
                                           rtol=0,atol=2e-12)
                np.testing.assert_allclose((at-left)/step,slope_left,
                                           rtol=2e-6,atol=2e-9)
                np.testing.assert_allclose((right-at)/step,slope_right,
                                           rtol=2e-6,atol=2e-9)
                # The target host must change on the hand-computed boundary.
                host_left = shell.sample(model,s-step+dx,dy)[0]
                host_right = shell.sample(model,s+step+dx,dy)[0]
                assert host_left != host_right


@pytest.mark.parametrize("topology", ("Q4", "CST-CB"))
def test_manufactured_port_adjoint_work(topology):
    model = shell.panel(4, 16, topology)
    q = _nodal(model)
    cs, _, _ = line.coupling(model, 8, 4, "P1")
    lam = np.linspace(-350., 550., cs.shape[0])
    rng = np.random.default_rng(203)
    direction = rng.normal(size=q.shape)*1e-5
    step = .01
    left = float(lam@(cs@(q-step*direction)))
    right = float(lam@(cs@(q+step*direction)))
    np.testing.assert_allclose((right-left)/(2*step),
                               (cs.T@lam)@direction, rtol=1e-10, atol=1e-12)
