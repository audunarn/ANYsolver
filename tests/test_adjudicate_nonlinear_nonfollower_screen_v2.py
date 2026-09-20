from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

import pytest

from scripts.adjudicate_nonlinear_nonfollower_screen_v2 import adjudicate


ROOT = Path(__file__).resolve().parents[1]
RAW_EVIDENCE_SHA256 = (
    "c9082649ba84d2bca5db0122c8b613fa9c773793beb6c976dd9162950438eca0"
)
PROVENANCE_SHA256 = (
    "3f07dee584e573af598f912e516031fee70735a044ffd52b7779b6917f6f6300"
)


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _sample(seconds: float, *, work: int = 4) -> dict[str, object]:
    physical = {"result": [1.0, 2.0]}
    work_payload = {"assembly_calls": work}
    return {
        "ok": True,
        "exit_code": 0,
        "terminal_reason": "exit",
        "status": "completed",
        "complete_route_wall_seconds": seconds,
        "solver_seconds": seconds * 0.9,
        "physical": physical,
        "physical_sha256": _json_digest(physical),
        "work": work_payload,
        "timing_repetitions": {
            "aggregation": "median",
            "count": 1,
            "physical_match": True,
            "physical_sha256": _json_digest(physical),
            "route_seconds": [seconds],
            "solver_seconds": [seconds * 0.9],
            "work_match": True,
            "work_sha256": _json_digest(work_payload),
        },
    }


def _case(reduction: float) -> dict[str, object]:
    baseline_times = [10.1, 10.0, 9.9]
    candidate_times = [
        value * (1.0 - reduction) for value in baseline_times
    ]
    pairs = []
    for offset in range(3):
        pairs.append(
            {
                "pair": offset + 1,
                "order": (
                    ["baseline", "candidate"]
                    if offset % 2 == 0
                    else ["candidate", "baseline"]
                ),
                "baseline": _sample(baseline_times[offset]),
                "candidate": _sample(candidate_times[offset]),
                "physical_comparison": {
                    "numerical_match": True,
                    "family_targets_met": True,
                },
            }
        )
    baseline_median = float(statistics.median(baseline_times))
    candidate_median = float(statistics.median(candidate_times))
    return {
        "complete": True,
        "physical_match": True,
        "summary": {
            "baseline_median_seconds": baseline_median,
            "candidate_median_seconds": candidate_median,
            "median_reduction_fraction": (
                baseline_median - candidate_median
            )
            / baseline_median,
        },
        "pairs": pairs,
    }


def _fixture(
    tmp_path: Path,
    reductions: list[float],
) -> tuple[Path, Path, Path]:
    case_ids = [f"case_{index}" for index in range(len(reductions))]
    runner_sha256 = "runner-sha256"
    manifest = {
        "baseline_revision": "baseline",
        "candidate_revision": "candidate",
        "source_trees": {"baseline": "baseline-tree", "candidate": "candidate-tree"},
        "execution": {"performance_pairs": 3},
        "performance_cases": [{"id": case_id} for case_id in case_ids],
        "screen_contract": {"runner_sha256": runner_sha256},
        "screen_acceptance": {
            "case_reduction_fraction": 0.05,
            "minimum_improved_case_count": 2,
            "aggregate_reduction_fraction": 0.05,
            "maximum_case_regression_fraction": 0.05,
        },
    }
    manifest_path = tmp_path / "manifest.json"
    _write_json(manifest_path, manifest)
    provenance = {
        "baseline_revision": "baseline",
        "candidate_revision": "candidate",
        "baseline_tree": "baseline-tree",
        "candidate_tree": "candidate-tree",
        "baseline_wheel_sha256": "baseline-wheel",
        "candidate_wheel_sha256": "candidate-wheel",
    }
    provenance_path = tmp_path / "provenance.json"
    _write_json(provenance_path, provenance)
    evidence = {
        "identity": {
            **{
                "baseline_revision": "baseline",
                "candidate_revision": "candidate",
                "baseline_tree": "baseline-tree",
                "candidate_tree": "candidate-tree",
            },
            "manifest_sha256": _sha256(manifest_path),
            "runner_sha256": runner_sha256,
            "build_provenance_sha256": _sha256(provenance_path),
            "baseline_wheel_sha256": "baseline-wheel",
            "candidate_wheel_sha256": "candidate-wheel",
            "installed_sites": {
                "baseline": {"wheel_sha256": "baseline-wheel"},
                "candidate": {"wheel_sha256": "candidate-wheel"},
            },
            "thread_environment": {
                "OMP_NUM_THREADS": "1",
                "OPENBLAS_NUM_THREADS": "1",
                "MKL_NUM_THREADS": "1",
                "NUMBA_NUM_THREADS": "1",
            },
        },
        "installed_regressions": {"ok": True, "exit_code": 0},
        "performance": {
            case_id: _case(reduction)
            for case_id, reduction in zip(case_ids, reductions)
        },
        "decision": {"completeness": "PASS"},
        "failures": [],
    }
    evidence_path = tmp_path / "evidence.json"
    _write_json(evidence_path, evidence)
    return evidence_path, manifest_path, provenance_path


def _adjudicate_fixture(
    evidence_path: Path,
    manifest_path: Path,
    provenance_path: Path,
) -> dict[str, object]:
    return adjudicate(
        evidence_path=evidence_path,
        manifest_path=manifest_path,
        provenance_path=provenance_path,
        expected_evidence_sha256=_sha256(evidence_path),
        expected_provenance_sha256=_sha256(provenance_path),
    )


def test_strict_adjudicator_recomputes_raw_pairs(tmp_path: Path) -> None:
    evidence, manifest, provenance = _fixture(
        tmp_path,
        [0.06, 0.05, 0.0, 0.0],
    )

    result = _adjudicate_fixture(evidence, manifest, provenance)

    assert result["validated_execution"]["successful_sample_count"] == 24
    assert result["decision"]["screen"] == "PASS"


def test_strict_adjudicator_rejects_missing_pair(tmp_path: Path) -> None:
    evidence, manifest, provenance = _fixture(
        tmp_path,
        [0.06, 0.05, 0.0, 0.0],
    )
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    payload["performance"]["case_0"]["pairs"].pop()
    _write_json(evidence, payload)

    with pytest.raises(ValueError, match="pair count"):
        _adjudicate_fixture(evidence, manifest, provenance)


def test_strict_adjudicator_rejects_fabricated_summary(tmp_path: Path) -> None:
    evidence, manifest, provenance = _fixture(
        tmp_path,
        [-0.10, -0.10, -0.10, -0.10],
    )
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    payload["performance"]["case_0"]["summary"][
        "median_reduction_fraction"
    ] = 0.99
    _write_json(evidence, payload)

    with pytest.raises(ValueError, match="stored reduction"):
        _adjudicate_fixture(evidence, manifest, provenance)


def test_strict_adjudicator_rejects_wheel_identity_change(tmp_path: Path) -> None:
    evidence, manifest, provenance = _fixture(
        tmp_path,
        [0.06, 0.05, 0.0, 0.0],
    )
    payload = json.loads(evidence.read_text(encoding="utf-8"))
    payload["identity"]["candidate_wheel_sha256"] = "other-wheel"
    _write_json(evidence, payload)

    with pytest.raises(ValueError, match="candidate_wheel_sha256"):
        _adjudicate_fixture(evidence, manifest, provenance)


def test_strict_adjudicator_recomputes_committed_screen() -> None:
    result = adjudicate(
        evidence_path=(
            ROOT
            / "reports"
            / "performance"
            / "nonlinear_static_nonfollower_screen_evidence.json"
        ),
        manifest_path=(
            ROOT
            / "docs"
            / "reference_cases"
            / "nonlinear_static_nonfollower_screen_manifest.json"
        ),
        provenance_path=(
            ROOT
            / "reports"
            / "performance"
            / "nonlinear_static_nonfollower_screen_build_provenance.json"
        ),
        expected_evidence_sha256=RAW_EVIDENCE_SHA256,
        expected_provenance_sha256=PROVENANCE_SHA256,
    )

    assert result["validated_execution"] == {
        "case_inventory": [
            "easy_elastic_shell_control",
            "large_deflection_shell_holdout",
            "plastic_s3_reversal_holdout",
            "prescribed_mpc_beam_holdout",
        ],
        "pairs_per_case": 3,
        "alternating_order": True,
        "successful_sample_count": 24,
        "physical_comparison_count": 12,
        "installed_regressions": "PASS",
    }
    assert result["criteria"]["work_mismatches"] == []
    assert result["decision"]["screen"] == "FAIL"
