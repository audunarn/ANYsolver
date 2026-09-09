"""Linear continuum neutral-shape recovery; never imports discrete mechanics.

Uses the separately reconstructed lateral Jacobi equations and a saved base
state/transfer. Shape comparison is not physical-mass modal qualification.
"""

import time

import numpy as np
from scipy.integrate import solve_ivp

from docs.reference_cases.ge_beam3_curved_p5_arch_lateral_reference import arch_generator,LateralReferenceError


def integrate(generator,momenta,*,nodes=33,max_callbacks=10000,max_seconds=30.):
    """Resolve all Hermite coefficient knots; retain continuous u,p/end errors."""
    if (type(nodes) is not int or nodes not in (17,33,65,129) or type(max_callbacks) is not int or
            not 0<=max_callbacks<=10000 or isinstance(max_seconds,bool) or
            not np.isfinite(max_seconds) or not 0<=max_seconds<=30):
        raise ValueError('registered small mode-sampling bounds required')
    momenta=np.asarray(momenta,dtype=float)
    if momenta.shape!=(3,) or not np.isfinite(momenta).all() or np.linalg.norm(momenta)==0:
        raise ValueError('finite nonzero three-component initial momentum required')
    parameters=np.linspace(-1.,1.,nodes);values=np.zeros((nodes,7))
    state=np.r_[np.zeros(3),momenta,0.];calls=0;started=time.monotonic()
    coefficient_knots=np.linspace(-1.,1.,257)
    for index,(left,right) in enumerate(zip(coefficient_knots[:-1],coefficient_knots[1:])):
        side=0 if right<=0 else 1
        def rhs(t,y):
            nonlocal calls
            if calls>=max_callbacks or time.monotonic()-started>=max_seconds:
                raise LateralReferenceError('linear mode callback/time budget exhausted')
            calls+=1
            h=np.asarray(generator(t,side),dtype=float)
            if h.shape!=(6,6) or not np.isfinite(h).all():
                raise LateralReferenceError('finite Jacobi generator required')
            u,p=y[:3],y[3:6];derivative=h@y[:6]
            # Independent scalar quadrature of the quadratic Lagrangian carried
            # as a seventh ODE state, checked against endpoint u dot p below.
            # Reconstructed from H: this checks integration/work consistency,
            # not independent authorship or the physical equation derivation.
            a=np.linalg.solve(h[:3,3:],np.eye(3));b=-h[:3,:3].T@a
            c=h[3:,:3]+b@h[:3,3:]@b.T
            velocity=derivative[:3]
            energy=velocity@a@velocity+2*u@b@velocity+u@c@u
            return np.r_[derivative,energy]
        result=solve_ivp(rhs,(left,right),state,method='DOP853',rtol=1e-11,atol=1e-13,dense_output=True,
                         first_step=right-left,max_step=right-left)
        if not result.success or result.t[-1]!=right or not np.isfinite(result.y).all():
            raise LateralReferenceError('linear mode integration failed without retry')
        selected=np.flatnonzero(((parameters>=left) if index==0 else (parameters>left))&(parameters<=right))
        if len(selected): values[selected]=result.sol(parameters[selected]).T
        state=result.y[:,-1]
    boundary_work=float(state[:3]@state[3:6])
    work_error=abs(state[6]-boundary_work)/max(1.,abs(state[6]),abs(boundary_work))
    if not np.isfinite(values).all() or work_error>1e-9:
        raise LateralReferenceError('linear variational work consistency failed')
    return {'parameters':parameters,'states':values[:,:6],'energy_integral':float(state[6]),
            'boundary_work':boundary_work,'work_error':float(work_error),'callbacks':calls,
            'coefficient_half_nodes':129}


def weights(parameters,*,height=.1):
    t=np.asarray(parameters,dtype=float)
    if (t.ndim!=1 or len(t)<3 or len(t)>129 or not np.isfinite(t).all() or
            t[0]!=-1 or t[-1]!=1 or np.any(np.diff(t)<=0) or not np.isfinite(height) or height<0):
        raise ValueError('ordered bounded reference interval required')
    w=np.r_[np.diff(t)[0]/2,(t[2:]-t[:-2])/2,np.diff(t)[-1]/2]
    return w*np.sqrt(1+(2*height*t)**2)


def shape(reference,endpoint,*,stride=1,nodes=33):
    """Recover an isolated near-neutral mode, without solving the base again."""
    if (endpoint['displacement']!=reference.displacement or endpoint['load']!=reference.load or
            endpoint['reference_stride']!=stride):
        raise ValueError('saved endpoint/base/stride identity mismatch')
    phi=np.asarray(endpoint['transfer'],dtype=float)
    if phi.shape!=(6,6) or not np.isfinite(phi).all():
        raise ValueError('finite saved continuum transfer required')
    _,singular,vh=np.linalg.svd(phi[:3,3:])
    if singular[0]<=0 or singular[-1]/singular[0]>1e-6 or singular[1]/singular[0]<1e-5:
        raise LateralReferenceError('isolated near-neutral boundary mode required')
    initial=vh[-1]
    recovered=integrate(arch_generator(reference,stride=stride),initial,nodes=nodes)
    predicted=phi@np.r_[np.zeros(3),initial]
    transfer_error=float(np.linalg.norm(recovered['states'][-1]-predicted))/max(1.,float(np.linalg.norm(predicted)))
    if transfer_error>1e-8:
        raise LateralReferenceError('saved-transfer/mode integration disagreement')
    metric=weights(recovered['parameters'],height=reference.height)
    scale=np.array([1.,2.,2.]) # Span-scaled coordinates, not mass or physical energy.
    norm=float(np.sqrt(np.sum(metric[:,None]*(recovered['states'][:,:3]*scale)**2)))
    if not np.isfinite(norm) or norm<=0:
        raise LateralReferenceError('positive finite shape norm required')
    q=np.zeros((nodes,6));q[:,[2,3,4]]=recovered['states'][:,:3]/norm
    sign=1. if q.ravel()[np.argmax(np.abs(q))]>=0 else -1.
    q*=sign
    end_error=float(np.max(np.abs(q[[0,-1]])))
    if end_error>1e-7:
        raise LateralReferenceError('near-neutral shape end residual unresolved')
    return {'parameters':recovered['parameters'],'nodal_increment':q,
            'normalized_state':sign*recovered['states']/norm,'metric_weights':metric,
            'coordinate_scale_span':2.,'normalization':norm,'end_error':end_error,
            'transfer_error':transfer_error,'work_error':recovered['work_error'],
            'energy_integral_normalized':recovered['energy_integral']/norm**2,
            'boundary_work_normalized':recovered['boundary_work']/norm**2,
            'callbacks':recovered['callbacks'],'reference_stride':stride,
            'coefficient_half_nodes':recovered['coefficient_half_nodes'],
            'displacement':reference.displacement,'load':reference.load,
            'production_qualified':False,'natural_frequencies_computed':False}


def compare(reference,discrete,metric_weights):
    """Static coordinate-metric squared cosine, explicitly NOT mass-weighted MAC."""
    a,b,w=(np.asarray(v,dtype=float) for v in (reference,discrete,metric_weights))
    if (a.ndim!=2 or a.shape!=b.shape or a.shape[1]!=6 or not 3<=len(a)<=129 or
            w.shape!=(len(a),) or any(not np.isfinite(v).all() for v in (a,b,w)) or np.any(w<=0)):
        raise ValueError('matching finite six-DOF shapes and positive weights required')
    def comparison(columns):
        scale=np.array([1.,1.,1.,2.,2.,2.])[columns]
        x,y=a[:,columns]*scale,b[:,columns]*scale
        nx,ny=float(np.sum(w[:,None]*x*x)),float(np.sum(w[:,None]*y*y))
        if min(nx,ny)<=0: raise LateralReferenceError('zero component norm cannot define shape overlap')
        inner=float(np.sum(w[:,None]*x*y));cosine=inner/np.sqrt(nx*ny)
        if abs(cosine)>1+1e-12: raise LateralReferenceError('shape inner-product consistency failure')
        sign=1. if inner>=0 else -1.
        distance=float(np.sqrt(np.sum(w[:,None]*(x/np.sqrt(nx)-sign*y/np.sqrt(ny))**2)))
        return {'squared_cosine':float(cosine*cosine),'sign_aligned_distance':distance,
                'reference_norm_squared':nx,'discrete_norm_squared':ny}
    return {'combined':comparison([0,1,2,3,4,5]),'translation':comparison([0,1,2]),
            'rotation':comparison([3,4,5]),'physical_mass_mac':False,'qualification_gate':False}
