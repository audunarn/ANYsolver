"""One-use, source-bound pure H1 norm validation; no structural solves.

Registers before work, supervises its own child, preserves each completed
Nm prefix, and independently checks the nine recorded metric rows.
"""

from __future__ import annotations

import argparse
from datetime import datetime,timezone
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


ROOT=Path(__file__).resolve().parents[1]
RUNNER=Path(__file__).resolve()
SOURCES=tuple(ROOT/'scripts'/name for name in (
    'b3_e4_f03_analytical_norm_study.py','_b3_e4_f03_norm_validation.py',
    '_b3_e4_f03_trace_dual_exact.py','_b3_e4_f03_trace_green_oracle.py',
    '_b3_e4_f03_trace_dual.py'))
THREADS=('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS',
         'NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS')
COUNTS=(4,8,16)
FAMILIES=('P1','hybrid','enriched')
LIMITS={'relative_skew':1e-12,'relative_frobenius_error':1e-12,
        'relative_operator_error':1e-9,'oracle_operator_change':1e-12,
        'analytical_identity_error':1e-12}
RESOURCES={'seconds':120,'sampled_rss_bytes':512*1024**2}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(path: Path,payload: object) -> None:
    with path.open('x',encoding='utf-8') as stream:
        json.dump(payload,stream,indent=2,sort_keys=True,allow_nan=False)
        stream.write('\n')


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def git(*args: str) -> str:
    return subprocess.check_output(('git',*args),cwd=ROOT,text=True,
                                   stderr=subprocess.DEVNULL).strip()


def identity() -> dict:
    return {'head':git('rev-parse','HEAD'),'accepted_main':git('rev-parse','main'),
            'sources':{p.relative_to(ROOT).as_posix():sha(p) for p in SOURCES},
            'python':sys.version,'executable':str(Path(sys.executable).resolve()),
            'platform':platform.platform(),
            'dependencies':{name:importlib.metadata.version(name) for name in
                            ('numpy','scipy','psutil','threadpoolctl')}}


def checked_registration(root: Path) -> tuple[dict,str]:
    digest=sha(root/'registration.json')
    if digest!=(root/'registration.sha256').read_text().strip():
        raise ValueError('registration hash mismatch')
    manifest=read(root/'registration.json')
    if (manifest['identity']!=identity() or manifest['counts']!=list(COUNTS) or
            manifest['families']!=list(FAMILIES) or manifest['criteria']!=LIMITS or
            manifest['resources']!=RESOURCES or manifest['oracle_orders']!=[12,16] or
            manifest['oracle_decimal_digits']!=70 or manifest['threads']!={k:'1' for k in THREADS}):
        raise ValueError('frozen norm contract changed')
    return manifest,digest


def child(root: Path) -> None:
    manifest,digest=checked_registration(root)
    if any(os.environ.get(k)!='1' for k in THREADS):
        raise ValueError('single-thread environment required')
    write_new(root/'child_started.json',{'registration_sha256':digest,
              'created_utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid()})
    import numpy as np
    from threadpoolctl import threadpool_info
    import _b3_e4_f03_norm_validation as validation
    pools=threadpool_info()
    if not pools or any(p['num_threads']!=1 for p in pools) or validation.LIMITS!=LIMITS:
        raise ValueError('thread or numerical criteria mismatch')
    print(json.dumps({'phase':'identity','identity':manifest['identity'],
                      'registration_sha256':digest,'threadpools':pools}),flush=True)
    artifacts={}
    for n in COUNTS:
        result,grams=validation.compare(n)
        archive=root/f'n{n}_grams.npz'
        with archive.open('xb') as stream:
            np.savez_compressed(stream,**grams)
        result['grams_sha256']=sha(archive)
        result['registration_sha256']=digest
        write_new(root/f'n{n}.json',result)
        artifacts[f'n{n}.json']=sha(root/f'n{n}.json')
        artifacts[archive.name]=sha(archive)
    checked_registration(root)
    write_new(root/'completed_artifacts.json',artifacts)
    print(json.dumps({'phase':'completed','artifact_inventory_sha256':
                      sha(root/'completed_artifacts.json')}),flush=True)


def adjudicate(root: Path,receipt: dict) -> bool:
    manifest,digest=checked_registration(root)
    if (receipt!=read(root/'supervision.json') or receipt['registration_sha256']!=digest or
            not isinstance(receipt['elapsed_seconds'],(int,float)) or
            not math.isfinite(receipt['elapsed_seconds']) or receipt['elapsed_seconds']<0 or
            type(receipt['sampled_peak_rss_bytes']) is not int or receipt['sampled_peak_rss_bytes']<0):
        raise ValueError('invalid or unbound supervisor receipt')
    if receipt['reason']!='completed' or receipt['exit_code']!=0 or receipt['failure'] is not None:
        write_new(root/'adjudication.json',{'status':'FAILED_EXECUTION','supervision':receipt})
        return False
    if (receipt['elapsed_seconds']>RESOURCES['seconds'] or
            receipt['sampled_peak_rss_bytes']>RESOURCES['sampled_rss_bytes']):
        raise ValueError('completed receipt exceeds registered resource limits')
    events=[json.loads(line) for line in (root/'stdout.jsonl').read_text().splitlines()]
    if (len(events)!=2 or not all(isinstance(e,dict) for e in events) or
            events[0].get('phase')!='identity' or events[0].get('identity')!=manifest['identity'] or
            events[0].get('registration_sha256')!=digest or not events[0].get('threadpools') or
            any(p.get('num_threads')!=1 for p in events[0]['threadpools']) or
            events[1]!={'phase':'completed','artifact_inventory_sha256':sha(root/'completed_artifacts.json')}):
        raise ValueError('raw child identity or completion event mismatch')
    artifacts=read(root/'completed_artifacts.json')
    if set(artifacts)!={f'n{n}{suffix}' for n in COUNTS for suffix in ('.json','_grams.npz')}:
        raise ValueError('incomplete pure-norm evidence inventory')
    if any(sha(root/name)!=artifact_hash for name,artifact_hash in artifacts.items()):
        raise ValueError('raw norm artifact changed')
    cases={}
    for n in COUNTS:
        result=read(root/f'n{n}.json')
        if (result['n_mortar']!=n or result['registration_sha256']!=digest or
                set(result['families'])!=set(FAMILIES) or
                result['grams_sha256']!=artifacts[f'n{n}_grams.npz']):
            raise ValueError('norm result identity mismatch')
        grams=verify_grams(root/f'n{n}_grams.npz',n)
        recomputed=saved_metrics(n,grams)
        for family in FAMILIES:
            values=result['families'][family]['measurements']
            if set(values)!=set(LIMITS) or any(not isinstance(v,(int,float)) or
                                               not math.isfinite(v) or v<0 for v in values.values()):
                raise ValueError('invalid norm-validation metric')
            if any(not math.isclose(values[k],recomputed[family][k],rel_tol=1e-10,abs_tol=1e-16)
                   for k in LIMITS):
                raise ValueError('reported metrics disagree with saved Gram matrices')
            values=recomputed[family]
            passed=all(values[k]<=limit for k,limit in LIMITS.items())
            status='PASSED_AUXILIARY_NORM_VALIDATION' if passed else 'FAILED_AUXILIARY_NORM_VALIDATION'
            if result['families'][family]['status']!=status:
                raise ValueError('reported norm status differs from frozen criteria')
            cases[f'n{n}_{family}']={'status':status,'measurements':values}
    passed=all(r['status']=='PASSED_AUXILIARY_NORM_VALIDATION' for r in cases.values())
    write_new(root/'adjudication.json',{'identity':manifest['identity'],
              'registration_sha256':digest,'cases':cases,
              'status':'PASSED_PURE_NORM_STUDY' if passed else 'FAILED_PURE_NORM_STUDY',
              'scope':manifest['scope']})
    return passed


def verify_grams(path: Path,n: int) -> dict:
    import numpy as np
    expected={'green12_enriched':n+3,'green16_enriched':n+3}
    expected.update({family+suffix:(n+3 if family=='enriched' else n+1)
                     for family in FAMILIES for suffix in ('_analytic','_fe32','_fe64')})
    matrices={}
    with np.load(path,allow_pickle=False) as saved:
        if set(saved.files)!=set(expected):
            raise ValueError('incomplete saved Gram inventory')
        for name,count in expected.items():
            value=saved[name]
            if (value.shape!=(count,count) or value.dtype!=np.dtype('float64') or
                    not np.all(np.isfinite(value))):
                raise ValueError('invalid saved Gram layout or values')
            matrices[name]=value
    return matrices


def saved_metrics(n: int,grams: dict) -> dict:
    """Recompute predicates from recorded arrays only; no norm constructions."""
    import numpy as np
    from scipy import linalg
    from _b3_e4_f03_norm_validation import relative_operator_error
    canonical=grams['enriched_analytic']
    measure=np.full(n+1,1/n);measure[[0,-1]]*=.5
    endpoint=np.array(((1/np.tanh(1.),1/np.sinh(1.)),
                       (1/np.sinh(1.),1/np.tanh(1.))))
    identity_error=max(float(np.max(np.abs(canonical[-2:,-2:]-endpoint))),
                       abs(float(measure@canonical[:n+1,:n+1]@measure)-1),
                       float(np.max(np.abs(measure@canonical[:n+1,-2:]-1))))
    result={}
    for family in FAMILIES:
        selected=(list(range(n+1)) if family=='P1' else
                  list(range(1,n))+[n+1,n+2] if family=='hybrid' else list(range(n+3)))
        a=grams[family+'_analytic']
        b=grams['green16_enriched'][np.ix_(selected,selected)]
        earlier=grams['green12_enriched'][np.ix_(selected,selected)]
        linalg.cholesky(a,lower=True);linalg.cholesky(b,lower=True)
        result[family]={
            'relative_skew':float(np.linalg.norm(a-a.T)/np.linalg.norm(a)),
            'relative_frobenius_error':float(np.linalg.norm(a-b)/np.linalg.norm(b)),
            'relative_operator_error':relative_operator_error(a,b),
            'oracle_operator_change':relative_operator_error(earlier,b),
            'analytical_identity_error':identity_error}
    return result


def run(root: Path) -> bool:
    if any(os.environ.get(k)!='1' for k in THREADS):
        raise ValueError('single-thread supervisor environment required before registration')
    if git('status','--porcelain'):
        raise ValueError('clean committed norm candidate required')
    root.relative_to(ROOT/'.qualification/b3-ge-e4-pl')
    manifest={'kind':'pure-analytical-trace-norm-validation-v1',
              'created_utc':datetime.now(timezone.utc).isoformat(),'identity':identity(),
              'counts':list(COUNTS),'families':list(FAMILIES),'criteria':LIMITS,
              'resources':RESOURCES,'oracle_orders':[12,16],'oracle_decimal_digits':70,
              'threads':{k:'1' for k in THREADS},
              'scope':'auxiliary norm only; no structural solve or retroactive endpoint-comparison acceptance'}
    root.mkdir(parents=True,exist_ok=False)
    write_new(root/'registration.json',manifest)
    (root/'registration.sha256').write_text(sha(root/'registration.json')+'\n',encoding='ascii')
    env=os.environ.copy();env.update(manifest['threads'])
    started=time.monotonic();peak=0;process=None;reason='unknown';failure=None;code=None
    try:
        with (root/'stdout.jsonl').open('x',encoding='utf-8') as out, \
                (root/'stderr.txt').open('x',encoding='utf-8') as err:
            process=subprocess.Popen((sys.executable,str(RUNNER),'--root',str(root),'--child'),
                                     cwd=ROOT,env=env,stdout=out,stderr=err)
            watched=psutil.Process(process.pid)
            while process.poll() is None:
                try:
                    peak=max(peak,watched.memory_info().rss)
                except psutil.NoSuchProcess:
                    if process.poll() is not None:
                        break
                    raise
                if peak>RESOURCES['sampled_rss_bytes'] or time.monotonic()-started>RESOURCES['seconds']:
                    reason='rss_limit' if peak>RESOURCES['sampled_rss_bytes'] else 'time_limit'
                    process.kill();break
                time.sleep(.1)
    except BaseException as exc:
        reason='supervisor_failure';failure=f'{type(exc).__name__}: {exc}'
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
            code=process.wait()
    elapsed=time.monotonic()-started
    if reason=='unknown':
        reason='completed' if code==0 else 'child_failure'
    if reason=='completed' and elapsed>RESOURCES['seconds']:
        reason='time_limit'
    receipt={'reason':reason,'exit_code':code,'failure':failure,'elapsed_seconds':elapsed,
             'sampled_peak_rss_bytes':peak,'registration_sha256':sha(root/'registration.json')}
    write_new(root/'supervision.json',receipt)
    try:
        passed=adjudicate(root,receipt)
    except BaseException as exc:
        write_new(root/'adjudication_failure.json',{'error':f'{type(exc).__name__}: {exc}'})
        raise
    print(json.dumps({'passed':passed,'registered_rows':9,'root':str(root),'elapsed_seconds':elapsed}))
    return passed


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--child',action='store_true')
    args=parser.parse_args()
    if args.child:
        child(args.root.resolve())
    else:
        raise SystemExit(0 if run(args.root.resolve()) else 1)
