"""Bounded same-author Decimal audit of a supplied finite linear system."""
from decimal import Decimal as D, localcontext
from time import monotonic


def solve_linear(matrix,rhs,*,digits=80):
    n=len(rhs);start=monotonic()
    if (type(digits) is not int or not 60<=digits<=100 or not 1<=n<=48
            or len(matrix)!=n or any(len(row)!=n for row in matrix)
            or any(type(x) is not float for row in matrix for x in row)
            or any(type(x) is not float for x in rhs)):
        raise ValueError('bounded binary64 audit system required')
    with localcontext() as context:
        context.prec=digits
        a=[[D.from_float(x) for x in row]+[D.from_float(b)] for row,b in zip(matrix,rhs)]
        if any(not x.is_finite() for row in a for x in row):raise ValueError('finite audit system required')
        for col in range(n):
            if monotonic()-start>30:raise ValueError('linear audit deadline')
            pivot=max(range(col,n),key=lambda i:abs(a[i][col]))
            if a[pivot][col]==0:raise ValueError('singular audit system')
            a[col],a[pivot]=a[pivot],a[col]
            for row in range(col+1,n):
                factor=a[row][col]/a[col][col]
                for j in range(col+1,n+1):a[row][j]-=factor*a[col][j]
                a[row][col]=D(0)
        x=[D(0)]*n
        for i in range(n-1,-1,-1):
            x[i]=(a[i][n]-sum((a[i][j]*x[j] for j in range(i+1,n)),D(0)))/a[i][i]
        return tuple(str(v) for v in x)
