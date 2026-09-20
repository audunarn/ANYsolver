"""Adjudicate the registered combined follower/S3 optimization gate.

This script never executes or retries a solve.  It consumes an immutable raw
campaign by exact SHA-256 and applies only the criteria registered in the
combined gate before the S3 product edit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import time
from pathlib import Path
from typing import Any, Mapping


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_identity(
    raw: Mapping[str, Any], manifest: Mapping[str, Any]
) -> None:
    identity = raw["identity"]
    expected = {
        "candidate_revision": manifest["candidate_revision"],
        "candidate_tree": manifest["source_trees"]["candidate"],
        "candidate_wheel_sha256": manifest["wheel_sha256"]["candidate"],
        "baseline_revision": manifest["baseline_revision"],
        "baseline_tree": manifest["source_trees"]["baseline"],
        "baseline_wheel_sha256": manifest["wheel_sha256"]["baseline"],
    }
    mismatches = {
        key: {"expected": value, "observed": identity.get(key)}
        for key, value in expected.items()
        if identity.get(key) != value
    }
    if mismatches:
        raise ValueError("campaign identity mismatch: " + json.dumps(mismatches, sort_keys=True))


def _exact_follower_compatibility(pair: Mapping[str, Any]) -> bool:
    comparison = pair["physical_comparison"]
    baseline_checks = pair["baseline"]["physical"]["family_checks"]
    candidate_checks = pair["candidate"]["physical"]["family_checks"]
    if baseline_checks.get("current_external_load") is not False:
        return False
    if candidate_checks.get("current_external_load") is not True:
        return False
    if not all(
        value
        for key, value in baseline_checks.items()
        if key != "current_external_load"
    ):
        return False
    if not all(candidate_checks.values()):
        return False
    zero_fields = (
        "max_displacement_difference",
        "max_reaction_difference",
        "max_plastic_state_difference",
        "max_step_load_factor_difference",
        "max_step_displacement_norm_difference",
        "max_step_plastic_strain_difference",
        "max_state_observable_difference",
        "max_snapshot_displacement_difference",
        "max_snapshot_state_difference",
    )
    inventory_fields = (
        "same_reaction_inventory",
        "same_step_path",
        "same_state_inventory",
        "same_snapshot_path",
        "same_snapshot_state_inventory",
    )
    return all(float(comparison[field]) == 0.0 for field in zero_fields) and all(
        bool(comparison[field]) for field in inventory_fields
    )


def _pair_status(pair: Mapping[str, Any], *, allow_follower_gap: bool) -> dict[str, Any]:
    baseline = pair["baseline"]
    candidate = pair["candidate"]
    comparison = pair["physical_comparison"]
    complete = (
        bool(baseline.get("ok"))
        and bool(candidate.get("ok"))
        and baseline.get("status") == "completed"
        and candidate.get("status") == "completed"
    )
    physical = bool(comparison.get("numerical_match"))
    compatibility_applied = False
    if not physical and allow_follower_gap and _exact_follower_compatibility(pair):
        physical = True
        compatibility_applied = True
    work = baseline.get("work") == candidate.get("work")
    return {
        "pair": int(pair["pair"]),
        "complete": complete,
        "physical_match": physical,
        "exact_work_match": work,
        "legacy_follower_diagnostic_compatibility": compatibility_applied,
        "baseline_seconds": baseline.get("complete_route_wall_seconds"),
        "candidate_seconds": candidate.get("complete_route_wall_seconds"),
    }


def adjudicate(
    raw: Mapping[str, Any], gate: Mapping[str, Any], manifest: Mapping[str, Any], phase: str
) -> dict[str, Any]:
    if phase not in {"component", "formal"}:
        raise ValueError(f"unknown phase: {phase}")
    _require_identity(raw, manifest)
    criteria = gate["component_screen" if phase == "component" else "formal_gate"]
    expected_pairs = int(criteria["performance_pairs"])
    expected_cases = (
        [str(criteria["case_id"])]
        if phase == "component"
        else [str(value) for value in criteria["performance_case_ids"]]
    )
    missing = [case_id for case_id in expected_cases if case_id not in raw["performance"]]
    if missing:
        raise ValueError(f"missing registered cases: {missing}")

    cases: dict[str, Any] = {}
    reductions: dict[str, float] = {}
    for case_id in expected_cases:
        case = raw["performance"][case_id]
        pairs = [
            _pair_status(
                pair,
                allow_follower_gap=(
                    phase == "formal"
                    and case_id == "nonsymmetric_follower_shell_holdout"
                ),
            )
            for pair in case["pairs"]
        ]
        summary = case.get("summary")
        reduction = (
            float(summary["median_reduction_fraction"])
            if summary is not None
            else float("nan")
        )
        reductions[case_id] = reduction
        cases[case_id] = {
            "pair_count": len(pairs),
            "expected_pair_count": expected_pairs,
            "pairs": pairs,
            "baseline_median_seconds": None if summary is None else summary["baseline_median_seconds"],
            "candidate_median_seconds": None if summary is None else summary["candidate_median_seconds"],
            "median_reduction_fraction": reduction,
            "complete": len(pairs) == expected_pairs and all(item["complete"] for item in pairs),
            "physical_match": all(item["physical_match"] for item in pairs),
            "exact_work_match": all(item["exact_work_match"] for item in pairs),
        }

    regressions = raw.get("installed_regressions", {})
    common_pass = (
        bool(regressions.get("ok"))
        and not raw.get("failures")
        and all(
            item["complete"] and item["physical_match"] and item["exact_work_match"]
            for item in cases.values()
        )
    )
    decision: dict[str, Any]
    if phase == "component":
        case_id = expected_cases[0]
        threshold = float(criteria["minimum_route_reduction_fraction"])
        performance_pass = reductions[case_id] >= threshold
        decision = {
            "completeness": "PASS" if common_pass else "FAIL",
            "performance": "GO" if performance_pass else "NO-GO",
            "advance": bool(common_pass and performance_pass),
            "plastic_s3_reduction_fraction": reductions[case_id],
            "minimum_plastic_s3_reduction_fraction": threshold,
        }
    else:
        easy = "easy_elastic_shell_control"
        nonlinear = [case_id for case_id in expected_cases if case_id != easy]
        representative = float(statistics.median(reductions[case_id] for case_id in nonlinear))
        min_case = min(reductions.values())
        performance_pass = (
            representative >= float(criteria["minimum_representative_reduction_fraction"])
            and reductions["plastic_s3_reversal_holdout"]
            >= float(criteria["minimum_plastic_s3_reduction_fraction"])
            and reductions["nonsymmetric_follower_shell_holdout"]
            >= float(criteria["minimum_follower_target_reduction_fraction"])
            and min_case >= -float(criteria["maximum_case_regression_fraction"])
        )
        decision = {
            "completeness": "PASS" if common_pass else "FAIL",
            "performance": "GO" if performance_pass else "NO-GO",
            "promote": bool(common_pass and performance_pass),
            "representative_nonlinear_median_reduction_fraction": representative,
            "plastic_s3_reduction_fraction": reductions["plastic_s3_reversal_holdout"],
            "follower_target_reduction_fraction": reductions[
                "nonsymmetric_follower_shell_holdout"
            ],
            "minimum_case_reduction_fraction": min_case,
        }
    return {
        "schema": "anysolver.nonlinear_static.combined_s3_adjudication",
        "version": 1,
        "phase": phase,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "installed_regressions": regressions,
        "cases": cases,
        "decision": decision,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gate", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--raw-sha256", required=True)
    parser.add_argument("--phase", choices=("component", "formal"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    observed = _sha256(args.raw)
    if observed.lower() != args.raw_sha256.lower():
        raise SystemExit(
            f"raw campaign SHA-256 mismatch: expected {args.raw_sha256}, observed {observed}"
        )
    gate = json.loads(args.gate.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    result = adjudicate(raw, gate, manifest, args.phase)
    result["source"] = {
        "gate": str(args.gate.resolve()),
        "gate_sha256": _sha256(args.gate),
        "manifest": str(args.manifest.resolve()),
        "manifest_sha256": _sha256(args.manifest),
        "raw": str(args.raw.resolve()),
        "raw_sha256": observed,
        "adjudicator": str(Path(__file__).resolve()),
        "adjudicator_sha256": _sha256(Path(__file__).resolve()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=False)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["decision"], sort_keys=True))
    terminal_key = "advance" if args.phase == "component" else "promote"
    return 0 if result["decision"][terminal_key] else 1


if __name__ == "__main__":
    raise SystemExit(main())
