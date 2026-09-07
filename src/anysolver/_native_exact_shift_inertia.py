"""Exact inertia of a represented binary64 symmetric shifted pencil.

This is arithmetic authority for H - shift*M as supplied, not an interval
certificate for continuum mechanics or the pre-rounding source operator.
"""
from fractions import Fraction
from time import monotonic
import numpy as np


def exact_inertia(h, mass, shift, check=lambda: None):
    started = monotonic()
    def guard():
        check()
        if monotonic()-started > 30.:
            raise TimeoutError('exact shifted inertia deadline')
    guard()
    if (h.ndim != 2 or h.shape[0] != h.shape[1] or not 1 <= len(h) <= 64
            or mass.shape != h.shape or not np.isfinite(h).all()
            or not np.isfinite(mass).all() or not np.isfinite(shift)
            or not np.array_equal(h, h.T) or not np.array_equal(mass, mass.T)):
        raise ValueError('bounded finite symmetric shifted pencil required')
    s = Fraction(float(shift))
    a = [[Fraction(float(x))-s*Fraction(float(y)) for x, y in zip(row, other)]
         for row, other in zip(h, mass)]
    positive = negative = zeros = 0
    while a:
        guard(); n = len(a)
        pivot = max(range(n), key=lambda i: abs(a[i][i]))
        if a[pivot][pivot]:
            order = [pivot]+[i for i in range(n) if i != pivot]
            a = [[a[i][j] for j in order] for i in order]
            d = a[0][0]
            positive += int(d > 0); negative += int(d < 0)
            a = [[a[i][j]-a[i][0]*a[0][j]/d for j in range(1, n)] for i in range(1, n)]
        else:
            # A nonzero off-diagonal with zero diagonals yields the exact
            # hyperbolic 2x2 block [[0,b],[b,0]], inertia (1,1,0).
            pair = next(((i, j) for i in range(n) for j in range(i+1, n) if a[i][j]), None)
            if pair is None:
                zeros += n; break
            order = list(pair)+[i for i in range(n) if i not in pair]
            a = [[a[i][j] for j in order] for i in order]; b = a[0][1]
            positive += 1; negative += 1
            a = [[a[i][j]-(a[i][0]*a[1][j]+a[i][1]*a[0][j])/b
                  for j in range(2, n)] for i in range(2, n)]
    guard()
    return positive, negative, zeros
