"""Curved material S3 work integrated in the existing retained native owner."""
import json,os,runpy
from pathlib import Path
import numpy as np
import pytest
from anysolver.general_contact.native_multi_s3_static import CURVED_MATERIAL_PROFILE


def _analysis(**kwargs):
    return runpy.run_path(str(Path(__file__).parents[1]/'examples/general_contact_native_curved_material_s3.py'))['analysis'](**kwargs)


def test_curved_s3_coupled_first_contact_complete_retained_and_target_work():
    owner=_analysis(targets=(1.,));run=owner.solve()
    path=os.environ.get('CONTACT_APP_RESULT_RECORD')
    if path:Path(path+'-curved-s3-owner.json').write_text(json.dumps(dict(
        status=run.status,failure=run.failure,profile=run.profile,completed_targets=run.accepted.completed_targets,
        candidate_evaluations=owner.candidate_evaluations,pair_evaluations=owner.pair_evaluations,
        trial_failures=owner.curved_trial_failures,
        contact=json.loads(run.checkpoint)['records'][-1]['contact'] if run.accepted.completed_targets else None),indent=2))
    assert run.status=='completed',run.failure
    assert run.profile==CURVED_MATERIAL_PROFILE and run.accepted.completed_targets==1
    contact=run.accepted.contact.contact
    assert contact.minimum_gap_m>=-3e-5
    assert np.linalg.norm(run.accepted.shell_displacement)>0.
    assert contact.minimum_rim_clearance_m>1.
    np.testing.assert_allclose(contact.beam_force_n+contact.shell_force_n,0.,atol=1e-10)
    np.testing.assert_allclose(contact.beam_moment_nm+contact.shell_moment_nm,0.,atol=1e-10)


def test_curved_s3_active_checkpoint_for_bounded_three_target_continuation():
    owner=_analysis();run=owner.solve(stop_after=1)
    path=os.environ.get('CONTACT_APP_RESULT_RECORD')
    if path:
        Path(path+'-curved-s3-active.checkpoint').write_bytes(run.checkpoint)
        Path(path+'-curved-s3-active.json').write_text(json.dumps(dict(status=run.status,failure=run.failure,
            completed_targets=run.accepted.completed_targets,checkpoint_sha256=run.checkpoint_sha256,
            profile=run.profile,contact=json.loads(run.checkpoint)['records'][-1]['contact'] if run.accepted.completed_targets else None,
            trial_failures=owner.curved_trial_failures,candidate_evaluations=owner.candidate_evaluations),indent=2))
    assert run.status=='paused',run.failure
    assert run.profile==CURVED_MATERIAL_PROFILE and run.accepted.completed_targets==1
    contact=run.accepted.contact.contact
    assert contact.minimum_gap_m>=-3e-5 and np.linalg.norm(run.accepted.shell_displacement)>0.
    np.testing.assert_allclose(contact.beam_force_n+contact.shell_force_n,0.,atol=1e-10)
    np.testing.assert_allclose(contact.beam_moment_nm+contact.shell_moment_nm,0.,atol=1e-10)


def test_curved_s3_driver_forwards_cancellation_and_preserves_initial_prefix():
    from anysolver.control import CancellationToken
    owner=_analysis(targets=(1.,));token=CancellationToken()
    initial=owner._checkpoint(())
    owner._assemble=lambda *args:(np.zeros(owner.context.count+len(owner.initial.shell_displacement)),
        np.zeros((1,1)),(1.,1.,1.),(),owner.initial.contact)
    owner._step=lambda *args:(np.zeros(owner.context.count+len(owner.initial.shell_displacement)),1.)
    real=owner._swept_cancellable;calls=[]
    def injected(*args,**kwargs):
        assert kwargs['cancellation_token'] is token
        calls.append(1);token.cancel();return real(*args,**kwargs)
    owner._swept_cancellable=injected
    run=owner.solve(cancellation_token=token)
    assert calls==[1] and run.status=='cancelled'
    assert run.accepted.completed_targets==0 and run.checkpoint==initial


def test_curved_s3_owner_uses_authoritative_path_increment_columns():
    from anysolver.control import CancellationToken,SolveCancelled
    owner=_analysis(targets=(1.,));start=owner.initial.mechanical;u=owner.initial.shell_displacement
    step=np.zeros(owner.context.count+len(u));step[12:15]=(.001,-.002,.001)
    step[owner.context.count:]=np.linspace(.001,-.002,len(u))
    end=owner.context.advance(start,step[:owner.context.count]);last=u+step[owner.context.count:]
    token=CancellationToken();work=owner.pairs[0].work;real=work.certify_path
    calls=[]
    def captured(pose,translations,angular,shell_increment,**kwargs):
        nodes=owner.context.nodes[0]
        np.testing.assert_array_equal(translations,np.array([step[6*i:6*i+3] for i in nodes]))
        np.testing.assert_array_equal(shell_increment,step[owner.context.count:])
        assert kwargs['cancellation_token'] is token
        calls.append(1);token.cancel();return real(pose,translations,angular,shell_increment,**kwargs)
    work.certify_path=captured
    with pytest.raises(SolveCancelled):owner._swept_admissible(start,u,step,end,last,cancellation_token=token)
    assert calls==[1]
