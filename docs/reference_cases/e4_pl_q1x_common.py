"""Canonical authority and I/O helpers for the bounded Q1X transport study."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from e4_pl_q1w_common import (
    Q1WError,
    canonical_bytes,
    read_json,
    sha256,
    validate_environment,
    verify_file,
    write_exclusive,
)


CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1x-transport-contract-v1"
PROOF_SCHEMA = "anysolver.s4.e4-pl-q1x-geometry-proof-v1"
PROOF_WRAPPER_SCHEMA = "anysolver.s4.e4-pl-q1x-geometry-proof-wrapper-v1"
CHECK_SCHEMA = "anysolver.s4.e4-pl-q1x-geometry-check-v1"
AGGREGATE_SCHEMA = "anysolver.s4.e4-pl-q1x-transport-aggregate-v1"

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
GAUSS_IDS = ("GP_MM", "GP_PM", "GP_PP", "GP_MP")
PATCH_IDS = ("MEMBRANE_PATCH", "BENDING_PATCH", "SHEAR_PATCH", "COMBINED_PHYSICAL_PATCH")


class Q1XError(Q1WError):
    """Fail-closed Q1X validation error."""


def _exact_keys(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise Q1XError(f"{label} exact-key schema mismatch")
    return value


def validate_contract(repository_root: Path, contract_path: Path, contract_sha256: str) -> dict[str, Any]:
    root = repository_root.resolve(strict=True)
    raw, value = read_json(contract_path)
    if sha256(raw) != contract_sha256.upper():
        raise Q1XError("transport contract caller hash mismatch")
    contract = _exact_keys(
        value,
        {
            "candidate_id",
            "checker",
            "exact_environment",
            "frozen_inputs",
            "geometry_ids",
            "historical_reference",
            "operation_ids",
            "parallelism",
            "primitive_field_table",
            "production",
            "q1b_execution",
            "scope",
            "schema",
            "study_id",
            "terminals",
        },
        "transport contract",
    )
    if contract["schema"] != CONTRACT_SCHEMA:
        raise Q1XError("transport contract schema mismatch")
    if contract["geometry_ids"] != list(GEOMETRY_IDS) or contract["operation_ids"] != list(OPERATION_IDS):
        raise Q1XError("frozen 7x8 coverage order mismatch")
    if contract["parallelism"] != {
        "checker_workers": 4,
        "memory_limit_gib_per_process": 24,
        "numerical_threads_per_process": 1,
        "producer_workers": 3,
        "replicas_per_geometry": 2,
        "timeout_seconds_per_process": 600,
    }:
        raise Q1XError("bounded process policy mismatch")
    if contract["checker"] != {
        "backend": "SYMPY_QQ_ALGEBRAIC_FIELD",
        "equality": "DOMAIN_ELEMENT_EQUALITY_WITH_FIELD_ZERO",
        "forbidden": ["FLOAT", "EVALF", "TOLERANCE_EQUALITY", "INTERVAL_CONTAINMENT_EQUALITY", "GENERIC_SIMPLIFY_ZERO"],
    }:
        raise Q1XError("checker policy mismatch")
    if contract["scope"] != {
        "assembled_38_field_system": False,
        "full_local_qualification": False,
        "global_kkt": False,
        "rank_psd": False,
        "registered_cases": 56,
        "stations": 224,
        "transport_only": True,
    }:
        raise Q1XError("bounded scientific scope mismatch")
    if contract["production"] != "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED" or contract["q1b_execution"] != "UNAUTHORIZED":
        raise Q1XError("production restriction mismatch")
    terminals = contract["terminals"]
    if terminals != {
        "blocked": "BLOCKED_E4_PL_Q1X_PROOF_OR_REVIEW",
        "exact_counterexample": "NO_GO_E4_PL_Q1X_EXACT_TRANSPORT_COUNTEREXAMPLE",
        "transport_closed_only": "UNCLASSIFIED_E4_PL_Q1X_TRANSPORT_CLOSED_ONLY",
    }:
        raise Q1XError("terminal vocabulary mismatch")
    rows = contract["frozen_inputs"]
    if not isinstance(rows, list) or len(rows) != 8:
        raise Q1XError("frozen input inventory mismatch")
    seen: set[str] = set()
    for row in rows:
        _exact_keys(row, {"bytes", "path", "sha256"}, "frozen input row")
        relative = str(row["path"])
        if relative in seen:
            raise Q1XError("duplicate frozen input path")
        seen.add(relative)
        verify_file(root / relative, size=int(row["bytes"]), digest=str(row["sha256"]))
    environment = _exact_keys(
        contract["exact_environment"],
        {"bytes", "extracted_file_count", "extracted_file_hash_graph_sha256", "path", "sha256", "sympy_version"},
        "exact environment",
    )
    verify_file(root / str(environment["path"]), size=int(environment["bytes"]), digest=str(environment["sha256"]))
    primitive = _exact_keys(
        contract["primitive_field_table"],
        {"bytes", "path", "schema", "sha256"},
        "primitive field table",
    )
    if primitive["schema"] != "anysolver.s4.e4-pl-q1x-primitive-fields-v1":
        raise Q1XError("primitive field table schema mismatch")
    verify_file(root / str(primitive["path"]), size=int(primitive["bytes"]), digest=str(primitive["sha256"]))
    historical = _exact_keys(
        contract["historical_reference"],
        {"bytes", "certificate_payload_sha256", "copies", "role", "sha256"},
        "historical reference",
    )
    if historical != {
        "bytes": 2688589,
        "certificate_payload_sha256": "8B0D08DE85B10B2F6549DD11F731EEDCF700D59814A66E0856548B45F008BE49",
        "copies": 2,
        "role": "HISTORICAL_WITNESS_SELECTION_NOT_Q1X_SCIENTIFIC_RESULT",
        "sha256": "4B570FC89FEA9DE0D9DE1A2E97B8B7B245BEBAEFCDD3B78CD08B4C8803A3F04E",
    }:
        raise Q1XError("historical wrapper authority mismatch")
    return contract


def compact_json_copy(value: Any) -> Any:
    """Return a JSON-value deep copy without importing producer mechanics."""

    return json.loads(canonical_bytes(value).decode("utf-8"))


__all__ = [
    "AGGREGATE_SCHEMA",
    "CHECK_SCHEMA",
    "CONTRACT_SCHEMA",
    "GAUSS_IDS",
    "GEOMETRY_IDS",
    "OPERATION_IDS",
    "PATCH_IDS",
    "PROOF_SCHEMA",
    "PROOF_WRAPPER_SCHEMA",
    "Q1XError",
    "canonical_bytes",
    "compact_json_copy",
    "read_json",
    "sha256",
    "validate_contract",
    "validate_environment",
    "verify_file",
    "write_exclusive",
]
