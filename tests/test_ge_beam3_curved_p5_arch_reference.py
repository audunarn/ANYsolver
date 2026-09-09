"""Continuum reference checks, no discrete beam qualification claims."""

import ast
from dataclasses import asdict
import inspect
import json

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_arch_reference as arch


def canonical(record):
    return (json.dumps(asdict(record),sort_keys=True,separators=(',',':'),allow_nan=False,
                       default=lambda v:v.tolist())+'\n').encode()


def test_equation_derivatives_match_complex_step():
    t = np.linspace(-1.,0.,7)
    y = np.array([t,.1*(1-t*t),.2*np.cos(t),.01*np.sin(t)])
    p = np.array([-.17,-.013])
    a,b = arch.derivatives(t,y,p,.1,1000.,400.,.01)
    for i in range(4):
        v = y.astype(complex);v[i]+=1e-25j
        observed = arch.equations(t,v,p,.1,1000.,400.,.01).imag/1e-25
        assert np.max(np.abs(observed-a[:,i,:]))<1e-11
    for i in range(2):
        v = p.astype(complex);v[i]+=1e-25j
        observed = arch.equations(t,y,v,.1,1000.,400.,.01).imag/1e-25
        assert np.max(np.abs(observed-b[:,i,:]))<1e-11


def test_stress_free_initial_arch_and_initial_stiffness():
    result = arch.solve(0.)
    t = result.parameter
    assert abs(result.load)<1e-10
    assert result.load_slope>0
    assert np.max(np.abs(result.fields[0]-t))<1e-10
    assert np.max(np.abs(result.fields[1]-.1*(1-t*t)))<1e-10
    assert result.strain_energy<1e-16
    assert result.production_qualified is False


@pytest.fixture(scope='module')
def fine_pair():
    return [arch.solve(d,profile='BVP9') for d in (.025,.05)]


def test_fine_reference_agrees_with_coarse_and_has_opposite_slopes(fine_pair):
    assert fine_pair[0].load_slope>0>fine_pair[1].load_slope
    for fine in fine_pair:
        coarse = arch.solve(fine.displacement,profile='BVP7')
        assert abs(fine.load/coarse.load-1)<1e-7
        assert abs(fine.load_slope-coarse.load_slope)<1e-7
        assert fine.boundary_error<=1e-11
        assert fine.differential_error<=1e-8 and fine.sensitivity_error<=1e-8
        assert fine.work_error<=1e-9
        assert fine.nodes<=4097 and fine.sensitivity_nodes<=4097
        assert fine.callbacks<=2000


def test_load_slope_and_energy_work_match_separate_displacement_perturbations(fine_pair):
    middle = fine_pair[1]
    h = 1e-5
    left = arch.solve(middle.displacement-h,previous=middle,profile='BVP9')
    right = arch.solve(middle.displacement+h,previous=middle,profile='BVP9')
    assert abs((right.load-left.load)/(2*h)-middle.load_slope)<1e-7
    assert abs((right.strain_energy-left.strain_energy)/(2*h)-middle.load)<1e-7


def test_spatial_moment_first_integral(fine_pair):
    for record in fine_pair:
        x,y,theta,m = record.fields
        conserved = m+x*record.force[1]-y*record.force[0]
        assert np.max(np.abs(conserved-conserved[0]))<1e-9


def test_bounded_limit_point_and_deterministic_recheck():
    left,right = arch.first_limit_point()
    assert left.load_slope>0>right.load_slope
    assert .025<left.displacement<right.displacement<.05
    assert right.displacement-left.displacement<1e-7
    assert abs(left.load-right.load)<1e-9 and left.load>0
    check = arch.solve(left.displacement,profile='BVP9')
    assert abs(check.load-left.load)<1e-9
    assert check.load_slope>0
    # Byte repeatability of one standalone solve, not a formal two-cycle run.
    assert canonical(check)==canonical(arch.solve(left.displacement,profile='BVP9'))


def test_reference_imports_no_discrete_producer_checker_or_production_code():
    tree = ast.parse(inspect.getsource(arch))
    imports = [n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    imports += [a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
    assert set(imports)=={'dataclasses','time','numpy','scipy.integrate'}


@pytest.mark.parametrize('kwargs',[{'max_callbacks':0},{'max_seconds':0}])
def test_budget_failure_yields_no_result_or_automatic_retry(kwargs):
    with pytest.raises(arch.ArchReferenceError,match='budget'):
        arch.solve(.025,**kwargs)


@pytest.mark.parametrize('kwargs',[{'height':0.},{'height':.3},{'axial':-1.},
                                 {'bending':float('nan')},{'profile':'unknown'},
                                 {'max_callbacks':True},{'max_seconds':61.}])
def test_invalid_reference_parameters_fail_closed(kwargs):
    with pytest.raises(ValueError):
        arch.solve(.025,**kwargs)


def test_limit_point_limits_and_incomplete_bracket_are_not_success():
    for kwargs in ({'iterations':True},{'iterations':25},{'max_seconds':float('nan')}):
        with pytest.raises(ValueError):
            arch.first_limit_point(**kwargs)
    with pytest.raises(arch.ArchReferenceError,match='width'):
        arch.first_limit_point(iterations=1)
