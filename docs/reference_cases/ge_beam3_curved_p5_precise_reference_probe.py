"""Explicit 80-digit dual-flexibility reference action for research checks.

No production integration or finite-state extension. Input F/H/J metrics stay
binary64; this backend improves subsequent linear algebra, not quadrature.
"""

from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import HALVES, metrics, validate_section
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _array


def _decimal(values):
    return [[Decimal.from_float(float(value)) for value in row] for row in values]


def _transpose(matrix):
    return list(map(list, zip(*matrix)))


def _multiply(left, right):
    return [[sum((a*b for a, b in zip(row, column)), Decimal(0))
             for column in _transpose(right)] for row in left]


def _solve(matrix, rhs):
    """Forward elimination/back substitution, deterministic partial pivoting."""
    n, width = len(matrix), len(rhs[0])
    rows = [list(a)+list(b) for a, b in zip(matrix, rhs)]
    for column in range(n):
        pivot = max(range(column, n), key=lambda index: abs(rows[index][column]))
        if not rows[pivot][column]:
            raise ValueError("singular precise reference system")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        for row in range(column+1, n):
            ratio = rows[row][column]/rows[column][column]
            rows[row][column] = Decimal(0)
            for k in range(column+1, n+width):
                rows[row][k] -= ratio*rows[column][k]
    answer = [[Decimal(0) for _ in range(width)] for _ in range(n)]
    for row in range(n-1, -1, -1):
        for column in range(width):
            answer[row][column] = (rows[row][n+column]-sum(
                (rows[row][k]*answer[k][column] for k in range(row+1, n)), Decimal(0)))/rows[row][row]
    return answer


class PreciseReferenceAction:
    """Six equilibrated force/moment coordinates per half; no dense nodal K."""

    def __init__(self, reference, section, order=24):
        section = validate_section(section)
        self.cells = []
        with localcontext(Context(prec=80, rounding=ROUND_HALF_EVEN)):
            coordinates = _decimal(reference.coordinates)
            frames = [_decimal(frame) for frame in reference.nodal_triads]
            for cell, (left, right) in enumerate(HALVES):
                data = metrics(reference, section, cell, order)
                f, h, j = map(_decimal, (data.force, data.compliance, data.coupling))
                x, y, z = [b-a for a, b in zip(coordinates[left], coordinates[right])]
                cross = [[Decimal(0), -z, y], [z, Decimal(0), -x], [-y, x, Decimal(0)]]
                identity = [[Decimal(i == k) for k in range(3)] for i in range(3)]
                left_map, right_map = _solve(frames[left], identity), _solve(frames[right], identity)
                force_moment = _multiply(right_map, cross)
                w = [[Decimal(0)]*3+row for row in left_map]
                w += [[-value for value in force]+moment for force, moment in zip(force_moment, right_map)]
                coupling = _multiply(_transpose(j), w)
                v = [[(Decimal(i == k) if k < 3 else Decimal(0))-coupling[i][k]
                      for k in range(6)] for i in range(3)]
                first = _multiply(_transpose(v), _solve(f, v))
                second = _multiply(_transpose(w), _multiply(h, w))
                flexibility = [[a+b for a, b in zip(row, other)] for row, other in zip(first, second)]
                inverse = _solve(flexibility, [[Decimal(i == k) for k in range(6)] for i in range(6)])
                self.cells.append((tuple(tuple(row) for row in cross), tuple(tuple(row) for row in inverse)))
        self.cells = tuple(self.cells)

    def action(self, high, low=None):
        high = _array(high, (18,), "displacement high")
        low = np.zeros(18) if low is None else _array(low, (18,), "displacement low")
        with localcontext(Context(prec=80, rounding=ROUND_HALF_EVEN)):
            values = [Decimal.from_float(float(a))+Decimal.from_float(float(b)) for a, b in zip(high, low)]
            result = [Decimal(0) for _ in range(18)]
            for (cross, inverse), (left, right) in zip(self.cells, HALVES):
                translation = [[values[6*right+i]-values[6*left+i]] for i in range(3)]
                theta_right = [[values[6*right+3+i]] for i in range(3)]
                rotation = [[values[6*right+3+i]-values[6*left+3+i]] for i in range(3)]
                lever = _multiply(cross, theta_right)
                work = [[a[0]+b[0]] for a, b in zip(translation, lever)]+rotation
                stresses = _multiply(inverse, work)
                force, moment = stresses[:3], stresses[3:]
                change = _multiply(cross, force)
                for i in range(3):
                    result[6*left+i] -= force[i][0]
                    result[6*right+i] += force[i][0]
                    result[6*left+3+i] -= moment[i][0]
                    result[6*right+3+i] += moment[i][0]-change[i][0]
            made = np.array([float(value) for value in result])
        if not np.isfinite(made).all():
            raise ValueError("nonfinite precise reference action")
        return made
