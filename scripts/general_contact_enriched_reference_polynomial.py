"""Finite analytic polynomial moments for the V15 reference control variate.

Pure stdlib coefficient algebra; NO contact/FE/quadrature implementation import.
Polynomials use dimensionless current affine source coordinates r,s. All actual
nonpolynomial geometry remains in the separate full integrand/remainder.
"""
from __future__ import annotations
from math import factorial, fsum, isfinite

DEGREE = 8
EXPONENTS = tuple((i, j) for i in range(DEGREE+1) for j in range(DEGREE+1-i))


class PolynomialRefused(ArithmeticError):
    pass


def require(ok, message):
    if not ok:
        raise PolynomialRefused(message)


def checked(poly):
    require(all(type(i) is int and type(j) is int and i >= 0 and j >= 0
                and i+j <= DEGREE and isfinite(c) for (i, j), c in poly.items()),
            'finite polynomial coefficients, complete degree<=8 only')
    return {key: float(value) for key, value in poly.items() if value != 0}


def add(a, b):
    result = dict(a)
    for key, value in b.items():
        result[key] = result.get(key, 0.)+value
    return checked(result)


def scale(poly, value):
    require(isfinite(value), 'finite polynomial scale')
    return checked({key: coefficient*value for key, coefficient in poly.items()})


def multiply(a, b):
    result = {}
    for (i, j), x in a.items():
        for (k, l), y in b.items():
            key = i+k, j+l
            require(sum(key) <= DEGREE, 'polynomial degree overflow; no truncated terms')
            result[key] = result.get(key, 0.)+x*y
    return checked(result)


def evaluate(poly, r, s):
    # Scalar coefficients may act on arrays supplied by the numeric oracle.
    return sum(coefficient*r**i*s**j for (i, j), coefficient in poly.items())


def triangle_moments(vertices, physical_area):
    """All45 monomials on SAME physical triangle, in a dimensionless chart.

    x=lambda1,y=lambda2 on the unit simplex. The PHYSICAL factor is 2A,
    integral x^i*y^j = i!j!/(i+j+2)!, not A times that simplex moment.
    """
    require(len(vertices) == 3 and all(len(p) == 2 and all(isfinite(x) for x in p) for p in vertices),
            'finite triangle affine coordinates')
    require(isfinite(physical_area) and physical_area > 0, 'positive SAME physical cut area')
    # Generating function H(t,u)=prod_v(1-r_v*t-s_v*u)^(-1).
    # Its denominator has degree3 and at most9 nonconstant terms. Thus each
    # of45 coefficients takes at most9 terms: fixed <=405 recurrence products,
    # no per-monomial symbolic expansion or quadrature/order increase.
    denominator = {(0, 0): 1.}
    for r, s in vertices:
        denominator = multiply(denominator, {(0, 0): 1., (1, 0): -r, (0, 1): -s})
    nonconstant = [(i, j, c) for (i, j), c in denominator.items() if (i, j) != (0, 0)]
    homogeneous = {(0, 0): 1.}
    for degree in range(1, DEGREE+1):
        for i in range(degree+1):
            j = degree-i
            homogeneous[i, j] = -fsum(c*homogeneous.get((i-a, j-b), 0.)
                                      for a, b, c in nonconstant if a <= i and b <= j)
    result = {}
    for i, j in EXPONENTS:
        moment = 2*physical_area*factorial(i)*factorial(j)/factorial(i+j+2)*homogeneous[i, j]
        require(isfinite(moment), 'finite analytic triangle moment')
        result[i, j] = moment
    return result


def integrate(poly, moments):
    require(set(moments) == set(EXPONENTS), 'all45 analytic moments required')
    value = fsum(coefficient*moments[key] for key, coefficient in checked(poly).items())
    require(isfinite(value), 'finite polynomial integral')
    return value


def hats_and_bubble(beta):
    require(len(beta) == 4 and all(isfinite(x) for x in beta), 'all4 finite physical modes')
    hats = [
        {(0, 0): .25, (1, 0): -.25, (0, 1): -.25, (1, 1): .25},
        {(0, 0): .25, (1, 0): .25, (0, 1): -.25, (1, 1): -.25},
        {(0, 0): .25, (1, 0): .25, (0, 1): .25, (1, 1): .25},
        {(0, 0): .25, (1, 0): -.25, (0, 1): .25, (1, 1): -.25}]
    b = {(0, 0): 1., (2, 0): -1., (0, 2): -1., (2, 2): 1.}
    amplitudes = {(0, 0): beta[0], (1, 0): beta[1], (0, 1): beta[2], (1, 1): beta[3]}
    return hats, multiply(b, amplitudes)


def control_polynomials(corners, beta, body_normal, corner_normal, target,
                        projected_target, chart_center, chart_r, chart_s, reference_jacobian):
    """Deterministic pose-dependent P_M(deg2), P_b(deg<=8), independent of order.

    corners/target retain ACTUAL physical offsets/directors. The selected part
    uses the constant corner normal, while full F uses actual varying normal.
    This approximation is ONLY P; F-P restores everything at every point.
    """
    require(len(corners) == 4 and len(target) == 3, 'Q4/S3 control-variate inventory')
    require(all(isfinite(x) for row in (*corners, *target, *projected_target) for x in row)
            and all(isfinite(x) for row in (body_normal, corner_normal, chart_center, chart_r, chart_s) for x in row),
            'finite physical polynomial input')
    determinant = chart_r[0]*chart_s[1]-chart_r[1]*chart_s[0]
    require(isfinite(determinant) and determinant > 0 and isfinite(reference_jacobian) and reference_jacobian > 0,
            'positive current affine chart and reference area')
    t0, t1, t2 = projected_target
    a, b = [t1[i]-t0[i] for i in range(2)], [t2[i]-t0[i] for i in range(2)]
    det = a[0]*b[1]-a[1]*b[0]
    require(isfinite(det) and det != 0, 'nondegenerate actual target plane chart')
    delta = [chart_center[i]-t0[i] for i in range(2)]
    def bary(vector, other, denominator):
        return checked({(0, 0): (vector[0]*other[1]-vector[1]*other[0])/denominator,
            (1, 0): (chart_r[0]*other[1]-chart_r[1]*other[0])/denominator,
            (0, 1): (chart_s[0]*other[1]-chart_s[1]*other[0])/denominator})
    l1 = bary(delta, b, det)
    # second barycentric is cross(a,delta)/det = cross(delta,a)/(-det).
    l2 = bary(delta, a, -det)
    l0 = add({(0, 0): 1.}, scale(add(l1, l2), -1.))
    hats, bubble = hats_and_bubble(beta)
    gap = {}
    for axis in range(3):
        source = scale(bubble, body_normal[axis])
        for i in range(4):
            source = add(source, scale(hats[i], corners[i][axis]))
        plane = add(add(scale(l0, target[0][axis]), scale(l1, target[1][axis])), scale(l2, target[2][axis]))
        gap = add(gap, scale(add(source, scale(plane, -1.)), corner_normal[axis]))
    support = [scale(hat, reference_jacobian/determinant) for hat in hats]
    weighted = [multiply(p, gap) for p in support]
    require(all(max((sum(key) for key in p), default=0) <= 2 for p in support), 'P_M degree<=2')
    return support, weighted
