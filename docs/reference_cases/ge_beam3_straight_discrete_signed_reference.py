"""Separate one-macro planar pencil, exact rational coefficients.

Same-author equation reconstruction, not independent review. No producer,
AD, NumPy, SciPy or production matrix imports. Two length-one cells, EI=1,
rho*A=1, prescribed axial force N, square-section slenderness s=L/h.

Per-cell second variation: S*(dv-lambda*c)^2+N*(2*dv*c-lambda*c^2)
plus endpoint bending jump j.T*[[4,-2],[-2,4]]*j, with
j=(c-theta_left, theta_right-c). The two free nodal rotation traces
are massless and eliminated exactly. Cell rotations retain j_rho=1/(3*s^2).
"""

from decimal import Decimal, localcontext
from fractions import Fraction as F
from itertools import permutations


def characteristic(slenderness, axial):
    if type(slenderness) is not int or slenderness < 1:
        raise ValueError('positive integral diagnostic slenderness required')
    n = F(str(axial)); ea = F(3*slenderness**2); shear = 25*ea/78
    stretch = 1+n/ea
    if stretch <= 0: raise ValueError('positive accepted axial stretch required')
    # x=(v_mid,v_tip,c1,c2,theta_mid,theta_tip), v0=theta0=0.
    k = [[F(0) for _ in range(6)] for _ in range(6)]
    for dv, c, jl, jr in (
        ([1,0,0,0,0,0], [0,0,1,0,0,0], [0,0,1,0,0,0], [0,0,-1,0,1,0]),
        ([-1,1,0,0,0,0], [0,0,0,1,0,0], [0,0,0,1,-1,0], [0,0,0,-1,0,1]),
    ):
        for i in range(6):
            for j in range(6):
                k[i][j] += (shear*dv[i]*dv[j]+(n-shear*stretch)*(dv[i]*c[j]+c[i]*dv[j])
                    +(shear*stretch**2-n*stretch)*c[i]*c[j]
                    +4*(jl[i]*jl[j]+jr[i]*jr[j])-2*(jl[i]*jr[j]+jr[i]*jl[j]))
    determinant = k[4][4]*k[5][5]-k[4][5]*k[5][4]
    inverse = [[k[5][5]/determinant, -k[4][5]/determinant],
               [-k[5][4]/determinant, k[4][4]/determinant]]
    reduced = [[k[i][j]-sum(k[i][4+a]*inverse[a][b]*k[4+b][j]
        for a in range(2) for b in range(2)) for j in range(4)] for i in range(4)]
    mass = [[F(2,3), F(1,6), F(0), F(0)], [F(1,6), F(1,3), F(0), F(0)],
        [F(0), F(0), 1/ea, F(0)], [F(0), F(0), F(0), 1/ea]]
    coefficients = [F(0)]*5
    for order in permutations(range(4)):
        sign = (-1)**sum(order[i] > order[j] for i in range(4) for j in range(i+1, 4))
        polynomial = [F(sign)]
        for i, j in enumerate(order):
            updated = [F(0)]*(len(polynomial)+1)
            for power, value in enumerate(polynomial):
                updated[power] += value*reduced[i][j]
                updated[power+1] -= value*mass[i][j]
            polynomial = updated
        coefficients = [a+b for a,b in zip(coefficients, polynomial)]
    return tuple(coefficients)


def bending_roots(slenderness, axial):
    """80-digit polynomial bisection in two separately frozen sign brackets.

    No interval certification or automatic root search. Exact polynomial
    coefficients avoid normal-equation cancellation in the comparison model.
    """
    coefficients = characteristic(slenderness, axial)
    with localcontext() as ctx:
        ctx.prec = 80
        decimal = [Decimal(x.numerator)/Decimal(x.denominator) for x in coefficients]
        def evaluate(value):
            result = decimal[-1]
            for coefficient in reversed(decimal[:-1]): result = result*value+coefficient
            return result
        roots = []
        for lower, upper in ((-10, 5), (5, 100)):
            lo, hi = Decimal(lower), Decimal(upper); left = evaluate(lo)
            if left*evaluate(hi) >= 0: raise ValueError('frozen discrete reference bracket failed')
            for _ in range(100):
                middle = (lo+hi)/2; value = evaluate(middle)
                if value == 0:
                    lo = hi = middle
                    break
                if left*value > 0: lo, left = middle, value
                else: hi = middle
            roots.append(float((lo+hi)/2))
        return tuple(roots)
