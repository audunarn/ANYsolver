"""Independent bounded coercivity proof for the admitted S3 triangle domain.

This research-only program does not import ANYsolver or the independent point
reference.  It transcribes the published flat MITC3+ kinematic identities and
the barycentric PL completion into scalar outward-rounded intervals.  The
proof normalizes the production formulation's directed edge 01 to one, without
relabeling connectivity, and encloses every admitted triangle in the compact
gauge

    (0, 0), (1, 0), (a, b),   -5 <= a <= 5,  1/6 <= b <= 5.

The rectangle is deliberately a strict *superset* of the frozen admission
envelope.  The edge-ratio gate (including its binary64 comparison margin)
bounds every edge relative to edge 01 by less than five.  The normalized-area
gate gives ``b > 1/6`` after longest-length scaling and therefore also after
edge-01 scaling.  Proving the larger rectangle avoids classifying a finite
collection of sampled shapes as a domain proof.

Constitutive matrices are normalized by their strictly positive smallest
eigenvalue.  If ``D >= I`` then stationary bubble minimization is monotone, and
the invariant drilling definition gives ``k_D >= 1/2``.  It is therefore
sufficient to certify the baseline ``D = I_8, k_D = 1/2``.  Exact Laurent-
polynomial identities independently prove the six rigid modes and two selected
nonzero quotient minors.  Outward interval Frobenius bounds turn those minors
into positive bubble, uncondensed, condensed, and total quotient lower bounds
over a deterministic adaptive cover.  The complete root certifies as one leaf;
subdivision remains a fail-safe for future input mutations.

Canonical output contains no timings or platform-dependent floating text.
Every numeric lower bound is encoded as the exact binary64 ratio that was
rounded toward minus infinity.

The implemented binary64 tying coordinates, tying offset, assumed-shear
interpolation coefficients, station coordinates, and quadrature weights are
frozen as exact algebraic inputs.  Ideal decimal or rational replacements are
not substituted by this certificate.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence



SCHEMA = "anysolver.e4_pl_s3.domain-coercivity-certificate.v1"
IMPLEMENTATION_ID = "INDEPENDENT_OUTWARD_INTERVAL_MITC3_PLUS_DOMAIN_V1"
FORMULATION_ID = "E4_PL_QUALIFIED_S3_COMPANION_V1"
QUOTIENT_METRIC_ID = "LOCAL_EDGE_01_ONE_EUCLIDEAN_DISTANCE_TO_RIGID_KERNEL_V1"
LONGEST_EDGE_QUOTIENT_METRIC_ID = (
    "LOCAL_LONGEST_EDGE_ONE_EUCLIDEAN_DISTANCE_TO_RIGID_KERNEL_V1"
)
CONSTITUTIVE_SCALING_ID = "LAMBDA_MIN_GENERALIZED_SECTION_WITH_KD_HALF_LOWER_BOUND_V1"
ADMISSION_ENVELOPE_ID = "QUALIFIED_S3_TRIANGLE_QUALITY_ENVELOPE_V1"
OUTWARD_POLICY_ID = "IEEE754_BINARY64_NEXTAFTER_EACH_SCALAR_OPERATION_V1"
PARTITION_POLICY_ID = "DYADIC_EDGE_01_NORMALIZED_SIDE_A_THEN_B_V1"
SELECTED_MINOR_POLICY_ID = "MITC3_PLUS_STATIONS_0_1_ELEVEN_ROWS_PLUS_PL3_V1"

# Exact determinant magnitude of both the selected 11x11 physical quotient
# map and the selected 14x14 physical-plus-PL quotient map in the production
# edge-01 gauge.  The complete determinant is ``-SELECTED_MINOR_CONSTANT/b**4``.
SELECTED_MINOR_CONSTANT = Fraction(
    24131211115033561645513037560451634903448148438445943644871167790144091683520062131482257210029944386723480798559263045629375,
    10830740992659433045228180406808920716548582325686783496759685861775864483615725089999900023844295226942934417817982702456930304,
)
SELECTED_PHYSICAL_ROWS = (
    (0, 0),
    (0, 1),
    (0, 2),
    (0, 3),
    (0, 4),
    (0, 5),
    (0, 6),
    (0, 7),
    (1, 3),
    (1, 5),
    (1, 6),
)

BUBBLE_SCALE = 27.0
TYING_OFFSET = 1.0e-4
SHEAR_TWO_THIRDS_BINARY64 = Fraction.from_float(2.0 / 3.0)
SHEAR_ONE_THIRD_BINARY64 = Fraction.from_float(1.0 / 3.0)
TYING_POINTS: Mapping[str, tuple[float, float]] = {
    "A": (1.0 / 6.0, 2.0 / 3.0),
    "B": (2.0 / 3.0, 1.0 / 6.0),
    "C": (1.0 / 6.0, 1.0 / 6.0),
    "D": (1.0 / 3.0 + TYING_OFFSET, 1.0 / 3.0 - 2.0 * TYING_OFFSET),
    "E": (1.0 / 3.0 - 2.0 * TYING_OFFSET, 1.0 / 3.0 + TYING_OFFSET),
    "F": (1.0 / 3.0 + TYING_OFFSET, 1.0 / 3.0 + TYING_OFFSET),
}
SEVEN_POINT_RULE: tuple[tuple[float, float, float], ...] = (
    (1.0 / 3.0, 1.0 / 3.0, 0.1125),
    (0.470142064105115, 0.470142064105115, 0.066197076394253),
    (0.059715871789770, 0.470142064105115, 0.066197076394253),
    (0.470142064105115, 0.059715871789770, 0.066197076394253),
    (0.101286507323456, 0.101286507323456, 0.062969590272414),
    (0.797426985353087, 0.101286507323456, 0.062969590272414),
    (0.101286507323456, 0.797426985353087, 0.062969590272414),
)
PHYSICAL_EXTERNAL_INDICES = tuple(
    6 * node + component for node in range(3) for component in range(5)
)
UNCONDENSED_PIVOT_INDICES = (0, 1, 2, 3, 4, 6)
UNCONDENSED_QUOTIENT_INDICES = tuple(
    index for index in range(17) if index not in UNCONDENSED_PIVOT_INDICES
)
CONDENSED_QUOTIENT_INDICES = tuple(
    index for index in range(15) if index not in UNCONDENSED_PIVOT_INDICES
)
TOTAL_QUOTIENT_INDICES = tuple(range(6, 18))


def _down(value: float) -> float:
    made = math.nextafter(float(value), -math.inf)
    if not math.isfinite(made):
        raise OverflowError("outward lower endpoint is nonfinite")
    return made


def _up(value: float) -> float:
    made = math.nextafter(float(value), math.inf)
    if not math.isfinite(made):
        raise OverflowError("outward upper endpoint is nonfinite")
    return made


@dataclass(frozen=True, slots=True)
class Interval:
    """Closed binary64 interval with scalar outward-rounded operations."""

    lo: float
    hi: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.lo) or not math.isfinite(self.hi) or self.lo > self.hi:
            raise ValueError("invalid finite interval")

    @classmethod
    def point(cls, value: float | int) -> "Interval":
        made = float(value)
        if not math.isfinite(made):
            raise ValueError("interval point must be finite")
        return cls(made, made)

    @classmethod
    def rational(cls, value: Fraction) -> "Interval":
        nearest = float(value)
        exact = Fraction.from_float(nearest)
        if exact == value:
            return cls(nearest, nearest)
        if exact < value:
            return cls(nearest, _up(nearest))
        return cls(_down(nearest), nearest)

    def __neg__(self) -> "Interval":
        return Interval(_down(-self.hi), _up(-self.lo))

    def __add__(self, other: object) -> "Interval":
        right = as_interval(other)
        return Interval(_down(self.lo + right.lo), _up(self.hi + right.hi))

    def __radd__(self, other: object) -> "Interval":
        return self + other

    def __sub__(self, other: object) -> "Interval":
        right = as_interval(other)
        return Interval(_down(self.lo - right.hi), _up(self.hi - right.lo))

    def __rsub__(self, other: object) -> "Interval":
        return as_interval(other) - self

    def __mul__(self, other: object) -> "Interval":
        right = as_interval(other)
        products = (
            self.lo * right.lo,
            self.lo * right.hi,
            self.hi * right.lo,
            self.hi * right.hi,
        )
        return Interval(_down(min(products)), _up(max(products)))

    def __rmul__(self, other: object) -> "Interval":
        return self * other

    def reciprocal(self) -> "Interval":
        if self.lo <= 0.0 <= self.hi:
            raise ZeroDivisionError("interval contains zero")
        values = (1.0 / self.lo, 1.0 / self.hi)
        return Interval(_down(min(values)), _up(max(values)))

    def __truediv__(self, other: object) -> "Interval":
        return self * as_interval(other).reciprocal()

    def __rtruediv__(self, other: object) -> "Interval":
        return as_interval(other) / self

    @property
    def abs_upper(self) -> float:
        return _up(max(abs(self.lo), abs(self.hi)))

    def intersect(self, other: "Interval") -> "Interval":
        lower = max(self.lo, other.lo)
        upper = min(self.hi, other.hi)
        if lower > upper:
            raise ArithmeticError("independent interval enclosures are disjoint")
        return Interval(lower, upper)


def as_interval(value: object) -> Interval:
    if isinstance(value, Interval):
        return value
    if isinstance(value, Fraction):
        return Interval.rational(value)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("interval scalar must be real")
    return Interval.point(value)


Matrix = list[list[Interval]]


def _zeros(rows: int, columns: int) -> Matrix:
    return [[Interval.point(0.0) for _ in range(columns)] for _ in range(rows)]


def _transpose(matrix: Matrix) -> Matrix:
    return [list(column) for column in zip(*matrix)]


def _matmul(left: Matrix, right: Matrix) -> Matrix:
    if not left or not right or len(left[0]) != len(right):
        raise ValueError("interval matrix multiply shape mismatch")
    columns = _transpose(right)
    result = _zeros(len(left), len(columns))
    for row_index, row in enumerate(left):
        for column_index, column in enumerate(columns):
            total = Interval.point(0.0)
            for a, b in zip(row, column):
                total = total + a * b
            result[row_index][column_index] = total
    return result


def _compatible(inverse: Matrix, r: float, s: float) -> tuple[Matrix, Matrix, Matrix]:
    derivative_r = (Interval.point(-1.0), Interval.point(1.0), Interval.point(0.0))
    derivative_s = (Interval.point(-1.0), Interval.point(0.0), Interval.point(1.0))
    derivative_x = tuple(
        inverse[0][0] * dr + inverse[0][1] * ds
        for dr, ds in zip(derivative_r, derivative_s)
    )
    derivative_y = tuple(
        inverse[1][0] * dr + inverse[1][1] * ds
        for dr, ds in zip(derivative_r, derivative_s)
    )
    r_interval = Interval.point(r)
    s_interval = Interval.point(s)
    one = Interval.point(1.0)
    shape = (one - r_interval - s_interval, r_interval, s_interval)
    bubble = (
        Interval.point(BUBBLE_SCALE)
        * r_interval
        * s_interval
        * (one - r_interval - s_interval)
    )
    bubble_r = (
        Interval.point(BUBBLE_SCALE)
        * s_interval
        * (one - Interval.point(2.0) * r_interval - s_interval)
    )
    bubble_s = (
        Interval.point(BUBBLE_SCALE)
        * r_interval
        * (one - r_interval - Interval.point(2.0) * s_interval)
    )
    bubble_x = inverse[0][0] * bubble_r + inverse[0][1] * bubble_s
    bubble_y = inverse[1][0] * bubble_r + inverse[1][1] * bubble_s

    membrane = _zeros(3, 17)
    bending = _zeros(3, 17)
    shear = _zeros(2, 17)
    for node in range(3):
        base = 5 * node
        membrane[0][base] = derivative_x[node]
        membrane[1][base + 1] = derivative_y[node]
        membrane[2][base] = derivative_y[node]
        membrane[2][base + 1] = derivative_x[node]
        bending[0][base + 4] = derivative_x[node]
        bending[1][base + 3] = -derivative_y[node]
        bending[2][base + 4] = derivative_y[node]
        bending[2][base + 3] = -derivative_x[node]
        shear[0][base + 2] = derivative_x[node]
        shear[0][base + 4] = shape[node]
        shear[1][base + 2] = derivative_y[node]
        shear[1][base + 3] = -shape[node]
    bending[0][16] = bubble_x
    bending[1][15] = -bubble_y
    bending[2][16] = bubble_y
    bending[2][15] = -bubble_x
    shear[0][16] = bubble
    shear[1][15] = -bubble
    return membrane, bending, shear


def _covariant_sample(jacobian: Matrix, inverse: Matrix, point: tuple[float, float]) -> Matrix:
    return _matmul(jacobian, _compatible(inverse, *point)[2])


def _assumed_shear_samples(jacobian: Matrix, inverse: Matrix) -> dict[str, Matrix]:
    return {
        name: _covariant_sample(jacobian, inverse, point)
        for name, point in TYING_POINTS.items()
    }


def _assumed_shear(inverse: Matrix, samples: Mapping[str, Matrix], r: float, s: float) -> Matrix:
    # These are the exact values produced by the formulation's Python
    # expressions ``2.0 / 3.0`` and ``1.0 / 3.0``.  Using ideal thirds here
    # would certify a nearby, but different, selected minor.
    two_thirds = Interval.rational(SHEAR_TWO_THIRDS_BINARY64)
    one_third = Interval.rational(SHEAR_ONE_THIRD_BINARY64)
    constant_r = [
        two_thirds
        * (samples["B"][0][column] - Interval.point(0.5) * samples["B"][1][column])
        + one_third
        * (samples["C"][0][column] + samples["C"][1][column])
        for column in range(17)
    ]
    constant_s = [
        two_thirds
        * (samples["A"][1][column] - Interval.point(0.5) * samples["A"][0][column])
        + one_third
        * (samples["C"][0][column] + samples["C"][1][column])
        for column in range(17)
    ]
    twisting = [
        samples["F"][0][column]
        - samples["D"][0][column]
        - samples["F"][1][column]
        + samples["E"][1][column]
        for column in range(17)
    ]
    covariant = [
        [
            constant_r[column]
            + twisting[column]
            * (
                (Interval.point(3.0) * Interval.point(s) - Interval.point(1.0))
                / Interval.point(3.0)
            )
            for column in range(17)
        ],
        [
            constant_s[column]
            + twisting[column]
            * (
                (Interval.point(1.0) - Interval.point(3.0) * Interval.point(r))
                / Interval.point(3.0)
            )
            for column in range(17)
        ],
    ]
    return _matmul(inverse, covariant)


def _kinematic(
    inverse: Matrix, samples: Mapping[str, Matrix], r: float, s: float
) -> Matrix:
    membrane, bending, _compatible_shear = _compatible(inverse, r, s)
    return membrane + bending + _assumed_shear(inverse, samples, r, s)


def _selected_interval_matrices(a: Interval, b: Interval) -> tuple[Matrix, Matrix]:
    """Enclose the exact selected physical and physical-plus-PL row maps."""

    jacobian = [
        [Interval.point(1.0), Interval.point(0.0)],
        [a, b],
    ]
    inverse = [
        [Interval.point(1.0), Interval.point(0.0)],
        [-a / b, Interval.point(1.0) / b],
    ]
    samples = _assumed_shear_samples(jacobian, inverse)
    operators = [
        _kinematic(inverse, samples, r, s)
        for r, s, _weight in SEVEN_POINT_RULE[:2]
    ]
    physical = [
        [operators[station][component][column] for column in UNCONDENSED_QUOTIENT_INDICES]
        for station, component in SELECTED_PHYSICAL_ROWS
    ]

    total_columns = TOTAL_QUOTIENT_INDICES + (18, 19)
    total: Matrix = []
    for station, component in SELECTED_PHYSICAL_ROWS:
        source = operators[station][component]
        full = [Interval.point(0.0) for _ in range(20)]
        for physical_column, external_column in enumerate(PHYSICAL_EXTERNAL_INDICES):
            full[external_column] = source[physical_column]
        full[18] = source[15]
        full[19] = source[16]
        total.append([full[column] for column in total_columns])

    derivative_x = (
        Interval.point(-1.0),
        Interval.point(1.0),
        Interval.point(0.0),
    )
    derivative_y = (
        (a - Interval.point(1.0)) / b,
        -a / b,
        Interval.point(1.0) / b,
    )
    constraint = _zeros(3, 18)
    for row in range(3):
        for node in range(3):
            constraint[row][6 * node] = Interval.point(0.5) * derivative_y[node]
            constraint[row][6 * node + 1] = Interval.point(-0.5) * derivative_x[node]
        constraint[row][6 * row + 5] = Interval.point(1.0)
    for row in constraint:
        full = list(row) + [Interval.point(0.0), Interval.point(0.0)]
        total.append([full[column] for column in total_columns])
    return physical, total


def _selected_map_lower_bound(
    matrix: Matrix,
    *,
    determinant_lower: float,
    energy_coefficient_lower: float,
) -> dict[str, float | str]:
    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise ValueError("selected quotient map must be square")
    frobenius_squared_upper = 0.0
    for row in matrix:
        for value in row:
            magnitude = value.abs_upper
            frobenius_squared_upper = _up(
                frobenius_squared_upper + _up(magnitude * magnitude)
            )
    frobenius_upper = _up(math.sqrt(frobenius_squared_upper))
    denominator_upper = 1.0
    for _ in range(size - 1):
        denominator_upper = _up(denominator_upper * frobenius_upper)
    singular_lower = _down(determinant_lower / denominator_upper)
    squared_lower = _down(singular_lower * singular_lower)
    energy_lower = _down(energy_coefficient_lower * squared_lower)
    if singular_lower <= 0.0 or energy_lower <= 0.0:
        return {
            "classification": "UNRESOLVED",
            "energy_lower": energy_lower,
            "frobenius_upper": frobenius_upper,
            "singular_lower": singular_lower,
        }
    return {
        "classification": "POSITIVE",
        "energy_lower": energy_lower,
        "frobenius_upper": frobenius_upper,
        "singular_lower": singular_lower,
    }


@dataclass(frozen=True, slots=True)
class Box:
    a_lower: Fraction
    a_upper: Fraction
    b_lower: Fraction
    b_upper: Fraction
    path: str = ""

    @property
    def depth(self) -> int:
        return len(self.path)

    def split(self) -> tuple["Box", "Box"]:
        a_width = (self.a_upper - self.a_lower) / 10
        b_width = (self.b_upper - self.b_lower) * Fraction(6, 29)
        split_a = a_width >= b_width
        if split_a:
            midpoint = (self.a_lower + self.a_upper) / 2
            return (
                Box(self.a_lower, midpoint, self.b_lower, self.b_upper, self.path + "0"),
                Box(midpoint, self.a_upper, self.b_lower, self.b_upper, self.path + "1"),
            )
        midpoint = (self.b_lower + self.b_upper) / 2
        return (
            Box(self.a_lower, self.a_upper, self.b_lower, midpoint, self.path + "0"),
            Box(self.a_lower, self.a_upper, midpoint, self.b_upper, self.path + "1"),
        )

    def intervals(self) -> tuple[Interval, Interval]:
        a_lo = Interval.rational(self.a_lower).lo
        a_hi = Interval.rational(self.a_upper).hi
        b_lo = Interval.rational(self.b_lower).lo
        b_hi = Interval.rational(self.b_upper).hi
        return Interval(a_lo, a_hi), Interval(b_lo, b_hi)

    def record(self) -> dict[str, object]:
        def ratio(value: Fraction) -> list[int]:
            return [value.numerator, value.denominator]

        return {
            "a": [ratio(self.a_lower), ratio(self.a_upper)],
            "b": [ratio(self.b_lower), ratio(self.b_upper)],
            "path": self.path,
        }


ROOT = Box(Fraction(-5), Fraction(5), Fraction(1, 6), Fraction(5))


def _ratio(value: float) -> list[int]:
    fraction = Fraction.from_float(value)
    return [fraction.numerator, fraction.denominator]


def _evaluate_box(box: Box) -> dict[str, object]:
    try:
        a, b = box.intervals()
        physical, total = _selected_interval_matrices(a, b)
        b_fourth = b * b * b * b
        determinant_lower = (
            Interval.rational(SELECTED_MINOR_CONSTANT) / b_fourth
        ).lo
        minimum_selected_weight = min(
            SEVEN_POINT_RULE[station][2]
            for station, _component in SELECTED_PHYSICAL_ROWS
        )
        physical_coefficient = (
            b * Interval.point(minimum_selected_weight)
        ).lo
        # N=[[2,1,1],[1,2,1],[1,1,2]] has exact lambda_min=1;
        # k_D=1/2 and M=b*N/24 therefore give b/48 ||Cq||^2.
        total_coefficient = (b / Interval.point(48.0)).lo
        physical_result = _selected_map_lower_bound(
            physical,
            determinant_lower=determinant_lower,
            energy_coefficient_lower=physical_coefficient,
        )
        total_result = _selected_map_lower_bound(
            total,
            determinant_lower=determinant_lower,
            energy_coefficient_lower=min(
                physical_coefficient, total_coefficient
            ),
        )
    except (ArithmeticError, OverflowError, ZeroDivisionError, ValueError) as exc:
        return {"classification": "UNRESOLVED", "reason": type(exc).__name__}
    if physical_result["classification"] != "POSITIVE":
        return {
            "classification": "UNRESOLVED",
            "reason": "PHYSICAL_SELECTED_MINOR_NORM_BOUND_NOT_POSITIVE",
        }
    if total_result["classification"] != "POSITIVE":
        return {
            "classification": "UNRESOLVED",
            "reason": "TOTAL_SELECTED_MINOR_NORM_BOUND_NOT_POSITIVE",
        }
    return {
        "classification": "POSITIVE",
        "reason": "EXACT_SELECTED_MINORS_AND_OUTWARD_NORM_BOUNDS_POSITIVE",
        "quotient_lower": total_result["energy_lower"],
        # A positive 11-variable uncondensed quotient lower bound applies to
        # every principal block, including the two bubble variables.  Taking
        # the stationary minimum over bubbles preserves the same lower bound
        # on the nine-variable condensed physical quotient.
        "bubble_lower": physical_result["energy_lower"],
        "uncondensed_lower": physical_result["energy_lower"],
        "condensed_lower": physical_result["energy_lower"],
    }


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


def _binary64_input_record() -> dict[str, object]:
    return {
        "assumed_shear_interpolation": {
            "one_third_exact_binary64_ratio": [
                SHEAR_ONE_THIRD_BINARY64.numerator,
                SHEAR_ONE_THIRD_BINARY64.denominator,
            ],
            "two_thirds_exact_binary64_ratio": [
                SHEAR_TWO_THIRDS_BINARY64.numerator,
                SHEAR_TWO_THIRDS_BINARY64.denominator,
            ],
        },
        "quadrature": [
            [r.hex(), s.hex(), weight.hex()]
            for r, s, weight in SEVEN_POINT_RULE
        ],
        "tying_offset": TYING_OFFSET.hex(),
        "tying_points": {
            name: [r.hex(), s.hex()]
            for name, (r, s) in sorted(TYING_POINTS.items())
        },
    }


def _partition_hash(leaves: Iterable[Box]) -> str:
    payload = [leaf.record() for leaf in sorted(leaves, key=lambda item: item.path)]
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest().upper()


def _verify_partition(leaves: Sequence[Box]) -> None:
    paths = sorted(leaf.path for leaf in leaves)
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate cover leaf")
    for left, right in zip(paths, paths[1:]):
        if right.startswith(left):
            raise ValueError("cover leaf paths are not prefix-free")
    if sum((Fraction(1, 2 ** len(path)) for path in paths), Fraction()) != 1:
        raise ValueError("cover leaves do not form a complete binary partition")
    by_path = {leaf.path: leaf for leaf in leaves}
    for path, leaf in by_path.items():
        expected = ROOT
        for digit in path:
            left, right = expected.split()
            expected = left if digit == "0" else right
        if leaf != expected:
            raise ValueError("cover leaf bounds do not match split path")


# A tiny exact Laurent-polynomial algebra is enough for rigid-strain identities:
# all normalized-triangle coefficients are polynomials in ``a`` and integral
# powers of ``b``.  It is intentionally separate from the interval evaluator.
@dataclass(frozen=True)
class Laurent:
    terms: tuple[tuple[tuple[int, int], Fraction], ...]

    @classmethod
    def constant(cls, value: Fraction | int) -> "Laurent":
        made = Fraction(value)
        return cls(()) if made == 0 else cls((((0, 0), made),))

    @classmethod
    def monomial(cls, a_power: int, b_power: int, value: Fraction | int = 1) -> "Laurent":
        made = Fraction(value)
        return cls(()) if made == 0 else cls((((a_power, b_power), made),))

    def mapping(self) -> dict[tuple[int, int], Fraction]:
        return dict(self.terms)

    @classmethod
    def from_mapping(cls, values: Mapping[tuple[int, int], Fraction]) -> "Laurent":
        return cls(tuple(sorted((power, value) for power, value in values.items() if value)))

    def __add__(self, other: object) -> "Laurent":
        right = as_laurent(other)
        values = self.mapping()
        for power, value in right.terms:
            values[power] = values.get(power, Fraction()) + value
        return Laurent.from_mapping(values)

    def __radd__(self, other: object) -> "Laurent":
        return self + other

    def __neg__(self) -> "Laurent":
        return Laurent(tuple((power, -value) for power, value in self.terms))

    def __sub__(self, other: object) -> "Laurent":
        return self + (-as_laurent(other))

    def __rsub__(self, other: object) -> "Laurent":
        return as_laurent(other) - self

    def __mul__(self, other: object) -> "Laurent":
        right = as_laurent(other)
        values: dict[tuple[int, int], Fraction] = {}
        for (a_left, b_left), left_value in self.terms:
            for (a_right, b_right), right_value in right.terms:
                power = (a_left + a_right, b_left + b_right)
                values[power] = values.get(power, Fraction()) + left_value * right_value
        return Laurent.from_mapping(values)

    def __rmul__(self, other: object) -> "Laurent":
        return self * other

    def __truediv__(self, other: object) -> "Laurent":
        if isinstance(other, bool) or not isinstance(other, (int, Fraction)):
            return NotImplemented
        divisor = Fraction(other)
        if divisor == 0:
            raise ZeroDivisionError("exact Laurent scalar division by zero")
        return Laurent(tuple((power, value / divisor) for power, value in self.terms))

    @property
    def is_zero(self) -> bool:
        return not self.terms


def _laurent_exact_divide(dividend: Laurent, divisor: Laurent) -> Laurent:
    """Return the exact Laurent-polynomial quotient using lexicographic division."""

    if divisor.is_zero:
        raise ZeroDivisionError("exact Laurent polynomial division by zero")
    remainder = dividend.mapping()
    divisor_terms = divisor.mapping()
    divisor_power = max(divisor_terms)
    divisor_value = divisor_terms[divisor_power]
    quotient: dict[tuple[int, int], Fraction] = {}
    iterations = 0
    while remainder:
        iterations += 1
        if iterations > 100_000:
            raise ArithmeticError("exact Laurent polynomial division did not terminate")
        remainder_power = max(remainder)
        remainder_value = remainder[remainder_power]
        quotient_power = (
            remainder_power[0] - divisor_power[0],
            remainder_power[1] - divisor_power[1],
        )
        quotient_value = remainder_value / divisor_value
        quotient[quotient_power] = quotient.get(quotient_power, Fraction()) + quotient_value
        for power, value in divisor_terms.items():
            target = (power[0] + quotient_power[0], power[1] + quotient_power[1])
            made = remainder.get(target, Fraction()) - quotient_value * value
            if made:
                remainder[target] = made
            else:
                remainder.pop(target, None)
    result = Laurent.from_mapping(quotient)
    if result * divisor != dividend:
        raise ArithmeticError("Laurent polynomial quotient is not exact")
    return result


def _laurent_determinant(matrix: Sequence[Sequence[Laurent]]) -> Laurent:
    """Fraction-free Bareiss determinant over exact Laurent polynomials."""

    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise ValueError("exact determinant requires a nonempty square matrix")
    work = [[value for value in row] for row in matrix]
    previous = Laurent.constant(1)
    sign = 1
    for pivot_index in range(size - 1):
        pivot_row = next(
            (row for row in range(pivot_index, size) if not work[row][pivot_index].is_zero),
            None,
        )
        if pivot_row is None:
            return Laurent.constant(0)
        if pivot_row != pivot_index:
            work[pivot_index], work[pivot_row] = work[pivot_row], work[pivot_index]
            sign *= -1
        pivot = work[pivot_index][pivot_index]
        for row in range(pivot_index + 1, size):
            for column in range(pivot_index + 1, size):
                numerator = (
                    work[row][column] * pivot
                    - work[row][pivot_index] * work[pivot_index][column]
                )
                work[row][column] = (
                    numerator
                    if pivot_index == 0
                    else _laurent_exact_divide(numerator, previous)
                )
            work[row][pivot_index] = Laurent.constant(0)
        previous = pivot
    determinant = work[-1][-1]
    return determinant if sign > 0 else -determinant


def as_laurent(value: object) -> Laurent:
    if isinstance(value, Laurent):
        return value
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError("exact Laurent scalar must be integer or Fraction")
    return Laurent.constant(Fraction(value))


def _exact_rigid_identity() -> dict[str, object]:
    """Prove all published station and PL rigid identities coefficientwise."""

    zero = Laurent.constant(0)
    one = Laurent.constant(1)
    a = Laurent.monomial(1, 0)
    b = Laurent.monomial(0, 1)
    inverse = [[one, zero], [-a * Laurent.monomial(0, -1), Laurent.monomial(0, -1)]]

    def compatible(r: Fraction, s: Fraction) -> tuple[list[list[Laurent]], list[list[Laurent]], list[list[Laurent]]]:
        dr = (-one, one, zero)
        ds = (-one, zero, one)
        dx = tuple(inverse[0][0] * x + inverse[0][1] * y for x, y in zip(dr, ds))
        dy = tuple(inverse[1][0] * x + inverse[1][1] * y for x, y in zip(dr, ds))
        shape = (one - r - s, Laurent.constant(r), Laurent.constant(s))
        bubble = Laurent.constant(27 * r * s * (1 - r - s))
        bubble_r = Laurent.constant(27 * s * (1 - 2 * r - s))
        bubble_s = Laurent.constant(27 * r * (1 - r - 2 * s))
        bx = inverse[0][0] * bubble_r + inverse[0][1] * bubble_s
        by = inverse[1][0] * bubble_r + inverse[1][1] * bubble_s
        membrane = [[zero for _ in range(17)] for _ in range(3)]
        bending = [[zero for _ in range(17)] for _ in range(3)]
        shear = [[zero for _ in range(17)] for _ in range(2)]
        for node in range(3):
            base = 5 * node
            membrane[0][base] = dx[node]
            membrane[1][base + 1] = dy[node]
            membrane[2][base] = dy[node]
            membrane[2][base + 1] = dx[node]
            bending[0][base + 4] = dx[node]
            bending[1][base + 3] = -dy[node]
            bending[2][base + 4] = dy[node]
            bending[2][base + 3] = -dx[node]
            shear[0][base + 2] = dx[node]
            shear[0][base + 4] = shape[node]
            shear[1][base + 2] = dy[node]
            shear[1][base + 3] = -shape[node]
        bending[0][16] = bx
        bending[1][15] = -by
        bending[2][16] = by
        bending[2][15] = -bx
        shear[0][16] = bubble
        shear[1][15] = -bubble
        return membrane, bending, shear

    jacobian = [[one, zero], [a, b]]
    exact_points = {
        name: (Fraction.from_float(r), Fraction.from_float(s))
        for name, (r, s) in TYING_POINTS.items()
    }
    samples: dict[str, list[list[Laurent]]] = {}
    for name, point in exact_points.items():
        shear = compatible(*point)[2]
        samples[name] = [
            [sum((jacobian[row][inner] * shear[inner][column] for inner in range(2)), zero) for column in range(17)]
            for row in range(2)
        ]

    def assumed(r: Fraction, s: Fraction) -> list[list[Laurent]]:
        cr = [
            SHEAR_TWO_THIRDS_BINARY64
            * (samples["B"][0][column] - Fraction(1, 2) * samples["B"][1][column])
            + SHEAR_ONE_THIRD_BINARY64
            * (samples["C"][0][column] + samples["C"][1][column])
            for column in range(17)
        ]
        cs = [
            SHEAR_TWO_THIRDS_BINARY64
            * (samples["A"][1][column] - Fraction(1, 2) * samples["A"][0][column])
            + SHEAR_ONE_THIRD_BINARY64
            * (samples["C"][0][column] + samples["C"][1][column])
            for column in range(17)
        ]
        twist = [
            samples["F"][0][column] - samples["D"][0][column]
            - samples["F"][1][column] + samples["E"][1][column]
            for column in range(17)
        ]
        covariant = [
            [cr[column] + twist[column] * (3 * s - 1) / 3 for column in range(17)],
            [cs[column] + twist[column] * (1 - 3 * r) / 3 for column in range(17)],
        ]
        return [
            [sum((inverse[row][inner] * covariant[inner][column] for inner in range(2)), zero) for column in range(17)]
            for row in range(2)
        ]

    # Columns: tx, ty, tz, rx, ry, rz.  Bubble coordinates are zero.
    nodes = ((zero, zero), (one, zero), (a, b))
    rigid17 = [[zero for _ in range(6)] for _ in range(17)]
    rigid18 = [[zero for _ in range(6)] for _ in range(18)]
    for node, (x, y) in enumerate(nodes):
        p = 5 * node
        rigid17[p][0] = one
        rigid17[p + 1][1] = one
        rigid17[p + 2][2] = one
        rigid17[p + 2][3] = y
        rigid17[p + 2][4] = -x
        rigid17[p][5] = -y
        rigid17[p + 1][5] = x
        rigid17[p + 3][3] = one
        rigid17[p + 4][4] = one
        q = 6 * node
        for component in range(5):
            for mode in range(6):
                rigid18[q + component][mode] = rigid17[p + component][mode]
        rigid18[q + 5][5] = one

    nonzero_station_terms = 0
    exact_operators: list[list[list[Laurent]]] = []
    for r_float, s_float, _weight in SEVEN_POINT_RULE:
        r = Fraction.from_float(r_float)
        s = Fraction.from_float(s_float)
        membrane, bending, _shear = compatible(r, s)
        operator = membrane + bending + assumed(r, s)
        exact_operators.append(operator)
        for row in operator:
            for mode in range(6):
                value = sum((row[column] * rigid17[column][mode] for column in range(17)), zero)
                nonzero_station_terms += int(not value.is_zero)

    dx = (-one, one, zero)
    dy = ((a - one) * Laurent.monomial(0, -1), -a * Laurent.monomial(0, -1), Laurent.monomial(0, -1))
    constraint = [[zero for _ in range(18)] for _ in range(3)]
    for row in range(3):
        for node in range(3):
            constraint[row][6 * node] = Fraction(1, 2) * dy[node]
            constraint[row][6 * node + 1] = -Fraction(1, 2) * dx[node]
        constraint[row][6 * row + 5] = one
    nonzero_pl_terms = 0
    for row in constraint:
        for mode in range(6):
            value = sum((row[column] * rigid18[column][mode] for column in range(18)), zero)
            nonzero_pl_terms += int(not value.is_zero)

    physical_selected = [
        [exact_operators[station][component][column] for column in UNCONDENSED_QUOTIENT_INDICES]
        for station, component in SELECTED_PHYSICAL_ROWS
    ]
    total_selected: list[list[Laurent]] = []
    total_columns = TOTAL_QUOTIENT_INDICES + (18, 19)
    for station, component in SELECTED_PHYSICAL_ROWS:
        source = exact_operators[station][component]
        full = [zero for _ in range(20)]
        for physical_column, external_column in enumerate(PHYSICAL_EXTERNAL_INDICES):
            full[external_column] = source[physical_column]
        full[18] = source[15]
        full[19] = source[16]
        total_selected.append([full[column] for column in total_columns])
    for row in constraint:
        full = list(row) + [zero, zero]
        total_selected.append([full[column] for column in total_columns])

    expected_determinant = Laurent.monomial(
        0, -4, -SELECTED_MINOR_CONSTANT
    )
    physical_determinant = _laurent_determinant(physical_selected)
    total_determinant = _laurent_determinant(total_selected)

    def derived_constant(determinant: Laurent) -> Fraction | None:
        if len(determinant.terms) != 1:
            return None
        power, coefficient = determinant.terms[0]
        if power != (0, -4) or coefficient >= 0:
            return None
        return -coefficient

    physical_derived_constant = derived_constant(physical_determinant)
    total_derived_constant = derived_constant(total_determinant)

    return {
        "derived_physical_selected_minor_constant": (
            [
                physical_derived_constant.numerator,
                physical_derived_constant.denominator,
            ]
            if physical_derived_constant is not None
            else None
        ),
        "derived_total_selected_minor_constant": (
            [
                total_derived_constant.numerator,
                total_derived_constant.denominator,
            ]
            if total_derived_constant is not None
            else None
        ),
        "physical_selected_minor_identity": physical_determinant == expected_determinant,
        "physical_rigid_identity": nonzero_station_terms == 0,
        "pl_rigid_identity": nonzero_pl_terms == 0,
        "physical_rigid_nonzero_terms": nonzero_station_terms,
        "pl_rigid_nonzero_terms": nonzero_pl_terms,
        "rigid_dimension": 6,
        "rigid_pivot_policy": "NODE_1_SIX_COORDINATES_IDENTITY_V1",
        "selected_minor_constant": [
            SELECTED_MINOR_CONSTANT.numerator,
            SELECTED_MINOR_CONSTANT.denominator,
        ],
        "selected_minor_determinant": "-C/B_POWER_4",
        "selected_minor_policy_id": SELECTED_MINOR_POLICY_ID,
        "total_selected_minor_identity": total_determinant == expected_determinant,
        "uncondensed_rigid_pivot_policy": "PHYSICAL_ROWS_0_1_2_3_4_6_V1",
    }


def run_certificate(*, max_depth: int = 20, max_processed: int = 10_000) -> dict[str, object]:
    if isinstance(max_depth, bool) or not isinstance(max_depth, int) or max_depth < 0:
        raise ValueError("max_depth must be a nonnegative integer")
    if isinstance(max_processed, bool) or not isinstance(max_processed, int) or max_processed <= 0:
        raise ValueError("max_processed must be a positive integer")
    exact = _exact_rigid_identity()
    analytic_failures = sorted(
        key
        for key in (
            "physical_rigid_identity",
            "pl_rigid_identity",
            "physical_selected_minor_identity",
            "total_selected_minor_identity",
        )
        if exact.get(key) is not True
    )
    pending = [] if analytic_failures else [ROOT]
    leaves: list[Box] = []
    positive_results: list[dict[str, object]] = []
    unresolved_results: list[tuple[Box, dict[str, object]]] = (
        [
            (
                ROOT,
                {
                    "classification": "UNRESOLVED",
                    "reason": "EXACT_ANALYTIC_IDENTITY_FAILED",
                },
            )
        ]
        if analytic_failures
        else []
    )
    if analytic_failures:
        leaves.append(ROOT)
    processed = 0
    maximum_depth = 0
    reason_counts: dict[str, int] = {}
    while pending and processed < max_processed:
        box = pending.pop()
        processed += 1
        maximum_depth = max(maximum_depth, box.depth)
        result = _evaluate_box(box)
        if result["classification"] == "POSITIVE":
            leaves.append(box)
            positive_results.append(result)
        elif box.depth < max_depth:
            left, right = box.split()
            pending.append(right)
            pending.append(left)
        else:
            leaves.append(box)
            unresolved_results.append((box, result))
            reason = str(result["reason"])
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
    if pending:
        leaves.extend(pending)
        for box in pending:
            result = {"classification": "UNRESOLVED", "reason": "MAX_PROCESSED_EXHAUSTED"}
            unresolved_results.append((box, result))
        reason_counts["MAX_PROCESSED_EXHAUSTED"] = len(pending)
    _verify_partition(leaves)

    if analytic_failures:
        reason_counts["EXACT_ANALYTIC_IDENTITY_FAILED"] = len(analytic_failures)
    complete = (
        not unresolved_results
        and bool(positive_results)
        and not analytic_failures
    )
    minimum_quotient = min(
        (float(result["quotient_lower"]) for result in positive_results),
        default=0.0,
    )
    minimum_bubble = min(
        (float(result["bubble_lower"]) for result in positive_results),
        default=0.0,
    )
    minimum_uncondensed = min(
        (float(result["uncondensed_lower"]) for result in positive_results),
        default=0.0,
    )
    minimum_condensed = min(
        (float(result["condensed_lower"]) for result in positive_results),
        default=0.0,
    )
    minimum_longest_quotient = (
        _down(minimum_quotient / 25.0) if minimum_quotient > 0.0 else 0.0
    )
    first_unresolved = (
        {
            "box": unresolved_results[0][0].record(),
            "reason": unresolved_results[0][1]["reason"],
        }
        if unresolved_results and not analytic_failures
        else (
            {
                "analytic_failures": analytic_failures,
                "reason": "EXACT_ANALYTIC_IDENTITY_FAILED",
            }
            if analytic_failures
            else None
        )
    )
    return {
        "admission": {
            "complete_envelope_bound": True,
            "envelope_id": ADMISSION_ENVELOPE_ID,
            "exact_constraints": {
                "connectivity_signs_mapped_to_positive_gauge": [-1, 1],
                "edge_ratio_maximum": [4, 1],
                "maximum_angle_degrees": [150, 1],
                "minimum_angle_degrees": [30, 1],
                "minimum_corner_scaled_jacobian": [1, 5],
                "minimum_normalized_area": [3, 5],
                "minimum_normalized_twice_area": "MAX_64_BINARY64_EPSILON_AND_1E_MINUS_14",
                "owner_normal_reorientation": True,
                "production_coordinate_gauge": (
                    "DIRECTED_EDGE_01_EQUALS_ONE_WITHOUT_CONNECTIVITY_RELABELING"
                ),
            },
            "proof_derivation_margin_binary64_ratio": _ratio(1.0e-12),
            "root_superset": ROOT.record(),
            "root_superset_derivation": (
                "EDGE_RATIO_LE_4_PLUS_CONSERVATIVE_PROOF_MARGIN_IMPLIES_"
                "LMAX_OVER_L01_LT_5_ABS_A_LT_5_AND_B_LT_5;"
                "NORMALIZED_AREA_IN_LONGEST_LENGTH_SCALE_IMPLIES_B_LONGEST_"
                "GT_1_OVER_6_AND_B_EDGE01_EQUALS_B_LONGEST_OVER_C_GT_1_OVER_6"
            ),
        },
        "algebraic_reductions": {
            "condensed_lower_bound": (
                "MIN_ALPHA_ENERGY_Y_ALPHA_GE_MU_MIN_ALPHA_"
                "NORM_Y_ALPHA_SQUARED_GE_MU_NORM_Y_SQUARED"
            ),
            "minor_to_singular_value": (
                "SIGMA_MIN_SELECTED_GE_ABS_DET_SELECTED_OVER_"
                "FROBENIUS_NORM_POWER_DIMENSION_MINUS_ONE"
            ),
            "saddle_inertia": (
                "CONGRUENT_TO_TOTAL_UNCONDENSED_POSITIVE_BLOCK_DIRECT_SUM_"
                "NEGATIVE_M_OVER_KD"
            ),
        },
        "analytic_identities": exact,
        "classification": "CERTIFIED_COMPLETE" if complete else "UNRESOLVED",
        "constitutive_scaling": {
            "baseline_drill_scale": [1, 2],
            "baseline_generalized_section": "IDENTITY_8",
            "bubble_minimization_monotonicity": True,
            "drill_bound_derivation": (
                "A_GE_LAMBDA_MIN_D_I3_AND_PTP_GE_G_IMPLIES_KD_GE_LAMBDA_MIN_D_OVER_2"
            ),
            "id": CONSTITUTIVE_SCALING_ID,
            "strict_positive_generalized_section_required": True,
        },
        "cover": {
            "leaf_partition_sha256": _partition_hash(leaves),
            "maximum_depth": maximum_depth,
            "partition_policy_id": PARTITION_POLICY_ID,
            "positive_leaf_count": len(positive_results),
            "processed_count": processed,
            "reason_counts": dict(sorted(reason_counts.items())),
            "unresolved_leaf_count": len(unresolved_results),
        },
        "first_unresolved": first_unresolved,
        "formulation_id": FORMULATION_ID,
        "formulation_input_authority": (
            "IMPLEMENTED_BINARY64_TYING_OFFSET_TYING_COORDINATES_ASSUMED_"
            "SHEAR_INTERPOLATION_COEFFICIENTS_STATION_COORDINATES_AND_"
            "QUADRATURE_WEIGHTS_FROZEN_AS_EXACT_ALGEBRAIC_INPUTS_WITH_NO_"
            "IDEAL_DECIMAL_OR_RATIONAL_SUBSTITUTION_V1"
        ),
        "frozen_binary64_input_sha256": hashlib.sha256(
            _canonical_bytes(_binary64_input_record())
        ).hexdigest().upper(),
        "implementation_id": IMPLEMENTATION_ID,
        "longest_edge_metric_equivalence": {
            "area_and_pl_gram_scale": "AREA_L_AND_M_L_EQUAL_C_SQUARED_TIMES_EDGE01_VALUES",
            "dof_map": (
                "T_EQUALS_DIAG_C_I_TRANSLATIONS_I_ROTATIONS_I_BUBBLES_I_DRILLS"
            ),
            "edge_ratio_scale": {
                "c_definition": "L01_OVER_LMAX",
                "c_lower_open": [1, 5],
                "c_upper_closed": [1, 1],
            },
            "kinematic_identity": (
                "B_L_T_EQUALS_DIAG_I_MEMBRANE_C_INVERSE_I_BENDING_I_SHEAR_"
                "TIMES_B_EDGE01"
            ),
            "longest_metric_id": LONGEST_EDGE_QUOTIENT_METRIC_ID,
            "minimum_baseline_total_eigenvalue_lower_ratio": _ratio(
                minimum_longest_quotient
            ),
            "pl_constraint_identity": "C_L_T_EQUALS_C_EDGE01",
            "quotient_distance_inequality": (
                "C_TIMES_DIST_EDGE01_LE_DIST_LONGEST_OF_TQ_LE_DIST_EDGE01"
            ),
            "rigid_space_map": "T_MAPS_EDGE01_RIGID_SPACE_BIJECTIVELY_TO_LONGEST_RIGID_SPACE",
            "transferred_lower_bound": "LONGEST_BASELINE_LOWER_GE_EDGE01_BASELINE_LOWER_OVER_25",
        },
        "outward_policy_id": OUTWARD_POLICY_ID,
        "proof_obligations": {
            "bubble_spd": complete,
            "condensed_physical_rank": 9 if complete else None,
            "full_saddle_inertia": [14, 3, 6] if complete else None,
            "full_saddle_rank": 17 if complete else None,
            "physical_uncondensed_rank": 11 if complete else None,
            "pl_rank": 3 if complete else None,
            "rigid_modes": 6 if complete else None,
            "schur_complement_spd_on_physical_quotient": complete,
            "strictly_positive_quotient_lower_bound": complete,
            "total_uncondensed_rank": 14 if complete else None,
            "total_rank": 12 if complete else None,
        },
        "quotient": {
            "metric_id": QUOTIENT_METRIC_ID,
            "metric_reduction": (
                "FIX_NODE_1_COORDINATES;STANDARD_COORDINATE_COMPLEMENT_NORM_"
                "UPPER_BOUNDS_EUCLIDEAN_DISTANCE_TO_RIGID_KERNEL"
            ),
            "minimum_baseline_bubble_eigenvalue_lower_ratio": _ratio(minimum_bubble),
            "minimum_baseline_condensed_physical_eigenvalue_lower_ratio": _ratio(minimum_condensed),
            "minimum_baseline_total_eigenvalue_lower_ratio": _ratio(minimum_quotient),
            "minimum_baseline_uncondensed_eigenvalue_lower_ratio": _ratio(minimum_uncondensed),
            "scale_statement": (
                "QFORM_D_Q_GE_LAMBDA_MIN_D_TIMES_BOUND_TIMES_"
                "EUCLIDEAN_DISTANCE_SQUARED_TO_RIGID_KERNEL"
            ),
        },
        "reference_surface_offset": {
            "baseline_numeric_lower_bound_offset": [0, 1],
            "finite_offset_composition": (
                "INVERTIBLE_REFERENCE_SURFACE_STRAIN_AND_DOF_CONGRUENCE_"
                "PRESERVES_RANK_INERTIA_AND_POSITIVE_SEMIDEFINITENESS"
            ),
            "offset_uniform_euclidean_lower_bound": False,
            "scope": (
                "STRICT_COERCIVITY_EXTENDS_POINTWISE_TO_EACH_FINITE_OFFSET;"
                "NO_UNIFORM_CONSTANT_IS_CLAIMED_OVER_AN_UNBOUNDED_OFFSET_PARAMETER"
            ),
        },
        "schema": SCHEMA,
    }


def write_certificate(path: Path, *, max_depth: int, max_processed: int) -> bytes:
    payload = run_certificate(max_depth=max_depth, max_processed=max_processed)
    encoded = _canonical_bytes(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(encoded)
    return encoded


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-depth", type=int, default=20)
    parser.add_argument("--max-processed", type=int, default=10_000)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    encoded = write_certificate(
        arguments.output,
        max_depth=arguments.max_depth,
        max_processed=arguments.max_processed,
    )
    print(
        json.dumps(
            {
                "bytes": len(encoded),
                "output": str(arguments.output),
                "sha256": hashlib.sha256(encoded).hexdigest().upper(),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "ADMISSION_ENVELOPE_ID",
    "Box",
    "IMPLEMENTATION_ID",
    "Interval",
    "ROOT",
    "SCHEMA",
    "run_certificate",
    "write_certificate",
]
