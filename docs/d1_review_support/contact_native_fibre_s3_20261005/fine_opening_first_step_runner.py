from pathlib import Path
from hashlib import sha256
import os,json,time,sys
import numpy as np
ROOT=Path('C:/ANYworkspaceWork/ANYsolver-contact-main-reconcile-20261001')
sys.path.insert(0,str(ROOT/'tests'))
from test_general_contact_native_fine_lifecycle import _owner
from anysolver._ge_beam3_p5_seeded.core import canonical

def test_actual_opening_first_newton_observation():
    started=time.monotonic()
    dest=Path(os.environ['CONTACT_APP_RESULT_RECORD']+'-opening-first-step.json')
    raw=(ROOT/'tests/data/general_contact_native_fibre_s3_plastic_k8e7_component_v1.checkpoint').read_bytes()
    assert sha256(raw).hexdigest()=='5c72a14e4288010a7f9407ada3cd1c5334e37ae071a7baf2281de75615a7d50a'
    record=dict(scope='one actual opening Newton step; no physical commit',events=[])
    def save():
        record['elapsed_s']=time.monotonic()-started
        temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(record,indent=2));temp.replace(dest)
    def timed(name,function,summary=None):
        def call(*args,**kwargs):
            row=dict(phase=name,start_s=time.monotonic()-started,status='running')
            record['events'].append(row);save();t=time.monotonic()
            try:
                value=function(*args,**kwargs)
                row.update(status='completed',duration_s=time.monotonic()-t)
                if summary:row.update(summary(value))
                return value
            except Exception as exc:
                row.update(status='exception',duration_s=time.monotonic()-t,error=type(exc).__name__+': '+str(exc),diagnostics=getattr(exc,'integration_diagnostics',None))
                raise
            finally:save()
        return call
    owner=timed('construction',_owner)()
    owner._restore=timed('source_replay',owner._restore)
    owner._contact=timed('contact',owner._contact,lambda v:dict(gap=v.contact.minimum_gap_m,pair_evaluations=owner.pair_evaluations,reuse_hits=owner.contact_reuse_hits))
    owner._assemble_structural=timed('structural_material',owner._assemble_structural)
    owner._assemble=timed('coupled_assembly',owner._assemble,lambda v:dict(metrics=list(v[2])))
    owner._candidate_geometry_admissible=timed('endpoint_geometry',owner._candidate_geometry_admissible,lambda v:dict(admitted=bool(v)))
    owner._swept_cancellable=timed('complete_path',owner._swept_cancellable,lambda v:dict(admitted=bool(v)))
    owner._activation_fraction=timed('activation_fraction',owner._activation_fraction,lambda v:dict(fraction=float(v)))
    step=timed('linear_step',owner._step,lambda v:dict(correction=float(v[1]),step_norm=float(np.linalg.norm(v[0]))))
    count=0;in_candidate=False
    begin=owner._begin_candidate_context
    def candidate_begin(token):
        nonlocal in_candidate
        begin(token);in_candidate=True
    owner._begin_candidate_context=candidate_begin
    def one_step(*args,**kwargs):
        nonlocal count
        if not in_candidate:return step(*args,**kwargs)
        if count:raise RuntimeError('bounded opening observation complete')
        count+=1
        value=step(*args,**kwargs);record['step']=value[0].tolist();record['actual_candidate_steps']=count;save();return value
    owner._step=one_step
    original_record=owner._record
    def committed_prefix_only(target,*args,**kwargs):
        if target>1:raise RuntimeError('bounded opening observation complete')
        return original_record(target,*args,**kwargs)
    owner._record=committed_prefix_only
    run=owner.solve(checkpoint=raw,expected_sha256=sha256(raw).hexdigest(),stop_after=2)
    record.update(status=run.status,failure=run.failure,completed=run.accepted.completed_targets,
        checkpoint_unchanged=run.checkpoint==raw,cache_cleared=owner._contact_reuse_entry is None,
        trial_failures=owner.curved_trial_failures);save()
    assert record.get('actual_candidate_steps')==1,record
    assert run.status=='failed' and 'bounded opening observation complete' in run.failure
    assert run.accepted.completed_targets==1 and run.checkpoint==raw
    assert canonical(run.accepted.native_histories)==canonical(json.loads(raw)['records'][0]['histories'])
    assert owner._contact_reuse_entry is None and not owner._contact_reuse_enabled