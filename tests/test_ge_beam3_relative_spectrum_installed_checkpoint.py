"""Static installed-wheel evidence checks; no rebuild or mechanics rerun."""

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
    raw = (ROOT/'docs/reference_cases/ge_beam3_relative_spectrum_installed_evidence.json').read_text(encoding='utf-8')
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)
    assert json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n' == raw
    return value


def test_harness_and_candidate_bindings():
    value = evidence()
    assert value['candidate'] == dict(commit='72e095f5dba8bc0dca11b84131bcf1da4af06bc8',
        tree='664b2f518758f1011ea640988de5230f69e0394d')
    assert value['source_normalization'] == 'UTF8_LF' and len(value['sources']) == 2
    for row in value['sources']:
        path = (ROOT/row['path']).resolve(); assert path.is_relative_to(ROOT)
        raw = path.read_text(encoding='utf-8').encode('utf-8')
        assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']


def test_wheel_source_archive_and_offline_dependency_receipt():
    value = evidence(); receipt = value['receipt']; archive = value['archive']
    rows = {r['path']: r for r in archive['files']}
    assert len(rows) == len(archive['files']) == archive['file_count'] == 25
    assert sum(r['bytes'] for r in rows.values()) == archive['bytes'] == 4836387
    wheel = rows['wheels/'+receipt['wheel_file']]
    assert wheel['bytes'] == receipt['wheel_bytes'] == 1379054
    assert wheel['sha256'] == receipt['wheel_sha256'] == '578d454bdfc7d2416dbf35711ec44ddd4d33ce3cc2ec1cb990fe000011cfe8cb'
    assert rows['candidate-source.zip']['sha256'] == receipt['source_archive_sha256']
    assert rows['source-map.json']['sha256'] == receipt['source_map_sha256']
    authority = json.loads((ROOT/'docs/reference_cases/ge_beam3_mixed_p3_package_execution_authority.json').read_text())
    assert receipt['dependencies'] == authority['wheelhouse']['files'] and len(receipt['dependencies']) == 10


def test_process_outputs_and_diagnostics_are_exact_pairs():
    value = evidence(); receipt = value['receipt']; rows = {r['path']: r for r in value['archive']['files']}
    expected = {'result.json': dict(bytes=receipt['result_bytes'], sha256=receipt['result_sha256']),
                **receipt['diagnostics']}
    assert len(expected) == 4 and receipt['cycles_identical']
    for name, identity in expected.items():
        for cycle in ('cycle-1', 'cycle-2'):
            row = rows[cycle+'/'+name]
            assert row['bytes'] == identity['bytes'] and row['sha256'] == identity['sha256']


def test_no_scope_upgrade_and_complete_isolation_checks():
    value = evidence()
    assert value['scope'] == dict(production_qualified=False, release_authorized=False,
        independent_review='PENDING', source_mechanics_changed=False, defaults_changed=False,
        prestressed_high_contrast_qualified=False, resource_requests_consumed=0)
    assert value['checks'] == dict(installed_test_passed=True, bound_source_modules=65,
        isolated_processes=2, results_byte_identical=True, diagnostics_byte_identical=True,
        typed_state_replay_exact=True, loaded_states_rejected=True, tiny_positive_preserved=True,
        imports_isolated=True)
    assert not value['receipt']['production_qualified'] and not value['receipt']['release_authorized']


def test_strict_json_rejects_duplicates_and_nonfinite_values():
    for raw in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
        with pytest.raises(ValueError): json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)
