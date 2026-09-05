"""Standalone strong-form shooting reference, not the discrete beam mechanics.

Source: arXiv:2605.04573v3, section 2.3/2.4 strain and equilibrium relations.
This module imports no ANYsolver or other reference-case implementation.
The coupled directed-hardening stress inversion is separately derived here.
Only a single increment from virgin history is admitted, not a load history.
"""

from dataclasses import dataclass

import numpy as np


class ContinuumReferenceError(ValueError):
    """Invalid input or bounded continuum solve did not converge."""


def _skew(v):
    x,y,z = v
    return np.array([[0.,-z,y],[z,0.,-x],[-y,x,0.]])


def _finite(value, shape):
    made = np.array(value,dtype=float,copy=True)
    if made.shape != shape or not np.isfinite(made).all():
        raise ContinuumReferenceError('finite reference input with exact shape required')
    return made


@dataclass(frozen=True)
class ShootingResult:
    coordinates: np.ndarray
    frames: np.ndarray
    spatial_moments: np.ndarray
    material_resultants: np.ndarray
    strains: np.ndarray
    plastic_coordinates: np.ndarray
    potential: float
    root_moment: np.ndarray
    tip_moment_residual: float
    orthogonality_error: float
    steps: int
    iterations: int
    integrations: int


class VirginParabolicCantileverReference:
    """r0(t)=(t,h(1-t*t),0), t in [-1,1], material axis 2 = global z.

Integrate r_t=J R(e1+gamma), R_t=J R hat(kappa0+kappa).
Spatial n=F and m=m_left-(r-r_left) cross F enforce force/moment balance.
Shoot the three left-end moments to enforce m_right=0. A fixed RK4 grid
integrates exact first sensitivities to those three shooting parameters.
No frame finite difference, normalization or polar projection is used.
"""

    def __init__(self, height, elastic, direction, yield_force, hardening):
        if isinstance(height,bool) or not np.isfinite(height) or not 0 <= height <= .75:
            raise ContinuumReferenceError('bounded parabolic reference height required')
        self.height = float(height)
        self.elastic = _finite(elastic,(6,6))
        if not np.array_equal(self.elastic,self.elastic.T):
            raise ContinuumReferenceError('exactly symmetric section required')
        try:
            np.linalg.cholesky(self.elastic)
            self.compliance = np.linalg.solve(self.elastic,np.eye(6))
        except np.linalg.LinAlgError as exc:
            raise ContinuumReferenceError('positive definite section required') from exc
        self.direction = _finite(direction,(6,))
        if not np.any(self.direction):
            raise ContinuumReferenceError('nonzero directed-hardening direction required')
        if any(isinstance(v,bool) or not np.isfinite(v) or v <= 0 for v in (yield_force,hardening)):
            raise ContinuumReferenceError('positive yield and hardening required')
        self.yield_force,self.hardening = float(yield_force),float(hardening)
        self.left = np.array([-1.,0.,0.])
        tangent = np.array([1.,2*self.height,0.]);tangent /= np.linalg.norm(tangent)
        normal = np.array([0.,0.,1.])
        self.left_frame = np.column_stack((tangent,normal,np.cross(tangent,normal)))

    def section_inverse(self, stress):
        """Virgin-history stress-controlled inverse and its exact branch derivative."""
        stress = _finite(stress,(6,))
        drive = float(self.direction @ stress)
        active = abs(drive) > self.yield_force
        z = np.sign(drive)*(abs(drive)-self.yield_force)/self.hardening if active else 0.
        strain = self.compliance @ stress+z*self.direction
        derivative = self.compliance+np.outer(self.direction,self.direction)/self.hardening if active else self.compliance
        potential = float(.5*stress @ self.compliance @ stress+.5*self.hardening*z*z+self.yield_force*abs(z))
        return strain, derivative, float(z), potential

    def _inverse_at(self, t, stress):
        # The virgin law is spatially uniform. History-reference successors
        # may override this hook with an explicitly fixed material-origin grid.
        return self.section_inverse(stress)

    def _rhs(self, t, state, moment, force):
        r,R = state[:3],state[3:12].reshape(3,3)
        sensitivity = state[13:].reshape(12,3)
        m = moment-np.cross(r-self.left,force)
        stress = np.r_[R.T @ force,R.T @ m]
        strain,compliance,_,potential = self._inverse_at(t,stress)
        jacobian = np.sqrt(1+4*self.height*self.height*t*t)
        k0 = np.array([0.,-2*self.height/jacobian**3,0.])
        velocity = np.array([1.,0.,0.])+strain[:3]
        curvature = k0+strain[3:]
        derivative = np.empty_like(state)
        derivative[:3] = jacobian*(R @ velocity)
        derivative[3:12] = (jacobian*R @ _skew(curvature)).ravel()
        derivative[12] = jacobian*potential
        output = derivative[13:].reshape(12,3)
        for j in range(3):
            dr,dR = sensitivity[:3,j],sensitivity[3:,j].reshape(3,3)
            dm = np.eye(3)[:,j]-np.cross(dr,force)
            dstress = np.r_[dR.T @ force,dR.T @ m+R.T @ dm]
            dstrain = compliance @ dstress
            output[:3,j] = jacobian*(dR @ velocity+R @ dstrain[:3])
            output[3:,j] = (jacobian*(dR @ _skew(curvature)+R @ _skew(dstrain[3:]))).ravel()
        return derivative

    def integrate(self, root_moment, force, *, steps=256):
        if type(steps) is not int or steps not in (32,64,128,256,512):
            raise ContinuumReferenceError('registered bounded RK4 grid required')
        moment,force = _finite(root_moment,(3,)),_finite(force,(3,))
        state = np.r_[self.left,self.left_frame.ravel(),0.,np.zeros(36)]
        states = [state.copy()]
        delta = 2./steps
        for i in range(steps):
            t = -1+i*delta
            k1 = self._rhs(t,state,moment,force)
            k2 = self._rhs(t+delta/2,state+delta*k1/2,moment,force)
            k3 = self._rhs(t+delta/2,state+delta*k2/2,moment,force)
            k4 = self._rhs(t+delta,state+delta*k3,moment,force)
            state = state+delta*(k1+2*k2+2*k3+k4)/6
            if not np.isfinite(state).all() or np.max(np.abs(state)) > 1e8:
                raise ContinuumReferenceError('continuum integration left bounded state domain')
            states.append(state.copy())
        residual = moment-np.cross(state[:3]-self.left,force)
        dr = state[13:].reshape(12,3)[:3]
        jacobian = np.column_stack([np.eye(3)[:,j]-np.cross(dr[:,j],force) for j in range(3)])
        return np.array(states),residual,jacobian

    def solve(self, force, *, steps=256, max_iterations=12, max_integrations=32):
        force = _finite(force,(3,))
        for value,bound in ((max_iterations,12),(max_integrations,32)):
            if type(value) is not int or not 0 <= value <= bound:
                raise ContinuumReferenceError('bounded shooting controls required')
        count = 0
        def evaluate(moment):
            nonlocal count
            if count >= max_integrations:
                raise ContinuumReferenceError('shooting integration budget exhausted')
            count += 1
            return self.integrate(moment,force,steps=steps)
        moment = np.cross(np.array([2.,0.,0.]),force)
        states,residual,jacobian = evaluate(moment)
        for iteration in range(max_iterations+1):
            norm = float(np.linalg.norm(residual))
            if norm <= 1e-12:
                frames = states[:,3:12].reshape(-1,3,3)
                error = float(np.max(np.linalg.norm(frames.transpose(0,2,1) @ frames-np.eye(3),axis=(1,2))))
                # This is a reference health check, not a projection or an error estimate.
                if error > 1e-7 or np.min(np.linalg.det(frames)) <= 0:
                    raise ContinuumReferenceError('unresolved integrated frame drift; refine explicitly')
                spatial = moment-np.cross(states[:,:3]-self.left,force)
                stresses = np.column_stack((np.einsum('nji,j->ni',frames,force),
                                           np.einsum('nji,nj->ni',frames,spatial)))
                inverse = [self._inverse_at(t,s) for t,s in zip(np.linspace(-1.,1.,steps+1),stresses)]
                return ShootingResult(states[:,:3],frames,spatial,stresses,np.array([s[0] for s in inverse]),
                    np.array([s[2] for s in inverse]),float(states[-1,12]),moment.copy(),norm,error,steps,iteration,count)
            if iteration == max_iterations:
                raise ContinuumReferenceError('shooting iteration budget exhausted')
            try:
                step = np.linalg.solve(jacobian,-residual)
            except np.linalg.LinAlgError as exc:
                raise ContinuumReferenceError('singular shooting Jacobian') from exc
            for backtrack in range(8):
                made_moment = moment+(.5**backtrack)*step
                made_states,made_residual,made_jacobian = evaluate(made_moment)
                if np.linalg.norm(made_residual) < norm:
                    moment,states,residual,jacobian = made_moment,made_states,made_residual,made_jacobian
                    break
            else:
                raise ContinuumReferenceError('shooting line search exhausted')
        raise AssertionError('unreachable shooting iteration')
