"""Frozen precise-arithmetic endpoint continuation and actual cancellation."""
import argparse,sys,os
from pathlib import Path
from hashlib import sha256
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes,read,canonical
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT

ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-precise-native-e9cf909-20260909')
MANIFEST='5be3566fbf5f420f73eef5856a56447c21d44ea8cd23303e714505f7ab9c063c'
INPUTS={'plus':{'seed.json':'f67be814eb841436d78e0bb3eb58729072df3f354036613afe5d7be6d9955308',
                'checkpoint.json':'a7880da4bf9bc0829f93c2b4ed97e87b816bcf8fd7c9016d548214d01e920c08'},
        'minus':{'seed.json':'962a2aad283b6a72d7737215882c9fd1f8a09469670d3208ca928f5f86caca55',
                 'checkpoint.json':'cbb81aa72e28ba7274f797fb4941f75a4703781fcd041429cfdf1190f899455a'}}


def source(sign,archive=ARCHIVE):
    if sign not in INPUTS:raise ValueError('registered signed source')
    raw=read(archive/'manifest.json')
    if sha256(raw).hexdigest()!=MANIFEST:raise ValueError('precise source archive manifest')
    entries={r['path']:r for r in strict_bytes(raw)['entries']};result={}
    for name,digest in INPUTS[sign].items():
        path='wave/'+sign+'-a/output/diagnostics/'+name;data=read(archive/path)
        if len(data)!=entries[path]['bytes'] or sha256(data).hexdigest()!=digest or entries[path]['sha256']!=digest:
            raise ValueError('source seed/checkpoint binding')
        strict_bytes(data);result[name]=data
    return result


def recipe(operation):
    choices={'advance':('completed',1,None),'cancel-before':('cancelled',0,'elastic-continuation.before_commit'),
             'cancel-after':('cancelled',1,'elastic-continuation.committed'),'resume-before':('completed',1,None)}
    if type(operation) is not str or operation not in choices:raise ValueError('registered precise lifecycle operation')
    return choices[operation]


def adjudicate(operation,status,cursor,observed):
    wanted,count,event=recipe(operation)
    if status!=wanted or type(cursor) is not int or cursor!=count:raise ValueError('lifecycle disposition/cursor')
    if type(observed) is not list:raise ValueError('event list')
    if event is None:
        if observed:raise ValueError('unexpected cancellation event')
    elif (len(observed)!=1 or set(observed[0])!={'stage','target','iteration'} or observed[0]['stage']!=event
            or type(observed[0]['target']) is not int or observed[0]['target']!=1
            or type(observed[0]['iteration']) is not int or not 0<=observed[0]['iteration']<=24):
        raise ValueError('actual target-one commit-boundary cancellation required')


def run(revision,sign,operation,output,checkpoint=None,expected_sha256=None):
    guard(revision);wanted,cursor,event=recipe(operation)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('one numerical thread')
    original=source(sign);prior=original['checkpoint.json']
    if operation=='resume-before':
        if checkpoint is None or expected_sha256 is None:raise ValueError('bound actual cancellation capsule required')
        prior=read(checkpoint)
        if sha256(prior).hexdigest()!=expected_sha256 or prior!=original['checkpoint.json']:
            raise ValueError('exact actual pre-commit capsule required')
    elif checkpoint is not None or expected_sha256 is not None:raise ValueError('unregistered extra input')
    if operation in ('cancel-before','cancel-after','resume-before') and sign!='plus':raise ValueError('positive lifecycle registered')
    root=Path(output).resolve()
    if root.is_relative_to(ROOT):raise ValueError('fresh external output required')
    root.mkdir(exist_ok=False);sys.path.insert(0,str(ROOT/'src'))
    from anysolver import _ge_beam3_elastic_seed_continuation as owner
    from anysolver._ge_beam3_precise_geometric_work import POLICY
    from anysolver._ge_beam3_retained_nodal_loading import NodalDeadForces
    from anysolver._ge_beam3_p5_seeded.core import canonical as native
    from anysolver.control import CancellationToken
    from docs.reference_cases.ge_beam3_refined_controlled_case import model
    s=1. if sign=='plus' else -1.
    program=owner.Program((s*.0065,),13,(0.,0.,1.),NodalDeadForces(((25,0.,-1.,0.),)))
    seed=original['seed.json'];seed_sha=sha256(seed).hexdigest();prior_sha=sha256(prior).hexdigest()
    token=CancellationToken();observed=[]
    def progress(row):
        print(row,flush=True)
        if row['stage']==event and row['target']==1:observed.append(dict(row));token.cancel()
    result=owner.solve(model(24,arithmetic_policy=POLICY),program,seed,expected_seed_sha256=seed_sha,
        checkpoint=prior,expected_sha256=prior_sha,cancellation_token=token,progress=progress)
    # Preserve genuine accepted prefixes and failure status even on rejection.
    write(root/'checkpoint.json',result.checkpoint)
    summary=dict(schema='GE_BEAM3_PRECISE_SIGNED_CONTINUATION_RESULT_V1',revision=revision,sign=sign,operation=operation,
        status=result.status,cursor=result.completed_targets,failure=result.failure,observations=observed,
        seed_sha256=seed_sha,prior_sha256=prior_sha,checkpoint_sha256=sha256(result.checkpoint).hexdigest(),
        load=result.state.parameter,production_qualified=False,physical_loading_path_from_rest=False)
    write(root/'result.json',summary);adjudicate(operation,result.status,result.completed_targets,observed)
    if operation=='cancel-before' and result.checkpoint!=prior:raise ValueError('cancel-before altered accepted prefix')
    # Independent owner instance mechanically validates the resulting chain.
    replay=owner.Context(model(24,arithmetic_policy=POLICY),program,seed,expected_seed_sha256=seed_sha)
    state,records=replay.restore(result.checkpoint,expected_sha256=summary['checkpoint_sha256'])
    if replay.checkpoint(records)!=result.checkpoint:raise ValueError('original continuation bytes changed on replay')
    before=native(state);recovered=native(replay.recover(state))
    if native(state)!=before:raise ValueError('recovery changed accepted state')
    write(root/'recovery.json',recovered)
    if result.completed_targets:
        final=strict_bytes(records[-1])
        if max(*final['metrics'],final['correction'])>1e-11 or final['displacement_target']!=s*.0065:
            raise ValueError('actual equilibrium/correction/target')
        if final['origins']!=final['histories']:raise ValueError('elastic history advanced')
    guard(revision)
    if source(sign)!=original or (checkpoint is not None and read(checkpoint)!=prior):raise ValueError('source evidence changed')
    write(root/'complete.json',dict(schema='GE_BEAM3_PRECISE_CONTINUATION_REPLAY_V1',revision=revision,
        sign=sign,operation=operation,checkpoint_sha256=summary['checkpoint_sha256'],recovery_sha256=sha256(recovered).hexdigest(),
        original_checkpoint_replayed=True,source_prior_unchanged=True,production_qualified=False))
    print(dict(stage='precise-continuation-complete',sign=sign,operation=operation,load=state.parameter),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--sign',choices=('plus','minus'),required=True)
    p.add_argument('--operation',required=True);p.add_argument('--output',required=True)
    p.add_argument('--checkpoint');p.add_argument('--expected-sha256');a=p.parse_args()
    run(a.revision,a.sign,a.operation,a.output,a.checkpoint,a.expected_sha256)
