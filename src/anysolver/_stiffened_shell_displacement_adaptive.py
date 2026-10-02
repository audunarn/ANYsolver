"""Signed displacement adaptation with bounded durable controller metadata."""
from dataclasses import dataclass,replace,asdict
from hashlib import sha256
import json
import numpy as np
from ._stiffened_shell_displacement_increment import DisplacementIncrementState
from ._stiffened_shell_increment_control import AdaptiveIncrementControl
from ._stiffened_shell_ge_checkpoint_binary import MAX_CHECKPOINT_BYTES
from ._stiffened_shell_displacement_corrector import DisplacementCorrectorFailure

MAGIC=b"ANYSSDCA1"
HEADER_LIMIT=256*1024


@dataclass(frozen=True)
class Context:
    state: DisplacementIncrementState
    dof: int
    direction_sha256: str
    history_start: int
    max_iterations: int
    max_backtracks: int


def direction_hash(direction):
    return sha256(np.asarray(direction,dtype="<f8").tobytes()).hexdigest()


def encode(model,context,inner):
    value=dict(model=model,state=context.state.payload(),dof=context.dof,
        direction_sha256=context.direction_sha256,history_start=context.history_start,
        max_iterations=context.max_iterations,max_backtracks=context.max_backtracks)
    header=json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode("ascii")
    if len(header)>HEADER_LIMIT or type(inner) is not bytes or not inner:
        raise ValueError("bounded adaptive displacement metadata required")
    content=MAGIC+len(header).to_bytes(4,"little")+header+inner
    if len(content)+32>MAX_CHECKPOINT_BYTES:raise ValueError("adaptive displacement byte limit")
    return content+sha256(content).digest()


def decode(owner,raw):
    if not owner._bl5_shell_material or type(raw) is not bytes or not raw.startswith(MAGIC) or not len(MAGIC)+36<len(raw)<=MAX_CHECKPOINT_BYTES:
        raise ValueError("bounded adaptive displacement checkpoint required")
    start=len(MAGIC)+4;size=int.from_bytes(raw[len(MAGIC):start],"little")
    if not 0<size<=HEADER_LIMIT or start+size>=len(raw)-32 or sha256(raw[:-32]).digest()!=raw[-32:]:
        raise ValueError("invalid adaptive displacement framing")
    try:
        header=raw[start:start+size];v=json.loads(header)
        if json.dumps(v,sort_keys=True,separators=(",",":"),allow_nan=False).encode("ascii")!=header:
            raise ValueError("noncanonical adaptive displacement metadata")
        if type(v) is not dict or set(v)!={"model","state","dof","direction_sha256","history_start","max_iterations","max_backtracks"} or v["model"]!=owner._identity:
            raise ValueError("incompatible adaptive displacement metadata")
        state=DisplacementIncrementState.from_payload(v["state"])
        context=Context(state,*(v[k] for k in ("dof","direction_sha256","history_start","max_iterations","max_backtracks")))
    except (TypeError,KeyError,UnicodeError,RecursionError) as error:
        raise ValueError("invalid adaptive displacement metadata") from error
    if (any(type(v[k]) is not int for k in ("dof","history_start","max_iterations","max_backtracks")) or
            not 0<=context.dof<owner._shell_count+6*len(owner._beam_ids) or context.dof%6>=3 or
            context.dof not in owner._free or context.history_start<0 or
            not 1<=context.max_iterations<=24 or not 0<=context.max_backtracks<=12 or
            type(context.direction_sha256) is not str or len(context.direction_sha256)!=64 or
            any(c not in "0123456789abcdef" for c in context.direction_sha256)):
        raise ValueError("invalid adaptive displacement controls")
    inner=raw[start+size:-32]
    if inner.startswith(MAGIC):raise ValueError("nested adaptive displacement checkpoint")
    return context,inner


def inner_checkpoint(owner):
    snapshot=getattr(owner,"_displacement_snapshot",None)
    return snapshot[0] if snapshot is not None else owner._finite_driver.checkpoint()


def validate_progress(owner,context):
    if owner._finite_driver is None or owner._finite_driver._accepted is None:
        raise ValueError("adaptive displacement requires a finite accepted seed")
    snapshot=getattr(owner,"_displacement_snapshot",None)
    rows=tuple(row.displacement for row in context.state.attempts if row.accepted)
    if snapshot is None:
        if rows or context.history_start!=0 or owner._finite_driver._state.q[context.dof]!=context.state.initial:
            raise ValueError("adaptive displacement seed mismatch")
    else:
        _,metadata,a=snapshot;history=a["history"]
        start=context.history_start
        if start>len(history) or tuple(history[start:,0])!=rows:
            raise ValueError("adaptive displacement accepted history mismatch")
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
    dof=control.dof(owner);direction=direction_hash(driver._load(actions))
    targets=tuple(float(v) for v in targets)
    current=getattr(owner,"_displacement_adaptive",None)
    if current is not None and not current[0].state.completed:
        context=current[0]
        if (context.state.targets!=targets or context.state.limits!=limits or
                context.dof!=dof or context.direction_sha256!=direction or
                context.max_iterations!=max_iterations or context.max_backtracks!=max_backtracks):
            raise ValueError("pending adaptive displacement controls must match")
    else:
        snapshot=getattr(owner,"_displacement_snapshot",None)
        count=0 if snapshot is None else len(snapshot[2]["history"])
        context=Context(DisplacementIncrementState(limits,targets,float(driver._state.q[dof])),
                        dof,direction,count,max_iterations,max_backtracks)
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
                linear_solves=detail.linear_solves,rejected_trials=detail.rejected_trials)
            context=replace(context,state=state)
            raw=encode(owner._identity,context,inner_checkpoint(owner))
            with owner._commit_lock:owner._displacement_adaptive=(context,raw)
        else:context=owner._displacement_adaptive[0]
    return owner.recover()
