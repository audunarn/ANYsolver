"""Separate first-integral, ODE and elliptic checks; no beam imports."""

import ast
from dataclasses import asdict
import json
import math
from pathlib import Path

import numpy as np
import pytest
from scipy.integrate import solve_ivp
from scipy.special import ellipk, ellipe

from docs.reference_cases import ge_beam3_curved_p5_postcritical_reference as reference


@pytest.mark.parametrize('angle',[.1,.6,1.2,math.pi/2])
def test_equal_axial_shear_stiffness_has_independent_elliptic_solution(angle):
    length,stiffness,ei = 2.,1000.,1.
    result = reference.solve(length,stiffness,stiffness,ei,angle)
    k = math.sin(angle/2)
    K,E = ellipk(k*k),ellipe(k*k)
    force = ei*(K/length)**2
    x = length*(2*E/K-1)-force*length/stiffness
    y = 2*k*length/K
    energy = .5*force**2*length/stiffness+force*length*(2*E/K-1-math.cos(angle))
    assert abs(result.load-force)<1e-12
    assert np.linalg.norm(result.coordinates[-1]-[x,y])<1e-12
    assert abs(result.strain_energy-energy)<1e-12


@pytest.mark.parametrize('angle',[.1,.6,1.2])
def test_separate_reference_arclength_ode_matches_first_integral(angle):
    length,ea,ga,ei = 2.,1000.,400.,1.
    result = reference.solve(length,ea,ga,ei,angle)
    load = result.load
    # Integrate directly in s, not the angle substitution/quadrature used by
    # the reference. This does not import any discrete element implementation.
    def rhs(s,z):
        theta,m,x,y,energy = z
        n,q = -load*np.cos(theta),load*np.sin(theta)
        eps,gamma,kappa = n/ea,q/ga,m/ei
        dx = (1+eps)*np.cos(theta)-gamma*np.sin(theta)
        dy = (1+eps)*np.sin(theta)+gamma*np.cos(theta)
        dm = -load*dy
        return [kappa,dm,dx,dy,.5*(n*eps+q*gamma+m*kappa)]
    count = [0]
    def bounded(s,z):
        count[0]+=1
        if count[0]>5000:
            raise RuntimeError('ODE evaluation bound')
        return rhs(s,z)
    solved = solve_ivp(bounded,(0.,length),[0.,result.moments[0],0.,0.,0.],
        method='DOP853',rtol=2e-13,atol=2e-14,t_eval=result.arclength)
    assert solved.success
    assert np.max(np.abs(solved.y[0]-result.angles))<1e-11
    assert np.max(np.abs(solved.y[1]-result.moments))<1e-11
    assert np.max(np.abs(solved.y[2:4].T-result.coordinates))<1e-11
    assert abs(solved.y[4,-1]-result.strain_energy)<1e-11
    assert abs(solved.y[1,-1])<1e-11


def test_critical_load_matches_source_98_and_small_amplitude_limit():
    length,ea,ga,ei = 2.,1000.,400.,1.
    slender2 = length**2/(ei*(1/ga+1/ea))
    nu = (ga-ea)/(ga+ea)
    beta = 1/(2*(1+math.sqrt(1-math.pi**2*nu/slender2)))
    source = beta*math.pi**2*ei/length**2
    actual = reference.critical_load(length,ea,ga,ei)
    assert abs(actual-source)<1e-15
    tiny = reference.solve(length,ea,ga,ei,1e-5)
    assert abs(tiny.load/actual-1)<2e-11
    assert actual<ei*(math.pi/(2*length))**2


def test_quadrature_convergence_work_balance_and_serialization():
    a = reference.solve(2.,1000.,400.,1.,.8,order=32)
    b = reference.solve(2.,1000.,400.,1.,.8,order=64)
    c = reference.solve(2.,1000.,400.,1.,.8,order=128)
    for result in (a,b,c):
        assert result.load>result.critical_load
        assert result.length_residual<1e-12 and result.moment_balance_residual<1e-11
        assert np.all(np.diff(result.angles)>0)
        assert result.angles[0]==0 and result.moments[-1]==0
        assert np.all(result.strains[:,0]>-1)
        assert np.max(np.abs(result.resultants-result.strains*np.array([1000.,400.,1.])))<1e-14
    assert np.linalg.norm(a.coordinates-c.coordinates)<1e-11
    assert np.linalg.norm(b.coordinates-c.coordinates)<1e-11
    encode = lambda r: json.dumps(asdict(r),sort_keys=True,separators=(',',':'),allow_nan=False,
        default=lambda v:v.tolist())
    assert encode(b)==encode(reference.solve(2.,1000.,400.,1.,.8,order=64))


@pytest.mark.parametrize('args,kwargs',[
    ((0.,1000.,400.,1.,.5),{}), ((2.,400.,1000.,1.,.5),{}),
    ((2.,1000.,400.,1.,0.),{}), ((2.,1000.,400.,1.,2.),{}),
    ((2.,1000.,400.,1.,float('nan')),{}), ((2.,1000.,400.,1.,.5),{'order':16}),
    ((2.,1000.,400.,1.,.5),{'stations':100}), ((2.,1000.,400.,1.,.5),{'max_bisections':0}),
    ((2.,.01,.01,1.,.5),{}), ((True,1000.,400.,1.,.5),{}),
    (('2',1000.,400.,1.,.5),{}), ((2.,1000.,400.,1.,None),{}),
])
def test_input_domain_and_solver_limits(args,kwargs):
    with pytest.raises(reference.PostcriticalReferenceError):
        reference.solve(*args,**kwargs)


def test_source_import_independence():
    tree = ast.parse(Path(reference.__file__).read_text())
    imports = [n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    imports += [a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
    assert set(imports)=={'dataclasses','math','numpy'}
