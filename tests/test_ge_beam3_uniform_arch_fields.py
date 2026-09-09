"""Sampling guards and independent continuum reflection/work conventions."""
import numpy as np
import pytest
from docs.reference_cases.ge_beam3_uniform_arch_reference import sampling_sites,Reference,primitive
from docs.reference_cases.ge_beam3_uniform_arch_fields import fields


@pytest.mark.parametrize('values',[[],[-1.],[-1.,0.,0.],[-.5,0.],[-1.,.1],[-1.,float('nan'),0.],[-1.,True,0.],[-1.,'0'],[[-1.,0.]]])
def test_sample_rejection(values):
    with pytest.raises(ValueError):sampling_sites(values)


def test_sample_default_and_ownership():
    np.testing.assert_array_equal(sampling_sites(),np.linspace(-1.,0.,129))
    values=[-1.,-.4,0.];made=sampling_sites(values);values[1]=-.2
    np.testing.assert_array_equal(made,[-1.,-.4,0.])


def test_field_conventions():
    sites=np.array([-1.,-.4,0.]);y=np.array([sites,[0.,.06,.09],[.2,.1,0.],[.001,.002,.003]])
    ref=Reference(.01,.3,-.2,np.array([-.01,.0003]),sites,y,{})
    x=np.array([-.4,.4,0.]);out=fields(ref,x);q=out['frame'];s=out['resultants'];g=out['global_resultants']
    expected=np.column_stack((np.full(3,-10.),.3*primitive(x),np.zeros(3)))
    np.testing.assert_allclose(g[:,:3],expected,rtol=0,atol=1e-11)
    np.testing.assert_allclose(g[:,3:],[[0.,0.,2.],[0.,0.,2.],[0.,0.,3.]],rtol=0,atol=1e-11)
    np.testing.assert_allclose(q.transpose(0,2,1)@q,np.tile(np.eye(3),(3,1,1)),rtol=0,atol=1e-11)
    assert np.max(np.abs(np.linalg.det(q)-1.))<=1e-11
    a=np.sin(np.arange(18).reshape(3,6));global_a=np.column_stack((np.einsum('nij,nj->ni',q,a[:,:3]),np.einsum('nij,nj->ni',q,a[:,3:])))
    assert abs(float(np.sum(a*s)-np.sum(global_a*g)))<=1e-11
    np.testing.assert_array_equal(out['position'][0]*[-1.,1.,1.],out['position'][1])
    with pytest.raises(ValueError):fields(ref,[-.3])
