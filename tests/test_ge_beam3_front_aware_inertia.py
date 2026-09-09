from decimal import Decimal as D, localcontext
import pytest
from docs.reference_cases.ge_beam3_front_aware_inertia import inertia, choose_pivots
from docs.reference_cases.ge_beam3_decimal_inertia_audit import inertia as dense
from docs.reference_cases.ge_beam3_front_energy_inertia import audit


@pytest.mark.parametrize('digits',(80,100))
@pytest.mark.parametrize('n',(12,438))
def test_badly_scaled_signed_chain(digits,n):
    with localcontext() as c:
        c.prec=digits
        diagonal=[(-D(1) if i%7==0 else D(1))*D(10)**(6 if i%2 else -6) for i in range(n)]
        a=[[D(0)]*n for _ in range(n)]
        for i in range(n):
            a[i][i]=diagonal[i]+(diagonal[i-1]/16 if i else 0)
            if i:a[i][i-1]=a[i-1][i]=diagonal[i-1]/4
        result=inertia(a)
        assert result['negative']==sum(x<0 for x in diagonal)
        assert result['max_front']<=96 and result['updates']<=2_000_000
        assert D(result['reconstruction_relative'])<=D('1e-60')
        assert sorted(i for p in result['pivot_indices'] for i in p)==list(range(n))
        if n==12:assert dense(a)['negative']==result['negative']


def test_avoid_stable_high_degree_hub():
    a={0:{0:D('.01'),1:D(1)},1:{0:D(1),1:D(2),2:D(1),3:D(1)},
       2:{1:D(1),2:D(2)},3:{1:D(1),3:D(2)}}
    assert choose_pivots(a,D('1e-50'))==(2,)


def test_two_by_two_and_tiny_coupling():
    with localcontext() as c:
        c.prec=80
        a=[[D(0),D(2),D(0)],[D(2),D(0),D('1e-30')],[D(0),D('1e-30'),D(3)]]
        result=inertia(a)
        assert result['negative']==dense(a)['negative']==1
        assert 2 in result['pivot_sizes']


@pytest.mark.parametrize('kind',('fill','singular','nonfinite','asymmetric','cancel'))
def test_unchanged_fail_closed_bounds(kind):
    with localcontext() as c:
        c.prec=80
        a=[[D(2),D(1)],[D(1),D(2)]]
        if kind=='fill':a=[[D(2) if i==j else D(1) for j in range(100)] for i in range(100)]
        elif kind=='singular':a=[[D(0)]]
        elif kind=='nonfinite':a[0][0]=D('NaN')
        elif kind=='asymmetric':a[0][1]=D(0)
        def check():
            if kind=='cancel':raise ValueError('cancelled')
        with pytest.raises(ValueError):inertia(a,check)


@pytest.mark.parametrize('digits',(80,100))
def test_complete_energy_factor_contract(digits):
    identity=[[1.,0.],[0.,1.]]
    result=audit(identity,identity,[[-2.,.3],[.30000000000000004,0.]],identity,(0,1),(),(0.,),digits=digits)
    assert result['rows'][0]['negative']==1 and result['physical_dimension']==2
    assert not result['raw_geometric_symmetric'] and result['quadratic_form_preserved']
