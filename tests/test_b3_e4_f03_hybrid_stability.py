"""Independent finite-dimensional work and quotient oracles."""

from pathlib import Path
import sys

import numpy as np
import pytest
from scipy import linalg,sparse
from scipy.sparse.linalg import spsolve

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import _b3_e4_f03_hybrid_stability as stability


def test_known_constraint_energy_and_spectrum():
    # Three independent two-spring systems tied at their midpoints.
    k=np.diag((2.,3.,4.,6.,8.,10.))
    c=np.c_[np.eye(3),-np.eye(3)]
    result,gram=stability.diagnose(sparse.csr_matrix(k),sparse.csr_matrix(c),
                                 np.ones((1,1)),np.ones((1,1)))
    expected=np.sort(1/np.diag(k)[:3]+1/np.diag(k)[3:])
    np.testing.assert_allclose(result['generalized_eigenvalues'],expected,rtol=1e-14)
    a,b=stability.normalized_kkt(sparse.csr_matrix(k),sparse.csr_matrix(c),
                                np.arange(1.,7.))
    x=spsolve(a,b)
    q=x[:6]
    np.testing.assert_allclose(q[:3],np.arange(5.,10.,2.)/
                               (np.diag(k)[:3]+np.diag(k)[3:]),rtol=1e-14)
    assert q@k@q==pytest.approx(np.arange(1.,7.)@q)
    np.testing.assert_allclose(c@q,0.,atol=1e-15)


def test_row_congruence_leaves_normalized_spectrum_unchanged():
    rng=np.random.default_rng(20260922)
    raw=rng.normal(size=(9,9)); k=raw.T@raw+np.eye(9)
    c=rng.normal(size=(6,9))
    g=np.array(((2.,.2),(.2,3.)))
    r,_=stability.diagnose(sparse.csr_matrix(k),sparse.csr_matrix(c),g,g)
    t=np.array(((1.,-1/6),(0.,1.)))
    transformed=np.kron(t,np.eye(3))@c
    r2,_=stability.diagnose(sparse.csr_matrix(k),sparse.csr_matrix(transformed),
                           t@g@t.T,t@g@t.T)
    np.testing.assert_allclose(r['generalized_eigenvalues'],r2['generalized_eigenvalues'],
                               rtol=1e-12,atol=1e-14)


def test_unresolved_auxiliary_norm_is_reported_without_retry():
    r,_=stability.diagnose(sparse.eye(3,format='csr'),sparse.eye(3,format='csr'),
                           np.ones((1,1)),1.002*np.ones((1,1)))
    assert r['auxiliary_status']=='UNRESOLVED_AUXILIARY_NORM'
    assert r['auxiliary_squared_norm_change']==pytest.approx(.002)


def test_nonpositive_or_asymmetric_norm_is_not_repaired():
    k=sparse.eye(6,format='csr'); c=k.copy()
    for gram in (np.diag((1.,-1.)),np.array(((1.,.5),(0.,1.)))):
        with pytest.raises((ValueError,linalg.LinAlgError)):
            stability.diagnose(k,c,gram,gram)


def test_analytic_norm_uses_same_sparse_schur_without_fe_delta():
    primal=sparse.diags((2.,3.,4.,6.,8.,10.),format='csr')
    constraint=sparse.csr_matrix(np.c_[np.eye(3),-np.eye(3)])
    identity={'kind':'piecewise_analytic_full_H1_free_endpoint',
              'normalized_rows':True,'source_sha256':'a'*64,
              'row_measures':[1.], 'selected_enriched_rows':[0]}
    captured=[]
    analytic,gram=stability.diagnose_analytic(
        primal,constraint,np.ones((1,1)),norm_identity=identity,
        matrix_sink=lambda s,g: captured.append((s,g)))
    legacy,legacy_gram=stability.diagnose(
        primal,constraint,np.ones((1,1)),np.ones((1,1)))
    np.testing.assert_allclose(analytic['generalized_eigenvalues'],
                               legacy['generalized_eigenvalues'],rtol=1e-14)
    np.testing.assert_array_equal(gram,legacy_gram)
    assert analytic['norm_source']=='analytic_h1'
    assert analytic['auxiliary_status']=='PIECEWISE_ANALYTIC_FLOATING'
    assert 'auxiliary_squared_norm_change' not in analytic
    assert 'norm_source' not in legacy
    assert 'norm_identity' not in legacy
    assert len(captured)==1
    schur,saved_gram=captured[0]
    np.testing.assert_allclose(linalg.eigvalsh(schur,saved_gram),
                               analytic['generalized_eigenvalues'],rtol=1e-14)
    assert not np.shares_memory(gram,saved_gram)
    saved_gram[0,0]=np.nan
    schur[0,0]=np.nan
    assert np.all(np.isfinite(gram))
    assert np.all(np.isfinite(analytic['generalized_eigenvalues']))
    identity['row_measures'][0]=42.
    assert analytic['norm_identity']['row_measures']==[1.]


def test_analytic_norm_rejects_bad_gram_or_identity():
    primal=sparse.eye(6,format='csr'); constraint=primal.copy()
    identity={'kind':'piecewise_analytic_full_H1_free_endpoint',
              'normalized_rows':True,'source_sha256':'b'*64,
              'row_measures':[1.,1.]}
    for gram in (np.diag((1.,-1.)),np.array(((1.,.5),(0.,1.)))):
        with pytest.raises((ValueError,linalg.LinAlgError)):
            stability.diagnose_analytic(primal,constraint,gram,norm_identity=identity)
    with pytest.raises(ValueError,match='identity'):
        stability.diagnose_analytic(primal,constraint,np.eye(2),
                                   norm_identity={**identity,'normalized_rows':False})
