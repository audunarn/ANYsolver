"""Independent one-dimensional H1-dual norms for bounded F03 diagnostics.

This auxiliary Riesz problem is independent of the structural stiffness
and coupling map. Its finite-element norm is an approximation from below,
not a certificate of continuum inf-sup stability. Coordinates are physical
metres on the existing one-metre fixture; L0=1 m is fixed, not mesh-sized.
"""

from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu


def functional_rows(n_mortar: int, family: str,
                    subdivisions: int) -> tuple[sparse.csr_matrix,np.ndarray]:
    """Return scalar actions on an independent continuous P1 trace grid.

    P1: all line hats. Hybrid: interior hats, then endpoint 0 and endpoint 1.
    Enriched: all line hats, then both endpoints (a separate stress comparator).
    Line actions are integrals (metres); endpoint actions are evaluations.
    The returned row measures are h (half h for boundary P1 hats) or 1
    for endpoints. Dividing by them gives dimensionless normalized rows.
    """
    if (type(n_mortar) is not int or not 2<=n_mortar<=16 or
            type(subdivisions) is not int or not 2<=subdivisions<=128 or
            family not in ('P1','hybrid','enriched')):
        raise ValueError('invalid bounded trace-dual layout')
    count=n_mortar*subdivisions
    fine_h=1/count
    indices=list(range(1,n_mortar) if family=='hybrid' else range(n_mortar+1))
    row_by_hat={hat:row for row,hat in enumerate(indices)}
    rows=[]; columns=[]; values=[]
    roots,weights=np.polynomial.legendre.leggauss(2)
    for cell in range(count):
        coarse=cell//subdivisions
        local=cell%subdivisions
        for root,weight in zip(roots,weights):
            t=(root+1)/2
            xi=(local+t)/subdivisions
            for hat,coarse_shape in ((coarse,1-xi),(coarse+1,xi)):
                if hat not in row_by_hat:
                    continue
                for node,fine_shape in ((cell,1-t),(cell+1,t)):
                    rows.append(row_by_hat[hat]); columns.append(node)
                    values.append(fine_h*weight/2*coarse_shape*fine_shape)
    basis_count=len(indices)+(2 if family!='P1' else 0)
    measures=np.full(basis_count,1/n_mortar)
    if family!='hybrid':
        measures[[0,n_mortar]]*=.5
    if family!='P1':
        rows.extend((len(indices),len(indices)+1)); columns.extend((0,count))
        values.extend((1.,1.)); measures[-2:]=1.
    matrix=sparse.coo_matrix((values,(rows,columns)),
                             shape=(basis_count,count+1)).tocsr()
    return matrix,measures


def riesz_matrix(count: int) -> sparse.csc_matrix:
    """Assemble ∫(u v/L0 + L0 u' v') ds, L0=L=1 m, free endpoints."""
    if type(count) is not int or not 2<=count<=2048:
        raise ValueError('invalid auxiliary grid size')
    h=1/count
    diagonal=np.full(count+1,2*h/3+2/h)
    diagonal[[0,-1]]*=.5
    off=np.full(count,h/6-1/h)
    return sparse.diags((off,diagonal,off),(-1,0,1),format='csc')


def dual_gram(n_mortar: int, family: str, subdivisions: int = 16,
              *, normalized: bool = True) -> np.ndarray:
    """Return an approximate scalar dual Gram, including physical endpoints.

    For three work-conjugate scaled-gap channels use kron(gram,I3).
    This norm deliberately does not use C, K, or a reachable-space projector:
    using C K^-1 C.T as both numerator and norm would hide stability loss.
    Increasing subdivisions tests only the auxiliary-norm approximation.
    """
    action,measures=functional_rows(n_mortar,family,subdivisions)
    if normalized:
        action=sparse.diags(1/measures)@action
    inverse=splu(riesz_matrix(n_mortar*subdivisions))
    gram=np.column_stack([action@inverse.solve(action.getrow(i).toarray().ravel())
                          for i in range(action.shape[0])])
    if not np.all(np.isfinite(gram)):
        raise ValueError('nonfinite auxiliary dual Gram')
    return gram
