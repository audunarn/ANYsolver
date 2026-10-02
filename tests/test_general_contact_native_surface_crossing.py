"""Analytic zero counts independent of the production geometry adapter."""
from math import acos,ceil,cos,floor,pi,sin

import pytest

from anysolver.general_contact.native_surface_crossing import GapSlabEnclosure,certify_single_crossing
from anysolver.general_contact.native_surface_support import SupportIntervalBudget


def rotating_family(phase,travel,level):
    # Whole spatial angular strip, including every angle between these limits.
    strip=(-.02,.02)
    def extrema(function,left,right,stationary_offset):
        points=[left,right]
        points.extend(stationary_offset+k*pi for k in range(
            ceil((left-stationary_offset)/pi),floor((right-stationary_offset)/pi)+1))
        values=[function(x) for x in points]
        return min(values),max(values)
    def enclose(left,right):
        low=phase+travel*left+strip[0];high=phase+travel*right+strip[1]
        gl,gu=extrema(cos,low,high,0.)
        dl,du=extrema(lambda x:-travel*sin(x),low,high,pi/2)
        # Conservative arithmetic allowance for this bounded analytic fixture.
        return GapSlabEnclosure(gl-level-1e-12,gu-level+1e-12,dl-1e-12,du+1e-12)
    def roots(offset):
        alpha=acos(level)
        return sorted(t for k in range(-3,4) for sign in (-1,1)
            if 0.<(t:=(sign*alpha+2*pi*k-phase-offset)/travel)<1.)
    return enclose,roots


def test_extremum_away_from_contact_allows_one_transverse_crossing():
    enclose,roots=rotating_family(-.4,2.,.7)
    assert all(len(roots(offset))==1 for offset in (-.02,0.,.02))
    # g' changes sign; the old whole-segment monotonicity proof cannot pass.
    assert enclose(0.,1.).derivative_lower<0<enclose(0.,1.).derivative_upper
    budget=SupportIntervalBudget(128)
    assert certify_single_crossing(enclose,budget=budget)
    assert 1<budget.intervals<128


def test_two_crossings_cannot_pass_even_with_same_signed_endpoints():
    enclose,roots=rotating_family(-1.2,2.4,.7)
    assert all(len(roots(offset))==2 for offset in (-.02,0.,.02))
    assert enclose(0.,0.).gap_upper<0 and enclose(1.,1.).gap_upper<0
    assert not certify_single_crossing(enclose,budget=SupportIntervalBudget(128))


def test_unresolved_tangency_consumes_bounded_budget_and_rejects():
    def tangent(left,right):
        minimum=0. if left<=.5<=right else min((left-.5)**2,(right-.5)**2)
        return GapSlabEnclosure(minimum,max((left-.5)**2,(right-.5)**2),2*(left-.5),2*(right-.5))
    budget=SupportIntervalBudget(8)
    assert not certify_single_crossing(tangent,budget=budget)
    assert budget.intervals==8


def test_strictly_open_gap_needs_no_derivative_sign():
    budget=SupportIntervalBudget(1)
    assert certify_single_crossing(lambda l,r:GapSlabEnclosure(1.,2.,-5.,5.),budget=budget)
    assert budget.intervals==1


@pytest.mark.parametrize('values',[(float('nan'),1.,0.,1.),(2.,1.,0.,1.),(0.,1.,2.,1.)])
def test_invalid_enclosures_rejected(values):
    with pytest.raises(ValueError,match='ordered'):
        GapSlabEnclosure(*values)
