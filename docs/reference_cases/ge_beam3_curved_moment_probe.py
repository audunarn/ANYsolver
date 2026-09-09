"""One frozen, process-contained curved moment development wave; no retry."""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import time

from docs.reference_cases.ge_beam3_fibre_arch_probe import guard, _ProcessJob, THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_preserved_arch_load_comparison import canonical, parse

ROOT=Path(__file__).resolve().parents[2]
ARTIFACTS=('checkpoint-1.json','checkpoint-2.json','checkpoint-4.json','fields-diagnostic.json',
    'native-status-1.json','native-status-2.json','native-status-4.json','reference-diagnostic.json')


def read(path):
    if path.is_symlink() or not path.is_file() or not 0<path.stat().st_size<=2*(1<<20):
        raise ValueError('bounded regular complete diagnostic')
    raw=path.read_bytes(); parse(raw); return raw


def summary(output,revision):
    from docs.reference_cases.ge_beam3_curved_moment_comparison import recompute
    packets={m:parse(read(output/f'checkpoint-{m}.json')) for m in (1,2,4)}
    detail=parse(read(output/'fields-diagnostic.json'))
    if canonical(detail['references'])!=read(output/'reference-diagnostic.json'):
        raise ValueError('preserved reference packet mismatch')
    for m in (1,2,4):
        if parse(read(output/f'native-status-{m}.json'))!=dict(status='completed',failure=None):
            raise ValueError('all native solves must complete')
    rows=recompute(detail,packets)
    artifacts=[]
    for name in ARTIFACTS:
        raw=read(output/name)
        artifacts.append(dict(path=name,bytes=len(raw),sha256=sha256(raw).hexdigest()))
    return dict(schema='GE_BEAM3_CURVED_MOMENT_DEVELOPMENT_V1',revision=revision,rows=rows,artifacts=artifacts,
        status='DEVELOPMENT_COMPARISON_NOT_QUALIFICATION',production_qualified=False,
        independent_review='PENDING',conservative_spectral_authority=False,runtime_version_check_only=True)


def worker(revision,output):
    guard(revision)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()): raise ValueError('single numerical thread required')
    sys.path.insert(0,str(ROOT/'src'))
    from docs.reference_cases.ge_beam3_curved_moment_comparison import build
    def progress(event): print(json.dumps(event,sort_keys=True),flush=True)
    def save(name,raw):
        with (output/name).open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    progress(dict(stage='INITIALIZATION'))
    rows,detail=build(save,progress)
    save('fields-diagnostic.json',canonical(detail))
    value=summary(output,revision)
    if canonical(value['rows'])!=canonical(rows): raise ValueError('reloaded metrics changed')
    guard(revision); save('comparison.pending.json',canonical(value))
    progress(dict(stage='COMPLETION',native_solves=3,reference_solves=6))


def run(revision,output):
    if os.name!='nt': raise ValueError('Windows Job containment required')
    guard(revision)
    if not output.is_absolute() or output.resolve().is_relative_to(Path('C:/Github').resolve()):
        raise ValueError('fresh external absolute output required')
    output.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ); env.update(THREAD_ENVIRONMENT)
    env.pop('PYTHONPATH',None); env['PYTHONDONTWRITEBYTECODE']='1'; env['PYTHONHASHSEED']='0'
    command=[sys.executable,'-B','-m','docs.reference_cases.ge_beam3_curved_moment_probe',
        '--worker','--revision',revision,'--output',str(output)]
    job=_ProcessJob(24*(1<<30)); start=time.monotonic(); activity=start; last=(0,0)
    try:
        with (output/'stdout.log').open('xb') as stdout,(output/'stderr.log').open('xb') as stderr:
            process=job.launch(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
            while True:
                cpu,active,memory=job.accounting(); code=process.poll(); now=time.monotonic()
                current=(cpu,(output/'stdout.log').stat().st_size)
                if current!=last: activity=now; last=current
                if now-start>=600 or now-activity>=120 or memory>=24*(1<<30):
                    raise RuntimeError('curved moment wall/inactivity/memory bound')
                if code is not None and active==0: break
                time.sleep(.2)
            if code!=0: raise RuntimeError(f'curved moment child failed: exit {code}; no retry')
        raw=read(output/'comparison.pending.json')
        if raw!=canonical(summary(output,revision)): raise ValueError('staged comparison mismatch')
        guard(revision)
    finally:
        try:
            if not job.terminate(): raise RuntimeError('complete curved moment process cleanup unproven')
        finally: job.close()
    guard(revision)
    if raw!=read(output/'comparison.pending.json') or raw!=canonical(summary(output,revision)):
        raise ValueError('staged comparison changed after cleanup')
    os.link(output/'comparison.pending.json',output/'comparison.json')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision',required=True); parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--worker',action='store_true'); args=parser.parse_args()
    (worker if args.worker else run)(args.revision,args.output)


if __name__=='__main__': main()
