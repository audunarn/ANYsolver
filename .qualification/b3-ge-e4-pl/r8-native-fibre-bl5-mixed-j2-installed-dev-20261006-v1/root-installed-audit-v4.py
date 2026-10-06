"""Final caller delta and immutable installed evidence, metadata only."""
import ast
import hashlib
import json
import pathlib
import subprocess
import zipfile

ROOT=pathlib.Path.cwd()
RAW=ROOT/'.qualification/b3-ge-e4-pl/r8-native-fibre-bl5-mixed-j2-installed-dev-20261006-v1'
def read(name): return json.loads((RAW/name).read_text(encoding='utf-8'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
manifest=read('artifact-sha256-v4.json')
assert len(manifest)==1431
assert sha(RAW/'artifact-sha256-v4.json')=='86eef8488a727e29985a0731e631c8cf23981893d28809f1f65464ffee162d52'
assert sha(RAW/'handoff-v4.json')=='4612fc7f50e8a9b5b896e7da92f2ee2db94cde9acdd890bbee66063b33aee2b8'
for path,expected in manifest.items():
    pure=pathlib.PurePosixPath(path)
    assert '\\' not in path and 'us3-modal-canary' not in path and not pure.is_absolute() and '..' not in pure.parts
    assert sha(RAW/pure)==expected,path
previous=read('root-installed-verification-v2.json')
assert subprocess.check_output(['git','rev-parse','HEAD']).decode().strip()==previous['source_commit']=='cb252cd15b6db14688dee1d60341ddfeda9103c6'
source=read('source-stage-binding-v1.json')['source']
for path,expected in source.items(): assert sha(ROOT/path)==expected,path
artifact=read('artifact-provenance-v1.json')
assert sha(RAW/artifact['wheel'])==artifact['wheel_sha256']=='375e9e4525c93aaa4e1d75a26bbbd8fb506494064ae3a698e5ea67603c9b5a9b'
site=RAW/artifact['installed_target']
with zipfile.ZipFile(RAW/artifact['wheel']) as wheel:
    for path,expected in artifact['payload'].items():
        assert hashlib.sha256(wheel.read(path)).hexdigest()==expected==sha(site/path),path
inputs=read('example-input-binding-v4.json')['files']
assert len(inputs)==4
for path,expected in inputs.items(): assert sha(ROOT/path)==expected==sha(RAW/'example-stage-v4'/path),path
example='examples/stiffened_shell_native_fibre_bl5_mixed_j2_displacement.py'
assert sha(ROOT/example)=='5fec6a6285aedcd8d006bd487d354082890d63bc3be8fd2d5307b4cf5cac14d9'
def non_workflow(path):
    tree=ast.parse(path.read_bytes())
    return ast.dump(ast.Module(body=[n for n in tree.body if not isinstance(n,ast.FunctionDef) or n.name!='workflow'],type_ignores=[]),include_attributes=False)
assert non_workflow(ROOT/example)==non_workflow(RAW/'check-stage-v1'/example)
old_runtime=read('installed-imports-after-tests-v1.json')
runtime_counts={}
for name in ('example-imports-before-v4.json','example-imports-after-v4.json','example-imports-terminal-v4.json'):
    d=read(name)
    assert d['affinity']==[0] and d['numba_threads']==1 and d['jit_disabled'] is True
    assert all(p['num_threads']==1 for p in d['pools']) and all(v is None for v in d['unforced_backend'].values())
    assert d['pins']==old_runtime['pins'] and d['dependency_distributions']==old_runtime['dependency_distributions']
    assert d['readonly_sibling_modules']==old_runtime['readonly_sibling_modules']
    for info in d['imports'].values():
        assert pathlib.Path(info['path']).is_relative_to(site)
        assert sha(pathlib.Path(info['path']))==info['sha256']==artifact['payload'][info['payload_key']]
    for info in d['readonly_sibling_modules'].values(): assert sha(pathlib.Path(info['path']))==info['sha256']
    runtime_counts[name]=len(d['imports'])
failed=read('example-job-v3/execution.json')
passed=read('example-job-v4/execution.json')
assert failed['exit_code']==1 and failed['status']=='failed'
assert passed['exit_code']==0 and passed['status']=='completed'
assert passed['sampled_numeric_or_unresolved_max']==1 and passed['affinity_before_child_code']==[0]
assert passed['elapsed_seconds']<=passed['seconds_limit']==90.
assert passed['sampled_peak_tree_bytes']<passed['memory_limit_bytes']==2147483648
disposition=read('failure-disposition-v3.json')
assert disposition['workflow_invoked'] is False and disposition['effective_pins_verified'] is False
assert disposition['entry_wrong_CI_path'] and disposition['launcher_wrong_CI_path']
data=read('example-result-v4.json')
result=data['result']; assert data['status']==result['status']=='completed'
assert result['history_generation']==3 and result['generation']==4
assert result['fresh_restore_bytes_equal'] and result['continued_bytes_equal'] and result['production_qualified'] is False
members=result['physical_fibre_members'];assert [m['element_id'] for m in members]==[2]
assert len(members[0]['station_accumulated'])==8
assert result['fibre_alpha_max']==max(members[0]['station_accumulated'])>0 and result['s3_alpha_max']>0
assert result['free_equilibrium_ratio']<=1e-9 and result['constraint_max']<=1e-9
used=previous['used_process_wall_seconds']+failed['elapsed_seconds']+passed['elapsed_seconds']
assert abs(used-402.72211770003196)<1e-10
proof=dict(status='final installed DEVELOPMENT delta verified',source_package_commit=previous['source_commit'],source_example_sha256=sha(ROOT/example),wheel_sha256=artifact['wheel_sha256'],frozen_manifest_files=1431,source_checkout_bindings=len(source),payloads=len(artifact['payload']),runtime_import_counts=runtime_counts,readonly_sibling_modules=117,definition_and_all_non_workflow_AST_unchanged=True,installed_tests_reused=8,public_example=result,used_process_wall_seconds=used,remaining_seconds=600-used,preserved_failed_attempt='V3 BOTH provenance paths wrong, pins unverified, stopped before workflow; previous owner-reuse failure and V2 attribution gap retained',git_newline_scope='Prior root V2 explicitly proved385 preexisting checkout CRLF/Git LF-only differences; no tested bytes changed',limitations=['Scoped DEVELOPMENT only; not scientific/different-family/G3/G6/release/complete-programme acceptance','Physical history is loaded generation3; endpoint generation4 quantities separately labelled','Source tangent evidence uses limited two-h/all-row-floor1 checks; mixed Q4 remains elastic','Resource memory and numerical threads are sampled, not practical-scale qualification'])
(RAW/'root-installed-verification-v4.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in proof.items() if k not in ('public_example','limitations','runtime_import_counts')},indent=2))
