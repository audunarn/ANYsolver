"""Bounded beam-only shared-node midpoint assembly; research, not solver API."""

from copy import deepcopy
from dataclasses import dataclass, replace
import hashlib
import json
import time

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _array, _frames, _readonly
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
from docs.reference_cases.ge_beam3_curved_p5_implicit_dynamics_probe import (
    DynamicStepError, DynamicTransactionError, left_jacobian,
)
from docs.reference_cases.ge_beam3_curved_p5_midpoint_dynamics_probe import MidpointDynamicProbe


SCHEMA = 'GE_BEAM3_P5_SHARED_MIDPOINT_DYNAMIC_ASSEMBLY_V1'


@dataclass(frozen=True)
class ChainState:
    schema: str
    model_sha256: str
    epoch: int
    time: float
    positions: np.ndarray
    rotations: np.ndarray
    cell_rotations: np.ndarray
    nodal_velocity: np.ndarray
    cell_angular_velocity: np.ndarray


@dataclass(frozen=True)
class ChainStage:
    endpoint_guess: ChainState
    residual: np.ndarray
    tangent: np.ndarray
    elastic_force: np.ndarray
    inertia: np.ndarray
    element_forces: tuple
    element_inertia: tuple


@dataclass(frozen=True)
class ChainResponse:
    state: ChainState
    stage: ChainStage
    elastic_energy: float
    kinetic_energy: float
    endpoint_force: np.ndarray
    endpoint_element_forces: tuple
    trace_iterations: int
    trace_evaluations: int
    trace_residual_norm: float


@dataclass(frozen=True)
class ChainTrial:
    origin: ChainState
    increment: np.ndarray
    step: float
    forces: np.ndarray
    response: ChainResponse
    residual_norm: float
    iterations: int
    evaluations: int


def _watchdog():
    start=time.monotonic()
    def check():
        if time.monotonic()-start>600: raise DynamicStepError('dynamic assembly wall limit')
    return check


class DynamicAssemblyProbe:
    def __init__(self,references,connectivity,sections,inertias,*,fixed_nodes=(0,),order=8):
        refs,maps,sections,inertias=map(tuple,(references,connectivity,sections,inertias))
        if not 1<=len(refs)<=4 or any(len(x)!=len(refs) for x in (maps,sections,inertias)):
            raise ValueError('one to four macros with matching maps/sections/inertias required')
        rows=[]
        for row in maps:
            row=tuple(row)
            if len(row)!=3 or any(type(i) is not int or not 0<=i<12 for i in row) or len(set(row))!=3:
                raise ValueError('three distinct bounded integer node IDs required')
            rows.append(row)
        if len({frozenset(row) for row in rows})!=len(rows): raise ValueError('duplicate macro node set')
        used=set(i for row in rows for i in row);reached={0}
        if used!=set(range(len(used))): raise ValueError('contiguous node IDs required')
        for _ in rows:
            for row in rows:
                if reached.intersection(row): reached.update(row)
        if reached!=used: raise ValueError('connected beam graph required')
        if (type(fixed_nodes) is not tuple or len(set(fixed_nodes))!=len(fixed_nodes)
                or any(type(i) is not int or i not in used for i in fixed_nodes)):
            raise ValueError('distinct valid whole-node clamps required')
        self._nodes=len(used);self._count=len(refs);self._fixed=tuple(sorted(fixed_nodes))
        self._maps=tuple(np.array(row,dtype=int) for row in rows)
        for row in self._maps: row.setflags(write=False)
        self._elements=tuple(MidpointDynamicProbe(r,s,m,order=order,fixed_nodes=())
                             for r,s,m in zip(refs,sections,inertias))
        coordinates=np.empty((self._nodes,3));seen=set()
        for row,element in zip(self._maps,self._elements):
            for node,value in zip(row,element._reference.coordinates):
                if node in seen and not np.array_equal(coordinates[node],value):
                    raise ValueError('identical shared reference positions required')
                coordinates[node]=value;seen.add(node)
        self._coordinates=_readonly(coordinates)
        self._length=max(np.linalg.norm(a-b) for a in coordinates for b in coordinates)
        self._nodal=6*self._nodes;self._size=self._nodal+6*self._count
        self._slots=tuple(np.r_[[6*i+j for i in row for j in range(6)],
                               np.arange(self._nodal+6*e,self._nodal+6*e+6)]
                          for e,row in enumerate(self._maps))
        for row in self._slots: row.setflags(write=False)
        self._free=np.array([i for i in range(self._size) if i>=self._nodal or i//6 not in self._fixed])
        self._traces=np.array([6*i+j for i in range(self._nodes) if i not in self._fixed for j in (3,4,5)],dtype=int)
        self._moment_starts=tuple(6*i+3 for i in range(self._nodes))+tuple(range(self._nodal,self._size,3))
        state=ChainState(SCHEMA,self._identity(),0,0.,self._coordinates,
            _readonly(np.tile(np.eye(3),(self._nodes,1,1))),_readonly(np.tile(np.eye(3),(self._count,2,1,1))),
            _readonly(np.zeros((self._nodes,3))),_readonly(np.zeros((self._count,2,3))))
        self._checkpoint=(state,None);self._pending=self._pending_digest=None

    def _identity(self):
        record={'schema':SCHEMA,'maps':[r.tolist() for r in self._maps],
                'coordinates':self._coordinates.tolist(),'fixed':self._fixed,
                'length':float(self._length),'size':self._size,
                'slots':[r.tolist() for r in self._slots],'free':self._free.tolist(),
                'traces':self._traces.tolist(),'moment_starts':self._moment_starts,
                'elements':[e._identity() for e in self._elements]}
        return hashlib.sha256(json.dumps(record,sort_keys=True,separators=(',',':'),allow_nan=False).encode('ascii')).hexdigest()

    @property
    def committed(self): return deepcopy(self._checkpoint[0])

    def _check_state(self,state):
        if (type(state) is not ChainState or state.schema!=SCHEMA or state.model_sha256!=self._identity()
                or type(state.epoch) is not int or state.epoch<0 or type(state.time) is not float
                or not np.isfinite(state.time) or state.time<0):
            raise DynamicTransactionError('dynamic graph state/model identity mismatch')
        _array(state.positions,(self._nodes,3),'graph positions')
        _frames(state.rotations,self._nodes,'shared deformation rotations')
        cells=_array(state.cell_rotations,(self._count,2,3,3),'retained cell rotations')
        _frames(cells.reshape(-1,3,3),2*self._count,'retained cell rotations')
        _array(state.nodal_velocity,(self._nodes,3),'graph velocities')
        _array(state.cell_angular_velocity,(self._count,2,3),'retained angular velocities')
        for i in self._fixed:
            if (not np.array_equal(state.positions[i],self._coordinates[i])
                    or not np.array_equal(state.rotations[i],np.eye(3)) or np.any(state.nodal_velocity[i]!=0.)):
                raise DynamicTransactionError('clamped graph state changed')

    def _norm(self,residual,forces):
        scaled=residual.copy()
        for i in self._moment_starts: scaled[i:i+3]/=self._length
        return float(np.linalg.norm(scaled[self._free])/max(1.,np.linalg.norm(forces)))

    def _stage(self,origin,increment,step,forces,guard=lambda:None):
        self._check_state(origin)
        z=_array(increment,(self._size,),'graph increment');forces=_array(forces,(self._nodes,3),'global dead forces')
        if type(step) is not float or not np.isfinite(step) or not 0<step<=.1: raise ValueError('bounded step required')
        for i in self._fixed:
            if np.any(z[6*i:6*i+6]!=0.): raise ValueError('clamped increment changed')
        force=np.zeros(self._size);inertia=np.zeros(self._size);tangent=np.zeros((self._size,self._size))
        element_forces=[];element_inertia=[]
        for e,(element,row,slots) in enumerate(zip(self._elements,self._maps,self._slots)):
            guard()
            local=replace(element.committed,epoch=origin.epoch,time=origin.time,
                positions=origin.positions[row],vertex_frames=origin.rotations[row]@element._reference.nodal_triads,
                cell_rotations=origin.cell_rotations[e],nodal_velocity=origin.nodal_velocity[row],
                cell_angular_velocity=origin.cell_angular_velocity[e])
            made=element._stage(local,z[slots],step,np.zeros((3,3)))
            force[slots]+=made.elastic_force;inertia[slots]+=made.inertia
            tangent[np.ix_(slots,slots)]+=made.tangent
            element_forces.append(made.elastic_force);element_inertia.append(made.inertia)
        residual=force+inertia
        for i in range(self._nodes): residual[6*i:6*i+3]-=forces[i]
        nodal=z[:self._nodal].reshape(self._nodes,6);spins=z[self._nodal:].reshape(self._count,2,3)
        rotations=np.array([rotation(a[3:])@u for a,u in zip(nodal,origin.rotations)])
        cells=np.array([[rotation(a)@u for a,u in zip(aa,uu)] for aa,uu in zip(spins,origin.cell_rotations)])
        state=ChainState(SCHEMA,origin.model_sha256,origin.epoch+1,float(origin.time+step),
            _readonly(origin.positions+nodal[:,:3]),_readonly(rotations),_readonly(cells),
            _readonly(2*nodal[:,:3]/step-origin.nodal_velocity),
            _readonly(2*spins/step-origin.cell_angular_velocity))
        self._check_state(state)
        if state.time<=origin.time: raise ValueError('step cannot advance represented time')
        if not np.isfinite(residual).all() or not np.isfinite(tangent).all(): raise ValueError('nonfinite assembled stage')
        return ChainStage(state,_readonly(residual),_readonly(tangent),_readonly(force),_readonly(inertia),
                          tuple(element_forces),tuple(element_inertia))

    def _endpoint(self,state,rotations,guard):
        force=np.zeros(self._size);tangent=np.zeros((self._size,self._size));energy=0.;parts=[]
        for e,(element,row,slots) in enumerate(zip(self._elements,self._maps,self._slots)):
            guard()
            frames=rotations[row]@element._reference.nodal_triads
            elastic=element._elastic._jet(state.positions[row],frames,state.cell_rotations[e],external=True)
            force[slots]+=elastic.gradient;tangent[np.ix_(slots,slots)]+=element._spatial_stiffness(elastic)
            energy+=float(elastic.value);parts.append(_readonly(elastic.gradient))
        return energy,force,tangent,tuple(parts)

    def _recover(self,state,guard):
        frames=state.rotations.copy();count=0
        def evaluate(q):
            nonlocal count
            if count>=64: raise DynamicStepError('global endpoint evaluation bound')
            count+=1;made=self._endpoint(state,q,guard)
            norm=float(np.linalg.norm(made[1][self._traces])/self._length)
            if not np.isfinite(norm): raise ValueError('nonfinite global endpoint balance')
            return made,norm
        made,norm=evaluate(frames)
        for iteration in range(9):
            if norm<=1e-11: return replace(state,rotations=_readonly(frames)),made,iteration,count,norm
            if iteration==8: raise DynamicStepError('global endpoint update bound')
            delta=np.zeros(self._size)
            delta[self._traces]=np.linalg.solve(made[2][np.ix_(self._traces,self._traces)],-made[1][self._traces])
            for backtrack in range(10):
                q=frames.copy()
                try:
                    for i in range(self._nodes):
                        if i in self._fixed: continue
                        spin=(.5**backtrack)*delta[6*i+3:6*i+6];left_jacobian(spin)
                        q[i]=rotation(spin)@frames[i]
                    candidate,new_norm=evaluate(q)
                except ValueError: continue
                if new_norm<norm:
                    frames,made,norm=q,candidate,new_norm;break
            else: raise DynamicStepError('global endpoint line search failed')
        raise AssertionError('unreachable')

    def _evaluate(self,origin,z,step,forces,guard=lambda:None):
        stage=self._stage(origin,z,step,forces,guard)
        state,made,iterations,evaluations,norm=self._recover(stage.endpoint_guess,guard)
        self._check_state(state);kinetic_energy=0.
        for e,(element,row) in enumerate(zip(self._elements,self._maps)):
            guard();velocity=np.zeros(24)
            velocity[:18].reshape(3,6)[:,:3]=state.nodal_velocity[row]
            velocity[18:]=state.cell_angular_velocity[e].ravel()
            kinetic_energy+=element._kinetic.evaluate(state.positions[row],state.cell_rotations[e],velocity,np.zeros(24)).kinetic_energy
        guard()
        return ChainResponse(state,stage,made[0],float(kinetic_energy),_readonly(made[1]),made[3],iterations,evaluations,norm)

    def trial(self,step,forces,*,max_iterations=16,max_evaluations=128):
        if self._pending is not None: raise DynamicTransactionError('commit/discard current graph trial first')
        if (type(max_iterations) is not int or not 0<=max_iterations<=16 or type(max_evaluations) is not int
                or not 1<=max_evaluations<=128): raise ValueError('bounded graph solver counts required')
        forces=_array(forces,(self._nodes,3),'global dead forces');origin=self.committed;count=0;guard=_watchdog()
        z=np.zeros(self._size)
        def evaluate(value):
            nonlocal count
            guard()
            if count>=max_evaluations: raise DynamicStepError('global stage evaluation bound')
            count+=1;response=self._evaluate(origin,value,step,forces,guard)
            return response,self._norm(response.stage.residual,forces)
        try:
            response,norm=evaluate(z)
            for iteration in range(max_iterations+1):
                if norm<=1e-11:
                    trial=ChainTrial(origin,_readonly(z),step,_readonly(forces),response,norm,iteration,count)
                    self._pending,self._pending_digest=trial,digest(trial);return trial
                if iteration==max_iterations: raise DynamicStepError('global stage update bound')
                delta=np.zeros(self._size)
                delta[self._free]=np.linalg.solve(response.stage.tangent[np.ix_(self._free,self._free)],-response.stage.residual[self._free])
                if not np.isfinite(delta).all(): raise DynamicStepError('nonfinite graph correction')
                for backtrack in range(10):
                    value=z+(.5**backtrack)*delta
                    try: candidate,new_norm=evaluate(value)
                    except ValueError: continue
                    if new_norm<norm:
                        z,response,norm=value,candidate,new_norm;break
                else: raise DynamicStepError('global stage line search failed')
        except (ValueError,np.linalg.LinAlgError,DynamicStepError) as error:
            raise DynamicStepError(f'dynamic graph failed without commit: {error}') from error
        raise AssertionError('unreachable')

    def _owned(self,trial):
        if type(trial) is not ChainTrial or trial is not self._pending or digest(trial.origin)!=digest(self._checkpoint[0]):
            raise DynamicTransactionError('owned current-origin graph trial required')

    def _reconstruct(self,trial):
        if (type(trial) is not ChainTrial or type(trial.iterations) is not int or not 0<=trial.iterations<=16
                or type(trial.evaluations) is not int or not trial.iterations+1<=trial.evaluations<=128
                or type(trial.residual_norm) is not float or not np.isfinite(trial.residual_norm) or trial.residual_norm<0):
            raise DynamicTransactionError('bounded graph receipt metadata required')
        made=self._evaluate(trial.origin,trial.increment,trial.step,trial.forces,_watchdog())
        norm=self._norm(made.stage.residual,trial.forces)
        if digest(made)!=digest(trial.response) or norm!=trial.residual_norm or norm>1e-11:
            raise DynamicTransactionError('global dynamic replay/balance mismatch')
        return made

    def commit(self,trial):
        self._owned(trial)
        if digest(trial)!=self._pending_digest: raise DynamicTransactionError('altered graph trial')
        self._reconstruct(trial)
        self._checkpoint=(deepcopy(trial.response.state),deepcopy(trial))
        self._pending=self._pending_digest=None

    def discard(self,trial):
        self._owned(trial);self._pending=self._pending_digest=None

    def replay(self):
        state,trial=self._checkpoint;self._check_state(state)
        if trial is None or digest(trial.response.state)!=digest(state):
            raise DynamicTransactionError('no consistent accepted graph receipt')
        return self._reconstruct(trial)
