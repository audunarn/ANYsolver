"""New frozen three-target owner programme; actual native advancement, no reseeding steps."""
import argparse,os,sys,traceback
from pathlib import Path
from hashlib import sha256
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes,canonical
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_n32_snapshot_capture import sources,PREFIX
from docs.reference_cases.ge_beam3_n32_owned_capture import POLICY
TARGETS=(.0075,.010,.015)
OPS=('enroll','advance','replay','cancel-before','cancel-after','resume-before')

def descriptor(sign):
    if sign not in ('plus','minus'):raise ValueError('registered signed branch')
    return dict(targets=[(1. if sign=='plus' else -1.)*v for v in TARGETS],control_node=17,
        direction=[0.,0.,1.],nodal_forces=dict(rows=[[33,0.,-1.,0.]]),max_iterations=24,max_backtracks=8)

def recipe(operation,step):
    if type(operation) is not str or operation not in OPS or type(step) is not int:raise ValueError('registered operation/step')
    if operation=='enroll':
        if step!=0:raise ValueError('zero-step enrollment only')
        return 'enrolled',0,None
    if operation=='replay':
        if step!=3:raise ValueError('complete three-target replay only')
        return 'replayed',3,None
    if operation in ('cancel-before','cancel-after','resume-before') and step!=2:raise ValueError('target-two lifecycle only')
    if not 1<=step<=3:raise ValueError('registered branch target')
    if operation=='cancel-before':return 'cancelled',1,'elastic-continuation.before_commit'
    if operation=='cancel-after':return 'cancelled',2,'elastic-continuation.committed'
    return ('completed' if step==3 else 'paused'),step,None

def adjudicate(operation,step,status,cursor,events):
    expected,n,event=recipe(operation,step)
    if status!=expected or type(cursor) is not int or cursor!=n or type(events) is not list:raise ValueError('actual lifecycle disposition')
    if event is None:
        if events:raise ValueError('unexpected cancellation event')
    elif len(events)!=1 or set(events[0])!={'stage','target','iteration'} or events[0]['stage']!=event or type(events[0]['target']) is not int or events[0]['target']!=2 or type(events[0]['iteration']) is not int or not 0<=events[0]['iteration']<=24:
        raise ValueError('observed target-two commit boundary required')

def capsule(raw,sign,cursor):
    v=strict_bytes(raw)
    if (v['schema']!='GE_BEAM3_ELASTIC_SEED_CONTINUATION_CHAIN_V1' or v['program']!=descriptor(sign)
        or v['seed_sha256']!=PREFIX[sign]['seed-input.json'] or type(v['completed_targets']) is not int
        or v['completed_targets']!=cursor or len(v['records'])!=cursor or v['physical_loading_path_from_rest'] is not False
        or v['elastic_only'] is not True):raise ValueError('new programme/cursor/source binding')
    def self_hash(row,key):
        if sha256(canonical({k:x for k,x in row.items() if k!=key})).hexdigest()!=row[key]:raise ValueError('canonical chain self hash')
    self_hash(v,'checkpoint_sha256');previous=v['model_sha256'];origin=v['initial']['origins']
    for i,row in enumerate([v['initial'],*v['records']]):
        self_hash(row,'record_sha256')
        target=(.0065 if sign=='plus' else -.0065) if i==0 else descriptor(sign)['targets'][i-1]
        if (type(row['target']) is not int or row['target']!=i or row['previous_sha256']!=previous
            or row['displacement_target']!=target or max(*row['metrics'],row['correction'])>1e-11
            or row['origins']!=origin or row['histories']!=origin):raise ValueError('actual contiguous elastic equilibrium chain')
        previous=row['record_sha256']
    return v

def run(revision,sign,operation,step,output,checkpoint=None,expected_sha256=None):
    guard(revision);wanted,cursor,event=recipe(operation,step);desc=descriptor(sign)
    if operation in ('cancel-before','cancel-after','resume-before') and sign!='plus':raise ValueError('positive lifecycle registered')
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('one numerical thread')
    original,eq=sources(sign);seed=original['seed-input.json'];digest=sha256(seed).hexdigest();prior=None
    if operation=='enroll':
        if checkpoint is not None or expected_sha256 is not None:raise ValueError('enrollment has no continuation input')
    else:
        if checkpoint is None or expected_sha256 is None:raise ValueError('bound prior capsule required')
        prior=Path(checkpoint).read_bytes()
        if sha256(prior).hexdigest()!=expected_sha256:raise ValueError('external prior hash')
        capsule(prior,sign,step if operation=='replay' else step-1)
    root=Path(output).resolve()
    if root.is_relative_to(ROOT):raise ValueError('exclusive external output')
    root.mkdir(exist_ok=False);sys.path.insert(0,str(ROOT/'src'))
    from anysolver import _ge_beam3_elastic_seed_continuation as owner
    from anysolver._ge_beam3_retained_nodal_loading import NodalDeadForces
    from anysolver._ge_beam3_refinement_capacity import n32_refinement_capacity
    from anysolver._ge_beam3_p5_seeded.core import canonical as native
    from anysolver.control import CancellationToken
    from docs.reference_cases.ge_beam3_n32_controlled_case import model
    events=[];token=CancellationToken()
    def progress(row):
        print(dict(sign=sign,operation=operation,**row),flush=True)
        if row['stage']==event and row['target']==2:events.append(dict(row));token.cancel()
    print(dict(stage='new-branch-programme-authority-complete',sign=sign,operation=operation,step=step),flush=True)
    try:
        with n32_refinement_capacity():
            program=owner.Program(tuple(desc['targets']),17,(0.,0.,1.),NodalDeadForces(((33,0.,-1.,0.),)))
            made=model(32,arithmetic_policy=POLICY)
            if operation in ('enroll','replay'):
                context=owner.Context(made,program,seed,expected_seed_sha256=digest)
                if operation=='enroll':state=context.initial;records=();data=context.checkpoint(records)
                else:state,records=context.restore(prior,expected_sha256=expected_sha256);data=context.checkpoint(records)
                before=native(state);recovery=native(context.recover(state))
                if before!=native(state):raise ValueError('recovery changed owned state')
                if operation=='enroll':
                    if native(state.mechanical.descriptor())!=native(eq['mechanical']) or strict_bytes(recovery)!=eq['recovery']:
                        raise ValueError('programme enrollment changed source equilibrium/recovery')
                    if data==original['checkpoint.json'] or strict_bytes(data)['model_sha256']==strict_bytes(original['checkpoint.json'])['model_sha256']:
                        raise ValueError('new programme identity not issued')
                elif data!=prior:raise ValueError('fresh owner replay changed original checkpoint bytes')
                write(root/'recovery.json',recovery);status=wanted;failure=None
            else:
                result=owner.solve(made,program,seed,expected_seed_sha256=digest,checkpoint=prior,expected_sha256=expected_sha256,
                    stop_after=step,cancellation_token=token,progress=progress)
                state=result.state;data=result.checkpoint;status=result.status;failure=result.failure
            # Preserve the genuine accepted prefix even if advancement failed.
            write(root/'checkpoint.json',data)
            summary=dict(schema='GE_BEAM3_N32_BRANCH_RESULT_V1',revision=revision,sign=sign,operation=operation,step=step,
                program=desc,status=status,cursor=state.completed_targets,failure=failure,observations=events,seed_sha256=digest,
                prior_sha256=expected_sha256,checkpoint_sha256=sha256(data).hexdigest(),state_sha256=sha256(native(state)).hexdigest(),
                load=state.parameter,production_qualified=False,physical_loading_path_from_rest=False)
            write(root/'result.json',summary);adjudicate(operation,step,status,state.completed_targets,events)
            capsule(data,sign,cursor)
            if operation=='cancel-before' and data!=prior:raise ValueError('cancel-before changed accepted prior')
            if operation not in ('cancel-before','cancel-after') and failure is not None:raise ValueError('unexpected worker failure')
            guard(revision)
            if sources(sign)[0]!=original or (checkpoint is not None and Path(checkpoint).read_bytes()!=prior):raise ValueError('source/prefix changed')
            write(root/'complete.json',dict(schema='GE_BEAM3_N32_BRANCH_COMPLETION_V1',revision=revision,sign=sign,
                operation=operation,step=step,checkpoint_sha256=sha256(data).hexdigest(),result_sha256=sha256(canonical(summary)).hexdigest(),
                fresh_owner_replayed=operation=='replay',physical_loading_path_from_rest=False,production_qualified=False,independent_author_review=False))
            print(dict(stage='N32-branch-worker-complete',sign=sign,operation=operation,step=step,cursor=state.completed_targets,load=state.parameter),flush=True)
    except BaseException:
        write(root/'failure.json',dict(revision=revision,sign=sign,operation=operation,step=step,error=traceback.format_exc(),production_qualified=False))
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--sign',choices=('plus','minus'),required=True)
    p.add_argument('--operation',choices=OPS,required=True);p.add_argument('--step',type=int,required=True);p.add_argument('--output',required=True)
    p.add_argument('--checkpoint');p.add_argument('--expected-sha256');a=p.parse_args()
    run(a.revision,a.sign,a.operation,a.step,a.output,a.checkpoint,a.expected_sha256)
