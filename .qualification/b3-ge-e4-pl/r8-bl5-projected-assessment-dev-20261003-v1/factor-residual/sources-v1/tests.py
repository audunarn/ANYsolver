"""Independent exact small residual/comparison controls, not qualification."""
from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy import sparse

from scripts import r8_bl5_sparse_factor_residual_dev as proof


def exact_inverse(lower):
    n = len(lower)
    inverse = [[F(0) for _ in range(n)] for _ in range(n)]
    for column in range(n):
        for row in range(n):
            numerator = F(int(row == column))-sum(lower[row][j]*inverse[j][column] for j in range(row))
            inverse[row][column] = numerator/lower[row][row]
    return inverse


def exact_factor_work(factor):
    return [[sum(factor[i][k]*factor[j][k] for k in range(len(factor)))
             for j in range(len(factor))] for i in range(len(factor))]


def test_signed_nonunit_lower_comparison_and_residual_bound_exact_fraction_target():
    factor = np.array(((2., 0., 0.), (-.25, -1.5, 0.), (.75, .1, 3.)))
    exact_f = [[F(float(value)) for value in row] for row in factor]
    work = exact_factor_work(exact_f)
    permutation, shift = [2, 0, 1], .125
    shifted = np.array([[float(value) for value in row] for row in work])+shift*np.eye(3)
    undo = np.argsort(permutation)
    matrix = shifted[undo][:, undo]
    result = proof.certify_factor_residual(sparse.csr_matrix(matrix), sparse.csr_matrix(factor), permutation, shift=shift)
    assert result['positive'] and result['status'] == 'POSITIVE_SHIFTED_FACTOR_RESIDUAL'
    inverse = exact_inverse(exact_f)
    inf_norm = max(sum(abs(value) for value in row) for row in inverse)
    one_norm = max(sum(abs(inverse[i][j]) for i in range(3)) for j in range(3))
    assert one_norm != inf_norm
    assert F(result['inverse_inf_upper']) >= inf_norm
    assert F(result['inverse_one_upper']) >= one_norm
    assert F(result['mu_lower']) <= 1/(one_norm*inf_norm)
    residual_squared = F(0)
    for i in range(3):
        for j in range(3):
            target = F(float(matrix[permutation[i], permutation[j]]))-F(shift)*int(i == j)
            residual_squared += (target-work[i][j])**2
    assert F(result['rho_upper'])**2 >= residual_squared
    assert 0 < F(result['margin_lower']) <= F(result['mu_lower'])-F(result['rho_upper'])
    for row in range(3):
        exact_diagonal = F(float(matrix[permutation[row], permutation[row]]))-F(shift)
        assert F(float(result['shift_diagonal_lower'][row])) <= exact_diagonal <= F(float(result['shift_diagonal_upper'][row]))
    # Check comparison recurrences independently in rational arithmetic, not
    # only the actual inverse norms; signed lower products become absolute.
    expected_forward = []
    for row in range(3):
        expected_forward.append((1+sum(abs(exact_f[row][j])*expected_forward[j] for j in range(row)))/abs(exact_f[row][row]))
    expected_backward = [F(0)]*3
    for row in range(2, -1, -1):
        expected_backward[row] = (1+sum(abs(exact_f[j][row])*expected_backward[j] for j in range(row+1, 3)))/abs(exact_f[row][row])
    assert all(F(float(actual)) >= exact for actual, exact in zip(result['comparison_forward_upper'], expected_forward))
    assert all(F(float(actual)) >= exact for actual, exact in zip(result['comparison_transpose_upper'], expected_backward))


@pytest.mark.parametrize('matrix,factor', ((np.zeros((2, 2)), np.eye(2)),
    (-np.eye(2), np.eye(2)), (np.eye(2), 10*np.eye(2))))
def test_zero_negative_or_bad_factor_margin_is_hold_without_negative_claim(matrix, factor):
    result = proof.certify_factor_residual(sparse.csr_matrix(matrix), sparse.csr_matrix(factor), [0, 1])
    assert not result['positive'] and result['status'] == 'HOLD_FACTOR_RESIDUAL'
    assert result['hold_kind'] == 'INSUFFICIENT_MARGIN' and result['margin_lower'] <= 0.
    assert 'negative' not in result and 'inertia' not in result


def test_wrong_complete_permutation_does_not_certify_factor_for_another_basis():
    matrix, factor = sparse.diags((16., 1., 4.), format='csr'), sparse.diags((1., 2., 4.), format='csr')
    assert proof.certify_factor_residual(matrix, factor, [1, 2, 0])['positive']
    assert not proof.certify_factor_residual(matrix, factor, [0, 1, 2])['positive']


def test_upper_entry_counterexample_is_rejected_instead_of_ignored():
    factor = sparse.csr_matrix([[1., 2.], [0., 1.]])
    matrix = sparse.csr_matrix([[4.7, 2.], [2., .7]])
    with pytest.raises(ValueError, match='no ignored upper'):
        proof.certify_factor_residual(matrix, factor, [0, 1])
    zero_upper = sparse.csr_matrix(([1., 0., 1.], [0, 1, 1], [0, 2, 3]), shape=(2, 2))
    with pytest.raises(ValueError, match='lower triangular'):
        proof.certify_factor_residual(sparse.eye(2, format='csr'), zero_upper, [0, 1])


@pytest.mark.parametrize('factor', (sparse.csr_matrix([[1., 0.], [.5, 0.]]),
    sparse.csr_matrix([[1., 0.], [.5, np.inf]]),
    sparse.csr_matrix(([1., 1., 1.], [0, 0, 1], [0, 2, 3]), shape=(2, 2))))
def test_missing_nonfinite_or_duplicate_factor_inputs_propagate_validation(factor):
    with pytest.raises(ValueError):
        proof.certify_factor_residual(sparse.eye(2, format='csr'), factor, [0, 1])


@pytest.mark.parametrize('permutation', ([0, 0], [0], [False, 1], [np.int64(0), 1], np.array([0, 1])))
def test_permutation_requires_complete_plain_integer_sequence(permutation):
    with pytest.raises(ValueError, match='plain-int'):
        proof.certify_factor_residual(sparse.eye(2, format='csr'), sparse.eye(2, format='csr'), permutation)


def test_exact_symmetry_and_square_shapes_are_not_repaired():
    with pytest.raises(ValueError, match='exact stored symmetric'):
        proof.certify_factor_residual(sparse.csr_matrix([[1., .1], [.2, 1.]]), sparse.eye(2, format='csr'), [0, 1])
    with pytest.raises(ValueError, match='square'):
        proof.certify_factor_residual(sparse.csr_matrix((1, 2)), sparse.eye(1, format='csr'), [0])


def test_cancellation_cannot_hide_complete_symbolic_product_resource_refusal(monkeypatch):
    # Exact product entry (1,2) cancels, but complete column0 has a 3x3 clique.
    factor = sparse.csr_matrix([[1., 0., 0.], [1., 1., 0.], [1., -1., 1.]])
    monkeypatch.setattr(proof, 'sparse_product', lambda *args: pytest.fail('product allocated before symbolic guard'))
    result = proof.certify_factor_residual(sparse.eye(3, format='csr'), factor, [0, 1, 2],
        budget=replace(proof.IntervalBudget(), max_pattern_nnz=8))
    assert result['hold_kind'] == 'RESOURCE_REFUSAL'
    assert result['product_symbolic_nnz'] == 9 and not result['positive']


def test_combined_workspace_is_refused_before_native_product(monkeypatch):
    monkeypatch.setattr(proof, 'sparse_product', lambda *args: pytest.fail('product ran despite combined workspace refusal'))
    result = proof.certify_factor_residual(sparse.eye(2, format='csr'), sparse.eye(2, format='csr'), [0, 1],
        budget=replace(proof.IntervalBudget(), max_workspace_bytes=3000))
    assert result['hold_kind'] == 'RESOURCE_REFUSAL' and not result['positive']


@pytest.mark.parametrize('field', ('max_clique_entries', 'max_updates'))
def test_symbolic_work_limits_refuse_before_product(field, monkeypatch):
    monkeypatch.setattr(proof, 'sparse_product', lambda *args: pytest.fail('symbolic work guard bypassed'))
    factor = sparse.csr_matrix([[1., 0.], [.5, 1.]])
    result = proof.certify_factor_residual(sparse.eye(2, format='csr'), factor, [0, 1],
        budget=replace(proof.IntervalBudget(), **{field: 1}))
    assert result['hold_kind'] == 'RESOURCE_REFUSAL' and 'clique/update' in result['hold_reason']


def test_default_input_order_refuses_and_explicit_larger_budget_admits():
    matrix = sparse.eye(2401, format='csr')
    default = proof.certify_factor_residual(matrix, matrix, list(range(2401)))
    assert default['hold_kind'] == 'RESOURCE_REFUSAL' and not default['positive']
    explicit = proof.certify_factor_residual(matrix, matrix, list(range(2401)),
        budget=replace(proof.IntervalBudget(), max_order=25068))
    assert explicit['positive'] and explicit['product_symbolic_nnz'] == 2401
    assert explicit['comparison_forward_completed'] == explicit['comparison_transpose_completed'] == 2401


def test_sparse_product_underflow_is_hold_not_a_negative_mode():
    factor = sparse.csr_matrix([[1., 0.], [1e-200, 1.]])
    result = proof.certify_factor_residual(sparse.eye(2, format='csr'), factor, [0, 1])
    assert result['hold_kind'] == 'ARITHMETIC_DOMAIN' and 'underflow' in result['hold_reason']
    assert not result['positive']


def test_all_ones_comparison_growth_holds_despite_exact_positive_factor_work():
    n = 520
    factor = sparse.csr_matrix(np.tril(np.ones((n, n))))
    # Exact F F.T has min(i,j)+1; the actual inverse of F is bidiagonal,
    # while the comparison recurrence grows as 2^(n-1).
    matrix = sparse.csr_matrix(np.minimum.outer(np.arange(n), np.arange(n))+1., dtype=np.float64)
    result = proof.certify_factor_residual(matrix, factor, list(range(n)),
        budget=replace(proof.IntervalBudget(), max_workspace_bytes=1 << 30))
    assert not result['positive'] and result['hold_kind'] == 'ARITHMETIC_DOMAIN'
    assert 'overflow' in result['hold_reason']
    assert result['comparison_forward_upper'][-1] >= float(2**(n-1))
    assert result['comparison_transpose_upper'][0] >= float(2**(n-1))


def test_inputs_and_returned_endpoint_vectors_are_owned():
    matrix, factor = sparse.diags((1., 4.), format='csr'), sparse.diags((1., -2.), format='csr')
    matrix_before, factor_before = matrix.data.copy(), factor.data.copy()
    matrix.data.flags.writeable = factor.data.flags.writeable = False
    result = proof.certify_factor_residual(matrix, factor, [0, 1])
    assert result['positive']
    np.testing.assert_array_equal(matrix.data, matrix_before)
    np.testing.assert_array_equal(factor.data, factor_before)
    result['comparison_forward_upper'][:] = -1.
    matrix.data.flags.writeable = factor.data.flags.writeable = True
    factor.data[:] = 17.
    assert np.all(result['comparison_transpose_upper'] > 0.)
    np.testing.assert_array_equal(matrix.data, matrix_before)


@pytest.mark.parametrize('error_type', (RuntimeError, MemoryError))
def test_programming_or_memory_error_is_not_converted_to_numerical_hold(monkeypatch, error_type):
    error = error_type('injected implementation defect')
    def fail(*args):
        raise error
    monkeypatch.setattr(proof, 'sparse_product', fail)
    with pytest.raises(error_type, match='implementation defect') as caught:
        proof.certify_factor_residual(sparse.eye(1, format='csr'), sparse.eye(1, format='csr'), [0])
    assert caught.value is error
