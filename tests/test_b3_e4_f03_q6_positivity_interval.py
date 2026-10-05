"""Bounded small-matrix checks for the experimental Q6 positivity route."""

from fractions import Fraction

import numpy as np
import pytest
from scipy import sparse

from scripts._b3_e4_f03_q6_positivity_interval import (
    PositivityIntervalBudget, _residual_norms, certify_positive,
)
from scripts._b3_e4_f03_sparse_certificate import SparseBudget


def _budget(n=2):
    return PositivityIntervalBudget(
        SparseBudget(n, n*n, n, 100_000), n**3, 2*n*n+n**3)


def _blocks(inverse):
    yield 0, np.array(inverse, dtype=np.float64, order="C", copy=True)


def test_positive_congruence_and_owned_inverse_candidate():
    k = sparse.csr_matrix(np.array([[4., 1.], [1., 3.]]))
    l = sparse.csr_matrix(np.array([[1., 0.], [.25, 1.]]))
    inverse = np.array([[1., 0.], [-.25, 1.]])
    result = certify_positive(
        k, l, np.array([4., 2.75]), (0, 1), _blocks(inverse),
        budget=_budget())
    assert result["status"] == "POSITIVE_QUADRATIC_FORM"
    assert result["inverse"]["inverse_columns"] == 2
    assert result["residual_pattern_nnz"] == 4
    assert result["strict_margin_squared_numerator"] > 0


def test_original_skew_is_in_residual_not_silently_symmetrized():
    k = sparse.csr_matrix(np.array([[4., 1.001], [.999, 3.]]))
    l = sparse.csr_matrix(np.array([[1., 0.], [.25, 1.]]))
    inverse = np.array([[1., 0.], [-.25, 1.]])
    result = certify_positive(
        k, l, np.array([4., 2.75]), (0, 1), _blocks(inverse),
        budget=_budget())
    assert result["status"] == "POSITIVE_QUADRATIC_FORM"
    assert result["residual_entry_upper"] > .0009


def test_missing_product_edge_and_indefinite_input_hold():
    k = sparse.csr_matrix(np.array([[1., 2.], [2., 1.]]))
    l = sparse.eye(2, format="csr")
    result = certify_positive(
        k, l, np.ones(2), (0, 1), _blocks(np.eye(2)),
        budget=_budget())
    assert result["status"] == "HOLD"
    assert result["residual_pattern_nnz"] == 4
    assert result["residual_entry_upper"] >= 2.


def test_bad_inverse_or_permutation_cannot_prove_positivity():
    k = sparse.eye(2, format="csr")
    l = sparse.eye(2, format="csr")
    result = certify_positive(
        k, l, np.ones(2), (0, 1), _blocks(np.zeros((2, 2))),
        budget=_budget())
    assert result["status"] == "HOLD"
    with pytest.raises(ValueError, match="permutation"):
        certify_positive(k, l, np.ones(2), (0, 0), _blocks(np.eye(2)),
                         budget=_budget())


def test_permuted_original_and_cancelled_product_are_covered():
    l = sparse.csr_matrix(np.array([[1., 0., 0.],
                                    [1., 1., 0.],
                                    [1., -1., 1.]]))
    diagonal = np.ones(3)
    in_factor_order = (l @ l.T).toarray()
    # The (1, 2) product has two nonzero terms that cancel exactly.
    assert in_factor_order[1, 2] == 0.
    order = (2, 0, 1)
    original = np.empty_like(in_factor_order)
    original[np.ix_(order, order)] = in_factor_order
    k = sparse.csr_matrix(original)
    inverse = np.linalg.inv(l.toarray())
    result = certify_positive(k, l, diagonal, order, _blocks(inverse),
                              budget=_budget(3))
    assert result["status"] == "POSITIVE_QUADRATIC_FORM"
    assert result["residual_pattern_nnz"] >= k.nnz


def test_nonfinite_compiled_residual_cannot_be_accepted():
    l = sparse.csr_matrix(np.array([[1., 0.], [1.e308, 1.]]))
    k = sparse.eye(2, format="csr")
    pattern = sparse.csr_matrix(np.ones((2, 2)))
    with np.errstate(over="ignore", invalid="ignore"):
        rows, columns, maximum = _residual_norms(
            k.indptr, k.indices, k.data,
            l.indptr, l.indices, l.data, np.array([1.e308, 1.]),
            pattern.indptr, pattern.indices)
    assert not (np.isfinite(rows).all() and np.isfinite(columns).all() and
                np.isfinite(maximum))


def test_compiled_congruence_residual_encloses_exact_dyadic_oracle():
    rng = np.random.default_rng(2709)
    subnormal = np.nextafter(0., 1.)
    for _ in range(20):
        lower = np.tril(rng.normal(size=(3, 3)))
        np.fill_diagonal(lower, 1.)
        lower[2, 0] = rng.choice([-1., 1.])*subnormal
        diagonal = np.array([.125, 1.5, 2.**-700])
        target = rng.normal(size=(3, 3))
        target[0, 2] = -subnormal
        k = sparse.csr_matrix(target)
        l = sparse.csr_matrix(lower)
        pattern = sparse.csr_matrix(np.ones((3, 3)))
        rows, columns, maximum = _residual_norms(
            k.indptr, k.indices, k.data,
            l.indptr, l.indices, l.data, diagonal,
            pattern.indptr, pattern.indices)
        exact = [[abs(Fraction.from_float(float(target[i, j])) - sum(
            Fraction.from_float(float(lower[i, q])) *
            Fraction.from_float(float(diagonal[q])) *
            Fraction.from_float(float(lower[j, q])) for q in range(3)))
            for j in range(3)] for i in range(3)]
        assert all(Fraction.from_float(float(rows[i])) >= sum(exact[i])
                   for i in range(3))
        assert all(Fraction.from_float(float(columns[j])) >=
                   sum(exact[i][j] for i in range(3)) for j in range(3))
        assert Fraction.from_float(float(maximum)) >= max(map(max, exact))
