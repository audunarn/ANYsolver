"""Small independent standard-library rational solve of supplied binary64 data."""
from fractions import Fraction
from math import isfinite
from time import monotonic


def solve(matrix,rhs):
    n=len(rhs)
    if not 1<=n<=48 or len(matrix)!=n or any(len(row)!=n for row in matrix):
        raise ValueError('small exact square witness only')
    def exact(v):
        if type(v) not in (int,float) or not isfinite(v): raise ValueError('finite numeric exact witness')
        return Fraction(v)
    original=[[exact(v) for v in row] for row in matrix]; b=list(map(exact,rhs))
    a=[row.copy()+[v] for row,v in zip(original,b)]; started=monotonic()
    for column in range(n):
        if monotonic()-started>20.: raise RuntimeError('rational witness deadline')
        pivot=next((i for i in range(column,n) if a[i][column]),None)
        if pivot is None: raise ValueError('exactly singular witness')
        a[column],a[pivot]=a[pivot],a[column]
        for i in range(column+1,n):
            if not a[i][column]: continue
            multiplier=a[i][column]/a[column][column]
            for j in range(column+1,n+1): a[i][j]-=multiplier*a[column][j]
            a[i][column]=Fraction(0)
    x=[Fraction(0)]*n
    for i in range(n-1,-1,-1): x[i]=(a[i][-1]-sum(a[i][j]*x[j] for j in range(i+1,n)))/a[i][i]
    if any(sum(v*w for v,w in zip(row,x))!=v for row,v in zip(original,b)):
        raise ValueError('exact full-system witness multiplication failed')
    if monotonic()-started>20.: raise RuntimeError('rational witness deadline')
    return tuple(x)
