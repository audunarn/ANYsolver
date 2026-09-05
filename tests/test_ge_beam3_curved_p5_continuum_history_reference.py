"""Fixed-origin continuum history and controlled cyclic beam comparisons."""

import ast
from pathlib import Path

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_continuum_history_reference as history
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_continuum_reference import VirginParabolicCantileverReference
from docs.reference_cases.ge_beam3_curved_p5_section_probe import SectionHistory
from test_ge_beam3_curved_p5_nonlinear_mixed_probe import section,A,law
from test_ge_beam3_curved_p5_assembly_history_probe import model,forces


SCHEDULE = (.1,.2,.1,0.,-.2,0.)


def reference(*, steps=128, origins=None):
    return history.HistoryParabolicCantileverReference(.4,section(),A,.02,.4,steps=steps,origins=origins)


def run_reference(steps):
    origins = None
    results = []
    for amplitude in SCHEDULE:
        solver = reference(steps=steps,origins=origins)
        before = solver.origins.tobytes()
        result = solver.solve(amplitude*np.array([.1,-.3,.2]))
        assert solver.origins.tobytes() == before
        results.append(result)
        origins = result.histories
    return results


@pytest.fixture(scope='module')
def cycles():
    return run_reference(128),run_reference(256)


def test_separate_reference_import_boundary():
    tree = ast.parse(Path(history.__file__).read_text(encoding='utf-8'))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node,ast.ImportFrom):
            imports.add(node.module)
    assert imports == {'dataclasses','numpy','docs.reference_cases.ge_beam3_curved_p5_nonlinear_continuum_reference'}


@pytest.mark.parametrize('origin,stress', [
    ([.02,.03],[0.,0.,0.,0.,0.,0.]),
    ([.02,.03],[.2,-.03,.02,.01,-.04,.06]),
    ([.02,.03],[-.2,.03,-.02,-.01,.04,-.06]),
    ([-.02,.03],[.2,-.03,.02,.01,-.04,.06]),
])
def test_fixed_history_inverse_matches_forward_return_and_work(origin,stress):
    solver = reference(steps=32)
    stress = np.array(stress)
    e,derivative,z,p,potential,dissipation = solver.stress_inverse(stress,origin)
    forward = law().strain_response(e,SectionHistory(*origin))
    assert np.linalg.norm(forward.resultants-stress) <= 1e-11
    assert abs(forward.history.plastic_coordinate-z) <= 1e-11
    assert abs(forward.history.accumulated-p) <= 1e-11
    assert abs(forward.incremental_potential-potential) <= 1e-11
    assert abs(forward.dissipation_increment-dissipation) <= 1e-11
    assert np.linalg.norm(forward.tangent @ derivative-np.eye(6)) <= 1e-11
    direction = np.cos(np.arange(6))/7
    plus = solver.stress_inverse(stress+1e-6*direction,origin)
    minus = solver.stress_inverse(stress-1e-6*direction,origin)
    assert np.linalg.norm((plus[0]-minus[0])/2e-6-derivative @ direction) <= 1e-7
    assert abs((plus[4]-minus[4])/2e-6-stress @ derivative @ direction) <= 1e-7


def test_first_increment_agrees_with_virgin_reference(cycles):
    first = cycles[0][0]
    virgin = VirginParabolicCantileverReference(.4,section(),A,.02,.4).solve([.01,-.03,.02],steps=128)
    assert np.linalg.norm(first.response.coordinates-virgin.coordinates) <= 1e-11
    assert np.linalg.norm(first.response.frames-virgin.frames) <= 1e-11
    assert abs(first.response.potential-virgin.potential) <= 1e-11
    assert not np.any(first.origins)
    assert np.array_equal(first.dense_coordinates[::2],first.response.coordinates)
    assert np.array_equal(first.dense_frames[::2],first.response.frames)


def test_loading_unloading_and_partial_reverse_plasticity(cycles):
    for cycle in cycles:
        count = len(cycle[0].histories)
        activity = [np.count_nonzero(r.dissipation_increments) for r in cycle]
        assert activity[:4] == [count,count,0,0]
        assert 0 < activity[4] < count//4
        assert activity[5] == 0
        for previous,current in zip(cycle,cycle[1:]):
            assert np.array_equal(current.origins,previous.histories)
            assert np.all(current.histories[:,1] >= previous.histories[:,1])
        for result in cycle:
            assert np.all(result.histories[:,1] >= np.abs(result.histories[:,0]))
            assert np.all(result.dissipation_increments >= 0)
            assert result.integrations_total <= 32 and result.response.iterations <= 12
            assert result.dense_orthogonality_error <= 1e-7
            assert result.response.tip_moment_residual <= 1e-12
        assert np.linalg.norm(cycle[-1].response.coordinates[-1]-[1.,0.,0.]) > .2
        active = cycle[4].dissipation_increments > 0
        assert np.all(cycle[4].histories[active,0] < cycle[4].origins[active,0])
        assert np.array_equal(cycle[5].histories,cycle[4].histories)


def test_reference_history_refinement_resolves_front_to_engineering_scale(cycles):
    coarse,fine = cycles
    for index,(a,b) in enumerate(zip(coarse,fine)):
        displacement = np.linalg.norm(a.response.coordinates[-1]-b.response.coordinates[-1])
        assert displacement < (1e-8 if index < 4 else 2e-7)
        assert np.max(np.abs(a.histories-b.histories[::2])) < 2e-7
        assert abs(a.response.potential-b.response.potential) < 1e-7
    # The active-front steps are less smooth; do not claim uniform RK4 order.
    assert np.linalg.norm(coarse[4].response.coordinates[-1]-fine[4].response.coordinates[-1]) > 1e-8


def test_identical_discrete_cycles_converge_but_eight_elements_do_not_close_two_percent(cycles):
    errors = []
    for count in (2,4,8):
        made = model(count)
        row = []
        for amplitude,exact in zip(SCHEDULE,cycles[-1]):
            trial = made.trial(amplitude*forces(count))
            made.commit(trial)
            expected = exact.response.coordinates[-1]-[1.,0.,0.]
            row.append(np.linalg.norm(trial.positions[-1]-made._coordinates[-1]-expected)/np.linalg.norm(expected))
            assert trial.residual_norm <= 1e-11
        errors.append(row)
    errors = np.array(errors)
    assert np.all(errors[1:] < errors[:-1])
    assert errors[-1,0] < .02
    assert np.all(errors[-1,1:] > .02)  # Preserve the unresolved cyclic engineering gate.
    assert .03 < errors[-1,-1] < .04
    assert .04 < errors[-1,-2] < .05


def test_midpoint_history_is_not_dropped(cycles):
    old = cycles[0][0]
    changed = old.histories.copy()
    changed[1::2,0] = 0.
    original = reference(origins=old.histories).solve(np.zeros(3))
    assert original.response.tip_moment_residual <= 1e-12
    # This oscillatory material-history mutation is unresolved on the fixed
    # grid and must fail closed, not silently ignore the midpoint origins.
    with pytest.raises(history.ContinuumReferenceError,match='frame drift'):
        reference(origins=changed).solve(np.zeros(3))


def test_fixed_history_shooting_sensitivities(cycles):
    solver = reference(origins=cycles[0][1].histories)
    force = np.array([.01,-.03,.02])
    moment = np.cross([2.,0.,0.],force)
    states,residual,jacobian = solver.integrate(moment,force)
    direction = np.array([.3,-.2,.4])
    plus,pr,_ = solver.integrate(moment+1e-6*direction,force)
    minus,mr,_ = solver.integrate(moment-1e-6*direction,force)
    assert np.linalg.norm((plus[-1,:12]-minus[-1,:12])/2e-6-states[-1,13:].reshape(12,3) @ direction) <= 1e-7
    assert np.linalg.norm((pr-mr)/2e-6-jacobian @ direction) <= 1e-7


def test_origin_copy_grid_identity_and_failures_preserve_input(cycles):
    origin = cycles[0][0].histories.copy()
    solver = reference(origins=origin)
    before = solver.origins.tobytes()
    origin[:] = 99.
    assert solver.origins.tobytes() == before
    for kwargs in ({'max_integrations':0},{'max_integrations':1},{'max_integrations':2},{'max_iterations':0}):
        with pytest.raises(history.ContinuumReferenceError,match='budget'):
            solver.solve([.02,-.06,.04],**kwargs)
        assert solver.origins.tobytes() == before
    for kwargs in ({'steps':256},{'max_integrations':33},{'max_integrations':True}):
        with pytest.raises(history.ContinuumReferenceError):
            solver.solve([.01,-.03,.02],**kwargs)
    with pytest.raises(history.ContinuumReferenceError):
        solver.integrate([0.,0.,0.],[0.,0.,0.],steps=256)
    with pytest.raises(history.ContinuumReferenceError):
        reference(steps=256,origins=solver.origins)
    with pytest.raises(history.ContinuumReferenceError):
        solver._origin_at(.0001)
    with pytest.raises(history.ContinuumReferenceError):
        solver.section_inverse(np.zeros(6))
    bad = solver.origins.copy();bad[0]=[1.,0.]
    with pytest.raises(history.ContinuumReferenceError):
        reference(origins=bad)


def test_late_dense_reconstruction_failure_cannot_advance_origins(cycles,monkeypatch):
    solver = reference(origins=cycles[0][0].histories)
    original = solver.integrate
    before,calls = solver.origins.tobytes(),[]
    def changed_replay(*args,**kwargs):
        result = original(*args,**kwargs)
        calls.append(1)
        # At zero load shooting takes one integration; the second is replay.
        if len(calls) == 2:
            result[0][-1,0] += .01
        return result
    monkeypatch.setattr(solver,'integrate',changed_replay)
    with pytest.raises(history.ContinuumReferenceError,match='replay'):
        solver.solve(np.zeros(3))
    assert len(calls) == 2 and solver.origins.tobytes() == before


def test_repeat_uses_same_accepted_origins(cycles):
    first = cycles[0][2]
    repeated = reference(origins=first.origins).solve(first.force)
    assert repeated.force.tobytes() == first.force.tobytes()
    assert repeated.histories.tobytes() == first.histories.tobytes()
    assert repeated.dense_coordinates.tobytes() == first.dense_coordinates.tobytes()
    assert repeated.dense_frames.tobytes() == first.dense_frames.tobytes()
    assert repeated.response.potential == first.response.potential
