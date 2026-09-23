"""Streamed, outward-rounded inverse-column certificate for research matrices.

Saved binary64 inputs are exact real operands. Every scalar product and
addition used for an enclosure is bracketed by its adjacent binary64 values.
This deliberately transparent verifier makes no BLAS/sparse-dot error claim.
It is candidate A, not a selected scientific protocol or a production inverse.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

import numpy as np
from scipy import sparse


@dataclass(frozen=True, slots=True)
class SparseBudget:
    max_order: int
    max_nnz: int
    max_block_columns: int
    max_work_bytes: int

    def __post_init__(self):
        if any(type(v) is not int or v <= 0 for v in (
                self.max_order, self.max_nnz, self.max_block_columns,
                self.max_work_bytes)):
            raise ValueError('explicit positive integer sparse budgets required')


def _workspace(rows, cols, nnz, block, budget):
    # Conservative bound for this implementation's live numerical arrays,
    # not caller-owned storage, Python/SciPy runtime, factor fill or total RSS.
    estimate = 128 * nnz + 128 * (rows + cols + 2) + 256 * rows * block
    if estimate > budget.max_work_bytes:
        raise ValueError('sparse verification workspace estimate exceeds budget')
    return estimate


def validate_sparse(value, budget, *, square=True):
    """Own canonical buffers before any native sparse traversal/conversion."""
    if not isinstance(budget, SparseBudget) or type(square) is not bool:
        raise ValueError('validated sparse budget and shape policy required')
    if type(value) not in (sparse.csr_matrix, sparse.csc_matrix):
        raise ValueError('canonical CSR/CSC matrix required')
    rows, cols = value.shape
    if (not 1 <= rows <= budget.max_order or not 1 <= cols <= budget.max_order
            or (square and rows != cols)):
        raise ValueError('sparse matrix shape exceeds declared budget')
    outer, inner = (rows, cols) if type(value) is sparse.csr_matrix else (cols, rows)
    data, indices, pointer = value.data, value.indices, value.indptr
    if (any(type(a) is not np.ndarray or a.ndim != 1
            for a in (data, indices, pointer)) or data.dtype != np.float64
            or indices.dtype not in (np.dtype('int32'), np.dtype('int64'))
            or pointer.dtype not in (np.dtype('int32'), np.dtype('int64'))
            or len(data) != len(indices) or len(data) > min(rows*cols, budget.max_nnz)
            or len(pointer) != outer+1):
        raise ValueError('invalid bounded sparse buffers')
    _workspace(rows, cols, len(data), 1, budget)
    data, indices, pointer = data.copy(), indices.copy(), pointer.copy()
    if (pointer[0] != 0 or pointer[-1] != len(data)
            or np.any(pointer < 0) or np.any(pointer > len(data))
            or np.any(pointer[1:] < pointer[:-1])
            or np.any(indices < 0) or np.any(indices >= inner)):
        raise ValueError('invalid sparse pointer/index structure')
    for start, end in zip(pointer, pointer[1:]):
        segment = indices[start:end]
        if np.any(segment[1:] <= segment[:-1]):
            raise ValueError('strictly ordered canonical sparse entries required')
    if not np.isfinite(data).all():
        raise ValueError('finite sparse entries required')
    cls = sparse.csr_matrix if type(value) is sparse.csr_matrix else sparse.csc_matrix
    return cls((data, indices, pointer), shape=(rows, cols), copy=False).tocsr(copy=True)


def _finite(value):
    if not np.isfinite(value).all():
        raise ArithmeticError('nonfinite interval endpoint; no certificate')
    return value


def _up(value):
    return _finite(np.nextafter(_finite(value), np.inf))


def _down(value):
    return _finite(np.nextafter(_finite(value), -np.inf))


def _positive_down(value):
    # Intersect with the independently known nonnegative real domain.
    return np.maximum(0., _down(value))


def _sqrt(value, upper):
    if not math.isfinite(value) or value < 0:
        raise ArithmeticError('finite nonnegative square-root domain required')
    root = math.sqrt(value)
    if not math.isfinite(root) or root < 0:
        raise ArithmeticError('finite nonnegative square-root response required')
    candidate = float(_up(root) if upper else _positive_down(root))
    square = Fraction(candidate)**2
    target = Fraction(float(value))
    if (square < target) if upper else (square > target):
        raise ArithmeticError('square-root enclosure failed exact scalar check')
    return candidate


def check_arithmetic():
    """Reject observed FTZ/DAZ; IEEE binary64 elementary rounding is required."""
    tiny = np.finfo(np.float64).tiny
    sub = np.nextafter(np.float64(0), np.float64(1))
    x = np.array([tiny, sub, sub], dtype=np.float64)
    if (np.finfo(np.float64).nmant != 52 or sub <= 0 or
            not np.array_equal(x*np.array([.5, 1., 2.]),
                               np.array([tiny/2, sub, 2*sub])) or
            (np.array([sub])+np.array([sub]))[0] != 2*sub or
            (np.array([tiny])/2)[0] != math.ldexp(1., -1023)):
        raise ArithmeticError('gradual-underflow binary64 arithmetic required')


def _vector(value, n, name):
    if (type(value) is not np.ndarray or value.dtype != np.float64
            or value.shape != (n,) or not np.isfinite(value).all()):
        raise ValueError(f'{name} must be a finite float64 length-N vector')
    return value.copy()


def _sum_up(values):
    total = 0.
    for v in np.ravel(values):
        if v != 0:
            total = float(_up(total+float(v)))
    return total


def _norm2(value):
    low = high = 0.
    for v in np.ravel(value):
        if v != 0:
            product = float(v)*float(v)
            low = float(_positive_down(low+float(_positive_down(product))))
            high = float(_up(high+float(_up(product))))
    if high == 0:
        return 0., 0.
    return _sqrt(low, False), _sqrt(high, True)


def _matrix_norms(matrix):
    n = matrix.shape[0]
    columns = np.zeros(n)
    columns_squared_low = np.zeros(n)
    infinity = norm_lower = 0.
    for row in range(n):
        start, end = matrix.indptr[row:row+2]
        values = matrix.data[start:end]
        infinity = max(infinity, _sum_up(np.abs(values)))
        norm_lower = max(norm_lower, _norm2(values)[0])
        for col, v in zip(matrix.indices[start:end], values):
            if v != 0:
                columns[col] = _up(columns[col]+abs(v))
                p = float(_positive_down(float(v)*float(v)))
                columns_squared_low[col] = _positive_down(columns_squared_low[col]+p)
    for v in columns_squared_low:
        norm_lower = max(norm_lower, _sqrt(float(v), False))
    return float(max(columns)), infinity, norm_lower


def _product_bounds(matrix, block):
    """Explicit per-entry interval arithmetic, independent of sparse @."""
    n, width = block.shape
    low, high = np.zeros((n, width)), np.zeros((n, width))
    for row in range(n):
        start, end = matrix.indptr[row:row+2]
        for col, v in zip(matrix.indices[start:end], matrix.data[start:end]):
            if v == 0:
                continue
            product = v*block[col]
            low[row] = _down(low[row]+_down(product))
            high[row] = _up(high[row]+_up(product))
    return low, high


def _residual_abs(low, high, target):
    return np.maximum(np.abs(_down(target-high)), np.abs(_up(target-low)))


def certificate_a(matrix, inverse_blocks, budget, *, b=None, z=None,
                  interval_kernel='scalar'):
    """Verify every supplied inverse column once, in contiguous block order.

    ``inverse_blocks`` yields ``(start_column, float64[N,width])``. It may
    load saved blocks; this function never computes an inverse or factorizes.
    All N columns are mandatory. Saved-array hashes/inventory and factor
    identities belong to the enclosing future scientific protocol.
    """
    h = validate_sparse(matrix, budget)
    if interval_kernel == 'scalar':
        product_bounds = _product_bounds
    elif interval_kernel == 'compiled_experimental':
        from scripts._b3_e4_f03_q6_interval_kernel import compiled_product_bounds
        product_bounds = compiled_product_bounds
    else:
        raise ValueError('unknown interval-product kernel')
    n = h.shape[0]
    _workspace(n, n, h.nnz, min(n, budget.max_block_columns), budget)
    if (b is None) != (z is None):
        raise ValueError('backward check requires both b and z')
    if b is not None:
        b, z = _vector(b, n, 'b'), _vector(z, n, 'z')
    check_arithmetic()
    h1, hi, hl = _matrix_norms(h)
    yrows, erows = np.zeros(n), np.zeros(n)
    y1 = e1 = 0.
    cursor = blocks = 0
    with np.errstate(over='raise', invalid='raise', under='ignore', divide='raise'):
        for item in inverse_blocks:
            if not isinstance(item, (tuple, list)) or len(item) != 2:
                raise ValueError('indexed inverse block required')
            start, supplied = item
            if (type(start) is not int or start != cursor
                    or type(supplied) is not np.ndarray or supplied.dtype != np.float64
                    or supplied.ndim != 2 or supplied.shape[0] != n
                    or not 1 <= supplied.shape[1] <= budget.max_block_columns
                    or cursor+supplied.shape[1] > n):
                raise ValueError('inverse block shape/order exceeds declared inventory')
            y = supplied.copy()
            if not np.isfinite(y).all():
                raise ValueError('finite inverse block required')
            width = y.shape[1]
            low, high = product_bounds(h, y)
            target = np.zeros((n, width))
            target[np.arange(cursor, cursor+width), np.arange(width)] = 1.
            error = _residual_abs(low, high, target)
            for j in range(width):
                yabs = np.abs(y[:, j])
                y1 = max(y1, _sum_up(yabs))
                e1 = max(e1, _sum_up(error[:, j]))
                yrows = _up(yrows+yabs)
                erows = _up(erows+error[:, j])
            cursor += width
            blocks += 1
        if cursor != n:
            raise ValueError('incomplete inverse-column inventory')
        yi, ei = float(max(yrows)), float(max(erows))
        output = {'method': 'STREAMED_INVERSE_COLUMNS_INTERVAL_V1',
            'interval_kernel': interval_kernel,
            'matrix_order': n, 'matrix_nnz': h.nnz, 'inverse_columns': cursor,
            'inverse_blocks': blocks, 'raw_inverse_evidence_bytes': 8*n*n,
            'matrix_one_upper': h1, 'matrix_infinity_upper': hi,
            'matrix_two_lower': hl, 'inverse_candidate_one_upper': y1,
            'inverse_candidate_infinity_upper': yi, 'error_one_upper': e1,
            'error_infinity_upper': ei, 'status': 'HOLD'}
        if e1 >= 1 or ei >= 1:
            output['reason'] = 'Neumann residual norm bound is not below one'
            return output
        b1 = float(_up(y1/float(_down(1-e1))))
        bi = float(_up(yi/float(_down(1-ei))))
        inverse_two = _sqrt(float(_up(b1*bi)), True)
        htwo = _sqrt(float(_up(h1*hi)), True)
        condition = float(_up(htwo*inverse_two))
        output.update(inverse_one_upper=b1, inverse_infinity_upper=bi,
            inverse_two_upper=inverse_two, condition_two_upper=condition,
            condition_limit=1e10, amplified_backward_limit=1e-8)
        if b is not None:
            low, high = product_bounds(h, z[:, None])
            residual_abs = _residual_abs(low, high, b[:, None])
            residual_upper = _norm2(residual_abs)[1]
            zl, zu = _norm2(z)
            bl, _ = _norm2(b)
            denominator = float(_down(float(_positive_down(hl*zl))+bl))
            if denominator <= 0:
                raise ArithmeticError('positive backward-error denominator required')
            backward = float(_up(residual_upper/denominator))
            amplified = float(_up(condition*backward))
            output.update(residual_two_upper=residual_upper, z_two_lower=zl,
                z_two_upper=zu, b_two_lower=bl, backward_denominator_lower=denominator,
                backward_error_upper=backward, amplified_backward_upper=amplified)
            output['status'] = ('CERTIFIED_WITHIN_LIMIT' if condition <= 1e10
                                and amplified <= 1e-8 else 'HOLD')
        else:
            output['status'] = 'CONDITION_BOUND_ONLY' if condition <= 1e10 else 'HOLD'
        return output
