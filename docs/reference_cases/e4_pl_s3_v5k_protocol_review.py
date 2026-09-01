"""Standard-library-only review of the frozen V5K successor protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
PLAN = REFERENCE / "e4_pl_s3_v5k_repair_plan.json"
CONTRACT = REFERENCE / "e4_pl_s3_v5k_repair_contract.json"


class ProtocolReviewError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise ProtocolReviewError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=lambda token: (_ for _ in ()).throw(ProtocolReviewError(f"nonfinite JSON token: {token}")))
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise ProtocolReviewError(f"noncanonical JSON: {path}")
    return raw, value


def review() -> dict[str, Any]:
    plan_raw, plan = load(PLAN)
    _contract_raw, contract = load(CONTRACT)
    if plan.get("schema") != "anysolver.e4-pl-s3-v5k-repair-plan-v1" or contract.get("schema") != "anysolver.e4-pl-s3-v5k-repair-contract-v1":
        raise ProtocolReviewError("unexpected V5K schema")
    spectral = plan.get("spectral_rule", {})
    if spectral != {
        "cluster_construction": "TRANSITIVE_ADJACENT_OVERLAP_IN_BOTH_REFERENCE_AND_CANDIDATE_ACCEPTANCE_INTERVALS",
        "factor_acceptance_relative": "0.03",
        "factor_gate_count": 5,
        "guard_mode_count": 3,
        "individual_or_subspace_mac_minimum": "0.95",
        "interval_definition": "[lambda*(1-factor_acceptance_relative),lambda*(1+factor_acceptance_relative)]",
        "subspace_metric": "MINIMUM_SQUARED_SINGULAR_VALUE_OF_ORTHONORMAL_CROSS_GRAM",
        "window_mode_count": 8,
    }:
        raise ProtocolReviewError("spectral successor rule changed")
    if plan["predecessor"]["stage4b_terminal_preserved"] != "NO_GO_E4_PL_S3_V5I_MIXED_EIGEN":
        raise ProtocolReviewError("V5I terminal was not preserved")
    if plan["fast_assembly"]["q4_route_unchanged"] is not True or plan["fast_assembly"]["exact_csr_byte_equality"] is not True:
        raise ProtocolReviewError("fast-assembly identity boundary changed")
    for row in contract.get("frozen_inputs", []):
        path = ROOT / row["path"]
        raw = path.read_bytes()
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest().upper() != row["sha256"]:
            raise ProtocolReviewError(f"frozen input mismatch: {row['path']}")
    return {
        "conclusions": {"mechanics_change_authorized": False, "posthoc_v5i_reclassification_forbidden": True, "v2c_exact_cache_route_authorized": True, "v5k_bounded_execution_authorized_after_implementation_review": True},
        "findings": {"P0": [], "P1": []},
        "reviewed_inputs": {"plan_sha256": hashlib.sha256(plan_raw).hexdigest().upper(), "r1_result_sha256": contract["frozen_inputs"][0]["sha256"]},
        "schema": "anysolver.e4-pl-s3-v5k-protocol-review-v1",
        "verdict": "ACCEPT_S3_V5K_PROTOCOL_NO_P0_P1",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-v5k-protocol", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(canonical_bytes(review()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
