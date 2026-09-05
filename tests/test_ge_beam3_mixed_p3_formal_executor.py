from __future__ import annotations

import ast
from dataclasses import replace
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "docs/reference_cases/ge_beam3_mixed_p3_formal_executor.py"
CONTRACT = ROOT / "docs/reference_cases/ge_beam3_mixed_p3_formal_contract.json"
SPEC = importlib.util.spec_from_file_location("_ge_beam3_p3_formal_executor", PROGRAM)
assert SPEC is not None and SPEC.loader is not None
executor = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = executor
SPEC.loader.exec_module(executor)


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(executor.canonical_bytes(value))


def _runtime() -> dict[str, object]:
    return {"frozen": True}


def _wheelhouse() -> dict[str, object]:
    return {
        "file_count": executor.WHEELHOUSE_FILE_COUNT,
        "files": [{"bytes": 1, "path": f"wheel-{index}.whl", "sha256": "A" * 64}
                  for index in range(executor.WHEELHOUSE_FILE_COUNT)],
        "sha256": executor.WHEELHOUSE_SHA256,
        "total_bytes": executor.WHEELHOUSE_TOTAL_BYTES,
    }


def _authority(tmp_path: Path, mode: str = "package") -> dict[str, object]:
    repository = (tmp_path / "repo").resolve()
    wheelhouse = (tmp_path / "wheelhouse").resolve()
    registry = (tmp_path / "registry").resolve()
    locations = {
        "authority": str(repository / executor.AUTHORITY_PATHS[mode][0]),
        "candidate_wheel": None, "executor": str(repository / executor.EXECUTOR_RELATIVE),
        "output": str((tmp_path / f"{mode}-result.json").resolve()),
        "package_aggregate": None, "package_receipt": None,
        "registry": str(registry), "repository": str(repository),
        "review": str(repository / executor.AUTHORITY_PATHS[mode][1]),
        "wheelhouse": str(wheelhouse),
        "work_root": str((tmp_path / f"{mode}-work").resolve()),
    }
    if mode == "performance":
        locations.update({
            "candidate_wheel": str((tmp_path / "candidate.whl").resolve()),
            "package_aggregate": str((tmp_path / "package-aggregate.json").resolve()),
            "package_receipt": str((tmp_path / "package-receipt.json").resolve()),
        })
    request = {
        "attempt_id": "2" * 32, "bounds": executor.BOUNDS,
        "formal_argv": executor._expected_formal_argv(mode, locations),
        "locations": locations, "mode": mode, "request_id": "1" * 32,
        "schema": executor.REQUEST_SCHEMA, "study_id": executor.STUDY_ID,
    }
    package_input = None
    if mode == "performance":
        package_input = {
            "aggregate": {"bytes": 1, "filename": "package-aggregate.json", "sha256": "B" * 64},
            "package_authority_sha256": "C" * 64,
            "package_request_id": "3" * 32,
            "receipt": {"bytes": 1, "filename": "package-receipt.json", "sha256": "D" * 64},
            "wheel": {"bytes": 1, "filename": "candidate.whl", "sha256": "E" * 64},
        }
    return {
        "activation_authorized": False,
        "candidate": {"candidate_id": executor.CANDIDATE_ID,
                      "commit": executor.CANDIDATE_COMMIT,
                      "formulation_id": executor.FORMULATION_ID,
                      "gate_sha256": executor.GATE_SHA256,
                      "manifest_sha256": "F" * 64, "selector": "ge-beam3",
                      "tree": executor.CANDIDATE_TREE},
        "execution": executor.BOUNDS, "execution_authorized": True,
        "formal_argv": request["formal_argv"],
        "harness": {"commit": "a" * 40,
                    "files": [{"bytes": 1, "path": path, "sha256": "A" * 64}
                              for path in executor.HARNESS_PATHS], "tree": "b" * 40},
        "locations": locations, "mode": mode,
        "overlay": {"exact_paths": list(executor.AUTHORITY_PATHS[mode]),
                    "expected_parent": "a" * 40,
                    "subject": executor.AUTHORITY_SUBJECTS[mode]},
        "package_input": package_input, "prior_incident": executor.PRIOR_INCIDENT,
        "publication_authorized": False,
        "request": {"attempt_id": "2" * 32,
                    "record_sha256": hashlib.sha256(executor.canonical_bytes(request)).hexdigest().upper(),
                    "request_id": "1" * 32},
        "runtime": {"identity": _runtime(),
                    "sha256": hashlib.sha256(executor.canonical_bytes(_runtime())).hexdigest().upper()},
        "schema": executor.SCHEMA, "study_id": executor.STUDY_ID,
        "wheelhouse": _wheelhouse(),
    }


def _validated(tmp_path: Path, mode: str = "package") -> object:
    authority = _authority(tmp_path, mode)
    return executor.ValidatedAuthority(
        mode, authority, {"bytes": 1, "filename": "authority.json", "sha256": "B" * 64},
        "c" * 40, "d" * 40,
        {"bytes": 1, "filename": "review.json", "sha256": "C" * 64},
        authority["runtime"]["sha256"], executor.WHEELHOUSE_SHA256,
    )


def _blocked_pair(tmp_path: Path, validated: object) -> tuple[Path, Path]:
    core = {
        "authority": {"commit": validated.authority_commit,
                      "sha256": validated.authority_identity["sha256"],
                      "tree": validated.authority_tree},
        "candidate": {"commit": executor.CANDIDATE_COMMIT, "tree": executor.CANDIDATE_TREE},
        "diagnostic_artifacts": [], "gate": {"aggregate": None, "wheel": None},
        "mode": validated.mode, "request_id": validated.authority["request"]["request_id"],
        "runtime_sha256": validated.runtime_sha256, "schema": executor.RESULT_SCHEMA,
        "terminal": executor.TERMINAL_BLOCKED_PROCESS,
        "wheelhouse_sha256": executor.WHEELHOUSE_SHA256,
    }
    receipt = {
        "aggregate_core": core,
        "aggregate_core_sha256": hashlib.sha256(executor.canonical_bytes(core)).hexdigest().upper(),
        "attempt_id": validated.authority["request"]["attempt_id"],
        "authority_commit": validated.authority_commit,
        "authority_sha256": validated.authority_identity["sha256"],
        "claim_sha256": "D" * 64,
        "request_id": validated.authority["request"]["request_id"],
        "request_record_sha256": validated.authority["request"]["record_sha256"],
        "runtime_sha256": validated.runtime_sha256, "schema": executor.RECEIPT_SCHEMA,
        "terminal": executor.TERMINAL_BLOCKED_PROCESS,
        "wheelhouse_sha256": executor.WHEELHOUSE_SHA256,
    }
    receipt_raw = executor.canonical_bytes(receipt)
    result = {**core, "consumption": {
        "attempt_claim_sha256": "D" * 64,
        "receipt_sha256": hashlib.sha256(receipt_raw).hexdigest().upper(),
        "request_claim_sha256": "D" * 64,
    }}
    result_path, receipt_path = tmp_path / "formal-result.json", tmp_path / "receipt.json"
    _write(result_path, result); receipt_path.write_bytes(receipt_raw)
    return result_path, receipt_path


def test_canonical_json_rejects_duplicate_nonfinite_and_noncanonical(tmp_path: Path) -> None:
    for index, raw in enumerate((b'{"a":1,"a":2}\n', b'{"a":NaN}\n', b'{"a": 1}\n')):
        path = tmp_path / f"bad-{index}.json"; path.write_bytes(raw)
        with pytest.raises(executor.FormalExecutionError):
            executor.strict_json(path)


def test_authority_schema_rejects_injection_and_unfrozen_scope(tmp_path: Path) -> None:
    authority = _authority(tmp_path)
    assert executor._validate_authority(
        authority, mode="package", runtime=_runtime(), wheelhouse=_wheelhouse()) == authority
    for key, value in (("command", ["python", "evil.py"]), ("callback", "evil")):
        changed = {**authority, key: value}
        with pytest.raises(executor.FormalExecutionError, match="keys"):
            executor._validate_authority(changed, mode="package", runtime=_runtime(), wheelhouse=_wheelhouse())
    changed = {**authority, "activation_authorized": True}
    with pytest.raises(executor.FormalExecutionError, match="scope"):
        executor._validate_authority(changed, mode="package", runtime=_runtime(), wheelhouse=_wheelhouse())
    changed = {**authority, "prior_incident": {
        **executor.PRIOR_INCIDENT, "worker_started": True}}
    with pytest.raises(executor.FormalExecutionError, match="incident"):
        executor._validate_authority(changed, mode="package", runtime=_runtime(), wheelhouse=_wheelhouse())
    changed = {**authority, "request": {
        **authority["request"], "request_id": executor.PRIOR_INCIDENT["request_id"]}}
    with pytest.raises(executor.FormalExecutionError, match="reused"):
        executor._validate_authority(changed, mode="package", runtime=_runtime(), wheelhouse=_wheelhouse())


def test_external_request_and_unique_claim_consume_once(tmp_path: Path) -> None:
    validated = _validated(tmp_path)
    registry = tmp_path / "registry"; (registry / "requests").mkdir(parents=True)
    _write(registry / "requests" / f"{'1' * 32}.json", executor._request_record(validated))
    claim = executor._acquire_claim(validated, registry)
    assert claim.request_path.is_file() and claim.attempt_path.is_file()
    executor._release_lock(claim)
    with pytest.raises(executor.FormalExecutionError, match="consumed"):
        executor._acquire_claim(validated, registry)
    assert not (registry / "active.lock").exists()


def test_receipt_precedes_atomic_publication_and_recovery(tmp_path: Path,
                                                          monkeypatch: pytest.MonkeyPatch) -> None:
    validated = _validated(tmp_path)
    registry = tmp_path / "registry"; (registry / "requests").mkdir(parents=True)
    _write(registry / "requests" / f"{'1' * 32}.json", executor._request_record(validated))
    claim = executor._acquire_claim(validated, registry)
    core = _blocked_pair(tmp_path / "template", validated)
    _raw, result = executor.strict_json(core[0]); result.pop("consumption")
    output = tmp_path / "published/result.json"
    original = os.replace
    def checked_replace(source: object, destination: object) -> None:
        assert claim.receipt_path.is_file()
        original(source, destination)
    monkeypatch.setattr(executor.os, "replace", checked_replace)
    made = executor._publish(claim, validated, result, output)
    executor._release_lock(claim)
    assert output.read_bytes() == executor.canonical_bytes(made)
    output.unlink()
    assert executor.recover_publication(validated, registry, output) == made


def test_child_environment_removes_ambient_injection_and_freezes_pip(tmp_path: Path,
                                                                     monkeypatch: pytest.MonkeyPatch) -> None:
    wheelhouse = tmp_path / "wheelhouse"; wheelhouse.mkdir()
    monkeypatch.setenv("PYTHONPATH", "EVIL")
    monkeypatch.setenv("PIP_INDEX_URL", "https://example.invalid")
    monkeypatch.setenv("PYTEST_ADDOPTS", "--pwn")
    environment = executor._child_environment(wheelhouse, tmp_path / "temp")
    assert environment["PIP_NO_INDEX"] == "1"
    assert environment["PIP_FIND_LINKS"] == str(wheelhouse.resolve())
    assert environment["PIP_CONFIG_FILE"] == os.devnull
    assert "PYTHONPATH" not in environment and "PYTEST_ADDOPTS" not in environment
    assert {environment[name] for name in executor.THREAD_VARIABLES} == {"1"}


def test_fake_child_success_failure_and_wall_termination(tmp_path: Path) -> None:
    success = executor._run_bounded(
        (sys.executable, "-c", "print('ok')"), cwd=tmp_path,
        environment=dict(os.environ), log_path=tmp_path / "ok.log", wall_seconds=5)
    assert success == executor.ProcessResult(0, None)
    failed = executor._run_bounded(
        (sys.executable, "-c", "raise SystemExit(7)"), cwd=tmp_path,
        environment=dict(os.environ), log_path=tmp_path / "failed.log", wall_seconds=5)
    assert failed == executor.ProcessResult(7, None)
    timed = executor._run_bounded(
        (sys.executable, "-c", "import time;time.sleep(5)"), cwd=tmp_path,
        environment=dict(os.environ), log_path=tmp_path / "timed.log", wall_seconds=1)
    assert timed.forced_reason == "COMPLETE_WAVE_WALL_LIMIT" and timed.returncode != 0


def test_commit_overlay_checks_parent_subject_and_exact_paths(tmp_path: Path) -> None:
    repository = tmp_path / "repo"; repository.mkdir()
    def git(*arguments: str) -> str:
        result = subprocess.run(["git", *arguments], cwd=repository, check=True,
                                stdout=subprocess.PIPE, text=True)
        return result.stdout.strip()
    git("init", "-q"); git("config", "user.email", "test@example.invalid"); git("config", "user.name", "Test")
    (repository / "base").write_text("base", encoding="utf-8"); git("add", "base"); git("commit", "-q", "-m", "base")
    parent = git("rev-parse", "HEAD")
    (repository / "a").write_text("a", encoding="utf-8"); (repository / "b").write_text("b", encoding="utf-8")
    git("add", "a", "b"); git("commit", "-q", "-m", "overlay")
    commit = git("rev-parse", "HEAD")
    assert executor._require_commit_overlay(
        repository, commit, parent=parent, subject="overlay", paths=("a", "b")) == git("rev-parse", "HEAD^{tree}")
    with pytest.raises(executor.FormalExecutionError, match="extent"):
        executor._require_commit_overlay(repository, commit, parent=parent,
                                         subject="overlay", paths=("a",))


def test_materialization_preserves_raw_blob_bytes_despite_tracked_crlf_attribute(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repository = tmp_path / "source"; repository.mkdir()
    def git(*arguments: str, binary: bool = False) -> bytes | str:
        result = subprocess.run(["git", *arguments], cwd=repository, check=True,
                                stdout=subprocess.PIPE,
                                text=not binary)
        return result.stdout if binary else result.stdout.strip()
    git("init", "-q")
    git("config", "user.email", "test@example.invalid")
    git("config", "user.name", "Test")
    (repository / ".gitattributes").write_bytes(b"*.md text eol=crlf\n")
    payload = b"first line\nsecond line\n"
    (repository / "proof.md").write_bytes(payload)
    git("add", ".gitattributes", "proof.md")
    git("commit", "-q", "-m", "fixture")
    commit = str(git("rev-parse", "HEAD"))
    tree = str(git("rev-parse", "HEAD^{tree}"))
    assert git("cat-file", "blob", f"{commit}:proof.md", binary=True) == payload
    monkeypatch.setattr(executor, "CANDIDATE_COMMIT", commit)
    monkeypatch.setattr(executor, "CANDIDATE_TREE", tree)
    destination = tmp_path / "materialized"
    made = executor._materialize(repository, destination)
    assert (made / "proof.md").read_bytes() == payload
    assert executor._git(made, "status", "--porcelain=v1", "--untracked-files=all") == ""


def test_frozen_gate_and_candidate_manifest_are_exact() -> None:
    raw = subprocess.check_output(
        ["git", "cat-file", "blob", f"{executor.CANDIDATE_COMMIT}:{executor.GATE_RELATIVE}"], cwd=ROOT)
    assert hashlib.sha256(raw).hexdigest().upper() == executor.GATE_SHA256
    executor._validate_gate_safeguards(raw)
    assert subprocess.check_output(
        ["git", "rev-parse", f"{executor.CANDIDATE_COMMIT}^{{tree}}"], cwd=ROOT,
        text=True).strip() == executor.CANDIDATE_TREE


def test_performance_validator_recomputes_all_nested_predicates() -> None:
    operations = ["CONSTRUCTION", "STIFFNESS", "INTERNAL_FORCE", "ASSEMBLY",
                  "SOLVE", "RECOVERY", "RESTART"]
    family = {"all_operations_pass": True, "maximum_median_ratio": "1.05",
              "operations": operations, "ratios": {key: "1.000000000000" for key in operations},
              "schema": executor.PERFORMANCE_GATE_SCHEMA}
    wheel = {"bytes": 1, "filename": "x.whl", "sha256": "A" * 64}
    value = {"all_existing_paths_pass": True,
             "base_commit": "e31c9e292a2fc9f6b57472bb8c5b90919a535492",
             "base_wheel": wheel, "candidate_commit": executor.CANDIDATE_COMMIT,
             "candidate_tree": executor.CANDIDATE_TREE, "candidate_wheel": wheel,
             "families": {"B2": family, "B3": dict(family)}, "ge_beam3_speed_gate": "NONE",
             "installed_runner_sha256": executor.GATE_SHA256,
             "order_sha256": "F80E4B923BB150F580F4774620C39E2CCF1B0AF02CCB2F462E0C06E119044B2D",
             "package_aggregate_sha256": "B" * 64, "pair_count": 11,
             "performance_diagnostics_sha256": "C" * 64,
             "process_containment": "WINDOWS_JOB_OBJECT_SUSPENDED_ASSIGN_V1",
             "raw_record_count": 22, "raw_record_graph_sha256": "D" * 64,
             "schema": executor.PERFORMANCE_GATE_SCHEMA, "warmup_count_per_role": 1}
    assert executor._validate_performance_gate(value) is True
    value["families"]["B2"] = {**family, "ratios": {**family["ratios"], "SOLVE": "1.060000000000"}}
    with pytest.raises(executor.FormalExecutionError, match="adjudication|predicate"):
        executor._validate_performance_gate(value)


def test_package_only_blocked_closeout_is_deterministic(tmp_path: Path,
                                                        monkeypatch: pytest.MonkeyPatch) -> None:
    validated = _validated(tmp_path)
    result, receipt = _blocked_pair(tmp_path, validated)
    monkeypatch.setattr(executor, "_validate_closeout_chain",
                        lambda *_args: (validated, None))
    monkeypatch.setattr(executor, "_validate_registry_provenance", lambda *_args: None)
    one = executor.synthesize_closeout(tmp_path, result, receipt, None, None,
                                       None, None, None, tmp_path / "one.json")
    two = executor.synthesize_closeout(tmp_path, result, receipt, None, None,
                                       None, None, None, tmp_path / "two.json")
    assert executor.canonical_bytes(one) == executor.canonical_bytes(two)
    assert one["terminal"] == executor.TERMINAL_BLOCKED_PROCESS
    assert one["authorities"]["performance"] is None
    assert all(value is False for key, value in one["production_boundary"].items()
               if key.endswith("authorized"))


def test_contract_and_executor_freezes_match_and_source_is_stdlib_only() -> None:
    contract_raw = CONTRACT.read_bytes()
    contract = json.loads(contract_raw)
    assert executor.canonical_bytes(contract) == contract_raw
    assert contract["schema"] == "anysolver.ge-beam3-mixed-p3-formal-contract-v2"
    assert contract["harness"]["exact_paths"] == list(executor.HARNESS_PATHS)
    assert contract["harness"]["expected_parent"] == executor.FAILED_PACKAGE_AUTHORITY_COMMIT
    assert contract["harness"]["expected_subject"] == executor.HARNESS_SUBJECT
    assert contract["harness"]["predecessor_chain"] == {
        "candidate": executor.CANDIDATE_COMMIT,
        "failed_package_authority": {
            "commit": executor.FAILED_PACKAGE_AUTHORITY_COMMIT,
            "tree": executor.FAILED_PACKAGE_AUTHORITY_TREE,
        },
        "original_harness": {
            "commit": executor.HARNESS_V1_COMMIT,
            "tree": executor.HARNESS_V1_TREE,
        },
    }
    assert contract["failed_package_incident"] == executor.PRIOR_INCIDENT
    assert contract["process"]["candidate_materialization"] \
        == "RAW_GIT_BLOBS_WITH_INDEX_NO_CHECKOUT_FILTERS"
    assert contract["execution"] == {**executor.BOUNDS,
        "formal_host": "WINDOWS_JOB_OBJECT_SUSPENDED_ASSIGN_V1",
        "package_then_performance_serial": True, "request_reuse": "FORBIDDEN",
        "retry": "FORBIDDEN", "separate_one_time_authorities": True}
    assert contract["wheelhouse_authority"] == {
        "canonical_row_fields": ["bytes", "path", "sha256"], "file_count": 10,
        "row_manifest_sha256": executor.WHEELHOUSE_SHA256,
        "total_bytes": executor.WHEELHOUSE_TOTAL_BYTES}
    imported = set()
    for node in ast.walk(ast.parse(PROGRAM.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import): imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module: imported.add(node.module.split(".")[0])
    assert imported <= set(sys.stdlib_module_names) | {"__future__"}
    source = PROGRAM.read_text(encoding="utf-8")
    assert "--create-authority" not in source and "--emit-authority" not in source
    assert "--command" not in source and "callback=" not in source
