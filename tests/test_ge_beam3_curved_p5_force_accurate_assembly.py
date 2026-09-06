"""Small opt-in assembly transactions, not arch refinement qualification."""

from copy import deepcopy
from dataclasses import replace, fields
import math

import numpy as np
import pytest

from docs.reference_cases.ge_beam3_curved_p5_force_accurate_assembly import (
    ForceAccurateAssemblyHistoryProbe, ForceAccurateElementResponse, SCHEMA, TOTAL_FORCE_BUDGET,
)
from docs.reference_cases.ge_beam3_curved_p5_assembly_history_probe import (
    AssemblyPathError, AssemblyTransactionError,
)
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import (
    NonlinearCondensedResponse, NonlinearMixedBeamProbe, _accuracy_metrics,
)
from docs.reference_cases.ge_beam3_curved_p5_displacement_control_probe import (
    DisplacementControlledAssemblyProbe, DisplacementControlError,
)
from docs.reference_cases.ge_beam3_curved_p5_arch_refinement_case import make_beam
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
from test_ge_beam3_curved_p5_assembly_history_probe import model, forces


def accurate(old):
    return ForceAccurateAssemblyHistoryProbe(old._references, [tuple(int(n) for n in row) for row in old._maps], old._sections,
        fixed_nodes=tuple(int(n) for n in old._fixed), order=old._order, extent=old._extent)


@pytest.fixture(scope='module')
def loaded():
    made = accurate(model())
    return made, made.trial(.1*forces())


def test_budget_allocation_and_independent_recomputation(loaded):
    made, trial = loaded
    policy = made.local_accuracy
    assert policy.limit == TOTAL_FORCE_BUDGET/2 and policy.rotation_length == made._length
    assert policy.force_scale == 1. and trial.residual_norm <= 1e-11
    assert math.fsum(e.estimated_force_error for e in trial.response.elements) <= TOTAL_FORCE_BUDGET
    for index, e in enumerate(trial.response.elements):
        assert e.accuracy_schema == SCHEMA and e.force_accuracy == policy
        ref, row = made._references[index], made._maps[index]
        local = NonlinearMixedBeamProbe(ref, made._sections[index], order=8, origins=trial.origins[index])
        ev = local.evaluate(trial.positions[row], trial.rotations[row] @ ref.nodal_triads,
                            e.local_rotations, e.moments)
        assert _accuracy_metrics(ev, policy)[1] == e.estimated_force_error
        np.testing.assert_array_equal(ev.residual[:18], e.residual)


def test_commit_replay_discard_and_plastic_continuation(loaded):
    original, trial = loaded
    made = deepcopy(original); trial = made._pending
    initial = digest(made.committed)
    made.commit(trial)
    assert digest(made.replay()) == digest(trial.response)
    assert digest(made.committed) != initial
    assert any(s.response.plastic_active for e in trial.response.elements for s in e.stations)
    after = digest(made.committed)
    declined = made.trial(.12*forces()); made.discard(declined)
    assert digest(made.committed) == after
    unloading = made.trial(.05*forces()); made.commit(unloading)
    assert digest(made.replay()) == digest(unloading.response)
    assert unloading.origins == tuple(tuple(s.response.history for s in e.stations) for e in trial.response.elements)


@pytest.mark.parametrize('mutation', ['schema', 'policy', 'estimate', 'missing'])
def test_rehashed_accuracy_mutations_cannot_commit(loaded, mutation):
    made = deepcopy(loaded[0]); old = made._pending
    e = old.response.elements[0]
    if mutation == 'schema': e = replace(e, accuracy_schema='other')
    if mutation == 'policy': e = replace(e, force_accuracy=replace(e.force_accuracy, limit=1e-11))
    if mutation == 'estimate': e = replace(e, estimated_force_error=e.estimated_force_error/2)
    if mutation == 'missing': e = NonlinearCondensedResponse(**{f.name:getattr(e,f.name) for f in fields(NonlinearCondensedResponse)})
    bad = replace(old, response=replace(old.response, elements=(e,)+old.response.elements[1:]))
    made._pending, made._pending_digest = bad, digest(bad)
    before = digest(made.committed)
    with pytest.raises(AssemblyTransactionError): made.commit(bad)
    assert digest(made.committed) == before


def test_failed_budget_and_cross_instance_trial_preserve_state(loaded):
    made = accurate(model()); before = digest(made.committed)
    with pytest.raises(AssemblyPathError): made.trial(.1*forces(), max_mixed_evaluations=0)
    assert digest(made.committed) == before and made._pending is None
    with pytest.raises(AssemblyTransactionError): made.commit(loaded[1])


def test_displacement_control_uses_explicit_successor_and_replays():
    old, _ = make_beam(2)
    control = DisplacementControlledAssemblyProbe(accurate(old), node=2)
    rows = []
    for target in (.1, .095):
        trial = control.trial(target, observer=rows.append)
        assert all(type(e) is ForceAccurateElementResponse for e in trial.assembly.response.elements)
        control.commit(trial)
        assert digest(control.committed_model.replay()) == digest(trial.assembly.response)
    before = digest(control.committed_model.committed)
    with pytest.raises(DisplacementControlError): control.trial(.09, max_mixed_evaluations=0)
    assert digest(control.committed_model.committed) == before
    assert trial.assembly.residual_norm <= 1e-11 and rows[-1]['phase'] == 'CONVERGED'


def test_successor_response_is_deterministic(loaded):
    made = accurate(model()); trial = made.trial(.1*forces())
    assert digest(trial) == digest(loaded[1])


def test_original_class_and_default_routing_stay_separate():
    old, _ = make_beam(2)
    assert type(old) is not ForceAccurateAssemblyHistoryProbe
    response = old.response_at(old.committed.positions, old.committed.rotations)
    assert all(type(e) is NonlinearCondensedResponse for e in response.elements)
    with pytest.raises(AssemblyTransactionError): accurate(old)._scatter(response.elements)


def test_estimated_scatter_obeys_the_allocated_triangle_inequality(loaded):
    made, trial = loaded
    total = np.zeros(6*made._nodes)
    for index, e in enumerate(trial.response.elements):
        ref, row = made._references[index], made._maps[index]
        local = NonlinearMixedBeamProbe(ref, made._sections[index], order=8, origins=trial.origins[index])
        ev = local.evaluate(trial.positions[row], trial.rotations[row] @ ref.nodal_triads,
                            e.local_rotations, e.moments)
        step = _accuracy_metrics(ev, made.local_accuracy)[0]
        total[made._dofs[index]] += ev.hessian[:18, 18:] @ step
    # Free restriction cannot increase Euclidean norm. This bounds only the
    # scattered estimate, not the unknown nonlinear/arithmetic remainder.
    estimate_norm = made._norm(total, np.zeros((made._nodes, 3)))
    assert estimate_norm <= math.fsum(e.estimated_force_error for e in trial.response.elements)
    assert estimate_norm <= TOTAL_FORCE_BUDGET


def test_physical_interface_and_global_force_moment_balance(loaded):
    made, trial = loaded
    first, second = [e.residual.reshape(3, 6) for e in trial.response.elements]
    assert np.linalg.norm(first[2]+second[0]) <= 1e-11
    r = trial.response.residual.reshape(made._nodes, 6)
    assert np.linalg.norm(r[:, :3].sum(axis=0)) <= 1e-11
    assert np.linalg.norm((r[:, 3:]+np.cross(trial.positions, r[:, :3])).sum(axis=0)) <= 1e-11
    assert np.linalg.norm(r[1:, :3]-trial.forces[1:]) <= 1e-11
    assert np.linalg.norm(r[1:, 3:]) <= 1e-11


def test_changed_policy_and_late_element_failure_leave_checkpoint_unchanged(loaded, monkeypatch):
    made = deepcopy(loaded[0]); trial = made._pending
    before = digest(made.committed)
    made._length *= 2
    with pytest.raises(AssemblyTransactionError): made.commit(trial)
    assert digest(made.committed) == before
    made = deepcopy(loaded[0]); trial = made._pending
    reconstruct = made._reconstruct_element
    def late(index, packet):
        if index == 1: raise ValueError('injected final-element replay failure')
        return reconstruct(index, packet)
    monkeypatch.setattr(made, '_reconstruct_element', late)
    with pytest.raises(AssemblyTransactionError): made.commit(trial)
    assert digest(made.committed) == before


def test_lower_accuracy_checkpoint_cannot_enter_successor_controller():
    old, _ = make_beam(2)
    control = DisplacementControlledAssemblyProbe(old, node=2)
    t = control.trial(.095); control.commit(t)
    successor = accurate(old)
    successor._checkpoint = deepcopy(control.committed_model._checkpoint)
    with pytest.raises(AssemblyTransactionError):
        DisplacementControlledAssemblyProbe(successor, node=2)
