"""Continuation algorithm and small beam tests, not engineering qualification."""

from copy import deepcopy
import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_continuation_probe as continuation
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation
from test_ge_beam3_curved_p5_assembly_history_probe import model, forces, law, digest, assembly


def test_exact_cubic_fold_crossed_without_regularizing_tangent():
    def evaluate(x):
        return x-x**3,np.diag(1-3*x*x),None
    x,lam,previous = np.zeros(1),0.,np.array([0.,1.])
    path = []
    for _ in range(25):
        x,lam,previous,_,iterations,arc = continuation.pseudo_step(
            evaluate,lambda x,d:x+d,lambda a,b:a-b,lambda r,p:np.linalg.norm(r),
            x,lam,np.ones(1),np.ones(2),previous,.08)
        assert abs(lam-(x[0]-x[0]**3))<1e-11
        assert arc<1e-11 and iterations<=16
        path.append((x[0],lam,previous[-1]))
    assert max(p[1] for p in path)>.38
    assert path[-1][1]<0 and path[-1][0]>1
    assert any(p[2]<0 for p in path)
    # At the exact mathematical fold, the augmented system is nonsingular
    # even though the one-dimensional load-controlled stiffness is zero.
    made = continuation.tangent(np.zeros((1,1)),np.ones(1),np.array([1.,0.]),np.ones(2))
    assert np.array_equal(made,np.array([1.,0.]))


def test_branch_singularity_fails_without_pseudoinverse():
    with pytest.raises(continuation.ContinuationError):
        continuation.tangent(np.zeros((1,1)),np.zeros(1),np.array([1.,0.]),np.ones(2))


def test_spatial_residual_derivative_off_equilibrium():
    made = model(order=4,laws=[law(1000.),law(1000.)])
    x,u = made.committed.positions.copy(),made.committed.rotations.copy()
    x[1:]+=np.sin(np.arange(12).reshape(4,3))*.003
    u[1:]=np.array([rotation(d) for d in .04*np.cos(np.arange(12).reshape(4,3))])
    base = made.response_at(x,u)
    direction = np.cos(np.arange(30)+.3)/5
    values = []
    for sign in (-1,1):
        delta = (sign*1e-6*direction).reshape(5,6)
        values.append(made.response_at(x+delta[:,:3],np.array([rotation(d[3:]) @ r for d,r in zip(delta,u)])).residual)
    expected = (values[1]-values[0])/2e-6
    actual = continuation.spatial_derivative(base) @ direction
    assert np.linalg.norm(actual-expected)<1e-7*max(1.,np.linalg.norm(expected))
    assert np.linalg.norm(base.tangent @ direction-expected)>1e-5


def test_small_beam_matches_load_control_and_replays():
    initial = model(order=4)
    driver = continuation.BeamContinuationProbe(initial,forces())
    before = digest(initial.committed)
    for _ in range(3):
        trial = driver.trial(.04)
        reference = deepcopy(initial)
        expected = reference.trial(trial.parameter*forces())
        assert np.linalg.norm(expected.positions-trial.assembly_trial.positions)<1e-10
        driver.commit(trial)
        assert digest(driver.committed_model.replay())==digest(trial.assembly_trial.response)
        initial = driver.committed_model
    assert driver.parameter>.1
    assert digest(model(order=4).committed)==before


@pytest.fixture
def pending():
    made = continuation.BeamContinuationProbe(model(order=4),forces())
    return made,made.trial(.02)


def test_atomic_late_commit_failure(pending,monkeypatch):
    made,trial = pending
    before = digest(made.committed_model.committed)
    factor = made.parameter
    old = assembly.NonlinearAssemblyHistoryProbe._reconstruct_element
    def fail(self,index,accepted):
        if index==1:
            raise ValueError('late element failure')
        return old(self,index,accepted)
    monkeypatch.setattr(assembly.NonlinearAssemblyHistoryProbe,'_reconstruct_element',fail)
    with pytest.raises(continuation.ContinuationError,match='validation'):
        made.commit(trial)
    assert made.parameter==factor
    assert digest(made.committed_model.committed)==before


def test_discard_stale_altered_and_defensive_access(pending):
    made,trial = pending
    with pytest.raises(continuation.ContinuationError):
        made.commit(deepcopy(trial))
    trial.tangent.setflags(write=True);trial.tangent[-1]+=1
    with pytest.raises(continuation.ContinuationError):
        made.commit(trial)
    made.discard(trial)
    with pytest.raises(continuation.ContinuationError):
        made.commit(trial)
    copied = made.committed_model
    copied.commit(copied.trial(.1*forces()))
    assert made.committed_model.committed.epoch==0


def test_budgets_fail_without_changing_state():
    made = continuation.BeamContinuationProbe(model(order=4),forces())
    before = digest(made.committed_model.committed)
    with pytest.raises(continuation.ContinuationError):
        made.trial(.02,max_mixed_evaluations=0)
    assert digest(made.committed_model.committed)==before
    with pytest.raises(continuation.ContinuationError):
        made.trial(.02,max_iterations=0)
    assert digest(made.committed_model.committed)==before and made.parameter==0


@pytest.mark.parametrize('step',[0.,-.1,.3,float('nan')])
def test_invalid_step(step):
    made = continuation.BeamContinuationProbe(model(order=4),forces())
    with pytest.raises((ValueError,continuation.ContinuationError)):
        made.trial(step)


def test_frame_chord_derivative_and_objectivity():
    x = np.arange(9).reshape(3,3)/9
    u = np.array([rotation(v) for v in np.arange(9).reshape(3,3)/12])
    v = np.array([rotation(v) for v in np.cos(np.arange(9)).reshape(3,3)/5]) @ u
    current = x+.1,v
    direction = np.sin(np.arange(18))
    increment = np.cos(np.arange(18))
    metric = np.ones(18)/3;metric[np.arange(18)%6<3]/=4
    free = np.arange(18)
    value,gradient = continuation.frame_constraint(current,(x,u),direction,metric,free)
    values = []
    for sign in (-1,1):
        delta = (sign*1e-6*increment).reshape(3,6)
        moved = (current[0]+delta[:,:3],np.array([rotation(d[3:]) @ q for d,q in zip(delta,v)]))
        values.append(continuation.frame_constraint(moved,(x,u),direction,metric,free)[0])
    assert abs((values[1]-values[0])/2e-6-gradient @ increment)<1e-9
    s = rotation([.6,-.4,.8]);t = np.array([2.,-1.,.3])
    moved = (current[0] @ s.T+t,s @ v @ s.T)
    origin = (x @ s.T+t,s @ u @ s.T)
    rotated = (direction.reshape(-1,3) @ s.T).ravel()
    transformed = continuation.frame_constraint(moved,origin,rotated,metric,free)
    assert abs(transformed[0]-value)<1e-12
    assert np.linalg.norm(transformed[1]-(gradient.reshape(-1,3) @ s.T).ravel())<1e-12


def test_beam_continuation_under_common_rigid_reexpression():
    original = model(order=4)
    s = rotation([.5,-.4,.7]);t = np.array([2.,-1.,.3])
    refs = [r.rigidly_transformed(s,t) for r in original._references]
    transformed = model(order=4,refs=refs)
    a = continuation.BeamContinuationProbe(original,forces())
    b = continuation.BeamContinuationProbe(transformed,forces() @ s.T)
    first,second = a.trial(.04),b.trial(.04)
    assert abs(first.parameter-second.parameter)<1e-11
    assert np.linalg.norm(second.assembly_trial.positions-(first.assembly_trial.positions @ s.T+t))<1e-11
    assert np.linalg.norm(second.assembly_trial.rotations-s @ first.assembly_trial.rotations @ s.T)<1e-11


def test_small_clamped_arch_compression_without_a_fold_claim():
    from docs.reference_cases.ge_beam3_curved_p5_continuum_probe import parabolic_references
    from docs.reference_cases.ge_beam3_curved_p5_section_probe import DirectedHardeningSectionProbe
    refs = parabolic_references(.1,2)
    elastic = np.diag([100.,100.,100.,1.,.1,.1])
    sections = [DirectedHardeningSectionProbe(elastic,[1.,0.,0.,0.,0.,0.],1e6,1.) for _ in refs]
    beam = assembly.NonlinearAssemblyHistoryProbe(refs,[(0,1,2),(2,3,4)],sections,
        fixed_nodes=(0,4),order=4)
    pattern = np.zeros((5,3));pattern[2,1] = -1.
    driver = continuation.BeamContinuationProbe(beam,pattern)
    previous = 0.
    for _ in range(12):
        trial = driver.trial(.04)
        driver.commit(trial)
        assert trial.parameter>previous
        previous = trial.parameter
        response = trial.assembly_trial.response
        assert np.linalg.eigvalsh(response.tangent[np.ix_(beam._free,beam._free)])[0]>0
        assert digest(driver.committed_model.replay())==digest(response)
        assert trial.arc_residual<=1e-11
    assert driver.committed_model.committed.positions[2,1]<0


def test_continuation_from_restored_assembly_and_explicit_orientation():
    from docs.reference_cases import ge_beam3_curved_p5_assembly_restart_probe as codec
    original = model(order=4)
    driver = continuation.BeamContinuationProbe(original,forces())
    driver.commit(driver.trial(.04))
    beam = driver.committed_model
    payload = codec.dumps(beam)
    restored = codec.loads(payload,beam._references,[r.tolist() for r in beam._maps],beam._sections,order=4)
    resumed = continuation.BeamContinuationProbe(restored,forces(),parameter=driver.parameter,
        previous=driver.orientation)
    first,second = driver.trial(.04),resumed.trial(.04)
    assert digest(first)==digest(second)
    # Assembly persistence does not implicitly supply continuation orientation.
    with pytest.raises(ValueError):
        continuation.BeamContinuationProbe(restored,forces())
