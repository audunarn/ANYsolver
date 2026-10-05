"""One frozen-pose discriminator; no new equilibrium target or acceptance claim."""
from dataclasses import replace, asdict
from hashlib import sha256
from pathlib import Path
import json, os, sys, time
import numpy as np

REPO=Path('C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001')
sys.path.insert(0,str(REPO/'tests'))
from test_general_contact_native_curved_s3_static import _analysis
from anysolver.general_contact.native_material_s3 import NativeMaterialS3Patch
from anysolver.general_contact.native_curved_s3_work import NativeCurvedMaterialS3Work

RAW=Path(__file__).parent/'installed_seeded_enforcement_k2e7/actual_result.json-enforcement.checkpoint'

def test_saved_fine_pose_tenth_budget_integration_response():
    started=time.monotonic()
    raw=RAW.read_bytes()
    owner=_analysis(physical_fibres=True,plastic_fibres=True,normal_stiffness_Pa_per_m=2e7)
    state,_=owner._restore(raw,sha256(raw).hexdigest())
    pair=owner.pairs[0];work=pair.work;patch=work.contact
    settings=replace(patch.settings,
        energy_absolute_tolerance=patch.settings.energy_absolute_tolerance/10,
        force_absolute_tolerance=patch.settings.force_absolute_tolerance/10,
        tangent_absolute_tolerance=patch.settings.tangent_absolute_tolerance/10)
    tighter=NativeCurvedMaterialS3Work(NativeMaterialS3Patch(patch.rule,patch.beam_node_ids,
        normal_stiffness_Pa_per_m=patch.stiffness,integration_settings=settings,
        geometry_tolerance_m=patch.geometry_tolerance,rim_clearance_m=patch.rim_clearance),work.shell)
    nodes=owner.context.nodes[0];m=state.mechanical;u=state.shell_displacement
    args=(m.positions[nodes],m.position_low[nodes],m.cell_rotations[0],u)
    base=work.evaluate(*args)
    out=Path(os.environ['CONTACT_APP_RESULT_RECORD']+'-integration-control.json')
    record=dict(checkpoint_sha256=sha256(raw).hexdigest(),
        scope='saved fine pose only; local linearized error estimate, no new solve',
        base_settings=asdict(patch.settings),control_settings=asdict(settings))
    try:control=tighter.evaluate(*args)
    except (ValueError,MemoryError) as exc:
        record.update(status='control_rejected',error=str(exc),
            diagnostics=getattr(exc,'integration_diagnostics',None),elapsed_s=time.monotonic()-started)
        out.write_text(json.dumps(record,indent=2));raise
    # Constitutive origin is the virgin target origin, not the accepted plastic history.
    r,K,_,_=owner._assemble_structural(m,u,1.,owner.initial.native_histories)
    slots=np.r_[owner.context.slots[0],owner.context.count+np.arange(len(u))]
    rows,cols=np.meshgrid(slots,slots,indexing='ij')
    np.add.at(K,(rows,cols),base.tangent.toarray())
    delta=np.zeros(len(r));np.add.at(delta,slots,control.residual-base.residual)
    free=np.r_[owner.context.free,owner.context.count+owner.shell_free]
    correction=np.zeros(len(r));correction[free]=np.linalg.solve(K[np.ix_(free,free)],-delta[free])
    tip=6*owner.context.node_ids.index(3)+2
    tip_value=-0.00015532544418551608
    dc=control.contact;bc=base.contact
    relative=lambda a,b:float(np.linalg.norm(np.asarray(a)-b)/np.linalg.norm(b))
    record.update(status='evaluated',elapsed_s=time.monotonic()-started,
        force_relative_change=relative(dc.beam_force_n,bc.beam_force_n),
        moment_relative_change=relative(dc.beam_moment_nm,bc.beam_moment_nm),
        energy_absolute_change_j=abs(dc.potential_j-bc.potential_j),
        residual_difference_norm=float(np.linalg.norm(delta)),
        linearized_tip_correction_m=float(correction[tip]),
        linearized_tip_relative_change=abs(float(correction[tip])/tip_value),
        intervals=[bc.integration_intervals,dc.integration_intervals],
        evaluations=[bc.integration_evaluations,dc.integration_evaluations],
        estimated_errors=[[c.energy_error_j,c.force_error_n,c.tangent_error_n_per_m] for c in (bc,dc)])
    out.write_text(json.dumps(record,indent=2))
    assert record['linearized_tip_relative_change']<=.002,record
    assert record['force_relative_change']<=.002,record
