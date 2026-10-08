"""Independent small-motion Timoshenko cantilever/finite-foundation reference.

No ANYsolver imports. Downward displacement w and rotation theta are positive.
The reference length is L; the fixed plane clearance from the declared tube is c.
Shear Q=S(w'-theta), moment M=D theta', M'=-Q and
Q'=k(w-c)_+-q. Thus each fixed branch is a constant four-state ODE. This
reference admits one active interval [a,L] only; it rejects an unverified branch.
It is a development discriminator, not a registered acceptance reference yet.
"""
from dataclasses import dataclass
import numpy as np
from scipy.linalg import expm
from scipy.optimize import brentq


@dataclass(frozen=True)
class FoundationReference:
    length: float
    clearance: float
    bending: float
    shear: float
    load: float
    line_stiffness: float
    front: float
    initial_scaled_state: np.ndarray
    open_generator: np.ndarray
    active_generator: np.ndarray
    boundary_residual: float
    front_residual: float
    contact_velocity_lower: float
    endpoint_stiffness: float = 0.
    tip_force: float = 0.

    def state(self, x):
        """Return w[m], theta[rad], M[Nm], Q[N] on original physical x."""
        x = float(x)
        if not 0 <= x <= self.length:
            raise ValueError("reference station outside beam")
        xi = x/self.length
        a = self.front/self.length
        value = expm(self.open_generator*min(xi,a))@self.initial_scaled_state
        if xi > a:
            value = expm(self.active_generator*(xi-a))@value
        scale = np.array((self.clearance, self.clearance/self.length,
                          self.bending*self.clearance/self.length**2,
                          self.bending*self.clearance/self.length**3))
        return value[:4]*scale

    @property
    def reaction(self):
        return self.load*self.length+self.tip_force-self.state(0)[3]


def cantilever_foundation_reference(*, length, clearance, bending, shear,
                                    load, line_stiffness, endpoint_stiffness=0.,
                                    tip_force=0.):
    values = np.array((length,clearance,bending,shear,load,line_stiffness),float)
    P=float(tip_force)
    if (not np.all(np.isfinite(values)) or np.min(values[[0,1,2,3,5]]) <= 0
            or values[4]<0 or not np.isfinite(P) or P<0 or values[4]+P<=0):
        raise ValueError("reference parameters must be finite and positive")
    L,c,D,S,q,k = values
    ke = float(endpoint_stiffness)
    if not np.isfinite(ke) or ke < 0:
        raise ValueError('reference endpoint stiffness must be nonnegative in N/m')
    endpoint_scaled = ke*L**3/D
    sigma = D/(S*L**2)
    beta = k*L**4/D
    qbar = q*L**4/(D*c)
    pbar = P*L**3/(D*c)
    free_tip = qbar/8+sigma*qbar/2+pbar/3+sigma*pbar
    if free_tip <= 1:
        raise ValueError("reference has no active foundation interval")

    def generator(active):
        matrix = np.zeros((5,5))
        matrix[0,1]=matrix[1,2]=1
        matrix[0,3]=sigma
        matrix[2,3]=-1
        matrix[3,0]=beta if active else 0
        matrix[3,4]=-qbar-(beta if active else 0)
        return matrix

    opened, active = generator(False), generator(True)

    def initial(a):
        total = expm(active*(1-a))@expm(opened*a)
        seed = np.array((0.,0.,0.,0.,1.))
        # Natural tip work: M(L)=0 and Q(L)+ke*(w(L)-c)=P.
        # This branch is checked active/monotone below. The zero-ke path
        # retains the original operations and numerical reference identity.
        if ke == 0. and P == 0.:
            seed[2:4] = np.linalg.solve(total[2:4,2:4],-total[2:4,4])
        elif ke == 0.:
            seed[2:4] = np.linalg.solve(total[2:4,2:4],
                np.array((0.,pbar))-total[2:4,4])
        else:
            rows = np.vstack((total[2],total[3]+endpoint_scaled*total[0]))
            seed[2:4] = np.linalg.solve(rows[:,2:4],
                np.array((0.,endpoint_scaled+pbar))-rows[:,4])
        return seed

    def front_equation(a):
        if a == 0:
            return -1.
        return float((expm(opened*a)@initial(a))[0]-1)

    a = brentq(front_equation,0.,1.,xtol=5e-15,rtol=4*np.finfo(float).eps)
    seed = initial(a)
    at_front = expm(opened*a)@seed
    at_end = expm(active*(1-a))@at_front
    boundary = (float(np.linalg.norm(at_end[2:4])) if P == 0. and ke == 0.
        else float(np.linalg.norm((at_end[2],
            at_end[3]+endpoint_scaled*(at_end[0]-1.)-pbar))))
    front_error = abs(float(at_front[0]-1))
    if max(boundary,front_error)>1e-9:
        raise ValueError("reference transfer boundary/front solve is unresolved")

    # Open-branch w is a quartic polynomial, so all its extrema are available.
    # Its derivative is theta+sigma*Q with theta integral of quadratic M.
    M0,Q0 = seed[2:4]
    derivative = np.array((qbar/6,-Q0/2,M0-sigma*qbar,sigma*Q0))
    extrema = [0.,a]+[float(z.real) for z in np.roots(derivative)
                         if abs(z.imag)<1e-12 and 0<z.real<a]
    if any(float((expm(opened*x)@seed)[0])>1+1e-9 for x in extrema):
        raise ValueError("reference needs additional active intervals")

    # Bound active-branch velocity variation on sixteen intervals using
    # ||exp(Ahat*t)||inf <= exp(||Ahat||inf*t). Characteristic scaling avoids
    # a vacuous estimate from the large dimensional foundation entry.
    alpha = max(1.,beta**.25)
    scaling = np.array((1.,alpha,alpha**2,alpha**3,1.))
    ahat = active*scaling[None,:]/scaling[:,None]
    norm_a = np.linalg.norm(ahat,np.inf)
    velocity_row = np.array((0.,1.,0.,sigma,0.))
    acceleration_norm = np.sum(np.abs((velocity_row@active)*scaling))
    width = (1-a)/16
    lower = np.inf
    for j in range(16):
        station = expm(active*(j*width))@at_front
        bound = acceleration_norm*np.linalg.norm(station/scaling,np.inf)*np.exp(norm_a*width)
        lower = min(lower,float(velocity_row@station)-width*bound)
    # A conservative floating margin keeps this branch control separate from
    # the response comparison. Expm uncertainty still needs qualification.
    if not np.isfinite(lower) or lower <= 1e-9:
        raise ValueError("reference single active branch is not resolved monotone")
    return FoundationReference(L,c,D,S,q,k,a*L,seed,opened,active,
                               boundary,front_error,lower*c/L,ke,P)
