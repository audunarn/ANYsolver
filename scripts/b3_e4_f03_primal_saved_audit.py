"""One-use supervised audit of frozen primal Ritz arrays, without new solves.

The original failed decision remains immutable. This runner only rechecks
its exact saved receipts, matrices and numerical screen under new authority.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
import zipfile

import b3_e4_f03_area_feasibility as supervisor
import b3_e4_f03_primal_ritz as parent_runner


ROOT = Path(__file__).resolve().parents[1]
QUALIFICATION = ROOT/'.qualification'/'b3-ge-e4-pl'
PARENT = QUALIFICATION/'f03-primal-ritz-v1'
AUDIT = QUALIFICATION/'f03-primal-saved-audit-v1'
PARENT_RELATIVE = '.qualification/b3-ge-e4-pl/f03-primal-ritz-v1'
CASES = parent_runner.CASES
MAX_SECONDS = 900
MAX_RSS_BYTES = 8*1024**3
LAUNCH_CUTOFF_SECONDS = 3600
KIND = 'experimental-primal-ritz-saved-evidence-audit-v1'
SCOPE = ('saved numerical integrity only; zero equilibrium solves or assembly; '
         'original FAILED_EVIDENCE and physical reference HOLD preserved')
PARENT_COMPLETE_SHA = 'c89cd28009a193b611fe24e3d98add868f3fc62f9b719f7915d7f0a80823157b'
PARENT_REGISTRATION_SHA = '4a8cdf3a77d561c2d8bd3bcdaf59d7df8b1a67e731505ad6f9ac05f52b6bb65e'
PARENT_ADJUDICATION_SHA = '3a079523bd3c4329135c8a445962e39fc3031ade42d74c72c93b8c036f54cf09'
PARENT_HEAD = 'e7908c1ad3dcff1cf9bc957ba8fd0fe1fe49b5b5'
CORRECTED_READER_SHA = 'ed734f961c558823ce2062c001c81193517fbfea20f2ffcee15127f410b2f410'
ORIGINAL_TERMINAL = 'FAILED_EVIDENCE'
SOURCES = ('b3_e4_f03_primal_saved_audit.py','b3_e4_f03_primal_ritz.py',
           '_b3_e4_f03_primal_ritz.py','_b3_e4_f03_primal_checks.py',
           '_b3_e4_f03_primal_functional.py','_b3_e4_f03_primal_archive.py',
           '_b3_e4_f03_primal_trends.py','b3_e4_f03_area_feasibility.py')
_ROOT_ARTIFACTS = {'registration.json','registration.sha256',
                   'adjudication.json','orchestration.json',
                   'execution_provenance.json','independent_review.json'}
_CASE_ARTIFACTS = {'arrays.npz','child_started.json','observables.json',
                   'stderr.txt','stdout.jsonl','supervision.json'}


def expected_parent_files() -> set[str]:
    return _ROOT_ARTIFACTS | {f'{case}/{file}' for case in CASES
                              for file in _CASE_ARTIFACTS}


def _strict_json(path: Path) -> dict:
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:
                raise ValueError(f'duplicate JSON key in {path.name}: {key}')
            result[key]=value
        return result
    return json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=unique)


def parent_inventory() -> dict:
    """Verify the complete frozen parent bytes and original math sources."""
    if parent_runner.sha(PARENT/'completed_artifacts.json') != PARENT_COMPLETE_SHA:
        raise ValueError('frozen parent completed inventory digest changed')
    completed = _strict_json(PARENT/'completed_artifacts.json')
    if (set(completed) != {'files','scope'} or
            set(completed['files']) != expected_parent_files() or
            len(completed['files']) != 36):
        raise ValueError('frozen parent 36-file inventory changed')
    all_entries=list(PARENT.rglob('*'))
    if PARENT.is_symlink() or any(entry.is_symlink() for entry in all_entries):
        raise ValueError('frozen parent contains symlinked path')
    resolved_parent=PARENT.resolve()
    for entry in all_entries:
        try:
            entry.resolve().relative_to(resolved_parent)
        except ValueError as exc:
            raise ValueError('frozen parent path resolves outside root') from exc
    directories={str(entry.relative_to(PARENT)).replace('\\','/')
                 for entry in all_entries if entry.is_dir()}
    if directories!=set(CASES):
        raise ValueError('frozen parent directory inventory changed')
    actual = {str(file.relative_to(PARENT)).replace('\\','/')
              for file in all_entries if file.is_file()}
    if actual != expected_parent_files() | {'completed_artifacts.json'}:
        raise ValueError('frozen parent on-disk inventory changed')
    for relative,digest in completed['files'].items():
        if type(digest) is not str or len(digest)!=64 or not all(
                c in '0123456789abcdef' for c in digest):
            raise ValueError(f'invalid parent digest at {relative}')
        if parent_runner.sha(PARENT/relative) != digest:
            raise ValueError(f'frozen parent artifact changed: {relative}')
    if (completed['files']['registration.json']!=PARENT_REGISTRATION_SHA or
            completed['files']['adjudication.json']!=PARENT_ADJUDICATION_SHA):
        raise ValueError('original registration or failed decision changed')
    registration = parent_runner.read(PARENT/'registration.json')
    decision = parent_runner.read(PARENT/'adjudication.json')
    import _b3_e4_f03_primal_checks as checks
    if (registration['identity']['dependencies']!=supervisor._versions() or
            registration['identity']['python']!=sys.version or
            registration['identity']['executable']!=str(Path(sys.executable).resolve()) or
            registration['identity']['platform']!=platform.platform() or
            registration['identity']['machine']!=platform.machine() or
            registration['threads']!={name:'1' for name in supervisor.THREADS} or
            registration['limits']['numerical']!=checks.LIMITS):
        raise ValueError('original dependencies, thread caps or numerical limits changed')
    if (registration['identity']['head']!=PARENT_HEAD or
            registration['cases']!=CASES or
            decision['status']!=ORIGINAL_TERMINAL or
            set(decision['cases'])!=set(CASES) or
            any(row['status']!=ORIGINAL_TERMINAL for row in decision['cases'].values()) or
            decision['registration_sha256']!=PARENT_REGISTRATION_SHA or
            parent_runner.sha(PARENT/'registration.json')!=PARENT_REGISTRATION_SHA):
        raise ValueError('original source identity, cases or decision changed')
    original_sources = registration['identity']['sources']
    for relative, digest in original_sources.items():
        try:
            blob=subprocess.check_output(('git','show',
                f'{PARENT_HEAD}:{relative}'),cwd=ROOT,stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as exc:
            raise ValueError(f'frozen original source blob unavailable: {relative}') from exc
        if hashlib.sha256(blob).hexdigest()!=digest:
            raise ValueError(f'original source blob mismatch: {relative}')
        if relative == 'scripts/b3_e4_f03_primal_ritz.py':
            continue  # Only the reviewed JSON scalar comparator changed.
        if parent_runner.sha(ROOT/relative) != digest:
            raise ValueError(f'frozen mathematical source changed: {relative}')
    if original_sources['scripts/b3_e4_f03_primal_ritz.py'] != (
            '572541996e74aa001c9a57f25662b3aab428299228e3823f9068a3f96c60a8ff'):
        raise ValueError('original comparator identity changed')
    if parent_runner.sha(ROOT/'scripts/b3_e4_f03_primal_ritz.py')!=CORRECTED_READER_SHA:
        raise ValueError('reviewed JSON comparator source changed')
    return {'root':PARENT_RELATIVE,
            'completed_artifacts_sha256':PARENT_COMPLETE_SHA,
            'registration_sha256':PARENT_REGISTRATION_SHA,
            'adjudication_sha256':PARENT_ADJUDICATION_SHA,
            'original_head':PARENT_HEAD,'original_terminal':ORIGINAL_TERMINAL,
            'original_identity':registration['identity'],
            'artifact_hashes':completed['files'],
            'reviewed_comparator_sha256':CORRECTED_READER_SHA}


def contract() -> dict:
    import _b3_e4_f03_primal_checks as checks
    return {'kind':KIND,'cases':CASES,'scope':SCOPE,
            'identity':supervisor._identity(),'parent':parent_inventory(),
            'threads':{name:'1' for name in supervisor.THREADS},
            'limits':{'seconds_per_case':MAX_SECONDS,
                      'rss_bytes_per_case':MAX_RSS_BYTES,
                      'launch_cutoff_seconds':LAUNCH_CUTOFF_SECONDS,
                      'numerical':checks.LIMITS},
            'work':{'equilibrium_solves_per_case':0,
                    'element_evaluations_per_case':0,
                    'integration_assemblies_per_case':0,
                    'assembly_descriptions_per_case':0},
            'terminal':['FAILED_EVIDENCE','FAILED_EXECUTION',
                        'FAILED_NUMERICAL_SCREEN',
                        'AUDIT_COMPLETE_NOT_REFERENCE_ACCEPTANCE']}


def register(root: Path) -> None:
    if root.resolve()!=AUDIT.resolve() or not supervisor._clean():
        raise ValueError('saved audit requires clean frozen source and exact new root')
    manifest=contract()
    manifest['created_utc']=datetime.now(timezone.utc).isoformat()
    root.mkdir(parents=True,exist_ok=False)
    supervisor._json_new(root/'registration.json',manifest)
    with (root/'registration.sha256').open('x',encoding='ascii') as stream:
        stream.write(parent_runner.sha(root/'registration.json')+'\n')


def registered(root: Path) -> dict:
    if root.resolve()!=AUDIT.resolve():
        raise ValueError('saved audit root changed')
    supervisor._registration_hash(root)
    manifest=parent_runner.read(root/'registration.json')
    frozen=contract()
    if (set(manifest)!=set(frozen)|{'created_utc'} or
            {k:v for k,v in manifest.items() if k!='created_utc'}!=frozen or
            not datetime.fromisoformat(manifest['created_utc']).tzinfo):
        raise ValueError('saved audit identity, parent inventory or contract changed')
    return manifest


@contextmanager
def forbid_scientific_construction():
    """Trap assembly, pose construction, recovery and equilibrium entrypoints."""
    import _b3_e4_f03_primal_ritz as operators
    import _b3_e4_f03_primal_checks as checks
    import numpy as np
    names={'operators':(operators,('assemble','pose_operators','solve',
              'recover_interface','recover_support_wrenches','basis',
              '_shell_stiffness','_beam_stiffness','_load','_scaled_system')),
           'checks':(checks,('evaluate_case','_lift_actions')),
           'numpy':(np.linalg,('solve',))}
    originals=[]
    def forbidden(*args,**kwargs):
        raise AssertionError('saved-only authority forbids construction or solve')
    try:
        for _,(module,entrypoints) in names.items():
            for name in entrypoints:
                if hasattr(module,name):
                    originals.append((module,name,getattr(module,name)))
                    setattr(module,name,forbidden)
        yield
    finally:
        for module,name,value in reversed(originals):
            setattr(module,name,value)


def reproduce_case(name: str, manifest: dict) -> dict:
    """Re-evaluate original receipts/archive, retaining the original verdict."""
    if name not in CASES:
        raise ValueError('unknown saved audit case')
    original=parent_runner.read(PARENT/'adjudication.json')['cases'][name]
    with forbid_scientific_construction():
        reproduced,_=parent_runner.verify_case(PARENT,name,
            parent_runner.read(PARENT/'registration.json'))
    if reproduced['status'] not in ('PASSED_NUMERICAL_SCREEN',
                                    'FAILED_NUMERICAL_SCREEN'):
        raise ValueError('parent raw case did not reproduce a numerical screen')
    return {'original_decision':original,'reproduced_decision':reproduced,
            'parent_arrays_sha256':manifest['parent']['artifact_hashes'][
                name+'/arrays.npz'],
            'equilibrium_solves':0,'element_evaluations':0,
            'integration_assemblies':0,'assembly_descriptions':0,'scope':SCOPE}


def observable_event(directory: Path,name: str,spec: dict,
                     capture_state: bool) -> dict:
    if name not in CASES or spec!=CASES[name] or capture_state is not False:
        raise ValueError('unregistered saved-audit event')
    manifest=registered(directory.parent)
    return {'phase':'observables','case':name,
            'sha256':parent_runner.sha(directory/'observables.json'),
            'parent_arrays_sha256':manifest['parent']['artifact_hashes'][
                name+'/arrays.npz'],
            'child_started_sha256':parent_runner.sha(directory/'child_started.json')}


def _single_threaded(pools: object) -> bool:
    return (isinstance(pools,list) and len(pools)>0 and all(
        isinstance(pool,dict) and type(pool.get('num_threads')) is int and
        pool['num_threads']==1 for pool in pools))


def child(root: Path,name: str) -> None:
    manifest=registered(root)
    if name not in CASES or any(os.environ.get(k)!='1' for k in supervisor.THREADS):
        raise ValueError('unregistered child or numerical thread setting')
    directory=root/name
    supervisor._json_new(directory/'child_started.json',{'case':name,
        'registration_sha256':supervisor._registration_hash(root),
        'pid':os.getpid(),'started_unix_seconds':time.time()})
    from threadpoolctl import threadpool_info
    pools=threadpool_info()
    if not _single_threaded(pools):
        raise ValueError('saved-audit numerical pools must be single-threaded')
    print(json.dumps({'phase':'identity','case':name,
        'identity':manifest['identity'],
        'registration_sha256':supervisor._registration_hash(root),
        'threadpools':pools}),flush=True)
    supervisor._json_new(directory/'observables.json',reproduce_case(name,manifest))
    print(json.dumps(observable_event(directory,name,CASES[name],False)),flush=True)


def verify_audit_case(root: Path,name: str,manifest: dict) -> dict:
    directory=root/name
    receipt=parent_runner.read(directory/'supervision.json')
    if (set(receipt)!={'reason','exit_code','elapsed_seconds',
                      'sampled_peak_rss_bytes','phases','registration_sha256',
                      'failure','observables_sha256'} or
            receipt['registration_sha256']!=supervisor._registration_hash(root)):
        raise ValueError('saved-audit supervisor receipt invalid')
    elapsed=receipt['elapsed_seconds'];rss=receipt['sampled_peak_rss_bytes']
    if (type(receipt['reason']) is not str or not receipt['reason'] or
            (type(receipt['exit_code']) is not int and
             receipt['exit_code'] is not None) or
            type(elapsed) not in (int,float) or not math.isfinite(elapsed) or
            elapsed<0 or type(rss) is not int or rss<0 or
            not isinstance(receipt['phases'],list) or
            any(type(phase) is not str for phase in receipt['phases']) or
            (receipt['failure'] is not None and
             type(receipt['failure']) is not str)):
        raise ValueError('malformed saved-audit supervisor resource receipt')
    if (receipt['reason']=='completed' and
            (receipt['failure'] is not None or
             type(receipt['exit_code']) is not int or receipt['exit_code']!=0 or
             elapsed>MAX_SECONDS or rss>MAX_RSS_BYTES)):
        raise ValueError('contradictory completed saved-audit receipt')
    if receipt['reason']!='completed' or receipt['exit_code']!=0:
        return {'status':'FAILED_EXECUTION','receipt':receipt}
    marker=parent_runner.read(directory/'child_started.json')
    event=observable_event(directory,name,CASES[name],False)
    events=[json.loads(line) for line in
            (directory/'stdout.jsonl').read_text(encoding='utf-8').splitlines()]
    if (set(marker)!={'case','registration_sha256','pid','started_unix_seconds'} or
            marker['case']!=name or marker['registration_sha256']!=
            supervisor._registration_hash(root) or
            type(marker['pid']) is not int or marker['pid']<=0 or
            type(marker['started_unix_seconds']) not in (int,float) or
            not math.isfinite(marker['started_unix_seconds']) or
            receipt['phases']!=['identity','observables'] or
            receipt['observables_sha256']!=event['sha256'] or
            len(events)!=2 or not all(isinstance(e,dict) for e in events) or
            events[0].get('phase')!='identity' or events[0].get('case')!=name or
            events[0].get('identity')!=manifest['identity'] or
            events[0].get('registration_sha256')!=supervisor._registration_hash(root) or
            not _single_threaded(events[0].get('threadpools')) or
            events[1]!=event):
        raise ValueError('saved-audit raw receipt, child identity or event invalid')
    observed=parent_runner.read(directory/'observables.json')
    recomputed=reproduce_case(name,manifest)
    parent_runner.bind_metrics(observed,recomputed)
    if (set(observed)!=set(recomputed) or
            observed['equilibrium_solves']!=0 or
            observed['element_evaluations']!=0 or
            observed['integration_assemblies']!=0 or
            observed['assembly_descriptions']!=0 or
            observed['scope']!=SCOPE or
            observed['parent_arrays_sha256']!=
            manifest['parent']['artifact_hashes'][name+'/arrays.npz']):
        raise ValueError('saved-audit observations changed')
    return {'status':recomputed['reproduced_decision']['status'],
            'original_decision':recomputed['original_decision'],
            'reproduced_decision':recomputed['reproduced_decision'],
            'parent_arrays_sha256':recomputed['parent_arrays_sha256']}


def adjudicate(root: Path) -> bool:
    manifest=registered(root)
    if any(not (root/name/'supervision.json').is_file() for name in CASES):
        raise ValueError('complete five-case audit receipts required')
    decisions={}
    for name in CASES:
        try:
            decisions[name]=verify_audit_case(root,name,manifest)
        except (OSError,ValueError,KeyError,TypeError,IndexError,AttributeError,
                EOFError,zipfile.BadZipFile) as exc:
            decisions[name]={'status':'FAILED_EVIDENCE',
                             'reason':f'{type(exc).__name__}: {exc}'}
    status=next((candidate for candidate in ('FAILED_EVIDENCE',
        'FAILED_EXECUTION','FAILED_NUMERICAL_SCREEN') if any(
        row['status']==candidate for row in decisions.values())),
        'AUDIT_COMPLETE_NOT_REFERENCE_ACCEPTANCE')
    integrity=('PASSED' if all(row['status'] in
        ('FAILED_NUMERICAL_SCREEN','PASSED_NUMERICAL_SCREEN')
        for row in decisions.values()) else 'FAILED')
    supervisor._json_new(root/'adjudication.json',{
        'registration_sha256':supervisor._registration_hash(root),
        'identity':manifest['identity'],'status':status,
        'audit_integrity':integrity,'cases':decisions,
        'original_terminal':ORIGINAL_TERMINAL,
        'parent_adjudication_sha256':PARENT_ADJUDICATION_SHA,
        'physical_trends':None,'scope':SCOPE})
    print(json.dumps({'status':status,'audit_integrity':integrity,
          'cases':{k:v['status'] for k,v in decisions.items()}},sort_keys=True))
    return status=='AUDIT_COMPLETE_NOT_REFERENCE_ACCEPTANCE'


def configure() -> None:
    supervisor.ROOT=ROOT
    supervisor.CASES=CASES
    supervisor.RUNNER=Path(__file__).resolve()
    supervisor.SOURCES=tuple(ROOT/'scripts'/name for name in SOURCES)+(
        ROOT/'docs/agent_plans/B3_GE_E4_PL_G0_F03_PRIMAL_SAVED_AUDIT_PROTOCOL.md',)
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
                raise TimeoutError('saved-audit launch cutoff; evidence incomplete')
            ok=supervisor.execute(root,name)
            completed.append({'case':name,'execution_completed':ok})
            if not ok:
                receipt=parent_runner.read(root/name/'supervision.json')
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
            'supervisor_thread_caps':{k:os.environ.get(k) for k in supervisor.THREADS}})


def main() -> int:
    if any(os.environ.get(k)!='1' for k in supervisor.THREADS):
        raise ValueError('all supervisor and child thread caps must equal one')
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    for flag in ('run-all','register','execute','adjudicate','child'):
        group.add_argument('--'+flag,action='store_true')
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--case',choices=CASES)
    args=parser.parse_args()
    if (args.execute or args.child)!=bool(args.case):
        parser.error('--case required only for execute or child')
    configure()
    root=args.root.resolve()
    if args.run_all:
        return 0 if run_once(root) else 1
    if args.register:
        register(root);return 0
    if args.execute:
        return 0 if supervisor.execute(root,args.case) else 1
    if args.adjudicate:
        return 0 if adjudicate(root) else 1
    child(root,args.case)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
