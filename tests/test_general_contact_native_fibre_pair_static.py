"""Physical-fibre work/history in the retained whole-curve beam-pair owner."""
from pathlib import Path
from hashlib import sha256
import json,os,runpy
import numpy as np
import pytest
from anysolver._ge_beam3_p5_seeded.core import canonical
from anysolver.control import CancellationToken
from anysolver.general_contact.native_retained_pair_static import FIBRE_WHOLE_PROFILE
from test_general_contact_native_fibre_s3 import _independent_material_history


def _owner(*,plastic=True,targets=(.05,),force=-.05,separation=.101):
    builder=runpy.run_path(str(Path(__file__).parents[1]/'examples/general_contact_native_retained_whole_pair.py'))['analysis']
    return builder(physical_fibres=True,plastic_fibres=plastic,targets=targets,force=force,
        separation=separation,gap_tolerance_m=5e-5)


def test_fibre_pair_context_step_complete_constrained_rank_one_reference():
    owner=_owner();c=owner.context;assert c.count==84
    d=np.arange(1,c.count+1,dtype=float);v=np.linspace(-.2,.3,c.count);r=np.linspace(.1,-.1,c.count)
    j=np.diag(d)+np.outer(v,v);free=np.array(c.free)
    expected=np.zeros(c.count);df=d[free];vf=v[free];rf=r[free]
    expected[free]=-rf/df+(vf/df)*(np.sum(vf*rf/df)/(1+np.sum(vf*vf/df)))
    step,correction=c.step(owner.initial.mechanical,r,j)
    np.testing.assert_allclose(step,expected,rtol=1e-13,atol=1e-15)
    assert correction>0. and np.count_nonzero(step[c.nodal_count:])==48
    assert owner.profile==FIBRE_WHOLE_PROFILE


def test_fibre_pair_family_binding_and_empty_restart():
    from test_general_contact_native_retained_whole_pair_static import _owner as generalized
    physical=_owner();elastic=_owner(plastic=False)
    assert physical.identity!=elastic.identity
    raw=physical._checkpoint(())
    for other in (elastic,generalized(targets=(.05,),separation=.101,force=-.05)):
        with pytest.raises(ValueError,match='binding'):other._restore(raw,sha256(raw).hexdigest())
    state,records=physical._restore(raw,sha256(raw).hexdigest())
    assert state.completed_targets==0 and physical._checkpoint(records)==raw


def test_fibre_pair_cancellation_and_precommit_exception_restore_origin(monkeypatch):
    owner=_owner();raw=owner._checkpoint(());origin=canonical(owner.initial.histories)
    token=CancellationToken();token.cancel('fibre-pair focused cancellation')
    failed=owner.solve(cancellation_token=token)
    assert failed.status=='failed' and 'SolveCancelled' in failed.failure
    assert failed.checkpoint==raw and canonical(failed.accepted.histories)==origin
    assert owner.context._token is None and not owner.context._lock.locked() and not owner.context._cancel_active
    owner=_owner(targets=(0.,));raw=owner._checkpoint(())
    def reject(*args,**kwargs):raise RuntimeError('fibre pair precommit interruption')
    monkeypatch.setattr(owner,'_record',reject)
    failed=owner.solve()
    assert failed.status=='failed' and 'precommit interruption' in failed.failure
    assert failed.checkpoint==raw and failed.accepted.completed_targets==0
    assert owner.context._token is None and not owner.context._lock.locked()


def test_fibre_pair_cancellation_after_checkpoint_staging_restores_origin(monkeypatch):
    owner=_owner(targets=(0.,));raw=owner._checkpoint(())
    origin=canonical(owner.initial.histories)
    token=CancellationToken();checkpoint=owner._checkpoint
    def stage_then_cancel(records):
        staged=checkpoint(records)
        if records:token.cancel('after staged fibre target')
        return staged
    monkeypatch.setattr(owner,'_checkpoint',stage_then_cancel)
    failed=owner.solve(cancellation_token=token)
    assert failed.status=='failed' and 'SolveCancelled' in failed.failure
    assert failed.checkpoint==raw and failed.accepted.completed_targets==0
    assert canonical(failed.accepted.histories)==origin
    assert owner.context._token is None and not owner.context._lock.locked() and not owner.context._cancel_active


def test_fibre_pair_complete_spatial_tangent_and_independent_material_trial():
    owner=_owner();c=owner.context
    step=np.zeros(c.count)
    step[6*c.node_ids.index(5)+1]=-.0008
    step[6*c.node_ids.index(6)+1]=-.002
    for slots in c.slots:step[np.asarray(slots)[24:42]]=np.linspace(-.001,.001,18)
    state=c.advance(owner.initial.mechanical,step);origins=owner.initial.histories
    before=canonical(origins)
    r,k,_,responses,contact=owner._assemble(state,.05,origins)
    assert contact.potential_j>0. and np.count_nonzero(contact.tangent[:42,42:])
    report,proposed=_independent_material_history(owner,state,origins)
    assert report['yielded']>0. and proposed==tuple(station for response in responses for station in response.history.stations)
    direction=np.random.default_rng(721).normal(size=c.count)*1e-4
    direction[list(c._backend.layout.fixed)]=0.
    errors=[]
    for h in (2e-6,1e-6):
        values=[owner._assemble(c.advance(state,sign*h*direction),.05,origins)[0] for sign in (1,-1)]
        fd=(values[0]-values[1])/(2*h);error=float(np.linalg.norm(k@direction-fd)/np.linalg.norm(fd));errors.append(error)
        assert error<=1e-5
    assert canonical(origins)==before
    record=os.environ.get('CONTACT_APP_RESULT_RECORD')
    if record:Path(record+'-fibre-pair-local.json').write_text(json.dumps(dict(
        material=report,directional_errors=errors,energy_j=contact.potential_j),indent=2))


def test_fibre_pair_actual_coupled_commit_and_restart():
    owner=_owner();origins=owner.initial.histories;before=canonical(origins)
    run=owner.solve();output=os.environ.get('CONTACT_APP_RESULT_RECORD')
    record=dict(status=run.status,failure=run.failure,completed=run.accepted.completed_targets,profile=run.profile)
    if output:
        Path(output+'-fibre-pair.json').write_text(json.dumps(record,indent=2))
        Path(output+'-fibre-pair.checkpoint').write_bytes(run.checkpoint)
    assert run.status=='completed' and run.accepted.completed_targets==1,run.failure
    contact=run.accepted.contact
    assert contact.potential_j>0. and contact.conservative_lower_gap_m>=-5e-5
    assert np.linalg.norm(contact.beam_a_force_n+contact.beam_b_force_n)/.0025<=1e-6
    assert np.linalg.norm(contact.beam_a_moment_nm+contact.beam_b_moment_nm)/.005<=1e-6
    material,proposed=_independent_material_history(owner,run.accepted.mechanical,origins)
    assert material['yielded']>0. and proposed==tuple(station for cell in run.accepted.histories for station in cell.stations)
    assert canonical(origins)==before
    restored,records=_owner()._restore(run.checkpoint,run.checkpoint_sha256)
    assert restored.histories==run.accepted.histories and owner._checkpoint(records)==run.checkpoint
    assert owner.context._token is None and not owner.context._lock.locked()
    if output:
        record.update(material=material,gap_lower_m=contact.conservative_lower_gap_m,
            checkpoint_sha256=run.checkpoint_sha256,force_a_n=contact.beam_a_force_n.tolist())
        Path(output+'-fibre-pair.json').write_text(json.dumps(record,indent=2))
