"""Independent analytical/adversarial checks of registered residual scaling."""
import dataclasses
import json
import numpy as np
import pytest
from scipy import sparse
from anysolver.solid_residuals import ResidualScales, evaluate_residuals


def evaluate(*, K=None, P=None, C=None, u=None, lam=None, F=None, g=None,
             scales=None, labels=None, rotations=()):
    u = np.zeros((2, 1)) if u is None else np.asarray(u)
    n, k = u.shape
    K = np.eye(n) if K is None else K
    P = np.eye(n) if P is None else P
    C = np.zeros((0, n)) if C is None else C
    m = C.shape[0] if hasattr(C, 'shape') else len(C)
    return evaluate_residuals(K, P, C, u,
        np.zeros((m, k)) if lam is None else lam,
        np.zeros((n, k)) if F is None else F,
        np.zeros(m) if g is None else g,
        scales=[ResidualScales(1., 1., 1.)] * k if scales is None else scales,
        constraint_interfaces=np.zeros(m, dtype=int) if labels is None else labels,
        native_rotation_dofs=rotations)


def test_local_constraint_counterexample_cannot_hide_in_global_norm():
    report = evaluate(K=np.zeros((2, 2)), C=np.diag([1., 1e-12]), u=[[1.], [1.]], g=[1., 0.])
    case = report['per_case'][0]
    assert not report['passed']
    assert case['local_constraint_error'] == [0., 1.]
    assert case['normwise_constraint_error'] == pytest.approx(5e-13)
    assert case['offending_constraint_indices'] == [1]
    assert report['normalized_constraint_error'] == 1.
    assert report['offending_constraint_indices'] == [{'case': 0, 'index': 1}]


def test_native_rotations_receive_dimensional_length_scaling():
    report = evaluate(K=np.eye(2), u=[[0.], [2.]], rotations=[1],
                      scales=[ResidualScales(10., 4., .5)])
    case = report['per_case'][0]
    assert case['reduced_column_scales'] == [1., 10.]
    assert case['local_equilibrium'] == [0., .05]
    # A=diag(1,.01), ubar=(0,20), hence eta=.2/20=.01.
    assert case['normwise_equilibrium'] == pytest.approx(.01)
    assert case['references']['native_rotation_dofs'] == [1]


def test_constraint_native_rotation_denominator():
    report = evaluate(K=np.zeros((2, 2)), C=[[0., 2.]], u=[[0.], [.1]], rotations=[1],
                      scales=[ResidualScales(10., 1., .5)])
    case = report['per_case'][0]
    assert case['local_constraint_denominators'] == pytest.approx([.1])
    assert case['local_constraint_error'] == pytest.approx([2.])


@pytest.mark.parametrize('row_scale', [1e-12, -7., 1e12])
def test_constraint_row_scalar_invariance(row_scale):
    base = dict(K=np.zeros((2, 2)), u=[[.4], [.7]], C=[[2., -3.]], g=[.1])
    a = evaluate(**base)['per_case'][0]
    base.update(C=np.array(base['C']) * row_scale, g=np.array(base['g']) * row_scale)
    b = evaluate(**base)['per_case'][0]
    assert b['local_constraint_error'] == pytest.approx(a['local_constraint_error'])
    assert b['normwise_constraint_error'] == pytest.approx(a['normwise_constraint_error'])


@pytest.mark.parametrize('column_scale', [1e-12, -5., 1e12])
def test_reduced_column_scalar_reparameterization(column_scale):
    args = dict(K=[[2., 1.], [1., 3.]], C=[[1., -1.]], u=[[.3], [.2]],
                lam=[[.4]], F=[[.5], [.6]], g=[.1])
    a = evaluate(P=np.eye(2), **args)['per_case'][0]
    b = evaluate(P=np.diag([column_scale, 1.]), **args)['per_case'][0]
    for key in ('local_equilibrium', 'normwise_equilibrium', 'normalized_equilibrium'):
        assert b[key] == pytest.approx(a[key])


def test_affine_support_primary_includes_prescribed_offset():
    # u=u0+P*z, u0=(3,0), z=2. Only the second equation is free.
    # First-equation reaction is intentionally ignored by P.T.
    report = evaluate(K=[[2., 1.], [1., 2.]], P=[[0.], [1.]],
                      u=[[3.], [2.]], F=[[0.], [7.]])
    assert report['passed']
    assert report['absolute_free_residual_max'] == 0.


def test_multiple_rhs_and_interface_specific_references():
    report = evaluate(K=np.zeros((2, 2)), C=np.eye(2), g=[1., 1.],
                      u=[[1. + 1e-10, 1. + 1e-10], [1. + 2e-10, 1. + 2e-10]],
                      labels=[0, 1], scales=[ResidualScales(1, 1, 1), ResidualScales(2, 3, 4, (1., .1))])
    a, b = report['per_case']
    assert a['local_constraint_error'] == pytest.approx([1e-10, 2e-10])
    assert b['local_constraint_error'] == pytest.approx([1e-10, 2e-9])
    assert a['references']['interface_displacements'] == [1., 1.]
    assert b['references']['interface_displacements'] == [1., .1]
    assert not report['passed']
    assert a['passed']
    assert not b['passed']
    assert b['offending_constraint_indices'] == [1]


def test_zero_zero_and_violated_zero_constraint_row():
    exact = evaluate(K=np.zeros((2, 2)), C=np.zeros((1, 2)))
    assert exact['passed']
    assert exact['normalized_equilibrium'] == exact['normalized_constraint_error'] == 0.
    violated = evaluate(K=np.zeros((2, 2)), C=np.zeros((1, 2)), g=[1.])
    assert not violated['passed']
    assert violated['normalized_constraint_error'] == float('inf')
    assert violated['per_case'][0]['normwise_constraint_error'] == 1.


def test_zero_reduced_columns_and_fully_prescribed_system():
    with pytest.raises(ValueError, match='nonzero physical scale'):
        evaluate(P=[[0.], [0.]])
    report = evaluate(P=np.zeros((2, 0)), u=[[3.], [7.]], F=[[1.], [2.]])
    assert report['passed']
    assert report['per_case'][0]['local_equilibrium'] == []


def test_empty_rhs_is_rejected_instead_of_vacuously_passing():
    with pytest.raises(ValueError, match='at least one RHS'):
        evaluate(u=np.empty((2, 0)), scales=[])


def test_legacy_diagnostics_exactly_preserve_existing_formulas():
    K = np.array([[2., -1.], [-1., 3.]])
    P = np.diag([2., -3.])
    C = np.array([[4., -2.]])
    u = np.array([[.3], [-.2]])
    lam = np.array([[.7]])
    F = np.array([[.4], [.1]])
    g = np.array([.8])
    r = P.T @ (K @ u + C.T @ lam - F)
    e = np.max(abs(r) / np.maximum(abs(P.T) @ (abs(K) @ abs(u) + abs(C.T @ lam) + abs(F)), np.finfo(float).tiny))
    c = np.max(abs(C @ u - g[:, None]) / np.maximum(abs(C) @ abs(u) + abs(g[:, None]), 1e-14))
    report = evaluate(K=K, P=P, C=C, u=u, lam=lam, F=F, g=g)
    assert report['legacy_componentwise_equilibrium'] == e
    assert report['legacy_componentwise_constraint_error'] == c


def test_legacy_failure_is_diagnostic_only():
    report = evaluate(K=np.zeros((1, 1)), u=[[0.]], F=[[1e-12]])
    assert report['legacy_componentwise_equilibrium'] == 1.
    # Normwise eta is 1, even though local physical value is 1e-12.
    assert not report['passed']
    report = evaluate(K=[[1.]], u=[[1.]], F=[[1. + 1e-12]])
    assert report['passed']
    # The second equation's own scale is its tiny force, so the historical
    # componentwise policy reports 1 despite a negligible registered residual.
    report = evaluate(K=[[1., 1.], [0., 0.]], u=[[1.], [-1.]], F=[[0.], [1e-12]])
    assert report['legacy_componentwise_equilibrium'] == 1.
    assert report['normalized_equilibrium'] == pytest.approx(1e-12)
    assert report['passed']


def test_general_multi_master_reviewer_counterexample_is_refused():
    M = 1e12
    P = np.array([[1., 0.], [0., 1.], [M, M]])
    with pytest.raises(ValueError, match='disjoint-support/orthogonal reduction'):
        evaluate(K=np.eye(3), P=P, u=[[1.], [-1.], [0.]])


def test_one_master_mpc_and_canonical_sparse_zero_entries():
    # Duplicate entries sum to an explicit zero in a second column. It must
    # be removed before the disjoint-support applicability check.
    P = sparse.coo_matrix(([1., 2., 3., -3.], ([0, 1, 1, 1], [0, 0, 1, 1])), shape=(2, 2))
    with pytest.raises(ValueError, match='nonzero physical scale'):
        evaluate(P=P)
    report = evaluate(P=[[1.], [2.]], u=[[1.], [2.]], F=[[1.], [2.]])
    assert report['passed']
    assert report['per_case'][0]['reduced_column_scales'] == [2.]


@pytest.mark.parametrize('field,bad', [(f, v) for f in ('length', 'force', 'displacement')
                                    for v in (True, 0, -1, np.nan, np.inf, '1')])
def test_invalid_references(field, bad):
    kwargs = dict(length=1., force=1., displacement=1.)
    kwargs[field] = bad
    with pytest.raises(ValueError):
        ResidualScales(**kwargs)


@pytest.mark.parametrize('bad', [(True,), (0.,), (np.inf,), 3, 'bad'])
def test_invalid_interface_references(bad):
    with pytest.raises(ValueError):
        ResidualScales(1., 1., 1., bad)


@pytest.mark.parametrize('kwargs', [
    {'K': np.eye(3)}, {'P': np.ones((3, 1))}, {'C': np.ones((1, 3))},
    {'F': np.ones((2, 2))}, {'lam': np.ones((1, 1))}, {'g': [0.]},
    {'scales': []}, {'scales': [1.]}, {'rotations': [2]}, {'rotations': [True]},
    {'rotations': [0, 0]}, {'rotations': [1.]},
    {'C': [[1., 0.]], 'labels': []}, {'C': [[1., 0.]], 'labels': [1]},
    {'C': [[1., 0.]], 'labels': [0.]},
    {'C': [[1., 0.]], 'scales': [ResidualScales(1, 1, 1, (1., 2.))]},
    {'u': [[np.nan], [0.]]}, {'K': [[np.inf, 0.], [0., 1.]]},
    {'C': [[np.nan, 0.]]}, {'F': [[np.nan], [0.]]},
    {'P': [[np.inf], [0.]]}, {'C': [[1., 0.]], 'lam': [[np.inf]]},
    {'C': [[1., 0.]], 'g': [np.nan]},
])
def test_invalid_shapes_labels_and_nonfinite_inputs(kwargs):
    with pytest.raises(ValueError):
        evaluate(**kwargs)


def test_computed_nonfinite_arithmetic_is_rejected():
    with pytest.raises(ValueError, match='nonfinite'):
        evaluate(K=np.eye(2) * 1e308, u=[[1e308], [1e308]])


def test_input_immutability_and_python_json_types():
    K = sparse.csr_matrix([[2., 0.], [0., 3.]])
    P = sparse.eye(2, format='csr')
    C = sparse.csr_matrix([[1., -1.]])
    u, F, lam, g = np.array([[.1], [.1]]), np.array([[.2], [.3]]), np.zeros((1, 1)), np.zeros(1)
    inputs = [K, P, C, u, F, lam, g]
    before = [x.copy() for x in inputs]
    scales = ResidualScales(np.float64(1), np.int64(1), 1, [1])
    with pytest.raises(dataclasses.FrozenInstanceError):
        scales.force = 2.
    result = evaluate(K=K, P=P, C=C, u=u, F=F, lam=lam, g=g, scales=[scales])
    assert result['passed']
    json.dumps(result, allow_nan=False)
    for original, saved in zip(inputs, before):
        if sparse.issparse(original):
            np.testing.assert_array_equal(original.data, saved.data)
            np.testing.assert_array_equal(original.indices, saved.indices)
            np.testing.assert_array_equal(original.indptr, saved.indptr)
        else:
            np.testing.assert_array_equal(original, saved)
