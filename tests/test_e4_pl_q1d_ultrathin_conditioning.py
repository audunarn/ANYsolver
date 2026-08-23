from __future__ import annotations

import copy
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

import e4_pl_q1b_common as common
import e4_pl_q1d_bounded_runner as runner


BASE_COMMIT = "22c57838f64205716d5e9272328acc9d0f06289e"
CONTRACT = REFERENCE_CASES / "e4_pl_q1d_contract.json"
RESULT = REFERENCE_CASES / "e4_pl_q1d_result.json"
CONTRACT_SHA = "DB21BE38827C8A0A8D2607D0D9D511C1241CF4E852FD5A3D69C6074A7B6A16CE"
AGGREGATE_SHA = "0A8AF4DC16DD803B886291CC3E68459CCAB55D13F8057D3CE67B3AA62A52EC46"


def _assert_base_and_production_boundary() -> None:
    base = subprocess.run(
        ["git", "cat-file", "-e", f"{BASE_COMMIT}^{{commit}}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if base.returncode:
        assert os.environ.get("GITHUB_ACTIONS") == "true"
        shallow_text = subprocess.run(
            ["git", "rev-parse", "--git-path", "shallow"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        shallow = (ROOT / shallow_text).resolve() if not Path(shallow_text).is_absolute() else Path(shallow_text)
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.strip()
        assert shallow.is_file()
        assert head in shallow.read_text(encoding="ascii").splitlines()
        return
    assert subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"], cwd=ROOT, check=False
    ).returncode == 0
    forbidden = subprocess.run(
        ["git", "diff", "--name-only", BASE_COMMIT, "--", ".gitattributes", ".github", "pyproject.toml", "src"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert forbidden.stdout.strip() == ""


@pytest.fixture(scope="module")
def checked_full_block(tmp_path_factory: pytest.TempPathFactory) -> tuple[object, object, Path]:
    environment_text = os.environ.get("Q1D_EXACT_ENV_ROOT")
    if not environment_text:
        pytest.skip("Q1D_EXACT_ENV_ROOT does not name the frozen research environment")
    environment = Path(environment_text).resolve(strict=True)
    sys.path.insert(0, str(environment))
    producer = importlib.import_module("e4_pl_q1d_precision_producer")
    checker = importlib.import_module("e4_pl_q1d_precision_checker")
    directory = tmp_path_factory.mktemp("q1d-full-block")
    proof_path = directory / "proof.json"
    check1_path = directory / "check1.json"
    check2_path = directory / "check2.json"
    common.write_exclusive(proof_path, producer.produce("FULL_BLOCK_LDL"))
    common.write_exclusive(check1_path, checker.verify(proof_path))
    common.write_exclusive(check2_path, checker.verify(proof_path))
    assert check1_path.read_bytes() == check2_path.read_bytes()
    return producer, checker, proof_path


def test_q1d_contract_base_environment_and_scope_are_exact() -> None:
    raw, contract = common.read_json(CONTRACT)
    assert raw == common.canonical_bytes(contract)
    assert common.sha256(raw) == CONTRACT_SHA
    assert contract["base_commit"] == BASE_COMMIT
    assert contract["runtime"] == {
        "automatic_retry": False,
        "checker_replicas": 2,
        "memory_limit_gib": 8,
        "numerical_threads": 1,
        "precision_bits": [128, 192, 256],
        "timeout_seconds": 120,
        "workers": 3,
    }
    assert contract["shards"] == ["FULL_BLOCK_LDL", "DRILL_SCHUR", "ULTRATHIN_REFINEMENT"]
    for row in (contract["q1c_authority"]["contract"], contract["q1c_authority"]["result"], contract["environment"]):
        common.verify_file(ROOT / row["path"], bytes_count=row["bytes"], digest=row["sha256"])
    _, environment = common.read_json(ROOT / contract["environment"]["path"])
    assert environment["extracted_file_count"] == 1662
    assert environment["extracted_file_hash_graph_sha256"] == "bc8c22965ed8271e06b6c05d4d33c3dcd7f4495acf73360be12ad6c682577b82"
    _assert_base_and_production_boundary()


def test_q1d_high_precision_full_block_and_checker_replicas(checked_full_block: tuple[object, object, Path]) -> None:
    _, checker, proof_path = checked_full_block
    check = checker.verify(proof_path)
    assert check["contradictions"] == []
    assert check["disagreements"] == []
    assert check["precision_unresolved"] is False
    assert check["classification_facts"] == {
        "precision_stable": True,
        "scaled_residual_below_limit": True,
        "ultrathin_error_below_two_percent": True,
    }


def test_q1d_checker_rejects_mutated_high_precision_evidence(
    checked_full_block: tuple[object, object, Path], tmp_path: Path
) -> None:
    _, checker, proof_path = checked_full_block
    _, proof = common.read_json(proof_path)
    mutated = copy.deepcopy(proof)
    mutated["payload"]["rows"][0]["response_ratio_eb"] = "9.5e-1"
    mutated["payload_sha256"] = common.sha256(common.canonical_bytes(mutated["payload"]))
    mutation_path = tmp_path / "mutated.json"
    common.write_exclusive(mutation_path, mutated)
    with pytest.raises(common.Q1BError, match="independent precision value mismatch"):
        checker.verify(mutation_path)


def test_q1d_parallel_overlap_timeout_cleanup_and_terminal_precedence(tmp_path: Path) -> None:
    commands = []
    for index in range(3):
        directory = tmp_path / f"overlap-{index}"
        record = directory / "record.json"
        code = "import json,pathlib,sys,time;s=time.time();time.sleep(.25);pathlib.Path(sys.argv[1]).write_text(json.dumps({'end':time.time(),'start':s}))"
        commands.append((str(index), [sys.executable, "-B", "-c", code, str(record)], directory, "record.json"))
    started = time.monotonic()
    results = runner.run_wave(
        commands,
        repository_root=ROOT,
        environment_root=tmp_path,
        timeout_seconds=2,
        memory_limit_gib=1,
    )
    assert time.monotonic() - started < 1.5
    assert all(row.returncode == 0 and not row.timed_out and not row.memory_exceeded for row in results)
    intervals = [json.loads((tmp_path / f"overlap-{index}/record.json").read_text()) for index in range(3)]
    assert max(row["start"] for row in intervals) < min(row["end"] for row in intervals)

    timeout_directory = tmp_path / "timeout"
    timeout_record = timeout_directory / "record.json"
    timeout_code = "import pathlib,sys,time;time.sleep(2);pathlib.Path(sys.argv[1]).write_text('{}')"
    [timed] = runner.run_wave(
        [("timeout", [sys.executable, "-B", "-c", timeout_code, str(timeout_record)], timeout_directory, "record.json")],
        repository_root=ROOT,
        environment_root=tmp_path,
        timeout_seconds=1,
        memory_limit_gib=1,
    )
    assert timed.timed_out is True and not timeout_record.exists()
    assert runner.choose_terminal(blocked=True, locking=True, equivalence=True, precision=True) == runner.TERMINALS[0]
    assert runner.choose_terminal(blocked=False, locking=True, equivalence=True, precision=True) == runner.TERMINALS[1]
    assert runner.choose_terminal(blocked=False, locking=False, equivalence=True, precision=True) == runner.TERMINALS[2]
    assert runner.choose_terminal(blocked=False, locking=False, equivalence=False, precision=True) == runner.TERMINALS[3]
    assert runner.choose_terminal(blocked=False, locking=False, equivalence=False, precision=False) == runner.TERMINALS[4]


def test_q1d_frozen_two_cycle_result_and_production_boundary() -> None:
    raw, result = common.read_json(RESULT)
    assert raw == common.canonical_bytes(result)
    assert result["schema"] == "anysolver.s4.e4-pl-q1d-result-v1"
    assert result["contract_sha256"] == common.sha256(CONTRACT.read_bytes()) == CONTRACT_SHA
    assert result["common_payload_sha256"] == common.sha256(common.canonical_bytes(result["common_payload"]))
    assert [row["aggregate_sha256"] for row in result["cycles"]] == [AGGREGATE_SHA, AGGREGATE_SHA]
    assert [row["aggregate_bytes"] for row in result["cycles"]] == [2059, 2059]
    assert result["terminal"] == result["common_payload"]["terminal"] == "UNCLASSIFIED_E4_PL_Q1D_ULTRATHIN_CONDITIONING_CLOSED_ONLY"
    assert result["decision"] == {
        "q1b_terminal_preserved": "NO_GO_E4_PL_Q1B_LOCKING_OR_CATEGORY_DRIFT",
        "scope": "ULTRATHIN_HIGH_PRECISION_CONDITIONING_ONLY",
        "solver_equivalence": "FULL_BLOCK_LDL_EQUALS_DRILL_SCHUR",
        "ultrathin_locking": "NOT_REPRODUCED_AT_256_BITS",
    }
    assert result["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert result["q1b_authorization"] == "UNAUTHORIZED"
    _assert_base_and_production_boundary()
