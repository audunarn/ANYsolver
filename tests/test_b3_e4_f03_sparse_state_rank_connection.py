"""Connect saved scaling/rank checks to the synthetic candidate owner."""
import numpy as np
import pytest
from scipy import sparse

from scripts import _b3_e4_f03_scaled_sparse as scaled
from scripts import _b3_e4_f03_sparse_certificate as common
from scripts import _b3_e4_f03_sparse_state_binding as binding
from scripts import _b3_e4_f03_sparse_root_rank as rank
from scripts import _b3_e4_f03_spatial_contract as c


SB=common.SparseBudget(32,1024,4,8*1024**2)
BB=binding.BindingBudget(SB,4096,8192,8_000_000,64*1024**2)
RB=rank.RankBudget(SB,8192,8_000_000,160,64*1024**2)


def fixture():
    scale=c.E0/c.U0**2
    ks=sparse.diags((np.full(8,-1.),np.full(9,4.),np.full(8,-1.)),
                    (-1,0,1),format='csr')*scale
    kb=sparse.diags(np.linspace(1.,2.,9),format='csr')*scale
    root=sparse.csr_matrix(np.eye(3,9))
    slope=sparse.csr_matrix(np.eye(1,9,3))
    force=np.arange(1.,10.)*c.F0
    system=scaled.prepare(ks,kb,root,force,SB)
    candidate=scaled.solve_candidate(system,scaled.SolveBudget(SB,2048,32*32*8))
    return ks,kb,root,slope,force,system,candidate


def test_actual_candidate_binds_and_reverifies_without_solve(monkeypatch):
    ks,kb,root,slope,force,system,candidate=fixture()
    action=system.matrix@candidate.z
    before=candidate.work
    def forbidden(*args,**kwargs):pytest.fail('saved admission must not factor or solve')
    monkeypatch.setattr(scaled,'splu',forbidden)
    def check():
        state=binding.verify_binding(ks,kb,root,force,system.diagonal,
            system.matrix,system.rhs,candidate.q,candidate.eta,candidate.z,
            h_z=action,budget=BB)
        ports=rank.verify_root_rank(root,slope,system.diagonal,budget=RB)
        return state,ports
    state,ports=check()
    assert state['status']=='BINDING_PASSED'
    assert state['action_binding']=='VERIFIED'
    assert ports['status']=='PORT_RANK_PASSED'
    state2,ports2=check()
    assert state2==state and ports2['exact_gram']==ports['exact_gram']
    assert candidate.work==before
    assert before['candidate_rhs_solves']==1
    assert candidate.work['qualification_status']=='NOT_QUALIFIED'


def test_rebinding_a_changed_physical_block_detects_stale_scaled_candidate():
    ks,kb,root,slope,force,system,candidate=fixture()
    changed=ks.copy();changed.data[0]*=1.01
    result=binding.verify_binding(changed,kb,root,force,system.diagonal,
        system.matrix,system.rhs,candidate.q,candidate.eta,candidate.z,
        h_z=system.matrix@candidate.z,budget=BB)
    assert result['status']=='HOLD'
    assert result['checks']['H_entry_bit_mismatch_count']>0
    assert not result['checks']['D_relative_within_1e_12']
