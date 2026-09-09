"""Explicit two-part coordinate transactions for the P5 research assembly.

No old state is upgraded implicitly. High and low coordinates are numerical
state bound into the complete trial/response digest, not additional DOFs.
"""

from copy import deepcopy
from dataclasses import dataclass, fields, replace
import math

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_assembly_history_probe import (
    AssemblyState, AssemblyTrial, AssemblyPathError, AssemblyTransactionError, _Budget,
)
from docs.reference_cases.ge_beam3_curved_p5_force_accurate_assembly import (
    ForceAccurateAssemblyHistoryProbe, ForceAccurateElementResponse,
)
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import (
    NonlinearCondensedResponse, NonlinearLocalError, _accuracy_metrics,
)
from docs.reference_cases.ge_beam3_curved_p5_compensated_coordinates import SCHEMA as COORDINATES, advance, validate_pair
from docs.reference_cases.ge_beam3_curved_p5_compensated_mixed import CompensatedMixedBeamProbe
from docs.reference_cases.ge_beam3_curved_p5_continuation_probe import spatial_derivative
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _array, _frames, _readonly
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest


SCHEMA = 'GE_BEAM3_P5_COMPENSATED_ASSEMBLY_FORCE_ACCURACY_V1'


@dataclass(frozen=True)
class CompensatedState(AssemblyState):
    position_low: np.ndarray
    coordinate_schema: str


@dataclass(frozen=True)
class CompensatedTrial(AssemblyTrial):
    position_low: np.ndarray
    coordinate_schema: str


@dataclass(frozen=True)
class CompensatedElementResponse(ForceAccurateElementResponse):
    position_low: np.ndarray


def checked_pairs(high, low, nodes):
    high = _array(high, (nodes, 3), 'coordinate high parts')
    low = _array(low, (nodes, 3), 'coordinate low parts')
    for a,b in zip(high.flat,low.flat): validate_pair(float(a),float(b))
    return high,low


def move_pairs(high, low, delta):
    high,low = checked_pairs(high,low,len(high))
    delta = _array(delta, high.shape, 'translation increment')
    made_high,made_low = np.empty_like(high),np.empty_like(low)
    for index in np.ndindex(high.shape):
        made_high[index],made_low[index] = advance(float(high[index]),float(low[index]),float(delta[index]))
    return made_high,made_low


class CompensatedAssemblyHistoryProbe(ForceAccurateAssemblyHistoryProbe):
    _accuracy_schema = SCHEMA

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        initial = self._checkpoint[0]
        values = {f.name:getattr(initial,f.name) for f in fields(AssemblyState)}
        self._checkpoint = (CompensatedState(**values,position_low=_readonly(np.zeros_like(initial.positions)),
                                             coordinate_schema=COORDINATES),None)

    def _check_state(self):
        state = self._checkpoint[0]
        if type(state) is not CompensatedState or state.coordinate_schema != COORDINATES:
            raise AssemblyTransactionError('explicit compensated checkpoint required')
        try:
            checked_pairs(state.positions,state.position_low,self._nodes)
        except ValueError as error:
            raise AssemblyTransactionError('invalid compensated checkpoint coordinates') from error
        if np.any(state.position_low[self._fixed]) or not np.array_equal(state.positions[self._fixed],self._coordinates[self._fixed]):
            raise AssemblyTransactionError('compensated clamp mismatch')
        return state

    @property
    def committed(self): return deepcopy(self._check_state())

    def _check_element_accuracy(self,response):
        expected = self.local_accuracy
        if (type(response) is not CompensatedElementResponse or response.accuracy_schema != SCHEMA or
                response.force_accuracy != expected or type(response.estimated_force_error) is not float or
                not math.isfinite(response.estimated_force_error) or not 0 <= response.estimated_force_error <= expected.limit):
            raise AssemblyTransactionError('compensated element policy/schema mismatch')
        _array(response.position_low,(3,3),'element coordinate low parts')

    def _solve_all(self,positions,rotations,origins,budget,*,position_low):
        positions,position_low = checked_pairs(positions,position_low,self._nodes)
        rotations = _frames(rotations,self._nodes,'shared rotations')
        if len(origins) != len(self._maps): raise ValueError('complete origin inventory required')
        class CountedMixed(CompensatedMixedBeamProbe):
            def evaluate(inner,*args,**kwargs):
                budget.consume();result=super().evaluate(*args,**kwargs)
                inner.last_evaluation=result;return result
        responses=[];accuracy=self.local_accuracy
        for ref,row,section,history in zip(self._references,self._maps,self._sections,origins):
            model=CountedMixed(ref,section,order=self._order,origins=history,position_low=position_low[row])
            solved=model.solve(positions[row],rotations[row]@ref.nodal_triads,force_accuracy=accuracy)
            error=_accuracy_metrics(model.last_evaluation,accuracy)[1]
            values={f.name:getattr(solved,f.name) for f in fields(NonlinearCondensedResponse)}
            responses.append(CompensatedElementResponse(**values,accuracy_schema=SCHEMA,force_accuracy=accuracy,
                estimated_force_error=error,position_low=_readonly(position_low[row])))
        return self._scatter(responses)

    def response_at(self,positions,rotations,*,position_low):
        state=self._check_state()
        return self._solve_all(positions,rotations,state.histories,_Budget(64*len(self._maps)),position_low=position_low)

    def _reconstruct_element(self,index,trial):
        if getattr(trial,'coordinate_schema',None) != COORDINATES:
            raise AssemblyTransactionError('explicit trial coordinate schema required')
        high,low=checked_pairs(trial.positions,trial.position_low,self._nodes)
        old=trial.response.elements[index];self._check_element_accuracy(old)
        ref,row,section=self._references[index],self._maps[index],self._sections[index]
        if not np.array_equal(old.position_low,low[row]):
            raise AssemblyTransactionError('element/trial low parts disagree')
        model=CompensatedMixedBeamProbe(ref,section,order=self._order,origins=trial.origins[index],position_low=low[row])
        made=model.evaluate(high[row],trial.rotations[row]@ref.nodal_triads,old.local_rotations,old.moments)
        h=made.hessian
        np.linalg.cholesky(-h[24:,24:])
        np.linalg.cholesky(h[18:24,18:24]-h[18:24,24:]@np.linalg.solve(h[24:,24:],h[24:,18:24]))
        tangent=h[:18,:18]-h[:18,18:]@np.linalg.solve(h[18:,18:],h[18:,:18])
        result=replace(old,potential=made.potential,residual=_readonly(made.residual[:18]),tangent=_readonly(tangent),
            stations=made.stations,local_residual_norm=float(np.linalg.norm(made.residual[18:],np.inf)),
            estimated_force_error=_accuracy_metrics(made,self.local_accuracy)[1],position_low=_readonly(low[row]))
        self._check_element_accuracy(result)
        return result

    def _validated(self,trial):
        if type(trial) is not CompensatedTrial or trial.coordinate_schema != COORDINATES:
            raise AssemblyTransactionError('owned compensated trial required')
        checked_pairs(trial.positions,trial.position_low,self._nodes)
        if np.any(trial.position_low[self._fixed]): raise AssemblyTransactionError('nonzero clamp low part')
        return super()._validated(trial)

    def commit(self,trial):
        self._owned(trial);state=self._check_state()
        try:
            if digest(trial)!=self._pending_digest or trial.origins!=state.histories:
                raise AssemblyTransactionError('altered trial or material origin')
            response,histories=self._validated(trial)
            committed=CompensatedState(trial.origin_epoch+1,_readonly(trial.positions),_readonly(trial.rotations),
                _readonly(trial.forces),histories,_readonly(trial.position_low),COORDINATES)
            accepted=deepcopy(replace(trial,response=response));exported=deepcopy(committed)
        except (ValueError,TypeError,np.linalg.LinAlgError) as error:
            raise AssemblyTransactionError('compensated all-element commit validation failed') from error
        self._checkpoint=(committed,accepted);self._pending=self._pending_digest=None
        return exported

    def replay(self):
        state=self._check_state();accepted=self._checkpoint[1]
        if (type(accepted) is not CompensatedTrial or state.epoch!=accepted.origin_epoch+1 or
                state.coordinate_schema!=accepted.coordinate_schema or
                not all(np.array_equal(getattr(state,k),getattr(accepted,k)) for k in
                        ('positions','position_low','rotations','forces'))):
            raise AssemblyTransactionError('compensated checkpoint/accepted trial mismatch')
        return super().replay()

    def trial(self,forces,*,max_iterations=16,max_mixed_evaluations=None):
        if self._pending is not None: raise AssemblyPathError('explicit commit/discard required')
        state=self._check_state();cap=256*len(self._maps)
        if max_mixed_evaluations is None: max_mixed_evaluations=cap
        if (type(max_iterations) is not int or not 0<=max_iterations<=16 or
                type(max_mixed_evaluations) is not int or not 0<=max_mixed_evaluations<=cap):
            raise ValueError('bounded global iteration/evaluation budget required')
        forces=_array(forces,(self._nodes,3),'spatial dead forces')
        x,low,u=state.positions.copy(),state.position_low.copy(),state.rotations.copy()
        budget=_Budget(max_mixed_evaluations);external=self._external(forces)
        try:
            response=self._solve_all(x,u,state.histories,budget,position_low=low)
            for iteration in range(max_iterations+1):
                residual=response.residual-external;norm=self._norm(residual,forces)
                if norm<=1e-11:
                    result=CompensatedTrial(state.epoch,_readonly(x),_readonly(u),_readonly(forces),deepcopy(state.histories),
                        response,norm,iteration,budget.count,_readonly(low),COORDINATES)
                    self._pending,self._pending_digest=result,digest(result)
                    return result
                if iteration==max_iterations: raise AssemblyPathError('compensated global iteration bound reached')
                h=spatial_derivative(response);step=np.zeros(6*self._nodes)
                step[self._free]=np.linalg.solve(h[np.ix_(self._free,self._free)],-residual[self._free])
                if not np.isfinite(step).all(): raise AssemblyPathError('nonfinite global correction')
                for backtrack in range(10):
                    delta=(step*.5**backtrack).reshape(self._nodes,6)
                    if np.max(np.linalg.norm(delta[:,3:],axis=1))>=.9*np.pi: continue
                    a,b=move_pairs(x,low,delta[:,:3])
                    rotations=np.array([rotation(d[3:])@old for d,old in zip(delta,u)])
                    try: candidate=self._solve_all(a,rotations,state.histories,budget,position_low=b)
                    except (ValueError,NonlinearLocalError,np.linalg.LinAlgError): continue
                    if self._norm(candidate.residual-external,forces)<norm:
                        x,low,u,response=a,b,rotations,candidate;break
                else: raise AssemblyPathError('compensated line search exhausted; no automatic retry')
        except (ValueError,NonlinearLocalError,np.linalg.LinAlgError) as error:
            raise AssemblyPathError('compensated trial failed without commit') from error
        raise AssertionError('unreachable')
