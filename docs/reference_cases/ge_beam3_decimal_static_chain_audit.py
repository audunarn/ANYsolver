"""Same-author, bounded supplied-factor static audit; not a mechanics oracle.

Retain both factors until Decimal multiplication and solve the full supported
nodal-plus-cell system. No nodal Schur subtraction or production import.
"""
from decimal import Decimal as D, localcontext
from time import monotonic
from docs.reference_cases.ge_beam3_decimal_chain_audit import (
    product, gram, select, cholesky, triangular_solve, transpose,
)


def solve_static_chain(left, right, rhs, free, *, digits=80):
    started = monotonic()
    n = len(rhs); link = len(right)
    if (type(digits) is not int or not 60 <= digits <= 100
            or not 1 <= n <= 48 or not 1 <= link <= 48
            or not 1 <= len(left) <= 256
            or any(len(row) != link for row in left)
            or any(len(row) != n for row in right)
            or not free or len(set(free)) != len(free)
            or any(type(i) is not int or not 0 <= i < n for i in free)
            or any(type(x) is not float for row in left+right for x in row)
            or any(type(x) is not float for x in rhs)):
        raise ValueError('bounded binary64 static chain required')
    with localcontext() as context:
        context.prec = digits
        a = [[D.from_float(x) for x in row] for row in left]
        b = [[D.from_float(x) for x in row] for row in right]
        force = [D.from_float(x) for x in rhs]
        if any(not x.is_finite() for row in a+b+[force] for x in row):
            raise ValueError('finite static chain required')
        k = select(gram(product(a, b)), free, free)
        root = cholesky(k)
        load = [[force[i]] for i in free]
        step = triangular_solve(transpose(root), triangular_solve(root, load, True), False)
        if monotonic()-started > 30:
            raise ValueError('static chain audit deadline')
        result = [D(0)]*n
        for i, row in zip(free, step): result[i] = row[0]
        return tuple(str(x) for x in result)
