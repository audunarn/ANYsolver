"""Pure-norm evidence guards without executing the registered study."""

import json
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import b3_e4_f03_analytical_norm_study as study


def test_inventory_limits_and_scope_are_fixed():
    assert study.COUNTS==(4,8,16)
    assert study.FAMILIES==('P1','hybrid','enriched')
    assert study.RESOURCES=={'seconds':120,'sampled_rss_bytes':512*1024**2}
    assert study.LIMITS['relative_operator_error']==1e-9
    assert all(path.exists() for path in study.SOURCES)


def test_failed_child_does_not_require_complete_output(tmp_path,monkeypatch):
    monkeypatch.setattr(study,'checked_registration',lambda root:({},'digest'))
    receipt={'reason':'time_limit','exit_code':1,'failure':None,
             'registration_sha256':'digest','elapsed_seconds':121.,'sampled_peak_rss_bytes':1000}
    study.write_new(tmp_path/'supervision.json',receipt)
    assert not study.adjudicate(tmp_path,receipt)
    assert json.loads((tmp_path/'adjudication.json').read_text())=={
        'status':'FAILED_EXECUTION','supervision':receipt}


def test_duplicate_evidence_write_is_rejected(tmp_path):
    path=tmp_path/'evidence.json'
    study.write_new(path,{'first':1})
    with pytest.raises(FileExistsError):
        study.write_new(path,{'replacement':2})
    assert json.loads(path.read_text())=={'first':1}


def test_gram_inventory_and_nonfinite_data_are_rejected(tmp_path):
    path=tmp_path/'grams.npz'
    np.savez(path,unexpected=np.eye(7))
    with pytest.raises(ValueError,match='inventory'):
        study.verify_grams(path,4)
    grams={'green12_enriched':np.eye(7),'green16_enriched':np.eye(7)}
    grams.update({family+suffix:np.eye(7 if family=='enriched' else 5)
                  for family in study.FAMILIES for suffix in ('_analytic','_fe32','_fe64')})
    np.savez(path,**grams)
    study.verify_grams(path,4)
    grams['P1_analytic'][0,0]=np.nan
    np.savez(path,**grams)
    with pytest.raises(ValueError,match='layout or values'):
        study.verify_grams(path,4)


@pytest.mark.parametrize('field,value',(
    ('elapsed_seconds',121.),('elapsed_seconds',float('nan')),
    ('sampled_peak_rss_bytes',513*1024**2),('registration_sha256','other')))
def test_unbound_or_over_budget_success_receipt_is_rejected(tmp_path,monkeypatch,field,value):
    monkeypatch.setattr(study,'checked_registration',lambda root:({},'digest'))
    receipt={'reason':'completed','exit_code':0,'failure':None,
             'registration_sha256':'digest','elapsed_seconds':1.,'sampled_peak_rss_bytes':1000}
    receipt[field]=value
    # Explicit JSON NaN exercises validation of a malformed external receipt.
    (tmp_path/'supervision.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='receipt'):
        study.adjudicate(tmp_path,receipt)
    assert not (tmp_path/'adjudication.json').exists()


def test_repeated_child_is_rejected_before_any_norm_computation(tmp_path,monkeypatch):
    monkeypatch.setattr(study,'checked_registration',lambda root:({},'digest'))
    for name in study.THREADS:
        monkeypatch.setenv(name,'1')
    study.write_new(tmp_path/'child_started.json',{'already':'consumed'})
    with pytest.raises(FileExistsError):
        study.child(tmp_path)


def test_saved_matrix_error_is_recomputed_not_taken_from_a_status_label():
    n=4;canonical=np.eye(n+3)
    grams={'green12_enriched':canonical,'green16_enriched':canonical,
           'P1_analytic':np.eye(n+1),'hybrid_analytic':np.eye(n+1),
           'enriched_analytic':canonical.copy()}
    grams['P1_analytic'][0,0]=1.1
    assert study.saved_metrics(n,grams)['P1']['relative_operator_error']==pytest.approx(.1)


def test_supervisor_requires_thread_caps_before_registration(tmp_path,monkeypatch):
    monkeypatch.delenv('OMP_NUM_THREADS',raising=False)
    with pytest.raises(ValueError,match='supervisor environment'):
        study.run(tmp_path/'unused')
    assert not (tmp_path/'unused').exists()
