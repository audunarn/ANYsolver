"""Non-mechanical Q1B CONTRACT3 authority tests."""

from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

import e4_pl_q1b_common as common


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "docs/reference_cases"
CONTRACT = REF / "e4_pl_q1b_execution_contract.json"
REVIEW = REF / "e4_pl_q1b_contract_review.json"
THIS_TEST = ROOT / "tests/test_e4_pl_q1b_contract.py"
IMPLEMENTATION_COMMIT = "ba17cf0e3ac05de581e0b39eee22943214c099ad"
IMPLEMENTATION_SUBJECT = "docs: freeze E4 PL Q1B assembled qualification implementations"
CONTRACT_SUBJECT = "docs: authorize E4 PL Q1B bounded assembled execution"
CONTRACT3 = {
    "docs/reference_cases/e4_pl_q1b_execution_contract.json",
    "docs/reference_cases/e4_pl_q1b_contract_review.json",
    "tests/test_e4_pl_q1b_contract.py",
}


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load(path: Path) -> dict[str, object]:
    raw, value = common.read_json(path)
    assert raw == common.canonical_bytes(value)
    return value


def _validate_static(value: dict[str, object]) -> None:
    assert set(value) == common.CONTRACT_KEYS
    assert value["schema"] == common.CONTRACT_SCHEMA
    assert value["candidate_id"] == common.CANDIDATE_ID
    assert value["study_id"] == common.STUDY_ID
    assert value["authorization"] == {
        "commit3_paths": list(common.CONTRACT3_PATHS),
        "commit3_subject": CONTRACT_SUBJECT,
        "hard_freeze_event": "FIRST_SCHEMA_VALID_CANONICAL_REGISTERED_SHARD_EXCLUSIVELY_CREATED_REOPENED_AND_HASH_VERIFIED",
        "token": "AUTHORIZE_E4_PL_Q1B_BOUNDED_ASSEMBLED_EXECUTION",
    }
    assert value["agreement"] == {
        "checker_replicas_per_shard": 2,
        "cycle_aggregates": "BYTE_IDENTICAL_CANONICAL_COMMON_PAYLOAD",
        "producer_shards": list(common.SHARDS),
    }
    assert value["runner_inventory"] == {
        "commissioning_before_mechanics": True,
        "runner_ids": list(common.RUNNER_IDS),
    }
    assert value["runtime"] == {
        "automatic_retry": False,
        "memory_limit_gib_per_process": 24,
        "numerical_threads_per_process": 1,
        "timeout_seconds_per_process": 600,
        "worker_count": 3,
    }
    assert value["output_absences"] == sorted(common.OUTCOME_PATHS)
    assert value["terminal_authority"] == list(common.TERMINALS)
    assert value["scientific_inventory"] == list(common.SCIENTIFIC_NODES)
    assert value["inherited_inputs"] == {
        "count": 12,
        "source": "docs/reference_cases/e4_pl_q1b_baseline.json",
        "source_sha256": "710C886A29ABBF8FDB4A5051C9005071831403D458D91ECB2EEFEC86E9C28692",
    }
    assert value["production_restriction"] == {
        "production": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "public_api_changes": False,
        "q1b_execution": "AUTHORIZED_ONLY_BY_CALLER_BOUND_CONTRACT",
        "src_changes": False,
    }
    assert value["environment"] == {
        "numpy": "2.4.3",
        "pytest": "9.0.1",
        "python_implementation": "CPython",
        "python_version": "3.13.9",
        "q1t_exact_environment": {
            "bytes": 227603,
            "path": "docs/reference_cases/e4_pl_q1t_environment.json",
            "sha256": "5461206324E7FC2A52B334CE736A512EE71313ED79181438047E3E20069A9746",
        },
        "scipy": "1.16.3",
    }
    ancestry = value["commit_ancestry"]
    assert ancestry["implementation"]["commit"] == IMPLEMENTATION_COMMIT
    assert ancestry["implementation"]["subject"] == IMPLEMENTATION_SUBJECT
    assert ancestry["implementation"]["path_count"] == 11
    assert ancestry["plan"]["accepted_plan_commit"] == "9cba0a191eb5f82ca4f9959ffc4f92df69b98d42"
    assert value["plan_inputs"]["count"] == 6
    assert value["implementation_inputs"]["count"] == 11
    assert {row["path"] for row in value["plan_inputs"]["rows"]} == set(common.PLAN_INPUT_PATHS)
    assert {row["path"] for row in value["implementation_inputs"]["rows"]} == set(common.IMPLEMENTATION_INPUT_PATHS)
    for group in (value["plan_inputs"], value["implementation_inputs"]):
        assert group["count"] == len(group["rows"])
        for row in group["rows"]:
            path = ROOT / row["path"]
            assert path.stat().st_size == row["bytes"]
            assert _sha(path) == row["sha256"]
            assert _git("rev-parse", f"{IMPLEMENTATION_COMMIT}:{row['path']}") == row["git_blob"]
    reviews = value["review_authorities"]
    for name, path, verdict in (
        ("plan", REF / "e4_pl_q1b_plan_review.json", "ACCEPT_Q1B_PREREGISTRATION_NO_P0_P1"),
        ("implementation", REF / "e4_pl_q1b_implementation_review.json", "ACCEPT_Q1B_IMPLEMENTATION_FREEZE_NO_P0_P1"),
    ):
        parsed = _load(path)
        assert parsed["findings"] == [] and parsed["verdict"] == verdict
        assert reviews[name]["sha256"] == _sha(path)
        expected_independence = {
            "plan": {"mechanics_executed": False, "reviewer_role": "INDEPENDENT_Q1B_PLAN_REVIEWER", "same_agent_as_packet_author": False},
            "implementation": {"authored_review_only": True, "mechanics_executed": False, "reviewed_input_authorship": False, "role": "INDEPENDENT_STATIC_IMPLEMENTATION_REVIEWER"},
        }[name]
        assert parsed["reviewer_independence"] == expected_independence
        for row in parsed["reviewed_inputs"]:
            reviewed = ROOT / row["path"]
            assert set(row) == {"bytes", "path", "sha256"}
            assert reviewed.stat().st_size == row["bytes"] and _sha(reviewed) == row["sha256"]
    assert reviews["contract"] == {
        "hash_binding": "EXTERNAL_AUTHORITY_RECORD",
        "path": "docs/reference_cases/e4_pl_q1b_contract_review.json",
        "verdict": "ACCEPT_Q1B_EXECUTION_CONTRACT_NO_P0_P1",
    }
    proofs = value["q1y3_commissioning"]["proofs"]
    assert proofs == [{"bytes": size, "name": name, "sha256": digest} for name, size, digest in common.Q1Y3_PROOFS]
    assert value["q1y3_commissioning"]["classification"] == "EXACT_EQUIVALENCE_COMMISSIONING_INPUT"
    environment_path = ROOT / value["environment"]["q1t_exact_environment"]["path"]
    assert environment_path.stat().st_size == 227603 and _sha(environment_path) == value["environment"]["q1t_exact_environment"]["sha256"]
    assert _git("rev-parse", f"{IMPLEMENTATION_COMMIT}:{value['environment']['q1t_exact_environment']['path']}") == _git("rev-parse", f"HEAD:{value['environment']['q1t_exact_environment']['path']}")
    evidence = os.environ.get("Q1B_Q1Y3_EVIDENCE_ROOT")
    if evidence:
        for row in proofs:
            path = Path(evidence) / row["name"]
            assert path.stat().st_size == row["bytes"] and _sha(path) == row["sha256"]


def test_q1b_complete_contract_hash_dag_and_authority() -> None:
    contract = _load(CONTRACT)
    _validate_static(contract)
    head = _git("rev-parse", "HEAD")
    if head == IMPLEMENTATION_COMMIT:
        assert _git("show", "-s", "--format=%s", head) == IMPLEMENTATION_SUBJECT
    else:
        assert _git("rev-parse", "HEAD^") == IMPLEMENTATION_COMMIT
        assert _git("show", "-s", "--format=%s", head) == CONTRACT_SUBJECT
        assert set(_git("diff-tree", "--no-commit-id", "--name-only", "-r", head).splitlines()) == CONTRACT3
        assert _git("show", f"HEAD:docs/reference_cases/e4_pl_q1b_execution_contract.json").encode() + b"\n" == CONTRACT.read_bytes()
    if REVIEW.exists():
        review = _load(REVIEW)
        assert set(review) == {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"}
        assert review["findings"] == [] and review["verdict"] == "ACCEPT_Q1B_EXECUTION_CONTRACT_NO_P0_P1"
        assert {row["path"] for row in review["reviewed_inputs"]} == {
            "docs/reference_cases/e4_pl_q1b_execution_contract.json", "tests/test_e4_pl_q1b_contract.py"
        }


def test_q1b_contract_mutation_matrix_rejects_drift() -> None:
    original = _load(CONTRACT)
    mutations = (
        ("schema", "bad"),
        ("candidate_id", "bad"),
        ("study_id", "bad"),
        ("agreement.cycle_aggregates", "BYTE_IDENTICAL_CANONICAL_JSON"),
        ("authorization.token", "bad"),
        ("commit_ancestry.implementation.commit", "0" * 40),
        ("environment.python_version", "0"),
        ("implementation_inputs.count", 10),
        ("inherited_inputs.count", 11),
        ("output_absences", []),
        ("plan_inputs.rows", []),
        ("production_restriction.src_changes", True),
        ("q1y3_commissioning.proofs", []),
        ("review_authorities.plan.sha256", "0" * 64),
        ("runner_inventory.runner_ids", [common.RUNNER_IDS[0]]),
        ("runtime.worker_count", 2),
        ("scientific_inventory", []),
        ("terminal_authority", list(reversed(common.TERMINALS))),
    )
    for dotted, replacement in mutations:
        candidate = copy.deepcopy(original)
        target = candidate
        parts = dotted.split(".")
        for part in parts[:-1]:
            target = target[part]
        target[parts[-1]] = replacement
        with pytest.raises(AssertionError):
            _validate_static(candidate)


def test_q1b_all_runner_guards_fail_closed_without_authority(tmp_path: Path) -> None:
    missing_contract = tmp_path / "contract.json"
    missing_authority = tmp_path / "authority.json"
    args = ["--authority-check-only", "--repository-root", str(ROOT), "--contract", str(missing_contract), "--contract-sha256", "0" * 64, "--authority", str(missing_authority), "--authority-sha256", "0" * 64]
    for name in ("e4_pl_q1b_assembled_producer.py", "e4_pl_q1b_assembled_checker.py", "e4_pl_q1b_bounded_runner.py"):
        result = subprocess.run([sys.executable, str(REF / name), *args], cwd=ROOT, capture_output=True, text=True, timeout=20, check=False)
        assert result.returncode == 2 and "PASS" not in result.stdout
    assert list(tmp_path.iterdir()) == []
