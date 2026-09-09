"""Same-author independent arithmetic, not a beam or interval oracle.

Direct Decimal Schur/Jacobi roots of ORIGINAL binary64 signed factor chains.
No production or numerical-library imports.
"""
from decimal import Decimal as D, localcontext
from math import isfinite
from time import monotonic
from docs.reference_cases.ge_beam3_decimal_factor_audit import (
    product, gram, select, transpose, cholesky, triangular_solve, subtract, symmetric_roots)


def roots(left, right, geometric, kinetic, free, algebraic, *, digits=80):
    start=monotonic()
    def checkpoint():
        if monotonic()-start>120: raise ValueError('signed arithmetic audit deadline')
    if type(digits) is not int or digits not in (80,100): raise ValueError('registered audit precision')
    if any(type(a) is not list or not a for a in (left,right,geometric,kinetic)):
        raise ValueError('explicit nonempty matrix rows')
    n=len(geometric); link=len(right)
    if not 2<=n<=48 or not 1<=link<=48 or len(left)>512 or len(kinetic)>2048:
        raise ValueError('bounded signed arithmetic dimensions')
    for a,cols in ((left,link),(right,n),(geometric,n),(kinetic,n)):
        if any(type(row) is not list or len(row)!=cols or any(type(x) is not float or not isfinite(x) for x in row) for row in a):
            raise ValueError('finite rectangular binary64 matrix required')
    if any(geometric[i][j]!=geometric[j][i] for i in range(n) for j in range(n)):
        raise ValueError('exact symmetric geometric factor required')
    for slots in (free,algebraic):
        if type(slots) is not tuple or len(set(slots))!=len(slots) or any(type(i) is not int or not 0<=i<n for i in slots):
            raise ValueError('complete exact DOF sets required')
    physical=tuple(i for i in free if i not in algebraic)
    if not set(algebraic)<=set(free) or not 2<=len(physical)<=30:
        raise ValueError('bounded physical/algebraic split')
    if any(row[i]!=0. for row in kinetic for i in algebraic): raise ValueError('exactly massless trace required')
    with localcontext() as ctx:
        ctx.prec=digits
        def convert(a): return [[D.from_float(v) for v in row] for row in a]
        material=gram(product(convert(left),convert(right))); geometry=convert(geometric)
        stiffness=[[x+y for x,y in zip(a,b)] for a,b in zip(material,geometry)]
        mass=gram(convert(kinetic)); checkpoint()
        reduced=select(stiffness,physical,physical)
        if algebraic:
            trace=select(stiffness,algebraic,algebraic); cross=select(stiffness,algebraic,physical)
            factor=cholesky(trace)
            eliminate=triangular_solve(transpose(factor),triangular_solve(factor,cross,True),False)
            reduced=subtract(reduced,product(transpose(cross),eliminate))
        factor=cholesky(select(mass,physical,physical))
        first=triangular_solve(factor,reduced,True)
        normalized=transpose(triangular_solve(factor,transpose(first),True))
        values=symmetric_roots(normalized,digits,checkpoint); checkpoint()
        return dict(eigenvalues=[str(x) for x in values],digits=digits,physical_dimension=len(physical),
                    trace_positive=True,mass_positive=True,certified_intervals=False,mechanics_reconstructed=False)
