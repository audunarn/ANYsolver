"""Conservative globalization diagnostics, not general beam qualification."""

from dataclasses import asdict
import json
from types import SimpleNamespace

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_energy_seed_probe as energy_seed
from docs.reference_cases import ge_beam3_curved_p5_seeded_equilibrium_probe as old_seed
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation
from test_ge_beam3_curved_p5_assembly_history_probe import model,forces,law,digest
from test_ge_beam3_curved_p5_seeded_equilibrium_probe import specimen


def test_energy_accepts_descent_with_temporary_residual_increase():
    assert energy_seed.acceptance(1.,.9,-.2,1.,2.,.1,.2)=='ACCEPT_ENERGY'
    assert energy_seed.acceptance(1.,1.1,-.2,1.,2.,.1,.05)=='REJECT_ENERGY'
    assert energy_seed.acceptance(1.,.9,.2,1.,2.,.1,.05)=='REJECT_NON_DESCENT'


def test_unresolved_energy_difference_requires_strict_residual_descent():
    assert energy_seed.acceptance(1.,1.,-1e-20,1.,2.,.1,.05)=='ACCEPT_ROUNDOFF_RESIDUAL'
    assert energy_seed.acceptance(1.,1.,-1e-20,1.,2.,.1,.1)=='REJECT_ROUNDOFF'
    assert energy_seed.acceptance(1.,1.,-.2,1.,2.,.1,.05)=='REJECT_ENERGY'


@pytest.mark.parametrize('mutated',[float('nan'),float('inf')])
def test_nonfinite_merit_rejected(mutated):
    with pytest.raises(ValueError,match='finite'):
        energy_seed.acceptance(1.,mutated,-1.,1.,2.,1.,.5)


def test_positive_rescaling_preserves_armijo_decision():
    for scale in (1e-6,1.,1e6):
        assert energy_seed.acceptance(scale,.9*scale,-.2*scale,1.,2*scale,.1,.2)=='ACCEPT_ENERGY'


@pytest.mark.parametrize('potential,force',[(float('nan'),1.),(1.,1e308)])
def test_total_energy_rejects_nonfinite_or_overflowed_work(potential,force):
    with pytest.raises(ValueError,match='finite total energy'):
        energy_seed.energy(SimpleNamespace(potential=potential),np.full((1,3),2.),
                           np.zeros((1,3)),np.full((1,3),force))


def test_total_potential_derivative_is_dead_load_virtual_work():
    made = model(order=4,laws=[law(1e6),law(1e6)])
    x = made.committed.positions.copy();u = made.committed.rotations.copy()
    u[-1] = rotation([.03,-.02,.04]);x[-1]+=[.005,-.002,.003]
    f = .01*forces()
    response = made.response_at(x,u)
    direction = np.sin(np.arange(30)).reshape(5,6);direction[0] = 0.
    direction/=np.linalg.norm(direction)
    values = []
    h = 1e-5
    for sign in (-1,1):
        v = sign*h*direction
        a = x+v[:,:3];b = np.array([rotation(d[3:]) @ old for d,old in zip(v,u)])
        r = made.response_at(a,b)
        values.append(energy_seed.energy(r,a,made._coordinates,f)[0])
    expected = (response.residual-made._external(f)) @ direction.ravel()
    assert abs((values[1]-values[0])/(2*h)-expected)<1e-7*max(1.,abs(expected))


def test_small_curved_coupled_elastic_case_preserves_old_equilibrium():
    made = model(order=4,laws=[law(1e6),law(1e6)])
    state = made.committed;f = .01*forces()
    old = old_seed.solve(made,state.positions,state.rotations,f)
    result = energy_seed.solve(made,state.positions,state.rotations,f)
    assert np.linalg.norm(old.committed.positions-result.model.committed.positions)<1e-11
    assert digest(result.model.replay())==digest(result.model._checkpoint[1].response)
    assert made.committed.epoch==0 and made._pending is None
    assert result.checkpoints[-1].disposition=='COMPLETE'
    assert result.checkpoints[-1].residual_norm<=1e-11
    encoded = json.dumps([asdict(c) for c in result.checkpoints],sort_keys=True,allow_nan=False)
    assert 'NaN' not in encoded


def test_exhausted_attempt_has_diagnostics_but_no_partial_model():
    made = model(order=4,laws=[law(1e6),law(1e6)])
    state = made.committed;before = digest(state)
    with pytest.raises(energy_seed.EnergySeedError) as caught:
        energy_seed.solve(made,state.positions,state.rotations,.01*forces(),max_mixed_evaluations=0)
    assert caught.value.evaluations==0 and caught.value.checkpoints==()
    assert not hasattr(caught.value,'model')
    assert digest(made.committed)==before and made._pending is None


def test_invalid_bounds_are_rejected_before_mechanics(monkeypatch):
    made = model(order=4,laws=[law(1e6),law(1e6)]);state = made.committed
    def forbidden(*args,**kwargs):
        raise AssertionError('must not evaluate')
    monkeypatch.setattr(type(made),'_solve_all',forbidden)
    for limits in ({'max_iterations':17},{'max_iterations':True},{'max_mixed_evaluations':513}):
        with pytest.raises(ValueError,match='bounded'):
            energy_seed.solve(made,state.positions,state.rotations,state.forces,**limits)


@pytest.fixture(scope='module')
def family():
    results = []
    for count in (2,4,8):
        made,x,u,f,reference = specimen(count)
        before = digest(made.committed)
        result = energy_seed.solve(made,x,u,f)
        assert digest(made.committed)==before and made._pending is None
        results.append((made,result,x,reference))
    return results


def test_two_element_solve_and_refinement_are_distinct_gates(family):
    errors = []
    for made,result,x,reference in family:
        state = result.model.committed;last = result.checkpoints[-1]
        assert last.residual_norm<=1e-11
        assert last.iteration<=16 and last.evaluations<=256*len(made._maps)
        assert .5<np.arctan2(state.rotations[-1,1,0],state.rotations[-1,0,0])<reference.angles[-1]
        errors.append(np.linalg.norm(state.positions[-1]-x[-1])/
                      np.linalg.norm(x[-1]-made.committed.positions[-1]))
        assert all(h.accumulated==0 for history in state.histories for h in history)
        assert digest(result.model.replay())==digest(result.model._checkpoint[1].response)
    assert errors[0]>errors[1]>errors[2]
    # Solving the coarse system must not be confused with meeting 2% accuracy.
    assert errors[0]>.02 and errors[1]>.02 and errors[2]<.02


def test_successful_seed_is_repeatable_not_a_failed_request_retry(family):
    made,first,x,_ = family[0]
    _,_,u,f,_ = specimen(2)
    second = energy_seed.solve(made,x,u,f)
    assert digest(first.model.committed)==digest(second.model.committed)
    assert digest(first.model.replay())==digest(second.model.replay())
    assert first.checkpoints==second.checkpoints


def test_successful_path_includes_energy_descent_with_rising_residual(family):
    checkpoints = family[0][1].checkpoints
    accepted = [r for r in checkpoints if r.disposition.startswith('ACCEPT_')]
    assert any(b.residual_norm>a.residual_norm and b.energy<a.energy
               for a,b in zip(accepted,accepted[1:]))
    assert any(r.disposition=='REJECT_ENERGY' for r in checkpoints)
    assert any(r.disposition=='ACCEPT_ROUNDOFF_RESIDUAL' for r in checkpoints)


def test_final_coarse_branch_has_positive_free_second_variation(family):
    made,result,_,_ = family[0]
    response = result.model.replay()
    k = response.tangent[np.ix_(made._free,made._free)]
    assert np.linalg.norm(k-k.T)<1e-11*np.linalg.norm(k)
    np.linalg.cholesky(k)  # Binary64 case check, not an exact domain-wide proof.


def test_small_curved_seed_covaries_under_reference_reexpression():
    made = model(order=4,laws=[law(1e6),law(1e6)])
    state = made.committed;f = .01*forces()
    first = energy_seed.solve(made,state.positions,state.rotations,f).model
    g = rotation([1.2,-.8,.7]);translation = np.array([2.,-3.,1.])
    refs = [r.rigidly_transformed(g,translation) for r in made._references]
    moved = model(order=4,laws=[law(1e6),law(1e6)],refs=refs)
    initial = moved.committed
    second = energy_seed.solve(moved,initial.positions,initial.rotations,f @ g.T).model
    assert np.linalg.norm(second.committed.positions-(first.committed.positions @ g.T+translation))<1e-11
    assert np.linalg.norm(second.committed.rotations-g @ first.committed.rotations @ g.T)<1e-11


def test_seed_rejects_plastic_state_without_inventing_loading_history():
    made,x,u,f,_ = specimen(2,yield_force=1e-5)
    before = digest(made.committed)
    with pytest.raises(energy_seed.EnergySeedError,match='plastic load history'):
        energy_seed.solve(made,x,u,f)
    assert digest(made.committed)==before and made._pending is None


def test_late_commit_failure_cannot_publish_copy(monkeypatch):
    made = model(order=4,laws=[law(1e6),law(1e6)]);state = made.committed
    before = digest(state)
    old_commit = type(made).commit
    def fail_after_commit(self,trial):
        old_commit(self,trial)
        raise ValueError('injected after private commit')
    monkeypatch.setattr(type(made),'commit',fail_after_commit)
    with pytest.raises(energy_seed.EnergySeedError,match='private commit') as caught:
        energy_seed.solve(made,state.positions,state.rotations,.01*forces())
    assert not hasattr(caught.value,'model')
    assert digest(made.committed)==before and made._pending is None
