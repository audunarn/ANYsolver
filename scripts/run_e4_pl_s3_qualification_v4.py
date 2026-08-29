"""Run the complete S3 activation-v4 authority over frozen v3 science.

The coordinator imports only the standard library, validates a reviewed final
candidate binding before mechanics imports, assigns every worker a canonical
hash-bound shard, and applies a complete-tree 24-GiB memory limit plus a
30-minute inactivity watchdog.  There is deliberately no elapsed runtime
ceiling; elapsed values are diagnostics and cannot classify a cycle.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import types
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
BASE_PROGRAM = REFERENCE_CASES / "e4_pl_s3_default_activation_v2.py"
BASE_INPUT = REFERENCE_CASES / "e4_pl_s3_default_activation_v2_input.json"
BASE_CONTRACT = REFERENCE_CASES / "e4_pl_s3_default_activation_v2_contract.json"
SUCCESSOR = REFERENCE_CASES / "e4_pl_s3_qualification_optimization_v4.py"
CONTRACT = REFERENCE_CASES / "e4_pl_s3_qualification_optimization_v6_contract.json"
COLD_COORDINATOR = ROOT / "scripts" / "benchmark_e4_pl_s3_activation_cold_path.py"
BINDING_GENERATOR = ROOT / "scripts" / "prepare_e4_pl_s3_qualification_v4_input.py"
WORKER_SCHEMA = "anysolver.e4-pl-s3-default-activation-worker-v3"
SCIENTIFIC_SCHEMA = "anysolver.e4-pl-s3-default-activation-scientific-v3"
CYCLE_SET_SCHEMA = "anysolver.e4-pl-s3-default-activation-cycle-set-v3"
ASSIGNMENT_SCHEMA = "anysolver.e4-pl-s3-formal-shard-assignment-v3"
AUTHORIZATION_SCHEMA = "anysolver.e4-pl-s3-qualification-authorization-v6"
REVIEW_SCHEMA = "anysolver.e4-pl-s3-qualification-independent-review-v6"
AUTHORITY_SUBJECT = "docs: authorize optimized S3 qualification execution v6"
RESOURCE_MANAGER = Path(r"C:\Github\.resource-manager")
RESOURCE_REQUEST_ENVIRONMENT = "E4_PL_S3_QUALIFICATION_REQUEST_ID"
RESOURCE_ATTEMPT_ENVIRONMENT = "E4_PL_S3_QUALIFICATION_ATTEMPT_SHA256"
REQUIRED_REVIEWER_IDS = (
    "s3-v6-authority-reviewer",
    "s3-v6-science-reviewer",
)
STRUCTURAL_WORKERS = (
    "STRUCTURAL_SLASH",
    "STRUCTURAL_BACKSLASH",
    "STRUCTURAL_ALTERNATING",
)
FOLLOWUP_WORKERS = ("EIGEN_PERFORMANCE", "SPECIAL_ECOSYSTEM")
BATCH_WORKERS = ("BATCH_0", "BATCH_1", "BATCH_2")
WORKERS = STRUCTURAL_WORKERS + FOLLOWUP_WORKERS + BATCH_WORKERS
WAVES = (STRUCTURAL_WORKERS, FOLLOWUP_WORKERS, BATCH_WORKERS)
TERMINALS = (
    "BLOCKED_E4_PL_S3_DEFAULT_ACTIVATION_EVIDENCE_OR_REVIEW",
    "NO_GO_E4_PL_S3_DEFAULT_ACTIVATION_QUALIFICATION",
    "PROVISIONAL_GO_E4_PL_S3_DEFAULT_ACTIVATION",
)
PRODUCTION_RESTRICTION = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
THREAD_ENVIRONMENT = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}
INACTIVITY_SECONDS = 1800
MEMORY_LIMIT_BYTES = 24 * (1 << 30)
MAX_RECORD_BYTES = 4 * (1 << 20)
TREE_RELEASE_ENVIRONMENT = "ANYSOLVER_S3_COLD_TREE_RELEASE"
TREE_RELEASE_BYTES = b"ANYSOLVER_S3_COLD_TREE_ACCOUNTED_V1\n"
TREE_RELEASE_WAIT_SECONDS = 5.0
WORKER_BOOTSTRAP = (
    "import builtins,sys;"
    "bound_path=sys.argv[1];expected=int(sys.argv[2]);del sys.argv[1:3];"
    "raw=sys.stdin.buffer.read(expected);"
    "assert len(raw)==expected and sys.stdin.buffer.read(1)==b'';"
    "scope={'__name__':'__main__','__file__':bound_path,'__package__':None,"
    "'__builtins__':builtins.__dict__};"
    "exec(compile(raw,bound_path,'exec',dont_inherit=True,optimize=0),scope)"
)
_BINDING_GENERATOR_RAW = BINDING_GENERATOR.read_bytes()
BINDING_GENERATOR_IDENTITY = {
    "bytes": len(_BINDING_GENERATOR_RAW),
    "path": "scripts/prepare_e4_pl_s3_qualification_v4_input.py",
    "sha256": hashlib.sha256(_BINDING_GENERATOR_RAW).hexdigest().upper(),
}
del _BINDING_GENERATOR_RAW


class QualificationError(ValueError):
    """Successor authority, worker evidence, or coverage is malformed."""


def _reject_constant(value: str) -> None:
    raise QualificationError(f"nonfinite JSON value is forbidden: {value}")


def _pairs(values: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in values:
        if key in result:
            raise QualificationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def read_json(path: Path, *, canonical: bool = True) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    if not raw or len(raw) > MAX_RECORD_BYTES:
        raise QualificationError(f"JSON record size is invalid: {path}")
    value = json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=_reject_constant,
    )
    if not isinstance(value, dict):
        raise QualificationError(f"JSON record is not an object: {path}")
    if canonical and raw != canonical_bytes(value):
        raise QualificationError(f"JSON record is not canonical: {path}")
    return raw, value


def write_exclusive(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))


def _stage_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def _publish_staged(
    pending: Path,
    canonical: Path,
    *,
    expected_raw: bytes | None = None,
) -> None:
    """Publish adjudicated bytes through a private same-volume hard link.

    Never link the caller-controlled pending inode into canonical evidence.
    A private, exclusively-created publication inode is populated from the
    already-adjudicated bytes, flushed, linked exclusively, and then unlinked.
    This removes the check/link race and leaves the canonical name as the only
    surviving link to the published bytes.
    """

    pending_raw = pending.read_bytes()
    if expected_raw is not None and pending_raw != expected_raw:
        raise QualificationError("staged publication bytes differ from adjudication")
    publication_raw = pending_raw if expected_raw is None else expected_raw
    if canonical.exists():
        if canonical.read_bytes() != publication_raw:
            raise QualificationError(f"canonical output already exists: {canonical}")
        pending.unlink(missing_ok=True)
        return
    canonical.parent.mkdir(parents=True, exist_ok=True)
    descriptor, private_name = tempfile.mkstemp(
        dir=canonical.parent,
        prefix=f".{canonical.name}.publication-",
        suffix=".tmp",
    )
    private = Path(private_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(publication_raw)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(private, canonical)
        except FileExistsError as exc:
            raise QualificationError(
                f"canonical output already exists: {canonical}"
            ) from exc
        if canonical.read_bytes() != publication_raw:
            canonical.unlink(missing_ok=True)
            raise QualificationError("published canonical bytes differ from adjudication")
    finally:
        private.unlink(missing_ok=True)
    pending.unlink(missing_ok=True)


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise QualificationError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_module_from_verified_bytes(name: str, path: Path, raw: bytes) -> Any:
    """Execute only the exact bytes already checked against frozen authority."""

    module = types.ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = ""
    sys.modules[name] = module
    try:
        code = compile(raw, str(path), "exec", dont_inherit=True, optimize=0)
        exec(code, module.__dict__)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


@dataclass(frozen=True)
class SuccessorAuthority:
    base: Any
    successor: Any
    authority: Any
    binding_path: Path
    binding_raw: bytes
    binding: dict[str, Any]
    authorization_path: Path
    authorization_raw: bytes
    authorization: dict[str, Any]
    control: Any | None = None
    verified_program_bytes: Mapping[str, bytes] | None = None
    verified_file_bytes: Mapping[str, bytes] | None = None
    qualification_contract: Mapping[str, Any] | None = None
    verified_data_bytes: Mapping[str, bytes] | None = None


def _live_file_binding(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    return {
        "bytes": len(raw),
        "path": path.resolve().relative_to(ROOT.resolve()).as_posix(),
        "sha256": sha256(raw),
    }


def _bound_regular_file(value: object, *, label: str) -> tuple[bytes, Path]:
    if not isinstance(value, dict) or set(value) != {"bytes", "path", "sha256"}:
        raise QualificationError(f"{label} binding differs")
    declared = Path(str(value["path"]))
    path = (
        declared if declared.is_absolute() else ROOT.resolve() / declared
    ).resolve(strict=True)
    if (
        not path.is_file()
        or path.is_symlink()
        or bool(getattr(path.lstat(), "st_file_attributes", 0) & 0x400)
    ):
        raise QualificationError(f"{label} is not a regular file")
    raw = path.read_bytes()
    if (
        type(value["bytes"]) is not int
        or value["bytes"] != len(raw)
        or not raw
        or type(value["sha256"]) is not str
        or value["sha256"] != sha256(raw)
    ):
        raise QualificationError(f"{label} bytes differ")
    return raw, path


def _bound_digest_file(value: object, *, label: str) -> tuple[bytes, Path]:
    """Capture a regular file bound by an exact route and SHA-256 row."""

    if not isinstance(value, dict) or set(value) != {"path", "sha256"}:
        raise QualificationError(f"{label} binding differs")
    declared = Path(str(value["path"]))
    if declared.is_absolute() or ".." in declared.parts:
        raise QualificationError(f"{label} route differs")
    path = (ROOT.resolve() / declared).resolve(strict=True)
    if (
        not path.is_relative_to(ROOT.resolve())
        or not path.is_file()
        or path.is_symlink()
        or bool(getattr(path.lstat(), "st_file_attributes", 0) & 0x400)
    ):
        raise QualificationError(f"{label} is not a regular repository file")
    raw = path.read_bytes()
    if (
        not raw
        or type(value["sha256"]) is not str
        or value["sha256"] != sha256(raw)
    ):
        raise QualificationError(f"{label} bytes differ")
    return raw, path


def _program_key(path: Path) -> str:
    """Return one case-normalized absolute key without importing from it."""

    return os.path.normcase(os.path.normpath(str(Path(path).absolute())))


def _verified_program_loader(
    program_bytes: Mapping[str, bytes],
    name: str,
    path: Path,
) -> Any:
    """Execute a helper only from the byte buffer frozen by authority load."""

    key = _program_key(path)
    raw = program_bytes.get(key)
    if raw is None:
        raise QualificationError(f"unregistered scientific program route: {path}")
    return _load_module_from_verified_bytes(name, Path(key), raw)


def _review_authority(
    value: object,
    *,
    expected_binding: Mapping[str, Any],
    label: str,
) -> tuple[str, Path]:
    raw, path = _bound_regular_file(value, label=label)
    review = json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=_reject_constant,
    )
    reviewer_id = review.get("reviewer_id") if isinstance(review, dict) else None
    if (
        not isinstance(review, dict)
        or raw != canonical_bytes(review)
        or set(review)
        != {
            "candidate_binding",
            "disposition",
            "findings",
            "production_restriction",
            "reviewer_id",
            "schema",
        }
        or review["schema"] != REVIEW_SCHEMA
        or review["candidate_binding"] != expected_binding
        or review["disposition"] != "ACCEPTED_NO_P0_P1"
        or review["findings"] != []
        or review["production_restriction"] != PRODUCTION_RESTRICTION
        or type(reviewer_id) is not str
        or not 3 <= len(reviewer_id) <= 64
        or reviewer_id != reviewer_id.strip().lower()
        or any(
            character not in "abcdefghijklmnopqrstuvwxyz0123456789._-"
            for character in reviewer_id
        )
    ):
        raise QualificationError(f"{label} is not an accepted canonical review")
    return reviewer_id, path


def _powershell_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _resource_command(
    request_id: str,
    python_executable: str,
    arguments: Sequence[str],
) -> str:
    prefix = (
        f"$env:{RESOURCE_REQUEST_ENVIRONMENT}={_powershell_quote(request_id)}; "
        f"& {_powershell_quote(python_executable)} "
        "-I -S -B "
        f"{_powershell_quote(str(Path(__file__).resolve()))}"
    )
    return prefix + " " + " ".join(_powershell_quote(item) for item in arguments)


def _ledger_rows(ledger_raw: bytes, request_id: str) -> list[tuple[str, str]]:
    try:
        text = ledger_raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise QualificationError("resource ledger is not UTF-8") from exc
    rows: list[tuple[str, str]] = []
    for line in text.splitlines():
        fields = [field.strip() for field in line.split("|")]
        if len(fields) >= 5 and fields[2] == request_id:
            rows.append((fields[3], sha256((line.rstrip() + "\n").encode("utf-8"))))
    return rows


def _verify_authority_commit(
    generator: Any,
    value: object,
    *,
    candidate_commit: str,
    required_paths: set[str],
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "changed_paths",
        "commit",
        "parent",
        "subject",
        "tree",
    }:
        raise QualificationError("authority commit fields differ")
    changed_paths = value["changed_paths"]
    if (
        value["parent"] != candidate_commit
        or value["subject"] != AUTHORITY_SUBJECT
        or not isinstance(changed_paths, list)
        or changed_paths != sorted(set(changed_paths))
        or set(changed_paths) != required_paths
        or any(
            type(path) is not str
            or not path.startswith("docs/reference_cases/")
            or not path.endswith(".json")
            for path in changed_paths
        )
    ):
        raise QualificationError("authority commit policy differs")
    observed = generator._commit_identity(ROOT, str(value["commit"]))
    if observed != {
        "commit": value["commit"],
        "tree": value["tree"],
        "parent": value["parent"],
        "subject": value["subject"],
    }:
        raise QualificationError("authority commit identity differs")
    if generator._git(ROOT, "rev-parse", "HEAD") != value["commit"]:
        raise QualificationError("authority worktree is not at the authorized commit")
    if generator._changed_paths(ROOT, value["parent"], value["commit"]) != changed_paths:
        raise QualificationError("authority commit path set differs")
    if generator._git(ROOT, "status", "--porcelain=v1", "--untracked-files=all"):
        raise QualificationError("authority worktree is dirty")
    return dict(value)


def _verify_resource_authority(
    value: object,
    *,
    authorization_path: Path,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "approval_row_sha256",
        "command_sha256",
        "coordinator_arguments",
        "ledger_path",
        "python_executable",
        "request",
    }:
        raise QualificationError("resource execution fields differ")
    request_binding = value["request"]
    if not isinstance(request_binding, dict) or set(request_binding) != {
        "bytes",
        "path",
        "request_id",
        "sha256",
    }:
        raise QualificationError("resource request binding differs")
    raw, request_path = _bound_regular_file(
        {key: request_binding[key] for key in ("bytes", "path", "sha256")},
        label="resource request",
    )
    request = json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=_reject_constant,
    )
    request_id = request_binding["request_id"]
    if (
        not isinstance(request, dict)
        or set(request)
        != {
            "command",
            "estimate_minutes",
            "repository",
            "request_id",
            "requested_at",
            "status",
            "task",
        }
        or type(request_id) is not str
        or len(request_id) != 32
        or any(character not in "0123456789abcdef" for character in request_id)
        or request["request_id"] != request_id
        or request_path != RESOURCE_MANAGER / "requests" / f"{request_id}.json"
        or request["repository"] != str(ROOT.resolve())
        or request["status"] != "PENDING"
        or request["task"] != "ANYsolver S3 qualification v3 two-cycle formal execution"
        or type(request["estimate_minutes"]) is not int
        or request["estimate_minutes"] <= 0
    ):
        raise QualificationError("resource request identity differs")
    arguments = value["coordinator_arguments"]
    python_executable = str(Path(str(value["python_executable"])).resolve(strict=True))
    expected_arguments = [
        "--binding",
        str(Path(str(arguments[1])).resolve(strict=True)),
        "--authorization",
        str(authorization_path.resolve(strict=True)),
        "--cycles",
        "2",
        "--output-root",
        str(Path(str(arguments[7])).resolve()),
    ] if isinstance(arguments, list) and len(arguments) == 8 else []
    expected_command = _resource_command(request_id, python_executable, expected_arguments)
    ledger_path = Path(str(value["ledger_path"])).resolve(strict=True)
    ledger_raw = ledger_path.read_bytes()
    rows = _ledger_rows(ledger_raw, request_id)
    approved = [digest for state, digest in rows if state == "APPROVED"]
    terminal = [
        state
        for state, _digest in rows
        if state in {"COMPLETED_PASS", "COMPLETED_FAIL", "CANCELLED_NOT_RUN", "INTERRUPTED_INCOMPLETE"}
    ]
    if (
        expected_arguments != arguments
        or request["command"] != expected_command
        or value["command_sha256"] != sha256(expected_command.encode("utf-8"))
        or ledger_path != (RESOURCE_MANAGER / "ledger.md").resolve(strict=True)
        or len(approved) != 1
        or approved[0] != value["approval_row_sha256"]
        or terminal
        or len([state for state, _digest in rows if state == "EXECUTION_STARTED"]) > 1
    ):
        raise QualificationError("resource request approval or one-use state differs")
    return {
        "approval_row_sha256": value["approval_row_sha256"],
        "command_sha256": value["command_sha256"],
        "coordinator_arguments": expected_arguments,
        "ledger_path": str(ledger_path),
        "python_executable": python_executable,
        "request": dict(request_binding),
    }


def _write_resource_attempt(
    *,
    request_id: str,
    command_sha256: str,
    output_root: Path,
    python_executable: Path,
) -> str:
    attempts = RESOURCE_MANAGER / "attempts"
    attempts.mkdir(parents=True, exist_ok=True)
    path = attempts / f"{request_id}.json"
    value = {
        "command_sha256": command_sha256,
        "coordinator_process_id": os.getpid(),
        "output_root": str(output_root.resolve()),
        "python_executable": str(python_executable),
        "request_id": request_id,
        "schema": "anysolver.e4-pl-s3-resource-attempt-v1",
    }
    raw = canonical_bytes(value)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    digest = sha256(raw)
    os.environ[RESOURCE_ATTEMPT_ENVIRONMENT] = digest
    return digest


def _claim_resource_attempt(
    authority: SuccessorAuthority,
    output_root: Path,
) -> str:
    resource = authority.authorization["resource_execution"]
    return _write_resource_attempt(
        request_id=str(resource["request"]["request_id"]),
        command_sha256=str(resource["command_sha256"]),
        output_root=output_root,
        python_executable=Path(sys.executable).resolve(strict=True),
    )


def _preclaim_launched_resource(output_root: Path) -> str:
    """Consume the launched request before validating mutable authority inputs."""

    request_id = os.environ.get(RESOURCE_REQUEST_ENVIRONMENT, "")
    if (
        len(request_id) != 32
        or any(character not in "0123456789abcdef" for character in request_id)
    ):
        raise QualificationError("resource request environment differs")
    request_path = RESOURCE_MANAGER / "requests" / f"{request_id}.json"
    _request_raw, request = read_json(request_path)
    python_executable = Path(sys.executable).resolve(strict=True)
    current_arguments = list(sys.argv[1:])
    current_command = _resource_command(
        request_id,
        str(python_executable),
        current_arguments,
    )
    if (
        set(request)
        != {
            "command",
            "estimate_minutes",
            "repository",
            "request_id",
            "requested_at",
            "status",
            "task",
        }
        or request.get("request_id") != request_id
        or request.get("repository") != str(ROOT.resolve())
        or request.get("status") != "PENDING"
        or request.get("task")
        != "ANYsolver S3 qualification v3 two-cycle formal execution"
        or request.get("command") != current_command
    ):
        raise QualificationError("launched resource request identity differs")
    ledger_path = RESOURCE_MANAGER / "ledger.md"
    rows = _ledger_rows(ledger_path.read_bytes(), request_id)
    if (
        len([state for state, _digest in rows if state == "EXECUTION_STARTED"]) != 1
        or any(
            state
            in {
                "COMPLETED_PASS",
                "COMPLETED_FAIL",
                "CANCELLED_NOT_RUN",
                "INTERRUPTED_INCOMPLETE",
            }
            for state, _digest in rows
        )
    ):
        raise QualificationError("launched resource request is not exclusively active")
    _owner_raw, owner = read_json(
        RESOURCE_MANAGER / "active-lock" / "owner.json",
        canonical=False,
    )
    if (
        set(owner)
        != {
            "acquired_at",
            "command",
            "process_id",
            "repository",
            "request_id",
            "task",
        }
        or owner.get("request_id") != request_id
        or owner.get("command") != current_command
        or owner.get("repository") != request["repository"]
        or owner.get("task") != request["task"]
    ):
        raise QualificationError("global resource slot is not owned by this launch")
    return _write_resource_attempt(
        request_id=request_id,
        command_sha256=sha256(current_command.encode("utf-8")),
        output_root=output_root,
        python_executable=python_executable,
    )


def require_active_resource_execution(
    authority: SuccessorAuthority,
    *,
    attempt_required: bool = True,
) -> None:
    resource = authority.authorization["resource_execution"]
    expected_python = Path(str(resource["python_executable"])).resolve(strict=True)
    observed_python = Path(sys.executable).resolve(strict=True)
    if observed_python != expected_python:
        raise QualificationError("live Python interpreter differs from resource authority")
    request_id = resource["request"]["request_id"]
    if os.environ.get(RESOURCE_REQUEST_ENVIRONMENT) != request_id:
        raise QualificationError("resource request environment differs")
    ledger_raw = Path(resource["ledger_path"]).read_bytes()
    rows = _ledger_rows(ledger_raw, request_id)
    if len([state for state, _digest in rows if state == "EXECUTION_STARTED"]) != 1:
        raise QualificationError("resource request was not started exactly once")
    if any(
        state in {"COMPLETED_PASS", "COMPLETED_FAIL", "CANCELLED_NOT_RUN", "INTERRUPTED_INCOMPLETE"}
        for state, _digest in rows
    ):
        raise QualificationError("resource request was already consumed")
    owner_path = RESOURCE_MANAGER / "active-lock" / "owner.json"
    _owner_raw, owner = read_json(owner_path, canonical=False)
    _request_raw, request = read_json(
        Path(resource["request"]["path"]), canonical=False
    )
    if (
        set(owner)
        != {
            "acquired_at",
            "command",
            "process_id",
            "repository",
            "request_id",
            "task",
        }
        or owner.get("request_id") != request_id
        or owner.get("command") != request.get("command")
        or owner.get("repository") != request.get("repository")
        or owner.get("task") != request.get("task")
    ):
        raise QualificationError("global resource slot is not owned by this request")
    if attempt_required:
        attempt_path = RESOURCE_MANAGER / "attempts" / f"{request_id}.json"
        attempt_raw, attempt = read_json(attempt_path)
        if (
            set(attempt)
            != {
                "command_sha256",
                "coordinator_process_id",
                "output_root",
                "python_executable",
                "request_id",
                "schema",
            }
            or attempt["schema"] != "anysolver.e4-pl-s3-resource-attempt-v1"
            or attempt["request_id"] != request_id
            or attempt["command_sha256"] != resource["command_sha256"]
            or attempt["python_executable"] != str(observed_python)
            or type(attempt["coordinator_process_id"]) is not int
            or attempt["coordinator_process_id"] <= 0
            or type(attempt["output_root"]) is not str
            or not Path(attempt["output_root"]).is_absolute()
            or os.environ.get(RESOURCE_ATTEMPT_ENVIRONMENT) != sha256(attempt_raw)
        ):
            raise QualificationError("exclusive resource attempt authority differs")


def _load_frozen_v2_scientific_authority(
    base: Any,
    binding_path: Path,
    binding_raw: bytes,
    binding: Mapping[str, Any],
    target: Path,
    verified_files: Mapping[str, bytes],
    v3_contract: Mapping[str, Any],
) -> Any:
    """Load v2 science without touching obsolete candidate worktrees.

    The v2 input is immutable historical authority.  Its program rows identify
    the originally preregistered implementations, but the reviewed lease and
    bounded-solve corrections deliberately produced successor program bytes.
    The v3 contract therefore binds the exact live successor programs.  Never
    rewrite the historical v2 input to make those two authorities appear equal.
    """

    input_raw = verified_files["base_input"]
    payload = base.strict_json(input_raw, label="frozen v2 scientific input")
    if not isinstance(payload, dict) or input_raw != base.pretty_bytes(payload):
        raise QualificationError("frozen v2 scientific input is noncanonical")
    base._exact_keys(
        payload,
        ("candidates", "contract", "evidence", "execution", "programs", "schema"),
        "frozen v2 input",
    )
    if payload["schema"] != base.INPUT_SCHEMA:
        raise QualificationError("frozen v2 input schema differs")
    contract_row = payload["contract"]
    base._exact_keys(contract_row, ("bytes", "path", "sha256"), "v2 contract")
    contract_path = (ROOT / str(contract_row["path"])).resolve(strict=True)
    if contract_path != BASE_CONTRACT.resolve(strict=True):
        raise QualificationError("frozen v2 contract route differs")
    contract_raw = verified_files["base_contract"]
    contract = base.strict_json(contract_raw, label="frozen v2 scientific contract")
    if (
        not isinstance(contract, dict)
        or contract_raw != base.pretty_bytes(contract)
        or len(contract_raw) != int(contract_row["bytes"])
        or sha256(contract_raw) != str(contract_row["sha256"])
        or contract.get("schema") != base.CONTRACT_SCHEMA
    ):
        raise QualificationError("frozen v2 contract binding differs")
    historical_programs = payload["programs"]
    if not isinstance(historical_programs, dict) or set(historical_programs) != {
        "batch_benchmark",
        "runner",
        "test",
    }:
        raise QualificationError("frozen v2 program set differs")
    for name, row in historical_programs.items():
        base._exact_keys(row, ("bytes", "path", "sha256"), f"v2 program {name}")
    successor_programs = v3_contract.get("frozen_successor_scientific_programs")
    if not isinstance(successor_programs, dict) or set(successor_programs) != set(
        historical_programs
    ):
        raise QualificationError("successor scientific program set differs")
    verified_program_labels = {
        "batch_benchmark": "batch_benchmark",
        "runner": "base_program",
        "test": "base_test",
    }
    for name, row in successor_programs.items():
        if not isinstance(row, dict) or set(row) != {"bytes", "path", "sha256"}:
            raise QualificationError(f"successor program binding differs: {name}")
        if row["path"] != historical_programs[name]["path"]:
            raise QualificationError(f"successor program route differs: {name}")
        program_path = (ROOT / str(row["path"])).resolve(strict=True)
        program_raw = verified_files[verified_program_labels[name]]
        expected_path = (
            ROOT / str(binding["files"][verified_program_labels[name]]["path"])
        ).resolve(strict=True)
        if (
            program_path != expected_path
            or row != binding["files"][verified_program_labels[name]]
            or len(program_raw) != int(row["bytes"])
            or sha256(program_raw) != str(row["sha256"])
        ):
            raise QualificationError(f"successor scientific program differs: {name}")
    evidence = payload["evidence"]
    manifest_row = evidence.get("connectivity_manifest") if isinstance(evidence, dict) else None
    if not isinstance(manifest_row, dict) or set(manifest_row) != {
        "bytes",
        "path",
        "sha256",
    }:
        raise QualificationError("frozen connectivity authority differs")
    manifest_path = Path(str(manifest_row["path"]))
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    manifest_path = manifest_path.resolve(strict=True)
    manifest_raw = verified_files["manifest"]
    if (
        manifest_path
        != (ROOT / str(binding["files"]["manifest"]["path"])).resolve(strict=True)
        or manifest_row != binding["files"]["manifest"]
        or len(manifest_raw) != int(manifest_row["bytes"])
        or sha256(manifest_raw) != str(manifest_row["sha256"])
    ):
        raise QualificationError("frozen connectivity manifest differs")
    manifest = base.strict_json(manifest_raw, label="frozen connectivity manifest")
    if not isinstance(manifest, dict) or len(manifest.get("records", ())) != 252:
        raise QualificationError("frozen connectivity manifest coverage differs")
    updated_input = deepcopy(payload)
    updated_input["candidates"] = deepcopy(binding["candidates"])
    updated_input["runtime_environment"] = deepcopy(
        binding["runtime_environment"]
    )
    updated_input["execution"] = {
        "automatic_retry": False,
        "inactivity_seconds": INACTIVITY_SECONDS,
        "memory_limit_gib_per_process": 24,
        "runtime_classification": False,
        "target": str(target),
        "total_runtime_limit_seconds": None,
        "workers_maximum": 3,
    }
    return base.Authority(
        input_path=binding_path.resolve(),
        input_raw=binding_raw,
        input=updated_input,
        contract_path=contract_path,
        contract_raw=contract_raw,
        contract=contract,
        manifest_path=manifest_path,
        manifest_raw=manifest_raw,
        manifest=manifest,
        target=target,
    )


def load_authority(binding_path: Path, authorization_path: Path) -> SuccessorAuthority:
    """Validate final successor authority before any mechanics import."""

    binding_raw, binding = read_json(binding_path)
    authorization_raw, authorization = read_json(authorization_path)
    if set(binding) != {
        "anysolver_policy",
        "candidate_graph",
        "candidate_preflight",
        "candidates",
        "execution_target",
        "files",
        "formal_execution_authorized",
        "production_restriction",
        "runtime_environment",
        "schema",
    }:
        raise QualificationError("candidate binding fields differ")
    if set(authorization) != {
        "authority_commit",
        "candidate_binding",
        "formal_execution_authorized",
        "independent_reviews",
        "production_restriction",
        "resource_execution",
        "schema",
        "user_approval",
    }:
        raise QualificationError("authorization fields differ")
    expected_binding = {
        "bytes": len(binding_raw),
        "path": str(binding_path.resolve()),
        "sha256": sha256(binding_raw),
    }
    if authorization.get("candidate_binding") != expected_binding:
        raise QualificationError("authorization does not bind candidate bytes")
    files = binding.get("files")
    generator_row = files.get("binding_generator") if isinstance(files, dict) else None
    expected_generator_path = BINDING_GENERATOR.relative_to(ROOT).as_posix()
    if (
        not isinstance(generator_row, dict)
        or generator_row != BINDING_GENERATOR_IDENTITY
        or generator_row.get("path") != expected_generator_path
    ):
        raise QualificationError("binding generator route differs")
    generator_raw, generator_path = _bound_regular_file(
        generator_row,
        label="binding generator",
    )
    if generator_path != BINDING_GENERATOR:
        raise QualificationError("binding generator path differs")
    generator = _load_module_from_verified_bytes(
        "_s3_v4_binding_generator",
        generator_path,
        generator_raw,
    )
    if (
        binding["schema"] != generator.SCHEMA
        or binding["formal_execution_authorized"] is not False
        or binding["production_restriction"] != PRODUCTION_RESTRICTION
    ):
        raise QualificationError("candidate binding policy differs")
    try:
        generator._activate_bound_runtime_environment(
            binding["runtime_environment"]
        )
    except generator.BindingError as exc:
        raise QualificationError("bound execution tools differ") from exc
    expected_files = {
        "base_contract": _live_file_binding(generator.BASE_CONTRACT),
        "base_input": _live_file_binding(generator.BASE_INPUT),
        "base_program": _live_file_binding(generator.BASE_PROGRAM),
        "base_test": _live_file_binding(generator.BASE_TEST),
        "batch_benchmark": _live_file_binding(generator.BATCH_BENCHMARK),
        "binding_generator": _live_file_binding(BINDING_GENERATOR),
        "contract": _live_file_binding(CONTRACT),
        "coordinator": _live_file_binding(COLD_COORDINATOR),
        "formal_runner": _live_file_binding(Path(__file__).resolve()),
        "formal_test": _live_file_binding(
            ROOT / "tests" / "test_e4_pl_s3_qualification_optimization_v4.py"
        ),
        "manifest": _live_file_binding(
            REFERENCE_CASES / "e4_pl_s3_mixed_mesh_connectivity_manifest.json"
        ),
        "mixed_eigen_performance": _live_file_binding(
            generator.MIXED_EIGEN_PERFORMANCE
        ),
        "mixed_mesh_manifest_program": _live_file_binding(
            generator.MIXED_MESH_MANIFEST_PROGRAM
        ),
        "mixed_mesh_runner": _live_file_binding(generator.MIXED_MESH_RUNNER),
        "mixed_mesh_smoke_input": _live_file_binding(
            generator.MIXED_MESH_SMOKE_INPUT
        ),
        "mixed_structural_common": _live_file_binding(
            generator.MIXED_STRUCTURAL_COMMON
        ),
        "mixed_structural_producer": _live_file_binding(
            generator.MIXED_STRUCTURAL_PRODUCER
        ),
        "optimization_evidence": _live_file_binding(
            REFERENCE_CASES / "e4_pl_s3_qualification_optimization_v3_evidence.json"
        ),
        "preflight_config": _live_file_binding(generator.PREFLIGHT_CONFIG),
        "preflight_runner": _live_file_binding(generator.PREFLIGHT_RUNNER),
        "successor": _live_file_binding(SUCCESSOR),
        "test": _live_file_binding(
            ROOT / "tests" / "test_e4_pl_s3_activation_cold_path.py"
        ),
    }
    if binding["files"] != expected_files:
        raise QualificationError("candidate binding program graph differs")
    verified_file_bytes: dict[str, bytes] = {}
    verified_file_paths: dict[str, Path] = {}
    for label, row in binding["files"].items():
        frozen_raw, frozen_path = _bound_regular_file(
            row,
            label=label.replace("_", " "),
        )
        expected_path = (ROOT / str(expected_files[label]["path"])).resolve(
            strict=True
        )
        if frozen_path != expected_path:
            raise QualificationError(f"{label.replace('_', ' ')} path differs")
        verified_file_bytes[label] = frozen_raw
        verified_file_paths[label] = frozen_path
    helper_paths = {
        "batch_benchmark": generator.BATCH_BENCHMARK,
        "mixed_eigen_performance": generator.MIXED_EIGEN_PERFORMANCE,
        "mixed_mesh_manifest_program": generator.MIXED_MESH_MANIFEST_PROGRAM,
        "mixed_mesh_runner": generator.MIXED_MESH_RUNNER,
        "mixed_structural_common": generator.MIXED_STRUCTURAL_COMMON,
        "mixed_structural_producer": generator.MIXED_STRUCTURAL_PRODUCER,
    }
    verified_program_bytes: dict[str, bytes] = {}
    for label, expected_path in helper_paths.items():
        program_raw = verified_file_bytes[label]
        program_path = verified_file_paths[label]
        expected_resolved = Path(expected_path).resolve(strict=True)
        if program_path != expected_resolved:
            raise QualificationError(f"{label.replace('_', ' ')} path differs")
        key = _program_key(program_path)
        if key in verified_program_bytes:
            raise QualificationError("scientific program routes are not unique")
        verified_program_bytes[key] = program_raw
    qualification_contract_raw = verified_file_bytes["contract"]
    qualification_contract = json.loads(
        qualification_contract_raw,
        object_pairs_hook=_pairs,
        parse_constant=_reject_constant,
    )
    if not isinstance(qualification_contract, dict):
        raise QualificationError("qualification contract must be an object")
    smoke_input_raw = verified_file_bytes["mixed_mesh_smoke_input"]
    smoke_input = json.loads(
        smoke_input_raw,
        object_pairs_hook=_pairs,
        parse_constant=_reject_constant,
    )
    smoke_authority = smoke_input.get("authority") if isinstance(smoke_input, dict) else None
    if not isinstance(smoke_authority, dict) or set(smoke_authority) != {
        "connectivity_manifest",
        "qualification_contract",
    }:
        raise QualificationError("mixed-mesh model authority differs")
    manifest_authority = smoke_authority["connectivity_manifest"]
    if manifest_authority != {
        "path": binding["files"]["manifest"]["path"],
        "sha256": binding["files"]["manifest"]["sha256"],
    }:
        raise QualificationError("mixed-mesh manifest authority differs")
    smoke_contract_raw, smoke_contract_path = _bound_digest_file(
        smoke_authority["qualification_contract"],
        label="mixed-mesh qualification contract",
    )
    verified_data_bytes = {
        _program_key(verified_file_paths["mixed_mesh_smoke_input"]): smoke_input_raw,
        _program_key(verified_file_paths["manifest"]): verified_file_bytes["manifest"],
        _program_key(smoke_contract_path): smoke_contract_raw,
    }
    candidates = binding["candidates"]
    if not isinstance(candidates, dict) or set(candidates) != set(generator.CANDIDATES):
        raise QualificationError("candidate graph membership or order differs")
    for name in generator.CANDIDATES:
        if generator._verify_candidate(name, candidates[name]) != candidates[name]:
            raise QualificationError(f"{name} candidate identity differs")
    preflight = binding["candidate_preflight"]
    if not isinstance(preflight, dict) or set(preflight) != set(generator.CANDIDATES):
        raise QualificationError("candidate preflight membership differs")
    for name in generator.CANDIDATES:
        entry = preflight[name]
        if not isinstance(entry, dict) or set(entry) != {"record", "result"}:
            raise QualificationError(f"{name} candidate preflight fields differ")
        if (
            generator._verify_preflight(
                name,
                candidates[name],
                entry["result"],
                Path(str(binding["execution_target"])),
                binding["runtime_environment"],
                candidates,
            )
            != entry
        ):
            raise QualificationError(f"{name} candidate preflight differs")
    policy = binding["anysolver_policy"]
    try:
        if (
            generator._reverify_bound_anysolver_policy(
                policy,
                candidates["ANYsolver"],
            )
            != policy
        ):
            raise QualificationError("qualified Q4 guard-only identity differs")
    except generator.BindingError as exc:
        raise QualificationError(
            "qualified Q4 guard-only identity differs"
        ) from exc
    target = Path(str(binding["execution_target"])).resolve(strict=True)
    try:
        if (
            generator._verify_bound_execution_target(
                target,
                candidates,
                binding["runtime_environment"],
            )
            != candidates
        ):
            raise QualificationError("isolated runtime environment is noncanonical")
    except generator.BindingError as exc:
        raise QualificationError("isolated runtime environment differs") from exc
    reviews = authorization["independent_reviews"]
    if (
        authorization["schema"] != AUTHORIZATION_SCHEMA
        or authorization["candidate_binding"] != expected_binding
        or authorization["formal_execution_authorized"] is not True
        or authorization["production_restriction"] != PRODUCTION_RESTRICTION
        or not isinstance(reviews, list)
        or len(reviews) != 2
    ):
        raise QualificationError("authorization is incomplete or malformed")
    if qualification_contract.get("review_authority") != {
        "required_reviewer_ids": list(REQUIRED_REVIEWER_IDS),
        "roles": (
            "SEPARATE_AUTHORITY_AND_SCIENTIFIC_REVIEWS_BOUND_BY_"
            "AUTHORIZATION_COMMIT"
        ),
    }:
        raise QualificationError("review authority contract differs")
    review_rows = [
        _review_authority(
            review,
            expected_binding=expected_binding,
            label=f"independent review {index}",
        )
        for index, review in enumerate(reviews, start=1)
    ]
    if tuple(sorted(reviewer for reviewer, _path in review_rows)) != tuple(
        sorted(REQUIRED_REVIEWER_IDS)
    ):
        raise QualificationError("independent reviewer authorities differ")
    authority_paths = {
        binding_path.resolve().relative_to(ROOT.resolve()).as_posix(),
        *(
            path.resolve().relative_to(ROOT.resolve()).as_posix()
            for _reviewer, path in review_rows
        ),
    }
    graph_binding = binding.get("candidate_graph")
    if not isinstance(graph_binding, dict) or set(graph_binding) != {
        "bytes",
        "path",
        "sha256",
    }:
        raise QualificationError("candidate graph binding differs")
    _graph_raw, graph_path = _bound_regular_file(
        graph_binding,
        label="candidate graph",
    )
    try:
        if generator.build_binding(graph_path) != binding:
            raise QualificationError("candidate graph does not reproduce its binding")
    except generator.BindingError as exc:
        raise QualificationError("candidate graph revalidation failed") from exc
    authority_paths.add(graph_path.relative_to(ROOT.resolve()).as_posix())
    _verify_authority_commit(
        generator,
        authorization["authority_commit"],
        candidate_commit=str(candidates["ANYsolver"]["commit"]),
        required_paths=authority_paths,
    )
    verified_resource = _verify_resource_authority(
        authorization["resource_execution"],
        authorization_path=authorization_path,
    )
    if authorization["user_approval"] != {
        "resource_approval_row_sha256": verified_resource[
            "approval_row_sha256"
        ],
        "scope": "STANDING_APPROVAL_FOR_REQUIRED_COMPLETION_REQUESTS",
    }:
        raise QualificationError("user approval authority differs")
    base_raw = verified_file_bytes["base_program"]
    base_path = verified_file_paths["base_program"]
    base = _load_module_from_verified_bytes(
        "_s3_activation_v3_base",
        base_path,
        base_raw,
    )
    authority = _load_frozen_v2_scientific_authority(
        base,
        binding_path,
        binding_raw,
        binding,
        target,
        verified_file_bytes,
        qualification_contract,
    )
    successor_raw = verified_file_bytes["successor"]
    successor_path = verified_file_paths["successor"]
    successor = _load_module_from_verified_bytes(
        "_s3_activation_v3_successor",
        successor_path,
        successor_raw,
    )
    control_raw = verified_file_bytes["coordinator"]
    control_path = verified_file_paths["coordinator"]
    control = _load_module_from_verified_bytes(
        "_s3_v3_verified_control",
        control_path,
        control_raw,
    )
    return SuccessorAuthority(
        base,
        successor,
        authority,
        binding_path,
        binding_raw,
        binding,
        authorization_path,
        authorization_raw,
        authorization,
        control,
        types.MappingProxyType(verified_program_bytes),
        types.MappingProxyType(verified_file_bytes),
        types.MappingProxyType(qualification_contract),
        types.MappingProxyType(verified_data_bytes),
    )


def _manifest_rows(authority: SuccessorAuthority, diagonal: str) -> list[dict[str, Any]]:
    rows = [
        dict(row)
        for row in authority.authority.manifest["records"]
        if row.get("diagonal") == diagonal
    ]
    if len(rows) != 84:
        raise QualificationError(f"{diagonal} assignment is not exactly 84 records")
    return rows


def _special_lanes(authority: SuccessorAuthority) -> tuple[list[dict[str, Any]], int]:
    contract = authority.qualification_contract
    if contract is None:
        raise QualificationError("verified qualification contract is absent")
    formal = contract.get("formal_runner")
    overlay = formal.get("special_lane_overlay") if isinstance(formal, dict) else None
    if not isinstance(overlay, list) or len(overlay) != 3:
        raise QualificationError("v3 special-lane overlay differs")
    historical = deepcopy(
        authority.authority.contract["coverage"]["special_pytest_lanes"]
    )
    lanes = historical + deepcopy(overlay)
    names = [row.get("name") for row in lanes if isinstance(row, dict)]
    if len(names) != len(lanes) or len(set(names)) != len(lanes):
        raise QualificationError("special lane identities are duplicated")
    return lanes, len(overlay)


def build_assignment(authority: SuccessorAuthority, worker_id: str) -> dict[str, Any]:
    if worker_id not in WORKERS:
        raise QualificationError(f"unknown worker: {worker_id}")
    frozen_files = authority.verified_file_bytes
    if frozen_files is None:
        raise QualificationError("verified authority file buffers are absent")
    if worker_id in STRUCTURAL_WORKERS:
        diagonal = worker_id.removeprefix("STRUCTURAL_").lower()
        rows = _manifest_rows(authority, diagonal)
        payload: dict[str, Any] = {
            "diagonal": diagonal,
            "manifest_records": [
                {"record": row, "sha256": sha256(canonical_bytes(row))}
                for row in rows
            ],
            "record_count": 84,
        }
    elif worker_id == "EIGEN_PERFORMANCE":
        selected = []
        for fraction in (0, 10, 25):
            mask = "none" if fraction == 0 else "dispersed"
            matches = [
                dict(row)
                for row in authority.authority.manifest["records"]
                if row.get("level") == 20
                and row.get("s3_area_fraction_percent") == fraction
                and row.get("mask") == mask
                and row.get("diagonal") == "alternating"
            ]
            if len(matches) != 1:
                raise QualificationError("eigen topology assignment differs")
            selected.append(
                {
                    "record": matches[0],
                    "sha256": sha256(canonical_bytes(matches[0])),
                }
            )
        payload = {
            "buckling_cases": 2,
            "modal_cases": 2,
            "paired_performance_comparisons": 24,
            "topology_records": selected,
        }
    elif worker_id == "SPECIAL_ECOSYSTEM":
        lanes, overlay_count = _special_lanes(authority)
        payload = {
            "lane_count": len(lanes),
            "lanes": lanes,
            "registered_special_fixtures": 8,
            "v3_overlay_lane_count": overlay_count,
        }
    else:
        index = int(worker_id.removeprefix("BATCH_"))
        spec = authority.authority.contract["coverage"]["eigen_performance"][
            "batch"
        ]
        payload = {
            "eligible_element_count": int(spec["eligible_element_count"]),
            "repetition_indices": list(range(index, int(spec["repetitions"]), 3)),
            "shard_count": 3,
            "shard_index": index,
        }
    return {
        "authorization_sha256": sha256(authority.authorization_raw),
        "base_contract_sha256": sha256(authority.authority.contract_raw),
        "binding_sha256": sha256(authority.binding_raw),
        "formal_runner_sha256": sha256(frozen_files["formal_runner"]),
        "payload": payload,
        "schema": ASSIGNMENT_SCHEMA,
        "successor_sha256": sha256(frozen_files["successor"]),
        "worker_id": worker_id,
    }


def read_assignment(
    authority: SuccessorAuthority, path: Path
) -> tuple[dict[str, Any], str]:
    raw, value = read_json(path)
    worker_id = value.get("worker_id")
    if type(worker_id) is not str or value != build_assignment(authority, worker_id):
        raise QualificationError("formal shard assignment differs")
    return value, sha256(raw)


def _checkpoint(path: Path, sequence: int, stage: str) -> None:
    with path.open("ab") as stream:
        stream.write(canonical_bytes({"sequence": sequence, "stage": stage}))
        stream.flush()
        os.fsync(stream.fileno())


def _await_tree_accounting_release() -> None:
    release_name = os.environ.get(TREE_RELEASE_ENVIRONMENT)
    if not release_name:
        return
    release = Path(release_name)
    deadline = time.monotonic() + TREE_RELEASE_WAIT_SECONDS
    while not release.is_file():
        if time.monotonic() >= deadline:
            raise QualificationError("process-tree accounting was not released")
        time.sleep(0.01)
    if release.read_bytes() != TREE_RELEASE_BYTES:
        raise QualificationError("process-tree accounting release differs")


def _require_safe_python_startup() -> None:
    if (
        sys.flags.isolated != 1
        or sys.flags.ignore_environment != 1
        or sys.flags.no_user_site != 1
        or sys.flags.no_site != 1
        or not bool(sys.flags.safe_path)
        or sys.flags.dont_write_bytecode != 1
        or sys.flags.optimize != 0
    ):
        raise QualificationError("formal execution requires Python -I -S -B startup")


def run_worker(
    binding_path: Path,
    authorization_path: Path,
    assignment_path: Path,
    output: Path,
    progress: Path,
) -> None:
    _require_safe_python_startup()
    _await_tree_accounting_release()
    if {name: os.environ.get(name) for name in THREAD_ENVIRONMENT} != THREAD_ENVIRONMENT:
        raise QualificationError("worker thread environment differs")
    sequence = 0

    def checkpoint(stage: str) -> None:
        nonlocal sequence
        sequence += 1
        _checkpoint(progress, sequence, stage)

    checkpoint("worker-initialized")
    successor_authority = load_authority(binding_path, authorization_path)
    require_active_resource_execution(successor_authority)
    assignment, assignment_sha = read_assignment(successor_authority, assignment_path)
    worker_id = str(assignment["worker_id"])
    checkpoint("authority-and-assignment-verified")
    base = successor_authority.base
    successor = successor_authority.successor
    authority = successor_authority.authority
    program_bytes = successor_authority.verified_program_bytes
    data_bytes = successor_authority.verified_data_bytes
    if program_bytes is None or data_bytes is None:
        raise QualificationError("verified scientific buffers are absent")

    def verified_loader(name: str, path: Path) -> Any:
        return _verified_program_loader(program_bytes, name, path)

    # Protocol-v2 also calls this hook for the batch benchmark.  Keep that
    # execution on the byte buffer captured during authority validation.
    base._load_module = verified_loader
    runtime_paths = [
        Path(successor_authority.binding["execution_target"]).resolve(strict=True),
        Path(
            successor_authority.binding["candidates"]["ANYintelligent"]["root"]
        ).resolve(strict=True),
    ]
    sys.path[:0] = [str(path) for path in runtime_paths]
    bundle = successor.activate_assigned(
        base,
        authority,
        verified_loader=verified_loader,
        verified_data_bytes=data_bytes,
    )
    checkpoint("mechanics-activated")
    if worker_id in STRUCTURAL_WORKERS:
        original = base._structural_authority

        def structural_factory(value: Any, mechanics: Any, diagonal: str) -> Any:
            return successor.structural_authority(
                base,
                value,
                mechanics,
                diagonal,
                base_factory=original,
            )

        base._structural_authority = structural_factory
        # Coordinator authority has already validated and hash-bound all 252
        # rows; do not regenerate the full manifest independently per worker.
        bundle.manifest_generator.build_manifest = lambda: deepcopy(authority.manifest)
        gates, diagnostics, coverage = base._structural_worker(
            authority, bundle, worker_id
        )
    elif worker_id == "EIGEN_PERFORMANCE":
        gates, diagnostics, coverage = base._eigen_worker(authority, bundle)
    elif worker_id == "SPECIAL_ECOSYSTEM":
        base._run_pytest_lane = lambda value, name, cwd, nodes: (
            successor.run_pytest_lane_without_elapsed_ceiling(
                base,
                value,
                name,
                cwd,
                nodes,
                isolation_config_bytes=successor_authority.verified_file_bytes[
                    "preflight_config"
                ],
            )
        )
        lanes, overlay_count = _special_lanes(successor_authority)
        results: list[dict[str, Any]] = []
        for lane in lanes:
            root = Path(str(authority.input["candidates"][lane["repository"]]["root"])).resolve()
            nodes = [
                str(root / node.split("::", 1)[0])
                + ("::" + node.split("::", 1)[1] if "::" in node else "")
                for node in lane["nodes"]
            ]
            results.append(
                base._run_pytest_lane(authority, str(lane["name"]), root, nodes)
            )
        # Preserve complete external diagnostics even when adjudication raises.
        # This file is never canonical scientific evidence.
        base._write_exclusive(
            output.with_name("special-lane-results.json"),
            {str(row["lane"]): row for row in results},
            pretty=True,
        )
        gates, diagnostics, coverage = base._adjudicate_special_lanes(
            lanes,
            results,
            authority.contract["coverage"]["structural"]["special_fixtures"],
        )
        coverage["v3_overlay_lanes"] = overlay_count
    else:
        gates, diagnostics, coverage = base._batch_shard_worker(
            authority,
            bundle,
            int(worker_id.removeprefix("BATCH_")),
        )
    checkpoint("scientific-work-complete")
    base._write_exclusive(output.with_name("diagnostic.json"), diagnostics, pretty=True)
    scientific_payload_sha256 = sha256(
        canonical_bytes(_scientific_projection(worker_id, diagnostics))
    )
    write_exclusive(
        output,
        {
            "assignment_sha256": assignment_sha,
            "coverage": coverage,
            "gates": gates,
            "production_restriction": PRODUCTION_RESTRICTION,
            "schema": WORKER_SCHEMA,
            "scientific_payload_sha256": scientific_payload_sha256,
            "worker_id": worker_id,
        },
    )
    checkpoint("worker-output-complete")


@dataclass(frozen=True)
class ProcessRow:
    worker_id: str
    status: str
    returncode: int
    elapsed_ms: int
    peak_tree_memory_bytes: int
    assignment_sha256: str
    checkpoint_sha256: str
    last_checkpoint: str
    stdout_sha256: str
    stderr_sha256: str


def _environment(
    authority: SuccessorAuthority,
    worker_directory: Path,
) -> dict[str, str]:
    process_environment = authority.binding["runtime_environment"].get(
        "process_environment"
    )
    if not isinstance(process_environment, dict) or not all(
        type(name) is str and type(value) is str
        for name, value in process_environment.items()
    ):
        raise QualificationError("bound process environment differs")
    environment = dict(process_environment)
    environment.update(THREAD_ENVIRONMENT)
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    request_id = os.environ.get(RESOURCE_REQUEST_ENVIRONMENT)
    attempt_sha = os.environ.get(RESOURCE_ATTEMPT_ENVIRONMENT)
    if request_id is not None:
        if len(request_id) != 32 or any(
            character not in "0123456789abcdef" for character in request_id
        ):
            raise QualificationError("resource request environment is malformed")
        environment[RESOURCE_REQUEST_ENVIRONMENT] = request_id
    if attempt_sha is not None:
        if len(attempt_sha) != 64 or any(
            character not in "0123456789ABCDEF" for character in attempt_sha
        ):
            raise QualificationError("resource attempt environment is malformed")
        environment[RESOURCE_ATTEMPT_ENVIRONMENT] = attempt_sha
    environment["ANYSOLVER_S3_V4_CROSS_WHEEL"] = "1"
    environment["ANYSOLVER_S3_V4_TARGET"] = str(
        Path(authority.binding["execution_target"]).resolve()
    )
    cache_root = worker_directory / "runtime-cache"
    cache_paths = {
        "MPLCONFIGDIR": cache_root / "matplotlib",
        "NUMBA_CACHE_DIR": cache_root / "numba",
        "XDG_CACHE_HOME": cache_root / "xdg",
    }
    for path in sorted(set(cache_paths.values()), key=str):
        path.mkdir(parents=True, exist_ok=False)
    environment.update({name: str(path.resolve()) for name, path in cache_paths.items()})
    return environment


def _checkpoint_identity(path: Path) -> tuple[str, str]:
    try:
        raw = path.read_bytes()
    except OSError:
        return "", ""
    last = ""
    for index, row in enumerate(raw.splitlines(keepends=True), start=1):
        value = json.loads(row, object_pairs_hook=_pairs, parse_constant=_reject_constant)
        if (
            not isinstance(value, dict)
            or value.get("sequence") != index
            or type(value.get("stage")) is not str
            or row != canonical_bytes(value)
        ):
            return sha256(raw), ""
        last = value["stage"]
    return sha256(raw) if raw else "", last


def _run_process(
    authority: SuccessorAuthority,
    worker_id: str,
    directory: Path,
    assignment_path: Path,
    assignment_sha: str,
) -> ProcessRow:
    control = authority.control
    if control is None:
        raise QualificationError("verified process-tree controller is absent")
    output = directory / "record.json"
    progress = directory / "progress.ndjson"
    stdout_path = directory / "stdout.log"
    stderr_path = directory / "stderr.log"
    release = directory / "tree-accounting.release"
    frozen_files = authority.verified_file_bytes
    if frozen_files is None:
        raise QualificationError("verified authority file buffers are absent")
    runner_raw = frozen_files["formal_runner"]
    runner_path = ROOT / str(authority.binding["files"]["formal_runner"]["path"])
    command = [
        sys.executable,
        "-I",
        "-S",
        "-B",
        "-c",
        WORKER_BOOTSTRAP,
        str(runner_path),
        str(len(runner_raw)),
        "--worker",
        "--binding",
        str(authority.binding_path),
        "--authorization",
        str(authority.authorization_path),
        "--assignment",
        str(assignment_path),
        "--output",
        str(output),
        "--progress",
        str(progress),
    ]
    environment = _environment(authority, directory)
    environment.pop(control.TREE_RELEASE_ENVIRONMENT, None)
    if os.name == "nt":
        environment[control.TREE_RELEASE_ENVIRONMENT] = str(release.resolve())
    started = time.monotonic_ns()
    status = "SPAWN_FAILED"
    returncode: int | None = None
    peak = -1
    process: Any | None = None
    controller: Any | None = None
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        try:
            process = subprocess.Popen(
                command,
                cwd=directory,
                env=environment,
                stdin=subprocess.PIPE,
                stdout=stdout,
                stderr=stderr,
                creationflags=(
                    int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
                    if os.name == "nt"
                    else 0
                ),
            )
        except (OSError, subprocess.SubprocessError):
            process = None
        if process is not None:
            try:
                controller = control._attach_tree_controller(process, MEMORY_LIMIT_BYTES)
            except (OSError, RuntimeError):
                status = "MEMORY_ACCOUNTING_UNAVAILABLE"
                control._terminate_tree(
                    process,
                    None,
                    deadline_ns=time.monotonic_ns()
                    + int(control.TERMINATION_BUDGET_SECONDS * 1.0e9),
                )
            else:
                try:
                    if os.name == "nt":
                        with release.open("xb") as stream:
                            stream.write(control.TREE_RELEASE_BYTES)
                    if process.stdin is None:
                        raise OSError("verified worker source pipe is unavailable")
                    process.stdin.write(runner_raw)
                    process.stdin.close()
                    status = "RUNNING"
                    previous_activity: tuple[Any, ...] | None = None
                    last_activity = time.monotonic_ns()
                    while True:
                        try:
                            tree_peak, active, cpu = controller.sample_activity()
                        except (OSError, RuntimeError):
                            status = "MEMORY_ACCOUNTING_UNAVAILABLE"
                            break
                        peak = max(peak, int(tree_peak))
                        if tree_peak > MEMORY_LIMIT_BYTES:
                            status = "MEMORY_LIMIT"
                            break
                        returncode = process.poll()
                        if returncode is not None and active == 0:
                            break
                        now = time.monotonic_ns()
                        activity = (
                            cpu,
                            control._file_activity(progress),
                            control._file_activity(stdout_path),
                            control._file_activity(stderr_path),
                        )
                        if previous_activity is None or activity != previous_activity:
                            previous_activity = activity
                            last_activity = now
                        if now - last_activity >= INACTIVITY_SECONDS * 1_000_000_000:
                            status = "INACTIVITY_TIMEOUT"
                            break
                        time.sleep(0.05)
                    if status != "RUNNING":
                        control._terminate_tree(
                            process,
                            controller,
                            deadline_ns=time.monotonic_ns()
                            + int(control.TERMINATION_BUDGET_SECONDS * 1.0e9),
                        )
                    returncode = process.poll()
                    if status == "RUNNING":
                        if returncode == 0 and output.is_file():
                            try:
                                _read_worker(
                                    output,
                                    worker_id,
                                    assignment_sha,
                                    authority,
                                )
                            except (OSError, QualificationError, TypeError, ValueError):
                                status = "MALFORMED_OUTPUT"
                            else:
                                status = "COMPLETE"
                        else:
                            status = "FAILED"
                except OSError:
                    status = "MEMORY_ACCOUNTING_UNAVAILABLE"
                    control._terminate_tree(
                        process,
                        controller,
                        deadline_ns=time.monotonic_ns()
                        + int(control.TERMINATION_BUDGET_SECONDS * 1.0e9),
                    )
            finally:
                if controller is not None:
                    try:
                        controller.close()
                    except (OSError, RuntimeError):
                        status = "MEMORY_ACCOUNTING_UNAVAILABLE"
    if status != "COMPLETE":
        output.unlink(missing_ok=True)
    checkpoint_sha, last_checkpoint = _checkpoint_identity(progress)
    ended = time.monotonic_ns()
    return ProcessRow(
        worker_id,
        status,
        -1 if returncode is None else int(returncode),
        int((ended - started) / 1_000_000),
        peak,
        assignment_sha,
        checkpoint_sha,
        last_checkpoint,
        sha256(stdout_path.read_bytes()),
        sha256(stderr_path.read_bytes()),
    )


def _expected_worker_fields(
    authority: SuccessorAuthority,
    worker_id: str,
) -> tuple[set[str], set[str]]:
    if worker_id == STRUCTURAL_WORKERS[0]:
        return (
            {
                "convergence",
                "interface_resultants",
                "locking",
                "patch_and_equilibrium",
                "pl_participation",
                "symmetry_and_covariance",
                "topology_252",
            },
            {
                "gated_topology_records",
                "global_convergence_records",
                "locking_records",
            },
        )
    if worker_id in STRUCTURAL_WORKERS:
        return (
            {
                "convergence",
                "interface_resultants",
                "pl_participation",
                "topology_252",
            },
            {"gated_topology_records", "global_convergence_records"},
        )
    if worker_id == "EIGEN_PERFORMANCE":
        return (
            {
                "buckling_10",
                "buckling_25",
                "modal_10",
                "modal_25",
                "performance_10",
                "performance_25",
            },
            {"buckling_cases", "modal_cases", "paired_performance_comparisons"},
        )
    if worker_id == "SPECIAL_ECOSYSTEM":
        lanes, _overlay_count = _special_lanes(authority)
        return (
            {f"lane_{row['name']}" for row in lanes},
            {
                "d3_numberings",
                "director_polarities",
                "director_reversal_cases",
                "director_reversal_d3_numberings",
                "registered_special_fixtures",
                "special_collected_tests",
                "special_failed_tests",
                "special_lanes",
                "special_passed_tests",
                "special_requested_nodes",
                "v3_overlay_lanes",
            },
        )
    if worker_id in BATCH_WORKERS:
        return (
            {"equality", "scalar_fallback", "shard_complete"},
            {"batch_elements", "batch_repetitions"},
        )
    raise QualificationError(f"unknown worker identity: {worker_id}")


def _read_worker(
    path: Path,
    worker_id: str,
    assignment_sha: str,
    authority: SuccessorAuthority,
) -> dict[str, Any]:
    _raw, value = read_json(path)
    if set(value) != {
        "assignment_sha256",
        "coverage",
        "gates",
        "production_restriction",
        "schema",
        "scientific_payload_sha256",
        "worker_id",
    }:
        raise QualificationError(f"{worker_id} worker fields differ")
    if (
        value["schema"] != WORKER_SCHEMA
        or value["worker_id"] != worker_id
        or value["assignment_sha256"] != assignment_sha
        or value["production_restriction"] != PRODUCTION_RESTRICTION
        or not isinstance(value["coverage"], dict)
        or not isinstance(value["gates"], dict)
        or type(value["scientific_payload_sha256"]) is not str
        or len(value["scientific_payload_sha256"]) != 64
        or any(
            character not in "0123456789ABCDEF"
            for character in value["scientific_payload_sha256"]
        )
    ):
        raise QualificationError(f"{worker_id} worker identity differs")
    expected_gates, expected_coverage = _expected_worker_fields(authority, worker_id)
    if (
        set(value["gates"]) != expected_gates
        or any(type(item) is not bool for item in value["gates"].values())
        or set(value["coverage"]) != expected_coverage
        or any(
            type(item) is not int or item < 0
            for item in value["coverage"].values()
        )
    ):
        raise QualificationError(f"{worker_id} worker gate or coverage schema differs")
    return value


def _scientific_projection(worker_id: str, diagnostics: Mapping[str, Any]) -> object:
    """Select deterministic science while keeping raw timing diagnostics external."""

    if worker_id in STRUCTURAL_WORKERS:
        return diagnostics
    if worker_id == "EIGEN_PERFORMANCE":
        return {
            key: diagnostics[key]
            for key in sorted(diagnostics)
            if key.startswith("modal_") or key.startswith("buckling_")
        }
    if worker_id == "SPECIAL_ECOSYSTEM":
        projection: dict[str, Any] = {}
        for lane in sorted(diagnostics):
            row = diagnostics[lane]
            if not isinstance(row, dict):
                raise QualificationError("special diagnostic row differs")
            if set(row) != {
                "passed",
                "report",
                "requested_node_count",
                "returncode",
                "status",
                "stderr",
                "stdout",
            }:
                raise QualificationError("special diagnostic schema differs")
            projection[lane] = {
                key: row[key]
                for key in (
                    "passed",
                    "report",
                    "requested_node_count",
                    "returncode",
                    "status",
                )
            }
        return projection
    if worker_id in BATCH_WORKERS:
        return {}
    raise QualificationError(f"unknown scientific projection worker: {worker_id}")


def _coverage_complete(coverage: Mapping[str, int], authority: SuccessorAuthority) -> bool:
    special_lanes, overlay_count = _special_lanes(authority)
    return bool(
        all(
            coverage.get(f"{worker.lower()}::gated_topology_records") == 84
            and coverage.get(f"{worker.lower()}::global_convergence_records") == 84
            for worker in STRUCTURAL_WORKERS
        )
        and sum(
            coverage.get(f"{worker.lower()}::gated_topology_records", 0)
            for worker in STRUCTURAL_WORKERS
        )
        == 252
        and coverage.get("structural_slash::locking_records") == 18
        and coverage.get("eigen_performance::modal_cases") == 2
        and coverage.get("eigen_performance::buckling_cases") == 2
        and coverage.get("eigen_performance::paired_performance_comparisons") == 24
        and coverage.get("special_ecosystem::special_lanes")
        == len(special_lanes)
        and coverage.get("special_ecosystem::registered_special_fixtures") == 8
        and coverage.get("special_ecosystem::v3_overlay_lanes") == overlay_count
        and coverage.get("special_ecosystem::d3_numberings") == 6
        and coverage.get("special_ecosystem::director_polarities") == 2
        and coverage.get("special_ecosystem::director_reversal_cases") == 12
        and coverage.get("special_ecosystem::director_reversal_d3_numberings") == 6
        and coverage.get("special_ecosystem::special_failed_tests") == 0
        and coverage.get("special_ecosystem::special_collected_tests")
        == coverage.get("special_ecosystem::special_passed_tests")
        and coverage.get("special_ecosystem::special_collected_tests", 0) > 0
        and sum(
            coverage.get(f"{worker.lower()}::batch_repetitions", 0)
            for worker in BATCH_WORKERS
        )
        == 12
        and all(
            coverage.get(f"{worker.lower()}::batch_elements") == 4096
            for worker in BATCH_WORKERS
        )
    )


def run_cycle(authority: SuccessorAuthority, output_root: Path) -> tuple[bytes, dict[str, Any]]:
    output_root.mkdir(parents=True, exist_ok=False)
    assignments: dict[str, tuple[Path, str]] = {}
    for worker_id in WORKERS:
        directory = output_root / worker_id.lower()
        directory.mkdir()
        assignment = build_assignment(authority, worker_id)
        path = directory / "assignment.json"
        write_exclusive(path, assignment)
        assignments[worker_id] = (path, sha256(path.read_bytes()))
    rows: list[ProcessRow] = []
    for wave in WAVES:
        with ThreadPoolExecutor(max_workers=3, thread_name_prefix="s3-v3") as pool:
            futures = {
                pool.submit(
                    _run_process,
                    authority,
                    worker_id,
                    output_root / worker_id.lower(),
                    assignments[worker_id][0],
                    assignments[worker_id][1],
                ): worker_id
                for worker_id in wave
            }
            for future in as_completed(futures):
                worker_id = futures[future]
                try:
                    rows.append(future.result())
                except Exception:
                    rows.append(
                        ProcessRow(
                            worker_id,
                            "COORDINATOR_CHILD_ERROR",
                            -1,
                            0,
                            -1,
                            assignments[worker_id][1],
                            "",
                            "",
                            "",
                            "",
                        )
                    )
    rows.sort(key=lambda item: WORKERS.index(item.worker_id))
    blocked = len(rows) != len(WORKERS) or any(row.status != "COMPLETE" for row in rows)
    gates: dict[str, bool] = {}
    coverage: dict[str, int] = {}
    worker_evidence: dict[str, dict[str, str]] = {}
    for row in rows:
        if row.status != "COMPLETE":
            continue
        try:
            worker = _read_worker(
                output_root / row.worker_id.lower() / "record.json",
                row.worker_id,
                row.assignment_sha256,
                authority,
            )
            worker_path = output_root / row.worker_id.lower() / "record.json"
            diagnostic_path = output_root / row.worker_id.lower() / "diagnostic.json"
            diagnostic_raw = diagnostic_path.read_bytes()
            _diagnostic_value = json.loads(
                diagnostic_raw,
                object_pairs_hook=_pairs,
                parse_constant=_reject_constant,
            )
            if not isinstance(_diagnostic_value, dict):
                raise QualificationError("worker diagnostic is not an object")
            observed_projection = sha256(
                canonical_bytes(
                    _scientific_projection(row.worker_id, _diagnostic_value)
                )
            )
            if observed_projection != worker["scientific_payload_sha256"]:
                raise QualificationError("worker scientific payload differs")
            worker_evidence[row.worker_id] = {
                "diagnostic_sha256": sha256(diagnostic_raw),
                "record_sha256": sha256(worker_path.read_bytes()),
                "scientific_payload_sha256": observed_projection,
            }
            for name, passed in worker["gates"].items():
                key = f"{row.worker_id.lower()}::{name}"
                if key in gates:
                    raise QualificationError("duplicate worker gate")
                gates[key] = passed
            for name, count in worker["coverage"].items():
                coverage[f"{row.worker_id.lower()}::{name}"] = count
        except (KeyError, OSError, QualificationError, TypeError, ValueError):
            blocked = True
    if not blocked and not _coverage_complete(coverage, authority):
        blocked = True
    if not blocked:
        try:
            batch_gates, batch_diagnostic = authority.base._aggregate_batch_shards(
                authority.authority, output_root
            )
            expected_batch_gates = {
                "candidate_hot_path",
                "complete_registered_repetitions",
                "recovery_throughput",
                "stiffness_throughput",
                "warm_s3_vs_q4",
            }
            if (
                not isinstance(batch_gates, dict)
                or set(batch_gates) != expected_batch_gates
                or any(type(value) is not bool for value in batch_gates.values())
            ):
                raise QualificationError("batch aggregate gate schema differs")
            gates.update(
                {f"batch_aggregate::{name}": value for name, value in batch_gates.items()}
            )
            authority.base._write_exclusive(
                output_root / "batch-aggregate-diagnostic.json",
                batch_diagnostic,
                pretty=True,
            )
            aggregate_path = output_root / "batch-aggregate-diagnostic.json"
            worker_evidence["BATCH_AGGREGATE"] = {
                "diagnostic_sha256": sha256(aggregate_path.read_bytes()),
                "record_sha256": "",
                "scientific_payload_sha256": "",
            }
        except (OSError, KeyError, QualificationError, TypeError, ValueError):
            blocked = True
    if not blocked:
        try:
            refreshed = load_authority(
                authority.binding_path,
                authority.authorization_path,
            )
            require_active_resource_execution(refreshed)
            if (
                refreshed.binding_raw != authority.binding_raw
                or refreshed.authorization_raw != authority.authorization_raw
            ):
                raise QualificationError("final authority bytes differ")
        except (OSError, QualificationError, subprocess.SubprocessError):
            blocked = True
    terminal = (
        TERMINALS[0]
        if blocked
        else TERMINALS[1]
        if not gates or not all(gates.values())
        else TERMINALS[2]
    )
    scientific = {
        "assignment_sha256": {
            worker_id: assignments[worker_id][1] for worker_id in WORKERS
        },
        "authorization_sha256": sha256(authority.authorization_raw),
        "candidate_binding_sha256": sha256(authority.binding_raw),
        "candidate_commits": {
            name: authority.binding["candidates"][name]["commit"]
            for name in sorted(authority.binding["candidates"])
        },
        "production_restriction": PRODUCTION_RESTRICTION,
        "terminal": terminal,
    }
    if blocked:
        scientific["schema"] = "anysolver.e4-pl-s3-default-activation-blocked-v3"
    else:
        scientific["coverage"] = coverage
        scientific["gates"] = gates
        scientific["schema"] = SCIENTIFIC_SCHEMA
        scientific["worker_scientific_payload_sha256"] = {
            worker_id: worker_evidence[worker_id]["scientific_payload_sha256"]
            for worker_id in WORKERS
        }
    raw = canonical_bytes(scientific)
    if blocked:
        _stage_bytes(output_root / ".pending-blocked.json", raw)
        _publish_staged(
            output_root / ".pending-blocked.json",
            output_root / "blocked.json",
            expected_raw=raw,
        )
    else:
        _stage_bytes(output_root / ".pending-scientific.json", raw)
    process_binding = {
        "inactivity_watchdog_seconds": INACTIVITY_SECONDS,
        "memory_limit_bytes_per_complete_tree": MEMORY_LIMIT_BYTES,
        "runtime_classification": False,
        "total_runtime_limit_seconds": None,
        "worker_evidence": worker_evidence,
        "workers": [row.__dict__ for row in rows],
    }
    write_exclusive(output_root / "process-binding.json", process_binding)
    return raw, scientific


def run_cycles(
    authority: SuccessorAuthority, output_root: Path, cycles: int
) -> dict[str, Any]:
    if cycles != 2:
        raise QualificationError("exactly two cycles are required")
    output_root.mkdir(parents=True, exist_ok=False)
    records = [run_cycle(authority, output_root / "cycle-1")]
    # A second complete scientific cycle is a preregistered replicate, not a
    # retry.  Only a process/evidence block prevents its launch.
    if records[0][1]["terminal"] != TERMINALS[0]:
        records.append(run_cycle(authority, output_root / "cycle-2"))
    identical = len(records) == 2 and records[0][0] == records[1][0]
    terminal = records[0][1]["terminal"] if len(records) == 1 else (
        TERMINALS[0] if not identical else records[1][1]["terminal"]
    )
    try:
        refreshed = load_authority(
            authority.binding_path,
            authority.authorization_path,
        )
        require_active_resource_execution(refreshed)
        if (
            refreshed.binding_raw != authority.binding_raw
            or refreshed.authorization_raw != authority.authorization_raw
        ):
            raise QualificationError("publication authority bytes differ")
    except (OSError, QualificationError, subprocess.SubprocessError):
        terminal = TERMINALS[0]
        identical = False
    process_hashes = [
        sha256((output_root / f"cycle-{index}" / "process-binding.json").read_bytes())
        for index in range(1, len(records) + 1)
    ]
    value = {
        "cycle_record_sha256": [sha256(raw) for raw, _value in records],
        "cycles_completed": len(records),
        "process_binding_sha256": process_hashes,
        "production_restriction": PRODUCTION_RESTRICTION,
        "publication_commit_marker": "cycle-set.json",
        "runtime_classification": False,
        "schema": CYCLE_SET_SCHEMA,
        "scientific_byte_identical": identical,
        "terminal": terminal,
        "total_runtime_limit_seconds": None,
    }
    cycle_set_raw = canonical_bytes(value)
    pending = output_root / ".pending-cycle-set.json"
    _stage_bytes(pending, cycle_set_raw)
    if terminal in {TERMINALS[1], TERMINALS[2]} and identical:
        for index in (1, 2):
            _publish_staged(
                output_root / f"cycle-{index}" / ".pending-scientific.json",
                output_root / f"cycle-{index}" / "scientific.json",
                expected_raw=records[index - 1][0],
            )
        for index in (1, 2):
            if (
                output_root / f"cycle-{index}" / "scientific.json"
            ).read_bytes() != records[index - 1][0]:
                raise QualificationError(
                    "canonical scientific bytes changed before publication marker"
                )
    # The final marker commits the multi-file publication.  Scientific files
    # without this schema-valid marker are incomplete recovery state, not
    # canonical qualification evidence.
    _publish_staged(
        pending,
        output_root / "cycle-set.json",
        expected_raw=cycle_set_raw,
    )
    return value


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--authority-only", action="store_true")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--assignment", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--progress", type=Path)
    parser.add_argument("--cycles", type=int, choices=(2,))
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.worker:
            if args.assignment is None or args.output is None or args.progress is None:
                raise QualificationError("worker paths are incomplete")
            run_worker(
                args.binding,
                args.authorization,
                args.assignment,
                args.output,
                args.progress,
            )
            return 0
        if not args.authority_only:
            _require_safe_python_startup()
        if args.authority_only:
            authority = load_authority(args.binding, args.authorization)
            print(sha256(authority.binding_raw))
            return 0
        if args.cycles is None or args.output_root is None:
            raise QualificationError("coordinator requires --cycles and --output-root")
        _preclaim_launched_resource(args.output_root)
        authority = load_authority(args.binding, args.authorization)
        require_active_resource_execution(authority)
        resource_arguments = authority.authorization["resource_execution"][
            "coordinator_arguments"
        ]
        if list(sys.argv[1:]) != resource_arguments:
            raise QualificationError("coordinator invocation differs from approved request")
        value = run_cycles(authority, args.output_root, args.cycles)
        print(value["terminal"])
        return 0 if value["terminal"] == TERMINALS[2] else 2
    except (OSError, QualificationError, subprocess.SubprocessError) as exc:
        print(f"qualification blocked: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
