"""Bounded research execution of the private authenticated spatial owner."""
from pathlib import Path
from hashlib import sha256
import argparse,sys
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes
from docs.reference_cases.ge_beam3_spatial_continuum_worker import source

def run(revision,output,stage,checkpoint=None,expected_sha256=None):
    guard(revision)
    if stage not in (1,2):raise ValueError('registered continuation stage')
    if (checkpoint is None)!=(expected_sha256 is None):raise ValueError('complete prior checkpoint binding')
    if stage==1 and checkpoint is not None:raise ValueError('smoke begins at authentic seed')
    if stage==2 and checkpoint is None:raise ValueError('stage two resumes original prefix')
    seed_source,diagnostic=source('plus-small')
    prior=None if checkpoint is None else Path(checkpoint).read_bytes()
    if prior is not None:
        if sha256(prior).hexdigest()!=expected_sha256 or strict_bytes(prior)['completed_targets']!=1:
            raise ValueError('original one-record prefix required')
    root=Path(output).resolve()
    if root.exists() or root.is_relative_to(ROOT):raise ValueError('fresh external continuation output')
    root.mkdir();sys.path.insert(0,str(ROOT/'src'))
    from anysolver import _ge_beam3_elastic_seed_continuation as owner
    from anysolver._ge_beam3_retained_nodal_loading import Context as Physical,Program as ForceProgram
    from anysolver._ge_beam3_native_generalized_loading import DistributedPattern
    from anysolver._ge_beam3_native_line_loading import LinePattern
    from anysolver._ge_beam3_p5_seeded.core import canonical
    from docs.reference_cases.ge_beam3_refined_controlled_case import model
    from anysolver._ge_beam3_retained_nodal_loading import NodalDeadForces
    programme=owner.Program((.0045,.006),11,(0.,0.,1.),NodalDeadForces(((21,0.,-1.,0.),)))
    made=model(20)
    capture=Physical(made,ForceProgram((0.,),DistributedPattern(LinePattern(()),()),programme.nodal_forces))
    seed=canonical(dict(schema=owner.SEED_SCHEMA,model_sha256=capture.model_identity,
        operators=[e.operator.identity for _,e in capture.elements],control_node=11,direction=programme.direction,
        nodal_forces=programme.nodal_forces,mechanical=diagnostic['mechanical'],parameter=diagnostic['load'],
        displacement=diagnostic['amplitude'],source_sha256=sha256(seed_source).hexdigest()))
    with (root/'seed.json').open('xb') as f:f.write(seed)
    seed_sha=sha256(seed).hexdigest()
    print(dict(stage='seed-input-captured',sha256=seed_sha),flush=True)
    result=owner.solve(made,programme,seed,expected_seed_sha256=seed_sha,checkpoint=prior,
        expected_sha256=expected_sha256,stop_after=stage,progress=lambda row:print(row,flush=True))
    with (root/'checkpoint.json').open('xb') as f:f.write(result.checkpoint)
    summary=dict(schema='GE_BEAM3_ELASTIC_SPATIAL_CONTINUATION_DIAGNOSTIC_V1',revision=revision,
        stage=stage,status=result.status,failure=result.failure,completed_targets=result.completed_targets,
        seed_sha256=seed_sha,source_sha256=sha256(seed_source).hexdigest(),
        prior_sha256=expected_sha256,checkpoint_sha256=sha256(result.checkpoint).hexdigest(),
        parameter=result.state.parameter,mechanical=result.state.mechanical.descriptor(),
        production_qualified=False,physical_loading_path_from_rest=False)
    with (root/'result.json').open('xb') as f:f.write(canonical(summary))
    if result.status!=('paused' if stage==1 else 'completed') or result.completed_targets!=stage:
        raise RuntimeError('continuation failed; accepted prefix preserved: '+str(result.failure))
    # A fresh owner mechanically replays the actual capsule, not a reconstructed
    # self-consistent substitute. Recovery follows replay with original origins.
    replay=owner.Context(model(20),programme,seed,expected_seed_sha256=seed_sha)
    state,records=replay.restore(result.checkpoint,expected_sha256=summary['checkpoint_sha256'])
    if replay.checkpoint(records)!=result.checkpoint:raise ValueError('original prefix replay changed')
    recovered=replay.recover(state)
    with (root/'recovery.json').open('xb') as f:f.write(canonical(recovered))
    guard(revision)
    if source('plus-small')[0]!=seed_source:raise ValueError('seed source changed')
    if prior is not None and Path(checkpoint).read_bytes()!=prior:raise ValueError('original checkpoint changed')
    with (root/'complete.json').open('xb') as f:f.write(canonical(dict(revision=revision,stage=stage,
        checkpoint_sha256=summary['checkpoint_sha256'],original_checkpoint_replay_identical=True,
        recovery_sha256=sha256(canonical(recovered)).hexdigest(),production_qualified=False)))
    print(dict(stage='elastic-continuation-evidence-complete',completed=result.completed_targets,load=state.parameter),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--output',required=True)
    p.add_argument('--stage',required=True,type=int);p.add_argument('--checkpoint');p.add_argument('--expected-sha256')
    a=p.parse_args();run(a.revision,a.output,a.stage,a.checkpoint,a.expected_sha256)
