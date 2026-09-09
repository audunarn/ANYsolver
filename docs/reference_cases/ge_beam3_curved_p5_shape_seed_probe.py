"""Two-phase elastic branch seed: angle-controlled load, then original dead load.

FAILED DEVELOPMENT EXPERIMENT: the two-element postcritical seed exhausted its
mixed-evaluation budget. The failing phase was not recorded. This module is
preserved for diagnosis; it is not a selected or qualified solver.

The x-y tip-angle chart is explicit benchmark initialization, not general load
or MPC support. Both phases share the old sixteen-update/256-per-element budget.
No changes to the beam potential, tolerance, section law or accepted history.
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
from docs.reference_cases.ge_beam3_curved_p5_continuation_probe import spatial_derivative, bordered


class ShapeSeedError(RuntimeError):
    """No final branch equilibrium; caller state is unchanged."""


@dataclass(frozen=True)
class ShapeSeedResult:
    model: object
    intermediate_factor: float
    shape_iterations: int
    shape_evaluations: int
    load_iterations: int
    load_evaluations: int


def tip_angle(u):
    d = u[-1,:,0]
    denominator = d[0]**2+d[1]**2
    if denominator<=1e-12:
        raise ValueError('tip direction outside x-y angle chart')
    return float(np.arctan2(d[1],d[0])),np.array([-d[0]*d[2]/denominator,-d[1]*d[2]/denominator,1.])


def solve(model, positions, rotations, forces, *, max_iterations=16, max_mixed_evaluations=None):
    if (type(model) is not NonlinearAssemblyHistoryProbe or model._pending is not None
            or model.committed.epoch!=0 or model._nodes-1 in model._fixed):
        raise ValueError('virgin assembly with a free tip and no pending trial required')
    cap = 256*len(model._maps)
    if max_mixed_evaluations is None:
        max_mixed_evaluations = cap
    if (type(max_iterations) is not int or not 0<=max_iterations<=16 or
            type(max_mixed_evaluations) is not int or not 0<=max_mixed_evaluations<=cap):
        raise ValueError('bounded two-phase initialization required')
    x = _array(positions,(model._nodes,3),'seed positions')
    u = _frames(rotations,model._nodes,'seed rotations')
    f = _array(forces,(model._nodes,3),'dead force')
    if (not np.array_equal(x[model._fixed],model._coordinates[model._fixed]) or
            not np.array_equal(u[model._fixed],np.tile(np.eye(3),(len(model._fixed),1,1)))):
        raise ValueError('seed must preserve clamps')
    target,_ = tip_angle(u)
    if not 0<target<np.pi/2 or not np.linalg.norm(f):
        raise ValueError('explicit positive first-branch tip-angle seed and nonzero force required')
    staged = deepcopy(model)
    origins = staged.committed.histories
    budget = _Budget(max_mixed_evaluations)
    free = staged._free
    external = staged._external(f)
    def evaluate(a,b,factor):
        response = staged._solve_all(a,b,origins,budget)
        if any(s.response.plastic_active for e in response.elements for s in e.stations):
            raise ShapeSeedError('shape initialization cannot invent plastic load history')
        angle,gradient = tip_angle(b)
        if abs(angle-target)>=np.pi/2:
            raise ValueError('tip angle left the initial branch chart')
        residual = response.residual-factor*external
        gap = angle-target
        normal = np.zeros(6*staged._nodes);normal[-3:] = gradient
        matrix = bordered(spatial_derivative(response)[np.ix_(free,free)],external[free],np.r_[normal[free],0.])
        measure = max(staged._norm(residual,factor*f),abs(gap))
        return response,residual,gap,matrix,measure
    try:
        factor = 1.
        response,residual,gap,matrix,measure = evaluate(x,u,factor)
        for iteration in range(max_iterations+1):
            if measure<=1e-11:
                break
            if iteration==max_iterations:
                raise ShapeSeedError('shape phase exhausted update budget')
            delta = np.linalg.solve(matrix,-np.r_[residual[free],gap])
            if not np.isfinite(delta).all():
                raise ShapeSeedError('nonfinite bordered correction')
            for backtrack in range(10):
                scale = .5**backtrack
                full = np.zeros(6*staged._nodes);full[free] = scale*delta[:-1]
                full = full.reshape(-1,6)
                if np.max(np.linalg.norm(full[:,3:],axis=1))>=.9*np.pi:
                    continue
                a = x+full[:,:3]
                b = np.array([rotation(d[3:]) @ old for d,old in zip(full,u)])
                trial_factor = float(factor+scale*delta[-1])
                try:
                    candidate = evaluate(a,b,trial_factor)
                except (ValueError,NonlinearLocalError):
                    continue
                if candidate[-1]<measure:
                    x,u,factor = a,b,trial_factor
                    response,residual,gap,matrix,measure = candidate
                    break
            else:
                raise ShapeSeedError('shape phase line-search bound reached')
        shape_count = budget.count
        trial = AssemblyTrial(0,_readonly(x),_readonly(u),_readonly(factor*f),deepcopy(origins),
            response,staged._norm(residual,factor*f),iteration,shape_count)
        staged._pending,staged._pending_digest = trial,digest(trial)
        staged.commit(trial)
        # This is an explicit second phase, not a retry after a failed solve.
        # Its force target is exactly the original input and no angle is fixed.
        final = staged.trial(f,max_iterations=max_iterations-iteration,
            max_mixed_evaluations=max_mixed_evaluations-shape_count)
        if any(s.response.plastic_active for e in final.response.elements for s in e.stations):
            raise ShapeSeedError('load phase yielded; no invented loading history allowed')
        staged.commit(final)
        return ShapeSeedResult(staged,float(factor),iteration,shape_count,final.iterations,final.mixed_evaluations)
    except (ValueError,NonlinearLocalError,AssemblyPathError,AssemblyTransactionError,np.linalg.LinAlgError) as exc:
        raise ShapeSeedError(f'two-phase seed failed without caller mutation: {type(exc).__name__}: {exc}') from exc
