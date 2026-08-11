from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "benchmark_sol_ultra_performance.py"
SPEC = importlib.util.spec_from_file_location("_sol_ultra_benchmark_script", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
BENCHMARK = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BENCHMARK
SPEC.loader.exec_module(BENCHMARK)

ASSEMBLY_SCRIPT = ROOT / "scripts" / "benchmark_nonlinear_assembly.py"
ASSEMBLY_SPEC = importlib.util.spec_from_file_location(
    "_nonlinear_assembly_benchmark_script",
    ASSEMBLY_SCRIPT,
)
assert ASSEMBLY_SPEC is not None and ASSEMBLY_SPEC.loader is not None
ASSEMBLY_BENCHMARK = importlib.util.module_from_spec(ASSEMBLY_SPEC)
sys.modules[ASSEMBLY_SPEC.name] = ASSEMBLY_BENCHMARK
ASSEMBLY_SPEC.loader.exec_module(ASSEMBLY_BENCHMARK)


def test_phase_report_uses_stable_complete_vocabulary() -> None:
    invocation = {
        "wall_seconds": 0.25,
        "payload": {
            "timing": {
                "stiffness_assembly_seconds": 0.10,
                "factorization_seconds": 0.05,
            }
        },
    }

    phases = BENCHMARK._phase_report([invocation])

    assert tuple(phases) == BENCHMARK.PHASE_NAMES
    assert phases["linear_K_assembly"] == {
        "available": True,
        "samples_seconds": [0.10],
        "median_seconds": 0.10,
        "minimum_seconds": 0.10,
        "maximum_seconds": 0.10,
        "mean_seconds": 0.10,
        "sources": ["timing.stiffness_assembly_seconds"],
    }
    assert phases["total_wall_time"]["median_seconds"] == 0.25
    assert phases["state_commit"]["available"] is False
    assert phases["state_commit"]["median_seconds"] is None


def test_write_report_emits_json_and_markdown_from_one_payload(tmp_path: Path) -> None:
    report = {
        "schema_name": BENCHMARK.SCHEMA_NAME,
        "schema_version": BENCHMARK.SCHEMA_VERSION,
        "report_kind": "test",
        "generated_at_utc": "2026-08-11T00:00:00Z",
        "revision": {"head_sha": "abc123"},
        "suite": {"name": "selected", "repeats": 1},
        "summary": {"completed_count": 1, "failed_count": 0},
        "environment": {
            "runtime": {"python_version": "3.13.9", "cpu": "test CPU"}
        },
        "cases": [
            {
                "case_id": "example",
                "title": "Example",
                "status": "completed",
                "measurements": {
                    "cold": {"wall_seconds": 0.2},
                    "warm": {
                        "wall_seconds": {"median": 0.1},
                        "python_peak_bytes": {"median": 1024.0},
                    },
                },
                "phases": {
                    "total_wall_time": {
                        "available": True,
                        "median_seconds": 0.1,
                    }
                },
                "representative_warm_payload": {
                    "results": {"relative_error": 0.0}
                },
            }
        ],
        "campaign_context": {
            "qualification": {
                "full_test_suite": {"passed": 624, "wall_seconds": 231.26}
            },
            "setup_incidents": [
                {
                    "stage": "environment",
                    "classification": "setup",
                    "outcome": "corrected",
                }
            ],
        },
        "known_limitations": ["same-machine comparison only"],
    }
    json_path = tmp_path / "report.json"
    markdown_path = tmp_path / "report.md"

    BENCHMARK.write_report(report, json_path, markdown_path)

    written = json.loads(json_path.read_text(encoding="utf-8"))
    assert written["schema_name"] == BENCHMARK.SCHEMA_NAME
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "| `example` | completed | 0.200000s | 0.100000s | 2.000x | 1.00 KiB |" in markdown
    assert "relative_error" in markdown
    assert "624 passed in 231.26s" in markdown
    assert "Setup incidents" in markdown


def test_case_selection_is_ordered_and_rejects_unknown_names() -> None:
    chosen = BENCHMARK._selected_case_ids(
        "full",
        ["large_stress_recovery", "weighted_mpc_panel"],
    )
    assert chosen == ("large_stress_recovery", "weighted_mpc_panel")
    with pytest.raises(ValueError, match="Unknown benchmark case"):
        BENCHMARK._selected_case_ids("smoke", ["not_a_case"])


def test_nonlinear_assembly_benchmark_installs_before_reading_oracle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sentinel = object()
    calls = []

    def install() -> bool:
        calls.append("install")
        monkeypatch.setattr(
            ASSEMBLY_BENCHMARK.nonlinear_performance,
            "_ORIGINAL_ASSEMBLER",
            sentinel,
        )
        return True

    monkeypatch.setattr(
        ASSEMBLY_BENCHMARK,
        "install_nonlinear_performance_optimizations",
        install,
    )
    monkeypatch.setattr(
        ASSEMBLY_BENCHMARK.nonlinear_performance,
        "_ORIGINAL_ASSEMBLER",
        None,
    )

    assert ASSEMBLY_BENCHMARK._ensure_performance_layer() is sentinel
    assert calls == ["install"]


def test_nonlinear_assembly_benchmark_rejects_disabled_layer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        ASSEMBLY_BENCHMARK,
        "install_nonlinear_performance_optimizations",
        lambda: False,
    )
    with pytest.raises(RuntimeError, match="FE_SOLVER_DISABLE_FAST_NL"):
        ASSEMBLY_BENCHMARK._ensure_performance_layer()
