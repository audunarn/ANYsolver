"""Standard-library validator for the S3 V3 preregistration gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SELECTION = ROOT / "docs/reference_cases/e4_pl_s3_v3_source_selection.json"
CONTRACT = ROOT / "docs/reference_cases/e4_pl_s3_v3_screening_contract.json"


def _reject_constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON constant: {value}")


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_canonical(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_object,
        parse_constant=_reject_constant,
    )
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON object required: {path}")
    if canonical_bytes(value) != raw:
        raise ValueError(f"noncanonical JSON: {path}")
    return value


def canonical_bytes(value: Any) -> bytes:
    def walk(item: Any) -> None:
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("nonfinite value")
        if isinstance(item, dict):
            for child in item.values():
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(value)
    return (
        json.dumps(value, allow_nan=False, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def validate() -> dict[str, Any]:
    selection = load_canonical(SELECTION)
    contract = load_canonical(CONTRACT)
    if selection.get("schema") != "anysolver.e4-pl-s3-v3-source-selection-v1":
        raise ValueError("source-selection schema mismatch")
    if contract.get("schema") != "anysolver.e4-pl-s3-v3-screening-contract-v1":
        raise ValueError("screening-contract schema mismatch")
    candidate = selection.get("candidate", {})
    if candidate.get("formulation_id") != "CANDIDATE_E4_PL_S3_V3A_MISP3_HR_FLAT_LINEAR_V1":
        raise ValueError("candidate identity mismatch")
    if candidate.get("implementation_status") != "NOT_IMPLEMENTED":
        raise ValueError("preregistration cannot bind implemented mechanics")
    if selection.get("stage") != "SOURCE_SELECTED_EQUATION_MAP_NOT_YET_AUTHORIZED":
        raise ValueError("source-selection stage mismatch")
    primary = selection.get("primary_source", {})
    if primary.get("version") != "ARXIV_1410_3683_V1":
        raise ValueError("versioned primary source required")
    if len(primary.get("sha256", "")) != 64 or primary.get("bytes", 0) <= 0:
        raise ValueError("primary source byte binding incomplete")
    comparators = selection.get("comparators", [])
    if len(comparators) != 1 or comparators[0].get("disposition") != "DIAGNOSTIC_ONLY_NOT_IMPLEMENTATION_AUTHORITY":
        raise ValueError("comparator disposition mismatch")
    expected_predecessors = {
        "NO_GO_E4_PL_S3_V1_QUALIFICATION",
        "NO_GO_E4_PL_S3_V2A_MIXED_FLEXURAL_CONVERGENCE",
        "UNCLASSIFIED_E4_PL_S3_V2B_FORMULATION_REPLACEMENT_REQUIRED",
    }
    actual_predecessors = {row.get("terminal") for row in selection.get("predecessors", [])}
    if actual_predecessors != expected_predecessors:
        raise ValueError("predecessor terminal set mismatch")
    execution = contract.get("execution", {})
    required_bounds = {
        "child_wall_seconds": 600,
        "complete_wave_wall_seconds": 1800,
        "maximum_concurrent_workers": 3,
        "memory_limit_gib_per_process_tree": 24,
        "numerical_library_threads_per_worker": 1,
        "required_cycle_count": 2,
    }
    for key, expected in required_bounds.items():
        if execution.get(key) != expected:
            raise ValueError(f"execution bound mismatch: {key}")
    if execution.get("no_automatic_retry") is not True:
        raise ValueError("automatic retry must be forbidden")
    production = contract.get("production_boundary", {})
    if production != {
        "anymesh_untouched": True,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
        "s3_activation_authorized": False,
    }:
        raise ValueError("production boundary mismatch")
    if contract.get("stage4a_rerun_authorized") is not False:
        raise ValueError("Stage 4A must remain unauthorized")
    for binding in contract.get("frozen_inputs", []):
        path = ROOT / binding["path"]
        if not path.is_file():
            raise ValueError(f"missing frozen input: {path}")
        if path.stat().st_size != binding["bytes"] or sha256(path) != binding["sha256"]:
            raise ValueError(f"frozen input mismatch: {path}")
    result = {
        "candidate_id": candidate["formulation_id"],
        "default_activation_authorized": False,
        "equation_map_required_before_mechanics": True,
        "primary_source_sha256": primary["sha256"],
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": "anysolver.e4-pl-s3-v3-preregistration-validation-v1",
        "stage4a_rerun_authorized": False,
        "terminal": "PROVISIONAL_GO_E4_PL_S3_V3A_BOUNDED_IMPLEMENTATION_SCREEN",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = canonical_bytes(validate())
    if args.output is None:
        os.write(1, payload)
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
