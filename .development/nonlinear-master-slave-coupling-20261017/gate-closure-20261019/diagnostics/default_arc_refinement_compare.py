"""Read-only pair comparison, preserving raw identities and root equivalence."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

PHASE=Path(__file__).resolve().parents[1]
TASK=PHASE.parent
REPO=TASK.parents[1]


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--coarse',type=Path,required=True)
    p.add_argument('--fine',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    coarse,fine=load(args.coarse),load(args.fine)
    attestation=PHASE/'analytical-source-equivalence-assessment.json'
    att=load(attestation)
    frozen=load(PHASE/'candidate-identities/revised-endpoint-frozen-candidate/candidate.json')
    assert att['active_benchmark_path_equivalent'] is True
    assert att['current_candidate']==frozen['candidate_identity_sha256']
    baseline=load((PHASE/att['historical_case']).resolve())
    core=['src/anysolver/'+s for s in ('corotational.py','elements.py','mesh_gen.py',
          'nonlinear_static.py','nonlinear_performance.py','_corotational_batch.py')]
    oracle=[(TASK/'diagnostics'/s).relative_to(REPO).as_posix()
            for s in ('arc_reference.py','assessment_support.py')]
    for row in (coarse,fine):
        expected=(frozen['working_source_and_selected_inputs_sha256'] if 'observer_identity' in row
                  else baseline['identity']['sha256'])
        for key in core+oracle:
            assert row['identity']['sha256'][key]==expected[key],key
        for key,value in row.get('observer_identity',{}).items():
            if key.startswith('src/anysolver/'):
                assert value==frozen['working_source_and_selected_inputs_sha256'][key],key
    for key in ('coupling','eccentricity','angle_degrees','ny','oracle','controls'):
        assert coarse[key]==fine[key],key
    assert coarse['kind']==fine['kind']=='analytical_arc'
    assert fine['nx']==2*coarse['nx']
    assert fine['connection_trace']=='linear default'
    assert coarse.get('connection_trace','linear default')=='linear default'
    changes={}; signed={}; decreasing={}
    for tip in ('shell','beam'):
        a,b=coarse['measured'][tip],fine['measured'][tip]
        changes[tip]=dict(u=math.dist(a['u_m'],b['u_m'])/math.sqrt(sum(x*x for x in b['u_m'])),
                          ry=abs(a['ry_rad']-b['ry_rad'])/abs(b['ry_rad']))
        signed[tip]=dict(coarse_ry=a['ry_rad']-fine['oracle']['phi'],
                         fine_ry=b['ry_rad']-fine['oracle']['phi'])
        decreasing[tip]={name:fine['errors'][tip][name]<coarse['errors'][tip][name]
                         for name in ('u_relative','ry_relative')}
    complete=(fine['status']=='completed' and abs(fine['load_factor']-1.)<=1e-12
              and fine['complete_and_equilibrated'] and fine['equilibrium']['passed']
              and fine['physical_root_My_balance_relative']<=1e-6)
    data=dict(kind='unchanged_default_refinement_pair',coarse=str(args.coarse),fine=str(args.fine),
        raw_source_hashes_equal=all(coarse['identity']['sha256'][k]==fine['identity']['sha256'][k] for k in core+oracle),
        root_active_path_equivalence=dict(path=str(attestation),sha256=hashlib.sha256(attestation.read_bytes()).hexdigest(),
             historical_and_current_fingerprints_validated=True,current_candidate=att['current_candidate']),
        levels=[coarse['nx'],fine['nx']],errors=dict(coarse=coarse['errors'],fine=fine['errors']),
        signed_rotation_errors=signed,refinement_changes=changes,error_decreases=decreasing,
        completed_and_independently_equilibrated=complete,
        accuracy_at_most_1_percent=all(fine['errors'][t][k]<=.01 for t in ('shell','beam') for k in ('u_relative','ry_relative')),
        last_refinement_at_most_0p25_percent=all(v<=.0025 for row in changes.values() for v in row.values()),
        conditional_next_refinement_eligible=bool(complete and all(v for row in decreasing.values() for v in row.values())),
        scope='Pair diagnostic only: not complete8/16/32coverage/all-family acceptance; raw identities preserved.')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps(data,indent=2,allow_nan=False),flush=True)


if __name__=='__main__': main()
