"""New-owner native precise-work gate on immutable signed endpoint fields."""
import argparse,json,os
from hashlib import sha256
from pathlib import Path
from docs.reference_cases.ge_beam3_native_directional_worker import guard,ROOT,THREAD_ENVIRONMENT,inputs,load,witness_input,PACKETS,WITNESS,CHECK
from docs.reference_cases.ge_beam3_retained_prestress_wave import write


def run(revision,sign,output):
    guard(revision)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('single numerical thread')
    source=inputs(sign);packet=load(sign);witness,checked,expected=witness_input(sign)
    root=Path(output).resolve()
    if root.is_relative_to(ROOT):raise ValueError('fresh external output required')
    root.mkdir(exist_ok=False);diagnostics=root/'diagnostics';diagnostics.mkdir(exist_ok=False)
    import sys
    sys.path.insert(0,str(ROOT/'src'))
    from anysolver import _ge_beam3_elastic_seed_continuation as owner
    from anysolver._ge_beam3_precise_geometric_work import POLICY
    from anysolver._ge_beam3_retained_nodal_loading import NodalDeadForces
    from anysolver._ge_beam3_p5_seeded.core import canonical
    from docs.reference_cases.ge_beam3_refined_controlled_case import model
    from docs.reference_cases.ge_beam3_precise_work_enrollment import enroll
    from docs.reference_cases.ge_beam3_native_directional_work import evaluate,adjudicate
    direction=1. if sign=='plus' else -1.
    # The following target registers an unused continuation programme, not a solve.
    program=owner.Program((direction*.0065,),13,(0.,0.,1.),NodalDeadForces(((25,0.,-1.,0.),)))
    print(dict(stage='new-precise-equilibrium-enrollment',sign=sign),flush=True)
    context,seed=enroll(model(24,arithmetic_policy=POLICY),program,source['checkpoint.json'],sha256(source['checkpoint.json']).hexdigest())
    state=context.initial;checkpoint=context.checkpoint(())
    write(diagnostics/'seed.json',seed);write(diagnostics/'checkpoint.json',checkpoint)
    state_bytes=canonical(state);recovery=canonical(context.recover(state));bindings=[]
    def record(row):
        path=diagnostics/('point-'+str(len(bindings))+'.json');write(path,row);raw=path.read_bytes()
        bindings.append(dict(path=path.name,bytes=len(raw),sha256=sha256(raw).hexdigest()))
    result=evaluate(context,state,packet,witness['direction'],progress=lambda row:print(row,flush=True),record=record)
    write(diagnostics/'unadjudicated.json',dict(result=result,expected=expected,raw=bindings,disposition='UNADJUDICATED'))
    adjudicate(result,expected)
    if (canonical(state)!=state_bytes or canonical(context.recover(state))!=recovery
            or context.checkpoint(())!=checkpoint):raise ValueError('new accepted state/checkpoint/recovery changed')
    # Actual new-owner replay; old checkpoint never supplied as a new checkpoint.
    replay,records=context.restore(checkpoint,expected_sha256=sha256(checkpoint).hexdigest())
    if canonical(replay)!=state_bytes or records!=():raise ValueError('new genesis replay mismatch')
    guard(revision)
    if inputs(sign)!=source or witness_input(sign)!=(witness,checked,expected):raise ValueError('source evidence changed')
    load(sign)
    write(root/'precise.json',dict(schema='GE_BEAM3_PRECISE_NATIVE_SIGNED_SECOND_VARIATION_V1',revision=revision,
        arithmetic_policy=POLICY,sign=sign,source_checkpoint_sha256=sha256(source['checkpoint.json']).hexdigest(),
        source_packet_sha256=PACKETS[sign],source_witness_sha256=WITNESS[sign],source_exact_sha256=CHECK[sign],
        seed_sha256=sha256(seed).hexdigest(),checkpoint_sha256=sha256(checkpoint).hexdigest(),
        recovery_sha256=sha256(recovery).hexdigest(),result=result,new_genesis_replayed=True,
        history_advanced=False,original_chain_relabelled=False,physical_loading_path_from_rest=False,
        production_qualified=False,independent_author_review='PENDING'))
    print(dict(stage='precise-native-gate-complete',sign=sign),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--sign',choices=('plus','minus'),required=True)
    p.add_argument('--output',required=True);a=p.parse_args();run(a.revision,a.sign,a.output)
