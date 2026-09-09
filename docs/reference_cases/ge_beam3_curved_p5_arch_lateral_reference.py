"""Continuum lateral Jacobi equations, separate from discrete beam mechanics.

Derived from material rod energy, spatial Exp perturbations and prestress;
see GE_BEAM3_CURVED_P5_LATERAL_REFERENCE_EQUATIONS.md. Binary64 research only,
not independent authorship, an exact spectral certificate or production API.
"""

from dataclasses import asdict
import time

import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import CubicHermiteSpline

from docs.reference_cases.ge_beam3_curved_p5_arch_reference import ArchReference,equations,solve as planar_solve


class LateralReferenceError(RuntimeError):
    """Bounded continuum reference failed; no retry or partial result."""


def coefficients(theta,vx,vy,fx,fy,moment,*,shear=400.,torsion=.02,bending=.02):
    """Q=u'^T A u' + 2 u^T B u' + u^T C u, u=(z,wx,wy)."""
    numbers=(theta,vx,vy,fx,fy,moment,shear,torsion,bending)
    if (any(isinstance(x,(bool,np.bool_)) or not np.isscalar(x) or not np.isfinite(x) for x in numbers)
            or min(shear,torsion,bending)<=0):
        raise ValueError('finite lateral state and positive section stiffness required')
    c,s=np.cos(theta),np.sin(theta)
    a=np.zeros((3,3));a[0,0]=shear
    a[1,1]=torsion*c*c+bending*s*s
    a[2,2]=torsion*s*s+bending*c*c
    a[1,2]=a[2,1]=(torsion-bending)*c*s
    b=np.zeros((3,3));b[1,0]=-shear*vy+fy;b[2,0]=shear*vx-fx
    b[1,2]=-moment/2;b[2,1]=moment/2
    d=np.zeros((3,3));d[1,1]=shear*vy*vy-fy*vy;d[2,2]=shear*vx*vx-fx*vx
    d[1,2]=d[2,1]=-shear*vy*vx+(fx*vy+fy*vx)/2
    return a,b,d


def jacobi(a,b,c):
    """First-order [u,p] system; no condensed/discrete matrix used."""
    a,b,c=(np.asarray(x,dtype=float) for x in (a,b,c))
    if (any(x.shape!=(3,3) or not np.isfinite(x).all() for x in (a,b,c)) or
            not np.allclose(a,a.T,rtol=0,atol=1e-13) or not np.allclose(c,c.T,rtol=0,atol=1e-13)):
        raise ValueError('finite symmetric derivative/value blocks required')
    np.linalg.cholesky(a)
    inverse=np.linalg.solve(a,np.eye(3));ab=inverse@b.T
    return np.block([[-ab,inverse],[c-b@ab,b@inverse]])


def boundary_measure(phi):
    phi=np.asarray(phi,dtype=float)
    if phi.shape!=(6,6) or not np.isfinite(phi).all():
        raise ValueError('finite complete transfer required')
    boundary=phi[:3,3:]
    # Never normalize each column by its own current norm: a neutral mode may
    # make an entire column vanish, and that scaling would amplify roundoff and
    # conceal the singularity. One common nonzero scale preserves rank loss.
    scale=max(1.,float(np.linalg.norm(boundary)))
    scaled=boundary/scale
    singular=np.linalg.svd(scaled,compute_uv=False)
    return {'boundary_matrix':boundary,'normalization_scale':scale,'singular_values':singular,
            'normalized_determinant':float(np.linalg.det(scaled)),
            'singular_ratio':float(singular[-1]/singular[0]) if singular[0]>0 else 0.}


def transfer(generator,*,breaks=(-1.,0.,1.),profile='IVP9',max_callbacks=10000,max_seconds=30.):
    """Fundamental matrix across fixed intervals; discontinuities never smeared.

    Callback/time bounds are checked during every RHS evaluation. A failed IVP
    is never retried. Symplectic error is a diagnostic, not rigorous enclosure.
    """
    if (profile not in ('IVP9','IVP11') or type(max_callbacks) is not int or not 0<=max_callbacks<=10000 or
            isinstance(max_seconds,bool) or not np.isfinite(max_seconds) or not 0<=max_seconds<=30):
        raise ValueError('registered bounded lateral integration profile required')
    breaks=np.asarray(breaks,dtype=float)
    if breaks.ndim!=1 or not 2<=len(breaks)<=3 or not np.isfinite(breaks).all() or np.any(np.diff(breaks)<=0):
        raise ValueError('one or two ordered finite integration intervals required')
    tolerance=1e-9 if profile=='IVP9' else 1e-11
    started=time.monotonic();calls=0;phi=np.eye(6);records=[]
    j=np.block([[np.zeros((3,3)),np.eye(3)],[-np.eye(3),np.zeros((3,3))]])
    def consume():
        nonlocal calls
        if calls>=max_callbacks or time.monotonic()-started>=max_seconds:
            raise LateralReferenceError('lateral callback/time budget exhausted')
        calls+=1
    for index,(left,right) in enumerate(zip(breaks[:-1],breaks[1:])):
        def rhs(t,value):
            consume()
            h=np.asarray(generator(t,index),dtype=float)
            if h.shape!=(6,6) or not np.isfinite(h).all():
                raise LateralReferenceError('finite continuum Jacobi generator required')
            if np.linalg.norm(h.T@j+j@h)>1e-11*max(1.,np.linalg.norm(h)):
                raise LateralReferenceError('Hamiltonian generator identity failed')
            return (h@value.reshape(6,6)).ravel()
        result=solve_ivp(rhs,(left,right),phi.ravel(),method='DOP853',rtol=tolerance,atol=tolerance*.01)
        if not result.success or result.t[-1]!=right or not np.isfinite(result.y).all():
            raise LateralReferenceError('continuum transfer failed without retry')
        phi=result.y[:,-1].reshape(6,6)
        records.append({'interval':[float(left),float(right)],'steps':len(result.t)-1,'transfer':phi.copy()})
    consume()
    symplectic=float(np.linalg.norm(phi.T@j@phi-j))
    normalized=symplectic/max(1.,float(np.linalg.norm(phi))**2)
    if normalized>10*tolerance:
        raise LateralReferenceError('transfer symplectic consistency failed')
    return {'profile':profile,'callbacks':calls,'transfer':phi,'intervals':records,
            'symplectic_error':symplectic,'normalized_symplectic_error':normalized,
            **boundary_measure(phi),'production_qualified':False,
            'restriction':'NO_GO_PRODUCTION_RESTRICTION_UNCHANGED'}


def arch_generator(reference,*,stride=1,torsion=.02,lateral_bending=.02):
    if type(reference) is not ArchReference or stride not in (1,2):
        raise ValueError('separate ArchReference and registered interpolation stride required')
    if (reference.parameter.shape!=(129,) or reference.fields.shape!=(4,129) or
            not np.array_equal(reference.parameter,np.linspace(-1.,0.,129)) or
            not np.isfinite(reference.fields).all() or not np.isfinite(reference.force).all()):
        raise ValueError('finite fixed-grid continuum base required')
    t=reference.parameter[::stride];fields=reference.fields[:,::stride]
    slope=equations(t,fields,reference.force,reference.height,reference.axial,reference.shear,reference.bending)
    interpolant=CubicHermiteSpline(t,fields.T,slope.T)
    def generator(x,index):
        if index not in (0,1) or not np.isfinite(x) or not -1<=x<=1:
            raise ValueError('registered arch half/domain required')
        side=1. if index==0 else -1.
        if (index==0 and x>0) or (index==1 and x<0):
            raise ValueError('arch half/coordinate mismatch')
        state=interpolant(-abs(x));theta=side*state[2]
        fx,fy=reference.force[0],side*reference.force[1]
        c,s=np.cos(theta),np.sin(theta)
        normal,transverse=fx*c+fy*s,-fx*s+fy*c
        vx=(1+normal/reference.axial)*c-transverse*s/reference.shear
        vy=(1+normal/reference.axial)*s+transverse*c/reference.shear
        a,b,d=coefficients(theta,vx,vy,fx,fy,state[3],shear=reference.shear,
                            torsion=torsion,bending=lateral_bending)
        return np.sqrt(1+(2*reference.height*x)**2)*jacobi(a,b,d)
    return generator


def solve(reference,*,stride=1,profile='IVP9',max_callbacks=10000,max_seconds=30.):
    result=transfer(arch_generator(reference,stride=stride),profile=profile,
                    max_callbacks=max_callbacks,max_seconds=max_seconds)
    return dict(result,displacement=reference.displacement,load=reference.load,
                base_profile=reference.profile,reference_stride=stride)


def neutral_bracket(*,profile='IVP11',stride=1,iterations=20,max_seconds=30.):
    """Observed lateral root in the explicitly extended development interval.

    The two original comparison points were both nonsingular with positive
    determinant. A separately checked endpoint d=0.05 is negative. This
    function never searches for a new bracket or retries a failed evaluation.
    It is not proof of uniqueness, first-root status or exact stability.
    """
    if (profile not in ('IVP9','IVP11') or stride not in (1,2) or type(iterations) is not int or
            not 1<=iterations<=20 or isinstance(max_seconds,bool) or
            not np.isfinite(max_seconds) or not 0<max_seconds<=30):
        raise ValueError('registered bounded lateral-root profile required')
    started=time.monotonic();trace=[]
    def remaining():
        value=max_seconds-(time.monotonic()-started)
        if value<=0: raise LateralReferenceError('whole lateral-root budget exhausted')
        return value
    def evaluate(d):
        reference=planar_solve(d,profile='BVP9',max_seconds=remaining())
        result=solve(reference,stride=stride,profile=profile,max_seconds=remaining())
        trace.append({k:result[k] for k in ('displacement','load','normalized_determinant',
                                          'singular_ratio','callbacks')})
        return reference,result
    try:
        left=evaluate(.044820372353098756);right=evaluate(.05)
        if not left[1]['normalized_determinant']>0>right[1]['normalized_determinant']:
            raise LateralReferenceError('registered lateral bracket is absent; no search extension')
        for _ in range(iterations):
            midpoint=evaluate((left[0].displacement+right[0].displacement)/2)
            if midpoint[1]['normalized_determinant']>0: left=midpoint
            else: right=midpoint
        remaining()
        if right[0].displacement-left[0].displacement>1e-8:
            raise LateralReferenceError('lateral root width remains unresolved')
        return {'left':dict(left[1],reference=asdict(left[0])),
                'right':dict(right[1],reference=asdict(right[0])),
                'trace':trace,'iterations':iterations,'profile':profile,'reference_stride':stride,
                'disposition':'OBSERVED_CONTINUUM_LATERAL_NEUTRAL_BRACKET',
                'production_qualified':False,'restriction':'NO_GO_PRODUCTION_RESTRICTION_UNCHANGED'}
    except Exception as error:
        failure=LateralReferenceError(f'bounded lateral-root diagnostic failed: {error}')
        failure.completed_trace=trace
        raise failure from error
