"""Bounded elastic global equilibrium and state-safety development tests."""

import numpy as np
import pytest

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation, log_rotation
from docs.reference_cases.ge_beam3_curved_p5_finite_path_probe import (
    FiniteCantileverPathProbe, FinitePathError, TransactionError,
)
from docs.reference_cases.ge_beam3_curved_p5_retained_response_probe import RetainedFiniteResponseProbe
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import CurvedFiniteProbe, LocalStationarityError
from test_ge_beam3_curved_p5_algebra_probe import reference, section


def loads():
    force = np.zeros((3, 3))
    force[-1] = [.1, -.3, .2]
    return force


def assert_state_equal(a, b):
    assert a.epoch == b.epoch
    for name in ('positions', 'vertex_frames', 'forces'):
        assert np.array_equal(getattr(a, name), getattr(b, name))


@pytest.fixture(scope='module')
def loaded_cycle():
    ref = reference(.4)
    model = FiniteCantileverPathProbe(ref, section())
    results = []
    for amplitude in (.1, .5, 1., .5, 0., -.5, 0.):
        before = model.committed
        trial = model.trial(amplitude*loads())
        assert_state_equal(before, model.committed)
        model.commit(trial)
        results.append(trial)
    return ref, model, results


def test_finite_load_unload_and_reversal_return_to_stress_free_state(loaded_cycle):
    ref, model, results = loaded_cycle
    assert model.committed.epoch == 7
    assert np.linalg.norm(results[2].positions[-1]-ref.coordinates[-1]) > .5
    assert np.linalg.norm(results[1].positions-results[3].positions) <= 1e-11
    assert np.linalg.norm(results[1].vertex_frames-results[3].vertex_frames) <= 1e-11
    for index in (4, 6):
        assert np.linalg.norm(results[index].positions-ref.coordinates) <= 1e-11
        assert np.linalg.norm(results[index].vertex_frames-ref.nodal_triads) <= 1e-11
        assert abs(results[index].potential) <= 1e-22
    for trial in results:
        assert trial.residual_norm <= 1e-11
        assert trial.iterations <= 16 and trial.evaluations <= 48
        assert np.array_equal(trial.positions[0], ref.coordinates[0])
        assert np.array_equal(trial.vertex_frames[0], ref.nodal_triads[0])


def test_current_geometry_force_moment_balance_and_rotation_integrity(loaded_cycle):
    _, _, results = loaded_cycle
    for trial in results:
        total_force = trial.reactions[:, :3]+trial.forces
        assert np.linalg.norm(total_force.sum(axis=0)) <= 1e-11
        assert np.linalg.norm((trial.reactions[:, 3:]+np.cross(trial.positions, total_force)).sum(axis=0)) <= 1e-11
        for frame in trial.vertex_frames:
            assert np.linalg.norm(frame.T @ frame-np.eye(3)) <= 1e-11
            assert abs(np.linalg.det(frame)-1) <= 1e-11


def test_converged_global_state_matches_original_local_scalar_potential(loaded_cycle):
    ref, _, results = loaded_cycle
    trial = results[2]
    original = CurvedFiniteProbe(ref, section()).evaluate(trial.positions, trial.vertex_frames)
    assert abs(original.potential-trial.potential) <= 1e-11
    assert np.linalg.norm(original.local_rotations-trial.local_rotations) <= 1e-11


def test_superposed_reference_and_load_rotation_preserves_loaded_response(loaded_cycle):
    ref, _, results = loaded_cycle
    g = rotation([2.1, -1.8, 2.5])
    shift = np.array([2., -4., 7.])
    moved_ref = ref.rigidly_transformed(g, shift)
    moved = FiniteCantileverPathProbe(moved_ref, section()).trial(loads() @ g.T)
    baseline = results[2]
    assert np.linalg.norm(moved.positions-(baseline.positions @ g.T+shift)) <= 1e-11
    assert np.linalg.norm(moved.vertex_frames-np.einsum('ij,njk->nik', g, baseline.vertex_frames)) <= 1e-11
    assert abs(moved.potential-baseline.potential) <= 1e-11
    assert np.linalg.norm(moved.reactions[:, :3]-baseline.reactions[:, :3] @ g.T) <= 1e-11
    assert np.linalg.norm(moved.reactions[:, 3:]-baseline.reactions[:, 3:] @ g.T) <= 1e-11


def test_loaded_tangent_and_virtual_work_match_load_directional_difference():
    ref = reference(.4)
    model = FiniteCantileverPathProbe(ref, section())
    base = model.trial(.5*loads())
    model.commit(base)
    local = RetainedFiniteResponseProbe(ref, section(), base.positions, base.vertex_frames).evaluate()
    force_direction = np.zeros((3, 6))
    force_direction[:, :3] = loads()
    predicted = np.zeros(18)
    predicted[6:] = np.linalg.solve(local.tangent[6:, 6:], force_direction.ravel()[6:])
    step = 2e-5
    plus = model.trial((.5+step)*loads())
    minus = model.trial((.5-step)*loads())
    difference = np.zeros((3, 6))
    difference[:, :3] = (plus.positions-minus.positions)/(2*step)
    for i in range(3):
        difference[i, 3:] = (log_rotation(plus.vertex_frames[i] @ base.vertex_frames[i].T)
                             -log_rotation(minus.vertex_frames[i] @ base.vertex_frames[i].T))/(2*step)
    assert np.linalg.norm(difference.ravel()-predicted) <= 1e-7*max(1., np.linalg.norm(predicted))
    work = np.sum(base.forces*difference[:, :3])
    assert abs((plus.potential-minus.potential)/(2*step)-work) <= 1e-7*max(1., abs(work))
    assert np.linalg.norm(local.tangent-local.tangent.T) <= 1e-11*np.linalg.norm(local.tangent)


def test_discard_stale_foreign_and_repeated_commit_are_rejected():
    model = FiniteCantileverPathProbe(reference(.4), section())
    other = FiniteCantileverPathProbe(reference(.4), section())
    zero = np.zeros((3, 3))
    first = model.trial(zero)
    with pytest.raises(TransactionError):
        other.commit(first)
    model.discard(first)
    with pytest.raises(TransactionError):
        model.commit(first)
    stale = model.trial(zero)
    current = model.trial(zero)
    with pytest.raises(TransactionError):
        model.commit(stale)
    model.commit(current)
    with pytest.raises(TransactionError):
        model.commit(current)
    with pytest.raises(TransactionError):
        model.commit(None)


@pytest.mark.parametrize('field', ['positions', 'vertex_frames', 'forces', 'reactions', 'local_rotations'])
def test_altered_trial_cannot_be_committed(field):
    model = FiniteCantileverPathProbe(reference(.4), section())
    before = model.committed
    trial = model.trial(np.zeros((3, 3)))
    array = getattr(trial, field)
    assert not array.flags.writeable
    array.setflags(write=True)
    array.flat[0] += .01
    with pytest.raises(TransactionError, match='altered'):
        model.commit(trial)
    assert_state_equal(before, model.committed)
    model.discard(trial)


def test_copied_state_and_inputs_cannot_mutate_committed_data():
    elastic = section()
    model = FiniteCantileverPathProbe(reference(.4), elastic)
    baseline = model.committed
    copy = model.committed
    copy.positions.setflags(write=True)
    copy.positions[:] = 99.
    elastic[:] = 0.
    assert_state_equal(model.committed, baseline)
    force = .1*loads()
    trial = model.trial(force)
    force[:] = 99.
    assert np.array_equal(trial.forces, .1*loads())


def test_budget_failure_invalidates_pending_trial_but_preserves_commit():
    model = FiniteCantileverPathProbe(reference(.4), section())
    first = model.trial(.1*loads())
    model.commit(first)
    before = model.committed
    for kwargs in ({'max_iterations': 0}, {'max_evaluations': 0}, {'max_evaluations': 1}):
        pending = model.trial(.1*loads())
        with pytest.raises(FinitePathError, match='budget'):
            model.trial(loads(), **kwargs)
        assert_state_equal(before, model.committed)
        with pytest.raises(TransactionError):
            model.commit(pending)


def test_local_failure_is_not_committed_or_retried(monkeypatch):
    model = FiniteCantileverPathProbe(reference(.4), section())
    before = model.committed
    calls = []
    def failed(*args, **kwargs):
        calls.append(1)
        raise LocalStationarityError('deliberate failure')
    monkeypatch.setattr(RetainedFiniteResponseProbe, 'evaluate', failed)
    with pytest.raises(FinitePathError, match='initial local'):
        model.trial(loads())
    assert len(calls) == 1
    assert_state_equal(before, model.committed)


def test_failed_local_line_search_trials_consume_global_budget(monkeypatch):
    model = FiniteCantileverPathProbe(reference(.4), section())
    before = model.committed
    original = RetainedFiniteResponseProbe.evaluate
    calls = []
    def fail_after_one_update(self, *args, **kwargs):
        calls.append(1)
        if len(calls) > 2:
            raise LocalStationarityError('deliberate later failure')
        return original(self, *args, **kwargs)
    monkeypatch.setattr(RetainedFiniteResponseProbe, 'evaluate', fail_after_one_update)
    with pytest.raises(FinitePathError, match='evaluation budget'):
        model.trial(loads(), max_evaluations=4)
    assert len(calls) == 4
    assert_state_equal(before, model.committed)


def test_same_initial_state_repeats_byte_identically():
    from docs.reference_cases.ge_beam3_curved_p5_finite_path_probe import _trial_digest
    first = FiniteCantileverPathProbe(reference(.4), section()).trial(loads())
    second = FiniteCantileverPathProbe(reference(.4), section()).trial(loads())
    assert _trial_digest(first) == _trial_digest(second)


def test_unsupported_loads_and_invalid_budgets_are_rejected():
    model = FiniteCantileverPathProbe(reference(.4), section())
    for force in (np.zeros((3, 6)), np.zeros(18), np.full((3, 3), np.nan)):
        with pytest.raises(ValueError, match='spatial dead'):
            model.trial(force)
    for kwargs in ({'max_iterations': 17}, {'max_iterations': True},
                   {'max_evaluations': 49}, {'max_evaluations': -1}):
        with pytest.raises(ValueError, match='limit'):
            model.trial(loads(), **kwargs)
