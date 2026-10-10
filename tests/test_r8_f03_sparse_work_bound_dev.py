"""Narrow sparse proof controls, no real model/owner/equilibrium solve."""
from types import SimpleNamespace
import numpy as np
import pytest
from scipy import sparse
from scripts.r8_f03_sparse_work_bound_dev import analyze,factor_certificate,inverse_factor_bounds,guarded_product,Refused,Unresolved

def mixed(a,c=(1.,1.),stress=-2.,coupling=(0.,0.)):
    k=np.zeros((3,3));k[:2,:2]=a;k[2,2]=stress;k[0,2],k[2,0]=coupling
    return sparse.csr_matrix(k),sparse.csr_matrix([[*c,0.]]),np.arange(3),np.array([],dtype=int),((2,),)

def test_positive_kernel_and_dominant_negative_stress_excluded():
    r=analyze(*mixed(np.array([[2.,.2],[.2,3.]]),stress=-1e20))
    assert r['status']=='POSITIVE_STORED_CONSTRAINED_WORK' and r['stronger_auxiliary_lower']>0,r.get('blocker')
    assert r['full_native_inertia'] is None and r['physical_defect'] is False

def test_indefinite_fullspace_constrained_positive_is_not_formulation_failure():
    args=mixed(np.array([[1.,1.1],[1.1,1.]]),c=(1.,-1.))
    unaug=analyze(*args,augment=False);aug=analyze(*args)
    assert unaug['status']=='UNRESOLVED' and unaug['physical_defect'] is False
    assert aug['status']=='POSITIVE_STORED_CONSTRAINED_WORK',aug.get('blocker')
    assert aug['constraint_gram_coefficient']==1

def test_negative_in_kernel_not_hidden_by_gram():
    r=analyze(*mixed(np.array([[1.,1.1],[1.1,1.]]),c=(1.,1.)))
    assert r['status']=='UNRESOLVED' and r['physical_defect'] is False

def test_independent_nonsymmetric_left_right_elimination():
    # Exact stationary work diag1 +10*(-10)=-99; averaging coupling wouldhideit.
    r=analyze(*mixed(np.eye(2),c=(0.,1.),stress=-1.,coupling=(10.,-10.)))
    assert r['status']=='UNRESOLVED'

def test_factor_permutation_mismatch_refused():
    factor=SimpleNamespace(perm_r=np.array([1,0]),perm_c=np.array([0,1]))
    with pytest.raises(Unresolved,match='permutations differ'):
        factor_certificate(sparse.eye(2,format='csr'),0.,factor_factory=lambda *a,**kw:factor)

def test_positive_lu_diagonal_is_insufficient_if_reconstruction_corrupt():
    factor=SimpleNamespace(perm_r=np.arange(2),perm_c=np.arange(2),L=sparse.eye(2,format='csr'),U=sparse.eye(2,format='csr'))
    r=factor_certificate(sparse.csr_matrix([[1.,2.],[2.,1.]]),0.,factor_factory=lambda *a,**kw:factor)
    assert r['status']=='UNRESOLVED' and r['factor_reconstruction_error_upper']>=2

def test_near_floor_reconstruction_or_formation_uncertainty_cannot_pass():
    r=factor_certificate(sparse.diags([1.,1e-16],format='csr'),1e-15)
    assert r['status']=='UNRESOLVED'

def test_sparse_outward_inverse_recurrences_bound_tiny_dense_oracle():
    l=sparse.csr_matrix([[1.,0,0],[-.25,1.,0],[.125,-.5,1.]])
    d=np.array([2.,3.,4.]);r=inverse_factor_bounds(l,d)
    t=np.diag(1/np.sqrt(d))@np.linalg.inv(l.toarray())
    assert r['triangular_inverse_infinity_upper']>=np.linalg.norm(t,np.inf)
    assert r['triangular_inverse_one_upper']>=np.linalg.norm(t,1)
    assert r['candidate_minimum_lower']<=np.linalg.eigvalsh(l.toarray()@np.diag(d)@l.toarray().T)[0]

def test_units_congruence_and_input_mutation_are_not_cached_or_aliased():
    args=mixed(np.array([[2.,.2],[.2,3.]]));first=analyze(*args)
    transform=sparse.diags([1e-3,1e3,1.]);changed=(transform@args[0]@transform).tocsr()
    transformed_c=(args[1]@transform).tocsr();changed.sort_indices();transformed_c.sort_indices()
    r=analyze(changed,transformed_c,*args[2:])
    assert first['status']==r['status']=='POSITIVE_STORED_CONSTRAINED_WORK'
    assert args[0][0,0]==2
    args[0][0,0]=-100.
    assert analyze(*args)['status']=='UNRESOLVED'

def test_no_global_dense_materialization(monkeypatch):
    original=sparse.csr_matrix.toarray
    def local_only(self,*a,**kw):
        assert max(self.shape)<=24
        return original(self,*a,**kw)
    monkeypatch.setattr(sparse.csr_matrix,'toarray',local_only)
    a=sparse.diags([3.]*29+[-2.],format='csr');c=sparse.csr_matrix(([1.],([0],[0])),shape=(1,30))
    r=analyze(a,c,np.arange(30),np.array([],dtype=int),((29,),))
    assert r['status']=='POSITIVE_STORED_CONSTRAINED_WORK'

def test_product_storage_eligibility_is_checked_before_product(monkeypatch):
    import scripts.r8_f03_sparse_work_bound_dev as m
    monkeypatch.setattr(m,'PRODUCT_TERM_CAP',1)
    with pytest.raises(Refused,match='eligibility'):guarded_product(sparse.eye(3,format='csr'),sparse.eye(3,format='csr'))

def test_negative_resultant_admission_and_zero_row_refusals():
    assert analyze(*mixed(np.eye(2),stress=1.))['status']=='UNRESOLVED'
    assert analyze(*mixed(np.eye(2),c=(0.,0.)))['status']=='UNRESOLVED'

def test_duplicate_sparse_input_refused_without_summing():
    duplicate=sparse.csr_matrix((np.array([.5,.5,1.]),np.array([0,0,1]),np.array([0,2,3])),shape=(2,2))
    assert not duplicate.has_canonical_format
    with pytest.raises(Refused,match='canonical'):factor_certificate(duplicate,0.)
    with pytest.raises(Refused,match='canonical'):guarded_product(duplicate,sparse.eye(2,format='csr'))

@pytest.mark.parametrize('error',[-1.,float('nan'),float('inf')])
def test_invalid_formation_error_refused_before_candidate(error):
    def forbidden(*a,**kw):raise AssertionError('factorization before admission')
    with pytest.raises(Refused,match='nonnegative formation'):
        factor_certificate(sparse.eye(2,format='csr'),error,factor_factory=forbidden)

def test_nontrivial_equal_three_cycle_permutation_reconstruction():
    l=sparse.csr_matrix([[1.,0.,0.],[.1,1.,0.],[.2,-.3,1.]])
    d=np.array([2.,3.,4.]);perm=np.array([1,2,0])
    gram=l@sparse.diags(d)@l.T;h=gram[perm][:,perm].tocsr();h.sort_indices()
    u=(sparse.diags(d)@l.T).tocsr();u.sort_indices()
    factor=SimpleNamespace(perm_r=perm,perm_c=perm,L=l,U=u)
    result=factor_certificate(h,0.,factor_factory=lambda *a,**kw:factor,ordering=np.arange(3))
    assert result['status']=='POSITIVE_STORED_CONSTRAINED_WORK'

def test_large_diagonal_band_forecast_does_not_override_actual_cost_admission():
    n=4000
    with pytest.raises(Refused,match='scaling eligibility unresolved'):
        factor_certificate(sparse.eye(n,format='csr'),0.)
    result=factor_certificate(sparse.eye(100,format='csr'),0.)
    assert result['status']=='POSITIVE_STORED_CONSTRAINED_WORK'
    assert result['bandwidth']==0 and result['band_factor_slots_informational']==200
    assert result['factor_slot_upper']==100*101

def test_float32_arithmetic_refused_before_binary64_bound():
    a=sparse.eye(2,dtype=np.float32,format='csr')
    with pytest.raises(Refused,match='binary64'):factor_certificate(a,0.)
    with pytest.raises(Refused,match='binary64'):guarded_product(a,a)
