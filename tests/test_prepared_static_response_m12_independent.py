"""Independent exact scalar/closed-form controls, not native qualification."""
import gc
from fractions import Fraction as F
from itertools import product

import numpy as np
import pytest
from scipy import sparse
from scipy.sparse.linalg import splu

from prepared_static_response_m12_resident import ResidentSolveBound, triangular_center_error
from prepared_static_response_m10_bounds import contains, UNIT, TINY


@pytest.mark.parametrize('lower', [True, False])
def test_closed_form_cancellation_and_residual_relation_adversaries(lower):
    # Exact inverse has an identically zero corner despite nonzero factors.
    a = [[F(1), F(0), F(0)], [F(2), F(1), F(0)], [F(4), F(2), F(1)]]
    if not lower:
        a = [list(row) for row in zip(*a)]
    b = [F(1), F(3), F(8)]
    def oracle(v):
        if lower:
            return [v[0], v[1]-2*v[0], v[2]-2*v[1]]
        return [v[0]-2*v[1], v[1]-2*v[2], v[2]]
    center, error = triangular_center_error(a, b, [F(0)]*3, lower)
    assert center == oracle(b)
    g = 8*UNIT/(1-8*UNIT)
    for signs in product((-1, 1), repeat=3):
        residual = [F(s)*UNIT for s in signs]
        q = oracle([x+r for x, r in zip(b, residual)])
        for i in range(3):
            permitted = g*(sum(abs(x)*abs(y) for x, y in zip(a[i], q))+abs(b[i]))
            assert abs(residual[i]) <= permitted
            assert abs(q[i]-center[i]) <= error[i]


def test_scalar_division_underflow_requires_diagonal_scaled_allowance():
    diagonal = F(float(1e308)); rhs = F(float(1e-20))
    center, error = triangular_center_error([[diagonal]], [rhs], [F(0)], False)
    assert center[0] == rhs/diagonal
    assert abs(center[0]) <= error[0]  # represented quotient can be zero
    assert rhs > 4*TINY


def test_factor_snapshot_outlives_source_and_has_no_numpy_aliases():
    a = sparse.csc_matrix([[0., 2.], [4., 1.]])
    solver = splu(a); scaling = np.array([.5, 2.]); rhs = np.array([1., 3.])
    bound = ResidentSolveBound(solver, a, scaling)
    intervals = bound.enclose(rhs)
    expected = scaling*solver.solve(scaling*rhs)
    # All future calculations use owned factor data, not live native containers.
    a.data[:] = 0.; scaling[:] = 100.
    solver.perm_r[:] = 0; solver.perm_c[:] = 0
    del solver
    gc.collect()
    assert intervals == bound.enclose(rhs)
    assert all(contains(i, x) for i, x in zip(intervals, expected))


def test_negative_signed_loads_and_nontrivial_external_scaling():
    a = sparse.csc_matrix([[8., -2.], [-2., 4.]])
    solver = splu(a); d = np.array([.25, 8.]); rhs = np.array([-3., 2.])
    bound = ResidentSolveBound(solver, a, d)
    intervals = bound.enclose(rhs)
    # Compute only after the enclosure, using the same represented scaling.
    expected = d*solver.solve(d*rhs)
    assert all(contains(i, x) for i, x in zip(intervals, expected))
