"""Final standard-library source/evidence binding; no solver import or Git."""
from pathlib import Path
import hashlib,json,datetime
R=Path(__file__).resolve().parent;E=R.parent;REPO=E.parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,x):
    p=R/name;assert not p.exists(),p;p.write_text(json.dumps(x,indent=2)+'\n')
preserved={}
for name in ('raw-artifact-sha256.json','raw-artifact-sha256-v2.json'):
    m=json.loads((E/name).read_text())
    for path,row in m['artifacts'].items():assert sha(E/path)==row['sha256'],path
    preserved[name]=dict(count=len(m['artifacts']),sha256=sha(E/name),all_verified=True)
read=json.loads((E/'owner-diagnosis-v3-handoff.json').read_text())
for path,row in read['new_files'].items():assert sha(E/path)==row['sha256'],path
preserved['owner-diagnosis-v3-handoff.json']=dict(count=len(read['new_files']),sha256=sha(E/'owner-diagnosis-v3-handoff.json'),all_verified=True)
for folder in ('local-audit-v4','boundary-candidate-v5'):
    manifest=E/folder/'artifact-sha256.json';m=json.loads(manifest.read_text())
    for path,row in m['artifacts'].items():assert sha(E/folder/path)==row['sha256'],path
    preserved[folder]=dict(count=len(m['artifacts']),sha256=sha(manifest),all_verified=True)
artifact=json.loads((E/'artifact-binding-v1.json').read_text());assert sha(artifact['artifact'])==artifact['sha256']
for path,digest in artifact['source'].items():assert sha(E/'installed-wheel-v1'/path.replace('\\','/').removeprefix('src/'))==digest,path
preserved['frozen_wheel']=dict(sha256=artifact['sha256'],installed_source_count=len(artifact['source']),all_verified=True)
paths=('src/anysolver/_stiffened_shell_ge_finite_experimental.py','src/anysolver/_stiffened_shell_q4_algorithmic_pullback.py',
    'src/anysolver/_stiffened_shell_q4_material_event.py','tests/test_q4_native_material_event.py',
    'tests/test_native_fibre_boundary_proposal.py','docs/reference_cases/stiffened_shell_native_fibre_bl5_material.md')
source={p:sha(REPO/p) for p in paths}
strict='tests/test_stiffened_shell_native_fibre_bl5_material.py';strict_sha=sha(REPO/strict)
assert strict_sha=='da08cde385f96718b922378f8735adabe98e2c6c5eee4760caa8391712f2d279'
phases={p:json.loads((R/p/'execution.json').read_text()) for p in ('paired-v1','helpers-v1','helpers-v2','candidate-screen-v1')}
process=json.loads((R/'owned-processes-terminal-v1.json').read_text());assert process['owned_processes_present']==0
for phase in ('paired-v1','helpers-v1','helpers-v2','candidate-screen-v1'):
    assert phases[phase]['sampled_numeric_or_unresolved_max']==1
    runtime=json.loads((R/phase/'runtime.json').read_text());assert runtime['affinity']==[0] and runtime['jit_disabled']
    assert all(p['num_threads']==1 for p in runtime['pools'])
    assert {n:r['version'] for n,r in runtime['dependencies'].items()}==dict(numpy='2.5.3',scipy='1.18.1',numba='0.68.0',llvmlite='0.50.0')
paired=json.loads((R/'paired-v1/result.json').read_text());candidate=json.loads((R/'candidate-screen-v1/result.json').read_text())
assert candidate['A']['prefix_bytes_equal'] and candidate['A']['generation']==3 and not candidate['A']['accepted']
write('preservation-final-v6.json',preserved)
handoff=dict(state='FAILED_FULL_TARGET',implementation='partial experimental candidate; helper verified; full assigned lifecycle criteria unmet',
    utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),repository=str(REPO),source_sha256=source,
    unchanged_strict_test=dict(path=strict,sha256=strict_sha),
    checks=dict(paired_capture='completed; A terminal reject; B fine-two derivative pass adopted by root; coarse crossing preserved',
        helpers_v1=dict(failed=4,passed=20,disposition='preserved; tuple-unpack and represented-cutoff guard repairs'),
        helpers_v2=dict(passed=25,failed=0,pytest_seconds=2.55),
        candidate_screen='FAILED original remaining target1; all three attempts Newton24; no accepted commit'),
    executions=phases,paired_result='paired-v1/result.json',candidate_result='candidate-screen-v1/result.json',
    primary_findings='owner-findings-v6.md',derivative_attribution='saved-analysis-v1.json',
    q4_equation='q4-event-reading-v1.json',terminal_obstruction='candidate-obstruction-v1.json',
    failures=dict(full_target_unmet=True,original_two_strict_cases='historical v5 failures retained; tests not modified or rerun',
        standard_library_postprocess='initial missing elastic label index; analyze-before-elastic-label-repair.py preserved; no mechanics repeated'),
    counts=dict(paired_resume_assemblies=169,paired_resume_linear_solves=21,A_probe_assemblies=6,B_probe_assemblies=7,
        candidate_resume_assemblies=239,candidate_resume_linear_solves=72,candidate_resume_advances=164,
        callback_counts='exact separated counts.json per stage',internal_local_work='internal cell counters saved only for retained responses; complete discarded intermediate totals unavailable'),
    limitations=['Local predictor guard does not certify finite geometry crossing or global acceptance',
        'A finer directional norm miss remains unqualified and dominated by amplified tiny retained channels',
        'No new cohort/wheel/installed acceptance; old ca2503 source only',
        'No further mechanics or algorithm authority; root owns science/adoption/Git'],
    protected_preservation=preserved,numerical_lease='RELEASED',owned_processes_present=0,
    owned_sessions_terminal=[42195,19978],owned_pids=process['records'],
    scope=dict(git_mutations=False,sibling_contact=False,new_workers=False,protected_canary_access=False),
    independent_transition_decision='root-owned separate review; excluded from this manifest and bound separately by root')
write('handoff-v6.json',handoff)
files={}
for p in sorted(R.rglob('*')):
    if not p.is_file() or any(x in ('__pycache__','.pytest_cache') for x in p.parts):continue
    if p.name in ('artifact-sha256-v6.json','independent-transition-decision-v1.md'):continue
    files[p.relative_to(R).as_posix()]=dict(bytes=p.stat().st_size,sha256=sha(p))
write('artifact-sha256-v6.json',dict(root=str(R),artifacts=files,exclusions=['__pycache__','.pytest_cache','manifest itself','root-owned independent-transition-decision-v1.md']))
print(json.dumps(dict(state=handoff['state'],artifacts=len(files),manifest_sha256=sha(R/'artifact-sha256-v6.json'),
    handoff_sha256=sha(R/'handoff-v6.json'),preserved=preserved,source_sha256=source,owned_processes=0)))
