"""Research-only point-isolated Euler wave; no mechanics imported before authority."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from hashlib import sha256
import os
from pathlib import Path
import sys
from threading import Event
import time
import traceback

from docs.reference_cases.ge_beam3_retained_prestress_protocol import (
    canonical,strict_bytes,read,bind,bound,assignment,search,finish)
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.e4_pl_s3_v2_bounded_process import _ProcessJob,THREAD_ENVIRONMENT

def write(path,value):
    raw=value if type(value) is bytes else canonical(value)
    with Path(path).open('xb') as stream:stream.write(raw)

def publish(path,value):
    """Same-volume, exclusive atomic publication after canonical validation."""
    path=Path(path);pending=path.with_name(path.name+'.pending')
    write(pending,value)
    strict_bytes(read(pending))
    os.link(pending,path)  # Fails if destination exists; never overwrites.

def point(request,expected_sha256,output):
    raw=read(request)
    if sha256(raw).hexdigest()!=expected_sha256:raise ValueError('external assignment hash')
    value=strict_bytes(raw);prior=assignment(value)
    guard(value['revision'])
    if sys.flags.optimize or any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):
        raise ValueError('assertions and one numerical thread required')
    root=Path(output);root.mkdir(exist_ok=False)
    print(dict(stage='authority-complete',index=value['index'],macros=value['macros']),flush=True)
    # Scientific imports occur only after assignment and complete source checks.
    sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'src')]
    from docs.reference_cases.ge_beam3_retained_prestress_point import evaluate_point
    constants={}
    if prior['outputs']:
        anchor=bound(prior['outputs'][0]['point'])
        if anchor['row']!=prior['rows'][0] or anchor['global_newton_programme_run'] is not True:
            raise ValueError('initial family proof authority')
        constants={key:anchor['families'][key] for key in ('axial','torsion')}
    row=evaluate_point(value['compression'],value['macros'],value['index'],constants,root)
    search([*prior['rows'],row],value['macros'])
    if read(request)!=raw:raise ValueError('assignment changed during point')
    assignment(value)
    if prior['outputs']:bound(prior['outputs'][0]['point'])
    guard(value['revision'])
    print(dict(stage='point-complete',index=value['index']),flush=True)

def supervise(command,root,deadline,stop,*,wall=600.,inactivity=120.,memory=24*1024**3):
    """Small bounds overrides are for disposable failure tests, never CLI runs."""
    if not 0<wall<=600 or not 0<inactivity<=120 or not 0<memory<=24*1024**3:
        raise ValueError('bounded process limits')
    start=time.monotonic();progress=start;previous=-1;job=None;process=None
    receipt=dict(started_utc=datetime.now(timezone.utc).isoformat(),reason=None,exit_code=None,
                 before=None,after=None,error=None,cleanup_error=None)
    try:
        if stop.is_set() or start>=deadline:raise RuntimeError('wave stopped before launch')
        job=_ProcessJob(memory)
        with (root/'stdout.txt').open('xb') as out,(root/'stderr.txt').open('xb') as err:
            process=job.launch(command,cwd=ROOT,env={**os.environ,**THREAD_ENVIRONMENT},stdout=out,stderr=err)
            receipt['pid']=process.pid
            while process.poll() is None:
                now=time.monotonic();cpu,active,peak=job.accounting()
                if cpu!=previous:previous=cpu;progress=now
                if stop.is_set():receipt['reason']='WAVE_STOPPED';break
                if now>=deadline:receipt['reason']='WAVE_DEADLINE';break
                if now-start>wall:receipt['reason']='CHILD_DEADLINE';break
                if now-progress>inactivity:receipt['reason']='CPU_INACTIVITY';break
                if peak>memory:receipt['reason']='MEMORY_BREACH';break
                time.sleep(.1)
            receipt['before']=job.accounting()
            if receipt['reason'] is None:
                receipt['reason']='COMPLETED' if process.returncode==0 else 'CHILD_FAILURE'
    except BaseException:
        receipt['reason']='SUPERVISOR_FAILURE';receipt['error']=traceback.format_exc()
    finally:
        if job is not None:
            try:
                job.terminate();until=time.monotonic()+5
                while True:
                    receipt['after']=job.accounting()
                    if receipt['after'][1]==0:break
                    if time.monotonic()>until:raise RuntimeError('process-tree cleanup deadline')
                    time.sleep(.05)
                if process is not None:receipt['exit_code']=process.wait(timeout=5)
            except BaseException:receipt['cleanup_error']=traceback.format_exc()
            finally:job.close()
    receipt['elapsed']=time.monotonic()-start
    receipt['ended_utc']=datetime.now(timezone.utc).isoformat()
    receipt['success']=(receipt['reason']=='COMPLETED' and receipt['exit_code']==0
        and receipt['error'] is None and receipt['cleanup_error'] is None
        and receipt['after'] is not None and receipt['after'][1]==0)
    write(root/'process.json',receipt)
    return receipt

def validate_outputs(outputs,rows,macros):
    if len(outputs)!=len(rows):raise ValueError('complete output extent')
    for i,(pair,row) in enumerate(zip(outputs,rows)):
        state=bound(pair['state']);proof=bound(pair['point'])
        if pair['state']['sha256']!=row['checkpoint_sha256']:raise ValueError('checkpoint binding')
        if set(proof)!={'row','packet','families','modes','global_newton_programme_run',
                       'manufactured_uniform_axial_equilibrium','production_qualified'}:
            raise ValueError('point proof schema')
        if proof['row']!=row or proof['global_newton_programme_run'] is not True:
            raise ValueError('actual point identity')
        if proof['manufactured_uniform_axial_equilibrium'] is not False or proof['production_qualified'] is not False:
            raise ValueError('invalid qualification claim')
        if set(proof['modes'])!={'bend-y','bend-z'}:raise ValueError('both bending families required')
        lam=min(proof['modes'][name]['eigenvalues'][0] for name in ('bend-y','bend-z'))
        if lam!=row['lambda_min']:raise ValueError('minimum signed spectrum identity')
        if len(state['records'])!=2:raise ValueError('both actual preload targets required')
    search(rows,macros)

def run_mesh(revision,macros,root,deadline,stop):
    root.mkdir(exist_ok=False);rows=[];outputs=[]
    for index in range(22):
        if stop.is_set() or time.monotonic()>=deadline:raise RuntimeError('wave ended')
        load,_=search(rows,macros)
        prior=root/('transcript-%02d.json'%index)
        write(prior,dict(revision=revision,macros=macros,rows=rows,outputs=outputs))
        request=root/('assignment-%02d.json'%index)
        write(request,dict(schema='GE_BEAM3_EULER_POINT_ASSIGNMENT_V1',revision=revision,macros=macros,
            index=index,compression=load,prior=bind(prior)))
        request_binding=bind(request);directory=root/('point-%02d'%index);directory.mkdir(exist_ok=False)
        receipt=supervise([sys.executable,'-B','-m',__name__ if __name__!='__main__' else
            'docs.reference_cases.ge_beam3_retained_prestress_wave','--point',str(request),
            '--expected-sha256',request_binding['sha256'],'--output',str(directory/'science')],directory,deadline,stop)
        if not receipt['success']:raise RuntimeError('point process failure: '+str(directory))
        bound(request_binding)
        science=directory/'science'
        pair=dict(state=bind(science/('state-%02d.json'%index)),point=bind(science/('point-%02d.json'%index)))
        row=bound(pair['point'])['row']
        search([*rows,row],macros)
        rows.append(row);outputs.append(pair)
        print(dict(stage='accepted-point',macros=macros,index=index,seconds=receipt['elapsed']),flush=True)
    guard(revision);validate_outputs(outputs,rows,macros)
    result=finish(rows,macros)
    write(root/'transcript-22.json',dict(revision=revision,macros=macros,rows=rows,outputs=outputs))
    publish(root/'buckling.json',result)
    return result

def wave(revision,meshes,output):
    if type(meshes) is not list or not meshes or meshes!=sorted(set(meshes)) or any(type(n) is not int or n not in (1,2,4,8) for n in meshes):
        raise ValueError('ordered unique registered meshes')
    if sys.flags.optimize:raise ValueError('assertions required')
    guard(revision)
    root=Path(output).resolve()
    if root.is_relative_to(ROOT.resolve()):raise ValueError('external output required')
    root.mkdir(exist_ok=False)
    start=time.monotonic();deadline=start+1800.;stop=Event();errors=[];results={}
    with ThreadPoolExecutor(max_workers=min(3,len(meshes))) as pool:
        futures={pool.submit(run_mesh,revision,n,root/('n%d'%n),deadline,stop):n for n in meshes}
        for future in as_completed(futures):
            try:results[futures[future]]=future.result()
            except BaseException:errors.append(traceback.format_exc());stop.set()
    try:
        guard(revision)
        if time.monotonic()>=deadline:raise RuntimeError('wave deadline')
        if set(results)!=set(meshes):raise RuntimeError('incomplete wave')
        if errors:raise RuntimeError('failed wave')
        ordered=[results[n] for n in meshes]
        if any(a['relative_euler_error']<=b['relative_euler_error'] for a,b in zip(ordered,ordered[1:])):
            raise ValueError('refinement error must decrease')
        publish(root/'aggregate.json',dict(schema='GE_BEAM3_ACTUAL_PRELOAD_EULER_SUBSET_V1',
            meshes=meshes,results=ordered,production_qualified=False,full_spatial_postbuckling_qualified=False))
    except BaseException:errors.append(traceback.format_exc())
    write(root/'wave.json',dict(revision=revision,meshes=meshes,elapsed=time.monotonic()-start,
        errors=errors,success=not errors,all_futures_terminal=True))
    if errors:raise RuntimeError('bounded Euler wave failed; preserve raw logs')

def main():
    parser=argparse.ArgumentParser();mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--point');mode.add_argument('--run',action='store_true')
    parser.add_argument('--expected-sha256');parser.add_argument('--revision');parser.add_argument('--meshes',type=int,nargs='+')
    parser.add_argument('--output',required=True);args=parser.parse_args()
    if args.point:point(args.point,args.expected_sha256,args.output)
    else:wave(args.revision,args.meshes,args.output)

if __name__=='__main__':main()
