"""Standalone two-DOF axial time reference, derived by polynomial integration.

Standard library only. Imports no beam implementation, matrix cache, section,
geometry, solver or numeric library. This separates temporal from spatial error
on the exact axial subspace of two unit-length linear rod halves.
"""

import math


SCHEMA = 'GE_BEAM3_P5_AXIAL_TEMPORAL_REFERENCE_V1'
EA = 100.
RHO = 2.
FORCE = .1
DURATION = .16
K = ((2*EA,-EA),(-EA,EA))
M = ((4*RHO/6,RHO/6),(RHO/6,2*RHO/6))


def product(a,x): return tuple(math.fsum(a[i][j]*x[j] for j in range(2)) for i in range(2))


def dot(a,b): return math.fsum(x*y for x,y in zip(a,b))


def energy(x,v): return (dot(x,product(K,x))+dot(v,product(M,v)))/2


def _solve(a,b):
    determinant=a[0][0]*a[1][1]-a[0][1]*a[1][0]
    if not math.isfinite(determinant) or determinant<=0.: raise ValueError('positive two-dimensional pencil required')
    return ((a[1][1]*b[0]-a[0][1]*b[1])/determinant,
            (a[0][0]*b[1]-a[1][0]*b[0])/determinant)


def step_response(time):
    """Analytic modal response from rest to a constant nodal tip force.

    Eigenvalues are 6 EA/(7 rho) (5 +/- 3 sqrt(2)); corresponding unnormalized
    modes are (1, -/+ sqrt(2)). No numerical eigensolver is used.
    """
    if type(time) not in (int,float) or not math.isfinite(time) or time<0.:
        raise ValueError('finite nonnegative reference time required')
    x=[0.,0.];v=[0.,0.]
    for sign in (-1,1):
        mode=(1.,-sign*math.sqrt(2.))
        squared=6*EA/(7*RHO)*(5+sign*3*math.sqrt(2.))
        frequency=math.sqrt(squared)
        coefficient=mode[1]*FORCE/(dot(mode,product(M,mode))*squared)
        # 1-cos is evaluated without subtracting near-equal values.
        displacement=coefficient*2*math.sin(frequency*time/2)**2
        velocity=coefficient*frequency*math.sin(frequency*time)
        for i in range(2): x[i]+=mode[i]*displacement;v[i]+=mode[i]*velocity
    return tuple(x),tuple(v)


def pulse_response(time):
    x,v=step_response(time)
    if time<=DURATION/2: return x,v
    delayed_x,delayed_v=step_response(time-DURATION/2)
    return tuple(a-b for a,b in zip(x,delayed_x)),tuple(a-b for a,b in zip(v,delayed_v))


def temporal_error(x,v):
    reference_x,reference_v=pulse_response(DURATION)
    dx=tuple(a-b for a,b in zip(x,reference_x));dv=tuple(a-b for a,b in zip(v,reference_v))
    return math.sqrt(energy(dx,dv)/energy(reference_x,reference_v))


def integrate(steps,*,method='BACKWARD_EULER'):
    """Frozen small linear reference schedules, not a beam mechanics run."""
    if type(steps) is not int or steps not in (4,8,16,32): raise ValueError('registered even step count required')
    if method not in ('BACKWARD_EULER','MIDPOINT'): raise ValueError('registered reference method required')
    h=DURATION/steps;x=(0.,0.);v=(0.,0.);records=[];work=0.;dissipation=0.
    for n in range(steps):
        force=(0.,FORCE if n<steps//2 else 0.)
        if method=='BACKWARD_EULER':
            matrix=tuple(tuple(M[i][j]+h*h*K[i][j] for j in range(2)) for i in range(2))
            mv,kx=product(M,v),product(K,x)
            new_v=_solve(matrix,tuple(mv[i]-h*kx[i]+h*force[i] for i in range(2)))
            new_x=tuple(x[i]+h*new_v[i] for i in range(2));work_velocity=new_v
            delta_v=tuple(new_v[i]-v[i] for i in range(2))
            dissipated=(dot(delta_v,product(M,delta_v))+h*h*dot(new_v,product(K,new_v)))/2
        else:
            matrix=tuple(tuple(M[i][j]+h*h*K[i][j]/4 for j in range(2)) for i in range(2))
            mv,kx=product(M,v),product(K,x)
            midpoint_v=_solve(matrix,tuple(mv[i]-h*kx[i]/2+h*force[i]/2 for i in range(2)))
            new_x=tuple(x[i]+h*midpoint_v[i] for i in range(2))
            new_v=tuple(2*midpoint_v[i]-v[i] for i in range(2));work_velocity=midpoint_v
            dissipated=0.
        step_work=h*dot(force,work_velocity)
        balance=energy(new_x,new_v)-energy(x,v)-step_work+dissipated
        work+=step_work;dissipation+=dissipated
        records.append({'step':n+1,'time':(n+1)*h,'force':force,'positions':new_x,'velocities':new_v,
            'energy':energy(new_x,new_v),'step_work':step_work,'dissipation':dissipated,'balance_error':balance})
        x,v=new_x,new_v
    exact_x,exact_v=pulse_response(DURATION)
    return {'schema':SCHEMA,'method':method,'steps':steps,'records':records,
        'temporal_error':temporal_error(x,v),'relative_energy_error':energy(x,v)/energy(exact_x,exact_v)-1,
        'work':work,'dissipation':dissipation,'production_qualified':False}
