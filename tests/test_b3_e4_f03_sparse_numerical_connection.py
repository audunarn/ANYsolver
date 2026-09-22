"""Connect numerical building blocks on synthetic scaled matrices only."""
import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_scaled_sparse as scaled
from scripts import _b3_e4_f03_sparse_certificate as common
from scripts import _b3_e4_f03_sparse_factor_candidate as factors
from scripts import _b3_e4_f03_sparse_positivity as positivity
from scripts import _b3_e4_f03_sparse_integration_checks as integration
from scripts import _b3_e4_f03_spatial_contract as c


SPARSE = common.SparseBudget(64, 4096, 4, 16*1024**2)
SOLVE = scaled.SolveBudget(SPARSE, 8192, 64*64*8)
FACTOR = factors.FactorBudget(SPARSE, 8192, 1024**2)
POSITIVE = positivity.PositivityBudget(SPARSE, 32768, 4096, 8192,
                                       16_000_000, 64*1024**2)
INTEGRATION = integration.IntegrationBudget(SPARSE, 8192, 8192,
                                            16_000_000, 64*1024**2)


def prepared_pair():
    rng = np.random.default_rng(892)
    a = rng.normal(size=(9, 9))
    scale = c.E0/c.U0**2
    ks = sparse.csr_matrix((a.T@a+3*np.eye(9))*scale)
    kb = sparse.diags(np.linspace(1, 2, 9)*scale, format='csr')
    root = sparse.csr_matrix(rng.normal(size=(3, 9)))
    load = rng.normal(size=9)*c.F0
    primary = scaled.prepare(ks, kb, root, load, SPARSE)
    alternate = scaled.prepare(ks*(1+2.**-44), kb, root,
                               load*(1+2.**-45), SPARSE, reference=primary)
    return primary, alternate


def test_connected_producer_solve_and_saved_column_verification(monkeypatch):
    primary, alternate = prepared_pair()
    candidate_factors = factors.produce(primary.stiffness, FACTOR)
    positive = factors.verify_against(primary.stiffness, candidate_factors, POSITIVE)
    assert positive['status'] == 'POSITIVE_QUADRATIC_FORM'
    candidate = scaled.solve_candidate(primary, SOLVE)
    saved = []
    def record():
        for start, block in candidate.inverse_blocks():
            saved.append((start, block.copy()))
            yield start, block
    direct = integration.verify_integration(primary.matrix, alternate.matrix,
        primary.rhs, alternate.rhs, candidate.z, record(), 9, budget=INTEGRATION)
    assert direct['status'] == 'NUMERICAL_PERTURBATION_PASSED'
    assert direct['scope'] == 'NUMERICAL_PERTURBATION_ONLY_NOT_SCALING_ADMISSION'
    assert candidate.work['candidate_rhs_solves'] == 1
    assert candidate.work['certificate_rhs_completed'] == 12
    assert candidate_factors.metadata['rhs_solve_count'] == 0
    before = candidate.work
    # Saved-only verification has no route to either factorization or solve.
    monkeypatch.setattr(factors, 'splu', lambda *a, **kw: pytest.fail('refactorization'))
    monkeypatch.setattr(scaled, 'splu', lambda *a, **kw: pytest.fail('refactorization'))
    replay = integration.verify_integration(primary.matrix, alternate.matrix,
        primary.rhs, alternate.rhs, candidate.z, iter(saved), 9, budget=INTEGRATION)
    assert replay == direct
    assert candidate.work == before
    assert replay['work']['alternate_equilibrium_solves'] == 0
    # These numerical passes cannot silently qualify a physical workflow.
    assert candidate.work['qualification_status'] == 'NOT_QUALIFIED'
    assert primary.metadata['qualification_status'] == 'NOT_QUALIFIED'


def test_changed_state_rechecks_primary_certificate_instead_of_reusing_status():
    primary, alternate = prepared_pair()
    candidate = scaled.solve_candidate(primary, SOLVE)
    saved = list(candidate.inverse_blocks())
    changed = candidate.z
    changed[0] += .01
    result = integration.verify_integration(primary.matrix, alternate.matrix,
        primary.rhs, alternate.rhs, changed, iter(saved), 9, budget=INTEGRATION)
    assert result['status'] == 'HOLD'
    assert result['primary_certificate']['status'] == 'HOLD'
    assert 'primary numerical certificate has not passed' in result['failures']
