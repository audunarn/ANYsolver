"""Freeze the S4-improved scientific and performance qualification contract."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_s4_improved_qualification.py"
SPEC = importlib.util.spec_from_file_location("_s4_improved_qualification", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
QUALIFICATION = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = QUALIFICATION
SPEC.loader.exec_module(QUALIFICATION)

BENCHMARK_SCRIPT = ROOT / "scripts" / "benchmark_s4_improved.py"
BENCHMARK_SPEC = importlib.util.spec_from_file_location(
    "_s4_improved_benchmark", BENCHMARK_SCRIPT
)
assert BENCHMARK_SPEC is not None and BENCHMARK_SPEC.loader is not None
BENCHMARK = importlib.util.module_from_spec(BENCHMARK_SPEC)
sys.modules[BENCHMARK_SPEC.name] = BENCHMARK
BENCHMARK_SPEC.loader.exec_module(BENCHMARK)


def test_qualification_contract_is_hashed_and_complete() -> None:
    QUALIFICATION.validate_contract()
    contract = QUALIFICATION.qualification_contract()

    assert contract["theory"] == "full_2x2_mitc4_plus_d"
    assert contract["geometry_boundary"] == {
        "api": ">=0.2,<0.3",
        "live_observed": "0.2.1",
        "forward_schema": 4,
        "legacy_schema": 3,
        "solver_document_parsing": False,
        "live_geometry_hot_loop_calls_allowed": False,
    }
    assert contract["sweeps"]["slenderness_L_over_t"] == [
        10,
        30,
        100,
        300,
        1000,
        3000,
        10000,
        30000,
    ]
    assert contract["sweeps"]["aspect_ratio"] == [1, 2, 5, 10, 20]
    assert contract["sweeps"]["distortion_sequences"] == {
        "skew_offset_over_height": [0.0, 0.10, 0.25, 0.50, 0.75],
        "taper_top_over_bottom": [1.0, 0.80, 0.60, 0.40, 0.25],
        "warpage_over_short_edge": [0.0, 0.01, 0.03, 0.07, 0.12],
    }
    assert contract["fixtures"]["mass_case"] == {
        "coordinates_fixture": "square",
        "thickness": 0.020,
        "density": 7850.0,
        "expected_total_mass": 314.0,
        "expected_centre_of_mass": [1.0, 0.5, 0.0],
    }
    assert (
        contract["fixtures"]["warped_coordinates"]["strong_valid_warp"][2]
        == [2.0, 1.0, 0.25]
    )
    families = {case["family"] for case in contract["cases"]}
    assert families == {
        "algebra",
        "patch",
        "locking_distortion",
        "linear",
        "modal_mass",
        "buckling",
        "nonlinear",
        "materials",
        "coupling_source_intent",
        "geometry_handoff",
        "recovery",
    }


def test_contract_rejects_an_unreviewed_tolerance_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    changed = dict(QUALIFICATION.TOLERANCES)
    changed["compiled_relative_linf"] = {
        **changed["compiled_relative_linf"],
        "limit": 1.0e-6,
    }
    monkeypatch.setattr(QUALIFICATION, "TOLERANCES", changed)

    with pytest.raises(RuntimeError, match="changed without updating"):
        QUALIFICATION.validate_contract()


def test_list_mode_is_read_only_and_json_serializable(capsys: pytest.CaptureFixture[str]) -> None:
    assert QUALIFICATION.main(["--list"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["contract_sha256"] == QUALIFICATION.QUALIFICATION_CONTRACT_SHA256
    assert payload["full_requires_perf_lease"] is True


def test_full_qualification_and_eleven_sample_benchmark_require_a_perf_lease(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(QUALIFICATION.PERF_LEASE_ENV, raising=False)
    with pytest.raises(SystemExit, match="requires an ecosystem PERF lease"):
        QUALIFICATION.main(["--full", "--perf-lease", ""])
    with pytest.raises(SystemExit, match="requires --perf-lease"):
        BENCHMARK.main(["--repeats", "11", "--perf-lease", ""])


def test_benchmark_protocol_uses_all_frozen_kernel_hard_gates() -> None:
    manifest = BENCHMARK.benchmark_manifest()
    assert manifest["protocol"] == {
        "warm_jit_outside_timing": True,
        "paired_adjacent_samples": True,
        "balanced_pair_order": True,
        "full_minimum_repeats": 11,
        "default_numba_threads": 1,
        "live_geometry_calls_allowed": 0,
        "unavailable_is_pass": False,
    }
    assert {case["case_id"] for case in manifest["cases"]} == {
        "linear_K",
        "mass",
        "KG",
        "elastic_residual_tangent",
        "direct_reduced_residual_tangent",
        "plastic_residual_tangent",
        "recovery",
        "retained_bytes",
    }


def test_paired_samples_preserve_adjacent_balanced_order() -> None:
    calls: list[str] = []

    def baseline() -> None:
        calls.append("b")

    def candidate() -> None:
        calls.append("c")

    result = BENCHMARK.paired_samples(
        baseline,
        candidate,
        repeats=3,
        warmup=False,
    )

    assert calls == ["b", "c", "c", "b", "b", "c"]
    assert result["pair_order"] == [
        "baseline_candidate",
        "candidate_baseline",
        "baseline_candidate",
    ]
    assert len(result["baseline"]["samples"]) == 3
    assert len(result["candidate"]["samples"]) == 3
