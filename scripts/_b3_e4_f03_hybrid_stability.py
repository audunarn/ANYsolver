"""Bounded dimensionless Schur/independent-trace-norm diagnostics.

No production inf-sup threshold is assigned. Matrices here are small
interface oracles; the structural stiffness remains sparse and is solved
column by column. No inverse or structural dense matrix is constructed.
"""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy

import numpy as np
from scipy import linalg, sparse
from scipy.sparse.linalg import splu


def _symmetric(matrix: np.ndarray, name: str) -> None:
    if (matrix.ndim!=2 or matrix.shape[0]!=matrix.shape[1] or
            not np.all(np.isfinite(matrix))):
        raise ValueError(f'invalid {name}')
    if np.linalg.norm(matrix-matrix.T)>1e-9*np.linalg.norm(matrix):
        raise ValueError(f'{name} is not symmetric within the frozen criterion')


def _structural_schur(primal: sparse.spmatrix,
                      constraint: sparse.spmatrix) -> tuple[np.ndarray,float]:
    """Sparse structural inverse actions, one interface column at a time."""
    factor=splu(primal.tocsc())
    schur=np.empty((constraint.shape[0],constraint.shape[0]))
    worst=0.
    for j in range(constraint.shape[0]):
        rhs=constraint.getrow(j).toarray().ravel()
        response=factor.solve(rhs)
        residual=primal@response-rhs
        worst=max(worst,float(np.linalg.norm(residual)/max(np.linalg.norm(rhs),1e-30)))
        schur[:,j]=constraint@response
    _symmetric(schur,'structural Schur')
    return schur,worst


def _spectrum(schur: np.ndarray, scalar_gram: np.ndarray
              ) -> tuple[np.ndarray,np.ndarray]:
    gram=np.kron(scalar_gram,np.eye(3))
    eigenvalues=linalg.eigvalsh(schur,gram)
    if not np.all(np.isfinite(eigenvalues)):
        raise ValueError('nonfinite normalized Schur spectrum')
    return eigenvalues,gram


def diagnose(primal: sparse.spmatrix, constraint: sparse.spmatrix,
             gram32: np.ndarray, gram64: np.ndarray) -> tuple[dict,np.ndarray]:
    """Compare dimensionless C K^-1 C.T to an independent scalar H1 dual Gram.

    The caller uses Kbar=D.T K D/E0 and Cbar=diag(1/(U0*m))*C*D.
    Gram rows use the same measure m, including m=1 for endpoint atoms.
    The three channels are [x,y,ell*yaw]; ell is the fixed port length.
    """
    _symmetric(gram32,'coarse trace Gram'); _symmetric(gram64,'fine trace Gram')
    if (gram32.shape!=gram64.shape or
            constraint.shape[0]!=3*len(gram64) or
            primal.shape!=(constraint.shape[1],)*2):
        raise ValueError('inconsistent structural and trace-norm layouts')
    # Positive-definite checks are intentional: no diagonal repair or clipping.
    linalg.cholesky(gram32,lower=True)
    linalg.cholesky(gram64,lower=True)
    ratios=linalg.eigvalsh(gram64,gram32)
    norm_change=float(np.max(np.abs(ratios-1)))
    schur,worst=_structural_schur(primal,constraint)
    eigenvalues,gram=_spectrum(schur,gram64)
    return {'auxiliary_squared_norm_change':norm_change,
            'auxiliary_status':('RESOLVED_AT_REGISTERED_LEVELS' if norm_change<=1e-3
                                else 'UNRESOLVED_AUXILIARY_NORM'),
            'structural_solve_relative_residual':worst,
            'generalized_eigenvalues':eigenvalues.tolist(),
            'minimum_beta_diagnostic':(float(np.sqrt(eigenvalues[0]))
                                       if eigenvalues[0]>0 else None),
            'scope':'finite-model diagnostic; no continuum inf-sup acceptance'},gram


def diagnose_analytic(primal: sparse.spmatrix, constraint: sparse.spmatrix,
                      scalar_gram: np.ndarray, *, norm_identity: dict,
                      matrix_sink: Callable[[np.ndarray,np.ndarray],None] | None = None
                      ) -> tuple[dict,np.ndarray]:
    """Use the independently analytic free-end full-H1 scalar trace Gram.

    No FE-grid resolution status or surrogate 32/64 norm difference is
    assigned. The returned identity binds the normalized auxiliary norm's
    source implementation and row layout, without changing physical rows.
    The optional hook receives owned copies of the small Schur and full
    three-channel Gram matrices after the spectrum is computed.
    """
    _symmetric(scalar_gram,'analytic full-H1 trace Gram')
    if (constraint.shape[0]!=3*len(scalar_gram) or
            primal.shape!=(constraint.shape[1],)*2 or
            not isinstance(norm_identity,dict) or
            norm_identity.get('kind')!='piecewise_analytic_full_H1_free_endpoint' or
            norm_identity.get('normalized_rows') is not True or
            len(norm_identity.get('source_sha256',''))!=64 or
            len(norm_identity.get('row_measures',()))!=len(scalar_gram)):
        raise ValueError('inconsistent analytic norm identity or layout')
    linalg.cholesky(scalar_gram,lower=True)
    schur,worst=_structural_schur(primal,constraint)
    eigenvalues,gram=_spectrum(schur,scalar_gram)
    if matrix_sink is not None:
        matrix_sink(schur.copy(),gram.copy())
    return {'norm_source':'analytic_h1',
            'norm_identity':deepcopy(norm_identity),
            'auxiliary_status':'PIECEWISE_ANALYTIC_FLOATING',
            'structural_solve_relative_residual':worst,
            'generalized_eigenvalues':eigenvalues.tolist(),
            'minimum_beta_diagnostic':(float(np.sqrt(eigenvalues[0]))
                                       if eigenvalues[0]>0 else None),
            'scope':'finite-model diagnostic; no continuum inf-sup acceptance'},gram


def normalized_kkt(primal: sparse.spmatrix, constraint: sparse.spmatrix,
                   rhs: np.ndarray) -> tuple[sparse.csc_matrix,np.ndarray]:
    if (primal.shape!=(constraint.shape[1],)*2 or rhs.shape!=(primal.shape[0],) or
            not np.all(np.isfinite(primal.data)) or
            not np.all(np.isfinite(constraint.data)) or not np.all(np.isfinite(rhs))):
        raise ValueError('invalid dimensionless KKT layout')
    return (sparse.bmat(((primal,constraint.T),(constraint,None)),format='csc'),
            np.r_[rhs,np.zeros(constraint.shape[0])])
