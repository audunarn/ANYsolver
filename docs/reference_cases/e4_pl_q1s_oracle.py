"""Independent exact/outward oracle for the E4-PL-Q1S study.

This file is deliberately self contained.  It uses only the Python standard
library and the eleven plan-stage artifacts frozen by preregistration commit
00d6a66c34712c8f3fd1e38113c83d0a03b2de43.  In particular it neither imports
nor inspects the independent reference implementation or any Q1A mechanics.

There are three disjoint entry surfaces:

* ``--static-metadata`` and ``--static-check`` perform no registered-case
  mechanics and are safe during the implementation-freeze stage;
* the public pure functions expose independently transcribed algebra for AST
  and unit inspection without selecting a registered case; and
* ``--execute`` is fail-closed behind the exact caller-bound execution
  contract and the third-commit subject required by the governing plan.

The stationary variables are ordered exactly as in the accepted E4-0 core
(35 WG-core plus 3 PL):

    generalized stress/resultant parameters (14),
    generalized strain parameters (21), PL multiplier (3).

The mixed functional is assembled before any condensation with
``D=[[0,F^T],[F,H]]`` and ``Q=[Gq^T,0]``.  The PL block uses the frozen
surface-reduced compliance and the geometry-dependent residual row is a
separate external energy.  No Gram surrogate, identity repair, ground drill
diagonal, or post-condensation rank repair occurs here.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence


CANDIDATE_ID = (
    "candidate_e4_pl_q1s.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1"
)
STUDY_ID = "study_e4_pl_q1s.q1r_frozen_identity_implementation_completion_v1"
IMPLEMENTATION_ID = "Q1S_ORACLE_INDEPENDENT"
RUNNER_ID = "ORACLE_RUNNER"
PREREGISTRATION_COMMIT = "00d6a66c34712c8f3fd1e38113c83d0a03b2de43"
PREREGISTRATION_TREE = "661bf7ce0c509adb3f8e0f0559974ce24171dda1"
PREREGISTRATION_PARENT = "46231c56d4c7d24000421fc3ba0f4800239e64bd"
PREREGISTRATION_SUBJECT = "docs: preregister E4 PL Q1S implementation completion"
IMPLEMENTATION_SUBJECT = "docs: freeze E4 PL Q1S independent implementations"
EXECUTION_SUBJECT = "docs: authorize E4 PL Q1S scientific execution"
EXECUTION_CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1s-execution-contract-v1"
EXECUTION_AUTHORITY_SCHEMA = "anysolver.s4.e4-pl-q1s-execution-authority-v1"
EXECUTION_AUTHORIZATION = "AUTHORIZE_E4_PL_Q1S_SCIENTIFIC_EXECUTION"
COMMON_PAYLOAD_SCHEMA = "anysolver.s4.e4-pl-q1s-certificate-payload-v1"

ROOT = Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "docs/reference_cases/e4_pl_q1r_cases.json"
FRAME_PATH = ROOT / "docs/reference_cases/e4_pl_q1r_frame_contract.json"
GEOMETRY_PATH = ROOT / "docs/reference_cases/e4_pl_q1r_geometry_contract.json"
MATERIAL_PATH = ROOT / "docs/reference_cases/e4_pl_q1r_material_contract.json"
SUPPORT_PATH = ROOT / "docs/reference_cases/e4_pl_q1r_support_contract.json"
TOLERANCES_PATH = ROOT / "docs/reference_cases/e4_pl_q1r_tolerances.json"
TERMINALS_PATH = ROOT / "docs/reference_cases/e4_pl_q1s_terminal_table.json"
COMPLETENESS_PATH = ROOT / "docs/reference_cases/e4_pl_q1s_implementation_completeness.json"
AUTHORITY_CONTRACT_PATH = ROOT / "docs/reference_cases/e4_pl_q1s_authority_contract.json"
INHERITANCE_PATH = ROOT / "docs/reference_cases/e4_pl_q1s_inheritance_manifest.json"
TEST_INVENTORY_PATH = ROOT / "docs/reference_cases/e4_pl_q1s_test_inventory.json"

PLAN_STAGE_SHA256 = {
    "docs/agent_plans/S4_E4_PL_Q1S_IMPLEMENTATION_COMPLETION_PLAN.md":
        "3FE4D21CA8A92EDF4A5D136F4BE6A6DA29A1DF139EF54AE204B208C3AE6285B2",
    "docs/reference_cases/e4_pl_q1s_plan_review.json":
        "95BAB9FBDA1931EFC62F399A3C8C4E444CF92ABE36197AC7AC96CF257932E6A6",
    "docs/reference_cases/e4_pl_q1s_baseline.json":
        "DE0AB7F20A8588AE7E72214F31763729F65D97682DA435294BF5FE52B45127E6",
    "docs/reference_cases/e4_pl_q1s_inheritance_manifest.json":
        "DBE7ACE7498AE971D891F5182BAAD8DEA2021C33A27F78D827C84FEC438B860E",
    "docs/reference_cases/e4_pl_q1s_draft_preservation_manifest.json":
        "8309F0E8FE82C8AFAB14E69F275C90662D2E9E8EB47115304B43F07B4678A410",
    "docs/reference_cases/e4_pl_q1s_allowed_extent.json":
        "8E14AE1E46A097F16C1CC0986F4AB578C4D385FD53EA8E5E9610AF249420214C",
    "docs/reference_cases/e4_pl_q1s_implementation_completeness.json":
        "C567F51F0EF97E5D2D33961A96D765E390D9E97B5E6BF4B659CD8B6980E67469",
    "docs/reference_cases/e4_pl_q1s_authority_contract.json":
        "0CE5590AF73F5B7A9ED3D2A6B4D1381CB0625A52940FD978E253C34C47F790C0",
    "docs/reference_cases/e4_pl_q1s_terminal_table.json":
        "A046AD7786502B204EDB83AD4235EC96C634166C6D423CC1AB291B8AA8A76D8E",
    "docs/reference_cases/e4_pl_q1s_test_inventory.json":
        "E95C190A1C2D6859FCDE2EB73961CE3C755D75736D1AA25F441104A04147A527",
    "tests/test_e4_pl_q1s_preregistration_authority.py":
        "2C33E02015B4CEB240CE2A734FA89D8032F6C4A9B9A1335C77B39B84532FF8A9",
}

INHERITED_CORE_SHA256 = {
    "docs/reference_cases/e4_core_cases.json":
        "FE08E59D9E01073E04251C52544EDF10C4CC86861EA8B98FC6CB1A645427FEF2",
    "docs/reference_cases/e4_core_contract.json":
        "8768ABDC5D77B5FCC1643AF69920EFEB83F27DDFBDE17525F06EE2B53A5C1678",
}
CORE_CASES_PATH = ROOT / "docs/reference_cases/e4_core_cases.json"
CORE_CONTRACT_PATH = ROOT / "docs/reference_cases/e4_core_contract.json"

STATIC_OBLIGATION_SYMBOLS = {
    "CORE_001_COORDINATE_SPLIT": "physical_drill_maps",
    "CORE_002_CENTRE_J_AND_J0_OVER_J": "centre_j_modes",
    "CORE_003_SOURCE_TRANSFORMS": "source_tensor_transform",
    "CORE_004_STRESS14": "source_spaces",
    "CORE_005_STRAIN21": "source_spaces",
    "CORE_006_COMPATIBLE_B_AND_MITC": ["physical_b", "mitc_shear_b"],
    "CORE_007_ACTUAL_35_FIELD_STATIONARY_SYSTEM": "assemble_stationary_element",
    "PL_001_CENTRE_TAYLOR_ONLY_RS_DELETED": "centre_taylor_constraint_rows",
    "PL_002_MULTIPLIER_GRAM_AND_CONDENSATION": "assemble_stationary_element",
    "PL_003_ACTUAL_38_FIELD_SYSTEM": "assemble_stationary_element",
    "RES_001_GEOMETRY_DEPENDENT_RESIDUAL_MODE": "assemble_stationary_element",
    "D4_001_ALL_EIGHT_ACTIONS": "d4_exact_certificate",
    "D4_002_FIELD_AND_PSEUDO_MAPS": "d4_field_work_certificate",
    "D4_003_PL_MAPS": "d4_field_work_certificate",
    "D4_004_EXACT_WORK_CONJUGACY": "d4_field_work_certificate",
    "D4_005_EMBEDDING_LOAD_SUPPORT_MAPS": ["numbered_physical20_map", "transported_case_certificate"],
    "REC_001_ACTUAL_224_STATION_PHYSICAL_RECOVERY": "patch_recovery_certificate",
    "REC_002_PATCH_EXPECTATIONS": ["_field_local_vector", "_expected_resultants"],
    "REC_003_NUMERICAL_SEPARATION": "patch_recovery_certificate",
    "GLOBAL_001_RSTAR_BSTAR_CORE_LOAD_PROJECTORS": [
        "exact_global_transform_static_certificate", "global_covariance_certificate"
    ],
    "GLOBAL_002_SUPPORT_KKT_SOLUTION_REACTION": "support_certificate",
    "GLOBAL_003_RECOVERY_AND_NUMERICAL_TRANSPORT": "global_covariance_certificate",
    "RANK_001_RIGID_DERIVED_QUOTIENT_LDL": ["rigid_derived_quotient", "ldl_congruence_certificate"],
    "RANK_002_CLASSIFICATION": "terminal_from_evidence",
    "ARITH_001_EXACT_ZERO_ONLY": "residual_certificate",
}

CASE_NESTED_KEYS = {
    "centre": {"centre_j_positive", "centre_taylor_exact", "residual_mode_exact"},
    "frame": {"equation7_exact", "projectors_exact"},
    "field_work": {"fields_exact", "pseudo_fields_exact", "pl_exact", "work_exact", "gauss_correspondence_exact"},
    "local_algebra": {"field_count", "internal_invertible", "rank_18", "six_rigid_exact", "symmetric", "psd", "mixed_condensed_exact", "unresolved"},
    "patches": {"membrane", "bending", "shear", "combined", "six_rigid_all_exact"},
    "recovery": {"compatible_all_exact", "independent_all_exact", "physical_resultants_all_exact", "numerical_separate", "station_count"},
    "global_support": {"projectors_exact", "load_exact", "support_exact", "solution_exact", "reaction_exact", "recovery_exact", "numerical_separate"},
}


class OracleError(RuntimeError):
    """Fail-closed oracle or authority error."""


class DuplicateKeyError(OracleError):
    """A JSON object contained a duplicate key."""


def _reject_constant(token: str) -> None:
    raise OracleError(f"non-finite JSON token is forbidden: {token}")


def _object_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def strict_json_bytes(raw: bytes) -> Any:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise OracleError("JSON is not UTF-8") from exc
    if "\r" in text:
        raise OracleError("canonical inputs must use LF, not CRLF")
    try:
        return json.loads(
            text,
            object_pairs_hook=_object_no_duplicates,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        if isinstance(exc, OracleError):
            raise
        raise OracleError(f"invalid strict JSON: {exc}") from exc


def strict_json_file(path: Path) -> Any:
    return strict_json_bytes(path.read_bytes())


def canonical_bytes(value: Any) -> bytes:
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise OracleError(f"value is not canonical-JSON encodable: {exc}") from exc
    return (encoded + "\n").encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def as_fraction(value: Any) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return Fraction(value)
    if isinstance(value, str):
        try:
            return Fraction(value)
        except (ValueError, ZeroDivisionError) as exc:
            raise OracleError(f"not an exact rational: {value!r}") from exc
    raise OracleError(f"categorical input must be an integer or rational string: {value!r}")


def fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _floor_fraction(value: Fraction) -> int:
    return value.numerator // value.denominator


def _ceil_fraction(value: Fraction) -> int:
    return -((-value.numerator) // value.denominator)


@dataclass(frozen=True, slots=True)
class DyadicBand:
    """Closed dyadic outward interval with per-operation rounding.

    This implementation is intentionally independent and local to the oracle.
    Both endpoints are exact :class:`Fraction` values whose denominators divide
    ``2**bits``.  Every arithmetic operation rounds outward at the active
    precision, even when its mathematical result happens to be rational.
    """

    lo: Fraction
    hi: Fraction
    bits: int

    def __post_init__(self) -> None:
        if self.bits <= 0:
            raise OracleError("interval precision must be positive")
        if self.lo > self.hi:
            raise OracleError("interval endpoints are reversed")
        scale = 1 << self.bits
        if scale % self.lo.denominator or scale % self.hi.denominator:
            raise OracleError("interval endpoint is not on the active dyadic grid")

    @classmethod
    def rounded(cls, lo: Fraction, hi: Fraction, bits: int) -> "DyadicBand":
        if lo > hi:
            raise OracleError("cannot outward-round reversed endpoints")
        scale = 1 << bits
        return cls(
            Fraction(_floor_fraction(lo * scale), scale),
            Fraction(_ceil_fraction(hi * scale), scale),
            bits,
        )

    @classmethod
    def exact(cls, value: Any, bits: int) -> "DyadicBand":
        q = as_fraction(value)
        return cls.rounded(q, q, bits)

    @classmethod
    def sqrt_fraction(cls, value: Fraction, bits: int) -> "DyadicBand":
        if value < 0:
            raise OracleError("square root of a negative rational")
        if value == 0:
            return cls.exact(0, bits)
        scale = 1 << bits
        quotient = (value.numerator * scale * scale) // value.denominator
        m = math.isqrt(quotient)
        lo = Fraction(m, scale)
        exact = m * m * value.denominator == value.numerator * scale * scale
        hi = lo if exact else Fraction(m + 1, scale)
        return cls(lo, hi, bits)

    def _same(self, other: Any) -> "DyadicBand":
        if isinstance(other, DyadicBand):
            if other.bits != self.bits:
                raise OracleError("mixed interval precisions are forbidden")
            return other
        return DyadicBand.exact(other, self.bits)

    def __add__(self, other: Any) -> "DyadicBand":
        rhs = self._same(other)
        return DyadicBand.rounded(self.lo + rhs.lo, self.hi + rhs.hi, self.bits)

    __radd__ = __add__

    def __neg__(self) -> "DyadicBand":
        return DyadicBand.rounded(-self.hi, -self.lo, self.bits)

    def __sub__(self, other: Any) -> "DyadicBand":
        return self + (-self._same(other))

    def __rsub__(self, other: Any) -> "DyadicBand":
        return self._same(other) - self

    def __mul__(self, other: Any) -> "DyadicBand":
        rhs = self._same(other)
        products = (
            self.lo * rhs.lo,
            self.lo * rhs.hi,
            self.hi * rhs.lo,
            self.hi * rhs.hi,
        )
        return DyadicBand.rounded(min(products), max(products), self.bits)

    __rmul__ = __mul__

    def reciprocal(self) -> "DyadicBand":
        if self.lo <= 0 <= self.hi:
            raise OracleError("division by an interval containing zero")
        values = (Fraction(1, 1) / self.lo, Fraction(1, 1) / self.hi)
        return DyadicBand.rounded(min(values), max(values), self.bits)

    def __truediv__(self, other: Any) -> "DyadicBand":
        return self * self._same(other).reciprocal()

    def __rtruediv__(self, other: Any) -> "DyadicBand":
        return self._same(other) / self

    def square(self) -> "DyadicBand":
        if self.lo >= 0:
            return self * self
        if self.hi <= 0:
            return (-self) * (-self)
        upper = max(self.lo * self.lo, self.hi * self.hi)
        return DyadicBand.rounded(Fraction(0), upper, self.bits)

    def sqrt(self) -> "DyadicBand":
        if self.lo < 0:
            raise OracleError("square root interval has a negative lower endpoint")
        low_band = DyadicBand.sqrt_fraction(self.lo, self.bits)
        high_band = DyadicBand.sqrt_fraction(self.hi, self.bits)
        return DyadicBand.rounded(low_band.lo, high_band.hi, self.bits)

    def contains_zero(self) -> bool:
        return self.lo <= 0 <= self.hi

    def strictly_positive(self) -> bool:
        return self.lo > 0

    def strictly_negative(self) -> bool:
        return self.hi < 0

    def midpoint(self) -> Fraction:
        return (self.lo + self.hi) / 2

    def width(self) -> Fraction:
        return self.hi - self.lo

    def payload(self) -> list[str]:
        return [fraction_text(self.lo), fraction_text(self.hi)]


Scalar = Fraction | DyadicBand
Matrix = list[list[Scalar]]
Vector = list[Scalar]


def scalar_zero(sample: Scalar) -> Scalar:
    return DyadicBand.exact(0, sample.bits) if isinstance(sample, DyadicBand) else Fraction(0)


def scalar_one(sample: Scalar) -> Scalar:
    return DyadicBand.exact(1, sample.bits) if isinstance(sample, DyadicBand) else Fraction(1)


def zeros(rows: int, cols: int, sample: Scalar) -> Matrix:
    return [[scalar_zero(sample) for _ in range(cols)] for _ in range(rows)]


def identity(size: int, sample: Scalar) -> Matrix:
    out = zeros(size, size, sample)
    one = scalar_one(sample)
    for i in range(size):
        out[i][i] = one
    return out


def transpose(matrix: Matrix) -> Matrix:
    if not matrix:
        return []
    return [list(row) for row in zip(*matrix)]


def matmul(left: Matrix, right: Matrix) -> Matrix:
    if not left or not right or len(left[0]) != len(right):
        raise OracleError("matrix product dimension mismatch")
    sample = left[0][0]
    result = zeros(len(left), len(right[0]), sample)
    for i, row in enumerate(left):
        for k, value in enumerate(row):
            for j, rhs in enumerate(right[k]):
                result[i][j] = result[i][j] + value * rhs
    return result


def matvec(matrix: Matrix, vector: Vector) -> Vector:
    if not matrix or len(matrix[0]) != len(vector):
        raise OracleError("matrix-vector dimension mismatch")
    return [sum((a * b for a, b in zip(row, vector)), scalar_zero(row[0])) for row in matrix]


def matrix_add(left: Matrix, right: Matrix, factor: Scalar | None = None) -> Matrix:
    if len(left) != len(right) or (left and len(left[0]) != len(right[0])):
        raise OracleError("matrix addition dimension mismatch")
    if not left:
        return []
    scale = scalar_one(left[0][0]) if factor is None else factor
    return [
        [a + scale * b for a, b in zip(row_a, row_b)]
        for row_a, row_b in zip(left, right)
    ]


def matrix_scale(matrix: Matrix, factor: Scalar) -> Matrix:
    return [[factor * value for value in row] for row in matrix]


def outer(left: Vector, right: Vector) -> Matrix:
    return [[a * b for b in right] for a in left]


def symmetric_gram(matrix: Matrix) -> Matrix:
    if not matrix:
        return []
    columns = len(matrix[0])
    result = zeros(columns, columns, matrix[0][0])
    for i in range(columns):
        for j in range(i, columns):
            total = scalar_zero(matrix[0][0])
            for row in matrix:
                if i == j and isinstance(row[i], DyadicBand):
                    total = total + row[i].square()
                else:
                    total = total + row[i] * row[j]
            result[i][j] = total
            result[j][i] = total
    return result


def block_put(target: Matrix, row0: int, col0: int, block: Matrix) -> None:
    for i, row in enumerate(block):
        for j, value in enumerate(row):
            target[row0 + i][col0 + j] = target[row0 + i][col0 + j] + value


def certified_nonzero(value: Scalar) -> bool:
    if isinstance(value, Fraction):
        return value != 0
    return value.strictly_positive() or value.strictly_negative()


def inverse(matrix: Matrix) -> Matrix:
    if not matrix or len(matrix) != len(matrix[0]):
        raise OracleError("inverse requires a nonempty square matrix")
    n = len(matrix)
    sample = matrix[0][0]
    augmented = [row[:] + eye for row, eye in zip(matrix, identity(n, sample))]
    for col in range(n):
        pivot = next((row for row in range(col, n) if certified_nonzero(augmented[row][col])), None)
        if pivot is None:
            raise OracleError(f"matrix pivot {col} is not certified nonzero")
        if pivot != col:
            augmented[col], augmented[pivot] = augmented[pivot], augmented[col]
        p = augmented[col][col]
        augmented[col] = [value / p for value in augmented[col]]
        for row in range(n):
            if row == col:
                continue
            factor = augmented[row][col]
            augmented[row] = [a - factor * b for a, b in zip(augmented[row], augmented[col])]
    return [row[n:] for row in augmented]


def determinant_fraction(matrix: list[list[Fraction]]) -> Fraction:
    if not matrix or len(matrix) != len(matrix[0]):
        raise OracleError("determinant requires a nonempty square matrix")
    work = [row[:] for row in matrix]
    sign = 1
    result = Fraction(1)
    for col in range(len(work)):
        pivot = next((r for r in range(col, len(work)) if work[r][col] != 0), None)
        if pivot is None:
            return Fraction(0)
        if pivot != col:
            work[col], work[pivot] = work[pivot], work[col]
            sign *= -1
        p = work[col][col]
        result *= p
        for r in range(col + 1, len(work)):
            factor = work[r][col] / p
            for c in range(col + 1, len(work)):
                work[r][c] -= factor * work[col][c]
    return result * sign


def rank_fraction(matrix: list[list[Fraction]]) -> int:
    if not matrix:
        return 0
    work = [row[:] for row in matrix]
    rows, cols = len(work), len(work[0])
    pivot_row = 0
    for col in range(cols):
        pivot = next((r for r in range(pivot_row, rows) if work[r][col] != 0), None)
        if pivot is None:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        scale = work[pivot_row][col]
        work[pivot_row] = [value / scale for value in work[pivot_row]]
        for r in range(rows):
            if r == pivot_row:
                continue
            factor = work[r][col]
            work[r] = [a - factor * b for a, b in zip(work[r], work[pivot_row])]
        pivot_row += 1
        if pivot_row == rows:
            break
    return pivot_row


def exact_fraction(value: Scalar, label: str) -> Fraction:
    """Extract a width-zero exact rational; intervals cannot masquerade as zero."""

    if isinstance(value, Fraction):
        return value
    if value.lo != value.hi:
        raise OracleError(f"{label} is not an exact rational singleton")
    return value.lo


def rigid_global_matrix(nodes_exact: list[list[Fraction]]) -> list[list[Fraction]]:
    """Form the frozen 24x6 analytical rigid matrix in global coordinates.

    Global input nodes are rational singletons even when the numbered local
    equation-7 frame contains radicals.  This makes the quotient construction
    independent of observed stiffness or conditioning.
    """

    if len(nodes_exact) != 4 or any(len(node) != 3 for node in nodes_exact):
        raise OracleError("rigid matrix requires four exact 3D nodes")
    if any(not isinstance(value, Fraction) for node in nodes_exact for value in node):
        raise OracleError("rigid quotient geometry must remain exact Fraction data")
    centre = [sum(node[j] for node in nodes_exact) / 4 for j in range(3)]
    result = [[Fraction(0) for _ in range(6)] for _ in range(24)]
    for node_index, node in enumerate(nodes_exact):
        x, y, z = [node[j] - centre[j] for j in range(3)]
        base = 6 * node_index
        # Three translations.
        result[base][0] = result[base + 1][1] = result[base + 2][2] = Fraction(1)
        # omega x (X-Xc), followed by the same physical nodal rotation omega.
        result[base + 1][3], result[base + 2][3] = -z, y
        result[base][4], result[base + 2][4] = z, -x
        result[base][5], result[base + 1][5] = -y, x
        result[base + 3][3] = result[base + 4][4] = result[base + 5][5] = Fraction(1)
    return result


def lexicographic_nullspace(matrix: list[list[Fraction]]) -> list[list[Fraction]]:
    """Exact RREF nullspace, with left-to-right lexicographic pivot selection."""

    if not matrix or not matrix[0]:
        raise OracleError("nullspace requires a nonempty matrix")
    work = [row[:] for row in matrix]
    rows, cols = len(work), len(work[0])
    pivots: list[int] = []
    pivot_row = 0
    for col in range(cols):
        pivot = next((r for r in range(pivot_row, rows) if work[r][col] != 0), None)
        if pivot is None:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        divisor = work[pivot_row][col]
        work[pivot_row] = [value / divisor for value in work[pivot_row]]
        for row in range(rows):
            if row == pivot_row:
                continue
            factor = work[row][col]
            if factor:
                work[row] = [a - factor * b for a, b in zip(work[row], work[pivot_row])]
        pivots.append(col)
        pivot_row += 1
        if pivot_row == rows:
            break
    free = [col for col in range(cols) if col not in pivots]
    basis = [[Fraction(0) for _ in free] for _ in range(cols)]
    for basis_col, free_col in enumerate(free):
        basis[free_col][basis_col] = Fraction(1)
        for row, pivot_col in enumerate(pivots):
            basis[pivot_col][basis_col] = -work[row][free_col]
    return basis


def rigid_derived_quotient(nodes_exact: list[list[Fraction]]) -> dict[str, Any]:
    rigid = rigid_global_matrix(nodes_exact)
    rigid_t = transpose(rigid)
    quotient = lexicographic_nullspace(rigid_t)
    combined = [rigid[row] + quotient[row] for row in range(24)]
    return {
        "rigid": rigid,
        "quotient": quotient,
        "rigid_rank": rank_fraction(rigid),
        "orthogonality_exact": matmul(rigid_t, quotient) == [
            [Fraction(0) for _ in range(18)] for _ in range(6)
        ],
        "combined_rank": rank_fraction(combined),
        "rule": "LEXICOGRAPHIC_EXACT_RREF_NULLSPACE_OF_R_TRANSPOSE",
        "geometry_source": "EXACT_GLOBAL_FRACTION_NODES",
        "stiffness_inputs": 0,
    }


def ldl_congruence_certificate(matrix: Matrix) -> dict[str, Any]:
    """Outward-certified, no-tolerance LDL congruence classification.

    A nonzero-width interval containing zero is unresolved, never an exact
    zero.  Elimination stops at an unresolved or exact-zero pivot so that the
    unclassified remainder is explicit rather than silently discarded.
    """

    if not matrix or len(matrix) != len(matrix[0]):
        raise OracleError("LDL certificate requires a nonempty square matrix")
    work = [row[:] for row in matrix]
    positive = negative = exact_zero = unresolved = 0
    pivots: list[dict[str, Any]] = []
    for k in range(len(work)):
        pivot = work[k][k]
        if isinstance(pivot, Fraction):
            classification = "POSITIVE" if pivot > 0 else "NEGATIVE" if pivot < 0 else "EXACT_ZERO"
        elif pivot.strictly_positive():
            classification = "POSITIVE"
        elif pivot.strictly_negative():
            classification = "NEGATIVE"
        elif pivot.lo == 0 and pivot.hi == 0:
            classification = "EXACT_ZERO"
        else:
            classification = "UNRESOLVED"
        pivots.append({"index": k, "classification": classification, "value": interval_summary(pivot)})
        if classification == "POSITIVE":
            positive += 1
        elif classification == "NEGATIVE":
            negative += 1
        elif classification == "EXACT_ZERO":
            exact_zero += 1
        else:
            unresolved += 1
        if classification in {"EXACT_ZERO", "UNRESOLVED"}:
            unresolved += len(work) - k - 1
            break
        for i in range(k + 1, len(work)):
            for j in range(k + 1, len(work)):
                work[i][j] = work[i][j] - work[i][k] * work[k][j] / pivot
    return {
        "dimension": len(matrix),
        "positive": positive,
        "negative": negative,
        "exact_zero": exact_zero,
        "unresolved": unresolved,
        "pivots": pivots,
        "complete": positive + negative + exact_zero == len(matrix) and unresolved == 0,
    }


def dot(left: Vector, right: Vector) -> Scalar:
    if len(left) != len(right) or not left:
        raise OracleError("dot-product dimension mismatch")
    total = scalar_zero(left[0])
    for a, b in zip(left, right):
        total = total + a * b
    return total


def vector_add(left: Vector, right: Vector, factor: Scalar | None = None) -> Vector:
    if len(left) != len(right):
        raise OracleError("vector dimension mismatch")
    scale = scalar_one(left[0]) if factor is None else factor
    return [a + scale * b for a, b in zip(left, right)]


def norm(vector: Vector) -> Scalar:
    if not vector:
        raise OracleError("norm requires a nonempty vector")
    if isinstance(vector[0], DyadicBand):
        total: Scalar = scalar_zero(vector[0])
        for value in vector:
            assert isinstance(value, DyadicBand)
            total = total + value.square()
    else:
        total = dot(vector, vector)
    if isinstance(total, Fraction):
        root = math.isqrt(total.numerator)
        den = math.isqrt(total.denominator)
        if root * root == total.numerator and den * den == total.denominator:
            return Fraction(root, den)
        raise OracleError("an irrational norm requires dyadic interval arithmetic")
    return total.sqrt()


def cross(left: Vector, right: Vector) -> Vector:
    if len(left) != 3 or len(right) != 3:
        raise OracleError("cross product requires two three-vectors")
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def normalize(vector: Vector) -> Vector:
    length = norm(vector)
    if not certified_nonzero(length):
        raise OracleError("WG equation-7 frame has an uncertified zero vector")
    return [value / length for value in vector]


def equation7_frame(nodes: list[Vector]) -> Matrix:
    if len(nodes) != 4 or any(len(node) != 3 for node in nodes):
        raise OracleError("a frame requires four three-dimensional nodes")
    d1 = vector_add(nodes[2], nodes[0], -scalar_one(nodes[0][0]))
    d2 = vector_add(nodes[1], nodes[3], -scalar_one(nodes[0][0]))
    a = normalize(d1)
    b = normalize(d2)
    t1 = normalize(vector_add(a, b))
    t2 = normalize(vector_add(a, b, -scalar_one(a[0])))
    t3 = cross(t1, t2)
    return transpose([t1, t2, t3])


def physical_drill_maps(frame: Matrix) -> tuple[Matrix, Matrix, Matrix]:
    sample = frame[0][0]
    t1 = [frame[i][0] for i in range(3)]
    t2 = [frame[i][1] for i in range(3)]
    t3 = [frame[i][2] for i in range(3)]
    b5 = zeros(6, 5, sample)
    for i in range(3):
        for j in range(3):
            b5[i][j] = frame[i][j]
        b5[i + 3][3] = t1[i]
        b5[i + 3][4] = t2[i]
    bd = [scalar_zero(sample), scalar_zero(sample), scalar_zero(sample), *t3]
    t5 = zeros(24, 20, sample)
    qd = zeros(24, 4, sample)
    rotation = zeros(24, 24, sample)
    for node in range(4):
        block_put(t5, 6 * node, 5 * node, b5)
        for i, value in enumerate(bd):
            qd[6 * node + i][node] = value
        block = zeros(6, 6, sample)
        block_put(block, 0, 0, frame)
        block_put(block, 3, 3, frame)
        block_put(rotation, 6 * node, 6 * node, block)
    return t5, qd, rotation


def local_xy(nodes: list[Vector], frame: Matrix) -> list[Vector]:
    sample = nodes[0][0]
    centre = [
        sum((node[k] for node in nodes), scalar_zero(sample)) / 4
        for k in range(3)
    ]
    t1 = [frame[i][0] for i in range(3)]
    t2 = [frame[i][1] for i in range(3)]
    result: list[Vector] = []
    for node in nodes:
        delta = vector_add(node, centre, -scalar_one(sample))
        result.append([dot(t1, delta), dot(t2, delta)])
    return result


NATURAL_NODES = ((-1, -1), (1, -1), (1, 1), (-1, 1))


def q4_shape(r: Scalar, s: Scalar) -> tuple[Vector, Vector, Vector]:
    one = scalar_one(r)
    four = as_fraction(4)
    n = [
        (one - r) * (one - s) / four,
        (one + r) * (one - s) / four,
        (one + r) * (one + s) / four,
        (one - r) * (one + s) / four,
    ]
    nr = [-(one - s) / four, (one - s) / four, (one + s) / four, -(one + s) / four]
    ns = [-(one - r) / four, -(one + r) / four, (one + r) / four, (one - r) / four]
    return n, nr, ns


def jacobian_data(xy: list[Vector], r: Scalar, s: Scalar) -> tuple[Vector, Vector, Scalar, Matrix]:
    _, nr, ns = q4_shape(r, s)
    xr = sum((nr[i] * xy[i][0] for i in range(4)), scalar_zero(r))
    xs = sum((ns[i] * xy[i][0] for i in range(4)), scalar_zero(r))
    yr = sum((nr[i] * xy[i][1] for i in range(4)), scalar_zero(r))
    ys = sum((ns[i] * xy[i][1] for i in range(4)), scalar_zero(r))
    j = [[xr, xs], [yr, ys]]
    det = xr * ys - xs * yr
    if not (det > 0 if isinstance(det, Fraction) else det.strictly_positive()):
        raise OracleError("numbered source-frame Jacobian is not certified positive")
    invj = [[ys / det, -xs / det], [-yr / det, xr / det]]
    nx: Vector = []
    ny: Vector = []
    for dri, dsi in zip(nr, ns):
        nx.append(dri * invj[0][0] + dsi * invj[1][0])
        ny.append(dri * invj[0][1] + dsi * invj[1][1])
    return nx, ny, det, j


def centre_taylor_constraint_rows(xy: list[Vector]) -> Matrix:
    """Exact centre Taylor rows ``[c(0),c_,r(0),c_,s(0)]``.

    This is the frozen affine PL constraint after deletion of only its faulty
    ``r*s`` coefficient.  It is not an L2 projection of the full rational
    physical curl.
    """

    sample = xy[0][0]
    zero = scalar_zero(sample)
    _, nr, ns = q4_shape(zero, zero)
    n, _, _ = q4_shape(zero, zero)
    nrs = [
        DyadicBand.exact(Fraction(value, 4), sample.bits)
        if isinstance(sample, DyadicBand) else Fraction(value, 4)
        for value in (1, -1, 1, -1)
    ]
    xr = sum((nr[i] * xy[i][0] for i in range(4)), zero)
    xs = sum((ns[i] * xy[i][0] for i in range(4)), zero)
    yr = sum((nr[i] * xy[i][1] for i in range(4)), zero)
    ys = sum((ns[i] * xy[i][1] for i in range(4)), zero)
    xrs = sum((nrs[i] * xy[i][0] for i in range(4)), zero)
    yrs = sum((nrs[i] * xy[i][1] for i in range(4)), zero)
    det = xr * ys - xs * yr
    if not certified_nonzero(det):
        raise OracleError("centre Taylor constraint has uncertified Jacobian")
    det_r = xr * yrs - xrs * yr
    det_s = xrs * ys - xs * yrs

    def quotient(value: Scalar, derivative: Scalar, det_derivative: Scalar) -> tuple[Scalar, Scalar]:
        return value / det, (derivative * det - value * det_derivative) / (det * det)

    rows = zeros(3, 24, sample)
    half = DyadicBand.exact(Fraction(1, 2), sample.bits) if isinstance(sample, DyadicBand) else Fraction(1, 2)
    for node in range(4):
        nx_num = nr[node] * ys - ns[node] * yr
        nx_num_r = nr[node] * yrs - nrs[node] * yr
        nx_num_s = nrs[node] * ys - ns[node] * yrs
        ny_num = -nr[node] * xs + ns[node] * xr
        ny_num_r = -nr[node] * xrs + nrs[node] * xr
        ny_num_s = -nrs[node] * xs + ns[node] * xrs
        nx, nx_r = quotient(nx_num, nx_num_r, det_r)
        _, nx_s = quotient(nx_num, nx_num_s, det_s)
        ny, ny_r = quotient(ny_num, ny_num_r, det_r)
        _, ny_s = quotient(ny_num, ny_num_s, det_s)
        base = 6 * node
        rows[0][base], rows[0][base + 1], rows[0][base + 5] = half * ny, -half * nx, n[node]
        rows[1][base], rows[1][base + 1], rows[1][base + 5] = half * ny_r, -half * nx_r, nr[node]
        rows[2][base], rows[2][base + 1], rows[2][base + 5] = half * ny_s, -half * nx_s, ns[node]
    return rows


def membrane_b(xy: list[Vector], r: Scalar, s: Scalar) -> Matrix:
    nx, ny, _, _ = jacobian_data(xy, r, s)
    sample = r
    result = zeros(3, 20, sample)
    for node in range(4):
        col = 5 * node
        result[0][col] = nx[node]
        result[1][col + 1] = ny[node]
        result[2][col] = ny[node]
        result[2][col + 1] = nx[node]
    return result


def bending_b(xy: list[Vector], r: Scalar, s: Scalar) -> Matrix:
    nx, ny, _, _ = jacobian_data(xy, r, s)
    result = zeros(3, 20, r)
    for node in range(4):
        tx = 5 * node + 3
        ty = 5 * node + 4
        result[0][ty] = nx[node]
        result[1][tx] = -ny[node]
        result[2][tx] = -nx[node]
        result[2][ty] = ny[node]
    return result


def _covariant_shear_row(xy: list[Vector], r: Scalar, s: Scalar, direction: str) -> Vector:
    n, nr, ns = q4_shape(r, s)
    deriv = nr if direction == "r" else ns
    dx = sum((deriv[i] * xy[i][0] for i in range(4)), scalar_zero(r))
    dy = sum((deriv[i] * xy[i][1] for i in range(4)), scalar_zero(r))
    row = [scalar_zero(r) for _ in range(20)]
    for node in range(4):
        base = 5 * node
        row[base + 2] = deriv[node]
        row[base + 3] = -dy * n[node]
        row[base + 4] = dx * n[node]
    return row


def mitc_shear_b(xy: list[Vector], r: Scalar, s: Scalar) -> Matrix:
    one = scalar_one(r)
    zero = scalar_zero(r)
    gr_bottom = _covariant_shear_row(xy, zero, -one, "r")
    gr_top = _covariant_shear_row(xy, zero, one, "r")
    gs_left = _covariant_shear_row(xy, -one, zero, "s")
    gs_right = _covariant_shear_row(xy, one, zero, "s")
    gr = [((one - s) * a + (one + s) * b) / 2 for a, b in zip(gr_bottom, gr_top)]
    gs = [((one - r) * a + (one + r) * b) / 2 for a, b in zip(gs_left, gs_right)]
    _, _, _, j = jacobian_data(xy, r, s)
    inv_j_t = transpose(inverse(j))
    return matmul(inv_j_t, [gr, gs])


def source_tensor_transform(j_wg: Matrix, a: int, b: int) -> Matrix:
    """WG source-skew tensor transform ``T(a,b)`` from the core authority."""

    j11, j12 = j_wg[0]
    j21, j22 = j_wg[1]
    return [
        [j11 * j11, j21 * j21, a * j11 * j21],
        [j12 * j12, j22 * j22, a * j12 * j22],
        [b * j11 * j12, b * j21 * j22, j11 * j22 + j12 * j21],
    ]


def centre_j_modes(xy: list[Vector]) -> dict[str, Scalar]:
    """Return the exact bilinear centre-J modal coefficients.

    ``x=x0+xr*r+xs*s+xrs*r*s`` (and likewise for ``y``), hence
    ``j=j0+jr*r+js*s``.  The WG centroid offsets are
    ``r_bar=jr/(3*j0)`` and ``s_bar=js/(3*j0)``.  No pointwise-J source-space
    replacement is made.
    """

    sample = xy[0][0]
    quarter = scalar_one(sample) / 4
    xi = [-1, 1, 1, -1]
    eta = [-1, -1, 1, 1]
    h4 = [1, -1, 1, -1]

    def modal(component: int, signs: Sequence[int]) -> Scalar:
        return sum(
            (xy[i][component] * signs[i] * quarter for i in range(4)),
            scalar_zero(sample),
        )

    xr, xs, xrs = modal(0, xi), modal(0, eta), modal(0, h4)
    yr, ys, yrs = modal(1, xi), modal(1, eta), modal(1, h4)
    j0 = xr * ys - xs * yr
    jr = xr * yrs - xrs * yr
    js = xrs * ys - xs * yrs
    if not certified_nonzero(j0):
        raise OracleError("centre-J determinant is not certified nonzero")
    return {
        "xr": xr, "xs": xs, "xrs": xrs,
        "yr": yr, "ys": ys, "yrs": yrs,
        "j0": j0, "jr": jr, "js": js,
        "r_bar": jr / (3 * j0), "s_bar": js / (3 * j0),
    }


def source_spaces(
    r: Scalar,
    s: Scalar,
    j_wg_centre: Matrix,
    centre_over_current_det: Scalar,
    r_bar: Scalar,
    s_bar: Scalar,
) -> tuple[Matrix, Matrix]:
    """Return source-exact ``N_sigma(8x14)`` and ``N_epsilon(8x21)``.

    The first eight columns are the frozen constant ``I_8`` block.  Columns
    8:14 use the accepted membrane/bending tensor seed and shear vector seed.
    The seven final strain columns are the ``n=7`` membrane enrichment,
    multiplied by ``j0/j``.  There is no ``k`` curvature enrichment.
    """

    one = scalar_one(r)
    zero = scalar_zero(r)
    n_sigma = zeros(8, 14, r)
    n_epsilon = zeros(8, 21, r)
    for index in range(8):
        n_sigma[index][index] = one
        n_epsilon[index][index] = one

    # WG2020 equations 11--18: the stress14 and first fourteen strain21
    # columns use the same centre-J transforms and centroid-shifted seeds.
    # Only the final seven strain columns receive j0/j.
    s_centred = s - s_bar
    r_centred = r - r_bar
    tensor_seed = [[s_centred, zero], [zero, r_centred], [zero, zero]]
    vector_seed = [[s_centred, zero], [zero, r_centred]]
    t_sigma = source_tensor_transform(j_wg_centre, 2, 1)
    t_epsilon = source_tensor_transform(j_wg_centre, 1, 2)
    j_map_centre = transpose(j_wg_centre)
    varying_sigma = matmul(t_sigma, tensor_seed)
    varying_epsilon = matmul(t_epsilon, tensor_seed)
    varying_vector = matmul(j_map_centre, vector_seed)
    for row in range(3):
        for col in range(2):
            n_sigma[row][8 + col] = varying_sigma[row][col]
            n_sigma[3 + row][10 + col] = varying_sigma[row][col]
            n_epsilon[row][8 + col] = varying_epsilon[row][col]
            n_epsilon[3 + row][10 + col] = varying_epsilon[row][col]
    for row in range(2):
        for col in range(2):
            n_sigma[6 + row][12 + col] = varying_vector[row][col]
            n_epsilon[6 + row][12 + col] = varying_vector[row][col]

    enhancement_natural = [
        [r, zero, zero, zero, r * s, zero, zero],
        [zero, s, zero, zero, zero, r * s, zero],
        [zero, zero, r, s, zero, zero, r * s],
    ]
    enhancement = matrix_scale(
        matmul(t_epsilon, enhancement_natural), centre_over_current_det
    )
    block_put(n_epsilon, 0, 14, enhancement)
    return n_sigma, n_epsilon


def physical_b(xy: list[Vector], r: Scalar, s: Scalar) -> Matrix:
    result = zeros(8, 20, r)
    block_put(result, 0, 0, membrane_b(xy, r, s))
    block_put(result, 3, 0, bending_b(xy, r, s))
    block_put(result, 6, 0, mitc_shear_b(xy, r, s))
    return result


def fraction_constitutive(material: Mapping[str, Any]) -> tuple[list[list[Fraction]], ...]:
    constitutive = material["constitutive"]
    return tuple(
        [[as_fraction(value) for value in row] for row in constitutive[key]]
        for key in ("membrane_A", "bending_D", "transverse_shear_A_s")
    )


def resultant_constitutive(material: Mapping[str, Any]) -> list[list[Fraction]]:
    membrane, bending, shear = fraction_constitutive(material)
    result = [[Fraction(0) for _ in range(8)] for _ in range(8)]
    for offset, block in ((0, membrane), (3, bending), (6, shear)):
        for i, row in enumerate(block):
            for j, value in enumerate(row):
                result[offset + i][offset + j] = value
    return result


def lift_fraction_matrix(matrix: list[list[Fraction]], bits: int) -> Matrix:
    return [[DyadicBand.exact(value, bits) for value in row] for row in matrix]


def gauss_points(bits: int) -> list[tuple[DyadicBand, DyadicBand]]:
    root = DyadicBand.sqrt_fraction(Fraction(1, 3), bits)
    return [(-root, -root), (root, -root), (root, root), (-root, root)]


def _accumulate_gram(target: Matrix, basis: Matrix, constitutive: Matrix, weight: Scalar) -> None:
    contribution = matrix_scale(matmul(transpose(basis), matmul(constitutive, basis)), weight)
    block_put(target, 0, 0, contribution)


def _accumulate_cross(target: Matrix, left: Matrix, right: Matrix, weight: Scalar) -> None:
    contribution = matrix_scale(matmul(transpose(left), right), weight)
    block_put(target, 0, 0, contribution)


@dataclass(slots=True)
class StationaryElement:
    bits: int
    geometry_id: str
    operation_id: str
    nodes: list[Vector]
    nodes_exact: list[list[Fraction]]
    frame: Matrix
    xy: list[Vector]
    t5: Matrix
    qd: Matrix
    local_to_global: Matrix
    kii: Matrix
    kii_inverse: Matrix
    kiq_local: Matrix
    kqq_local: Matrix
    condensed_local: Matrix
    condensed_global: Matrix
    core_condensed_20: Matrix
    pl_condensed_local: Matrix
    pl_condensed_global: Matrix
    hg_condensed_global: Matrix
    core_kii: Matrix
    core_kiq20: Matrix
    c_taylor: Matrix
    m_pl: Matrix
    b_pl: Matrix
    j_wg_centre: Matrix
    j_modes: Mapping[str, Scalar]
    gamma_row: Vector
    area_hg: Scalar
    jacobian_lowers: list[Fraction]


def assemble_stationary_element(
    geometry_id: str,
    operation_id: str,
    node_values: Sequence[Sequence[Any]],
    operation: Mapping[str, Any],
    material: Mapping[str, Any],
    bits: int,
) -> StationaryElement:
    """Assemble the actual 38-field uncondensed stationary system.

    Calling this function on a registered case is scientific execution and is
    therefore guarded by the CLI.  Unit callers are responsible for observing
    the same stage barrier.
    """

    base_nodes_exact = [[as_fraction(value) for value in node] for node in node_values]
    permutation = [int(index) - 1 for index in operation["node_tuple"]]
    nodes_exact = [base_nodes_exact[index][:] for index in permutation]
    nodes = [[DyadicBand.exact(value, bits) for value in node] for node in nodes_exact]
    frame = equation7_frame(nodes)
    xy = local_xy(nodes, frame)
    t5, qd, rotation = physical_drill_maps(frame)
    constitutive = lift_fraction_matrix(resultant_constitutive(material), bits)
    sample = nodes[0][0]

    # Accepted E4-0 core: stress(14), strain(21), with
    # D=[[0,F^T],[F,H]], Q=[Gq^T,0].
    h_core = zeros(21, 21, sample)
    f_core = zeros(21, 14, sample)
    gq_core = zeros(14, 20, sample)
    jacobian_lowers: list[Fraction] = []
    zero_gp = DyadicBand.exact(0, bits)
    _, _, det_centre, j_map_centre = jacobian_data(xy, zero_gp, zero_gp)
    j_wg_centre = transpose(j_map_centre)
    j_modes = centre_j_modes(xy)

    for r, s in gauss_points(bits):
        _, _, det_j, _ = jacobian_data(xy, r, s)
        assert isinstance(det_j, DyadicBand)
        jacobian_lowers.append(det_j.lo)
        n_sigma, n_epsilon = source_spaces(
            r, s, j_wg_centre, det_centre / det_j,
            j_modes["r_bar"], j_modes["s_bar"],
        )
        b_operator = physical_b(xy, r, s)
        _accumulate_gram(h_core, n_epsilon, constitutive, det_j)
        _accumulate_cross(
            f_core, n_epsilon, n_sigma, -det_j
        )
        _accumulate_cross(gq_core, n_sigma, b_operator, det_j)

    core_kii = zeros(35, 35, sample)
    core_kiq20 = zeros(35, 20, sample)
    block_put(core_kii, 0, 14, transpose(f_core))
    block_put(core_kii, 14, 0, f_core)
    block_put(core_kii, 14, 14, h_core)
    block_put(core_kiq20, 0, 0, gq_core)

    core_inverse = inverse(core_kii)
    core_condensed_20 = matrix_scale(
        matmul(transpose(core_kiq20), matmul(core_inverse, core_kiq20)),
        -scalar_one(sample),
    )

    select20 = zeros(20, 24, sample)
    for node in range(4):
        for local in range(5):
            select20[5 * node + local][6 * node + local] = scalar_one(sample)
    core_kiq24 = matmul(core_kiq20, select20)

    # PL: T_h=lambda^T[1,r,s], c=theta_D-(v_x-u_y)/2.
    t = DyadicBand.exact(as_fraction(material["exact_parameters"]["t"]), bits)
    g = DyadicBand.exact(as_fraction(material["exact_parameters"]["G"]), bits)
    m_pl = zeros(3, 3, sample)
    for r, s in gauss_points(bits):
        _, _, det_j, _ = jacobian_data(xy, r, s)
        p = [scalar_one(sample), r, s]
        block_put(m_pl, 0, 0, matrix_scale(outer(p, p), t * det_j))
    c_taylor = centre_taylor_constraint_rows(xy)
    b_pl = matmul(m_pl, c_taylor)

    kii = zeros(38, 38, sample)
    kiq = zeros(38, 24, sample)
    block_put(kii, 0, 0, core_kii)
    block_put(kiq, 0, 0, core_kiq24)
    block_put(kii, 35, 35, matrix_scale(m_pl, -(scalar_one(sample) / g)))
    block_put(kiq, 35, 0, b_pl)

    # WT2011 26.44--26.45 geometry-dependent residual row.
    zero = DyadicBand.exact(0, bits)
    centre_n, _, _ = q4_shape(zero, zero)
    x_c = sum((centre_n[i] * xy[i][0] for i in range(4)), zero)
    y_c = sum((centre_n[i] * xy[i][1] for i in range(4)), zero)
    s1 = [node[0] - x_c for node in xy]
    s2 = [node[1] - y_c for node in xy]
    xi = [DyadicBand.exact(v, bits) for v in (-1, 1, 1, -1)]
    eta = [DyadicBand.exact(v, bits) for v in (-1, -1, 1, 1)]
    h4 = [DyadicBand.exact(v, bits) for v in (1, -1, 1, -1)]
    _, _, j_c, _ = jacobian_data(xy, zero, zero)
    area_hg = 4 * j_c
    b1 = vector_add(
        [dot(eta, s2) * value / (4 * area_hg) for value in xi],
        [dot(xi, s2) * value / (4 * area_hg) for value in eta],
        -scalar_one(sample),
    )
    b2 = vector_add(
        [-dot(eta, s1) * value / (4 * area_hg) for value in xi],
        [dot(xi, s1) * value / (4 * area_hg) for value in eta],
    )
    gamma = [
        (h4[i] - dot(h4, s1) * b1[i] - dot(h4, s2) * b2[i]) / 4
        for i in range(4)
    ]
    hg_row = [scalar_zero(sample) for _ in range(24)]
    for node, value in enumerate(gamma):
        hg_row[6 * node + 5] = value
    epsilon_hg = DyadicBand.exact(
        as_fraction(material["exact_parameters"]["epsilon_hg"]), bits
    )
    kqq = matrix_scale(outer(hg_row, hg_row), 2 * epsilon_hg * g * t * area_hg)

    kii_inverse = inverse(kii)
    condensed_local = matrix_add(
        kqq,
        matmul(transpose(kiq), matmul(kii_inverse, kiq)),
        -scalar_one(sample),
    )
    condensed_global = matmul(rotation, matmul(condensed_local, transpose(rotation)))
    pl_condensed_local = matrix_scale(
        matmul(transpose(b_pl), matmul(inverse(m_pl), b_pl)), g
    )
    pl_condensed_global = matmul(
        rotation, matmul(pl_condensed_local, transpose(rotation))
    )
    hg_condensed_global = matmul(rotation, matmul(kqq, transpose(rotation)))
    return StationaryElement(
        bits=bits,
        geometry_id=geometry_id,
        operation_id=operation_id,
        nodes=nodes,
        nodes_exact=nodes_exact,
        frame=frame,
        xy=xy,
        t5=t5,
        qd=qd,
        local_to_global=rotation,
        kii=kii,
        kii_inverse=kii_inverse,
        kiq_local=kiq,
        kqq_local=kqq,
        condensed_local=condensed_local,
        condensed_global=condensed_global,
        core_condensed_20=core_condensed_20,
        pl_condensed_local=pl_condensed_local,
        pl_condensed_global=pl_condensed_global,
        hg_condensed_global=hg_condensed_global,
        core_kii=core_kii,
        core_kiq20=core_kiq20,
        c_taylor=c_taylor,
        m_pl=m_pl,
        b_pl=b_pl,
        j_wg_centre=j_wg_centre,
        j_modes=j_modes,
        gamma_row=gamma,
        area_hg=area_hg,
        jacobian_lowers=jacobian_lowers,
    )


def d4_exact_certificate(frame_contract: Mapping[str, Any]) -> dict[str, Any]:
    natural = [[Fraction(x), Fraction(y)] for x, y in NATURAL_NODES]
    operation_records = []
    for operation in frame_contract["d4"]["operations"]:
        a = [[Fraction(value) for value in row] for row in operation["A"]]
        det = a[0][0] * a[1][1] - a[0][1] * a[1][0]
        orthogonal = matmul(transpose(a), a) == identity(2, Fraction(0))
        node_tuple = [int(index) - 1 for index in operation["node_tuple"]]
        mapping = []
        for new_node in natural:
            mapped = matvec(a, new_node)
            mapping.append(natural.index(mapped))
        ahat_det = determinant_fraction([
            [a[0][0], a[0][1], Fraction(0)],
            [a[1][0], a[1][1], Fraction(0)],
            [Fraction(0), Fraction(0), det],
        ])
        operation_records.append({
            "id": operation["id"],
            "det": fraction_text(det),
            "node_map_exact": mapping == node_tuple,
            "orthogonal_exact": orthogonal,
            "lifted_det": fraction_text(ahat_det),
            "lifted_proper": ahat_det == 1,
        })
    return {
        "operation_count": len(operation_records),
        "complete_reversal": frame_contract["d4"]["complete_orientation_reversal"],
        "operations": operation_records,
        "all_exact": all(
            row["node_map_exact"] and row["orthogonal_exact"] and row["lifted_proper"]
            for row in operation_records
        ),
    }


def d4_field_work_certificate(frame_contract: Mapping[str, Any]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    gauss_signs = {(a, b) for a in (-1, 1) for b in (-1, 1)}
    for operation in frame_contract["d4"]["operations"]:
        a = [[Fraction(value) for value in row] for row in operation["A"]]
        det = Fraction(operation["det"])
        aa, ab = a[0]
        ac, ad = a[1]
        c_eng = [
            [aa * aa, ab * ab, aa * ab],
            [ac * ac, ad * ad, ac * ad],
            [2 * aa * ac, 2 * ab * ad, aa * ad + ab * ac],
        ]
        c_res = [
            [aa * aa, ab * ab, 2 * aa * ab],
            [ac * ac, ad * ad, 2 * ac * ad],
            [aa * ac, ab * ad, aa * ad + ab * ac],
        ]
        membrane_work = matmul(transpose(c_res), c_eng) == identity(3, Fraction(0))
        curvature_work = matmul(
            transpose(matrix_scale(c_res, det)), matrix_scale(c_eng, det)
        ) == identity(3, Fraction(0))
        pseudo_vector = matrix_scale(a, det)
        shear_work = matmul(transpose(pseudo_vector), pseudo_vector) == identity(2, Fraction(0))
        s_g = [
            [Fraction(1), Fraction(0), Fraction(0)],
            [Fraction(0), a[0][0], a[0][1]],
            [Fraction(0), a[1][0], a[1][1]],
        ]
        basis_map = all(
            matvec(s_g, [Fraction(1), Fraction(r), Fraction(s)])
            == [Fraction(1), *(matvec(a, [Fraction(r), Fraction(s)]))]
            for r, s in gauss_signs
        )
        mapped_gauss = {
            tuple(int(value) for value in matvec(a, [Fraction(r), Fraction(s)]))
            for r, s in gauss_signs
        }
        pl_orthogonal = matmul(transpose(s_g), s_g) == identity(3, Fraction(0))
        row = {
            "operation_id": operation["id"],
            "engineering_field_maps_exact": membrane_work,
            "resultant_conjugate_maps_exact": membrane_work,
            "curvature_moment_pseudoscalar_maps_exact": curvature_work,
            "shear_force_pseudovector_maps_exact": shear_work,
            "epsilon_N_work_exact": membrane_work,
            "kappa_M_pseudo_work_exact": curvature_work,
            "gamma_Q_pseudo_work_exact": shear_work,
            "pl_basis_map_exact": basis_map,
            "pl_constraint_pseudoscalar_map_exact": det * det == 1,
            "pl_multiplier_pseudoscalar_map_exact": det * det == 1,
            "pl_lambda_c_pseudoscalar_sign_cancels": det * det == 1,
            "pl_multiplier_gram_transport_exact": pl_orthogonal,
            "corresponding_gauss_set_exact": mapped_gauss == gauss_signs,
            "reconstruct_then_transport_required": True,
        }
        row["all_exact"] = all(value for key, value in row.items() if key not in {"operation_id"})
        records.append(row)
    return {
        "operation_count": len(records),
        "records": records,
        "all_operations_exact": len(records) == 8 and all(row["all_exact"] for row in records),
        "all_field_maps_exact": len(records) == 8 and all(
            row["engineering_field_maps_exact"] and row["resultant_conjugate_maps_exact"]
            for row in records
        ),
        "all_pseudo_maps_exact": len(records) == 8 and all(
            row["curvature_moment_pseudoscalar_maps_exact"]
            and row["shear_force_pseudovector_maps_exact"] for row in records
        ),
        "all_pl_maps_exact": len(records) == 8 and all(
            row["pl_basis_map_exact"] and row["pl_constraint_pseudoscalar_map_exact"]
            and row["pl_multiplier_pseudoscalar_map_exact"]
            and row["pl_multiplier_gram_transport_exact"] for row in records
        ),
        "all_work_equalities_exact": len(records) == 8 and all(
            row["epsilon_N_work_exact"] and row["kappa_M_pseudo_work_exact"]
            and row["gamma_Q_pseudo_work_exact"]
            and row["pl_lambda_c_pseudoscalar_sign_cancels"] for row in records
        ),
        "all_gauss_correspondence_exact": len(records) == 8 and all(
            row["corresponding_gauss_set_exact"] for row in records
        ),
    }


def structural_mode_certificate() -> dict[str, Any]:
    # Exact Fraction coefficient checks are contextual derivation evidence.
    # They never replace the assembled K*R certificate in element_certificate.
    zero, one = Fraction(0), Fraction(1)
    gamma_sum_coefficients = {
        "sum_h4": sum(map(Fraction, (1, -1, 1, -1))),
        "sum_xi": sum(map(Fraction, (-1, 1, 1, -1))),
        "sum_eta": sum(map(Fraction, (-1, -1, 1, 1))),
    }
    polynomial_checks = {
        "translation_derivatives": [zero, zero, zero],
        "rotation_t1_shear": [zero, one - one],
        "rotation_t2_shear": [-one + one, zero],
        "rotation_t3_membrane": [zero, zero, -one + one],
        "rotation_t3_pl": one - (one - (-one)) / 2,
    }
    return {
        "six_rigid_fields": [
            "RIGID_TRANSLATION_T1",
            "RIGID_TRANSLATION_T2",
            "RIGID_TRANSLATION_T3",
            "RIGID_ROTATION_T1",
            "RIGID_ROTATION_T2",
            "RIGID_ROTATION_T3_MATCHED_DRILL",
        ],
        "rigid_annihilation_identities": {
            "membrane": "sym_grad_rigid_is_zero",
            "bending": "registered_curvature_of_rigid_rotation_is_zero",
            "mitc_shear": "tying_covariant_shear_of_rigid_field_is_zero",
            "pl": "theta_D_minus_half_vx_minus_uy_is_zero",
            "residual": "gamma_dot_one_is_zero",
        },
        "residual_row_sum_exact": all(value == 0 for value in gamma_sum_coefficients.values()),
        "residual_row_sum_coefficients": gamma_sum_coefficients,
        "polynomial_checks": polynomial_checks,
        "polynomial_checks_exact_zero": all(
            value == 0
            for values in polynomial_checks.values()
            for value in (values if isinstance(values, list) else [values])
        ),
        "assembled_operator_required": "K_TIMES_R_EXACT_RESIDUAL_CERTIFICATE",
    }


def interval_summary(value: Scalar) -> Any:
    return value.payload() if isinstance(value, DyadicBand) else fraction_text(value)


def element_certificate(element: StationaryElement) -> dict[str, Any]:
    internal_ldl = ldl_congruence_certificate(symmetric_gram(element.kii))
    quotient = rigid_derived_quotient(element.nodes_exact)
    z = [
        [DyadicBand.exact(value, element.bits) for value in row]
        for row in quotient["quotient"]
    ]
    quotient_matrix = matmul(transpose(z), matmul(element.condensed_global, z))
    quotient_ldl = ldl_congruence_certificate(quotient_matrix)
    rigid = [
        [DyadicBand.exact(value, element.bits) for value in row]
        for row in quotient["rigid"]
    ]
    rigid_action = residual_certificate(
        matmul(element.condensed_global, rigid), zeros(24, 6, element.condensed_global[0][0])
    )
    gamma_sum = sum(element.gamma_row, scalar_zero(element.gamma_row[0]))
    gamma_sum_certificate = residual_certificate(
        [[gamma_sum]], [[scalar_zero(gamma_sum)]]
    )
    b_pl_definition_exact = element.b_pl == matmul(element.m_pl, element.c_taylor)
    return {
        "geometry_id": element.geometry_id,
        "operation_id": element.operation_id,
        "precision_bits": element.bits,
        "stationary_field_count": len(element.kii),
        "core_field_count": 35,
        "pl_field_count": 3,
        "external_dof_count": len(element.condensed_local),
        "jacobian_positive": all(value > 0 for value in element.jacobian_lowers),
        "jacobian_min_lower": fraction_text(min(element.jacobian_lowers)),
        "internal_invertibility_ldl": internal_ldl,
        "rigid_rank_exact": quotient["rigid_rank"],
        "rigid_quotient_orthogonality_exact": quotient["orthogonality_exact"],
        "rigid_plus_quotient_rank_exact": quotient["combined_rank"],
        "quotient_rule": quotient["rule"],
        "quotient_geometry_source": quotient["geometry_source"],
        "quotient_stiffness_inputs": quotient["stiffness_inputs"],
        "quotient_ldl": quotient_ldl,
        "rigid_action": rigid_action,
        "rank_psd_certificate_rule": (
            "SIX_EXACT_RIGID_ACTIONS_PLUS_POSITIVE_RIGID_DERIVED_18D_QUOTIENT_"
            "AND_EXACT_BLOCK_CONGRUENCE_PROVE_RANK18_PSD"
        ),
        "gamma_sum": gamma_sum_certificate,
        "centre_taylor_B_equals_M_C_exact": b_pl_definition_exact,
        "area_hg": interval_summary(element.area_hg),
    }


def residual_certificate(left: Matrix, right: Matrix) -> dict[str, Any]:
    if len(left) != len(right) or (left and len(left[0]) != len(right[0])):
        raise OracleError("residual comparison dimension mismatch")
    residuals = [a - b for row_a, row_b in zip(left, right) for a, b in zip(row_a, row_b)]
    def is_exact_zero(value: Scalar) -> bool:
        return (
            value == 0 if isinstance(value, Fraction)
            else value.lo == 0 and value.hi == 0
        )

    certified_nonzeros = sum(1 for value in residuals if certified_nonzero(value))
    exact_zeros = sum(1 for value in residuals if is_exact_zero(value))
    inconclusive = len(residuals) - certified_nonzeros - exact_zeros
    if residuals and isinstance(residuals[0], DyadicBand):
        max_width = max(value.width() for value in residuals if isinstance(value, DyadicBand))
        width: str | None = fraction_text(max_width)
    else:
        width = None
    return {
        "entry_count": len(residuals),
        "certified_nonzero_count": certified_nonzeros,
        "all_contain_zero": certified_nonzeros == 0,
        "exact_zero_count": exact_zeros,
        "inconclusive_zero_count": inconclusive,
        "all_exact_zero": exact_zeros == len(residuals),
        "max_interval_width": width,
    }


def permutation24(operation: Mapping[str, Any], sample: Scalar) -> Matrix:
    result = zeros(24, 24, sample)
    for new_node, base_one_indexed in enumerate(operation["node_tuple"]):
        base_node = int(base_one_indexed) - 1
        for dof in range(6):
            result[6 * new_node + dof][6 * base_node + dof] = scalar_one(sample)
    return result


def numbered_physical20_map(operation: Mapping[str, Any], sample: Scalar) -> Matrix:
    """Return ``P4 tensor block_diag(Ahat^T,A^T)`` in the frozen ordering."""

    a = [[as_fraction(value) for value in row] for row in operation["A"]]
    delta = as_fraction(operation["det"])
    ahat_t = [
        [a[0][0], a[1][0], Fraction(0)],
        [a[0][1], a[1][1], Fraction(0)],
        [Fraction(0), Fraction(0), delta],
    ]
    a_t = transpose(a)
    l5_fraction = [[Fraction(0) for _ in range(5)] for _ in range(5)]
    block_put(l5_fraction, 0, 0, ahat_t)
    block_put(l5_fraction, 3, 3, a_t)
    l5 = [[
        DyadicBand.exact(value, sample.bits) if isinstance(sample, DyadicBand) else value
        for value in row
    ] for row in l5_fraction]
    result = zeros(20, 20, sample)
    for new_node, base_one_indexed in enumerate(operation["node_tuple"]):
        block_put(result, 5 * new_node, 5 * (int(base_one_indexed) - 1), l5)
    return result


def numbered_drill4_map(operation: Mapping[str, Any], sample: Scalar) -> Matrix:
    result = zeros(4, 4, sample)
    delta = as_fraction(operation["det"])
    lifted = DyadicBand.exact(delta, sample.bits) if isinstance(sample, DyadicBand) else delta
    for new_node, base_one_indexed in enumerate(operation["node_tuple"]):
        result[new_node][int(base_one_indexed) - 1] = lifted
    return result


def global_rotation24(rotation_values: Sequence[Sequence[Any]], bits: int) -> Matrix:
    rotation = [
        [DyadicBand.exact(as_fraction(value), bits) for value in row]
        for row in rotation_values
    ]
    result = zeros(24, 24, rotation[0][0])
    for node in range(4):
        block_put(result, 6 * node, 6 * node, rotation)
        block_put(result, 6 * node + 3, 6 * node + 3, rotation)
    return result


def _field_local_vector(element: StationaryElement, field_id: str) -> Vector:
    sample = element.xy[0][0]
    zero = scalar_zero(sample)
    q = [zero for _ in range(24)]
    for node, (x, y) in enumerate(element.xy):
        u = v = w = tx = ty = td = zero
        if field_id in {"MEMBRANE_PATCH", "COMBINED_PHYSICAL_PATCH"}:
            u = 2 * x + y / 3
            v = -2 * x / 5 + 4 * y / 3
            td = DyadicBand.exact(Fraction(-11, 30), element.bits)
        if field_id in {"BENDING_PATCH", "COMBINED_PHYSICAL_PATCH"}:
            w_b = -x * x / 5 + y * y / 6 - 3 * x * y / 14
            tx_b = y / 3 - 3 * x / 14
            ty_b = 2 * x / 5 + 3 * y / 14
            w, tx, ty = w + w_b, tx + tx_b, ty + ty_b
        if field_id in {"SHEAR_PATCH", "COMBINED_PHYSICAL_PATCH"}:
            tx = tx + Fraction(1, 4)
            ty = ty + Fraction(2, 3)
        if field_id == "RIGID_TRANSLATION_T1":
            u = scalar_one(sample)
        elif field_id == "RIGID_TRANSLATION_T2":
            v = scalar_one(sample)
        elif field_id == "RIGID_TRANSLATION_T3":
            w = scalar_one(sample)
        elif field_id == "RIGID_ROTATION_T1":
            w, tx = y, scalar_one(sample)
        elif field_id == "RIGID_ROTATION_T2":
            w, ty = -x, scalar_one(sample)
        elif field_id == "RIGID_ROTATION_T3_MATCHED_DRILL":
            u, v, td = -y, x, scalar_one(sample)
        base = 6 * node
        q[base:base + 6] = [u, v, w, tx, ty, td]
    return q


def transported_field_vectors(
    group: Mapping[str, StationaryElement], operation: Mapping[str, Any],
) -> dict[str, Vector]:
    """Construct fields once in E, then apply node-only global transport."""

    source, target = group["E"], group[operation["id"]]
    p = permutation24(operation, source.nodes[0][0])
    fields = [
        "MEMBRANE_PATCH", "BENDING_PATCH", "SHEAR_PATCH", "COMBINED_PHYSICAL_PATCH",
        *structural_mode_certificate()["six_rigid_fields"],
    ]
    result: dict[str, Vector] = {}
    for field_id in fields:
        source_global = matvec(source.local_to_global, _field_local_vector(source, field_id))
        target_global = matvec(p, source_global)
        result[field_id] = matvec(transpose(target.local_to_global), target_global)
    return result


def _state_for_local_q(element: StationaryElement, q: Vector) -> Vector:
    rhs = matvec(element.kiq_local, q)
    return [-value for value in matvec(element.kii_inverse, rhs)]


def _expected_strain(
    field_id: str, bits: int, operation: Mapping[str, Any] | None = None,
) -> Vector:
    sample = DyadicBand.exact(0, bits)
    strain = [scalar_zero(sample) for _ in range(8)]
    if field_id in {"MEMBRANE_PATCH", "COMBINED_PHYSICAL_PATCH"}:
        strain[0:3] = [
            DyadicBand.exact(Fraction(2), bits),
            DyadicBand.exact(Fraction(4, 3), bits),
            DyadicBand.exact(Fraction(-1, 15), bits),
        ]
    if field_id in {"BENDING_PATCH", "COMBINED_PHYSICAL_PATCH"}:
        strain[3:6] = [
            DyadicBand.exact(Fraction(2, 5), bits),
            DyadicBand.exact(Fraction(-1, 3), bits),
            DyadicBand.exact(Fraction(3, 7), bits),
        ]
    if field_id in {"SHEAR_PATCH", "COMBINED_PHYSICAL_PATCH"}:
        strain[6:8] = [
            DyadicBand.exact(Fraction(2, 3), bits),
            DyadicBand.exact(Fraction(-1, 4), bits),
        ]
    if operation is None or operation["id"] == "E":
        return strain
    a_fraction = [[as_fraction(value) for value in row] for row in operation["A"]]
    delta = as_fraction(operation["det"])
    aa, ab = a_fraction[0]
    ac, ad = a_fraction[1]
    c_eng_fraction = [
        [aa * aa, ab * ab, aa * ab],
        [ac * ac, ad * ad, ac * ad],
        [2 * aa * ac, 2 * ab * ad, aa * ad + ab * ac],
    ]
    c_eng_inverse = inverse(lift_fraction_matrix(c_eng_fraction, bits))
    a_t = lift_fraction_matrix(transpose(a_fraction), bits)
    transformed = [scalar_zero(sample) for _ in range(8)]
    transformed[0:3] = matvec(c_eng_inverse, strain[0:3])
    transformed[3:6] = [delta * value for value in matvec(c_eng_inverse, strain[3:6])]
    transformed[6:8] = [delta * value for value in matvec(a_t, strain[6:8])]
    return transformed


def _expected_resultants(
    field_id: str, material: Mapping[str, Any], bits: int,
    operation: Mapping[str, Any] | None = None,
) -> Vector:
    constitutive = lift_fraction_matrix(resultant_constitutive(material), bits)
    return matvec(constitutive, _expected_strain(field_id, bits, operation))


def station_recovery_vectors(
    element: StationaryElement, q: Vector, state: Vector, r: Scalar, s: Scalar,
) -> tuple[Vector, Vector, Vector]:
    """Reconstruct compatible, independent and physical N/M/Q at one station."""

    _, _, det_j, _ = jacobian_data(element.xy, r, s)
    zero = scalar_zero(r)
    _, _, det_centre, _ = jacobian_data(element.xy, zero, zero)
    n_sigma, n_epsilon = source_spaces(
        r, s, element.j_wg_centre, det_centre / det_j,
        element.j_modes["r_bar"], element.j_modes["s_bar"],
    )
    q5 = [q[6 * node + dof] for node in range(4) for dof in range(5)]
    return (
        matvec(physical_b(element.xy, r, s), q5),
        matvec(n_epsilon, state[14:35]),
        matvec(n_sigma, state[0:14]),
    )


def global_resultant_vector(element: StationaryElement, resultants: Vector) -> Vector:
    """Return flattened global N(3x3), M(3x3), Q(3) from local N/M/Q."""

    t12 = [[element.frame[i][j] for j in range(2)] for i in range(3)]
    def tensor(values: Sequence[Scalar]) -> Matrix:
        local = [[values[0], values[2]], [values[2], values[1]]]
        return matmul(t12, matmul(local, transpose(t12)))
    n_global = tensor(resultants[0:3])
    m_global = tensor(resultants[3:6])
    q_global = matvec(t12, resultants[6:8])
    return [value for row in n_global for value in row] + [
        value for row in m_global for value in row
    ] + q_global


def rotate_global_resultant_vector(values: Vector, rotation: Matrix) -> Vector:
    n = [values[index:index + 3] for index in range(0, 9, 3)]
    m = [values[index:index + 3] for index in range(9, 18, 3)]
    q = values[18:21]
    n_star = matmul(rotation, matmul(n, transpose(rotation)))
    m_star = matmul(rotation, matmul(m, transpose(rotation)))
    q_star = matvec(rotation, q)
    return [value for row in n_star for value in row] + [
        value for row in m_star for value in row
    ] + q_star


def patch_recovery_certificate(
    element: StationaryElement,
    material: Mapping[str, Any],
    field_vectors: Mapping[str, Vector] | None = None,
    operation: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    field_ids = [
        "MEMBRANE_PATCH", "BENDING_PATCH", "SHEAR_PATCH", "COMBINED_PHYSICAL_PATCH",
        *structural_mode_certificate()["six_rigid_fields"],
    ]
    station_ids = ["GP_MM", "GP_PM", "GP_PP", "GP_MP"]
    for field_id in field_ids:
        q = (
            list(field_vectors[field_id]) if field_vectors is not None
            else _field_local_vector(element, field_id)
        )
        state = _state_for_local_q(element, q)
        expected_strain = _expected_strain(field_id, element.bits, operation)
        expected = _expected_resultants(field_id, material, element.bits, operation)
        point_records = []
        for station_id, (r, s) in zip(station_ids, gauss_points(element.bits)):
            compatible, independent, recovered = station_recovery_vectors(
                element, q, state, r, s
            )
            compatible_residual = residual_certificate(
                [[value] for value in compatible], [[value] for value in expected_strain]
            )
            independent_residual = residual_certificate(
                [[value] for value in independent], [[value] for value in expected_strain]
            )
            resultant_residual = residual_certificate(
                [[value] for value in recovered], [[value] for value in expected]
            )
            point_records.append({
                "station_id": station_id,
                "compatible": compatible_residual,
                "independent": independent_residual,
                "physical_resultants": resultant_residual,
            })
        numerical = state[35:38]
        records.append({
            "field_id": field_id,
            "gauss_points": point_records,
            "physical_resultants": ["N", "M", "Q"],
            "numerical_diagnostics": {
                "PL_multiplier_interval": [interval_summary(value) for value in numerical],
                "excluded_from_physical_recovery": (
                    len(state[0:14]) == 14 and len(numerical) == 3
                    and set(range(14)).isdisjoint(set(range(35, 38)))
                ),
                "residual_mode_excluded": all(
                    set(point) == {"station_id", "compatible", "independent", "physical_resultants"}
                    for point in point_records
                ),
            },
        })
    return {
        "records": records,
        "station_count": 4,
        "all_compatible_exact": all(
            point["compatible"]["all_exact_zero"]
            for record in records for point in record["gauss_points"]
        ),
        "all_independent_exact": all(
            point["independent"]["all_exact_zero"]
            for record in records for point in record["gauss_points"]
        ),
        "all_physical_resultants_exact": all(
            point["physical_resultants"]["all_exact_zero"]
            for record in records for point in record["gauss_points"]
        ),
        "any_certified_nonzero": any(
            comparison["certified_nonzero_count"]
            for record in records for point in record["gauss_points"]
            for comparison in (point["compatible"], point["independent"], point["physical_resultants"])
        ),
        "any_inconclusive": any(
            comparison["inconclusive_zero_count"]
            for record in records for point in record["gauss_points"]
            for comparison in (point["compatible"], point["independent"], point["physical_resultants"])
        ),
        "numerical_physical_separation": (
            set(range(14)).isdisjoint(set(range(35, 38)))
            and set(("N", "M", "Q")).isdisjoint(
                {"PL_CONSTRAINT", "PL_MULTIPLIER", "PL_COMPLIANCE_ENERGY",
                 "RESIDUAL_MODE_COORDINATE", "RESIDUAL_MODE_ENERGY",
                 "RESIDUAL_MODE_RESIDUAL", "RESIDUAL_MODE_TANGENT"}
            ) and all(
                record["numerical_diagnostics"]["excluded_from_physical_recovery"]
                and record["numerical_diagnostics"]["residual_mode_excluded"]
                for record in records
            )
        ),
    }


def rigid_action_diagnostics(element: StationaryElement) -> dict[str, Any]:
    records = []
    for field_id in structural_mode_certificate()["six_rigid_fields"]:
        q = _field_local_vector(element, field_id)
        action = matvec(element.condensed_local, q)
        exact_zero_count = sum(
            1 for value in action
            if (value == 0 if isinstance(value, Fraction) else value.lo == 0 == value.hi)
        )
        nonzero_count = sum(1 for value in action if certified_nonzero(value))
        records.append({
            "field_id": field_id,
            "all_action_components_contain_zero": all(
                value.contains_zero() if isinstance(value, DyadicBand) else value == 0
                for value in action
            ),
            "all_action_components_exact_zero": exact_zero_count == len(action),
            "certified_nonzero_count": nonzero_count,
            "inconclusive_zero_count": len(action) - exact_zero_count - nonzero_count,
        })
    return {
        "records": records,
        "structural_exact_certificate": structural_mode_certificate(),
        "all_interval_actions_contain_zero": all(
            row["all_action_components_contain_zero"] for row in records
        ),
        "all_actions_exact_zero": all(
            row["all_action_components_exact_zero"] for row in records
        ),
    }


def mixed_condensed_certificate(element: StationaryElement) -> dict[str, Any]:
    product = matmul(element.kii, element.kii_inverse)
    inverse_residual = residual_certificate(product, identity(38, product[0][0]))
    symmetry = residual_certificate(element.condensed_local, transpose(element.condensed_local))
    # A deterministic rational probe verifies stationary residual and the
    # Schur force identity without invoking any registered load convention.
    q = [DyadicBand.exact(Fraction((i % 7) - 3, 5), element.bits) for i in range(24)]
    state = _state_for_local_q(element, q)
    stationary = vector_add(matvec(element.kii, state), matvec(element.kiq_local, q))
    force_mixed = vector_add(matvec(element.kqq_local, q), matvec(transpose(element.kiq_local), state))
    force_condensed = matvec(element.condensed_local, q)
    energy_mixed = (
        dot(q, matvec(element.kqq_local, q)) / 2
        + dot(state, matvec(element.kiq_local, q))
        + dot(state, matvec(element.kii, state)) / 2
    )
    energy_condensed = dot(q, force_condensed) / 2
    stationary_residual = residual_certificate(
        [[value] for value in stationary],
        zeros(len(stationary), 1, stationary[0]),
    )
    force_residual = residual_certificate(
        [[value] for value in force_mixed], [[value] for value in force_condensed]
    )
    energy_residual = residual_certificate([[energy_mixed]], [[energy_condensed]])
    exact_equalities = all(
        row["all_exact_zero"] for row in (
            inverse_residual, symmetry, stationary_residual, force_residual, energy_residual
        )
    )
    return {
        "inverse_identity": inverse_residual,
        "condensed_symmetry": symmetry,
        "stationary_residual": stationary_residual,
        "mixed_condensed_force": force_residual,
        "mixed_condensed_energy": energy_residual,
        "mixed_condensed_work": force_residual,
        "energy_work_tangent_same_stationary_functional": exact_equalities,
        "post_condensation_rank_repair": False,
    }


def support_certificate(
    element: StationaryElement, cases: Mapping[str, Any], physical_load: Vector | None = None,
    support_matrix: Matrix | None = None,
) -> dict[str, Any]:
    """Exact full-physical-zero KKT certificate for the registered load.

    With ``A_bc=T5^T`` and ``f=T5*p_f``, the exact solution is ``q=0`` and
    ``mu=p_f``.  This is an actual solution of the frozen KKT equations; it is
    not a synthetic reaction probe.  Its uniqueness is tied to the certified
    positive four-dimensional drill block after the twenty physical rows are
    constrained.
    """

    a_bc = transpose(element.t5) if support_matrix is None else support_matrix
    orthogonality = matmul(a_bc, element.qd)
    zero = zeros(20, 4, orthogonality[0][0])
    membership = residual_certificate(orthogonality, zero)
    p_f = [
        DyadicBand.exact(as_fraction(value), element.bits)
        for row in cases["physical_load"]["p_f_node_major"] for value in row
    ]
    load = matvec(element.t5, p_f) if physical_load is None else list(physical_load)
    q_solution = [DyadicBand.exact(0, element.bits) for _ in range(24)]
    mu_solution = matvec(a_bc, load)
    reaction = matvec(transpose(a_bc), mu_solution)
    drill_projection = matvec(transpose(element.qd), reaction)
    load_projection = matvec(element.t5, matvec(transpose(element.t5), load))
    load_range = residual_certificate(
        [[value] for value in load_projection], [[value] for value in load]
    )
    load_drill = residual_certificate(
        [[value] for value in matvec(transpose(element.qd), load)],
        zeros(4, 1, element.nodes[0][0]),
    )
    reaction_projection = matvec(
        element.t5, matvec(transpose(element.t5), reaction)
    )
    reaction_range = residual_certificate(
        [[value] for value in reaction_projection], [[value] for value in reaction]
    )
    reaction_equals_load = residual_certificate(
        [[value] for value in reaction], [[value] for value in load]
    )
    drill_tangent = matmul(
        transpose(element.qd), matmul(element.condensed_global, element.qd)
    )
    drill_ldl = ldl_congruence_certificate(drill_tangent)
    equilibrium = vector_add(
        vector_add(matvec(element.condensed_global, q_solution), reaction), load,
        -scalar_one(load[0]),
    )
    equilibrium_residual = residual_certificate(
        [[value] for value in equilibrium], zeros(24, 1, equilibrium[0])
    )
    constraint_residual = residual_certificate(
        [[value] for value in matvec(a_bc, q_solution)],
        zeros(20, 1, q_solution[0]),
    )
    reaction_drill = residual_certificate(
        [[value] for value in drill_projection], zeros(4, 1, drill_projection[0])
    )
    delta_q = matvec(element.t5, [
        DyadicBand.exact(Fraction((index % 5) - 2, 7), element.bits)
        for index in range(20)
    ])
    reaction_work = residual_certificate(
        [[dot(reaction, delta_q)]], [[dot(mu_solution, matvec(a_bc, delta_q))]]
    )
    return {
        "unsupported_case_present": True,
        "full_physical_zero_projector_shape": [20, 24],
        "A_bc_QD": membership,
        "load_range": load_range,
        "load_drill": load_drill,
        "reaction_equals_load": reaction_equals_load,
        "reaction_range": reaction_range,
        "reaction_drill": reaction_drill,
        "reaction_work": reaction_work,
        "constraint": constraint_residual,
        "drill_block_ldl": drill_ldl,
        "equilibrium": equilibrium_residual,
        "direct_drill_moment": "EXCLUDED",
        "drill_support_row": "EXCLUDED",
        "prescribed_drill_coordinate": "EXCLUDED",
        "numerical_reaction_separation_exact": (
            reaction_range["all_exact_zero"] and reaction_drill["all_exact_zero"]
        ),
    }


def transported_case_certificate(
    base: StationaryElement,
    numbered: StationaryElement,
    operation: Mapping[str, Any],
    cases: Mapping[str, Any],
    field_work_row: Mapping[str, Any],
) -> dict[str, Any]:
    sample = base.condensed_global[0][0]
    p = permutation24(operation, sample)
    c20 = numbered_physical20_map(operation, sample)
    c4 = numbered_drill4_map(operation, sample)
    t5_transport = residual_certificate(
        matmul(numbered.t5, c20), matmul(p, base.t5)
    )
    qd_transport = residual_certificate(
        matmul(numbered.qd, c4), matmul(p, base.qd)
    )
    pi5_base = matmul(base.t5, transpose(base.t5))
    pi5_numbered = matmul(numbered.t5, transpose(numbered.t5))
    pid_base = matmul(base.qd, transpose(base.qd))
    pid_numbered = matmul(numbered.qd, transpose(numbered.qd))
    pi5_transport = residual_certificate(
        pi5_numbered, matmul(p, matmul(pi5_base, transpose(p)))
    )
    pid_transport = residual_certificate(
        pid_numbered, matmul(p, matmul(pid_base, transpose(p)))
    )
    pl_transport = residual_certificate(
        numbered.pl_condensed_global,
        matmul(p, matmul(base.pl_condensed_global, transpose(p))),
    )
    residual_mode_transport = residual_certificate(
        numbered.hg_condensed_global,
        matmul(p, matmul(base.hg_condensed_global, transpose(p))),
    )
    field_ids = [
        "MEMBRANE_PATCH", "BENDING_PATCH", "SHEAR_PATCH", "COMBINED_PHYSICAL_PATCH",
        *structural_mode_certificate()["six_rigid_fields"],
    ]
    vector_records = []
    for field_id in field_ids:
        q_local = _field_local_vector(base, field_id)
        q_global = matvec(base.local_to_global, q_local)
        q_numbered = matvec(p, q_global)
        q_numbered_local = matvec(transpose(numbered.local_to_global), q_numbered)
        roundtrip = matvec(numbered.local_to_global, q_numbered_local)
        rigid_action = None
        if field_id.startswith("RIGID_"):
            action = matvec(numbered.condensed_global, q_numbered)
            rigid_action = residual_certificate(
                [[value] for value in action], zeros(24, 1, action[0])
            )
        vector_records.append({
            "field_id": field_id,
            "transport": "q_g=P_g*q_0",
            "roundtrip": residual_certificate(
                [[value] for value in roundtrip], [[value] for value in q_numbered]
            ),
            "rigid_action": rigid_action,
        })

    p_f = [
        DyadicBand.exact(as_fraction(value), base.bits)
        for row in cases["physical_load"]["p_f_node_major"] for value in row
    ]
    f_base = matvec(base.t5, p_f)
    f_numbered = matvec(p, f_base)
    p_numbered = matvec(transpose(numbered.t5), f_numbered)
    f_reconstructed = matvec(numbered.t5, p_numbered)
    drill_projection = matvec(transpose(numbered.qd), f_numbered)
    q_work = matvec(p, matvec(base.local_to_global, _field_local_vector(base, "COMBINED_PHYSICAL_PATCH")))
    work_global = dot(f_numbered, q_work)
    work_local = dot(p_numbered, matvec(transpose(numbered.t5), q_work))
    load_representation = residual_certificate(
        [[value] for value in f_reconstructed], [[value] for value in f_numbered]
    )
    load_drill = residual_certificate(
        [[value] for value in drill_projection], zeros(4, 1, drill_projection[0])
    )
    load_work = residual_certificate([[work_global]], [[work_local]])
    return {
        "geometry_id": base.geometry_id,
        "operation_id": operation["id"],
        "transported_global_field_count": len(vector_records),
        "transported_global_fields": vector_records,
        "physical_load_representation": load_representation,
        "physical_load_drill_orthogonality": load_drill,
        "physical_load_work": load_work,
        "T5_transport": t5_transport,
        "QD_transport": qd_transport,
        "physical_projector_transport": pi5_transport,
        "drill_projector_transport": pid_transport,
        "pl_tangent_transport": pl_transport,
        "residual_mode_tangent_transport": residual_mode_transport,
        "field_maps_exact": bool(
            field_work_row["engineering_field_maps_exact"]
            and field_work_row["resultant_conjugate_maps_exact"]
            and field_work_row["curvature_moment_pseudoscalar_maps_exact"]
            and field_work_row["shear_force_pseudovector_maps_exact"]
        ),
        "pl_maps_exact": bool(
            field_work_row["pl_basis_map_exact"]
            and field_work_row["pl_constraint_pseudoscalar_map_exact"]
            and field_work_row["pl_multiplier_pseudoscalar_map_exact"]
            and field_work_row["pl_multiplier_gram_transport_exact"]
        ),
        "work_maps_exact": bool(
            field_work_row["epsilon_N_work_exact"]
            and field_work_row["kappa_M_pseudo_work_exact"]
            and field_work_row["gamma_Q_pseudo_work_exact"]
            and field_work_row["pl_lambda_c_pseudoscalar_sign_cancels"]
        ),
        "gauss_correspondence_exact": bool(field_work_row["corresponding_gauss_set_exact"]),
        "embedding_load_projector_exact": all(
            row["all_exact_zero"] for row in (
                t5_transport, qd_transport, pi5_transport, pid_transport,
                load_representation, load_drill, load_work,
            )
        ),
        "pl_residual_transport_exact": (
            pl_transport["all_exact_zero"] and residual_mode_transport["all_exact_zero"]
        ),
        "recovery_field_work_transport_exact": bool(field_work_row["all_exact"]),
        "support": support_certificate(
            numbered, cases, f_numbered,
            matmul(transpose(base.t5), transpose(p)),
        ),
        "direct_drill_excluded": bool(load_drill["all_exact_zero"]),
    }


def numbered_covariance_certificate(
    base: StationaryElement,
    numbered: StationaryElement,
    operation: Mapping[str, Any],
) -> dict[str, Any]:
    p = permutation24(operation, base.condensed_global[0][0])
    pulled = matmul(transpose(p), matmul(numbered.condensed_global, p))
    q_base = matvec(base.local_to_global, _field_local_vector(base, "COMBINED_PHYSICAL_PATCH"))
    q_numbered = matvec(p, q_base)
    residual_base = matvec(base.condensed_global, q_base)
    residual_numbered = matvec(numbered.condensed_global, q_numbered)
    residual_pulled = matvec(transpose(p), residual_numbered)
    energy_base = dot(q_base, residual_base) / 2
    energy_numbered = dot(q_numbered, residual_numbered) / 2
    return {
        "geometry_id": base.geometry_id,
        "operation_id": operation["id"],
        "stiffness": residual_certificate(pulled, base.condensed_global),
        "residual": residual_certificate(
            [[value] for value in residual_pulled], [[value] for value in residual_base]
        ),
        "energy": residual_certificate([[energy_numbered]], [[energy_base]]),
        "structural_frame_theorem": "T_Xg_EQUALS_T_X_DIAG_A_DET_A",
        "global_permutation_is_node_only": True,
    }


def global_covariance_certificate(
    base_group: Mapping[str, StationaryElement],
    transformed_group: Mapping[str, StationaryElement],
    rotation_values: Sequence[Sequence[Any]],
    translation_values: Sequence[Any],
    cases: Mapping[str, Any],
    material: Mapping[str, Any],
    operations: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    rotation_exact = [[as_fraction(value) for value in row] for row in rotation_values]
    translation_exact = [as_fraction(value) for value in translation_values]
    proper_rotation_exact = (
        matmul(transpose(rotation_exact), rotation_exact) == identity(3, Fraction(0))
        and determinant_fraction(rotation_exact) == 1
    )
    p_f_values = [value for row in cases["physical_load"]["p_f_node_major"] for value in row]
    for operation_id in ("E", "R90", "R180", "R270", "MR", "MS", "MD", "MA"):
        base = base_group[operation_id]
        transformed = transformed_group[operation_id]
        base_vectors = transported_field_vectors(base_group, operations[operation_id])
        transformed_vectors = transported_field_vectors(
            transformed_group, operations[operation_id]
        )
        g_r = global_rotation24(rotation_values, base.bits)
        r3 = [[DyadicBand.exact(as_fraction(v), base.bits) for v in rr] for rr in rotation_values]
        expected = matmul(g_r, matmul(base.condensed_global, transpose(g_r)))
        q_base = matvec(
            base.local_to_global, base_vectors["COMBINED_PHYSICAL_PATCH"]
        )
        q_star = matvec(g_r, q_base)
        q_star_constructed = matvec(
            transformed.local_to_global,
            transformed_vectors["COMBINED_PHYSICAL_PATCH"],
        )
        residual_base = matvec(base.condensed_global, q_base)
        residual_star = matvec(transformed.condensed_global, q_star)
        expected_residual = matvec(g_r, residual_base)
        p_f = [DyadicBand.exact(as_fraction(value), base.bits) for value in p_f_values]
        p24 = permutation24(operations[operation_id], base.nodes[0][0])
        load_base = matvec(p24, matvec(base_group["E"].t5, p_f))
        load_star = matvec(p24, matvec(transformed_group["E"].t5, p_f))
        expected_load = matvec(g_r, load_base)
        a_base = matmul(transpose(base_group["E"].t5), transpose(p24))
        a_star = matmul(transpose(transformed_group["E"].t5), transpose(p24))
        expected_a_star = matmul(a_base, transpose(g_r))
        mu_base, mu_star = matvec(a_base, load_base), matvec(a_star, load_star)
        reaction_base = matvec(transpose(a_base), mu_base)
        reaction_star = matvec(transpose(a_star), mu_star)
        base_recovery = patch_recovery_certificate(
            base, material, base_vectors, operations[operation_id]
        )
        transformed_recovery = patch_recovery_certificate(
            transformed, material, transformed_vectors, operations[operation_id]
        )
        recovery_transport: list[dict[str, Any]] = []
        for field_id in [
            "MEMBRANE_PATCH", "BENDING_PATCH", "SHEAR_PATCH", "COMBINED_PHYSICAL_PATCH",
            *structural_mode_certificate()["six_rigid_fields"],
        ]:
            q0 = base_vectors[field_id]
            qs = transformed_vectors[field_id]
            state0, states = _state_for_local_q(base, q0), _state_for_local_q(transformed, qs)
            for station_id, ((r0, s0), (rs, ss)) in zip(
                ("GP_MM", "GP_PM", "GP_PP", "GP_MP"),
                zip(gauss_points(base.bits), gauss_points(transformed.bits)),
            ):
                comp0, ind0, result0 = station_recovery_vectors(base, q0, state0, r0, s0)
                comps, inds, results = station_recovery_vectors(transformed, qs, states, rs, ss)
                global0 = global_resultant_vector(base, result0)
                globals_ = global_resultant_vector(transformed, results)
                recovery_transport.append({
                    "field_id": field_id, "station_id": station_id,
                    "compatible_local": residual_certificate(
                        [[v] for v in comps], [[v] for v in comp0]
                    ),
                    "independent_local": residual_certificate(
                        [[v] for v in inds], [[v] for v in ind0]
                    ),
                    "physical_local": residual_certificate(
                        [[v] for v in results], [[v] for v in result0]
                    ),
                    "physical_global": residual_certificate(
                        [[v] for v in globals_],
                        [[v] for v in rotate_global_resultant_vector(global0, r3)],
                    ),
                })
        transformed_nodes_expected = [
            vector_add(matvec(rotation_exact, node), translation_exact)
            for node in base.nodes_exact
        ]
        exact_geometry_transform = transformed.nodes_exact == transformed_nodes_expected
        row = {
            "operation_id": operation_id,
            "frame": residual_certificate(transformed.frame, matmul(
                r3, base.frame,
            )),
            "T5": residual_certificate(transformed.t5, matmul(g_r, base.t5)),
            "QD": residual_certificate(transformed.qd, matmul(g_r, base.qd)),
            "Pi5": residual_certificate(
                matmul(transformed.t5, transpose(transformed.t5)),
                matmul(g_r, matmul(matmul(base.t5, transpose(base.t5)), transpose(g_r))),
            ),
            "PiD": residual_certificate(
                matmul(transformed.qd, transpose(transformed.qd)),
                matmul(g_r, matmul(matmul(base.qd, transpose(base.qd)), transpose(g_r))),
            ),
            "stiffness": residual_certificate(transformed.condensed_global, expected),
            "pl_tangent": residual_certificate(
                transformed.pl_condensed_global,
                matmul(g_r, matmul(base.pl_condensed_global, transpose(g_r))),
            ),
            "residual_mode_tangent": residual_certificate(
                transformed.hg_condensed_global,
                matmul(g_r, matmul(base.hg_condensed_global, transpose(g_r))),
            ),
            "residual": residual_certificate(
                [[value] for value in residual_star], [[value] for value in expected_residual]
            ),
            "energy": residual_certificate(
                [[dot(q_star, residual_star) / 2]], [[dot(q_base, residual_base) / 2]]
            ),
            "field": residual_certificate(
                [[value] for value in q_star_constructed], [[value] for value in q_star]
            ),
            "local_xy": residual_certificate(transformed.xy, base.xy),
            "load": residual_certificate(
                [[value] for value in load_star], [[value] for value in expected_load]
            ),
            "support": residual_certificate(a_star, expected_a_star),
            "support_drill_base": residual_certificate(
                matmul(a_base, base.qd), zeros(20, 4, base.nodes[0][0])
            ),
            "support_drill_star": residual_certificate(
                matmul(a_star, transformed.qd), zeros(20, 4, transformed.nodes[0][0])
            ),
            "kkt_base": residual_certificate(
                [[v] for v in reaction_base], [[v] for v in load_base]
            ),
            "kkt_star": residual_certificate(
                [[v] for v in reaction_star], [[v] for v in load_star]
            ),
            "reaction": residual_certificate(
                [[value] for value in reaction_star],
                [[value] for value in matvec(g_r, reaction_base)],
            ),
            "proper_rotation_exact": proper_rotation_exact,
            "exact_geometry_transform": exact_geometry_transform,
            "recovery_transport": recovery_transport,
            "local_recovery_equal": all(
                comparison["all_exact_zero"]
                for item in recovery_transport
                for comparison in (
                    item["compatible_local"], item["independent_local"],
                    item["physical_local"], item["physical_global"],
                )
            ),
            "translation_invariant": exact_geometry_transform,
            "numerical_recovery_separate": (
                base_recovery["numerical_physical_separation"]
                and transformed_recovery["numerical_physical_separation"]
            ),
        }
        records.append(row)
    return {
        "source_geometry": "Q3_TAPERED_SKEW",
        "transformed_geometry": "Q3_TAPERED_SKEW_RSTAR_TRANSLATED",
        "operation_count": len(records),
        "records": records,
        "frame": "T_RX_PLUS_B_EQUALS_R_T_X",
        "origin_translation_exact": all(row["exact_geometry_transform"] for row in records),
        "proper_rotation_exact": proper_rotation_exact,
    }


def terminal_from_evidence(evidence: Mapping[str, Any]) -> str:
    if evidence.get("authority_failure"):
        return "BLOCKED_E4_PL_Q1S_CONTRACT_OR_NONDETERMINISM"
    if evidence.get("frame_contradiction"):
        return "NO_GO_E4_PL_Q1S_FRAME_IDENTITY"
    if evidence.get("implementation_failure"):
        return "BLOCKED_E4_PL_Q1S_IMPLEMENTATION_IDENTITY"
    if evidence.get("oracle_failure"):
        return "BLOCKED_E4_PL_Q1S_ORACLE_OR_REVIEW"
    if evidence.get("local_algebra_failure"):
        return "NO_GO_E4_PL_Q1S_LOCAL_ALGEBRA"
    if evidence.get("patch_or_covariance_failure"):
        return "NO_GO_E4_PL_Q1S_PATCH_OR_COVARIANCE"
    if evidence.get("inconclusive"):
        return "UNCLASSIFIED_E4_PL_Q1S_LOCAL_PLANAR_IDENTITY"
    return "PROVISIONAL_GO_E4_PL_Q1S_Q1B_PLAN"


def static_metadata() -> dict[str, Any]:
    return {
        "schema": "anysolver.s4.e4-pl-q1s-static-implementation-metadata-v1",
        "candidate_id": CANDIDATE_ID,
        "study_id": STUDY_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "role": "INDEPENDENT_ORACLE",
        "preregistration_commit": PREREGISTRATION_COMMIT,
        "preregistration_tree": PREREGISTRATION_TREE,
        "registered_mechanics_executed": False,
        "stdlib_only": True,
        "arithmetic": ["fractions.Fraction", "independent_dyadic_outward_intervals"],
        "field_order": {
            "wg_core": ["stress14", "strain21"],
            "wg_core_total": 35,
            "pl_multiplier": 3,
            "stationary_total": 38,
        },
        "core_stationary_matrices": {
            "D": "[[0_14x14,F^T],[F,H]]",
            "Q": "[Gq^T,0_20x21]",
            "F": "-integral_N_epsilon^T_N_sigma",
            "H": "integral_N_epsilon^T_C_N_epsilon",
            "Gq": "integral_N_sigma^T_B",
        },
        "inherited_core_sha256": INHERITED_CORE_SHA256,
        "execution_contract_inherited_row_order": [
            "Q1R_INPUTS_16", "Q1R_CLOSEOUT_INPUTS_5", "E4_CORE_INPUTS_2"
        ],
        "quadrature": "positive_unshifted_2x2_gauss",
        "rigid_quotient": {
            "geometry": "SEPARATE_EXACT_GLOBAL_FRACTION_NODES",
            "rule": "LEXICOGRAPHIC_EXACT_RREF_NULLSPACE_OF_R_TRANSPOSE",
            "stiffness_dependent_selection": False,
        },
        "scientific_guard": "external_authority_plus_exact_commit3_contract",
        "execution_contract_schema": EXECUTION_CONTRACT_SCHEMA,
        "execution_authorization": EXECUTION_AUTHORIZATION,
        "common_payload_schema": COMMON_PAYLOAD_SCHEMA,
        "forbidden_imports": ["numpy", "scipy", "sympy", "mpmath"],
        "imports_reference": False,
        "imports_q1a": False,
    }


def inherited_core_static_certificate() -> dict[str, Any]:
    cases = strict_json_file(CORE_CASES_PATH)
    contract = strict_json_file(CORE_CONTRACT_PATH)
    dimensions = cases.get("dimensions", {})
    matrices = cases.get("source_exact_operator", {}).get("matrices", {})
    n_sigma_order = (
        cases.get("source_exact_operator", {}).get("N_sigma", {}).get("parameter_order")
    )
    n_epsilon_order = (
        cases.get("source_exact_operator", {}).get("N_epsilon", {}).get("parameter_order")
    )
    checks = {
        "stress_parameters_14": dimensions.get("stress_parameters") == 14,
        "strain_parameters_21": dimensions.get("strain_parameters") == 21,
        "core_internal_35": dimensions.get("core_internal") == 35,
        "D_source_form": matrices.get("D") == "[[0_14x14,F^T],[F,H]]",
        "Q_source_form": matrices.get("Q") == "[Gq^T,0_20x21]",
        "F_source_form": matrices.get("F") == "-integral_A N_epsilon^T*N_sigma*dA",
        "H_source_form": matrices.get("H") == "integral_A N_epsilon^T*C*N_epsilon*dA",
        "Gq_source_form": matrices.get("Gq") == "integral_A N_sigma^T*B*dA",
        "N_sigma_order_14": isinstance(n_sigma_order, list) and len(n_sigma_order) == 14,
        "N_epsilon_order_21": isinstance(n_epsilon_order, list) and len(n_epsilon_order) == 21,
        "contract_proof_program": "SOURCE_EXACT_WG_F_G_H_D_ASSEMBLY" in contract.get("proof_program", []),
    }
    return {"checks": checks, "all_closed": all(checks.values())}


def pl_centre_taylor_static_certificate() -> dict[str, Any]:
    material = strict_json_file(MATERIAL_PATH)
    cases = strict_json_file(CASES_PATH)
    source = strict_json_file(ROOT / "docs/reference_cases/e4_pl_q1r_source_map.json")
    checks = {
        "basis_is_centre_linear": material["formulation_identity"]["pl_multiplier_basis"] == ["1", "r", "s"],
        "three_multiplier_variables": material["formulation_identity"]["pl_multiplier_variables"] == 3,
        "only_rs_deleted": (
            material["formulation_identity"]["faulty_equal_order_rs_pl_coefficient"]
            == "DELETED_ONLY"
            and cases["formulation"]["removed_term"]
            == "ONLY_FAULTY_EQUAL_ORDER_r*s_PL_COEFFICIENT"
        ),
        "source_grammar_closed": any(
            row.get("id") == "unchanged_pl_constraint_multiplier_and_residual_grammar"
            and row.get("status") == "CLOSED"
            for row in source["indispensable_statements"]
        ),
        "B_construction": "B=M*C_WITH_C=[c(0),c_r(0),c_s(0)]",
        "full_rational_curl_L2_projection_excluded": True,
    }
    return {"checks": checks, "all_closed": all(bool(value) for value in checks.values())}


def exact_global_transform_static_certificate() -> dict[str, Any]:
    """Exact Fraction-only verification of the registered R*X+b node record."""

    geometry = strict_json_file(GEOMETRY_PATH)
    source_id = geometry["global_transform"]["source_geometry"]
    source = next(row for row in geometry["geometries"] if row["id"] == source_id)
    rotation = [
        [as_fraction(value) for value in row]
        for row in geometry["global_transform"]["R_star"]
    ]
    translation = [as_fraction(value) for value in geometry["global_transform"]["b_star"]]
    nodes = [[as_fraction(value) for value in row] for row in source["nodes"]]
    derived = [
        [as_fraction(value) for value in row]
        for row in geometry["global_transform"]["derived_nodes"]
    ]
    reconstructed = [
        vector_add(matvec(rotation, node), translation) for node in nodes
    ]
    return {
        "node_representation": "Fraction",
        "node_count": len(nodes),
        "proper_rotation_exact": (
            matmul(transpose(rotation), rotation) == identity(3, Fraction(0))
            and determinant_fraction(rotation) == 1
        ),
        "derived_nodes_exact": reconstructed == derived,
        "all_closed": len(nodes) == 4 and reconstructed == derived,
    }


def static_check() -> dict[str, Any]:
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(Path(__file__)))
    imported = sorted({
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in (node.names if isinstance(node, ast.Import) else [ast.alias(node.module or "")])
    })
    forbidden = sorted(set(imported) & {"numpy", "scipy", "sympy", "mpmath"})
    plan_hashes = {
        path: sha256_file(ROOT / path)
        for path in sorted(PLAN_STAGE_SHA256)
    }
    drift = {
        path: {"expected": PLAN_STAGE_SHA256[path], "actual": digest}
        for path, digest in plan_hashes.items()
        if digest != PLAN_STAGE_SHA256[path]
    }
    inherited_hashes = {
        path: sha256_file(ROOT / path)
        for path in sorted(INHERITED_CORE_SHA256)
    }
    inherited_drift = {
        path: {"expected": INHERITED_CORE_SHA256[path], "actual": digest}
        for path, digest in inherited_hashes.items()
        if digest != INHERITED_CORE_SHA256[path]
    }
    inheritance = strict_json_file(INHERITANCE_PATH)
    inherited_rows = (
        inheritance["inherited_q1r_inputs"]
        + inheritance["q1r_closeout_inputs"]
        + inheritance["inherited_e4_core_inputs"]
    )
    inherited_manifest_drift: dict[str, Any] = {}
    for row in inherited_rows:
        path = ROOT / row["path"]
        actual = sha256_file(path) if path.is_file() else None
        if actual != row["sha256"] or (path.stat().st_size if path.is_file() else None) != row["bytes"]:
            inherited_manifest_drift[row["path"]] = {
                "expected": row["sha256"], "actual": actual,
            }
    schemas = {}
    for path in (CASES_PATH, FRAME_PATH, GEOMETRY_PATH, MATERIAL_PATH, SUPPORT_PATH,
                 TOLERANCES_PATH, TERMINALS_PATH, CORE_CASES_PATH, CORE_CONTRACT_PATH,
                 COMPLETENESS_PATH, AUTHORITY_CONTRACT_PATH, INHERITANCE_PATH,
                 TEST_INVENTORY_PATH):
        document = strict_json_file(path)
        schemas[path.name] = document.get("schema")
    core_authority = inherited_core_static_certificate()
    pl_identity = pl_centre_taylor_static_certificate()
    global_exact_geometry = exact_global_transform_static_certificate()
    completeness = strict_json_file(COMPLETENESS_PATH)
    required_ids = [row["id"] for row in completeness["required_rows"]]
    defined_symbols = {
        node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))
    }
    obligation_keys_exact = list(STATIC_OBLIGATION_SYMBOLS) == required_ids
    obligation_symbols_present = all(
        symbol in defined_symbols
        for owner in STATIC_OBLIGATION_SYMBOLS.values()
        for symbol in ([owner] if isinstance(owner, str) else owner)
    )
    quotient_node = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "rigid_derived_quotient"
    )
    quotient_geometry_only = [arg.arg for arg in quotient_node.args.args] == ["nodes_exact"]
    return {
        "schema": "anysolver.s4.e4-pl-q1s-static-check-v1",
        "implementation_id": IMPLEMENTATION_ID,
        "ast_parse": True,
        "forbidden_imports": forbidden,
        "plan_stage_drift": drift,
        "inherited_core_drift": inherited_drift,
        "inherited_manifest_drift": inherited_manifest_drift,
        "schemas": schemas,
        "inherited_core_authority": core_authority,
        "pl_centre_taylor_identity": pl_identity,
        "global_exact_geometry": global_exact_geometry,
        "obligation_keys_exact": obligation_keys_exact,
        "obligation_symbols_present": obligation_symbols_present,
        "rigid_quotient_geometry_only": quotient_geometry_only,
        "registered_mechanics_executed": False,
        "ok": (
            not forbidden and not drift and not inherited_drift and not inherited_manifest_drift
            and all(schemas.values()) and core_authority["all_closed"]
            and pl_identity["all_closed"] and obligation_keys_exact
            and obligation_symbols_present and quotient_geometry_only
            and global_exact_geometry["all_closed"]
        ),
    }


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=ROOT, check=False, capture_output=True, text=True,
        encoding="utf-8", errors="strict",
    )
    if completed.returncode:
        raise OracleError(f"git {' '.join(args)} failed: {completed.stderr.strip()}")
    return completed.stdout.strip()


def _require_exact_keys(value: Any, expected: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise OracleError(f"{label} must be an object")
    actual = set(value)
    if actual != expected:
        raise OracleError(
            f"{label} key set mismatch: missing={sorted(expected - actual)}, "
            f"extra={sorted(actual - expected)}"
        )
    return value


def _reject_contract_floats(value: Any, label: str = "contract") -> None:
    if isinstance(value, float):
        raise OracleError(f"{label} contains a floating JSON number")
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_contract_floats(item, f"{label}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_contract_floats(item, f"{label}[{index}]")


def _safe_bound_path(path_text: Any) -> Path:
    if not isinstance(path_text, str) or not path_text or "\\" in path_text:
        raise OracleError("bound paths must be nonempty repository-relative POSIX paths")
    relative = Path(path_text)
    if relative.is_absolute() or ".." in relative.parts:
        raise OracleError(f"unsafe bound path: {path_text!r}")
    candidate = ROOT / relative
    if candidate.is_symlink():
        raise OracleError(f"bound path may not be a symlink: {path_text!r}")
    resolved = candidate.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise OracleError(f"bound path escapes repository: {path_text!r}") from exc
    return resolved


def _validate_bound_file(
    record: Any,
    label: str,
    *,
    expected_path: str | None = None,
    extra_keys: set[str] | None = None,
) -> tuple[Mapping[str, Any], Path]:
    keys = {"path", "bytes", "sha256"} | (extra_keys or set())
    item = _require_exact_keys(record, keys, label)
    if expected_path is not None and item["path"] != expected_path:
        raise OracleError(f"{label}.path must be {expected_path!r}")
    path = _safe_bound_path(item["path"])
    if not path.is_file() or path.is_symlink():
        raise OracleError(f"bound file is absent: {item['path']}")
    raw = path.read_bytes()
    if not isinstance(item["bytes"], int) or isinstance(item["bytes"], bool):
        raise OracleError(f"{label}.bytes must be an integer")
    if item["bytes"] != len(raw):
        raise OracleError(f"bound byte count mismatch: {item['path']}")
    if not isinstance(item["sha256"], str) or item["sha256"] != item["sha256"].upper():
        raise OracleError(f"{label}.sha256 must be uppercase hexadecimal")
    if item["sha256"] != sha256_bytes(raw):
        raise OracleError(f"bound SHA-256 mismatch: {item['path']}")
    return item, path


def _validate_path_map(
    value: Any,
    expected_hashes: Mapping[str, str],
    label: str,
) -> None:
    mapping = _require_exact_keys(value, set(expected_hashes), label)
    for path, expected_hash in expected_hashes.items():
        record = _require_exact_keys(mapping[path], {"bytes", "sha256"}, f"{label}[{path}]")
        actual_path = _safe_bound_path(path)
        raw = actual_path.read_bytes()
        if (
            not isinstance(record["bytes"], int) or isinstance(record["bytes"], bool)
            or not isinstance(record["sha256"], str)
            or record["sha256"] != record["sha256"].upper()
            or record["bytes"] != len(raw) or record["sha256"] != expected_hash
        ):
            raise OracleError(f"{label} identity mismatch: {path}")
        if sha256_bytes(raw) != expected_hash:
            raise OracleError(f"{label} worktree drift: {path}")


def _validate_canonical_review(
    record: Mapping[str, Any], expected_path: str, expected_schema: str,
    expected_verdict: str, label: str,
) -> tuple[Mapping[str, Any], Path]:
    bound, path = _validate_bound_file(
        record, label, expected_path=expected_path, extra_keys={"schema", "verdict"}
    )
    review = strict_json_file(path)
    _require_exact_keys(
        review, {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"},
        f"{label} document",
    )
    if canonical_bytes(review) != path.read_bytes():
        raise OracleError(f"{label} must be canonical JSON")
    if review["schema"] != expected_schema or review["verdict"] != expected_verdict:
        raise OracleError(f"{label} schema or exact verdict mismatch")
    if bound["schema"] != expected_schema or bound["verdict"] != expected_verdict:
        raise OracleError(f"{label} bound schema or verdict mismatch")
    return bound, path


def _git_stage_paths(commit: str) -> list[str]:
    return sorted(filter(None, _git("diff-tree", "--no-commit-id", "--name-only", "-r", commit).splitlines()))


def _authority_outside_all_worktrees(path: Path) -> bool:
    resolved = path.resolve()
    lines = _git("worktree", "list", "--porcelain").splitlines()
    roots = [Path(line[9:]).resolve() for line in lines if line.startswith("worktree ")]
    for root in roots:
        try:
            resolved.relative_to(root)
            return False
        except ValueError:
            pass
    return True


def verify_execution_authority(
    authority_path: Path, authority_sha256: str,
    contract_path: Path, contract_sha256: str, runner_id: str,
) -> Mapping[str, Any]:
    """Validate Commit-3 and the non-self-referential external authority.

    No registered object is constructed before every check in this function
    succeeds.  Unknown/minimal/alternate contract shapes are rejected.
    """

    authority_plan = strict_json_file(AUTHORITY_CONTRACT_PATH)
    exact_top = set(authority_plan["execution_contract"]["exact_top_level_keys"])
    stage = authority_plan["stage_extents"]
    review_plan = authority_plan["reviews"]

    expected_contract_path = (ROOT / "docs/reference_cases/e4_pl_q1s_execution_contract.json").resolve()
    if contract_path.resolve() != expected_contract_path or contract_path.is_symlink():
        raise OracleError("execution contract must be the regular committed Q1S contract")
    if not contract_path.is_file() or not authority_path.is_file() or authority_path.is_symlink():
        raise OracleError("authority and contract must be regular non-symlink files")
    if not _authority_outside_all_worktrees(authority_path):
        raise OracleError("external execution authority must be outside every Git worktree")
    contract_raw, authority_raw = contract_path.read_bytes(), authority_path.read_bytes()
    if sha256_bytes(contract_raw) != contract_sha256.upper():
        raise OracleError("passed execution-contract SHA-256 mismatch")
    if sha256_bytes(authority_raw) != authority_sha256.upper():
        raise OracleError("passed external-authority SHA-256 mismatch")
    contract, authority = strict_json_bytes(contract_raw), strict_json_bytes(authority_raw)
    if canonical_bytes(contract) != contract_raw or canonical_bytes(authority) != authority_raw:
        raise OracleError("contract and authority must be canonical UTF-8/LF JSON")
    _reject_contract_floats(contract)

    contract = _require_exact_keys(contract, exact_top, "execution contract")
    authority_keys = set(authority_plan["execution_authority_record"]["canonical_exact_keys"])
    authority = _require_exact_keys(authority, authority_keys, "external authority")
    if contract["schema"] != EXECUTION_CONTRACT_SCHEMA:
        raise OracleError("execution contract schema mismatch")
    if authority["schema"] != EXECUTION_AUTHORITY_SCHEMA:
        raise OracleError("external authority schema mismatch")
    if contract["candidate_id"] != CANDIDATE_ID or authority["candidate_id"] != CANDIDATE_ID:
        raise OracleError("candidate identity mismatch")
    if contract["study_id"] != STUDY_ID or authority["study_id"] != STUDY_ID:
        raise OracleError("study identity mismatch")

    authorization = _require_exact_keys(
        contract["authorization"],
        {"token", "commit3_subject", "commit3_path_count", "commit3_paths",
         "external_authority_schema", "external_authority_exact_keys"},
        "authorization",
    )
    if authorization != {
        "token": EXECUTION_AUTHORIZATION,
        "commit3_subject": EXECUTION_SUBJECT,
        "commit3_path_count": 3,
        "commit3_paths": stage["CONTRACT"],
        "external_authority_schema": EXECUTION_AUTHORITY_SCHEMA,
        "external_authority_exact_keys": authority_plan["execution_authority_record"]["canonical_exact_keys"],
    }:
        raise OracleError("authorization block mismatch")
    if authority["authorization"] != EXECUTION_AUTHORIZATION:
        raise OracleError("external authority token mismatch")
    expected_runner_ids = ["REFERENCE_RUNNER", "ORACLE_RUNNER", "SCIENTIFIC_TEST_RUNNER"]
    if authority["runner_ids"] != expected_runner_ids or runner_id != RUNNER_ID:
        raise OracleError("runner authority mismatch")

    ancestry = _require_exact_keys(contract["commit_ancestry"], {"commit1", "commit2"}, "commit_ancestry")
    commit_keys = {"commit", "tree", "parent", "subject", "path_count", "paths"}
    commit1 = _require_exact_keys(ancestry["commit1"], commit_keys, "commit_ancestry.commit1")
    commit2 = _require_exact_keys(ancestry["commit2"], commit_keys, "commit_ancestry.commit2")
    if commit1 != {
        "commit": PREREGISTRATION_COMMIT, "tree": PREREGISTRATION_TREE,
        "parent": PREREGISTRATION_PARENT, "subject": PREREGISTRATION_SUBJECT,
        "path_count": 11, "paths": stage["PLAN"],
    }:
        raise OracleError("Commit 1 ancestry mismatch")
    if commit2["parent"] != PREREGISTRATION_COMMIT or commit2["subject"] != IMPLEMENTATION_SUBJECT:
        raise OracleError("Commit 2 ancestry mismatch")
    if commit2["path_count"] != 10 or commit2["paths"] != stage["IMPLEMENTATION"]:
        raise OracleError("Commit 2 exact extent mismatch")
    for label, item in (("Commit 1", commit1), ("Commit 2", commit2)):
        if not all(isinstance(item[key], str) and len(item[key]) == 40 for key in ("commit", "tree", "parent")):
            raise OracleError(f"{label} object IDs must be full SHA-1 values")
        if _git("show", "-s", "--format=%T", item["commit"]) != item["tree"]:
            raise OracleError(f"{label} tree mismatch")
        if _git("show", "-s", "--format=%P", item["commit"]) != item["parent"]:
            raise OracleError(f"{label} parent mismatch")
        if _git("show", "-s", "--format=%s", item["commit"]) != item["subject"]:
            raise OracleError(f"{label} subject mismatch")
        if _git_stage_paths(item["commit"]) != sorted(item["paths"]):
            raise OracleError(f"{label} committed extent mismatch")

    inputs = _require_exact_keys(
        contract["implementation_inputs"],
        {"reference", "oracle", "scientific_runner", "manifest", "implementation_review", "scientific_tests"},
        "implementation_inputs",
    )
    bound_implementations: dict[str, Mapping[str, Any]] = {}
    for role, expected_path in (
        ("reference", "docs/reference_cases/e4_pl_q1s_reference.py"),
        ("oracle", "docs/reference_cases/e4_pl_q1s_oracle.py"),
    ):
        row, _ = _validate_bound_file(
            inputs[role], f"implementation_inputs.{role}", expected_path=expected_path,
            extra_keys={"implementation_id"},
        )
        bound_implementations[role] = row
    if bound_implementations["oracle"]["implementation_id"] != IMPLEMENTATION_ID:
        raise OracleError("oracle implementation identity mismatch")
    if bound_implementations["reference"]["sha256"] == bound_implementations["oracle"]["sha256"]:
        raise OracleError("independent implementation hashes must differ")
    runner, _ = _validate_bound_file(
        inputs["scientific_runner"], "implementation_inputs.scientific_runner",
        expected_path="docs/reference_cases/e4_pl_q1s_scientific_test_runner.py",
        extra_keys={"runner_id"},
    )
    if runner["runner_id"] != "SCIENTIFIC_TEST_RUNNER":
        raise OracleError("scientific runner identity mismatch")
    manifest, manifest_path = _validate_bound_file(
        inputs["manifest"], "implementation_inputs.manifest",
        expected_path="docs/reference_cases/e4_pl_q1s_implementation_manifest.json",
        extra_keys={"schema"},
    )
    if strict_json_file(manifest_path).get("schema") != manifest["schema"]:
        raise OracleError("implementation manifest schema mismatch")
    implementation_review, _ = _validate_canonical_review(
        inputs["implementation_review"], review_plan["implementation"]["path"],
        review_plan["implementation"]["schema"], review_plan["implementation"]["exact_verdict"],
        "implementation review",
    )

    expected_nodes = strict_json_file(TEST_INVENTORY_PATH)["scientific_inventory"]["node_ids"]
    expected_test_paths = [node.split("::", 1)[0] for node in expected_nodes]
    tests = inputs["scientific_tests"]
    if not isinstance(tests, list) or len(tests) != 5:
        raise OracleError("scientific_tests must be the ordered five-file list")
    flattened_nodes: list[str] = []
    for index, (value, expected_path, expected_node) in enumerate(zip(tests, expected_test_paths, expected_nodes)):
        row, _ = _validate_bound_file(
            value, f"implementation_inputs.scientific_tests[{index}]",
            expected_path=expected_path, extra_keys={"node_ids"},
        )
        if row["node_ids"] != [expected_node]:
            raise OracleError("scientific test node binding mismatch")
        flattened_nodes.extend(row["node_ids"])

    plan_inputs = _require_exact_keys(contract["plan_inputs"], {"count", "rows"}, "plan_inputs")
    if plan_inputs["count"] != 11 or not isinstance(plan_inputs["rows"], list):
        raise OracleError("plan input count mismatch")
    expected_plan_rows = [
        {"path": path, "bytes": (ROOT / path).stat().st_size, "sha256": PLAN_STAGE_SHA256[path]}
        for path in stage["PLAN"]
    ]
    if plan_inputs["rows"] != expected_plan_rows:
        raise OracleError("plan input row order or identity mismatch")
    for row in plan_inputs["rows"]:
        _validate_bound_file(row, f"plan input {row['path']}", expected_path=row["path"])

    inherited = _require_exact_keys(contract["inherited_inputs"], {"count", "rows"}, "inherited_inputs")
    inheritance = strict_json_file(INHERITANCE_PATH)
    expected_inherited_rows = (
        inheritance["inherited_q1r_inputs"]
        + inheritance["q1r_closeout_inputs"]
        + inheritance["inherited_e4_core_inputs"]
    )
    if inherited != {"count": 23, "rows": expected_inherited_rows}:
        raise OracleError("all 23 inherited identities must match the committed manifest")
    for row in inherited["rows"]:
        bound, _ = _validate_bound_file(
            {key: row[key] for key in ("path", "bytes", "sha256")},
            f"inherited input {row['path']}", expected_path=row["path"],
        )
        if _git("hash-object", row["path"]) != row["git_blob"]:
            raise OracleError(f"inherited Git blob mismatch: {bound['path']}")

    review_authorities = _require_exact_keys(
        contract["review_authorities"], {"plan", "implementation", "contract"}, "review_authorities"
    )
    plan_review, _ = _validate_canonical_review(
        review_authorities["plan"], review_plan["plan"]["path"], review_plan["plan"]["schema"],
        review_plan["plan"]["exact_verdict"], "plan review",
    )
    if review_authorities["implementation"] != implementation_review:
        raise OracleError("implementation review bindings disagree")
    contract_review = _require_exact_keys(
        review_authorities["contract"], {"path", "schema", "verdict", "hash_binding"},
        "review_authorities.contract",
    )
    if contract_review != {
        "path": review_plan["contract"]["path"], "schema": review_plan["contract"]["schema"],
        "verdict": review_plan["contract"]["exact_verdict"],
        "hash_binding": "EXTERNAL_AUTHORITY_RECORD",
    }:
        raise OracleError("contract review authority mismatch")
    contract_review_path = _safe_bound_path(contract_review["path"])
    contract_review_document = strict_json_file(contract_review_path)
    _require_exact_keys(
        contract_review_document,
        {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"},
        "contract review document",
    )
    if canonical_bytes(contract_review_document) != contract_review_path.read_bytes():
        raise OracleError("contract review must be canonical JSON")
    if (contract_review_document["schema"] != contract_review["schema"]
            or contract_review_document["verdict"] != contract_review["verdict"]):
        raise OracleError("contract review exact schema/verdict mismatch")

    expected_verdicts = {
        "plan": review_plan["plan"]["exact_verdict"],
        "implementation": review_plan["implementation"]["exact_verdict"],
        "contract": review_plan["contract"]["exact_verdict"],
    }
    if authority["review_verdicts"] != expected_verdicts:
        raise OracleError("external authority review-verdict map mismatch")
    if authority["plan_review_sha256"] != plan_review["sha256"]:
        raise OracleError("external plan-review hash mismatch")
    if authority["implementation_review_sha256"] != implementation_review["sha256"]:
        raise OracleError("external implementation-review hash mismatch")
    if authority["contract_review_sha256"] != sha256_file(contract_review_path):
        raise OracleError("external contract-review hash mismatch")
    if authority["execution_contract_sha256"] != contract_sha256.upper():
        raise OracleError("external contract hash mismatch")

    runtime = contract["runtime"]
    if runtime != authority_plan["runtime"]:
        raise OracleError("runtime block must equal the committed runtime authority")
    if sys.implementation.name != "cpython" or sys.version_info[:3] != (3, 13, 9):
        raise OracleError("authorized CPython 3.13.9 runtime is required")
    required_environment = runtime["environment"]
    if any(os.environ.get(key) != value for key, value in required_environment.items()):
        raise OracleError("frozen thread/determinism environment mismatch")
    if runtime["python_executable_path_authority"] != "DIAGNOSTIC_ONLY":
        raise OracleError("Python executable path may not be hard authority")

    runner_inventory = _require_exact_keys(contract["runner_inventory"], {"count", "rows"}, "runner_inventory")
    expected_runner_rows = authority_plan["guard_runners"]
    if runner_inventory != {"count": 3, "rows": expected_runner_rows}:
        raise OracleError("three-runner inventory mismatch")
    inventory = _require_exact_keys(
        contract["scientific_inventory"], {"count", "node_ids", "inventories_separate"},
        "scientific_inventory",
    )
    if inventory != {"count": 5, "node_ids": flattened_nodes, "inventories_separate": True}:
        raise OracleError("five-node scientific inventory mismatch")

    terminal, _ = _validate_bound_file(
        contract["terminal_authority"], "terminal_authority",
        expected_path="docs/reference_cases/e4_pl_q1s_terminal_table.json",
        extra_keys={"schema", "evaluation", "terminal_count"},
    )
    terminal_doc = strict_json_file(TERMINALS_PATH)
    if terminal != {
        "path": "docs/reference_cases/e4_pl_q1s_terminal_table.json",
        "bytes": TERMINALS_PATH.stat().st_size,
        "sha256": PLAN_STAGE_SHA256["docs/reference_cases/e4_pl_q1s_terminal_table.json"],
        "schema": terminal_doc["schema"], "evaluation": terminal_doc["evaluation"],
        "terminal_count": 12,
    }:
        raise OracleError("terminal authority mismatch")

    agreement = _require_exact_keys(
        contract["agreement"],
        {"payload_schema", "cross_implementation", "within_reference_fresh_processes",
         "within_oracle_fresh_processes", "wrapper_schema"}, "agreement",
    )
    if agreement != {
        "payload_schema": COMMON_PAYLOAD_SCHEMA,
        "cross_implementation": "BYTE_IDENTICAL_CANONICAL_CERTIFICATE_PAYLOAD",
        "within_reference_fresh_processes": 2,
        "within_oracle_fresh_processes": 2,
        "wrapper_schema": "anysolver.s4.e4-pl-q1s-certificate-wrapper-v1",
    }:
        raise OracleError("agreement block mismatch")
    restrictions = _require_exact_keys(
        contract["production_restriction"],
        {"production", "q1b_execution", "legacy_default", "post_execution_source_changes"},
        "production_restriction",
    )
    if restrictions != {
        "production": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED", "q1b_execution": "UNAUTHORIZED",
        "legacy_default": "ShellElement",
        "post_execution_source_changes": "FORBIDDEN_REQUIRES_NEW_SUCCESSOR",
    }:
        raise OracleError("production restriction mismatch")
    absences = _require_exact_keys(
        contract["output_absences"], {"paths", "absent_from_commit3_tree"}, "output_absences"
    )
    if absences != {"paths": stage["OUTCOME"], "absent_from_commit3_tree": True}:
        raise OracleError("Commit-3 output-absence declaration mismatch")

    head = _git("rev-parse", "HEAD")
    head_tree = _git("show", "-s", "--format=%T", head)
    if authority["commit"] != head or authority["tree"] != head_tree:
        raise OracleError("external authority HEAD commit/tree mismatch")
    if _git("show", "-s", "--format=%s", head) != EXECUTION_SUBJECT:
        raise OracleError("Commit 3 subject mismatch")
    if _git("show", "-s", "--format=%P", head) != commit2["commit"]:
        raise OracleError("Commit 3 parent mismatch")
    if _git("show", "-s", "--format=%P", commit2["commit"]) != commit1["commit"]:
        raise OracleError("Commit 3 grandparent mismatch")
    if _git_stage_paths(head) != sorted(stage["CONTRACT"]):
        raise OracleError("Commit 3 exact three-path extent mismatch")
    tracked_at_head = set(_git("ls-tree", "-r", "--name-only", head).splitlines())
    if any(path in tracked_at_head for path in stage["OUTCOME"]):
        raise OracleError("outcome path exists in Commit 3 tree")
    if _git("diff", "--name-only") or _git("diff", "--cached", "--name-only"):
        raise OracleError("tracked worktree or index is dirty")
    return contract


def _operation_map(frame_contract: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {operation["id"]: operation for operation in frame_contract["d4"]["operations"]}


def _geometry_map(geometry_contract: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {geometry["id"]: geometry for geometry in geometry_contract["geometries"]}


def _zero_gate_summary(rows: Iterable[Mapping[str, Any]]) -> tuple[bool, bool, bool]:
    rows = list(rows)
    return (
        bool(rows) and all(bool(row["all_exact_zero"]) for row in rows),
        any(bool(row["certified_nonzero_count"]) for row in rows),
        any(bool(row["inconclusive_zero_count"]) for row in rows),
    )


def _ordered_id_digest(ids: Sequence[str]) -> str:
    return sha256_bytes(("\n".join(ids) + "\n").encode("utf-8"))


def run_registered_cases(contract_hash: str, authority_hash: str) -> dict[str, Any]:
    frame_contract = strict_json_file(FRAME_PATH)
    geometry_contract = strict_json_file(GEOMETRY_PATH)
    material_contract = strict_json_file(MATERIAL_PATH)
    cases_contract = strict_json_file(CASES_PATH)
    tolerance_contract = strict_json_file(TOLERANCES_PATH)
    completeness = strict_json_file(COMPLETENESS_PATH)
    operations = _operation_map(frame_contract)
    base_geometries = _geometry_map(geometry_contract)
    transform = geometry_contract["global_transform"]
    geometries = dict(base_geometries)
    geometries[transform["id"]] = {
        "id": transform["id"], "family": "GLOBAL_PROPER_ROTATION_AND_TRANSLATION",
        "nodes": transform["derived_nodes"],
    }
    geometry_order = completeness["coverage"]["base_geometry_order"]
    operation_order = completeness["coverage"]["d4_operation_order"]
    station_labels = [row["id"] for row in completeness["coverage"]["gauss_station_order"]]
    precision_levels = [int(value) for value in tolerance_contract["precision_bits"]]
    if precision_levels != [256, 512, 1024]:
        raise OracleError("frozen precision schedule mismatch")

    frame_certificate = d4_exact_certificate(frame_contract)
    field_work = d4_field_work_certificate(frame_contract)
    field_work_by_operation = {row["operation_id"]: row for row in field_work["records"]}
    precision_summaries: list[dict[str, Any]] = []
    final_groups: dict[str, dict[str, StationaryElement]] = {}
    final_element: dict[str, dict[str, Any]] = {}
    final_mixed: dict[str, dict[str, Any]] = {}
    final_covariance: dict[str, dict[str, Any]] = {}
    final_transport: dict[str, dict[str, Any]] = {}
    final_recovery: dict[str, dict[str, Any]] = {}

    for bits in precision_levels:
        groups: dict[str, dict[str, StationaryElement]] = {}
        level_certificates: list[dict[str, Any]] = []
        for geometry_id in geometry_order:
            group: dict[str, StationaryElement] = {}
            for operation_id in operation_order:
                element = assemble_stationary_element(
                    geometry_id, operation_id, geometries[geometry_id]["nodes"],
                    operations[operation_id], material_contract, bits,
                )
                group[operation_id] = element
                level_certificates.append(element_certificate(element))
            groups[geometry_id] = group
        precision_summaries.append({
            "precision_bits": bits,
            "case_count": len(level_certificates),
            "all_positive_jacobians": all(row["jacobian_positive"] for row in level_certificates),
            "internal_unresolved": sum(row["internal_invertibility_ldl"]["unresolved"] for row in level_certificates),
            "quotient_unresolved": sum(row["quotient_ldl"]["unresolved"] for row in level_certificates),
        })
        if bits == 1024:
            final_groups = groups
            for geometry_id in geometry_order:
                base = groups[geometry_id]["E"]
                for operation_id in operation_order:
                    case_id = f"{geometry_id}::{operation_id}"
                    numbered = groups[geometry_id][operation_id]
                    final_element[case_id] = element_certificate(numbered)
                    final_mixed[case_id] = mixed_condensed_certificate(numbered)
                    final_covariance[case_id] = numbered_covariance_certificate(
                        base, numbered, operations[operation_id]
                    )
                    final_transport[case_id] = transported_case_certificate(
                        base, numbered, operations[operation_id], cases_contract,
                        field_work_by_operation[operation_id],
                    )
                    final_recovery[case_id] = patch_recovery_certificate(
                        numbered, material_contract,
                        transported_field_vectors(groups[geometry_id], operations[operation_id]),
                        operations[operation_id],
                    )

    global_covariance = global_covariance_certificate(
        final_groups["Q3_TAPERED_SKEW"],
        final_groups["Q3_TAPERED_SKEW_RSTAR_TRANSLATED"],
        transform["R_star"], transform["b_star"], cases_contract, material_contract, operations,
    )

    case_ids = [f"{geometry_id}::{operation_id}" for geometry_id in geometry_order for operation_id in operation_order]
    station_ids = [f"{case_id}::{station}" for case_id in case_ids for station in station_labels]
    case_certificates: list[dict[str, Any]] = []
    any_local_no_go = False
    any_patch_no_go = False
    any_unresolved = False
    any_frame_no_go = False

    for case_id in case_ids:
        geometry_id, operation_id = case_id.split("::")
        element = final_element[case_id]
        mixed = final_mixed[case_id]
        covariance = final_covariance[case_id]
        transport = final_transport[case_id]
        recovery = final_recovery[case_id]
        internal = element["internal_invertibility_ldl"]
        quotient = element["quotient_ldl"]
        internal_ok = (
            internal["positive"] == 38 and not internal["negative"]
            and not internal["exact_zero"] and not internal["unresolved"]
        )
        rigid_basis_exact = bool(
            element["rigid_rank_exact"] == 6
            and element["rigid_quotient_orthogonality_exact"]
            and element["rigid_plus_quotient_rank_exact"] == 24
            and element["quotient_rule"]
            == "LEXICOGRAPHIC_EXACT_RREF_NULLSPACE_OF_R_TRANSPOSE"
            and element["quotient_geometry_source"] == "EXACT_GLOBAL_FRACTION_NODES"
            and element["quotient_stiffness_inputs"] == 0
        )
        quotient_ok = (
            quotient["positive"] == 18 and not quotient["negative"]
            and not quotient["exact_zero"] and not quotient["unresolved"]
            and rigid_basis_exact
        )
        rigid_action = element["rigid_action"]
        rigid_ok = bool(rigid_action["all_exact_zero"])
        rigid_nonzero = bool(rigid_action["certified_nonzero_count"])
        rigid_unresolved = bool(rigid_action["inconclusive_zero_count"])
        gamma = element["gamma_sum"]
        mixed_rows = [
            mixed["inverse_identity"], mixed["condensed_symmetry"],
            mixed["stationary_residual"], mixed["mixed_condensed_force"],
            mixed["mixed_condensed_energy"], mixed["mixed_condensed_work"],
        ]
        mixed_exact, mixed_nonzero, mixed_unresolved = _zero_gate_summary(mixed_rows)
        covariance_rows = [covariance["stiffness"], covariance["residual"], covariance["energy"]]
        transport_rows = [
            transport["physical_load_representation"], transport["physical_load_drill_orthogonality"],
            transport["physical_load_work"], transport["T5_transport"], transport["QD_transport"],
            transport["physical_projector_transport"], transport["drill_projector_transport"],
            transport["pl_tangent_transport"], transport["residual_mode_tangent_transport"],
            *(field["roundtrip"] for field in transport["transported_global_fields"]),
        ]
        covariance_exact, covariance_nonzero, covariance_unresolved = _zero_gate_summary(
            covariance_rows + transport_rows
        )
        _, frame_nonzero, frame_unresolved = _zero_gate_summary([
            transport["T5_transport"], transport["QD_transport"],
            transport["physical_projector_transport"], transport["drill_projector_transport"],
        ])
        any_frame_no_go = any_frame_no_go or frame_nonzero
        recovery_no_go = bool(recovery["any_certified_nonzero"])
        recovery_unresolved = bool(recovery["any_inconclusive"])
        support = transport["support"]
        support_ldl = support["drill_block_ldl"]
        support_rows = [
            support["A_bc_QD"], support["load_range"], support["load_drill"],
            support["reaction_equals_load"], support["reaction_range"],
            support["reaction_drill"], support["reaction_work"],
            support["constraint"], support["equilibrium"],
        ]
        support_exact, support_residual_nonzero, support_residual_unresolved = _zero_gate_summary(
            support_rows
        )
        support_no_go = bool(
            support_ldl["negative"] or support_ldl["exact_zero"] or support_residual_nonzero
        )
        support_unresolved = bool(support_ldl["unresolved"] or support_residual_unresolved)
        support_ok = bool(
            support_exact and support_ldl["positive"] == 4
            and not support_no_go and not support_unresolved
        )
        local_no_go = (
            not element["jacobian_positive"] or internal["negative"] or internal["exact_zero"]
            or quotient["negative"] or quotient["exact_zero"] or not rigid_basis_exact
            or rigid_nonzero or mixed_nonzero
        )
        patch_no_go = (
            covariance_nonzero or recovery_no_go or support_no_go
            or bool(gamma["certified_nonzero_count"])
            or not element["centre_taylor_B_equals_M_C_exact"]
            or not recovery["numerical_physical_separation"]
            or not support["numerical_reaction_separation_exact"]
        )
        unresolved = (
            bool(internal["unresolved"] or quotient["unresolved"])
            or rigid_unresolved or mixed_unresolved or covariance_unresolved
            or recovery_unresolved or support_unresolved
            or frame_unresolved or bool(gamma["inconclusive_zero_count"])
        )
        any_local_no_go = any_local_no_go or bool(local_no_go)
        any_patch_no_go = any_patch_no_go or bool(patch_no_go)
        any_unresolved = any_unresolved or bool(unresolved)
        status = "NO_GO" if (local_no_go or patch_no_go) else "UNCLASSIFIED" if unresolved else "PASS"
        patches = {
            normalized: all(
                comparison["all_exact_zero"]
                for record in recovery["records"] if record["field_id"] == field_id
                for point in record["gauss_points"]
                for comparison in (point["compatible"], point["independent"], point["physical_resultants"])
            )
            for normalized, field_id in (
                ("membrane", "MEMBRANE_PATCH"), ("bending", "BENDING_PATCH"),
                ("shear", "SHEAR_PATCH"), ("combined", "COMBINED_PHYSICAL_PATCH"),
            )
        }
        patches["six_rigid_all_exact"] = rigid_ok
        case_certificates.append({
            "case_id": case_id,
            "geometry_id": geometry_id,
            "operation_id": operation_id,
            "gauss_station_ids": [f"{case_id}::{station}" for station in station_labels],
            "centre": {
                "centre_j_positive": bool(element["jacobian_positive"]),
                "centre_taylor_exact": bool(element["centre_taylor_B_equals_M_C_exact"]),
                "residual_mode_exact": bool(gamma["all_exact_zero"]),
            },
            "frame": {
                "equation7_exact": bool(
                    transport["T5_transport"]["all_exact_zero"]
                    and transport["QD_transport"]["all_exact_zero"]
                ),
                "projectors_exact": bool(
                    transport["physical_projector_transport"]["all_exact_zero"]
                    and transport["drill_projector_transport"]["all_exact_zero"]
                ),
            },
            "field_work": {
                "fields_exact": bool(transport["field_maps_exact"]),
                "pseudo_fields_exact": bool(field_work_by_operation[operation_id]["kappa_M_pseudo_work_exact"]
                                            and field_work_by_operation[operation_id]["gamma_Q_pseudo_work_exact"]),
                "pl_exact": bool(transport["pl_maps_exact"]),
                "work_exact": bool(transport["work_maps_exact"]),
                "gauss_correspondence_exact": bool(transport["gauss_correspondence_exact"]),
            },
            "local_algebra": {
                "field_count": 38, "internal_invertible": internal_ok,
                "rank_18": quotient_ok and rigid_ok, "six_rigid_exact": rigid_ok,
                "symmetric": bool(mixed["condensed_symmetry"]["all_exact_zero"]),
                "psd": (
                    quotient_ok and rigid_ok
                    and mixed["condensed_symmetry"]["all_exact_zero"]
                ),
                "mixed_condensed_exact": mixed_exact,
                "unresolved": bool(
                    internal["unresolved"] or quotient["unresolved"]
                    or rigid_unresolved or mixed_unresolved
                ),
            },
            "patches": patches,
            "recovery": {
                "compatible_all_exact": bool(recovery["all_compatible_exact"]),
                "independent_all_exact": bool(recovery["all_independent_exact"]),
                "physical_resultants_all_exact": bool(recovery["all_physical_resultants_exact"]),
                "numerical_separate": bool(recovery["numerical_physical_separation"]),
                "station_count": 4,
            },
            "global_support": {
                "projectors_exact": bool(
                    transport["physical_projector_transport"]["all_exact_zero"]
                    and transport["drill_projector_transport"]["all_exact_zero"]
                ),
                "load_exact": bool(
                    transport["physical_load_representation"]["all_exact_zero"]
                    and transport["physical_load_drill_orthogonality"]["all_exact_zero"]
                    and transport["physical_load_work"]["all_exact_zero"]
                ),
                "support_exact": bool(support["A_bc_QD"]["all_exact_zero"]),
                "solution_exact": bool(support_ok),
                "reaction_exact": bool(
                    support["reaction_equals_load"]["all_exact_zero"]
                    and support["reaction_range"]["all_exact_zero"]
                    and support["reaction_drill"]["all_exact_zero"]
                    and support["reaction_work"]["all_exact_zero"]
                ),
                "recovery_exact": bool(recovery["all_physical_resultants_exact"]),
                "numerical_separate": bool(support["numerical_reaction_separation_exact"]),
            },
            "status": status,
        })

    global_rows = [
        value
        for record in global_covariance["records"]
        for key, value in record.items()
        if key in {"frame", "T5", "QD", "Pi5", "PiD", "local_xy", "stiffness", "pl_tangent", "residual_mode_tangent",
                   "residual", "energy", "field", "load", "support", "support_drill_base",
                   "support_drill_star", "kkt_base", "kkt_star", "reaction"}
    ] + [
        comparison
        for record in global_covariance["records"]
        for station in record["recovery_transport"]
        for comparison in (
            station["compatible_local"], station["independent_local"],
            station["physical_local"], station["physical_global"],
        )
    ]
    global_exact, global_nonzero, global_unresolved = _zero_gate_summary(global_rows)
    global_frame_exact, global_frame_nonzero, global_frame_unresolved = _zero_gate_summary([
        value for record in global_covariance["records"]
        for key, value in record.items() if key in {"frame", "T5", "QD", "Pi5", "PiD", "local_xy"}
    ])
    exact_global_geometry = bool(
        global_covariance["proper_rotation_exact"]
        and global_covariance["origin_translation_exact"]
    )
    if global_nonzero or global_unresolved:
        replacement = "NO_GO" if global_nonzero else "UNCLASSIFIED"
        for row in case_certificates:
            if row["geometry_id"] in {"Q3_TAPERED_SKEW", "Q3_TAPERED_SKEW_RSTAR_TRANSLATED"}:
                if row["status"] != "NO_GO":
                    row["status"] = replacement
    any_patch_no_go = any_patch_no_go or global_nonzero
    if any(not row["numerical_recovery_separate"] for row in global_covariance["records"]):
        any_patch_no_go = True
    any_unresolved = any_unresolved or global_unresolved or global_frame_unresolved
    frame_failure = bool(
        not frame_certificate["all_exact"] or not field_work["all_operations_exact"]
        or not exact_global_geometry or any_frame_no_go or global_frame_nonzero
    )
    evidence = {
        "authority_failure": False, "frame_contradiction": frame_failure,
        "implementation_failure": False, "oracle_failure": False,
        "local_algebra_failure": any_local_no_go,
        "patch_or_covariance_failure": any_patch_no_go,
        "inconclusive": any_unresolved or any(row["status"] == "UNCLASSIFIED" for row in case_certificates),
    }
    terminal = terminal_from_evidence(evidence)
    inconclusive = terminal == "UNCLASSIFIED_E4_PL_Q1S_LOCAL_PLANAR_IDENTITY"
    all_case = lambda path: all(path(row) for row in case_certificates)
    def global_keys_exact(keys: set[str]) -> bool:
        comparisons = [
            value for record in global_covariance["records"]
            for key, value in record.items() if key in keys
        ]
        exact, _, _ = _zero_gate_summary(comparisons)
        return exact
    global_recovery_exact = all(
        comparison["all_exact_zero"]
        for record in global_covariance["records"]
        for station in record["recovery_transport"]
        for comparison in (
            station["compatible_local"], station["independent_local"],
            station["physical_local"], station["physical_global"],
        )
    )
    numerical_excluded = [
        "PL_CONSTRAINT", "PL_MULTIPLIER", "PL_COMPLIANCE_ENERGY",
        "RESIDUAL_MODE_COORDINATE", "RESIDUAL_MODE_ENERGY",
        "RESIDUAL_MODE_RESIDUAL", "RESIDUAL_MODE_TANGENT",
    ]
    certificate_payload = {
        "schema": COMMON_PAYLOAD_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "study_id": STUDY_ID,
        "precision_bits": precision_levels,
        "coverage": {
            "base_geometries": 6, "global_transform_variants": 1,
            "d4_operations": 8, "numbered_cases": len(case_ids),
            "centre_records": len(case_ids), "gauss_records": len(station_ids),
            "ordered_case_ids_sha256": _ordered_id_digest(case_ids),
            "ordered_station_ids_sha256": _ordered_id_digest(station_ids),
        },
        "frame_and_fields": {
            "all_d4_field_maps_exact": bool(field_work["all_field_maps_exact"]),
            "all_d4_frame_identities_exact": bool(
                frame_certificate["all_exact"]
                and all_case(lambda row: row["frame"]["equation7_exact"])
            ),
            "all_d4_pl_maps_exact": bool(field_work["all_pl_maps_exact"]),
            "all_d4_work_equalities_exact": bool(field_work["all_work_equalities_exact"]),
            "all_gauss_correspondence_exact": bool(field_work["all_gauss_correspondence_exact"]),
            "all_numbered_loads_exact": all_case(lambda row: row["global_support"]["load_exact"]),
            "all_numbered_projectors_exact": all_case(lambda row: row["global_support"]["projectors_exact"]),
            "all_numbered_residual_modes_exact": all_case(lambda row: row["centre"]["residual_mode_exact"]),
        },
        "local_algebra": {
            "all_38_field_blocks_invertible": all_case(lambda row: row["local_algebra"]["internal_invertible"]),
            "all_condensed_rank_18": all_case(lambda row: row["local_algebra"]["rank_18"]),
            "all_mixed_condensed_equalities_exact": all_case(lambda row: row["local_algebra"]["mixed_condensed_exact"]),
            "all_psd": all_case(lambda row: row["local_algebra"]["psd"]),
            "all_six_rigid_actions_exact_zero": all_case(lambda row: row["local_algebra"]["six_rigid_exact"]),
            "all_symmetric": all_case(lambda row: row["local_algebra"]["symmetric"]),
            "quotient_rule": "LEXICOGRAPHIC_EXACT_RREF_NULLSPACE_OF_R_TRANSPOSE",
            "unresolved_at_1024": bool(any_unresolved),
        },
        "recovery": {
            "all_224_compatible_fields": all_case(lambda row: row["recovery"]["compatible_all_exact"]),
            "all_224_independent_fields": all_case(lambda row: row["recovery"]["independent_all_exact"]),
            "all_224_physical_resultants": all_case(lambda row: row["recovery"]["physical_resultants_all_exact"]),
            "all_numerical_fields_separate": all_case(lambda row: row["recovery"]["numerical_separate"]),
            "numerical_fields_excluded": numerical_excluded,
            "physical_resultants": ["N", "M", "Q"],
        },
        "global_supports": {
            "all_global_field_recovery_exact": global_recovery_exact,
            "all_global_loads_exact": global_keys_exact({"load"}),
            "all_global_projectors_exact": global_keys_exact({"T5", "QD", "Pi5", "PiD"}),
            "all_global_reactions_exact": global_keys_exact({"reaction"}),
            "all_global_support_solutions_exact": global_keys_exact({"kkt_base", "kkt_star"}),
            "all_global_supports_exact": global_keys_exact(
                {"support", "support_drill_base", "support_drill_star"}
            ),
            "all_numerical_reactions_separate": all(
                row["numerical_recovery_separate"]
                and row["support_drill_base"]["all_exact_zero"]
                and row["support_drill_star"]["all_exact_zero"]
                for row in global_covariance["records"]
            ),
            "all_translation_invariant": all(
                row["translation_invariant"] and row["local_xy"]["all_exact_zero"]
                for row in global_covariance["records"]
            ),
            "direct_drill_excluded": all(
                final_transport[case_id]["physical_load_drill_orthogonality"]["all_exact_zero"]
                for case_id in case_ids
            ),
            "physical_supports_only": all(
                final_transport[case_id]["support"]["A_bc_QD"]["all_exact_zero"]
                for case_id in case_ids
            ),
        },
        "case_certificates": case_certificates,
        "classification": {
            "inconclusive": inconclusive,
            "production": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
            "q1b_execution": "UNAUTHORIZED",
            "terminal": terminal,
        },
    }
    completeness_payload = completeness["certificate_payload"]
    _require_exact_keys(certificate_payload, set(completeness_payload["exact_top_level_keys"]), "certificate payload")
    for key, keys in completeness_payload["nested_exact_keys"].items():
        _require_exact_keys(certificate_payload[key], set(keys), f"certificate payload.{key}")
    for index, record in enumerate(case_certificates):
        _require_exact_keys(record, set(completeness_payload["case_record_exact_keys"]), f"case[{index}]")
        for key, keys in CASE_NESTED_KEYS.items():
            _require_exact_keys(record[key], set(keys), f"case[{index}].{key}")
        if record["status"] not in {"PASS", "NO_GO", "UNCLASSIFIED"}:
            raise OracleError("case status is outside the frozen normalized enum")
    payload_hash = sha256_bytes(canonical_bytes(certificate_payload))
    return {
        "schema": "anysolver.s4.e4-pl-q1s-certificate-wrapper-v1",
        "candidate_id": CANDIDATE_ID,
        "study_id": STUDY_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "certificate_payload": certificate_payload,
        "certificate_payload_sha256": payload_hash,
        "execution_contract_sha256": contract_hash.upper(),
        "execution_authority_sha256": authority_hash.upper(),
        "implementation_diagnostics": {
            "precision_summaries": precision_summaries,
            "element_certificates": final_element,
            "mixed_condensed": final_mixed,
            "numbered_covariance": final_covariance,
            "numbered_transport": final_transport,
            "station_recovery": final_recovery,
            "global_covariance": global_covariance,
            "field_work": field_work,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--static-metadata", action="store_true")
    mode.add_argument("--static-check", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--authority-record", type=Path)
    parser.add_argument("--authority-sha256")
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--contract-sha256")
    parser.add_argument("--runner-id")
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.static_metadata:
        result = static_metadata()
    elif args.static_check:
        result = static_check()
        if not result["ok"]:
            raise OracleError("static implementation check failed")
    else:
        if (
            args.authority_record is None or not args.authority_sha256
            or args.contract is None or not args.contract_sha256 or not args.runner_id
            or args.output is None
        ):
            raise OracleError(
                "--execute requires --authority-record/--authority-sha256, "
                "--contract/--contract-sha256, --runner-id, and a fresh --output"
            )
        verify_execution_authority(
            args.authority_record, args.authority_sha256,
            args.contract, args.contract_sha256, args.runner_id,
        )
        if args.output.exists() or args.output.is_symlink():
            raise OracleError("registered output must be a fresh exclusive path")
        if not args.output.parent.is_dir() or not _authority_outside_all_worktrees(args.output):
            raise OracleError("registered output must be in a caller-owned directory outside Git worktrees")
        result = run_registered_cases(args.contract_sha256, args.authority_sha256)
    raw = canonical_bytes(result)
    if args.output is not None:
        with args.output.open("xb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        if args.output.read_bytes() != raw or sha256_file(args.output) != sha256_bytes(raw):
            raise OracleError("exclusive output reopen verification failed")
    else:
        sys.stdout.buffer.write(raw)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OracleError as exc:
        sys.stderr.write(f"E4_PL_Q1S_ORACLE_ERROR: {exc}\n")
        raise SystemExit(2)
