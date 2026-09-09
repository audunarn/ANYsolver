"""Capture-only successor consuming genuinely issued, immutable N32 prefixes."""
import argparse
from hashlib import sha256
import os
from pathlib import Path
import sys
import traceback
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes,canonical
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT
from docs.reference_cases.ge_beam3_next_spatial_native import member
from docs.reference_cases.ge_beam3_n32_owned_capture import source as equilibrium,validate_packet,POLICY

ARCHIVE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-n32-owned-0db89ad-20260909')
MANIFEST='7abaafe452adc09cd5258256c68231655d6970af628083fb63c7c2ab6934d3e4'
PREFIX={
    'plus':{'seed-input.json':'0a6ffaf93e9044e2458c6a3088da349cdfe49d0febad1b219c31d1a04f45ffa6',
            'checkpoint.json':'a4cfc9161e959b6f29289118adc34281016ee623cd54cace609ae934d2f0e235',
            'recovery.json':'06f378f2b81674c13056b3c7fd95f8cc6d31de5c78d591926e81d05559c165c8'},
    'minus':{'seed-input.json':'32a3cf1e904490257d25dce15c587c5aaf9adec096c5937bafa25c79dbffc68d',
             'checkpoint.json':'37502083b03c3d7f5859cccd0342855a5c0f460d05691d51101bc47e9e2fae19',
             'recovery.json':'c740cbfda40c954562e10e9fa2148b5dec6d7a961c7b7b3d861d4ed3acdc8629'}}
POSITIVE_PACKET='3d64d11ed63ae8401aa755a6d362a7891301306cd55f4225c924a40426ea5e13'
GUARD_POLICY='GE_BEAM3_COMPLIANCE_SNAPSHOT_GUARD_V1'

def sources(sign,root=ARCHIVE):
    if sign not in PREFIX:raise ValueError('registered sign')
    inputs={name:member(root,MANIFEST,'wave/'+sign+'-a/output/'+name,digest)
            for name,digest in PREFIX[sign].items()}
    # Both old replica owners issued the same prefix before factor capture failed.
    for name,digest in PREFIX[sign].items():
        if member(root,MANIFEST,'wave/'+sign+'-b/output/'+name,digest)!=inputs[name]:
            raise ValueError('issued-prefix replica mismatch')
    raw,v=equilibrium(sign)
    seed=strict_bytes(inputs['seed-input.json']);checkpoint=strict_bytes(inputs['checkpoint.json'])
    if seed['source_sha256']!=sha256(raw).hexdigest() or seed['mechanical']!=v['mechanical'] or seed['parameter']!=v['load']:
        raise ValueError('same actual source equilibrium')
    if checkpoint['records']!=[] or strict_bytes(inputs['recovery.json'])!=v['recovery']:
        raise ValueError('issued genesis only and unchanged recovery')
    return inputs,v

def positive_equivalence(packet,root=ARCHIVE):
    old=strict_bytes(member(root,MANIFEST,'wave/plus-a/output/packet.json',POSITIVE_PACKET))
    if canonical(packet)!=canonical(old['packet']):raise ValueError('original positive factor packet changed')
    return sha256(canonical(packet)).hexdigest()

def run(revision,sign,output):
    guard(revision);inputs,v=sources(sign)
    if any(os.environ.get(k)!=x for k,x in THREAD_ENVIRONMENT.items()):raise ValueError('one numerical thread')
    root=Path(output).resolve()
    if root.is_relative_to(ROOT):raise ValueError('exclusive external output')
    root.mkdir(exist_ok=False);sys.path.insert(0,str(ROOT/'src'))
    from anysolver import _ge_beam3_elastic_seed_modal as modal
    from anysolver import _ge_beam3_elastic_seed_continuation as owner
    from anysolver._ge_beam3_compliance_snapshot_guard import POLICY as actual_policy
    from anysolver._ge_beam3_refinement_capacity import n32_refinement_capacity
    from anysolver._ge_beam3_retained_nodal_loading import NodalDeadForces
    from anysolver._ge_beam3_p5_seeded.core import canonical as native
    from docs.reference_cases.ge_beam3_n32_controlled_case import model
    from docs.reference_cases.ge_beam3_refined_controlled_case import masses
    def progress(stage):print(dict(stage=stage,sign=sign),flush=True)
    try:
        if actual_policy!=GUARD_POLICY:raise ValueError('registered snapshot policy')
        for name,raw in inputs.items():write(root/name,raw)
        progress('issued-prefix-authority-complete')
        with n32_refinement_capacity():
            made=model(32,arithmetic_policy=POLICY)
            program=owner.Program((v['amplitude'],),17,(0.,0.,1.),NodalDeadForces(((33,0.,-1.,0.),)))
            # prepare still performs its own native enrollment and exact replay.
            # No equilibrium solve, history advance, or expired timer reuse.
            packet,check=modal.prepare(made,program,inputs['seed-input.json'],inputs['checkpoint.json'],masses(made),
                expected_seed_sha256=PREFIX[sign]['seed-input.json'],expected_sha256=PREFIX[sign]['checkpoint.json'],
                compliance_guard_policy=GUARD_POLICY)
            check();p=strict_bytes(native(packet));check()
            progress('native-original-factor-capture-complete')
            validate_packet(p,sign,inputs['seed-input.json'],inputs['checkpoint.json'],v['load'])
            equivalence=positive_equivalence(p) if sign=='plus' else None
            if sources(sign)[0]!=inputs:raise ValueError('issued inputs changed')
            guard(revision)
            wrapper=dict(schema='GE_BEAM3_N32_SNAPSHOT_FACTORS_V1',revision=revision,sign=sign,
                source_manifest_sha256=MANIFEST,arithmetic_policy=POLICY,compliance_guard_policy=GUARD_POLICY,
                packet=p,production_qualified=False)
            raw=native(wrapper);strict_bytes(raw);write(root/'packet.json',raw)
            write(root/'complete.json',dict(schema='GE_BEAM3_N32_SNAPSHOT_CAPTURE_V1',revision=revision,sign=sign,
                source_manifest_sha256=MANIFEST,input_hashes=PREFIX[sign],packet_sha256=sha256(raw).hexdigest(),
                compliance_guard_policy=GUARD_POLICY,positive_original_packet_body_sha256=equivalence,
                original_deadline_unchanged=True,history_advanced=False,completed_targets=0,
                physical_loading_path_from_rest=False,modal_comparison_passed=False,
                production_qualified=False,independent_author_review=False))
            progress('capture-only-complete')
    except BaseException:
        write(root/'failure.json',dict(revision=revision,sign=sign,error=traceback.format_exc(),production_qualified=False))
        raise

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--revision',required=True)
    parser.add_argument('--sign',choices=('plus','minus'),required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();run(args.revision,args.sign,args.output)
