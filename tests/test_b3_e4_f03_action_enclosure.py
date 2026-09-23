"""Analytical primitive and manufactured tests for real Action enclosures."""
from dataclasses import replace
from decimal import Decimal,localcontext
from fractions import Fraction as F

import numpy as np
import pytest

from scripts import _b3_e4_f03_action_enclosure as bound
from scripts import _b3_e4_f03_local_recovery as recovery
from scripts import _b3_e4_f03_spatial_contract as c

BUDGET=bound.ActionBudget(80,128,65536,100_000_000,1_000_000,128*1024**2)


def dec(x):return Decimal(x.numerator)/Decimal(x.denominator)


def primitive_oracle(action):
    # Independent integration-by-parts recurrence, with guard digits for
    # small intervals. This high-precision numerical oracle is not itself
    # a scientific acceptance certificate; the source uses exact bounds.
    def sincos(x):
        st=sv=x;ct=cv=Decimal(1)
        for k in range(1,500):
            st*=-x*x/Decimal((2*k)*(2*k+1));sv+=st
            ct*=-x*x/Decimal((2*k-1)*(2*k));cv+=ct
        return sv,cv
    with localcontext() as ctx:
        ctx.prec=600
        answer=dec(action.rational);omega=dec(c.Q_OMEGA)
        for a,b,p in action.cosine_terms:
            h=dec(b-a);delta=omega*h
            sa,ca=sincos(omega*dec(a));sb,cb=sincos(omega*dec(b))
            cm=(sb-sa)/delta;sm=(ca-cb)/delta;total=dec(p[0])*cm
            for j in range(1,len(p)):
                cm,sm=sb/delta-Decimal(j)*sm/delta,-cb/delta+Decimal(j)*cm/delta
                total+=dec(p[j])*cm
            answer+=h*total
        return +answer


def assert_contains(result,value):
    with localcontext() as ctx:
        ctx.prec=600
        assert dec(result['lower'])<=value<=dec(result['upper'])


@pytest.mark.parametrize('a,b,p',[
    (F(0),F(1),(F(1),)),
    (F(0),F(1),(F(0),F(1))),
    (F(1,7),F(5,6),(F(2),F(-3),F(5),F(-7),F(11),F(-13))),
    (F(1,2),F(1,2)+F(1,2**100),(F(1),F(2),F(-1)))])
def test_enclosure_contains_independent_analytical_primitives(a,b,p):
    action=recovery.Action(F(0),((a,b,p),))
    result=bound.enclose(action,budget=BUDGET)
    assert_contains(result,primitive_oracle(action))
    assert result['lower']<result['upper']
    assert result['work']['quadrature_evaluations']==0
    assert result['work']['equilibrium_solves']==0
    if float(a)==float(b):
        assert result['work']['retained_intervals']==1
        assert result['upper']<0


def test_exact_union_restriction_cancels_different_partitions_before_taylor():
    a=F(1,3)
    action=recovery.Action(F(7),((F(0),F(1),(F(0),F(1))),
        (F(0),a,(F(0),-a)),(a,F(1),(-a,-(1-a)))))
    result=bound.enclose(action,budget=replace(BUDGET,order=0))
    assert result['lower']==result['upper']==7
    assert result['work']['retained_intervals']==0
    assert result['normalized_sha256']==bound.enclose(recovery.Action(F(7)),budget=BUDGET)['normalized_sha256']


def test_overlapping_signed_intervals_match_independent_primitive_sum():
    action=recovery.Action(F(-3,7),((F(0),F(3,4),(F(1),F(-2))),
        (F(1,4),F(1),(F(-3),F(1),F(2)))))
    result=bound.enclose(action,budget=BUDGET)
    assert result['work']['union_intervals']==3
    assert_contains(result,primitive_oracle(action))


def test_exact_saved_threshold_and_definite_failure():
    action=recovery.Action(F(1));eps=F(1,2**50)
    assert bound.compare_saved(action,F(1)+eps,F(1),eps,budget=BUDGET)['status']=='PASSED'
    failed=bound.compare_saved(action,F(0),F(1),F(1,2),budget=BUDGET)
    assert failed['status']=='FAILED'
    assert failed['absolute_error_lower']==failed['absolute_error_upper']==1
    zero=bound.compare_saved(recovery.Action(F(0)),0.,1.,0.,budget=BUDGET)
    assert zero['status']=='PASSED'


def test_straddled_tolerance_holds_without_retry_and_declared_higher_order_passes():
    action=recovery.Action(F(0),((F(0),F(1),(F(1),)),))
    coarse=bound.compare_saved(action,0.,1.,1e-10,budget=replace(BUDGET,order=0))
    assert coarse['status']=='HOLD_UNRESOLVED'
    assert coarse['enclosure']['order']==0
    assert coarse['enclosure']['work']['automatic_retries']==0
    fine=bound.compare_saved(action,0.,1.,1e-10,budget=BUDGET)
    assert fine['status']=='PASSED'


def test_owned_action_input_and_binary64_saved_value():
    coefficients=[F(1),F(2)];terms=[[F(0),F(1),coefficients]]
    action=recovery.Action(F(0),terms)
    result=bound.enclose(action,budget=BUDGET)
    coefficients[0]=F(999);terms.clear()
    assert bound.enclose(action,budget=BUDGET)==result
    value=np.float64(float(primitive_oracle(action)))
    assert bound.compare_saved(action,value,1.,1e-12,budget=BUDGET)['status']=='PASSED'


def test_public_action_identity_matches_enclosure_without_evaluation():
    action=recovery.Action(F(7,11),((F(0),F(1),(F(1),F(-2))),))
    assert bound.action_identity(action)==bound.enclose(action,budget=BUDGET)['input_sha256']
    with pytest.raises(ValueError,match='Action'):
        bound.action_identity(F(7,11))


@pytest.mark.parametrize('change',[
    {'max_fraction_bits':1},{'max_total_bits':1},{'max_operations':1},
    {'max_work_bytes':1},{'max_intervals':1}])
def test_explicit_resource_caps(change):
    action=recovery.Action(F(2),((F(0),F(1,4),(F(1),)),(F(3,4),F(1),(F(1),))))
    with pytest.raises(ValueError,match='budget'):
        bound.enclose(action,budget=replace(BUDGET,**change))


def test_workspace_failure_precedes_taylor_evaluation(monkeypatch):
    def forbidden(*args,**kwargs):pytest.fail('Taylor evaluation before resource guard')
    monkeypatch.setattr(bound,'_center',forbidden)
    action=recovery.Action(F(0),((F(0),F(1),(F(1),)),))
    with pytest.raises(ValueError,match='workspace'):
        bound.enclose(action,budget=replace(BUDGET,max_work_bytes=1))


@pytest.mark.parametrize('saved,scale,limit',[(np.nan,1.,1e-10),(0.,0.,1e-10),(0.,1.,-1.)])
def test_nonfinite_saved_value_and_invalid_scales_rejected(saved,scale,limit):
    with pytest.raises(ValueError):
        bound.compare_saved(recovery.Action(F(0)),saved,scale,limit,budget=BUDGET)


@pytest.mark.parametrize('saved,scale,limit',[
    (F(0),F(2**1000),F(0)),(F(0),F(1),F(2**1000)),
    (F(2**1000),F(2**1000),F(1))])
def test_comparison_operands_cannot_evade_budget_with_small_result(saved,scale,limit):
    with pytest.raises(ValueError,match='budget'):
        bound.compare_saved(recovery.Action(F(0)),saved,scale,limit,
                            budget=replace(BUDGET,max_fraction_bits=2))
