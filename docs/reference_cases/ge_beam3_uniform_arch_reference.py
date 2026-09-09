"""Separate symmetric planar continuum reference under uniform dead line load.

Simo-Reissner balances and reference-arclength loading: Bali et al.,
doi:10.1002/nme.6994, equations 6--11 and 15--17. The half-arch elimination
and sensitivity below are a same-author specialization, not independent
review or a production certificate. No ANYsolver mechanics imports.
"""
from dataclasses import dataclass
from time import monotonic
import numpy as np
from scipy.integrate import solve_bvp

HEIGHT=.1
AXIAL=1000.
SHEAR=400.
BENDING=.01
DROPS=(.01,.025,.04,.055,.08,.1)


def primitive(t):
    """Signed reference arclength from crown; derivative is J0(t)."""
    a=2*HEIGHT
    return .5*(t*np.sqrt(1+(a*t)**2)+np.arcsinh(a*t)/a)


def equations(t,y,p):
    # Normalize every stiffness and force by EA; p=[nx/EA, density/EA].
    c,s=np.cos(y[2]),np.sin(y[2]);nx,ny=p[0],p[1]*primitive(t)
    n,v=nx*c+ny*s,-nx*s+ny*c
    shear=SHEAR/AXIAL;bending=BENDING/AXIAL
    vx,vy=(1+n)*c-v*s/shear,(1+n)*s+v*c/shear
    j=np.sqrt(1+(2*HEIGHT*t)**2)
    return np.array([j*vx,j*vy,-2*HEIGHT/(1+(2*HEIGHT*t)**2)+j*y[3]/bending,j*(vy*nx-vx*ny)])


def derivatives(t,y,p):
    c,s=np.cos(y[2]),np.sin(y[2]);f=primitive(t);nx,ny=p[0],p[1]*f
    n,v=nx*c+ny*s,-nx*s+ny*c;ga=SHEAR/AXIAL;ei=BENDING/AXIAL
    vx,vy=(1+n)*c-v*s/ga,(1+n)*s+v*c/ga
    vx_t=v*c-(1+n)*s+n*s/ga-v*c/ga
    vy_t=v*s+(1+n)*c-n*c/ga-v*s/ga
    xx,xy,yy=c*c+s*s/ga,c*s*(1-1/ga),s*s+c*c/ga
    a=np.zeros((4,4,len(t)));b=np.zeros((4,2,len(t)))
    a[0,2],a[1,2],a[2,3]=vx_t,vy_t,1/ei
    a[3,2]=nx*vy_t-ny*vx_t
    b[0,0],b[0,1],b[1,0],b[1,1]=xx,xy*f,xy,yy*f
    b[3,0],b[3,1]=vy+nx*xy-ny*xx,(nx*yy-vx-ny*xy)*f
    j=np.sqrt(1+(2*HEIGHT*t)**2)
    return a*j,b*j


@dataclass(frozen=True)
class Reference:
    drop: float
    density: float
    slope: float
    parameters: np.ndarray
    sites: np.ndarray
    fields: np.ndarray
    diagnostics: dict
    production_qualified: bool=False


def sampling_sites(values=None):
    if values is None:return np.linspace(-1.,0.,129)
    raw=np.asarray(values,dtype=object)
    if raw.ndim!=1 or not 2<=len(raw)<=4097 or any(type(v) not in (int,float) for v in raw):
        raise ValueError('bounded explicit reference samples')
    sites=np.array(raw,dtype=float)
    if not np.isfinite(sites).all() or sites[0]!=-1. or sites[-1]!=0. or np.any(np.diff(sites)<=0):
        raise ValueError('ordered reference samples including both ends')
    return sites


def solve(drop,*,previous=None,profile='BVP9',sample_parameters=None):
    sample=sampling_sites(sample_parameters)
    if type(drop) is not float or not np.isfinite(drop) or not 0<=drop<=2*HEIGHT:
        raise ValueError('explicit finite bounded crown drop')
    if profile not in ('BVP7','BVP9'):raise ValueError('registered BVP profile')
    if previous is not None and type(previous) is not Reference:raise ValueError('same-family reference required')
    tolerance=1e-7 if profile=='BVP7' else 1e-9
    maximum_nodes=1025 if profile=='BVP7' else 4097
    started=monotonic();calls=0
    def consume():
        nonlocal calls
        calls+=1
        if calls>2000 or monotonic()-started>60:raise RuntimeError('uniform arch reference callback/time bound')
    t=np.linspace(-1.,0.,33)
    w=.5*drop*(1+np.cos(np.pi*t));dy=-2*HEIGHT*t+.5*drop*np.pi*np.sin(np.pi*t)
    ddy=-2*HEIGHT+.5*drop*np.pi**2*np.cos(np.pi*t)
    moment=(BENDING/AXIAL)*(ddy/(1+dy*dy)+2*HEIGHT/(1+(2*HEIGHT*t)**2))/np.sqrt(1+(2*HEIGHT*t)**2)
    initial=np.array([t,HEIGHT*(1-t*t)-w,np.arctan(dy),moment]);p=np.zeros(2)
    if previous is not None:
        initial=np.array([np.interp(t,previous.sites,row) for row in previous.fields])
        initial[1]-=.5*(drop-previous.drop)*(1+np.cos(np.pi*t));p=previous.parameters.copy()
    def fun(t,y,p):consume();return equations(t,y,p)
    def jac(t,y,p):consume();return derivatives(t,y,p)
    def bc(a,b,p):consume();return np.r_[a[:3]-[-1.,0.,np.arctan(2*HEIGHT)],b[:3]-[0.,HEIGHT-drop,0.]]
    def bc_jac(a,b,p):
        consume();a,b=np.zeros((6,4)),np.zeros((6,4));a[:3,:3]=np.eye(3);b[3:,:3]=np.eye(3)
        return a,b,np.zeros((6,2))
    result=solve_bvp(fun,bc,t,initial,p=p,fun_jac=jac,bc_jac=bc_jac,tol=tolerance,bc_tol=1e-11,max_nodes=maximum_nodes)
    if not result.success:raise RuntimeError('uniform arch collocation failed: '+result.message)
    def sensitivity(t,z,p):
        consume();a,b=derivatives(t,result.sol(t),result.p)
        return np.einsum('ijk,jk->ik',a,z)+np.einsum('ijk,j->ik',b,p)
    def sensitivity_jac(t,z,p):consume();return derivatives(t,result.sol(t),result.p)
    def sensitivity_bc(a,b,p):consume();return np.r_[a[:3],b[:3]-[0.,-1.,0.]]
    z=np.zeros((4,len(result.x)));z[1]=-.5*(1+np.cos(np.pi*result.x))
    tangent=solve_bvp(sensitivity,sensitivity_bc,result.x,z,p=np.zeros(2),fun_jac=sensitivity_jac,bc_jac=bc_jac,
        tol=tolerance,bc_tol=1e-11,max_nodes=maximum_nodes)
    if not tangent.success:raise RuntimeError('uniform arch sensitivity failed: '+tangent.message)
    def residual(solution,rhs):
        sites=(solution.x[:-1,None]+np.diff(solution.x)[:,None]*np.array([.21132486540518713,.7886751345948129])).ravel()
        expected=rhs(sites,solution.sol(sites),solution.p)
        return float(np.max(np.abs(solution.sol(sites,1)-expected)/(1+np.abs(expected))))
    differential=residual(result,fun);sensitivity_error=residual(tangent,sensitivity)
    boundary=float(max(np.max(np.abs(bc(result.y[:,0],result.y[:,-1],result.p))),
        np.max(np.abs(sensitivity_bc(tangent.y[:,0],tangent.y[:,-1],tangent.p)))))
    edges=np.unique(np.r_[result.x,tangent.x]);g,w=np.polynomial.legendre.leggauss(8)
    sites=(edges[:-1,None]+np.diff(edges)[:,None]*(g+1)/2).ravel()
    measures=(np.diff(edges)[:,None]*w/2).ravel()*np.sqrt(1+(2*HEIGHT*sites)**2)
    y,z=result.sol(sites),tangent.sol(sites);c,s=np.cos(y[2]),np.sin(y[2]);f=primitive(sites)
    nx,ny=result.p[0],result.p[1]*f;dnx,dny=tangent.p[0],tangent.p[1]*f
    n,v=nx*c+ny*s,-nx*s+ny*c;dn=dnx*c+dny*s+v*z[2];dv=-dnx*s+dny*c-n*z[2]
    internal=2*np.sum(measures*(n*dn+v*dv/(SHEAR/AXIAL)+y[3]*z[3]/(BENDING/AXIAL)))
    external=-2*result.p[1]*np.sum(measures*z[1])
    work_error=float(abs(internal-external)/max(1.,abs(internal),abs(external)))
    if boundary>1e-11 or max(differential,sensitivity_error,work_error)>10*tolerance or np.min(1+n)<=0:
        raise RuntimeError('uniform arch residual/stretch/work rejection')
    values=(result.p,tangent.p,y,z)
    if any(not np.isfinite(v).all() for v in values):raise RuntimeError('uniform arch nonfinite result')
    fields=result.sol(sample);parameters=result.p.copy()
    for a in (sample,fields,parameters):a.setflags(write=False)
    consume()
    return Reference(drop,float(AXIAL*result.p[1]),float(AXIAL*tangent.p[1]),parameters,sample,fields,
        dict(profile=profile,boundary_error=boundary,differential_error=differential,sensitivity_error=sensitivity_error,
        work_error=work_error,nodes=len(result.x),sensitivity_nodes=len(tangent.x),callbacks=calls,
        normalized_force_scale=AXIAL,independent_authorship=False,full_spatial_stability=False))
