"""Standard-library-only review of the V5L Stage 4B successor protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
PLAN = REFERENCE / "e4_pl_s3_v5l_stage4b_plan.json"
CONTRACT = REFERENCE / "e4_pl_s3_v5l_stage4b_contract.json"


class ReviewError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise ReviewError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=lambda token: (_ for _ in ()).throw(ReviewError(f"nonfinite token: {token}")))
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise ReviewError(f"noncanonical JSON: {path}")
    return raw, value


def review() -> dict[str, Any]:
    plan_raw, plan = load(PLAN)
    _contract_raw, contract = load(CONTRACT)
    if plan.get("schema") != "anysolver.e4-pl-s3-v5l-stage4b-plan-v1" or contract.get("schema") != "anysolver.e4-pl-s3-v5l-stage4b-contract-v1":
        raise ReviewError("V5L schema changed")
    if plan["worker_ids"] != ["MODAL_10", "MODAL_25", "BUCKLING_10", "BUCKLING_25", "PERFORMANCE_0", "PERFORMANCE_10", "PERFORMANCE_25"]:
        raise ReviewError("V5L coverage changed")
    buckling = plan["lane"]["buckling"]
    if buckling["factor_acceptance_relative"] != "0.03" or buckling["factor_gate_count"] != 5 or buckling["guard_mode_count"] != 3 or buckling["subspace_mac_minimum"] != "0.95":
        raise ReviewError("V5K spectral authority changed")
    if plan["lane"]["performance"] != {"maximum_regression":"0.10","mixed_fractions_percent":[10,25],"repetitions":11,"routes":["assembly","production_end_to_end_solve","rss"],"warmups_per_route":1}:
        raise ReviewError("performance authority changed")
    for row in contract["frozen_inputs"]:
        raw = (ROOT / row["path"]).read_bytes()
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest().upper() != row["sha256"]:
            raise ReviewError(f"frozen input mismatch: {row['path']}")
    return {"conclusions":{"activation_authorized":False,"full_stage4b_successor_execution_authorized_after_implementation_review":True,"v5i_posthoc_reclassification_forbidden":True,"v5k_rule_preserved":True},"findings":{"P0":[],"P1":[]},"reviewed_inputs":{"plan_sha256":hashlib.sha256(plan_raw).hexdigest().upper(),"v5k_result_sha256":plan["predecessor"]["v5k_result_sha256"]},"schema":"anysolver.e4-pl-s3-v5l-protocol-review-v1","verdict":"ACCEPT_S3_V5L_PROTOCOL_NO_P0_P1"}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-v5l-protocol", action="store_true", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(canonical_bytes(review()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
