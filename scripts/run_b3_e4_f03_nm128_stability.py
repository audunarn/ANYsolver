"""Single-use supervised source-frozen F03 classical stability diagnostic.

The four cases require a separate reviewed execution registration. Running
this file without one does not turn finite beta into F03 qualification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
import psutil
import scipy
from threadpoolctl import threadpool_info

import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell
import _b3_e4_f03_kkt_scaling as scaling
import _b3_e4_f03_nm128_stability as stability


CASES={'q4-nm64':('Q4',64),'q4-nm128':('Q4',128),
       'cb-nm64':('CST-CB',64),'cb-nm128':('CST-CB',128)}
MAX_RSS=8*1024**3
MAX_SECONDS=900
SOURCES=(Path(__file__),Path(beam.__file__),Path(line.__file__),
         Path(shell.__file__),Path(scaling.__file__),Path(stability.__file__))


def _hashes() -> dict[str,str]:
    return {str(path.resolve()):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in SOURCES}


def _record(value: dict) -> None:
    print(json.dumps(value,allow_nan=False,sort_keys=True),flush=True)


def _child(case: str,manifest_path: Path) -> int:
    registered=json.loads(manifest_path.read_text(encoding='utf-8'))
    registration_path=Path(registered['registration_path'])
    qualification=json.loads(registration_path.read_text(encoding='utf-8'))
    if (_hashes()!=registered['sources'] or case!=registered['case'] or
            qualification['runner_source_hashes']!=registered['sources'] or
            hashlib.sha256(registration_path.read_bytes()).hexdigest()!=
                registered['registration_sha256'] or
            any(os.environ.get(key)!=value for key,value in
                registered['threads'].items())):
        raise ValueError('source, case or thread identity changed')
    process=psutil.Process()
    pools=threadpool_info()
    if not pools or any(item.get('num_threads')!=1 for item in pools):
        raise ValueError('stability preflight requires observed single-thread pools')
    _record(dict(phase='identity',sources=_hashes(),
                 threads={key:os.environ[key] for key in registered['threads']},
                 threadpools=pools,
                 modules={name:str(Path(module.__file__).resolve())
                          for name,module in (('numpy',np),('scipy',scipy),
                                              ('psutil',psutil))},
                 rss_bytes=process.memory_info().rss))
    topology,nm=CASES[case]
    start=time.perf_counter()
    measures,matrices=stability.analyze(128,64,512,nm,topology,
                                        retain_matrices=True)
    payload=manifest_path.parent/'schur.npz'
    np.savez(payload,**matrices)
    _record(dict(phase='stability',case=case,measures=measures,
                 payload_sha256=hashlib.sha256(payload.read_bytes()).hexdigest(),
                 elapsed_seconds=time.perf_counter()-start,
                 rss_bytes=process.memory_info().rss))
    return 0 if measures['numerical_checks_pass'] else 2


def _supervise(case: str,directory: Path,
               registration_path: Path | None=None) -> int:
    if registration_path is None:
        raise ValueError('reviewed registration is required before execution')
    checkout=Path(__file__).resolve().parents[1]
    def git(*args: str) -> str:
        return subprocess.run(('git',*args),cwd=checkout,check=True,
                              capture_output=True,text=True).stdout.strip()
    head=git('rev-parse','HEAD')
    if git('status','--porcelain'):
        raise ValueError('stability diagnostic requires committed clean source')
    sources=_hashes()
    registration_path=registration_path.resolve()
    registered=json.loads(registration_path.read_text(encoding='utf-8'))
    expected=[sys.executable,str(Path(__file__).resolve()),'--case',case,
              '--output',str(directory.resolve()),'--registration',
              str(registration_path)]
    expected_commands=[
        [sys.executable,str(Path(__file__).resolve()),'--case',name,
         '--output',str((directory.parent/name).resolve()),'--registration',
         str(registration_path)] for name in CASES]
    if (registered['kind']!='F03_NM128_SUPPORTED_STABILITY_V1' or
            registered['execution_head']!=head or
            registered['cases']!=list(CASES) or
            registered['runner_source_hashes']!=sources or
            registered['runner_path']!=str(Path(__file__).resolve()) or
            registered['python_executable']!=sys.executable or
            registered['commands']!=expected_commands or
            registered['commands'][list(CASES).index(case)]!=expected or
            registered['limits']!=dict(max_rss_bytes=MAX_RSS,
                                       max_seconds=MAX_SECONDS) or
            registered['adjudicator_sha256']!=hashlib.sha256(
                Path(__file__).with_name(
                    'adjudicate_b3_e4_f03_nm128_stability.py').read_bytes()
            ).hexdigest() or
            not registered['dependency_file_sha256'] or
            any(hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest
                for path,digest in registered['dependency_file_sha256'].items())):
        raise ValueError('registration or source identity changed')
    manifest_path=directory/'manifest.json'
    command=[sys.executable,'-u',str(Path(__file__).resolve()),'--child',
             '--case',case,'--expected-manifest',str(manifest_path.resolve())]
    environment=os.environ.copy()
    environment.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',
                       MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',
                       PYTHONDONTWRITEBYTECODE='1')
    threads={key:environment[key] for key in
             ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS',
              'MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}
    if threads!=registered['threads']:
        raise ValueError('registered thread settings changed')
    if registered['runtime']!=dict(python=sys.version,numpy=np.__version__,
                                   scipy=scipy.__version__,
                                   psutil=psutil.__version__,
                                   platform=platform.platform()):
        raise ValueError('registered runtime changed')
    if registered['module_paths']!={name:str(Path(module.__file__).resolve())
                                    for name,module in (('numpy',np),
                                    ('scipy',scipy),('psutil',psutil))}:
        raise ValueError('registered module paths changed')
    directory.mkdir(parents=True,exist_ok=False)
    manifest=dict(kind='F03_NM128_SUPPORTED_STABILITY_V1',case=case,
                  mesh=dict(n_s=128,n_y=64,n_beam=512,
                            n_mortar=CASES[case][1]),
                  topology=CASES[case][0],source_commit=head,
                  source_dirty=False,sources=sources,threads=threads,
                  registration_path=str(registration_path),
                  registration_sha256=hashlib.sha256(
                      registration_path.read_bytes()).hexdigest(),
                  command=command,
                  limits=dict(max_rss_bytes=MAX_RSS,max_seconds=MAX_SECONDS),
                  python=sys.version,numpy=np.__version__,
                  scipy=scipy.__version__,psutil=psutil.__version__,
                  platform=platform.platform())
    manifest_path.write_text(json.dumps(manifest,indent=2,sort_keys=True),
                             encoding='utf-8')
    begun=time.monotonic();peak=0;reason='process_exit';failure=None
    child=None;code=None;records=[];malformed=[]
    try:
        with (directory/'phases.jsonl').open('wb') as stdout, \
             (directory/'stderr.log').open('wb') as stderr, \
             (directory/'rss.jsonl').open('w',encoding='utf-8') as samples:
            child=subprocess.Popen(command,cwd=checkout,env=environment,
                                   stdout=stdout,stderr=stderr)
            tracked=psutil.Process(child.pid)
            while child.poll() is None:
                elapsed=time.monotonic()-begun
                try:
                    rss=tracked.memory_info().rss
                except psutil.NoSuchProcess:
                    rss=0
                peak=max(peak,rss)
                samples.write(json.dumps(dict(elapsed_seconds=elapsed,
                                              rss_bytes=rss))+'\n')
                if rss>MAX_RSS or elapsed>MAX_SECONDS:
                    reason='rss_limit' if rss>MAX_RSS else 'time_limit'
                    child.kill()
                    break
                time.sleep(.1)
    except BaseException as exc:
        reason='supervisor_error'
        failure=f'{type(exc).__name__}: {exc}'
    finally:
        if child is not None:
            if child.poll() is None:
                child.kill()
            code=child.wait()
        path=directory/'phases.jsonl'
        if path.exists():
            for number,row in enumerate(path.read_text(
                    encoding='utf-8',errors='replace').splitlines(),1):
                try:
                    parsed=json.loads(row)
                    if (not isinstance(parsed,dict) or
                            not isinstance(parsed.get('rss_bytes'),int) or
                            parsed['rss_bytes']<0 or
                            not isinstance(parsed.get('phase'),str)):
                        malformed.append(number)
                    else:
                        records.append(parsed)
                except (ValueError,TypeError):
                    malformed.append(number)
        peak=max([peak]+[record['rss_bytes'] for record in records])
        elapsed=time.monotonic()-begun
        post=_hashes()
        post_head=None;post_dirty=None;post_checkout_error=None
        try:
            post_head=git('rev-parse','HEAD')
            post_dirty=bool(git('status','--porcelain'))
        except (OSError,subprocess.SubprocessError) as exc:
            post_checkout_error=f'{type(exc).__name__}: {exc}'
        if reason=='process_exit':
            phases=[row.get('phase') for row in records]
            identity=(not malformed and phases==['identity','stability'] and
                      records[0].get('sources')==sources and
                      records[0].get('threads')==threads and
                      isinstance(records[0].get('threadpools'),list) and
                      bool(records[0]['threadpools']) and
                      all(isinstance(pool,dict) and
                          pool.get('num_threads')==1 for pool in
                          records[0]['threadpools']) and post==sources and
                      (directory/'schur.npz').is_file() and
                      records[-1].get('payload_sha256')==
                      hashlib.sha256((directory/'schur.npz').read_bytes()).hexdigest())
            if peak>MAX_RSS:
                reason='rss_limit'
            elif elapsed>MAX_SECONDS:
                reason='time_limit'
            elif (post_head!=head or post_dirty is not False or
                  post_checkout_error is not None):
                reason='source_checkout_changed'
            elif not identity:
                reason='identity_or_phase_failure'
            elif code==2:
                reason='numerical_failure'
            elif code!=0:
                reason='child_failure'
        result=dict(reason=reason,exit_code=code,
                    elapsed_seconds=elapsed,sampled_peak_rss_bytes=peak,
                    completed_phases=[row.get('phase') for row in records],
                    malformed_phase_lines=malformed,
                    post_source_hashes=post,post_head=post_head,
                    post_dirty=post_dirty,
                    post_checkout_error=post_checkout_error,
                    failure=failure)
        (directory/'result.json').write_text(
            json.dumps(result,indent=2,sort_keys=True),encoding='utf-8')
    print(json.dumps(dict(evidence=str(directory.resolve()),
                          reason=reason,exit_code=code,
                          elapsed_seconds=elapsed,
                          sampled_peak_rss_bytes=peak),sort_keys=True))
    return 0 if reason=='process_exit' and code==0 else 1


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--case',choices=CASES,required=True)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--registration',type=Path)
    parser.add_argument('--child',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--expected-manifest',type=Path,help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.child:
        if args.expected_manifest is None:
            parser.error('--expected-manifest is required for child')
        return _child(args.case,args.expected_manifest)
    if args.output is None:
        parser.error('--output is required for supervised execution')
    if args.registration is None:
        parser.error('--registration is required for supervised execution')
    return _supervise(args.case,args.output,args.registration)


if __name__=='__main__':
    raise SystemExit(main())
