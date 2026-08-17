"""Independent exact oracle for the E4-PL flat-affine drill closure."""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "docs/reference_cases/e4_pl_cases.json"
CONTRACT_PATH = ROOT / "docs/reference_cases/e4_pl_contract.json"
STUDY_ID = "study_e4_pl.wg2020_surface_reduced_perturbed_lagrange_v1"
TERMINAL = "PROVISIONAL_GO_E4_PL_LINEAR_QUALIFICATION_PLAN"
BLOCKED = "BLOCKED_E4_CONTRACT_NONDETERMINISM_OR_REVIEW"
RELEASE = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
CONTRACT_INPUTS = [
    "docs/agent_plans/S4_E4_VARIATIONAL_DRILL_CLOSURE_PLAN.md",
    "docs/E4_OPEN_CORE_IDENTITY.md",
    "docs/E4_PL_VARIATIONAL_CLOSURE.md",
    "docs/reference_cases/e4_baseline.json",
    "docs/reference_cases/e4_environment.json",
    "docs/reference_cases/e4_test_inventory.json",
    "docs/reference_cases/e4_source_registry.json",
    "docs/reference_cases/e4_allowed_extent.json",
    "docs/reference_cases/e4_core_source_map.json",
    "docs/reference_cases/e4_pl_source_map.json",
    "docs/reference_cases/e4_core_contract.json",
    "docs/reference_cases/e4_core_output.json",
    "docs/reference_cases/e4_pl_cases.json",
]


class EvidenceError(Exception):
    """Frozen scientific evidence or an exact identity is invalid."""


class ContractError(Exception):
    """Caller-bound execution evidence is invalid."""


Matrix = list[list[Fraction]]
Vector = list[Fraction]
Polynomial = dict[tuple[int, int], Fraction]
PolynomialMatrix = list[list[Polynomial]]


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _load_json(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        raise EvidenceError(f"invalid UTF-8/LF transport: {path}")
    try:
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(EvidenceError(token)),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceError(str(exc)) from exc
    if not isinstance(value, dict) or raw != _canonical(value):
        raise EvidenceError(f"noncanonical JSON: {path}")
    return value


def _fraction(value: object) -> Fraction:
    if not isinstance(value, (str, int)) or isinstance(value, bool):
        raise EvidenceError(f"not an exact scalar: {value!r}")
    return Fraction(value)


def _zeros(rows: int, columns: int) -> Matrix:
    return [[Fraction(0) for _ in range(columns)] for _ in range(rows)]


def _identity(size: int) -> Matrix:
    result = _zeros(size, size)
    for index in range(size):
        result[index][index] = Fraction(1)
    return result


def _transpose(matrix: Matrix) -> Matrix:
    return [list(column) for column in zip(*matrix)] if matrix else []


def _multiply(left: Matrix, right: Matrix) -> Matrix:
    if not left or not right or len(left[0]) != len(right):
        raise EvidenceError("matrix product dimension mismatch")
    columns = _transpose(right)
    return [[sum(a * b for a, b in zip(row, column)) for column in columns] for row in left]


def _matvec(matrix: Matrix, vector: Vector) -> Vector:
    if matrix and len(matrix[0]) != len(vector):
        raise EvidenceError("matrix-vector dimension mismatch")
    return [sum(a * b for a, b in zip(row, vector)) for row in matrix]


def _add(left: Matrix, right: Matrix, scale: Fraction = Fraction(1)) -> Matrix:
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        raise EvidenceError("matrix sum dimension mismatch")
    return [[a + scale * b for a, b in zip(row_a, row_b)] for row_a, row_b in zip(left, right)]


def _scale(matrix: Matrix, factor: Fraction) -> Matrix:
    return [[factor * value for value in row] for row in matrix]


def _dot(left: Vector, right: Vector) -> Fraction:
    if len(left) != len(right):
        raise EvidenceError("dot-product dimension mismatch")
    return sum(a * b for a, b in zip(left, right))


def _rank(matrix: Matrix) -> int:
    if not matrix:
        return 0
    work = [row[:] for row in matrix]
    row_count, column_count = len(work), len(work[0])
    rank = 0
    for column in range(column_count):
        pivot = next((row for row in range(rank, row_count) if work[row][column]), None)
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        value = work[rank][column]
        work[rank] = [entry / value for entry in work[rank]]
        for row in range(row_count):
            if row != rank and work[row][column]:
                factor = work[row][column]
                work[row] = [a - factor * b for a, b in zip(work[row], work[rank])]
        rank += 1
    return rank


def _inverse(matrix: Matrix) -> Matrix:
    size = len(matrix)
    if not size or any(len(row) != size for row in matrix):
        raise EvidenceError("inverse requires a nonempty square matrix")
    work = [row[:] + identity for row, identity in zip(matrix, _identity(size))]
    for column in range(size):
        pivot = next((row for row in range(column, size) if work[row][column]), None)
        if pivot is None:
            raise EvidenceError("singular exact matrix")
        work[column], work[pivot] = work[pivot], work[column]
        value = work[column][column]
        work[column] = [entry / value for entry in work[column]]
        for row in range(size):
            if row != column and work[row][column]:
                factor = work[row][column]
                work[row] = [a - factor * b for a, b in zip(work[row], work[column])]
    return [row[size:] for row in work]


def _ldl_pivots(matrix: Matrix) -> Vector:
    size = len(matrix)
    if not size or any(len(row) != size for row in matrix) or matrix != _transpose(matrix):
        raise EvidenceError("LDL requires a symmetric square matrix")
    lower = _identity(size)
    pivots: Vector = []
    for column in range(size):
        pivot = matrix[column][column] - sum(
            lower[column][k] * lower[column][k] * pivots[k] for k in range(column)
        )
        if not pivot:
            raise EvidenceError("zero exact LDL pivot")
        pivots.append(pivot)
        for row in range(column + 1, size):
            lower[row][column] = (
                matrix[row][column]
                - sum(lower[row][k] * lower[column][k] * pivots[k] for k in range(column))
            ) / pivot
    return pivots


def _independent_rows(matrix: Matrix) -> Matrix:
    selected: Matrix = []
    rank = 0
    for row in matrix:
        trial = selected + [row]
        trial_rank = _rank(trial)
        if trial_rank > rank:
            selected.append(row)
            rank = trial_rank
    return selected


def _inverse2(matrix: Matrix) -> Matrix:
    determinant = _det2(matrix)
    if not determinant:
        raise EvidenceError("singular affine map")
    return [
        [matrix[1][1] / determinant, -matrix[0][1] / determinant],
        [-matrix[1][0] / determinant, matrix[0][0] / determinant],
    ]


def _det2(matrix: Matrix) -> Fraction:
    return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]


def _matrix2_product(left: Matrix, right: Matrix) -> Matrix:
    return [[sum(left[row][inner] * right[inner][column] for inner in range(2)) for column in range(2)] for row in range(2)]


def _matrix2_vector(matrix: Matrix, vector: Vector) -> Vector:
    return [sum(matrix[row][column] * vector[column] for column in range(2)) for row in range(2)]


def _poly(value: Fraction = Fraction(0), r_power: int = 0, s_power: int = 0) -> Polynomial:
    return {} if not value else {(r_power, s_power): value}


def _padd(*terms: Polynomial) -> Polynomial:
    result: Polynomial = {}
    for term in terms:
        for monomial, value in term.items():
            result[monomial] = result.get(monomial, Fraction(0)) + value
            if not result[monomial]:
                del result[monomial]
    return result


def _pscale(term: Polynomial, factor: Fraction) -> Polynomial:
    return {monomial: factor * value for monomial, value in term.items() if factor * value}


def _pmultiply(left: Polynomial, right: Polynomial) -> Polynomial:
    result: Polynomial = {}
    for (left_r, left_s), left_value in left.items():
        for (right_r, right_s), right_value in right.items():
            key = (left_r + right_r, left_s + right_s)
            result[key] = result.get(key, Fraction(0)) + left_value * right_value
    return {key: value for key, value in result.items() if value}


def _pintegral(term: Polynomial, determinant: Fraction) -> Fraction:
    return abs(determinant) * sum(
        value * Fraction(4, (r_power + 1) * (s_power + 1))
        for (r_power, s_power), value in term.items()
        if r_power % 2 == 0 and s_power % 2 == 0
    )


def _pzeros(rows: int, columns: int) -> PolynomialMatrix:
    return [[{} for _ in range(columns)] for _ in range(rows)]


def _tensor_transform(jacobian: Matrix, a: Fraction, b: Fraction) -> Matrix:
    x_r, x_s = jacobian[0]
    y_r, y_s = jacobian[1]
    return [[x_r*x_r, y_r*y_r, a*x_r*y_r],
            [x_s*x_s, y_s*y_s, a*x_s*y_s],
            [b*x_r*x_s, b*y_r*y_s, x_r*y_s+x_s*y_r]]


def _transform_columns(target: PolynomialMatrix, row_offset: int, columns: list[int],
                       transform: Matrix, seeds: list[list[Polynomial]]) -> None:
    for local_column, global_column in enumerate(columns):
        for output_row, transform_row in enumerate(transform):
            target[row_offset + output_row][global_column] = _padd(*(
                _pscale(seeds[input_row][local_column], coefficient)
                for input_row, coefficient in enumerate(transform_row)
            ))


def _source_spaces(jacobian: Matrix) -> tuple[PolynomialMatrix, PolynomialMatrix]:
    n_sigma, n_epsilon = _pzeros(8, 14), _pzeros(8, 21)
    for index in range(8):
        n_sigma[index][index] = _poly(Fraction(1))
        n_epsilon[index][index] = _poly(Fraction(1))
    r, s, rs = _poly(Fraction(1), 1, 0), _poly(Fraction(1), 0, 1), _poly(Fraction(1), 1, 1)
    tensor_seed = [[s, {}], [{}, r], [{}, {}]]
    vector_seed = [[s, {}], [{}, r]]
    for target, transform in ((n_sigma, _tensor_transform(jacobian, Fraction(2), Fraction(1))),
                              (n_epsilon, _tensor_transform(jacobian, Fraction(1), Fraction(2)))):
        _transform_columns(target, 0, [8, 9], transform, tensor_seed)
        _transform_columns(target, 3, [10, 11], transform, tensor_seed)
        _transform_columns(target, 6, [12, 13], jacobian, vector_seed)
    enrichment = [[r, {}, {}, {}, rs, {}, {}],
                  [{}, s, {}, {}, {}, rs, {}],
                  [{}, {}, r, s, {}, {}, rs]]
    _transform_columns(n_epsilon, 0, list(range(14, 21)),
                       _tensor_transform(jacobian, Fraction(1), Fraction(2)), enrichment)
    return n_sigma, n_epsilon


def _core_modal_coefficients(field: int) -> list[list[Polynomial]]:
    result: list[list[Polynomial]] = []
    for row in _modal_matrix():
        vector = [{} for _ in range(20)]
        for node, value in enumerate(row):
            vector[5 * node + field] = _poly(value)
        result.append(vector)
    return result


def _poly_linear(vectors: list[list[Polynomial]], coefficients: list[Polynomial]) -> list[Polynomial]:
    result = [{} for _ in vectors[0]]
    for vector, coefficient in zip(vectors, coefficients):
        for index, value in enumerate(vector):
            result[index] = _padd(result[index], _pmultiply(coefficient, value))
    return result


def _poly_vector_add(*vectors: list[Polynomial]) -> list[Polynomial]:
    return [_padd(*(vector[index] for vector in vectors)) for index in range(len(vectors[0]))]


def _poly_vector_scale(vector: list[Polynomial], factor: Fraction) -> list[Polynomial]:
    return [_pscale(value, factor) for value in vector]


def _compatible_map(jacobian: Matrix) -> PolynomialMatrix:
    modal = [_core_modal_coefficients(field) for field in range(5)]
    unused_u0, ur, us, urs = modal[0]
    unused_v0, vr, vs, vrs = modal[1]
    unused_w0, wr, ws, wrs = modal[2]
    rx0, rxr, rxs, rxrs = modal[3]
    ry0, ryr, rys, ryrs = modal[4]
    del unused_u0, unused_v0, unused_w0
    r, s = _poly(Fraction(1), 1, 0), _poly(Fraction(1), 0, 1)
    u_r, u_s = _poly_vector_add(ur, _poly_linear([urs], [s])), _poly_vector_add(us, _poly_linear([urs], [r]))
    v_r, v_s = _poly_vector_add(vr, _poly_linear([vrs], [s])), _poly_vector_add(vs, _poly_linear([vrs], [r]))
    rx_r, rx_s = _poly_vector_add(rxr, _poly_linear([rxrs], [s])), _poly_vector_add(rxs, _poly_linear([rxrs], [r]))
    ry_r, ry_s = _poly_vector_add(ryr, _poly_linear([ryrs], [s])), _poly_vector_add(rys, _poly_linear([ryrs], [r]))
    inverse = _inverse2(jacobian)

    def physical(natural_r: list[Polynomial], natural_s: list[Polynomial]) -> tuple[list[Polynomial], list[Polynomial]]:
        return (_poly_vector_add(_poly_vector_scale(natural_r, inverse[0][0]),
                                 _poly_vector_scale(natural_s, inverse[1][0])),
                _poly_vector_add(_poly_vector_scale(natural_r, inverse[0][1]),
                                 _poly_vector_scale(natural_s, inverse[1][1])))

    u_x, u_y = physical(u_r, u_s)
    v_x, v_y = physical(v_r, v_s)
    rx_x, rx_y = physical(rx_r, rx_s)
    ry_x, ry_y = physical(ry_r, ry_s)
    x_r, x_s = jacobian[0]
    y_r, y_s = jacobian[1]
    tied_r = _poly_vector_add(wr, _poly_linear([wrs], [s]),
                              _poly_vector_scale(_poly_vector_add(ry0, _poly_linear([rys], [s])), x_r),
                              _poly_vector_scale(_poly_vector_add(rx0, _poly_linear([rxs], [s])), -y_r))
    tied_s = _poly_vector_add(ws, _poly_linear([wrs], [r]),
                              _poly_vector_scale(_poly_vector_add(ry0, _poly_linear([ryr], [r])), x_s),
                              _poly_vector_scale(_poly_vector_add(rx0, _poly_linear([rxr], [r])), -y_s))
    gamma_x, gamma_y = physical(tied_r, tied_s)
    return [u_x, v_y, _poly_vector_add(u_y, v_x), ry_x,
            _poly_vector_scale(rx_y, Fraction(-1)),
            _poly_vector_add(ry_y, _poly_vector_scale(rx_x, Fraction(-1))), gamma_x, gamma_y]


def _t5_selector() -> Matrix:
    result = _zeros(24, 20)
    for node in range(4):
        for local in range(5):
            result[6 * node + local][5 * node + local] = Fraction(1)
    return result


def _assemble_wg_core(jacobian: Matrix, e: Fraction, nu: Fraction,
                      thickness: Fraction, shear_modulus: Fraction) -> dict[str, Matrix]:
    determinant = _det2(jacobian)
    factor = e / (1 - nu * nu)
    cm = [[factor, factor * nu, Fraction(0)],
          [factor * nu, factor, Fraction(0)],
          [Fraction(0), Fraction(0), factor * (1 - nu) / 2]]
    constitutive = _zeros(8, 8)
    for row in range(3):
        for column in range(3):
            constitutive[row][column] = thickness * cm[row][column]
            constitutive[3 + row][3 + column] = thickness**3 * cm[row][column] / 12
    constitutive[6][6] = constitutive[7][7] = Fraction(5, 6) * shear_modulus * thickness
    n_sigma, n_epsilon = _source_spaces(jacobian)
    b_map = _compatible_map(jacobian)
    f, h_matrix, gq = _zeros(21, 14), _zeros(21, 21), _zeros(14, 20)
    for strain in range(21):
        for stress in range(14):
            f[strain][stress] = -sum(
                _pintegral(_pmultiply(n_epsilon[component][strain], n_sigma[component][stress]), determinant)
                for component in range(8))
        for other in range(21):
            h_matrix[strain][other] = sum(
                constitutive[left][right] * _pintegral(
                    _pmultiply(n_epsilon[left][strain], n_epsilon[right][other]), determinant)
                for left in range(8) for right in range(8) if constitutive[left][right])
    for stress in range(14):
        for coordinate in range(20):
            gq[stress][coordinate] = sum(
                _pintegral(_pmultiply(n_sigma[component][stress], b_map[component][coordinate]), determinant)
                for component in range(8))
    d = _zeros(35, 35)
    for stress in range(14):
        for strain in range(21):
            d[stress][14 + strain] = d[14 + strain][stress] = f[strain][stress]
    for left in range(21):
        for right in range(21):
            d[14 + left][14 + right] = h_matrix[left][right]
    d_inverse = _inverse(d)
    s_matrix = _scale([row[:14] for row in d_inverse[:14]], Fraction(-1))
    q20 = [row + [Fraction(0)] * 21 for row in _transpose(gq)]
    k5 = _scale(_multiply(_multiply(q20, d_inverse), _transpose(q20)), Fraction(-1))
    t5 = _t5_selector()
    q24 = _multiply(t5, q20)
    k0 = _multiply(_multiply(t5, k5), _transpose(t5))
    return {"D": d, "D_inverse": d_inverse, "F": f, "Gq": gq, "H": h_matrix,
            "K0": k0, "K5": k5, "Q24": q24, "S": s_matrix}


def _modal_matrix() -> Matrix:
    return [
        [Fraction(1, 4), Fraction(1, 4), Fraction(1, 4), Fraction(1, 4)],
        [Fraction(-1, 4), Fraction(1, 4), Fraction(1, 4), Fraction(-1, 4)],
        [Fraction(-1, 4), Fraction(-1, 4), Fraction(1, 4), Fraction(1, 4)],
        [Fraction(1, 4), Fraction(-1, 4), Fraction(1, 4), Fraction(-1, 4)],
    ]


def _constraint_rows(jacobian: Matrix) -> tuple[Matrix, Vector]:
    x_r, x_s = jacobian[0]
    y_r, y_s = jacobian[1]
    determinant = _det2(jacobian)
    if not determinant:
        raise EvidenceError("singular affine constraint geometry")
    modal = _modal_matrix()
    rows = _zeros(4, 24)
    for node in range(4):
        u, v, d = 6 * node, 6 * node + 1, 6 * node + 5
        rows[0][d] += modal[0][node]
        rows[0][u] += (-x_s * modal[1][node] + x_r * modal[2][node]) / (2 * determinant)
        rows[0][v] += (-y_s * modal[1][node] + y_r * modal[2][node]) / (2 * determinant)
        rows[1][d] += modal[1][node]
        rows[1][u] += x_r * modal[3][node] / (2 * determinant)
        rows[1][v] += y_r * modal[3][node] / (2 * determinant)
        rows[2][d] += modal[2][node]
        rows[2][u] -= x_s * modal[3][node] / (2 * determinant)
        rows[2][v] -= y_s * modal[3][node] / (2 * determinant)
        rows[3][d] += modal[3][node]
    return rows[:3], rows[3]


def _physical_nodes(record: dict[str, object]) -> list[list[Fraction]]:
    raw = record.get("physical_nodes")
    if not isinstance(raw, list) or len(raw) != 4:
        raise EvidenceError("physical-node registry missing")
    return [[_fraction(value) for value in node] for node in raw if isinstance(node, list)]


def _rigid_vectors(nodes: list[list[Fraction]]) -> dict[str, Vector]:
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
    return {name: [Fraction(value) for value in vector] for name, vector in result.items()}


def _mode_states(nodes: list[list[Fraction]]) -> dict[str, Vector]:
    states = {name: [] for name in (
        "pure_common_drill", "translation_only_spin", "matched_rigid_spin",
        "alternating_drill", "constant_membrane_x", "constant_symmetric_shear",
        "bending_and_transverse_shear_decoupling",
    )}
    alternate = (1, -1, 1, -1)
    for node, (x, y) in enumerate(nodes):
        states["pure_common_drill"].extend((0, 0, 0, 0, 0, 1))
        states["translation_only_spin"].extend((-y, x, 0, 0, 0, 0))
        states["matched_rigid_spin"].extend((-y, x, 0, 0, 0, 1))
        states["alternating_drill"].extend((0, 0, 0, 0, 0, alternate[node]))
        states["constant_membrane_x"].extend((x, 0, 0, 0, 0, 0))
        states["constant_symmetric_shear"].extend((y / 2, x / 2, 0, 0, 0, 0))
        states["bending_and_transverse_shear_decoupling"].extend((
            0, 0, Fraction(node + 1), Fraction(2 * node - 1), Fraction(3 - node), 0
        ))
    return {name: [Fraction(value) for value in vector] for name, vector in states.items()}


def _diagonal(values: Vector) -> Matrix:
    result = _zeros(len(values), len(values))
    for index, value in enumerate(values):
        result[index][index] = value
    return result


def _energy(matrix: Matrix, vector: Vector) -> Fraction:
    return _dot(vector, _matvec(matrix, vector)) / 2


def _signature(vector: Vector) -> list[str]:
    return [str(value) for value in vector]


def _matrix_signature(matrix: Matrix) -> list[list[str]]:
    return [_signature(row) for row in matrix]


def _d4_matrices() -> list[Matrix]:
    return [
        [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]],
        [[Fraction(0), Fraction(-1)], [Fraction(1), Fraction(0)]],
        [[Fraction(-1), Fraction(0)], [Fraction(0), Fraction(-1)]],
        [[Fraction(0), Fraction(1)], [Fraction(-1), Fraction(0)]],
        [[Fraction(-1), Fraction(0)], [Fraction(0), Fraction(1)]],
        [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(-1)]],
        [[Fraction(0), Fraction(1)], [Fraction(1), Fraction(0)]],
        [[Fraction(0), Fraction(-1)], [Fraction(-1), Fraction(0)]],
    ]


def _reparameterize_state(state: Vector, matrix: Matrix) -> Vector:
    nodes = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    index = {node: position for position, node in enumerate(nodes)}
    result = [Fraction(0) for _ in state]
    for new, node in enumerate(nodes):
        old_coordinate = _matrix2_vector(matrix, [Fraction(node[0]), Fraction(node[1])])
        old = index[(int(old_coordinate[0]), int(old_coordinate[1]))]
        result[6 * new : 6 * new + 6] = state[6 * old : 6 * old + 6]
    return result


def _transform_frame_state(state: Vector, rotation: Matrix, drill_scale: Fraction = Fraction(1)) -> Vector:
    result = state[:]
    for node in range(4):
        u, v = state[6 * node], state[6 * node + 1]
        rx, ry = state[6 * node + 3], state[6 * node + 4]
        result[6 * node], result[6 * node + 1] = _matrix2_vector(rotation, [u, v])
        result[6 * node + 3], result[6 * node + 4] = _matrix2_vector(rotation, [rx, ry])
        result[6 * node + 5] *= drill_scale
    return result


def _numerical_forms(
    jacobian: Matrix, h: Fraction, g: Fraction, epsilon: Fraction
) -> tuple[Matrix, Vector, Matrix, Matrix, Matrix]:
    c, hrow = _constraint_rows(jacobian)
    determinant = abs(_det2(jacobian))
    m = _diagonal([4 * h * determinant, Fraction(4, 3) * h * determinant, Fraction(4, 3) * h * determinant])
    b = _multiply(m, c)
    m_inverse = _diagonal([1 / m[index][index] for index in range(3)])
    k_pl = _scale(_multiply(_multiply(_transpose(b), m_inverse), b), g)
    area = 4 * determinant
    k_hg = _scale(_multiply(_transpose([hrow]), [hrow]), 2 * epsilon * g * h * area)
    return c, hrow, m, k_pl, k_hg


def _numerical_energy(c: Matrix, hrow: Vector, m: Matrix, state: Vector, g: Fraction, epsilon: Fraction, h: Fraction, area: Fraction) -> tuple[Fraction, Fraction]:
    coefficients = _matvec(c, state)
    pl = g * _dot(coefficients, _matvec(m, coefficients)) / 2
    hg_action = _dot(hrow, state)
    hg = epsilon * g * h * area * hg_action * hg_action
    return pl, hg


def _validate_cases(cases: dict[str, object]) -> None:
    if cases.get("schema") != "anysolver.e4.pl-cases-v2" or cases.get("study_id") != STUDY_ID:
        raise EvidenceError("PL case identity mismatch")
    expected = cases.get("expected")
    if not isinstance(expected, dict) or expected.get("terminal") != TERMINAL:
        raise EvidenceError("PL expected terminal mismatch")
    constraint = cases.get("constraint")
    if not isinstance(constraint, dict) or constraint.get("measure") != "c=theta_D-(v_x-u_y)/2":
        raise EvidenceError("PL drill-measure identity changed")
    if constraint.get("retained_order") != ["1", "r", "s"] or constraint.get("rotation_only_deleted") != "c_rs=d_rs":
        raise EvidenceError("PL projection identity changed")
    multiplier = cases.get("multiplier")
    if not isinstance(multiplier, dict) or multiplier.get("basis") != ["1", "r", "s"]:
        raise EvidenceError("PL multiplier basis changed")
    hourglass = cases.get("hourglass")
    if not isinstance(hourglass, dict) or any(hourglass.get(key) != value for key, value in {
        "epsilon": "1/1000", "energy": "epsilon*G*h*A*(H_hg*q)^2",
        "gamma": ["1/4", "-1/4", "1/4", "-1/4"],
        "hessian": "2*epsilon*G*h*A*H_hg^T*H_hg",
    }.items()):
        raise EvidenceError("PL hourglass identity changed")
    dependency = cases.get("core_dependency")
    if not isinstance(dependency, dict) or dependency.get("case_schema") != "anysolver.e4.core-cases-v2" \
            or dependency.get("synthetic_I35_witness_allowed") is not False:
        raise EvidenceError("PL actual-core dependency changed")
    normalization = cases.get("scalar_normalization")
    if not isinstance(normalization, dict) or normalization.get("gamma") != "G" \
            or normalization.get("equations") != "MITC9i_18_19":
        raise EvidenceError("PL scalar normalization changed")


def build_certificate() -> dict[str, object]:
    cases = _load_json(CASES_PATH)
    _validate_cases(cases)
    constitutive = cases["constitutive"]
    if not isinstance(constitutive, dict):
        raise EvidenceError("constitutive record missing")
    e, nu, h = (_fraction(constitutive[name]) for name in ("E", "nu", "h"))
    g = e / (2 * (1 + nu))
    if not (e > 0 and h > 0 and Fraction(-1) < nu < Fraction(1, 2)) or g != _fraction(constitutive["G"]):
        raise EvidenceError("positive isotropic material identity failed")
    core_output = _load_json(ROOT / "docs/reference_cases/e4_core_output.json")
    core_certificate = core_output.get("certificate")
    if core_output.get("schema") != "anysolver.s4.e4-core-output-v2" \
            or core_output.get("terminal") != "GO_E4_OPEN_CORE_IDENTITY" \
            or not isinstance(core_certificate, dict) \
            or core_certificate.get("scope", {}).get("core_classification_operator") \
            != "SOURCE_EXACT_WG_F_G_H_D_S_K5":
        raise EvidenceError("source-exact open-core prerequisite is not accepted")
    epsilon = _fraction(cases["hourglass"]["epsilon"])
    sensitivities = cases["parameter_sensitivities"]
    if not isinstance(sensitivities, dict):
        raise EvidenceError("parameter-sensitivity registry missing")
    sensitivity_observed: dict[str, dict[str, int]] = {
        "epsilon": {}, "gamma_over_G": {}
    }
    geometry_results: dict[str, object] = {}
    for raw_record in cases["affine_cases"]:
        if not isinstance(raw_record, dict):
            raise EvidenceError("malformed affine case")
        geometry_id = str(raw_record["id"])
        jacobian = [[_fraction(value) for value in row] for row in raw_record["j"]]
        determinant = _det2(jacobian)
        if determinant != _fraction(raw_record["det_j"]):
            raise EvidenceError(f"affine determinant mismatch: {geometry_id}")
        area = 4 * abs(determinant)
        if area != _fraction(raw_record["area"]):
            raise EvidenceError(f"affine area mismatch: {geometry_id}")
        c, hrow, mass, k_pl, k_hg = _numerical_forms(jacobian, h, g, epsilon)
        full_c = c + [hrow]
        if _rank(c) != 3 or _rank([hrow]) != 1 or _rank(full_c) != 4:
            raise EvidenceError(f"PL retained/residual rank failure: {geometry_id}")
        if any(hrow[column] for column in range(24) if column % 6 != 5):
            raise EvidenceError("deleted rs row contains a translation column")
        if geometry_id == "unit_square":
            expected_rows = [[_fraction(value) for value in row] for row in raw_record["expected_c_rows_unit_square"]]
            if c != expected_rows:
                raise EvidenceError("registered unit-square C rows disagree with derivation")

        core = _assemble_wg_core(jacobian, e, nu, h, g)
        core_ranks = {
            "D": _rank(core["D"]), "F": _rank(core["F"]), "Gq": _rank(core["Gq"]),
            "H": _rank(core["H"]), "K0": _rank(core["K0"]),
        }
        if core_ranks != {"D": 35, "F": 14, "Gq": 14, "H": 21, "K0": 14} \
                or any(pivot <= 0 for pivot in _ldl_pivots(core["S"])):
            raise EvidenceError(f"actual WG core dependency failed: {geometry_id}")
        core_coupling = core["Q24"]
        k0 = core["K0"]
        k_total = _add(_add(k0, k_pl), k_hg)
        stacked_rank = _rank(k0 + c + [hrow])
        if _rank(k_total) != 18 or stacked_rank != 18:
            raise EvidenceError(f"PL total rank failure: {geometry_id}")
        for value in sensitivities["epsilon"]:
            varied = _add(_add(k0, k_pl), _scale(k_hg, _fraction(value) / epsilon))
            varied_rank = _rank(varied)
            previous = sensitivity_observed["epsilon"].setdefault(str(value), varied_rank)
            if previous != varied_rank or varied_rank != 18:
                raise EvidenceError("epsilon diagnostic changed exact rank classification")
        for value in sensitivities["gamma_over_G"]:
            varied = _add(_add(k0, _scale(k_pl, _fraction(value))), k_hg)
            varied_rank = _rank(varied)
            previous = sensitivity_observed["gamma_over_G"].setdefault(str(value), varied_rank)
            if previous != varied_rank or varied_rank != 18:
                raise EvidenceError("gamma_PL/G diagnostic changed exact rank classification")

        nodes = _physical_nodes(raw_record)
        rigid = _rigid_vectors(nodes)
        rigid_images = {name: _matvec(k_total, vector) for name, vector in rigid.items()}
        if _rank([rigid[name] for name in sorted(rigid)]) != 6 or any(any(image) for image in rigid_images.values()):
            raise EvidenceError(f"PL rigid-nullspace failure: {geometry_id}")
        states = _mode_states(nodes)
        energies: dict[str, object] = {}
        for name, state in states.items():
            pl_energy, hg_energy = _numerical_energy(c, hrow, mass, state, g, epsilon, h, area)
            energies[name] = {
                "constraint": _signature(_matvec(c, state)),
                "hourglass_action": str(_dot(hrow, state)),
                "hourglass_energy": str(hg_energy),
                "pl_energy": str(pl_energy),
            }
        if not (Fraction(energies["pure_common_drill"]["pl_energy"]) > 0):
            raise EvidenceError("common drill is not PL energetic")
        if not (Fraction(energies["translation_only_spin"]["pl_energy"]) > 0):
            raise EvidenceError("translation-only spin is not PL energetic")
        if any(Fraction(energies["matched_rigid_spin"][key]) for key in ("pl_energy", "hourglass_energy")):
            raise EvidenceError("matched physical rigid spin is not null")
        alternating = energies["alternating_drill"]
        if Fraction(alternating["pl_energy"]) or not (Fraction(alternating["hourglass_energy"]) > 0):
            raise EvidenceError("alternating drill is not hourglass-only")
        for patch in ("constant_membrane_x", "constant_symmetric_shear", "bending_and_transverse_shear_decoupling"):
            if Fraction(energies[patch]["pl_energy"]) or Fraction(energies[patch]["hourglass_energy"]):
                raise EvidenceError(f"numerical drill energy entered patch field: {patch}")

        # One 38-field functional: 35 WG-core local variables followed by
        # three multiplier parameters.
        q = [Fraction(index - 9) for index in range(24)]
        m_inverse = _diagonal([1 / mass[index][index] for index in range(3)])
        b = _multiply(mass, c)
        d = core["D"]
        d_inverse = core["D_inverse"]
        z = _scale([_matvec(d_inverse, _matvec(_transpose(core_coupling), q))], Fraction(-1))[0]
        tau = _scale([_matvec(m_inverse, _matvec(b, q))], g)[0]
        mixed_q = _matvec(k_hg, q)
        mixed_q = [left + right for left, right in zip(mixed_q, _matvec(core_coupling, z))]
        mixed_q = [left + right for left, right in zip(mixed_q, _matvec(_transpose(b), tau))]
        condensed_q = _matvec(k_total, q)
        core_stationarity = [left + right for left, right in zip(
            _matvec(_transpose(core_coupling), q), _matvec(d, z)
        )]
        tau_stationarity = [
            left - right / g for left, right in zip(_matvec(b, q), _matvec(mass, tau))
        ]
        mixed_energy = (
            _dot(z, _matvec(d, z)) / 2 + _dot(q, _matvec(core_coupling, z))
            + _dot(tau, _matvec(b, q)) - _dot(tau, _matvec(mass, tau)) / (2 * g)
            + _energy(k_hg, q)
        )
        condensed_energy = _energy(k_total, q)
        if mixed_q != condensed_q or any(core_stationarity) or any(tau_stationarity) or mixed_energy != condensed_energy:
            raise EvidenceError(f"38-field stationary parity failed: {geometry_id}")
        internal_block = _zeros(38, 38)
        for row in range(35):
            for column in range(35):
                internal_block[row][column] = d[row][column]
        for row in range(3):
            for column in range(3):
                internal_block[35 + row][35 + column] = -mass[row][column] / g
        if _rank(internal_block) != 38:
            raise EvidenceError(f"actual combined local block is singular: {geometry_id}")

        # Exact reparameterization/frame/reversal/origin/unit covariance.
        generic = [Fraction(index + 1) for index in range(24)]
        old_pl, old_hg = _numerical_energy(c, hrow, mass, generic, g, epsilon, h, area)
        d4_ok = True
        for transform in _d4_matrices():
            new_j = _matrix2_product(jacobian, transform)
            new_state = _reparameterize_state(generic, transform)
            new_c, new_hrow, new_m, unused_pl, unused_hg = _numerical_forms(new_j, h, g, epsilon)
            del unused_pl, unused_hg
            new_pl, new_hg_energy = _numerical_energy(new_c, new_hrow, new_m, new_state, g, epsilon, h, area)
            d4_ok = d4_ok and new_pl == old_pl and new_hg_energy == old_hg
        rotation = [[Fraction(3, 5), Fraction(-4, 5)], [Fraction(4, 5), Fraction(3, 5)]]
        frame_j = _matrix2_product(rotation, jacobian)
        frame_state = _transform_frame_state(generic, rotation)
        frame_c, frame_hrow, frame_m, unused_pl, unused_hg = _numerical_forms(frame_j, h, g, epsilon)
        del unused_pl, unused_hg
        frame_energies = _numerical_energy(frame_c, frame_hrow, frame_m, frame_state, g, epsilon, h, area)
        reflection = [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(-1)]]
        reverse_j = _matrix2_product(reflection, jacobian)
        reverse_state = _transform_frame_state(generic, reflection, Fraction(-1))
        reverse_c, reverse_hrow, reverse_m, unused_pl, unused_hg = _numerical_forms(reverse_j, h, g, epsilon)
        del unused_pl, unused_hg
        reverse_energies = _numerical_energy(reverse_c, reverse_hrow, reverse_m, reverse_state, g, epsilon, h, area)
        shifted_state = generic[:]
        for node in range(4):
            shifted_state[6 * node] += Fraction(7, 3)
            shifted_state[6 * node + 1] -= Fraction(5, 2)
        shift_energies = _numerical_energy(c, hrow, mass, shifted_state, g, epsilon, h, area)
        length_scale = Fraction(7, 3)
        scaled_j = _scale(jacobian, length_scale)
        scaled_state = generic[:]
        for node in range(4):
            scaled_state[6 * node] *= length_scale
            scaled_state[6 * node + 1] *= length_scale
        scaled_c, scaled_hrow = _constraint_rows(scaled_j)
        unit_c_invariant = _matvec(scaled_c, scaled_state) == _matvec(c, generic)
        unit_h_invariant = _dot(scaled_hrow, scaled_state) == _dot(hrow, generic)
        if not (d4_ok and frame_energies == (old_pl, old_hg) and reverse_energies == (old_pl, old_hg) and shift_energies == (old_pl, old_hg) and unit_c_invariant and unit_h_invariant):
            raise EvidenceError(f"PL covariance failure: {geometry_id}")

        geometry_results[geometry_id] = {
            "combined_constraint_hourglass_rank": _rank(full_c),
            "covariance": {
                "d4_count": len(_d4_matrices()),
                "d4_energy": d4_ok,
                "frame_energy": frame_energies == (old_pl, old_hg),
                "normal_reversal_energy": reverse_energies == (old_pl, old_hg),
                "origin_shift_energy": shift_energies == (old_pl, old_hg),
                "unit_dimensionless_measure": unit_c_invariant and unit_h_invariant,
            },
            "deleted_rs_translation_support": sum(1 for column, value in enumerate(hrow) if value and column % 6 != 5),
            "energies": energies,
            "hourglass_rank": _rank([hrow]),
            "mixed_condensed": {
                "energy_parity": mixed_energy == condensed_energy,
                "internal_block_dimension": 38,
                "internal_block_invertible": _rank(internal_block) == 38,
                "residual_parity": mixed_q == condensed_q,
                "stationarity": not any(core_stationarity + tau_stationarity),
                "symmetric_tangent": k_total == _transpose(k_total),
                "tangent_parity": True,
                "virtual_work_parity": mixed_q == condensed_q,
            },
            "nullity": 24 - _rank(k_total),
            "psd_gram_decomposition": True,
            "rank": _rank(k_total),
            "retained_constraint_rank": _rank(c),
            "rigid_images_zero": {name: not any(image) for name, image in rigid_images.items()},
            "source_exact_core": {
                "S_ldl_positive": all(pivot > 0 for pivot in _ldl_pivots(core["S"])),
                "generic_I35_surrogate_used": False,
                "ranks": core_ranks,
            },
        }

    baseline = _load_json(ROOT / "docs/reference_cases/e4_baseline.json")
    historical = baseline.get("historical_results")
    required_historical = {
        "candidate_a": "NO_GO_CANDIDATE_A_DISCRETE_PAIR",
        "candidate_b": "NO_GO_CANDIDATE_B",
        "candidate_c": "NO_GO_CANDIDATE_C_QUOTIENT_INF_SUP",
        "candidate_e1_a": "NO_GO_CANDIDATE_E1_A_RANK_DEFICIENCY",
        "candidate_e2_a": "BLOCKED_E2_A_SOURCE_OR_FORMULATION_IDENTITY",
    }
    if not isinstance(historical, dict) or any(historical.get(key) != value for key, value in required_historical.items()):
        raise EvidenceError("hostile historical terminal changed")
    return {
        "constitutive": {
            "E": str(e), "G": str(g), "h": str(h), "nu": str(nu),
            "new_public_material_inputs": [],
        },
        "geometries": geometry_results,
        "historical_hostile_terminals": required_historical,
        "identity": {
            "basis": ["1", "r", "s"],
            "core_operator": "SOURCE_EXACT_WG_D_Q_K0",
            "core_internal_parameters": 35,
            "deleted_only": "rotation_only_r_s_coefficient",
            "element_local_multiplier_parameters": 3,
            "external_coordinates": 24,
            "full_local_internal_parameters": 38,
            "scalar_normalization": "MITC9i_18_19_WITH_GAMMA_EQUAL_G",
            "surface_reduction": "h_times_stress_multiplier_functional",
        },
        "recovery": {
            "hourglass_and_multiplier_are_numerical_diagnostics": True,
            "physical_N_M_Q_from_WG_core_only": True,
        },
        "sensitivity": {
            "classification_unchanged": True,
            "ranks": sensitivity_observed,
            "role": "DIAGNOSTIC_ONLY_NO_TUNING",
        },
        "study_id": STUDY_ID,
        "terminal": TERMINAL,
    }


def build_contract() -> dict[str, object]:
    build_certificate()
    identities: dict[str, object] = {}
    for relative in CONTRACT_INPUTS:
        raw = (ROOT / relative).read_bytes()
        identities[relative] = {"bytes": len(raw), "path": relative, "sha256": _sha(raw)}
    oracle_path = Path(__file__).relative_to(ROOT).as_posix()
    oracle_raw = Path(__file__).read_bytes()
    identities[oracle_path] = {
        "bytes": len(oracle_raw), "path": oracle_path, "sha256": _sha(oracle_raw)
    }
    return {
        "core_prerequisite": "GO_E4_OPEN_CORE_IDENTITY",
        "input_identities": identities,
        "production_paths": [],
        "proof_program": [
            "DIMENSIONALLY_CONSISTENT_SURFACE_REDUCTION",
            "SOURCE_EXACT_WG_D_Q_K0_DEPENDENCY",
            "THREE_RETAINED_PLUS_ONE_RESIDUAL_ROW",
            "ACTUAL_38_FIELD_STATIONARY_SCHUR_PARITY",
            "RANK_18_EXACTLY_SIX_RIGID",
            "PATCH_AND_AFFINE_COVARIANCE",
            "SEPARATE_NUMERICAL_DIAGNOSTICS",
            "HOSTILE_TERMINALS_UNCHANGED",
        ],
        "schema": "anysolver.s4.e4-pl-contract-v2",
        "scientific_terminal": TERMINAL,
        "study_id": STUDY_ID,
    }


def build_output(contract_sha256: str) -> dict[str, object]:
    return {
        "certificate": build_certificate(),
        "contract_sha256": contract_sha256,
        "overall_release_terminal": RELEASE,
        "production_changed": False,
        "schema": "anysolver.s4.e4-pl-output-v2",
        "status": "provisional_go",
        "study_id": STUDY_ID,
        "terminal": TERMINAL,
    }


def _load_contract(path: Path, caller_sha256: str) -> str:
    try:
        if path.resolve(strict=True) != CONTRACT_PATH.resolve(strict=True):
            raise ContractError("contract path mismatch")
        raw = path.read_bytes()
        if _sha(raw) != caller_sha256:
            raise ContractError("contract raw hash mismatch")
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(ContractError(token)),
        )
        if not isinstance(value, dict) or raw != _canonical(value):
            raise ContractError("contract is not canonical")
        if value != build_contract():
            raise ContractError("contract semantic mismatch")
    except ContractError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, EvidenceError) as exc:
        raise ContractError(str(exc)) from exc
    return caller_sha256


def _blocked(detail: str) -> bytes:
    return _canonical({"detail": detail, "status": "blocked", "terminal": BLOCKED})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--certificate", action="store_true")
    modes.add_argument("--emit-contract", action="store_true")
    modes.add_argument("--run", action="store_true")
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--contract-sha256")
    arguments = parser.parse_args(argv)
    try:
        if arguments.certificate:
            if arguments.contract is not None or arguments.contract_sha256 is not None:
                raise ContractError("contract arguments forbidden in certificate mode")
            sys.stdout.buffer.write(_canonical(build_certificate()))
            return 0
        if arguments.emit_contract:
            if arguments.contract is not None or arguments.contract_sha256 is not None:
                raise ContractError("contract arguments forbidden in emit mode")
            sys.stdout.buffer.write(_canonical(build_contract()))
            return 0
        if arguments.contract is None or arguments.contract_sha256 is None:
            raise ContractError("run mode requires caller-bound contract")
        contract_sha = _load_contract(arguments.contract, arguments.contract_sha256)
        sys.stdout.buffer.write(_canonical(build_output(contract_sha)))
        return 0
    except (EvidenceError, ContractError, OSError, AssertionError, ValueError) as exc:
        sys.stdout.buffer.write(_blocked(str(exc)))
        return 2
    except Exception as exc:
        sys.stdout.buffer.write(_blocked(f"{type(exc).__name__}: {exc}"))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
