"""Experimental compiled counterpart of the F03 CSR interval product.

This preserves the scalar operation order of `_product_bounds` but is not a
registered numerical certificate. The full gate needs independent review.
"""

from __future__ import annotations

import numba
import numpy as np
from scipy import sparse


@numba.njit(cache=False, fastmath=False)
def _compiled_arithmetic_signature(sub, normal, amplifier):
    # Operands enter at runtime so a JIT cannot substitute constant results
    # for the FTZ/DAZ-sensitive operations used by the interval kernel.
    return (sub+sub, normal*.5, sub*amplifier,
            (-sub)*amplifier, np.nextafter(0., -np.inf))


@numba.njit(cache=False, fastmath=False)
def _csr_bounds(indptr, indices, data, block):
    rows = len(indptr)-1
    width = block.shape[1]
    low = np.zeros((rows, width), dtype=np.float64)
    high = np.zeros((rows, width), dtype=np.float64)
    for row in range(rows):
        for pointer in range(indptr[row], indptr[row+1]):
            col = indices[pointer]
            value = data[pointer]
            if value == 0.:
                continue
            for channel in range(width):
                product = value*block[col, channel]
                low_product = np.nextafter(product, -np.inf)
                high_product = np.nextafter(product, np.inf)
                low[row, channel] = np.nextafter(
                    low[row, channel]+low_product, -np.inf)
                high[row, channel] = np.nextafter(
                    high[row, channel]+high_product, np.inf)
    return low, high


def compiled_product_bounds(matrix: sparse.csr_matrix,
                            block: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if (not sparse.isspmatrix_csr(matrix) or
            not isinstance(block, np.ndarray) or block.dtype != np.float64 or
            block.ndim != 2 or block.shape[0] != matrix.shape[1] or
            not np.isfinite(matrix.data).all() or not np.isfinite(block).all()):
        raise ValueError("finite CSR and float64 inverse block required")
    if (matrix.indptr.shape != (matrix.shape[0]+1,) or
            matrix.indptr[0] != 0 or matrix.indptr[-1] != len(matrix.data) or
            len(matrix.indices) != len(matrix.data) or
            np.any(matrix.indptr[1:] < matrix.indptr[:-1]) or
            (len(matrix.indices) and
             (np.min(matrix.indices) < 0 or
              np.max(matrix.indices) >= matrix.shape[1]))):
        raise ValueError("invalid CSR structure for compiled interval product")
    sub = np.nextafter(0., 1.)
    normal = np.finfo(np.float64).tiny
    amplifier = 2.**350
    if _compiled_arithmetic_signature(sub, normal, amplifier) != (
            2*sub, np.ldexp(1., -1023), np.ldexp(1., -724),
            -np.ldexp(1., -724), -sub):
        raise ArithmeticError("compiled gradual-underflow arithmetic required")
    low, high = _csr_bounds(matrix.indptr, matrix.indices, matrix.data, block)
    if not np.isfinite(low).all() or not np.isfinite(high).all():
        raise ArithmeticError("nonfinite compiled interval enclosure")
    return low, high
