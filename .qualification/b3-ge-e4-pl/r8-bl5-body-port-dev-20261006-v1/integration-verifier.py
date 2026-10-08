"""Root inspection of a FAILED development slice. No numerical execution."""
from pathlib import Path
import ast
import hashlib
import json
import xml.etree.ElementTree as ET
import zipfile

raw = Path(__file__).resolve().parent
repo = raw.parents[2]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda name: json.loads((raw / name).read_text())
handoff = read('handoff.json')
binding = read('binding-v2.json')
for name, digest in handoff['source'].items():
    assert sha(repo / name) == digest, name
for name, digest in handoff['evidence'].items():
    assert sha(raw / name) == digest, name
assert sha(raw / 'run-v2.py') == binding['runner_sha256']
assert sha(raw / 'entry-v2.py') == binding['entry_sha256']
assert sha(raw / 'supervisor-function-v2.py') == binding['derived_supervisor_sha256']
assert sha(repo / 'scripts/r8_bl5_body_port_probe.py') == sha(raw / 'executed-script-v2.py')
assert sha(repo / 'tests/test_r8_bl5_body_port_probe.py') == sha(raw / 'executed-tests-v2.py')
site = raw.parent / 'r8-native-fibre-bl5-dev-20261005-v1/installed-s3-v1'
wheel = site.parent / 'wheel-s3-v1/anysolver-0.4.7-py3-none-any.whl'
ci = raw.parent / 'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
assert sha(wheel) == binding['wheel_sha256']
with zipfile.ZipFile(wheel) as archive:
    for name, digest in binding['installed_modules'].items():
        assert sha(site / name) == digest, name
        assert hashlib.sha256(archive.read(name.replace(chr(92), '/'))).hexdigest() == digest, name
for name, digest in binding['ci_dependencies'].items():
    assert sha(ci / name) == digest, name
saved = raw.parent / 'r8-bl5-weak-continuum-dev-20261006-v1'
for name, digest in binding['saved_continuum'].items():
    assert sha(saved / name) == digest, name

coverage, failures, phases = set(), set(), {}
for version in (1, 2):
    cases = list(ET.parse(raw / f'junit-v{version}.xml').iter('testcase'))
    passed = {c.attrib['name'] for c in cases if all(c.find(k) is None for k in ('failure', 'error', 'skipped'))}
    failed = {c.attrib['name'] for c in cases if c.find('failure') is not None or c.find('error') is not None}
    coverage.update(passed)
    failures.update(failed)
    phases[str(version)] = {'passed': len(passed), 'failed': len(failed)}
assert len(coverage) == 6 and failures == {'test_two_body_rhs_and_actual_material_energy'}
functions = lambda p: {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(p.read_text()).body if isinstance(n, ast.FunctionDef)}
prior, final = (functions(raw / f'executed-tests-v{v}.py') for v in (1, 2))
reuse = read('reuse-v2.json')
assert reuse['state'] == 'EXACT_PASSED_PREREQUISITE_FUNCTIONS_REUSED'
prior_text = (raw / 'executed-tests-v1.py').read_text()
prior_segments = {n.name: ast.get_source_segment(prior_text, n) for n in ast.parse(prior_text).body if isinstance(n, ast.FunctionDef)}
for name, digest in reuse['prerequisite_function_sha256'].items():
    assert prior[name] == final[name]
    assert hashlib.sha256(prior_segments[name].encode()).hexdigest() == digest, name
runtime, execution = read('runtime-v2.json'), read('focused-v2/execution.json')
assert runtime['affinity'] == [0] and runtime['jit_off'] and runtime['numba_threads'] == 1
assert runtime['exit_code'] == execution['exit_code'] == 1 and runtime['failed'] == 1 and not runtime['errors']
assert all(p['num_threads'] == 1 for p in runtime['pools'])
assert all(Path(p).resolve().is_relative_to(site.resolve()) for p in runtime['imports'].values())
expected_versions = {'numpy': '2.5.3', 'scipy': '1.18.1', 'numba': '0.68.0', 'llvmlite': '0.50.0'}
for name, version in expected_versions.items():
    dep = runtime['dependencies'][name]
    assert dep['version'] == version and Path(dep['path']).resolve().is_relative_to(ci.resolve()), name
assert execution['sampled_numeric_or_unresolved_max'] <= 1
assert execution['sampled_peak_tree_bytes'] <= 2147483648 and execution['elapsed_seconds'] <= 600
result = read('results-v2/probe/shell-calculated.json')
slot = 51
load = result['full_physical_load_covector'][slot]
residual = result['full_unscaled_residual'][slot]
assert result['status'] == 'CALCULATED_NOT_VALIDATED'
assert abs(residual / load) == handoff['obstruction']['active_row_ratio']
assert abs(residual / load) > 1e-8 and result['work_relative_error'] <= 1e-8
assert handoff['compute_inventory']['shell_calculations'] == 2
assert handoff['compute_inventory']['beam_RHS'] == handoff['compute_inventory']['external'] == 0
assert not handoff['scientific_acceptance']
summary = dict(scope='Root artifact/source/runtime inspection; no numerical rerun',
    disposition='FAILED_BODY_COMPARISON_WITHHELD', phases=phases,
    distinct_prerequisite_controls_passed=len(coverage), scientific_probe_failed=True,
    source_site_wheel_modules=len(binding['installed_modules']),
    loaded_solver_modules=len(runtime['imports']),
    evidence_hashes_checked=len(handoff['evidence']),
    wheel_sha256=sha(wheel), verifier_sha256=sha(__file__),
    compute_inventory=handoff['compute_inventory'],
    original_row_gate_ratio=abs(residual/load), scientific_acceptance=False,
    evidence_gap='Native matrix bytes absent; residual is observed, not independently reproduced from saved native K',
    runtime_scope='V2 actual settings and sampled resources only; V1 serialization unproven',
    product_source_scope='Installed prior immutable artifact; current dirty material source is not represented')
(raw / 'integration-binding.json').write_bytes((json.dumps(summary, indent=2) + '\n').encode())
print(json.dumps(summary))
