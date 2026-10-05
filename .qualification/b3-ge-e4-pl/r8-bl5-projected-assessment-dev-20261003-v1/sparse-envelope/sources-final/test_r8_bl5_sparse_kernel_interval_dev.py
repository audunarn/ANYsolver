"""Adversarial exact small controls for the development sparse proof primitive."""
from fractions import Fraction as F
from dataclasses import replace

import numpy as np
import pytest
from scipy import sparse
from scripts.r8_bl5_sparse_kernel_interval_dev import (
    IntervalBudget, certify_shifted_lower, dot_interval, factor_pattern,
    product_quotient_bounds,
    complete_symbolic_pattern,
    certify_decimal_lower,
)


def full_pattern(n):
    return sparse.csr_matrix(np.tril(np.ones((n, n))))


def exact_pivots(matrix, permutation, shift=0.):
    a = [[F(float(matrix[i, j])) for j in permutation] for i in permutation]
    for i in range(len(a)):
        a[i][i] -= F(float(shift))
    pivots = []
    for k in range(len(a)):
        d = a[k][k]; pivots.append(d)
        for i in range(k+1, len(a)):
            for j in range(k+1, len(a)):
                a[i][j] -= a[i][k] * a[k][j] / d
    return pivots


@pytest.mark.parametrize("reverse", (False, True))
@pytest.mark.parametrize("shift", (0., .125))
def test_every_interval_pivot_contains_exact_positive_schur(reverse, shift):
    b = np.array([[2., -.5, .25, 0.], [.5, 1., -.25, .5], [0., .25, 1.5, -.5], [0., 0., .5, 2.]])
    a = b @ b.T
    order = list(range(4))[::(-1 if reverse else 1)]
    result = certify_shifted_lower(sparse.csr_matrix(a), full_pattern(4), order, shift=shift)
    assert result["status"] == "POSITIVE_SHIFTED_LOWER_COMPLETION"
    for lo, hi, actual in zip(result["pivot_lower"], result["pivot_upper"], exact_pivots(a, order, shift)):
        assert F(float(lo)) <= actual <= F(float(hi))
    assert np.min(result["pivot_lower"]) > 0.


def test_positive_input_diagonal_does_not_accept_indefinite_form():
    a = np.array([[1., 2.], [2., 1.]])
    result = certify_shifted_lower(sparse.csr_matrix(a), full_pattern(2), [0, 1])
    assert result["status"] == "NONPOSITIVE_REPRESENTATIVE"
    assert result["stopping_pivot"] == 1 and result["pivot_upper"][-1] < 0.


def test_symbolic_closure_keeps_generated_zero_value_fill():
    a = sparse.csr_matrix([[4., 1., 1., 0.], [1., 4., 0., 1.],
                          [1., 0., 4., 1.], [0., 1., 1., 4.]])
    order = [2, 0, 3, 1]
    complete = complete_symbolic_pattern(a, order)
    result = certify_shifted_lower(a, complete, order)
    assert result['status'] == 'POSITIVE_SHIFTED_LOWER_COMPLETION'
    for lo, hi, exact in zip(result['pivot_lower'], result['pivot_upper'], exact_pivots(a.toarray(), order)):
        assert F(float(lo)) <= exact <= F(float(hi))
    with pytest.raises(ValueError, match='ceiling'):
        complete_symbolic_pattern(a, order, budget=replace(IntervalBudget(), max_updates=1))


@pytest.mark.parametrize('matrix,shift', ((np.array([[2., .1], [.1, 1.]]), .125),
    (np.array([[1., 1.], [1., np.nextafter(1., np.inf)]]), 0.)))
def test_directed_decimal_contains_fraction_exact_pivots(matrix, shift):
    order = [1, 0]
    result = certify_decimal_lower(sparse.csr_matrix(matrix), full_pattern(2), order, shift=shift)
    assert result['status'] == 'POSITIVE_SHIFTED_LOWER_COMPLETION'
    for lo, hi, exact in zip(result['pivot_lower'], result['pivot_upper'], exact_pivots(matrix, order, shift)):
        assert F(str(lo)) <= exact <= F(str(hi))
    assert all(F(str(v)) > 0 for v in result['pivot_lower'])


def test_directed_decimal_rejects_indefinite_and_missing_pattern():
    a = sparse.csr_matrix([[1., 2.], [2., 1.]])
    assert certify_decimal_lower(a, full_pattern(2), [0, 1])['status'] == 'NONPOSITIVE_REPRESENTATIVE'
    with pytest.raises(ValueError, match='missing initial'):
        certify_decimal_lower(a, sparse.eye(2, format='csr'), [0, 1])
    with pytest.raises(ValueError, match='ceiling|budget'):
        certify_decimal_lower(a, full_pattern(2), [0, 1], budget=replace(IntervalBudget(), max_updates=1, max_clique_entries=1, max_workspace_bytes=1))


def test_zero_crossing_is_unresolved_even_for_positive_matrix():
    a = np.array([[1., 1.], [1., np.nextafter(1., np.inf)]])
    result = certify_shifted_lower(sparse.csr_matrix(a), full_pattern(2), [0, 1])
    assert exact_pivots(a, [0, 1])[-1] > 0
    assert result["status"] == "HOLD_INTERVAL_PIVOT"


@pytest.mark.parametrize("matrix", (np.eye(3)*4 + np.ones((3, 3)), np.array([[4., 1., 1.], [1., 4., 0.], [1., 0., 4.]])))
def test_missing_input_or_generated_clique_is_rejected(matrix):
    candidate = sparse.csr_matrix(np.tril(matrix != 0).astype(float))
    if np.count_nonzero(matrix) == 9:
        candidate[2, 0] = 0.
        candidate.eliminate_zeros()
    with pytest.raises(ValueError, match="missing initial entry or elimination clique"):
        certify_shifted_lower(sparse.csr_matrix(matrix), candidate, [0, 1, 2])


def test_factor_permutation_is_only_a_pattern_candidate():
    a = sparse.diags([-.25*np.ones(7), np.ones(8), -.25*np.ones(7)], [-1, 0, 1], format="csr")
    fill, order = factor_pattern(a)
    result = certify_shifted_lower(a, fill, order)
    assert result["status"] == "POSITIVE_SHIFTED_LOWER_COMPLETION"
    dense = a.toarray()
    for lo, hi, exact in zip(result["pivot_lower"], result["pivot_upper"], exact_pivots(dense, order)):
        assert F(float(lo)) <= exact <= F(float(hi))


def test_product_division_encloses_sign_crossing_and_subnormal():
    alo, ahi = np.array([-2., -1e-300]), np.array([1., 1e-300])
    blo, bhi = np.array([-3., 1e-20]), np.array([4., 2e-20])
    lo, hi = product_quotient_bounds(alo, ahi, blo, bhi, .75, 1.25)
    for i in range(2):
        values = [F(float(a))*F(float(b))/F(float(d))
            for a in (alo[i], ahi[i]) for b in (blo[i], bhi[i]) for d in (.75, 1.25)]
        assert F(float(lo[i])) <= min(values) <= max(values) <= F(float(hi[i]))


def test_local_dot_interval_encloses_cancellation():
    a = np.array([[1e16, 1., -1e16], [-.25, .5, -.75]])
    b = np.array([[1., .25], [1., -.5], [1., .75]])
    lo, hi = dot_interval(a, b)
    for i in range(2):
        for j in range(2):
            exact = sum((F(float(a[i,k]))*F(float(b[k,j])) for k in range(3)), F(0))
            assert F(float(lo[i,j])) <= exact <= F(float(hi[i,j]))


def test_shift_and_budget_cannot_be_silently_relaxed():
    a = sparse.eye(3, format="csr")
    result = certify_shifted_lower(a, full_pattern(3), [0, 1, 2], shift=2.)
    assert result["status"] == "NONPOSITIVE_REPRESENTATIVE"
    with pytest.raises(ValueError, match="resource|ceiling"):
        certify_shifted_lower(a, full_pattern(3), [0, 1, 2], budget=replace(IntervalBudget(), max_updates=1))


def test_corrupt_sparse_buffer_and_nonpermutation_rejected():
    a = sparse.eye(3, format="csr")
    a.indices[0] = -1
    with pytest.raises(ValueError, match="structure"):
        certify_shifted_lower(a, full_pattern(3), [0, 1, 2])
    with pytest.raises(ValueError, match="permutation"):
        certify_shifted_lower(sparse.eye(3, format="csr"), full_pattern(3), [0, 0, 2])


def test_owned_inputs_not_modified():
    a = sparse.csr_matrix([[2., -.5], [-.5, 1.]])
    before = a.data.copy()
    result = certify_shifted_lower(a, full_pattern(2), [1, 0])
    result["pivot_lower"][:] = 0.
    np.testing.assert_array_equal(a.data, before)


def test_factor_producer_validates_sparse_buffers_before_backend():
    a = sparse.eye(3, format="csr")
    a.indices[0] = -1
    with pytest.raises(ValueError, match="structure"):
        factor_pattern(a)
