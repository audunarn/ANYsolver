"""Static signed-spectrum development evidence bindings."""

from copy import deepcopy
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
    raw = (ROOT/'docs/reference_cases/ge_beam3_signed_spectrum_evidence.json').read_text(encoding='utf-8')
    record = json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)
    assert json.dumps(record, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n' == raw
    return record


def validate_sources(record):
    assert len(record['sources']) == 6 and record['source_normalization'] == 'UTF8_LF'
    for row in record['sources']:
        path = (ROOT/row['path']).resolve(); assert path.is_relative_to(ROOT)
        assert row['path'].startswith(('docs/reference_cases/', 'tests/'))
        raw = path.read_text(encoding='utf-8').encode('utf-8')
        assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']


def test_source_baseline_and_scope_bindings():
    record = evidence(); validate_sources(record)
    assert record['baseline'] == dict(commit='a2dbb114e4ecb6c2f45141b0b37e14188abf3231',
        tree='c2f265be51dbbef08f5d00dc762d72a326700597')
    assert record['scope'] == dict(production_qualified=False, independent_review='PENDING',
        source_mechanics_changed=False, defaults_changed=False, previous_sources_changed=False,
        certified_intervals=False, full_prestressed_modal_qualification=False,
        installed_wheel_checked=False, resource_requests_consumed=0, public_adapter_added=False)


def test_archive_inventory_and_identical_pairs():
    archive = evidence()['archive']; rows = {r['path']: r for r in archive['files']}
    assert len(rows) == len(archive['files']) == archive['file_count'] == 67
    assert sum(r['bytes'] for r in rows.values()) == archive['bytes'] == 835576
    assert len(archive['identical_pairs']) == 17
    used = []
    for a, b in archive['identical_pairs']:
        assert a.startswith('final/') and b == a.replace('final/', 'repeat/', 1)
        assert rows[a]['bytes'] == rows[b]['bytes'] and rows[a]['sha256'] == rows[b]['sha256']
        used.extend((a, b))
    assert len(set(used)) == 34
    assert rows['failed_scaling/failed-signed-spectrum-probe.py']['sha256'] == evidence()['incidents']['failed_scaling_source_sha256']


def test_separate_inventories_and_failure_disclosure():
    record = evidence()
    assert record['checks'] == dict(split_tests=5, signed_linear_algebra_tests=11,
        loaded_spectrum_tests=7, preserved_loaded_modal_tests=23, preserved_jacobi_driver_tests=17,
        final_suite_passed=True, repeat_new_suite_passed=True, finite_discrete_reference_passed=True,
        negative_modes_retained=True)
    incident = record['incidents']
    assert incident['scaling_test_failed_before_correction'] and incident['failed_scaling_test_count'] == 1
    assert incident['recovered_previous_test_transcript'] == 'UNAVAILABLE_NO_PASS_CLAIM'
    assert incident['recovered_previous_output_count'] == 3


def test_changed_source_identity_is_rejected():
    record = deepcopy(evidence()); record['sources'][0]['sha256'] = '0'*64
    with pytest.raises(AssertionError): validate_sources(record)


@pytest.mark.parametrize('raw', ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'])
def test_ambiguous_evidence_rejected(raw):
    with pytest.raises(ValueError): json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)
