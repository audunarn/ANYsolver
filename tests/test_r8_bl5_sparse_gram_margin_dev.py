"""Independent sign/completeness controls for the extra-shift Gram argument."""
from dataclasses import replace

import numpy as np
import pytest
from scipy import sparse

from scripts import r8_bl5_sparse_gram_margin_dev as proof


def test_gram_certificate_needs_no_factor_inverse_or_positive_diagonal():
    # Singular, nontriangular F still gives a complete positive target bound.
    f = sparse.csr_matrix([[0., 1.], [0., 0.]])
    a = sparse.diags([1.125, .125], format='csr')
    result = proof.certify_gram_margin(a, f, [0, 1], target_shift=.0625, producer_shift=.125)
    assert result['positive'] and result['margin_lower'] > .0624
    assert 'mu_lower' not in result and 'inverse_inf_upper' not in result


def test_complete_symmetric_permutation_and_mutation_isolation():
    a = sparse.diags([4.125, 1.125], format='csr')
    f = sparse.diags([1., 2.], format='csr')
    before_a, before_f = a.data.copy(), f.data.copy()
    result = proof.certify_gram_margin(a, f, [1, 0], target_shift=.0625, producer_shift=.125)
    assert result['positive']
    np.testing.assert_array_equal(a.data, before_a)
    np.testing.assert_array_equal(f.data, before_f)
    result['shifted_diagonal_rounded'][:] = -1.
    np.testing.assert_array_equal(a.data, before_a)


@pytest.mark.parametrize('value', [.0625, .06249999999999999, -.125])
def test_zero_or_negative_shifted_mode_cannot_be_accepted(value):
    result = proof.certify_gram_margin(sparse.diags([1.125, value], format='csr'),
        sparse.diags([1., 0.], format='csr'), [0, 1], target_shift=.0625, producer_shift=.125)
    assert not result['positive'] and result['hold_kind'] == 'INSUFFICIENT_MARGIN'


def test_cancellation_entries_count_before_product_allocation(monkeypatch):
    f = sparse.csr_matrix([[1., 0., 0.], [1., 1., 0.], [1., -1., 1.]])
    monkeypatch.setattr(proof, 'sparse_product', lambda *a: pytest.fail('allocated before guard'))
    result = proof.certify_gram_margin(sparse.eye(3, format='csr'), f, [0, 1, 2],
        target_shift=0., producer_shift=.125,
        budget=replace(proof.IntervalBudget(), max_pattern_nnz=8))
    assert result['hold_kind'] == 'RESOURCE_REFUSAL'
    assert result['product_symbolic_nnz'] == 9


def test_underflow_is_not_silently_dropped():
    result = proof.certify_gram_margin(sparse.eye(2, format='csr'),
        sparse.csr_matrix([[1., 0.], [1e-200, 1.]]), [0, 1],
        target_shift=0., producer_shift=.125)
    assert not result['positive'] and result['hold_kind'] == 'ARITHMETIC_DOMAIN'


@pytest.mark.parametrize('permutation', [[0, 0], [False, 1], [np.int64(0), 1]])
def test_incomplete_or_nonplain_permutation_rejected(permutation):
    with pytest.raises(ValueError, match='plain-int'):
        proof.certify_gram_margin(sparse.eye(2, format='csr'), sparse.eye(2, format='csr'),
            permutation, target_shift=0., producer_shift=.125)


def test_skew_matrix_and_invalid_shift_are_not_repaired():
    with pytest.raises(ValueError, match='symmetric'):
        proof.certify_gram_margin(sparse.csr_matrix([[1., .1], [.2, 1.]]),
            sparse.eye(2, format='csr'), [0, 1], target_shift=0., producer_shift=.125)
    with pytest.raises(ValueError, match='strictly exceed'):
        proof.certify_gram_margin(sparse.eye(1, format='csr'), sparse.eye(1, format='csr'),
            [0], target_shift=.125, producer_shift=.125)


@pytest.mark.parametrize('error_type', [RuntimeError, MemoryError])
def test_unexpected_errors_propagate(error_type, monkeypatch):
    def fail(*a):
        raise error_type('injected')
    monkeypatch.setattr(proof, 'sparse_product', fail)
    with pytest.raises(error_type, match='injected'):
        proof.certify_gram_margin(sparse.eye(1, format='csr'), sparse.eye(1, format='csr'),
            [0], target_shift=0., producer_shift=.125)
