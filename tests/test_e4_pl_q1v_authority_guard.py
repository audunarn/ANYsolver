from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
GUARD_PATH = REFERENCE_CASES / "e4_pl_q1v_authority_guard.py"
COMMISSIONING_RUNNER_PATH = REFERENCE_CASES / "e4_pl_q1v_commissioning_runner.py"
SCIENTIFIC_RUNNER_PATH = REFERENCE_CASES / "e4_pl_q1v_scientific_test_runner.py"
AUTHORITY_CONTRACT_PATH = REFERENCE_CASES / "e4_pl_q1v_authority_contract.json"
COMMISSIONING_CONTRACT_PATH = REFERENCE_CASES / "e4_pl_q1v_commissioning_contract.json"


def _load(name: str, path: Path):
    sys.path.insert(0, str(REFERENCE_CASES))
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(REFERENCE_CASES))


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def test_q1v_strict_json_reviews_and_reauthorization_content():
    guard = _load("q1v_guard_strict_test", GUARD_PATH)
    authority_contract_raw = AUTHORITY_CONTRACT_PATH.read_bytes()
    authority_contract = guard.strict_json_bytes(authority_contract_raw)
    commissioning_contract = guard.strict_json_bytes(COMMISSIONING_CONTRACT_PATH.read_bytes())

    expected_authority_keys = set(
        authority_contract["execution_authority_record"]["exact_top_level_keys"]
    )
    assert guard.AUTHORITY_KEYS == expected_authority_keys
    assert guard.HARD_FREEZE_EVENT == authority_contract["hard_scientific_freeze"]["event"]
    assert (
        guard.PRE_CERTIFICATE_REAUTHORIZATION
        == authority_contract["pre_certificate_reauthorization"]["authorization_token"]
    )
    assert guard.STUDY_ID == authority_contract["study_id"]
    assert commissioning_contract["forbidden_content_scan"] == {
        "mode": "RECURSIVE_EXACT_TOKEN_SCAN",
        "rejection": "ANY_FORBIDDEN_TOKEN_IN_ANY_KEY_OR_VALUE_BLOCKS_COMMISSIONING",
        "scope": "ALL_NESTED_MAPPING_KEYS_AND_VALUES_AND_SEQUENCE_VALUES",
    }
    assert "ENERGY" in commissioning_contract["forbidden_content"]
    assert "STIFFNESS_SIGN" in commissioning_contract["forbidden_content"]
    guard._verify_commissioning_contract(commissioning_contract)

    plan_review_raw = (REFERENCE_CASES / "e4_pl_q1v_plan_review.json").read_bytes()
    plan_review = guard.strict_json_bytes(plan_review_raw)
    assert set(plan_review) == guard.REVIEW_KEYS
    assert plan_review["verdict"] == "ACCEPT_Q1V_PREREGISTRATION_NO_P0_P1"
    assert plan_review["findings"] == []
    plan_review_sha256 = guard.sha256_bytes(plan_review_raw)
    assert guard._verify_review(
        ROOT,
        "plan",
        {
            "bytes": len(plan_review_raw),
            "path": "docs/reference_cases/e4_pl_q1v_plan_review.json",
            "schema": "anysolver.s4.e4-pl-q1v-plan-review-v1",
            "sha256": plan_review_sha256,
            "verdict": "ACCEPT_Q1V_PREREGISTRATION_NO_P0_P1",
        },
        plan_review_sha256,
    ) == plan_review
    assert guard.REVIEW_EXPECTATIONS["implementation"]["independence"] == {
        "authored_review_only": True,
        "mechanics_executed": False,
        "reviewed_input_authorship": False,
        "role": "INDEPENDENT_STATIC_IMPLEMENTATION_REVIEWER",
    }

    with pytest.raises(guard.AuthorityGuardError, match="duplicate JSON key"):
        guard.strict_json_bytes(b'{"a":1,"a":2}\n')
    with pytest.raises(guard.AuthorityGuardError, match="not canonical"):
        guard.strict_json_bytes(b'{"b": 1, "a": 2}\n')
    with pytest.raises(guard.AuthorityGuardError, match="non-finite"):
        guard.strict_json_bytes(b'{"a":NaN}\n')

    latest = {
        "commit": "a" * 40,
        "cycle": 2,
        "subject": "docs: reauthorize E4 PL Q1V scientific execution cycle 2",
        "tree": "b" * 40,
    }
    pre_certificate = {
        "all_outcome_paths_absent": True,
        "authorization_token": guard.PRE_CERTIFICATE_REAUTHORIZATION,
        "correction_budget_valid": True,
        "cycle": 2,
        "hard_freeze_event": guard.HARD_FREEZE_EVENT,
        "no_canonical_registered_certificate_exists": True,
    }
    assert guard.strict_json_bytes(_canonical(latest)) == latest
    assert guard.strict_json_bytes(_canonical(pre_certificate)) == pre_certificate


def test_q1v_git_environment_paths_and_output_profiles(tmp_path: Path):
    guard = _load("q1v_guard_paths_test", GUARD_PATH)
    for hostile in ("../escape", "/absolute", "C:\\hostile", "a\\b"):
        with pytest.raises(guard.AuthorityGuardError):
            guard._safe_relative_path(hostile)

    with pytest.raises(guard.AuthorityGuardError, match="absolute"):
        guard._require_external(Path("relative.json"), [ROOT], "probe", directory=False)

    fake_root = tmp_path / "fake-repository"
    fake_root.mkdir()
    guard._verify_output_profile(
        fake_root,
        "REFERENCE_RUNNER",
        "AUTHORITY_CHECK_ONLY",
        b"{}\n",
    )
    forbidden = fake_root / guard.OUTCOME_PATHS[0]
    forbidden.parent.mkdir(parents=True)
    forbidden.write_bytes(b"{}\n")
    with pytest.raises(guard.AuthorityGuardError, match="forbidden outcome"):
        guard._verify_output_profile(
            fake_root,
            "REFERENCE_RUNNER",
            "AUTHORITY_CHECK_ONLY",
            b"{}\n",
        )

    worktree_output = ROOT / "commissioning-attempt.json"
    with pytest.raises(guard.AuthorityGuardError, match="outside every Git worktree"):
        guard._require_external_output(worktree_output, [ROOT], "commissioning output")

    assert guard.ENVIRONMENT_RECORD == "docs/reference_cases/e4_pl_q1t_environment.json"
    assert guard.ENVIRONMENT_SHA256 == (
        "5461206324E7FC2A52B334CE736A512EE71313ED79181438047E3E20069A9746"
    )


def test_q1v_correction_budget_and_hard_freeze_boundary(tmp_path: Path, monkeypatch):
    guard = _load("q1v_guard_cycles_test", GUARD_PATH)
    authority_contract = json.loads(AUTHORITY_CONTRACT_PATH.read_bytes())
    correction = authority_contract["correction_authority"]
    assert correction["cycles_max"] == 2
    assert correction["hard_freeze_event"] == guard.HARD_FREEZE_EVENT
    assert correction["correction_dag"]["monotonicity"] == {
        "cycle_numbers": [0, 1, 2],
        "cycles_max": 2,
        "gaps_reuse_or_decrease_forbidden": True,
        "strictly_increasing": True,
    }

    mandatory = list(correction["mandatory_revision_paths"])
    affected = correction["affected_mutable_program_or_test_paths"][0]
    assert guard._revision_paths_are_authorized(sorted(mandatory + [affected]))
    assert not guard._revision_paths_are_authorized([affected])
    assert not guard._revision_paths_are_authorized(
        sorted(mandatory + ["tests/test_e4_pl_q1v_local_algebra.py"])
    )

    assert guard.COMMISSIONING_RUNNER_IDS == {
        "REFERENCE_COMMISSIONING_RUNNER",
        "ORACLE_COMMISSIONING_RUNNER",
    }
    assert guard.INVOCATION_MODES == {"AUTHORITY_CHECK_ONLY", "EXECUTE"}
    assert len(guard.PLAN_PATHS) == 14
    assert len(guard.IMPLEMENTATION_PATHS) == 20
    assert len(guard.CONTRACT_PATHS) == 3
    assert len(guard.OUTCOME_PATHS) == 11

    incident = "A" * 64
    manifest = tmp_path / "docs" / "reference_cases" / "e4_pl_q1v_implementation_manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_bytes(_canonical({"correction_incident_sha256": incident}))
    derived = {
        "authorization_commit": "1" * 40,
        "authorization_subject": "docs: reauthorize E4 PL Q1V scientific execution cycle 1",
        "authorization_tree": "2" * 40,
        "cycle": 1,
        "revision_changed_paths": sorted(mandatory + [affected]),
        "revision_commit": "3" * 40,
        "revision_subject": "docs: revise E4 PL Q1V implementations before certificate cycle 1",
        "revision_tree": "4" * 40,
    }
    monkeypatch.setattr(
        guard,
        "_authorization_history_from_commit",
        lambda _root, _head: (1, [derived]),
    )
    authority = {
        "authorization_cycle": 1,
        "correction_cycles_used": 1,
        "correction_history": [{**derived, "incident_sha256": incident}],
    }
    assert guard._verify_correction_history(tmp_path, authority, "1" * 40) == 1
    authority["correction_cycles_used"] = 2
    with pytest.raises(guard.AuthorityGuardError, match="usage drift"):
        guard._verify_correction_history(tmp_path, authority, "1" * 40)


def test_q1v_guard_precedes_commissioning_or_scientific_evaluation(monkeypatch):
    guard_tree = ast.parse(GUARD_PATH.read_text(encoding="utf-8"))
    forbidden_imports = {"numpy", "sympy", "mpmath"}
    imported = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(guard_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        (node.module or "").split(".", 1)[0]
        for node in ast.walk(guard_tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert not imported.intersection(forbidden_imports)

    oracle_text = (REFERENCE_CASES / "e4_pl_q1v_oracle.py").read_text(encoding="utf-8")
    reference_text = (REFERENCE_CASES / "e4_pl_q1v_reference.py").read_text(encoding="utf-8")
    scientific_text = SCIENTIFIC_RUNNER_PATH.read_text(encoding="utf-8")
    commissioning_text = COMMISSIONING_RUNNER_PATH.read_text(encoding="utf-8")
    assert oracle_text.index("validate_commissioning_authority(") < oracle_text.index("_commissioning_payload(", oracle_text.index("validate_commissioning_authority("))
    assert reference_text.index("validate_commissioning_authority(") < reference_text.index("commissioning_record(", reference_text.index("validate_commissioning_authority("))
    assert scientific_text.index("validate_execution_authority(", scientific_text.index("def main")) < scientific_text.index("_execute_pytest(", scientific_text.index("def main"))
    assert commissioning_text.index("validate_commissioning_authority(", commissioning_text.index("def run_twice")) < commissioning_text.index("subprocess.run(", commissioning_text.index("def run_twice"))

    scientific = _load("q1v_scientific_guard_order_test", SCIENTIFIC_RUNNER_PATH)
    reached = {"scientific": False}

    def fail_guard(**_kwargs):
        raise scientific.AuthorityGuardError("negative guard probe")

    def forbidden_scientific(*_args, **_kwargs):
        reached["scientific"] = True
        raise AssertionError("scientific evaluation became reachable")

    monkeypatch.setattr(scientific, "validate_execution_authority", fail_guard)
    monkeypatch.setattr(scientific, "_execute_pytest", forbidden_scientific)
    result = scientific.main(
        [
            "--authority-record", "absent-authority.json",
            "--authority-sha256", "0" * 64,
            "--contract", "absent-contract.json",
            "--contract-sha256", "0" * 64,
            "--environment-root", "absent-environment",
            "--environment-record", "absent-record.json",
            "--environment-sha256", "0" * 64,
            "--runner-id", "SCIENTIFIC_TEST_RUNNER",
        ]
    )
    assert result == 2
    assert reached == {"scientific": False}

    commissioning = _load("q1v_commissioning_guard_order_test", COMMISSIONING_RUNNER_PATH)
    reached = {"process": False}

    def fail_commissioning_guard(**_kwargs):
        raise commissioning.AuthorityGuardError("negative commissioning guard probe")

    def forbidden_process(*_args, **_kwargs):
        reached["process"] = True
        raise AssertionError("commissioning process became reachable")

    monkeypatch.setattr(commissioning, "validate_commissioning_authority", fail_commissioning_guard)
    monkeypatch.setattr(commissioning.subprocess, "run", forbidden_process)
    with pytest.raises(commissioning.AuthorityGuardError):
        commissioning.run_twice(
            root=ROOT,
            implementation="oracle",
            contract_path=COMMISSIONING_CONTRACT_PATH,
            contract_sha256="0" * 64,
            environment_root=Path("absent"),
            environment_record=Path("absent"),
            environment_sha256="0" * 64,
            attempt_root=Path("absent"),
            output=Path("absent"),
        )
    assert reached == {"process": False}
