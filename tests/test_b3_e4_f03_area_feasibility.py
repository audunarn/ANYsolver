"""One-use evidence failure paths, without executing scientific cases."""

import json
import hashlib
import subprocess
import sys
from pathlib import Path

import pytest
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import b3_e4_f03_area_feasibility as pilot


def _fake_registration(monkeypatch):
    registration={'identity':{'head':'test'},
                  'threads':{name:'1' for name in pilot.THREADS},
                  'cases':{'q4_coarse':{'topology':'Q4'}}}
    monkeypatch.setattr(pilot,'_registered',lambda root:registration)
    monkeypatch.setattr(pilot,'_registration_hash',lambda root:'frozen-digest')
    return registration


def test_spawn_failure_consumes_case_and_leaves_failure_receipt(tmp_path,monkeypatch):
    _fake_registration(monkeypatch)
    monkeypatch.setattr(pilot,'_clean',lambda:True)
    def cannot_spawn(*args,**kwargs):
        raise OSError('synthetic spawn failure')
    monkeypatch.setattr(pilot.subprocess,'Popen',cannot_spawn)
    assert not pilot.execute(tmp_path,'q4_coarse')
    receipt=json.loads((tmp_path/'q4_coarse'/'supervision.json').read_text())
    assert receipt['reason']=='supervisor_failure'
    assert receipt['exit_code'] is None
    assert 'synthetic spawn failure' in receipt['failure']
    with pytest.raises(FileExistsError):
        pilot.execute(tmp_path,'q4_coarse')


@pytest.mark.parametrize('raw_event',('[]','42'))
def test_non_object_child_event_leaves_failure_receipt(tmp_path,monkeypatch,raw_event):
    _fake_registration(monkeypatch)
    monkeypatch.setattr(pilot,'_clean',lambda:True)
    class FinishedChild:
        pid=123
        def poll(self):
            return 0
        def wait(self):
            return 0
    def finished_child(*args,stdout,**kwargs):
        stdout.write(raw_event+'\n')
        stdout.flush()
        return FinishedChild()
    monkeypatch.setattr(pilot.subprocess,'Popen',finished_child)
    monkeypatch.setattr(pilot.psutil,'Process',lambda pid:object())
    assert not pilot.execute(tmp_path,'q4_coarse')
    receipt=json.loads((tmp_path/'q4_coarse'/'supervision.json').read_text())
    assert receipt['reason']=='supervisor_failure'
    assert receipt['phases']==[]
    assert 'non-object child event' in receipt['failure']


def test_adjudication_requires_all_case_receipts_before_consuming_name(
        tmp_path,monkeypatch):
    _fake_registration(monkeypatch)
    with pytest.raises(ValueError,match='all registered case receipts'):
        pilot.adjudicate(tmp_path)
    assert not (tmp_path/'adjudication.json').exists()


def test_corrupted_child_record_fails_independent_adjudication(
        tmp_path,monkeypatch):
    _fake_registration(monkeypatch)
    case=tmp_path/'q4_coarse'
    case.mkdir()
    (case/'supervision.json').write_text(json.dumps({
        'reason':'completed','exit_code':0,'elapsed_seconds':1.,
        'sampled_peak_rss_bytes':1234,'phases':['identity','observables'],
        'registration_sha256':'frozen-digest','observables_sha256':'bogus'}))
    (case/'stdout.jsonl').write_text('{broken json\n')
    (case/'observables.json').write_text('{}')
    assert not pilot.adjudicate(tmp_path)
    decision=json.loads((tmp_path/'adjudication.json').read_text())
    assert decision['cases']['q4_coarse']['status']=='FAILED_EVIDENCE'


@pytest.mark.parametrize('expected_parity', (None,'matching','intentionally-wrong-hash'))
def test_valid_raw_balance_and_energy_reach_a_final_decision(
        tmp_path,monkeypatch,expected_parity):
    registration=_fake_registration(monkeypatch)
    case=tmp_path/'q4_coarse'
    case.mkdir()
    values={'topology':'Q4','law':'P1','loading':'smooth',
            'halfwidth_m':.05,'shell_energy_j':1.,'beam_energy_j':1.,
            'interface_work_j':0.,'external_work_j':4.,'energy_scaled':0.,
            'free_residual_scaled':0.,'weak_gap_scaled':0.,
            'balance_scaled':[0.,0.,0.],
            'support_wrenches':[[0.,0.,0.],
                                [0.,-1e6,-5e5],[0.,0.,0.]],
            'beam_root_elastic_wrench':[0.,0.,0.],
            'beam_root_port_wrench':[0.,0.,0.],
            'beam_root_load_wrench':[0.,0.,0.],
            'beam_port_quarter_wrenches':[[0.,0.,0.]]*4}
    raw=json.dumps(values).encode()
    (case/'observables.json').write_bytes(raw)
    digest=hashlib.sha256(raw).hexdigest()
    if expected_parity is not None:
        registration['parity_reference']={
            'q4_coarse':digest if expected_parity=='matching' else expected_parity}
    events=[{'phase':'identity','case':'q4_coarse',
             'identity':registration['identity'],
             'registration_sha256':'frozen-digest','threadpools':[]},
            {'phase':'observables','case':'q4_coarse','sha256':digest}]
    (case/'stdout.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in events))
    (case/'supervision.json').write_text(json.dumps({
        'reason':'completed','exit_code':0,'elapsed_seconds':1.,
        'sampled_peak_rss_bytes':1234,'phases':['identity','observables'],
        'registration_sha256':'frozen-digest','observables_sha256':digest}))
    success=expected_parity in (None,'matching')
    assert pilot.adjudicate(tmp_path)==success
    decision=json.loads((tmp_path/'adjudication.json').read_text())
    assert decision['cases']['q4_coarse']['status']==(
        'PASSED_ALGEBRAIC_SCREEN' if success
        else 'FAILED_BASELINE_PARITY')


def test_solved_state_event_validates_binary_payload_before_hashing(tmp_path):
    (tmp_path/'observables.json').write_text('{}')
    spec={'n_s':2,'n_y':4,'n_beam':4,'n_mortar':2}
    path=tmp_path/'solved_state.npz'
    q=np.zeros(2*5*5+6*4+4)
    lam=np.zeros(9)
    np.savez_compressed(path,physical_q=q,physical_lambda=lam)
    event=pilot._observable_event(tmp_path,'test',spec,True)
    assert event['state_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    lam[0]=np.nan
    np.savez_compressed(path,physical_q=q,physical_lambda=lam)
    with pytest.raises(ValueError,match='solved-state shape, type or finite'):
        pilot._observable_event(tmp_path,'test',spec,True)


def test_axis_runner_inventory_and_child_source_binding():
    code=("import json,sys; sys.path.insert(0,'scripts'); "
          "import b3_e4_f03_area_axis_refinement as axis; p=axis.pilot; "
          "print(json.dumps({'cases':p.CASES,'runner':p.RUNNER.name,"
          "'sources':[x.name for x in p.SOURCES],"
          "'parity':p.PARITY_REFERENCE,'capture':p.CAPTURE_STATE}))")
    root=Path(__file__).resolve().parents[1]
    result=json.loads(subprocess.check_output((sys.executable,'-c',code),
                                              cwd=root,text=True))
    assert len(result['cases'])==18
    assert result['runner']=='b3_e4_f03_area_axis_refinement.py'
    assert result['sources'][:2]==[
        'b3_e4_f03_area_axis_refinement.py','b3_e4_f03_area_feasibility.py']
    assert len(result['sources'])==len(set(result['sources']))==9
    assert set(result['parity'])=={'q4_baseline','cst_cb_baseline'}
    assert result['capture'] is True
    for prefix,topology in (('q4','Q4'),('cst_cb','CST-CB')):
        cases={name.removeprefix(prefix+'_'):tuple(spec[1:])
               for name,spec in result['cases'].items() if spec[0]==topology}
        assert set(cases)=={
            'baseline','shell_x_low','shell_x_high',
            'shell_y_low','shell_y_high','beam_low','beam_high',
            'mortar_low','mortar_high'}
        assert len(set(cases.values()))==9
        baseline=cases['baseline']
        assert baseline==(8,16,16,8)
        for name,mesh in cases.items():
            assert name=='baseline' or sum(a!=b for a,b in zip(mesh,baseline))==1
