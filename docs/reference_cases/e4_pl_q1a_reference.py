"""Research reference for the E4-PL-Q1A planar element identity.

This module is deliberately outside ``src`` and is not imported by the
independent qualification oracle.  It evaluates the frozen source equations
with exact arithmetic in Q(sqrt(3)); it is not a production element.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
from typing import Sequence


ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "docs/reference_cases/e4_pl_q1a_cases.json"


def _fraction(value: object) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if not isinstance(value, str):
        raise TypeError(f"not an exact rational: {value!r}")
    return Fraction(value)


@dataclass(frozen=True)
class Q3:
    """An exact element of Q(sqrt(3))."""

    a: Fraction = Fraction(0)
    b: Fraction = Fraction(0)

    @classmethod
    def make(cls, value: object) -> "Q3":
        if isinstance(value, cls):
            return value
        return cls(_fraction(value), Fraction(0))

    def __add__(self, other: object) -> "Q3":
        rhs = Q3.make(other)
        return Q3(self.a + rhs.a, self.b + rhs.b)

    __radd__ = __add__

    def __neg__(self) -> "Q3":
        return Q3(-self.a, -self.b)

    def __sub__(self, other: object) -> "Q3":
        return self + (-Q3.make(other))

    def __rsub__(self, other: object) -> "Q3":
        return Q3.make(other) - self

    def __mul__(self, other: object) -> "Q3":
        rhs = Q3.make(other)
        return Q3(
            self.a * rhs.a + 3 * self.b * rhs.b,
            self.a * rhs.b + self.b * rhs.a,
        )

    __rmul__ = __mul__

    def inverse(self) -> "Q3":
        denominator = self.a * self.a - 3 * self.b * self.b
        if not denominator:
            raise ZeroDivisionError("zero in Q(sqrt(3))")
        return Q3(self.a / denominator, -self.b / denominator)

    def __truediv__(self, other: object) -> "Q3":
        return self * Q3.make(other).inverse()

    def __rtruediv__(self, other: object) -> "Q3":
        return Q3.make(other) / self

    def __bool__(self) -> bool:
        return bool(self.a or self.b)

    def pair(self) -> list[str]:
        return [str(self.a), str(self.b)]


Scalar = Q3
Vector = list[Scalar]
Matrix = list[Vector]


ZERO = Q3()
ONE = Q3(Fraction(1))


def _zeros(rows: int, columns: int) -> Matrix:
    return [[ZERO for _ in range(columns)] for _ in range(rows)]


def _identity(size: int) -> Matrix:
    result = _zeros(size, size)
    for index in range(size):
        result[index][index] = ONE
    return result


def _transpose(matrix: Matrix) -> Matrix:
    if not matrix:
        return []
    return [list(row) for row in zip(*matrix)]


def _add(left: Matrix, right: Matrix) -> Matrix:
    return [
        [left[row][column] + right[row][column] for column in range(len(left[0]))]
        for row in range(len(left))
    ]


def _sub(left: Matrix, right: Matrix) -> Matrix:
    return [
        [left[row][column] - right[row][column] for column in range(len(left[0]))]
        for row in range(len(left))
    ]


def _scale(matrix: Matrix, factor: object) -> Matrix:
    scalar = Q3.make(factor)
    return [[scalar * value for value in row] for row in matrix]


def _multiply(left: Matrix, right: Matrix) -> Matrix:
    if not left or not right or len(left[0]) != len(right):
        raise ValueError("matrix product dimensions")
    result = _zeros(len(left), len(right[0]))
    right_t = _transpose(right)
    for row_index, row in enumerate(left):
        for column_index, column in enumerate(right_t):
            result[row_index][column_index] = sum(
                (x * y for x, y in zip(row, column) if x and y), ZERO
            )
    return result


def _matvec(matrix: Matrix, vector: Vector) -> Vector:
    return [sum((x * y for x, y in zip(row, vector) if x and y), ZERO) for row in matrix]


def _rank(matrix: Matrix) -> int:
    if not matrix:
        return 0
    work = [row[:] for row in matrix]
    rows, columns = len(work), len(work[0])
    rank = 0
    for column in range(columns):
        pivot = next((row for row in range(rank, rows) if work[row][column]), None)
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        inverse = work[rank][column].inverse()
        work[rank] = [value * inverse for value in work[rank]]
        for row in range(rows):
            if row == rank or not work[row][column]:
                continue
            factor = work[row][column]
            work[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(work[row], work[rank])
            ]
        rank += 1
        if rank == rows:
            break
    return rank


def _inverse(matrix: Matrix) -> Matrix:
    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise ValueError("inverse requires a square matrix")
    work = [row[:] + identity for row, identity in zip(matrix, _identity(size))]
    for column in range(size):
        pivot = next((row for row in range(column, size) if work[row][column]), None)
        if pivot is None:
            raise ValueError("singular exact matrix")
        work[column], work[pivot] = work[pivot], work[column]
        inverse = work[column][column].inverse()
        work[column] = [value * inverse for value in work[column]]
        for row in range(size):
            if row == column or not work[row][column]:
                continue
            factor = work[row][column]
            work[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(work[row], work[column])
            ]
    return [row[size:] for row in work]


def _ldl_pivots(matrix: Matrix) -> Vector:
    size = len(matrix)
    lower = _zeros(size, size)
    pivots: Vector = []
    for row in range(size):
        lower[row][row] = ONE
        pivot = matrix[row][row] - sum(
            (lower[row][column] * lower[row][column] * pivots[column] for column in range(row)),
            ZERO,
        )
        if not pivot:
            raise ValueError("zero LDL pivot")
        pivots.append(pivot)
        for target in range(row + 1, size):
            numerator = matrix[target][row] - sum(
                (
                    lower[target][column] * lower[row][column] * pivots[column]
                    for column in range(row)
                ),
                ZERO,
            )
            lower[target][row] = numerator / pivot
    return pivots


def _positive_rational_pivots(matrix: Matrix) -> bool:
    return all(not pivot.b and pivot.a > 0 for pivot in _ldl_pivots(matrix))


def _dot(left: Sequence[Scalar], right: Sequence[Scalar]) -> Scalar:
    return sum((x * y for x, y in zip(left, right) if x and y), ZERO)


def _outer(left: Vector, right: Vector) -> Matrix:
    return [[x * y for y in right] for x in left]


def _block_diagonal(left: Matrix, right: Matrix) -> Matrix:
    result = _zeros(len(left) + len(right), len(left) + len(right))
    for row in range(len(left)):
        for column in range(len(left)):
            result[row][column] = left[row][column]
    for row in range(len(right)):
        for column in range(len(right)):
            result[len(left) + row][len(left) + column] = right[row][column]
    return result


def _canonical(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _matrix_digest(matrix: Matrix) -> dict[str, object]:
    signature = [[value.pair() for value in row] for row in matrix]
    raw = _canonical(signature)
    return {
        "bytes": len(raw),
        "nonzeros": sum(bool(value) for row in matrix for value in row),
        "sha256": _sha(raw),
        "shape": [len(matrix), len(matrix[0]) if matrix else 0],
    }


def _vector_digest(vector: Vector) -> dict[str, object]:
    raw = _canonical([value.pair() for value in vector])
    return {
        "bytes": len(raw),
        "nonzeros": sum(bool(value) for value in vector),
        "sha256": _sha(raw),
        "size": len(vector),
    }


def _as_q3_matrix(matrix: Sequence[Sequence[object]]) -> Matrix:
    return [[Q3.make(value) for value in row] for row in matrix]


def _modal(values: Sequence[object]) -> list[Fraction]:
    nodal = [_fraction(value) for value in values]
    signs = (
        (1, 1, 1, 1),
        (-1, 1, 1, -1),
        (-1, -1, 1, 1),
        (1, -1, 1, -1),
    )
    return [sum(Fraction(sign) * value for sign, value in zip(row, nodal)) / 4 for row in signs]


def _shape(r: Scalar, s: Scalar) -> tuple[Vector, Vector, Vector]:
    signs_r = (-1, 1, 1, -1)
    signs_s = (-1, -1, 1, 1)
    values, derivatives_r, derivatives_s = [], [], []
    for sign_r, sign_s in zip(signs_r, signs_s):
        values.append((ONE + sign_r * r) * (ONE + sign_s * s) / 4)
        derivatives_r.append(Q3.make(sign_r) * (ONE + sign_s * s) / 4)
        derivatives_s.append(Q3.make(sign_s) * (ONE + sign_r * r) / 4)
    return values, derivatives_r, derivatives_s


def _geometry_modes(nodes: Sequence[Sequence[object]]) -> dict[str, list[Fraction]]:
    x = _modal([node[0] for node in nodes])
    y = _modal([node[1] for node in nodes])
    xr, xs, xrs = x[1], x[2], x[3]
    yr, ys, yrs = y[1], y[2], y[3]
    jc = xr * ys - xs * yr
    jr = xr * yrs - xrs * yr
    js = xrs * ys - xs * yrs
    if jc == 0:
        raise ValueError("frozen common-frame geometry requires nonzero centre Jacobian")
    return {"x": x, "y": y, "j": [jc, jr, js]}


def _geometry_at(modes: dict[str, list[Fraction]], r: Scalar, s: Scalar) -> tuple[Matrix, Scalar]:
    x, y = modes["x"], modes["y"]
    # Cartesian-by-natural form.  WG's printed J is its transpose.
    jacobian = [
        [Q3.make(x[1]) + x[3] * s, Q3.make(x[2]) + x[3] * r],
        [Q3.make(y[1]) + y[3] * s, Q3.make(y[2]) + y[3] * r],
    ]
    determinant = jacobian[0][0] * jacobian[1][1] - jacobian[0][1] * jacobian[1][0]
    return jacobian, determinant


def _integration_measure(
    modes: dict[str, list[Fraction]], determinant: Scalar
) -> Scalar:
    """Return the positive area measure for either exact orientation.

    The frozen cases and every D4 image have one Jacobian sign throughout the
    element.  Natural-coordinate reversal changes both the centre and station
    signs, while the physical area measure remains positive.  No tolerance or
    pointwise absolute-value branch is used.
    """

    return determinant if modes["j"][0] > 0 else -determinant


def _inverse2(matrix: Matrix) -> Matrix:
    determinant = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    return [
        [matrix[1][1] / determinant, -matrix[0][1] / determinant],
        [-matrix[1][0] / determinant, matrix[0][0] / determinant],
    ]


def _tensor_transform(jacobian: Matrix, a: object, b: object) -> Matrix:
    x_r, x_s = jacobian[0]
    y_r, y_s = jacobian[1]
    return [
        [x_r * x_r, y_r * y_r, Q3.make(a) * x_r * y_r],
        [x_s * x_s, y_s * y_s, Q3.make(a) * x_s * y_s],
        [Q3.make(b) * x_r * x_s, Q3.make(b) * y_r * y_s, x_r * y_s + x_s * y_r],
    ]


def _set_transformed_columns(
    target: Matrix,
    row_offset: int,
    global_columns: Sequence[int],
    transform: Matrix,
    seeds: Matrix,
) -> None:
    for local_column, global_column in enumerate(global_columns):
        for output_row, transform_row in enumerate(transform):
            target[row_offset + output_row][global_column] = sum(
                (
                    transform_row[input_row] * seeds[input_row][local_column]
                    for input_row in range(len(seeds))
                    if transform_row[input_row] and seeds[input_row][local_column]
                ),
                ZERO,
            )


def _source_spaces(
    modes: dict[str, list[Fraction]], r: Scalar, s: Scalar, determinant: Scalar
) -> tuple[Matrix, Matrix]:
    n_sigma, n_epsilon = _zeros(8, 14), _zeros(8, 21)
    for index in range(8):
        n_sigma[index][index] = ONE
        n_epsilon[index][index] = ONE
    jc, jr, js = modes["j"]
    bar_r, bar_s = jr / (3 * jc), js / (3 * jc)
    center_jacobian = _as_q3_matrix(
        [[modes["x"][1], modes["x"][2]], [modes["y"][1], modes["y"][2]]]
    )
    tensor_seed = [
        [s - bar_s, ZERO],
        [ZERO, r - bar_r],
        [ZERO, ZERO],
    ]
    vector_seed = [[s - bar_s, ZERO], [ZERO, r - bar_r]]
    for target, transform in (
        (n_sigma, _tensor_transform(center_jacobian, 2, 1)),
        (n_epsilon, _tensor_transform(center_jacobian, 1, 2)),
    ):
        _set_transformed_columns(target, 0, (8, 9), transform, tensor_seed)
        _set_transformed_columns(target, 3, (10, 11), transform, tensor_seed)
        _set_transformed_columns(target, 6, (12, 13), center_jacobian, vector_seed)
    rs = r * s
    enrichment_seed = [
        [r, ZERO, ZERO, ZERO, rs, ZERO, ZERO],
        [ZERO, s, ZERO, ZERO, ZERO, rs, ZERO],
        [ZERO, ZERO, r, s, ZERO, ZERO, rs],
    ]
    scale = Q3.make(jc) / determinant
    enrichment_seed = _scale(enrichment_seed, scale)
    _set_transformed_columns(
        n_epsilon,
        0,
        tuple(range(14, 21)),
        _tensor_transform(center_jacobian, 1, 2),
        enrichment_seed,
    )
    return n_sigma, n_epsilon


def _linear_row_at(
    field: int,
    values: Vector,
    derivatives_r: Vector | None = None,
    derivatives_s: Vector | None = None,
) -> tuple[Vector, Vector, Vector]:
    rows = (_zeros(1, 20)[0], _zeros(1, 20)[0], _zeros(1, 20)[0])
    for node in range(4):
        rows[0][5 * node + field] = values[node]
        if derivatives_r is not None:
            rows[1][5 * node + field] = derivatives_r[node]
        if derivatives_s is not None:
            rows[2][5 * node + field] = derivatives_s[node]
    return rows


def _vadd(*vectors: Vector) -> Vector:
    return [sum((vector[index] for vector in vectors), ZERO) for index in range(len(vectors[0]))]


def _vscale(vector: Vector, factor: object) -> Vector:
    scalar = Q3.make(factor)
    return [scalar * value for value in vector]


def _physical_derivatives(
    row_r: Vector, row_s: Vector, jacobian: Matrix
) -> tuple[Vector, Vector]:
    # [f_x,f_y]^T = J_cartesian-natural^-T [f_r,f_s]^T.
    inverse_t = _transpose(_inverse2(jacobian))
    return (
        _vadd(_vscale(row_r, inverse_t[0][0]), _vscale(row_s, inverse_t[0][1])),
        _vadd(_vscale(row_r, inverse_t[1][0]), _vscale(row_s, inverse_t[1][1])),
    )


def _tied_natural_shear(
    modes: dict[str, list[Fraction]], direction: str, coordinate: int
) -> Vector:
    if direction == "r":
        r, s = Q3(), Q3.make(coordinate)
    else:
        r, s = Q3.make(coordinate), Q3()
    values, derivatives_r, derivatives_s = _shape(r, s)
    jacobian, unused = _geometry_at(modes, r, s)
    del unused
    w = _linear_row_at(2, values, derivatives_r, derivatives_s)
    rx = _linear_row_at(3, values)
    ry = _linear_row_at(4, values)
    if direction == "r":
        return _vadd(w[1], _vscale(ry[0], jacobian[0][0]), _vscale(rx[0], -jacobian[1][0]))
    return _vadd(w[2], _vscale(ry[0], jacobian[0][1]), _vscale(rx[0], -jacobian[1][1]))


def _compatible_map(
    modes: dict[str, list[Fraction]], r: Scalar, s: Scalar, jacobian: Matrix
) -> Matrix:
    values, derivatives_r, derivatives_s = _shape(r, s)
    rows = [_linear_row_at(field, values, derivatives_r, derivatives_s) for field in range(5)]
    u, v, unused_w, rx, ry = rows
    del unused_w
    u_x, u_y = _physical_derivatives(u[1], u[2], jacobian)
    v_x, v_y = _physical_derivatives(v[1], v[2], jacobian)
    rx_x, rx_y = _physical_derivatives(rx[1], rx[2], jacobian)
    ry_x, ry_y = _physical_derivatives(ry[1], ry[2], jacobian)

    tied_r_minus = _tied_natural_shear(modes, "r", -1)
    tied_r_plus = _tied_natural_shear(modes, "r", 1)
    tied_s_minus = _tied_natural_shear(modes, "s", -1)
    tied_s_plus = _tied_natural_shear(modes, "s", 1)
    tied_r = _vadd(_vscale(tied_r_minus, (ONE - s) / 2), _vscale(tied_r_plus, (ONE + s) / 2))
    tied_s = _vadd(_vscale(tied_s_minus, (ONE - r) / 2), _vscale(tied_s_plus, (ONE + r) / 2))
    gamma_x, gamma_y = _physical_derivatives(tied_r, tied_s, jacobian)
    return [
        u_x,
        v_y,
        _vadd(u_y, v_x),
        ry_x,
        _vscale(rx_y, -1),
        _vadd(ry_y, _vscale(rx_x, -1)),
        gamma_x,
        gamma_y,
    ]


def _gauss_points() -> list[tuple[Scalar, Scalar]]:
    g = Q3(Fraction(0), Fraction(1, 3))
    return [(-g, -g), (g, -g), (g, g), (-g, g)]


def _constitutive(record: dict[str, object]) -> Matrix:
    return _as_q3_matrix(record["resultant_matrix"])


def _isotropic_constitutive(e: Fraction, nu: Fraction, thickness: Fraction) -> Matrix:
    shear_modulus = e / (2 * (1 + nu))
    factor = e / (1 - nu * nu)
    membrane = [
        [factor, factor * nu, Fraction(0)],
        [factor * nu, factor, Fraction(0)],
        [Fraction(0), Fraction(0), factor * (1 - nu) / 2],
    ]
    result = _zeros(8, 8)
    for row in range(3):
        for column in range(3):
            result[row][column] = Q3.make(thickness * membrane[row][column])
            result[3 + row][3 + column] = Q3.make(
                thickness**3 * membrane[row][column] / 12
            )
    result[6][6] = result[7][7] = Q3.make(Fraction(5, 6) * shear_modulus * thickness)
    return result


def _assemble_core(case: dict[str, object], constitutive: Matrix) -> dict[str, Matrix | int]:
    modes = _geometry_modes(case["coordinates"])
    f, h, gq = _zeros(21, 14), _zeros(21, 21), _zeros(14, 20)
    for r, s in _gauss_points():
        jacobian, determinant = _geometry_at(modes, r, s)
        n_sigma, n_epsilon = _source_spaces(modes, r, s, determinant)
        bmap = _compatible_map(modes, r, s, jacobian)
        measure = _integration_measure(modes, determinant)
        f = _sub(f, _scale(_multiply(_transpose(n_epsilon), n_sigma), measure))
        h = _add(h, _scale(_multiply(_multiply(_transpose(n_epsilon), constitutive), n_epsilon), measure))
        gq = _add(gq, _scale(_multiply(_transpose(n_sigma), bmap), measure))
    d = _zeros(35, 35)
    for stress in range(14):
        for strain in range(21):
            d[stress][14 + strain] = f[strain][stress]
            d[14 + strain][stress] = f[strain][stress]
    for left in range(21):
        for right in range(21):
            d[14 + left][14 + right] = h[left][right]
    d_inverse = _inverse(d)
    coupling = [row + [ZERO] * 21 for row in _transpose(gq)]
    k5 = _scale(_multiply(_multiply(coupling, d_inverse), _transpose(coupling)), -1)
    return {
        "D": d,
        "D_inverse": d_inverse,
        "F": f,
        "Gq": gq,
        "H": h,
        "K5": k5,
        "Q": coupling,
    }


def _selectors() -> tuple[Matrix, Matrix]:
    t5, qd = _zeros(24, 20), _zeros(24, 4)
    for node in range(4):
        for local in range(5):
            t5[6 * node + local][5 * node + local] = ONE
        qd[6 * node + 5][node] = ONE
    return t5, qd


def _det2(matrix: Sequence[Sequence[object]]) -> Fraction:
    return (
        _fraction(matrix[0][0]) * _fraction(matrix[1][1])
        - _fraction(matrix[0][1]) * _fraction(matrix[1][0])
    )


def _component_transform_5(frame: Sequence[Sequence[object]]) -> Matrix:
    rotation = _as_q3_matrix(frame)
    normal_scale = Q3.make(_det2(frame))
    result = _zeros(5, 5)
    for row in range(2):
        for column in range(2):
            result[row][column] = rotation[row][column]
            result[3 + row][3 + column] = rotation[row][column]
    result[2][2] = normal_scale
    return result


def _component_transform_6(frame: Sequence[Sequence[object]]) -> Matrix:
    physical = _component_transform_5(frame)
    result = _zeros(6, 6)
    for row in range(5):
        for column in range(5):
            result[row][column] = physical[row][column]
    result[5][5] = Q3.make(_det2(frame))
    return result


def _nodal_transform(
    block: Matrix, old_indices_for_new_nodes: Sequence[int] = (0, 1, 2, 3)
) -> Matrix:
    block_size = len(block)
    result = _zeros(4 * block_size, 4 * block_size)
    for new_node, old_node in enumerate(old_indices_for_new_nodes):
        for row in range(block_size):
            for column in range(block_size):
                result[block_size * new_node + row][block_size * old_node + column] = block[row][column]
    return result


def _transform_nodes(
    nodes: Sequence[Sequence[object]],
    frame: Sequence[Sequence[object]],
    old_indices_for_new_nodes: Sequence[int] = (0, 1, 2, 3),
    shift: Sequence[object] = (0, 0),
    scale: object = 1,
) -> list[list[str]]:
    factor = _fraction(scale)
    transformed: list[list[str]] = []
    for old_node in old_indices_for_new_nodes:
        x, y = (_fraction(value) for value in nodes[old_node])
        new_x = _fraction(frame[0][0]) * x + _fraction(frame[0][1]) * y
        new_y = _fraction(frame[1][0]) * x + _fraction(frame[1][1]) * y
        transformed.append(
            [str(factor * new_x + _fraction(shift[0])), str(factor * new_y + _fraction(shift[1]))]
        )
    return transformed


def _natural_node_permutation(matrix: Sequence[Sequence[object]]) -> list[int]:
    nodes = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    lookup = {node: index for index, node in enumerate(nodes)}
    result: list[int] = []
    for r, s in nodes:
        old_r = int(_fraction(matrix[0][0]) * r + _fraction(matrix[0][1]) * s)
        old_s = int(_fraction(matrix[1][0]) * r + _fraction(matrix[1][1]) * s)
        result.append(lookup[(old_r, old_s)])
    return result


def _d4_matrices() -> list[list[list[int]]]:
    return [
        [[1, 0], [0, 1]],
        [[0, -1], [1, 0]],
        [[-1, 0], [0, -1]],
        [[0, 1], [-1, 0]],
        [[-1, 0], [0, 1]],
        [[1, 0], [0, -1]],
        [[0, 1], [1, 0]],
        [[0, -1], [-1, 0]],
    ]


def _transformed_case(
    case: dict[str, object],
    coordinates: list[list[str]],
    suffix: str,
) -> dict[str, object]:
    return {
        "class": case["class"],
        "coordinates": coordinates,
        "id": f"{case['id']}__{suffix}",
        "mapping": case["mapping"],
    }


def _congruence(matrix: Matrix, transform: Matrix) -> Matrix:
    return _multiply(_multiply(transform, matrix), _transpose(transform))


def _common_frame_embedding_covariance(matrix: Matrix, transform: Matrix) -> bool:
    """Certify a local shell operator's exact global-frame embedding.

    Q1A matrices are assembled in the frozen common orthonormal component
    frame.  A global frame action therefore changes the local-to-global
    embedding, not the local geometry supplied to the WG source equations.
    """

    identity = _identity(len(transform))
    if _multiply(_transpose(transform), transform) != identity:
        return False
    embedded = _congruence(matrix, transform)
    if _multiply(_multiply(_transpose(transform), embedded), transform) != matrix:
        return False
    local_probe = [Q3.make(Fraction(index - 7, 11)) for index in range(len(matrix))]
    global_probe = _matvec(transform, local_probe)
    return _dot(local_probe, _matvec(matrix, local_probe)) == _dot(
        global_probe, _matvec(embedded, global_probe)
    )


def _constraint_rows(case: dict[str, object]) -> Matrix:
    modes = _geometry_modes(case["coordinates"])
    x, y = modes["x"], modes["y"]
    jc, jr, js = modes["j"]
    rows = [[Fraction(0) for _ in range(24)] for _ in range(3)]
    for column in range(24):
        node, local = divmod(column, 6)
        u = [Fraction(0)] * 4
        v = [Fraction(0)] * 4
        d = [Fraction(0)] * 4
        if local == 0:
            u[node] = Fraction(1)
        elif local == 1:
            v[node] = Fraction(1)
        elif local == 5:
            d[node] = Fraction(1)
        um, vm, dm = _modal(u), _modal(v), _modal(d)
        n0 = -x[2] * um[1] + x[1] * um[2] - y[2] * vm[1] + y[1] * vm[2]
        nr = -x[3] * um[1] + x[1] * um[3] - y[3] * vm[1] + y[1] * vm[3]
        ns = -x[2] * um[3] + x[3] * um[2] - y[2] * vm[3] + y[3] * vm[2]
        rows[0][column] = dm[0] + n0 / (2 * jc)
        rows[1][column] = dm[1] + (nr * jc - n0 * jr) / (2 * jc * jc)
        rows[2][column] = dm[2] + (ns * jc - n0 * js) / (2 * jc * jc)
    return _as_q3_matrix(rows)


def _gamma_row(case: dict[str, object]) -> Vector:
    nodes = [[_fraction(value) for value in node] for node in case["coordinates"]]
    center = [sum(node[axis] for node in nodes) / 4 for axis in range(2)]
    s1 = [node[0] - center[0] for node in nodes]
    s2 = [node[1] - center[1] for node in nodes]
    xi = [Fraction(value) for value in (-1, 1, 1, -1)]
    eta = [Fraction(value) for value in (-1, -1, 1, 1)]
    hourglass = [Fraction(value) for value in (1, -1, 1, -1)]
    area = 4 * abs(_geometry_modes(case["coordinates"])["j"][0])
    eta_s2 = sum(x * y for x, y in zip(eta, s2))
    xi_s2 = sum(x * y for x, y in zip(xi, s2))
    eta_s1 = sum(x * y for x, y in zip(eta, s1))
    xi_s1 = sum(x * y for x, y in zip(xi, s1))
    b1 = [
        (eta_s2 * xi[index] - xi_s2 * eta[index]) / (4 * area)
        for index in range(4)
    ]
    b2 = [
        (-eta_s1 * xi[index] + xi_s1 * eta[index]) / (4 * area)
        for index in range(4)
    ]
    hs1 = sum(x * y for x, y in zip(hourglass, s1))
    hs2 = sum(x * y for x, y in zip(hourglass, s2))
    return [Q3.make((hourglass[index] - hs1 * b1[index] - hs2 * b2[index]) / 4) for index in range(4)]


def _multiplier_mass(case: dict[str, object], thickness: Fraction) -> Matrix:
    modes = _geometry_modes(case["coordinates"])
    mass = _zeros(3, 3)
    for r, s in _gauss_points():
        unused_jacobian, determinant = _geometry_at(modes, r, s)
        del unused_jacobian
        p = [ONE, r, s]
        measure = _integration_measure(modes, determinant)
        mass = _add(mass, _scale(_outer(p, p), Q3.make(thickness) * measure))
    return mass


def _numerical_operators(
    case: dict[str, object], shear_modulus: Fraction, thickness: Fraction, epsilon: Fraction
) -> dict[str, Matrix]:
    c = _constraint_rows(case)
    gamma = _gamma_row(case)
    mass = _multiplier_mass(case, thickness)
    b = _multiply(mass, c)
    k_pl = _scale(_multiply(_multiply(_transpose(c), mass), c), shear_modulus)
    h24 = [ZERO for _ in range(24)]
    for node, value in enumerate(gamma):
        h24[6 * node + 5] = value
    area = 4 * abs(_geometry_modes(case["coordinates"])["j"][0])
    k_hg = _scale(_outer(h24, h24), 2 * epsilon * shear_modulus * thickness * area)
    t5, qd = _selectors()
    a = _multiply(c, t5) + [_zeros(1, 20)[0]]
    rmap = _multiply(c, qd) + [gamma]
    weight = _block_diagonal(_scale(mass, shear_modulus), [[Q3.make(2 * epsilon * shear_modulus * thickness * area)]])
    kdd = _multiply(_multiply(_transpose(rmap), weight), rmap)
    return {
        "A": a,
        "B": b,
        "C": c,
        "Kdd": kdd,
        "K_hg": k_hg,
        "K_num": _add(k_pl, k_hg),
        "K_pl": k_pl,
        "L": [left + right for left, right in zip(a, rmap)],
        "M": mass,
        "R": rmap,
        "W": weight,
    }


def _element_matrices(
    case: dict[str, object],
    material: dict[str, object],
    constitutive: Matrix | None = None,
) -> dict[str, object]:
    e = _fraction(material["E"])
    nu = _fraction(material["nu"])
    thickness = _fraction(material["t"])
    shear_modulus = e / (2 * (1 + nu))
    epsilon = _fraction(material["epsilon_hg"])
    if constitutive is None:
        constitutive = _isotropic_constitutive(e, nu, thickness)
    core = _assemble_core(case, constitutive)
    numerical = _numerical_operators(case, shear_modulus, thickness, epsilon)
    t5, unused_qd = _selectors()
    del unused_qd
    k5 = core["K5"]
    if not isinstance(k5, list):
        raise TypeError("K5")
    k0 = _multiply(_multiply(t5, k5), _transpose(t5))
    return {
        "core": core,
        "K0": k0,
        "K24": _add(k0, numerical["K_num"]),
        "K5": k5,
        "numerical": numerical,
    }


def _rigid_vectors_20(case: dict[str, object]) -> dict[str, Vector]:
    nodes = [[_fraction(value) for value in node] for node in case["coordinates"]]
    result = {name: [] for name in (
        "translation_x", "translation_y", "translation_z",
        "rotation_x", "rotation_y", "rotation_z_translation_only",
    )}
    for x, y in nodes:
        result["translation_x"].extend((1, 0, 0, 0, 0))
        result["translation_y"].extend((0, 1, 0, 0, 0))
        result["translation_z"].extend((0, 0, 1, 0, 0))
        result["rotation_x"].extend((0, 0, y, 1, 0))
        result["rotation_y"].extend((0, 0, -x, 0, 1))
        result["rotation_z_translation_only"].extend((-y, x, 0, 0, 0))
    return {name: [Q3.make(value) for value in vector] for name, vector in result.items()}


def _rigid_vectors_24(case: dict[str, object]) -> dict[str, Vector]:
    nodes = [[_fraction(value) for value in node] for node in case["coordinates"]]
    result = {name: [] for name in (
        "translation_x", "translation_y", "translation_z",
        "rotation_x", "rotation_y", "rotation_z",
    )}
    for x, y in nodes:
        result["translation_x"].extend((1, 0, 0, 0, 0, 0))
        result["translation_y"].extend((0, 1, 0, 0, 0, 0))
        result["translation_z"].extend((0, 0, 1, 0, 0, 0))
        result["rotation_x"].extend((0, 0, y, 1, 0, 0))
        result["rotation_y"].extend((0, 0, -x, 0, 1, 0))
        result["rotation_z"].extend((-y, x, 0, 0, 0, 1))
    return {name: [Q3.make(value) for value in vector] for name, vector in result.items()}


def _patch_vectors(case: dict[str, object]) -> dict[str, Vector]:
    nodes = [[_fraction(value) for value in node] for node in case["coordinates"]]
    patches: dict[str, Vector] = {}

    def field(a: Fraction, b: Fraction, c: Fraction, d: Fraction) -> Vector:
        drill = (c - b) / 2
        vector: Vector = []
        for x, y in nodes:
            vector.extend(Q3.make(value) for value in (a * x + b * y, c * x + d * y, 0, 0, 0, drill))
        return vector

    patches["constant_extension"] = field(Fraction(1), Fraction(0), Fraction(0), Fraction(0))
    patches["constant_symmetric_shear"] = field(Fraction(0), Fraction(1, 2), Fraction(1, 2), Fraction(0))
    patches["general_affine_membrane_with_spin"] = field(
        Fraction(2), Fraction(1, 3), Fraction(-2, 5), Fraction(4, 3)
    )
    patches["bending_shear_decoupling"] = [ZERO for _ in range(24)]
    for node, (x, y) in enumerate(nodes):
        patches["bending_shear_decoupling"][6 * node + 2] = Q3.make(x + 2 * y)
        patches["bending_shear_decoupling"][6 * node + 3] = Q3.make(Fraction(-2))
        patches["bending_shear_decoupling"][6 * node + 4] = ONE
    return patches


def _physical_patch_fields(case: dict[str, object]) -> dict[str, dict[str, Vector]]:
    nodes = [[_fraction(value) for value in node] for node in case["coordinates"]]

    def membrane(a: Fraction, b: Fraction, c: Fraction, d: Fraction) -> tuple[Vector, Vector]:
        physical: Vector = []
        complete: Vector = []
        drill = (c - b) / 2
        for x, y in nodes:
            values5 = (a * x + b * y, c * x + d * y, 0, 0, 0)
            physical.extend(Q3.make(value) for value in values5)
            complete.extend(Q3.make(value) for value in (*values5, drill))
        return physical, complete

    membrane_p, membrane_q = membrane(
        Fraction(2), Fraction(1, 3), Fraction(-2, 5), Fraction(4, 3)
    )
    membrane_expected = [
        Q3.make(value)
        for value in (Fraction(2), Fraction(4, 3), Fraction(-1, 15), 0, 0, 0, 0, 0)
    ]

    kxx, kyy, kxy = Fraction(2, 5), Fraction(-1, 3), Fraction(3, 7)
    bending_p: Vector = []
    bending_q: Vector = []
    for x, y in nodes:
        rx = -kxy * x / 2 - kyy * y
        ry = kxx * x + kxy * y / 2
        w = -kxx * x * x / 2 - kxy * x * y / 2 - kyy * y * y / 2
        values5 = (0, 0, w, rx, ry)
        bending_p.extend(Q3.make(value) for value in values5)
        bending_q.extend(Q3.make(value) for value in (*values5, 0))
    bending_expected = [Q3.make(value) for value in (0, 0, 0, kxx, kyy, kxy, 0, 0)]

    shear_x, shear_y = Fraction(2, 3), Fraction(-1, 4)
    shear_p: Vector = []
    shear_q: Vector = []
    for unused_x, unused_y in nodes:
        del unused_x, unused_y
        values5 = (0, 0, 0, -shear_y, shear_x)
        shear_p.extend(Q3.make(value) for value in values5)
        shear_q.extend(Q3.make(value) for value in (*values5, 0))
    shear_expected = [Q3.make(value) for value in (0, 0, 0, 0, 0, 0, shear_x, shear_y)]

    combined_p = _vadd(membrane_p, bending_p, shear_p)
    combined_q = _vadd(membrane_q, bending_q, shear_q)
    combined_expected = _vadd(membrane_expected, bending_expected, shear_expected)
    return {
        "membrane_nonzero_spin": {
            "expected": membrane_expected,
            "p": membrane_p,
            "q": membrane_q,
        },
        "bending": {"expected": bending_expected, "p": bending_p, "q": bending_q},
        "transverse_shear": {"expected": shear_expected, "p": shear_p, "q": shear_q},
        "combined": {"expected": combined_expected, "p": combined_p, "q": combined_q},
    }


def _physical_patch_certificate(
    case: dict[str, object],
    core: dict[str, Matrix | int],
    k5: Matrix,
    k_num: Matrix,
    constitutive: Matrix,
) -> dict[str, dict[str, object]]:
    modes = _geometry_modes(case["coordinates"])
    area = Q3.make(4 * abs(modes["j"][0]))
    result: dict[str, dict[str, object]] = {}
    for name, record in _physical_patch_fields(case).items():
        physical, complete, expected = record["p"], record["q"], record["expected"]
        expected_stress = _matvec(constitutive, expected)
        gauss_strain_exact = True
        recovery_exact = True
        d_inverse = core["D_inverse"]
        coupling = core["Q"]
        if not isinstance(d_inverse, list) or not isinstance(coupling, list):
            raise TypeError("core recovery blocks")
        stationary = _vscale(
            _matvec(d_inverse, _matvec(_transpose(coupling), physical)), -1
        )
        stress_parameters = stationary[:14]
        for r, s in _gauss_points():
            jacobian, determinant = _geometry_at(modes, r, s)
            bmap = _compatible_map(modes, r, s, jacobian)
            n_sigma, unused_n_epsilon = _source_spaces(modes, r, s, determinant)
            del unused_n_epsilon
            gauss_strain_exact = gauss_strain_exact and _matvec(bmap, physical) == expected
            recovery_exact = recovery_exact and _matvec(n_sigma, stress_parameters) == expected_stress
        core_energy = _dot(physical, _matvec(k5, physical)) / 2
        continuum_energy = area * _dot(expected, expected_stress) / 2
        result[name] = {
            "core_energy": core_energy.pair(),
            "energy_exact": core_energy == continuum_energy,
            "expected_strain": [value.pair() for value in expected],
            "gauss_strain_exact": gauss_strain_exact,
            "numerical_zero": not any(_matvec(k_num, complete)),
            "recovery_exact": recovery_exact,
        }
    return result


def _unit_coordinate_transform(block_size: int, scale: Fraction) -> Matrix:
    block = _identity(block_size)
    for index in range(3):
        block[index][index] = Q3.make(scale)
    return _nodal_transform(block)


def _scaled_material(material: dict[str, object], scale: Fraction) -> dict[str, object]:
    return {
        "E": str(_fraction(material["E"]) / (scale * scale)),
        "epsilon_hg": str(_fraction(material["epsilon_hg"])),
        "nu": str(_fraction(material["nu"])),
        "t": str(_fraction(material["t"]) * scale),
    }


def _full_covariance_certificate(
    case: dict[str, object],
    base_k5: Matrix,
    base_k24: Matrix,
    material: dict[str, object],
) -> dict[str, object]:
    nodes = case["coordinates"]
    d4_k5_count, d4_k24_count = 0, 0
    for natural in _d4_matrices():
        determinant = _det2(natural)
        # The preregistered common component frame stays fixed for proper D4
        # reparameterizations.  An improper action uses the one frozen tangent
        # reflection needed to preserve a right-handed shell frame.
        frame = [[1, 0], [0, 1]] if determinant == 1 else [[1, 0], [0, -1]]
        permutation = _natural_node_permutation(natural)
        transformed = _transformed_case(
            case,
            _transform_nodes(nodes, frame, permutation),
            "d4",
        )
        matrices = _element_matrices(transformed, material)
        transform5 = _nodal_transform(_component_transform_5(frame), permutation)
        transform6 = _nodal_transform(_component_transform_6(frame), permutation)
        d4_k5_count += int(matrices["K5"] == _congruence(base_k5, transform5))
        d4_k24_count += int(matrices["K24"] == _congruence(base_k24, transform6))

    # Complete orientation reversal uses the other right-handed tangent/normal
    # flip than the D4 reflection convention above and is therefore independent.
    reversal_frame = [[1, 0], [0, -1]]
    reversal_permutation = [0, 3, 2, 1]
    reversed_case = _transformed_case(
        case,
        _transform_nodes(nodes, reversal_frame, reversal_permutation),
        "orientation_reversal",
    )
    reversed_matrices = _element_matrices(reversed_case, material)
    reversal5 = _nodal_transform(
        _component_transform_5(reversal_frame), reversal_permutation
    )
    reversal6 = _nodal_transform(
        _component_transform_6(reversal_frame), reversal_permutation
    )

    frame = [[Fraction(3, 5), Fraction(-4, 5)], [Fraction(4, 5), Fraction(3, 5)]]
    frame5 = _nodal_transform(_component_transform_5(frame))
    frame6 = _nodal_transform(_component_transform_6(frame))

    origin_case = _transformed_case(
        case,
        _transform_nodes(nodes, [[1, 0], [0, 1]], shift=(Fraction(7, 3), Fraction(-5, 4))),
        "origin",
    )
    origin_matrices = _element_matrices(origin_case, material)

    unit_k5, unit_k24 = True, True
    unit_scales = [Fraction(1, 1000), Fraction(1000)]
    for scale in unit_scales:
        scaled_case = _transformed_case(
            case,
            _transform_nodes(nodes, [[1, 0], [0, 1]], scale=scale),
            f"unit_{scale}",
        )
        scaled_matrices = _element_matrices(scaled_case, _scaled_material(material, scale))
        scale5 = _unit_coordinate_transform(5, scale)
        scale6 = _unit_coordinate_transform(6, scale)
        expected5 = _scale(
            _congruence(base_k5, _inverse(scale5)), scale
        )
        expected6 = _scale(
            _congruence(base_k24, _inverse(scale6)), scale
        )
        unit_k5 = unit_k5 and scaled_matrices["K5"] == expected5
        unit_k24 = unit_k24 and scaled_matrices["K24"] == expected6

    return {
        "d4_k24_congruence": d4_k24_count == 8,
        "d4_k24_count": d4_k24_count,
        "d4_k5_congruence": d4_k5_count == 8,
        "d4_k5_count": d4_k5_count,
        "frame_k24_congruence": _common_frame_embedding_covariance(
            base_k24, frame6
        ),
        "frame_k5_congruence": _common_frame_embedding_covariance(base_k5, frame5),
        "orientation_reversal_k24_congruence": reversed_matrices["K24"]
        == _congruence(base_k24, reversal6),
        "orientation_reversal_k5_congruence": reversed_matrices["K5"]
        == _congruence(base_k5, reversal5),
        "origin_k24_invariant": origin_matrices["K24"] == base_k24,
        "origin_k5_invariant": origin_matrices["K5"] == base_k5,
        "unit_k24_dimensional_congruence": unit_k24,
        "unit_k5_dimensional_congruence": unit_k5,
        "unit_scales": ["1/1000", "1000"],
    }


def _support_reaction_certificate(k0: Matrix, k_num: Matrix, k24: Matrix) -> dict[str, object]:
    t5, qd = _selectors()
    p5 = _multiply(t5, _transpose(t5))
    pd = _multiply(qd, _transpose(qd))
    sample = [Q3.make(Fraction(index - 11, 7)) for index in range(24)]
    wg = _matvec(k0, sample)
    numerical = _matvec(k_num, sample)
    total = _matvec(k24, sample)
    wg_physical = _matvec(p5, wg)
    wg_drill = _matvec(pd, wg)
    numerical_physical = _matvec(p5, numerical)
    numerical_drill = _matvec(pd, numerical)
    total_physical = _matvec(p5, total)
    total_drill = _matvec(pd, total)
    primary_support_row = [ZERO for _ in range(24)]
    primary_support_row[0] = ONE
    return {
        "primary_support": {
            "a_PD_zero": not any(_multiply([primary_support_row], pd)[0]),
            "a_P5_equals_a": _multiply([primary_support_row], p5)[0]
            == primary_support_row,
            "definition": "a*QD=0",
        },
        "projectors": {
            "P5_PD_zero": _multiply(p5, pd) == _zeros(24, 24),
            "P5_plus_PD_I24": _add(p5, pd) == _identity(24),
            "P5_symmetric_idempotent": p5 == _transpose(p5)
            and _multiply(p5, p5) == p5,
            "PD_symmetric_idempotent": pd == _transpose(pd)
            and _multiply(pd, pd) == pd,
            "p5_sha256": _matrix_digest(p5)["sha256"],
            "pd_sha256": _matrix_digest(pd)["sha256"],
        },
        "reaction_separation": {
            "numerical_drill": _vector_digest(numerical_drill),
            "numerical_physical": _vector_digest(numerical_physical),
            "projected_parts_recombine": _vadd(total_physical, total_drill) == total,
            "total_equals_wg_plus_numerical": _vadd(wg, numerical) == total,
            "total_drill": _vector_digest(total_drill),
            "total_physical": _vector_digest(total_physical),
            "wg_drill_exact_zero": not any(wg_drill),
            "wg_physical": _vector_digest(wg_physical),
        },
        "reporting": [
            "WG_PHYSICAL_RECOVERY",
            "PROJECTED_TOTAL_REACTION",
            "PROJECTED_PL_HG_REACTION",
        ],
    }


def _case_certificate(
    case: dict[str, object], constitutive: Matrix, material: dict[str, object]
) -> dict[str, object]:
    e = _fraction(material["E"])
    nu = _fraction(material["nu"])
    thickness = _fraction(material["t"])
    shear_modulus = e / (2 * (1 + nu))
    epsilon = _fraction(material["epsilon_hg"])
    core = _assemble_core(case, constitutive)
    numerical = _numerical_operators(case, shear_modulus, thickness, epsilon)
    t5, qd = _selectors()
    k5 = core["K5"]
    if not isinstance(k5, list):
        raise TypeError("K5")
    k0 = _multiply(_multiply(t5, k5), _transpose(t5))
    k_total = _add(k0, numerical["K_num"])
    kpp = _multiply(_multiply(_transpose(t5), k_total), t5)
    kpd = _multiply(_multiply(_transpose(t5), k_total), qd)
    kdp = _transpose(kpd)
    kdd = _multiply(_multiply(_transpose(qd), k_total), qd)
    schur = _sub(kpp, _multiply(_multiply(kpd, _inverse(kdd)), kdp))
    core_coupling_q = _multiply(t5, core["Q"])
    multiplier_coupling_q = _transpose(numerical["B"])
    internal = _block_diagonal(core["D"], _scale(numerical["M"], -1 / shear_modulus))
    complete_coupling = [
        core_row + multiplier_row
        for core_row, multiplier_row in zip(core_coupling_q, multiplier_coupling_q)
    ]
    condensed_from_mixed = _sub(
        numerical["K_hg"],
        _multiply(_multiply(complete_coupling, _inverse(internal)), _transpose(complete_coupling)),
    )
    rigid20 = _rigid_vectors_20(case)
    rigid24 = _rigid_vectors_24(case)
    patch_images = {
        name: {
            "constraint_zero": not any(_matvec(numerical["C"], vector)),
            "hourglass_zero": not any(_matvec(numerical["K_hg"], vector)),
            "numerical_stiffness_zero": not any(_matvec(numerical["K_num"], vector)),
        }
        for name, vector in _patch_vectors(case).items()
    }
    physical_patches = _physical_patch_certificate(
        case, core, k5, numerical["K_num"], constitutive
    )
    full_covariance = _full_covariance_certificate(
        case, k5, k_total, material
    )
    support_reaction = _support_reaction_certificate(
        k0, numerical["K_num"], k_total
    )
    gamma = _gamma_row(case)
    if any(value.b for value in gamma):
        raise ValueError("residual row unexpectedly left Q")
    core_ranks = {
        name: _rank(core[name]) for name in ("F", "Gq", "H", "D", "K5")
    }
    rigid_images_zero = {
        name: not any(_matvec(k_total, vector)) for name, vector in rigid24.items()
    }
    agreement = {
        "core_ranks": core_ranks,
        "internal_block_rank": _rank(internal),
        "kdd_ldl_positive": _positive_rational_pivots(kdd),
        "local_physical_schur_equals_k5": schur == k5,
        "nullity": 24 - _rank(k_total),
        "numerical_patch_actions_zero": {
            name: all(record.values()) for name, record in patch_images.items()
        },
        "physical_patches": {
            name: {
                key: record[key]
                for key in ("energy_exact", "gauss_strain_exact", "numerical_zero", "recovery_exact")
            }
            for name, record in physical_patches.items()
        },
        "r_map_rank": _rank(numerical["R"]),
        "rank": _rank(k_total),
        "residual_drill_row": [str(value.a) for value in gamma],
        "rigid_images_zero": rigid_images_zero,
    }
    return {
        "agreement": agreement,
        "case_id": case["id"],
        "core": {
            "matrix_digests": {
                name: _matrix_digest(core[name])
                for name in ("F", "Gq", "H", "D", "K5")
                if isinstance(core[name], list)
            },
            "ranks": core_ranks,
            "rigid_images_zero": {
                name: not any(_matvec(k5, vector)) for name, vector in rigid20.items()
            },
        },
        "geometry": {
            "gamma": [value.pair() for value in gamma],
            "jacobian_modes": [str(value) for value in _geometry_modes(case["coordinates"])["j"]],
        },
        "full_covariance": full_covariance,
        "local_algebra": {
            "C_rank": _rank(numerical["C"]),
            "R_rank": _rank(numerical["R"]),
            "actual_38_field_internal_rank": _rank(internal),
            "kdd_rank": _rank(kdd),
            "kdd_ldl_positive": _positive_rational_pivots(kdd),
            "mixed_condensed_equals_total": condensed_from_mixed == k_total,
            "schur_equals_k5": schur == k5,
            "total_rank": _rank(k_total),
            "total_nullity": 24 - _rank(k_total),
            "total_rigid_images_zero": rigid_images_zero,
        },
        "numerical": {
            "B_equals_M_C": numerical["B"] == _multiply(numerical["M"], numerical["C"]),
            "matrix_digests": {
                name: _matrix_digest(numerical[name])
                for name in ("C", "M", "B", "R", "Kdd", "K_num")
            },
            "patches": patch_images,
        },
        "physical_patches": physical_patches,
        "support_reaction": support_reaction,
    }


def build_certificate(cases_path: Path = CASES_PATH) -> dict[str, object]:
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    if cases.get("schema") != "anysolver.s4.e4-pl-q1a-cases-v1":
        raise ValueError("case schema mismatch")
    constitutive = _constitutive(cases["material"])
    registered_material = cases["material"]
    expected_constitutive = _isotropic_constitutive(
        _fraction(registered_material["E"]),
        _fraction(registered_material["nu"]),
        _fraction(registered_material["t"]),
    )
    if constitutive != expected_constitutive:
        raise ValueError("registered resultant matrix disagrees with isotropic derivation")
    results = [_case_certificate(case, constitutive, cases["material"]) for case in cases["geometries"]]
    fatal = []
    for result in results:
        ranks = result["core"]["ranks"]
        algebra = result["local_algebra"]
        if ranks != {"D": 35, "F": 14, "Gq": 14, "H": 21, "K5": 14}:
            fatal.append(f"{result['case_id']}: core rank")
        if not (
            algebra["R_rank"] == 4
            and algebra["actual_38_field_internal_rank"] == 38
            and algebra["kdd_rank"] == 4
            and algebra["kdd_ldl_positive"]
            and algebra["mixed_condensed_equals_total"]
            and algebra["schur_equals_k5"]
            and algebra["total_rank"] == 18
            and algebra["total_nullity"] == 6
            and all(algebra["total_rigid_images_zero"].values())
        ):
            fatal.append(f"{result['case_id']}: local algebra")
        if not all(
            all(patch.values()) for patch in result["numerical"]["patches"].values()
        ):
            fatal.append(f"{result['case_id']}: numerical patch")
        if not all(
            all(
                patch[key]
                for key in ("energy_exact", "gauss_strain_exact", "numerical_zero", "recovery_exact")
            )
            for patch in result["physical_patches"].values()
        ):
            fatal.append(f"{result['case_id']}: physical patch or recovery")
        covariance = result["full_covariance"]
        if not (
            covariance["d4_k5_count"] == 8
            and covariance["d4_k24_count"] == 8
            and all(
                covariance[key]
                for key in (
                    "d4_k5_congruence",
                    "d4_k24_congruence",
                    "orientation_reversal_k5_congruence",
                    "orientation_reversal_k24_congruence",
                    "frame_k5_congruence",
                    "frame_k24_congruence",
                    "origin_k5_invariant",
                    "origin_k24_invariant",
                    "unit_k5_dimensional_congruence",
                    "unit_k24_dimensional_congruence",
                )
            )
        ):
            fatal.append(f"{result['case_id']}: full covariance")
        support = result["support_reaction"]
        if not (
            all(
                support["projectors"][key]
                for key in (
                    "P5_PD_zero",
                    "P5_plus_PD_I24",
                    "P5_symmetric_idempotent",
                    "PD_symmetric_idempotent",
                )
            )
            and support["primary_support"]["a_PD_zero"]
            and support["primary_support"]["a_P5_equals_a"]
            and all(
                support["reaction_separation"][key]
                for key in (
                    "projected_parts_recombine",
                    "total_equals_wg_plus_numerical",
                    "wg_drill_exact_zero",
                )
            )
        ):
            fatal.append(f"{result['case_id']}: support or reaction separation")
    agreement = {result["case_id"]: result["agreement"] for result in results}
    if not fatal:
        terminal_hint = "PROVISIONAL_GO_E4_PL_Q1B_NONINTRUSION_STABILITY_LOCKING_PLAN"
    elif any(
        marker in item
        for item in fatal
        for marker in ("physical patch or recovery", "full covariance")
    ):
        terminal_hint = "NO_GO_E4_PL_Q1A_PATCH_OR_COVARIANCE"
    elif any("local algebra" in item or "core rank" in item for item in fatal):
        terminal_hint = "NO_GO_E4_PL_Q1A_LOCAL_ALGEBRA"
    else:
        terminal_hint = "UNCLASSIFIED_E4_PL_Q1A_PLANAR_IDENTITY_AND_LOCAL_ALGEBRA"
    return {
        "agreement": agreement,
        "agreement_sha256": _sha(_canonical(agreement)),
        "candidate_id": cases["candidate_id"],
        "cases": results,
        "fatal": fatal,
        "reference_role": "CORROBORATION_NOT_INDEPENDENT_ORACLE",
        "schema": "anysolver.s4.e4-pl-q1a-reference-certificate-v1",
        "terminal_hint": terminal_hint,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=CASES_PATH)
    arguments = parser.parse_args(argv)
    certificate = build_certificate(arguments.cases)
    sys.stdout.buffer.write(_canonical(certificate))
    return 0 if not certificate["fatal"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
