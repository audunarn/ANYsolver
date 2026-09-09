"""Small continuum mode and comparison checks; no nonlinear arch execution."""

import ast
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.linalg import expm

from docs.reference_cases import ge_beam3_curved_p5_arch_lateral_mode_reference as mode
from docs.reference_cases import ge_beam3_curved_p5_arch_lateral_mode_comparison as reader
from docs.reference_cases.ge_beam3_curved_p5_arch_lateral_reference import coefficients,jacobi
from docs.reference_cases import ge_beam3_curved_p5_lateral_knot_diagnostic as knots
from docs.reference_cases import ge_beam3_curved_p5_lateral_knot_revalidation as revalidator


def straight():
    g,ea,b=400.,1000.,.02
    target=np.pi**2*b;p=2*target/(1+np.sqrt(1+4*(1/g-1/ea)*target))
    h=jacobi(*coefficients(0.,1-p/ea,0.,-p,0.,0.,shear=g,bending=b))
    return h,p


def test_straight_neutral_shape_clamps_work_and_analytical_deflection(monkeypatch):
    h,p=straight();phi=expm(2*h)
    monkeypatch.setattr(mode,'arch_generator',lambda *args,**kwargs:lambda t,i:h)
    reference=SimpleNamespace(height=0.,displacement=0.,load=p)
    endpoint={'transfer':phi,'displacement':0.,'load':p,'reference_stride':1}
    result=mode.shape(reference,endpoint)
    assert result['end_error']<1e-8 and result['transfer_error']<1e-8
    assert result['work_error']<1e-9
    assert abs(result['energy_integral_normalized'])<1e-8
    q=result['nodal_increment'];z=q[:,2]
    expected=1-np.cos(np.pi*(result['parameters']+1))
    assert np.linalg.norm(z/z[16]-expected/2)<1e-8
    assert np.all(q[:,[0,1,5]]==0)
    assert not result['natural_frequencies_computed'] and not result['production_qualified']


def test_linear_integration_matches_constant_exponential_and_boundary_work():
    h=jacobi(*coefficients(.1,.99,.03,-.1,-.01,.002))
    initial=np.array([.2,-.1,.3])
    result=mode.integrate(lambda t,i:h,initial)
    assert np.allclose(result['states'][-1],expm(2*h)@np.r_[np.zeros(3),initial],rtol=1e-9,atol=1e-9)
    assert result['work_error']<1e-9
    assert np.array_equal(result['parameters'],np.linspace(-1.,1.,33))


@pytest.mark.parametrize('kwargs',[{'nodes':257},{'nodes':True},{'max_seconds':31.},{'max_callbacks':10001}])
def test_bounds_reject_before_integration(kwargs):
    def forbidden(*args): raise AssertionError('no callback before valid bounds')
    with pytest.raises(ValueError): mode.integrate(forbidden,[1.,0.,0.],**kwargs)


def test_zero_budget_has_no_automatic_retry():
    calls=[]
    def forbidden(*args): calls.append(1);raise AssertionError('budget must precede callback')
    with pytest.raises(mode.LateralReferenceError,match='budget'):
        mode.integrate(forbidden,[1.,0.,0.],max_callbacks=0)
    with pytest.raises(mode.LateralReferenceError,match='budget'):
        mode.integrate(forbidden,[1.,0.,0.],max_seconds=0)
    assert calls==[]


def test_missing_neutrality_and_wrong_endpoint_fail_before_field_integration():
    phi=np.eye(6);phi[:3,3:]=np.eye(3)
    ref=SimpleNamespace(height=.1,displacement=.04,load=.03)
    endpoint={'transfer':phi,'displacement':.04,'load':.03,'reference_stride':1}
    with pytest.raises(mode.LateralReferenceError,match='near-neutral'): mode.shape(ref,endpoint)
    endpoint['displacement']=.05
    with pytest.raises(ValueError,match='identity'): mode.shape(ref,endpoint)


def test_reference_trapezoid_weights_and_invalid_order():
    t=np.linspace(-1.,1.,33);w=mode.weights(t,height=0.)
    assert np.sum(w)==2 and w[0]==w[-1]==1/32 and np.all(w[1:-1]==1/16)
    assert np.sum(mode.weights(t,height=.1))>2
    with pytest.raises(ValueError): mode.weights(t[::-1])


def shapes():
    t=np.linspace(-1.,1.,33);a=np.zeros((33,6));a[:,2]=1-t*t;a[:,3]=t*(1-t*t)
    return a,mode.weights(t)


def test_shape_measure_is_amplitude_sign_invariant_not_mass_mac():
    a,w=shapes();result=mode.compare(a,-7*a,w)
    for key in ('combined','translation','rotation'):
        assert abs(result[key]['squared_cosine']-1)<1e-12
        assert result[key]['sign_aligned_distance']<1e-12
    assert not result['physical_mass_mac'] and not result['qualification_gate']


def test_component_comparisons_expose_mismatch_hidden_by_other_coordinates():
    a,w=shapes();b=a.copy();b[:,2]*=np.linspace(-1.,1.,33)
    result=mode.compare(a,b,w)
    assert result['translation']['squared_cosine']<1e-10
    assert result['translation']['sign_aligned_distance']==pytest.approx(np.sqrt(2))
    assert result['rotation']['squared_cosine']==pytest.approx(1.)


@pytest.mark.parametrize('mutation',['zero','nonfinite','weights','shape'])
def test_invalid_comparison_rejected(mutation):
    a,w=shapes();b=a.copy()
    if mutation=='zero': b[:]=0
    if mutation=='nonfinite': b[2,2]=np.nan
    if mutation=='weights': w[0]=0
    if mutation=='shape': b=b[:-1]
    with pytest.raises((ValueError,mode.LateralReferenceError)): mode.compare(a,b,w)


def test_input_byte_hash_guard(tmp_path):
    path=tmp_path/'input.json';path.write_bytes(b'{"value":1}\n')
    binding=(path.stat().st_size,reader.sha(path.read_bytes()))
    assert reader.bound(path,binding)=={'value':1}
    path.write_bytes(b'{"value":2}\n')
    with pytest.raises(reader.RefinementError,match='hash'): reader.bound(path,binding)
    with pytest.raises(reader.RefinementError): reader.bound(path,(1,binding[1]))


def test_reference_does_not_import_or_read_discrete_mechanics():
    modules=[]
    for node in ast.walk(ast.parse(Path(mode.__file__).read_text())):
        if isinstance(node,ast.Import): modules.extend(a.name for a in node.names)
        if isinstance(node,ast.ImportFrom): modules.append(node.module)
    assert set(modules)=={'time','numpy','scipy.integrate',
                         'docs.reference_cases.ge_beam3_curved_p5_arch_lateral_reference'}
    top=ast.parse(Path(reader.__file__).read_text()).body
    assert not any(isinstance(n,(ast.Import,ast.ImportFrom)) and 'numpy' in ast.unparse(n) for n in top)


def test_every_coefficient_knot_is_an_integration_boundary(monkeypatch):
    calls=[];original=mode.solve_ivp;h,_=straight()
    def record(fun,bounds,*args,**kwargs):
        calls.append(bounds)
        assert kwargs['rtol']==1e-11 and kwargs['atol']==1e-13
        return original(fun,bounds,*args,**kwargs)
    monkeypatch.setattr(mode,'solve_ivp',record)
    result=mode.integrate(lambda t,i:h,[0.,0.,1.])
    expected=np.linspace(-1.,1.,257)
    assert calls==list(zip(expected[:-1],expected[1:]))
    assert result['coefficient_half_nodes']==129 and result['callbacks']<=10000


def test_knot_matrix_vector_linearity_and_refinement():
    def generator(t,i):
        angle=.2*np.sin(3*t)
        return jacobi(*coefficients(angle,.99,.03,-.1,-.01,.002))
    vector=np.r_[np.zeros(3),[.2,-.1,.3]]
    a=knots.propagate(generator,np.eye(6));b=knots.propagate(generator,vector)
    assert np.allclose(b['endpoint'],a['endpoint']@vector,rtol=1e-11,atol=1e-11)
    c=mode.integrate(generator,vector[3:])
    assert np.allclose(c['states'][-1],b['endpoint'],rtol=1e-11,atol=1e-11)


def test_knot_profile_and_legacy_input_guard(tmp_path):
    with pytest.raises(ValueError): knots.propagate(lambda *args:np.eye(6),np.eye(6),half_nodes=513)
    with pytest.raises(RuntimeError,match='budget'):
        knots.propagate(lambda *args:np.eye(6),np.eye(6),max_callbacks=0)
    path=tmp_path/'bad.json';path.write_bytes(b'{}\n')
    with pytest.raises(revalidator.RefinementError,match='hash'): revalidator.revalidate(path,1)
    with pytest.raises(ValueError): revalidator.revalidate(path,True)
