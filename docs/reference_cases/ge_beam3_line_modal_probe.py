"""Frozen saved-state modal comparison; no native solves and no automatic retry."""
import argparse
import json
import os
from pathlib import Path
import sys
import time

from docs.reference_cases.ge_beam3_fibre_arch_probe import guard, _ProcessJob, THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_preserved_arch_load_comparison import canonical, parse

ROOT=Path(__file__).resolve().parents[2]


def read(path):
    if path.is_symlink() or not path.is_file() or not 0<path.stat().st_size<=2*(1<<20):
        raise ValueError('bounded regular complete diagnostic')
    raw=path.read_bytes(); parse(raw); return raw


def summary(output,revision):
    from docs.reference_cases.ge_beam3_line_modal_comparison import summary as inspect
    return inspect(output,revision)


def worker(revision,output):
    guard(revision)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()): raise ValueError('single numerical thread required')
    from docs.reference_cases.ge_beam3_line_modal_comparison import build
    def progress(event): print(json.dumps(event,sort_keys=True),flush=True)
    def save(name,raw):
        with (output/name).open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    progress(dict(stage='INITIALIZATION'))
    rows=build(save,progress)
    value=summary(output,revision)
    if canonical(value['rows'])!=canonical(rows): raise ValueError('reloaded metrics changed')
    guard(revision); save('comparison.pending.json',canonical(value))
    progress(dict(stage='COMPLETION',new_native_solves=0,new_reference_equilibria=1,new_reference_spectra=2))


def run(revision,output):
    if os.name!='nt': raise ValueError('Windows Job containment required')
    guard(revision)
    if not output.is_absolute() or output.resolve().is_relative_to(Path('C:/Github').resolve()):
        raise ValueError('fresh external absolute output required')
    output.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ); env.update(THREAD_ENVIRONMENT)
    env.pop('PYTHONPATH',None); env['PYTHONDONTWRITEBYTECODE']='1'; env['PYTHONHASHSEED']='0'
    command=[sys.executable,'-B','-m','docs.reference_cases.ge_beam3_line_modal_probe',
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
                    raise RuntimeError('line modal wall/inactivity/memory bound')
                if code is not None and active==0: break
                time.sleep(.2)
            if code!=0: raise RuntimeError(f'line modal child failed: exit {code}; no retry')
        raw=read(output/'comparison.pending.json')
        if raw!=canonical(summary(output,revision)): raise ValueError('staged comparison mismatch')
        guard(revision)
    finally:
        try:
            if not job.terminate(): raise RuntimeError('complete line modal process cleanup unproven')
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
