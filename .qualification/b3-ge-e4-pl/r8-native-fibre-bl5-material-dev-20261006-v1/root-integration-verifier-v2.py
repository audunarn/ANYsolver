"""Final reporting correction inspection. No solver or numerical rerun."""
from pathlib import Path
import ast
import hashlib
import json
import xml.etree.ElementTree as ET

raw = Path(__file__).resolve().parent
repo = raw.parents[2]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda name: json.loads((raw / name).read_text())
v1, v2 = (read(name)['artifacts'] for name in ('raw-artifact-sha256.json', 'raw-artifact-sha256-v2.json'))
assert all(v2[name] == expected for name, expected in v1.items())
for name, expected in v2.items():
    p = raw / name
    assert p.resolve().is_relative_to(raw.resolve())
    assert p.stat().st_size == expected['bytes'] and sha(p) == expected['sha256'], name
old, new = read('handoff.json'), read('handoff-v2.json')
for name in old['changed_product_files']:
    assert sha(repo / name) == old['source_sha256'][name], name
for name, expected in new['source_sha256'].items():
    assert sha(repo / name) == expected, name
test_name = 'tests/test_stiffened_shell_native_fibre_bl5_material.py'
snapshots = [raw / name for name, expected in v1.items() if expected['sha256'] == old['source_sha256'][test_name]]
assert snapshots, 'Original strict tests must remain reconstructable'
functions = lambda p: {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(p.read_text()).body if isinstance(n, ast.FunctionDef)}
before, after = functions(snapshots[0]), functions(repo / test_name)
strict = 'test_native_material_lifecycle_and_fixed_predecessor_tangent'
assert before[strict] == after[strict]
assert not any('skip' in n or 'xfail' in n for n in after)
case = list(ET.parse(raw / 'report-correction-v2/junit.xml').iter('testcase'))
assert len(case) == 1 and all(case[0].find(k) is None for k in ('error', 'failure', 'skipped'))
report_record = read('report-correction-v2/result-installed-report-v2.json')
result = report_record['report']
assert all(result[name] == value for name, value in report_record['actual_final'].items())
runtime = read('report-correction-v2/runtime.json')
assert result['load_factor'] == .25625 and result['generation'] == result['resumed_generation'] == 4
assert result['fibre_alpha_max'] > old['installed_artifact']['public_result']['fibre_alpha_max']
assert result['shell_alpha_max'] == 0 and not result['production_qualified']
site = Path(old['installed_artifact']['installed_root'])
assert all(Path(p).resolve().is_relative_to(site.resolve()) for p in runtime['imports'].values())
assert all(p['num_threads'] == 1 for p in runtime['pools'])
assert not new['owned_numerical_processes']
summary = dict(scope='Final source/artifact and executed reporting regression inspection; no numerical rerun',
    original760_preserved=True, version2_raw_artifacts=len(v2), strict_full_cases_AST_unchanged=True,
    final_report_load_factor=result['load_factor'], final_report_fibre_alpha=result['fibre_alpha_max'],
    scientific_acceptance=False, full_material_gate=False,
    prior_root_binding_sha256=sha(raw / 'root-integration-binding-v1.json'),
    verifier_sha256=sha(__file__), candidate_disposition='PARTIAL_EXPERIMENTAL_NOT_MERGE_READY')
(raw / 'root-integration-binding-v2.json').write_bytes((json.dumps(summary, indent=2) + '\n').encode())
print(json.dumps(summary))
