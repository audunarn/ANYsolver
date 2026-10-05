"""One-use, supervised saved-state F03 spatial residual diagnostic.

This reads three immutable Ritz states and accepted exact-pose records. Child
processes perform fixed spatial integrations; adjudication checks saved raw
integrals without reassembling, resolving an equilibrium or rerunning fields.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime,timezone
import json
import math
import os
from pathlib import Path
import platform
import sys
import time
import zipfile

# A direct ``python scripts/...py`` launch normally places only scripts/ on
# sys.path. The bounded mechanics helpers deliberately use ``scripts.*``;
# resolve their package from this runner's own location, not ambient PYTHONPATH.
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

import b3_e4_f03_area_feasibility as supervisor
import b3_e4_f03_primal_ritz as original
import b3_e4_f03_primal_saved_audit as saved
import b3_e4_f03_primal_exact_pose as exact_runner


BASE=ROOT/'.qualification'/'b3-ge-e4-pl'
PARENT=BASE/'f03-primal-ritz-v1'
AUDIT=BASE/'f03-primal-saved-audit-v1'
EXACT=BASE/'f03-primal-exact-pose-v1'
TARGET=BASE/'f03-spatial-residual-v1'
CASES={name:original.CASES[name] for name in ('n12','n16','n24')}
MAX_SECONDS=900
MAX_RSS_BYTES=2*1024**3
LAUNCH_CUTOFF_SECONDS=3600
MAX_JSON_BYTES=32*1024**2
KIND='experimental-primal-saved-spatial-residual-v1'
SCOPE=('saved-state represented spatial integration only; original '
       'FAILED_EVIDENCE, audit numerical HOLD and physical HOLD retained')
EXACT_HEAD='d0b6d0902360210f78e06b45f7bbabb030ea4022'
EXACT_REGISTRATION_SHA='0371cb7e2e3d6cf68f54e215fb455ba2bce8ec7e59b57c2144ebe0ec023d85d7'
EXACT_ADJUDICATION_SHA='557ec2d058db562e0d1991c1929b475e9d86d5f9a7ba4109fdbcbabedbdb7b18'
EXACT_COMPLETE_SHA='e7f0b5c8a8a403d7785ddba793e8061628b8b1b163ba4251338b63c3f0e5de0a'
EXACT_ROOT_FILES={'adjudication.json','execution_provenance.json',
    'independent_review.json','orchestration.json','pre_execution_review.json',
    'registration.json','registration.sha256','unit_checks_final_runner.log',
    'unit_checks_initial_scalar_failure.log','unit_checks_integrated.log'}
EXACT_CASE_FILES={'child_started.json','observables.json','stderr.txt',
                  'stdout.jsonl','supervision.json'}
SOURCES=('b3_e4_f03_spatial_residual.py','_b3_e4_f03_spatial_checks.py',
         '_b3_e4_f03_spatial_fields.py','_b3_e4_f03_spatial_tests.py',
         '_b3_e4_f03_spatial_contract.py',
         'b3_e4_f03_primal_exact_pose.py','_b3_e4_f03_primal_exact_pose.py',
         '_b3_e4_f03_primal_exact_checks.py',
         'b3_e4_f03_primal_saved_audit.py','b3_e4_f03_primal_ritz.py',
         'b3_e4_f03_area_feasibility.py','_b3_e4_f03_primal_archive.py',
         '_b3_e4_f03_primal_checks.py','_b3_e4_f03_primal_functional.py',
         '_b3_e4_f03_primal_ritz.py','_b3_e4_f03_primal_trends.py')
TEST_SOURCES=('test_b3_e4_f03_spatial_fields.py',
              'test_b3_e4_f03_spatial_test_fields.py',
              'test_b3_e4_f03_spatial_checks.py',
              'test_b3_e4_f03_spatial_residual_runner.py')
DOCS=('B3_GE_E4_PL_G0_F03_SPATIAL_RESIDUAL_DESIGN.md',
      'B3_GE_E4_PL_G0_F03_SPATIAL_RESIDUAL_PROTOCOL.md')


def _strict_json(path: Path,max_bytes: int=MAX_JSON_BYTES) -> dict:
    if path.stat().st_size>max_bytes:
        raise ValueError('bounded spatial JSON size exceeded')
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result: raise ValueError(f'duplicate spatial JSON key: {key}')
            result[key]=value
        return result
    def reject(value): raise ValueError(f'nonfinite JSON token: {value}')
    result=json.loads(path.read_text(encoding='utf-8'),
                      object_pairs_hook=unique,parse_constant=reject)
    if type(result) is not dict: raise ValueError('spatial JSON root must be object')
    return result


def expected_exact_files() -> set[str]:
    return EXACT_ROOT_FILES | {f'{name}/{item}' for name in CASES
                               for item in EXACT_CASE_FILES}


def exact_inventory() -> dict:
    """Bind every byte of the accepted exact diagnostic and its source."""
    if original.sha(EXACT/'completed_artifacts.json')!=EXACT_COMPLETE_SHA:
        raise ValueError('exact-pose completed inventory hash changed')
    completed=_strict_json(EXACT/'completed_artifacts.json',1024**2)
    if (set(completed)!={'files','scope'} or
            set(completed['files'])!=expected_exact_files() or
            len(completed['files'])!=25):
        raise ValueError('exact-pose 25-file inventory changed')
    entries=list(EXACT.rglob('*'))
    if EXACT.is_symlink() or any(entry.is_symlink() for entry in entries):
        raise ValueError('exact-pose symlinked artifact path')
    resolved=EXACT.resolve()
    for entry in entries:
        try: entry.resolve().relative_to(resolved)
        except ValueError as exc:
            raise ValueError('exact-pose path resolves outside root') from exc
    directories={str(p.relative_to(EXACT)).replace('\\','/') for p in entries
                 if p.is_dir()}
    files={str(p.relative_to(EXACT)).replace('\\','/') for p in entries
           if p.is_file()}
    if directories!=set(CASES) or files!=expected_exact_files()|{'completed_artifacts.json'}:
        raise ValueError('exact-pose on-disk inventory changed')
    for relative,digest in completed['files'].items():
        if (type(digest) is not str or len(digest)!=64 or
                any(char not in '0123456789abcdef' for char in digest) or
                original.sha(EXACT/relative)!=digest):
            raise ValueError(f'exact-pose artifact changed: {relative}')
    if (completed['files']['registration.json']!=EXACT_REGISTRATION_SHA or
            completed['files']['adjudication.json']!=EXACT_ADJUDICATION_SHA):
        raise ValueError('exact-pose registration or decision changed')
    registration=_strict_json(EXACT/'registration.json',1024**2)
    adjudication=_strict_json(EXACT/'adjudication.json',MAX_JSON_BYTES)
    identity=registration['identity']
    if (identity['head']!=EXACT_HEAD or registration['cases']!=CASES or
            identity['dependencies']!=supervisor._versions() or
            identity['python']!=sys.version or
            identity['executable']!=str(Path(sys.executable).resolve()) or
            identity['platform']!=platform.platform() or
            identity['machine']!=platform.machine() or
            registration['threads']!={key:'1' for key in supervisor.THREADS} or
            adjudication['registration_sha256']!=EXACT_REGISTRATION_SHA or
            adjudication['status']!='PASSED_REPRESENTATION_DIAGNOSTIC' or
            adjudication['original_terminal']!='FAILED_EVIDENCE' or
            adjudication['saved_audit_terminal']!='FAILED_NUMERICAL_SCREEN' or
            adjudication['saved_audit_integrity']!='PASSED' or
            set(adjudication['cases'])!=set(CASES) or
            any(row['status']!='PASSED_REPRESENTATION_DIAGNOSTIC'
                for row in adjudication['cases'].values())):
        raise ValueError('exact-pose frozen identity/terminal changed')
    for relative,digest in identity['sources'].items():
        if original.sha(ROOT/relative)!=digest:
            raise ValueError(f'exact-pose frozen source changed: {relative}')
    return {'root':'.qualification/b3-ge-e4-pl/f03-primal-exact-pose-v1',
            'head':EXACT_HEAD,'registration_sha256':EXACT_REGISTRATION_SHA,
            'adjudication_sha256':EXACT_ADJUDICATION_SHA,
            'completed_artifacts_sha256':EXACT_COMPLETE_SHA,
            'artifact_hashes':completed['files'],'identity':identity}


def contract() -> dict:
    import _b3_e4_f03_spatial_checks as checks
    from scripts import _b3_e4_f03_spatial_contract as physical
    return {'kind':KIND,'cases':CASES,'scope':SCOPE,
            'identity':supervisor._identity(),
            'original_parent':saved.parent_inventory(),
            'saved_audit':exact_runner.audit_inventory(),
            'exact_pose':exact_inventory(),
            'spatial_definition':checks.definition_record(),
            'physical_definition':physical.definition_record(),
            'threads':{key:'1' for key in supervisor.THREADS},
            'limits':{'seconds_per_case':MAX_SECONDS,
                      'rss_bytes_per_case':MAX_RSS_BYTES,
                      'launch_cutoff_seconds':LAUNCH_CUTOFF_SECONDS,
                      'observables_json_bytes':MAX_JSON_BYTES},
            'work':checks.work_counts(),
            'terminal':['FAILED_EVIDENCE','FAILED_EXECUTION',
                'FAILED_NUMERICAL_IDENTITY','PASSED_SPATIAL_RESIDUAL_DIAGNOSTIC']}


def register(root: Path) -> None:
    if root.resolve()!=TARGET.resolve() or not supervisor._clean():
        raise ValueError('spatial registration requires clean source and exact new root')
    manifest=contract()
    manifest['created_utc']=datetime.now(timezone.utc).isoformat()
    root.mkdir(parents=True,exist_ok=False)
    supervisor._json_new(root/'registration.json',manifest)
    with (root/'registration.sha256').open('x',encoding='ascii') as stream:
        stream.write(original.sha(root/'registration.json')+'\n')


def registered(root: Path) -> dict:
    if root.resolve()!=TARGET.resolve():
        raise ValueError('spatial registration root changed')
    supervisor._registration_hash(root)
    manifest=_strict_json(root/'registration.json',MAX_JSON_BYTES)
    frozen=contract()
    if (set(manifest)!=set(frozen)|{'created_utc'} or
            {k:v for k,v in manifest.items() if k!='created_utc'}!=frozen or
            type(manifest['created_utc']) is not str or
            not datetime.fromisoformat(manifest['created_utc']).tzinfo):
        raise ValueError('spatial registration identity or inputs changed')
    return manifest


@contextmanager
def forbid_original_recomputation():
    """Block old science and exact-study replay during spatial integration.

    The accepted exact.from_record deliberately reconstructs its own pure
    rational pose to prove the saved record; that validated parse is allowed.
    """
    import _b3_e4_f03_primal_exact_checks as exact_checks
    originals=[]
    def forbidden(*args,**kwargs):
        raise AssertionError('spatial saved-state scope forbids old recomputation')
    with exact_runner.forbid_original_recomputation():
        try:
            for module,names in ((exact_checks,('evaluate_saved','verify_saved_record')),
                                 (exact_runner,('verify_case','make_observations'))):
                for name in names:
                    originals.append((module,name,getattr(module,name)))
                    setattr(module,name,forbidden)
            yield
        finally:
            for module,name,value in reversed(originals):
                setattr(module,name,value)


def _inputs(name: str,manifest: dict) -> tuple[dict,dict,dict,dict]:
    import _b3_e4_f03_primal_exact_checks as exact_checks
    if name not in CASES: raise ValueError('unknown spatial case')
    arrays=exact_runner._original_arrays(name,manifest)
    audit_case=exact_runner._audit_decision(name,manifest)
    if original.sha(EXACT/'adjudication.json')!=manifest['exact_pose']['adjudication_sha256']:
        raise ValueError('exact-pose frozen decision changed')
    exact_case=_strict_json(EXACT/'adjudication.json',MAX_JSON_BYTES)['cases'][name]
    path=EXACT/name/'observables.json'
    if original.sha(path)!=manifest['exact_pose']['artifact_hashes'][name+'/observables.json']:
        raise ValueError('exact-pose frozen observation changed')
    observed=_strict_json(path,exact_runner.MAX_JSON_BYTES)
    if (observed['case']!=name or observed['degree']!=CASES[name]['degree'] or
            observed['parent_arrays_sha256']!=manifest['original_parent'][
                'artifact_hashes'][name+'/arrays.npz'] or
            observed['original_registration_sha256']!=manifest['original_parent'][
                'registration_sha256'] or
            observed['saved_audit_registration_sha256']!=manifest['saved_audit'][
                'registration_sha256'] or
            observed['work']!=exact_runner.WORK or observed['scope']!=exact_runner.SCOPE or
            exact_case['status']!='PASSED_REPRESENTATION_DIAGNOSTIC' or
            observed['diagnostic']['diagnostic_status']!=exact_case['status']):
        raise ValueError('exact-pose saved input links changed')
    exact_checks._identical(observed['saved_audit_decision'],audit_case)
    exact_checks._identical(observed['original_decision'],audit_case['original_decision'])
    exact_checks._identical(exact_case['diagnostic'],observed['diagnostic'])
    exact_checks.validate_payload(observed['diagnostic'],CASES[name]['degree'])
    return arrays,audit_case,exact_case,observed['diagnostic']['pose']


def _envelope(name: str,manifest: dict,raw: dict,child_decision: dict,
              audit_case: dict,exact_case: dict) -> dict:
    return {'case':name,'degree':CASES[name]['degree'],
            'diagnostic':{'raw':raw,'child_decision':child_decision},
            'original_decision':audit_case['original_decision'],
            'saved_audit_decision':audit_case,'exact_pose_decision':exact_case,
            'parent_arrays_sha256':manifest['original_parent'][
                'artifact_hashes'][name+'/arrays.npz'],
            'exact_observables_sha256':manifest['exact_pose'][
                'artifact_hashes'][name+'/observables.json'],
            'original_registration_sha256':manifest['original_parent'][
                'registration_sha256'],
            'saved_audit_registration_sha256':manifest['saved_audit'][
                'registration_sha256'],
            'exact_pose_registration_sha256':manifest['exact_pose'][
                'registration_sha256'],
            'work':manifest['work'],'scope':SCOPE}


def make_observations(name: str,manifest: dict) -> dict:
    import _b3_e4_f03_spatial_checks as checks
    arrays,audit_case,exact_case,pose_record=_inputs(name,manifest)
    with forbid_original_recomputation():
        raw=checks.evaluate_saved(CASES[name]['degree'],arrays,pose_record)
        checks.validate_saved_binding(raw,CASES[name]['degree'],arrays,pose_record)
        decision=checks.adjudicate_record(raw,CASES[name]['degree'])
    if decision['status'] not in ('FAILED_NUMERICAL_IDENTITY',
                                  'PASSED_SPATIAL_RESIDUAL_DIAGNOSTIC'):
        raise ValueError('invalid spatial diagnostic decision')
    return _envelope(name,manifest,raw,decision,audit_case,exact_case)


def _json_new_limited(path: Path,payload: dict) -> None:
    encoded=json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+'\n'
    if len(encoded.encode('utf-8'))>MAX_JSON_BYTES:
        raise ValueError('spatial observation exceeds 32MiB')
    with path.open('x',encoding='utf-8') as stream: stream.write(encoded)


def observable_event(directory: Path,name: str,spec: dict,
                     capture_state: bool) -> dict:
    if name not in CASES or spec!=CASES[name] or capture_state is not False:
        raise ValueError('unregistered spatial observable event')
    manifest=registered(directory.parent)
    return {'phase':'observables','case':name,
            'sha256':original.sha(directory/'observables.json'),
            'parent_arrays_sha256':manifest['original_parent'][
                'artifact_hashes'][name+'/arrays.npz'],
            'exact_observables_sha256':manifest['exact_pose'][
                'artifact_hashes'][name+'/observables.json'],
            'child_started_sha256':original.sha(directory/'child_started.json')}


def child(root: Path,name: str) -> None:
    manifest=registered(root)
    if name not in CASES or any(os.environ.get(k)!='1' for k in supervisor.THREADS):
        raise ValueError('unregistered spatial child or thread setting')
    directory=root/name
    supervisor._json_new(directory/'child_started.json',{'case':name,
        'registration_sha256':supervisor._registration_hash(root),
        'pid':os.getpid(),'started_unix_seconds':time.time()})
    from threadpoolctl import threadpool_info
    pools=threadpool_info()
    if not saved._single_threaded(pools):
        raise ValueError('spatial numerical pools must be single-threaded')
    print(json.dumps({'phase':'identity','case':name,
        'identity':manifest['identity'],
        'registration_sha256':supervisor._registration_hash(root),
        'threadpools':pools}),flush=True)
    _json_new_limited(directory/'observables.json',make_observations(name,manifest))
    print(json.dumps(observable_event(directory,name,CASES[name],False)),flush=True)


def verify_case(root: Path,name: str,manifest: dict) -> dict:
    import _b3_e4_f03_spatial_checks as checks
    import _b3_e4_f03_primal_exact_checks as exact_checks
    if name not in CASES: raise ValueError('unknown spatial case')
    directory=root/name
    receipt=_strict_json(directory/'supervision.json',1024**2)
    if (set(receipt)!={'reason','exit_code','elapsed_seconds',
                      'sampled_peak_rss_bytes','phases','registration_sha256',
                      'failure','observables_sha256'} or
            receipt['registration_sha256']!=supervisor._registration_hash(root)):
        raise ValueError('spatial supervisor receipt inventory invalid')
    elapsed=receipt['elapsed_seconds'];rss=receipt['sampled_peak_rss_bytes']
    if (type(receipt['reason']) is not str or not receipt['reason'] or
            (type(receipt['exit_code']) is not int and
             receipt['exit_code'] is not None) or
            type(elapsed) not in (int,float) or not math.isfinite(elapsed) or
            elapsed<0 or type(rss) is not int or rss<0 or
            type(receipt['phases']) is not list or
            any(type(phase) is not str for phase in receipt['phases']) or
            (receipt['failure'] is not None and
             type(receipt['failure']) is not str)):
        raise ValueError('malformed spatial resource receipt')
    if (receipt['reason']=='completed' and
            (receipt['failure'] is not None or
             type(receipt['exit_code']) is not int or receipt['exit_code']!=0 or
             elapsed>MAX_SECONDS or rss>MAX_RSS_BYTES)):
        raise ValueError('contradictory completed spatial receipt')
    if receipt['reason']!='completed':
        return {'status':'FAILED_EXECUTION','receipt':receipt}
    marker=_strict_json(directory/'child_started.json',1024**2)
    event=observable_event(directory,name,CASES[name],False)
    lines=(directory/'stdout.jsonl').read_text(encoding='utf-8').splitlines()
    events=[json.loads(line) for line in lines]
    if (set(marker)!={'case','registration_sha256','pid','started_unix_seconds'} or
            marker['case']!=name or marker['registration_sha256']!=
            supervisor._registration_hash(root) or
            type(marker['pid']) is not int or marker['pid']<=0 or
            type(marker['started_unix_seconds']) not in (int,float) or
            not math.isfinite(marker['started_unix_seconds']) or
            receipt['phases']!=['identity','observables'] or
            receipt['observables_sha256']!=event['sha256'] or
            len(events)!=2 or not all(type(e) is dict for e in events) or
            events[0].get('phase')!='identity' or events[0].get('case')!=name or
            events[0].get('identity')!=manifest['identity'] or
            events[0].get('registration_sha256')!=
            supervisor._registration_hash(root) or
            not saved._single_threaded(events[0].get('threadpools')) or
            events[1]!=event):
        raise ValueError('spatial child identity, receipt or event invalid')
    observed=_strict_json(directory/'observables.json')
    if (set(observed)!={'case','degree','diagnostic','original_decision',
                        'saved_audit_decision','exact_pose_decision',
                        'parent_arrays_sha256','exact_observables_sha256',
                        'original_registration_sha256',
                        'saved_audit_registration_sha256',
                        'exact_pose_registration_sha256','work','scope'} or
            type(observed['diagnostic']) is not dict or
            set(observed['diagnostic'])!={'raw','child_decision'} or
            observed['work']!=manifest['work'] or observed['scope']!=SCOPE):
        raise ValueError('spatial observation inventory changed')
    arrays,audit_case,exact_case,pose_record=_inputs(name,manifest)
    with forbid_original_recomputation():
        checks.validate_saved_binding(observed['diagnostic']['raw'],
                                      CASES[name]['degree'],arrays,pose_record)
        checked=checks.adjudicate_record(observed['diagnostic']['raw'],
                                         CASES[name]['degree'])
    if checked['status'] not in ('FAILED_NUMERICAL_IDENTITY',
                                'PASSED_SPATIAL_RESIDUAL_DIAGNOSTIC'):
        raise ValueError('invalid verified spatial decision')
    expected=_envelope(name,manifest,observed['diagnostic']['raw'],checked,
                       audit_case,exact_case)
    exact_checks._identical(observed,expected)
    return {'status':checked['status'],'metrics':checked['metrics'],
            'failures':checked['failures'],'summaries':checked['summaries'],
            'parent_arrays_sha256':expected['parent_arrays_sha256'],
            'exact_observables_sha256':expected['exact_observables_sha256'],
            'original_decision':expected['original_decision'],
            'saved_audit_decision':expected['saved_audit_decision'],
            'exact_pose_decision':expected['exact_pose_decision']}


def adjudicate(root: Path) -> bool:
    manifest=registered(root)
    if any(not (root/name/'supervision.json').is_file() for name in CASES):
        raise ValueError('complete three-case spatial receipt inventory required')
    decisions={}
    for name in CASES:
        try:
            decisions[name]=verify_case(root,name,manifest)
        except (OSError,ValueError,KeyError,TypeError,IndexError,AttributeError,
                EOFError,zipfile.BadZipFile) as exc:
            decisions[name]={'status':'FAILED_EVIDENCE',
                             'reason':f'{type(exc).__name__}: {exc}'}
    status=next((candidate for candidate in ('FAILED_EVIDENCE',
        'FAILED_EXECUTION','FAILED_NUMERICAL_IDENTITY') if any(
        row['status']==candidate for row in decisions.values())),
        'PASSED_SPATIAL_RESIDUAL_DIAGNOSTIC')
    supervisor._json_new(root/'adjudication.json',{
        'registration_sha256':supervisor._registration_hash(root),
        'identity':manifest['identity'],'status':status,'cases':decisions,
        'original_terminal':'FAILED_EVIDENCE',
        'saved_audit_terminal':'FAILED_NUMERICAL_SCREEN',
        'saved_audit_integrity':'PASSED',
        'exact_pose_terminal':'PASSED_REPRESENTATION_DIAGNOSTIC',
        'work':manifest['work'],'scope':SCOPE})
    print(json.dumps({'status':status,'cases':{
        k:v['status'] for k,v in decisions.items()}},sort_keys=True))
    return status=='PASSED_SPATIAL_RESIDUAL_DIAGNOSTIC'


def configure() -> None:
    supervisor.ROOT=ROOT
    supervisor.CASES=CASES
    supervisor.RUNNER=Path(__file__).resolve()
    supervisor.SOURCES=(tuple(ROOT/'scripts'/name for name in SOURCES)+
                        tuple(ROOT/'tests'/name for name in TEST_SOURCES)+
                        tuple(ROOT/'docs/agent_plans'/name for name in DOCS))
    supervisor.CAPTURE_STATE=False
    supervisor.MAX_SECONDS=MAX_SECONDS
    supervisor.MAX_RSS_BYTES=MAX_RSS_BYTES
    supervisor._registered=registered
    supervisor._observable_event=observable_event


def run_once(root: Path) -> bool:
    register(root)
    start=time.monotonic();completed=[]
    try:
        for name in CASES:
            if time.monotonic()-start>LAUNCH_CUTOFF_SECONDS:
                raise TimeoutError('spatial launch cutoff; evidence incomplete')
            ok=supervisor.execute(root,name)
            completed.append({'case':name,'execution_completed':ok})
            if not ok:
                receipt=_strict_json(root/name/'supervision.json',1024**2)
                if (receipt.get('reason')=='supervisor_failure' and
                    (receipt.get('failure') or '').startswith((
                        'KeyboardInterrupt:','SystemExit:','GeneratorExit:'))):
                    raise KeyboardInterrupt('preserved supervised cancellation')
        return adjudicate(root)
    finally:
        supervisor._json_new(root/'orchestration.json',{
            'registration_sha256':supervisor._registration_hash(root),
            'cases':completed,'inventory_complete':len(completed)==len(CASES),
            'elapsed_seconds':time.monotonic()-start,
            'supervisor_thread_caps':{k:os.environ.get(k)
                                      for k in supervisor.THREADS}})


def main() -> int:
    if any(os.environ.get(k)!='1' for k in supervisor.THREADS):
        raise ValueError('all spatial supervisor and child thread caps must equal one')
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    for flag in ('run-all','register','execute','adjudicate','child'):
        group.add_argument('--'+flag,action='store_true')
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--case',choices=CASES)
    args=parser.parse_args()
    if (args.execute or args.child)!=bool(args.case):
        parser.error('--case required only for execute or child')
    configure();root=args.root.resolve()
    if args.run_all: return 0 if run_once(root) else 1
    if args.register: register(root);return 0
    if args.execute: return 0 if supervisor.execute(root,args.case) else 1
    if args.adjudicate: return 0 if adjudicate(root) else 1
    child(root,args.case);return 0


if __name__=='__main__':
    raise SystemExit(main())
