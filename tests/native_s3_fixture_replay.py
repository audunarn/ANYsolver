"""Test-side strict-first restore for frozen native/S3 fixture capsules.

The production replay contract stays byte-exact and fail-closed. This helper
only serves positive fixture consumers on platforms whose numerical libraries
recompute the three derived contact diagnostic estimates differently: it first
demands the unchanged strict production restore. Only a replay mismatch
isolated to those diagnostics - with every physical, history, mechanical,
target and contact binding field exact - is resealed once into a fresh local
capsule that the unchanged production restore must then accept byte-exactly.
Any other production refusal (binding, hash, chain, schema, noncanonical,
material or equilibrium) propagates unchanged, and a physical difference
raises and stays red.

This is bounded test setup for NativeMultiS3 fixtures only: no public
checkpoint migration or admission, and no change to any fixture file, solver
tolerance or stored digest.
"""
from hashlib import sha256
from math import isfinite
from pathlib import Path

from anysolver._ge_beam3_p5_seeded.codec import _load
from anysolver._ge_beam3_p5_seeded.core import canonical, sha
from anysolver.general_contact.native_multi_s3_static import NativeRetainedMultiS3Analysis
from anysolver.general_contact.native_replay_diagnostics import replay_difference_message

DIAGNOSTIC_KEYS = frozenset({'energy_error_j', 'force_error_n', 'tangent_error_n_per_m'})
_REPLAY_MISMATCH = 'multiple native/S3 checkpoint replay mismatch'
_RECORD_KEYS = {'target', 'previous_sha256', 'mechanical', 'histories',
                'shell_displacement', 'contact'}


def _fixture_payload(source):
    raw = source.read_bytes() if isinstance(source, Path) else bytes(source)
    # Existing CRLF-container rule only: a text-container checkout may
    # terminate the canonical payload's final newline as CRLF; drop only
    # that container carriage return. No-op on LF checkouts.
    return raw[:-2] + b'\n' if raw.endswith(b'\r\n') else raw


def _physical_contact(contact):
    physical = {key: value for key, value in contact.items() if key not in DIAGNOSTIC_KEYS}
    pairs = physical.get('pairs')
    if type(pairs) is list:
        physical['pairs'] = [
            {key: value for key, value in item.items() if key not in DIAGNOSTIC_KEYS}
            if type(item) is dict else item
            for item in pairs]
    return physical


def _physical_record(row):
    # Every stored field except the resealed chain link is compared exact.
    # Only the three diagnostic estimates are excluded, and only at the
    # contact root and at contact.pairs item locations.
    return {'target': row['target'], 'mechanical': row['mechanical'],
            'histories': row['histories'], 'shell_displacement': row['shell_displacement'],
            'contact': _physical_contact(row['contact'])}


def _validate_diagnostic_values(contact, where):
    # A stored diagnostic estimate must be a finite non-negative float;
    # anything else is a capsule schema fault, not platform numerical drift.
    locations = [contact]
    pairs = contact.get('pairs')
    if type(pairs) is list:
        locations.extend(item for item in pairs if type(item) is dict)
    for location in locations:
        for key in DIAGNOSTIC_KEYS:
            if key in location:
                value = location[key]
                if type(value) is not float or not isfinite(value) or value < 0.:
                    raise ValueError('native/S3 fixture diagnostic schema at %s: %s'
                                     % (where, key))


def _validate_original_chain(owner, capsule):
    previous = sha({'schema': owner.schema, 'identity': owner.identity})
    for index, row in enumerate(capsule['records'], 1):
        if row['target'] != index or row['previous_sha256'] != previous:
            raise ValueError('native/S3 fixture accepted chain mismatch at record %d' % index)
        previous = sha(row)


def restore_native_s3_fixture(owner, source, expected_sha256=None):
    """Return (accepted, records, payload) from a strict-first fixture restore.

    ``payload`` is the original bytes when they replay exactly, otherwise the
    once-resealed local capsule; the unchanged production restore accepted it
    and ``owner._checkpoint(records) == payload``. The fixture file itself is
    never written or changed.
    """
    if not isinstance(owner, NativeRetainedMultiS3Analysis):
        raise ValueError('native/S3 fixture helper requires a NativeMultiS3 owner')
    raw = _fixture_payload(source)
    if expected_sha256 is not None and sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('multiple native/S3 external checkpoint hash mismatch')
    try:
        accepted, records = owner._restore(raw, sha256(raw).hexdigest())
        return accepted, records, raw
    except ValueError as failure:
        if _REPLAY_MISMATCH not in str(failure):
            raise
    # Replay mismatch only: the refused capsule must itself be byte-canonical
    # with well-formed diagnostics, otherwise noncanonical whitespace plus
    # changed diagnostics would be silently accepted as drift. Then validate
    # the original accepted chain independently and recompute each record
    # once from the same mechanical state, shell displacement and origins.
    capsule = _load(raw.decode('ascii'))
    if owner._checkpoint(tuple(capsule['records'])) != raw:
        raise ValueError('native/S3 fixture capsule is not byte-canonical')
    for index, row in enumerate(capsule['records'], 1):
        _validate_diagnostic_values(row['contact'], 'record %d' % index)
    _validate_original_chain(owner, capsule)
    accepted = owner.initial
    replayed = ()
    previous = sha({'schema': owner.schema, 'identity': owner.identity})
    for index, row in enumerate(capsule['records'], 1):
        if set(row) != _RECORD_KEYS:
            raise ValueError('native/S3 fixture record schema')
        mechanical = owner.context.make(row['mechanical'], decoded=True)
        accepted, record = owner._record(index, mechanical, row['shell_displacement'],
                                         accepted.native_histories, previous)
        if canonical(_physical_record(row)) != canonical(_physical_record(record)):
            raise ValueError('native/S3 fixture physical replay mismatch'
                             + replay_difference_message(_physical_record(row),
                                                         _physical_record(record),
                                                         'record %d' % index))
        replayed += (record,)
        previous = sha(record)
    # The local chain is resealed only because diagnostics changed; require a
    # fresh strict production restore and an exact byte round trip of it.
    local = owner._checkpoint(replayed)
    accepted, records = owner._restore(local, sha256(local).hexdigest())
    if owner._checkpoint(records) != local:
        raise ValueError('native/S3 fixture local reseal is not byte-canonical')
    return accepted, records, local
