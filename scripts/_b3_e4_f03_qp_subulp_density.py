"""Preparatory high-precision polynomial recovery on sub-binary64 pad intervals.

The ordinary Qp oracle cannot sample the interior of a one-ulp station
interval. This module evaluates its physical cell polynomials in Decimal
arithmetic and fits the *polynomial* part of the section density. It does
not itself certify the complete functional or a scientific comparison.
"""
from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction

import numpy as np

from scripts._b3_e4_f03_primal_ritz import F0, SECTION


def _d(value):
    return Decimal.from_float(float(value))


def audit_represented_crossings(oracle):
    """Return exact binary64 event audit; reject a displaced interior event.

    The event builder subtracts rounded geometry in binary64. Fraction
    arithmetic checks whether that subtraction preserves its *exact*
    crossing coordinate. An interior discrepancy would invalidate a fixed
    polynomial interval even if it is less than one ulp.
    """
    interior = set()
    boundary_max = Fraction(0)
    for edge in oracle.x:
        for ox, _ in oracle.offsets:
            for boundary in (ox-oracle.a, ox+oracle.a):
                represented = edge-boundary
                exact = Fraction.from_float(edge)-Fraction.from_float(boundary)
                exact_inside = Fraction(0) < exact < Fraction(1)
                represented_inside = 0. < represented < 1.
                if exact_inside != represented_inside:
                    raise ArithmeticError("rounded crossing changes beam-domain inventory")
                if exact_inside:
                    interior.add(represented)
                    if exact != Fraction.from_float(represented):
                        raise ArithmeticError("rounded interior crossing changes station partition")
                elif represented in (0., 1.):
                    boundary_max = max(boundary_max,
                        abs(exact-Fraction.from_float(represented)))
    return len(interior), float(boundary_max)


def _moment(low, high, count):
    return [(high**(i+1)-low**(i+1))/(i+1) for i in range(count)]


def _dot2(coeff, xx, yy):
    return sum(coeff[i][k]*xx[i]*yy[k]
               for i in range(len(xx)) for k in range(len(yy)))


def _solve(matrix, values):
    """Small Decimal solve with partial pivoting; three right-hand sides."""
    a = [row.copy()+rhs.copy() for row, rhs in zip(matrix, values)]
    n = len(a)
    for j in range(n):
        pivot = max(range(j, n), key=lambda k: abs(a[k][j]))
        if not a[pivot][j]:
            raise ArithmeticError("singular sub-ulp polynomial fit")
        a[j], a[pivot] = a[pivot], a[j]
        div = a[j][j]
        a[j] = [v/div for v in a[j]]
        for k in range(n):
            if k == j:
                continue
            factor = a[k][j]
            if factor:
                a[k] = [v-factor*w for v, w in zip(a[k], a[j])]
    return [row[n:] for row in a]


def _legendre(z, degree):
    values = [Decimal(1)]
    if degree:
        values.append(z)
    for n in range(1, degree):
        values.append(((2*n+1)*z*values[n]-n*values[n-1])/(n+1))
    return values


def _nodal_coefficients(oracle, q):
    """Independently reconstruct exact-Decimal cell polynomials from nodes."""
    values = np.asarray(q, dtype=np.float64)
    if (values.shape != (2*oracle.n,) or not np.isfinite(values).all()):
        raise ValueError("invalid nodal state for sub-ulp reconstruction")
    fields = values.reshape(2, oracle.nx, oracle.ny)
    p = oracle.p
    nodes = [2*Decimal(a)/p-1 for a in range(p+1)]
    vander = [[Decimal(1) if i == 0 else t**i
               for i in range(p+1)] for t in nodes]
    components = []
    for field in fields:
        cells = []
        for ix in range(len(oracle.x)-1):
            row = []
            for iy in range(len(oracle.y)-1):
                block = [[_d(field[ix*p+a, iy*p+b])
                          for b in range(p+1)] for a in range(p+1)]
                ycoeff = [[item[0] for item in _solve(vander,
                          [[block[a][b]] for b in range(p+1)])]
                          for a in range(p+1)]
                xcoeff = [[item[0] for item in _solve(vander,
                          [[ycoeff[a][k]] for a in range(p+1)])]
                          for k in range(p+1)]
                row.append([[xcoeff[k][i] for k in range(p+1)]
                            for i in range(p+1)])
            cells.append(row)
        components.append(cells)
    return components


def _density(oracle, coefficients, station, *, return_kinematics=False):
    """Polynomial section density; cosine is intentionally omitted."""
    p = oracle.p
    xs, ys = tuple(map(_d, oracle.x)), tuple(map(_d, oracle.y))
    area = _d(oracle.area)
    j = _d(oracle.j)
    pose = [Decimal(0)]*3
    first = [Decimal(0)]*3
    second = [Decimal(0)]*3

    def edge(x, bottom, top):
        host = next((i for i in range(len(xs)-1) if xs[i] <= x < xs[i+1]),
                    len(xs)-2)
        if not xs[host] <= x <= xs[host+1]:
            raise ArithmeticError("sub-ulp pad edge leaves the shell")
        hx = xs[host+1]-xs[host]
        t = 2*(x-xs[host])/hx-1
        powers = [t**i for i in range(p+1)]
        deriv = [Decimal(0)]+[2*i*t**(i-1)/hx for i in range(1, p+1)]
        result = [Decimal(0)]*6
        for k in range(len(ys)-1):
            down, up = max(bottom, ys[k]), min(top, ys[k+1])
            if up <= down:
                continue
            hy = ys[k+1]-ys[k]
            my = _moment(2*(down-ys[k])/hy-1, 2*(up-ys[k])/hy-1, p+2)
            ym = [(ys[k]+hy/2)*my[v]+hy*my[v+1]/2 for v in range(p+1)]
            cx, cy = coefficients[0][host][k], coefficients[1][host][k]
            factor = hy/2
            for row, cc, xp, yp in (
                (0,cx,powers,my[:p+1]), (1,cy,powers,my[:p+1]),
                (2,cx,deriv,my[:p+1]), (3,cy,deriv,my[:p+1]),
                (4,cx,powers,ym), (5,cx,deriv,ym),
            ):
                result[row] += factor*_dot2(cc, xp, yp)
        return result

    for ox, oy in oracle.offsets:
        # Match the frozen oracle's represented offset arithmetic. All
        # subsequent station operations retain their exact binary64 inputs.
        left_offset, right_offset = _d(ox-oracle.a), _d(ox+oracle.a)
        low, high = station+left_offset, station+right_offset
        bottom, top = _d(oy-oracle.a), _d(oy+oracle.a)
        pad = [Decimal(0)]*3
        for i in range(len(xs)-1):
            l, r = max(low, xs[i]), min(high, xs[i+1])
            if r <= l:
                continue
            hx = xs[i+1]-xs[i]
            tx = _moment(2*(l-xs[i])/hx-1, 2*(r-xs[i])/hx-1, p+2)
            for k in range(len(ys)-1):
                b, t = max(bottom, ys[k]), min(top, ys[k+1])
                if t <= b:
                    continue
                hy = ys[k+1]-ys[k]
                ty = _moment(2*(b-ys[k])/hy-1, 2*(t-ys[k])/hy-1, p+2)
                cx, cy = coefficients[0][i][k], coefficients[1][i][k]
                scale = hx*hy/4
                ux = scale*_dot2(cx, tx[:p+1], ty[:p+1])
                uy = scale*_dot2(cy, tx[:p+1], ty[:p+1])
                yu = scale*((ys[k]+hy/2)*_dot2(cx, tx[:p+1], ty[:p+1])
                    +hy*_dot2(cx, tx[:p+1], ty[1:])/2)
                xv = scale*((xs[i]+hx/2-station)*_dot2(cy, tx[:p+1], ty[:p+1])
                    +hx*_dot2(cy, tx[1:], ty[:p+1])/2)
                pad[0] += ux
                pad[1] += uy
                pad[2] += (xv-yu)/j
        le, re = edge(low, bottom, top), edge(high, bottom, top)
        pose = [v+w for v,w in zip(pose, pad)]
        first[0] += re[0]-le[0]
        first[1] += re[1]-le[1]
        first[2] += (right_offset*re[1]-left_offset*le[1]
                     -pad[1]-re[4]+le[4])/j
        second[0] += re[2]-le[2]
        second[1] += re[3]-le[3]
        second[2] += (right_offset*re[3]-left_offset*le[3]
                      -re[1]+le[1]-re[5]+le[5])/j
    pose, first, second = ([v/area for v in row]
                           for row in (pose, first, second))
    if return_kinematics:
        return pose, first, second
    ea, ei, ga = map(_d, np.diag(SECTION))
    return (ea*second[0],
            ga*(second[1]-first[2])+_d(F0),
            ei*second[2]+ga*(first[1]-pose[2]))


def exact_endpoint_resultant(oracle, cell_coefficients, station,
                             *, precision=120):
    """Section resultant from the rounded physical geometry at s=0 or 1."""
    if station not in (0., 1.):
        raise ValueError("only physical beam endpoints are supported")
    with localcontext() as ctx:
        ctx.prec = precision
        cc = [[[[[_d(v) for v in row] for row in plane]
                 for plane in component_i] for component_i in component]
              for component in cell_coefficients]
        pose, first, _ = _density(oracle, cc, _d(station),
                                  return_kinematics=True)
        ea, ei, ga = map(_d, np.diag(SECTION))
        return np.asarray([float(ea*first[0]),
                           float(ga*(first[1]-pose[2])),
                           float(ei*first[2])])


def reconstruct_subulp_polynomial(oracle, cell_coefficients, left, right,
                                  degree, *, precision=90, nodal_state=None):
    """Return Legendre coefficients and held-point Decimal fit defect.

    Refuse an exact geometric crossing inside the represented interval: one
    polynomial would then be invalid even though no binary64 point resolves
    the change of host cell.
    """
    if not (0 <= left < right <= 1 and 1 <= degree <= 7 and precision >= 60):
        raise ValueError("invalid bounded sub-ulp reconstruction request")
    if np.asarray(cell_coefficients).shape != (2, len(oracle.x)-1,
            len(oracle.y)-1, oracle.p+1, oracle.p+1):
        raise ValueError("invalid cell polynomial shape")
    with localcontext() as ctx:
        ctx.prec = precision
        l, r = _d(left), _d(right)
        for x in oracle.x:
            for ox, _ in oracle.offsets:
                for boundary in (ox-oracle.a, ox+oracle.a):
                    crossing = _d(x)-_d(boundary)
                    if l < crossing < r:
                        raise ArithmeticError("unrepresented crossing inside sub-ulp interval")
        if nodal_state is None:
            cc = [[[[[_d(v) for v in row] for row in plane]
                     for plane in component_i] for component_i in component]
                  for component in cell_coefficients]
        else:
            cc = _nodal_coefficients(oracle, nodal_state)
        n = degree+1
        nodes = [Decimal(-1)+Decimal(2*i+1)/n for i in range(n)]
        points = [l+(z+1)*(r-l)/2 for z in nodes]
        vandermonde = [_legendre(z, degree) for z in nodes]
        values = [list(_density(oracle, cc, s)) for s in points]
        coefficients = _solve(vandermonde, values)
        defect = Decimal(0)
        for numerator in (-8, -4, 0, 4, 8):
            z = Decimal(numerator)/10
            s = l+(z+1)*(r-l)/2
            basis = _legendre(z, degree)
            predicted = [sum(row[k]*basis[i]
                             for i, row in enumerate(coefficients)) for k in range(3)]
            expected = _density(oracle, cc, s)
            defect = max(defect, *(abs(a-b) for a,b in zip(predicted, expected)))
        return np.asarray([[float(v) for v in row] for row in coefficients]), float(defect)
