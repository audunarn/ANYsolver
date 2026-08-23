from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

import e4_pl_q1b_common as common
import e4_pl_q1c_bounded_runner as runner
import e4_pl_q1c_diagnostic_checker as checker
import e4_pl_q1c_diagnostic_producer as producer


ROOT = Path(__file__).resolve().parents[1]
Q1B_COMMIT = "3df23199893eb136b2682c5190d1405b52dbdd58"
CONTRACT = ROOT / "docs/reference_cases/e4_pl_q1c_contract.json"
RESULT = ROOT / "docs/reference_cases/e4_pl_q1c_result.json"


def test_q1c_contract_and_historical_authority() -> None:
    raw, contract = common.read_json(CONTRACT)
    assert contract["schema"] == "anysolver.s4.e4-pl-q1c-contract-v1"
    assert contract["q1b_authority"]["commit"] == Q1B_COMMIT
    assert contract["repair"] == {
        "drill_coordinate": "EXACT_SCHUR_CONDENSATION_AND_BACK_SUBSTITUTION",
        "formulation_changes": False,
        "global_solve": "SYMMETRIC_DIAGONAL_EQUILIBRATION_OF_CONDENSED_PHYSICAL_SYSTEM",
        "hourglass_changes": False,
        "mitc_changes": False,
        "pl_changes": False,
    }
    assert contract["runtime"] == {"automatic_retry": False, "checker_replicas": 2, "memory_limit_gib": 8, "numerical_threads": 1, "timeout_seconds": 120, "workers": 3}
    assert common.sha256(raw) == "E8D7C83BFE4C2F8734317E525BA8C01EBBDD592E11BCC234B0D3346123D0C89B"
    assert runner.validate_contract(ROOT, CONTRACT, common.sha256(raw)) == contract
    for key in ("cycle1", "cycle2"):
        row = contract["q1b_authority"][key]
        common.verify_file(ROOT / row["path"], bytes_count=row["bytes"], digest=row["sha256"])
    assert subprocess.run(["git", "merge-base", "--is-ancestor", Q1B_COMMIT, "HEAD"], cwd=ROOT, check=False).returncode == 0


def test_q1c_producers_and_independent_checker(tmp_path: Path) -> None:
    for shard in producer.SHARDS:
        proof_path = tmp_path / f"{shard}.json"
        check1 = tmp_path / f"{shard}-check1.json"
        check2 = tmp_path / f"{shard}-check2.json"
        common.write_exclusive(proof_path, producer.produce(shard))
        common.write_exclusive(check1, checker.verify(proof_path))
        common.write_exclusive(check2, checker.verify(proof_path))
        assert check1.read_bytes() == check2.read_bytes()
        _, result = common.read_json(check1)
        assert result["contradictions"] == []
        assert result["disagreements"] == []
    _, spatial = common.read_json(tmp_path / "SPATIAL_DISCRETIZATION-check1.json")
    _, thickness = common.read_json(tmp_path / "THICKNESS_LOCKING-check1.json")
    assert spatial["classification_facts"]["monotone_spatial_convergence"] is True
    assert spatial["classification_facts"]["finest_error_below_two_percent"] is True
    assert thickness["classification_facts"]["resolved_response_spread_below_limit"] is True
    assert thickness["conditioning_unresolved"] is True


def test_q1c_checker_rejects_mutated_evidence(tmp_path: Path) -> None:
    proof = producer.produce("SPATIAL_DISCRETIZATION")
    mutated = copy.deepcopy(proof)
    mutated["payload"]["rows"][0]["displacement"] = 1.0.hex()
    mutated["payload_sha256"] = common.sha256(common.canonical_bytes(mutated["payload"]))
    path = tmp_path / "mutated.json"
    common.write_exclusive(path, mutated)
    with pytest.raises(common.Q1BError, match="derived value mismatch"):
        checker.verify(path)


def test_q1c_parallel_bounds_cleanup_and_terminal_precedence(tmp_path: Path) -> None:
    commands = []
    for index in range(3):
        directory = tmp_path / f"overlap-{index}"
        record = directory / "record.json"
        code = "import json,pathlib,sys,time; s=time.time(); time.sleep(.25); pathlib.Path(sys.argv[1]).write_text(json.dumps({'end':time.time(),'start':s}))"
        commands.append((str(index), [sys.executable, "-c", code, str(record)], directory, "record.json"))
    started = time.monotonic()
    results = runner.run_wave(commands, timeout_seconds=2, memory_limit_gib=1)
    assert time.monotonic() - started < 1.5
    assert all(row.returncode == 0 and not row.timed_out and not row.memory_exceeded for row in results)
    intervals = [json.loads((tmp_path / f"overlap-{index}/record.json").read_text()) for index in range(3)]
    assert max(row["start"] for row in intervals) < min(row["end"] for row in intervals)

    timeout_directory = tmp_path / "timeout"
    timeout_record = timeout_directory / "record.json"
    timeout_code = "import pathlib,sys,time; time.sleep(2); pathlib.Path(sys.argv[1]).write_text('{}')"
    [timeout_result] = runner.run_wave([("timeout", [sys.executable, "-c", timeout_code, str(timeout_record)], timeout_directory, "record.json")], timeout_seconds=1, memory_limit_gib=1)
    assert timeout_result.timed_out is True and not timeout_record.exists()
    assert runner.choose_terminal(blocked=True, locking=True, formulation=True, unresolved=True) == runner.TERMINALS[0]
    assert runner.choose_terminal(blocked=False, locking=True, formulation=True, unresolved=True) == runner.TERMINALS[1]
    assert runner.choose_terminal(blocked=False, locking=False, formulation=True, unresolved=True) == runner.TERMINALS[2]
    assert runner.choose_terminal(blocked=False, locking=False, formulation=False, unresolved=True) == runner.TERMINALS[3]
    assert runner.choose_terminal(blocked=False, locking=False, formulation=False, unresolved=False) == runner.TERMINALS[4]


def test_q1c_frozen_two_cycle_result_and_production_boundary() -> None:
    raw, result = common.read_json(RESULT)
    assert result["schema"] == "anysolver.s4.e4-pl-q1c-result-v1"
    assert result["contract_sha256"] == common.sha256(CONTRACT.read_bytes())
    assert result["common_payload_sha256"] == common.sha256(common.canonical_bytes(result["common_payload"]))
    assert [row["aggregate_sha256"] for row in result["cycles"]] == ["EDD8AF7699656A1EEADA23E64C5AD19F1F138490F52450242309756910104D57"] * 2
    assert [row["aggregate_bytes"] for row in result["cycles"]] == [2145, 2145]
    assert result["terminal"] == result["common_payload"]["terminal"] == "UNCLASSIFIED_E4_PL_Q1C_NUMERICAL_CONDITIONING"
    assert result["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert result["q1b_authorization"] == "UNAUTHORIZED"
    assert raw.endswith(b"\n")
    forbidden = subprocess.run(["git", "diff", "--name-only", Q1B_COMMIT, "--", ".gitattributes", ".github", "pyproject.toml", "src"], cwd=ROOT, capture_output=True, text=True, check=True)
    assert forbidden.stdout.strip() == ""
