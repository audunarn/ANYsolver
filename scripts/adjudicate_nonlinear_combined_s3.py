"""Adjudicate the registered combined follower/S3 optimization gate.

This script never executes or retries a solve.  It consumes an immutable raw
campaign by exact SHA-256 and applies only the criteria registered in the
combined gate before the S3 product edit.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import statistics
import time
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts/qualify_nonlinear_representative.py"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_runner(expected_sha256: str):
    observed = _sha256(RUNNER)
    if observed.lower() != expected_sha256.lower():
        raise RuntimeError(
            "campaign runner SHA-256 mismatch: "
            f"expected {expected_sha256}, observed {observed}"
        )
    spec = importlib.util.spec_from_file_location("combined_s3_runner", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {RUNNER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _require_identity(
    raw: Mapping[str, Any],
    manifest: Mapping[str, Any],
    *,
    manifest_sha256: str,
    runner_sha256: str,
) -> None:
    identity = raw["identity"]
    expected = {
        "candidate_revision": manifest["candidate_revision"],
        "candidate_tree": manifest["source_trees"]["candidate"],
        "candidate_wheel_sha256": manifest["wheel_sha256"]["candidate"],
        "baseline_revision": manifest["baseline_revision"],
        "baseline_tree": manifest["source_trees"]["baseline"],
        "baseline_wheel_sha256": manifest["wheel_sha256"]["baseline"],
        "manifest_sha256": manifest_sha256,
        "runner_sha256": runner_sha256,
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


def _pair_status(
    pair: Mapping[str, Any],
    *,
    allow_follower_gap: bool,
    compare_physics: Any | None,
) -> dict[str, Any]:
    baseline = pair["baseline"]
    candidate = pair["candidate"]
    comparison = pair["physical_comparison"]
    if compare_physics is not None:
        recomputed = compare_physics(baseline, candidate)
        if comparison != recomputed:
            raise ValueError("stored physical comparison differs from raw samples")
        comparison = recomputed
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


def _require_sample_integrity(
    sample: Mapping[str, Any],
    *,
    expected_site: str,
    timing_repetitions: int,
) -> None:
    if sample.get("physical_sha256") != _json_digest(sample.get("physical")):
        raise ValueError("sample physical digest mismatch")
    identity = sample.get("identity", {})
    module_path = Path(str(identity.get("anysolver_module", ""))).resolve()
    if not module_path.is_relative_to(Path(expected_site).resolve()):
        raise ValueError("sample did not import anysolver from its frozen site")
    timing = sample.get("timing_repetitions", {})
    route_seconds = [float(value) for value in timing.get("route_seconds", [])]
    solver_seconds = [float(value) for value in timing.get("solver_seconds", [])]
    if (
        timing.get("count") != timing_repetitions
        or timing.get("aggregation") != "median"
        or len(route_seconds) != timing_repetitions
        or len(solver_seconds) != timing_repetitions
        or timing.get("physical_sha256") != sample.get("physical_sha256")
        or timing.get("work_sha256") != _json_digest(sample.get("work"))
        or timing.get("physical_match") is not True
        or timing.get("work_match") is not True
        or float(sample["complete_route_wall_seconds"])
        != float(statistics.median(route_seconds))
        or float(sample["solver_seconds"])
        != float(statistics.median(solver_seconds))
    ):
        raise ValueError("sample timing-repetition inventory or digest mismatch")


def adjudicate(
    raw: Mapping[str, Any],
    gate: Mapping[str, Any],
    manifest: Mapping[str, Any],
    phase: str,
    *,
    manifest_sha256: str,
    runner_sha256: str,
    compare_physics: Any | None = None,
) -> dict[str, Any]:
    if phase not in {"component", "formal"}:
        raise ValueError(f"unknown phase: {phase}")
    _require_identity(
        raw,
        manifest,
        manifest_sha256=manifest_sha256,
        runner_sha256=runner_sha256,
    )
    if raw.get("resource_limits") != manifest.get("resource_limits"):
        raise ValueError("campaign resource limits do not match the manifest")
    if raw["identity"].get("thread_environment") != gate["environment"][
        "thread_environment"
    ]:
        raise ValueError("campaign thread environment does not match the gate")
    if int(manifest["execution"]["numerical_threads"]) != 1:
        raise ValueError("manifest no longer requires one numerical thread")
    if raw.get("convergence"):
        raise ValueError("combined candidate must not execute the closed Armijo campaign")
    criteria = gate["component_screen" if phase == "component" else "formal_gate"]
    expected_pairs = int(criteria["performance_pairs"])
    expected_cases = (
        [str(criteria["case_id"])]
        if phase == "component"
        else [str(value) for value in criteria["performance_case_ids"]]
    )
    if int(manifest["execution"]["performance_pairs"]) != expected_pairs:
        raise ValueError("manifest pair count differs from the registered gate")
    if (
        manifest["execution"].get("serial") is not True
        or manifest["execution"].get("alternating_order") is not True
        or int(manifest["execution"].get("warmups_per_sample", 0)) != 1
    ):
        raise ValueError("manifest execution policy differs from the registered gate")
    expected_mode = "component_screen" if phase == "component" else "representative"
    if manifest.get("execution_mode", "representative") != expected_mode:
        raise ValueError("manifest execution mode differs from the adjudication phase")
    manifest_specs = {
        str(spec["id"]): spec for spec in manifest["performance_cases"]
    }
    if list(manifest_specs) != expected_cases:
        raise ValueError("manifest case inventory or order differs from the registered gate")
    if list(raw["performance"]) != list(manifest_specs):
        raise ValueError("raw performance case inventory or order differs from manifest")
    missing = [case_id for case_id in expected_cases if case_id not in manifest_specs]
    if missing:
        raise ValueError(f"manifest is missing registered cases: {missing}")

    cases: dict[str, Any] = {}
    reductions: dict[str, float] = {}
    for case_id in expected_cases:
        case = raw["performance"][case_id]
        if case.get("spec") != manifest_specs[case_id]:
            raise ValueError(f"raw case specification differs for {case_id}")
        expected_pair_ids = list(range(1, expected_pairs + 1))
        observed_pair_ids = [int(pair["pair"]) for pair in case["pairs"]]
        if observed_pair_ids != expected_pair_ids:
            raise ValueError(f"pair inventory or order differs for {case_id}")
        for pair in case["pairs"]:
            expected_order = (
                ["baseline", "candidate"]
                if int(pair["pair"]) % 2 == 1
                else ["candidate", "baseline"]
            )
            if pair.get("order") != expected_order:
                raise ValueError(f"alternating order differs for {case_id}")
            timing_repetitions = int(manifest_specs[case_id].get("timing_repetitions", 1))
            for label in ("baseline", "candidate"):
                _require_sample_integrity(
                    pair[label],
                    expected_site=raw["identity"]["installed_sites"][label]["site"],
                    timing_repetitions=timing_repetitions,
                )
            if pair["baseline"].get("dispatch") != pair["candidate"].get("dispatch"):
                raise ValueError(f"performance dispatch differs for {case_id}")
        pairs = [
            _pair_status(
                pair,
                allow_follower_gap=(
                    phase == "formal"
                    and case_id == "nonsymmetric_follower_shell_holdout"
                ),
                compare_physics=compare_physics,
            )
            for pair in case["pairs"]
        ]
        if all(item["complete"] for item in pairs):
            baseline_median = float(
                statistics.median(item["baseline_seconds"] for item in pairs)
            )
            candidate_median = float(
                statistics.median(item["candidate_seconds"] for item in pairs)
            )
            reduction = (baseline_median - candidate_median) / baseline_median
            expected_summary = {
                "baseline_median_seconds": baseline_median,
                "candidate_median_seconds": candidate_median,
                "median_reduction_fraction": reduction,
            }
            summary = case.get("summary") or {}
            if any(
                float(summary.get(key, float("nan"))) != value
                for key, value in expected_summary.items()
            ):
                raise ValueError(f"runner summary differs from raw pairs for {case_id}")
        else:
            baseline_median = None
            candidate_median = None
            reduction = float("nan")
        reductions[case_id] = reduction
        cases[case_id] = {
            "pair_count": len(pairs),
            "expected_pair_count": expected_pairs,
            "pairs": pairs,
            "baseline_median_seconds": baseline_median,
            "candidate_median_seconds": candidate_median,
            "median_reduction_fraction": reduction,
            "complete": len(pairs) == expected_pairs and all(item["complete"] for item in pairs),
            "physical_match": all(item["physical_match"] for item in pairs),
            "exact_work_match": all(item["exact_work_match"] for item in pairs),
        }

    regressions = raw.get("installed_regressions", {})
    if regressions.get("tests") != manifest["required_regressions"]:
        raise ValueError("installed regression inventory or order differs from manifest")
    candidate_site = raw["identity"]["installed_sites"]["candidate"]["site"]
    if regressions.get("installed_site") != candidate_site:
        raise ValueError("installed regressions did not use the candidate site")
    common_pass = (
        bool(regressions.get("ok"))
        and regressions.get("exit_code") == 0
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
        "version": 2,
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
    parser.add_argument("--correction", type=Path, required=True)
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
    correction = json.loads(args.correction.read_text(encoding="utf-8"))
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    manifest_sha256 = _sha256(args.manifest)
    runner_sha256 = str(correction["correction"]["new_runner_execution_sha256"])
    runner = _load_runner(runner_sha256)
    result = adjudicate(
        raw,
        gate,
        manifest,
        args.phase,
        manifest_sha256=manifest_sha256,
        runner_sha256=runner_sha256,
        compare_physics=runner._compare_physics,
    )
    result["source"] = {
        "gate": str(args.gate.resolve()),
        "gate_sha256": _sha256(args.gate),
        "manifest": str(args.manifest.resolve()),
        "manifest_sha256": _sha256(args.manifest),
        "correction": str(args.correction.resolve()),
        "correction_sha256": _sha256(args.correction),
        "raw": str(args.raw.resolve()),
        "raw_sha256": observed,
        "adjudicator": str(Path(__file__).resolve()),
        "adjudicator_sha256": _sha256(Path(__file__).resolve()),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["decision"], sort_keys=True))
    terminal_key = "advance" if args.phase == "component" else "promote"
    return 0 if result["decision"][terminal_key] else 1


if __name__ == "__main__":
    raise SystemExit(main())
