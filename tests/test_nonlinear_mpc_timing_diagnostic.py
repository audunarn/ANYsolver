from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/diagnose_nonlinear_mpc_timing.py"


def _module():
    spec = importlib.util.spec_from_file_location(
        "mpc_timing_diagnostic",
        SCRIPT,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sample(route: float, solver: float) -> dict:
    return {
        "complete_route_wall_seconds": route,
        "solver_seconds": solver,
        "physical_sha256": "same-physics",
        "work": {"iterations": 32},
    }


def test_summary_separates_route_solver_and_build_time() -> None:
    result = _module().summarize_pairs(
        [
            {
                "baseline": _sample(1.0, 0.8),
                "candidate": _sample(0.8, 0.7),
            },
            {
                "baseline": _sample(1.2, 0.9),
                "candidate": _sample(1.0, 0.8),
            },
        ]
    )
    assert result["physical_match"] is True
    assert result["work_match"] is True
    assert result["route_seconds"][
        "separate_median_reduction_fraction"
    ] == pytest.approx(0.18181818181818182)
    assert result["solver_seconds"][
        "separate_median_reduction_fraction"
    ] == pytest.approx(0.11764705882352942)
    assert result["model_build_seconds"]["baseline"]["median"] == (
        pytest.approx(0.25)
    )


def test_summary_detects_physics_or_work_differences() -> None:
    left = _sample(1.0, 0.8)
    right = _sample(1.0, 0.8)
    right["physical_sha256"] = "different-physics"
    right["work"] = {"iterations": 33}
    result = _module().summarize_pairs(
        [{"baseline": left, "candidate": right}]
    )
    assert result["physical_match"] is False
    assert result["work_match"] is False
    assert result["route_seconds"]["baseline"]["q1"] == 1.0
    assert result["route_seconds"]["baseline"]["q3"] == 1.0
