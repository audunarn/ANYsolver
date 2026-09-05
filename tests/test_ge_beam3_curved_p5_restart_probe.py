"""Strict research restart checks; not production qualification."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from docs.reference_cases import ge_beam3_curved_p5_restart_probe as codec
from test_ge_beam3_curved_p5_history_path_probe import (
    NonlinearCantileverHistoryProbe, reference, law, forces, digest,
)


@pytest.fixture(scope='module')
def checkpoint():
    model = NonlinearCantileverHistoryProbe(reference(.4), law(), order=8)
    model.commit(model.trial(.1*forces()))
    return codec.dumps(model)


def restore(payload):
    return codec.loads(payload, reference(.4), law(), order=8)


def modified(payload, path, value, *, rehash=True):
    record = json.loads(payload)
    item = record
    for key in path[:-1]:
        item = item[key]
    item[path[-1]] = value
    if rehash:
        body = {key: value for key, value in record.items() if key != 'payload_sha256'}
        record['payload_sha256'] = hashlib.sha256(codec.canonical(body)).hexdigest()
    return codec.canonical(record)


def test_initial_and_plastic_roundtrip(checkpoint):
    initial = NonlinearCantileverHistoryProbe(reference(.4), law(), order=8)
    payload = codec.dumps(initial)
    assert codec.dumps(restore(payload)) == payload
    assert codec.dumps(restore(checkpoint)) == checkpoint
    assert restore(checkpoint).committed.epoch == 1


def test_default_48_station_restart():
    model = NonlinearCantileverHistoryProbe(reference(.4), law())
    model.commit(model.trial(.1*forces()))
    payload = codec.dumps(model)
    restored = codec.loads(payload, reference(.4), law())
    assert len(restored.committed.histories) == 48
    assert codec.dumps(restored) == payload


def test_rejected_import_does_not_mutate_existing_model(checkpoint):
    existing = restore(checkpoint)
    before = codec.dumps(existing)
    with pytest.raises(codec.RestartError):
        restore(modified(checkpoint, ['accepted','origins',0,'accumulated'], .1))
    assert codec.dumps(existing) == before


def test_restored_loading_unloading_reversal_matches_uninterrupted(checkpoint):
    original = NonlinearCantileverHistoryProbe(reference(.4), law(), order=8)
    original.commit(original.trial(.1*forces()))
    resumed = restore(checkpoint)
    for amplitude in (.2, .1, 0., -.1, 0.):
        first, second = original.trial(amplitude*forces()), resumed.trial(amplitude*forces())
        assert digest(first) == digest(second)
        original.commit(first)
        resumed.commit(second)
        assert digest(original.committed) == digest(resumed.committed)
        assert digest(original.replay()) == digest(resumed.replay())
        assert codec.dumps(original) == codec.dumps(resumed)


@pytest.mark.parametrize('mutation', [
    lambda p: p.rstrip(), lambda p: b' '+p,
    lambda p: b'\xef\xbb\xbf'+p, lambda p: b'\xff'+p,
    lambda p: p.replace(b'{', b'{"schema":null,', 1),
    lambda p: b'{"x":NaN}\n', lambda p: b'{"x":Infinity}\n',
    lambda p: b'{"x":1e400}\n', lambda p: b'['*33+b'0'+b']'*33,
    lambda p: b' '* (codec.MAX_BYTES+1), lambda p: b'',
])
def test_noncanonical_duplicate_nonfinite_and_resource_bounds(checkpoint, mutation):
    with pytest.raises(codec.RestartError):
        restore(mutation(checkpoint))


@pytest.mark.parametrize('path,value', [
    (['state','epoch'], True), (['state','epoch'], 1.0),
    (['state','positions',0,0], '-1.0'), (['state','positions',0,0], -1),
    (['state','positions'], []), (['state','histories'], []),
    (['state','unknown'], 0), (['unknown'], 0),
    (['state','histories',0,'accumulated'], -.1),
    (['accepted','response','stations',0,'response','plastic_active'], 1),
    (['accepted','mixed_evaluations'], 257),
    (['accepted','response','iterations'], 26),
])
def test_exact_schema_without_scalar_coercion(checkpoint, path, value):
    with pytest.raises(codec.RestartError):
        restore(modified(checkpoint, path, value))


@pytest.mark.parametrize('path,value', [
    (['state','epoch'], 3), (['accepted','origin_epoch'], 2),
    (['state','positions',2,0], 1.1), (['state','frames',2,0,0], .5),
    (['state','forces',2,0], .8),
    (['state','histories',0,'accumulated'], .9),
    (['accepted','origins',0,'accumulated'], .1),
    (['accepted','response','moments',0,0,0], .9),
    (['accepted','response','local_rotations',0,0,0], .5),
    (['accepted','response','tangent',0,0], 99.),
    (['accepted','response','residual',0], 99.),
    (['accepted','response','stations',0,'reference_coordinate'], -.9),
    (['accepted','response','stations',0,'index'], 1),
    (['accepted','response','stations',0,'response','resultants',0], 99.),
    (['accepted','response','stations',0,'response','strain',0], 99.),
    (['accepted','response','stations',0,'response','history','accumulated'], .9),
    (['accepted','residual_norm'], .1),
])
def test_rehashed_semantic_mutation_is_not_accepted(checkpoint, path, value):
    with pytest.raises(codec.RestartError):
        restore(modified(checkpoint, path, value))


def test_hash_mutation_and_identity_guard_precede_replay(checkpoint, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError('mismatched identity must not reach mechanics replay')
    monkeypatch.setattr(NonlinearCantileverHistoryProbe, '_reconstruct', forbidden)
    for payload in (
        modified(checkpoint, ['state','epoch'], 2, rehash=False),
        modified(checkpoint, ['identity','runtime','numpy'], 'other'),
        modified(checkpoint, ['identity','implementation_sources'], {}),
        modified(checkpoint, ['identity','candidate'], 'legacy-b3'),
        modified(checkpoint, ['identity','production_qualified'], True),
    ):
        with pytest.raises(codec.RestartError):
            restore(payload)
    for ref, section, order in ((reference(.5),law(),8), (reference(.4),law(.03),8),
                                (reference(.4),law(),24)):
        with pytest.raises(codec.RestartError):
            codec.loads(checkpoint, ref, section, order=order)


def test_pending_export_rejected_without_state_change(checkpoint):
    model = restore(checkpoint)
    before = digest(model.committed)
    trial = model.trial(.1*forces())
    with pytest.raises(codec.RestartError):
        codec.dumps(model)
    assert digest(model.committed) == before
    model.discard(trial)
    assert codec.dumps(model) == checkpoint


def test_import_replay_does_not_run_newton(checkpoint, monkeypatch):
    from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import NonlinearMixedBeamProbe
    def forbidden(*args, **kwargs):
        raise AssertionError('restart must not rerun Newton')
    monkeypatch.setattr(NonlinearMixedBeamProbe, 'solve', forbidden)
    assert codec.dumps(restore(checkpoint)) == checkpoint


def test_fresh_process_roundtrip(checkpoint):
    script = """
import sys
sys.path.insert(0, 'tests')
from test_ge_beam3_curved_p5_history_path_probe import reference, law
from docs.reference_cases.ge_beam3_curved_p5_restart_probe import loads, dumps
model = loads(sys.stdin.buffer.read(), reference(.4), law(), order=8)
sys.stdout.buffer.write(dumps(model))
"""
    result = subprocess.run([sys.executable, '-B', '-c', script], input=checkpoint,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            cwd=Path(__file__).resolve().parents[1], timeout=30, check=True)
    assert result.stdout == checkpoint


def test_exclusive_atomic_publication(checkpoint, tmp_path):
    path = tmp_path/'checkpoint.json'
    model = restore(checkpoint)
    assert codec.write_exclusive(path, model) == hashlib.sha256(checkpoint).hexdigest()
    assert path.read_bytes() == checkpoint
    with pytest.raises(FileExistsError):
        codec.write_exclusive(path, model)
    assert path.read_bytes() == checkpoint
    assert list(tmp_path.iterdir()) == [path]


def test_failed_publication_leaves_no_partial_output(checkpoint, tmp_path, monkeypatch):
    def fail_link(*args):
        raise OSError('simulated unavailable atomic hard-link publication')
    monkeypatch.setattr(os, 'link', fail_link)
    with pytest.raises(OSError, match='atomic'):
        codec.write_exclusive(tmp_path/'checkpoint.json', restore(checkpoint))
    assert list(tmp_path.iterdir()) == []
