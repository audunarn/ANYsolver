"""Separate spatial second-variation reference about a planar arch equilibrium.

Derived from Simo-Reissner strain definitions using a spatial Exp chart;
no native tangent, mass, mixed-cell or recovery imports. Linear hyperelastic
section and fixed spatial dead force only. Same authorship, not qualification.
"""
from dataclasses import dataclass
from time import monotonic
import numpy as np
from scipy.linalg import eigh
from numpy.polynomial import legendre


def skew(v):
    x,y,z=v
    return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])


def station_tangent(q,r_s,v0,kappa,section):
    """Gradient/Hessian in [v_s,omega,omega_s], including prestress terms."""
    q=np.asarray(q,dtype=float); r=np.asarray(r_s,dtype=float); v0=np.asarray(v0,dtype=float)
    kappa=np.asarray(kappa,dtype=float); c=np.asarray(section,dtype=float)
    if (q.shape!=(3,3) or r.shape!=(3,) or v0.shape!=(3,) or kappa.shape!=(3,) or c.shape!=(6,6)
            or not all(np.isfinite(a).all() for a in (q,r,v0,kappa,c))
            or np.max(abs(q.T@q-np.eye(3)))>1e-11 or abs(np.linalg.det(q)-1)>1e-11
            or np.max(abs(c-c.T))>1e-13*max(1.,np.max(abs(c)))):
        raise ValueError('finite proper director and symmetric section required')
    np.linalg.cholesky(c)
    strain=np.r_[q.T@r-v0,kappa]; stress=c@strain
    b=np.zeros((6,9)); b[:3,:3]=q.T; b[:3,3:6]=q.T@skew(r); b[3:,6:]=q.T
    n=q@stress[:3]; m=q@stress[3:]
    geometric=np.zeros((9,9)); geometric[:3,3:6]=-skew(n); geometric[3:6,:3]=skew(n)
    geometric[3:6,3:6]=.5*(np.outer(n,r)+np.outer(r,n))-float(n@r)*np.eye(3)
    geometric[3:6,6:]=.5*skew(m); geometric[6:,3:6]=-.5*skew(m)
    return b.T@stress,b.T@c@b+geometric,b.T@c@b,geometric


def quadrature_sites(order):
    if type(order) is not int or not 24<=order<=96: raise ValueError('bounded half-arch quadrature')
    points,weights=legendre.leggauss(order)
    return np.r_[(points-1)/2,(points+1)/2],np.tile(weights/2,2)


def basis(t,degree):
    """Continuous crown trace plus endpoint-zero polynomial bubbles per half."""
    if type(degree) is not int or not 2<=degree<=18: raise ValueError('bounded local Ritz degree')
    left=t<0; s=2*t+(1 if left else -1)
    p=legendre.legvander(np.array([s]),degree)[0]
    dp=np.array([legendre.legval(s,legendre.legder(np.eye(degree+1)[i])) for i in range(degree+1)])
    size=1+2*(degree+1); phi=np.zeros(size); derivative=np.zeros(size)
    phi[0]=1-abs(t); derivative[0]=1 if left else -1
    start=1 if left else degree+2
    phi[start:start+degree+1]=(1-s*s)*p
    derivative[start:start+degree+1]=2*((1-s*s)*dp-2*s*p)
    return phi,derivative


def arch_state(reference,t):
    index=np.flatnonzero(reference.parameter==-abs(t))
    if len(index)!=1: raise ValueError('explicit loaded-reference station absent')
    angle,moment=reference.fields[2:,index[0]]; fx,fy=reference.force
    if t>0: angle,fy=-angle,-fy
    tangent=np.array([np.cos(angle),np.sin(angle),0.]); second=np.array([0.,0.,1.])
    q=np.column_stack((tangent,second,np.cross(tangent,second)))
    normal=fx*np.cos(angle)+fy*np.sin(angle); transverse=-fx*np.sin(angle)+fy*np.cos(angle)
    r_s=q@np.array([1+normal/reference.axial,0.,-transverse/reference.shear])
    return q,r_s,np.array([0.,moment/reference.bending,0.])


@dataclass(frozen=True)
class LoadedRitzResult:
    stiffness: np.ndarray
    mass: np.ndarray
    eigenvalues: np.ndarray
    modes: np.ndarray
    degree: int
    quadrature: int
    displacement: float
    load: float
    residual: float
    material: np.ndarray
    geometric: np.ndarray
    production_qualified: bool=False


def solve(reference,*,degree=12,quadrature=48,count=6):
    if (type(count) is not int or not 1<=count<=12 or quadrature<2*degree+6
            or (reference.height,reference.axial,reference.shear,reference.bending)!=(.1,1.,.4,.0001)):
        raise ValueError('registered nominal loaded arch reference and bounded roots')
    sites,weights=quadrature_sites(quadrature); size=6*(1+2*(degree+1)); started=monotonic()
    c=np.diag([1e6,4e5,4e5,80.,100.,100.]); inertia=np.diag([1.,1.,1.,.02,.01,.01])
    material=np.zeros((size,size)); geometric=np.zeros_like(material); mass=np.zeros_like(material)
    for t,w in zip(sites,weights):
        if monotonic()-started>60.: raise RuntimeError('loaded Ritz construction deadline')
        phi,dphi=basis(float(t),degree); jac=np.sqrt(1+(.2*t)**2)
        q,r_s,kappa=arch_state(reference,float(t)); _,_,km,kg=station_tangent(q,r_s,[1.,0.,0.],kappa,c)
        mapping=np.zeros((9,size)); velocity=np.zeros((6,size))
        for i,(p,dp) in enumerate(zip(phi,dphi)):
            mapping[:3,6*i:6*i+3]=(dp/jac)*np.eye(3)
            mapping[3:6,6*i+3:6*i+6]=p*np.eye(3)
            mapping[6:,6*i+3:6*i+6]=(dp/jac)*np.eye(3)
            velocity[:3,6*i:6*i+3]=p*q.T; velocity[3:,6*i+3:6*i+6]=p*q.T
        measure=float(w*jac); material+=measure*(mapping.T@km@mapping)
        geometric+=measure*(mapping.T@kg@mapping); mass+=measure*(velocity.T@inertia@velocity)
    k=material+geometric
    for a in (k,mass):
        if np.max(abs(a-a.T))>1e-11*max(1.,np.max(abs(a))): raise ValueError('loaded variational symmetry')
    k=(k+k.T)/2; mass=(mass+mass.T)/2
    roots,vectors=eigh(k,mass,subset_by_index=(0,count-1),driver='gvx')
    residual=k@vectors-(mass@vectors)*roots
    scale=np.maximum(1.,np.maximum(np.linalg.norm(material@vectors,axis=0),
        np.maximum(np.linalg.norm(geometric@vectors,axis=0),np.linalg.norm((mass@vectors)*roots,axis=0))))
    error=float(np.max(np.linalg.norm(residual,axis=0)/scale))
    if not np.isfinite(error) or error>1e-8: raise RuntimeError('loaded continuum Ritz residual')
    for i in range(len(roots)):
        if vectors[int(np.argmax(abs(vectors[:,i]))),i]<0: vectors[:,i]*=-1
    for a in (k,mass,roots,vectors,material,geometric): a.setflags(write=False)
    return LoadedRitzResult(k,mass,roots,vectors,degree,quadrature,reference.displacement,
        float(1e6*reference.load),error,material,geometric)
