"""Source-bound, resource-supervised finite-pad classical F03 feasibility pilot.

This is a bounded diagnostic for a *different physical connection* from the
four-point reference. It does not qualify a physical continuum reference,
native element coupling, or a later G0B/G1 gate.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import psutil


HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
SOURCES=tuple(HERE/name for name in (
    'b3_e4_f03_area_feasibility.py',
    '_b3_e4_f03_area_loaded.py',
    '_b3_e4_f03_area_line.py',
    '_b3_e4_f03_area_port.py',
    '_b3_e4_f03_independent_beam.py',
    '_b3_e4_f03_independent_line.py',
    '_b3_e4_f03_independent_shell.py',
    '_b3_e4_f03_kkt_scaling.py'))
CASES={
    'q4_coarse': ('Q4',4,8,8,4),
    'cst_cb_coarse': ('CST-CB',4,8,8,4),
    'q4_terminal': ('Q4',8,16,16,8),
    'cst_cb_terminal': ('CST-CB',8,16,16,8),
}
HALFWIDTH_M=.05  # Four separate 0.1 m square material pads.
MAX_SECONDS=900
MAX_RSS_BYTES=8*1024**3
THREADS=('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
         'NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS')
LIMITS={'free_residual_scaled':1e-8,'weak_gap_scaled':1e-9,
        'balance_scaled_absolute_max':1e-8,'energy_scaled':1e-8}


def _hashes() -> dict[str,str]:
    return {str(p.relative_to(ROOT)).replace('\\','/'):
            hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCES}


def _head() -> str:
    return subprocess.check_output(('git','rev-parse','HEAD'),cwd=ROOT,
                                   text=True,stderr=subprocess.DEVNULL).strip()


def _accepted_main() -> str:
    return subprocess.check_output(('git','rev-parse','main'),cwd=ROOT,
                                   text=True,stderr=subprocess.DEVNULL).strip()


def _clean() -> bool:
    return not subprocess.check_output(('git','status','--porcelain'),cwd=ROOT,
                                       text=True,stderr=subprocess.DEVNULL).strip()


def _versions() -> dict[str,str]:
    return {name:importlib.metadata.version(name) for name in
            ('numpy','scipy','psutil','threadpoolctl')}


def _json_new(path: Path, payload: object) -> None:
    with path.open('x',encoding='utf-8') as stream:
        json.dump(payload,stream,indent=2,sort_keys=True,allow_nan=False)
        stream.write('\n')


def _registration_hash(root: Path) -> str:
    raw=(root/'registration.json').read_bytes()
    digest=hashlib.sha256(raw).hexdigest()
    if (root/'registration.sha256').read_text(encoding='ascii').strip()!=digest:
        raise ValueError('registration content hash mismatch')
    return digest


def _identity() -> dict:
    return {'head':_head(),'accepted_main':_accepted_main(),
            'sources':_hashes(),'dependencies':_versions(),
            'python':sys.version,'executable':str(Path(sys.executable).resolve()),
            'platform':platform.platform(),'machine':platform.machine()}


def register(root: Path) -> None:
    if not _clean():
        raise ValueError('commit candidate before registering diagnostic evidence')
    identity=_identity()
    try:
        root.relative_to(ROOT/'.qualification'/'b3-ge-e4-pl')
    except ValueError as exc:
        raise ValueError('diagnostic evidence must reside under ignored qualification root') from exc
    root.mkdir(parents=True,exist_ok=False)
    _json_new(root/'registration.json',{
        'kind':'experimental-classical-finite-pad-feasibility-v1',
        'created_utc':datetime.now(timezone.utc).isoformat(),
        'identity':identity,
        'physical_model':{
            'description':'four separate 0.1 m square material pads, 0.1 m matching the declared classical beam section width; separate idealization from four-point comparator',
            'halfwidth_m':HALFWIDTH_M,
            'pad_centers_m':[[dx,dy] for dx in (-.2,.2) for dy in (-.23,.23)],
            'beam_section_area_m2':.01,
            'beam_section_width_m':.1,
            'load':'smooth', 'mortar':'P1',
            'equivalence_claim':'none: beam section dimensions alone do not establish connection geometry'},
        'cases':{name:{'topology':v[0],'n_s':v[1],'n_y':v[2],
                       'n_beam':v[3],'n_mortar':v[4]}
                 for name,v in CASES.items()},
        'threads':{name:'1' for name in THREADS},
        'limits':{'seconds_per_case':MAX_SECONDS,
                  'rss_bytes_per_case':MAX_RSS_BYTES,'numerical':LIMITS},
        'scope':'resource and algebraic screen; all physical channels diagnostic only; G0B stays open',
        'terminal':'case failure remains in immutable evidence; no retries in this registration'})
    (root/'registration.sha256').write_text(
        hashlib.sha256((root/'registration.json').read_bytes()).hexdigest()+'\n',
        encoding='ascii')


def _registered(root: Path) -> dict:
    _registration_hash(root)
    manifest=json.loads((root/'registration.json').read_text(encoding='utf-8'))
    expected_cases={name:{'topology':v[0],'n_s':v[1],'n_y':v[2],
                          'n_beam':v[3],'n_mortar':v[4]}
                    for name,v in CASES.items()}
    if (set(manifest)!={'kind','created_utc','identity','physical_model',
                       'cases','threads','limits','scope','terminal'} or
            manifest['kind']!='experimental-classical-finite-pad-feasibility-v1' or
            not datetime.fromisoformat(manifest['created_utc']).tzinfo or
            manifest['scope']!='resource and algebraic screen; all physical channels diagnostic only; G0B stays open' or
            manifest['terminal']!='case failure remains in immutable evidence; no retries in this registration' or
            manifest['identity']!=_identity() or
            manifest['threads']!={name:'1' for name in THREADS} or
            manifest['limits']!={'seconds_per_case':MAX_SECONDS,
                                'rss_bytes_per_case':MAX_RSS_BYTES,
                                'numerical':LIMITS} or
            manifest['cases']!=expected_cases or
            manifest['physical_model']!={
                'description':'four separate 0.1 m square material pads, 0.1 m matching the declared classical beam section width; separate idealization from four-point comparator',
                'halfwidth_m':HALFWIDTH_M,
                'pad_centers_m':[[dx,dy] for dx in (-.2,.2) for dy in (-.23,.23)],
                'beam_section_area_m2':.01,'beam_section_width_m':.1,
                'load':'smooth','mortar':'P1',
                'equivalence_claim':'none: beam section dimensions alone do not establish connection geometry'}):
        raise ValueError('registered source, environment or protocol changed')
    return manifest


def child(root: Path, name: str) -> None:
    manifest=_registered(root)
    if any(os.environ.get(key)!='1' for key in THREADS):
        raise ValueError('child thread environment differs from registration')
    import numpy as np
    from threadpoolctl import threadpool_info
    import _b3_e4_f03_area_loaded as loaded
    pools=threadpool_info()
    if any(p['num_threads']!=1 for p in pools):
        raise ValueError('child numerical thread pool is not single-threaded')
    spec=manifest['cases'][name]
    print(json.dumps({'phase':'identity','case':name,'identity':_identity(),
                      'registration_sha256':_registration_hash(root),
                      'threadpools':pools}),flush=True)
    result=loaded.solve(spec['n_s'],spec['n_y'],spec['n_beam'],
                        spec['n_mortar'],spec['topology'],'P1','smooth',
                        HALFWIDTH_M)
    data=asdict(result)
    data['energy_scaled']=abs(2*(result.shell_energy_j+result.beam_energy_j)+
                              result.interface_work_j-result.external_work_j)/loaded.scaling.E0
    if not all(np.isfinite(v) for v in (data['energy_scaled'],
                                       result.free_residual_scaled,
                                       result.weak_gap_scaled)):
        raise ValueError('nonfinite feasibility metrics')
    _json_new(root/name/'observables.json',data)
    print(json.dumps({'phase':'observables','case':name,
                      'sha256':hashlib.sha256((root/name/'observables.json').read_bytes()).hexdigest()}),
          flush=True)


def execute(root: Path, name: str) -> bool:
    manifest=_registered(root)
    registered_digest=_registration_hash(root)
    if name not in CASES or not _clean():
        raise ValueError('unknown case or dirty registered candidate')
    directory=root/name
    directory.mkdir(exist_ok=False)
    env=os.environ.copy()
    env.update(manifest['threads'])
    begun=time.monotonic()
    reason='unknown'
    sampled_peak=0
    code=None
    process=None
    failure=None
    try:
        with (directory/'stdout.jsonl').open('x',encoding='utf-8') as out, \
                (directory/'stderr.txt').open('x',encoding='utf-8') as err:
            process=subprocess.Popen((sys.executable,str(Path(__file__).resolve()),
                                      '--child','--root',str(root),'--case',name),
                                     cwd=ROOT,env=env,stdout=out,stderr=err)
            watched=psutil.Process(process.pid)
            while process.poll() is None:
                try:
                    sampled_peak=max(sampled_peak,watched.memory_info().rss)
                except psutil.NoSuchProcess:
                    if process.poll() is not None:
                        break
                    raise
                elapsed=time.monotonic()-begun
                if sampled_peak>MAX_RSS_BYTES or elapsed>MAX_SECONDS:
                    reason='rss_limit' if sampled_peak>MAX_RSS_BYTES else 'time_limit'
                    process.kill()
                    break
                time.sleep(.1)
    except BaseException as exc:
        reason='supervisor_failure'
        failure=f'{type(exc).__name__}: {exc}'
    finally:
        if process is not None:
            if process.poll() is None:
                try:
                    process.kill()
                except ProcessLookupError:
                    pass
            code=process.wait()
    elapsed=time.monotonic()-begun
    events=[]
    observations=directory/'observables.json'
    digest=None
    try:
        stdout_path=directory/'stdout.jsonl'
        lines=(stdout_path.read_text(encoding='utf-8',errors='replace').splitlines()
               if stdout_path.exists() else [])
        events=[json.loads(line) for line in lines]
        if not all(isinstance(event,dict) for event in events):
            raise ValueError('non-object child event')
        digest=(hashlib.sha256(observations.read_bytes()).hexdigest()
                if observations.exists() else None)
        if reason=='unknown':
            reason=('completed' if code==0 and len(events)==2 and
                    events[0].get('phase')=='identity' and
                    events[0].get('identity')==manifest['identity'] and
                    events[0].get('case')==name and
                    events[0].get('registration_sha256')==registered_digest and
                    all(pool.get('num_threads')==1 for pool in
                        events[0].get('threadpools',[])) and
                    events[1].get('phase')=='observables' and
                    events[1].get('case')==name and
                    events[1].get('sha256')==digest and digest is not None and
                    _identity()==manifest['identity'] and
                    sampled_peak<=MAX_RSS_BYTES and elapsed<=MAX_SECONDS
                    else 'identity_phase_or_process_failure')
    except BaseException as exc:
        reason='supervisor_failure'
        failure=f'{type(exc).__name__}: {exc}'
    summary={'reason':reason,'exit_code':code,'elapsed_seconds':elapsed,
             'sampled_peak_rss_bytes':sampled_peak,
             'phases':[event.get('phase') for event in events],
             'registration_sha256':registered_digest,
             'failure':failure,
             'observables_sha256':digest}
    _json_new(directory/'supervision.json',summary)
    print(json.dumps({'case':name,**summary},sort_keys=True))
    return reason=='completed'


def adjudicate(root: Path) -> bool:
    manifest=_registered(root)
    if any(not (root/name/'supervision.json').is_file()
           for name in manifest['cases']):
        raise ValueError('all registered case receipts required before final adjudication')
    import _b3_e4_f03_kkt_scaling as scaling
    decision={}
    for name in manifest['cases']:
        try:
            directory=root/name
            summary=json.loads((directory/'supervision.json').read_text(encoding='utf-8'))
            if summary['registration_sha256']!=_registration_hash(root):
                raise ValueError('supervision registration mismatch')
            if summary['reason']!='completed':
                decision[name]={'status':'FAILED','reason':summary['reason']}
                continue
            if (summary['exit_code']!=0 or
                    summary['phases']!=['identity','observables'] or
                    not math.isfinite(summary['elapsed_seconds']) or
                    not 0<=summary['elapsed_seconds']<=MAX_SECONDS or
                    not isinstance(summary['sampled_peak_rss_bytes'],int) or
                    not 0<=summary['sampled_peak_rss_bytes']<=MAX_RSS_BYTES):
                raise ValueError('invalid completed supervision')
            lines=(directory/'stdout.jsonl').read_text(encoding='utf-8').splitlines()
            events=[json.loads(line) for line in lines]
            path=directory/'observables.json'
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            if (len(events)!=2 or not all(isinstance(x,dict) for x in events) or
                    events[0].get('phase')!='identity' or
                    events[0].get('case')!=name or
                    events[0].get('identity')!=manifest['identity'] or
                    events[0].get('registration_sha256')!=_registration_hash(root) or
                    not isinstance(events[0].get('threadpools'),list) or
                    any(pool.get('num_threads')!=1 for pool in
                        events[0]['threadpools']) or
                    events[1]!={'phase':'observables','case':name,'sha256':digest} or
                    summary['observables_sha256']!=digest):
                raise ValueError('raw child identity, thread or hash mismatch')
            values=json.loads(path.read_text(encoding='utf-8'))
            if (values['topology']!=manifest['cases'][name]['topology'] or
                    values['law']!='P1' or values['loading']!='smooth' or
                    values['halfwidth_m']!=HALFWIDTH_M or
                    len(values['balance_scaled'])!=3 or
                    len(values['support_wrenches'])!=3 or
                    len(values['beam_port_quarter_wrenches'])!=4):
                raise ValueError('observables case contract mismatch')
            energy=abs(2*(values['shell_energy_j']+values['beam_energy_j'])+
                       values['interface_work_j']-values['external_work_j'])/scaling.E0
            support=values['support_wrenches']
            balance=[sum(w[j] for w in support)/
                     (scaling.M0 if j==2 else scaling.F0)+
                     (1. if j==1 else .5 if j==2 else 0.)
                     for j in range(3)]
            root=[values['beam_root_elastic_wrench'][j]+
                  values['beam_root_port_wrench'][j]-
                  values['beam_root_load_wrench'][j] for j in range(3)]
            if (not math.isclose(energy,values['energy_scaled'],
                                 rel_tol=1e-10,abs_tol=1e-12) or
                    any(not math.isclose(balance[j],values['balance_scaled'][j],
                                         rel_tol=1e-10,abs_tol=1e-12)
                        for j in range(3)) or
                    any(not math.isclose(root[j],support[2][j],
                                         rel_tol=1e-10,abs_tol=1e-5)
                        for j in range(3))):
                raise ValueError('raw energy, support balance or root partition disagrees')
            measurements={'free_residual_scaled':values['free_residual_scaled'],
                          'weak_gap_scaled':values['weak_gap_scaled'],
                          'balance_scaled_absolute_max':max(map(abs,balance)),
                          'energy_scaled':energy}
            if any(not isinstance(value,(int,float)) or
                   not math.isfinite(value) or value<0
                   for value in measurements.values()):
                raise ValueError('nonfinite, negative or invalid numerical metric')
            decision[name]={'status':('PASSED_ALGEBRAIC_SCREEN' if
                                      all(measurements[k]<=v for k,v in LIMITS.items())
                                      else 'FAILED_ALGEBRAIC_SCREEN'),
                            'measurements':measurements}
        except (OSError,ValueError,KeyError,TypeError,IndexError,AttributeError) as exc:
            decision[name]={'status':'FAILED_EVIDENCE',
                            'reason':f'{type(exc).__name__}: {exc}'}
    _json_new(root/'adjudication.json',{
        'identity':manifest['identity'],'cases':decision,
        'scope':'bounded classical feasibility only; physical convergence, native coupling, G0B and G1 unqualified'})
    print(json.dumps(decision,sort_keys=True))
    return all(item['status']=='PASSED_ALGEBRAIC_SCREEN'
               for item in decision.values())


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('register','execute','adjudicate'),nargs='?')
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--case',choices=CASES)
    parser.add_argument('--child',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    root=args.root.resolve()
    if args.child:
        if args.case is None:
            parser.error('--case required for child')
        child(root,args.case)
        return 0
    elif args.action=='register':
        register(root)
        return 0
    elif args.action=='execute':
        if args.case is None:
            parser.error('--case required for execution')
        return 0 if execute(root,args.case) else 1
    elif args.action=='adjudicate':
        return 0 if adjudicate(root) else 1
    else:
        parser.error('action required')


if __name__=='__main__':
    raise SystemExit(main())
