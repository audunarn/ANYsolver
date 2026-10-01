"""Adjudicate the registered follower-validation retention criteria."""

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
            "follower-validation evidence SHA-256 mismatch: "
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
            "follower-validation evidence identity mismatch: "
            + json.dumps(identity_mismatches, sort_keys=True)
        )

    performance: Mapping[str, Mapping[str, Any]] = evidence["performance"]
    acceptance = manifest["acceptance"]
    target_case = str(acceptance["target_case"])
    target_threshold = float(acceptance["target_case_reduction_fraction"])
    maximum_regression = float(
        acceptance["maximum_non_target_regression_fraction"]
    )
    target_reduction = float(
        performance[target_case]["summary"]["median_reduction_fraction"]
    )
    non_target_reductions = {
        case_id: float(case["summary"]["median_reduction_fraction"])
        for case_id, case in performance.items()
        if case_id != target_case
    }
    non_target_failures = {
        case_id: reduction
        for case_id, reduction in non_target_reductions.items()
        if reduction < -maximum_regression
    }
    complete = bool(
        evidence["decision"]["completeness"] == "PASS"
        and not evidence.get("failures")
        and all(
            bool(case["complete"] and case["physical_match"])
            for case in performance.values()
        )
    )
    target_pass = target_reduction >= target_threshold
    non_target_pass = not non_target_failures
    promotion = bool(
        complete
        and target_pass
        and non_target_pass
        and evidence["decision"]["performance"] == "GO"
    )
    return {
        "schema": "anysolver.nonlinear_static.follower_validation_adjudication",
        "version": 1,
        "identity": {
            **expected_identity,
            "raw_evidence_sha256": observed_evidence_sha256,
            "runner_sha256": identity["runner_sha256"],
            "baseline_wheel_sha256": identity["baseline_wheel_sha256"],
            "candidate_wheel_sha256": identity["candidate_wheel_sha256"],
        },
        "criteria": {
            "target_case": target_case,
            "target_required_reduction_fraction": target_threshold,
            "target_observed_reduction_fraction": target_reduction,
            "target_pass": target_pass,
            "maximum_non_target_regression_fraction": maximum_regression,
            "non_target_observed_reduction_fraction": non_target_reductions,
            "non_target_failures": non_target_failures,
            "non_target_pass": non_target_pass,
            "representative_median_reduction_fraction": evidence["decision"][
                "representative_nonlinear_median_reduction_fraction"
            ],
            "representative_performance_decision": evidence["decision"][
                "performance"
            ],
        },
        "decision": {
            "completeness": "PASS" if complete else "FAIL",
            "mechanics": "PASS" if complete else "FAIL",
            "target_performance": "PASS" if target_pass else "FAIL",
            "non_target_regression": "PASS" if non_target_pass else "FAIL",
            "promotion": "GO" if promotion else "NO-GO",
            "retention": (
                "RETAIN_EXPERIMENTAL"
                if complete and target_pass
                else "DO_NOT_RETAIN"
            ),
        },
    }


def _write_report(result: Mapping[str, Any], path: Path) -> None:
    criteria = result["criteria"]
    decision = result["decision"]
    lines = [
        "# Follower-validation retention adjudication",
        "",
        f"Raw evidence SHA-256: `{result['identity']['raw_evidence_sha256']}`.",
        "",
        "## Registered criteria",
        "",
        "| Criterion | Required | Observed | Result |",
        "| --- | ---: | ---: | --- |",
        (
            f"| Target follower reduction | "
            f"{criteria['target_required_reduction_fraction']:.2%} | "
            f"{criteria['target_observed_reduction_fraction']:.2%} | "
            f"{'PASS' if criteria['target_pass'] else 'FAIL'} |"
        ),
    ]
    for case_id, reduction in criteria[
        "non_target_observed_reduction_fraction"
    ].items():
        passed = case_id not in criteria["non_target_failures"]
        lines.append(
            f"| Non-target `{case_id}` | no worse than "
            f"-{criteria['maximum_non_target_regression_fraction']:.2%} | "
            f"{reduction:.2%} | {'PASS' if passed else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Evidence completeness: **{decision['completeness']}**",
            f"- Mechanics equivalence: **{decision['mechanics']}**",
            f"- Registered representative performance: "
            f"**{criteria['representative_performance_decision']}** "
            f"({criteria['representative_median_reduction_fraction']:.2%})",
            f"- Target follower performance: **{decision['target_performance']}**",
            f"- Non-target regression limit: **{decision['non_target_regression']}**",
            f"- Promotion: **{decision['promotion']}**",
            f"- Retention: **{decision['retention']}**",
            "",
            "The optimization remains mechanics-preserving and is retained for "
            "review, but it does not pass the registered promotion gate. The "
            "raw campaign and its NO-GO decision remain unchanged.",
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
