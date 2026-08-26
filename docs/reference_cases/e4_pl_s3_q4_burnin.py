"""Strict evidence validation for the corrected S3/Q4 burn-in cycles."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import statistics
import subprocess
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path(__file__).with_name("e4_pl_s3_q4_burnin_contract.json")
RESULT_SCHEMA = "anysolver.e4-pl-s3-q4-burn-in-result-v1"
PROCESS_RESULT_SCHEMA = "anysolver.e4-pl-s3-q4-process-result-v1"
PERFORMANCE_BASELINE_MARKER = b"Q1M_PERFORMANCE_BASELINE_JSON="
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
GIT_OBJECT_RE = re.compile(r"[0-9a-f]{40}\Z")
REQUEST_ID_RE = re.compile(r"[0-9a-f]{32}\Z")
PROCESS_DIRECTORY_NAMES = {
    "common.quick.1": "quick",
    "common.package.1": "package",
    "common.additive.1": "additive-1",
    "common.additive.2": "additive-2",
    "common.additive.3": "additive-3",
    "cycle_1.functional": "cycle-1-functional",
    "cycle_1.anyfem": "cycle-1-anyfem",
    "cycle_1.performance": "cycle-1-performance",
    "cycle_2.functional": "cycle-2-functional",
    "cycle_2.anyfem": "cycle-2-anyfem",
    "cycle_2.performance": "cycle-2-performance",
}


class EvidenceError(ValueError):
    """Raised when burn-in authority or evidence is malformed."""


def _reject_constant(value: str) -> None:
    raise EvidenceError(f"non-finite JSON number is forbidden: {value}")


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(value: Any, location: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise EvidenceError(f"non-finite value at {location}")
    if isinstance(value, dict):
        for key, child in value.items():
            _reject_nonfinite(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_nonfinite(child, f"{location}[{index}]")


def strict_json_loads(raw: str | bytes) -> Any:
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise EvidenceError("JSON must be UTF-8") from exc
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"invalid JSON: {exc.msg}") from exc
    _reject_nonfinite(value)
    return value


def strict_json_load(path: Path) -> Any:
    if not path.is_file() or path.is_symlink():
        raise EvidenceError(f"JSON input must be a regular non-symlink file: {path}")
    return strict_json_loads(path.read_bytes())


def canonical_json_bytes(value: Any) -> bytes:
    _reject_nonfinite(value)
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def file_hash_record(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": sha256_bytes(raw)}


def optional_regular_file_record(
    path: Path, *, filename: bool = False
) -> dict[str, Any] | None:
    """Return an exact record for an optional canonical, non-symlink file."""

    if path.is_symlink():
        raise EvidenceError(f"canonical artifact may not be a symlink: {path}")
    if not path.exists():
        return None
    if not path.is_file():
        raise EvidenceError(f"canonical artifact must be a regular file: {path}")
    record = file_hash_record(path)
    return {**record, "filename": path.name} if filename else record


def _require_int(value: Any, location: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise EvidenceError(f"{location} must be an integer >= {minimum}")
    return value


def _exact_keys(value: Any, expected: Iterable[str], location: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceError(f"{location} must be an object")
    expected_set = set(expected)
    if set(value) != expected_set:
        raise EvidenceError(
            f"{location} keys mismatch: expected {sorted(expected_set)}, got {sorted(value)}"
        )
    return value


def _require_string(value: Any, location: str) -> str:
    if not isinstance(value, str) or not value:
        raise EvidenceError(f"{location} must be a nonempty string")
    return value


def _require_hash(value: Any, location: str) -> str:
    text = _require_string(value, location)
    if not SHA256_RE.fullmatch(text):
        raise EvidenceError(f"{location} must be a lowercase SHA-256")
    return text


def _validate_hash_record(
    value: Any,
    location: str,
    *,
    filename: bool = False,
) -> dict[str, Any]:
    keys = {"bytes", "sha256"}
    if filename:
        keys.add("filename")
    record = _exact_keys(value, keys, location)
    if not isinstance(record["bytes"], int) or isinstance(record["bytes"], bool):
        raise EvidenceError(f"{location}.bytes must be an integer")
    if record["bytes"] < 0:
        raise EvidenceError(f"{location}.bytes must be nonnegative")
    _require_hash(record["sha256"], f"{location}.sha256")
    if filename:
        name = _require_string(record["filename"], f"{location}.filename")
        if Path(name).name != name:
            raise EvidenceError(f"{location}.filename must be a basename")
    return record


def _require_timestamp(value: Any, location: str) -> str:
    text = _require_string(value, location)
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceError(f"{location} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise EvidenceError(f"{location} must include a UTC offset")
    return text


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    raw = path.read_bytes()
    contract = strict_json_loads(raw)
    if raw != canonical_json_bytes(contract):
        raise EvidenceError("burn-in contract is not canonical JSON")
    _exact_keys(
        contract,
        {
            "adjudication",
            "authority_commit",
            "candidate_chain",
            "execution",
            "external_authority",
            "hard_gate_authority",
            "historical_inputs",
            "lane_inventories",
            "non_resource_commands",
            "package",
            "production_boundary",
            "resource_requests",
            "runner_inputs",
            "schema",
            "sibling_authority",
            "study_id",
        },
        "$contract",
    )
    if contract["schema"] != "anysolver.e4-pl-s3-q4-burn-in-contract-v1":
        raise EvidenceError("burn-in contract schema mismatch")
    return contract


def execution_tool_path(contract: Mapping[str, Any], name: str) -> Path:
    if name not in {"git", "powershell", "python"}:
        raise EvidenceError(f"unknown frozen execution tool: {name}")
    guard = _exact_keys(
        contract["execution"]["environment_guard"],
        {
            "fixed",
            "git",
            "numba_cache_root",
            "powershell",
            "python",
            "python_cache_root",
            "removed",
            "removed_prefixes",
        },
        "$contract.execution.environment_guard",
    )
    record = _exact_keys(
        guard[name],
        {"bytes", "path", "sha256"},
        f"$contract.execution.environment_guard.{name}",
    )
    _require_int(record["bytes"], f"$contract.execution.environment_guard.{name}.bytes")
    _require_hash(record["sha256"], f"$contract.execution.environment_guard.{name}.sha256")
    path = Path(
        _require_string(record["path"], f"$contract.execution.environment_guard.{name}.path")
    )
    if not path.is_absolute():
        raise EvidenceError(f"frozen {name} path must be absolute")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise EvidenceError(f"frozen {name} executable is unavailable") from exc
    if resolved != path or path.is_symlink() or file_hash_record(path) != {
        "bytes": record["bytes"],
        "sha256": record["sha256"],
    }:
        raise EvidenceError(f"frozen {name} executable identity mismatch")
    return path


def sanitized_execution_environment(contract: Mapping[str, Any]) -> dict[str, str]:
    guard = _exact_keys(
        contract["execution"]["environment_guard"],
        {
            "fixed",
            "git",
            "numba_cache_root",
            "powershell",
            "python",
            "python_cache_root",
            "removed",
            "removed_prefixes",
        },
        "$contract.execution.environment_guard",
    )
    removed = guard["removed"]
    prefixes = guard["removed_prefixes"]
    fixed = guard["fixed"]
    if (
        not isinstance(removed, list)
        or len(set(removed)) != len(removed)
        or not all(isinstance(name, str) and name for name in removed)
        or not isinstance(prefixes, list)
        or len(set(prefixes)) != len(prefixes)
        or not all(isinstance(prefix, str) and prefix for prefix in prefixes)
        or not isinstance(fixed, dict)
        or not all(
            isinstance(name, str)
            and name
            and isinstance(value, str)
            for name, value in fixed.items()
        )
    ):
        raise EvidenceError("execution environment guard is malformed")
    environment = dict(os.environ)
    for name in list(environment):
        if name in removed or any(name.startswith(prefix) for prefix in prefixes):
            environment.pop(name, None)
    environment.update(fixed)
    return environment


def execution_cache_paths(
    contract: Mapping[str, Any], process_prefix: str
) -> tuple[Path, Path]:
    try:
        process_name = PROCESS_DIRECTORY_NAMES[process_prefix]
    except KeyError as exc:
        raise EvidenceError(f"unknown frozen process prefix: {process_prefix}") from exc
    guard = contract["execution"]["environment_guard"]
    pycache_root = Path(
        _require_string(
            guard["python_cache_root"],
            "$contract.execution.environment_guard.python_cache_root",
        )
    )
    numba_root = Path(
        _require_string(
            guard["numba_cache_root"],
            "$contract.execution.environment_guard.numba_cache_root",
        )
    )
    if not pycache_root.is_absolute() or not numba_root.is_absolute():
        raise EvidenceError("execution cache paths must be absolute")
    return pycache_root / process_name, numba_root / process_name


def external_repository_paths(contract: Mapping[str, Any]) -> dict[str, Path]:
    external = _exact_keys(
        contract["external_authority"],
        {"repositories", "resource_manager"},
        "$contract.external_authority",
    )
    repositories = _exact_keys(
        external["repositories"],
        {"ANYsolver", *contract["sibling_authority"]},
        "$contract.external_authority.repositories",
    )
    result: dict[str, Path] = {}
    for name, raw_path in repositories.items():
        path = Path(_require_string(raw_path, f"$contract.external_authority.repositories.{name}"))
        if not path.is_absolute():
            raise EvidenceError(f"repository authority must be absolute: {name}")
        result[name] = path
    return result


def resource_manager_authority(contract: Mapping[str, Any]) -> dict[str, Any]:
    manager = _exact_keys(
        contract["external_authority"]["resource_manager"],
        {"acquire", "active_lock", "ledger", "release", "requests", "root"},
        "$contract.external_authority.resource_manager",
    )
    root = Path(_require_string(manager["root"], "$contract.external_authority.resource_manager.root"))
    if not root.is_absolute():
        raise EvidenceError("resource-manager root authority must be absolute")
    for key in ("active_lock", "ledger", "requests"):
        value = _require_string(
            manager[key], f"$contract.external_authority.resource_manager.{key}"
        )
        if Path(value).name != value:
            raise EvidenceError(f"resource-manager {key} must be a basename")
    for key in ("acquire", "release"):
        _validate_hash_record(
            manager[key],
            f"$contract.external_authority.resource_manager.{key}",
            filename=True,
        )
    return manager


def output_root(contract: Mapping[str, Any]) -> Path:
    root = Path(
        _require_string(
            contract["non_resource_commands"]["output_root"],
            "$contract.non_resource_commands.output_root",
        )
    )
    if not root.is_absolute():
        raise EvidenceError("burn-in output root must be absolute")
    return root


def process_output_directory(contract: Mapping[str, Any], prefix: str) -> Path:
    try:
        name = PROCESS_DIRECTORY_NAMES[prefix]
    except KeyError as exc:
        raise EvidenceError(f"unknown frozen process prefix: {prefix}") from exc
    return output_root(contract) / name


def _validate_process(
    value: Any,
    location: str,
    *,
    expected_request_id: str | None,
    expected_command_sha256: str | None,
    expected_producer_sha256: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvidenceError(f"{location} must be an object")
    status = value.get("status")
    if status == "NOT_RUN":
        process = _exact_keys(value, {"request_id", "status"}, location)
        if process["request_id"] != expected_request_id:
            raise EvidenceError(f"{location}.request_id mismatch")
        return process
    process = _exact_keys(
        value,
        {
            "command_sha256",
            "elapsed_seconds",
            "ended_at",
            "execution_state",
            "exit_code",
            "producer_sha256",
            "request_id",
            "resource_lock_released",
            "result",
            "started_at",
            "status",
            "stderr",
            "stdout",
        },
        location,
    )
    if status not in {"PASS", "FAIL"}:
        raise EvidenceError(f"{location}.status is invalid")
    if process["request_id"] != expected_request_id:
        raise EvidenceError(f"{location}.request_id mismatch")
    lock_released = process["resource_lock_released"]
    if expected_request_id is None:
        if lock_released is not None:
            raise EvidenceError(f"{location}.resource_lock_released must be null")
    elif not isinstance(lock_released, bool):
        raise EvidenceError(f"{location}.resource_lock_released must be boolean")
    if process["execution_state"] not in {"EXECUTED", "NOT_STARTED"}:
        raise EvidenceError(f"{location}.execution_state is invalid")
    command_sha256 = _require_hash(
        process["command_sha256"], f"{location}.command_sha256"
    )
    if expected_command_sha256 is not None and command_sha256 != expected_command_sha256:
        raise EvidenceError(f"{location}.command_sha256 mismatch")
    producer_sha256 = _require_hash(
        process["producer_sha256"], f"{location}.producer_sha256"
    )
    if producer_sha256 != expected_producer_sha256:
        raise EvidenceError(f"{location}.producer_sha256 mismatch")
    if (
        not isinstance(process["exit_code"], int)
        or isinstance(process["exit_code"], bool)
    ):
        raise EvidenceError(f"{location}.exit_code must be an integer")
    if (status == "PASS") != (
        process["exit_code"] == 0
        and process["execution_state"] == "EXECUTED"
        and (expected_request_id is None or lock_released is True)
    ):
        raise EvidenceError(f"{location} status/exit-code mismatch")
    elapsed = process["elapsed_seconds"]
    if (
        not isinstance(elapsed, (int, float))
        or isinstance(elapsed, bool)
        or elapsed < 0.0
    ):
        raise EvidenceError(f"{location}.elapsed_seconds is invalid")
    started = _require_timestamp(process["started_at"], f"{location}.started_at")
    ended = _require_timestamp(process["ended_at"], f"{location}.ended_at")
    if dt.datetime.fromisoformat(ended.replace("Z", "+00:00")) < dt.datetime.fromisoformat(
        started.replace("Z", "+00:00")
    ):
        raise EvidenceError(f"{location} ends before it starts")
    for key in ("result", "stderr", "stdout"):
        _validate_hash_record(process[key], f"{location}.{key}")
    return process


def _lane_status(processes: list[dict[str, Any]]) -> str:
    statuses = [process["status"] for process in processes]
    if statuses and all(status == "PASS" for status in statuses):
        return "PASS"
    if statuses and all(status == "NOT_RUN" for status in statuses):
        return "NOT_RUN"
    return "FAIL"


def _process_interval(process: Mapping[str, Any]) -> tuple[dt.datetime, dt.datetime] | None:
    if process["status"] == "NOT_RUN":
        return None
    return (
        dt.datetime.fromisoformat(process["started_at"].replace("Z", "+00:00")),
        dt.datetime.fromisoformat(process["ended_at"].replace("Z", "+00:00")),
    )


def _require_barrier(
    before: Iterable[Mapping[str, Any]],
    after: Iterable[Mapping[str, Any]],
    label: str,
) -> None:
    before_intervals = [
        interval
        for process in before
        if (interval := _process_interval(process)) is not None
    ]
    after_intervals = [
        interval
        for process in after
        if (interval := _process_interval(process)) is not None
    ]
    if before_intervals and after_intervals:
        if max(interval[1] for interval in before_intervals) > min(
            interval[0] for interval in after_intervals
        ):
            raise EvidenceError(f"execution chronology violates {label}")


def _validate_common_lane(
    value: Any,
    location: str,
    *,
    expected_command_sha256: list[str],
    expected_inventory: Mapping[str, Any],
    expected_producer_sha256: str,
    process_count: int,
) -> list[dict[str, Any]]:
    lane = _exact_keys(value, {"inventory", "processes", "status"}, location)
    if lane["inventory"] != dict(expected_inventory):
        raise EvidenceError(f"{location}.inventory mismatch")
    if not isinstance(lane["processes"], list) or len(lane["processes"]) != process_count:
        raise EvidenceError(f"{location}.processes count mismatch")
    if len(expected_command_sha256) != process_count:
        raise EvidenceError(f"{location} command authority count mismatch")
    processes = [
        _validate_process(
            process,
            f"{location}.processes[{index}]",
            expected_request_id=None,
            expected_command_sha256=expected_command_sha256[index],
            expected_producer_sha256=expected_producer_sha256,
        )
        for index, process in enumerate(lane["processes"])
    ]
    if lane["status"] != _lane_status(processes):
        raise EvidenceError(f"{location}.status does not match its processes")
    return processes


def _request_table(contract: Mapping[str, Any]) -> dict[tuple[int, str], dict[str, Any]]:
    result: dict[tuple[int, str], dict[str, Any]] = {}
    identifiers: set[str] = set()
    for cycle in (1, 2):
        rows = contract["resource_requests"][f"cycle_{cycle}"]
        if [row.get("lane") for row in rows] != ["functional", "anyfem", "performance"]:
            raise EvidenceError(f"cycle {cycle} request lane ordering mismatch")
        for row in rows:
            _exact_keys(
                row,
                {"bytes", "command_sha256", "lane", "request_id", "request_sha256"},
                f"$contract.resource_requests.cycle_{cycle}",
            )
            request_id = _require_string(row["request_id"], "request_id")
            if not REQUEST_ID_RE.fullmatch(request_id) or request_id in identifiers:
                raise EvidenceError("resource request IDs must be unique lowercase IDs")
            identifiers.add(request_id)
            _require_hash(row["command_sha256"], "command_sha256")
            _require_hash(row["request_sha256"], "request_sha256")
            if not isinstance(row["bytes"], int) or row["bytes"] <= 0:
                raise EvidenceError("request bytes must be a positive integer")
            result[(cycle, row["lane"])] = row
    return result


def validate_resource_approval_authority(
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    authority = _exact_keys(
        contract["execution"]["resource_approval_authority"],
        {"delegation", "request_ids", "source", "user_statement"},
        "$contract.execution.resource_approval_authority",
    )
    if authority["source"] != "EXPLICIT_USER_APPROVAL_IN_THIS_CODEX_TASK":
        raise EvidenceError("resource approval source is not the frozen user authority")
    if authority["delegation"] != (
        "COORDINATOR_MAY_APPEND_APPROVED_ROWS_FOR_THE_EXACT_BOUND_REQUEST_IDS_"
        "AFTER_COMMON_PREFLIGHT"
    ):
        raise EvidenceError("resource approval delegation is malformed")
    if authority["user_statement"] != (
        "I approve. Also for future requests required to finish the job."
    ):
        raise EvidenceError("resource approval statement differs from the frozen authority")
    expected_ids = [
        row["request_id"]
        for cycle in ("cycle_1", "cycle_2")
        for row in contract["resource_requests"][cycle]
    ]
    if authority["request_ids"] != expected_ids:
        raise EvidenceError("resource approval IDs differ from the bound requests")
    return authority


def _non_resource_command_table(contract: Mapping[str, Any]) -> dict[str, list[str]]:
    authority = _exact_keys(
        contract["non_resource_commands"],
        {"additive", "output_root", "package", "quick"},
        "$contract.non_resource_commands",
    )
    _require_string(authority["output_root"], "$contract.non_resource_commands.output_root")
    result: dict[str, list[str]] = {}
    for lane in ("quick", "package"):
        row = _exact_keys(
            authority[lane],
            {"command", "command_sha256"},
            f"$contract.non_resource_commands.{lane}",
        )
        command = _require_string(row["command"], f"$contract.non_resource_commands.{lane}.command")
        expected_hash = _require_hash(
            row["command_sha256"],
            f"$contract.non_resource_commands.{lane}.command_sha256",
        )
        if sha256_bytes(command.encode("utf-8")) != expected_hash:
            raise EvidenceError(f"{lane} command hash mismatch")
        result[lane] = [expected_hash]
    additive = authority["additive"]
    if not isinstance(additive, list) or len(additive) != 3:
        raise EvidenceError("additive command authority must contain three partitions")
    additive_hashes: list[str] = []
    additive_count = 0
    additive_paths: list[list[str]] = []
    for expected_partition, row_value in enumerate(additive, start=1):
        row = _exact_keys(
            row_value,
            {"command", "command_sha256", "count", "inventory_sha256", "partition"},
            f"$contract.non_resource_commands.additive[{expected_partition - 1}]",
        )
        if row["partition"] != expected_partition:
            raise EvidenceError("additive partition ordering mismatch")
        if not isinstance(row["count"], int) or isinstance(row["count"], bool) or row["count"] <= 0:
            raise EvidenceError("additive partition count is invalid")
        additive_count += row["count"]
        inventory_sha256 = _require_hash(
            row["inventory_sha256"], "additive inventory SHA-256"
        )
        command = _require_string(row["command"], "additive command")
        command_hash = _require_hash(row["command_sha256"], "additive command SHA-256")
        if sha256_bytes(command.encode("utf-8")) != command_hash:
            raise EvidenceError("additive command hash mismatch")
        marker = "python -m pytest -q "
        suffix = f" --basetemp='{authority['output_root']}\\pytest-additive-{expected_partition}'"
        if command.count(marker) != 1 or not command.endswith(suffix):
            raise EvidenceError("additive command route mismatch")
        paths = command.split(marker, 1)[1][: -len(suffix)].split()
        if len(paths) != row["count"] or any(
            not path.startswith("tests/") or not path.endswith(".py") for path in paths
        ):
            raise EvidenceError("additive command path coverage mismatch")
        if sha256_bytes(canonical_json_bytes(paths)) != inventory_sha256:
            raise EvidenceError("additive command inventory hash mismatch")
        additive_paths.append(paths)
        additive_hashes.append(command_hash)
    if additive_count != contract["lane_inventories"]["additive"]["count"]:
        raise EvidenceError("additive partition coverage count mismatch")
    interleaved = [
        paths[index]
        for index in range(max(len(paths) for paths in additive_paths))
        for paths in additive_paths
        if index < len(paths)
    ]
    if sha256_bytes(canonical_json_bytes(interleaved)) != contract["lane_inventories"][
        "additive"
    ]["sha256"]:
        raise EvidenceError("additive partitions do not reconstruct the frozen inventory")
    result["additive"] = additive_hashes
    return result


def validate_performance_observation(
    value: Any,
    *,
    contract: Mapping[str, Any],
    location: str,
) -> dict[str, Any]:
    observation = _exact_keys(
        value,
        {"hard_gates", "performance_baseline", "schema"},
        location,
    )
    authority = _exact_keys(
        contract["hard_gate_authority"],
        {"performance", "s3"},
        "$contract.hard_gate_authority",
    )["performance"]
    authority = _exact_keys(
        authority,
        {
            "baseline_schema",
            "evidence_nodes",
            "measurement_names",
            "observation_schema",
            "repetitions",
            "speed_claim",
            "warmups",
        },
        "$contract.hard_gate_authority.performance",
    )
    if observation["schema"] != authority["observation_schema"]:
        raise EvidenceError(f"{location}.schema mismatch")
    gates = _exact_keys(
        observation["hard_gates"],
        set(authority["evidence_nodes"]),
        f"{location}.hard_gates",
    )
    for name, nodes in authority["evidence_nodes"].items():
        gate = _exact_keys(
            gates[name],
            {"evidence_nodes", "observed", "status"},
            f"{location}.hard_gates.{name}",
        )
        if gate != {"evidence_nodes": nodes, "observed": True, "status": "PASS"}:
            raise EvidenceError(f"{location}.hard_gates.{name} is not an exact pass")
    baseline = _exact_keys(
        observation["performance_baseline"],
        {"measurements", "repetitions", "schema", "speed_claim", "warmups"},
        f"{location}.performance_baseline",
    )
    for key in ("repetitions", "schema", "speed_claim", "warmups"):
        expected_key = "baseline_schema" if key == "schema" else key
        if baseline[key] != authority[expected_key]:
            raise EvidenceError(f"{location}.performance_baseline.{key} mismatch")
    repetitions = _require_int(
        baseline["repetitions"], f"{location}.performance_baseline.repetitions", minimum=1
    )
    measurements = _exact_keys(
        baseline["measurements"],
        set(authority["measurement_names"]),
        f"{location}.performance_baseline.measurements",
    )
    for name, summary_value in measurements.items():
        summary = _exact_keys(
            summary_value,
            {"mad_ns", "median_ns", "p95_ns", "samples_ns"},
            f"{location}.performance_baseline.measurements.{name}",
        )
        samples = summary["samples_ns"]
        if not isinstance(samples, list) or len(samples) != repetitions:
            raise EvidenceError(f"{location} timing sample count mismatch")
        for index, sample in enumerate(samples):
            _require_int(sample, f"{location}.{name}.samples_ns[{index}]")
        ordered = sorted(samples)
        median_ns = int(statistics.median(ordered))
        mad_ns = int(statistics.median(abs(sample - median_ns) for sample in ordered))
        p95_ns = int(ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)])
        if {
            "median_ns": summary["median_ns"],
            "mad_ns": summary["mad_ns"],
            "p95_ns": summary["p95_ns"],
        } != {"median_ns": median_ns, "mad_ns": mad_ns, "p95_ns": p95_ns}:
            raise EvidenceError(f"{location}.{name} timing statistics mismatch")
    return observation


def extract_performance_observation(
    path: Path,
    *,
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise EvidenceError(f"performance stdout must be a regular file: {path}")
    payloads = [
        line[len(PERFORMANCE_BASELINE_MARKER) :]
        for line in path.read_bytes().splitlines()
        if line.startswith(PERFORMANCE_BASELINE_MARKER)
    ]
    if len(payloads) != 1:
        raise EvidenceError("performance stdout must contain exactly one baseline marker")
    payload = payloads[0]
    observation = strict_json_loads(payload)
    if canonical_json_bytes(observation).rstrip(b"\n") != payload:
        raise EvidenceError("performance observation marker is not canonical JSON")
    return validate_performance_observation(
        observation, contract=contract, location="$performance_observation"
    )


def _validate_package_process(value: Any, location: str, *, allow_empty: bool) -> None:
    process = _exact_keys(value, {"bytes", "returncode", "sha256"}, location)
    if _require_int(process["returncode"], f"{location}.returncode") != 0:
        raise EvidenceError(f"{location}.returncode must be zero")
    record = _validate_hash_record(
        {"bytes": process["bytes"], "sha256": process["sha256"]}, location
    )
    if not allow_empty and record["bytes"] == 0:
        raise EvidenceError(f"{location} must not be empty")


def validate_package_result(
    value: Any, *, contract: Mapping[str, Any]
) -> dict[str, Any]:
    package_authority = contract["package"]
    package = _exact_keys(
        value,
        {
            "build_logs",
            "install_log",
            "schema",
            "smoke",
            "smoke_log",
            "sources",
            "status",
            "wheels",
        },
        "$package",
    )
    if package["schema"] != package_authority["package_result_schema"]:
        raise EvidenceError("package result schema mismatch")
    if package["status"] != "PASS":
        raise EvidenceError("package result status must be PASS")
    distributions = _exact_keys(
        package_authority["local_distributions"],
        {"ANYfileIO", "ANYgeometry", "ANYmaterial", "ANYmesh", "ANYsolver"},
        "$contract.package.local_distributions",
    )
    names = set(distributions)
    build_logs = _exact_keys(package["build_logs"], names, "$package.build_logs")
    for name in names:
        _validate_package_process(
            build_logs[name], f"$package.build_logs.{name}", allow_empty=False
        )
    _validate_package_process(package["install_log"], "$package.install_log", allow_empty=False)
    smoke_log = _validate_hash_record(package["smoke_log"], "$package.smoke_log")
    if smoke_log["bytes"] == 0:
        raise EvidenceError("package smoke log must not be empty")
    sources = _exact_keys(package["sources"], names, "$package.sources")
    for name in names:
        source = _exact_keys(
            sources[name],
            {"archive", "archive_log", "commit", "content", "tree"},
            f"$package.sources.{name}",
        )
        for key in ("commit", "tree"):
            if not isinstance(source[key], str) or not GIT_OBJECT_RE.fullmatch(source[key]):
                raise EvidenceError(f"package source {name} {key} is invalid")
        archive = _validate_hash_record(source["archive"], f"$package.sources.{name}.archive")
        if archive["bytes"] == 0:
            raise EvidenceError(f"package source archive is empty: {name}")
        _validate_package_process(
            source["archive_log"], f"$package.sources.{name}.archive_log", allow_empty=True
        )
        content = _exact_keys(
            source["content"], {"files", "sha256"}, f"$package.sources.{name}.content"
        )
        _require_int(content["files"], f"$package.sources.{name}.content.files", minimum=1)
        _require_hash(content["sha256"], f"$package.sources.{name}.content.sha256")
    wheels = _exact_keys(package["wheels"], names, "$package.wheels")
    for name in names:
        _validate_hash_record(wheels[name], f"$package.wheels.{name}", filename=True)
        if wheels[name]["bytes"] == 0 or not wheels[name]["filename"].endswith(".whl"):
            raise EvidenceError(f"package wheel is invalid: {name}")
    smoke = _exact_keys(
        package["smoke"],
        {"diagnostics_schema", "legacy_warning", "non_q4_types", "origins", "q4_type"},
        "$package.smoke",
    )
    expected_smoke = package_authority["smoke"]
    for key in ("diagnostics_schema", "legacy_warning", "non_q4_types", "q4_type"):
        if smoke[key] != expected_smoke[key]:
            raise EvidenceError(f"package smoke {key} mismatch")
    expected_packages = set(distributions.values())
    origins = _exact_keys(smoke["origins"], expected_packages, "$package.smoke.origins")
    for package_name, origin in origins.items():
        pure = PurePosixPath(origin) if isinstance(origin, str) else None
        if (
            pure is None
            or pure.is_absolute()
            or ".." in pure.parts
            or not pure.parts
            or pure.parts[0] != package_name
        ):
            raise EvidenceError(f"package smoke origin is invalid: {package_name}")
    return package


def validate_result(
    value: Any,
    *,
    contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    contract = dict(contract or load_contract())
    requests = _request_table(contract)
    common_commands = _non_resource_command_table(contract)
    producer_sha256 = _require_hash(
        contract["runner_inputs"]["process_runner"]["sha256"],
        "$contract.runner_inputs.process_runner.sha256",
    )
    record = _exact_keys(
        value,
        {
            "candidate",
            "common_lanes",
            "cycles",
            "hard_gates",
            "ledger",
            "package_artifacts",
            "performance_observations",
            "production_boundary",
            "resource_requests",
            "schema",
            "siblings",
            "terminal",
        },
        "$result",
    )
    if record["schema"] != RESULT_SCHEMA:
        raise EvidenceError("burn-in result schema mismatch")
    candidate = _exact_keys(record["candidate"], {"clean", "commit", "tree"}, "$.candidate")
    if candidate["clean"] is not True:
        raise EvidenceError("candidate must be recorded clean")
    for key in ("commit", "tree"):
        if not isinstance(candidate[key], str) or not GIT_OBJECT_RE.fullmatch(candidate[key]):
            raise EvidenceError(f"candidate {key} is invalid")
    common = _exact_keys(record["common_lanes"], {"additive", "package", "quick"}, "$.common_lanes")
    common_processes = {
        "quick": _validate_common_lane(
            common["quick"],
            "$.common_lanes.quick",
            expected_command_sha256=common_commands["quick"],
            expected_inventory=contract["lane_inventories"]["quick"],
            expected_producer_sha256=producer_sha256,
            process_count=1,
        ),
        "package": _validate_common_lane(
            common["package"],
            "$.common_lanes.package",
            expected_command_sha256=common_commands["package"],
            expected_inventory=contract["lane_inventories"]["package"],
            expected_producer_sha256=producer_sha256,
            process_count=1,
        ),
        "additive": _validate_common_lane(
            common["additive"],
            "$.common_lanes.additive",
            expected_command_sha256=common_commands["additive"],
            expected_inventory=contract["lane_inventories"]["additive"],
            expected_producer_sha256=producer_sha256,
            process_count=3,
        ),
    }
    _validate_hash_record(record["ledger"], "$.ledger")
    if not isinstance(record["cycles"], list) or len(record["cycles"]) != 2:
        raise EvidenceError("result must contain two cycles")
    cycle_processes: dict[tuple[int, str], dict[str, Any]] = {}
    for expected_cycle, cycle_value in enumerate(record["cycles"], start=1):
        cycle = _exact_keys(cycle_value, {"cycle", "lanes", "status"}, f"$.cycles[{expected_cycle - 1}]")
        if cycle["cycle"] != expected_cycle:
            raise EvidenceError("cycle ordering mismatch")
        lanes = _exact_keys(cycle["lanes"], {"anyfem", "functional", "performance"}, f"$.cycles[{expected_cycle - 1}].lanes")
        processes: list[dict[str, Any]] = []
        for lane_name in ("functional", "anyfem", "performance"):
            request = requests[(expected_cycle, lane_name)]
            process = _validate_process(
                lanes[lane_name],
                f"$.cycles[{expected_cycle - 1}].lanes.{lane_name}",
                expected_request_id=request["request_id"],
                expected_command_sha256=request["command_sha256"],
                expected_producer_sha256=producer_sha256,
            )
            cycle_processes[(expected_cycle, lane_name)] = process
            processes.append(process)
        if cycle["status"] != _lane_status(processes):
            raise EvidenceError("cycle status does not match its lanes")
    if record["resource_requests"] != contract["resource_requests"]:
        raise EvidenceError("result resource requests differ from the contract")
    if record["siblings"] != contract["sibling_authority"]:
        raise EvidenceError("result sibling authority differs from the contract")
    if record["production_boundary"] != contract["production_boundary"]:
        raise EvidenceError("result production boundary differs from the contract")
    performance_rows = record["performance_observations"]
    performance_passes = [
        cycle_processes[(cycle, "performance")]["status"] == "PASS"
        for cycle in (1, 2)
    ]
    if all(performance_passes):
        if not isinstance(performance_rows, list) or len(performance_rows) != 2:
            raise EvidenceError("two passed performance lanes require two observations")
        validated_observations: list[dict[str, Any]] = []
        for expected_cycle, row_value in enumerate(performance_rows, start=1):
            row = _exact_keys(
                row_value,
                {"cycle", "observation"},
                f"$.performance_observations[{expected_cycle - 1}]",
            )
            if row["cycle"] != expected_cycle:
                raise EvidenceError("performance observation cycle ordering mismatch")
            validated_observations.append(
                validate_performance_observation(
                    row["observation"],
                    contract=contract,
                    location=f"$.performance_observations[{expected_cycle - 1}].observation",
                )
            )
    elif performance_rows is not None:
        raise EvidenceError("unpassed performance lanes forbid performance observations")
    hard_gates = _exact_keys(
        record["hard_gates"],
        {
            "batch_path_equality",
            "q4_numerical_parity",
            "qualified_s3_opt_in",
            "s3_default_legacy",
            "warm_cache_reuse",
        },
        "$.hard_gates",
    )
    s3_gate_nodes = _exact_keys(
        contract["hard_gate_authority"]["s3"],
        {"qualified_s3_opt_in", "s3_default_legacy"},
        "$contract.hard_gate_authority.s3",
    )
    for name, nodes in s3_gate_nodes.items():
        if (
            not isinstance(nodes, list)
            or not nodes
            or any(not isinstance(node, str) or "::" not in node for node in nodes)
        ):
            raise EvidenceError(f"S3 hard-gate node authority is invalid: {name}")
    derived_hard_gates = {
        "batch_path_equality": (
            "PASS" if all(performance_passes) else "NOT_EVALUATED"
        ),
        "q4_numerical_parity": (
            "PASS" if all(performance_passes) else "NOT_EVALUATED"
        ),
        "qualified_s3_opt_in": (
            "PASS" if common["additive"]["status"] == "PASS" else "NOT_EVALUATED"
        ),
        "s3_default_legacy": (
            "PASS" if common["additive"]["status"] == "PASS" else "NOT_EVALUATED"
        ),
        "warm_cache_reuse": (
            "PASS" if all(performance_passes) else "NOT_EVALUATED"
        ),
    }
    if hard_gates != derived_hard_gates:
        raise EvidenceError("hard gates are not derived from their frozen lanes")
    sequence = [
        common["quick"]["status"],
        common["package"]["status"],
        common["additive"]["status"],
        *[
            cycle_processes[(cycle, lane)]["status"]
            for cycle in (1, 2)
            for lane in ("functional", "anyfem", "performance")
        ],
    ]
    resource_processes = [
        cycle_processes[(cycle, lane)]
        for cycle in (1, 2)
        for lane in ("functional", "anyfem", "performance")
    ]
    _require_barrier(
        common_processes["quick"], common_processes["package"], "quick -> package"
    )
    _require_barrier(
        common_processes["package"], common_processes["additive"], "package -> additive"
    )
    _require_barrier(
        common_processes["additive"], resource_processes[:1], "common -> resources"
    )
    for index in range(len(resource_processes) - 1):
        _require_barrier(
            resource_processes[index : index + 1],
            resource_processes[index + 1 : index + 2],
            f"resource {index + 1} -> resource {index + 2}",
        )
    first_nonpass = next((index for index, status in enumerate(sequence) if status != "PASS"), None)
    success = first_nonpass is None and all(value == "PASS" for value in hard_gates.values())
    expected_terminal = (
        contract["adjudication"]["result_success_terminal"]
        if success
        else contract["adjudication"]["result_blocked_terminal"]
    )
    if record["terminal"] != expected_terminal:
        raise EvidenceError("terminal does not follow frozen precedence")
    if first_nonpass is not None and any(status != "NOT_RUN" for status in sequence[first_nonpass + 1 :]):
        raise EvidenceError("a failed/not-run lane must leave every later lane NOT_RUN")
    package_artifacts = record["package_artifacts"]
    package_status = common["package"]["status"]
    if package_status == "PASS":
        artifacts = _exact_keys(package_artifacts, {"result", "wheel"}, "$.package_artifacts")
        _validate_hash_record(artifacts["result"], "$.package_artifacts.result")
        _validate_hash_record(artifacts["wheel"], "$.package_artifacts.wheel", filename=True)
    elif package_status == "FAIL":
        artifacts = _exact_keys(package_artifacts, {"result", "wheel"}, "$.package_artifacts")
        if artifacts["result"] is not None:
            _validate_hash_record(artifacts["result"], "$.package_artifacts.result")
        if artifacts["wheel"] is not None:
            _validate_hash_record(
                artifacts["wheel"], "$.package_artifacts.wheel", filename=True
            )
    elif package_artifacts is not None:
        raise EvidenceError("not-run package lane forbids package artifacts")
    return record


def _git(path: Path, *args: str, contract: Mapping[str, Any]) -> str:
    git = execution_tool_path(contract, "git")
    completed = subprocess.run(
        [
            str(git),
            "--no-replace-objects",
            "-c",
            f"safe.directory={path}",
            "-c",
            "core.autocrlf=true",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.quotepath=false",
            "-c",
            "core.untrackedCache=false",
            "-c",
            "status.showUntrackedFiles=all",
            "-C",
            str(path),
            *args,
        ],
        capture_output=True,
        env=sanitized_execution_environment(contract),
        text=True,
        check=False,
    )
    if completed.returncode:
        raise EvidenceError(f"git {' '.join(args)} failed for {path}: {completed.stderr.strip()}")
    return completed.stdout.strip()


def assert_clean_execution_repository(path: Path, *, contract: Mapping[str, Any]) -> None:
    path = path.resolve(strict=True)
    guard = contract["execution"]["environment_guard"]
    fixed = guard["fixed"]
    pycache_prefix = Path(guard.get("python_cache_root", ""))
    numba_cache = Path(guard.get("numba_cache_root", ""))
    if (
        fixed.get("PYTHONDONTWRITEBYTECODE") != "1"
        or not pycache_prefix.is_absolute()
        or not numba_cache.is_absolute()
        or path == pycache_prefix
        or path in pycache_prefix.parents
        or path == numba_cache
        or path in numba_cache.parents
    ):
        raise EvidenceError("external Python/Numba cache isolation is not frozen")
    top = Path(_git(path, "rev-parse", "--show-toplevel", contract=contract)).resolve(
        strict=True
    )
    if top != path:
        raise EvidenceError(f"execution path is not a repository root: {path}")
    replacements = _git(
        path,
        "for-each-ref",
        "--format=%(refname)",
        "refs/replace",
        contract=contract,
    )
    if replacements:
        raise EvidenceError(f"Git replacement refs are forbidden: {path}")
    if _git(path, "rev-parse", "--is-shallow-repository", contract=contract) != "false":
        raise EvidenceError(f"shallow execution repositories are forbidden: {path}")
    graft_path = Path(
        _git(path, "rev-parse", "--git-path", "info/grafts", contract=contract)
    )
    if not graft_path.is_absolute():
        graft_path = path / graft_path
    if graft_path.exists() or graft_path.is_symlink():
        raise EvidenceError(f"Git graft metadata is forbidden: {path}")
    attributes_path = Path(
        _git(path, "rev-parse", "--git-path", "info/attributes", contract=contract)
    )
    if not attributes_path.is_absolute():
        attributes_path = path / attributes_path
    if attributes_path.exists() or attributes_path.is_symlink():
        raise EvidenceError(f"Git info attributes are forbidden: {path}")
    if _git(
        path,
        "status",
        "--porcelain=v1",
        "--untracked-files=no",
        contract=contract,
    ):
        raise EvidenceError(f"execution repository is dirty: {path}")
    tracked = _git(path, "ls-files", "-v", "-z", contract=contract)
    for record in tracked.split("\0"):
        if record and (len(record) < 3 or record[0] != "H" or record[1] != " "):
            raise EvidenceError(f"tracked execution path has a hidden index flag: {path}")
    untracked = _git(path, "ls-files", "-z", "--others", contract=contract)
    ignored = _git(
        path,
        "ls-files",
        "-z",
        "--others",
        "--ignored",
        "--exclude-standard",
        contract=contract,
    )
    forbidden_suffixes = (
        ".bat",
        ".cmd",
        ".dll",
        ".egg-link",
        ".exe",
        ".ps1",
        ".py",
        ".pyo",
        ".pyd",
        ".pth",
        ".so",
        ".zip",
    )
    forbidden_basenames = {
        ".pytest.ini",
        ".pytest.toml",
        "pyproject.toml",
        "pytest.ini",
        "pytest.toml",
        "setup.cfg",
        "tox.ini",
    }
    hidden_python = []
    for name in sorted(set(untracked.split("\0")) | set(ignored.split("\0"))):
        if not name:
            continue
        normalized = PurePosixPath(name)
        lowered = name.casefold()
        if lowered.endswith(".pyc") and "__pycache__" in normalized.parts:
            continue
        if (
            normalized.name.casefold() in forbidden_basenames
            or lowered.endswith((".pyc", *forbidden_suffixes))
        ):
            hidden_python.append(name)
    if hidden_python:
        raise EvidenceError(
            f"untracked/ignored execution paths are forbidden: {hidden_python[:3]}"
        )


def _iter_processes(record: Mapping[str, Any]) -> Iterable[tuple[str, Mapping[str, Any]]]:
    for lane in ("quick", "package", "additive"):
        for index, process in enumerate(record["common_lanes"][lane]["processes"], start=1):
            yield f"common.{lane}.{index}", process
    for cycle in record["cycles"]:
        for lane in ("functional", "anyfem", "performance"):
            yield f"cycle_{cycle['cycle']}.{lane}", cycle["lanes"][lane]


def _validate_process_result_artifact(
    path: Path,
    *,
    candidate: Mapping[str, Any],
    process: Mapping[str, Any],
    request: Mapping[str, Any] | None,
) -> None:
    raw = path.read_bytes()
    wrapper = strict_json_loads(raw)
    if raw != canonical_json_bytes(wrapper):
        raise EvidenceError(f"process result is not canonical JSON: {path}")
    wrapper = _exact_keys(
        wrapper,
        {
            "candidate_commit",
            "candidate_tree",
            "command_sha256",
            "elapsed_seconds",
            "ended_at",
            "execution_state",
            "exit_code",
            "producer_sha256",
            "request_id",
            "request_sha256",
            "resource_lock_released",
            "schema",
            "started_at",
            "stderr",
            "stdout",
        },
        "$process_result",
    )
    expected_request_id = None if request is None else request["request_id"]
    expected_request_sha256 = None if request is None else request["request_sha256"]
    expected_lock = process["resource_lock_released"]
    expected = {
        "candidate_commit": candidate["commit"],
        "candidate_tree": candidate["tree"],
        "command_sha256": process["command_sha256"],
        "elapsed_seconds": process["elapsed_seconds"],
        "ended_at": process["ended_at"],
        "execution_state": process["execution_state"],
        "exit_code": process["exit_code"],
        "producer_sha256": contract_producer_sha256(),
        "request_id": expected_request_id,
        "request_sha256": expected_request_sha256,
        "resource_lock_released": expected_lock,
        "schema": PROCESS_RESULT_SCHEMA,
        "started_at": process["started_at"],
        "stderr": process["stderr"],
        "stdout": process["stdout"],
    }
    if wrapper != expected:
        raise EvidenceError(f"process result contents mismatch: {path}")


def contract_producer_sha256(contract: Mapping[str, Any] | None = None) -> str:
    contract = dict(contract or load_contract())
    return contract["runner_inputs"]["process_runner"]["sha256"]


def approval_ledger_fields(
    request: Mapping[str, Any],
    request_row: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> list[str]:
    return [
        request_row["request_id"],
        "APPROVED",
        request["task"],
        request["repository"],
        (
            f"Immutable request bytes {request_row['bytes']} SHA-256 "
            f"{request_row['request_sha256'].upper()}; command SHA-256 "
            f"{request_row['command_sha256'].upper()}"
        ),
        f"{request['estimate_minutes']} minutes",
        (
            "Standing user approval received for required completion requests; "
            f"candidate {candidate['commit']}; tree {candidate['tree']}; "
            "two corrected serial burn-in cycles only."
        ),
    ]


def terminal_ledger_fields(
    request: Mapping[str, Any],
    process: Mapping[str, Any],
    result_record: Mapping[str, Any] | None,
) -> list[str]:
    if process["status"] == "NOT_RUN":
        return [
            request["request_id"],
            "CANCELLED_NOT_RUN",
            request["task"],
            request["repository"],
            "Not executed",
            f"{request['estimate_minutes']} minutes",
            "Cancelled by frozen fail-fast policy; request was never acquired; do not reuse.",
        ]
    if result_record is None:
        raise EvidenceError("executed resource process lacks a result record")
    status = "COMPLETED_PASS" if process["status"] == "PASS" else "COMPLETED_FAIL"
    note = (
        f"Candidate {process['candidate_commit']}; tree {process['candidate_tree']}; "
        f"exit {process['exit_code']}; result bytes {result_record['bytes']} SHA-256 "
        f"{result_record['sha256'].upper()}; stdout bytes {process['stdout']['bytes']} "
        f"SHA-256 {process['stdout']['sha256'].upper()}; stderr bytes "
        f"{process['stderr']['bytes']} SHA-256 {process['stderr']['sha256'].upper()}; "
        f"elapsed {process['elapsed_seconds']:.6f}s; lock released "
        f"{process['resource_lock_released']}; execution state "
        f"{process['execution_state']}."
    )
    return [
        request["request_id"],
        status,
        request["task"],
        request["repository"],
        (
            "Exact immutable request command executed once"
            if process["execution_state"] == "EXECUTED"
            else "Request consumed after acquisition/process-start failure; command not retried"
        ),
        f"{request['estimate_minutes']} minutes",
        note,
    ]


def _ledger_entries(ledger: str, request_id: str, status: str) -> list[list[str]]:
    entries: list[list[str]] = []
    for line in ledger.splitlines():
        if not line.startswith("|") or not line.endswith("|"):
            continue
        fields = [field.strip() for field in line.split("|")[1:-1]]
        if len(fields) == 8 and fields[1] == request_id and fields[2] == status:
            _require_timestamp(fields[0], f"ledger {request_id} {status} timestamp")
            entries.append(fields)
    return entries


def _require_successor_after_terminal(
    started_at: dt.datetime,
    previous_terminal: dt.datetime | None,
    request_id: str,
) -> None:
    if previous_terminal is not None and started_at < previous_terminal:
        raise EvidenceError(
            f"resource successor starts before predecessor terminal: {request_id}"
        )


def validate_external_bindings(
    record: Mapping[str, Any],
    *,
    contract: Mapping[str, Any] | None = None,
    require_aggregate: bool = True,
) -> None:
    contract = dict(contract or load_contract())
    validated = validate_result(record, contract=contract)
    first_pycache, first_numba_cache = execution_cache_paths(
        contract, "common.quick.1"
    )
    allowed_cache_children = {
        PROCESS_DIRECTORY_NAMES[prefix]
        for prefix, process in _iter_processes(validated)
        if process["status"] != "NOT_RUN"
    }
    for name, cache_root in (
        ("Python", first_pycache.parent),
        ("Numba", first_numba_cache.parent),
    ):
        if cache_root.exists():
            if not cache_root.is_dir() or cache_root.is_symlink():
                raise EvidenceError(f"{name} cache root is not a canonical directory")
            children = list(cache_root.iterdir())
            if any(
                child.name not in allowed_cache_children
                or not child.is_dir()
                or child.is_symlink()
                for child in children
            ):
                raise EvidenceError(
                    f"{name} cache extent is outside one-shot process authority"
                )
    aggregate_path = output_root(contract) / contract["adjudication"][
        "external_result_filename"
    ]
    if require_aggregate:
        if aggregate_path.is_symlink() or not aggregate_path.is_file():
            raise EvidenceError("canonical external aggregate is missing")
        if aggregate_path.read_bytes() != canonical_json_bytes(validated):
            raise EvidenceError("canonical external aggregate differs from adjudicated result")
    elif aggregate_path.exists():
        raise EvidenceError("aggregate output already exists before exclusive promotion")
    repositories = external_repository_paths(contract)
    for name, path in repositories.items():
        if path.resolve(strict=True) != path or not path.is_dir():
            raise EvidenceError(f"{name} repository is not the exact frozen directory")
    candidate_path = repositories["ANYsolver"]
    sibling_paths = {
        name: repositories[name] for name in contract["sibling_authority"]
    }
    manager = resource_manager_authority(contract)
    validate_resource_approval_authority(contract)
    manager_root = Path(manager["root"])
    if manager_root.resolve(strict=True) != manager_root or not manager_root.is_dir():
        raise EvidenceError("resource-manager root is not the exact frozen directory")
    for key in ("acquire", "release"):
        authority = manager[key]
        path = manager_root / authority["filename"]
        if path.is_symlink() or file_hash_record(path) != {
            "bytes": authority["bytes"],
            "sha256": authority["sha256"],
        }:
            raise EvidenceError(f"resource-manager {key} script identity mismatch")
    ledger_path = manager_root / manager["ledger"]
    requests_root = manager_root / manager["requests"]
    if (
        ledger_path.is_symlink()
        or not ledger_path.is_file()
        or requests_root.is_symlink()
        or not requests_root.is_dir()
    ):
        raise EvidenceError("resource-manager ledger/requests may not be symlinks")
    if (manager_root / manager["active_lock"]).exists():
        raise EvidenceError("resource-manager active lock remains after adjudication")
    candidate_path = candidate_path.resolve(strict=True)
    assert_clean_execution_repository(candidate_path, contract=contract)
    if _git(candidate_path, "rev-parse", "HEAD", contract=contract) != validated["candidate"]["commit"]:
        raise EvidenceError("candidate HEAD mismatch")
    if _git(candidate_path, "rev-parse", "HEAD^{tree}", contract=contract) != validated["candidate"]["tree"]:
        raise EvidenceError("candidate tree mismatch")
    authority = contract["authority_commit"]
    introductions = _git(
        candidate_path,
        "log",
        "--format=%H",
        "--diff-filter=A",
        "--",
        "docs/reference_cases/e4_pl_s3_q4_burnin_contract.json",
        contract=contract,
    ).splitlines()
    if introductions != [validated["candidate"]["commit"]]:
        raise EvidenceError("candidate is not the unique registered authority commit")
    authority_metadata = _git(
        candidate_path,
        "show",
        "-s",
        "--format=%P%n%s",
        validated["candidate"]["commit"],
        contract=contract,
    ).splitlines()
    if authority_metadata != [authority["exact_parent"], authority["subject"]]:
        raise EvidenceError("authority parent or subject mismatch")
    authority_paths = _git(
        candidate_path,
        "diff",
        "--name-only",
        authority["exact_parent"],
        validated["candidate"]["commit"],
        contract=contract,
    ).splitlines()
    if authority_paths != authority["exact_paths"]:
        raise EvidenceError("authority changed-path extent mismatch")
    if set(sibling_paths) != set(contract["sibling_authority"]):
        raise EvidenceError("sibling repository bindings are incomplete")
    for name, authority in contract["sibling_authority"].items():
        path = sibling_paths[name].resolve(strict=True)
        assert_clean_execution_repository(path, contract=contract)
        if _git(path, "rev-parse", "HEAD", contract=contract) != authority["commit"]:
            raise EvidenceError(f"{name} commit mismatch")
        if _git(path, "rev-parse", "HEAD^{tree}", contract=contract) != authority["tree"]:
            raise EvidenceError(f"{name} tree mismatch")
    requests = _request_table(contract)
    request_payloads: dict[str, dict[str, Any]] = {}
    for (_cycle, lane), row in requests.items():
        request_path = requests_root / f"{row['request_id']}.json"
        if request_path.name != f"{row['request_id']}.json" or request_path.is_symlink():
            raise EvidenceError(f"request path mismatch: {row['request_id']}")
        if file_hash_record(request_path) != {
            "bytes": row["bytes"],
            "sha256": row["request_sha256"],
        }:
            raise EvidenceError(f"request identity mismatch: {row['request_id']}")
        request = strict_json_load(request_path)
        if request.get("request_id") != row["request_id"]:
            raise EvidenceError("request payload ID mismatch")
        expected_repository = repositories["ANYfem" if lane == "anyfem" else "ANYsolver"]
        if Path(request.get("repository", "")) != expected_repository:
            raise EvidenceError(f"request repository mismatch: {row['request_id']}")
        if request.get("status") != "PENDING":
            raise EvidenceError(f"immutable request status mismatch: {row['request_id']}")
        command = request.get("command")
        if not isinstance(command, str):
            raise EvidenceError("request command must be a string")
        if sha256_bytes(command.encode("utf-8")) != row["command_sha256"]:
            raise EvidenceError("request command mismatch")
        request_payloads[row["request_id"]] = request
    snapshot_name = _require_string(
        contract["adjudication"]["ledger_snapshot_filename"],
        "$contract.adjudication.ledger_snapshot_filename",
    )
    if Path(snapshot_name).name != snapshot_name:
        raise EvidenceError("resource ledger snapshot must be a basename")
    ledger_snapshot_path = output_root(contract) / snapshot_name
    if (
        ledger_snapshot_path.is_symlink()
        or not ledger_snapshot_path.is_file()
        or file_hash_record(ledger_snapshot_path) != validated["ledger"]
    ):
        raise EvidenceError("immutable resource ledger snapshot identity mismatch")
    ledger = ledger_snapshot_path.read_text(encoding="utf-8")
    process_by_request = {
        process["request_id"]: process
        for _prefix, process in _iter_processes(validated)
        if process["request_id"] is not None
    }
    common_preflight_passed = all(
        validated["common_lanes"][lane]["status"] == "PASS"
        for lane in ("quick", "package", "additive")
    )
    approval_times: dict[str, dt.datetime] = {}
    for row in requests.values():
        request_id = row["request_id"]
        approvals = _ledger_entries(ledger, request_id, "APPROVED")
        terminals = [
            entry
            for status in ("COMPLETED_PASS", "COMPLETED_FAIL", "CANCELLED_NOT_RUN")
            for entry in _ledger_entries(ledger, request_id, status)
        ]
        if not common_preflight_passed:
            if approvals or terminals or process_by_request[request_id]["status"] != "NOT_RUN":
                raise EvidenceError(
                    f"failed common preflight consumed resource authority: {request_id}"
                )
            continue
        expected_approval = approval_ledger_fields(
            request_payloads[request_id], row, validated["candidate"]
        )
        if len(approvals) != 1 or approvals[0][1:] != expected_approval:
            raise EvidenceError(f"request approval ledger row mismatch: {request_id}")
        approval_times[request_id] = dt.datetime.fromisoformat(
            approvals[0][0].replace("Z", "+00:00")
        )
    additive_ends = [
        dt.datetime.fromisoformat(process["ended_at"].replace("Z", "+00:00"))
        for process in validated["common_lanes"]["additive"]["processes"]
        if process["status"] != "NOT_RUN"
    ]
    first_resource = next(
        (
            process
            for _prefix, process in _iter_processes(validated)
            if process.get("request_id") is not None and process["status"] != "NOT_RUN"
        ),
        None,
    )
    if approval_times and additive_ends and max(additive_ends) > min(approval_times.values()):
        raise EvidenceError("resource approvals precede completion of common preflight")
    if approval_times and first_resource is not None:
        first_start = dt.datetime.fromisoformat(
            first_resource["started_at"].replace("Z", "+00:00")
        )
        if max(approval_times.values()) > first_start:
            raise EvidenceError("all resource approvals must precede the first resource run")
    expected_artifacts: dict[str, tuple[Mapping[str, Any], Path]] = {}
    for prefix, process in _iter_processes(validated):
        directory = process_output_directory(contract, prefix)
        if process["status"] == "NOT_RUN":
            if directory.exists():
                raise EvidenceError(f"not-run process has an output directory: {prefix}")
        else:
            if not directory.is_dir() or directory.is_symlink() or {
                path.name for path in directory.iterdir()
            } != {"result.json", "stderr.txt", "stdout.txt"}:
                raise EvidenceError(f"process output extent mismatch: {prefix}")
            for key in ("result", "stderr", "stdout"):
                expected_artifacts[f"{prefix}.{key}"] = (
                    process[key],
                    directory / f"{key}.{'json' if key == 'result' else 'txt'}",
                )
    for name, (expected, path) in expected_artifacts.items():
        if path.is_symlink() or file_hash_record(path) != expected:
            raise EvidenceError(f"process artifact identity mismatch: {name}")
    requests_by_id = {row["request_id"]: row for row in requests.values()}
    wrappers_by_request: dict[str, dict[str, Any]] = {}
    for prefix, process in _iter_processes(validated):
        if process["status"] == "NOT_RUN":
            continue
        request = (
            None
            if process["request_id"] is None
            else requests_by_id[process["request_id"]]
        )
        _validate_process_result_artifact(
            expected_artifacts[f"{prefix}.result"][1],
            candidate=validated["candidate"],
            process=process,
            request=request,
        )
        if request is not None:
            wrappers_by_request[request["request_id"]] = strict_json_load(
                expected_artifacts[f"{prefix}.result"][1]
            )
    last_executed_end: dt.datetime | None = None
    last_terminal_time: dt.datetime | None = None
    for request_id, process in process_by_request.items():
        if not common_preflight_passed:
            continue
        request = request_payloads[request_id]
        terminal_status = {
            "PASS": "COMPLETED_PASS",
            "FAIL": "COMPLETED_FAIL",
            "NOT_RUN": "CANCELLED_NOT_RUN",
        }[process["status"]]
        entries = _ledger_entries(ledger, request_id, terminal_status)
        all_terminal_entries = [
            entry
            for status in ("COMPLETED_PASS", "COMPLETED_FAIL", "CANCELLED_NOT_RUN")
            for entry in _ledger_entries(ledger, request_id, status)
        ]
        wrapper = wrappers_by_request.get(request_id)
        result_record = (
            None
            if wrapper is None
            else file_hash_record(
                process_output_directory(
                    contract,
                    next(
                        prefix
                        for prefix, candidate_process in _iter_processes(validated)
                        if candidate_process.get("request_id") == request_id
                    ),
                )
                / "result.json"
            )
        )
        expected_fields = terminal_ledger_fields(
            request, process if wrapper is None else wrapper, result_record
        )
        if (
            len(entries) != 1
            or len(all_terminal_entries) != 1
            or entries[0][1:] != expected_fields
        ):
            raise EvidenceError(f"request terminal ledger row mismatch: {request_id}")
        terminal_time = dt.datetime.fromisoformat(entries[0][0].replace("Z", "+00:00"))
        if process["status"] != "NOT_RUN":
            start_time = dt.datetime.fromisoformat(
                process["started_at"].replace("Z", "+00:00")
            )
            _require_successor_after_terminal(
                start_time, last_terminal_time, request_id
            )
            end_time = dt.datetime.fromisoformat(process["ended_at"].replace("Z", "+00:00"))
            if approval_times[request_id] > start_time or terminal_time < end_time:
                raise EvidenceError(f"resource ledger chronology mismatch: {request_id}")
            last_executed_end = end_time
        elif (
            last_executed_end is None
            or last_terminal_time is None
            or terminal_time < last_terminal_time
        ):
            raise EvidenceError(f"resource cancellation chronology mismatch: {request_id}")
        last_terminal_time = terminal_time
    if validated["performance_observations"] is not None:
        for row in validated["performance_observations"]:
            prefix = f"cycle_{row['cycle']}.performance"
            observed = extract_performance_observation(
                expected_artifacts[f"{prefix}.stdout"][1], contract=contract
            )
            if observed != row["observation"]:
                raise EvidenceError(f"cycle {row['cycle']} performance observation mismatch")
    package_passed = validated["common_lanes"]["package"]["status"] == "PASS"
    package_result_path = output_root(contract) / contract["package"]["result_filename"]
    wheel_path = output_root(contract) / contract["package"]["wheel_filename"]
    if package_passed:
        if wheel_path.is_symlink() or not wheel_path.is_file():
            raise EvidenceError("canonical wheel must be a regular non-symlink file")
        if file_hash_record(package_result_path) != validated["package_artifacts"]["result"]:
            raise EvidenceError("package result identity mismatch")
        wheel_expected = dict(validated["package_artifacts"]["wheel"])
        filename = wheel_expected.pop("filename")
        if wheel_path.name != filename or file_hash_record(wheel_path) != wheel_expected:
            raise EvidenceError("wheel identity mismatch")
        package = strict_json_load(package_result_path)
        if package_result_path.read_bytes() != canonical_json_bytes(package):
            raise EvidenceError("package result is not canonical JSON")
        package = validate_package_result(package, contract=contract)
        expected_sources = {
            "ANYsolver": validated["candidate"],
            **{
                name: authority
                for name, authority in contract["sibling_authority"].items()
                if name != "ANYfem"
            },
        }
        for name, authority in expected_sources.items():
            source = package.get("sources", {}).get(name, {})
            if source.get("commit") != authority["commit"] or source.get("tree") != authority["tree"]:
                raise EvidenceError(f"package source authority mismatch: {name}")
        if package.get("wheels", {}).get("ANYsolver") != validated[
            "package_artifacts"
        ]["wheel"]:
            raise EvidenceError("package result ANYsolver wheel mismatch")
    elif validated["common_lanes"]["package"]["status"] == "FAIL":
        artifacts = validated["package_artifacts"]
        for key, path, filename in (
            ("result", package_result_path, False),
            ("wheel", wheel_path, True),
        ):
            expected = artifacts[key]
            if expected is None:
                if path.exists() or path.is_symlink():
                    raise EvidenceError(
                        f"unrecorded failed-package artifact exists: {key}"
                    )
                continue
            if path.is_symlink() or not path.is_file():
                raise EvidenceError(f"failed-package artifact is missing: {key}")
            observed = file_hash_record(path)
            expected_hash = dict(expected)
            if filename:
                expected_name = expected_hash.pop("filename")
                if path.name != expected_name:
                    raise EvidenceError("failed-package wheel filename mismatch")
            if observed != expected_hash:
                raise EvidenceError(f"failed-package artifact identity mismatch: {key}")
    elif (
        package_result_path.exists()
        or package_result_path.is_symlink()
        or wheel_path.exists()
        or wheel_path.is_symlink()
    ):
        raise EvidenceError("not-run package lane left canonical package artifacts")


def validate_adjudication_files(
    result_path: Path,
    status_path: Path,
    review_path: Path,
    *,
    contract: Mapping[str, Any] | None = None,
    repository_root: Path | None = ROOT,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    contract = dict(contract or load_contract())
    values = [strict_json_load(path) for path in (result_path, status_path, review_path)]
    raws = [path.read_bytes() for path in (result_path, status_path, review_path)]
    result = validate_result(values[0], contract=contract)
    validate_external_bindings(result, contract=contract)
    adjudication = contract["adjudication"]
    status = _exact_keys(
        values[1], set(adjudication["status_required_keys"]), "$status"
    )
    review = _exact_keys(
        values[2], set(adjudication["review_required_keys"]), "$review"
    )
    for raw, value, label in zip(
        raws, (result, status, review), ("result", "status", "review"), strict=True
    ):
        if raw != canonical_json_bytes(value):
            raise EvidenceError(f"{label} is not canonical JSON")
    success = result["terminal"] == adjudication["result_success_terminal"]
    if repository_root is not None:
        root = repository_root.resolve(strict=True)
        try:
            actual_paths = [
                path.resolve().relative_to(root).as_posix()
                for path in (result_path, status_path, review_path)
            ]
        except ValueError as exc:
            raise EvidenceError("adjudication output is outside the repository") from exc
        route = "success_paths" if success else "blocked_paths"
        if actual_paths != adjudication[route]:
            raise EvidenceError("adjudication output extent mismatch")
    if status["schema"] != adjudication["status_schema"]:
        raise EvidenceError("status schema mismatch")
    if status["gate_result_sha256"] != sha256_bytes(raws[0]):
        raise EvidenceError("status gate-result hash mismatch")
    expected_status = {
        "clean_cycles_recorded": 2 if success else 0,
        "gate_result_sha256": sha256_bytes(raws[0]),
        "legacy_q4_removal_authorized": False,
        "qualified_s3_default_activation_authorized": False,
        "schema": adjudication["status_schema"],
        "terminal": (
            adjudication["success_terminal"]
            if success
            else adjudication["blocked_terminal"]
        ),
    }
    if status != expected_status:
        raise EvidenceError("status does not follow the frozen adjudication")
    if review["schema"] != adjudication["review_schema"]:
        raise EvidenceError("review schema mismatch")
    if review["findings"] != []:
        raise EvidenceError("accepted independent review must have no findings")
    if review["reviewer_independence"] != adjudication["review_independence"]:
        raise EvidenceError("review independence mismatch")
    expected_verdict = adjudication[
        "accepted_success_verdict" if success else "accepted_blocked_verdict"
    ]
    if review["verdict"] != expected_verdict:
        raise EvidenceError("review verdict mismatch")
    reviewed_inputs = _exact_keys(
        review["reviewed_inputs"],
        set(adjudication["reviewed_input_hashes"]),
        "$review.reviewed_inputs",
    )
    expected_inputs = {
        "contract_sha256": sha256_bytes(canonical_json_bytes(contract)),
        "gate_result_sha256": sha256_bytes(raws[0]),
        "status_sha256": sha256_bytes(raws[1]),
    }
    if reviewed_inputs != expected_inputs:
        raise EvidenceError("reviewed-input hashes mismatch")
    return result, status, review


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="mode", required=True)
    result_parser = subparsers.add_parser("result")
    result_parser.add_argument("evidence", type=Path)
    adjudication_parser = subparsers.add_parser("adjudication")
    adjudication_parser.add_argument("result", type=Path)
    adjudication_parser.add_argument("status", type=Path)
    adjudication_parser.add_argument("review", type=Path)
    args = parser.parse_args(argv)
    if args.mode == "result":
        raw = args.evidence.read_bytes()
        record = strict_json_loads(raw)
        if raw != canonical_json_bytes(record):
            raise EvidenceError("burn-in result is not canonical JSON")
        validate_external_bindings(record)
    else:
        validate_adjudication_files(args.result, args.status, args.review)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
