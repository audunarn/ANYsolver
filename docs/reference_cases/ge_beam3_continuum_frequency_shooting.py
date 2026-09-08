"""Separate continuum shooting reference; no ANYsolver mechanics imports.

Author-derived first variation of the linear reference Simo-Reissner energy.
Spatial unknowns are y=(u,theta,n,m). q'=Aq+Sf, f'=-lambda Jq-A.T f.
This is independently implemented, not independently authored/reviewed.
"""
from dataclasses import dataclass
from time import monotonic
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

PROFILES={'ODE11':(1e-11,1e-13,1e-9),'ODE13':(1e-13,1e-15,1e-11)}

def matrix(value):
    a=np.array(value,dtype=float,copy=True)
    if a.shape!=(6,6) or not np.isfinite(a).all() or not np.array_equal(a,a.T):
        raise ValueError('finite symmetric six-by-six continuum data')
    np.linalg.cholesky(a)
    return a

def geometry(t,height):
    direction=np.array([1.,-2*height*t,0.]);jac=float(np.linalg.norm(direction))
    tangent=direction/jac
    rotation=np.column_stack((tangent,[0.,0.,1.],np.cross(tangent,[0.,0.,1.])))
    return jac,tangent,np.kron(np.eye(2),rotation)

def generator(t,height,compliance,inertia,eigenvalue):
    jac,tangent,rotation=geometry(t,height)
    x,y,z=tangent
    cross=np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])
    a=np.zeros((6,6));a[:3,3:]=-cross
    return jac*np.block([[a,rotation@compliance@rotation.T],
                         [-eigenvalue*rotation@inertia@rotation.T,-a.T]])

@dataclass(frozen=True)
class Reference:
    height: float
    eigenvalues: np.ndarray
    sites: np.ndarray
    fields: np.ndarray
    tip_errors: np.ndarray
    work_errors: np.ndarray
    brackets: np.ndarray
    profile: str
    callbacks: int
    independent_authorship: bool=False
    production_qualified: bool=False

def solve(height,section,inertia,seeds,*,profile='ODE13',sites=None):
    if type(height) is not float or not 0<=height<=.75 or profile not in PROFILES:
        raise ValueError('registered continuum geometry/profile')
    c=matrix(section);j=matrix(inertia);compliance=np.linalg.inv(c)
    seeds=np.array(seeds,dtype=float,copy=True)
    if seeds.shape!=(6,) or not np.isfinite(seeds).all() or np.any(seeds<=0) or np.any(np.diff(seeds)<=0):
        raise ValueError('six positive increasing Ritz frequency seeds')
    sites=np.linspace(-1.,1.,129) if sites is None else np.array(sites,dtype=float,copy=True)
    if (sites.ndim!=1 or not 2<=len(sites)<=2049 or not np.isfinite(sites).all()
            or sites[0]!=-1. or sites[-1]!=1. or np.any(np.diff(sites)<=0)):
        raise ValueError('bounded ordered explicit continuum sites')
    rtol,atol,work_limit=PROFILES[profile]
    start=monotonic();calls=0
    initial=np.vstack((np.zeros((6,6)),np.eye(6)))
    def check():
        if monotonic()-start>60. or calls>60000:
            raise RuntimeError('continuum shooting callback/time bound')
    def integrate(omega,dense=False):
        def rhs(t,y):
            nonlocal calls
            calls+=1;check()
            return (generator(t,height,compliance,j,omega*omega)@y.reshape(12,6)).ravel()
        result=solve_ivp(rhs,(-1.,1.),initial.ravel(),method='DOP853',
            rtol=rtol,atol=atol,dense_output=dense)
        check()
        if not result.success or not np.isfinite(result.y).all():
            raise ValueError('continuum shooting integration failed')
        return result
    def determinant(omega):
        block=integrate(float(omega)).y[:,-1].reshape(12,6)[6:]
        scale=np.linalg.norm(block,axis=0)
        if np.any(scale==0):raise ValueError('degenerate shooting column')
        return float(np.linalg.det(block/scale))
    brackets=np.column_stack((seeds*(1-.002),seeds*(1+.002)))
    if np.any(brackets[:-1,1]>=brackets[1:,0]):raise ValueError('overlapping reference brackets')
    roots=[];fields=[];tip=[];work=[]
    gauss,weights=np.polynomial.legendre.leggauss(96)
    for lo,hi in brackets:
        print(dict(stage='continuum-root',profile=profile,index=len(roots),bracket=[float(lo),float(hi)]),flush=True)
        if not determinant(lo)*determinant(hi)<0:
            raise ValueError('registered Ritz-anchored root bracket failed')
        omega=float(brentq(determinant,float(lo),float(hi),xtol=1e-12,rtol=1e-13,maxiter=60))
        response=integrate(omega,dense=True)
        end=response.y[:,-1].reshape(12,6)
        _,_,right=np.linalg.svd(end[6:])
        force=right[-1].copy()
        if force[np.argmax(np.abs(force))]<0:force=-force
        def sample(parameters):
            fundamental=response.sol(parameters).reshape(12,6,len(parameters))
            return np.einsum('ijk,j->ki',fundamental,force)
        values=sample(gauss);mass=energy=0.
        for t,w,value in zip(gauss,weights,values):
            jac,_,rotation=geometry(float(t),height)
            q,f=value[:6],value[6:]
            mass+=float(w*jac*(q@rotation@j@rotation.T@q))
            energy+=float(w*jac*(f@rotation@compliance@rotation.T@f))
        if not np.isfinite(mass) or mass<=0:raise ValueError('positive continuum modal inertia')
        boundary=float(np.linalg.norm(end[6:]@force)/max(1.,np.linalg.norm(end)*np.linalg.norm(force)))
        error=float(abs(energy-omega*omega*mass)/max(1.,abs(energy),omega*omega*mass))
        if boundary>1e-11 or error>work_limit:
            raise ValueError('continuum boundary/energy identity failed')
        roots.append(omega*omega);fields.append(sample(sites)/np.sqrt(mass))
        tip.append(boundary);work.append(error)
    arrays=[np.array(roots),sites,np.array(fields),np.array(tip),np.array(work),brackets]
    for a in arrays:
        if not np.isfinite(a).all():raise ValueError('nonfinite reference output')
        a.setflags(write=False)
    check()
    return Reference(height,*arrays[:-1],arrays[-1],profile,calls)
