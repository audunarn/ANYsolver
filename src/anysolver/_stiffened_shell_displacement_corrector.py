"""Private displacement-control corrector; no public admission or state commit.

The affine dead load is base + amplitude * direction. Amplitude is an independent
unknown, not a staged-programme cursor. All material trials use the same accepted
predecessor. The caller owns lifecycle publication and controller persistence.
"""
from dataclasses import dataclass
import warnings
import numpy as np
from scipy import sparse
from scipy.sparse import linalg as spla
from .control import cancellation_safe_point


@dataclass(frozen=True)
class DisplacementTrial:
    state: object
    amplitude: float
    evaluation: tuple
    iterations: int
    evaluations: int
    rejected_trials: int
    accepted_generation: int
    predecessor_state: object
    shell_predecessor: object
    beam_predecessor: object
    base_load: np.ndarray
    load_direction: np.ndarray
    control_dof: int
    target: float
    linear_solves: int = 0
    event_cell_evaluations: int = 0


@dataclass(frozen=True)
class DisplacementFailureDetail:
    accepted_generation: int
    target: float
    amplitude: float
    iterations: int
    evaluations: int
    linear_solves: int
    rejected_trials: int
    equilibrium_ratio: float
    constraint_max: float
    scaled_control_error: float
    event_cell_evaluations: int = 0


class DisplacementCorrectorFailure(RuntimeError):
    """Numerical failure; no accepted state has been published."""
    def __init__(self,message,detail=None):
        super().__init__(message)
        self.detail=detail


def bordered_correction(matrix, residual, direction, control_dof, gap, free):
    """Solve general sparse [K, -p; e, 0], including algebraic variables."""
    selected=np.flatnonzero(free==control_dof)
    if len(selected)!=1:
        raise ValueError("displacement control must be a free coordinate")
    gradient=np.zeros(matrix.shape[0]);gradient[control_dof]=1.
    return bordered_path_correction(matrix,residual,direction,gradient,gap,free)


def bordered_path_correction(matrix,residual,direction,gradient,gap,free):
    """General sparse border for a physical path row; no tangent inversion."""
    count=matrix.shape[0]
    gradient=np.asarray(gradient,dtype=float)
    if gradient.shape!=(count,) or not np.isfinite(gradient).all() or not np.isfinite(gap):
        raise ValueError("finite complete path gradient required")
    column=sparse.csc_matrix((-direction[free],(np.arange(len(free)),
                              np.zeros(len(free),dtype=int))),shape=(len(free),1))
    row=sparse.csc_matrix(gradient[free].reshape(1,-1))
    bordered=sparse.bmat([[matrix[free,:][:,free],column],[row,None]],format="csc")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error",spla.MatrixRankWarning)
            step=spla.spsolve(bordered,-np.r_[residual[free],gap])
    except spla.MatrixRankWarning as error:
        raise DisplacementCorrectorFailure("singular bordered tangent") from error
    if not np.isfinite(step).all():
        raise DisplacementCorrectorFailure("nonfinite bordered correction")
    full=np.zeros(count);full[free]=step[:-1]
    return full,float(step[-1])


def correct(driver, *, base_load, load_direction, amplitude, control_dof,
            target, max_iterations=20, max_backtracks=12, cancellation_token=None,
            trial_policy=None, event_records=None):
    """Return an uncommitted equilibrium at a translational displacement.

    Current scope is nodal dead translations only. No load-programme cursor is
    changed and no constitutive state is committed. Constraint/control acceptance
    uses the existing 1e-9 scaled compatibility limit; equilibrium remains 1e-8.
    Assembly updates recovery scratch; publication must rebuild/check recovery and
    recheck all predecessor identities under the owner's commit lock.
    """
    from ._stiffened_shell_ge_finite_experimental import _RotationStepTooLarge
    from ._stiffened_shell_bl5_local_experimental import BL5TrialDomainError
    owner=driver.owner
    from ._stiffened_shell_branch_event_trial import POLICY as EVENT_POLICY
    if trial_policy not in (None,EVENT_POLICY):
        raise ValueError("explicit supported private displacement trial policy required")
    from ._stiffened_shell_affine_endpoint import is_native_point_material
    native=is_native_point_material(owner)
    from ._stiffened_shell_affine_endpoint import require_native_displacement_policy
    require_native_displacement_policy(owner,driver)
    if native and trial_policy is not None:
        raise ValueError("native point displacement excludes branch event policy")
    if native:
        from ._stiffened_shell_displacement_adaptive import require_native_seed
        require_native_seed(owner,driver)
    if driver._accepted is None or not (
            owner._bl5_shell_material or getattr(owner,"_curved_material",False) or native):
        raise ValueError("accepted coupled-J2 BL5 predecessor required")
    n=owner._K.shape[0];size=n+len(driver._state.multipliers)
    nodal=owner._shell_count+6*len(owner._beam_ids)
    if driver._external is not None:
        raise ValueError("displacement corrector admits nodal dead translations only")
    if (type(control_dof) is not int or not 0<=control_dof<nodal or
            control_dof%6>=3 or control_dof not in owner._free):
        raise ValueError("free physical translation control required")
    if (not np.isfinite(target) or not np.isfinite(amplitude) or
            type(max_iterations) is not int or not 1<=max_iterations<=24 or
            type(max_backtracks) is not int or not 0<=max_backtracks<=12):
        raise ValueError("finite target/amplitude and bounded controls required")
    base=np.array(base_load,dtype=float,copy=True)
    pattern=np.array(load_direction,dtype=float,copy=True)
    if base.shape!=(n,) or pattern.shape!=(n,) or not np.isfinite(base).all() or not np.isfinite(pattern).all():
        raise ValueError("finite complete dead-load vectors required")
    allowed=np.zeros(n,dtype=bool)
    for start in range(0,nodal,6):allowed[start:start+3]=True
    if np.any(base[~allowed]) or np.any(pattern[~allowed]) or not np.any(pattern[owner._free]):
        raise ValueError("nonzero free translational load direction required")
    free=np.r_[owner._free,np.arange(n,size)]
    direction=np.r_[pattern,np.zeros(size-n)]
    with owner._commit_lock:
        generation=owner._generation;predecessor=driver._state
        shell=driver._shell_origins;beam=driver._beam_origins
        accepted_load=getattr(driver,"_displacement_applied_load",None)
        if accepted_load is None:
            accepted_load=(driver._applied_load if driver._programme is not None else
                           driver._load_factor*driver._pattern)
        if not np.array_equal(base+float(amplitude)*pattern,accepted_load):
            raise ValueError("affine load must start at the accepted endpoint")
    state=driver._increment_origin(predecessor)
    base.setflags(write=False);pattern.setflags(write=False)
    energy=float(np.max((abs(owner._K)@owner._coordinate_scale)*owner._coordinate_scale))
    if not np.isfinite(energy) or energy<=0.:
        raise ValueError("positive reference work scale required")
    weights=np.r_[owner._coordinate_scale,energy/owner._constraint_scale]/energy
    def current():
        if (owner._generation!=generation or driver._state is not predecessor or
                driver._shell_origins is not shell or driver._beam_origins is not beam):
            raise ValueError("stale displacement predecessor")
    evaluations=0;rejected=0;solves=0;amplitude=float(amplitude)
    local_events=[]
    def event_work():
        return sum(row["cell_evaluations"] for row in local_events)
    def evaluate(trial,value):
        nonlocal evaluations
        cancellation_safe_point(cancellation_token,"stiffened-shell.displacement.trial")
        current()
        evaluations+=1
        return driver._assemble(trial,0.,shell,beam,applied_load=base+value*pattern)
    def merit(trial,evaluation):
        # Fixed dual-work scaling, including constraint rows. The changing
        # applied-load equilibrium ratio remains mandatory for acceptance only.
        return float(np.linalg.norm(evaluation[0][free]*weights[free]))
    evaluation=evaluate(state,amplitude)
    def failure(message,iteration):
        return DisplacementCorrectorFailure(message,DisplacementFailureDetail(
            generation,float(target),amplitude,iteration,evaluations,solves,rejected,
            float(evaluation[2]),float(evaluation[3]),
            float(abs(state.q[control_dof]-target)/owner._reference_length),event_work()))
    def correction(gap,iteration):
        nonlocal solves
        solves+=1
        try:
            return bordered_correction(evaluation[1],evaluation[0],direction,
                                       control_dof,gap,free)
        except DisplacementCorrectorFailure as error:
            raise failure(str(error),iteration) from error
    # A full displacement predictor defines the corrector's initial guess.
    # Domain failure returns to the caller; never silently shorten the target.
    gap=state.q[control_dof]-target
    if abs(gap)/owner._reference_length>1e-9:
        step,delta=correction(gap,0)
        try:
            candidate=driver._advance(state,step,1.)
            value=amplitude+delta
            changed=evaluate(candidate,value)
            state,amplitude,evaluation=candidate,value,changed
        except (_RotationStepTooLarge,BL5TrialDomainError) as error:
            raise failure("displacement predictor outside domain",0) from error
    for iteration in range(max_iterations+1):
        control_gap=state.q[control_dof]-target
        if (evaluation[2]<=1e-8 and evaluation[3]<=1e-9 and
                abs(control_gap)/owner._reference_length<=1e-9):
            with owner._commit_lock:
                current()
                cancellation_safe_point(cancellation_token,"stiffened-shell.displacement.return")
                return DisplacementTrial(state,amplitude,evaluation,iteration,
                    evaluations,rejected,generation,predecessor,shell,beam,base,
                    pattern,control_dof,float(target),solves,event_work())
        if iteration==max_iterations:
            raise failure("displacement Newton iteration limit",iteration)
        step,delta=correction(control_gap,iteration)
        old=merit(state,evaluation)
        initial_amount=1.
        if trial_policy==EVENT_POLICY:
            from ._stiffened_shell_branch_event_trial import trial_fraction
            def event_check():
                current()
                cancellation_safe_point(cancellation_token,"stiffened-shell.displacement.event")
            record=dict(iteration=iteration,cell_evaluations=0,amount=None,events=())
            local_events.append(record)
            if event_records is not None:event_records.append(record)
            try:
                initial_amount,events=trial_fraction(driver,state,step,beam,event_check,record)
            except DisplacementCorrectorFailure as error:
                raise failure(str(error),iteration) from error
            record.update(amount=initial_amount,events=events)
        for backtrack in range(max_backtracks+1):
            amount=initial_amount*.5**backtrack
            try:
                candidate=driver._advance(state,step,amount)
                value=amplitude+amount*delta
                changed=evaluate(candidate,value)
            except (_RotationStepTooLarge,BL5TrialDomainError):
                rejected+=1;continue
            if merit(candidate,changed)<old:
                state,amplitude,evaluation=candidate,value,changed
                break
            rejected+=1
        else:
            raise failure("displacement backtrack budget exhausted",iteration)
    raise AssertionError("unreachable displacement corrector state")
