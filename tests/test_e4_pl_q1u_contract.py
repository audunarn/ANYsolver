from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Callable, Iterator, Mapping

import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "docs" / "reference_cases"
sys.path.insert(0, str(REFERENCE_DIR))

from e4_pl_q1u_authority_guard import (  # noqa: E402
    AuthorityGuardError,
    _verify_contract_content,
)


CONTRACT = REFERENCE_DIR / "e4_pl_q1u_execution_contract.json"
CONTRACT_REVIEW = REFERENCE_DIR / "e4_pl_q1u_contract_review.json"
ENVIRONMENT_RECORD = REFERENCE_DIR / "e4_pl_q1t_environment.json"
COMMIT1 = "2404ec3cec03fe9ddef131d9bfd39a24e4e7eabc"
COMMIT1_TREE = "25bc45287495e9349eeebf552e76f88ec70c13b6"
COMMIT2 = "9add6b937d4e2bd5668717f9a9b8d6bd1dfe6cda"
COMMIT2_TREE = "4a4656a8f713d5ed9618f37fe185132c45d08fe2"
COMMIT3_SUBJECT = "docs: authorize E4 PL Q1U scientific execution"
ENVIRONMENT_SHA256 = "5461206324E7FC2A52B334CE736A512EE71313ED79181438047E3E20069A9746"
AGREEMENT_MODE = "BYTE_IDENTICAL_CANONICAL_CERTIFICATE_PAYLOAD"
CONTRACT_KEYS = {
    "agreement",
    "authorization",
    "candidate_id",
    "commit_ancestry",
    "environment",
    "implementation_inputs",
    "inherited_inputs",
    "output_absences",
    "plan_inputs",
    "production_restriction",
    "review_authorities",
    "runner_inventory",
    "runtime",
    "schema",
    "scientific_inventory",
    "study_id",
    "terminal_authority",
}
REVIEW_KEYS = {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"}


def _git(*arguments: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    if check:
        assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, allow_nan=False, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _reject_constant(token: str) -> None:
    raise ValueError(f"nonfinite JSON token: {token}")


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _canonical(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    assert raw.endswith(b"\n") and not raw.endswith(b"\n\n") and b"\r" not in raw
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique_pairs,
        parse_constant=_reject_constant,
    )
    assert isinstance(value, dict)
    assert raw == _canonical_bytes(value)
    return value, raw


def _bound(row: Mapping[str, Any]) -> None:
    assert set(row).issuperset({"bytes", "path", "sha256"})
    relative = Path(str(row["path"]))
    assert not relative.is_absolute() and ".." not in relative.parts
    path = ROOT / relative
    assert path.is_file() and not path.is_symlink()
    raw = path.read_bytes()
    assert row["bytes"] == len(raw)
    assert row["sha256"] == _sha256(raw)


def _changed_paths(commit: str) -> list[str]:
    return sorted(
        line.replace("\\", "/")
        for line in _git("diff-tree", "--no-commit-id", "--name-only", "-r", commit).splitlines()
        if line
    )


def _verify_commit(row: Mapping[str, Any], expected: Mapping[str, Any]) -> None:
    assert set(row) == {"commit", "tree", "parent", "subject", "path_count", "paths"}
    assert row == expected
    commit = str(row["commit"])
    assert _git("rev-list", "--parents", "-n", "1", commit).split() == [commit, row["parent"]]
    assert _git("rev-parse", f"{commit}^{{tree}}") == row["tree"]
    assert _git("show", "-s", "--format=%s", commit) == row["subject"]
    assert _changed_paths(commit) == sorted(row["paths"])


def _iter_bound_rows(value: Any) -> Iterator[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        if {"bytes", "path", "sha256"}.issubset(value):
            yield value
        for nested in value.values():
            yield from _iter_bound_rows(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_bound_rows(nested)


def _row(path: str) -> dict[str, Any]:
    raw = (ROOT / path).read_bytes()
    return {"bytes": len(raw), "path": path, "sha256": _sha256(raw)}


def _review(
    path: Path,
    *,
    schema: str,
    verdict: str,
    role: str,
    reviewed_paths: list[str],
) -> None:
    value, _ = _canonical(path)
    assert set(value) == REVIEW_KEYS
    assert value["schema"] == schema and value["verdict"] == verdict
    assert value["findings"] == []
    assert value["reviewer_independence"] == {
        "authored_review_only": True,
        "mechanics_executed": False,
        "reviewed_input_authorship": False,
        "role": role,
    }
    assert value["reviewed_inputs"] == sorted((_row(item) for item in reviewed_paths), key=lambda row: row["path"])


def test_q1u_contract_complete_hash_dag() -> None:
    contract, contract_raw = _canonical(CONTRACT)
    allowed, _ = _canonical(REFERENCE_DIR / "e4_pl_q1u_allowed_extent.json")
    inventory, _ = _canonical(REFERENCE_DIR / "e4_pl_q1u_test_inventory.json")
    inheritance, _ = _canonical(REFERENCE_DIR / "e4_pl_q1u_inheritance_manifest.json")
    environment, environment_raw = _canonical(ENVIRONMENT_RECORD)
    terminal, _ = _canonical(REFERENCE_DIR / "e4_pl_q1u_terminal_table.json")

    assert set(contract) == CONTRACT_KEYS
    assert contract["schema"] == "anysolver.s4.e4-pl-q1u-execution-contract-v1"
    assert contract["candidate_id"] == "candidate_e4_pl_q1u.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1"
    assert contract["study_id"] == "study_e4_pl_q1u.q1t_frozen_mechanics_execution_guard_completion_v1"
    plan_paths = allowed["path_sets"]["PLAN12"]
    implementation_paths = allowed["path_sets"]["IMPLEMENTATION14"]
    contract_paths = allowed["path_sets"]["CONTRACT3"]
    outcome_paths = allowed["path_sets"]["OUTCOME11"]
    _verify_commit(
        contract["commit_ancestry"]["commit1"],
        {
            "commit": COMMIT1,
            "tree": COMMIT1_TREE,
            "parent": "850733cc9d2f9185d0a73c5fa6c0acd89067caba",
            "subject": "docs: preregister E4 PL Q1U execution-guard completion",
            "path_count": 12,
            "paths": plan_paths,
        },
    )
    _verify_commit(
        contract["commit_ancestry"]["commit2"],
        {
            "commit": COMMIT2,
            "tree": COMMIT2_TREE,
            "parent": COMMIT1,
            "subject": "docs: freeze E4 PL Q1U guard-corrected implementations",
            "path_count": 14,
            "paths": implementation_paths,
        },
    )

    assert contract["plan_inputs"]["count"] == 12
    assert [row["path"] for row in contract["plan_inputs"]["rows"]] == plan_paths
    for row in contract["plan_inputs"]["rows"]:
        assert set(row) == {"bytes", "path", "sha256"}
        _bound(row)

    implementation_rows = list(_iter_bound_rows(contract["implementation_inputs"]))
    assert sorted(row["path"] for row in implementation_rows) == sorted(implementation_paths)
    for row in implementation_rows:
        _bound(row)
    assert contract["implementation_inputs"]["authority_guard"]["entrypoint"] == "validate_execution_authority"
    assert contract["implementation_inputs"]["reference"]["implementation_id"] == "Q1U_REFERENCE_STDLIB_FIELD_ALG"
    assert contract["implementation_inputs"]["oracle"]["implementation_id"] == "Q1U_ORACLE_SYMPY_ALGEBRAIC_FIELD"
    assert contract["implementation_inputs"]["scientific_runner"]["runner_id"] == "SCIENTIFIC_TEST_RUNNER"
    assert contract["implementation_inputs"]["exact_backend_test"]["node_ids"] == inventory["implementation_inventory"]["node_ids"][:1]
    assert contract["implementation_inputs"]["authority_guard_test"]["node_ids"] == inventory["implementation_inventory"]["node_ids"][1:]

    assert contract["inherited_inputs"] == {"count": 82, "rows": inheritance["inputs"]}
    for row in contract["inherited_inputs"]["rows"]:
        assert set(row) == {"bytes", "classification", "git_blob", "path", "sha256", "source_commit", "source_tree"}
        _bound(row)
        assert _git("rev-parse", f"{row['source_commit']}^{{tree}}") == row["source_tree"]
        assert _git("rev-parse", f"{row['source_commit']}:{row['path']}") == row["git_blob"]

    graph_raw = _canonical_bytes(environment["extracted_file_hash_graph"])
    assert len(environment["extracted_file_hash_graph"]) == 1662
    assert hashlib.sha256(graph_raw).hexdigest() == environment["extracted_file_hash_graph_sha256"]
    assert contract["environment"] == {
        "record_path": "docs/reference_cases/e4_pl_q1t_environment.json",
        "bytes": len(environment_raw),
        "sha256": ENVIRONMENT_SHA256,
        "schema": "e4_pl_q1t_environment_record_v1",
        "environment_id": "e4_pl_q1t_external_exact_environment_v1",
        "external_root_required": True,
        "extracted_file_count": 1662,
        "extracted_file_hash_graph_sha256": environment["extracted_file_hash_graph_sha256"],
    }
    assert "path" not in contract["environment"]
    assert contract["agreement"]["cross_implementation"] == AGREEMENT_MODE
    assert "BYTE_IDENTICAL_CANONICAL_COMMON_PAYLOAD" not in contract_raw.decode("utf-8")
    assert contract["runner_inventory"] == {
        "count": 3,
        "runner_ids": ["REFERENCE_RUNNER", "ORACLE_RUNNER", "SCIENTIFIC_TEST_RUNNER"],
    }
    assert contract["scientific_inventory"] == {
        "count": 5,
        "inventories_separate": True,
        "node_ids": inventory["scientific_inventory"]["node_ids"],
    }
    assert contract["output_absences"] == {"absent_from_commit3_tree": True, "paths": outcome_paths}
    assert not any((ROOT / item).exists() for item in outcome_paths)
    assert contract["terminal_authority"]["terminal_count"] == 11
    assert contract["terminal_authority"]["evaluation"] == terminal["evaluation"]
    _bound(contract["terminal_authority"])

    authorization = contract["authorization"]
    assert authorization["commit3_subject"] == COMMIT3_SUBJECT
    assert authorization["commit3_path_count"] == 3 and authorization["commit3_paths"] == contract_paths
    assert authorization["token"] == "AUTHORIZE_E4_PL_Q1U_SCIENTIFIC_EXECUTION"
    assert authorization["external_authority_exact_keys"] == sorted(
        [
            "schema", "authorization", "candidate_id", "study_id", "commit", "tree",
            "execution_contract_sha256", "environment_sha256", "plan_review_sha256",
            "implementation_review_sha256", "contract_review_sha256", "review_verdicts", "runner_ids",
        ]
    )
    assert contract["review_authorities"]["contract"] == {
        "hash_binding": "EXTERNAL_AUTHORITY_RECORD",
        "path": "docs/reference_cases/e4_pl_q1u_contract_review.json",
        "schema": "anysolver.s4.e4-pl-q1u-contract-review-v1",
        "verdict": "ACCEPT_Q1U_EXECUTION_CONTRACT_NO_P0_P1",
    }
    for stage in ("plan", "implementation"):
        _bound(contract["review_authorities"][stage])

    _review(
        REFERENCE_DIR / "e4_pl_q1u_plan_review.json",
        schema="anysolver.s4.e4-pl-q1u-plan-review-v1",
        verdict="ACCEPT_Q1U_PREREGISTRATION_NO_P0_P1",
        role="INDEPENDENT_PLAN_ONLY_REVIEWER",
        reviewed_paths=[path for path in plan_paths if not path.endswith("plan_review.json")],
    )
    _review(
        REFERENCE_DIR / "e4_pl_q1u_implementation_review.json",
        schema="anysolver.s4.e4-pl-q1u-implementation-review-v1",
        verdict="ACCEPT_Q1U_IMPLEMENTATION_FREEZE_NO_P0_P1",
        role="INDEPENDENT_IMPLEMENTATION_REVIEWER",
        reviewed_paths=[path for path in implementation_paths if not path.endswith("implementation_review.json")],
    )
    if CONTRACT_REVIEW.exists():
        _review(
            CONTRACT_REVIEW,
            schema="anysolver.s4.e4-pl-q1u-contract-review-v1",
            verdict="ACCEPT_Q1U_EXECUTION_CONTRACT_NO_P0_P1",
            role="INDEPENDENT_EXECUTION_CONTRACT_REVIEWER",
            reviewed_paths=["docs/reference_cases/e4_pl_q1u_execution_contract.json", "tests/test_e4_pl_q1u_contract.py"],
        )

    head = _git("rev-parse", "HEAD")
    if head == COMMIT2:
        assert _git("diff", "--name-only") == ""
        assert _git("diff", "--cached", "--name-only") == ""
    else:
        assert _git("rev-list", "--parents", "-n", "1", head).split() == [head, COMMIT2]
        assert _git("show", "-s", "--format=%s", head) == COMMIT3_SUBJECT
        assert _changed_paths(head) == sorted(contract_paths)


Mutation = Callable[[dict[str, Any]], None]


def test_q1u_contract_mutation_matrix() -> None:
    contract, _ = _canonical(CONTRACT)
    environment, _ = _canonical(ENVIRONMENT_RECORD)
    assert _verify_contract_content(ROOT, contract, environment) == (COMMIT1, COMMIT2)

    mutations: list[tuple[str, Mutation]] = [
        ("extra top key", lambda value: value.__setitem__("extra", True)),
        ("schema", lambda value: value.__setitem__("schema", "wrong")),
        ("candidate", lambda value: value.__setitem__("candidate_id", "wrong")),
        ("study", lambda value: value.__setitem__("study_id", "wrong")),
        ("authorization", lambda value: value["authorization"].__setitem__("token", "wrong")),
        ("commit tree", lambda value: value["commit_ancestry"]["commit2"].__setitem__("tree", "0" * 40)),
        ("plan hash", lambda value: value["plan_inputs"]["rows"][0].__setitem__("sha256", "0" * 64)),
        ("guard entrypoint", lambda value: value["implementation_inputs"]["authority_guard"].__setitem__("entrypoint", "wrong")),
        ("inheritance classification", lambda value: value["inherited_inputs"]["rows"][0].__setitem__("classification", "wrong")),
        (
            "environment path alias",
            lambda value: value["environment"].__setitem__("path", value["environment"].pop("record_path")),
        ),
        ("plan review", lambda value: value["review_authorities"]["plan"].__setitem__("verdict", "wrong")),
        ("contract review binding", lambda value: value["review_authorities"]["contract"].__setitem__("hash_binding", "wrong")),
        (
            "agreement alias",
            lambda value: value["agreement"].__setitem__("cross_implementation", "BYTE_IDENTICAL_CANONICAL_COMMON_PAYLOAD"),
        ),
        ("runner inventory", lambda value: value["runner_inventory"].__setitem__("count", 2)),
        ("scientific inventory", lambda value: value["scientific_inventory"].__setitem__("count", 4)),
        ("output absences", lambda value: value["output_absences"].__setitem__("absent_from_commit3_tree", False)),
        ("production", lambda value: value["production_restriction"].__setitem__("legacy_default", "wrong")),
        ("runtime", lambda value: value["runtime"].__setitem__("python_version", "wrong")),
        ("terminal", lambda value: value["terminal_authority"].__setitem__("terminal_count", 10)),
    ]
    for label, mutate in mutations:
        changed = copy.deepcopy(contract)
        mutate(changed)
        with pytest.raises(AuthorityGuardError, match=".+"):
            _verify_contract_content(ROOT, changed, environment)


def _negative_runner(program: str, runner_id: str, *, output: bool) -> None:
    contract_raw = CONTRACT.read_bytes()
    external_root = Path(tempfile.gettempdir()).resolve(strict=True)
    missing_authority = external_root / f"q1u-missing-authority-{os.getpid()}-{runner_id}.json"
    forbidden_output = external_root / f"q1u-forbidden-output-{os.getpid()}-{runner_id}.json"
    assert not missing_authority.exists() and not forbidden_output.exists()
    command = [
        sys.executable,
        str(ROOT / program),
        "--authority-record", str(missing_authority),
        "--authority-sha256", "0" * 64,
        "--contract", str(CONTRACT),
        "--contract-sha256", _sha256(contract_raw),
        "--environment-root", str(external_root),
        "--environment-record", str(ENVIRONMENT_RECORD),
        "--environment-sha256", ENVIRONMENT_SHA256,
        "--runner-id", runner_id,
    ]
    if output:
        command.extend(["--execute", "--output", str(forbidden_output)])
    completed = subprocess.run(command, cwd=ROOT, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert completed.returncode == 2
    assert any(
        token in completed.stderr
        for token in (
            b"BLOCKED_E4_PL_Q1U_CONTRACT_OR_NONDETERMINISM",
            b"Q1U_ORACLE_FAIL_CLOSED",
        )
    )
    assert not forbidden_output.exists()
    assert not any((ROOT / path).exists() for path in _canonical(REFERENCE_DIR / "e4_pl_q1u_allowed_extent.json")[0]["path_sets"]["OUTCOME11"])


def test_q1u_reference_runner_guard_fails_closed() -> None:
    _negative_runner("docs/reference_cases/e4_pl_q1u_reference.py", "REFERENCE_RUNNER", output=True)


def test_q1u_oracle_runner_guard_fails_closed() -> None:
    _negative_runner("docs/reference_cases/e4_pl_q1u_oracle.py", "ORACLE_RUNNER", output=True)


def test_q1u_scientific_runner_guard_fails_closed() -> None:
    _negative_runner("docs/reference_cases/e4_pl_q1u_scientific_test_runner.py", "SCIENTIFIC_TEST_RUNNER", output=False)
