"""Full spatial continuum energy variation; no discrete beam imports.

Derived from r_t=r+t*u, R_t=Exp(t*hat(theta))*R and material Simo-Reissner
strains. This is separate implementation, not independent author review.
Primes denote reference arclength derivatives. Only conservative elastic
material potential plus spatial dead force work is covered here.
"""
import numpy as np


def skew(v):
    x,y,z=v
    return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])


def inputs(frame,section,velocity,force,moment):
    r=np.asarray(frame,dtype=float);c=np.asarray(section,dtype=float)
    vectors=[np.asarray(v,dtype=float) for v in (velocity,force,moment)]
    if (r.shape!=(3,3) or c.shape!=(6,6) or not np.isfinite(r).all()
            or not np.isfinite(c).all() or not np.array_equal(c,c.T)
            or any(v.shape!=(3,) or not np.isfinite(v).all() for v in vectors)):
        raise ValueError('finite frame, symmetric section and spatial vectors')
    if np.max(abs(r.T@r-np.eye(3)))>1e-11 or abs(np.linalg.det(r)-1)>1e-11:
        raise ValueError('proper physical frame required; no normalization')
    np.linalg.cholesky(c)
    return r,c,*vectors


def blocks(frame,section,velocity,force,moment):
    """Hessian density q'.D.q' + 2*q'.B.q + q.F.q, q=(u,theta)."""
    r,c,v,n,m=inputs(frame,section,velocity,force,moment)
    rotation=np.kron(np.eye(2),r);d=rotation@c@rotation.T
    vhat,nhat,mhat=map(skew,(v,n,m))
    t=np.zeros((6,6));t[:3,3:]=vhat
    g=np.zeros((6,6));g[:3,3:]=-nhat;g[3:,3:]=-.5*mhat
    f=t.T@d@t;f[3:,3:]+=.5*(nhat@vhat+vhat@nhat)
    return d,d@t+g,f


def generator(frame,section,velocity,force,moment):
    """Canonical (q,p) Jacobi generator. p=D*q'+B*q, not raw moment delta."""
    d,b,f=blocks(frame,section,velocity,force,moment)
    s=np.linalg.solve(d,np.eye(6));a=-s@b
    return np.block([[a,s],[f-b.T@s@b,-a.T]])


def direct_density(frame,section,velocity,force,moment,q,dq):
    """Cross-product variation, evaluated without the block construction."""
    r,c,v,n,m=inputs(frame,section,velocity,force,moment)
    q=np.asarray(q,dtype=float);dq=np.asarray(dq,dtype=float)
    if q.shape!=(6,) or dq.shape!=(6,) or not np.isfinite(q).all() or not np.isfinite(dq).all():
        raise ValueError('finite six-component variation and arclength derivative')
    theta=q[3:];du=dq[:3];dt=dq[3:]
    first=np.r_[r.T@(du-np.cross(theta,v)),r.T@dt]
    return float(first@c@first+n@(np.cross(theta,np.cross(theta,v))-2*np.cross(theta,du))
                 -m@np.cross(theta,dt))


def variation_basis(x,jac,order):
    """Smooth H1_0 fields: six spatial components, every sine mode in each.

    These are diagnostic Ritz trial functions, not the production interpolation.
    Zero end values are assigned exactly; no interior controller is imposed.
    """
    if (type(order) is not int or not 1<=order<=32 or not np.isfinite(x)
            or not -1<=x<=1 or not np.isfinite(jac) or jac<=0):
        raise ValueError('bounded admissible trial basis')
    k=np.arange(1,order+1)*np.pi/2
    values=np.sin(k*(x+1)) if -1<x<1 else np.zeros(order)
    derivative=k*np.cos(k*(x+1))/jac
    return np.kron(np.eye(6),values[None,:]),np.kron(np.eye(6),derivative[None,:])
