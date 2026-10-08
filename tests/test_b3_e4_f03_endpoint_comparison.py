"""Evidence-contract and independent aggregate checks for the diagnostic runner."""

from pathlib import Path
import json
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import b3_e4_f03_endpoint_comparison as runner


def test_inventory_is_ten_geometries_with_frozen_parent_states():
    assert len(runner.CASES)==10
    assert set(runner.CASES)==set(runner.PARENT_STATES)
    assert {case[3:] for case in runner.CASES.values()}=={
        (16,4),(16,8),(16,16),(8,8),(32,8)}
    assert runner.FAMILIES==('P1','hybrid','enriched')
    assert all(case[1:3]==(8,16) for case in runner.CASES.values())


@pytest.fixture
def sample():
    spec={'topology':'Q4','n_s':2,'n_y':4,'n_beam':2,'n_mortar':2}
    data={'topology':'Q4','mesh':[2,4,2,2],'halfwidth_m':.05,
          'baseline_parity_ratio':0.,'enriched_energy_order_scaled':0.,'families':{}}
    for family in runner.FAMILIES:
        count=3*(2+(3 if family=='enriched' else 1))
        data['families'][family]={
            'shell_energy_j':.5,'beam_energy_j':.5,'interface_work_j':0.,
            'external_work_j':2.,'support_wrenches':[[0.,-1e6,-.5e6],[0.,0.,0.],[0.,0.,0.]],
            'root_elastic_wrench':[0.,0.,0.],'root_port_wrench':[0.,0.,0.],
            'root_load_wrench':[0.,0.,0.],'root_line_wrench':[0.,0.,0.],
            'root_endpoint_wrench':[0.,0.,0.],'balance_scaled':[0.,0.,0.],
            'energy_scaled':0.,'free_residual_scaled':0.,'weak_gap_scaled':0.,
            'stability':{'generalized_eigenvalues':list(np.linspace(.1,1.,count)),
                         'structural_solve_relative_residual':0.,
                         'auxiliary_squared_norm_change':1e-4}}
    return data,spec


def test_aggregate_check_uses_signed_work_and_support_balance(sample):
    data,spec=sample
    got=runner.measurements(data,spec)
    assert got['auxiliary_squared_norm_change']==1e-4
    assert got['energy_scaled']==0.


@pytest.mark.parametrize('mutation',('energy','root','endpoint','nan','spectrum','family'))
def test_contradictory_or_invalid_payload_is_rejected(sample,mutation):
    data,spec=sample
    row=data['families']['hybrid']
    if mutation=='energy':
        row['external_work_j']=3.
    elif mutation=='root':
        row['root_elastic_wrench'][1]=1.
    elif mutation=='endpoint':
        row['root_endpoint_wrench'][1]=1.
    elif mutation=='nan':
        row['free_residual_scaled']=float('nan')
    elif mutation=='spectrum':
        row['stability']['generalized_eigenvalues'].pop()
    else:
        del data['families']['enriched']
    with pytest.raises(ValueError):
        runner.measurements(data,spec)


def test_unresolved_auxiliary_value_cannot_be_hidden_by_a_status_label(sample):
    data,spec=sample
    data['families']['hybrid']['stability'].update(
        auxiliary_squared_norm_change=.01,auxiliary_status='RESOLVED_AT_REGISTERED_LEVELS')
    assert runner.measurements(data,spec)['auxiliary_squared_norm_change']>.001


def test_nonpositive_mode_is_a_diagnostic_failure_not_corrupted_evidence(sample):
    data,spec=sample
    data['families']['hybrid']['stability']['generalized_eigenvalues'][0]=-1e-12
    assert runner.measurements(data,spec)['nonpositive_schur_modes']==1


def test_snapshot_requires_complete_finite_owned_inventory(tmp_path,sample):
    _,spec=sample
    q_count=2*(2*spec['n_s']+1)*(spec['n_y']+1)+6*spec['n_beam']+4
    states={}
    for family in runner.FAMILIES:
        states[family+'_q']=np.zeros(q_count)
        states[family+'_lambda']=np.zeros(3*(2+(3 if family=='enriched' else 1)))
    path=tmp_path/'solved_state.npz'
    np.savez(path,**states)
    (tmp_path/'observables.json').write_text('{}')
    event=runner.observable_event(tmp_path,'case',spec,True)
    assert event['state_sha256']==runner.sha(path)
    states['hybrid_q'][0]=np.nan
    np.savez(path,**states)
    with pytest.raises(ValueError,match='state array'):
        runner.observable_event(tmp_path,'case',spec,True)


def test_changed_parent_snapshot_is_rejected(tmp_path,monkeypatch):
    (tmp_path/'registration.json').write_text('{}')
    directory=tmp_path/'case'; directory.mkdir()
    (directory/'solved_state.npz').write_bytes(b'changed')
    monkeypatch.setattr(runner,'PARENT',tmp_path)
    monkeypatch.setattr(runner,'PARENT_REGISTRATION',runner.sha(tmp_path/'registration.json'))
    monkeypatch.setattr(runner,'PARENT_STATES',{'case':'frozen different bytes'})
    with pytest.raises(ValueError,match='snapshot changed'):
        runner.parent_state('case')


def test_premature_adjudication_does_not_consume_canonical_output(tmp_path,monkeypatch):
    monkeypatch.setattr(runner.common,'_registered',lambda root:{'cases':{'pending':{}}})
    with pytest.raises(ValueError,match='complete supervisor inventory'):
        runner.adjudicate(tmp_path)
    assert not (tmp_path/'adjudication.json').exists()


def test_failed_child_keeps_supervisor_reason_without_final_snapshot(tmp_path,monkeypatch):
    directory=tmp_path/'case'; directory.mkdir()
    receipt={'reason':'time_limit','exit_code':1,'failure':None,
             'registration_sha256':'registered'}
    (directory/'supervision.json').write_text(json.dumps(receipt))
    monkeypatch.setattr(runner.common,'_registered',lambda root:{'cases':{'case':{}},'identity':{}})
    monkeypatch.setattr(runner.common,'_registration_hash',lambda root:'registered')
    assert not runner.adjudicate(tmp_path)
    case=json.loads((tmp_path/'adjudication.json').read_text())['cases']['case']
    assert case=={'status':'FAILED_EXECUTION','supervision':receipt}
