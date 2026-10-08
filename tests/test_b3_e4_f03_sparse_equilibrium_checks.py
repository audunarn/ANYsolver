"""Bounded analytical sparse identities, without scientific equilibrium cases."""
from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_sparse_certificate as shared
from scripts import _b3_e4_f03_sparse_state_binding as binding
from scripts import _b3_e4_f03_sparse_equilibrium_checks as check
from scripts import _b3_e4_f03_spatial_contract as c


def _budget(**changes):
    sb=shared.SparseBudget(32,512,3,2_000_000)
    bb=binding.BindingBudget(sb,1024,8192,8_000_000,32*1024**2)
    return replace(check.EquilibriumBudget(bb,1024,8192,12_000_000,
                                           48*1024**2),**changes)


def _fixture(*,zero_shell=False):
    shell=sparse.diags([0. if zero_shell else 1e7]*4,format='csr')
    beam=sparse.diags([1e7]*4,format='csr')
    root=sparse.csr_matrix(np.eye(3,4))
    stiffness=shell+beam
    d=np.sqrt(c.E0/stiffness.diagonal())
    r=np.array((1/c.U0,1/c.U0,.46/c.U0))
    kbar=((stiffness.toarray()*d[:,None])*d[None,:])/c.E0
    cbar=(root.toarray()*r[:,None])*d[None,:]
    h=sparse.csr_matrix(np.block([[kbar,cbar.T],[cbar,np.zeros((3,3))]]))
    z=np.array([0.,0.,0.,.25,0.,0.,0.])
    f=np.zeros(4);f[3]=stiffness.diagonal()[3]*(d[3]*z[3])
    b=np.r_[d*f/c.E0,np.zeros(3)]
    q=d*z[:4];eta=c.E0*r*z[4:]
    return [shell,beam,shell.copy(),beam.copy(),root,f,d,h,b,q,eta,z,h@z]


def _verify(data,**kwargs):
    return check.verify_equilibrium(*data,budget=_budget(),**kwargs)


def test_all_five_numerical_checks_pass_with_exact_zero_comparisons():
    data=_fixture()
    result=_verify(data)
    assert result['status']=='NUMERICAL_MECHANICAL_CHECKS_PASSED'
    assert result['binding']['status']=='BINDING_PASSED'
    assert not result['failures']
    assert all(value['squared']==0 for value in result['integration_blocks'].values())
    assert all(value['squared']==0 for value in result['skew_blocks'].values())
    assert result['checks']['root_compatibility_scaled']==0
    assert result['checks']['energy_identity_scaled']<=1e-10
    assert result['work']['new_equilibrium_solves']==0
    digest=result['input_sha256']['K_shell_plus']
    data[2].data[0]+=100.
    assert result['input_sha256']['K_shell_plus']==digest


def test_individual_integration_blocks_fail_even_if_combined_cancels():
    data=_fixture()
    plus=data[2].tolil();plus[0,0]+=0.001;data[2]=plus.tocsr()
    plus=data[3].tolil();plus[0,0]-=0.001;data[3]=plus.tocsr()
    result=_verify(data)
    assert result['status']=='HOLD'
    assert not result['integration_blocks']['shell']['within_limit']
    assert not result['integration_blocks']['beam']['within_limit']
    assert result['integration_blocks']['combined']['squared']==0
    assert all(value['within_limit'] for value in result['skew_blocks'].values())


def test_six_scaled_skews_are_independently_checked_without_averaging():
    data=_fixture()
    plus=data[2].tolil();plus[0,1]=.001;data[2]=plus.tocsr()
    result=_verify(data)
    assert result['status']=='HOLD'
    assert not result['skew_blocks']['shell_plus']['within_limit']
    assert not result['skew_blocks']['combined_plus']['within_limit']
    assert result['skew_blocks']['shell']['squared']==0
    assert result['skew_blocks']['beam']['squared']==0


def test_zero_shell_absolute_integration_and_skew_gate():
    data=_fixture(zero_shell=True)
    assert _verify(data)['status']=='NUMERICAL_MECHANICAL_CHECKS_PASSED'
    plus=sparse.diags([1e-12,0.,0.,0.],format='csr')
    data[2]=plus
    result=_verify(data)
    expected=F.from_float(float(((1e-12*data[6][0])*data[6][0])/c.E0))**2
    assert result['integration_blocks']['shell']['squared']==expected
    # Exact own-norm rule: the zero shell has an absolute scaled comparison.
    assert result['integration_blocks']['shell']['squared']>0
    assert result['integration_blocks']['shell']['within_limit']
    assert result['skew_blocks']['shell']['upper']==0


@pytest.mark.parametrize('kind',('stationarity','root','energy'))
def test_saved_numerical_residuals_independently_expose_bad_state(kind):
    data=_fixture()
    if kind=='stationarity':
        data[8]=data[8].copy();data[8][3]+=1e-7
    elif kind=='root':
        data[11]=data[11].copy();data[11][0]=.001
        data[9]=data[6]*data[11][:4]
        data[12]=data[7]@data[11]
    else:
        data[5]=data[5].copy();data[5][3]+=100.
        data[8]=np.r_[data[6]*data[5]/c.E0,np.zeros(3)]
    result=_verify(data)
    assert result['status']=='HOLD'
    assert result['checks'][dict(stationarity='stationarity_scaled',
        root='root_compatibility_scaled',energy='energy_identity_scaled')[kind]]>1e-10


def test_exact_small_dense_fraction_oracle_for_energy_and_stationarity():
    data=_fixture()
    result=_verify(data)
    ks,kb,_,_,_,f,_,h,b,q,_,z,_=data
    qf=[F.from_float(float(x)) for x in q]
    energy=sum(qf[i]*F.from_float(float((ks+kb)[i,i]))*qf[i]
               for i in range(4))
    load=sum(F.from_float(float(f[i]))*qf[i] for i in range(4))
    expected=abs(energy-load)/max(F.from_float(c.E0),abs(energy),abs(load))
    assert result['raw']['energy_identity_ratio_exact']==expected
    residual=max(abs(sum(F.from_float(float(h[i,j]))*
                         F.from_float(float(z[j])) for j in range(7))-
                     F.from_float(float(b[i]))) for i in range(4))
    assert result['raw']['primal_residual_max_exact']==residual


def test_symmetric_physical_block_can_have_nonzero_rounded_scaled_skew():
    data=_fixture()
    # Different diagonal scalings make the two independently rounded stored
    # entries differ even though this physical shell block is symmetric.
    shell=sparse.diags([1e7,3e7,5e7,7e7],format='lil')
    shell[0,1]=shell[1,0]=.1
    data[0]=shell.tocsr();data[2]=data[0].copy()
    stiffness=data[0]+data[1]
    d=np.sqrt(c.E0/stiffness.diagonal());data[6]=d
    root=data[4].toarray();r=np.array((1/c.U0,1/c.U0,.46/c.U0))
    k=stiffness.toarray()
    kbar=((k*d[:,None])*d[None,:])/c.E0
    cbar=(root*r[:,None])*d[None,:]
    data[7]=sparse.csr_matrix(np.block([[kbar,cbar.T],[cbar,np.zeros((3,3))]]))
    data[9]=d*data[11][:4]
    data[5]=stiffness.diagonal()*data[9]
    data[8]=np.r_[d*data[5]/c.E0,np.zeros(3)]
    data[12]=data[7]@data[11]
    result=_verify(data)
    left=F.from_float(float(((.1*d[0])*d[1])/c.E0))
    right=F.from_float(float(((.1*d[1])*d[0])/c.E0))
    assert left!=right
    assert result['skew_blocks']['shell']['squared']>0
    assert result['skew_blocks']['shell']['within_limit']
    scaled=data[0].toarray()
    scaled=((scaled*d[:,None])*d[None,:])/c.E0
    exact_norm=sum(F.from_float(float(v))**2 for v in scaled.flat)
    exact_skew=sum((F.from_float(float(scaled[i,j]))-
                    F.from_float(float(scaled[j,i])))**2
                   for i in range(4) for j in range(4))
    assert result['skew_blocks']['shell']['squared']==exact_skew/exact_norm


def test_separate_shell_beam_energy_retains_lost_rounded_combined_entry():
    data=_fixture()
    shell=data[0].tolil();shell[3,3]=1e16;data[0]=shell.tocsr()
    beam=data[1].tolil();beam[3,3]=1.;data[1]=beam.tocsr()
    data[2]=data[0].copy();data[3]=data[1].copy()
    stiffness=data[0]+data[1]
    d=np.sqrt(c.E0/stiffness.diagonal());data[6]=d
    root=data[4].toarray();r=np.array((1/c.U0,1/c.U0,.46/c.U0))
    k=stiffness.toarray();kbar=((k*d[:,None])*d[None,:])/c.E0
    cbar=(root*r[:,None])*d[None,:]
    data[7]=sparse.csr_matrix(np.block([[kbar,cbar.T],[cbar,np.zeros((3,3))]]))
    data[9]=d*data[11][:4]
    data[5]=stiffness.diagonal()*data[9]
    data[8]=np.r_[d*data[5]/c.E0,np.zeros(3)]
    data[12]=data[7]@data[11]
    result=_verify(data)
    q=F.from_float(float(data[9][3]))
    separate=(F.from_float(1e16)+F.from_float(1.))*q*q
    combined=F.from_float(float(stiffness[3,3]))*q*q
    assert separate!=combined
    assert result['raw']['physical_strain_work_exact']==separate


def test_caller_mutation_after_binding_does_not_change_later_metrics(monkeypatch):
    data=_fixture()
    baseline=_verify(data)
    real=binding.verify_binding
    def mutate_after_binding(*args,**kwargs):
        answer=real(*args,**kwargs)
        data[5][3]+=1e7
        data[9][3]+=1e-3
        data[7].data[0]+=1e3
        return answer
    monkeypatch.setattr(binding,'verify_binding',mutate_after_binding)
    observed=_verify(data)
    assert observed['status']==baseline['status']
    assert observed['checks']==baseline['checks']
    assert observed['raw']==baseline['raw']
    assert observed['input_sha256']==baseline['input_sha256']


def test_six_block_cap_counts_both_derived_combined_matrices():
    data=_fixture()
    # Four input blocks occupy 16 entries; two sums add eight more.
    with pytest.raises(ValueError,match='six-block sparse inventory'):
        check.verify_equilibrium(*data,budget=_budget(max_six_block_nnz=20))


def test_malformed_and_resource_preflight_never_reaches_binding(monkeypatch):
    data=_fixture()
    def forbidden(*args,**kwargs):
        pytest.fail('binding reached after failed six-block preflight')
    monkeypatch.setattr(binding,'verify_binding',forbidden)
    with pytest.raises(ValueError,match='six-block sparse inventory'):
        check.verify_equilibrium(*data,budget=_budget(max_six_block_nnz=1))
    data[2].data[0]=np.nan
    with pytest.raises(ValueError,match='finite'):
        check.verify_equilibrium(*data,budget=_budget())
