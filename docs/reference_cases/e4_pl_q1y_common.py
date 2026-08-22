"""Canonical authority and I/O helpers for bounded Q1Y local algebra."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from e4_pl_q1x_common import canonical_bytes, read_json, sha256, validate_environment, verify_file, write_exclusive


CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1y-local-algebra-contract-v1"
PROOF_SCHEMA = "anysolver.s4.e4-pl-q1y-algebra-proof-v1"
PROOF_WRAPPER_SCHEMA = "anysolver.s4.e4-pl-q1y-algebra-proof-wrapper-v1"
CHECK_SCHEMA = "anysolver.s4.e4-pl-q1y-algebra-check-v1"
AGGREGATE_SCHEMA = "anysolver.s4.e4-pl-q1y-algebra-aggregate-v1"
GEOMETRY_IDS = (
    "Q0_SQUARE", "Q1_AFFINE_SKEW", "Q2_TRAPEZOID", "Q3_TAPERED_SKEW",
    "Q4_HOSTILE_ASYMMETRIC_1", "Q5_HOSTILE_ASYMMETRIC_2", "Q3_TAPERED_SKEW_RSTAR_TRANSLATED",
)
OPERATION_IDS = ("E", "R90", "R180", "R270", "MR", "MS", "MD", "MA")


class Q1YError(RuntimeError):
    """Fail-closed Q1Y error."""


def _keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise Q1YError(f"{label} exact-key mismatch")
    return value


def validate_contract(root: Path, path: Path, caller_sha256: str) -> dict[str, Any]:
    repository = root.resolve(strict=True)
    raw, value = read_json(path)
    if sha256(raw) != caller_sha256.upper():
        raise Q1YError("contract caller hash mismatch")
    contract = _keys(value, {
        "candidate_id", "checker", "exact_environment", "frozen_inputs", "geometry_ids",
        "operation_ids", "ordered_signs", "parallelism", "production", "q1b_execution",
        "schema", "scope", "study_id", "terminals",
    }, "contract")
    if contract["schema"] != CONTRACT_SCHEMA:
        raise Q1YError("contract schema mismatch")
    if contract["geometry_ids"] != list(GEOMETRY_IDS) or contract["operation_ids"] != list(OPERATION_IDS):
        raise Q1YError("coverage order mismatch")
    if contract["parallelism"] != {
        "checker_workers": 4, "memory_limit_gib_per_process": 24,
        "numerical_threads_per_process": 1, "producer_workers": 3,
        "replicas_per_geometry": 2, "timeout_seconds_per_process": 600,
    }:
        raise Q1YError("process policy mismatch")
    if contract["scope"] != {
        "base_factorizations": 7, "derived_numbering_cases": 56, "global_kkt": False,
        "internal_fields": 38, "physical_dofs": 24, "quotient_dimension": 18,
        "support_solve": False,
    }:
        raise Q1YError("scope mismatch")
    if contract["production"] != "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED" or contract["q1b_execution"] != "UNAUTHORIZED":
        raise Q1YError("production boundary mismatch")
    rows = contract["frozen_inputs"]
    if not isinstance(rows, list) or len(rows) != 10:
        raise Q1YError("frozen input inventory mismatch")
    for row in rows:
        _keys(row, {"bytes", "path", "sha256"}, "frozen input")
        verify_file(repository / row["path"], size=int(row["bytes"]), digest=str(row["sha256"]))
    environment = _keys(contract["exact_environment"], {
        "bytes", "extracted_file_count", "extracted_file_hash_graph_sha256", "path", "sha256", "sympy_version",
    }, "environment")
    verify_file(repository / environment["path"], size=int(environment["bytes"]), digest=str(environment["sha256"]))
    return contract


__all__ = [
    "AGGREGATE_SCHEMA", "CHECK_SCHEMA", "CONTRACT_SCHEMA", "GEOMETRY_IDS", "OPERATION_IDS",
    "PROOF_SCHEMA", "PROOF_WRAPPER_SCHEMA", "Q1YError", "canonical_bytes", "read_json", "sha256",
    "validate_contract", "validate_environment", "verify_file", "write_exclusive",
]
