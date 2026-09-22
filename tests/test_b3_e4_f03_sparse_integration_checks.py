"""Synthetic scaled KKT perturbations only, without scientific states."""
from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_sparse_certificate as shared
from scripts import _b3_e4_f03_sparse_integration_checks as check


def _budget(**changes):
    original=check.IntegrationBudget(shared.SparseBudget(64,4096,3,10_000_000),
                                     8192,8192,16_000_000,64*1024**2)
    return replace(original,**changes)


def _fixture():
    eye=np.eye(3,dtype=np.float64)
    zero=np.zeros((3,3),dtype=np.float64)
    H=np.block([[eye,eye],[eye,zero]])
    b=np.array([1.,2.,3.,0.,0.,0.])
    z=np.linalg.solve(H,b)
    Y=np.linalg.inv(H)
    return H,b,z,Y


def _blocks(Y):
    return ((i,Y[:,i:i+3]) for i in range(0,len(Y),3))


def test_identity_and_small_outside_pattern_perturbation_are_verified():
    H,b,z,Y=_fixture()
    primary=sparse.csr_matrix(H)
    identical=check.verify_integration(primary,sparse.csc_matrix(H),b,b,z,
                                       _blocks(Y),3,budget=_budget())
    assert identical['status']=='NUMERICAL_PERTURBATION_PASSED'
    assert identical['raw']['H_difference_frobenius_squared']==0
    assert identical['perturbation']['original_integration_sensitivity_upper']==0
    assert identical['perturbation']['full_saved_state_alternate_error_upper']>=0
    assert identical['scope']==check.SCOPE
    assert identical['primary_certificate']['inverse_columns']==6
    assert identical['input_sha256']['primary_H']==identical['input_sha256']['alternate_H']
    eps=2.**-42
    higher=H.copy();higher[0,1]=eps  # only-one-pattern, top K triangle
    bplus=b.copy();bplus[0]+=eps
    result=check.verify_integration(primary,sparse.csc_matrix(higher),b,bplus,z,
                                    _blocks(Y),3,budget=_budget())
    assert result['status']=='NUMERICAL_PERTURBATION_PASSED'
    assert result['raw']['H_difference_frobenius_squared']==F.from_float(eps)**2
    assert result['raw']['b_difference_two_squared']==F.from_float(eps)**2
    assert result['work']['plus_only']>=1
    assert result['blocks']['K']['within_limit']
    assert result['blocks']['C_upper']['within_limit']
    assert result['perturbation']['alpha_upper']<1
    assert result['raw']['alternate_residual_two_upper']>=np.linalg.norm(higher@z-bplus)
    assert result['input_sha256']['primary_H']!=result['input_sha256']['alternate_H']
    assert result['work']['alternate_equilibrium_solves']==0


def test_independent_c_triangles_and_original_relative_block_limit():
    H,b,z,Y=_fixture()
    higher=H.copy();higher[0,3]+=2.**-30
    result=check.verify_integration(sparse.csr_matrix(H),sparse.csr_matrix(higher),
                                    b,b,z,_blocks(Y),3,budget=_budget())
    assert result['status']=='HOLD'
    assert result['blocks']['C_upper']['within_limit'] is False
    assert result['blocks']['C_lower']['within_limit'] is True
    assert result['blocks']['K']['within_limit'] is True
    assert result['perturbation']['alpha_upper']<1
    assert result['perturbation']['original_integration_sensitivity_upper'] is not None
    assert result['perturbation']['full_saved_state_alternate_error_upper'] is not None
    assert any('C_upper' in reason for reason in result['failures'])


def test_small_nonzero_c_uses_frozen_unit_floor_and_load_uses_original_infinity_norm():
    H,b,z,Y=_fixture()
    scale=2.**-8
    H[:3,3:]*=scale;H[3:,:3]*=scale
    b=np.array([100.,100.,100.,0.,0.,0.])
    z=np.linalg.solve(H,b);Y=np.linalg.inv(H)
    higher=H.copy();higher[0,3]+=scale*2.**-30
    alternate=b.copy();alternate[0]+=1.5e-9
    actual_delta=F.from_float(float(alternate[0]))-F.from_float(float(b[0]))
    result=check.verify_integration(sparse.csr_matrix(H),sparse.csr_matrix(higher),
                                    b,alternate,z,_blocks(Y),3,budget=_budget())
    assert result['status']=='HOLD'
    assert result['blocks']['C_upper']['within_limit'] is True
    c_delta=F.from_float(float(higher[0,3]))-F.from_float(float(H[0,3]))
    assert result['blocks']['C_upper']['squared']==c_delta*c_delta
    assert result['blocks']['C_lower']['within_limit'] is True
    assert result['blocks']['f']['within_limit'] is False
    assert result['raw']['load_difference_infinity']==actual_delta
    assert result['blocks']['f']['squared']==(actual_delta/F(100))**2


def test_alpha_at_least_one_has_null_final_bound_without_repair():
    H,b,z,Y=_fixture()
    higher=H.copy();higher[0,0]+=100.
    result=check.verify_integration(sparse.csr_matrix(H),sparse.csr_matrix(higher),
                                    b,b,z,_blocks(Y),3,budget=_budget())
    assert result['status']=='HOLD'
    assert result['perturbation']['alpha_upper']>=1
    assert result['perturbation']['alpha_violation']==1
    assert result['perturbation']['original_integration_sensitivity_upper'] is None
    assert result['perturbation']['full_saved_state_alternate_error_upper'] is None
    assert result['raw']['alternate_residual_two_upper']>0


@pytest.mark.parametrize('kind',('root_block','dual_rhs','nonfinite','order','workspace'))
def test_structural_and_resource_preflight_never_consumes_inverse_blocks(kind):
    H,b,z,Y=_fixture()
    plus=H.copy();other=b.copy();order=3;budget=_budget()
    if kind=='root_block':plus[3,4]=1e-9
    elif kind=='dual_rhs':other[3]=1e-9
    elif kind=='nonfinite':plus[0,0]=np.nan
    elif kind=='order':order=2
    else:budget=replace(budget,max_python_work_bytes=1)
    def forbidden():
        raise AssertionError('inverse evidence consumed before preflight')
        yield
    with pytest.raises(ValueError):
        check.verify_integration(sparse.csr_matrix(H),sparse.csr_matrix(plus),
                                 b,other,z,forbidden(),order,budget=budget)


def test_missing_inverse_evidence_and_producer_errors_propagate():
    H,b,z,Y=_fixture()
    with pytest.raises(ValueError,match='incomplete'):
        check.verify_integration(sparse.csr_matrix(H),sparse.csr_matrix(H),
                                 b,b,z,iter(()),3,budget=_budget())
    def backend_failure():
        raise RuntimeError('archived factor block unavailable')
        yield
    with pytest.raises(RuntimeError,match='archived factor'):
        check.verify_integration(sparse.csr_matrix(H),sparse.csr_matrix(H),
                                 b,b,z,backend_failure(),3,budget=_budget())


def test_no_dense_global_conversion_and_exact_vector_difference():
    H,b,z,Y=_fixture()
    original=sparse.csr_matrix(H);higher=sparse.csr_matrix(H)
    alternate=b.copy();alternate[1]+=2.**-40
    from scipy.sparse import csr_matrix
    old=csr_matrix.toarray
    try:
        csr_matrix.toarray=lambda *args,**kwargs:pytest.fail('dense fallback reached')
        result=check.verify_integration(original,higher,b,alternate,z,
                                        _blocks(Y),3,budget=_budget())
    finally:
        csr_matrix.toarray=old
    assert result['raw']['b_difference_two_squared']==F.from_float(2.**-40)**2
    assert result['blocks']['f']['within_limit'] is True


def test_identical_descriptions_keep_primary_saved_state_residual_in_full_bound():
    H,b,zstar,Y=_fixture()
    z=np.nextafter(zstar,np.inf)
    result=check.verify_integration(sparse.csr_matrix(H),sparse.csr_matrix(H),
                                    b,b,z,_blocks(Y),3,budget=_budget())
    assert result['primary_certificate']['status']=='CERTIFIED_WITHIN_LIMIT'
    assert result['status']=='NUMERICAL_PERTURBATION_PASSED'
    assert result['perturbation']['original_integration_sensitivity_upper']==0
    rigorous=result['perturbation']['full_saved_state_alternate_error_upper']
    assert rigorous>0
    error_squared=sum((F.from_float(float(a))-F.from_float(float(t)))**2
                      for a,t in zip(z,zstar))
    norm_squared=sum(F.from_float(float(a))**2 for a in z)
    assert F.from_float(rigorous)**2>=error_squared/norm_squared
