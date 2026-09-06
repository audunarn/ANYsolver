"""Bounded first-order implicit retained-spin research transactions.

Not a production transient solver or qualified integration policy. Elastic
sections only; cell inertia is retained, vertex traces stay algebraic.
"""

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json

import numpy as np

from anysolver.ge_beam3_curved_reference import CurvedBeam3ReferenceGeometry
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation,skew
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import CurvedFiniteProbe,_array,_frames,_readonly
from docs.reference_cases.ge_beam3_curved_p5_finite_inertia_probe import FiniteInertiaProbe
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest


SCHEMA = 'GE_BEAM3_P5_IMPLICIT_RETAINED_SPIN_RESEARCH_V1'
ROTATIONS = (3,9,15,18,21)
DYNAMIC = np.array([0,1,2,6,7,8,12,13,14,18,19,20,21,22,23])


class DynamicStepError(RuntimeError):
    """Bounded step failed without changing the committed state."""


class DynamicTransactionError(RuntimeError):
    """Foreign, stale, altered or nonreproducible transaction."""


def left_jacobian(vector):
    vector = _array(vector,(3,),'rotation increment');theta = float(np.linalg.norm(vector))
    if theta >= .9*np.pi: raise ValueError('rotation step requires explicit cutback')
    cross = skew(vector)
    if theta < 1e-4:
        a = .5-theta**2/24+theta**4/720
        b = 1/6-theta**2/120+theta**4/5040
    else:
        a = (1-np.cos(theta))/theta**2;b = (theta-np.sin(theta))/theta**3
    return np.eye(3)+a*cross+b*(cross@cross)


@dataclass(frozen=True)
class DynamicState:
    schema: str
    model_sha256: str
    epoch: int
    time: float
    positions: np.ndarray
    vertex_frames: np.ndarray
    cell_rotations: np.ndarray
    nodal_velocity: np.ndarray
    cell_angular_velocity: np.ndarray


@dataclass(frozen=True)
class DynamicEvaluation:
    state: DynamicState
    elastic_energy: float
    kinetic_energy: float
    residual: np.ndarray
    tangent: np.ndarray
    elastic_force: np.ndarray
    inertia: np.ndarray


@dataclass(frozen=True)
class DynamicTrial:
    origin: DynamicState
    increment: np.ndarray
    step: float
    forces: np.ndarray
    response: DynamicEvaluation
    residual_norm: float
    iterations: int
    evaluations: int


class ImplicitDynamicProbe:
    def __init__(self,reference,section,section_mass,*,order=8,fixed_nodes=(0,)):
        if (type(fixed_nodes) is not tuple or len(set(fixed_nodes)) != len(fixed_nodes) or
                any(type(n) is not int or n not in (0,1,2) for n in fixed_nodes)):
            raise ValueError('distinct whole-node clamp tuple required')
        self._reference = CurvedBeam3ReferenceGeometry(reference.coordinates,reference.nodal_triads)
        self._elastic = CurvedFiniteProbe(self._reference,section,order=order)
        self._kinetic = FiniteInertiaProbe(self._reference,section_mass,order=order)
        self._fixed = tuple(sorted(fixed_nodes));self._order = order
        self._free = np.array([i for i in range(24) if i>=18 or i//6 not in self._fixed])
        self._length = max(np.linalg.norm(a-b) for a in self._reference.coordinates for b in self._reference.coordinates)
        state = DynamicState(SCHEMA,self._identity(),0,0.,_readonly(self._reference.coordinates),
            _readonly(self._reference.nodal_triads),_readonly(np.tile(np.eye(3),(2,1,1))),
            _readonly(np.zeros((3,3))),_readonly(np.zeros((2,3))))
        self._checkpoint = (state,None);self._pending = self._pending_digest = None

    def _identity(self):
        record = {'schema':SCHEMA,'coordinates':self._reference.coordinates,'triads':self._reference.nodal_triads,
            'section':self._elastic.section,'inertia':self._kinetic.section_mass,'order':self._order,'fixed':self._fixed}
        return hashlib.sha256(json.dumps(record,sort_keys=True,separators=(',',':'),allow_nan=False,
            default=lambda a:a.tolist()).encode('ascii')).hexdigest()

    @property
    def committed(self): return deepcopy(self._checkpoint[0])

    def _check_state(self,state):
        if (type(state) is not DynamicState or state.schema != SCHEMA or state.model_sha256 != self._identity() or
                type(state.epoch) is not int or state.epoch<0 or type(state.time) is not float or not np.isfinite(state.time) or state.time<0):
            raise DynamicTransactionError('dynamic state/model identity mismatch')
        _array(state.positions,(3,3),'state positions');_frames(state.vertex_frames,3,'state vertex frames')
        _frames(state.cell_rotations,2,'state cell rotations');_array(state.nodal_velocity,(3,3),'state velocities')
        _array(state.cell_angular_velocity,(2,3),'state cell velocities')
        for node in self._fixed:
            if (not np.array_equal(state.positions[node],self._reference.coordinates[node]) or
                    not np.array_equal(state.vertex_frames[node],self._reference.nodal_triads[node]) or
                    np.any(state.nodal_velocity[node] != 0.)):
                raise DynamicTransactionError('fixed dynamic state changed')

    def _norm(self,residual,forces):
        scaled=residual.copy()
        for start in ROTATIONS: scaled[start:start+3]/=self._length
        return float(np.linalg.norm(scaled[self._free])/max(1.,np.linalg.norm(forces)))

    def _evaluate(self,origin,increment,step,forces):
        self._check_state(origin)
        z=_array(increment,(24,),'dynamic increment');forces=_array(forces,(3,3),'dead nodal forces')
        if type(step) is not float or not np.isfinite(step) or not 0<step<=.1:
            raise ValueError('finite positive bounded step required')
        for node in self._fixed:
            if np.any(z[6*node:6*node+6] != 0.): raise ValueError('fixed increment changed')
        chart=np.eye(24)
        for start in ROTATIONS: chart[start:start+3,start:start+3]=left_jacobian(z[start:start+3])
        x=origin.positions+z[:18].reshape(3,6)[:,:3]
        q=np.array([rotation(z[6*i+3:6*i+6])@origin.vertex_frames[i] for i in range(3)])
        u=np.array([rotation(z[18+3*c:21+3*c])@origin.cell_rotations[c] for c in (0,1)])
        velocity=np.zeros(24);velocity[DYNAMIC]=z[DYNAMIC]/step
        old=np.zeros(24)
        for i in range(3): old[6*i:6*i+3]=origin.nodal_velocity[i]
        old[18:]=origin.cell_angular_velocity.ravel()
        acceleration=(velocity-old)/step
        # Partially condensed moment potential ONLY. Do not call a local spin solve.
        elastic=self._elastic._jet(x,q,u,external=True)
        stiffness=elastic.hessian.copy()
        for start in ROTATIONS: stiffness[start:start+3,start:start+3]-=.5*skew(elastic.gradient[start:start+3])
        kinetic=self._kinetic.evaluate(x,u,velocity,acceleration)
        external=np.zeros(24)
        for i in range(3): external[6*i:6*i+3]=forces[i]
        residual=elastic.gradient+kinetic.inertia-external
        tangent=(stiffness+kinetic.configuration_derivative)@chart
        tangent[:,DYNAMIC]+=kinetic.velocity_derivative[:,DYNAMIC]/step+kinetic.mass[:,DYNAMIC]/step**2
        state=DynamicState(SCHEMA,origin.model_sha256,origin.epoch+1,float(origin.time+step),
            _readonly(x),_readonly(q),_readonly(u),_readonly(velocity[:18].reshape(3,6)[:,:3]),
            _readonly(velocity[18:].reshape(2,3)))
        self._check_state(state)
        if state.time<=origin.time: raise ValueError('dynamic step cannot advance the represented time')
        if not np.isfinite(residual).all() or not np.isfinite(tangent).all(): raise ValueError('nonfinite dynamic balance')
        return DynamicEvaluation(state,float(elastic.value),kinetic.kinetic_energy,_readonly(residual),
            _readonly(tangent),_readonly(elastic.gradient),kinetic.inertia)

    def trial(self,step,forces,*,max_iterations=16,max_evaluations=128):
        if self._pending is not None: raise DynamicTransactionError('explicit commit/discard required')
        if (type(max_iterations) is not int or not 0<=max_iterations<=16 or
                type(max_evaluations) is not int or not 1<=max_evaluations<=128):
            raise ValueError('bounded dynamic update/evaluation counts required')
        forces=_array(forces,(3,3),'dead nodal forces');origin=self.committed;count=0
        z=np.zeros(24)
        def evaluate(value):
            nonlocal count
            if count>=max_evaluations: raise DynamicStepError('dynamic evaluation budget reached')
            count+=1
            result=self._evaluate(origin,value,step,forces)
            return result,self._norm(result.residual,forces)
        try:
            response,norm=evaluate(z)
            for iteration in range(max_iterations+1):
                if norm<=1e-11:
                    trial=DynamicTrial(origin,_readonly(z),step,_readonly(forces),response,norm,iteration,count)
                    self._pending,self._pending_digest=trial,digest(trial)
                    return trial
                if iteration==max_iterations: raise DynamicStepError('dynamic Newton update bound reached')
                delta=np.zeros(24)
                delta[self._free]=np.linalg.solve(response.tangent[np.ix_(self._free,self._free)],-response.residual[self._free])
                if not np.isfinite(delta).all(): raise DynamicStepError('nonfinite dynamic correction')
                for backtrack in range(10):
                    candidate=z+(.5**backtrack)*delta
                    try: made,new_norm=evaluate(candidate)
                    except ValueError: continue
                    if new_norm<norm:
                        z,response,norm=candidate,made,new_norm;break
                else: raise DynamicStepError('dynamic line search failed; no automatic retry')
        except (ValueError,np.linalg.LinAlgError,DynamicStepError) as error:
            raise DynamicStepError(f'dynamic step failed without commit: {error}') from error
        raise AssertionError('unreachable')

    def _owned(self,trial):
        if type(trial) is not DynamicTrial or trial is not self._pending or digest(trial.origin)!=digest(self._checkpoint[0]):
            raise DynamicTransactionError('owned current-origin dynamic trial required')

    def _reconstruct(self,trial):
        if (type(trial) is not DynamicTrial or type(trial.iterations) is not int or not 0<=trial.iterations<=16 or
                type(trial.evaluations) is not int or not trial.iterations+1<=trial.evaluations<=128 or
                type(trial.residual_norm) is not float or not np.isfinite(trial.residual_norm) or trial.residual_norm<0):
            raise DynamicTransactionError('bounded dynamic trial metadata required')
        made=self._evaluate(trial.origin,trial.increment,trial.step,trial.forces)
        norm=self._norm(made.residual,trial.forces)
        if digest(made)!=digest(trial.response) or norm!=trial.residual_norm or norm>1e-11:
            raise DynamicTransactionError('dynamic replay/balance mismatch')
        return made

    def commit(self,trial):
        self._owned(trial)
        if digest(trial)!=self._pending_digest: raise DynamicTransactionError('altered dynamic trial')
        self._reconstruct(trial)
        self._checkpoint=(deepcopy(trial.response.state),deepcopy(trial))
        self._pending=self._pending_digest=None

    def discard(self,trial):
        self._owned(trial);self._pending=self._pending_digest=None

    def replay(self):
        state,trial=self._checkpoint;self._check_state(state)
        if trial is None: raise DynamicTransactionError('no committed dynamic trial to replay')
        if digest(trial.response.state)!=digest(state): raise DynamicTransactionError('committed dynamic state mismatch')
        return self._reconstruct(trial)
