"""Complete Gram residual proof of a fixed shifted mechanical representative.

Development only: preserves the target shift, using a separately frozen larger
producer shift. No inverse bound, inertia assertion or mixed-K SPD assumption.
The existing sparse arithmetic/enclosure assumptions and supervisor apply.
"""
from dataclasses import asdict
import time

import numpy as np

from scripts.r8_bl5_sparse_factor_residual_dev import (
    _ResourceRefusal, _own, _workspace, _deadline, _product_preflight,
)
from scripts._b3_e4_f03_sparse_certificate import check_arithmetic
from scripts.r8_bl5_sparse_kernel_interval_dev import IntervalBudget, down, up, sum_up
from scripts.r8_bl5_sparse_kernel_saved_dev import sparse_product, difference_upper


def certify_gram_margin(matrix, factor, permutation, *, target_shift, producer_shift, budget=None):
    """Enclose R=PAP.T-tauI-FF.T; prove A-sigmaI >= (tau-sigma-rho)I.

    F need not be invertible or triangular: every real FF.T is PSD. All entries,
    including cancellation fill, are included. Validation/programming/memory
    errors propagate; arithmetic/resource/insufficient-margin returns HOLD.
    """
    budget = IntervalBudget() if budget is None else budget
    if type(budget) is not IntervalBudget:
        raise ValueError('explicit IntervalBudget required')
    for shift in (target_shift, producer_shift):
        if type(shift) not in (float, int) or not np.isfinite(shift) or shift < 0.:
            raise ValueError('finite nonnegative exact stored shifts required')
    sigma, tau = float(target_shift), float(producer_shift)
    if tau <= sigma:
        raise ValueError('producer shift must strictly exceed fixed target shift')
    started = time.monotonic()
    report = dict(status='HOLD_GRAM_MARGIN', positive=False,
        target_shift=sigma, producer_shift=tau, budget=asdict(budget),
        target='exact stored symmetric representative minus fixed target_shift I',
        arithmetic='outward binary64; conditional ordinary IEEE complete sparse accumulation',
        limitations='HOLD proves no negative mode; no mixed-K SPD/inertia or qualification claim')
    try:
        a, f = _own(matrix, budget), _own(factor, budget)
        n = a.shape[0]
        if f.shape != a.shape:
            raise ValueError('matching square matrix/factor order required')
        if (type(permutation) not in (list, tuple) or len(permutation) != n or
                any(type(v) is not int for v in permutation) or set(permutation) != set(range(n))):
            raise ValueError('complete plain-int symmetric permutation required')
        if np.any((a-a.T).data != 0.):
            raise ValueError('exact stored symmetric matrix required; no triangle completion')
        report.update(order=n, matrix_nnz=a.nnz, factor_nnz=f.nnz, permutation=list(permutation))
        workspace = _workspace(a.nnz, f.nnz, 0, n)
        report['workspace_estimate_bytes'] = workspace
        if workspace > budget.max_workspace_bytes:
            raise _ResourceRefusal('combined Gram input/copy workspace ceiling exceeded')
        check_arithmetic()
        _product_preflight(f, a, permutation, tau, started, budget, report)
        bhat = a[list(permutation)][:, list(permutation)].tocsr()
        rounded = bhat.diagonal()-tau
        lo, hi = down(rounded), up(rounded)
        shift_error = float(np.maximum(up(np.abs(lo-rounded)), up(np.abs(hi-rounded))).max())
        bhat.setdiag(rounded)
        bhat.sort_indices()
        report.update(shift_error_upper=shift_error, shift_diagonal_lower=lo,
                      shift_diagonal_upper=hi, shifted_diagonal_rounded=rounded)
        _deadline(started, budget)
        qhat, product_error = sparse_product(f, f.T.tocsr())
        _deadline(started, budget)
        difference = difference_upper(bhat, qhat)
        rho = sum_up([shift_error, product_error, difference])
        gap = float(down(tau-sigma))
        margin = float(down(gap-rho))
        report.update(product_error_upper=product_error, difference_error_upper=difference,
                      rho_upper=rho, shift_gap_lower=gap, margin_lower=margin,
                      rounded_product_nnz=qhat.nnz, positive=bool(margin > 0.))
        if margin > 0.:
            report['status'] = 'POSITIVE_FIXED_SHIFT_GRAM_MARGIN'
        else:
            report.update(hold_kind='INSUFFICIENT_MARGIN',
                          hold_reason='directed producer-target shift gap minus complete residual is not positive')
        _deadline(started, budget)
    except _ResourceRefusal as error:
        report.update(status='HOLD_GRAM_MARGIN', positive=False,
                      hold_kind='RESOURCE_REFUSAL', hold_reason=str(error))
    except (ArithmeticError, FloatingPointError) as error:
        if type(error) not in (ArithmeticError, FloatingPointError, OverflowError):
            raise
        report.update(status='HOLD_GRAM_MARGIN', positive=False,
                      hold_kind='ARITHMETIC_DOMAIN', hold_reason=str(error))
    report['elapsed_seconds'] = time.monotonic()-started
    return report
