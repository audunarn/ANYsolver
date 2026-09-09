"""Factor the supplied virgin generalized Hessian, not an independent element.

Numerical diagnosis only: retained constitutive/kinematic factor separation.
No loaded-state substitution, production mutation or reference qualification.
"""
import numpy as np

def virgin_chain(high,low,residual):
    high=np.array(high,dtype=float,copy=True);low=np.array(low,dtype=float,copy=True)
    residual=np.array(residual,dtype=float,copy=True)
    if high.shape!=(42,42) or low.shape!=(42,42) or residual.shape!=(42,):
        raise ValueError('complete generalized virgin Hessian required')
    if not all(np.isfinite(x).all() for x in (high,low,residual)):
        raise ValueError('finite generalized virgin data')
    h=high+low
    if np.any(residual) or np.any(h[:24,:24]):
        raise ValueError('zero-stress zero-geometric-Hessian diagnostic only')
    if not np.array_equal(h,h.T):raise ValueError('symmetric generalized virgin Hessian')
    compliance=-h[24:,24:]
    root=np.linalg.cholesky(compliance)
    left=np.linalg.solve(root,np.eye(18));right=h[24:,:24].copy()
    for a in (left,right,compliance):a.setflags(write=False)
    return left,right,compliance
