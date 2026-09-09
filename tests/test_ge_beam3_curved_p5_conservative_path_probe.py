"""Physical load-step transactions with fixed constitutive origins."""

from copy import deepcopy

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_conservative_path_probe as path
from docs.reference_cases import ge_beam3_curved_p5_assembly_restart_probe as codec
from test_ge_beam3_curved_p5_assembly_history_probe import model,forces,digest,assembly
from test_ge_beam3_curved_p5_seeded_equilibrium_probe import specimen
from docs.reference_cases.ge_beam3_curved_p5_energy_seed_probe import solve as seed
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation


def test_curved_plastic_trial_commit_replay_and_caller_isolation():
    made = model(order=4);before = digest(made.committed)
    driver = path.ConservativeAssemblyPathProbe(made)
    trial = driver.trial(.1*forces())
    assert digest(made.committed)==before
    assert digest(driver.committed_model.committed)==before
    assert trial.assembly.origins==made.committed.histories
    assert any(s.response.plastic_active for e in trial.assembly.response.elements for s in e.stations)
    assert trial.assembly.residual_norm<=1e-11
    driver.commit(trial)
    current = driver.committed_model
    assert current.committed.epoch==1
    assert digest(current.replay())==digest(trial.assembly.response)
    assert digest(made.committed)==before and made._pending is None


def test_pending_trial_requires_explicit_commit_or_discard():
    driver = path.ConservativeAssemblyPathProbe(model(order=4))
    trial = driver.trial(.01*forces())
    with pytest.raises(path.ConservativePathError,match='existing trial'):
        driver.trial(.02*forces())
    with pytest.raises(path.ConservativePathError,match='owned'):
        driver.commit(deepcopy(trial))
    driver.discard(trial)
    assert driver.committed_model.committed.epoch==0
    with pytest.raises(path.ConservativePathError,match='owned'):
        driver.commit(trial)


def test_trial_mutation_cannot_commit():
    driver = path.ConservativeAssemblyPathProbe(model(order=4))
    trial = driver.trial(.01*forces())
    before = digest(driver.committed_model.committed)
    object.__setattr__(trial.assembly,'residual_norm',0.)
    with pytest.raises(path.ConservativePathError,match='altered'):
        driver.commit(trial)
    assert digest(driver.committed_model.committed)==before
    driver.discard(trial)


def test_budget_failure_preserves_checkpoint_then_explicit_new_target_is_allowed():
    driver = path.ConservativeAssemblyPathProbe(model(order=4))
    driver.commit(driver.trial(.01*forces()))
    before = digest(driver.committed_model.committed)
    with pytest.raises(path.ConservativePathError) as caught:
        driver.trial(.02*forces(),max_mixed_evaluations=0)
    assert caught.value.evaluations==0 and caught.value.checkpoints==()
    assert driver._pending is None and driver._staged is None
    assert digest(driver.committed_model.committed)==before
    # Explicit smaller load requested by this test, not an automatic retry.
    smaller = driver.trial(.015*forces())
    assert smaller.origin_epoch==1
    driver.discard(smaller)
    assert digest(driver.committed_model.committed)==before


def test_late_private_commit_failure_preserves_previous_state(monkeypatch):
    driver = path.ConservativeAssemblyPathProbe(model(order=4))
    driver.commit(driver.trial(.01*forces()))
    before = digest(driver.committed_model.committed)
    trial = driver.trial(.02*forces())
    assert trial.assembly.iterations==3
    assert trial.checkpoints[-2].disposition=='ACCEPT_EQUILIBRIUM'
    assert trial.checkpoints[-2].residual_norm<=1e-11
    old_commit = assembly.NonlinearAssemblyHistoryProbe.commit
    def fail_after(self,trial):
        old_commit(self,trial)
        raise ValueError('injected private publication failure')
    monkeypatch.setattr(assembly.NonlinearAssemblyHistoryProbe,'commit',fail_after)
    with pytest.raises(path.ConservativePathError,match='commit validation'):
        driver.commit(trial)
    assert digest(driver.committed_model.committed)==before
    driver.discard(trial)


@pytest.fixture(scope='module')
def plastic_cycle():
    made = model(order=4)
    driver = path.ConservativeAssemblyPathProbe(made)
    records = []
    for amplitude in (.1,.2,.1,0.,-.2,0.):
        before = driver.committed_model.committed
        trial = driver.trial(amplitude*forces())
        assert digest(driver.committed_model.committed)==digest(before)
        assert trial.assembly.origins==before.histories
        driver.commit(trial)
        current = driver.committed_model
        assert digest(current.replay())==digest(trial.assembly.response)
        records.append((amplitude,trial,current))
    return made,records


def test_coupled_curved_plastic_load_unload_reverse_and_permanent_set(plastic_cycle):
    made,records = plastic_cycle
    assert made.committed.epoch==0
    active = []
    for index,(amplitude,trial,current) in enumerate(records):
        assert current.committed.epoch==index+1
        assert trial.assembly.residual_norm<=1e-11
        assert trial.assembly.iterations<=16 and trial.assembly.mixed_evaluations<=512
        stations = [s.response for e in trial.assembly.response.elements for s in e.stations]
        active.append(sum(s.plastic_active for s in stations))
        assert all(s.history.accumulated>=s.origin.accumulated for s in stations)
        assert all(s.dissipation_increment>=0 for s in stations)
        r = trial.assembly.response.residual.reshape(5,6)
        x = trial.assembly.positions
        assert np.linalg.norm(r[:,:3].sum(axis=0))<1e-11
        assert np.linalg.norm((r[:,3:]+np.cross(x,r[:,:3])).sum(axis=0))<1e-11
    assert active[0]>0 and active[1]>0 and active[4]>0
    assert active[2]==active[3]==active[5]==0
    last = records[-1][2]
    assert np.linalg.norm(last.committed.positions[-1]-last._coordinates[-1])>.01


def test_restart_continuation_preserves_exact_next_trial(plastic_cycle):
    _,records = plastic_cycle
    beam = records[1][2]
    payload = codec.dumps(beam)
    restored = codec.loads(payload,beam._references,[r.tolist() for r in beam._maps],
                           beam._sections,order=beam._order)
    assert codec.dumps(restored)==payload
    uninterrupted = path.ConservativeAssemblyPathProbe(beam)
    resumed = path.ConservativeAssemblyPathProbe(restored)
    a,b = uninterrupted.trial(.1*forces()),resumed.trial(.1*forces())
    assert digest(a)==digest(b)
    uninterrupted.commit(a);resumed.commit(b)
    assert codec.dumps(uninterrupted.committed_model)==codec.dumps(resumed.committed_model)
    assert digest(a)==digest(records[2][1])


def test_postcritical_elastic_branch_committed_load_decrease_increase_return():
    made,x,u,f,_ = specimen(2)
    initialized = seed(made,x,u,f).model
    driver = path.ConservativeAssemblyPathProbe(initialized)
    angles = []
    for factor in (.995,1.005,1.):
        before = digest(driver.committed_model.committed)
        trial = driver.trial(factor*f)
        assert digest(driver.committed_model.committed)==before
        driver.commit(trial)
        current = driver.committed_model
        assert trial.assembly.residual_norm<=1e-11
        assert digest(current.replay())==digest(trial.assembly.response)
        state = current.committed
        angles.append(np.arctan2(state.rotations[-1,1,0],state.rotations[-1,0,0]))
        assert all(h.accumulated==0 for hs in state.histories for h in hs)
        assert angles[-1]>.4  # Never count collapse to the straight branch as success.
    assert angles[0]<angles[2]<angles[1]
    assert np.array_equal(driver.committed_model.committed.forces,initialized.committed.forces)
    # Equilibrium tolerance and coarse-mesh error are separate; exact binary64
    # return displacement is not asserted on this ill-conditioned branch.
    old = initialized.replay();new = driver.committed_model.replay()
    assert np.linalg.norm(new.residual-old.residual)<1e-11


def test_invalid_input_and_published_model_copies_cannot_mutate_controller():
    driver = path.ConservativeAssemblyPathProbe(model(order=4))
    before = digest(driver.committed_model.committed)
    for limits in ({'max_iterations':17},{'max_iterations':True},{'max_mixed_evaluations':513}):
        with pytest.raises(ValueError,match='bounded'):
            driver.trial(.1*forces(),**limits)
    with pytest.raises(ValueError):
        driver.trial(np.full((5,3),np.nan))
    clone = driver.committed_model
    clone.commit(clone.trial(.01*forces()))
    assert digest(driver.committed_model.committed)==before


def test_curved_plastic_path_is_objective_under_reference_reexpression():
    base = model(order=4)
    g = rotation([1.1,-.7,.9]);c = np.array([2.,-1.,3.])
    moved = model(order=4,refs=[r.rigidly_transformed(g,c) for r in base._references])
    first,second = path.ConservativeAssemblyPathProbe(base),path.ConservativeAssemblyPathProbe(moved)
    for amplitude in (.1,.2):
        a,b = first.trial(amplitude*forces()),second.trial(amplitude*forces() @ g.T)
        assert np.linalg.norm(b.assembly.positions-(a.assembly.positions @ g.T+c))<1e-11
        assert np.linalg.norm(b.assembly.rotations-g @ a.assembly.rotations @ g.T)<1e-11
        transform = np.kron(np.eye(10),g)
        ra,rb = a.assembly.response,b.assembly.response
        assert np.linalg.norm(rb.residual-transform @ ra.residual)<1e-11
        assert np.linalg.norm(rb.tangent-transform @ ra.tangent @ transform.T)<1e-11*np.linalg.norm(ra.tangent)
        first.commit(a);second.commit(b)
        for hs,ks in zip(first.committed_model.committed.histories,second.committed_model.committed.histories):
            for h,k in zip(hs,ks):
                assert abs(h.plastic_coordinate-k.plastic_coordinate)<1e-11
                assert abs(h.accumulated-k.accumulated)<1e-11
