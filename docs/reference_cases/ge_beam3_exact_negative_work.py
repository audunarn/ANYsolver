"""Exact direct work checker; no producer, inertia, NumPy or mechanics imports."""
from fractions import Fraction as F
from decimal import Decimal as D
from math import isfinite
from time import monotonic


def fraction_record(value):
    return dict(numerator=str(value.numerator),denominator=str(value.denominator))


def verify(left,right,geometric,free,direction):
    start=monotonic()
    def check():
        if monotonic()-start>120:raise ValueError('exact work checker deadline')
    n=len(geometric);link=len(right)
    if not 1<=n<=512 or not 1<=link<=512 or not 1<=len(left)<=8192:raise ValueError('bounded factors')
    for a,width in ((left,link),(right,n),(geometric,n)):
        if type(a) is not list or any(type(row) is not list or len(row)!=width
                or any(type(x) is not float or not isfinite(x) for x in row) for row in a):
            raise ValueError('original finite binary64 factor entries')
    if (type(free) is not tuple or not free or len(set(free))!=len(free)
            or any(type(i) is not int or not 0<=i<n for i in free)):
        raise ValueError('exact free coordinate map')
    if type(direction) is not list or len(direction)!=len(free):raise ValueError('complete witness coordinates')
    x=[F(0)]*n
    for i,s in zip(free,direction):
        if type(s) is not str or not 1<=len(s)<=160:raise ValueError('bounded Decimal coordinate')
        v=D(s)
        if not v.is_finite() or abs(v.as_tuple().exponent)>500 or str(v)!=s:raise ValueError('canonical finite Decimal coordinate')
        x[i]=F(v)
    if max(abs(v) for v in x)!=1:raise ValueError('normalized nonzero original-coordinate witness')
    def product(a,v):
        out=[]
        for row in a:
            check();out.append(sum((F.from_float(c)*w for c,w in zip(row,v) if c and w),F(0)))
        return out
    compatible=product(right,x);stress=product(left,compatible)
    material=sum((v*v for v in stress),F(0))
    hx=product(geometric,x);geometric_work=sum((v*w for v,w in zip(x,hx)),F(0))
    total=material+geometric_work
    if total>=0:raise ValueError('claimed negative witness has nonnegative exact work')
    check()
    return dict(schema='GE_BEAM3_EXACT_ORIGINAL_FACTOR_NEGATIVE_WORK_V1',
                dimension=n,free_dimension=len(free),nonzero_coordinates=sum(v!=0 for v in x),
                material=fraction_record(material),geometric=fraction_record(geometric_work),
                total=fraction_record(total),exact_negative=True,roundoff_tolerance_used=False,
                raw_geometric_entries_unchanged=True,inertia_algorithm_used=False,
                production_qualified=False)
