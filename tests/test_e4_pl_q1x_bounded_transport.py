from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import ast
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
sys.path.insert(0, str(REFERENCE_CASES))

import e4_pl_q1x_bounded_runner as runner
import e4_pl_q1x_common as common
import e4_pl_q1x_transport_checker as checker
import e4_pl_q1x_transport_producer as producer


CONTRACT = REFERENCE_CASES / "e4_pl_q1x_transport_contract.json"
CONTRACT_SHA = common.sha256(CONTRACT.read_bytes())
PRODUCER = REFERENCE_CASES / "e4_pl_q1x_transport_producer.py"
CHECKER = REFERENCE_CASES / "e4_pl_q1x_transport_checker.py"
RESULT = REFERENCE_CASES / "e4_pl_q1x_bounded_result.json"


def _external_inputs() -> tuple[Path, Path]:
    historical = os.environ.get("Q1X_HISTORICAL_REFERENCE")
    environment = os.environ.get("Q1X_EXACT_ENV_ROOT")
    if not historical or not environment:
        pytest.skip("Q1X preserved wrapper and exact SymPy environment are not configured")
    return Path(historical), Path(environment)


def test_q1x_contract_backend_and_source_boundary_are_exact() -> None:
    raw, value = common.read_json(CONTRACT)
    assert raw == common.canonical_bytes(value)
    checked = common.validate_contract(ROOT, CONTRACT, CONTRACT_SHA)
    assert checked["geometry_ids"] == list(common.GEOMETRY_IDS)
    assert checked["operation_ids"] == list(common.OPERATION_IDS)
    assert len(checked["geometry_ids"]) * len(checked["operation_ids"]) == 56
    primitive_raw, primitive = common.read_json(REFERENCE_CASES / "e4_pl_q1x_primitive_fields.json")
    assert primitive_raw == common.canonical_bytes(primitive)
    assert sorted(item for row in primitive["fields"] for item in row["geometry_ids"]) == sorted(common.GEOMETRY_IDS)
    result_raw, result = common.read_json(RESULT)
    assert result_raw == common.canonical_bytes(result)
    assert result["transport_contract_sha256"] == CONTRACT_SHA
    assert result["aggregate"] == {
        "bytes": 5584,
        "cycles": 2,
        "external_role": "PRESERVED_Q1X_BOUNDED_TRANSPORT_EVIDENCE",
        "sha256": "0EB174F50F5930E52F6A5B8CEDCAA69562F3A23F1CDC05777CF00662F846A476",
        "two_cycle_byte_identical": True,
    }
    assert result["coverage"] == {"case_count": 56, "geometry_count": 7, "station_count": 224}
    assert result["terminal"] == "UNCLASSIFIED_E4_PL_Q1X_TRANSPORT_CLOSED_ONLY"
    assert result["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert result["q1b_execution"] == "UNAUTHORIZED"

    field = producer.Field()
    field, root2 = field.with_sqrt(field.rational(2))
    nested_radicand = field.rational(3) + root2
    field, nested = field.with_sqrt(nested_radicand)
    root2 = root2.lift(field)
    nested_radicand = nested_radicand.lift(field)
    left = field.rational(5) + root2 + nested
    right = field.rational(7) - root2 + 2 * nested
    third = field.rational(2) + root2 * nested
    assert root2 * root2 == field.rational(2)
    assert nested * nested == nested_radicand
    assert left * right == right * left
    assert (left * right) * third == left * (right * third)
    assert left * (right + third) == left * right + left * third
    assert left * left.inverse() == field.rational(1)
    assert left.inverse() * left == field.rational(1)

    checker_source = CHECKER.read_text(encoding="utf-8")
    checker_tree = ast.parse(checker_source)
    imported = {
        alias.name
        for node in ast.walk(checker_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(checker_tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert "e4_pl_q1x_transport_producer" not in imported
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"evalf", "simplify"}
        for node in ast.walk(checker_tree)
    )
    changed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.splitlines()
    changed = [row[3:].replace("\\", "/") for row in changed]
    assert not any(path == "pyproject.toml" or path == ".gitattributes" or path.startswith(("src/", ".github/")) for path in changed)


def test_q1x_three_processes_overlap_and_incomplete_outputs_are_removed(tmp_path: Path) -> None:
    environment = os.environ.copy()

    def sleep_job(index: int) -> runner.ProcessResult:
        directory = tmp_path / f"worker-{index}"
        directory.mkdir()
        return runner.run_bounded_process(
            [sys.executable, "-c", "import time; time.sleep(0.25)"],
            cwd=ROOT,
            environment=environment,
            stdout_path=directory / "stdout.log",
            stderr_path=directory / "stderr.log",
            timeout_seconds=2,
            memory_limit_bytes=1024**3,
            rss_reader=lambda _pid: 1,
        )

    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(sleep_job, range(3)))
    assert time.monotonic() - started < 0.7
    assert all(row.status == "COMPLETE" for row in rows)
    assert {Path(row.stdout_path).name for row in rows} == {"stdout.log"}
    worker_logs = {(tmp_path / f"worker-{index}" / "stdout.log").resolve() for index in range(3)}
    assert len(worker_logs) == 3
    assert all(path.is_file() for path in worker_logs)

    for label, timeout, memory, rss in (("timeout", 0.1, 1024**3, 1), ("memory", 2, 10, 11)):
        directory = tmp_path / label
        directory.mkdir()
        canonical = directory / "canonical.json"
        command = [
            sys.executable,
            "-c",
            f"from pathlib import Path; import time; Path({str(canonical)!r}).write_text('partial'); time.sleep(2)",
        ]
        result = runner.run_bounded_process(
            command,
            cwd=ROOT,
            environment=environment,
            stdout_path=directory / "stdout.log",
            stderr_path=directory / "stderr.log",
            timeout_seconds=timeout,
            memory_limit_bytes=memory,
            rss_reader=lambda _pid, value=rss: value,
        )
        runner.discard_incomplete_output(canonical, result)
        assert result.status == ("TIMEOUT" if label == "timeout" else "MEMORY_LIMIT")
        assert not canonical.exists()


def _write_wrapper(path: Path, wrapper: dict[str, object]) -> None:
    path.write_bytes(common.canonical_bytes(wrapper))


def test_q1x_checker_rejects_nodes_maps_stations_residuals_generators_and_hashes(tmp_path: Path) -> None:
    historical, environment = _external_inputs()
    historical_sha = common.sha256(historical.read_bytes())
    wrapper = producer.emit_geometry_proof(
        repository_root=ROOT,
        contract_path=CONTRACT,
        contract_sha256=CONTRACT_SHA,
        historical_reference=historical,
        historical_reference_sha256=historical_sha,
        geometry_id="Q0_SQUARE",
    )
    baseline = tmp_path / "baseline.json"
    _write_wrapper(baseline, wrapper)
    accepted = checker.verify_geometry_proof(
        repository_root=ROOT,
        contract_path=CONTRACT,
        contract_sha256=CONTRACT_SHA,
        historical_reference=historical,
        historical_reference_sha256=historical_sha,
        proof_path=baseline,
        environment_root=environment,
    )
    assert accepted["terminal"] == "UNCLASSIFIED_E4_PL_Q1X_TRANSPORT_CLOSED_ONLY"

    def mutate_node(value: dict[str, object]) -> None:
        value["proof"]["cases"][0]["nodes"][0][0][0] = "1"  # type: ignore[index]

    def mutate_map(value: dict[str, object]) -> None:
        value["proof"]["cases"][1]["field_maps"]["C_eng"][0][0] = "2"  # type: ignore[index]

    def mutate_station(value: dict[str, object]) -> None:
        value["proof"]["cases"][0]["stations"][0]["compatible"][0] = "3"  # type: ignore[index]

    def mutate_residual(value: dict[str, object]) -> None:
        value["proof"]["cases"][0]["stations"][0]["transport_residuals"]["compatible"][0] = "1"  # type: ignore[index]

    def mutate_generator(value: dict[str, object]) -> None:
        value["proof"]["exact_field"]["generators"][0]["radicand_coefficients"][0] = "3"  # type: ignore[index]

    mutations = [mutate_node, mutate_map, mutate_station, mutate_residual, mutate_generator]
    for index, mutation in enumerate(mutations):
        value = copy.deepcopy(wrapper)
        mutation(value)
        value["proof_sha256"] = common.sha256(common.canonical_bytes(value["proof"]))
        path = tmp_path / f"mutation-{index}.json"
        _write_wrapper(path, value)
        with pytest.raises((common.Q1XError, KeyError, TypeError, ValueError)):
            checker.verify_geometry_proof(
                repository_root=ROOT,
                contract_path=CONTRACT,
                contract_sha256=CONTRACT_SHA,
                historical_reference=historical,
                historical_reference_sha256=historical_sha,
                proof_path=path,
                environment_root=environment,
            )
    bad_hash = copy.deepcopy(wrapper)
    bad_hash["proof_sha256"] = "0" * 64
    bad_hash_path = tmp_path / "mutation-hash.json"
    _write_wrapper(bad_hash_path, bad_hash)
    with pytest.raises(common.Q1XError):
        checker.verify_geometry_proof(
            repository_root=ROOT,
            contract_path=CONTRACT,
            contract_sha256=CONTRACT_SHA,
            historical_reference=historical,
            historical_reference_sha256=historical_sha,
            proof_path=bad_hash_path,
            environment_root=environment,
        )


def test_q1x_terminal_precedence_is_fail_closed_and_ordered() -> None:
    terminals = common.validate_contract(ROOT, CONTRACT, CONTRACT_SHA)["terminals"]
    order = [f"{geometry}::{operation}" for geometry in common.GEOMETRY_IDS for operation in common.OPERATION_IDS]
    assert runner.select_terminal(order, [order[20], order[4]], blocked=False, terminals=terminals) == (
        "NO_GO_E4_PL_Q1X_EXACT_TRANSPORT_COUNTEREXAMPLE",
        order[4],
    )
    assert runner.select_terminal(order, [], blocked=False, terminals=terminals) == (
        "UNCLASSIFIED_E4_PL_Q1X_TRANSPORT_CLOSED_ONLY",
        "",
    )
    assert runner.select_terminal(order, [order[0]], blocked=True, terminals=terminals) == (
        "BLOCKED_E4_PL_Q1X_PROOF_OR_REVIEW",
        "",
    )


def test_q1x_full_56_case_cycle_is_parallel_checked_and_deterministic(tmp_path: Path) -> None:
    historical, environment = _external_inputs()
    historical_sha = common.sha256(historical.read_bytes())

    def execute(label: str) -> dict[str, object]:
        return runner.execute_bounded(
            repository_root=ROOT,
            contract_path=CONTRACT,
            contract_sha256=CONTRACT_SHA,
            historical_reference=historical,
            historical_reference_sha256=historical_sha,
            environment_root=environment,
            producer_path=PRODUCER,
            checker_path=CHECKER,
            output_directory=tmp_path / label,
        )

    first = execute("cycle-1")
    second = execute("cycle-2")
    assert common.canonical_bytes(first) == common.canonical_bytes(second)
    bounded = first["bounded_result"]
    assert bounded["case_count"] == 56
    assert bounded["station_count"] == 224
    assert bounded["geometry_count"] == 7
    assert bounded["exact_counterexample_cases"] == []
    assert bounded["selected_counterexample"] == ""
    assert bounded["terminal"] == "UNCLASSIFIED_E4_PL_Q1X_TRANSPORT_CLOSED_ONLY"
    assert len(first["shards"]) == 7
    assert all(row["checker_byte_identical"] for row in first["shards"])
    assert all(len(row["checker_processes"]) == 2 for row in first["shards"])
    assert all(row["producer_process"] == {"returncode": 0, "status": "COMPLETE"} for row in first["shards"])
    assert all(row["case_count"] == 8 and row["station_count"] == 32 for row in first["shards"])
