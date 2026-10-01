"""Adjudicate the registered non-follower implementation screen."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def adjudicate(
    *,
    evidence_path: Path,
    manifest_path: Path,
    expected_evidence_sha256: str,
) -> dict[str, Any]:
    observed_evidence_sha256 = _sha256(evidence_path)
    if observed_evidence_sha256.lower() != expected_evidence_sha256.lower():
        raise ValueError(
            "non-follower screen evidence SHA-256 mismatch: "
            f"expected {expected_evidence_sha256}, observed "
            f"{observed_evidence_sha256}"
        )

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    identity = evidence["identity"]
    expected_identity = {
        "baseline_revision": manifest["baseline_revision"],
        "candidate_revision": manifest["candidate_revision"],
        "manifest_sha256": _sha256(manifest_path),
    }
    identity_mismatches = {
        key: {"expected": value, "observed": identity.get(key)}
        for key, value in expected_identity.items()
        if identity.get(key) != value
    }
    if identity_mismatches:
        raise ValueError(
            "non-follower screen evidence identity mismatch: "
            + json.dumps(identity_mismatches, sort_keys=True)
        )

    performance: Mapping[str, Mapping[str, Any]] = evidence["performance"]
    expected_cases = [
        str(spec["id"]) for spec in manifest["performance_cases"]
    ]
    if list(performance) != expected_cases:
        raise ValueError(
            "non-follower screen case inventory mismatch: "
            f"expected {expected_cases}, observed {list(performance)}"
        )

    acceptance = manifest["screen_acceptance"]
    case_threshold = float(acceptance["case_reduction_fraction"])
    minimum_case_count = int(acceptance["minimum_improved_case_count"])
    aggregate_threshold = float(acceptance["aggregate_reduction_fraction"])
    maximum_regression = float(acceptance["maximum_case_regression_fraction"])

    reductions = {
        case_id: float(case["summary"]["median_reduction_fraction"])
        for case_id, case in performance.items()
    }
    improved_cases = [
        case_id
        for case_id, reduction in reductions.items()
        if reduction >= case_threshold
    ]
    regression_failures = {
        case_id: reduction
        for case_id, reduction in reductions.items()
        if reduction < -maximum_regression
    }
    baseline_aggregate = sum(
        float(case["summary"]["baseline_median_seconds"])
        for case in performance.values()
    )
    candidate_aggregate = sum(
        float(case["summary"]["candidate_median_seconds"])
        for case in performance.values()
    )
    aggregate_reduction = (
        (baseline_aggregate - candidate_aggregate) / baseline_aggregate
        if baseline_aggregate > 0.0
        else float("-inf")
    )

    work_mismatches: list[dict[str, Any]] = []
    for case_id, case in performance.items():
        for pair in case["pairs"]:
            if pair["baseline"].get("work") != pair["candidate"].get("work"):
                work_mismatches.append(
                    {
                        "case": case_id,
                        "pair": int(pair["pair"]),
                        "baseline": pair["baseline"].get("work"),
                        "candidate": pair["candidate"].get("work"),
                    }
                )

    complete = bool(
        evidence["decision"]["completeness"] == "PASS"
        and not evidence.get("failures")
        and evidence.get("installed_regressions", {}).get("ok") is True
        and all(
            bool(case["complete"] and case["physical_match"])
            for case in performance.values()
        )
    )
    work_pass = not work_mismatches
    improved_case_route = len(improved_cases) >= minimum_case_count
    aggregate_route = aggregate_reduction >= aggregate_threshold
    performance_pass = bool(improved_case_route or aggregate_route)
    regression_pass = not regression_failures
    advance = bool(
        complete and work_pass and performance_pass and regression_pass
    )

    return {
        "schema": "anysolver.nonlinear_static.nonfollower_screen_adjudication",
        "version": 1,
        "identity": {
            **expected_identity,
            "raw_evidence_sha256": observed_evidence_sha256,
            "runner_sha256": identity["runner_sha256"],
            "baseline_wheel_sha256": identity["baseline_wheel_sha256"],
            "candidate_wheel_sha256": identity["candidate_wheel_sha256"],
        },
        "criteria": {
            "case_reduction_fraction": case_threshold,
            "minimum_improved_case_count": minimum_case_count,
            "observed_case_reduction_fraction": reductions,
            "improved_cases": improved_cases,
            "improved_case_route_pass": improved_case_route,
            "aggregate_definition": "sum of per-case median complete-route seconds",
            "aggregate_reduction_fraction": aggregate_threshold,
            "baseline_aggregate_seconds": baseline_aggregate,
            "candidate_aggregate_seconds": candidate_aggregate,
            "observed_aggregate_reduction_fraction": aggregate_reduction,
            "aggregate_route_pass": aggregate_route,
            "maximum_case_regression_fraction": maximum_regression,
            "regression_failures": regression_failures,
            "work_mismatches": work_mismatches,
        },
        "decision": {
            "completeness": "PASS" if complete else "FAIL",
            "mechanics": "PASS" if complete else "FAIL",
            "work_equivalence": "PASS" if work_pass else "FAIL",
            "performance_route": "PASS" if performance_pass else "FAIL",
            "case_regression_limit": "PASS" if regression_pass else "FAIL",
            "screen": "PASS" if advance else "FAIL",
            "next_action": (
                "ADVANCE_COMBINED_CANDIDATE_TO_EXISTING_FORMAL_GATE"
                if advance
                else "RETAIN_OR_REJECT_COMPONENT_WITHOUT_PROMOTION"
            ),
        },
    }


def _write_report(result: Mapping[str, Any], path: Path) -> None:
    criteria = result["criteria"]
    decision = result["decision"]
    lines = [
        "# Non-follower implementation screen",
        "",
        f"Raw evidence SHA-256: `{result['identity']['raw_evidence_sha256']}`.",
        "",
        "| Case | Median reduction | Result |",
        "| --- | ---: | --- |",
    ]
    for case_id, reduction in criteria[
        "observed_case_reduction_fraction"
    ].items():
        passed = reduction >= criteria["case_reduction_fraction"]
        lines.append(
            f"| `{case_id}` | {reduction:.2%} | "
            f"{'improved case' if passed else 'below case threshold'} |"
        )
    lines.extend(
        [
            "",
            f"Aggregate reduction: "
            f"**{criteria['observed_aggregate_reduction_fraction']:.2%}** "
            f"using {criteria['aggregate_definition']}.",
            "",
            f"- Evidence completeness: **{decision['completeness']}**",
            f"- Mechanics equivalence: **{decision['mechanics']}**",
            f"- Work equivalence: **{decision['work_equivalence']}**",
            f"- Performance route: **{decision['performance_route']}**",
            f"- Case regression limit: **{decision['case_regression_limit']}**",
            f"- Screen: **{decision['screen']}**",
            f"- Next action: **{decision['next_action']}**",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected-evidence-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = adjudicate(
        evidence_path=args.evidence.resolve(),
        manifest_path=args.manifest.resolve(),
        expected_evidence_sha256=args.expected_evidence_sha256,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(result, args.report)
    return 0 if result["decision"]["completeness"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
