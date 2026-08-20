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

from e4_pl_q1v_authority_guard import (  # noqa: E402
    AUTHORITY_KEYS,
    AuthorityGuardError,
    _verify_contract_content,
)


CONTRACT = REFERENCE_DIR / "e4_pl_q1v_execution_contract.json"
CONTRACT_REVIEW = REFERENCE_DIR / "e4_pl_q1v_contract_review.json"
ENVIRONMENT_RECORD = REFERENCE_DIR / "e4_pl_q1t_environment.json"
COMMIT1 = "7a33044aee429557d770b914130df47105d6bec9"
COMMIT1_TREE = "7ae5c3278aed1e5937d90c308db6f570e424b1f7"
COMMIT2 = "c51f4705a1f0f547ec2265a7846894dba098307d"
COMMIT2_TREE = "b627b32312178e67ee746362fe9233ca97931543"
COMMIT3_SUBJECT = "docs: authorize E4 PL Q1V scientific execution"
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
    independence: Mapping[str, Any],
    reviewed_paths: list[str],
) -> None:
    value, _ = _canonical(path)
    assert set(value) == REVIEW_KEYS
    assert value["schema"] == schema and value["verdict"] == verdict
    assert value["findings"] == []
    assert value["reviewer_independence"] == independence
    assert value["reviewed_inputs"] == sorted((_row(item) for item in reviewed_paths), key=lambda row: row["path"])


def test_q1v_contract_complete_hash_dag() -> None:
    contract, contract_raw = _canonical(CONTRACT)
    allowed, _ = _canonical(REFERENCE_DIR / "e4_pl_q1v_allowed_extent.json")
    inventory, _ = _canonical(REFERENCE_DIR / "e4_pl_q1v_test_inventory.json")
    inheritance, _ = _canonical(REFERENCE_DIR / "e4_pl_q1v_inheritance_manifest.json")
    environment, environment_raw = _canonical(ENVIRONMENT_RECORD)
    terminal, _ = _canonical(REFERENCE_DIR / "e4_pl_q1v_terminal_table.json")

    assert set(contract) == CONTRACT_KEYS
    assert contract["schema"] == "anysolver.s4.e4-pl-q1v-execution-contract-v1"
    assert contract["candidate_id"] == "candidate_e4_pl_q1v.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1"
    assert contract["study_id"] == "study_e4_pl_q1v.q1u_backend_repair_and_local_completion_v1"
    plan_paths = allowed["path_sets"]["PLAN14"]
    implementation_paths = allowed["path_sets"]["IMPLEMENTATION20"]
    contract_paths = allowed["path_sets"]["CONTRACT3"]
    outcome_paths = allowed["path_sets"]["OUTCOME11"]
    _verify_commit(
        contract["commit_ancestry"]["commit1"],
        {
            "commit": COMMIT1,
            "tree": COMMIT1_TREE,
            "parent": "7d4ac30b4d50a1ee62edefbe5fb0198b47276360",
            "subject": "docs: preregister E4 PL Q1V local completion",
            "path_count": 14,
            "paths": plan_paths,
        },
    )
    _verify_commit(
        contract["commit_ancestry"]["commit2"],
        {
            "commit": COMMIT2,
            "tree": COMMIT2_TREE,
            "parent": COMMIT1,
            "subject": "docs: freeze E4 PL Q1V commissioned exact implementations",
            "path_count": 20,
            "paths": implementation_paths,
        },
    )

    assert contract["plan_inputs"]["count"] == 14
    assert [row["path"] for row in contract["plan_inputs"]["rows"]] == plan_paths
    for row in contract["plan_inputs"]["rows"]:
        assert set(row) == {"bytes", "path", "sha256"}
        _bound(row)

    implementation_rows = list(_iter_bound_rows(contract["implementation_inputs"]))
    assert sorted(row["path"] for row in implementation_rows) == sorted(implementation_paths)
    for row in implementation_rows:
        _bound(row)
    assert contract["implementation_inputs"]["authority_guard"]["entrypoint"] == "validate_execution_authority"
    assert contract["implementation_inputs"]["reference"]["implementation_id"] == "Q1V_REFERENCE_STDLIB_FIELD_ALG"
    assert contract["implementation_inputs"]["oracle"]["implementation_id"] == "Q1V_ORACLE_SYMPY_ALGEBRAIC_FIELD"
    assert contract["implementation_inputs"]["scientific_runner"]["runner_id"] == "SCIENTIFIC_TEST_RUNNER"
    assert contract["implementation_inputs"]["commissioning_runner"]["runner_ids"] == [
        "ORACLE_COMMISSIONING_RUNNER",
        "REFERENCE_COMMISSIONING_RUNNER",
    ]
    assert contract["implementation_inputs"]["exact_backend_test"]["node_ids"] == inventory["implementation_inventory"]["node_ids"][:1]
    assert contract["implementation_inputs"]["commissioning_test"]["node_ids"] == inventory["implementation_inventory"]["node_ids"][1:2]
    assert contract["implementation_inputs"]["authority_guard_test"]["node_ids"] == inventory["implementation_inventory"]["node_ids"][2:]

    manifest, _ = _canonical(REFERENCE_DIR / "e4_pl_q1v_implementation_manifest.json")
    assert manifest["correction_cycles"] == {
        "hard_freeze_event": "FIRST_SUCCESSFULLY_WRITTEN_REOPENED_HASH_VERIFIED_COMPLETE_SCHEMA_VALID_EXCLUSIVELY_CREATED_CANONICAL_REGISTERED_CERTIFICATE",
        "implementation_cycles_max": 2,
        "implementation_cycles_used": 1,
        "incident_records": [
            {
                "bytes": 1947,
                "classification": "EXTERNAL_IMPLEMENTATION_CORRECTION_INCIDENT",
                "correction_cycle": 1,
                "external_path_committed": False,
                "sha256": "993A9691E62E119F9A1ACE63D96036486C9F6C1EC9963F355BA9AC7322D3CD82",
            }
        ],
        "plan_cycles_max": 1,
        "plan_cycles_used": 1,
        "registered_scientific_certificate_created": False,
    }
    assert manifest["commissioning"]["correction_cycle"] == 1
    assert manifest["commissioning"]["recommissioned_after_incident_sha256"] == manifest["correction_cycles"]["incident_records"][0]["sha256"]
    assert contract["implementation_inputs"]["manifest"]["sha256"] == _sha256(
        (REFERENCE_DIR / "e4_pl_q1v_implementation_manifest.json").read_bytes()
    )
    assert contract["implementation_inputs"]["backend_conformance"]["verdict"] == "ACCEPT_Q1V_EXACT_BACKEND_CONFORMANCE"
    assert contract["implementation_inputs"]["commissioning_reference"]["determinism_payload_sha256"] == contract["implementation_inputs"]["commissioning_oracle"]["determinism_payload_sha256"]
    assert contract["implementation_inputs"]["commissioning_agreement"]["reference_sha256"] == contract["implementation_inputs"]["commissioning_reference"]["sha256"]
    assert contract["implementation_inputs"]["commissioning_agreement"]["oracle_sha256"] == contract["implementation_inputs"]["commissioning_oracle"]["sha256"]

    assert contract["inherited_inputs"] == {"count": 117, "rows": inheritance["inputs"]}
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
    assert contract["terminal_authority"]["terminal_count"] == 12
    assert contract["terminal_authority"]["evaluation"] == terminal["evaluation"]
    _bound(contract["terminal_authority"])

    authorization = contract["authorization"]
    assert authorization["commit3_subject"] == COMMIT3_SUBJECT
    assert authorization["commit3_path_count"] == 3 and authorization["commit3_paths"] == contract_paths
    assert authorization["token"] == "AUTHORIZE_E4_PL_Q1V_SCIENTIFIC_EXECUTION"
    assert authorization["external_authority_exact_keys"] == sorted(AUTHORITY_KEYS)
    assert contract["commit_ancestry"]["commit2"]["commit"] == COMMIT2
    assert authorization["commit3_paths"] == allowed["path_sets"]["CONTRACT3"]
    assert authorization["commit3_subject"] == COMMIT3_SUBJECT

    authority, _ = _canonical(REFERENCE_DIR / "e4_pl_q1v_authority_contract.json")
    correction = authority["correction_authority"]["correction_dag"]
    assert correction["initial_authorization"] == {
        "authorization_alias": "A_0",
        "cycle": 0,
        "id": "C3",
        "parent": "ACCEPTED_COMMIT2",
        "path_count": 3,
        "paths": list(contract_paths),
        "subject": COMMIT3_SUBJECT,
    }
    assert correction["latest_accepted_authorization"]["cycle_0"] == "A_0_EQUALS_C3"
    assert correction["monotonicity"]["cycles_max"] == 2
    assert [row["revision"]["parent"] for row in correction["revision_cycles"]] == ["A_0", "A_1"]
    assert [row["authorization"]["parent"] for row in correction["revision_cycles"]] == ["R_1", "R_2"]
    assert authority["blocked_routes"]["post_authority_or_reauthorization"]["exact_parent"] == "LATEST_ACCEPTED_AUTHORIZATION"
    assert authority["blocked_routes"]["scientific"]["exact_parent"] == "LATEST_ACCEPTED_AUTHORIZATION"

    commissioning, _ = _canonical(REFERENCE_DIR / "e4_pl_q1v_commissioning_contract.json")
    certificate, _ = _canonical(REFERENCE_DIR / "e4_pl_q1v_certificate_schema.json")
    assert commissioning["recursive_forbidden_content_scan"] is True
    assert {"ENERGY", "STIFFNESS_SIGN", "CLASSIFICATION", "PROPOSED_TERMINAL"} <= set(commissioning["forbidden_content"])
    assert certificate["cross_implementation"]["mode"] == AGREEMENT_MODE
    assert certificate["hard_freeze"]["event"] == authority["hard_scientific_freeze"]["event"]
    assert [row["precedence"] for row in terminal["terminals"]] == list(range(1, 13))
    assert terminal["terminals"][-1]["id"] == "PROVISIONAL_GO_E4_PL_Q1V_Q1B_PLAN"
    assert contract["review_authorities"]["contract"] == {
        "hash_binding": "EXTERNAL_AUTHORITY_RECORD",
        "path": "docs/reference_cases/e4_pl_q1v_contract_review.json",
        "schema": "anysolver.s4.e4-pl-q1v-contract-review-v1",
        "verdict": "ACCEPT_Q1V_EXECUTION_CONTRACT_NO_P0_P1",
    }
    for stage in ("plan", "implementation"):
        _bound(contract["review_authorities"][stage])

    _review(
        REFERENCE_DIR / "e4_pl_q1v_plan_review.json",
        schema="anysolver.s4.e4-pl-q1v-plan-review-v1",
        verdict="ACCEPT_Q1V_PREREGISTRATION_NO_P0_P1",
        independence={
            "mechanics_executed": False,
            "reviewer_role": "INDEPENDENT_PLAN_REVIEWER",
            "same_agent_as_packet_author": False,
        },
        reviewed_paths=[path for path in plan_paths if not path.endswith("plan_review.json")],
    )
    _review(
        REFERENCE_DIR / "e4_pl_q1v_implementation_review.json",
        schema="anysolver.s4.e4-pl-q1v-implementation-review-v1",
        verdict="ACCEPT_Q1V_IMPLEMENTATION_FREEZE_NO_P0_P1",
        independence={
            "authored_review_only": True,
            "mechanics_executed": False,
            "reviewed_input_authorship": False,
            "role": "INDEPENDENT_STATIC_IMPLEMENTATION_REVIEWER",
        },
        reviewed_paths=[path for path in implementation_paths if not path.endswith("implementation_review.json")],
    )
    if CONTRACT_REVIEW.exists():
        _review(
            CONTRACT_REVIEW,
            schema="anysolver.s4.e4-pl-q1v-contract-review-v1",
            verdict="ACCEPT_Q1V_EXECUTION_CONTRACT_NO_P0_P1",
            independence={
                "authored_review_only": True,
                "mechanics_executed": False,
                "reviewed_input_authorship": False,
                "role": "INDEPENDENT_EXECUTION_CONTRACT_REVIEWER",
            },
            reviewed_paths=["docs/reference_cases/e4_pl_q1v_execution_contract.json", "tests/test_e4_pl_q1v_contract.py"],
        )

    head = _git("rev-parse", "HEAD")
    if head == COMMIT2:
        assert _git("diff", "--name-only") == ""
        assert _git("diff", "--cached", "--name-only") == ""
        untracked = {
            line[3:].replace("\\", "/")
            for line in _git("status", "--porcelain=v1", "--untracked-files=all").splitlines()
            if line.startswith("?? ")
        }
        assert {
            "docs/reference_cases/e4_pl_q1v_execution_contract.json",
            "tests/test_e4_pl_q1v_contract.py",
        } <= untracked <= set(contract_paths)
    else:
        assert _git("rev-list", "--parents", "-n", "1", head).split() == [head, COMMIT2]
        assert _git("show", "-s", "--format=%s", head) == COMMIT3_SUBJECT
        assert _changed_paths(head) == sorted(contract_paths)


Mutation = Callable[[dict[str, Any]], None]


def test_q1v_contract_mutation_matrix() -> None:
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
        ("manifest hash", lambda value: value["implementation_inputs"]["manifest"].__setitem__("sha256", "0" * 64)),
        ("commissioning digest", lambda value: value["implementation_inputs"]["commissioning_oracle"].__setitem__("determinism_payload_sha256", "0" * 64)),
        ("inheritance classification", lambda value: value["inherited_inputs"]["rows"][0].__setitem__("classification", "wrong")),
        (
            "environment path alias",
            lambda value: value["environment"].__setitem__("path", value["environment"].pop("record_path")),
        ),
        ("plan review", lambda value: value["review_authorities"]["plan"].__setitem__("verdict", "wrong")),
        ("contract review binding", lambda value: value["review_authorities"]["contract"].__setitem__("hash_binding", "wrong")),
        ("external authority keys", lambda value: value["authorization"]["external_authority_exact_keys"].pop()),
        (
            "agreement alias",
            lambda value: value["agreement"].__setitem__("cross_implementation", "BYTE_IDENTICAL_CANONICAL_COMMON_PAYLOAD"),
        ),
        ("runner inventory", lambda value: value["runner_inventory"].__setitem__("count", 2)),
        ("scientific inventory", lambda value: value["scientific_inventory"].__setitem__("count", 4)),
        ("output absences", lambda value: value["output_absences"].__setitem__("absent_from_commit3_tree", False)),
        ("output path", lambda value: value["output_absences"]["paths"].__setitem__(0, "wrong")),
        ("production", lambda value: value["production_restriction"].__setitem__("legacy_default", "wrong")),
        ("runtime", lambda value: value["runtime"].__setitem__("python_version", "wrong")),
        ("terminal", lambda value: value["terminal_authority"].__setitem__("terminal_count", 10)),
        ("terminal hash", lambda value: value["terminal_authority"].__setitem__("sha256", "0" * 64)),
    ]
    for label, mutate in mutations:
        changed = copy.deepcopy(contract)
        mutate(changed)
        with pytest.raises(AuthorityGuardError, match=".+"):
            _verify_contract_content(ROOT, changed, environment)


def _negative_runner(program: str, runner_id: str, *, output: bool) -> None:
    contract_raw = CONTRACT.read_bytes()
    external_root = Path(tempfile.gettempdir()).resolve(strict=True)
    missing_authority = external_root / f"q1v-missing-authority-{os.getpid()}-{runner_id}.json"
    forbidden_output = external_root / f"q1v-forbidden-output-{os.getpid()}-{runner_id}.json"
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
            b"BLOCKED_E4_PL_Q1V_CONTRACT_OR_NONDETERMINISM",
            b"Q1V_ORACLE_FAIL_CLOSED",
        )
    )
    assert not forbidden_output.exists()
    assert not any((ROOT / path).exists() for path in _canonical(REFERENCE_DIR / "e4_pl_q1v_allowed_extent.json")[0]["path_sets"]["OUTCOME11"])


def test_q1v_reference_runner_guard_fails_closed() -> None:
    _negative_runner("docs/reference_cases/e4_pl_q1v_reference.py", "REFERENCE_RUNNER", output=True)


def test_q1v_oracle_runner_guard_fails_closed() -> None:
    _negative_runner("docs/reference_cases/e4_pl_q1v_oracle.py", "ORACLE_RUNNER", output=True)


def test_q1v_scientific_runner_guard_fails_closed() -> None:
    _negative_runner("docs/reference_cases/e4_pl_q1v_scientific_test_runner.py", "SCIENTIFIC_TEST_RUNNER", output=False)
