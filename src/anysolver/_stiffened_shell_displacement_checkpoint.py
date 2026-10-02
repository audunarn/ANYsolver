"""Private displacement snapshot framing; decoding is NOT mechanical acceptance.

No force factors are fabricated. Generation includes chart events; history rows
contain only actual accepted displacement steps (target, amplitude). The seed is
an authentic earlier accepted endpoint identified by its checkpoint digest.
"""
import json
from hashlib import sha256
import numpy as np
from ._stiffened_shell_ge_checkpoint_binary import encode,decode,MAX_CHECKPOINT_BYTES

MAGIC=b"ANYSSDC1"
KIND="finite_displacement_bl5_coupled"
POLICY="B3_GE_BL5_COUPLED_DISPLACEMENT_CONTROL_V1_DEV"


def _layout(owner,steps):
    n=owner._K.shape[0];members=len(owner._beam_parts);shells=len(owner._shell_parts)
    stations=sum(len(part[0].operator.cell.stations) for part in owner._beam_parts)
    return (("q",(n,)),("frames",(len(owner._beam_ids),3,3)),
        ("cells",(members,2,3,3)),("resultants",(members,18)),
        ("multipliers",(owner._C.shape[0],)),
        ("shell_anchors",(len(owner._shell_ids),3,3)),
        ("shell_frames",(len(owner._shell_ids),3,3)),
        ("base_load",(n,)),("load_direction",(n,)),("applied_load",(n,)),
        ("seed",(2,)),("history",(steps,2)),
        ("beam_plastic",(stations,6,2)),("beam_accumulated",(stations,2)),
        ("beam_origin_plastic",(stations,6,2)),("beam_origin_accumulated",(stations,2)),
        ("shell_plastic",(shells,12,3)),("shell_alpha",(shells,12)),
        ("shell_origin_plastic",(shells,12,3)),("shell_origin_alpha",(shells,12)))


def _canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode("ascii")


def encode_snapshot(owner, *, generation, seed_generation, seed_sha256,
                    control_dof, arrays):
    """Frame owned endpoint arrays, without conferring mechanical validity."""
    steps=len(arrays["history"])
    metadata=dict(policy=POLICY,model=owner._identity,generation=generation,
        seed_generation=seed_generation,seed_sha256=seed_sha256,
        control_dof=control_dof,steps=steps)
    header=_canonical(metadata)
    if len(header)>1024 or set(arrays)!={name for name,_ in _layout(owner,steps)}:
        raise ValueError("invalid displacement snapshot fields")
    inner=encode(KIND,owner._identity,generation,
                 tuple((name,arrays[name]) for name,_ in _layout(owner,steps)))
    content=MAGIC+len(header).to_bytes(4,"little")+header+inner
    if len(content)+32>MAX_CHECKPOINT_BYTES:
        raise ValueError("displacement snapshot exceeds resource limit")
    raw=content+sha256(content).digest()
    decode_snapshot(owner,raw)
    return raw


def decode_snapshot(owner,raw):
    """Validate framing/layout/controller consistency; caller must replay mechanics.

    Returned byte-backed arrays are read-only. Caller must additionally validate
    physical frames, supports, material state, equilibrium and endpoint work before
    atomic publication in an isolated restoration owner.
    """
    if (not owner._bl5_shell_material or type(raw) is not bytes or
            not raw.startswith(MAGIC) or not len(MAGIC)+4+32<len(raw)<=MAX_CHECKPOINT_BYTES):
        raise ValueError("bounded coupled displacement snapshot required")
    start=len(MAGIC)+4;length=int.from_bytes(raw[len(MAGIC):start],"little")
    if not 0<length<=1024 or start+length>=len(raw)-32:
        raise ValueError("invalid displacement metadata bound")
    if sha256(memoryview(raw)[:-32]).digest()!=raw[-32:]:
        raise ValueError("displacement snapshot digest mismatch")
    try:
        header=raw[start:start+length];m=json.loads(header.decode("ascii"))
        canonical=_canonical(m)
    except (ValueError,UnicodeError,RecursionError) as error:
        raise ValueError("invalid displacement metadata") from error
    if (type(m) is not dict or set(m)!={"policy","model","generation","seed_generation",
            "seed_sha256","control_dof","steps"} or canonical!=header or
            m["policy"]!=POLICY or m["model"]!=owner._identity):
        raise ValueError("incompatible displacement metadata")
    if (any(type(m[k]) is not int for k in ("generation","seed_generation","control_dof","steps")) or
            not 1<=m["seed_generation"]<=m["generation"] or
            not 1<=m["steps"]==m["generation"]-m["seed_generation"] or
            m["generation"]>MAX_CHECKPOINT_BYTES//8):
        raise ValueError("invalid displacement generation/history")
    dof=m["control_dof"];nodal=owner._shell_count+6*len(owner._beam_ids)
    if not 0<=dof<nodal or dof%6>=3 or dof not in owner._free:
        raise ValueError("free physical translation control required")
    digest=m["seed_sha256"]
    if type(digest) is not str or len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("canonical seed checkpoint digest required")
    def shapes(kind,generation):
        if kind!=KIND or generation!=m["generation"]:
            raise ValueError("displacement mechanical identity mismatch")
        return _layout(owner,m["steps"])
    _,_,a=decode(raw[start+length:-32],owner._identity,shapes)
    if np.any(np.diff(np.r_[a["seed"][0],a["history"][:,0]])==0.):
        raise ValueError("displacement history targets must change")
    target,amplitude=a["history"][-1]
    if not np.array_equal(a["base_load"]+amplitude*a["load_direction"],a["applied_load"]):
        raise ValueError("displacement affine load mismatch")
    if abs(a["q"][dof]-target)/owner._reference_length>1e-9:
        raise ValueError("displacement target mismatch")
    return m,a



def validate_endpoint(owner,raw):
    """Replay an endpoint in an isolated driver; never publish to the caller.

    Returns private prepared mechanics and decoded controller data. This is not
    a public restore operation and does not authenticate the loading path.
    """
    from copy import copy
    from threading import RLock
    from ._stiffened_shell_ge_finite_experimental import (
        FinitePointDriver,_State,_owned,_material_histories,_material_arrays,
        _shell_material_states,_shell_material_arrays)
    from ._stiffened_shell_rotation_charts import owned_anchors,physical_frames
    metadata,a=decode_snapshot(owner,raw)
    prepared=copy(owner);prepared._commit_lock=RLock();prepared._writing=False
    prepared._finite_driver=None;prepared._accepted=None
    if getattr(owner,"_external_context",None) is not None:
        raise ValueError("displacement snapshot excludes external load contexts")
    driver=FinitePointDriver(prepared)
    n=owner._shell_count+6*len(owner._beam_ids)
    q=_owned(a["q"])
    if (np.any(q[owner._fixed]!=0.) or np.any(q[n:]!=0.) or
            np.any(q[owner._shell_count:n].reshape(-1,6)[:,3:]!=0.)):
        raise ValueError("invalid displacement coordinate/support layout")
    for name in ("base_load","load_direction","applied_load"):
        if np.any(a[name][n:]) or np.any(a[name][:n].reshape(-1,6)[:,3:]):
            raise ValueError("displacement snapshot requires nodal dead translations")
    if not np.any(a["load_direction"][owner._free]):
        raise ValueError("nonzero free displacement load direction required")
    anchors=owned_anchors(a["shell_anchors"],len(owner._shell_ids))
    witness=owned_anchors(a["shell_frames"],len(owner._shell_ids))
    if not np.allclose(physical_frames(q[:owner._shell_count],anchors),witness,
                       rtol=0.,atol=1e-11):
        raise ValueError("displacement shell pose witness mismatch")
    fixed=set(owner._fixed)
    for i,anchor in enumerate(anchors):
        if any(6*i+j in fixed for j in (3,4,5)) and np.linalg.norm(anchor-np.eye(3))>1e-12:
            raise ValueError("displacement anchor violates rotational support")
    for name in ("frames","cells"):
        for frame in a[name].reshape(-1,3,3):
            if np.linalg.norm(frame.T@frame-np.eye(3))>1e-9 or abs(np.linalg.det(frame)-1.)>1e-9:
                raise ValueError("nonphysical displacement rotation")
    for name in ("shell_alpha","shell_origin_alpha"):
        if np.any(a[name]<0.):raise ValueError("nonphysical shell J2 history")
    shell_parent=_shell_material_states(a["shell_origin_plastic"],a["shell_origin_alpha"])
    beam_parent=_material_histories(prepared,a["beam_origin_plastic"],a["beam_origin_accumulated"])
    # Validate accepted beam history admissibility before replay comparison.
    _material_histories(prepared,a["beam_plastic"],a["beam_accumulated"])
    state=_State(q,_owned(a["frames"]),_owned(a["cells"]),
                 _owned(a["resultants"]),_owned(a["multipliers"]),anchors)
    evaluation=driver._assemble(state,0.,shell_parent,beam_parent,applied_load=a["applied_load"])
    if not np.isfinite(evaluation[2]) or evaluation[2]>1e-8 or evaluation[3]>1e-9:
        raise ValueError("mechanically inconsistent displacement equilibrium")
    bp,ba=_material_arrays(evaluation[5]);sp,sa=_shell_material_arrays(evaluation[4])
    for name,repeated in (("beam_plastic",bp),("beam_accumulated",ba),
                          ("shell_plastic",sp),("shell_alpha",sa)):
        saved=a[name]
        scale=max(float(np.max(abs(saved),initial=0.)),
                  float(np.max(abs(repeated),initial=0.)),np.finfo(float).tiny)
        if np.max(abs(saved-repeated),initial=0.)>64*np.finfo(float).eps*scale:
            raise ValueError("displacement material replay mismatch")
    # Scratch recovery belongs only to this prepared driver. The publisher must
    # seal histories, build results/checkpoint and recheck its live predecessor.
    return metadata,a,driver,state,evaluation,shell_parent,beam_parent
