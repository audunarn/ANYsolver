"""Deterministic checker for the independent flat DKMT reference.

Arbitrary binary64 cases are checked as implementation diagnostics.  Rank,
nullity, inertia, patches, D3 covariance, and equation residuals are also
proved with ``Fraction`` arithmetic for one hash-bound 3-4-5 canonical case.
Consequently this module never presents tolerance-based SVD/eigenvalue output
as an exact certificate for an arbitrary geometry.
"""

from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
import hashlib
import itertools
import json
import math
from typing import Any, Mapping, Sequence

import numpy as np


CHECKER_IMPLEMENTATION_ID = "INDEPENDENT_S3_V2A_FLAT_DKMT_CHECKER_V1"
EXPECTED_REFERENCE_IMPLEMENTATION_ID = "INDEPENDENT_S3_V2A_FLAT_DKMT_EQ12_41_V1"
PROOF_SCHEMA = "E4_PL_S3_V2A_FLAT_DKMT_PROOF_V1"
EXACT_CASE_ID = "DKMT_RATIONAL_3_4_5_ISOTROPIC_V1"
SOURCE_PDF_SHA256 = "CAACAB9E0DF9B4F8B55887E84FAFA923899677F7D0F285EB2EEB46FBDFF8D17A"
ORIENTED_EDGES = ((0, 1), (1, 2), (2, 0))
TRIANGLE_RULE = (
    ((2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0), 1.0 / 3.0),
    ((1.0 / 6.0, 2.0 / 3.0, 1.0 / 6.0), 1.0 / 3.0),
    ((1.0 / 6.0, 1.0 / 6.0, 2.0 / 3.0), 1.0 / 3.0),
)
F = Fraction


def _canonical_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [_canonical_value(item) for item in value.tolist()]
    if isinstance(value, (np.floating, float)):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("canonical records forbid nonfinite numbers")
        return {"binary64": number.hex()}
    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, Mapping):
        return {str(key): _canonical_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    if value is None or isinstance(value, (str, bool)):
        return value
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(_canonical_value(value), sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest().upper()


def _matrix_hash(matrix: np.ndarray) -> str:
    return _canonical_sha256({"matrix": np.asarray(matrix, dtype=np.float64)})


def _diagnostic_rank(matrix: np.ndarray) -> int:
    singular = np.linalg.svd(np.asarray(matrix, dtype=np.float64), compute_uv=False)
    threshold = max(float(singular[0]) if singular.size else 0.0, 1.0) * max(matrix.shape) * 4096.0 * np.finfo(float).eps
    return int(np.count_nonzero(singular > threshold))


def _diagnostic_inertia(matrix: np.ndarray) -> tuple[int, int, int]:
    values = np.linalg.eigvalsh(0.5 * (matrix + matrix.T))
    threshold = max(float(np.max(np.abs(values))) if values.size else 0.0, 1.0) * len(values) * 4096.0 * np.finfo(float).eps
    return (
        int(np.count_nonzero(values > threshold)),
        int(np.count_nonzero(values < -threshold)),
        int(np.count_nonzero(np.abs(values) <= threshold)),
    )


def _scaled_residual(actual: np.ndarray, expected: np.ndarray) -> float:
    scale = max(float(np.linalg.norm(expected, ord=np.inf)), 1.0)
    return float(np.linalg.norm(actual - expected, ord=np.inf)) / scale


def _probe_vector() -> np.ndarray:
    return np.asarray((3, -5, 7, 11, -13, 17, -19, 23, 29, -31, 37, 41, 43, -47, 53, 59, -61, 67), dtype=np.float64) / 32.0


# ----- Independently reconstructed arbitrary binary64 path ---------------------------

def _finite_matrix_f(value: object, shape: tuple[int, int], name: str) -> np.ndarray:
    matrix = np.asarray(value, dtype=np.float64)
    if matrix.shape != shape or not np.all(np.isfinite(matrix)):
        raise ValueError(f"{name} must be a finite {shape[0]}x{shape[1]} matrix")
    return matrix


def _validate_section_f(section: Sequence[Sequence[float]]) -> tuple[np.ndarray, dict[str, float]]:
    matrix = _finite_matrix_f(section, (8, 8), "section")
    scale = max(float(np.linalg.norm(matrix, ord=np.inf)), 1.0)
    tolerance = 8192.0 * np.finfo(float).eps * scale
    if float(np.linalg.norm(matrix - matrix.T, ord=np.inf)) > tolerance:
        raise ValueError("section must be symmetric")
    matrix = 0.5 * (matrix + matrix.T)
    try:
        np.linalg.cholesky(matrix)
    except np.linalg.LinAlgError as exc:
        raise ValueError("section must be positive definite") from exc
    allowed = np.zeros((8, 8), dtype=bool)
    allowed[:3, :3] = True
    allowed[3:6, 3:6] = True
    allowed[6:, 6:] = True
    if np.any(np.abs(matrix[~allowed]) > tolerance):
        raise ValueError("unsupported generalized section coupling")
    membrane = matrix[:3, :3]
    bending = matrix[3:6, 3:6]
    shear = matrix[6:, 6:]
    poisson = float(membrane[0, 1] / membrane[0, 0])
    membrane_expected = membrane[0, 0] * np.asarray(
        ((1.0, poisson, 0.0), (poisson, 1.0, 0.0), (0.0, 0.0, 0.5 * (1.0 - poisson)))
    )
    if not (-1.0 < poisson < 0.5) or not np.allclose(membrane, membrane_expected, rtol=2.0e-13, atol=tolerance):
        raise ValueError("unsupported non-isotropic membrane section")
    ratio = float(bending[0, 0] / membrane[0, 0])
    if ratio <= 0.0 or not np.allclose(bending, ratio * membrane, rtol=2.0e-13, atol=tolerance):
        raise ValueError("unsupported non-isotropic bending section")
    if not np.allclose(shear, shear[0, 0] * np.eye(2), rtol=2.0e-13, atol=tolerance):
        raise ValueError("unsupported non-isotropic transverse shear section")
    thickness = math.sqrt(12.0 * ratio)
    shear_correction = float(shear[0, 0] / membrane[2, 2])
    if shear_correction <= 0.0:
        raise ValueError("unsupported shear correction")
    return matrix, {
        "poisson": poisson,
        "thickness": thickness,
        "shear_correction": shear_correction,
        "bending_rigidity": float(bending[0, 0]),
        "shear_rigidity": float(shear[0, 0]),
    }


def _isotropic_section_f(young: float, poisson: float, thickness: float, shear_correction: float = 5.0 / 6.0) -> np.ndarray:
    if young <= 0.0 or thickness <= 0.0 or shear_correction <= 0.0 or not (-1.0 < poisson < 0.5):
        raise ValueError("unsupported isotropic section parameters")
    rigidity = young * thickness / (1.0 - poisson * poisson)
    membrane = rigidity * np.asarray(
        ((1.0, poisson, 0.0), (poisson, 1.0, 0.0), (0.0, 0.0, 0.5 * (1.0 - poisson)))
    )
    section = np.zeros((8, 8), dtype=np.float64)
    section[:3, :3] = membrane
    section[3:6, 3:6] = thickness * thickness * membrane / 12.0
    section[6:, 6:] = shear_correction * membrane[2, 2] * np.eye(2)
    return section


def _geometry_f(nodes: Sequence[Sequence[float]]) -> tuple[np.ndarray, float, np.ndarray]:
    points = _finite_matrix_f(nodes, (3, 2), "nodes")
    jacobian = np.column_stack((points[1] - points[0], points[2] - points[0]))
    determinant = float(np.linalg.det(jacobian))
    scale = max(float(np.linalg.norm(jacobian, ord=np.inf)) ** 2, 1.0)
    if not math.isfinite(determinant) or abs(determinant) <= 64.0 * np.finfo(float).eps * scale:
        raise ValueError("nodes must define a nondegenerate triangle")
    gradients = np.asarray(((-1.0, -1.0), (1.0, 0.0), (0.0, 1.0))) @ np.linalg.inv(jacobian)
    return points, abs(determinant) / 2.0, gradients


def _edge_geometry_f(nodes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    directions = np.zeros((3, 2), dtype=np.float64)
    lengths = np.zeros(3, dtype=np.float64)
    for row, (left, right) in enumerate(ORIENTED_EDGES):
        vector = nodes[right] - nodes[left]
        length = float(np.linalg.norm(vector))
        if not math.isfinite(length) or length <= 0.0:
            raise ValueError("every DKMT edge must have positive length")
        directions[row] = vector / length
        lengths[row] = length
    return directions, lengths


def _membrane_operator_f(gradients: np.ndarray) -> np.ndarray:
    operator = np.zeros((3, 18), dtype=np.float64)
    for node, (dx, dy) in enumerate(gradients):
        base = 6 * node
        operator[0, base] = dx
        operator[1, base + 1] = dy
        operator[2, base] = dy
        operator[2, base + 1] = dx
    return operator


def _beta_operator_f(gradients: np.ndarray) -> np.ndarray:
    operator = np.zeros((3, 18), dtype=np.float64)
    for node, (dx, dy) in enumerate(gradients):
        base = 6 * node
        operator[0, base + 4] = dx
        operator[1, base + 3] = -dy
        operator[2, base + 4] = dy
        operator[2, base + 3] = -dx
    return operator


def _au_f(directions: np.ndarray, lengths: np.ndarray) -> np.ndarray:
    operator = np.zeros((3, 18), dtype=np.float64)
    for row, (left, right) in enumerate(ORIENTED_EDGES):
        cosine, sine = directions[row]
        length = lengths[row]
        operator[row, 6 * left + 2] = -1.0 / length
        operator[row, 6 * right + 2] = 1.0 / length
        for node in (left, right):
            operator[row, 6 * node + 3] = -sine / 2.0
            operator[row, 6 * node + 4] = cosine / 2.0
    return operator


def _bdelta_f(barycentric: Sequence[float], gradients: np.ndarray, directions: np.ndarray) -> np.ndarray:
    shapes = np.asarray(barycentric, dtype=np.float64)
    pairs = ((0, 1), (1, 2), (0, 2))
    p_gradients = np.asarray(
        [4.0 * (shapes[left] * gradients[right] + shapes[right] * gradients[left]) for left, right in pairs]
    )
    operator = np.zeros((3, 3), dtype=np.float64)
    for edge, ((px, py), (cosine, sine)) in enumerate(zip(p_gradients, directions, strict=True)):
        operator[0, edge] = px * cosine
        operator[1, edge] = py * sine
        operator[2, edge] = py * cosine + px * sine
    return operator


def _edge_projection_f(barycentric: Sequence[float], directions: np.ndarray) -> np.ndarray:
    n1, n2, n3 = np.asarray(barycentric, dtype=np.float64)
    (c12, s12), (c23, s23), (c31, s31) = directions
    a1 = c12 * s31 - c31 * s12
    a2 = c23 * s12 - c12 * s23
    a3 = c31 * s23 - c23 * s31
    if min(abs(a1), abs(a2), abs(a3)) <= 64.0 * np.finfo(float).eps:
        raise ValueError("DKMT edge projection denominators must be nonzero")
    first = (
        s31 * n1 / a1 - s23 * n2 / a2,
        s12 * n2 / a2 - s31 * n3 / a3,
        s23 * n3 / a3 - s12 * n1 / a1,
    )
    second = (
        -c31 * n1 / a1 + c23 * n2 / a2,
        -c12 * n2 / a2 + c31 * n3 / a3,
        -c23 * n3 / a3 + c12 * n1 / a1,
    )
    return np.asarray((first, second), dtype=np.float64)


def _pl_f(gradients: np.ndarray, area: float, membrane: np.ndarray) -> tuple[np.ndarray, np.ndarray, float, np.ndarray]:
    projector = np.asarray(((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0)))
    metric_inverse_sqrt = np.asarray(((1.0 / math.sqrt(2.0), 0.0), (0.0, math.sqrt(2.0))))
    restricted = metric_inverse_sqrt @ (projector.T @ membrane @ projector) @ metric_inverse_sqrt
    scale = 0.5 * float(np.linalg.eigvalsh(0.5 * (restricted + restricted.T))[0])
    if not math.isfinite(scale) or scale <= 0.0:
        raise ValueError("PL scale must be strictly positive")
    constraint = np.zeros((3, 18), dtype=np.float64)
    for row in range(3):
        for node, (dx, dy) in enumerate(gradients):
            constraint[row, 6 * node] = dy / 2.0
            constraint[row, 6 * node + 1] = -dx / 2.0
        constraint[row, 6 * row + 5] = 1.0
    gram = area * np.asarray(((2.0, 1.0, 1.0), (1.0, 2.0, 1.0), (1.0, 1.0, 2.0))) / 12.0
    stiffness = scale * constraint.T @ gram @ constraint
    return constraint, gram, scale, 0.5 * (stiffness + stiffness.T)


def _rigid_f(nodes: np.ndarray) -> np.ndarray:
    modes = np.zeros((18, 6), dtype=np.float64)
    for node, (x, y) in enumerate(nodes):
        base = 6 * node
        modes[base, 0] = 1.0
        modes[base + 1, 1] = 1.0
        modes[base + 2, 2] = 1.0
        modes[base + 2, 3] = y
        modes[base + 3, 3] = 1.0
        modes[base + 2, 4] = -x
        modes[base + 4, 4] = 1.0
        modes[base, 5] = -y
        modes[base + 1, 5] = x
        modes[base + 5, 5] = 1.0
    return modes


def _assemble_f(nodes: Sequence[Sequence[float]], section: Sequence[Sequence[float]]) -> dict[str, Any]:
    points, area, gradients = _geometry_f(nodes)
    constitutive, parameters = _validate_section_f(section)
    directions, lengths = _edge_geometry_f(points)
    b_membrane = _membrane_operator_f(gradients)
    b_beta = _beta_operator_f(gradients)
    a_u = _au_f(directions, lengths)
    phi = 12.0 * parameters["bending_rigidity"] / (parameters["shear_rigidity"] * lengths * lengths)
    a_delta = -(2.0 / 3.0) * np.diag(1.0 + phi)
    delta = np.linalg.solve(a_delta, a_u)
    k_membrane = area * (b_membrane.T @ constitutive[:3, :3] @ b_membrane)
    k_bending = np.zeros((18, 18), dtype=np.float64)
    k_shear = np.zeros((18, 18), dtype=np.float64)
    curvatures: list[np.ndarray] = []
    shears: list[np.ndarray] = []
    for barycentric, weight in TRIANGLE_RULE:
        curvature = b_beta + _bdelta_f(barycentric, gradients, directions) @ delta
        shear = _edge_projection_f(barycentric, directions) @ ((phi / (1.0 + phi))[:, None] * a_u)
        curvatures.append(curvature)
        shears.append(shear)
        k_bending += area * weight * (curvature.T @ constitutive[3:6, 3:6] @ curvature)
        k_shear += area * weight * (shear.T @ constitutive[6:, 6:] @ shear)
    physical = k_membrane + k_bending + k_shear
    physical = 0.5 * (physical + physical.T)
    constraint, gram, pl_scale, pl = _pl_f(gradients, area, constitutive[:3, :3])
    condensed = physical + pl
    coupling = constraint.T @ gram
    saddle = np.zeros((21, 21), dtype=np.float64)
    saddle[:18, :18] = physical
    saddle[:18, 18:] = coupling
    saddle[18:, :18] = coupling.T
    saddle[18:, 18:] = -gram / pl_scale
    return {
        "nodes": points,
        "section": constitutive,
        "parameters": parameters,
        "area": area,
        "gradients": gradients,
        "directions": directions,
        "lengths": lengths,
        "b_membrane": b_membrane,
        "au": a_u,
        "phi": phi,
        "a_delta": a_delta,
        "delta": delta,
        "curvatures": np.asarray(curvatures),
        "shears": np.asarray(shears),
        "physical": physical,
        "pl": pl,
        "condensed": 0.5 * (condensed + condensed.T),
        "saddle": 0.5 * (saddle + saddle.T),
        "rigid": _rigid_f(points),
    }


def _direct_force_f(assembled: Mapping[str, Any], vector: np.ndarray) -> np.ndarray:
    force = np.zeros(18, dtype=np.float64)
    for station, (_barycentric, weight) in enumerate(TRIANGLE_RULE):
        operator = np.vstack((assembled["b_membrane"], assembled["curvatures"][station], assembled["shears"][station]))
        force += assembled["area"] * weight * (operator.T @ (assembled["section"] @ (operator @ vector)))
    return force


def _block_permutation_f(permutation: Sequence[int]) -> np.ndarray:
    order = tuple(int(value) for value in permutation)
    if sorted(order) != [0, 1, 2]:
        raise ValueError("invalid D3 permutation")
    transform = np.zeros((18, 18), dtype=np.float64)
    for new_node, old_node in enumerate(order):
        transform[6 * new_node : 6 * new_node + 6, 6 * old_node : 6 * old_node + 6] = np.eye(6)
    return transform


# ----- Exact rational canonical path -------------------------------------------------

QMatrix = list[list[Fraction]]


def _qzeros(rows: int, columns: int) -> QMatrix:
    return [[F(0) for _column in range(columns)] for _row in range(rows)]


def _qtranspose(matrix: QMatrix) -> QMatrix:
    return [list(row) for row in zip(*matrix, strict=True)]


def _qmatmul(left: QMatrix, right: QMatrix) -> QMatrix:
    if not left or not right or len(left[0]) != len(right):
        raise ValueError("incompatible exact matrix product")
    transposed = _qtranspose(right)
    return [[sum((a * b for a, b in zip(row, column, strict=True)), F(0)) for column in transposed] for row in left]


def _qadd(*matrices: QMatrix) -> QMatrix:
    return [[sum((matrix[i][j] for matrix in matrices), F(0)) for j in range(len(matrices[0][0]))] for i in range(len(matrices[0]))]


def _qscale(value: Fraction, matrix: QMatrix) -> QMatrix:
    return [[value * entry for entry in row] for row in matrix]


def _qdiag(values: Sequence[Fraction]) -> QMatrix:
    matrix = _qzeros(len(values), len(values))
    for index, value in enumerate(values):
        matrix[index][index] = value
    return matrix


def _qrank(matrix: QMatrix) -> int:
    work = [row[:] for row in matrix]
    rows = len(work)
    columns = len(work[0]) if rows else 0
    pivot_row = 0
    for column in range(columns):
        selected = next((row for row in range(pivot_row, rows) if work[row][column] != 0), None)
        if selected is None:
            continue
        work[pivot_row], work[selected] = work[selected], work[pivot_row]
        pivot = work[pivot_row][column]
        work[pivot_row] = [entry / pivot for entry in work[pivot_row]]
        for row in range(rows):
            if row != pivot_row and work[row][column] != 0:
                factor = work[row][column]
                work[row] = [entry - factor * base for entry, base in zip(work[row], work[pivot_row], strict=True)]
        pivot_row += 1
        if pivot_row == rows:
            break
    return pivot_row


def _q_psd_ldl_inertia(matrix: QMatrix) -> tuple[int, int, int] | None:
    """Exact symmetric 1x1-pivot LDL; fail closed if a 2x2 pivot is needed."""

    work = [row[:] for row in matrix]
    positive = negative = zero = 0
    while work:
        size = len(work)
        selected = next((index for index in range(size) if work[index][index] != 0), None)
        if selected is None:
            if any(work[i][j] != 0 for i in range(size) for j in range(size)):
                return None
            zero += size
            break
        if selected:
            work[0], work[selected] = work[selected], work[0]
            for row in work:
                row[0], row[selected] = row[selected], row[0]
        pivot = work[0][0]
        positive += int(pivot > 0)
        negative += int(pivot < 0)
        tail = _qzeros(size - 1, size - 1)
        for i in range(1, size):
            for j in range(1, size):
                tail[i - 1][j - 1] = work[i][j] - work[i][0] * work[0][j] / pivot
        work = tail
    return positive, negative, zero


def _qsqrt(value: Fraction) -> Fraction:
    numerator = math.isqrt(value.numerator)
    denominator = math.isqrt(value.denominator)
    if numerator * numerator != value.numerator or denominator * denominator != value.denominator:
        raise ArithmeticError("canonical edge length is not rational")
    return F(numerator, denominator)


def _qgeometry(nodes: Sequence[Sequence[Fraction]]) -> tuple[Fraction, QMatrix, QMatrix, list[Fraction]]:
    x1, y1 = nodes[0]
    a = nodes[1][0] - x1
    c = nodes[1][1] - y1
    b = nodes[2][0] - x1
    d = nodes[2][1] - y1
    determinant = a * d - b * c
    if determinant == 0:
        raise ValueError("exact triangle is degenerate")
    inverse = [[d / determinant, -b / determinant], [-c / determinant, a / determinant]]
    reference_gradients = [[F(-1), F(-1)], [F(1), F(0)], [F(0), F(1)]]
    gradients = _qmatmul(reference_gradients, inverse)
    directions: QMatrix = []
    lengths: list[Fraction] = []
    for left, right in ORIENTED_EDGES:
        dx = nodes[right][0] - nodes[left][0]
        dy = nodes[right][1] - nodes[left][1]
        length = _qsqrt(dx * dx + dy * dy)
        lengths.append(length)
        directions.append([dx / length, dy / length])
    return abs(determinant) / 2, gradients, directions, lengths


def _qmembrane(gradients: QMatrix) -> QMatrix:
    operator = _qzeros(3, 18)
    for node, (dx, dy) in enumerate(gradients):
        base = 6 * node
        operator[0][base] = dx
        operator[1][base + 1] = dy
        operator[2][base] = dy
        operator[2][base + 1] = dx
    return operator


def _qbeta(gradients: QMatrix) -> QMatrix:
    operator = _qzeros(3, 18)
    for node, (dx, dy) in enumerate(gradients):
        base = 6 * node
        operator[0][base + 4] = dx
        operator[1][base + 3] = -dy
        operator[2][base + 4] = dy
        operator[2][base + 3] = -dx
    return operator


def _qau(directions: QMatrix, lengths: Sequence[Fraction]) -> QMatrix:
    operator = _qzeros(3, 18)
    for row, ((left, right), ((cosine, sine), length)) in enumerate(zip(ORIENTED_EDGES, zip(directions, lengths), strict=True)):
        for node, w_sign in ((left, F(-1)), (right, F(1))):
            base = 6 * node
            operator[row][base + 2] = w_sign / length
            operator[row][base + 3] = -sine / 2
            operator[row][base + 4] = cosine / 2
    return operator


def _qbdelta(barycentric: Sequence[Fraction], gradients: QMatrix, directions: QMatrix) -> QMatrix:
    pairs = ((0, 1), (1, 2), (0, 2))
    p_gradients = [
        [4 * (barycentric[left] * gradients[right][axis] + barycentric[right] * gradients[left][axis]) for axis in range(2)]
        for left, right in pairs
    ]
    operator = _qzeros(3, 3)
    for edge, ((px, py), (cosine, sine)) in enumerate(zip(p_gradients, directions, strict=True)):
        operator[0][edge] = px * cosine
        operator[1][edge] = py * sine
        operator[2][edge] = py * cosine + px * sine
    return operator


def _qbs_gamma(barycentric: Sequence[Fraction], directions: QMatrix) -> QMatrix:
    n1, n2, n3 = barycentric
    (c12, s12), (c23, s23), (c31, s31) = directions
    a1 = c12 * s31 - c31 * s12
    a2 = c23 * s12 - c12 * s23
    a3 = c31 * s23 - c23 * s31
    if a1 == 0 or a2 == 0 or a3 == 0:
        raise ArithmeticError("exact edge projection denominator is zero")
    return [
        [s31 * n1 / a1 - s23 * n2 / a2, s12 * n2 / a2 - s31 * n3 / a3, s23 * n3 / a3 - s12 * n1 / a1],
        [-(c31 * n1 / a1 - c23 * n2 / a2), -(c12 * n2 / a2 - c31 * n3 / a3), -(c23 * n3 / a3 - c12 * n1 / a1)],
    ]


def _qrigid(nodes: Sequence[Sequence[Fraction]]) -> QMatrix:
    modes = _qzeros(18, 6)
    for node, (x, y) in enumerate(nodes):
        base = 6 * node
        modes[base][0] = 1
        modes[base + 1][1] = 1
        modes[base + 2][2] = 1
        modes[base + 2][3] = y
        modes[base + 3][3] = 1
        modes[base + 2][4] = -x
        modes[base + 4][4] = 1
        modes[base][5] = -y
        modes[base + 1][5] = x
        modes[base + 5][5] = 1
    return modes


def _qassemble(nodes: Sequence[Sequence[Fraction]]) -> dict[str, Any]:
    area, gradients, directions, lengths = _qgeometry(nodes)
    membrane = [[F(64), F(16), F(0)], [F(16), F(64), F(0)], [F(0), F(0), F(24)]]
    bending = _qscale(F(1, 48), membrane)
    shear = [[F(20), F(0)], [F(0), F(20)]]
    b_membrane = _qmembrane(gradients)
    b_beta = _qbeta(gradients)
    a_u = _qau(directions, lengths)
    phi = [F(4, 5) / (length * length) for length in lengths]
    a_delta_values = [F(-2, 3) * (1 + value) for value in phi]
    delta = [[a_u[i][j] / a_delta_values[i] for j in range(18)] for i in range(3)]
    k_membrane = _qscale(area, _qmatmul(_qtranspose(b_membrane), _qmatmul(membrane, b_membrane)))
    k_bending = _qzeros(18, 18)
    k_shear = _qzeros(18, 18)
    curvature_operators: list[QMatrix] = []
    shear_operators: list[QMatrix] = []
    stations = ((F(2, 3), F(1, 6), F(1, 6)), (F(1, 6), F(2, 3), F(1, 6)), (F(1, 6), F(1, 6), F(2, 3)))
    for barycentric in stations:
        curvature = _qadd(b_beta, _qmatmul(_qbdelta(barycentric, gradients, directions), delta))
        rho_au = [[phi[i] / (1 + phi[i]) * entry for entry in a_u[i]] for i in range(3)]
        assumed_shear = _qmatmul(_qbs_gamma(barycentric, directions), rho_au)
        curvature_operators.append(curvature)
        shear_operators.append(assumed_shear)
        k_bending = _qadd(k_bending, _qscale(area / 3, _qmatmul(_qtranspose(curvature), _qmatmul(bending, curvature))))
        k_shear = _qadd(k_shear, _qscale(area / 3, _qmatmul(_qtranspose(assumed_shear), _qmatmul(shear, assumed_shear))))
    physical = _qadd(k_membrane, k_bending, k_shear)

    constraint = _qzeros(3, 18)
    for row in range(3):
        for node, (dx, dy) in enumerate(gradients):
            constraint[row][6 * node] = dy / 2
            constraint[row][6 * node + 1] = -dx / 2
        constraint[row][6 * row + 5] = 1
    gram = _qscale(area / 12, [[F(2), F(1), F(1)], [F(1), F(2), F(1)], [F(1), F(1), F(2)]])
    pl_scale = F(24)
    pl = _qscale(pl_scale, _qmatmul(_qtranspose(constraint), _qmatmul(gram, constraint)))
    condensed = _qadd(physical, pl)
    coupling = _qmatmul(_qtranspose(constraint), gram)
    saddle = _qzeros(21, 21)
    for i in range(18):
        for j in range(18):
            saddle[i][j] = physical[i][j]
    for i in range(18):
        for j in range(3):
            saddle[i][18 + j] = coupling[i][j]
            saddle[18 + j][i] = coupling[i][j]
    for i in range(3):
        for j in range(3):
            saddle[18 + i][18 + j] = -gram[i][j] / pl_scale
    return {
        "nodes": [list(row) for row in nodes],
        "area": area,
        "gradients": gradients,
        "directions": directions,
        "lengths": lengths,
        "phi": phi,
        "a_delta": _qdiag(a_delta_values),
        "au": a_u,
        "delta": delta,
        "curvatures": curvature_operators,
        "shears": shear_operators,
        "physical": physical,
        "pl": pl,
        "gram": gram,
        "condensed": condensed,
        "saddle": saddle,
        "rigid": _qrigid(nodes),
    }


def _qrecord(matrix: QMatrix) -> list[list[list[int]]]:
    return [[[entry.numerator, entry.denominator] for entry in row] for row in matrix]


@lru_cache(maxsize=1)
def exact_canonical_certificate() -> dict[str, Any]:
    """Prove the canonical 3-4-5 case using Fraction arithmetic only."""

    nodes = ((F(0), F(0)), (F(3), F(0)), (F(0), F(4)))
    assembled = _qassemble(nodes)
    equation37 = _qmatmul(assembled["a_delta"], assembled["delta"]) == assembled["au"]
    phi_equation32 = assembled["phi"] == [F(4, 45), F(4, 125), F(1, 20)]
    rigid_null = _qmatmul(assembled["condensed"], assembled["rigid"]) == _qzeros(18, 6)

    kappa = (F(2), F(-1), F(3, 2))
    bend_patch = [F(0) for _index in range(18)]
    for node, (x, y) in enumerate(nodes):
        base = 6 * node
        bend_patch[base + 2] = -(kappa[0] * x * x + kappa[1] * y * y + kappa[2] * x * y) / 2
        beta_x = kappa[0] * x + kappa[2] * y / 2
        beta_y = kappa[1] * y + kappa[2] * x / 2
        bend_patch[base + 3] = -beta_y
        bend_patch[base + 4] = beta_x
    patch_column = [[value] for value in bend_patch]
    patch_au_zero = _qmatmul(assembled["au"], patch_column) == _qzeros(3, 1)
    patch_curvature = all(_qmatmul(operator, patch_column) == [[kappa[0]], [kappa[1]], [kappa[2]]] for operator in assembled["curvatures"])
    patch_shear = all(_qmatmul(operator, patch_column) == _qzeros(2, 1) for operator in assembled["shears"])

    ranks = {name: _qrank(assembled[name]) for name in ("physical", "pl", "condensed", "saddle", "rigid")}
    physical_inertia = _q_psd_ldl_inertia(assembled["physical"])
    pl_inertia = _q_psd_ldl_inertia(assembled["pl"])
    condensed_inertia = _q_psd_ldl_inertia(assembled["condensed"])
    gram_inertia = _q_psd_ldl_inertia(assembled["gram"])
    saddle_inertia = (
        None
        if condensed_inertia is None or gram_inertia != (3, 0, 0)
        else (condensed_inertia[0], condensed_inertia[1] + gram_inertia[0], condensed_inertia[2])
    )

    d3_exact = True
    base = assembled["condensed"]
    for permutation in itertools.permutations(range(3)):
        permuted_nodes = tuple(nodes[index] for index in permutation)
        permuted = _qassemble(permuted_nodes)["condensed"]
        expected_indices = [6 * old + component for old in permutation for component in range(6)]
        expected = [[base[i][j] for j in expected_indices] for i in expected_indices]
        d3_exact = d3_exact and permuted == expected

    checks = {
        "equation37": equation37,
        "equation32_phi": phi_equation32,
        "rigid_null": rigid_null,
        "bending_patch": patch_au_zero and patch_curvature and patch_shear,
        "d3_covariance": d3_exact,
        "ranks": ranks == {"physical": 9, "pl": 3, "condensed": 12, "saddle": 15, "rigid": 6},
        "physical_psd": physical_inertia == (9, 0, 9),
        "pl_psd": pl_inertia == (3, 0, 15),
        "condensed_psd": condensed_inertia == (12, 0, 6),
        "saddle_inertia": saddle_inertia == (12, 3, 6),
    }
    hashes = {
        name: _canonical_sha256({"fraction_matrix": _qrecord(assembled[name])})
        for name in ("physical", "pl", "condensed", "saddle")
    }
    return {
        "schema": "E4_PL_S3_V2A_DKMT_EXACT_CANONICAL_CERTIFICATE_V1",
        "case_id": EXACT_CASE_ID,
        "arithmetic": "FRACTION_GAUSSIAN_AND_SYMMETRIC_LDL",
        "classification": "PASS_E4_PL_S3_V2A_DKMT_EXACT_CANONICAL" if all(checks.values()) else "NO_GO_E4_PL_S3_V2A_DKMT_EXACT_CANONICAL",
        "checks": checks,
        "ranks": ranks,
        "inertia": {"physical": list(physical_inertia) if physical_inertia else None, "pl": list(pl_inertia) if pl_inertia else None, "condensed": list(condensed_inertia) if condensed_inertia else None, "saddle": list(saddle_inertia) if saddle_inertia else None},
        "hashes": hashes,
    }


# ----- Binary64 equation and transport diagnostics -----------------------------------

def _bending_patch(nodes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    target = np.asarray((0.375, -0.25, 0.625), dtype=np.float64)
    vector = np.zeros(18, dtype=np.float64)
    for node, (x, y) in enumerate(nodes):
        base = 6 * node
        vector[base + 2] = -0.5 * (target[0] * x * x + target[1] * y * y + target[2] * x * y)
        beta_x = target[0] * x + 0.5 * target[2] * y
        beta_y = target[1] * y + 0.5 * target[2] * x
        vector[base + 3] = -beta_y
        vector[base + 4] = beta_x
    return vector, target


def check_reference_case(nodes: Sequence[Sequence[float]], section: Sequence[Sequence[float]]) -> dict[str, Any]:
    """Independently reconstruct a supported arbitrary binary64 proof case."""

    assembled = _assemble_f(nodes, section)
    tolerance = 3.0e-11
    symmetry = max(
        _scaled_residual(matrix, matrix.T)
        for matrix in (assembled["physical"], assembled["pl"], assembled["condensed"], assembled["saddle"])
    )
    lower = assembled["saddle"][18:, 18:]
    coupling = assembled["saddle"][:18, 18:]
    schur = assembled["saddle"][:18, :18] - coupling @ np.linalg.solve(lower, coupling.T)
    schur_residual = _scaled_residual(schur, assembled["condensed"])
    rigid_residual = float(np.linalg.norm(assembled["condensed"] @ assembled["rigid"], ord=np.inf)) / max(
        float(np.linalg.norm(assembled["condensed"], ord=np.inf)), 1.0
    )
    equation37 = _scaled_residual(assembled["a_delta"] @ assembled["delta"], assembled["au"])

    parameters = assembled["parameters"]
    phi_formula = 2.0 * parameters["thickness"] ** 2 / (
        parameters["shear_correction"] * (1.0 - parameters["poisson"]) * assembled["lengths"] ** 2
    )
    phi_residual = _scaled_residual(assembled["phi"], phi_formula)

    patch, target = _bending_patch(assembled["nodes"])
    patch_au = float(np.linalg.norm(assembled["au"] @ patch, ord=np.inf))
    patch_curvature = max(float(np.linalg.norm(operator @ patch - target, ord=np.inf)) for operator in assembled["curvatures"])
    patch_shear = max(float(np.linalg.norm(operator @ patch, ord=np.inf)) for operator in assembled["shears"])

    probe = _probe_vector()
    direct_force = _direct_force_f(assembled, probe)
    station_resultants: list[np.ndarray] = []
    for station in range(3):
        operator = np.vstack(
            (assembled["b_membrane"], assembled["curvatures"][station], assembled["shears"][station])
        )
        resultants = assembled["section"] @ (operator @ probe)
        if resultants.shape != (8,) or not np.all(np.isfinite(resultants)):
            raise AssertionError("invalid independently reconstructed N/M/Q resultants")
        station_resultants.append(resultants)
    direct_force_residual = _scaled_residual(direct_force, assembled["physical"] @ probe)
    virtual = probe[::-1].copy()
    virtual_work_residual = abs(float(virtual @ direct_force) - float(virtual @ assembled["physical"] @ probe)) / max(
        abs(float(virtual @ assembled["physical"] @ probe)), 1.0
    )

    d3_residual = 0.0
    base_nodes = np.asarray(nodes, dtype=np.float64)
    for permutation in itertools.permutations(range(3)):
        transform = _block_permutation_f(permutation)
        permuted = _assemble_f(base_nodes[np.asarray(permutation)], section)
        d3_residual = max(
            d3_residual,
            _scaled_residual(permuted["condensed"], transform @ assembled["condensed"] @ transform.T),
        )

    thin = _assemble_f(nodes, _isotropic_section_f(100.0, 0.25, 1.0e-6))
    thick = _assemble_f(nodes, _isotropic_section_f(100.0, 0.25, 1.0e3))
    thin_factor = float(np.max(thin["phi"] / (1.0 + thin["phi"])))
    thick_factor = float(np.min(thick["phi"] / (1.0 + thick["phi"])))

    diagnostic_ranks = {
        "physical": _diagnostic_rank(assembled["physical"]),
        "pl": _diagnostic_rank(assembled["pl"]),
        "condensed": _diagnostic_rank(assembled["condensed"]),
        "saddle": _diagnostic_rank(assembled["saddle"]),
        "rigid": _diagnostic_rank(assembled["rigid"]),
    }
    diagnostic_inertia = _diagnostic_inertia(assembled["saddle"])
    exact = exact_canonical_certificate()
    checks = {
        "source_hash_bound": SOURCE_PDF_SHA256 == "CAACAB9E0DF9B4F8B55887E84FAFA923899677F7D0F285EB2EEB46FBDFF8D17A",
        "symmetry": symmetry <= tolerance,
        "schur": schur_residual <= tolerance,
        "rigid_null": rigid_residual <= tolerance,
        "equation37": equation37 <= tolerance,
        "phi_equivalence": phi_residual <= tolerance,
        "bending_patch": max(patch_au, patch_curvature, patch_shear) <= tolerance,
        "direct_variational_work": max(direct_force_residual, virtual_work_residual) <= tolerance,
        "d3_covariance": d3_residual <= tolerance,
        "thin_thick_limits": thin_factor < 1.0e-10 and thick_factor > 1.0 - 1.0e-5,
        "exact_canonical": exact["classification"] == "PASS_E4_PL_S3_V2A_DKMT_EXACT_CANONICAL",
    }
    residuals = {
        "d3": d3_residual,
        "direct_force": direct_force_residual,
        "equation37": equation37,
        "phi": phi_residual,
        "patch": max(patch_au, patch_curvature, patch_shear),
        "rigid": rigid_residual,
        "schur": schur_residual,
        "symmetry": symmetry,
        "virtual_work": virtual_work_residual,
    }
    return {
        "schema": "E4_PL_S3_V2A_FLAT_DKMT_CHECK_V1",
        "checker": CHECKER_IMPLEMENTATION_ID,
        "reference": EXPECTED_REFERENCE_IMPLEMENTATION_ID,
        "classification": "PASS_E4_PL_S3_V2A_FLAT_DKMT_REFERENCE" if all(checks.values()) else "NO_GO_E4_PL_S3_V2A_FLAT_DKMT_IDENTITY",
        "checks": checks,
        "counts": {"d3": 6, "hammer_stations": 3, "rigid_modes": 6},
        "diagnostic_ranks": diagnostic_ranks,
        "diagnostic_inertia": list(diagnostic_inertia),
        "rank_inertia_disposition": "EXACT_CANONICAL_CASE_ONLY_ARBITRARY_BINARY64_DIAGNOSTIC",
        "residuals": residuals,
        "limits": {"thin_rho_max": thin_factor, "thick_rho_min": thick_factor},
        "exact_canonical_sha256": _canonical_sha256(exact),
        "hashes": {
            "physical": _matrix_hash(assembled["physical"]),
            "pl": _matrix_hash(assembled["pl"]),
            "condensed": _matrix_hash(assembled["condensed"]),
            "saddle": _matrix_hash(assembled["saddle"]),
            "direct_force": _matrix_hash(direct_force),
            "station_resultants": _canonical_sha256({"rows": station_resultants}),
        },
    }


check_case = check_reference_case


def make_proof(nodes: Sequence[Sequence[float]], section: Sequence[Sequence[float]]) -> dict[str, Any]:
    report = check_reference_case(nodes, section)
    return {
        "schema": PROOF_SCHEMA,
        "nodes": np.asarray(nodes, dtype=np.float64),
        "section": np.asarray(section, dtype=np.float64),
        "claims": {
            "reference": EXPECTED_REFERENCE_IMPLEMENTATION_ID,
            "source_pdf_sha256": SOURCE_PDF_SHA256,
            "hashes": {
                name: report["hashes"][name]
                for name in ("physical", "pl", "condensed", "saddle", "direct_force", "station_resultants")
            },
        },
    }


def _reject_duplicate(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def _decode_canonical(value: Any) -> Any:
    if isinstance(value, list):
        return [_decode_canonical(item) for item in value]
    if isinstance(value, dict):
        if set(value) == {"binary64"}:
            number = float.fromhex(value["binary64"])
            if not math.isfinite(number):
                raise ValueError("nonfinite binary64 value")
            return number
        return {key: _decode_canonical(item) for key, item in value.items()}
    return value


def load_proof(raw: bytes) -> dict[str, Any]:
    encoded = json.loads(raw, object_pairs_hook=_reject_duplicate, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(f"nonfinite token: {token}")))
    decoded = _decode_canonical(encoded)
    if _canonical_bytes(decoded) != raw:
        raise ValueError("proof is not canonical")
    if not isinstance(decoded, dict) or set(decoded) != {"schema", "nodes", "section", "claims"}:
        raise ValueError("proof has an invalid top-level schema")
    if decoded["schema"] != PROOF_SCHEMA:
        raise ValueError("proof schema mismatch")
    return decoded


def verify_proof(proof: Mapping[str, Any] | bytes) -> dict[str, Any]:
    decoded = load_proof(proof) if isinstance(proof, bytes) else dict(proof)
    if decoded.get("schema") != PROOF_SCHEMA:
        raise ValueError("proof schema mismatch")
    report = check_reference_case(decoded["nodes"], decoded["section"])
    expected_claims = {
        "reference": EXPECTED_REFERENCE_IMPLEMENTATION_ID,
        "source_pdf_sha256": SOURCE_PDF_SHA256,
        "hashes": {
            name: report["hashes"][name]
            for name in ("physical", "pl", "condensed", "saddle", "direct_force", "station_resultants")
        },
    }
    if decoded.get("claims") != expected_claims:
        raise ValueError("proof claims disagree with independent reconstruction")
    return report


def canonical_report_bytes(report: Mapping[str, Any]) -> bytes:
    return _canonical_bytes(report)


__all__ = [
    "CHECKER_IMPLEMENTATION_ID",
    "EXACT_CASE_ID",
    "PROOF_SCHEMA",
    "canonical_report_bytes",
    "check_case",
    "check_reference_case",
    "exact_canonical_certificate",
    "load_proof",
    "make_proof",
    "verify_proof",
]
