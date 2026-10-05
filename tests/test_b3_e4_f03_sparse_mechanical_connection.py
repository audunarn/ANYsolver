"""Candidate-to-admission connection on synthetic algebraic matrices only."""
import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_scaled_sparse as scaled
from scripts import _b3_e4_f03_sparse_certificate as common
from scripts import _b3_e4_f03_sparse_state_binding as binding
from scripts import _b3_e4_f03_sparse_equilibrium_checks as checks
from scripts import _b3_e4_f03_spatial_contract as c


def test_actual_scaled_candidate_passes_saved_mechanical_checks_without_resolve(monkeypatch):
    sb=common.SparseBudget(32,2048,4,8*1024**2)
    bb=binding.BindingBudget(sb,8192,16384,16_000_000,64*1024**2)
    eb=checks.EquilibriumBudget(bb,8192,16384,32_000_000,128*1024**2)
    scale=c.E0/c.U0**2
    shell=sparse.diags((np.full(8,-1.),np.full(9,4.),np.full(8,-1.)),
                      (-1,0,1),format='csr')*scale
    beam=sparse.diags(np.linspace(1.,2.,9),format='csr')*scale
    root=sparse.csr_matrix(np.eye(3,9));force=np.arange(1.,10.)*c.F0
    system=scaled.prepare(shell,beam,root,force,sb)
    candidate=scaled.solve_candidate(system,scaled.SolveBudget(sb,8192,32*32*8))
    saved_action=system.matrix@candidate.z
    before=candidate.work
    def forbidden(*args,**kwargs):pytest.fail('saved mechanical admission cannot solve')
    monkeypatch.setattr(scaled,'splu',forbidden)
    result=checks.verify_equilibrium(shell,beam,shell.copy(),beam.copy(),root,
        force,system.diagonal,system.matrix,system.rhs,candidate.q,candidate.eta,
        candidate.z,saved_action,budget=eb)
    assert result['status']=='NUMERICAL_MECHANICAL_CHECKS_PASSED'
    assert result['binding']['status']=='BINDING_PASSED'
    assert result['checks']['stationarity_scaled']<=1e-10
    assert result['checks']['root_compatibility_scaled']<=1e-10
    assert result['checks']['energy_identity_scaled']<=1e-10
    assert candidate.work==before
    assert result['work']['new_equilibrium_solves']==0
    assert before['candidate_rhs_solves']==1
    assert before['qualification_status']=='NOT_QUALIFIED'
