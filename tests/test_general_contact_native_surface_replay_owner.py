"""Opt-in replay integration through the actual retained native/S3 owner."""
from dataclasses import replace
from hashlib import sha256

import numpy as np
import pytest

from anysolver.general_contact.native_surface_transaction import NativeS3MaterialTransaction
from test_general_contact_native_surface_patch import _patch
from test_general_contact_native_surface_normal import _settings as normal_settings
from test_general_contact_native_surface_friction_integral import _settings as friction_settings


def _replay_patch():
    return _patch(activation_policy='transverse_events',gap_check='straight_patch',
        normal_integration='straight_segmented',normal_integration_settings=normal_settings(),
        friction_integration='replay',friction_integration_settings=friction_settings())


def test_replay_initialization_rejected_trial_and_checkpoint_identity():
    owner,bridge=_replay_patch();transaction=NativeS3MaterialTransaction(bridge)
    before=transaction.checkpoint();history=transaction.accepted.friction_history
    assert len(history.segments)==0
    proposal=transaction.propose(np.zeros(42),np.zeros(18),1.)
    assert len(proposal.assembly.material.contribution.trial.candidate_state.segments)==0
    assert proposal.assembly.material.contribution.friction_integral.diagnostics['queries']==0
    with pytest.raises(ValueError,match='equilibrium'):
        transaction.commit(proposal)
    assert transaction.checkpoint()==before
    delta=np.zeros(42);delta[18]=np.pi
    with pytest.raises(ValueError,match='requires cutback'):
        transaction.propose(delta,np.zeros(18),1.)
    assert transaction.checkpoint()==before
    foreign=replace(history,maximum_intervals=history.maximum_intervals+1)
    with pytest.raises(ValueError,match='interval binding'):
        bridge.evaluate(transaction.accepted,foreign,np.zeros(42),np.zeros(18),0.)
    restored=NativeS3MaterialTransaction.restore(bridge,before,sha256(before).hexdigest())
    assert restored.checkpoint()==before
    _,other=_patch(activation_policy='transverse_events',gap_check='straight_patch',
        normal_integration='straight_segmented',normal_integration_settings=normal_settings())
    with pytest.raises(ValueError,match='definition/settings'):
        NativeS3MaterialTransaction.restore(other,before,sha256(before).hexdigest())


@pytest.mark.parametrize('reason',[
    'native friction integration requires resolved historical contact envelope',
    'native friction integration requires swept whole-patch target ownership'])
def test_replay_geometry_rejection_backtracks_without_commit(monkeypatch,reason):
    owner,bridge=_replay_patch();transaction=NativeS3MaterialTransaction(bridge)
    before=transaction.checkpoint();original=transaction.propose;calls=0
    def rejected_once(*args,**kwargs):
        nonlocal calls
        calls+=1
        if calls==2:
            assert transaction.checkpoint()==before
            raise ValueError(reason)
        if calls==3:assert transaction.checkpoint()==before
        return original(*args,**kwargs)
    monkeypatch.setattr(transaction,'propose',rejected_once)
    owner.solve_material_increment(transaction,.001)
    assert calls>=3 and transaction.accepted.sequence==1


def test_replay_unexpected_trial_error_remains_fatal(monkeypatch):
    owner,bridge=_replay_patch();transaction=NativeS3MaterialTransaction(bridge)
    before=transaction.checkpoint();original=transaction.propose;calls=0
    def unexpected(*args,**kwargs):
        nonlocal calls
        calls+=1
        if calls==2:raise ValueError('unexpected replay defect')
        return original(*args,**kwargs)
    monkeypatch.setattr(transaction,'propose',unexpected)
    with pytest.raises(ValueError,match='unexpected replay defect'):
        owner.solve_material_increment(transaction,.001)
    assert transaction.checkpoint()==before


def test_material_newton_reuses_exact_candidate_but_rechecks_commit(monkeypatch):
    owner,bridge=_replay_patch();transaction=NativeS3MaterialTransaction(bridge)
    original_propose=transaction.propose;original_evaluate=bridge.evaluate
    proposed=[];evaluated=[]
    def key(native,shell,parameter):
        return (sha256(np.asarray(native).tobytes()+np.asarray(shell).tobytes()).hexdigest(),float(parameter))
    def propose(native,shell,parameter,**kwargs):
        proposed.append(key(native,shell,parameter))
        return original_propose(native,shell,parameter,**kwargs)
    def evaluate(origin,history,native,shell,parameter):
        evaluated.append(key(native,shell,parameter))
        return original_evaluate(origin,history,native,shell,parameter)
    monkeypatch.setattr(transaction,'propose',propose)
    monkeypatch.setattr(bridge,'evaluate',evaluate)
    owner.solve_material_increment(transaction,.001)
    assert len(proposed[:-1])==len(set(proposed[:-1]))
    # Commit alone repeats the final candidate's constitutive/contact work.
    assert proposed[-1]==proposed[-2]
    assert evaluated==proposed
    assert transaction.accepted.sequence==1


def test_replay_coupled_active_rebase_and_split_restart(monkeypatch):
    # Preserve a rejected integration path so subsequent diagnosis can replay
    # the local contribution without spending another structural solve.
    import json,os
    from dataclasses import asdict
    from pathlib import Path
    import anysolver.general_contact.native_surface_friction_integral as module
    original=module.integrate_material_friction
    calls=0
    def captured(field,settings):
        nonlocal calls
        calls+=1
        try:return original(field,settings)
        except (MemoryError,ValueError) as error:
            folder=os.environ.get('RUNNER_TEMP')
            if folder:
                payload=dict(calls=calls,error=str(error),initial=asdict(field.initial),
                    segments=[asdict(s) for s in field.segments],settings=asdict(settings),
                    definition=field.patch._definition(),maximum_intervals=field.maximum_intervals,
                    integration_diagnostics=getattr(error,'integration_diagnostics',None))
                Path(folder,'rejected_material_path.json').write_text(json.dumps(payload,
                    default=lambda value:value.tolist(),indent=2)+'\n')
            raise
    monkeypatch.setattr(module,'integrate_material_friction',captured)
    owner,bridge=_replay_patch();transaction=NativeS3MaterialTransaction(bridge)
    def stage(name):
        folder=os.environ.get('RUNNER_TEMP')
        if folder:
            Path(folder,'coupled_stage.json').write_text(json.dumps(dict(stage=name,
                accepted_sequence=transaction.accepted.sequence,integral_calls=calls))+'\n')
            if transaction.accepted.sequence:
                Path(folder,'accepted_material_checkpoint.json').write_bytes(transaction.checkpoint())
    stage('initial')
    owner.solve_material_increment(transaction,1.)
    stage('first_load_accepted')
    accepted=transaction.accepted
    assert len(accepted.friction_history.segments)==1
    same=transaction.propose(np.zeros(42),np.zeros(18),1.).assembly
    assert max(same.metrics)<owner.equilibrium_tolerance
    assert same.material.contribution.friction_integral.stored_energy_j>0
    assert same.material.contribution.friction_integral.dissipated_increment_j==0.
    assert same.material.contribution.friction_integral.diagnostics['queries']>0
    stage('committed_origin_rebased')
    capsule=transaction.checkpoint()
    owner.solve_material_increment(transaction,1.05)
    stage('uninterrupted_path_completed')
    # A real restart reconstructs its analysis; it does not reset the original
    # context's deadline. Each analysis retains its own unchanged120s guard.
    restarted_owner,restarted_bridge=_replay_patch()
    restored=NativeS3MaterialTransaction.restore(restarted_bridge,capsule,sha256(capsule).hexdigest())
    stage('active_checkpoint_restored')
    restarted_owner.solve_material_increment(restored,1.05)
    assert transaction.checkpoint()==restored.checkpoint()
    stage('split_restart_identical')


def test_saved_replay_candidate_branch_discriminator(tmp_path):
    """Small saved-pose diagnostic; does not repeat the coupled failure."""
    import json,os
    from pathlib import Path
    from anysolver.general_contact.native_surface_history import (
        NativeSurfaceHistoryField,NativeSurfaceMotionSegment,NativeSurfaceReplayBudget)
    from anysolver.general_contact.native_surface_s3_friction import NativeS3MaterialConfiguration
    path=Path(__file__).parents[1]/'docs/d1_review_support/contact_c5_native_surface_point_20261002/replay_owner_rejected_path.json'
    saved=json.loads(path.read_text())
    _,bridge=_replay_patch()
    initial=NativeS3MaterialConfiguration(**{k:np.asarray(v) for k,v in saved['initial'].items()})
    segments=tuple(NativeSurfaceMotionSegment(**{k:np.asarray(v) for k,v in s.items()}) for s in saved['segments'])
    field=NativeSurfaceHistoryField(bridge.pair,initial,segments,maximum_intervals=saved['maximum_intervals'])
    budget=NativeSurfaceReplayBudget(30);rows=[]
    for xi in (.79945,.7997,.79995):
        for angle in (3.48106,3.4812,3.48138):
            query=field.query(xi,angle,budget=budget);p=query.last_contribution
            rows.append(dict(xi=xi,angle=angle,gap=p.normal_gap_m,branch=p.trial.branch,
                pressure=p.normal_pressure_Pa,event_fraction=getattr(p,'event_fraction',None),
                friction_force=(p.residual-p.normal_residual).tolist(),
                tangent_norm=float(np.linalg.norm(p.spatial_tangent()-p.normal_spatial_tangent()))))
    output=Path(os.environ.get('RUNNER_TEMP',str(tmp_path)))/'branch_discriminator.json'
    output.write_text(json.dumps(rows,indent=2)+'\n')
    assert len(rows)==9


@pytest.mark.parametrize('filename',[
    'replay_owner_rejected_path.json','replay_owner_support_rejected_path.json'])
def test_saved_replay_candidate_front_refinement(tmp_path,filename):
    import json,os
    from pathlib import Path
    from anysolver.general_contact.native_surface_history import NativeSurfaceHistoryField,NativeSurfaceMotionSegment
    from anysolver.general_contact.native_surface_s3_friction import NativeS3MaterialConfiguration
    from anysolver.general_contact.native_surface_friction_integral import integrate_material_friction
    saved=json.loads((Path(__file__).parents[1]/'docs/d1_review_support/contact_c5_native_surface_point_20261002'/filename).read_text())
    _,bridge=_replay_patch()
    field=NativeSurfaceHistoryField(bridge.pair,
        NativeS3MaterialConfiguration(**{k:np.asarray(v) for k,v in saved['initial'].items()}),
        tuple(NativeSurfaceMotionSegment(**{k:np.asarray(v) for k,v in s.items()}) for s in saved['segments']),
        maximum_intervals=saved['maximum_intervals'])
    output=Path(os.environ.get('RUNNER_TEMP',str(tmp_path)))/'saved_candidate_result.json'
    try:
        value=integrate_material_friction(field,friction_settings())
    except MemoryError as error:
        output.write_text(json.dumps(dict(error=str(error),diagnostics=getattr(error,'integration_diagnostics',None)),indent=2)+'\n')
        raise
    output.write_text(json.dumps(value.diagnostics,indent=2)+'\n')
    assert value.diagnostics['maximum_scaled_error_estimate']<=1.
    assert value.stored_energy_j>0
