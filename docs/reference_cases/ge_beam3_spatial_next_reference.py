"""New +/-0.0065 BVP; unchanged continuum equations, no beam imports."""
from time import monotonic
import numpy as np
from scipy.integrate import solve_bvp
from scipy.interpolate import PPoly
from docs.reference_cases import ge_beam3_spatial_continuum as base


def solve(guess_record,amplitude,progress=lambda row:None):
    if (type(amplitude) is not float or amplitude not in (-.0065,.0065)
            or guess_record.get('amplitude')!=(.006 if amplitude>0 else -.006)
            or len(guess_record['mechanical']['positions'])!=41):
        raise ValueError('new signed target and original N20 initializer required')
    start=monotonic();calls=0
    def consume():
        nonlocal calls
        calls+=1
        if calls>2000 or monotonic()-start>60:raise RuntimeError('spatial reference callback/time bound')
        if calls%100==0:progress(dict(stage='continuum-callback',callbacks=calls))
    def fun(u,y,p):
        consume()
        return np.vstack([(hi-lo)*base.equations(lo+(hi-lo)*u,y[13*i:13*(i+1)])
            for i,(lo,hi) in enumerate(zip(base.BREAKS[:-1],base.BREAKS[1:]))])
    def bc(a,b,p):consume();return base.boundary(a,b,p,amplitude)
    u=np.linspace(0.,1.,33);guess=base.initial_guess(guess_record,u)
    progress(dict(stage='next-spatial-reference-start',amplitude=amplitude))
    result=solve_bvp(fun,bc,u,guess,p=np.array([guess_record['load']]),tol=1e-9,bc_tol=1e-11,max_nodes=4097)
    if not result.success or not np.isfinite(result.y).all():raise RuntimeError('spatial continuum failed: '+result.message)
    boundary_error=float(np.max(abs(base.boundary(result.y[:,0],result.y[:,-1],result.p,amplitude))))
    sites=base.validation_grid(result.x);values=result.sol(sites);expected=fun(sites,values,result.p)
    differential_error=float(np.max(abs(result.sol(sites,1)-expected)/(1+abs(expected))))
    norm_error=max(float(np.max(abs(np.sum(values[13*i+3:13*i+7]**2,axis=0)-1.))) for i in range(4))
    if boundary_error>1e-11 or differential_error>1e-8 or norm_error>1e-8:raise RuntimeError('reference consistency')
    metadata=dict(profile='BVP9_NEXT_0065',amplitude=amplitude,load=float(result.p[0]),nodes=len(result.x),
        iterations=result.niter,callbacks=calls,boundary_error=boundary_error,differential_error=differential_error,
        quaternion_norm_error=norm_error,validation_sites=len(sites),
        validation_policy='GAUSS_INTERIOR_EVERY_ACTUAL_COLLOCATION_INTERVAL_V1')
    progress(dict(stage='next-spatial-reference-complete',**metadata));return result,metadata


def pack(solution):
    # Save the actual piecewise polynomial, not only a plotting grid. Later
    # stability work can use these immutable fields without repeating this solve.
    if (solution.c.shape!=(4,len(solution.x)-1,52) or solution.axis!=1
            or not np.isfinite(solution.c).all()):raise ValueError('complete 52-field cubic BVP polynomial')
    return dict(knots=solution.x.tolist(),coefficients=solution.c.tolist(),axis=solution.axis,extrapolate=False)


def unpack(record):
    if type(record) is not dict or set(record)!={'knots','coefficients','axis','extrapolate'}:raise ValueError('polynomial schema')
    x=np.asarray(record['knots']);c=np.asarray(record['coefficients'])
    if (x.ndim!=1 or not 2<=len(x)<=4097 or x[0]!=0. or x[-1]!=1. or np.any(np.diff(x)<=0)
            or c.shape!=(4,len(x)-1,52) or not np.isfinite(c).all() or not np.isfinite(x).all()
            or type(record['axis']) is not int or record['axis']!=1 or record['extrapolate'] is not False):
        raise ValueError('finite bounded 52-field polynomial')
    return PPoly.construct_fast(c.copy(),x.copy(),extrapolate=False,axis=1)
