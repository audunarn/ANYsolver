"""One-use three-case exact attribution of frozen Ritz pose coefficients.

This saved-input diagnostic has no equilibrium, stiffness assembly, fresh
reaction recovery, projection or Green-norm authority. Its result cannot
accept the previously failed numerical or physical reference.
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

import b3_e4_f03_area_feasibility as supervisor
import b3_e4_f03_primal_ritz as original
import b3_e4_f03_primal_saved_audit as saved


ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'.qualification'/'b3-ge-e4-pl'
PARENT=BASE/'f03-primal-ritz-v1'
AUDIT=BASE/'f03-primal-saved-audit-v1'
TARGET=BASE/'f03-primal-exact-pose-v1'
CASES={name:original.CASES[name] for name in ('n12','n16','n24')}
MAX_SECONDS=300
MAX_RSS_BYTES=1024**3
LAUNCH_CUTOFF_SECONDS=1200
MAX_JSON_BYTES=16*1024**2
KIND='experimental-primal-exact-saved-pose-v1'
SCOPE=('exact represented-binary64 pose attribution of saved states only; '
       'original FAILED_EVIDENCE and saved-audit numerical HOLD retained')
AUDIT_HEAD='c8b2f78d3ace4e23ed8f636fd6b474ef250ccda6'
AUDIT_REGISTRATION_SHA='62dd4f7bdb2001471603c7b45fc2a3adc709a9bf06ab49e075def1407cc5389a'
AUDIT_ADJUDICATION_SHA='27ffa25aa390f8d83a579430015d49eb86fb9df6ada654d492aec5a20e478935'
AUDIT_REVIEW_SHA='a9b61c230d417d5c1004725cc87ba1bab59882de88c52dcdee0a966cdd62dec8'
AUDIT_COMPLETE_SHA='5073230a813bf9acef534d756ac05fb7deb29d1f7cf7caae507db94afc99014d'
AUDIT_ROOT_FILES={'adjudication.json','execution_provenance.json',
                  'independent_review.json','orchestration.json',
                  'pre_execution_review.json','registration.json',
                  'registration.sha256'}
AUDIT_CASE_FILES={'child_started.json','observables.json','stderr.txt',
                  'stdout.jsonl','supervision.json'}
SOURCES=('b3_e4_f03_primal_exact_pose.py','_b3_e4_f03_primal_exact_pose.py',
         '_b3_e4_f03_primal_exact_checks.py','b3_e4_f03_primal_saved_audit.py',
         'b3_e4_f03_primal_ritz.py','b3_e4_f03_area_feasibility.py',
         '_b3_e4_f03_primal_archive.py','_b3_e4_f03_primal_checks.py',
         '_b3_e4_f03_primal_functional.py','_b3_e4_f03_primal_ritz.py',
         '_b3_e4_f03_primal_trends.py')
WORK={'equilibrium_solves':0,'element_evaluations':0,
      'integration_assemblies':0,'assembly_descriptions':0,
      'projection_constructions':0,'reaction_recoveries':0,
      'green_norm_evaluations':0}


def _strict_json(path: Path) -> dict:
    if path.stat().st_size>MAX_JSON_BYTES:
        raise ValueError('exact-pose JSON exceeds 16MiB')
    def unique(pairs):
        result={}
        for key,value in pairs:
            if key in result:
                raise ValueError(f'duplicate exact-pose JSON key: {key}')
            result[key]=value
        return result
    def reject_constant(value):
        raise ValueError(f'nonfinite JSON token {value}')
    return json.loads(path.read_text(encoding='utf-8'),
                      object_pairs_hook=unique,parse_constant=reject_constant)


def expected_audit_files() -> set[str]:
    return AUDIT_ROOT_FILES | {f'{case}/{file}' for case in original.CASES
                               for file in AUDIT_CASE_FILES}


def audit_inventory() -> dict:
    """Bind all 32 audit artifacts and their original registered sources."""
    if original.sha(AUDIT/'completed_artifacts.json')!=AUDIT_COMPLETE_SHA:
        raise ValueError('saved-audit completed inventory hash changed')
    completed=_strict_json(AUDIT/'completed_artifacts.json')
    if (set(completed)!={'files','scope'} or
            set(completed['files'])!=expected_audit_files() or
            len(completed['files'])!=32):
        raise ValueError('saved-audit 32-file inventory changed')
    entries=list(AUDIT.rglob('*'))
    if AUDIT.is_symlink() or any(entry.is_symlink() for entry in entries):
        raise ValueError('saved-audit symlinked path')
    resolved=AUDIT.resolve()
    for entry in entries:
        try:
            entry.resolve().relative_to(resolved)
        except ValueError as exc:
            raise ValueError('saved-audit path resolves outside root') from exc
    if ({str(path.relative_to(AUDIT)).replace('\\','/')
         for path in entries if path.is_dir()}!=set(original.CASES) or
        {str(path.relative_to(AUDIT)).replace('\\','/')
         for path in entries if path.is_file()}!=
            expected_audit_files()|{'completed_artifacts.json'}):
        raise ValueError('saved-audit on-disk inventory changed')
    for relative,digest in completed['files'].items():
        if (type(digest) is not str or len(digest)!=64 or
            any(char not in '0123456789abcdef' for char in digest) or
            original.sha(AUDIT/relative)!=digest):
            raise ValueError(f'saved-audit artifact changed: {relative}')
    if (completed['files']['registration.json']!=AUDIT_REGISTRATION_SHA or
        completed['files']['adjudication.json']!=AUDIT_ADJUDICATION_SHA or
        completed['files']['independent_review.json']!=AUDIT_REVIEW_SHA):
        raise ValueError('saved-audit registration, decision or review changed')
    registration=_strict_json(AUDIT/'registration.json')
    decision=_strict_json(AUDIT/'adjudication.json')
    if (registration['identity']['head']!=AUDIT_HEAD or
            registration['cases']!=original.CASES or
            registration['identity']['dependencies']!=supervisor._versions() or
            registration['identity']['python']!=sys.version or
            registration['identity']['executable']!=str(Path(sys.executable).resolve()) or
            registration['identity']['platform']!=platform.platform() or
            registration['identity']['machine']!=platform.machine() or
            registration['threads']!={key:'1' for key in supervisor.THREADS} or
            decision['registration_sha256']!=AUDIT_REGISTRATION_SHA or
            decision['status']!='FAILED_NUMERICAL_SCREEN' or
            decision['audit_integrity']!='PASSED' or
            decision['original_terminal']!='FAILED_EVIDENCE' or
            set(decision['cases'])!=set(original.CASES)):
        raise ValueError('saved-audit source, dependencies or terminal changed')
    for relative,digest in registration['identity']['sources'].items():
        if original.sha(ROOT/relative)!=digest:
            raise ValueError(f'saved-audit frozen source changed: {relative}')
    return {'root':'.qualification/b3-ge-e4-pl/f03-primal-saved-audit-v1',
            'head':AUDIT_HEAD,'registration_sha256':AUDIT_REGISTRATION_SHA,
            'adjudication_sha256':AUDIT_ADJUDICATION_SHA,
            'independent_review_sha256':AUDIT_REVIEW_SHA,
            'completed_artifacts_sha256':AUDIT_COMPLETE_SHA,
            'artifact_hashes':completed['files'],
            'identity':registration['identity']}


def contract() -> dict:
    return {'kind':KIND,'cases':CASES,'scope':SCOPE,
            'identity':supervisor._identity(),
            'original_parent':saved.parent_inventory(),
            'saved_audit':audit_inventory(),
            'threads':{key:'1' for key in supervisor.THREADS},
            'limits':{'seconds_per_case':MAX_SECONDS,
                      'rss_bytes_per_case':MAX_RSS_BYTES,
                      'launch_cutoff_seconds':LAUNCH_CUTOFF_SECONDS,
                      'observables_json_bytes':MAX_JSON_BYTES},
            'work':WORK,'terminal':['FAILED_EVIDENCE','FAILED_EXECUTION',
                'FAILED_DIAGNOSTIC_IDENTITY',
                'PASSED_REPRESENTATION_DIAGNOSTIC']}


def register(root: Path) -> None:
    if root.resolve()!=TARGET.resolve() or not supervisor._clean():
        raise ValueError('exact-pose registration requires clean source and exact new root')
    manifest=contract()
    manifest['created_utc']=datetime.now(timezone.utc).isoformat()
    root.mkdir(parents=True,exist_ok=False)
    supervisor._json_new(root/'registration.json',manifest)
    with (root/'registration.sha256').open('x',encoding='ascii') as stream:
        stream.write(original.sha(root/'registration.json')+'\n')


def registered(root: Path) -> dict:
    if root.resolve()!=TARGET.resolve():
        raise ValueError('exact-pose registration root changed')
    supervisor._registration_hash(root)
    manifest=_strict_json(root/'registration.json')
    frozen=contract()
    if (set(manifest)!=set(frozen)|{'created_utc'} or
            {k:v for k,v in manifest.items() if k!='created_utc'}!=frozen or
            not datetime.fromisoformat(manifest['created_utc']).tzinfo):
        raise ValueError('exact-pose registration identity or inputs changed')
    return manifest


@contextmanager
def forbid_original_recomputation():
    """Trap all original construction and unrelated numerical verification."""
    import numpy as np
    import _b3_e4_f03_primal_checks as checks
    import _b3_e4_f03_primal_functional as functional
    imports=((checks,('verify_saved','_project_b','_virtual_work',
                      '_derived_density','_section_from_b')),
             (functional,('norm_squared','green_inner',
                          'from_gauss_density','band_wrench',
                          'band_wrench_analytic')),
             (original,('verify_case','adjudicate')),
             (np.linalg,('solve',)))
    originals=[]
    def forbidden(*args,**kwargs):
        raise AssertionError('exact-pose diagnostic forbids original recomputation')
    with saved.forbid_scientific_construction():
        try:
            for module,names in imports:
                for name in names:
                    originals.append((module,name,getattr(module,name)))
                    setattr(module,name,forbidden)
            yield
        finally:
            for module,name,value in reversed(originals):
                setattr(module,name,value)


def _original_arrays(name: str,manifest: dict) -> dict:
    import _b3_e4_f03_primal_archive as archive
    if name not in CASES:
        raise ValueError('unknown exact-pose case')
    path=PARENT/name/'arrays.npz'
    if original.sha(path)!=manifest['original_parent']['artifact_hashes'][
            name+'/arrays.npz']:
        raise ValueError('original solved-state archive changed')
    return archive.unpack(path,CASES[name]['degree'])


def _audit_decision(name: str,manifest: dict) -> dict:
    if original.sha(AUDIT/'adjudication.json')!=manifest['saved_audit'][
            'adjudication_sha256']:
        raise ValueError('saved-audit decision changed')
    case=_strict_json(AUDIT/'adjudication.json')['cases'][name]
    if (case['original_decision']['status']!='FAILED_EVIDENCE' or
            case['status'] not in ('FAILED_NUMERICAL_SCREEN',
                                   'PASSED_NUMERICAL_SCREEN') or
            case['reproduced_decision']['status']!=case['status'] or
            case['parent_arrays_sha256']!=manifest['original_parent'][
                'artifact_hashes'][name+'/arrays.npz']):
        raise ValueError('saved-audit case identity changed')
    return case


def make_observations(name: str,manifest: dict) -> dict:
    """One saved-only exact construction and immediate arithmetic selfcheck."""
    import _b3_e4_f03_primal_exact_checks as exact_checks
    n=CASES[name]['degree']
    arrays=_original_arrays(name,manifest)
    audit_case=_audit_decision(name,manifest)
    with forbid_original_recomputation():
        record=exact_checks.evaluate_saved(n,arrays,audit_case)
        checked=exact_checks.verify_saved_record(record,n,arrays,audit_case)
    exact_checks._identical(record,checked)
    if (type(checked) is not dict or checked.get('diagnostic_status') not in
            ('PASSED_REPRESENTATION_DIAGNOSTIC',
             'FAILED_DIAGNOSTIC_IDENTITY')):
        raise ValueError('invalid exact-pose arithmetic diagnostic status')
    return _envelope(name,manifest,audit_case,checked)


def _envelope(name: str,manifest: dict,audit_case: dict,
              diagnostic: dict) -> dict:
    return {'case':name,'degree':CASES[name]['degree'],'diagnostic':diagnostic,
            'original_decision':audit_case['original_decision'],
            'saved_audit_decision':audit_case,
            'parent_arrays_sha256':audit_case['parent_arrays_sha256'],
            'original_registration_sha256':manifest['original_parent'][
                'registration_sha256'],
            'saved_audit_registration_sha256':manifest['saved_audit'][
                'registration_sha256'],
            'work':WORK,'scope':SCOPE}


def _json_new_limited(path: Path,payload: dict) -> None:
    encoded=json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+'\n'
    if len(encoded.encode('utf-8'))>MAX_JSON_BYTES:
        raise ValueError('exact-pose observables exceed 16MiB')
    with path.open('x',encoding='utf-8') as stream:
        stream.write(encoded)


def observable_event(directory: Path,name: str,spec: dict,
                     capture_state: bool) -> dict:
    if name not in CASES or spec!=CASES[name] or capture_state is not False:
        raise ValueError('unregistered exact-pose event')
    manifest=registered(directory.parent)
    return {'phase':'observables','case':name,
            'sha256':original.sha(directory/'observables.json'),
            'parent_arrays_sha256':manifest['original_parent'][
                'artifact_hashes'][name+'/arrays.npz'],
            'child_started_sha256':original.sha(directory/'child_started.json')}


def child(root: Path,name: str) -> None:
    manifest=registered(root)
    if name not in CASES or any(os.environ.get(k)!='1' for k in supervisor.THREADS):
        raise ValueError('unregistered exact-pose child or thread setting')
    directory=root/name
    supervisor._json_new(directory/'child_started.json',{'case':name,
        'registration_sha256':supervisor._registration_hash(root),
        'pid':os.getpid(),'started_unix_seconds':time.time()})
    from threadpoolctl import threadpool_info
    pools=threadpool_info()
    if not saved._single_threaded(pools):
        raise ValueError('exact-pose numerical pools must be single-threaded')
    print(json.dumps({'phase':'identity','case':name,
        'identity':manifest['identity'],
        'registration_sha256':supervisor._registration_hash(root),
        'threadpools':pools}),flush=True)
    _json_new_limited(directory/'observables.json',make_observations(name,manifest))
    print(json.dumps(observable_event(directory,name,CASES[name],False)),flush=True)


def verify_case(root: Path,name: str,manifest: dict) -> dict:
    directory=root/name
    receipt=_strict_json(directory/'supervision.json')
    if (set(receipt)!={'reason','exit_code','elapsed_seconds',
                      'sampled_peak_rss_bytes','phases','registration_sha256',
                      'failure','observables_sha256'} or
            receipt['registration_sha256']!=supervisor._registration_hash(root)):
        raise ValueError('exact-pose supervisor receipt invalid')
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
        raise ValueError('malformed exact-pose resource receipt')
    if (receipt['reason']=='completed' and
            (receipt['failure'] is not None or
             type(receipt['exit_code']) is not int or receipt['exit_code']!=0 or
             elapsed>MAX_SECONDS or rss>MAX_RSS_BYTES)):
        raise ValueError('contradictory completed exact-pose receipt')
    if receipt['reason']!='completed':
        return {'status':'FAILED_EXECUTION','receipt':receipt}
    marker=_strict_json(directory/'child_started.json')
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
            len(events)!=2 or not all(isinstance(e,dict) for e in events) or
            events[0].get('phase')!='identity' or events[0].get('case')!=name or
            events[0].get('identity')!=manifest['identity'] or
            events[0].get('registration_sha256')!=
            supervisor._registration_hash(root) or
            not saved._single_threaded(events[0].get('threadpools')) or
            events[1]!=event):
        raise ValueError('exact-pose child identity, receipt or event invalid')
    observed=_strict_json(directory/'observables.json')
    if (set(observed)!={'case','degree','diagnostic','original_decision',
                        'saved_audit_decision','parent_arrays_sha256',
                        'original_registration_sha256',
                        'saved_audit_registration_sha256','work','scope'} or
            observed['work']!=WORK or observed['scope']!=SCOPE):
        raise ValueError('exact-pose observation inventory changed')
    import _b3_e4_f03_primal_exact_checks as exact_checks
    arrays=_original_arrays(name,manifest)
    audit_case=_audit_decision(name,manifest)
    with forbid_original_recomputation():
        checked=exact_checks.verify_saved_record(observed['diagnostic'],
            CASES[name]['degree'],arrays,audit_case)
    if (type(checked) is not dict or checked.get('diagnostic_status') not in
            ('PASSED_REPRESENTATION_DIAGNOSTIC',
             'FAILED_DIAGNOSTIC_IDENTITY')):
        raise ValueError('invalid verified exact-pose diagnostic status')
    expected=_envelope(name,manifest,audit_case,checked)
    exact_checks._identical(observed,expected)
    return {'status':expected['diagnostic']['diagnostic_status'],
            'parent_arrays_sha256':expected['parent_arrays_sha256'],
            'original_decision':expected['original_decision'],
            'saved_audit_decision':expected['saved_audit_decision'],
            'diagnostic':expected['diagnostic']}


def adjudicate(root: Path) -> bool:
    manifest=registered(root)
    if any(not (root/name/'supervision.json').is_file() for name in CASES):
        raise ValueError('complete three-case exact-pose receipt inventory required')
    decisions={}
    for name in CASES:
        try:
            decisions[name]=verify_case(root,name,manifest)
        except (OSError,ValueError,KeyError,TypeError,IndexError,AttributeError,
                EOFError,zipfile.BadZipFile) as exc:
            decisions[name]={'status':'FAILED_EVIDENCE',
                             'reason':f'{type(exc).__name__}: {exc}'}
    status=next((candidate for candidate in ('FAILED_EVIDENCE',
        'FAILED_EXECUTION','FAILED_DIAGNOSTIC_IDENTITY') if any(
        row['status']==candidate for row in decisions.values())),
        'PASSED_REPRESENTATION_DIAGNOSTIC')
    supervisor._json_new(root/'adjudication.json',{
        'registration_sha256':supervisor._registration_hash(root),
        'identity':manifest['identity'],'status':status,'cases':decisions,
        'original_terminal':'FAILED_EVIDENCE',
        'saved_audit_terminal':'FAILED_NUMERICAL_SCREEN',
        'saved_audit_integrity':'PASSED','work':WORK,'scope':SCOPE})
    print(json.dumps({'status':status,'cases':{
        k:v['status'] for k,v in decisions.items()}},sort_keys=True))
    return status=='PASSED_REPRESENTATION_DIAGNOSTIC'


def configure() -> None:
    supervisor.ROOT=ROOT
    supervisor.CASES=CASES
    supervisor.RUNNER=Path(__file__).resolve()
    supervisor.SOURCES=tuple(ROOT/'scripts'/name for name in SOURCES)+(
        ROOT/'docs/agent_plans/B3_GE_E4_PL_G0_F03_PRIMAL_EXACT_POSE_PROTOCOL.md',
        ROOT/'docs/agent_plans/B3_GE_E4_PL_G0_F03_PRIMAL_NEXT_DIAGNOSTIC_DRAFT.md')
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
                raise TimeoutError('exact-pose launch cutoff; evidence incomplete')
            ok=supervisor.execute(root,name)
            completed.append({'case':name,'execution_completed':ok})
            if not ok:
                receipt=_strict_json(root/name/'supervision.json')
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
    child(root,args.case);return 0


if __name__=='__main__':
    raise SystemExit(main())
