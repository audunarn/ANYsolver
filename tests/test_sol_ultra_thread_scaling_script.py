from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "benchmark_sol_ultra_thread_scaling.py"
SPEC = importlib.util.spec_from_file_location("_sol_ultra_thread_scaling_script", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
BENCHMARK = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BENCHMARK
SPEC.loader.exec_module(BENCHMARK)


def _fake_factory(_config):
    def factory(thread_count):
        def invoke():
            return {
                "status": "completed",
                "resource_config": {"requested_threads": int(thread_count)},
                "backend": {"api": "fake_public_api"},
                "_comparison_vector": np.asarray([1.0, 2.0, 3.0]),
            }

        return invoke, {"nodes": 2, "elements": 1, "dofs": 12}, lambda: None

    return factory


def test_small_campaign_invocation_has_stable_evidence_schema(monkeypatch) -> None:
    monkeypatch.setattr(BENCHMARK, "_nonlinear_factory", _fake_factory)
    monkeypatch.setattr(BENCHMARK, "_linear_factory", _fake_factory)
    monkeypatch.setattr(BENCHMARK, "_recovery_factory", _fake_factory)
    config = BENCHMARK.CampaignConfig(
        assembly_threads=(1, 2),
        solver_threads=(1, 2),
        recovery_threads=(1, 2),
        repeats=2,
        assembly_nx=1,
        assembly_ny=1,
        linear_nx=1,
        linear_ny=1,
        recovery_nx=1,
        recovery_ny=1,
        nonlinear_steps=1,
    )

    report = BENCHMARK.run_campaign(config, run_exception_audit=False)

    assert report["schema_name"] == BENCHMARK.SCHEMA_NAME
    assert report["schema_version"] == BENCHMARK.SCHEMA_VERSION
    assert report["summary"] == {
        "status": "completed",
        "failed_sections": [],
        "timings_are_acceptance_thresholds": False,
        "default_thread_policy_changed": False,
    }
    assert set(report["workloads"]) == {
        "nonlinear_assembly",
        "linear_solver",
        "stress_recovery",
    }
    for workload in report["workloads"].values():
        assert workload["thread_counts"] == [1, 2]
        assert workload["status"] == "completed"
        for entry in workload["entries"]:
            cold = entry["measurements"]["cold"]
            warm = entry["measurements"]["warm"]
            assert cold["wall_seconds"] >= 0.0
            assert cold["python_peak_bytes"] >= 0
            assert "process_peak_rss_bytes" in cold
            assert cold["thread_restoration"]["restored"] is True
            assert warm["repeats"] == 2
            assert len(warm["wall_seconds"]["samples"]) == 2
            assert warm["all_thread_policies_restored"] is True
            assert warm["representative_payload"]["backend"]["api"] == "fake_public_api"
            assert entry["numerical_comparison"]["relative_l2_error"] == 0.0
            assert entry["cleanup"]["status"] == "completed"


def test_default_campaign_includes_required_assembly_sweep() -> None:
    args = BENCHMARK._parser().parse_args([])
    config = BENCHMARK._config_from_args(args)

    assert config.assembly_threads == (1, 2, 4, 8, 16)
    assert config.solver_threads[0] == 1
    assert config.recovery_threads[0] == 1
    assert (config.linear_nx, config.linear_ny) == (60, 30)
    assert config.repeats >= 2
