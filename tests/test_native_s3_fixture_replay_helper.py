"""Focused regression for the test-side native/S3 fixture restore helper.

The production replay gate stays strict: a synthetic diagnostic-only mismatch
is refused by the unchanged production restore, then accepted once locally
with every physical field exact. A one-ULP physical force or moment
difference, and binding, hash or accepted-chain failures, stay rejected.
Fixture files are never written.
"""
from hashlib import sha256
from pathlib import Path
import json

import numpy as np
import pytest

from anysolver._ge_beam3_p5_seeded.codec import _load
from native_s3_fixture_replay import DIAGNOSTIC_KEYS, restore_native_s3_fixture
from test_general_contact_native_curved_s3_static import _analysis

FIXTURE = Path(__file__).parent / 'data/general_contact_native_curved_s3_v2_active.checkpoint'


def _reseal(owner, raw, mutate):
    capsule = _load(raw.decode('ascii'))
    return owner._checkpoint(tuple(mutate(record) for record in capsule['records']))


def _bump(value):
    return float(np.nextafter(float(value), np.inf))


@pytest.fixture(scope='module')
def owner_and_payload():
    owner = _analysis()
    accepted, records, raw = restore_native_s3_fixture(owner, FIXTURE)
    assert accepted.completed_targets == 1 and owner._checkpoint(records) == raw
    return owner, raw


def test_diagnostic_only_mismatch_resealed_once_and_fixture_bytes_unchanged(owner_and_payload):
    owner, raw = owner_and_payload
    before = FIXTURE.read_bytes()

    def bump_diagnostic(record):
        contact = dict(record['contact'])
        for key in DIAGNOSTIC_KEYS:
            if key in contact:
                contact[key] = _bump(contact[key])
        contact['pairs'] = [dict(item) for item in contact['pairs']]
        for item in contact['pairs']:
            for key in DIAGNOSTIC_KEYS:
                if key in item:
                    item[key] = _bump(item[key])
        return {**record, 'contact': contact}

    mismatched = _reseal(owner, raw, bump_diagnostic)
    # The unchanged production restore strictly refuses the foreign diagnostics.
    with pytest.raises(ValueError, match='replay mismatch'):
        owner._restore(mismatched, sha256(mismatched).hexdigest())
    # One local reseal; the physical replay was exact, so the resealed capsule
    # reproduces the original canonical bytes.
    state, records, local = restore_native_s3_fixture(owner, mismatched)
    assert local == raw
    assert owner._checkpoint(records) == local
    assert state.completed_targets == 1
    assert FIXTURE.read_bytes() == before


@pytest.mark.parametrize('field', ('beam_force_n', 'beam_moment_nm'))
def test_physical_one_ulp_mismatch_stays_rejected(owner_and_payload, field):
    owner, raw = owner_and_payload

    def bump_physical(record):
        contact = dict(record['contact'])
        values = list(contact[field])
        values[0] = _bump(values[0])
        contact[field] = values
        return {**record, 'contact': contact}

    mismatched = _reseal(owner, raw, bump_physical)
    with pytest.raises(ValueError, match='replay mismatch'):
        owner._restore(mismatched, sha256(mismatched).hexdigest())
    with pytest.raises(ValueError, match='physical replay mismatch'):
        restore_native_s3_fixture(owner, mismatched)


def test_binding_hash_and_accepted_chain_failures_propagate(owner_and_payload):
    owner, raw = owner_and_payload
    with pytest.raises(ValueError, match='binding'):
        restore_native_s3_fixture(owner,
            _analysis(targets=(1.,), two_facets=True)._checkpoint(()))
    with pytest.raises(ValueError, match='hash mismatch'):
        restore_native_s3_fixture(owner, raw, expected_sha256='0' * 64)

    def break_chain(record):
        return {**record, 'previous_sha256': '0' * 64}

    with pytest.raises(ValueError, match='accepted chain'):
        restore_native_s3_fixture(owner, _reseal(owner, raw, break_chain))


def _damage_diagnostics(record, damage):
    contact = dict(record['contact'])
    for key in DIAGNOSTIC_KEYS:
        if key in contact:
            contact[key] = damage(contact[key])
    contact['pairs'] = [dict(item) for item in contact['pairs']]
    for item in contact['pairs']:
        for key in DIAGNOSTIC_KEYS:
            if key in item:
                item[key] = damage(item[key])
    return {**record, 'contact': contact}


def _bump_diagnostics(record):
    return _damage_diagnostics(record, _bump)


def test_noncanonical_capsule_with_diagnostic_mismatch_stays_rejected(owner_and_payload):
    owner, raw = owner_and_payload
    mismatched = _reseal(owner, raw, _bump_diagnostics)
    # The same parsed records under different bytes: whitespace
    # noncanonicality combined with changed diagnostics must be refused
    # outright rather than silently resealed as numerical drift. The strict
    # production restore refuses it; the helper gate is the second barrier.
    assert mismatched[:1] == b'{'
    spaced = mismatched[:1] + b' ' + mismatched[1:]
    with pytest.raises(ValueError,
                        match='noncanonical native checkpoint|not byte-canonical'):
        restore_native_s3_fixture(owner, spaced)


@pytest.mark.parametrize('bad', ('string', 'negative', 'nonfinite'))
def test_malformed_diagnostic_values_stay_rejected(owner_and_payload, bad):
    owner, raw = owner_and_payload

    def damage(value):
        if bad == 'string':
            return repr(float(value))
        if bad == 'negative':
            negative = -abs(float(value))
            return negative if negative < 0. else -1.0
        return float('nan')

    if bad == 'nonfinite':
        # A nonfinite estimate cannot exist inside a canonical capsule: the
        # strict serialization gates refuse it before any rebase is weighed
        # as numerical drift.
        capsule = _load(raw.decode('ascii'))
        for record in capsule['records']:
            record['contact'] = _damage_diagnostics(record, damage)['contact']
        malformed = json.dumps(capsule, separators=(',', ':'),
                               allow_nan=True).encode('ascii')
        with pytest.raises(ValueError,
                           match='nonfinite JSON constant|not JSON compliant'):
            restore_native_s3_fixture(owner, malformed)
        return
    mismatched = _reseal(owner, raw,
                         lambda record: _damage_diagnostics(record, damage))
    with pytest.raises(ValueError, match='diagnostic schema'):
        restore_native_s3_fixture(owner, mismatched)
