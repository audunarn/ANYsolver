"""Synthetic sparse congruence proof only; no classical assembled state."""
from dataclasses import replace
from fractions import Fraction as F

import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_sparse_certificate as shared
from scripts import _b3_e4_f03_sparse_positivity as p


def _budget(**changes):
    base=p.PositivityBudget(
        shared.SparseBudget(64,4096,1,10_000_000),
        max_product_paths=262_144,max_residual_nnz=4096,
        max_fraction_bits=8192,max_total_bits=16_000_000,
        max_python_work_bytes=64*1024**2)
    return replace(base,**changes)


def _factor_fixture():
    L=np.array([[1.,0.,0.],[.5,1.,0.],[0.,.25,1.]],dtype=np.float64)
    d=np.array([2.,4.,8.],dtype=np.float64)
    B=L@np.diag(d)@L.T
    return B,L,d


def test_exact_sparse_congruence_proves_spd_and_tracks_resources():
    B,L,d=_factor_fixture()
    K=sparse.csr_matrix(B);factor=sparse.csr_matrix(L)
    before=K.data.copy();before_factor=factor.data.copy()
    result=p.certify_positive(K,factor,d,(0,1,2),budget=_budget())
    assert result['status']=='POSITIVE_QUADRATIC_FORM'
    assert result['raw']['delta_squared']==0
    assert result['raw']['residual_1']==result['raw']['residual_inf']==0
    assert result['residual_entries']==()
    assert result['work']['product_paths']==sum(np.count_nonzero(L[:,j])**2
                                                for j in range(3))
    assert result['work']['factor_rhs_solves']==0
    assert result['work']['rational_checks']>0
    assert result['work']['python_workspace_estimate_bytes']<64*1024**2
    assert result['raw']['lower_inverse_1_upper']>=F.from_float(
        float(np.linalg.norm(np.linalg.inv(L),1)))
    np.testing.assert_array_equal(K.data,before)
    np.testing.assert_array_equal(factor.data,before_factor)


def test_symmetric_permutation_and_admitted_skew_certify_full_quadratic_form():
    B,L,d=_factor_fixture()
    order=(2,0,1)
    K=np.zeros_like(B)
    for i in range(3):
        for j in range(3):K[order[i],order[j]]=B[i,j]
    K[0,1]+=2.**-48  # one independently stored triangle, no averaging
    result=p.certify_positive(sparse.csr_matrix(K),sparse.csc_matrix(L),d,
                              order,budget=_budget())
    assert result['status']=='POSITIVE_QUADRATIC_FORM'
    assert result['raw']['stored_skew_frobenius_squared']>0
    assert 0<result['raw']['delta_squared']<1
    assert result['work']['residual_nnz']>0
    for x in ((1.,0.,0.),(1.,-2.,3.),(.5,.25,-1.)):
        vector=np.asarray(x)
        assert vector@K@vector>0


def test_skew_above_existing_limit_and_indefinite_or_poor_factors_hold():
    B,L,d=_factor_fixture()
    K=B.copy();K[0,1]+=.01
    result=p.certify_positive(sparse.csr_matrix(K),sparse.csr_matrix(L),d,
                              (0,1,2),budget=_budget())
    assert result['status']=='HOLD'
    assert result['reason']=='stored skew exceeds unchanged gate'
    assert result['work']['product_paths']==0
    K=sparse.diags([1.,-1.],format='csr')
    result=p.certify_positive(K,sparse.eye(2,format='csr'),np.ones(2),
                              (0,1),budget=_budget())
    assert result['status']=='HOLD'
    assert result['raw']['delta_squared']>=1
    assert result['reason']=='congruence residual bound not contractive'
    B,L,d=_factor_fixture()
    d[0]=0.
    result=p.certify_positive(sparse.csr_matrix(B),sparse.csr_matrix(L),d,
                              (0,1,2),budget=_budget())
    assert result['status']=='HOLD'
    assert result['reason']=='nonpositive supplied congruence diagonal'


def test_full_residual_includes_fill_outside_input_without_dense_conversion(monkeypatch):
    K=sparse.eye(2,format='csr')
    L=sparse.csr_matrix(np.array([[1.,0.],[.5,1.]]))
    d=np.array([1.,.75])
    monkeypatch.setattr(sparse.csr_matrix,'toarray',
                        lambda *args,**kwargs:pytest.fail('dense fallback reached'))
    result=p.certify_positive(K,L,d,(0,1),budget=_budget())
    assert result['status']=='HOLD'
    assert result['work']['residual_pattern_nnz']==4
    assert (0,1,F(-1,2)) in result['residual_entries']
    assert (1,0,F(-1,2)) in result['residual_entries']


def test_caps_and_malformed_inputs_fail_before_factor_products(monkeypatch):
    B,L,d=_factor_fixture()
    K=sparse.csr_matrix(B);factor=sparse.csr_matrix(L)
    with pytest.raises(ValueError,match='shape|budget'):
        p.certify_positive(sparse.eye(65,format='csr'),factor,d,(0,1,2),
                           budget=_budget())
    with pytest.raises(ValueError,match='product-path'):
        p.certify_positive(K,factor,d,(0,1,2),
                           budget=_budget(max_product_paths=1))
    with pytest.raises(ValueError,match='Python rational/pattern workspace'):
        p.certify_positive(K,factor,d,(0,1,2),
                           budget=_budget(max_python_work_bytes=1))
    with pytest.raises(ValueError,match='pattern cap'):
        p.certify_positive(K,factor,d,(0,1,2),
                           budget=_budget(max_residual_nnz=1))
    with pytest.raises(ValueError,match='permutation'):
        p.certify_positive(K,factor,d,(0,0,2),budget=_budget())
    with pytest.raises(ValueError,match='unit lower'):
        p.certify_positive(K,sparse.csr_matrix(np.eye(3)*2),d,(0,1,2),
                           budget=_budget())
    with pytest.raises(ValueError,match='rational positivity resource'):
        p.certify_positive(K,factor,d,(0,1,2),
                           budget=_budget(max_total_bits=2))
    duplicate=sparse.csr_matrix((np.array([.5,.5]),np.array([0,0]),
                                 np.array([0,2,2])),shape=(2,2))
    with pytest.raises(ValueError,match='canonical'):
        p.certify_positive(duplicate,sparse.eye(2,format='csr'),np.ones(2),
                           (0,1),budget=_budget())


def test_resource_rejections_precede_comparison_and_exact_row_storage(monkeypatch):
    B,L,d=_factor_fixture()
    K=sparse.csr_matrix(B);factor=sparse.csr_matrix(L)
    with monkeypatch.context() as m:
        m.setattr(p,'_inverse_comparison',
                  lambda *args:pytest.fail('comparison occurred before path cap'))
        with pytest.raises(ValueError,match='product-path'):
            p.certify_positive(K,factor,d,(0,1,2),
                               budget=_budget(max_product_paths=1))
    with monkeypatch.context() as m:
        m.setattr(p,'_rows',
                  lambda *args:pytest.fail('row storage occurred before workspace cap'))
        with pytest.raises(ValueError,match='Python rational/pattern workspace'):
            p.certify_positive(K,factor,d,(0,1,2),
                               budget=_budget(max_python_work_bytes=1))
