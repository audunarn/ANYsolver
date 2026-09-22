"""Small synthetic scaling/state identities; no physical case execution."""
from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_sparse_certificate as shared
from scripts import _b3_e4_f03_sparse_state_binding as binding
from scripts import _b3_e4_f03_spatial_contract as c


def _budget(**changes):
    original=binding.BindingBudget(shared.SparseBudget(32,512,3,2_000_000),
        1024,8192,8_000_000,32*1024**2)
    return replace(original,**changes)


def _fixture():
    shell=sparse.diags([1e7,2e7,3e7],format='csr')
    beam=sparse.diags([1e7,2e7,3e7],format='csr')
    root=sparse.csr_matrix(np.array([[1.,0.,0.],[0.,2.,0.],[0.,0.,3.]]))
    f=np.array([100.,200.,300.],dtype=np.float64)
    d=np.sqrt(c.E0/(shell+beam).diagonal())
    r=np.array((1/c.U0,1/c.U0,.46/c.U0))
    k=(shell+beam).toarray()
    kbar=((k*d[:,None])*d[None,:])/c.E0
    cc=root.toarray()
    cbar=(cc*r[:,None])*d[None,:]
    h=sparse.csr_matrix(np.block([[kbar,cbar.T],[cbar,np.zeros((3,3))]]))
    b=np.r_[d*f/c.E0,np.zeros(3)]
    z=np.array([.25,-.5,.75,1.,-2.,3.],dtype=np.float64)
    q=d*z[:3]
    eta=c.E0*r*z[-3:]
    action=h@z
    return [shell,beam,root,f,d,h,b,q,eta,z,action]


def _check(data,**kwargs):
    return binding.verify_binding(*data[:10],h_z=data[10],budget=_budget(),**kwargs)


def test_full_sparse_scaling_and_saved_state_pass_with_owned_hashes():
    data=_fixture()
    result=_check(data)
    assert result['status']=='BINDING_PASSED'
    assert not result['failures']
    assert result['checks']['D_relative_within_1e_12']
    assert result['checks']['H_entry_bit_mismatch_count']==0
    assert result['checks']['b_entry_bit_mismatch_count']==0
    assert result['checks']['H_z_absolute_max_upper']<=1e-11
    assert result['work']['equilibrium_solves']==0
    saved=result['input_sha256']['H']
    data[5].data[0]+=1.
    assert saved==result['input_sha256']['H']


def test_missing_action_is_explicit_partial_and_incorrect_action_holds():
    data=_fixture()
    partial=binding.verify_binding(*data[:10],budget=_budget())
    assert partial['status']=='PARTIAL_ACTION_NOT_PROVIDED'
    assert partial['action_binding']=='NOT_PROVIDED'
    assert partial['checks']['H_z_absolute_max_upper'] is None
    data[10]=data[10].copy();data[10][5]+=1e-8
    failed=_check(data)
    assert failed['status']=='HOLD'
    assert failed['action_binding']=='FAILED'
    assert any('H_z' in x for x in failed['failures'])


@pytest.mark.parametrize('channel',('K','C_lower','C_upper','b','q','eta'))
def test_both_triangles_full_rhs_and_physical_actions_are_bound(channel):
    data=_fixture()
    if channel=='K':data[5]=data[5].tolil();data[5][0,0]+=2**-30
    if channel=='C_lower':data[5]=data[5].tolil();data[5][3,0]+=2**-30
    if channel=='C_upper':data[5]=data[5].tolil();data[5][0,3]+=2**-30
    if channel in ('K','C_lower','C_upper'):data[5]=data[5].tocsr()
    if channel=='b':data[6]=data[6].copy();data[6][0]+=2**-30
    if channel=='q':data[7]=data[7].copy();data[7][0]+=1e-8
    if channel=='eta':data[8]=data[8].copy();data[8][0]+=1.
    result=_check(data)
    assert result['status']=='HOLD'
    if channel in ('K','C_lower','C_upper'):
        assert result['checks']['H_entry_bit_mismatch_count']==1
    elif channel=='b':assert result['checks']['b_entry_bit_mismatch_count']==1
    else:assert any(channel in reason for reason in result['failures'])


def test_coherently_changed_scaling_fails_diagonal_identity():
    data=_fixture()
    d=data[4].copy();d[0]*=1+1e-9
    root=data[2].toarray()
    r=np.array((1/c.U0,1/c.U0,.46/c.U0))
    k=(data[0]+data[1]).toarray()
    cbar=(root*r[:,None])*d[None,:]
    data[4]=d
    data[5]=sparse.csr_matrix(np.block([[(k*d[:,None])*d[None,:]/c.E0,cbar.T],
                                      [cbar,np.zeros((3,3))]]))
    data[6]=np.r_[d*data[3]/c.E0,np.zeros(3)]
    data[7]=d*data[9][:3]
    data[10]=data[5]@data[9]
    result=_check(data)
    assert result['status']=='HOLD'
    assert not result['checks']['D_relative_within_1e_12']
    assert result['checks']['H_entry_bit_mismatch_count']==0


def test_explicit_and_signed_sparse_zeros_do_not_change_nonzero_parity():
    data=_fixture()
    h=data[5].tolil();h[0,1]=-0.;h[5,5]=0.
    data[5]=h.tocsr()
    result=_check(data)
    assert result['status']=='BINDING_PASSED'


def test_malformed_resource_caps_and_nonfinite_are_rejected_before_sparse_sum(monkeypatch):
    data=_fixture()
    low=_budget(max_combined_nnz=1)
    original=sparse.bmat
    def forbidden(*args,**kwargs):
        pytest.fail('sparse block construction reached before resource cap')
    monkeypatch.setattr(sparse,'bmat',forbidden)
    with pytest.raises(ValueError,match='envelope'):
        binding.verify_binding(*data[:10],h_z=data[10],budget=low)
    monkeypatch.setattr(sparse,'bmat',original)
    data[4]=data[4].copy();data[4][0]=np.nan
    with pytest.raises(ValueError,match='finite'):
        _check(data)
    data[4][0]=-1.
    with pytest.raises(ValueError,match='positive'):
        _check(data)


def test_fixed_kkt_bit_order_is_stricter_than_generic_exact_real_parity():
    data=_fixture()
    # The future producer must declare left-then-right float arithmetic.
    # A nonzero alternate rounded value, however physically close, fails.
    h=data[5].copy()
    h.data[0]=np.nextafter(h.data[0],np.inf)
    data[5]=h
    result=_check(data)
    assert result['status']=='HOLD'
    assert result['checks']['H_entry_bit_mismatch_count']==1
    assert result['raw']['H_entry_max_abs_difference_upper']>0
