"""Synthetic SPD-plus-three-root scaling; no classical equilibrium fixture."""
from dataclasses import replace

import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_scaled_sparse as s
from scripts import _b3_e4_f03_sparse_certificate as verify
from scripts import _b3_e4_f03_spatial_contract as c


BUDGET = verify.SparseBudget(64, 4096, 4, 4*1024**2)
SOLVE = s.SolveBudget(BUDGET, 8192, 64*64*8)


def fixture():
    rng = np.random.default_rng(741)
    a = rng.normal(size=(9, 9))
    ks = (a.T@a+np.eye(9))*c.E0/c.U0**2
    kb = np.diag(np.linspace(1, 2, 9))*c.E0/c.U0**2
    root = rng.normal(size=(3, 9))
    f = rng.normal(size=9)*c.F0
    return sparse.csr_matrix(ks), sparse.csr_matrix(kb), sparse.csr_matrix(root), f


def test_scaling_equivalence_full_solve_and_same_factor_certificate():
    ks, kb, root, f = fixture()
    system = s.prepare(ks, kb, root, f, BUDGET)
    state = s.solve_candidate(system, SOLVE)
    physical = sparse.bmat(((ks+kb, root.T), (root, None))).toarray()
    expected = np.linalg.solve(physical, np.r_[f, np.zeros(3)])
    np.testing.assert_allclose(state.q, expected[:9], rtol=1e-12, atol=1e-17)
    np.testing.assert_allclose(state.eta, expected[9:], rtol=1e-12, atol=1e-7)
    assert np.linalg.norm((ks+kb)@state.q+root.T@state.eta-f)/c.F0 < 1e-12
    assert np.linalg.norm(root@state.q)/c.U0 < 1e-12
    assert abs(state.q@((ks+kb)@state.q)/c.E0-
               state.z[:9]@(system.stiffness@state.z[:9])) < 1e-12
    result = verify.certificate_a(system.matrix, state.inverse_blocks(), BUDGET,
                                   b=system.rhs, z=state.z)
    assert result['status'] == 'CERTIFIED_WITHIN_LIMIT'
    assert state.work['factorizations'] == 1
    assert state.work['candidate_rhs_solves'] == 1
    assert state.work['certificate_rhs_completed'] == 12
    assert state.work['certificate_solve_calls'] == 3
    assert state.work['qualification_status'] == 'NOT_QUALIFIED'


def test_scaling_owned_and_fixed_for_integration_check():
    ks, kb, root, f = fixture()
    system = s.prepare(ks, kb, root, f, BUDGET)
    old_d, old_h, old_f = system.diagonal, system.matrix, system.rhs
    plus = s.prepare(ks*1.01, kb, root, f, BUDGET, reference=system)
    np.testing.assert_array_equal(plus.diagonal, old_d)
    np.testing.assert_array_equal(plus.root_scale, system.root_scale)
    assert plus.metadata['primary_scaling'] is False
    ks.data[:] = 0; kb.data[:] = 0; root.data[:] = 0; f[:] = 0
    system.diagonal[:] = 7; system.matrix.data[:] = 7; system.rhs[:] = 7
    np.testing.assert_array_equal(system.diagonal, old_d)
    np.testing.assert_array_equal(system.matrix.data, old_h.data)
    np.testing.assert_array_equal(system.rhs, old_f)
    with pytest.raises(TypeError): system.metadata['energy_scale'] = 2
    with pytest.raises(TypeError): s.ScaledSystem()


def test_candidate_array_ownership_and_stream_cannot_restart():
    system = s.prepare(*fixture(), BUDGET)
    state = s.solve_candidate(system, SOLVE)
    q, z, eta = state.q, state.z, state.eta
    state.q[:] = 99; state.z[:] = 99; state.eta[:] = 99
    state.work['factorizations'] = 99
    np.testing.assert_array_equal(state.q, q)
    np.testing.assert_array_equal(state.z, z)
    np.testing.assert_array_equal(state.eta, eta)
    assert state.work['factorizations'] == 1
    stream = state.inverse_blocks()
    next(stream)
    stream.close()
    with pytest.raises(RuntimeError, match='already started'):
        next(state.inverse_blocks())
    assert state.work['certificate_rhs_attempted'] == 4
    assert state.work['certificate_rhs_completed'] == 4


def test_preflight_limits_fail_before_factorization(monkeypatch):
    system = s.prepare(*fixture(), BUDGET)
    def forbidden(*args, **kwargs):
        pytest.fail('native factorization before required preflight')
    monkeypatch.setattr(s, 'splu', forbidden)
    with pytest.raises(ValueError, match='evidence'):
        s.solve_candidate(system, replace(SOLVE, max_inverse_evidence_bytes=1))
    with pytest.raises(ValueError, match='budget|shape'):
        s.solve_candidate(system, replace(SOLVE, sparse_budget=replace(BUDGET, max_order=3)))


@pytest.mark.parametrize('failure', [MemoryError('owned test'), RuntimeError('backend test')])
def test_backend_exception_identity_propagates(monkeypatch, failure):
    system = s.prepare(*fixture(), BUDGET)
    def broken(*args, **kwargs): raise failure
    monkeypatch.setattr(s, 'splu', broken)
    with pytest.raises(type(failure)) as caught:
        s.solve_candidate(system, SOLVE)
    assert caught.value is failure


def test_fill_cap_and_inverse_failure_keep_attempted_work(monkeypatch):
    system = s.prepare(*fixture(), BUDGET)
    with pytest.raises(ValueError, match='fill'):
        s.solve_candidate(system, replace(SOLVE, max_factor_nnz=1))
    real_splu = s.splu
    class Factor:
        def __init__(self, *args, **kwargs):
            self.inner = real_splu(*args, **kwargs)
            self.L, self.U = self.inner.L, self.inner.U
        def solve(self, rhs):
            if rhs.ndim == 2: raise MemoryError('certificate block failure')
            return self.inner.solve(rhs)
    monkeypatch.setattr(s, 'splu', Factor)
    state = s.solve_candidate(system, SOLVE)
    with pytest.raises(MemoryError, match='certificate block'):
        next(state.inverse_blocks())
    assert state.work['certificate_rhs_attempted'] == 4
    assert state.work['certificate_rhs_completed'] == 0
    with pytest.raises(RuntimeError): next(state.inverse_blocks())


def test_invalid_blocks_and_diagonal_are_rejected():
    ks, kb, root, f = fixture()
    with pytest.raises(ValueError, match='three root'):
        s.prepare(ks, kb, root[:2], f, BUDGET)
    with pytest.raises(ValueError, match='positive finite'):
        s.prepare(-ks, -kb, root, f, BUDGET)
    with pytest.raises(ValueError, match='pattern envelope'):
        s.prepare(ks, kb, root, f, replace(BUDGET, max_nnz=90))
    with pytest.raises(ValueError, match='force'):
        s.prepare(ks, kb, root, np.full(9, np.nan), BUDGET)
