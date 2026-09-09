"""Separate planar continuum arch BVP; no discrete/production mechanics imports.

Planar specialization of Simo-Reissner balance, initial-curvature subtraction
and linear hyperelasticity: Bali et al., doi:10.1002/nme.6994, equations 6,7,
10,11,15-17. Binary64 collocation is not a multiprecision/interval certificate
or independent authorship. Symmetric equilibrium is not full stability proof.
"""

from dataclasses import dataclass
import time

import numpy as np
from scipy.integrate import solve_bvp


class ArchReferenceError(RuntimeError):
    """No admissible bounded reference result; never retry automatically."""


@dataclass(frozen=True)
class ArchReference:
    height: float
    displacement: float
    axial: float
    shear: float
    bending: float
    load: float
    load_slope: float
    force: np.ndarray
    parameter: np.ndarray
    fields: np.ndarray
    iterations: int
    callbacks: int
    nodes: int
    sensitivity_nodes: int
    profile: str
    boundary_error: float
    differential_error: float
    sensitivity_error: float
    strain_energy: float
    work_error: float
    production_qualified: bool = False


def equations(t,y,p,height,axial,shear,bending):
    """State [x,y,theta,M], constant spatial force p=[Fx,Fy], t=X in [-1,0]."""
    c,s = np.cos(y[2]),np.sin(y[2])
    normal = p[0]*c+p[1]*s
    transverse = -p[0]*s+p[1]*c
    vx = (1+normal/axial)*c-transverse*s/shear
    vy = (1+normal/axial)*s+transverse*c/shear
    jacobian = np.sqrt(1+(2*height*t)**2)
    theta0_derivative = -2*height/(1+(2*height*t)**2)
    return np.array([jacobian*vx,jacobian*vy,theta0_derivative+jacobian*y[3]/bending,
                     jacobian*(vy*p[0]-vx*p[1])])


def derivatives(t,y,p,height,axial,shear,bending):
    c,s = np.cos(y[2]),np.sin(y[2])
    normal = p[0]*c+p[1]*s
    transverse = -p[0]*s+p[1]*c
    extension = 1+normal/axial
    gamma = transverse/shear
    vx,vy = extension*c-gamma*s,extension*s+gamma*c
    vx_t = transverse*c/axial-extension*s+normal*s/shear-gamma*c
    vy_t = transverse*s/axial+extension*c-normal*c/shear-gamma*s
    xx,xy,yy = c*c/axial+s*s/shear,c*s*(1/axial-1/shear),s*s/axial+c*c/shear
    count = len(t)
    a,b = np.zeros((4,4,count)),np.zeros((4,2,count))
    a[0,2],a[1,2],a[2,3] = vx_t,vy_t,1/bending
    a[3,2] = p[0]*vy_t-p[1]*vx_t
    b[0,0],b[0,1],b[1,0],b[1,1] = xx,xy,xy,yy
    b[3,0],b[3,1] = vy+p[0]*xy-p[1]*xx,-vx+p[0]*yy-p[1]*xy
    jacobian = np.sqrt(1+(2*height*t)**2)
    return a*jacobian,b*jacobian


def sampling_parameters(values=None):
    """Explicit evaluation sites for the resolved collocation polynomial.

    This changes saved sampling only, not the BVP mesh, equations or tolerances.
    Keep both boundary sites; do not extrapolate or interpolate saved stations.
    """
    if values is None: return np.linspace(-1., 0., 129)
    raw = np.asarray(values, dtype=object)
    if (raw.ndim != 1 or not 2 <= len(raw) <= 4097
            or any(type(v) not in (int, float) for v in raw)):
        raise ValueError('bounded explicit reference sampling parameters')
    result = np.array(raw, dtype=float)
    if (not np.isfinite(result).all() or result[0] != -1. or result[-1] != 0.
            or np.any(np.diff(result) <= 0)):
        raise ValueError('strictly ordered reference samples including both boundaries')
    return result


def solve(displacement,*,height=.1,axial=1000.,shear=400.,bending=.01,
          previous=None,profile='BVP7',max_callbacks=2000,max_seconds=60.,sample_parameters=None):
    station = sampling_parameters(sample_parameters)
    if (any(isinstance(v,(bool,np.bool_)) or not np.isfinite(v) or v<=0
            for v in (height,axial,shear,bending)) or not 0<height<=.25 or
            isinstance(displacement,(bool,np.bool_)) or not np.isfinite(displacement) or
            not 0<=displacement<=2*height):
        raise ValueError('positive finite stiffness, bounded height and crown displacement required')
    if (profile not in ('BVP7','BVP9') or type(max_callbacks) is not int or not 0<=max_callbacks<=2000
            or not isinstance(max_seconds,(float,int)) or isinstance(max_seconds,bool)
            or not np.isfinite(max_seconds) or not 0<=max_seconds<=60):
        raise ValueError('registered bounded collocation profile required')
    tolerance = 1e-7 if profile=='BVP7' else 1e-9
    maximum_nodes = 1025 if profile=='BVP7' else 4097
    t = np.linspace(-1.,0.,33)
    if previous is None:
        w = .5*displacement*(1+np.cos(np.pi*t))
        dy = -2*height*t+.5*displacement*np.pi*np.sin(np.pi*t)
        ddy = -2*height+.5*displacement*np.pi**2*np.cos(np.pi*t)
        theta = np.arctan(dy)
        moment = bending*(ddy/(1+dy*dy)+2*height/(1+(2*height*t)**2))/np.sqrt(1+(2*height*t)**2)
        initial = np.array([t,height*(1-t*t)-w,theta,moment])
        p = np.zeros(2)
    else:
        if (type(previous) is not ArchReference or
                (previous.height,previous.axial,previous.shear,previous.bending)!=(height,axial,shear,bending)):
            raise ValueError('same-family explicit previous reference required')
        initial = np.array([np.interp(t,previous.parameter,row) for row in previous.fields])
        initial[1]-=(displacement-previous.displacement)*.5*(1+np.cos(np.pi*t))
        p = previous.force.copy()
    started,count = time.monotonic(),0
    def consume():
        nonlocal count
        if count>=max_callbacks or time.monotonic()-started>=max_seconds:
            raise ArchReferenceError('reference callback/time budget exhausted')
        count+=1
    def fun(t,y,p):
        consume()
        return equations(t,y,p,height,axial,shear,bending)
    def jac(t,y,p):
        consume()
        return derivatives(t,y,p,height,axial,shear,bending)
    def boundary(a,b,p):
        consume()
        return np.r_[a[:3]-[-1.,0.,np.arctan(2*height)],b[:3]-[0.,height-displacement,0.]]
    def boundary_jac(a,b,p):
        consume()
        left,right = np.zeros((6,4)),np.zeros((6,4))
        left[:3,:3] = np.eye(3);right[3:,:3] = np.eye(3)
        return left,right,np.zeros((6,2))
    result = solve_bvp(fun,boundary,t,initial,p=p,fun_jac=jac,bc_jac=boundary_jac,
                       tol=tolerance,bc_tol=1e-11,max_nodes=maximum_nodes)
    if not result.success:
        raise ArchReferenceError(f'collocation failed without retry: {result.message}')
    fields = result.sol(station)
    boundary_error = float(np.max(np.abs(boundary(fields[:,0],fields[:,-1],result.p))))
    # Avoid checking only collocation nodes, where the ODE can hold by design.
    interior = (result.x[:-1,None]+np.diff(result.x)[:,None]*np.array([.21132486540518713,.7886751345948129])).ravel()
    expected = fun(interior,result.sol(interior),result.p)
    actual = result.sol(interior,1)
    differential = float(np.max(np.abs(actual-expected)/(1+np.abs(expected))))
    normal = result.p[0]*np.cos(fields[2])+result.p[1]*np.sin(fields[2])
    if (not np.isfinite(fields).all() or not np.isfinite(result.p).all() or
            np.min(1+normal/axial)<=0 or boundary_error>1e-11 or differential>10*tolerance):
        raise ArchReferenceError('reference residual, positive stretch or finite-field check failed')
    # Differentiate the continuum BVP with respect to prescribed crown drop.
    # This linear variational BVP is not a differenced production tangent.
    def sensitivity_fun(t,z,p):
        consume()
        a,b = derivatives(t,result.sol(t),result.p,height,axial,shear,bending)
        return np.einsum('ijk,jk->ik',a,z)+np.einsum('ijk,j->ik',b,p)
    def sensitivity_jac(t,z,p):
        consume()
        return derivatives(t,result.sol(t),result.p,height,axial,shear,bending)
    def sensitivity_boundary(a,b,p):
        consume()
        return np.r_[a[:3],b[:3]-[0.,-1.,0.]]
    # Reuse the resolved coefficient mesh instead of forcing the sensitivity
    # solver to rediscover its knots from a fresh uniform grid.
    sensitivity_mesh = result.x
    z = np.zeros((4,len(sensitivity_mesh)));z[1] = -.5*(1+np.cos(np.pi*sensitivity_mesh))
    sensitivity = solve_bvp(sensitivity_fun,sensitivity_boundary,sensitivity_mesh,z,p=np.zeros(2),
        fun_jac=sensitivity_jac,bc_jac=boundary_jac,tol=tolerance,bc_tol=1e-11,max_nodes=maximum_nodes)
    if not sensitivity.success or not np.isfinite(sensitivity.p).all():
        raise ArchReferenceError(f'load-slope sensitivity BVP failed without retry: {sensitivity.message}')
    interior_s = (sensitivity.x[:-1,None]+np.diff(sensitivity.x)[:,None]*np.array([.21132486540518713,.7886751345948129])).ravel()
    rhs = sensitivity_fun(interior_s,sensitivity.sol(interior_s),sensitivity.p)
    sensitivity_error = float(np.max(np.abs(sensitivity.sol(interior_s,1)-rhs)/(1+np.abs(rhs))))
    if (sensitivity_error>10*tolerance or
            np.max(np.abs(sensitivity_boundary(sensitivity.y[:,0],sensitivity.y[:,-1],sensitivity.p)))>1e-11):
        raise ArchReferenceError('load-slope residual check failed')
    consume()
    partition = np.unique(np.r_[result.x,sensitivity.x])
    points,weights = np.polynomial.legendre.leggauss(8)
    quadrature = (partition[:-1,None]+np.diff(partition)[:,None]*(points+1)/2).ravel()
    measures = (np.diff(partition)[:,None]*weights/2).ravel()*np.sqrt(1+(2*height*quadrature)**2)
    q,z = result.sol(quadrature),sensitivity.sol(quadrature)
    c,s = np.cos(q[2]),np.sin(q[2])
    n,v = result.p[0]*c+result.p[1]*s,-result.p[0]*s+result.p[1]*c
    dn = sensitivity.p[0]*c+sensitivity.p[1]*s+v*z[2]
    dv = -sensitivity.p[0]*s+sensitivity.p[1]*c-n*z[2]
    strain_energy = float(np.sum(measures*(n*n/axial+v*v/shear+q[3]*q[3]/bending)))
    energy_derivative = float(2*np.sum(measures*(n*dn/axial+v*dv/shear+q[3]*z[3]/bending)))
    work_error = abs(energy_derivative+2*result.p[1])/max(1.,abs(energy_derivative),abs(2*result.p[1]))
    if not np.isfinite(strain_energy) or not np.isfinite(work_error) or work_error>10*tolerance:
        raise ArchReferenceError('symmetric full-arch virtual-work identity failed')
    for array in (station,fields,result.p):
        array.setflags(write=False)
    return ArchReference(float(height),float(displacement),float(axial),float(shear),float(bending),
        float(-2*result.p[1]),float(-2*sensitivity.p[1]),result.p,station,fields,int(result.niter),count,len(result.x),len(sensitivity.x),profile,
        boundary_error,differential,sensitivity_error,strain_energy,work_error)


def first_limit_point(*,iterations=20,max_seconds=60.,profile='BVP9'):
    """First observed symmetric load-slope sign change in [0.025,0.05].

    Fixed development family only. Bisection is not an interval certificate or
    proof excluding earlier symmetry-breaking modes of the spatial beam.
    """
    if (type(iterations) is not int or not 1<=iterations<=24 or
            not isinstance(max_seconds,(int,float)) or isinstance(max_seconds,bool) or
            not np.isfinite(max_seconds) or not 0<max_seconds<=60):
        raise ValueError('at most 24 bounded limit-point bisections required')
    started = time.monotonic()
    def evaluate(displacement,previous=None):
        remaining = max_seconds-(time.monotonic()-started)
        if remaining<=0:
            raise ArchReferenceError('whole limit-point diagnostic time budget exhausted')
        return solve(displacement,previous=previous,profile=profile,max_seconds=remaining)
    left = evaluate(.025)
    right = evaluate(.05,left)
    if not left.load_slope>0>right.load_slope:
        raise ArchReferenceError('no registered positive-to-negative load-slope bracket')
    for _ in range(iterations):
        mid = evaluate((left.displacement+right.displacement)/2,left)
        if mid.load_slope>0:
            left = mid
        else:
            right = mid
    if right.displacement-left.displacement>1e-6*left.height:
        raise ArchReferenceError('unresolved limit-point width')
    return left,right
