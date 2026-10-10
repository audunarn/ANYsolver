import numpy as np
import pytest
from scipy import sparse
from scipy.sparse.linalg import splu
import prepared_static_response_m14_exact_actions as module
from prepared_static_response_m14_exact_actions import *

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

def test_exact_dyadic_rational_boundary_controls():
    assert scale_is_exact((TINY,TINY),Q(2))
    assert not scale_is_exact((TINY,TINY),Q(1,2))
    assert scale_is_exact((2*TINY,2*TINY),Q(1,2))
    assert not scale_is_exact((3*TINY,3*TINY),Q(1,2))
    assert scale_is_exact((2*MIN_NORMAL,4*MIN_NORMAL),Q(1,2))
    assert not scale_is_exact((MIN_NORMAL,2*MIN_NORMAL),Q(1,2))
    assert not scale_is_exact((-2*MIN_NORMAL,2*MIN_NORMAL),Q(1,2))
    assert not scale_is_exact((ZERO,4*MIN_NORMAL),Q(1,2))
    assert scale_is_exact((MAX_FINITE/2,MAX_FINITE/2),Q(2))
    assert not scale_is_exact((MAX_FINITE,MAX_FINITE),Q(2))
    assert not scale_is_exact((Q(1,10),Q(1,10)),ONE)
    for x in (TINY,2*TINY,MIN_NORMAL,MAX_FINITE):
        for factor in (Q(-1),Q(1),Q(2),Q(1,2)):
            if scale_is_exact((x,x),factor):
                assert rational(float(x*factor))==x*factor

def test_selector_exactness_multioperand_rounding_and_signed_zero_scope():
    graph,nodes=owner().prepare(np.array([-1.,2.]))
    before=len(graph.errors)
    selected=graph.dot([0.,-1.],nodes,'selector')
    assert len(graph.errors)==before
    cancelled=graph.dot([1.,1.],[nodes[0],graph.negate(nodes[0])],'two_term')
    assert len(graph.errors)>before
    assert contains(graph.enclose(cancelled)[0],0.)
    assert contains(graph.enclose(selected)[0],-2.)
    zero=graph.dot([0.,0.],nodes,'zero')
    assert graph.enclose(zero)[0]==(ZERO,ZERO)
    # Numerical zero equality only; no +/-zero payload identity claim.
    assert rational(-0.)==ZERO

def test_downscale_keeps_subnormal_allowance_and_overflow_refuses():
    graph,_=owner(np.eye(1)).prepare(np.ones(1))
    node=graph.new_node([ZERO],{},(TINY,TINY),ZERO,'point')
    # A synthetic represented point tests the primitive allowance itself.
    before=len(graph.errors)
    halved=graph.scale(node,.5,'half')
    assert len(graph.errors)>before and halved.interval[0]<=ZERO<=halved.interval[1]
    with pytest.raises(ResidentRefusal,match='scalar_overflow'):
        graph.scale(graph.new_node([ZERO],{},(MAX_FINITE,MAX_FINITE),ZERO,'max'),2.,'overflow')
    with pytest.raises(ResidentRefusal,match='zero_divisor'):graph.divide(node,0.,'zero')

