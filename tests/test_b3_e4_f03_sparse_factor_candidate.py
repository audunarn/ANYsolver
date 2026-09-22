"""Synthetic factor production only: no classical reference equilibrium."""
from dataclasses import replace
from types import SimpleNamespace

import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_sparse_certificate as common
from scripts import _b3_e4_f03_sparse_factor_candidate as f
from scripts import _b3_e4_f03_sparse_positivity as p


SPARSE = common.SparseBudget(256, 50_000, 8, 64*1024**2)
FACTOR = f.FactorBudget(SPARSE, 100_000, 4*1024**2)
PROOF = p.PositivityBudget(SPARSE, 2_000_000, 70_000, 8192,
                           32_000_000, 512*1024**2)


def matrix():
    a = np.random.default_rng(509).normal(size=(9, 9))
    return sparse.csr_matrix(a.T@a+5*np.eye(9))


def test_real_superlu_candidate_verified_by_independent_full_residual():
    k = matrix()
    candidate = f.produce(k, FACTOR)
    assert candidate.metadata['status'] == 'CANDIDATE_CREATED'
    check = f.verify_against(k, candidate, PROOF)
    assert check['status'] == 'POSITIVE_QUADRATIC_FORM'
    assert check['proof']['raw']['delta_squared'] < 1
    assert check['proof']['work']['factor_rhs_solves'] == 0
    assert candidate.metadata['factorization_count'] == 1
    assert candidate.metadata['rhs_solve_count'] == 0
    assert candidate.metadata['qualification_status'] == 'NOT_QUALIFIED'
    n = len(candidate.permutation)
    pr = sparse.csr_matrix((np.ones(n), (candidate.row_map, np.arange(n))))
    pc = sparse.csr_matrix((np.ones(n), (np.arange(n), candidate.column_map)))
    residual = pr@k@pc-candidate.lower@candidate.upper
    assert np.linalg.norm(residual.data)/np.linalg.norm(k.data) < 1e-14
    assert check['factor_metadata']['matrix_sha256'] == candidate.metadata['matrix_sha256']


def mock_three_cycle():
    lower = np.array([[1., 0., 0.], [.5, 1., 0.], [.25, .125, 1.]])
    d = np.array([2., 4., 8.])
    upper = np.diag(d)@lower.T
    order = (2, 0, 1)
    k = np.zeros((3, 3))
    k[np.ix_(order, order)] = lower@upper
    perm = np.argsort(order).astype(np.int32)
    native = SimpleNamespace(L=sparse.csc_matrix(lower), U=sparse.csc_matrix(upper),
                             perm_r=perm.copy(), perm_c=perm.copy())
    return sparse.csr_matrix(k), native, order


def test_noninvolutive_native_permutation_uses_inverse_gather(monkeypatch):
    k, native, order = mock_three_cycle()
    calls = []
    def factor(matrix, **options):
        calls.append(options)
        return native
    monkeypatch.setattr(f, 'splu', factor)
    candidate = f.produce(k, FACTOR)
    assert candidate.permutation == order
    assert not np.array_equal(candidate.permutation, candidate.row_map)
    assert calls == [dict(permc_spec='MMD_AT_PLUS_A', diag_pivot_thresh=0.,
        options=dict(Equil=False, SymmetricMode=True, IterRefine='NOREFINE'))]
    result = f.verify_against(k, candidate, PROOF)
    assert result['status'] == 'POSITIVE_QUADRATIC_FORM'
    assert result['proof']['raw']['delta_squared'] == 0


def test_stored_small_skew_retained_by_producer_and_proof():
    k = matrix()
    k[1, 2] += 2.**-43
    candidate = f.produce(k, FACTOR)
    np.testing.assert_array_equal(candidate.matrix.data, k.data)
    result = f.verify_against(k, candidate, PROOF)
    assert result['status'] == 'POSITIVE_QUADRATIC_FORM'
    assert result['proof']['raw']['stored_skew_frobenius_squared'] > 0


def test_candidate_owns_all_arrays_and_input_identity_is_checked():
    k = matrix()
    candidate = f.produce(k, FACTOR)
    stored = candidate.matrix
    d = candidate.diagonal
    row = candidate.row_map
    candidate.lower.data[:] = 99; candidate.upper.data[:] = 99
    candidate.matrix.data[:] = 99; candidate.diagonal[:] = 99
    candidate.row_map[:] = 0; candidate.column_map[:] = 0
    assert f.verify_against(stored, candidate, PROOF)['status'] == 'POSITIVE_QUADRATIC_FORM'
    np.testing.assert_array_equal(candidate.diagonal, d)
    np.testing.assert_array_equal(candidate.row_map, row)
    with pytest.raises(TypeError): candidate.metadata['status'] = 'PASSED'
    with pytest.raises(TypeError): f.FactorCandidate()
    k.data[0] += 1
    with pytest.raises(ValueError, match='identity'):
        f.verify_against(k, candidate, PROOF)


def test_row_pivot_mismatch_is_hold_without_proof_or_fallback(monkeypatch):
    k, native, _ = mock_three_cycle()
    native.perm_r = np.roll(native.perm_r, 1)
    monkeypatch.setattr(f, 'splu', lambda *a, **kw: native)
    candidate = f.produce(k, FACTOR)
    monkeypatch.setattr(p, 'certify_positive', lambda *a, **kw: pytest.fail('invalid producer admitted'))
    result = f.verify_against(k, candidate, PROOF)
    assert result['status'] == 'HOLD' and result['proof'] is None
    assert 'permutations differ' in result['reason']


def test_nonpositive_and_singular_cases_do_not_establish_positivity():
    k = sparse.diags([1., -1., 2.], format='csr')
    candidate = f.produce(k, FACTOR)
    assert candidate.metadata['status'] == 'HOLD'
    assert f.verify_against(k, candidate, PROOF)['status'] == 'HOLD'
    with pytest.raises(RuntimeError):
        f.produce(sparse.diags([1., 0., 2.], format='csr'), FACTOR)


def test_sparse_producer_above_dense_probe_cap(monkeypatch):
    n = 129
    k = sparse.diags(np.linspace(1, 2, n), format='csr')
    monkeypatch.setattr(sparse.csr_matrix, 'toarray',
                        lambda *a, **kw: pytest.fail('dense global fallback'))
    candidate = f.produce(k, FACTOR)
    result = f.verify_against(k, candidate, PROOF)
    assert result['status'] == 'POSITIVE_QUADRATIC_FORM'
    assert candidate.metadata['factor_nnz'] == 2*n
    assert result['proof']['work']['product_paths'] == n


def test_coupled_two_dimensional_sparse_spd_graph():
    # Pure algebraic Dirichlet graph with a two-component shear congruence;
    # it invokes neither an element nor the classical reference assembler.
    line = sparse.diags([-np.ones(6), 2*np.ones(7), -np.ones(6)],
                         [-1, 0, 1], format='csr')
    grid = sparse.kronsum(line, line, format='csr')
    transform = sparse.kron(sparse.eye(49), np.array([[1., .5], [0., 1.]]), format='csr')
    original = sparse.kron(grid, np.diag([1., 2.]), format='csr')
    k = (transform.T@original@transform).tocsr()
    k.sort_indices()
    candidate = f.produce(k, FACTOR)
    result = f.verify_against(k, candidate, PROOF)
    assert result['status'] == 'POSITIVE_QUADRATIC_FORM'
    assert result['proof']['raw']['delta_squared'] < 1
    assert candidate.metadata['factor_nnz'] > 2*98


def test_budgets_before_factorization_and_observed_fill_after(monkeypatch):
    k = matrix()
    native = f.splu
    monkeypatch.setattr(f, 'splu', lambda *a, **kw: pytest.fail('factor before preflight'))
    with pytest.raises(ValueError, match='minimum'):
        f.produce(k, replace(FACTOR, max_factor_nnz=1))
    with pytest.raises(ValueError, match='minimum'):
        f.produce(k, replace(FACTOR, max_factor_storage_bytes=1))
    monkeypatch.setattr(f, 'splu', native)
    with pytest.raises(ValueError, match='observed'):
        f.produce(k, replace(FACTOR, max_factor_nnz=18))


@pytest.mark.parametrize('error', [MemoryError('opaque factor'), RuntimeError('native failure')])
def test_exceptions_propagate_unchanged(monkeypatch, error):
    def failed(*a, **kw): raise error
    monkeypatch.setattr(f, 'splu', failed)
    with pytest.raises(type(error)) as caught: f.produce(matrix(), FACTOR)
    assert caught.value is error


@pytest.mark.parametrize('defect', ['permutation', 'lower', 'upper', 'nonfinite'])
def test_invalid_native_output_rejected(monkeypatch, defect):
    k, native, _ = mock_three_cycle()
    if defect == 'permutation': native.perm_c[:] = 0
    if defect == 'lower': native.L.data[0] = 2
    if defect == 'upper': native.U = sparse.csc_matrix(native.U.toarray().T)
    if defect == 'nonfinite': native.U.data[0] = np.nan
    monkeypatch.setattr(f, 'splu', lambda *a, **kw: native)
    with pytest.raises((ValueError, ArithmeticError)): f.produce(k, FACTOR)


@pytest.mark.parametrize('kind', [sparse.csr_array, sparse.csc_array])
def test_sparse_array_bridge_checks_buffers_before_native_conversion(monkeypatch, kind):
    value = kind(np.eye(3))
    copied = f._native_factor(value, SPARSE)
    value.data[:] = 8
    np.testing.assert_array_equal(copied.data, np.ones(3))
    value.indices[0] = 9
    def forbidden(*a, **kw): pytest.fail('native traversal of invalid factor buffers')
    monkeypatch.setattr(sparse.csr_matrix, 'tocsr', forbidden)
    monkeypatch.setattr(sparse.csc_matrix, 'tocsr', forbidden)
    with pytest.raises(ValueError, match='structure'):
        f._native_factor(value, SPARSE)


@pytest.mark.parametrize('kind', [sparse.csr_array, sparse.csc_array])
def test_native_index_normalization_preserves_bits_without_duplicate_sum(kind):
    raw = kind((np.array([2., -.25, 1.]), np.array([1, 0, 1]),
                np.array([0, 2, 3])), shape=(2, 2))
    before = raw.data.copy()
    result = f._native_factor(raw, SPARSE)
    expected = np.array([[-.25, 2.], [0., 1.]])
    if kind is sparse.csc_array: expected = expected.T
    np.testing.assert_array_equal(result.toarray(), expected)
    np.testing.assert_array_equal(raw.data, before)
    raw.indices[0] = 0
    with pytest.raises(ValueError, match='duplicate'):
        f._native_factor(raw, SPARSE)
