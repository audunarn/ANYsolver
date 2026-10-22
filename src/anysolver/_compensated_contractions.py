"""Finite, fixed-order element-local contractions (no BLAS dispatch).

Products are split on normalized binary64 mantissas with Dekker's transform;
both parts are accumulated with ``math.fsum`` in ascending index order.
No exact-rounding claim is made: scaling a residual into the subnormal range
can lose at most one minimum subnormal per product, and fsum has its documented
platform double-rounding limitation. Exact cancellation/empty sums give +0.
Nonfinite inputs and overflowing individual products or sums are refused,
even when a wider exact accumulator could cancel an intermediate overflow.
There is no precision option, persistent result cache or fallback that changes
a value. Optional compiled kernels (``_compensated_native``, Numba) execute the
same arithmetic bit for bit; they are enabled only when Numba is present and a
known-answer self-check at import reproduces the numpy path bitwise (it guards
against fused multiply-add contraction). Any refusal replays the numpy path so
the reference exception is raised.
"""
from math import frexp as _frexp, fsum as _fsum, isfinite as _isfinite, ldexp as _ldexp

import os

import numpy as np

from . import _compensated_native as _native

# Compiled kernels run the identical arithmetic (see _compensated_native); a
# nonzero kernel status replays the vectorised path, which raises the reference
# exception. ANYSOLVER_NATIVE_CONTRACTIONS=0 forces the numpy path.
_USE_NATIVE = _native.AVAILABLE and os.environ.get("ANYSOLVER_NATIVE_CONTRACTIONS", "1") != "0"


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


_SPLIT = 134217729.0


def _vector_parts(a, b):
    """Elementwise ``_product_parts`` for finite broadcastable arrays.

    Same IEEE operations in the same order as the scalar routine, so the
    (product, residual) pairs are bitwise identical. Refuses nonfinite inputs
    and overflowing products with the scalar routine's exceptions.
    """
    with np.errstate(all="ignore"):
        product = a * b
        if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))
                and np.all(np.isfinite(product))):
            # Rare error path: reproduce the scalar first-failure semantics.
            for x, y in zip(np.broadcast_to(a, product.shape).ravel().tolist(),
                            np.broadcast_to(b, product.shape).ravel().tolist()):
                _product_parts(x, y)
        x, ex = np.frexp(a)
        y, ey = np.frexp(b)
        cx, cy = _SPLIT * x, _SPLIT * y
        xh, yh = cx - (cx - x), cy - (cy - y)
        xl, yl = x - xh, y - yh
        high = x * y
        low = ((xh * yh - high) + xh * yl + xl * yh) + xl * yl
        low = np.ldexp(low, ex + ey)
        low = np.where((a == 0.0) | (b == 0.0), 0.0, low)
    return product, low


def _interleave_sum(product, low):
    """fsum of ``[p0, l0, p1, l1, ...]`` along the last axis, as the scalar dot."""
    lead = product.shape[:-1]
    count = product.shape[-1]
    parts = np.empty((product.size // max(count, 1), 2 * count), dtype=float)
    parts[:, 0::2] = product.reshape(-1, count)
    parts[:, 1::2] = low.reshape(-1, count)
    values = np.array(list(map(_fsum, parts.tolist())), dtype=float)
    if not np.all(np.isfinite(values)):
        raise OverflowError("compensated sum overflow")
    return values.reshape(lead)


def dot(left, right):
    if len(left) != len(right):
        raise ValueError("compensated dot shape mismatch")
    a = np.array([float(v) for v in left], dtype=float)
    b = np.array([float(v) for v in right], dtype=float)
    if a.size == 0:
        return 0.0
    product, low = _vector_parts(a, b)
    return float(_interleave_sum(product, low))


def product(left, right):
    """Matrix/matrix or matrix/vector product; each dot uses the same policy."""
    a, b = np.asarray(left, dtype=float), np.asarray(right, dtype=float)
    if a.ndim != 2 or b.ndim not in (1, 2) or a.shape[1] != b.shape[0]:
        raise ValueError("compensated product shape mismatch")
    if not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)):
        raise ValueError("compensated product requires finite inputs")
    vector = b.ndim == 1
    columns = b.reshape((-1, 1)) if vector else b
    if _USE_NATIVE:
        native = np.empty((a.shape[0], columns.shape[1]), dtype=float)
        if _native.contract_product(np.ascontiguousarray(a), np.ascontiguousarray(columns),
                                    native, _native.POW2) == 0:
            return native[:, 0] if vector else native
    result = np.zeros((a.shape[0], columns.shape[1]), dtype=float)
    # Terms with an all-zero operand slice are exact zeros in every dot and
    # cannot change an exactly rounded sum.
    keep = np.any(a != 0.0, axis=0) & np.any(columns != 0.0, axis=1)
    # Overflow in a pruned term would still be refused by the scalar policy
    # only if both factors were nonzero, so pruning never hides an error.
    if keep.any():
        a, columns = a[:, keep], columns[keep]
        prod, low = _vector_parts(a[:, None, :], columns.T[None, :, :])
        result = _interleave_sum(prod, low)
    return result[:, 0] if vector else result


def sum_arrays(terms):
    """Fixed-order componentwise sum of already represented equal-shape terms."""
    arrays = [np.asarray(term, dtype=float) for term in terms]
    if not arrays or any(a.shape != arrays[0].shape for a in arrays):
        raise ValueError("compensated array sum requires equal nonempty shapes")
    if any(not np.all(np.isfinite(a)) for a in arrays):
        raise ValueError("compensated array sum requires finite inputs")
    shape = arrays[0].shape
    if _USE_NATIVE:
        stack = np.ascontiguousarray(np.stack(arrays).reshape(len(arrays), -1))
        native = np.empty(stack.shape[1], dtype=float)
        if _native.contract_sum(stack, native) == 0:
            return native.reshape(shape)
    rows = np.stack(arrays).reshape(len(arrays), -1).T.tolist()
    result = np.array(list(map(_fsum, rows)), dtype=float).reshape(shape)
    if not np.all(np.isfinite(result)):
        raise OverflowError("compensated array sum overflow")
    return result


def weighted_sum(terms, weights):
    """Quadrature reduction including compensation of each weight product."""
    arrays = [np.asarray(term, dtype=float) for term in terms]
    if not arrays or len(arrays) != len(weights) or any(a.shape != arrays[0].shape for a in arrays):
        raise ValueError("compensated weighted sum shape mismatch")
    shape = arrays[0].shape
    try:
        if _USE_NATIVE:
            flat = np.ascontiguousarray(np.stack(arrays).reshape(len(arrays), -1))
            w = np.array([float(v) for v in weights], dtype=float)
            native = np.empty(flat.shape[1], dtype=float)
            if _native.contract_weighted(flat, w, native, _native.POW2) == 0:
                return native.reshape(shape)
        stacked = np.stack(arrays).reshape(len(arrays), -1).T
        w = np.array([float(v) for v in weights], dtype=float)
        prod, low = _vector_parts(stacked, w[None, :])
        return _interleave_sum(prod, low).reshape(shape)
    except (ValueError, OverflowError):
        # Refused input: replay index by index so the first failure (and its
        # exception type) is the one the scalar policy reports.
        result = np.empty(shape, dtype=float)
        for index in np.ndindex(shape):
            result[index] = _scalar_dot([a[index] for a in arrays], weights)
        return result


def _scalar_dot(left, right):
    parts = []
    for a, b in zip(left, right):
        parts.extend(_product_parts(float(a), float(b)))
    result = _fsum(parts)
    if not _isfinite(result):
        raise OverflowError("compensated sum overflow")
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


def _native_known_answers_match():
    """Disable the compiled kernels unless they reproduce the numpy path bitwise."""
    global _USE_NATIVE
    if not _USE_NATIVE:
        return
    rng = np.random.default_rng(20261022)
    a = rng.standard_normal((7, 9)) * 2.0 ** rng.integers(-40, 40, (7, 9))
    b = rng.standard_normal((9, 6)) * 2.0 ** rng.integers(-40, 40, (9, 6))
    stack = rng.standard_normal((5, 11)) * 2.0 ** rng.integers(-40, 40, (5, 11)) * 1e8
    stack[1] = -stack[0] * (1.0 + 2.0 ** -40)
    weights = rng.standard_normal(5)
    results = []
    for use in (True, False):
        _USE_NATIVE = use
        try:
            results.append((product(a, b).tobytes(), sum_arrays(list(stack)).tobytes(),
                            weighted_sum(list(stack), weights).tobytes()))
        except Exception:  # noqa: BLE001 - any failure disables the kernels
            results.append(None)
    _USE_NATIVE = results[0] is not None and results[0] == results[1]


_native_known_answers_match()
