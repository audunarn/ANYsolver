"""Focused tests for the bounded mixed eigen/performance lane."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
from scipy import sparse


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_mixed_eigen_performance.py"
)
INPUT_PATH = (
    ROOT
    / "docs"
    / "reference_cases"
    / "e4_pl_s3_mixed_eigen_performance_input.json"
)


def _load() -> Any:
    name = "_e4_pl_s3_mixed_eigen_performance_test"
    spec = importlib.util.spec_from_file_location(name, MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def lane() -> Any:
    return _load()


@pytest.fixture(scope="module")
def authorities(lane: Any) -> Any:
    return lane.load_authorities(INPUT_PATH)


def test_input_is_canonical_hash_bound_and_uses_the_frozen_candidate(
    lane: Any, authorities: Any
) -> None:
    raw = INPUT_PATH.read_bytes()
    assert raw == lane.pretty_canonical_bytes(json.loads(raw))
    assert authorities.input_raw == raw
    assert authorities.input["authority"]["candidate"] == {
        "allowed_successor_paths": [
            "docs/reference_cases/e4_pl_s3_mixed_eigen_performance.py",
            "docs/reference_cases/e4_pl_s3_mixed_eigen_performance_input.json",
            "docs/reference_cases/e4_pl_s3_mixed_structural_common.py",
            "docs/reference_cases/e4_pl_s3_mixed_structural_coordinator.py",
            "docs/reference_cases/e4_pl_s3_mixed_structural_input.json",
            "docs/reference_cases/e4_pl_s3_mixed_structural_input_schema.json",
            "docs/reference_cases/e4_pl_s3_mixed_structural_producer.py",
            "tests/test_e4_pl_s3_mixed_eigen_performance.py",
            "tests/test_e4_pl_s3_mixed_structural_qualification.py",
        ],
        "changed_paths": [
            "src/anysolver/matrix_assembly.py",
            "src/anysolver/s3_reference_batch.py",
            "tests/test_e4_pl_s3_reference_batch.py",
        ],
        "commit": "4e5b5976d4286ffd0cda5b8424d154132f3f8da0",
        "parent": "7d85ecef35daa6ebe11f11536a7ede4d288e0aa3",
        "subject": "perf: amortize immutable S3 matrix validation",
        "tree": "96f60dcdd61a78111091ce4f93d7170cf7d0878a",
    }
    assert authorities.input["execution"] == {
        "automatic_retry": False,
        "canonical_cycles": 2,
        "memory_limit_gib_per_process": 24,
        "numerical_library_threads_per_process": 1,
        "performance_workers_are_serial": True,
        "timeout_seconds_per_process": 600,
        "worker_concurrency": 3,
        "worker_ids": list(lane.WORKER_IDS),
    }
    assert authorities.input["coverage"]["performance"] == {
        "comparison": lane.PAIRED_COMPARISON,
        "mixed_fractions_percent": [10, 25],
        "repetitions": 12,
        "rss_isolated_workers": True,
        "schedule": lane.PAIRED_SCHEDULE,
        "warmups_per_route": 1,
    }
    assert authorities.contract["candidate"]["qualified_q4_mechanics_sha256"] == (
        "EE49BAE1C9439C41EC2D61798A8A8B88CBA9081DCAD2DFDC857FE313C6C0D4D1"
    )


def test_duplicate_nonfinite_hash_and_topology_mutations_fail_before_mechanics(
    lane: Any, tmp_path: Path
) -> None:
    raw = INPUT_PATH.read_bytes()
    duplicate = raw.replace(
        b'  "schema": "anysolver.e4-pl-s3-mixed-eigen-performance-input-v1"',
        b'  "schema": "bad",\n  "schema": "anysolver.e4-pl-s3-mixed-eigen-performance-input-v1"',
    )
    duplicate_path = tmp_path / "duplicate.json"
    duplicate_path.write_bytes(duplicate)
    with pytest.raises(lane.EigenPerformanceError, match="duplicate key"):
        lane.load_authorities(duplicate_path)

    payload = json.loads(raw)
    payload["coverage"]["modal"]["shift"] = float("nan")
    with pytest.raises(ValueError):
        lane.pretty_canonical_bytes(payload)

    payload = json.loads(raw)
    payload["authority"]["production_boundary"]["q4_mechanics"][
        "sha256"
    ] = "0" * 64
    mutation = tmp_path / "hash.json"
    mutation.write_bytes(lane.pretty_canonical_bytes(payload))
    with pytest.raises(lane.EigenPerformanceError, match="hash mismatch"):
        lane.load_authorities(mutation)

    payload = json.loads(raw)
    payload["authority"]["candidate"]["changed_paths"] = sorted(
        [
            *payload["authority"]["candidate"]["changed_paths"][:-1],
            "src/anysolver/e4_pl_element.py",
        ]
    )
    extent = tmp_path / "extent.json"
    extent.write_bytes(lane.pretty_canonical_bytes(payload))
    with pytest.raises(lane.EigenPerformanceError, match="changed extent mismatch"):
        lane.load_authorities(extent)

    payload = json.loads(raw)
    payload["authority"]["candidate"]["allowed_successor_paths"] = (
        payload["authority"]["candidate"]["allowed_successor_paths"][:-1]
    )
    successor_extent = tmp_path / "successor-extent.json"
    successor_extent.write_bytes(lane.pretty_canonical_bytes(payload))
    with pytest.raises(
        lane.EigenPerformanceError,
        match="candidate-to-current evidence extent mismatch",
    ):
        lane.load_authorities(successor_extent)

    payload = json.loads(raw)
    payload["authority"]["prior_hot_path_baseline"]["files"][
        "cycle_1_batch"
    ]["sha256"] = "0" * 64
    baseline = tmp_path / "baseline.json"
    baseline.write_bytes(lane.pretty_canonical_bytes(payload))
    with pytest.raises(lane.EigenPerformanceError, match="hash mismatch"):
        lane.load_authorities(baseline)

    payload = json.loads(raw)
    payload["coverage"]["candidate_hot_path_baseline"][
        "maximum_regression"
    ] = "0.06"
    policy = tmp_path / "policy.json"
    policy.write_bytes(lane.pretty_canonical_bytes(payload))
    with pytest.raises(lane.EigenPerformanceError, match="gate policy changed"):
        lane.load_authorities(policy)

    payload = json.loads(raw)
    payload["coverage"]["matched_topologies"]["mixed_10_percent"][
        "connectivity_sha256"
    ] = "A" * 64
    topology = tmp_path / "topology.json"
    topology.write_bytes(lane.pretty_canonical_bytes(payload))
    with pytest.raises(lane.EigenPerformanceError, match="topology 10% mismatch"):
        lane.load_authorities(topology)


def test_registered_free_assemblies_have_exactly_six_scaled_null_roots(
    lane: Any, authorities: Any
) -> None:
    for fraction in (0, 10):
        built = lane._build_case(authorities, fraction, auxiliary=False)
        certificate = lane._free_rigid_certificate(built.model, 10)
        assert certificate["support_state"] == "NO_BOUNDARY_CONDITIONS_APPLIED"
        assert certificate["analytic_basis_columns"] == 6
        assert certificate["analytic_basis_rank"] == 6
        assert certificate["numerical_nullity"] == 6
        assert certificate["first_flexible_root"] > 1.0e-8
        assert certificate["analytic_null_action_residual"] <= 1.0e-12
        assert certificate["passed"] is True


def test_clustered_mac_is_basis_invariant_and_detects_a_changed_subspace(
    lane: Any
) -> None:
    reference = np.asarray(
        (
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
            (0.0, 0.0, 0.0),
        )
    )
    angle = 0.37
    rotation = np.asarray(
        (
            (np.cos(angle), -np.sin(angle)),
            (np.sin(angle), np.cos(angle)),
        )
    )
    candidate = reference.copy()
    candidate[:, :2] = reference[:, :2] @ rotation
    values = (1.0, 1.0 + 1.0e-6, 3.0)
    result = lane._clustered_mac(
        reference,
        candidate,
        sparse.eye(4, format="csr"),
        values,
        1.0e-4,
    )
    assert result["minimum_clustered_mac"] == pytest.approx(1.0, abs=2.0e-15)

    candidate[:, 2] = np.asarray((0.0, 0.0, 0.0, 1.0))
    changed = lane._clustered_mac(
        reference,
        candidate,
        sparse.eye(4, format="csr"),
        values,
        1.0e-4,
    )
    assert changed["minimum_clustered_mac"] == pytest.approx(0.0)


def test_physical_global_buckling_prestress_is_transformed_per_element_frame(
    lane: Any, authorities: Any
) -> None:
    built = lane._build_case(authorities, 10, auxiliary=False)
    spec = authorities.input["coverage"]["buckling"]
    states = lane._reference_elastic_states(built.model, spec)
    global_tensor = np.asarray(
        spec["physical_global_membrane_compression_tensor"], dtype=float
    )
    observed_local: set[tuple[float, float, float]] = set()
    for element_id, element in built.model.mesh.elements.items():
        material = built.model.get_material(element.material_name)
        frame = np.asarray(
            element.compute_stiffness_components(built.model.mesh, material)["frame"],
            dtype=float,
        )
        expected = frame[:, :2].T @ global_tensor @ frame[:, :2]
        state = states[int(element_id)]
        actual = np.asarray(state["membrane_compression"], dtype=float)
        np.testing.assert_allclose(
            actual,
            (expected[0, 0], expected[1, 1], expected[0, 1]),
            rtol=0.0,
            atol=4.0e-16,
        )
        np.testing.assert_allclose(
            state["stress_second_moment"],
            actual * float(element.thickness) ** 2 / 12.0,
            rtol=0.0,
            atol=4.0e-20,
        )
        observed_local.add(tuple(round(float(value), 12) for value in actual))
    assert {(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.5, 0.5, -0.5)} <= observed_local


def test_production_buckling_worker_passes_the_physical_global_n20_gate(
    lane: Any, authorities: Any
) -> None:
    record = lane.run_worker(authorities, "BUCKLING_MIXED_10")
    lane.validate_worker(record, "BUCKLING_MIXED_10")
    statuses = record["common"]["gate_status"]
    assert statuses["buckling_factors"] == lane.PASS
    assert statuses["buckling_mac"] == lane.PASS
    assert statuses["buckling_positive"] == lane.PASS
    diagnostics = record["diagnostic_payload"]
    assert diagnostics["fraction_percent"] == 10
    assert len(diagnostics["reference_factors"]) == 5
    assert len(diagnostics["candidate_factors"]) == 5
    assert diagnostics["maximum_factor_relative_error"] < 0.003
    assert diagnostics["clustered_mac"]["minimum_clustered_mac"] >= 0.95
    assert "all boundary nodes constrain ux, uy, uz" in diagnostics[
        "boundary_construction"
    ]


def _fake_worker(
    lane: Any,
    authorities: Any,
    worker_id: str,
    statuses: dict[str, str],
    diagnostics: dict[str, Any],
) -> dict[str, Any]:
    common = {
        "gate_status": statuses,
        "production_restriction": lane.PRODUCTION_RESTRICTION,
        "worker_id": worker_id,
    }
    return {
        "authority_sha256": lane.sha256(authorities.input_raw),
        "common": common,
        "diagnostic_payload": diagnostics,
        "diagnostic_payload_sha256": lane.sha256(lane.canonical_bytes(diagnostics)),
        "schema": lane.WORKER_SCHEMA,
        "worker_id": worker_id,
    }


def _paired_diagnostics(
    lane: Any,
    *,
    assembly_ratios: dict[int, float] | None = None,
    solve_ratios: dict[int, float] | None = None,
) -> dict[str, Any]:
    ratios = {
        "assembly": assembly_ratios or {10: 1.01, 25: 1.02},
        "production_end_to_end_solve": solve_ratios or {10: 1.01, 25: 1.02},
    }
    records = {
        route: {fraction: [] for fraction in lane.MIXED_FRACTIONS}
        for route in lane.PERFORMANCE_ROUTES
    }
    for row in lane._paired_schedule(lane.PAIRED_REPETITIONS):
        route = row["route"]
        fraction = row["fraction_percent"]
        reference_ns = 1_000_000_000 + 1_000_000 * int(row["repetition"])
        candidate_ns = int(round(reference_ns * ratios[route][fraction]))
        records[route][fraction].append(
            {
                "candidate_cpu_ns": candidate_ns,
                "candidate_wall_ns": candidate_ns,
                "order": list(row["order"]),
                "reference_cpu_ns": reference_ns,
                "reference_wall_ns": reference_ns,
                "repetition": int(row["repetition"]),
            }
        )
    return {
        "comparisons": {
            route: {
                str(fraction): lane._paired_comparison(records[route][fraction])
                for fraction in lane.MIXED_FRACTIONS
            }
            for route in lane.PERFORMANCE_ROUTES
        },
        "protocol": {
            "comparison": lane.PAIRED_COMPARISON,
            "repetitions": lane.PAIRED_REPETITIONS,
            "schedule": lane.PAIRED_SCHEDULE,
            "warmups_per_topology_route": 1,
        },
        "topologies": {},
        "worker_elapsed_seconds": 1.0,
    }


def test_paired_schedule_is_adjacent_and_fully_position_balanced(lane: Any) -> None:
    rows = lane._paired_schedule(lane.PAIRED_REPETITIONS)
    assert len(rows) == lane.PAIRED_REPETITIONS * 4
    for route in lane.PERFORMANCE_ROUTES:
        for fraction in lane.MIXED_FRACTIONS:
            selected = [
                row
                for row in rows
                if row["route"] == route
                and row["fraction_percent"] == fraction
            ]
            assert len(selected) == lane.PAIRED_REPETITIONS
            assert sum(row["order"] == [0, fraction] for row in selected) == 6
            assert sum(row["order"] == [fraction, 0] for row in selected) == 6
    pair_positions = {route: {10: 0, 25: 0} for route in lane.PERFORMANCE_ROUTES}
    route_positions = {route: 0 for route in lane.PERFORMANCE_ROUTES}
    for repetition in range(lane.PAIRED_REPETITIONS):
        repetition_rows = [row for row in rows if row["repetition"] == repetition]
        route_order = list(dict.fromkeys(row["route"] for row in repetition_rows))
        assert set(route_order) == set(lane.PERFORMANCE_ROUTES)
        route_positions[route_order[0]] += 1
        for route in lane.PERFORMANCE_ROUTES:
            route_rows = [row for row in repetition_rows if row["route"] == route]
            assert len(route_rows) == 2
            pair_positions[route][route_rows[0]["fraction_percent"]] += 1
    assert route_positions == {route: 6 for route in lane.PERFORMANCE_ROUTES}
    assert pair_positions == {
        route: {10: 6, 25: 6} for route in lane.PERFORMANCE_ROUTES
    }


def test_paired_collection_warms_each_topology_route_once_and_recomputes(
    lane: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    built = {0: "q4", 10: "mixed10", 25: "mixed25"}
    fraction_by_model = {model: fraction for fraction, model in built.items()}
    warmups: list[tuple[str, str]] = []
    measured: list[tuple[str, str]] = []

    def execute(model: str, route: str) -> None:
        warmups.append((model, route))

    def timed(model: str, route: str) -> tuple[int, int]:
        measured.append((model, route))
        fraction = fraction_by_model[model]
        wall = {0: 1_000_000_000, 10: 1_050_000_000, 25: 1_090_000_000}[
            fraction
        ]
        return wall, wall

    monkeypatch.setattr(lane, "_execute_performance_route", execute)
    monkeypatch.setattr(lane, "_timed_performance_route", timed)
    comparisons = lane._collect_paired_measurements(
        built,
        repetitions=lane.PAIRED_REPETITIONS,
        warmups_per_route=1,
    )
    assert warmups == [
        (built[fraction], route)
        for fraction in lane.PERFORMANCE_FRACTIONS
        for route in lane.PERFORMANCE_ROUTES
    ]
    assert len(measured) == lane.PAIRED_REPETITIONS * 8
    record = {
        "diagnostic_payload": {
            "comparisons": comparisons,
            "protocol": {
                "comparison": lane.PAIRED_COMPARISON,
                "repetitions": lane.PAIRED_REPETITIONS,
                "schedule": lane.PAIRED_SCHEDULE,
                "warmups_per_topology_route": 1,
            },
        }
    }
    metrics = lane._validated_paired_metrics(
        record,
        repetitions=lane.PAIRED_REPETITIONS,
        warmups_per_route=1,
    )
    assert metrics == {
        "assembly": {10: 1.05, 25: 1.09},
        "production_end_to_end_solve": {10: 1.05, 25: 1.09},
    }


def test_paired_statistic_uses_adjacent_ratios_and_common_slow_epochs_cancel(
    lane: Any,
) -> None:
    records = []
    reference_values = [101, 1, 100]
    candidate_values = [106, 2, 50]
    for repetition, (reference, candidate) in enumerate(
        zip(reference_values, candidate_values, strict=True)
    ):
        multiplier = 10 if repetition == 1 else 1
        records.append(
            {
                "candidate_cpu_ns": candidate * multiplier,
                "candidate_wall_ns": candidate * multiplier,
                "order": [0, 10],
                "reference_cpu_ns": reference * multiplier,
                "reference_wall_ns": reference * multiplier,
                "repetition": repetition,
            }
        )
    comparison = lane._paired_comparison(records)
    assert comparison["paired_ratio"]["median"] == pytest.approx(
        106.0 / 101.0
    )
    assert comparison["reference"]["samples_seconds"] == pytest.approx(
        [101.0e-9, 10.0e-9, 100.0e-9]
    )
    independent_ratio = (
        comparison["candidate"]["median_seconds"]
        / comparison["reference"]["median_seconds"]
    )
    assert independent_ratio != pytest.approx(
        comparison["paired_ratio"]["median"]
    )


def test_paired_gate_accepts_exact_boundary_and_rejects_candidate_slowdown(
    lane: Any,
) -> None:
    diagnostics = _paired_diagnostics(
        lane,
        assembly_ratios={10: 1.10, 25: 1.10},
        solve_ratios={10: 1.10, 25: 1.1001},
    )
    metrics = lane._validated_paired_metrics(
        {"diagnostic_payload": diagnostics},
        repetitions=lane.PAIRED_REPETITIONS,
        warmups_per_route=1,
    )
    assert lane._ratio_gate(metrics["assembly"][10], 1.10) == lane.PASS
    assert lane._ratio_gate(metrics["production_end_to_end_solve"][10], 1.10) == (
        lane.PASS
    )
    assert lane._ratio_gate(metrics["production_end_to_end_solve"][25], 1.10) == (
        lane.FAIL
    )


@pytest.mark.parametrize("mutation", ["order", "summary", "zero"])
def test_paired_record_mutations_block_recomputation(
    lane: Any, mutation: str
) -> None:
    diagnostics = _paired_diagnostics(lane)
    comparison = diagnostics["comparisons"]["assembly"]["10"]
    if mutation == "order":
        comparison["pairs"][0]["order"] = [10, 0]
    elif mutation == "summary":
        comparison["paired_ratio"]["median"] *= 2.0
    else:
        comparison["pairs"][0]["reference_wall_ns"] = 0
    with pytest.raises(lane.EigenPerformanceError):
        lane._validated_paired_metrics(
            {"diagnostic_payload": diagnostics},
            repetitions=lane.PAIRED_REPETITIONS,
            warmups_per_route=1,
        )


def test_nonconverged_or_nonfinite_solve_is_not_a_timing_sample(
    lane: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    import anysolver.assembly as assembly

    built = SimpleNamespace(model=object(), load_case=object())
    monkeypatch.setattr(
        assembly,
        "solve_linear",
        lambda *_args, **_kwargs: (
            [0.0],
            {"convergence_info": {"status": "failed"}},
        ),
    )
    with pytest.raises(lane.EigenPerformanceError, match="did not converge"):
        lane._execute_performance_route(built, "production_end_to_end_solve")

    monkeypatch.setattr(
        assembly,
        "solve_linear",
        lambda *_args, **_kwargs: (
            [float("nan")],
            {"convergence_info": {"status": "converged"}},
        ),
    )
    with pytest.raises(lane.EigenPerformanceError, match="nonfinite"):
        lane._execute_performance_route(built, "production_end_to_end_solve")


def test_rss_worker_is_isolated_and_emits_no_timing_classification(
    lane: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    authorities = SimpleNamespace(
        input={
            "coverage": {
                "performance": {
                    "repetitions": lane.PAIRED_REPETITIONS,
                    "warmups_per_route": 1,
                }
            }
        }
    )
    built = object()
    calls: list[str] = []
    monkeypatch.setattr(lane, "_build_case", lambda *_args, **_kwargs: built)
    monkeypatch.setattr(
        lane, "_execute_performance_route", lambda _built, route: calls.append(route)
    )
    monkeypatch.setattr(lane, "_peak_rss_bytes", lambda: 123456)
    monkeypatch.setattr(
        lane,
        "_topology_diagnostics",
        lambda *_args, **_kwargs: {"fraction_percent": 25},
    )
    statuses, diagnostics = lane._rss_worker(authorities, 25)
    assert statuses == {"rss_measurement": lane.PASS}
    assert diagnostics["peak_rss_bytes"] == 123456
    assert "assembly" not in diagnostics
    assert "production_end_to_end_solve" not in diagnostics
    assert calls.count("assembly") == lane.PAIRED_REPETITIONS + 1
    assert calls.count("production_end_to_end_solve") == (
        lane.PAIRED_REPETITIONS + 1
    )


def test_aggregate_is_deterministic_excludes_timings_and_closes_hot_path_gate(
    lane: Any, tmp_path: Path
) -> None:
    authorities = SimpleNamespace(
        contract={
            "acceptance_gates": {
                "performance": {
                    "mixed_assembly_solve_rss_regression_maximum": "0.10"
                }
            }
        },
        hot_path_baseline_cycles=(),
        input={
            "coverage": {
                "candidate_hot_path_baseline": {
                    "maximum_regression": "0.05",
                    "reference_selection": "TEST_HASH_BOUND_ENVELOPE",
                    "secondary_guard": "TEST_WARM_S3_VS_Q4",
                },
                "performance": {
                    "repetitions": lane.PAIRED_REPETITIONS,
                    "warmups_per_route": 1,
                },
            }
        },
        input_raw=b"paired-aggregate-authority\n",
    )
    process_results = []
    worker_records: dict[str, dict[str, Any]] = {}
    for index, worker_id in enumerate(lane.WORKER_IDS):
        directory = tmp_path / worker_id.lower()
        directory.mkdir()
        if worker_id.startswith("MODAL_"):
            statuses = {
                "modal_frequency": lane.PASS,
                "modal_mac": lane.PASS,
                "rigid_modes": lane.PASS,
            }
            diagnostics = {"worker_elapsed_seconds": 0.01 + index}
        elif worker_id.startswith("BUCKLING_"):
            statuses = {
                "buckling_factors": lane.PASS,
                "buckling_mac": lane.PASS,
                "buckling_positive": lane.PASS,
            }
            diagnostics = {"worker_elapsed_seconds": 0.01 + index}
        elif worker_id == "PERFORMANCE_PAIRED":
            statuses = {"performance_measurement": lane.PASS}
            diagnostics = _paired_diagnostics(lane)
        elif worker_id.startswith("RSS_"):
            fraction = 0 if worker_id.endswith("ALL_Q4") else int(
                worker_id.rsplit("_", 1)[1]
            )
            statuses = {"rss_measurement": lane.PASS}
            diagnostics = {
                "fraction_percent": fraction,
                "peak_rss_bytes": 1000 + fraction,
                "worker_elapsed_seconds": 10.0 + index,
            }
        else:
            statuses = {
                "batch_equality": lane.PASS,
                "batch_scalar_fallback": lane.PASS,
                "batch_throughput": lane.PASS,
                "warm_s3_vs_q4": lane.PASS,
            }
            diagnostics = {
                "benchmark": {
                    "qualified_q4_comparator": {
                        "batch": {"median_seconds": 1.0}
                    },
                    "recovery": {
                        "batch": {"median_seconds": 0.1},
                        "scalar": {"median_seconds": 1.0},
                    },
                    "stiffness": {
                        "batch": {"median_seconds": 0.04},
                        "scalar": {"median_seconds": 0.2},
                    },
                },
                "worker_elapsed_seconds": 99.0,
            }
        worker_record = _fake_worker(
            lane, authorities, worker_id, statuses, diagnostics
        )
        worker_records[worker_id] = worker_record
        lane.write_exclusive(directory / "record.json", worker_record)
        (directory / "stdout.log").write_bytes(b"")
        (directory / "stderr.log").write_bytes(b"")
        process_results.append(
            lane.ProcessResult(
                worker_id=worker_id,
                status="COMPLETE",
                returncode=0,
                elapsed_seconds=100.0 + index,
                peak_rss_bytes=5000 + index,
                directory=directory,
            )
        )
    authorities.hot_path_baseline_cycles = (worker_records, worker_records)
    first, first_diagnostics = lane._aggregate(authorities, 1, process_results)
    second, second_diagnostics = lane._aggregate(authorities, 2, process_results)
    assert lane.canonical_bytes(first) == lane.canonical_bytes(second)
    assert first["gate_status"]["candidate_hot_path_regression"] == lane.PASS
    assert first["terminal"] == lane.TERMINALS[3]
    comparison = first_diagnostics["candidate_hot_path_comparison"]
    assert comparison["primary_metric"]["metric"] == lane.HOT_PATH_PRIMARY_METRIC
    assert comparison["primary_metric"]["gate_status"] == lane.PASS
    assert tuple(comparison["normalized_diagnostics"]) == (
        lane.HOT_PATH_DIAGNOSTIC_METRICS
    )
    performance = first_diagnostics["performance_comparison"]
    assert performance["10"]["assembly_paired_median_ratio_to_all_q4"] == (
        pytest.approx(1.01)
    )
    assert performance["25"]["solve_paired_median_ratio_to_all_q4"] == (
        pytest.approx(1.02)
    )
    assert "seconds" not in lane.canonical_bytes(first).decode("ascii")
    assert first_diagnostics != second_diagnostics


@pytest.mark.parametrize(
    ("cycle_terminals", "expected_terminal"),
    [
        ((3, 3), 3),
        ((1, 1), 1),
        ((3, 1), 0),
    ],
)
def test_two_cycle_precedence_never_averages_or_selects_a_cycle(
    lane: Any,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    cycle_terminals: tuple[int, int],
    expected_terminal: int,
) -> None:
    cycle_values = [
        {
            "authority_sha256": "A" * 64,
            "gate_status": {"mixed_performance": lane.PASS if index == 3 else lane.FAIL},
            "production_restriction": lane.PRODUCTION_RESTRICTION,
            "schema": lane.COMMON_SCHEMA,
            "terminal": lane.TERMINALS[index],
        }
        for index in cycle_terminals
    ]
    calls = iter(cycle_values)

    def fake_cycle(
        _authorities: Any, _output: Path, *, cycle: int
    ) -> tuple[bytes, dict[str, Any], dict[str, Any]]:
        assert cycle in (1, 2)
        value = next(calls)
        return lane.canonical_bytes(value), value, {}

    monkeypatch.setattr(lane, "run_cycle", fake_cycle)
    result = lane.run_two_cycles(
        SimpleNamespace(input_raw=b"paired-authority\n"),
        tmp_path / "two-cycles",
    )
    assert result["terminal"] == lane.TERMINALS[expected_terminal]
    assert result["cycles_byte_identical"] is (cycle_terminals[0] == cycle_terminals[1])


def test_candidate_hot_path_gate_rejects_a_regressed_normalized_metric(
    lane: Any, authorities: Any
) -> None:
    accepted = copy.deepcopy(authorities.hot_path_baseline_cycles[0])
    status, diagnostics = lane._candidate_hot_path_gate(authorities, accepted)
    assert status == lane.PASS
    assert diagnostics["primary_metric"]["gate_status"] == lane.PASS
    assert diagnostics["primary_metric"]["baseline_cycle_values"] == pytest.approx(
        [0.061557499997434206, 0.06595939999533584],
        rel=0.0,
        abs=0.0,
    )
    assert diagnostics["primary_metric"]["gate_limit"] == pytest.approx(
        0.06595939999533584 * 1.05,
        rel=0.0,
        abs=0.0,
    )

    diagnostic_only = copy.deepcopy(accepted)
    diagnostic_only["PERFORMANCE_MIXED_10"]["diagnostic_payload"]["assembly"][
        "median_seconds"
    ] *= 2.0
    status, changed_diagnostics = lane._candidate_hot_path_gate(
        authorities, diagnostic_only
    )
    assert status == lane.PASS
    assert changed_diagnostics["normalized_diagnostics"][
        "mixed_10_assembly_ratio_to_all_q4"
    ]["candidate_value"] > diagnostics["normalized_diagnostics"][
        "mixed_10_assembly_ratio_to_all_q4"
    ]["candidate_value"]

    regressed = copy.deepcopy(accepted)
    regressed["BATCH_4096"]["diagnostic_payload"]["benchmark"]["stiffness"][
        "batch"
    ][
        "median_seconds"
    ] *= 2.0
    status, diagnostics = lane._candidate_hot_path_gate(authorities, regressed)
    assert status == lane.FAIL
    assert diagnostics["primary_metric"]["gate_status"] == lane.FAIL


def test_timeout_terminates_worker_and_removes_partial_canonical_output(
    lane: Any, tmp_path: Path
) -> None:
    directory = tmp_path / "timeout-worker"
    code = (
        "from pathlib import Path; import sys,time; "
        "Path(sys.argv[1]).write_text('{}'); time.sleep(5)"
    )
    result = lane.run_bounded_process(
        "TIMEOUT_TEST",
        [sys.executable, "-c", code, str(directory / "record.json")],
        directory=directory,
        environment={**os.environ, **lane.THREAD_ENVIRONMENT},
        timeout_seconds=1,
        memory_limit_bytes=1 << 30,
        rss_reader=lambda _pid: 1,
    )
    assert result.status == "TIMEOUT"
    assert not (directory / "record.json").exists()


def test_default_s3_remains_legacy_and_q4_mechanics_is_unchanged(
    authorities: Any,
) -> None:
    from anysolver.elements import DEFAULT_S3_FORMULATION

    assert DEFAULT_S3_FORMULATION == "legacy-s3"
    q4 = ROOT / "src" / "anysolver" / "e4_pl_element.py"
    assert authorities.input["authority"]["production_boundary"]["q4_mechanics"][
        "sha256"
    ] == (
        __import__("hashlib").sha256(q4.read_bytes()).hexdigest().upper()
    )
    changed = set(authorities.input["authority"]["candidate"]["changed_paths"])
    boundary = authorities.input["authority"]["production_boundary"]
    assert changed.isdisjoint(row["path"] for row in boundary.values())
    for row in boundary.values():
        path = ROOT / row["path"]
        assert path.stat().st_size == row["bytes"]
        assert __import__("hashlib").sha256(path.read_bytes()).hexdigest().upper() == (
            row["sha256"]
        )


def test_cli_requires_exclusive_mode_and_output(lane: Any) -> None:
    with pytest.raises(SystemExit):
        lane.main([])
    with pytest.raises(SystemExit):
        lane.main(["--worker", "BATCH_4096"])
