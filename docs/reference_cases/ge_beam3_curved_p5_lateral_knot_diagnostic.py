"""Bounded investigation of coefficient-knot resolution in linear propagation.

No base solve or discrete mechanics. Same Jacobi generator/tolerances; force
steps to land on the known Hermite grid so adaptive steps cannot straddle its
third-derivative discontinuities. This does not replace any stored transfer.
"""

import time
import numpy as np
from scipy.integrate import solve_ivp


def propagate(generator,initial,*,half_nodes=129,max_callbacks=10000,max_seconds=30.):
    if (type(half_nodes) is not int or half_nodes not in (129,257) or
            type(max_callbacks) is not int or not 0<=max_callbacks<=10000 or
            isinstance(max_seconds,bool) or not np.isfinite(max_seconds) or not 0<=max_seconds<=30):
        raise ValueError('registered bounded coefficient-knot profile required')
    initial=np.asarray(initial,dtype=float)
    if initial.shape not in ((6,),(6,6)) or not np.isfinite(initial).all():
        raise ValueError('one vector or complete fundamental matrix required')
    parameters=np.linspace(-1.,1.,2*half_nodes-1);state=initial.copy()
    states=[state.copy()];calls=0;started=time.monotonic()
    for left,right in zip(parameters[:-1],parameters[1:]):
        side=0 if right<=0 else 1
        def rhs(t,y):
            nonlocal calls
            if calls>=max_callbacks or time.monotonic()-started>=max_seconds:
                raise RuntimeError('coefficient-knot callback/time budget exhausted')
            calls+=1
            h=np.asarray(generator(t,side))
            if h.shape!=(6,6) or not np.isfinite(h).all(): raise ValueError('finite Jacobi generator required')
            return (h@y.reshape(initial.shape)).ravel()
        solution=solve_ivp(rhs,(left,right),state.ravel(),method='DOP853',rtol=1e-11,atol=1e-13,
                           first_step=right-left,max_step=right-left)
        if not solution.success or solution.t[-1]!=right or not np.isfinite(solution.y).all():
            raise RuntimeError('coefficient-knot propagation failed; no retry')
        state=solution.y[:,-1].reshape(initial.shape);states.append(state.copy())
    return {'parameters':parameters,'states':np.array(states),'endpoint':state,
            'callbacks':calls,'half_nodes':half_nodes,'diagnostic_only':True}
