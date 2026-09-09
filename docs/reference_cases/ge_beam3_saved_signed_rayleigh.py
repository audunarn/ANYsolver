"""Independent stdlib arithmetic on saved matrices, not a mechanics oracle."""
from fractions import Fraction as F
from decimal import Decimal, localcontext
from math import isfinite


def number(x):
    if type(x) not in (int,float) or not isfinite(x):
        raise ValueError('finite supplied scalar required')
    return F(x)


def dot(a,b):
    if len(a)!=len(b):raise ValueError('matching scalar action')
    return sum((x*y for x,y in zip(a,b)),F(0))


def action(matrix,v,check=lambda:None):
    result=[]
    for row in matrix:
        check()
        if len(row)!=len(v):raise ValueError('matching matrix action')
        result.append(sum((number(a)*b for a,b in zip(row,v) if a and b),F(0)))
    return result


def vector(high,low=None):
    if not 1<=len(high)<=150 or any(len(row)!=1 for row in high):
        raise ValueError('one bounded saved physical mode required')
    if low is None:low=[[0.] for _ in high]
    if len(low)!=len(high) or any(len(row)!=1 for row in low):raise ValueError('matching explicit mode halves')
    return [number(a[0])+number(b[0]) for a,b in zip(high,low)]


def factor_quotient(packet,v,macros,check=lambda:None):
    if macros not in (4,8) or len(v)!=6*(2*macros+1)+6*macros:
        raise ValueError('registered straight uniform-mesh packet only')
    layout=dict(packet['internal_layout']);operators=packet['operators']
    if [eid for eid,_ in operators]!=list(range(1,macros+1)):raise ValueError('complete ordered operator graph')
    if any(v[i] for i in range(6)):raise ValueError('fixed endpoint mode must vanish')
    material=geometric=kinetic=F(0)
    for eid,op in operators:
        expected=list(range(6*(2*macros+1)+6*(eid-1),6*(2*macros+1)+6*eid))
        if layout[eid]!=expected:raise ValueError('registered internal coordinate map')
        slots=list(range(12*(eid-1),12*(eid-1)+18))+expected
        local=[v[i] for i in slots]
        strain=action(op['left'],action(op['right'],local,check),check)
        speed=action(op['kinetic'],local,check)
        material+=dot(strain,strain);geometric+=dot(local,action(op['geometric'],local,check))
        kinetic+=dot(speed,speed)
    if kinetic<=0:raise ValueError('positive physical kinetic quotient required')
    return (material+geometric)/kinetic


def dense_quotient(packet,v,check=lambda:None):
    energy=dot(v,action(packet['stiffness'],v,check))
    mass=dot(v,action(packet['mass'],v,check))
    if mass<=0:raise ValueError('positive dense kinetic quotient required')
    return energy/mass


def encode(value):
    with localcontext() as ctx:
        ctx.prec=80
        decimal=str(Decimal(value.numerator)/Decimal(value.denominator))
    return dict(numerator=str(value.numerator),denominator=str(value.denominator),decimal80=decimal)


def compare(current,old,macros,check=lambda:None):
    new_value=number(current['modes']['eigenvalues'][0]);old_value=number(old['modes']['eigenvalues'][0])
    new_vector=vector(current['modes']['high_modes'],current['modes']['low_modes'])
    old_vector=vector(old['modes']['full_modes'])
    original_new=factor_quotient(current['packet'],new_vector,macros,check)
    original_old=factor_quotient(current['packet'],old_vector,macros,check)
    old_dense=dense_quotient(old['packet'],old_vector,check)
    parts=dict(new_extraction=new_value-original_new,
        vector_quotient=original_new-original_old,
        operator_representation=original_old-old_dense,
        old_extraction=old_dense-old_value)
    difference=new_value-old_value
    assert sum(parts.values(),F(0))==difference
    scale=max(F(1),abs(new_value),abs(old_value))
    return dict(exact_parts={k:encode(v) for k,v in parts.items()},
        normalized_parts={k:float(v/scale) for k,v in parts.items()},
        exact_difference=encode(difference),normalized_difference=float(difference/scale),
        original_new_quotient=encode(original_new),original_old_quotient=encode(original_old),
        old_dense_quotient=encode(old_dense),decomposition_exact=True,
        production_qualified=False,independent_mechanics_oracle=False)
