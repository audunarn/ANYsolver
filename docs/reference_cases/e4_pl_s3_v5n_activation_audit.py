"""Standard-library-only V5N synthesis of S3 activation readiness."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
PLAN = REFERENCE / "e4_pl_s3_v5n_activation_audit_plan.json"
CONTRACT = REFERENCE / "e4_pl_s3_v5n_activation_audit_contract.json"
SOURCE = ROOT / "src/anysolver/e4_pl_s3_v2c_element.py"
PASS = "PASS_ACCEPTED_EVIDENCE"
MISSING = "MISSING_REQUIRED_AUTHORITY_OR_EVIDENCE"
BLOCKED = "BLOCKED_E4_PL_S3_V5N_EVIDENCE_OR_REVIEW"
NO_GO = "NO_GO_E4_PL_S3_V5N_ACTIVATION_QUALIFICATION"
UNCLASSIFIED = "UNCLASSIFIED_E4_PL_S3_V5N_NATIVE_PARITY_SOURCE_REQUIRED"
GO = "PROVISIONAL_GO_E4_PL_S3_V5N_ACTIVATION_EXECUTION_PREPARATION"


class V5NActivationAuditError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise V5NActivationAuditError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=lambda token: (_ for _ in ()).throw(V5NActivationAuditError(f"nonfinite token: {token}")))
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V5NActivationAuditError(f"noncanonical JSON: {path}")
    return raw, value


def validate_authority() -> tuple[dict[str, Any], dict[str, Any]]:
    _plan_raw, plan = load(PLAN)
    _contract_raw, contract = load(CONTRACT)
    if plan.get("schema") != "anysolver.e4-pl-s3-v5n-activation-audit-plan-v1" or contract.get("schema") != "anysolver.e4-pl-s3-v5n-activation-audit-contract-v1":
        raise V5NActivationAuditError("V5N protocol schema mismatch")
    if plan.get("production_boundary") != contract.get("production_boundary"):
        raise V5NActivationAuditError("V5N production boundary mismatch")
    for row in contract.get("frozen_inputs", []):
        raw = (ROOT / row["path"]).read_bytes()
        if len(raw) != row["bytes"] or sha256(raw) != row["sha256"]:
            raise V5NActivationAuditError(f"frozen input mismatch: {row['path']}")
    return plan, contract


def capability_sets() -> tuple[frozenset[str], frozenset[str]]:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    values: dict[str, frozenset[str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id
        if name not in {"SUPPORTED_OPERATIONS", "BLOCKED_OPERATIONS"}:
            continue
        if not isinstance(node.value, ast.Call) or not node.value.args:
            raise V5NActivationAuditError(f"{name} is not a frozen literal set")
        made = ast.literal_eval(node.value.args[0])
        if not isinstance(made, set) or not all(isinstance(item, str) for item in made):
            raise V5NActivationAuditError(f"{name} is malformed")
        values[name] = frozenset(made)
    if set(values) != {"SUPPORTED_OPERATIONS", "BLOCKED_OPERATIONS"}:
        raise V5NActivationAuditError("candidate capability sets are absent")
    return values["SUPPORTED_OPERATIONS"], values["BLOCKED_OPERATIONS"]


def _accepted_review(value: Mapping[str, Any]) -> bool:
    findings = value.get("findings")
    return isinstance(findings, dict) and findings.get("P0") == [] and findings.get("P1") == []


def adjudicate(plan: Mapping[str, Any], evidence: Mapping[str, Mapping[str, Any]], blocked_operations: frozenset[str]) -> dict[str, Any]:
    v5e, v5h, v5l, v5m, source_selection = (evidence[name] for name in ("v5e", "v5h", "v5l", "v5m", "source_selection"))
    accepted = {
        "LOCAL_OPERATOR_AND_RECOVERY": bool(v5h.get("terminal") == "PROVISIONAL_GO_E4_PL_S3_V5H_STAGE4B_PROTOCOL_PREPARATION" and len(v5h.get("cycles", [])) == 2 and all(row.get("passed") is True for row in v5h.get("cycles", []))),
        "FULL_252_MIXED_TOPOLOGY_N20_N40_N80_N160": bool(v5e.get("coverage", {}).get("record_count_per_cycle") == 252 and v5e.get("coverage", {}).get("cycle_count") == 2),
        "SPECIAL_INTERFACES_D3_AND_DIRECTOR_REVERSAL": bool(v5h.get("coverage", {}).get("special_interface_complete") is True),
        "LOCKING_T_OVER_L_1E1_TO_1E6": bool(v5e.get("coverage", {}).get("locking_thickness_count") == 6),
        "MODAL": v5l.get("gate_status", {}).get("modal") == "PASS_MEASURED_REGISTERED_SCOPE",
        "BUCKLING": v5l.get("gate_status", {}).get("buckling") == "PASS_MEASURED_REGISTERED_SCOPE",
        "RECOVERY": bool(v5h.get("worst", {}).get("work_worst_hex") and v5h.get("worst", {}).get("component_worst_hex")),
        "BATCH": v5m.get("gate_status", {}).get("BATCH_4096") == "PASS_MEASURED_REGISTERED_SCOPE",
        "SAME_FORMULATION_RESTART": "restart" not in blocked_operations,
        "SERIALIZATION": v5m.get("gate_status", {}).get("SERIALIZATION_RESTART") == "PASS_MEASURED_REGISTERED_SCOPE",
        "MIGRATION": bool(v5m.get("migration_gate_passed") is True),
        "CROSS_WHEEL_ECOSYSTEM": bool(v5m.get("cross_wheel_ecosystem_gate_passed") is True),
        "NONLINEAR_GEOMETRY": bool(source_selection.get("scope", {}).get("full_nonlinear_authorized") is True and "nonlinear_geometry" not in blocked_operations),
        "MATERIAL_NONLINEARITY": bool(source_selection.get("scope", {}).get("full_nonlinear_authorized") is True and "material_nonlinearity" not in blocked_operations),
        "INITIAL_FIELDS": bool(source_selection.get("scope", {}).get("initial_fields_authorized") is True),
        "GENERALIZED_SECTIONS": bool(source_selection.get("scope", {}).get("generalized_sections_authorized") is True and "generalized_section" not in blocked_operations),
        "OFFSETS_AND_COMPLETE_LOAD_WORK": bool(source_selection.get("scope", {}).get("complete_load_work_authorized") is True and not {"follower_pressure", "distributed_couple", "offset_load"}.intersection(blocked_operations)),
        "CONTACT_COUPLING_ACTIVITY_DELETION_DAMPING": bool(source_selection.get("scope", {}).get("ecosystem_mechanics_parity_authorized") is True),
        "PERFORMANCE": v5l.get("gate_status", {}).get("mixed_performance") == "PASS_MEASURED_REGISTERED_SCOPE",
        "TWO_COMPLETE_BYTE_IDENTICAL_CYCLES": bool(v5m.get("coverage", {}).get("cycles") == 2 and v5m.get("cycle_common", {}).get("sha256")),
    }
    required = list(plan["required_activation_gates"])
    if set(accepted) != set(required):
        raise V5NActivationAuditError("activation gate inventory mismatch")
    missing = sorted(name for name in required if not accepted[name])
    gates = {name: PASS if accepted[name] else MISSING for name in sorted(required)}
    terminal = UNCLASSIFIED if missing else GO
    return {
        "activation_authorized": False,
        "candidate_formulation_id": "CANDIDATE_E4_PL_S3_V2C_FLAT_LINEAR_PARITY_V1",
        "gate_status": gates,
        "missing_gate_ids": missing,
        "next_gate": plan["next_gate_on_missing_authority"] if missing else "V5N_FULL_ACTIVATION_EXECUTION",
        "production_boundary": plan["production_boundary"],
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "qualified_gate_count": len(required) - len(missing),
        "required_gate_count": len(required),
        "schema": "anysolver.e4-pl-s3-v5n-activation-audit-evidence-v1",
        "terminal": terminal,
    }


def synthesize() -> dict[str, Any]:
    plan, _contract = validate_authority()
    _supported, blocked = capability_sets()
    evidence = {}
    for name, filename in (
        ("v5e", "e4_pl_s3_v5e_stage4a_spatial_result.json"),
        ("v5h", "e4_pl_s3_v5h_local_parity_result.json"),
        ("v5l", "e4_pl_s3_v5l_stage4b_result.json"),
        ("v5m", "e4_pl_s3_v5m_parity_result.json"),
        ("source_selection", "e4_pl_s3_v5g_stage4b_extension_source_selection.json"),
    ):
        evidence[name] = load(REFERENCE / filename)[1]
    for filename in (
        "e4_pl_s3_v5e_stage4a_spatial_review.json",
        "e4_pl_s3_v5h_local_parity_review.json",
        "e4_pl_s3_v5l_stage4b_review.json",
        "e4_pl_s3_v5m_parity_review.json",
    ):
        if not _accepted_review(load(REFERENCE / filename)[1]):
            raise V5NActivationAuditError(f"accepted review has findings: {filename}")
    result = adjudicate(plan, evidence, blocked)
    result["blocked_operations"] = sorted(blocked)
    result["evidence_payload_sha256"] = sha256(canonical_bytes(result))
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    raw = canonical_bytes(synthesize())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
