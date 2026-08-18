"""Independent exact oracle for the E4-PL Q1A planar qualification.

The oracle deliberately does not import the research implementation.  It
reconstructs the 35-field WG core and the three-field perturbed-Lagrange
block from their frozen discrete spaces.  All four 2 x 2 Gauss stations are
evaluated in Q(sqrt(3)); no floating-point rank decision is made.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "docs/reference_cases/e4_pl_q1a_cases.json"
CONTRACT_PATH = ROOT / "docs/reference_cases/e4_pl_q1a_contract.json"
STUDY_ID = "candidate_e4_pl_q1.wg2020_n7_k0_surface_pl_planar_linear_iso_v1"
PASS_TERMINAL = "PROVISIONAL_GO_E4_PL_Q1B_NONINTRUSION_STABILITY_LOCKING_PLAN"
RELEASE_TERMINAL = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
PINNED_PYTHON = "C:/Python/Python313/python.exe"
PINNED_PYTHON_VERSION = "3.13.9"

# The coordinator freezes these paths before emitting the caller-bound
# contract.  Their raw hashes, including this oracle, become contract inputs.
CONTRACT_INPUTS = [
    "docs/agent_plans/S4_E4_PL_PLANAR_LINEAR_QUALIFICATION_PLAN.md",
    "docs/E4_PL_Q1A_PLAN_REVIEW.md",
    "docs/E4_PL_Q1A_PLANAR_IDENTITY.md",
    "docs/E4_PL_Q1A_LOCAL_ALGEBRA.md",
    "docs/reference_cases/e4_pl_q1a_baseline.json",
    "docs/reference_cases/e4_pl_q1a_environment.json",
    "docs/reference_cases/e4_pl_q1a_source_map.json",
    "docs/reference_cases/e4_pl_q1a_geometry_contract.json",
    "docs/reference_cases/e4_pl_q1a_material_contract.json",
    "docs/reference_cases/e4_pl_q1a_support_contract.json",
    "docs/reference_cases/e4_pl_q1a_cases.json",
    "docs/reference_cases/e4_pl_q1a_tolerances.json",
    "docs/reference_cases/e4_pl_q1a_terminal_table.json",
    "docs/reference_cases/e4_pl_q1a_test_inventory.json",
    "docs/reference_cases/e4_pl_q1a_allowed_extent.json",
    "docs/reference_cases/e4_pl_q1a_reference.py",
]


class EvidenceError(Exception):
    """A frozen input or exact scientific identity is invalid."""


class BaselineMismatch(EvidenceError):
    """The immutable baseline or accepted E4 evidence changed."""


class PlanAuthorityError(EvidenceError):
    """A preregistered authority/environment/manifest row changed."""


class SourceIdentityError(EvidenceError):
    """The source-exact non-affine formulation is absent or nonunique."""


class ContractError(Exception):
    """Caller-bound execution evidence is invalid."""


class OracleReviewError(EvidenceError):
    """Independent execution or review evidence disagrees."""


class LocalAlgebraError(EvidenceError):
    """An exact stationary-block, rank, or Schur gate failed."""


class PatchCovarianceError(EvidenceError):
    """An exact patch or covariance gate failed."""


class MaterialRecoveryError(EvidenceError):
    """The DNV material interface or recovery separation failed."""


class UnclassifiedError(EvidenceError):
    """The exact evidence budget was exhausted without a classification."""


TERMINALS_BY_EXCEPTION: tuple[tuple[type[BaseException], str], ...] = (
    (BaselineMismatch, "BLOCKED_E4_PL_Q1A_BASELINE_MISMATCH"),
    (PlanAuthorityError, "BLOCKED_E4_PL_Q1A_PLAN_AUTHORITY"),
    (SourceIdentityError, "BLOCKED_E4_PL_Q1A_SOURCE_OR_PLANAR_IDENTITY"),
    (ContractError, "BLOCKED_E4_PL_Q1A_CONTRACT_OR_NONDETERMINISM"),
    (OracleReviewError, "BLOCKED_E4_PL_Q1A_ORACLE_OR_REVIEW"),
    (LocalAlgebraError, "NO_GO_E4_PL_Q1A_LOCAL_ALGEBRA"),
    (PatchCovarianceError, "NO_GO_E4_PL_Q1A_PATCH_OR_COVARIANCE"),
    (MaterialRecoveryError, "NO_GO_E4_PL_Q1A_DNV_MATERIAL_OR_RECOVERY_CONTRACT"),
    (UnclassifiedError, "UNCLASSIFIED_E4_PL_Q1A_PLANAR_IDENTITY_AND_LOCAL_ALGEBRA"),
    (EvidenceError, "BLOCKED_E4_PL_Q1A_ORACLE_OR_REVIEW"),
)


@dataclass(frozen=True)
class Q3:
    """Exact element ``a + b*sqrt(3)`` of Q(sqrt(3))."""

    a: Fraction = Fraction(0)
    b: Fraction = Fraction(0)

    @staticmethod
    def coerce(value: object) -> "Q3":
        if isinstance(value, Q3):
            return value
        if isinstance(value, (int, Fraction)) and not isinstance(value, bool):
            return Q3(Fraction(value))
        raise TypeError(f"not a Q(sqrt(3)) scalar: {value!r}")

    def __add__(self, other: object) -> "Q3":
        rhs = self.coerce(other)
        return Q3(self.a + rhs.a, self.b + rhs.b)

    __radd__ = __add__

    def __neg__(self) -> "Q3":
        return Q3(-self.a, -self.b)

    def __sub__(self, other: object) -> "Q3":
        return self + (-self.coerce(other))

    def __rsub__(self, other: object) -> "Q3":
        return self.coerce(other) - self

    def __mul__(self, other: object) -> "Q3":
        rhs = self.coerce(other)
        return Q3(self.a * rhs.a + 3 * self.b * rhs.b,
                  self.a * rhs.b + self.b * rhs.a)

    __rmul__ = __mul__

    def __truediv__(self, other: object) -> "Q3":
        rhs = self.coerce(other)
        denominator = rhs.a * rhs.a - 3 * rhs.b * rhs.b
        if not denominator:
            raise ZeroDivisionError("zero divisor in Q(sqrt(3))")
        return self * Q3(rhs.a / denominator, -rhs.b / denominator)

    def __rtruediv__(self, other: object) -> "Q3":
        return self.coerce(other) / self

    def __pow__(self, exponent: int) -> "Q3":
        if not isinstance(exponent, int):
            return NotImplemented
        if exponent < 0:
            return (_q(1) / self) ** (-exponent)
        result, factor, power = _q(1), self, exponent
        while power:
            if power & 1:
                result *= factor
            factor *= factor
            power //= 2
        return result

    def __bool__(self) -> bool:
        return bool(self.a or self.b)

    def sign(self) -> int:
        if not self:
            return 0
        if self.a >= 0 and self.b >= 0:
            return 1
        if self.a <= 0 and self.b <= 0:
            return -1
        magnitude = self.a * self.a - 3 * self.b * self.b
        if not magnitude:
            raise EvidenceError("irrational cancellation reached rational zero")
        if self.a > 0:
            return 1 if magnitude > 0 else -1
        return -1 if magnitude > 0 else 1

    def __lt__(self, other: object) -> bool:
        return (self - self.coerce(other)).sign() < 0

    def __le__(self, other: object) -> bool:
        return (self - self.coerce(other)).sign() <= 0

    def __gt__(self, other: object) -> bool:
        return (self - self.coerce(other)).sign() > 0

    def __ge__(self, other: object) -> bool:
        return (self - self.coerce(other)).sign() >= 0

    def absolute(self) -> "Q3":
        return self if self.sign() >= 0 else -self

    def signature(self) -> str:
        if not self.b:
            return str(self.a)
        return f"{self.a}{'+' if self.b >= 0 else ''}{self.b}*sqrt(3)"


Scalar = Q3
Vector = list[Scalar]
Matrix = list[list[Scalar]]


def _q(value: int | Fraction = 0, radical: int | Fraction = 0) -> Scalar:
    return Q3(Fraction(value), Fraction(radical))


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
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


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


def _zeros(rows: int, columns: int) -> Matrix:
    return [[_q() for _ in range(columns)] for _ in range(rows)]


def _identity(size: int) -> Matrix:
    result = _zeros(size, size)
    for index in range(size):
        result[index][index] = _q(1)
    return result


def _transpose(matrix: Matrix) -> Matrix:
    return [list(column) for column in zip(*matrix)] if matrix else []


def _multiply(left: Matrix, right: Matrix) -> Matrix:
    if not left or not right or len(left[0]) != len(right):
        raise EvidenceError("matrix product dimension mismatch")
    columns = _transpose(right)
    return [[sum((a * b for a, b in zip(row, column)), _q()) for column in columns]
            for row in left]


def _matvec(matrix: Matrix, vector: Vector) -> Vector:
    if matrix and len(matrix[0]) != len(vector):
        raise EvidenceError("matrix-vector dimension mismatch")
    return [sum((a * b for a, b in zip(row, vector)), _q()) for row in matrix]


def _add(left: Matrix, right: Matrix, scale: Scalar = _q(1)) -> Matrix:
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        raise EvidenceError("matrix sum dimension mismatch")
    return [[a + scale * b for a, b in zip(row_a, row_b)]
            for row_a, row_b in zip(left, right)]


def _scale(matrix: Matrix, factor: Scalar) -> Matrix:
    return [[factor * value for value in row] for row in matrix]


def _dot(left: Vector, right: Vector) -> Scalar:
    if len(left) != len(right):
        raise EvidenceError("dot-product dimension mismatch")
    return sum((a * b for a, b in zip(left, right)), _q())


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
            (lower[column][k] * lower[column][k] * pivots[k] for k in range(column)), _q()
        )
        if not pivot:
            raise EvidenceError("zero exact LDL pivot")
        pivots.append(pivot)
        for row in range(column + 1, size):
            lower[row][column] = (
                matrix[row][column]
                - sum((lower[row][k] * lower[column][k] * pivots[k]
                       for k in range(column)), _q())
            ) / pivot
    return pivots


def _matrix_signature(matrix: Matrix) -> list[list[str]]:
    return [[entry.signature() for entry in row] for row in matrix]


def _matrix_digest(matrix: Matrix) -> dict[str, object]:
    raw = _canonical(_matrix_signature(matrix))
    return {
        "bytes": len(raw),
        "nonzeros": sum(bool(value) for row in matrix for value in row),
        "sha256": _sha(raw),
        "shape": [len(matrix), len(matrix[0]) if matrix else 0],
    }


REFERENCE_NODES = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
GAUSS = [(_q(0, -Fraction(1, 3)), _q(0, -Fraction(1, 3))),
         (_q(0, Fraction(1, 3)), _q(0, -Fraction(1, 3))),
         (_q(0, Fraction(1, 3)), _q(0, Fraction(1, 3))),
         (_q(0, -Fraction(1, 3)), _q(0, Fraction(1, 3)))]


def _shape(r: Scalar, s: Scalar) -> tuple[Vector, Vector, Vector]:
    values, dr, ds = [], [], []
    for ri, si in REFERENCE_NODES:
        values.append((_q(1) + ri * r) * (_q(1) + si * s) / 4)
        dr.append(ri * (_q(1) + si * s) / 4)
        ds.append(si * (_q(1) + ri * r) / 4)
    return values, dr, ds


def _jacobian(nodes: list[tuple[Fraction, Fraction]], r: Scalar, s: Scalar) -> Matrix:
    unused, dr, ds = _shape(r, s)
    del unused
    return [[sum((_q(x) * value for (x, unused_y), value in zip(nodes, dr)), _q()),
             sum((_q(x) * value for (x, unused_y), value in zip(nodes, ds)), _q())],
            [sum((_q(y) * value for (unused_x, y), value in zip(nodes, dr)), _q()),
             sum((_q(y) * value for (unused_x, y), value in zip(nodes, ds)), _q())]]


def _det2(matrix: Matrix) -> Scalar:
    return matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]


def _inverse2(matrix: Matrix) -> Matrix:
    determinant = _det2(matrix)
    if not determinant:
        raise EvidenceError("singular planar Jacobian")
    return [[matrix[1][1] / determinant, -matrix[0][1] / determinant],
            [-matrix[1][0] / determinant, matrix[0][0] / determinant]]


def _gradient(nodes: list[tuple[Fraction, Fraction]], r: Scalar, s: Scalar
              ) -> tuple[Vector, Vector, Matrix, Scalar]:
    unused, dr, ds = _shape(r, s)
    del unused
    jacobian = _jacobian(nodes, r, s)
    determinant = _det2(jacobian)
    if determinant.sign() <= 0:
        raise EvidenceError("nonpositive Jacobian in admitted planar case")
    inverse = _inverse2(jacobian)
    dx = [inverse[0][0] * nr + inverse[1][0] * ns for nr, ns in zip(dr, ds)]
    dy = [inverse[0][1] * nr + inverse[1][1] * ns for nr, ns in zip(dr, ds)]
    return dx, dy, jacobian, determinant


def _tensor_transform(jacobian: Matrix, a: Scalar, b: Scalar) -> Matrix:
    x_r, x_s = jacobian[0]
    y_r, y_s = jacobian[1]
    return [[x_r*x_r, y_r*y_r, a*x_r*y_r],
            [x_s*x_s, y_s*y_s, a*x_s*y_s],
            [b*x_r*x_s, b*y_r*y_s, x_r*y_s+x_s*y_r]]


def _apply_seed(target: Matrix, row_offset: int, columns: list[int],
                transform: Matrix, seeds: Matrix) -> None:
    for local_column, global_column in enumerate(columns):
        for output_row, transform_row in enumerate(transform):
            target[row_offset + output_row][global_column] = sum(
                (seeds[input_row][local_column] * coefficient
                 for input_row, coefficient in enumerate(transform_row)), _q()
            )


def _source_spaces(center_j: Matrix, r: Scalar, s: Scalar, determinant: Scalar,
                   bar_r: Scalar, bar_s: Scalar) -> tuple[Matrix, Matrix]:
    n_sigma, n_epsilon = _zeros(8, 14), _zeros(8, 21)
    for index in range(8):
        n_sigma[index][index] = n_epsilon[index][index] = _q(1)
    tensor_seed = [[s - bar_s, _q()], [_q(), r - bar_r], [_q(), _q()]]
    vector_seed = [[s - bar_s, _q()], [_q(), r - bar_r]]
    for target, transform in (
        (n_sigma, _tensor_transform(center_j, _q(2), _q(1))),
        (n_epsilon, _tensor_transform(center_j, _q(1), _q(2))),
    ):
        _apply_seed(target, 0, [8, 9], transform, tensor_seed)
        _apply_seed(target, 3, [10, 11], transform, tensor_seed)
        _apply_seed(target, 6, [12, 13], center_j, vector_seed)
    center_det = _det2(center_j)
    enhancement_scale = center_det / determinant
    enrichment = [[enhancement_scale*r, _q(), _q(), _q(), enhancement_scale*r*s, _q(), _q()],
                  [_q(), enhancement_scale*s, _q(), _q(), _q(), enhancement_scale*r*s, _q()],
                  [_q(), _q(), enhancement_scale*r, enhancement_scale*s,
                   _q(), _q(), enhancement_scale*r*s]]
    _apply_seed(n_epsilon, 0, list(range(14, 21)),
                _tensor_transform(center_j, _q(1), _q(2)), enrichment)
    return n_sigma, n_epsilon


def _compatible_map(nodes: list[tuple[Fraction, Fraction]], r: Scalar, s: Scalar) -> Matrix:
    """Source MITC-compatible strain map at one Gauss station."""

    values, unused_dr, unused_ds = _shape(r, s)
    del values, unused_dr, unused_ds
    dx, dy, jacobian, unused_det = _gradient(nodes, r, s)
    del unused_det
    result = _zeros(8, 20)
    for node in range(4):
        u, v, w, rx, ry = (5 * node + offset for offset in range(5))
        result[0][u] = dx[node]
        result[1][v] = dy[node]
        result[2][u] = dy[node]
        result[2][v] = dx[node]
        result[3][ry] = dx[node]
        result[4][rx] = -dy[node]
        result[5][ry] = dy[node]
        result[5][rx] = -dx[node]

    # WG2004 equations 19-21: sample the covariant r shear at the two
    # r=0 edge-midpoint lines s=+/-1, and the covariant s shear at the two
    # s=0 lines r=+/-1; interpolate those tied values before transforming at
    # the current station.
    def tied(direction: str, coordinate: int) -> Vector:
        rr, ss = (_q(), _q(coordinate)) if direction == "r" \
            else (_q(coordinate), _q())
        values_t, dr_t, ds_t = _shape(rr, ss)
        jacobian_t = _jacobian(nodes, rr, ss)
        row = [_q() for _ in range(20)]
        for node in range(4):
            w, rx, ry = 5*node+2, 5*node+3, 5*node+4
            if direction == "r":
                row[w] += dr_t[node]
                row[ry] += jacobian_t[0][0] * values_t[node]
                row[rx] -= jacobian_t[1][0] * values_t[node]
            else:
                row[w] += ds_t[node]
                row[ry] += jacobian_t[0][1] * values_t[node]
                row[rx] -= jacobian_t[1][1] * values_t[node]
        return row

    tied_r_minus, tied_r_plus = tied("r", -1), tied("r", 1)
    tied_s_minus, tied_s_plus = tied("s", -1), tied("s", 1)
    tied_r = [(_q(1)-s)*minus/2 + (_q(1)+s)*plus/2
              for minus, plus in zip(tied_r_minus, tied_r_plus)]
    tied_s = [(_q(1)-r)*minus/2 + (_q(1)+r)*plus/2
              for minus, plus in zip(tied_s_minus, tied_s_plus)]
    inverse = _inverse2(jacobian)
    result[6] = [inverse[0][0] * a + inverse[1][0] * b
                 for a, b in zip(tied_r, tied_s)]
    result[7] = [inverse[0][1] * a + inverse[1][1] * b
                 for a, b in zip(tied_r, tied_s)]
    return result


def _constitutive(e: Scalar, nu: Scalar, thickness: Scalar, shear: Scalar) -> Matrix:
    factor = e / (_q(1) - nu * nu)
    membrane = [[factor, factor * nu, _q()],
                [factor * nu, factor, _q()],
                [_q(), _q(), factor * (_q(1) - nu) / 2]]
    result = _zeros(8, 8)
    for row in range(3):
        for column in range(3):
            result[row][column] = thickness * membrane[row][column]
            result[3 + row][3 + column] = thickness**3 * membrane[row][column] / 12
    result[6][6] = result[7][7] = _q(5, 0) * shear * thickness / 6
    return result


def _assemble_core(nodes: list[tuple[Fraction, Fraction]], e: Scalar, nu: Scalar,
                   thickness: Scalar, shear: Scalar) -> dict[str, Matrix]:
    """Assemble the actual 14/21 WG stationary fields by positive 2 x 2."""

    center_j = _jacobian(nodes, _q(), _q())
    center_det = _det2(center_j)
    det_r = _det2(_jacobian(nodes, _q(1), _q())) - center_det
    det_s = _det2(_jacobian(nodes, _q(), _q(1))) - center_det
    bar_r, bar_s = det_r / (3 * center_det), det_s / (3 * center_det)
    material = _constitutive(e, nu, thickness, shear)
    f, h_matrix, gq = _zeros(21, 14), _zeros(21, 21), _zeros(14, 20)
    for r, s in GAUSS:
        unused_dx, unused_dy, unused_j, determinant = _gradient(nodes, r, s)
        del unused_dx, unused_dy, unused_j
        n_sigma, n_epsilon = _source_spaces(
            center_j, r, s, determinant, bar_r, bar_s
        )
        b_map = _compatible_map(nodes, r, s)
        for strain in range(21):
            for stress in range(14):
                f[strain][stress] -= determinant * sum(
                    (n_epsilon[component][strain] * n_sigma[component][stress]
                     for component in range(8)), _q()
                )
            for other in range(21):
                h_matrix[strain][other] += determinant * sum(
                    (material[left][right] * n_epsilon[left][strain]
                     * n_epsilon[right][other]
                     for left in range(8) for right in range(8)
                     if material[left][right]), _q()
                )
        for stress in range(14):
            for coordinate in range(20):
                gq[stress][coordinate] += determinant * sum(
                    (n_sigma[component][stress] * b_map[component][coordinate]
                     for component in range(8)), _q()
                )
    d = _zeros(35, 35)
    for stress in range(14):
        for strain in range(21):
            d[stress][14 + strain] = d[14 + strain][stress] = f[strain][stress]
    for left in range(21):
        for right in range(21):
            d[14 + left][14 + right] = h_matrix[left][right]
    d_inverse = _inverse(d)
    q20 = [row + [_q()] * 21 for row in _transpose(gq)]
    k5 = _scale(_multiply(_multiply(q20, d_inverse), _transpose(q20)), -_q(1))
    s_matrix = _scale([row[:14] for row in d_inverse[:14]], -_q(1))
    return {"D": d, "D_inverse": d_inverse, "F": f, "Gq": gq,
            "H": h_matrix, "K5": k5, "Q20": q20, "S": s_matrix}


def _selectors() -> tuple[Matrix, Matrix]:
    t5, qd = _zeros(24, 20), _zeros(24, 4)
    for node in range(4):
        for local in range(5):
            t5[6 * node + local][5 * node + local] = _q(1)
        qd[6 * node + 5][node] = _q(1)
    return t5, qd


def _modal_rows() -> Matrix:
    return [[_q(1, 0)/4, _q(1, 0)/4, _q(1, 0)/4, _q(1, 0)/4],
            [-_q(1)/4, _q(1)/4, _q(1)/4, -_q(1)/4],
            [-_q(1)/4, -_q(1)/4, _q(1)/4, _q(1)/4],
            [_q(1)/4, -_q(1)/4, _q(1)/4, -_q(1)/4]]


def _modal_geometry(nodes: list[tuple[Fraction, Fraction]]) -> tuple[Vector, Vector]:
    modal = _modal_rows()
    x = [_q(node[0]) for node in nodes]
    y = [_q(node[1]) for node in nodes]
    return _matvec(modal, x), _matvec(modal, y)


def _center_constraint(nodes: list[tuple[Fraction, Fraction]]) -> Matrix:
    """Centre Taylor rows [c(0), c_,r(0), c_,s(0)] from WT 26.42."""

    x, y = _modal_geometry(nodes)
    x0, xr, xs, xrs = x
    y0, yr, ys, yrs = y
    del x0, y0
    jc = xr * ys - xs * yr
    jr = xr * yrs - xrs * yr
    js = xrs * ys - xs * yrs
    if jc.sign() <= 0:
        raise EvidenceError("nonpositive centre Jacobian")
    modal = _modal_rows()
    rows = _zeros(3, 24)
    for node in range(4):
        u, v, drill = 6 * node, 6 * node + 1, 6 * node + 5
        u0, ur, us, urs = (modal[index][node] for index in range(4))
        v0, vr, vs, vrs = (modal[index][node] for index in range(4))
        del u0, v0
        n0_u = -xs * ur + xr * us
        nr_u = -xrs * ur + xr * urs
        ns_u = -xs * urs + xrs * us
        n0_v = -ys * vr + yr * vs
        nr_v = -yrs * vr + yr * vrs
        ns_v = -ys * vrs + yrs * vs
        rows[0][u] += n0_u / (2 * jc)
        rows[0][v] += n0_v / (2 * jc)
        rows[1][u] += (nr_u * jc - n0_u * jr) / (2 * jc * jc)
        rows[1][v] += (nr_v * jc - n0_v * jr) / (2 * jc * jc)
        rows[2][u] += (ns_u * jc - n0_u * js) / (2 * jc * jc)
        rows[2][v] += (ns_v * jc - n0_v * js) / (2 * jc * jc)
        rows[0][drill] = modal[0][node]
        rows[1][drill] = modal[1][node]
        rows[2][drill] = modal[2][node]
    return rows


def _gamma_row(nodes: list[tuple[Fraction, Fraction]]) -> Vector:
    """Geometry-dependent residual-drill row from WT equations 26.44-26.45."""

    xi = [_q(-1), _q(1), _q(1), _q(-1)]
    eta = [_q(-1), _q(-1), _q(1), _q(1)]
    hourglass = [_q(1), _q(-1), _q(1), _q(-1)]
    xc = sum((_q(x) for x, unused_y in nodes), _q()) / 4
    yc = sum((_q(y) for unused_x, y in nodes), _q()) / 4
    s1 = [_q(x) - xc for x, unused_y in nodes]
    s2 = [_q(y) - yc for unused_x, y in nodes]
    center_det = _det2(_jacobian(nodes, _q(), _q()))
    area = 4 * center_det
    b1 = [(_dot(eta, s2) * xi_i - _dot(xi, s2) * eta_i) / (4 * area)
          for xi_i, eta_i in zip(xi, eta)]
    b2 = [(-_dot(eta, s1) * xi_i + _dot(xi, s1) * eta_i) / (4 * area)
          for xi_i, eta_i in zip(xi, eta)]
    gamma = [(h_i - _dot(hourglass, s1) * b1_i
              - _dot(hourglass, s2) * b2_i) / 4
             for h_i, b1_i, b2_i in zip(hourglass, b1, b2)]
    row = [_q() for _ in range(24)]
    for node, value in enumerate(gamma):
        row[6 * node + 5] = value
    return row


def _pl_mass(nodes: list[tuple[Fraction, Fraction]], thickness: Scalar) -> Matrix:
    mass = _zeros(3, 3)
    for r, s in GAUSS:
        determinant = _det2(_jacobian(nodes, r, s))
        if determinant.sign() <= 0:
            raise EvidenceError("nonpositive Jacobian in PL integration")
        p = [_q(1), r, s]
        for row in range(3):
            for column in range(3):
                mass[row][column] += thickness * determinant * p[row] * p[column]
    return mass


def _numerical_forms(nodes: list[tuple[Fraction, Fraction]], thickness: Scalar,
                     shear: Scalar, epsilon: Scalar) -> dict[str, Matrix | Vector | Scalar]:
    c = _center_constraint(nodes)
    mass = _pl_mass(nodes, thickness)
    b = _multiply(mass, c)
    hrow = _gamma_row(nodes)
    area = 4 * _det2(_jacobian(nodes, _q(), _q()))
    k_pl = _scale(_multiply(_transpose(c), _multiply(mass, c)), shear)
    k_hg = _scale(_multiply(_transpose([hrow]), [hrow]),
                  2 * epsilon * shear * thickness * area)
    l_map = c + [hrow]
    weight = _zeros(4, 4)
    for row in range(3):
        for column in range(3):
            weight[row][column] = shear * mass[row][column]
    weight[3][3] = 2 * epsilon * shear * thickness * area
    return {"A": area, "B": b, "C": c, "Hrow": hrow, "K_hg": k_hg,
            "K_pl": k_pl, "L": l_map, "M": mass, "W": weight}


def _energy(matrix: Matrix, vector: Vector) -> Scalar:
    return _dot(vector, _matvec(matrix, vector)) / 2


def _embed_physical(vector: Vector, drill: Vector | None = None) -> Vector:
    if len(vector) != 20 or drill is not None and len(drill) != 4:
        raise EvidenceError("physical/drill embedding dimension mismatch")
    result = [_q() for _ in range(24)]
    for node in range(4):
        result[6*node:6*node+5] = vector[5*node:5*node+5]
        if drill is not None:
            result[6*node+5] = drill[node]
    return result


def _rigid_vectors(nodes: list[tuple[Fraction, Fraction]]) -> dict[str, Vector]:
    result = {name: [] for name in (
        "translation_x", "translation_y", "translation_z",
        "rotation_x", "rotation_y", "rotation_z",
    )}
    for x_raw, y_raw in nodes:
        x, y = _q(x_raw), _q(y_raw)
        result["translation_x"].extend((_q(1), _q(), _q(), _q(), _q(), _q()))
        result["translation_y"].extend((_q(), _q(1), _q(), _q(), _q(), _q()))
        result["translation_z"].extend((_q(), _q(), _q(1), _q(), _q(), _q()))
        result["rotation_x"].extend((_q(), _q(), y, _q(1), _q(), _q()))
        result["rotation_y"].extend((_q(), _q(), -x, _q(), _q(1), _q()))
        result["rotation_z"].extend((-y, x, _q(), _q(), _q(), _q(1)))
    return result


def _patch_vectors(nodes: list[tuple[Fraction, Fraction]]) -> dict[str, Vector]:
    patches: dict[str, Vector] = {}
    definitions = {
        "constant_membrane_x": (_q(1), _q(), _q(), _q()),
        "constant_symmetric_shear": (_q(), _q(Fraction(1, 2)),
                                      _q(Fraction(1, 2)), _q()),
        "combined_membrane": (_q(2), _q(Fraction(1, 3)),
                              _q(Fraction(-2, 5)), _q(Fraction(4, 3))),
    }
    for name, (ux, uy, vx, vy) in definitions.items():
        vector: Vector = []
        drill = (vx - uy) / 2
        for x_raw, y_raw in nodes:
            x, y = _q(x_raw), _q(y_raw)
            vector.extend((ux*x + uy*y, vx*x + vy*y, _q(), _q(), _q(), drill))
        patches[name] = vector
    patches["matched_continuum_spin"] = _rigid_vectors(nodes)["rotation_z"]
    bending: Vector = []
    shear: Vector = []
    kxx, kyy, kxy = _q(Fraction(2, 5)), _q(Fraction(-1, 3)), _q(Fraction(3, 7))
    shear_x, shear_y = _q(Fraction(2, 3)), _q(Fraction(-1, 4))
    for x_raw, y_raw in nodes:
        x, y = _q(x_raw), _q(y_raw)
        w = -kxx*x*x/2 - kxy*x*y/2 - kyy*y*y/2
        rx = -kxy*x/2 - kyy*y
        ry = kxx*x + kxy*y/2
        bending.extend((_q(), _q(), w, rx, ry, _q()))
        shear.extend((_q(), _q(), _q(), -shear_y, shear_x, _q()))
    patches["constant_bending_x"] = bending
    patches["constant_transverse_shear_x"] = shear
    return patches


def _physical_patch_certificate(nodes: list[tuple[Fraction, Fraction]],
                                core: dict[str, Matrix], forms: dict[str, object],
                                e: Scalar, nu: Scalar, thickness: Scalar,
                                shear: Scalar) -> dict[str, dict[str, bool]]:
    """Prove compatible energy and stationary-resultant patch identities."""

    patches = _patch_vectors(nodes)
    targets: dict[str, Vector] = {
        "constant_membrane_x": [_q(1), _q(), _q(), _q(), _q(), _q(), _q(), _q()],
        "constant_symmetric_shear": [_q(), _q(), _q(1), _q(), _q(), _q(), _q(), _q()],
        "combined_membrane": [_q(2), _q(Fraction(4, 3)), _q(Fraction(-1, 15)),
                              _q(), _q(), _q(), _q(), _q()],
        "constant_bending_x": [_q(), _q(), _q(), _q(Fraction(2, 5)),
                                _q(Fraction(-1, 3)), _q(Fraction(3, 7)), _q(), _q()],
        "constant_transverse_shear_x": [_q(), _q(), _q(), _q(), _q(), _q(),
                                        _q(Fraction(2, 3)), _q(Fraction(-1, 4))],
    }
    combined_names = (
        "combined_membrane", "constant_bending_x", "constant_transverse_shear_x",
    )
    patches["combined_physical"] = [
        sum((patches[name][index] for name in combined_names), _q())
        for index in range(24)
    ]
    targets["combined_physical"] = [
        sum((targets[name][index] for name in combined_names), _q())
        for index in range(8)
    ]
    t5, unused_qd = _selectors()
    del unused_qd
    material = _constitutive(e, nu, thickness, shear)
    area = sum((_det2(_jacobian(nodes, r, s)) for r, s in GAUSS), _q())
    l_map = forms.get("L")
    if not isinstance(l_map, list):
        raise PatchCovarianceError("numerical patch operator missing")
    certificate: dict[str, dict[str, bool]] = {}
    for name, target in targets.items():
        q24 = patches[name]
        p20 = _matvec(_transpose(t5), q24)
        compatible = True
        recovered = True
        z = [-value for value in _matvec(
            core["D_inverse"], _matvec(_transpose(core["Q20"]), p20)
        )]
        stress_parameters = z[:14]
        for r, s in GAUSS:
            b_map = _compatible_map(nodes, r, s)
            if _matvec(b_map, p20) != target:
                compatible = False
            determinant = _det2(_jacobian(nodes, r, s))
            center_j = _jacobian(nodes, _q(), _q())
            center_det = _det2(center_j)
            det_r = _det2(_jacobian(nodes, _q(1), _q())) - center_det
            det_s = _det2(_jacobian(nodes, _q(), _q(1))) - center_det
            n_sigma, unused_n_epsilon = _source_spaces(
                center_j, r, s, determinant,
                det_r/(3*center_det), det_s/(3*center_det),
            )
            del unused_n_epsilon
            observed = _matvec(n_sigma, stress_parameters)
            expected = _matvec(material, target)
            if observed != expected:
                recovered = False
        expected_energy = area * _dot(target, _matvec(material, target)) / 2
        certificate[name] = {
            "compatible_strain_exact": compatible,
            "energy_exact": _energy(core["K5"], p20) == expected_energy,
            "matched_drill_numerical_zero": not any(_matvec(l_map, q24)),
            "stationary_resultant_exact": recovered,
        }
    return certificate


def _case_nodes(value: object) -> list[tuple[Fraction, Fraction]]:
    if not isinstance(value, list) or len(value) != 4:
        raise EvidenceError("geometry must contain four nodes")
    result: list[tuple[Fraction, Fraction]] = []
    for node in value:
        if not isinstance(node, list) or len(node) != 2:
            raise EvidenceError("malformed planar node")
        if any(not isinstance(item, (str, int)) or isinstance(item, bool) for item in node):
            raise EvidenceError("nonexact planar coordinate")
        result.append((Fraction(node[0]), Fraction(node[1])))
    return result


def _d4_maps() -> list[list[list[int]]]:
    result: list[list[list[int]]] = []
    for swap in (False, True):
        for sign_r in (-1, 1):
            for sign_s in (-1, 1):
                if swap:
                    result.append([[0, sign_r], [sign_s, 0]])
                else:
                    result.append([[sign_r, 0], [0, sign_s]])
    return result


def _d4_permutation(transform: list[list[int]]) -> list[int]:
    result: list[int] = []
    for r, s in REFERENCE_NODES:
        old = (transform[0][0]*r + transform[0][1]*s,
               transform[1][0]*r + transform[1][1]*s)
        result.append(REFERENCE_NODES.index(old))
    return result


def _state_map(permutation: list[int], frame: Matrix, *, external: int,
               length_scale: Scalar = _q(1)) -> Matrix:
    """Map an old nodal state to a transformed/relabelled nodal state.

    ``frame`` is the in-plane block of the proper three-dimensional frame
    transformation ``diag(frame, det(frame))``.  Translations carry length
    scaling; rotations do not.  The drill coordinate carries the transformed
    director-normal sign exactly when ``det(frame)=-1``.
    """

    if len(permutation) != 4 or external not in (20, 24):
        raise PatchCovarianceError("invalid covariance state-map dimensions")
    block = 5 if external == 20 else 6
    determinant = _det2(frame)
    if determinant not in (_q(-1), _q(1)):
        raise PatchCovarianceError("frame must be rational orthogonal with determinant +/-1")
    result = _zeros(external, external)
    for new_node, old_node in enumerate(permutation):
        new, old = block*new_node, block*old_node
        for row in range(2):
            for column in range(2):
                result[new+row][old+column] = length_scale * frame[row][column]
                result[new+3+row][old+3+column] = frame[row][column]
        result[new+2][old+2] = length_scale * determinant
        if block == 6:
            result[new+5][old+5] = determinant
    return result


def _transform_nodes(nodes: list[tuple[Fraction, Fraction]], permutation: list[int],
                     frame: Matrix, scale: Scalar = _q(1),
                     shift: tuple[Scalar, Scalar] = (_q(), _q())
                     ) -> list[tuple[Fraction, Fraction]]:
    result: list[tuple[Fraction, Fraction]] = []
    for old_node in permutation:
        x, y = (_q(value) for value in nodes[old_node])
        transformed = [scale*(frame[0][0]*x + frame[0][1]*y) + shift[0],
                       scale*(frame[1][0]*x + frame[1][1]*y) + shift[1]]
        if any(value.b for value in transformed):
            raise PatchCovarianceError("registered transform left rational geometry field")
        result.append((transformed[0].a, transformed[1].a))
    return result


def _operators(nodes: list[tuple[Fraction, Fraction]], e: Scalar, nu: Scalar,
               thickness: Scalar, shear: Scalar, epsilon: Scalar
               ) -> tuple[Matrix, Matrix]:
    core = _assemble_core(nodes, e, nu, thickness, shear)
    forms = _numerical_forms(nodes, thickness, shear, epsilon)
    t5, unused_qd = _selectors()
    del unused_qd
    physical = _multiply(_multiply(t5, core["K5"]), _transpose(t5))
    numerical = _multiply(_transpose(forms["L"]),
                          _multiply(forms["W"], forms["L"]))  # type: ignore[arg-type]
    return core["K5"], _add(physical, numerical)


def _congruence(operator: Matrix, transformed: Matrix, state_map: Matrix,
                factor: Scalar = _q(1)) -> bool:
    return _multiply(_transpose(state_map), _multiply(transformed, state_map)) \
        == _scale(operator, factor)


def _covariance_certificate(nodes: list[tuple[Fraction, Fraction]],
                            base_k5: Matrix, base_k24: Matrix,
                            e: Scalar, nu: Scalar, thickness: Scalar,
                            shear: Scalar, epsilon: Scalar
                            ) -> dict[str, object]:
    identity2 = [[_q(1), _q()], [_q(), _q(1)]]
    reflection = [[_q(1), _q()], [_q(), _q(-1)]]
    identity_permutation = list(range(4))
    d4_k5, d4_k24 = [], []
    for transform in _d4_maps():
        permutation = _d4_permutation(transform)
        natural_det = transform[0][0]*transform[1][1] - transform[0][1]*transform[1][0]
        frame = identity2 if natural_det > 0 else reflection
        transformed_nodes = _transform_nodes(nodes, permutation, frame)
        transformed_k5, transformed_k24 = _operators(
            transformed_nodes, e, nu, thickness, shear, epsilon
        )
        d4_k5.append(_congruence(
            base_k5, transformed_k5,
            _state_map(permutation, frame, external=20),
        ))
        d4_k24.append(_congruence(
            base_k24, transformed_k24,
            _state_map(permutation, frame, external=24),
        ))

    # Complete orientation reversal is an explicit, separately executed
    # numbering/director-frame operation rather than an alias for the D4 loop.
    reversal = [0, 3, 2, 1]
    reversed_nodes = _transform_nodes(nodes, reversal, reflection)
    reversed_k5, reversed_k24 = _operators(
        reversed_nodes, e, nu, thickness, shear, epsilon
    )
    reversal_k5 = _congruence(
        base_k5, reversed_k5, _state_map(reversal, reflection, external=20)
    )
    reversal_k24 = _congruence(
        base_k24, reversed_k24, _state_map(reversal, reflection, external=24)
    )

    rotation = [[_q(Fraction(3, 5)), _q(Fraction(-4, 5))],
                [_q(Fraction(4, 5)), _q(Fraction(3, 5))]]
    # The source-skew operators live in the common element frame.  A global
    # frame rotation therefore rotates the local/global embedding, not the
    # already-local x/y coordinates.  Verify both coordinate pullback and the
    # full embedded-operator congruence.
    rotated_global_nodes = _transform_nodes(nodes, identity_permutation, rotation)
    rotation_t = _transpose(rotation)
    pulled_back_nodes = _transform_nodes(
        rotated_global_nodes, identity_permutation, rotation_t
    )
    if pulled_back_nodes != nodes:
        raise PatchCovarianceError("common-frame coordinate pullback failed")
    frame_map20 = _state_map(identity_permutation, rotation, external=20)
    frame_map24 = _state_map(identity_permutation, rotation, external=24)
    rotated_k5 = _multiply(frame_map20, _multiply(base_k5, _transpose(frame_map20)))
    rotated_k24 = _multiply(frame_map24, _multiply(base_k24, _transpose(frame_map24)))
    frame_k5 = _congruence(
        base_k5, rotated_k5, frame_map20,
    )
    frame_k24 = _congruence(
        base_k24, rotated_k24, frame_map24,
    )

    shifted_nodes = _transform_nodes(
        nodes, identity_permutation, identity2,
        shift=(_q(Fraction(7, 3)), _q(Fraction(-5, 4))),
    )
    shifted_k5, shifted_k24 = _operators(
        shifted_nodes, e, nu, thickness, shear, epsilon
    )
    origin_k5 = shifted_k5 == base_k5
    origin_k24 = shifted_k24 == base_k24

    unit_results: dict[str, dict[str, bool]] = {}
    for scale in (_q(Fraction(1, 1000)), _q(1000)):
        scaled_nodes = _transform_nodes(
            nodes, identity_permutation, identity2, scale=scale
        )
        scaled_k5, scaled_k24 = _operators(
            scaled_nodes, e/(scale*scale), nu, thickness*scale,
            shear/(scale*scale), epsilon,
        )
        unit_results[scale.signature()] = {
            "K5": _congruence(
                base_k5, scaled_k5,
                _state_map(identity_permutation, identity2, external=20,
                           length_scale=scale),
                scale,
            ),
            "K24": _congruence(
                base_k24, scaled_k24,
                _state_map(identity_permutation, identity2, external=24,
                           length_scale=scale),
                scale,
            ),
        }

    return {
        "d4_count": 8,
        "d4_k5_count": sum(d4_k5),
        "d4_k24_count": sum(d4_k24),
        "d4_k5_congruence": all(d4_k5),
        "d4_k24_congruence": all(d4_k24),
        "frame_k5_congruence": frame_k5,
        "frame_k24_congruence": frame_k24,
        "orientation_reversal_k5_congruence": reversal_k5,
        "orientation_reversal_k24_congruence": reversal_k24,
        "origin_k5_invariant": origin_k5,
        "origin_k24_invariant": origin_k24,
        "unit_dimensional_congruence": unit_results,
        "unit_k5_dimensional_congruence": all(
            checks["K5"] for checks in unit_results.values()
        ),
        "unit_k24_dimensional_congruence": all(
            checks["K24"] for checks in unit_results.values()
        ),
        "unit_scales": ["1/1000", "1000"],
    }


def _support_certificate(support: dict[str, object]) -> dict[str, object]:
    expected = {
        "direct_drill_moments": "EXCLUDED",
        "hostile": {
            "nonzero_prescribed_drill": "EXCLUDED",
            "six_coordinate_clamp": "NON_GATING_HOSTILE_CONTROL",
        },
        "physical_loads": "RANGE_T5_ONLY",
        "primary_support": {
            "definition": "a_QD_equals_zero",
            "projectors": {"drill": "QD_QD_transpose", "physical": "T5_T5_transpose"},
        },
        "reaction_reporting": [
            "WG_PHYSICAL_RECOVERY", "PROJECTED_TOTAL_REACTION", "PROJECTED_PL_HG_REACTION",
        ],
        "schema": "anysolver.s4.e4-pl-q1a-support-contract-v1",
    }
    if support != expected:
        raise PlanAuthorityError("support/load/reaction contract changed")
    t5, qd = _selectors()
    physical = _multiply(t5, _transpose(t5))
    drill = _multiply(qd, _transpose(qd))
    identity = _identity(24)
    sample_physical = [identity[0]]
    forbidden_drill = [identity[5]]
    certificate = {
        "forbidden_direct_drill_is_pure_QD": (
            _multiply(forbidden_drill, drill) == forbidden_drill
            and not any(value for row in _multiply(forbidden_drill, physical) for value in row)
        ),
        "full_clamp_is_hostile_physical_plus_drill": _add(physical, drill) == identity,
        "physical_projector_idempotent": _multiply(physical, physical) == physical,
        "physical_support_annihilates_QD": (
            not any(value for row in _multiply(sample_physical, qd) for value in row)
            and _multiply(sample_physical, physical) == sample_physical
        ),
        "projectors_orthogonal": not any(
            value for row in _multiply(physical, drill) for value in row
        ),
    }
    if not all(certificate.values()):
        raise MaterialRecoveryError("support/load projector semantics failed")
    return certificate


def _validate_governance() -> dict[str, object]:
    baseline = _load_json(ROOT / "docs/reference_cases/e4_pl_q1a_baseline.json")
    expected_authority = {
        "branch": "codex/s4-e4-pl-planar-linear-qualification",
        "commit": "97c3150c9ecd41cf42fc108e9ff476497154428c",
        "tree": "9ea7e81a17c246e41b3fdfc236200d9dbf3e2b60",
    }
    if baseline.get("schema") != "anysolver.s4.e4-pl-q1a-baseline-v1" \
            or baseline.get("authority") != expected_authority:
        raise BaselineMismatch("baseline authority identity changed")
    accepted_inventory = baseline.get("e4", {}).get("test_inventory", {}) \
        if isinstance(baseline.get("e4"), dict) else {}
    if not isinstance(accepted_inventory, dict) \
            or {key: accepted_inventory.get(key) for key in (
                "canonical_lf_bytes", "canonical_lf_sha256", "count", "execution",
            )} != {
                "canonical_lf_bytes": 1795,
                "canonical_lf_sha256": "1C29534F6568AA2FF072F5D776E9D10BD71DE85F51C7562827FC6A3F0234E10F",
                "count": 20,
                "execution": "DETACHED_EXACT_AUTHORITY_WITH_WORKSPACE_BASETEMP",
            } or not str(accepted_inventory.get("result", "")).startswith("20_PASSED_IN_"):
        raise BaselineMismatch("detached accepted E4 test result changed")
    for record_name in ("conditional_plan", "review", "status"):
        record = baseline["e4"].get(record_name)  # type: ignore[index]
        if not isinstance(record, dict):
            raise BaselineMismatch(f"accepted E4 {record_name} identity missing")
        raw = (ROOT / str(record.get("path"))).read_bytes()
        if len(raw) != record.get("bytes") or _sha(raw) != record.get("sha256"):
            raise BaselineMismatch(f"accepted E4 {record_name} identity changed")

    environment = _load_json(ROOT / "docs/reference_cases/e4_pl_q1a_environment.json")
    runtime = environment.get("oracle_runtime")
    if environment.get("schema") != "anysolver.s4.e4-pl-q1a-environment-v1" \
            or environment.get("canonical_json") != {
                "allow_nan": False, "duplicate_keys": False, "encoding": "utf-8",
                "ensure_ascii": False, "key_order": "unicode_codepoint_sorted",
                "newline": "lf", "separators": [",", ":"], "terminal_lf": True,
            } or not isinstance(runtime, dict) or runtime != {
                "dependencies": "python_standard_library_only",
                "fresh_process_runs": 2,
                "python_executable": PINNED_PYTHON,
                "python_version": PINNED_PYTHON_VERSION,
                "thread_environment": {
                    "OMP_NUM_THREADS": "1", "OMP_STACKSIZE": "1G",
                    "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0",
                },
            }:
        raise PlanAuthorityError("canonical environment contract changed")
    actual_executable = str(Path(sys.executable)).replace("\\", "/").casefold()
    if actual_executable != PINNED_PYTHON.casefold() \
            or ".".join(str(value) for value in sys.version_info[:3]) != PINNED_PYTHON_VERSION:
        raise PlanAuthorityError("oracle is not running in the pinned Python transport")

    tolerances = _load_json(ROOT / "docs/reference_cases/e4_pl_q1a_tolerances.json")
    if tolerances != {
        "classification": {
            "covariance": "EXACT", "local_rank": "EXACT_ONLY",
            "non_affine_gauss": "EXACT_QUADRATIC_SURD_OR_OUTWARD_RATIONAL",
            "schur_identity": "EXACT", "surd_interval_max_depth": 12,
            "surd_interval_max_subdivisions": 4096,
            "uncovered_budget_terminal": "UNCLASSIFIED_E4_PL_Q1A_PLANAR_IDENTITY_AND_LOCAL_ALGEBRA",
        },
        "corroboration": {
            "dimensionless_residual_atol": "1e-11", "floating_svd_classifies": False,
            "precision_bits": [80, 160],
        },
        "schema": "anysolver.s4.e4-pl-q1a-tolerances-v1",
    }:
        raise PlanAuthorityError("classification/tolerance contract changed")

    terminals = _load_json(ROOT / "docs/reference_cases/e4_pl_q1a_terminal_table.json")
    expected_terminals = [terminal for unused, terminal in TERMINALS_BY_EXCEPTION[:-1]] + [PASS_TERMINAL]
    if terminals != {
        "ordered": expected_terminals,
        "production": RELEASE_TERMINAL,
        "schema": "anysolver.s4.e4-pl-q1a-terminal-table-v1",
        "success_authority": "Q1B_PLAN_ONLY",
    }:
        raise PlanAuthorityError("terminal precedence table changed")

    extent = _load_json(ROOT / "docs/reference_cases/e4_pl_q1a_allowed_extent.json")
    required_new = {
        "docs/reference_cases/e4_pl_q1a_oracle.py",
        "docs/reference_cases/e4_pl_q1a_reference.py",
        "tests/test_e4_pl_q1a_authority.py",
        "tests/test_e4_pl_q1a_exact.py",
    }
    if extent.get("schema") != "anysolver.s4.e4-pl-q1a-allowed-extent-v1" \
            or extent.get("authority") != {key: expected_authority[key] for key in ("commit", "tree")} \
            or extent.get("modified_paths") != [] or extent.get("production_paths") != [] \
            or not isinstance(extent.get("new_paths"), list) \
            or len(extent["new_paths"]) != 27 \
            or extent["new_paths"] != sorted(set(extent["new_paths"])) \
            or not required_new.issubset(set(extent["new_paths"])) \
            or extent.get("conditional_paths") != {
                "docs/agent_plans/S4_E4_PL_Q1B_NONINTRUSION_STABILITY_LOCKING_PLAN.md":
                "ONLY_IF_PROVISIONAL_GO_E4_PL_Q1B_NONINTRUSION_STABILITY_LOCKING_PLAN"
            }:
        raise PlanAuthorityError("allowed-path extent changed")

    inventory = _load_json(ROOT / "docs/reference_cases/e4_pl_q1a_test_inventory.json")
    q1a = inventory.get("q1a")
    expected_nodes = [
        "tests/test_e4_pl_q1a_authority.py::test_e4_pl_q1a_exact_main_authority_and_immutable_e4_packet",
        "tests/test_e4_pl_q1a_authority.py::test_e4_pl_q1a_test_inventory_and_historical_roots_are_frozen",
        "tests/test_e4_pl_q1a_authority.py::test_e4_pl_q1a_material_and_production_boundaries",
        "tests/test_e4_pl_q1a_authority.py::test_e4_pl_q1a_source_gate_is_unique_closed_and_copyright_clean",
        "tests/test_e4_pl_q1a_exact.py::test_e4_pl_q1a_exact_affine_reproduction_and_actual_38_field_algebra",
        "tests/test_e4_pl_q1a_exact.py::test_e4_pl_q1a_exact_covariance_recovery_and_material_boundary",
        "tests/test_e4_pl_q1a_exact.py::test_e4_pl_q1a_oracle_is_stdlib_independent_strict_and_deterministic",
        "tests/test_e4_pl_q1a_exact.py::test_e4_pl_q1a_caller_bound_contract_and_output_are_exact",
    ]
    if inventory.get("schema") != "anysolver.s4.e4-pl-q1a-test-inventory-v1" \
            or not isinstance(q1a, dict) or q1a.get("count_before_closeout") != 8 \
            or not q1a.get("live_successor_only") \
            or q1a.get("node_ids_before_closeout") != expected_nodes:
        raise PlanAuthorityError("successor test inventory changed")

    support = _load_json(ROOT / "docs/reference_cases/e4_pl_q1a_support_contract.json")
    return _support_certificate(support)


def _validate_packet() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    cases = _load_json(CASES_PATH)
    geometry = _load_json(ROOT / "docs/reference_cases/e4_pl_q1a_geometry_contract.json")
    material = _load_json(ROOT / "docs/reference_cases/e4_pl_q1a_material_contract.json")
    source_map = _load_json(ROOT / "docs/reference_cases/e4_pl_q1a_source_map.json")
    if cases.get("schema") != "anysolver.s4.e4-pl-q1a-cases-v1" \
            or cases.get("candidate_id") != STUDY_ID:
        raise SourceIdentityError("Q1A case identity mismatch")
    if geometry.get("schema") != "anysolver.s4.e4-pl-q1a-geometry-contract-v1":
        raise SourceIdentityError("Q1A geometry contract mismatch")
    if material.get("schema") != "anysolver.s4.e4-pl-q1a-material-contract-v1":
        raise MaterialRecoveryError("Q1A material contract mismatch")
    if source_map.get("schema") != "anysolver.s4.e4-pl-q1a-source-map-v1" \
            or source_map.get("candidate_id") != STUDY_ID \
            or source_map.get("source_gate") != "CLOSED_UNIQUE_NON_AFFINE_PLANAR_IDENTITY":
        raise SourceIdentityError("Q1A source/formulation identity is not closed")
    statements = source_map.get("indispensable_statements")
    if not isinstance(statements, list) or len(statements) != 11 \
            or any(not isinstance(row, dict) or row.get("status") != "CLOSED"
                   for row in statements[:-1]) \
            or not isinstance(statements[-1], dict) \
            or statements[-1].get("id") != "covariance_patch_recovery_separation" \
            or statements[-1].get("status") != "DISPROVED_D4_AND_REVERSAL" \
            or source_map.get("qualification_terminal") != (
                "NO_GO_E4_PL_Q1A_PATCH_OR_COVARIANCE"
            ):
        raise SourceIdentityError("Q1A indispensable source statement is not reproducible")
    case_geometries_raw = cases.get("geometries")
    contract_geometries = geometry.get("cases")
    if not isinstance(case_geometries_raw, list) or not isinstance(contract_geometries, dict):
        raise SourceIdentityError("Q1A geometry registry missing")
    case_geometries = {
        str(record.get("id")): record for record in case_geometries_raw if isinstance(record, dict)
    }
    for name in ("unit_square", "affine_skew", "trapezoid", "tapered_skew"):
        if name not in case_geometries or name not in contract_geometries:
            raise SourceIdentityError(f"missing Q1A geometry: {name}")
        case_record = case_geometries[name]
        contract_record = contract_geometries[name]
        if not isinstance(case_record, dict) or not isinstance(contract_record, dict):
            raise SourceIdentityError(f"malformed Q1A geometry: {name}")
        if _case_nodes(case_record.get("coordinates")) != _case_nodes(contract_record.get("coordinates")):
            raise SourceIdentityError(f"case/geometry disagreement: {name}")
    formulation = cases.get("formulation")
    if not isinstance(formulation, dict) or formulation.get("core") != {
        "external_coordinates": 24,
        "independent_strain_parameters": 21,
        "k": 0,
        "local_parameters": 35,
        "mitc_shear": "WG2004_EQ_19_21",
        "n": 7,
        "quadrature": "UNSHIFTED_POSITIVE_2X2",
        "stress_parameters": 14,
        "transform": "WG2020_CENTRE_J_EQ_7_18",
    } or formulation.get("pl", {}).get("basis") != ["1", "r", "s"] \
            or formulation.get("hourglass", {}).get("epsilon") != "1/1000":
        raise SourceIdentityError("Q1A frozen mechanics changed")
    return cases, geometry, material


def _material_certificate(material: dict[str, object]) -> dict[str, object]:
    fixture_record = material.get("fixture")
    if not isinstance(fixture_record, dict):
        raise MaterialRecoveryError("DNV material fixture record missing")
    fixture_path = ROOT / str(fixture_record.get("path"))
    raw = fixture_path.read_bytes()
    if len(raw) != fixture_record.get("bytes") or _sha(raw) != fixture_record.get("sha256"):
        raise MaterialRecoveryError("DNV material fixture identity mismatch")
    fixture = _load_json(fixture_path)
    rp = fixture.get("rp_c208")
    compatibility = material.get("compatibility")
    if not isinstance(rp, dict) or not isinstance(compatibility, dict):
        raise MaterialRecoveryError("DNV material contract incomplete")
    expected_grades = ["S235", "S275", "S355", "S420", "S460"]
    if rp.get("grades") != expected_grades or rp.get("row_count") != 17:
        raise MaterialRecoveryError("DNV material row registry changed")
    if compatibility != {
        "density_required_metadata_but_unused": True,
        "dnv_approval": False,
        "new_public_fields": [],
        "reporting": "compatible_with_DNV_analysis_workflows",
        "ru_ship_project_edition": "July_2025",
        "ru_ship_records_in_anymaterial": False,
    }:
        raise MaterialRecoveryError("DNV compatibility claim changed")
    inherited_record = material.get("inherited_detail")
    if not isinstance(inherited_record, dict):
        raise MaterialRecoveryError("inherited 17-row fixture identity missing")
    inherited_path = ROOT / str(inherited_record.get("path"))
    inherited_raw = inherited_path.read_bytes()
    if len(inherited_raw) != 2135 or _sha(inherited_raw) != (
        "A16024C81522FB783841CC790C11772A10C8D0D936F9E678BE1CA981FD3DD016"
    ) or len(inherited_raw) != inherited_record.get("bytes") \
            or _sha(inherited_raw) != inherited_record.get("sha256"):
        raise MaterialRecoveryError("inherited 2135-byte fixture changed")
    inherited = _load_json(inherited_path)
    exact_ranges = {
        "S235": [[0, 16], [16, 40], [40, 63], [63, 100]],
        "S275": [[0, 16], [16, 40], [40, 63]],
        "S355": [[0, 16], [16, 40], [40, 63], [63, 100]],
        "S420": [[0, 16], [16, 40], [40, 63]],
        "S460": [[0, 16], [16, 40], [40, 63]],
    }
    dataset = inherited.get("rp_c208_dataset")
    if not isinstance(dataset, dict) or dataset.get("grades") != exact_ranges \
            or dataset.get("row_count") != 17:
        raise MaterialRecoveryError("inherited 17 exact RP-C208 ranges changed")
    return {
        "density_required_metadata_but_unused": True,
        "dnv_approval": False,
        "grades": expected_grades,
        "new_public_fields": [],
        "reporting": "compatible with DNV analysis workflows",
        "row_count": 17,
        "row_ranges": exact_ranges,
        "rp_c208_edition": "September_2019_amended_October_2022",
        "ru_ship_project_edition": "July_2025",
    }


def _affine_reproduction() -> dict[str, object]:
    e, nu, thickness, shear = _q(Fraction(5, 2)), _q(Fraction(1, 4)), _q(1), _q(1)
    normalized = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    core = _assemble_core(normalized, e, nu, thickness, shear)
    expected = _load_json(ROOT / "docs/reference_cases/e4_core_cases.json")[
        "source_exact_operator"
    ]["square_matrix_signatures"]
    if not isinstance(expected, dict):
        raise EvidenceError("accepted E4 core signatures missing")
    observed = {name: _matrix_digest(core[name]) for name in ("D", "F", "Gq", "H", "K5", "S")}
    if any(observed[name] != expected.get(name) for name in observed):
        raise EvidenceError("affine E4 core reproduction mismatch")

    accepted_pl = _load_json(ROOT / "docs/reference_cases/e4_pl_cases.json")
    unit_record = next(record for record in accepted_pl["affine_cases"]
                       if record["id"] == "unit_square")
    expected_c = [[_q(Fraction(value)) for value in row]
                  for row in unit_record["expected_c_rows_unit_square"]]
    unit_c = _center_constraint([(0, 0), (1, 0), (1, 1), (0, 1)])
    if unit_c != expected_c:
        raise EvidenceError("affine E4 drill rows not reproduced")
    return {"accepted_core_matrix_signatures": observed,
            "accepted_drill_rows_exact": True,
            "accepted_terminal": "PROVISIONAL_GO_E4_PL_LINEAR_QUALIFICATION_PLAN"}


def build_certificate() -> dict[str, object]:
    support_certificate = _validate_governance()
    cases, unused_geometry, material = _validate_packet()
    del unused_geometry
    e, nu, thickness = _q(Fraction(5, 2)), _q(Fraction(1, 4)), _q(1)
    shear = e / (2 * (_q(1) + nu))
    epsilon = _q(Fraction(1, 1000))
    if shear != _q(1):
        raise SourceIdentityError("registered isotropic shear identity changed")
    registered_material = cases.get("material")
    if not isinstance(registered_material, dict) or {
        key: registered_material.get(key) for key in ("E", "G", "epsilon_hg", "nu", "scope", "t")
    } != {
        "E": "5/2", "G": "1", "epsilon_hg": "1/1000", "nu": "1/4",
        "scope": "HOMOGENEOUS_ISOTROPIC_LINEAR", "t": "1",
    }:
        raise SourceIdentityError("registered exact material probe changed")
    expected_constitutive = [[_q(Fraction(value)) for value in row]
                             for row in registered_material.get("resultant_matrix", [])]
    if expected_constitutive != _constitutive(e, nu, thickness, shear):
        raise MaterialRecoveryError("registered isotropic resultant matrix mismatch")
    t5, qd = _selectors()
    if (_multiply(_transpose(t5), t5) != _identity(20)
            or _multiply(_transpose(qd), qd) != _identity(4)
            or any(value for row in _multiply(_transpose(t5), qd) for value in row)):
        raise LocalAlgebraError("physical/drill coordinate split failed")

    geometry_results: dict[str, object] = {}
    covariance_failures: list[dict[str, object]] = []
    patch_failures: list[dict[str, object]] = []
    for record in cases["geometries"]:
        if not isinstance(record, dict):
            raise SourceIdentityError("malformed geometry record")
        name = str(record.get("id"))
        nodes = _case_nodes(record.get("coordinates"))
        core = _assemble_core(nodes, e, nu, thickness, shear)
        forms = _numerical_forms(nodes, thickness, shear, epsilon)
        c = forms["C"]
        mass = forms["M"]
        b = forms["B"]
        hrow = forms["Hrow"]
        l_map = forms["L"]
        weight = forms["W"]
        if not all(isinstance(value, list) for value in (c, mass, b, l_map, weight)) \
                or not isinstance(hrow, list):
            raise LocalAlgebraError("malformed numerical operator")
        if b != _multiply(mass, c):
            raise LocalAlgebraError("B=M*C identity failed")
        core_ranks = {key: _rank(core[key]) for key in ("D", "F", "Gq", "H", "K5")}
        if core_ranks != {"D": 35, "F": 14, "Gq": 14, "H": 21, "K5": 14}:
            raise LocalAlgebraError(f"WG core rank failure: {name}")
        if any(pivot.sign() <= 0 for pivot in _ldl_pivots(core["S"])):
            raise LocalAlgebraError(f"WG core material form is not positive: {name}")

        a_map = _multiply(l_map, t5)
        r_map = _multiply(l_map, qd)
        if _rank(c) != 3 or _rank([hrow]) != 1 or _rank(l_map) != 4 or _rank(r_map) != 4:
            raise LocalAlgebraError(f"four-mode drill completion failed: {name}")
        kdd = _multiply(_transpose(r_map), _multiply(weight, r_map))
        if any(pivot.sign() <= 0 for pivot in _ldl_pivots(kdd)):
            raise LocalAlgebraError(f"drill Kdd is not SPD: {name}")
        kpp = _add(core["K5"], _multiply(_transpose(a_map), _multiply(weight, a_map)))
        kpd = _multiply(_transpose(a_map), _multiply(weight, r_map))
        schur = _add(kpp, _multiply(_multiply(kpd, _inverse(kdd)), _transpose(kpd)), -_q(1))
        if schur != core["K5"]:
            raise LocalAlgebraError(f"local physical Schur non-intrusion failed: {name}")

        q20 = core["Q20"]
        q24 = _multiply(t5, q20)
        k0 = _multiply(_multiply(t5, core["K5"]), _transpose(t5))
        k_num = _multiply(_transpose(l_map), _multiply(weight, l_map))
        k_total = _add(k0, k_num)
        if k_total != _add(_add(k0, forms["K_pl"]), forms["K_hg"]):
            raise LocalAlgebraError(f"numerical Hessian decomposition failed: {name}")
        if _rank(k_total) != 18 or k_total != _transpose(k_total):
            raise LocalAlgebraError(f"rank/symmetry screen failed: {name}")

        rigid = _rigid_vectors(nodes)
        rigid_images = {key: _matvec(k_total, value) for key, value in rigid.items()}
        if _rank(list(rigid.values())) != 6 or any(any(image) for image in rigid_images.values()):
            raise LocalAlgebraError(f"six-rigid-mode screen failed: {name}")
        patches = _patch_vectors(nodes)
        patch_actions = {key: _matvec(l_map, value) for key, value in patches.items()}
        if any(any(action) for action in patch_actions.values()):
            raise PatchCovarianceError(f"patch numerical non-intrusion failed: {name}")

        # Actual 35+3 stationary block and one deterministic algebraic probe.
        internal = _zeros(38, 38)
        for row in range(35):
            for column in range(35):
                internal[row][column] = core["D"][row][column]
        for row in range(3):
            for column in range(3):
                internal[35+row][35+column] = -mass[row][column] / shear
        if _rank(internal) != 38:
            raise LocalAlgebraError(f"38-field internal block singular: {name}")
        probe = [_q(index - 11) for index in range(24)]
        z = _matvec(core["D_inverse"], _matvec(_transpose(q24), probe))
        z = [-value for value in z]
        tau = _matvec(_inverse(mass), _matvec(b, probe))
        tau = [shear * value for value in tau]
        core_stationarity = _add_vectors(_matvec(_transpose(q24), probe),
                                         _matvec(core["D"], z))
        tau_stationarity = _add_vectors(_matvec(b, probe),
                                        _matvec(mass, tau), -_q(1)/shear)
        mixed_residual = _add_vectors(
            _add_vectors(_matvec(forms["K_hg"], probe), _matvec(q24, z)),
            _matvec(_transpose(b), tau),
        )
        condensed_residual = _matvec(k_total, probe)
        mixed_energy = (_dot(z, _matvec(core["D"], z))/2
                        + _dot(probe, _matvec(q24, z))
                        + _dot(tau, _matvec(b, probe))
                        - _dot(tau, _matvec(mass, tau))/(2*shear)
                        + _energy(forms["K_hg"], probe))
        if (any(core_stationarity) or any(tau_stationarity)
                or mixed_residual != condensed_residual
                or mixed_energy != _energy(k_total, probe)):
            raise LocalAlgebraError(f"mixed/condensed parity failed: {name}")

        common = [_q() for _ in range(24)]
        alternating = [_q() for _ in range(24)]
        for node in range(4):
            common[6*node+5] = _q(1)
            alternating[6*node+5] = _q(1 if node % 2 == 0 else -1)
        spin = _rigid_vectors(nodes)["rotation_z"][:]
        for node in range(4):
            spin[6*node+5] = _q()
        modes = {
            "pure_common_drill": _matvec(l_map, common),
            "translation_only_spin": _matvec(l_map, spin),
            "matched_rigid_spin": _matvec(l_map, rigid["rotation_z"]),
            "alternating_drill": _matvec(l_map, alternating),
        }
        if (not any(modes["pure_common_drill"]) or not any(modes["translation_only_spin"])
                or any(modes["matched_rigid_spin"])
                or any(modes["alternating_drill"][:3])
                or not modes["alternating_drill"][3]):
            raise LocalAlgebraError(f"registered drill-mode action failed: {name}")

        physical_patches = _physical_patch_certificate(
            nodes, core, forms, e, nu, thickness, shear
        )
        if not all(all(checks.values()) for checks in physical_patches.values()):
            patch_failures.append({
                "failed": {
                    patch: [check for check, passed in checks.items() if not passed]
                    for patch, checks in physical_patches.items() if not all(checks.values())
                },
                "geometry": name,
            })
        full_covariance = _covariance_certificate(
            nodes, core["K5"], k_total, e, nu, thickness, shear, epsilon
        )
        covariance_values: list[bool] = []
        for key, value in full_covariance.items():
            if key in ("d4_count", "unit_scales"):
                continue
            if key == "unit_dimensional_congruence":
                covariance_values.extend(
                    check for scale_checks in value.values() for check in scale_checks.values()
                )
            else:
                covariance_values.append(bool(value))
        if not all(covariance_values):
            covariance_failures.append({
                "d4_k24_count": full_covariance["d4_k24_count"],
                "d4_k5_count": full_covariance["d4_k5_count"],
                "geometry": name,
                "orientation_reversal_k24_congruence": full_covariance[
                    "orientation_reversal_k24_congruence"
                ],
                "orientation_reversal_k5_congruence": full_covariance[
                    "orientation_reversal_k5_congruence"
                ],
            })
        covariance = {
            "d4": full_covariance["d4_k5_congruence"]
                  and full_covariance["d4_k24_congruence"],
            "d4_count": 8,
            "frame": full_covariance["frame_k5_congruence"]
                     and full_covariance["frame_k24_congruence"],
            "orientation_reversal": full_covariance["orientation_reversal_k5_congruence"]
                                    and full_covariance["orientation_reversal_k24_congruence"],
            "origin": full_covariance["origin_k5_invariant"]
                      and full_covariance["origin_k24_invariant"],
            "units": all(
                check for scale_checks in full_covariance["unit_dimensional_congruence"].values()
                for check in scale_checks.values()
            ),
        }
        geometry_results[str(name)] = {
            "arithmetic": "Q(sqrt(3))",
            "core_ranks": core_ranks,
            "covariance": covariance,
            "full_covariance": full_covariance,
            "internal_block_rank": _rank(internal),
            "kdd_ldl_positive": True,
            "local_physical_schur_equals_k5": True,
            "mixed_condensed": {
                "energy": True, "residual": True, "stationarity": True,
                "symmetric_tangent": True, "virtual_work": True,
            },
            "mode_actions": {key: [entry.signature() for entry in value]
                             for key, value in modes.items()},
            "patch_numerical_actions_zero": {key: not any(value)
                                              for key, value in patch_actions.items()},
            "physical_patches": physical_patches,
            "rank": 18,
            "nullity": 6,
            "residual_drill_row": [hrow[6*node+5].signature() for node in range(4)],
            "rigid_images_zero": {key: not any(value) for key, value in rigid_images.items()},
            "r_map_rank": 4,
        }

    scientific_terminal = (
        "NO_GO_E4_PL_Q1A_PATCH_OR_COVARIANCE"
        if covariance_failures or patch_failures else PASS_TERMINAL
    )
    return {
        "affine_reproduction": _affine_reproduction(),
        "candidate_id": STUDY_ID,
        "coordinate_split": {
            "QD_T_QD_I4": True, "T5_T_QD_zero": True, "T5_T_T5_I20": True,
        },
        "component_ledger": {
            "dnv_material_recovery_contract": "GO_E4_PL_Q1A_DNV_MATERIAL_RECOVERY",
            "local_algebra": "GO_E4_PL_Q1A_LOCAL_ALGEBRA",
            "patch_fields": (
                "NO_GO_E4_PL_Q1A_PATCH_OR_COVARIANCE"
                if patch_failures else "GO_E4_PL_Q1A_PHYSICAL_PATCHES"
            ),
            "source_planar_identity": "GO_E4_PL_Q1A_SOURCE_PLANAR_IDENTITY",
            "full_covariance": (
                "NO_GO_E4_PL_Q1A_PATCH_OR_COVARIANCE"
                if covariance_failures else "GO_E4_PL_Q1A_FULL_COVARIANCE"
            ),
        },
        "covariance_failures": covariance_failures,
        "geometry_results": geometry_results,
        "material_compatibility": _material_certificate(material),
        "patch_failures": patch_failures,
        "recovery": {
            "physical_resultants_from": "WG_STATIONARY_FIELDS_ONLY",
            "projected_numerical_reaction_reported_separately": True,
            "pl_hourglass_in_physical_N_M_Q": False,
        },
        "support_and_load_contract": support_certificate,
        "release_terminal": RELEASE_TERMINAL,
        "terminal": scientific_terminal,
    }


def _add_vectors(first: Vector, second: Vector, second_scale: Scalar = _q(1),
                 third: Vector | None = None) -> Vector:
    if len(first) != len(second) or third is not None and len(first) != len(third):
        raise EvidenceError("vector sum dimension mismatch")
    result = [a + second_scale*b for a, b in zip(first, second)]
    if third is not None:
        result = [a + b for a, b in zip(result, third)]
    return result


def build_contract() -> dict[str, object]:
    certificate = build_certificate()
    identities: dict[str, object] = {}
    for relative in CONTRACT_INPUTS:
        raw = (ROOT / relative).read_bytes()
        identities[relative] = {"bytes": len(raw), "path": relative, "sha256": _sha(raw)}
    oracle_path = Path(__file__).relative_to(ROOT).as_posix()
    oracle_raw = Path(__file__).read_bytes()
    identities[oracle_path] = {
        "bytes": len(oracle_raw), "path": oracle_path, "sha256": _sha(oracle_raw),
    }
    return {
        "candidate_id": STUDY_ID,
        "input_identities": identities,
        "production_paths": [],
        "proof_program": [
            "AFFINE_E4_0_BYTE_IDENTITY",
            "Q_SQRT3_POSITIVE_2X2_ASSEMBLY",
            "ACTUAL_WG_35_PLUS_PL_3_STATIONARY_BLOCK",
            "CENTER_TAYLOR_C_AND_WT_GEOMETRY_GAMMA",
            "R_INVERTIBLE_KDD_SPD_PHYSICAL_SCHUR_EQUALS_K5",
            "RANK18_EXACTLY_SIX_RIGID",
            "PATCH_COVARIANCE_RECOVERY_SEPARATION",
            "DNV_WORKFLOW_MATERIAL_CONTRACT_17_ROWS",
        ],
        "schema": "anysolver.s4.e4-pl-q1a-contract-v1",
        "scientific_terminal": certificate["terminal"],
    }


def build_output(contract_sha256: str) -> dict[str, object]:
    certificate = build_certificate()
    terminal = str(certificate["terminal"])
    return {
        "candidate_id": STUDY_ID,
        "certificate": certificate,
        "contract_sha256": contract_sha256,
        "overall_release_terminal": RELEASE_TERMINAL,
        "production_changed": False,
        "schema": "anysolver.s4.e4-pl-q1a-output-v1",
        "status": "no_go" if terminal.startswith("NO_GO_") else "provisional_go_q1b_plan_only",
        "terminal": terminal,
    }


def _load_contract(path: Path, caller_sha256: str) -> str:
    try:
        if path.resolve(strict=True) != CONTRACT_PATH.resolve(strict=True):
            raise ContractError("contract path mismatch")
        raw = path.read_bytes()
        if _sha(raw) != caller_sha256:
            raise ContractError("contract raw hash mismatch")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                           parse_constant=lambda token: (_ for _ in ()).throw(ContractError(token)))
        if not isinstance(value, dict) or raw != _canonical(value):
            raise ContractError("contract is not canonical")
        if value != build_contract():
            raise ContractError("contract semantic mismatch")
    except ContractError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, EvidenceError) as exc:
        raise ContractError(str(exc)) from exc
    return caller_sha256


def _terminal_for(exception: BaseException) -> str:
    for exception_type, terminal in TERMINALS_BY_EXCEPTION:
        if isinstance(exception, exception_type):
            return terminal
    return "BLOCKED_E4_PL_Q1A_ORACLE_OR_REVIEW"


def _classified_failure(exception: BaseException) -> bytes:
    terminal = _terminal_for(exception)
    if terminal.startswith("NO_GO_"):
        status = "no_go"
    elif terminal.startswith("UNCLASSIFIED_"):
        status = "unclassified"
    else:
        status = "blocked"
    return _canonical({"detail": str(exception), "status": status, "terminal": terminal})


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
    except (EvidenceError, ContractError) as exc:
        sys.stdout.buffer.write(_classified_failure(exc))
        return 2
    except (OSError, AssertionError, ValueError, ZeroDivisionError) as exc:
        wrapped = OracleReviewError(f"{type(exc).__name__}: {exc}")
        sys.stdout.buffer.write(_classified_failure(wrapped))
        return 2
    except Exception as exc:
        wrapped = OracleReviewError(f"{type(exc).__name__}: {exc}")
        sys.stdout.buffer.write(_classified_failure(wrapped))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
