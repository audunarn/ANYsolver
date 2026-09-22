"""Synthetic-only outward condition certificates; no classical state input."""
from fractions import Fraction as F
import math

import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_local_condition_probe as p


def _exact_kkt():
    H=np.array([[1.,0.,1.],[0.,4.,1.],[1.,1.,0.]],dtype=np.float64)
    L=np.array([[1.,0.,0.],[0.,1.,0.],[1.,.25,1.]],dtype=np.float64)
    U=np.array([[1.,0.,1.],[0.,4.,1.],[0.,0.,-1.25]],dtype=np.float64)
    return H,L,U


def _compare_certificate(cert,H):
    _,_,actual=p.dense_singular_values(H)
    bound=cert['bounds']['condition_2_upper']
    assert bound>=actual*(1-2e-13)
    assert cert['bounds']['inverse_2_upper']>=1/np.linalg.svd(H,compute_uv=False)[-1]*(1-2e-13)
    assert cert['bounds']['h1_upper']>=float(cert['exact']['h1'])
    assert cert['bounds']['hi_upper']>=float(cert['exact']['hi'])
    if cert['bounds']['backward_error_upper'] is not None:
        assert cert['bounds']['h2_lower']<=np.linalg.svd(H,compute_uv=False)[0]
        assert cert['bounds']['backward_denominator_lower']>0


def test_symmetric_indefinite_kkt_both_methods_and_backward_lower_denominator():
    H,L,U=_exact_kkt()
    z=np.array([1.,-2.,3.]);b=H@z
    a=p.certificate_a(H,b=b,z=z)
    bb=p.certificate_b(H,L,U,b=b,z=z)
    assert a['status']==bb['status']=='CERTIFIED_WITHIN_LIMIT'
    assert a['work']['rhs_solves']==3 and a['work']['inverse_columns']==3
    assert bb['work']['rhs_solves']==0 and bb['work']['factor_residual_entries']==9
    assert a['exact']['e1']<1 and a['exact']['ei']<1
    assert bb['exact']['r1']==bb['exact']['ri']==0
    for cert in (a,bb):
        _compare_certificate(cert,H)
        assert cert['bounds']['backward_error_upper']>=0
        assert cert['bounds']['amplified_backward_upper']<=1e-8


def test_nonsymmetric_stored_triangles_permutations_and_factor_residual():
    # Perturb one stored K triangle of a three-row KKT saddle block.
    L=np.array([[1.,0.,0.],[0.,1.,0.],[1.,.21875,1.]],dtype=np.float64)
    U=np.array([[1.,.125,1.],[0.,4.,1.],[0.,0.,-1.21875]],dtype=np.float64)
    Htilde=L@U
    assert Htilde[2,2]==0 and Htilde[0,1]!=Htilde[1,0]
    row_perm=(1,0,2)
    col_perm=(2,1,0)
    H=Htilde[np.argsort(row_perm),:][:,np.argsort(col_perm)]
    a=p.certificate_a(H)
    b=p.certificate_b(H,L,U,row_perm=row_perm,col_perm=col_perm)
    assert a['status']==b['status']=='CONDITION_BOUND_ONLY'
    assert H[0,1]!=H[1,0]
    assert b['exact']['r1']==b['exact']['ri']==0
    _compare_certificate(a,H);_compare_certificate(b,H)


def test_canonical_sparse_synthetic_storage_matches_dense_certificate():
    H,L,U=_exact_kkt()
    dense_a=p.certificate_a(H)
    sparse_a=p.certificate_a(sparse.csr_matrix(H))
    dense_b=p.certificate_b(H,L,U)
    sparse_b=p.certificate_b(sparse.csc_matrix(H),sparse.csr_matrix(L),
                             sparse.csc_matrix(U))
    for dense,stored in ((dense_a,sparse_a),(dense_b,sparse_b)):
        assert dense['exact']==stored['exact']
        assert dense['bounds']==stored['bounds']
        assert stored['status']=='CONDITION_BOUND_ONLY'
    assert p.dense_singular_values(sparse.csr_matrix(H))==p.dense_singular_values(H)


def test_condition_hold_keeps_fixed_1e10_gate_and_no_fallback():
    eps=1e-6
    H=np.array([[1.,0.,eps],[0.,1.,0.],[eps,0.,0.]],dtype=np.float64)
    L=np.array([[1.,0.,0.],[0.,1.,0.],[eps,0.,1.]],dtype=np.float64)
    U=np.array([[1.,0.,eps],[0.,1.,0.],[0.,0.,-eps*eps]],dtype=np.float64)
    for result in (p.certificate_a(H),p.certificate_b(H,L,U)):
        assert result['status']=='HOLD'
        assert result['bounds']['condition_2_upper']>p.CONDITION_LIMIT
        _compare_certificate(result,H)


def test_inaccurate_columns_or_factors_hold_without_implicit_second_method():
    H=np.eye(3,dtype=np.float64)
    bad=p.certificate_a(H,inverse_columns=np.zeros((3,3),dtype=np.float64))
    assert bad['status']=='HOLD' and bad['reason']=='inverse residual not contractive'
    assert bad['exact']['e1']==bad['exact']['ei']==1
    assert bad['work']['rhs_solves']==0 and bad['work']['inverse_columns']==3
    L=np.eye(3,dtype=np.float64)
    U=np.diag([.49,1.,1.]).astype(np.float64)
    hold=p.certificate_b(H,L,U)
    assert hold['status']=='HOLD' and hold['reason']=='factor residual not contractive'
    assert hold['exact']['nuinf']*hold['exact']['ri']>1
    U[0,0]=.51
    conservative=p.certificate_b(H,L,U)
    assert conservative['status']=='CONDITION_BOUND_ONLY'
    assert conservative['bounds']['condition_2_upper']>20
    assert p.dense_singular_values(H)[2]==1
    backward_hold=p.certificate_a(H,b=np.ones(3),z=np.zeros(3))
    assert backward_hold['status']=='HOLD'
    assert backward_hold['bounds']['condition_gate'] is True
    assert backward_hold['bounds']['backward_gate'] is False
    assert backward_hold['bounds']['amplified_backward_upper']>p.AMPLIFIED_BACKWARD_LIMIT


def test_exact_outward_rounding_and_backward_gate_with_perturbed_state():
    H=np.array([[1.,.125],[-.25,2.]],dtype=np.float64)
    b=np.array([1.,-1.]);z=np.linalg.solve(H,b)
    cert=p.certificate_a(H,b=b,z=z)
    assert cert['status']=='CERTIFIED_WITHIN_LIMIT'
    residual=np.linalg.norm(H@z-b)
    measured=residual/(np.linalg.norm(H,2)*np.linalg.norm(z)+np.linalg.norm(b))
    assert cert['bounds']['backward_error_upper']>=measured*(1-1e-12)
    assert cert['bounds']['h2_lower']<=np.linalg.norm(H,2)
    assert p._upper(F(1,3))>=1/3
    assert p._lower(F(1,3))<=1/3
    assert F.from_float(p._sqrt_out(F(2),True))**2>=2
    assert F.from_float(p._sqrt_out(F(2),False))**2<=2


def test_hard_cap_shapes_types_singularity_and_zero_pivot():
    with pytest.raises(ValueError,match='N<=64'):
        p.certificate_a(np.eye(65,dtype=np.float64))
    with pytest.raises(ValueError,match='float64'):
        p.certificate_a(np.eye(2,dtype=np.float32))
    with pytest.raises(ValueError,match='nonfinite'):
        p.certificate_a(np.array([[1.,np.nan],[0.,1.]]))
    with pytest.raises(ValueError,match='permutation'):
        p.certificate_b(np.eye(2),np.eye(2),np.eye(2),row_perm=(0,0))
    with pytest.raises(ValueError,match='triangular'):
        p.certificate_b(np.eye(2),np.array([[1.,1.],[0.,1.]]),np.eye(2))
    duplicate=sparse.csr_matrix((np.array([.5,.5]),np.array([0,0]),
                                 np.array([0,2,2])),shape=(2,2))
    with pytest.raises(ValueError,match='canonical'):
        p.certificate_a(duplicate)
    H=np.diag([1.,0.]).astype(np.float64)
    assert p.certificate_a(H)['reason']=='singular inverse-column solve'
    assert p.certificate_b(H,np.eye(2),H)['reason']=='zero triangular pivot'


@pytest.mark.parametrize('nonsymmetric',[False,True])
def test_three_root_synthetic_kkt_with_computed_lu_and_exact_backward_check(nonsymmetric):
    from scipy.linalg import lu
    # Nine synthetic primal coordinates and three algebraic root equations.
    # This is not a matrix or accepted state from the physical reference.
    K=4*np.eye(9)-np.eye(9,k=1)-np.eye(9,k=-1)
    if nonsymmetric: K[0,1]+=.25
    C=np.zeros((3,9))
    C[0,[0,3]]=[1.,.5];C[1,[2,5]]=[1.,-.25];C[2,[6,8]]=[.5,1.]
    H=np.block([[K,C.T],[C,np.zeros((3,3))]])
    permutation,L,U=lu(H)
    rows=tuple(int(v) for v in np.argmax(permutation.T,axis=1))
    z=np.arange(12,dtype=float)/8;b=H@z
    A=p.certificate_a(H,b=b,z=z)
    B=p.certificate_b(H,L,U,row_perm=rows,b=b,z=z)
    for certificate in (A,B):
        assert certificate['status']=='CERTIFIED_WITHIN_LIMIT'
        _compare_certificate(certificate,H)
        assert certificate['bounds']['backward_error_upper']==0
    assert A['work']['inverse_columns']==A['work']['rhs_solves']==12
    assert B['work']['factor_residual_entries']==144
    assert np.count_nonzero(H[-3:,-3:])==0


@pytest.mark.parametrize('fault',['negative_index','large_index','backwards_pointer','short_pointer','noninteger_index'])
def test_sparse_buffers_rejected_before_native_canonical_check_or_conversion(monkeypatch,fault):
    matrix=sparse.csr_matrix(np.eye(2))
    if fault=='negative_index': matrix.indices[0]=-1
    elif fault=='large_index': matrix.indices[0]=99
    elif fault=='backwards_pointer': matrix.indptr=np.array([0,2,1])
    elif fault=='short_pointer': matrix.indptr=np.array([0,2])
    else: matrix.indices=np.array([0.,1.])
    def forbidden(*args,**kwargs):
        raise AssertionError('native sparse traversal reached before structural validation')
    monkeypatch.setattr(sparse.csr_matrix,'has_canonical_format',property(forbidden))
    monkeypatch.setattr(sparse.csr_matrix,'toarray',forbidden)
    with pytest.raises(ValueError,match='sparse structure'):
        p.certificate_a(matrix)
