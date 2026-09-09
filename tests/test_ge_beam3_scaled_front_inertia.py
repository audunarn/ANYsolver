from decimal import Decimal as D,localcontext
from fractions import Fraction as F
import pytest
from docs.reference_cases.ge_beam3_scaled_front_inertia import inertia
from docs.reference_cases.ge_beam3_decimal_inertia_audit import inertia as dense


@pytest.mark.parametrize('digits',(80,100))
@pytest.mark.parametrize('n',(12,438))
def test_scaled_indefinite_chain_original_reconstruction(digits,n):
    with localcontext() as ctx:
        ctx.prec=digits
        diagonal=[(-D(1) if i%7==0 else D(1))*D(10)**(10 if i%2 else -10) for i in range(n)]
        a=[[D(0)]*n for _ in range(n)]
        for i in range(n):
            a[i][i]=diagonal[i]+(diagonal[i-1]/16 if i else 0)
            if i:a[i][i-1]=a[i-1][i]=diagonal[i-1]/4
        before=[r[:] for r in a];r=inertia(a)
        assert a==before and r['negative']==sum(x<0 for x in diagonal)
        assert r['positive_diagonal_congruence'] and r['max_front']<=96
        assert D(r['original_reconstruction_bound'])<=D('1e-60')
        if n==12:assert dense(a)['negative']==r['negative']


def test_exact_coordinate_congruence_identity():
    a=[[F(1,3),F(2,7)],[F(2,7),F(-3,11)]];s=[F(D('1.123456789')),F(D('123.456789'))];x=[F(7,13),F(-11,19)]
    b=[[a[i][j]*s[i]*s[j] for j in range(2)] for i in range(2)]
    assert sum(x[i]*b[i][j]*x[j] for i in range(2) for j in range(2))==sum((s[i]*x[i])*a[i][j]*(s[j]*x[j]) for i in range(2) for j in range(2))


def test_zero_diagonal_block_and_exact_source_preserved():
    with localcontext() as ctx:
        ctx.prec=80
        a=[[D(0),D('1e-8')],[D('1e-8'),D(0)]]
        r=inertia(a)
        assert r['negative']==1 and r['pivot_sizes']==[2]
        assert a[0][0]==0


@pytest.mark.parametrize('kind',('zero','asymmetric','nonfinite','fill','cancel'))
def test_scaled_bounds(kind):
    with localcontext() as ctx:
        ctx.prec=80
        a=[[D(2),D(1)],[D(1),D(2)]]
        if kind=='zero':a=[[D(0)]]
        elif kind=='asymmetric':a[0][1]=D(0)
        elif kind=='nonfinite':a[0][0]=D('Infinity')
        elif kind=='fill':a=[[D(2) if i==j else D(1) for j in range(100)] for i in range(100)]
        def check():
            if kind=='cancel':raise ValueError('cancelled')
        with pytest.raises(ValueError):inertia(a,check)
