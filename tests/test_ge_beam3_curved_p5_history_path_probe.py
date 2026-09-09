"""Global nonlinear history/atomicity research checks, not qualification."""

import numpy as np
import pytest

from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import (
    NonlinearCantileverHistoryProbe, HistoryPathError, HistoryTransactionError, digest,
)
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import NonlinearMixedBeamProbe
from test_ge_beam3_curved_p5_nonlinear_mixed_probe import reference, law


def forces():
    result = np.zeros((3, 3))
    result[-1] = [.1, -.3, .2]
    return result


@pytest.fixture(scope='module')
def cycle():
    ref = reference(.4)
    model = NonlinearCantileverHistoryProbe(ref, law(), order=8)
    results = []
    for amplitude in (.05, .1, .2, .1, 0., -.1, 0.):
        before = digest(model.committed)
        trial = model.trial(amplitude*forces())
        assert digest(model.committed) == before
        model.commit(trial)
        assert digest(model.replay()) == digest(trial.response)
        results.append(trial)
    return ref, model, results


def test_global_history_cycle_has_elastic_plastic_unloading_and_permanent_set(cycle):
    ref, model, results = cycle
    assert model.committed.epoch == 7
    active = [sum(s.response.plastic_active for s in r.response.stations) for r in results]
    assert active == [0, 16, 16, 0, 0, 16, 0]
    assert np.linalg.norm(results[-1].positions[-1]-ref.coordinates[-1]) > .02
    for previous, current in zip(results, results[1:]):
        expected = tuple(s.response.history for s in previous.response.stations)
        assert current.origins == expected
        assert all(new.response.history.accumulated >= old.accumulated
                   for new, old in zip(current.response.stations, expected))
    for trial in results:
        assert trial.residual_norm <= 1e-11
        assert trial.iterations <= 16 and trial.mixed_evaluations <= 256
        assert np.array_equal(trial.positions[0], ref.coordinates[0])
        assert np.array_equal(trial.frames[0], ref.nodal_triads[0])
        assert all(s.response.dissipation_increment >= 0 for s in trial.response.stations)


def test_global_force_and_current_geometry_moment_balance(cycle):
    _, _, results = cycle
    for trial in results:
        internal = trial.response.residual.reshape(3, 6)
        assert np.linalg.norm(internal[:, :3].sum(axis=0)) <= 1e-11
        assert np.linalg.norm((internal[:, 3:]+np.cross(trial.positions, internal[:, :3])).sum(axis=0)) <= 1e-11
        assert np.linalg.norm(internal[1:, :3]-trial.forces[1:]) <= 1e-11
        assert np.linalg.norm(internal[1:, 3:]) <= 1e-11


def test_default_all_48_stations_commit_and_replay():
    model = NonlinearCantileverHistoryProbe(reference(.4), law())
    result = model.trial(.1*forces())
    assert len(result.response.stations) == 48
    model.commit(result)
    assert len(model.committed.histories) == 48
    assert digest(model.replay()) == digest(result.response)


def test_discard_repeat_and_foreign_trials_do_not_change_history():
    model = NonlinearCantileverHistoryProbe(reference(.4), law(), order=8)
    other = NonlinearCantileverHistoryProbe(reference(.4), law(), order=8)
    before = digest(model.committed)
    first = model.trial(.1*forces())
    with pytest.raises(HistoryTransactionError):
        other.commit(first)
    model.discard(first)
    assert digest(model.committed) == before
    with pytest.raises(HistoryTransactionError):
        model.commit(first)
    repeated = model.trial(.1*forces())
    assert digest(repeated) == digest(first)
    model.commit(repeated)
    with pytest.raises(HistoryTransactionError):
        model.commit(repeated)


def test_late_station_commit_failure_is_atomic(monkeypatch):
    import docs.reference_cases.ge_beam3_curved_p5_history_path_probe as module
    model = NonlinearCantileverHistoryProbe(reference(.4), law(), order=8)
    first = model.trial(.1*forces())
    model.commit(first)
    before, accepted = digest(model.committed), digest(model.replay())
    next_trial = model.trial(.2*forces())
    original = module._history
    calls = []
    def fail_last(history):
        calls.append(1)
        if len(calls) == 16:
            raise ValueError('deliberate final station validation failure')
        return original(history)
    with monkeypatch.context() as context:
        context.setattr(module, '_history', fail_last)
        with pytest.raises(HistoryTransactionError, match='validation'):
            model.commit(next_trial)
    assert len(calls) == 16
    assert digest(model.committed) == before
    assert digest(model.replay()) == accepted


def test_commit_and_replay_reconstruct_without_rerunning_newton(monkeypatch):
    model = NonlinearCantileverHistoryProbe(reference(.4), law(), order=8)
    trial = model.trial(.1*forces())
    def forbidden(*args, **kwargs):
        raise AssertionError('Newton must not run during commit/replay')
    monkeypatch.setattr(NonlinearMixedBeamProbe, 'solve', forbidden)
    model.commit(trial)
    assert digest(model.replay()) == digest(trial.response)
    trial.positions.setflags(write=True)
    trial.positions[:] = 99.
    trial.response.tangent.setflags(write=True)
    trial.response.tangent[:] = 99.
    assert not np.any(model.committed.positions == 99.)
    assert not np.any(model.replay().tangent == 99.)


def test_mutated_final_station_and_stale_trials_are_rejected():
    model = NonlinearCantileverHistoryProbe(reference(.4), law(), order=8)
    before = digest(model.committed)
    trial = model.trial(.1*forces())
    last = trial.response.stations[-1].response
    last.resultants.setflags(write=True)
    last.resultants[0] += .1
    with pytest.raises(HistoryTransactionError, match='altered'):
        model.commit(trial)
    assert digest(model.committed) == before
    model.discard(trial)
    stale = model.trial(np.zeros((3, 3)))
    current = model.trial(np.zeros((3, 3)))
    with pytest.raises(HistoryTransactionError):
        model.commit(stale)
    model.commit(current)


def test_global_budget_and_invalid_input_preserve_geometry_histories_and_replay():
    model = NonlinearCantileverHistoryProbe(reference(.4), law(), order=8)
    accepted = model.trial(.1*forces())
    model.commit(accepted)
    before, replay = digest(model.committed), digest(model.replay())
    for kwargs in ({'max_iterations': 0}, {'max_mixed_evaluations': 0}, {'max_mixed_evaluations': 5}):
        with pytest.raises(HistoryPathError, match='budget'):
            model.trial(.2*forces(), **kwargs)
        assert digest(model.committed) == before
        assert digest(model.replay()) == replay
    pending = model.trial(.1*forces())
    with pytest.raises(ValueError):
        model.trial(np.full((3, 3), np.nan))
    with pytest.raises(HistoryTransactionError):
        model.commit(pending)
    for kwargs in ({'max_iterations': 17}, {'max_mixed_evaluations': 257}, {'max_iterations': True}):
        with pytest.raises(ValueError, match='bound'):
            model.trial(forces(), **kwargs)
    assert digest(model.committed) == before


def test_replay_does_not_use_the_new_committed_history_as_its_origin():
    model = NonlinearCantileverHistoryProbe(reference(.4), law(), order=8)
    accepted = model.trial(.1*forces())
    model.commit(accepted)
    replay = model.replay()
    assert all(s.response.plastic_active for s in replay.stations)
    fresh = NonlinearMixedBeamProbe(reference(.4), law(), order=8, origins=model.committed.histories)
    from_committed = fresh.evaluate(accepted.positions, accepted.frames,
                                   accepted.response.local_rotations, accepted.response.moments)
    assert all(s.response.origin == h for s, h in zip(from_committed.stations, model.committed.histories))
    assert replay.stations[0].response.origin != from_committed.stations[0].response.origin
    assert digest(model.replay()) == digest(accepted.response)
