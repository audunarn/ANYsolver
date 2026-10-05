"""Additive fixed positive-part backend Gram candidate for a saved HOLD.

Clipping the backend U diagonal constructs an arbitrary real Gram factor. This
is neither a spectral positive part nor an exact LDL decomposition. Only the
unchanged complete Gram-residual certificate can admit the original target.
"""
import numpy as np
from scipy import sparse

from scripts.r8_bl5_envelope_gram_dev import PROOF_BUDGET
from scripts.r8_bl5_sparse_envelope_kernel_dev import require, store_sparse
from scripts.r8_bl5_sparse_factor_residual_dev import _own, _ResourceRefusal
from scripts.r8_bl5_sparse_gram_margin_dev import certify_gram_margin
from scripts.r8_bl5_sparse_kernel_interval_dev import IntervalBudget, down, up


IDENTITY = 'BL5_FIXED_BACKEND_DIAGONAL_POSITIVE_PART_GRAM_DEV_V1'


def _permutation(value, order):
    if type(value) in (list, tuple):
        require(not any(type(v) in (bool, np.bool_) for v in value),
                'complete integer saved permutation required')
    array = np.asarray(value)
    require(array.shape == (order,) and array.dtype.kind in 'iu' and
            np.array_equal(np.sort(array), np.arange(order)),
            'complete integer saved permutation required')
    return array.astype(np.int64, copy=True)


def certify_target(matrix, *, epsilon, metric, expected_perm_r, expected_perm_c,
                   budget=PROOF_BUDGET, checkpoint=None):
    """One replayed backend candidate; same shifts, proof, budget and floor.

    Checkpoint receives complete owned producer L/D/permutations before sign
    admission, then complete F before proof. Unexpected exceptions propagate
    after a FAILED checkpoint; the original saved HOLD is never written here.
    """
    require(type(budget) is IntervalBudget, 'explicit IntervalBudget required')
    require(checkpoint is None or callable(checkpoint), 'callable evidence checkpoint required')
    require(type(epsilon) is float and np.isfinite(epsilon) and epsilon > 0.,
            'positive finite stored error required')
    require(type(metric) is float and np.isfinite(metric) and metric > 0.,
            'positive finite physical graph metric required')
    sigma = float(up(2*epsilon))
    tau = float(up(sigma+epsilon))
    report = dict(identity=IDENTITY, status='HOLD_MECHANICAL_KERNEL',
                  fixed_shift=sigma, producer_shift=tau, epsilon=epsilon,
                  graph_metric_upper=metric, physical_kernel_lower_bound=None,
                  formal_f03_authority_consumed=False,
                  limitation='Backend-diagonal clipping only constructs a real Gram candidate; no spectral positive part, exact LDL, mixed-K SPD or qualification claim.')
    arrays = {}

    def save(stage):
        if checkpoint is not None:
            checkpoint(stage, report, arrays)

    try:
        try:
            a = _own(matrix, budget)
        except _ResourceRefusal as error:
            report.update(hold_kind='RESOURCE_REFUSAL', hold_reason=str(error))
            save('HOLD_RESOURCE_REFUSAL')
            return report, arrays
        require(not np.any((a-a.T).data != 0.), 'exact symmetric representative required')
        n = a.shape[0]
        expected_r = _permutation(expected_perm_r, n)
        expected_c = _permutation(expected_perm_c, n)
        arrays.update(expected_perm_r=expected_r, expected_perm_c=expected_c)
        bhat = a.copy()
        bhat.setdiag(bhat.diagonal()-tau)
        bhat.sort_indices()
        backend = sparse.linalg.splu(bhat.tocsc(), permc_spec='MMD_AT_PLUS_A',
            diag_pivot_thresh=0., options={'SymmetricMode':True, 'Equil':False})
        # Preserve complete raw producer evidence before finite/sign admission.
        lower = sparse.csr_matrix(backend.L, copy=True)
        diagonal = backend.U.diagonal().copy()
        row, column = backend.perm_r.copy(), backend.perm_c.copy()
        arrays.update(producer_diagonal=diagonal, producer_perm_r=row,
                      producer_perm_c=column)
        store_sparse(arrays, 'producer_L', lower)
        report['producer'] = dict(L_nnz=lower.nnz, U_nnz=backend.U.nnz,
            options=dict(permc_spec='MMD_AT_PLUS_A', diag_pivot_thresh=0.,
                         SymmetricMode=True, Equil=False),
            candidate_rule='candidate_F=stored L times sqrt(max(stored U diagonal,0)); not a spectral positive part or exact LDL')
        del backend, bhat
        save('SAVED_PRODUCER')
        actual_r, actual_c = _permutation(row, n), _permutation(column, n)
        if (not np.array_equal(actual_r, expected_r) or
                not np.array_equal(actual_c, expected_c) or
                not np.array_equal(actual_r, actual_c)):
            report.update(hold_kind='PRODUCER_PERMUTATION',
                          hold_reason='producer must replay both saved permutations and their symmetric ordering')
            save('HOLD_PRODUCER_PERMUTATION')
            return report, arrays
        if (diagonal.shape != (n,) or diagonal.dtype != np.float64 or
                not np.isrealobj(diagonal) or not np.isfinite(diagonal).all()):
            report.update(hold_kind='PRODUCER_DIAGONAL',
                          hold_reason='finite real binary64 producer diagonal required')
            save('HOLD_PRODUCER_DIAGONAL')
            return report, arrays
        try:
            lower = _own(lower, budget)
        except _ResourceRefusal as error:
            report.update(hold_kind='RESOURCE_REFUSAL', hold_reason=str(error))
            save('HOLD_RESOURCE_REFUSAL')
            return report, arrays
        require(lower.shape == a.shape, 'complete matching producer L required')
        positive = np.maximum(diagonal, 0.)
        arrays['producer_diagonal_positive_part'] = positive.copy()
        report['producer'].update(positive_entries=int(np.count_nonzero(diagonal > 0.)),
            zero_entries=int(np.count_nonzero(diagonal == 0.)),
            negative_entries=int(np.count_nonzero(diagonal < 0.)))
        order = np.argsort(actual_r).tolist()
        arrays['permutation'] = np.asarray(order, dtype=np.int64)
        f = sparse.csr_matrix(lower.multiply(np.sqrt(positive)))
        f.sum_duplicates()
        f.sort_indices()
        store_sparse(arrays, 'candidate_F', f)
        save('SAVED_CANDIDATE_FACTOR')
        # Singular and all-zero candidates are legitimate: FF.T is still PSD.
        proof = certify_gram_margin(a, f, order, target_shift=sigma,
                                    producer_shift=tau, budget=budget)
        for name, value in list(proof.items()):
            if isinstance(value, np.ndarray):
                arrays['proof_'+name] = proof.pop(name)
        report['gram_margin_proof'] = proof
        floor = float(down(float(down(sigma-epsilon))/metric))
        if proof['status'] == 'POSITIVE_FIXED_SHIFT_GRAM_MARGIN' and proof['positive'] and floor > 0.:
            report.update(status='POSITIVE_ENVELOPE_MECHANICAL_KERNEL_DEVELOPMENT_ONLY',
                          physical_kernel_lower_bound=floor)
        save('COMPLETE_GRAM_ASSESSMENT')
        return report, arrays
    except BaseException as error:
        report.update(status='FAILED_POSITIVE_PART_GRAM_ASSESSMENT',
                      physical_kernel_lower_bound=None,
                      failure=dict(type=type(error).__name__, message=str(error)))
        try:
            save('FAILED')
        except BaseException as recording_error:
            error.add_note('Recording also failed: '+repr(recording_error))
        raise
