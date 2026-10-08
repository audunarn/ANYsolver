"""Discriminating controls for the additive fixed positive-part candidate."""
import copy
from dataclasses import replace
import weakref

import numpy as np
import pytest
from scipy import sparse

from scripts import r8_bl5_envelope_gram_dev as old
from scripts import r8_bl5_positive_part_gram_dev as assessment


def evaluate(a, epsilon=.125, metric=4., **kwargs):
    n = a.shape[0]
    return assessment.certify_target(a, epsilon=epsilon, metric=metric,
        expected_perm_r=kwargs.pop('expected_perm_r', list(range(n))),
        expected_perm_c=kwargs.pop('expected_perm_c', list(range(n))), **kwargs)


def factor(arrays, prefix='candidate_F'):
    return sparse.csr_matrix((arrays[prefix+'_data'], arrays[prefix+'_indices'],
                              arrays[prefix+'_indptr']), shape=arrays[prefix+'_shape'])


@pytest.mark.parametrize('multiple,positive', [(2.5, True), (1.5, False)])
def test_scalar_negative_backend_diagonal_is_decided_by_original_target(multiple, positive):
    eps = .125
    a = sparse.csr_matrix([[multiple*eps]])
    report, arrays = evaluate(a, eps)
    assert arrays['producer_diagonal'][0] < 0.
    assert arrays['producer_diagonal_positive_part'][0] == 0.
    assert factor(arrays).count_nonzero() == 0
    assert report['gram_margin_proof']['positive'] is positive
    assert report['fixed_shift'] == float(assessment.up(2*eps))
    assert report['producer_shift'] == float(assessment.up(report['fixed_shift']+eps))
    if positive:
        assert report['status'] == 'POSITIVE_ENVELOPE_MECHANICAL_KERNEL_DEVELOPMENT_ONLY'
        assert report['physical_kernel_lower_bound'] == float(assessment.down(
            float(assessment.down(report['fixed_shift']-eps))/4.))
    else:
        assert report['status'] == 'HOLD_MECHANICAL_KERNEL'
        assert report['physical_kernel_lower_bound'] is None


def test_hidden_negative_direction_cannot_be_accepted_after_clipping():
    a = sparse.csr_matrix([[1., 2.], [2., 1.]])
    _, original = old.certify_target(a, epsilon=.125, metric=4.)
    report, arrays = evaluate(a, expected_perm_r=original['producer_perm_r'],
                             expected_perm_c=original['producer_perm_c'])
    assert np.linalg.eigvalsh(a.toarray()).min() < 0.
    assert report['status'] == 'HOLD_MECHANICAL_KERNEL'
    assert report['gram_margin_proof']['positive'] is False
    assert factor(arrays).shape == (2, 2)


def mock_backend(monkeypatch, lower, diagonal, row=None, column=None):
    n = lower.shape[0]
    class Backend:
        pass
    made = []
    def producer(matrix, **kwargs):
        assert kwargs == dict(permc_spec='MMD_AT_PLUS_A', diag_pivot_thresh=0.,
                              options={'SymmetricMode': True, 'Equil': False})
        obj = Backend()
        obj.L = sparse.csc_matrix(lower)
        obj.U = sparse.diags(np.asarray(diagonal), format='csc')
        obj.perm_r = np.asarray(list(range(n)) if row is None else row, dtype=np.int32)
        obj.perm_c = np.asarray(list(range(n)) if column is None else column, dtype=np.int32)
        made.append(weakref.ref(obj))
        return obj
    monkeypatch.setattr(assessment.sparse.linalg, 'splu', producer)
    return made


def test_singular_factor_and_signed_lower_amplification_use_complete_residual(monkeypatch):
    lower = sparse.csr_matrix([[1., 0.], [-10., 1.]])
    d = np.array([1., -.001])
    tau = float(assessment.up(float(assessment.up(.25))+.125))
    a = (lower@sparse.diags(d)@lower.T+tau*sparse.eye(2)).tocsr()
    a.sum_duplicates(); a.sort_indices()
    made = mock_backend(monkeypatch, lower, d)
    original = assessment.certify_gram_margin
    def proof(*args, **kwargs):
        assert made[0]() is None, 'opaque backend must be released before proof'
        return original(*args, **kwargs)
    monkeypatch.setattr(assessment, 'certify_gram_margin', proof)
    report, arrays = evaluate(a)
    assert factor(arrays).toarray()[1, 0] == -10.
    assert factor(arrays).toarray()[1, 1] == 0.
    assert report['gram_margin_proof']['positive']
    assert report['producer']['negative_entries'] == 1


def test_backend_sparse_array_lower_is_owned_as_csr_matrix(monkeypatch):
    def producer(matrix, **kwargs):
        # Real SuperLU can expose sparse arrays; the proof seam admits matrices.
        class Backend:
            L = sparse.csr_array([[1.]])
            U = sparse.csr_matrix([[1.]])
            perm_r = np.array([0], dtype=np.int32)
            perm_c = np.array([0], dtype=np.int32)
        return Backend()
    monkeypatch.setattr(assessment.sparse.linalg, 'splu', producer)
    original = assessment._own
    admitted = []
    def own(matrix, budget):
        admitted.append(type(matrix))
        return original(matrix, budget)
    monkeypatch.setattr(assessment, '_own', own)
    tau = float(assessment.up(float(assessment.up(.25))+.125))
    report, arrays = evaluate(sparse.csr_matrix([[1.+tau]]))
    assert admitted == [sparse.csr_matrix, sparse.csr_matrix]
    assert report['gram_margin_proof']['positive']
    assert factor(arrays, 'producer_L').toarray().tolist() == [[1.]]


def test_negative_diagonal_amplified_by_lower_is_not_silently_ignored(monkeypatch):
    lower = sparse.csr_matrix([[1., 0.], [-10., 1.]])
    d = np.array([-.01, 1.])
    tau = float(assessment.up(float(assessment.up(.25))+.125))
    a = (lower@sparse.diags(d)@lower.T+tau*sparse.eye(2)).tocsr()
    a.sum_duplicates(); a.sort_indices()
    mock_backend(monkeypatch, lower, d)
    report, _ = evaluate(a)
    assert report['status'] == 'HOLD_MECHANICAL_KERNEL'
    assert report['gram_margin_proof']['rho_upper'] > .125


@pytest.mark.parametrize('diagonal', ([np.nan, 1.], [np.inf, 1.], [1+1j, 1.]))
def test_nonfinite_or_nonreal_diagonal_preserves_full_producer_before_refusal(monkeypatch, diagonal):
    mock_backend(monkeypatch, sparse.eye(2), diagonal)
    stages, retained = [], {}
    def checkpoint(stage, report, arrays):
        stages.append(stage)
        retained.update({key: value.copy() for key, value in arrays.items()})
    report, arrays = evaluate(sparse.eye(2, format='csr'), checkpoint=checkpoint)
    assert report['hold_kind'] == 'PRODUCER_DIAGONAL'
    assert stages == ['SAVED_PRODUCER', 'HOLD_PRODUCER_DIAGONAL']
    np.testing.assert_array_equal(retained['producer_diagonal'], arrays['producer_diagonal'])
    assert factor(retained, 'producer_L').shape == (2, 2)
    assert 'candidate_F_data' not in retained


@pytest.mark.parametrize('row,column,expected_r,expected_c', (
    ([1, 0], [1, 0], [0, 1], [0, 1]),
    ([0, 1], [1, 0], [0, 1], [0, 1]),
    ([0, 1], [1, 0], [0, 1], [1, 0]),
))
def test_replay_and_symmetric_permutation_mismatch_preserve_producer(monkeypatch, row, column, expected_r, expected_c):
    mock_backend(monkeypatch, sparse.eye(2), [1., 1.], row, column)
    monkeypatch.setattr(assessment, 'certify_gram_margin', lambda *a, **k: pytest.fail('proof after order refusal'))
    report, arrays = evaluate(sparse.eye(2, format='csr'),
                             expected_perm_r=expected_r, expected_perm_c=expected_c)
    assert report['hold_kind'] == 'PRODUCER_PERMUTATION'
    np.testing.assert_array_equal(arrays['producer_perm_r'], row)
    assert factor(arrays, 'producer_L').shape == (2, 2)


def test_all_positive_case_matches_unchanged_old_function():
    a = sparse.csr_matrix([[4., -1., 0.], [-1., 3., -.5], [0., -.5, 2.]])
    before = a.copy()
    previous, old_arrays = old.certify_target(a, epsilon=1e-6, metric=4.)
    report, arrays = evaluate(a, 1e-6, expected_perm_r=old_arrays['producer_perm_r'],
                             expected_perm_c=old_arrays['producer_perm_c'])
    for key in ('status', 'fixed_shift', 'producer_shift', 'physical_kernel_lower_bound'):
        assert report[key] == previous[key]
    np.testing.assert_array_equal(factor(arrays).toarray(), factor(old_arrays).toarray())
    assert report['gram_margin_proof']['rho_upper'] == previous['gram_margin_proof']['rho_upper']
    np.testing.assert_array_equal(a.data, before.data)


def test_unexpected_proof_failure_retains_producer_factor_and_exception(monkeypatch):
    stages, snapshots = [], []
    def checkpoint(stage, report, arrays):
        stages.append(stage)
        snapshots.append((copy.deepcopy(report), {k: v.copy() for k, v in arrays.items()}))
    def failure(*args, **kwargs):
        raise MemoryError('complete proof failed')
    monkeypatch.setattr(assessment, 'certify_gram_margin', failure)
    with pytest.raises(MemoryError, match='complete proof failed'):
        evaluate(sparse.eye(1, format='csr'), checkpoint=checkpoint)
    assert stages == ['SAVED_PRODUCER', 'SAVED_CANDIDATE_FACTOR', 'FAILED']
    report, arrays = snapshots[-1]
    assert report['failure'] == dict(type='MemoryError', message='complete proof failed')
    assert report['physical_kernel_lower_bound'] is None
    assert factor(arrays, 'producer_L').shape == factor(arrays).shape == (1, 1)


def test_backend_failure_is_recorded_once_without_retry(monkeypatch):
    calls, snapshots = [], []
    def failure(*args, **kwargs):
        calls.append(1)
        raise RuntimeError('producer failed')
    monkeypatch.setattr(assessment.sparse.linalg, 'splu', failure)
    with pytest.raises(RuntimeError, match='producer failed'):
        evaluate(sparse.eye(1, format='csr'), checkpoint=lambda stage, report, arrays:
                 snapshots.append((stage, copy.deepcopy(report))))
    assert calls == [1] and snapshots[-1][0] == 'FAILED'
    assert snapshots[-1][1]['failure']['message'] == 'producer failed'


def test_resource_refusal_precedes_backend(monkeypatch):
    monkeypatch.setattr(assessment.sparse.linalg, 'splu', lambda *a, **k: pytest.fail('unguarded backend'))
    report, _ = evaluate(sparse.eye(2, format='csr'),
                         budget=replace(assessment.PROOF_BUDGET, max_order=1))
    assert report['hold_kind'] == 'RESOURCE_REFUSAL'


@pytest.mark.parametrize('permutation', ([0, 0], [False, 1], [0., 1.]))
def test_malformed_saved_permutations_are_rejected_before_backend(monkeypatch, permutation):
    monkeypatch.setattr(assessment.sparse.linalg, 'splu', lambda *a, **k: pytest.fail('backend before saved-order validation'))
    with pytest.raises(ValueError, match='integer saved permutation'):
        evaluate(sparse.eye(2, format='csr'), expected_perm_r=permutation)
