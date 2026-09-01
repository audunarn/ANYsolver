"""Independent standard-library review of the frozen V5M protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "docs/reference_cases/e4_pl_s3_v5m_parity_plan.json"
CONTRACT = ROOT / "docs/reference_cases/e4_pl_s3_v5m_parity_contract.json"


class V5MProtocolReviewError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise V5MProtocolReviewError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=lambda token: (_ for _ in ()).throw(V5MProtocolReviewError(f"nonfinite token: {token}")))
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V5MProtocolReviewError(f"noncanonical JSON: {path}")
    return raw, value


def review() -> dict[str, Any]:
    plan_raw, plan = load(PLAN)
    contract_raw, contract = load(CONTRACT)
    if plan.get("schema") != "anysolver.e4-pl-s3-v5m-parity-plan-v1":
        raise V5MProtocolReviewError("unexpected plan schema")
    if contract.get("schema") != "anysolver.e4-pl-s3-v5m-parity-contract-v1":
        raise V5MProtocolReviewError("unexpected contract schema")
    bounds = plan.get("bounds", {})
    expected_workers = ["BATCH_4096", "SERIALIZATION_RESTART", "PACKAGE_WHEEL"]
    if bounds.get("worker_ids") != expected_workers or bounds.get("cycles") != 2:
        raise V5MProtocolReviewError("worker coverage changed")
    if bounds.get("child_timeout_seconds") != 600 or bounds.get("wave_timeout_seconds") != 1800:
        raise V5MProtocolReviewError("bounded execution changed")
    if plan.get("acceptance", {}).get("batch", {}).get("element_count") != 4096:
        raise V5MProtocolReviewError("batch coverage changed")
    boundary = plan.get("production_boundary", {})
    if boundary != contract.get("production_boundary") or boundary != {
        "activation_authorized": False,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
    }:
        raise V5MProtocolReviewError("production boundary changed")
    for row in contract.get("frozen_inputs", []):
        raw = (ROOT / row["path"]).read_bytes()
        if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest().upper() != row["sha256"]:
            raise V5MProtocolReviewError(f"frozen input mismatch: {row['path']}")
    return {
        "contract_sha256": hashlib.sha256(contract_raw).hexdigest().upper(),
        "findings": [],
        "plan_sha256": hashlib.sha256(plan_raw).hexdigest().upper(),
        "reviewer": "INDEPENDENT_STANDARD_LIBRARY_PROTOCOL_REVIEW",
        "schema": "anysolver.e4-pl-s3-v5m-protocol-review-v1",
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    raw = canonical_bytes(review())
    if args.output is None:
        print(raw.decode("ascii"), end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            stream.write(raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
