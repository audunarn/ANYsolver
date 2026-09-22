"""One-use evidence failure paths, without executing scientific cases."""

import json
import hashlib
import sys
from pathlib import Path

import pytest

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


def test_valid_raw_balance_and_energy_reach_a_final_decision(tmp_path,monkeypatch):
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
    events=[{'phase':'identity','case':'q4_coarse',
             'identity':registration['identity'],
             'registration_sha256':'frozen-digest','threadpools':[]},
            {'phase':'observables','case':'q4_coarse','sha256':digest}]
    (case/'stdout.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in events))
    (case/'supervision.json').write_text(json.dumps({
        'reason':'completed','exit_code':0,'elapsed_seconds':1.,
        'sampled_peak_rss_bytes':1234,'phases':['identity','observables'],
        'registration_sha256':'frozen-digest','observables_sha256':digest}))
    assert pilot.adjudicate(tmp_path)
    decision=json.loads((tmp_path/'adjudication.json').read_text())
    assert decision['cases']['q4_coarse']['status']=='PASSED_ALGEBRAIC_SCREEN'
