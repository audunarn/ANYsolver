"""Transactional incremental-potential load control for the P5 research assembly.

Only spatial dead nodal forces and the existing variational section law. Fixed
committed origins define every trial potential. This is not follower loading,
unstable-branch continuation, a production API or independent qualification.
"""

from copy import deepcopy
from dataclasses import dataclass

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _array, _readonly
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
from docs.reference_cases.ge_beam3_curved_p5_assembly_history_probe import (
    NonlinearAssemblyHistoryProbe, AssemblyTrial, AssemblyPathError, AssemblyTransactionError, _Budget,
)
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import NonlinearLocalError
from docs.reference_cases.ge_beam3_curved_p5_continuation_probe import spatial_derivative
from docs.reference_cases.ge_beam3_curved_p5_energy_seed_probe import acceptance,energy,SeedCheckpoint


class ConservativePathError(RuntimeError):
    """No published state change; diagnostics may describe a failed trial."""

    def __init__(self,message,checkpoints=(),evaluations=0):
        super().__init__(message)
        self.checkpoints = tuple(checkpoints)
        self.evaluations = evaluations


@dataclass(frozen=True)
class ConservativeTrial:
    origin_epoch: int
    assembly: AssemblyTrial
    checkpoints: tuple


class ConservativeAssemblyPathProbe:
    """Own a private assembly; publish all-element state only after replay.

    Unlike shape initialization, these are explicit physical load increments.
    The existing section's variational plastic trial states are permitted; all
    evaluations use the same old histories until global commit. No automatic
    load cutback, retry, stabilization or unloading approximation is performed.
    """

    def __init__(self,model):
        if type(model) is not NonlinearAssemblyHistoryProbe or model._pending is not None:
            raise ValueError('exact research assembly with no pending trial required')
        staged = deepcopy(model)
        if staged.committed.epoch:
            staged.replay()
        self._checkpoint = staged
        self._pending = self._pending_digest = self._staged = None

    @property
    def committed_model(self):
        return deepcopy(self._checkpoint)

    def trial(self,forces,*,max_iterations=16,max_mixed_evaluations=None):
        if self._pending is not None:
            raise ConservativePathError('commit or discard the existing trial explicitly')
        original = self._checkpoint
        cap = 256*len(original._maps)
        if max_mixed_evaluations is None:
            max_mixed_evaluations = cap
        if (type(max_iterations) is not int or not 0<=max_iterations<=16 or
                type(max_mixed_evaluations) is not int or not 0<=max_mixed_evaluations<=cap):
            raise ValueError('bounded conservative load increment required')
        f = _array(forces,(original._nodes,3),'spatial dead forces')
        staged = deepcopy(original)
        state = staged.committed
        x,u = state.positions.copy(),state.rotations.copy()
        origins = state.histories
        external,free = staged._external(f),staged._free
        budget = _Budget(max_mixed_evaluations)
        checkpoints = []
        def evaluate(a,b):
            return staged._solve_all(a,b,origins,budget)
        try:
            response = evaluate(x,u)
            for iteration in range(max_iterations+1):
                residual = response.residual-external
                norm = staged._norm(residual,f)
                current,roundoff_scale = energy(response,x,staged._coordinates,f)
                if norm<=1e-11:
                    assembly = AssemblyTrial(state.epoch,_readonly(x),_readonly(u),_readonly(f),
                        deepcopy(origins),response,norm,iteration,budget.count)
                    staged._pending,staged._pending_digest = assembly,digest(assembly)
                    checkpoints.append(SeedCheckpoint(iteration,-1,budget.count,norm,current,0.,'COMPLETE'))
                    trial = ConservativeTrial(state.epoch,assembly,tuple(checkpoints))
                    self._pending_digest = digest(trial)
                    self._pending,self._staged = trial,staged
                    return trial
                if iteration==max_iterations:
                    raise ConservativePathError('conservative update bound reached')
                step = np.zeros(6*staged._nodes)
                derivative = spatial_derivative(response)
                step[free] = np.linalg.solve(derivative[np.ix_(free,free)],-residual[free])
                slope = float(residual @ step)
                if not np.isfinite(step).all() or not np.isfinite(slope) or slope>=0:
                    raise ConservativePathError('no finite descent direction; explicit continuation strategy required')
                for backtrack in range(10):
                    scale = .5**backtrack
                    delta = (step*scale).reshape(-1,6)
                    if np.max(np.linalg.norm(delta[:,3:],axis=1))>=.9*np.pi:
                        continue
                    a = x+delta[:,:3]
                    b = np.array([rotation(d[3:]) @ old for d,old in zip(delta,u)])
                    try:
                        candidate = evaluate(a,b)
                    except (ValueError,NonlinearLocalError):
                        continue
                    value,candidate_scale = energy(candidate,a,staged._coordinates,f)
                    candidate_norm = staged._norm(candidate.residual-external,f)
                    disposition = acceptance(current,value,slope,scale,max(roundoff_scale,candidate_scale),norm,candidate_norm)
                    # A finite candidate satisfying the actual equations must
                    # not be rejected by a noisy auxiliary energy difference.
                    # Replay/commit validation still precedes publication.
                    if candidate_norm<=1e-11:
                        disposition = 'ACCEPT_EQUILIBRIUM'
                    checkpoints.append(SeedCheckpoint(iteration,backtrack,budget.count,candidate_norm,value,slope,disposition))
                    if disposition.startswith('ACCEPT_'):
                        x,u,response = a,b,candidate
                        break
                else:
                    raise ConservativePathError('conservative line-search bound reached; explicit cutback required')
            raise AssertionError('unreachable')
        except (ConservativePathError,ValueError,NonlinearLocalError,AssemblyPathError,np.linalg.LinAlgError) as exc:
            raise ConservativePathError(f'load trial failed without commit: {type(exc).__name__}: {exc}',
                                        checkpoints,budget.count) from exc

    def _owned(self,trial):
        if trial is None or trial is not self._pending or trial.origin_epoch!=self._checkpoint.committed.epoch:
            raise ConservativePathError('owned current conservative trial required')

    def commit(self,trial):
        self._owned(trial)
        if digest(trial)!=self._pending_digest:
            raise ConservativePathError('altered conservative trial')
        staged = deepcopy(self._staged)
        try:
            staged.commit(staged._pending)
            exported = staged.committed
        except (ValueError,AssemblyTransactionError,np.linalg.LinAlgError) as exc:
            raise ConservativePathError('all-element conservative commit validation failed') from exc
        self._checkpoint = staged
        self._pending = self._pending_digest = self._staged = None
        return exported

    def discard(self,trial):
        self._owned(trial)
        self._pending = self._pending_digest = self._staged = None
