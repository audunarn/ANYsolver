"""Static isolated-wheel evidence and embedded reference bindings."""

import ast
import hashlib
import json
from pathlib import Path
import pytest


ROOT = Path(__file__).resolve().parents[1]


def pairs(rows):
    result = {}
    for key, value in rows:
        if key in result: raise ValueError('duplicate key')
        result[key] = value
    return result


def reject(_): raise ValueError('nonfinite value')


def evidence():
    raw = (ROOT/'docs/reference_cases/ge_beam3_signed_modes_installed_evidence.json').read_text(encoding='utf-8')
    record = json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)
    assert json.dumps(record, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n' == raw
    return record


def test_baseline_and_two_source_bindings():
    record = evidence()
    assert record['baseline'] == dict(commit='2b0ee70beda6f12e81bb57aa95195c424364a23d',
        tree='f8a21473610c6e05abe92847f796c0ea80ff88b2')
    assert len(record['sources']) == 2 and record['source_normalization'] == 'UTF8_LF'
    for row in record['sources']:
        path = (ROOT/row['path']).resolve(); assert path.is_relative_to(ROOT)
        raw = path.read_text(encoding='utf-8').encode('utf-8')
        assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']


def test_archive_package_and_eleven_exact_pairs():
    record = evidence(); archive = record['archive']; package = record['package']
    rows = {r['path']: r for r in archive['files']}
    assert len(rows) == len(archive['files']) == archive['file_count'] == 39
    assert sum(r['bytes'] for r in rows.values()) == archive['bytes'] == 3552060
    assert len(archive['identical_pairs']) == 11
    used = []
    for a, b in archive['identical_pairs']:
        assert a.startswith('cycle-1/') and b == a.replace('cycle-1/', 'cycle-2/', 1)
        assert rows[a]['bytes'] == rows[b]['bytes'] and rows[a]['sha256'] == rows[b]['sha256']
        used.extend((a, b))
    assert len(set(used)) == 22
    assert rows['wheels/'+package['wheel_file']]['bytes'] == package['wheel_bytes'] == 1387052
    assert rows['wheels/'+package['wheel_file']]['sha256'] == package['wheel_sha256']
    assert rows['candidate-source.zip']['sha256'] == package['source_archive_sha256']
    assert rows['source-map.json']['sha256'] == package['source_map_sha256']
    assert rows['cycle-1/result.json']['sha256'] == package['result_sha256']
    assert package['cycles_identical'] and not package['release_authorized']
    assert len(package['dependencies']) == 10 and len(package['diagnostics']) == 10


def test_scope_and_five_installed_cases():
    record = evidence()
    assert record['scope'] == dict(production_qualified=False, release_authorized=False,
        independent_review='PENDING', previous_sources_changed=False, mechanics_changed=False,
        defaults_changed=False, resource_requests_consumed=0, installed_source_count=67,
        full_prestressed_modal_qualification=False)
    assert record['checks'] == dict(installed_test_passed=True, case_count=5, process_count=2,
        source_import_isolated=True, state_replay_exact=True, negative_modes_retained=True,
        scientific_records_identical=True)
    assert record['installed_runtime'] == dict(python='3.13.9', numpy='2.5.2', scipy='1.18.1')
    cases = record['cases']
    assert [r['case'] for r in cases] == ['straight_compression', 'straight_tension', 'curved_pair',
        'plastic_unloading', 'free_curved']
    assert cases[0]['negative_count'] == 2 and cases[2]['retained_coordinates'] == 42
    assert all(r['checks_passed'] and r['replay_exact'] and r['state_preserved']
        and r['parameter_mismatch_rejected'] for r in cases)


def test_embedded_discrete_reference_matches_preserved_equations():
    reference = ast.parse((ROOT/'docs/reference_cases/ge_beam3_straight_discrete_signed_reference.py').read_text())
    worker = ast.parse((ROOT/'docs/reference_cases/ge_beam3_signed_modes_installed_smoke.py').read_text())
    for name in ('characteristic', 'bending_roots'):
        a = next(n for n in reference.body if isinstance(n, ast.FunctionDef) and n.name == name)
        b = next(n for n in worker.body if isinstance(n, ast.FunctionDef) and n.name == name)
        assert ast.dump(a, include_attributes=False) == ast.dump(b, include_attributes=False)
    for node in ast.walk(worker):
        if isinstance(node, ast.ImportFrom): assert not (node.module or '').startswith(('docs', 'tests'))
        if isinstance(node, ast.Import): assert all(not n.name.startswith(('docs', 'tests')) for n in node.names)


@pytest.mark.parametrize('raw', ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'])
def test_ambiguous_evidence_rejected(raw):
    with pytest.raises(ValueError): json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)
