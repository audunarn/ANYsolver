from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/reference_cases/nonlinear_static_representative_manifest.json"
FOLLOWER_MANIFEST = (
    ROOT
    / "docs/reference_cases/nonlinear_static_follower_validation_manifest.json"
)
RUNNER = ROOT / "scripts/qualify_nonlinear_representative.py"


def _runner_module():
    spec = importlib.util.spec_from_file_location("representative_runner", RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_manifest_freezes_inventory_limits_and_acceptance() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    case_ids = [case["id"] for case in manifest["performance_cases"]]
    assert len(case_ids) == len(set(case_ids)) == 5
    assert manifest["execution"]["performance_pairs"] == 7
    assert manifest["execution"]["convergence_repeats"] == 3
    assert manifest["resource_limits"] == {
        "per_solve_timeout_seconds": 900,
        "worker_startup_timeout_seconds": 120,
        "process_tree_memory_bytes": 8 * 1024**3,
        "campaign_wall_budget_seconds": 4 * 60 * 60,
    }
    assert set(manifest["convergence_case_ids"]) < set(case_ids)
    assert manifest["acceptance"]["performance_median_reduction_fraction"] == 0.10
    assert manifest["acceptance"]["maximum_easy_regression_fraction"] == 0.05


def test_follower_manifest_amplifies_only_the_short_mpc_timing_case() -> None:
    manifest = json.loads(FOLLOWER_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["version"] == 2
    repetitions = {
        str(case["id"]): int(case.get("timing_repetitions", 1))
        for case in manifest["performance_cases"]
    }
    assert repetitions == {
        "easy_elastic_shell_control": 1,
        "large_deflection_shell_holdout": 1,
        "plastic_s3_reversal_holdout": 1,
        "prescribed_mpc_beam_holdout": 25,
        "nonsymmetric_follower_shell_holdout": 1,
    }
    assert "identical physical and work hashes" in manifest["execution"][
        "short_case_timing_aggregation"
    ]


@pytest.mark.parametrize(
    "case_id",
    [
        "easy_elastic_shell_control",
        "large_deflection_shell_holdout",
        "plastic_s3_reversal_holdout",
        "prescribed_mpc_beam_holdout",
        "nonsymmetric_follower_shell_holdout",
    ],
)
def test_frozen_case_builders_produce_independent_models(case_id: str) -> None:
    module = _runner_module()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    case = next(case for case in manifest["performance_cases"] if case["id"] == case_id)
    left_model, left_options, left_probes = module._build_case(case, "never")
    right_model, right_options, right_probes = module._build_case(case, "never")
    assert left_model is not right_model
    assert left_model.name == right_model.name == case_id
    assert left_options["num_steps"] == right_options["num_steps"] == case["num_steps"]
    assert left_options["convergence_settings"] == {
        "profile": "legacy",
        "line_search": "never",
    }
    assert left_probes == right_probes


def test_physical_comparison_rejects_status_or_inventory_changes() -> None:
    module = _runner_module()
    physical = {
        "status": "completed",
        "load_factor": 1.0,
        "displacements": [0.0, 1.0],
        "steps": [
            {
                "load_factor": 1.0,
                "residual_norm": 0.0,
                "displacement_norm": 1.0,
                "max_equivalent_plastic_strain": 0.0,
            }
        ],
        "support_reactions": [{"fixed": [1.0]}],
        "state_summary": {"alpha": 0.0, "plastic_strain": 0.0},
        "state_observables": {},
        "snapshots": [],
        "family_checks": {"completed": True, "target_load_factor": True},
    }
    left = {
        "ok": True,
        "physical": physical,
        "physical_sha256": module._json_digest(physical),
    }
    right = json.loads(json.dumps(left))
    assert module._compare_physics(left, right)["numerical_match"] is True
    right["physical"]["status"] = "failed"
    assert module._compare_physics(left, right)["numerical_match"] is False


def test_physical_comparison_rejects_changed_increment_path() -> None:
    module = _runner_module()
    physical = {
        "status": "completed",
        "load_factor": 1.0,
        "displacements": [0.0, 1.0],
        "steps": [
            {
                "load_factor": 1.0,
                "residual_norm": 0.0,
                "displacement_norm": 1.0,
                "max_equivalent_plastic_strain": 0.0,
            }
        ],
        "support_reactions": [{"fixed": [1.0]}],
        "state_summary": {"alpha": 0.0, "plastic_strain": 0.0},
        "state_observables": {},
        "snapshots": [],
        "family_checks": {"completed": True, "target_load_factor": True},
    }
    left = {
        "ok": True,
        "physical": physical,
        "physical_sha256": module._json_digest(physical),
    }
    right = json.loads(json.dumps(left))
    right["physical"]["steps"][0]["load_factor"] = 0.9
    assert module._compare_physics(left, right)["numerical_match"] is False


def test_timing_repetitions_use_median_and_require_equivalent_work() -> None:
    module = _runner_module()
    samples = [
        {
            "complete_route_wall_seconds": route,
            "solver_seconds": solver,
            "physical_sha256": "physics",
            "work": {"iterations": 32},
            "status": "completed",
        }
        for route, solver in ((0.4, 0.3), (0.2, 0.1), (0.3, 0.2))
    ]
    result = module._aggregate_timing_repetitions(samples)
    assert result["complete_route_wall_seconds"] == pytest.approx(0.3)
    assert result["solver_seconds"] == pytest.approx(0.2)
    assert result["timing_repetitions"]["count"] == 3
    assert result["timing_repetitions"]["physical_match"] is True
    assert result["timing_repetitions"]["work_match"] is True

    changed = json.loads(json.dumps(samples))
    changed[-1]["work"]["iterations"] = 33
    with pytest.raises(RuntimeError, match="different solver work"):
        module._aggregate_timing_repetitions(changed)


def test_identity_validation_rejects_stale_wheel(tmp_path: Path) -> None:
    module = _runner_module()
    baseline = tmp_path / "baseline.whl"
    candidate = tmp_path / "candidate.whl"
    baseline.write_bytes(b"baseline")
    candidate.write_bytes(b"candidate")
    manifest = {
        "baseline_revision": "base-revision",
        "candidate_revision": "candidate-revision",
        "source_trees": {"baseline": "base-tree", "candidate": "candidate-tree"},
    }
    provenance = {
        "baseline_revision": "base-revision",
        "candidate_revision": "candidate-revision",
        "baseline_tree": "base-tree",
        "candidate_tree": "candidate-tree",
        "baseline_wheel_sha256": module._sha256(baseline),
        "candidate_wheel_sha256": "stale",
    }
    with pytest.raises(ValueError, match="build provenance"):
        module._validate_campaign_identity(
            manifest=manifest,
            provenance=provenance,
            baseline_wheel=baseline,
            candidate_wheel=candidate,
        )


def test_armijo_resource_failure_cannot_promote() -> None:
    module = _runner_module()
    convergence = {
        "case": {
            "complete": True,
            "physical_match": True,
            "newly_solved_by_armijo": True,
            "residual_decrease_failed_work": 100,
            "armijo_failed_work": 0,
            "residual_decrease_median_seconds": None,
            "armijo_median_seconds": None,
            "pairs": [
                {
                    "always": {"ok": False, "terminal_reason": "measured_timeout"},
                    "armijo": {"ok": False, "terminal_reason": "memory_limit"},
                }
            ],
        }
    }
    decision = module._adjudicate_armijo(
        convergence=convergence,
        convergence_repeats=3,
        timeout_seconds=900.0,
        acceptance={
            "armijo_new_difficult_solves": 1,
            "armijo_failed_work_reduction_fraction": 0.25,
        },
    )
    assert decision["go"] is False
    assert decision["armijo_all_samples_completed"] is False


def test_report_renders_incomplete_performance_case(tmp_path: Path) -> None:
    module = _runner_module()
    report = tmp_path / "report.md"
    module._write_report(
        {
            "started_utc": "2026-09-20T00:00:00Z",
            "completed_utc": "2026-09-20T00:01:00Z",
            "identity": {
                "baseline_revision": "base",
                "candidate_revision": "candidate",
                "manifest_sha256": "manifest",
                "runner_sha256": "runner",
            },
            "performance": {
                "case": {"summary": None, "physical_match": False}
            },
            "convergence": {},
            "decision": {
                "performance": "NO-GO",
                "armijo": "NO-GO",
                "completeness": "FAIL",
            },
        },
        report,
    )
    assert "resource limit" in report.read_text(encoding="utf-8")


def test_install_root_conflict_is_reportable_setup_failure(tmp_path: Path) -> None:
    module = _runner_module()
    install_root = tmp_path / "existing"
    install_root.mkdir()
    sites, records, failure = module._install_frozen_wheels(
        install_root=install_root,
        baseline_wheel=tmp_path / "baseline.whl",
        candidate_wheel=tmp_path / "candidate.whl",
        campaign_deadline=time.perf_counter() + 10.0,
    )
    assert sites == {}
    assert records == {}
    assert failure["terminal_reason"] == "install_root_error"


def test_legacy_follower_diagnostic_absence_does_not_fail_physics() -> None:
    module = _runner_module()
    result = SimpleNamespace(
        status="completed",
        load_factor=1.0,
        displacements=[0.0, 1.0],
        info={"equilibrium_tangent": "K_internal-K_external"},
    )
    checks = module._family_checks(
        result,
        {"builder": "clamped_shell", "follower_pressure": True},
        {"centre_uz_dof": 1},
    )
    assert checks["current_external_load"] is True


def test_convergence_resource_terminals_are_complete_no_solution_evidence() -> None:
    module = _runner_module()
    terminal = {"ok": False, "terminal_reason": "warm_timeout"}
    status = module._convergence_physical_status(
        oracle={"ok": True},
        method_samples={"always": [terminal], "armijo": [terminal]},
    )
    assert status == {
        "physical_match": True,
        "basis": "resource_terminal_no_solution",
        "completed_samples": 0,
    }
