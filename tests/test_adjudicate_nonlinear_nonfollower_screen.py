from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.adjudicate_nonlinear_nonfollower_screen import adjudicate


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _case(reduction: float, *, work_match: bool = True) -> dict[str, object]:
    baseline_seconds = 10.0
    candidate_seconds = baseline_seconds * (1.0 - reduction)
    baseline_work = {"assembly_calls": 4}
    candidate_work = dict(baseline_work)
    if not work_match:
        candidate_work["assembly_calls"] = 3
    return {
        "complete": True,
        "physical_match": True,
        "summary": {
            "baseline_median_seconds": baseline_seconds,
            "candidate_median_seconds": candidate_seconds,
            "median_reduction_fraction": reduction,
        },
        "pairs": [
            {
                "pair": 1,
                "baseline": {"work": baseline_work},
                "candidate": {"work": candidate_work},
            }
        ],
    }


def _adjudicate(
    tmp_path: Path,
    reductions: list[float],
    *,
    mismatched_work_case: int | None = None,
) -> dict[str, object]:
    case_ids = [f"case_{index}" for index in range(len(reductions))]
    manifest = {
        "baseline_revision": "baseline",
        "candidate_revision": "candidate",
        "performance_cases": [{"id": case_id} for case_id in case_ids],
        "screen_acceptance": {
            "case_reduction_fraction": 0.05,
            "minimum_improved_case_count": 2,
            "aggregate_reduction_fraction": 0.05,
            "maximum_case_regression_fraction": 0.05,
        },
    }
    manifest_path = tmp_path / "manifest.json"
    _write_json(manifest_path, manifest)
    evidence = {
        "identity": {
            "baseline_revision": "baseline",
            "candidate_revision": "candidate",
            "manifest_sha256": _sha256(manifest_path),
            "runner_sha256": "runner",
            "baseline_wheel_sha256": "baseline-wheel",
            "candidate_wheel_sha256": "candidate-wheel",
        },
        "installed_regressions": {"ok": True},
        "performance": {
            case_id: _case(
                reduction,
                work_match=index != mismatched_work_case,
            )
            for index, (case_id, reduction) in enumerate(
                zip(case_ids, reductions)
            )
        },
        "decision": {"completeness": "PASS"},
        "failures": [],
    }
    evidence_path = tmp_path / "evidence.json"
    _write_json(evidence_path, evidence)
    return adjudicate(
        evidence_path=evidence_path,
        manifest_path=manifest_path,
        expected_evidence_sha256=_sha256(evidence_path),
    )


def test_screen_passes_through_two_case_route(tmp_path: Path) -> None:
    result = _adjudicate(tmp_path, [0.06, 0.05, 0.0, 0.0])

    assert result["criteria"]["improved_case_route_pass"] is True
    assert result["decision"]["screen"] == "PASS"


def test_screen_passes_through_aggregate_route(tmp_path: Path) -> None:
    result = _adjudicate(tmp_path, [0.04, 0.04, 0.04, 0.08])

    assert result["criteria"]["improved_case_route_pass"] is False
    assert result["criteria"]["aggregate_route_pass"] is True
    assert result["decision"]["screen"] == "PASS"


def test_screen_rejects_case_regression_or_work_change(tmp_path: Path) -> None:
    result = _adjudicate(
        tmp_path,
        [0.10, 0.10, 0.10, -0.06],
        mismatched_work_case=1,
    )

    assert result["decision"]["work_equivalence"] == "FAIL"
    assert result["decision"]["case_regression_limit"] == "FAIL"
    assert result["decision"]["screen"] == "FAIL"
