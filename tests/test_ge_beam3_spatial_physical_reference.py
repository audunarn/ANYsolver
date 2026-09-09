from copy import deepcopy
import numpy as np
import pytest
from scipy.linalg import expm
from docs.reference_cases.ge_beam3_spatial_second_variation import skew
from docs.reference_cases.ge_beam3_spatial_physical_reference import density,rates,validate_reference


def test_physical_inertia_frame_covariance_not_l2():
    r=expm(skew([.4,-.2,.8]));q=expm(skew([-.3,.7,.2]));s=np.kron(np.eye(2),q)
    np.testing.assert_allclose(density(q@r),s@density(r)@s.T,rtol=1e-11,atol=1e-11)
    assert np.linalg.eigvalsh(density(r))[0]>0
    np.testing.assert_allclose(np.linalg.eigvalsh(density(r)),[1e-5,2e-5,3e-5,1,1,1],rtol=1e-11)
    with pytest.raises(ValueError):density(np.diag([1.,1.,-1.]))


def profile():
    return dict(profiles=[dict(quadrature=q,modes_per_component=n,result=dict(eigenvalues=[-4.,1.,9.,16.,25.,36.]))
        for q,n in ((128,16),(128,24),(128,32),(64,32))])


def test_signed_growth_and_frequency_rates():
    np.testing.assert_array_equal(rates([-4.,1.,9.,16.,25.,36.]),[-2.,1.,3.,4.,5.,6.])
    assert validate_reference(profile())==(0.,0.)
    with pytest.raises(ValueError):rates([0.,1.,9.,16.,25.,36.])


@pytest.mark.parametrize('kind',('inventory','sign','refinement','quadrature','nan'))
def test_reference_profile_mutations(kind):
    v=profile()
    if kind=='inventory':v['profiles'].pop()
    elif kind=='sign':v['profiles'][0]['result']['eigenvalues'][0]=4.
    elif kind=='refinement':v['profiles'][1]['result']['eigenvalues'][1]=1.1
    elif kind=='quadrature':v['profiles'][3]['result']['eigenvalues'][1]=1.0001
    else:v['profiles'][0]['result']['eigenvalues'][0]=float('nan')
    with pytest.raises(ValueError):validate_reference(v)


@pytest.mark.parametrize('sign',('plus','minus'))
def test_saved_native_factor_and_endpoint_identity(sign):
    from docs.reference_cases.ge_beam3_spatial_physical_worker import inputs
    packet,mechanical=inputs(sign)
    assert len(packet['free_dofs'])==426 and 74 in packet['free_dofs']
    assert len(mechanical['cell_rotations'])==24
