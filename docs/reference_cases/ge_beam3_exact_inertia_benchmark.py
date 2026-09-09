"""Bounded arithmetic-only comparison on a preserved native spectral packet."""
import argparse
from hashlib import sha256
from functools import partial
import json
import os
from pathlib import Path
import statistics
import sys
import time
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard, _ProcessJob, THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_preserved_arch_load_comparison import canonical

ROOT=Path(__file__).resolve().parents[2]
INPUT=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-loaded-spectra-20260907-v1/native-1.json')
INPUT_SHA='4519178585b0ba921559bf161a5bea4425a4f069f51f7f07a306edac303204c8'
SIX_INPUT=INPUT.parent.parent/'ge-beam3-loaded-six-20260907-v1/native-1.json'
SIX_SHA='613e1170278556a5c4f07348c5fc1cff5a6433c8672bbf25ddc3fad00ed82277'


def deadline_check(start, stage=None):
    if time.monotonic()-start>120.: raise TimeoutError('arithmetic comparison deadline')


def worker(revision, output, case_id='four'):
    guard(revision)
    if case_id not in ('four','six'): raise ValueError('registered arithmetic case required')
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()): raise ValueError('one thread')
    path,size,digest,dimension=(INPUT,210271,INPUT_SHA,45) if case_id=='four' else (SIX_INPUT,434444,SIX_SHA,69)
    raw=path.read_bytes()
    if len(raw)!=size or sha256(raw).hexdigest()!=digest: raise ValueError('saved packet changed')
    sys.path.insert(0,str(ROOT/'src'))
    import runpy
    import numpy as np
    from anysolver._native_exact_shift_inertia import exact_inertia,integer_inertia
    from anysolver._native_factor_chain_modes import mm, _reduce, reassemble
    if case_id=='four':
        oracle=runpy.run_path(str(ROOT/'tests/test_native_fraction_free_inertia.py'))['rational_inertia']
        routines={'rational':oracle,'integer':integer_inertia}
    else:
        routines={'integer':partial(integer_inertia,dimension_limit=96),'filtered':partial(exact_inertia,dimension_limit=96)}
    p=json.loads(raw)['packet']; left,right,g,b=(np.asarray(p[k]) for k in ('left','right','geometric','kinetic'))
    start=time.monotonic()
    check=partial(deadline_check,start)
    print('REASSEMBLY',flush=True)
    _,_,mapping=_reduce(mm(left,right,check),g,b.T@b,tuple(p['free']),tuple(p['algebraic']),check,b)
    h,m=reassemble(left,right,g,b,mapping,check)
    if h.shape!=(dimension,dimension): raise ValueError('saved arithmetic pencil dimension')
    shift=float(json.loads(raw)['modes']['numerical_brackets'][-1][0])
    names=tuple(routines); timings={name:[] for name in names}; answers={}
    for repetition in range(12):  # one warm-up plus eleven paired repetitions
        order=names if repetition%2==0 else names[::-1]
        for name in order:
            check(); wall=time.perf_counter(); cpu=time.process_time()
            answer=routines[name](h,m,shift)
            duration=time.perf_counter()-wall; cpu=time.process_time()-cpu
            check()
            if name in answers and answers[name]!=answer: raise ValueError('nondeterministic inertia')
            answers[name]=answer
            if repetition: timings[name].append(dict(wall=duration,cpu=cpu))
        if answers[names[0]]!=answers[names[1]]: raise ValueError('exact arithmetic disagreement')
        print(f'PAIR {repetition} inertia={answer}',flush=True)
    summary={}
    for name,records in timings.items():
        values=[r['wall'] for r in records]; median=statistics.median(values)
        summary[name]=dict(median=median,mad=statistics.median(abs(x-median) for x in values),
            p95=float(np.percentile(values,95)))
    value=dict(schema='GE_BEAM3_EXACT_INERTIA_ARITHMETIC_DIAGNOSTIC_V1' if case_id=='four' else 'GE_BEAM3_DYADIC_INERTIA_ARITHMETIC_DIAGNOSTIC_V1',revision=revision,
        input_sha256=digest,dimension=dimension,shift=shift,inertia=list(answers[names[0]]),
        equal=True,warmup_pairs=1,timed_pairs=11,timings=timings,summary=summary,
        mechanics_changed=False,root_width_changed=False,production_qualified=False)
    guard(revision)
    if path.read_bytes()!=raw: raise ValueError('saved packet changed after comparison')
    with (output/'benchmark.pending.json').open('xb') as stream: stream.write(canonical(value))


def run(revision,output,case_id='four'):
    guard(revision)
    if case_id not in ('four','six'): raise ValueError('registered arithmetic case required')
    if os.name!='nt' or not output.is_absolute() or output.resolve().is_relative_to(Path('C:/Github')): raise ValueError('external Windows output')
    output.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ); env.update(THREAD_ENVIRONMENT); env.pop('PYTHONPATH',None); env['PYTHONDONTWRITEBYTECODE']='1'
    command=[sys.executable,'-B','-m','docs.reference_cases.ge_beam3_exact_inertia_benchmark','--worker','--revision',revision,'--output',str(output),'--case-id',case_id]
    job=_ProcessJob(24*(1<<30)); start=time.monotonic(); last=(0,0); activity=start
    try:
        with (output/'stdout.log').open('xb') as stdout,(output/'stderr.log').open('xb') as stderr:
            child=job.launch(command,cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
            while True:
                cpu,active,memory=job.accounting(); now=time.monotonic(); code=child.poll()
                current=(cpu,(output/'stdout.log').stat().st_size)
                if current!=last: activity=now; last=current
                if now-start>=180 or now-activity>=120 or memory>=24*(1<<30): raise RuntimeError('arithmetic comparison process bound')
                if code is not None and active==0: break
                time.sleep(.2)
            if code!=0: raise RuntimeError('arithmetic comparison failed; no retry')
        raw=(output/'benchmark.pending.json').read_bytes(); value=json.loads(raw)
        if canonical(value)!=raw or value['equal'] is not True or value['revision']!=revision: raise ValueError('arithmetic result')
    finally:
        try:
            if not job.terminate(): raise RuntimeError('arithmetic cleanup unproven')
        finally: job.close()
    guard(revision)
    if (output/'benchmark.pending.json').read_bytes()!=raw: raise ValueError('arithmetic result changed')
    os.link(output/'benchmark.pending.json',output/'benchmark.json')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--revision',required=True)
    parser.add_argument('--output',required=True,type=Path); parser.add_argument('--worker',action='store_true')
    parser.add_argument('--case-id',choices=('four','six'),default='four')
    args=parser.parse_args(); (worker if args.worker else run)(args.revision,args.output,args.case_id)
