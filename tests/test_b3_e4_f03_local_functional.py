"""Synthetic full-H1 Green functional checks, without scientific states."""
from fractions import Fraction
import math

import pytest

from scripts import _b3_e4_f03_local_functional as f
from scripts import _b3_e4_f03_spatial_contract as c


Z=Fraction(0)
O=Fraction(1)


def _functional(cuts=(Z,O),polys=None,cosine=(Z,Z,Z),atoms=None):
    if polys is None:
        polys=tuple(((Z,)*6,)*3 for _ in range(len(cuts)-1))
    if atoms is None: atoms=((Z,Z,Z),(Z,Z,Z))
    return f.Functional(cuts,polys,cosine,atoms)


def _one_channel(polys,cuts=(Z,O),channel=0,atoms=None,cosine=(Z,Z,Z)):
    rows=[]
    for poly in polys:
        row=[(Z,)*6 for _ in range(3)]
        row[channel]=tuple(poly)
        rows.append(tuple(row))
    return _functional(cuts,tuple(rows),cosine,atoms)


def test_constant_riesz_and_free_endpoint_green_atoms():
    constant=_one_channel(((O,Z,Z,Z,Z,Z),))
    result=f.squared_norm(constant)
    assert result['squared_norm']==pytest.approx(1.,rel=2e-14)
    assert result['resolution']<=f.RESOLUTION_LIMIT
    assert result['q64']['diagonal'][0]==pytest.approx(1.,rel=2e-14)
    assert result['q64']['offdiagonal']==[0.,0.,0.]
    root=_functional(atoms=((O,Z,Z),(Z,Z,Z)))
    assert f.squared_norm(root)['squared_norm']==pytest.approx(
        math.cosh(1)/math.sinh(1),rel=3e-15)
    both=_functional(atoms=((O,Z,Z),(O,Z,Z)))
    assert f.squared_norm(both)['squared_norm']==pytest.approx(
        2*(math.cosh(1)+1)/math.sinh(1),rel=3e-15)
    assert f.norm_at_order(both,48)['atom_gram'][0]==pytest.approx(
        2*(math.cosh(1)+1)/math.sinh(1))


def test_linear_riesz_polynomial_with_exact_partition_restrictions():
    # Solve -w''+w=s with Neumann w'(0)=w'(1)=0, then integrate s*w.
    sh,ch=math.sinh(1),math.cosh(1)
    A=(ch-1)/sh
    target=1/3+A*(sh-ch+1)-(ch-sh)
    whole=_one_channel(((Z,O,Z,Z,Z,Z),))
    cuts=(Z,Fraction(1,7),Fraction(5,9),O)
    pieces=tuple((a,b-a,Z,Z,Z,Z) for a,b in zip(cuts,cuts[1:]))
    partitioned=_one_channel(pieces,cuts)
    assert f.squared_norm(whole)['squared_norm']==pytest.approx(target,rel=3e-14)
    assert f.squared_norm(partitioned)['squared_norm']==pytest.approx(target,rel=3e-14)
    assert f.norm_at_order(partitioned,48)['offdiagonal'][0]!=0
    assert f.difference(whole,partitioned).exact_zero


def test_union_subtraction_cosine_atoms_and_exact_zero():
    whole=_one_channel(((Fraction(3),Fraction(2),O,Z,Z,Z),),
                      cosine=(Z,Fraction(7),Z),
                      atoms=((Fraction(5),Z,Fraction(2)),(Z,Fraction(-3),Z)))
    cuts=(Z,Fraction(1,3),O)
    rows=[]
    for a,b in zip(cuts,cuts[1:]):
        h=b-a
        row=[(Z,)*6 for _ in range(3)]
        row[0]=(3+2*a+a*a,2*h*(1+a),h*h,Z,Z,Z)
        rows.append(tuple(row))
    other=_functional(cuts,tuple(rows),(Z,Fraction(7),Z),
                      ((Fraction(5),Z,Fraction(2)),(Z,Fraction(-3),Z)))
    diff=f.difference(whole,other)
    assert diff.cuts==cuts and diff.exact_zero
    result=f.squared_norm(diff)
    assert result['norm']==0 and result['resolution']==0
    assert result['q48']['exact_zero'] and result['q64']['exact_zero']


def test_moment_scaled_once_and_channels_do_not_invent_lever_arms():
    theta=_one_channel(((f.ELL,Z,Z,Z,Z,Z),),channel=2,
                       atoms=((Z,Z,f.ELL),(Z,Z,Z)))
    equivalent=_one_channel(((O,Z,Z,Z,Z,Z),),channel=0,
                            atoms=((O,Z,Z),(Z,Z,Z)))
    t=f.squared_norm(theta);e=f.squared_norm(equivalent)
    assert t['squared_norm']==pytest.approx(e['squared_norm'],rel=1e-15)
    assert t['q64']['channels'][2]==pytest.approx(e['q64']['channels'][0])
    y_only=_one_channel(((O,Z,Z,Z,Z,Z),),channel=1)
    assert f.squared_norm(y_only)['q64']['channels']==pytest.approx([0.,1.,0.])


def test_cosine_local_phase_partition_and_polarization():
    a=_one_channel(((Fraction(2),Z,Z,Z,Z,Z),),
                   cosine=(Fraction(1,4),Z,Z))
    b=_one_channel(((Z,Fraction(1,3),Z,Z,Z,Z),))
    neg_b=_one_channel(((Z,Fraction(-1,3),Z,Z,Z,Z),))
    plus=f.difference(a,neg_b)
    minus=f.difference(a,b)
    norm=lambda x:f.norm_at_order(x,64)['squared_norm']
    assert norm(plus)+norm(minus)==pytest.approx(2*(norm(a)+norm(b)),rel=2e-13)
    cuts=(Z,Fraction(1,5),Fraction(1,2),O)
    pieces=_one_channel(tuple(((Fraction(2),Z,Z,Z,Z,Z) for _ in range(3))),
                        cuts,cosine=(Fraction(1,4),Z,Z))
    assert f.squared_norm(a)['squared_norm']==pytest.approx(
        f.squared_norm(pieces)['squared_norm'],rel=3e-14)


def test_collapsed_binary64_interval_preserves_local_positive_mass():
    near=2*(c.Q_DX+c.Q_A);other=1-near
    lo,hi=sorted((near,other))
    assert lo<hi and float(lo)==float(hi)
    local=_one_channel(((Z,)*6,(Fraction(10000),Z,Z,Z,Z,Z),(Z,)*6),
                       (Z,lo,hi,O))
    q=f.norm_at_order(local,48)
    assert q['squared_norm']>0 and math.isfinite(q['squared_norm'])
    assert q['diagonal'][0]>0 and q['offdiagonal'][0]==0
    assert f.squared_norm(local)['resolution']<=f.RESOLUTION_LIMIT


@pytest.mark.parametrize('denominator', (10**161, 10**150))
def test_active_duffy_weights_must_be_normal_even_with_other_density(denominator):
    width=Fraction(1,denominator)
    zero=(Z,)*6
    local=_functional((Z,width,O),(
        ((1/width,Z,Z,Z,Z,Z),zero,zero),
        ((O,Z,Z,Z,Z,Z),(O,Z,Z,Z,Z,Z),zero)))
    # The second interval and y channel have ordinary nonzero norms; they
    # cannot conceal an unrepresented first-interval Duffy contribution.
    for order in (48,64):
        with pytest.raises(ValueError,match='Duffy.*underflow|Duffy.*subnormal'):
            f.norm_at_order(local,order)
    with pytest.raises(ValueError,match='Duffy.*underflow|Duffy.*subnormal'):
        f.squared_norm(local)


def test_input_ownership_bit_caps_union_and_numerical_rejections(monkeypatch):
    cuts=[Z,O];polys=[[[Z]*6 for _ in range(3)]]
    polys[0][0][0]=O
    input_f=f.Functional(cuts,polys,[Z,Z,Z],[[Z,Z,Z],[Z,Z,Z]])
    cuts[1]=Fraction(1,2);polys[0][0][0]=Fraction(9)
    assert input_f.cuts==(Z,O) and input_f.coefficients[0][0][0]==O
    assert isinstance(input_f.coefficients[0][0],tuple)
    with pytest.raises(ValueError,match='rational integer bit cap'):
        _one_channel(((Fraction(2**4096),Z,Z,Z,Z,Z),))
    with pytest.raises(ValueError,match='positive exact'):
        _functional((Z,Z,O),(((Z,)*6,)*3,)*2)
    with pytest.raises(ValueError,match='exact Fraction'):
        _functional((Z,O),(((0.,)*6,)*3,))
    with pytest.raises(ValueError,match='inventory'):
        _functional(tuple(Fraction(i,2049) for i in range(2050)),
                    tuple((((Z,)*6,)*3 for _ in range(2049))))
    tiny=_one_channel(((O,Z,Z,Z,Z,Z),(Z,)*6),
                      (Z,Fraction(1,10**400),O))
    with pytest.raises(ValueError,match='underflow'):
        f.norm_at_order(tiny,48)
    tiny_area=_one_channel(((O,Z,Z,Z,Z,Z),(Z,)*6),
                           (Z,Fraction(1,10**200),O))
    with pytest.raises(ValueError,match='Green area underflows'):
        f.norm_at_order(tiny_area,48)
    tiny_atom=_functional(atoms=((Fraction(1,10**200),Z,Z),(Z,Z,Z)))
    with pytest.raises(ValueError,match='atom square underflows'):
        f.norm_at_order(tiny_atom,48)
    tiny_density=_one_channel(((Fraction(1,10**200),Z,Z,Z,Z,Z),))
    with pytest.raises(ValueError,match='nonzero exact channel has zero'):
        f.norm_at_order(tiny_density,48)
    with pytest.raises(ValueError,match='fixed Green'):
        f.norm_at_order(input_f,32)
    original=f.norm_at_order
    def inconsistent(value,order=48):
        result=original(value,order)
        if order==64:
            result['channels'][0]+=1.
            result['squared_norm']+=1.
        return result
    monkeypatch.setattr(f,'norm_at_order',inconsistent)
    with pytest.raises(ValueError,match='unresolved'):
        f.squared_norm(input_f)


def test_exact_union_max_4095_intervals_without_input_cap_bypass():
    first_cuts=tuple(Fraction(i,2048) for i in range(2049))
    other_cuts=(Z,)+tuple(Fraction(2*i+1,4096) for i in range(2047))+(O,)
    zero=((Z,)*6,)*3
    first=_functional(first_cuts,(zero,)*2048)
    second=_functional(other_cuts,(zero,)*2048)
    result=f.difference(first,second)
    assert len(result.coefficients)==4095 and result.exact_zero
    assert result.cuts[0]==Z and result.cuts[-1]==O
    with pytest.raises(ValueError,match='inventory'):
        f.Functional(result.cuts,result.coefficients,result.cosine,result.atoms)


@pytest.mark.parametrize('limit',('individual','aggregate'))
def test_difference_rejects_derived_growth_before_later_intervals(limit,monkeypatch):
    cuts=(Z,Fraction(1,2),O)
    first=_one_channel(((Fraction(8),Z,Z,Z,Z,Z),(O,Z,Z,Z,Z,Z)),cuts)
    second=_functional(cuts)
    calls=[]
    original=f._restrict
    def counted(*args):
        calls.append(1)
        if len(calls)>6:
            pytest.fail('later interval restricted before first was admitted')
        return original(*args)
    monkeypatch.setattr(f,'_restrict',counted)
    if limit=='individual':
        monkeypatch.setattr(f,'DERIVED_INTEGER_BITS',3)
        message='rational integer bit cap'
    else:
        metadata=(*cuts,*first.cosine,*(v for atom in first.atoms for v in atom))
        bits=sum(v.numerator.bit_length()+v.denominator.bit_length()
                 for v in metadata)
        monkeypatch.setattr(f,'TOTAL_INTEGER_BITS',bits+5)
        message='aggregate bit cap'
    with pytest.raises(ValueError,match=message):
        f.difference(first,second)
    assert len(calls)==6
