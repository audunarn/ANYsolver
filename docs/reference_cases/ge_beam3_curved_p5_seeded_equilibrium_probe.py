"""Bounded elastic branch initialization from an explicit external shape seed.

This is not a physical load history or automatic branch switching. It returns
a new verified equilibrium model, leaving the caller's virgin model untouched.
"""

from copy import deepcopy

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _array, _frames, _readonly
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
from docs.reference_cases.ge_beam3_curved_p5_assembly_history_probe import (
    NonlinearAssemblyHistoryProbe, AssemblyTrial, AssemblyPathError, AssemblyTransactionError, _Budget,
)
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import NonlinearLocalError
from docs.reference_cases.ge_beam3_curved_p5_continuation_probe import spatial_derivative


class SeededEquilibriumError(RuntimeError):
    """No verified elastic branch state; the supplied model is unchanged."""


def solve(model, positions, rotations, forces, *, max_iterations=16, max_mixed_evaluations=None):
    if (type(model) is not NonlinearAssemblyHistoryProbe or model._pending is not None
            or model.committed.epoch!=0):
        raise ValueError('virgin research assembly without pending trial required')
    cap = 256*len(model._maps)
    if max_mixed_evaluations is None:
        max_mixed_evaluations = cap
    if (type(max_iterations) is not int or not 0<=max_iterations<=16
            or type(max_mixed_evaluations) is not int or not 0<=max_mixed_evaluations<=cap):
        raise ValueError('bounded seeded solve required')
    x = _array(positions,(model._nodes,3),'seed positions')
    u = _frames(rotations,model._nodes,'seed spatial rotations')
    f = _array(forces,(model._nodes,3),'spatial dead force')
    if (not np.array_equal(x[model._fixed],model._coordinates[model._fixed])
            or not np.array_equal(u[model._fixed],np.tile(np.eye(3),(len(model._fixed),1,1)))):
        raise ValueError('seed must preserve every clamp exactly')
    staged = deepcopy(model)
    origins = staged.committed.histories
    budget = _Budget(max_mixed_evaluations)
    external,free = staged._external(f),staged._free
    def evaluate(a,b):
        response = staged._solve_all(a,b,origins,budget)
        if any(s.response.plastic_active for e in response.elements for s in e.stations):
            raise SeededEquilibriumError('elastic branch seed cannot invent plastic load history')
        return response
    try:
        response = evaluate(x,u)
        for iteration in range(max_iterations+1):
            residual = response.residual-external
            norm = staged._norm(residual,f)
            if norm<=1e-11:
                trial = AssemblyTrial(0,_readonly(x),_readonly(u),_readonly(f),deepcopy(origins),
                    response,norm,iteration,budget.count)
                staged._pending,staged._pending_digest = trial,digest(trial)
                staged.commit(trial)
                return staged
            if iteration==max_iterations:
                raise SeededEquilibriumError('seeded equilibrium iteration bound reached')
            step = np.zeros(6*staged._nodes)
            derivative = spatial_derivative(response)
            step[free] = np.linalg.solve(derivative[np.ix_(free,free)],-residual[free])
            if not np.isfinite(step).all():
                raise SeededEquilibriumError('nonfinite seeded correction')
            for backtrack in range(10):
                delta = (step*.5**backtrack).reshape(-1,6)
                if np.max(np.linalg.norm(delta[:,3:],axis=1))>=.9*np.pi:
                    continue
                a = x+delta[:,:3]
                b = np.array([rotation(d[3:]) @ old for d,old in zip(delta,u)])
                try:
                    candidate = evaluate(a,b)
                except (ValueError,NonlinearLocalError):
                    continue
                if staged._norm(candidate.residual-external,f)<norm:
                    x,u,response = a,b,candidate
                    break
            else:
                raise SeededEquilibriumError('seeded equilibrium line-search bound reached')
        raise AssertionError('unreachable')
    except (ValueError,NonlinearLocalError,AssemblyPathError,AssemblyTransactionError,np.linalg.LinAlgError) as exc:
        raise SeededEquilibriumError(
            f'seeded equilibrium failed without caller state change: {type(exc).__name__}: {exc}') from exc
