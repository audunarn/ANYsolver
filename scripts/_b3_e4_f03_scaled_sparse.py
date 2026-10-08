"""Owned classical scaling and one sparse candidate solve; no qualification.

The factor is a general LU. Positivity, numerical certification, mechanical
acceptance and scientific execution registration are deliberately separate.
The native factor workspace needs an external time/RSS supervisor before
scientific use; a post-factor fill cap is not a peak-memory guarantee.
"""
from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu

from scripts import _b3_e4_f03_sparse_certificate as check
from scripts import _b3_e4_f03_spatial_contract as c


def _owned_array(value):
    return np.frombuffer(value.tobytes(), dtype=np.float64).reshape(value.shape)


def _scale_matrix(matrix, row_scale, col_scale, denominator=1.):
    result = matrix.copy()
    for row in range(result.shape[0]):
        lo, hi = result.indptr[row:row+2]
        # Fixed left-then-right arithmetic; never average paired entries.
        original = result.data[lo:hi].copy()
        result.data[lo:hi] = ((original*row_scale[row]) *
                              col_scale[result.indices[lo:hi]])/denominator
        if (not np.isfinite(result.data[lo:hi]).all() or
                np.any((original != 0) & (result.data[lo:hi] == 0))):
            raise ArithmeticError('nonfinite/underflowed nonzero scaled entry')
    return result


@dataclass(frozen=True, slots=True, init=False)
class ScaledSystem:
    _stiffness: object
    _root: object
    _matrix: object
    _rhs: np.ndarray
    _diagonal: np.ndarray
    _root_scale: np.ndarray
    _metadata: object

    def __init__(self, *args, **kwargs):
        raise TypeError('use prepare to own a scaled system')

    @property
    def stiffness(self): return self._stiffness.copy()
    @property
    def root(self): return self._root.copy()
    @property
    def matrix(self): return self._matrix.copy()
    @property
    def rhs(self): return self._rhs.copy()
    @property
    def diagonal(self): return self._diagonal.copy()
    @property
    def root_scale(self): return self._root_scale.copy()
    @property
    def metadata(self): return self._metadata


def prepare(shell, beam, root, force, budget, *, reference=None):
    """Prepare Kbar, Cbar and H with fixed held energy/force/moment scales.

    Optional reference freezes its D/R for an integration crosscheck; it
    never recomputes a different scaling from the alternate diagonal.
    This preparation records no symmetry, rank or positivity acceptance.
    """
    ks = check.validate_sparse(shell, budget)
    kb = check.validate_sparse(beam, budget)
    cc = check.validate_sparse(root, budget, square=False)
    n = ks.shape[0]
    if kb.shape != (n, n) or cc.shape != (3, n) or n+3 > budget.max_order:
        raise ValueError('matching primal blocks and exactly three root rows required')
    force = check._vector(force, n, 'physical force')
    # Reserve for the input sum before constructing it. Its union can be
    # smaller than the sum of input counts when shell/beam patterns overlap.
    input_upper = ks.nnz+kb.nnz+2*cc.nnz
    check._workspace(n+3, n+3, input_upper, 1, budget)
    stiffness = ks+kb
    if stiffness.nnz+2*cc.nnz > budget.max_nnz:
        raise ValueError('combined sparse pattern envelope exceeds budget')
    diagonal = stiffness.diagonal()
    if not np.isfinite(diagonal).all() or np.any(diagonal <= 0):
        raise ValueError('strictly positive finite supported stiffness diagonal required')
    if reference is None:
        d = np.sqrt(c.E0/diagonal)
        r = np.array([1/c.U0, 1/c.U0, .46/c.U0])
    else:
        if type(reference) is not ScaledSystem or reference._stiffness.shape != (n, n):
            raise ValueError('same-size owned primary scaling required')
        d, r = reference.diagonal, reference.root_scale
    if not np.isfinite(d).all() or np.any(d <= 0) or not np.isfinite(r).all():
        raise ArithmeticError('finite positive scaling required')
    kbar = _scale_matrix(stiffness, d, d, c.E0)
    cbar = _scale_matrix(cc, r, d)
    fbar = d*force/c.E0
    if (not np.isfinite(fbar).all() or np.any((force != 0) & (fbar == 0))):
        raise ArithmeticError('nonfinite/underflowed nonzero scaled load')
    matrix = sparse.bmat(((kbar, cbar.T), (cbar, None)), format='csc')
    if matrix.nnz > budget.max_nnz:
        raise ValueError('combined sparse pattern envelope exceeds budget')
    rhs = np.r_[fbar, np.zeros(3)]
    result = object.__new__(ScaledSystem)
    metadata = {'physical_dofs': n, 'root_multipliers': 3, 'matrix_nnz': matrix.nnz,
        'energy_scale': c.E0, 'displacement_scale': c.U0, 'length_scale': .46,
        'primary_scaling': reference is None, 'qualification_status': 'NOT_QUALIFIED'}
    for key, value in (('_stiffness', kbar), ('_root', cbar), ('_matrix', matrix),
            ('_rhs', _owned_array(rhs)), ('_diagonal', _owned_array(d)),
            ('_root_scale', _owned_array(r)), ('_metadata', MappingProxyType(metadata))):
        object.__setattr__(result, key, value)
    return result


@dataclass(frozen=True, slots=True)
class SolveBudget:
    sparse_budget: check.SparseBudget
    max_factor_nnz: int
    max_inverse_evidence_bytes: int

    def __post_init__(self):
        if (type(self.sparse_budget) is not check.SparseBudget or
                any(type(v) is not int or v <= 0 for v in
                    (self.max_factor_nnz, self.max_inverse_evidence_bytes))):
            raise ValueError('explicit sparse solve/evidence budgets required')


class SparseCandidate:
    __slots__ = ('_system', '_factor', '_z', '_q', '_eta', '_budget',
                 '_inverse_started', '_work')

    def __init__(self, *args, **kwargs):
        raise TypeError('use solve_candidate for an unqualified sparse candidate')

    @property
    def z(self): return self._z.copy()
    @property
    def q(self): return self._q.copy()
    @property
    def eta(self): return self._eta.copy()
    @property
    def work(self): return dict(self._work)

    def inverse_blocks(self):
        """One-pass column inventory from the same factor, with RHS accounting."""
        if self._inverse_started:
            raise RuntimeError('inverse-column stream already started; no implicit retry')
        self._inverse_started = True
        n = len(self._z)
        block = min(n, self._budget.sparse_budget.max_block_columns)
        for start in range(0, n, block):
            width = min(block, n-start)
            rhs = np.zeros((n, width))
            rhs[np.arange(start, start+width), np.arange(width)] = 1.
            self._work['certificate_rhs_attempted'] += width
            self._work['certificate_solve_calls'] += 1
            value = self._factor.solve(rhs)
            if (type(value) is not np.ndarray or value.dtype != np.float64 or
                    value.shape != (n, width) or not np.isfinite(value).all()):
                raise ArithmeticError('invalid inverse-column solve response')
            self._work['certificate_rhs_completed'] += width
            yield start, value.copy()


def solve_candidate(system, budget):
    """Exactly one general LU and one candidate RHS; no acceptance implied."""
    if type(system) is not ScaledSystem or type(budget) is not SolveBudget:
        raise ValueError('owned scaled system and explicit solve budget required')
    h = check.validate_sparse(system._matrix, budget.sparse_budget).tocsc()
    n = h.shape[0]
    if 8*n*n > budget.max_inverse_evidence_bytes:
        raise ValueError('complete inverse-column raw evidence exceeds budget')
    check._workspace(n, n, h.nnz, min(n, budget.sparse_budget.max_block_columns),
                     budget.sparse_budget)
    # No generic exception translation: backend, memory and programming
    # exceptions remain distinguishable to the future run supervisor.
    factor = splu(h, permc_spec='COLAMD', diag_pivot_thresh=1.,
                  options={'Equil': False, 'IterRefine': 'NOREFINE'})
    factor_nnz = int(factor.L.nnz+factor.U.nnz)
    if factor_nnz > budget.max_factor_nnz:
        raise ValueError('observed factor fill exceeds budget')
    z = factor.solve(system._rhs.copy())
    z = check._vector(z, n, 'candidate state')
    nq = len(system._diagonal)
    q = system._diagonal*z[:nq]
    eta = c.E0*system._root_scale*z[nq:]
    if (not np.isfinite(q).all() or not np.isfinite(eta).all() or
            np.any((z[:nq] != 0) & (q == 0)) or
            np.any((z[nq:] != 0) & (eta == 0))):
        raise ArithmeticError('nonfinite/underflowed recovered candidate coordinates')
    result = object.__new__(SparseCandidate)
    result._system, result._factor, result._budget = system, factor, budget
    result._z, result._q, result._eta = map(_owned_array, (z, q, eta))
    result._inverse_started = False
    result._work = {'factorizations': 1, 'factor_nnz': factor_nnz,
        'candidate_rhs_solves': 1, 'certificate_solve_calls': 0,
        'certificate_rhs_attempted': 0, 'certificate_rhs_completed': 0,
        'qualification_status': 'NOT_QUALIFIED'}
    return result
