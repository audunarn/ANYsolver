from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/adjudicate_follower_validation.py"


def _module():
    spec = importlib.util.spec_from_file_location(
        "follower_validation_adjudicator",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    module = _module()
    manifest = {
        "baseline_revision": "base",
        "candidate_revision": "candidate",
        "acceptance": {
            "target_case": "follower",
            "target_case_reduction_fraction": 0.1,
            "maximum_non_target_regression_fraction": 0.05,
        },
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    evidence = {
        "identity": {
            "baseline_revision": "base",
            "candidate_revision": "candidate",
            "manifest_sha256": module._sha256(manifest_path),
            "runner_sha256": "runner",
            "baseline_wheel_sha256": "baseline-wheel",
            "candidate_wheel_sha256": "candidate-wheel",
        },
        "performance": {
            "control": {
                "complete": True,
                "physical_match": True,
                "summary": {"median_reduction_fraction": -0.06},
            },
            "follower": {
                "complete": True,
                "physical_match": True,
                "summary": {"median_reduction_fraction": 0.8},
            },
        },
        "decision": {
            "completeness": "PASS",
            "performance": "NO-GO",
            "representative_nonlinear_median_reduction_fraction": 0.0,
        },
        "failures": [],
    }
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
    return evidence_path, manifest_path


def test_adjudicator_records_target_pass_and_non_target_failure(
    tmp_path: Path,
) -> None:
    module = _module()
    evidence, manifest = _write_inputs(tmp_path)
    result = module.adjudicate(
        evidence_path=evidence,
        manifest_path=manifest,
        expected_evidence_sha256=module._sha256(evidence),
    )
    assert result["decision"] == {
        "completeness": "PASS",
        "mechanics": "PASS",
        "target_performance": "PASS",
        "non_target_regression": "FAIL",
        "promotion": "NO-GO",
        "retention": "RETAIN_EXPERIMENTAL",
    }
    assert result["criteria"]["non_target_failures"] == {
        "control": -0.06
    }


def test_adjudicator_rejects_unbound_raw_evidence(tmp_path: Path) -> None:
    module = _module()
    evidence, manifest = _write_inputs(tmp_path)
    with pytest.raises(ValueError, match="evidence SHA-256 mismatch"):
        module.adjudicate(
            evidence_path=evidence,
            manifest_path=manifest,
            expected_evidence_sha256="0" * 64,
        )
