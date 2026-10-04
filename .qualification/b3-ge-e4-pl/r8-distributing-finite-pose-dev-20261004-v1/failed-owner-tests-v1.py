"""Private owner-local finite saddle assembly; no public finite admission."""
from dataclasses import replace

import numpy as np
import pytest
from scipy import sparse
from scipy.sparse import linalg as spla

from anysolver._ge_beam3_pose_joint import _exp_terms
from anysolver._stiffened_shell_ge_distributing_finite import PreparedFiniteDistributingAttachment
from anysolver._stiffened_shell_ge_finite_experimental import FinitePointDriver
from anysolver._stiffened_shell_ge_experimental import ExperimentalGEAnalysis
from test_stiffened_shell_ge_distributing_reference import _multi_definition, _multi_selection


@pytest.fixture(scope="module")
def model():
    owner = ExperimentalGEAnalysis(replace(_multi_definition(), points=()))
    adapter = PreparedFiniteDistributingAttachment(owner, _multi_selection())
    driver = FinitePointDriver(owner)
    try:
        yield owner, adapter, driver
    finally:
        owner.close()


def error(value, reference):
    return np.linalg.norm(value-reference)/max(np.linalg.norm(reference), 1e-12)


def test_reference_saddle_sparse_dense_and_physical_solution(model):
    owner, adapter, driver = model
    count = owner._K.shape[0]
    block = adapter.evaluate(owner, driver._state, np.zeros(6))
    residual, attachment = block.scatter(count+6)
    rows, cols = np.nonzero(adapter.reference.constraint_matrix)
    C = sparse.coo_matrix((adapter.reference.constraint_matrix[rows,cols],
        (rows, adapter.reference.gather_slots[cols])), shape=(6,count)).tocsr()
    independent = sparse.bmat(((owner._K,C.T),(C,None)),format="csr")
    assembled = sparse.block_diag((owner._K,sparse.csr_matrix((6,6))),format="csr")+attachment
    assert error(assembled.toarray(), independent.toarray()) < 1e-12
    assert np.max(np.abs(residual)) < 1e-14
    free = np.r_[owner._free, count+np.arange(6)]
    force = np.zeros(count+6)
    force[owner._shell_count+6*owner._beam_index[103]+1] = .01
    A = assembled[free,:][:,free]
    answer = spla.splu(A.tocsc()).solve(force[free])
    dense = np.linalg.solve(independent[free,:][:,free].toarray(),force[free])
    assert error(answer,dense)<1e-10
    assert np.linalg.norm(A@answer-force[free])<1e-10
    q = np.zeros(count);q[owner._free]=answer[:-6]
    assert np.max(np.abs(C@q))<1e-12


@pytest.mark.parametrize("step",(2e-4,2e-5,2e-6))
def test_actual_owner_updates_with_multiplier_columns(model,step):
    owner,adapter,driver=model;count=owner._K.shape[0]
    rng=np.random.default_rng(818)
    move=rng.normal(size=count)*1e-3;move[owner._fixed]=0.
    state=driver._advance(driver._state,move,1.)
    lam=np.array((.1,-.2,.3,.02,-.03,.04))
    direction=rng.normal(size=count+6);direction[owner._fixed]=0.
    direction/=np.linalg.norm(direction)
    block=adapter.evaluate(owner,state,lam)
    local=direction[block.slots]
    def residual(alpha):
        trial=driver._advance(state,direction[:count],alpha)
        return adapter.evaluate(owner,trial,lam+alpha*direction[count:]).residual
    fd=(residual(step)-residual(-step))/(2*step)
    assert error(fd,block.tangent@local)<1e-7
    assert np.linalg.norm(block.tangent.toarray()-block.tangent.toarray().T)>1e-4


def test_existing_global_element_rows_and_attachment_derivative(model):
    owner,adapter,driver=model;count=owner._K.shape[0]
    rng=np.random.default_rng(541)
    move=rng.normal(size=count)*1e-5;move[owner._fixed]=0.
    state=driver._advance(driver._state,move,1.)
    lam=np.array((.1,-.2,.3,.02,-.03,.04))
    direction=rng.normal(size=count+6);direction[owner._fixed]=0.
    direction/=np.linalg.norm(direction)
    def assemble(s,multipliers):
        base=driver._assemble(s,0.,driver._shell_origins,driver._beam_origins,
                              pattern=np.zeros(count))
        part=adapter.evaluate(owner,s,multipliers)
        residual,matrix=part.scatter(count+6)
        residual=np.r_[base[0],np.zeros(6)]+residual
        matrix=sparse.block_diag((base[1],sparse.csr_matrix((6,6))),format="csr")+matrix
        return residual,matrix
    residual,matrix=assemble(state,lam)
    step=2e-6
    plus=assemble(driver._advance(state,direction[:count],step),lam+step*direction[count:])[0]
    minus=assemble(driver._advance(state,direction[:count],-step),lam-step*direction[count:])[0]
    assert error((plus-minus)/(2*step),matrix@direction)<1e-6


def test_chart_anchors_do_not_change_physical_trial_or_spatial_rows(model):
    owner,adapter,driver=model;count=owner._K.shape[0]
    q=driver._state.q.copy()
    q[:owner._shell_count].reshape(-1,6)[:,3:]=(.2,-.1,.12)
    state=replace(driver._state,q=q)
    anchors=np.tile(_exp_terms(np.array((.2,-.1,.12)))[0],(len(owner._shell_ids),1,1))
    rebased=q.copy();rebased[:owner._shell_count].reshape(-1,6)[:,3:]=0.
    changed=replace(state,q=rebased,shell_anchors=anchors)
    lam=np.array((.1,-.2,.3,.02,-.03,.04))
    a,b=adapter.evaluate(owner,state,lam),adapter.evaluate(owner,changed,lam)
    assert error(a.residual,b.residual)<1e-12
    assert error(a.shell_node_actions,b.shell_node_actions)<1e-12
    assert np.allclose(a.gap,b.gap,atol=1e-14,rtol=0.)


def test_exerted_recovery_balance_virtual_work_and_owned_buffers(model):
    owner,adapter,driver=model;count=owner._K.shape[0]
    rng=np.random.default_rng(75)
    state=driver._advance(driver._state,rng.normal(size=count)*1e-3,1.)
    lam=np.array((.1,-.2,.3,.02,-.03,.04));block=adapter.evaluate(owner,state,lam)
    assert error(block.shell_action[:3],-block.beam_action[:3])<1e-12
    arm=(block.beam_position-block.centroid)+(block.beam_position_low-block.centroid_low)
    assert np.linalg.norm(block.shell_action[3:]+block.beam_action[3:]+np.cross(arm,block.beam_action[:3]))<1e-12
    velocity=np.tile(np.r_[.03,-.02,.01,.1,.2,-.1],(len(adapter.pose.node_ids)+1,1))
    actions=np.vstack((block.shell_node_actions,block.beam_action))
    assert np.isclose(np.sum(actions*velocity),-block.residual[:-6]@velocity.ravel(),atol=1e-14)
    retained=np.arange(owner._shell_count+6*len(owner._beam_ids),count)
    assert not np.any(np.isin(block.slots,retained))
    for array in (block.residual,block.slots,block.shell_node_actions,block.tangent.data):
        with pytest.raises(ValueError):array.setflags(write=True)
    saved=block.residual.copy();state.q[:]=0.;lam[:]=0.
    assert np.array_equal(block.residual,saved)
    assert not block.owner_binding_authorized and not block.production_qualified


def test_mapping_preparation_is_immutable_and_stale_owner_rejected(model):
    owner,adapter,driver=model
    with pytest.raises(AttributeError):adapter.model_identity="changed"
    with pytest.raises(ValueError):adapter.evaluate(object(),driver._state,np.zeros(6))
    with pytest.raises(ValueError):adapter.evaluate(owner,driver._state,np.zeros(6),multiplier_row_start=-1)
    block=adapter.evaluate(owner,driver._state,np.zeros(6),multiplier_row_start=7)
    assert np.array_equal(block.slots[-6:],owner._K.shape[0]+7+np.arange(6))
    with pytest.raises(ValueError):block.scatter(owner._K.shape[0]+12)


def test_closed_owner_rejected_without_changing_public_admission():
    owner=ExperimentalGEAnalysis(replace(_multi_definition(),points=()))
    adapter=PreparedFiniteDistributingAttachment(owner,_multi_selection())
    state=FinitePointDriver(owner)._state
    owner.close()
    with pytest.raises(RuntimeError,match="closed"):adapter.evaluate(owner,state,np.zeros(6))
