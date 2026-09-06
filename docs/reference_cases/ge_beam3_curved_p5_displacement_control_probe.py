"""Single-translation control for the unchanged P5 research assembly.

All remaining spatial DOFs are solved; no lateral mode is projected away.
The controlled nodal force is recovered as a reaction and used as the
equivalent dead load for the existing all-element replay/commit validation.
This is not a production constraint API or full post-bifurcation solver.
"""

from copy import deepcopy
from dataclasses import dataclass

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _readonly
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
from docs.reference_cases.ge_beam3_curved_p5_continuation_probe import spatial_derivative
from docs.reference_cases.ge_beam3_curved_p5_assembly_history_probe import (
    NonlinearAssemblyHistoryProbe,AssemblyTrial,AssemblyPathError,AssemblyTransactionError,_Budget,
)
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import NonlinearLocalError


class DisplacementControlError(RuntimeError):
    def __init__(self,message,checkpoints=(),evaluations=0):
        super().__init__(message);self.checkpoints=tuple(checkpoints);self.evaluations=evaluations


@dataclass(frozen=True)
class ControlCheckpoint:
    iteration: int
    mixed_evaluations: int
    residual: float
    reaction: float


@dataclass(frozen=True)
class DisplacementTrial:
    origin_epoch: int
    control_dof: int
    target: float
    reaction_derivative: float
    assembly: AssemblyTrial
    checkpoints: tuple


class DisplacementControlledAssemblyProbe:
    def __init__(self,model,*,node,component=1):
        if type(model) is not NonlinearAssemblyHistoryProbe or model._pending is not None:
            raise ValueError('exact research assembly without pending trial required')
        if (type(node) is not int or type(component) is not int or not 0<=component<3 or
                node not in model._free_nodes):
            raise ValueError('one existing free nodal translation must be controlled')
        self._control=6*node+component;self._node=node;self._component=component
        self._checkpoint=deepcopy(model)
        if model.committed.epoch: self._checkpoint.replay()
        self._pending=self._pending_digest=self._staged=None

    @property
    def committed_model(self): return deepcopy(self._checkpoint)

    def trial(self,target,*,max_iterations=16,max_mixed_evaluations=None):
        if self._pending is not None: raise DisplacementControlError('explicit commit/discard required')
        original=self._checkpoint;state=original.committed;cap=256*len(original._maps)
        if max_mixed_evaluations is None: max_mixed_evaluations=cap
        if (isinstance(target,(bool,np.bool_)) or not np.isscalar(target) or not np.isfinite(target) or
                abs(target-state.positions[self._node,self._component])>.01*original._length or
                type(max_iterations) is not int or not 0<=max_iterations<=16 or
                type(max_mixed_evaluations) is not int or not 0<=max_mixed_evaluations<=cap):
            raise ValueError('finite bounded displacement increment/iteration budget required')
        staged=deepcopy(original);origins=state.histories;budget=_Budget(max_mixed_evaluations)
        free=staged._free[staged._free!=self._control]
        x,u=state.positions.copy(),state.rotations.copy();checkpoints=[]
        def evaluate(a,b): return staged._solve_all(a,b,origins,budget)
        def residual(response):
            forces=state.forces.copy()
            forces[self._node,self._component]=response.residual[self._control]
            r=response.residual-staged._external(forces)
            return r,forces,staged._norm(r,forces)
        def move(a,b,delta):
            d=delta.reshape(staged._nodes,6)
            if np.max(np.linalg.norm(d[:,3:],axis=1))>=.9*np.pi:
                raise DisplacementControlError('rotation increment requires explicit smaller target')
            made=a+d[:,:3];made[self._node,self._component]=target
            return made,np.array([rotation(v[3:])@old for v,old in zip(d,b)])
        try:
            response=evaluate(x,u)
            change=target-x[self._node,self._component]
            if change:
                # Linear constraint predictor distributes the prescribed change
                # through equilibrium, instead of moving only the crown node.
                derivative=spatial_derivative(response);r,_,_=residual(response)
                delta=np.zeros(6*staged._nodes);delta[self._control]=change
                delta[free]=np.linalg.solve(derivative[np.ix_(free,free)],
                                            -r[free]-derivative[free,self._control]*change)
                if not np.isfinite(delta).all(): raise DisplacementControlError('nonfinite constraint predictor')
                x,u=move(x,u,delta);response=evaluate(x,u)
            for iteration in range(max_iterations+1):
                r,forces,norm=residual(response)
                checkpoints.append(ControlCheckpoint(iteration,budget.count,norm,float(forces[self._node,self._component])))
                if norm<=1e-11:
                    if x[self._node,self._component]!=target: raise DisplacementControlError('target not satisfied')
                    h=spatial_derivative(response)
                    reaction_derivative=float(h[self._control,self._control]-h[self._control,free]@
                        np.linalg.solve(h[np.ix_(free,free)],h[free,self._control]))
                    if not np.isfinite(reaction_derivative): raise DisplacementControlError('nonfinite reaction derivative')
                    assembly=AssemblyTrial(state.epoch,_readonly(x),_readonly(u),_readonly(forces),deepcopy(origins),
                                           response,norm,iteration,budget.count)
                    staged._pending,staged._pending_digest=assembly,digest(assembly)
                    trial=DisplacementTrial(state.epoch,self._control,float(target),reaction_derivative,assembly,tuple(checkpoints))
                    self._pending,self._pending_digest,self._staged=trial,digest(trial),staged
                    return trial
                if iteration==max_iterations: raise DisplacementControlError('controlled update bound reached')
                derivative=spatial_derivative(response);delta=np.zeros(6*staged._nodes)
                delta[free]=np.linalg.solve(derivative[np.ix_(free,free)],-r[free])
                if not np.isfinite(delta).all(): raise DisplacementControlError('nonfinite controlled correction')
                for backtrack in range(10):
                    try:
                        a,b=move(x,u,delta*.5**backtrack);candidate=evaluate(a,b)
                    except (ValueError,NonlinearLocalError,DisplacementControlError): continue
                    if residual(candidate)[2]<norm:
                        x,u,response=a,b,candidate;break
                else: raise DisplacementControlError('controlled line search failed; no automatic cutback')
            raise AssertionError('unreachable')
        except (DisplacementControlError,AssemblyPathError,ValueError,NonlinearLocalError,np.linalg.LinAlgError) as error:
            raise DisplacementControlError(f'controlled trial failed without commit: {error}',checkpoints,budget.count) from error

    def _owned(self,trial):
        if trial is not self._pending or trial is None or trial.origin_epoch!=self._checkpoint.committed.epoch:
            raise DisplacementControlError('owned current displacement trial required')

    def commit(self,trial):
        self._owned(trial)
        if digest(trial)!=self._pending_digest: raise DisplacementControlError('altered displacement trial')
        staged=deepcopy(self._staged)
        try: staged.commit(staged._pending)
        except (ValueError,AssemblyTransactionError,np.linalg.LinAlgError) as error:
            raise DisplacementControlError('all-element controlled replay/commit failed') from error
        self._checkpoint=staged;self._pending=self._pending_digest=self._staged=None
        return staged.committed

    def discard(self,trial):
        self._owned(trial);self._pending=self._pending_digest=self._staged=None
