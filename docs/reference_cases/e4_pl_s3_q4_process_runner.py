"""Execute preregistered S3/Q4 burn-in commands and emit canonical manifests."""

from __future__ import annotations

import sys


if __name__ == "__main__" and not sys.flags.isolated:
    raise RuntimeError("process runner must be launched with Python isolated mode (-I)")

import argparse
import datetime as dt
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Any, Mapping


_RUNNER_PATH = Path(__file__).resolve(strict=True)
_FROZEN_ROOT = Path(r"C:\Github\ANYsolver\.perf2-worktrees\s3-e4-pl-final-freeze")
ROOT = _FROZEN_ROOT if __name__ == "__main__" else _RUNNER_PATH.parents[2]
_VALIDATOR_PATH = ROOT / "docs" / "reference_cases" / "e4_pl_s3_q4_burnin.py"
burnin: Any = None
PROCESS_RESULT_SCHEMA = "anysolver.e4-pl-s3-q4-process-result-v1"
_VALIDATOR_BYTES = 72670
_VALIDATOR_SHA256 = "eaabb99792220953af9bc0646c611886dab1bc7458226984761545dfcef9868d"


def _load_source_module(path: Path, *, expected_bytes: int, expected_sha256: str) -> Any:
    import hashlib
    import types

    if path.is_symlink():
        raise RuntimeError("canonical evidence validator may not be a symlink")
    raw = path.read_bytes()
    if len(raw) != expected_bytes or hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise RuntimeError("canonical evidence validator source identity mismatch")
    module = types.ModuleType("_e4_pl_s3_q4_burnin_authority")
    module.__file__ = str(path)
    module.__package__ = ""
    exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
    return module


def _bootstrap_authority() -> None:
    global ROOT, _VALIDATOR_PATH, burnin
    expected_runner = (
        _FROZEN_ROOT / "docs" / "reference_cases" / "e4_pl_s3_q4_process_runner.py"
    )
    if not sys.flags.isolated:
        raise RuntimeError("process coordinator is not running in Python isolated mode")
    if _RUNNER_PATH != expected_runner:
        raise RuntimeError("process runner is outside the literal frozen authority path")
    if expected_runner.resolve(strict=True) != expected_runner:
        raise RuntimeError("literal process runner authority path is noncanonical")
    ROOT = _FROZEN_ROOT
    _VALIDATOR_PATH = (
        ROOT / "docs" / "reference_cases" / "e4_pl_s3_q4_burnin.py"
    ).resolve(strict=True)
    module = _load_source_module(
        _VALIDATOR_PATH,
        expected_bytes=_VALIDATOR_BYTES,
        expected_sha256=_VALIDATOR_SHA256,
    )
    if (
        Path(module.__file__).resolve(strict=True) != _VALIDATOR_PATH
        or module.PROCESS_RESULT_SCHEMA != PROCESS_RESULT_SCHEMA
    ):
        raise RuntimeError("process runner loaded a noncanonical evidence validator")
    burnin = module


RESOURCE_ORDER = [
    (cycle, lane)
    for cycle in (1, 2)
    for lane in ("functional", "anyfem", "performance")
]


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _execution_environment(
    contract: Mapping[str, Any], *, process_prefix: str
) -> dict[str, str]:
    python = burnin.execution_tool_path(contract, "python")
    git = burnin.execution_tool_path(contract, "git")
    burnin.execution_tool_path(contract, "powershell")
    if python != Path(sys.executable).resolve(strict=True):
        raise burnin.EvidenceError("process Python executable differs from frozen authority")
    environment = burnin.sanitized_execution_environment(contract)
    pycache, numba_cache = burnin.execution_cache_paths(contract, process_prefix)
    if pycache.exists() or numba_cache.exists():
        raise burnin.EvidenceError("one-shot external execution cache already exists")
    for name, root in (
        ("Python", pycache.parent),
        ("Numba", numba_cache.parent),
    ):
        if root.exists() and (not root.is_dir() or root.is_symlink()):
            raise burnin.EvidenceError(f"{name} cache root is not a canonical directory")
    environment["PYTHONPYCACHEPREFIX"] = str(pycache)
    environment["NUMBA_CACHE_DIR"] = str(numba_cache)
    current_path = environment.get("PATH", "")
    environment["PATH"] = os.pathsep.join(
        (str(python.parent), str(git.parent), current_path)
    )
    return environment


def _verify_local_runner_inputs(contract: Mapping[str, Any]) -> None:
    if contract["execution"].get("coordinator_isolated_mode") is not True:
        raise burnin.EvidenceError("Python isolated mode is not frozen for the coordinator")
    if not sys.flags.isolated:
        raise burnin.EvidenceError("process coordinator is not running in Python isolated mode")
    expected = {
        "evidence_validator": _VALIDATOR_PATH,
        "process_runner": _RUNNER_PATH,
    }
    for name, path in expected.items():
        record = burnin._exact_keys(
            contract["runner_inputs"][name],
            {"bytes", "path", "sha256"},
            f"$contract.runner_inputs.{name}",
        )
        if record["path"] != path.relative_to(ROOT).as_posix():
            raise burnin.EvidenceError(f"{name} canonical path mismatch")
        if path.is_symlink() or burnin.file_hash_record(path) != {
            "bytes": record["bytes"],
            "sha256": record["sha256"],
        }:
            raise burnin.EvidenceError(f"{name} identity mismatch")


def _write_exclusive(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(payload)
    except FileExistsError as exc:
        raise burnin.EvidenceError(f"refusing to replace process artifact: {path}") from exc


def _reserve_output(path: Path) -> None:
    expected_parent = burnin.output_root(burnin.load_contract())
    if path.parent != expected_parent or path.name not in set(
        burnin.PROCESS_DIRECTORY_NAMES.values()
    ):
        raise burnin.EvidenceError(f"output directory is outside frozen authority: {path}")
    try:
        path.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise burnin.EvidenceError(f"frozen one-shot output already exists: {path}") from exc
    if path.resolve(strict=True) != path:
        raise burnin.EvidenceError(f"output directory is not canonical: {path}")


def _authority_commit(candidate: Path, contract: Mapping[str, Any]) -> tuple[str, str]:
    candidate = candidate.resolve(strict=True)
    burnin.assert_clean_execution_repository(candidate, contract=contract)
    head = burnin._git(candidate, "rev-parse", "HEAD", contract=contract)
    tree = burnin._git(candidate, "rev-parse", "HEAD^{tree}", contract=contract)
    authority = contract["authority_commit"]
    introductions = burnin._git(
        candidate,
        "log",
        "--format=%H",
        "--diff-filter=A",
        "--",
        "docs/reference_cases/e4_pl_s3_q4_burnin_contract.json",
        contract=contract,
    ).splitlines()
    if introductions != [head]:
        raise burnin.EvidenceError("candidate is not the unique authority commit")
    metadata = burnin._git(
        candidate, "show", "-s", "--format=%P%n%s", head, contract=contract
    ).splitlines()
    if metadata != [authority["exact_parent"], authority["subject"]]:
        raise burnin.EvidenceError("authority parent or subject mismatch")
    paths = burnin._git(
        candidate,
        "diff",
        "--name-only",
        authority["exact_parent"],
        head,
        contract=contract,
    ).splitlines()
    if paths != authority["exact_paths"]:
        raise burnin.EvidenceError("authority changed-path extent mismatch")
    return head, tree


def _verify_repositories(
    contract: Mapping[str, Any],
) -> tuple[Path, dict[str, Path], str, str]:
    _verify_local_runner_inputs(contract)
    repositories = burnin.external_repository_paths(contract)
    candidate = repositories["ANYsolver"]
    siblings = {name: repositories[name] for name in contract["sibling_authority"]}
    if ROOT.resolve(strict=True) != candidate.resolve(strict=True):
        raise burnin.EvidenceError("process runner is not executing from the frozen candidate")
    for name, path in repositories.items():
        if path.resolve(strict=True) != path:
            raise burnin.EvidenceError(f"{name} path is not the exact frozen repository")
    head, tree = _authority_commit(candidate, contract)
    if set(siblings) != set(contract["sibling_authority"]):
        raise burnin.EvidenceError("sibling repository bindings are incomplete")
    for name, authority in contract["sibling_authority"].items():
        path = siblings[name].resolve(strict=True)
        burnin.assert_clean_execution_repository(path, contract=contract)
        if burnin._git(path, "rev-parse", "HEAD", contract=contract) != authority["commit"]:
            raise burnin.EvidenceError(f"{name} commit mismatch")
        if burnin._git(path, "rev-parse", "HEAD^{tree}", contract=contract) != authority["tree"]:
            raise burnin.EvidenceError(f"{name} tree mismatch")
    return candidate, siblings, head, tree


def _run(
    command: str, *, contract: Mapping[str, Any], cwd: Path, process_prefix: str
) -> tuple[subprocess.CompletedProcess[bytes], str, str, float, str]:
    started_at = _now()
    started = time.perf_counter()
    execution_state = "EXECUTED"
    try:
        powershell = burnin.execution_tool_path(contract, "powershell")
        completed = subprocess.run(
            [str(powershell), "-NoProfile", "-Command", command],
            cwd=cwd,
            env=_execution_environment(contract, process_prefix=process_prefix),
            check=False,
            capture_output=True,
        )
    except (OSError, burnin.EvidenceError) as exc:
        execution_state = "NOT_STARTED"
        completed = subprocess.CompletedProcess(
            args=["powershell", "-NoProfile", "-Command", command],
            returncode=250,
            stdout=b"",
            stderr=f"process start failed: {exc}\n".encode("utf-8", errors="replace"),
        )
    elapsed = time.perf_counter() - started
    ended_at = _now()
    return completed, started_at, ended_at, elapsed, execution_state


def _process_manifest(
    *,
    candidate_commit: str,
    candidate_tree: str,
    command: str,
    completed: subprocess.CompletedProcess[bytes],
    elapsed_seconds: float,
    ended_at: str,
    execution_state: str,
    request_id: str | None,
    request_sha256: str | None,
    resource_lock_released: bool | None,
    started_at: str,
) -> dict[str, Any]:
    producer_sha256 = burnin.file_hash_record(_RUNNER_PATH)["sha256"]
    return {
        "candidate_commit": candidate_commit,
        "candidate_tree": candidate_tree,
        "command_sha256": burnin.sha256_bytes(command.encode("utf-8")),
        "elapsed_seconds": elapsed_seconds,
        "ended_at": ended_at,
        "execution_state": execution_state,
        "exit_code": completed.returncode,
        "producer_sha256": producer_sha256,
        "request_id": request_id,
        "request_sha256": request_sha256,
        "resource_lock_released": resource_lock_released,
        "schema": PROCESS_RESULT_SCHEMA,
        "started_at": started_at,
        "stderr": {
            "bytes": len(completed.stderr),
            "sha256": burnin.sha256_bytes(completed.stderr),
        },
        "stdout": {
            "bytes": len(completed.stdout),
            "sha256": burnin.sha256_bytes(completed.stdout),
        },
    }


def _write_process(
    output_dir: Path,
    *,
    manifest: Mapping[str, Any],
    stderr: bytes,
    stdout: bytes,
) -> tuple[Path, Path, Path]:
    if not output_dir.is_dir() or output_dir.is_symlink():
        raise burnin.EvidenceError(f"process output was not exclusively reserved: {output_dir}")
    stdout_path = output_dir / "stdout.txt"
    stderr_path = output_dir / "stderr.txt"
    result_path = output_dir / "result.json"
    _write_exclusive(stdout_path, stdout)
    _write_exclusive(stderr_path, stderr)
    _write_exclusive(result_path, burnin.canonical_json_bytes(dict(manifest)))
    return result_path, stdout_path, stderr_path


def _load_process_manifest(
    contract: Mapping[str, Any], prefix: str, *, required: bool
) -> dict[str, Any] | None:
    directory = burnin.process_output_directory(contract, prefix)
    result_path = directory / "result.json"
    if not result_path.exists():
        if required:
            state = "reserved but nonterminal" if directory.exists() else "absent"
            raise burnin.EvidenceError(f"required predecessor {prefix} is {state}")
        return None
    raw = result_path.read_bytes()
    manifest = burnin.strict_json_loads(raw)
    if raw != burnin.canonical_json_bytes(manifest):
        raise burnin.EvidenceError(f"process manifest is not canonical: {prefix}")
    is_resource = prefix.startswith("cycle_")
    request_row: dict[str, Any] | None = None
    if is_resource:
        match = re.fullmatch(r"cycle_(1|2)\.(functional|anyfem|performance)", prefix)
        if match is None:
            raise burnin.EvidenceError(f"invalid resource prefix: {prefix}")
        cycle, lane = int(match.group(1)), match.group(2)
        request_row = next(
            row
            for row in contract["resource_requests"][f"cycle_{cycle}"]
            if row["lane"] == lane
        )
        expected_command = request_row["command_sha256"]
        expected_request_id = request_row["request_id"]
    else:
        if prefix == "common.quick.1":
            command_row = contract["non_resource_commands"]["quick"]
        elif prefix == "common.package.1":
            command_row = contract["non_resource_commands"]["package"]
        else:
            partition = int(prefix.rsplit(".", 1)[1])
            command_row = contract["non_resource_commands"]["additive"][partition - 1]
        expected_command = command_row["command_sha256"]
        expected_request_id = None
    candidate = burnin.external_repository_paths(contract)["ANYsolver"]
    candidate_record = {
        "commit": burnin._git(candidate, "rev-parse", "HEAD", contract=contract),
        "tree": burnin._git(candidate, "rev-parse", "HEAD^{tree}", contract=contract),
    }
    status = (
        "PASS"
        if manifest.get("exit_code") == 0
        and manifest.get("execution_state") == "EXECUTED"
        and manifest.get("resource_lock_released") == (True if is_resource else None)
        else "FAIL"
    )
    process = {
        key: manifest[key]
        for key in (
            "command_sha256",
            "elapsed_seconds",
            "ended_at",
            "execution_state",
            "exit_code",
            "producer_sha256",
            "request_id",
            "resource_lock_released",
            "started_at",
            "stderr",
            "stdout",
        )
    }
    process.update(
        {
            "result": burnin.file_hash_record(result_path),
            "status": status,
        }
    )
    burnin._validate_process(
        process,
        f"$process.{prefix}",
        expected_request_id=expected_request_id,
        expected_command_sha256=expected_command,
        expected_producer_sha256=burnin.contract_producer_sha256(contract),
    )
    for name in ("stdout", "stderr"):
        path = directory / f"{name}.txt"
        if path.is_symlink() or burnin.file_hash_record(path) != manifest[name]:
            raise burnin.EvidenceError(f"process {name} identity mismatch: {prefix}")
    burnin._validate_process_result_artifact(
        result_path,
        candidate=candidate_record,
        process=process,
        request=request_row,
    )
    return manifest


def _manifest_passed(manifest: Mapping[str, Any]) -> bool:
    return (
        manifest.get("exit_code") == 0
        and manifest.get("execution_state") == "EXECUTED"
        and manifest.get("resource_lock_released") in {None, True}
    )


def _require_passed(contract: Mapping[str, Any], prefix: str) -> dict[str, Any]:
    manifest = _load_process_manifest(contract, prefix, required=True)
    assert manifest is not None
    if not _manifest_passed(manifest):
        raise burnin.EvidenceError(f"required predecessor did not pass: {prefix}")
    return manifest


def _assert_absent(contract: Mapping[str, Any], prefixes: list[str]) -> None:
    for prefix in prefixes:
        if burnin.process_output_directory(contract, prefix).exists():
            raise burnin.EvidenceError(f"frozen one-shot output already exists: {prefix}")


def _local_prefix(lane: str, partition: int | None) -> str:
    if lane == "additive":
        if partition not in {1, 2, 3}:
            raise burnin.EvidenceError("additive execution requires partition 1, 2, or 3")
        return f"common.additive.{partition}"
    if lane not in {"quick", "package"} or partition is not None:
        raise burnin.EvidenceError("invalid local lane/partition selection")
    return f"common.{lane}.1"


def _verify_local_order(
    contract: Mapping[str, Any], lane: str, partition: int | None
) -> str:
    prefix = _local_prefix(lane, partition)
    resource_prefixes = [f"cycle_{cycle}.{name}" for cycle, name in RESOURCE_ORDER]
    if lane == "quick":
        if burnin.output_root(contract).exists():
            raise burnin.EvidenceError("frozen output root already exists before quick")
    elif lane == "package":
        _require_passed(contract, "common.quick.1")
        _assert_absent(
            contract,
            [prefix, "common.additive.1", "common.additive.2", "common.additive.3", *resource_prefixes],
        )
        for filename in (
            contract["package"]["result_filename"],
            contract["package"]["wheel_filename"],
        ):
            if (burnin.output_root(contract) / filename).exists():
                raise burnin.EvidenceError("canonical package output already exists")
    else:
        _require_passed(contract, "common.quick.1")
        _require_passed(contract, "common.package.1")
        _assert_absent(contract, [prefix, *resource_prefixes])
        assert partition is not None
        if (burnin.output_root(contract) / f"pytest-additive-{partition}").exists():
            raise burnin.EvidenceError("additive pytest output already exists")
    if (burnin.output_root(contract) / contract["adjudication"]["external_result_filename"]).exists():
        raise burnin.EvidenceError("aggregate already exists; no further execution is allowed")
    return prefix


def _resource_position(
    contract: Mapping[str, Any], request_id: str
) -> tuple[int, str, int]:
    for index, (cycle, lane) in enumerate(RESOURCE_ORDER):
        row = next(
            candidate
            for candidate in contract["resource_requests"][f"cycle_{cycle}"]
            if candidate["lane"] == lane
        )
        if row["request_id"] == request_id:
            return cycle, lane, index
    raise burnin.EvidenceError(f"request is not preregistered: {request_id}")


def _verify_resource_order(
    contract: Mapping[str, Any], request_id: str
) -> tuple[str, int, str]:
    for prefix in (
        "common.quick.1",
        "common.package.1",
        "common.additive.1",
        "common.additive.2",
        "common.additive.3",
    ):
        _require_passed(contract, prefix)
    cycle, lane, index = _resource_position(contract, request_id)
    ordered_prefixes = [f"cycle_{c}.{name}" for c, name in RESOURCE_ORDER]
    for prefix in ordered_prefixes[:index]:
        manifest = _require_passed(contract, prefix)
        _require_resource_terminal(contract, prefix, manifest)
    _assert_absent(contract, ordered_prefixes[index:])
    if (burnin.output_root(contract) / contract["adjudication"]["external_result_filename"]).exists():
        raise burnin.EvidenceError("aggregate already exists; no further execution is allowed")
    return lane, cycle, ordered_prefixes[index]


def run_local(
    *,
    lane: str,
    partition: int | None,
) -> int:
    _bootstrap_authority()
    contract = burnin.load_contract()
    candidate, _siblings, candidate_commit, candidate_tree = _verify_repositories(contract)
    prefix = _verify_local_order(contract, lane, partition)
    output_dir = burnin.process_output_directory(contract, prefix)
    commands = contract["non_resource_commands"]
    if lane == "additive":
        assert partition is not None
        row = commands["additive"][partition - 1]
    else:
        row = commands[lane]
    command = row["command"]
    if burnin.sha256_bytes(command.encode("utf-8")) != row["command_sha256"]:
        raise burnin.EvidenceError("local command authority mismatch")
    _execution_environment(contract, process_prefix=prefix)
    _reserve_output(output_dir)
    completed, started_at, ended_at, elapsed, execution_state = _run(
        command, contract=contract, cwd=candidate, process_prefix=prefix
    )
    try:
        _candidate, _siblings, post_commit, post_tree = _verify_repositories(contract)
        if (post_commit, post_tree) != (candidate_commit, candidate_tree):
            raise burnin.EvidenceError("candidate identity changed during execution")
    except burnin.EvidenceError as exc:
        completed = subprocess.CompletedProcess(
            args=completed.args,
            returncode=251,
            stdout=completed.stdout,
            stderr=completed.stderr + f"\npost-execution authority failure: {exc}\n".encode(),
        )
    manifest = _process_manifest(
        candidate_commit=candidate_commit,
        candidate_tree=candidate_tree,
        command=command,
        completed=completed,
        elapsed_seconds=elapsed,
        ended_at=ended_at,
        execution_state=execution_state,
        request_id=None,
        request_sha256=None,
        resource_lock_released=None,
        started_at=started_at,
    )
    _write_process(
        output_dir,
        manifest=manifest,
        stderr=completed.stderr,
        stdout=completed.stdout,
    )
    sys.stdout.buffer.write(burnin.canonical_json_bytes(manifest))
    sys.stdout.buffer.flush()
    return completed.returncode


def _request_row(contract: Mapping[str, Any], request_id: str) -> dict[str, Any]:
    matches = [
        row
        for cycle in ("cycle_1", "cycle_2")
        for row in contract["resource_requests"][cycle]
        if row["request_id"] == request_id
    ]
    if len(matches) != 1:
        raise burnin.EvidenceError(f"request is not uniquely preregistered: {request_id}")
    return matches[0]


def _manager_paths(contract: Mapping[str, Any]) -> dict[str, Path]:
    authority = burnin.resource_manager_authority(contract)
    root = Path(authority["root"])
    if root.resolve(strict=True) != root or not root.is_dir():
        raise burnin.EvidenceError("resource-manager root identity mismatch")
    result = {
        "root": root,
        "ledger": root / authority["ledger"],
        "requests": root / authority["requests"],
        "active_lock": root / authority["active_lock"],
    }
    for key in ("acquire", "release"):
        record = authority[key]
        path = root / record["filename"]
        if path.is_symlink() or burnin.file_hash_record(path) != {
            "bytes": record["bytes"],
            "sha256": record["sha256"],
        }:
            raise burnin.EvidenceError(f"resource-manager {key} identity mismatch")
        result[key] = path
    if (
        result["ledger"].is_symlink()
        or not result["ledger"].is_file()
        or result["requests"].is_symlink()
        or not result["requests"].is_dir()
    ):
        raise burnin.EvidenceError("resource-manager ledger/request authority mismatch")
    return result


def _request_payload(
    contract: Mapping[str, Any], request_id: str
) -> tuple[dict[str, Any], dict[str, Any], Path]:
    row = _request_row(contract, request_id)
    manager = _manager_paths(contract)
    request_path = manager["requests"] / f"{request_id}.json"
    if request_path.name != f"{request_id}.json" or request_path.is_symlink():
        raise burnin.EvidenceError("resource request path mismatch")
    if burnin.file_hash_record(request_path) != {
        "bytes": row["bytes"],
        "sha256": row["request_sha256"],
    }:
        raise burnin.EvidenceError("resource request identity mismatch")
    request = burnin.strict_json_load(request_path)
    if request.get("request_id") != request_id or request.get("status") != "PENDING":
        raise burnin.EvidenceError("resource request payload identity mismatch")
    command = request.get("command")
    if not isinstance(command, str) or burnin.sha256_bytes(command.encode("utf-8")) != row[
        "command_sha256"
    ]:
        raise burnin.EvidenceError("resource request command mismatch")
    return row, request, request_path


def _ledger_rows(ledger: str, request_id: str, status: str) -> list[str]:
    return re.findall(
        rf"^\|[^\n]*\|\s*{request_id}\s*\|\s*{status}\s*\|[^\n]*$",
        ledger,
        flags=re.MULTILINE,
    )


def _append_terminal_ledger(
    ledger_path: Path,
    *,
    manifest_path: Path,
    request: Mapping[str, Any],
) -> None:
    manifest = burnin.strict_json_load(manifest_path)
    result = burnin.file_hash_record(manifest_path)
    process = dict(manifest)
    process["status"] = (
        "PASS"
        if process["exit_code"] == 0
        and process["execution_state"] == "EXECUTED"
        and process["resource_lock_released"] is True
        else "FAIL"
    )
    fields = burnin.terminal_ledger_fields(request, process, result)
    row = f"| {_now()} | {' | '.join(str(field) for field in fields)} |\n"
    with ledger_path.open("a", encoding="utf-8", newline="") as stream:
        stream.write(row)


def _require_resource_terminal(
    contract: Mapping[str, Any],
    prefix: str,
    manifest: Mapping[str, Any],
    *,
    expected_status: str = "PASS",
) -> dt.datetime:
    request_id = manifest["request_id"]
    row, request, _path = _request_payload(contract, request_id)
    manager = _manager_paths(contract)
    ledger = manager["ledger"].read_text(encoding="utf-8")
    ledger_status = "COMPLETED_PASS" if expected_status == "PASS" else "COMPLETED_FAIL"
    entries = burnin._ledger_entries(ledger, request_id, ledger_status)
    process = dict(manifest)
    process["status"] = expected_status
    result_record = burnin.file_hash_record(
        burnin.process_output_directory(contract, prefix) / "result.json"
    )
    expected = burnin.terminal_ledger_fields(request, process, result_record)
    if len(entries) != 1 or entries[0][1:] != expected:
        raise burnin.EvidenceError(f"predecessor terminal ledger mismatch: {request_id}")
    ended = dt.datetime.fromisoformat(manifest["ended_at"].replace("Z", "+00:00"))
    terminal = dt.datetime.fromisoformat(entries[0][0].replace("Z", "+00:00"))
    if terminal < ended:
        raise burnin.EvidenceError(f"predecessor terminal precedes completion: {request_id}")
    if row["request_id"] != request_id:
        raise burnin.EvidenceError("predecessor request authority mismatch")
    return terminal


def approve_requests() -> None:
    _bootstrap_authority()
    contract = burnin.load_contract()
    burnin.validate_resource_approval_authority(contract)
    _candidate, _siblings, candidate_commit, candidate_tree = _verify_repositories(contract)
    for prefix in (
        "common.quick.1",
        "common.package.1",
        "common.additive.1",
        "common.additive.2",
        "common.additive.3",
    ):
        _require_passed(contract, prefix)
    _assert_absent(
        contract, [f"cycle_{cycle}.{lane}" for cycle, lane in RESOURCE_ORDER]
    )
    manager = _manager_paths(contract)
    if manager["active_lock"].exists():
        raise burnin.EvidenceError("global resource slot is occupied")
    ledger = manager["ledger"].read_text(encoding="utf-8")
    candidate_record = {"commit": candidate_commit, "tree": candidate_tree}
    rows: list[str] = []
    timestamp = _now()
    for cycle, lane in RESOURCE_ORDER:
        row = next(
            item
            for item in contract["resource_requests"][f"cycle_{cycle}"]
            if item["lane"] == lane
        )
        _authority, request, _path = _request_payload(contract, row["request_id"])
        if any(
            _ledger_rows(ledger, row["request_id"], status)
            for status in (
                "APPROVED",
                "COMPLETED_PASS",
                "COMPLETED_FAIL",
                "CANCELLED_NOT_RUN",
            )
        ):
            raise burnin.EvidenceError(f"request already appears in ledger: {row['request_id']}")
        fields = burnin.approval_ledger_fields(request, row, candidate_record)
        rows.append(f"| {timestamp} | {' | '.join(str(field) for field in fields)} |\n")
    with manager["ledger"].open("a", encoding="utf-8", newline="") as stream:
        stream.write("".join(rows))


def _lock_owner(manager: Mapping[str, Path], request: Mapping[str, Any]) -> None:
    owner_path = manager["active_lock"] / "owner.json"
    if not owner_path.is_file() or owner_path.is_symlink():
        raise burnin.EvidenceError("resource lock owner record is missing")
    owner = burnin.strict_json_loads(owner_path.read_text(encoding="utf-8-sig"))
    burnin._exact_keys(
        owner,
        {"acquired_at", "command", "process_id", "repository", "request_id", "task"},
        "$resource_lock.owner",
    )
    for key in ("command", "repository", "request_id", "task"):
        if owner[key] != request[key]:
            raise burnin.EvidenceError(f"resource lock owner {key} mismatch")
    burnin._require_timestamp(owner["acquired_at"], "$resource_lock.owner.acquired_at")
    if not isinstance(owner["process_id"], int) or isinstance(owner["process_id"], bool):
        raise burnin.EvidenceError("resource lock owner process ID is invalid")


def run_resource(*, request_id: str) -> int:
    _bootstrap_authority()
    contract = burnin.load_contract()
    candidate, _siblings, candidate_commit, candidate_tree = _verify_repositories(contract)
    lane, _cycle, prefix = _verify_resource_order(contract, request_id)
    row, request, _request_path = _request_payload(contract, request_id)
    repositories = burnin.external_repository_paths(contract)
    execution_repository = repositories["ANYfem" if lane == "anyfem" else "ANYsolver"]
    if Path(request["repository"]) != execution_repository:
        raise burnin.EvidenceError("resource execution repository is not the frozen binding")
    manager = _manager_paths(contract)
    ledger = manager["ledger"].read_text(encoding="utf-8")
    expected_approval = burnin.approval_ledger_fields(
        request, row, {"commit": candidate_commit, "tree": candidate_tree}
    )
    approvals = burnin._ledger_entries(ledger, request_id, "APPROVED")
    if len(approvals) != 1 or approvals[0][1:] != expected_approval:
        raise burnin.EvidenceError("resource request lacks its exact approval")
    if any(
        _ledger_rows(ledger, request_id, terminal)
        for terminal in ("COMPLETED_PASS", "COMPLETED_FAIL", "CANCELLED_NOT_RUN")
    ):
        raise burnin.EvidenceError("resource request already has a terminal ledger row")
    if manager["active_lock"].exists():
        raise burnin.EvidenceError("global resource slot is occupied")
    execution_environment = _execution_environment(contract, process_prefix=prefix)
    powershell = burnin.execution_tool_path(contract, "powershell")
    output_dir = burnin.process_output_directory(contract, prefix)
    _reserve_output(output_dir)
    started_at = _now()
    started = time.perf_counter()
    command = request["command"]
    completed = subprocess.CompletedProcess(
        args=[str(powershell), "-NoProfile", "-Command", command],
        returncode=252,
        stdout=b"",
        stderr=b"resource command was not started\n",
    )
    execution_state = "NOT_STARTED"
    acquired_lock = False
    lock_released = False
    try:
        acquired = subprocess.run(
            [
                str(powershell),
                "-NoProfile",
                "-File",
                str(manager["acquire"]),
                "-RequestId",
                request_id,
            ],
            capture_output=True,
            check=False,
            env=execution_environment,
        )
        if acquired.returncode:
            completed = subprocess.CompletedProcess(
                args=completed.args,
                returncode=252,
                stdout=acquired.stdout,
                stderr=b"resource acquisition failed\n" + acquired.stderr,
            )
        else:
            acquired_lock = True
            _lock_owner(manager, request)
            completed, _command_start, _command_end, _command_elapsed, execution_state = _run(
                command,
                contract=contract,
                cwd=execution_repository,
                process_prefix=prefix,
            )
            try:
                _candidate, _bound_siblings, post_commit, post_tree = _verify_repositories(contract)
                if (post_commit, post_tree) != (candidate_commit, candidate_tree):
                    raise burnin.EvidenceError("candidate identity changed during resource execution")
            except burnin.EvidenceError as exc:
                completed = subprocess.CompletedProcess(
                    args=completed.args,
                    returncode=253,
                    stdout=completed.stdout,
                    stderr=completed.stderr
                    + f"\npost-execution authority failure: {exc}\n".encode(),
                )
    except (burnin.EvidenceError, OSError) as exc:
        completed = subprocess.CompletedProcess(
            args=completed.args,
            returncode=254,
            stdout=completed.stdout,
            stderr=completed.stderr + f"\nresource authority failure: {exc}\n".encode(),
        )
    finally:
        if acquired_lock:
            try:
                released = subprocess.run(
                    [
                        str(powershell),
                        "-NoProfile",
                        "-File",
                        str(manager["release"]),
                        "-RequestId",
                        request_id,
                    ],
                    capture_output=True,
                    check=False,
                    env=execution_environment,
                )
            except OSError as exc:
                released = subprocess.CompletedProcess(
                    args=[str(powershell), "-NoProfile", "-File", str(manager["release"])],
                    returncode=255,
                    stdout=b"",
                    stderr=f"resource lock release could not start: {exc}\n".encode(),
                )
            lock_released = released.returncode == 0 and not manager["active_lock"].exists()
            if not lock_released:
                completed = subprocess.CompletedProcess(
                    args=completed.args,
                    returncode=255,
                    stdout=completed.stdout,
                    stderr=completed.stderr + b"\nresource lock release failed\n" + released.stderr,
                )
    ended_at = _now()
    elapsed = time.perf_counter() - started
    manifest = _process_manifest(
        candidate_commit=candidate_commit,
        candidate_tree=candidate_tree,
        command=command,
        completed=completed,
        elapsed_seconds=elapsed,
        ended_at=ended_at,
        execution_state=execution_state,
        request_id=request_id,
        request_sha256=row["request_sha256"],
        resource_lock_released=lock_released,
        started_at=started_at,
    )
    result_path, _stdout_path, _stderr_path = _write_process(
        output_dir,
        manifest=manifest,
        stderr=completed.stderr,
        stdout=completed.stdout,
    )
    _append_terminal_ledger(
        manager["ledger"], manifest_path=result_path, request=request
    )
    sys.stdout.buffer.write(burnin.canonical_json_bytes(manifest))
    sys.stdout.buffer.flush()
    return completed.returncode if lock_released else 255


def cancel_remaining() -> None:
    _bootstrap_authority()
    contract = burnin.load_contract()
    _candidate, _siblings, candidate_commit, candidate_tree = _verify_repositories(contract)
    manager = _manager_paths(contract)
    if manager["active_lock"].exists():
        raise burnin.EvidenceError("cannot cancel while the global slot is occupied")
    failure_index: int | None = None
    failure_terminal: dt.datetime | None = None
    for index, (cycle, lane) in enumerate(RESOURCE_ORDER):
        prefix = f"cycle_{cycle}.{lane}"
        manifest = _load_process_manifest(contract, prefix, required=False)
        if manifest is None:
            break
        if not _manifest_passed(manifest):
            failure_index = index
            failure_terminal = _require_resource_terminal(
                contract, prefix, manifest, expected_status="FAIL"
            )
            break
        _require_resource_terminal(contract, prefix, manifest)
    if failure_index is None:
        raise burnin.EvidenceError("no failed resource process authorizes cancellation")
    ledger = manager["ledger"].read_text(encoding="utf-8")
    rows: list[str] = []
    timestamp = _now()
    cancellation_time = dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    assert failure_terminal is not None
    if cancellation_time < failure_terminal:
        raise burnin.EvidenceError("cancellation precedes failed-request terminal")
    for cycle, lane in RESOURCE_ORDER[failure_index + 1 :]:
        row = next(
            item
            for item in contract["resource_requests"][f"cycle_{cycle}"]
            if item["lane"] == lane
        )
        authority, request, _path = _request_payload(contract, row["request_id"])
        approvals = burnin._ledger_entries(ledger, row["request_id"], "APPROVED")
        expected_approval = burnin.approval_ledger_fields(
            request,
            authority,
            {"commit": candidate_commit, "tree": candidate_tree},
        )
        if len(approvals) != 1 or approvals[0][1:] != expected_approval:
            raise burnin.EvidenceError("only approved later requests may be cancelled")
        if any(
            _ledger_rows(ledger, row["request_id"], state)
            for state in ("COMPLETED_PASS", "COMPLETED_FAIL", "CANCELLED_NOT_RUN")
        ):
            raise burnin.EvidenceError("later request already has a terminal row")
        if burnin.process_output_directory(contract, f"cycle_{cycle}.{lane}").exists():
            raise burnin.EvidenceError("a request with process output cannot be cancelled")
        process = {"request_id": row["request_id"], "status": "NOT_RUN"}
        fields = burnin.terminal_ledger_fields(request, process, None)
        rows.append(f"| {timestamp} | {' | '.join(str(field) for field in fields)} |\n")
    with manager["ledger"].open("a", encoding="utf-8", newline="") as stream:
        stream.write("".join(rows))


def _process_record(contract: Mapping[str, Any], prefix: str) -> dict[str, Any]:
    manifest = _load_process_manifest(contract, prefix, required=True)
    assert manifest is not None
    directory = burnin.process_output_directory(contract, prefix)
    status = "PASS" if _manifest_passed(manifest) else "FAIL"
    return {
        "command_sha256": manifest["command_sha256"],
        "elapsed_seconds": manifest["elapsed_seconds"],
        "ended_at": manifest["ended_at"],
        "execution_state": manifest["execution_state"],
        "exit_code": manifest["exit_code"],
        "producer_sha256": manifest["producer_sha256"],
        "request_id": manifest["request_id"],
        "resource_lock_released": manifest["resource_lock_released"],
        "result": burnin.file_hash_record(directory / "result.json"),
        "started_at": manifest["started_at"],
        "status": status,
        "stderr": burnin.file_hash_record(directory / "stderr.txt"),
        "stdout": burnin.file_hash_record(directory / "stdout.txt"),
    }


def aggregate_result() -> dict[str, Any]:
    _bootstrap_authority()
    contract = burnin.load_contract()
    _candidate, _siblings, candidate_commit, candidate_tree = _verify_repositories(contract)
    not_run_local = {"request_id": None, "status": "NOT_RUN"}
    quick_processes = [_process_record(contract, "common.quick.1")]
    if quick_processes[0]["status"] == "PASS":
        package_processes = [_process_record(contract, "common.package.1")]
    else:
        package_processes = [dict(not_run_local)]
    if package_processes[0]["status"] == "PASS":
        additive_processes = [
            _process_record(contract, f"common.additive.{partition}")
            for partition in (1, 2, 3)
        ]
    else:
        additive_processes = [dict(not_run_local) for _partition in (1, 2, 3)]
    common_processes = {
        "quick": quick_processes,
        "package": package_processes,
        "additive": additive_processes,
    }
    common_statuses = {
        lane: (
            "PASS"
            if all(process["status"] == "PASS" for process in processes)
            else "NOT_RUN"
            if all(process["status"] == "NOT_RUN" for process in processes)
            else "FAIL"
        )
        for lane, processes in common_processes.items()
    }
    cycles: list[dict[str, Any]] = []
    encountered_failure = any(
        common_statuses[lane] != "PASS" for lane in ("quick", "package", "additive")
    )
    for cycle in (1, 2):
        lanes: dict[str, Any] = {}
        for lane in ("functional", "anyfem", "performance"):
            row = next(
                item
                for item in contract["resource_requests"][f"cycle_{cycle}"]
                if item["lane"] == lane
            )
            prefix = f"cycle_{cycle}.{lane}"
            if encountered_failure:
                lanes[lane] = {"request_id": row["request_id"], "status": "NOT_RUN"}
                continue
            manifest = _load_process_manifest(contract, prefix, required=True)
            assert manifest is not None
            process = _process_record(contract, prefix)
            lanes[lane] = process
            encountered_failure = process["status"] == "FAIL"
        statuses = [lanes[lane]["status"] for lane in ("functional", "anyfem", "performance")]
        cycle_status = (
            "PASS"
            if statuses == ["PASS", "PASS", "PASS"]
            else "NOT_RUN"
            if statuses == ["NOT_RUN", "NOT_RUN", "NOT_RUN"]
            else "FAIL"
        )
        cycles.append({"cycle": cycle, "lanes": lanes, "status": cycle_status})
    performance_passed = all(
        cycle["lanes"]["performance"]["status"] == "PASS" for cycle in cycles
    )
    performance_observations = (
        [
            {
                "cycle": cycle,
                "observation": burnin.extract_performance_observation(
                    burnin.process_output_directory(contract, f"cycle_{cycle}.performance")
                    / "stdout.txt",
                    contract=contract,
                ),
            }
            for cycle in (1, 2)
        ]
        if performance_passed
        else None
    )
    package_result = burnin.output_root(contract) / contract["package"]["result_filename"]
    wheel = burnin.output_root(contract) / contract["package"]["wheel_filename"]
    package_status = common_statuses["package"]

    package_artifacts = (
        None
        if package_status == "NOT_RUN"
        else {
            "result": burnin.optional_regular_file_record(package_result),
            "wheel": burnin.optional_regular_file_record(wheel, filename=True),
        }
    )
    all_resource_passed = all(cycle["status"] == "PASS" for cycle in cycles)
    all_common_passed = all(
        status == "PASS" for status in common_statuses.values()
    )
    success = all_common_passed and all_resource_passed and performance_passed
    result = {
        "candidate": {"clean": True, "commit": candidate_commit, "tree": candidate_tree},
        "common_lanes": {
            lane: {
                "inventory": contract["lane_inventories"][lane],
                "processes": processes,
                "status": common_statuses[lane],
            }
            for lane, processes in common_processes.items()
        },
        "cycles": cycles,
        "hard_gates": {
            "batch_path_equality": "PASS" if performance_passed else "NOT_EVALUATED",
            "q4_numerical_parity": "PASS" if performance_passed else "NOT_EVALUATED",
            "qualified_s3_opt_in": (
                "PASS" if common_statuses["additive"] == "PASS" else "NOT_EVALUATED"
            ),
            "s3_default_legacy": (
                "PASS" if common_statuses["additive"] == "PASS" else "NOT_EVALUATED"
            ),
            "warm_cache_reuse": "PASS" if performance_passed else "NOT_EVALUATED",
        },
        "ledger": None,
        "package_artifacts": package_artifacts,
        "performance_observations": performance_observations,
        "production_boundary": contract["production_boundary"],
        "resource_requests": contract["resource_requests"],
        "schema": burnin.RESULT_SCHEMA,
        "siblings": contract["sibling_authority"],
        "terminal": contract["adjudication"][
            "result_success_terminal" if success else "result_blocked_terminal"
        ],
    }
    manager = _manager_paths(contract)
    snapshot_name = contract["adjudication"]["ledger_snapshot_filename"]
    if Path(snapshot_name).name != snapshot_name:
        raise burnin.EvidenceError("resource ledger snapshot authority is malformed")
    ledger_snapshot = burnin.output_root(contract) / snapshot_name
    _write_exclusive(ledger_snapshot, manager["ledger"].read_bytes())
    result["ledger"] = burnin.file_hash_record(ledger_snapshot)
    burnin.validate_external_bindings(result, contract=contract, require_aggregate=False)
    output = burnin.output_root(contract) / contract["adjudication"]["external_result_filename"]
    _write_exclusive(output, burnin.canonical_json_bytes(result))
    burnin.validate_external_bindings(result, contract=contract, require_aggregate=True)
    return result


def main(argv: list[str] | None = None) -> int:
    _bootstrap_authority()
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    local = subparsers.add_parser("local")
    local.add_argument("--lane", choices=("quick", "package", "additive"), required=True)
    local.add_argument("--partition", type=int)
    resource = subparsers.add_parser("resource")
    resource.add_argument("--request-id", required=True)
    subparsers.add_parser("approve")
    subparsers.add_parser("cancel-remaining")
    subparsers.add_parser("aggregate")
    args = parser.parse_args(argv)
    if args.mode == "local":
        return run_local(
            lane=args.lane,
            partition=args.partition,
        )
    if args.mode == "resource":
        return run_resource(request_id=args.request_id)
    if args.mode == "approve":
        approve_requests()
        return 0
    if args.mode == "cancel-remaining":
        cancel_remaining()
        return 0
    result = aggregate_result()
    sys.stdout.buffer.write(burnin.canonical_json_bytes(result))
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
