"""Separate strong-form reference and controlled discrete convergence probes."""

import ast
from pathlib import Path

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_nonlinear_continuum_reference as continuum
from test_ge_beam3_curved_p5_nonlinear_mixed_probe import section, A, law
from test_ge_beam3_curved_p5_assembly_history_probe import model, forces


def reference(yield_force=.02, height=.4):
    return continuum.VirginParabolicCantileverReference(height,section(),A,yield_force,.4)


@pytest.fixture(scope='module', params=(1000.,.02), ids=('elastic','plastic'))
def solutions(request):
    y = request.param
    solver = reference(y)
    refs = [solver.solve([.01,-.03,.02],steps=n) for n in (128,256,512)]
    discrete = []
    for count in (1,2,4,8):
        made = model(count,laws=[law(y) for _ in range(count)])
        discrete.append(made.trial(.1*forces(count)))
    return y,refs,discrete


def test_reference_has_no_producer_or_mechanics_imports():
    tree = ast.parse(Path(continuum.__file__).read_text(encoding='utf-8'))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node,ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node,ast.ImportFrom):
            imports.add(node.module)
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
            assert node.func.id not in ('eval','exec','__import__')
    assert imports == {'dataclasses','numpy'}


@pytest.mark.parametrize('stress', [np.zeros(6), np.array([.01,0,0,0,0,0]),
                                    np.array([.1,-.03,.02,.01,-.04,.06]),
                                    np.array([-.1,.03,-.02,-.01,.04,-.06])])
def test_stress_inverse_matches_full_constitutive_return_and_derivative(stress):
    solver = reference()
    strain,derivative,z,potential = solver.section_inverse(stress)
    forward = law().strain_response(strain)
    assert np.linalg.norm(forward.resultants-stress) <= 1e-11
    assert abs(forward.history.plastic_coordinate-z) <= 1e-11
    assert abs(forward.incremental_potential-potential) <= 1e-11
    assert np.linalg.norm(forward.tangent @ derivative-np.eye(6)) <= 1e-11
    d = np.cos(np.arange(6))/7
    plus = solver.section_inverse(stress+1e-6*d)[0]
    minus = solver.section_inverse(stress-1e-6*d)[0]
    assert np.linalg.norm((plus-minus)/2e-6-derivative @ d) <= 1e-7


def test_shooting_sensitivity_matches_independent_directional_difference():
    solver = reference()
    force = np.array([.01,-.03,.02])
    moment = np.cross([2.,0.,0.],force)
    states,residual,jacobian = solver.integrate(moment,force,steps=64)
    direction = np.array([.3,-.2,.4])
    plus,pr,_ = solver.integrate(moment+1e-6*direction,force,steps=64)
    minus,mr,_ = solver.integrate(moment-1e-6*direction,force,steps=64)
    expected = states[-1,13:].reshape(12,3) @ direction
    assert np.linalg.norm((plus[-1,:12]-minus[-1,:12])/2e-6-expected) <= 1e-7
    assert np.linalg.norm((pr-mr)/2e-6-jacobian @ direction) <= 1e-7


@pytest.mark.parametrize('force', [.1,-.1])
def test_straight_axial_plastic_manufactured_solution(force):
    stiffness = np.diag([2.,3.,4.,5.,6.,7.])
    solver = continuum.VirginParabolicCantileverReference(0.,stiffness,[1.,0.,0.,0.,0.,0.],.02,.4)
    made = solver.solve([force,0.,0.],steps=64)
    z = np.sign(force)*(abs(force)-.02)/.4
    strain = force/2+z
    assert np.linalg.norm(made.coordinates[-1]-[1+2*strain,0.,0.]) <= 1e-11
    assert np.max(np.abs(made.strains[:,0]-strain)) <= 1e-11
    assert np.max(np.abs(made.strains[:,1:])) <= 1e-11
    assert np.max(np.abs(made.plastic_coordinates-z)) <= 1e-11
    potential = 2*(.5*force*force/2+.5*.4*z*z+.02*abs(z))
    assert abs(made.potential-potential) <= 1e-11
    assert made.iterations == 0 and made.integrations == 1


def test_pure_bending_ivp_reproduces_exact_circular_centerline():
    solver = continuum.VirginParabolicCantileverReference(0.,np.diag([2.,3.,4.,5.,6.,7.]),A,1000.,.4)
    # Constant spatial couple about z is material bending component 2 here.
    moment,curvature = .6,.1
    states,_,_ = solver.integrate([0.,0.,moment],[0.,0.,0.],steps=128)
    expected = np.array([-1+np.sin(2*curvature)/curvature,(1-np.cos(2*curvature))/curvature,0.])
    assert np.linalg.norm(states[-1,:3]-expected) <= 1e-11
    assert abs(states[-1,12]-.6*.6/6) <= 1e-11


def test_stress_free_curved_geometry_is_reproduced_without_projection():
    solver = reference(height=.7)
    made = solver.solve([0.,0.,0.],steps=512)
    t = np.linspace(-1.,1.,513)
    expected = np.column_stack((t,.7*(1-t*t),np.zeros_like(t)))
    assert np.max(np.linalg.norm(made.coordinates-expected,axis=1)) <= 1e-9
    assert made.orthogonality_error <= 1e-10
    assert made.potential == 0.
    assert not np.any(made.strains)


def test_reference_refinement_and_balance(solutions):
    _,refs,_ = solutions
    coarse,middle,fine = refs
    first = np.linalg.norm(coarse.coordinates[-1]-middle.coordinates[-1])
    second = np.linalg.norm(middle.coordinates[-1]-fine.coordinates[-1])
    assert first <= 1e-8 and second <= 1e-9
    assert first > 8*second
    assert abs(middle.potential-fine.potential) <= 1e-10
    for result in refs:
        assert result.iterations <= 12 and result.integrations <= 32
        assert result.tip_moment_residual <= 1e-12
        assert result.orthogonality_error <= 1e-9
        balance = result.spatial_moments+np.cross(result.coordinates-[-1.,0.,0.],[.01,-.03,.02])
        assert np.max(np.linalg.norm(balance-result.root_moment,axis=1)) <= 1e-11
    assert fine.orthogonality_error < middle.orthogonality_error < coarse.orthogonality_error
    assert np.all(np.max(np.abs(fine.strains),axis=0) > 1e-5)


def test_reference_repeat_is_byte_identical(solutions):
    y,refs,_ = solutions
    repeated = reference(y).solve([.01,-.03,.02],steps=128)
    for name in ('coordinates','frames','spatial_moments','material_resultants','strains','plastic_coordinates','root_moment'):
        assert getattr(repeated,name).tobytes() == getattr(refs[0],name).tobytes()
    assert repeated.potential == refs[0].potential
    assert repeated.iterations == refs[0].iterations and repeated.integrations == refs[0].integrations


def test_identical_virgin_increment_converges_to_continuum(solutions):
    y,refs,discrete = solutions
    expected = refs[-1].coordinates[-1]-[1.,0.,0.]
    errors = [np.linalg.norm(t.positions[-1]-[1.,0.,0.]-expected)/np.linalg.norm(expected) for t in discrete]
    assert all(b<a for a,b in zip(errors,errors[1:]))
    assert errors[-1] < .02
    assert np.log2(errors[-2]/errors[-1]) > 1.8
    if y == .02:
        assert errors[0] > .3 and errors[2] > .05  # Preserve known coarse-mesh discrepancy.
    for trial in discrete:
        assert all(h.plastic_coordinate == 0 and h.accumulated == 0 for origin in trial.origins for h in origin)
        assert trial.residual_norm <= 1e-11
    energy_errors = [abs(t.response.potential-refs[-1].potential) for t in discrete]
    assert all(b<a for a,b in zip(energy_errors,energy_errors[1:]))


def test_eight_element_virgin_case_quadrature_sensitivity(solutions):
    y,_,discrete = solutions
    made = model(8,order=24,laws=[law(y) for _ in range(8)])
    high = made.trial(.1*forces(8))
    low = discrete[-1]
    assert np.linalg.norm(high.positions-low.positions) <= 1e-11
    assert np.linalg.norm(high.rotations-low.rotations) <= 1e-11
    assert abs(high.response.potential-low.response.potential) <= 1e-11
    assert [len(e.stations) for e in high.response.elements] == [48]*8


def test_bounded_failure_invalid_input_and_no_implicit_retry():
    solver = reference()
    for kwargs in ({'max_integrations':0},{'max_integrations':1},{'max_iterations':0}):
        with pytest.raises(continuum.ContinuumReferenceError,match='budget'):
            solver.solve([.01,-.03,.02],steps=32,**kwargs)
    for kwargs in ({'max_integrations':33},{'max_iterations':13},{'max_iterations':True},{'steps':1024}):
        with pytest.raises(continuum.ContinuumReferenceError):
            solver.solve([.01,-.03,.02],**kwargs)
    with pytest.raises(continuum.ContinuumReferenceError):
        solver.solve([np.nan,0.,0.])
    for h in (-1.,np.nan,.8,True):
        with pytest.raises(continuum.ContinuumReferenceError):
            reference(height=h)
