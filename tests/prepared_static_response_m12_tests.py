import numpy as np
import pytest
from scipy import sparse
from scipy.sparse.linalg import splu
from prepared_static_response_m12_resident import *
from prepared_static_response_m10_bounds import contains

def test_identity_and_scaled_canonical_solve():
    A=sparse.eye(2,format='csc');solver=splu(A);d=np.array([2.,.5]);b=np.array([1.,3.])
    bound=ResidentSolveBound(solver,A,d)
    intervals=bound.enclose(b)
    actual=d*solver.solve(d*b)
    assert all(contains(i,x) for i,x in zip(intervals,actual))
    assert bound.defect==0

def test_row_column_permutation_and_factor_relation():
    A=sparse.csc_matrix([[0.,0.,3.,0.],[4.,0.,0.,5.],[0.,6.,0.,0.],[7.,0.,0.,8.]])
    solver=splu(A);bound=ResidentSolveBound(solver,A,np.ones(4))
    assert bound.metadata['nontrivial_row_permutation'] and bound.metadata['nontrivial_column_permutation']
    assert bound.defect<rational(1e-12)
    rhs=np.array([1.,2.,3.,4.]);intervals=bound.enclose(rhs)
    assert all(contains(i,x) for i,x in zip(intervals,solver.solve(rhs)))

def test_cancellation_and_diagonal_scaled_subnormal_quotient():
    A=sparse.csc_matrix([[1e16,1.,-1e16],[0.,1.,0.],[0.,0.,1.]])
    solver=splu(A);bound=ResidentSolveBound(solver,A,np.ones(3));rhs=np.array([0.,1.,1.])
    intervals=bound.enclose(rhs)
    assert all(contains(i,x) for i,x in zip(intervals,solver.solve(rhs)))
    T=[[rational(1e308)]];b=[rational(1e-20)]
    center,error=triangular_center_error(T,b,[ZERO],False)
    assert abs(center[0])<=error[0]  # native quotient may underflow to zero
    assert b[0]>4*TINY  # disproves a constant count*mu row allowance
    tiny=sparse.csc_matrix([[1e308]]);solver=splu(tiny)
    intervals=ResidentSolveBound(solver,tiny,np.ones(1)).enclose(np.array([1e-20]))
    assert contains(intervals[0],solver.solve(np.array([1e-20]))[0])

def test_refuse_backend_nonfinite_and_overflow():
    A=sparse.eye(1,format='csc');solver=splu(A)
    with pytest.raises(ResidentRefusal,match='SuperLU'):
        ResidentSolveBound(solver,A,np.ones(1),backend_name='pypardiso')
    with pytest.raises(ResidentRefusal,match='nonfinite'):
        ResidentSolveBound(solver,A,np.array([np.nan]))
    with pytest.raises(ResidentRefusal,match='scaling_overflow'):
        ResidentSolveBound(solver,A,np.array([2.])).enclose(np.array([np.finfo(float).max]))
    with pytest.raises(ResidentRefusal,match='rhs'):
        ResidentSolveBound(solver,A,np.ones(1)).enclose(np.array([np.inf]))

def test_signed_row_action_preserves_triangular_cancellation():
    T=matrix(np.array([[1.,0.,0.],[1e8,1.,0.],[1e8,1.,1.]]))
    center,error=triangular_center_error(T,[ONE,ONE,ONE],[ONE,ZERO,ZERO],True)
    assert center==[ONE,ONE-Q(100000000),ZERO]
    # Last exact inverse row is [0,-1,1], unlike the positive-comparison
    # recurrence whose first-column magnitude is 2e8.
    assert error[2]<Q(1,1000)
