"""Small analytical prestress and coarse critical-load diagnostic tests."""

import numpy as np
import pytest

from docs.reference_cases import ge_beam3_curved_p5_prestress_probe as prestress
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import NonlinearMixedBeamProbe


@pytest.fixture(scope='module')
def critical_family():
    records = [prestress.critical(count) for count in (1,2,4,8)]
    for record in records:
        print('CRITICAL_DIAGNOSTIC',record)
    return records


def test_coarse_critical_brackets_explain_only_one_element_load_mismatch(critical_family):
    one,two,_,_ = critical_family
    comparison_load = .6449785996190569
    assert one['lower']>comparison_load>two['upper']
    assert 0<two['relative_error']<one['relative_error']
    assert all(r['upper']-r['lower']<1e-8*r['continuum'] for r in critical_family)
    assert all(r['production_qualified'] is False for r in critical_family)
    errors = [r['relative_error'] for r in critical_family]
    assert all(a>b>0 for a,b in zip(errors,errors[1:]))
    assert errors[-1]<.02


@pytest.mark.parametrize('count',[1,2,4,8])
def test_comparison_load_local_and_global_signs_are_distinct(count):
    r = prestress.evaluate(count,.6449785996190569)
    smallest = np.linalg.eigvalsh(r.tangent[np.ix_(r.free,r.free)])[0]
    assert (smallest>0)==(count==1)
    assert r.minimum_moment_block>0 and r.minimum_rotation_block>0
    assert r.equilibrium_error<1e-11 and r.local_residual<1e-11


def test_prestress_never_runs_local_newton(monkeypatch):
    def forbidden(*a,**k):
        raise AssertionError('analytical prestress must not rerun a local solve')
    monkeypatch.setattr(NonlinearMixedBeamProbe,'solve',forbidden)
    for load in (-.5,0.,.5):
        r = prestress.evaluate(2,load)
        assert r.equilibrium_error<1e-11


def test_tension_stiffens_and_compression_destabilizes_transverse_mode():
    records = [prestress.evaluate(2,p) for p in (-.5,0.,.5)]
    node_count = 5
    # In-plane y translations and z rotations, with the first node clamped.
    plane = (6*np.arange(1,node_count)[:,None]+np.array([1,5])).ravel()
    values = [np.linalg.eigvalsh(r.tangent[np.ix_(plane,plane)])[0] for r in records]
    assert values[0]>values[1]>values[2]>0
    for r in records:
        assert np.linalg.norm(r.tangent-r.tangent.T)<1e-11*np.linalg.norm(r.tangent)


def test_resource_and_physical_bounds():
    for count,load in ((3,0.),(1,1000.),(True,0.)):
        with pytest.raises(ValueError):
            prestress.evaluate(count,load)
    with pytest.raises(ValueError):
        prestress.critical(1,iterations=41)
    with pytest.raises(prestress.PrestressError,match='budget'):
        prestress.critical(1,iterations=0)


def test_critical_sign_brackets_survive_direct_recheck(critical_family):
    for result in critical_family:
        for key,positive in (('lower',True),('upper',False)):
            r = prestress.evaluate(result['elements'],result[key])
            k = r.tangent[np.ix_(r.free,r.free)]
            # Use the registered initial-diagonal congruence, not a new
            # coordinate-scaled eigensolver at this very narrow sign bracket.
            initial = prestress.evaluate(result['elements'],0.)
            scale = 1/np.sqrt(np.diag(initial.tangent)[r.free])
            k = k*scale[:,None]*scale[None,:]
            assert (np.linalg.eigvalsh(k)[0]>0)==positive


def test_local_block_failure_not_reported_as_global_buckling(monkeypatch):
    from dataclasses import replace
    original = NonlinearMixedBeamProbe.evaluate
    def corrupt(self,*args,**kwargs):
        result = original(self,*args,**kwargs)
        h = result.hessian.copy();h[24,24] = abs(h[24,24])
        return replace(result,hessian=h)
    monkeypatch.setattr(NonlinearMixedBeamProbe,'evaluate',corrupt)
    with pytest.raises(prestress.PrestressError,match='local stationary'):
        prestress.evaluate(1,.1)
