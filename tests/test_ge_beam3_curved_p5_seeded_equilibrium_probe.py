"""One elastic postcritical cantilever benchmark, not full qualification."""

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_seeded_equilibrium_probe as seed
from docs.reference_cases.ge_beam3_curved_p5_postcritical_reference import solve as reference
from docs.reference_cases.ge_beam3_curved_p5_continuum_probe import parabolic_references
from docs.reference_cases.ge_beam3_curved_p5_assembly_history_probe import NonlinearAssemblyHistoryProbe
from docs.reference_cases.ge_beam3_curved_p5_section_probe import DirectedHardeningSectionProbe
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
from docs.reference_cases.ge_beam3_curved_p5_continuation_probe import BeamContinuationProbe


def specimen(count=8,yield_force=1e6):
    independent = reference(2.,1000.,400.,1.,.6,stations=2*count+1)
    refs = parabolic_references(0.,count)
    elastic = np.diag([1000.,400.,400.,2.,1.,2.])
    sections = [DirectedHardeningSectionProbe(elastic,[1.,0.,0.,0.,0.,0.],yield_force,1.) for _ in refs]
    model = NonlinearAssemblyHistoryProbe(refs,[(2*i,2*i+1,2*i+2) for i in range(count)],sections,order=8)
    positions = np.column_stack((independent.coordinates,np.zeros(2*count+1)))
    positions[:,0]-=1.
    rotations = np.array([rotation([0.,0.,a]) for a in independent.angles])
    forces = np.zeros_like(positions);forces[-1,0] = -independent.load
    return model,positions,rotations,forces,independent


@pytest.fixture(scope='module')
def resolved():
    values = []
    for count in (4,8):
        model,x,u,f,independent = specimen(count)
        before = digest(model.committed)
        solved = seed.solve(model,x,u,f)
        assert digest(model.committed)==before
        values.append((model,solved,x,independent))
    return values


def test_resolved_postcritical_branch_refines_below_two_percent(resolved):
    errors = []
    for model,solved,x,independent in resolved:
        state = solved.committed
        angle = np.arctan2(state.rotations[-1,1,0],state.rotations[-1,0,0])
        # Explicitly reject return to the straight branch as a false match.
        assert angle>.5 and independent.load>independent.critical_load
        errors.append(np.linalg.norm(state.positions[-1]-x[-1])/
                      np.linalg.norm(x[-1]-model.committed.positions[-1]))
        assert digest(solved.replay())==digest(solved._checkpoint[1].response)
        assert solved._checkpoint[1].residual_norm<=1e-11
        assert all(h.accumulated==0 for history in state.histories for h in history)
    assert errors[1]<errors[0] and errors[1]<.02


def test_postcritical_continuation_against_reference_branch(resolved):
    _,solved,_,independent = resolved[-1]
    pattern = np.zeros_like(solved.committed.forces);pattern[-1,0] = -1.
    driver = BeamContinuationProbe(solved,pattern,parameter=independent.load)
    previous = independent.load
    for _ in range(3):
        trial = driver.trial(.01)
        driver.commit(trial)
        state = driver.committed_model.committed
        angle = np.arctan2(state.rotations[-1,1,0],state.rotations[-1,0,0])
        continuum = reference(2.,1000.,400.,1.,angle)
        assert trial.parameter>previous
        assert abs(trial.parameter/continuum.load-1)<.02
        expected = np.r_[continuum.coordinates[-1],0.];expected[0]-=1.
        assert np.linalg.norm(state.positions[-1]-expected)/np.linalg.norm(expected-[1.,0.,0.])<.02
        previous = trial.parameter


def test_budget_failure_and_elastic_seed_guard():
    model,x,u,f,_ = specimen(4)
    before = digest(model.committed)
    with pytest.raises(seed.SeededEquilibriumError):
        seed.solve(model,x,u,f,max_mixed_evaluations=0)
    assert digest(model.committed)==before
    # A branch shape does not define the loading history of a yielded section.
    nonlinear,x,u,f,_ = specimen(4,yield_force=1e-5)
    before = digest(nonlinear.committed)
    with pytest.raises(seed.SeededEquilibriumError):
        seed.solve(nonlinear,x,u,f)
    assert digest(nonlinear.committed)==before


def test_invalid_seed_and_nonvirgin_model(resolved):
    _,solved,_,_ = resolved[0]
    state = solved.committed
    with pytest.raises(ValueError):
        seed.solve(solved,state.positions,state.rotations,state.forces)
    model,x,u,f,_ = specimen(4)
    wrong = x.copy();wrong[0,0]+=.1
    with pytest.raises(ValueError):
        seed.solve(model,wrong,u,f)


def test_injected_late_commit_failure_does_not_publish(resolved,monkeypatch):
    model,solved,_,_ = resolved[0]
    before = digest(model.committed)
    original = NonlinearAssemblyHistoryProbe._reconstruct_element
    def fail(self,index,trial):
        if index==3:
            raise ValueError('late seed commit failure')
        return original(self,index,trial)
    monkeypatch.setattr(NonlinearAssemblyHistoryProbe,'_reconstruct_element',fail)
    state = solved.committed
    with pytest.raises(seed.SeededEquilibriumError,match='AssemblyTransactionError'):
        seed.solve(model,state.positions,state.rotations,state.forces)
    assert digest(model.committed)==before
