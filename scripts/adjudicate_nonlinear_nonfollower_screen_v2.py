"""Strictly re-adjudicate the frozen non-follower screen evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
from pathlib import Path
from typing import Any, Mapping


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _content_hashes(path: Path) -> set[str]:
    """Return exact and Git checkout line-ending representations."""

    payload = path.read_bytes()
    normalized = payload.replace(b"\r\n", b"\n")
    return {
        hashlib.sha256(payload).hexdigest(),
        hashlib.sha256(normalized).hexdigest(),
        hashlib.sha256(normalized.replace(b"\n", b"\r\n")).hexdigest(),
    }


def _require_content_hash(name: str, path: Path, expected: str) -> str:
    normalized_expected = str(expected).lower()
    if normalized_expected not in _content_hashes(path):
        raise ValueError(
            f"{name} SHA-256 mismatch: expected {normalized_expected}, "
            f"observed {sorted(_content_hashes(path))}"
        )
    return normalized_expected


def _json_digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _require_equal(name: str, observed: Any, expected: Any) -> None:
    if observed != expected:
        raise ValueError(
            f"{name} mismatch: expected {expected!r}, observed {observed!r}"
        )


def _require_close(name: str, observed: Any, expected: float) -> None:
    value = float(observed)
    if not math.isclose(value, expected, rel_tol=1.0e-12, abs_tol=1.0e-12):
        raise ValueError(
            f"{name} mismatch: expected {expected!r}, observed {value!r}"
        )


def _validate_identity(
    *,
    evidence: Mapping[str, Any],
    manifest: Mapping[str, Any],
    manifest_path: Path,
    provenance: Mapping[str, Any],
    provenance_sha256: str,
) -> dict[str, Any]:
    expected_provenance = {
        "baseline_revision": manifest["baseline_revision"],
        "candidate_revision": manifest["candidate_revision"],
        "baseline_tree": manifest["source_trees"]["baseline"],
        "candidate_tree": manifest["source_trees"]["candidate"],
    }
    for name, expected in expected_provenance.items():
        _require_equal(f"provenance.{name}", provenance.get(name), expected)

    contract = manifest["screen_contract"]
    identity = evidence["identity"]
    manifest_sha256 = _require_content_hash(
        "manifest",
        manifest_path,
        identity.get("manifest_sha256", ""),
    )
    expected_identity = {
        **expected_provenance,
        "manifest_sha256": manifest_sha256,
        "runner_sha256": contract["runner_sha256"],
        "build_provenance_sha256": provenance_sha256,
        "baseline_wheel_sha256": provenance["baseline_wheel_sha256"],
        "candidate_wheel_sha256": provenance["candidate_wheel_sha256"],
    }
    for name, expected in expected_identity.items():
        _require_equal(f"evidence.identity.{name}", identity.get(name), expected)

    installed_sites = identity.get("installed_sites")
    if not isinstance(installed_sites, Mapping):
        raise ValueError("evidence installed-site identity is missing")
    for label in ("baseline", "candidate"):
        installed = installed_sites.get(label)
        if not isinstance(installed, Mapping):
            raise ValueError(f"evidence installed-site identity missing {label}")
        _require_equal(
            f"evidence.identity.installed_sites.{label}.wheel_sha256",
            installed.get("wheel_sha256"),
            expected_identity[f"{label}_wheel_sha256"],
        )

    _require_equal(
        "thread environment",
        identity.get("thread_environment"),
        {
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMBA_NUM_THREADS": "1",
        },
    )
    return expected_identity


def _validate_sample(
    *,
    case_id: str,
    pair_index: int,
    label: str,
    sample: Mapping[str, Any],
    timing_repetitions: int,
) -> None:
    prefix = f"{case_id} pair {pair_index} {label}"
    _require_equal(f"{prefix} ok", sample.get("ok"), True)
    _require_equal(f"{prefix} exit code", sample.get("exit_code"), 0)
    _require_equal(f"{prefix} terminal reason", sample.get("terminal_reason"), "exit")
    _require_equal(f"{prefix} status", sample.get("status"), "completed")
    if float(sample.get("complete_route_wall_seconds", 0.0)) <= 0.0:
        raise ValueError(f"{prefix} has no positive complete-route time")
    _require_equal(
        f"{prefix} physical digest",
        sample.get("physical_sha256"),
        _json_digest(sample.get("physical")),
    )
    work = sample.get("work")
    if not isinstance(work, Mapping) or not work:
        raise ValueError(f"{prefix} solver work is missing")

    repetitions = sample.get("timing_repetitions")
    if not isinstance(repetitions, Mapping):
        raise ValueError(f"{prefix} timing repetitions are missing")
    _require_equal(
        f"{prefix} timing count", repetitions.get("count"), timing_repetitions
    )
    _require_equal(
        f"{prefix} timing aggregation",
        repetitions.get("aggregation"),
        "median",
    )
    _require_equal(
        f"{prefix} timing physical match",
        repetitions.get("physical_match"),
        True,
    )
    _require_equal(f"{prefix} timing work match", repetitions.get("work_match"), True)
    _require_equal(
        f"{prefix} route timing inventory",
        len(repetitions.get("route_seconds", [])),
        timing_repetitions,
    )
    _require_equal(
        f"{prefix} solver timing inventory",
        len(repetitions.get("solver_seconds", [])),
        timing_repetitions,
    )
    _require_equal(
        f"{prefix} repeated physical digest",
        repetitions.get("physical_sha256"),
        sample.get("physical_sha256"),
    )
    _require_equal(
        f"{prefix} repeated work digest",
        repetitions.get("work_sha256"),
        _json_digest(work),
    )
    _require_close(
        f"{prefix} repeated route median",
        sample.get("complete_route_wall_seconds"),
        float(statistics.median(repetitions["route_seconds"])),
    )
    _require_close(
        f"{prefix} repeated solver median",
        sample.get("solver_seconds"),
        float(statistics.median(repetitions["solver_seconds"])),
    )


def adjudicate(
    *,
    evidence_path: Path,
    manifest_path: Path,
    provenance_path: Path,
    expected_evidence_sha256: str,
    expected_provenance_sha256: str,
) -> dict[str, Any]:
    evidence_sha256 = _require_content_hash(
        "raw evidence",
        evidence_path,
        expected_evidence_sha256,
    )
    provenance_sha256 = _require_content_hash(
        "build provenance",
        provenance_path,
        expected_provenance_sha256,
    )

    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    expected_identity = _validate_identity(
        evidence=evidence,
        manifest=manifest,
        manifest_path=manifest_path,
        provenance=provenance,
        provenance_sha256=provenance_sha256,
    )

    installed = evidence.get("installed_regressions")
    if not isinstance(installed, Mapping):
        raise ValueError("installed regression evidence is missing")
    _require_equal("installed regressions ok", installed.get("ok"), True)
    _require_equal("installed regressions exit code", installed.get("exit_code"), 0)
    _require_equal(
        "installed regression inventory",
        installed.get("tests"),
        manifest["required_regressions"],
    )
    _require_equal("raw failures", evidence.get("failures"), [])

    performance = evidence.get("performance")
    if not isinstance(performance, Mapping):
        raise ValueError("performance evidence is missing")
    specs = manifest["performance_cases"]
    case_ids = [str(spec["id"]) for spec in specs]
    _require_equal("performance case inventory", list(performance), case_ids)
    pair_count = int(manifest["execution"]["performance_pairs"])
    if pair_count != 3:
        raise ValueError("non-follower screen must retain exactly three pairs")

    reductions: dict[str, float] = {}
    medians: dict[str, dict[str, float]] = {}
    work_mismatches: list[dict[str, Any]] = []
    for spec in specs:
        case_id = str(spec["id"])
        case = performance[case_id]
        pairs = case.get("pairs")
        if not isinstance(pairs, list):
            raise ValueError(f"{case_id} pair inventory is missing")
        _require_equal(f"{case_id} pair count", len(pairs), pair_count)
        baseline_times: list[float] = []
        candidate_times: list[float] = []
        timing_repetitions = int(spec.get("timing_repetitions", 1))
        for offset, pair in enumerate(pairs):
            pair_index = offset + 1
            expected_order = (
                ["baseline", "candidate"]
                if offset % 2 == 0
                else ["candidate", "baseline"]
            )
            _require_equal(f"{case_id} pair number", pair.get("pair"), pair_index)
            _require_equal(
                f"{case_id} pair {pair_index} order",
                pair.get("order"),
                expected_order,
            )
            for label in ("baseline", "candidate"):
                sample = pair.get(label)
                if not isinstance(sample, Mapping):
                    raise ValueError(
                        f"{case_id} pair {pair_index} {label} sample is missing"
                    )
                _validate_sample(
                    case_id=case_id,
                    pair_index=pair_index,
                    label=label,
                    sample=sample,
                    timing_repetitions=timing_repetitions,
                )
                family_checks = sample["physical"].get("family_checks")
                if not isinstance(family_checks, Mapping) or not family_checks:
                    raise ValueError(
                        f"{case_id} pair {pair_index} {label} family checks "
                        "are missing"
                    )
                if not all(value is True for value in family_checks.values()):
                    raise ValueError(
                        f"{case_id} pair {pair_index} {label} family checks "
                        "did not all pass"
                    )
            _require_equal(
                f"{case_id} pair {pair_index} physical digest equality",
                pair["candidate"]["physical_sha256"],
                pair["baseline"]["physical_sha256"],
            )
            comparison = pair.get("physical_comparison")
            if not isinstance(comparison, Mapping):
                raise ValueError(
                    f"{case_id} pair {pair_index} physical comparison is missing"
                )
            _require_equal(
                f"{case_id} pair {pair_index} numerical match",
                comparison.get("numerical_match"),
                True,
            )
            _require_equal(
                f"{case_id} pair {pair_index} family targets",
                comparison.get("family_targets_met"),
                True,
            )
            if pair["baseline"]["work"] != pair["candidate"]["work"]:
                work_mismatches.append(
                    {
                        "case": case_id,
                        "pair": pair_index,
                        "baseline": pair["baseline"]["work"],
                        "candidate": pair["candidate"]["work"],
                    }
                )
            baseline_times.append(
                float(pair["baseline"]["complete_route_wall_seconds"])
            )
            candidate_times.append(
                float(pair["candidate"]["complete_route_wall_seconds"])
            )

        baseline_median = float(statistics.median(baseline_times))
        candidate_median = float(statistics.median(candidate_times))
        reduction = (baseline_median - candidate_median) / baseline_median
        medians[case_id] = {
            "baseline_median_seconds": baseline_median,
            "candidate_median_seconds": candidate_median,
        }
        reductions[case_id] = reduction
        summary = case.get("summary")
        if not isinstance(summary, Mapping):
            raise ValueError(f"{case_id} stored summary is missing")
        _require_close(
            f"{case_id} stored baseline median",
            summary.get("baseline_median_seconds"),
            baseline_median,
        )
        _require_close(
            f"{case_id} stored candidate median",
            summary.get("candidate_median_seconds"),
            candidate_median,
        )
        _require_close(
            f"{case_id} stored reduction",
            summary.get("median_reduction_fraction"),
            reduction,
        )
        _require_equal(f"{case_id} stored complete", case.get("complete"), True)
        _require_equal(
            f"{case_id} stored physical match", case.get("physical_match"), True
        )

    acceptance = manifest["screen_acceptance"]
    case_threshold = float(acceptance["case_reduction_fraction"])
    minimum_case_count = int(acceptance["minimum_improved_case_count"])
    aggregate_threshold = float(acceptance["aggregate_reduction_fraction"])
    maximum_regression = float(acceptance["maximum_case_regression_fraction"])
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
        value["baseline_median_seconds"] for value in medians.values()
    )
    candidate_aggregate = sum(
        value["candidate_median_seconds"] for value in medians.values()
    )
    aggregate_reduction = (
        baseline_aggregate - candidate_aggregate
    ) / baseline_aggregate

    work_pass = not work_mismatches
    improved_case_route = len(improved_cases) >= minimum_case_count
    aggregate_route = aggregate_reduction >= aggregate_threshold
    performance_pass = improved_case_route or aggregate_route
    regression_pass = not regression_failures
    advance = work_pass and performance_pass and regression_pass

    return {
        "schema": "anysolver.nonlinear_static.nonfollower_screen_adjudication",
        "version": 2,
        "identity": {
            **expected_identity,
            "raw_evidence_sha256": evidence_sha256,
            "build_provenance_sha256": provenance_sha256,
        },
        "validated_execution": {
            "case_inventory": case_ids,
            "pairs_per_case": pair_count,
            "alternating_order": True,
            "successful_sample_count": len(case_ids) * pair_count * 2,
            "physical_comparison_count": len(case_ids) * pair_count,
            "installed_regressions": "PASS",
        },
        "criteria": {
            "case_reduction_fraction": case_threshold,
            "minimum_improved_case_count": minimum_case_count,
            "observed_case_medians_seconds": medians,
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
            "completeness": "PASS",
            "mechanics": "PASS",
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
        "# Non-follower implementation screen: strict re-adjudication",
        "",
        f"Raw evidence SHA-256: `{result['identity']['raw_evidence_sha256']}`.",
        "",
        "All registered identities, three alternating pairs per case, 24 successful "
        "samples, 12 physical comparisons, and installed regressions were checked "
        "before recomputing the timing result from raw pair samples.",
        "",
        "| Case | Recomputed median reduction |",
        "| --- | ---: |",
    ]
    for case_id, reduction in criteria[
        "observed_case_reduction_fraction"
    ].items():
        lines.append(f"| `{case_id}` | {reduction:.2%} |")
    lines.extend(
        [
            "",
            f"Recomputed aggregate reduction: "
            f"**{criteria['observed_aggregate_reduction_fraction']:.2%}**.",
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
    parser.add_argument("--provenance", type=Path, required=True)
    parser.add_argument("--expected-evidence-sha256", required=True)
    parser.add_argument("--expected-provenance-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = adjudicate(
        evidence_path=args.evidence.resolve(),
        manifest_path=args.manifest.resolve(),
        provenance_path=args.provenance.resolve(),
        expected_evidence_sha256=args.expected_evidence_sha256,
        expected_provenance_sha256=args.expected_provenance_sha256,
    )
    result["adjudicator"] = str(Path(__file__).resolve())
    result["adjudicator_sha256"] = _sha256(Path(__file__).resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_report(result, args.report)
    return 0 if result["decision"]["completeness"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
