"""Small independent continuum/algebra checks; no discrete mechanics import."""

import ast
from fractions import Fraction as F
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.linalg import expm

from docs.reference_cases import ge_beam3_curved_p5_arch_lateral_reference as lateral
from docs.reference_cases.ge_beam3_curved_p5_arch_reference import solve as base


def cross(a,b): return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def dot(a,b): return sum(x*y for x,y in zip(a,b))


def test_coefficient_quadratic_form_against_rational_so3_variations():
    c,s=F(3,5),F(4,5)
    directors=[[c,s,0],[0,0,1],[s,-c,0]]
    v=[F(7,8),F(-1,9),0];force=[F(-2,7),F(1,11),0];moment=F(3,17)
    stiffness=[F(5,2),F(3,13),F(2,19)]
    matrices=lateral.coefficients(np.arctan2(float(s),float(c)),*map(float,v[:2]),
        *map(float,force[:2]),float(moment),shear=float(stiffness[0]),
        torsion=float(stiffness[1]),bending=float(stiffness[2]))
    samples=[[F(int(i==j)) for i in range(6)] for j in range(6)]
    samples += [[F((i+1)*(j+2)-7,11) for i in range(6)] for j in range(8)]
    for values in samples:
        u,up=values[:3],values[3:];w=[u[1],u[2],0];wp=[up[1],up[2],0];rp=[0,0,up[0]]
        delta=[x-y for x,y in zip(rp,cross(w,v))]
        second=[x-2*y for x,y in zip(cross(w,cross(w,v)),cross(w,rp))]
        e1=[dot(d,delta) for d in directors];e2=[dot(d,second) for d in directors]
        k1=[dot(d,wp) for d in directors];k2=[-dot(d,cross(w,wp)) for d in directors]
        n=[dot(d,force) for d in directors]
        expected=stiffness[0]*e1[1]**2+stiffness[1]*k1[0]**2+stiffness[2]*k1[2]**2+dot(n,e2)+moment*k2[1]
        a,b,d=matrices;x,y=np.array(u,dtype=float),np.array(up,dtype=float)
        actual=y@a@y+2*x@b@y+x@d@x
        assert abs(actual-float(expected))<=1e-13*max(1.,abs(float(expected)))


def test_spatial_moment_balance_reconstructs_from_symmetric_second_variation():
    vx,vy,fx,fy,m=.8,.1,-.4,-.02,.003
    a,b,c=lateral.coefficients(.3,vx,vy,fx,fy,m,torsion=.07,bending=.02)
    h=lateral.jacobi(a,b,c)
    value=np.array([.2,-.1,.3,.05,.02,-.03]);derivative=h@value
    moment_prime=vy*fx-vx*fy
    dm=derivative[4:]+.5*np.array([moment_prime*value[2]+m*derivative[2],
                                 -moment_prime*value[1]-m*derivative[1]])
    physical_balance=dm+np.array([-fy*derivative[0]+vy*value[3],fx*derivative[0]-vx*value[3]])
    assert np.max(np.abs(physical_balance))<1e-13
    assert derivative[3]==0 # Incremental out-of-plane spatial force is constant.
    j=np.block([[np.zeros((3,3)),np.eye(3)],[-np.eye(3),np.zeros((3,3))]])
    assert np.max(np.abs(h.T@j+j@h))<1e-12


def test_straight_unstressed_transfer_and_separate_exponential():
    length,g,t,b=2.,400.,.03,.02
    h=lateral.jacobi(*lateral.coefficients(0.,1.,0.,0.,0.,0.,shear=g,torsion=t,bending=b))
    result=lateral.transfer(lambda x,i:h,breaks=(0.,length),profile='IVP11')
    expected=np.array([[length/g-length**3/(6*b),0.,-length**2/(2*b)],
                       [0.,length/t,0.],[length**2/(2*b),0.,length/b]])
    assert np.allclose(result['boundary_matrix'],expected,rtol=1e-10,atol=1e-10)
    assert np.allclose(result['transfer'],expm(length*h),rtol=1e-10,atol=1e-10)
    assert result['normalized_determinant']>0
    assert not result['production_qualified']


def test_straight_compression_neutral_condition_and_sign_change():
    length,g,ea,b=2.,400.,1000.,.02
    target=4*np.pi**2*b/length**2
    critical=2*target/(1+np.sqrt(1+4*(1/g-1/ea)*target))
    signs=[]
    for factor in (.95,1.,1.05):
        p=factor*critical
        h=lateral.jacobi(*lateral.coefficients(0.,1-p/ea,0.,-p,0.,0.,shear=g,bending=b))
        result=lateral.transfer(lambda x,i:h,breaks=(0.,length),profile='IVP11')
        signs.append(result['normalized_determinant'])
        if factor==1: assert result['singular_ratio']<1e-9
    assert signs[0]>0>signs[2] and abs(signs[1])<1e-9


@pytest.mark.parametrize('force',[0.,.1,.2])
def test_unloaded_and_tension_straight_boundary_is_not_neutral(force):
    h=lateral.jacobi(*lateral.coefficients(0.,1+force/1000,0.,force,0.,0.))
    result=lateral.transfer(lambda x,i:h,breaks=(0.,2.))
    assert result['normalized_determinant']>0 and result['singular_ratio']>1e-5


def test_exact_piecewise_transfer_keeps_crown_boundary():
    left=lateral.jacobi(*lateral.coefficients(.1,1.,.05,-.1,-.02,.001))
    right=lateral.jacobi(*lateral.coefficients(-.1,1.,-.05,-.1,.02,.001))
    result=lateral.transfer(lambda x,i:(left,right)[i],profile='IVP11')
    expected=expm(right)@expm(left)
    assert np.allclose(result['transfer'],expected,rtol=1e-9,atol=1e-9)
    assert [r['interval'] for r in result['intervals']]==[[-1.,0.],[0.,1.]]


@pytest.mark.parametrize('small',[0.,1e-14,-1e-14])
def test_vanishing_boundary_column_is_not_normalized_away(small):
    phi=np.eye(6);phi[:3,3:]=np.diag([2.,1.,small])
    result=lateral.boundary_measure(phi)
    assert result['singular_ratio']<=5e-15
    assert np.sign(result['normalized_determinant'])==np.sign(small)


@pytest.mark.parametrize('kwargs',[{'shear':0.},{'torsion':-1.},{'bending':np.nan}])
def test_invalid_section_rejected(kwargs):
    with pytest.raises(ValueError): lateral.coefficients(0.,1.,0.,0.,0.,0.,**kwargs)


@pytest.mark.parametrize('kwargs',[{'profile':'retry'},{'max_callbacks':10001},{'max_seconds':31.}])
def test_invalid_bounds_rejected(kwargs):
    with pytest.raises(ValueError): lateral.transfer(lambda x,i:np.zeros((6,6)),**kwargs)


def test_zero_budgets_and_invalid_generator_fail_without_retry():
    def forbidden(*args): raise AssertionError('budget before evaluation')
    for kwargs in ({'max_callbacks':0},{'max_seconds':0.}):
        with pytest.raises(lateral.LateralReferenceError,match='budget'): lateral.transfer(forbidden,**kwargs)
    with pytest.raises(lateral.LateralReferenceError,match='Hamiltonian'):
        lateral.transfer(lambda x,i:np.eye(6))


def test_base_field_guard_and_mirror():
    reference=base(.01,profile='BVP9')
    generator=lateral.arch_generator(reference)
    reflection=np.diag([1.,1.,-1.,-1.,-1.,1.]) # x-reversal maps u=(z,wx,wy); momenta flip.
    assert np.allclose(generator(.3,1),-reflection@generator(-.3,0)@reflection,rtol=0,atol=1e-11)
    for x,index in ((.1,0),(-.1,1),(2.,1)):
        with pytest.raises(ValueError): generator(x,index)
    with pytest.raises(ValueError): lateral.arch_generator(reference,stride=3)


def test_reference_imports_no_discrete_beam_operators():
    modules=[]
    for node in ast.walk(ast.parse(Path(lateral.__file__).read_text())):
        if isinstance(node,ast.Import): modules.extend(a.name for a in node.names)
        if isinstance(node,ast.ImportFrom): modules.append(node.module)
    assert set(modules)=={'dataclasses','time','numpy','scipy.integrate','scipy.interpolate',
                         'docs.reference_cases.ge_beam3_curved_p5_arch_reference'}


def test_root_failure_retains_trace_without_search_extension(monkeypatch):
    calls=[]
    def fake(d,**kwargs):
        calls.append(d)
        if len(calls)>1: raise RuntimeError('injected second reference failure')
        return SimpleNamespace(displacement=d)
    monkeypatch.setattr(lateral,'planar_solve',fake)
    monkeypatch.setattr(lateral,'solve',lambda ref,**kwargs:{'displacement':ref.displacement,'load':1.,
        'normalized_determinant':1.,'singular_ratio':.1,'callbacks':1})
    with pytest.raises(lateral.LateralReferenceError) as caught: lateral.neutral_bracket()
    assert calls==[.044820372353098756,.05]
    assert len(caught.value.completed_trace)==1


def test_absent_root_bracket_is_not_automatically_expanded(monkeypatch):
    calls=[]
    def fake(d,**kwargs): calls.append(d);return SimpleNamespace(displacement=d)
    monkeypatch.setattr(lateral,'planar_solve',fake)
    monkeypatch.setattr(lateral,'solve',lambda ref,**kwargs:{'displacement':ref.displacement,'load':1.,
        'normalized_determinant':1.,'singular_ratio':.1,'callbacks':1})
    with pytest.raises(lateral.LateralReferenceError,match='bracket is absent'): lateral.neutral_bracket()
    assert calls==[.044820372353098756,.05]


@pytest.mark.parametrize('kwargs',[{'iterations':21},{'iterations':True},{'max_seconds':31.},{'stride':3}])
def test_root_bounds_fail_before_evaluation(monkeypatch,kwargs):
    def forbidden(*args,**kw): raise AssertionError('no base evaluation')
    monkeypatch.setattr(lateral,'planar_solve',forbidden)
    with pytest.raises(ValueError): lateral.neutral_bracket(**kwargs)
