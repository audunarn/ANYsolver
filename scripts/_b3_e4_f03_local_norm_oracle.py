"""Bounded, independent Decimal Green oracle for synthetic local-norm checks.

This is not the production norm or an acceptance gate. Each interval holds
three physical density polynomials in ascending powers of local tau in [0, 1],
padded to six coefficients, plus a global cosine amplitude per component.
Only the two physical endpoint atoms occur. Moment components are divided by
the held binary64 ELL exactly once per operand.

Gauss rules are generated entirely in Decimal. Exact rational common cuts and
polynomial restrictions split the diagonal; every off-diagonal rectangle is
then integrated directly, without prefix sums or factored interval moments.
The 70-digit arithmetic is a numerical oracle, not an interval certificate.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import (Context, Decimal, DivisionByZero, InvalidOperation, Overflow,
                     ROUND_HALF_EVEN, localcontext)
from fractions import Fraction
from functools import lru_cache
from math import comb, pi
from collections.abc import Mapping


DIGITS = 70
ORDERS = (16, 24)
MAX_INTERVALS = 8
MAX_UNION_INTERVALS = 15
MAX_INPUT_BITS = 4096
ELL = Fraction.from_float(.46)
OMEGA = Fraction.from_float(2 * pi)
_PI = Decimal('3.141592653589793238462643383279502884197169399375105820974944592307816406286')
_ZERO = Decimal(0)
_ONE = Decimal(1)
_CONTEXT = Context(prec=DIGITS, rounding=ROUND_HALF_EVEN, Emin=-999999, Emax=999999,
                   capitals=1, clamp=0, traps=[InvalidOperation, DivisionByZero, Overflow])


@dataclass(frozen=True)
class Functional:
    cuts: tuple[Fraction, ...]
    coefficients: tuple[tuple[tuple[Fraction, ...], ...], ...]
    cosine: tuple[Fraction, ...]
    atoms: tuple[tuple[Fraction, ...], ...]


@dataclass(frozen=True)
class NormResult:
    channels: tuple[Decimal, Decimal, Decimal]
    total: Decimal


def _fraction(value: object) -> Fraction:
    if type(value) is not Fraction:
        raise ValueError('oracle inputs must contain exact Fraction values')
    if (value.numerator.bit_length() > MAX_INPUT_BITS or
            value.denominator.bit_length() > MAX_INPUT_BITS):
        raise ValueError('oracle rational exceeds the fixed input bit bound')
    return value


def _tuple(value: object, length: int) -> tuple:
    if type(value) is not tuple or len(value) != length:
        raise ValueError('oracle input has an invalid tuple shape')
    return value


def validate_functional(record: Mapping | Functional) -> Functional:
    """Validate the bounded exact input and return an owned immutable record."""
    keys = ('cuts', 'coefficients', 'cosine', 'atoms')
    if type(record) is Functional:
        values = {key: getattr(record, key) for key in keys}
    elif isinstance(record, Mapping) and set(record) == set(keys):
        values = record
    else:
        raise ValueError('oracle input must have exactly the four declared fields')
    raw_cuts = values['cuts']
    if type(raw_cuts) is not tuple or not 2 <= len(raw_cuts) <= MAX_INTERVALS + 1:
        raise ValueError('oracle supports one through eight input intervals')
    cuts = tuple(_fraction(x) for x in raw_cuts)
    if cuts[0] != 0 or cuts[-1] != 1 or any(b <= a for a, b in zip(cuts, cuts[1:])):
        raise ValueError('oracle cuts must strictly partition [0, 1]')
    coefficients = tuple(
        tuple(tuple(_fraction(c) for c in _tuple(channel, 6))
              for channel in _tuple(cell, 3))
        for cell in _tuple(values['coefficients'], len(cuts) - 1))
    cosine = tuple(_fraction(c) for c in _tuple(values['cosine'], 3))
    atoms = tuple(tuple(_fraction(c) for c in _tuple(atom, 3))
                  for atom in _tuple(values['atoms'], 2))
    return Functional(cuts, coefficients, cosine, atoms)


def _decimal(value: Fraction) -> Decimal:
    return Decimal(value.numerator) / Decimal(value.denominator)


def _cos(value: Decimal) -> Decimal:
    """Taylor cosine; all call arguments have magnitude at most held 2*pi."""
    term = _ONE
    result = _ONE
    square = value * value
    for k in range(1, 256):
        term = -term * square / ((2 * k - 1) * (2 * k))
        result += term
        if abs(term) < Decimal('1e-76'):
            return result
    raise ArithmeticError('bounded Decimal cosine did not converge')


def _legendre(order: int, x: Decimal) -> tuple[Decimal, Decimal]:
    previous, value = _ONE, x
    for k in range(2, order + 1):
        previous, value = value, ((2 * k - 1) * x * value - (k - 1) * previous) / k
    derivative = order * (x * value - previous) / (x * x - 1)
    return value, derivative


@lru_cache(maxsize=2)
def _gauss(order: int) -> tuple[tuple[Decimal, Decimal], ...]:
    """Independent 70-digit Gauss-Legendre rule on [0, 1]."""
    if type(order) is not int or order not in ORDERS:
        raise ValueError('the fixed oracle orders are 16 and 24')
    with localcontext(_CONTEXT):
        points = []
        for k in range(1, order // 2 + 1):
            x = _cos(_PI * (Decimal(k) - Decimal('.25')) / (Decimal(order) + Decimal('.5')))
            for _ in range(64):
                value, derivative = _legendre(order, x)
                step = value / derivative
                x -= step
                if abs(step) < Decimal('1e-65'):
                    break
            else:
                raise ArithmeticError('Decimal Gauss root did not converge')
            value, derivative = _legendre(order, x)
            if abs(value) > Decimal('1e-63') or not 0 < x < 1:
                raise ArithmeticError('invalid Decimal Gauss root')
            weight = _ONE / ((1 - x * x) * derivative * derivative)
            points.extend((((1 - x) / 2, weight), ((1 + x) / 2, weight)))
        points.sort()
        if (any(w <= 0 for _, w in points) or
                abs(sum((w for _, w in points), _ZERO) - 1) > Decimal('1e-63')):
            raise ArithmeticError('invalid Decimal Gauss weights')
        return tuple(points)


def _restrict(functional: Functional, cuts: tuple[Fraction, ...]) -> tuple:
    """Exact affine restriction; no float cut, midpoint, or width is formed."""
    result = []
    cell = 0
    for a, b in zip(cuts, cuts[1:]):
        while a >= functional.cuts[cell + 1]:
            cell += 1
        left, right = functional.cuts[cell:cell + 2]
        if not left <= a < b <= right:
            raise ArithmeticError('common interval failed exact containment')
        alpha, beta = (a - left) / (right - left), (b - a) / (right - left)
        channels = []
        for coefficients in functional.coefficients[cell]:
            channels.append(tuple(beta ** k * sum(
                (coefficients[j] * comb(j, k) * alpha ** (j - k) for j in range(k, 6)),
                Fraction(0)) for k in range(6)))
        result.append(tuple(channels))
    return tuple(result)


def _poly(coefficients: tuple[Decimal, ...], tau: Decimal) -> Decimal:
    result = _ZERO
    for coefficient in reversed(coefficients):
        result = result * tau + coefficient
    return result


def _cosh(value: Decimal) -> Decimal:
    return (value.exp() + (-value).exp()) / 2


def _sample(a: Decimal, width: Decimal, tau: Decimal, first: tuple,
            second: tuple, cosine_f: tuple, cosine_g: tuple, omega: Decimal) -> tuple:
    # Width is independently converted from its positive exact rational value.
    # Even when adding width*tau rounds at 70 digits, its integration measure
    # survives and the lost coordinate variation is below working precision.
    station = a + width * tau
    cosine = _cos(omega * station) if any(cosine_f) or any(cosine_g) else _ZERO
    f = tuple(_poly(first[c], tau) + cosine_f[c] * cosine for c in range(3))
    g = tuple(_poly(second[c], tau) + cosine_g[c] * cosine for c in range(3))
    return f, g, _cosh(station), _cosh(1 - station)


def green_inner(first: Mapping | Functional, second: Mapping | Functional, *,
                order: int = 16) -> tuple[Decimal, Decimal, Decimal]:
    """Raw channelwise bilinear form; signed cross terms are never clipped."""
    if type(order) is not int or order not in ORDERS:
        raise ValueError('the fixed oracle orders are 16 and 24')
    f, g = validate_functional(first), validate_functional(second)
    cuts = tuple(sorted(set(f.cuts) | set(g.cuts)))
    if len(cuts) - 1 > MAX_UNION_INTERVALS:
        raise ValueError('oracle common partition exceeds fifteen intervals')
    fc, gc = _restrict(f, cuts), _restrict(g, cuts)
    with localcontext(_CONTEXT):
        scales = (Fraction(1), Fraction(1), 1 / ELL)
        fc = tuple(tuple(tuple(_decimal(v * scales[c]) for v in cell[c])
                         for c in range(3)) for cell in fc)
        gc = tuple(tuple(tuple(_decimal(v * scales[c]) for v in cell[c])
                         for c in range(3)) for cell in gc)
        cosine_f = tuple(_decimal(f.cosine[c] * scales[c]) for c in range(3))
        cosine_g = tuple(_decimal(g.cosine[c] * scales[c]) for c in range(3))
        atoms_f = tuple(tuple(_decimal(atom[c] * scales[c]) for c in range(3)) for atom in f.atoms)
        atoms_g = tuple(tuple(_decimal(atom[c] * scales[c]) for c in range(3)) for atom in g.atoms)
        rule = _gauss(order)
        omega = _decimal(OMEGA)
        sinh_one = (_ONE.exp() - (-_ONE).exp()) / 2
        cosh_one = _cosh(_ONE)
        channels = [_ZERO, _ZERO, _ZERO]
        widths = tuple(_decimal(b - a) for a, b in zip(cuts, cuts[1:]))
        samples = []
        for i, (left, width) in enumerate(zip(cuts, widths)):
            a = _decimal(left)
            points = tuple(_sample(a, width, u, fc[i], gc[i], cosine_f, cosine_g, omega)
                           for u, _ in rule)
            samples.append(points)
            # Two triangles fill the diagonal square. Each pair includes both
            # operand orientations and the Duffy Jacobian width**2 * u.
            for (u, wu), outer in zip(rule, points):
                for v, wv in rule:
                    inner = _sample(a, width, u * v, fc[i], gc[i], cosine_f, cosine_g, omega)
                    weight = width * width * u * wu * wv * inner[2] * outer[3] / sinh_one
                    for c in range(3):
                        channels[c] += weight * (outer[0][c] * inner[1][c] +
                                                  outer[1][c] * inner[0][c])
            # Density/atom terms: each of the two operands contributes once.
            for (_, w), point in zip(rule, points):
                for c in range(3):
                    root = atoms_f[0][c] * point[1][c] + atoms_g[0][c] * point[0][c]
                    tip = atoms_f[1][c] * point[1][c] + atoms_g[1][c] * point[0][c]
                    channels[c] += width * w * (root * point[3] + tip * point[2]) / sinh_one
        # Direct rectangle quadrature, including both ordered operand pairs.
        for i in range(len(widths)):
            for j in range(i + 1, len(widths)):
                for (_, wi), lower in zip(rule, samples[i]):
                    for (_, wj), upper in zip(rule, samples[j]):
                        weight = widths[i] * widths[j] * wi * wj * lower[2] * upper[3] / sinh_one
                        for c in range(3):
                            channels[c] += weight * (lower[0][c] * upper[1][c] +
                                                      lower[1][c] * upper[0][c])
        for c in range(3):
            channels[c] += (cosh_one * (atoms_f[0][c] * atoms_g[0][c] +
                                         atoms_f[1][c] * atoms_g[1][c]) +
                            atoms_f[0][c] * atoms_g[1][c] +
                            atoms_f[1][c] * atoms_g[0][c]) / sinh_one
        if not all(value.is_finite() for value in channels):
            raise ArithmeticError('nonfinite Decimal Green bilinear response')
        return tuple(channels)


def norm_squared(functional: Mapping | Functional, *, order: int = 16) -> NormResult:
    """Return raw per-channel and total squared norms, with no repair or gate."""
    channels = green_inner(functional, functional, order=order)
    with localcontext(_CONTEXT):
        total = sum(channels, _ZERO)
    if not total.is_finite():
        raise ArithmeticError('nonfinite Decimal full squared norm')
    return NormResult(channels, total)
