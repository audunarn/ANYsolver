"""Synthetic supervisor/identity tests; no saved scientific state is read."""
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import b3_e4_f03_spatial_residual as runner
import _b3_e4_f03_spatial_checks as checks
import _b3_e4_f03_primal_checks as old_checks


def test_direct_entry_imports_package_without_ambient_pythonpath(tmp_path):
    script=runner.ROOT/'scripts/b3_e4_f03_spatial_residual.py'
    env=os.environ.copy();env['PYTHONPATH']=''
    for key in runner.supervisor.THREADS: env[key]='1'
    direct=subprocess.run([sys.executable,str(script),'--help'],cwd=tmp_path,
                          env=env,capture_output=True,text=True,timeout=20)
    assert direct.returncode==0,direct.stderr
    assert '--run-all' in direct.stdout
    # Simulate sys.path[0]=scripts with neither cwd nor PYTHONPATH holding ROOT.
    code=('import sys; sys.path=[p for p in sys.path if p not in '
          f'({str(runner.ROOT)!r}, "")]; '
          f'sys.path.insert(0,{str(script.parent)!r}); '
          'import b3_e4_f03_spatial_residual as runner; '
          'from scripts import _b3_e4_f03_spatial_checks as checks; '
          'assert runner.ROOT in [__import__("pathlib").Path(p) for p in sys.path]; '
          'assert checks.SCHEMA.startswith("f03_spatial_")')
    nested=subprocess.run([sys.executable,'-c',code],cwd=tmp_path,
                          env=env,capture_output=True,text=True,timeout=20)
    assert nested.returncode==0,nested.stderr


def _fake_exact(tmp_path,monkeypatch):
    root=tmp_path/'exact';root.mkdir()
    registration={'identity':{'head':runner.EXACT_HEAD,
        'dependencies':runner.supervisor._versions(),
        'python':sys.version,'executable':str(Path(sys.executable).resolve()),
        'platform':platform.platform(),'machine':platform.machine(),
        'sources':{'scripts/b3_e4_f03_primal_exact_pose.py':runner.original.sha(
            runner.ROOT/'scripts/b3_e4_f03_primal_exact_pose.py')}},
        'cases':runner.CASES,'threads':{k:'1' for k in runner.supervisor.THREADS}}
    (root/'registration.json').write_text(json.dumps(registration))
    reg_sha=runner.original.sha(root/'registration.json')
    (root/'adjudication.json').write_text(json.dumps({
        'registration_sha256':reg_sha,'status':'PASSED_REPRESENTATION_DIAGNOSTIC',
        'original_terminal':'FAILED_EVIDENCE',
        'saved_audit_terminal':'FAILED_NUMERICAL_SCREEN',
        'saved_audit_integrity':'PASSED',
        'cases':{name:{'status':'PASSED_REPRESENTATION_DIAGNOSTIC'}
                 for name in runner.CASES}}))
    for relative in runner.expected_exact_files()-{
            'registration.json','adjudication.json'}:
        file=root/relative;file.parent.mkdir(parents=True,exist_ok=True)
        file.write_bytes(f'mock:{relative}'.encode())
    inventory={'scope':'mock','files':{rel:runner.original.sha(root/rel)
                for rel in runner.expected_exact_files()}}
    (root/'completed_artifacts.json').write_text(json.dumps(inventory))
    monkeypatch.setattr(runner,'EXACT',root)
    monkeypatch.setattr(runner,'EXACT_COMPLETE_SHA',runner.original.sha(
        root/'completed_artifacts.json'))
    monkeypatch.setattr(runner,'EXACT_REGISTRATION_SHA',reg_sha)
    monkeypatch.setattr(runner,'EXACT_ADJUDICATION_SHA',inventory['files'][
        'adjudication.json'])
    return root,inventory


def test_exact_25_files_full_hashes_and_duplicate_json(tmp_path,monkeypatch):
    root,inventory=_fake_exact(tmp_path,monkeypatch)
    assert len(inventory['files'])==25
    assert runner.exact_inventory()['artifact_hashes']==inventory['files']
    (root/'n12/stdout.jsonl').write_text('changed')
    with pytest.raises(ValueError,match='artifact changed'):
        runner.exact_inventory()
    (root/'n12/stdout.jsonl').write_bytes(b'mock:n12/stdout.jsonl')
    (root/'extra').mkdir()
    with pytest.raises(ValueError,match='on-disk inventory'):
        runner.exact_inventory()
    duplicate=tmp_path/'duplicate.json';duplicate.write_text('{"x":1,"x":2}')
    with pytest.raises(ValueError,match='duplicate'):
        runner._strict_json(duplicate)
    invalid=tmp_path/'nan.json';invalid.write_text('{"x":NaN}')
    with pytest.raises(ValueError,match='nonfinite'):
        runner._strict_json(invalid)


def _fake_registration(tmp_path,monkeypatch):
    root=tmp_path/'new';monkeypatch.setattr(runner,'TARGET',root)
    monkeypatch.setattr(runner.supervisor,'_clean',lambda:True)
    monkeypatch.setattr(runner.supervisor,'_identity',lambda:{'mock':'identity'})
    monkeypatch.setattr(runner.saved,'parent_inventory',lambda:{
        'registration_sha256':'oldreg','artifact_hashes':{
            'n12/arrays.npz':'oldarray'}})
    monkeypatch.setattr(runner.exact_runner,'audit_inventory',lambda:{
        'registration_sha256':'auditreg'})
    monkeypatch.setattr(runner,'exact_inventory',lambda:{
        'registration_sha256':'exactreg','artifact_hashes':{
            'n12/observables.json':'exactobservation'}})
    runner.register(root)
    manifest=runner.registered(root)
    assert manifest['limits']=={'seconds_per_case':900,
        'rss_bytes_per_case':2*1024**3,'launch_cutoff_seconds':3600,
        'observables_json_bytes':32*1024**2}
    return root,manifest


def test_one_child_integration_parent_raw_only_and_exact_envelope(
        tmp_path,monkeypatch,capsys):
    root,manifest=_fake_registration(tmp_path,monkeypatch)
    calls=[]
    audit={'original_decision':{'status':'FAILED_EVIDENCE'},
           'reproduced_decision':{'status':'FAILED_NUMERICAL_SCREEN',
                                  'inherited_numeric':1.0}}
    exact_case={'status':'PASSED_REPRESENTATION_DIAGNOSTIC','mock':'exact'}
    monkeypatch.setattr(runner,'_inputs',lambda name,m:({
        'q':'synthetic'},audit,exact_case,{'schema':'synthetic_pose'}))
    def evaluate(n,arrays,pose):
        calls.append(('evaluate',n))
        with pytest.raises(AssertionError,match='forbids'):
            old_checks.verify_saved(None,n)
        return {'raw':'synthetic integral'}
    monkeypatch.setattr(checks,'evaluate_saved',evaluate)
    monkeypatch.setattr(checks,'validate_saved_binding',lambda record,n,arrays,pose:
        calls.append(('binding',n)))
    monkeypatch.setattr(checks,'adjudicate_record',lambda record,n:
        (calls.append(('adjudicate',n)) or {
            'status':'PASSED_SPATIAL_RESIDUAL_DIAGNOSTIC',
            'metrics':{'numerical':0.},'failures':{},'summaries':{}}))
    import threadpoolctl
    monkeypatch.setattr(threadpoolctl,'threadpool_info',lambda:[{'num_threads':1}])
    for key in runner.supervisor.THREADS: monkeypatch.setenv(key,'1')
    directory=root/'n12';directory.mkdir()
    runner.child(root,'n12')
    lines=capsys.readouterr().out.splitlines()
    assert len(lines)==2
    (directory/'stdout.jsonl').write_text('\n'.join(lines)+'\n')
    event=json.loads(lines[1])
    receipt={'reason':'completed','exit_code':0,'elapsed_seconds':.25,
        'sampled_peak_rss_bytes':2048,'phases':['identity','observables'],
        'registration_sha256':runner.supervisor._registration_hash(root),
        'failure':None,'observables_sha256':event['sha256']}
    (directory/'supervision.json').write_text(json.dumps(receipt))
    result=runner.verify_case(root,'n12',manifest)
    assert result['status']=='PASSED_SPATIAL_RESIDUAL_DIAGNOSTIC'
    assert calls==[('evaluate',12),('binding',12),('adjudicate',12),
                   ('binding',12),('adjudicate',12)]
    observed=runner._strict_json(directory/'observables.json')
    assert observed['work']==checks.work_counts()
    assert observed['exact_observables_sha256']=='exactobservation'
    observed['saved_audit_decision']['reproduced_decision'][
        'inherited_numeric']=1.+5e-13
    (directory/'observables.json').write_text(json.dumps(observed))
    event=runner.observable_event(directory,'n12',runner.CASES['n12'],False)
    (directory/'stdout.jsonl').write_text(lines[0]+'\n'+json.dumps(event)+'\n')
    receipt['observables_sha256']=event['sha256']
    (directory/'supervision.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match='floating value changed'):
        runner.verify_case(root,'n12',manifest)
    with pytest.raises(FileExistsError): runner.child(root,'n12')
    identity=json.loads(lines[0]);identity['threadpools'][0]['num_threads']=True
    (directory/'stdout.jsonl').write_text(json.dumps(identity)+'\n'+lines[1]+'\n')
    with pytest.raises(ValueError,match='child identity'):
        runner.verify_case(root,'n12',manifest)


def test_receipt_resource_types_and_partial_execution(tmp_path,monkeypatch):
    root=tmp_path/'new';directory=root/'n12';directory.mkdir(parents=True)
    monkeypatch.setattr(runner.supervisor,'_registration_hash',lambda root:'reg')
    receipt={'reason':'time_limit','exit_code':-9,
        'elapsed_seconds':runner.MAX_SECONDS+1,
        'sampled_peak_rss_bytes':runner.MAX_RSS_BYTES+1,
        'phases':[],'registration_sha256':'reg',
        'failure':None,'observables_sha256':None}
    (directory/'supervision.json').write_text(json.dumps(receipt))
    assert runner.verify_case(root,'n12',{})['status']=='FAILED_EXECUTION'
    for key,value in (('elapsed_seconds',True),('sampled_peak_rss_bytes',False),
                      ('exit_code',True),('elapsed_seconds',float('nan')),
                      ('elapsed_seconds',float('inf')),
                      ('elapsed_seconds',1e309),
                      ('sampled_peak_rss_bytes',3.5),
                      ('sampled_peak_rss_bytes',-1)):
        changed=receipt.copy();changed[key]=value
        (directory/'supervision.json').write_text(json.dumps(changed))
        with pytest.raises(ValueError,match='resource receipt|nonfinite JSON token'):
            runner.verify_case(root,'n12',{})
    for key,value in (('exit_code',-9),('failure','not completed'),
                      ('elapsed_seconds',runner.MAX_SECONDS+1),
                      ('sampled_peak_rss_bytes',runner.MAX_RSS_BYTES+1)):
        completed={**receipt,'reason':'completed','exit_code':0,
                   'failure':None,'elapsed_seconds':1.,
                   'sampled_peak_rss_bytes':4096}
        completed[key]=value
        (directory/'supervision.json').write_text(json.dumps(completed))
        with pytest.raises(ValueError,match='contradictory completed'):
            runner.verify_case(root,'n12',{})


def test_terminal_precedence_and_programming_assertion(tmp_path,monkeypatch):
    root=tmp_path/'new';root.mkdir()
    for name in runner.CASES:
        (root/name).mkdir();(root/name/'supervision.json').write_text('{}')
    monkeypatch.setattr(runner,'registered',lambda root:{
        'identity':{'mock':1},'work':checks.work_counts()})
    monkeypatch.setattr(runner.supervisor,'_registration_hash',lambda root:'reg')
    statuses={'n12':'PASSED_SPATIAL_RESIDUAL_DIAGNOSTIC',
              'n16':'FAILED_NUMERICAL_IDENTITY',
              'n24':'PASSED_SPATIAL_RESIDUAL_DIAGNOSTIC'}
    monkeypatch.setattr(runner,'verify_case',lambda root,name,manifest:{
        'status':statuses[name]})
    assert runner.adjudicate(root) is False
    decision=runner._strict_json(root/'adjudication.json')
    assert decision['status']=='FAILED_NUMERICAL_IDENTITY'
    assert decision['original_terminal']=='FAILED_EVIDENCE'
    assert decision['exact_pose_terminal']=='PASSED_REPRESENTATION_DIAGNOSTIC'
    with pytest.raises(FileExistsError): runner.adjudicate(root)

    other=tmp_path/'assertion';other.mkdir()
    for name in runner.CASES:
        (other/name).mkdir();(other/name/'supervision.json').write_text('{}')
    def unexpected(*args,**kwargs): raise AssertionError('programmer error')
    monkeypatch.setattr(runner,'verify_case',unexpected)
    with pytest.raises(AssertionError,match='programmer error'):
        runner.adjudicate(other)
    assert not (other/'adjudication.json').exists()


def test_incomplete_receipts_cannot_make_canonical_decision(tmp_path,monkeypatch):
    root=tmp_path/'new';root.mkdir()
    (root/'n12').mkdir();(root/'n12/supervision.json').write_text('{}')
    monkeypatch.setattr(runner,'registered',lambda root:{
        'identity':{'mock':1},'work':checks.work_counts()})
    with pytest.raises(ValueError,match='complete three-case'):
        runner.adjudicate(root)
    assert not (root/'adjudication.json').exists()
