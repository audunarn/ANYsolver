"""Fixed-grid material-history extension of the separate continuum reference.

No discrete beam, section, AD, recovery or production state implementation is
imported. Every shooting candidate sees exactly the supplied prior histories.
Returned history fields are explicit next-increment inputs, not live commits.
"""

from dataclasses import dataclass

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_nonlinear_continuum_reference import (
    VirginParabolicCantileverReference, ContinuumReferenceError, ShootingResult, _finite,
)


def _readonly(value):
    made = np.array(value,copy=True)
    made.setflags(write=False)
    return made


@dataclass(frozen=True)
class HistoryShootingResult:
    response: ShootingResult
    force: np.ndarray
    dense_coordinates: np.ndarray
    dense_frames: np.ndarray
    material_resultants: np.ndarray
    strains: np.ndarray
    origins: np.ndarray
    histories: np.ndarray
    dissipation_increments: np.ndarray
    dense_orthogonality_error: float
    integrations_total: int


class HistoryParabolicCantileverReference(VirginParabolicCantileverReference):
    """Origin grid includes every RK4 endpoint and midpoint, with fixed N.

Accepted midpoint positions/frames use cubic Hermite dense reconstruction
from RK4 endpoint states and their actual ODE derivatives. This is a finite
grid history approximation, whose accuracy must be checked by refinement.
No interpolation or history update occurs inside a shooting candidate.
"""

    def __init__(self, height, elastic, direction, yield_force, hardening, *, steps=128, origins=None):
        super().__init__(height,elastic,direction,yield_force,hardening)
        if type(steps) is not int or steps not in (32,64,128,256,512):
            raise ContinuumReferenceError('fixed registered history grid required')
        self.steps = steps
        history = np.zeros((2*steps+1,2)) if origins is None else _finite(origins,(2*steps+1,2))
        if np.any(history[:,1] < np.abs(history[:,0])):
            raise ContinuumReferenceError('history requires accumulated >= absolute plastic coordinate')
        self.origins = _readonly(history)

    def section_inverse(self, stress):
        raise ContinuumReferenceError('explicit history or material grid coordinate required')

    def stress_inverse(self, stress, origin):
        stress,origin = _finite(stress,(6,)),_finite(origin,(2,))
        z0,p0 = origin
        if p0 < abs(z0):
            raise ContinuumReferenceError('invalid material history')
        drive = float(self.direction @ stress)
        threshold = self.yield_force+self.hardening*p0
        increment = max(0.,(abs(drive)-threshold)/self.hardening)
        z = z0+np.sign(drive)*increment
        p = p0+increment
        strain = self.compliance @ stress+z*self.direction
        derivative = (self.compliance+np.outer(self.direction,self.direction)/self.hardening
                      if increment > 0 else self.compliance)
        dissipation = self.yield_force*increment
        potential = float(.5*stress @ self.compliance @ stress+.5*self.hardening*(p*p-p0*p0)+dissipation)
        if not np.isfinite([z,p,potential,dissipation]).all():
            raise ContinuumReferenceError('nonfinite history inverse')
        return strain,derivative,float(z),float(p),potential,float(dissipation)

    def _origin_at(self, t):
        coordinate = (t+1)*self.steps
        if not np.isfinite(coordinate) or coordinate != int(coordinate) or not 0 <= coordinate <= 2*self.steps:
            raise ContinuumReferenceError('history access must use a registered RK4 material point')
        return self.origins[int(coordinate)]

    def _inverse_at(self, t, stress):
        strain,derivative,z,_,potential,_ = self.stress_inverse(stress,self._origin_at(t))
        return strain,derivative,z,potential

    def integrate(self, root_moment, force, *, steps=None):
        if steps is None:
            steps = self.steps
        if type(steps) is not int or steps != self.steps:
            raise ContinuumReferenceError('history grid cannot change during an increment')
        return super().integrate(root_moment,force,steps=steps)

    def solve(self, force, *, steps=None, max_iterations=12, max_integrations=32):
        if steps is not None and (type(steps) is not int or steps != self.steps):
            raise ContinuumReferenceError('history grid cannot change during an increment')
        if type(max_integrations) is not int or not 0 <= max_integrations <= 32:
            raise ContinuumReferenceError('bounded history integrations required')
        if max_integrations < 2:
            raise ContinuumReferenceError('history solve/reconstruction budget exhausted')
        force = _finite(force,(3,))
        # Reserve one integration for accepted-field replay and dense output.
        result = super().solve(force,steps=self.steps,max_iterations=max_iterations,
                               max_integrations=max_integrations-1)
        states,residual,_ = self.integrate(result.root_moment,force)
        if (not np.array_equal(states[:,:3],result.coordinates)
                or not np.array_equal(states[:,3:12].reshape(-1,3,3),result.frames)
                or float(states[-1,12]) != result.potential
                or float(np.linalg.norm(residual)) != result.tip_moment_residual):
            raise ContinuumReferenceError('accepted history shooting replay mismatch')
        delta = 2./self.steps
        t = np.linspace(-1.,1.,self.steps+1)
        derivatives = np.array([self._rhs(ti,si,result.root_moment,force) for ti,si in zip(t,states)])
        dense = np.empty((2*self.steps+1,12))
        dense[::2] = states[:,:12]
        dense[1::2] = .5*(states[:-1,:12]+states[1:,:12])+delta/8*(derivatives[:-1,:12]-derivatives[1:,:12])
        frames = dense[:,3:12].reshape(-1,3,3)
        error = float(np.max(np.linalg.norm(frames.transpose(0,2,1) @ frames-np.eye(3),axis=(1,2))))
        if not np.isfinite(dense).all() or error > 1e-7 or np.min(np.linalg.det(frames)) <= 0:
            raise ContinuumReferenceError('unresolved dense history frame drift; refine explicitly')
        spatial = result.root_moment-np.cross(dense[:,:3]-self.left,force)
        stresses = np.column_stack((np.einsum('nji,j->ni',frames,force),np.einsum('nji,nj->ni',frames,spatial)))
        inverse = [self.stress_inverse(s,h) for s,h in zip(stresses,self.origins)]
        histories = np.array([[s[2],s[3]] for s in inverse])
        if np.any(histories[:,1] < self.origins[:,1]) or np.any(histories[:,1] < np.abs(histories[:,0])):
            raise ContinuumReferenceError('invalid advanced material history')
        return HistoryShootingResult(result,_readonly(force),_readonly(dense[:,:3]),_readonly(frames),_readonly(stresses),
            _readonly([s[0] for s in inverse]),_readonly(self.origins),_readonly(histories),
            _readonly([s[5] for s in inverse]),error,result.integrations+1)
