"""Independent scalar/structural controls for the bounded block inverse proof."""
from dataclasses import replace
from fractions import Fraction as Q

import numpy as np
import pytest
from scipy import sparse

from scripts import r8_bl5_sparse_factor_block_dev as proof


def exact_inverse(lower):
    n = len(lower)
    answer = [[Q(0) for _ in range(n)] for _ in range(n)]
    for column in range(n):
        for row in range(n):
            answer[row][column] = (Q(int(row == column))-
                sum(lower[row][k]*answer[k][column] for k in range(row)))/lower[row][row]
    return answer


def csr(result, prefix):
    return sparse.csr_matrix((result[prefix+'_data'], result[prefix+'_indices'],
                             result[prefix+'_indptr']), shape=result[prefix+'_shape'])


@pytest.mark.parametrize('n', (3, 18, 21))
def test_signed_nonunit_factor_bound_contains_exact_fraction_inverse(n):
    factor = np.diag([(-1.)**i*(1.+(i % 3)/2.) for i in range(n)])
    for row in range(1, n):
        factor[row, row-1] = (-1.)**row*.125
        if row > 1:
            factor[row, row-2] = .0625
    result = proof.certify_block_inverse(sparse.csr_matrix(factor))
    assert result['finite_bound'] and result['status'] == 'FINITE_FACTOR_INVERSE_BOUND'
    inverse = exact_inverse([[Q(float(x)) for x in row] for row in factor])
    one = max(sum(abs(inverse[i][j]) for i in range(n)) for j in range(n))
    inf = max(sum(abs(x) for x in row) for row in inverse)
    # The proof's induced1/inf majorants also bound their product independently.
    assert Q(result['inverse_two_upper'])**2 >= one*inf
    assert 0 < Q(result['mu_lower']) <= 1/(one*inf)
    assert Q(result['inverse_two_square_upper']) >= Q(result['inverse_two_upper'])**2
    assert Q(result['mu_lower']) <= 1/Q(result['inverse_two_square_upper'])
    assert np.max(np.diff(result['block_bounds'], axis=1)) <= 18
    assert result['comparison_forward_completed'] == n
    assert result['comparison_transpose_completed'] == n
    w, g = csr(result, 'w').toarray(), csr(result, 'ghat').toarray()
    squared_error = Q(0)
    for row in range(n):
        for column in range(n):
            exact = sum(Q(float(w[row, k]))*Q(float(factor[k, column])) for k in range(n))
            squared_error += (exact-Q(float(g[row, column])))**2
    assert Q(result['eg_upper'])**2 >= squared_error
    assert Q(result['eta_upper']) >= Q(result['ghat_inverse_two_upper'])*Q(result['eg_upper'])
    assert Q(result['neumann_denominator_lower']) <= 1-Q(result['eta_upper'])


def test_two_blocks_cancel_allones_growth_without_assuming_candidate_accuracy():
    n = 36
    factor = sparse.csr_matrix(np.tril(np.ones((n, n))))
    result = proof.certify_block_inverse(factor)
    assert result['finite_bound']
    # Exact inverse is bidiagonal (1,-1), so ||inverse||1=||inverse||inf=2.
    assert Q(result['inverse_two_upper'])**2 >= 4
    assert result['inverse_two_upper'] < 100.
    # Original absolute comparison recurrence has endpoint 2^(n-1).
    assert result['inverse_two_upper'] < 2**(n-1)/1e6
    np.testing.assert_array_equal(result['block_bounds'], ((0, 18), (18, 36)))
    g = csr(result, 'ghat')
    assert g.nnz < result['product_symbolic_nnz']
    assert result['product_symbolic_nnz'] == n*(n+1)//2
    assert result['eg_upper'] > 0.


@pytest.mark.parametrize('factor', (
    sparse.csr_matrix((0, 0)), sparse.csr_matrix((2, 3)),
    sparse.csr_matrix([[1., 2.], [0., 1.]]),
    sparse.csr_matrix(([1., 0., 1.], [0, 1, 1], [0, 2, 3]), shape=(2, 2)),
    sparse.csr_matrix(([1., 1., 1.], [0, 0, 1], [0, 2, 3]), shape=(2, 2)),
    sparse.csr_matrix([[1., 0.], [1., 0.]]),
    sparse.csr_matrix([[1., 0.], [1., np.inf]]),
    sparse.csr_matrix([[1., 0.], [1., np.nan]]),
))
def test_invalid_factor_is_rejected_without_repair(factor):
    with pytest.raises(ValueError):
        proof.certify_block_inverse(factor)


@pytest.mark.parametrize('size', (True, False, 1, 17, 19, 18., np.int64(18), None))
def test_only_plain_eighteen_is_admitted(size):
    with pytest.raises(ValueError, match='plain integer'):
        proof.certify_block_inverse(sparse.eye(1, format='csr'), block_size=size)


def test_preallocation_workspace_refusal_precedes_local_solve(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('local native solve must not precede workspace guard')
    monkeypatch.setattr(proof.linalg, 'solve_triangular', forbidden)
    result = proof.certify_block_inverse(sparse.eye(18, format='csr'),
        budget=replace(proof.IntervalBudget(), max_workspace_bytes=10000))
    assert not result['finite_bound'] and result['hold_kind'] == 'RESOURCE_REFUSAL'
    assert result['workspace_estimate_bytes'] > 10000


def test_complete_cancelled_product_work_guard_precedes_sparse_product(monkeypatch):
    def forbidden(*args):
        pytest.fail('native WF product must not precede complete work guard')
    monkeypatch.setattr(proof, 'sparse_product', forbidden)
    result = proof.certify_block_inverse(sparse.csr_matrix(np.tril(np.ones((18, 18)))),
        budget=replace(proof.IntervalBudget(), max_updates=1))
    assert result['hold_kind'] == 'RESOURCE_REFUSAL'
    assert result['product_symbolic_updates'] > 1
    assert 'w_data' in result


def test_complete_crossblock_output_union_is_guarded_before_product(monkeypatch):
    factor = np.eye(36)+np.diag(np.ones(35), -1)
    factor[18, 17] = 0.
    factor[18, :18] = 1.
    def forbidden(*args):
        pytest.fail('native product must not precede complete symbolic output guard')
    monkeypatch.setattr(proof, 'sparse_product', forbidden)
    result = proof.certify_block_inverse(sparse.csr_matrix(factor),
        budget=replace(proof.IntervalBudget(), max_pattern_nnz=342))
    assert result['hold_kind'] == 'RESOURCE_REFUSAL'
    assert result['local_candidate_nnz_limit'] == 342
    assert result['product_symbolic_nnz'] > 342
    assert 'symbolic output' in result['hold_reason']


def test_default_order_refusal_and_explicit_budget_are_separate():
    factor = sparse.eye(2401, format='csr')
    assert proof.certify_block_inverse(factor)['hold_kind'] == 'RESOURCE_REFUSAL'
    result = proof.certify_block_inverse(factor,
        budget=replace(proof.IntervalBudget(), max_order=25068))
    assert result['finite_bound'] and result['order'] == 2401
    assert result['budget']['max_order'] == 25068
    assert proof.IntervalBudget().max_order == 2400


def test_non_neumann_error_retains_raw_candidate_and_product(monkeypatch):
    original = proof.sparse_product
    def deliberately_loose(a, b):
        value, error = original(a, b)
        # An honest looser enclosure: cannot improve any certificate.
        return value, max(2., error)
    monkeypatch.setattr(proof, 'sparse_product', deliberately_loose)
    result = proof.certify_block_inverse(sparse.eye(2, format='csr'))
    assert not result['finite_bound'] and result['hold_kind'] == 'NON_NEUMANN_MARGIN'
    assert result['eta_upper'] >= 1. and result['neumann_denominator_lower'] <= 0.
    assert all(name in result for name in ('w_data', 'ghat_data', 'eg_upper',
        'comparison_forward_upper', 'comparison_transpose_upper'))
    assert 'inverse_two_upper' not in result and 'negative' not in result


def test_scaled_approximate_local_candidate_is_verified_as_stored(monkeypatch):
    original = proof.linalg.solve_triangular
    def scaled(*args, **kwargs):
        return .5*original(*args, **kwargs)
    monkeypatch.setattr(proof.linalg, 'solve_triangular', scaled)
    result = proof.certify_block_inverse(sparse.eye(3, format='csr'))
    assert result['finite_bound'] and 1. <= result['inverse_two_upper'] < 1.01
    np.testing.assert_array_equal(csr(result, 'w').diagonal(), np.full(3, .5))
    np.testing.assert_array_equal(csr(result, 'ghat').diagonal(), np.full(3, .5))


def test_upper_product_entry_is_preserved_and_rejected(monkeypatch):
    original = proof.sparse_product
    def perturbed(a, b):
        value, error = original(a, b)
        value = value.tolil()
        value[0, 1] = .25
        # This honestly encloses the deliberately perturbed product too.
        return value.tocsr(), float(proof.up(error+.25))
    monkeypatch.setattr(proof, 'sparse_product', perturbed)
    with pytest.raises(ValueError, match='no ignored upper'):
        proof.certify_block_inverse(sparse.eye(2, format='csr'))


def test_arithmetic_refusal_retains_local_candidate(monkeypatch):
    def arithmetic(*args):
        raise ArithmeticError('injected product arithmetic refusal')
    monkeypatch.setattr(proof, 'sparse_product', arithmetic)
    result = proof.certify_block_inverse(sparse.eye(2, format='csr'))
    assert result['hold_kind'] == 'ARITHMETIC_DOMAIN' and not result['finite_bound']
    assert 'w_data' in result and 'product_symbolic_nnz' in result


@pytest.mark.parametrize('error_type', (MemoryError, RuntimeError, ZeroDivisionError))
def test_memory_and_programming_errors_propagate_exact_object(monkeypatch, error_type):
    error = error_type('injected implementation defect')
    def fail(*args):
        raise error
    monkeypatch.setattr(proof, 'sparse_product', fail)
    with pytest.raises(error_type) as caught:
        proof.certify_block_inverse(sparse.eye(1, format='csr'))
    assert caught.value is error


def test_factor_and_saved_candidate_buffers_are_owned():
    factor = sparse.csr_matrix([[2., 0.], [.5, -1.]])
    original = tuple(x.copy() for x in (factor.data, factor.indices, factor.indptr))
    factor.data.flags.writeable = False
    result = proof.certify_block_inverse(factor)
    assert result['finite_bound']
    for actual, expected in zip((factor.data, factor.indices, factor.indptr), original):
        np.testing.assert_array_equal(actual, expected)
    saved_g = result['ghat_data'].copy()
    result['w_data'][:] = 123.
    result['comparison_forward_upper'][:] = -1.
    np.testing.assert_array_equal(result['ghat_data'], saved_g)
    assert np.all(result['comparison_transpose_upper'] > 0.)
    factor.data.flags.writeable = True
    factor.data[:] = 17.
    np.testing.assert_array_equal(result['ghat_data'], saved_g)
