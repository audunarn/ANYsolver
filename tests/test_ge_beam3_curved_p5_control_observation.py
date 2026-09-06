"""Small observation-only controller checks, never a 32-element solve."""

import copy
from dataclasses import asdict

import numpy as np
import pytest

from docs.reference_cases.ge_beam3_curved_p5_arch_refinement_case import make_beam
from docs.reference_cases.ge_beam3_curved_p5_displacement_control_probe import (
    DisplacementControlledAssemblyProbe, DisplacementControlError, ControlObservationError,
)
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
from docs.reference_cases.ge_beam3_curved_p5_refinement_wave import canonical


def driver():
    beam, _ = make_beam(2)
    return DisplacementControlledAssemblyProbe(beam, node=2)


def test_observations_preserve_trial_commit_and_replay_exactly():
    plain, observed = driver(), driver();events = []
    a = plain.trial(.095);b = observed.trial(.095, observer=events.append)
    assert canonical(asdict(a)) == canonical(asdict(b))
    plain.commit(a);observed.commit(b)
    assert digest(plain.committed_model.committed) == digest(observed.committed_model.committed)
    assert digest(observed.committed_model.replay()) == digest(a.assembly.response)
    assert [e['sequence'] for e in events] == list(range(len(events)))
    assert events[0]['phase'] == 'INITIALIZATION' and events[-1]['phase'] == 'CONVERGED'
    assert {'PREDICTOR', 'ITERATION', 'CORRECTION', 'CANDIDATE'} <= {e['phase'] for e in events}
    for event in events:
        assert set(event) == {'sequence', 'phase', 'iteration', 'backtrack', 'mixed_evaluations', 'metrics'}
        assert all(type(v) in (int, float, str, bool) for v in event['metrics'].values())
        if event['phase'] in ('ITERATION', 'CANDIDATE'):
            m = event['metrics']
            assert np.isclose(np.hypot(m['translation_residual'], m['rotation_residual']), m['residual'], rtol=1e-14, atol=0)
            assert 6 <= m['largest_residual_dof'] < 24
        if event['phase'] in ('PREDICTOR', 'CORRECTION'):
            assert event['metrics']['condition_2'] >= 1.
            assert event['metrics']['linear_residual'] < 1e-11


def test_observation_is_deterministic_and_mixed_budget_unchanged():
    first, second = [], []
    a = driver().trial(.095, observer=first.append)
    b = driver().trial(.095, observer=second.append)
    assert canonical(first) == canonical(second)
    assert a.assembly.mixed_evaluations == b.assembly.mixed_evaluations
    assert len(first) < 256


def test_failed_budget_retains_failure_event_and_no_state():
    control = driver();before = digest(control.committed_model.committed);events = []
    with pytest.raises(DisplacementControlError) as caught:
        control.trial(.095, max_mixed_evaluations=0, observer=events.append)
    assert events[-1]['phase'] == 'FAILURE'
    assert events[-1]['metrics']['error_type'] == 'AssemblyPathError'
    assert caught.value.evaluations == 0 and not caught.value.checkpoints
    assert control._pending is None and digest(control.committed_model.committed) == before


def test_failed_update_limit_retains_measured_iteration():
    control = driver();events = []
    with pytest.raises(DisplacementControlError) as caught:
        control.trial(.095, max_iterations=0, observer=events.append)
    assert caught.value.checkpoints
    iterations = [e for e in events if e['phase'] == 'ITERATION']
    assert len(iterations) == 1
    assert iterations[0]['metrics']['residual'] == caught.value.checkpoints[0].residual
    assert events[-1]['phase'] == 'FAILURE' and control._pending is None


@pytest.mark.parametrize('phase', ['INITIALIZATION', 'ITERATION', 'CONVERGED'])
def test_sink_failure_never_publishes_trial(phase):
    control = driver();before = digest(control.committed_model.committed)
    def broken(event):
        if event['phase'] == phase: raise OSError('unavailable output')
    with pytest.raises(ControlObservationError, match='sink failed'):
        control.trial(.095, observer=broken)
    assert control._pending is None and digest(control.committed_model.committed) == before


def test_mutating_event_cannot_mutate_solver_arrays_or_acceptance():
    reference = driver().trial(.095)
    def mutate(event):
        event['phase'] = 'FORGED'
        event['metrics']['residual'] = 0.
        event.clear()
    actual = driver().trial(.095, observer=mutate)
    assert digest(actual) == digest(reference)


def test_invalid_observer_is_rejected_before_evaluation():
    with pytest.raises(ValueError, match='observation sink'): driver().trial(.095, observer=1)


def test_local_candidate_rejection_is_observed_not_silenced(monkeypatch):
    from docs.reference_cases.ge_beam3_curved_p5_assembly_history_probe import NonlinearAssemblyHistoryProbe
    from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import NonlinearLocalError
    original = NonlinearAssemblyHistoryProbe._solve_all;calls = 0
    def reject_one(self, *args):
        nonlocal calls
        calls += 1
        if calls == 3: raise NonlinearLocalError('synthetic local rejection')
        return original(self, *args)
    monkeypatch.setattr(NonlinearAssemblyHistoryProbe, '_solve_all', reject_one)
    control = driver();events = [];trial = control.trial(.095, observer=events.append)
    rejected = [e for e in events if e['phase'] == 'CANDIDATE_REJECTED']
    assert len(rejected) == 1
    assert rejected[0]['metrics'] == {'error_type': 'NonlinearLocalError', 'error': 'synthetic local rejection'}
    assert events[-1]['phase'] == 'CONVERGED' and trial.assembly.residual_norm <= 1e-11
    control.discard(trial)
