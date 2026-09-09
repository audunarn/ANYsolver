"""Standalone analytical linear curved-cantilever reference (author research).

No producer, frame, mechanics, NumPy or quadrature imports. The centreline is
r(t)=(t,h*(1-t*t),0), -1<=t<=1, with material second axis global z. The
clamped-left tip compliance follows continuum equilibrium and virtual work.
This is a separately constructed reference, not independent authorship.
"""

from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import math


def _add(a, b):
    return [(a[i] if i < len(a) else Decimal(0))+(b[i] if i < len(b) else Decimal(0))
            for i in range(max(len(a), len(b)))]


def _multiply(a, b):
    result = [Decimal(0)]*(len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            result[i+j] += x*y
    return result


def _inverse_spd(section):
    if len(section) != 6 or any(len(row) != 6 for row in section):
        raise ValueError("six-by-six section required")
    if not all(math.isfinite(float(x)) for row in section for x in row):
        raise ValueError("finite section required")
    a = [[Decimal.from_float(float(value)) for value in row] for row in section]
    if any(a[i][j] != a[j][i] for i in range(6) for j in range(6)):
        raise ValueError("symmetric section required")
    l = [[Decimal(i == j) for j in range(6)] for i in range(6)]
    d = [Decimal(0)]*6
    for i in range(6):
        d[i] = a[i][i]-sum((l[i][k]*l[i][k]*d[k] for k in range(i)), Decimal(0))
        if d[i] <= 0:
            raise ValueError("positive definite section required")
        for j in range(i+1, 6):
            l[j][i] = (a[j][i]-sum((l[j][k]*l[i][k]*d[k] for k in range(i)), Decimal(0)))/d[i]
    inverse = [[Decimal(0)]*6 for _ in range(6)]
    for column in range(6):
        y = [Decimal(0)]*6
        for i in range(6):
            y[i] = Decimal(i == column)-sum((l[i][k]*y[k] for k in range(i)), Decimal(0))
        z = [y[i]/d[i] for i in range(6)]
        for i in range(5, -1, -1):
            inverse[i][column] = z[i]-sum((l[k][i]*inverse[k][column] for k in range(i+1, 6)), Decimal(0))
    return inverse


def parabolic_tip_compliance(height, section):
    """Return the exact-integral compliance evaluated at 80 Decimal digits.

    For tip force f and couple c, continuum resultants are f and
    c+(r_tip-r(t)) cross f. Let B map these six tip loads to material
    resultants. Tip compliance is integral B^T C^-1 B ds.

    Each row of B is polynomial or polynomial/J, J=sqrt(1+4h^2 t^2).
    Integration reduces to polynomial moments and I_n=integral t^n/J dt.
    I_0=2*asinh(2h)/(2h); even moments obey
    n*(2h)^2*I_n=2*sqrt(1+(2h)^2)-(n-1)*I_(n-2).
    No sampled finite-element field or numerical quadrature enters this
    calculation. The bounded research family is 0<=h<=0.75.
    """
    if not math.isfinite(float(height)) or not 0 <= float(height) <= .75:
        raise ValueError("reference height must be finite in [0,0.75]")
    with localcontext(Context(prec=80, rounding=ROUND_HALF_EVEN)):
        h = Decimal.from_float(float(height))
        compliance = _inverse_spd(section)
        zero, one = Decimal(0), Decimal(1)
        # Numerators of R^T rows. Rows 0/2 carry denominator J; row 1 does not.
        rows = [[[one], [zero, -2*h], [zero]],
                [[zero], [zero], [one]],
                [[zero, -2*h], [-one], [zero]]]
        # r_tip-r(t)=(1-t,-h+h*t^2,0).
        lever = [[[zero], [zero], [-h, zero, h]],
                 [[zero], [zero], [-one, one]],
                 [[h, zero, -h], [one, -one], [zero]]]
        b = [[[zero] for _ in range(6)] for _ in range(6)]
        for i in range(3):
            for j in range(3):
                b[i][j] = rows[i][j]
                b[i+3][j+3] = rows[i][j]
                for k in range(3):
                    b[i+3][j] = _add(b[i+3][j], _multiply(rows[i][k], lever[k][j]))
        a = 2*h
        moments = [zero]*11
        if a == 0:
            for n in range(0, 11, 2):
                moments[n] = Decimal(2)/Decimal(n+1)
        elif a <= Decimal('.5'):
            # The upward recurrence divides cancellation by a^2. Use the
            # convergent binomial integral for the near-straight limit.
            for n in range(0, 11, 2):
                coefficient = one
                for k in range(256):
                    term = 2*coefficient/Decimal(n+2*k+1)
                    moments[n] += term
                    if abs(term) < Decimal('1e-85'):
                        break
                    coefficient *= -a*a*Decimal(2*k+1)/Decimal(2*k+2)
                else:
                    raise ArithmeticError("bounded analytical moment series exhausted")
        else:
            endpoint = (1+a*a).sqrt()
            moments[0] = 2*(a+endpoint).ln()/a
            for n in range(2, 11, 2):
                moments[n] = (2*endpoint-(n-1)*moments[n-2])/(n*a*a)
        denominator = [1, 0, 1, 1, 0, 1]
        result = [[zero for _ in range(6)] for _ in range(6)]
        for i in range(6):
            for j in range(6):
                if not compliance[i][j]:
                    continue
                power = denominator[i]+denominator[j]
                for p in range(6):
                    for q in range(6):
                        polynomial = _multiply(b[i][p], b[j][q])
                        integral = zero
                        for n, coefficient in enumerate(polynomial):
                            if n % 2:
                                continue
                            weight = (moments[n] if power == 2 else Decimal(2)/Decimal(n+1)
                                      if power == 1 else moments[n]+a*a*moments[n+2])
                            integral += coefficient*weight
                        result[p][q] += compliance[i][j]*integral
        return tuple(tuple(row) for row in result)
