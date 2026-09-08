"""Fresh-process arch steps with full native replay; no mechanics changes."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
import os
from pathlib import Path
import sys
from threading import Event
import time
import traceback
from docs.reference_cases import ge_beam3_retained_arch_point_protocol as protocol
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard, ROOT
from docs.reference_cases.ge_beam3_retained_prestress_wave import supervise, write, publish
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT

MODULE = 'docs.reference_cases.ge_beam3_retained_arch_point_wave'

def evaluate(macros, index, root, prior_state=None, previous_reference=None):
    """Only called after external assignment/source validation in the worker."""
    from dataclasses import asdict
    import numpy as np
    from docs.reference_cases import ge_beam3_retained_arch_case as case
    from anysolver._ge_beam3_p5_seeded.core import canonical
    protocol.extent(macros)
    if type(index) is not int or not 1<=index<=12: raise ValueError('registered point')
    if (prior_state is None)!=(index==1) or (previous_reference is None)!=(index==1):
        raise ValueError('virgin or complete explicit predecessor required')
    # Existing controller restores, reissues and checks the entire predecessor
    # chain; only stop_after changes scheduling, never the frozen program.
    print(dict(stage='native-prefix-and-next-step',macros=macros,index=index),flush=True)
    result=case.arc.solve(case.model(macros),case.program(macros),checkpoint=prior_state,
        expected_sha256=None if prior_state is None else sha256(prior_state).hexdigest(),
        stop_after=index,progress=lambda row:print(row,flush=True))
    write(root/'checkpoint-diagnostic.json',result.checkpoint)
    write(root/'process-disposition.json',dict(status=result.status,failure=result.failure,
        cursor=result.completed_steps,production_qualified=False))
    if result.status!=('completed' if index==12 else 'paused') or result.completed_steps!=index:
        raise RuntimeError('native arc step failed: '+str(result.failure))
    if len(protocol.strict_bytes(result.checkpoint)['records'])!=index: raise ValueError('accepted step count')
    print(dict(stage='full-accepted-prefix-replay',macros=macros,index=index),flush=True)
    context=case.arc.Context(case.model(macros),case.program(macros))
    accepted,records=context.restore(result.checkpoint,expected_sha256=sha256(result.checkpoint).hexdigest())
    if context.checkpoint(records)!=result.checkpoint: raise ValueError('native replay changed bytes')
    previous=None
    if previous_reference is not None:
        if set(previous_reference)!=protocol.REFERENCE_KEYS: raise ValueError('reference continuation schema')
        values=dict(previous_reference)
        for key in ('force','parameter','fields'): values[key]=np.asarray(values[key],dtype=float)
        previous=case.continuum.ArchReference(**values)
        if canonical(asdict(previous))!=protocol.canonical(previous_reference):
            raise ValueError('reference roundtrip changed fields')
    row,reference,recovered=case.compare(context,accepted,previous=previous)
    protocol.identity_errors(protocol.strict_bytes(canonical(row)))
    write(root/('state-%02d.json'%index),result.checkpoint)
    write(root/('point-%02d.json'%index),canonical(dict(row=row,reference=asdict(reference),recovered=recovered)))
    print(dict(stage='reference-complete',macros=macros,index=index,
        load_error=row['load_error'],recovery_error=row['recovery_error'],energy_error=row['energy_error']),flush=True)

def point(request, expected_sha256, output):
    raw=protocol.read(request)
    if sha256(raw).hexdigest()!=expected_sha256: raise ValueError('external assignment hash')
    value=protocol.strict_bytes(raw); prior=protocol.assignment(value); guard(value['revision'])
    if sys.flags.optimize or any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):
        raise ValueError('assertions and one numerical thread required')
    root=Path(output); root.mkdir(exist_ok=False)
    print(dict(stage='authority-complete',macros=value['macros'],index=value['index']),flush=True)
    sys.path[:0]=[str(ROOT/'src')]
    state=reference=None
    if prior['outputs']:
        pair=prior['outputs'][-1]
        # Bound reads are repeated immediately before importing/evaluating mechanics.
        protocol.bound(pair['state']); state=protocol.read(pair['state']['path'])
        if sha256(state).hexdigest()!=pair['state']['sha256']: raise ValueError('predecessor changed')
        reference=protocol.bound(pair['point'])['reference']
    evaluate(value['macros'],value['index'],root,state,reference)
    if protocol.read(request)!=raw: raise ValueError('assignment changed during execution')
    protocol.assignment(value); guard(value['revision'])
    pair=dict(state=protocol.bind(root/('state-%02d.json'%value['index'])),
        point=protocol.bind(root/('point-%02d.json'%value['index'])))
    protocol.outputs([*prior['outputs'],pair],value['macros'])
    publish(root/'ready.json',dict(schema='GE_BEAM3_RETAINED_ARCH_POINT_READY_V1',
        assignment_sha256=expected_sha256,outputs=pair,production_qualified=False))

def run_mesh(revision, macros, root, deadline, stop):
    root.mkdir(); pairs=[]
    for index in range(1,13):
        guard(revision)
        if stop.is_set() or time.monotonic()>=deadline: raise RuntimeError('wave stopped before next step')
        transcript=root/('transcript-%02d.json'%(index-1))
        write(transcript,dict(schema=protocol.TRANSCRIPT,revision=revision,macros=macros,outputs=pairs))
        directory=root/('step-%02d'%index); directory.mkdir()
        request=directory/'assignment.json'
        write(request,dict(schema=protocol.SCHEMA,revision=revision,macros=macros,index=index,prior=protocol.bind(transcript)))
        request_binding=protocol.bind(request); protocol.assignment(protocol.bound(request_binding))
        receipt=supervise([sys.executable,'-B','-m',MODULE,'--point',str(request),
            '--expected-sha256',request_binding['sha256'],'--output',str(directory/'science')],directory,deadline,stop)
        if not receipt['success']: raise RuntimeError('point process failed: '+str(directory))
        protocol.bound(request_binding); science=directory/'science'
        ready=protocol.strict_bytes(protocol.read(science/'ready.json'))
        if (set(ready)!={'schema','assignment_sha256','outputs','production_qualified'}
                or ready['schema']!='GE_BEAM3_RETAINED_ARCH_POINT_READY_V1'
                or ready['assignment_sha256']!=request_binding['sha256'] or ready['production_qualified'] is not False):
            raise ValueError('ready authority')
        pair=dict(state=protocol.bind(science/('state-%02d.json'%index)),point=protocol.bind(science/('point-%02d.json'%index)))
        if ready['outputs']!=pair: raise ValueError('ready outputs changed')
        protocol.outputs([*pairs,pair],macros); pairs.append(pair)
        print(dict(stage='accepted-point',macros=macros,index=index,seconds=receipt['elapsed']),flush=True)
    guard(revision); result=protocol.finish(pairs,macros)
    write(root/'transcript-12.json',dict(schema=protocol.TRANSCRIPT,revision=revision,macros=macros,outputs=pairs))
    # Full-path artifacts remain under this geometry directory until the whole
    # wave is complete; aggregate.json alone records complete wave disposition.
    publish(root/'comparison.json',result)
    write(root/'checkpoint.json',protocol.read(pairs[-1]['state']['path']))
    write(root/'process-disposition.json',dict(status='completed',failure=None,cursor=12,production_qualified=False))
    return result

def wave(revision, meshes, output):
    if type(meshes) is not list or not meshes or meshes!=sorted(set(meshes)): raise ValueError('ordered unique meshes')
    for n in meshes: protocol.extent(n)
    if sys.flags.optimize: raise ValueError('assertions required')
    guard(revision); root=Path(output).resolve()
    if root.is_relative_to(ROOT.resolve()): raise ValueError('external output only')
    root.mkdir(exist_ok=False); started=time.monotonic(); deadline=started+1800.; stop=Event(); errors=[]; results={}
    with ThreadPoolExecutor(max_workers=min(3,len(meshes))) as pool:
        futures={pool.submit(run_mesh,revision,n,root/('n%d'%n),deadline,stop):n for n in meshes}
        for future in as_completed(futures):
            try: results[futures[future]]=future.result()
            except BaseException: errors.append(traceback.format_exc()); stop.set()
    try:
        guard(revision)
        if time.monotonic()>=deadline or set(results)!=set(meshes) or errors: raise RuntimeError('incomplete bounded arch wave')
        ordered=[results[n] for n in meshes]
        terminal=('NO_GO_GE_BEAM3_RETAINED_ARCH_ENGINEERING_COMPARISON'
            if 12 in results and not results[12]['engineering_2_percent_pass'] else
            'UNCLASSIFIED_GE_BEAM3_RETAINED_ARCH_COMPARISON_ONLY')
        publish(root/'aggregate.json',dict(schema='GE_BEAM3_RETAINED_ARCH_POINT_SUBSET_V1',
            meshes=meshes,results=ordered,terminal=terminal,production_qualified=False,
            full_spatial_stability=False,independent_review='PENDING'))
    except BaseException: errors.append(traceback.format_exc())
    write(root/'wave.json',dict(revision=revision,meshes=meshes,elapsed=time.monotonic()-started,
        errors=errors,success=not errors,all_futures_terminal=True,production_qualified=False))
    if errors: raise RuntimeError('bounded arch wave failed; preserve diagnostics; no automatic retry')

def main():
    parser=argparse.ArgumentParser(); mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--point'); mode.add_argument('--run',action='store_true')
    parser.add_argument('--expected-sha256'); parser.add_argument('--revision')
    parser.add_argument('--meshes',type=int,nargs='+'); parser.add_argument('--output',required=True)
    args=parser.parse_args()
    if args.point: point(args.point,args.expected_sha256,args.output)
    else: wave(args.revision,args.meshes,args.output)

if __name__=='__main__': main()
