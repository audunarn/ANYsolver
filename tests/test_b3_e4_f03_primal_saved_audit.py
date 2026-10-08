"""Mock-only contracts for the one-use frozen saved-evidence audit."""

import json
import platform
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import b3_e4_f03_primal_saved_audit as audit
import _b3_e4_f03_primal_ritz as operators


def fake_parent(tmp_path,monkeypatch):
    """Tiny synthetic bytes with all 36 names; no frozen case is opened."""
    parent=tmp_path/'parent';parent.mkdir()
    registration={'identity':{'head':audit.PARENT_HEAD,
        'dependencies':audit.supervisor._versions(),
        'python':sys.version,'executable':str(Path(sys.executable).resolve()),
        'platform':platform.platform(),'machine':platform.machine(),
        'sources':{'scripts/b3_e4_f03_primal_ritz.py':
                   '572541996e74aa001c9a57f25662b3aab428299228e3823f9068a3f96c60a8ff',
                   'scripts/_b3_e4_f03_primal_ritz.py':audit.parent_runner.sha(
                        audit.ROOT/'scripts/_b3_e4_f03_primal_ritz.py')}},
        'threads':{k:'1' for k in audit.supervisor.THREADS},
        'cases':audit.CASES,
        'limits':{'numerical':__import__(
            '_b3_e4_f03_primal_checks').LIMITS}}
    (parent/'registration.json').write_text(json.dumps(registration))
    registration_sha=audit.parent_runner.sha(parent/'registration.json')
    (parent/'adjudication.json').write_text(json.dumps({
        'status':audit.ORIGINAL_TERMINAL,
        'registration_sha256':registration_sha,
        'cases':{k:{'status':audit.ORIGINAL_TERMINAL,
                    'reason':'original comparator failure'} for k in audit.CASES}}))
    adjud_sha=audit.parent_runner.sha(parent/'adjudication.json')
    for relative in audit.expected_parent_files()-{
            'registration.json','adjudication.json'}:
        file=parent/relative;file.parent.mkdir(parents=True,exist_ok=True)
        file.write_bytes(f'mock:{relative}'.encode())
    inventory={'scope':'synthetic unit test',
        'files':{relative:audit.parent_runner.sha(parent/relative)
                 for relative in audit.expected_parent_files()}}
    (parent/'completed_artifacts.json').write_text(json.dumps(inventory))
    monkeypatch.setattr(audit,'PARENT',parent)
    monkeypatch.setattr(audit,'PARENT_COMPLETE_SHA',audit.parent_runner.sha(
        parent/'completed_artifacts.json'))
    monkeypatch.setattr(audit,'PARENT_REGISTRATION_SHA',registration_sha)
    monkeypatch.setattr(audit,'PARENT_ADJUDICATION_SHA',adjud_sha)
    return parent,inventory


def test_exact_parent_inventory_and_all_artifact_hashes(tmp_path,monkeypatch):
    parent,inventory=fake_parent(tmp_path,monkeypatch)
    bound=audit.parent_inventory()
    assert len(bound['artifact_hashes'])==36
    assert bound['artifact_hashes']==inventory['files']
    assert bound['original_terminal']=='FAILED_EVIDENCE'
    with (parent/'n12/arrays.npz').open('ab') as stream:
        stream.write(b'tamper')
    with pytest.raises(ValueError,match='frozen parent artifact changed'):
        audit.parent_inventory()


def test_missing_extra_and_duplicate_parent_paths_rejected(tmp_path,monkeypatch):
    parent,_=fake_parent(tmp_path,monkeypatch)
    (parent/'extra.txt').write_text('extra')
    with pytest.raises(ValueError,match='on-disk inventory changed'):
        audit.parent_inventory()
    (parent/'extra.txt').unlink()
    (parent/'n08/stdout.jsonl').unlink()
    with pytest.raises(ValueError,match='on-disk inventory changed'):
        audit.parent_inventory()
    (parent/'n08/stdout.jsonl').write_bytes(b'mock:n08/stdout.jsonl')
    (parent/'empty').mkdir()
    with pytest.raises(ValueError,match='directory inventory changed'):
        audit.parent_inventory()
    (parent/'empty').rmdir()
    original_resolve=Path.resolve
    target=parent/'n08/stdout.jsonl'
    def redirected(self,*args,**kwargs):
        return tmp_path/'outside' if self==target else original_resolve(
            self,*args,**kwargs)
    monkeypatch.setattr(Path,'resolve',redirected)
    with pytest.raises(ValueError,match='resolves outside root'):
        audit.parent_inventory()
    monkeypatch.setattr(Path,'resolve',original_resolve)
    # JSON duplicate names must be rejected before a dict silently discards one.
    duplicate=tmp_path/'duplicate.json'
    duplicate.write_text('{"files":{},"files":{}}')
    with pytest.raises(ValueError,match='duplicate JSON key'):
        audit._strict_json(duplicate)


def test_only_saved_recomputation_and_zero_replay_counts(tmp_path,monkeypatch):
    parent,_=fake_parent(tmp_path,monkeypatch)
    original=operators.assemble
    seen=[]
    def saved_only(root,name,manifest):
        assert root==parent and name=='n04'
        seen.append(name)
        with pytest.raises(AssertionError,match='forbids'):
            operators.assemble(4)
        with pytest.raises(AssertionError,match='forbids'):
            operators.pose_operators(4,0.)
        with pytest.raises(AssertionError,match='forbids'):
            np.linalg.solve(np.eye(1),np.ones(1))
        return {'status':'FAILED_NUMERICAL_SCREEN',
                'failed_checks':{'saved_action_parity_scaled':{'value':2e-11,
                                  'limit':1e-11}},'metrics':{'checks':{}}},None
    monkeypatch.setattr(audit.parent_runner,'verify_case',saved_only)
    result=audit.reproduce_case('n04',{'parent':audit.parent_inventory()})
    assert seen==['n04'] and operators.assemble is original
    assert result['original_decision']['status']=='FAILED_EVIDENCE'
    assert result['reproduced_decision']['status']=='FAILED_NUMERICAL_SCREEN'
    assert all(result[k]==0 for k in ('equilibrium_solves','element_evaluations',
                                     'integration_assemblies','assembly_descriptions'))


def test_adjudication_integrity_is_separate_from_failed_numerical_screen(
        tmp_path,monkeypatch):
    root=tmp_path/'audit';root.mkdir()
    for name in audit.CASES:
        (root/name).mkdir()
        (root/name/'supervision.json').write_text('{}')
    monkeypatch.setattr(audit,'registered',lambda actual:{'identity':{'mock':True}})
    monkeypatch.setattr(audit.supervisor,'_registration_hash',lambda actual:'mockhash')
    def row(actual,name,manifest):
        status=('FAILED_NUMERICAL_SCREEN' if name in ('n16','n24') else
                'PASSED_NUMERICAL_SCREEN')
        return {'status':status,'original_decision':{'status':'FAILED_EVIDENCE'},
                'reproduced_decision':{'status':status,'failed_checks':{}},
                'parent_arrays_sha256':'mock'}
    monkeypatch.setattr(audit,'verify_audit_case',row)
    assert audit.adjudicate(root) is False
    decision=json.loads((root/'adjudication.json').read_text())
    assert decision['status']=='FAILED_NUMERICAL_SCREEN'
    assert decision['audit_integrity']=='PASSED'
    assert decision['physical_trends'] is None
    assert decision['original_terminal']=='FAILED_EVIDENCE'
    assert set(decision['cases'])==set(audit.CASES)


def test_contradictory_completed_receipt_is_evidence_failure(tmp_path,monkeypatch):
    root=tmp_path/'audit';directory=root/'n04';directory.mkdir(parents=True)
    monkeypatch.setattr(audit.supervisor,'_registration_hash',lambda actual:'mockhash')
    receipt={'reason':'completed','exit_code':0,'elapsed_seconds':1.,
             'sampled_peak_rss_bytes':1000,'phases':['identity','observables'],
             'registration_sha256':'mockhash','failure':'unexpected',
             'observables_sha256':'abc'}
    (directory/'supervision.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='contradictory completed'):
        audit.verify_audit_case(root,'n04',{'identity':{'mock':True}})
    receipt['failure']=None;receipt['exit_code']=False
    (directory/'supervision.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='resource receipt'):
        audit.verify_audit_case(root,'n04',{'identity':{'mock':True}})


@pytest.mark.parametrize('field,value',(
    ('elapsed_seconds',True),('elapsed_seconds',float('nan')),
    ('elapsed_seconds',-1),('sampled_peak_rss_bytes',False),
    ('sampled_peak_rss_bytes',3.5),('sampled_peak_rss_bytes',-1),
    ('exit_code',True)))
@pytest.mark.parametrize('reason',('completed','time_limit'))
def test_malformed_completed_and_failed_resources_are_evidence_failure(
        tmp_path,monkeypatch,reason,field,value):
    root=tmp_path/'audit';directory=root/'n04';directory.mkdir(parents=True)
    monkeypatch.setattr(audit.supervisor,'_registration_hash',lambda actual:'mockhash')
    receipt={'reason':reason,'exit_code':0,'elapsed_seconds':1.,
             'sampled_peak_rss_bytes':1000,'phases':[],
             'registration_sha256':'mockhash','failure':None,
             'observables_sha256':None}
    receipt[field]=value
    (directory/'supervision.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='resource receipt'):
        audit.verify_audit_case(root,'n04',{'identity':{}})


def test_genuine_over_budget_or_partial_failed_receipts_need_no_child_files(
        tmp_path,monkeypatch):
    root=tmp_path/'audit';directory=root/'n04';directory.mkdir(parents=True)
    monkeypatch.setattr(audit.supervisor,'_registration_hash',lambda actual:'mockhash')
    receipt={'reason':'time_limit','exit_code':-9,
             'elapsed_seconds':audit.MAX_SECONDS+3.,
             'sampled_peak_rss_bytes':audit.MAX_RSS_BYTES+1,
             'phases':['identity'],'registration_sha256':'mockhash',
             'failure':None,'observables_sha256':None}
    (directory/'supervision.json').write_text(json.dumps(receipt))
    assert audit.verify_audit_case(root,'n04',{'identity':{}})['status']==(
        'FAILED_EXECUTION')
    receipt['reason']='completed';receipt['exit_code']=0
    receipt['failure']=None
    (directory/'supervision.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='contradictory completed'):
        audit.verify_audit_case(root,'n04',{'identity':{}})
    receipt['reason']='supervisor_failure';receipt['exit_code']=None
    receipt['failure']='OSError: process startup failed';receipt['phases']=[]
    (directory/'supervision.json').write_text(json.dumps(receipt))
    assert audit.verify_audit_case(root,'n04',{'identity':{}})['status']==(
        'FAILED_EXECUTION')


def test_synthetic_child_receipt_and_exclusive_authority(
        tmp_path,monkeypatch,capsys):
    fake_parent(tmp_path,monkeypatch)
    root=tmp_path/'new-audit'
    monkeypatch.setattr(audit,'AUDIT',root)
    monkeypatch.setattr(audit.supervisor,'_clean',lambda:True)
    monkeypatch.setattr(audit.supervisor,'_identity',lambda:{'mock':'identity'})
    audit.register(root)
    manifest=audit.registered(root)
    assert manifest['work']=={'equilibrium_solves_per_case':0,
        'element_evaluations_per_case':0,'integration_assemblies_per_case':0,
        'assembly_descriptions_per_case':0}
    assert len(manifest['parent']['artifact_hashes'])==36
    import threadpoolctl
    monkeypatch.setattr(threadpoolctl,'threadpool_info',lambda:[{'num_threads':1}])
    for key in audit.supervisor.THREADS:
        monkeypatch.setenv(key,'1')
    directory=root/'n04';directory.mkdir()
    calls=[]
    def saved_only(parent,name,old_manifest):
        calls.append(name)
        with pytest.raises(AssertionError,match='forbids'):
            operators.solve(None)
        return {'status':'PASSED_NUMERICAL_SCREEN',
                'failed_checks':{},
                'metrics':{'checks':{'finite':1.},
                           'details':{'nullable':None}}},None
    monkeypatch.setattr(audit.parent_runner,'verify_case',saved_only)
    audit.child(root,'n04')
    events=capsys.readouterr().out.splitlines()
    assert len(events)==2
    (directory/'stdout.jsonl').write_text('\n'.join(events)+'\n')
    event=json.loads(events[1])
    receipt={'reason':'completed','exit_code':0,'elapsed_seconds':.2,
             'sampled_peak_rss_bytes':2048,'phases':['identity','observables'],
             'registration_sha256':audit.supervisor._registration_hash(root),
             'failure':None,'observables_sha256':event['sha256']}
    (directory/'supervision.json').write_text(json.dumps(receipt))
    verified=audit.verify_audit_case(root,'n04',manifest)
    assert verified['status']=='PASSED_NUMERICAL_SCREEN'
    assert calls==['n04','n04']
    assert audit.parent_runner.read(directory/'observables.json')[
        'equilibrium_solves']==0
    with pytest.raises(FileExistsError):
        audit.child(root,'n04')
    (root/'n08').mkdir()
    monkeypatch.setattr(threadpoolctl,'threadpool_info',lambda:[{'num_threads':True}])
    with pytest.raises(ValueError,match='must be single-threaded'):
        audit.child(root,'n08')
    events[0]=json.loads(events[0]);events[0]['threadpools'][0][
        'num_threads']=True
    (directory/'stdout.jsonl').write_text(json.dumps(events[0])+'\n'+events[1]+'\n')
    with pytest.raises(ValueError,match='raw receipt'):
        audit.verify_audit_case(root,'n04',manifest)
    receipt['failure']=None;receipt['exit_code']=False
    (directory/'supervision.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='resource receipt'):
        audit.verify_audit_case(root,'n04',{'identity':{'mock':True}})
