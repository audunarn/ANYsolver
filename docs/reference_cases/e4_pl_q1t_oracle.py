#!/usr/bin/env python3
"""Independent SymPy exact oracle for the frozen E4-PL-Q1T study.

There are deliberately three disjoint entry paths:

* ``--static-transcription`` inspects constants and schemas only;
* ``--toy-exact-backend`` exercises algebraic fields and dyadic signs only;
* ``--execute`` first validates all eight caller inputs, then (and only then)
  constructs registered geometry and mechanics.

Exact equality in this module is equality of SymPy ``QQ.algebraic_field``
domain elements.  The separately constructed :class:`Expr` DAG is never an
equality authority.  It is evaluated by the standard-library-only outward
dyadic engine solely for ordered signs.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import subprocess
import sys
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence


IMPLEMENTATION_ID = "Q1T_ORACLE_SYMPY_ALGEBRAIC_FIELD"
WRAPPER_SCHEMA = "anysolver.s4.e4-pl-q1t-oracle-raw-v1"
PAYLOAD_SCHEMA = "e4_pl_q1t_common_certificate_payload_v1"
CANDIDATE_ID = "candidate_e4_pl_q1t.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1"
STUDY_ID = "study_e4_pl_q1t.q1s_frozen_identity_exact_oracle_completion_v1"
SUCCESS_TERMINAL = "PROVISIONAL_GO_E4_PL_Q1T_Q1B_PLAN"
LOCAL_NO_GO = "NO_GO_E4_PL_Q1T_LOCAL_ALGEBRA"
PATCH_NO_GO = "NO_GO_E4_PL_Q1T_PATCH_OR_COVARIANCE"
UNCLASSIFIED_TERMINAL = "UNCLASSIFIED_E4_PL_Q1T_LOCAL_PLANAR_IDENTITY"
PRODUCTION = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
PRECISION_BITS = (256, 512, 1024)
ENVIRONMENT_SHA256 = "5461206324e7fc2a52b334ce736a512ee71313ed79181438047e3e20069a9746"
EXECUTION_CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1t-execution-contract-v1"
EXECUTION_CONTRACT_PATH = "docs/reference_cases/e4_pl_q1t_execution_contract.json"
BASE_COMMIT = "914a9a633c585d45a419d97f92b4faf7fa1e4486"
BASE_TREE = "569c0b15c9e5d50835fa5fe16414d5d1864d0106"
CONTRACT_TOP_KEYS = frozenset(
    {
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
)

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = ROOT / "docs" / "reference_cases"

GEOMETRY_IDS = (
    "Q0_SQUARE",
    "Q1_AFFINE_SKEW",
    "Q2_TRAPEZOID",
    "Q3_TAPERED_SKEW",
    "Q4_HOSTILE_ASYMMETRIC_1",
    "Q5_HOSTILE_ASYMMETRIC_2",
    "Q3_TAPERED_SKEW_RSTAR_TRANSLATED",
)
OPERATION_IDS = ("E", "R90", "R180", "R270", "MR", "MS", "MD", "MA")
GAUSS_LABELS = ("GP_MM", "GP_PM", "GP_PP", "GP_MP")

TOP_LEVEL_KEYS = frozenset(
    {
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
)
CASE_KEYS = frozenset(
    {
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
)


class OracleError(RuntimeError):
    """Fail-closed oracle error."""


def _reject_constant(token: str) -> None:
    raise ValueError(f"non-finite JSON token rejected: {token}")


def _reject_duplicate(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise ValueError(f"duplicate JSON key: {key}")
        out[key] = value
    return out


def strict_json(raw: bytes) -> Any:
    if not raw.endswith(b"\n") or raw.endswith(b"\n\n") or b"\r" in raw:
        raise ValueError("canonical JSON must have one terminal LF and no CR")
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicate,
        parse_constant=_reject_constant,
    )
    if canonical_bytes(value) != raw:
        raise ValueError("JSON is not canonical sorted compact UTF-8/LF")
    return value


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode("utf-8")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _regular_nonsymlink(path: Path) -> bool:
    return path.is_file() and not path.is_symlink()


def _read_canonical(path: Path) -> tuple[bytes, Any]:
    if not _regular_nonsymlink(path):
        raise OracleError(f"not a regular non-symlink file: {path}")
    raw = path.read_bytes()
    try:
        return raw, strict_json(raw)
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise OracleError(f"invalid canonical JSON: {path}") from exc


# ---------------------------------------------------------------------------
# Independent rational/positive-root expression DAG


@dataclass(frozen=True, slots=True)
class Expr:
    op: str
    args: tuple[Any, ...]

    def __add__(self, other: object) -> "Expr":
        return expr_add(self, as_expr(other))

    def __radd__(self, other: object) -> "Expr":
        return expr_add(as_expr(other), self)

    def __sub__(self, other: object) -> "Expr":
        return expr_sub(self, as_expr(other))

    def __rsub__(self, other: object) -> "Expr":
        return expr_sub(as_expr(other), self)

    def __mul__(self, other: object) -> "Expr":
        return expr_mul(self, as_expr(other))

    def __rmul__(self, other: object) -> "Expr":
        return expr_mul(as_expr(other), self)

    def __truediv__(self, other: object) -> "Expr":
        return expr_div(self, as_expr(other))

    def __rtruediv__(self, other: object) -> "Expr":
        return expr_div(as_expr(other), self)

    def __neg__(self) -> "Expr":
        return expr_neg(self)


def expr_q(numerator: int | Fraction, denominator: int = 1) -> Expr:
    q = numerator if isinstance(numerator, Fraction) else Fraction(numerator, denominator)
    if q.denominator == 1:
        return Expr("integer", (q.numerator,))
    return Expr("rational", (q.numerator, q.denominator))


E_ZERO = expr_q(0)
E_ONE = expr_q(1)


def as_expr(value: object) -> Expr:
    if isinstance(value, Expr):
        return value
    if isinstance(value, Fraction):
        return expr_q(value)
    if isinstance(value, int):
        return expr_q(value)
    raise TypeError(f"not an expression scalar: {type(value).__name__}")


def _expr_fraction(value: Expr) -> Fraction | None:
    if value.op == "integer":
        return Fraction(value.args[0])
    if value.op == "rational":
        return Fraction(value.args[0], value.args[1])
    return None


def expr_add(left: Expr, right: Expr) -> Expr:
    if left == E_ZERO:
        return right
    if right == E_ZERO:
        return left
    a, b = _expr_fraction(left), _expr_fraction(right)
    return expr_q(a + b) if a is not None and b is not None else Expr("add", (left, right))


def expr_sub(left: Expr, right: Expr) -> Expr:
    if right == E_ZERO:
        return left
    if left == right:
        return E_ZERO
    a, b = _expr_fraction(left), _expr_fraction(right)
    return expr_q(a - b) if a is not None and b is not None else Expr("subtract", (left, right))


def expr_mul(left: Expr, right: Expr) -> Expr:
    if left == E_ZERO or right == E_ZERO:
        return E_ZERO
    if left == E_ONE:
        return right
    if right == E_ONE:
        return left
    a, b = _expr_fraction(left), _expr_fraction(right)
    return expr_q(a * b) if a is not None and b is not None else Expr("multiply", (left, right))


def expr_div(left: Expr, right: Expr) -> Expr:
    if right == E_ZERO:
        raise ZeroDivisionError("expression division by zero")
    if left == E_ZERO:
        return E_ZERO
    if right == E_ONE:
        return left
    if left == right:
        return E_ONE
    a, b = _expr_fraction(left), _expr_fraction(right)
    return expr_q(a / b) if a is not None and b is not None else Expr("divide", (left, right))


def expr_neg(value: Expr) -> Expr:
    if value == E_ZERO:
        return value
    a = _expr_fraction(value)
    if a is not None:
        return expr_q(-a)
    if value.op == "negate":
        return value.args[0]
    return Expr("negate", (value,))


def expr_sqrt(value: Expr) -> Expr:
    q = _expr_fraction(value)
    if q is not None:
        if q < 0:
            raise ValueError("positive root of negative rational")
        sn, sd = math.isqrt(q.numerator), math.isqrt(q.denominator)
        if sn * sn == q.numerator and sd * sd == q.denominator:
            return expr_q(sn, sd)
    return Expr("positive_sqrt", (value,))


@dataclass(frozen=True, slots=True)
class DyadicInterval:
    lo: Fraction
    hi: Fraction

    def __post_init__(self) -> None:
        if self.lo > self.hi:
            raise ValueError("reversed interval")


def _floor_fraction(q: Fraction) -> int:
    return q.numerator // q.denominator


def _ceil_fraction(q: Fraction) -> int:
    return -((-q.numerator) // q.denominator)


def _outward(q: Fraction, bits: int) -> DyadicInterval:
    scale = 1 << bits
    return DyadicInterval(Fraction(_floor_fraction(q * scale), scale), Fraction(_ceil_fraction(q * scale), scale))


def _sqrt_down(q: Fraction, bits: int) -> Fraction:
    if q < 0:
        raise OracleError("square root lower endpoint is negative")
    scale2 = 1 << (2 * bits)
    k = math.isqrt((q.numerator * scale2) // q.denominator)
    return Fraction(k, 1 << bits)


def _sqrt_up(q: Fraction, bits: int) -> Fraction:
    lo = _sqrt_down(q, bits)
    return lo if lo * lo == q else lo + Fraction(1, 1 << bits)


class DyadicEvaluator:
    """Outward dyadic evaluator; it has no dependency outside the stdlib."""

    def __init__(self, bits: int) -> None:
        if bits <= 0:
            raise ValueError("positive precision required")
        self.bits = bits
        self.calls = 0
        self._cache: dict[Expr, DyadicInterval] = {}

    def evaluate(self, expression: Expr) -> DyadicInterval:
        self.calls += 1
        return self._eval(expression)

    def _eval(self, expression: Expr) -> DyadicInterval:
        cached = self._cache.get(expression)
        if cached is not None:
            return cached
        op, args = expression.op, expression.args
        if op == "integer":
            result = DyadicInterval(Fraction(args[0]), Fraction(args[0]))
        elif op == "rational":
            result = _outward(Fraction(args[0], args[1]), self.bits)
        elif op in {"add", "subtract", "multiply", "divide"}:
            a, b = self._eval(args[0]), self._eval(args[1])
            if op == "add":
                result = _outward(a.lo + b.lo, self.bits)
                result = DyadicInterval(result.lo, _outward(a.hi + b.hi, self.bits).hi)
            elif op == "subtract":
                result = DyadicInterval(
                    _outward(a.lo - b.hi, self.bits).lo,
                    _outward(a.hi - b.lo, self.bits).hi,
                )
            elif op == "multiply":
                products = (a.lo * b.lo, a.lo * b.hi, a.hi * b.lo, a.hi * b.hi)
                result = DyadicInterval(
                    _outward(min(products), self.bits).lo,
                    _outward(max(products), self.bits).hi,
                )
            else:
                if b.lo <= 0 <= b.hi:
                    raise OracleError("interval denominator contains zero")
                quotients = (a.lo / b.lo, a.lo / b.hi, a.hi / b.lo, a.hi / b.hi)
                result = DyadicInterval(
                    _outward(min(quotients), self.bits).lo,
                    _outward(max(quotients), self.bits).hi,
                )
        elif op == "negate":
            a = self._eval(args[0])
            result = DyadicInterval(-a.hi, -a.lo)
        elif op == "positive_sqrt":
            a = self._eval(args[0])
            result = DyadicInterval(_sqrt_down(a.lo, self.bits), _sqrt_up(a.hi, self.bits))
        else:
            raise OracleError(f"unknown expression operation: {op}")
        self._cache[expression] = result
        return result


def expression_digest(expression: Expr) -> str:
    memo: dict[Expr, int] = {}
    rows: list[list[Any]] = []

    def visit(node: Expr) -> int:
        if node in memo:
            return memo[node]
        children: list[int | str] = []
        for arg in node.args:
            children.append(visit(arg) if isinstance(arg, Expr) else str(arg))
        index = len(rows)
        memo[node] = index
        rows.append([node.op, children])
        return index

    root = visit(expression)
    return sha256(canonical_bytes({"nodes": rows, "root": root}))


# ---------------------------------------------------------------------------
# SymPy domain coupling.  The import is intentionally lazy.


def _load_sympy() -> Any:
    try:
        import sympy  # type: ignore[import-not-found]
    except ImportError as exc:
        raise OracleError("SymPy 1.14.0 is required from the frozen external environment") from exc
    if sympy.__version__ != "1.14.0":
        raise OracleError(f"wrong SymPy version: {sympy.__version__}")
    return sympy


def _expr_to_sympy(expression: Expr, sympy: Any, memo: dict[Expr, Any] | None = None) -> Any:
    if memo is None:
        memo = {}
    if expression in memo:
        return memo[expression]
    op, args = expression.op, expression.args
    if op == "integer":
        out = sympy.Integer(args[0])
    elif op == "rational":
        out = sympy.Rational(args[0], args[1])
    elif op == "add":
        out = _expr_to_sympy(args[0], sympy, memo) + _expr_to_sympy(args[1], sympy, memo)
    elif op == "subtract":
        out = _expr_to_sympy(args[0], sympy, memo) - _expr_to_sympy(args[1], sympy, memo)
    elif op == "multiply":
        out = _expr_to_sympy(args[0], sympy, memo) * _expr_to_sympy(args[1], sympy, memo)
    elif op == "divide":
        out = _expr_to_sympy(args[0], sympy, memo) / _expr_to_sympy(args[1], sympy, memo)
    elif op == "negate":
        out = -_expr_to_sympy(args[0], sympy, memo)
    elif op == "positive_sqrt":
        out = sympy.sqrt(_expr_to_sympy(args[0], sympy, memo))
    else:
        raise OracleError(f"unknown expression operation: {op}")
    memo[expression] = out
    return out


class FieldContext:
    """One frozen five-generator geometry-group algebraic field."""

    def __init__(self, sympy: Any, roots: Sequence[Expr]) -> None:
        if len(roots) != 5:
            raise OracleError("the frozen generator schedule has exactly five roots")
        self.sympy = sympy
        self.root_expressions = tuple(roots)
        symbolic_roots = tuple(_expr_to_sympy(root, sympy) for root in roots)
        self.domain = sympy.QQ.algebraic_field(*symbolic_roots)
        degree = int(self.domain.mod.degree())
        if degree > 32:
            raise OracleError(f"formal field degree exceeds 32: {degree}")
        self.degree = degree
        self.zero = self.domain.zero
        self.one = self.domain.one
        self._cache: dict[Expr, Any] = {}

    def element(self, expression: Expr) -> Any:
        if expression not in self._cache:
            self._cache[expression] = self.domain.from_sympy(_expr_to_sympy(expression, self.sympy))
        return self._cache[expression]

    def exact(self, expression: Expr | int | Fraction) -> "Exact":
        node = as_expr(expression)
        return Exact(self, self.element(node), node)

    def positive_root(self, expression: Expr) -> "Exact":
        return self.exact(expr_sqrt(expression))


@dataclass(frozen=True, slots=True)
class Exact:
    field: FieldContext
    value: Any
    expression: Expr

    def _coerce(self, other: object) -> "Exact":
        if isinstance(other, Exact):
            if other.field is not self.field:
                raise TypeError("cross-field operation")
            return other
        if isinstance(other, (int, Fraction, Expr)):
            return self.field.exact(other)
        raise TypeError(f"not an exact scalar: {type(other).__name__}")

    def __add__(self, other: object) -> "Exact":
        b = self._coerce(other)
        return Exact(self.field, self.value + b.value, expr_add(self.expression, b.expression))

    __radd__ = __add__

    def __sub__(self, other: object) -> "Exact":
        b = self._coerce(other)
        return Exact(self.field, self.value - b.value, expr_sub(self.expression, b.expression))

    def __rsub__(self, other: object) -> "Exact":
        return self._coerce(other) - self

    def __mul__(self, other: object) -> "Exact":
        b = self._coerce(other)
        return Exact(self.field, self.value * b.value, expr_mul(self.expression, b.expression))

    __rmul__ = __mul__

    def __truediv__(self, other: object) -> "Exact":
        b = self._coerce(other)
        if b.is_zero():
            raise ZeroDivisionError("exact division by zero")
        return Exact(self.field, self.value / b.value, expr_div(self.expression, b.expression))

    def __rtruediv__(self, other: object) -> "Exact":
        return self._coerce(other) / self

    def __neg__(self) -> "Exact":
        return Exact(self.field, -self.value, expr_neg(self.expression))

    def is_zero(self) -> bool:
        return self.value == self.field.zero

    def is_equal(self, other: object) -> bool:
        return (self - other).is_zero()


def exact_sign(value: Exact, evaluators: Mapping[int, DyadicEvaluator] | None = None) -> tuple[str, int]:
    """Return POSITIVE/NEGATIVE/ZERO/UNRESOLVED and deciding precision."""
    if value.is_zero():
        return "ZERO", 0
    local = evaluators if evaluators is not None else {b: DyadicEvaluator(b) for b in PRECISION_BITS}
    for bits in PRECISION_BITS:
        interval = local[bits].evaluate(value.expression)
        if interval.lo > 0:
            return "POSITIVE", bits
        if interval.hi < 0:
            return "NEGATIVE", bits
    return "UNRESOLVED", 1024


# ---------------------------------------------------------------------------
# Small exact linear algebra, with deterministic leftmost pivoting.


Matrix = list[list[Exact]]
Vector = list[Exact]


def zeros(field: FieldContext, rows: int, cols: int) -> Matrix:
    return [[field.exact(0) for _ in range(cols)] for _ in range(rows)]


def identity(field: FieldContext, size: int) -> Matrix:
    out = zeros(field, size, size)
    for i in range(size):
        out[i][i] = field.exact(1)
    return out


def shape(matrix: Matrix) -> tuple[int, int]:
    return len(matrix), len(matrix[0]) if matrix else 0


def transpose(matrix: Matrix) -> Matrix:
    rows, cols = shape(matrix)
    return [[matrix[i][j] for i in range(rows)] for j in range(cols)]


def matmul(left: Matrix, right: Matrix) -> Matrix:
    lr, lc = shape(left)
    rr, rc = shape(right)
    if lc != rr:
        raise ValueError(f"matrix shape mismatch: {(lr, lc)} x {(rr, rc)}")
    if not left or not right:
        return []
    field = left[0][0].field
    out = zeros(field, lr, rc)
    right_t = transpose(right)
    for i in range(lr):
        for j in range(rc):
            acc = field.exact(0)
            for a, b in zip(left[i], right_t[j], strict=True):
                acc = acc + a * b
            out[i][j] = acc
    return out


def matvec(matrix: Matrix, vector: Vector) -> Vector:
    return [sum_exact((a * b for a, b in zip(row, vector, strict=True)), row[0].field) for row in matrix]


def sum_exact(values: Iterable[Exact], field: FieldContext) -> Exact:
    total = field.exact(0)
    for value in values:
        total = total + value
    return total


def matrix_add(left: Matrix, right: Matrix) -> Matrix:
    if shape(left) != shape(right):
        raise ValueError("matrix addition shape mismatch")
    return [[a + b for a, b in zip(arow, brow, strict=True)] for arow, brow in zip(left, right, strict=True)]


def matrix_sub(left: Matrix, right: Matrix) -> Matrix:
    if shape(left) != shape(right):
        raise ValueError("matrix subtraction shape mismatch")
    return [[a - b for a, b in zip(arow, brow, strict=True)] for arow, brow in zip(left, right, strict=True)]


def scalar_matrix(factor: Exact, matrix: Matrix) -> Matrix:
    return [[factor * value for value in row] for row in matrix]


def outer(left: Vector, right: Vector) -> Matrix:
    return [[a * b for b in right] for a in left]


def all_zero_matrix(matrix: Matrix) -> bool:
    return all(value.is_zero() for row in matrix for value in row)


def all_zero_vector(vector: Vector) -> bool:
    return all(value.is_zero() for value in vector)


def matrix_equal(left: Matrix, right: Matrix) -> bool:
    return shape(left) == shape(right) and all_zero_matrix(matrix_sub(left, right))


def rref(matrix: Matrix) -> tuple[Matrix, tuple[int, ...]]:
    rows, cols = shape(matrix)
    work = [row[:] for row in matrix]
    pivot_row = 0
    pivots: list[int] = []
    for col in range(cols):
        pivot = next((r for r in range(pivot_row, rows) if not work[r][col].is_zero()), None)
        if pivot is None:
            continue
        if pivot != pivot_row:
            work[pivot_row], work[pivot] = work[pivot], work[pivot_row]
        scale = work[pivot_row][col]
        work[pivot_row] = [entry / scale for entry in work[pivot_row]]
        for r in range(rows):
            if r == pivot_row or work[r][col].is_zero():
                continue
            factor = work[r][col]
            work[r] = [a - factor * b for a, b in zip(work[r], work[pivot_row], strict=True)]
        pivots.append(col)
        pivot_row += 1
        if pivot_row == rows:
            break
    return work, tuple(pivots)


def matrix_rank(matrix: Matrix) -> int:
    return len(rref(matrix)[1])


def inverse(matrix: Matrix) -> Matrix:
    rows, cols = shape(matrix)
    if rows != cols or rows == 0:
        raise ValueError("inverse requires a nonempty square matrix")
    aug = [row[:] + eye for row, eye in zip(matrix, identity(matrix[0][0].field, rows), strict=True)]
    reduced, pivots = rref(aug)
    if pivots[:rows] != tuple(range(rows)):
        raise OracleError("singular exact matrix")
    return [row[rows:] for row in reduced]


def nullspace_rref(matrix: Matrix) -> Matrix:
    """Columns are the ascending-free-coordinate exact RREF nullspace basis."""
    rows, cols = shape(matrix)
    reduced, pivots = rref(matrix)
    pivot_set = set(pivots)
    free = [j for j in range(cols) if j not in pivot_set]
    field = matrix[0][0].field
    basis: list[Vector] = []
    for free_col in free:
        v = [field.exact(0) for _ in range(cols)]
        v[free_col] = field.exact(1)
        for row, pivot_col in enumerate(pivots):
            if row < rows:
                v[pivot_col] = -reduced[row][free_col]
        basis.append(v)
    return transpose(basis) if basis else zeros(field, cols, 0)


def dot(left: Vector, right: Vector) -> Exact:
    if len(left) != len(right) or not left:
        raise ValueError("dot product shape mismatch")
    return sum_exact((a * b for a, b in zip(left, right, strict=True)), left[0].field)


def cross(left: Vector, right: Vector) -> Vector:
    if len(left) != 3 or len(right) != 3:
        raise ValueError("cross product requires three-vectors")
    return [
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    ]


def ldl_no_pivot(matrix: Matrix) -> tuple[Matrix, Vector]:
    rows, cols = shape(matrix)
    if rows != cols:
        raise ValueError("LDL requires square matrix")
    field = matrix[0][0].field
    lower = identity(field, rows)
    pivots = [field.exact(0) for _ in range(rows)]
    for i in range(rows):
        pivots[i] = matrix[i][i] - sum_exact(
            (lower[i][k] * lower[i][k] * pivots[k] for k in range(i)), field
        )
        if pivots[i].is_zero():
            continue
        for j in range(i + 1, rows):
            numerator = matrix[j][i] - sum_exact(
                (lower[j][k] * lower[i][k] * pivots[k] for k in range(i)), field
            )
            lower[j][i] = numerator / pivots[i]
    return lower, pivots


def _parse_q(text: str) -> Fraction:
    return Fraction(text)


def _static_transcription() -> dict[str, Any]:
    return {
        "case_count": 56,
        "case_keys": sorted(CASE_KEYS),
        "formal_degree_maximum": 32,
        "gauss_station_count": 224,
        "generator_ids": ["g1", "g2", "g3", "g4", "g5"],
        "implementation_id": IMPLEMENTATION_ID,
        "mechanics_executed": False,
        "payload_keys": sorted(TOP_LEVEL_KEYS),
        "precision_bits": list(PRECISION_BITS),
        "wrapper_schema": WRAPPER_SCHEMA,
    }


def toy_exact_backend() -> dict[str, Any]:
    sympy = _load_sympy()
    a_expr = expr_sqrt(expr_q(2))
    b_expr = expr_sqrt(expr_q(3) + a_expr)
    domain = sympy.QQ.algebraic_field(_expr_to_sympy(a_expr, sympy), _expr_to_sympy(b_expr, sympy))
    a = domain.from_sympy(_expr_to_sympy(a_expr, sympy))
    b = domain.from_sympy(_expr_to_sympy(b_expr, sympy))
    exact_cancellation = (a + b) - (a + b) == domain.zero
    exact_inverse = a * (domain.one / a) == domain.one
    nested_square = b * b == domain.from_sympy(_expr_to_sympy(expr_q(3) + a_expr, sympy))
    toy_field = FieldContext(sympy, (a_expr, expr_q(1), b_expr, expr_q(1), expr_sqrt(expr_q(3))))
    nested = toy_field.exact(b_expr)
    evaluators = {bits: DyadicEvaluator(bits) for bits in PRECISION_BITS}
    sign, _ = exact_sign(nested, evaluators)
    calls_before = sum(item.calls for item in evaluators.values())
    zero = toy_field.exact(a_expr - a_expr)
    zero_sign, _ = exact_sign(zero, evaluators)
    calls_after = sum(item.calls for item in evaluators.values())
    matrix = [
        [toy_field.exact(1), toy_field.exact(a_expr)],
        [toy_field.exact(a_expr), toy_field.exact(3)],
    ]
    result = {
        "domain_equalities": {
            "exact_cancellation": exact_cancellation,
            "inverse": exact_inverse,
            "nested_square": nested_square,
        },
        "implementation_id": IMPLEMENTATION_ID,
        "matrix_rank": matrix_rank(matrix),
        "mechanics_executed": False,
        "nested_positive": sign == "POSITIVE",
        "zero_never_called_intervals": zero_sign == "ZERO" and calls_before == calls_after,
    }
    if set(result["domain_equalities"].values()) != {True} or result["matrix_rank"] != 2:
        raise OracleError("toy exact backend self-test failed")
    return result


# ---------------------------------------------------------------------------
# Frozen geometry and source mechanics.  Nothing below is called by static or
# toy modes, nor before the execute guard has returned successfully.


@dataclass(frozen=True, slots=True)
class Operation:
    operation_id: str
    natural_map: tuple[tuple[int, int], tuple[int, int]]
    node_tuple: tuple[int, int, int, int]
    determinant: int


@dataclass(slots=True)
class Geometry:
    geometry_id: str
    operation: Operation
    field: FieldContext
    nodes: list[Vector]
    frame: Matrix
    local_nodes: list[tuple[Exact, Exact]]
    coefficients: dict[str, Exact]
    roots: tuple[Exact, ...]
    frame_exact: bool


@dataclass(slots=True)
class LocalMechanics:
    geometry: Geometry
    gauss: list[tuple[Exact, Exact]]
    d38: Matrix
    q38: Matrix
    d38_inverse: Matrix
    k24: Matrix
    core_k24: Matrix
    pl_k24: Matrix
    hourglass_k24: Matrix
    rigid: Matrix
    quotient: Matrix
    ldl_pivots: Vector
    ldl_signs: list[str]
    n_sigma: list[Matrix]
    n_epsilon: list[Matrix]
    compatible_b: list[Matrix]
    c_taylor: Matrix
    residual_gamma: Vector
    internal_invertible: bool
    mixed_condensed_exact: bool
    numerical_modes: dict[str, bool]
    ordered_unresolved: bool
    probe_vectors: dict[str, Vector]
    patch_vectors: dict[str, Vector]
    registered_load_global: Vector | None
    registered_support_global: Matrix | None
    exact_local_contradiction: bool


@dataclass(frozen=True, slots=True)
class MechanicsFailure:
    geometry: Geometry
    category: str
    reason: str
    unresolved: bool


def _load_frozen_json(filename: str) -> Any:
    _, value = _read_canonical(REFERENCE_DIR / filename)
    return value


def _frozen_inputs() -> tuple[list[tuple[str, list[list[str]]]], list[Operation], dict[str, Any], dict[str, Any]]:
    geometry_contract = _load_frozen_json("e4_pl_q1r_geometry_contract.json")
    frame_contract = _load_frozen_json("e4_pl_q1r_frame_contract.json")
    material_contract = _load_frozen_json("e4_pl_q1r_material_contract.json")
    cases = _load_frozen_json("e4_pl_q1r_cases.json")
    geometries = [(row["id"], row["nodes"]) for row in geometry_contract["geometries"]]
    transform = geometry_contract["global_transform"]
    geometries.append((transform["id"], transform["derived_nodes"]))
    if tuple(item[0] for item in geometries) != GEOMETRY_IDS:
        raise OracleError("frozen geometry ordering changed")
    operations = [
        Operation(
            row["id"],
            tuple(tuple(int(v) for v in line) for line in row["A"]),  # type: ignore[arg-type]
            tuple(int(v) for v in row["node_tuple"]),
            int(row["det"]),
        )
        for row in frame_contract["d4"]["operations"]
    ]
    if tuple(row.operation_id for row in operations) != OPERATION_IDS:
        raise OracleError("frozen D4 ordering changed")
    return geometries, operations, material_contract, cases


def _expr_vector(values: Sequence[str]) -> list[Expr]:
    return [expr_q(_parse_q(value)) for value in values]


def _field_schedule(node_text: Sequence[Sequence[str]], sympy: Any) -> tuple[FieldContext, tuple[Expr, ...]]:
    nodes = [_expr_vector(row) for row in node_text]
    d1 = [nodes[2][i] - nodes[0][i] for i in range(3)]
    d2 = [nodes[1][i] - nodes[3][i] for i in range(3)]
    g1 = expr_sqrt(sum((v * v for v in d1), E_ZERO))
    g2 = expr_sqrt(sum((v * v for v in d2), E_ZERO))
    unit_sum = [d1[i] / g1 + d2[i] / g2 for i in range(3)]
    g3 = expr_sqrt(sum((v * v for v in unit_sum), E_ZERO))
    raw_cross = [
        d1[1] * d2[2] - d1[2] * d2[1],
        d1[2] * d2[0] - d1[0] * d2[2],
        d1[0] * d2[1] - d1[1] * d2[0],
    ]
    g4 = expr_sqrt(sum((v * v for v in raw_cross), E_ZERO))
    g5 = expr_sqrt(expr_q(3))
    schedule = (g1, g2, g3, g4, g5)
    field = FieldContext(sympy, schedule)
    roots = tuple(field.exact(item) for item in schedule)
    for root in roots:
        sign, _ = exact_sign(root)
        if sign != "POSITIVE":
            raise OracleError("a frozen field generator is not certified positive")
    return field, schedule


def _numbered_geometry(
    geometry_id: str,
    node_text: Sequence[Sequence[str]],
    operation: Operation,
    sympy: Any,
    field_cache: dict[str, tuple[FieldContext, tuple[Expr, ...]]],
) -> Geometry:
    if geometry_id not in field_cache:
        field_cache[geometry_id] = _field_schedule(node_text, sympy)
    field, schedule = field_cache[geometry_id]
    base_nodes = [[field.exact(expr_q(_parse_q(value))) for value in row] for row in node_text]
    nodes = [base_nodes[index - 1] for index in operation.node_tuple]
    roots = tuple(field.exact(root) for root in schedule)
    g1, g2, g3, g4, _ = roots
    d1 = [nodes[2][i] - nodes[0][i] for i in range(3)]
    d2 = [nodes[1][i] - nodes[3][i] for i in range(3)]
    # Numbered diagonal norms are schedule roots up to the exact D4 swaps.
    d1_norm = g1 if operation.operation_id in {"E", "R180", "MD", "MA"} else g2
    d2_norm = g2 if operation.operation_id in {"E", "R180", "MD", "MA"} else g1
    a = [value / d1_norm for value in d1]
    b = [value / d2_norm for value in d2]
    plus = [a[i] + b[i] for i in range(3)]
    minus = [a[i] - b[i] for i in range(3)]
    # |a+b| is g3 for E and is either g3 or the derived complementary norm
    # after signed swaps.  No sixth generator is constructed.
    complement = field.exact(2) * g4 / (g1 * g2 * g3)
    plus_norm = g3 if operation.operation_id in {"E", "R180", "MR", "MS"} else complement
    minus_norm = complement if operation.operation_id in {"E", "R180", "MR", "MS"} else g3
    t1 = [value / plus_norm for value in plus]
    t2 = [value / minus_norm for value in minus]
    t3 = cross(t1, t2)
    frame = transpose([t1, t2, t3])
    gram = matmul(transpose(frame), frame)
    frame_exact = matrix_equal(gram, identity(field, 3))
    centre = [sum_exact((node[k] for node in nodes), field) / 4 for k in range(3)]
    local_nodes: list[tuple[Exact, Exact]] = []
    for node in nodes:
        relative = [node[k] - centre[k] for k in range(3)]
        local_nodes.append((dot(t1, relative), dot(t2, relative)))
    x = [item[0] for item in local_nodes]
    y = [item[1] for item in local_nodes]

    def modal(values: Vector) -> tuple[Exact, Exact, Exact, Exact]:
        return (
            sum_exact(values, field) / 4,
            (-values[0] + values[1] + values[2] - values[3]) / 4,
            (-values[0] - values[1] + values[2] + values[3]) / 4,
            (values[0] - values[1] + values[2] - values[3]) / 4,
        )

    x0, xr, xs, xrs = modal(x)
    y0, yr, ys, yrs = modal(y)
    jc = xr * ys - xs * yr
    jr = xr * yrs - xrs * yr
    js = xrs * ys - xs * yrs
    coefficients = {
        "x0": x0,
        "xr": xr,
        "xs": xs,
        "xrs": xrs,
        "y0": y0,
        "yr": yr,
        "ys": ys,
        "yrs": yrs,
        "jc": jc,
        "jr": jr,
        "js": js,
    }
    return Geometry(geometry_id, operation, field, nodes, frame, local_nodes, coefficients, roots, frame_exact)


def _gauss_points(field: FieldContext, g5: Exact) -> list[tuple[Exact, Exact]]:
    a = g5 / 3
    return [(-a, -a), (a, -a), (a, a), (-a, a)]


def _jacobian(geometry: Geometry, r: Exact, s: Exact) -> tuple[Exact, Exact, Exact, Exact, Exact]:
    c = geometry.coefficients
    xr = c["xr"] + c["xrs"] * s
    xs = c["xs"] + c["xrs"] * r
    yr = c["yr"] + c["yrs"] * s
    ys = c["ys"] + c["yrs"] * r
    determinant = xr * ys - xs * yr
    return xr, xs, yr, ys, determinant


def _shape_derivatives(field: FieldContext, r: Exact, s: Exact) -> tuple[Vector, Vector]:
    one = field.exact(1)
    nr = [-(one - s) / 4, (one - s) / 4, (one + s) / 4, -(one + s) / 4]
    ns = [-(one - r) / 4, -(one + r) / 4, (one + r) / 4, (one - r) / 4]
    return nr, ns


def _modal_rows(field: FieldContext) -> tuple[Vector, Vector, Vector, Vector]:
    return (
        [field.exact(Fraction(1, 4))] * 4,
        [field.exact(Fraction(-1, 4)), field.exact(Fraction(1, 4)), field.exact(Fraction(1, 4)), field.exact(Fraction(-1, 4))],
        [field.exact(Fraction(-1, 4)), field.exact(Fraction(-1, 4)), field.exact(Fraction(1, 4)), field.exact(Fraction(1, 4))],
        [field.exact(Fraction(1, 4)), field.exact(Fraction(-1, 4)), field.exact(Fraction(1, 4)), field.exact(Fraction(-1, 4))],
    )


def _compatible_b(geometry: Geometry, r: Exact, s: Exact) -> Matrix:
    field = geometry.field
    nr, ns = _shape_derivatives(field, r, s)
    xr, xs, yr, ys, jac = _jacobian(geometry, r, s)
    nx = [(ys * nr[i] - yr * ns[i]) / jac for i in range(4)]
    ny = [(-xs * nr[i] + xr * ns[i]) / jac for i in range(4)]
    out = zeros(field, 8, 20)
    for i in range(4):
        base = 5 * i
        out[0][base] = nx[i]
        out[1][base + 1] = ny[i]
        out[2][base] = ny[i]
        out[2][base + 1] = nx[i]
        out[3][base + 4] = nx[i]
        out[4][base + 3] = -ny[i]
        out[5][base + 4] = ny[i]
        out[5][base + 3] = -nx[i]
    f0, fr, fs, frs = _modal_rows(field)
    tr = [field.exact(0) for _ in range(20)]
    ts = [field.exact(0) for _ in range(20)]
    x_r = xr
    x_s = xs
    y_r = yr
    y_s = ys
    for i in range(4):
        base = 5 * i
        tr[base + 2] = fr[i] + s * frs[i]
        ts[base + 2] = fs[i] + r * frs[i]
        tr[base + 4] = x_r * (f0[i] + s * fs[i])
        tr[base + 3] = -y_r * (f0[i] + s * fs[i])
        ts[base + 4] = x_s * (f0[i] + r * fr[i])
        ts[base + 3] = -y_s * (f0[i] + r * fr[i])
    out[6] = [(ys * tr[i] - yr * ts[i]) / jac for i in range(20)]
    out[7] = [(-xs * tr[i] + xr * ts[i]) / jac for i in range(20)]
    return out


def _tensor_transform(field: FieldContext, xr: Exact, xs: Exact, yr: Exact, ys: Exact, a: int, b: int) -> Matrix:
    # J_wg = [[x_r,y_r],[x_s,y_s]]; the printed T(a,b) is used verbatim.
    j11, j12, j21, j22 = xr, yr, xs, ys
    return [
        [j11 * j11, j21 * j21, field.exact(a) * j11 * j21],
        [j12 * j12, j22 * j22, field.exact(a) * j12 * j22],
        [field.exact(b) * j11 * j12, field.exact(b) * j21 * j22, j11 * j22 + j12 * j21],
    ]


def _independent_interpolations(geometry: Geometry, r: Exact, s: Exact) -> tuple[Matrix, Matrix]:
    field = geometry.field
    c = geometry.coefficients
    jc, jr, js = c["jc"], c["jr"], c["js"]
    rbar, sbar = jr / (3 * jc), js / (3 * jc)
    t_sigma = _tensor_transform(field, c["xr"], c["xs"], c["yr"], c["ys"], 2, 1)
    t_epsilon = _tensor_transform(field, c["xr"], c["xs"], c["yr"], c["ys"], 1, 2)
    t_shear = [[c["xr"], c["xs"]], [c["yr"], c["ys"]]]
    nsigma = zeros(field, 8, 14)
    nepsilon = zeros(field, 8, 21)
    for i in range(8):
        nsigma[i][i] = field.exact(1)
        nepsilon[i][i] = field.exact(1)
    seed = [[s - sbar, field.exact(0)], [field.exact(0), r - rbar], [field.exact(0), field.exact(0)]]
    stress_vary = matmul(t_sigma, seed)
    strain_vary = matmul(t_epsilon, seed)
    for block_row, first_column in ((0, 8), (3, 10)):
        for i in range(3):
            for j in range(2):
                nsigma[block_row + i][first_column + j] = stress_vary[i][j]
                nepsilon[block_row + i][first_column + j] = strain_vary[i][j]
    shear_seed = [[s - sbar, field.exact(0)], [field.exact(0), r - rbar]]
    shear_vary = matmul(t_shear, shear_seed)
    for i in range(2):
        for j in range(2):
            nsigma[6 + i][12 + j] = shear_vary[i][j]
            nepsilon[6 + i][12 + j] = shear_vary[i][j]
    m7 = [
        [r, field.exact(0), field.exact(0), field.exact(0), r * s, field.exact(0), field.exact(0)],
        [field.exact(0), s, field.exact(0), field.exact(0), field.exact(0), r * s, field.exact(0)],
        [field.exact(0), field.exact(0), r, s, field.exact(0), field.exact(0), r * s],
    ]
    _, _, _, _, jac = _jacobian(geometry, r, s)
    enrichment = scalar_matrix(jc / jac, matmul(t_epsilon, m7))
    for i in range(3):
        for j in range(7):
            nepsilon[i][14 + j] = enrichment[i][j]
    return nsigma, nepsilon


def _constitutive(field: FieldContext, contract: Mapping[str, Any]) -> Matrix:
    result = zeros(field, 8, 8)
    blocks = (
        (0, contract["constitutive"]["membrane_A"]),
        (3, contract["constitutive"]["bending_D"]),
        (6, contract["constitutive"]["transverse_shear_A_s"]),
    )
    for offset, block in blocks:
        for i, row in enumerate(block):
            for j, value in enumerate(row):
                result[offset + i][offset + j] = field.exact(expr_q(_parse_q(value)))
    return result


def _centre_taylor(geometry: Geometry) -> Matrix:
    field = geometry.field
    c = geometry.coefficients
    jc, jr, js = c["jc"], c["jr"], c["js"]
    f0, fr, fs, frs = _modal_rows(field)
    out = zeros(field, 3, 24)
    for coordinate in range(24):
        node = coordinate // 6
        component = coordinate % 6
        ur = fr[node] if component == 0 else field.exact(0)
        us = fs[node] if component == 0 else field.exact(0)
        urs = frs[node] if component == 0 else field.exact(0)
        vr = fr[node] if component == 1 else field.exact(0)
        vs = fs[node] if component == 1 else field.exact(0)
        vrs = frs[node] if component == 1 else field.exact(0)
        d0 = f0[node] if component == 5 else field.exact(0)
        dr = fr[node] if component == 5 else field.exact(0)
        ds = fs[node] if component == 5 else field.exact(0)
        n0 = -c["xs"] * ur + c["xr"] * us - c["ys"] * vr + c["yr"] * vs
        nr = -c["xrs"] * ur + c["xr"] * urs - c["yrs"] * vr + c["yr"] * vrs
        ns = -c["xs"] * urs + c["xrs"] * us - c["ys"] * vrs + c["yrs"] * vs
        out[0][coordinate] = d0 + n0 / (2 * jc)
        out[1][coordinate] = dr + (nr * jc - n0 * jr) / (2 * jc * jc)
        out[2][coordinate] = ds + (ns * jc - n0 * js) / (2 * jc * jc)
    return out


def _residual_gamma(geometry: Geometry) -> Vector:
    field = geometry.field
    x = [item[0] for item in geometry.local_nodes]
    y = [item[1] for item in geometry.local_nodes]
    xc, yc = geometry.coefficients["x0"], geometry.coefficients["y0"]
    s1 = [value - xc for value in x]
    s2 = [value - yc for value in y]
    xi = [field.exact(value) for value in (-1, 1, 1, -1)]
    eta = [field.exact(value) for value in (-1, -1, 1, 1)]
    h4 = [field.exact(value) for value in (1, -1, 1, -1)]
    area = 4 * geometry.coefficients["jc"]
    b1 = [((dot(eta, s2) * xi[i]) - (dot(xi, s2) * eta[i])) / (4 * area) for i in range(4)]
    b2 = [(-(dot(eta, s1) * xi[i]) + (dot(xi, s1) * eta[i])) / (4 * area) for i in range(4)]
    return [(h4[i] - dot(h4, s1) * b1[i] - dot(h4, s2) * b2[i]) / 4 for i in range(4)]


def _embed_20x35(field: FieldContext, q20: Matrix) -> Matrix:
    out = zeros(field, 24, 35)
    for node in range(4):
        for component in range(5):
            out[6 * node + component] = q20[5 * node + component][:]
    return out


def _assemble_local(
    geometry: Geometry,
    material: Mapping[str, Any],
    base_mechanics: LocalMechanics | None = None,
) -> LocalMechanics | MechanicsFailure:
    field = geometry.field
    gauss = _gauss_points(field, geometry.roots[4])
    jacobian_signs = [exact_sign(geometry.coefficients["jc"])[0]] + [
        exact_sign(_jacobian(geometry, r, s)[4])[0] for r, s in gauss
    ]
    if any(sign == "UNRESOLVED" for sign in jacobian_signs):
        return MechanicsFailure(geometry, "UNCLASSIFIED", "JACOBIAN_SIGN_UNRESOLVED", True)
    if any(sign != "POSITIVE" for sign in jacobian_signs):
        return MechanicsFailure(geometry, "PATCH", "JACOBIAN_NOT_CERTIFIED_POSITIVE", False)
    constitutive = _constitutive(field, material)
    f_block = zeros(field, 21, 14)
    gq = zeros(field, 14, 20)
    h_block = zeros(field, 21, 21)
    nsigma_rows: list[Matrix] = []
    nepsilon_rows: list[Matrix] = []
    compatible_rows: list[Matrix] = []
    for r, s in gauss:
        _, _, _, _, jac = _jacobian(geometry, r, s)
        nsigma, nepsilon = _independent_interpolations(geometry, r, s)
        compatible = _compatible_b(geometry, r, s)
        nsigma_rows.append(nsigma)
        nepsilon_rows.append(nepsilon)
        compatible_rows.append(compatible)
        f_block = matrix_sub(f_block, scalar_matrix(jac, matmul(transpose(nepsilon), nsigma)))
        gq = matrix_add(gq, scalar_matrix(jac, matmul(transpose(nsigma), compatible)))
        h_block = matrix_add(
            h_block,
            scalar_matrix(jac, matmul(matmul(transpose(nepsilon), constitutive), nepsilon)),
        )
    d35 = zeros(field, 35, 35)
    for i in range(14):
        for j in range(21):
            d35[i][14 + j] = f_block[j][i]
            d35[14 + j][i] = f_block[j][i]
    for i in range(21):
        for j in range(21):
            d35[14 + i][14 + j] = h_block[i][j]
    q20 = zeros(field, 20, 35)
    gq_t = transpose(gq)
    for i in range(20):
        for j in range(14):
            q20[i][j] = gq_t[i][j]
    q_core = _embed_20x35(field, q20)
    c_taylor = _centre_taylor(geometry)
    t = field.exact(expr_q(_parse_q(material["exact_parameters"]["t"])))
    shear_modulus = field.exact(expr_q(_parse_q(material["exact_parameters"]["G"])))
    epsilon = field.exact(expr_q(_parse_q(material["exact_parameters"]["epsilon_hg"])))
    gram = zeros(field, 3, 3)
    for r, s in gauss:
        _, _, _, _, jac = _jacobian(geometry, r, s)
        p = [field.exact(1), r, s]
        gram = matrix_add(gram, scalar_matrix(t * jac, outer(p, p)))
    b_pl = matmul(gram, c_taylor)
    d38 = zeros(field, 38, 38)
    for i in range(35):
        for j in range(35):
            d38[i][j] = d35[i][j]
    minus_compliance = scalar_matrix(-field.exact(1) / shear_modulus, gram)
    for i in range(3):
        for j in range(3):
            d38[35 + i][35 + j] = minus_compliance[i][j]
    q38 = zeros(field, 24, 38)
    for i in range(24):
        for j in range(35):
            q38[i][j] = q_core[i][j]
        for j in range(3):
            q38[i][35 + j] = b_pl[j][i]
    internal_invertible = matrix_rank(d38) == 38
    if not internal_invertible:
        return MechanicsFailure(geometry, "LOCAL", "D38_EXACT_SINGULAR", False)
    d38_inverse = inverse(d38)
    core_k24 = scalar_matrix(field.exact(-1), matmul(matmul(q_core, inverse(d35)), transpose(q_core)))
    pl_k24 = scalar_matrix(
        shear_modulus,
        matmul(matmul(transpose(c_taylor), gram), c_taylor),
    )
    gamma = _residual_gamma(geometry)
    gamma24 = [field.exact(0) for _ in range(24)]
    for node in range(4):
        gamma24[6 * node + 5] = gamma[node]
    hourglass_factor = 2 * epsilon * shear_modulus * t * (4 * geometry.coefficients["jc"])
    hourglass_k24 = scalar_matrix(hourglass_factor, outer(gamma24, gamma24))
    condensed_from_mixed = scalar_matrix(field.exact(-1), matmul(matmul(q38, d38_inverse), transpose(q38)))
    k24 = matrix_add(condensed_from_mixed, hourglass_k24)
    separated = matrix_add(matrix_add(core_k24, pl_k24), hourglass_k24)
    tangent_parity = matrix_equal(k24, separated)
    # A nontrivial exact probe certifies energy, work, and residual parity from
    # the same 38-field stationary system, rather than from a chosen witness.
    probe = [field.exact((index % 7) - 3) for index in range(24)]
    internal = [-(value) for value in matvec(d38_inverse, matvec(transpose(q38), probe))]
    mixed_residual = [a + b for a, b in zip(matvec(q38, internal), matvec(hourglass_k24, probe), strict=True)]
    condensed_residual = matvec(k24, probe)
    residual_parity = all_zero_vector([a - b for a, b in zip(mixed_residual, condensed_residual, strict=True)])
    internal_energy = dot(internal, matvec(d38, internal)) / 2
    coupling_energy = dot(probe, matvec(q38, internal))
    hourglass_energy = dot(probe, matvec(hourglass_k24, probe)) / 2
    condensed_energy = dot(probe, condensed_residual) / 2
    energy_parity = (internal_energy + coupling_energy + hourglass_energy - condensed_energy).is_zero()
    virtual = [field.exact(((index * 3) % 11) - 5) for index in range(24)]
    work_parity = (dot(virtual, mixed_residual) - dot(virtual, condensed_residual)).is_zero()
    mixed_condensed_exact = tangent_parity and residual_parity and energy_parity and work_parity
    rigid = (
        _rigid_matrix(geometry)
        if base_mechanics is None
        else _transport_local_columns(base_mechanics.geometry, geometry, base_mechanics.rigid)
    )
    if shape(rigid) != (24, 6) or matrix_rank(rigid) != 6:
        return MechanicsFailure(geometry, "LOCAL", "TRANSPORTED_RIGID_MATRIX_RANK_NOT_SIX", False)
    quotient = nullspace_rref(transpose(rigid))
    if shape(quotient) != (24, 18):
        raise OracleError("rigid quotient does not have frozen 24x18 shape")
    restricted = matmul(matmul(transpose(quotient), k24), quotient)
    _, pivots = ldl_no_pivot(restricted)
    signs = [exact_sign(value)[0] for value in pivots]
    probes = (
        _base_numerical_probe_vectors(geometry)
        if base_mechanics is None
        else {
            name: _transport_local_vector(base_mechanics.geometry, geometry, vector)
            for name, vector in base_mechanics.probe_vectors.items()
        }
    )
    patch_vectors = (
        {name: _local_patch_vector(geometry, name) for name in ("membrane", "bending", "shear", "combined")}
        if base_mechanics is None
        else {
            name: _transport_local_vector(base_mechanics.geometry, geometry, vector)
            for name, vector in base_mechanics.patch_vectors.items()
        }
    )
    mechanics = LocalMechanics(
        geometry,
        gauss,
        d38,
        q38,
        d38_inverse,
        k24,
        core_k24,
        pl_k24,
        hourglass_k24,
        rigid,
        quotient,
        pivots,
        signs,
        nsigma_rows,
        nepsilon_rows,
        compatible_rows,
        c_taylor,
        gamma,
        internal_invertible,
        mixed_condensed_exact,
        {},
        False,
        probes,
        patch_vectors,
        None,
        None,
        False,
    )
    modes, mode_unresolved, mode_exact_contradiction = _numerical_mode_certificate(mechanics, probes)
    mechanics.numerical_modes = modes
    mechanics.ordered_unresolved = mode_unresolved
    mechanics.exact_local_contradiction = (not mixed_condensed_exact) or mode_exact_contradiction
    mechanics.mixed_condensed_exact = mechanics.mixed_condensed_exact and all(modes.values())
    return mechanics


def _rigid_matrix(geometry: Geometry) -> Matrix:
    field = geometry.field
    result = zeros(field, 24, 6)
    for node, (x, y) in enumerate(geometry.local_nodes):
        base = 6 * node
        result[base][0] = field.exact(1)
        result[base + 1][1] = field.exact(1)
        result[base + 2][2] = field.exact(1)
        result[base + 2][3] = y
        result[base + 3][3] = field.exact(1)
        result[base + 2][4] = -x
        result[base + 4][4] = field.exact(1)
        result[base][5] = -y
        result[base + 1][5] = x
        result[base + 5][5] = field.exact(1)
    return result


def _block_frame(frame: Matrix) -> Matrix:
    field = frame[0][0].field
    result = zeros(field, 24, 24)
    for node in range(4):
        for block in range(2):
            for i in range(3):
                for j in range(3):
                    result[6 * node + 3 * block + i][6 * node + 3 * block + j] = frame[i][j]
    return result


def _t5_qd(frame: Matrix) -> tuple[Matrix, Matrix]:
    field = frame[0][0].field
    t5 = zeros(field, 24, 20)
    qd = zeros(field, 24, 4)
    for node in range(4):
        for i in range(3):
            for j in range(3):
                t5[6 * node + i][5 * node + j] = frame[i][j]
            for j in range(2):
                t5[6 * node + 3 + i][5 * node + 3 + j] = frame[i][j]
            qd[6 * node + 3 + i][node] = frame[i][2]
    return t5, qd


def _permutation(field: FieldContext, operation: Operation, block_size: int) -> Matrix:
    result = zeros(field, 4 * block_size, 4 * block_size)
    for new_node, base_node_one in enumerate(operation.node_tuple):
        base_node = base_node_one - 1
        for component in range(block_size):
            result[block_size * new_node + component][block_size * base_node + component] = field.exact(1)
    return result


def _ahat(field: FieldContext, operation: Operation) -> Matrix:
    a = operation.natural_map
    return [
        [field.exact(a[0][0]), field.exact(a[0][1]), field.exact(0)],
        [field.exact(a[1][0]), field.exact(a[1][1]), field.exact(0)],
        [field.exact(0), field.exact(0), field.exact(operation.determinant)],
    ]


def _frame_identity(base: Geometry, current: Geometry) -> bool:
    expected = matmul(base.frame, _ahat(base.field, current.operation))
    return matrix_equal(current.frame, expected)


def _global_matrix(local: Matrix, frame: Matrix) -> Matrix:
    rotation = _block_frame(frame)
    return matmul(matmul(rotation, local), transpose(rotation))


def _global_vector(local: Vector, frame: Matrix) -> Vector:
    return matvec(_block_frame(frame), local)


def _transport_local_vector(base: Geometry, current: Geometry, vector: Vector) -> Vector:
    """Transport one E-source vector by the frozen node-only global action."""
    global_base = _global_vector(vector, base.frame)
    permutation = _permutation(current.field, current.operation, 6)
    global_current = matvec(permutation, global_base)
    return matvec(transpose(_block_frame(current.frame)), global_current)


def _transport_local_columns(base: Geometry, current: Geometry, columns: Matrix) -> Matrix:
    return transpose(
        [_transport_local_vector(base, current, column) for column in transpose(columns)]
    )


def _base_numerical_probe_vectors(geometry: Geometry) -> dict[str, Vector]:
    field = geometry.field
    common = [field.exact(0) for _ in range(24)]
    spin_only = [field.exact(0) for _ in range(24)]
    matched = [field.exact(0) for _ in range(24)]
    alternating = [field.exact(0) for _ in range(24)]
    for node, (x, y) in enumerate(geometry.local_nodes):
        common[6 * node + 5] = field.exact(1)
        spin_only[6 * node] = -y
        spin_only[6 * node + 1] = x
        matched[6 * node] = -y
        matched[6 * node + 1] = x
        matched[6 * node + 5] = field.exact(1)
        alternating[6 * node + 5] = field.exact((1, -1, 1, -1)[node])
    return {
        "common_drill": common,
        "translation_only_spin": spin_only,
        "matched_rigid": matched,
        "alternating_drill": alternating,
    }


def _numerical_mode_certificate(
    mechanics: LocalMechanics,
    probes: Mapping[str, Vector],
) -> tuple[dict[str, bool], bool, bool]:
    common_energy = dot(probes["common_drill"], matvec(mechanics.k24, probes["common_drill"]))
    spin_energy = dot(probes["translation_only_spin"], matvec(mechanics.k24, probes["translation_only_spin"]))
    alternating_hourglass = dot(
        probes["alternating_drill"],
        matvec(mechanics.hourglass_k24, probes["alternating_drill"]),
    )
    signs = [exact_sign(value)[0] for value in (common_energy, spin_energy, alternating_hourglass)]
    certificate = {
        "common_drill_energetic": signs[0] == "POSITIVE",
        "translation_only_spin_energetic": signs[1] == "POSITIVE",
        "matched_rigid_combination_null": all_zero_vector(matvec(mechanics.k24, probes["matched_rigid"])),
        "alternating_retained_pl_null": all_zero_vector(matvec(mechanics.pl_k24, probes["alternating_drill"])),
        "alternating_hourglass_energetic": signs[2] == "POSITIVE",
    }
    unresolved = any(sign == "UNRESOLVED" for sign in signs)
    exact_contradiction = (
        any(sign in {"ZERO", "NEGATIVE"} for sign in signs)
        or not certificate["matched_rigid_combination_null"]
        or not certificate["alternating_retained_pl_null"]
    )
    return certificate, unresolved, exact_contradiction


def _cross_field_matrix_equal(target_field: FieldContext, left: Matrix, right: Matrix) -> bool:
    if shape(left) != shape(right):
        return False
    for left_row, right_row in zip(left, right, strict=True):
        for a, b in zip(left_row, right_row, strict=True):
            converted = target_field.exact(b.expression)
            if not (a - converted).is_zero():
                return False
    return True


def _local_patch_vector(geometry: Geometry, patch: str) -> Vector:
    field = geometry.field
    q = [field.exact(0) for _ in range(24)]
    for node, (x, y) in enumerate(geometry.local_nodes):
        u = v = w = tx = ty = drill = field.exact(0)
        if patch in {"membrane", "combined"}:
            u = u + 2 * x + y / 3
            v = v - 2 * x / 5 + 4 * y / 3
            drill = drill - field.exact(Fraction(11, 30))
        if patch in {"bending", "combined"}:
            w = w - x * x / 5 + y * y / 6 - 3 * x * y / 14
            tx = tx + y / 3 - 3 * x / 14
            ty = ty + 2 * x / 5 + 3 * y / 14
        if patch in {"shear", "combined"}:
            tx = tx + field.exact(Fraction(1, 4))
            ty = ty + field.exact(Fraction(2, 3))
        q[6 * node : 6 * node + 6] = [u, v, w, tx, ty, drill]
    return q


def _physical20(local24: Vector) -> Vector:
    return [local24[6 * node + component] for node in range(4) for component in range(5)]


def _expected_patch_strain(field: FieldContext, patch: str) -> Vector:
    result = [field.exact(0) for _ in range(8)]
    if patch in {"membrane", "combined"}:
        result[0:3] = [field.exact(2), field.exact(Fraction(4, 3)), field.exact(Fraction(-1, 15))]
    if patch in {"bending", "combined"}:
        result[3:6] = [field.exact(Fraction(2, 5)), field.exact(Fraction(-1, 3)), field.exact(Fraction(3, 7))]
    if patch in {"shear", "combined"}:
        result[6:8] = [field.exact(Fraction(2, 3)), field.exact(Fraction(-1, 4))]
    return result


def _stationary_internal(mechanics: LocalMechanics, local24: Vector) -> Vector:
    return [
        -value
        for value in matvec(
            mechanics.d38_inverse,
            matvec(transpose(mechanics.q38), local24),
        )
    ]


def _corresponding_base_station(base: LocalMechanics, current: LocalMechanics, station: int) -> int:
    field = current.geometry.field
    a = current.geometry.operation.natural_map
    r, s = current.gauss[station]
    mapped = (
        field.exact(a[0][0]) * r + field.exact(a[0][1]) * s,
        field.exact(a[1][0]) * r + field.exact(a[1][1]) * s,
    )
    for index, (br, bs) in enumerate(base.gauss):
        if mapped[0].is_equal(field.exact(br.expression)) and mapped[1].is_equal(field.exact(bs.expression)):
            return index
    raise OracleError("frozen Gauss correspondence is not a permutation")


def _field_transport_8(field: FieldContext, operation: Operation, *, resultant: bool) -> Matrix:
    a = operation.natural_map
    aa, ab = field.exact(a[0][0]), field.exact(a[0][1])
    ac, ad = field.exact(a[1][0]), field.exact(a[1][1])
    if resultant:
        tensor = [
            [aa * aa, ab * ab, 2 * aa * ab],
            [ac * ac, ad * ad, 2 * ac * ad],
            [aa * ac, ab * ad, aa * ad + ab * ac],
        ]
    else:
        tensor = [
            [aa * aa, ab * ab, aa * ab],
            [ac * ac, ad * ad, ac * ad],
            [2 * aa * ac, 2 * ab * ad, aa * ad + ab * ac],
        ]
    delta = field.exact(operation.determinant)
    result = zeros(field, 8, 8)
    for i in range(3):
        for j in range(3):
            result[i][j] = tensor[i][j]
            result[3 + i][3 + j] = delta * tensor[i][j]
    result[6][6] = delta * aa
    result[6][7] = delta * ab
    result[7][6] = delta * ac
    result[7][7] = delta * ad
    return result


def _patch_and_recovery(
    base: LocalMechanics,
    mechanics: LocalMechanics,
    material: Mapping[str, Any],
) -> tuple[dict[str, bool], dict[str, bool | int], bool]:
    field = mechanics.geometry.field
    constitutive = _constitutive(field, material)
    strain_transport = _field_transport_8(field, mechanics.geometry.operation, resultant=False)
    resultant_transport = _field_transport_8(field, mechanics.geometry.operation, resultant=True)
    patch_results: dict[str, bool] = {}
    all_actual_work = True
    combined_recovery = {
        "compatible_all_exact": True,
        "independent_all_exact": True,
        "physical_resultants_all_exact": True,
        "numerical_separate": True,
        "station_count": 4,
    }
    for patch in ("membrane", "bending", "shear", "combined"):
        q24 = mechanics.patch_vectors[patch]
        q24_base = base.patch_vectors[patch]
        p20 = _physical20(q24)
        p20_base = _physical20(q24_base)
        expected = _expected_patch_strain(field, patch)
        expected_resultants = matvec(constitutive, expected)
        internal = _stationary_internal(mechanics, q24)
        internal_base = _stationary_internal(base, q24_base)
        stress_parameters = internal[:14]
        strain_parameters = internal[14:35]
        stress_parameters_base = internal_base[:14]
        strain_parameters_base = internal_base[14:35]
        patch_pass = True
        for station in range(4):
            base_station = _corresponding_base_station(base, mechanics, station)
            compatible = matvec(mechanics.compatible_b[station], p20)
            independent = matvec(mechanics.n_epsilon[station], strain_parameters)
            resultants = matvec(mechanics.n_sigma[station], stress_parameters)
            compatible_base = matvec(base.compatible_b[base_station], p20_base)
            independent_base = matvec(base.n_epsilon[base_station], strain_parameters_base)
            resultants_base = matvec(base.n_sigma[base_station], stress_parameters_base)
            compatible_mapped = matvec(strain_transport, compatible)
            independent_mapped = matvec(strain_transport, independent)
            resultants_mapped = matvec(resultant_transport, resultants)
            prescribed_ok = (
                all_zero_vector([a - b for a, b in zip(compatible_base, expected, strict=True)])
                and all_zero_vector([a - b for a, b in zip(independent_base, expected, strict=True)])
                and all_zero_vector([a - b for a, b in zip(resultants_base, expected_resultants, strict=True)])
            )
            compatible_ok = prescribed_ok and all_zero_vector(
                [a - b for a, b in zip(compatible_mapped, compatible_base, strict=True)]
            )
            independent_ok = prescribed_ok and all_zero_vector(
                [a - b for a, b in zip(independent_mapped, independent_base, strict=True)]
            )
            resultants_ok = prescribed_ok and all_zero_vector(
                [a - b for a, b in zip(resultants_mapped, resultants_base, strict=True)]
            )
            actual_work = (
                dot(resultants, independent) - dot(resultants_base, independent_base)
            ).is_zero()
            all_actual_work = all_actual_work and actual_work
            patch_pass = patch_pass and compatible_ok and independent_ok and resultants_ok
            if patch == "combined":
                combined_recovery["compatible_all_exact"] = bool(combined_recovery["compatible_all_exact"]) and compatible_ok
                combined_recovery["independent_all_exact"] = bool(combined_recovery["independent_all_exact"]) and independent_ok
                combined_recovery["physical_resultants_all_exact"] = bool(combined_recovery["physical_resultants_all_exact"]) and resultants_ok
        # Centre-linear PL constraint and residual mode are diagnostics.  The
        # registered physical patches have their continuum spin and therefore
        # introduce no numerical contamination of N/M/Q.
        if patch in {"membrane", "bending", "shear", "combined"}:
            c_action = matvec(mechanics.c_taylor, q24)
            gamma_action = dot(
                mechanics.residual_gamma,
                [q24[6 * node + 5] for node in range(4)],
            )
            patch_pass = patch_pass and all_zero_vector(c_action) and gamma_action.is_zero()
        patch_results[patch] = patch_pass
    rigid_pass = all_zero_matrix(matmul(mechanics.k24, mechanics.rigid))
    patch_results["six_rigid_all_exact"] = rigid_pass
    # Structural separation: core columns never address drill coordinates;
    # numerical blocks do not enter the stress/strain recovery operators.
    drill_columns_zero = all(
        mechanics.q38[6 * node + 5][parameter].is_zero()
        for node in range(4)
        for parameter in range(35)
    )
    combined_recovery["numerical_separate"] = drill_columns_zero
    return patch_results, combined_recovery, all_actual_work


def _field_maps_exact(base: Geometry, current: Geometry) -> tuple[bool, bool]:
    field = current.field
    a = current.operation.natural_map
    delta = current.operation.determinant
    a_matrix = [[field.exact(a[i][j]) for j in range(2)] for i in range(2)]
    # Explicit engineering/resultant maps are work conjugate.  Checking their
    # product is the identity certifies all membrane and bending work maps.
    aa, ab = a_matrix[0]
    ac, ad = a_matrix[1]
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
    work = matrix_equal(matmul(transpose(c_res), c_eng), identity(field, 3))
    shear = scalar_matrix(field.exact(delta), a_matrix)
    work = work and matrix_equal(matmul(transpose(shear), shear), identity(field, 2))
    s_map = [
        [field.exact(1), field.exact(0), field.exact(0)],
        [field.exact(0), aa, ab],
        [field.exact(0), ac, ad],
    ]
    pl = matrix_equal(matmul(transpose(s_map), s_map), identity(field, 3))
    return work, pl


def _gauss_correspondence(base: LocalMechanics, current: LocalMechanics) -> bool:
    field = current.geometry.field
    a = current.geometry.operation.natural_map
    base_set = {(r.expression, s.expression) for r, s in base.gauss}
    for r, s in current.gauss:
        mapped_r = field.exact(a[0][0]) * r + field.exact(a[0][1]) * s
        mapped_s = field.exact(a[1][0]) * r + field.exact(a[1][1]) * s
        if (mapped_r.expression, mapped_s.expression) not in base_set:
            # DAG spelling can differ even when the field value is exact; use
            # only domain equality with a group-field zero as authority.
            found = any(
                mapped_r.is_equal(field.exact(br.expression)) and mapped_s.is_equal(field.exact(bs.expression))
                for br, bs in base.gauss
            )
            if not found:
                return False
    return True


def _load_vector(field: FieldContext, cases: Mapping[str, Any]) -> Vector:
    return [
        field.exact(expr_q(_parse_q(value)))
        for node in cases["physical_load"]["p_f_node_major"]
        for value in node
    ]


def _local_load_transform(field: FieldContext, operation: Operation) -> Matrix:
    ahat_t = transpose(_ahat(field, operation))
    a = operation.natural_map
    a_t = [[field.exact(a[j][i]) for j in range(2)] for i in range(2)]
    l5 = zeros(field, 5, 5)
    for i in range(3):
        for j in range(3):
            l5[i][j] = ahat_t[i][j]
    for i in range(2):
        for j in range(2):
            l5[3 + i][3 + j] = a_t[i][j]
    permutation = _permutation(field, operation, 5)
    block = zeros(field, 20, 20)
    for node in range(4):
        for i in range(5):
            for j in range(5):
                block[5 * node + i][5 * node + j] = l5[i][j]
    return matmul(permutation, block)


def _bind_registered_load_and_supports(
    base: LocalMechanics,
    group: Sequence[LocalMechanics],
    cases: Mapping[str, Any],
) -> None:
    """Construct load/support once at E and transport only by node permutation."""
    t5_base, _ = _t5_qd(base.geometry.frame)
    base.registered_load_global = matvec(t5_base, _load_vector(base.geometry.field, cases))
    base.registered_support_global = transpose(t5_base)
    for mechanics in group:
        permutation = _permutation(mechanics.geometry.field, mechanics.geometry.operation, 6)
        mechanics.registered_load_global = matvec(permutation, base.registered_load_global)
        mechanics.registered_support_global = matmul(base.registered_support_global, transpose(permutation))


def _kkt_solve(k: Matrix, support: Matrix, load: Vector) -> tuple[Vector, Vector] | None:
    field = k[0][0].field
    n, m = len(k), len(support)
    system = zeros(field, n + m, n + m)
    support_t = transpose(support)
    for i in range(n):
        for j in range(n):
            system[i][j] = k[i][j]
        for j in range(m):
            system[i][n + j] = support_t[i][j]
    for i in range(m):
        for j in range(n):
            system[n + i][j] = support[i][j]
    if matrix_rank(system) != n + m:
        return None
    solution = matvec(inverse(system), load + [field.exact(0) for _ in range(m)])
    return solution[:n], solution[n:]


def _case_global_support(
    base_mechanics: LocalMechanics,
    mechanics: LocalMechanics,
    cases: Mapping[str, Any],
) -> dict[str, bool]:
    base, current = base_mechanics.geometry, mechanics.geometry
    field = current.field
    if mechanics.registered_load_global is None or mechanics.registered_support_global is None:
        raise OracleError("registered E-source load/support vectors were not bound")
    p24 = _permutation(field, current.operation, 6)
    base_global_k = _global_matrix(base_mechanics.k24, base.frame)
    current_global_k = _global_matrix(mechanics.k24, current.frame)
    covariance = matrix_equal(matmul(matmul(transpose(p24), current_global_k), p24), base_global_k)
    t5_base, qd_base = _t5_qd(base.frame)
    t5_current, qd_current = _t5_qd(current.frame)
    pi5_base = matmul(t5_base, transpose(t5_base))
    pid_base = matmul(qd_base, transpose(qd_base))
    pi5_current = matmul(t5_current, transpose(t5_current))
    pid_current = matmul(qd_current, transpose(qd_current))
    projectors = (
        matrix_equal(matrix_add(pi5_current, pid_current), identity(field, 24))
        and matrix_equal(matmul(matmul(transpose(p24), pi5_current), p24), pi5_base)
        and matrix_equal(matmul(matmul(transpose(p24), pid_current), p24), pid_base)
    )
    if base_mechanics.registered_load_global is None or base_mechanics.registered_support_global is None:
        raise OracleError("base E-source load/support vectors were not bound")
    f_base = base_mechanics.registered_load_global
    f_current = mechanics.registered_load_global
    support_base = base_mechanics.registered_support_global
    support_current = mechanics.registered_support_global
    load = all_zero_vector([a - b for a, b in zip(f_current, matvec(p24, f_base), strict=True)])
    support_transport = matrix_equal(support_current, matmul(support_base, transpose(p24)))
    drill_orthogonal = all_zero_vector(matvec(transpose(qd_current), f_current))
    physical_support = all_zero_matrix(matmul(support_current, qd_current))
    solved = _kkt_solve(current_global_k, support_current, f_current)
    if solved is None:
        return {
            "projectors_exact": projectors,
            "load_exact": load and drill_orthogonal,
            "support_exact": False,
            "solution_exact": False,
            "reaction_exact": False,
            "recovery_exact": False,
            "numerical_separate": False,
        }
    q_global, multipliers = solved
    reaction_global = matvec(transpose(support_current), multipliers)
    equilibrium = all_zero_vector(
        [a + b - c for a, b, c in zip(matvec(current_global_k, q_global), reaction_global, f_current, strict=True)]
    )
    prescribed = all_zero_vector(matvec(support_current, q_global))
    reaction_physical = all_zero_vector(matvec(transpose(qd_current), reaction_global))
    local_q = matvec(transpose(_block_frame(current.frame)), q_global)
    core_local = matvec(mechanics.core_k24, local_q)
    pl_local = matvec(mechanics.pl_k24, local_q)
    hg_local = matvec(mechanics.hourglass_k24, local_q)
    separated_tangent_action = all_zero_vector(
        [a + b + c - d for a, b, c, d in zip(core_local, pl_local, hg_local, matvec(mechanics.k24, local_q), strict=True)]
    )
    internal = _stationary_internal(mechanics, local_q)
    physical_recovery = all_zero_vector(internal[:35]) and all_zero_vector(local_q)
    numerical_separate = (
        separated_tangent_action
        and all_zero_vector(pl_local)
        and all_zero_vector(hg_local)
        and all_zero_vector(internal[35:38])
    )
    return {
        "projectors_exact": projectors,
        "load_exact": load and drill_orthogonal,
        "support_exact": support_transport and physical_support,
        "solution_exact": equilibrium and prescribed,
        "reaction_exact": equilibrium and reaction_physical,
        "recovery_exact": covariance and physical_recovery,
        "numerical_separate": numerical_separate,
    }


def _case_certificate(
    base: LocalMechanics,
    mechanics: LocalMechanics,
    material: Mapping[str, Any],
    cases: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    geometry = mechanics.geometry
    field = geometry.field
    operation = geometry.operation
    case_id = f"{geometry.geometry_id}::{operation.operation_id}"
    station_ids = [f"{case_id}::{label}" for label in GAUSS_LABELS]
    centre_sign, _ = exact_sign(geometry.coefficients["jc"])
    gamma = mechanics.residual_gamma
    ones = [field.exact(1)] * 4
    h4 = [field.exact(v) for v in (1, -1, 1, -1)]
    residual_mode_exact = dot(gamma, ones).is_zero() and dot(gamma, h4).is_equal(1)
    centre = {
        "centre_j_positive": centre_sign == "POSITIVE",
        "centre_taylor_exact": shape(mechanics.c_taylor) == (3, 24),
        "residual_mode_exact": residual_mode_exact,
    }
    t5, qd = _t5_qd(geometry.frame)
    projector_exact = (
        matrix_equal(matmul(transpose(t5), t5), identity(field, 20))
        and matrix_equal(matmul(transpose(qd), qd), identity(field, 4))
        and all_zero_matrix(matmul(transpose(t5), qd))
        and matrix_equal(
            matrix_add(matmul(t5, transpose(t5)), matmul(qd, transpose(qd))),
            identity(field, 24),
        )
    )
    frame = {
        "equation7_exact": geometry.frame_exact and _frame_identity(base.geometry, geometry),
        "projectors_exact": projector_exact,
    }
    work_exact, pl_map_exact = _field_maps_exact(base.geometry, geometry)
    p24 = _permutation(field, operation, 6)
    base_core = _global_matrix(base.core_k24, base.geometry.frame)
    current_core = _global_matrix(mechanics.core_k24, geometry.frame)
    core_covariance = matrix_equal(matmul(matmul(transpose(p24), current_core), p24), base_core)
    base_pl = _global_matrix(base.pl_k24, base.geometry.frame)
    current_pl = _global_matrix(mechanics.pl_k24, geometry.frame)
    pl_covariance = matrix_equal(matmul(matmul(transpose(p24), current_pl), p24), base_pl)
    base_hg = _global_matrix(base.hourglass_k24, base.geometry.frame)
    current_hg = _global_matrix(mechanics.hourglass_k24, geometry.frame)
    residual_covariance = matrix_equal(matmul(matmul(transpose(p24), current_hg), p24), base_hg)
    support = _case_global_support(base, mechanics, cases)
    field_work = {
        "fields_exact": core_covariance,
        "pseudo_fields_exact": residual_covariance,
        "pl_exact": pl_map_exact and pl_covariance,
        "work_exact": work_exact,
        "gauss_correspondence_exact": _gauss_correspondence(base, mechanics),
    }
    symmetric = matrix_equal(mechanics.k24, transpose(mechanics.k24))
    rigid_exact = all_zero_matrix(matmul(mechanics.k24, mechanics.rigid))
    positive_count = sum(sign == "POSITIVE" for sign in mechanics.ldl_signs)
    unresolved = any(sign == "UNRESOLVED" for sign in mechanics.ldl_signs) or mechanics.ordered_unresolved
    pivot_exact_contradiction = any(sign in {"ZERO", "NEGATIVE"} for sign in mechanics.ldl_signs)
    psd = positive_count == 18 and not unresolved
    rank_18 = psd and rigid_exact
    local = {
        "field_count": 38,
        "internal_invertible": mechanics.internal_invertible,
        "rank_18": rank_18,
        "six_rigid_exact": rigid_exact,
        "symmetric": symmetric,
        "psd": psd,
        "mixed_condensed_exact": mechanics.mixed_condensed_exact,
        "unresolved": unresolved,
    }
    patches, recovery, actual_work = _patch_and_recovery(base, mechanics, material)
    field_work["work_exact"] = field_work["work_exact"] and actual_work
    exact_local_contradiction = (
        not mechanics.internal_invertible
        or not rigid_exact
        or not symmetric
        or pivot_exact_contradiction
        or mechanics.exact_local_contradiction
    )
    patch_pass = (
        all(centre.values())
        and all(frame.values())
        and all(field_work.values())
        and all(patches.values())
        and all(recovery.values())
        and all(support.values())
    )
    if exact_local_contradiction:
        status = "NO_GO"
    elif not patch_pass:
        status = "NO_GO"
    elif unresolved:
        status = "UNCLASSIFIED"
    else:
        status = "PASS"
    row = {
        "case_id": case_id,
        "geometry_id": geometry.geometry_id,
        "operation_id": operation.operation_id,
        "gauss_station_ids": station_ids,
        "centre": centre,
        "frame": frame,
        "field_work": field_work,
        "local_algebra": local,
        "patches": patches,
        "recovery": recovery,
        "global_support": support,
        "status": status,
    }
    if set(row) != CASE_KEYS:
        raise OracleError("case certificate schema mismatch")
    diagnostics = {
        "case_id": case_id,
        "field_degree": field.degree,
        "exact_local_contradiction": exact_local_contradiction,
        "ldl_signs": mechanics.ldl_signs,
        "numerical_modes": mechanics.numerical_modes,
        "patch_contradiction": not patch_pass,
        "pivot_dag_sha256": [expression_digest(value.expression) for value in mechanics.ldl_pivots],
    }
    return row, diagnostics


def _failure_certificate(failure: MechanicsFailure) -> tuple[dict[str, Any], dict[str, Any]]:
    geometry = failure.geometry
    case_id = f"{geometry.geometry_id}::{geometry.operation.operation_id}"
    unresolved = failure.unresolved
    local_failure = failure.category == "LOCAL"
    patch_failure = failure.category == "PATCH"
    false_local = {
        "field_count": 38,
        "internal_invertible": False,
        "rank_18": False,
        "six_rigid_exact": False,
        "symmetric": False,
        "psd": False,
        "mixed_condensed_exact": False,
        "unresolved": unresolved,
    }
    row = {
        "case_id": case_id,
        "geometry_id": geometry.geometry_id,
        "operation_id": geometry.operation.operation_id,
        "gauss_station_ids": [f"{case_id}::{label}" for label in GAUSS_LABELS],
        "centre": {"centre_j_positive": False, "centre_taylor_exact": False, "residual_mode_exact": False},
        "frame": {"equation7_exact": geometry.frame_exact, "projectors_exact": False},
        "field_work": {
            "fields_exact": False,
            "pseudo_fields_exact": False,
            "pl_exact": False,
            "work_exact": False,
            "gauss_correspondence_exact": False,
        },
        "local_algebra": false_local,
        "patches": {"membrane": False, "bending": False, "shear": False, "combined": False, "six_rigid_all_exact": False},
        "recovery": {
            "compatible_all_exact": False,
            "independent_all_exact": False,
            "physical_resultants_all_exact": False,
            "numerical_separate": False,
            "station_count": 4,
        },
        "global_support": {
            "projectors_exact": False,
            "load_exact": False,
            "support_exact": False,
            "solution_exact": False,
            "reaction_exact": False,
            "recovery_exact": False,
            "numerical_separate": False,
        },
        "status": "UNCLASSIFIED" if unresolved and not (local_failure or patch_failure) else "NO_GO",
    }
    diagnostics = {
        "case_id": case_id,
        "failure_category": failure.category,
        "failure_reason": failure.reason,
        "exact_local_contradiction": local_failure,
        "patch_contradiction": patch_failure,
        "numerical_modes": {
            "common_drill_energetic": False,
            "translation_only_spin_energetic": False,
            "matched_rigid_combination_null": False,
            "alternating_retained_pl_null": False,
            "alternating_hourglass_energetic": False,
        },
    }
    return row, diagnostics


def _convert_matrix(field: FieldContext, matrix: Matrix) -> Matrix:
    return [[field.exact(value.expression) for value in row] for row in matrix]


def _global_transform_certificate(
    mechanics_by_key: Mapping[tuple[str, str], LocalMechanics],
    cases: Mapping[str, Any],
) -> dict[str, bool]:
    del cases
    required = [
        (geometry, operation)
        for geometry in ("Q3_TAPERED_SKEW", "Q3_TAPERED_SKEW_RSTAR_TRANSLATED")
        for operation in OPERATION_IDS
    ]
    if any(key not in mechanics_by_key for key in required):
        return {
            "all_global_field_recovery_exact": False,
            "all_global_loads_exact": False,
            "all_global_projectors_exact": False,
            "all_global_reactions_exact": False,
            "all_global_support_solutions_exact": False,
            "all_global_supports_exact": False,
            "all_numerical_reactions_separate": False,
            "all_translation_invariant": False,
            "direct_drill_excluded": True,
            "physical_supports_only": True,
        }
    geometry_contract = _load_frozen_json("e4_pl_q1r_geometry_contract.json")
    transform = geometry_contract["global_transform"]
    all_frame = all_stiffness = all_projectors = True
    all_loads = all_supports = all_solutions = all_reactions = True
    all_recovery = all_numerical = all_translation = True
    for operation_id in OPERATION_IDS:
        source = mechanics_by_key[("Q3_TAPERED_SKEW", operation_id)]
        transformed = mechanics_by_key[("Q3_TAPERED_SKEW_RSTAR_TRANSLATED", operation_id)]
        field = transformed.geometry.field
        rotation = [[field.exact(expr_q(_parse_q(value))) for value in row] for row in transform["R_star"]]
        source_frame = _convert_matrix(field, source.geometry.frame)
        expected_frame = matmul(rotation, source_frame)
        all_frame = all_frame and matrix_equal(transformed.geometry.frame, expected_frame)
        all_stiffness = all_stiffness and _cross_field_matrix_equal(field, transformed.k24, source.k24)
        source_global = _convert_matrix(field, _global_matrix(source.k24, source.geometry.frame))
        transformed_global = _global_matrix(transformed.k24, transformed.geometry.frame)
        global_rotation = zeros(field, 24, 24)
        for node in range(4):
            for block in range(2):
                for i in range(3):
                    for j in range(3):
                        global_rotation[6 * node + 3 * block + i][6 * node + 3 * block + j] = rotation[i][j]
        all_stiffness = all_stiffness and matrix_equal(
            transformed_global,
            matmul(matmul(global_rotation, source_global), transpose(global_rotation)),
        )
        t5_source, qd_source = _t5_qd(source_frame)
        t5_star, qd_star = _t5_qd(transformed.geometry.frame)
        all_projectors = all_projectors and (
            matrix_equal(t5_star, matmul(global_rotation, t5_source))
            and matrix_equal(qd_star, matmul(global_rotation, qd_source))
        )
        all_translation = all_translation and all(
            transformed.geometry.local_nodes[i][j].is_equal(field.exact(source.geometry.local_nodes[i][j].expression))
            for i in range(4)
            for j in range(2)
        )
        if (
            source.registered_load_global is None
            or source.registered_support_global is None
            or transformed.registered_load_global is None
            or transformed.registered_support_global is None
        ):
            all_loads = all_supports = all_solutions = all_reactions = all_numerical = False
            continue
        source_load = [field.exact(value.expression) for value in source.registered_load_global]
        source_support = _convert_matrix(field, source.registered_support_global)
        all_loads = all_loads and all_zero_vector(
            [a - b for a, b in zip(transformed.registered_load_global, matvec(global_rotation, source_load), strict=True)]
        )
        all_supports = all_supports and matrix_equal(
            transformed.registered_support_global,
            matmul(source_support, transpose(global_rotation)),
        )
        source_solution = _kkt_solve(source_global, source_support, source_load)
        transformed_solution = _kkt_solve(
            transformed_global,
            transformed.registered_support_global,
            transformed.registered_load_global,
        )
        if source_solution is None or transformed_solution is None:
            all_solutions = all_reactions = all_numerical = False
            continue
        source_q, source_mu = source_solution
        transformed_q, transformed_mu = transformed_solution
        all_solutions = all_solutions and all_zero_vector(
            [a - b for a, b in zip(transformed_q, matvec(global_rotation, source_q), strict=True)]
        ) and all_zero_vector([a - b for a, b in zip(transformed_mu, source_mu, strict=True)])
        source_reaction = matvec(transpose(source_support), source_mu)
        transformed_reaction = matvec(transpose(transformed.registered_support_global), transformed_mu)
        all_reactions = all_reactions and all_zero_vector(
            [a - b for a, b in zip(transformed_reaction, matvec(global_rotation, source_reaction), strict=True)]
        )
        local_source_q = matvec(transpose(_block_frame(source_frame)), source_q)
        local_transformed_q = matvec(transpose(_block_frame(transformed.geometry.frame)), transformed_q)
        all_numerical = all_numerical and all_zero_vector(
            [a - b for a, b in zip(local_transformed_q, local_source_q, strict=True)]
        ) and all_zero_vector(matvec(transformed.pl_k24, local_transformed_q)) and all_zero_vector(
            matvec(transformed.hourglass_k24, local_transformed_q)
        )
        source_internal = _stationary_internal(source, source.patch_vectors["combined"])
        transformed_internal = _stationary_internal(transformed, transformed.patch_vectors["combined"])
        for station in range(4):
            source_compatible = matvec(source.compatible_b[station], _physical20(source.patch_vectors["combined"]))
            transformed_compatible = matvec(
                transformed.compatible_b[station], _physical20(transformed.patch_vectors["combined"])
            )
            source_independent = matvec(source.n_epsilon[station], source_internal[14:35])
            transformed_independent = matvec(transformed.n_epsilon[station], transformed_internal[14:35])
            source_resultants = matvec(source.n_sigma[station], source_internal[:14])
            transformed_resultants = matvec(transformed.n_sigma[station], transformed_internal[:14])
            all_recovery = all_recovery and all_zero_vector(
                [a - field.exact(b.expression) for a, b in zip(transformed_compatible, source_compatible, strict=True)]
            ) and all_zero_vector(
                [a - field.exact(b.expression) for a, b in zip(transformed_independent, source_independent, strict=True)]
            ) and all_zero_vector(
                [a - field.exact(b.expression) for a, b in zip(transformed_resultants, source_resultants, strict=True)]
            )
    common = all_frame and all_stiffness and all_translation
    return {
        "all_global_field_recovery_exact": common and all_recovery,
        "all_global_loads_exact": all_loads,
        "all_global_projectors_exact": all_projectors,
        "all_global_reactions_exact": all_reactions,
        "all_global_support_solutions_exact": all_solutions,
        "all_global_supports_exact": all_supports,
        "all_numerical_reactions_separate": all_numerical,
        "all_translation_invariant": all_translation,
        "direct_drill_excluded": True,
        "physical_supports_only": True,
    }


def _line_digest(ordered_ids: Sequence[str]) -> str:
    return sha256(("\n".join(ordered_ids) + "\n").encode("utf-8"))


def _classification(
    rows: Sequence[Mapping[str, Any]],
    diagnostics: Sequence[Mapping[str, Any]],
    global_supports: Mapping[str, bool],
) -> dict[str, Any]:
    unresolved = any(row["status"] == "UNCLASSIFIED" for row in rows)
    local_failure = any(bool(row.get("exact_local_contradiction")) for row in diagnostics)
    patch_failure = any(bool(row.get("patch_contradiction")) for row in diagnostics) or not all(global_supports.values())
    if local_failure:
        terminal = LOCAL_NO_GO
    elif patch_failure:
        terminal = PATCH_NO_GO
    elif unresolved:
        terminal = UNCLASSIFIED_TERMINAL
    else:
        terminal = SUCCESS_TERMINAL
    return {
        "inconclusive": terminal == UNCLASSIFIED_TERMINAL,
        "production": PRODUCTION,
        "q1b_execution": "UNAUTHORIZED",
        "terminal": terminal,
    }


def _common_payload(sympy: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    geometry_specs, operations, material, cases = _frozen_inputs()
    field_cache: dict[str, tuple[FieldContext, tuple[Expr, ...]]] = {}
    mechanics_by_key: dict[tuple[str, str], LocalMechanics] = {}
    rows: list[dict[str, Any]] = []
    diagnostic_rows: list[dict[str, Any]] = []
    for geometry_id, node_text in geometry_specs:
        base_geometry = _numbered_geometry(geometry_id, node_text, operations[0], sympy, field_cache)
        base_result = _assemble_local(base_geometry, material)
        if isinstance(base_result, MechanicsFailure):
            for operation in operations:
                geometry = (
                    base_geometry
                    if operation.operation_id == "E"
                    else _numbered_geometry(geometry_id, node_text, operation, sympy, field_cache)
                )
                failure = MechanicsFailure(
                    geometry,
                    base_result.category,
                    f"BASE_E_{base_result.reason}",
                    base_result.unresolved,
                )
                row, diagnostic = _failure_certificate(failure)
                rows.append(row)
                diagnostic_rows.append(diagnostic)
            continue
        base = base_result
        group: list[LocalMechanics] = [base]
        results: list[LocalMechanics | MechanicsFailure] = [base]
        mechanics_by_key[(geometry_id, "E")] = base
        for operation in operations[1:]:
            geometry = _numbered_geometry(geometry_id, node_text, operation, sympy, field_cache)
            result = _assemble_local(geometry, material, base)
            results.append(result)
            if isinstance(result, LocalMechanics):
                group.append(result)
                mechanics_by_key[(geometry_id, operation.operation_id)] = result
        _bind_registered_load_and_supports(base, group, cases)
        for result in results:
            if isinstance(result, MechanicsFailure):
                row, diagnostic = _failure_certificate(result)
            else:
                row, diagnostic = _case_certificate(base, result, material, cases)
            rows.append(row)
            diagnostic_rows.append(diagnostic)
    if len(rows) != 56:
        raise OracleError("registered case coverage is not 56")
    ordered_case_ids = [row["case_id"] for row in rows]
    ordered_station_ids = [station for row in rows for station in row["gauss_station_ids"]]
    if len(ordered_station_ids) != 224:
        raise OracleError("registered station coverage is not 224")
    global_supports = _global_transform_certificate(mechanics_by_key, cases)
    frame_and_fields = {
        "all_d4_field_maps_exact": all(row["field_work"]["fields_exact"] for row in rows),
        "all_d4_frame_identities_exact": all(row["frame"]["equation7_exact"] for row in rows),
        "all_d4_pl_maps_exact": all(row["field_work"]["pl_exact"] for row in rows),
        "all_d4_work_equalities_exact": all(row["field_work"]["work_exact"] for row in rows),
        "all_gauss_correspondence_exact": all(row["field_work"]["gauss_correspondence_exact"] for row in rows),
        "all_numbered_loads_exact": all(row["global_support"]["load_exact"] for row in rows),
        "all_numbered_projectors_exact": all(row["global_support"]["projectors_exact"] for row in rows),
        "all_numbered_residual_modes_exact": all(row["centre"]["residual_mode_exact"] and row["field_work"]["pseudo_fields_exact"] for row in rows),
    }
    local_algebra = {
        "all_38_field_blocks_invertible": all(row["local_algebra"]["internal_invertible"] for row in rows),
        "all_condensed_rank_18": all(row["local_algebra"]["rank_18"] for row in rows),
        "all_mixed_condensed_equalities_exact": all(row["local_algebra"]["mixed_condensed_exact"] for row in rows),
        "all_psd": all(row["local_algebra"]["psd"] for row in rows),
        "all_six_rigid_actions_exact_zero": all(row["local_algebra"]["six_rigid_exact"] for row in rows),
        "all_symmetric": all(row["local_algebra"]["symmetric"] for row in rows),
        "quotient_rule": "LEXICOGRAPHIC_EXACT_RREF_NULLSPACE_OF_R_TRANSPOSE",
        "unresolved_at_1024": any(row["local_algebra"]["unresolved"] for row in rows),
    }
    recovery = {
        "all_224_compatible_fields": all(row["recovery"]["compatible_all_exact"] for row in rows),
        "all_224_independent_fields": all(row["recovery"]["independent_all_exact"] for row in rows),
        "all_224_physical_resultants": all(row["recovery"]["physical_resultants_all_exact"] for row in rows),
        "all_numerical_fields_separate": all(row["recovery"]["numerical_separate"] for row in rows),
        "physical_resultants": ["N", "M", "Q"],
        "numerical_fields_excluded": [
            "PL_CONSTRAINT",
            "PL_MULTIPLIER",
            "PL_COMPLIANCE_ENERGY",
            "RESIDUAL_MODE_COORDINATE",
            "RESIDUAL_MODE_ENERGY",
            "RESIDUAL_MODE_RESIDUAL",
            "RESIDUAL_MODE_TANGENT",
        ],
    }
    payload = {
        "schema": PAYLOAD_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "study_id": STUDY_ID,
        "precision_bits": list(PRECISION_BITS),
        "coverage": {
            "base_geometries": 6,
            "centre_records": 56,
            "d4_operations": 8,
            "gauss_records": 224,
            "global_transform_variants": 1,
            "numbered_cases": 56,
            "ordered_case_ids_sha256": _line_digest(ordered_case_ids),
            "ordered_station_ids_sha256": _line_digest(ordered_station_ids),
        },
        "frame_and_fields": frame_and_fields,
        "local_algebra": local_algebra,
        "recovery": recovery,
        "global_supports": global_supports,
        "classification": _classification(rows, diagnostic_rows, global_supports),
        "case_certificates": rows,
    }
    if set(payload) != TOP_LEVEL_KEYS:
        raise OracleError("common payload schema mismatch")
    diagnostics = {
        "backend": "SYMPY_QQ_ALGEBRAIC_FIELD",
        "case_diagnostics": diagnostic_rows,
        "equality_authority": "DOMAIN_ELEMENT_EQUALITY_WITH_FIELD_ZERO",
        "expression_dag": "INDEPENDENT_RATIONAL_POSITIVE_ROOT_DAG",
        "field_degrees": [field_cache[geometry_id][0].degree for geometry_id in GEOMETRY_IDS],
        "global_transform_and_supports": global_supports,
        "ordered_sign_engine": "STDLIB_OUTWARD_DYADIC_256_512_1024",
    }
    return payload, diagnostics


# ---------------------------------------------------------------------------
# Eight-input fail-closed execution guard


@dataclass(frozen=True, slots=True)
class ExecuteInputs:
    authority_record: Path
    authority_sha256: str
    contract: Path
    contract_sha256: str
    environment_root: Path
    environment_sha256: str
    runner_id: str
    output: Path


@dataclass(frozen=True, slots=True)
class GuardEvidence:
    authority_sha256: str
    contract_sha256: str
    environment_sha256: str


def _git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise OracleError(f"git guard command failed: {' '.join(arguments)}")
    return completed.stdout.strip()


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _worktree_roots() -> list[Path]:
    lines = _git("worktree", "list", "--porcelain").splitlines()
    return [Path(line[9:]).resolve() for line in lines if line.startswith("worktree ")]


def _validate_external(path: Path, *, existing_file: bool) -> Path:
    resolved = path.resolve(strict=existing_file)
    if any(_inside(resolved, root) for root in _worktree_roots()):
        raise OracleError(f"external caller artifact is inside a git worktree: {path}")
    return resolved


def _validate_environment(root: Path, claimed_sha: str) -> str:
    record_raw, record = _read_canonical(REFERENCE_DIR / "e4_pl_q1t_environment.json")
    actual_record_sha = sha256(record_raw)
    if actual_record_sha != ENVIRONMENT_SHA256.upper() or claimed_sha.upper() != actual_record_sha:
        raise OracleError("exact environment record hash mismatch")
    resolved = _validate_external(root, existing_file=False)
    if not resolved.is_dir() or resolved.is_symlink():
        raise OracleError("environment root must be a regular external directory")
    for row in record["extracted_file_hash_graph"]:
        relative = Path(row["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise OracleError("unsafe environment graph member")
        path = resolved / relative
        if not _regular_nonsymlink(path):
            raise OracleError(f"environment member missing or symlinked: {relative.as_posix()}")
        raw = path.read_bytes()
        if len(raw) != row["bytes"] or sha256(raw) != row["sha256"].upper():
            raise OracleError(f"environment member identity mismatch: {relative.as_posix()}")
    return actual_record_sha


def _review(path: Path, schema: str, verdict: str) -> tuple[bytes, Mapping[str, Any]]:
    raw, value = _read_canonical(path)
    if set(value) != {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"}:
        raise OracleError(f"review exact-key mismatch: {path.name}")
    if value["schema"] != schema or value["verdict"] != verdict or value["findings"] != []:
        raise OracleError(f"review verdict/schema mismatch: {path.name}")
    return raw, value


def _validate_inheritance_metadata() -> None:
    _, manifest = _read_canonical(REFERENCE_DIR / "e4_pl_q1t_inheritance_manifest.json")
    rows = (
        manifest["q1r_e4_inherited_inputs"]
        + manifest["q1s_commit1_inputs"]
        + manifest["q1s_closeout_inputs"]
    )
    if len(rows) != 49:
        raise OracleError("inheritance row count mismatch")
    for row in rows:
        # For prohibited predecessor implementations the guard verifies only
        # immutable Git metadata and file size.  It neither imports nor reads
        # their algebra or interval code.
        blob = _git("rev-parse", f"{row['source_commit']}:{row['path']}")
        if blob != row["git_blob"]:
            raise OracleError(f"inherited git blob mismatch: {row['path']}")
        current = ROOT / row["path"]
        if not _regular_nonsymlink(current) or current.stat().st_size != row["bytes"]:
            raise OracleError(f"inherited current path mismatch: {row['path']}")
        raw = current.read_bytes()
        if sha256(raw) != str(row["sha256"]).upper():
            raise OracleError(f"inherited current SHA-256 mismatch: {row['path']}")
        current_blob = _git("hash-object", "--", row["path"])
        if current_blob != row["git_blob"]:
            raise OracleError(f"inherited current blob mismatch: {row['path']}")


def _exact_keys(value: Any, expected: set[str] | frozenset[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != set(expected):
        raise OracleError(f"{label} exact-key mismatch")
    return value


def _validate_bound_row(
    row: Any,
    exact_keys: set[str] | frozenset[str],
    label: str,
    expected_path: str | None = None,
) -> Mapping[str, Any]:
    bound = _exact_keys(row, exact_keys, label)
    relative_text = bound["path"]
    if not isinstance(relative_text, str) or (expected_path is not None and relative_text != expected_path):
        raise OracleError(f"{label} path mismatch")
    relative = Path(relative_text)
    if relative.is_absolute() or ".." in relative.parts:
        raise OracleError(f"{label} unsafe path")
    path = ROOT / relative
    if not _regular_nonsymlink(path):
        raise OracleError(f"{label} is not a regular non-symlink file")
    raw = path.read_bytes()
    if len(raw) != bound["bytes"] or sha256(raw) != str(bound["sha256"]).upper():
        raise OracleError(f"{label} byte identity mismatch")
    return bound


def _commit_paths(commit: str) -> list[str]:
    raw = _git("diff-tree", "--no-commit-id", "--name-only", "-r", commit)
    return sorted(line.replace("\\", "/") for line in raw.splitlines() if line)


def _validate_commit_row(
    row: Any,
    *,
    label: str,
    commit: str,
    parent: str,
    subject: str,
    paths: Sequence[str],
) -> None:
    value = _exact_keys(row, {"commit", "tree", "parent", "subject", "path_count", "paths"}, label)
    tree = _git("rev-parse", f"{commit}^{{tree}}")
    expected = {
        "commit": commit,
        "tree": tree,
        "parent": parent,
        "subject": subject,
        "path_count": len(paths),
        "paths": list(paths),
    }
    if value != expected:
        raise OracleError(f"{label} ancestry record mismatch")
    if _git("rev-parse", f"{commit}^") != parent or _git("show", "-s", "--format=%s", commit) != subject:
        raise OracleError(f"{label} Git ancestry mismatch")
    if _commit_paths(commit) != sorted(paths):
        raise OracleError(f"{label} exact diff-tree extent mismatch")


def _validate_execution_contract(contract: Mapping[str, Any]) -> None:
    if set(contract) != CONTRACT_TOP_KEYS:
        raise OracleError("execution contract exact 17-key mismatch")
    if contract["schema"] != EXECUTION_CONTRACT_SCHEMA:
        raise OracleError("execution contract schema mismatch")
    if contract["candidate_id"] != CANDIDATE_ID or contract["study_id"] != STUDY_ID:
        raise OracleError("execution contract study identity mismatch")
    allowed = _load_frozen_json("e4_pl_q1t_allowed_extent.json")["path_sets"]
    plan_paths = allowed["PLAN"]
    implementation_paths = allowed["IMPLEMENTATION"]
    contract_paths = allowed["CONTRACT"]

    authorization = _exact_keys(
        contract["authorization"],
        {"token", "commit3_subject", "commit3_path_count", "commit3_paths", "external_authority_schema", "external_authority_exact_keys"},
        "contract authorization",
    )
    authority_contract = _load_frozen_json("e4_pl_q1t_authority_contract.json")
    expected_authorization = {
        "token": "AUTHORIZE_E4_PL_Q1T_SCIENTIFIC_EXECUTION",
        "commit3_subject": "docs: authorize E4 PL Q1T scientific execution",
        "commit3_path_count": 3,
        "commit3_paths": contract_paths,
        "external_authority_schema": "anysolver.s4.e4-pl-q1t-execution-authority-v1",
        "external_authority_exact_keys": authority_contract["execution_authority_record"]["canonical_exact_keys"],
    }
    if authorization != expected_authorization:
        raise OracleError("contract authorization value mismatch")

    ancestry = _exact_keys(contract["commit_ancestry"], {"commit1", "commit2"}, "commit ancestry")
    commit1 = _git("rev-parse", "HEAD~2")
    commit2 = _git("rev-parse", "HEAD~1")
    commit3 = _git("rev-parse", "HEAD")
    _validate_commit_row(
        ancestry["commit1"],
        label="commit1",
        commit=commit1,
        parent=BASE_COMMIT,
        subject="docs: preregister E4 PL Q1T exact-oracle completion",
        paths=plan_paths,
    )
    _validate_commit_row(
        ancestry["commit2"],
        label="commit2",
        commit=commit2,
        parent=commit1,
        subject="docs: freeze E4 PL Q1T exact reference and oracle",
        paths=implementation_paths,
    )
    if _git("rev-parse", "HEAD^") != commit2:
        raise OracleError("commit3 parent mismatch")
    if _git("show", "-s", "--format=%s", commit3) != authorization["commit3_subject"]:
        raise OracleError("commit3 subject mismatch")
    if _commit_paths(commit3) != sorted(contract_paths):
        raise OracleError("commit3 exact CONTRACT3 diff-tree extent mismatch")

    plan_inputs = _exact_keys(contract["plan_inputs"], {"count", "rows"}, "plan inputs")
    if plan_inputs["count"] != 14 or not isinstance(plan_inputs["rows"], list) or len(plan_inputs["rows"]) != 14:
        raise OracleError("plan input count mismatch")
    plan_rows = [
        _validate_bound_row(row, {"path", "bytes", "sha256"}, f"plan input {index}")
        for index, row in enumerate(plan_inputs["rows"])
    ]
    if [row["path"] for row in plan_rows] != plan_paths:
        raise OracleError("plan input path ordering mismatch")

    inherited = _exact_keys(contract["inherited_inputs"], {"count", "rows"}, "inherited inputs")
    manifest = _load_frozen_json("e4_pl_q1t_inheritance_manifest.json")
    manifest_rows = manifest["q1r_e4_inherited_inputs"] + manifest["q1s_commit1_inputs"] + manifest["q1s_closeout_inputs"]
    if inherited != {"count": 49, "rows": manifest_rows}:
        raise OracleError("contract inherited input rows mismatch")
    _validate_inheritance_metadata()

    implementation = _exact_keys(
        contract["implementation_inputs"],
        {"reference", "oracle", "scientific_runner", "manifest", "implementation_review", "exact_backend_test", "scientific_tests"},
        "implementation inputs",
    )
    reference = _validate_bound_row(
        implementation["reference"],
        {"path", "bytes", "sha256", "implementation_id"},
        "bound reference",
        "docs/reference_cases/e4_pl_q1t_reference.py",
    )
    oracle = _validate_bound_row(
        implementation["oracle"],
        {"path", "bytes", "sha256", "implementation_id"},
        "bound oracle",
        "docs/reference_cases/e4_pl_q1t_oracle.py",
    )
    if reference["implementation_id"] != "Q1T_REFERENCE_STDLIB_FIELD_ALG" or oracle["implementation_id"] != IMPLEMENTATION_ID:
        raise OracleError("implementation identity mismatch")
    runner = _validate_bound_row(
        implementation["scientific_runner"],
        {"path", "bytes", "sha256", "runner_id"},
        "bound scientific runner",
        "docs/reference_cases/e4_pl_q1t_scientific_test_runner.py",
    )
    if runner["runner_id"] != "SCIENTIFIC_TEST_RUNNER":
        raise OracleError("scientific runner identity mismatch")
    manifest_row = _validate_bound_row(
        implementation["manifest"],
        {"path", "bytes", "sha256", "schema"},
        "bound implementation manifest",
        "docs/reference_cases/e4_pl_q1t_implementation_manifest.json",
    )
    review_row = _validate_bound_row(
        implementation["implementation_review"],
        {"path", "bytes", "sha256", "schema", "verdict"},
        "bound implementation review",
        "docs/reference_cases/e4_pl_q1t_implementation_review.json",
    )
    if manifest_row["schema"] != "anysolver.s4.e4-pl-q1t-implementation-manifest-v1":
        raise OracleError("implementation manifest schema mismatch")
    if review_row["schema"] != "anysolver.s4.e4-pl-q1t-implementation-review-v1" or review_row["verdict"] != "ACCEPT_Q1T_IMPLEMENTATION_FREEZE_NO_P0_P1":
        raise OracleError("implementation review authority mismatch")
    exact_backend = _validate_bound_row(
        implementation["exact_backend_test"],
        {"path", "bytes", "sha256", "node_ids"},
        "bound exact backend test",
        "tests/test_e4_pl_q1t_exact_backend.py",
    )
    tests = contract["scientific_inventory"]
    test_inventory = _load_frozen_json("e4_pl_q1t_test_inventory.json")
    if exact_backend["node_ids"] != test_inventory["exact_backend_inventory"]["node_ids"]:
        raise OracleError("exact backend node inventory mismatch")
    scientific_rows_raw = implementation["scientific_tests"]
    if not isinstance(scientific_rows_raw, list) or len(scientific_rows_raw) != 5:
        raise OracleError("scientific test row count mismatch")
    scientific_rows = [
        _validate_bound_row(row, {"path", "bytes", "sha256", "node_ids"}, f"scientific test {index}")
        for index, row in enumerate(scientific_rows_raw)
    ]
    implementation_bound_paths = [
        reference["path"], oracle["path"], runner["path"], manifest_row["path"], review_row["path"], exact_backend["path"],
        *(row["path"] for row in scientific_rows),
    ]
    if implementation_bound_paths != implementation_paths:
        raise OracleError("implementation input path ordering mismatch")

    environment = _exact_keys(
        contract["environment"],
        {"record_path", "bytes", "sha256", "schema", "environment_id", "external_root_required", "extracted_file_count", "extracted_file_hash_graph_sha256"},
        "contract environment",
    )
    environment_raw, environment_record = _read_canonical(REFERENCE_DIR / "e4_pl_q1t_environment.json")
    expected_environment = {
        "record_path": "docs/reference_cases/e4_pl_q1t_environment.json",
        "bytes": len(environment_raw),
        "sha256": sha256(environment_raw),
        "schema": "e4_pl_q1t_environment_record_v1",
        "environment_id": "e4_pl_q1t_external_exact_environment_v1",
        "external_root_required": True,
        "extracted_file_count": 1662,
        "extracted_file_hash_graph_sha256": environment_record["extracted_file_hash_graph_sha256"].upper(),
    }
    normalized_environment = dict(environment)
    normalized_environment["sha256"] = str(normalized_environment["sha256"]).upper()
    normalized_environment["extracted_file_hash_graph_sha256"] = str(normalized_environment["extracted_file_hash_graph_sha256"]).upper()
    if normalized_environment != expected_environment:
        raise OracleError("contract environment identity mismatch")

    reviews = _exact_keys(contract["review_authorities"], {"plan", "implementation", "contract"}, "review authorities")
    plan_review = _validate_bound_row(reviews["plan"], {"path", "bytes", "sha256", "schema", "verdict"}, "plan review authority")
    implementation_review = _validate_bound_row(reviews["implementation"], {"path", "bytes", "sha256", "schema", "verdict"}, "implementation review authority")
    contract_review = _exact_keys(reviews["contract"], {"path", "schema", "verdict", "hash_binding"}, "contract review authority")
    if plan_review["path"] != "docs/reference_cases/e4_pl_q1t_plan_review.json" or plan_review["schema"] != "anysolver.s4.e4-pl-q1t-plan-review-v1" or plan_review["verdict"] != "ACCEPT_Q1T_PREREGISTRATION_NO_P0_P1":
        raise OracleError("plan review contract authority mismatch")
    if implementation_review != review_row:
        raise OracleError("implementation review duplicate binding mismatch")
    if contract_review != {
        "path": "docs/reference_cases/e4_pl_q1t_contract_review.json",
        "schema": "anysolver.s4.e4-pl-q1t-contract-review-v1",
        "verdict": "ACCEPT_Q1T_EXECUTION_CONTRACT_NO_P0_P1",
        "hash_binding": "EXTERNAL_AUTHORITY_RECORD",
    }:
        raise OracleError("contract review authority mismatch")

    runners = _exact_keys(contract["runner_inventory"], {"count", "runner_ids"}, "runner inventory")
    if runners != {"count": 3, "runner_ids": ["REFERENCE_RUNNER", "ORACLE_RUNNER", "SCIENTIFIC_TEST_RUNNER"]}:
        raise OracleError("runner inventory mismatch")
    scientific = _exact_keys(tests, {"count", "node_ids", "inventories_separate"}, "scientific inventory")
    expected_nodes = test_inventory["scientific_inventory"]["node_ids"]
    if scientific != {"count": 5, "node_ids": expected_nodes, "inventories_separate": True}:
        raise OracleError("scientific inventory mismatch")
    if [node for row in scientific_rows for node in row["node_ids"]] != expected_nodes:
        raise OracleError("scientific test row node mismatch")

    terminal = _validate_bound_row(
        contract["terminal_authority"],
        {"path", "bytes", "sha256", "schema", "evaluation", "terminal_count"},
        "terminal authority",
        "docs/reference_cases/e4_pl_q1t_terminal_table.json",
    )
    terminal_table = _load_frozen_json("e4_pl_q1t_terminal_table.json")
    if terminal["schema"] != terminal_table["schema"] or terminal["evaluation"] != terminal_table["evaluation"] or terminal["terminal_count"] != 11:
        raise OracleError("terminal authority value mismatch")
    absences = _exact_keys(contract["output_absences"], {"paths", "absent_from_commit3_tree"}, "output absences")
    if absences != {"paths": allowed["OUTCOME"], "absent_from_commit3_tree": True}:
        raise OracleError("output absence contract mismatch")

    agreement = _exact_keys(
        contract["agreement"],
        {"common_payload_schema", "cross_implementation", "within_reference_fresh_processes", "within_oracle_fresh_processes", "reference_wrapper_schema", "oracle_wrapper_schema"},
        "agreement contract",
    )
    if agreement != {
        "common_payload_schema": PAYLOAD_SCHEMA,
        "cross_implementation": "BYTE_IDENTICAL_CANONICAL_CERTIFICATE_PAYLOAD",
        "within_reference_fresh_processes": 2,
        "within_oracle_fresh_processes": 2,
        "reference_wrapper_schema": "anysolver.s4.e4-pl-q1t-reference-raw-v1",
        "oracle_wrapper_schema": WRAPPER_SCHEMA,
    }:
        raise OracleError("agreement contract mismatch")
    production = _exact_keys(
        contract["production_restriction"],
        {"legacy_default", "post_execution_source_changes", "production", "q1b_execution"},
        "production restriction",
    )
    if production != {
        "legacy_default": "ShellElement",
        "post_execution_source_changes": "FORBIDDEN_REQUIRES_NEW_SUCCESSOR",
        "production": PRODUCTION,
        "q1b_execution": "UNAUTHORIZED",
    }:
        raise OracleError("production restriction mismatch")
    runtime = _exact_keys(
        contract["runtime"],
        {"environment", "mpmath", "precision_bits", "python_implementation", "python_version", "reference_categorical_backend", "sympy_environment", "pytest_version"},
        "runtime authority",
    )
    if runtime != {
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
    }:
        raise OracleError("runtime authority mismatch")


def _validate_runtime_process(contract: Mapping[str, Any]) -> None:
    runtime = contract["runtime"]
    if sys.implementation.name != "cpython" or sys.version.split()[0] != runtime["python_version"]:
        raise OracleError("caller Python runtime mismatch")
    try:
        pytest_version = importlib.metadata.version("pytest")
    except importlib.metadata.PackageNotFoundError as exc:
        raise OracleError("pytest runtime is unavailable") from exc
    if pytest_version != runtime["pytest_version"]:
        raise OracleError("caller pytest runtime mismatch")
    for name, expected in runtime["environment"].items():
        if os.environ.get(name) != expected:
            raise OracleError(f"frozen runtime variable mismatch: {name}")


def _validate_authority_and_repository(
    authority: Mapping[str, Any],
    contract: Mapping[str, Any],
    authority_sha: str,
    contract_sha: str,
    environment_sha: str,
    runner_id: str,
) -> None:
    expected_keys = {
        "schema",
        "authorization",
        "candidate_id",
        "study_id",
        "commit",
        "tree",
        "execution_contract_sha256",
        "environment_sha256",
        "plan_review_sha256",
        "implementation_review_sha256",
        "contract_review_sha256",
        "review_verdicts",
        "runner_ids",
    }
    if set(authority) != expected_keys:
        raise OracleError("execution authority exact-key mismatch")
    if authority["schema"] != "anysolver.s4.e4-pl-q1t-execution-authority-v1":
        raise OracleError("execution authority schema mismatch")
    if authority["authorization"] != "AUTHORIZE_E4_PL_Q1T_SCIENTIFIC_EXECUTION":
        raise OracleError("execution authority token mismatch")
    if authority["candidate_id"] != CANDIDATE_ID or authority["study_id"] != STUDY_ID:
        raise OracleError("execution authority study identity mismatch")
    if str(authority["execution_contract_sha256"]).upper() != contract_sha:
        raise OracleError("authority does not bind execution contract")
    if str(authority["environment_sha256"]).upper() != environment_sha:
        raise OracleError("authority does not bind exact environment")
    runner_values: set[str] = set()
    runners = authority["runner_ids"]
    if isinstance(runners, dict):
        runner_values.update(str(value) for value in runners.values())
        runner_values.update(str(key) for key in runners)
    elif isinstance(runners, list):
        runner_values.update(str(value) for value in runners)
    if runner_id != "ORACLE_RUNNER" or runner_id not in runner_values:
        raise OracleError("runner identity is not authorized for this oracle")
    _validate_execution_contract(contract)
    _validate_runtime_process(contract)
    head = _git("rev-parse", "HEAD")
    tree = _git("rev-parse", "HEAD^{tree}")
    if authority["commit"] != head or authority["tree"] != tree:
        raise OracleError("HEAD commit/tree does not match execution authority")
    if _git("status", "--porcelain", "--untracked-files=no"):
        raise OracleError("tracked worktree or index is not clean")
    subjects = (
        "docs: preregister E4 PL Q1T exact-oracle completion",
        "docs: freeze E4 PL Q1T exact reference and oracle",
        "docs: authorize E4 PL Q1T scientific execution",
    )
    chain = [_git("show", "-s", "--format=%s", f"HEAD~{offset}") for offset in (2, 1, 0)]
    if tuple(chain) != subjects:
        raise OracleError("three-stage ancestry/subject chain mismatch")
    plan_raw, _ = _review(
        REFERENCE_DIR / "e4_pl_q1t_plan_review.json",
        "anysolver.s4.e4-pl-q1t-plan-review-v1",
        "ACCEPT_Q1T_PREREGISTRATION_NO_P0_P1",
    )
    implementation_raw, _ = _review(
        REFERENCE_DIR / "e4_pl_q1t_implementation_review.json",
        "anysolver.s4.e4-pl-q1t-implementation-review-v1",
        "ACCEPT_Q1T_IMPLEMENTATION_FREEZE_NO_P0_P1",
    )
    contract_raw, _ = _review(
        REFERENCE_DIR / "e4_pl_q1t_contract_review.json",
        "anysolver.s4.e4-pl-q1t-contract-review-v1",
        "ACCEPT_Q1T_EXECUTION_CONTRACT_NO_P0_P1",
    )
    expected_review_hashes = (
        ("plan_review_sha256", plan_raw),
        ("implementation_review_sha256", implementation_raw),
        ("contract_review_sha256", contract_raw),
    )
    for key, raw in expected_review_hashes:
        if str(authority[key]).upper() != sha256(raw):
            raise OracleError(f"authority review binding mismatch: {key}")
    verdicts = authority["review_verdicts"]
    expected_verdicts = {
        "plan": "ACCEPT_Q1T_PREREGISTRATION_NO_P0_P1",
        "implementation": "ACCEPT_Q1T_IMPLEMENTATION_FREEZE_NO_P0_P1",
        "contract": "ACCEPT_Q1T_EXECUTION_CONTRACT_NO_P0_P1",
    }
    if not isinstance(verdicts, dict) or any(verdicts.get(key) != value for key, value in expected_verdicts.items()):
        raise OracleError("authority review verdict map mismatch")
    outcome_paths = _load_frozen_json("e4_pl_q1t_allowed_extent.json")["path_sets"]["OUTCOME"]
    if any((ROOT / path).exists() for path in outcome_paths):
        raise OracleError("registered outcome path exists before mechanics")
    del authority_sha  # Raw hash was already checked at the caller boundary.


def _guard_execute(inputs: ExecuteInputs) -> GuardEvidence:
    authority_path = _validate_external(inputs.authority_record, existing_file=True)
    contract_path = inputs.contract.resolve(strict=True)
    expected_contract_path = (ROOT / EXECUTION_CONTRACT_PATH).resolve(strict=True)
    if contract_path != expected_contract_path:
        raise OracleError("contract path is not the committed Q1T execution contract")
    authority_raw, authority = _read_canonical(authority_path)
    contract_raw, contract = _read_canonical(contract_path)
    actual_authority_sha = sha256(authority_raw)
    actual_contract_sha = sha256(contract_raw)
    if inputs.authority_sha256.upper() != actual_authority_sha:
        raise OracleError("caller authority hash mismatch")
    if inputs.contract_sha256.upper() != actual_contract_sha:
        raise OracleError("caller contract hash mismatch")
    actual_environment_sha = _validate_environment(inputs.environment_root, inputs.environment_sha256)
    _validate_authority_and_repository(
        authority,
        contract,
        actual_authority_sha,
        actual_contract_sha,
        actual_environment_sha,
        inputs.runner_id,
    )
    output = _validate_external(inputs.output, existing_file=False)
    if output.exists() or not output.parent.is_dir() or output.parent.is_symlink():
        raise OracleError("output must be an absent file in an existing external directory")
    return GuardEvidence(actual_authority_sha, actual_contract_sha, actual_environment_sha)


def _execute(inputs: ExecuteInputs) -> dict[str, Any]:
    guard = _guard_execute(inputs)
    # Adding the caller-owned, graph-verified environment happens after every
    # authority check and immediately before the lazy SymPy import.
    environment_text = str(inputs.environment_root.resolve())
    if environment_text not in sys.path:
        sys.path.insert(0, environment_text)
    sympy = _load_sympy()
    payload, diagnostics = _common_payload(sympy)
    payload_raw = canonical_bytes(payload)
    wrapper = {
        "schema": WRAPPER_SCHEMA,
        "candidate_id": CANDIDATE_ID,
        "study_id": STUDY_ID,
        "implementation_id": IMPLEMENTATION_ID,
        "certificate_payload": payload,
        "certificate_payload_sha256": sha256(payload_raw),
        "execution_contract_sha256": guard.contract_sha256,
        "execution_authority_sha256": guard.authority_sha256,
        "exact_environment_sha256": guard.environment_sha256,
        "implementation_diagnostics": diagnostics,
    }
    raw = canonical_bytes(wrapper)
    inputs.output.write_bytes(raw)
    if inputs.output.read_bytes() != raw:
        raise OracleError("output write verification failed")
    return wrapper


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--static-transcription", action="store_true")
    modes.add_argument("--toy-exact-backend", action="store_true")
    modes.add_argument("--execute", action="store_true")
    parser.add_argument("--authority-record", type=Path)
    parser.add_argument("--authority-sha256")
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--contract-sha256")
    parser.add_argument("--environment-root", type=Path)
    parser.add_argument("--environment-sha256")
    parser.add_argument("--runner-id")
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.static_transcription:
            forbidden = [
                args.authority_record,
                args.authority_sha256,
                args.contract,
                args.contract_sha256,
                args.environment_root,
                args.environment_sha256,
                args.runner_id,
                args.output,
            ]
            if any(item is not None for item in forbidden):
                raise OracleError("static transcription accepts no execute inputs")
            sys.stdout.buffer.write(canonical_bytes(_static_transcription()))
            return 0
        if args.toy_exact_backend:
            forbidden = [
                args.authority_record,
                args.authority_sha256,
                args.contract,
                args.contract_sha256,
                args.runner_id,
                args.output,
            ]
            if any(item is not None for item in forbidden):
                raise OracleError("toy exact backend accepts only the frozen environment root/hash")
            if args.environment_root is not None:
                if args.environment_sha256 is None or args.environment_sha256.upper() != ENVIRONMENT_SHA256.upper():
                    raise OracleError("toy exact environment hash mismatch")
                root = args.environment_root.resolve(strict=True)
                if not root.is_dir() or root.is_symlink():
                    raise OracleError("toy environment root is invalid")
                sys.path.insert(0, str(root))
            elif args.environment_sha256 is not None:
                raise OracleError("toy environment hash requires its environment root")
            sys.stdout.buffer.write(canonical_bytes(toy_exact_backend()))
            return 0
        values = (
            args.authority_record,
            args.authority_sha256,
            args.contract,
            args.contract_sha256,
            args.environment_root,
            args.environment_sha256,
            args.runner_id,
            args.output,
        )
        if any(value is None for value in values):
            raise OracleError("execute requires all eight caller inputs")
        _execute(
            ExecuteInputs(
                args.authority_record,
                args.authority_sha256,
                args.contract,
                args.contract_sha256,
                args.environment_root,
                args.environment_sha256,
                args.runner_id,
                args.output,
            )
        )
        return 0
    except (OracleError, OSError, ValueError, TypeError, ZeroDivisionError) as exc:
        print(f"Q1T_ORACLE_FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
