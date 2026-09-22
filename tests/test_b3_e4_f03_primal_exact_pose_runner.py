"""Synthetic source/evidence tests; never open a frozen solved-state archive."""

import json
import platform
import sys
import types
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import b3_e4_f03_primal_exact_pose as runner
import _b3_e4_f03_primal_checks as original_checks
import _b3_e4_f03_primal_exact_checks as actual_exact_checks


def fake_audit(tmp_path,monkeypatch):
    audit=tmp_path/'audit';audit.mkdir()
    source_map={'scripts/b3_e4_f03_primal_saved_audit.py':runner.original.sha(
        runner.ROOT/'scripts/b3_e4_f03_primal_saved_audit.py')}
    registration={'identity':{'head':runner.AUDIT_HEAD,
        'dependencies':runner.supervisor._versions(),
        'python':sys.version,'executable':str(Path(sys.executable).resolve()),
        'platform':platform.platform(),'machine':platform.machine(),
        'sources':source_map},'cases':runner.original.CASES,
        'threads':{k:'1' for k in runner.supervisor.THREADS}}
    (audit/'registration.json').write_text(json.dumps(registration))
    reg_sha=runner.original.sha(audit/'registration.json')
    (audit/'adjudication.json').write_text(json.dumps({
        'registration_sha256':reg_sha,'status':'FAILED_NUMERICAL_SCREEN',
        'audit_integrity':'PASSED','original_terminal':'FAILED_EVIDENCE',
        'cases':{name:{'original_decision':{'status':'FAILED_EVIDENCE'},
            'status':'PASSED_NUMERICAL_SCREEN',
            'reproduced_decision':{'status':'PASSED_NUMERICAL_SCREEN'},
            'parent_arrays_sha256':'synthetic'}
            for name in runner.original.CASES}}))
    for relative in runner.expected_audit_files()-{
            'registration.json','adjudication.json'}:
        file=audit/relative;file.parent.mkdir(parents=True,exist_ok=True)
        file.write_bytes(f'synthetic:{relative}'.encode())
    inventory={'scope':'mock','files':{
        relative:runner.original.sha(audit/relative)
        for relative in runner.expected_audit_files()}}
    (audit/'completed_artifacts.json').write_text(json.dumps(inventory))
    monkeypatch.setattr(runner,'AUDIT',audit)
    monkeypatch.setattr(runner,'AUDIT_COMPLETE_SHA',runner.original.sha(
        audit/'completed_artifacts.json'))
    monkeypatch.setattr(runner,'AUDIT_REGISTRATION_SHA',reg_sha)
    monkeypatch.setattr(runner,'AUDIT_ADJUDICATION_SHA',inventory['files'][
        'adjudication.json'])
    monkeypatch.setattr(runner,'AUDIT_REVIEW_SHA',inventory['files'][
        'independent_review.json'])
    return audit,inventory


def test_32_artifacts_complete_digest_and_duplicate_json(tmp_path,monkeypatch):
    audit,inventory=fake_audit(tmp_path,monkeypatch)
    bound=runner.audit_inventory()
    assert bound['artifact_hashes']==inventory['files']
    assert len(bound['artifact_hashes'])==32
    (audit/'n08/stdout.jsonl').write_text('tamper')
    with pytest.raises(ValueError,match='artifact changed'):
        runner.audit_inventory()
    (audit/'n08/stdout.jsonl').write_text('synthetic:n08/stdout.jsonl')
    (audit/'extra').mkdir()
    with pytest.raises(ValueError,match='on-disk inventory'):
        runner.audit_inventory()
    duplicate=tmp_path/'duplicate.json';duplicate.write_text('{"a":1,"a":2}')
    with pytest.raises(ValueError,match='duplicate'):
        runner._strict_json(duplicate)


def fake_checker(monkeypatch,calls):
    module=types.ModuleType('_b3_e4_f03_primal_exact_checks')
    def evaluate(n,arrays,decision):
        calls.append(('evaluate',n))
        with pytest.raises(AssertionError,match='forbids'):
            original_checks.verify_saved(None,n)
        with pytest.raises(AssertionError,match='forbids'):
            runner.original.verify_case(None,None,None)
        return {'diagnostic_status':'PASSED_REPRESENTATION_DIAGNOSTIC',
                'rational':['1','2'],'signed':.5}
    def verify(record,n,arrays,decision):
        calls.append(('verify',n))
        if record!={'diagnostic_status':'PASSED_REPRESENTATION_DIAGNOSTIC',
                    'rational':['1','2'],'signed':.5}:
            raise ValueError('changed synthetic exact record')
        return record.copy()
    module.evaluate_saved=evaluate
    module.verify_saved_record=verify
    module._identical=actual_exact_checks._identical
    monkeypatch.setitem(sys.modules,module.__name__,module)


def test_saved_only_envelope_and_readback_verifier_without_reevaluate(
        tmp_path,monkeypatch,capsys):
    fake_audit(tmp_path,monkeypatch)
    root=tmp_path/'new';monkeypatch.setattr(runner,'TARGET',root)
    monkeypatch.setattr(runner.supervisor,'_clean',lambda:True)
    monkeypatch.setattr(runner.supervisor,'_identity',lambda:{'mock':'identity'})
    monkeypatch.setattr(runner.saved,'parent_inventory',lambda:{
        'registration_sha256':'oldreg','artifact_hashes':{
            'n12/arrays.npz':'synthetic'}})
    runner.register(root);manifest=runner.registered(root)
    assert set(manifest['cases'])=={'n12','n16','n24'}
    assert manifest['limits']['seconds_per_case']==300
    assert manifest['limits']['rss_bytes_per_case']==1024**3
    assert manifest['limits']['launch_cutoff_seconds']==1200
    monkeypatch.setattr(runner,'_original_arrays',lambda name,m:{
        'q':np.zeros(2*(12*12-1),dtype=np.float64)})
    monkeypatch.setattr(runner,'_audit_decision',lambda name,m:{
        'status':'PASSED_NUMERICAL_SCREEN',
        'original_decision':{'status':'FAILED_EVIDENCE'},
        'parent_arrays_sha256':'synthetic',
        'reproduced_decision':{'status':'PASSED_NUMERICAL_SCREEN',
                               'inherited_metric':1.0}})
    calls=[];fake_checker(monkeypatch,calls)
    import threadpoolctl
    monkeypatch.setattr(threadpoolctl,'threadpool_info',lambda:[{'num_threads':1}])
    for key in runner.supervisor.THREADS: monkeypatch.setenv(key,'1')
    directory=root/'n12';directory.mkdir()
    runner.child(root,'n12')
    lines=capsys.readouterr().out.splitlines()
    assert len(lines)==2
    (directory/'stdout.jsonl').write_text('\n'.join(lines)+'\n')
    event=json.loads(lines[1])
    receipt={'reason':'completed','exit_code':0,'elapsed_seconds':.5,
        'sampled_peak_rss_bytes':4096,'phases':['identity','observables'],
        'registration_sha256':runner.supervisor._registration_hash(root),
        'failure':None,'observables_sha256':event['sha256']}
    (directory/'supervision.json').write_text(json.dumps(receipt))
    result=runner.verify_case(root,'n12',manifest)
    assert result['status']=='PASSED_REPRESENTATION_DIAGNOSTIC'
    assert calls==[('evaluate',12),('verify',12),('verify',12)]
    observed=runner._strict_json(directory/'observables.json')
    assert all(value==0 for value in observed['work'].values())
    assert observed['original_decision']['status']=='FAILED_EVIDENCE'
    observed['saved_audit_decision']['reproduced_decision'][
        'inherited_metric']=1.+5e-13
    (directory/'observables.json').write_text(json.dumps(observed))
    altered_event=runner.observable_event(directory,'n12',runner.CASES['n12'],False)
    (directory/'stdout.jsonl').write_text(lines[0]+'\n'+
        json.dumps(altered_event)+'\n')
    receipt['observables_sha256']=altered_event['sha256']
    (directory/'supervision.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='floating value changed'):
        runner.verify_case(root,'n12',manifest)
    with pytest.raises(FileExistsError): runner.child(root,'n12')
    lines[0]=json.loads(lines[0]);lines[0]['threadpools'][0]['num_threads']=True
    (directory/'stdout.jsonl').write_text(json.dumps(lines[0])+'\n'+lines[1]+'\n')
    with pytest.raises(ValueError,match='child identity'):
        runner.verify_case(root,'n12',manifest)


def test_malformed_resources_and_true_partial_failure(tmp_path,monkeypatch):
    root=tmp_path/'new';directory=root/'n12';directory.mkdir(parents=True)
    monkeypatch.setattr(runner.supervisor,'_registration_hash',lambda path:'reg')
    receipt={'reason':'time_limit','exit_code':-9,
        'elapsed_seconds':runner.MAX_SECONDS+2,
        'sampled_peak_rss_bytes':runner.MAX_RSS_BYTES+1,
        'phases':[],'registration_sha256':'reg',
        'failure':None,'observables_sha256':None}
    (directory/'supervision.json').write_text(json.dumps(receipt))
    assert runner.verify_case(root,'n12',{})['status']=='FAILED_EXECUTION'
    for field,value in (('elapsed_seconds',True),('sampled_peak_rss_bytes',False),
                        ('exit_code',True),('elapsed_seconds',float('nan'))):
        changed=receipt.copy();changed[field]=value
        (directory/'supervision.json').write_text(json.dumps(changed))
        with pytest.raises(ValueError,match='resource receipt|nonfinite JSON token'):
            runner.verify_case(root,'n12',{})
    receipt['reason']='completed';receipt['exit_code']=0
    (directory/'supervision.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='contradictory completed'):
        runner.verify_case(root,'n12',{})


def test_terminal_precedence_preserves_both_parent_failures(tmp_path,monkeypatch):
    root=tmp_path/'new';root.mkdir()
    for name in runner.CASES:
        (root/name).mkdir();(root/name/'supervision.json').write_text('{}')
    monkeypatch.setattr(runner,'registered',lambda root:{'identity':{'mock':1}})
    monkeypatch.setattr(runner.supervisor,'_registration_hash',lambda root:'reg')
    results={'n12':'PASSED_REPRESENTATION_DIAGNOSTIC',
             'n16':'FAILED_DIAGNOSTIC_IDENTITY',
             'n24':'PASSED_REPRESENTATION_DIAGNOSTIC'}
    monkeypatch.setattr(runner,'verify_case',lambda root,name,manifest:{
        'status':results[name]})
    assert runner.adjudicate(root) is False
    decision=runner._strict_json(root/'adjudication.json')
    assert decision['status']=='FAILED_DIAGNOSTIC_IDENTITY'
    assert decision['original_terminal']=='FAILED_EVIDENCE'
    assert decision['saved_audit_terminal']=='FAILED_NUMERICAL_SCREEN'
    assert all(value==0 for value in decision['work'].values())


def test_unexpected_assertion_propagates_without_canonical_adjudication(
        tmp_path,monkeypatch):
    root=tmp_path/'new';root.mkdir()
    for name in runner.CASES:
        (root/name).mkdir();(root/name/'supervision.json').write_text('{}')
    monkeypatch.setattr(runner,'registered',lambda root:{'identity':{'mock':1}})
    def unexpected(*args,**kwargs):
        raise AssertionError('programmer or ownership error')
    monkeypatch.setattr(runner,'verify_case',unexpected)
    with pytest.raises(AssertionError,match='programmer or ownership error'):
        runner.adjudicate(root)
    assert not (root/'adjudication.json').exists()
