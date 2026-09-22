from fractions import Fraction as F

import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_sparse_certificate as s
from scripts import _b3_e4_f03_local_condition_probe as exact


BUDGET = s.SparseBudget(512, 50_000, 16, 32*1024**2)


def blocks(y, width=3):
    return ((i, y[:, i:i+width]) for i in range(0, len(y), width))


@pytest.mark.parametrize('skew', [0., 1e-4])
def test_bounds_enclose_exact_rational_oracle_and_svd(skew):
    rng = np.random.default_rng(438)
    a = rng.normal(size=(9, 9))
    k = a.T@a+3*np.eye(9)
    c = rng.normal(size=(3, 9))
    h = np.block([[k, c.T], [c, np.zeros((3, 3))]])
    h[1, 2] += skew
    y = np.linalg.inv(h)
    b = np.r_[np.arange(1., 10.), np.zeros(3)]
    z = np.linalg.solve(h, b)
    result = s.certificate_a(sparse.csc_matrix(h), blocks(y), BUDGET, b=b, z=z)
    oracle = exact.certificate_a(h, inverse_columns=y, b=b, z=z)
    assert result['status'] == 'CERTIFIED_WITHIN_LIMIT'
    for actual, reference in (
            ('matrix_one_upper', 'h1_upper'),
            ('matrix_infinity_upper', 'hi_upper'),
            ('inverse_candidate_one_upper', 'y1_upper'),
            ('inverse_candidate_infinity_upper', 'yi_upper'),
            ('error_one_upper', 'e1_upper'), ('error_infinity_upper', 'ei_upper'),
            ('inverse_one_upper', 'b1_upper'), ('inverse_infinity_upper', 'bi_upper'),
            ('inverse_two_upper', 'inverse_2_upper'),
            ('condition_two_upper', 'condition_2_upper'),
            ('residual_two_upper', 'residual_2_upper'),
            ('backward_error_upper', 'backward_error_upper')):
        assert result[actual] >= oracle['bounds'][reference], (actual, result, oracle)
    sv = np.linalg.svd(h, compute_uv=False)
    assert result['condition_two_upper'] >= sv[0]/sv[-1]
    assert result['matrix_two_lower'] <= sv[0]
    assert result['inverse_columns'] == 12
    assert result['raw_inverse_evidence_bytes'] == 8*12**2


def test_block_partition_and_csc_csr_agree():
    h = np.array([[3., .7, 0.], [-.25, 2., .3], [.1, 0., 1.]])
    y = np.linalg.inv(h)
    a = s.certificate_a(sparse.csr_matrix(h), blocks(y, 1), BUDGET)
    b = s.certificate_a(sparse.csc_matrix(h), blocks(y, 3), BUDGET)
    for key in a:
        if key != 'inverse_blocks':
            assert a[key] == b[key]
    assert a['status'] == 'CONDITION_BOUND_ONLY'


def test_streams_beyond_dense_probe_cap_without_square_dense_storage(monkeypatch):
    n = 257
    h = sparse.diags(np.linspace(1, 2, n), format='csr')
    original = np.zeros
    def guarded(shape, *args, **kwargs):
        assert shape != (n, n), 'global dense matrix allocated'
        return original(shape, *args, **kwargs)
    monkeypatch.setattr(np, 'zeros', guarded)
    def supply():
        for start in range(0, n, 16):
            width = min(16, n-start)
            y = np.zeros((n, width))
            y[np.arange(start, start+width), np.arange(width)] = 1/h.diagonal()[start:start+width]
            yield start, y
    result = s.certificate_a(h, supply(), BUDGET)
    assert result['status'] == 'CONDITION_BOUND_ONLY'
    assert result['inverse_columns'] == n
    assert 2 <= result['condition_two_upper'] < 2.000001


def test_bad_inverse_and_ill_conditioned_matrix_hold():
    h = sparse.eye(3, format='csr')
    result = s.certificate_a(h, blocks(np.zeros((3, 3))), BUDGET)
    assert result['status'] == 'HOLD' and result['error_one_upper'] >= 1
    h = sparse.diags([1., 1e-11], format='csr')
    result = s.certificate_a(h, blocks(np.diag([1., 1e11])), BUDGET)
    assert result['status'] == 'HOLD' and result['condition_two_upper'] >= 1e11


def test_backward_error_rejects_bad_state_and_zero_denominator():
    h = sparse.eye(3, format='csr')
    result = s.certificate_a(h, blocks(np.eye(3)), BUDGET,
                             b=np.ones(3), z=np.ones(3)*1.001)
    assert result['status'] == 'HOLD'
    assert result['amplified_backward_upper'] > 1e-8
    with pytest.raises(ArithmeticError, match='denominator'):
        s.certificate_a(h, blocks(np.eye(3)), BUDGET, b=np.zeros(3), z=np.zeros(3))


@pytest.mark.parametrize('supply', [[], [(1, np.eye(3))],
    [(0, np.ones((3, 1)))], [(0, np.eye(3)), (3, np.ones((3, 1)))],
    [(0, np.full((3, 3), np.nan))]])
def test_inventory_is_complete_ordered_finite_and_unique(supply):
    with pytest.raises(ValueError):
        s.certificate_a(sparse.eye(3, format='csr'), supply, BUDGET)


@pytest.mark.parametrize('defect', ['short', 'outside', 'duplicate', 'descending', 'pointer'])
def test_bad_sparse_buffers_rejected_before_native_conversion(defect, monkeypatch):
    h = sparse.csr_matrix(np.ones((3, 3)))
    h.has_canonical_format = True
    if defect == 'short': h.indices = h.indices[:-1]
    if defect == 'outside': h.indices[0] = 3
    if defect == 'duplicate': h.indices[1] = h.indices[0]
    if defect == 'descending': h.indices[:3] = [2, 1, 0]
    if defect == 'pointer': h.indptr[1] = -1
    def forbidden(*args, **kwargs):
        raise AssertionError('native conversion before structural validation')
    monkeypatch.setattr(sparse.csr_matrix, 'tocsr', forbidden)
    with pytest.raises(ValueError): s.validate_sparse(h, BUDGET)


def test_budget_before_copy_or_consumption_and_owned_validation():
    h = sparse.eye(3, format='csc')
    owned = s.validate_sparse(h, BUDGET)
    h.data[:] = 7
    assert np.array_equal(owned.data, np.ones(3))
    def forbidden():
        raise AssertionError('blocks consumed after resource rejection')
        yield
    for budget in (s.SparseBudget(2, 100, 1, 10_000),
                   s.SparseBudget(4, 2, 1, 10_000),
                   s.SparseBudget(4, 100, 1, 10)):
        with pytest.raises(ValueError): s.certificate_a(h, forbidden(), budget)
    with pytest.raises(ValueError): s.SparseBudget(True, 1, 1, 1)


def test_interval_products_cover_cancellation_and_subnormal_products():
    tiny = np.finfo(np.float64).tiny
    h = s.validate_sparse(sparse.csr_matrix(
        [[1e100, -1e100, tiny], [.1, .2, .3], [tiny, 0., 0.]]), BUDGET)
    y = np.array([[1., .5], [1., -.5], [.5, tiny]])
    low, high = s._product_bounds(h, y)
    dense = h.toarray()  # bounded 3x3 independent exact test oracle only
    for i in range(3):
        for j in range(2):
            actual = sum((F(float(dense[i, k]))*F(float(y[k, j])) for k in range(3)), F(0))
            assert F(float(low[i, j])) <= actual <= F(float(high[i, j]))
    for v in (np.zeros(3), np.array([tiny, .2, -.3])):
        l, u = s._norm2(v)
        square = sum((F(float(x))**2 for x in v), F(0))
        assert F(l)**2 <= square <= F(u)**2


def test_nonfinite_arithmetic_and_partial_backward_request_propagate():
    h = sparse.diags([1e308, 1.], format='csr')
    with np.errstate(over='ignore'):
        with pytest.raises(ArithmeticError):
            s.certificate_a(h, blocks(np.eye(2)), BUDGET)
    with pytest.raises(ValueError, match='both'):
        s.certificate_a(sparse.eye(2, format='csr'), blocks(np.eye(2)), BUDGET,
                        b=np.ones(2))


@pytest.mark.parametrize('upper,factor', [(True, .9), (False, 1.1)])
def test_inaccurate_square_root_cannot_create_an_invalid_enclosure(monkeypatch, upper, factor):
    actual = s.math.sqrt
    monkeypatch.setattr(s.math, 'sqrt', lambda value: factor*actual(value))
    with pytest.raises(ArithmeticError, match='exact scalar'):
        s._sqrt(2., upper)


def test_negative_upper_square_root_cannot_pass_squared_check(monkeypatch):
    monkeypatch.setattr(s.math, 'sqrt', lambda value: -2.)
    with pytest.raises(ArithmeticError, match='square-root'):
        s._sqrt(2., True)
