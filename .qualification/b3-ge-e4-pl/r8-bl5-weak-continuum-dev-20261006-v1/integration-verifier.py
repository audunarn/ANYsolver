"""Root artifact/coverage inspection only; no numerical job or inference."""
from pathlib import Path
import ast, hashlib, json, xml.etree.ElementTree as ET, zipfile

raw = Path(__file__).resolve().parent
repo = raw.parents[2]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
handoff = json.loads((raw / 'handoff.json').read_text())
for name, digest in handoff['all_artifacts'].items():
    assert sha(raw / name) == digest, name
for name, digest in handoff['source'].items():
    assert sha(repo / name) == digest, name
binding = json.loads((raw / 'binding-v3.json').read_text())
site = raw.parent / 'r8-native-fibre-bl5-dev-20261005-v1/installed-s3-v1'
ci = raw.parent / 'r8-native-s3-restart-binding-dev-20261005-v1/ci-site-network-v2'
coverage, inventory, phases = set(), set(), {}
for version in (1, 2, 3):
    cases = list(ET.parse(raw / f'junit-v{version}.xml').iter('testcase'))
    names = {c.attrib['name'] for c in cases}
    passed = {c.attrib['name'] for c in cases if all(c.find(k) is None for k in ('failure', 'error', 'skipped'))}
    if version == 1:
        inventory = names
    coverage.update(passed)
    phases[str(version)] = {'tested': len(cases), 'passed': len(passed)}
    runtime = json.loads((raw / f'runtime-v{version}.json').read_text())
    execution = json.loads((raw / f'focused-v{version}/execution.json').read_text())
    assert runtime['affinity'] == [0] and runtime['jit_off'] and runtime['numba_threads'] == 1 and not runtime['errors']
    assert all(p['num_threads'] == 1 for p in runtime['pools'])
    assert all(Path(p).resolve().is_relative_to(site.resolve()) for p in runtime['imports'].values())
    assert all(Path(runtime['dependencies'][n]['path']).resolve().is_relative_to(ci.resolve()) for n in ('numpy', 'scipy', 'numba', 'llvmlite'))
    assert execution['sampled_numeric_or_unresolved_max'] <= 1
    assert execution['sampled_peak_tree_bytes'] <= 2147483648 and execution['elapsed_seconds'] <= 600
assert coverage == inventory and len(coverage) == 9
functions = lambda p: {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(p.read_text()).body if isinstance(n, ast.FunctionDef)}
scripts = [functions(raw / f'executed-script-v{v}.py') for v in (1, 2, 3)]
tests = [functions(raw / f'executed-tests-v{v}.py') for v in (1, 2, 3)]
assert scripts[0] == scripts[1]
assert {k for k in scripts[1] if scripts[1][k] != scripts[2][k]} == {'solve'}
assert {k for k in tests[0] if tests[0][k] != tests[1][k]} == {'test_transpose_work_both_body_wrenches_and_normal_spin'}
assert {k for k in tests[1] if tests[1][k] != tests[2][k]} == {'strong_verified', 'test_one_weak_solve_and_saved_native_diagnostic'}
assert sha(repo / 'scripts/r8_bl5_weak_continuum_reference.py') == sha(raw / 'executed-script-v3.py')
assert sha(repo / 'tests/test_r8_bl5_weak_continuum_reference.py') == sha(raw / 'executed-tests-v3.py')
for rel, digest in binding['installed_modules'].items():
    assert sha(site / rel) == digest and sha(repo / 'src' / rel) == digest, rel
wheel = site.parent / 'wheel-s3-v1/anysolver-0.4.7-py3-none-any.whl'
assert sha(wheel) == binding['wheel_sha256']
with zipfile.ZipFile(wheel) as archive:
    for rel, digest in binding['installed_modules'].items():
        assert hashlib.sha256(archive.read(rel.replace(chr(92), '/'))).hexdigest() == digest, rel
expected = {'strong': 2, 'strong_failed_reporting': 1, 'strong_validated': 1, 'weak': 1, 'native': 0, 'external': 0}
assert handoff['compute_inventory'] == expected
strong = json.loads((raw / 'results-v3/strong-v1.json').read_text())
weak = json.loads((raw / 'results-v3/weak-v1.json').read_text())
for result in (strong, weak):
    assert result['status'] == 'DEVELOPMENT_SOLVED_NOT_ACCEPTED' and not result['comparison_qualified']
    assert result['equation_ratio'] <= 1e-8 and result['constraint_max'] <= 1e-9
    assert max(abs(v) for v in result['total_wrench']) <= 1e-8
    assert result['internal_work_relative_error'] <= 1e-8 and result['interface_work_relative_error'] <= 1e-8
    for cut in result['domain_cuts'].values():
        assert max(abs(a-b-c-d) for a,b,c,d in zip(cut['internal_wrench'],cut['interface_wrench'],cut['applied_wrench'],cut['support_wrench'])) <= 1e-8
summary = {'scope': 'root independent artifact, source-impact and executed-check inspection; no numerical rerun', 'distinct_controls': len(coverage), 'phases': phases, 'compute_inventory': expected, 'verified_artifact_count': len(handoff['all_artifacts']), 'source_site_wheel_modules': len(binding['installed_modules']), 'loaded_solver_modules': len(runtime['imports']), 'wheel_sha256': sha(wheel), 'verifier_sha256': sha(__file__), 'scientific_acceptance': False, 'runtime_settings_verified': True}
(raw / 'integration-binding.json').write_bytes((json.dumps(summary, indent=2) + '\n').encode())
print(json.dumps(summary))
