"""One isolated actual state-lifecycle operation; authority before mechanics."""
import argparse
from copy import deepcopy
from hashlib import sha256
from math import fsum
import os
from pathlib import Path
import sys
from docs.reference_cases import ge_beam3_plastic_arc_lifecycle_protocol as p
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_wave import write,publish
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT

def progress(row):print(row,flush=True)

def active(raw,completed):
    cp=p.strict_bytes(raw)
    if cp['completed_steps']!=completed or len(cp['records'])!=completed:raise ValueError('actual completed prefix')
    old=cp['initial']['histories']
    for row in cp['records']:
        if p.canonical(row['origins'])!=p.canonical(old):raise ValueError('original material history continuity')
        changes=[fsum(b['accumulated'])-fsum(a['accumulated']) for aa,bb in zip(old,row['histories'],strict=True)
            for a,b in zip(aa['stations'],bb['stations'],strict=True)]
        if not changes or min(changes)<0. or max(changes)<=0.:raise ValueError('actual plastic increment required')
        old=row['histories']
    return cp

def mutated(raw,kind):
    v=p.strict_bytes(raw);row=v['records'][0]
    if kind=='origins':row['origins'][0]['stations'][0]['plastic'][0][0]+=.01
    elif kind=='histories':row['histories'][0]['stations'][0]['plastic'][0][0]+=.01
    elif kind=='accumulated':row['histories'][0]['stations'][0]['accumulated'][0]+=.01
    elif kind=='predictor':row['predictor'][-1]*=-1.
    elif kind=='program':v['program']['steps'][0]=.06
    elif kind=='work':row['work'][-1]+=.01
    elif kind=='recovery':row['recovery_sha256']='0'*64
    elif kind=='cursor':v['completed_steps']=True
    # Reseal EVERY downstream record and outer checkpoint. Rejection cannot
    # rely on an accidentally stale self hash after a scientific mutation.
    previous=v['initial']['record_sha256']
    for row in v['records']:
        row['previous_sha256']=previous
        row['record_sha256']=sha256(p.canonical({k:x for k,x in row.items() if k!='record_sha256'})).hexdigest()
        previous=row['record_sha256']
    if kind=='predecessor':
        v['records'][1]['previous_sha256']='0'*64
        v['records'][1]['record_sha256']=sha256(p.canonical({k:x for k,x in v['records'][1].items() if k!='record_sha256'})).hexdigest()
    if kind=='record':v['records'][0]['record_sha256']='0'*64
    v['checkpoint_sha256']=sha256(p.canonical({k:x for k,x in v.items() if k!='checkpoint_sha256'})).hexdigest()
    made=p.canonical(v)
    if kind=='duplicate':made=made.replace(b'{',b'{"schema":"duplicate",',1)
    elif kind=='nonfinite':made=made.replace(b'"parameter":',b'"bad":NaN,"parameter":',1)
    return made

def run(request_path,request_sha,output):
    raw=p.read(request_path)
    if sha256(raw).hexdigest()!=request_sha:raise ValueError('request digest')
    request=p.strict_bytes(raw);inputs=p.request(request);p.authority();guard(request['revision'])
    if sys.flags.optimize or any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('assertions and one numerical thread')
    out=Path(output).resolve()
    if out.exists() or out.is_relative_to(ROOT):raise ValueError('fresh external worker output')
    out.mkdir();mode=request['mode'];n=request['macros'];revision=request['revision']
    progress(dict(stage='lifecycle-initialized',macros=n,mode=mode))
    blobs={k:p.read(b['path']) for k,b in request['inputs'].items()}
    full_sha=request['inputs'].get('full',{}).get('sha256');checkpoint_sha=full_sha;checks={}
    if mode=='check':
        from docs.reference_cases.ge_beam3_plastic_arc_audit import audit
        result=audit(inputs['capture'],blobs['full'],revision,n)
        if any(name=='anysolver' or name.startswith('anysolver.') or name in ('numpy','scipy') for name in sys.modules):
            raise ValueError('independent checker imported mechanics')
        publish(out/'material.json',result);checks={'all_stations_independently_checked':True}
    else:
        sys.path.insert(0,str(ROOT/'src'))
        from anysolver import _ge_beam3_retained_arc as arc
        from anysolver.control import CancellationToken
        from anysolver._ge_beam3_p5_seeded.core import canonical
        from docs.reference_cases.ge_beam3_plastic_arc_lifecycle_case import build,capture
        model,programme=build(n)
        if mode in ('full','prefix','resume') or mode.startswith('cancel-'):
            kw={}
            if mode=='prefix':kw['stop_after']=1  # Comparison full is NEVER a starting state.
            elif mode=='resume' or mode.startswith('cancel-'):
                kw=dict(checkpoint=blobs['prefix'],expected_sha256=request['inputs']['prefix']['sha256'])
                active(blobs['prefix'],1)
            reached=[]
            if mode.startswith('cancel-'):
                token=CancellationToken();kw['cancellation_token']=token
                stage={'cancel-assembly':'before_assembly','cancel-trial':'before_trial','cancel-commit':'before_commit'}[mode]
                def observe(row):
                    progress(row)
                    if row['step']==2 and row['stage']=='retained-arc.'+stage:
                        reached.append(dict(row));token.cancel()
                observer=observe
            else:observer=progress
            result=arc.solve(model,programme,progress=observer,**kw)
            write(out/'checkpoint-diagnostic.json',result.checkpoint)
            write(out/'disposition.json',dict(status=result.status,completed=result.completed_steps,failure=result.failure,reached=reached))
            if mode.startswith('cancel-'):
                if not reached or result.status!='cancelled' or result.completed_steps!=1 or result.checkpoint!=blobs['prefix']:
                    raise ValueError('actual cancellation must preserve plastic predecessor')
                old=canonical(result.state)
                resumed=arc.solve(model,programme,checkpoint=result.checkpoint,expected_sha256=sha256(result.checkpoint).hexdigest(),progress=progress)
                write(out/'resumed-diagnostic.json',resumed.checkpoint)
                if resumed.status!='completed' or resumed.checkpoint!=blobs['full'] or canonical(result.state)!=old:
                    raise ValueError('cancelled resume differs from uninterrupted history')
                checks=dict(injection_reached=True,preceding_checkpoint_preserved=True,resumed_equals_full=True)
            else:
                count=1 if mode=='prefix' else 3
                if result.status!=('paused' if mode=='prefix' else 'completed') or result.completed_steps!=count:
                    raise ValueError('actual lifecycle solve failed: '+str(result.failure))
                active(result.checkpoint,count)
                if mode=='resume' and result.checkpoint!=blobs['full']:raise ValueError('resume byte disagreement')
                checks={dict(full='full_completed',prefix='paused_after_plastic_step',resume='resumed_equals_full')[mode]:True}
            write(out/'checkpoint.json',result.checkpoint);checkpoint_sha=sha256(result.checkpoint).hexdigest()
            if mode=='full':
                full_sha=checkpoint_sha
                if n==1 and full_sha!=p.authority()['one_macro_checkpoint_sha256']:raise ValueError('one-macro smoke reproducibility')
        elif mode=='capture':
            write(out/'capture.json',capture(n,blobs['full'],revision,progress))
            checks={'original_histories_replayed':True}
        elif mode=='mutations':
            original=blobs['full'];active(original,3)
            # The valid state is independently owned and preserved throughout.
            owner=arc.Context(model,programme);state,records=owner.restore(original,expected_sha256=full_sha)
            old=canonical(state)
            for kind in p.MUTATIONS:
                candidate=mutated(original,kind)
                expected='0'*64 if kind=='external-hash' else sha256(candidate).hexdigest()
                rejected=False
                try:arc.Context(model,programme).restore(candidate,expected_sha256=expected)
                except ValueError:rejected=True
                if not rejected:raise ValueError('resealed mutation accepted: '+kind)
                if canonical(state)!=old:raise ValueError('negative test altered original owned state')
                checks[kind]=True;progress(dict(stage='mutation-rejected',macros=n,kind=kind))
            if owner.checkpoint(records)!=original:raise ValueError('original chain changed during rejection tests')
    p.request(request);p.authority();guard(revision)
    if p.read(request_path)!=raw:raise ValueError('request changed')
    for key,b in request['inputs'].items():
        if p.read(b['path'])!=blobs[key]:raise ValueError('frozen predecessor changed')
    publish(out/'report.json',dict(schema='GE_BEAM3_PLASTIC_ARC_LIFECYCLE_REPORT_V1',revision=revision,macros=n,mode=mode,
        checkpoint_sha256=checkpoint_sha,reference_full_sha256=full_sha,checks=checks,production_qualified=False))
    progress(dict(stage='lifecycle-worker-complete',macros=n,mode=mode))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--request',required=True);parser.add_argument('--sha256',required=True);parser.add_argument('--output',required=True)
    a=parser.parse_args();run(a.request,a.sha256,a.output)

if __name__=='__main__':main()
