from pathlib import Path
import datetime, hashlib, json

ROOT=Path(__file__).resolve().parent;EVIDENCE=ROOT.parent;REPO=EVIDENCE.parents[2]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
preserved={}
for name in ('raw-artifact-sha256.json','raw-artifact-sha256-v2.json'):
    data=read(EVIDENCE/name)
    for path,row in data['artifacts'].items():assert sha(EVIDENCE/path)==row['sha256'],path
    preserved[name]=dict(count=len(data['artifacts']),sha256=sha(EVIDENCE/name))
diagnosis=read(EVIDENCE/'owner-diagnosis-v3-handoff.json')
for name,row in diagnosis['new_files'].items():assert sha(EVIDENCE/name)==row['sha256'],name
local=read(EVIDENCE/'local-audit-v4/artifact-sha256.json')
for name,row in local['artifacts'].items():assert sha(EVIDENCE/'local-audit-v4'/name)==row['sha256'],name
artifact=read(EVIDENCE/'artifact-binding-v1.json')
assert sha(artifact['artifact'])==artifact['sha256']=='ca2503e2178aa536b79d556a2c105faef29977f6d7a1442e989bddde077cd849'
for name,digest in artifact['source'].items():assert sha(EVIDENCE/'installed-wheel-v1'/name.replace('\\','/').removeprefix('src/'))==digest,name
phases=('helpers-v1','helpers-v2','screen-v1','screen-v2','cohort-v1','helpers-v3')
runs={}
for phase in phases:
    binding=read(ROOT/('binding-'+phase+'.json'))
    for name,digest in binding['source'].items():assert sha(ROOT/('executed-'+phase)/name)==digest,name
    for name,digest in binding['tools'].items():assert sha(ROOT/('executed-'+phase)/name)==digest,name
    execution=read(ROOT/phase/'execution.json')
    runtime=read(ROOT/phase/'runtime.json')
    assert execution['status'] in ('completed','failed')
    assert all(Path(p).resolve().is_relative_to((REPO/'src').resolve()) for p in runtime['imports'].values())
    assert runtime['jit_disabled'] and len(runtime['affinity'])==1
    assert all(p['num_threads']==1 for p in runtime['pools'])
    runs[phase]=dict(execution=execution,result=read(ROOT/phase/'result.json'),
        binding_sha256=sha(ROOT/('binding-'+phase+'.json')),runtime_sha256=sha(ROOT/phase/'runtime.json'),
        solver_imports=len(runtime['imports']))
unchanged=('tests/test_stiffened_shell_native_fibre_bl5_material.py',
           'examples/stiffened_shell_native_fibre_bl5_material.py','examples/stiffened_shell_native_fibre_bl5.py',
           'src/anysolver/stiffened_shell.py','src/anysolver/_stiffened_shell_ge_point_buckling.py')
baseline=read(ROOT/'binding-helpers-v1.json')['source']
for name in unchanged:assert sha(REPO/name)==baseline[name],name
changed=('src/anysolver/_stiffened_shell_ge_finite_experimental.py','src/anysolver/_ge_beam3_fibre_cell.py',
         'src/anysolver/_ge_beam3_retained_fibre.py','src/anysolver/_stiffened_shell_ge_experimental.py',
         'tests/test_native_fibre_boundary_proposal.py','docs/reference_cases/stiffened_shell_native_fibre_bl5_material.md')
final_source={name:sha(REPO/name) for name in changed}
focused=read(ROOT/'binding-helpers-v3.json')['source']
for name in changed[:-1]:assert final_source[name]==focused[name],name
process=read(ROOT/'process-check.json');assert process['matching_python_processes']==0
summary=read(ROOT/'summary.json')
assert runs['screen-v2']['result']['screen_pass']
assert runs['helpers-v3']['result']['pytest_exit_code']==0
assert sum(row['outcome']=='failed' for row in summary['tests'])==2
assert sum(row['outcome']=='passed' for row in summary['tests'])==6
handoff=dict(state='PARTIAL source candidate; narrow screen and focused ownership checks verified; strict full cohort FAILED; unqualified',
    completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    numerical_lease='RELEASE; no owned process or job handle remains',process_check=process,
    changed_paths_and_sha256=final_source,unchanged_strict_fixture_and_legacy={name:sha(REPO/name) for name in unchanged},
    preserved_original_manifests=preserved,
    preserved_read=dict(handoff_sha256=sha(EVIDENCE/'owner-diagnosis-v3-handoff.json'),files=len(diagnosis['new_files'])),
    preserved_local_audit=dict(manifest_sha256=sha(EVIDENCE/'local-audit-v4/artifact-sha256.json'),files=len(local['artifacts'])),
    preserved_old_wheel=dict(sha256=artifact['sha256'],artifact=artifact['artifact'],verified_payloads=len(artifact['source']),
                             limitation='older source only, not candidate installed evidence'),
    checks_actually_run={phase:dict(status=r['execution']['status'],exit_code=r['execution']['exit_code'],
        seconds=r['execution']['elapsed_seconds'],peak_tree_bytes=r['execution']['sampled_peak_tree_bytes'],
        numerical_pool_ceiling=r['execution']['sampled_numeric_or_unresolved_max'],
        binding_sha256=r['binding_sha256'],runtime_sha256=r['runtime_sha256'],solver_imports=r['solver_imports'])
        for phase,r in runs.items()},
    results=dict(screen_commit=runs['screen-v2']['result']['accepted'],screen_work=runs['screen-v2']['result']['work_counts'],
        focused_helpers='15 passed in2.32s after schema/iterable repairs; 14 passed earlier',
        strict_cohort='2 FAILED /6 historical impact PASS; 30 accepted checkpoints saved; no rerun',
        strict_accepted_inventories=summary['strict_accepted_inventories'],terminal_j2_failure=summary['terminal_j2_failure']),
    algorithm='new-policy-only existing yield/table equations, reused T^-1L, owned station derivatives, propagated binary64 guard; full-first+actual strict merit within unchanged13candidate budget',
    preparation='one original compliance solve per physical response; added owned station projection per capture; zero additional material response/compliance solves from event proposal; exact per-test counts in summary.json/work.json',
    failures=dict(helper_path='helpers-v1 preserved zero-collection relative-path error',
        screen_observation='screen-v1 preserved exact-float harness assertion before Newton work',
        false_strict='unchanged line249 at h1e-4 branch consistency fails; directional error not computed',
        true_strict='backtrack/cutback exhaustion at .90625 after accepted.875; final proposal null and all13dyadics',
        metadata='summary empty elastic-shell inventory error preserved, repaired standard-library only',
        procedure='procedure-observations.json; initial root sandbox missing-file observation was ACL false status, not preservation defect'),
    unmet=['full lifecycle/smooth tangent at unchanged controls', 'J2 global equilibrium beyond.875',
           'failed J2 R/K/residual and merit-state capture missing', 'new installed candidate gate',
           'aggregate material/connection/chart/F03/G0-G6 and qualification/consumer obligations'],
    disposition='candidate preserved; no new wheel because full cohort FAILED; no fixture/direction/tolerance/global equation change or speculative next trial',
    source_versions='global screen/cohort bind executed pre-schema/iterable repair source; final source programming fixes bind helpers-v3; no scientific rerun claimed',
    evidence=['summary.json','cohort-v1/junit.xml','cohort-v1/accepted-histories.json','cohort-v1/accepted-*.bin',
              'cohort-v1/work.json','screen-v2/result.json','screen-v2/accepted.bin','helpers-v3/stdout.log',
              'binding-*.json','executed-*/','*/runtime.json','*/execution.json','*/thread-samples.json'])
(ROOT/'handoff.json').write_text(json.dumps(handoff,indent=2)+'\n')
manifest={}
for path in sorted(ROOT.rglob('*')):
    if path.is_file() and not any(part in ('__pycache__','.pytest_cache') for part in path.parts) and path.name!='artifact-sha256.json':
        manifest[str(path.relative_to(ROOT)).replace('\\','/')]=dict(bytes=path.stat().st_size,sha256=sha(path))
(ROOT/'artifact-sha256.json').write_text(json.dumps(dict(scope='new owned boundary-candidate-v5 only; excludes self/caches',
                                                     artifacts=manifest),indent=2)+'\n')
print(json.dumps(dict(state=handoff['state'],source=final_source,preserved_counts=[760,779],
    local_artifacts=len(manifest),owned_processes=0,handoff_sha256=sha(ROOT/'handoff.json'),
    manifest_sha256=sha(ROOT/'artifact-sha256.json')),indent=2))
