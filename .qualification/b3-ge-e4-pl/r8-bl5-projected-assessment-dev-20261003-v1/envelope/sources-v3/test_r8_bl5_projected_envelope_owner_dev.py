"""Registration trust boundary, without invoking a native owner solve."""
import json
from pathlib import Path

import pytest

from scripts import r8_bl5_projected_envelope_owner_dev as owner
from scripts import r8_bl5_projected_envelope_norm_dev as norm


def record_pair(tmp_path, *, reference='original', legacy=False):
    case = norm.case_from_id('ns16_b1_8')
    source = Path(norm.__file__).resolve().parents[1]
    path = tmp_path/'registration.json'
    path.with_suffix('.npz').write_bytes(b'array binding only; no mechanical claim')
    record = dict(status='REGISTERED_ENVELOPE_DEVELOPMENT_BOUND',
        identity=norm.IDENTITY if reference == 'original' else norm.UNIFORM_IDENTITY,
        fixture_case=case.fixture_case, fixture=case.fixture, fixed_criteria=dict(norm.CRITERIA),
        source_sha256=norm.LEGACY_SOURCE_SHA256 if legacy else norm.sha(norm.__file__),
        helper_sha256=norm.helpers(case, reference=reference),
        arrays_sha256=norm.sha(path.with_suffix('.npz')),
        predicates=dict(physical_work=True), safe_case_floor=.4)
    if not legacy:
        record['reference_bound'] = reference
    path.write_text(json.dumps(record))
    return case, source, path, record


@pytest.mark.parametrize('reference,legacy', [('original', True), ('original', False), ('exact_uniform', False)])
def test_exact_versioned_registration_binding(tmp_path, reference, legacy):
    case, source, path, record = record_pair(tmp_path, reference=reference, legacy=legacy)
    actual, binding = owner.registration_identity(case, path, source)
    assert actual == record
    assert binding['source_sha256'] == record['source_sha256']


@pytest.mark.parametrize('key,value', [
    ('source_sha256', '0'*64), ('identity', 'unsupported'),
    ('predicates', {}), ('predicates', {'physical_work': 1}),
    ('predicates', {'physical_work': False}), ('safe_case_floor', 0.),
    ('safe_case_floor', float('nan')), ('safe_case_floor', float('inf')),
    ('helper_sha256', {}), ('arrays_sha256', '0'*64),
])
def test_reject_ineligible_or_stale_record(tmp_path, key, value):
    case, source, path, record = record_pair(tmp_path, legacy=True)
    record[key] = value
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        owner.registration_identity(case, path, source)


def test_uniform_record_cannot_claim_legacy_source(tmp_path):
    case, source, path, record = record_pair(tmp_path, reference='exact_uniform')
    record['source_sha256'] = norm.LEGACY_SOURCE_SHA256
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        owner.registration_identity(case, path, source)
