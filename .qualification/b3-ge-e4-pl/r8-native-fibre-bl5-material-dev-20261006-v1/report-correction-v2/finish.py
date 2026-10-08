from pathlib import Path
import ast, hashlib, json
import psutil
ROOT=Path(__file__).resolve().parent;EVIDENCE=ROOT.parent;REPO=EVIDENCE.parents[2]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
old_manifest=EVIDENCE/'raw-artifact-sha256.json'
consumed=json.loads(old_manifest.read_text())
for name,row in consumed['artifacts'].items():assert sha(EVIDENCE/name)==row['sha256'],name
old=json.loads((EVIDENCE/'handoff.json').read_text())
for name,digest in old['source_sha256'].items():
    if name.startswith('src/'):assert sha(REPO/name)==digest,name
artifact=json.loads((EVIDENCE/'artifact-binding-v1.json').read_text())
assert sha(artifact['artifact'])==artifact['sha256']
for name,digest in artifact['source'].items():
    installed=EVIDENCE/'installed-wheel-v1'/name.replace('\\','/').removeprefix('src/')
    assert sha(installed)==digest,name
test='tests/test_stiffened_shell_native_fibre_bl5_material.py'
gate='test_native_material_lifecycle_and_fixed_predecessor_tangent'
def gate_ast(p):
    return ast.dump(next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==gate))
assert gate_ast(REPO/test)==gate_ast(EVIDENCE/'executed-source-partial-atomic-v1'/test)
names=('examples/stiffened_shell_native_fibre_bl5_material.py',test,'docs/reference_cases/stiffened_shell_native_fibre_bl5_material.md')
for name in names:
    if name.endswith('.py'):ast.parse((REPO/name).read_text())
runtime=json.loads((ROOT/'runtime.json').read_text())
execution=json.loads((ROOT/'installed-report-v2/execution.json').read_text())
assert runtime['failed']==0 and runtime['collected']==1 and execution['status']=='completed'
processes=[]
entries={str((EVIDENCE/'entry.py').resolve()).lower(),str((ROOT/'entry.py').resolve()).lower()}
for p in psutil.process_iter(['pid','cmdline']):
    try:
        if any(str(Path(a).resolve()).lower() in entries for a in (p.info['cmdline'] or [])):
            processes.append(p.info)
    except (psutil.AccessDenied,psutil.NoSuchProcess,OSError):pass
assert not processes,processes
handoff=dict(state='partial verified reporting correction only; original full material milestone remains FAILED/unmet',
    disposition='V1 material maxima mixed prefix.2 with continued.25625 report fields; fixed both maxima to actual continued state',
    source_sha256={n:sha(REPO/n) for n in names},frozen_product_unchanged=True,
    consumed_v1=dict(artifacts_verified=len(consumed['artifacts']),manifest_sha256=sha(old_manifest),
        handoff_sha256=sha(EVIDENCE/'handoff.json'),result_sha256=sha(EVIDENCE/'result-installed-partial-v1.json'),
        all_paths_byte_exact=True),
    installed_input=dict(wheel_path=artifact['artifact'],sha256=artifact['sha256'],
        installed_root=artifact['installed_root'],all424source_payload_hashes_unchanged=True,rebuilt=False),
    check=dict(test='test_public_partial_report_matches_final_accepted_state',passed=1,
        execution=execution,actual_imported_solver_modules=len(runtime['imports']),
        runtime='report-correction-v2/runtime.json',binding='report-correction-v2/binding.json',
        result=json.loads((ROOT/'result-installed-report-v2.json').read_text())),
    full_gate_cases='Both strict(.5,1) lifecycle parameter cases remain in producttests; AST byte-semantics unchanged; no skip/xfail/full rerun/acceptance claim',
    numerical_slot='RELEASED; no owned entry process remains',owned_numerical_processes=0,
    remaining='Original handoff unmet simultaneous shell/fibre, yielded mixed-generalized and failed-trial complete tangent/global equilibrium obligations unchanged')
target=EVIDENCE/'handoff-v2.json';assert not target.exists();target.write_text(json.dumps(handoff,indent=2)+'\n')
excluded={'installed-wheel-v1','wheel-v1','wheel-source-v1','__pycache__','.pytest_cache'}
manifest={}
for p in EVIDENCE.rglob('*'):
    if p.is_file() and not any(part in excluded for part in p.relative_to(EVIDENCE).parts) and p.name!='raw-artifact-sha256-v2.json':
        manifest[str(p.relative_to(EVIDENCE))]=dict(bytes=p.stat().st_size,sha256=sha(p))
target=EVIDENCE/'raw-artifact-sha256-v2.json';assert not target.exists()
target.write_text(json.dumps(dict(excluded_directories=sorted(excluded),consumed_v1_preserved=True,artifacts=manifest),indent=2)+'\n')
print(json.dumps(dict(passed=1,consumed_v1_verified=len(consumed['artifacts']),manifest_v2_artifacts=len(manifest),
    actual_solver_imports=len(runtime['imports']),owned_processes=0,final_fibre_alpha=handoff['check']['result']['actual_final']['fibre_alpha_max'])))
