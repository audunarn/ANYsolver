"""Instrumentation transparency and experimental merit algebra, not qualification."""

import inspect
import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_local_trace_probe as tracing
from docs.reference_cases import ge_beam3_curved_p5_correction_seed_probe as correction
from docs.reference_cases import ge_beam3_curved_p5_seeded_equilibrium_probe as original
from docs.reference_cases import ge_beam3_curved_p5_shape_seed_probe as shape
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation
from test_ge_beam3_curved_p5_assembly_history_probe import model,forces,law,digest


def test_local_trace_transparent_and_deterministic():
    made = model(order=8,laws=[law(1e6),law(1e6)])
    ref,section = made._references[0],made._sections[0]
    first = tracing.trace(ref,section,ref.coordinates,ref.nodal_triads)
    second = tracing.trace(ref,section,ref.coordinates,ref.nodal_triads)
    assert first['status']['state']=='COMPLETE'
    assert first['status']['evaluations']==1 and len(first['records'])==1
    assert tracing.canonical(first)==tracing.canonical(second)
    assert first['production_qualified'] is False


def test_global_trace_does_not_patch_class_or_mutate_model():
    made = model(order=8,laws=[law(1e6),law(1e6)])
    state = made.committed
    before = digest(state)
    method = type(made)._solve_all
    result = tracing.trace_seed(made,state.positions,state.rotations,np.zeros_like(state.forces))
    assert result['status']['state']=='COMPLETE'
    assert len(result['attempts'])==1
    assert all(e['status']=='COMPLETE' for e in result['attempts'][0]['elements'])
    assert type(made)._solve_all is method
    assert digest(made.committed)==before and made._pending is None


def test_correction_merit_is_residual_row_scaling_invariant():
    rng = np.random.default_rng(4)
    a = rng.normal(size=(12,12));a = a.T @ a+np.eye(12)
    f = rng.normal(size=12)
    scales = np.logspace(-3,3,12)
    first = np.linalg.solve(a,f)
    second = np.linalg.solve(scales[:,None]*a,scales*f)
    free = np.arange(6,18)
    assert abs(correction.correction_norm(first,free,2.)-correction.correction_norm(second,free,2.))<1e-12


def test_correction_metric_is_rigid_reexpression_invariant():
    v = np.sin(np.arange(24)).reshape(4,6)
    s = rotation([.5,.4,-.7])
    transformed = (v.reshape(-1,3) @ s.T).reshape(4,6)
    free = np.arange(6,30)
    assert abs(correction.correction_norm(v.ravel(),free,2.)-
               correction.correction_norm(transformed.ravel(),free,2.))<1e-12


def test_experimental_solver_preserves_resolved_small_elastic_case():
    made = model(order=4,laws=[law(1e6),law(1e6)])
    state = made.committed
    f = .01*forces()
    a = original.solve(made,state.positions,state.rotations,f)
    b = correction.solve(made,state.positions,state.rotations,f)
    assert np.linalg.norm(a.committed.positions-b.committed.positions)<1e-11
    assert np.linalg.norm(a.replay().tangent-b.replay().tangent)<1e-11*np.linalg.norm(a.replay().tangent)
    assert made.committed.epoch==0


def test_merit_change_does_not_change_other_solver_code():
    old,new = inspect.getsource(original.solve),inspect.getsource(correction.solve)
    new = new.replace('matrix = derivative[np.ix_(free,free)]\n            step[free] = np.linalg.solve(matrix,-residual[free])\n            merit = correction_norm(step[free],free,staged._length)',
                      'step[free] = np.linalg.solve(derivative[np.ix_(free,free)],-residual[free])')
    new = new.replace('simplified = np.linalg.solve(matrix,(candidate.residual-external)[free])\n                if correction_norm(simplified,free,staged._length)<merit:',
                      'if staged._norm(candidate.residual-external,f)<norm:')
    assert new==old


def test_experimental_zero_budget_does_not_advance_state():
    made = model(order=4,laws=[law(1e6),law(1e6)])
    state = made.committed
    with pytest.raises(correction.SeededEquilibriumError):
        correction.solve(made,state.positions,state.rotations,.01*forces(),max_mixed_evaluations=0)
    assert digest(state)==digest(made.committed)


def test_tip_angle_spatial_derivative_in_three_dimensions():
    u = np.array([np.eye(3),rotation([.3,-.2,.6])])
    direction = np.array([.4,-.7,.2])
    _,gradient = shape.tip_angle(u)
    h = 1e-5
    values = []
    for sign in (-1,1):
        moved = u.copy();moved[-1] = rotation(sign*h*direction) @ u[-1]
        values.append(shape.tip_angle(moved)[0])
    assert abs((values[1]-values[0])/(2*h)-gradient @ direction)<1e-7


def test_tip_angle_rejects_singular_chart():
    u = np.array([rotation([0.,np.pi/2,0.])])
    with pytest.raises(ValueError,match='chart'):
        shape.tip_angle(u)


@pytest.mark.parametrize('limits',[
    {'max_iterations':17},{'max_iterations':True},
    {'max_mixed_evaluations':513},{'max_mixed_evaluations':-1},
])
def test_shape_experiment_rejects_invalid_bounds_before_evaluation(monkeypatch,limits):
    made = model(order=4,laws=[law(1e6),law(1e6)])
    state = made.committed
    def forbidden(*args,**kwargs):
        raise AssertionError('no mechanics evaluation allowed')
    monkeypatch.setattr(type(made),'_solve_all',forbidden)
    with pytest.raises(ValueError,match='bounded'):
        shape.solve(made,state.positions,state.rotations,state.forces,**limits)
    assert digest(state)==digest(made.committed) and made._pending is None


def test_shape_experiment_budget_failure_is_atomic():
    made = model(order=4,laws=[law(1e6),law(1e6)])
    state = made.committed
    u = state.rotations.copy();u[-1] = rotation([0.,0.,.1])
    before = digest(state)
    with pytest.raises(shape.ShapeSeedError,match='budget'):
        shape.solve(made,state.positions,u,.01*forces(),max_mixed_evaluations=0)
    assert digest(made.committed)==before and made._pending is None
    assert np.array_equal(u[-1],rotation([0.,0.,.1]))


def test_failed_experiments_cannot_be_mistaken_for_selected_solvers():
    for module in (correction,shape):
        assert 'FAILED DEVELOPMENT EXPERIMENT' in module.__doc__
        assert 'not a selected or qualified solver' in module.__doc__
