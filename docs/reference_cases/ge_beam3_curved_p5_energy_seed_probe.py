"""Bounded conservative elastic seed with potential-energy backtracking.

Research successor, not production routing or qualification. The potential,
local solver, spatial derivative, final equilibrium tolerance and original
failed algorithms are unchanged. This is not a plastic loading history or
an algorithm for nonconservative loads/unstable equilibrium branches.
"""

from copy import deepcopy
from dataclasses import dataclass

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _array, _frames, _readonly
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
from docs.reference_cases.ge_beam3_curved_p5_assembly_history_probe import (
    NonlinearAssemblyHistoryProbe, AssemblyTrial, AssemblyPathError, AssemblyTransactionError, _Budget,
)
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import NonlinearLocalError
from docs.reference_cases.ge_beam3_curved_p5_continuation_probe import spatial_derivative


@dataclass(frozen=True)
class SeedCheckpoint:
    iteration: int
    backtrack: int
    evaluations: int
    residual_norm: float
    energy: float
    slope: float
    disposition: str


class EnergySeedError(RuntimeError):
    """Unresolved bounded attempt; only diagnostics, never a partial model."""

    def __init__(self,message,checkpoints=(),evaluations=0):
        super().__init__(message)
        self.checkpoints = tuple(checkpoints)
        self.evaluations = evaluations


@dataclass(frozen=True)
class EnergySeedResult:
    model: object
    checkpoints: tuple


def energy(response, positions, reference_positions, forces):
    with np.errstate(over='ignore',invalid='ignore'):
        work = float(np.sum(forces*(positions-reference_positions)))
    value,scale = response.potential-work,abs(response.potential)+abs(work)
    if not np.isfinite(value) or not np.isfinite(scale):
        raise ValueError('finite total energy and work scale required')
    return value,scale


def acceptance(old,new,slope,scale,roundoff_scale,old_norm,new_norm):
    """Armijo c=1e-4; only unresolved energy differences use residual descent.

    The roundoff guard does not relax the final physical residual criterion.
    No stiffness shifts, gradient fallback, step growth or automatic retry.
    """
    if not all(np.isfinite(v) for v in (old,new,slope,scale,roundoff_scale,old_norm,new_norm)):
        raise ValueError('finite line-search quantities required')
    if not (0<scale<=1 and roundoff_scale>=0 and old_norm>=0 and new_norm>=0):
        raise ValueError('valid line-search scales required')
    if slope>=0:
        return 'REJECT_NON_DESCENT'
    floor = 32*np.finfo(float).eps*roundoff_scale
    difference = new-old
    # Resolve near-stationary cancellation before the energy Armijo test:
    # indistinguishable energy alone must never authorize an arbitrary step.
    if abs(difference)<=floor and abs(scale*slope)<=floor:
        return 'ACCEPT_ROUNDOFF_RESIDUAL' if new_norm<old_norm else 'REJECT_ROUNDOFF'
    return 'ACCEPT_ENERGY' if difference<=1e-4*scale*slope else 'REJECT_ENERGY'


def solve(model,positions,rotations,forces,*,max_iterations=16,max_mixed_evaluations=None):
    if (type(model) is not NonlinearAssemblyHistoryProbe or model._pending is not None
            or model.committed.epoch!=0):
        raise ValueError('virgin research assembly without pending trial required')
    cap = 256*len(model._maps)
    if max_mixed_evaluations is None:
        max_mixed_evaluations = cap
    if (type(max_iterations) is not int or not 0<=max_iterations<=16 or
            type(max_mixed_evaluations) is not int or not 0<=max_mixed_evaluations<=cap):
        raise ValueError('bounded conservative seed required')
    x = _array(positions,(model._nodes,3),'seed positions')
    u = _frames(rotations,model._nodes,'seed spatial rotations')
    f = _array(forces,(model._nodes,3),'spatial dead force')
    if (not np.array_equal(x[model._fixed],model._coordinates[model._fixed]) or
            not np.array_equal(u[model._fixed],np.tile(np.eye(3),(len(model._fixed),1,1)))):
        raise ValueError('seed must preserve every clamp exactly')
    staged = deepcopy(model)
    origins = staged.committed.histories
    external,free = staged._external(f),staged._free
    budget = _Budget(max_mixed_evaluations)
    checkpoints = []
    def evaluate(a,b):
        response = staged._solve_all(a,b,origins,budget)
        if any(s.response.plastic_active for e in response.elements for s in e.stations):
            raise EnergySeedError('elastic seed cannot invent plastic load history')
        return response
    try:
        response = evaluate(x,u)
        for iteration in range(max_iterations+1):
            residual = response.residual-external
            norm = staged._norm(residual,f)
            current,roundoff_scale = energy(response,x,staged._coordinates,f)
            if norm<=1e-11:
                trial = AssemblyTrial(0,_readonly(x),_readonly(u),_readonly(f),deepcopy(origins),
                    response,norm,iteration,budget.count)
                staged._pending,staged._pending_digest = trial,digest(trial)
                staged.commit(trial)
                checkpoints.append(SeedCheckpoint(iteration,-1,budget.count,norm,current,0.,'COMPLETE'))
                return EnergySeedResult(staged,tuple(checkpoints))
            if iteration==max_iterations:
                raise EnergySeedError('energy seed update bound reached')
            derivative = spatial_derivative(response)
            step = np.zeros(6*staged._nodes)
            step[free] = np.linalg.solve(derivative[np.ix_(free,free)],-residual[free])
            slope = float(residual @ step)
            if not np.isfinite(step).all() or not np.isfinite(slope) or slope>=0:
                raise EnergySeedError('no finite descent direction; explicit branch strategy required')
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
                decision = acceptance(current,value,slope,scale,max(roundoff_scale,candidate_scale),norm,candidate_norm)
                checkpoints.append(SeedCheckpoint(iteration,backtrack,budget.count,candidate_norm,value,slope,decision))
                if decision.startswith('ACCEPT_'):
                    x,u,response = a,b,candidate
                    break
            else:
                raise EnergySeedError('energy seed line-search bound reached')
        raise AssertionError('unreachable')
    except (EnergySeedError,ValueError,NonlinearLocalError,AssemblyPathError,AssemblyTransactionError,np.linalg.LinAlgError) as exc:
        raise EnergySeedError(f'energy seed failed without caller mutation: {type(exc).__name__}: {exc}',
                              checkpoints,budget.count) from exc
