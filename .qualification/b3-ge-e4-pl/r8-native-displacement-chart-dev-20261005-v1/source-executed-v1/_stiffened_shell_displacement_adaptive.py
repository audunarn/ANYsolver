"""Signed displacement adaptation with bounded durable controller metadata."""
from dataclasses import dataclass,replace,asdict
from hashlib import sha256
import json
import numpy as np
from ._stiffened_shell_displacement_increment import DisplacementIncrementState,MAX_EVENT_WORK
from ._stiffened_shell_increment_control import AdaptiveIncrementControl
from ._stiffened_shell_ge_checkpoint_binary import MAX_CHECKPOINT_BYTES
from ._stiffened_shell_displacement_corrector import DisplacementCorrectorFailure

from ._stiffened_shell_branch_event_trial import POLICY as EVENT_POLICY

MAGIC=b"ANYSSDCA1"
EVENT_MAGIC=b"ANYSSDCA2"
NATIVE_MAGIC=b"ANYSSDCN1"
MAGICS=(MAGIC,EVENT_MAGIC,NATIVE_MAGIC)
HEADER_LIMIT=256*1024


@dataclass(frozen=True)
class Context:
    state: DisplacementIncrementState
    dof: int
    direction_sha256: str
    history_start: int
    max_iterations: int
    max_backtracks: int
    trial_policy: str | None = None
    event_work_start: int = 0

    def __post_init__(self):
        if ((self.trial_policy is not None and
                (type(self.trial_policy) is not str or self.trial_policy!=EVENT_POLICY)) or
                type(self.event_work_start) is not int or not 0<=self.event_work_start<=MAX_EVENT_WORK or
                self.event_work_start+sum(row.event_cell_evaluations for row in self.state.attempts)>MAX_EVENT_WORK or
                (self.trial_policy is None and (self.event_work_start or
                    any(row.event_cell_evaluations for row in self.state.attempts)))):
            raise ValueError("invalid adaptive displacement event policy/work")


def direction_hash(direction):
    return sha256(np.asarray(direction,dtype="<f8").tobytes()).hexdigest()


def require_native_seed(owner,driver):
    """Check native seed admission before controller publication or restoration."""
    from ._stiffened_shell_affine_endpoint import require_native_displacement_policy
    require_native_displacement_policy(owner,driver)
    anchors=driver._state.shell_anchors
    snapshot=getattr(owner,"_displacement_snapshot",None)
    charted=False
    if snapshot is not None:
        from ._stiffened_shell_displacement_checkpoint import identities
        metadata=snapshot[1]
        charted=(metadata.get("chart_events",0)>0 and metadata.get("policy")==identities(owner)[2])
    if (driver._programme is not None or driver._external is not None or
            driver._adaptive_state is not None or
            (snapshot is None and anchors is not None) or
            (anchors is not None and not charted and not np.array_equal(
                anchors,np.tile(np.eye(3),(len(owner._shell_ids),1,1))))):
        raise ValueError("native adaptive displacement requires an ordinary unrebased force seed")
    if getattr(owner,"_displacement_snapshot",None) is None:
        applied=driver._load_factor*driver._pattern
        nodal=owner._shell_count+6*len(owner._beam_ids)
        if np.any(applied[nodal:]) or np.any(applied[:nodal].reshape(-1,6)[:,3:]):
            raise ValueError("native adaptive displacement requires nodal dead translations")


def require_native_inner(inner):
    from ._stiffened_shell_ge_checkpoint_binary import MAGIC as FORCE_MAGIC,S3_MAGIC,NATIVE_SHELL_MAGIC
    from ._stiffened_shell_displacement_checkpoint import MAGIC as FIXED_MAGIC
    if not inner.startswith((FORCE_MAGIC,S3_MAGIC,NATIVE_SHELL_MAGIC,FIXED_MAGIC)):
        raise ValueError("nested or unsupported native adaptive displacement checkpoint")


def encode(model,context,inner,*,native=False):
    if type(native) is not bool or (native and context.trial_policy is not None):
        raise ValueError("native adaptive displacement excludes branch event policy")
    value=dict(model=model,state=context.state.payload(),dof=context.dof,
        direction_sha256=context.direction_sha256,history_start=context.history_start,
        max_iterations=context.max_iterations,max_backtracks=context.max_backtracks)
    if context.trial_policy is not None:
        value.update(trial_policy=context.trial_policy,event_work_start=context.event_work_start)
    magic=NATIVE_MAGIC if native else EVENT_MAGIC if context.trial_policy is not None else MAGIC
    header=json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode("ascii")
    if len(header)>HEADER_LIMIT or type(inner) is not bytes or not inner:
        raise ValueError("bounded adaptive displacement metadata required")
    if native:require_native_inner(inner)
    content=magic+len(header).to_bytes(4,"little")+header+inner
    if len(content)+32>MAX_CHECKPOINT_BYTES:raise ValueError("adaptive displacement byte limit")
    return content+sha256(content).digest()


def decode(owner,raw):
    from ._stiffened_shell_affine_endpoint import is_native_point_material
    native=is_native_point_material(owner)
    if (not (owner._bl5_shell_material or getattr(owner,"_curved_material",False) or native) or
            type(raw) is not bytes or not raw.startswith(MAGICS) or
            not len(MAGIC)+36<len(raw)<=MAX_CHECKPOINT_BYTES):
        raise ValueError("bounded adaptive displacement checkpoint required")
    if raw.startswith(NATIVE_MAGIC)!=native:
        raise ValueError("adaptive displacement formulation identity mismatch")
    eventful=raw.startswith(EVENT_MAGIC)
    start=len(MAGIC)+4;size=int.from_bytes(raw[len(MAGIC):start],"little")
    if not 0<size<=HEADER_LIMIT or start+size>=len(raw)-32 or sha256(raw[:-32]).digest()!=raw[-32:]:
        raise ValueError("invalid adaptive displacement framing")
    try:
        header=raw[start:start+size];v=json.loads(header)
        if json.dumps(v,sort_keys=True,separators=(",",":"),allow_nan=False).encode("ascii")!=header:
            raise ValueError("noncanonical adaptive displacement metadata")
        keys={"model","state","dof","direction_sha256","history_start","max_iterations","max_backtracks"}
        if eventful:keys|={"trial_policy","event_work_start"}
        if type(v) is not dict or set(v)!=keys or v["model"]!=owner._identity:
            raise ValueError("incompatible adaptive displacement metadata")
        state=DisplacementIncrementState.from_payload(v["state"])
        if eventful and v["trial_policy"]!=EVENT_POLICY:
            raise ValueError("explicit adaptive event trial policy required")
        context=Context(state,*(v[k] for k in ("dof","direction_sha256","history_start","max_iterations","max_backtracks")),
                        trial_policy=v.get("trial_policy"),event_work_start=v.get("event_work_start",0))
    except (TypeError,KeyError,UnicodeError,RecursionError) as error:
        raise ValueError("invalid adaptive displacement metadata") from error
    if (any(type(v[k]) is not int for k in ("dof","history_start","max_iterations","max_backtracks")) or
            not 0<=context.dof<owner._shell_count+6*len(owner._beam_ids) or context.dof%6>=3 or
            context.dof not in owner._free or not 0<=context.history_start<=MAX_CHECKPOINT_BYTES//8 or
            not 1<=context.max_iterations<=24 or not 0<=context.max_backtracks<=12 or
            type(context.direction_sha256) is not str or len(context.direction_sha256)!=64 or
            any(c not in "0123456789abcdef" for c in context.direction_sha256)):
        raise ValueError("invalid adaptive displacement controls")
    inner=raw[start+size:-32]
    if inner.startswith(MAGICS):
        raise ValueError("nested adaptive displacement checkpoint")
    if native:require_native_inner(inner)
    return context,inner


def inner_checkpoint(owner):
    snapshot=getattr(owner,"_displacement_snapshot",None)
    return snapshot[0] if snapshot is not None else owner._finite_driver.checkpoint()


def validate_progress(owner,context):
    if owner._finite_driver is None or owner._finite_driver._accepted is None:
        raise ValueError("adaptive displacement requires a finite accepted seed")
    from ._stiffened_shell_affine_endpoint import is_native_point_material
    if is_native_point_material(owner):
        if context.trial_policy is not None:
            raise ValueError("native adaptive displacement excludes branch event policy")
        require_native_seed(owner,owner._finite_driver)
    snapshot=getattr(owner,"_displacement_snapshot",None)
    rows=tuple(row.displacement for row in context.state.attempts if row.accepted)
    if snapshot is None:
        if rows or context.history_start!=0 or context.event_work_start!=0 or owner._finite_driver._state.q[context.dof]!=context.state.initial:
            raise ValueError("adaptive displacement seed mismatch")
    else:
        _,metadata,a=snapshot;history=a["history"]
        start=context.history_start
        if (start>len(history) or tuple(history[start:,0])!=rows or
                (start==0 and context.event_work_start!=0)):
            raise ValueError("adaptive displacement accepted history mismatch")
        accepted_work=sum(row.event_cell_evaluations for row in context.state.attempts if row.accepted)
        if (metadata.get("trial_policy")!=context.trial_policy or
                metadata.get("event_cell_evaluations",0)!=context.event_work_start+accepted_work):
            raise ValueError("adaptive displacement event policy/work mismatch")
        initial=a["seed"][0] if start==0 else history[start-1,0]
        if (context.state.initial!=initial or context.dof!=metadata["control_dof"] or
                context.direction_sha256!=direction_hash(a["load_direction"])):
            raise ValueError("adaptive displacement load/control mismatch")


def solve(owner,actions,targets,control,limits,*,max_iterations,max_backtracks,
          cancellation_token=None,on_accepted=None):
    from ._stiffened_shell_displacement_control import solve as fixed_solve,DisplacementControl
    if type(limits) is not AdaptiveIncrementControl:
        raise ValueError("typed adaptive displacement limits required")
    driver=owner._finite_driver
    if driver is None:raise ValueError("accepted displacement seed required")
    if type(control) is not DisplacementControl or type(targets) is not tuple or any(
            not isinstance(v,(float,int,np.floating,np.integer)) or isinstance(v,(bool,np.bool_)) or not np.isfinite(v) for v in targets):
        raise ValueError("typed control and finite displacement targets required")
    from ._stiffened_shell_affine_endpoint import is_native_point_material
    native=is_native_point_material(owner)
    if native:
        if control.trial_policy is not None:
            raise ValueError("native adaptive displacement excludes branch event policy")
        require_native_seed(owner,driver)
    dof=control.dof(owner);direction=direction_hash(driver._load(actions))
    targets=tuple(float(v) for v in targets)
    snapshot=getattr(owner,"_displacement_snapshot",None)
    if snapshot is not None and snapshot[1].get("trial_policy")!=control.trial_policy:
        raise ValueError("displacement trial policy must match restart")
    current=getattr(owner,"_displacement_adaptive",None)
    if current is not None and not current[0].state.completed:
        context=current[0]
        if (context.state.targets!=targets or context.state.limits!=limits or
                context.dof!=dof or context.direction_sha256!=direction or
                context.max_iterations!=max_iterations or context.max_backtracks!=max_backtracks or
                context.trial_policy!=control.trial_policy):
            raise ValueError("pending adaptive displacement controls must match")
    else:
        snapshot=getattr(owner,"_displacement_snapshot",None)
        count=0 if snapshot is None else len(snapshot[2]["history"])
        context=Context(DisplacementIncrementState(limits,targets,float(driver._state.q[dof])),
                        dof,direction,count,max_iterations,max_backtracks,control.trial_policy,
                        0 if snapshot is None else snapshot[1].get("event_cell_evaluations",0))
    while not context.state.completed:
        target=context.state.next_target()
        predecessor=owner._finite_driver;generation=owner._generation
        try:
            fixed_solve(owner,actions,(target,),control,max_iterations=max_iterations,
                max_backtracks=max_backtracks,cancellation_token=cancellation_token,
                on_accepted=on_accepted,_adaptive=context)
        except DisplacementCorrectorFailure as error:
            if owner._finite_driver is not predecessor or owner._generation!=generation:
                # Observer failure after publication is not a rejected corrector.
                raise
            detail=error.detail
            if detail is None:raise
            state=context.state.record(False,evaluations=detail.evaluations,
                linear_solves=detail.linear_solves,rejected_trials=detail.rejected_trials,
                event_cell_evaluations=detail.event_cell_evaluations)
            context=replace(context,state=state)
            raw=encode(owner._identity,context,inner_checkpoint(owner),native=native)
            result=(replace(owner._finite_driver._accepted,status="accepted_prefix",
                            increment_attempts=state.attempts)
                    if getattr(owner,"_displacement_snapshot",None) is not None else None)
            with owner._commit_lock:
                if owner._finite_driver is not predecessor or owner._generation!=generation:
                    raise ValueError("stale adaptive displacement failure")
                owner._displacement_adaptive=(context,raw)
                if result is not None:owner._finite_driver._accepted=result
        else:context=owner._displacement_adaptive[0]
    return owner.recover()
