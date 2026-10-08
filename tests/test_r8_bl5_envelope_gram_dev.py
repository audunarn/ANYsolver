"""Controls for one-producer fixed-target saved-envelope assessment."""
from dataclasses import replace

import numpy as np
import pytest
from scipy import sparse

from scripts import r8_bl5_envelope_gram_dev as assessment


def test_sparse_producer_and_original_floor_match_independent_dense_oracle():
    a = sparse.csr_matrix([[4., -1., 0.], [-1., 3., -.5], [0., -.5, 2.]])
    before = a.data.copy()
    report, arrays = assessment.certify_target(a, epsilon=1e-6, metric=4.)
    assert report['status']=='POSITIVE_ENVELOPE_MECHANICAL_KERNEL_DEVELOPMENT_ONLY'
    assert np.linalg.eigvalsh(a.toarray()-report['fixed_shift']*np.eye(3)).min() > 1.
    proof = report['gram_margin_proof']
    assert proof['margin_lower'] > 0. and proof['rho_upper'] < 1e-6
    assert report['producer_shift']==float(assessment.up(report['fixed_shift']+1e-6))
    assert report['physical_kernel_lower_bound']==float(assessment.down(
        float(assessment.down(report['fixed_shift']-1e-6))/4.))
    np.testing.assert_array_equal(a.data, before)
    assert set(arrays['permutation'])==set(range(3))


def test_nonpositive_producer_never_returns_estimated_physical_success():
    report, arrays = assessment.certify_target(sparse.diags([-1., 1.],format='csr'),
        epsilon=1e-6, metric=1.)
    assert report['status']=='HOLD_MECHANICAL_KERNEL'
    assert report['physical_kernel_lower_bound'] is None
    assert report['hold_kind']=='PRODUCER_DIAGONAL' and 'producer_diagonal' in arrays


def test_input_resource_refusal_precedes_opaque_backend(monkeypatch):
    monkeypatch.setattr(assessment.sparse.linalg,'splu',lambda *a,**k:pytest.fail('backend before guard'))
    report,_ = assessment.certify_target(sparse.eye(2,format='csr'), epsilon=1e-6,metric=1.,
        budget=replace(assessment.PROOF_BUDGET,max_order=1))
    assert report['hold_kind']=='RESOURCE_REFUSAL' and report['physical_kernel_lower_bound'] is None


@pytest.mark.parametrize('epsilon,metric', [(0.,1.),(np.nan,1.),(1e-6,0.),(1e-6,np.inf)])
def test_invalid_error_or_metric_cannot_change_acceptance(epsilon,metric):
    with pytest.raises(ValueError,match='positive finite'):
        assessment.certify_target(sparse.eye(2,format='csr'),epsilon=epsilon,metric=metric)


def test_exact_symmetry_is_required_before_backend(monkeypatch):
    monkeypatch.setattr(assessment.sparse.linalg,'splu',lambda *a,**k:pytest.fail('backend before validation'))
    with pytest.raises(ValueError,match='symmetric'):
        assessment.certify_target(sparse.csr_matrix([[1.,.1],[.2,1.]]),epsilon=1e-6,metric=1.)


def test_backend_failure_details_propagate_without_retry(monkeypatch):
    calls=[]
    def failure(*args,**kwargs):
        calls.append(1)
        raise RuntimeError('backend detail')
    monkeypatch.setattr(assessment.sparse.linalg,'splu',failure)
    with pytest.raises(RuntimeError,match='backend detail'):
        assessment.certify_target(sparse.eye(2,format='csr'),epsilon=1e-6,metric=1.)
    assert len(calls)==1


def test_candidate_evidence_survives_unexpected_helper_failure(monkeypatch):
    stages=[]
    retained={}
    def checkpoint(stage,report,arrays):
        stages.append(stage)
        retained.update(arrays)
        assert report['physical_kernel_lower_bound'] is None
    def failure(*args,**kwargs):
        raise MemoryError('helper failed after candidate')
    monkeypatch.setattr(assessment,'certify_gram_margin',failure)
    with pytest.raises(MemoryError,match='after candidate'):
        assessment.certify_target(sparse.eye(2,format='csr'),epsilon=1e-6,metric=1.,checkpoint=checkpoint)
    assert stages==['SAVED_PRODUCER','SAVED_CANDIDATE_FACTOR']
    assert retained['candidate_F_shape'].tolist()==[2,2]
    assert set(retained['permutation'])=={0,1}
    assert np.isfinite(retained['producer_diagonal']).all()
