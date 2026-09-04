"""Independent exact checker for the two-cell mixed GE-beam macroelement.

This module deliberately reconstructs the reference-linear operator from the
mixed potential, rather than importing either production beam mechanics or the
separately authored reference builder.  All algebra used for classification is
performed over :class:`fractions.Fraction`.

The reconstruction is the linearization of Humer--Steinbrecher--Pechstein
equations (30)--(31), (43)--(46) for two adjacent, lowest-order cells.  Each
cell has a P1 centreline, a P1 material-moment field, a P0 element rotation,
and hybrid rotations at its vertices.  The public macroelement therefore has
three vertices with six external coordinates each; its two P1 moment fields
and two P0 rotation fields supply eighteen local coordinates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from fractions import Fraction
from pathlib import Path
from typing import Iterable, Sequence


SCHEMA = "anysolver.ge-beam3-dc-mixed-independent-check-v1"
CANDIDATE_ID = "CANDIDATE_GE_BEAM3_DC_MIXED_K1_MACRO_V2"
STUDY_ID = "study_ge_beam3.dc_mixed_k1_macro_v2"

F = Fraction
Matrix = list[list[Fraction]]
CELL_LENGTH = F(1, 2)


def _q(value: int | str | Fraction) -> Fraction:
    return value if isinstance(value, Fraction) else F(value)


def _zeros(rows: int, columns: int) -> Matrix:
    return [[F(0) for _ in range(columns)] for _ in range(rows)]


def _identity(size: int) -> Matrix:
    result = _zeros(size, size)
    for index in range(size):
        result[index][index] = F(1)
    return result


def _transpose(matrix: Sequence[Sequence[Fraction]]) -> Matrix:
    if not matrix:
        return []
    return [list(column) for column in zip(*matrix)]


def _matmul(
    left: Sequence[Sequence[Fraction]], right: Sequence[Sequence[Fraction]]
) -> Matrix:
    if not left or not right:
        return []
    right_t = _transpose(right)
    return [
        [sum((a * b for a, b in zip(row, column)), F(0)) for column in right_t]
        for row in left
    ]


def _matsub(
    left: Sequence[Sequence[Fraction]], right: Sequence[Sequence[Fraction]]
) -> Matrix:
    return [
        [a - b for a, b in zip(left_row, right_row)]
        for left_row, right_row in zip(left, right)
    ]


def _matrix_equal(
    left: Sequence[Sequence[Fraction]], right: Sequence[Sequence[Fraction]]
) -> bool:
    return len(left) == len(right) and all(
        len(a) == len(b) and all(x == y for x, y in zip(a, b))
        for a, b in zip(left, right)
    )


def _rank(matrix: Sequence[Sequence[Fraction]]) -> int:
    work = [list(row) for row in matrix]
    if not work:
        return 0
    rows = len(work)
    columns = len(work[0])
    pivot_row = 0
    for column in range(columns):
        pivot = next(
            (row for row in range(pivot_row, rows) if work[row][column]), None
        )
        if pivot is None:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        scale = work[pivot_row][column]
        work[pivot_row] = [value / scale for value in work[pivot_row]]
        for row in range(rows):
            if row == pivot_row or not work[row][column]:
                continue
            factor = work[row][column]
            work[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(work[row], work[pivot_row])
            ]
        pivot_row += 1
        if pivot_row == rows:
            break
    return pivot_row


def _inverse(matrix: Sequence[Sequence[Fraction]]) -> Matrix:
    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise ValueError("inverse requires a nonempty square matrix")
    work = [list(row) + identity_row for row, identity_row in zip(matrix, _identity(size))]
    for column in range(size):
        pivot = next((row for row in range(column, size) if work[row][column]), None)
        if pivot is None:
            raise ValueError("matrix is singular")
        work[column], work[pivot] = work[pivot], work[column]
        scale = work[column][column]
        work[column] = [value / scale for value in work[column]]
        for row in range(size):
            if row == column or not work[row][column]:
                continue
            factor = work[row][column]
            work[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(work[row], work[column])
            ]
    return [row[size:] for row in work]


def _ldl(matrix: Sequence[Sequence[Fraction]]) -> tuple[Matrix, list[Fraction]]:
    """Return a deterministic no-pivot LDL^T factorization."""

    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise ValueError("LDL requires a nonempty square matrix")
    if not _matrix_equal(matrix, _transpose(matrix)):
        raise ValueError("LDL requires a symmetric matrix")
    lower = _identity(size)
    diagonal: list[Fraction] = []
    for row in range(size):
        pivot = matrix[row][row] - sum(
            (lower[row][k] * lower[row][k] * diagonal[k] for k in range(row)),
            F(0),
        )
        if pivot == 0:
            raise ValueError("zero pivot in no-pivot LDL")
        diagonal.append(pivot)
        for below in range(row + 1, size):
            numerator = matrix[below][row] - sum(
                (
                    lower[below][k] * lower[row][k] * diagonal[k]
                    for k in range(row)
                ),
                F(0),
            )
            lower[below][row] = numerator / pivot
    return lower, diagonal


def _ldl_reconstruction(lower: Matrix, diagonal: Sequence[Fraction]) -> Matrix:
    weighted = [
        [lower[row][column] * diagonal[column] for column in range(len(diagonal))]
        for row in range(len(lower))
    ]
    return _matmul(weighted, _transpose(lower))


def _fraction_text(value: Fraction) -> str:
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def _matrix_payload(matrix: Sequence[Sequence[Fraction]]) -> list[list[str]]:
    return [[_fraction_text(value) for value in row] for row in matrix]


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("ascii")


def _digest_matrix(matrix: Sequence[Sequence[Fraction]]) -> str:
    return hashlib.sha256(_canonical_bytes(_matrix_payload(matrix))).hexdigest().upper()


def _block(
    matrix: Sequence[Sequence[Fraction]],
    row_start: int,
    row_stop: int,
    column_start: int,
    column_stop: int,
) -> Matrix:
    return [list(row[column_start:column_stop]) for row in matrix[row_start:row_stop]]


def _diag(values: Sequence[Fraction]) -> Matrix:
    result = _zeros(len(values), len(values))
    for index, value in enumerate(values):
        result[index][index] = value
    return result


def _block_diag(left: Matrix, right: Matrix) -> Matrix:
    result = _zeros(len(left) + len(right), len(left[0]) + len(right[0]))
    for row, values in enumerate(left):
        result[row][: len(values)] = values
    for row, values in enumerate(right):
        result[len(left) + row][len(left[0]) :] = values
    return result


def default_section() -> Matrix:
    """Return a rational SPD section with genuine force--moment coupling."""

    # This is written explicitly, rather than sharing the reference builder's
    # Cholesky construction.  Its nonzero off-diagonal 3 by 3 block exercises
    # the partial Legendre transform instead of silently assuming B=0.
    return [
        [F(4), F(2), F(0), F(2), F(0), F(0)],
        [F(2), F(10), F(3), F(1), F(3), F(0)],
        [F(0), F(3), F(5), F(0), F(1), F(2)],
        [F(2), F(1), F(0), F(10), F(3), F(0)],
        [F(0), F(3), F(1), F(3), F(6), F(2)],
        [F(0), F(0), F(2), F(0), F(2), F(6)],
    ]


def partial_legendre_blocks(section: Matrix) -> dict[str, Matrix]:
    """Compute the partial Legendre transform in the moment variables.

    For C=[[A,B],[B^T,D]], stationarity of

      1/2 gamma^T S gamma + gamma^T E M - 1/2 M^T F M + M^T kappa

    gives kappa=D^-1(M-B^T gamma), where F=D^-1,
    E=B D^-1 and S=A-B D^-1 B^T.  This supports a fully coupled SPD
    generalized section without pretending that its force and moment parts are
    uncoupled.
    """

    if len(section) != 6 or any(len(row) != 6 for row in section):
        raise ValueError("section must be 6 by 6")
    if not _matrix_equal(section, _transpose(section)):
        raise ValueError("section must be symmetric")
    lower, pivots = _ldl(section)
    if not _matrix_equal(_ldl_reconstruction(lower, pivots), section) or any(
        pivot <= 0 for pivot in pivots
    ):
        raise ValueError("section must be strictly positive definite")
    a = _block(section, 0, 3, 0, 3)
    b = _block(section, 0, 3, 3, 6)
    d = _block(section, 3, 6, 3, 6)
    f = _inverse(d)
    e = _matmul(b, f)
    s = _matsub(a, _matmul(e, _transpose(b)))
    return {"A": a, "B": b, "D": d, "F": f, "E": e, "S": s}


def _linear_form(size: int) -> list[Fraction]:
    return [F(0) for _ in range(size)]


def _cross_matrix(vector: Sequence[Fraction]) -> Matrix:
    x, y, z = vector
    return [[F(0), -z, y], [z, F(0), -x], [-y, x, F(0)]]


def _q_index(node: int, component: int) -> int:
    return 6 * node + component


def _local_index(cell: int, offset: int) -> int:
    return 18 + 9 * cell + offset


def _gamma_forms(cell: int, rotation: Matrix, mutation: str | None) -> Matrix:
    """Linearized material force strain for one half-length cell."""

    size = 36
    left_node, right_node = cell, cell + 1
    tangent = [rotation[row][0] for row in range(3)]
    tangent_cross = _cross_matrix(tangent)
    rotation_t = _transpose(rotation)
    forms = [_linear_form(size) for _ in range(3)]
    sign = F(-1) if mutation == "force_sign" and cell == 0 else F(1)
    for material in range(3):
        for spatial in range(3):
            component = rotation_t[material][spatial]
            forms[material][_q_index(right_node, spatial)] += (
                component / CELL_LENGTH
            )
            forms[material][_q_index(left_node, spatial)] -= (
                component / CELL_LENGTH
            )
            for phi_component in range(3):
                forms[material][_local_index(cell, phi_component)] += (
                    sign
                    * component
                    * tangent_cross[spatial][phi_component]
                )
    return forms


def _relative_rotation_forms(cell: int, node: int, rotation: Matrix) -> Matrix:
    """Linearized angle((Lambda_E)^T Lambda_V) in material coordinates."""

    size = 36
    rotation_t = _transpose(rotation)
    forms = [_linear_form(size) for _ in range(3)]
    for material in range(3):
        for spatial in range(3):
            component = rotation_t[material][spatial]
            forms[material][_q_index(node, 3 + spatial)] += component
            forms[material][_local_index(cell, spatial)] -= component
    return forms


def _moment_forms(cell: int, endpoint: str) -> Matrix:
    offset = 3 if endpoint == "left" else 6
    forms = [_linear_form(36) for _ in range(3)]
    for component in range(3):
        forms[component][_local_index(cell, offset + component)] = F(1)
    return forms


def _average_forms(left: Matrix, right: Matrix) -> Matrix:
    return [
        [(a + b) / 2 for a, b in zip(left_row, right_row)]
        for left_row, right_row in zip(left, right)
    ]


def _add_quadratic(
    hessian: Matrix,
    forms: Matrix,
    coefficient: Matrix,
    scale: Fraction = F(1),
) -> None:
    """Add the Hessian of scale/2 * forms^T coefficient forms."""

    dimension = len(hessian)
    for row in range(dimension):
        for column in range(dimension):
            value = F(0)
            for left_component in range(len(forms)):
                left_value = forms[left_component][row]
                if not left_value:
                    continue
                for right_component in range(len(forms)):
                    value += (
                        left_value
                        * coefficient[left_component][right_component]
                        * forms[right_component][column]
                    )
            hessian[row][column] += scale * value


def _add_cross(
    hessian: Matrix,
    left_forms: Matrix,
    coefficient: Matrix,
    right_forms: Matrix,
    scale: Fraction = F(1),
) -> None:
    """Add the Hessian of scale * left^T coefficient right."""

    dimension = len(hessian)
    for row in range(dimension):
        for column in range(dimension):
            value = F(0)
            for left_component in range(len(left_forms)):
                left_value = left_forms[left_component][row]
                if not left_value:
                    continue
                for right_component in range(len(right_forms)):
                    value += (
                        left_value
                        * coefficient[left_component][right_component]
                        * right_forms[right_component][column]
                    )
            hessian[row][column] += scale * value
            hessian[column][row] += scale * value


def _moment_mass(inverse_moment: Matrix, one_point: bool = False) -> Matrix:
    weights = (
        [[F(1, 4), F(1, 4)], [F(1, 4), F(1, 4)]]
        if one_point
        else [[F(1, 3), F(1, 6)], [F(1, 6), F(1, 3)]]
    )
    result = _zeros(6, 6)
    for endpoint_a in range(2):
        for endpoint_b in range(2):
            for row in range(3):
                for column in range(3):
                    result[3 * endpoint_a + row][3 * endpoint_b + column] = (
                        CELL_LENGTH
                        * weights[endpoint_a][endpoint_b]
                        * inverse_moment[row][column]
                    )
    return result


def build_mixed_hessian(
    section: Matrix,
    *,
    rotation: Matrix | None = None,
    mutation: str | None = None,
) -> Matrix:
    """Build the exact 36 by 36 mixed Hessian for two half-length cells."""

    rotation = _identity(3) if rotation is None else rotation
    blocks = partial_legendre_blocks(section)
    if mutation == "wrong_legendre_sign":
        blocks["E"] = [[-value for value in row] for row in blocks["E"]]
    hessian = _zeros(36, 36)
    for cell in range(2):
        gamma = _gamma_forms(cell, rotation, mutation)
        moment_left = _moment_forms(cell, "left")
        moment_right = _moment_forms(cell, "right")
        moment_average = _average_forms(moment_left, moment_right)
        _add_quadratic(hessian, gamma, blocks["S"], CELL_LENGTH)
        _add_cross(
            hessian, gamma, blocks["E"], moment_average, CELL_LENGTH
        )

        all_moments = moment_left + moment_right
        _add_quadratic(
            hessian,
            all_moments,
            _moment_mass(
                blocks["F"], one_point=mutation == "moment_one_point"
            ),
            F(-1),
        )

        left_relative = _relative_rotation_forms(cell, cell, rotation)
        right_relative = _relative_rotation_forms(cell, cell + 1, rotation)
        if not (mutation == "drop_middle_jump" and cell == 0):
            _add_cross(hessian, right_relative, _identity(3), moment_right)
        if not (mutation == "drop_middle_jump" and cell == 1):
            _add_cross(
                hessian, left_relative, _identity(3), moment_left, F(-1)
            )
    return hessian


def _schur_condense(hessian: Matrix) -> tuple[Matrix, Matrix, Matrix]:
    external = _block(hessian, 0, 18, 0, 18)
    coupling = _block(hessian, 0, 18, 18, 36)
    internal = _block(hessian, 18, 36, 18, 36)
    inverse_internal = _inverse(internal)
    condensed = _matsub(
        external,
        _matmul(_matmul(coupling, inverse_internal), _transpose(coupling)),
    )
    return condensed, internal, inverse_internal


def _rigid_modes() -> tuple[Matrix, Matrix]:
    external = _zeros(18, 6)
    full = _zeros(36, 6)
    positions = [F(0), F(1, 2), F(1)]
    for node, coordinate in enumerate(positions):
        for translation in range(3):
            external[_q_index(node, translation)][translation] = F(1)
        for rotation_component in range(3):
            column = 3 + rotation_component
            external[_q_index(node, 3 + rotation_component)][column] = F(1)
        # omega cross (x e1): omega_y gives -x e3; omega_z gives x e2.
        external[_q_index(node, 2)][4] = -coordinate
        external[_q_index(node, 1)][5] = coordinate
    for row in range(18):
        for column in range(6):
            full[row][column] = external[row][column]
    for cell in range(2):
        for rotation_component in range(3):
            full[_local_index(cell, rotation_component)][
                3 + rotation_component
            ] = F(1)
    return external, full


def _zero_matrix(rows: int, columns: int) -> Matrix:
    return _zeros(rows, columns)


def _deterministic_complement(rigid: Matrix) -> Matrix:
    """Use nonpivot rows of R as a deterministic quotient complement."""

    rigid_t = _transpose(rigid)
    work = [list(row) for row in rigid_t]
    pivot_columns: list[int] = []
    pivot_row = 0
    for column in range(len(rigid)):
        pivot = next(
            (row for row in range(pivot_row, 6) if work[row][column]), None
        )
        if pivot is None:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        scale = work[pivot_row][column]
        work[pivot_row] = [value / scale for value in work[pivot_row]]
        for row in range(6):
            if row == pivot_row or not work[row][column]:
                continue
            factor = work[row][column]
            work[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(work[row], work[pivot_row])
            ]
        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row == 6:
            break
    nonpivots = [index for index in range(18) if index not in pivot_columns]
    complement = _zeros(18, len(nonpivots))
    for column, row in enumerate(nonpivots):
        complement[row][column] = F(1)
    return complement


def _section_reversal(section: Matrix) -> tuple[Matrix, Matrix, Matrix]:
    proper_triad_change = _diag([F(-1), F(1), F(-1)])
    strain_change = [[-value for value in row] for row in proper_triad_change]
    generalized = _block_diag(strain_change, strain_change)
    reversed_section = _matmul(
        _matmul(generalized, section), _transpose(generalized)
    )
    return reversed_section, proper_triad_change, strain_change


def _reversal_transform(strain_change: Matrix, mutation: str | None) -> Matrix:
    """Map forward variables into the reversed connectivity representation."""

    transform = _zeros(36, 36)
    for new_node in range(3):
        old_node = 2 - new_node
        for component in range(6):
            transform[_q_index(new_node, component)][
                _q_index(old_node, component)
            ] = F(1)
    moment_change = (
        _diag([F(-1), F(1), F(-1)])
        if mutation == "reversal_map"
        else strain_change
    )
    for new_cell in range(2):
        old_cell = 1 - new_cell
        for component in range(3):
            transform[_local_index(new_cell, component)][
                _local_index(old_cell, component)
            ] = F(1)
            for source_component in range(3):
                transform[_local_index(new_cell, 3 + component)][
                    _local_index(old_cell, 6 + source_component)
                ] = moment_change[component][source_component]
                transform[_local_index(new_cell, 6 + component)][
                    _local_index(old_cell, 3 + source_component)
                ] = moment_change[component][source_component]
    return transform


def _two_point_monomial(degree: int) -> Fraction:
    """Exact symmetric Gauss-2 moment on [0,1], eliminating the surd."""

    midpoint = F(1, 2)
    offset_squared = F(1, 12)
    return sum(
        (
            F(math.comb(degree, even))
            * midpoint ** (degree - even)
            * offset_squared ** (even // 2)
            for even in range(0, degree + 1, 2)
        ),
        F(0),
    )


def _integration_checks() -> dict[str, bool]:
    exact = [F(1, degree + 1) for degree in range(5)]
    one_point = [F(1, 2) ** degree for degree in range(5)]
    two_point = [_two_point_monomial(degree) for degree in range(5)]
    exact_shape_mass = [[F(1, 3), F(1, 6)], [F(1, 6), F(1, 3)]]
    gauss_shape_mass = [
        [
            two_point[0] - 2 * two_point[1] + two_point[2],
            two_point[1] - two_point[2],
        ],
        [two_point[1] - two_point[2], two_point[2]],
    ]
    return {
        "one_point_exact_for_constant_and_linear_moments": one_point[:2]
        == exact[:2],
        "one_point_not_exact_for_quadratic_moment_energy": one_point[2]
        != exact[2],
        "two_point_exact_through_cubic": two_point[:4] == exact[:4],
        "two_point_not_claimed_beyond_degree_three": two_point[4] != exact[4],
        "two_point_exact_p1_shape_mass": gauss_shape_mass == exact_shape_mass,
    }


def _partial_legendre_reconstruction(
    section: Matrix, blocks: dict[str, Matrix], mutation: str | None
) -> bool:
    e = blocks["E"]
    if mutation == "wrong_legendre_sign":
        e = [[-value for value in row] for row in e]
    d = blocks["D"]
    b = _matmul(e, d)
    a = [
        [s_value + correction for s_value, correction in zip(s_row, correction_row)]
        for s_row, correction_row in zip(
            blocks["S"], _matmul(_matmul(e, d), _transpose(e))
        )
    ]
    reconstructed = _zeros(6, 6)
    for row in range(3):
        for column in range(3):
            reconstructed[row][column] = a[row][column]
            reconstructed[row][3 + column] = b[row][column]
            reconstructed[3 + column][row] = b[row][column]
            reconstructed[3 + row][3 + column] = d[row][column]
    return reconstructed == section


def reconstruct_certificate(
    *, section: Matrix | None = None, mutation: str | None = None
) -> dict[str, object]:
    """Return the deterministic exact local-algebra certificate."""

    allowed_mutations = {
        None,
        "drop_middle_jump",
        "force_sign",
        "moment_one_point",
        "reversal_map",
        "wrong_legendre_sign",
    }
    if mutation not in allowed_mutations:
        raise ValueError(f"unknown mutation: {mutation}")
    section = default_section() if section is None else [list(row) for row in section]
    section_lower, section_pivots = _ldl(section)
    section_spd = _matrix_equal(
        _ldl_reconstruction(section_lower, section_pivots), section
    ) and all(pivot > 0 for pivot in section_pivots)
    blocks = partial_legendre_blocks(section)
    hessian = build_mixed_hessian(section, mutation=mutation)
    condensed, internal, inverse_internal = _schur_condense(hessian)
    rigid, full_rigid = _rigid_modes()
    complement = _deterministic_complement(rigid)
    quotient = _matmul(_matmul(_transpose(complement), condensed), complement)
    try:
        quotient_lower, quotient_pivots = _ldl(quotient)
        quotient_reconstructs = (
            _ldl_reconstruction(quotient_lower, quotient_pivots) == quotient
        )
        quotient_positive = len(quotient_pivots) == 12 and all(
            pivot > 0 for pivot in quotient_pivots
        )
    except ValueError:
        # Mutations that add null modes must become deterministic findings,
        # rather than aborting before the remaining predicates are recorded.
        quotient_pivots = []
        quotient_reconstructs = False
        quotient_positive = False

    reversed_section, reversed_rotation, strain_change = _section_reversal(section)
    reversed_hessian = build_mixed_hessian(
        reversed_section, rotation=reversed_rotation
    )
    reversed_condensed, _, _ = _schur_condense(reversed_hessian)
    reversal = _reversal_transform(strain_change, mutation)
    external_reversal = _block(reversal, 0, 18, 0, 18)

    integration = _integration_checks()
    if mutation == "moment_one_point":
        integration["two_point_exact_p1_shape_mass"] = False

    predicates = {
        "dimensions_18_external_18_local_36_total": len(hessian) == 36
        and len(internal) == 18
        and len(condensed) == 18,
        "section_spd": section_spd,
        "partial_legendre_reconstructs_coupled_section": (
            _partial_legendre_reconstruction(section, blocks, mutation)
        ),
        "mixed_hessian_symmetric": hessian == _transpose(hessian),
        "internal_rank_18": _rank(internal) == 18,
        "internal_inverse_two_sided": _matmul(internal, inverse_internal)
        == _identity(18)
        and _matmul(inverse_internal, internal) == _identity(18),
        "full_rank_30_nullity_6": _rank(hessian) == 30,
        "condensed_rank_12_nullity_6": _rank(condensed) == 12,
        "six_rigid_modes_independent": _rank(rigid) == 6,
        "six_rigid_modes_exact_condensed_nulls": _matmul(condensed, rigid)
        == _zero_matrix(18, 6),
        "six_rigid_modes_exact_full_nulls": _matmul(hessian, full_rigid)
        == _zero_matrix(36, 6),
        "quotient_ldl_reconstructs": quotient_reconstructs,
        "quotient_has_12_positive_pivots": quotient_positive,
        "full_reversal_covariance": _matmul(
            _matmul(_transpose(reversal), reversed_hessian), reversal
        )
        == hessian,
        "condensed_reversal_covariance": _matmul(
            _matmul(_transpose(external_reversal), reversed_condensed),
            external_reversal,
        )
        == condensed,
        **integration,
    }
    failed = sorted(key for key, value in predicates.items() if not value)
    status = "PASS_LOCAL_LINEAR_IDENTITY" if not failed else "FAIL_LOCAL_LINEAR_IDENTITY"
    return {
        "candidate_id": CANDIDATE_ID,
        "counts": {
            "condensed_nullity": 18 - _rank(condensed),
            "condensed_rank": _rank(condensed),
            "external_variables": 18,
            "full_nullity": 36 - _rank(hessian),
            "full_rank": _rank(hessian),
            "internal_rank": _rank(internal),
            "local_variables": 18,
            "quotient_dimension": len(complement[0]),
            "rigid_modes": _rank(rigid),
        },
        "failed_predicates": failed,
        "hashes": {
            "condensed_operator_sha256": _digest_matrix(condensed),
            "full_mixed_operator_sha256": _digest_matrix(hessian),
            "internal_operator_sha256": _digest_matrix(internal),
            "quotient_ldl_pivots_sha256": hashlib.sha256(
                _canonical_bytes([_fraction_text(value) for value in quotient_pivots])
            ).hexdigest().upper(),
            "section_sha256": _digest_matrix(section),
        },
        "mutation": mutation or "NONE",
        "predicates": predicates,
        "production_boundary": {
            "production_authorized": False,
            "selector_authorized": False,
        },
        "qualification_claim": "LOCAL_REFERENCE_LINEAR_IDENTITY_ONLY",
        "schema": SCHEMA,
        "status": status,
        "study_id": STUDY_ID,
    }


def canonical_certificate_bytes(
    *, section: Matrix | None = None, mutation: str | None = None
) -> bytes:
    return _canonical_bytes(reconstruct_certificate(section=section, mutation=mutation))


def _write_exclusive(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--mutation",
        choices=[
            "drop_middle_jump",
            "force_sign",
            "moment_one_point",
            "reversal_map",
            "wrong_legendre_sign",
        ],
    )
    arguments = parser.parse_args(list(argv) if argv is not None else None)
    payload = canonical_certificate_bytes(mutation=arguments.mutation)
    if arguments.output is None:
        sys.stdout.buffer.write(payload)
    else:
        _write_exclusive(arguments.output, payload)
    certificate = json.loads(payload)
    return 0 if certificate["status"] == "PASS_LOCAL_LINEAR_IDENTITY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
