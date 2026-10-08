"""Independent four-P1-cell axial reference; no native or solver imports.

Two native elements each have two AFFINE retained half-cell chords. This is not
an assumed quadratic axial bar. Numerical routines execute only when invoked.
"""
import numpy as np

EA=1.e5
RHO_A=2.
ELL=.5
AMPLITUDE=2.e-5
DT=2.**-16
ORIGIN=np.array((.25,-.5,.125))
DIRECTION=np.array((0.,1.,0.))
FRAME=np.array(((0.,-1.,0.),(1.,0.,0.),(0.,0.,1.)))
FORCE_SCALE=1.                         # N, initial axial half-cell tension
MOMENT_SCALE=1.                        # N m, positive declared world-origin scale
ENERGY_SCALE=1.e-5                     # J, four initial half-cell elastic energies
VELOCITY_SCALE=AMPLITUDE*np.sqrt(EA/RHO_A)/(4*ELL)
ACCELERATION_SCALE=AMPLITUDE*EA/RHO_A/ELL**2


def operators():
    """Primitive weak-form integrals; not a production FE/operator recovery."""
    mass=np.zeros((5,5));stiffness=np.zeros((5,5))
    for left in range(4):
        ix=np.ix_((left,left+1),(left,left+1))
        mass[ix]+=RHO_A*ELL/6*np.array(((2.,1.),(1.,2.)))
        stiffness[ix]+=EA/ELL*np.array(((1.,-1.),(-1.,1.)))
    return mass,stiffness


def initial():
    return AMPLITUDE*np.arange(5)/4,np.zeros(5)


def account(q,v):
    mass,stiffness=operators()
    potential=.5*float(q@stiffness@q);kinetic=.5*float(v@mass@v)
    linear=DIRECTION*float(np.ones(5)@mass@v)
    # Position remains on the offset axis; axial displacement contributes no arm.
    angular=np.cross(ORIGIN,linear)
    return dict(elastic_energy=potential,kinetic_energy=kinetic,
                total_energy=potential+kinetic,linear_momentum=linear,angular_momentum=angular)


def endpoint_acceleration(q):
    mass,stiffness=operators();a=np.zeros(5)
    a[1:]=np.linalg.solve(mass[1:,1:],-stiffness[1:,1:]@q[1:])
    return a


def step(q,v,h):
    """Independent scalar implicit-midpoint weak balance; root q/v/a exactly0."""
    mass,stiffness=operators();a=np.zeros(5)
    a[1:]=np.linalg.solve(mass[1:,1:]+.25*h*h*stiffness[1:,1:],
                         -stiffness[1:,1:]@(q[1:]+.5*h*v[1:]))
    endq=q+h*v+.5*h*h*a;endv=v+h*a
    stageq=.5*(q+endq);stagev=.5*(v+endv)
    residual=mass@a+stiffness@stageq
    support_force=DIRECTION*residual[0]
    return dict(q=endq,v=endv,a=endpoint_acceleration(endq),stage_q=stageq,
        stage_v=stagev,stage_a=a,support_force=support_force,
        support_moment=np.cross(ORIGIN,support_force),
        force_impulse=h*support_force,moment_impulse=h*np.cross(ORIGIN,support_force),
        support_work=0.,half_cell_forces=EA/ELL*np.diff(stageq))


def semidiscrete_exact(t):
    """Analytical semidiscrete vibration via symmetric mass-weighted modes."""
    mass,stiffness=operators();mf=mass[1:,1:];kf=stiffness[1:,1:]
    chol=np.linalg.cholesky(mf)
    transform=np.linalg.solve(chol,kf)@np.linalg.inv(chol.T)
    eigenvalues,modes=np.linalg.eigh(transform)
    omega=np.sqrt(eigenvalues);q0,v0=initial()
    y0=modes.T@chol.T@q0[1:];yd0=modes.T@chol.T@v0[1:]
    c=np.cos(omega*t);s=np.sin(omega*t)
    y=y0*c+yd0*s/omega;yd=-omega*y0*s+yd0*c
    q=np.zeros(5);v=np.zeros(5);a=np.zeros(5)
    q[1:]=np.linalg.solve(chol.T,modes@y)
    v[1:]=np.linalg.solve(chol.T,modes@yd)
    a[1:]=np.linalg.solve(chol.T,modes@(-eigenvalues*y))
    return q,v,a
