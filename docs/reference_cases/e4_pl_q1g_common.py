"""Shared canonical I/O and exact rational primitives for Q1G.

This module deliberately contains no shell mechanics or domain classification.
The producer and checker separately transcribe the rigid-field construction.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from fractions import Fraction
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


STUDY_ID = "study_e4_pl_q1g.q1f_rigid_range_repair_and_domain_coercivity_v1"
CANDIDATE_ID = "candidate_e4_pl_q1g.wg2020_g1_domain_coercivity_v1"
CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1g-contract-v1"
BASE_COMMIT = "c9d75eaed17e658e84879085a01ecca823dd32cd"
Q1F_CLOSEOUT = "ace68489b9061450c06250ccc3573515c39382f7"


class Q1GError(RuntimeError):
    """Fail-closed Q1G authority or proof error."""


Matrix = list[list[Fraction]]


def _pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in rows:
        if key in result:
            raise Q1GError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _nonfinite(token: str) -> None:
    raise Q1GError(f"non-finite JSON token: {token}")


def canonical_bytes(value: Any) -> bytes:
    try:
        return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise Q1GError("value is not finite canonical JSON") from exc


def strict_json_bytes(raw: bytes, *, canonical: bool = True) -> Any:
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw:
        raise Q1GError("JSON must be UTF-8/LF and BOM-free")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_nonfinite)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Q1GError("invalid strict JSON") from exc
    if canonical and canonical_bytes(value) != raw:
        raise Q1GError("JSON is not canonical sorted compact UTF-8/LF")
    return value


def read_json(path: Path, *, canonical: bool = True) -> tuple[bytes, Any]:
    target = path.resolve()
    if not target.is_file() or target.is_symlink():
        raise Q1GError(f"not a regular nonsymlink file: {target}")
    raw = target.read_bytes()
    return raw, strict_json_bytes(raw, canonical=canonical)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def write_exclusive(path: Path, value: Any) -> None:
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical_bytes(value)
    try:
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0), 0o600)
    except FileExistsError as exc:
        raise Q1GError(f"exclusive output already exists: {target}") from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        try:
            target.unlink(missing_ok=True)
        finally:
            raise
    if target.read_bytes() != raw:
        target.unlink(missing_ok=True)
        raise Q1GError("exclusive output reopen verification failed")


def exact_keys(value: Any, expected: Iterable[str], label: str) -> dict[str, Any]:
    keys = set(expected)
    if not isinstance(value, dict) or set(value) != keys:
        raise Q1GError(f"{label} exact-key mismatch")
    return value


def rational(value: str | int | Fraction) -> Fraction:
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return Fraction(value)
    if not isinstance(value, str) or not value or value.strip() != value:
        raise Q1GError("invalid rational token")
    try:
        result = Fraction(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise Q1GError("invalid rational token") from exc
    if token(result) != value:
        raise Q1GError("noncanonical rational token")
    return result


def token(value: Fraction | int) -> str:
    item = Fraction(value)
    return str(item.numerator) if item.denominator == 1 else f"{item.numerator}/{item.denominator}"


def matrix_record(matrix: Sequence[Sequence[Fraction]]) -> list[list[str]]:
    return [[token(value) for value in row] for row in matrix]


def matrix_from_record(value: Any, rows: int, columns: int, label: str) -> Matrix:
    if not isinstance(value, list) or len(value) != rows:
        raise Q1GError(f"{label} row count mismatch")
    result: Matrix = []
    for row in value:
        if not isinstance(row, list) or len(row) != columns:
            raise Q1GError(f"{label} column count mismatch")
        result.append([rational(item) for item in row])
    return result


def identity(size: int) -> Matrix:
    return [[Fraction(int(i == j)) for j in range(size)] for i in range(size)]


def transpose(matrix: Sequence[Sequence[Fraction]]) -> Matrix:
    if not matrix:
        return []
    return [list(row) for row in zip(*matrix)]


def multiply(left: Sequence[Sequence[Fraction]], right: Sequence[Sequence[Fraction]]) -> Matrix:
    if not left or not right or len(left[0]) != len(right):
        raise Q1GError("matrix multiplication dimension mismatch")
    if any(len(row) != len(left[0]) for row in left) or any(len(row) != len(right[0]) for row in right):
        raise Q1GError("ragged matrix")
    right_t = transpose(right)
    return [[sum((Fraction(a) * Fraction(b) for a, b in zip(row, column)), Fraction()) for column in right_t] for row in left]


def matrix_equal(left: Sequence[Sequence[Fraction]], right: Sequence[Sequence[Fraction]]) -> bool:
    return len(left) == len(right) and all(len(a) == len(b) and all(Fraction(x) == Fraction(y) for x, y in zip(a, b)) for a, b in zip(left, right))


def rref(matrix: Sequence[Sequence[Fraction]]) -> tuple[Matrix, tuple[int, ...]]:
    if not matrix or not matrix[0]:
        raise Q1GError("RREF matrix must be nonempty")
    result = [[Fraction(value) for value in row] for row in matrix]
    if any(len(row) != len(result[0]) for row in result):
        raise Q1GError("ragged RREF matrix")
    pivot_row = 0
    pivots: list[int] = []
    for column in range(len(result[0])):
        selected = next((row for row in range(pivot_row, len(result)) if result[row][column]), None)
        if selected is None:
            continue
        result[pivot_row], result[selected] = result[selected], result[pivot_row]
        pivot = result[pivot_row][column]
        result[pivot_row] = [value / pivot for value in result[pivot_row]]
        for row in range(len(result)):
            if row == pivot_row:
                continue
            factor = result[row][column]
            if factor:
                result[row] = [value - factor * base for value, base in zip(result[row], result[pivot_row])]
        pivots.append(column)
        pivot_row += 1
        if pivot_row == len(result):
            break
    return result, tuple(pivots)


def rank(matrix: Sequence[Sequence[Fraction]]) -> int:
    return len(rref(matrix)[1])


def inverse(matrix: Sequence[Sequence[Fraction]]) -> Matrix:
    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise Q1GError("inverse requires square matrix")
    augmented = [[Fraction(value) for value in row] + identity(size)[index] for index, row in enumerate(matrix)]
    reduced, pivots = rref(augmented)
    if pivots[:size] != tuple(range(size)):
        raise Q1GError("singular matrix")
    return [row[size:] for row in reduced]


def determinant(matrix: Sequence[Sequence[Fraction]]) -> Fraction:
    size = len(matrix)
    if size == 0 or any(len(row) != size for row in matrix):
        raise Q1GError("determinant requires square matrix")
    work = [[Fraction(value) for value in row] for row in matrix]
    result = Fraction(1)
    for column in range(size):
        selected = next((row for row in range(column, size) if work[row][column]), None)
        if selected is None:
            return Fraction()
        if selected != column:
            work[column], work[selected] = work[selected], work[column]
            result = -result
        pivot = work[column][column]
        result *= pivot
        for row in range(column + 1, size):
            factor = work[row][column] / pivot
            for item in range(column + 1, size):
                work[row][item] -= factor * work[column][item]
    return result


def leftmost_independent_rows(matrix: Sequence[Sequence[Fraction]], count: int) -> tuple[int, ...]:
    selected: list[int] = []
    current: Matrix = []
    current_rank = 0
    for index, row in enumerate(matrix):
        candidate = current + [[Fraction(value) for value in row]]
        candidate_rank = rank(candidate)
        if candidate_rank > current_rank:
            selected.append(index)
            current = candidate
            current_rank = candidate_rank
            if len(selected) == count:
                return tuple(selected)
    raise Q1GError("matrix lacks requested independent rows")


def subrows(matrix: Sequence[Sequence[Fraction]], rows: Sequence[int]) -> Matrix:
    return [[Fraction(value) for value in matrix[index]] for index in rows]


def contract_path(repository_root: Path) -> Path:
    return repository_root.resolve() / "docs" / "reference_cases" / "e4_pl_q1g_contract.json"


def _git(repository_root: Path, *arguments: str) -> str:
    completed = subprocess.run(["git", *arguments], cwd=repository_root, text=True, encoding="utf-8", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if completed.returncode:
        raise Q1GError(f"git authority command failed: {' '.join(arguments)}")
    return completed.stdout.strip()


def _verify_tracked_clean(repository_root: Path, relative: str) -> None:
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise Q1GError("reviewed path is not repository-relative")
    _git(repository_root, "ls-files", "--error-unmatch", "--", relative)
    completed = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", relative],
        cwd=repository_root, check=False,
    )
    if completed.returncode != 0:
        raise Q1GError(f"tracked authority path differs from HEAD: {relative}")


def _verify_review(repository_root: Path, relative: str, schema: str, verdict: str) -> dict[str, Any]:
    raw, review = read_json(repository_root / relative)
    if review.get("schema") != schema or review.get("verdict") != verdict or review.get("findings") != []:
        raise Q1GError(f"review authority mismatch: {relative}")
    rows = review.get("reviewed_inputs")
    if not isinstance(rows, list) or not rows:
        raise Q1GError(f"reviewed input extent is empty: {relative}")
    paths: set[str] = set()
    for row in rows:
        exact_keys(row, {"bytes", "path", "sha256"}, "reviewed input")
        path = row["path"]
        if path in paths:
            raise Q1GError("duplicate reviewed input path")
        paths.add(path)
        _verify_tracked_clean(repository_root, path)
        current = (repository_root / path).read_bytes()
        if len(current) != row["bytes"] or sha256(current) != row["sha256"]:
            raise Q1GError(f"reviewed input identity mismatch: {path}")
    _verify_tracked_clean(repository_root, relative)
    if canonical_bytes(review) != raw:
        raise Q1GError("review is not canonical")
    return review


def validate_contract(repository_root: Path, path: Path, caller_sha256: str) -> dict[str, Any]:
    root = repository_root.resolve()
    expected_path = contract_path(root)
    if path.resolve() != expected_path:
        raise Q1GError("contract path is not the repository Q1G contract")
    raw, value = read_json(expected_path)
    if sha256(raw) != caller_sha256.upper():
        raise Q1GError("contract caller hash mismatch")
    if value.get("schema") != CONTRACT_SCHEMA or value.get("study_id") != STUDY_ID or value.get("candidate_id") != CANDIDATE_ID:
        raise Q1GError("contract identity mismatch")
    authority = value.get("authority", {})
    if authority.get("base_commit") != BASE_COMMIT or authority.get("q1f_closeout_commit") != Q1F_CLOSEOUT:
        raise Q1GError("contract Git authority mismatch")
    if _git(root, "cat-file", "-t", BASE_COMMIT) != "commit" or _git(root, "cat-file", "-t", Q1F_CLOSEOUT) != "commit":
        raise Q1GError("bound Git commits are unavailable")
    if _git(root, "merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"):
        raise Q1GError("Q1G HEAD is not descended from merged Q1F authority")
    for row in value.get("q1f_inputs", {}).values():
        target = root / row["path"]
        current = target.read_bytes()
        if len(current) != row["bytes"] or sha256(current) != row["sha256"]:
            raise Q1GError(f"Q1F input identity mismatch: {row['path']}")
    if len(value.get("rejected_drafts", [])) != 8:
        raise Q1GError("rejected draft inventory mismatch")
    plan_review = _verify_review(
        root, "docs/reference_cases/e4_pl_q1g_plan_review.json",
        "anysolver.s4.e4-pl-q1g-plan-review-v1",
        "ACCEPT_Q1G_RIGID_RANGE_PREREGISTRATION_NO_P0_P1",
    )
    implementation_review = _verify_review(
        root, "docs/reference_cases/e4_pl_q1g_implementation_review.json",
        "anysolver.s4.e4-pl-q1g-implementation-review-v1",
        "ACCEPT_Q1G_RIGID_RANGE_IMPLEMENTATION_NO_P0_P1",
    )
    execution_review = _verify_review(
        root, "docs/reference_cases/e4_pl_q1g_execution_review.json",
        "anysolver.s4.e4-pl-q1g-execution-review-v1",
        "ACCEPT_Q1G_BOUNDED_EXECUTION_CONTRACT_NO_P0_P1",
    )
    expected_execution_paths = {
        "docs/reference_cases/e4_pl_q1g_contract.json",
        "docs/reference_cases/e4_pl_q1g_implementation_review.json",
        "docs/reference_cases/e4_pl_q1g_plan_review.json",
    }
    if {row["path"] for row in execution_review["reviewed_inputs"]} != expected_execution_paths:
        raise Q1GError("execution review exact input extent mismatch")
    if plan_review.get("reviewer_independence", {}).get("mechanics_executed") is not False:
        raise Q1GError("plan review mechanics boundary mismatch")
    if implementation_review.get("reviewer_independence", {}).get("checker_imports_producer") is not False:
        raise Q1GError("implementation independence mismatch")
    return value


def pythagorean_rotations() -> tuple[Matrix, ...]:
    return (
        [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]],
        [[Fraction(3, 5), Fraction(-4, 5)], [Fraction(4, 5), Fraction(3, 5)]],
        [[Fraction(-5, 13), Fraction(-12, 13)], [Fraction(12, 13), Fraction(-5, 13)]],
    )


def validate_proper_rotation(rotation: Sequence[Sequence[Fraction]]) -> None:
    if not matrix_equal(multiply(transpose(rotation), rotation), identity(2)) or determinant(rotation) != 1:
        raise Q1GError("rotation is not exact proper orthogonal")


def sample_transforms() -> tuple[tuple[tuple[Fraction, Fraction], Matrix, Fraction], ...]:
    translations = ((Fraction(), Fraction()), (Fraction(2, 3), Fraction(-5, 7)), (Fraction(-11, 13), Fraction(17, 19)))
    scales = (Fraction(1), Fraction(7, 5), Fraction(19, 11))
    rotations = pythagorean_rotations()
    return tuple((translations[index], rotations[index], scales[index]) for index in range(3))


def verify_environment_threads() -> bool:
    return all(os.environ.get(name, "1") == "1" for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"))


__all__ = [
    "BASE_COMMIT", "CANDIDATE_ID", "CONTRACT_SCHEMA", "Matrix", "Q1GError", "STUDY_ID",
    "canonical_bytes", "determinant", "exact_keys", "identity", "inverse", "leftmost_independent_rows",
    "matrix_equal", "matrix_from_record", "matrix_record", "multiply", "rank", "rational", "read_json",
    "sample_transforms", "sha256", "subrows", "token", "transpose", "validate_contract",
    "validate_proper_rotation", "verify_environment_threads", "write_exclusive",
]
