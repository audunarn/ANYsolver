"""Byte/provenance audit only; no numerical imports or execution."""
import ast
import hashlib
import json
import pathlib
import subprocess
import xml.etree.ElementTree as ET
import zipfile

ROOT = pathlib.Path.cwd()
RAW = ROOT / '.qualification/b3-ge-e4-pl/r8-native-fibre-bl5-mixed-j2-installed-dev-20261006-v1'
COMMIT = 'cb252cd15b6db14688dee1d60341ddfeda9103c6'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read(name):
    return json.loads((RAW / name).read_text(encoding='utf-8'))

def safe(name):
    assert '\\' not in name and 'us3-modal-canary' not in name
    p = pathlib.PurePosixPath(name)
    assert not p.is_absolute() and '..' not in p.parts
    return RAW / p

def verify_manifest(name):
    values = read(name)
    for path, expected in values.items():
        assert digest(safe(path).read_bytes()) == expected, path
    return len(values)

assert subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip() == COMMIT
counts = {n: verify_manifest(n) for n in ('artifact-sha256-v1.json', 'artifact-sha256-v2.json')}
assert counts == {'artifact-sha256-v1.json': 1363, 'artifact-sha256-v2.json': 1387}
assert digest((RAW/'handoff-v2.json').read_bytes()) == '37faad662a8afae946e52cf2e65d5e576834c40e16902a645f88b259a25f57be'
assert digest((RAW/'artifact-sha256-v2.json').read_bytes()) == '2ea5f50a473e4226098763ad69aa3a9f0d55d6142658ef5ad4a90ef2f58a8813'

binding = read('source-stage-binding-v1.json')['source']
assert len(binding) == 435
tree = subprocess.check_output(['git','ls-tree','-r','-z',COMMIT,'--','src/anysolver','pyproject.toml','README.md','LICENSE','COPYRIGHT','THIRD_PARTY_NOTICES.md'])
objects = {}
eol_equivalent = []
for item in tree.split(b'\0'):
    if item:
        header, path = item.split(b'\t',1)
        objects[path.decode()] = header.split()[2].decode()
for path, expected in binding.items():
    data = (ROOT/path).read_bytes()
    assert digest(data) == expected, path
    git_bytes = data
    if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() != objects[path]:
        data.decode('utf-8')
        git_bytes = data.replace(b'\r\n',b'\n')
        assert hashlib.sha1(b'blob '+str(len(git_bytes)).encode()+b'\0'+git_bytes).hexdigest() == objects[path], path
        eol_equivalent.append(path)
    assert digest((RAW/'build-source-v1'/path).read_bytes()) == expected, path

provenance = read('artifact-provenance-v1.json')
wheel = safe(provenance['wheel'])
assert digest(wheel.read_bytes()) == provenance['wheel_sha256'] == '375e9e4525c93aaa4e1d75a26bbbd8fb506494064ae3a698e5ea67603c9b5a9b'
payload = provenance['payload']
assert len(payload) == 430
site = RAW/provenance['installed_target']
with zipfile.ZipFile(wheel) as archive:
    keys = {n for n in archive.namelist() if n.startswith('anysolver/') and not n.endswith('/')}
    assert keys == set(payload)
    for path, expected in payload.items():
        assert digest(archive.read(path)) == expected == binding['src/'+path], path
        assert digest((site/path).read_bytes()) == expected, path

original_inputs = read('check-input-binding-v1.json')['files']
corrected_inputs = read('example-input-binding-v2.json')['files']
assert len(original_inputs) == 7 and len(corrected_inputs) == 4
for path, expected in original_inputs.items():
    assert digest((RAW/'check-stage-v1'/path).read_bytes()) == expected, path
for path, expected in corrected_inputs.items():
    assert digest((RAW/'example-stage-v2'/path).read_bytes()) == expected, path
    if path != 'examples/stiffened_shell_native_fibre_bl5_mixed_j2_displacement.py':
        assert digest((ROOT/path).read_bytes()) == expected == original_inputs[path], path
example_path = 'examples/stiffened_shell_native_fibre_bl5_mixed_j2_displacement.py'
original = ast.parse((RAW/'check-stage-v1'/example_path).read_bytes())
corrected = ast.parse((RAW/'example-stage-v2'/example_path).read_bytes())
def without_workflow(tree):
    return ast.dump(ast.Module(body=[n for n in tree.body if not isinstance(n,ast.FunctionDef) or n.name!='workflow'],type_ignores=[]),include_attributes=False)
assert without_workflow(original) == without_workflow(corrected)
assert digest((ROOT/'tests/test_native_fibre_bl5_mixed_j2_displacement.py').read_bytes()) == '2c361f2be50c74277d526d97f804f58eeede3120fa433932bb4278451df74c7c'

expected_pins = {'numpy':'2.5.3','scipy':'1.18.1','numba':'0.68.0','llvmlite':'0.50.0'}
runtime_files = ['installed-imports-before-v1.json','installed-imports-after-tests-v1.json','installed-imports-terminal-v1.json','example-imports-before-v2.json','example-imports-after-v2.json','example-imports-terminal-v2.json']
runtime_counts = {}
baseline = read(runtime_files[0])
for name in runtime_files:
    runtime = read(name)
    assert runtime['affinity']==[0] and runtime['numba_threads']==1 and runtime['jit_disabled'] is True
    assert all(p['num_threads']==1 for p in runtime['pools'])
    assert all(v is None for v in runtime['unforced_backend'].values())
    assert {k:v['version'] for k,v in runtime['pins'].items()} == expected_pins
    assert runtime['pins']==baseline['pins'] and runtime['dependency_distributions']==baseline['dependency_distributions']
    assert runtime['readonly_sibling_modules']==baseline['readonly_sibling_modules']
    for info in runtime['imports'].values():
        assert pathlib.Path(info['path']).is_relative_to(site)
        assert digest(pathlib.Path(info['path']).read_bytes()) == info['sha256'] == payload[info['payload_key']]
    for info in runtime['readonly_sibling_modules'].values():
        assert digest(pathlib.Path(info['path']).read_bytes()) == info['sha256']
    runtime_counts[name] = len(runtime['imports'])
assert len(baseline['readonly_sibling_modules']) == 117

suite = ET.parse(RAW/'installed-junit-v1.xml').getroot().find('testsuite')
assert suite.attrib['tests']=='8' and all(suite.attrib[k]=='0' for k in ('errors','failures','skipped'))
ids = [case.attrib['classname']+'::'+case.attrib['name'] for case in suite.findall('testcase')]
assert len(set(ids))==8
old = read('installed-job-v1/execution.json')
new = read('example-job-v2/execution.json')
build = read('build-resource-receipt-v1.json')
assert old['status']=='failed' and old['exit_code']==1
assert new['status']=='completed' and new['exit_code']==0
assert read('installed-result-v1.json')['pytest_exit_code']==0
result = read('example-result-v2.json')['result']
assert result['status']=='completed' and result['generation']==4
assert result['fresh_restore_bytes_equal'] and result['continued_bytes_equal'] and result['production_qualified'] is False
for receipt in (build,old,new):
    assert receipt['elapsed_seconds'] <= receipt['seconds_limit']
    assert receipt['sampled_peak_tree_bytes'] < receipt['memory_limit_bytes'] == 2*1024**3
    assert receipt['affinity_before_child_code']==[0]
for receipt in (old,new):
    assert receipt['sampled_numeric_or_unresolved_max']==1
used = 252.45465660013724 + build['elapsed_seconds']+old['elapsed_seconds']+new['elapsed_seconds']
assert abs(used-372.8705885000527)<1e-10
proof = dict(status='verified',source_commit=COMMIT,manifest_counts=counts,source_and_build_bindings=435,git_checkout_CRLF_only_paths=eol_equivalent,package_payloads=430,original_inputs=7,example_inputs=4,non_workflow_AST_unchanged=True,test_SHA_unchanged=True,actual_import_counts=runtime_counts,readonly_sibling_modules=117,test_case_ids=ids,installed_tests='8 PASS; original subsequent example failure retained',corrected_example='completed restore and continuation',used_process_wall_seconds=used,remaining_seconds=600-used,wheel_sha256=provenance['wheel_sha256'],limitations=['Sampled RSS/threads; not G5 resource qualification','Named material-family proof is from mapped raw focused tests; example aggregate labels require separate disposition','Different-family/scientific/G6/release/complete-programme gates remain open'])
(RAW/'root-installed-verification-v2.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in proof.items() if k not in ('test_case_ids','actual_import_counts','limitations','git_checkout_CRLF_only_paths')},indent=2))
