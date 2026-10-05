"""Independent direct Decimal rectangles versus binary64 prefix/Duffy norms."""
from decimal import Decimal, localcontext
from fractions import Fraction as F
import math

import pytest

from scripts import _b3_e4_f03_local_functional as binary
from scripts import _b3_e4_f03_local_norm_oracle as oracle
from scripts import _b3_e4_f03_spatial_contract as held


ZERO=(F(0),)*6


def record(value):
    return {key:getattr(value,key) for key in ('cuts','coefficients','cosine','atoms')}


def manufactured(cuts):
    # Per-interval degree-five values deliberately change at each cut.
    coefficients=tuple(tuple(tuple(F((i+1)*(c+2)*(-1)**(c+k)*(k+3),k+1)*10**5
        for k in range(6)) for c in range(3)) for i in range(len(cuts)-1))
    return binary.Functional(cuts,coefficients,(F(250000),F(-125000),F(60000)),
        ((F(170000),F(-90000),F(13000)),(F(-40000),F(270000),F(-21000))))


def test_constant_identities_do_not_drift_between_implementations():
    assert oracle.ELL==binary.ELL==F.from_float(.46)
    assert oracle.OMEGA==held.Q_OMEGA


@pytest.mark.parametrize('cuts',[(F(0),F(1)),(F(0),F(1,3),F(1)),
                                  (F(0),F(1,7),F(2,5),F(3,4),F(1))])
def test_degree_five_cosine_all_atoms_and_channels(cuts):
    value=manufactured(cuts)
    q16=oracle.norm_squared(record(value),order=16)
    q24=oracle.norm_squared(record(value),order=24)
    q64=binary.squared_norm(value)
    for low,high,fast in zip(q16.channels,q24.channels,q64['q64']['channels']):
        assert abs(low-high)/max(abs(high),Decimal(1))<Decimal('2e-20')
        assert fast==pytest.approx(float(high),rel=5e-13)
    assert q64['squared_norm']==pytest.approx(float(q24.total),rel=5e-13)


def test_collapsed_interval_with_large_density_keeps_measurable_mass():
    a=1-2*(held.Q_DX+held.Q_A);b=2*(held.Q_DX+held.Q_A)
    assert a<b and float(a)==float(b)
    intervals=((ZERO,ZERO,ZERO),((F(10**20),F(-2*10**20),F(3*10**20),F(0),F(0),F(0)),ZERO,ZERO),
               (ZERO,ZERO,ZERO))
    value=binary.Functional((F(0),a,b,F(1)),intervals,(F(0),)*3,((F(0),)*3,)*2)
    slow=oracle.norm_squared(record(value),order=24)
    fast=binary.squared_norm(value)
    assert float(slow.total)>10**6
    assert fast['squared_norm']==pytest.approx(float(slow.total),rel=2e-14)


def test_difference_subtracts_before_evaluating_large_nearly_equal_measures():
    first=manufactured((F(0),F(1,3),F(1)))
    common=F(10**24)
    base=binary.Functional(first.cuts,tuple(tuple(tuple(v+(common if k==0 else 0)
        for k,v in enumerate(poly)) for poly in row) for row in first.coefficients),
        tuple(v+common for v in first.cosine),
        tuple(tuple(v+common for v in row) for row in first.atoms))
    # A differently partitioned constant plus cosine and atoms represents
    # precisely the large common part, even though each norm would be huge.
    cuts=(F(0),F(1,5),F(3,5),F(1))
    other=binary.Functional(cuts,(((common,)+(F(0),)*5,)*3,)*3,
                            (common,)*3,((common,)*3,)*2)
    delta=binary.difference(base,other)
    slow=oracle.norm_squared(record(delta),order=24)
    expected=oracle.norm_squared(record(first),order=24)
    assert float(slow.total)==pytest.approx(float(expected.total),rel=1e-15)
    assert binary.squared_norm(delta)['squared_norm']==pytest.approx(float(expected.total),rel=5e-13)


def test_independent_signed_cross_form_and_atom_cancellation():
    # For z(s)=s, f=z-z''=s and atoms=(-z'(0),z'(1))=(-1,1).
    # Its exact Riesz energy is integral(s^2+1)=4/3, including cancellation.
    value=binary.Functional((F(0),F(1)),(((F(0),F(10**6),F(0),F(0),F(0),F(0)),ZERO,ZERO),),
        (F(0),)*3,((F(-10**6),F(0),F(0)),(F(10**6),F(0),F(0))))
    opposite=binary.Functional(value.cuts,tuple(tuple(tuple(-v for v in poly)
        for poly in row) for row in value.coefficients),value.cosine,
        tuple(tuple(-v for v in atom) for atom in value.atoms))
    q=oracle.green_inner(record(value),record(opposite),order=24)
    assert q[0]<0
    assert float(q[0])==pytest.approx(-4e12/3,rel=1e-15)
    fast=binary.squared_norm(value)
    assert fast['squared_norm']==pytest.approx(4e12/3,rel=3e-14)
    assert fast['q64']['atom_cross'][0]!=0
