"""Standard-library immutable handoff; no solver/dependency imports or Git."""
from pathlib import Path
import hashlib,json,datetime
R=Path(__file__).resolve().parent;E=R.parent;REPO=E.parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name,data):
    p=R/name;assert not p.exists();p.write_text(json.dumps(data,indent=2)+'\n')
preserved={}
for name in ('raw-artifact-sha256.json','raw-artifact-sha256-v2.json'):
    data=json.loads((E/name).read_text())
    for path,row in data['artifacts'].items():assert sha(E/path)==row['sha256'],path
    preserved[name]=dict(count=len(data['artifacts']),sha256=sha(E/name),verified=True)
for sub,name in (('local-audit-v4','artifact-sha256.json'),('boundary-candidate-v5','artifact-sha256.json'),('j2-unblock-dev-v6','artifact-sha256-v6.json')):
    manifest=E/sub/name;data=json.loads(manifest.read_text())
    for path,row in data['artifacts'].items():assert sha(E/sub/path)==row['sha256'],path
    preserved[sub]=dict(count=len(data['artifacts']),sha256=sha(manifest),verified=True)
previous=json.loads((E/'owner-diagnosis-v3-handoff.json').read_text())
for path,row in previous['new_files'].items():assert sha(E/path)==row['sha256'],path
preserved['owner-diagnosis-v3-handoff.json']=dict(count=len(previous['new_files']),sha256=sha(E/'owner-diagnosis-v3-handoff.json'),verified=True)
artifact=json.loads((E/'artifact-binding-v1.json').read_text());assert sha(artifact['artifact'])==artifact['sha256']
for path,digest in artifact['source'].items():assert sha(E/'installed-wheel-v1'/path.replace('\\','/').removeprefix('src/'))==digest,path
preserved['old_wheel']=dict(sha256=artifact['sha256'],installed_source_count=len(artifact['source']),verified=True)
v6=json.loads((E/'j2-unblock-dev-v6/handoff-v6.json').read_text())
source={path:sha(REPO/path) for path in v6['source_sha256']}
assert source==v6['source_sha256'],'product changed during raw-only v7 discriminator'
strict=v6['unchanged_strict_test'];assert sha(REPO/strict['path'])==strict['sha256']
decision=E/'j2-unblock-dev-v6/independent-transition-decision-v1.md'
runtime=json.loads((R/'local-v1/runtime.json').read_text());execution=json.loads((R/'local-v1/execution.json').read_text())
assert runtime['affinity']==[0] and runtime['jit_disabled'] and all(p['num_threads']==1 for p in runtime['pools'])
assert execution['sampled_numeric_or_unresolved_max']==1 and execution['exit_code']==0
result=json.loads((R/'local-v1/result.json').read_text())
assert not result['supports_candidate'] and result['prefix_bytes_equal'] and result['controller_bytes_equal'] and result['origin_bytes_equal'] and result['generation']==3
process=json.loads((R/'owned-processes-terminal-v1.json').read_text());assert process['owned_processes_present']==0
counts=json.loads((R/'local-v1/counts.json').read_text())
totals={}
for row in counts:totals[row['method']]=totals.get(row['method'],0)+row['count']
handoff=dict(state='LOCAL_COMPOUND_DISCRIMINATOR_FAILED_NO_IMPLEMENTATION',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    baseline_root_provided='4219ad1f37ef8fd5a6174ea10ba0215940cd5e31',repository=str(REPO),product_changes=[],
    source_sha256_unchanged=source,unchanged_strict_test=strict,decision_sha256=sha(decision),
    result=result,execution=execution,complete_work_counts=counts,total_work=totals,
    source_ready=False,conditional_stages_not_run=['product implementation','focused checks','pending controller continuation','cohort','wheel'],
    reason='actual event switches branch, but full post-switch correction endpoint increases original-parent merit',
    actual_check='parent R/K bitwise revalidated; actual full/event/compound states/operators/branches recorded; one post-switch solve; accepted history/controller unchanged',
    primary_findings='owner-findings-v7.md',operators='local-v1/{parent,full,event,compound}.npz',callbacks='local-v1/{parent,full,event,compound}.json',
    correction='local-v1/post-switch-correction.npz',protected_preservation=preserved,
    owned_processes=process,numerical_lease='RELEASED',owned_handles=0,
    limits=['Negative bounded discriminator does not establish formulation/tangent/factorization failure',
        'No damping search, new event, subsequent correction or alternative candidate authorized/run',
        'Scientific full material target remains failed; root owns next decision'],
    no_git_mutations=True,no_sibling_contact=True,no_new_workers=True,no_protected_canary_access=True)
write('preservation-final-v7.json',preserved);write('handoff-v7.json',handoff)
files={}
for p in sorted(R.rglob('*')):
    if not p.is_file() or any(x in ('__pycache__','.pytest_cache') for x in p.parts) or p.name=='artifact-sha256-v7.json':continue
    files[p.relative_to(R).as_posix()]=dict(bytes=p.stat().st_size,sha256=sha(p))
write('artifact-sha256-v7.json',dict(root=str(R),artifacts=files,exclusions=['__pycache__','.pytest_cache','manifest itself']))
print(json.dumps(dict(state=handoff['state'],artifacts=len(files),manifest_sha256=sha(R/'artifact-sha256-v7.json'),
    handoff_sha256=sha(R/'handoff-v7.json'),preserved=preserved,total_work=totals,owned_handles=0)))
