"""Sparse producer of *candidate* factors for the separate positivity proof.

SuperLU is a general factorization, not a positivity oracle. The complete
stored primal matrix is subsequently compared with L diag(d) L.T exactly.
No physical equilibrium RHS or dense global operator is created here.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from types import MappingProxyType

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

from scripts import _b3_e4_f03_sparse_certificate as common
from scripts import _b3_e4_f03_sparse_positivity as positivity


@dataclass(frozen=True, slots=True)
class FactorBudget:
    sparse_budget: common.SparseBudget
    max_factor_nnz: int
    max_factor_storage_bytes: int

    def __post_init__(self):
        if (type(self.sparse_budget) is not common.SparseBudget or
                any(type(v) is not int or v <= 0 for v in
                    (self.max_factor_nnz, self.max_factor_storage_bytes))):
            raise ValueError('explicit sparse factor resource budget required')


def _digest_owned(matrix):
    digest = hashlib.sha256(b'F03_CANONICAL_CSR_BINARY64_V1\0')
    for array, dtype in ((matrix.shape, '<i8'), (matrix.indptr, '<i8'),
                         (matrix.indices, '<i8'), (matrix.data, '<f8')):
        value = np.asarray(array, dtype=dtype)
        digest.update(value.tobytes(order='C'))
    return digest.hexdigest()


def _permutation(value, n):
    if (type(value) is not np.ndarray or value.shape != (n,) or
            value.dtype not in (np.dtype('int32'), np.dtype('int64'))):
        raise ValueError('bounded native integer permutation required')
    value = value.copy()
    if (np.any(value < 0) or np.any(value >= n) or
            not np.array_equal(np.sort(value), np.arange(n))):
        raise ValueError('native factor permutation is not complete')
    return np.frombuffer(value.astype(np.int64).tobytes(), dtype=np.int64)


def _bytes(matrix):
    return matrix.data.nbytes+matrix.indices.nbytes+matrix.indptr.nbytes


def _native_factor(value, budget):
    if type(value) not in (sparse.csr_matrix, sparse.csc_matrix,
                           sparse.csr_array, sparse.csc_array):
        raise ValueError('supported native compressed sparse factor required')
    rows, cols = value.shape
    if rows != cols or not 1 <= rows <= budget.max_order:
        raise ValueError('native factor shape exceeds declared budget')
    data, indices, pointer = value.data, value.indices, value.indptr
    if (any(type(a) is not np.ndarray or a.ndim != 1 for a in (data, indices, pointer))
            or data.dtype != np.float64
            or indices.dtype not in (np.dtype('int32'), np.dtype('int64'))
            or pointer.dtype not in (np.dtype('int32'), np.dtype('int64'))
            or len(data) != len(indices) or len(data) > min(rows*cols, budget.max_nnz)
            or len(pointer) != rows+1):
        raise ValueError('invalid bounded native factor buffers')
    common._workspace(rows, cols, len(data), 1, budget)
    data, indices, pointer = data.copy(), indices.copy(), pointer.copy()
    if (pointer[0] != 0 or pointer[-1] != len(data) or
            np.any(pointer < 0) or np.any(pointer > len(data)) or
            np.any(pointer[1:] < pointer[:-1]) or
            np.any(indices < 0) or np.any(indices >= rows)):
        raise ValueError('invalid native factor pointer/index structure')
    if not np.isfinite(data).all():
        raise ValueError('finite native factor entries required')
    # SuperLU may return valid unordered compressed columns. Normalize by
    # index permutation only, before native traversal. Never sum duplicates.
    for lo, hi in zip(pointer, pointer[1:]):
        order = np.argsort(indices[lo:hi], kind='stable')
        ordered = indices[lo:hi][order]
        if np.any(ordered[1:] == ordered[:-1]):
            raise ValueError('duplicate native factor entries are inadmissible')
        indices[lo:hi], data[lo:hi] = ordered, data[lo:hi][order]
    cls = sparse.csr_matrix if type(value) in (sparse.csr_matrix, sparse.csr_array) else sparse.csc_matrix
    # An empty bounded shell receives only already-checked buffers. The
    # common validator rechecks canonical order before native conversion.
    wrapper = cls((rows, cols), dtype=np.float64)
    wrapper.data, wrapper.indices, wrapper.indptr = data, indices, pointer
    return common.validate_sparse(wrapper, budget)


@dataclass(frozen=True, slots=True, init=False)
class FactorCandidate:
    _matrix: object
    _lower: object
    _upper: object
    _diagonal: np.ndarray
    _row_map: np.ndarray
    _column_map: np.ndarray
    _permutation: tuple
    _metadata: object

    def __init__(self, *args, **kwargs):
        raise TypeError('use produce to construct owned candidate factors')

    @property
    def matrix(self): return self._matrix.copy()
    @property
    def lower(self): return self._lower.copy()
    @property
    def upper(self): return self._upper.copy()
    @property
    def diagonal(self): return self._diagonal.copy()
    @property
    def row_map(self): return self._row_map.copy()
    @property
    def column_map(self): return self._column_map.copy()
    @property
    def permutation(self): return self._permutation
    @property
    def metadata(self): return self._metadata


def produce(kbar, budget):
    """One LU; all fill/storage caps are observations after factor creation.

    Scientific use requires external factor time/RSS supervision. This
    function cannot bound opaque native workspace from post-factor sizes.
    Exceptions propagate unchanged; no fallback ordering/pivoting or retry.
    """
    if type(budget) is not FactorBudget:
        raise ValueError('explicit factor resource budget required')
    matrix = common.validate_sparse(kbar, budget.sparse_budget)
    n = matrix.shape[0]
    if 2*n > budget.max_factor_nnz or 32*n+8 > budget.max_factor_storage_bytes:
        raise ValueError('minimum factor inventory exceeds declared budget')
    common._workspace(n, n, matrix.nnz, 1, budget.sparse_budget)
    factor = splu(matrix.tocsc(), permc_spec='MMD_AT_PLUS_A',
        diag_pivot_thresh=0., options={'Equil': False, 'SymmetricMode': True,
                                     'IterRefine': 'NOREFINE'})
    # Extract once. Validating native outputs is still required before
    # subsequent sparse traversal; cached flags are not an ownership contract.
    lower = _native_factor(factor.L, budget.sparse_budget)
    upper = _native_factor(factor.U, budget.sparse_budget)
    if lower.shape != (n, n) or upper.shape != (n, n):
        raise ValueError('native factor shape mismatch')
    count = lower.nnz+upper.nnz
    storage = _bytes(lower)+_bytes(upper)
    if count > budget.max_factor_nnz or storage > budget.max_factor_storage_bytes:
        raise ValueError('observed factor fill/storage exceeds declared budget')
    rows = _permutation(factor.perm_r, n)
    cols = _permutation(factor.perm_c, n)
    # SuperLU's maps are old -> new. The proof requires the inverse gather:
    # K[order][:,order] = P K P.T, where order = argsort(old_to_new).
    order = tuple(int(i) for i in np.argsort(cols))
    diagonal = upper.diagonal()
    if not np.isfinite(diagonal).all():
        raise ArithmeticError('nonfinite native factor diagonal')
    for i in range(n):
        a, b = lower.indptr[i:i+2]
        indices, values = lower.indices[a:b], lower.data[a:b]
        if (np.any(indices > i) or np.count_nonzero(indices == i) != 1
                or values[indices == i][0] != 1.):
            raise ValueError('native lower factor is not unit triangular')
        a, b = upper.indptr[i:i+2]
        if np.any(upper.indices[a:b] < i):
            raise ValueError('native upper factor is not triangular')
    reason = (None if np.array_equal(rows, cols) else
              'native row and column permutations differ')
    if reason is None and np.any(diagonal <= 0):
        reason = 'native congruence candidate has nonpositive diagonal'
    metadata = dict(status='CANDIDATE_CREATED' if reason is None else 'HOLD',
        reason=reason, matrix_sha256=_digest_owned(matrix),
        lower_sha256=_digest_owned(lower), upper_sha256=_digest_owned(upper),
        ordering='MMD_AT_PLUS_A', pivot_threshold=0., equilibration=False,
        symmetric_mode=True, iterative_refinement='NOREFINE',
        factor_preparation='validated stable index permutation; no value arithmetic',
        factorization_count=1, rhs_solve_count=0, factor_nnz=count,
        factor_storage_bytes=storage, qualification_status='NOT_QUALIFIED')
    result = object.__new__(FactorCandidate)
    for name, value in (('_matrix', matrix), ('_lower', lower), ('_upper', upper),
            ('_diagonal', np.frombuffer(diagonal.tobytes(), dtype=np.float64)),
            ('_row_map', rows), ('_column_map', cols), ('_permutation', order),
            ('_metadata', MappingProxyType(metadata))):
        object.__setattr__(result, name, value)
    return result


def verify_against(kbar, factors, budget):
    """Bind to a supplied matrix, then run the independent full-residual proof."""
    if type(factors) is not FactorCandidate or type(budget) is not positivity.PositivityBudget:
        raise ValueError('owned factors and explicit positivity budget required')
    matrix = common.validate_sparse(kbar, budget.sparse_budget)
    if _digest_owned(matrix) != factors.metadata['matrix_sha256']:
        raise ValueError('positivity factor matrix identity mismatch')
    if factors.metadata['status'] != 'CANDIDATE_CREATED':
        return {'status': 'HOLD', 'reason': factors.metadata['reason'],
                'matrix_sha256': factors.metadata['matrix_sha256'],
                'factor_metadata': dict(factors.metadata), 'proof': None}
    proof = positivity.certify_positive(matrix, factors._lower,
        factors._diagonal, factors._permutation, budget=budget)
    return {'status': proof['status'], 'reason': proof['reason'],
            'matrix_sha256': factors.metadata['matrix_sha256'],
            'factor_metadata': dict(factors.metadata), 'proof': proof}
