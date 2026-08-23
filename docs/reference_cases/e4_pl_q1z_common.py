"""Canonical authority and I/O helpers for bounded Q1Z support/KKT proof."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from e4_pl_q1x_common import (
    canonical_bytes,
    read_json,
    sha256,
    validate_environment,
    verify_file,
    write_exclusive,
)


CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1z-support-kkt-contract-v1"
PROOF_SCHEMA = "anysolver.s4.e4-pl-q1z-support-proof-v1"
PROOF_WRAPPER_SCHEMA = "anysolver.s4.e4-pl-q1z-support-proof-wrapper-v1"
CHECK_SCHEMA = "anysolver.s4.e4-pl-q1z-support-check-v1"
AGGREGATE_SCHEMA = "anysolver.s4.e4-pl-q1z-support-aggregate-v1"
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


class Q1ZError(RuntimeError):
    """Fail-closed Q1Z authority or proof error."""


def _keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise Q1ZError(f"{label} exact-key mismatch")
    return value


def validate_contract(root: Path, path: Path, caller_sha256: str) -> dict[str, Any]:
    repository = root.resolve(strict=True)
    raw, value = read_json(path)
    if sha256(raw) != caller_sha256.upper():
        raise Q1ZError("contract caller hash mismatch")
    contract = _keys(
        value,
        {
            "base_commit",
            "candidate_id",
            "coverage",
            "exact_environment",
            "frozen_inputs",
            "parallelism",
            "production",
            "q1b_execution",
            "q1y3_proofs",
            "schema",
            "scope",
            "study_id",
            "terminals",
        },
        "contract",
    )
    if contract["schema"] != CONTRACT_SCHEMA:
        raise Q1ZError("contract schema mismatch")
    if contract["base_commit"] != "795ae1b44748cd6896a49079f82c947b96260aea":
        raise Q1ZError("base commit mismatch")
    if contract["coverage"] != {
        "base_support_systems": 7,
        "derived_numbering_cases": 56,
        "drill_coordinates": 4,
        "kkt_dimension": 44,
        "physical_support_rows": 20,
    }:
        raise Q1ZError("coverage mismatch")
    if contract["parallelism"] != {
        "checker_workers": 4,
        "global_timeout_seconds": 300,
        "memory_limit_gib_per_process": 8,
        "numerical_threads_per_process": 1,
        "producer_workers": 7,
        "replicas_per_geometry": 2,
        "timeout_seconds_per_process": 180,
        "weighted_process_slots": 8,
    }:
        raise Q1ZError("parallel policy mismatch")
    if contract["scope"] != {
        "full_local_qualification": False,
        "q1b_authorized": False,
        "stationary_reassembly": False,
        "support_kkt_reaction": True,
    }:
        raise Q1ZError("scope mismatch")
    if (
        contract["production"] != "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
        or contract["q1b_execution"] != "UNAUTHORIZED"
    ):
        raise Q1ZError("production boundary mismatch")
    rows = contract["frozen_inputs"]
    if not isinstance(rows, list) or len(rows) != 7:
        raise Q1ZError("frozen input inventory mismatch")
    for row in rows:
        _keys(row, {"bytes", "path", "sha256"}, "frozen input")
        verify_file(repository / row["path"], size=int(row["bytes"]), digest=str(row["sha256"]))
    proofs = contract["q1y3_proofs"]
    if not isinstance(proofs, list) or len(proofs) != 7:
        raise Q1ZError("Q1Y3 proof inventory mismatch")
    if [row.get("geometry_id") for row in proofs] != list(GEOMETRY_IDS):
        raise Q1ZError("Q1Y3 proof order mismatch")
    for row in proofs:
        _keys(row, {"bytes", "geometry_id", "name", "sha256"}, "Q1Y3 proof")
    environment = _keys(
        contract["exact_environment"],
        {
            "bytes",
            "extracted_file_count",
            "extracted_file_hash_graph_sha256",
            "path",
            "sha256",
            "sympy_version",
        },
        "environment",
    )
    verify_file(
        repository / environment["path"],
        size=int(environment["bytes"]),
        digest=str(environment["sha256"]),
    )
    return contract


def proof_authority(contract: dict[str, Any], geometry_id: str) -> dict[str, Any]:
    for row in contract["q1y3_proofs"]:
        if row["geometry_id"] == geometry_id:
            return row
    raise Q1ZError("unregistered Q1Y3 proof geometry")


__all__ = [
    "AGGREGATE_SCHEMA",
    "CHECK_SCHEMA",
    "CONTRACT_SCHEMA",
    "GEOMETRY_IDS",
    "OPERATION_IDS",
    "PROOF_SCHEMA",
    "PROOF_WRAPPER_SCHEMA",
    "Q1ZError",
    "canonical_bytes",
    "proof_authority",
    "read_json",
    "sha256",
    "validate_contract",
    "validate_environment",
    "verify_file",
    "write_exclusive",
]
