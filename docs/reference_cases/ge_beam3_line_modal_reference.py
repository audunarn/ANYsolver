"""Separate continuum Ritz spectrum about the curved line-load BVP state.

Spatial fields v and omega are independent. The fixed dead-line potential is
linear in r+epsilon*v, so its continuum second variation is zero. Prestress
still enters the internal second variation. This differs consistently from
the nonlinear lifted centerline map of the discrete beam. No native imports.
"""
from dataclasses import dataclass
from time import monotonic
import numpy as np
from numpy.polynomial import legendre
from scipy.linalg import eigh
from docs.reference_cases.ge_beam3_dead_line_reference import ReferenceResult, array
from docs.reference_cases.ge_beam3_loaded_ritz_reference import station_tangent, skew


@dataclass(frozen=True)
class ModalReference:
    stiffness: np.ndarray
    mass: np.ndarray
    eigenvalues: np.ndarray
    modes: np.ndarray
    material: np.ndarray
    geometric: np.ndarray
    inertia: np.ndarray
    degree: int
    quadrature: int
    height: float
    force: np.ndarray
    residual: float
    production_qualified: bool = False
    external_hessian_policy: str = 'ZERO_FOR_ADDITIVE_SPATIAL_POSITION_VARIATION'


def sites(order):
    if type(order) is not int or not 24<=order<=96: raise ValueError('bounded continuum modal quadrature')
    return legendre.leggauss(order)


def balanced_station(q,strain,section,n,m):
    """Use BVP-balanced prestress, not roundoff in Q.T@Q as a false stress.

The continuum equations carry spatial n,m as independent equilibrium fields.
Validate their constitutive identity before constructing the geometric terms.
No director projection, stress clipping or accepted tolerance change occurs.
"""
    strain=array(strain,(6,)); n=array(n,(3,)); m=array(m,(3,))
    stress=section@strain; pulled=np.r_[q.T@n,q.T@m]
    if np.linalg.norm(stress-pulled)>1e-11*max(1.,np.linalg.norm(pulled)):
        raise ValueError('continuum prestress and section strain disagree')
    r_s=q@(np.array([1.,0.,0.])+strain[:3])
    _,_,material,_=station_tangent(q,r_s,[1.,0.,0.],strain[3:],section)
    geometric=np.zeros((9,9)); geometric[:3,3:6]=-skew(n); geometric[3:6,:3]=skew(n)
    geometric[3:6,3:6]=.5*(np.outer(n,r_s)+np.outer(r_s,n))-float(n@r_s)*np.eye(3)
    geometric[3:6,6:]=.5*skew(m); geometric[6:,3:6]=-.5*skew(m)
    return material,geometric


def build(reference,inertia,*,degree=14,quadrature=64):
    if (type(reference) is not ReferenceResult or reference.profile!='BVP9' or reference.production_qualified is not False
            or type(degree) is not int or not 2<=degree<=20 or type(quadrature) is not int
            or not 2*degree+4<=quadrature<=96):
        raise ValueError('explicit bounded loaded continuum profile')
    density=array(inertia,(6,6))
    if np.max(abs(density-density.T))>1e-13*max(1.,np.max(abs(density))): raise ValueError('symmetric physical inertia')
    np.linalg.cholesky(density)
    points,weights=sites(quadrature); values=legendre.legvander(points,degree)
    derivatives=np.column_stack([legendre.legval(points,legendre.legder(np.eye(degree+1)[i])) for i in range(degree+1)])
    derivatives=(1+points[:,None])*derivatives+values; values=(1+points[:,None])*values
    size=6*(degree+1); material=np.zeros((size,size)); geometric=np.zeros_like(material); mass=np.zeros_like(material)
    started=monotonic()
    for t,w,phi,dphi in zip(points,weights,values,derivatives):
        if monotonic()-started>60.: raise RuntimeError('loaded continuum modal construction deadline')
        indices=np.flatnonzero(reference.parameter==float(t))
        if len(indices)!=1: raise ValueError('exact explicit equilibrium sample absent; no historical interpolation')
        index=int(indices[0]); q=reference.frames[index]; strain=reference.strains[index]
        km,kg=balanced_station(q,strain,reference.section,reference.spatial_forces[index],reference.spatial_moments[index])
        jac=np.sqrt(1+(2*reference.height*t)**2); mapping=np.zeros((9,size)); velocity=np.zeros((6,size))
        for i,(p,dp) in enumerate(zip(phi,dphi)):
            mapping[:3,6*i:6*i+3]=(dp/jac)*np.eye(3)
            mapping[3:6,6*i+3:6*i+6]=p*np.eye(3)
            mapping[6:,6*i+3:6*i+6]=(dp/jac)*np.eye(3)
            velocity[:3,6*i:6*i+3]=p*q.T; velocity[3:,6*i+3:6*i+6]=p*q.T
        measure=float(w*jac)
        material+=measure*(mapping.T@km@mapping); geometric+=measure*(mapping.T@kg@mapping)
        mass+=measure*(velocity.T@density@velocity)
    k=material+geometric
    for a in (k,mass):
        if not np.isfinite(a).all() or np.max(abs(a-a.T))>1e-11*max(1.,np.max(abs(a))):
            raise ValueError('finite symmetric continuum variational operator')
    return (k+k.T)/2,(mass+mass.T)/2,material,geometric,density


def solve(reference,inertia,*,degree=14,quadrature=64,count=6):
    if type(count) is not int or not 1<=count<=12: raise ValueError('bounded signed mode count')
    started=monotonic()
    k,m,material,geometric,density=build(reference,inertia,degree=degree,quadrature=quadrature)
    roots,vectors=eigh(k,m,subset_by_index=(0,count-1),driver='gvx')
    # Measure the serialized sign/layout, not LAPACK's transient Fortran layout.
    vectors=np.array(vectors,order='C',copy=True)
    for i in range(len(roots)):
        if vectors[int(np.argmax(abs(vectors[:,i]))),i]<0: vectors[:,i]*=-1
    residual=k@vectors-(m@vectors)*roots
    scale=np.maximum(1.,np.maximum(np.linalg.norm(material@vectors,axis=0),
        np.maximum(np.linalg.norm(geometric@vectors,axis=0),np.linalg.norm((m@vectors)*roots,axis=0))))
    error=float(np.max(np.linalg.norm(residual,axis=0)/scale))
    if monotonic()-started>60. or not np.isfinite(error) or error>1e-8:
        raise RuntimeError('loaded continuum modal residual/deadline')
    for a in (k,m,roots,vectors,material,geometric,density): a.setflags(write=False)
    return ModalReference(k,m,roots,vectors,material,geometric,density,degree,quadrature,reference.height,
        reference.force,error)
