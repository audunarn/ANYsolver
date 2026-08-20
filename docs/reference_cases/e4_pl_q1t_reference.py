"""Independent exact reference for the E4-PL-Q1T local qualification.

This module is intentionally self contained.  It imports no candidate, Q1A,
production, or oracle code.  Importing it performs no mechanics.  The only
pre-authority commands, ``--static-transcription`` and
``--toy-exact-backend``, validate committed input syntax and synthetic exact
algebra without assembling a registered case.  Scientific execution requires
a committed caller-bound contract and its SHA-256 on the command line.

The arithmetic kernel is a small multiquadratic field over ``Fraction`` plus
an independent dyadic outward-interval evaluator.  Registered 2 x 2 Gauss
stations and the planar source chart therefore remain exact; interval signs
are used only for ordered-field certificates (positive Jacobians and LDL
pivots), never to turn a residual into zero.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import pathlib
import subprocess
import sys
from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable, Iterator, Mapping, Sequence


CANDIDATE_ID = "candidate_e4_pl_q1t.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1"
STUDY_ID = "study_e4_pl_q1t.q1s_frozen_identity_exact_oracle_completion_v1"
IMPLEMENTATION_ID = "Q1T_REFERENCE_STDLIB_FIELD_ALG"
PLAN_COMMIT = "658619184d354401f55fc7a6640a4770d900ded7"
PLAN_TREE = "c4b9d5ef80779ba26912bbb2d53e5d547a47c629"
PLAN_SUBJECT = "docs: preregister E4 PL Q1T exact-oracle completion"
IMPLEMENTATION_SUBJECT = "docs: freeze E4 PL Q1T exact reference and oracle"
EXECUTION_SUBJECT = "docs: authorize E4 PL Q1T scientific execution"
EXECUTION_TOKEN = "AUTHORIZE_E4_PL_Q1T_SCIENTIFIC_EXECUTION"
PAYLOAD_SCHEMA = "e4_pl_q1t_common_certificate_payload_v1"
OUTPUT_SCHEMA = "anysolver.s4.e4-pl-q1t-reference-raw-v1"
AUTHORITY_SCHEMA = "anysolver.s4.e4-pl-q1t-execution-authority-v1"
CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1t-execution-contract-v1"
SOURCE_CORE_TRANSFORM_POLICY = "CENTRE_J_FOR_ALL_BASE_AND_VARYING_SEEDS_POINTWISE_J_FORBIDDEN"
PL_PROJECTION_POLICY = "CENTRE_TAYLOR_C0_CR_CS_B_EQUALS_M_C_RS_DELETED"

STATIC_OBLIGATION_SYMBOLS = {
    "CORE_001_COORDINATE_SPLIT": "_frame_embeddings",
    "CORE_002_CENTRE_J_AND_J0_OVER_J": "_centre_geometry_terms",
    "CORE_003_SOURCE_TRANSFORMS": ["_tensor_transform", "_source_mixed_fields"],
    "CORE_004_STRESS14": "_source_mixed_fields",
    "CORE_005_STRAIN21": "_source_mixed_fields",
    "CORE_006_COMPATIBLE_B_AND_MITC": [
        "_kinematic_membrane",
        "_kinematic_bending",
        "_kinematic_mitc_shear",
    ],
    "CORE_007_ACTUAL_35_FIELD_STATIONARY_SYSTEM": "assemble",
    "PL_001_CENTRE_TAYLOR_ONLY_RS_DELETED": "_drill_taylor_rows",
    "PL_002_MULTIPLIER_GRAM_AND_CONDENSATION": "assemble",
    "PL_003_ACTUAL_38_FIELD_SYSTEM": ["assemble", "_stationary_certificate"],
    "RES_001_GEOMETRY_DEPENDENT_RESIDUAL_MODE": ["_residual_row", "assemble"],
    "D4_001_ALL_EIGHT_ACTIONS": ["_operations", "_frame_static_certificate"],
    "D4_002_FIELD_AND_PSEUDO_MAPS": ["_field_transport_maps", "_covariance_certificate"],
    "D4_003_PL_MAPS": "_covariance_certificate",
    "D4_004_EXACT_WORK_CONJUGACY": "_covariance_certificate",
    "D4_005_EMBEDDING_LOAD_SUPPORT_MAPS": ["_covariance_certificate", "_boundary_certificate"],
    "REC_001_ACTUAL_224_STATION_PHYSICAL_RECOVERY": "_recovery_at_gauss",
    "REC_002_PATCH_EXPECTATIONS": ["_expected_strains", "_expected_resultants", "_patch_certificate"],
    "REC_003_NUMERICAL_SEPARATION": ["_recovery_certificate", "_boundary_certificate"],
    "GLOBAL_001_RSTAR_BSTAR_CORE_LOAD_PROJECTORS": "_global_covariance_certificate",
    "GLOBAL_002_SUPPORT_KKT_SOLUTION_REACTION": ["_boundary_certificate", "_global_covariance_certificate"],
    "GLOBAL_003_RECOVERY_AND_NUMERICAL_TRANSPORT": "_global_covariance_certificate",
    "RANK_001_RIGID_DERIVED_QUOTIENT_LDL": ["lexicographic_nullspace", "_rank_certificate"],
    "RANK_002_CLASSIFICATION": ["sign_certificate", "_rank_certificate", "execute"],
    "ARITH_001_EXACT_ZERO_ONLY": ["Alg", "DyadicInterval", "sign_certificate"],
}

ROOT = pathlib.Path(__file__).resolve().parents[2]
REFERENCE_PATH = pathlib.Path(__file__).resolve()
_EXECUTION_CAPABILITY = object()

PLAN_INPUTS = (
    "docs/agent_plans/S4_E4_PL_Q1T_EXACT_ORACLE_COMPLETION_PLAN.md",
    "docs/reference_cases/e4_pl_q1t_plan_review.json",
    "docs/reference_cases/e4_pl_q1t_baseline.json",
    "docs/reference_cases/e4_pl_q1t_inheritance_manifest.json",
    "docs/reference_cases/e4_pl_q1t_rejected_evidence_manifest.json",
    "docs/reference_cases/e4_pl_q1t_allowed_extent.json",
    "docs/reference_cases/e4_pl_q1t_environment.json",
    "docs/reference_cases/e4_pl_q1t_environment_builder.py",
    "docs/reference_cases/e4_pl_q1t_exact_backend_contract.json",
    "docs/reference_cases/e4_pl_q1t_certificate_schema.json",
    "docs/reference_cases/e4_pl_q1t_authority_contract.json",
    "docs/reference_cases/e4_pl_q1t_terminal_table.json",
    "docs/reference_cases/e4_pl_q1t_test_inventory.json",
    "tests/test_e4_pl_q1t_preregistration_authority.py",
)

MECHANICS_INPUTS = (
    "docs/reference_cases/e4_pl_q1r_frame_contract.json",
    "docs/reference_cases/e4_pl_q1r_geometry_contract.json",
    "docs/reference_cases/e4_pl_q1r_material_contract.json",
    "docs/reference_cases/e4_pl_q1r_support_contract.json",
    "docs/reference_cases/e4_pl_q1r_cases.json",
    "docs/reference_cases/e4_pl_q1r_tolerances.json",
)

JSON_INPUTS = tuple(path for path in PLAN_INPUTS if path.endswith(".json")) + MECHANICS_INPUTS

INHERITED_CORE_INPUTS = {
    "docs/reference_cases/e4_core_cases.json": {
        "bytes": 5435,
        "sha256": "FE08E59D9E01073E04251C52544EDF10C4CC86861EA8B98FC6CB1A645427FEF2",
    },
    "docs/reference_cases/e4_core_contract.json": {
        "bytes": 2284,
        "sha256": "8768ABDC5D77B5FCC1643AF69920EFEB83F27DDFBDE17525F06EE2B53A5C1678",
    },
}


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def strict_json_bytes(raw: bytes, *, require_canonical: bool = True) -> object:
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw:
        raise ValueError("JSON must be UTF-8 without BOM and LF-only")
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=_reject_constant,
    )
    if require_canonical and raw != canonical_bytes(value):
        raise ValueError("JSON is not canonical UTF-8/LF transport")
    return value


def load_json(path: pathlib.Path, *, require_canonical: bool = True) -> object:
    return strict_json_bytes(path.read_bytes(), require_canonical=require_canonical)


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def sha256_path(path: pathlib.Path) -> str:
    return sha256_bytes(path.read_bytes())


def F(value: object = 0) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, str):
        return Fraction(value)
    raise TypeError(f"cannot convert {type(value).__name__} to Fraction")


def fstr(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def _factor_square(value: Fraction) -> tuple[Fraction, Fraction]:
    """Return ``scale, radicand`` with sqrt(value)=scale*sqrt(radicand).

    The returned positive radicand is a square-free integer represented as a
    Fraction.  Registered inputs are small; trial division is deterministic
    and keeps the implementation independent of external algebra packages.
    """

    if value < 0:
        raise ValueError("square root of negative Fraction")
    if value == 0:
        return Fraction(0), Fraction(1)
    n, d = value.numerator, value.denominator
    combined = n * d
    outside = 1
    inside = 1
    p = 2
    while p * p <= combined:
        exponent = 0
        while combined % p == 0:
            combined //= p
            exponent += 1
        outside *= p ** (exponent // 2)
        if exponent % 2:
            inside *= p
        p += 1 if p == 2 else 2
    if combined > 1:
        inside *= combined
    return Fraction(outside, d), Fraction(inside)


@dataclass(frozen=True)
class Field:
    """An exact tower ``Q(sqrt(d0), sqrt(d1), ...)``.

    Radicand ``di`` is stored in the preceding subfield, so equation-7's
    nested normalizations remain exact rather than being replaced by floats.
    """

    radicands: tuple[tuple[Fraction, ...], ...]

    @classmethod
    def for_radicands(cls, values: Iterable[Fraction]) -> "Field":
        field = cls(())
        for value in values:
            field, _ = field.with_sqrt(field.rational(value))
        return field

    @property
    def dimension(self) -> int:
        return 1 << len(self.radicands)

    def rational(self, value: object = 0) -> "Alg":
        coeff = [Fraction(0) for _ in range(self.dimension)]
        coeff[0] = F(value)
        return Alg(self, tuple(coeff))

    def with_sqrt(self, value: "Alg") -> tuple["Field", "Alg"]:
        if value.field != self:
            raise TypeError("radicand belongs to a different tower")
        scale = Fraction(1)
        reduced = value
        if value.is_rational:
            scale, rad = _factor_square(value.coeff[0])
            if scale == 0:
                return self, self.rational()
            if rad == 1:
                return self, self.rational(scale)
            reduced = self.rational(rad)
        for index, stored in enumerate(self.radicands):
            padded = stored + (Fraction(0),) * (self.dimension - len(stored))
            if reduced.coeff == padded:
                coeff = [Fraction(0) for _ in range(self.dimension)]
                coeff[1 << index] = scale
                return self, Alg(self, tuple(coeff))
        if len(self.radicands) >= 5:
            raise ValueError("frozen Q1T exact field exceeds formal degree 32")
        new = Field(self.radicands + (reduced.coeff,))
        coeff = [Fraction(0) for _ in range(new.dimension)]
        coeff[1 << len(self.radicands)] = scale
        return new, Alg(new, tuple(coeff))

    def sqrt(self, value: Fraction | "Alg") -> "Alg":
        algebraic = value if isinstance(value, Alg) else self.rational(value)
        new, root = self.with_sqrt(algebraic)
        if new != self:
            raise ValueError("radicand absent from frozen exact tower")
        return root

    def subfield(self) -> "Field":
        if not self.radicands:
            raise ValueError("rational field has no proper subfield")
        return Field(self.radicands[:-1])


@dataclass(frozen=True)
class Alg:
    field: Field
    coeff: tuple[Fraction, ...]

    def __post_init__(self) -> None:
        if len(self.coeff) != self.field.dimension:
            raise ValueError("coefficient dimension does not match field")

    def _coerce(self, other: object) -> "Alg":
        if isinstance(other, Alg):
            if other.field != self.field:
                raise TypeError("cannot mix distinct exact fields")
            return other
        return self.field.rational(other)

    def lift(self, field: Field) -> "Alg":
        if field == self.field:
            return self
        if field.radicands[: len(self.field.radicands)] != self.field.radicands:
            raise TypeError("target is not an extension of this tower")
        return Alg(field, self.coeff + (Fraction(0),) * (field.dimension - len(self.coeff)))

    @property
    def is_zero(self) -> bool:
        return all(value == 0 for value in self.coeff)

    @property
    def is_rational(self) -> bool:
        return all(value == 0 for value in self.coeff[1:])

    def __add__(self, other: object) -> "Alg":
        rhs = self._coerce(other)
        return Alg(self.field, tuple(a + b for a, b in zip(self.coeff, rhs.coeff)))

    __radd__ = __add__

    def __neg__(self) -> "Alg":
        return Alg(self.field, tuple(-value for value in self.coeff))

    def __sub__(self, other: object) -> "Alg":
        return self + (-self._coerce(other))

    def __rsub__(self, other: object) -> "Alg":
        return self._coerce(other) - self

    def __mul__(self, other: object) -> "Alg":
        rhs = self._coerce(other)
        out = [Fraction(0) for _ in range(self.field.dimension)]

        def basis_product(left_mask: int, right_mask: int) -> dict[int, Fraction]:
            common = left_mask & right_mask
            if not common:
                return {left_mask ^ right_mask: Fraction(1)}
            bit = common.bit_length() - 1
            base_left = left_mask ^ (1 << bit)
            base_right = right_mask ^ (1 << bit)
            result: dict[int, Fraction] = {}
            radicand = self.field.radicands[bit]
            for rad_mask, rad_coeff in enumerate(radicand):
                if rad_coeff == 0:
                    continue
                for mask, factor in basis_product(base_left ^ rad_mask, base_right).items():
                    result[mask] = result.get(mask, Fraction(0)) + rad_coeff * factor
            return result

        for left_mask, left in enumerate(self.coeff):
            if left == 0:
                continue
            for right_mask, right in enumerate(rhs.coeff):
                if right == 0:
                    continue
                for mask, factor in basis_product(left_mask, right_mask).items():
                    out[mask] += left * right * factor
        return Alg(self.field, tuple(out))

    __rmul__ = __mul__

    def inverse(self) -> "Alg":
        if self.is_zero:
            raise ZeroDivisionError("inverse of exact zero")
        coeff = list(self.coeff)

        def recursive(values: list[Fraction], field: Field) -> list[Fraction]:
            if not field.radicands:
                if values[0] == 0:
                    raise ZeroDivisionError("algebraic norm vanished")
                return [1 / values[0]]
            half = len(values) // 2
            a, b = values[:half], values[half:]
            subfield = field.subfield()
            aa = Alg(subfield, tuple(a)) * Alg(subfield, tuple(a))
            bb = Alg(subfield, tuple(b)) * Alg(subfield, tuple(b))
            radicand = Alg(subfield, field.radicands[-1])
            norm_alg = aa - radicand * bb
            inv_norm = recursive(list(norm_alg.coeff), subfield)
            invn = Alg(subfield, tuple(inv_norm))
            left = list((Alg(subfield, tuple(a)) * invn).coeff)
            right = list((-Alg(subfield, tuple(b)) * invn).coeff)
            return left + right

        return Alg(self.field, tuple(recursive(coeff, self.field)))

    def __truediv__(self, other: object) -> "Alg":
        return self * self._coerce(other).inverse()

    def __rtruediv__(self, other: object) -> "Alg":
        return self._coerce(other) / self

    def token(self) -> list[str]:
        return [fstr(value) for value in self.coeff]


@dataclass(frozen=True)
class DyadicInterval:
    lo: Fraction
    hi: Fraction
    bits: int

    @property
    def denominator(self) -> int:
        return 1 << self.bits

    @classmethod
    def rounded(cls, lo: Fraction, hi: Fraction, bits: int) -> "DyadicInterval":
        den = 1 << bits
        lo_i = (lo.numerator * den) // lo.denominator
        hi_i = -((-hi.numerator * den) // hi.denominator)
        return cls(Fraction(lo_i, den), Fraction(hi_i, den), bits)

    @classmethod
    def exact(cls, value: Fraction, bits: int) -> "DyadicInterval":
        return cls.rounded(value, value, bits)

    @classmethod
    def sqrt_fraction(cls, value: Fraction, bits: int) -> "DyadicInterval":
        if value < 0:
            raise ValueError("negative interval square root")
        den = 1 << bits
        quotient = (value.numerator << (2 * bits)) // value.denominator
        m = math.isqrt(quotient)
        lo = Fraction(m, den)
        if Fraction(m * m, den * den) == value:
            return cls(lo, lo, bits)
        return cls(lo, Fraction(m + 1, den), bits)

    @classmethod
    def sqrt_interval(cls, value: "DyadicInterval") -> "DyadicInterval":
        if value.lo < 0:
            raise ValueError("interval square root is not certified nonnegative")
        lower = cls.sqrt_fraction(value.lo, value.bits).lo
        upper = cls.sqrt_fraction(value.hi, value.bits).hi
        return cls.rounded(lower, upper, value.bits)

    def __add__(self, other: "DyadicInterval") -> "DyadicInterval":
        if self.bits != other.bits:
            raise TypeError("dyadic precision mismatch")
        return self.rounded(self.lo + other.lo, self.hi + other.hi, self.bits)

    def __neg__(self) -> "DyadicInterval":
        return DyadicInterval(-self.hi, -self.lo, self.bits)

    def __sub__(self, other: "DyadicInterval") -> "DyadicInterval":
        return self + (-other)

    def __mul__(self, other: "DyadicInterval") -> "DyadicInterval":
        if self.bits != other.bits:
            raise TypeError("dyadic precision mismatch")
        products = (
            self.lo * other.lo,
            self.lo * other.hi,
            self.hi * other.lo,
            self.hi * other.hi,
        )
        return self.rounded(min(products), max(products), self.bits)

    def token(self) -> list[str]:
        return [fstr(self.lo), fstr(self.hi)]


@dataclass(frozen=True)
class ExpressionNode:
    """Backend-neutral rational/positive-root expression DAG node.

    The DAG is reconstructed independently from the exact tower coefficients;
    it never asks the :class:`Alg` domain to decide an ordered sign.  Shared
    child objects make the representation a DAG rather than an expanded tree.
    """

    operation: str
    arguments: tuple[object, ...]


def _rational_node(value: Fraction) -> ExpressionNode:
    return ExpressionNode("rational", (value.numerator, value.denominator))


def _linear_combination_dag(
    coefficients: Sequence[Fraction],
    roots: Sequence[ExpressionNode],
) -> ExpressionNode:
    terms: list[ExpressionNode] = []
    for mask, coefficient in enumerate(coefficients):
        if coefficient == 0:
            continue
        term = _rational_node(coefficient)
        for index, root in enumerate(roots):
            if mask & (1 << index):
                term = ExpressionNode("multiply", (term, root))
        terms.append(term)
    if not terms:
        return _rational_node(Fraction())
    result = terms[0]
    for term in terms[1:]:
        result = ExpressionNode("add", (result, term))
    return result


def expression_dag(value: Alg) -> ExpressionNode:
    """Return the independent canonical expression DAG carried by ``value``."""

    roots: list[ExpressionNode] = []
    for radicand in value.field.radicands:
        radicand_dag = _linear_combination_dag(radicand, roots)
        roots.append(ExpressionNode("positive_sqrt", (radicand_dag,)))
    return _linear_combination_dag(value.coeff, roots)


def _evaluate_expression_dag(
    node: ExpressionNode,
    bits: int,
    cache: dict[ExpressionNode, DyadicInterval],
) -> DyadicInterval:
    cached = cache.get(node)
    if cached is not None:
        return cached
    if node.operation == "rational":
        result = DyadicInterval.exact(Fraction(int(node.arguments[0]), int(node.arguments[1])), bits)
    elif node.operation == "add":
        result = _evaluate_expression_dag(node.arguments[0], bits, cache) + _evaluate_expression_dag(  # type: ignore[arg-type]
            node.arguments[1], bits, cache  # type: ignore[arg-type]
        )
    elif node.operation == "multiply":
        result = _evaluate_expression_dag(node.arguments[0], bits, cache) * _evaluate_expression_dag(  # type: ignore[arg-type]
            node.arguments[1], bits, cache  # type: ignore[arg-type]
        )
    elif node.operation == "positive_sqrt":
        result = DyadicInterval.sqrt_interval(
            _evaluate_expression_dag(node.arguments[0], bits, cache)  # type: ignore[arg-type]
        )
    else:  # pragma: no cover - construction above makes this unreachable
        raise ValueError(f"unsupported expression DAG operation: {node.operation}")
    cache[node] = result
    return result


def interval_of(value: Alg, bits: int) -> DyadicInterval:
    return _evaluate_expression_dag(expression_dag(value), bits, {})


def sign_certificate(value: Alg, precisions: Sequence[int]) -> dict[str, object]:
    if value.is_rational:
        rational = value.coeff[0]
        return {
            "classification": "POSITIVE" if rational > 0 else "NEGATIVE" if rational < 0 else "ZERO",
            "exact": fstr(rational),
            "intervals": [],
        }
    rows: list[dict[str, object]] = []
    classification = "INCONCLUSIVE"
    for bits in precisions:
        interval = interval_of(value, bits)
        rows.append({"bits": bits, "bounds": interval.token()})
        if interval.lo > 0:
            classification = "POSITIVE"
        elif interval.hi < 0:
            classification = "NEGATIVE"
    return {"classification": classification, "intervals": rows}


Matrix = list[list[Alg]]
Vector = list[Alg]


def zeros(field: Field, rows: int, cols: int) -> Matrix:
    return [[field.rational() for _ in range(cols)] for _ in range(rows)]


def eye(field: Field, size: int) -> Matrix:
    result = zeros(field, size, size)
    for index in range(size):
        result[index][index] = field.rational(1)
    return result


def transpose(matrix: Matrix) -> Matrix:
    return [list(row) for row in zip(*matrix)]


def matmul(left: Matrix, right: Matrix) -> Matrix:
    if not left or not right or len(left[0]) != len(right):
        raise ValueError("matrix product dimension mismatch")
    field = left[0][0].field
    out = zeros(field, len(left), len(right[0]))
    right_t = transpose(right)
    for i, row in enumerate(left):
        for j, column in enumerate(right_t):
            total = field.rational()
            for a, b in zip(row, column):
                total += a * b
            out[i][j] = total
    return out


def matvec(matrix: Matrix, vector: Vector) -> Vector:
    return [sum((a * b for a, b in zip(row, vector)), row[0].field.rational()) for row in matrix]


def madd(left: Matrix, right: Matrix, factor: object = 1) -> Matrix:
    if len(left) != len(right) or len(left[0]) != len(right[0]):
        raise ValueError("matrix addition dimension mismatch")
    return [[a + factor * b for a, b in zip(x, y)] for x, y in zip(left, right)]


def mscale(matrix: Matrix, factor: object) -> Matrix:
    return [[factor * value for value in row] for row in matrix]


def outer(left: Vector, right: Vector) -> Matrix:
    return [[a * b for b in right] for a in left]


def dot(left: Vector, right: Vector) -> Alg:
    if len(left) != len(right):
        raise ValueError("dot product dimension mismatch")
    return sum((a * b for a, b in zip(left, right)), left[0].field.rational())


def submatrix(matrix: Matrix, indices: Sequence[int]) -> Matrix:
    return [[matrix[i][j] for j in indices] for i in indices]


def matrix_inverse(matrix: Matrix) -> Matrix:
    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise ValueError("inverse requires square matrix")
    field = matrix[0][0].field
    work = [row[:] + unit[:] for row, unit in zip(matrix, eye(field, size))]
    for column in range(size):
        pivot = next((row for row in range(column, size) if not work[row][column].is_zero), None)
        if pivot is None:
            raise ZeroDivisionError(f"singular exact matrix at column {column}")
        if pivot != column:
            work[column], work[pivot] = work[pivot], work[column]
        inverse_pivot = work[column][column].inverse()
        work[column] = [value * inverse_pivot for value in work[column]]
        for row in range(size):
            if row == column or work[row][column].is_zero:
                continue
            factor = work[row][column]
            work[row] = [a - factor * b for a, b in zip(work[row], work[column])]
    return [row[size:] for row in work]


def matrix_rank(matrix: Matrix) -> int:
    if not matrix:
        return 0
    rows, columns = len(matrix), len(matrix[0])
    if any(len(row) != columns for row in matrix):
        raise ValueError("ragged matrix")
    work = [row[:] for row in matrix]
    pivot_row = 0
    for column in range(columns):
        pivot = next((row for row in range(pivot_row, rows) if not work[row][column].is_zero), None)
        if pivot is None:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        inverse = work[pivot_row][column].inverse()
        work[pivot_row] = [value * inverse for value in work[pivot_row]]
        for row in range(rows):
            if row == pivot_row or work[row][column].is_zero:
                continue
            factor = work[row][column]
            work[row] = [a - factor * b for a, b in zip(work[row], work[pivot_row])]
        pivot_row += 1
        if pivot_row == rows:
            break
    return pivot_row


def lexicographic_nullspace(matrix: Matrix) -> Matrix:
    """Exact nullspace columns using first-column/first-row RREF pivots."""

    if not matrix:
        raise ValueError("nullspace source must be nonempty")
    rows, columns = len(matrix), len(matrix[0])
    work = [row[:] for row in matrix]
    pivot_columns: list[int] = []
    pivot_row = 0
    for column in range(columns):
        pivot = next((row for row in range(pivot_row, rows) if not work[row][column].is_zero), None)
        if pivot is None:
            continue
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        inverse = work[pivot_row][column].inverse()
        work[pivot_row] = [value * inverse for value in work[pivot_row]]
        for row in range(rows):
            if row == pivot_row or work[row][column].is_zero:
                continue
            factor = work[row][column]
            work[row] = [a - factor * b for a, b in zip(work[row], work[pivot_row])]
        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row == rows:
            break
    free_columns = [column for column in range(columns) if column not in pivot_columns]
    field = matrix[0][0].field
    basis = zeros(field, columns, len(free_columns))
    for basis_column, free in enumerate(free_columns):
        basis[free][basis_column] = field.rational(1)
        for row, pivot in enumerate(pivot_columns):
            basis[pivot][basis_column] = -work[row][free]
    return basis


def ldl_pivots(matrix: Matrix) -> list[Alg]:
    size = len(matrix)
    field = matrix[0][0].field
    lower = zeros(field, size, size)
    pivots: list[Alg] = []
    for i in range(size):
        lower[i][i] = field.rational(1)
        pivot = matrix[i][i]
        for k in range(i):
            pivot -= lower[i][k] * lower[i][k] * pivots[k]
        if pivot.is_zero:
            raise ZeroDivisionError(f"zero LDL pivot {i}")
        pivots.append(pivot)
        for j in range(i + 1, size):
            value = matrix[j][i]
            for k in range(i):
                value -= lower[j][k] * lower[i][k] * pivots[k]
            lower[j][i] = value / pivot
    return pivots


def matrix_is_zero(matrix: Matrix) -> bool:
    return all(value.is_zero for row in matrix for value in row)


def vector_is_zero(vector: Vector) -> bool:
    return all(value.is_zero for value in vector)


def matrix_digest(matrix: Matrix) -> str:
    payload = [[value.token() for value in row] for row in matrix]
    return sha256_bytes(canonical_bytes(payload))


def vector_digest(vector: Vector) -> str:
    return sha256_bytes(canonical_bytes([value.token() for value in vector]))


def _permutation24(field: Field, operation: "Operation") -> Matrix:
    result = zeros(field, 24, 24)
    for new_node, old_node in enumerate(operation.permutation):
        for dof in range(6):
            result[6 * new_node + dof][6 * old_node + dof] = field.rational(1)
    return result


def _numbered_local5_map(field: Field, operation: "Operation") -> Matrix:
    """Return ``P4 tensor block_diag(Ahat.T,A.T)`` from the frame contract."""

    result = zeros(field, 20, 20)
    ahat = (
        (operation.A[0][0], operation.A[0][1], 0),
        (operation.A[1][0], operation.A[1][1], 0),
        (0, 0, operation.det),
    )
    for new_node, old_node in enumerate(operation.permutation):
        for i in range(3):
            for j in range(3):
                result[5 * new_node + i][5 * old_node + j] = field.rational(ahat[j][i])
        for i in range(2):
            for j in range(2):
                result[5 * new_node + 3 + i][5 * old_node + 3 + j] = field.rational(operation.A[j][i])
    return result


def _numbered_drill_map(field: Field, operation: "Operation") -> Matrix:
    result = zeros(field, 4, 4)
    for new_node, old_node in enumerate(operation.permutation):
        result[new_node][old_node] = field.rational(operation.det)
    return result


def _fraction_matrix(field: Field, values: Sequence[Sequence[object]]) -> Matrix:
    return [[field.rational(F(value)) for value in row] for row in values]


def _shape(field: Field, r: Alg, s: Alg) -> tuple[Vector, Vector, Vector]:
    one = field.rational(1)
    four = field.rational(4)
    n = [
        (one - r) * (one - s) / four,
        (one + r) * (one - s) / four,
        (one + r) * (one + s) / four,
        (one - r) * (one + s) / four,
    ]
    dr = [-(one - s) / four, (one - s) / four, (one + s) / four, -(one + s) / four]
    ds = [-(one - r) / four, -(one + r) / four, (one + r) / four, (one - r) / four]
    return n, dr, ds


def _jacobian(coords: Sequence[tuple[Alg, Alg]], dr: Vector, ds: Vector) -> tuple[Matrix, Alg]:
    field = dr[0].field
    xr = sum((coords[i][0] * dr[i] for i in range(4)), field.rational())
    xs = sum((coords[i][0] * ds[i] for i in range(4)), field.rational())
    yr = sum((coords[i][1] * dr[i] for i in range(4)), field.rational())
    ys = sum((coords[i][1] * ds[i] for i in range(4)), field.rational())
    determinant = xr * ys - xs * yr
    return [[xr, xs], [yr, ys]], determinant


def _physical_gradients(jacobian: Matrix, det: Alg, dr: Vector, ds: Vector) -> tuple[Vector, Vector]:
    # J=[x_r x_s; y_r y_s], grad_x=J^{-T} grad_natural.
    dx = [(jacobian[1][1] * dr[i] - jacobian[1][0] * ds[i]) / det for i in range(4)]
    dy = [(-jacobian[0][1] * dr[i] + jacobian[0][0] * ds[i]) / det for i in range(4)]
    return dx, dy


def _kinematic_membrane(field: Field, dx: Vector, dy: Vector) -> Matrix:
    result = zeros(field, 3, 24)
    for i in range(4):
        base = 6 * i
        result[0][base] = dx[i]
        result[1][base + 1] = dy[i]
        result[2][base] = dy[i]
        result[2][base + 1] = dx[i]
    return result


def _kinematic_bending(field: Field, dx: Vector, dy: Vector) -> Matrix:
    result = zeros(field, 3, 24)
    for i in range(4):
        base = 6 * i
        result[0][base + 4] = dx[i]
        result[1][base + 3] = -dy[i]
        result[2][base + 4] = dy[i]
        result[2][base + 3] = -dx[i]
    return result


def _natural_shear_row(
    field: Field,
    coords: Sequence[tuple[Alg, Alg]],
    r: Alg,
    s: Alg,
    direction: int,
) -> Vector:
    n, dr, ds = _shape(field, r, s)
    deriv = dr if direction == 0 else ds
    x_deriv = sum((coords[i][0] * deriv[i] for i in range(4)), field.rational())
    y_deriv = sum((coords[i][1] * deriv[i] for i in range(4)), field.rational())
    row = [field.rational() for _ in range(24)]
    for i in range(4):
        base = 6 * i
        row[base + 2] = deriv[i]
        row[base + 3] = -y_deriv * n[i]
        row[base + 4] = x_deriv * n[i]
    return row


def _kinematic_mitc_shear(
    field: Field,
    coords: Sequence[tuple[Alg, Alg]],
    r: Alg,
    s: Alg,
    jacobian: Matrix,
    det: Alg,
) -> Matrix:
    zero, one = field.rational(), field.rational(1)
    minus_one = field.rational(-1)
    gr_a = _natural_shear_row(field, coords, zero, minus_one, 0)
    gr_c = _natural_shear_row(field, coords, zero, one, 0)
    gs_b = _natural_shear_row(field, coords, one, zero, 1)
    gs_d = _natural_shear_row(field, coords, minus_one, zero, 1)
    half = field.rational(Fraction(1, 2))
    gr = [(half * (one - s)) * a + (half * (one + s)) * c for a, c in zip(gr_a, gr_c)]
    gs = [(half * (one + r)) * b + (half * (one - r)) * d for b, d in zip(gs_b, gs_d)]
    # J^{-T} maps covariant natural shear components to physical components.
    gx = [(jacobian[1][1] * gr[i] - jacobian[1][0] * gs[i]) / det for i in range(24)]
    gy = [(-jacobian[0][1] * gr[i] + jacobian[0][0] * gs[i]) / det for i in range(24)]
    return [gx, gy]


def _drill_constraint(field: Field, n: Vector, dx: Vector, dy: Vector) -> Matrix:
    row = [field.rational() for _ in range(24)]
    half = field.rational(Fraction(1, 2))
    for i in range(4):
        base = 6 * i
        row[base] = half * dy[i]
        row[base + 1] = -half * dx[i]
        row[base + 5] = n[i]
    return [row]


def _jinv_t_apply(jacobian: Matrix, det: Alg, vector: Vector) -> Vector:
    return [
        (jacobian[1][1] * vector[0] - jacobian[1][0] * vector[1]) / det,
        (-jacobian[0][1] * vector[0] + jacobian[0][0] * vector[1]) / det,
    ]


def _drill_taylor_rows(field: Field, coords: Sequence[tuple[Alg, Alg]]) -> Matrix:
    """Exact centre Taylor rows ``[c(0), c_,r(0), c_,s(0)]``.

    This is the frozen affine PL grammar.  There is deliberately no ``r*s``
    row and no Gauss L2 projection of the full rational curl.
    """

    zero = field.rational()
    n, nr, ns = _shape(field, zero, zero)
    jac, det = _jacobian(coords, nr, ns)
    quarter = field.rational(Fraction(1, 4))
    nr_s = [quarter, -quarter, quarter, -quarter]
    ns_r = [quarter, -quarter, quarter, -quarter]
    xs_r = sum((coords[i][0] * ns_r[i] for i in range(4)), zero)
    ys_r = sum((coords[i][1] * ns_r[i] for i in range(4)), zero)
    xr_s = sum((coords[i][0] * nr_s[i] for i in range(4)), zero)
    yr_s = sum((coords[i][1] * nr_s[i] for i in range(4)), zero)
    jac_r = [[zero, xs_r], [zero, ys_r]]
    jac_s = [[xr_s, zero], [yr_s, zero]]
    rows = [[zero for _ in range(24)] for _ in range(3)]
    half = field.rational(Fraction(1, 2))
    for node in range(4):
        natural = [nr[node], ns[node]]
        grad = _jinv_t_apply(jac, det, natural)
        derivatives: list[Vector] = []
        for natural_derivative, jac_derivative in (([zero, ns_r[node]], jac_r), ([nr_s[node], zero], jac_s)):
            correction = matvec(transpose(jac_derivative), grad)
            rhs = [a - b for a, b in zip(natural_derivative, correction)]
            derivatives.append(_jinv_t_apply(jac, det, rhs))
        base = 6 * node
        rows[0][base] = half * grad[1]
        rows[0][base + 1] = -half * grad[0]
        rows[0][base + 5] = n[node]
        rows[1][base] = half * derivatives[0][1]
        rows[1][base + 1] = -half * derivatives[0][0]
        rows[1][base + 5] = nr[node]
        rows[2][base] = half * derivatives[1][1]
        rows[2][base + 1] = -half * derivatives[1][0]
        rows[2][base + 5] = ns[node]
    return rows


def _tensor_transform(jacobian: Matrix, a: int, b: int) -> Matrix:
    """Accepted E4-0 ``T(a,b)`` with ``J_wg=J_map^T``."""

    xr, xs = jacobian[0]
    yr, ys = jacobian[1]
    return [
        [xr * xr, xs * xs, a * xr * xs],
        [yr * yr, ys * ys, a * yr * ys],
        [b * xr * yr, b * xs * ys, xr * ys + yr * xs],
    ]


def _centre_geometry_terms(
    field: Field,
    coords: Sequence[tuple[Alg, Alg]],
) -> tuple[Matrix, Alg, Alg, Alg]:
    """Return ``J0, j0, r_bar, s_bar`` from the frozen bilinear map.

    The centroid offsets are the WG source-space offsets
    ``jr/(3*j0), js/(3*j0)``.  They are geometry coefficients, not values
    inferred from a pointwise-J transform or from an observed rank.
    """

    zero = field.rational()
    _, dr, ds = _shape(field, zero, zero)
    jacobian, j0 = _jacobian(coords, dr, ds)
    cross = [field.rational(Fraction(value, 4)) for value in (1, -1, 1, -1)]
    xrs = sum((coords[i][0] * cross[i] for i in range(4)), zero)
    yrs = sum((coords[i][1] * cross[i] for i in range(4)), zero)
    xr, xs = jacobian[0]
    yr, ys = jacobian[1]
    jr = xr * yrs - xrs * yr
    js = xrs * ys - xs * yrs
    return jacobian, j0, jr / (3 * j0), js / (3 * j0)


def _source_mixed_fields(
    field: Field,
    r: Alg,
    s: Alg,
    centre_jacobian: Matrix,
    current_det: Alg,
    centre_det: Alg,
    r_bar: Alg,
    s_bar: Alg,
) -> tuple[Matrix, Matrix]:
    """Return source-ordered ``N_sigma(8x14), N_epsilon(8x21)``.

    Ordering and transformations are the inherited accepted E4-0 identity:
    constant resultant/strain block, membrane/bending/shear varying pairs,
    followed by the seven ``n=7, k=0`` membrane enrichment parameters.
    """

    n_sigma = zeros(field, 8, 14)
    n_epsilon = zeros(field, 8, 21)
    for index in range(8):
        n_sigma[index][index] = field.rational(1)
        n_epsilon[index][index] = field.rational(1)

    tensor_seed = [
        [s - s_bar, field.rational()],
        [field.rational(), r - r_bar],
        [field.rational(), field.rational()],
    ]
    vector_seed = [[s - s_bar, field.rational()], [field.rational(), r - r_bar]]
    t_sigma = _tensor_transform(centre_jacobian, 2, 1)
    t_epsilon = _tensor_transform(centre_jacobian, 1, 2)
    t_tilde = centre_jacobian
    sigma_tensor = matmul(t_sigma, tensor_seed)
    epsilon_tensor = matmul(t_epsilon, tensor_seed)
    shear_seed = matmul(t_tilde, vector_seed)
    _add_block(n_sigma, sigma_tensor, 0, 8)
    _add_block(n_sigma, sigma_tensor, 3, 10)
    _add_block(n_sigma, shear_seed, 6, 12)
    _add_block(n_epsilon, epsilon_tensor, 0, 8)
    _add_block(n_epsilon, epsilon_tensor, 3, 10)
    _add_block(n_epsilon, shear_seed, 6, 12)

    z, rs = field.rational(), r * s
    enrichment_natural = [
        [r, z, z, z, rs, z, z],
        [z, s, z, z, z, rs, z],
        [z, z, r, s, z, z, rs],
    ]
    enrichment = mscale(matmul(t_epsilon, enrichment_natural), centre_det / current_det)
    _add_block(n_epsilon, enrichment, 0, 14)
    return n_sigma, n_epsilon


def _physical20(matrix24: Matrix) -> Matrix:
    columns = [6 * node + dof for node in range(4) for dof in range(5)]
    return [[row[column] for column in columns] for row in matrix24]


def _kinematic_source_operator(bm24: Matrix, bb24: Matrix, bs24: Matrix) -> Matrix:
    return _physical20(bm24 + bb24 + bs24)


def _add_block(target: Matrix, block: Matrix, row: int, col: int, factor: object = 1) -> None:
    for i, values in enumerate(block):
        for j, value in enumerate(values):
            target[row + i][col + j] += factor * value


def _integrate_product(left: Matrix, middle: Matrix, right: Matrix, weight: Alg) -> Matrix:
    return mscale(matmul(matmul(transpose(left), middle), right), weight)


def _integrate_pair(left: Matrix, right: Matrix, weight: Alg) -> Matrix:
    return mscale(matmul(transpose(left), right), weight)


@dataclass(frozen=True)
class Operation:
    id: str
    A: tuple[tuple[int, int], tuple[int, int]]
    det: int
    permutation: tuple[int, int, int, int]


@dataclass(frozen=True)
class Geometry:
    id: str
    nodes: tuple[tuple[Fraction, Fraction, Fraction], ...]
    transformed: bool = False


@dataclass
class Assembly:
    field: Field
    geometry_id: str
    operation_id: str
    nodes: tuple[tuple[Alg, Alg, Alg], ...]
    frame: Matrix
    coords: tuple[tuple[Alg, Alg], ...]
    t5: Matrix
    qd: Matrix
    physical_projector: Matrix
    drill_projector: Matrix
    local_to_global: Matrix
    f_core: Matrix
    h_strain: Matrix
    gq: Matrix
    h_core: Matrix
    inv_core: Matrix
    c_core: Matrix
    m_pl: Matrix
    taylor_c: Matrix
    h_pl: Matrix
    inv_pl: Matrix
    c_pl: Matrix
    k_hg: Matrix
    k_core: Matrix
    k_pl: Matrix
    k_total: Matrix
    k_core_global: Matrix
    k_pl_global: Matrix
    k_hg_global: Matrix
    k_total_global: Matrix
    jacobians: tuple[Alg, ...]
    gamma_hg: Vector
    area_hg: Alg


def _contracts() -> dict[str, object]:
    result: dict[str, object] = {}
    for relative in JSON_INPUTS + tuple(INHERITED_CORE_INPUTS):
        value = load_json(ROOT / relative)
        if not isinstance(value, dict):
            raise ValueError(f"{relative} must contain a JSON object")
        result[pathlib.Path(relative).stem] = value
    for relative, expected in INHERITED_CORE_INPUTS.items():
        raw = (ROOT / relative).read_bytes()
        if len(raw) != expected["bytes"] or sha256_bytes(raw) != expected["sha256"]:
            raise ValueError(f"inherited accepted E4-0 core identity mismatch: {relative}")
    manifest = result["e4_pl_q1t_inheritance_manifest"]
    if not isinstance(manifest, dict):
        raise ValueError("Q1T inheritance manifest must be an object")
    groups = ("q1r_e4_inherited_inputs", "q1s_commit1_inputs", "q1s_closeout_inputs")
    direct_rows = [row for group in groups for row in manifest[group]]  # type: ignore[index]
    if len(direct_rows) != 49 or len({str(row["path"]) for row in direct_rows}) != 49:
        raise ValueError("Q1T inheritance manifest must bind exactly 49 distinct paths")
    bound_rows = {str(row["path"]): row for row in direct_rows}
    for relative, row in bound_rows.items():
        path = ROOT / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"inherited authority is not a regular nonsymlink file: {relative}")
        raw = path.read_bytes()
        if len(raw) != row["bytes"] or sha256_bytes(raw) != str(row["sha256"]).upper():
            raise ValueError(f"inherited authority identity mismatch: {relative}")
        if _git("rev-parse", f"{row['source_commit']}:{relative}") != row["git_blob"]:
            raise ValueError(f"inherited authority Git blob mismatch: {relative}")
    for relative in MECHANICS_INPUTS + tuple(INHERITED_CORE_INPUTS):
        row = bound_rows.get(relative)
        if not isinstance(row, dict):
            raise ValueError(f"missing inherited source authority: {relative}")
    return result


def _operations(frame_contract: Mapping[str, object]) -> tuple[Operation, ...]:
    rows = frame_contract["d4"]["operations"]  # type: ignore[index]
    return tuple(
        Operation(
            str(row["id"]),
            tuple(tuple(int(x) for x in values) for values in row["A"]),  # type: ignore[arg-type]
            int(row["det"]),
            tuple(int(x) - 1 for x in row["node_tuple"]),
        )
        for row in rows  # type: ignore[union-attr]
    )


def _geometries(geometry_contract: Mapping[str, object]) -> tuple[Geometry, ...]:
    result = []
    for row in geometry_contract["geometries"]:  # type: ignore[index]
        nodes = tuple((F(node[0]), F(node[1]), F(node[2])) for node in row["nodes"])
        result.append(Geometry(str(row["id"]), nodes))
    source = next(item for item in result if item.id == "Q3_TAPERED_SKEW")
    transform = geometry_contract["global_transform"]  # type: ignore[index]
    rotation = [[F(value) for value in row] for row in transform["R_star"]]
    translation = [F(value) for value in transform["b_star"]]
    transformed_nodes = tuple(
        tuple(sum((rotation[i][j] * node[j] for j in range(3)), Fraction()) + translation[i] for i in range(3))
        for node in source.nodes
    )
    expected = tuple(tuple(F(value) for value in node) for node in transform["derived_nodes"])
    if transformed_nodes != expected:
        raise ValueError("frozen R_star/translation does not reproduce derived Q3 nodes")
    result.append(Geometry("Q3_TAPERED_SKEW_RSTAR_TRANSLATED", transformed_nodes, True))
    return tuple(result)


def _dot3(left: Sequence[Alg], right: Sequence[Alg]) -> Alg:
    return dot(list(left), list(right))


def _cross3(left: Sequence[Alg], right: Sequence[Alg]) -> tuple[Alg, Alg, Alg]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _lift_vector(vector: Sequence[Alg], field: Field) -> tuple[Alg, ...]:
    return tuple(value.lift(field) for value in vector)


def _equation7_context(geometry: Geometry) -> Field:
    d1 = tuple(geometry.nodes[2][i] - geometry.nodes[0][i] for i in range(3))
    d2 = tuple(geometry.nodes[1][i] - geometry.nodes[3][i] for i in range(3))
    l1 = sum((value * value for value in d1), Fraction())
    l2 = sum((value * value for value in d2), Fraction())
    field = Field(())
    field, root1 = field.with_sqrt(field.rational(l1))
    field, root2 = field.with_sqrt(field.rational(l2))
    root1 = root1.lift(field)
    a = tuple(field.rational(value) / root1 for value in d1)
    b = tuple(field.rational(value) / root2 for value in d2)
    plus = tuple(x + y for x, y in zip(a, b))
    field, _ = field.with_sqrt(_dot3(plus, plus))
    d1_lifted = _lift_vector(tuple(field.rational(value) for value in d1), field)
    d2_lifted = _lift_vector(tuple(field.rational(value) for value in d2), field)
    diagonal_cross = _cross3(d1_lifted, d2_lifted)
    field, _ = field.with_sqrt(_dot3(diagonal_cross, diagonal_cross))
    field, _ = field.with_sqrt(field.rational(3))
    return field


def _equation7_frame(
    geometry: Geometry,
    operation: Operation,
) -> tuple[Field, tuple[tuple[Alg, Alg, Alg], ...], Matrix, tuple[tuple[Alg, Alg], ...]]:
    field = _equation7_context(geometry)
    numbered_fraction = tuple(geometry.nodes[index] for index in operation.permutation)
    nodes = tuple(tuple(field.rational(value) for value in node) for node in numbered_fraction)
    d1 = tuple(nodes[2][i] - nodes[0][i] for i in range(3))
    d2 = tuple(nodes[1][i] - nodes[3][i] for i in range(3))
    root1 = field.sqrt(_dot3(d1, d1))
    root2 = field.sqrt(_dot3(d2, d2))
    a = tuple(value / root1 for value in d1)
    b = tuple(value / root2 for value in d2)
    plus = tuple(x + y for x, y in zip(a, b))
    minus = tuple(x - y for x, y in zip(a, b))
    t1_norm = field.sqrt(_dot3(plus, plus))
    diagonal_cross = _cross3(d1, d2)
    cross_norm = field.sqrt(_dot3(diagonal_cross, diagonal_cross))
    # Since the normalized diagonal sum and difference are orthogonal,
    # |a-b| = 2|d1 x d2|/(|d1||d2||a+b|).  This avoids adjoining a
    # redundant square root whose product with |a+b| already lies in the
    # preceding exact field.
    t2_norm = 2 * cross_norm / (root1 * root2 * t1_norm)
    if t2_norm * t2_norm != _dot3(minus, minus):
        raise ValueError("equation-7 second diagonal normalization identity failed")
    t1 = tuple(value / t1_norm for value in plus)
    t2 = tuple(value / t2_norm for value in minus)
    t3 = _cross3(t1, t2)
    frame = [[t1[row], t2[row], t3[row]] for row in range(3)]
    centre = tuple(sum((node[i] for node in nodes), field.rational()) / 4 for i in range(3))
    coords = tuple(
        (_dot3(tuple(node[i] - centre[i] for i in range(3)), t1), _dot3(tuple(node[i] - centre[i] for i in range(3)), t2))
        for node in nodes
    )
    return field, nodes, frame, coords


def _frame_embeddings(field: Field, frame: Matrix) -> tuple[Matrix, Matrix, Matrix, Matrix, Matrix]:
    t5 = zeros(field, 24, 20)
    qd = zeros(field, 24, 4)
    local_to_global = zeros(field, 24, 24)
    for node in range(4):
        for i in range(3):
            for j in range(3):
                t5[6 * node + i][5 * node + j] = frame[i][j]
                local_to_global[6 * node + i][6 * node + j] = frame[i][j]
                local_to_global[6 * node + 3 + i][6 * node + 3 + j] = frame[i][j]
            for j in range(2):
                t5[6 * node + 3 + i][5 * node + 3 + j] = frame[i][j]
            qd[6 * node + 3 + i][node] = frame[i][2]
    p5 = matmul(t5, transpose(t5))
    pd = matmul(qd, transpose(qd))
    return t5, qd, p5, pd, local_to_global


def _gauss(field: Field) -> tuple[tuple[Alg, Alg], ...]:
    g = field.sqrt(Fraction(3)) / 3
    return ((-g, -g), (g, -g), (g, g), (-g, g))


GAUSS_IDS = ("GP_MM", "GP_PM", "GP_PP", "GP_MP")


def _material(field: Field) -> tuple[Matrix, Matrix, Matrix]:
    membrane = _fraction_matrix(field, (("32/3", "8/3", 0), ("8/3", "32/3", 0), (0, 0, 4)))
    bending = _fraction_matrix(field, (("32/81", "8/81", 0), ("8/81", "32/81", 0), (0, 0, "4/27")))
    shear = _fraction_matrix(field, (("10/3", 0), (0, "10/3")))
    return membrane, bending, shear


def _material8(field: Field) -> Matrix:
    membrane, bending, shear = _material(field)
    result = zeros(field, 8, 8)
    _add_block(result, membrane, 0, 0)
    _add_block(result, bending, 3, 3)
    _add_block(result, shear, 6, 6)
    return result


def _residual_row(field: Field, coords: tuple[tuple[Alg, Alg], ...]) -> tuple[Vector, Alg]:
    zero = field.rational()
    r0 = zero
    s0 = zero
    _, dr, ds = _shape(field, r0, s0)
    _, jc = _jacobian(coords, dr, ds)
    area = 4 * jc
    xc = sum((x for x, _ in coords), zero) / 4
    yc = sum((y for _, y in coords), zero) / 4
    s1 = [x - xc for x, _ in coords]
    s2 = [y - yc for _, y in coords]
    xi = [field.rational(v) for v in (-1, 1, 1, -1)]
    eta = [field.rational(v) for v in (-1, -1, 1, 1)]
    h4 = [field.rational(v) for v in (1, -1, 1, -1)]
    eta_s2, xi_s2 = dot(eta, s2), dot(xi, s2)
    eta_s1, xi_s1 = dot(eta, s1), dot(xi, s1)
    b1 = [(eta_s2 * xi[i] - xi_s2 * eta[i]) / (4 * area) for i in range(4)]
    b2 = [(-eta_s1 * xi[i] + xi_s1 * eta[i]) / (4 * area) for i in range(4)]
    h_s1, h_s2 = dot(h4, s1), dot(h4, s2)
    gamma = [(h4[i] - h_s1 * b1[i] - h_s2 * b2[i]) / 4 for i in range(4)]
    return gamma, area


def assemble(geometry: Geometry, operation: Operation) -> Assembly:
    field, nodes, frame, coords = _equation7_frame(geometry, operation)
    t5, qd, p5, pd, local_to_global = _frame_embeddings(field, frame)
    constitutive = _material8(field)
    f_core = zeros(field, 21, 14)
    h_strain = zeros(field, 21, 21)
    gq = zeros(field, 14, 20)
    m_pl = zeros(field, 3, 3)
    jacobians: list[Alg] = []

    centre_jacobian, centre_det, r_bar, s_bar = _centre_geometry_terms(field, coords)
    for r, s in _gauss(field):
        n, dr, ds = _shape(field, r, s)
        jac, det = _jacobian(coords, dr, ds)
        jacobians.append(det)
        dx, dy = _physical_gradients(jac, det, dr, ds)
        bm = _kinematic_membrane(field, dx, dy)
        bb = _kinematic_bending(field, dx, dy)
        bs = _kinematic_mitc_shear(field, coords, r, s, jac, det)
        b_source = _kinematic_source_operator(bm, bb, bs)
        n_sigma, n_epsilon = _source_mixed_fields(
            field, r, s, centre_jacobian, det, centre_det, r_bar, s_bar
        )
        f_core = madd(f_core, _integrate_pair(n_epsilon, n_sigma, det), -1)
        h_strain = madd(h_strain, _integrate_product(n_epsilon, constitutive, n_epsilon, det))
        gq = madd(gq, _integrate_pair(n_sigma, b_source, det))

        p = [[field.rational(1), r, s]]
        thickness = field.rational(Fraction(2, 3))
        m_pl = madd(m_pl, _integrate_pair(p, p, thickness * det))

    # Accepted E4-0 source ordering and stationary matrices:
    # D=[[0_14x14,F^T],[F,H]], Q=[Gq^T,0_20x21].
    h_core = zeros(field, 35, 35)
    _add_block(h_core, transpose(f_core), 0, 14)
    _add_block(h_core, f_core, 14, 0)
    _add_block(h_core, h_strain, 14, 14)
    c_core = zeros(field, 35, 24)
    for stress in range(14):
        for physical in range(20):
            node, dof = divmod(physical, 5)
            c_core[stress][6 * node + dof] = gq[stress][physical]
    taylor_c = _drill_taylor_rows(field, coords)
    h_pl = mscale(m_pl, Fraction(-1, 6))
    c_pl = matmul(m_pl, taylor_c)

    inv_core = matrix_inverse(h_core)
    inv_pl = matrix_inverse(h_pl)
    k_core = mscale(matmul(matmul(transpose(c_core), inv_core), c_core), -1)
    k_pl = mscale(matmul(matmul(transpose(c_pl), inv_pl), c_pl), -1)

    gamma, area = _residual_row(field, coords)
    row = [field.rational() for _ in range(24)]
    for i, value in enumerate(gamma):
        row[6 * i + 5] = value
    # Pi_hg=eps*G*t*A*(row*q)^2, hence K_hg=2*eps*G*t*A*row^T row.
    coefficient = field.rational(2 * Fraction(1, 1000) * 6 * Fraction(2, 3)) * area
    k_hg = mscale(outer(row, row), coefficient)
    total = madd(madd(k_core, k_pl), k_hg)
    k_core_global = matmul(matmul(local_to_global, k_core), transpose(local_to_global))
    k_pl_global = matmul(matmul(local_to_global, k_pl), transpose(local_to_global))
    k_hg_global = matmul(matmul(local_to_global, k_hg), transpose(local_to_global))
    k_total_global = madd(madd(k_core_global, k_pl_global), k_hg_global)
    return Assembly(
        field=field,
        geometry_id=geometry.id,
        operation_id=operation.id,
        nodes=nodes,
        frame=frame,
        coords=coords,
        t5=t5,
        qd=qd,
        physical_projector=p5,
        drill_projector=pd,
        local_to_global=local_to_global,
        f_core=f_core,
        h_strain=h_strain,
        gq=gq,
        h_core=h_core,
        inv_core=inv_core,
        c_core=c_core,
        m_pl=m_pl,
        taylor_c=taylor_c,
        h_pl=h_pl,
        inv_pl=inv_pl,
        c_pl=c_pl,
        k_hg=k_hg,
        k_core=k_core,
        k_pl=k_pl,
        k_total=total,
        k_core_global=k_core_global,
        k_pl_global=k_pl_global,
        k_hg_global=k_hg_global,
        k_total_global=k_total_global,
        jacobians=tuple(jacobians),
        gamma_hg=gamma,
        area_hg=area,
    )


def _field_q(
    assembly: Assembly,
    field_id: str,
) -> Vector:
    f = assembly.field
    result = [f.rational() for _ in range(24)]
    for i, (x, y) in enumerate(assembly.coords):
        u = v = w = tx = ty = td = f.rational()
        if field_id == "RIGID_TRANSLATION_T1":
            u = f.rational(1)
        elif field_id == "RIGID_TRANSLATION_T2":
            v = f.rational(1)
        elif field_id == "RIGID_TRANSLATION_T3":
            w = f.rational(1)
        elif field_id == "RIGID_ROTATION_T1":
            w, tx = y, f.rational(1)
        elif field_id == "RIGID_ROTATION_T2":
            w, ty = -x, f.rational(1)
        elif field_id == "RIGID_ROTATION_T3_MATCHED_DRILL":
            u, v, td = -y, x, f.rational(1)
        elif field_id == "MEMBRANE_PATCH":
            u, v, td = 2 * x + y / 3, -F(2) * x / 5 + F(4) * y / 3, f.rational(Fraction(-11, 30))
        elif field_id == "BENDING_PATCH":
            w = -x * x / 5 + y * y / 6 - 3 * x * y / 14
            tx, ty = y / 3 - 3 * x / 14, 2 * x / 5 + 3 * y / 14
        elif field_id == "SHEAR_PATCH":
            tx, ty = f.rational(Fraction(1, 4)), f.rational(Fraction(2, 3))
        elif field_id == "COMBINED_PHYSICAL_PATCH":
            u, v, td = 2 * x + y / 3, -F(2) * x / 5 + F(4) * y / 3, f.rational(Fraction(-11, 30))
            w = -x * x / 5 + y * y / 6 - 3 * x * y / 14
            tx = y / 3 - 3 * x / 14 + Fraction(1, 4)
            ty = 2 * x / 5 + 3 * y / 14 + Fraction(2, 3)
        elif field_id == "COMMON_DRILL":
            td = f.rational(1)
        elif field_id == "TRANSLATION_ONLY_SPIN":
            u, v = -y, x
        elif field_id == "ALTERNATING_DRILL":
            td = f.rational((1, -1, 1, -1)[i])
        else:
            raise KeyError(field_id)
        result[6 * i : 6 * i + 6] = [u, v, w, tx, ty, td]
    return result


FIELD_IDS = (
    "RIGID_TRANSLATION_T1",
    "RIGID_TRANSLATION_T2",
    "RIGID_TRANSLATION_T3",
    "RIGID_ROTATION_T1",
    "RIGID_ROTATION_T2",
    "RIGID_ROTATION_T3_MATCHED_DRILL",
    "MEMBRANE_PATCH",
    "BENDING_PATCH",
    "SHEAR_PATCH",
    "COMBINED_PHYSICAL_PATCH",
    "COMMON_DRILL",
    "TRANSLATION_ONLY_SPIN",
    "ALTERNATING_DRILL",
)


def _transported_fields(base: Assembly, transformed: Assembly, operation: Operation) -> dict[str, Vector]:
    """Construct fields once in E's source frame, then apply the node-only map."""

    p24 = _permutation24(base.field, operation)
    return {
        field_id: matvec(
            transpose(transformed.local_to_global),
            matvec(p24, matvec(base.local_to_global, _field_q(base, field_id))),
        )
        for field_id in FIELD_IDS
    }


def _frozen_physical_load(field: Field) -> Vector:
    rows = (
        ("1", "2", "3", "4", "5"),
        ("-1", "1/2", "-2", "3/2", "-3"),
        ("2", "-1", "4", "-2", "1"),
        ("-2", "3", "-1", "1/3", "-1/2"),
    )
    return [field.rational(F(value)) for row in rows for value in row]


def _boundary_certificate(
    base: Assembly,
    assembly: Assembly,
    operation: Operation,
    fields: Mapping[str, Vector],
) -> dict[str, object]:
    """Certify the frozen physical load and full physical-zero KKT probe.

    The exact supported solution is constructed from the work-conjugate
    identities, then substituted into the actual KKT equations.  Uniqueness
    is certified independently by the four-coordinate drill block; no
    support row is used to repair element rank.
    """

    p24 = _permutation24(assembly.field, operation)
    local5 = _numbered_local5_map(assembly.field, operation)
    p_f = _frozen_physical_load(assembly.field)
    base_load = matvec(base.t5, p_f)
    physical_load = matvec(p24, base_load)
    rebuilt_load = matvec(assembly.t5, matvec(local5, p_f))
    drill_load = matvec(transpose(assembly.qd), physical_load)
    # A_bc^(g)=A_bc^(E)*P_g^T is the registered full physical-zero probe.
    a_bc = matmul(transpose(base.t5), transpose(p24))
    support_drill = matmul(a_bc, assembly.qd)
    zero24 = [assembly.field.rational() for _ in range(24)]
    multiplier = p_f[:]
    support_reaction = matvec(transpose(a_bc), multiplier)
    equilibrium = [
        a + b - c
        for a, b, c in zip(
            matvec(assembly.k_total_global, zero24), support_reaction, physical_load
        )
    ]
    constraint = matvec(a_bc, zero24)
    kkt = zeros(assembly.field, 44, 44)
    _add_block(kkt, assembly.k_total_global, 0, 0)
    _add_block(kkt, transpose(a_bc), 0, 24)
    _add_block(kkt, a_bc, 24, 0)
    kkt_solution = zero24 + multiplier
    kkt_rhs = physical_load + [assembly.field.rational() for _ in range(20)]
    kkt_solution_exact = vector_is_zero(
        [a - b for a, b in zip(matvec(kkt, kkt_solution), kkt_rhs)]
    )
    drill_block = matmul(
        matmul(transpose(assembly.qd), assembly.k_total_global), assembly.qd
    )
    try:
        drill_inverse = matrix_inverse(drill_block)
        drill_block_invertible = matmul(drill_block, drill_inverse) == eye(assembly.field, 4)
    except ZeroDivisionError:
        drill_block_invertible = False
    virtual = [
        assembly.field.rational(Fraction((index % 9) - 4, (index % 4) + 1))
        for index in range(24)
    ]
    virtual_work_exact = dot(support_reaction, virtual) == dot(multiplier, matvec(a_bc, virtual))

    q_local = fields["COMBINED_PHYSICAL_PATCH"]
    q_global = matvec(assembly.local_to_global, q_local)
    physical_internal = matvec(assembly.k_core_global, q_global)
    pl_internal = matvec(assembly.k_pl_global, q_global)
    residual_internal = matvec(assembly.k_hg_global, q_global)
    numerical_internal = [a + b for a, b in zip(pl_internal, residual_internal)]
    total_internal = [a + b for a, b in zip(physical_internal, numerical_internal)]
    total_physical_projection = matvec(assembly.physical_projector, total_internal)
    total_drill_projection = matvec(assembly.drill_projector, total_internal)
    numerical_physical_projection = matvec(assembly.physical_projector, numerical_internal)
    numerical_drill_projection = matvec(assembly.drill_projector, numerical_internal)
    support_reaction_drill = matvec(transpose(assembly.qd), support_reaction)
    physical_internal_drill = matvec(transpose(assembly.qd), physical_internal)
    return {
        "T5_QD_orthogonal": matrix_is_zero(matmul(transpose(assembly.t5), assembly.qd)),
        "projector_partition": madd(madd(assembly.physical_projector, assembly.drill_projector), eye(assembly.field, 24), -1) == zeros(assembly.field, 24, 24),
        "transported_load_rebuilt": physical_load == rebuilt_load,
        "physical_load_drill_free": vector_is_zero(drill_load),
        "A_bc_QD_zero": matrix_is_zero(support_drill),
        "KKT_drill_block_invertible": drill_block_invertible,
        "KKT_equilibrium_exact": vector_is_zero(equilibrium),
        "KKT_constraint_exact": vector_is_zero(constraint),
        "KKT_full_system_exact": kkt_solution_exact,
        "KKT_virtual_work_exact": virtual_work_exact,
        "support_reaction_drill_free": vector_is_zero(support_reaction_drill),
        "physical_internal_drill_free": vector_is_zero(physical_internal_drill),
        "numerical_reactions_separate": all(
            a == b + c for a, b, c in zip(numerical_internal, pl_internal, residual_internal)
        )
        and all(a == b + c for a, b, c in zip(total_internal, physical_internal, numerical_internal))
        and all(
            a == b + c
            for a, b, c in zip(total_internal, total_physical_projection, total_drill_projection)
        )
        and all(
            a == b + c
            for a, b, c in zip(
                numerical_internal,
                numerical_physical_projection,
                numerical_drill_projection,
            )
        ),
        "physical_load_digest": vector_digest(physical_load),
        "supported_solution_digest": vector_digest(zero24),
        "multiplier_digest": vector_digest(multiplier),
        "support_reaction_digest": vector_digest(support_reaction),
        "KKT_digest": matrix_digest(kkt),
        "physical_internal_digest": vector_digest(physical_internal),
        "pl_internal_digest": vector_digest(pl_internal),
        "residual_internal_digest": vector_digest(residual_internal),
        "numerical_internal_digest": vector_digest(numerical_internal),
        "total_internal_digest": vector_digest(total_internal),
        "total_physical_projection_digest": vector_digest(total_physical_projection),
        "total_drill_projection_digest": vector_digest(total_drill_projection),
        "numerical_physical_projection_digest": vector_digest(numerical_physical_projection),
        "numerical_drill_projection_digest": vector_digest(numerical_drill_projection),
    }


def _solve_internal(assembly: Assembly, q: Vector) -> tuple[Vector, Vector]:
    core_rhs = [-value for value in matvec(assembly.c_core, q)]
    pl_rhs = [-value for value in matvec(assembly.c_pl, q)]
    return matvec(assembly.inv_core, core_rhs), matvec(assembly.inv_pl, pl_rhs)


def _recovery_at_gauss(assembly: Assembly, core: Vector, q: Vector) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    stress = core[0:14]
    strain = core[14:35]
    q5 = [q[6 * node + dof] for node in range(4) for dof in range(5)]
    centre_jacobian, centre_det, r_bar, s_bar = _centre_geometry_terms(
        assembly.field, assembly.coords
    )
    for station_id, (r, s) in zip(GAUSS_IDS, _gauss(assembly.field)):
        _, dr, ds = _shape(assembly.field, r, s)
        jac, det = _jacobian(assembly.coords, dr, ds)
        dx, dy = _physical_gradients(jac, det, dr, ds)
        compatible_operator = _kinematic_source_operator(
            _kinematic_membrane(assembly.field, dx, dy),
            _kinematic_bending(assembly.field, dx, dy),
            _kinematic_mitc_shear(assembly.field, assembly.coords, r, s, jac, det),
        )
        n_sigma, n_epsilon = _source_mixed_fields(
            assembly.field, r, s, centre_jacobian, det, centre_det, r_bar, s_bar
        )
        compatible = matvec(compatible_operator, q5)
        independent = matvec(n_epsilon, strain)
        resultant = matvec(n_sigma, stress)
        tangent = [[assembly.frame[i][j] for j in range(2)] for i in range(3)]

        def tensor_global(values: Sequence[Alg]) -> Matrix:
            local = [[values[0], values[2]], [values[2], values[1]]]
            return matmul(matmul(tangent, local), transpose(tangent))

        q_global = [assembly.frame[i][0] * resultant[6] + assembly.frame[i][1] * resultant[7] for i in range(3)]
        result.append(
            {
                "station_id": station_id,
                "compatible": [value.token() for value in compatible],
                "independent": [value.token() for value in independent],
                "N": [value.token() for value in resultant[0:3]],
                "M": [value.token() for value in resultant[3:6]],
                "Q": [value.token() for value in resultant[6:8]],
                "N_global": [[value.token() for value in row] for row in tensor_global(resultant[0:3])],
                "M_global": [[value.token() for value in row] for row in tensor_global(resultant[3:6])],
                "Q_global": [value.token() for value in q_global],
            }
        )
    return result


def _expected_strains(field: Field, field_id: str) -> tuple[Vector, Vector, Vector]:
    zero3 = [field.rational() for _ in range(3)]
    zero2 = [field.rational() for _ in range(2)]
    eps = zero3[:]
    kap = zero3[:]
    shear = zero2[:]
    if field_id in ("MEMBRANE_PATCH", "COMBINED_PHYSICAL_PATCH"):
        eps = [field.rational(2), field.rational(Fraction(4, 3)), field.rational(Fraction(-1, 15))]
    if field_id in ("BENDING_PATCH", "COMBINED_PHYSICAL_PATCH"):
        kap = [field.rational(Fraction(2, 5)), field.rational(Fraction(-1, 3)), field.rational(Fraction(3, 7))]
    if field_id in ("SHEAR_PATCH", "COMBINED_PHYSICAL_PATCH"):
        shear = [field.rational(Fraction(2, 3)), field.rational(Fraction(-1, 4))]
    return eps, kap, shear


def _expected_strain_tokens(field: Field, field_id: str) -> list[str | list[str]]:
    eps, kap, shear = _expected_strains(field, field_id)
    return [value.token() for value in eps + kap + shear]


def _expected_resultants(field: Field, field_id: str) -> tuple[Vector, Vector, Vector]:
    a_mat, d_mat, as_mat = _material(field)
    eps, kap, shear = _expected_strains(field, field_id)
    return matvec(a_mat, eps), matvec(d_mat, kap), matvec(as_mat, shear)


def _field_transport_maps(field: Field, operation: Operation) -> tuple[Matrix, Matrix, Matrix, Matrix, Matrix]:
    """Return C_eng, C_res, delta*A, S and delta*S for g-to-0 transport."""

    a, b = operation.A[0]
    c, d = operation.A[1]
    c_eng = _fraction_matrix(
        field,
        ((a * a, b * b, a * b), (c * c, d * d, c * d), (2 * a * c, 2 * b * d, a * d + b * c)),
    )
    c_res = _fraction_matrix(
        field,
        ((a * a, b * b, 2 * a * b), (c * c, d * d, 2 * c * d), (a * c, b * d, a * d + b * c)),
    )
    pseudo_vector = _fraction_matrix(
        field,
        (
            (operation.det * a, operation.det * b),
            (operation.det * c, operation.det * d),
        ),
    )
    s_map = _fraction_matrix(field, ((1, 0, 0), (0, a, b), (0, c, d)))
    return c_eng, c_res, pseudo_vector, s_map, mscale(s_map, operation.det)


def _expected_numbered_resultants(field: Field, field_id: str, operation: Operation) -> tuple[Vector, Vector, Vector]:
    base_n, base_m, base_q = _expected_resultants(field, field_id)
    c_eng, _, pseudo_vector, _, _ = _field_transport_maps(field, operation)
    # Frozen maps are N0=C_res*Ng, M0=delta*C_res*Mg and Q0=delta*A*Qg.
    return (
        matvec(transpose(c_eng), base_n),
        [operation.det * value for value in matvec(transpose(c_eng), base_m)],
        matvec(transpose(pseudo_vector), base_q),
    )


def _patch_certificate(assembly: Assembly, operation: Operation, fields: Mapping[str, Vector], field_id: str) -> dict[str, object]:
    q = fields[field_id]
    core, pl = _solve_internal(assembly, q)
    recovered = _recovery_at_gauss(assembly, core, q)
    expected_n, expected_m, expected_q = _expected_numbered_resultants(assembly.field, field_id, operation)
    expected = {
        "N": [value.token() for value in expected_n],
        "M": [value.token() for value in expected_m],
        "Q": [value.token() for value in expected_q],
    }
    expected_strain = _expected_strain_tokens(assembly.field, field_id)
    exact = all(
        {key: row[key] for key in ("N", "M", "Q")} == expected
        and row["compatible"] == expected_strain
        and row["independent"] == expected_strain
        for row in recovered
    )
    return {
        "field": field_id,
        "physical_recovery_exact": exact,
        "physical_recovery_digest": sha256_bytes(canonical_bytes(recovered)),
        "pl_diagnostic_digest": vector_digest(pl),
        "recovery_keys": ["N", "M", "Q"],
        "numerical_excluded": ["PL_MULTIPLIER", "PL_CONSTRAINT", "PL_ENERGY", "RESIDUAL_MODE", "RESIDUAL_MODE_ENERGY"],
    }


def _rank_certificate(assembly: Assembly, fields: Mapping[str, Vector], precisions: Sequence[int]) -> dict[str, object]:
    rigid_ids = (
        "RIGID_TRANSLATION_T1",
        "RIGID_TRANSLATION_T2",
        "RIGID_TRANSLATION_T3",
        "RIGID_ROTATION_T1",
        "RIGID_ROTATION_T2",
        "RIGID_ROTATION_T3_MATCHED_DRILL",
    )
    rigid = [[fields[name][row] for name in rigid_ids] for row in range(24)]
    rigid_rank = matrix_rank(rigid)
    nulls = {name: vector_is_zero(matvec(assembly.k_total, fields[name])) for name in rigid_ids}
    complement = lexicographic_nullspace(transpose(rigid))
    quotient = matmul(matmul(transpose(complement), assembly.k_total), complement)
    basis = [rigid[row] + complement[row] for row in range(24)]
    basis_rank = matrix_rank(basis)
    orthogonal = matrix_is_zero(matmul(transpose(rigid), complement))
    cross = matrix_is_zero(matmul(matmul(transpose(rigid), assembly.k_total), complement))
    exact_zero = negative = positive = unresolved = 0
    try:
        pivots = ldl_pivots(quotient)
        signs = [sign_certificate(value, precisions) for value in pivots]
        positive = sum(row["classification"] == "POSITIVE" for row in signs)
        negative = sum(row["classification"] == "NEGATIVE" for row in signs)
        exact_zero = sum(row["classification"] == "ZERO" for row in signs)
        unresolved = sum(row["classification"] == "INCONCLUSIVE" for row in signs)
    except ZeroDivisionError:
        pivots, signs, exact_zero = [], [], 1
    rank_18 = (
        rigid_rank == 6
        and all(nulls.values())
        and len(complement[0]) == 18
        and orthogonal
        and basis_rank == 24
        and cross
        and positive == 18
        and negative == exact_zero == unresolved == 0
    )
    return {
        "quotient_rule": "LEXICOGRAPHIC_EXACT_RREF_NULLSPACE_OF_R_TRANSPOSE",
        "rigid_rank": rigid_rank,
        "complement_columns": len(complement[0]),
        "rigid_complement_orthogonal": orthogonal,
        "combined_basis_rank": basis_rank,
        "rigid_quotient_cross_zero": cross,
        "complement_digest": matrix_digest(complement),
        "quotient_digest": matrix_digest(quotient),
        "ldl_pivot_count": len(pivots),
        "ldl_pivot_signs": signs,
        "ldl_counts": {
            "exact_zero": exact_zero,
            "negative": negative,
            "positive": positive,
            "unresolved": unresolved,
        },
        "positive_quotient": positive == 18 and negative == exact_zero == unresolved == 0,
        "inconclusive": unresolved > 0,
        "rigid_nulls": nulls,
        "rank_18": rank_18,
        "psd": rank_18,
    }


def _stationary_certificate(assembly: Assembly) -> dict[str, object]:
    f = assembly.field
    q = [f.rational(Fraction((i % 11) - 5, (i % 5) + 1)) for i in range(24)]
    core, pl = _solve_internal(assembly, q)
    h38 = zeros(f, 38, 38)
    c38 = zeros(f, 38, 24)
    _add_block(h38, assembly.h_core, 0, 0)
    _add_block(h38, assembly.h_pl, 35, 35)
    inv38 = zeros(f, 38, 38)
    _add_block(inv38, assembly.inv_core, 0, 0)
    _add_block(inv38, assembly.inv_pl, 35, 35)
    _add_block(c38, assembly.c_core, 0, 0)
    _add_block(c38, assembly.c_pl, 35, 0)
    alpha38 = core + pl
    internal38 = [a + b for a, b in zip(matvec(h38, alpha38), matvec(c38, q))]
    schur38 = madd(
        mscale(matmul(matmul(transpose(c38), inv38), c38), -1),
        assembly.k_hg,
    )
    internal_core = [a + b for a, b in zip(matvec(assembly.h_core, core), matvec(assembly.c_core, q))]
    internal_pl = [a + b for a, b in zip(matvec(assembly.h_pl, pl), matvec(assembly.c_pl, q))]
    condensed = matvec(assembly.k_total, q)
    mixed = matvec(assembly.k_hg, q)
    for addition in (matvec(transpose(assembly.c_core), core), matvec(transpose(assembly.c_pl), pl)):
        mixed = [a + b for a, b in zip(mixed, addition)]
    mixed_energy = (
        dot(core, matvec(assembly.h_core, core)) / 2
        + dot(core, matvec(assembly.c_core, q))
        + dot(pl, matvec(assembly.h_pl, pl)) / 2
        + dot(pl, matvec(assembly.c_pl, q))
        + dot(q, matvec(assembly.k_hg, q)) / 2
    )
    condensed_energy = dot(q, condensed) / 2
    virtual = [f.rational(Fraction((index % 13) - 6, (index % 6) + 1)) for index in range(24)]
    return {
        "core_stationarity_exact": vector_is_zero(internal_core),
        "pl_stationarity_exact": vector_is_zero(internal_pl),
        "actual_38_stationarity_exact": vector_is_zero(internal38),
        "actual_38_inverse_exact": matmul(h38, inv38) == eye(f, 38),
        "condensed_energy_exact": mixed_energy == condensed_energy,
        "condensed_work_exact": dot(virtual, mixed) == dot(virtual, condensed),
        "condensed_residual_exact": all(a == b for a, b in zip(condensed, mixed)),
        "condensed_tangent_exact": schur38 == assembly.k_total,
        "symmetric_tangent_exact": assembly.k_total == transpose(assembly.k_total),
        "D38_digest": matrix_digest(h38),
    }


def _mode_certificate(assembly: Assembly, fields: Mapping[str, Vector]) -> dict[str, object]:
    modes = {}
    for name in ("COMMON_DRILL", "TRANSLATION_ONLY_SPIN", "RIGID_ROTATION_T3_MATCHED_DRILL", "ALTERNATING_DRILL"):
        q = fields[name]
        energies = {
            "core": dot(q, matvec(assembly.k_core, q)) / 2,
            "pl": dot(q, matvec(assembly.k_pl, q)) / 2,
            "hourglass": dot(q, matvec(assembly.k_hg, q)) / 2,
            "total": dot(q, matvec(assembly.k_total, q)) / 2,
        }
        modes[name] = {key: value.token() for key, value in energies.items()}
    common = fields["COMMON_DRILL"]
    spin = fields["TRANSLATION_ONLY_SPIN"]
    rigid = fields["RIGID_ROTATION_T3_MATCHED_DRILL"]
    alternating = fields["ALTERNATING_DRILL"]
    return {
        "energies": modes,
        "matched_state_vector_exact": all(a + b == c for a, b, c in zip(common, spin, rigid)),
        "matched_state_null_exact": vector_is_zero(matvec(assembly.k_total, rigid)),
        "common_drill_energetic": not dot(common, matvec(assembly.k_pl, common)).is_zero,
        "translation_spin_energetic": not dot(spin, matvec(assembly.k_pl, spin)).is_zero,
        "alternating_pl_null": dot(alternating, matvec(assembly.k_pl, alternating)).is_zero,
        "alternating_hg_energetic": not dot(alternating, matvec(assembly.k_hg, alternating)).is_zero,
    }


def _centre_certificate(assembly: Assembly, precisions: Sequence[int]) -> dict[str, object]:
    _, centre_det, _, _ = _centre_geometry_terms(assembly.field, assembly.coords)
    h4 = [assembly.field.rational(value) for value in (1, -1, 1, -1)]
    ones = [assembly.field.rational(1) for _ in range(4)]
    centre_sign = sign_certificate(centre_det, precisions)
    m_signs = [sign_certificate(value, precisions) for value in ldl_pivots(assembly.m_pl)]
    return {
        "centre_j_positive": centre_sign["classification"] == "POSITIVE",
        "centre_j_inconclusive": centre_sign["classification"] == "INCONCLUSIVE",
        "centre_taylor_exact": assembly.c_pl == matmul(assembly.m_pl, assembly.taylor_c)
        and len(assembly.taylor_c) == 3,
        "multiplier_gram_positive": all(row["classification"] == "POSITIVE" for row in m_signs),
        "multiplier_gram_inconclusive": any(row["classification"] == "INCONCLUSIVE" for row in m_signs),
        "residual_mode_exact": dot(assembly.gamma_hg, ones).is_zero
        and dot(assembly.gamma_hg, h4) == assembly.field.rational(1),
    }


def _recovery_certificate(assembly: Assembly, fields: Mapping[str, Vector]) -> dict[str, object]:
    q = fields["COMBINED_PHYSICAL_PATCH"]
    core, pl = _solve_internal(assembly, q)
    rows = _recovery_at_gauss(assembly, core, q)
    expected_strain = _expected_strain_tokens(assembly.field, "COMBINED_PHYSICAL_PATCH")
    return {
        "rows": rows,
        "compatible_all_exact": all(row["compatible"] == expected_strain for row in rows),
        "independent_all_exact": all(row["independent"] == expected_strain for row in rows),
        "numerical_separate": len(pl) == 3
        and all(
            set(row)
            == {
                "station_id",
                "compatible",
                "independent",
                "N",
                "M",
                "Q",
                "N_global",
                "M_global",
                "Q_global",
            }
            for row in rows
        ),
        "station_count": len(rows),
        "digest": sha256_bytes(canonical_bytes(rows)),
    }


def _case_certificate(
    base: Assembly,
    assembly: Assembly,
    operation: Operation,
    fields: Mapping[str, Vector],
    precisions: Sequence[int],
) -> dict[str, object]:
    jacobian_signs = [sign_certificate(value, precisions) for value in assembly.jacobians]
    rank = _rank_certificate(assembly, fields, precisions)
    stationary = _stationary_certificate(assembly)
    patches = [
        _patch_certificate(assembly, operation, fields, field_id)
        for field_id in ("MEMBRANE_PATCH", "BENDING_PATCH", "SHEAR_PATCH", "COMBINED_PHYSICAL_PATCH")
    ]
    rigid_patches = [
        _patch_certificate(assembly, operation, fields, field_id)
        for field_id in (
            "RIGID_TRANSLATION_T1",
            "RIGID_TRANSLATION_T2",
            "RIGID_TRANSLATION_T3",
            "RIGID_ROTATION_T1",
            "RIGID_ROTATION_T2",
            "RIGID_ROTATION_T3_MATCHED_DRILL",
        )
    ]
    recovery = _recovery_certificate(assembly, fields)
    expected_n, expected_m, expected_q = _expected_numbered_resultants(
        assembly.field, "COMBINED_PHYSICAL_PATCH", operation
    )
    expected_resultants = {
        "N": [value.token() for value in expected_n],
        "M": [value.token() for value in expected_m],
        "Q": [value.token() for value in expected_q],
    }
    recovery["physical_resultants_all_exact"] = all(
        {key: row[key] for key in ("N", "M", "Q")} == expected_resultants
        for row in recovery["rows"]  # type: ignore[union-attr]
    )
    internal_ranks = {
        "F": matrix_rank(assembly.f_core),
        "H": matrix_rank(assembly.h_strain),
        "Gq": matrix_rank(assembly.gq),
        "D35": matrix_rank(assembly.h_core),
        "M3": matrix_rank(assembly.m_pl),
    }
    return {
        "id": f"{assembly.geometry_id}::{assembly.operation_id}",
        "geometry": assembly.geometry_id,
        "operation": assembly.operation_id,
        "internal_invertible": internal_ranks
        == {"F": 14, "H": 21, "Gq": 14, "D35": 35, "M3": 3},
        "internal_ranks": internal_ranks,
        "jacobian_positive": all(row["classification"] == "POSITIVE" for row in jacobian_signs),
        "jacobian_inconclusive": any(row["classification"] == "INCONCLUSIVE" for row in jacobian_signs),
        "jacobian_signs": jacobian_signs,
        "core_internal_digest": matrix_digest(assembly.h_core),
        "pl_internal_digest": matrix_digest(assembly.h_pl),
        "condensed_digest": matrix_digest(assembly.k_total),
        "rank": rank,
        "stationary": stationary,
        "centre": _centre_certificate(assembly, precisions),
        "modes": _mode_certificate(assembly, fields),
        "patches": patches,
        "rigid_patches": rigid_patches,
        "recovery": recovery,
        "restricted_boundary": _boundary_certificate(base, assembly, operation, fields),
        "recovery_separated": all(row["recovery_keys"] == ["N", "M", "Q"] for row in patches),
    }


def _independent_rows(matrix: Matrix, count: int) -> tuple[int, ...]:
    """Return deterministic row indices spanning all columns, or fail closed."""

    if not matrix or len(matrix[0]) != count:
        raise ValueError("column-space certificate dimension mismatch")
    field = matrix[0][0].field
    work = [row[:] for row in matrix]
    row_ids = list(range(len(work)))
    selected: list[int] = []
    pivot_row = 0
    for column in range(count):
        pivot = next((i for i in range(pivot_row, len(work)) if not work[i][column].is_zero), None)
        if pivot is None:
            raise ZeroDivisionError("source reconstruction matrix lacks full column rank")
        work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        row_ids[pivot_row], row_ids[pivot] = row_ids[pivot], row_ids[pivot_row]
        inverse = work[pivot_row][column].inverse()
        work[pivot_row] = [value * inverse for value in work[pivot_row]]
        for i in range(len(work)):
            if i == pivot_row or work[i][column].is_zero:
                continue
            factor = work[i][column]
            work[i] = [a - factor * b for a, b in zip(work[i], work[pivot_row])]
        selected.append(row_ids[pivot_row])
        pivot_row += 1
    if len(selected) != count or field != matrix[0][0].field:
        raise AssertionError("invalid source reconstruction pivot certificate")
    return tuple(selected)


def _column_space_certificate(left: Matrix, right: Matrix) -> dict[str, object]:
    if len(left) != len(right) or len(left[0]) != len(right[0]):
        raise ValueError("column-space comparison shape mismatch")
    count = len(left[0])
    indices = _independent_rows(left, count)
    left_minor = [[left[i][j] for j in range(count)] for i in indices]
    right_minor = [[right[i][j] for j in range(count)] for i in indices]
    parameter_map = matmul(matrix_inverse(left_minor), right_minor)
    residual = madd(matmul(left, parameter_map), right, -1)
    return {
        "exact": matrix_is_zero(residual),
        "pivot_rows": list(indices),
        "parameter_map_digest": matrix_digest(parameter_map),
        "residual_digest": matrix_digest(residual),
    }


def _source_reconstruction_certificate(
    base: Assembly,
    transformed: Assembly,
    operation: Operation,
) -> dict[str, object]:
    field = base.field
    c_eng, c_res, shear_map, _, _ = _field_transport_maps(field, operation)
    stress_map = zeros(field, 8, 8)
    strain_map = zeros(field, 8, 8)
    _add_block(stress_map, c_res, 0, 0)
    _add_block(stress_map, mscale(c_res, operation.det), 3, 3)
    _add_block(stress_map, shear_map, 6, 6)
    _add_block(strain_map, c_eng, 0, 0)
    _add_block(strain_map, mscale(c_eng, operation.det), 3, 3)
    _add_block(strain_map, shear_map, 6, 6)
    bcentre, bdet0, br_bar, bs_bar = _centre_geometry_terms(field, base.coords)
    gcentre, gdet0, gr_bar, gs_bar = _centre_geometry_terms(field, transformed.coords)
    stress_base: Matrix = []
    stress_numbered: Matrix = []
    strain_base: Matrix = []
    strain_numbered: Matrix = []
    gauss_correspondence = True
    gauss = _gauss(field)
    for rg, sg in gauss:
        r0 = operation.A[0][0] * rg + operation.A[0][1] * sg
        s0 = operation.A[1][0] * rg + operation.A[1][1] * sg
        gauss_correspondence = gauss_correspondence and (r0, s0) in gauss
        _, dr0, ds0 = _shape(field, r0, s0)
        _, det0 = _jacobian(base.coords, dr0, ds0)
        ns0, ne0 = _source_mixed_fields(
            field, r0, s0, bcentre, det0, bdet0, br_bar, bs_bar
        )
        _, drg, dsg = _shape(field, rg, sg)
        _, detg = _jacobian(transformed.coords, drg, dsg)
        nsg, neg = _source_mixed_fields(
            field, rg, sg, gcentre, detg, gdet0, gr_bar, gs_bar
        )
        stress_base.extend(ns0)
        stress_numbered.extend(matmul(stress_map, nsg))
        strain_base.extend(ne0)
        strain_numbered.extend(matmul(strain_map, neg))
    stress = _column_space_certificate(stress_base, stress_numbered)
    strain = _column_space_certificate(strain_base, strain_numbered)
    return {
        "gauss_correspondence": gauss_correspondence,
        "stress14": stress,
        "strain21": strain,
        "exact": gauss_correspondence and bool(stress["exact"]) and bool(strain["exact"]),
    }


def _covariance_certificate(
    base: Assembly,
    transformed: Assembly,
    operation: Operation,
    fields: Mapping[str, Vector],
) -> dict[str, object]:
    field = base.field
    source_reconstruction = _source_reconstruction_certificate(base, transformed, operation)
    p24 = _permutation24(field, operation)
    stiffness_residual = madd(
        matmul(matmul(transpose(p24), transformed.k_total_global), p24),
        base.k_total_global,
        -1,
    )
    component_stiffness = {
        name: matrix_is_zero(
            madd(matmul(matmul(transpose(p24), numbered), p24), original, -1)
        )
        for name, original, numbered in (
            ("WG_PHYSICAL", base.k_core_global, transformed.k_core_global),
            ("PL_NUMERICAL", base.k_pl_global, transformed.k_pl_global),
            ("RESIDUAL_NUMERICAL", base.k_hg_global, transformed.k_hg_global),
        )
    }
    ahat = _fraction_matrix(
        field,
        (
            (operation.A[0][0], operation.A[0][1], 0),
            (operation.A[1][0], operation.A[1][1], 0),
            (0, 0, operation.det),
        ),
    )
    frame_residual = madd(transformed.frame, matmul(base.frame, ahat), -1)
    physical_projector_residual = madd(
        transformed.physical_projector,
        matmul(matmul(p24, base.physical_projector), transpose(p24)),
        -1,
    )
    drill_projector_residual = madd(
        transformed.drill_projector,
        matmul(matmul(p24, base.drill_projector), transpose(p24)),
        -1,
    )

    local5 = _numbered_local5_map(field, operation)
    drill_map = _numbered_drill_map(field, operation)
    t5_residual = madd(matmul(transformed.t5, local5), matmul(p24, base.t5), -1)
    qd_residual = madd(matmul(transformed.qd, drill_map), matmul(p24, base.qd), -1)
    base_p = _frozen_physical_load(field)
    numbered_p = matvec(local5, base_p)
    load_base = matvec(base.t5, base_p)
    load_numbered = matvec(transformed.t5, numbered_p)
    load_residual = [a - b for a, b in zip(matvec(transpose(p24), load_numbered), load_base)]

    a_bc_base = transpose(base.t5)
    a_bc_numbered = matmul(a_bc_base, transpose(p24))
    support_map_exact = matrix_is_zero(matmul(a_bc_numbered, transformed.qd))
    zero24 = [field.rational() for _ in range(24)]
    multiplier = base_p[:]
    reaction_base = matvec(transpose(a_bc_base), multiplier)
    reaction_numbered = matvec(transpose(a_bc_numbered), multiplier)
    reaction_transport_exact = reaction_numbered == matvec(p24, reaction_base)
    kkt_base = vector_is_zero(
        [
            a + b - c
            for a, b, c in zip(
                matvec(base.k_total_global, zero24), reaction_base, load_base
            )
        ]
    ) and vector_is_zero(matvec(a_bc_base, zero24))
    kkt_numbered = vector_is_zero(
        [
            a + b - c
            for a, b, c in zip(
                matvec(transformed.k_total_global, zero24), reaction_numbered, load_numbered
            )
        ]
    ) and vector_is_zero(matvec(a_bc_numbered, zero24))
    virtual_base = [
        field.rational(Fraction((index % 9) - 4, (index % 4) + 1))
        for index in range(24)
    ]
    virtual_numbered = matvec(p24, virtual_base)
    support_work_exact = (
        dot(reaction_base, virtual_base) == dot(multiplier, matvec(a_bc_base, virtual_base))
        and dot(reaction_numbered, virtual_numbered)
        == dot(multiplier, matvec(a_bc_numbered, virtual_numbered))
        and dot(reaction_base, virtual_base) == dot(reaction_numbered, virtual_numbered)
    )
    support_reaction_exact = (
        reaction_transport_exact
        and vector_is_zero(matvec(transpose(base.qd), reaction_base))
        and vector_is_zero(matvec(transpose(transformed.qd), reaction_numbered))
        and support_work_exact
    )

    q_local = _field_q(base, "COMBINED_PHYSICAL_PATCH")
    q_base = matvec(base.local_to_global, q_local)
    q_numbered = matvec(p24, q_base)
    q_rebuilt = matvec(transformed.local_to_global, fields["COMBINED_PHYSICAL_PATCH"])
    residual_base = matvec(base.k_total_global, q_base)
    residual_numbered = matvec(transformed.k_total_global, q_numbered)
    residual_residual = [a - b for a, b in zip(matvec(transpose(p24), residual_numbered), residual_base)]

    c_eng, c_res, shear_map, s_map, lambda_map = _field_transport_maps(field, operation)
    tensor_work = matmul(transpose(c_res), c_eng) == eye(field, 3)
    shear_work = matmul(transpose(shear_map), shear_map) == eye(field, 2)
    pl_gram = matmul(matmul(transpose(lambda_map), base.h_pl), lambda_map)
    pl_gram_exact = pl_gram == transformed.h_pl
    c_pl_base_global = matmul(base.c_pl, transpose(base.local_to_global))
    c_pl_numbered_global = matmul(transformed.c_pl, transpose(transformed.local_to_global))
    pl_work_exact = matmul(c_pl_numbered_global, p24) == matmul(transpose(lambda_map), c_pl_base_global)
    c_base = matmul(matrix_inverse(mscale(base.h_pl, -6)), base.c_pl)
    c_numbered = matmul(matrix_inverse(mscale(transformed.h_pl, -6)), transformed.c_pl)
    base_c_coeff = matvec(c_base, q_local)
    numbered_c_coeff = matvec(c_numbered, fields["COMBINED_PHYSICAL_PATCH"])
    pl_constraint_transport = numbered_c_coeff == matvec(transpose(lambda_map), base_c_coeff)
    _, multiplier_base = _solve_internal(base, q_local)
    _, multiplier_numbered = _solve_internal(
        transformed, fields["COMBINED_PHYSICAL_PATCH"]
    )
    multiplier_transport_exact = multiplier_base == matvec(
        lambda_map, multiplier_numbered
    )
    compliance_transport_exact = dot(
        multiplier_base, matvec(base.m_pl, multiplier_base)
    ) == dot(
        multiplier_numbered, matvec(transformed.m_pl, multiplier_numbered)
    )
    drill_base = [q_local[6 * node + 5] for node in range(4)]
    drill_numbered = [
        fields["COMBINED_PHYSICAL_PATCH"][6 * node + 5] for node in range(4)
    ]
    residual_coordinate_base = dot(base.gamma_hg, drill_base)
    residual_coordinate_numbered = dot(transformed.gamma_hg, drill_numbered)
    residual_mode_transport_exact = (
        residual_coordinate_base == residual_coordinate_numbered
        and base.area_hg == transformed.area_hg
    )
    tangent_base = [[base.frame[i][j] for j in range(2)] for i in range(3)]
    tangent_numbered = [[transformed.frame[i][j] for j in range(2)] for i in range(3)]

    def tensor_reconstruct(tangent: Matrix, values: Sequence[Alg]) -> Matrix:
        local = [[values[0], values[2]], [values[2], values[1]]]
        return matmul(matmul(tangent, local), transpose(tangent))

    n_g = [field.rational(2), field.rational(-3), field.rational(5)]
    m_g = [field.rational(-1), field.rational(4), field.rational(Fraction(2, 3))]
    q_g = [field.rational(Fraction(3, 2)), field.rational(Fraction(-5, 4))]
    n_0 = matvec(c_res, n_g)
    m_0 = [operation.det * value for value in matvec(c_res, m_g)]
    q_0 = matvec(shear_map, q_g)
    recovery_reconstruction = (
        tensor_reconstruct(tangent_base, n_0) == tensor_reconstruct(tangent_numbered, n_g)
        and tensor_reconstruct(tangent_base, m_0) == tensor_reconstruct(tangent_numbered, m_g)
        and matvec(tangent_base, q_0) == matvec(tangent_numbered, q_g)
    )
    gauss = _gauss(field)
    corresponding_gauss = True
    point_work_exact = True
    pl_point_exact = True
    lambda_g = [field.rational(2), field.rational(-1), field.rational(3)]
    lambda_0 = matvec(lambda_map, lambda_g)
    for r_g, s_g in gauss:
        mapped = (
            operation.A[0][0] * r_g + operation.A[0][1] * s_g,
            operation.A[1][0] * r_g + operation.A[1][1] * s_g,
        )
        corresponding_gauss = corresponding_gauss and mapped in gauss
        e_g = [field.rational(1) + r_g, field.rational(2) - s_g, r_g + s_g]
        n_g_point = [field.rational(3) - s_g, field.rational(-2) + r_g, field.rational(Fraction(1, 2)) + r_g - s_g]
        k_g = [field.rational(-1) + s_g, field.rational(4) + r_g, r_g - 2 * s_g]
        m_g_point = [field.rational(2) + r_g, field.rational(1) - s_g, field.rational(-3) + r_g + s_g]
        shear_g = [field.rational(1) + r_g, field.rational(2) + s_g]
        q_g_point = [field.rational(3) - s_g, field.rational(-1) + r_g]
        e_0 = matvec(c_eng, e_g)
        n_0_point = matvec(c_res, n_g_point)
        k_0 = [operation.det * value for value in matvec(c_eng, k_g)]
        m_0_point = [operation.det * value for value in matvec(c_res, m_g_point)]
        shear_0 = matvec(shear_map, shear_g)
        q_0_point = matvec(shear_map, q_g_point)
        ell_g = [field.rational(1), r_g, s_g]
        ell_0 = [field.rational(1), mapped[0], mapped[1]]
        pl_point_exact = pl_point_exact and (
            dot(lambda_0, ell_0) == operation.det * dot(lambda_g, ell_g)
            and dot(base_c_coeff, ell_0) == operation.det * dot(numbered_c_coeff, ell_g)
        )
        point_work_exact = point_work_exact and (
            dot(n_0_point, e_0) == dot(n_g_point, e_g)
            and dot(m_0_point, k_0) == dot(m_g_point, k_g)
            and dot(q_0_point, shear_0) == dot(q_g_point, shear_g)
        )
    field_work_exact = (
        tensor_work
        and shear_work
        and pl_gram_exact
        and pl_work_exact
        and pl_constraint_transport
        and multiplier_transport_exact
        and compliance_transport_exact
        and residual_mode_transport_exact
        and pl_point_exact
        and corresponding_gauss
        and point_work_exact
        and recovery_reconstruction
    )
    exact = all(
        (
            matrix_is_zero(stiffness_residual),
            all(component_stiffness.values()),
            matrix_is_zero(frame_residual),
            matrix_is_zero(physical_projector_residual),
            matrix_is_zero(drill_projector_residual),
            vector_is_zero(load_residual),
            support_map_exact,
            kkt_base,
            kkt_numbered,
            support_reaction_exact,
            vector_is_zero(residual_residual),
            q_numbered == q_rebuilt,
            matrix_is_zero(t5_residual),
            matrix_is_zero(qd_residual),
            pl_constraint_transport,
            multiplier_transport_exact,
            compliance_transport_exact,
            residual_mode_transport_exact,
            bool(source_reconstruction["exact"]),
            field_work_exact,
        )
    )
    return {
        "geometry": base.geometry_id,
        "operation": operation.id,
        "exact_zero": exact,
        "equation7_frame": matrix_is_zero(frame_residual),
        "stiffness": matrix_is_zero(stiffness_residual),
        "component_stiffness": component_stiffness,
        "residual": vector_is_zero(residual_residual),
        "load": vector_is_zero(load_residual),
        "support": support_map_exact,
        "support_solution": kkt_base and kkt_numbered,
        "support_reaction": support_reaction_exact,
        "T5_QD_projectors": matrix_is_zero(t5_residual)
        and matrix_is_zero(qd_residual)
        and matrix_is_zero(physical_projector_residual)
        and matrix_is_zero(drill_projector_residual),
        "epsilon_N_work": tensor_work,
        "kappa_M_pseudo_work": tensor_work,
        "gamma_Q_pseudo_work": shear_work,
        "PL_multiplier_gram_work": pl_gram_exact
        and pl_work_exact
        and pl_constraint_transport
        and pl_point_exact
        and multiplier_transport_exact
        and compliance_transport_exact,
        "residual_mode_transport": residual_mode_transport_exact,
        "corresponding_gauss_reconstruction": corresponding_gauss and point_work_exact,
        "physical_recovery_reconstruction": recovery_reconstruction,
        "source_stress_strain_reconstruction": source_reconstruction,
        "residual_digest": matrix_digest(stiffness_residual),
    }


def _global_covariance_certificate(
    base: Assembly,
    transformed: Assembly,
    operation: Operation,
    transform: Mapping[str, object],
) -> dict[str, object]:
    field = base.field
    rotation = _fraction_matrix(field, transform["R_star"])  # type: ignore[arg-type]
    translation = [field.rational(F(value)) for value in transform["b_star"]]  # type: ignore[index]
    rotation_orthogonal = matmul(transpose(rotation), rotation) == eye(field, 3)
    rotation_det = (
        rotation[0][0] * (rotation[1][1] * rotation[2][2] - rotation[1][2] * rotation[2][1])
        - rotation[0][1] * (rotation[1][0] * rotation[2][2] - rotation[1][2] * rotation[2][0])
        + rotation[0][2] * (rotation[1][0] * rotation[2][1] - rotation[1][1] * rotation[2][0])
    )
    proper_rotation = rotation_orthogonal and rotation_det == field.rational(1)
    g_r = zeros(field, 24, 24)
    for node in range(4):
        _add_block(g_r, rotation, 6 * node, 6 * node)
        _add_block(g_r, rotation, 6 * node + 3, 6 * node + 3)
    p24 = _permutation24(field, operation)
    permutation_rotation_commute = matmul(p24, g_r) == matmul(g_r, p24)
    frame_exact = transformed.frame == matmul(rotation, base.frame)
    stiffness_exact = transformed.k_total_global == matmul(matmul(g_r, base.k_total_global), transpose(g_r))
    component_stiffness = {
        name: numbered == matmul(matmul(g_r, original), transpose(g_r))
        for name, original, numbered in (
            ("WG_PHYSICAL", base.k_core_global, transformed.k_core_global),
            ("PL_NUMERICAL", base.k_pl_global, transformed.k_pl_global),
            ("RESIDUAL_NUMERICAL", base.k_hg_global, transformed.k_hg_global),
        )
    }
    t5_exact = transformed.t5 == matmul(g_r, base.t5)
    qd_exact = transformed.qd == matmul(g_r, base.qd)
    physical_projector_exact = transformed.physical_projector == matmul(
        matmul(g_r, base.physical_projector), transpose(g_r)
    )
    drill_projector_exact = transformed.drill_projector == matmul(
        matmul(g_r, base.drill_projector), transpose(g_r)
    )
    load_base = matvec(base.t5, _frozen_physical_load(field))
    load_transformed = matvec(transformed.t5, _frozen_physical_load(field))
    load_exact = load_transformed == matvec(g_r, load_base)
    nodes_exact = all(
        transformed.nodes[node][i]
        == sum((rotation[i][j] * base.nodes[node][j] for j in range(3)), field.rational()) + translation[i]
        for node in range(4)
        for i in range(3)
    )
    edge_differences_exact = all(
        transformed.nodes[node][i] - transformed.nodes[0][i]
        == sum((rotation[i][j] * (base.nodes[node][j] - base.nodes[0][j]) for j in range(3)), field.rational())
        for node in range(1, 4)
        for i in range(3)
    )
    q_local = _field_q(base, "COMBINED_PHYSICAL_PATCH")
    q_base = matvec(base.local_to_global, q_local)
    q_rebuilt = matvec(transformed.local_to_global, _field_q(transformed, "COMBINED_PHYSICAL_PATCH"))
    q_exact = q_rebuilt == matvec(g_r, q_base)
    residual_base = matvec(base.k_total_global, q_base)
    residual_transformed = matvec(transformed.k_total_global, q_rebuilt)
    residual_exact = residual_transformed == matvec(g_r, residual_base)
    physical_internal_base = matvec(base.k_core_global, q_base)
    physical_internal_star = matvec(transformed.k_core_global, q_rebuilt)
    pl_internal_base = matvec(base.k_pl_global, q_base)
    pl_internal_star = matvec(transformed.k_pl_global, q_rebuilt)
    residual_mode_base = matvec(base.k_hg_global, q_base)
    residual_mode_star = matvec(transformed.k_hg_global, q_rebuilt)
    numerical_transport_exact = (
        physical_internal_star == matvec(g_r, physical_internal_base)
        and pl_internal_star == matvec(g_r, pl_internal_base)
        and residual_mode_star == matvec(g_r, residual_mode_base)
        and dot(q_rebuilt, physical_internal_star) == dot(q_base, physical_internal_base)
        and dot(q_rebuilt, pl_internal_star) == dot(q_base, pl_internal_base)
        and dot(q_rebuilt, residual_mode_star) == dot(q_base, residual_mode_base)
    )

    p_f = _frozen_physical_load(field)
    a_bc = transpose(base.t5)
    a_bc_star = matmul(a_bc, transpose(g_r))
    support_exact = a_bc_star == transpose(transformed.t5)
    zero24 = [field.rational() for _ in range(24)]
    multiplier = p_f[:]
    reaction = matvec(transpose(a_bc), multiplier)
    reaction_star = matvec(transpose(a_bc_star), multiplier)
    reaction_exact = reaction_star == matvec(g_r, reaction)
    kkt_base = vector_is_zero(
        [
            a + b - c
            for a, b, c in zip(
                matvec(base.k_total_global, zero24), reaction, load_base
            )
        ]
    ) and vector_is_zero(matvec(a_bc, zero24))
    kkt_star = vector_is_zero(
        [
            a + b - c
            for a, b, c in zip(
                matvec(transformed.k_total_global, zero24), reaction_star, load_transformed
            )
        ]
    ) and vector_is_zero(matvec(a_bc_star, zero24))
    reaction_drill_exact = vector_is_zero(matvec(transpose(base.qd), reaction)) and vector_is_zero(
        matvec(transpose(transformed.qd), reaction_star)
    )
    reaction_projector_exact = vector_is_zero(matvec(base.drill_projector, reaction)) and vector_is_zero(
        matvec(transformed.drill_projector, reaction_star)
    )
    virtual_base = [
        field.rational(Fraction((index % 9) - 4, (index % 4) + 1))
        for index in range(24)
    ]
    virtual_star = matvec(g_r, virtual_base)
    support_work_exact = (
        dot(reaction, virtual_base) == dot(multiplier, matvec(a_bc, virtual_base))
        and dot(reaction_star, virtual_star) == dot(multiplier, matvec(a_bc_star, virtual_star))
        and dot(reaction, virtual_base) == dot(reaction_star, virtual_star)
    )
    n_values, m_values, q_values = _expected_resultants(field, "COMBINED_PHYSICAL_PATCH")

    def reconstructed(assembly: Assembly, tensor_values: Sequence[Alg], vector_values: Sequence[Alg]) -> tuple[Matrix, Vector]:
        tangent = [[assembly.frame[i][j] for j in range(2)] for i in range(3)]
        local_tensor = [[tensor_values[0], tensor_values[2]], [tensor_values[2], tensor_values[1]]]
        global_tensor = matmul(matmul(tangent, local_tensor), transpose(tangent))
        global_vector = [assembly.frame[i][0] * vector_values[0] + assembly.frame[i][1] * vector_values[1] for i in range(3)]
        return global_tensor, global_vector

    n_base, q_base_recovery = reconstructed(base, n_values, q_values)
    n_star, q_star_recovery = reconstructed(transformed, n_values, q_values)
    m_base, _ = reconstructed(base, m_values, q_values)
    m_star, _ = reconstructed(transformed, m_values, q_values)
    recovery_exact = (
        n_star == matmul(matmul(rotation, n_base), transpose(rotation))
        and m_star == matmul(matmul(rotation, m_base), transpose(rotation))
        and q_star_recovery == matvec(rotation, q_base_recovery)
    )
    core_base, multiplier_base = _solve_internal(base, q_local)
    q_local_star = _field_q(transformed, "COMBINED_PHYSICAL_PATCH")
    core_star, multiplier_star = _solve_internal(transformed, q_local_star)
    recovered_base = _recovery_at_gauss(base, core_base, q_local)
    recovered_star = _recovery_at_gauss(transformed, core_star, q_local_star)

    def token_matrix(values: object) -> Matrix:
        return [
            [Alg(field, tuple(F(item) for item in token)) for token in row]
            for row in values  # type: ignore[union-attr]
        ]

    def token_vector(values: object) -> Vector:
        return [Alg(field, tuple(F(item) for item in token)) for token in values]  # type: ignore[union-attr]

    actual_recovery_exact = len(recovered_base) == len(recovered_star) == 4
    for base_row, star_row in zip(recovered_base, recovered_star):
        n_base_actual = token_matrix(base_row["N_global"])
        m_base_actual = token_matrix(base_row["M_global"])
        q_base_actual = token_vector(base_row["Q_global"])
        n_star_actual = token_matrix(star_row["N_global"])
        m_star_actual = token_matrix(star_row["M_global"])
        q_star_actual = token_vector(star_row["Q_global"])
        actual_recovery_exact = actual_recovery_exact and (
            n_star_actual == matmul(matmul(rotation, n_base_actual), transpose(rotation))
            and m_star_actual == matmul(matmul(rotation, m_base_actual), transpose(rotation))
            and q_star_actual == matvec(rotation, q_base_actual)
            and base_row["compatible"] == star_row["compatible"]
            and base_row["independent"] == star_row["independent"]
            and base_row["N"] == star_row["N"]
            and base_row["M"] == star_row["M"]
            and base_row["Q"] == star_row["Q"]
        )
    multiplier_transport_exact = multiplier_base == multiplier_star
    return {
        "equation7_frame": frame_exact,
        "proper_global_rotation": proper_rotation,
        "stiffness": stiffness_exact,
        "component_stiffness": component_stiffness,
        "T5": t5_exact,
        "QD": qd_exact,
        "physical_projector": physical_projector_exact,
        "drill_projector": drill_projector_exact,
        "load": load_exact,
        "residual_reaction": residual_exact,
        "numerical_diagnostics": numerical_transport_exact and multiplier_transport_exact,
        "support": support_exact,
        "support_solution": kkt_base and kkt_star,
        "support_reaction": reaction_exact
        and reaction_drill_exact
        and reaction_projector_exact
        and support_work_exact,
        "nodes_R_X_plus_b": nodes_exact,
        "origin_translation_removed_by_differences": edge_differences_exact,
        "permutation_rotation_commute": permutation_rotation_commute,
        "rebuilt_patch_field": q_exact,
        "recovery_global_reconstruction": recovery_exact and actual_recovery_exact,
        "PL_multiplier_transport": multiplier_transport_exact,
        "exact_zero": all(
            (
                frame_exact,
                proper_rotation,
                stiffness_exact,
                all(component_stiffness.values()),
                t5_exact,
                qd_exact,
                physical_projector_exact,
                drill_projector_exact,
                load_exact,
                nodes_exact,
                edge_differences_exact,
                permutation_rotation_commute,
                q_exact,
                residual_exact,
                numerical_transport_exact,
                support_exact,
                kkt_base,
                kkt_star,
                reaction_exact,
                reaction_drill_exact,
                reaction_projector_exact,
                support_work_exact,
                recovery_exact,
                actual_recovery_exact,
                multiplier_transport_exact,
            )
        ),
    }


def _frame_static_certificate(contracts: Mapping[str, object]) -> dict[str, object]:
    frame = contracts["e4_pl_q1r_frame_contract"]
    operations = _operations(frame)  # type: ignore[arg-type]
    natural = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    rows = []
    for operation in operations:
        mapped = tuple(
            (
                operation.A[0][0] * r + operation.A[0][1] * s,
                operation.A[1][0] * r + operation.A[1][1] * s,
            )
            for r, s in natural
        )
        expected = tuple(natural[index] for index in operation.permutation)
        ata = (
            (
                operation.A[0][0] ** 2 + operation.A[1][0] ** 2,
                operation.A[0][0] * operation.A[0][1] + operation.A[1][0] * operation.A[1][1],
            ),
            (
                operation.A[0][1] * operation.A[0][0] + operation.A[1][1] * operation.A[1][0],
                operation.A[0][1] ** 2 + operation.A[1][1] ** 2,
            ),
        )
        determinant = operation.A[0][0] * operation.A[1][1] - operation.A[0][1] * operation.A[1][0]
        rows.append(
            {
                "id": operation.id,
                "natural_node_map_exact": mapped == expected,
                "orthogonal_exact": ata == ((1, 0), (0, 1)),
                "determinant_exact": determinant == operation.det,
                "lifted_determinant_one": determinant * operation.det == 1,
            }
        )
    return {
        "equation_7_rows": rows,
        "all_exact": all(all(value is True for key, value in row.items() if key != "id") for row in rows),
        "complete_reversal": "MD",
        "operation_count": len(rows),
        "reflection_repair": "FORBIDDEN",
    }


def static_transcription() -> dict[str, object]:
    contracts = _contracts()
    source_text = REFERENCE_PATH.read_text(encoding="utf-8")
    source_ast = ast.parse(source_text)
    functions = {node.name: node for node in source_ast.body if isinstance(node, ast.FunctionDef)}
    classes = {node.name: node for node in source_ast.body if isinstance(node, ast.ClassDef)}
    if len(STATIC_OBLIGATION_SYMBOLS) != 25:
        raise AssertionError("reference scaffolding must preserve all 25 frozen Q1S mechanics obligations")
    available_symbols = set(functions) | set(classes)
    for obligation, owners in STATIC_OBLIGATION_SYMBOLS.items():
        names = [owners] if isinstance(owners, str) else owners
        if not names or any(name not in available_symbols for name in names):
            raise AssertionError(f"static obligation owner missing: {obligation}")
    mixed_ast = functions["_source_mixed_fields"]
    transform_calls = [
        node
        for node in ast.walk(mixed_ast)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_tensor_transform"
    ]
    assemble_ast = functions["assemble"]
    gauss_curl_projection = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_integrate_pair"
        and "cdrill" in ast.unparse(node)
        for node in ast.walk(assemble_ast)
    )
    c_pl_assignments = [
        node
        for node in ast.walk(assemble_ast)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "c_pl" for target in node.targets)
    ]
    taylor_assignments = [
        node
        for node in ast.walk(assemble_ast)
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "taylor_c" for target in node.targets)
    ]
    taylor_ast = functions["_drill_taylor_rows"]
    context_text = ast.unparse(functions["_equation7_context"])
    generator_schedule = [
        "field.with_sqrt(field.rational(l1))",
        "field.with_sqrt(field.rational(l2))",
        "field.with_sqrt(_dot3(plus, plus))",
        "field.with_sqrt(_dot3(diagonal_cross, diagonal_cross))",
        "field.with_sqrt(field.rational(3))",
    ]
    offsets = [context_text.find(token) for token in generator_schedule]
    if any(offset < 0 for offset in offsets) or offsets != sorted(offsets):
        raise AssertionError("Q1T g1..g5 generator schedule is absent or reordered")
    source_core_fidelity = {
        "policy": SOURCE_CORE_TRANSFORM_POLICY,
        "centre_J_for_T_sigma": "_tensor_transform(centre_jacobian, 2, 1)" in source_text,
        "centre_J_for_T_epsilon": "_tensor_transform(centre_jacobian, 1, 2)" in source_text,
        "centre_J_for_T_tilde": "t_tilde = centre_jacobian" in source_text,
        "only_enrichment_has_j0_over_j": "centre_det / current_det" in source_text,
        "centroid_offsets_present": "s - s_bar" in source_text and "r - r_bar" in source_text,
        "centroid_offsets_from_bilinear_det": "jr / (3 * j0), js / (3 * j0)" in source_text,
        "pointwise_J_seed_transform_rejected": len(transform_calls) == 2
        and all(isinstance(call.args[0], ast.Name) and call.args[0].id == "centre_jacobian" for call in transform_calls),
    }
    pl_fidelity = {
        "policy": PL_PROJECTION_POLICY,
        "centre_taylor_rows_present": any(isinstance(node, ast.FunctionDef) and node.name == "_drill_taylor_rows" for node in ast.walk(source_ast)),
        "B_equals_M_C": len(taylor_assignments) == 1
        and ast.unparse(taylor_assignments[0].value) == "_drill_taylor_rows(field, coords)"
        and len(c_pl_assignments) == 1
        and ast.unparse(c_pl_assignments[0].value) == "matmul(m_pl, taylor_c)",
        "faulty_rs_row_absent": "rows = [[zero for _ in range(24)] for _ in range(3)]" in ast.unparse(taylor_ast),
        "gauss_L2_full_curl_projection_rejected": not gauss_curl_projection,
    }
    if not all(value is True for key, value in source_core_fidelity.items() if key != "policy"):
        raise AssertionError("static source-core fidelity assertion failed")
    if not all(value is True for key, value in pl_fidelity.items() if key != "policy"):
        raise AssertionError("static PL identity assertion failed")
    identities = {
        relative: {"bytes": len((ROOT / relative).read_bytes()), "sha256": sha256_path(ROOT / relative)}
        for relative in PLAN_INPUTS
    }
    inherited = {
        relative: {"bytes": len((ROOT / relative).read_bytes()), "sha256": sha256_path(ROOT / relative)}
        for relative in INHERITED_CORE_INPUTS
    }
    mechanics = {
        relative: {"bytes": len((ROOT / relative).read_bytes()), "sha256": sha256_path(ROOT / relative)}
        for relative in MECHANICS_INPUTS
    }
    frame = _frame_static_certificate(contracts)
    material = contracts["e4_pl_q1r_material_contract"]
    cases = contracts["e4_pl_q1r_cases"]
    core = contracts["e4_core_cases"]
    return {
        "schema": "anysolver.s4.e4-pl-q1t-reference-static-transcription-v1",
        "candidate_id": CANDIDATE_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "plan_commit": PLAN_COMMIT,
        "plan_tree": PLAN_TREE,
        "input_identities": identities,
        "mechanics_input_identities": mechanics,
        "inherited_accepted_core_identities": inherited,
        "inherited_core": {
            "schema": core["schema"],
            "terminal": core["expected"]["terminal"],
            "stress_parameters": core["dimensions"]["stress_parameters"],
            "strain_parameters": core["dimensions"]["strain_parameters"],
            "internal_order": core["source_exact_operator"]["N_sigma"]["parameter_order"]
            + core["source_exact_operator"]["N_epsilon"]["parameter_order"],
            "D": core["source_exact_operator"]["matrices"]["D"],
            "Q": core["source_exact_operator"]["matrices"]["Q"],
            "transformations": core["source_exact_operator"]["transformations"],
        },
        "source_core_fidelity": source_core_fidelity,
        "pl_fidelity": pl_fidelity,
        "exact_backend": {
            "domain": "STDLIB_FIELD_ALG_QUADRATIC_TOWER",
            "expression_dag": "INDEPENDENT_CANONICAL_RATIONAL_POSITIVE_ROOT_DAG",
            "formal_degree_maximum": 32,
            "generator_schedule": ["g1", "g2", "g3", "g4", "g5"],
            "ordered_sign_precisions": [256, 512, 1024],
        },
        "static_obligation_symbols": STATIC_OBLIGATION_SYMBOLS,
        "geometry_frame_fidelity": {
            "actual_3d_nodes": True,
            "R_star_plus_translation_constructed": True,
            "equation7_both_normalized_diagonals": True,
            "numbered_frame_rebuilt_per_operation": True,
            "T5_QD_projectors_global_embedding": True,
        },
        "frame": frame,
        "stationary_field_count": material["formulation_identity"]["stationary_field_count"],
        "core_internal_variables": material["formulation_identity"]["core_internal_variables"],
        "pl_multiplier_variables": material["formulation_identity"]["pl_multiplier_variables"],
        "registered_geometry_count": len(contracts["e4_pl_q1r_geometry_contract"]["geometries"]) + 1,
        "registered_numbered_case_count": (len(contracts["e4_pl_q1r_geometry_contract"]["geometries"]) + 1)
        * len(_operations(contracts["e4_pl_q1r_frame_contract"])),
        "registered_station_count": (len(contracts["e4_pl_q1r_geometry_contract"]["geometries"]) + 1)
        * len(_operations(contracts["e4_pl_q1r_frame_contract"]))
        * len(GAUSS_IDS),
        "registered_rigid_count": len(cases["rigid_fields"]),
        "mechanics_executed": False,
    }


def toy_exact_backend_certificate() -> dict[str, object]:
    """Exercise only synthetic algebra; no registered geometry is reachable."""

    field = Field(())
    field, root2 = field.with_sqrt(field.rational(2))
    root2 = root2.lift(field)
    nested_radicand = field.rational(3) + root2
    field, nested = field.with_sqrt(nested_radicand)
    root2 = root2.lift(field)
    nested_radicand = nested_radicand.lift(field)
    one = field.rational(1)
    cancellation = (nested * nested - nested_radicand) + (root2 * root2 - 2)
    inverse = (one + nested).inverse()
    toy_matrix = [[one, root2], [root2, field.rational(3)]]
    nested_sign = sign_certificate(nested, (256, 512, 1024))
    zero_sign = sign_certificate(cancellation, (256, 512, 1024))
    node_operations = sorted(
        {
            node.operation
            for node in _walk_expression_dag(expression_dag(nested))
        }
    )
    payload = {
        "schema": "anysolver.s4.e4-pl-q1t-reference-toy-exact-backend-v1",
        "candidate_id": CANDIDATE_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "domain_equalities": {
            "exact_cancellation": cancellation.is_zero,
            "nested_square": nested * nested == nested_radicand,
            "inverse": (one + nested) * inverse == one,
        },
        "matrix_rank": matrix_rank(toy_matrix),
        "nested_positive": nested_sign["classification"] == "POSITIVE",
        "zero_never_called_intervals": zero_sign["classification"] == "ZERO"
        and zero_sign["intervals"] == [],
        "expression_dag_operations": node_operations,
        "mechanics_executed": False,
    }
    payload["deterministic_sha256"] = sha256_bytes(canonical_bytes(payload))
    return payload


def _walk_expression_dag(root: ExpressionNode) -> Iterator[ExpressionNode]:
    seen: set[ExpressionNode] = set()
    pending = [root]
    while pending:
        node = pending.pop()
        if node in seen:
            continue
        seen.add(node)
        yield node
        pending.extend(value for value in node.arguments if isinstance(value, ExpressionNode))


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-c", "core.excludesFile=/dev/null", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _require_keys(value: Mapping[str, object], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise PermissionError(f"{label} keys differ from the frozen contract schema")


Q1S_CLOSEOUT_COMMIT = "914a9a633c585d45a419d97f92b4faf7fa1e4486"
REVIEW_KEYS = {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"}
AUTHORITY_KEYS = {
    "authorization",
    "candidate_id",
    "commit",
    "contract_review_sha256",
    "execution_contract_sha256",
    "environment_sha256",
    "implementation_review_sha256",
    "plan_review_sha256",
    "review_verdicts",
    "runner_ids",
    "schema",
    "study_id",
    "tree",
}
CONTRACT_KEYS = {
    "agreement",
    "authorization",
    "candidate_id",
    "commit_ancestry",
    "environment",
    "implementation_inputs",
    "inherited_inputs",
    "output_absences",
    "plan_inputs",
    "production_restriction",
    "review_authorities",
    "runner_inventory",
    "runtime",
    "schema",
    "scientific_inventory",
    "study_id",
    "terminal_authority",
}


def _bound_path(row: Mapping[str, object], *, expected_path: str | None = None) -> pathlib.Path:
    _require_keys(row, {"path", "bytes", "sha256"}, "bound path")
    relative = str(row["path"])
    if expected_path is not None and relative != expected_path:
        raise PermissionError(f"bound path mismatch: {relative}")
    path = (ROOT / relative).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise PermissionError("bound path escapes the repository") from exc
    if path.is_symlink() or not path.is_file():
        raise PermissionError(f"bound path is not a regular nonsymlink file: {relative}")
    raw = path.read_bytes()
    if len(raw) != row["bytes"] or sha256_bytes(raw) != str(row["sha256"]).upper():
        raise PermissionError(f"bound file identity mismatch: {relative}")
    return path


def _stage_paths(stage: str) -> list[str]:
    allowed = load_json(ROOT / "docs/reference_cases/e4_pl_q1t_allowed_extent.json")
    if not isinstance(allowed, dict):
        raise PermissionError("allowed extent must be an object")
    return [str(row["path"]) for row in allowed["paths"] if row["stage"] == stage]  # type: ignore[index]


def _commit_paths(commit: str) -> list[str]:
    text = _git("diff-tree", "--no-commit-id", "--name-only", "-r", commit)
    return [row.replace("\\", "/") for row in text.splitlines() if row]


def _same_extent(observed: Sequence[str], expected: Sequence[str]) -> bool:
    return len(observed) == len(expected) and set(observed) == set(expected)


def _validate_review(
    row: Mapping[str, object],
    *,
    expected_path: str,
    expected_schema: str,
    expected_verdict: str,
    bound: bool,
) -> tuple[pathlib.Path, dict[str, object]]:
    expected_keys = {"path", "schema", "verdict"}
    if bound:
        expected_keys |= {"bytes", "sha256"}
    _require_keys(row, expected_keys, f"{expected_path} review authority")
    if row["path"] != expected_path or row["schema"] != expected_schema or row["verdict"] != expected_verdict:
        raise PermissionError(f"review authority mismatch: {expected_path}")
    if bound:
        path = _bound_path(
            {"path": row["path"], "bytes": row["bytes"], "sha256": row["sha256"]},
            expected_path=expected_path,
        )
    else:
        path = (ROOT / expected_path).resolve()
        if path.is_symlink() or not path.is_file():
            raise PermissionError(f"review is not a regular nonsymlink file: {expected_path}")
    value = load_json(path)
    if not isinstance(value, dict):
        raise PermissionError(f"review must be an object: {expected_path}")
    _require_keys(value, REVIEW_KEYS, f"{expected_path} review")
    if value["schema"] != expected_schema or value["verdict"] != expected_verdict:
        raise PermissionError(f"review schema or exact verdict mismatch: {expected_path}")
    return path, value


def _validate_reviewed_inputs(review: Mapping[str, object], paths: Sequence[str]) -> None:
    expected = sorted(
        (
            {
                "path": relative,
                "bytes": len((ROOT / relative).read_bytes()),
                "sha256": sha256_path(ROOT / relative),
            }
            for relative in paths
        ),
        key=lambda row: row["path"],
    )
    observed = review["reviewed_inputs"]
    if not isinstance(observed, list) or sorted(observed, key=lambda row: row["path"]) != expected:
        raise PermissionError("reviewed-input identity set mismatch")
    independence = review["reviewer_independence"]
    if not isinstance(independence, dict) or (
        independence.get("authored_review_only") is not True
        or independence.get("mechanics_executed") is not False
        or independence.get("reviewed_input_authorship") is not False
    ):
        raise PermissionError("reviewer-independence declaration mismatch")


def _runtime_authority() -> dict[str, object]:
    return {
        "environment": {
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "PYTHONHASHSEED": "0",
        },
        "mpmath": "1.3.0_IMPORT_DEPENDENCY_ONLY_CATEGORICAL_USE_FORBIDDEN",
        "precision_bits": [256, 512, 1024],
        "python_implementation": "CPython",
        "python_version": "3.13.9",
        "reference_categorical_backend": "STANDARD_LIBRARY_ONLY",
        "sympy_environment": "1.14.0_ORACLE_ONLY_REFERENCE_IMPORT_FORBIDDEN",
        "pytest_version": "9.0.1",
    }


def _validate_execution_contract(path: pathlib.Path, expected_sha256: str) -> dict[str, object]:
    expected_path = (ROOT / "docs/reference_cases/e4_pl_q1t_execution_contract.json").resolve()
    path = path.resolve()
    if path != expected_path or path.is_symlink() or not path.is_file():
        raise PermissionError("execution contract path is not the frozen regular repository path")
    raw = path.read_bytes()
    if sha256_bytes(raw) != expected_sha256.upper():
        raise PermissionError("caller-supplied execution-contract SHA-256 mismatch")
    value = strict_json_bytes(raw)
    if not isinstance(value, dict):
        raise PermissionError("execution contract must be an object")
    _require_keys(value, CONTRACT_KEYS, "execution contract")
    if (
        value["schema"] != CONTRACT_SCHEMA
        or value["candidate_id"] != CANDIDATE_ID
        or value["study_id"] != STUDY_ID
    ):
        raise PermissionError("execution contract identity mismatch")

    authority_contract = load_json(ROOT / "docs/reference_cases/e4_pl_q1t_authority_contract.json")
    external_keys = authority_contract["execution_authority_record"]["canonical_exact_keys"]  # type: ignore[index]
    authorization = value["authorization"]
    _require_keys(
        authorization,
        {
            "token",
            "commit3_subject",
            "commit3_path_count",
            "commit3_paths",
            "external_authority_schema",
            "external_authority_exact_keys",
        },
        "authorization",
    )
    expected_contract_paths = _stage_paths("CONTRACT")
    if authorization != {
        "token": EXECUTION_TOKEN,
        "commit3_subject": EXECUTION_SUBJECT,
        "commit3_path_count": 3,
        "commit3_paths": expected_contract_paths,
        "external_authority_schema": AUTHORITY_SCHEMA,
        "external_authority_exact_keys": external_keys,
    }:
        raise PermissionError("execution authorization block mismatch")

    ancestry = value["commit_ancestry"]
    _require_keys(ancestry, {"commit1", "commit2"}, "commit ancestry")
    for label in ("commit1", "commit2"):
        _require_keys(
            ancestry[label],
            {"commit", "tree", "parent", "subject", "path_count", "paths"},
            f"{label} ancestry",
        )
    if ancestry["commit1"] != {
        "commit": PLAN_COMMIT,
        "tree": PLAN_TREE,
        "parent": Q1S_CLOSEOUT_COMMIT,
        "subject": PLAN_SUBJECT,
        "path_count": 14,
        "paths": _stage_paths("PLAN"),
    }:
        raise PermissionError("Commit 1 ancestry binding mismatch")
    commit2 = ancestry["commit2"]
    if (
        commit2["parent"] != PLAN_COMMIT
        or commit2["subject"] != IMPLEMENTATION_SUBJECT
        or commit2["path_count"] != 11
        or commit2["paths"] != _stage_paths("IMPLEMENTATION")
        or not isinstance(commit2["commit"], str)
        or not isinstance(commit2["tree"], str)
    ):
        raise PermissionError("Commit 2 ancestry binding mismatch")

    plan = value["plan_inputs"]
    _require_keys(plan, {"count", "rows"}, "plan inputs")
    if plan["count"] != len(PLAN_INPUTS) or not isinstance(plan["rows"], list):
        raise PermissionError("plan input count mismatch")
    expected_plan_rows = [
        {
            "path": relative,
            "bytes": len((ROOT / relative).read_bytes()),
            "sha256": sha256_path(ROOT / relative),
        }
        for relative in PLAN_INPUTS
    ]
    if plan["rows"] != expected_plan_rows:
        raise PermissionError("plan input rows mismatch")
    for row in plan["rows"]:
        _bound_path(row)

    environment = value["environment"]
    _require_keys(
        environment,
        {
            "record_path",
            "bytes",
            "sha256",
            "schema",
            "environment_id",
            "external_root_required",
            "extracted_file_count",
            "extracted_file_hash_graph_sha256",
        },
        "exact environment authority",
    )
    environment_path = _bound_path(
        {
            "path": environment["record_path"],
            "bytes": environment["bytes"],
            "sha256": environment["sha256"],
        },
        expected_path="docs/reference_cases/e4_pl_q1t_environment.json",
    )
    environment_record = load_json(environment_path)
    if environment != {
        "record_path": "docs/reference_cases/e4_pl_q1t_environment.json",
        "bytes": len(environment_path.read_bytes()),
        "sha256": sha256_path(environment_path),
        "schema": environment_record["schema"],
        "environment_id": environment_record["environment_id"],
        "external_root_required": True,
        "extracted_file_count": environment_record["extracted_file_count"],
        "extracted_file_hash_graph_sha256": environment_record["extracted_file_hash_graph_sha256"],
    }:
        raise PermissionError("exact environment contract binding mismatch")

    inherited = value["inherited_inputs"]
    _require_keys(inherited, {"count", "rows"}, "inherited inputs")
    inheritance_manifest = load_json(ROOT / "docs/reference_cases/e4_pl_q1t_inheritance_manifest.json")
    expected_inherited_rows = [
        row
        for group in ("q1r_e4_inherited_inputs", "q1s_commit1_inputs", "q1s_closeout_inputs")
        for row in inheritance_manifest[group]  # type: ignore[index]
    ]
    if inherited != {"count": 49, "rows": expected_inherited_rows}:
        raise PermissionError("49-row inheritance binding mismatch")
    for row in inherited["rows"]:
        _require_keys(
            row,
            {"path", "bytes", "sha256", "git_blob", "source_commit", "classification"},
            "inherited row",
        )
        _bound_path({key: row[key] for key in ("path", "bytes", "sha256")})
        if _git("rev-parse", f"{row['source_commit']}:{row['path']}") != row["git_blob"]:
            raise PermissionError(f"inherited Git blob mismatch: {row['path']}")

    inputs = value["implementation_inputs"]
    _require_keys(
        inputs,
        {
            "reference",
            "oracle",
            "scientific_runner",
            "manifest",
            "implementation_review",
            "exact_backend_test",
            "scientific_tests",
        },
        "implementation inputs",
    )
    implementations = {
        "reference": (
            "docs/reference_cases/e4_pl_q1t_reference.py",
            "Q1T_REFERENCE_STDLIB_FIELD_ALG",
        ),
        "oracle": (
            "docs/reference_cases/e4_pl_q1t_oracle.py",
            "Q1T_ORACLE_SYMPY_ALGEBRAIC_FIELD",
        ),
    }
    for name, (expected, implementation_id) in implementations.items():
        row = inputs[name]
        _require_keys(row, {"path", "bytes", "sha256", "implementation_id"}, f"{name} implementation")
        _bound_path({key: row[key] for key in ("path", "bytes", "sha256")}, expected_path=expected)
        if row["implementation_id"] != implementation_id:
            raise PermissionError(f"{name} implementation id mismatch")
    runner = inputs["scientific_runner"]
    _require_keys(runner, {"path", "bytes", "sha256", "runner_id"}, "scientific runner")
    _bound_path(
        {key: runner[key] for key in ("path", "bytes", "sha256")},
        expected_path="docs/reference_cases/e4_pl_q1t_scientific_test_runner.py",
    )
    if runner["runner_id"] != "SCIENTIFIC_TEST_RUNNER":
        raise PermissionError("scientific runner id mismatch")

    manifest = inputs["manifest"]
    _require_keys(manifest, {"path", "bytes", "sha256", "schema"}, "implementation manifest")
    manifest_path = _bound_path(
        {key: manifest[key] for key in ("path", "bytes", "sha256")},
        expected_path="docs/reference_cases/e4_pl_q1t_implementation_manifest.json",
    )
    manifest_value = load_json(manifest_path)
    if not isinstance(manifest_value, dict) or manifest_value.get("schema") != manifest["schema"]:
        raise PermissionError("implementation manifest schema mismatch")

    implementation_review = inputs["implementation_review"]
    implementation_review_path, implementation_review_value = _validate_review(
        implementation_review,
        expected_path="docs/reference_cases/e4_pl_q1t_implementation_review.json",
        expected_schema="anysolver.s4.e4-pl-q1t-implementation-review-v1",
        expected_verdict="ACCEPT_Q1T_IMPLEMENTATION_FREEZE_NO_P0_P1",
        bound=True,
    )
    _validate_reviewed_inputs(
        implementation_review_value,
        [path for path in _stage_paths("IMPLEMENTATION") if path != str(implementation_review["path"])],
    )

    implementation_stage = _stage_paths("IMPLEMENTATION")
    exact_backend_test = inputs["exact_backend_test"]
    _require_keys(exact_backend_test, {"path", "bytes", "sha256", "node_ids"}, "exact backend test")
    _bound_path(
        {key: exact_backend_test[key] for key in ("path", "bytes", "sha256")},
        expected_path=implementation_stage[5],
    )
    if exact_backend_test["node_ids"] != [
        "tests/test_e4_pl_q1t_exact_backend.py::test_q1t_exact_backend_toy_cancellation_nested_radicals_inverse_rank_sign_and_serialization"
    ]:
        raise PermissionError("toy exact-backend node identity mismatch")

    expected_tests = implementation_stage[6:]
    tests = inputs["scientific_tests"]
    if not isinstance(tests, list) or len(tests) != 5:
        raise PermissionError("scientific test input must have five rows")
    flattened_nodes: list[str] = []
    for row, expected in zip(tests, expected_tests):
        _require_keys(row, {"path", "bytes", "sha256", "node_ids"}, "scientific test")
        _bound_path({key: row[key] for key in ("path", "bytes", "sha256")}, expected_path=expected)
        if not isinstance(row["node_ids"], list) or len(row["node_ids"]) != 1:
            raise PermissionError("each scientific test row must bind one node")
        flattened_nodes.extend(str(node) for node in row["node_ids"])

    reviews = value["review_authorities"]
    _require_keys(reviews, {"plan", "implementation", "contract"}, "review authorities")
    plan_review_path, plan_review_value = _validate_review(
        reviews["plan"],
        expected_path="docs/reference_cases/e4_pl_q1t_plan_review.json",
        expected_schema="anysolver.s4.e4-pl-q1t-plan-review-v1",
        expected_verdict="ACCEPT_Q1T_PREREGISTRATION_NO_P0_P1",
        bound=True,
    )
    _validate_reviewed_inputs(
        plan_review_value,
        [path for path in _stage_paths("PLAN") if path != str(reviews["plan"]["path"])],
    )
    reviewed_implementation_path, _ = _validate_review(
        reviews["implementation"],
        expected_path="docs/reference_cases/e4_pl_q1t_implementation_review.json",
        expected_schema="anysolver.s4.e4-pl-q1t-implementation-review-v1",
        expected_verdict="ACCEPT_Q1T_IMPLEMENTATION_FREEZE_NO_P0_P1",
        bound=True,
    )
    if reviewed_implementation_path != implementation_review_path:
        raise PermissionError("implementation review bindings disagree")
    contract_review = reviews["contract"]
    _require_keys(contract_review, {"path", "schema", "verdict", "hash_binding"}, "contract review authority")
    if contract_review != {
        "path": "docs/reference_cases/e4_pl_q1t_contract_review.json",
        "schema": "anysolver.s4.e4-pl-q1t-contract-review-v1",
        "verdict": "ACCEPT_Q1T_EXECUTION_CONTRACT_NO_P0_P1",
        "hash_binding": "EXTERNAL_AUTHORITY_RECORD",
    }:
        raise PermissionError("non-self-referential contract-review authority mismatch")

    if value["runtime"] != _runtime_authority():
        raise PermissionError("runtime authority mismatch")
    if sys.implementation.name != "cpython" or ".".join(str(part) for part in sys.version_info[:3]) != "3.13.9":
        raise PermissionError("running Python implementation/version differs from frozen runtime")
    for name, expected in value["runtime"]["environment"].items():
        if os.environ.get(name) != expected:
            raise PermissionError(f"frozen thread environment mismatch: {name}")
    scientific = value["scientific_inventory"]
    if scientific != {"count": 5, "node_ids": flattened_nodes, "inventories_separate": True}:
        raise PermissionError("scientific inventory mismatch")

    runner_inventory = value["runner_inventory"]
    if runner_inventory != {
        "count": 3,
        "runner_ids": ["REFERENCE_RUNNER", "ORACLE_RUNNER", "SCIENTIFIC_TEST_RUNNER"],
    }:
        raise PermissionError("three-runner inventory mismatch")

    terminal = value["terminal_authority"]
    _require_keys(terminal, {"path", "bytes", "sha256", "schema", "evaluation", "terminal_count"}, "terminal authority")
    terminal_path = _bound_path(
        {key: terminal[key] for key in ("path", "bytes", "sha256")},
        expected_path="docs/reference_cases/e4_pl_q1t_terminal_table.json",
    )
    terminal_value = load_json(terminal_path)
    if (
        terminal["schema"] != terminal_value["schema"]
        or terminal["evaluation"] != "FIRST_MATCH_IN_ASCENDING_PRECEDENCE_WINS"
        or terminal["evaluation"] != terminal_value["evaluation"]
        or terminal["terminal_count"] != 11
        or len(terminal_value["terminals"]) != 11
    ):
        raise PermissionError("terminal authority mismatch")

    expected_outcomes = _stage_paths("OUTCOME")
    if value["output_absences"] != {"paths": expected_outcomes, "absent_from_commit3_tree": True}:
        raise PermissionError("output absence authority mismatch")
    if value["agreement"] != {
        "common_payload_schema": PAYLOAD_SCHEMA,
        "cross_implementation": "BYTE_IDENTICAL_CANONICAL_CERTIFICATE_PAYLOAD",
        "within_reference_fresh_processes": 2,
        "within_oracle_fresh_processes": 2,
        "reference_wrapper_schema": OUTPUT_SCHEMA,
        "oracle_wrapper_schema": "anysolver.s4.e4-pl-q1t-oracle-raw-v1",
    }:
        raise PermissionError("agreement authority mismatch")
    if value["production_restriction"] != {
        "legacy_default": "ShellElement",
        "post_execution_source_changes": "FORBIDDEN_REQUIRES_NEW_SUCCESSOR",
        "production": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "q1b_execution": "UNAUTHORIZED",
    }:
        raise PermissionError("production restriction mismatch")

    # Ensure the two bound preregistration reviews really are the files whose
    # hashes appear in their contract rows.
    if sha256_path(plan_review_path) != str(reviews["plan"]["sha256"]):
        raise PermissionError("plan review hash mismatch")
    return value


def _path_is_within(path: pathlib.Path, parent: pathlib.Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _validate_external_authority_path(path: pathlib.Path) -> None:
    if not path.is_absolute():
        raise PermissionError("authority record path must be absolute")
    resolved = path.resolve()
    if path.is_symlink() or not path.is_file():
        raise PermissionError("authority record must be a regular nonsymlink file")
    worktree_text = _git("worktree", "list", "--porcelain")
    worktrees = [
        pathlib.Path(line.split(" ", 1)[1]).resolve()
        for line in worktree_text.splitlines()
        if line.startswith("worktree ")
    ]
    if any(_path_is_within(resolved, worktree) for worktree in worktrees):
        raise PermissionError("authority record must be outside every Git worktree")


def _validate_external_environment_root(
    root: pathlib.Path,
    expected_environment_sha256: str,
) -> dict[str, object]:
    """Bind the caller-owned extraction to the committed canonical graph."""

    if not root.is_absolute():
        raise PermissionError("exact environment root must be absolute")
    resolved = root.resolve()
    if root.is_symlink() or not root.is_dir():
        raise PermissionError("exact environment root must be a regular nonsymlink directory")
    worktrees = [
        pathlib.Path(line.split(" ", 1)[1]).resolve()
        for line in _git("worktree", "list", "--porcelain").splitlines()
        if line.startswith("worktree ")
    ]
    if any(_path_is_within(resolved, worktree) for worktree in worktrees):
        raise PermissionError("exact environment root must be outside every Git worktree")

    record_path = ROOT / "docs/reference_cases/e4_pl_q1t_environment.json"
    record_raw = record_path.read_bytes()
    actual_record_sha = sha256_bytes(record_raw)
    if actual_record_sha != expected_environment_sha256.upper():
        raise PermissionError("caller-supplied environment-record SHA-256 mismatch")
    record = strict_json_bytes(record_raw)
    if not isinstance(record, dict):
        raise PermissionError("exact environment record must be an object")
    if (
        record.get("schema") != "e4_pl_q1t_environment_record_v1"
        or record.get("candidate_id") != CANDIDATE_ID
        or record.get("study_id") != STUDY_ID
        or record.get("absolute_paths_recorded") is not False
        or record.get("mpmath_categorical_evidence_permitted") is not False
    ):
        raise PermissionError("exact environment record identity mismatch")
    graph = record.get("extracted_file_hash_graph")
    if not isinstance(graph, list) or len(graph) != record.get("extracted_file_count"):
        raise PermissionError("exact environment graph count mismatch")
    if sha256_bytes(canonical_bytes(graph)) != str(record.get("extracted_file_hash_graph_sha256", "")).upper():
        raise PermissionError("exact environment graph digest mismatch")

    expected_paths: set[str] = set()
    for row in graph:
        if not isinstance(row, dict) or set(row) != {"path", "bytes", "sha256"}:
            raise PermissionError("exact environment graph row schema mismatch")
        relative = pathlib.PurePosixPath(str(row["path"]))
        if relative.is_absolute() or not relative.parts or ".." in relative.parts:
            raise PermissionError("exact environment graph path is unsafe")
        token = relative.as_posix()
        if token in expected_paths:
            raise PermissionError("duplicate exact environment graph path")
        expected_paths.add(token)
        path = resolved.joinpath(*relative.parts)
        if path.is_symlink() or not path.is_file():
            raise PermissionError(f"exact environment file is absent or non-regular: {token}")
        raw = path.read_bytes()
        if len(raw) != row["bytes"] or sha256_bytes(raw) != str(row["sha256"]).upper():
            raise PermissionError(f"exact environment file identity mismatch: {token}")
    observed_paths: set[str] = set()
    for path in resolved.rglob("*"):
        if path.is_symlink():
            raise PermissionError("exact environment contains a symlink")
        if path.is_file():
            observed_paths.add(path.relative_to(resolved).as_posix())
    if observed_paths != expected_paths:
        raise PermissionError("exact environment file extent differs from canonical graph")
    return record


def _validate_external_output_path(path: pathlib.Path) -> None:
    if not path.is_absolute():
        raise PermissionError("registered raw output path must be absolute")
    resolved = path.resolve()
    parent = resolved.parent
    if path.exists() or path.is_symlink() or not parent.is_dir() or parent.is_symlink():
        raise PermissionError("output must be an absent path in a regular existing directory")
    worktree_text = _git("worktree", "list", "--porcelain")
    worktrees = [
        pathlib.Path(line.split(" ", 1)[1]).resolve()
        for line in worktree_text.splitlines()
        if line.startswith("worktree ")
    ]
    if any(_path_is_within(resolved, worktree) for worktree in worktrees):
        raise PermissionError("registered raw output must be outside every Git worktree")


def _validate_execution_commit_chain(
    contract: Mapping[str, object],
    authority: Mapping[str, object],
    contract_path: pathlib.Path,
) -> None:
    head = _git("rev-parse", "HEAD")
    tree = _git("rev-parse", "HEAD^{tree}")
    if authority["commit"] != head or authority["tree"] != tree:
        raise PermissionError("external authority commit/tree does not match checked-out HEAD")
    if _git("show", "-s", "--format=%s", head) != EXECUTION_SUBJECT:
        raise PermissionError("HEAD subject is not the exact Commit 3 subject")
    if not _same_extent(_commit_paths(head), _stage_paths("CONTRACT")):
        raise PermissionError("Commit 3 does not have the exact ordered three-path extent")

    parents = _git("show", "-s", "--format=%P", head).split()
    if len(parents) != 1:
        raise PermissionError("Commit 3 must have exactly one parent")
    commit2 = contract["commit_ancestry"]["commit2"]  # type: ignore[index]
    if parents[0] != commit2["commit"]:
        raise PermissionError("Commit 3 parent differs from contract-bound Commit 2")
    if _git("rev-parse", f"{parents[0]}^{{tree}}") != commit2["tree"]:
        raise PermissionError("Commit 2 tree mismatch")
    if _git("show", "-s", "--format=%s", parents[0]) != IMPLEMENTATION_SUBJECT:
        raise PermissionError("Commit 2 subject mismatch")
    if not _same_extent(_commit_paths(parents[0]), _stage_paths("IMPLEMENTATION")):
        raise PermissionError("Commit 2 does not have the exact eleven-path extent")

    commit2_parents = _git("show", "-s", "--format=%P", parents[0]).split()
    if commit2_parents != [PLAN_COMMIT]:
        raise PermissionError("Commit 2 must have sole Commit 1 parent")
    if _git("rev-parse", f"{PLAN_COMMIT}^{{tree}}") != PLAN_TREE:
        raise PermissionError("Commit 1 tree mismatch")
    if _git("show", "-s", "--format=%s", PLAN_COMMIT) != PLAN_SUBJECT:
        raise PermissionError("Commit 1 subject mismatch")
    if _git("show", "-s", "--format=%P", PLAN_COMMIT).split() != [Q1S_CLOSEOUT_COMMIT]:
        raise PermissionError("Commit 1 parent mismatch")
    if not _same_extent(_commit_paths(PLAN_COMMIT), _stage_paths("PLAN")):
        raise PermissionError("Commit 1 does not have the exact fourteen-path extent")

    expected_contract = (ROOT / "docs/reference_cases/e4_pl_q1t_execution_contract.json").resolve()
    if contract_path.resolve() != expected_contract:
        raise PermissionError("contract path differs from Commit 3 authority")
    commit3_paths = set(_git("ls-tree", "-r", "--name-only", head).replace("\\", "/").splitlines())
    if any(path in commit3_paths for path in contract["output_absences"]["paths"]):  # type: ignore[index]
        raise PermissionError("an outcome path exists in the Commit 3 tree")
    if any((ROOT / path).exists() for path in contract["output_absences"]["paths"]):  # type: ignore[index]
        raise PermissionError("an outcome path already exists in the execution worktree")
    if _git("diff", "--name-only") or _git("diff", "--cached", "--name-only"):
        raise PermissionError("tracked worktree or index is dirty")


def _validate_execution_authority(
    authority_path: pathlib.Path,
    authority_sha256: str,
    contract_path: pathlib.Path,
    contract_sha256: str,
    environment_root: pathlib.Path,
    environment_sha256: str,
    runner_id: str,
) -> tuple[dict[str, object], str, object]:
    _validate_external_authority_path(authority_path)
    raw = authority_path.read_bytes()
    actual_authority_sha = sha256_bytes(raw)
    if actual_authority_sha != authority_sha256.upper():
        raise PermissionError("caller-supplied execution-authority SHA-256 mismatch")
    authority = strict_json_bytes(raw)
    if not isinstance(authority, dict):
        raise PermissionError("execution authority must be an object")
    _require_keys(authority, AUTHORITY_KEYS, "execution authority")
    expected_runner_ids = ["REFERENCE_RUNNER", "ORACLE_RUNNER", "SCIENTIFIC_TEST_RUNNER"]
    expected_verdicts = {
        "plan": "ACCEPT_Q1T_PREREGISTRATION_NO_P0_P1",
        "implementation": "ACCEPT_Q1T_IMPLEMENTATION_FREEZE_NO_P0_P1",
        "contract": "ACCEPT_Q1T_EXECUTION_CONTRACT_NO_P0_P1",
    }
    if (
        authority["schema"] != AUTHORITY_SCHEMA
        or authority["candidate_id"] != CANDIDATE_ID
        or authority["study_id"] != STUDY_ID
        or authority["authorization"] != EXECUTION_TOKEN
        or authority["runner_ids"] != expected_runner_ids
        or authority["review_verdicts"] != expected_verdicts
        or runner_id != "REFERENCE_RUNNER"
        or runner_id not in authority["runner_ids"]
    ):
        raise PermissionError("execution authority identity, runner, or verdict mismatch")
    if authority["execution_contract_sha256"] != contract_sha256.upper():
        raise PermissionError("authority does not bind caller-supplied contract hash")
    if authority["environment_sha256"] != environment_sha256.upper():
        raise PermissionError("authority does not bind caller-supplied environment-record hash")

    contract = _validate_execution_contract(contract_path, contract_sha256)
    environment_record = _validate_external_environment_root(environment_root, environment_sha256)
    if contract["environment"]["sha256"] != environment_sha256.upper():  # type: ignore[index]
        raise PermissionError("execution contract and caller environment hash disagree")
    if contract["environment"]["extracted_file_hash_graph_sha256"] != environment_record[  # type: ignore[index]
        "extracted_file_hash_graph_sha256"
    ]:
        raise PermissionError("execution contract and environment file graph disagree")
    reviews = contract["review_authorities"]
    plan_path = ROOT / str(reviews["plan"]["path"])  # type: ignore[index]
    implementation_path = ROOT / str(reviews["implementation"]["path"])  # type: ignore[index]
    contract_review_path, contract_review_value = _validate_review(
        {
            key: reviews["contract"][key]  # type: ignore[index]
            for key in ("path", "schema", "verdict")
        },
        expected_path="docs/reference_cases/e4_pl_q1t_contract_review.json",
        expected_schema="anysolver.s4.e4-pl-q1t-contract-review-v1",
        expected_verdict="ACCEPT_Q1T_EXECUTION_CONTRACT_NO_P0_P1",
        bound=False,
    )
    _validate_reviewed_inputs(
        contract_review_value,
        [
            path
            for path in _stage_paths("CONTRACT")
            if path != "docs/reference_cases/e4_pl_q1t_contract_review.json"
        ],
    )
    if (
        authority["plan_review_sha256"] != sha256_path(plan_path)
        or authority["implementation_review_sha256"] != sha256_path(implementation_path)
        or authority["contract_review_sha256"] != sha256_path(contract_review_path)
    ):
        raise PermissionError("external authority review hash binding mismatch")
    _validate_execution_commit_chain(contract, authority, contract_path)
    return contract, actual_authority_sha, _EXECUTION_CAPABILITY


def _ordered_lf_digest(values: Sequence[str]) -> str:
    return sha256_bytes(("\n".join(values) + "\n").encode("utf-8"))


COMMON_PAYLOAD_KEYS = {
    "schema",
    "candidate_id",
    "study_id",
    "precision_bits",
    "coverage",
    "frame_and_fields",
    "local_algebra",
    "recovery",
    "global_supports",
    "classification",
    "case_certificates",
}
COMMON_CASE_KEYS = {
    "case_id",
    "geometry_id",
    "operation_id",
    "gauss_station_ids",
    "centre",
    "frame",
    "field_work",
    "local_algebra",
    "patches",
    "recovery",
    "global_support",
    "status",
}


def _validate_common_payload(payload: Mapping[str, object]) -> None:
    if set(payload) != COMMON_PAYLOAD_KEYS or payload["schema"] != PAYLOAD_SCHEMA:
        raise AssertionError("common certificate payload top-level schema mismatch")
    cases = payload["case_certificates"]
    if not isinstance(cases, list) or len(cases) != 56:
        raise AssertionError("common certificate payload must contain 56 ordered cases")
    for row in cases:
        if not isinstance(row, dict) or set(row) != COMMON_CASE_KEYS:
            raise AssertionError("common case certificate exact-key schema mismatch")
        if row["status"] not in {"PASS", "NO_GO", "UNCLASSIFIED"}:
            raise AssertionError("common case status enum mismatch")

    def visit(value: object) -> None:
        if isinstance(value, bool) or isinstance(value, int):
            return
        if isinstance(value, str):
            if not value or "\n" in value or "\r" in value:
                raise AssertionError("common payload identifiers must be nonempty single-line strings")
            return
        if isinstance(value, list):
            for item in value:
                visit(item)
            return
        if isinstance(value, dict):
            for key, item in value.items():
                if not isinstance(key, str) or not key:
                    raise AssertionError("common payload object keys must be identifiers")
                visit(item)
            return
        raise AssertionError(f"forbidden common payload scalar: {type(value).__name__}")

    visit(dict(payload))


def _case_common_record(
    row: Mapping[str, object],
    covariance: Mapping[str, object],
    global_certificate: Mapping[str, object] | None,
) -> dict[str, object]:
    centre_diagnostic = row["centre"]
    rank = row["rank"]
    stationary = row["stationary"]
    modes = row["modes"]
    boundary = row["restricted_boundary"]
    patch_rows = {str(item["field"]): item for item in row["patches"]}
    rigid_rows = row["rigid_patches"]
    recovery_diagnostic = row["recovery"]

    centre = {
        "centre_j_positive": bool(centre_diagnostic["centre_j_positive"]),
        "centre_taylor_exact": bool(centre_diagnostic["centre_taylor_exact"])
        and bool(centre_diagnostic["multiplier_gram_positive"]),
        "residual_mode_exact": bool(centre_diagnostic["residual_mode_exact"])
        and bool(covariance["residual_mode_transport"]),
    }
    frame = {
        "equation7_exact": bool(covariance["equation7_frame"]),
        "projectors_exact": bool(covariance["T5_QD_projectors"]),
    }
    field_work = {
        "fields_exact": bool(covariance["source_stress_strain_reconstruction"]["exact"])
        and bool(covariance["physical_recovery_reconstruction"]),
        "pseudo_fields_exact": bool(covariance["kappa_M_pseudo_work"])
        and bool(covariance["gamma_Q_pseudo_work"]),
        "pl_exact": bool(covariance["PL_multiplier_gram_work"]),
        "work_exact": bool(covariance["epsilon_N_work"])
        and bool(covariance["kappa_M_pseudo_work"])
        and bool(covariance["gamma_Q_pseudo_work"])
        and bool(covariance["PL_multiplier_gram_work"]),
        "gauss_correspondence_exact": bool(covariance["corresponding_gauss_reconstruction"])
        and bool(covariance["source_stress_strain_reconstruction"]["gauss_correspondence"])
        and bool(row["jacobian_positive"]),
    }
    mode_exact = all(
        bool(modes[key])
        for key in (
            "matched_state_vector_exact",
            "matched_state_null_exact",
            "common_drill_energetic",
            "translation_spin_energetic",
            "alternating_pl_null",
            "alternating_hg_energetic",
        )
    )
    local_algebra = {
        "field_count": 38,
        "internal_invertible": bool(row["internal_invertible"]),
        "rank_18": bool(rank["rank_18"]) and mode_exact,
        "six_rigid_exact": all(bool(value) for value in rank["rigid_nulls"].values())
        and rank["rigid_rank"] == 6,
        "symmetric": bool(stationary["symmetric_tangent_exact"]),
        "psd": bool(rank["psd"]) and mode_exact,
        "mixed_condensed_exact": all(
            bool(stationary[key])
            for key in (
                "core_stationarity_exact",
                "pl_stationarity_exact",
                "actual_38_stationarity_exact",
                "actual_38_inverse_exact",
                "condensed_energy_exact",
                "condensed_work_exact",
                "condensed_residual_exact",
                "condensed_tangent_exact",
            )
        ),
        "unresolved": bool(rank["inconclusive"])
        or bool(centre_diagnostic["centre_j_inconclusive"])
        or bool(centre_diagnostic["multiplier_gram_inconclusive"])
        or bool(row["jacobian_inconclusive"]),
    }
    patches = {
        "membrane": bool(patch_rows["MEMBRANE_PATCH"]["physical_recovery_exact"]),
        "bending": bool(patch_rows["BENDING_PATCH"]["physical_recovery_exact"]),
        "shear": bool(patch_rows["SHEAR_PATCH"]["physical_recovery_exact"]),
        "combined": bool(patch_rows["COMBINED_PHYSICAL_PATCH"]["physical_recovery_exact"]),
        "six_rigid_all_exact": len(rigid_rows) == 6
        and all(bool(item["physical_recovery_exact"]) for item in rigid_rows),
    }
    recovery = {
        "compatible_all_exact": bool(recovery_diagnostic["compatible_all_exact"]),
        "independent_all_exact": bool(recovery_diagnostic["independent_all_exact"]),
        "physical_resultants_all_exact": bool(recovery_diagnostic["physical_resultants_all_exact"]),
        "numerical_separate": bool(recovery_diagnostic["numerical_separate"])
        and bool(row["recovery_separated"]),
        "station_count": int(recovery_diagnostic["station_count"]),
    }
    apply_global = global_certificate is not None
    global_support = {
        "projectors_exact": bool(boundary["projector_partition"])
        and bool(boundary["T5_QD_orthogonal"])
        and bool(covariance["T5_QD_projectors"])
        and (not apply_global or (
            bool(global_certificate["equation7_frame"])
            and bool(global_certificate["proper_global_rotation"])
            and bool(global_certificate["stiffness"])
            and all(bool(value) for value in global_certificate["component_stiffness"].values())
            and bool(global_certificate["physical_projector"])
            and bool(global_certificate["drill_projector"])
            and bool(global_certificate["T5"])
            and bool(global_certificate["QD"])
        )),
        "load_exact": bool(boundary["transported_load_rebuilt"])
        and bool(boundary["physical_load_drill_free"])
        and bool(covariance["load"])
        and (not apply_global or bool(global_certificate["load"])),
        "support_exact": bool(boundary["A_bc_QD_zero"])
        and bool(covariance["support"])
        and (not apply_global or bool(global_certificate["support"])),
        "solution_exact": bool(boundary["KKT_drill_block_invertible"])
        and bool(boundary["KKT_equilibrium_exact"])
        and bool(boundary["KKT_constraint_exact"])
        and bool(boundary["KKT_full_system_exact"])
        and bool(covariance["support_solution"])
        and (
            not apply_global
            or (
                bool(global_certificate["support_solution"])
                and bool(global_certificate["residual_reaction"])
                and bool(global_certificate["rebuilt_patch_field"])
            )
        ),
        "reaction_exact": bool(boundary["KKT_virtual_work_exact"])
        and bool(boundary["support_reaction_drill_free"])
        and bool(boundary["physical_internal_drill_free"])
        and bool(covariance["support_reaction"])
        and (not apply_global or bool(global_certificate["support_reaction"])),
        "recovery_exact": bool(recovery["physical_resultants_all_exact"])
        and (not apply_global or bool(global_certificate["recovery_global_reconstruction"])),
        "numerical_separate": bool(boundary["numerical_reactions_separate"])
        and bool(recovery["numerical_separate"])
        and (not apply_global or bool(global_certificate["numerical_diagnostics"])),
    }

    exact_groups = (frame, patches, recovery, global_support)
    any_exact_failure = any(
        value is False
        for group in exact_groups
        for key, value in group.items()
        if key != "station_count"
    ) or any(
        value is False
        for key, value in centre.items()
        if key not in ("centre_j_positive", "centre_taylor_exact")
    ) or any(
        value is False
        for key, value in field_work.items()
        if key != "gauss_correspondence_exact"
    )
    ordered_failure = (
        (
            not centre["centre_j_positive"]
            or not centre["centre_taylor_exact"]
            or not field_work["gauss_correspondence_exact"]
        )
        and not local_algebra["unresolved"]
    )
    local_failure = (
        not local_algebra["internal_invertible"]
        or not mode_exact
        or not local_algebra["six_rigid_exact"]
        or not local_algebra["symmetric"]
        or not local_algebra["mixed_condensed_exact"]
        or rank["ldl_counts"]["negative"] > 0
        or rank["ldl_counts"]["exact_zero"] > 0
        or (
            rank["ldl_counts"]["positive"] != 18
            and rank["ldl_counts"]["unresolved"] == 0
        )
    )
    if local_failure or any_exact_failure or ordered_failure:
        status = "NO_GO"
    elif local_algebra["unresolved"]:
        status = "UNCLASSIFIED"
    else:
        status = "PASS"
    return {
        "case_id": str(row["id"]),
        "centre": centre,
        "field_work": field_work,
        "frame": frame,
        "gauss_station_ids": [
            f"{row['id']}::{station_id}" for station_id in GAUSS_IDS
        ],
        "geometry_id": str(row["geometry"]),
        "global_support": global_support,
        "local_algebra": local_algebra,
        "operation_id": str(row["operation"]),
        "patches": patches,
        "recovery": recovery,
        "status": status,
    }


def execute(
    contract: Mapping[str, object],
    *,
    contract_sha256: str,
    authority_sha256: str,
    capability: object,
) -> dict[str, object]:
    if capability is not _EXECUTION_CAPABILITY:
        raise PermissionError("registered mechanics requires a validated external-authority capability")
    contracts = _contracts()
    frame_contract = contracts["e4_pl_q1r_frame_contract"]
    geometry_contract = contracts["e4_pl_q1r_geometry_contract"]
    tolerances = contracts["e4_pl_q1r_tolerances"]
    operations = _operations(frame_contract)  # type: ignore[arg-type]
    geometries = _geometries(geometry_contract)  # type: ignore[arg-type]
    precisions = tuple(int(value) for value in tolerances["precision_bits"])  # type: ignore[index]
    if precisions != (256, 512, 1024):
        raise PermissionError("precision sequence differs from frozen Q1T authority")
    frame_static = _frame_static_certificate(contracts)

    diagnostic_cases: list[dict[str, object]] = []
    covariance_rows: list[dict[str, object]] = []
    assemblies_by_geometry: dict[str, dict[str, Assembly]] = {}
    for geometry in geometries:
        by_operation = {operation.id: assemble(geometry, operation) for operation in operations}
        assemblies_by_geometry[geometry.id] = by_operation
        base = by_operation["E"]
        for operation in operations:
            assembly = by_operation[operation.id]
            fields = _transported_fields(base, assembly, operation)
            diagnostic_cases.append(
                _case_certificate(base, assembly, operation, fields, precisions)
            )
            covariance_rows.append(
                _covariance_certificate(base, assembly, operation, fields)
            )

    transform = geometry_contract["global_transform"]  # type: ignore[index]
    global_rows = {
        operation.id: _global_covariance_certificate(
            assemblies_by_geometry["Q3_TAPERED_SKEW"][operation.id],
            assemblies_by_geometry["Q3_TAPERED_SKEW_RSTAR_TRANSLATED"][operation.id],
            operation,
            transform,
        )
        for operation in operations
    }

    case_certificates: list[dict[str, object]] = []
    for row, covariance in zip(diagnostic_cases, covariance_rows):
        link = (
            global_rows[str(row["operation"])]
            if row["geometry"] in ("Q3_TAPERED_SKEW", "Q3_TAPERED_SKEW_RSTAR_TRANSLATED")
            else None
        )
        case_certificates.append(_case_common_record(row, covariance, link))

    ordered_case_ids = [str(row["case_id"]) for row in case_certificates]
    ordered_station_ids = [
        str(station)
        for row in case_certificates
        for station in row["gauss_station_ids"]
    ]
    coverage = {
        "base_geometries": 6,
        "centre_records": len(case_certificates),
        "d4_operations": len(operations),
        "gauss_records": len(ordered_station_ids),
        "global_transform_variants": 1,
        "numbered_cases": len(case_certificates),
        "ordered_case_ids_sha256": _ordered_lf_digest(ordered_case_ids),
        "ordered_station_ids_sha256": _ordered_lf_digest(ordered_station_ids),
    }
    frame_and_fields = {
        "all_d4_field_maps_exact": all(
            bool(row["field_work"]["fields_exact"])
            and bool(row["field_work"]["pseudo_fields_exact"])
            for row in case_certificates
        ),
        "all_d4_frame_identities_exact": bool(frame_static["all_exact"])
        and all(bool(row["frame"]["equation7_exact"]) for row in case_certificates),
        "all_d4_pl_maps_exact": all(
            bool(row["field_work"]["pl_exact"]) for row in case_certificates
        ),
        "all_d4_work_equalities_exact": all(
            bool(row["field_work"]["work_exact"]) for row in case_certificates
        ),
        "all_gauss_correspondence_exact": all(
            bool(row["field_work"]["gauss_correspondence_exact"])
            for row in case_certificates
        ),
        "all_numbered_loads_exact": all(
            bool(row["global_support"]["load_exact"]) for row in case_certificates
        ),
        "all_numbered_projectors_exact": all(
            bool(row["frame"]["projectors_exact"])
            and bool(row["global_support"]["projectors_exact"])
            for row in case_certificates
        ),
        "all_numbered_residual_modes_exact": all(
            bool(row["centre"]["residual_mode_exact"]) for row in case_certificates
        )
        and all(bool(row["residual_mode_transport"]) for row in covariance_rows),
    }
    local_algebra = {
        "all_38_field_blocks_invertible": all(
            bool(row["local_algebra"]["internal_invertible"]) for row in case_certificates
        ),
        "all_condensed_rank_18": all(
            bool(row["local_algebra"]["rank_18"]) for row in case_certificates
        ),
        "all_mixed_condensed_equalities_exact": all(
            bool(row["local_algebra"]["mixed_condensed_exact"]) for row in case_certificates
        ),
        "all_psd": all(bool(row["local_algebra"]["psd"]) for row in case_certificates),
        "all_six_rigid_actions_exact_zero": all(
            bool(row["local_algebra"]["six_rigid_exact"]) for row in case_certificates
        ),
        "all_symmetric": all(
            bool(row["local_algebra"]["symmetric"]) for row in case_certificates
        ),
        "quotient_rule": "LEXICOGRAPHIC_EXACT_RREF_NULLSPACE_OF_R_TRANSPOSE",
        "unresolved_at_1024": any(
            bool(row["local_algebra"]["unresolved"]) for row in case_certificates
        ),
    }
    recovery = {
        "all_224_compatible_fields": len(ordered_station_ids) == 224
        and all(bool(row["recovery"]["compatible_all_exact"]) for row in case_certificates),
        "all_224_independent_fields": len(ordered_station_ids) == 224
        and all(bool(row["recovery"]["independent_all_exact"]) for row in case_certificates),
        "all_224_physical_resultants": len(ordered_station_ids) == 224
        and all(bool(row["recovery"]["physical_resultants_all_exact"]) for row in case_certificates),
        "all_numerical_fields_separate": all(
            bool(row["recovery"]["numerical_separate"]) for row in case_certificates
        ),
        "numerical_fields_excluded": [
            "PL_CONSTRAINT",
            "PL_MULTIPLIER",
            "PL_COMPLIANCE_ENERGY",
            "RESIDUAL_MODE_COORDINATE",
            "RESIDUAL_MODE_ENERGY",
            "RESIDUAL_MODE_RESIDUAL",
            "RESIDUAL_MODE_TANGENT",
        ],
        "physical_resultants": ["N", "M", "Q"],
    }
    global_supports = {
        "all_global_field_recovery_exact": all(
            bool(row["recovery_global_reconstruction"]) for row in global_rows.values()
        ),
        "all_global_loads_exact": all(bool(row["load"]) for row in global_rows.values()),
        "all_global_projectors_exact": all(
            bool(row["physical_projector"]) and bool(row["drill_projector"])
            for row in global_rows.values()
        ),
        "all_global_reactions_exact": all(
            bool(row["support_reaction"]) for row in global_rows.values()
        ),
        "all_global_support_solutions_exact": all(
            bool(row["support_solution"]) for row in global_rows.values()
        ),
        "all_global_supports_exact": all(
            bool(row["support"]) for row in global_rows.values()
        ),
        "all_numerical_reactions_separate": all(
            bool(row["numerical_diagnostics"]) for row in global_rows.values()
        )
        and all(
            bool(row["global_support"]["numerical_separate"]) for row in case_certificates
        ),
        "all_translation_invariant": all(
            bool(row["origin_translation_removed_by_differences"])
            and bool(row["nodes_R_X_plus_b"])
            and bool(row["permutation_rotation_commute"])
            for row in global_rows.values()
        ),
        "direct_drill_excluded": all(
            bool(row["global_support"]["load_exact"])
            and bool(row["global_support"]["support_exact"])
            for row in case_certificates
        ),
        "physical_supports_only": all(
            bool(row["global_support"]["support_exact"])
            and bool(row["global_support"]["reaction_exact"])
            for row in case_certificates
        ),
    }

    frame_failure = (
        not bool(frame_static["all_exact"])
        or any(not bool(row["exact_zero"]) for row in covariance_rows)
        or any(
            (
                not bool(row["centre"]["centre_j_positive"])
                and not bool(row["centre"]["centre_j_inconclusive"])
            )
            or not bool(row["centre"]["centre_taylor_exact"])
            or (
                not bool(row["centre"]["multiplier_gram_positive"])
                and not bool(row["centre"]["multiplier_gram_inconclusive"])
            )
            or not bool(row["centre"]["residual_mode_exact"])
            or (not bool(row["jacobian_positive"]) and not bool(row["jacobian_inconclusive"]))
            for row in diagnostic_cases
        )
    )
    algebra_failure = any(
        not bool(row["internal_invertible"])
        or not all(
            bool(row["modes"][key])
            for key in (
                "matched_state_vector_exact",
                "matched_state_null_exact",
                "common_drill_energetic",
                "translation_spin_energetic",
                "alternating_pl_null",
                "alternating_hg_energetic",
            )
        )
        or row["rank"]["rigid_rank"] != 6
        or not all(bool(value) for value in row["rank"]["rigid_nulls"].values())
        or not bool(row["rank"]["rigid_complement_orthogonal"])
        or row["rank"]["combined_basis_rank"] != 24
        or not bool(row["rank"]["rigid_quotient_cross_zero"])
        or row["rank"]["ldl_counts"]["negative"] > 0
        or row["rank"]["ldl_counts"]["exact_zero"] > 0
        or (
            row["rank"]["ldl_counts"]["positive"] != 18
            and row["rank"]["ldl_counts"]["unresolved"] == 0
        )
        or not all(
            bool(value)
            for key, value in row["stationary"].items()
            if key != "D38_digest"
        )
        for row in diagnostic_cases
    )
    patch_failure = (
        any(
            not all(bool(value) for value in row["patches"].values())
            or not all(
                bool(value)
                for key, value in row["recovery"].items()
                if key != "station_count"
            )
            or not all(bool(value) for value in row["global_support"].values())
            for row in case_certificates
        )
        or not all(bool(value) for value in recovery.values() if isinstance(value, bool))
        or not all(bool(value) for value in global_supports.values())
    )
    unresolved = bool(local_algebra["unresolved_at_1024"]) or any(
        row["status"] == "UNCLASSIFIED" for row in case_certificates
    )
    if frame_failure:
        terminal = "NO_GO_E4_PL_Q1T_PATCH_OR_COVARIANCE"
    elif algebra_failure:
        terminal = "NO_GO_E4_PL_Q1T_LOCAL_ALGEBRA"
    elif patch_failure:
        terminal = "NO_GO_E4_PL_Q1T_PATCH_OR_COVARIANCE"
    elif unresolved:
        terminal = "UNCLASSIFIED_E4_PL_Q1T_LOCAL_PLANAR_IDENTITY"
    else:
        terminal = "PROVISIONAL_GO_E4_PL_Q1T_Q1B_PLAN"

    payload = {
        "candidate_id": CANDIDATE_ID,
        "case_certificates": case_certificates,
        "classification": {
            "inconclusive": unresolved,
            "production": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
            "q1b_execution": "UNAUTHORIZED",
            "terminal": terminal,
        },
        "coverage": coverage,
        "frame_and_fields": frame_and_fields,
        "global_supports": global_supports,
        "local_algebra": local_algebra,
        "precision_bits": list(precisions),
        "recovery": recovery,
        "schema": PAYLOAD_SCHEMA,
        "study_id": STUDY_ID,
    }
    _validate_common_payload(payload)
    return {
        "schema": OUTPUT_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "study_id": STUDY_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "certificate_payload": payload,
        "certificate_payload_sha256": sha256_bytes(canonical_bytes(payload)),
        "execution_contract_sha256": contract_sha256,
        "execution_authority_sha256": authority_sha256,
        "exact_environment_sha256": contract["environment"]["sha256"],
        "implementation_diagnostics": {
            "frame": frame_static,
            "cases": diagnostic_cases,
            "covariance": covariance_rows,
            "global_rotation_origin": [global_rows[operation.id] for operation in operations],
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--static-transcription", action="store_true")
    group.add_argument("--toy-exact-backend", action="store_true")
    group.add_argument("--execute", action="store_true")
    parser.add_argument("--authority-record", type=pathlib.Path)
    parser.add_argument("--authority-sha256")
    parser.add_argument("--contract", type=pathlib.Path)
    parser.add_argument("--contract-sha256")
    parser.add_argument("--environment-root", type=pathlib.Path)
    parser.add_argument("--environment-sha256")
    parser.add_argument("--runner-id")
    parser.add_argument("--output", type=pathlib.Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.static_transcription or args.toy_exact_backend:
        if any(
            value is not None
            for value in (
                args.authority_record,
                args.authority_sha256,
                args.contract,
                args.contract_sha256,
                args.environment_root,
                args.environment_sha256,
                args.runner_id,
                args.output,
            )
        ):
            raise SystemExit("static/toy mode accepts no execution or output arguments")
        raw = canonical_bytes(
            static_transcription() if args.static_transcription else toy_exact_backend_certificate()
        )
    else:
        required = {
            "--authority-record": args.authority_record,
            "--authority-sha256": args.authority_sha256,
            "--contract": args.contract,
            "--contract-sha256": args.contract_sha256,
            "--environment-root": args.environment_root,
            "--environment-sha256": args.environment_sha256,
            "--runner-id": args.runner_id,
            "--output": args.output,
        }
        missing = [name for name, value in required.items() if value is None]
        if missing:
            raise SystemExit("registered execution requires: " + ", ".join(missing))
        if args.output.exists() or args.output.is_symlink():
            raise SystemExit("registered output path must be absent for exclusive creation")
        _validate_external_output_path(args.output)
        contract, authority_sha, capability = _validate_execution_authority(
            args.authority_record,
            args.authority_sha256,
            args.contract,
            args.contract_sha256,
            args.environment_root,
            args.environment_sha256,
            args.runner_id,
        )
        raw = canonical_bytes(
            execute(
                contract,
                contract_sha256=args.contract_sha256.upper(),
                authority_sha256=authority_sha,
                capability=capability,
            )
        )
    if args.output:
        with args.output.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        if args.output.read_bytes() != raw:
            raise IOError("registered output reopen verification failed")
    else:
        sys.stdout.buffer.write(raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
