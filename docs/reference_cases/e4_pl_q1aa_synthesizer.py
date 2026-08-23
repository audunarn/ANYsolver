#!/usr/bin/env python3
"""Synthesize accepted Q1X/Q1Y3/Q1Z2 evidence without running mechanics."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Sequence


CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1aa-synthesis-contract-v1"
EVIDENCE_SCHEMA = "anysolver.s4.e4-pl-q1aa-synthesis-evidence-v1"
STATUS_SCHEMA = "anysolver.s4.e4-pl-q1aa-status-v1"
GEOMETRY_IDS = [
    "Q0_SQUARE",
    "Q1_AFFINE_SKEW",
    "Q2_TRAPEZOID",
    "Q3_TAPERED_SKEW",
    "Q4_HOSTILE_ASYMMETRIC_1",
    "Q5_HOSTILE_ASYMMETRIC_2",
    "Q3_TAPERED_SKEW_RSTAR_TRANSLATED",
]


class SynthesisError(RuntimeError):
    """Fail-closed synthesis authority or evidence error."""


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SynthesisError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(SynthesisError(f"nonfinite JSON: {token}")),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SynthesisError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise SynthesisError(f"noncanonical JSON: {path}")
    return raw, value


def _keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise SynthesisError(f"{label} exact-key mismatch")
    return value


def validate_contract(root: Path, path: Path, caller_sha256: str) -> dict[str, Any]:
    raw, contract = read_json(path)
    if sha256(raw) != caller_sha256.upper():
        raise SynthesisError("contract caller hash mismatch")
    _keys(
        contract,
        {
            "base_commit",
            "candidate_id",
            "coverage",
            "evidence_inputs",
            "production",
            "q1b_execution",
            "review_authority",
            "schema",
            "scope",
            "study_id",
            "terminals",
        },
        "contract",
    )
    if contract["schema"] != CONTRACT_SCHEMA or contract["base_commit"] != "31cea60897889310e6b62dc479c7a86bd506b4b4":
        raise SynthesisError("contract authority mismatch")
    if contract["coverage"] != {
        "geometry_count": 7,
        "numbering_case_count": 56,
        "quotient_dimension": 18,
        "rigid_mode_count": 6,
        "station_count": 224,
    }:
        raise SynthesisError("contract coverage mismatch")
    if contract["production"] != "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED" or contract["q1b_execution"] != "UNAUTHORIZED":
        raise SynthesisError("contract production boundary mismatch")
    repository = root.resolve(strict=True)
    rows = contract["evidence_inputs"]
    if not isinstance(rows, list) or len(rows) != 9:
        raise SynthesisError("evidence input inventory mismatch")
    for row in rows:
        _keys(row, {"bytes", "git_blob", "path", "role", "sha256"}, "evidence input")
        evidence_path = repository / row["path"]
        raw_evidence = evidence_path.read_bytes()
        if len(raw_evidence) != row["bytes"] or sha256(raw_evidence) != row["sha256"]:
            raise SynthesisError(f"evidence identity mismatch: {row['path']}")
    return contract


def _by_role(root: Path, contract: dict[str, Any], role: str) -> dict[str, Any]:
    row = next((value for value in contract["evidence_inputs"] if value["role"] == role), None)
    if row is None:
        raise SynthesisError(f"missing evidence role: {role}")
    return read_json(root / row["path"])[1]


def select_terminal(
    contract: dict[str, Any],
    *,
    blocked: bool,
    local_algebra: bool,
    patch_recovery_support_covariance: bool,
    unresolved: bool,
    review_accepted: bool,
) -> str:
    terminals = contract["terminals"]
    if blocked or not review_accepted:
        return terminals["blocked"]
    if local_algebra:
        return terminals["local_algebra"]
    if patch_recovery_support_covariance:
        return terminals["patch_recovery_support_covariance"]
    if unresolved:
        return terminals["unclassified"]
    return terminals["provisional_go"]


def synthesize(root: Path, contract_path: Path, caller_sha256: str) -> dict[str, Any]:
    contract = validate_contract(root, contract_path, caller_sha256)
    terminal_table = _by_role(root, contract, "ORIGINAL_TERMINAL_CALCULUS")
    q1x_contract = _by_role(root, contract, "TRANSPORT_CONTRACT")
    q1x = _by_role(root, contract, "TRANSPORT_RESULT")
    q1y3_contract = _by_role(root, contract, "LOCAL_ALGEBRA_CONTRACT")
    q1y3 = _by_role(root, contract, "LOCAL_ALGEBRA_RESULT")
    q1z_contract = _by_role(root, contract, "SUPPORT_CONTRACT")
    q1z = _by_role(root, contract, "SUPPORT_PREDECESSOR_RESULT")
    q1z2_contract = _by_role(root, contract, "SUPPORT_COMPLETION_CONTRACT")
    q1z2 = _by_role(root, contract, "SUPPORT_COMPLETION_RESULT")

    if terminal_table.get("evaluation") != "FIRST_MATCH_IN_ASCENDING_PRECEDENCE_WINS" or len(terminal_table.get("terminals", [])) != 11:
        raise SynthesisError("original terminal calculus mismatch")
    if q1x_contract.get("scope", {}).get("transport_only") is not True:
        raise SynthesisError("Q1X scope mismatch")
    if q1y3_contract.get("coverage") != {
        "base_factorizations": 7,
        "derived_numbering_cases": 56,
        "internal_fields": 38,
        "physical_dofs": 24,
        "quotient_dimension": 18,
        "rigid_modes": 6,
    }:
        raise SynthesisError("Q1Y3 scope mismatch")
    if q1z2_contract.get("q1z_predecessor_aggregate", {}).get("sha256") != sha256(canonical_bytes(q1z)):
        raise SynthesisError("Q1Z/Q1Z2 predecessor binding mismatch")
    frozen = {row["path"]: row["sha256"] for row in q1z_contract.get("frozen_inputs", [])}
    expected_links = {
        "docs/reference_cases/e4_pl_q1x_transport_contract.json": sha256(canonical_bytes(q1x_contract)),
        "docs/reference_cases/e4_pl_q1x_bounded_result.json": sha256(canonical_bytes(q1x)),
        "docs/reference_cases/e4_pl_q1y3_local_algebra_contract.json": sha256(canonical_bytes(q1y3_contract)),
        "docs/reference_cases/e4_pl_q1y3_bounded_result.json": sha256(canonical_bytes(q1y3)),
    }
    if any(frozen.get(path) != digest for path, digest in expected_links.items()):
        raise SynthesisError("cross-layer contract binding mismatch")

    x_geometry = [row.get("geometry_id") for row in q1x.get("shards", [])]
    y_geometry = [row.get("geometry_id") for row in q1y3.get("shards", [])]
    z_geometry = [row.get("geometry_id") for row in q1z.get("shards", [])]
    geometry_aligned = x_geometry == GEOMETRY_IDS and y_geometry == GEOMETRY_IDS and z_geometry == GEOMETRY_IDS
    transport = (
        q1x.get("terminal") == "UNCLASSIFIED_E4_PL_Q1X_TRANSPORT_CLOSED_ONLY"
        and q1x.get("coverage") == {"case_count": 56, "geometry_count": 7, "station_count": 224}
        and all(row.get("checker_byte_identical") for row in q1x.get("shards", []))
    )
    local = (
        q1y3.get("terminal") == "UNCLASSIFIED_E4_PL_Q1Y3_LOCAL_ALGEBRA_CLOSED_ONLY"
        and q1y3.get("coverage") == {"case_count": 56, "geometry_count": 7, "rigid_mode_count": 6}
        and q1y3.get("local_algebra_contradiction") is False
        and q1y3.get("operator_covariance_contradiction") is False
        and q1y3.get("ordered_sign_unresolved") is False
        and q1y3.get("q3_proper_global_local_identity") is True
        and all(row.get("checker_byte_identical") and not row.get("proof_disagreement") for row in q1y3.get("shards", []))
    )
    support = (
        q1z2.get("terminal") == "UNCLASSIFIED_E4_PL_Q1Z2_SUPPORT_KKT_CLOSED_ONLY"
        and q1z2.get("coverage") == {"case_count": 56, "geometry_count": 7, "new_case_count": 8, "predecessor_case_count": 48}
        and q1z2.get("checker_byte_identical") is True
        and q1z2.get("support_boundary_contradiction") is False
        and q1z2.get("kkt_reaction_contradiction") is False
        and q1z2.get("support_covariance_contradiction") is False
        and q1z2.get("q3star_proper_global_support_identity") is True
    )
    production_exact = all(
        value.get("production") == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED" and value.get("q1b_execution") == "UNAUTHORIZED"
        for value in (q1x, q1y3, q1z, q1z2)
    )
    deterministic = (
        q1x.get("aggregate", {}).get("two_cycle_byte_identical") is True
        and all(row.get("checker_byte_identical") for row in q1y3.get("shards", []))
        and q1z2.get("checker_byte_identical") is True
    )
    gates = {
        "cross_layer_authority_exact": True,
        "deterministic_evidence": deterministic,
        "geometry_case_alignment": geometry_aligned,
        "local_algebra_closed": local,
        "ordered_signs_resolved": q1y3.get("ordered_sign_unresolved") is False,
        "production_boundary_unchanged": production_exact,
        "support_kkt_reaction_closed": support,
        "transport_patch_recovery_closed": transport,
    }
    complete = all(gates.values())
    return {
        "candidate_id": contract["candidate_id"],
        "contract_sha256": caller_sha256.upper(),
        "coverage": contract["coverage"] if complete else {key: 0 for key in contract["coverage"]},
        "evidence_disposition": "LOCAL_QUALIFICATION_EVIDENCE_COMPLETE_PENDING_INDEPENDENT_REVIEW" if complete else "LOCAL_QUALIFICATION_EVIDENCE_INCOMPLETE",
        "evidence_hashes": {row["role"]: row["sha256"] for row in contract["evidence_inputs"]},
        "expected_terminal_after_accepted_review": contract["terminals"]["provisional_go"] if complete else contract["terminals"]["blocked"],
        "gates": gates,
        "production": contract["production"],
        "q1b_execution": contract["q1b_execution"],
        "q1b_plan_preparation": "PENDING_INDEPENDENT_REVIEW" if complete else "UNAUTHORIZED",
        "schema": EVIDENCE_SCHEMA,
        "study_id": contract["study_id"],
    }


def write_exclusive(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthesize-local-qualification", action="store_true", required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        value = synthesize(args.repository_root.resolve(strict=True), args.contract, args.contract_sha256)
        write_exclusive(args.output, value)
        return 0
    except (OSError, TypeError, ValueError, SynthesisError) as exc:
        print(f"BLOCKED_E4_PL_Q1AA_EVIDENCE_OR_REVIEW: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
