"""Separate 3D continuum dead-line BVP; no ANYsolver mechanics imports.

n_s + f = 0, m_s + r_s cross n = 0. For a free tip, n=f*(L-s).
r_s=Q(e1+gamma), Q_s=Q hat(kappa0+kappa), [gamma,kappa]=C^-1[Q^T n,Q^T m].
Integrate the directors without projection. Algorithmic independence does not
mean independent authorship/review or a multiprecision reference certificate.
"""
from dataclasses import dataclass
from time import monotonic
import numpy as np
from scipy.integrate import solve_bvp


@dataclass(frozen=True)
class ReferenceResult:
    height: float
    section: np.ndarray
    force: np.ndarray
    parameter: np.ndarray
    positions: np.ndarray
    frames: np.ndarray
    strains: np.ndarray
    resultants: np.ndarray
    spatial_forces: np.ndarray
    spatial_moments: np.ndarray
    strain_energy: float
    profile: str
    evaluations: int
    mesh_nodes: int
    boundary_error: float
    differential_error: float
    orthogonality_error: float
    production_qualified: bool = False


def array(value, shape):
    data=np.asarray(value,dtype=object)
    if data.shape!=shape or any(type(x) not in (int,float) for x in data.flat):
        raise ValueError('explicit numeric reference data; no booleans')
    made=np.array(value,dtype=float,copy=True)
    if not np.isfinite(made).all(): raise ValueError('finite reference data required')
    return made


def arclength_primitive(t,height):
    t=np.asarray(t,dtype=float)
    if height==0.: return t.copy()
    a=2*height
    return .5*(t*np.sqrt(1+(a*t)**2)+np.arcsinh(a*t)/a)


def reference_frames(t,height):
    t=np.asarray(t,dtype=float); tangent=np.column_stack((np.ones(len(t)),-2*height*t,np.zeros(len(t))))
    tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    second=np.tile([0.,0.,1.],(len(t),1))
    return np.stack((tangent,second,np.cross(tangent,second)),axis=2)


def hats(values):
    made=np.zeros((len(values),3,3)); x,y,z=values.T
    made[:,0,1]=-z; made[:,0,2]=y; made[:,1,0]=z
    made[:,1,2]=-x; made[:,2,0]=-y; made[:,2,1]=x
    return made


def solve(section,force,samples,*,height=.15,profile='BVP9',max_evaluations=4000,max_seconds=60.):
    c=array(section,(6,6)); f=array(force,(3,)); samples=array(samples,(len(samples),))
    if (type(height) not in (int,float) or not np.isfinite(height) or not 0<=height<=.25
            or not 2<=len(samples)<=4097 or samples[0]!=-1. or samples[-1]!=1.
            or np.any(np.diff(samples)<=0)):
        raise ValueError('registered parabolic geometry and ordered explicit sample grid')
    if np.max(abs(c-c.T))>1e-13*max(1.,float(np.max(abs(c)))): raise ValueError('symmetric reference section')
    np.linalg.cholesky(c)
    if (profile not in ('BVP7','BVP9') or type(max_evaluations) is not int or not 0<=max_evaluations<=4000
            or type(max_seconds) not in (int,float) or not np.isfinite(max_seconds) or not 0<=max_seconds<=60.):
        raise ValueError('bounded reference profile required')
    tolerance,limit={'BVP7':(1e-7,1025),'BVP9':(1e-9,4097)}[profile]
    compliance=np.linalg.solve(c,np.eye(6)); started=monotonic(); evaluations=0
    end=float(arclength_primitive(1.,height)); initial_frame=reference_frames([-1.],height)[0]

    def fields(t,state):
        q=state[3:12].T.reshape(-1,3,3); m=state[12:15].T
        n=(end-arclength_primitive(t,height))[:,None]*f
        stress=np.concatenate((np.einsum('nji,nj->ni',q,n),np.einsum('nji,nj->ni',q,m)),axis=1)
        return q,n,m,stress,stress@compliance.T

    def rhs(t,state):
        nonlocal evaluations
        if evaluations>=max_evaluations or monotonic()-started>=max_seconds:
            raise RuntimeError('reference evaluation/time budget exhausted; no retry')
        evaluations+=1
        q,n,m,stress,strain=fields(t,state)
        jacobian=np.sqrt(1+(2*height*t)**2)
        kappa=strain[:,3:].copy(); kappa[:,1]-=2*height/jacobian**3
        dr=jacobian[:,None]*np.einsum('nij,nj->ni',q,strain[:,:3]+[1.,0.,0.])
        dq=jacobian[:,None,None]*(q@hats(kappa))
        dm=-np.cross(dr,n)
        energy=.5*jacobian*np.einsum('ni,ni->n',stress,strain)
        return np.vstack((dr.T,dq.reshape(-1,9).T,dm.T,energy))

    def boundary(left,right):
        return np.r_[left[:3]-[-1.,0.,0.],left[3:12]-initial_frame.ravel(),right[12:15],left[15]]

    grid=np.linspace(-1.,1.,33)
    guess=np.zeros((16,len(grid))); guess[:3]=np.array([grid,height*(1-grid**2),np.zeros(len(grid))])
    guess[3:12]=reference_frames(grid,height).reshape(-1,9).T
    answer=solve_bvp(rhs,boundary,grid,guess,tol=tolerance,bc_tol=tolerance,max_nodes=limit)
    if not answer.success or not np.isfinite(answer.y).all():
        raise RuntimeError('incomplete continuum line-load BVP; no retry')
    state=answer.sol(samples)
    q,n,m,stress,strain=fields(samples,state)
    orthogonality=float(max(np.max(abs(q.transpose(0,2,1)@q-np.eye(3))),np.max(abs(np.linalg.det(q)-1.))))
    boundary_error=float(np.max(abs(boundary(state[:,0],state[:,-1]))))
    differential_error=float(np.max(abs(answer.sol(samples,1)-rhs(samples,state))/(1+abs(rhs(samples,state)))))
    if orthogonality>20*tolerance or boundary_error>tolerance or differential_error>20*tolerance:
        raise RuntimeError('reference director/boundary/differential check failed; no projection or retry')
    if np.min(1+strain[:,0])<=0: raise RuntimeError('reference material stretch inverted')
    positions=state[:3].T.copy(); energy=float(state[15,-1])
    for data in (c,f,samples,positions,q,strain,stress,n,m): data.setflags(write=False)
    return ReferenceResult(float(height),c,f,samples,positions,q,strain,stress,n,m,energy,
        profile,evaluations,len(answer.x),boundary_error,differential_error,orthogonality)
