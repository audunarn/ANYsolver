"""Exact dyadic outward intervals for the S4 Stage-M mechanics oracle.

This module is proof infrastructure, not production numerics.  Endpoints are
``fractions.Fraction`` values whose denominators are powers of two whenever an
interval is created by :func:`sqrt_fraction`.  All arithmetic is outward by
exact rational inclusion; no binary floating-point value enters a bound.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import isqrt
import re
from typing import Iterable, Sequence


class IntervalError(ValueError):
    """Raised when a requested interval operation is not certifiable."""


def _fraction(value: Fraction | int) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return Fraction(value, 1)
    raise TypeError("dyadic interval endpoints require Fraction or int")


@dataclass(frozen=True, slots=True)
class DyadicInterval:
    """Closed exact interval with rational endpoints."""

    lower: Fraction
    upper: Fraction

    def __post_init__(self) -> None:
        lower = _fraction(self.lower)
        upper = _fraction(self.upper)
        if lower > upper:
            raise IntervalError("interval lower endpoint exceeds upper endpoint")
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)

    @classmethod
    def point(cls, value: Fraction | int) -> "DyadicInterval":
        exact = _fraction(value)
        return cls(exact, exact)

    @property
    def is_point(self) -> bool:
        return self.lower == self.upper

    @property
    def contains_zero(self) -> bool:
        return self.lower <= 0 <= self.upper

    @property
    def midpoint(self) -> Fraction:
        return (self.lower + self.upper) / 2

    @property
    def width(self) -> Fraction:
        return self.upper - self.lower

    def sign(self) -> int | None:
        if self.lower > 0:
            return 1
        if self.upper < 0:
            return -1
        if self.is_point and self.lower == 0:
            return 0
        return None

    def __neg__(self) -> "DyadicInterval":
        return DyadicInterval(-self.upper, -self.lower)

    def __add__(self, other: "DyadicInterval") -> "DyadicInterval":
        if not isinstance(other, DyadicInterval):
            return NotImplemented
        return DyadicInterval(self.lower + other.lower, self.upper + other.upper)

    def __sub__(self, other: "DyadicInterval") -> "DyadicInterval":
        if not isinstance(other, DyadicInterval):
            return NotImplemented
        return self + (-other)

    def __mul__(self, other: "DyadicInterval") -> "DyadicInterval":
        if not isinstance(other, DyadicInterval):
            return NotImplemented
        products = (
            self.lower * other.lower,
            self.lower * other.upper,
            self.upper * other.lower,
            self.upper * other.upper,
        )
        return DyadicInterval(min(products), max(products))

    def reciprocal(self) -> "DyadicInterval":
        if self.contains_zero:
            raise IntervalError("cannot invert an interval containing zero")
        reciprocals = (1 / self.lower, 1 / self.upper)
        return DyadicInterval(min(reciprocals), max(reciprocals))

    def __truediv__(self, other: "DyadicInterval") -> "DyadicInterval":
        if not isinstance(other, DyadicInterval):
            return NotImplemented
        return self * other.reciprocal()

    def square(self) -> "DyadicInterval":
        if self.contains_zero:
            return DyadicInterval(Fraction(0), max(self.lower * self.lower, self.upper * self.upper))
        squares = (self.lower * self.lower, self.upper * self.upper)
        return DyadicInterval(min(squares), max(squares))

    def token(self) -> dict[str, list[str]]:
        return {
            "lower": [str(self.lower.numerator), str(self.lower.denominator)],
            "upper": [str(self.upper.numerator), str(self.upper.denominator)],
        }


def fraction_from_decimal(text: str) -> Fraction:
    """Parse a finite base-ten decimal or signed rational string exactly."""

    if not isinstance(text, str) or not text or text.strip() != text:
        raise IntervalError("exact decimal token must be a trimmed nonempty string")
    rational_match = re.fullmatch(r"(-?(?:0|[1-9][0-9]*))/([1-9][0-9]*)", text)
    if rational_match:
        numerator = int(rational_match.group(1))
        denominator = int(rational_match.group(2))
        if denominator <= 0:
            raise IntervalError("rational denominator must be positive")
        return Fraction(numerator, denominator)
    decimal_match = re.fullmatch(
        r"(-?(?:0|[1-9][0-9]*))(?:\.([0-9]+))?(?:e(-?(?:0|[1-9][0-9]*)))?",
        text,
    )
    if decimal_match is None:
        raise IntervalError("invalid canonical decimal token")
    whole_text, fractional, exponent_text = decimal_match.groups()
    fractional = fractional or ""
    exponent = int(exponent_text) if exponent_text is not None else 0
    sign = -1 if whole_text.startswith("-") else 1
    whole = whole_text.lstrip("-")
    digits = whole + fractional
    value = Fraction(sign * int(digits), 10 ** len(fractional))
    return value * (Fraction(10) ** exponent)


def fraction_from_mpf_tuple(token: Sequence[int]) -> Fraction:
    """Convert an mpmath ``_mpf_`` tuple to its exact dyadic value."""

    if len(token) != 4:
        raise IntervalError("mpf tuple must have four entries")
    sign, mantissa, exponent, bitcount = token
    if any(isinstance(value, bool) or not isinstance(value, int) for value in token):
        raise IntervalError("mpf tuple entries must be integers")
    if sign not in (0, 1) or mantissa < 0 or bitcount < 0:
        raise IntervalError("invalid finite mpf tuple")
    if mantissa == 0:
        if (sign, exponent, bitcount) != (0, 0, 0):
            raise IntervalError("zero mpf tuple is not canonical")
        return Fraction(0)
    if bitcount != mantissa.bit_length() or mantissa % 2 == 0:
        raise IntervalError("nonzero mpf tuple is not canonical")
    value = Fraction(mantissa) * (Fraction(2) ** exponent)
    return -value if sign else value


def sqrt_fraction(value: Fraction, bits: int) -> DyadicInterval:
    """Return a dyadic enclosure of a nonnegative rational square root."""

    value = _fraction(value)
    if value < 0:
        raise IntervalError("square root requires a nonnegative value")
    if isinstance(bits, bool) or not isinstance(bits, int) or bits <= 0:
        raise IntervalError("square-root precision must be a positive integer")
    scaled_numerator = value.numerator << (2 * bits)
    quotient = scaled_numerator // value.denominator
    floor_scaled = isqrt(quotient)
    denominator = 1 << bits
    lower = Fraction(floor_scaled, denominator)
    if floor_scaled * floor_scaled * value.denominator == scaled_numerator:
        return DyadicInterval.point(lower)
    return DyadicInterval(lower, Fraction(floor_scaled + 1, denominator))


def sqrt_interval(value: DyadicInterval, bits: int) -> DyadicInterval:
    """Return an outward dyadic enclosure of a nonnegative interval root."""

    if not isinstance(value, DyadicInterval):
        raise TypeError("sqrt_interval requires a DyadicInterval")
    if value.lower < 0:
        raise IntervalError("interval square root requires a nonnegative lower bound")
    lower = sqrt_fraction(value.lower, bits).lower
    upper = sqrt_fraction(value.upper, bits).upper
    return DyadicInterval(lower, upper)


def sum_intervals(values: Iterable[DyadicInterval]) -> DyadicInterval:
    result = DyadicInterval.point(0)
    for value in values:
        result = result + value
    return result


def dot_intervals(
    left: Sequence[DyadicInterval], right: Sequence[DyadicInterval]
) -> DyadicInterval:
    if len(left) != len(right):
        raise IntervalError("interval dot product dimensions differ")
    return sum_intervals(a * b for a, b in zip(left, right, strict=True))


def determinant_interval(matrix: Sequence[Sequence[DyadicInterval]]) -> DyadicInterval:
    """Certify a square determinant through deterministic interval LU.

    The first row at or below the pivot whose interval excludes zero is used.
    If every candidate contains zero, the minor is unclassified rather than
    guessed from midpoint pivoting.
    """

    size = len(matrix)
    if any(len(row) != size for row in matrix):
        raise IntervalError("determinant requires a square interval matrix")
    if size == 0:
        return DyadicInterval.point(1)
    work = [[entry for entry in row] for row in matrix]
    sign = 1
    determinant = DyadicInterval.point(1)
    for column in range(size):
        pivot_row = next(
            (row for row in range(column, size) if not work[row][column].contains_zero),
            None,
        )
        if pivot_row is None:
            raise IntervalError(f"minor pivot {column} is not sign-certified")
        if pivot_row != column:
            work[column], work[pivot_row] = work[pivot_row], work[column]
            sign = -sign
        pivot = work[column][column]
        determinant = determinant * pivot
        for row in range(column + 1, size):
            factor = work[row][column] / pivot
            work[row][column] = DyadicInterval.point(0)
            for inner in range(column + 1, size):
                work[row][inner] = work[row][inner] - factor * work[column][inner]
    return determinant if sign > 0 else -determinant


def certify_nonzero_minor(
    matrix: Sequence[Sequence[DyadicInterval]],
) -> tuple[int, DyadicInterval]:
    determinant = determinant_interval(matrix)
    sign = determinant.sign()
    if sign not in (-1, 1):
        raise IntervalError("minor determinant interval contains zero")
    return sign, determinant


__all__ = [
    "DyadicInterval",
    "IntervalError",
    "certify_nonzero_minor",
    "determinant_interval",
    "dot_intervals",
    "fraction_from_decimal",
    "fraction_from_mpf_tuple",
    "sqrt_fraction",
    "sqrt_interval",
    "sum_intervals",
]
