"""Bounded supported-energy stability diagnostic for the classical F03 line.

This evaluates a fixed elastic reference operator without a loaded solve.
Finite-dimensional beta is not uniform inf-sup qualification or a native
B3-GE/E4-PL coupling result.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import linalg, sparse
from scipy.sparse import linalg as sparse_linalg

import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_kkt_scaling as scaling


def p1_norm(nm: int) -> tuple[np.ndarray,np.ndarray,dict]:
    """Exact P1 mass and H-minus-one-half dual norm on the unit line."""
    if not isinstance(nm,int) or not 1<=nm<=128:
        raise ValueError('unsupported stability multiplier count')
    h=1/nm
    diagonal=np.full(nm+1,2*h/3)
    diagonal[[0,-1]]=h/3
    m=sparse.diags((np.full(nm,h/6),diagonal,np.full(nm,h/6)),
                   offsets=(-1,0,1)).toarray()
    diagonal=np.full(nm+1,2/h)
    diagonal[[0,-1]]=1/h
    g=sparse.diags((np.full(nm,-1/h),diagonal,np.full(nm,-1/h)),
                   offsets=(-1,0,1)).toarray()
    mu,v=linalg.eigh(g,m,check_finite=True)
    if mu[0]<-1e-10*max(1.,mu[-1]):
        raise ValueError('negative P1 derivative norm eigenvalue')
    orth=float(np.max(np.abs(v.T@m@v-np.eye(nm+1))))
    if orth>1e-10:
        raise ValueError('P1 mass-orthonormal basis failed')
    mv=m@v
    r=(mv*np.power(1+np.maximum(mu,0.),-.5))@mv.T
    skew=float(np.max(np.abs(r-r.T))/max(np.max(np.abs(r)),1e-300))
    if skew>1e-10:
        raise ValueError('P1 dual norm is asymmetric')
    r=(r+r.T)/2
    r3=np.kron(r,np.eye(3))
    m3=np.kron(m,np.eye(3))
    eigen=linalg.eigvalsh(r,check_finite=True)
    if eigen[0]<=0:
        raise ValueError('P1 dual norm is not positive')
    info=dict(p1_mass_trace=float(np.trace(m)),
              p1_derivative_zero=float(mu[0]),
              p1_derivative_max=float(mu[-1]),
              mass_orthogonality_error=orth,dual_skew=skew,
              dual_min_eigen=float(eigen[0]),
              dual_max_eigen=float(eigen[-1]))
    return m3,r3,info


def analyze(ns: int,ny: int,nb: int,nm: int,topology: str,
            *,batch: int=16,retain_matrices: bool=False) -> dict | tuple[dict,dict]:
    """Assemble supported sparse energy and form a bounded Schur diagnostic."""
    if (topology not in ('Q4','CST-CB') or
            not 1<=ns<=128 or not 2<=ny<=64 or
            not 1<=nb<=512 or nm not in (64,128) or
            not 1<=batch<=32):
        raise ValueError('unsupported stability diagnostic case')
    model=shell.panel(ns,ny,topology)
    ks=shell.stiffness(model)
    kb=beam.assembled_stiffness(nb)
    cs,cb,overlay=line.coupling(model,nb,nm,'P1')
    k=sparse.block_diag((ks,kb),format='csr')
    c=sparse.hstack((-cs,cb),format='csr')
    supports=np.r_[model.supported,model.dof_count+beam.root_dofs(nb)]
    free=np.setdiff1d(np.arange(k.shape[0]),supports)
    scaled=scaling.build(k,c,np.zeros(k.shape[0]),free,model.dof_count,
                         nb,nm,'P1')
    n=len(free); m=c.shape[0]
    kbar=scaled.matrix[:n,:n].tocsc()
    d=scaled.physical_coordinate_scale
    b=(c[:,free]@sparse.diags(d/scaling.U0)).tocsr()
    if (n!=2*(2*ns+1)*(ny+1)+beam.dof_count(nb)-len(supports)
            or m!=3*(nm+1) or b.shape!=(m,n)):
        raise ValueError('stability dimensions differ from assembled layout')
    skew=kbar-kbar.T
    k_skew=float(np.max(np.abs(skew.data))/max(np.max(np.abs(kbar.data)),1e-300)
                 if skew.nnz else 0.)
    if k_skew>1e-10:
        raise ValueError('supported elastic stiffness is asymmetric')
    lu=sparse_linalg.splu(kbar)
    inverse=sparse_linalg.LinearOperator(kbar.shape,matvec=lu.solve,
                                         dtype=np.float64)
    near_zero,modes=sparse_linalg.eigsh(kbar,k=2,sigma=0.,which='LM',
                                        OPinv=inverse,tol=1e-8,maxiter=3000)
    mode_res=np.linalg.norm(kbar@modes-modes*near_zero[None,:],axis=0)/np.maximum(
        np.linalg.norm(kbar@modes,axis=0)+
        np.linalg.norm(modes*near_zero[None,:],axis=0),1e-300)
    if not np.all(np.isfinite(near_zero)) or np.min(near_zero)<=0:
        raise ValueError('nonpositive or unresolved supported energy mode')
    s=np.empty((m,m))
    residuals=[]
    for start in range(0,m,batch):
        stop=min(start+batch,m)
        rhs=b[start:stop].T.toarray()
        solution=lu.solve(rhs)
        error=kbar@solution-rhs
        norm=np.linalg.norm(error,axis=0)/np.maximum(np.linalg.norm(rhs,axis=0),1e-300)
        residuals.extend(norm.tolist())
        s[:,start:stop]=b@solution
    s_skew=float(np.max(np.abs(s-s.T))/max(np.max(np.abs(s)),1e-300))
    if s_skew>1e-10:
        raise ValueError('supported Schur is asymmetric')
    s=(s+s.T)/2  # roundoff only, after the unmodified skew is checked
    mass,dual,norm_info=p1_norm(nm)
    values,v=linalg.eigh(s,dual,check_finite=True)
    if not np.all(np.isfinite(values)):
        raise ValueError('nonfinite generalized stability eigenvalues')
    se=s@v; re=dual@v*values[None,:]
    eig_res=np.linalg.norm(se-re,axis=0)/np.maximum(
        np.linalg.norm(se,axis=0)+np.linalg.norm(re,axis=0),1e-300)
    l2=linalg.eigh(s,mass,eigvals_only=True,check_finite=True)
    smallest=float(values[0]);largest=float(values[-1])
    screening_margin=20*largest*(max(residuals)+max(eig_res)+s_skew)
    numeric_pass=(max(residuals)<=1e-9 and max(eig_res)<=1e-8 and
                  max(mode_res)<=1e-8 and
                  smallest>max(1e-10*largest,screening_margin,0.) and
                  math.isfinite(largest))
    answer=dict(mesh=dict(n_s=ns,n_y=ny,n_beam=nb,n_mortar=nm),
                topology=topology,physical_free=n,multiplier_rows=m,
                kkt_dimension=n+m,kbar_nnz=kbar.nnz,coupling_nnz=c.nnz,
                overlay_intervals=len(overlay)-1,
                kbar_skew=k_skew,
                supported_near_zero_eigenvalues=sorted(map(float,near_zero)),
                max_supported_mode_residual=float(max(mode_res)),
                schur_skew=s_skew,
                max_stiffness_solve_residual=float(max(residuals)),
                max_generalized_eigen_residual=float(max(eig_res)),
                minimum_generalized_eigen=smallest,
                maximum_generalized_eigen=largest,
                minimum_eigen_screening_margin=float(max(1e-10*largest,
                                                         screening_margin)),
                beta_min=math.sqrt(smallest) if smallest>0 else None,
                beta_max=math.sqrt(largest) if largest>0 else None,
                beta_ratio=math.sqrt(smallest/largest)
                if smallest>0 and largest>0 else None,
                l2_minimum_generalized_eigen=float(l2[0]),
                l2_maximum_generalized_eigen=float(l2[-1]),
                numerical_checks_pass=bool(numeric_pass),
                norm=norm_info)
    if retain_matrices:
        return answer,dict(schur=s.copy(),dual=dual.copy(),mass=mass.copy())
    return answer
