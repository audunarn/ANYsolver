"""Registration trust boundary, without invoking a native owner solve."""
import json
from pathlib import Path

import pytest

from scripts import r8_bl5_projected_envelope_owner_dev as owner
from scripts import r8_bl5_projected_envelope_norm_dev as norm


def _current_helper_hashes():
    directory = Path(norm.__file__).resolve().parent
    return {name: norm.sha(directory/name) for name in norm.EXPECTED_HELPERS}


def _helper_identity_drift():
    """Frozen v1 preparation identity vs current helper bytes."""
    current = _current_helper_hashes()
    return {name: (frozen, current[name]) for name, frozen in norm.EXPECTED_HELPERS.items()
        if current[name] != frozen}


_HELPER_DRIFT = _helper_identity_drift()
# The exact historical registration binding requires the original helper
# bytes recorded in the frozen EXPECTED_HELPERS identity. When production
# helpers have drifted, that historical fixture is absent: skip only this
# evidence-dependent binding and report the concrete delta; never rebind
# the frozen identity here.
_skip_drifted_helper_identity = pytest.mark.skipif(
    bool(_HELPER_DRIFT),
    reason='frozen v1 scalar preparation identity requires the original '
        'helper bytes; drifted from EXPECTED_HELPERS: '
        + '; '.join(f'{name} {frozen} -> {current}'
                    for name, (frozen, current) in sorted(_HELPER_DRIFT.items()))
        + ' (prospective amendment reported to root; not adopted in this slice)')


def _bind_current_helpers(monkeypatch):
    """Synthetic current compatible helper binding for unit/mutation controls.

    The frozen source identity is untouched; rejection logic is exercised
    against the current helper bytes so the controls stay portable whether
    or not the exact historical fixture is present.
    """
    monkeypatch.setattr(norm, 'EXPECTED_HELPERS', _current_helper_hashes())


def record_pair(tmp_path, *, reference='original', legacy=False):
    case = norm.case_from_id('ns16_b1_8')
    source = Path(norm.__file__).resolve().parents[1]
    path = tmp_path/'registration.json'
    path.with_suffix('.npz').write_bytes(b'array binding only; no mechanical claim')
    record = dict(status='REGISTERED_ENVELOPE_DEVELOPMENT_BOUND',
        identity=norm.IDENTITY if reference == 'original' else norm.UNIFORM_IDENTITY,
        fixture_case=case.fixture_case, fixture=case.fixture, fixed_criteria=dict(norm.CRITERIA),
        coordinate_norm=dict(length_m=float(norm.LENGTH), width_m=float(norm.WIDTH), ell_m=float(norm.ELL)),
        counts=case.counts, fixed_count=case.fixed_count, supported_kkt_count=case.supported_kkt_count,
        source_sha256=norm.LEGACY_SOURCE_SHA256 if legacy else norm.sha(norm.__file__),
        helper_sha256=norm.helpers(case, reference=reference),
        arrays_sha256=norm.sha(path.with_suffix('.npz')),
        predicates=dict(physical_work=True), safe_case_floor=.4)
    if not legacy:
        record['reference_bound'] = reference
    path.write_text(json.dumps(record))
    return case, source, path, record


@pytest.mark.parametrize('reference,legacy', [('original', True), ('original', False), ('exact_uniform', False)])
@_skip_drifted_helper_identity
def test_exact_versioned_registration_binding(tmp_path, reference, legacy):
    case, source, path, record = record_pair(tmp_path, reference=reference, legacy=legacy)
    actual, binding = owner.registration_identity(case, path, source)
    assert actual == record
    assert binding['source_sha256'] == record['source_sha256']


@pytest.mark.parametrize('reference,legacy', [('original', True), ('original', False), ('exact_uniform', False)])
def test_current_helper_registration_positive_control(tmp_path, monkeypatch, reference, legacy):
    """Synthetic current-helper positive baseline; runs before any mutation control.

    With the helper identity bound to the current helper bytes, an otherwise
    exact record must be accepted for every admitted reference/legacy
    combination. Mutations below are meaningful only once this succeeds.
    """
    _bind_current_helpers(monkeypatch)
    case, source, path, record = record_pair(tmp_path, reference=reference, legacy=legacy)
    actual, binding = owner.registration_identity(case, path, source)
    assert actual == record
    assert binding['source_sha256'] == record['source_sha256']
    assert binding['helper_sha256'] == record['helper_sha256']


@pytest.mark.skipif(not _HELPER_DRIFT,
    reason='current helper bytes match the frozen EXPECTED_HELPERS identity; '
        'the exact historical binding test covers the unpatched positive path')
def test_unpatched_frozen_helper_drift_refuses(tmp_path, monkeypatch):
    """The unpatched frozen identity must refuse drifted helper bytes.

    The record is built under the synthetic current binding only so the
    fixture exists; the gate itself then runs with the real frozen
    EXPECTED_HELPERS and must raise rather than silently rebind.
    """
    with monkeypatch.context() as patch:
        _bind_current_helpers(patch)
        case, source, path, record = record_pair(tmp_path)
    with pytest.raises(ValueError, match='scalar preparation helper identity changed'):
        owner.registration_identity(case, path, source)


@pytest.mark.parametrize('key,value', [
    ('source_sha256', '0'*64), ('identity', 'unsupported'),
    ('predicates', {}), ('predicates', {'physical_work': 1}),
    ('predicates', {'physical_work': False}), ('safe_case_floor', 0.),
    ('safe_case_floor', float('nan')), ('safe_case_floor', float('inf')),
    ('helper_sha256', {}), ('arrays_sha256', '0'*64),
    ('coordinate_norm', {'length_m': 1., 'width_m': .2, 'ell_m': .5}),
    ('counts', {}), ('fixed_count', 0), ('supported_kkt_count', 1),
])
def test_reject_ineligible_or_stale_record(tmp_path, monkeypatch, key, value):
    _bind_current_helpers(monkeypatch)
    case, source, path, record = record_pair(tmp_path, legacy=True)
    record[key] = value
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        owner.registration_identity(case, path, source)


def test_uniform_record_cannot_claim_legacy_source(tmp_path, monkeypatch):
    _bind_current_helpers(monkeypatch)
    case, source, path, record = record_pair(tmp_path, reference='exact_uniform')
    record['source_sha256'] = norm.LEGACY_SOURCE_SHA256
    path.write_text(json.dumps(record))
    with pytest.raises(ValueError):
        owner.registration_identity(case, path, source)


def test_legacy_reuse_rejects_any_unreviewed_current_norm_source(tmp_path, monkeypatch):
    _bind_current_helpers(monkeypatch)
    case, source, path, record = record_pair(tmp_path, legacy=True)
    original_sha = owner.common.sha
    def changed_sha(filename):
        if Path(filename).name == 'r8_bl5_projected_envelope_norm_dev.py':
            return 'f'*64
        return original_sha(filename)
    monkeypatch.setattr(owner.common, 'sha', changed_sha)
    with pytest.raises(ValueError):
        owner.registration_identity(case, path, source)
