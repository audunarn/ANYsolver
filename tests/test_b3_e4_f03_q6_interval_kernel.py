"""Bounded parity checks for the unregistered compiled interval-product pilot."""

import numpy as np
from fractions import Fraction
from scipy import sparse
import pytest

from scripts._b3_e4_f03_q6_interval_kernel import compiled_product_bounds
from scripts._b3_e4_f03_sparse_certificate import (
    SparseBudget, _product_bounds, certificate_a,
)


def test_compiled_interval_product_matches_scalar_oracle_bitwise():
    rng = np.random.default_rng(20260924)
    for n, width in ((1, 1), (7, 4), (31, 3)):
        matrix = sparse.random(n, n, density=.35, format="csr",
                               random_state=rng, data_rvs=rng.standard_normal)
        matrix.sum_duplicates()
        matrix.sort_indices()
        block = rng.normal(size=(n, width))
        if n > 1:
            block[0] = 0.
            matrix.data[0] = -0.
        expected = _product_bounds(matrix, block)
        observed = compiled_product_bounds(matrix, block)
        for old, new in zip(expected, observed):
            assert np.array_equal(old.view(np.uint64), new.view(np.uint64))


def test_compiled_full_certificate_matches_scalar_small_case():
    h = sparse.csr_matrix(np.array([[2., -.25], [-.25, 3.]]))
    inverse = np.linalg.inv(h.toarray())
    budget = SparseBudget(4, 16, 2, 1024*1024)

    def blocks():
        yield 0, np.array(inverse, dtype=np.float64)

    original = certificate_a(h, blocks(), budget, b=np.array([1., -2.]),
                             z=inverse @ np.array([1., -2.]))
    compiled = certificate_a(h, blocks(), budget, b=np.array([1., -2.]),
                             z=inverse @ np.array([1., -2.]),
                             interval_kernel="compiled_experimental")
    assert original["status"] == compiled["status"] == "CERTIFIED_WITHIN_LIMIT"
    assert {k: v for k, v in original.items() if k != "interval_kernel"} == {
        k: v for k, v in compiled.items() if k != "interval_kernel"}


def test_subnormal_cancellation_and_mixed_scale_bounds_exact_products():
    tiny = np.nextafter(0., np.inf)
    h = sparse.csr_matrix(np.array([
        [tiny, 1., -1., -tiny],
        [1e150, -1e150, 3., 0.],
        [1e-150, 1e-150, -2e-150, tiny],
        [0., 0., tiny, -tiny],
    ]))
    block = np.array([[1., tiny], [1., -1.], [1., 1.], [1., 0.]])
    scalar = _product_bounds(h, block)
    compiled = compiled_product_bounds(h, block)
    for old, new in zip(scalar, compiled):
        assert np.array_equal(old.view(np.uint64), new.view(np.uint64))
    low, high = compiled
    for row in range(h.shape[0]):
        for channel in range(block.shape[1]):
            exact = sum((Fraction.from_float(float(h[row, col])) *
                         Fraction.from_float(float(block[col, channel]))
                         for col in range(h.shape[1])), Fraction(0))
            assert Fraction.from_float(float(low[row, channel])) <= exact
            assert exact <= Fraction.from_float(float(high[row, channel]))


def test_compiled_interval_product_rejects_overflow():
    matrix = sparse.csr_matrix(np.array([[1e308]]))
    with pytest.raises(ArithmeticError, match="nonfinite"):
        compiled_product_bounds(matrix, np.array([[2.]]))
