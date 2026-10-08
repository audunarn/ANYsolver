"""Supervised 48-case algebraic row-rank preflight for the F03 comparator.

Row-normalized Euclidean coupling rank is only an algebraic diagnostic. It
does not establish a mechanical inf-sup bound or select a mortar law.
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
from scipy import sparse
from scipy.linalg import svdvals
from threadpoolctl import threadpool_info

import _b3_e4_f03_independent_beam as beam
import _b3_e4_f03_independent_inventory as inventory
import _b3_e4_f03_independent_line as line
import _b3_e4_f03_independent_shell as shell


MAX_RSS=8*1024**3
MAX_TOTAL_SECONDS=7200
MAX_CASE_SECONDS=900
SINGULAR_RATIO_FLOOR=1e-6
SOURCES=(Path(__file__),Path(beam.__file__),Path(inventory.__file__),
         Path(line.__file__),Path(shell.__file__))


def _hashes() -> dict[str,str]:
    return {str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in SOURCES}


def _cases(smoke: bool = False) -> tuple[inventory.Case,...]:
    if smoke:
        return (inventory.Case(inventory.Mesh(3,6,6,3),'Q4','smooth','P1'),)
    result=tuple(case for case in inventory.cases() if case.loading=='smooth')
    if len(result)!=48 or len({case.identity for case in result})!=48:
        raise AssertionError('not exactly 48 load-independent coupling cases')
    return result


def _row_spectrum(case: inventory.Case) -> dict[str,float | int | bool]:
    m=case.mesh
    model=shell.panel(m.n_s,m.n_y,case.topology)
    cs,cb,_=line.coupling(model,m.n_beam,m.n_mortar,case.law)
    free_shell=np.setdiff1d(np.arange(model.dof_count),model.supported)
    free_beam=np.setdiff1d(np.arange(beam.dof_count(m.n_beam)),
                           beam.root_dofs(m.n_beam))
    c=sparse.hstack((-cs[:,free_shell],cb[:,free_beam]),format='csr')
    row_norm=np.sqrt(np.asarray(c.multiply(c).sum(axis=1)).ravel())
    if not np.all(np.isfinite(row_norm)) or np.any(row_norm<=0):
        raise ValueError(f'nonfinite or zero coupling row: {case.identity}')
    normalized=sparse.diags(1/row_norm)@c
    gram=(normalized@normalized.T).toarray()
    skew=float(np.max(np.abs(gram-gram.T)))
    eig=np.linalg.eigvalsh(gram)
    smallest=float(eig[0]); largest=float(eig[-1])
    gram_ratio=float(np.sqrt(max(smallest,0)/largest)) if largest>0 else 0.
    direct_ratio=None
    # Gram squares the condition number. Resolve possible numerical
    # ambiguity around the frozen algebraic cutoff with an independent SVD.
    if gram_ratio<10*SINGULAR_RATIO_FLOOR:
        singular=svdvals(normalized.toarray(),check_finite=False)
        direct_ratio=float(singular[-1]/singular[0])
    ratio=gram_ratio if direct_ratio is None else direct_ratio
    return dict(rows=c.shape[0],columns=c.shape[1],coupling_nnz=c.nnz,
                row_norm_min=float(np.min(row_norm)),
                row_norm_max=float(np.max(row_norm)),
                gram_eigen_min=smallest,gram_eigen_max=largest,
                gram_skew_max=skew,gram_singular_ratio=gram_ratio,
                direct_svd_ratio=direct_ratio,singular_ratio=ratio,
                passes_algebraic_floor=bool(np.isfinite(ratio) and
                                            ratio>=SINGULAR_RATIO_FLOOR))


def _child(manifest_path: Path) -> None:
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    if _hashes()!=manifest['sources']:
        raise ValueError('child sources differ from frozen manifest')
    if any(os.environ.get(name)!=value for name,value in manifest['threads'].items()):
        raise ValueError('child thread environment differs from manifest')
    cases=_cases(manifest['smoke'])
    if [case.identity for case in cases]!=manifest['case_ids']:
        raise ValueError('child inventory differs from manifest')
    pools=threadpool_info()
    print(json.dumps(dict(kind='identity',sources=_hashes(),
                          modules={name:str(Path(module.__file__).resolve())
                                   for name,module in (('numpy',np),('scipy',scipy),
                                                       ('psutil',psutil))},
                          threadpools=pools,threads={name:os.environ[name]
                                                     for name in manifest['threads']}),
                     sort_keys=True),flush=True)
    if any(pool.get('num_threads')!=1 for pool in pools):
        raise ValueError('observed rank-screen thread pool is not single-threaded')
    process=psutil.Process()
    for case in cases:
        print(json.dumps(dict(kind='case_start',case_id=case.identity),sort_keys=True),
              flush=True)
        began=time.perf_counter()
        spectrum=_row_spectrum(case)
        elapsed=time.perf_counter()-began
        print(json.dumps(dict(kind='case',case_id=case.identity,
                              topology=case.topology,law=case.law,
                              mesh=vars(case.mesh),case_seconds=elapsed,
                              rss_bytes=process.memory_info().rss,**spectrum),
                         sort_keys=True),flush=True)
        if elapsed>MAX_CASE_SECONDS:
            raise TimeoutError(f'case time limit: {case.identity}')
        if _hashes()!=manifest['sources']:
            raise ValueError('source changed during rank screen')
    print(json.dumps(dict(kind='complete',count=len(cases),sources=_hashes()),
                     sort_keys=True),flush=True)


def _supervise(directory: Path, smoke: bool = False) -> int:
    checkout=Path(__file__).resolve().parents[1]
    def git(*args: str) -> str:
        return subprocess.run(('git',*args),cwd=checkout,check=True,
                              capture_output=True,text=True).stdout.strip()
    commit=git('rev-parse','HEAD')
    dirty=bool(git('status','--porcelain'))
    if dirty and not smoke:
        raise ValueError('rank screen requires clean committed source')
    directory.mkdir(parents=True,exist_ok=False)
    sources=_hashes()
    path=directory/'manifest.json'
    command=[sys.executable,'-u',str(Path(__file__).resolve()),
             '--child','--expected-manifest',str(path.resolve())]
    environment=os.environ.copy()
    environment.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',
                       MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',
                       PYTHONDONTWRITEBYTECODE='1')
    manifest=dict(purpose='load-independent F03 algebraic row-rank preflight',
                  source_commit=commit,source_dirty=dirty,smoke=smoke,sources=sources,
                  case_ids=[case.identity for case in _cases(smoke)],
                  thresholds=dict(singular_ratio_floor=SINGULAR_RATIO_FLOOR,
                                  max_rss_bytes=MAX_RSS,
                                  max_case_seconds=MAX_CASE_SECONDS,
                                  max_total_seconds=MAX_TOTAL_SECONDS),
                  command=command,python=sys.version,numpy=np.__version__,
                  scipy=scipy.__version__,psutil=psutil.__version__,
                  platform=platform.platform(),
                  threads={key:environment[key] for key in
                           ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS',
                            'MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')})
    path.write_text(json.dumps(manifest,sort_keys=True,indent=2),encoding='utf-8')
    began=time.monotonic(); peak=0; reason='process_exit'; failure=None
    child=None; code=None; records=[]; malformed=[]
    active_id=None; active_since=None
    try:
        with (directory/'records.jsonl').open('wb') as stdout, \
             (directory/'stderr.log').open('wb') as stderr, \
             (directory/'rss.jsonl').open('w',encoding='utf-8') as samples, \
             (directory/'records.jsonl').open('rb') as observe:
            child=subprocess.Popen(command,cwd=checkout,env=environment,
                                   stdout=stdout,stderr=stderr)
            tracked=psutil.Process(child.pid)
            while child.poll() is None:
                elapsed=time.monotonic()-began
                while True:
                    position=observe.tell()
                    entry=observe.readline()
                    if not entry or not entry.endswith(b'\n'):
                        observe.seek(position)
                        break
                    try:
                        record=json.loads(entry)
                    except (ValueError,TypeError):
                        continue
                    if record.get('kind')=='case_start':
                        active_id=record.get('case_id')
                        active_since=time.monotonic()
                    elif record.get('kind')=='case' and record.get('case_id')==active_id:
                        active_id=None; active_since=None
                try:
                    rss=tracked.memory_info().rss
                except psutil.NoSuchProcess:
                    rss=0
                peak=max(peak,rss)
                samples.write(json.dumps(dict(elapsed_seconds=elapsed,rss_bytes=rss))+'\n')
                case_over=(active_since is not None and
                           time.monotonic()-active_since>MAX_CASE_SECONDS)
                if rss>MAX_RSS or elapsed>MAX_TOTAL_SECONDS or case_over:
                    reason=('rss_limit' if rss>MAX_RSS else
                            'total_time_limit' if elapsed>MAX_TOTAL_SECONDS else
                            'case_time_limit')
                    child.kill()
                    break
                time.sleep(.1)
    except BaseException as exc:
        reason='supervisor_error'; failure=f'{type(exc).__name__}: {exc}'
    finally:
        if child is not None:
            if child.poll() is None:
                child.kill()
            code=child.wait()
        saved=directory/'records.jsonl'
        if saved.exists():
            for i,entry in enumerate(saved.read_text(encoding='utf-8',errors='replace').splitlines(),1):
                try:
                    records.append(json.loads(entry))
                except (ValueError,TypeError):
                    malformed.append(i)
        post=_hashes()
        elapsed=time.monotonic()-began
        peak=max([peak]+[record.get('rss_bytes',0) for record in records])
        identities=[record for record in records if record.get('kind')=='identity']
        results=[record for record in records if record.get('kind')=='case']
        starts=[record for record in records if record.get('kind')=='case_start']
        ids=[record.get('case_id') for record in results]
        complete=[record for record in records if record.get('kind')=='complete']
        if reason=='process_exit':
            if peak>MAX_RSS:
                reason='rss_limit'
            elif elapsed>MAX_TOTAL_SECONDS:
                reason='total_time_limit'
            elif (code!=0 or malformed or len(identities)!=1 or
                  identities[0].get('sources')!=sources or
                  identities[0].get('threads')!=manifest['threads'] or
                  any(pool.get('num_threads')!=1 for pool in
                      identities[0].get('threadpools',[])) or
                  len(complete)!=1 or complete[0].get('sources')!=sources or
                  complete[0].get('count')!=len(manifest['case_ids']) or
                  len(results)!=len(manifest['case_ids']) or ids!=manifest['case_ids'] or
                  [record.get('case_id') for record in starts]!=manifest['case_ids'] or
                  [record.get('kind') for record in records[1:-1]]!=
                  [kind for _ in manifest['case_ids']
                   for kind in ('case_start','case')] or
                  records[-1].get('kind')!='complete' or post!=sources):
                reason='identity_or_inventory_failure'
            elif any(record['case_seconds']>MAX_CASE_SECONDS for record in results):
                reason='case_time_limit'
            elif not all(record['passes_algebraic_floor'] for record in results):
                reason='algebraic_floor_failure'
        result=dict(reason=reason,exit_code=code,elapsed_seconds=elapsed,
                    sampled_peak_rss_bytes=peak,case_count=len(results),
                    failures=[record['case_id'] for record in results
                              if not record['passes_algebraic_floor']],
                    minimum_singular_ratio=(min(record['singular_ratio'] for record in results)
                                            if results else None),
                    malformed_lines=malformed,post_source_hashes=post,failure=failure)
        (directory/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2),
                                             encoding='utf-8')
    print(json.dumps(dict(evidence=str(directory.resolve()),reason=reason,
                          exit_code=code,case_count=len(results),
                          minimum_singular_ratio=result['minimum_singular_ratio'],
                          elapsed_seconds=elapsed,sampled_peak_rss_bytes=peak),
                     sort_keys=True))
    return 0 if reason=='process_exit' and code==0 else 1


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path)
    parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--child',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--expected-manifest',type=Path,help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.child:
        if args.expected_manifest is None:
            parser.error('--expected-manifest is required for child')
        _child(args.expected_manifest)
        return 0
    if args.output is None:
        parser.error('--output is required for supervised screen')
    return _supervise(args.output,args.smoke)


if __name__=='__main__':
    raise SystemExit(main())
