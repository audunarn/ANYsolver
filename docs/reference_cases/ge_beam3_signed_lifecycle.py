"""Research-only signed continuation and real commit-boundary cancellation."""
from pathlib import Path
from hashlib import sha256
import argparse,sys
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes,read,canonical
from docs.reference_cases.ge_beam3_spatial_continuum_worker import source

ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-elastic-continuation-7701e35-20260909')
MANIFEST_SHA='fdbae90dea53f7226d9451ff46da10caf8ac1571848ab8d0a4bcc05fe7c30e97'
OWNER_SHA='9d0bf7a01a0577a1867090a1ac4828eb6df2c45d902bcb1767280f007faa9045'
POSITIVES={'prefix':('smoke/output/checkpoint.json','2e4a553cf4f3ee77adc8cdbe79c4c23ff8747204103f4f976022e77f7ebb4d2d'),
           'full':('resume/a/output/checkpoint.json','1ceffb6a7a35b85fca86920a5b804ef062e736e6532379e5b094c665233accab')}

def positive(name,archive=ARCHIVE):
    if name not in POSITIVES:raise ValueError('registered positive capsule')
    manifest=read(archive/'manifest.json')
    if sha256(manifest).hexdigest()!=MANIFEST_SHA:raise ValueError('positive archive manifest')
    path,digest=POSITIVES[name];entries={r['path']:r for r in strict_bytes(manifest)['entries']}
    raw=read(archive/path)
    if sha256(raw).hexdigest()!=digest or entries[path]['sha256']!=digest or len(raw)!=entries[path]['bytes']:
        raise ValueError('positive capsule authority')
    strict_bytes(raw);return raw

def recipe(operation):
    cases={'negative-seed':(-1.,1,'paused',1,None),
           'negative-resume':(-1.,2,'completed',2,None),
           'cancel-before':(1.,2,'cancelled',1,'elastic-continuation.before_commit'),
           'cancel-after':(1.,2,'cancelled',2,'elastic-continuation.committed'),
           'resume-cancelled':(1.,2,'completed',2,None)}
    if type(operation) is not str or operation not in cases:raise ValueError('registered signed lifecycle operation')
    return cases[operation]

def disposition(operation,status,cursor,observations):
    _,_,expected,count,event=recipe(operation)
    if status!=expected or type(cursor) is not int or cursor!=count:raise ValueError('lifecycle outcome/cursor')
    if type(observations) is not list:raise ValueError('actual cancellation observation list')
    if event is None:
        if observations:raise ValueError('unexpected cancellation')
    elif (len(observations)!=1 or set(observations[0])!={'stage','target','iteration'}
          or observations[0]['stage']!=event or type(observations[0]['target']) is not int or observations[0]['target']!=2
          or type(observations[0]['iteration']) is not int or not 0<=observations[0]['iteration']<=24):
        raise ValueError('actual target2 cancellation callback required')

def run(revision,operation,output,checkpoint=None,expected_sha256=None):
    guard(revision);sign,end,expected,cursor,event=recipe(operation)
    if sha256(read(ROOT/'src/anysolver/_ge_beam3_elastic_seed_continuation.py')).hexdigest()!=OWNER_SHA:
        raise ValueError('unchanged elastic owner required')
    if operation in ('negative-resume','resume-cancelled'):
        if checkpoint is None or expected_sha256 is None:raise ValueError('bound actual predecessor required')
        prior=read(checkpoint)
        if sha256(prior).hexdigest()!=expected_sha256 or strict_bytes(prior)['completed_targets']!=1:raise ValueError('one-record predecessor hash/cursor')
        if operation=='resume-cancelled' and prior!=positive('prefix'):raise ValueError('exact cancellation predecessor required')
    else:
        if checkpoint is not None or expected_sha256 is not None:raise ValueError('unregistered prior input')
        prior=positive('prefix') if event else None
        expected_sha256=None if prior is None else sha256(prior).hexdigest()
    case='minus-small' if sign<0 else 'plus-small';raw,diagnostic=source(case)
    root=Path(output).resolve()
    if root.exists() or root.is_relative_to(ROOT):raise ValueError('fresh external lifecycle output')
    root.mkdir();sys.path.insert(0,str(ROOT/'src'))
    from anysolver import _ge_beam3_elastic_seed_continuation as owner
    from anysolver._ge_beam3_retained_nodal_loading import Context as Physical,Program as ForceProgram,NodalDeadForces
    from anysolver._ge_beam3_native_generalized_loading import DistributedPattern
    from anysolver._ge_beam3_native_line_loading import LinePattern
    from anysolver._ge_beam3_p5_seeded.core import canonical as native
    from anysolver.control import CancellationToken
    from docs.reference_cases.ge_beam3_refined_controlled_case import model
    programme=owner.Program((sign*.0045,sign*.006),11,(0.,0.,1.),NodalDeadForces(((21,0.,-1.,0.),)))
    made=model(20);capture=Physical(made,ForceProgram((0.,),DistributedPattern(LinePattern(()),()),programme.nodal_forces))
    seed=native(dict(schema=owner.SEED_SCHEMA,model_sha256=capture.model_identity,
        operators=[e.operator.identity for _,e in capture.elements],control_node=11,direction=programme.direction,
        nodal_forces=programme.nodal_forces,mechanical=diagnostic['mechanical'],parameter=diagnostic['load'],
        displacement=diagnostic['amplitude'],source_sha256=sha256(raw).hexdigest()))
    with (root/'seed.json').open('xb') as f:f.write(seed)
    token=CancellationToken();observations=[]
    def progress(row):
        print(row,flush=True)
        if row['stage']==event and row['target']==2:
            observations.append(dict(row));token.cancel()
    result=owner.solve(made,programme,seed,expected_seed_sha256=sha256(seed).hexdigest(),checkpoint=prior,
        expected_sha256=expected_sha256,stop_after=end,cancellation_token=token,progress=progress)
    with (root/'checkpoint.json').open('xb') as f:f.write(result.checkpoint)
    summary=dict(schema='GE_BEAM3_SIGNED_SPATIAL_LIFECYCLE_RESULT_V1',revision=revision,operation=operation,
        status=result.status,cursor=result.completed_targets,failure=result.failure,observations=observations,
        seed_sha256=sha256(seed).hexdigest(),source_sha256=sha256(raw).hexdigest(),prior_sha256=expected_sha256,
        checkpoint_sha256=sha256(result.checkpoint).hexdigest(),production_qualified=False,physical_loading_path_from_rest=False)
    with (root/'result.json').open('xb') as f:f.write(canonical(summary))
    disposition(operation,result.status,result.completed_targets,observations)
    if operation in ('cancel-before','cancel-after','resume-cancelled'):
        wanted=positive('prefix' if operation=='cancel-before' else 'full')
        if result.checkpoint!=wanted:raise ValueError('cancellation/restart did not preserve original bytes')
    replay=owner.Context(model(20),programme,seed,expected_seed_sha256=sha256(seed).hexdigest())
    state,records=replay.restore(result.checkpoint,expected_sha256=summary['checkpoint_sha256'])
    if replay.checkpoint(records)!=result.checkpoint:raise ValueError('actual lifecycle checkpoint replay differs')
    recovered=native(replay.recover(state))
    with (root/'recovery.json').open('xb') as f:f.write(recovered)
    guard(revision)
    if source(case)[0]!=raw or (checkpoint is not None and read(checkpoint)!=prior):raise ValueError('lifecycle source changed')
    with (root/'complete.json').open('xb') as f:f.write(canonical(dict(revision=revision,operation=operation,
        checkpoint_sha256=summary['checkpoint_sha256'],recovery_sha256=sha256(recovered).hexdigest(),
        actual_original_checkpoint_replay=True,production_qualified=False)))
    print(dict(stage='signed-lifecycle-complete',operation=operation,cursor=result.completed_targets,load=state.parameter),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--operation',required=True)
    p.add_argument('--output',required=True);p.add_argument('--checkpoint');p.add_argument('--expected-sha256')
    a=p.parse_args();run(a.revision,a.operation,a.output,a.checkpoint,a.expected_sha256)
