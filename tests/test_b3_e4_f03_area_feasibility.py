"""One-use evidence failure paths, without executing scientific cases."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import b3_e4_f03_area_feasibility as pilot


def _fake_registration(monkeypatch):
    registration={'identity':{'head':'test'},
                  'threads':{name:'1' for name in pilot.THREADS},
                  'cases':{'q4_coarse':pilot.CASES['q4_coarse']}}
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
