"""Bounded block-preconditioned inverse proof for an exact stored lower factor.

Local solves supply only stored candidates. The guarded WF product and directed
Neumann bound verify their use, without assuming local inverse accuracy. This
primitive makes no mechanical sign, mixed-system or qualification claim.
"""
from __future__ import annotations

from dataclasses import asdict
import time

import numpy as np
from scipy import linalg, sparse

from scripts._b3_e4_f03_sparse_certificate import check_arithmetic, _sqrt
from scripts.r8_bl5_sparse_kernel_interval_dev import IntervalBudget, down, up
from scripts.r8_bl5_sparse_kernel_saved_dev import norm_upper, sparse_product
from scripts.r8_bl5_sparse_factor_residual_dev import (
    _ResourceRefusal, _own, _deadline, _comparison, _positive_product,
)


def _workspace(f_nnz, w_nnz, g_nnz, n):
    # Simultaneous owned inputs, W/local blocks, WF signed/absolute products,
    # canonical/transpose copies, symbolic sets and recurrence vectors. Native
    # allocator overhead remains the caller's supervised resource obligation.
    return 256*(5*f_nnz+6*w_nnz+8*g_nnz+8*n+4*18**2)+512*g_nnz


def _lower_diagonal(matrix):
    diagonal = np.abs(matrix.diagonal())
    if not np.all(diagonal > 0.):
        raise ValueError('every factor diagonal must be finite and nonzero')
    for row in range(matrix.shape[0]):
        if np.any(matrix.indices[matrix.indptr[row]:matrix.indptr[row+1]] > row):
            raise ValueError('exact lower triangular factor required; no ignored upper entries')
    return diagonal


def _buffers(report, prefix, matrix):
    report[prefix+'_data'] = matrix.data.copy()
    report[prefix+'_indices'] = matrix.indices.copy()
    report[prefix+'_indptr'] = matrix.indptr.copy()
    report[prefix+'_shape'] = list(matrix.shape)


def _preflight(w, f, started, budget, report):
    total, updates, maximum = 0, 0, 0
    for row in range(f.shape[0]):
        _deadline(started, budget)
        columns = set()
        work = 0
        for k in w.indices[w.indptr[row]:w.indptr[row+1]]:
            support = f.indices[f.indptr[k]:f.indptr[k+1]]
            work += len(support)
            columns.update(map(int, support))
        total += len(columns)
        updates += work
        maximum = max(maximum, work)
        report.update(product_symbolic_nnz=total, product_symbolic_updates=updates,
                      product_maximum_row_updates=maximum)
        workspace = _workspace(f.nnz, w.nnz, total, f.shape[0])
        report['workspace_estimate_bytes'] = workspace
        if maximum > budget.max_clique_entries or updates > budget.max_updates:
            raise _ResourceRefusal('complete WF product row/update ceiling exceeded')
        if total > budget.max_pattern_nnz:
            raise _ResourceRefusal('complete WF symbolic output exceeds nnz budget')
        if workspace > budget.max_workspace_bytes:
            raise _ResourceRefusal('combined block inverse product workspace ceiling exceeded')


def certify_block_inverse(factor, *, budget=None, block_size=18):
    """Bound ||F^-1||2 for exact stored F using contiguous <=18 local blocks.

    B bounds the inverse norm only if eta=b*eg<1, where b bounds the stored
    rounded Ghat inverse, eg encloses exact WF-Ghat, and c bounds stored W.
    Then B=b*c/(1-eta), and mu<=lambda_min(F F.T). HOLD proves no negative
    mode. Validation, programming and MemoryError exceptions propagate.
    """
    if type(block_size) is not int or block_size != 18:
        raise ValueError('plain integer block_size=18 required')
    budget = IntervalBudget() if budget is None else budget
    if type(budget) is not IntervalBudget:
        raise ValueError('explicit IntervalBudget required')
    started = time.monotonic()
    report = dict(status='HOLD_FACTOR_INVERSE_BOUND', finite_bound=False,
        target='inverse2 of exact stored lower factor; lower eigenvalue bound for its exact FF.T',
        block_size=18, budget=asdict(budget),
        local_block_source='scipy.linalg.solve_triangular on owned contiguous factor-order diagonal blocks; candidate only',
        arithmetic='directed binary64 comparison/Neumann bounds; conditional ordinary IEEE sparse product accumulation',
        limitations='no mechanical sign or qualification claim; native allocation requires caller supervision')
    try:
        f = _own(factor, budget)
        _lower_diagonal(f)
        n = f.shape[0]
        bounds = [(first, min(first+18, n)) for first in range(0, n, 18)]
        w_limit = sum((last-first)*(last-first+1)//2 for first, last in bounds)
        report.update(order=n, factor_nnz=f.nnz, block_bounds=np.array(bounds, dtype=np.int64),
                      local_candidate_nnz_limit=w_limit)
        workspace = _workspace(f.nnz, w_limit, 0, n)
        report['workspace_estimate_bytes'] = workspace
        if w_limit > budget.max_pattern_nnz:
            raise _ResourceRefusal('block candidate structural nnz ceiling exceeded')
        if workspace > budget.max_workspace_bytes:
            raise _ResourceRefusal('combined block inverse input/candidate workspace ceiling exceeded')
        check_arithmetic()
        data, indices, pointer = [], [], [0]
        records = []
        report['local_block_records'] = records
        for first, last in bounds:
            _deadline(started, budget)
            local = f[first:last, first:last].toarray()
            candidate = linalg.solve_triangular(local, np.eye(last-first), lower=True,
                                               unit_diagonal=False, check_finite=True)
            if not np.isfinite(candidate).all():
                raise ArithmeticError('nonfinite local stored inverse candidate')
            if np.any(np.triu(candidate, 1) != 0.):
                raise ValueError('local inverse candidate contains an upper entry')
            records.append(dict(first=first, last=last, order=last-first,
                source_nnz=int(np.count_nonzero(local)),
                candidate_nnz=int(np.count_nonzero(candidate))))
            for row in range(last-first):
                for column in range(row+1):
                    value = float(candidate[row, column])
                    if value != 0.:
                        data.append(value)
                        indices.append(first+column)
                pointer.append(len(data))
        w = sparse.csr_matrix((np.array(data, dtype=np.float64),
            np.array(indices, dtype=np.int64), np.array(pointer, dtype=np.int64)), shape=(n, n))
        report['w_nnz'] = w.nnz
        _buffers(report, 'w', w)
        _preflight(w, f, started, budget, report)
        _deadline(started, budget)
        g, eg = sparse_product(w, f)
        _buffers(report, 'ghat', g)
        report.update(eg_upper=eg, ghat_nnz=g.nnz)
        _deadline(started, budget)
        if not np.isfinite(eg) or eg < 0.:
            raise ArithmeticError('finite nonnegative WF product error required')
        # Own and validate the actual stored product before recurrence traversal.
        g = _own(g, budget)
        try:
            diagonal = _lower_diagonal(g)
        except ValueError as error:
            # A finite rounded product with a zero diagonal has no inverse bound.
            if str(error) == 'every factor diagonal must be finite and nonzero':
                raise ArithmeticError('stored WF diagonal does not establish an inverse') from error
            raise
        forward, backward = np.zeros(n), np.zeros(n)
        report.update(comparison_forward_upper=forward, comparison_transpose_upper=backward)
        _comparison(g, diagonal, False, started, budget, forward)
        _comparison(g.T.tocsr(), diagonal, True, started, budget, backward)
        binf, b1 = float(forward.max()), float(backward.max())
        report.update(ghat_inverse_inf_upper=binf, ghat_inverse_one_upper=b1)
        b = _sqrt(_positive_product(b1, binf), True)
        report['ghat_inverse_two_upper'] = b
        # norm_upper uses induced1/inf sums; exclude an underflowing norm square.
        magnitude = float(np.max(np.abs(w.data), initial=0.))
        _positive_product(magnitude, magnitude)
        c = float(norm_upper(w))
        if not np.isfinite(c) or c <= 0.:
            raise ArithmeticError('finite positive stored W norm bound required')
        report['w_norm_two_upper'] = c
        eta = _positive_product(b, eg)
        report['eta_upper'] = eta
        denominator = float(down(1.-eta))
        report['neumann_denominator_lower'] = denominator
        if eta >= 1. or denominator <= 0.:
            report.update(hold_kind='NON_NEUMANN_MARGIN',
                          hold_reason='directed WF error does not establish eta<1 and positive denominator')
        else:
            numerator = _positive_product(b, c)
            report['neumann_numerator_upper'] = numerator
            bound = float(up(numerator/denominator))
            if bound < np.finfo(float).tiny:
                raise ArithmeticError('block inverse division underflow domain')
            report['inverse_two_upper'] = bound
            square = _positive_product(bound, bound)
            report['inverse_two_square_upper'] = square
            reciprocal = 1./square
            if reciprocal < np.finfo(float).tiny:
                raise ArithmeticError('block inverse eigenvalue reciprocal underflow domain')
            mu = float(down(reciprocal))
            report.update(inverse_two_upper=bound, inverse_two_square_upper=square, mu_lower=mu,
                          status='FINITE_FACTOR_INVERSE_BOUND', finite_bound=True)
        _deadline(started, budget)
    except _ResourceRefusal as error:
        report.update(status='HOLD_FACTOR_INVERSE_BOUND', finite_bound=False,
                      hold_kind='RESOURCE_REFUSAL', hold_reason=str(error))
    except (ArithmeticError, FloatingPointError) as error:
        if type(error) not in (ArithmeticError, FloatingPointError, OverflowError):
            raise
        report.update(status='HOLD_FACTOR_INVERSE_BOUND', finite_bound=False,
                      hold_kind='ARITHMETIC_DOMAIN', hold_reason=str(error))
    for name in ('comparison_forward_upper', 'comparison_transpose_upper'):
        if name in report:
            report[name.replace('_upper', '_completed')] = int(np.count_nonzero(report[name]))
    report['elapsed_seconds'] = time.monotonic()-started
    return report
