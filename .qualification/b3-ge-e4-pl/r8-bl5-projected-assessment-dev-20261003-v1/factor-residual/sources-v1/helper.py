"""Bounded comparison-inverse/residual proof for an exact stored factor.

This development primitive verifies a shifted symmetric representative, never
backend inertia, mixed-system positivity or qualification. Native sparse
allocations still require the caller's process supervisor.
"""
from __future__ import annotations

from dataclasses import asdict
import time

import numpy as np
from scipy import sparse

from scripts._b3_e4_f03_sparse_certificate import SparseBudget, validate_sparse, check_arithmetic
from scripts.r8_bl5_sparse_kernel_interval_dev import IntervalBudget, down, up, sum_up
from scripts.r8_bl5_sparse_kernel_saved_dev import sparse_product, difference_upper


class _ResourceRefusal(Exception):
    pass


def _deadline(started, budget):
    if time.monotonic()-started > budget.max_seconds:
        raise _ResourceRefusal('factor residual time ceiling exceeded')


def _own(matrix, budget):
    if type(matrix) in (sparse.csr_matrix, sparse.csc_matrix):
        if min(matrix.shape) < 1 or matrix.shape[0] != matrix.shape[1]:
            raise ValueError('positive square sparse matrix required')
        if type(matrix.data) is np.ndarray and len(matrix.data) > budget.max_pattern_nnz:
            raise _ResourceRefusal('input sparse nnz exceeds declared budget')
    try:
        return validate_sparse(matrix, SparseBudget(budget.max_order,
            budget.max_pattern_nnz, 1, budget.max_workspace_bytes))
    except ValueError as error:
        if str(error) in ('sparse matrix shape exceeds declared budget',
                         'sparse verification workspace estimate exceeds budget'):
            raise _ResourceRefusal(str(error)) from error
        raise


def _workspace(a_nnz, f_nnz, product_nnz, n):
    # Conservative combined live-storage estimate: owned/permuted/shifted A,
    # F/transpose/CSC/absolute copies, signed+absolute product, residual and
    # magnitude temporaries, symbolic row sets and recurrence vectors. Runtime
    # and unexposed native allocation overhead still need process supervision.
    union = a_nnz+product_nnz+n
    return 256*(5*a_nnz+6*f_nnz+4*product_nnz+6*union+8*n)+512*product_nnz


def _positive_product(left, right):
    if left == 0. or right == 0.:
        return 0.
    value = float(left)*float(right)
    if not np.isfinite(value) or value < np.finfo(float).tiny:
        raise ArithmeticError('comparison product overflow/underflow domain')
    return float(up(value))


def _comparison(matrix, diagonal, reverse, started, budget, endpoint):
    order = range(matrix.shape[0]-1, -1, -1) if reverse else range(matrix.shape[0])
    for row in order:
        _deadline(started, budget)
        products = []
        for position in range(matrix.indptr[row], matrix.indptr[row+1]):
            column = int(matrix.indices[position])
            if column == row:
                continue
            # Each elementary product is enclosed BEFORE addition.
            products.append(_positive_product(abs(float(matrix.data[position])), endpoint[column]))
        numerator = float(up(1.+sum_up(products)))
        value = numerator/float(diagonal[row])
        if not np.isfinite(value) or value < np.finfo(float).tiny:
            raise ArithmeticError('comparison division overflow/underflow domain')
        endpoint[row] = float(up(value))


def _product_preflight(factor, matrix, permutation, shift, started, budget, report):
    columns = factor.tocsc()
    union_rows = [set() for _ in range(factor.shape[0])]
    total, updates, maximum = 0, 0, 0
    for column in range(factor.shape[0]):
        _deadline(started, budget)
        rows = columns.indices[columns.indptr[column]:columns.indptr[column+1]]
        clique = len(rows)**2
        updates += clique
        maximum = max(maximum, clique)
        report.update(product_symbolic_updates=updates, product_maximum_clique_entries=maximum)
        if maximum > budget.max_clique_entries or updates > budget.max_updates:
            raise _ResourceRefusal('factor product clique/update ceiling exceeded')
        for row in rows:
            before = len(union_rows[int(row)])
            union_rows[int(row)].update(map(int, rows))
            total += len(union_rows[int(row)])-before
            report['product_symbolic_nnz'] = total
            workspace = _workspace(matrix.nnz, factor.nnz, total, factor.shape[0])
            report['workspace_estimate_bytes'] = workspace
            if total > budget.max_pattern_nnz:
                raise _ResourceRefusal('complete factor product symbolic output exceeds nnz budget')
            if workspace > budget.max_workspace_bytes:
                raise _ResourceRefusal('combined factor residual workspace ceiling exceeded')
    inverse = np.empty(len(permutation), dtype=int)
    inverse[list(permutation)] = np.arange(len(permutation))
    residual_count = 0
    for row, original in enumerate(permutation):
        _deadline(started, budget)
        actual = matrix.indices[matrix.indptr[original]:matrix.indptr[original+1]]
        union_rows[row].update(map(int, inverse[actual]))
        if shift:
            union_rows[row].add(row)
        residual_count += len(union_rows[row])
        report['residual_symbolic_nnz'] = residual_count
        if residual_count > budget.max_pattern_nnz:
            raise _ResourceRefusal('complete residual symbolic output exceeds nnz budget')
    return total


def certify_factor_residual(matrix, factor, permutation, *, shift=0., budget=None):
    """Certify B=A[permutation,permutation]-shiftI using exact stored lower F.

    Validation/programming errors propagate. Arithmetic/resource refusal and an
    insufficient directed margin return HOLD, which proves no negative mode.
    The comparison recurrence bounds inverse infinity/one norms without a
    global inverse; independently enclosed residual transfers that bound to B.
    """
    budget = IntervalBudget() if budget is None else budget
    if type(budget) is not IntervalBudget:
        raise ValueError('explicit IntervalBudget required')
    if type(shift) not in (float, int) or not np.isfinite(shift) or shift < 0.:
        raise ValueError('finite nonnegative exact stored shift required')
    shift = float(shift)
    started = time.monotonic()
    report = dict(status='HOLD_FACTOR_RESIDUAL', positive=False,
        target='exact stored symmetric matrix after complete symmetric permutation minus shiftI',
        shift=shift, budget=asdict(budget),
        arithmetic='outward binary64 comparison recurrence; conditional ordinary IEEE sparse residual accumulation',
        limitations='HOLD is not mechanical negativity; supervisor required; no mixed-K SPD/inertia or qualification claim')
    try:
        a, f = _own(matrix, budget), _own(factor, budget)
        n = a.shape[0]
        if f.shape != a.shape:
            raise ValueError('matching square matrix/factor order required')
        if (type(permutation) not in (list, tuple) or len(permutation) != n or
                any(type(value) is not int for value in permutation) or set(permutation) != set(range(n))):
            raise ValueError('complete plain-int symmetric permutation required')
        permutation = tuple(permutation)
        diagonal = np.abs(f.diagonal())
        if not np.all(diagonal > 0.):
            raise ValueError('every factor diagonal must be finite and nonzero')
        for row in range(n):
            if np.any(f.indices[f.indptr[row]:f.indptr[row+1]] > row):
                raise ValueError('exact lower triangular factor required; no ignored upper entries')
        report.update(order=n, matrix_nnz=a.nnz, factor_nnz=f.nnz, permutation=list(permutation))
        workspace = _workspace(a.nnz, f.nnz, 0, n)
        report['workspace_estimate_bytes'] = workspace
        if workspace > budget.max_workspace_bytes:
            raise _ResourceRefusal('combined factor residual input/copy workspace ceiling exceeded')
        transpose_a = a.T.tocsr()
        if np.any((a-transpose_a).data != 0.):
            raise ValueError('exact stored symmetric matrix required; no triangle completion')
        del transpose_a
        check_arithmetic()
        forward, backward = np.zeros(n), np.zeros(n)
        report.update(comparison_forward_upper=forward, comparison_transpose_upper=backward)
        _comparison(f, diagonal, False, started, budget, forward)
        # Actual transpose, with reverse dependency order; not forward reused.
        ft = f.T.tocsr()
        _comparison(ft, diagonal, True, started, budget, backward)
        binf, b1 = float(forward.max()), float(backward.max())
        report.update(inverse_inf_upper=binf, inverse_one_upper=b1)
        product = _positive_product(b1, binf)
        reciprocal = 1./product
        if reciprocal < np.finfo(float).tiny:
            raise ArithmeticError('inverse-norm reciprocal underflow domain')
        mu = float(down(reciprocal))
        report.update(inverse_norm_product_upper=product, mu_lower=mu)
        _product_preflight(f, a, permutation, shift, started, budget, report)
        bhat = a[list(permutation)][:, list(permutation)].tocsr()
        shift_error = 0.
        if shift:
            original_diagonal = bhat.diagonal()
            rounded = original_diagonal-shift
            lo, hi = down(rounded), up(rounded)
            radii = np.maximum(up(np.abs(lo-rounded)), up(np.abs(hi-rounded)))
            shift_error = float(radii.max())
            bhat.setdiag(rounded)
            bhat.sort_indices()
            report.update(shift_diagonal_lower=lo, shift_diagonal_upper=hi,
                          shifted_diagonal_rounded=rounded)
        report['shift_error_upper'] = shift_error
        _deadline(started, budget)
        qhat, product_error = sparse_product(f, ft)
        report['product_error_upper'] = product_error
        _deadline(started, budget)
        residual_bound = difference_upper(bhat, qhat)
        rho = sum_up([shift_error, product_error, residual_bound])
        margin = float(down(mu-rho))
        report.update(difference_error_upper=residual_bound, rho_upper=rho, margin_lower=margin,
            rounded_product_nnz=qhat.nnz,
            status='POSITIVE_SHIFTED_FACTOR_RESIDUAL' if margin > 0. else 'HOLD_FACTOR_RESIDUAL',
            positive=bool(margin > 0.))
        if margin <= 0.:
            report.update(hold_kind='INSUFFICIENT_MARGIN', hold_reason='directed mu-rho is not strictly positive')
        _deadline(started, budget)
    except _ResourceRefusal as error:
        report.update(status='HOLD_FACTOR_RESIDUAL', positive=False,
                      hold_kind='RESOURCE_REFUSAL', hold_reason=str(error))
    except (ArithmeticError, FloatingPointError) as error:
        if type(error) not in (ArithmeticError, FloatingPointError, OverflowError):
            raise
        report.update(status='HOLD_FACTOR_RESIDUAL', positive=False,
                      hold_kind='ARITHMETIC_DOMAIN', hold_reason=str(error))
    for name in ('comparison_forward_upper', 'comparison_transpose_upper'):
        if name in report:
            report[name.replace('_upper', '_completed')] = int(np.count_nonzero(report[name]))
    report['elapsed_seconds'] = time.monotonic()-started
    return report
