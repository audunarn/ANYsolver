"""Shared bounded beam gate runner; only explicitly registered gates execute."""
import argparse
import ast
from hashlib import sha256
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import threading
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import ge_beam3_g3b_environment as environment

SCOPE='GE_BEAM3_BOUNDED_REGISTERED_GATE_V2'
BASE='8767dbaaf4003daa24369628a1e6e119a642e0bf'
CONTRACT='docs/reference_cases/ge_beam3_g3c_b2_physical_contract_v1.json'
CONTRACT_SHA='6d202e2c25bc62c0987f090a7b5c092bc788318bbb37e27c1261e67af592996b'
DESIGN_REVIEW='docs/reference_cases/ge_beam3_g3c_b2_physical_contract_review_v1.json'
DESIGN_SHA='ba784eb40010a765fed25f891a0b0ccadf68c5beadabcf20b5161f2da5c204a4'
CAPSULE=Path('C:/Users/AudunArnesenNyhus/AppData/Local/ANYrelease/ge-beam3-g3b-rehearsal-history-20260912-0fe7f8f/capsule/environment.json')
CAPSULE_SHA='2ce154b866565e1d03019651b1ae7fdd070e5554f38d72adf21d8080558b6756'
JOB='docs/reference_cases/e4_pl_s3_v2_bounded_process.py'
JOB_SHA='c5b192c9c3f6ee2c68a42ab4a0cfbcdbe81581381b800c13aacce0bb219a3383'
TEST='tests/test_ge_beam3_g3c_b2_physical_core.py'
TESTS={'b2-core':(TEST,'numeric_core'),
       'b2-adapter':('tests/test_ge_beam3_g3c_b2_physical_adapter.py','adapter'),
       'q4-audit':('tests/test_ge_beam3_q4_recovery_coefficient_audit.py','q4_audit'),
       'q4-affine-exact':('tests/test_ge_beam3_q4_affine_recovery.py','q4_affine'),
       'q4-affine-numerical':('tests/test_ge_beam3_q4_affine_numerical_recovery.py','q4_affine_numerical')}
NUMERICAL_PLAN='docs/GE_BEAM3_Q4_AFFINE_NUMERICAL_RECOVERY_CONTRACT.md'
NUMERICAL_PLAN_SHA='21cec54b2469e291c8f90a2c042e3cf693a14f7bc10efd5111ea842ca65a218c'
NUMERICAL_REVIEW='docs/reference_cases/ge_beam3_q4_affine_numerical_design_review_v1.json'
NUMERICAL_REVIEW_SHA='e2a28209165d72046093ec08d06b8243399f820ab8db0b6fb7beeeab0e96055f'
NUMERICAL_TESTS=['test_affine_recovery_'+suffix for suffix in (
    'definition_and_source_identity','zero_and_station_constitutive','independent_material_fields',
    '64_stationarity_and_schur','actual_chart_work_hessian','directional_derivatives_all_steps',
    'six_rigid_modes_and_common_motion','d4_and_director_transports','passive_and_same_pose_rebase',
    'all_graph_q4_reference_variants','tiny_physical_energy_and_numerical_separation',
    'definition_observation_races','immutable_detached_results_and_reentry',
    'unsupported_routes_and_cancellation','actual_mutation_rejection')]
NUMERICAL_SMOKE='test_affine_recovery_smoke_square_station_work'
NUMERICAL_TABLES=[{'definitions':19,'source_graph':1,'extension_lemma':1,'fingerprint':1},
    {'station':54},{'independent':54},{'schur':54},{'work':54},{'directional':27},
    {'rigid':3,'common_motion':12},{'d4':24,'director':6},{'passive':3,'rebase':3},
    {'graph':20},{'tiny':6,'channels':54},{'races':12},{'immutability':8},{'rejections':19},{'mutations':39}]
NUMERICAL_SHAPES=('SQUARE','RECTANGLE','RHOMBUS')
NUMERICAL_BASE_IDS=[s+'::'+v for s in NUMERICAL_SHAPES for v in ('0.01','1','10')]
NUMERICAL_GRAPH_IDS=[g+'::'+v for g in ('J_Q4_PAIR','J_MULTIFAMILY_LOOP') for v in
    ('BASE','SHUFFLED_INSERTION','RENUMBERED','CONNECTIVITY_REVERSED','PROPER_GLOBAL_TRANSFORM')]
NUMERICAL_CONTEXT_IDS=[s+'::'+p for s in NUMERICAL_BASE_IDS for p in ('ZERO','MEMBRANE','BENDING','SHEAR','CHECKERBOARD','MIXED')]
NUMERICAL_TABLE_IDS=[
    {'definitions':NUMERICAL_BASE_IDS+NUMERICAL_GRAPH_IDS,'source_graph':['source_graph'],'extension_lemma':['ideal_recipe_extension'],'fingerprint':['typed_payload_encoding']},
    {'station':NUMERICAL_CONTEXT_IDS},{'independent':NUMERICAL_CONTEXT_IDS},{'schur':NUMERICAL_CONTEXT_IDS},{'work':NUMERICAL_CONTEXT_IDS},
    {'directional':[i+'::h='+h for i in NUMERICAL_BASE_IDS for h in ('0.0001','1e-05','1e-06')]},
    {'rigid':[s+'::1' for s in NUMERICAL_SHAPES],'common_motion':[s+'::1::motion='+str(i) for s in NUMERICAL_SHAPES for i in range(4)]},
    {'d4':[s+'::1::D4:'+str(i) for s in NUMERICAL_SHAPES for i in range(8)],
     'director':[s+'::1::DIRECTOR:'+str(i) for s in NUMERICAL_SHAPES for i in (-1,1)]},
    {'passive':[s+'::1::PASSIVE' for s in NUMERICAL_SHAPES],'rebase':[s+'::1' for s in NUMERICAL_SHAPES]},
    {'graph':[g+'::'+p for g in NUMERICAL_GRAPH_IDS for p in ('ZERO','MIXED')]},
    {'tiny':[s+'::1::amplitude='+a for s in NUMERICAL_SHAPES for a in ('1e-06','0.001')],'channels':NUMERICAL_CONTEXT_IDS},
    {'races':['descriptor','displacement_array','accepted_array','cancellation','material_descriptor','cache_array','cache_cancellation',
              'preentry_E','preentry_coordinates','preentry_material_direction','preentry_policy','preentry_cached_definition']},
    {'immutability':['all_detached_arrays','caller_arrays_preserved','same_input_repeat','reentry','changed_accepted_matrix','concurrent_evaluation','operator_cache_tamper','nested_candidate_bytes']},
    {'rejections':['nonaffine','director','material_direction','node_ids','generalized_section','history_section','offset','initial_fields','foreign_policy',
       'GE_BEAM3_G3C_MATRIX_POSE_SHELL_PULLBACK_V1','OLD_RETAINED_35_VARIABLE_SYSTEM','FOREIGN',
       'nonfinite_q','nonfinite_accepted','wrong_q_shape','wrong_rotation_shape','before_work','before_publication','invalid_callback']},
    {'mutations':[s+'::'+m for s in NUMERICAL_SHAPES for m in ('station_order','weight','frame','M','resultant','n','Dn','Hn',
       'force_weighted_Hessian','chart_second','coupling_sign','inverse','numerical_energy_leak')]}]
NUMERICAL_SOURCE_HASHES={
 'src/anysolver/e4_pl_element.py':'7fc46a18046e043512a5fb2c3f61ed0b95b834e4dde764f63c500a885e87ea38',
 'src/anysolver/elements.py':'f8c59792947a3c9b84416c61a4d9db98e42926d1bf21e74e736afbf6a9a88b37',
 'src/anysolver/_ge_beam3_g3c_local_shell.py':'69d9f27a96ed7e9a5959a42a081eeafbbe72021de6e4da1f91355c5fb3850f10',
 'src/anysolver/_ge_beam3_variational_shell.py':'b0db7a83633f4a835c06e940a6f0de36ab958f7e816c37a23c6ebc16259a2a60',
 'src/anysolver/_ge_beam3_mixed_ad.py':'b299ff765cd2eaae8b33a2ba1d05069f6fe8c39209e1eac75df356a2afb1fe36',
 'src/anysolver/_ge_beam3_pose_joint.py':'69cfb0a71761ab7cad0d62080d81511949e7c920f7f70162bcaba0497b402657',
 'src/anysolver/_ge_beam3_g3c_definition.py':'4b46b870fec010e3378df83c374d763f858d8f25820c14f9704dc6f0a656f0c2',
 'src/anysolver/_ge_beam3_g3c_owner.py':'18b9565d56192e23f192b1a3fbae3cb12ed7ede958c0e4b3e46279a799d1afc5',
 'docs/reference_cases/ge_beam3_g3c_fixtures_v1.json':'d5fecc80c3203ac7d191b4031d64bf35c56d2900066cb01fc1dfa4276d24c006'}
PHYSICAL_TABLES=frozenset(('work','common_motion','d4','director','passive','rebase','graph','tiny','smoke'))
PHYSICAL_SHAPES={'physical_energy':[],'physical_force':[24],'physical_hessian':[24,24],
    'source_physical_energy':[],'source_physical_force':[24],'source_physical_hessian':[24,24]}
OBSERVATION_MANIFEST='docs/reference_cases/ge_beam3_q4_affine_observation_manifest_v1.json'
OBSERVATION_MANIFEST_SHA='c844fcdf8ee83c6d5373d1eba5283b3ffc3db093703db8be9ebf557e529734c4'
AFFINE_TESTS=['test_affine_exact_arithmetic_and_schema','test_affine_source_and_representation_boundaries',
              'test_affine_square_chart_polynomial','test_affine_rectangle_chart_polynomial',
              'test_affine_rhombus_chart_polynomial','test_affine_stationary_schur_and_mutations']
AFFINE_FIXTURES=('AFFINE_Q4_SQUARE','AFFINE_Q4_RECTANGLE','AFFINE_Q4_RHOMBUS')
AFFINE_PLAN='docs/GE_BEAM3_Q4_AFFINE_CHART_RECOVERY_PLAN.md'
AFFINE_PLAN_SHA='42abd8f6cae8131be9bc62869329e1000244675f005b9bef9660a54e3e239fc0'
AFFINE_REVIEW='docs/reference_cases/ge_beam3_q4_affine_design_review_v1.json'
AFFINE_REVIEW_SHA='0d7e631ed3aad3630aa6bd296670735d93f24a4fa8160e4a17a4eed0164b66f5'
Q4_TESTS=['test_exact_field_laws_and_schema','test_registered_source_boundary',
          'test_square_coefficient_proof','test_rhombus_coefficient_proof','test_assembly_and_proof_mutations']
Q4_FIXTURES=('MO16_SQUARE_EXACT','MO16_AFFINE_RHOMBUS_EXACT')
Q4_PLAN_SHA='65f51816fe678acd38dffa9578f7cf2864d7cea518fc0e16e659899632cc3ce8'
ALLOWED={
    'scripts/run_ge_beam3_qualification.py','tests/test_ge_beam3_qualification_runner.py',
    'docs/GE_BEAM3_QUALIFICATION_COMPLETION_REGISTER.md',
    'src/anysolver/_ge_beam3_g3c_affine_q4_recovery.py',
    'src/anysolver/_ge_beam3_g3c_affine_q4_registry.py',
    'docs/reference_cases/ge_beam3_q4_affine_numerical_checker.py',
    'docs/reference_cases/ge_beam3_q4_affine_numerical_chart.py',
    'docs/GE_BEAM3_Q4_AFFINE_RECOVERY_EXTENSION_LEMMA.md',
    'docs/reference_cases/ge_beam3_q4_affine_extension_lemma_review_v1.json',
    OBSERVATION_MANIFEST,
    TESTS['q4-affine-numerical'][0],
}
INTEGRATION_REVIEW='docs/reference_cases/ge_beam3_8073635_integration_contract_review.json'
INTEGRATION_SHA='3be7021fd63a259cca5c48d0e6b47e6a261805f10b4909374f5a9610c17a7b59'
MEMORY=24*1024**3
THREADS=('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','BLIS_NUM_THREADS','NUMBA_NUM_THREADS','TBB_NUM_THREADS')

def canonical(v):
    return (json.dumps(v,sort_keys=True,separators=(',', ':'),allow_nan=False)+'\n').encode('ascii')

def write(path,value):
    with path.open('xb') as stream:stream.write(canonical(value))

def read(path):return environment.regular(path).read_bytes()
def fingerprint(raw):return dict(bytes=len(raw),sha256=sha256(raw).hexdigest())

def git(*args):
    return subprocess.check_output(['git','-c','safe.directory='+ROOT.as_posix(),
        '-c','core.autocrlf=true','-c','core.eol=crlf',*args],cwd=ROOT,
        env=environment.git_env(),timeout=30).decode().strip()

def inputs():
    names=git('ls-files','-z').split('\0')
    return {name:fingerprint(read(ROOT/name).replace(b'\r\n',b'\n')) for name in sorted(names) if name}

def inventory(lane,gate='b2-core'):
    if gate not in TESTS:raise ValueError('unregistered gate')
    test_path,inventory_key=TESTS[gate]
    contract=environment.strict(read(ROOT/CONTRACT).replace(b'\r\n',b'\n'))
    names=(NUMERICAL_TESTS if gate=='q4-affine-numerical' else AFFINE_TESTS if gate=='q4-affine-exact' else
           Q4_TESTS if gate=='q4-audit' else contract['test_nodes'][inventory_key])
    tree=ast.parse(read(ROOT/test_path))
    actual=[n.name for n in tree.body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
    if actual!=names+([NUMERICAL_SMOKE] if gate=='q4-affine-numerical' else []):raise ValueError('registered test inventory changed')
    if lane=='smoke':
        names=([names[0],NUMERICAL_SMOKE] if gate=='q4-affine-numerical' else
               [names[2],names[7]] if gate=='b2-core' else (names[:2] if gate in ('q4-audit','q4-affine-exact') else [names[0]]))
    elif lane!='core':raise ValueError('unregistered lane')
    return [test_path+'::'+name for name in names]

def verify_review(raw,digest,candidate,rows,gate='b2-core'):
    if sha256(raw).hexdigest()!=digest:raise ValueError('review hash')
    r=environment.strict(raw)
    if (set(r)!={'decision','findings','reviewer','scope','subject_commit'}
        or r['decision']!='ACCEPTED_GE_BEAM3_REGISTERED_GATE_FOR_BOUNDED_EXECUTION' or r['findings']
        or r['reviewer'].get('independent') is not True
        or r['subject_commit']!=candidate['commit']
        or r['scope']!={'scope_id':SCOPE,'gate':gate,'subject_tree':candidate['tree'],
                        'inputs_sha256':sha256(canonical(rows)).hexdigest(),
                        'contract_sha256':NUMERICAL_PLAN_SHA if gate=='q4-affine-numerical' else AFFINE_PLAN_SHA if gate=='q4-affine-exact' else
                                         Q4_PLAN_SHA if gate=='q4-audit' else CONTRACT_SHA}):
        raise ValueError('implementation review authority')
    return r

def authority(review_path,review_sha,gate='b2-core',*,observation_capture=None):
    if gate not in TESTS:raise ValueError('unregistered gate')
    if git('status','--porcelain','--untracked-files=all'):raise ValueError('dirty candidate')
    candidate=dict(commit=git('rev-parse','HEAD'),tree=git('rev-parse','HEAD^{tree}'))
    git('merge-base','--is-ancestor',BASE,'HEAD')
    changed=set(filter(None,git('diff','--name-only',BASE,'HEAD').splitlines()))
    if not changed<=ALLOWED:raise ValueError('production or unregistered extent changed')
    for path,digest in ((CONTRACT,CONTRACT_SHA),(DESIGN_REVIEW,DESIGN_SHA),(JOB,JOB_SHA),(INTEGRATION_REVIEW,INTEGRATION_SHA)):
        if sha256(read(ROOT/path).replace(b'\r\n',b'\n')).hexdigest()!=digest:raise ValueError('frozen authority input')
    contract=environment.strict(read(ROOT/CONTRACT).replace(b'\r\n',b'\n'))
    for key in ('source','proposal'):
        item=contract[key]
        if sha256(read(ROOT/item['path']).replace(b'\r\n',b'\n')).hexdigest()!=item['sha256']:raise ValueError('source equation changed')
    design=environment.strict(read(ROOT/INTEGRATION_REVIEW).replace(b'\r\n',b'\n'))
    for path,key in (('docs/GE_BEAM3_B2_PHYSICAL_ADAPTER_PLAN.md','b2_adapter_plan_sha256'),
                     ('docs/GE_BEAM3_Q4_RECOVERY_COEFFICIENT_AUDIT_PLAN.md','q4_audit_plan_sha256')):
        if sha256(read(ROOT/path).replace(b'\r\n',b'\n')).hexdigest()!=design['scope'][key]:raise ValueError('integration plan changed')
    if gate=='q4-affine-exact':
        for path,digest in ((AFFINE_PLAN,AFFINE_PLAN_SHA),(AFFINE_REVIEW,AFFINE_REVIEW_SHA)):
            if sha256(read(ROOT/path).replace(b'\r\n',b'\n')).hexdigest()!=digest:raise ValueError('affine design authority')
        affine=environment.strict(read(ROOT/AFFINE_REVIEW).replace(b'\r\n',b'\n'))
        if (set(affine)!={'decision','findings','reviewer','scope','subject_commit'}
            or affine['decision']!='ACCEPTED_GE_BEAM3_Q4_AFFINE_EXACT_GATE_DESIGN_ONLY' or affine['findings']
            or affine['reviewer'].get('independent') is not True
            or affine['scope'].get('gate')!='q4-affine-exact' or affine['scope'].get('plan_sha256')!=AFFINE_PLAN_SHA):
            raise ValueError('affine independent design acceptance')
    if gate=='q4-affine-numerical':
        for path,digest in ((NUMERICAL_PLAN,NUMERICAL_PLAN_SHA),(NUMERICAL_REVIEW,NUMERICAL_REVIEW_SHA),
            ('docs/GE_BEAM3_Q4_AFFINE_RECOVERY_EXTENSION_LEMMA.md','156d33ae5a621b953b5d04050218618f6416bac1042f94d3d3fc5c305c9f8762'),
            ('docs/reference_cases/ge_beam3_q4_affine_extension_lemma_review_v1.json','e28f184023ce1bba825a89079bcd2f9af99cf7861d701d7d918e2d30492b073e'),
            ('docs/reference_cases/ge_beam3_d49aacd_affine_evidence_review.json','a40277da9d95692e690f51e19dc069a7229455bcf76b84ea11f5f0dbd71dda7f'),
            ('docs/reference_cases/ge_beam3_d49aacd_affine_evidence_manifest.json','f5983d496cdac583c8ce4d13c49bcd882579aa0751864389bcc588d8b6e2e529')):
            if sha256(read(ROOT/path).replace(b'\r\n',b'\n')).hexdigest()!=digest:raise ValueError('numerical prerequisite authority')
        design=environment.strict(read(ROOT/NUMERICAL_REVIEW))
        if (set(design)!={'decision','findings','reviewer','scope','subject_commit'} or design['findings']
            or design['decision']!='ACCEPTED_GE_BEAM3_Q4_AFFINE_NUMERICAL_RECOVERY_DESIGN_ONLY'
            or design['reviewer'].get('independent') is not True
            or design['scope'].get('plan_sha256')!=NUMERICAL_PLAN_SHA
            or design['scope'].get('execution_authorized') is not False):raise ValueError('numerical design review')
        lemma=environment.strict(read(ROOT/'docs/reference_cases/ge_beam3_q4_affine_extension_lemma_review_v1.json'))
        if (lemma['decision']!='ACCEPTED_GE_BEAM3_Q4_AFFINE_EXTENSION_LEMMA' or lemma['findings']
            or lemma['reviewer'].get('independent') is not True
            or lemma['scope'].get('lemma_sha256')!='156d33ae5a621b953b5d04050218618f6416bac1042f94d3d3fc5c305c9f8762'):
            raise ValueError('extension lemma prerequisite review')
        observations=frozen_observations()
        if observation_capture is not None:observation_capture.update(observations)
    inventory('core',gate)
    rows=inputs();raw=read(review_path);verify_review(raw,review_sha,candidate,rows,gate)
    environment.verify(CAPSULE,CAPSULE_SHA)
    return candidate,rows,raw

def monitor(job,process,progress,clock=time.monotonic,sleep=time.sleep,start=None):
    """One terminal state; reserve 15 seconds inside the child limit to drain."""
    start=clock() if start is None else start;last=start;seen=None;peak=0
    while True:
        cpu,active,mem=job.accounting();now=clock();peak=max(peak,mem)
        current=(cpu,*progress())
        if current!=seen:seen=current;last=now
        if now-start>=585 or now-last>=120 or peak>MEMORY:
            drained=job.terminate()
            return dict(status='RESOURCE_BLOCKED',active_processes=job.accounting()[1],
                        peak_tree_bytes=peak,drained=bool(drained),elapsed_seconds=clock()-start)
        code=process.poll()
        if code is not None and active==0:
            return dict(status='PASSED' if code==0 else 'FAILED',active_processes=0,
                        peak_tree_bytes=peak,drained=True,elapsed_seconds=clock()-start)
        sleep(.1)

def validate_lease(lease,expected,review_sha,lane,out):
    candidate,rows,_=expected
    numeric=lease.get('gate')=='q4-affine-numerical'
    if (set(lease)!=({'schema','run_id','gate','lane','candidate','inputs','review_sha256','selected'}|
                    ({'observation_manifest_sha256'} if numeric else set()))
        or lease['schema']!=SCOPE or lease['gate'] not in TESTS or lease['lane']!=lane
        or lease['candidate']!=candidate or lease['inputs']!=rows
        or lease['review_sha256']!=review_sha or lease['selected']!=inventory(lane,lease['gate'])
        or str(uuid.UUID(lease['run_id']))!=lease['run_id']):raise ValueError('lease authority')
    if numeric and lease['observation_manifest_sha256']!=OBSERVATION_MANIFEST_SHA:raise ValueError('lease observation authority')

def claim_attempt(out,run_id):
    write(out/'worker-attempt.json',dict(run_id=run_id))

def q4_adjudication(records,lane):
    if lane=='smoke':return dict(terminal='NOT_ADJUDICATED_SMOKE_ONLY',recovery_qualified=False)
    fixtures=[row for row in records if row.get('test') in Q4_FIXTURES]
    if [row['test'] for row in fixtures]!=list(Q4_FIXTURES):raise ValueError('Q4 fixture inventory')
    witness=None
    for row in fixtures:
        proof=row['proof'];verification=row['verification']
        nonzero=[item for item in proof['coefficient_records'] if any(c!='0' for c in item['coefficient'])]
        first=nonzero[0] if nonzero else None
        if (len(proof['coefficient_records'])!=20150 or proof['coefficient_count']!=20150
            or proof['nonzero_count']!=len(nonzero) or proof['zero_count']!=20150-len(nonzero)
            or proof['first_nonzero']!=first or verification['first_nonzero']!=first
            or verification['nonzero_count']!=len(nonzero) or verification['independently_verified'] is not True
            or row['checker_replicas_byte_identical'] is not True):raise ValueError('Q4 adjudication authority')
        if witness is None and first is not None:witness=dict(fixture_id=row['test'],coefficient=first)
    return dict(terminal=('NO_GO_G3C_Q4_NATURAL_RETAINED_SPACE_FINITE_IDENTITY' if witness else
                         'UNCLASSIFIED_G3C_Q4_TWO_FIXTURE_COEFFICIENT_IDENTITIES'),
                first_nonzero=witness,coefficient_count=40300,recovery_qualified=False,
                universal_impossibility_claim=False)


def affine_adjudication(records,lane):
    if lane=='smoke':return dict(terminal='NOT_ADJUDICATED_SMOKE_ONLY',physical_recovery_qualified=False)
    rows=[row for row in records if row.get('test') in AFFINE_FIXTURES]
    if [row['test'] for row in rows]!=list(AFFINE_FIXTURES):raise ValueError('affine fixture inventory')
    first=None
    for row in rows:
        p,v=row['proof'],row['verification']
        nonzero=[r for r in p['coefficient_records'] if any(x!='0' for x in r['coefficient'])]
        witness=nonzero[0] if nonzero else None
        if (p['schema']!='GE_BEAM3_Q4_AFFINE_RECOVERY_EXACT_FIXTURE_V1'
            or p['fixture_id']!=row['test'] or len(p['coefficient_records'])!=7125 or p['coefficient_count']!=7125
            or p['degree_counts']!={'3':1140,'4':5985}
            or p['nonzero_count']!=len(nonzero) or p['zero_count']!=7125-len(nonzero)
            or p['first_nonzero']!=witness or v!={'fixture_id':row['test'],'coefficient_count':7125,
                'nonzero_count':len(nonzero),'first_nonzero':witness,'independently_verified':True,
                'physical_recovery_qualified':False,'full_g3c_qualified':False}
            or row['checker_replicas_byte_identical'] is not True
            or p['physical_recovery_qualified'] is not False or p['full_g3c_qualified'] is not False):
            raise ValueError('affine adjudication authority')
        if first is None and witness is not None:first=dict(fixture_id=row['test'],coefficient=witness)
    return dict(terminal='NO_GO_G3C_Q4_AFFINE_RECOVERY_VARIATIONAL_IDENTITY' if first else
                'UNCLASSIFIED_G3C_Q4_AFFINE_RECOVERY_EXACT_IDENTITIES_ONLY',first_nonzero=first,
                coefficient_count=21375,physical_recovery_qualified=False,full_g3c_qualified=False)

def job_type():
    spec=importlib.util.spec_from_file_location('beam_bounded_job',ROOT/JOB)
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
    return m._ProcessJob

def worker(out,lease_sha):
    raw=read(out/'lease.json')
    if sha256(raw).hexdigest()!=lease_sha:raise ValueError('lease hash')
    lease=environment.strict(raw)
    if lease['gate']=='q4-affine-numerical':raise ValueError('numerical gate requires one-node assignment')
    print('BEAM CHECKPOINT initialization',flush=True)
    expected=authority(out/'review.json',lease['review_sha256'],lease['gate'])
    validate_lease(lease,expected,lease['review_sha256'],lease['lane'],out)
    claim_attempt(out,lease['run_id'])
    if any(os.environ.get(key)!='1' for key in THREADS):raise ValueError('numerical thread environment')
    print('BEAM CHECKPOINT authority complete',flush=True)
    os.environ['BEAM_QUALIFICATION_OUTPUT']=str(out)
    sys.path[:0]=[str(ROOT/'src'),str(ROOT),str(CAPSULE.parent/'site')]
    import pytest
    class Recorder:
        def __init__(self):self.collected=[];self.passed=[];self.bad=[];self.module=None
        def pytest_collection_modifyitems(self,items):
            self.collected=[i.nodeid for i in items]
            if self.collected!=lease['selected']:raise ValueError('collected inventory differs')
            self.module=items[0].module
        def pytest_runtest_logstart(self,nodeid,location):print('BEAM CHECKPOINT test '+nodeid,flush=True)
        def pytest_runtest_logreport(self,report):
            if report.failed or report.skipped:self.bad.append(report.nodeid)
            if report.when=='call' and report.passed:self.passed.append(report.nodeid)
    recorder=Recorder()
    code=pytest.main(['-vv','-s','-p','no:cacheprovider','--basetemp',str(out/'pytest'),*lease['selected']],plugins=[recorder])
    if code!=0 or recorder.bad or recorder.passed!=lease['selected']:return 1
    records=recorder.module.SCIENTIFIC_RECORDS
    if not records:raise ValueError('missing numerical scientific records')
    if authority(out/'review.json',lease['review_sha256'],lease['gate'])!=expected:raise ValueError('final authority changed')
    scientific=dict(schema='GE_BEAM3_REGISTERED_GATE_SCIENCE_V2',gate=lease['gate'],lane=lease['lane'],
                    candidate=lease['candidate'],selected=lease['selected'],records=records,
                    full_g3c_qualified=False,production_qualified=False)
    if lease['gate']=='q4-audit':scientific['adjudication']=q4_adjudication(records,lease['lane'])
    if lease['gate']=='q4-affine-exact':scientific['adjudication']=affine_adjudication(records,lease['lane'])
    write(out/'scientific.pending.json',scientific)
    write(out/'completion.json',dict(selected=recorder.passed,scientific=fingerprint(read(out/'scientific.pending.json'))))
    print('BEAM CHECKPOINT evidence complete',flush=True)
    return 0


def q4_checker(out,fixture,replica,proof_sha,gate='q4-audit'):
    """Independent fresh checker process inside the parent Windows job tree."""
    if gate not in ('q4-audit','q4-affine-exact'):raise ValueError('checker gate')
    fixtures=AFFINE_FIXTURES if gate=='q4-affine-exact' else Q4_FIXTURES
    if fixture not in fixtures or replica not in ('1','2'):raise ValueError('checker identity')
    lease=environment.strict(read(out/'lease.json'))
    if lease['gate']!=gate or lease['lane']!='core':raise ValueError('checker gate authority')
    expected=authority(out/'review.json',lease['review_sha256'],gate)
    validate_lease(lease,expected,lease['review_sha256'],'core',out)
    if any(os.environ.get(key)!='1' for key in THREADS):raise ValueError('checker thread authority')
    directory=out/fixture
    write(directory/('checker'+replica+'.attempt.json'),dict(run_id=lease['run_id'],fixture=fixture,replica=replica))
    proof_raw=read(directory/'proof.json')
    if sha256(proof_raw).hexdigest()!=proof_sha:raise ValueError('checker proof hash')
    proof=environment.strict(proof_raw)
    if canonical(proof)!=proof_raw or proof.get('fixture_id')!=fixture:raise ValueError('canonical proof authority')
    sys.path.insert(0,str(ROOT/'docs/reference_cases'))
    if gate=='q4-affine-exact':
        from ge_beam3_q4_affine_recovery_checker import verify
    else:
        from ge_beam3_q4_recovery_coefficient_checker import verify
    result=verify(proof,lambda message:print('BEAM CHECKPOINT '+message,flush=True))
    if read(directory/'proof.json')!=proof_raw:raise ValueError('checker proof changed')
    if authority(out/'review.json',lease['review_sha256'],gate)!=expected:raise ValueError('checker final authority')
    schema='GE_BEAM3_Q4_AFFINE_CHECKER_RESULT_V1' if gate=='q4-affine-exact' else 'GE_BEAM3_Q4_CHECKER_RESULT_V1'
    write(directory/('checker'+replica+'.json'),dict(schema=schema,
        candidate=expected[0],inputs_sha256=sha256(canonical(expected[1])).hexdigest(),
        proof_sha256=proof_sha,verification=result))
    print('BEAM CHECKPOINT checker complete',flush=True)
    return 0

class WaveWatchdog:
    """Active coordinator deadline, including authority IO and finalization.

    Start drain with twenty seconds left; an independent hard timer exits even
    if draining or coordinator IO stalls. Windows job handles are kill-on-close.
    """
    def __init__(self,timer=threading.Timer,exit_process=os._exit):
        self.expired=threading.Event();self.job=None;self.jobs=[];self.exit_process=exit_process
        self.soft=timer(1780,self.expire);self.hard=timer(1800,self.hard_exit)
        for t in (self.hard,self.soft):t.daemon=True;t.start()

    def check(self):
        if self.expired.is_set():raise TimeoutError('whole invocation deadline')

    def attach(self,job):
        self.job=job
        self.jobs.append(job)
        self.check()

    def detach(self,job):
        self.jobs.remove(job)
        if self.job is job:self.job=None

    def expire(self):
        self.expired.set()
        try:
            for job in tuple(self.jobs):job.terminate()
        finally:self.exit_process(124)

    def hard_exit(self):
        self.expired.set()
        self.exit_process(124)

    def close(self):
        self.soft.cancel();self.hard.cancel()


def execute(args):
    watchdog=WaveWatchdog()
    try:return (execute_numerical(args,watchdog) if args.gate=='q4-affine-numerical' else execute_guarded(args,watchdog))
    finally:watchdog.close()


def numerical_assignment(lease,index):
    """No free-form module dispatch: each assignment is one registered node."""
    if lease['gate']!='q4-affine-numerical' or type(index)is not int or not 0<=index<len(lease['selected']):
        raise ValueError('numerical assignment index')
    sha_value(lease['observation_manifest_sha256'])
    return dict(schema='GE_BEAM3_REGISTERED_NODE_ASSIGNMENT_V1',run_id=lease['run_id'],
        index=index,node=lease['selected'][index],gate=lease['gate'],lane=lease['lane'],
        candidate=lease['candidate'],inputs_sha256=sha256(canonical(lease['inputs'])).hexdigest(),
        whole_inventory_sha256=sha256(canonical(lease['selected'])).hexdigest(),
        parent_lease_sha256=sha256(canonical(lease)).hexdigest(),observation_manifest_sha256=lease['observation_manifest_sha256'])


def validate_assignment(value,lease,index):
    if canonical(value)!=canonical(numerical_assignment(lease,index)):raise ValueError('node assignment authority')


def numerical_worker(out,index,assignment_sha):
    lease_raw=read(out/'lease.json');lease=environment.strict(lease_raw)
    if canonical(lease)!=lease_raw:raise ValueError('noncanonical parent lease')
    observations={}
    expected=authority(out/'review.json',lease['review_sha256'],'q4-affine-numerical',observation_capture=observations)
    validate_lease(lease,expected,lease['review_sha256'],lease['lane'],out)
    directory=out/('node-%02d'%index)
    raw=read(directory/'assignment.json')
    if sha256(raw).hexdigest()!=assignment_sha:raise ValueError('assignment hash')
    assignment=environment.strict(raw);validate_assignment(assignment,lease,index)
    claim_attempt(directory,lease['run_id'])
    if any(os.environ.get(k)!='1' for k in THREADS):raise ValueError('numerical threads')
    print('BEAM CHECKPOINT node initialization '+assignment['node'],flush=True)
    os.environ['BEAM_QUALIFICATION_OUTPUT']=str(directory)
    os.environ['BEAM_QUALIFICATION_NODE']=assignment['node']
    sys.path[:0]=[str(ROOT/'src'),str(ROOT),str(CAPSULE.parent/'site'),str(ROOT/'docs/reference_cases')]
    import pytest
    class Recorder:
        def __init__(self):self.passed=[];self.bad=[];self.module=None
        def pytest_collection_modifyitems(self,items):
            if [i.nodeid for i in items]!=[assignment['node']]:raise ValueError('single node collection')
            self.module=items[0].module
        def pytest_runtest_logreport(self,report):
            if report.failed or report.skipped:self.bad.append(report.nodeid)
            if report.when=='call' and report.passed:self.passed.append(report.nodeid)
    recorder=Recorder()
    code=pytest.main(['-vv','-s','-p','no:cacheprovider','--basetemp',str(directory/'pytest'),assignment['node']],plugins=[recorder])
    # Assertions, skips and unexpected exceptions are process/evidence failures,
    # not a typed scientific contradiction and never produce canonical evidence.
    if code!=0 or recorder.bad or recorder.passed!=[assignment['node']]:return 1
    records=recorder.module.SCIENTIFIC_RECORDS
    contradictions=recorder.module.CONTRADICTIONS
    if type(records)is not list or not records or type(contradictions)is not list:raise ValueError('node evidence missing')
    validate_numerical_tables(assignment['node'],records)
    validate_registered_observations(records)
    from ge_beam3_q4_affine_numerical_checker import verify_contradiction
    verified=[]
    for payload in contradictions:
        if (payload.get('candidate_identity')!=lease['candidate']['commit']
            or payload.get('source_identity')!=sha256(canonical(lease['inputs'])).hexdigest()):
            raise ValueError('contradiction source/candidate identity')
        verification=verify_contradiction(payload)
        if type(verification)is not dict or verification.get('accepted') is not True:raise ValueError('contradiction not independently accepted')
        verified.append(dict(payload=payload,verification=verification))
    validate_contradictions(assignment['node'],records,verified,lease,observations)
    if authority(out/'review.json',lease['review_sha256'],lease['gate'])!=expected:raise ValueError('node final authority')
    if read(directory/'assignment.json')!=raw or read(out/'lease.json')!=lease_raw:raise ValueError('node authority changed')
    result=dict(schema='GE_BEAM3_REGISTERED_NUMERICAL_NODE_V1',node=assignment['node'],index=index,
        candidate=lease['candidate'],inputs_sha256=assignment['inputs_sha256'],
        whole_inventory_sha256=assignment['whole_inventory_sha256'],lane=lease['lane'],
        observation_manifest_sha256=lease['observation_manifest_sha256'],
        records=records,contradictions=verified,status='CONTRADICTION' if verified else 'PASSED',
        physical_recovery_scope='REGISTERED_AFFINE_LOCAL_ONLY',full_g3c_qualified=False,production_qualified=False)
    write(directory/'scientific.pending.json',result)
    write(directory/'completion.json',dict(assignment_sha256=assignment_sha,node=assignment['node'],
        scientific=fingerprint(read(directory/'scientific.pending.json'))))
    print('BEAM CHECKPOINT node evidence complete',flush=True)
    return 0


def validate_numerical_result(raw,completion,lease,index,assignment_sha,observations):
    value=environment.strict(raw);assignment=numerical_assignment(lease,index)
    if canonical(value)!=raw:raise ValueError('noncanonical node science')
    if (set(value)!={'schema','node','index','candidate','inputs_sha256','whole_inventory_sha256','lane',
                    'records','contradictions','status','physical_recovery_scope','full_g3c_qualified','production_qualified','observation_manifest_sha256'}
        or value['schema']!='GE_BEAM3_REGISTERED_NUMERICAL_NODE_V1'
        or value['node']!=assignment['node'] or type(value['index'])is not int or value['index']!=index
        or value['candidate']!=lease['candidate'] or value['lane']!=lease['lane']
        or value['inputs_sha256']!=assignment['inputs_sha256']
        or value['whole_inventory_sha256']!=assignment['whole_inventory_sha256']
        or value['observation_manifest_sha256']!=lease['observation_manifest_sha256']
        or type(value['records'])is not list or not value['records']
        or type(value['contradictions'])is not list
        or value['status']!=('CONTRADICTION' if value['contradictions'] else 'PASSED')
        or value['physical_recovery_scope']!='REGISTERED_AFFINE_LOCAL_ONLY'
        or value['full_g3c_qualified'] is not False or value['production_qualified'] is not False
        or completion!={'assignment_sha256':assignment_sha,'node':assignment['node'],'scientific':fingerprint(raw)}):
        raise ValueError('numerical node evidence authority')
    validate_numerical_tables(value['node'],value['records'])
    validate_contradictions(value['node'],value['records'],value['contradictions'],lease,observations)
    return value


def registered_observation_state(table,row_id):
    """Fixture data only. Never construct a facade or evaluate any operator."""
    from anysolver import _ge_beam3_g3c_affine_q4_registry as registry
    c=registry.construction(row_construction(table,row_id))
    pose=row_id.rsplit('::',1)[1] if table in ('work','graph','smoke') else 'MIXED'
    amplitude=float(row_id.split('::amplitude=')[1]) if table=='tiny' else 1.
    q,accepted=registry.pose(c.construction_id,pose,amplitude)
    if table=='common_motion':q,accepted,_=registry.common_motion(q,accepted,c.coordinates,int(row_id.split('::motion=')[1]))
    if table=='rebase':q,accepted=registry.rebase(q,accepted)
    return dict(construction_id=c.construction_id,coordinates=c.coordinates.tolist(),q=q.tolist(),
        accepted=accepted.tolist(),normal=c.normal.tolist(),material_direction=c.material_direction.tolist(),
        director_polarity=c.director_polarity)


def observation_specs():
    result=[];path=TESTS['q4-affine-numerical'][0]
    for name,tables in zip(NUMERICAL_TESTS,NUMERICAL_TABLE_IDS):
        for table,ids in tables.items():
            if table in PHYSICAL_TABLES:
                result.extend(dict(node=path+'::'+name,table=table,row_id=identity) for identity in ids)
    result.extend(dict(node=path+'::'+NUMERICAL_SMOKE,table='smoke',row_id=identity)
                  for identity in ('SQUARE::1::ZERO','SQUARE::1::MIXED'))
    return result


def fixture_source_bindings():
    """Whole importable ANYsolver Python graph plus frozen fixture/environment."""
    paths={p.relative_to(ROOT).as_posix() for p in (ROOT/'src/anysolver').rglob('*.py')}
    paths.update(('docs/reference_cases/ge_beam3_g3c_fixtures_v1.json',
                  'scripts/ge_beam3_g3b_environment.py',JOB))
    return {path:fingerprint(read(ROOT/path).replace(b'\r\n',b'\n')) for path in sorted(paths)}


def fixture_generator_bindings():
    # Individual fixed functions avoid circularity with the later inserted
    # manifest hash. The accepted implementation review binds the whole runner.
    source=read(Path(__file__)).decode().replace('\r\n','\n');tree=ast.parse(source)
    names={'registered_observation_state','observation_specs','fixture_source_bindings',
           'fixture_generator_bindings','observation_authority','prepare_observation_manifest',
           'row_construction','canonical','fingerprint','read'}
    functions={n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    return {name:sha256(ast.get_source_segment(source,functions[name]).encode()).hexdigest() for name in sorted(names)}


def observation_authority():
    return dict(source_bindings=fixture_source_bindings(),generator_bindings=fixture_generator_bindings(),
        capsule_sha256=CAPSULE_SHA,inventory_sha256=sha256(canonical(observation_specs())).hexdigest())


def prepare_observation_manifest(output,expected_authority_sha256):
    """Reviewed prefreeze fixture-only command, enclosed in existing ProcessJob.

    This is not a scientific node, not a qualification result and not a retry.
    Imported fixture helpers use NumPy/rotation construction, but no facade or
    operator is called. The external caller must enforce the registered limits.
    """
    if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):raise ValueError('isolated fixture preparation required')
    if any(os.environ.get(k)!='1' for k in THREADS):raise ValueError('fixture thread envelope')
    output=Path(output)
    if not output.is_absolute() or output.exists():raise ValueError('exclusive external fixture output')
    expected=observation_authority()
    if sha256(canonical(expected)).hexdigest()!=expected_authority_sha256:raise ValueError('fixture preparation source authority')
    environment.verify(CAPSULE,CAPSULE_SHA)
    sys.path[:0]=[str(ROOT/'src'),str(CAPSULE.parent/'site')]
    rows=[]
    for spec in observation_specs():
        print('BEAM CHECKPOINT fixture '+spec['row_id'],flush=True)
        state=registered_observation_state(spec['table'],spec['row_id'])
        rows.append(dict(spec,state_sha256=sha256(canonical(state)).hexdigest()))
    environment.verify(CAPSULE,CAPSULE_SHA)
    if observation_authority()!=expected:raise ValueError('fixture preparation final authority changed')
    value=dict(schema='GE_BEAM3_REGISTERED_OBSERVATION_HASHES_V1',**expected,observations=rows,
        fixture_data_only=True,numerical_qualification=False)
    write(output,value)
    print('BEAM CHECKPOINT fixture manifest complete '+sha256(read(output)).hexdigest(),flush=True)


def frozen_observations():
    raw=read(ROOT/OBSERVATION_MANIFEST)
    if sha256(raw).hexdigest()!=OBSERVATION_MANIFEST_SHA:raise ValueError('frozen observation manifest hash')
    value=environment.strict(raw)
    if canonical(value)!=raw:raise ValueError('canonical observation manifest required')
    exact_keys(value,('schema','source_bindings','generator_bindings','capsule_sha256','inventory_sha256',
                      'observations','fixture_data_only','numerical_qualification'))
    expected=observation_authority()
    if (value['schema']!='GE_BEAM3_REGISTERED_OBSERVATION_HASHES_V1'
        or any(value[k]!=v for k,v in expected.items())
        or value['fixture_data_only'] is not True or value['numerical_qualification'] is not False):
        raise ValueError('frozen fixture graph authority')
    specs=observation_specs();rows=value['observations']
    if type(rows)is not list or len(rows)!=len(specs):raise ValueError('observation manifest inventory')
    result={}
    for row,spec in zip(rows,specs):
        exact_keys(row,('node','table','row_id','state_sha256'))
        if any(row[k]!=v for k,v in spec.items()):raise ValueError('observation manifest row identity')
        sha_value(row['state_sha256']);result[(row['node'],row['table'],row['row_id'])]=row['state_sha256']
    return result


def validate_registered_observations(records):
    """Authorized child only: shared fixture recipes, never checker mechanics."""
    for table,rows in records[0]['tables'].items():
        if table not in PHYSICAL_TABLES:continue
        for row in rows:
            state=observed_state(row,table);expected=registered_observation_state(table,row['id'])
            if canonical(state)!=canonical(expected):raise ValueError('observed state is not assigned registered fixture')


def validate_contradictions(node,records,contradictions,lease,observations):
    """Strict stdlib-only binding: one complete receipt per failed row predicate."""
    lookup={(table,row['id']):row for table,rows in records[0]['tables'].items() for row in rows}
    for table,rows in records[0]['tables'].items():
        if table not in PHYSICAL_TABLES:continue
        for row in rows:
            if observations.get((node,table,row['id']))!=row['state_sha256']:raise ValueError('state differs from frozen observation manifest')
    failed={(table,row['id'],predicate) for table,rows in records[0]['tables'].items() if table in PHYSICAL_TABLES
            for row in rows for predicate,check in row['physical_checks'].items() if not check['passed']}
    seen=set()
    for item in contradictions:
        exact_keys(item,('payload','verification'));payload=item['payload'];receipt=item['verification']
        exact_keys(payload,('schema','predicate','coordinates','q','accepted','normal','material_direction',
            'director_polarity','actual','tolerance','scale_mode','source_identity','candidate_identity',
            'fixture_identity','node','table','row_id','state_sha256'))
        exact_keys(receipt,('accepted','predicate','relative_error','node','table','row_id','fixture_identity',
            'payload_sha256','state_sha256','actual','expected'))
        table,row_id,predicate=payload['table'],payload['row_id'],payload['predicate']
        if any(type(v)is not str for v in (table,row_id,predicate)):raise ValueError('contradiction locator types')
        key=(table,row_id,predicate)
        if key not in failed or key in seen:raise ValueError('orphan or reused contradiction')
        row=lookup[(table,row_id)];state=observed_state(row,table);check=row['physical_checks'][predicate]
        if (payload['schema']!='Q4_AFFINE_NUMERICAL_CONTRADICTION_V1' or payload['node']!=node
            or type(payload['tolerance']) not in (int,float) or payload['tolerance']!=1e-11
            or payload['scale_mode']!='REFERENCE_EDGE_NONDIMENSIONAL_V1'
            or payload['source_identity']!=sha256(canonical(lease['inputs'])).hexdigest()
            or payload['candidate_identity']!=lease['candidate']['commit']
            or payload['fixture_identity']!=state['construction_id']):raise ValueError('contradiction assigned authority')
        supplied_state=dict(construction_id=payload['fixture_identity'],**{name:payload[name] for name in
            ('coordinates','q','accepted','normal','material_direction','director_polarity')})
        if canonical(supplied_state)!=canonical(state) or payload['state_sha256']!=row['state_sha256']:raise ValueError('contradiction observed state mismatch')
        actual=numeric_array(payload['actual'],PHYSICAL_SHAPES[predicate])
        if actual!=check['actual']:raise ValueError('contradiction differs from actual row observation')
        array_fingerprint(receipt['actual'],PHYSICAL_SHAPES[predicate]);array_fingerprint(receipt['expected'],PHYSICAL_SHAPES[predicate])
        for keyname in ('payload_sha256','state_sha256'):sha_value(receipt[keyname])
        if (receipt['accepted'] is not True or receipt['predicate']!=predicate or receipt['node']!=node
            or receipt['table']!=table or receipt['row_id']!=row_id or receipt['fixture_identity']!=state['construction_id']
            or receipt['payload_sha256']!=sha256(canonical(payload)).hexdigest()
            or receipt['state_sha256']!=row['state_sha256'] or receipt['actual']!=actual
            or finite_number(receipt['relative_error'])<=1e-11
            or receipt['relative_error']!=check['relative_error']):raise ValueError('independent contradiction receipt mismatch')
        seen.add(key)
    if seen!=failed:raise ValueError('failed physical checks missing verified contradiction')


def exact_keys(value,keys):
    if type(value)is not dict or set(value)!=set(keys):raise ValueError('closed numerical object schema')


def finite_number(value):
    if type(value) not in (float,int) or not math.isfinite(value):raise ValueError('finite numerical scalar required')
    return value


def sha_value(value):
    if type(value)is not str or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):raise ValueError('SHA256 encoding')


def residual(value,tolerance=1e-11):
    if not 0<=finite_number(value)<=tolerance:raise ValueError('residual outside registered threshold')


def numeric_array(value,shape):
    """Shape/finite validation and LE-binary64 digest without importing NumPy."""
    numbers=[]
    def visit(v,dimensions):
        if not dimensions:numbers.append(finite_number(v));return
        if type(v)is not list or len(v)!=dimensions[0]:raise ValueError('numerical array shape')
        for item in v:visit(item,dimensions[1:])
    visit(value,shape)
    return dict(shape=list(shape),sha256=sha256(b''.join(struct.pack('<d',v) for v in numbers)).hexdigest())


def array_fingerprint(value,shape):
    exact_keys(value,('shape','sha256'))
    if type(value['shape'])is not list or any(type(v)is not int for v in value['shape']) or value['shape']!=shape:raise ValueError('array digest shape')
    sha_value(value['sha256'])


def physical_check(value,predicate):
    exact_keys(value,('relative_error','passed','actual'))
    error=finite_number(value['relative_error'])
    if error<0 or type(value['passed'])is not bool or value['passed']!=(error<=1e-11):raise ValueError('physical predicate truth mismatch')
    array_fingerprint(value['actual'],PHYSICAL_SHAPES[predicate])


def row_construction(table,identity):
    if table in ('work','graph','smoke'):return identity.rsplit('::',1)[0]
    if table=='common_motion':return identity.split('::motion=')[0]
    if table=='tiny':return identity.split('::amplitude=')[0]
    return identity


def observed_state(row,table):
    state=row['state'];exact_keys(state,('construction_id','coordinates','q','accepted','normal','material_direction','director_polarity'))
    if state['construction_id']!=row_construction(table,row['id']):raise ValueError('row construction mismatch')
    for name,shape in (('coordinates',[4,3]),('q',[24]),('accepted',[4,3,3]),('normal',[3]),('material_direction',[3])):
        numeric_array(state[name],shape)
    if type(state['director_polarity'])is not int or state['director_polarity'] not in (-1,1):raise ValueError('director polarity type')
    if state['director_polarity']!=(-1 if state['construction_id'].endswith('::DIRECTOR:-1') else 1):raise ValueError('registered physical director polarity')
    sha_value(row['state_sha256'])
    if row['state_sha256']!=sha256(canonical(state)).hexdigest():raise ValueError('observed state hash mismatch')
    return state


def validate_numerical_row(table,row):
    if type(row)is not dict or type(row.get('id'))is not str:raise ValueError('numerical row identity schema')
    identity=row['id'];physical=table in PHYSICAL_TABLES
    base={'id','state','state_sha256','physical_checks'} if physical else {'id'}
    if table=='definitions':
        exact_keys(row,base|{'recipe_sha256','descriptor_sha256'})
        sha_value(row['recipe_sha256']);sha_value(row['descriptor_sha256'])
    elif table=='source_graph':
        exact_keys(row,base|{'hashes'})
        if row['hashes']!=NUMERICAL_SOURCE_HASHES:raise ValueError('source graph hashes')
    elif table=='extension_lemma':
        exact_keys(row,base|{'lemma_sha256','review_sha256'})
        if row['lemma_sha256']!='156d33ae5a621b953b5d04050218618f6416bac1042f94d3d3fc5c305c9f8762' or row['review_sha256']!='e28f184023ce1bba825a89079bcd2f9af99cf7861d701d7d918e2d30492b073e':raise ValueError('lemma evidence binding')
    elif table=='fingerprint':
        exact_keys(row,base|{'distinct_fingerprints','nonfinite_rejections','evidence_sha256','verified'})
        sha_value(row['evidence_sha256'])
        if row['verified'] is not True:raise ValueError('typed fingerprint evidence required')
        if type(row['distinct_fingerprints'])is not int or row['distinct_fingerprints']!=20:raise ValueError('typed fingerprint inventory')
        if type(row['nonfinite_rejections'])is not int or row['nonfinite_rejections']!=5:raise ValueError('nonfinite fingerprint inventory')
    elif table=='station':
        exact_keys(row,base|{'checks','energy','stations'});finite_number(row['energy'])
        if type(row['stations'])is not int or row['stations']!=4:raise ValueError('station count')
        exact_keys(row['checks'],('d','D','D2','R','Q','x'))
        for value in row['checks'].values():residual(value)
    elif table=='independent':
        exact_keys(row,base|{'stations'})
        if type(row['stations'])is not list or len(row['stations'])!=4:raise ValueError('independent station inventory')
        for item in row['stations']:
            exact_keys(item,('M','strain','resultant','frame','constitutive'))
            for value in item.values():residual(value)
    elif table=='schur':
        exact_keys(row,base|{'schur','full_internal_dimension'});array_fingerprint(row['schur'],[24,24])
        if type(row['full_internal_dimension'])is not int or row['full_internal_dimension']!=64:raise ValueError('full station dimension')
    elif table=='work':
        exact_keys(row,base|{'checks','chart_image_sentinels'})
        if type(row['chart_image_sentinels'])is not bool:raise ValueError('chart sentinel type')
    elif table=='directional':
        exact_keys(row,base|{'work','tangent'});residual(row['work'],1e-7);residual(row['tangent'],1e-7)
    elif table=='rigid':
        exact_keys(row,base|{'rigid_columns','total_positive_modes','eigenvalues'});array_fingerprint(row['eigenvalues'],[24])
        if type(row['rigid_columns'])is not int or row['rigid_columns']!=6 or type(row['total_positive_modes'])is not int or row['total_positive_modes']!=18:raise ValueError('rigid mode inventory')
    elif table in ('common_motion','passive','rebase','tiny'):
        exact_keys(row,base|{'energy','checks'});energy=finite_number(row['energy'])
        if table=='tiny' and energy<=0:raise ValueError('positive tiny physical energy required')
    elif table=='d4':
        exact_keys(row,base|{'station_map','checks'})
        k=int(identity.rsplit(':',1)[1]);corners=(0,1,2,3) if k<4 else (0,3,2,1)
        expected=[(i+k%4)%4 for i in corners]
        if type(row['station_map'])is not list or any(type(i)is not int for i in row['station_map']) or row['station_map']!=expected:raise ValueError('D4 station transport')
    elif table=='director':
        exact_keys(row,base|{'physical_polarity','checks'})
        if type(row['physical_polarity'])is not int or row['physical_polarity']!=int(identity.rsplit(':',1)[1]):raise ValueError('physical polarity authority')
    elif table=='graph':
        exact_keys(row,base|{'node_ids','element_id','recipe_sha256','checks'});sha_value(row['recipe_sha256'])
        ids=[101,102,103,104] if identity.startswith('J_Q4_PAIR::') else [301,302,303,304]
        element=11 if identity.startswith('J_Q4_PAIR::') else 13
        if '::RENUMBERED::' in identity:ids=[10000+7*i for i in ids];element=20000+5*element
        if '::CONNECTIVITY_REVERSED::' in identity:ids=[ids[i] for i in (0,3,2,1)]
        if type(row['node_ids'])is not list or any(type(i)is not int for i in row['node_ids']) or row['node_ids']!=ids or type(row['element_id'])is not int or row['element_id']!=element:raise ValueError('graph source identities')
    elif table=='channels':
        exact_keys(row,base|{'physical','numerical'});finite_number(row['physical'])
        if type(row['numerical'])is not list or len(row['numerical'])!=2:raise ValueError('numerical energy channel inventory')
        for item,name in zip(row['numerical'],('NUMERICAL_PL','NUMERICAL_HOURGLASS')):
            exact_keys(item,('name','energy'))
            if item['name']!=name:raise ValueError('numerical channel identity')
            finite_number(item['energy'])
    elif table=='races':
        exact_keys(row,base|{'rejected_before_family'})
        if row['rejected_before_family'] is not True:raise ValueError('state safety rejection required')
    elif table=='immutability':
        extra={'array_count'} if identity=='all_detached_arrays' else {'rejections'} if identity=='reentry' else {'fingerprint_sha256'} if identity=='nested_candidate_bytes' else set()
        exact_keys(row,base|{'verified','prior_arrays_sha256'}|extra);sha_value(row['prior_arrays_sha256'])
        if row['verified'] is not True:raise ValueError('immutable output evidence required')
        if identity=='all_detached_arrays' and (type(row['array_count'])is not int or row['array_count']<=30):raise ValueError('detached array inventory')
        if identity=='reentry' and (type(row['rejections'])is not int or row['rejections']!=2):raise ValueError('reentry checks')
        if identity=='nested_candidate_bytes':sha_value(row['fingerprint_sha256'])
    elif table=='rejections':
        if identity in ('before_work','before_publication','invalid_callback'):
            exact_keys(row,base|{'callbacks','family_entries','published'})
            callbacks,entries=(2,1) if identity=='before_publication' else (1,0)
            if type(row['callbacks'])is not int or row['callbacks']!=callbacks or type(row['family_entries'])is not int or row['family_entries']!=entries or row['published'] is not False:raise ValueError('cancellation receipt')
        else:
            exact_keys(row,base|{'rejected_before_family'})
            if row['rejected_before_family'] is not True:raise ValueError('admission rejection receipt')
    elif table=='mutations':
        exact_keys(row,base|{'rejection'});mutation=identity.split('::',1)[1]
        enum=('INDEPENDENT_HESSIAN' if mutation in ('force_weighted_Hessian','chart_second') else
              'STATION_EQUILIBRIUM' if mutation=='coupling_sign' else 'STATION_INVERSE' if mutation=='inverse' else
              'MATERIAL_ENERGY' if mutation=='numerical_energy_leak' else 'INDEPENDENT_STATION_COMPARISON')
        if row['rejection']!=enum:raise ValueError('mutation rejection mechanism')
    elif table=='smoke':exact_keys(row,base|{'checks'})
    else:raise ValueError('unregistered numerical table')
    if physical:
        observed_state(row,table)
        mapping={'energy':'physical_energy','force':'physical_force','hessian':'physical_hessian'}
        if table=='work' and not identity.endswith('::ZERO'):
            mapping.update(source_energy='source_physical_energy',source_force='source_physical_force',source_hessian='source_physical_hessian')
        exact_keys(row['physical_checks'],mapping.values())
        exact_keys(row['checks'],set(mapping)|{'symmetry','spatial_force','spatial_tangent'})
        for key,predicate in mapping.items():
            physical_check(row['physical_checks'][predicate],predicate)
            if row['checks'][key]!=row['physical_checks'][predicate]:raise ValueError('physical check row mismatch')
        for key in ('symmetry','spatial_force','spatial_tangent'):residual(row['checks'][key])
        if table=='work':
            source_failed=any(not value['passed'] for key,value in row['physical_checks'].items() if key.startswith('source_'))
            if row['chart_image_sentinels'] is source_failed:raise ValueError('chart image sentinel disposition')


def validate_numerical_tables(node,records):
    name=node.split('::')[-1]
    tables=({'smoke':2} if name==NUMERICAL_SMOKE else NUMERICAL_TABLES[NUMERICAL_TESTS.index(name)])
    identities=({'smoke':['SQUARE::1::ZERO','SQUARE::1::MIXED']} if name==NUMERICAL_SMOKE else NUMERICAL_TABLE_IDS[NUMERICAL_TESTS.index(name)])
    if len(records)!=1:raise ValueError('one complete named-node record required')
    record=records[0]
    if (type(record)is not dict or set(record)!={'test','tables','full_g3c_qualified','production_qualified'}
        or record['test']!=name.removeprefix('test_affine_recovery_')
        or record['full_g3c_qualified'] is not False or record['production_qualified'] is not False
        or type(record['tables'])is not dict or set(record['tables'])!=set(tables)):
        raise ValueError('numerical named table schema')
    for key,count in tables.items():
        rows=record['tables'][key]
        if (type(rows)is not list or len(rows)!=count or any(type(row)is not dict or type(row.get('id'))is not str or not row['id'] for row in rows)
            or [row['id'] for row in rows]!=identities[key]):raise ValueError('numerical table coverage')
        for row in rows:validate_numerical_row(key,row)


def numerical_union(lease,nodes,observations):
    if len(nodes)!=len(lease['selected']) or [n['node'] for n in nodes]!=lease['selected']:
        raise ValueError('incomplete or reordered numerical union')
    if [n['index'] for n in nodes]!=list(range(len(nodes))):raise ValueError('duplicated numerical nodes')
    for node in nodes:
        validate_numerical_tables(node['node'],node['records'])
        validate_contradictions(node['node'],node['records'],node['contradictions'],lease,observations)
        if node['status']!=('CONTRADICTION' if node['contradictions'] else 'PASSED'):raise ValueError('node contradiction disposition')
    contradictions=[dict(node=n['node'],evidence=c) for n in nodes for c in n['contradictions']]
    terminal=('NOT_ADJUDICATED_SMOKE_ONLY' if lease['lane']=='smoke' else
        'NO_GO_G3C_Q4_AFFINE_RECOVERY_VARIATIONAL_OR_STATE' if contradictions else
        'PROVISIONAL_GO_G3C_Q4_AFFINE_LOCAL_PHYSICAL_RECOVERY_ONLY')
    return dict(schema='GE_BEAM3_REGISTERED_NUMERICAL_UNION_V1',gate=lease['gate'],lane=lease['lane'],
        candidate=lease['candidate'],inputs_sha256=sha256(canonical(lease['inputs'])).hexdigest(),
        observation_manifest_sha256=lease['observation_manifest_sha256'],
        selected=lease['selected'],nodes=nodes,terminal=terminal,contradictions=contradictions,
        physical_recovery_qualified=lease['lane']=='core' and not contradictions,
        full_g3c_qualified=False,production_qualified=False)


def monitor_batch(entries,watchdog,clock=time.monotonic,sleep=time.sleep):
    """Independent tree accounting prevents a busy sibling masking inactivity."""
    if not 1<=len(entries)<=3:raise ValueError('numerical batch worker count')
    for e in entries:e.update(last=e['start'],seen=None,peak=0,record=None)
    while any(e['record'] is None for e in entries):
        watchdog.check()
        for e in entries:
            if e['record'] is not None:continue
            cpu,active,mem=e['job'].accounting();now=clock();e['peak']=max(e['peak'],mem)
            progress=(cpu,*e['progress']())
            if progress!=e['seen']:e['seen']=progress;e['last']=now
            reason=('wall' if now-e['start']>=585 else 'inactivity' if now-e['last']>=120 else
                    'memory' if mem>MEMORY else None)
            code=e['process'].poll()
            if reason:
                e['record']=dict(status='RESOURCE_BLOCKED',reason=reason,drained=False)
            elif code is not None and active==0:
                e['record']=dict(status='PASSED' if code==0 else 'FAILED',drained=True)
            if e['record'] is not None:
                e['record'].update(returncode=e['process'].poll(),active_processes=e['job'].accounting()[1],
                    peak_tree_bytes=e['peak'],elapsed_seconds=clock()-e['start'])
                if e['record']['active_processes'] and not reason:e['record']['status']='FAILED_TO_DRAIN'
        if any(e['record'] and e['record']['status']!='PASSED' for e in entries):
            # Drain the three independent jobs concurrently, not three successive
            # fifteen-second drains that could exceed a sibling's 600s ceiling.
            drains=[]
            for e in entries:
                if e['job'].accounting()[1]:
                    def drain(entry=e):
                        try:entry['drained']=bool(entry['job'].terminate())
                        except BaseException:entry['drained']=False
                    thread=threading.Thread(target=drain,daemon=True);drains.append((e,thread));thread.start()
            drain_deadline=time.monotonic()+15
            for e,thread in drains:thread.join(max(0,drain_deadline-time.monotonic()))
            for e in entries:
                if e['record'] is None:e['record']=dict(status='ABORTED_PEER_FAILURE')
                e['record'].update(drained=e.get('drained',e['job'].accounting()[1]==0),
                    active_processes=e['job'].accounting()[1],returncode=e['process'].poll(),
                    peak_tree_bytes=e['peak'],elapsed_seconds=clock()-e['start'])
                if e['record']['active_processes']:e['record']['status']='FAILED_TO_DRAIN'
            return
        if any(e['record'] is None for e in entries):sleep(.1)


def execute_numerical(args,watchdog):
    observations={}
    expected=authority(args.review,args.review_sha256,args.gate,observation_capture=observations);watchdog.check()
    out=Path(tempfile.mkdtemp(prefix='anysolver-beam-qualification-'))
    print('DIAGNOSTICS '+str(out),flush=True)
    lease=dict(schema=SCOPE,run_id=str(uuid.uuid4()),gate=args.gate,lane=args.lane,candidate=expected[0],
        inputs=expected[1],review_sha256=args.review_sha256,selected=inventory(args.lane,args.gate),
        observation_manifest_sha256=OBSERVATION_MANIFEST_SHA)
    write(out/'lease.json',lease)
    with (out/'review.json').open('xb') as stream:stream.write(expected[2])
    env=dict(os.environ,**{key:'1' for key in THREADS})
    env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTEST_ADDOPTS='',PYTHONDONTWRITEBYTECODE='1')
    nodes=[];process_records=[];failed=False;start=time.monotonic()
    try:
        for offset in range(0,len(lease['selected']),3):
            entries=[]
            try:
                for index in range(offset,min(offset+3,len(lease['selected']))):
                    watchdog.check();directory=out/('node-%02d'%index);directory.mkdir(exist_ok=False)
                    assignment=numerical_assignment(lease,index);write(directory/'assignment.json',assignment)
                    digest=sha256(read(directory/'assignment.json')).hexdigest()
                    job=job_type()(MEMORY);watchdog.attach(job)
                    entry=dict(index=index,job=job,record=None,directory=directory,assignment_sha=digest,streams=[])
                    entries.append(entry)
                    stdout=(directory/'stdout.log').open('xb');entry['streams'].append(stdout)
                    stderr=(directory/'stderr.log').open('xb');entry['streams'].append(stderr)
                    entry['start']=time.monotonic()
                    entry['process']=job.launch([sys.executable,'-I','-S','-B','-u',str(Path(__file__).resolve()),
                        '--numerical-node',str(out),str(index),digest],cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
                    entry['progress']=lambda d=directory:((d/'stdout.log').stat().st_size,(d/'stderr.log').stat().st_size)
                monitor_batch(entries,watchdog)
            finally:
                for e in entries:
                    try:
                        if e['job'].accounting()[1] and e.get('record') is None:e['job'].terminate()
                        active=e['job'].accounting()[1]
                        record=e.get('record') or dict(status='FAILED',drained=active==0)
                        record.update(index=e['index'],node=lease['selected'][e['index']],active_processes=active)
                        if active:record['status']='FAILED_TO_DRAIN'
                        for stream in e['streams']:stream.close()
                        write(e['directory']/'process.json',record);process_records.append(record)
                    finally:
                        e['job'].close();watchdog.detach(e['job'])
            if any(r['status']!='PASSED' or r['active_processes'] for r in process_records):failed=True;break
            for e in entries:
                pending=read(e['directory']/'scientific.pending.json')
                completion=environment.strict(read(e['directory']/'completion.json'))
                nodes.append(validate_numerical_result(pending,completion,lease,e['index'],e['assignment_sha'],observations))
        if not failed:
            if authority(args.review,args.review_sha256,args.gate)!=expected:raise ValueError('numerical union final authority')
            watchdog.check();science=numerical_union(lease,nodes,observations)
            write(out/'scientific.pending.json',science)
    except BaseException:
        failed=True
        raise
    finally:
        write(out/'process.json',dict(status='BLOCKED' if failed else 'PASSED',run_id=lease['run_id'],
            completed_nodes=process_records,launched_nodes=len(process_records),required_nodes=len(lease['selected']),
            elapsed_seconds=time.monotonic()-start,
            terminal='BLOCKED_G3C_Q4_AFFINE_RECOVERY_PROCESS_OR_EVIDENCE' if failed else 'COMPLETE_PROCESS_INVENTORY'))
    if not failed:
        watchdog.check()
        if (out/'scientific.json').exists():raise ValueError('exclusive numerical union')
        os.rename(out/'scientific.pending.json',out/'scientific.json')
    return int(failed)


def execute_guarded(args,watchdog):
    wave_start=time.monotonic()
    expected=authority(args.review,args.review_sha256,args.gate)
    watchdog.check()
    out=Path(tempfile.mkdtemp(prefix='anysolver-beam-qualification-'))
    print('DIAGNOSTICS '+str(out),flush=True)
    lease=dict(schema=SCOPE,run_id=str(uuid.uuid4()),gate=args.gate,lane=args.lane,
               candidate=expected[0],inputs=expected[1],review_sha256=args.review_sha256,selected=inventory(args.lane,args.gate))
    write(out/'lease.json',lease)
    with (out/'review.json').open('xb') as stream:stream.write(expected[2])
    job=job_type()(MEMORY);record=dict(status='FAILED');process=None
    try:
        watchdog.attach(job)
        env=dict(os.environ,**{key:'1' for key in THREADS})
        env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTEST_ADDOPTS='',PYTHONDONTWRITEBYTECODE='1')
        with (out/'stdout.log').open('xb') as stdout,(out/'stderr.log').open('xb') as stderr:
            child_start=time.monotonic()
            watchdog.check()
            process=job.launch([sys.executable,'-I','-S','-B','-u',str(Path(__file__).resolve()),'--worker',str(out),
                sha256(read(out/'lease.json')).hexdigest()],cwd=ROOT,env=env,stdout=stdout,stderr=stderr)
            record=monitor(job,process,lambda:((out/'stdout.log').stat().st_size,(out/'stderr.log').stat().st_size),start=child_start)
        if record['status']=='PASSED':
            completion=environment.strict(read(out/'completion.json'))
            pending=read(out/'scientific.pending.json');science=environment.strict(pending)
            if (completion!={'selected':lease['selected'],'scientific':fingerprint(pending)}
                or set(science)!=({'schema','gate','lane','candidate','selected','records','full_g3c_qualified','production_qualified'}
                                  | ({'adjudication'} if lease['gate'] in ('q4-audit','q4-affine-exact') else set()))
                or science['schema']!='GE_BEAM3_REGISTERED_GATE_SCIENCE_V2' or science['gate']!=lease['gate']
                or science['lane']!=lease['lane'] or type(science['records']) is not list or not science['records']
                or science['candidate']!=lease['candidate'] or science['selected']!=lease['selected']
                or science['full_g3c_qualified'] or science['production_qualified']):raise ValueError('completion mismatch')
            if lease['gate']=='q4-audit' and canonical(science['adjudication'])!=canonical(q4_adjudication(science['records'],lease['lane'])):
                raise ValueError('Q4 terminal mismatch')
            if lease['gate']=='q4-affine-exact' and canonical(science['adjudication'])!=canonical(affine_adjudication(science['records'],lease['lane'])):
                raise ValueError('affine terminal mismatch')
            if authority(args.review,args.review_sha256,args.gate)!=expected:raise ValueError('coordinator final authority')
            if time.monotonic()-wave_start>=1800:raise ValueError('wave deadline')
    except BaseException as exc:
        record.update(status='FAILED',exception=type(exc).__name__)
        raise
    finally:
        try:
            if job.accounting()[1]:
                # monitor already consumed its drain reserve on resource failure.
                if record.get('status')!='RESOURCE_BLOCKED':job.terminate()
            record['active_processes']=job.accounting()[1]
            if record['active_processes']:record['status']='FAILED_TO_DRAIN'
        finally:job.close()
        record.update(scope=SCOPE,run_id=lease['run_id'],returncode=process.poll() if process else None,
                      wave_elapsed_seconds=time.monotonic()-wave_start,
                      files={p.name:fingerprint(p.read_bytes()) for p in out.iterdir() if p.is_file()})
        write(out/'process.json',record)
        print(canonical(record).decode(),flush=True)
    if record['status']=='PASSED':
        watchdog.check()
        if (out/'scientific.json').exists():raise ValueError('exclusive publication')
        os.rename(out/'scientific.pending.json',out/'scientific.json')
    return int(record['status']!='PASSED')

def main():
    if not (sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode):raise ValueError('use -I -S -B')
    if len(sys.argv)==4 and sys.argv[1]=='--worker':return worker(Path(sys.argv[2]),sys.argv[3])
    if len(sys.argv)==5 and sys.argv[1]=='--numerical-node':return numerical_worker(Path(sys.argv[2]),int(sys.argv[3]),sys.argv[4])
    if len(sys.argv)==6 and sys.argv[1]=='--q4-checker':
        return q4_checker(Path(sys.argv[2]),sys.argv[3],sys.argv[4],sys.argv[5])
    if len(sys.argv)==6 and sys.argv[1]=='--q4-affine-checker':
        return q4_checker(Path(sys.argv[2]),sys.argv[3],sys.argv[4],sys.argv[5],'q4-affine-exact')
    if os.name!='nt':raise ValueError('Windows process-tree execution required')
    parser=argparse.ArgumentParser()
    parser.add_argument('--gate',choices=list(TESTS),required=True)
    parser.add_argument('--lane',choices=['smoke','core'],required=True)
    parser.add_argument('--review',type=Path,required=True)
    parser.add_argument('--review-sha256',required=True)
    return execute(parser.parse_args())

if __name__=='__main__':raise SystemExit(main())
