"""Bounded classical shell/beam Schur decomposition for G0B diagnosis.

No loaded solve, native GE coupling, or multiplier-space qualification is
performed. The two supported primal domains are independent before tying.
"""

from __future__ import annotations

import numpy as np
from scipy import linalg, sparse
from scipy.sparse import linalg as sparse_linalg

import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_kkt_scaling as scaling
import _b3_e4_f03_nm128_stability as stability


def decompose(ns: int, ny: int, nb: int, nm: int,
              topology: str, *, retain_matrices: bool=False) -> dict | tuple[dict,dict]:
    """Evaluate bounded primal contributions in the frozen P1 dual norm."""
    if (topology not in ('Q4','CST-CB') or not 1<=ns<=16 or
            not 2<=ny<=16 or not 1<=nb<=128 or not 1<=nm<=128):
        raise ValueError('unsupported bounded axial patch')
    model=shell.panel(ns,ny,topology)
    ks=shell.stiffness(model)
    kb=beam.assembled_stiffness(nb)
    cs,cb,_=line.coupling(model,nb,nm,'P1')
    k=sparse.block_diag((ks,kb),format='csr')
    c=sparse.hstack((-cs,cb),format='csr')
    supports=np.r_[model.supported,model.dof_count+beam.root_dofs(nb)]
    free=np.setdiff1d(np.arange(k.shape[0]),supports)
    compiled=scaling.build(k,c,np.zeros(k.shape[0]),free,model.dof_count,
                           nb,nm,'P1')
    n=len(free)
    split=int(np.count_nonzero(free<model.dof_count))
    kbar=compiled.matrix[:n,:n].tocsc()
    scale=max(float(np.max(np.abs(kbar.data),initial=0.)),1e-300)
    skew=kbar-kbar.T
    kbar_skew=float(np.max(np.abs(skew.data),initial=0.))/scale
    cross_error=max(float(np.max(np.abs(kbar[:split,split:].data),initial=0.)),
                    float(np.max(np.abs(kbar[split:,:split].data),initial=0.)))
    if kbar_skew>1e-10 or cross_error>1e-12*scale:
        raise ValueError('primal blocks are asymmetric or not independent')
    b=(c[:,free]@sparse.diags(
        compiled.physical_coordinate_scale/scaling.U0)).tocsr()
    parts=[]
    solve_residuals=[]
    for lo,hi in ((0,split),(split,n)):
        klocal=kbar[lo:hi,lo:hi].tocsc()
        local=b[:,lo:hi].tocsr()
        lu=sparse_linalg.splu(klocal)
        rhs=local.T.toarray()
        solution=lu.solve(rhs)
        solve_residuals.append(float(np.max(np.linalg.norm(
            klocal@solution-rhs,axis=0)/np.maximum(
                np.linalg.norm(rhs,axis=0),1e-300))))
        contribution=local@solution
        skew=float(np.max(np.abs(contribution-contribution.T))/
                   max(np.max(np.abs(contribution)),1e-300))
        if not np.all(np.isfinite(contribution)) or skew>1e-10:
            raise ValueError('invalid side Schur contribution')
        parts.append((contribution+contribution.T)/2)
    ss,sb=parts
    s=ss+sb
    _,dual,_=stability.p1_norm(nm)
    axial=np.arange(0,3*(nm+1),3)
    lambdas,vectors=linalg.eigh(s[np.ix_(axial,axial)],
                                dual[np.ix_(axial,axial)],check_finite=True)
    v=vectors[:,0]
    axial_s=s[np.ix_(axial,axial)]
    axial_r=dual[np.ix_(axial,axial)]
    eigen_residual=float(np.linalg.norm(axial_s@v-lambdas[0]*axial_r@v)/
                         max(np.linalg.norm(axial_s@v)+
                             np.linalg.norm(lambdas[0]*axial_r@v),1e-300))
    side_spectra=[linalg.eigh(part[np.ix_(axial,axial)],axial_r,
                             eigvals_only=True,check_finite=True)
                  for part in (ss,sb)]
    side_minima=[float(values[0]) for values in side_spectra]
    side_scales=[float(max(abs(values[0]),abs(values[-1])))
                 for values in side_spectra]
    side_status=[('near_zero_unresolved' if abs(value)<=1e-10*scale else
                  'positive' if value>0 else 'negative_witness')
                 for value,scale in zip(side_minima,side_scales)]
    shell_action=float(v@ss[np.ix_(axial,axial)]@v)
    beam_action=float(v@sb[np.ix_(axial,axial)]@v)
    result=dict(topology=topology,mesh=dict(n_s=ns,n_y=ny,n_beam=nb,n_mortar=nm),
                axial_minimum_generalized_eigen=float(lambdas[0]),
                axial_beta=float(np.sqrt(lambdas[0])) if lambdas[0]>0 else None,
                axial_shell_action=shell_action,
                axial_beam_action=beam_action,
                axial_shell_fraction=shell_action/(shell_action+beam_action),
                split_free=(split,n-split),
                primal_cross_block_max=cross_error,
                primal_skew=kbar_skew,
                max_side_solve_residual=max(solve_residuals),
                axial_eigen_residual=eigen_residual,
                side_alone_axial_minima=side_minima,
                side_alone_axial_scales=side_scales,
                side_alone_axial_status=side_status)
    if retain_matrices:
        return result,dict(shell=ss.copy(),beam=sb.copy(),
                           total=s.copy(),dual=dual.copy())
    return result
