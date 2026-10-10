"""Focused controls and one installed assessment; execution requires authority."""
from pathlib import Path
import json
import os
import pytest


def test_source_adopted_scale_and_complete_nonzeros():
    from scripts import r8_f06_paired_branch_assessment_dev as a
    candidate,prepared=a.load_candidate()
    original=a.domain.read_vector(a.domain.SAVED/'direction-and-row-map.npz','direction')
    scaled=a.scaled_from_original(original,candidate)
    assert scaled==candidate['direction'] and len(scaled)==132
    assert sum(x!=0 for x in scaled)==120 and prepared['nonzero_after']==120


def test_source_changed_scale_channel_and_metadata_refused():
    from copy import deepcopy
    from scripts import r8_f06_paired_branch_assessment_dev as a
    candidate,_=a.load_candidate();vector=a.domain.read_vector(a.domain.SAVED/'direction-and-row-map.npz','direction')
    for field,value in [('uniform_scale',a.SCALE*2),('h',[1e-4,1e-5,2e-6]),('direction',[0.]*132)]:
        changed=deepcopy(candidate);changed[field]=value
        with pytest.raises(ValueError):a.scaled_from_original(vector,changed)


def test_source_changed_candidate_bytes_refused(tmp_path):
    from scripts import r8_f06_paired_branch_assessment_dev as a
    path=tmp_path/'candidate-direction.json';path.write_bytes((a.PREP/'candidate-direction.json').read_bytes()+b' ')
    with pytest.raises(ValueError,match='changed candidate'):a.load_candidate(path)


def test_source_missing_branch_and_unexercised_work_refused():
    from scripts import r8_f06_paired_branch_assessment_dev as a
    good=dict(raw_action_norm=1.,work_action_norm=2.,exercised=True)
    report=dict(base_smooth=True,smooth_assessment_resolved=True,
        evaluations=[dict(h=h,branches_stable=True,groups={g:dict(good) for g in
            ('shell','beam','constraints','fibre_retained','generalized_retained')}) for h in a.original.STEPS],
        local_adjacent_plateau={'0':True},local_derivatives=[dict(metrics=dict(good)) for _ in range(3)])
    assert all(a.complete_metrics(report).values())
    del report['evaluations'][1]['branches_stable']
    assert not a.complete_metrics(report)['branches']
    report['evaluations'][1]['branches_stable']=True
    report['evaluations'][0]['groups']['constraints']['raw_action_norm']=0.
    assert not a.complete_metrics(report)['positive_groups']
    report['local_derivatives'][0]['metrics']['work_action_norm']=0.
    assert not a.complete_metrics(report)['positive_locals']


def test_source_override_refused_outside_installed_child(tmp_path,monkeypatch):
    from scripts import r8_f06_paired_branch_assessment_dev as a
    monkeypatch.delenv('F06_BRANCH_STAGE',raising=False)
    saved=a.original.frozen_direction
    with pytest.raises(ValueError,match='installed-child-only'):a.assess(tmp_path)
    assert a.original.frozen_direction is saved
    # Exercise the actual wrapper caller with a persisted-report writer which
    # deliberately returns None, and with a failure after partial persistence.
    good=dict(raw_action_norm=1.,work_action_norm=2.,exercised=True)
    report=dict(status='SCOPED_PASS',base_smooth=True,smooth_assessment_resolved=True,
        evaluations=[dict(h=h,branches_stable=True,groups={g:dict(good) for g in
            ('shell','beam','constraints','fibre_retained','generalized_retained')}) for h in a.original.STEPS],
        local_adjacent_plateau={'0':True},local_derivatives=[dict(metrics=dict(good)) for _ in range(3)])
    vector=a.domain.read_vector(a.domain.SAVED/'direction-and-row-map.npz','direction')
    def fake_direction(owner,residual):return vector
    monkeypatch.setattr(a.original,'frozen_direction',fake_direction)
    monkeypatch.setenv('F06_BRANCH_STAGE','installed-assessment')
    def writer(out):
        assert a.original.frozen_direction is not fake_direction
        assert a.original.frozen_direction(None,None).tolist()==[a.SCALE*x for x in vector]
        a.original.write(out/'assessment.json',report)
    monkeypatch.setattr(a.original,'assess',writer)
    result=a.assess(tmp_path)
    assert result['status']=='SCOPED_PASS' and all(result['complete_observations'].values())
    persisted=json.loads((tmp_path/'assessment.json').read_text())
    assert persisted['branch_direction_provenance']['uniform_scale']==a.SCALE
    assert a.original.frozen_direction is fake_direction
    def refusal(out):
        a.original.write(out/'assessment.json',{**report,'status':'UNRESOLVED_BRANCH','smooth_assessment_resolved':False})
        raise ValueError('actual saved branch refusal')
    monkeypatch.setattr(a.original,'assess',refusal)
    with pytest.raises(ValueError,match='actual saved branch refusal'):a.assess(tmp_path)
    persisted=json.loads((tmp_path/'assessment.json').read_text())
    assert persisted['status']=='UNRESOLVED_BRANCH' and not persisted['complete_observations']['branches']
    assert persisted['branch_direction_provenance']['candidate_sha256']==a.CANDIDATE_SHA
    assert a.original.frozen_direction is fake_direction


def test_installed_branch_domain_tangent():
    from scripts.r8_f06_paired_branch_assessment_dev import assess
    result=assess(Path(os.environ['F06_BRANCH_ASSESSMENT_OUTPUT']))
    assert result['status']=='SCOPED_PASS' and all(result['complete_observations'].values())
