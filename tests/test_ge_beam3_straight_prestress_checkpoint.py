"""Static development-record checks; do not rerun mechanics or require archives."""

import hashlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT/'docs/reference_cases/ge_beam3_straight_prestress_development_evidence.json'


def pairs(items):
    result = {}
    for key, value in items:
        if key in result: raise ValueError('duplicate key')
        result[key] = value
    return result


def reject(value):
    raise ValueError('nonfinite value')


def read():
    raw = RECORD.read_text(encoding='utf-8')
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)
    assert json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n' == raw
    return value


def test_development_record_and_source_bindings():
    value = read()
    assert set(value) == {'schema', 'baseline', 'source_normalization', 'sources', 'archive', 'checks', 'scope'}
    assert value['schema'] == 'GE_BEAM3_STRAIGHT_PRESTRESS_DEVELOPMENT_V1'
    assert value['baseline'] == dict(commit='f29fb7fce7a8aab3f44ba722e7356087778b319b',
        tree='400c91fc1354e05daa423b319df44fc069e5fcdb')
    assert value['source_normalization'] == 'UTF8_LF'
    assert len(value['sources']) == 3
    for row in value['sources']:
        path = (ROOT/row['path']).resolve()
        assert path.is_relative_to(ROOT) and path.is_file()
        raw = path.read_text(encoding='utf-8').encode('utf-8')
        assert len(raw) == row['bytes']
        assert hashlib.sha256(raw).hexdigest() == row['sha256']


def test_archive_manifest_has_exact_repeated_cases():
    value = read(); archive = value['archive']; rows = archive['files']
    assert len(rows) == archive['file_count'] == 20
    assert sum(r['bytes'] for r in rows) == archive['bytes'] == 578310
    expected = {f'{count}-{ratio}-{kind}.json' for count, ratio in
        ((2, '0.0'), (4, '0.0'), (4, '0.5'), (4, '0.98'), (4, '1.02'))
        for kind in ('state', 'comparison')}
    assert len({r['path'] for r in rows}) == 20
    for name in expected:
        left = next(r for r in rows if r['path'] == 'run-1/'+name)
        right = next(r for r in rows if r['path'] == 'run-2/'+name)
        assert left['bytes'] == right['bytes'] and left['bytes'] > 0
        assert left['sha256'] == right['sha256'] and len(left['sha256']) == 64
        assert set(left['sha256']) <= set('0123456789abcdef')


def test_no_scope_upgrade_or_hidden_qualification_claim():
    value = read()
    assert value['scope'] == dict(production_qualified=False, buckling_factor_authorized=False,
        independent_review='PENDING', curved_engineering_qualification=False,
        full_spectrum_accuracy_qualified=False, source_mechanics_changed=False,
        defaults_changed=False, resource_requests_consumed=0)
    assert value['checks'] == dict(continuum_tests=20, native_engineering_tests=2,
        existing_loaded_modal_tests=23, all_passed=True, native_repetitions=2,
        case_count_per_repetition=5, byte_identical_comparisons=True,
        byte_identical_accepted_checkpoints=True, complete_spatial_equilibrium_checked=True,
        history_unchanged=True)


@pytest.mark.parametrize('raw', ['{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'])
def test_strict_parser_rejects_ambiguous_records(raw):
    with pytest.raises(ValueError): json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)
