"""Explicit elastic dynamic initialization; no production or preload history."""

from copy import deepcopy
from dataclasses import dataclass, replace
import hashlib

import numpy as np

from docs.reference_cases import ge_beam3_curved_p5_dynamic_assembly_probe as dynamic
from docs.reference_cases import ge_beam3_curved_p5_dynamic_restart_probe as restart
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _array, _frames, _readonly
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest


REQUEST_SCHEMA='GE_BEAM3_P5_INITIAL_CONDITIONS_REQUEST_V1'
RECEIPT_SCHEMA='GE_BEAM3_P5_CONSISTENT_INITIALIZATION_V1'
MODEL_SCHEMA='GE_BEAM3_P5_INITIALIZED_DYNAMIC_MODEL_V1'


class InitializationError(ValueError):
    """Initialization rejected without exposing a partially initialized model."""


@dataclass(frozen=True)
class InitialConditions:
    schema: str
    model_sha256: str
    positions: np.ndarray
    trace_seed: np.ndarray
    cell_rotations: np.ndarray
    nodal_velocity: np.ndarray
    cell_angular_velocity: np.ndarray
    forces: np.ndarray


@dataclass(frozen=True)
class InitializationReceipt:
    schema: str
    request: InitialConditions
    state: dynamic.ChainState
    rate: np.ndarray
    acceleration: np.ndarray
    endpoint_force: np.ndarray
    balance: np.ndarray
    elastic_energy: float
    kinetic_energy: float
    linear_momentum: np.ndarray
    angular_momentum: np.ndarray
    trace_iterations: int
    trace_evaluations: int
    trace_residual_norm: float
    rate_residual_norm: float
    physical_residual_norm: float


def request(expected,*,positions=None,trace_seed=None,cell_rotations=None,
            nodal_velocity=None,cell_angular_velocity=None,forces=None):
    if type(expected) is not dynamic.DynamicAssemblyProbe: raise InitializationError('exact physical model required')
    expected._check_state(expected.committed)
    n,m=expected._nodes,expected._count
    x=expected._coordinates if positions is None else positions
    q=np.tile(np.eye(3),(n,1,1)) if trace_seed is None else trace_seed
    u=np.tile(np.eye(3),(m,2,1,1)) if cell_rotations is None else cell_rotations
    v=np.zeros((n,3)) if nodal_velocity is None else nodal_velocity
    w=np.zeros((m,2,3)) if cell_angular_velocity is None else cell_angular_velocity
    f=np.zeros((n,3)) if forces is None else forces
    values=(_array(x,(n,3),'requested positions'),_frames(q,n,'requested trace seed'),
            _array(u,(m,2,3,3),'requested cell rotations'),_array(v,(n,3),'requested velocity'),
            _array(w,(m,2,3),'requested angular velocity'),_array(f,(n,3),'initial dead forces'))
    _frames(values[2].reshape(-1,3,3),2*m,'requested cell rotations')
    return InitialConditions(REQUEST_SCHEMA,expected._identity(),*(_readonly(a) for a in values))


class _InitializedCore(dynamic.DynamicAssemblyProbe):
    def __init__(self,base,request_sha256):
        self._request_sha256=request_sha256
        elements=base._elements
        super().__init__([e._reference for e in elements],[r.tolist() for r in base._maps],
                         [e._elastic.section for e in elements],[e._kinetic.section_mass for e in elements],
                         fixed_nodes=base._fixed,order=elements[0]._order)

    def _identity(self):
        text=MODEL_SCHEMA+':'+super()._identity()+':'+self._request_sha256
        return hashlib.sha256(text.encode('ascii')).hexdigest()


class InitializedDynamicProbe:
    """Research trajectory with immutable initialization context; not restart API."""

    def __init__(self,core,receipt):
        self._core=core;self._receipt=deepcopy(receipt);self._receipt_sha256=digest(receipt)

    @property
    def committed(self): return self._core.committed

    @property
    def initialization(self): return deepcopy(self._receipt)

    def _guard(self):
        core=self._core;core._check_state(core.committed)
        if (digest(self._receipt)!=self._receipt_sha256
                or digest(self._receipt.request)!=core._request_sha256
                or self._receipt.state.model_sha256!=core._identity()):
            raise dynamic.DynamicTransactionError('initialized-model authority changed')
        state,trial=core._checkpoint
        if state.epoch==0:
            if trial is not None or digest(state)!=digest(self._receipt.state):
                raise dynamic.DynamicTransactionError('initialized origin changed')
        elif trial is None or digest(trial.response.state)!=digest(state):
            raise dynamic.DynamicTransactionError('initialized accepted receipt mismatch')
        elif trial.origin.epoch==0 and digest(trial.origin)!=digest(self._receipt.state):
            raise dynamic.DynamicTransactionError('first step lost its initialization origin')

    def trial(self,*args,**kwargs):
        self._guard();return self._core.trial(*args,**kwargs)

    def commit(self,trial):
        self._guard();self._core.commit(trial)

    def discard(self,trial):
        self._guard();self._core.discard(trial)

    def replay(self):
        self._guard();return self._core.replay()


def initialize(expected,conditions):
    """Construct a new trajectory from explicit conditions; do not mutate expected."""
    try:
        if type(expected) is not dynamic.DynamicAssemblyProbe or type(conditions) is not InitialConditions:
            raise InitializationError('exact physical model and initial-condition request required')
        base=restart._fresh(expected)
        if digest(expected.committed)!=digest(base.committed) or expected._checkpoint[1] is not None:
            raise InitializationError('initialization cannot reset an accepted or privately altered model')
        if conditions.schema!=REQUEST_SCHEMA or conditions.model_sha256!=base._identity():
            raise InitializationError('initial-condition schema/model mismatch')
        checked=request(base,positions=conditions.positions,trace_seed=conditions.trace_seed,
                        cell_rotations=conditions.cell_rotations,nodal_velocity=conditions.nodal_velocity,
                        cell_angular_velocity=conditions.cell_angular_velocity,forces=conditions.forces)
        if digest(checked)!=digest(conditions): raise InitializationError('noncanonical initial-condition arrays')
        core=_InitializedCore(base,digest(checked));guard=dynamic._watchdog()
        state=replace(core.committed,positions=checked.positions,rotations=checked.trace_seed,
                      cell_rotations=checked.cell_rotations,nodal_velocity=checked.nodal_velocity,
                      cell_angular_velocity=checked.cell_angular_velocity)
        core._check_state(state)
        state,endpoint,iterations,evaluations,trace_norm=core._recover(state,guard)
        core._check_state(state);elastic_energy,force,tangent,_=endpoint
        physical=np.array([i for i in core._free if i>=core._nodal or i%6<3],dtype=int)
        rate=np.zeros(core._size)
        rate[:core._nodal].reshape(core._nodes,6)[:,:3]=state.nodal_velocity
        rate[core._nodal:]=state.cell_angular_velocity.ravel()
        if len(core._traces):
            block=tangent[np.ix_(core._traces,core._traces)]
            if np.linalg.norm(block-block.T)>1e-11*max(1.,np.linalg.norm(block)):
                raise InitializationError('initial free trace tangent is not symmetric')
            np.linalg.cholesky((block+block.T)/2)
            rate[core._traces]=np.linalg.solve(block,-(tangent@rate)[core._traces])
        rate_norm=float(np.linalg.norm((tangent@rate)[core._traces])/core._length/max(1.,np.linalg.norm(rate)))
        if not np.isfinite(rate_norm) or rate_norm>1e-11: raise InitializationError('initial trace rate inconsistency')
        mass=np.zeros((core._size,core._size));convective=np.zeros(core._size)
        kinetic_energy=0.;linear=np.zeros(3);angular=np.zeros(3)
        for e,(element,row,slots) in enumerate(zip(core._elements,core._maps,core._slots)):
            guard()
            made=element._kinetic.evaluate(state.positions[row],state.cell_rotations[e],rate[slots],np.zeros(24))
            mass[np.ix_(slots,slots)]+=made.mass;convective[slots]+=made.inertia
            kinetic_energy+=made.kinetic_energy;linear+=made.linear_momentum;angular+=made.angular_momentum
        all_traces=np.array([6*i+j for i in range(core._nodes) for j in (3,4,5)])
        if np.any(mass[:,all_traces]!=0.): raise InitializationError('trace inertia is forbidden')
        external=np.zeros(core._size)
        external[:core._nodal].reshape(core._nodes,6)[:,:3]=checked.forces
        block=mass[np.ix_(physical,physical)];np.linalg.cholesky(block)
        acceleration=np.zeros(core._size)
        acceleration[physical]=np.linalg.solve(block,(external-force-convective)[physical])
        balance=mass@acceleration+convective+force-external
        scaled=balance.copy()
        for i in core._moment_starts: scaled[i:i+3]/=core._length
        physical_norm=float(np.linalg.norm(scaled[physical])/max(1.,np.linalg.norm(external)))
        if not np.isfinite(physical_norm) or physical_norm>1e-11: raise InitializationError('initial acceleration imbalance')
        receipt=InitializationReceipt(RECEIPT_SCHEMA,checked,state,_readonly(rate),_readonly(acceleration),
            _readonly(force),_readonly(balance),float(elastic_energy),float(kinetic_energy),_readonly(linear),
            _readonly(angular),iterations,evaluations,trace_norm,rate_norm,physical_norm)
        guard();core._checkpoint=(deepcopy(state),None)
        return InitializedDynamicProbe(core,receipt)
    except InitializationError: raise
    except (ValueError,TypeError,AttributeError,KeyError,dynamic.DynamicStepError,
            dynamic.DynamicTransactionError,np.linalg.LinAlgError) as error:
        raise InitializationError('inconsistent or inadmissible dynamic initialization') from error
