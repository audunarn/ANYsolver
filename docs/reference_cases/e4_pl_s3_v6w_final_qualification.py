"""Compose the final opt-in S3 V2D qualification evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v6w_final_qualification_contract.json"
GO = "PROVISIONAL_GO_E4_PL_S3_V2D_OPT_IN_QUALIFIED"
NO_GO = "NO_GO_E4_PL_S3_V6W_QUALIFICATION"
BLOCKED = "BLOCKED_E4_PL_S3_V6W_EVIDENCE_OR_REVIEW"
PASS = "PASS_BOUND_REGISTERED_SCOPE"


class V6WError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("ascii")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise V6WError(f"duplicate key: {key}")
        value[key] = item
    return value


def load(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(
            V6WError(f"nonfinite token: {token}")
        ),
    )
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V6WError(f"noncanonical JSON: {path}")
    return raw, value


def _git(*arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode:
        raise V6WError(process.stderr.strip() or "git command failed")
    return process.stdout.strip()


def validate_contract() -> tuple[bytes, dict[str, Any]]:
    raw, value = load(CONTRACT)
    if value.get("schema") != "anysolver.e4-pl-s3-v6w-final-qualification-contract-v1":
        raise V6WError("V6W contract schema differs")
    if value.get("execution") != {
        "mechanics_execution": False,
        "required_synthesis_count": 2,
        "standard_library_only": True,
    }:
        raise V6WError("V6W execution contract differs")
    for row in value.get("frozen_inputs", []):
        candidate = (ROOT / row["path"]).read_bytes()
        if len(candidate) != row["bytes"] or sha256(candidate) != row["sha256"]:
            raise V6WError(f"frozen input differs: {row['path']}")
    return raw, value


def validate_authorization(path: Path, contract_raw: bytes) -> None:
    _raw, value = load(path)
    if value.get("schema") != "anysolver.e4-pl-s3-v6w-execution-authorization-v1":
        raise V6WError("V6W authorization schema differs")
    if value.get("qualification_execution_authorized") is not True:
        raise V6WError("V6W qualification execution is not authorized")
    if value.get("default_activation_authorized") is not False:
        raise V6WError("V6W cannot activate S3 defaults")
    if value.get("contract_sha256") != sha256(contract_raw):
        raise V6WError("V6W authorization contract differs")
    if _git("rev-parse", "HEAD^") != value.get("authority_commit"):
        raise V6WError("V6W authorization topology differs")
    if _git("show", "-s", "--format=%s", "HEAD") != value.get(
        "expected_authorization_subject"
    ):
        raise V6WError("V6W authorization subject differs")
    if _git("status", "--porcelain"):
        raise V6WError("V6W frozen worktree is dirty")


def _all_true(value: Any) -> bool:
    return isinstance(value, dict) and bool(value) and all(item is True for item in value.values())


def adjudicate(contract: dict[str, Any]) -> dict[str, Any]:
    documents = {
        role: load(ROOT / path)[1]
        for role, path in contract["evidence_paths"].items()
    }
    v6c = documents["v6c_restart"]
    v6d = documents["v6d_batch"]
    v6e = documents["v6e_dynamics"]
    v6g = documents["v6g_recovery"]
    v6p = documents["v6p_historical_nogo"]
    v6q = documents["v6q_historical_block"]
    v6r = documents["v6r_spatial_successor"]
    v6s = documents["v6s_historical_nogo"]
    v6t = documents["v6t_cache_successor"]
    v6u = documents["v6u_stage4b"]
    v6v = documents["v6v_package"]

    checks = {
        "local_and_recovery_parity": (
            _all_true(v6g.get("checks"))
            and v6g.get("cycles", {}).get("canonical_readiness_outputs_byte_identical")
            is True
        ),
        "modal_buckling_and_dynamics": (
            _all_true(v6e.get("checks"))
            and v6u.get("gate_status", {}).get("modal")
            == "PASS_MEASURED_REGISTERED_SCOPE"
            and v6u.get("gate_status", {}).get("buckling")
            == "PASS_MEASURED_REGISTERED_SCOPE"
        ),
        "mixed_spatial_successor": (
            v6r.get("formal_failure_count") == 0
            and v6r.get("cycle_count") == 2
            and v6r.get("replicas_byte_identical") is True
            and v6r.get("mechanics_executed") is False
        ),
        "performance_successor": (
            v6t.get("implementation", {}).get("mechanics_changed") is False
            and v6u.get("cycles", {}).get("count") == 2
            and v6u.get("cycles", {}).get("common_byte_identical") is True
            and v6u.get("cycles", {}).get("proofs_byte_identical_by_worker") is True
            and all(
                value == "PASS_MEASURED_REGISTERED_SCOPE"
                for value in v6u.get("gate_status", {}).values()
            )
        ),
        "restart_migration_and_batching": (
            _all_true(v6c.get("checks"))
            and _all_true(v6d.get("checks"))
            and v6c.get("solver_integrated_hot_restart_authorized") is True
        ),
        "isolated_package_and_provenance": (
            isinstance(v6v.get("checks"), dict)
            and v6v["checks"].get("focused_test_count") == 42
            and all(
                value is True
                for key, value in v6v["checks"].items()
                if key != "focused_test_count"
            )
            and v6v.get("package", {}).get("anysolver", {}).get(
                "import_from_isolated_target"
            )
            is True
            and v6v.get("package", {}).get("anysolver", {}).get("round_trip_exact")
            is True
        ),
        "historical_incidents_preserved": (
            v6p.get("terminal")
            == "NO_GO_E4_PL_S3_V2D_STAGE4A_MIXED_FLEXURAL_CONVERGENCE"
            and bool(v6p.get("formal_failures"))
            and v6q.get("terminal") == "BLOCKED_E4_PL_S3_V6Q_PROCESS_OR_EVIDENCE"
            and v6s.get("terminal") == "NO_GO_E4_PL_S3_V6S_MIXED_PERFORMANCE"
            and v6v.get("predecessor_incidents", {}).get("v6p_reclassified")
            is False
            and v6v.get("predecessor_incidents", {}).get("v6q_reclassified")
            is False
        ),
    }
    source = (ROOT / "src/anysolver/elements.py").read_text(encoding="utf-8")
    checks["production_boundary"] = (
        'DEFAULT_Q4_FORMULATION = "e4-pl"' in source
        and 'DEFAULT_S3_FORMULATION = "legacy-s3"' in source
        and v6v.get("production_boundary", {}).get("anymesh_untouched") is True
        and v6v.get("activation_authorized") is False
    )
    passed = all(checks.values())
    bindings = [
        {"path": row["path"], "sha256": row["sha256"]}
        for row in contract["frozen_inputs"]
    ]
    return {
        "candidate_formulation_id": "CANDIDATE_E4_PL_S3_V2D_NATIVE_PARITY_V1",
        "checks": checks,
        "default_activation_authorized": False,
        "evidence_binding_sha256": sha256(canonical_bytes(bindings)),
        "historical_disposition": {
            "v6p_nogo_preserved": True,
            "v6q_block_preserved": True,
            "v6r_spatial_successor_accepted": True,
            "v6s_nogo_preserved": True,
            "v6t_v6u_performance_successor_accepted": True,
            "v6v_block_preserved": True,
        },
        "next_gate": "S3_V2D_ECOSYSTEM_DEFAULT_ACTIVATION_CANDIDATE" if passed else None,
        "production_boundary": {
            "anymesh_untouched": True,
            "default_q4_formulation": "e4-pl",
            "default_s3_formulation": "legacy-s3",
            "q4_mechanics_unchanged": True,
        },
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "qualified_selector": "e4-pl-s3-v2d" if passed else None,
        "schema": "anysolver.e4-pl-s3-v6w-final-qualification-evidence-v1",
        "terminal": GO if passed else NO_GO,
    }


def run(authorization: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise V6WError("exclusive V6W output exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        contract_raw, contract = validate_contract()
        validate_authorization(authorization, contract_raw)
        result = adjudicate(contract)
    except Exception as exc:
        result = {
            "candidate_formulation_id": "CANDIDATE_E4_PL_S3_V2D_NATIVE_PARITY_V1",
            "default_activation_authorized": False,
            "error": f"{type(exc).__name__}: {exc}",
            "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
            "schema": "anysolver.e4-pl-s3-v6w-final-qualification-evidence-v1",
            "terminal": BLOCKED,
        }
    with output.open("xb") as stream:
        stream.write(canonical_bytes(result))
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthesize", action="store_true", required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run(args.authorization, args.output)
    print(canonical_bytes(result).decode("ascii"), end="")
    return 0 if result["terminal"] != BLOCKED else 2


if __name__ == "__main__":
    raise SystemExit(main())
