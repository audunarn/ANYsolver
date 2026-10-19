"""Independent W6 reference equations; no ANY product imports (MPL-2.0).

Material-coordinate force integrals use adaptive quadrature and a terminal
geometry root. These are independent of the discrete product initializer.
Contact references retain foundation storage after raw-force clipping.
"""
import math

import numpy as np
from scipy.integrate import quad, solve_ivp
from scipy.optimize import brentq, root
from scipy.special import expit


def cable_integral(h, v, weight, ea, length):
    if h <= 0 or length < 0:
        raise ValueError("positive horizontal tension and nonnegative material length required")
    return np.array([
        quad(lambda s: h / math.hypot(h, v + weight*s) + h/ea,
             0, length, epsabs=1e-11, epsrel=1e-11)[0],
        quad(lambda s: (v + weight*s) / math.hypot(h, v + weight*s)
             + (v + weight*s)/ea, 0, length, epsabs=1e-11, epsrel=1e-11)[0],
    ])


def catenary(first, last, length, ea, weight, material, *, grounded=False):
    first, last, material = map(np.asarray, (first, last, material))
    delta = last - first
    span = float(np.linalg.norm(delta[:2]))
    if span <= 0:
        raise ValueError("reference requires a positive horizontal span")
    direction = np.r_[delta[:2]/span, 0.]
    if abs(weight) < 1e-14:
        distance = float(np.linalg.norm(delta))
        if distance <= length:
            raise ValueError("weightless reference requires a taut line")
        tension = ea*(distance/length-1)
        vector = tension*delta/distance
        return dict(positions=first+material[:, None]*delta/length,
                    first_force=vector, last_force=-vector,
                    tensions=np.full(len(material), tension), closure=0., grounded_length=0.)
    scale = abs(weight)*length
    if grounded:
        if weight <= 0 or delta[2] <= 0 or span + delta[2] < length:
            raise ValueError("no admitted monotone grounded reference for this geometry")
        def residual(x):
            h = scale*math.exp(float(x[0]))
            suspended = length*expit(float(x[1]))
            xyz = cable_integral(h, 0., weight, ea, suspended)
            return (xyz + [(length-suspended)*(1+h/ea), 0.] - [span, delta[2]])/length
        answer = root(residual, [math.log(.1), 0.], tol=1e-10)
        h, suspended = scale*math.exp(float(answer.x[0])), length*expit(float(answer.x[1]))
        v, grounded_length = 0., length-suspended
        positions = []
        for s in material:
            xy = (np.array([s*(1+h/ea), 0.]) if s <= grounded_length else
                  cable_integral(h, 0., weight, ea, s-grounded_length)
                  + [grounded_length*(1+h/ea), 0.])
            positions.append(first + direction*xy[0] + [0., 0., xy[1]])
        vertical = weight*np.maximum(material-grounded_length, 0.)
        last_vertical = weight*suspended
    else:
        def residual(x):
            h, v = scale*math.exp(float(x[0])), scale*float(x[1])
            return (cable_integral(h, v, weight, ea, length)-[span, delta[2]])/length
        answer = root(residual, [math.log(.1), -.5*math.copysign(1., weight)], tol=1e-10)
        h, v = scale*math.exp(float(answer.x[0])), scale*float(answer.x[1])
        grounded_length = 0.
        positions = [first + direction*xy[0] + [0., 0., xy[1]]
                     for xy in (cable_integral(h, v, weight, ea, s) for s in material)]
        vertical = v+weight*material
        last_vertical = v+weight*length
    closure = float(np.max(np.abs(residual(answer.x)))*length)
    if not answer.success or not math.isfinite(closure) or closure > 1e-9*length:
        raise ValueError(f"independent geometry root failed: {answer.message}; closure={closure}")
    return dict(positions=np.asarray(positions), first_force=h*direction+[0., 0., v],
                last_force=-h*direction-[0., 0., last_vertical],
                tensions=np.hypot(h, vertical), closure=closure,
                grounded_length=grounded_length)


def contact_response(times, q0, v0, mass, stiffness, damping, *, activation_depth_m=None):
    """Underdamped, slack-line contact response including landing and clipping."""
    if activation_depth_m is not None:
        return continuous_contact_response(times,q0,v0,mass,stiffness,damping,activation_depth_m)
    times = np.asarray(times)
    alpha = damping/(2*mass)
    omega = math.sqrt(stiffness/mass)
    if alpha >= omega:
        raise ValueError("registered reference is underdamped")
    beta = math.sqrt(omega**2-alpha**2)
    if q0 < 0 and v0 == 0:
        start = 0.
        raw_release = math.atan2(beta, alpha)/beta
        def touching(t):
            decay = np.exp(-alpha*t)
            q = q0*decay*(np.cos(beta*t)+alpha/beta*np.sin(beta*t))
            v = -q0*decay*omega**2/beta*np.sin(beta*t)
            return q, v
    elif q0 > 0 and v0 < 0:
        start = -q0/v0
        raw_release = (math.pi-math.atan2(2*alpha*beta, omega**2-2*alpha**2))/beta
        def touching(t):
            decay = np.exp(-alpha*t)
            return v0/beta*decay*np.sin(beta*t), v0*decay*(np.cos(beta*t)-alpha/beta*np.sin(beta*t))
    else:
        raise ValueError("unsupported registered contact initial state")
    elapsed = np.maximum(times-start, 0.)
    q, v = touching(np.minimum(elapsed, raw_release))
    qr, vr = touching(raw_release)
    post = elapsed > raw_release
    q = np.where(post, qr+vr*(elapsed-raw_release), q)
    v = np.where(post, vr, v)
    q = np.where(times < start, q0+v0*times, q)
    v = np.where(times < start, v0, v)
    elastic = stiffness*np.maximum(-q, 0.)
    force = np.where(q < 0, np.maximum(elastic-damping*v, 0.), 0.)
    storage = .5*stiffness*np.maximum(-q, 0.)**2
    loss = -(force-elastic)*v
    return dict(q=q, v=v, force=force, storage=storage, loss=loss,
                landing=start, raw_release=start+raw_release,
                geometric_release=start+raw_release-qr/vr)


def continuous_contact_response(times,q0,v0,mass,stiffness,damping,depth):
    """Independent scalar ODE and loss integration; no product law/stepper calls.

    Analytic free flight ends at the exact landing time. DOP853's internal steps
    are bounded; events record surface/ramp crossings and gated outgoing clipping.
    Raw force is not used as an event outside contact, where it would be flat.
    """
    times=np.asarray(times)
    if depth<=0 or len(times)<2 or times[0]!=0 or np.any(np.diff(times)<=0):
        raise ValueError('positive depth and increasing reference times from zero required')
    def force_loss(q,v):
        pen=np.maximum(-q,0.)
        elastic=stiffness*pen
        # Independent pressure/velocity formula, retaining loss when clipped.
        raw=elastic-damping*np.minimum(pen/depth,1.)*v
        force=np.where(q<0,np.maximum(raw,0.),0.)
        return force,-(force-elastic)*v
    # This registered overthreshold departure is exactly ballistic with clipped
    # traction until geometric separation. It supplies an independent exact case.
    if damping>0 and -depth<=q0<0 and v0>=stiffness*depth/damping:
        q=q0+v0*times;v=np.full_like(times,v0)
        force,loss=force_loss(q,v)
        storage=.5*stiffness*np.maximum(-q,0.)**2
        integrated_loss=storage[0]-storage
        events=dict(surface=[-q0/v0],ramp=[],outgoing_clipping=[0.])
        method='analytical_clipped_departure'
    else:
        landing=-q0/v0 if q0>0 and v0<0 else 0.
        if q0>0 and v0>=0:
            raise ValueError('unregistered non-contacting departure')
        if landing>=times[-1]:
            raise ValueError('registered duration must include contact')
        initial_q=0. if landing>0 else q0
        def rhs(t,y):
            force,loss=force_loss(y[0],y[1])
            return [y[1],float(force)/mass,float(loss)]
        def surface(t,y):return y[0]
        def ramp(t,y):return -y[0]-depth
        def clipping(t,y):
            # Positive sentinel outside; roots there are ignored explicitly.
            if y[0]>=0:return 1.
            return -stiffness*y[0]-damping*min(-y[0]/depth,1.)*y[1]
        clipping.direction=-1.
        maximum_step=min((times[-1]-landing)/200,1/(20*math.sqrt(stiffness/mass)))
        sol=solve_ivp(rhs,(landing,float(times[-1])),[initial_q,v0,0.],method='DOP853',
            rtol=5e-12,atol=[5e-14,5e-12,5e-14],max_step=maximum_step,dense_output=True,
            events=(surface,ramp,clipping))
        if not sol.success:raise ValueError('independent DOP853 reference failed: '+sol.message)
        y=sol.sol(np.maximum(times,landing))
        q=np.where(times<landing,q0+v0*times,y[0])
        v=np.where(times<landing,v0,y[1])
        integrated_loss=np.where(times<landing,0.,y[2])
        force,loss=force_loss(q,v)
        storage=.5*stiffness*np.maximum(-q,0.)**2
        clipping_events=[float(t) for t in sol.t_events[2] if sol.sol(t)[0]<-1e-12 and sol.sol(t)[1]>0]
        events=dict(surface=sol.t_events[0].tolist(),ramp=sol.t_events[1].tolist(),outgoing_clipping=clipping_events)
        method='independent_DOP853'
    e0=.5*mass*v0*v0+.5*stiffness*max(-q0,0.)**2
    defect=float(np.max(np.abs(.5*mass*v*v+storage+integrated_loss-e0)))/e0
    if defect>1e-9 or np.min(loss)<-1e-12:
        raise ValueError(f'independent reference energy/passivity failure: {defect:g}')
    return dict(q=q,v=v,force=force,storage=storage,loss=loss,integrated_loss=integrated_loss,
                events=events,method=method,reference_energy_defect=defect,activation_depth_m=depth)


def airy(points, time, fixture, heading):
    """Finite-depth Airy waves with Eulerian-local acceleration and steady current."""
    p = np.asarray(points)
    h, g, omega = (fixture[k] for k in ('water_depth', 'gravity', 'omega'))
    k = brentq(lambda k: g*k*math.tanh(k*h)-omega**2, 1e-12, max(1., 2*omega**2/g), xtol=1e-14)
    d = np.array([math.cos(math.radians(heading)), math.sin(math.radians(heading))])
    theta = k*(p[:, :2]@d)-omega*time+fixture['phase']
    ch = np.cosh(k*(p[:, 2]+h))/math.sinh(k*h)
    sh = np.sinh(k*(p[:, 2]+h))/math.sinh(k*h)
    u = np.column_stack((fixture['amplitude']*omega*ch[:, None]*np.cos(theta)[:, None]*d,
                         fixture['amplitude']*omega*sh*np.sin(theta)))
    a = np.column_stack((fixture['amplitude']*omega**2*ch[:, None]*np.sin(theta)[:, None]*d,
                         -fixture['amplitude']*omega**2*sh*np.cos(theta)))
    return u+fixture['current'], a


def morison_endpoint(points, time, fixture, heading, velocity, acceleration, represented):
    u, af = airy(points, time, fixture, heading)
    relative = u-velocity
    normal, tangent = relative.copy(), np.zeros_like(relative)
    tangent[:, 1] = relative[:, 1]
    normal[:, 1] = 0.
    rho, diameter = fixture['water_density'], fixture['diameter']
    area = math.pi*diameter**2/4
    cn = np.array([fixture['inertia_normal'], fixture['inertia_tangential'], fixture['inertia_normal']])
    ca = np.array([fixture['added_mass_normal'], fixture['added_mass_tangential'], fixture['added_mass_normal']])
    parts = dict(
        drag_normal=.5*rho*diameter*fixture['drag_normal']*represented[:, None]*np.linalg.norm(normal, axis=1)[:, None]*normal,
        drag_tangential=.5*rho*math.pi*diameter*fixture['drag_tangential']*represented[:, None]*np.linalg.norm(tangent, axis=1)[:, None]*tangent,
        fluid_inertia=rho*area*represented[:, None]*cn*af,
        added_mass=-rho*area*represented[:, None]*ca*acceleration)
    return parts, rho*area*represented[:, None]*ca
