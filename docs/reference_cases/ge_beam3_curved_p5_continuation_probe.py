"""Bounded pseudo-arclength research with unchanged beam mechanics.

The beam hyperplane uses positions, frame chords and load, not accumulated rotations.
This is a continuation algorithm, not bifurcation detection or qualification.
No automatic retry, step adaptation or branch switching is performed.
"""

from copy import deepcopy
from dataclasses import dataclass

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation, skew
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _array, _readonly
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
from docs.reference_cases.ge_beam3_curved_p5_assembly_history_probe import (
    NonlinearAssemblyHistoryProbe, AssemblyTrial, AssemblyPathError, AssemblyTransactionError, _Budget,
)
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import NonlinearLocalError


class ContinuationError(RuntimeError):
    """No accepted continuation step; explicit caller decision is required."""


def bordered(jacobian, load, normal):
    n = len(load)
    matrix = np.zeros((n+1,n+1))
    matrix[:n,:n] = jacobian
    matrix[:n,n] = -load
    matrix[n] = normal
    return matrix


def tangent(jacobian, load, previous, metric):
    normal = metric*previous
    rhs = np.zeros(len(load)+1);rhs[-1] = 1.
    try:
        made = np.linalg.solve(bordered(jacobian,load,normal),rhs)
    except np.linalg.LinAlgError as exc:
        raise ContinuationError('singular continuation border; no automatic branch selection') from exc
    length = float(np.sqrt(np.sum(metric*made*made)))
    if not np.isfinite(length) or length <= 0 or not np.isfinite(made).all():
        raise ContinuationError('unresolved continuation direction')
    return made/length


def pseudo_step(evaluate, move, difference, norm, state, parameter, load, metric,
                previous, step, *, max_iterations=16, constraint=None):
    """One hyperplane predictor/corrector; callbacks cannot commit material state.

    evaluate returns internal residual, its spatial-coordinate derivative and
    an opaque response. A manifold constraint returns the exact weighted
    displacement and its current spatial derivative; Euclidean difference is
    the default. move applies multiplicative rotational increments if needed.
    """
    if (type(max_iterations) is not int or not 0<=max_iterations<=16
            or not np.isfinite(step) or not 0<step<=.25):
        raise ValueError('bounded positive step and at most sixteen updates required')
    load = np.asarray(load,dtype=float)
    metric = np.asarray(metric,dtype=float)
    previous = np.asarray(previous,dtype=float)
    if (load.ndim!=1 or metric.shape!=(len(load)+1,) or previous.shape!=metric.shape
            or not np.isfinite(load).all() or not np.isfinite(metric).all()
            or not np.isfinite(previous).all() or np.any(metric<0) or metric[-1]<=0):
        raise ValueError('finite consistent continuation vectors required')
    force,jacobian,_ = evaluate(state)
    if norm(force-parameter*load,parameter)>1e-11:
        raise ContinuationError('initial state is not in equilibrium')
    direction = tangent(jacobian,load,previous,metric)
    normal = metric*direction
    current = move(state,step*direction[:-1])
    lam = float(parameter+step*direction[-1])
    def residual(value, factor):
        internal,jac,response = evaluate(value)
        force = internal-factor*load
        if constraint is None:
            gap,gradient = normal[:-1] @ difference(value,state),normal[:-1]
        else:
            gap,gradient = constraint(value,state,direction[:-1],metric[:-1])
        arc = float(gap+normal[-1]*(factor-parameter)-step)
        measure = max(norm(force,factor),abs(arc))
        if not np.isfinite(measure) or not np.isfinite(jac).all() or not np.isfinite(gradient).all():
            raise ContinuationError('nonfinite augmented residual')
        return force,arc,jac,response,np.r_[gradient,normal[-1]],measure
    force,arc,jac,response,border,measure = residual(current,lam)
    for iteration in range(max_iterations+1):
        if measure<=1e-11:
            return current,lam,direction,response,iteration,abs(arc)
        if iteration==max_iterations:
            raise ContinuationError('continuation iteration bound reached')
        try:
            delta = np.linalg.solve(bordered(jac,load,border),-np.r_[force,arc])
        except np.linalg.LinAlgError as exc:
            raise ContinuationError('singular corrector; no stabilization') from exc
        if not np.isfinite(delta).all():
            raise ContinuationError('nonfinite corrector')
        for backtrack in range(10):
            scale = .5**backtrack
            try:
                candidate = move(current,scale*delta[:-1])
                factor = float(lam+scale*delta[-1])
                checked = residual(candidate,factor)
            except (NonlinearLocalError,ValueError):
                continue
            if checked[-1]<measure:
                current,lam = candidate,factor
                force,arc,jac,response,border,measure = checked
                break
        else:
            raise ContinuationError('continuation line-search bound reached')
    raise AssertionError('unreachable')


def spatial_derivative(response):
    """Derivative of spatial moment components, not an altered energy Hessian.

    BCH gives f(exp(eps)Q)=f(Q)+(H-0.5*hat(f))eps for a rotational
    block. The skew term vanishes at rotational equilibrium for dead forces.
    """
    made = response.tangent.copy()
    for i,moment in enumerate(response.residual.reshape(-1,6)[:,3:]):
        block = slice(6*i+3,6*i+6)
        made[block,block] -= .5*skew(moment)
    return made


def frame_constraint(current, origin, direction, metric, free):
    """Exact chord hyperplane value and derivative under spatial increments.

    Each rotation term is weight/2 * <U-U0, hat(w0)U0>_F. Its derivative
    is weight*axl(skew(hat(w0)U0 U.T)), equal to weight*w0 at the origin.
    """
    x,u = current
    x0,u0 = origin
    d = np.zeros((len(x),6));d.ravel()[free] = direction
    weights = np.zeros((len(x),6));weights.ravel()[free] = metric
    gradient = np.zeros_like(d)
    gradient[:,:3] = weights[:,:3]*d[:,:3]
    value = float(np.sum(gradient[:,:3]*(x-x0)))
    for i in range(len(x)):
        if not np.all(weights[i,3:]==weights[i,3]):
            raise ValueError('isotropic frame metric required')
        w = weights[i,3]
        a = skew(d[i,3:]) @ u0[i]
        value += .5*w*float(np.sum((u[i]-u0[i])*a))
        k = .5*(a @ u[i].T-u[i] @ a.T)
        gradient[i,3:] = w*np.array([k[2,1],k[0,2],k[1,0]])
    return value,gradient.ravel()[free]


@dataclass(frozen=True)
class ContinuationTrial:
    origin_epoch: int
    parameter: float
    tangent: np.ndarray
    step: float
    arc_residual: float
    assembly_trial: AssemblyTrial


class BeamContinuationProbe:
    """Private model ownership and atomic model/load/tangent publication."""

    def __init__(self, model, load_pattern, *, parameter=0., previous=None):
        if type(model) is not NonlinearAssemblyHistoryProbe or model._pending is not None:
            raise ValueError('exact assembly with no pending trial required')
        self._pattern = _readonly(_array(load_pattern,(model._nodes,3),'dead force pattern'))
        if not np.isfinite(parameter) or not np.linalg.norm(self._pattern):
            raise ValueError('finite factor and nonzero force pattern required')
        if not np.array_equal(model.committed.forces,parameter*self._pattern):
            raise ValueError('committed forces must match continuation factor')
        free = model._free
        self._metric = np.r_[np.where(free%6<3,1/model._length**2,1.)/len(model._free_nodes),1.]
        if previous is None:
            previous = np.zeros(len(free)+1);previous[-1] = 1.
        previous = _array(previous,(len(free)+1,),'continuation orientation')
        if np.sum(self._metric*previous**2)<=0:
            raise ValueError('nonzero weighted orientation required')
        self._checkpoint = (deepcopy(model),float(parameter),_readonly(previous))
        self._pending = self._pending_digest = self._staged = None

    @property
    def committed_model(self):
        return deepcopy(self._checkpoint[0])

    @property
    def parameter(self):
        return self._checkpoint[1]

    @property
    def orientation(self):
        return self._checkpoint[2].copy()

    def trial(self, step, *, max_iterations=16, max_mixed_evaluations=None):
        self._pending = self._pending_digest = self._staged = None
        original,parameter,previous = self._checkpoint
        staged = deepcopy(original)
        state = staged.committed
        cap = 256*len(staged._maps)
        if max_mixed_evaluations is None:
            max_mixed_evaluations = cap
        if type(max_mixed_evaluations) is not int or not 0<=max_mixed_evaluations<=cap:
            raise ValueError('bounded continuation evaluation count required')
        budget = _Budget(max_mixed_evaluations)
        free = staged._free
        pattern = staged._external(self._pattern)[free]
        def evaluate(geometry):
            x,u = geometry
            response = staged._solve_all(x,u,state.histories,budget)
            return response.residual[free],spatial_derivative(response)[np.ix_(free,free)],response
        def move(geometry,delta):
            full = np.zeros(6*staged._nodes);full[free] = delta
            full = full.reshape(-1,6)
            if np.max(np.linalg.norm(full[:,3:],axis=1))>=.9*np.pi:
                raise ValueError('rotation increment requires explicit smaller step')
            x,u = geometry
            return x+full[:,:3],np.array([rotation(d[3:]) @ q for d,q in zip(full,u)])
        def difference(a,b):
            # Euclidean fallback is unused by the explicit frame constraint.
            return np.column_stack((a[0]-b[0],np.zeros_like(a[0]))).ravel()[free]
        def constraint(a,b,d,w):
            return frame_constraint(a,b,d,w,free)
        def norm(residual,factor):
            full = np.zeros(6*staged._nodes);full[free] = residual
            return staged._norm(full,factor*self._pattern)
        try:
            geometry,factor,direction,response,iterations,arc = pseudo_step(
                evaluate,move,difference,norm,(state.positions,state.rotations),parameter,
                pattern,self._metric,previous,step,max_iterations=max_iterations,constraint=constraint)
            x,u = geometry
            forces = factor*self._pattern
            trial = AssemblyTrial(state.epoch,_readonly(x),_readonly(u),_readonly(forces),
                deepcopy(state.histories),response,staged._norm(response.residual-staged._external(forces),forces),
                iterations,budget.count)
            staged._pending,staged._pending_digest = trial,digest(trial)
            result = ContinuationTrial(state.epoch,factor,_readonly(direction),float(step),arc,trial)
            self._pending_digest,self._pending,self._staged = digest(result),result,staged
            return result
        except (ValueError,NonlinearLocalError,AssemblyPathError,np.linalg.LinAlgError) as exc:
            raise ContinuationError('continuation failed without commit; no automatic retry') from exc

    def _owned(self, trial):
        if trial is None or trial is not self._pending or trial.origin_epoch!=self._checkpoint[0].committed.epoch:
            raise ContinuationError('owned current continuation trial required')

    def commit(self, trial):
        self._owned(trial)
        if digest(trial)!=self._pending_digest:
            raise ContinuationError('altered continuation trial')
        staged = deepcopy(self._staged)
        # deepcopy preserves ownership of the staged assembly's pending object.
        try:
            staged.commit(staged._pending)
        except (ValueError,AssemblyTransactionError,np.linalg.LinAlgError) as exc:
            raise ContinuationError('accepted continuation commit validation failed') from exc
        checkpoint = (staged,trial.parameter,_readonly(trial.tangent))
        exported = staged.committed
        self._checkpoint = checkpoint
        self._pending = self._pending_digest = self._staged = None
        return exported

    def discard(self, trial):
        self._owned(trial)
        self._pending = self._pending_digest = self._staged = None
