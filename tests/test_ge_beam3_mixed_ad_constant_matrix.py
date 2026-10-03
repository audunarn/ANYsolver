"""Explicit constant matrix products retain the generic Jet work and ownership."""
import warnings
from collections.abc import Sequence

import numpy as np
import pytest

from anysolver._ge_beam3_mixed_ad import (
    Jet2, constant_matrix, matmul, matmul_constant_right,
)
from test_ge_beam3_mixed_ad_scalars import _same


@pytest.mark.parametrize("size", (0, 3, 18, 24))
@pytest.mark.parametrize("policy", ("ignore", "raise"))
def test_ordered_reference_product_and_errors(size, policy):
    rng = np.random.default_rng(721)
    left = [[Jet2(v, rng.normal(size=size), rng.normal(size=(size, size)))
             for v in (0., -0., 2.)],
            [Jet2(v, rng.normal(size=size), rng.normal(size=(size, size)))
             for v in (-3., 1., .5)]]
    for right in (np.eye(3), np.zeros((3, 2)),
                  np.array([[0., -0.], [-2., 4.], [.75, -1.]]),
                  rng.normal(size=(3, 2)),
                  np.full((3, 2), np.nan), np.full((3, 2), np.inf),
                  np.full((3, 2), 1e308)):
        with warnings.catch_warnings(), np.errstate(all=policy):
            warnings.simplefilter("ignore", RuntimeWarning)
            try:
                expected = matmul(left, constant_matrix(right, size))
            except FloatingPointError as error:
                with pytest.raises(type(error)) as actual:
                    matmul_constant_right(left, right)
                assert actual.value.args == error.args
            else:
                actual = matmul_constant_right(left, right)
                for ar, er in zip(actual, expected):
                    for a, e in zip(ar, er):
                        _same(a, e)


def test_reference_coefficients_and_derivatives_are_not_borrowed():
    g = np.arange(8.)[::2]
    h = np.arange(32.).reshape(4, 8)[:, ::2]
    g.setflags(write=False); h.setflags(write=False)
    left = [[Jet2(2., g, h), Jet2(-3., g, h)]]
    right = np.array(((0., 2.), (-3., 1.)))
    actual = matmul_constant_right(left, right)
    expected = matmul(left, constant_matrix(right, 4))
    right[:] = 907.
    for a, e in zip(actual[0], expected[0]):
        _same(a, e)
        assert a.gradient.flags.owndata and a.hessian.flags.owndata
        assert not np.shares_memory(a.gradient, g)
        assert not np.shares_memory(a.hessian, h)
    before = actual[0][1].gradient.copy()
    actual[0][0].gradient[:] = 98.
    actual[0][0].hessian[:] = 99.
    np.testing.assert_array_equal(actual[0][1].gradient, before)
    assert g[0] == 0. and h[0, 0] == 0.


def test_subclasses_malformed_layouts_and_shapes_keep_generic_behavior():
    class Derived(Jet2):
        def _coerce(self, other):
            return other if isinstance(other, Jet2) else Jet2.constant(float(other)+1., self.gradient.size)

    for cls, dtype in ((Derived, np.float64), (Jet2, np.float32)):
        left = [[cls(2., np.ones(3, dtype=dtype), np.eye(3, dtype=dtype))]]
        _same(matmul_constant_right(left, [[3.]])[0][0],
              matmul(left, constant_matrix([[3.]], 3))[0][0])
    left = [[Jet2(2., np.ones(3), np.eye(3))]]
    for right in (1., [1., 2.], np.empty((0, 2)), np.ones((2, 1))):
        try:
            matmul(left, constant_matrix(right, 3))
        except (IndexError, ValueError) as error:
            with pytest.raises(type(error)) as actual:
                matmul_constant_right(left, right)
            assert error.args == actual.value.args
        else:
            raise AssertionError("fixture must exercise generic shape failure")
    bad = [[Jet2(2., np.ones((2, 2)), np.ones((4, 4)))]]
    with pytest.raises(ValueError):
        matmul_constant_right(bad, [[3.]])


def test_custom_sequences_retain_integer_indexed_generic_order():
    class IntegerRow(Sequence):
        def __init__(self, entries):
            self.entries = entries
        def __len__(self):
            return len(self.entries)
        def __getitem__(self, index):
            if isinstance(index, slice):
                raise TypeError("integer indexing only")
            return self.entries[index]

    class ReversedIterator(IntegerRow):
        def __iter__(self):
            return iter(reversed(self.entries))

    a = Jet2(2., np.ones(3), np.eye(3))
    b = Jet2(-3., np.arange(3.), -np.eye(3))
    right = [[4.]]
    for left in ([IntegerRow([a]), IntegerRow([b])],
                 ReversedIterator([[a], [b]])):
        actual = matmul_constant_right(left, right)
        expected = matmul(left, constant_matrix(right, 3))
        for ar, er in zip(actual, expected):
            _same(ar[0], er[0])
