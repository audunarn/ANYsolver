"""Same-state precise-policy native capture and saved-factor checks only."""
import argparse
from hashlib import sha256
from math import isfinite
import os
from pathlib import Path
import sys
from docs.reference_cases.ge_beam3_fibre_arch_probe import guard,ROOT
from docs.reference_cases.ge_beam3_retained_prestress_protocol import strict_bytes,canonical
from docs.reference_cases.ge_beam3_retained_prestress_wave import write
from docs.reference_cases.e4_pl_s3_v2_bounded_process import THREAD_ENVIRONMENT

ENDPOINT=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-precise-continuation-43f18e3-20260909')
ENDPOINT_SHA='b7bcc4a9e513050a42b1542b081ba3c8ed22ff108044a6b5cdbb15586746cfac'
TRIAL=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-spatial-trial-9555a25-20260909')
TRIAL_SHA='7b994d3dda0bafeb3714b238b69e48619217d5df2b90fdbe5a62215ba14b81eb'
CHECKPOINT={'plus':'b1c74d0ff21bb4bc6e8bfc4f038bca16ebfc6eba4e1eecce5cd317cf0ea0702a',
            'minus':'602241bee7a56edd7834ba5dc613873a2c52ae42d840807ad098dcf569586c5d'}
TRIAL_WORK={'plus':'5feda98ccba52eecdd88272002ee3961264f1afd9d11f8f4edab8cc499bec8f6',
            'minus':'feeb287a52d5a1f05a5d88d95ecfffef64467b6c260923a782b74bf8b899341b'}
BODY=('left','right','geometric','kinetic','stiffness','mass','net_residual','free_dofs','algebraic_dofs',
      'internal_layout','compliance_errors','checkpoint_sha256','model_sha256','parameter','completed_targets','displacement_target')


def member(root,manifest_sha,relative,expected):
    raw=(root/'manifest.json').read_bytes()
    if sha256(raw).hexdigest()!=manifest_sha:raise ValueError('registered archive manifest')
    rows=[r for r in strict_bytes(raw)['entries'] if r['path']==relative]
    if len(rows)!=1 or rows[0]['sha256']!=expected:raise ValueError('unique hash-bound archive member')
    raw=(root/relative).read_bytes()
    if len(raw)!=rows[0]['bytes'] or sha256(raw).hexdigest()!=expected:raise ValueError('archive member bytes')
    strict_bytes(raw);return raw


def source(sign):
    if sign not in CHECKPOINT:raise ValueError('registered signed endpoint')
    from docs.reference_cases.ge_beam3_precise_continuation import source as enrolled
    old=enrolled(sign)
    checkpoint=member(ENDPOINT,ENDPOINT_SHA,'wave/'+sign+'-a/output/checkpoint.json',CHECKPOINT[sign])
    trial=member(TRIAL,TRIAL_SHA,'wave/'+sign+'-a/output/trial-work.json',TRIAL_WORK[sign])
    return old['seed.json'],checkpoint,trial


def validate(p,sign,seed,checkpoint):
    if (p['seed_sha256']!=sha256(seed).hexdigest() or p['checkpoint_sha256']!=sha256(checkpoint).hexdigest()
            or type(p['completed_targets']) is not int or p['completed_targets']!=1
            or p['displacement_target']!=(.0065 if sign=='plus' else -.0065)
            or p['control_constraint_in_physical_stiffness'] is not False
            or p['physical_loading_path_from_rest'] is not False or p['production_qualified'] is not False):
        raise ValueError('same-state ownership/target/physical-policy binding')
    if sha256(canonical(dict(policy=p['policy'],**{k:p[k] for k in BODY}))).hexdigest()!=p['identity']:
        raise ValueError('actual native factor identity')
    expected_free=list(range(6,288))+list(range(294,438))
    expected_algebraic=[6*i+j for i in range(1,48) for j in (3,4,5)]
    if p['free_dofs']!=expected_free or p['algebraic_dofs']!=expected_algebraic:
        raise ValueError('physical clamps only; controller must remain free')
    if p['internal_layout']!=[[i+1,list(range(294+6*i,300+6*i))] for i in range(24)]:
        raise ValueError('all internal spatial rotations retained')
    for name,rows,columns in (('left',432,432),('right',432,438),('geometric',438,438),('stiffness',438,438),('mass',438,438)):
        a=p[name]
        if len(a)!=rows or any(len(row)!=columns or any(type(x) is not float or not isfinite(x) for x in row) for row in a):
            raise ValueError('complete finite native factor shape: '+name)


def capture(revision,sign,root):
    seed,checkpoint,trial=source(sign)
    sys.path.insert(0,str(ROOT/'src'))
    from anysolver import _ge_beam3_elastic_seed_modal as modal
    from anysolver import _ge_beam3_elastic_seed_continuation as owner
    from anysolver._ge_beam3_precise_geometric_work import POLICY
    from anysolver._ge_beam3_retained_nodal_loading import NodalDeadForces
    from anysolver._ge_beam3_p5_seeded.core import canonical as native
    from docs.reference_cases.ge_beam3_refined_controlled_case import model,masses
    program=owner.Program(((.0065 if sign=='plus' else -.0065),),13,(0.,0.,1.),NodalDeadForces(((25,0.,-1.,0.),)))
    made=model(24,arithmetic_policy=POLICY)
    print(dict(stage='same-state-authenticated-native-replay',sign=sign),flush=True)
    packet,check=modal.prepare(made,program,seed,checkpoint,masses(made),
        expected_seed_sha256=sha256(seed).hexdigest(),expected_sha256=sha256(checkpoint).hexdigest())
    p=strict_bytes(native(packet));validate(p,sign,seed,checkpoint)
    print(dict(stage='same-state-native-factors-complete',coordinates=438,free=426),flush=True)
    check();guard(revision)
    if source(sign)!=(seed,checkpoint,trial):raise ValueError('immutable endpoint inputs changed')
    write(root/'packet.json',dict(schema='GE_BEAM3_PRECISE_NEXT_SPATIAL_FACTORS_V1',revision=revision,sign=sign,
        arithmetic_policy=POLICY,endpoint_manifest_sha256=ENDPOINT_SHA,trial_sha256=TRIAL_WORK[sign],
        packet=p,production_qualified=False))


def verify(revision,path,digest,digits,root):
    raw=Path(path).read_bytes()
    if sha256(raw).hexdigest()!=digest:raise ValueError('external packet SHA-256')
    wrapper=strict_bytes(raw)
    if (set(wrapper)!={'schema','revision','sign','arithmetic_policy','endpoint_manifest_sha256','trial_sha256','packet','production_qualified'}
            or wrapper['schema']!='GE_BEAM3_PRECISE_NEXT_SPATIAL_FACTORS_V1' or wrapper['revision']!=revision
            or wrapper['endpoint_manifest_sha256']!=ENDPOINT_SHA or wrapper['production_qualified'] is not False
            or wrapper['arithmetic_policy']!='GE_BEAM3_RETAINED_GEOMETRIC_WORK_DECIMAL80_V1'):
        raise ValueError('exact native capture wrapper authority')
    sign=wrapper['sign'];seed,checkpoint,trial_raw=source(sign);trial=strict_bytes(trial_raw)
    if wrapper['trial_sha256']!=TRIAL_WORK[sign]:raise ValueError('same-state reference identity')
    p=wrapper['packet'];validate(p,sign,seed,checkpoint)
    from docs.reference_cases.ge_beam3_scaled_energy_inertia import audit
    print(dict(stage='same-state-full-native-inertia',sign=sign,digits=digits),flush=True)
    result=audit(p['left'],p['right'],p['geometric'],p['kinetic'],tuple(p['free_dofs']),tuple(p['algebraic_dofs']),(0.,),digits=digits)
    if result['physical_dimension']!=285 or result['algebraic_dimension']!=141:raise ValueError('full mass/algebraic split')
    native_negative=result['rows'][0]['negative']>0
    # This checks signs at the same load-controlled endpoint, not equality of
    # differently normalized directions or a complete continuum inertia count.
    agree=native_negative and trial['numerical_negative_direction'] is True
    guard(revision)
    if Path(path).read_bytes()!=raw or source(sign)!=(seed,checkpoint,trial_raw):raise ValueError('input changed during audit')
    write(root/'inertia.json',dict(schema='GE_BEAM3_SAME_STATE_NATIVE_CONTINUUM_STABILITY_V1',revision=revision,
        sign=sign,packet_sha256=digest,trial_sha256=TRIAL_WORK[sign],result=result,
        native_and_continuum_negative=agree,continuum_full_inertia_proved=False,
        physical_loading_path_from_rest=False,production_qualified=False,independent_author_review=False))
    print(dict(stage='same-state-inertia-complete',negative=result['rows'][0]['negative'],agreement=agree),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--revision',required=True)
    parser.add_argument('--mode',choices=('capture','audit'),required=True);parser.add_argument('--sign',choices=('plus','minus'))
    parser.add_argument('--packet');parser.add_argument('--sha256');parser.add_argument('--digits',type=int,choices=(80,100))
    parser.add_argument('--output',required=True);a=parser.parse_args();guard(a.revision)
    if any(os.environ.get(k)!=v for k,v in THREAD_ENVIRONMENT.items()):raise ValueError('single numerical thread')
    root=Path(a.output).resolve()
    if root.is_relative_to(ROOT):raise ValueError('fresh external output required')
    root.mkdir(exist_ok=False)
    if a.mode=='capture':capture(a.revision,a.sign,root)
    else:verify(a.revision,a.packet,a.sha256,a.digits,root)
