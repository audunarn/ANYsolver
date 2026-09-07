"""Separate 3D Simo-Reissner end-couple IVP, no ANYsolver imports.

An initially parabolic cantilever has zero spatial force and constant spatial
moment. Integrate r'=J Q(e1+gamma), Q'=J Q hat(kappa0+kappa). A coupled
linear section gives [gamma,kappa]=C^-1[0,Q.T M]. This is not production
mechanics, independent authorship, multiprecision or a stability certificate.
"""
from dataclasses import dataclass
from time import monotonic
import numpy as np
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class ReferenceResult:
    height: float
    section: np.ndarray
    moment: np.ndarray
    parameter: np.ndarray
    positions: np.ndarray
    frames: np.ndarray
    strains: np.ndarray
    resultants: np.ndarray
    strain_energy: float
    profile: str
    evaluations: int
    orthogonality_error: float
    production_qualified: bool = False


def matrix(values, shape):
    raw=np.asarray(values,dtype=object)
    if raw.shape!=shape or any(type(x) not in (int,float) for x in raw.flat):
        raise ValueError('finite numeric reference array; booleans forbidden')
    data=np.asarray(raw,dtype=float)
    if not np.isfinite(data).all(): raise ValueError('finite reference array')
    return data


def skew(v):
    x,y,z=v
    return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])


def reference_frame(t,height):
    tangent=np.array([1.,-2*height*t,0.]); tangent/=np.linalg.norm(tangent)
    return np.column_stack((tangent,[0.,0.,1.],np.cross(tangent,[0.,0.,1.])))


def solve(section,moment,samples,*,height=.15,profile='IVP11',max_evaluations=4000,max_seconds=60.):
    c=matrix(section,(6,6)); m=matrix(moment,(3,)); x=matrix(samples,(len(samples),))
    if (type(height) not in (int,float) or not np.isfinite(height) or not 0<=height<=.25
            or not 2<=len(x)<=4097 or x[0]!=-1. or x[-1]!=1. or np.any(np.diff(x)<=0)):
        raise ValueError('registered parabolic geometry and ordered bounded samples')
    if np.max(abs(c-c.T))>1e-13*max(1.,float(np.max(abs(c)))): raise ValueError('symmetric section required')
    np.linalg.cholesky(c)
    if (profile not in ('IVP9','IVP11') or type(max_evaluations) is not int or not 0<=max_evaluations<=4000
            or type(max_seconds) not in (float,int) or not np.isfinite(max_seconds) or not 0<=max_seconds<=60.):
        raise ValueError('bounded explicit reference integration profile')
    relative=1e-9 if profile=='IVP9' else 1e-11
    absolute=1e-11 if profile=='IVP9' else 1e-13
    compliance=np.linalg.solve(c,np.eye(6)); started=monotonic(); evaluations=0
    def rhs(t,state):
        nonlocal evaluations
        if evaluations>=max_evaluations or monotonic()-started>=max_seconds:
            raise RuntimeError('reference evaluation/time budget exhausted; no retry')
        evaluations+=1
        q=state[3:12].reshape(3,3); resultant=np.r_[np.zeros(3),q.T@m]
        strain=compliance@resultant
        jacobian=np.sqrt(1+(2*height*t)**2)
        curvature=np.array([0.,-2*height/(1+(2*height*t)**2)**1.5,0.])
        dx=jacobian*(q@(np.array([1.,0.,0.])+strain[:3]))
        dq=jacobian*q@skew(curvature+strain[3:])
        return np.r_[dx,dq.ravel(),.5*jacobian*float(strain@resultant)]
    initial=np.r_[[-1.,0.,0.],reference_frame(-1.,height).ravel(),0.]
    answer=solve_ivp(rhs,(-1.,1.),initial,method='DOP853',rtol=relative,atol=absolute,t_eval=x)
    if not answer.success or answer.y.shape!=(13,len(x)) or not np.isfinite(answer.y).all():
        raise RuntimeError('incomplete finite reference IVP')
    positions=answer.y[:3].T.copy(); frames=answer.y[3:12].T.reshape(-1,3,3).copy()
    error=float(np.max(abs(frames.transpose(0,2,1)@frames-np.eye(3))))
    if error>20*relative or np.max(abs(np.linalg.det(frames)-1.))>20*relative:
        raise RuntimeError('reference director integration lost SO(3); no projection or retry')
    resultants=np.concatenate((np.zeros((len(x),3)),np.einsum('nji,j->ni',frames,m)),axis=1)
    strains=(compliance@resultants.T).T
    if np.min(1+strains[:,0])<=0: raise RuntimeError('reference inverted material stretch')
    for data in (c,m,x,positions,frames,strains,resultants): data.setflags(write=False)
    return ReferenceResult(float(height),c,m,x,positions,frames,strains,resultants,
        float(answer.y[-1,-1]),profile,evaluations,error)
