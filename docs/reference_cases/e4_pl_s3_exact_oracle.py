"""Standard-library exact oracle for one rational flat S3 formulation slice.

The oracle is independently authored and does not import the production
element or the binary64 reference.  It evaluates every algebraic operation in
``fractions.Fraction`` after binding the frozen binary64 quadrature and tying
coordinates as exact rational inputs.  Its admitted scope is rational local
geometry, a positive rational generalized-section matrix, and an isotropic
membrane block (so the selected generalized-eigenvalue drill scale is exactly
``A66``).

This closes an exact local cancellation/rank witness.  It is deliberately not
the still-required interval proof over the complete admitted triangle domain.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, Sequence


ORACLE_IMPLEMENTATION_ID = "INDEPENDENT_STDLIB_FRACTION_MITC3_PLUS_V1"
F = Fraction


def _f64(text: str) -> Fraction:
    """Bind the exact binary64 value created from a frozen decimal literal."""

    return Fraction(float(text))


TYING_POINTS = {
    "A": (Fraction(1, 6), Fraction(2, 3)),
    "B": (Fraction(2, 3), Fraction(1, 6)),
    "C": (Fraction(1, 6), Fraction(1, 6)),
    "D": (Fraction(1.0 / 3.0 + 1.0e-4), Fraction(1.0 / 3.0 - 2.0e-4)),
    "E": (Fraction(1.0 / 3.0 - 2.0e-4), Fraction(1.0 / 3.0 + 1.0e-4)),
    "F": (Fraction(1.0 / 3.0 + 1.0e-4), Fraction(1.0 / 3.0 + 1.0e-4)),
}

SEVEN_POINT_RULE = (
    (Fraction(1, 3), Fraction(1, 3), _f64("0.1125")),
    (_f64("0.470142064105115"), _f64("0.470142064105115"), _f64("0.066197076394253")),
    (_f64("0.059715871789770"), _f64("0.470142064105115"), _f64("0.066197076394253")),
    (_f64("0.470142064105115"), _f64("0.059715871789770"), _f64("0.066197076394253")),
    (_f64("0.101286507323456"), _f64("0.101286507323456"), _f64("0.062969590272414")),
    (_f64("0.797426985353087"), _f64("0.101286507323456"), _f64("0.062969590272414")),
    (_f64("0.101286507323456"), _f64("0.797426985353087"), _f64("0.062969590272414")),
)

Matrix = list[list[Fraction]]
PHYSICAL_EXTERNAL_INDICES = tuple(
    6 * node + component for node in range(3) for component in range(5)
)


@dataclass(frozen=True)
class ExactOracleBlocks:
    uncondensed_physical: Matrix
    bubble_block: Matrix
    bubble_map: Matrix
    condensed_physical_15: Matrix
    physical_local_18: Matrix
    pl_constraint: Matrix
    pl_multiplier_gram: Matrix
    pl_local_18: Matrix
    total_local_18: Matrix
    full_saddle_23: Matrix
    k_d: Fraction
    ranks: dict[str, int]


def _fraction(value: object) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        raise TypeError("boolean is not an exact scalar")
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, str):
        return Fraction(value)
    raise TypeError("exact oracle inputs must be int, Fraction, or rational string")


def _matrix(values: Sequence[Sequence[object]], rows: int, columns: int, name: str) -> Matrix:
    result = [[_fraction(value) for value in row] for row in values]
    if len(result) != rows or any(len(row) != columns for row in result):
        raise ValueError(f"{name} must be {rows}x{columns}")
    return result


def _zeros(rows: int, columns: int) -> Matrix:
    return [[Fraction(0) for _ in range(columns)] for _ in range(rows)]


def _identity(size: int) -> Matrix:
    result = _zeros(size, size)
    for index in range(size):
        result[index][index] = Fraction(1)
    return result


def _transpose(matrix: Matrix) -> Matrix:
    return [list(column) for column in zip(*matrix)]


def _add(left: Matrix, right: Matrix) -> Matrix:
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        raise ValueError("matrix add shape mismatch")
    return [[a + b for a, b in zip(row_a, row_b)] for row_a, row_b in zip(left, right)]


def _scale(value: Fraction, matrix: Matrix) -> Matrix:
    return [[value * item for item in row] for row in matrix]


def _multiply(left: Matrix, right: Matrix) -> Matrix:
    if not left or not right or len(left[0]) != len(right):
        raise ValueError("matrix multiply shape mismatch")
    transposed = _transpose(right)
    return [
        [sum((a * b for a, b in zip(row, column)), Fraction(0)) for column in transposed]
        for row in left
    ]


def _submatrix(matrix: Matrix, rows: Iterable[int], columns: Iterable[int]) -> Matrix:
    row_ids = tuple(rows)
    column_ids = tuple(columns)
    return [[matrix[row][column] for column in column_ids] for row in row_ids]


def _solve(left: Matrix, right: Matrix) -> Matrix:
    size = len(left)
    columns = len(right[0]) if right else 0
    if size == 0 or any(len(row) != size for row in left) or len(right) != size:
        raise ValueError("exact solve requires square compatible matrices")
    augmented = [list(a) + list(b) for a, b in zip(left, right)]
    for pivot_column in range(size):
        pivot_row = next(
            (row for row in range(pivot_column, size) if augmented[row][pivot_column]),
            None,
        )
        if pivot_row is None:
            raise ValueError("exact solve matrix is singular")
        augmented[pivot_column], augmented[pivot_row] = augmented[pivot_row], augmented[pivot_column]
        pivot = augmented[pivot_column][pivot_column]
        augmented[pivot_column] = [value / pivot for value in augmented[pivot_column]]
        for row in range(size):
            if row == pivot_column:
                continue
            factor = augmented[row][pivot_column]
            if factor:
                augmented[row] = [
                    value - factor * pivot_value
                    for value, pivot_value in zip(augmented[row], augmented[pivot_column])
                ]
    return [row[size : size + columns] for row in augmented]


def exact_rank(matrix: Matrix) -> int:
    work = [list(row) for row in matrix]
    if not work:
        return 0
    rows = len(work)
    columns = len(work[0])
    rank = 0
    for column in range(columns):
        pivot = next((row for row in range(rank, rows) if work[row][column]), None)
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        pivot_value = work[rank][column]
        work[rank] = [value / pivot_value for value in work[rank]]
        for row in range(rows):
            if row == rank:
                continue
            factor = work[row][column]
            if factor:
                work[row] = [
                    value - factor * pivot_item
                    for value, pivot_item in zip(work[row], work[rank])
                ]
        rank += 1
        if rank == rows:
            break
    return rank


def _geometry(local_nodes: Sequence[Sequence[object]]) -> tuple[Matrix, Matrix, Fraction]:
    local = _matrix(local_nodes, 3, 2, "local_nodes")
    jacobian = [
        [local[1][0] - local[0][0], local[1][1] - local[0][1]],
        [local[2][0] - local[0][0], local[2][1] - local[0][1]],
    ]
    determinant = jacobian[0][0] * jacobian[1][1] - jacobian[0][1] * jacobian[1][0]
    if not determinant:
        raise ValueError("local_nodes define a singular triangle")
    inverse = [
        [jacobian[1][1] / determinant, -jacobian[0][1] / determinant],
        [-jacobian[1][0] / determinant, jacobian[0][0] / determinant],
    ]
    return local, inverse, determinant


def _compatible(inverse: Matrix, r: Fraction, s: Fraction) -> tuple[Matrix, Matrix, Matrix]:
    derivative_r = (Fraction(-1), Fraction(1), Fraction(0))
    derivative_s = (Fraction(-1), Fraction(0), Fraction(1))
    derivative_x = tuple(inverse[0][0] * a + inverse[0][1] * b for a, b in zip(derivative_r, derivative_s))
    derivative_y = tuple(inverse[1][0] * a + inverse[1][1] * b for a, b in zip(derivative_r, derivative_s))
    shape = (Fraction(1) - r - s, r, s)
    bubble = Fraction(27) * r * s * (Fraction(1) - r - s)
    bubble_r = Fraction(27) * s * (Fraction(1) - 2 * r - s)
    bubble_s = Fraction(27) * r * (Fraction(1) - r - 2 * s)
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


def _assumed_shear(jacobian: Matrix, inverse: Matrix, r: Fraction, s: Fraction) -> Matrix:
    samples = {
        name: _multiply(jacobian, _compatible(inverse, *point)[2])
        for name, point in TYING_POINTS.items()
    }
    constant_r = [
        Fraction(2, 3) * (samples["B"][0][column] - Fraction(1, 2) * samples["B"][1][column])
        + Fraction(1, 3) * (samples["C"][0][column] + samples["C"][1][column])
        for column in range(17)
    ]
    constant_s = [
        Fraction(2, 3) * (samples["A"][1][column] - Fraction(1, 2) * samples["A"][0][column])
        + Fraction(1, 3) * (samples["C"][0][column] + samples["C"][1][column])
        for column in range(17)
    ]
    twisting = [
        samples["F"][0][column] - samples["D"][0][column]
        - samples["F"][1][column] + samples["E"][1][column]
        for column in range(17)
    ]
    covariant = [
        [constant_r[column] + twisting[column] * (3 * s - 1) / 3 for column in range(17)],
        [constant_s[column] + twisting[column] * (1 - 3 * r) / 3 for column in range(17)],
    ]
    return _multiply(inverse, covariant)


def _kinematic(jacobian: Matrix, inverse: Matrix, r: Fraction, s: Fraction) -> Matrix:
    membrane, bending, _shear = _compatible(inverse, r, s)
    return membrane + bending + _assumed_shear(jacobian, inverse, r, s)


def _isotropic_drill_scale(membrane: Matrix) -> Fraction:
    if membrane[0][0] != membrane[1][1] or membrane[0][1] != membrane[1][0]:
        raise ValueError("exact oracle membrane block must be isotropic")
    if any(membrane[row][column] for row, column in ((0, 2), (1, 2), (2, 0), (2, 1))):
        raise ValueError("exact oracle membrane block must be isotropic")
    expected = (membrane[0][0] - membrane[0][1]) / 2
    if membrane[2][2] != expected or expected <= 0:
        raise ValueError("exact oracle isotropic membrane block must be positive")
    return expected


def reconstruct_exact_blocks(
    local_nodes: Sequence[Sequence[object]],
    constitutive: Sequence[Sequence[object]],
    *,
    director_polarity: int = 1,
) -> ExactOracleBlocks:
    """Return exact local physical, PL, and saddle blocks."""

    local, inverse, determinant = _geometry(local_nodes)
    del local
    section = _matrix(constitutive, 8, 8, "constitutive")
    if section != _transpose(section):
        raise ValueError("constitutive must be symmetric")
    if director_polarity not in (-1, 1):
        raise ValueError("director_polarity must be -1 or +1")
    jacobian = _solve(inverse, _identity(2))
    reversal = _identity(8)
    for index in range(3, 8):
        reversal[index][index] = Fraction(director_polarity)

    uncondensed = _zeros(17, 17)
    for r, s, weight in SEVEN_POINT_RULE:
        operator = _multiply(reversal, _kinematic(jacobian, inverse, r, s))
        term = _multiply(_transpose(operator), _multiply(section, operator))
        uncondensed = _add(uncondensed, _scale(abs(determinant) * weight, term))
    uncondensed = _scale(Fraction(1, 2), _add(uncondensed, _transpose(uncondensed)))
    bubble = _submatrix(uncondensed, (15, 16), (15, 16))
    coupling = _submatrix(uncondensed, range(15), (15, 16))
    bubble_map = _scale(Fraction(-1), _solve(bubble, _transpose(coupling)))
    condensed = _add(
        _submatrix(uncondensed, range(15), range(15)),
        _multiply(coupling, bubble_map),
    )
    condensed = _scale(Fraction(1, 2), _add(condensed, _transpose(condensed)))
    physical = _zeros(18, 18)
    for out_row, row in enumerate(PHYSICAL_EXTERNAL_INDICES):
        for out_column, column in enumerate(PHYSICAL_EXTERNAL_INDICES):
            physical[row][column] = condensed[out_row][out_column]

    k_d = _isotropic_drill_scale(_submatrix(section, range(3), range(3)))
    derivative_r = (Fraction(-1), Fraction(1), Fraction(0))
    derivative_s = (Fraction(-1), Fraction(0), Fraction(1))
    derivative_x = tuple(inverse[0][0] * a + inverse[0][1] * b for a, b in zip(derivative_r, derivative_s))
    derivative_y = tuple(inverse[1][0] * a + inverse[1][1] * b for a, b in zip(derivative_r, derivative_s))
    constraint = _zeros(3, 18)
    for row in range(3):
        for node in range(3):
            constraint[row][6 * node] = derivative_y[node] / 2
            constraint[row][6 * node + 1] = -derivative_x[node] / 2
        constraint[row][6 * row + 5] = Fraction(1)
    gram_numerator = [[Fraction(value) for value in row] for row in ((2, 1, 1), (1, 2, 1), (1, 1, 2))]
    gram = _scale(abs(determinant) / 24, gram_numerator)
    pl = _scale(k_d, _multiply(_transpose(constraint), _multiply(gram, constraint)))
    total = _add(physical, pl)

    embedded = _zeros(20, 20)
    combined = PHYSICAL_EXTERNAL_INDICES + (18, 19)
    for out_row, row in enumerate(combined):
        for out_column, column in enumerate(combined):
            embedded[row][column] = uncondensed[out_row][out_column]
    multiplier = _zeros(20, 3)
    qt = _multiply(_transpose(constraint), gram)
    for row in range(18):
        multiplier[row] = qt[row]
    saddle = _zeros(23, 23)
    for row in range(20):
        for column in range(20):
            saddle[row][column] = embedded[row][column]
        for column in range(3):
            saddle[row][20 + column] = multiplier[row][column]
            saddle[20 + column][row] = multiplier[row][column]
    negative_gram = _scale(-Fraction(1, 1) / k_d, gram)
    for row in range(3):
        for column in range(3):
            saddle[20 + row][20 + column] = negative_gram[row][column]

    ranks = {
        "bubble": exact_rank(bubble),
        "condensed_physical_15": exact_rank(condensed),
        "embedded_physical_18": exact_rank(physical),
        "full_saddle_23": exact_rank(saddle),
        "pl": exact_rank(pl),
        "total_18": exact_rank(total),
        "uncondensed_physical_17": exact_rank(uncondensed),
    }
    return ExactOracleBlocks(
        uncondensed_physical=uncondensed,
        bubble_block=bubble,
        bubble_map=bubble_map,
        condensed_physical_15=condensed,
        physical_local_18=physical,
        pl_constraint=constraint,
        pl_multiplier_gram=gram,
        pl_local_18=pl,
        total_local_18=total,
        full_saddle_23=saddle,
        k_d=k_d,
        ranks=ranks,
    )


def to_float_matrix(matrix: Matrix) -> list[list[float]]:
    return [[float(value) for value in row] for row in matrix]


__all__ = [
    "ExactOracleBlocks",
    "ORACLE_IMPLEMENTATION_ID",
    "exact_rank",
    "reconstruct_exact_blocks",
    "to_float_matrix",
]
