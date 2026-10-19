"""Finite, fixed-order element-local contractions (no BLAS dispatch).

Products are split on normalized binary64 mantissas with Dekker's transform;
both parts are accumulated with ``math.fsum`` in ascending index order.
No exact-rounding claim is made: scaling a residual into the subnormal range
can lose at most one minimum subnormal per product, and fsum has its documented
platform double-rounding limitation. Exact cancellation/empty sums give +0.
Nonfinite inputs and overflowing individual products or sums are refused,
even when a wider exact accumulator could cancel an intermediate overflow.
There is no precision option, native backend, persistent cache or fallback.
"""
from math import frexp as _frexp, fsum as _fsum, isfinite as _isfinite, ldexp as _ldexp

import numpy as np


def _product_parts(a, b):
    if not _isfinite(a) or not _isfinite(b):
        raise ValueError("compensated contraction requires finite inputs")
    product = a * b
    if not _isfinite(product):
        raise OverflowError("compensated product overflow")
    if a == 0.0 or b == 0.0:
        return product, 0.0
    x, ex = _frexp(a)
    y, ey = _frexp(b)
    split = 134217729.0
    cx, cy = split * x, split * y
    xh, yh = cx - (cx - x), cy - (cy - y)
    xl, yl = x - xh, y - yh
    high = x * y
    low = ((xh * yh - high) + xh * yl + xl * yh) + xl * yl
    # In the normal range power-of-two scaling is exact. In the subnormal
    # range the rounded product need not equal a doubly rounded scaled high;
    # the contract allows that lost half-ulp and scaled-low rounding (<= one
    # minimum subnormal together), rather than claiming an exact expansion.
    return product, _ldexp(low, ex + ey)


def dot(left, right):
    if len(left) != len(right):
        raise ValueError("compensated dot shape mismatch")
    parts = []
    for a, b in zip(left, right):
        parts.extend(_product_parts(float(a), float(b)))
    result = _fsum(parts)
    if not _isfinite(result):
        raise OverflowError("compensated sum overflow")
    return result


def product(left, right):
    """Matrix/matrix or matrix/vector product; each dot uses the same policy."""
    a, b = np.asarray(left, dtype=float), np.asarray(right, dtype=float)
    if a.ndim != 2 or b.ndim not in (1, 2) or a.shape[1] != b.shape[0]:
        raise ValueError("compensated product shape mismatch")
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError("compensated product requires finite inputs")
    vector = b.ndim == 1
    columns = b.reshape((-1, 1)) if vector else b
    result = np.empty((a.shape[0], columns.shape[1]), dtype=float)
    for i in range(a.shape[0]):
        for j in range(columns.shape[1]):
            result[i, j] = dot(a[i], columns[:, j])
    return result[:, 0] if vector else result


def sum_arrays(terms):
    """Fixed-order componentwise sum of already represented equal-shape terms."""
    arrays = [np.asarray(term, dtype=float) for term in terms]
    if not arrays or any(a.shape != arrays[0].shape for a in arrays):
        raise ValueError("compensated array sum requires equal nonempty shapes")
    if any(not np.all(np.isfinite(a)) for a in arrays):
        raise ValueError("compensated array sum requires finite inputs")
    result = np.empty_like(arrays[0])
    for index in np.ndindex(result.shape):
        result[index] = _fsum(float(a[index]) for a in arrays)
    if not np.all(np.isfinite(result)):
        raise OverflowError("compensated array sum overflow")
    return result


def weighted_sum(terms, weights):
    """Quadrature reduction including compensation of each weight product."""
    arrays = [np.asarray(term, dtype=float) for term in terms]
    if not arrays or len(arrays) != len(weights) or any(a.shape != arrays[0].shape for a in arrays):
        raise ValueError("compensated weighted sum shape mismatch")
    result = np.empty_like(arrays[0])
    for index in np.ndindex(result.shape):
        result[index] = dot([a[index] for a in arrays], weights)
    return result


def shell_zero_tangent(geometry, membrane, bending, shear, drill):
    """Contract independently supplied elastic coefficients on frozen geometry."""
    terms, weights = [], []
    for bm, bb, bd, weight in zip(geometry["B_m_all"], geometry["B_b_all"],
                                  geometry["B_d_all"], geometry["detw_all"]):
        terms.append(sum_arrays((product(product(bm.T, membrane), bm),
                                 product(product(bb.T, bending), bb),
                                 product(bd.T, drill * bd))))
        weights.append(weight)
    for bs, weight in zip(geometry["B_s_all"], geometry["detw_shear_all"]):
        terms.append(product(product(bs.T, shear), bs))
        weights.append(weight)
    local = weighted_sum(terms, weights)
    transform = geometry["T0"]
    return product(product(transform.T, local), transform)
