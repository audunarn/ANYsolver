"""Observe one actual driver Newton step, then stop before another step/commit."""
from pathlib import Path
from hashlib import sha256
import json,os,sys,time
import numpy as np
ROOT=Path('C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001')
sys.path.insert(0,str(ROOT/'tests'))
from test_general_contact_native_curved_s3_static import _analysis
from anysolver._ge_beam3_p5_seeded.core import canonical
RAW=Path('C:/ANYworkspaceWork/contact_native_fibre_s3_20261005/candidate08/installed_seeded_enforcement_k2e7/actual_result.json-enforcement.checkpoint')
HASH='2c96b3194034fe153a8e0e15ca4882d0b235cbdc1e75b2580f14210e1c15755c'

def test_actual_first_newton_step_cost_without_commit():
    started=time.monotonic();dest=Path(os.environ['CONTACT_APP_RESULT_RECORD']+'-first-step.json')
    rows=[];record=dict(scope='one actual driver Newton step, no physical commit',
        source_sha256=HASH,stiffness_Pa_per_m=4e7,events=rows)
    def save():
        record['elapsed_s']=time.monotonic()-started
        temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(record,indent=2));temp.replace(dest)
    def timed(name,function,summary=None):
        def call(*args,**kwargs):
            event=dict(phase=name,start_s=time.monotonic()-started,status='running')
            rows.append(event);save();t=time.monotonic()
            try:
                value=function(*args,**kwargs)
                event.update(status='completed',duration_s=time.monotonic()-t)
                if summary:event.update(summary(value))
                return value
            except Exception as exc:
                event.update(status='exception',duration_s=time.monotonic()-t,error=type(exc).__name__+': '+str(exc))
                raise
            finally:save()
        return call
    raw=RAW.read_bytes();assert sha256(raw).hexdigest()==HASH
    owner=timed('fine_construction',lambda:_analysis(physical_fibres=True,plastic_fibres=True,
        normal_stiffness_Pa_per_m=4e7))()
    source=timed('source_construction',lambda:_analysis(physical_fibres=True,plastic_fibres=True,
        normal_stiffness_Pa_per_m=2e7))()
    guess=timed('source_replay_guess_factory',owner.make_initial_guess)(source,raw,HASH)
    record.update(owner_identity=owner.identity,guess_fingerprint=guess.fingerprint);save()
    owner._initial_guess_trial=timed('initial_to_guess_admission',owner._initial_guess_trial)
    owner._contact=timed('contact',owner._contact,lambda v:dict(
        gap_lower_m=v.contact.minimum_gap_m,candidate_requests=owner.candidate_evaluations,
        pair_evaluations=owner.pair_evaluations,reuse_hits=owner.contact_reuse_hits))
    observed_contact=owner._contact
    def capture_rejected_pose(mechanical,displacement):
        try:return observed_contact(mechanical,displacement)
        except MemoryError as exc:
            snapshot=Path(os.environ['CONTACT_APP_RESULT_RECORD']+'-rejected-pose.json')
            if not snapshot.exists():
                nodes=owner.context.nodes[0]
                snapshot.write_text(json.dumps(dict(
                    scope='first rejected actual Newton contact pose; no physical commit',
                    owner_identity=owner.identity,source_checkpoint_sha256=HASH,
                    work_identity=owner.pairs[0].work.identity,
                    positions=mechanical.positions[nodes].tolist(),
                    position_low=mechanical.position_low[nodes].tolist(),
                    cell_rotations=mechanical.cell_rotations[0].tolist(),
                    shell_displacement=displacement.tolist(),
                    failure=str(exc),diagnostics=getattr(exc,'integration_diagnostics',None)),indent=2))
            raise
    owner._contact=capture_rejected_pose
    owner._assemble_structural=timed('structural_material',owner._assemble_structural)
    owner._candidate_geometry_admissible=timed('endpoint_geometry',owner._candidate_geometry_admissible,
        lambda v:dict(admitted=bool(v)))
    owner._swept_cancellable=timed('complete_swept',owner._swept_cancellable,
        lambda v:dict(admitted=bool(v)))
    owner._activation_fraction=timed('activation_fraction',owner._activation_fraction,
        lambda v:dict(fraction=float(v)))
    owner._assemble=timed('coupled_assembly',owner._assemble,lambda v:dict(metrics=list(v[2])))
    step_function=timed('linear_step',owner._step,lambda v:dict(correction=float(v[1]),
        step_norm=float(np.linalg.norm(v[0]))))
    steps=0
    def one_step(*args,**kwargs):
        nonlocal steps
        if steps:
            record['controlled_stop']='before second Newton step';save()
            raise RuntimeError('bounded first-Newton observation complete')
        steps+=1
        return step_function(*args,**kwargs)
    def no_commit(*args,**kwargs):
        record['controlled_stop']='before physical commit';save()
        raise RuntimeError('bounded first-Newton observation complete')
    owner._step=one_step;owner._record=no_commit
    initial=owner._checkpoint(())
    run=owner.solve(stop_after=1,initial_guess=guess)
    record.update(status=run.status,failure=run.failure,completed_targets=run.accepted.completed_targets,
        checkpoint_unchanged=run.checkpoint==initial,cache_cleared=owner._contact_reuse_entry is None,
        trial_failures=owner.curved_trial_failures,pair_evaluations=owner.pair_evaluations,
        reuse_hits=owner.contact_reuse_hits);save()
    assert run.status=='failed' and run.accepted.completed_targets==0
    assert run.checkpoint==initial and canonical(run.accepted.native_histories)==canonical(owner.initial.native_histories)
    assert owner._contact_reuse_entry is None and not owner._contact_reuse_enabled
    # A real admission failure is retained, not mistaken for a complete step.
    assert 'bounded first-Newton observation complete' in run.failure,record
