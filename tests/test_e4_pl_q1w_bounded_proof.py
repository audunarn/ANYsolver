from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import importlib
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

common = importlib.import_module("e4_pl_q1w_common")
producer = importlib.import_module("e4_pl_q1w_proof_producer")
checker = importlib.import_module("e4_pl_q1w_proof_checker")
runner = importlib.import_module("e4_pl_q1w_bounded_runner")

CONTRACT = REFERENCE_CASES / "e4_pl_q1w_proof_contract.json"
CONTRACT_SHA = common.sha256(CONTRACT.read_bytes())
RESULT = REFERENCE_CASES / "e4_pl_q1w_bounded_result.json"


def test_q1w_contract_is_canonical_bounded_and_production_is_unchanged() -> None:
    raw, value = common.read_json(CONTRACT)
    assert raw == common.canonical_bytes(value)
    checked = common.validate_contract(ROOT, CONTRACT, CONTRACT_SHA)
    assert checked["shards"] == ["Q0_SQUARE::R90", "Q0_SQUARE::R180", "Q0_SQUARE::R270"]
    assert checked["parallelism"] == {
        "checker_workers": 6,
        "memory_limit_gib_per_producer": 24,
        "numerical_threads_per_process": 1,
        "producer_workers": 3,
        "timeout_seconds_per_process": 600,
    }
    assert checked["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    result_raw, result = common.read_json(RESULT)
    assert result_raw == common.canonical_bytes(result)
    assert result["proof_contract_sha256"] == CONTRACT_SHA
    assert result["terminal"] == "UNCLASSIFIED_E4_PL_Q1W_BOUNDED_EVIDENCE"
    assert len(result["shards"]) == 3
    changed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.splitlines()
    paths = [row[3:] for row in changed]
    assert not any(path == "pyproject.toml" or path.startswith(("src/", ".github/")) for path in paths)


def test_q1w_parallel_process_bounds_overlap_timeout_and_memory(tmp_path: Path) -> None:
    environment = os.environ.copy()

    def sleep_job(index: int) -> runner.ProcessResult:
        return runner.run_bounded_process(
            [sys.executable, "-c", "import time; time.sleep(0.25)"],
            cwd=ROOT,
            environment=environment,
            stdout_path=tmp_path / f"parallel-{index}.out",
            stderr_path=tmp_path / f"parallel-{index}.err",
            timeout_seconds=2,
            memory_limit_bytes=1024**3,
            rss_reader=lambda _pid: 1,
        )

    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(sleep_job, range(3)))
    elapsed = time.monotonic() - started
    assert all(row.status == "COMPLETE" for row in rows)
    assert elapsed < 0.65
    timeout = runner.run_bounded_process(
        [sys.executable, "-c", "import time; time.sleep(2)"],
        cwd=ROOT,
        environment=environment,
        stdout_path=tmp_path / "timeout.out",
        stderr_path=tmp_path / "timeout.err",
        timeout_seconds=0.1,
        memory_limit_bytes=1024**3,
        rss_reader=lambda _pid: 1,
    )
    assert timeout.status == "TIMEOUT"
    memory = runner.run_bounded_process(
        [sys.executable, "-c", "import time; time.sleep(2)"],
        cwd=ROOT,
        environment=environment,
        stdout_path=tmp_path / "memory.out",
        stderr_path=tmp_path / "memory.err",
        timeout_seconds=2,
        memory_limit_bytes=10,
        rss_reader=lambda _pid: 11,
    )
    assert memory.status == "MEMORY_LIMIT"


def test_q1w_terminal_selection_is_ordered_and_fail_closed() -> None:
    terminals = common.read_json(CONTRACT)[1]["terminals"]
    cases = ["Q0_SQUARE::R90", "Q0_SQUARE::R180", "Q0_SQUARE::R270"]
    assert runner.select_terminal(cases, [cases[2], cases[1]], blocked=False, terminals=terminals) == (
        "NO_GO_E4_PL_Q1W_EXACT_COUNTEREXAMPLE",
        cases[1],
    )
    assert runner.select_terminal(cases, [], blocked=False, terminals=terminals) == (
        "UNCLASSIFIED_E4_PL_Q1W_BOUNDED_EVIDENCE",
        "",
    )
    assert runner.select_terminal(cases, [cases[0]], blocked=True, terminals=terminals) == (
        "BLOCKED_E4_PL_Q1W_PROOF_OR_REVIEW",
        "",
    )


def _external_inputs() -> tuple[Path, Path]:
    historical_text = os.environ.get("Q1W_HISTORICAL_REFERENCE")
    environment_text = os.environ.get("Q1W_EXACT_ENV_ROOT")
    if not historical_text or not environment_text:
        pytest.skip("Q1W external historical wrapper and exact environment are not configured")
    return Path(historical_text), Path(environment_text)


def test_q1w_three_proofs_and_two_checker_replicas_are_exact_and_deterministic(tmp_path: Path) -> None:
    historical, environment = _external_inputs()
    historical_sha = common.sha256(historical.read_bytes())
    common.validate_environment(ROOT, environment, common.validate_contract(ROOT, CONTRACT, CONTRACT_SHA))
    results: dict[str, dict[str, object]] = {}
    for case_id in common.read_json(CONTRACT)[1]["shards"]:
        value = producer.emit_proof(
            repository_root=ROOT,
            contract_path=CONTRACT,
            contract_sha256=CONTRACT_SHA,
            historical_reference=historical,
            historical_reference_sha256=historical_sha,
            case_id=case_id,
        )
        proof_path = tmp_path / f"{case_id.replace('::', '_')}.json"
        proof_path.write_bytes(common.canonical_bytes(value))
        first = checker.verify_proof(
            repository_root=ROOT,
            contract_path=CONTRACT,
            contract_sha256=CONTRACT_SHA,
            historical_reference=historical,
            historical_reference_sha256=historical_sha,
            proof_path=proof_path,
            environment_root=environment,
        )
        second = checker.verify_proof(
            repository_root=ROOT,
            contract_path=CONTRACT,
            contract_sha256=CONTRACT_SHA,
            historical_reference=historical,
            historical_reference_sha256=historical_sha,
            proof_path=proof_path,
            environment_root=environment,
        )
        assert common.canonical_bytes(first) == common.canonical_bytes(second)
        assert first["terminal"] == "UNCLASSIFIED_E4_PL_Q1W_BOUNDED_EVIDENCE"
        assert first["exact_nonzero_transport_residuals"] == []
        assert first["legacy_untransformed_nonzero_residual_count"] > 0
        results[case_id] = value
    assert set(results) == {"Q0_SQUARE::R90", "Q0_SQUARE::R180", "Q0_SQUARE::R270"}


def test_q1w_checker_rejects_mutated_proof(tmp_path: Path) -> None:
    historical, environment = _external_inputs()
    historical_sha = common.sha256(historical.read_bytes())
    value = producer.emit_proof(
        repository_root=ROOT,
        contract_path=CONTRACT,
        contract_sha256=CONTRACT_SHA,
        historical_reference=historical,
        historical_reference_sha256=historical_sha,
        case_id="Q0_SQUARE::R90",
    )
    value["proof"]["stations"][0]["N"][0] = "999"
    value["proof_sha256"] = common.sha256(common.canonical_bytes(value["proof"]))
    path = tmp_path / "mutated.json"
    path.write_bytes(common.canonical_bytes(value))
    with pytest.raises(common.Q1WError):
        checker.verify_proof(
            repository_root=ROOT,
            contract_path=CONTRACT,
            contract_sha256=CONTRACT_SHA,
            historical_reference=historical,
            historical_reference_sha256=historical_sha,
            proof_path=path,
            environment_root=environment,
        )
