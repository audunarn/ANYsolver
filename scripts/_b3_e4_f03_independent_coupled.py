"""Small, independent classical plane-stress/beam weak-line solve for F03.

Only bounded preflight systems belong here. It is neither a native coupling
operator nor an executed qualification reference.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve

import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell


@dataclass(frozen=True)
class Solution:
    shell: np.ndarray
    beam: np.ndarray
    multipliers: np.ndarray
    shell_reactions: np.ndarray
    beam_reactions: np.ndarray
    weak_gap: np.ndarray
    algebraic_residual_ratio: float
    weak_compatibility_ratio: float
    shell_energy: float
    beam_energy: float
    external_work: float


def solve(model: shell.Panel, n_beam: int, n_mortar: int,
          law: str, loading: str, *, equilibrate: bool = False) -> Solution:
    """Solve one explicitly small constrained saddle system from fresh parts."""
    if model.n_s>64 or model.n_y>64 or n_beam>128 or n_mortar>64:
        raise ValueError('only bounded derivation preflight systems admitted')
    ks=shell.stiffness(model)
    kb=beam.assembled_stiffness(n_beam)
    cs,cb,_=line.coupling(model,n_beam,n_mortar,law)
    c=sparse.hstack((-cs,cb),format='csr')
    k=sparse.block_diag((ks,kb),format='csr')
    f=np.r_[np.zeros(model.dof_count),beam.assembled_load(n_beam,loading)]
    supported=np.r_[model.supported,model.dof_count+beam.root_dofs(n_beam)]
    free=np.setdiff1d(np.arange(k.shape[0]),supported)
    a=sparse.bmat(((k[free,:][:,free],c[:,free].T),
                   (c[:,free],None)),format='csc')
    right=np.r_[f[free],np.zeros(c.shape[0])]
    if equilibrate:
        diagonal=np.ones(a.shape[0])
        scaled=a.tocsr()
        for _ in range(6):
            rowmax=np.asarray(abs(scaled).max(axis=1).toarray()).ravel()
            if not np.all(np.isfinite(rowmax)) or np.any(rowmax<=0.):
                raise ValueError('invalid mixed-system row equilibration')
            step=1/np.sqrt(rowmax)
            diagonal*=step
            transform=sparse.diags(step,format='csr')
            scaled=(transform@scaled@transform).tocsr()
        result=diagonal*spsolve(scaled.tocsc(),diagonal*right)
    else:
        result=spsolve(a,right)
    if not np.all(np.isfinite(result)):
        raise ValueError('nonfinite independent coupled preflight response')
    q=np.zeros(k.shape[0]); q[free]=result[:len(free)]
    lam=result[len(free):]
    residual=k@q+c.T@lam-f
    algebraic_residual_ratio=float(np.linalg.norm(residual[free])/
        max(np.linalg.norm((k@q)[free]),np.linalg.norm((c.T@lam)[free]),
            np.linalg.norm(f[free]),1.))
    weak_compatibility_ratio=float(np.linalg.norm(c@q)/
        max(np.linalg.norm(cs@q[:model.dof_count]),
            np.linalg.norm(cb@q[model.dof_count:]),1e-16))
    qs=q[:model.dof_count].copy(); qb=q[model.dof_count:].copy()
    reactions=np.zeros_like(q); reactions[supported]=residual[supported]
    rs=reactions[:model.dof_count].copy()
    rb=reactions[model.dof_count:].copy()
    return Solution(qs,qb,lam,rs,rb,c@q,algebraic_residual_ratio,
                    weak_compatibility_ratio,
                    float(.5*qs@(ks@qs)),float(.5*qb@(kb@qb)),float(f@q))
