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
import stat
import statistics
import subprocess
from typing import Any, Iterable, Mapping


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path(__file__).with_name("e4_pl_s3_q4_burnin_contract.json")
CONTRACT_SCHEMA = "anysolver.e4-pl-s3-q4-burn-in-contract-v4"
RESULT_SCHEMA = "anysolver.e4-pl-s3-q4-burn-in-result-v3"
PROCESS_RESULT_SCHEMA = "anysolver.e4-pl-s3-q4-process-result-v3"
LEDGER_SNAPSHOT_SCHEMA = "anysolver.e4-pl-s3-q4-resource-ledger-snapshot-v1"
PENDING_MANIFEST_SCHEMA = "anysolver.e4-pl-s3-q4-pending-process-manifest-v1"
FUNCTIONAL_WAVE_SCHEMA = "anysolver.e4-pl-s3-q4-functional-wave-v2"
FUNCTIONAL_WAVE_FILE_GRAPH_SCHEMA = (
    "anysolver.e4-pl-s3-q4-functional-wave-file-graph-v1"
)
FUNCTIONAL_WAVE_AGGREGATE_SCHEMA = (
    "anysolver.e4-pl-s3-q4-functional-wave-aggregate-v2"
)
FUNCTIONAL_WAVE_DIAGNOSTICS_SCHEMA = (
    "anysolver.e4-pl-s3-q4-functional-wave-diagnostics-v2"
)
FUNCTIONAL_SHARD_SCHEMA = "anysolver.e4-pl-s3-q4-functional-shard-v2"
PERFORMANCE_BASELINE_MARKER = b"Q1M_PERFORMANCE_BASELINE_JSON="
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
GIT_OBJECT_RE = re.compile(r"[0-9a-f]{40}\Z")
REQUEST_ID_RE = re.compile(r"[0-9a-f]{32}\Z")
V10_SUPERSEDED_REQUEST_IDS = (
    "7a0b6b26646d42f8b6a51787e47dc205",
    "4585253af140476fae32c9953926519b",
    "3bf2afed4d324947ad17a390a607bf00",
    "1e1de0b84cb2408aae25426aa95e87fa",
    "98ff7f767fbd4c2da1d9f96d2d572a8d",
    "ce9f73f7f5194cbcb138c157e47f7964",
)
V11_REQUEST_IDS = (
    "332d8d4192e247859d73810dd4ef5bcb",
    "41092897ba884ef39e015cefc451de39",
    "48f2afd41cf946fb9671871e61402f3d",
    "a8d35183b8b84d89b9d95103cf7c60d8",
    "f3f14c97691d494bae9e9834b112252b",
    "8238ffbc8b0f457f808ce3cef0e20eca",
)
V9_SUPERSEDED_REQUEST_IDS = (
    "99c2fcc3c6e84c7c99408023e5dc33a4",
    "5c7e14b9ec54493eab0c07b65b9ea060",
    "66beb32c09804696894ad948f6af1a03",
    "34d8eebb21814cd68968940bbe8eb54c",
    "227de96509e445f1acdbb70f531dee73",
    "701c043879b0481180926b890ae1571d",
)
V8_SUPERSEDED_REQUEST_IDS = (
    "c2f3383ea7ab4702bb9107c010afa826",
    "0a1f61046a4e4a8a8857f191b60b87f6",
    "dc3c9442dfd547dda5cd86854a541253",
    "8142bd76fe494f34886f5b0f8124efd0",
    "570f8fba9c9544a9989ae71400688794",
    "1dc0401d62b04e959d6cb9424db17a54",
)
V7_REJECTED_REQUEST_IDS = (
    "43fd3902318c41bab21aa0ea851bbbb3",
    "f8586b30ae12448498bfe104b3776f01",
    "06a261a4e43549acb33449d6ef455644",
    "435ffa6e24b84371ba9be0f41128c22e",
    "535cb95402874b5b8dfe32a912db20e4",
    "a024744a6f674ebba9a7d6028434e1d8",
)
V6_REJECTED_REQUEST_IDS = (
    "31973767658f492ea0b7f376d59399df",
    "ec8740b65b9e45c5a803a718372b91c4",
    "d07ea2cee1224e26bc8c1aa0c5215e64",
    "0193fe79ba67489aa63af05cf6e23780",
    "eb4ac0c0d9cf46a7be4be22a59faffa5",
    "fdf28a8c7eda4d6faf6cb359561042a4",
)
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
FUNCTIONAL_WAVE_SHARD_IDS = tuple(f"P{index:02d}" for index in range(1, 5))
FUNCTIONAL_WAVE_SHARD_AUTHORITIES = {
    "P01": {
        "node_count": 1,
        "node_ids_sha256": (
            "9a2ff93c333465e9815679ef6e9f971cbee782f2b833934c765447867a5a5704"
        ),
    },
    "P02": {
        "node_count": 362,
        "node_ids_sha256": (
            "c6d005d0e69b2be5bbe1b197c71f22af598081ec2a1fc9e31cf217f7b5ef37ce"
        ),
    },
    "P03": {
        "node_count": 361,
        "node_ids_sha256": (
            "c7dad7210a3bebcdd7a497db946b574e05c5d2a1694fa9426ee7b62da271b8b3"
        ),
    },
    "P04": {
        "node_count": 312,
        "node_ids_sha256": (
            "38cb6d54b4c0e163308cdbcde38eff5a8372cc5a3c3702b1c0edbdf173b2118a"
        ),
    },
}
FUNCTIONAL_WAVE_TAIL_NODE = (
    "tests/test_fe_solver_nonlinear_static.py::"
    "test_pure_bending_reaches_plastic_moment"
)
FUNCTIONAL_WAVE_COLLECTION_ARTIFACT = {
    "bytes": 116046,
    "sha256": "244132e6294f3dc37f5bf865bd800c7402d9ff6b3300af670ca954ad24bb5c15",
}
FUNCTIONAL_WAVE_ROUTING = {
    "aggregate_filename": "functional-wave-aggregate.json",
    "archive_filename": "functional-wave-source.tar",
    "directory_name": "functional-wave",
    "raw_diagnostics_filename": "functional-wave-raw-diagnostics.json",
    "shard_directory_prefix": "shard-",
    "source_directory_name": "source",
}
FUNCTIONAL_WAVE_SHARD_SUBDIRECTORIES = (
    "cwd",
    "basetemp",
    "python_cache",
    "numba_cache",
    "temp",
    "reports",
    "logs",
)
TIMEOUT_DISPOSITIONS = {
    "INTERRUPTED_TREE_TERMINATED",
    "INTERRUPTED_TREE_TERMINATION_FAILED",
    "NORMAL_EXIT",
    "START_FAILED",
    "TIMEOUT_TREE_TERMINATED",
    "TIMEOUT_TREE_TERMINATION_FAILED",
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
    if not path.is_file() or path.is_symlink() or is_reparse_point(path):
        raise EvidenceError(f"JSON input must be a regular non-reparse file: {path}")
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


def is_reparse_point(path: Path) -> bool:
    """Return true for Windows reparse points, including non-symlink junctions."""

    try:
        attributes = path.lstat().st_file_attributes
    except (AttributeError, FileNotFoundError, OSError):
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def require_regular_file(path: Path, *, nonempty: bool = False) -> Path:
    if path.is_symlink() or is_reparse_point(path) or not path.is_file():
        raise EvidenceError(f"artifact must be a regular non-reparse file: {path}")
    if nonempty and path.stat().st_size <= 0:
        raise EvidenceError(f"artifact must be nonempty: {path}")
    return path


def require_package_process_result_identity(
    *, contract: Mapping[str, Any]
) -> bytes:
    """Return package-result bytes only when they are the package worker stdout."""

    root = output_root(contract)
    if not root.is_dir() or root.is_symlink() or is_reparse_point(root):
        raise EvidenceError("package output root is noncanonical")
    result_path = require_regular_file(
        root / contract["package"]["result_filename"], nonempty=True
    )
    stdout_path = require_regular_file(
        process_output_directory(contract, "common.package.1") / "stdout.txt",
        nonempty=True,
    )
    raw = result_path.read_bytes()
    if stdout_path.read_bytes() != raw:
        raise EvidenceError(
            "package result differs from the validated package-process stdout"
        )
    return raw


def optional_regular_file_record(
    path: Path, *, filename: bool = False
) -> dict[str, Any] | None:
    """Return an exact record for an optional canonical, non-symlink file."""

    if path.is_symlink() or is_reparse_point(path):
        raise EvidenceError(f"canonical artifact may not be a reparse point: {path}")
    if not path.exists():
        return None
    require_regular_file(path)
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


def validate_eol_bound_input(
    path: Path,
    record: Any,
    *,
    expected_relative_path: str,
    location: str,
) -> dict[str, Any]:
    """Validate one text input by canonical LF content and exact checkout bytes."""

    bound = _exact_keys(
        record,
        {"canonical_lf", "path", "working_tree_identities"},
        location,
    )
    if bound["path"] != expected_relative_path:
        raise EvidenceError(f"{location}.path mismatch")
    canonical = _validate_hash_record(
        bound["canonical_lf"], f"{location}.canonical_lf"
    )
    identities = bound["working_tree_identities"]
    if not isinstance(identities, list) or len(identities) != 2:
        raise EvidenceError(f"{location}.working_tree_identities must contain LF and CRLF")
    expected_endings = ["LF", "CRLF"]
    validated_identities: list[dict[str, Any]] = []
    for index, (identity, line_endings) in enumerate(
        zip(identities, expected_endings, strict=True)
    ):
        item = _exact_keys(
            identity,
            {"bytes", "line_endings", "sha256"},
            f"{location}.working_tree_identities[{index}]",
        )
        if item["line_endings"] != line_endings:
            raise EvidenceError(f"{location} working-tree identity order mismatch")
        validated_identities.append(
            {
                **_validate_hash_record(
                    {"bytes": item["bytes"], "sha256": item["sha256"]},
                    f"{location}.working_tree_identities[{index}]",
                ),
                "line_endings": line_endings,
            }
        )
    if validated_identities[0] != {**canonical, "line_endings": "LF"}:
        raise EvidenceError(f"{location} LF identity must equal canonical LF")

    require_regular_file(path, nonempty=True)
    raw = path.read_bytes()
    observed = {"bytes": len(raw), "sha256": sha256_bytes(raw)}
    if observed not in [
        {"bytes": item["bytes"], "sha256": item["sha256"]}
        for item in validated_identities
    ]:
        raise EvidenceError(f"{location} working-tree identity mismatch")
    normalized = raw.replace(b"\r\n", b"\n")
    if b"\r" in normalized or {
        "bytes": len(normalized),
        "sha256": sha256_bytes(normalized),
    } != canonical:
        raise EvidenceError(f"{location} is not exact LF/CRLF-equivalent content")
    return bound


def _require_timestamp(value: Any, location: str) -> str:
    text = _require_string(value, location)
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceError(f"{location} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise EvidenceError(f"{location} must include a UTC offset")
    return text


def _require_basename(value: Any, location: str) -> str:
    name = _require_string(value, location)
    if name in {".", ".."} or "/" in name or "\\" in name or Path(name).name != name:
        raise EvidenceError(f"{location} must be a safe basename")
    return name


def _require_ordered_unique_strings(
    value: Any,
    location: str,
    *,
    expected_count: int | None = None,
) -> list[str]:
    if not isinstance(value, list):
        raise EvidenceError(f"{location} must be an array")
    result = [
        _require_string(item, f"{location}[{index}]")
        for index, item in enumerate(value)
    ]
    if expected_count is not None and len(result) != expected_count:
        raise EvidenceError(f"{location} must contain exactly {expected_count} entries")
    if len(set(result)) != len(result):
        raise EvidenceError(f"{location} contains duplicate entries")
    return result


def _require_canonical_list_hash(
    values: list[str], value: Any, location: str
) -> str:
    observed = _require_hash(value, location)
    expected = sha256_bytes(canonical_json_bytes(values))
    if observed != expected:
        raise EvidenceError(f"{location} does not bind the canonical ordered list")
    return observed


def _validate_timeout_policy(value: Any, location: str) -> dict[str, Any]:
    policy = _exact_keys(
        value,
        {
            "automatic_retry",
            "evidence_reserve_seconds",
            "scope",
            "termination_grace_seconds",
            "timeout_exit_code",
            "wall_limit_seconds",
            "windows_job",
            "windows_termination",
        },
        location,
    )
    if policy["automatic_retry"] is not False:
        raise EvidenceError(f"{location}.automatic_retry must be false")
    if (
        _require_int(
            policy["evidence_reserve_seconds"],
            f"{location}.evidence_reserve_seconds",
            minimum=1,
        )
        != 20
    ):
        raise EvidenceError(f"{location}.evidence_reserve_seconds must be 20")
    if (
        _require_int(
            policy["wall_limit_seconds"],
            f"{location}.wall_limit_seconds",
            minimum=1,
        )
        != 1200
    ):
        raise EvidenceError(f"{location}.wall_limit_seconds must be 1200")
    if _require_int(policy["timeout_exit_code"], f"{location}.timeout_exit_code") != 124:
        raise EvidenceError(f"{location}.timeout_exit_code must be 124")
    if (
        _require_int(
            policy["termination_grace_seconds"],
            f"{location}.termination_grace_seconds",
            minimum=1,
        )
        != 10
    ):
        raise EvidenceError(f"{location}.termination_grace_seconds must be 10")
    if policy["scope"] != "COMPLETE_RESOURCE_INVOCATION_AND_CHILD_PROCESS_TREE":
        raise EvidenceError(f"{location}.scope mismatch")
    if policy["windows_job"] != {
        "assignment": "CREATE_SUSPENDED_ASSIGN_RESUME",
        "limit": "JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE",
        "watchdog_termination_start_seconds": 1190,
    }:
        raise EvidenceError(f"{location}.windows_job mismatch")
    windows = _exact_keys(
        policy["windows_termination"],
        {"arguments", "bytes", "path", "sha256"},
        f"{location}.windows_termination",
    )
    expected_tool = {
        "bytes": 118784,
        "path": r"C:\Windows\System32\taskkill.exe",
        "sha256": "1249717315fc8f4d2df17d5db9da0444795fdb9fb83dfb1f763c3f39282244f7",
    }
    if {key: windows[key] for key in expected_tool} != expected_tool:
        raise EvidenceError(f"{location}.windows_termination identity mismatch")
    _validate_hash_record(
        {"bytes": windows["bytes"], "sha256": windows["sha256"]},
        f"{location}.windows_termination",
    )
    if windows["arguments"] != ["/PID", "{pid}", "/T", "/F"]:
        raise EvidenceError(f"{location}.windows_termination.arguments mismatch")
    return policy


def _validate_cycle_wall_policy(value: Any, location: str) -> dict[str, Any]:
    """Validate the single monotonic deadline shared by a complete cycle."""

    policy = _exact_keys(
        value,
        {
            "absolute_wall_limit_seconds",
            "clock",
            "cumulative_deadlines_seconds",
            "final_evidence_reserve_seconds",
            "scope",
        },
        location,
    )
    deadlines = _exact_keys(
        policy["cumulative_deadlines_seconds"],
        {"anyfem", "functional", "performance"},
        f"{location}.cumulative_deadlines_seconds",
    )
    expected = {
        "absolute_wall_limit_seconds": 1200,
        "clock": "time.monotonic",
        "cumulative_deadlines_seconds": {
            "anyfem": 990,
            "functional": 900,
            "performance": 1110,
        },
        "final_evidence_reserve_seconds": 90,
        "scope": "COMPLETE_CYCLE_AND_ALL_CHILD_PROCESS_TREES",
    }
    if policy != expected:
        raise EvidenceError(f"{location} mismatch")
    if not (
        0
        < _require_int(deadlines["functional"], f"{location}.functional")
        < _require_int(deadlines["anyfem"], f"{location}.anyfem")
        < _require_int(deadlines["performance"], f"{location}.performance")
        < _require_int(
            policy["absolute_wall_limit_seconds"],
            f"{location}.absolute_wall_limit_seconds",
        )
    ):
        raise EvidenceError(f"{location} cumulative deadlines are not strictly ordered")
    if (
        deadlines["performance"] + policy["final_evidence_reserve_seconds"]
        != policy["absolute_wall_limit_seconds"]
    ):
        raise EvidenceError(f"{location} final evidence reserve does not close the wall limit")
    return policy


def _validate_request_execution_policy(
    value: Any, location: str
) -> dict[str, Any]:
    """Require current one-shot requests to run only through the cycle coordinator."""

    policy = _exact_keys(
        value,
        {
            "current_request_execution_mode",
            "idempotent_publication_recovery",
            "scope",
            "standalone_resource_command",
        },
        location,
    )
    expected = {
        "current_request_execution_mode": "FORMAL_CYCLE_COORDINATOR_ONLY",
        "idempotent_publication_recovery": "FINALIZE_COMMAND_ONLY",
        "scope": "ALL_SIX_CURRENT_REQUEST_IDS",
        "standalone_resource_command": "FORBIDDEN_FOR_CURRENT_REQUEST_IDS",
    }
    if policy != expected:
        raise EvidenceError(f"{location} mismatch")
    return policy


def _validate_gate_git_invocation_policy(
    value: Any, location: str
) -> dict[str, Any]:
    """Bind gate Git probes to the validator's hardened Windows prefix."""

    policy = _exact_keys(
        value,
        {"environment", "launcher", "prefix_after_launcher", "scope"},
        location,
    )
    expected = {
        "environment": "VALIDATOR_EQUIVALENT_SANITIZED_GIT_ENVIRONMENT",
        "launcher": "FROZEN_EXECUTION_GIT",
        "prefix_after_launcher": [
            "--no-replace-objects",
            "-c",
            "safe.directory={repository}",
            "-c",
            "core.autocrlf=true",
            "-c",
            "core.attributesFile=NUL",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.quotepath=false",
            "-c",
            "core.untrackedCache=false",
            "-c",
            "status.showUntrackedFiles=all",
            "-C",
            "{repository}",
        ],
        "scope": "ALL_GATE_GIT_SUBPROCESSES",
    }
    if policy != expected:
        raise EvidenceError(f"{location} mismatch")
    return policy


def _validate_ci_policy(
    value: Any,
    contract: Mapping[str, Any],
    location: str,
) -> dict[str, Any]:
    """Require the bounded CI lane to retain every frozen quick/functional/additive input."""

    policy = _exact_keys(
        value,
        {
            "coordinator_wall_limit_seconds",
            "extent",
            "required_lanes",
            "smoke_or_representative_only_forbidden",
        },
        location,
    )
    if policy != {
        "coordinator_wall_limit_seconds": 1200,
        "extent": "COMPLETE_FROZEN_INVENTORIES",
        "required_lanes": ["quick", "functional", "additive"],
        "smoke_or_representative_only_forbidden": True,
    }:
        raise EvidenceError(f"{location} mismatch")
    inventories = _exact_keys(
        contract["lane_inventories"],
        {
            "additive",
            "anyfem",
            "extended",
            "functional",
            "package",
            "performance",
            "quick",
        },
        "$contract.lane_inventories",
    )
    expected_rows = {
        "quick": {
            "count": 7,
            "execution": "COMMON_NONRESOURCE_PREFLIGHT",
            "sha256": (
                "6798a1e7bf8d796c210b60cb2600ed0a161545ea9f239a3720975ae591800304"
            ),
        },
        "functional": {
            "count": 85,
            "execution": "BOUNDED_PARALLEL_WAVE_4_SHARDS_MAX_4",
            "sha256": (
                "eb6228e05649d158d29c63725ca19a1a8f35cfcea71c6b1ce35d27215e9b6b6c"
            ),
        },
        "additive": {
            "count": 43,
            "execution": "THREE_OR_FEWER_PARALLEL_PARTITIONS",
            "sha256": (
                "a304eaea654c4ad779cc067cef594f13d3c617a835a35a1d6ab31409bc59593a"
            ),
        },
    }
    for lane, expected in expected_rows.items():
        row = _exact_keys(
            inventories[lane],
            {"count", "execution", "sha256"},
            f"$contract.lane_inventories.{lane}",
        )
        if row != expected:
            raise EvidenceError(f"{location} does not bind the complete {lane} inventory")
    if inventories["functional"]["count"] != contract["functional_wave"]["manifest"][
        "module_count"
    ]:
        raise EvidenceError(f"{location} functional extent differs from its manifest")
    return policy


def timeout_termination_tool(contract: Mapping[str, Any]) -> Path:
    """Return the hash-bound taskkill executable after checking host identity."""

    policy = _validate_timeout_policy(
        contract["execution"]["timeout_policy"],
        "$contract.execution.timeout_policy",
    )
    record = policy["windows_termination"]
    path = require_regular_file(Path(record["path"]), nonempty=True)
    if file_hash_record(path) != {
        "bytes": record["bytes"],
        "sha256": record["sha256"],
    }:
        raise EvidenceError("taskkill executable identity mismatch")
    return path


def _validate_artifact_routing(value: Any, location: str) -> dict[str, Any]:
    routing = _exact_keys(value, set(FUNCTIONAL_WAVE_ROUTING), location)
    for key, expected in FUNCTIONAL_WAVE_ROUTING.items():
        observed = _require_string(routing[key], f"{location}.{key}")
        if observed != expected:
            raise EvidenceError(f"{location}.{key} mismatch")
    for key in (
        "aggregate_filename",
        "archive_filename",
        "directory_name",
        "raw_diagnostics_filename",
        "source_directory_name",
    ):
        _require_basename(routing[key], f"{location}.{key}")
    prefix = routing["shard_directory_prefix"]
    if prefix in {".", ".."} or "/" in prefix or "\\" in prefix:
        raise EvidenceError(f"{location}.shard_directory_prefix is unsafe")
    routed_names = {
        routing["archive_filename"],
        routing["source_directory_name"],
        routing["aggregate_filename"],
        routing["raw_diagnostics_filename"],
        *(f"{prefix}{shard_id}" for shard_id in FUNCTIONAL_WAVE_SHARD_IDS),
    }
    if len(routed_names) != 8:
        raise EvidenceError(f"{location} routes collide")
    return routing


def _validate_functional_wave(value: Any, location: str) -> dict[str, Any]:
    wave = _exact_keys(
        value,
        {"aggregate", "execution", "manifest", "schema", "source"},
        location,
    )
    if wave["schema"] != FUNCTIONAL_WAVE_SCHEMA:
        raise EvidenceError(f"{location}.schema mismatch")

    source = _exact_keys(
        wave["source"],
        {
            "archive_filename",
            "commit_role",
            "file_graph_filename",
            "file_graph_schema",
            "tree_role",
        },
        f"{location}.source",
    )
    expected_source = {
        "archive_filename": "functional-wave-source.tar",
        "commit_role": "EXECUTION_AUTHORIZATION_COMMIT",
        "file_graph_filename": "functional-wave-source-file-graph.json",
        "file_graph_schema": FUNCTIONAL_WAVE_FILE_GRAPH_SCHEMA,
        "tree_role": "EXECUTION_AUTHORIZATION_TREE",
    }
    if source != expected_source:
        raise EvidenceError(f"{location}.source mismatch")
    _require_basename(source["archive_filename"], f"{location}.source.archive_filename")
    _require_basename(
        source["file_graph_filename"], f"{location}.source.file_graph_filename"
    )

    manifest = _exact_keys(
        wave["manifest"],
        {
            "collection_artifact",
            "full_node_ids",
            "full_node_ids_sha256",
            "module_count",
            "modules",
            "modules_sha256",
            "node_count",
            "shards",
        },
        f"{location}.manifest",
    )
    if _require_int(manifest["module_count"], f"{location}.manifest.module_count") != 85:
        raise EvidenceError(f"{location}.manifest.module_count must be 85")
    modules = _require_ordered_unique_strings(
        manifest["modules"],
        f"{location}.manifest.modules",
        expected_count=85,
    )
    if any(
        not module.startswith("tests/test_")
        or not module.endswith(".py")
        or "\\" in module
        for module in modules
    ):
        raise EvidenceError(f"{location}.manifest.modules are malformed")
    _require_canonical_list_hash(
        modules,
        manifest["modules_sha256"],
        f"{location}.manifest.modules_sha256",
    )
    if _require_int(manifest["node_count"], f"{location}.manifest.node_count") != 1036:
        raise EvidenceError(f"{location}.manifest.node_count must be 1036")
    full_node_ids = _require_ordered_unique_strings(
        manifest["full_node_ids"],
        f"{location}.manifest.full_node_ids",
        expected_count=1036,
    )
    for index, node_id in enumerate(full_node_ids):
        if (
            "::" not in node_id
            or "\\" in node_id
            or not node_id.split("::", 1)[0].endswith(".py")
        ):
            raise EvidenceError(
                f"{location}.manifest.full_node_ids[{index}] is not a pytest node ID"
            )
    _require_canonical_list_hash(
        full_node_ids,
        manifest["full_node_ids_sha256"],
        f"{location}.manifest.full_node_ids_sha256",
    )
    derived_modules = list(dict.fromkeys(node_id.split("::", 1)[0] for node_id in full_node_ids))
    if modules != derived_modules:
        raise EvidenceError(f"{location}.manifest.modules do not match node collection order")
    collection_artifact = _validate_hash_record(
        manifest["collection_artifact"],
        f"{location}.manifest.collection_artifact",
    )
    if collection_artifact != FUNCTIONAL_WAVE_COLLECTION_ARTIFACT:
        raise EvidenceError(f"{location}.manifest.collection_artifact mismatch")

    shards = manifest["shards"]
    if not isinstance(shards, list) or len(shards) != len(FUNCTIONAL_WAVE_SHARD_IDS):
        raise EvidenceError(f"{location}.manifest.shards must contain P01 through P04")
    assigned: list[str] = []
    global_nodes = set(full_node_ids)
    for index, expected_shard_id in enumerate(FUNCTIONAL_WAVE_SHARD_IDS):
        shard_location = f"{location}.manifest.shards[{index}]"
        shard = _exact_keys(
            shards[index],
            {"node_count", "node_ids", "node_ids_sha256", "shard_id"},
            shard_location,
        )
        if shard["shard_id"] != expected_shard_id:
            raise EvidenceError(f"{shard_location}.shard_id mismatch")
        node_ids = _require_ordered_unique_strings(
            shard["node_ids"], f"{shard_location}.node_ids"
        )
        if not node_ids:
            raise EvidenceError(f"{shard_location}.node_ids may not be empty")
        if any(node_id not in global_nodes for node_id in node_ids):
            raise EvidenceError(f"{shard_location}.node_ids contain unknown nodes")
        if _require_int(shard["node_count"], f"{shard_location}.node_count") != len(node_ids):
            raise EvidenceError(f"{shard_location}.node_count mismatch")
        node_ids_sha256 = _require_canonical_list_hash(
            node_ids,
            shard["node_ids_sha256"],
            f"{shard_location}.node_ids_sha256",
        )
        expected_authority = FUNCTIONAL_WAVE_SHARD_AUTHORITIES[expected_shard_id]
        if {
            "node_count": len(node_ids),
            "node_ids_sha256": node_ids_sha256,
        } != expected_authority:
            raise EvidenceError(f"{shard_location} differs from the frozen balanced shard")
        assigned.extend(node_ids)
    if len(assigned) != len(set(assigned)):
        raise EvidenceError(f"{location}.manifest.shards overlap")
    if set(assigned) != set(full_node_ids):
        raise EvidenceError(f"{location}.manifest.shards omit or add node IDs")
    if shards[0]["node_ids"] != [FUNCTIONAL_WAVE_TAIL_NODE]:
        raise EvidenceError(f"{location}.manifest.shards[0] must isolate the tail-risk node")

    execution = _exact_keys(
        wave["execution"],
        {
            "artifact_routing",
            "automatic_retry",
            "environment",
            "internal_deadline_seconds",
            "max_workers",
            "numerical_library_threads",
            "raw_observability",
            "selector_safety",
            "source_mode",
            "source_status_must_match",
            "unproven_tree_action",
        },
        f"{location}.execution",
    )
    if _require_int(execution["max_workers"], f"{location}.execution.max_workers", minimum=1) != 4:
        raise EvidenceError(f"{location}.execution.max_workers must be 4")
    if (
        _require_int(
            execution["numerical_library_threads"],
            f"{location}.execution.numerical_library_threads",
            minimum=1,
        )
        != 1
    ):
        raise EvidenceError(f"{location}.execution.numerical_library_threads must be 1")
    if execution["automatic_retry"] is not False:
        raise EvidenceError(f"{location}.execution.automatic_retry must be false")
    if (
        _require_int(
            execution["internal_deadline_seconds"],
            f"{location}.execution.internal_deadline_seconds",
            minimum=1,
        )
        != 830
    ):
        raise EvidenceError(f"{location}.execution.internal_deadline_seconds must be 830")
    environment = _exact_keys(
        execution["environment"],
        {"NUMBA_NUM_THREADS", "scope"},
        f"{location}.execution.environment",
    )
    if environment != {
        "NUMBA_NUM_THREADS": "1",
        "scope": "FUNCTIONAL_SHARDS_ONLY",
    }:
        raise EvidenceError(f"{location}.execution.environment mismatch")
    selector_safety = _exact_keys(
        execution["selector_safety"],
        {
            "extra_nodes",
            "full_module_selector",
            "missing_nodes",
            "split_module_selector",
        },
        f"{location}.execution.selector_safety",
    )
    if selector_safety != {
        "extra_nodes": "REJECT",
        "full_module_selector": (
            "ONLY_WHEN_ALL_COLLECTED_MODULE_NODES_ARE_SHARD_OWNED"
        ),
        "missing_nodes": "REJECT",
        "split_module_selector": "EXACT_NODE_IDS_ONLY",
    }:
        raise EvidenceError(f"{location}.execution.selector_safety mismatch")
    raw_observability = _exact_keys(
        execution["raw_observability"],
        {"canonical_timings", "lifecycle_progress", "pytest_durations"},
        f"{location}.execution.raw_observability",
    )
    if raw_observability != {
        "canonical_timings": False,
        "lifecycle_progress": True,
        "pytest_durations": True,
    }:
        raise EvidenceError(f"{location}.execution.raw_observability mismatch")
    if execution["source_mode"] != "GIT_ARCHIVE_HEAD":
        raise EvidenceError(f"{location}.execution.source_mode mismatch")
    if execution["source_status_must_match"] is not True:
        raise EvidenceError(f"{location}.execution.source_status_must_match must be true")
    if (
        execution["unproven_tree_action"]
        != "WAIT_FOR_OUTER_RESOURCE_TREE_TERMINATION"
    ):
        raise EvidenceError(f"{location}.execution.unproven_tree_action mismatch")
    routing = _validate_artifact_routing(
        execution["artifact_routing"], f"{location}.execution.artifact_routing"
    )
    if routing["archive_filename"] != source["archive_filename"]:
        raise EvidenceError(f"{location} source/archive routing mismatch")

    aggregate = _exact_keys(
        wave["aggregate"],
        {"blocked_terminal", "schema", "success_terminal"},
        f"{location}.aggregate",
    )
    expected_aggregate = {
        "blocked_terminal": "BLOCKED_E4_PL_S3_Q4_FUNCTIONAL_WAVE",
        "schema": FUNCTIONAL_WAVE_AGGREGATE_SCHEMA,
        "success_terminal": "PASS_E4_PL_S3_Q4_FUNCTIONAL_WAVE",
    }
    if aggregate != expected_aggregate:
        raise EvidenceError(f"{location}.aggregate mismatch")
    return wave


def validate_functional_wave_contract(
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate and return the exact bounded functional-wave authority."""

    return _validate_functional_wave(
        contract["functional_wave"], "$contract.functional_wave"
    )


def functional_wave_artifact_paths(
    contract: Mapping[str, Any], cycle: int
) -> dict[str, Any]:
    """Return deterministic external-only routes for one functional-wave cycle."""

    if not isinstance(cycle, int) or isinstance(cycle, bool) or cycle not in {1, 2}:
        raise EvidenceError("functional-wave cycle must be 1 or 2")
    wave = validate_functional_wave_contract(contract)
    routing = wave["execution"]["artifact_routing"]
    external_root = output_root(contract).resolve()
    cycle_root = (
        external_root / routing["directory_name"] / f"cycle-{cycle}"
    ).resolve()
    if not cycle_root.is_relative_to(external_root):
        raise EvidenceError("functional-wave cycle root escapes the external output root")
    paths: dict[str, Any] = {
        "aggregate": cycle_root / routing["aggregate_filename"],
        "archive": cycle_root / routing["archive_filename"],
        "cycle_root": cycle_root,
        "raw_diagnostics": cycle_root / routing["raw_diagnostics_filename"],
        "source": cycle_root / routing["source_directory_name"],
        "shards": {
            shard_id: cycle_root
            / f"{routing['shard_directory_prefix']}{shard_id}"
            for shard_id in FUNCTIONAL_WAVE_SHARD_IDS
        },
    }
    routed = [
        paths["aggregate"],
        paths["archive"],
        paths["raw_diagnostics"],
        paths["source"],
        *paths["shards"].values(),
    ]
    if len({str(path).casefold() for path in routed}) != len(routed):
        raise EvidenceError("functional-wave artifact routes collide")
    if any(not path.resolve().is_relative_to(cycle_root) for path in routed):
        raise EvidenceError("functional-wave artifact route escapes its cycle root")
    return paths


def functional_wave_shard_artifact_paths(
    contract: Mapping[str, Any], cycle: int, shard_id: str
) -> dict[str, Path]:
    """Return the isolated directories reserved for one functional shard."""

    if shard_id not in FUNCTIONAL_WAVE_SHARD_IDS:
        raise EvidenceError("functional-wave shard ID must be P01 through P04")
    paths = functional_wave_artifact_paths(contract, cycle)
    shard_root = paths["shards"][shard_id]
    routed = {
        "root": shard_root,
        **{
            name: shard_root / name
            for name in FUNCTIONAL_WAVE_SHARD_SUBDIRECTORIES
        },
    }
    if len({str(path).casefold() for path in routed.values()}) != len(routed):
        raise EvidenceError("functional-wave shard routes collide")
    if any(not path.resolve().is_relative_to(shard_root.resolve()) for path in routed.values()):
        raise EvidenceError("functional-wave shard route escapes its root")
    return routed


def validate_functional_wave_artifact_state(
    contract: Mapping[str, Any],
    cycle: int,
    *,
    require_fresh: bool,
) -> dict[str, Any]:
    """Reject repository-local, colliding, or reparse-point artifact routing."""

    paths = functional_wave_artifact_paths(contract, cycle)
    external_root = output_root(contract)
    repository_root = ROOT.resolve()
    resolved_external = external_root.resolve()
    if resolved_external == repository_root or resolved_external.is_relative_to(
        repository_root
    ):
        raise EvidenceError("functional-wave artifacts may not be repository-local")
    all_paths: list[Path] = [
        paths["cycle_root"],
        paths["aggregate"],
        paths["archive"],
        paths["raw_diagnostics"],
        paths["source"],
    ]
    for shard_id in FUNCTIONAL_WAVE_SHARD_IDS:
        all_paths.extend(
            functional_wave_shard_artifact_paths(
                contract, cycle, shard_id
            ).values()
        )
    if len({str(path.resolve()).casefold() for path in all_paths}) != len(all_paths):
        raise EvidenceError("functional-wave artifact paths are not distinct")
    for path in [external_root, *all_paths]:
        if path.exists() and (path.is_symlink() or is_reparse_point(path)):
            raise EvidenceError(f"functional-wave artifact route is a reparse point: {path}")
    if require_fresh and paths["cycle_root"].exists():
        raise EvidenceError("functional-wave cycle output already exists")
    return paths


def _functional_wave_extent_records(
    cycle_root: Path, *, excluded_paths: Iterable[str]
) -> list[dict[str, Any]]:
    excluded = set(excluded_paths)
    records: list[dict[str, Any]] = []
    try:
        descendants = sorted(
            cycle_root.rglob("*"),
            key=lambda path: path.relative_to(cycle_root).as_posix(),
        )
    except OSError as exc:
        raise EvidenceError("functional-wave extent cannot be enumerated") from exc
    for path in descendants:
        if path.is_symlink() or is_reparse_point(path):
            raise EvidenceError(f"functional-wave extent contains a reparse point: {path}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise EvidenceError(f"functional-wave extent contains a special file: {path}")
        relative = path.relative_to(cycle_root).as_posix()
        if relative in excluded:
            continue
        records.append({**file_hash_record(path), "path": relative})
    return records


def _validate_functional_wave_extent(
    value: Any,
    *,
    cycle_root: Path,
    excluded_paths: Iterable[str],
    location: str,
) -> dict[str, Any]:
    excluded = set(excluded_paths)
    extent = _exact_keys(value, {"files", "records", "sha256"}, location)
    records = extent["records"]
    if not isinstance(records, list):
        raise EvidenceError(f"{location}.records must be an array")
    validated_records: list[dict[str, Any]] = []
    prior_path: str | None = None
    for index, raw_record in enumerate(records):
        record_location = f"{location}.records[{index}]"
        record = _exact_keys(
            raw_record, {"bytes", "path", "sha256"}, record_location
        )
        _validate_hash_record(
            {"bytes": record["bytes"], "sha256": record["sha256"]},
            record_location,
        )
        relative_text = _require_string(record["path"], f"{record_location}.path")
        relative = PurePosixPath(relative_text)
        if (
            relative.is_absolute()
            or relative_text != relative.as_posix()
            or not relative.parts
            or any(part in {"", ".", ".."} for part in relative.parts)
            or "\\" in relative_text
            or relative_text in excluded
        ):
            raise EvidenceError(f"{record_location}.path is unsafe")
        if prior_path is not None and relative_text <= prior_path:
            raise EvidenceError(f"{location}.records are not uniquely sorted")
        prior_path = relative_text
        validated_records.append(dict(record))
    if _require_int(extent["files"], f"{location}.files") != len(
        validated_records
    ):
        raise EvidenceError(f"{location}.files mismatch")
    expected_sha256 = sha256_bytes(canonical_json_bytes(validated_records))
    if _require_hash(extent["sha256"], f"{location}.sha256") != expected_sha256:
        raise EvidenceError(f"{location}.sha256 mismatch")
    observed_records = _functional_wave_extent_records(
        cycle_root, excluded_paths=excluded
    )
    if validated_records != observed_records:
        raise EvidenceError("functional-wave diagnostic extent differs from disk")
    return extent


def _validate_functional_file_graph(
    path: Path,
    *,
    source_root: Path,
    schema: str,
) -> dict[str, Any]:
    raw = require_regular_file(path, nonempty=True).read_bytes()
    graph = strict_json_loads(raw)
    if raw != canonical_json_bytes(graph):
        raise EvidenceError("functional-wave file graph is noncanonical")
    graph = _exact_keys(graph, {"files", "schema", "summary"}, "$file_graph")
    if graph["schema"] != schema:
        raise EvidenceError("functional-wave file-graph schema mismatch")
    files = graph["files"]
    if not isinstance(files, list) or not files:
        raise EvidenceError("functional-wave file graph is empty")
    validated: list[dict[str, Any]] = []
    prior_path: str | None = None
    for index, raw_record in enumerate(files):
        location = f"$file_graph.files[{index}]"
        record = _exact_keys(raw_record, {"bytes", "path", "sha256"}, location)
        _validate_hash_record(
            {"bytes": record["bytes"], "sha256": record["sha256"]}, location
        )
        relative_text = _require_string(record["path"], f"{location}.path")
        relative = PurePosixPath(relative_text)
        if (
            relative.is_absolute()
            or relative_text != relative.as_posix()
            or any(part in {"", ".", ".."} for part in relative.parts)
            or "\\" in relative_text
        ):
            raise EvidenceError(f"{location}.path is unsafe")
        if prior_path is not None and relative_text <= prior_path:
            raise EvidenceError("functional-wave file graph is not uniquely sorted")
        prior_path = relative_text
        validated.append(dict(record))
    summary = _exact_keys(graph["summary"], {"files", "sha256"}, "$file_graph.summary")
    if summary != {
        "files": len(validated),
        "sha256": sha256_bytes(canonical_json_bytes(validated)),
    }:
        raise EvidenceError("functional-wave file-graph summary mismatch")
    observed = _functional_wave_extent_records(
        source_root, excluded_paths=()
    )
    if validated != observed:
        raise EvidenceError("functional-wave source graph differs from disk")
    return graph


def _functional_shard_selectors(
    shard_nodes: list[str], full_nodes: list[str]
) -> tuple[list[str], dict[str, Any]]:
    """Recompute the only selectors permitted by the frozen split-module policy."""

    full_by_module: dict[str, list[str]] = {}
    for node_id in full_nodes:
        full_by_module.setdefault(node_id.partition("::")[0], []).append(node_id)
    shard_by_module: dict[str, list[str]] = {}
    for node_id in shard_nodes:
        shard_by_module.setdefault(node_id.partition("::")[0], []).append(node_id)
    selectors: list[str] = []
    full_module_count = 0
    exact_node_count = 0
    for module, nodes in shard_by_module.items():
        if nodes == full_by_module.get(module):
            selectors.append(module)
            full_module_count += 1
        else:
            selectors.extend(nodes)
            exact_node_count += len(nodes)
    expanded: list[str] = []
    for selector in selectors:
        if "::" in selector:
            expanded.append(selector)
        else:
            expanded.extend(full_by_module[selector])
    if expanded != shard_nodes:
        raise EvidenceError("functional shard selectors change frozen node order")
    return selectors, {
        "exact_node_count": exact_node_count,
        "full_module_count": full_module_count,
        "selector_count": len(selectors),
        "selectors_sha256": sha256_bytes(canonical_json_bytes(selectors)),
    }


def _validate_functional_progress(
    path: Path,
    *,
    authority: Mapping[str, Any],
    raw_shard: Mapping[str, Any],
    location: str,
) -> list[dict[str, Any]]:
    """Validate one noncanonical NDJSON timing stream without promoting timings."""

    raw = require_regular_file(path, nonempty=True).read_bytes()
    lines = raw.splitlines(keepends=True)
    events: list[dict[str, Any]] = []
    previous_timestamp: dt.datetime | None = None
    allowed_events = {
        "COLLECTION_FINISHED",
        "PREPARATION_FAILED",
        "PREPARATION_STARTED",
        "PROCESS_EXITED",
        "PYTEST_ITEM_FINISHED",
        "SESSION_FINISHED",
        "STARTED",
        "START_FAILED",
        "TIMED_OUT",
    }
    expected_nodes = authority["node_ids"]
    expected_node_set = set(expected_nodes)
    for index, line in enumerate(lines):
        event_location = f"{location}[{index}]"
        value = strict_json_loads(line)
        if line != canonical_json_bytes(value):
            raise EvidenceError(f"{event_location} is not canonical JSONL")
        if not isinstance(value, dict):
            raise EvidenceError(f"{event_location} must be an object")
        event_name = value.get("event")
        if event_name not in allowed_events:
            raise EvidenceError(f"{event_location}.event is invalid")
        common = {"event", "recorded_at", "shard_id"}
        expected_keys: set[str]
        if event_name == "PREPARATION_STARTED":
            expected_keys = {*common, "selector_count"}
        elif event_name in {"PREPARATION_FAILED", "START_FAILED"}:
            expected_keys = {*common, "error"}
        elif event_name == "STARTED":
            expected_keys = {*common, "pid"}
        elif event_name == "COLLECTION_FINISHED":
            expected_keys = {
                *common,
                "collected_count",
                "collection_matches",
                "duplicate_count",
                "expected_count",
                "missing_count",
                "selected_count",
                "unexpected_count",
            }
        elif event_name == "PYTEST_ITEM_FINISHED":
            expected_keys = {
                *common,
                "duration_seconds",
                "node_id",
                "outcome",
            }
        elif event_name == "SESSION_FINISHED":
            expected_keys = {*common, "exit_code", "node_count"}
        elif event_name in {"PROCESS_EXITED", "TIMED_OUT"} and value.get(
            "launched"
        ) is True:
            expected_keys = {
                *common,
                "launched",
                "returncode",
                "termination_returncode",
            }
        else:
            expected_keys = {*common, "launched"}
        event = _exact_keys(value, expected_keys, event_location)
        if event["shard_id"] != authority["shard_id"]:
            raise EvidenceError(f"{event_location}.shard_id mismatch")
        timestamp = dt.datetime.fromisoformat(
            _require_timestamp(
                event["recorded_at"], f"{event_location}.recorded_at"
            ).replace("Z", "+00:00")
        )
        if previous_timestamp is not None and timestamp < previous_timestamp:
            raise EvidenceError(f"{location} timestamps are not ordered")
        previous_timestamp = timestamp

        if event_name == "PREPARATION_STARTED":
            if _require_int(
                event["selector_count"], f"{event_location}.selector_count"
            ) != raw_shard["selector_summary"]["selector_count"]:
                raise EvidenceError(f"{event_location}.selector_count mismatch")
        elif event_name in {"PREPARATION_FAILED", "START_FAILED"}:
            _require_string(event["error"], f"{event_location}.error")
        elif event_name == "STARTED":
            if _require_int(event["pid"], f"{event_location}.pid", minimum=1) != (
                raw_shard["pid"]
            ):
                raise EvidenceError(f"{event_location}.pid mismatch")
        elif event_name == "COLLECTION_FINISHED":
            for key in (
                "collected_count",
                "duplicate_count",
                "expected_count",
                "missing_count",
                "selected_count",
                "unexpected_count",
            ):
                _require_int(event[key], f"{event_location}.{key}")
            if not isinstance(event["collection_matches"], bool):
                raise EvidenceError(
                    f"{event_location}.collection_matches must be boolean"
                )
            if event["expected_count"] != authority["node_count"]:
                raise EvidenceError(f"{event_location}.expected_count mismatch")
            if event["collection_matches"] and (
                event["collected_count"] != authority["node_count"]
                or event["selected_count"] != authority["node_count"]
                or any(
                    event[key] != 0
                    for key in ("duplicate_count", "missing_count", "unexpected_count")
                )
            ):
                raise EvidenceError(f"{event_location} false exact-collection claim")
        elif event_name == "PYTEST_ITEM_FINISHED":
            if event["node_id"] not in expected_node_set:
                raise EvidenceError(f"{event_location}.node_id is unregistered")
            if event["outcome"] not in {
                "ERROR",
                "FAILED",
                "NOT_RUN",
                "PASSED",
                "SKIPPED",
                "XFAIL",
                "XPASS",
            }:
                raise EvidenceError(f"{event_location}.outcome is invalid")
            duration = event["duration_seconds"]
            if (
                not isinstance(duration, (int, float))
                or isinstance(duration, bool)
                or not math.isfinite(duration)
                or duration < 0.0
            ):
                raise EvidenceError(f"{event_location}.duration_seconds is invalid")
        elif event_name == "SESSION_FINISHED":
            _require_int(event["exit_code"], f"{event_location}.exit_code")
            if _require_int(
                event["node_count"], f"{event_location}.node_count"
            ) != authority["node_count"]:
                raise EvidenceError(f"{event_location}.node_count mismatch")
        elif event_name in {"PROCESS_EXITED", "TIMED_OUT"}:
            if not isinstance(event["launched"], bool):
                raise EvidenceError(f"{event_location}.launched must be boolean")
            if event["launched"]:
                _require_int(event["returncode"], f"{event_location}.returncode")
                termination_returncode = event["termination_returncode"]
                if termination_returncode is not None:
                    _require_int(
                        termination_returncode,
                        f"{event_location}.termination_returncode",
                    )
        events.append(dict(event))

    event_names = [event["event"] for event in events]
    if not event_names or event_names[0] != "PREPARATION_STARTED":
        raise EvidenceError(f"{location} does not begin with preparation")
    if raw_shard["attempts"] == 1:
        if "STARTED" not in event_names:
            raise EvidenceError(f"{location} omits the launched-worker event")
        if event_names[-1] not in {"PROCESS_EXITED", "TIMED_OUT"}:
            raise EvidenceError(f"{location} omits the terminal process event")
    item_nodes = [
        event["node_id"]
        for event in events
        if event["event"] == "PYTEST_ITEM_FINISHED"
    ]
    if len(item_nodes) != len(set(item_nodes)):
        raise EvidenceError(f"{location} repeats a pytest-item event")
    expected_order = {node_id: index for index, node_id in enumerate(expected_nodes)}
    if item_nodes != sorted(item_nodes, key=expected_order.__getitem__):
        raise EvidenceError(f"{location} pytest-item events are out of frozen order")
    if raw_shard["returncode"] == 0:
        required = {
            "COLLECTION_FINISHED",
            "PROCESS_EXITED",
            "SESSION_FINISHED",
            "STARTED",
        }
        if not required.issubset(event_names):
            raise EvidenceError(f"{location} omits completed-shard lifecycle events")
        collection = next(
            event for event in events if event["event"] == "COLLECTION_FINISHED"
        )
        if collection["collection_matches"] is not True:
            raise EvidenceError(f"{location} passing shard did not collect exactly")
        if item_nodes != expected_nodes:
            raise EvidenceError(f"{location} passing shard lacks per-node durations")
    return events


def _validate_functional_raw_shard(
    value: Any,
    *,
    authority: Mapping[str, Any],
    contract: Mapping[str, Any],
    cycle: int,
    location: str,
) -> dict[str, Any]:
    """Validate raw timing/progress diagnostics without admitting them to evidence."""

    required_keys = {
        "attempts",
        "command",
        "command_sha256",
        "deadline_seconds",
        "duration_seconds",
        "ended_at",
        "pid",
        "progress",
        "pytest_durations",
        "returncode",
        "selector_summary",
        "shard_id",
        "started_at",
        "stderr",
        "stdout",
        "termination",
        "timed_out",
    }
    optional_keys = {
        "disposition",
        "error",
        "process_error",
        "result_error",
        "termination_error",
    }
    if not isinstance(value, dict):
        raise EvidenceError(f"{location} must be an object")
    if set(value) == {"attempts", "error", "shard_id"}:
        emergency = dict(value)
        if (
            emergency["shard_id"] != authority["shard_id"]
            or emergency["attempts"] != 1
        ):
            raise EvidenceError(f"{location} emergency diagnostics mismatch")
        _require_string(emergency["error"], f"{location}.error")
        return emergency
    if not required_keys.issubset(value) or not set(value).issubset(
        required_keys | optional_keys
    ):
        raise EvidenceError(f"{location} keys mismatch")
    shard = dict(value)
    if shard["shard_id"] != authority["shard_id"]:
        raise EvidenceError(f"{location}.shard_id mismatch")
    attempts = _require_int(shard["attempts"], f"{location}.attempts")
    if attempts not in {0, 1}:
        raise EvidenceError(f"{location}.attempts must be zero or one")
    if _require_int(
        shard["deadline_seconds"], f"{location}.deadline_seconds"
    ) != 830:
        raise EvidenceError(f"{location}.deadline_seconds mismatch")
    for key in ("duration_seconds",):
        duration = shard[key]
        if (
            not isinstance(duration, (int, float))
            or isinstance(duration, bool)
            or not math.isfinite(duration)
            or duration < 0.0
        ):
            raise EvidenceError(f"{location}.{key} is invalid")
    started = dt.datetime.fromisoformat(
        _require_timestamp(shard["started_at"], f"{location}.started_at").replace(
            "Z", "+00:00"
        )
    )
    ended = dt.datetime.fromisoformat(
        _require_timestamp(shard["ended_at"], f"{location}.ended_at").replace(
            "Z", "+00:00"
        )
    )
    if ended < started:
        raise EvidenceError(f"{location} ends before it starts")
    if not isinstance(shard["timed_out"], bool):
        raise EvidenceError(f"{location}.timed_out must be boolean")
    returncode = _require_int(shard["returncode"], f"{location}.returncode")
    pid = shard["pid"]
    if attempts == 1:
        _require_int(pid, f"{location}.pid", minimum=1)
    elif pid is not None:
        raise EvidenceError(f"{location}.pid must be null when no process started")
    if shard["pytest_durations"] != {
        "enabled": True,
        "minimum_seconds": 0.0,
    }:
        raise EvidenceError(f"{location}.pytest_durations mismatch")

    selectors, selector_summary = _functional_shard_selectors(
        authority["node_ids"],
        contract["functional_wave"]["manifest"]["full_node_ids"],
    )
    observed_summary = _exact_keys(
        shard["selector_summary"],
        {
            "exact_node_count",
            "full_module_count",
            "selector_count",
            "selectors_sha256",
        },
        f"{location}.selector_summary",
    )
    if observed_summary != selector_summary:
        raise EvidenceError(f"{location}.selector_summary mismatch")
    command = shard["command"]
    if not isinstance(command, list) or any(
        not isinstance(argument, str) or not argument for argument in command
    ):
        raise EvidenceError(f"{location}.command must be a string array")
    _require_canonical_list_hash(
        command, shard["command_sha256"], f"{location}.command_sha256"
    )
    if command:
        basetemp = functional_wave_shard_artifact_paths(
            contract, cycle, authority["shard_id"]
        )["basetemp"]
        expected_tail = [
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "-p",
            "scripts.run_e4_pl_burnin_gate",
            "--durations=0",
            "--durations-min=0.0",
            f"--basetemp={basetemp}",
            *selectors,
        ]
        if command[1:] != expected_tail:
            raise EvidenceError(f"{location}.command selector/observability mismatch")
        if Path(command[0]).resolve() != execution_tool_path(contract, "python"):
            raise EvidenceError(f"{location}.command Python identity mismatch")

    logs = functional_wave_shard_artifact_paths(
        contract, cycle, authority["shard_id"]
    )["logs"]
    artifact_paths = {
        "progress": logs / "progress.ndjson",
        "stderr": logs / "stderr.txt",
        "stdout": logs / "stdout.txt",
    }
    for key, artifact_path in artifact_paths.items():
        record = shard[key]
        if record is None:
            if artifact_path.exists() or artifact_path.is_symlink():
                raise EvidenceError(f"{location}.{key} omits an existing artifact")
            if attempts == 1 or "error" not in shard:
                raise EvidenceError(f"{location}.{key} is unexpectedly absent")
            continue
        validated = _validate_hash_record(record, f"{location}.{key}")
        if file_hash_record(require_regular_file(artifact_path)) != validated:
            raise EvidenceError(f"{location}.{key} artifact identity mismatch")
    progress_events: list[dict[str, Any]] = []
    if shard["progress"] is not None:
        progress_events = _validate_functional_progress(
            artifact_paths["progress"],
            authority=authority,
            raw_shard=shard,
            location=f"{location}.progress_events",
        )
    termination = shard["termination"]
    if termination is not None:
        termination = _exact_keys(
            termination,
            {"bytes", "returncode", "sha256"},
            f"{location}.termination",
        )
        _validate_hash_record(
            {"bytes": termination["bytes"], "sha256": termination["sha256"]},
            f"{location}.termination",
        )
        _require_int(
            termination["returncode"], f"{location}.termination.returncode"
        )
    if shard["timed_out"] and returncode != 124:
        raise EvidenceError(f"{location} timed-out return code mismatch")
    for key in optional_keys - {"disposition"}:
        if key in shard:
            _require_string(shard[key], f"{location}.{key}")
    if attempts == 0:
        disposition = _require_string(
            shard.get("disposition"), f"{location}.disposition"
        )
        last_event = progress_events[-1]["event"] if progress_events else None
        if shard["timed_out"]:
            expected_disposition = "DEADLINE_EXPIRED_NOT_STARTED"
            if last_event != "TIMED_OUT":
                raise EvidenceError(f"{location} timeout progress is incomplete")
        elif last_event == "START_FAILED":
            expected_disposition = "PROCESS_START_FAILED_NO_CHILD"
        else:
            expected_disposition = "PREPARATION_FAILED_BEFORE_LAUNCH"
        if disposition != expected_disposition:
            raise EvidenceError(f"{location}.disposition mismatch")
    elif "disposition" in shard:
        raise EvidenceError(f"{location}.disposition is forbidden after launch")
    return shard


def _validate_functional_wave_diagnostics(
    path: Path,
    *,
    contract: Mapping[str, Any],
    cycle_root: Path,
    cycle: int,
    routing: Mapping[str, str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = require_regular_file(path, nonempty=True).read_bytes()
    diagnostics = strict_json_loads(raw)
    if raw != canonical_json_bytes(diagnostics):
        raise EvidenceError("functional-wave diagnostics are noncanonical")
    if not isinstance(diagnostics, dict):
        raise EvidenceError("functional-wave diagnostics must be an object")
    common_keys = {"artifact_extent", "cycle", "schema"}
    success_keys = {
        *common_keys,
        "archive_process",
        "shards",
        "source_status_after",
        "source_status_before",
    }
    failure_keys = {*common_keys, "failure"}
    keys = set(diagnostics)
    if keys == success_keys:
        kind = "SUCCESS_SHAPE"
    elif keys == failure_keys:
        kind = "FAILURE_SHAPE"
    else:
        raise EvidenceError("functional-wave diagnostics keys mismatch")
    if diagnostics["schema"] != FUNCTIONAL_WAVE_DIAGNOSTICS_SCHEMA:
        raise EvidenceError("functional-wave diagnostics schema mismatch")
    if diagnostics["cycle"] != cycle:
        raise EvidenceError("functional-wave diagnostics cycle mismatch")
    extent = _validate_functional_wave_extent(
        diagnostics["artifact_extent"],
        cycle_root=cycle_root,
        excluded_paths={
            routing["aggregate_filename"],
            routing["raw_diagnostics_filename"],
        },
        location="$functional_wave_diagnostics.artifact_extent",
    )
    if kind == "SUCCESS_SHAPE":
        if not isinstance(diagnostics["archive_process"], dict):
            raise EvidenceError("functional-wave archive diagnostics are malformed")
        shards = diagnostics["shards"]
        if not isinstance(shards, list) or len(shards) != len(
            FUNCTIONAL_WAVE_SHARD_IDS
        ):
            raise EvidenceError("functional-wave raw shard diagnostics are incomplete")
        if [row.get("shard_id") for row in shards if isinstance(row, dict)] != list(
            FUNCTIONAL_WAVE_SHARD_IDS
        ):
            raise EvidenceError("functional-wave raw shard diagnostics are misordered")
        authorities = contract["functional_wave"]["manifest"]["shards"]
        for index, (shard, authority) in enumerate(
            zip(shards, authorities, strict=True)
        ):
            _validate_functional_raw_shard(
                shard,
                authority=authority,
                contract=contract,
                cycle=cycle,
                location=f"$functional_wave_diagnostics.shards[{index}]",
            )
        before = _validate_hash_record(
            diagnostics["source_status_before"],
            "$functional_wave_diagnostics.source_status_before",
        )
        after = _validate_hash_record(
            diagnostics["source_status_after"],
            "$functional_wave_diagnostics.source_status_after",
        )
        if before != after or before != {
            "bytes": 0,
            "sha256": sha256_bytes(b""),
        }:
            raise EvidenceError("functional-wave source status changed or was dirty")
    else:
        failure = diagnostics["failure"]
        if not isinstance(failure, (dict, str)) or not failure:
            raise EvidenceError("functional-wave failure diagnostics are malformed")
    return diagnostics, {"bytes": len(raw), "sha256": sha256_bytes(raw)}


def _validate_functional_shard_result(
    path: Path,
    *,
    authority: Mapping[str, Any],
    location: str,
) -> tuple[dict[str, Any], bool]:
    """Independently recompute one shard's exact collection/outcome disposition."""

    raw = require_regular_file(path, nonempty=True).read_bytes()
    value = strict_json_loads(raw)
    if raw != canonical_json_bytes(value):
        raise EvidenceError(f"{location} is noncanonical")
    result = _exact_keys(
        value,
        {"collection_matches", "exit_code", "nodes", "schema", "shard_id"},
        location,
    )
    if result["schema"] != FUNCTIONAL_SHARD_SCHEMA:
        raise EvidenceError(f"{location}.schema mismatch")
    if result["shard_id"] != authority["shard_id"]:
        raise EvidenceError(f"{location}.shard_id mismatch")
    collection_matches = result["collection_matches"]
    if not isinstance(collection_matches, bool):
        raise EvidenceError(f"{location}.collection_matches must be boolean")
    exit_code = _require_int(result["exit_code"], f"{location}.exit_code")
    nodes = result["nodes"]
    expected_nodes = authority["node_ids"]
    if not isinstance(nodes, list) or len(nodes) != len(expected_nodes):
        raise EvidenceError(f"{location}.nodes count mismatch")
    allowed_outcomes = {
        "ERROR",
        "FAILED",
        "NOT_RUN",
        "PASSED",
        "SKIPPED",
        "XFAIL",
        "XPASS",
    }
    outcomes: list[str] = []
    for index, (row, expected_node) in enumerate(
        zip(nodes, expected_nodes, strict=True)
    ):
        node_location = f"{location}.nodes[{index}]"
        row = _exact_keys(row, {"node_id", "outcome"}, node_location)
        if row["node_id"] != expected_node:
            raise EvidenceError(f"{node_location}.node_id mismatch")
        outcome = row["outcome"]
        if outcome not in allowed_outcomes:
            raise EvidenceError(f"{node_location}.outcome is invalid")
        outcomes.append(outcome)
    passed = (
        collection_matches
        and exit_code == 0
        and all(outcome in {"PASSED", "SKIPPED", "XFAIL"} for outcome in outcomes)
    )
    return result, passed


def _validate_functional_wave_aggregate(
    value: Any,
    *,
    contract: Mapping[str, Any],
    cycle: int,
    candidate: Mapping[str, Any],
    paths: Mapping[str, Any],
    diagnostics_record: Mapping[str, Any],
    expect_success: bool,
) -> dict[str, Any]:
    wave = validate_functional_wave_contract(contract)
    aggregate = _exact_keys(
        value,
        {
            "candidate",
            "diagnostics",
            "manifest",
            "schema",
            "shards",
            "source",
            "terminal",
        },
        "$functional_wave_aggregate",
    )
    if aggregate["schema"] != wave["aggregate"]["schema"]:
        raise EvidenceError("functional-wave aggregate schema mismatch")
    expected_terminal = wave["aggregate"][
        "success_terminal" if expect_success else "blocked_terminal"
    ]
    if aggregate["terminal"] != expected_terminal:
        raise EvidenceError("functional-wave aggregate terminal mismatch")
    diagnostics = _validate_hash_record(
        aggregate["diagnostics"], "$functional_wave_aggregate.diagnostics"
    )
    if diagnostics != diagnostics_record:
        raise EvidenceError("functional-wave aggregate diagnostics binding mismatch")
    expected_candidate = {
        "commit": candidate["commit"],
        "tree": candidate["tree"],
    }
    sentinel_candidate = {"commit": "0" * 40, "tree": "0" * 40}
    if aggregate["candidate"] != expected_candidate and (
        expect_success or aggregate["candidate"] != sentinel_candidate
    ):
        raise EvidenceError("functional-wave aggregate candidate mismatch")
    manifest = _exact_keys(
        aggregate["manifest"],
        {
            "module_count",
            "modules_sha256",
            "node_count",
            "node_ids_sha256",
            "shard_count",
        },
        "$functional_wave_aggregate.manifest",
    )
    expected_manifest = {
        "module_count": wave["manifest"]["module_count"],
        "modules_sha256": wave["manifest"]["modules_sha256"],
        "node_count": wave["manifest"]["node_count"],
        "node_ids_sha256": wave["manifest"]["full_node_ids_sha256"],
        "shard_count": len(FUNCTIONAL_WAVE_SHARD_IDS),
    }
    if manifest != expected_manifest:
        raise EvidenceError("functional-wave aggregate manifest mismatch")
    shards = aggregate["shards"]
    if not isinstance(shards, list) or len(shards) != len(FUNCTIONAL_WAVE_SHARD_IDS):
        raise EvidenceError("functional-wave aggregate shard count mismatch")
    all_pass = True
    allowed_statuses = {
        "MALFORMED_RESULT",
        "MISSING_RESULT",
        "PASS",
        "PREPARATION_FAILED",
        "PROCESS_ERROR",
        "PROCESS_FAILED",
        "START_FAILED",
        "TEST_FAILURE",
        "TIMED_OUT",
        "TIMED_OUT_NOT_STARTED",
        "TIMEOUT_TREE_TERMINATION_FAILED",
        "NOT_STARTED_OR_UNBOUND_PARTIAL",
    }
    for index, (shard, authority) in enumerate(
        zip(shards, wave["manifest"]["shards"], strict=True)
    ):
        location = f"$functional_wave_aggregate.shards[{index}]"
        shard = _exact_keys(
            shard,
            {"exit_code", "node_count", "node_ids_sha256", "result", "shard_id", "status"},
            location,
        )
        if (
            shard["shard_id"] != authority["shard_id"]
            or shard["node_count"] != authority["node_count"]
            or shard["node_ids_sha256"] != authority["node_ids_sha256"]
        ):
            raise EvidenceError(f"{location} authority mismatch")
        if shard["status"] not in allowed_statuses:
            raise EvidenceError(f"{location}.status is invalid")
        if not isinstance(shard["exit_code"], int) or isinstance(
            shard["exit_code"], bool
        ):
            raise EvidenceError(f"{location}.exit_code must be an integer")
        shard_passed = shard["status"] == "PASS" and shard["exit_code"] == 0
        all_pass = all_pass and shard_passed
        result_path = (
            paths["shards"][authority["shard_id"]]
            / "logs"
            / "shard-result.json"
        )
        if shard["result"] is None:
            if result_path.exists() or result_path.is_symlink():
                raise EvidenceError(f"{location} omits an existing result")
            if shard_passed:
                raise EvidenceError(f"{location} pass lacks a result")
        else:
            result_record = _validate_hash_record(
                shard["result"], f"{location}.result"
            )
            if file_hash_record(require_regular_file(result_path, nonempty=True)) != result_record:
                raise EvidenceError(f"{location}.result identity mismatch")
            try:
                shard_result, result_passed = _validate_functional_shard_result(
                    result_path,
                    authority=authority,
                    location=f"{location}.result_content",
                )
            except (EvidenceError, OSError, UnicodeError):
                if shard["status"] in {"PASS", "TEST_FAILURE"}:
                    raise EvidenceError(f"{location} status hides a malformed result")
            else:
                if shard["status"] == "MALFORMED_RESULT":
                    raise EvidenceError(f"{location} falsely classifies a valid result as malformed")
                if shard["status"] in {"PASS", "TEST_FAILURE"}:
                    expected_status = "PASS" if result_passed else "TEST_FAILURE"
                    if shard["status"] != expected_status:
                        raise EvidenceError(f"{location} status disagrees with exact node outcomes")
                    if shard["exit_code"] != shard_result["exit_code"]:
                        raise EvidenceError(f"{location}.exit_code differs from shard result")
    if all_pass != expect_success:
        raise EvidenceError("functional-wave terminal does not follow shard outcomes")
    source = _exact_keys(
        aggregate["source"],
        {"archive", "file_graph", "file_graph_content", "repository_status"},
        "$functional_wave_aggregate.source",
    )
    archive_exists = paths["archive"].exists() or paths["archive"].is_symlink()
    if source["archive"] is None:
        if expect_success or archive_exists:
            raise EvidenceError("functional-wave aggregate omits its archive")
    else:
        archive_record = _validate_hash_record(
            source["archive"], "$functional_wave_aggregate.source.archive"
        )
        if (
            file_hash_record(require_regular_file(paths["archive"], nonempty=True))
            != archive_record
        ):
            raise EvidenceError("functional-wave archive identity mismatch")
    graph_path = paths["cycle_root"] / wave["source"]["file_graph_filename"]
    graph_exists = graph_path.exists() or graph_path.is_symlink()
    if source["file_graph"] is None:
        if expect_success or graph_exists or source["file_graph_content"] is not None:
            raise EvidenceError("functional-wave aggregate omits its file graph")
    else:
        graph_record = _validate_hash_record(
            source["file_graph"], "$functional_wave_aggregate.source.file_graph"
        )
        if file_hash_record(require_regular_file(graph_path, nonempty=True)) != graph_record:
            raise EvidenceError("functional-wave file-graph identity mismatch")
        graph = _validate_functional_file_graph(
            graph_path,
            source_root=paths["source"],
            schema=wave["source"]["file_graph_schema"],
        )
        if source["file_graph_content"] != graph["summary"]:
            raise EvidenceError("functional-wave file-graph content mismatch")
    empty_status = {
        "bytes": 0,
        "sha256": sha256_bytes(b""),
    }
    if source["repository_status"] is None:
        if expect_success:
            raise EvidenceError("functional-wave aggregate omits source status")
    elif source["repository_status"] != empty_status:
        raise EvidenceError("functional-wave source status was not clean")
    return aggregate


def validate_functional_wave_external_evidence(
    *,
    contract: Mapping[str, Any],
    cycle: int,
    candidate: Mapping[str, Any],
    process: Mapping[str, Any],
    stdout_path: Path,
) -> dict[str, Any]:
    """Validate one complete or blocked wave and its recursive diagnostic extent."""

    if process["status"] == "NOT_RUN":
        raise EvidenceError("not-run functional process has no wave evidence")
    wave = validate_functional_wave_contract(contract)
    paths = validate_functional_wave_artifact_state(
        contract, cycle, require_fresh=False
    )
    cycle_root = paths["cycle_root"]
    if (
        not cycle_root.is_dir()
        or cycle_root.is_symlink()
        or is_reparse_point(cycle_root)
    ):
        raise EvidenceError("functional-wave cycle root is noncanonical")
    routing = wave["execution"]["artifact_routing"]
    allowed_top_level = {
        routing["aggregate_filename"],
        routing["archive_filename"],
        routing["raw_diagnostics_filename"],
        routing["source_directory_name"],
        wave["source"]["file_graph_filename"],
        *(
            f"{routing['shard_directory_prefix']}{shard_id}"
            for shard_id in FUNCTIONAL_WAVE_SHARD_IDS
        ),
    }
    observed_top_level = {path.name for path in cycle_root.iterdir()}
    if not observed_top_level.issubset(allowed_top_level):
        raise EvidenceError("functional-wave cycle contains an unregistered artifact")
    required = {
        routing["aggregate_filename"],
        routing["raw_diagnostics_filename"],
    }
    if not required.issubset(observed_top_level):
        raise EvidenceError("functional-wave terminal evidence is incomplete")

    diagnostics_path = paths["raw_diagnostics"]
    diagnostics, diagnostics_record = _validate_functional_wave_diagnostics(
        diagnostics_path,
        contract=contract,
        cycle_root=cycle_root,
        cycle=cycle,
        routing=routing,
    )
    aggregate_path = paths["aggregate"]
    aggregate_raw = require_regular_file(aggregate_path, nonempty=True).read_bytes()
    stdout_raw = require_regular_file(stdout_path, nonempty=True).read_bytes()
    if aggregate_raw != stdout_raw:
        raise EvidenceError("functional resource stdout differs from wave aggregate")
    aggregate = strict_json_loads(aggregate_raw)
    if aggregate_raw != canonical_json_bytes(aggregate):
        raise EvidenceError("functional-wave aggregate is noncanonical")
    validated = _validate_functional_wave_aggregate(
        aggregate,
        contract=contract,
        cycle=cycle,
        candidate=candidate,
        paths=paths,
        diagnostics_record=diagnostics_record,
        expect_success=process["status"] == "PASS",
    )
    diagnostics_failure = "failure" in diagnostics
    if process["status"] == "PASS" and diagnostics_failure:
        raise EvidenceError("passing functional wave carries failure diagnostics")
    return {
        "aggregate": file_hash_record(aggregate_path),
        "diagnostics": diagnostics_record,
        "terminal": validated["terminal"],
    }


def _validate_git_commit_record(
    value: Any,
    location: str,
    *,
    commit: str,
    subject: str,
    tree: str,
) -> dict[str, Any]:
    record = _exact_keys(value, {"commit", "subject", "tree"}, location)
    if record != {"commit": commit, "subject": subject, "tree": tree}:
        raise EvidenceError(f"{location} mismatch")
    return record


def _validate_repository_evidence_record(
    value: Any,
    location: str,
    *,
    expected_path: str,
    expected_bytes: int,
    expected_sha256: str,
) -> dict[str, Any]:
    record = _exact_keys(value, {"bytes", "path", "sha256"}, location)
    _validate_hash_record(
        {"bytes": record["bytes"], "sha256": record["sha256"]}, location
    )
    if record != {
        "bytes": expected_bytes,
        "path": expected_path,
        "sha256": expected_sha256,
    }:
        raise EvidenceError(f"{location} mismatch")
    return record


def _validate_attempt_4_incident(value: Any, location: str) -> dict[str, Any]:
    incident = _exact_keys(
        value,
        {
            "attempt",
            "authority_commit",
            "blocked_closeout",
            "contract_sha256",
            "execution_authorization_commit",
            "external_authority",
            "failure",
            "preserved_branch",
            "preserved_repository_evidence",
            "request_disposition",
            "request_ids",
            "role",
            "terminal",
        },
        location,
    )
    if incident["attempt"] != 4:
        raise EvidenceError(f"{location}.attempt must be 4")
    _validate_git_commit_record(
        incident["authority_commit"],
        f"{location}.authority_commit",
        commit="d7bdc8cafe714a4f8d9fd082ec05e7ed64b15a1c",
        subject="docs: authorize corrected S3 Q4 burn-in cycles",
        tree="36890750f735d36ee887a5f1d35e6dfa0becce8c",
    )
    _validate_git_commit_record(
        incident["execution_authorization_commit"],
        f"{location}.execution_authorization_commit",
        commit="4642b7487dc9f9db8e709f3b2e133c781a69fbc9",
        subject="docs: reauthorize corrected S3 Q4 burn-in execution",
        tree="16f0c607c18845c35586026fcdabcdbfa9a8f861",
    )
    _validate_git_commit_record(
        incident["blocked_closeout"],
        f"{location}.blocked_closeout",
        commit="7bf87c397f11bcfb27a242bb74369cf0df3437a5",
        subject="docs: record blocked corrected S3 Q4 burn-in",
        tree="0c84054d9a060fb37aef2d6f8ddd51db46630140",
    )
    if (
        incident["contract_sha256"]
        != "012f3bb6e0e5bb9e737f0947070ac5f3725ec57c3a6b1de722c337f54e0ce8c7"
    ):
        raise EvidenceError(f"{location}.contract_sha256 mismatch")

    external = _exact_keys(
        incident["external_authority"],
        {
            "approval_snapshot",
            "interruption_checkpoint",
            "interruption_ledger_snapshot",
            "launch",
            "output_root",
            "stderr",
            "stdout",
        },
        f"{location}.external_authority",
    )
    if external["output_root"] != (
        r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
        r"\s3-q4-final-freeze-correction-3"
    ):
        raise EvidenceError(f"{location}.external_authority.output_root mismatch")
    expected_external_records = {
        "approval_snapshot": (
            4466,
            "303e24e108f65b0c1fd22de6acc2793a446efb5173f3ba90a985bf4e2c775558",
        ),
        "interruption_checkpoint": (
            1952,
            "c929d708c4a2dbccdf2d83184a5fb14f3c4dc364a14b231614adedb95f139fb6",
        ),
        "interruption_ledger_snapshot": (
            3433,
            "e84ea4bf98e5bba85553919c3ee0f6ad7b2d696456420f83540b4cec45bbbe2a",
        ),
        "launch": (731, "43ecd23cd2c587a5a00294040d93c7a35061ac3716eecb18d822e9fabcf96f88"),
        "stderr": (0, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
        "stdout": (631, "3432918c7de8e411b5fb5fae9c9b8081d939c4832df40357e4c1aac2659f24e0"),
    }
    for key, (expected_bytes, expected_sha256) in expected_external_records.items():
        record = _validate_hash_record(
            external[key], f"{location}.external_authority.{key}"
        )
        if record != {"bytes": expected_bytes, "sha256": expected_sha256}:
            raise EvidenceError(f"{location}.external_authority.{key} mismatch")

    failure = _exact_keys(
        incident["failure"],
        {
            "cause",
            "completion_observed",
            "end_time_observed",
            "exit_code_observed",
            "lane",
            "phase",
            "protocol_terminal_observed",
            "request_id",
            "resource_command_started",
            "wall_limit_seconds",
            "worker_tree_confirmed_absent",
        },
        f"{location}.failure",
    )
    expected_failure = {
        "cause": "MONOLITHIC_FUNCTIONAL_GATE_EXCEEDED_USER_WALL_LIMIT",
        "completion_observed": False,
        "end_time_observed": False,
        "exit_code_observed": False,
        "lane": "functional",
        "phase": "CYCLE_1_RESOURCE_EXECUTION",
        "protocol_terminal_observed": False,
        "request_id": "5c8dd384914c4f7cac6a628a658ce3c9",
        "resource_command_started": True,
        "wall_limit_seconds": 1200,
        "worker_tree_confirmed_absent": True,
    }
    if failure != expected_failure:
        raise EvidenceError(f"{location}.failure mismatch")

    evidence = _exact_keys(
        incident["preserved_repository_evidence"],
        {"result", "review", "status"},
        f"{location}.preserved_repository_evidence",
    )
    _validate_repository_evidence_record(
        evidence["result"],
        f"{location}.preserved_repository_evidence.result",
        expected_path="docs/reference_cases/e4_pl_s3_q4_blocked_burnin_result.json",
        expected_bytes=4730,
        expected_sha256="8b332ad570906d98d9f705f4671b0f25ee7a4b24f1c46549eacca34176c5f7b4",
    )
    _validate_repository_evidence_record(
        evidence["review"],
        f"{location}.preserved_repository_evidence.review",
        expected_path="docs/reference_cases/e4_pl_s3_q4_blocked_burnin_review.json",
        expected_bytes=536,
        expected_sha256="f6e5ddd2cf1057326652084c3f5d5cd0d6af1a5374124ef8a41acc034f0abc69",
    )
    _validate_repository_evidence_record(
        evidence["status"],
        f"{location}.preserved_repository_evidence.status",
        expected_path="docs/reference_cases/e4_pl_s3_q4_blocked_burnin_status.json",
        expected_bytes=293,
        expected_sha256="b6ba5edd829e130908a49b75e22235341114e92ed250b4fdbb96c734cda03752",
    )
    expected_request_ids = [
        "5c8dd384914c4f7cac6a628a658ce3c9",
        "74475e0ae7444fc4b4a48e25f4400ba5",
        "de953b708c9b4ff5bf96963d74e5cc3a",
        "150ebb3da109449eb16e4a21714c8ba3",
        "3b5c383d85664da99d60d4f8d65456ba",
        "9451d872c7554a8aa764d8496952a9f5",
    ]
    if incident["request_ids"] != expected_request_ids:
        raise EvidenceError(f"{location}.request_ids mismatch")
    if incident["request_disposition"] != (
        "INTERRUPTED_INCOMPLETE_FIRST_REQUEST_REMAINING_"
        "CANCELLED_NOT_RUN_SUPERSEDED"
    ):
        raise EvidenceError(f"{location}.request_disposition mismatch")
    if incident["preserved_branch"] != "codex/s3-e4-pl-final-burnin-blocked-attempt-4":
        raise EvidenceError(f"{location}.preserved_branch mismatch")
    if incident["role"] != "PRESERVED_BLOCKED_PREDECESSOR_ONLY":
        raise EvidenceError(f"{location}.role mismatch")
    if incident["terminal"] != "BLOCKED_E4_PL_S3_Q4_BURN_IN_GATE":
        raise EvidenceError(f"{location}.terminal mismatch")
    return incident


def _validate_attempt_5_incident(value: Any, location: str) -> dict[str, Any]:
    """Bind the review-created bytecode contamination that blocked attempt 5."""

    incident = _exact_keys(
        value,
        {
            "attempt",
            "authority_commit",
            "blocked_closeout",
            "contract_sha256",
            "execution_authorization_commit",
            "external_authority",
            "failure",
            "preserved_branch",
            "preserved_repository_evidence",
            "request_disposition",
            "request_ids",
            "role",
            "terminal",
        },
        location,
    )
    if incident["attempt"] != 5:
        raise EvidenceError(f"{location}.attempt must be 5")
    _validate_git_commit_record(
        incident["authority_commit"],
        f"{location}.authority_commit",
        commit="ca0b3a5d95d336262542f317f0e207dde837197a",
        subject="docs: authorize corrected S3 Q4 burn-in cycles",
        tree="c0216f08d7613de7a22c25e1ae88fa79f3aee896",
    )
    _validate_git_commit_record(
        incident["execution_authorization_commit"],
        f"{location}.execution_authorization_commit",
        commit="c51e5c249f4d754ee285c489b165fba78cd34c01",
        subject="docs: reauthorize corrected S3 Q4 burn-in execution",
        tree="14f6d1cd696d35ee329f4a4cdc79b39058f31e2f",
    )
    _validate_git_commit_record(
        incident["blocked_closeout"],
        f"{location}.blocked_closeout",
        commit="6fa5f1e86c8b4fb91d00dce095cd4ba4a6c81e28",
        subject="docs: record blocked corrected S3 Q4 burn-in",
        tree="bfd679e4410105d5d5ab29c2e3df6dc647d826e5",
    )
    if (
        incident["contract_sha256"]
        != "519b24c97f7a3953457922aa08514efd59e5aacfc26843c1765988e79cc1842c"
    ):
        raise EvidenceError(f"{location}.contract_sha256 mismatch")

    external = _exact_keys(
        incident["external_authority"],
        {"output_root", "present"},
        f"{location}.external_authority",
    )
    if external["output_root"] != (
        r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
        r"\s3-q4-final-freeze-correction-4"
    ) or external["present"] is not False:
        raise EvidenceError(f"{location}.external_authority output mismatch")
    expected_contamination = [
        {
            "bytes": 180248,
            "path": "docs/reference_cases/__pycache__/e4_pl_s3_q4_burnin.cpython-313.pyc",
            "sha256": "ebf0b3a9aaadac2f8f664ebf4d8a939ba9d0e2a0856ebbc9f18ba733e2b8dc0f",
        },
        {
            "bytes": 173172,
            "path": (
                "docs/reference_cases/__pycache__/"
                "e4_pl_s3_q4_process_runner.cpython-313.pyc"
            ),
            "sha256": "013c46be51e20e59469bf40ed7332f92c072e1d16c351e47eba84c719f8494ae",
        },
        {
            "bytes": 148815,
            "path": "scripts/__pycache__/run_e4_pl_burnin_gate.cpython-313.pyc",
            "sha256": "2c24f1bad6904c2562a034cbce4bac9d32ee21662f747e497a001e2274a93e34",
        },
        {
            "bytes": 943,
            "path": "tests/__pycache__/conftest.cpython-313-pytest-9.0.1.pyc",
            "sha256": "1750f214a003af3fa00005ce9f39448e0745e7932cc9c7b0acef84496f1f4055",
        },
        {
            "bytes": 327953,
            "path": (
                "tests/__pycache__/"
                "test_e4_pl_s3_q4_burnin_authority.cpython-313-pytest-9.0.1.pyc"
            ),
            "sha256": "5321edca00f152e796a970d0651e059366f0adaa20a616bb2c6d15a687d305dc",
        },
    ]
    failure = _exact_keys(
        incident["failure"],
        {
            "cause",
            "clean_input_guard_rejected",
            "coordinator_exit_code",
            "global_lock_acquired",
            "input_contamination",
            "lane",
            "ledger_rows_written",
            "phase",
            "quick_command_started",
            "resource_commands_started",
        },
        f"{location}.failure",
    )
    expected_failure = {
        "cause": "IGNORED_BYTECODE_CONTAMINATED_FROZEN_INPUT",
        "clean_input_guard_rejected": True,
        "coordinator_exit_code": 1,
        "global_lock_acquired": False,
        "input_contamination": {
            "count": 5,
            "origin": (
                "INDEPENDENT_REVIEW_PYTEST_WITHOUT_EXTERNAL_PYTHON_CACHE_ISOLATION"
            ),
            "records": expected_contamination,
        },
        "lane": "quick",
        "ledger_rows_written": False,
        "phase": "COMMON_PREFLIGHT_AUTHORITY_CHECK",
        "quick_command_started": False,
        "resource_commands_started": False,
    }
    if failure != expected_failure:
        raise EvidenceError(f"{location}.failure mismatch")
    contamination = _exact_keys(
        failure["input_contamination"],
        {"count", "origin", "records"},
        f"{location}.failure.input_contamination",
    )
    for index, record in enumerate(contamination["records"]):
        _validate_repository_evidence_record(
            record,
            f"{location}.failure.input_contamination.records[{index}]",
            expected_path=expected_contamination[index]["path"],
            expected_bytes=expected_contamination[index]["bytes"],
            expected_sha256=expected_contamination[index]["sha256"],
        )

    evidence = _exact_keys(
        incident["preserved_repository_evidence"],
        {"result", "review", "status"},
        f"{location}.preserved_repository_evidence",
    )
    _validate_repository_evidence_record(
        evidence["result"],
        f"{location}.preserved_repository_evidence.result",
        expected_path="docs/reference_cases/e4_pl_s3_q4_blocked_burnin_result.json",
        expected_bytes=2796,
        expected_sha256="b7b42e283e3a8ce58bd8527e567dd70e5e7829e39d33256db59d031795291090",
    )
    _validate_repository_evidence_record(
        evidence["review"],
        f"{location}.preserved_repository_evidence.review",
        expected_path="docs/reference_cases/e4_pl_s3_q4_blocked_burnin_review.json",
        expected_bytes=536,
        expected_sha256="5ce4294c9d8f5ce9efc53685ae57a6881b96107a593bf698c7b890281ada6ed6",
    )
    _validate_repository_evidence_record(
        evidence["status"],
        f"{location}.preserved_repository_evidence.status",
        expected_path="docs/reference_cases/e4_pl_s3_q4_blocked_burnin_status.json",
        expected_bytes=293,
        expected_sha256="2b28f2d0029cb5c0339d41e2978ee38e4628958c973dcd621c72b61d83e10962",
    )
    expected_request_ids = [
        "fa0a053dbd144a15b65e6f63d1abd81c",
        "bac1d19b20574f69a74e2313973e7f33",
        "2b34ad0ce56d49579405e8431f4a47d1",
        "1353d866827648b88e718f2134a26fc5",
        "020582eaea1e4633a29abc853a2647dc",
        "15205bbf29a54b2abb4289a5fcb02379",
    ]
    if incident["request_ids"] != expected_request_ids:
        raise EvidenceError(f"{location}.request_ids mismatch")
    if incident["request_disposition"] != "NOT_APPROVED_NOT_CONSUMED_SUPERSEDED":
        raise EvidenceError(f"{location}.request_disposition mismatch")
    if incident["preserved_branch"] != (
        "codex/s3-e4-pl-final-burnin-blocked-attempt-5"
    ):
        raise EvidenceError(f"{location}.preserved_branch mismatch")
    if incident["role"] != "PRESERVED_BLOCKED_PREDECESSOR_ONLY":
        raise EvidenceError(f"{location}.role mismatch")
    if incident["terminal"] != "BLOCKED_E4_PL_S3_Q4_BURN_IN_GATE":
        raise EvidenceError(f"{location}.terminal mismatch")
    return incident


def _validate_attempt_6_incident(value: Any, location: str) -> dict[str, Any]:
    """Bind the rejected v6 authority reviews without treating them as approval."""

    incident = _exact_keys(
        value,
        {
            "attempt",
            "authority_commit",
            "contract",
            "failure",
            "ledger_occurrences",
            "preserved_ref",
            "request_disposition",
            "request_ids",
            "review_test_results",
            "reviews",
            "role",
            "terminal",
        },
        location,
    )
    if incident["attempt"] != 6:
        raise EvidenceError(f"{location}.attempt must be 6")
    _validate_git_commit_record(
        incident["authority_commit"],
        f"{location}.authority_commit",
        commit="a52994945721295686d9c1776a2bdb5a9a1c7ec3",
        subject="docs: authorize corrected S3 Q4 burn-in cycles",
        tree="87d18d978d94035bc49c11a4610d2bcbc964157c",
    )
    contract_record = _exact_keys(
        incident["contract"], {"bytes", "sha256"}, f"{location}.contract"
    )
    _validate_hash_record(contract_record, f"{location}.contract")
    if contract_record != {
        "bytes": 274979,
        "sha256": "9f7e5a2bf25ba2ed94efd1c6fbf7caec98bda48124a43466a83447846040f7f0",
    }:
        raise EvidenceError(f"{location}.contract mismatch")

    reviewed_inputs = {
        "attachment_sha256": (
            "c76832af87afa4a8828ba6dbad0c582b79d69934233081f0bb640fb2d250240a"
        ),
        "authority_commit": "a52994945721295686d9c1776a2bdb5a9a1c7ec3",
        "authority_tree": "87d18d978d94035bc49c11a4610d2bcbc964157c",
        "base_commit": "e34f12398751a6315372bae68c089f8184a045fe",
        "checkpoint_commit": "bfdadccfb35b7f62689acb77bb071192ad831c61",
        "contract_sha256": (
            "9f7e5a2bf25ba2ed94efd1c6fbf7caec98bda48124a43466a83447846040f7f0"
        ),
    }
    expected_reviews = [
        {
            "findings": [
                {
                    "details": (
                        "Sanitized Git probes omit the frozen safe.directory and "
                        "core.autocrlf=true options. The exact probe fails with dubious "
                        "ownership; with only safe.directory added it reports 91 false "
                        "modified paths (3842 bytes), while core.autocrlf=true produces "
                        "the required empty status. This blocks functional Cycle 1 "
                        "before shard launch and can also reject package/CI repository "
                        "identities."
                    ),
                    "locations": ["_git", "_functional_source_status"],
                    "path": "scripts/run_e4_pl_burnin_gate.py",
                    "priority": "P1",
                    "title": "Pin canonical Windows Git options in every gate probe",
                }
            ],
            "reviewed_inputs": reviewed_inputs,
            "reviewer_independence": {
                "did_not_author_candidate": True,
                "did_not_execute_resource_lanes": True,
                "independent_of_other_reviewer": True,
                "reviewer_id": "codex-v6-independent-authority-review-1-a5299494",
            },
            "schema": "anysolver.e4-pl-s3-q4-authority-review-v1",
            "verdict": "REJECT_E4_PL_S3_Q4_BURN_IN_AUTHORITY_P1",
        },
        {
            "findings": [
                {
                    "evidence": (
                        "With GIT_CONFIG_GLOBAL=NUL and GIT_CONFIG_NOSYSTEM=1, "
                        "the gate-style status command reports 12980 bytes on this "
                        "otherwise clean detached Windows checkout; the "
                        "validator-equivalent command with core.autocrlf=true reports "
                        "zero."
                    ),
                    "location": "scripts/run_e4_pl_burnin_gate.py:1086",
                    "priority": "P1",
                    "summary": (
                        "Formal gate Git commands disable the user line-ending policy "
                        "without pinning an equivalent core.autocrlf policy, so "
                        "quick/package/functional CI can falsely classify the clean "
                        "authority worktree as dirty before scientific execution."
                    ),
                }
            ],
            "reviewed_inputs": reviewed_inputs,
            "reviewer_independence": {
                "did_not_author_candidate": True,
                "did_not_execute_resource_lanes": True,
                "independent_of_other_reviewer": True,
                "reviewer_id": "codex-v6-independent-authority-review-2-a529949",
            },
            "schema": "anysolver.e4-pl-s3-q4-authority-review-v1",
            "verdict": "REJECT_E4_PL_S3_Q4_BURN_IN_AUTHORITY_P1",
        },
    ]
    if incident["reviews"] != expected_reviews:
        raise EvidenceError(f"{location}.reviews mismatch")
    expected_test_results = [
        {
            "failed": 0,
            "passed": 35,
            "reviewer_id": "codex-v6-independent-authority-review-1-a5299494",
        },
        {
            "failed": 0,
            "passed": 35,
            "reviewer_id": "codex-v6-independent-authority-review-2-a529949",
        },
    ]
    if incident["review_test_results"] != expected_test_results:
        raise EvidenceError(f"{location}.review_test_results mismatch")
    expected_failure = {
        "cause": "SANITIZED_GATE_GIT_POLICY_OMITTED_SAFE_DIRECTORY_AND_AUTOCRLF",
        "formal_execution_started": False,
        "resource_requests_approved": False,
        "resource_requests_consumed": False,
    }
    if incident["failure"] != expected_failure:
        raise EvidenceError(f"{location}.failure mismatch")
    if incident["request_ids"] != list(V6_REJECTED_REQUEST_IDS):
        raise EvidenceError(f"{location}.request_ids mismatch")
    expected_disposition = {
        "ledger_occurrences": 0,
        "preserved_ref": "codex/s3-e4-pl-final-burnin-rejected-v6-a529949",
        "request_disposition": "NOT_APPROVED_NOT_CONSUMED_SUPERSEDED",
        "role": "PRESERVED_REJECTED_AUTHORITY_ONLY",
        "terminal": "BLOCKED_E4_PL_S3_Q4_BURN_IN_AUTHORITY_REVIEW",
    }
    if any(incident[key] != expected for key, expected in expected_disposition.items()):
        raise EvidenceError(f"{location} disposition mismatch")
    return incident


def _validate_attempt_7_incident(value: Any, location: str) -> dict[str, Any]:
    """Bind the rejected v7 CI-partition review without granting execution."""

    incident = _exact_keys(
        value,
        {
            "attempt",
            "authority_commit",
            "contract",
            "failure",
            "ledger_occurrences",
            "preserved_ref",
            "request_disposition",
            "request_ids",
            "review_test_results",
            "reviews",
            "role",
            "terminal",
        },
        location,
    )
    if incident["attempt"] != 7:
        raise EvidenceError(f"{location}.attempt must be 7")
    _validate_git_commit_record(
        incident["authority_commit"],
        f"{location}.authority_commit",
        commit="f9fa288a0b19b63f3d51d1e5e0eaab64790b14d8",
        subject="docs: authorize corrected S3 Q4 burn-in cycles",
        tree="3942ae13d497ce3353d900b4d46502167d8b68c0",
    )
    contract_record = _exact_keys(
        incident["contract"], {"bytes", "sha256"}, f"{location}.contract"
    )
    _validate_hash_record(contract_record, f"{location}.contract")
    if contract_record != {
        "bytes": 279259,
        "sha256": "c779a03ee08db6f9f8696a804cab31fa7da0d73bc6841e1fe483bd9c741de79c",
    }:
        raise EvidenceError(f"{location}.contract mismatch")

    reviewed_inputs = {
        "attachment_sha256": (
            "c76832af87afa4a8828ba6dbad0c582b79d69934233081f0bb640fb2d250240a"
        ),
        "authority_commit": "f9fa288a0b19b63f3d51d1e5e0eaab64790b14d8",
        "authority_tree": "3942ae13d497ce3353d900b4d46502167d8b68c0",
        "base_commit": "e34f12398751a6315372bae68c089f8184a045fe",
        "checkpoint_commit": "bfdadccfb35b7f62689acb77bb071192ad831c61",
        "contract_sha256": (
            "c779a03ee08db6f9f8696a804cab31fa7da0d73bc6841e1fe483bd9c741de79c"
        ),
    }
    expected_reviews = [
        {
            "findings": [],
            "reviewed_inputs": reviewed_inputs,
            "reviewer_independence": {
                "did_not_author_candidate": True,
                "did_not_execute_resource_lanes": True,
                "independent_of_other_reviewer": True,
                "reviewer_id": "codex-v7-independent-authority-review-1-f9fa288",
            },
            "schema": "anysolver.e4-pl-s3-q4-authority-review-v1",
            "verdict": "ACCEPT_E4_PL_S3_Q4_BURN_IN_AUTHORITY_NO_P0_P1",
        },
        {
            "findings": [
                {
                    "evidence": (
                        "The independently collected current extent is 1,036 "
                        "functional plus 871 nonfunctional nodes, totaling 1,907. "
                        "However, nonfunctional_buckets[0] is empty, so P01 contains "
                        "only its one functional node, while "
                        "CI_SHARD_NODE_AUTHORITIES requires P01 to contain 93 nodes. "
                        "_run_bounded_ci therefore deterministically raises before "
                        "launching any CI worker."
                    ),
                    "location": "scripts/run_e4_pl_burnin_gate.py:3630",
                    "priority": "P1",
                    "summary": (
                        "The bounded CI shard assignment cannot satisfy its frozen "
                        "P01 authority."
                    ),
                }
            ],
            "reviewed_inputs": reviewed_inputs,
            "reviewer_independence": {
                "did_not_author_candidate": True,
                "did_not_execute_resource_lanes": True,
                "independent_of_other_reviewer": True,
                "reviewer_id": "codex-v7-independent-authority-review-2-f9fa288",
            },
            "schema": "anysolver.e4-pl-s3-q4-authority-review-v1",
            "verdict": "REJECT_E4_PL_S3_Q4_BURN_IN_AUTHORITY_P1",
        },
    ]
    if incident["reviews"] != expected_reviews:
        raise EvidenceError(f"{location}.reviews mismatch")
    expected_test_results = [
        {
            "failed": 0,
            "passed": 35,
            "reviewer_id": "codex-v7-independent-authority-review-1-f9fa288",
        },
        {
            "failed": 0,
            "passed": 35,
            "reviewer_id": "codex-v7-independent-authority-review-2-f9fa288",
        },
    ]
    if incident["review_test_results"] != expected_test_results:
        raise EvidenceError(f"{location}.review_test_results mismatch")
    expected_failure = {
        "cause": "BOUNDED_CI_P01_NONFUNCTIONAL_PARTITION_EMPTY",
        "formal_execution_started": False,
        "resource_requests_approved": False,
        "resource_requests_consumed": False,
    }
    if incident["failure"] != expected_failure:
        raise EvidenceError(f"{location}.failure mismatch")
    if incident["request_ids"] != list(V7_REJECTED_REQUEST_IDS):
        raise EvidenceError(f"{location}.request_ids mismatch")
    expected_disposition = {
        "ledger_occurrences": 0,
        "preserved_ref": "codex/s3-e4-pl-final-burnin-rejected-v7-f9fa288",
        "request_disposition": "NOT_APPROVED_NOT_CONSUMED_SUPERSEDED",
        "role": "PRESERVED_REJECTED_AUTHORITY_ONLY",
        "terminal": "BLOCKED_E4_PL_S3_Q4_BURN_IN_AUTHORITY_REVIEW",
    }
    if any(incident[key] != expected for key, expected in expected_disposition.items()):
        raise EvidenceError(f"{location} disposition mismatch")
    return incident


def _validate_attempt_8_incident(value: Any, location: str) -> dict[str, Any]:
    """Bind the frozen-sibling hygiene failure that blocked attempt 8."""

    incident = _exact_keys(
        value,
        {
            "attempt",
            "authority_commit",
            "blocked_closeout",
            "contract",
            "execution_authorization_commit",
            "external_authority",
            "failure",
            "preserved_branch",
            "preserved_repository_evidence",
            "request_disposition",
            "request_ids",
            "role",
            "terminal",
        },
        location,
    )
    if incident["attempt"] != 8:
        raise EvidenceError(f"{location}.attempt must be 8")
    _validate_git_commit_record(
        incident["authority_commit"],
        f"{location}.authority_commit",
        commit="880a75a672c9dd32b774aab819a08475af7ba05c",
        subject="docs: authorize corrected S3 Q4 burn-in cycles",
        tree="e2964ddfa4e1c5291c0f95ba8edc0df0f8fbf231",
    )
    _validate_git_commit_record(
        incident["execution_authorization_commit"],
        f"{location}.execution_authorization_commit",
        commit="da12d8264338ff80cfe54540aaa233565dcaaae0",
        subject="docs: reauthorize corrected S3 Q4 burn-in execution",
        tree="bece1cb5eeb0d49b46d50edff5faf10ed567c146",
    )
    _validate_git_commit_record(
        incident["blocked_closeout"],
        f"{location}.blocked_closeout",
        commit="0a893a39ffefeebbeab0dfe31f7ac84cd2c91b25",
        subject="docs: record blocked corrected S3 Q4 burn-in",
        tree="2b8b3d7ddb5991b056f03483d979d75d0445ec4b",
    )
    contract_record = _exact_keys(
        incident["contract"], {"bytes", "sha256"}, f"{location}.contract"
    )
    _validate_hash_record(contract_record, f"{location}.contract")
    if contract_record != {
        "bytes": 282481,
        "sha256": "2301bcdeffc85f4e6c9c6242591eca9c81af1bcdebbd9da231cf329c908347e2",
    }:
        raise EvidenceError(f"{location}.contract mismatch")

    external = _exact_keys(
        incident["external_authority"],
        {"gate_result", "output_root"},
        f"{location}.external_authority",
    )
    expected_output_root = (
        r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
        r"\s3-q4-final-freeze-correction-7"
    )
    if external["output_root"] != expected_output_root:
        raise EvidenceError(f"{location}.external_authority.output_root mismatch")
    _validate_repository_evidence_record(
        external["gate_result"],
        f"{location}.external_authority.gate_result",
        expected_path=str(Path(expected_output_root) / "gate-result.json"),
        expected_bytes=4382,
        expected_sha256="a752ede1659f9abe57fe1bfc5a41d28134f36627d0a274695dea8fd91dae5c3f",
    )

    expected_failure = {
        "cause": "IGNORED_BYTECODE_CONTAMINATED_FROZEN_SIBLING_INPUT",
        "clean_input_guard_rejected": True,
        "coordinator_exit_code": 1,
        "input_contamination": {
            "complete_file_hashes_available": False,
            "reported_paths": [
                "src/anyfileio/__pycache__/__init__.cpython-313.pyc",
                (
                    "src/anyfileio/__pycache__/"
                    "_semantic_dependencies.cpython-313.pyc"
                ),
                "src/anyfileio/__pycache__/cad.cpython-313.pyc",
            ],
            "repository": (
                r"C:\Github\ANYsolver\.perf2-worktrees"
                r"\s3-q4-anyfileio-9b1e5ad"
            ),
        },
        "lane": "quick",
        "phase": "COMMON_PREFLIGHT_AUTHORITY_CHECK",
        "post_abort_hygiene": {
            "all_six_frozen_repositories_clean_including_ignored": True,
            "generated_bytecode_removed_only": True,
        },
        "quick_command_started": False,
        "resource_commands_started": False,
    }
    if incident["failure"] != expected_failure:
        raise EvidenceError(f"{location}.failure mismatch")

    evidence = _exact_keys(
        incident["preserved_repository_evidence"],
        {"result", "review", "status"},
        f"{location}.preserved_repository_evidence",
    )
    _validate_repository_evidence_record(
        evidence["result"],
        f"{location}.preserved_repository_evidence.result",
        expected_path="docs/reference_cases/e4_pl_s3_q4_blocked_burnin_result.json",
        expected_bytes=4382,
        expected_sha256="a752ede1659f9abe57fe1bfc5a41d28134f36627d0a274695dea8fd91dae5c3f",
    )
    _validate_repository_evidence_record(
        evidence["review"],
        f"{location}.preserved_repository_evidence.review",
        expected_path="docs/reference_cases/e4_pl_s3_q4_blocked_burnin_review.json",
        expected_bytes=536,
        expected_sha256="838a25cb80357c5d995fa40a48735cc2e0eff37d8886bcbb3031f427e94d3746",
    )
    _validate_repository_evidence_record(
        evidence["status"],
        f"{location}.preserved_repository_evidence.status",
        expected_path="docs/reference_cases/e4_pl_s3_q4_blocked_burnin_status.json",
        expected_bytes=293,
        expected_sha256="949bed07b708815a839f6f51e91b329ffb5292217186bc24329158c3d2076414",
    )
    if incident["request_ids"] != list(V8_SUPERSEDED_REQUEST_IDS):
        raise EvidenceError(f"{location}.request_ids mismatch")
    expected_disposition = {
        "preserved_branch": "codex/s3-e4-pl-final-burnin-blocked-attempt-8",
        "request_disposition": "NOT_APPROVED_NOT_CONSUMED_SUPERSEDED",
        "role": "PRESERVED_BLOCKED_PREDECESSOR_ONLY",
        "terminal": "BLOCKED_E4_PL_S3_Q4_BURN_IN_GATE",
    }
    if any(incident[key] != expected for key, expected in expected_disposition.items()):
        raise EvidenceError(f"{location} disposition mismatch")
    return incident


def _validate_attempt_9_incident(value: Any, location: str) -> dict[str, Any]:
    """Bind the recursive-CI quick preflight that was aborted in attempt 9."""

    incident = _exact_keys(
        value,
        {
            "attempt",
            "authority_commit",
            "contract",
            "correction_commit",
            "execution_authorization_commit",
            "external_authority",
            "failure",
            "request_disposition",
            "request_ids",
            "role",
            "terminal",
        },
        location,
    )
    if incident["attempt"] != 9:
        raise EvidenceError(f"{location}.attempt must be 9")
    _validate_git_commit_record(
        incident["authority_commit"],
        f"{location}.authority_commit",
        commit="9109a820dd45d35839c50f27d75593fd9caadadb",
        subject="docs: authorize corrected S3 Q4 burn-in cycles",
        tree="34c299b47dda6215e0d0022efda7b005946c22c7",
    )
    _validate_git_commit_record(
        incident["execution_authorization_commit"],
        f"{location}.execution_authorization_commit",
        commit="06182d7bcfae40a0b0fad827f3b494b53eec0f0a",
        subject="docs: reauthorize corrected S3 Q4 burn-in execution",
        tree="3eed0a4a527364177e6f7a6df108980e26a7903c",
    )
    _validate_git_commit_record(
        incident["correction_commit"],
        f"{location}.correction_commit",
        commit="02a3b101aa5d1d7877eef7b15b6349210e0441cc",
        subject="test: make S3 Q4 CI extent check process-free",
        tree="df3af43a29321a49a119e1bcc1386d1ef92d7bb7",
    )
    contract_record = _exact_keys(
        incident["contract"], {"bytes", "sha256"}, f"{location}.contract"
    )
    _validate_hash_record(contract_record, f"{location}.contract")
    if contract_record != {
        "bytes": 285245,
        "sha256": "9cdea010543f4b6cd712310f713c199626018f1b135f492fca121d07ec31d6f4",
    }:
        raise EvidenceError(f"{location}.contract mismatch")

    external = _exact_keys(
        incident["external_authority"],
        {"output_root", "partial_tree"},
        f"{location}.external_authority",
    )
    if external["output_root"] != (
        r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
        r"\s3-q4-final-freeze-correction-8"
    ):
        raise EvidenceError(f"{location}.external_authority.output_root mismatch")
    expected_partial_tree = {
        "captured_at": "2026-08-26T19:13:19.8920987+02:00",
        "file_count": 185,
        "file_graph_bytes": 40223,
        "file_graph_sha256": (
            "b4e823d8c705834aa36000f265eec03700976cdd6a1c3ad1b77a3ff980fa51f1"
        ),
        "quick_output_file_count": 0,
        "quick_output_reserved": True,
        "started_at": "2026-08-26T18:58:15.9476579+02:00",
        "total_bytes": 14418287,
    }
    partial_tree = _exact_keys(
        external["partial_tree"],
        set(expected_partial_tree),
        f"{location}.external_authority.partial_tree",
    )
    if partial_tree != expected_partial_tree:
        raise EvidenceError(f"{location}.external_authority.partial_tree mismatch")

    expected_failure = {
        "canonical_process_manifest_created": False,
        "cause": "OUTDATED_QUICK_TEST_PATCH_LAUNCHED_RECURSIVE_COMPLETE_CI_WAVE",
        "formal_cycle_started": False,
        "phase": "COMMON_QUICK_PREFLIGHT",
        "quick_command_started": True,
        "resource_requests_approved": False,
        "resource_requests_consumed": False,
        "termination": "USER_DIRECTED_EFFICIENCY_ABORT_AFTER_ROOT_CAUSE_CONFIRMED",
        "worker_tree_confirmed_absent": True,
    }
    failure = _exact_keys(
        incident["failure"], set(expected_failure), f"{location}.failure"
    )
    if failure != expected_failure:
        raise EvidenceError(f"{location}.failure mismatch")
    if incident["request_ids"] != list(V9_SUPERSEDED_REQUEST_IDS):
        raise EvidenceError(f"{location}.request_ids mismatch")
    expected_disposition = {
        "request_disposition": "NOT_APPROVED_NOT_CONSUMED_SUPERSEDED",
        "role": "PRESERVED_BLOCKED_PREDECESSOR_ONLY",
        "terminal": "BLOCKED_E4_PL_S3_Q4_BURN_IN_GATE",
    }
    if any(incident[key] != expected for key, expected in expected_disposition.items()):
        raise EvidenceError(f"{location} disposition mismatch")
    return incident


def _validate_attempt_10_incident(value: Any, location: str) -> dict[str, Any]:
    """Bind the consumed v10 functional pre-launch cleanliness failure."""

    incident = _exact_keys(
        value,
        {
            "attempt",
            "authority_commit",
            "blocked_closeout",
            "contract",
            "execution_authorization_commit",
            "external_authority",
            "failure",
            "preserved_branch",
            "preserved_repository_evidence",
            "request_disposition",
            "request_ids",
            "role",
            "terminal",
        },
        location,
    )
    if incident["attempt"] != 10:
        raise EvidenceError(f"{location}.attempt must be 10")
    _validate_git_commit_record(
        incident["authority_commit"],
        f"{location}.authority_commit",
        commit="f2feeead59bc79471652bf562c3862533e213518",
        subject="docs: authorize corrected S3 Q4 burn-in cycles",
        tree="fcdfd4db6d5016430dd0ddbf3dc7f85c955d38e7",
    )
    _validate_git_commit_record(
        incident["execution_authorization_commit"],
        f"{location}.execution_authorization_commit",
        commit="5244822799feb8a73de636b076099e03a1d68e0b",
        subject="docs: reauthorize corrected S3 Q4 burn-in execution",
        tree="1079fa8d8703db821b3ab322a489e4b9c55dcf73",
    )
    _validate_git_commit_record(
        incident["blocked_closeout"],
        f"{location}.blocked_closeout",
        commit="1e84bcacc539e90941bf718af443b8e34f283c63",
        subject="docs: record blocked corrected S3 Q4 burn-in",
        tree="5c2c9c3256267882b432fc9173de24c131022cb2",
    )
    contract_record = _validate_hash_record(
        incident["contract"], f"{location}.contract"
    )
    if contract_record != {
        "bytes": 287240,
        "sha256": "ae13f921cd79bb2396a220434a3b7056de92a9b471f2d9d48db7f1832d9a1390",
    }:
        raise EvidenceError(f"{location}.contract mismatch")

    external = _exact_keys(
        incident["external_authority"],
        {
            "approval_snapshot",
            "cycle_1_terminal_snapshot",
            "cycle_2_terminal_snapshot",
            "functional",
            "gate_result",
            "output_root",
        },
        f"{location}.external_authority",
    )
    expected_root = (
        r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
        r"\s3-q4-final-freeze-correction-9"
    )
    if external["output_root"] != expected_root:
        raise EvidenceError(f"{location}.external_authority.output_root mismatch")
    for name, filename, size, digest in (
        ("gate_result", "gate-result.json", 10180, "07bb1ed2e8124533494966fa69581f3489e1e14a55213106618b088bdf208f13"),
        ("approval_snapshot", "resource-ledger-approval-snapshot.json", 4420, "03f24368b37cdb1b4b381e1b89720665362e255bebbdb16da126b76e7bada106"),
        ("cycle_1_terminal_snapshot", "resource-ledger-cycle-1-terminal-snapshot.json", 4834, "5de268e9b4817a5b0160839c1ecfc92b49a6129dbc6d690dddee6b469ae03cd9"),
        ("cycle_2_terminal_snapshot", "resource-ledger-cycle-2-terminal-snapshot.json", 3716, "33dae588fb63f79580577efc36a6708a7f3ac95ecc91bfd05364fbb7df6089af"),
    ):
        _validate_repository_evidence_record(
            external[name],
            f"{location}.external_authority.{name}",
            expected_path=str(Path(expected_root) / filename),
            expected_bytes=size,
            expected_sha256=digest,
        )
    functional = _exact_keys(
        external["functional"],
        {"aggregate", "diagnostics", "launch", "pending_manifest", "result", "stderr", "stdout"},
        f"{location}.external_authority.functional",
    )
    functional_records = {
        "launch": ("cycle-1-functional/launch.json", 731, "7e7090125e78e3029be861716ad4021211b8aa78639227ee168bfbba926ed2fc"),
        "pending_manifest": ("cycle-1-functional/pending-manifest.json", 905, "76b033b7400c10f914cd1200aed06e7e33cb8400310fc98eb54d9b8a2366909d"),
        "result": ("cycle-1-functional/result.json", 1130, "d09f9ce0b2b056af6c0ba74b14fe34c7b80b0ab18a73e584d28cac3ee9e672da"),
        "stdout": ("cycle-1-functional/stdout.txt", 1443, "6089cf01578c572400e63bc022ff941a76ae7b8d1c4575760db81380de558658"),
        "stderr": ("cycle-1-functional/stderr.txt", 0, "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
        "aggregate": ("functional-wave/cycle-1/functional-wave-aggregate.json", 1443, "6089cf01578c572400e63bc022ff941a76ae7b8d1c4575760db81380de558658"),
        "diagnostics": ("functional-wave/cycle-1/functional-wave-raw-diagnostics.json", 405, "bc4589567408f6614627b6510c6b6c8f95df1d2e06ab463864303fe74fb2d764"),
    }
    for name, (relative, size, digest) in functional_records.items():
        _validate_repository_evidence_record(
            functional[name],
            f"{location}.external_authority.functional.{name}",
            expected_path=str(Path(expected_root) / Path(relative)),
            expected_bytes=size,
            expected_sha256=digest,
        )

    expected_failure = {
        "cause": "IGNORED_EMPTY_SCRATCH_DIRECTORIES_ESCAPED_PREAPPROVAL_CLEAN_GUARD",
        "clean_cycles_recorded": 0,
        "failed_request": {
            "execution_state": "EXECUTED_ONCE",
            "request_id": V10_SUPERSEDED_REQUEST_IDS[0],
            "status": "COMPLETED_FAIL",
        },
        "other_requests": {
            "acquired": False,
            "request_ids": list(V10_SUPERSEDED_REQUEST_IDS[1:]),
            "status": "CANCELLED_NOT_RUN",
        },
        "phase": "CYCLE_1_FUNCTIONAL_SOURCE_STATUS_BEFORE_SHARD_LAUNCH",
        "recovered_cleanliness": {
            "entries": [
                ".pytest_tmp_beam_validity/",
                ".pytest_tmp_capacity_workflow/",
                ".pytest_tmp_element_qualification/",
                ".pytest_tmp_fe_verification/",
                ".pytest_tmp_fe_verification_family/",
                ".pytest_tmp_mass_modal/",
                ".pytest_tmp_plasticity_qualification/",
                ".pytest_tmp_s4_validity/",
                "reports/external_references/",
            ],
            "entries_verified_empty": True,
            "entries_verified_non_reparse": True,
            "post_status": {
                "bytes": 0,
                "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            },
            "removal": "EXACT_EMPTY_LEAVES_NONRECURSIVE",
        },
        "shards_started": 0,
        "source_status": {
            "bytes": 301,
            "sha256": "827045256df721e866640ffd7abde585f437a5a4f36b1575b57c15d7f3c1b124",
        },
    }
    if incident["failure"] != expected_failure:
        raise EvidenceError(f"{location}.failure mismatch")
    evidence = _exact_keys(
        incident["preserved_repository_evidence"],
        {"result", "review", "status"},
        f"{location}.preserved_repository_evidence",
    )
    for name, size, digest in (
        ("result", 10180, "07bb1ed2e8124533494966fa69581f3489e1e14a55213106618b088bdf208f13"),
        ("review", 536, "fe00aa210da1472272db5cbd2000bdd43b81eba990ef92bc16f12ca25da4b6ef"),
        ("status", 293, "f621dd24cc9265844a1eaebe3c891302af9b997cdb33fe307e2d4751549d203a"),
    ):
        _validate_repository_evidence_record(
            evidence[name],
            f"{location}.preserved_repository_evidence.{name}",
            expected_path=f"docs/reference_cases/e4_pl_s3_q4_blocked_burnin_{name}.json",
            expected_bytes=size,
            expected_sha256=digest,
        )
    if incident["request_ids"] != list(V10_SUPERSEDED_REQUEST_IDS):
        raise EvidenceError(f"{location}.request_ids mismatch")
    expected_disposition = {
        "preserved_branch": "codex/s3-e4-pl-final-burnin-blocked-attempt-10",
        "request_disposition": "ONE_COMPLETED_FAIL_FIVE_CANCELLED_NOT_RUN_SUPERSEDED",
        "role": "PRESERVED_BLOCKED_PREDECESSOR_ONLY",
        "terminal": "BLOCKED_E4_PL_S3_Q4_BURN_IN_GATE",
    }
    if any(incident[key] != expected for key, expected in expected_disposition.items()):
        raise EvidenceError(f"{location} disposition mismatch")
    return incident


def _validate_review_hygiene(value: Any, location: str) -> dict[str, Any]:
    """Require reviews to leave the frozen candidate byte-for-byte clean."""

    hygiene = _exact_keys(
        value,
        {
            "candidate_worktree_mode",
            "post_review_status",
            "pre_review_status",
            "pytest_basetemp",
            "python_cache_prefix",
            "python_invocation",
            "reviewers_must_not_modify_candidate",
            "schema",
        },
        location,
    )
    expected = {
        "candidate_worktree_mode": "DETACHED_CLEAN_REVIEW_WORKTREE",
        "post_review_status": "EXACTLY_MATCHES_PRE_REVIEW",
        "pre_review_status": "CLEAN_INCLUDING_IGNORED",
        "pytest_basetemp": "FRESH_EXTERNAL_DIRECTORY",
        "python_cache_prefix": "FRESH_EXTERNAL_DIRECTORY",
        "python_invocation": ["python", "-B", "-m", "pytest"],
        "reviewers_must_not_modify_candidate": True,
        "schema": "anysolver.e4-pl-s3-q4-review-hygiene-v2",
    }
    if hygiene != expected:
        raise EvidenceError(f"{location} mismatch")
    return hygiene


def _validate_termination_metadata(
    value: Any,
    location: str,
    *,
    bounded: bool,
) -> dict[str, Any] | None:
    if not bounded:
        if value is not None:
            raise EvidenceError(f"{location} must be null for an unbounded local process")
        return None
    termination = _exact_keys(
        value,
        {
            "child_exit_observed",
            "disposition",
            "tree_kill_attempted",
            "tree_kill_exit_code",
            "wall_limit_seconds",
        },
        location,
    )
    disposition = termination["disposition"]
    if disposition not in TIMEOUT_DISPOSITIONS:
        raise EvidenceError(f"{location}.disposition is invalid")
    if (
        _require_int(
            termination["wall_limit_seconds"],
            f"{location}.wall_limit_seconds",
            minimum=1,
        )
        != 1200
    ):
        raise EvidenceError(f"{location}.wall_limit_seconds must be 1200")
    for key in ("child_exit_observed", "tree_kill_attempted"):
        if not isinstance(termination[key], bool):
            raise EvidenceError(f"{location}.{key} must be boolean")
    kill_exit = termination["tree_kill_exit_code"]
    if kill_exit is not None and (
        not isinstance(kill_exit, int) or isinstance(kill_exit, bool)
    ):
        raise EvidenceError(f"{location}.tree_kill_exit_code must be integer or null")
    if disposition == "NORMAL_EXIT":
        if (
            termination["tree_kill_attempted"]
            or kill_exit is not None
            or not termination["child_exit_observed"]
        ):
            raise EvidenceError(f"{location} normal-exit metadata is inconsistent")
    elif disposition == "START_FAILED":
        if (
            termination["tree_kill_attempted"]
            or kill_exit is not None
            or termination["child_exit_observed"]
        ):
            raise EvidenceError(f"{location} pre-start metadata is inconsistent")
    else:
        if not termination["tree_kill_attempted"] or kill_exit is None:
            raise EvidenceError(f"{location} tree-termination metadata is incomplete")
        if disposition.endswith("_TERMINATED") and (
            kill_exit != 0 or not termination["child_exit_observed"]
        ):
            raise EvidenceError(f"{location} successful tree termination is inconsistent")
        if (
            disposition.endswith("_FAILED")
            and kill_exit == 0
            and termination["child_exit_observed"]
        ):
            raise EvidenceError(f"{location} failed tree termination is inconsistent")
    return termination


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
            "background_inputs",
            "candidate_chain",
            "ci_policy",
            "execution",
            "functional_wave",
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
            "execution_authorization_commit",
        },
        "$contract",
    )
    if contract["schema"] != CONTRACT_SCHEMA:
        raise EvidenceError("burn-in contract schema mismatch")
    if contract["study_id"] != (
        "study_e4_pl_s3_q4.corrected_opt_in_release_burnin_v11"
    ):
        raise EvidenceError("burn-in study identity mismatch")
    if not isinstance(contract["non_resource_commands"], dict) or contract[
        "non_resource_commands"
    ].get("output_root") != (
        r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
        r"\s3-q4-final-freeze-correction-10"
    ):
        raise EvidenceError("v11 burn-in output root mismatch")
    execution = _exact_keys(
        contract["execution"],
        {
            "automatic_retry",
            "clean_status_args",
            "clean_status_empty",
            "clean_status_phases",
            "clean_status_scope",
            "common_preflight_before_resources",
            "coordinator_isolated_mode",
            "cycle_wall_policy",
            "environment_guard",
            "fresh_external_logs",
            "gate_git_invocation_policy",
            "global_resource_slot_required",
            "numerical_library_threads",
            "request_execution_policy",
            "resource_approval_authority",
            "resource_cycle_order",
            "resource_lane_order",
            "resource_lanes_serial",
            "stored_commands_exact",
            "timeout_policy",
            "unapproved_timeout_or_resource_wrappers",
        },
        "$contract.execution",
    )
    expected_clean_status_args = [
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignored=matching",
    ]
    expected_clean_status_empty = {
        "bytes": 0,
        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    }
    expected_clean_status_scope = [
        "ANYsolver",
        "ANYfem",
        "ANYfileIO",
        "ANYgeometry",
        "ANYmaterial",
        "ANYmesh",
    ]
    expected_clean_status_phases = [
        "BEFORE_LOCAL_PREFLIGHT_OUTPUT_RESERVATION",
        "BEFORE_APPROVAL_LEDGER_MUTATION",
        "BEFORE_RESOURCE_ACQUIRE_OR_EXECUTION_STARTED",
        "POST_WORKER",
        "FINAL_RESULT_VALIDATION",
    ]
    if execution["clean_status_args"] != expected_clean_status_args:
        raise EvidenceError("strict clean-status arguments mismatch")
    if execution["clean_status_empty"] != expected_clean_status_empty:
        raise EvidenceError("strict clean-status empty-record mismatch")
    if execution["clean_status_scope"] != expected_clean_status_scope:
        raise EvidenceError("strict clean-status repository scope mismatch")
    if execution["clean_status_phases"] != expected_clean_status_phases:
        raise EvidenceError("strict clean-status phase policy mismatch")
    _validate_timeout_policy(
        execution["timeout_policy"], "$contract.execution.timeout_policy"
    )
    _validate_cycle_wall_policy(
        execution["cycle_wall_policy"], "$contract.execution.cycle_wall_policy"
    )
    _validate_request_execution_policy(
        execution["request_execution_policy"],
        "$contract.execution.request_execution_policy",
    )
    _validate_gate_git_invocation_policy(
        execution["gate_git_invocation_policy"],
        "$contract.execution.gate_git_invocation_policy",
    )
    validate_functional_wave_contract(contract)
    _validate_ci_policy(contract["ci_policy"], contract, "$contract.ci_policy")
    background = _exact_keys(
        contract["background_inputs"],
        {
            "attachment",
            "base",
            "failed_ci_partition_review_attempt",
            "failed_common_preflight_attempt",
            "failed_git_probe_review_attempt",
            "failed_preflight_attempt",
            "failed_resource_acquisition_attempt",
            "failed_resource_interruption_attempt",
            "failed_review_contamination_attempt",
            "failed_recursive_ci_quick_preflight_attempt",
            "failed_sibling_hygiene_preflight_attempt",
            "failed_v10_functional_cleanliness_attempt",
            "paused_checkpoint",
        },
        "$contract.background_inputs",
    )
    interruption = _validate_attempt_4_incident(
        background["failed_resource_interruption_attempt"],
        "$contract.background_inputs.failed_resource_interruption_attempt",
    )
    review_contamination = _validate_attempt_5_incident(
        background["failed_review_contamination_attempt"],
        "$contract.background_inputs.failed_review_contamination_attempt",
    )
    git_probe_review = _validate_attempt_6_incident(
        background["failed_git_probe_review_attempt"],
        "$contract.background_inputs.failed_git_probe_review_attempt",
    )
    ci_partition_review = _validate_attempt_7_incident(
        background["failed_ci_partition_review_attempt"],
        "$contract.background_inputs.failed_ci_partition_review_attempt",
    )
    sibling_hygiene_preflight = _validate_attempt_8_incident(
        background["failed_sibling_hygiene_preflight_attempt"],
        "$contract.background_inputs.failed_sibling_hygiene_preflight_attempt",
    )
    recursive_ci_quick_preflight = _validate_attempt_9_incident(
        background["failed_recursive_ci_quick_preflight_attempt"],
        "$contract.background_inputs.failed_recursive_ci_quick_preflight_attempt",
    )
    v10_functional_cleanliness = _validate_attempt_10_incident(
        background["failed_v10_functional_cleanliness_attempt"],
        "$contract.background_inputs.failed_v10_functional_cleanliness_attempt",
    )
    requests = _exact_keys(
        contract["resource_requests"],
        {"cycle_1", "cycle_2"},
        "$contract.resource_requests",
    )
    current_request_ids: list[Any] = []
    for cycle_name in ("cycle_1", "cycle_2"):
        rows = requests[cycle_name]
        if not isinstance(rows, list) or len(rows) != 3:
            raise EvidenceError(f"$contract.resource_requests.{cycle_name} is malformed")
        for row in rows:
            if not isinstance(row, dict):
                raise EvidenceError(
                    f"$contract.resource_requests.{cycle_name} contains a non-object"
                )
            current_request_ids.append(row.get("request_id"))
    if len(current_request_ids) != 6 or any(
        not isinstance(request_id, str)
        or not REQUEST_ID_RE.fullmatch(request_id)
        for request_id in current_request_ids
    ):
        raise EvidenceError("v11 resource request IDs are incomplete or malformed")
    if len(set(current_request_ids)) != 6:
        raise EvidenceError("v11 resource request IDs are not unique")
    if current_request_ids != list(V11_REQUEST_IDS):
        raise EvidenceError("v11 resource request IDs differ from frozen authority")
    historical_request_ids: set[str] = {
        *interruption["request_ids"],
        *review_contamination["request_ids"],
        *git_probe_review["request_ids"],
        *ci_partition_review["request_ids"],
        *sibling_hygiene_preflight["request_ids"],
        *recursive_ci_quick_preflight["request_ids"],
        *v10_functional_cleanliness["request_ids"],
    }
    for incident_name, request_key in (
        ("failed_preflight_attempt", "resource_request_ids"),
        ("failed_resource_acquisition_attempt", "request_ids"),
        ("failed_common_preflight_attempt", "request_ids"),
    ):
        prior = background[incident_name]
        if not isinstance(prior, dict):
            raise EvidenceError(f"$contract.background_inputs.{incident_name} is malformed")
        request_ids = _require_ordered_unique_strings(
            prior.get(request_key),
            f"$contract.background_inputs.{incident_name}.{request_key}",
            expected_count=6,
        )
        if any(not REQUEST_ID_RE.fullmatch(request_id) for request_id in request_ids):
            raise EvidenceError(
                f"$contract.background_inputs.{incident_name}.{request_key} is malformed"
            )
        historical_request_ids.update(request_ids)
    if set(current_request_ids) & historical_request_ids:
        raise EvidenceError("v11 resource request IDs reuse historical authority")
    runner_inputs = _exact_keys(
        contract["runner_inputs"],
        {
            "burnin_runner",
            "evidence_validator",
            "performance_measurement",
            "process_runner",
        },
        "$contract.runner_inputs",
    )
    for name in ("evidence_validator", "performance_measurement", "process_runner"):
        item = _exact_keys(
            runner_inputs[name],
            {"bytes", "path", "sha256"},
            f"$contract.runner_inputs.{name}",
        )
        _validate_hash_record(
            {"bytes": item["bytes"], "sha256": item["sha256"]},
            f"$contract.runner_inputs.{name}",
        )
        _require_string(item["path"], f"$contract.runner_inputs.{name}.path")
    burnin_runner = _exact_keys(
        runner_inputs["burnin_runner"],
        {"canonical_lf", "path", "working_tree_identities"},
        "$contract.runner_inputs.burnin_runner",
    )
    _validate_hash_record(
        burnin_runner["canonical_lf"],
        "$contract.runner_inputs.burnin_runner.canonical_lf",
    )
    if burnin_runner["path"] != "scripts/run_e4_pl_burnin_gate.py":
        raise EvidenceError("burn-in runner path mismatch")
    identities = burnin_runner["working_tree_identities"]
    if (
        not isinstance(identities, list)
        or len(identities) != 2
        or [item.get("line_endings") for item in identities if isinstance(item, dict)]
        != ["LF", "CRLF"]
    ):
        raise EvidenceError("burn-in runner LF/CRLF identities are malformed")
    for index, item in enumerate(identities):
        value = _exact_keys(
            item,
            {"bytes", "line_endings", "sha256"},
            f"$contract.runner_inputs.burnin_runner.working_tree_identities[{index}]",
        )
        _validate_hash_record(
            {"bytes": value["bytes"], "sha256": value["sha256"]},
            f"$contract.runner_inputs.burnin_runner.working_tree_identities[{index}]",
        )
    authority = _exact_keys(
        contract["authority_commit"],
        {"exact_parent", "exact_paths", "path_count", "subject"},
        "$contract.authority_commit",
    )
    if authority["exact_parent"] != "1e84bcacc539e90941bf718af443b8e34f283c63":
        raise EvidenceError("burn-in authority parent mismatch")
    expected_authority_paths = [
        "docs/reference_cases/e4_pl_s3_q4_burnin.py",
        "docs/reference_cases/e4_pl_s3_q4_burnin_contract.json",
        "docs/reference_cases/e4_pl_s3_q4_process_runner.py",
        "scripts/run_e4_pl_burnin_gate.py",
        "tests/test_e4_pl_s3_q4_burnin_authority.py",
    ]
    if authority["exact_paths"] != expected_authority_paths or authority["path_count"] != 5:
        raise EvidenceError("burn-in authority extent mismatch")
    authorization = _exact_keys(
        contract["execution_authorization_commit"],
        {
            "approval_path",
            "approval_schema",
            "exact_parent_role",
            "exact_paths",
            "path_count",
            "review_hygiene",
            "review_paths",
            "review_schema",
            "review_verdict",
            "subject",
        },
        "$contract.execution_authorization_commit",
    )
    if (
        authorization["exact_parent_role"] != "DERIVED_AUTHORITY_COMMIT"
        or authorization["path_count"] != 3
        or authorization["exact_paths"]
        != [*authorization["review_paths"], authorization["approval_path"]]
        or len(set(authorization["exact_paths"])) != 3
    ):
        raise EvidenceError("execution authorization extent is malformed")
    _validate_review_hygiene(
        authorization["review_hygiene"],
        "$contract.execution_authorization_commit.review_hygiene",
    )
    return contract


def execution_tool_path(contract: Mapping[str, Any], name: str) -> Path:
    if name not in {"git", "git_engine", "powershell", "python"}:
        raise EvidenceError(f"unknown frozen execution tool: {name}")
    guard = _exact_keys(
        contract["execution"]["environment_guard"],
        {
            "fixed",
            "git",
            "git_engine",
            "git_runtime",
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
    if resolved != path or path.is_symlink() or is_reparse_point(path) or file_hash_record(path) != {
        "bytes": record["bytes"],
        "sha256": record["sha256"],
    }:
        raise EvidenceError(f"frozen {name} executable identity mismatch")
    return path


def validate_git_runtime(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Bind the Git launcher, native engine, build identity, and exec path."""

    launcher = execution_tool_path(contract, "git")
    execution_tool_path(contract, "git_engine")
    guard = contract["execution"]["environment_guard"]
    runtime = _exact_keys(
        guard["git_runtime"],
        {"build_options", "exec_path", "exec_path_output"},
        "$contract.execution.environment_guard.git_runtime",
    )
    environment = sanitized_execution_environment(contract)
    observed: dict[str, bytes] = {}
    for name, arguments in (
        ("build_options", ("--version", "--build-options")),
        ("exec_path_output", ("--exec-path",)),
    ):
        completed = subprocess.run(
            [str(launcher), *arguments],
            capture_output=True,
            check=False,
            env=environment,
        )
        if completed.returncode or completed.stderr:
            raise EvidenceError(f"Git {name} identity probe failed")
        expected = _validate_hash_record(runtime[name], f"$contract.git_runtime.{name}")
        if {"bytes": len(completed.stdout), "sha256": sha256_bytes(completed.stdout)} != expected:
            raise EvidenceError(f"Git {name} identity mismatch")
        observed[name] = completed.stdout
    exec_path = observed["exec_path_output"].decode("utf-8").strip().replace("\\", "/")
    if exec_path != runtime["exec_path"]:
        raise EvidenceError("Git exec path mismatch")
    return dict(runtime)


def sanitized_execution_environment(contract: Mapping[str, Any]) -> dict[str, str]:
    guard = _exact_keys(
        contract["execution"]["environment_guard"],
        {
            "fixed",
            "git",
            "git_engine",
            "git_runtime",
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
            "approval_snapshot",
            "command_sha256",
            "elapsed_seconds",
            "ended_at",
            "execution_state",
            "exit_code",
            "producer_sha256",
            "pending_manifest_sha256",
            "request_id",
            "resource_lock_released",
            "result",
            "started_at",
            "status",
            "stderr",
            "stdout",
            "termination",
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
        if process["approval_snapshot"] is not None or process["pending_manifest_sha256"] is not None:
            raise EvidenceError(f"{location} local process may not bind resource authority")
    elif not isinstance(lock_released, bool):
        raise EvidenceError(f"{location}.resource_lock_released must be boolean")
    else:
        _validate_hash_record(process["approval_snapshot"], f"{location}.approval_snapshot")
        _require_hash(
            process["pending_manifest_sha256"],
            f"{location}.pending_manifest_sha256",
        )
    if process["execution_state"] not in {"EXECUTED", "NOT_STARTED"}:
        raise EvidenceError(f"{location}.execution_state is invalid")
    termination = _validate_termination_metadata(
        process["termination"],
        f"{location}.termination",
        bounded=True,
    )
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
    exit_code = process["exit_code"]
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        raise EvidenceError(f"{location}.exit_code must be an integer")
    if termination is None:  # Defensive: executed v3 process records are bounded.
        raise EvidenceError(f"{location}.termination may not be null")
    disposition = termination["disposition"]
    if disposition == "START_FAILED":
        if exit_code == 0 or process["execution_state"] != "NOT_STARTED":
            raise EvidenceError(f"{location} pre-start termination mismatch")
    elif disposition == "NORMAL_EXIT":
        if process["execution_state"] != "EXECUTED":
            raise EvidenceError(f"{location} normal termination mismatch")
    elif disposition.startswith("TIMEOUT_"):
        if exit_code != 124 or process["execution_state"] != "EXECUTED":
            raise EvidenceError(f"{location} timeout termination mismatch")
    elif process["execution_state"] != "EXECUTED":
        raise EvidenceError(f"{location} interrupted termination mismatch")
    if (status == "PASS") != (
        exit_code == 0
        and process["execution_state"] == "EXECUTED"
        and (expected_request_id is None or lock_released is True)
        and termination["disposition"] == "NORMAL_EXIT"
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
            "ledger_snapshots",
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
    snapshots = _exact_keys(
        record["ledger_snapshots"], {"approval", "cycle_1", "cycle_2"}, "$.ledger_snapshots"
    )
    common_preflight_passed = all(
        common[name]["status"] == "PASS" for name in ("quick", "package", "additive")
    )
    if common_preflight_passed:
        for name in ("approval", "cycle_1", "cycle_2"):
            _validate_hash_record(snapshots[name], f"$.ledger_snapshots.{name}")
    elif any(snapshots[name] is not None for name in ("approval", "cycle_1", "cycle_2")):
        raise EvidenceError("failed common preflight forbids resource ledger snapshots")
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
            "core.attributesFile=NUL",
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


def strict_clean_status_record(
    path: Path, *, contract: Mapping[str, Any]
) -> dict[str, Any]:
    """Return and verify the frozen raw-byte complete Git cleanliness record."""

    path = path.resolve(strict=True)
    execution = contract["execution"]
    arguments = execution["clean_status_args"]
    expected = execution["clean_status_empty"]
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
            "core.attributesFile=NUL",
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
            *arguments,
        ],
        capture_output=True,
        env=sanitized_execution_environment(contract),
        check=False,
    )
    if completed.returncode:
        raise EvidenceError(f"strict clean-status Git probe failed for {path}")
    observed = {
        "bytes": len(completed.stdout),
        "sha256": sha256_bytes(completed.stdout),
    }
    if observed != expected:
        raise EvidenceError(f"execution repository is not completely clean: {path}")
    return observed


def assert_clean_execution_repository(path: Path, *, contract: Mapping[str, Any]) -> None:
    path = path.resolve(strict=True)
    validate_git_runtime(contract)
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
    strict_clean_status_record(path, contract=contract)
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
    common_git_dir = Path(
        _git(path, "rev-parse", "--git-common-dir", contract=contract)
    )
    if not common_git_dir.is_absolute():
        common_git_dir = path / common_git_dir
    graft_path = common_git_dir / "info" / "grafts"
    if graft_path.exists() or graft_path.is_symlink():
        raise EvidenceError(f"Git graft metadata is forbidden: {path}")
    attributes_path = common_git_dir / "info" / "attributes"
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
    unregistered = sorted(
        name
        for name in set(untracked.split("\0")) | set(ignored.split("\0"))
        if name
    )
    if unregistered:
        raise EvidenceError(
            f"untracked/ignored execution paths are forbidden: {unregistered[:3]}"
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
            "approval_snapshot",
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
            "termination",
        },
        "$process_result",
    )
    expected_request_id = None if request is None else request["request_id"]
    expected_request_sha256 = None if request is None else request["request_sha256"]
    expected_lock = process["resource_lock_released"]
    expected = {
        "approval_snapshot": process["approval_snapshot"],
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
        "termination": process["termination"],
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


def execution_started_ledger_fields(
    request: Mapping[str, Any],
    launch: Mapping[str, Any],
    launch_record: Mapping[str, Any],
) -> list[str]:
    _validate_hash_record(launch_record, "launch_record")
    return [
        request["request_id"],
        "EXECUTION_STARTED",
        request["task"],
        request["repository"],
        "Exact immutable request launch committed",
        f"{request['estimate_minutes']} minutes",
        (
            f"Launch bytes {launch_record['bytes']} SHA-256 "
            f"{launch_record['sha256'].upper()}; candidate "
            f"{launch['candidate']['commit']}; tree {launch['candidate']['tree']}; "
            f"cycle {launch['cycle']}; lane {launch['lane']}."
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
    pending_manifest_sha256 = _require_hash(
        process.get("pending_manifest_sha256"), "process.pending_manifest_sha256"
    )
    termination = _validate_termination_metadata(
        process.get("termination"), "process.termination", bounded=True
    )
    assert termination is not None
    status = "COMPLETED_PASS" if process["status"] == "PASS" else "COMPLETED_FAIL"
    note = (
        f"Candidate {process['candidate_commit']}; tree {process['candidate_tree']}; "
        f"exit {process['exit_code']}; result bytes {result_record['bytes']} SHA-256 "
        f"{result_record['sha256'].upper()}; stdout bytes {process['stdout']['bytes']} "
        f"SHA-256 {process['stdout']['sha256'].upper()}; stderr bytes "
        f"{process['stderr']['bytes']} SHA-256 {process['stderr']['sha256'].upper()}; "
        f"elapsed {process['elapsed_seconds']:.6f}s; lock released "
        f"{process['resource_lock_released']}; execution state "
        f"{process['execution_state']}; pending manifest SHA-256 "
        f"{pending_manifest_sha256.upper()}."
        f" termination {termination['disposition']}; wall limit "
        f"{termination['wall_limit_seconds']}s; tree kill attempted "
        f"{termination['tree_kill_attempted']}; tree kill exit "
        f"{termination['tree_kill_exit_code']}; child exit observed "
        f"{termination['child_exit_observed']}."
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


def validate_superseded_request_ledger_absence(
    ledger: str, *, contract: Mapping[str, Any] | None = None
) -> None:
    """Require rejected review-only request IDs to have no ledger row of any kind."""

    contract = dict(contract or load_contract())
    for incident_name in (
        "failed_git_probe_review_attempt",
        "failed_ci_partition_review_attempt",
    ):
        incident = contract["background_inputs"][incident_name]
        expected = _require_int(
            incident["ledger_occurrences"],
            f"$contract.background_inputs.{incident_name}.ledger_occurrences",
            minimum=0,
        )
        occurrences = sum(
            ledger.count(request_id) for request_id in incident["request_ids"]
        )
        if occurrences != expected or expected != 0:
            raise EvidenceError(
                f"rejected request ID from {incident_name} occurs in the resource ledger"
            )
    for incident_name in (
        "failed_sibling_hygiene_preflight_attempt",
        "failed_recursive_ci_quick_preflight_attempt",
    ):
        superseded = contract["background_inputs"][incident_name]
        if any(request_id in ledger for request_id in superseded["request_ids"]):
            raise EvidenceError(
                f"superseded request ID from {incident_name} occurs in the resource ledger"
            )
    v10 = contract["background_inputs"]["failed_v10_functional_cleanliness_attempt"]
    expected_sequences = [
        ["APPROVED", "EXECUTION_STARTED", "COMPLETED_FAIL"],
        *([["APPROVED", "CANCELLED_NOT_RUN"]] * 5),
    ]
    for request_id, expected_sequence in zip(
        v10["request_ids"], expected_sequences, strict=True
    ):
        observed_sequence: list[str] = []
        for line in ledger.splitlines():
            if not line.startswith("|") or not line.endswith("|"):
                continue
            fields = [field.strip() for field in line.split("|")[1:-1]]
            if len(fields) == 8 and fields[1] == request_id:
                _require_timestamp(fields[0], f"ledger {request_id} timestamp")
                observed_sequence.append(fields[2])
        if observed_sequence != expected_sequence:
            raise EvidenceError(
                "v10 superseded request terminal ledger disposition mismatch"
            )


def _require_successor_after_terminal(
    started_at: dt.datetime,
    previous_terminal: dt.datetime | None,
    request_id: str,
) -> None:
    if previous_terminal is not None and started_at < previous_terminal:
        raise EvidenceError(
            f"resource successor starts before predecessor terminal: {request_id}"
        )


def validate_execution_authorization(
    candidate_path: Path,
    *,
    contract: Mapping[str, Any] | None = None,
    require_successor: bool = True,
) -> dict[str, Any]:
    """Validate the self-reference-free authority and its reviewed successor."""

    contract = dict(contract or load_contract())
    candidate_path = candidate_path.resolve(strict=True)
    authority = contract["authority_commit"]
    authority_commits = _git(
        candidate_path,
        "log",
        "-1",
        "--format=%H",
        "--",
        "docs/reference_cases/e4_pl_s3_q4_burnin_contract.json",
        contract=contract,
    ).splitlines()
    if len(authority_commits) != 1:
        raise EvidenceError("burn-in contract does not have one latest authority commit")
    authority_commit = authority_commits[0]
    metadata = _git(
        candidate_path,
        "show",
        "-s",
        "--format=%P%n%s",
        authority_commit,
        contract=contract,
    ).splitlines()
    if metadata != [authority["exact_parent"], authority["subject"]]:
        raise EvidenceError("derived authority parent or subject mismatch")
    paths = _git(
        candidate_path,
        "diff",
        "--name-only",
        authority["exact_parent"],
        authority_commit,
        contract=contract,
    ).splitlines()
    if paths != authority["exact_paths"] or len(paths) != authority["path_count"]:
        raise EvidenceError("derived authority changed-path extent mismatch")
    authority_tree = _git(
        candidate_path, "rev-parse", f"{authority_commit}^{{tree}}", contract=contract
    )
    head = _git(candidate_path, "rev-parse", "HEAD", contract=contract)
    head_tree = _git(candidate_path, "rev-parse", "HEAD^{tree}", contract=contract)
    if not require_successor and head == authority_commit:
        return {
            "authority_commit": authority_commit,
            "authority_tree": authority_tree,
            "candidate_commit": head,
            "candidate_tree": head_tree,
            "reviews": None,
        }
    successor = contract["execution_authorization_commit"]
    head_metadata = _git(
        candidate_path, "show", "-s", "--format=%P%n%s", head, contract=contract
    ).splitlines()
    if head_metadata != [authority_commit, successor["subject"]]:
        raise EvidenceError("execution authorization parent or subject mismatch")
    head_paths = _git(
        candidate_path,
        "diff",
        "--name-only",
        authority_commit,
        head,
        contract=contract,
    ).splitlines()
    if head_paths != successor["exact_paths"] or len(head_paths) != successor["path_count"]:
        raise EvidenceError("execution authorization changed-path extent mismatch")

    contract_path = candidate_path / "docs/reference_cases/e4_pl_s3_q4_burnin_contract.json"
    contract_sha256 = file_hash_record(contract_path)["sha256"]
    expected_reviewed_inputs = {
        "attachment_sha256": contract["background_inputs"]["attachment"]["sha256"],
        "authority_commit": authority_commit,
        "authority_tree": authority_tree,
        "base_commit": contract["background_inputs"]["base"]["commit"],
        "checkpoint_commit": contract["background_inputs"]["paused_checkpoint"]["commit"],
        "contract_sha256": contract_sha256,
    }
    reviews: list[dict[str, Any]] = []
    review_records: dict[str, dict[str, Any]] = {}
    reviewer_ids: set[str] = set()
    for index, relative in enumerate(successor["review_paths"], start=1):
        path = candidate_path / relative
        raw = path.read_bytes()
        review = strict_json_loads(raw)
        if raw != canonical_json_bytes(review):
            raise EvidenceError(f"authority review {index} is not canonical JSON")
        review = _exact_keys(
            review,
            {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"},
            f"$authority_review[{index}]",
        )
        if (
            review["schema"] != successor["review_schema"]
            or review["verdict"] != successor["review_verdict"]
            or review["findings"] != []
            or review["reviewed_inputs"] != expected_reviewed_inputs
        ):
            raise EvidenceError(f"authority review {index} contents mismatch")
        independence = _exact_keys(
            review["reviewer_independence"],
            {
                "did_not_author_candidate",
                "did_not_execute_resource_lanes",
                "independent_of_other_reviewer",
                "reviewer_id",
            },
            f"$authority_review[{index}].reviewer_independence",
        )
        if any(independence[key] is not True for key in (
            "did_not_author_candidate",
            "did_not_execute_resource_lanes",
            "independent_of_other_reviewer",
        )):
            raise EvidenceError(f"authority review {index} is not independent")
        reviewer_id = _require_string(independence["reviewer_id"], "reviewer_id")
        if reviewer_id in reviewer_ids:
            raise EvidenceError("authority reviewer identities must be distinct")
        reviewer_ids.add(reviewer_id)
        reviews.append(review)
        review_records[f"review_{index}"] = file_hash_record(path)

    approval_path = candidate_path / successor["approval_path"]
    approval_raw = approval_path.read_bytes()
    approval = strict_json_loads(approval_raw)
    if approval_raw != canonical_json_bytes(approval):
        raise EvidenceError("execution authorization is not canonical JSON")
    approval = _exact_keys(
        approval,
        {"authority", "request_ids", "review_hashes", "schema", "user_approval"},
        "$execution_authorization",
    )
    expected_ids = [
        row["request_id"]
        for cycle in ("cycle_1", "cycle_2")
        for row in contract["resource_requests"][cycle]
    ]
    if (
        approval["schema"] != successor["approval_schema"]
        or approval["authority"]
        != {"commit": authority_commit, "tree": authority_tree}
        or approval["request_ids"] != expected_ids
        or approval["review_hashes"] != review_records
        or approval["user_approval"]
        != {
            "source": "EXPLICIT_USER_APPROVAL_IN_THIS_CODEX_TASK",
            "statement": "I approve. Also for future requests required to finish the job.",
        }
    ):
        raise EvidenceError("execution authorization contents mismatch")
    return {
        "authority_commit": authority_commit,
        "authority_tree": authority_tree,
        "candidate_commit": head,
        "candidate_tree": head_tree,
        "reviews": reviews,
    }


def _validate_snapshot_row(value: Any, location: str) -> dict[str, Any]:
    row = _exact_keys(value, {"fields", "timestamp"}, location)
    _require_timestamp(row["timestamp"], f"{location}.timestamp")
    if (
        not isinstance(row["fields"], list)
        or len(row["fields"]) != 7
        or any(not isinstance(field, str) or not field for field in row["fields"])
    ):
        raise EvidenceError(f"{location}.fields must contain seven nonempty strings")
    return row


def validate_ledger_snapshot(
    value: Any, *, contract: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    """Validate a filtered immutable approval or cycle-terminal ledger snapshot."""

    contract = dict(contract or load_contract())
    snapshot = _exact_keys(
        value,
        (
            {"candidate", "kind", "request_order", "rows", "schema", "source_ledger"}
            if isinstance(value, dict) and value.get("kind") == "APPROVAL"
            else {
                "candidate",
                "cycle",
                "kind",
                "predecessor",
                "request_order",
                "rows",
                "schema",
                "source_ledger",
            }
        ),
        "$ledger_snapshot",
    )
    if snapshot["schema"] != LEDGER_SNAPSHOT_SCHEMA:
        raise EvidenceError("ledger snapshot schema mismatch")
    candidate = _exact_keys(snapshot["candidate"], {"commit", "tree"}, "$.candidate")
    for key in ("commit", "tree"):
        if not isinstance(candidate[key], str) or not GIT_OBJECT_RE.fullmatch(candidate[key]):
            raise EvidenceError(f"ledger snapshot candidate {key} is invalid")
    _validate_hash_record(snapshot["source_ledger"], "$.source_ledger")
    all_ids = [
        row["request_id"]
        for cycle in ("cycle_1", "cycle_2")
        for row in contract["resource_requests"][cycle]
    ]
    kind = snapshot["kind"]
    if kind == "APPROVAL":
        expected_ids = all_ids
        if snapshot["request_order"] != expected_ids:
            raise EvidenceError("approval snapshot request ordering mismatch")
        if not isinstance(snapshot["rows"], list) or len(snapshot["rows"]) != 6:
            raise EvidenceError("approval snapshot must contain six rows")
        rows = [
            _validate_snapshot_row(row, f"$.rows[{index}]")
            for index, row in enumerate(snapshot["rows"])
        ]
        if [row["fields"][0] for row in rows] != expected_ids or any(
            row["fields"][1] != "APPROVED" for row in rows
        ):
            raise EvidenceError("approval snapshot rows mismatch")
        return snapshot
    if kind != "CYCLE_TERMINAL" or snapshot.get("cycle") not in {1, 2}:
        raise EvidenceError("ledger snapshot kind/cycle mismatch")
    cycle = int(snapshot["cycle"])
    expected_ids = [
        row["request_id"] for row in contract["resource_requests"][f"cycle_{cycle}"]
    ]
    if snapshot["request_order"] != expected_ids:
        raise EvidenceError("cycle snapshot request ordering mismatch")
    _validate_hash_record(snapshot["predecessor"], "$.predecessor")
    if not isinstance(snapshot["rows"], list) or len(snapshot["rows"]) != 3:
        raise EvidenceError("cycle snapshot must contain three request rows")
    for index, (request_id, item) in enumerate(zip(expected_ids, snapshot["rows"], strict=True)):
        item = _exact_keys(
            item,
            {"approval", "execution_started", "terminal"},
            f"$.rows[{index}]",
        )
        approval = _validate_snapshot_row(item["approval"], f"$.rows[{index}].approval")
        terminal = _validate_snapshot_row(item["terminal"], f"$.rows[{index}].terminal")
        if approval["fields"][:2] != [request_id, "APPROVED"]:
            raise EvidenceError("cycle snapshot approval row mismatch")
        terminal_status = terminal["fields"][1]
        if terminal["fields"][0] != request_id or terminal_status not in {
            "COMPLETED_PASS",
            "COMPLETED_FAIL",
            "CANCELLED_NOT_RUN",
        }:
            raise EvidenceError("cycle snapshot terminal row mismatch")
        started = item["execution_started"]
        if terminal_status == "CANCELLED_NOT_RUN":
            if started is not None:
                raise EvidenceError("cancelled request may not have an execution-start row")
        else:
            started = _validate_snapshot_row(started, f"$.rows[{index}].execution_started")
            if started["fields"][:2] != [request_id, "EXECUTION_STARTED"]:
                raise EvidenceError("cycle snapshot execution-start row mismatch")
            if "pending manifest SHA-256" not in terminal["fields"][6]:
                raise EvidenceError("cycle terminal does not bind its pending manifest")
    return snapshot


def validate_pending_manifest(
    value: Any, *, contract: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    contract = dict(contract or load_contract())
    manifest = _exact_keys(
        value,
        {
            "approval_snapshot",
            "candidate",
            "cycle",
            "lane",
            "launch",
            "request",
            "result",
            "schema",
            "stderr",
            "stdout",
            "target_directory",
        },
        "$pending_manifest",
    )
    if manifest["schema"] != PENDING_MANIFEST_SCHEMA:
        raise EvidenceError("pending manifest schema mismatch")
    for key in ("approval_snapshot", "launch", "result", "stderr", "stdout"):
        _validate_hash_record(manifest[key], f"$.{key}")
    candidate = _exact_keys(manifest["candidate"], {"commit", "tree"}, "$.candidate")
    for key in ("commit", "tree"):
        if not isinstance(candidate[key], str) or not GIT_OBJECT_RE.fullmatch(candidate[key]):
            raise EvidenceError(f"pending manifest candidate {key} is invalid")
    request = _exact_keys(
        manifest["request"], {"bytes", "request_id", "sha256"}, "$.request"
    )
    _require_int(request["bytes"], "$.request.bytes", minimum=1)
    _require_hash(request["sha256"], "$.request.sha256")
    if not REQUEST_ID_RE.fullmatch(_require_string(request["request_id"], "$.request.request_id")):
        raise EvidenceError("pending manifest request ID is invalid")
    if manifest["cycle"] not in {1, 2} or manifest["lane"] not in {
        "functional", "anyfem", "performance"
    }:
        raise EvidenceError("pending manifest cycle/lane is invalid")
    expected = _request_table(contract)[(manifest["cycle"], manifest["lane"])]
    if request != {
        "bytes": expected["bytes"],
        "request_id": expected["request_id"],
        "sha256": expected["request_sha256"],
    }:
        raise EvidenceError("pending manifest request authority mismatch")
    target = _require_string(manifest["target_directory"], "$.target_directory")
    prefix = f"cycle_{manifest['cycle']}.{manifest['lane']}"
    if target != PROCESS_DIRECTORY_NAMES[prefix]:
        raise EvidenceError("pending manifest target directory mismatch")
    return manifest


def validate_resource_launch(
    value: Any, *, contract: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    contract = dict(contract or load_contract())
    launch = _exact_keys(
        value,
        {
            "approval_snapshot",
            "candidate",
            "command_sha256",
            "cycle",
            "lane",
            "lock_owner",
            "request",
            "schema",
            "started_at",
            "target_directory",
        },
        "$resource_launch",
    )
    if launch["schema"] != "anysolver.e4-pl-s3-q4-resource-launch-v1":
        raise EvidenceError("resource launch schema mismatch")
    for key in ("approval_snapshot", "lock_owner"):
        _validate_hash_record(launch[key], f"$.{key}")
    candidate = _exact_keys(launch["candidate"], {"commit", "tree"}, "$.candidate")
    for key in ("commit", "tree"):
        if not isinstance(candidate[key], str) or not GIT_OBJECT_RE.fullmatch(candidate[key]):
            raise EvidenceError(f"resource launch candidate {key} is invalid")
    _require_hash(launch["command_sha256"], "$.command_sha256")
    _require_timestamp(launch["started_at"], "$.started_at")
    request = _exact_keys(
        launch["request"], {"bytes", "request_id", "sha256"}, "$.request"
    )
    _require_int(request["bytes"], "$.request.bytes", minimum=1)
    _require_hash(request["sha256"], "$.request.sha256")
    if launch["cycle"] not in {1, 2} or launch["lane"] not in {
        "functional", "anyfem", "performance"
    }:
        raise EvidenceError("resource launch cycle/lane is invalid")
    expected = _request_table(contract)[(launch["cycle"], launch["lane"])]
    if request != {
        "bytes": expected["bytes"],
        "request_id": expected["request_id"],
        "sha256": expected["request_sha256"],
    } or launch["command_sha256"] != expected["command_sha256"]:
        raise EvidenceError("resource launch request authority mismatch")
    if launch["target_directory"] != PROCESS_DIRECTORY_NAMES[
        f"cycle_{launch['cycle']}.{launch['lane']}"
    ]:
        raise EvidenceError("resource launch target directory mismatch")
    return launch


def load_bound_ledger_snapshots(
    record: Mapping[str, Any], *, contract: Mapping[str, Any]
) -> tuple[dict[str, dict[str, Any]], dict[str, Path], str]:
    common_passed = all(
        record["common_lanes"][name]["status"] == "PASS"
        for name in ("quick", "package", "additive")
    )
    records = record["ledger_snapshots"]
    if not common_passed:
        if records != {"approval": None, "cycle_1": None, "cycle_2": None}:
            raise EvidenceError("failed common preflight ledger snapshot mismatch")
        return {}, {}, ""
    snapshot_names = {
        "approval": contract["adjudication"]["approval_snapshot_filename"],
        **contract["adjudication"]["cycle_terminal_snapshot_filenames"],
    }
    values: dict[str, dict[str, Any]] = {}
    paths: dict[str, Path] = {}
    for name in ("approval", "cycle_1", "cycle_2"):
        filename = _require_string(snapshot_names[name], f"$contract.snapshot.{name}")
        if Path(filename).name != filename:
            raise EvidenceError("resource ledger snapshot must be a basename")
        path = output_root(contract) / filename
        require_regular_file(path, nonempty=True)
        if file_hash_record(path) != records[name]:
            raise EvidenceError(f"immutable resource ledger snapshot mismatch: {name}")
        raw = path.read_bytes()
        value = strict_json_loads(raw)
        if raw != canonical_json_bytes(value):
            raise EvidenceError(f"resource ledger snapshot is not canonical: {name}")
        values[name] = validate_ledger_snapshot(value, contract=contract)
        paths[name] = path
    if values["cycle_1"]["predecessor"] != file_hash_record(paths["approval"]):
        raise EvidenceError("cycle 1 snapshot predecessor mismatch")
    if values["cycle_2"]["predecessor"] != file_hash_record(paths["cycle_1"]):
        raise EvidenceError("cycle 2 snapshot predecessor mismatch")
    expected_candidate = {
        "commit": record["candidate"]["commit"],
        "tree": record["candidate"]["tree"],
    }
    if any(value["candidate"] != expected_candidate for value in values.values()):
        raise EvidenceError("ledger snapshot candidate identity mismatch")

    def snapshot_line(row: Mapping[str, Any]) -> str:
        return f"| {row['timestamp']} | {' | '.join(row['fields'])} |"

    lines = [snapshot_line(row) for row in values["approval"]["rows"]]
    for cycle_name in ("cycle_1", "cycle_2"):
        for row in values[cycle_name]["rows"]:
            if row["execution_started"] is not None:
                lines.append(snapshot_line(row["execution_started"]))
            lines.append(snapshot_line(row["terminal"]))
    return values, paths, "\n".join(lines) + "\n"


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
        if aggregate_path.is_symlink() or is_reparse_point(aggregate_path) or not aggregate_path.is_file():
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
        if path.is_symlink() or is_reparse_point(path) or file_hash_record(path) != {
            "bytes": authority["bytes"],
            "sha256": authority["sha256"],
        }:
            raise EvidenceError(f"resource-manager {key} script identity mismatch")
    ledger_path = manager_root / manager["ledger"]
    requests_root = manager_root / manager["requests"]
    if (
        ledger_path.is_symlink()
        or is_reparse_point(ledger_path)
        or not ledger_path.is_file()
        or requests_root.is_symlink()
        or is_reparse_point(requests_root)
        or not requests_root.is_dir()
    ):
        raise EvidenceError("resource-manager ledger/requests may not be symlinks")
    validate_superseded_request_ledger_absence(
        ledger_path.read_text(encoding="utf-8"), contract=contract
    )
    if (manager_root / manager["active_lock"]).exists():
        raise EvidenceError("resource-manager active lock remains after adjudication")
    candidate_path = candidate_path.resolve(strict=True)
    assert_clean_execution_repository(candidate_path, contract=contract)
    if _git(candidate_path, "rev-parse", "HEAD", contract=contract) != validated["candidate"]["commit"]:
        raise EvidenceError("candidate HEAD mismatch")
    if _git(candidate_path, "rev-parse", "HEAD^{tree}", contract=contract) != validated["candidate"]["tree"]:
        raise EvidenceError("candidate tree mismatch")
    topology = validate_execution_authorization(candidate_path, contract=contract)
    if (
        topology["candidate_commit"] != validated["candidate"]["commit"]
        or topology["candidate_tree"] != validated["candidate"]["tree"]
    ):
        raise EvidenceError("reviewed successor identity mismatch")
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
        if (
            request_path.name != f"{row['request_id']}.json"
            or request_path.is_symlink()
            or is_reparse_point(request_path)
        ):
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
    snapshot_values, snapshot_paths, ledger = load_bound_ledger_snapshots(
        validated, contract=contract
    )
    process_by_request = {
        process["request_id"]: process
        for _prefix, process in _iter_processes(validated)
        if process["request_id"] is not None
    }
    approval_snapshot_record = (
        file_hash_record(snapshot_paths["approval"]) if "approval" in snapshot_paths else None
    )
    for process in process_by_request.values():
        if process["status"] != "NOT_RUN" and process["approval_snapshot"] != approval_snapshot_record:
            raise EvidenceError("resource process approval snapshot binding mismatch")
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
            expected_extent = (
                {"launch.json", "pending-manifest.json", "result.json", "stderr.txt", "stdout.txt"}
                if process["request_id"] is not None
                else {"result.json", "stderr.txt", "stdout.txt"}
            )
            if (
                not directory.is_dir()
                or directory.is_symlink()
                or is_reparse_point(directory)
                or {path.name for path in directory.iterdir()} != expected_extent
            ):
                raise EvidenceError(f"process output extent mismatch: {prefix}")
            for key in ("result", "stderr", "stdout"):
                expected_artifacts[f"{prefix}.{key}"] = (
                    process[key],
                    directory / f"{key}.{'json' if key == 'result' else 'txt'}",
                )
    for name, (expected, path) in expected_artifacts.items():
        if path.is_symlink() or is_reparse_point(path) or file_hash_record(path) != expected:
            raise EvidenceError(f"process artifact identity mismatch: {name}")
    wave = validate_functional_wave_contract(contract)
    wave_parent = output_root(contract) / wave["execution"]["artifact_routing"][
        "directory_name"
    ]
    executed_functional_cycles: list[int] = []
    for cycle in validated["cycles"]:
        cycle_number = cycle["cycle"]
        process = cycle["lanes"]["functional"]
        cycle_root = functional_wave_artifact_paths(contract, cycle_number)[
            "cycle_root"
        ]
        if process["status"] == "NOT_RUN":
            if cycle_root.exists() or cycle_root.is_symlink():
                raise EvidenceError("not-run functional wave left cycle evidence")
            continue
        executed_functional_cycles.append(cycle_number)
        validate_functional_wave_external_evidence(
            contract=contract,
            cycle=cycle_number,
            candidate=validated["candidate"],
            process=process,
            stdout_path=expected_artifacts[
                f"cycle_{cycle_number}.functional.stdout"
            ][1],
        )
    if executed_functional_cycles:
        if (
            not wave_parent.is_dir()
            or wave_parent.is_symlink()
            or is_reparse_point(wave_parent)
            or {path.name for path in wave_parent.iterdir()}
            != {f"cycle-{cycle}" for cycle in executed_functional_cycles}
        ):
            raise EvidenceError("functional-wave parent extent mismatch")
    elif wave_parent.exists() or wave_parent.is_symlink():
        raise EvidenceError("not-run functional waves left an output directory")
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
            directory = process_output_directory(contract, prefix)
            launch_path = directory / "launch.json"
            pending_path = directory / "pending-manifest.json"
            require_regular_file(launch_path, nonempty=True)
            require_regular_file(pending_path, nonempty=True)
            launch_raw = launch_path.read_bytes()
            pending_raw = pending_path.read_bytes()
            launch = validate_resource_launch(strict_json_loads(launch_raw), contract=contract)
            pending = validate_pending_manifest(strict_json_loads(pending_raw), contract=contract)
            if (
                launch_raw != canonical_json_bytes(launch)
                or pending_raw != canonical_json_bytes(pending)
                or process["pending_manifest_sha256"] != sha256_bytes(pending_raw)
                or process["approval_snapshot"] != pending["approval_snapshot"]
                or launch["approval_snapshot"] != pending["approval_snapshot"]
                or launch["candidate"] != pending["candidate"]
                or pending["launch"] != file_hash_record(launch_path)
                or pending["result"] != process["result"]
                or pending["stderr"] != process["stderr"]
                or pending["stdout"] != process["stdout"]
                or pending["candidate"]
                != {
                    "commit": validated["candidate"]["commit"],
                    "tree": validated["candidate"]["tree"],
                }
            ):
                raise EvidenceError(f"resource staged-publication binding mismatch: {prefix}")
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
        started_entries = _ledger_entries(ledger, request_id, "EXECUTION_STARTED")
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
        ledger_process = dict(process)
        if wrapper is not None:
            ledger_process["candidate_commit"] = wrapper["candidate_commit"]
            ledger_process["candidate_tree"] = wrapper["candidate_tree"]
        expected_fields = terminal_ledger_fields(
            request, ledger_process, result_record
        )
        if (
            len(entries) != 1
            or len(all_terminal_entries) != 1
            or entries[0][1:] != expected_fields
        ):
            raise EvidenceError(f"request terminal ledger row mismatch: {request_id}")
        if process["status"] == "NOT_RUN":
            if started_entries:
                raise EvidenceError(f"cancelled request has an execution-start row: {request_id}")
        else:
            prefix = next(
                prefix
                for prefix, candidate_process in _iter_processes(validated)
                if candidate_process.get("request_id") == request_id
            )
            launch_path = process_output_directory(contract, prefix) / "launch.json"
            launch = validate_resource_launch(strict_json_load(launch_path), contract=contract)
            expected_started = execution_started_ledger_fields(
                request, launch, file_hash_record(launch_path)
            )
            if len(started_entries) != 1 or started_entries[0][1:] != expected_started:
                raise EvidenceError(f"request execution-start ledger row mismatch: {request_id}")
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
        package_raw = require_package_process_result_identity(contract=contract)
        require_regular_file(wheel_path, nonempty=True)
        if file_hash_record(package_result_path) != validated["package_artifacts"]["result"]:
            raise EvidenceError("package result identity mismatch")
        wheel_expected = dict(validated["package_artifacts"]["wheel"])
        filename = wheel_expected.pop("filename")
        if wheel_path.name != filename or file_hash_record(wheel_path) != wheel_expected:
            raise EvidenceError("wheel identity mismatch")
        package = strict_json_loads(package_raw)
        if package_raw != canonical_json_bytes(package):
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
            if path.is_symlink() or is_reparse_point(path) or not path.is_file():
                raise EvidenceError(f"failed-package artifact is missing: {key}")
            observed = file_hash_record(path)
            if key == "wheel" and observed["bytes"] <= 0:
                raise EvidenceError("failed-package wheel is empty")
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

    root = output_root(contract)
    if not root.is_dir() or root.is_symlink() or is_reparse_point(root):
        raise EvidenceError("burn-in output root is not a canonical directory")
    allowed_children = {
        PROCESS_DIRECTORY_NAMES[prefix]
        for prefix, process in _iter_processes(validated)
        if process["status"] != "NOT_RUN"
    }
    for cache_name in ("python-cache", "numba-cache"):
        if (root / cache_name).exists() or (root / cache_name).is_symlink():
            allowed_children.add(cache_name)
    for partition, process in enumerate(
        validated["common_lanes"]["additive"]["processes"], start=1
    ):
        if process["status"] != "NOT_RUN" and (root / f"pytest-additive-{partition}").exists():
            allowed_children.add(f"pytest-additive-{partition}")
    for path in (package_result_path, wheel_path):
        if path.exists() or path.is_symlink():
            allowed_children.add(path.name)
    for path in snapshot_paths.values():
        allowed_children.add(path.name)
    if executed_functional_cycles:
        allowed_children.add(
            contract["functional_wave"]["execution"]["artifact_routing"][
                "directory_name"
            ]
        )
    if require_aggregate:
        allowed_children.add(aggregate_path.name)
    observed_children = {path.name for path in root.iterdir()}
    if observed_children != allowed_children:
        raise EvidenceError(
            "burn-in output-root extent mismatch: "
            f"expected {sorted(allowed_children)}, got {sorted(observed_children)}"
        )
    if any(path.is_symlink() or is_reparse_point(path) for path in root.iterdir()):
        raise EvidenceError("burn-in output root contains a reparse point")


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
