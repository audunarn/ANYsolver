"""Research Lie-midpoint steps with retained cell inertia and endpoint traces.

Not a production integrator, nonlinear energy-momentum method or qualification.
The backward-Euler transaction implementation remains immutable.
"""

from dataclasses import dataclass, replace
import hashlib

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation, skew
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _array, _readonly
from docs.reference_cases.ge_beam3_curved_p5_implicit_dynamics_probe import (
    ImplicitDynamicProbe, DynamicState, DynamicEvaluation, DynamicStepError,
    DynamicTransactionError, left_jacobian, ROTATIONS, DYNAMIC, SCHEMA as BE_SCHEMA,
)


SCHEMA = 'GE_BEAM3_P5_MIDPOINT_RETAINED_SPIN_RESEARCH_V1'


@dataclass(frozen=True)
class MidpointEvaluation(DynamicEvaluation):
    stage_vertex_frames: np.ndarray
    endpoint_elastic_force: np.ndarray
    trace_iterations: int
    trace_evaluations: int
    trace_residual_norm: float


class MidpointDynamicProbe(ImplicitDynamicProbe):
    """Small elastic macrocell: whole-node clamps and spatial dead forces only."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._checkpoint = (replace(self._checkpoint[0], schema=SCHEMA), None)
        self._traces = np.array([6*i+j for i in range(3) if i not in self._fixed
                                 for j in (3,4,5)], dtype=int)

    def _identity(self):
        return hashlib.sha256((SCHEMA+':'+super()._identity()).encode('ascii')).hexdigest()

    def _check_state(self, state):
        if type(state) is not DynamicState or state.schema != SCHEMA:
            raise DynamicTransactionError('midpoint state schema required; no cross-method restart')
        # Reuse shape/clamp/model checks only, after enforcing our distinct
        # public schema. This temporary copy is never stored or published.
        super()._check_state(replace(state, schema=BE_SCHEMA))

    @staticmethod
    def _spatial_stiffness(elastic):
        result = elastic.hessian.copy()
        for start in ROTATIONS:
            result[start:start+3,start:start+3] -= .5*skew(elastic.gradient[start:start+3])
        return result

    def _stage(self, origin, increment, step, forces):
        self._check_state(origin)
        z = _array(increment, (24,), 'midpoint increment')
        forces = _array(forces, (3,3), 'midpoint spatial dead forces')
        if type(step) is not float or not np.isfinite(step) or not 0 < step <= .1:
            raise ValueError('finite positive bounded step required')
        for node in self._fixed:
            if np.any(z[6*node:6*node+6] != 0.): raise ValueError('fixed increment changed')
        chart = np.eye(24)*.5
        for start in ROTATIONS:
            left_jacobian(z[start:start+3])  # also guard the full endpoint step
            scale = 1. if start < 18 else .5
            chart[start:start+3,start:start+3] = scale*left_jacobian(scale*z[start:start+3])
        dx = z[:18].reshape(3,6)[:,:3]
        xm = origin.positions+dx/2
        qm = np.array([rotation(z[6*i+3:6*i+6])@origin.vertex_frames[i] for i in range(3)])
        um = np.array([rotation(z[18+3*c:21+3*c]/2)@origin.cell_rotations[c] for c in (0,1)])
        u1 = np.array([rotation(z[18+3*c:21+3*c])@origin.cell_rotations[c] for c in (0,1)])
        velocity = np.zeros(24); velocity[DYNAMIC] = z[DYNAMIC]/step
        old = np.zeros(24)
        for i in range(3): old[6*i:6*i+3] = origin.nodal_velocity[i]
        old[18:] = origin.cell_angular_velocity.ravel()
        acceleration = 2*(velocity-old)/step
        elastic = self._elastic._jet(xm,qm,um,external=True)
        kinetic = self._kinetic.evaluate(xm,um,velocity,acceleration)
        external = np.zeros(24)
        for i in range(3): external[6*i:6*i+3] = forces[i]
        residual = elastic.gradient+kinetic.inertia-external
        tangent = (self._spatial_stiffness(elastic)+kinetic.configuration_derivative)@chart
        tangent[:,DYNAMIC] += kinetic.velocity_derivative[:,DYNAMIC]/step+2*kinetic.mass[:,DYNAMIC]/step**2
        endpoint_velocity = 2*velocity-old
        # Qm is an endpoint starting guess only, not a solved endpoint trace.
        state = DynamicState(SCHEMA,origin.model_sha256,origin.epoch+1,float(origin.time+step),
            _readonly(origin.positions+dx),_readonly(qm),_readonly(u1),
            _readonly(endpoint_velocity[:18].reshape(3,6)[:,:3]),
            _readonly(endpoint_velocity[18:].reshape(2,3)))
        self._check_state(state)
        if state.time <= origin.time: raise ValueError('step cannot advance represented time')
        if not np.isfinite(residual).all() or not np.isfinite(tangent).all():
            raise ValueError('nonfinite midpoint balance')
        return DynamicEvaluation(state,float(elastic.value),kinetic.kinetic_energy,
            _readonly(residual),_readonly(tangent),_readonly(elastic.gradient),kinetic.inertia)

    def _recover_traces(self, state):
        self._check_state(state)
        frames = state.vertex_frames.copy(); count = 0

        def evaluate(q):
            nonlocal count
            if count >= 64: raise DynamicStepError('endpoint trace evaluation bound reached')
            count += 1
            value = self._elastic._jet(state.positions,q,state.cell_rotations,external=True)
            norm = float(np.linalg.norm(value.gradient[self._traces])/self._length)
            if not np.isfinite(norm): raise ValueError('nonfinite endpoint trace balance')
            return value,norm

        elastic,norm = evaluate(frames)
        for iteration in range(9):
            if norm <= 1e-11:
                return replace(state,vertex_frames=_readonly(frames)),elastic,iteration,count,norm
            if iteration == 8: raise DynamicStepError('endpoint trace update bound reached')
            tangent = self._spatial_stiffness(elastic)
            delta = np.zeros(24)
            delta[self._traces] = np.linalg.solve(tangent[np.ix_(self._traces,self._traces)],-elastic.gradient[self._traces])
            for backtrack in range(10):
                candidate = frames.copy()
                try:
                    for node in range(3):
                        if node in self._fixed: continue
                        spin = (.5**backtrack)*delta[6*node+3:6*node+6]
                        left_jacobian(spin)
                        candidate[node] = rotation(spin)@frames[node]
                    made,new_norm = evaluate(candidate)
                except ValueError: continue
                if new_norm < norm:
                    frames,elastic,norm = candidate,made,new_norm
                    break
            else: raise DynamicStepError('endpoint trace line search failed')
        raise AssertionError('unreachable')

    def _evaluate(self, origin, increment, step, forces):
        stage = self._stage(origin,increment,step,forces)
        state,elastic,iterations,evaluations,norm = self._recover_traces(stage.state)
        self._check_state(state)
        velocity = np.zeros(24)
        for i in range(3): velocity[6*i:6*i+3] = state.nodal_velocity[i]
        velocity[18:] = state.cell_angular_velocity.ravel()
        kinetic = self._kinetic.evaluate(state.positions,state.cell_rotations,velocity,np.zeros(24))
        return MidpointEvaluation(state,float(elastic.value),kinetic.kinetic_energy,
            stage.residual,stage.tangent,stage.elastic_force,stage.inertia,
            stage.state.vertex_frames,_readonly(elastic.gradient),iterations,evaluations,norm)
