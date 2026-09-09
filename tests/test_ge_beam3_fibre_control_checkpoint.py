"""Static preservation of an unresolved development failure, not a waiver."""
import hashlib
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]


def record():
    def unique(pairs):
        value = {}
        for key, member in pairs:
            if key in value: raise ValueError('duplicate checkpoint key')
            value[key] = member
        return value
    def finite(value): raise ValueError('nonfinite checkpoint value')
    raw = (ROOT/'docs/reference_cases/ge_beam3_fibre_control_development_evidence.json').read_bytes().replace(b'\r\n', b'\n')
    value = json.loads(raw, object_pairs_hook=unique, parse_constant=finite)
    assert raw == (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode('ascii')
    return value


def test_required_failure_is_not_a_qualification_or_determinism_pass():
    value = record()
    assert value['status'] == 'DEVELOPMENT_HIGH_CONTRAST_CONTROL_UNRESOLVED'
    assert value['independent_review'] == 'PENDING'
    for key in ('qualification_pass', 'production_qualified', 'public_routing_changed', 'deterministic_cycle_pair_completed'):
        assert value[key] is False
    assert value['resource_requests_consumed'] == []
    assert [(r['tests'], r['failures'], r['errors']) for r in value['inventories']] == [(4, 1, 0), (4, 1, 0), (29, 0, 0), (33, 1, 0)]
    assert value['predictor_diagnostic']['accepted_targets'] == 0
    assert value['predictor_diagnostic']['minimum_chart_safe_halvings'] > value['predictor_diagnostic']['allowed_backtracks']
    assert len(value['incidents']) == 3 and len(value['arch_summary']) == 8


@pytest.mark.parametrize('index', [0, 1])
def test_latest_tested_source_hash_is_preserved(index):
    row = record()['sources'][index]
    raw = (ROOT/row['path']).read_bytes().replace(b'\r\n', b'\n')
    assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']


def test_high_contrast_test_has_not_been_skipped_or_reclassified():
    source = (ROOT/'tests/test_ge_beam3_retained_fibre_control.py').read_text()
    assert "@pytest.mark.parametrize('contrast', [1., 1.e12])" in source
    assert 'pytest.mark.xfail' not in source and 'pytest.mark.skip' not in source
    assert "assert whole.status == 'completed', whole.failure" in source
