"""Independent saved-artifact inspection. Standard library only; no solver job."""
from pathlib import Path
import hashlib
import json
import xml.etree.ElementTree as ET
import zipfile

raw = Path(__file__).resolve().parent
repo = raw.parents[2]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda name: json.loads((raw / name).read_text())
manifest = read('raw-artifact-sha256.json')['artifacts']
for name, expected in manifest.items():
    path = raw / name
    assert path.resolve().is_relative_to(raw.resolve()), name
    assert path.stat().st_size == expected['bytes'] and sha(path) == expected['sha256'], name
handoff = read('handoff.json')
for name in handoff['changed_product_files']:
    assert sha(repo / name) == handoff['source_sha256'][name], name
artifact = read('artifact-binding-v1.json')
site, wheel = Path(artifact['installed_root']), Path(artifact['artifact'])
assert sha(wheel) == artifact['sha256'] == 'ca2503e2178aa536b79d556a2c105faef29977f6d7a1442e989bddde077cd849'
with zipfile.ZipFile(wheel) as archive:
    for name, expected in artifact['source'].items():
        rel = name.replace(chr(92), '/')
        assert rel.startswith('src/anysolver/')
        assert sha(repo / rel) == sha(site / rel[4:]) == expected, name
        assert hashlib.sha256(archive.read(rel[4:])).hexdigest() == expected, name
runtime = read('runtime-installed-partial-v1.json')
ci = raw.parent / 'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
for name, version in {'numpy': '2.5.3', 'scipy': '1.18.1', 'numba': '0.68.0', 'llvmlite': '0.50.0'}.items():
    dep = runtime['dependencies'][name]
    assert dep['version'] == version and Path(dep['path']).resolve().is_relative_to(ci.resolve()), name
assert all(Path(p).resolve().is_relative_to(site.resolve()) for p in runtime['imports'].values())
assert runtime['jit_disabled'] and runtime['affinity'] == [0]
assert all(p['num_threads'] == 1 for p in runtime['pools'])
cases = {}
for phase in ('admission-v4', 'impact-v1', 'impact-v2', 'partial-atomic-v1', 'lifecycle-v1'):
    tested = list(ET.parse(raw / f'junit-{phase}.xml').iter('testcase'))
    failed = sum(c.find('failure') is not None or c.find('error') is not None for c in tested)
    skipped = sum(c.find('skipped') is not None for c in tested)
    cases[phase] = {'executed': len(tested), 'failed': failed, 'skipped': skipped}
    assert skipped == 0
    assert failed == (2 if phase == 'lifecycle-v1' else 0), phase
for phase in ('admission-v4', 'impact-v1', 'impact-v2', 'partial-atomic-v1', 'installed-partial-v1'):
    execution = read(f'{phase}/execution.json')
    assert execution['exit_code'] == 0 and execution['status'] == 'completed', phase
    assert execution['elapsed_seconds'] <= 600 and execution['sampled_peak_tree_bytes'] <= 2147483648, phase
    assert execution['sampled_numeric_or_unresolved_max'] <= 1, phase
# Reverted product is byte-equal to the original recorded dyadic driver.
admission = read('binding-admission-v4.json')
driver = 'src/anysolver/_stiffened_shell_ge_finite_experimental.py'
assert sha(repo / driver) == admission['source'][driver], 'dyadic rollback'
assert '.5**backtrack' in (repo / driver).read_text()
assert not handoff['owned_numerical_processes']
summary = dict(scope='Independent artifact/source/runtime inspection; no numerical rerun',
    original_raw_artifacts=len(manifest), current_source_site_wheel_modules=len(artifact['source']),
    actual_imported_solver_modules=len(runtime['imports']), wheel_sha256=sha(wheel),
    cases=cases, product_dyadic_rollback_verified=True,
    candidate_disposition='PARTIAL_EXPERIMENTAL_NOT_MERGE_READY', full_material_gate=False,
    scientific_acceptance=False, runtime_scope='Actual effective settings and sampled resources only',
    lifecycle_scope='Original full failures used wrong dependency graph; final exact-CI full cases remain unmet, no current full-file pass',
    reporting_scope='V1 public result mixed prefix material maxima with final state; retained failed reporting evidence, separately repaired in V2',
    verifier_sha256=sha(__file__))
(raw / 'root-integration-binding-v1.json').write_bytes((json.dumps(summary, indent=2) + '\n').encode())
print(json.dumps(summary))
