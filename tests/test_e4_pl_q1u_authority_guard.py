from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "docs/reference_cases"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


GUARD = _load_module("e4_pl_q1u_authority_guard_for_test", CASES / "e4_pl_q1u_authority_guard.py")
sys.modules["e4_pl_q1u_authority_guard"] = GUARD


def _canonical(value: object) -> bytes:
    return (
        json.dumps(value, allow_nan=False, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _write(path: Path, value: object) -> bytes:
    raw = _canonical(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return raw


def test_q1u_strict_json_reviews_and_vocabulary() -> None:
    assert GUARD.strict_json_bytes(b'{"a":1}\n') == {"a": 1}
    for raw in (
        b'{"a":1,"a":2}\n',
        b'{"a":NaN}\n',
        b'{"a":1}\r\n',
        b'{ "a":1}\n',
        b'\xef\xbb\xbf{"a":1}\n',
    ):
        with pytest.raises(GUARD.AuthorityGuardError):
            GUARD.strict_json_bytes(raw)

    vocabulary = GUARD.strict_json_bytes((CASES / "e4_pl_q1u_contract_vocabulary.json").read_bytes())
    assert vocabulary["environment"]["canonical_record_field"] == "environment.record_path"
    assert vocabulary["environment"]["forbidden_aliases"] == ["environment.path"]
    assert vocabulary["agreement"]["canonical_mode"] == "BYTE_IDENTICAL_CANONICAL_CERTIFICATE_PAYLOAD"
    assert vocabulary["agreement"]["forbidden_aliases"] == ["BYTE_IDENTICAL_CANONICAL_COMMON_PAYLOAD"]

    review = GUARD.strict_json_bytes((CASES / "e4_pl_q1u_plan_review.json").read_bytes())
    assert set(review) == GUARD.REVIEW_KEYS
    assert review["findings"] == []
    assert review["reviewer_independence"] == {
        "authored_review_only": True,
        "mechanics_executed": False,
        "reviewed_input_authorship": False,
        "role": "INDEPENDENT_PLAN_ONLY_REVIEWER",
    }


def test_q1u_git_environment_and_path_rejection(tmp_path: Path) -> None:
    git_root = Path(GUARD._run_git(ROOT, "rev-parse", "--show-toplevel")).resolve(strict=True)
    assert os.path.normcase(os.path.normpath(git_root)) == os.path.normcase(os.path.normpath(ROOT.resolve()))
    assert GUARD._safe_relative_path("docs/reference_cases/value.json") == "docs/reference_cases/value.json"
    for value in ("/absolute", "../escape", "docs/../escape", r"docs\value"):
        with pytest.raises(GUARD.AuthorityGuardError):
            GUARD._safe_relative_path(value)

    worktrees = GUARD._worktree_roots(ROOT)
    with pytest.raises(GUARD.AuthorityGuardError):
        GUARD._require_external(ROOT / "pyproject.toml", worktrees, "authority record", directory=False)
    missing = tmp_path / "missing-authority.json"
    with pytest.raises(GUARD.AuthorityGuardError):
        GUARD.validate_execution_authority(
            repository_root=ROOT,
            runner_id="REFERENCE_RUNNER",
            authority_record_path=missing,
            authority_sha256="0" * 64,
            contract_path=CASES / "e4_pl_q1u_execution_contract.json",
            contract_sha256="0" * 64,
            environment_root=tmp_path,
            environment_record_path=CASES / "e4_pl_q1t_environment.json",
            environment_sha256=GUARD.ENVIRONMENT_SHA256,
            invocation_mode="AUTHORITY_CHECK_ONLY",
        )


def test_q1u_runner_output_profiles(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    authority = {"schema": "authority"}
    authority_raw = _canonical(authority)
    GUARD._verify_output_profile(root, "REFERENCE_RUNNER", "EXECUTE", authority_raw)
    GUARD._verify_output_profile(root, "SCIENTIFIC_TEST_RUNNER", "AUTHORITY_CHECK_ONLY", authority_raw)

    payload = {"classification": {"terminal": "PROVISIONAL_GO_E4_PL_Q1U_Q1B_PLAN"}}
    payload_sha = hashlib.sha256(_canonical(payload)).hexdigest().upper()
    reference = {
        "certificate_payload": payload,
        "certificate_payload_sha256": payload_sha,
        "implementation_id": "Q1U_REFERENCE_STDLIB_FIELD_ALG",
    }
    oracle = {
        "certificate_payload": payload,
        "certificate_payload_sha256": payload_sha,
        "implementation_id": "Q1U_ORACLE_SYMPY_ALGEBRAIC_FIELD",
    }
    reference_raw = _write(root / GUARD.OUTCOME_PATHS[0], reference)
    oracle_raw = _write(root / GUARD.OUTCOME_PATHS[1], oracle)
    agreement = {
        "byte_identical_certificate_payload": True,
        "certificate_payload_sha256": payload_sha,
        "oracle": {
            "deterministic": True,
            "run1_sha256": hashlib.sha256(oracle_raw).hexdigest().upper(),
            "run2_sha256": hashlib.sha256(oracle_raw).hexdigest().upper(),
            "sha256": hashlib.sha256(oracle_raw).hexdigest().upper(),
        },
        "reference": {
            "deterministic": True,
            "run1_sha256": hashlib.sha256(reference_raw).hexdigest().upper(),
            "run2_sha256": hashlib.sha256(reference_raw).hexdigest().upper(),
            "sha256": hashlib.sha256(reference_raw).hexdigest().upper(),
        },
    }
    agreement_raw = _write(root / GUARD.OUTCOME_PATHS[2], agreement)
    _write(
        root / GUARD.OUTCOME_PATHS[3],
        {
            "agreement_sha256": hashlib.sha256(agreement_raw).hexdigest().upper(),
            "certificate_payload": payload,
        },
    )
    (root / GUARD.OUTCOME_PATHS[5]).parent.mkdir(parents=True, exist_ok=True)
    (root / GUARD.OUTCOME_PATHS[5]).write_bytes(authority_raw)
    GUARD._verify_output_profile(root, "SCIENTIFIC_TEST_RUNNER", "EXECUTE", authority_raw)

    _write(root / GUARD.OUTCOME_PATHS[4], {"forbidden": True})
    with pytest.raises(GUARD.AuthorityGuardError):
        GUARD._verify_output_profile(root, "SCIENTIFIC_TEST_RUNNER", "EXECUTE", authority_raw)


def test_q1u_guard_precedes_registered_evaluation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    reference = _load_module("e4_pl_q1u_reference_guard_order", CASES / "e4_pl_q1u_reference.py")
    called = False

    def forbidden_contracts() -> dict[str, object]:
        nonlocal called
        called = True
        raise AssertionError("registered contracts became reachable before authority")

    monkeypatch.setattr(reference, "_contracts", forbidden_contracts)
    missing = tmp_path / "missing-authority.json"
    result = reference.main(
        [
            "--execute",
            "--authority-record",
            str(missing),
            "--authority-sha256",
            "0" * 64,
            "--contract",
            str(CASES / "e4_pl_q1u_execution_contract.json"),
            "--contract-sha256",
            "0" * 64,
            "--environment-root",
            str(tmp_path),
            "--environment-record",
            str(CASES / "e4_pl_q1t_environment.json"),
            "--environment-sha256",
            GUARD.ENVIRONMENT_SHA256,
            "--runner-id",
            "REFERENCE_RUNNER",
            "--output",
            str(tmp_path / "output.json"),
        ]
    )
    assert result == 2
    assert called is False

    guard_called = False

    def forbidden_guard(**_kwargs: object) -> object:
        nonlocal guard_called
        guard_called = True
        raise AssertionError("shared guard reached for the wrong executable runner id")

    monkeypatch.setattr(reference, "validate_execution_authority", forbidden_guard)
    wrong_reference = reference.main(
        [
            "--authority-check-only",
            "--authority-record",
            str(missing),
            "--authority-sha256",
            "0" * 64,
            "--contract",
            str(CASES / "e4_pl_q1u_execution_contract.json"),
            "--contract-sha256",
            "0" * 64,
            "--environment-root",
            str(tmp_path),
            "--environment-record",
            str(CASES / "e4_pl_q1t_environment.json"),
            "--environment-sha256",
            GUARD.ENVIRONMENT_SHA256,
            "--runner-id",
            "ORACLE_RUNNER",
        ]
    )
    assert wrong_reference == 2
    assert guard_called is False

    scientific_runner = _load_module(
        "e4_pl_q1u_scientific_runner_guard_order",
        CASES / "e4_pl_q1u_scientific_test_runner.py",
    )
    monkeypatch.setattr(scientific_runner, "validate_execution_authority", forbidden_guard)
    wrong_scientific_runner = scientific_runner.main(
        [
            "--authority-check-only",
            "--authority-record",
            str(missing),
            "--authority-sha256",
            "0" * 64,
            "--contract",
            str(CASES / "e4_pl_q1u_execution_contract.json"),
            "--contract-sha256",
            "0" * 64,
            "--environment-root",
            str(tmp_path),
            "--environment-record",
            str(CASES / "e4_pl_q1t_environment.json"),
            "--environment-sha256",
            GUARD.ENVIRONMENT_SHA256,
            "--runner-id",
            "REFERENCE_RUNNER",
        ]
    )
    assert wrong_scientific_runner == 2
    assert guard_called is False

    source = (CASES / "e4_pl_q1u_scientific_test_runner.py").read_text(encoding="utf-8")
    assert source.index("validate_execution_authority(") < source.index("_execute_pytest(", source.index("def main"))
