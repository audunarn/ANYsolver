"""Separate continuum reference-linear Ritz operator; no native mechanics.

Spatial variation fields v,omega give gamma=R0.T(v_s+tangent cross omega),
kappa=R0.T omega_s. Integrate their coupled section energy and physical mass.
Global Legendre trial fields differ from the native discontinuous-cell map.
This is a binary64 convergence reference, not an exact or independent-review
certificate. Root-clamped or free-boundary straight/parabolic cases only.
"""
from dataclasses import dataclass
from time import monotonic
import numpy as np
from scipy.linalg import eigh
from numpy.polynomial import legendre


@dataclass(frozen=True)
class RitzResult:
    stiffness: np.ndarray
    mass: np.ndarray
    eigenvalues: np.ndarray
    modes: np.ndarray
    degree: int
    quadrature: int
    clamped: bool
    height: float
    residual: float
    production_qualified: bool=False


def positive_matrix(value):
    a=np.asarray(value,dtype=float)
    if a.shape!=(6,6) or not np.isfinite(a).all() or np.max(abs(a-a.T))>1e-13*max(1.,np.max(abs(a))):
        raise ValueError('finite symmetric six-dimensional physical section')
    np.linalg.cholesky(a); return a


def skew(v):
    x,y,z=v
    return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])


def build(section,inertia,*,degree=14,quadrature=64,height=.15,clamped=True):
    if (type(degree) is not int or not 2<=degree<=24 or type(quadrature) is not int
            or not 2*degree+4<=quadrature<=128 or type(clamped) is not bool
            or type(height) not in (int,float) or not np.isfinite(height) or not 0<=height<=.25):
        raise ValueError('bounded explicit Ritz family')
    c=positive_matrix(section); density=positive_matrix(inertia); start=monotonic()
    points,weights=legendre.leggauss(quadrature); values=legendre.legvander(points,degree)
    derivatives=np.column_stack([legendre.legval(points,legendre.legder(np.eye(degree+1)[i])) for i in range(degree+1)])
    if clamped:
        derivatives=(1+points[:,None])*derivatives+values
        values=(1+points[:,None])*values
    size=6*(degree+1); k=np.zeros((size,size)); mass=np.zeros_like(k)
    for t,w,phi,dphi in zip(points,weights,values,derivatives):
        if monotonic()-start>30.: raise RuntimeError('Ritz reference construction deadline')
        jac=np.sqrt(1+(2*height*t)**2); tangent=np.array([1.,-2*height*t,0.])/jac
        frame=np.column_stack((tangent,[0.,0.,1.],np.cross(tangent,[0.,0.,1.])))
        strain=np.zeros((6,size)); velocity=np.zeros((6,size))
        for i,(value,derivative) in enumerate(zip(phi,dphi)):
            strain[:3,6*i:6*i+3]=frame.T*(derivative/jac)
            strain[:3,6*i+3:6*i+6]=frame.T@skew(tangent)*value
            strain[3:,6*i+3:6*i+6]=frame.T*(derivative/jac)
            velocity[:3,6*i:6*i+3]=frame.T*value
            velocity[3:,6*i+3:6*i+6]=frame.T*value
        k+=float(w*jac)*(strain.T@c@strain)
        mass+=float(w*jac)*(velocity.T@density@velocity)
    for a in (k,mass):
        if np.max(abs(a-a.T))>1e-11*max(1.,np.max(abs(a))): raise ValueError('Ritz variational symmetry lost')
    # Roundoff symmetrization only after checking the unsymmetrized variational
    # assembly. This does not add stiffness, remove modes or alter quadrature.
    return (k+k.T)/2,(mass+mass.T)/2


def solve(section,inertia,*,degree=14,quadrature=64,height=.15,clamped=True,count=6):
    if type(count) is not int or not 1<=count<=12: raise ValueError('bounded reference root count')
    k,m=build(section,inertia,degree=degree,quadrature=quadrature,height=height,clamped=clamped)
    roots,vectors=eigh(k,m,subset_by_index=(0,count-1),driver='gvx')
    residual=k@vectors-(m@vectors)*roots
    scale=np.maximum(1.,np.maximum(np.linalg.norm(k@vectors,axis=0),np.linalg.norm((m@vectors)*roots,axis=0)))
    error=float(np.max(np.linalg.norm(residual,axis=0)/scale))
    if not np.isfinite(error) or error>1e-8: raise RuntimeError('Ritz reference eigenvector residual')
    for i in range(len(roots)):
        if vectors[int(np.argmax(abs(vectors[:,i]))),i]<0: vectors[:,i]*=-1
    for a in (k,m,roots,vectors): a.setflags(write=False)
    return RitzResult(k,m,roots,vectors,degree,quadrature,clamped,float(height),error)
