"""Private fixed-affine endpoint validation for admitted Q4 arc mechanics.

Decoding arrays or checkpoint framing is not mechanical acceptance. This module
replays the decoded endpoint in an isolated owner and driver. The final publisher
owns predecessor validation and the atomic live commit; this validator never
publishes state.
"""
from copy import copy
from threading import RLock
import numpy as np

from ._stiffened_shell_ge_finite_experimental import (
    FinitePointDriver,_State,_owned,_material_histories,_material_arrays,
    _shell_material_states,_shell_material_arrays)
from ._stiffened_shell_rotation_charts import owned_anchors,physical_frames


def is_native_point_material(owner):
    """Fixed-target native point route with admitted Q4/S3 material histories."""
    if getattr(owner,"_definition",None) is None:
        return False
    from ._stiffened_shell_q4_algorithmic_pullback import POLICY,HISTORICAL_POLICY
    definition=owner._definition
    return bool(definition.points and
        (definition.shell.q4_elements or definition.shell.s3_elements) and
        definition.shell_reference_policy=="flat" and
        definition.q4_pullback_policy==(POLICY if definition.shell.q4_elements else HISTORICAL_POLICY) and
        not definition.lines and not definition.footprints and
        not definition.distributing_footprints and not definition.finite_distributing_footprints)


def require_native_displacement_policy(owner,driver):
    """Never upgrade legacy S3 force-seed arithmetic during replay."""
    if (is_native_point_material(owner) and owner._definition.shell.s3_elements and
            driver._stable_s3 != bool(owner._has_physical_fibre and
                                      owner._definition.shell.j2_curve is None)):
        raise ValueError("native S3 displacement seed numerical policy mismatch")


def has_native_s3_material(owner):
    return bool(is_native_point_material(owner) and owner._definition.shell.s3_elements
                and owner._definition.shell.j2_curve is not None)


def has_shell_material(owner):
    """Only admitted algorithmic shell histories belong in affine endpoints."""
    return owner._bl5_shell_material or (is_native_point_material(owner) and
        owner._definition.shell.j2_curve is not None) or (
        getattr(owner, "_curved_material", False)
        and owner._definition.shell.j2_curve is not None)


def validate_arrays(owner,a,*,native_chart=False):
    """Replay decoded fixed-affine translation arrays in isolated mechanics."""
    if not (owner._bl5_shell_material or getattr(owner,"_curved_reference",False) or is_native_point_material(owner)):
        raise ValueError("bounded coupled affine endpoint required")
    prepared=copy(owner);prepared._commit_lock=RLock();prepared._writing=False
    prepared._finite_driver=None;prepared._accepted=None
    prepared._s3_restart_validation = getattr(owner, "_s3_restart_policy", None) is not None
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
    if is_native_point_material(owner) and not native_chart and not np.array_equal(
            anchors,np.tile(np.eye(3),(len(owner._shell_ids),1,1))):
        raise ValueError("native point displacement excludes rebased shell charts")
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
    for name in (("shell_alpha","shell_origin_alpha") if has_shell_material(owner) else ()):
        if np.any(a[name]<0.):raise ValueError("nonphysical shell J2 history")
    shell_parent=(_shell_material_states(a["shell_origin_plastic"],a["shell_origin_alpha"])
                  if has_shell_material(owner) else driver._shell_origins)
    s3_material=has_native_s3_material(owner)
    if s3_material:
        predecessor_anchors=owned_anchors(a["shell_origin_anchors"],len(owner._shell_ids))
        if not native_chart and not np.array_equal(predecessor_anchors,
                              np.tile(np.eye(3),(len(owner._shell_ids),1,1))):
            raise ValueError("native point displacement excludes rebased predecessor charts")
        from ._stiffened_shell_ge_finite_experimental import _restore_native_s3_histories
        accepted_s3, predecessor_s3, origin_q, origin_anchors = _restore_native_s3_histories(
            prepared, q, anchors, a)
        shell_parent += predecessor_s3
        driver._snapshot_s3_accepted = accepted_s3
        driver._shell_predecessor_q = origin_q
        driver._shell_predecessor_anchors = origin_anchors
    native=is_native_point_material(owner)
    if native:
        from ._stiffened_shell_beam_history import histories
        beam_parent=histories(prepared._beam_parts,a,"beam_origin")
        histories(prepared._beam_parts,a,"beam")
    else:
        beam_parent=_material_histories(prepared,a["beam_origin_plastic"],a["beam_origin_accumulated"])
        # Validate accepted beam history admissibility before replay comparison.
        _material_histories(prepared,a["beam_plastic"],a["beam_accumulated"])
    state=_State(q,_owned(a["frames"]),_owned(a["cells"]),
                 _owned(a["resultants"]),_owned(a["multipliers"]),anchors)
    evaluation=driver._assemble(state,0.,shell_parent,beam_parent,applied_load=a["applied_load"])
    if not np.isfinite(evaluation[2]) or evaluation[2]>1e-8 or evaluation[3]>1e-9:
        raise ValueError("mechanically inconsistent displacement equilibrium")
    if native:
        from ._stiffened_shell_beam_history import arrays
        comparisons=list(arrays(prepared._beam_parts,evaluation[5],"beam"))
    else:
        bp,ba=_material_arrays(evaluation[5])
        comparisons=[("beam_plastic",bp),("beam_accumulated",ba)]
    if has_shell_material(owner):
        q4_count = len(owner._definition.shell.q4_elements)
        sp,sa=_shell_material_arrays(evaluation[4][:q4_count] if s3_material else evaluation[4])
        comparisons.extend((("shell_plastic",sp),("shell_alpha",sa)))
        if s3_material:
            from ._stiffened_shell_ge_finite_experimental import _require_native_s3_replay
            saved = _shell_material_states(a["shell_plastic"],a["shell_alpha"]) + accepted_s3
            _require_native_s3_replay(prepared, state, saved, evaluation[4],
                                     driver=driver, residual=evaluation[0], applied=a["applied_load"])
            prepared._s3_restart_validation = False
    for name,repeated in comparisons:
        saved=a[name]
        if native and not name.startswith("shell_"):
            if not np.array_equal(saved,repeated):
                raise ValueError("displacement native material replay mismatch")
            continue
        scale=max(float(np.max(abs(saved),initial=0.)),
                  float(np.max(abs(repeated),initial=0.)),np.finfo(float).tiny)
        if np.max(abs(saved-repeated),initial=0.)>64*np.finfo(float).eps*scale:
            raise ValueError("displacement material replay mismatch")
    # Scratch recovery belongs only to this prepared driver. The publisher must
    # seal histories, build results/checkpoint and recheck its live predecessor.
    return driver,state,evaluation,shell_parent,beam_parent
