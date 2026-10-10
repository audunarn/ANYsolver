"""Independent small exact-solution controls for the signed action proof."""
from prepared_static_response_m10_bounds import *

def test_signed_action_and_permutation_known_solution():
    A=np.array([[1.,2.],[3.,5.]])
    bound=SignedActionBound(A)
    assert bound.accepted and list(bound.order)==[1,0]
    known=[Q(1),Q(2)]
    candidate=np.array([1.1,1.8])
    error=bound.error(np.array([5.,13.]),candidate)
    assert all(abs(rational(x)-exact)<=e for x,exact,e in zip(candidate,known,error))
    # Test action algebra directly, independently of the error calculation.
    u=[sum((a*b for a,b in zip(row,known)),ZERO) for row in bound.U]
    lu=[sum((a*b for a,b in zip(row,u)),ZERO) for row in bound.L]
    assert bound.signed_action(lu)==known

def test_signed_defect_refusal_and_zero_residual():
    ill=np.array([[1.,1.],[1.,np.nextafter(1.,np.inf)]])
    p,l,u=lu(ill);u[-1,-1]=1e-30
    assert not SignedActionBound(ill,(p,l,u)).accepted
    bound=SignedActionBound(np.array([[2.,0.],[0.,4.]]))
    assert bound.eta==0 and bound.error([2.,8.],[1.,2.])==[ZERO,ZERO]

def test_strict_interval_decisions_keep_equal_and_touching():
    a=(Q(0),Q(1));b=(Q(2),Q(3));touch=(Q(1),Q(2))
    assert strict_max_excluded(a,b) and strict_min_excluded(b,a)
    assert not strict_max_excluded(a,a) and not strict_max_excluded(a,touch)
