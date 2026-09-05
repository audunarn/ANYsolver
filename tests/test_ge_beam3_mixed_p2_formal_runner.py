"""Tests for the bounded, non-authoring GE Beam3 P2 formal runner."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "docs/reference_cases/ge_beam3_mixed_p2_formal_runner.py"


def _load_runner():
    name = f"ge_beam3_mixed_p2_formal_runner_test_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(name, RUNNER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


runner = _load_runner()


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=repository,
        env={
            **{
                key: value
                for key, value in os.environ.items()
                if not key.upper().startswith("GIT_")
            },
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_TERMINAL_PROMPT": "0",
        },
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def _repository(tmp_path: Path) -> tuple[Path, str, str]:
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init", "--initial-branch=main")
    _git(repository, "config", "user.name", "P2 Runner Test")
    _git(repository, "config", "user.email", "p2-runner@example.invalid")
    _git(repository, "config", "core.autocrlf", "false")
    (repository / ".gitattributes").write_text(
        "registered.txt text eol=lf\n", encoding="utf-8", newline="\n"
    )
    (repository / "registered.txt").write_text(
        "alpha\nbeta\n", encoding="utf-8", newline="\n"
    )
    _git(repository, "add", ".gitattributes", "registered.txt")
    _git(repository, "commit", "-m", "test: registered blobs")
    commit = _git(repository, "rev-parse", "HEAD")
    tree = _git(repository, "show", "-s", "--format=%T", "HEAD")
    return repository, commit, tree


def _snapshot() -> object:
    return runner.RepositorySnapshot(
        harness_commit="A" * 40,
        harness_tree="B" * 40,
        manifest_sha256="C" * 64,
        producer_input_bindings={
            Path(path).name: {
                "bytes": index + 1,
                "sha256": format(index + 101, "064X")[-64:],
            }
            for index, path in enumerate(runner.PRODUCER_BOUND_RELATIVES)
        },
        test_bindings={
            spec.test_id: {
                "git_blob_oid": (format(index + 1, "040X"))[-40:].lower(),
                "sha256": format(index + 1, "064X")[-64:],
            }
            for index, spec in enumerate(runner.FOCUSED_TESTS)
        },
    )


def _passing_cycle() -> dict[str, object]:
    rows = [
        {
            "collected_count": index + 1,
            "finding_group": "NONE",
            "node_ids_sha256": format(index + 17, "064X")[-64:],
            "outcome": "PASS",
            "passed": True,
            "record_sha256": format(index + 31, "064X")[-64:],
            "test_id": spec.test_id,
        }
        for index, spec in enumerate(runner.FOCUSED_TESTS)
    ]
    return {
        "collected_count": sum(row["collected_count"] for row in rows),
        "failed_test_file_count": 0,
        "passed_test_file_count": len(rows),
        "scientific": {
            "checker_replica_count": 2,
            "checker_replicas_byte_identical": True,
            "checker_sha256": "8" * 64,
            "finding_groups": [],
            "outcome": "PASS",
            "passed": True,
            "proof": {
                "bytes": 1000,
                "content_sha256": "9" * 64,
                "proof_sha256": "A" * 64,
                "raw_record_count": 21,
            },
            "raw_record_count": 21,
        },
        "test_file_count": len(rows),
        "tests": rows,
    }


def _write_canonical(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(runner.canonical_bytes(value))


def _authority_checks(
    tmp_path: Path, snapshot: object
) -> tuple[tuple[Path, Path], str]:
    paths = (tmp_path / "authority-check-1.json", tmp_path / "authority-check-2.json")
    payload = runner.canonical_bytes(runner.expected_authority_check(snapshot))
    for path in paths:
        path.write_bytes(payload)
    return paths, runner._sha256(payload)


def test_frozen_scope_bounds_and_terminals_are_exact() -> None:
    assert runner.FROZEN_BOUNDS.authority_record() == {
        "child_wall_seconds": 600,
        "complete_wave_wall_seconds": 1800,
        "inactivity_seconds": 300,
        "maximum_concurrent_workers": 3,
        "memory_limit_gib_per_process_tree": 24,
        "no_automatic_retry": True,
        "numerical_library_threads_per_worker": 1,
        "required_formal_cycle_count": 2,
    }
    assert [spec.test_id for spec in runner.FOCUSED_TESTS] == [
        "PREREGISTRATION",
        "RECOVERY_CORRECTION",
        "SOLVER_CHART",
        "STATE_RESTART",
        "LOAD_MASS_RECOVERY",
        "MODAL_BUCKLING",
        "ACCEPTED_STATIC_CORE",
    ]
    assert runner.TERMINAL_PRECEDENCE == (
        "BLOCKED_GE_BEAM3_P2_BASELINE_OR_AUTHORITY",
        "BLOCKED_GE_BEAM3_P2_PROCESS_OR_EVIDENCE",
        "NO_GO_GE_BEAM3_P2_SOLVER_CHART_OR_STATE",
        "NO_GO_GE_BEAM3_P2_LOAD_MASS_OR_RECOVERY",
        "NO_GO_GE_BEAM3_P2_MODAL_OR_BUCKLING",
        "PROVISIONAL_GO_GE_BEAM3_P2_PRIVATE_PARITY",
    )
    assert runner.HARNESS_PATHS == tuple(sorted((
        "docs/reference_cases/ge_beam3_mixed_p2_formal_checker.py",
        "docs/reference_cases/ge_beam3_mixed_p2_formal_producer.py",
        "docs/reference_cases/ge_beam3_mixed_p2_formal_runner.py",
        "tests/test_ge_beam3_mixed_p2_formal_checker.py",
        "tests/test_ge_beam3_mixed_p2_formal_producer.py",
        "tests/test_ge_beam3_mixed_p2_formal_runner.py",
    )))


def test_strict_canonical_json_rejects_duplicate_nonfinite_and_noncanonical(
    tmp_path: Path,
) -> None:
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_bytes(b'{"a":1,"a":2}\n')
    with pytest.raises(runner.AuthorizationError, match="malformed"):
        runner.strict_canonical_json(duplicate)

    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_bytes(b'{"a":NaN}\n')
    with pytest.raises(runner.AuthorizationError, match="malformed"):
        runner.strict_canonical_json(nonfinite)

    spaced = tmp_path / "spaced.json"
    spaced.write_bytes(b'{"a": 1}\n')
    with pytest.raises(runner.AuthorizationError, match="canonical"):
        runner.strict_canonical_json(spaced)


def test_git_blob_hashing_uses_committed_bytes_and_dirty_tree_fails_closed(
    tmp_path: Path,
) -> None:
    repository, commit, tree = _repository(tmp_path)
    binding = runner.git_blob_binding(repository, commit, "registered.txt")
    assert binding == {
        "bytes": len(b"alpha\nbeta\n"),
        "git_blob_oid": _git(repository, "rev-parse", f"{commit}:registered.txt"),
        "path": "registered.txt",
        "sha256": runner._sha256(b"alpha\nbeta\n"),
    }
    # Checkout bytes now differ in line endings, but the authority hash remains
    # the committed blob hash.  Cleanliness is a separate mandatory gate.
    (repository / "registered.txt").write_bytes(b"alpha\r\nbeta\r\n")
    assert runner.git_blob_binding(repository, commit, "registered.txt") == binding
    with pytest.raises(runner.BaselineError, match="not clean"):
        runner._require_clean(repository)

    runner._verify_commit(repository, commit, tree)
    with pytest.raises(runner.BaselineError, match="tree mismatch"):
        runner._verify_commit(repository, commit, "0" * 40)
    with pytest.raises(runner.BaselineError, match="missing or malformed"):
        runner.git_blob_binding(repository, commit, "missing.txt")


@pytest.mark.parametrize(
    ("groups", "terminal"),
    [
        (
            ["PROCESS_OR_EVIDENCE", "BASELINE_OR_AUTHORITY", "MODAL_OR_BUCKLING"],
            "BLOCKED_GE_BEAM3_P2_BASELINE_OR_AUTHORITY",
        ),
        (
            ["PROCESS_OR_EVIDENCE", "SOLVER_CHART_OR_STATE"],
            "BLOCKED_GE_BEAM3_P2_PROCESS_OR_EVIDENCE",
        ),
        (
            ["SOLVER_CHART_OR_STATE", "LOAD_MASS_OR_RECOVERY"],
            "NO_GO_GE_BEAM3_P2_SOLVER_CHART_OR_STATE",
        ),
        (
            ["LOAD_MASS_OR_RECOVERY", "MODAL_OR_BUCKLING"],
            "NO_GO_GE_BEAM3_P2_LOAD_MASS_OR_RECOVERY",
        ),
        (["MODAL_OR_BUCKLING"], "NO_GO_GE_BEAM3_P2_MODAL_OR_BUCKLING"),
        ([], "PROVISIONAL_GO_GE_BEAM3_P2_PRIVATE_PARITY"),
    ],
)
def test_terminal_precedence(groups: list[str], terminal: str) -> None:
    records = [
        {"finding_group": group, "passed": False, "test_id": str(index)}
        for index, group in enumerate(groups)
    ]
    assert runner.adjudicate(records) == terminal


def test_formal_mode_requires_separate_exact_authorization_before_side_effects(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    snapshot = _snapshot()
    monkeypatch.setattr(runner, "validate_repository", lambda _repository: snapshot)
    authority_checks, check_sha256 = _authority_checks(tmp_path, snapshot)
    output = tmp_path / "aggregate.json"
    work = tmp_path / "work"
    with pytest.raises(runner.AuthorizationError, match="separate authorization"):
        runner.run(
            mode=runner.FORMAL_MODE,
            output_path=output,
            work_root=work,
            repository=repository,
            authority_check_paths=authority_checks,
        )
    assert not output.exists()
    assert not work.exists()

    authority = tmp_path / "authorization.json"
    wrong = runner.expected_authorization(snapshot, check_sha256)
    wrong["harness"]["manifest_sha256"] = "0" * 64
    _write_canonical(authority, wrong)
    with pytest.raises(runner.AuthorizationError, match="does not bind"):
        runner.run(
            mode=runner.FORMAL_MODE,
            output_path=output,
            work_root=work,
            authorization_path=authority,
            authority_check_paths=authority_checks,
            repository=repository,
        )
    assert not output.exists()
    assert not work.exists()


def test_authority_check_only_is_path_free_deterministic_and_replica_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    snapshot = _snapshot()
    monkeypatch.setattr(runner, "validate_repository", lambda _repository: snapshot)
    outputs = (tmp_path / "check-a.json", tmp_path / "check-b.json")
    for output in outputs:
        record = runner.write_authority_check(
            output_path=output,
            repository=repository,
        )
        assert record["terminal"] == "AUTHORITY_CHECK_ONLY_PASS"
    assert outputs[0].read_bytes() == outputs[1].read_bytes()
    raw, validated = runner.validate_authority_checks(outputs, snapshot)
    assert raw == outputs[0].read_bytes()
    assert validated == runner.expected_authority_check(snapshot)

    mutated = tmp_path / "check-mutated.json"
    changed = dict(validated)
    changed["test_file_count"] += 1
    _write_canonical(mutated, changed)
    with pytest.raises(runner.AuthorizationError, match="not byte-identical"):
        runner.validate_authority_checks((outputs[0], mutated), snapshot)
    with pytest.raises(runner.AuthorizationError, match="distinct"):
        runner.validate_authority_checks((outputs[0], outputs[0]), snapshot)


def test_two_formal_invocations_are_byte_identical_and_run_two_cycles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    snapshot = _snapshot()
    monkeypatch.setattr(runner, "validate_repository", lambda _repository: snapshot)
    authority_checks, check_sha256 = _authority_checks(tmp_path, snapshot)
    authority = tmp_path / "authorization.json"
    _write_canonical(authority, runner.expected_authorization(snapshot, check_sha256))
    calls: list[str] = []

    def fake_cycle(
        _repository: Path,
        _runner: Path,
        directory: Path,
        **_keywords: object,
    ) -> dict[str, object]:
        directory.mkdir(parents=False, exist_ok=False)
        calls.append(directory.name)
        return _passing_cycle()

    outputs: list[bytes] = []
    for index in (1, 2):
        output = tmp_path / f"aggregate-{index}.json"
        result = runner.run(
            mode=runner.FORMAL_MODE,
            output_path=output,
            work_root=tmp_path / f"work-{index}",
            authorization_path=authority,
            authority_check_paths=authority_checks,
            repository=repository,
            cycle_runner=fake_cycle,
        )
        assert result["terminal"] == "PROVISIONAL_GO_GE_BEAM3_P2_PRIVATE_PARITY"
        assert result["cycle_replica_count"] == 2
        assert result["cycle_results_byte_identical"] is True
        assert len(set(result["cycle_result_sha256"])) == 1
        outputs.append(output.read_bytes())
    assert outputs[0] == outputs[1]
    assert calls == ["cycle-1", "cycle-2", "cycle-1", "cycle-2"]


def test_no_retry_after_failed_first_formal_cycle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    snapshot = _snapshot()
    monkeypatch.setattr(runner, "validate_repository", lambda _repository: snapshot)
    authority_checks, check_sha256 = _authority_checks(tmp_path, snapshot)
    authority = tmp_path / "authorization.json"
    _write_canonical(authority, runner.expected_authorization(snapshot, check_sha256))
    calls = 0

    def failing_cycle(
        _repository: Path,
        _runner: Path,
        directory: Path,
        **_keywords: object,
    ) -> dict[str, object]:
        nonlocal calls
        calls += 1
        directory.mkdir(parents=False, exist_ok=False)
        cycle = _passing_cycle()
        row = cycle["tests"][2]
        row.update(
            {
                "finding_group": "SOLVER_CHART_OR_STATE",
                "outcome": "TEST_FAILURE",
                "passed": False,
            }
        )
        cycle["failed_test_file_count"] = 1
        cycle["passed_test_file_count"] -= 1
        return cycle

    result = runner.run(
        mode=runner.FORMAL_MODE,
        output_path=tmp_path / "aggregate.json",
        work_root=tmp_path / "work",
        authorization_path=authority,
        authority_check_paths=authority_checks,
        repository=repository,
        cycle_runner=failing_cycle,
    )
    assert calls == 1
    assert result["cycle_replica_count"] == 1
    assert result["terminal"] == "NO_GO_GE_BEAM3_P2_SOLVER_CHART_OR_STATE"


def test_bounded_process_terminates_timeout_and_reports_process_failure(
    tmp_path: Path,
) -> None:
    environment = dict(os.environ)
    for name in runner.THREAD_VARIABLES:
        environment[name] = "1"
    short = runner.ExecutionBounds(
        child_wall_seconds=0.08,
        complete_wave_wall_seconds=2.0,
        inactivity_seconds=1.0,
        memory_limit_bytes=1024**3,
        maximum_concurrent_workers=1,
        numerical_library_threads=1,
    )
    timeout_result = runner.run_bounded_process(
        (sys.executable, "-c", "import time; time.sleep(3)"),
        directory=tmp_path / "timeout-child",
        result_path=tmp_path / "timeout-child" / "missing.json",
        environment=environment,
        bounds=short,
        absolute_deadline=time.monotonic() + 2.0,
        poll_seconds=0.01,
    )
    assert timeout_result.forced_reason == "CHILD_WALL_LIMIT"
    assert timeout_result.returncode is not None

    failed_result = runner.run_bounded_process(
        (sys.executable, "-c", "raise SystemExit(7)"),
        directory=tmp_path / "failed-child",
        result_path=tmp_path / "failed-child" / "missing.json",
        environment=environment,
        bounds=short,
        absolute_deadline=time.monotonic() + 2.0,
        poll_seconds=0.01,
    )
    assert failed_result.forced_reason is None
    assert failed_result.returncode == 7


def test_worker_evidence_missing_or_malformed_is_process_failure(tmp_path: Path) -> None:
    spec = runner.FOCUSED_TESTS[0]
    process = runner.ProcessResult(forced_reason=None, returncode=0)
    missing = runner._validate_worker_record(tmp_path / "missing.json", spec, process)
    assert missing == {
        "finding_group": "PROCESS_OR_EVIDENCE",
        "outcome": "PROCESS_FAILURE",
        "passed": False,
        "reason": "WORKER_PROCESS_OR_OUTPUT_FAILURE",
        "test_id": spec.test_id,
    }
    malformed = tmp_path / "malformed.json"
    _write_canonical(malformed, {"schema": runner.WORKER_SCHEMA})
    record = runner._validate_worker_record(malformed, spec, process)
    assert record["finding_group"] == "PROCESS_OR_EVIDENCE"
    assert record["reason"] == "MALFORMED_WORKER_RECORD"


def test_raw_producer_and_two_independent_checker_replicas_pass(tmp_path: Path) -> None:
    snapshot = _snapshot()
    snapshot = runner.RepositorySnapshot(
        harness_commit=snapshot.harness_commit,
        harness_tree=snapshot.harness_tree,
        manifest_sha256=snapshot.manifest_sha256,
        producer_input_bindings={
            Path(relative).name: {
                "bytes": len(raw),
                "sha256": runner._sha256(raw),
            }
            for relative in runner.PRODUCER_BOUND_RELATIVES
            for raw in [(ROOT / relative).read_bytes()]
        },
        test_bindings=snapshot.test_bindings,
    )
    cycle = tmp_path / "scientific-cycle"
    cycle.mkdir()
    result = runner._run_scientific_lane(
        ROOT,
        cycle,
        snapshot,
        bounds=runner.FROZEN_BOUNDS,
        absolute_deadline=time.monotonic() + 600.0,
    )
    assert result["outcome"] == "PASS"
    assert result["passed"] is True
    assert result["checker_replica_count"] == 2
    assert result["checker_replicas_byte_identical"] is True
    assert result["finding_groups"] == []
    assert result["raw_record_count"] == 21
    assert result["proof"]["raw_record_count"] == 21
    assert len(result["proof"]["proof_sha256"]) == 64
    assert len(result["checker_sha256"]) == 64


def test_focused_modules_run_once_each_in_isolated_children(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    scientific = _passing_cycle()["scientific"]
    monkeypatch.setattr(
        runner,
        "_run_scientific_lane",
        lambda *_arguments, **_keywords: scientific,
    )
    cycle = runner.run_cycle(
        ROOT,
        RUNNER,
        tmp_path / "focused-cycle",
        snapshot=_snapshot(),
        bounds=runner.FROZEN_BOUNDS,
        absolute_deadline=time.monotonic() + 600.0,
    )
    assert cycle["test_file_count"] == 7
    assert cycle["passed_test_file_count"] == 7
    assert cycle["failed_test_file_count"] == 0
    assert cycle["collected_count"] > 0
    assert [record["test_id"] for record in cycle["tests"]] == [
        spec.test_id for spec in runner.FOCUSED_TESTS
    ]
    assert all(record["passed"] for record in cycle["tests"])
    assert len({record["record_sha256"] for record in cycle["tests"]}) == 7
    for spec in runner.FOCUSED_TESTS:
        directory = tmp_path / "focused-cycle" / spec.test_id.lower()
        assert (directory / "stdout.log").is_file()
        assert (directory / "stderr.log").is_file()


def test_aggregate_contains_no_paths_timings_or_measurements() -> None:
    snapshot = _snapshot()
    cycle = runner._decorate_cycle(_passing_cycle(), snapshot)
    aggregate = runner._aggregate(
        mode=runner.FORMAL_MODE,
        snapshot=snapshot,
        cycle=cycle,
        cycle_hashes=[runner._sha256(runner.canonical_bytes(cycle))] * 2,
        cycles_byte_identical=True,
        authority_check_sha256="E" * 64,
        authorization_sha256="D" * 64,
    )

    forbidden_keys = {
        "path",
        "cwd",
        "command",
        "duration",
        "elapsed",
        "timing",
        "rss",
        "pid",
        "stdout",
        "stderr",
    }

    def inspect(value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                assert key.lower() not in forbidden_keys
                inspect(item)
        elif isinstance(value, list):
            for item in value:
                inspect(item)
        elif isinstance(value, float):
            pytest.fail("canonical aggregate contains a floating measurement")
        elif isinstance(value, str):
            assert "\\" not in value and "/" not in value

    inspect(aggregate)
    raw = runner.canonical_bytes(aggregate)
    assert json.loads(raw) == aggregate


def test_child_environment_forces_one_numerical_thread(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    environment = runner._child_environment(repository, tmp_path)
    assert {environment[name] for name in runner.THREAD_VARIABLES} == {"1"}
    assert environment["PYTHONHASHSEED"] == "0"
    assert environment["PYTHONDONTWRITEBYTECODE"] == "1"
    assert environment["PYTHONNOUSERSITE"] == "1"


def test_exclusive_outputs_and_nonfrozen_bounds_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    monkeypatch.setattr(runner, "validate_repository", lambda _repository: _snapshot())
    output = tmp_path / "aggregate.json"
    output.write_bytes(b"occupied")
    with pytest.raises(runner.ExclusiveOutputError, match="fresh"):
        runner.run(
            mode=runner.REHEARSAL_MODE,
            output_path=output,
            work_root=tmp_path / "work",
            repository=repository,
        )
    output.unlink()
    changed = runner.ExecutionBounds(child_wall_seconds=599.0)
    with pytest.raises(runner.AuthorizationError, match="frozen"):
        runner.run(
            mode=runner.REHEARSAL_MODE,
            output_path=output,
            work_root=tmp_path / "work",
            repository=repository,
            bounds=changed,
        )


def test_runner_does_not_author_or_expose_public_integration() -> None:
    source = RUNNER.read_text(encoding="utf-8")
    assert "--emit-authority" not in source
    assert "--create-authority" not in source
    assert "src/anysolver/__init__.py" not in runner.HARNESS_PATHS
    assert "src/anysolver/elements.py" not in runner.HARNESS_PATHS
    assert "PROVISIONAL_GO_GE_BEAM3_P2_PRIVATE_PARITY" in source
    assert "PROVISIONAL_GO_GE_BEAM3_STRAIGHT_STANDALONE_OPT_IN" not in source
