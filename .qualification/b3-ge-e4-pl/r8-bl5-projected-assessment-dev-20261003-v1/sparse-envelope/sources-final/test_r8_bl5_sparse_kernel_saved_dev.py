"""Exact small controls for graph, inverse and stationary rounding enclosures."""
from fractions import Fraction as F

import numpy as np
import pytest
from scipy import sparse
from scripts import r8_bl5_sparse_kernel_saved_dev as proof


def fractions(a):
    return [[F(float(v)) for v in row] for row in a]


def inverse2(a):
    determinant = a[0][0]*a[1][1]-a[0][1]*a[1][0]
    return [[a[1][1]/determinant, -a[0][1]/determinant],
            [-a[1][0]/determinant, a[0][0]/determinant]]


def product(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(len(b)))
             for j in range(len(b[0]))] for i in range(len(a))]


def test_sparse_product_error_contains_exact_cancellation_and_signs():
    a = np.array([[.1, -.7, .2], [1e10, -1e10, .3]])
    b = np.array([[.2, .8], [.2, -.9], [1., .25]])
    value, error = proof.sparse_product(sparse.csr_matrix(a), sparse.csr_matrix(b))
    exact = product(fractions(a), fractions(b))
    for i, row in enumerate(exact):
        for j, entry in enumerate(row):
            assert abs(F(float(value[i, j]))-entry) <= F(error)


def test_sparse_product_refuses_underflow_instead_of_dropping_it():
    with pytest.raises(ArithmeticError, match='underflow'):
        proof.sparse_product(sparse.csr_matrix([[np.finfo(float).tiny]]), sparse.csr_matrix([[.5]]))


@pytest.mark.parametrize('magnitude', (1., np.finfo(float).tiny, np.nextafter(0., 1.)))
def test_scaled_frobenius_majorant_including_subnormals(magnitude):
    values = np.array([magnitude, -.25*magnitude, .5*magnitude])
    bound = proof.fro_upper(values)
    assert F(bound)**2 >= sum(F(float(v))**2 for v in values)


def test_scaled_constraint_boxes_enclose_exact_dimensional_operations():
    c = sparse.csr_matrix([[.3, -.7], [.9, .11]])
    left, right = np.array([.17, 3.]), np.array([.4, 7.])
    _, lo, hi = proof.scaled_data(c, left, right, divide_left=True)
    for i in range(2):
        for j in range(2):
            exact = F(float(c[i, j]))*F(float(right[j]))/F(float(left[i]))
            assert F(float(lo[i, j])) <= exact <= F(float(hi[i, j]))
    with pytest.raises(ValueError, match='positive'):
        proof.scaled_data(c, -left, right)


def test_complete_graph_error_contains_exact_local_kernel():
    c = np.array([[.3, .7, .2, .1], [-.6, .2, .5, .4]])
    matrix = sparse.csr_matrix(c)
    z, error, details = proof.graph_kernel(matrix, matrix, matrix,
        [np.array([0, 1])], [np.array([0, 1])])
    exact = product(inverse2(fractions(c[:, :2])), fractions(-c[:, 2:]))
    for i in range(2):
        for j in range(2):
            assert abs(F(float(z[i, j]))-exact[i][j]) <= F(error)
    np.testing.assert_array_equal(z[2:].toarray(), np.eye(2))
    assert details[0]['residual_one'] < 1.


def test_graph_rejects_incomplete_and_cross_support_pivots():
    c = sparse.csr_matrix([[1., .1, .2], [.5, 1., .3]])
    with pytest.raises(ValueError, match='another support'):
        proof.graph_kernel(c, c, c, [np.array([0]), np.array([1])], [np.array([0]), np.array([1])])
    with pytest.raises(ValueError, match='complete'):
        proof.graph_kernel(c, c, c, [np.array([0])], [np.array([0])])


def test_graph_checks_arithmetic_before_computing_bounds(monkeypatch):
    def reject():
        raise ArithmeticError('unsupported arithmetic')
    monkeypatch.setattr(proof, 'check_arithmetic', reject)
    monkeypatch.setattr(proof, 'inverse_bound', lambda *a: pytest.fail('inverse called before gate'))
    c = sparse.csr_matrix([[1., 1.]])
    with pytest.raises(ArithmeticError, match='unsupported arithmetic'):
        proof.graph_kernel(c, c, c, [np.array([0])], [np.array([0])])


def test_uncertain_local_inverse_cannot_claim_rank():
    with pytest.raises(ArithmeticError, match='rank'):
        proof.inverse_bound(np.array([[-.1]]), np.array([[2.1]]))


def test_stationary_error_contains_exact_nonsymmetric_saved_schur():
    k = np.array([[2., .2, .1, .3], [.21, 3., .4, .7],
                  [.11, .41, -2., .2], [.31, .71, .21, -3.]])
    scale = np.array([.3, 2.])
    x, block = np.array([0, 1]), np.array([2, 3])
    exact = fractions(k[:2, :2])
    extra = product(product(fractions(k[:2, 2:]), inverse2(fractions(k[2:, 2:]))), fractions(k[2:, :2]))
    exact = [[(exact[i][j]-extra[i][j])*F(float(scale[i]))*F(float(scale[j]))
              for j in range(2)] for i in range(2)]
    stored = np.array([[float(v) for v in row] for row in exact])
    stored[0, 1] += 1e-6
    bound, details = proof.stationary_error(sparse.csr_matrix(k), sparse.csr_matrix(stored), scale, x, [block])
    for i in range(2):
        for j in range(2):
            assert abs(F(float(stored[i, j]))-exact[i][j]) <= F(bound)
    assert bound < 1e-5 and details[0]['inverse_one_upper'] > 0.


def test_sparse_norm_majorant_matches_independent_symmetric_control():
    a = sparse.csr_matrix([[2., -1., 0.], [-1., 2., -1.], [0., -1., 2.]])
    assert proof.norm_upper(a) >= np.linalg.norm(a.toarray(), 2)
    np.testing.assert_array_equal(a.toarray(), [[2., -1., 0.], [-1., 2., -1.], [0., -1., 2.]])
