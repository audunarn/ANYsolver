"""Static relative-reference source and evidence preservation checks."""

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
    raw = (ROOT/'docs/reference_cases/ge_beam3_relative_reference_spectrum_evidence.json').read_text(encoding='utf-8')
    record = json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)
    assert json.dumps(record, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n' == raw
    return record


def test_source_and_baseline_bindings():
    record = evidence()
    assert record['baseline'] == dict(commit='6c4baab141d5479b8009e7a80a9ac457e9c05830',
        tree='99ab3437f7276a17c29be73f7ed44de16d1457f6')
    assert record['source_normalization'] == 'UTF8_LF' and len(record['sources']) == 8
    for row in record['sources']:
        path = (ROOT/row['path']).resolve(); assert path.is_relative_to(ROOT)
        raw = path.read_text(encoding='utf-8').encode('utf-8')
        assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
    assert record['driver'] == dict(name='DGEJSV', joba='G', jobu='U', jobv='J',
        jobr='N', jobt='N', jobp='N', automatic_fallback=False)


def test_exact_archive_and_repetition_inventory():
    archive = evidence()['archive']; rows = {r['path']: r for r in archive['files']}
    assert len(rows) == len(archive['files']) == archive['file_count'] == 20
    assert sum(r['bytes'] for r in rows.values()) == archive['bytes'] == 7414
    assert len(archive['identical_pairs']) == 10
    used = []
    for a, b in archive['identical_pairs']:
        assert a != b; used.extend((a, b))
        assert rows[a]['sha256'] == rows[b]['sha256'] and rows[a]['bytes'] == rows[b]['bytes']
    assert len(set(used)) == 20 and set(used) == set(rows)


def test_scope_and_separate_test_inventories():
    record = evidence()
    assert record['scope'] == dict(production_qualified=False, prestressed_tangent_authorized=False,
        independent_review='PENDING', previous_sources_changed=False, mechanics_changed=False,
        defaults_changed=False, full_slenderness_qualification=False, installed_wheel_checked=False,
        resource_requests_consumed=0)
    assert record['checks'] == dict(driver_tests=17, native_adapter_tests=10, relative_probe_tests=7,
        engineering_tests=2, preserved_reference_tests=26, preserved_loaded_modal_tests=23,
        preserved_prestress_engineering_tests=2, final_suite_passed=True, degenerate_pairs_passed=True,
        first_six_finest_frequencies_passed=True)


@pytest.mark.parametrize('raw', ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'])
def test_ambiguous_records_are_rejected(raw):
    with pytest.raises(ValueError): json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)
