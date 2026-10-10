import numpy as np
import pytest
from scipy import sparse
from scipy.sparse.linalg import splu
import prepared_static_response_m13_output_actions as module
from prepared_static_response_m13_output_actions import *

def owner(A=None,d=None):
    A=sparse.eye(2,format='csc') if A is None else sparse.csc_matrix(A)
    d=np.ones(A.shape[0]) if d is None else d
    return OutputActions(splu(A),A,d)

def test_identity_exact_ties_and_correlated_recovery_cancellation():
    graph,nodes=owner().prepare(np.array([1.,2.]))
    zero=graph.add(nodes[0],graph.negate(nodes[0]),'cancel')
    interval,contribution=graph.enclose(zero)
    assert contains(interval,0.) and contribution['native_forward']==0 and contribution['native_backward']==0
    assert not strict_max_excluded(interval,interval) and not strict_min_excluded(interval,interval)
    assert contribution['cancel']>0  # rounded add still conservatively included

def test_permutations_and_output_oracle_after_bound():
    A=np.array([[0.,0.,3.,0.],[4.,0.,0.,5.],[0.,6.,0.,0.],[7.,0.,0.,8.]])
    solver=splu(sparse.csc_matrix(A));d=np.array([2.,.5,4.,.25])
    bound=OutputActions(solver,A,d);rhs=np.array([1.,2.,3.,4.])
    graph,nodes=bound.prepare(rhs);row=np.array([1.,-2.,3.,-4.])
    node=graph.dot(row,nodes,'output_dot');interval,_=graph.enclose(node)
    actual=row@(d*solver.solve(d*rhs))
    assert contains(interval,actual)
    assert bound.metadata['nontrivial_row_permutation'] and bound.metadata['nontrivial_column_permutation']

def test_callback_cancel_and_selected_helper_authority(monkeypatch):
    bound=owner();called=[]
    def cancel():raise RuntimeError('cancelled')
    with pytest.raises(RuntimeError,match='cancelled'):bound.prepare(np.ones(2),cancel)
    original=module.triangular_center_error
    def foreign(*args):called.append(True);return original(*args)
    def mutate():monkeypatch.setattr(module,'triangular_center_error',foreign)
    with pytest.raises(ResidentRefusal,match='authority'):bound.prepare(np.ones(2),mutate)
    assert called==[]

def test_subnormal_and_refusal_boundaries():
    bound=owner(np.array([[1e308]]));graph,nodes=bound.prepare(np.array([1e-20]))
    interval,_=graph.enclose(nodes[0]);assert contains(interval,0.)
    with pytest.raises(ResidentRefusal,match='dot_count'):graph.dot([],[],'invalid')
    with pytest.raises(ResidentRefusal,match='nonfinite'):graph.dot([np.nan],nodes,'invalid')
    with pytest.raises(ResidentRefusal,match='overflow'):
        graph.new_node([ZERO],{},(Q(0),Q(10)**400),ZERO,'invalid')
    with pytest.raises(ResidentRefusal,match='scaling_overflow'):
        owner(np.eye(1),np.array([2.])).prepare(np.array([np.finfo(float).max]))
