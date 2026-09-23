"""Experimental compiled counterpart of the F03 CSR interval product.

This preserves the scalar operation order of `_product_bounds` but is not a
registered numerical certificate. The full gate needs independent review.
"""

from __future__ import annotations

import numba
import numpy as np
from scipy import sparse


@numba.njit(cache=False, fastmath=False)
def _csr_bounds(indptr, indices, data, block):
    n, width = block.shape
    low = np.zeros((n, width), dtype=np.float64)
    high = np.zeros((n, width), dtype=np.float64)
    for row in range(n):
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
            block.shape[0] != matrix.shape[1] or block.ndim != 2 or
            not np.isfinite(matrix.data).all() or not np.isfinite(block).all()):
        raise ValueError("finite CSR and float64 inverse block required")
    return _csr_bounds(matrix.indptr, matrix.indices, matrix.data, block)
