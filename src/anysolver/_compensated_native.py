"""Optional compiled kernels for the local compensated contractions.

Bitwise the same arithmetic as ``_compensated_contractions``: Dekker product
splitting and CPython ``math.fsum`` (Shewchuk partials with the final half-way
correction), with no fast-math and no fused multiply-add contraction.  A kernel
returns status 1 for nonfinite input, product overflow or fsum overflow; the
caller then replays the scalar-policy path, which raises the reference
exception.  Without Numba the kernels are never used.
"""
import math

import numpy as np

from .jit_compiler import JIT_ENABLED, njit

AVAILABLE = bool(JIT_ENABLED)

POW2 = np.array([math.ldexp(1.0, e) if e <= 1023 else float("inf") for e in range(-1100, 1100)])
POW2.flags.writeable = False


def _kernel(function):
    """njit with the disk cache; without a writable cache location compile uncached."""
    try:
        return njit(function)
    except Exception:  # noqa: BLE001 - numba raises RuntimeError when no cache locator exists
        return njit(cache=False)(function)


@_kernel
def _fsum_buf(buf, n, partials):
    """math.fsum(buf[:n]); status 1 on intermediate overflow."""
    m = 0
    for t in range(n):
        x = buf[t]
        j = 0
        for i in range(m):
            y = partials[i]
            if abs(x) < abs(y):
                tmp = x
                x = y
                y = tmp
            hi = x + y
            if not math.isfinite(hi):
                return 0.0, 1
            yr = hi - x
            lo = y - yr
            if lo != 0.0:
                partials[j] = lo
                j += 1
            x = hi
        m = j
        if x != 0.0:
            partials[m] = x
            m += 1
    hi = 0.0
    if m > 0:
        m -= 1
        hi = partials[m]
        lo = 0.0
        while m > 0:
            x = hi
            m -= 1
            y = partials[m]
            hi = x + y
            yr = hi - x
            lo = y - yr
            if lo != 0.0:
                break
        if m > 0 and ((lo < 0.0 and partials[m - 1] < 0.0) or (lo > 0.0 and partials[m - 1] > 0.0)):
            y = lo * 2.0
            x = hi + y
            yr = x - hi
            if y == yr:
                hi = x
    return hi, 0


@_kernel
def _prep(a, xm, xh, xl, ex):
    """Mantissa, Dekker halves and exponent of every operand; False on nonfinite."""
    split = 134217729.0
    for idx in range(a.size):
        v = a.flat[idx]
        if not math.isfinite(v):
            return False
        if v == 0.0:
            xm.flat[idx] = 0.0
            xh.flat[idx] = 0.0
            xl.flat[idx] = 0.0
            ex.flat[idx] = 0
        else:
            x, e = math.frexp(v)
            c = split * x
            h = c - (c - x)
            xm.flat[idx] = x
            xh.flat[idx] = h
            xl.flat[idx] = x - h
            ex.flat[idx] = e
    return True


@_kernel
def _residual(x, xh, xl, ex, y, yh, yl, ey, pow2):
    high = x * y
    low = ((xh * yh - high) + xh * yl + xl * yh) + xl * yl
    e = ex + ey
    if low == 0.0:
        return low
    if -1100 <= e < 1100:
        scaled = low * pow2[e + 1100]
        if abs(scaled) >= 2.2250738585072014e-308:
            return scaled
    return math.ldexp(low, e)


@_kernel
def contract_product(a, b, out, pow2):
    m, k = a.shape
    n = b.shape[1]
    ax = np.empty((m, k))
    ah = np.empty((m, k))
    al = np.empty((m, k))
    ae = np.empty((m, k), dtype=np.int64)
    bx = np.empty((k, n))
    bh = np.empty((k, n))
    bl = np.empty((k, n))
    be = np.empty((k, n), dtype=np.int64)
    if not (_prep(a, ax, ah, al, ae) and _prep(b, bx, bh, bl, be)):
        return 1
    buf = np.empty(2 * k)
    partials = np.empty(2 * k + 1)
    for i in range(m):
        for j in range(n):
            for l in range(k):
                av = a[i, l]
                bv = b[l, j]
                product = av * bv
                if not math.isfinite(product):
                    return 1
                buf[2 * l] = product
                if av == 0.0 or bv == 0.0:
                    buf[2 * l + 1] = 0.0
                else:
                    buf[2 * l + 1] = _residual(ax[i, l], ah[i, l], al[i, l], ae[i, l],
                                               bx[l, j], bh[l, j], bl[l, j], be[l, j], pow2)
            v, st = _fsum_buf(buf, 2 * k, partials)
            if st != 0:
                return 1
            out[i, j] = v
    return 0


@_kernel
def contract_weighted(stack, w, out, pow2):
    """out[c] = compensated dot(stack[:, c], w): terms (left) times weights (right)."""
    t, n = stack.shape
    sx = np.empty((t, n))
    sh = np.empty((t, n))
    sl = np.empty((t, n))
    se = np.empty((t, n), dtype=np.int64)
    wx = np.empty(t)
    wh = np.empty(t)
    wl = np.empty(t)
    we = np.empty(t, dtype=np.int64)
    if not (_prep(stack, sx, sh, sl, se) and _prep(w, wx, wh, wl, we)):
        return 1
    buf = np.empty(2 * t)
    partials = np.empty(2 * t + 1)
    for c in range(n):
        for l in range(t):
            av = stack[l, c]
            bv = w[l]
            product = av * bv
            if not math.isfinite(product):
                return 1
            buf[2 * l] = product
            if av == 0.0 or bv == 0.0:
                buf[2 * l + 1] = 0.0
            else:
                buf[2 * l + 1] = _residual(sx[l, c], sh[l, c], sl[l, c], se[l, c],
                                           wx[l], wh[l], wl[l], we[l], pow2)
        v, st = _fsum_buf(buf, 2 * t, partials)
        if st != 0:
            return 1
        out[c] = v
    return 0


@_kernel
def contract_sum(stack, out):
    t, n = stack.shape
    buf = np.empty(t)
    partials = np.empty(t + 1)
    for c in range(n):
        for l in range(t):
            buf[l] = stack[l, c]
        v, st = _fsum_buf(buf, t, partials)
        if st != 0:
            return 1
        out[c] = v
    return 0
