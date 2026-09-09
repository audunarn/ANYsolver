"""Connected research restart integrity and continuation; not qualification."""

from copy import deepcopy
import hashlib
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_assembly_restart_probe as codec
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import NonlinearMixedBeamProbe
from test_ge_beam3_curved_p5_assembly_history_probe import model, forces, law, assembly, digest
from test_ge_beam3_curved_p5_restart_probe import modified


def restore(payload, expected=None, **overrides):
    expected = model() if expected is None else expected
    arguments = dict(fixed_nodes=expected._fixed.tolist(), order=expected._order, extent=expected._extent)
    arguments.update(overrides)
    return codec.loads(payload, expected._references, [r.tolist() for r in expected._maps], expected._sections, **arguments)


@pytest.fixture(scope='module')
def loaded():
    made = model()
    made.commit(made.trial(.1*forces()))
    return made


@pytest.fixture(scope='module')
def checkpoint(loaded):
    return codec.dumps(loaded)


def test_initial_and_committed_roundtrip(checkpoint):
    initial = codec.dumps(model())
    assert codec.dumps(restore(initial)) == initial
    restored = restore(checkpoint)
    assert restored.committed.epoch == 1
    assert codec.dumps(restored) == checkpoint
    assert len(restored.committed.histories) == 2
    assert all(len(h) == 16 for h in restored.committed.histories)


def test_continuation_load_unload_reverse_flow_and_permanent_set(checkpoint, loaded):
    uninterrupted = deepcopy(loaded)
    resumed = restore(checkpoint)
    active_reverse = 0
    for amplitude in (.2, .1, 0., -.2, 0.):
        a, b = uninterrupted.trial(amplitude*forces()), resumed.trial(amplitude*forces())
        assert digest(a) == digest(b)
        if amplitude == -.2:
            active_reverse = sum(s.response.plastic_active for e in a.response.elements for s in e.stations)
        uninterrupted.commit(a)
        resumed.commit(b)
        assert digest(uninterrupted.committed) == digest(resumed.committed)
        assert digest(uninterrupted.replay()) == digest(resumed.replay())
        payload = codec.dumps(resumed)
        assert codec.dumps(uninterrupted) == payload
        # Every continuation step starts from an independently validated load.
        resumed = restore(payload)
    assert active_reverse > 0
    assert np.linalg.norm(resumed.committed.positions[-1]-resumed._coordinates[-1]) > .01


@pytest.mark.parametrize('mutation', [
    lambda p: p.rstrip(), lambda p: b' '+p, lambda p: b'\xff'+p,
    lambda p: p.replace(b'{', b'{"schema":null,', 1),
    lambda p: b'{"x":NaN}\n', lambda p: b'{"x":Infinity}\n',
    lambda p: b'{"x":1e400}\n', lambda p: b'['*33+b'0'+b']'*33,
    lambda p: b' '*(codec.MAX_BYTES+1), lambda p: b'',
])
def test_strict_parser_limits(checkpoint, mutation):
    with pytest.raises(codec.RestartError):
        restore(mutation(checkpoint))


@pytest.mark.parametrize('path,value', [
    (['state','epoch'], True), (['state','epoch'], 1.0), (['state','epoch'], 3),
    (['state','unknown'], 0), (['unknown'], 0),
    (['state','positions',0,0], '-1.0'), (['state','positions'], []),
    (['state','histories'], []), (['state','histories',1], []),
    (['state','histories',1,15,'accumulated'], -.1),
    (['state','histories',1,15,'accumulated'], 99.),
    (['state','rotations',4,0,0], .5), (['state','forces',4,0], 2.),
    (['accepted','mixed_evaluations'], 513), (['accepted','iterations'], 17),
    (['accepted','origins',1,15,'accumulated'], .9),
    (['accepted','residual_norm'], .1),
    (['accepted','response','elements'], []),
    (['accepted','response','residual',0], 99.),
    (['accepted','response','tangent',0,0], 99.),
    (['accepted','response','elements',1,'local_rotations',0,0,0], .5),
    (['accepted','response','elements',1,'moments',0,0,0], 99.),
    (['accepted','response','elements',1,'iterations'], 26),
    (['accepted','response','elements',1,'stations',15,'index'], 0),
    (['accepted','response','elements',1,'stations',15,'reference_coordinate'], .9),
    (['accepted','response','elements',1,'stations',15,'response','plastic_active'], 1),
    (['accepted','response','elements',1,'stations',15,'response','strain',0], 99.),
    (['accepted','response','elements',1,'stations',15,'response','resultants',0], 99.),
])
def test_rehashed_schema_and_semantic_mutation(checkpoint, path, value):
    with pytest.raises(codec.RestartError):
        restore(modified(checkpoint, path, value))


def test_identity_and_hash_rejection_precede_replay(checkpoint, monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError('wrong identity reached mechanics replay')
    monkeypatch.setattr(assembly.NonlinearAssemblyHistoryProbe, '_validated', forbidden)
    for path, value in [
        (['identity','candidate'], 'legacy-b3'), (['identity','production_qualified'], True),
        (['identity','connectivity'], [[0,1,2],[2,4,3]]),
        (['identity','fixed_nodes'], [4]), (['identity','extent'], 'REFINEMENT16'),
        (['identity','references',1,'frames',0,0,0], .9),
        (['identity','sections',1,'yield_force'], .03),
        (['identity','runtime','numpy'], 'other'), (['identity','implementation_sources'], {}),
    ]:
        with pytest.raises(codec.RestartError):
            restore(modified(checkpoint,path,value))
    with pytest.raises(codec.RestartError):
        restore(modified(checkpoint,['state','epoch'],2,rehash=False))
    for kw in ({'order':24}, {'fixed_nodes':(4,)}, {'extent':'REFINEMENT16'}):
        with pytest.raises(codec.RestartError):
            restore(checkpoint, **kw)


def test_late_element_failure_exposes_no_model_or_mutation(checkpoint, loaded, monkeypatch):
    before = tuple(digest(item) for item in loaded._checkpoint)
    reconstruct = assembly.NonlinearAssemblyHistoryProbe._reconstruct_element
    visited = []
    def fail_last(self, index, trial):
        visited.append(index)
        if index == 1:
            raise ValueError('late staged failure')
        return reconstruct(self,index,trial)
    monkeypatch.setattr(assembly.NonlinearAssemblyHistoryProbe,'_reconstruct_element',fail_last)
    with pytest.raises(codec.RestartError):
        restore(checkpoint, loaded)
    assert visited == [0,1]
    assert tuple(digest(item) for item in loaded._checkpoint) == before


def test_pending_export_rejected_and_defensive_state(checkpoint):
    made = restore(checkpoint)
    before = digest(made.committed)
    trial = made.trial(.1*forces())
    with pytest.raises(codec.RestartError):
        codec.dumps(made)
    assert digest(made.committed) == before
    made.discard(trial)
    copied = made.committed
    copied.positions.setflags(write=True)
    copied.positions[-1] = 100.
    assert codec.dumps(made) == checkpoint


def test_newton_free_restore(checkpoint, monkeypatch):
    def forbidden(*a, **k):
        raise AssertionError('restart must not solve Newton')
    monkeypatch.setattr(NonlinearMixedBeamProbe,'solve',forbidden)
    monkeypatch.setattr(assembly.NonlinearAssemblyHistoryProbe,'trial',forbidden)
    assert codec.dumps(restore(checkpoint)) == checkpoint


def test_default_quadrature_and_heterogeneous_sections():
    made = model(order=24, laws=[law(.02),law(.04)])
    made.commit(made.trial(.1*forces()))
    payload = codec.dumps(made)
    resumed = restore(payload,made)
    assert codec.dumps(resumed) == payload
    assert [len(h) for h in resumed.committed.histories] == [48,48]


def test_initial_refinement_extent_not_implicitly_reduced():
    from docs.reference_cases.ge_beam3_curved_p5_refinement_wave import refined_references
    refs = refined_references(np)
    made = assembly.NonlinearAssemblyHistoryProbe(refs,[(2*i,2*i+1,2*i+2) for i in range(16)],
        [law() for _ in refs],order=8,extent='REFINEMENT16')
    payload = codec.dumps(made)
    assert codec.dumps(restore(payload,made)) == payload
    assert restore(payload,made)._extent == 'REFINEMENT16'


def test_nonzero_clamp_and_reordered_material_frames():
    from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import T6
    from docs.reference_cases.ge_beam3_curved_p5_section_probe import DirectedHardeningSectionProbe
    original = model()
    refs = list(original._references)
    refs[1] = refs[1].reversed()
    s = original._sections[1]
    sections = [original._sections[0],DirectedHardeningSectionProbe(
        T6 @ s._elastic @ T6.T,T6 @ s._direction,s._yield,s._hardening)]
    made = assembly.NonlinearAssemblyHistoryProbe(refs,[(0,1,2),(4,3,2)],sections,
        fixed_nodes=(4,),order=8)
    load = np.zeros((5,3));load[0] = [.01,-.02,.01]
    made.commit(made.trial(load))
    payload = codec.dumps(made)
    resumed = restore(payload,made)
    assert codec.dumps(resumed) == payload
    a,b = made.trial(np.zeros((5,3))),resumed.trial(np.zeros((5,3)))
    assert digest(a) == digest(b)


def test_private_checkpoint_corruption_cannot_be_exported(checkpoint):
    from dataclasses import replace
    made = restore(checkpoint)
    state,accepted = made._checkpoint
    made._checkpoint = (replace(state,epoch=state.epoch+1),accepted)
    before = tuple(digest(item) for item in made._checkpoint)
    with pytest.raises(codec.RestartError):
        codec.dumps(made)
    assert tuple(digest(item) for item in made._checkpoint) == before


def test_rehashed_consistent_but_nonorthogonal_shared_rotations_rejected(checkpoint):
    payload = modified(checkpoint,['state','rotations',4,0,0],.5)
    payload = modified(payload,['accepted','rotations',4,0,0],.5)
    with pytest.raises(codec.RestartError):
        restore(payload)


def test_signed_zero_state_must_match_accepted_bytes(checkpoint):
    with pytest.raises(codec.RestartError):
        restore(modified(checkpoint,['state','forces',0,0],-0.0))


def test_nonfinite_private_export_is_typed_and_unpublished(checkpoint,tmp_path):
    from dataclasses import replace
    made = restore(checkpoint)
    state,accepted = made._checkpoint
    bad = state.forces.copy();bad[0,0] = float('nan')
    made._checkpoint = (replace(state,forces=bad),accepted)
    with pytest.raises(codec.RestartError):
        codec.write_exclusive(tmp_path/'absent.json',made)
    assert list(tmp_path.iterdir()) == []


def test_cross_schema_rejected(checkpoint):
    from test_ge_beam3_curved_p5_history_path_probe import reference
    with pytest.raises(codec.RestartError):
        codec.single.loads(checkpoint,reference(.4),law(),order=8)
    one = codec.single.NonlinearCantileverHistoryProbe(reference(.4),law(),order=8)
    with pytest.raises(codec.RestartError):
        restore(codec.single.dumps(one))


def test_fresh_process_roundtrip(checkpoint):
    script = """
import sys
sys.path.insert(0,'tests')
from test_ge_beam3_curved_p5_assembly_restart_probe import restore,codec
sys.stdout.buffer.write(codec.dumps(restore(sys.stdin.buffer.read())))
"""
    completed = subprocess.run([sys.executable,'-B','-c',script],input=checkpoint,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,check=True,
        cwd=Path(__file__).resolve().parents[1])
    assert completed.stdout == checkpoint


def test_exclusive_publication_and_failed_staging(checkpoint,tmp_path,monkeypatch):
    made = restore(checkpoint)
    target = tmp_path/'checkpoint.json'
    assert codec.write_exclusive(target,made) == hashlib.sha256(checkpoint).hexdigest()
    assert target.read_bytes() == checkpoint
    with pytest.raises(FileExistsError):
        codec.write_exclusive(target,made)
    assert list(tmp_path.iterdir()) == [target]
    def fail(*args):
        raise OSError('publication unsupported')
    monkeypatch.setattr(os,'link',fail)
    with pytest.raises(OSError):
        codec.write_exclusive(tmp_path/'absent.json',made)
    assert list(tmp_path.iterdir()) == [target]
    assert target.read_bytes() == checkpoint
