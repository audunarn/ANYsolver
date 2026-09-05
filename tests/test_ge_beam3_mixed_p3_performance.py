"""P3 paired nonintrusion-performance contract checks."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs" / "reference_cases"
GATE_PATH = REFERENCE / "ge_beam3_mixed_p3_package_gate.py"
SPEC = importlib.util.spec_from_file_location("ge_beam3_mixed_p3_perf_gate", GATE_PATH)
assert SPEC is not None and SPEC.loader is not None
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


def _timings(value: float, count: int = 11) -> dict[str, list[float]]:
    return {
        operation: [value * (1.0 + 0.001 * index) for index in range(count)]
        for operation in GATE.OPERATIONS
    }


def test_order_is_paired_alternating_and_requires_eleven_pairs() -> None:
    order = GATE.balanced_orders(11)
    assert len(order) == 11
    assert order[0] == ("base", "candidate")
    assert order[1] == ("candidate", "base")
    assert order[2] == order[0]
    assert sum(pair[0] == "base" for pair in order) == 6
    assert sum(pair[0] == "candidate" for pair in order) == 5
    with pytest.raises(GATE.PackageGateError, match="at least 11"):
        GATE.balanced_orders(10)
    with pytest.raises(GATE.PackageGateError, match="at least 11"):
        GATE.balanced_orders(True)


def test_summary_reports_median_mad_and_fixed_linear_p95() -> None:
    values = [float(index) for index in range(1, 12)]
    summary = GATE.summarize_timings(values)
    assert summary["median"] == 6.0
    assert summary["mad"] == 3.0
    assert summary["p95"] == pytest.approx(10.5)
    with pytest.raises(GATE.PackageGateError, match="finite positive"):
        GATE.summarize_timings(values[:-1])
    with pytest.raises(GATE.PackageGateError, match="finite positive"):
        GATE.summarize_timings([*values[:-1], float("nan")])


def test_adjudication_covers_exact_inventory_and_five_percent_gate() -> None:
    base = _timings(1.0)
    candidate = _timings(1.049)
    accepted = GATE.adjudicate_performance(base, candidate)
    assert accepted["all_operations_pass"] is True
    assert accepted["operations"] == list(GATE.OPERATIONS)
    assert set(accepted["ratios"]) == set(GATE.OPERATIONS)
    assert accepted["maximum_median_ratio"] == "1.05"

    candidate["RECOVERY"] = [1.051 * value for value in base["RECOVERY"]]
    rejected = GATE.adjudicate_performance(base, candidate)
    assert rejected["all_operations_pass"] is False
    assert float(rejected["ratios"]["RECOVERY"]) > 1.05

    missing = dict(base)
    missing.pop("RESTART")
    with pytest.raises(GATE.PackageGateError, match="inventory mismatch"):
        GATE.adjudicate_performance(missing, candidate)

    # Marginal medians can reverse a paired conclusion.  Six of eleven
    # registered pairs regress 2x here, so the paired median must reject even
    # though the ratio of the two marginal medians is less than one.
    base_values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 100.0, 101.0, 102.0, 103.0, 104.0]
    candidate_values = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 0.1, 0.1, 0.1, 0.1, 0.1]
    paired_base = {operation: list(base_values) for operation in GATE.OPERATIONS}
    paired_candidate = {
        operation: list(candidate_values) for operation in GATE.OPERATIONS
    }
    paired_rejected = GATE.adjudicate_performance(
        paired_base, paired_candidate
    )
    assert paired_rejected["all_operations_pass"] is False
    assert float(paired_rejected["ratios"]["SOLVE"]) == pytest.approx(2.0)


def test_frozen_performance_contract_has_no_ge_beam3_speed_gate() -> None:
    contract = json.loads(
        (REFERENCE / "ge_beam3_mixed_p3_contract.json").read_text(encoding="utf-8")
    )
    cases = json.loads(
        (REFERENCE / "ge_beam3_mixed_p3_cases.json").read_text(encoding="utf-8")
    )
    policy = contract["performance_gate"]
    registered = cases["performance"]
    assert policy == {
        "base_commit": GATE.BASE_COMMIT,
        "comparison": "PAIRED_ORDER_BALANCED_BASE_WHEEL_VERSUS_CANDIDATE_WHEEL",
        "existing_b2_b3_maximum_median_regression": "0.05",
        "ge_beam3_speed_ratio": "NOT_GATED",
        "measured_pairs_minimum": 11,
        "raw_timings_noncanonical": True,
        "warmups": 1,
    }
    assert registered["comparison"] == (
        "PAIRED_ORDER_BALANCED_BASE_AND_CANDIDATE_WHEELS"
    )
    assert registered["operations"] == list(GATE.OPERATIONS)
    assert registered["ge_beam3_speed_claim"] == "NONE"
    assert registered["maximum_existing_path_median_ratio"] == "1.05"
    assert registered["raw_fields"] == [
        "WALL_TIME",
        "CPU_TIME",
        "PEAK_RSS",
        "MEDIAN",
        "MAD",
        "P95",
    ]


def test_performance_summary_contains_no_raw_times() -> None:
    summary = GATE.adjudicate_performance(_timings(2.0), _timings(2.0))
    encoded = GATE.canonical_json_bytes(summary)
    assert set(summary) == {
        "all_operations_pass",
        "maximum_median_ratio",
        "operations",
        "ratios",
        "schema",
    }
    for forbidden in (b"wall_time", b"cpu_time", b"peak_rss", b'"mad"', b'"p95"'):
        assert forbidden not in encoded.lower()
    assert b'"ratios"' in encoded


def test_performance_coordinator_runs_warmups_and_eleven_alternating_pairs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, ...]] = []
    runner_bytes = GATE_PATH.read_bytes()

    def fake_git(_repository: Path, *arguments: str) -> str:
        if arguments[0] == "status":
            return ""
        if arguments == ("rev-parse", "HEAD"):
            return "c" * 40
        if arguments == ("rev-parse", "HEAD^{tree}"):
            return "d" * 40
        if arguments == ("rev-parse", GATE.BASE_COMMIT):
            return GATE.BASE_COMMIT
        raise AssertionError(arguments)

    def fake_git_bytes(_repository: Path, *arguments: str) -> bytes:
        assert arguments[:2] == ("cat-file", "blob")
        return runner_bytes

    class FakeTar:
        def __enter__(self) -> "FakeTar":
            return self

        def __exit__(self, *_args: Any) -> None:
            return None

        def extractall(self, path: Path, *, filter: str) -> None:
            assert filter == "data"
            (path / "pyproject.toml").write_text("[build-system]\n", encoding="utf-8")

    def fake_tar_open(*_args: Any, **_kwargs: Any) -> FakeTar:
        return FakeTar()

    def fake_install(
        _wheel: Path,
        environment_root: Path,
        *,
        output_root: Path,
        diagnostics: Path,
        role: str,
        deadline_monotonic: float,
    ) -> Path:
        del output_root, diagnostics, deadline_monotonic
        environment_root.mkdir()
        return environment_root / f"{role}-python"

    def fake_run(
        command: list[str],
        *,
        cwd: Path,
        log_path: Path,
        timeout_seconds: int = GATE.CHILD_TIMEOUT_SECONDS,
        deadline_monotonic: float | None = None,
    ) -> None:
        del cwd, timeout_seconds, deadline_monotonic
        calls.append(tuple(map(str, command)))
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_bytes(b"diagnostic\n")
        if "archive" in command:
            target = next(Path(item.split("=", 1)[1]) for item in command if item.startswith("--output="))
            target.write_bytes(b"archive")
        if "wheel" in command:
            target = Path(command[command.index("--wheel-dir") + 1])
            (target / "ANYsolver-0.4.2-py3-none-any.whl").write_bytes(b"base-wheel")
        if "--performance-probe" in command:
            role = "candidate" if "candidate-environment" in command[0] else "base"
            sample_index = int(command[command.index("--sample-index") + 1])
            timing = 104 if role == "candidate" else 100
            record = {
                "families": {
                    family: {
                        "family": family,
                        "inner_repetitions": GATE.PERFORMANCE_INNER_REPETITIONS,
                        "measurements": {
                            operation: {
                                "cpu_ns_per_call": timing,
                                "wall_ns_per_call": timing,
                            }
                            for operation in GATE.OPERATIONS
                        },
                    }
                    for family in ("B2", "B3")
                },
                "peak_rss_bytes": 1024,
                "sample_index": sample_index,
                "schema": GATE.PERFORMANCE_RAW_SCHEMA,
            }
            output = Path(command[command.index("--output") + 1])
            GATE.write_exclusive(output, record)

    monkeypatch.setattr(GATE, "_git", fake_git)
    monkeypatch.setattr(GATE, "_git_bytes", fake_git_bytes)
    monkeypatch.setattr(GATE.tarfile, "open", fake_tar_open)
    monkeypatch.setattr(GATE, "_install_wheel_environment", fake_install)
    monkeypatch.setattr(GATE, "run_bounded", fake_run)
    monkeypatch.setattr(GATE, "_require_formal_process_containment", lambda: None)
    candidate_wheel = tmp_path / "candidate.whl"
    candidate_wheel.write_bytes(b"candidate-wheel")
    package_record = {
        "candidate_commit": "c" * 40,
        "candidate_tree": "d" * 40,
        "canonical_run_count": 2,
        "correctness_record_sha256": "A" * 64,
        "correctness_records_byte_identical": True,
        "formulation_id": GATE.QUALIFIED_ID,
        "installed_runner_sha256": GATE.sha256_file(GATE_PATH),
        "package_gate_passed": True,
        "process_containment": GATE.PROCESS_CONTAINMENT_ID,
        "schema": GATE.SCHEMA,
        "selector": GATE.SELECTOR,
        "wheel": GATE.assert_regular_wheel(candidate_wheel),
    }
    package_aggregate = tmp_path / "package-aggregate.json"
    GATE.write_exclusive(package_aggregate, package_record)
    output_root = tmp_path / "performance"
    aggregate = GATE.run_performance_gate(
        ROOT,
        candidate_wheel,
        output_root,
        package_aggregate=package_aggregate,
        pair_count=11,
    )
    assert aggregate["all_existing_paths_pass"] is True
    assert aggregate["pair_count"] == 11
    assert aggregate["raw_record_count"] == 22
    assert aggregate["warmup_count_per_role"] == 1
    assert aggregate["ge_beam3_speed_gate"] == "NONE"
    assert aggregate["package_aggregate_sha256"] == GATE.sha256_file(
        package_aggregate
    )
    diagnostics_path = (
        output_root / "diagnostics" / "performance-statistics.json"
    )
    diagnostics = GATE.strict_canonical_json_loads(diagnostics_path.read_bytes())
    assert aggregate["performance_diagnostics_sha256"] == GATE.sha256_file(
        diagnostics_path
    )
    assert diagnostics["families"]["B2"]["candidate"]["operations"]["SOLVE"][
        "wall_ns_per_call"
    ] == {"mad": 0.0, "median": 104.0, "p95": 104.0}
    probes = [call for call in calls if "--performance-probe" in call]
    assert len(probes) == 24
    measured = [
        call for call in probes if call[call.index("--sample-index") + 1] != "-1"
    ]
    assert "base-environment" in measured[0][0]
    assert "candidate-environment" in measured[1][0]
    assert "candidate-environment" in measured[2][0]
    assert "base-environment" in measured[3][0]
    raw = (output_root / "performance-aggregate.json").read_bytes()
    assert GATE.strict_canonical_json_loads(raw) == aggregate
    assert b"wall_ns_per_call" not in raw
    assert b"cpu_ns_per_call" not in raw
    assert b"peak_rss_bytes" not in raw


def test_performance_gate_rejects_wheel_not_bound_by_package_aggregate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    candidate_wheel = tmp_path / "candidate.whl"
    candidate_wheel.write_bytes(b"candidate-wheel")
    package_record = {
        "candidate_commit": "c" * 40,
        "candidate_tree": "d" * 40,
        "canonical_run_count": 2,
        "correctness_record_sha256": "A" * 64,
        "correctness_records_byte_identical": True,
        "formulation_id": GATE.QUALIFIED_ID,
        "installed_runner_sha256": "B" * 64,
        "package_gate_passed": True,
        "process_containment": GATE.PROCESS_CONTAINMENT_ID,
        "schema": GATE.SCHEMA,
        "selector": GATE.SELECTOR,
        "wheel": {
            "bytes": 1,
            "filename": candidate_wheel.name,
            "sha256": "C" * 64,
        },
    }
    package_aggregate = tmp_path / "package-aggregate.json"
    GATE.write_exclusive(package_aggregate, package_record)

    def fake_git(_repository: Path, *arguments: str) -> str:
        if arguments[0] == "status":
            return ""
        if arguments == ("rev-parse", "HEAD"):
            return "c" * 40
        if arguments == ("rev-parse", "HEAD^{tree}"):
            return "d" * 40
        raise AssertionError(arguments)

    monkeypatch.setattr(GATE, "_git", fake_git)
    monkeypatch.setattr(GATE, "_require_formal_process_containment", lambda: None)
    with pytest.raises(GATE.PackageGateError, match="package-gate wheel"):
        GATE.run_performance_gate(
            ROOT,
            candidate_wheel,
            tmp_path / "performance",
            package_aggregate=package_aggregate,
            pair_count=11,
        )
