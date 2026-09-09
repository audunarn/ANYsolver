"""One-use, ledger-backed executor for the GE-Beam3 P4 reference gate.

This successor is intentionally unable to author requests, approvals, or
authority overlays.  It validates a separately committed authority and review,
the workspace-wide resource-manager lifecycle, and then reuses only the frozen
C1 runner's low-level authority and cycle functions.  C1's disposable aggregate
and adjudicator remain nonclassifying and are never invoked here.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence


STUDY_ID = "study_ge_beam3.curved_mixed_q2_reference_core_v1"
CANDIDATE_ID = "CANDIDATE_GE_BEAM3_DC_MIXED_CURVED_Q2_MACRO_V1"
AUTHORITY_SCHEMA = "anysolver.ge-beam3-curved-p4-scientific-authority-v1"
REVIEW_SCHEMA = "anysolver.ge-beam3-curved-p4-scientific-execution-review-v1"
EXECUTOR_REVIEW_SCHEMA = "anysolver.ge-beam3-curved-p4-scientific-executor-review-v1"
CLAIM_SCHEMA = "anysolver.ge-beam3-curved-p4-scientific-claim-v1"
RECEIPT_SCHEMA = "anysolver.ge-beam3-curved-p4-scientific-receipt-v1"
PENDING_SCHEMA = "anysolver.ge-beam3-curved-p4-scientific-pending-v1"
RESULT_SCHEMA = "anysolver.ge-beam3-curved-p4-scientific-result-v1"
BLOCKED_AUTHORITY = "BLOCKED_GE_BEAM3_P4_BASELINE_OR_AUTHORITY"
BLOCKED_PROCESS = "BLOCKED_GE_BEAM3_P4_REFERENCE_PROCESS_OR_EVIDENCE"
NO_GO_REGULARITY = "NO_GO_GE_BEAM3_P4_REFERENCE_REGULARITY"
NO_GO_FRAME = "NO_GO_GE_BEAM3_P4_REFERENCE_FRAME_IDENTITY"
NO_GO_COVARIANCE = "NO_GO_GE_BEAM3_P4_REFERENCE_REVERSAL_OR_OBJECTIVITY"
PASS = "PROVISIONAL_GO_GE_BEAM3_P4_PRIVATE_CURVED_REFERENCE_CORE"
RESTRICTION = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"

C1 = {
    "commit": "780991f7adea6fb4dc2da9fcdeca1d37379bf2ba",
    "parent": "8fcf827b6e5364f0e1bc8221a3f74602e3f39261",
    "subject": "test: freeze GE Beam3 curved P4 reference harness",
    "tree": "3b14a1ba42a47cd186b299539196731c4505a408",
}
C2 = {
    "commit": "20e895e8803de086b8abf19e3183e4d6a3b96fd6",
    "parent": C1["commit"],
    "subject": "docs: review GE Beam3 curved P4 reference harness",
    "tree": "76743dd2167b7accf2f480f5606d0095a5513b7a",
}
C2_REVIEW = {
    "bytes": 2909,
    "sha256": "43724089DB9A7A3C249548A88C31ADE756FEF383C1EA0627B39ECF22A236F976",
}
FROZEN_AUTHORITY_MANIFEST_SHA256 = (
    "13308601CA45CE5DB7CB8A32138ABB273560F1EF426F0763E45F59618D46F7F7"
)
FROZEN_C1_PROGRAMS = {
    "checker": {
        "bytes": 93225,
        "path": "docs/reference_cases/ge_beam3_curved_p4_reference_checker.py",
        "sha256": "018C3A84FA89EA9C460C9E2951EE6F694B015BA2E100696DBF77C47BB9CB3083",
    },
    "producer": {
        "bytes": 58885,
        "path": "docs/reference_cases/ge_beam3_curved_p4_reference_producer.py",
        "sha256": "CD61E00D06B48E9905799AE0C83E3EECB9E0692339ECEC3E9D9BAD090078B725",
    },
    "runner": {
        "bytes": 65783,
        "path": "docs/reference_cases/ge_beam3_curved_p4_reference_runner.py",
        "sha256": "7D61E0A10D9291046F2F7B5A8429100AF399711BB13D33FB29BD250CCC68B2CD",
    },
}
FROZEN_PROTECTED_STRAIGHT_BLOBS = {
    "pyproject.toml": "16da1c1ca1be9f56de4c0c3505cdfabb8752bd99",
    "src/anysolver/__init__.py": "2aa4911f538b6cb08e66dbb4590d0d1545dd7560",
    "src/anysolver/elements.py": "4dfe4212b9ee9947969b087809e72b9973e88e07",
    "src/anysolver/ge_beam3_element.py": "70542da7fea26dcb2da5b5f9da5fc0b0b8d484ab",
    "src/anysolver/ge_beam3_mixed_element.py": "f49062b55b4bf749a1654100cf3a4ed6ffb61d37",
    "src/anysolver/ge_beam3_mixed_state.py": "74caa1814448245f907bd3efdb6c8a1cc1d2269d",
    "src/anysolver/ge_beam3_state.py": "ba8f65761197c62cb2b7ce74bf488e75f2c24818",
}
EXPECTED_C4_TEST_COUNT = 132
C3_SUBJECT = "test: add ledger-backed GE Beam3 curved P4 executor"
C3_PATHS = (
    "docs/reference_cases/ge_beam3_curved_p4_scientific_executor.py",
    "tests/test_ge_beam3_curved_p4_scientific_executor.py",
)
C4_SUBJECT = "docs: review GE Beam3 curved P4 scientific executor"
C4_PATHS = ("docs/reference_cases/ge_beam3_curved_p4_scientific_executor_review.json",)
C2_REVIEW_RELATIVE = "docs/reference_cases/ge_beam3_curved_p4_harness_review.json"
C5_SUBJECT = "docs: authorize GE Beam3 curved P4 reference execution"
C5_PATHS = (
    "docs/reference_cases/ge_beam3_curved_p4_scientific_authority.json",
    "docs/reference_cases/ge_beam3_curved_p4_scientific_execution_review.json",
)
AUTHORITY_RELATIVE = C5_PATHS[0]
REVIEW_RELATIVE = C5_PATHS[1]
RUNNER_RELATIVE = "docs/reference_cases/ge_beam3_curved_p4_reference_runner.py"
RESOURCE_MANAGER = Path(r"C:\Github\.resource-manager")
BOUNDS = {
    "child_timeout_seconds": 600,
    "inactivity_seconds": 300,
    "memory_limit_bytes": 24 * (1 << 30),
    "wave_timeout_seconds": 1800,
}
THREAD_VARIABLES = (
    "BLIS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS",
    "NUMEXPR_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
    "TBB_NUM_THREADS",
)
HEX32 = re.compile(r"[0-9a-f]{32}\Z")
OID = re.compile(r"[0-9a-f]{40}\Z")
SHA256 = re.compile(r"[0-9A-F]{64}\Z")
TERMINALS = (
    BLOCKED_AUTHORITY,
    BLOCKED_PROCESS,
    NO_GO_REGULARITY,
    NO_GO_FRAME,
    NO_GO_COVARIANCE,
    PASS,
)


class ExecutionError(RuntimeError):
    """The authority, resource lifecycle, process, or evidence is invalid."""


@dataclass(frozen=True)
class ValidatedAuthority:
    repository: Path
    authority: dict[str, Any]
    authority_raw: bytes
    review_raw: bytes
    request: dict[str, Any]
    request_raw: bytes
    c3: dict[str, str]
    c4: dict[str, str]
    c5: dict[str, str]


@dataclass(frozen=True)
class Claim:
    request_id: str
    attempt_id: str
    active_lock: Path
    owner_raw: bytes
    request_claim: Path
    attempt_claim: Path
    receipt: Path
    claim_raw: bytes
    request_claim_mtime_ns: int
    attempt_claim_mtime_ns: int


def canonical_bytes(value: Any) -> bytes:
    """Return strict, deterministic ASCII JSON; reject non-finite numbers."""

    def visit(item: Any) -> None:
        if item is None or type(item) in (bool, int, str):
            return
        if type(item) is float:
            if not math.isfinite(item):
                raise ExecutionError("nonfinite JSON number")
            return
        if type(item) is list:
            for member in item:
                visit(member)
            return
        if type(item) is dict:
            if not all(type(key) is str for key in item):
                raise ExecutionError("JSON object key is not a string")
            for member in item.values():
                visit(member)
            return
        raise ExecutionError(f"unsupported JSON value: {type(item).__name__}")

    visit(value)
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                       allow_nan=False) + "\n").encode("ascii")


def _strict_json_bytes(raw: bytes, label: str) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        made: dict[str, Any] = {}
        for key, value in pairs:
            if key in made:
                raise ExecutionError(f"duplicate JSON key in {label}: {key}")
            made[key] = value
        return made

    def reject(value: str) -> None:
        raise ExecutionError(f"nonfinite JSON value in {label}: {value}")

    try:
        value = json.loads(raw.decode("ascii"), object_pairs_hook=unique,
                           parse_constant=reject)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExecutionError(f"malformed JSON: {label}") from exc
    if type(value) is not dict or raw != canonical_bytes(value):
        raise ExecutionError(f"noncanonical JSON: {label}")
    return value


def _is_reparse(path: Path) -> bool:
    try:
        return bool(getattr(path.lstat(), "st_file_attributes", 0) &
                    getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    except OSError:
        return True


def _regular_bytes(path: Path, label: str) -> bytes:
    if path.is_symlink() or _is_reparse(path) or not path.is_file():
        raise ExecutionError(f"{label} is not a regular file")
    return path.read_bytes()


def strict_json(path: Path, label: str | None = None) -> tuple[bytes, dict[str, Any]]:
    raw = _regular_bytes(path, label or path.name)
    return raw, _strict_json_bytes(raw, label or path.name)


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _identity(path: Path, label: str) -> dict[str, Any]:
    raw = _regular_bytes(path, label)
    return {"bytes": len(raw), "sha256": _sha(raw)}


def _exact(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != keys:
        raise ExecutionError(f"{label} keys differ")
    return value


def _write_once(path: Path, value: Mapping[str, Any]) -> bytes:
    raw = canonical_bytes(dict(value))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return raw


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


# Trust, authority, resource-lifecycle, cycle, and publication routines follow.


def _base_environment() -> dict[str, str]:
    """Build a Git/Python environment with user-controlled injection disabled."""

    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    null = "NUL" if os.name == "nt" else "/dev/null"
    environment = {
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": null,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "PATH": os.environ.get("PATH", ""),
        "PATHEXT": os.environ.get("PATHEXT", ".EXE"),
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
        "PYTHONSAFEPATH": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "SystemRoot": system_root,
    }
    return environment


def _git_executable() -> Path:
    made = shutil.which("git", path=os.environ.get("PATH", ""))
    if made is None:
        raise ExecutionError("Git executable is unavailable")
    path = Path(made).resolve(strict=True)
    if path.is_symlink() or _is_reparse(path) or not path.is_file():
        raise ExecutionError("Git executable is indirect")
    return path


def _git(repository: Path, *arguments: str, binary: bool = False) -> str | bytes:
    null = "NUL" if os.name == "nt" else "/dev/null"
    command = [
        str(_git_executable()),
        "--no-replace-objects",
        "-c", f"core.attributesFile={null}",
        "-c", f"core.hooksPath={null}",
        "-c", f"safe.directory={repository}",
        *arguments,
    ]
    result = subprocess.run(
        command,
        cwd=repository,
        env=_base_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ExecutionError(detail or f"Git command failed: {' '.join(arguments)}")
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


def _commit_identity(repository: Path, commit: str) -> dict[str, str]:
    lines = str(_git(repository, "show", "-s", "--format=%H%n%T%n%P%n%s", commit)).splitlines()
    if len(lines) != 4 or not all(OID.fullmatch(value) for value in lines[:3]):
        raise ExecutionError("commit identity is malformed")
    return {"commit": lines[0], "tree": lines[1], "parent": lines[2], "subject": lines[3]}


def _changed_paths(repository: Path, commit: str) -> tuple[str, ...]:
    raw = str(_git(repository, "diff-tree", "--no-commit-id", "--name-only", "-r", commit))
    return tuple(sorted(line for line in raw.splitlines() if line))


def _blob_identity(repository: Path, commit: str, relative: str) -> dict[str, Any]:
    raw = _git(repository, "cat-file", "blob", f"{commit}:{relative}", binary=True)
    assert isinstance(raw, bytes)
    return {"bytes": len(raw), "sha256": _sha(raw)}


def _require_commit(
    repository: Path,
    commit: str,
    *,
    parent: str,
    subject: str,
    paths: Sequence[str],
    tree: str | None = None,
) -> dict[str, str]:
    actual = _commit_identity(repository, commit)
    if actual["parent"] != parent or actual["subject"] != subject:
        raise ExecutionError("commit overlay identity differs")
    if tree is not None and actual["tree"] != tree:
        raise ExecutionError("commit tree differs")
    if _changed_paths(repository, commit) != tuple(sorted(paths)):
        raise ExecutionError("commit overlay path extent differs")
    return actual


def _require_unmodified_git_graph(repository: Path) -> None:
    repository = repository.resolve(strict=True)
    if repository.is_symlink() or _is_reparse(repository) or not repository.is_dir():
        raise ExecutionError("repository path is indirect")
    if _git(repository, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ExecutionError("authority repository is dirty")
    if _git(repository, "for-each-ref", "--format=%(refname)", "refs/replace"):
        raise ExecutionError("Git replacement objects are forbidden")
    git_dir = Path(str(_git(repository, "rev-parse", "--absolute-git-dir")))
    common = Path(str(_git(repository, "rev-parse", "--git-common-dir")))
    if not common.is_absolute():
        common = (repository / common).resolve()
    for candidate in (
        git_dir / "info/grafts",
        common / "info/grafts",
        common / "objects/info/alternates",
        common / "shallow",
    ):
        if candidate.exists() and candidate.read_bytes().strip():
            raise ExecutionError(f"Git graph indirection is forbidden: {candidate.name}")
    config = str(_git(repository, "config", "--show-origin", "--list", binary=False))
    for line in config.splitlines():
        lowered = line.lower()
        if "core.attributesfile" in lowered and (lowered.endswith("=nul") or lowered.endswith("=/dev/null")) and "command line:" in lowered:
            continue
        if any(token in lowered for token in ("include.path", "includeif.", "core.attributesfile")):
            raise ExecutionError("external Git configuration is active")


def _validate_identity(value: Any, label: str) -> dict[str, Any]:
    row = _exact(value, {"bytes", "sha256"}, label)
    if type(row["bytes"]) is not int or row["bytes"] <= 0 or not SHA256.fullmatch(str(row["sha256"])):
        raise ExecutionError(f"{label} identity is malformed")
    return row


def _validate_commit_row(value: Any, label: str) -> dict[str, str]:
    row = _exact(value, {"commit", "parent", "subject", "tree"}, label)
    if not all(type(row[key]) is str for key in row):
        raise ExecutionError(f"{label} fields are malformed")
    if not all(OID.fullmatch(row[key]) for key in ("commit", "parent", "tree")) or not row["subject"]:
        raise ExecutionError(f"{label} identity is malformed")
    return row


def _parse_timestamp(value: Any, label: str) -> None:
    if type(value) is not str or not value or value.endswith("z"):
        raise ExecutionError(f"{label} timestamp is malformed")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ExecutionError(f"{label} timestamp is malformed") from exc
    if parsed.tzinfo is None:
        raise ExecutionError(f"{label} timestamp lacks an offset")


def _ledger_rows(raw: bytes) -> list[list[str]]:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ExecutionError("resource ledger is not UTF-8") from exc
    rows: list[list[str]] = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        if not line.endswith("|"):
            raise ExecutionError("resource ledger pipe row is malformed")
        fields = [field.strip() for field in line[1:-1].split("|")]
        if len(fields) != 8:
            raise ExecutionError("resource ledger row width differs")
        if fields[1] == "Request ID" or set(fields) == {"---"}:
            continue
        if fields[0].startswith("---"):
            continue
        if any(not field for field in fields):
            raise ExecutionError("resource ledger contains an empty field")
        rows.append(fields)
    return rows


def _prefix_through_row(raw: bytes, target: Sequence[str]) -> bytes:
    cumulative = b""
    matches: list[bytes] = []
    for raw_line in raw.splitlines(keepends=True):
        cumulative += raw_line
        try:
            line = raw_line.decode("utf-8-sig").rstrip("\r\n")
        except UnicodeDecodeError as exc:
            raise ExecutionError("resource ledger is not UTF-8") from exc
        if not line.startswith("|") or not line.endswith("|"):
            continue
        fields = [field.strip() for field in line[1:-1].split("|")]
        if fields == list(target):
            matches.append(cumulative)
    if len(matches) != 1:
        raise ExecutionError("bound ledger row is not uniquely serialized")
    return matches[0]


def _powershell_quote(value: str) -> str:
    if "\r" in value or "\n" in value or "\x00" in value:
        raise ExecutionError("request argv contains a forbidden character")
    return "'" + value.replace("'", "''") + "'"


def expected_request_command(argv: Sequence[str]) -> str:
    if type(argv) not in (list, tuple) or not argv or any(type(token) is not str or not token for token in argv):
        raise ExecutionError("request argv is malformed")
    # The workspace manager stores the exact Windows command line.  The frozen
    # C1 runner itself supplies the one-thread/private-environment child policy.
    return subprocess.list2cmdline(list(argv))


def approval_ledger_note(authority: Mapping[str, Any]) -> str:
    request = authority["request"]
    c3 = authority["commits"]["c3"]
    c4 = authority["commits"]["c4"]
    return (
        "User approved one-use GE-Beam3 P4 private-reference execution; "
        f"request bytes {request['record']['bytes']} SHA-256 {request['record']['sha256']}; "
        f"C3 commit {c3['commit']} tree {c3['tree']}; "
        f"C4 commit {c4['commit']} tree {c4['tree']}; "
        "no retry, activation, publication, selector, or default change."
    )


def execution_started_ledger_note(authority: Mapping[str, Any]) -> str:
    request = authority["request"]
    c4 = authority["commits"]["c4"]
    return (
        f"Attempt {request['attempt_id']}; request SHA-256 {request['record']['sha256']}; "
        f"C4 commit {c4['commit']} tree {c4['tree']}; exact command once; no retry."
    )


def _validate_request_record(
    request: Any,
    *,
    request_id: str,
    repository: Path,
    command: str,
) -> dict[str, Any]:
    row = _exact(
        request,
        {"command", "estimate_minutes", "repository", "request_id", "requested_at", "status", "task"},
        "resource request",
    )
    if row["request_id"] != request_id or HEX32.fullmatch(str(row["request_id"])) is None:
        raise ExecutionError("resource request ID differs")
    if row["status"] != "PENDING" or row["repository"] != str(repository) or row["command"] != command:
        raise ExecutionError("resource request scope differs")
    if type(row["task"]) is not str or not row["task"]:
        raise ExecutionError("resource request task is malformed")
    if type(row["estimate_minutes"]) is not int or row["estimate_minutes"] <= 0:
        raise ExecutionError("resource request estimate is malformed")
    _parse_timestamp(row["requested_at"], "request")
    return row


def validate_request_and_ledger(
    authority: Mapping[str, Any],
    *,
    repository: Path,
    resource_manager: Path = RESOURCE_MANAGER,
    allow_terminal: bool = False,
) -> tuple[dict[str, Any], bytes, list[list[str]]]:
    """Validate the immutable request and exact approved/started ledger prefix."""

    request_binding = _exact(
        authority["request"],
        {"attempt_id", "argv", "command", "record", "request_id"},
        "authority request",
    )
    request_id = request_binding["request_id"]
    attempt_id = request_binding["attempt_id"]
    if (
        HEX32.fullmatch(str(request_id)) is None
        or HEX32.fullmatch(str(attempt_id)) is None
        or request_id == attempt_id
        or type(request_binding["argv"]) is not list
        or not all(type(member) is str for member in request_binding["argv"])
        or type(request_binding["command"]) is not str
        or not request_binding["command"]
    ):
        raise ExecutionError("authority request identity is malformed")
    if request_binding["command"] != expected_request_command(request_binding["argv"]):
        raise ExecutionError("resource request command is not the exact registered argv")
    record_identity = _validate_identity(request_binding["record"], "request record")
    manager_binding = _exact(
        authority["resource_manager"],
        {
            "acquire", "approved_ledger_prefix", "approved_row", "execution_started_row",
            "ledger", "release", "root",
        },
        "resource manager",
    )
    if manager_binding["root"] != str(resource_manager):
        raise ExecutionError("resource-manager root differs")
    root = resource_manager.resolve(strict=True)
    if root != resource_manager or root.is_symlink() or _is_reparse(root):
        raise ExecutionError("resource-manager root is indirect")
    for key, filename in (("acquire", "acquire-test.ps1"), ("release", "release-test.ps1")):
        binding = _exact(manager_binding[key], {"bytes", "filename", "sha256"}, key)
        if binding["filename"] != filename or _identity(root / filename, key) != {
            "bytes": binding["bytes"], "sha256": binding["sha256"]
        }:
            raise ExecutionError(f"resource-manager {key} identity differs")
    request_path = root / "requests" / f"{request_id}.json"
    request_raw, request = strict_json(request_path, "resource request")
    if {"bytes": len(request_raw), "sha256": _sha(request_raw)} != record_identity:
        raise ExecutionError("immutable request identity differs")
    request = _validate_request_record(
        request,
        request_id=request_id,
        repository=repository,
        command=request_binding["command"],
    )
    ledger_name = manager_binding["ledger"]
    if ledger_name != "ledger.md":
        raise ExecutionError("resource ledger filename differs")
    ledger_path = root / ledger_name
    ledger_raw = _regular_bytes(ledger_path, "resource ledger")
    prefix = _exact(manager_binding["approved_ledger_prefix"], {"bytes", "sha256"}, "ledger prefix")
    if type(prefix["bytes"]) is not int or prefix["bytes"] <= 0 or prefix["bytes"] > len(ledger_raw):
        raise ExecutionError("approved ledger prefix length is malformed")
    if not SHA256.fullmatch(str(prefix["sha256"])) or _sha(ledger_raw[: prefix["bytes"]]) != prefix["sha256"]:
        raise ExecutionError("approved ledger prefix differs")
    rows = _ledger_rows(ledger_raw)
    approved = manager_binding["approved_row"]
    started = manager_binding["execution_started_row"]
    if not (type(approved) is list and type(started) is list and len(approved) == len(started) == 8):
        raise ExecutionError("bound ledger rows are malformed")
    if rows.count(approved) != 1 or rows.count(started) != 1 or approved[1:3] != [request_id, "APPROVED"] or started[1:3] != [request_id, "EXECUTION_STARTED"]:
        raise ExecutionError("approved or execution-start ledger row differs")
    for label, row in (("approval", approved), ("execution start", started)):
        _parse_timestamp(row[0], label)
        if (
            row[3] != request["task"]
            or row[4] != request["repository"]
            or row[5] != "Exact command in immutable request JSON"
            or row[6] != f"{request['estimate_minutes']} minutes"
            or not row[7]
        ):
            raise ExecutionError(f"{label} ledger scope differs")
    if approved[7] != approval_ledger_note(authority):
        raise ExecutionError("approval ledger authority binding differs")
    if started[7] != execution_started_ledger_note(authority):
        raise ExecutionError("execution-start attempt/authority binding differs")
    approved_time = dt.datetime.fromisoformat(approved[0].replace("Z", "+00:00"))
    started_time = dt.datetime.fromisoformat(started[0].replace("Z", "+00:00"))
    if started_time <= approved_time:
        raise ExecutionError("resource ledger timestamp chronology differs")
    exact_approved_prefix = _prefix_through_row(ledger_raw, approved)
    if prefix["bytes"] != len(exact_approved_prefix) or ledger_raw[: prefix["bytes"]] != exact_approved_prefix:
        raise ExecutionError("approved ledger prefix chronology does not end at its approval row")
    if rows.index(approved) >= rows.index(started):
        raise ExecutionError("resource ledger chronology differs")
    request_rows = [row for row in rows if row[1] == request_id]
    allowed = {"APPROVED", "EXECUTION_STARTED"}
    statuses = [row[2] for row in request_rows]
    if allow_terminal:
        valid_statuses = (
            ["APPROVED", "EXECUTION_STARTED"],
            ["APPROVED", "EXECUTION_STARTED", "COMPLETED_PASS"],
            ["APPROVED", "EXECUTION_STARTED", "COMPLETED_FAIL"],
        )
    else:
        valid_statuses = (["APPROVED", "EXECUTION_STARTED"],)
    if statuses not in valid_statuses or any(row[2] not in allowed | {"COMPLETED_PASS", "COMPLETED_FAIL"} for row in request_rows):
        raise ExecutionError("request was reused, cancelled, or already terminal")
    return request, request_raw, rows


def validate_active_lock(
    authority: Mapping[str, Any],
    request: Mapping[str, Any],
    *,
    resource_manager: Path = RESOURCE_MANAGER,
) -> tuple[Path, bytes]:
    """Validate the official ``acquire-test.ps1`` owner record without replacing it."""

    active_lock = resource_manager / "active-lock"
    owner_path = active_lock / "owner.json"
    if (
        not active_lock.is_dir()
        or active_lock.is_symlink()
        or _is_reparse(active_lock)
        or {child.name for child in active_lock.iterdir()} != {"owner.json"}
    ):
        raise ExecutionError("official resource-manager active lock is unavailable or malformed")
    owner_raw = _regular_bytes(owner_path, "active-lock owner")
    # PowerShell's ConvertTo-Json output is intentionally not required to be canonical.
    try:
        owner = json.loads(
            owner_raw.decode("utf-8-sig"),
            object_pairs_hook=lambda pairs: _unique_object(pairs, "active-lock owner"),
            parse_constant=lambda value: _reject_json_constant(value, "active-lock owner"),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExecutionError("active-lock owner is malformed") from exc
    owner = _exact(
        owner,
        {"acquired_at", "command", "process_id", "repository", "request_id", "task"},
        "active-lock owner",
    )
    if (
        owner["request_id"] != request["request_id"]
        or owner["repository"] != request["repository"]
        or owner["task"] != request["task"]
        or owner["command"] != request["command"]
        or type(owner["process_id"]) is not int
        or owner["process_id"] <= 0
    ):
        raise ExecutionError("active-lock owner does not match the immutable request")
    _parse_timestamp(owner["acquired_at"], "active-lock acquisition")
    expected_owner = authority["resource_manager"].get("active_lock_owner_sha256")
    if expected_owner is not None and expected_owner != _sha(owner_raw):
        raise ExecutionError("active-lock owner hash differs")
    return active_lock, owner_raw


def _unique_object(pairs: list[tuple[str, Any]], label: str) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise ExecutionError(f"duplicate JSON key in {label}: {key}")
        made[key] = value
    return made


def _reject_json_constant(value: str, label: str) -> None:
    raise ExecutionError(f"nonfinite JSON value in {label}: {value}")


def _validate_review(value: Any, authority_identity: Mapping[str, Any], c4: Mapping[str, str]) -> None:
    review = _exact(
        value,
        {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"},
        "scientific execution review",
    )
    if (
        review["schema"] != REVIEW_SCHEMA
        or review["findings"] != []
        or review["verdict"] != "ACCEPT_GE_BEAM3_CURVED_P4_SCIENTIFIC_EXECUTION_AUTHORITY_NO_P0_P1_P2"
    ):
        raise ExecutionError("scientific execution review is not accepted")
    expected = {
        "authority": {
            "bytes": authority_identity["bytes"],
            "path": AUTHORITY_RELATIVE,
            "sha256": authority_identity["sha256"],
        },
        "authorization_overlay": {
            "exact_paths": list(C5_PATHS),
            "expected_parent": c4["commit"],
            "subject": C5_SUBJECT,
        },
    }
    if review["reviewed_inputs"] != expected:
        raise ExecutionError("scientific execution review input binding differs")
    if review["reviewer_independence"] != {
        "authority_authorship": False,
        "executor_authorship": False,
        "formal_execution_performed": False,
        "harness_authorship": False,
        "review_artifact_authorship": True,
        "reviewer_role": "INDEPENDENT_GE_BEAM3_CURVED_P4_SCIENTIFIC_EXECUTION_REVIEWER",
        "scientific_execution_performed": False,
    }:
        raise ExecutionError("scientific execution review independence differs")


def _validate_executor_review(
    value: Any,
    *,
    c3: Mapping[str, str],
    repository: Path,
) -> None:
    review = _exact(
        value,
        {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"},
        "scientific executor review",
    )
    if (
        review["schema"] != EXECUTOR_REVIEW_SCHEMA
        or review["findings"] != []
        or review["verdict"] != "ACCEPT_GE_BEAM3_CURVED_P4_SCIENTIFIC_EXECUTOR_NO_P0_P1_P2"
    ):
        raise ExecutionError("scientific executor review is not accepted")
    reviewed = _exact(
        review["reviewed_inputs"],
        {"candidate", "candidate_paths", "test_receipts"},
        "executor reviewed inputs",
    )
    if reviewed["candidate"] != dict(c3):
        raise ExecutionError("executor review candidate differs")
    expected_paths = []
    for relative in C3_PATHS:
        identity = _blob_identity(repository, c3["commit"], relative)
        expected_paths.append({**identity, "path": relative})
    if reviewed["candidate_paths"] != expected_paths:
        raise ExecutionError("executor review changed-path binding differs")
    receipts = reviewed["test_receipts"]
    expected_tests = [
        "tests/test_ge_beam3_curved_p4_preregistration.py",
        "tests/test_ge_beam3_curved_p4_reference.py",
        "tests/test_ge_beam3_curved_p4_implementation_review.py",
        "tests/test_ge_beam3_curved_p4_formal_runner.py",
        "tests/test_ge_beam3_curved_p4_scientific_executor.py",
    ]
    if type(receipts) is not list or len(receipts) != 1:
        raise ExecutionError("executor review test receipt inventory differs")
    receipt = _exact(
        receipts[0],
        {"failed", "formal_execution", "passed", "receipt_id", "scientific_execution", "status", "test_paths"},
        "executor review test receipt",
    )
    if (
        receipt["failed"] != 0
        or receipt["formal_execution"] is not False
        or receipt["passed"] != EXPECTED_C4_TEST_COUNT
        or type(receipt["receipt_id"]) is not str
        or not receipt["receipt_id"]
        or receipt["scientific_execution"] is not False
        or receipt["status"] != "PASS"
        or receipt["test_paths"] != expected_tests
    ):
        raise ExecutionError("executor review test receipt differs")
    if review["reviewer_independence"] != {
        "executor_authorship": False,
        "formal_execution_performed": False,
        "review_artifact_authorship": True,
        "reviewer_role": "INDEPENDENT_GE_BEAM3_CURVED_P4_SCIENTIFIC_EXECUTOR_REVIEWER",
        "scientific_execution_performed": False,
        "test_authorship": False,
    }:
        raise ExecutionError("scientific executor review independence differs")


def _validate_authority_schema(value: Any) -> dict[str, Any]:
    authority = _exact(
        value,
        {
            "activation_authorized", "bounds", "candidate_id", "commits",
            "execution_authorized", "harness", "locations", "production_boundary",
            "publication_authorized", "request", "resource_manager", "schema", "study_id",
        },
        "scientific authority",
    )
    if authority["schema"] != AUTHORITY_SCHEMA or authority["study_id"] != STUDY_ID or authority["candidate_id"] != CANDIDATE_ID:
        raise ExecutionError("scientific authority identity differs")
    if authority["execution_authorized"] is not True or authority["activation_authorized"] is not False or authority["publication_authorized"] is not False:
        raise ExecutionError("scientific authority scope differs")
    if authority["bounds"] != BOUNDS:
        raise ExecutionError("scientific execution bounds differ")
    if authority["production_boundary"] != {
        "default_activation_authorized": False,
        "distribution_publication_authorized": False,
        "ecosystem_exposure_authorized": False,
        "existing_defaults_unchanged": True,
        "qualified_q4_unchanged": True,
        "qualified_s3_v2d_unchanged": True,
    }:
        raise ExecutionError("production boundary differs")
    commits = _exact(authority["commits"], {"c1", "c2", "c3", "c4"}, "commit chain")
    if commits["c1"] != C1 or commits["c2"] != C2:
        raise ExecutionError("frozen C1/C2 identity differs")
    c3 = _validate_commit_row(commits["c3"], "C3")
    c4 = _validate_commit_row(commits["c4"], "C4")
    if c3["parent"] != C2["commit"] or c3["subject"] != C3_SUBJECT:
        raise ExecutionError("C3 noncyclic overlay contract differs")
    if c4["parent"] != c3["commit"] or c4["subject"] != C4_SUBJECT:
        raise ExecutionError("C4 noncyclic overlay contract differs")
    harness = _exact(
        authority["harness"],
        {"authority_manifest_sha256", "checker", "executor", "producer", "runner"},
        "frozen harness",
    )
    if harness["authority_manifest_sha256"] != FROZEN_AUTHORITY_MANIFEST_SHA256:
        raise ExecutionError("frozen C1 authority-manifest hash differs")
    for key in ("checker", "executor", "producer", "runner"):
        item = _exact(harness[key], {"bytes", "path", "sha256"}, f"harness {key}")
        if type(item["path"]) is not str or not item["path"].startswith("docs/reference_cases/"):
            raise ExecutionError(f"harness {key} path is malformed")
        _validate_identity({"bytes": item["bytes"], "sha256": item["sha256"]}, f"harness {key}")
        if key != "executor" and item != FROZEN_C1_PROGRAMS[key]:
            raise ExecutionError(f"frozen C1 {key} identity differs")
    if harness["executor"]["path"] != C3_PATHS[0]:
        raise ExecutionError("scientific executor path differs")
    locations = _exact(
        authority["locations"],
        {"authority", "executor", "output", "repository", "review", "work_root"},
        "registered locations",
    )
    for key, value in locations.items():
        if type(value) is not str or not Path(value).is_absolute() or str(Path(value)) != value:
            raise ExecutionError(f"registered {key} location is not exact and absolute")
    repository = Path(locations["repository"])
    if locations["executor"] != str(repository / C3_PATHS[0]) or locations["authority"] != str(repository / AUTHORITY_RELATIVE) or locations["review"] != str(repository / REVIEW_RELATIVE):
        raise ExecutionError("registered repository paths differ")
    return authority


def validate_authority(
    repository: Path,
    authority_path: Path,
    review_path: Path,
    *,
    resource_manager: Path = RESOURCE_MANAGER,
    invocation_argv: Sequence[str] | None = None,
    allow_terminal: bool = False,
) -> ValidatedAuthority:
    """Perform the complete standard-library trust/authority check."""

    repository = repository.resolve(strict=True)
    authority_path = authority_path.resolve(strict=True)
    review_path = review_path.resolve(strict=True)
    if authority_path != repository / AUTHORITY_RELATIVE or review_path != repository / REVIEW_RELATIVE:
        raise ExecutionError("authority or review path is noncanonical")
    _require_unmodified_git_graph(repository)
    authority_raw, authority = strict_json(authority_path, "scientific authority")
    authority = _validate_authority_schema(authority)
    locations = authority["locations"]
    if repository != Path(locations["repository"]) or authority_path != Path(locations["authority"]) or review_path != Path(locations["review"]):
        raise ExecutionError("live paths differ from authority")
    c3_expected = authority["commits"]["c3"]
    c4_expected = authority["commits"]["c4"]
    c3 = _require_commit(repository, c3_expected["commit"], parent=C2["commit"],
                         subject=C3_SUBJECT, paths=C3_PATHS, tree=c3_expected["tree"])
    c4 = _require_commit(repository, c4_expected["commit"], parent=c3["commit"],
                         subject=C4_SUBJECT, paths=C4_PATHS, tree=c4_expected["tree"])
    c1 = _require_commit(repository, C1["commit"], parent=C1["parent"], subject=C1["subject"],
                         paths=(
                             "docs/reference_cases/ge_beam3_curved_p4_reference_checker.py",
                             "docs/reference_cases/ge_beam3_curved_p4_reference_producer.py",
                             "docs/reference_cases/ge_beam3_curved_p4_reference_runner.py",
                             "tests/test_ge_beam3_curved_p4_formal_runner.py",
                         ), tree=C1["tree"])
    c2 = _require_commit(repository, C2["commit"], parent=C2["parent"], subject=C2["subject"],
                         paths=("docs/reference_cases/ge_beam3_curved_p4_harness_review.json",),
                         tree=C2["tree"])
    if c1 != C1 or c2 != C2:
        raise ExecutionError("frozen harness ancestry differs")
    if _blob_identity(repository, C2["commit"], C2_REVIEW_RELATIVE) != C2_REVIEW:
        raise ExecutionError("accepted C2 harness review identity differs")
    _executor_review_raw, executor_review = strict_json(
        repository / C4_PATHS[0], "scientific executor review"
    )
    _validate_executor_review(executor_review, c3=c3, repository=repository)
    head = str(_git(repository, "rev-parse", "HEAD"))
    c5 = _require_commit(repository, head, parent=c4["commit"], subject=C5_SUBJECT, paths=C5_PATHS)
    executor_identity = _identity(repository / C3_PATHS[0], "scientific executor")
    expected_executor = authority["harness"]["executor"]
    if ({"bytes": expected_executor["bytes"], "sha256": expected_executor["sha256"]} != executor_identity or expected_executor["path"] != C3_PATHS[0]):
        raise ExecutionError("scientific executor identity differs")
    for key in ("runner", "producer", "checker"):
        row = authority["harness"][key]
        target = repository / row["path"]
        if _identity(target, f"frozen {key}") != {"bytes": row["bytes"], "sha256": row["sha256"]}:
            raise ExecutionError(f"frozen {key} identity differs")
    authority_identity = {"bytes": len(authority_raw), "sha256": _sha(authority_raw)}
    review_raw, review = strict_json(review_path, "scientific execution review")
    _validate_review(review, authority_identity, c4)
    request, request_raw, _rows = validate_request_and_ledger(
        authority, repository=repository, resource_manager=resource_manager,
        allow_terminal=allow_terminal,
    )
    if invocation_argv is not None and list(invocation_argv) != authority["request"]["argv"]:
        raise ExecutionError("live formal argv differs from authority")
    return ValidatedAuthority(
        repository=repository,
        authority=authority,
        authority_raw=authority_raw,
        review_raw=review_raw,
        request=request,
        request_raw=request_raw,
        c3=c3,
        c4=c4,
        c5=c5,
    )


def validate_chain(repository: Path) -> dict[str, dict[str, str]]:
    """Validate the immutable C1/C2 prefix and return its exact identities."""

    repository = repository.resolve(strict=True)
    _require_unmodified_git_graph(repository)
    c1 = _require_commit(
        repository, C1["commit"], parent=C1["parent"], subject=C1["subject"],
        paths=(
            "docs/reference_cases/ge_beam3_curved_p4_reference_checker.py",
            "docs/reference_cases/ge_beam3_curved_p4_reference_producer.py",
            "docs/reference_cases/ge_beam3_curved_p4_reference_runner.py",
            "tests/test_ge_beam3_curved_p4_formal_runner.py",
        ), tree=C1["tree"],
    )
    c2 = _require_commit(
        repository, C2["commit"], parent=C2["parent"], subject=C2["subject"],
        paths=("docs/reference_cases/ge_beam3_curved_p4_harness_review.json",),
        tree=C2["tree"],
    )
    return {"c1": c1, "c2": c2}


def validate_request(
    path: Path,
    *,
    expected_repository: Path,
    expected_argv: Sequence[str],
) -> tuple[bytes, dict[str, Any]]:
    """Validate one standard immutable request, including its exact command argv."""

    raw, value = strict_json(path, "resource request")
    value = _exact(
        value,
        {"command", "estimate_minutes", "repository", "request_id", "requested_at", "status", "task"},
        "resource request",
    )
    if value["repository"] != str(expected_repository) or value["status"] != "PENDING":
        raise ExecutionError("resource request repository or status differs")
    if HEX32.fullmatch(str(value["request_id"])) is None:
        raise ExecutionError("resource request ID is malformed")
    if type(value["command"]) is not str or not value["command"]:
        raise ExecutionError("resource request command is malformed")
    if type(value["estimate_minutes"]) is not int or value["estimate_minutes"] <= 0:
        raise ExecutionError("resource request estimate is malformed")
    _parse_timestamp(value["requested_at"], "request")
    if not expected_argv or any(type(token) is not str or not token for token in expected_argv):
        raise ExecutionError("expected request argv is malformed")
    if value["command"] != expected_request_command(expected_argv):
        raise ExecutionError("resource request command differs from the exact registered argv")
    return raw, value


def validate_ledger_lifecycle(
    path: Path,
    request_id: str,
    approved_prefix_sha256: str,
) -> dict[str, Any]:
    """Validate exactly one approval and start row, with no terminal/reuse row."""

    raw = _regular_bytes(path, "resource ledger")
    if not SHA256.fullmatch(str(approved_prefix_sha256)):
        raise ExecutionError("approved ledger prefix hash is malformed")
    rows = _ledger_rows(raw)
    matching = [row for row in rows if row[1] == request_id]
    statuses = [row[2] for row in matching]
    if statuses != ["APPROVED", "EXECUTION_STARTED"]:
        raise ExecutionError("resource ledger lifecycle differs")
    approval_end = raw.find(("| " + " | ".join(matching[0]) + " |\n").encode("utf-8"))
    if approval_end < 0:
        # Existing ledgers may use a different but still valid spacing convention.
        lines = raw.splitlines(keepends=True)
        prefix = b""
        for line in lines:
            prefix += line
            if request_id.encode("ascii") in line and b"APPROVED" in line:
                break
    else:
        marker = ("| " + " | ".join(matching[0]) + " |\n").encode("utf-8")
        prefix = raw[: approval_end + len(marker)]
    if _sha(prefix) != approved_prefix_sha256:
        raise ExecutionError("approved ledger prefix differs")
    return {"approved_prefix": prefix, "raw": raw, "rows": matching}


def validate_active_lock_owner(
    manager: Path,
    request_id: str,
    attempt_id: str,
) -> bytes:
    """Testable strict validation of the official active-lock owner."""

    if HEX32.fullmatch(request_id) is None or HEX32.fullmatch(attempt_id) is None or request_id == attempt_id:
        raise ExecutionError("request or attempt ID is malformed")
    active = manager / "active-lock"
    owner_path = active / "owner.json"
    if not active.is_dir() or active.is_symlink() or _is_reparse(active) or {p.name for p in active.iterdir()} != {"owner.json"}:
        raise ExecutionError("official active lock is malformed")
    raw = _regular_bytes(owner_path, "active-lock owner")
    try:
        owner = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=lambda pairs: _unique_object(pairs, "active-lock owner"), parse_constant=lambda value: _reject_json_constant(value, "active-lock owner"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExecutionError("active-lock owner is malformed") from exc
    owner = _exact(owner, {"acquired_at", "command", "process_id", "repository", "request_id", "task"}, "active-lock owner")
    if owner["request_id"] != request_id or type(owner["process_id"]) is not int or owner["process_id"] <= 0:
        raise ExecutionError("active-lock owner request differs")
    _parse_timestamp(owner["acquired_at"], "active-lock acquisition")
    return raw


def _write_exclusive_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def acquire_claim(
    validated: ValidatedAuthority,
    *,
    resource_manager: Path = RESOURCE_MANAGER,
) -> Claim:
    """Durably consume the one request/attempt pair after official lock acquisition."""

    request_id = validated.authority["request"]["request_id"]
    attempt_id = validated.authority["request"]["attempt_id"]
    active_lock, owner_raw = validate_active_lock(
        validated.authority, validated.request, resource_manager=resource_manager
    )
    # Also exercise the standalone owner validator so tests and formal execution
    # share the same exact official-lock shape.
    if validate_active_lock_owner(resource_manager, request_id, attempt_id) != owner_raw:
        raise ExecutionError("active-lock validation disagrees")
    claims = resource_manager / "claims"
    attempts = resource_manager / "attempts"
    receipts = resource_manager / "receipts"
    for directory in (claims, attempts, receipts):
        if not directory.is_dir() or directory.is_symlink() or _is_reparse(directory):
            raise ExecutionError("resource-manager transaction directory is malformed")
    request_claim = claims / f"{request_id}.json"
    attempt_claim = attempts / f"{attempt_id}.json"
    receipt = receipts / f"{request_id}.json"
    if any(path.exists() or path.is_symlink() for path in (request_claim, attempt_claim, receipt)):
        raise ExecutionError("resource request or attempt is already claimed/consumed")
    started = validated.authority["resource_manager"]["execution_started_row"]
    claim_value = {
        "active_lock_owner_sha256": _sha(owner_raw),
        "approved_ledger_prefix_sha256": validated.authority["resource_manager"]["approved_ledger_prefix"]["sha256"],
        "attempt_id": attempt_id,
        "authority_commit": validated.c5["commit"],
        "authority_sha256": _sha(validated.authority_raw),
        "authority_tree": validated.c5["tree"],
        "execution_started_row_sha256": _sha(canonical_bytes(started)),
        "request_id": request_id,
        "request_record_sha256": _sha(validated.request_raw),
        "schema": CLAIM_SCHEMA,
    }
    claim_raw = canonical_bytes(claim_value)
    # Both names are exclusive immutable consumption markers.  If the second
    # write collides, the first remains as an unambiguously consumed request.
    _write_exclusive_bytes(request_claim, claim_raw)
    _write_exclusive_bytes(attempt_claim, claim_raw)
    return Claim(
        request_id=request_id,
        attempt_id=attempt_id,
        active_lock=active_lock,
        owner_raw=owner_raw,
        request_claim=request_claim,
        attempt_claim=attempt_claim,
        receipt=receipt,
        claim_raw=claim_raw,
        request_claim_mtime_ns=request_claim.stat().st_mtime_ns,
        attempt_claim_mtime_ns=attempt_claim.stat().st_mtime_ns,
    )


def _validate_claim_record(
    validated: ValidatedAuthority,
    claim_raw: bytes,
    owner_raw: bytes,
) -> dict[str, Any]:
    """Validate an immutable request/attempt claim, including lock ownership."""

    claim = _strict_json_bytes(claim_raw, "execution claim")
    expected = {
        "active_lock_owner_sha256": _sha(owner_raw),
        "approved_ledger_prefix_sha256": validated.authority["resource_manager"]["approved_ledger_prefix"]["sha256"],
        "attempt_id": validated.authority["request"]["attempt_id"],
        "authority_commit": validated.c5["commit"],
        "authority_sha256": _sha(validated.authority_raw),
        "authority_tree": validated.c5["tree"],
        "execution_started_row_sha256": _sha(
            canonical_bytes(validated.authority["resource_manager"]["execution_started_row"])
        ),
        "request_id": validated.authority["request"]["request_id"],
        "request_record_sha256": _sha(validated.request_raw),
        "schema": CLAIM_SCHEMA,
    }
    if claim != expected:
        raise ExecutionError("immutable execution claim binding differs")
    return claim


def _verify_claim(claim: Claim, validated: ValidatedAuthority, resource_manager: Path) -> None:
    if _regular_bytes(claim.request_claim, "request claim") != claim.claim_raw or _regular_bytes(claim.attempt_claim, "attempt claim") != claim.claim_raw:
        raise ExecutionError("request and attempt claims differ")
    if claim.request_claim.stat().st_mtime_ns != claim.request_claim_mtime_ns or claim.attempt_claim.stat().st_mtime_ns != claim.attempt_claim_mtime_ns:
        raise ExecutionError("immutable claim file was rewritten")
    active, owner = validate_active_lock(validated.authority, validated.request, resource_manager=resource_manager)
    if active != claim.active_lock or owner != claim.owner_raw:
        raise ExecutionError("official active-lock ownership changed")
    _validate_claim_record(validated, claim.claim_raw, owner)


def release_claim(
    claim: Claim,
    validated: ValidatedAuthority,
    *,
    resource_manager: Path = RESOURCE_MANAGER,
) -> None:
    """Verify durable claim ownership; never delete claims or the official lock."""

    _verify_claim(claim, validated, resource_manager)


def _load_frozen_runner(validated: ValidatedAuthority) -> Any:
    """Load C1 only after all standard-library authority checks have passed."""

    row = validated.authority["harness"]["runner"]
    path = validated.repository / row["path"]
    if _identity(path, "frozen C1 runner") != {"bytes": row["bytes"], "sha256": row["sha256"]}:
        raise ExecutionError("frozen C1 runner changed before import")
    name = "_ge_beam3_curved_p4_frozen_c1_runner"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ExecutionError("frozen C1 runner cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    for function in ("_verify_authority_inputs", "_cycle"):
        if not callable(getattr(module, function, None)):
            raise ExecutionError(f"frozen C1 runner lacks {function}")
    if getattr(module, "BLOCKED", None) != BLOCKED_PROCESS or getattr(module, "PASS", None) != PASS:
        raise ExecutionError("frozen C1 runner terminal vocabulary differs")
    return module


_load_runner = _load_frozen_runner


def _validate_cycle_record(
    cycle: Mapping[str, Any],
    raw: bytes,
    cycle_dir: Path,
) -> None:
    expected_keys = {
        "candidate_id", "check_sha256", "counts", "diagnostic_checker_terminal",
        "process", "process_log_sha256", "production_restriction", "proof_sha256",
        "schema", "status", "terminal",
    }
    if type(cycle) is not dict or set(cycle) != expected_keys or raw != canonical_bytes(cycle):
        raise ExecutionError("cycle record is malformed or noncanonical")
    if cycle["candidate_id"] != CANDIDATE_ID or cycle["schema"] != "anysolver.ge-beam3-curved-p4-reference-cycle-v2" or cycle["production_restriction"] != RESTRICTION or cycle["terminal"] != BLOCKED_PROCESS:
        raise ExecutionError("cycle identity or nonclassifying boundary differs")
    process = cycle["process"]
    counts = cycle["counts"]
    if type(process) is not dict or set(process) != {"checkers", "fresh_checker_processes", "producer"}:
        raise ExecutionError("cycle process record differs")
    if type(process["checkers"]) is not list or len(process["checkers"]) != 2:
        raise ExecutionError("cycle checker process inventory differs")
    process_states = [str(process["producer"]), *[str(state) for state in process["checkers"]]]
    if any("TERMINATION_FAILED" in state for state in process_states):
        raise ExecutionError("process-tree absence remains uncertain")
    if type(counts) is not dict or set(counts) != {"accepted_cases", "covered_obligations", "registered_obligations", "stations"}:
        raise ExecutionError("cycle counts differ")
    if counts["registered_obligations"] != 26 or any(type(counts[key]) is not int or counts[key] < 0 for key in counts):
        raise ExecutionError("cycle counts are malformed")
    diagnostic = cycle["diagnostic_checker_terminal"]
    allowed_diagnostics = {PASS, NO_GO_REGULARITY, NO_GO_FRAME, NO_GO_COVARIANCE}
    if cycle["status"] == "COMPLETE":
        if diagnostic not in allowed_diagnostics or process != {
            "checkers": ["PASS", "PASS"], "fresh_checker_processes": True, "producer": "PASS"
        }:
            raise ExecutionError("complete cycle lacks terminal child/checker evidence")
        if type(cycle["check_sha256"]) is not list or len(cycle["check_sha256"]) != 2 or cycle["check_sha256"][0] != cycle["check_sha256"][1]:
            raise ExecutionError("checker replicas are not byte-identical")
        if diagnostic == PASS and counts != {
            "accepted_cases": 6, "covered_obligations": 26,
            "registered_obligations": 26, "stations": 144,
        }:
            # The frozen C1 currently emits 6*3*8 = 144 stations.  Any future
            # expansion requires a successor authority rather than weakening C3.
            raise ExecutionError("PASS cycle lacks complete registered coverage")
    else:
        if diagnostic != "UNAVAILABLE":
            raise ExecutionError("failed cycle improperly carries a scientific terminal")
    for filename, digest in (("proof.json", cycle["proof_sha256"]), ("check-1.json", cycle["check_sha256"][0]), ("check-2.json", cycle["check_sha256"][1])):
        path = cycle_dir / filename
        if digest == "ABSENT":
            if path.exists():
                raise ExecutionError("cycle claims absent evidence that exists")
        elif not SHA256.fullmatch(str(digest)) or _sha(_regular_bytes(path, filename)) != digest:
            raise ExecutionError("cycle evidence hash differs")
    logs = cycle["process_log_sha256"]
    if type(logs) is not dict or set(logs) != {"checker_stderr", "checker_stdout", "producer_stderr", "producer_stdout"}:
        raise ExecutionError("cycle process-log record differs")
    log_bindings = [
        ("producer.stderr.log", logs["producer_stderr"]),
        ("producer.stdout.log", logs["producer_stdout"]),
    ]
    if type(logs["checker_stderr"]) is not list or type(logs["checker_stdout"]) is not list or len(logs["checker_stderr"]) != 2 or len(logs["checker_stdout"]) != 2:
        raise ExecutionError("cycle checker log inventory differs")
    for index in (0, 1):
        log_bindings.extend(((f"checker-{index + 1}.stderr.log", logs["checker_stderr"][index]), (f"checker-{index + 1}.stdout.log", logs["checker_stdout"][index])))
    for filename, digest in log_bindings:
        if digest == "ABSENT":
            if (cycle_dir / filename).exists():
                raise ExecutionError("cycle log absence claim differs")
        elif not SHA256.fullmatch(str(digest)) or _sha(_regular_bytes(cycle_dir / filename, filename)) != digest:
            raise ExecutionError("cycle log hash differs")


def adjudicate_diagnostic_cycles(
    cycles: Sequence[Mapping[str, Any]],
    cycle_raws: Sequence[bytes],
) -> str:
    """Map independently validated C1 diagnostics through frozen P4 precedence."""

    if len(cycles) != 2 or len(cycle_raws) != 2:
        return BLOCKED_PROCESS
    if cycle_raws[0] != cycle_raws[1]:
        return BLOCKED_PROCESS
    expected_keys = {
        "candidate_id", "check_sha256", "counts", "diagnostic_checker_terminal",
        "process", "process_log_sha256", "production_restriction", "proof_sha256",
        "schema", "status", "terminal",
    }
    for cycle, raw in zip(cycles, cycle_raws, strict=True):
        if type(cycle) is not dict or set(cycle) != expected_keys or raw != canonical_bytes(cycle):
            return BLOCKED_PROCESS
        if (
            cycle.get("candidate_id") != CANDIDATE_ID
            or cycle.get("schema") != "anysolver.ge-beam3-curved-p4-reference-cycle-v2"
            or cycle.get("status") != "COMPLETE"
            or cycle.get("terminal") != BLOCKED_PROCESS
            or cycle.get("production_restriction") != RESTRICTION
            or cycle.get("process") != {
                "checkers": ["PASS", "PASS"],
                "fresh_checker_processes": True,
                "producer": "PASS",
            }
        ):
            return BLOCKED_PROCESS
        counts = cycle.get("counts")
        diagnostic = cycle.get("diagnostic_checker_terminal")
        if type(counts) is not dict or set(counts) != {"accepted_cases", "covered_obligations", "registered_obligations", "stations"} or counts.get("registered_obligations") != 26:
            return BLOCKED_PROCESS
        if diagnostic == PASS and counts != {
            "accepted_cases": 6,
            "covered_obligations": 26,
            "registered_obligations": 26,
            "stations": 144,
        }:
            return BLOCKED_PROCESS
        if diagnostic in {NO_GO_REGULARITY, NO_GO_FRAME, NO_GO_COVARIANCE} and not (
            type(counts.get("covered_obligations")) is int
            and 1 <= counts["covered_obligations"] <= 26
            and type(counts.get("accepted_cases")) is int
            and type(counts.get("stations")) is int
        ):
            return BLOCKED_PROCESS
    diagnostics = [cycle.get("diagnostic_checker_terminal") for cycle in cycles]
    if diagnostics[0] != diagnostics[1]:
        return BLOCKED_PROCESS
    terminal = diagnostics[0]
    if terminal in {NO_GO_REGULARITY, NO_GO_FRAME, NO_GO_COVARIANCE, PASS}:
        return str(terminal)
    return BLOCKED_PROCESS


def _external_location(path: Path, repository: Path, resource_manager: Path, label: str) -> Path:
    path = path.absolute()
    for root in (repository.resolve(strict=True), resource_manager.resolve(strict=True)):
        try:
            path.resolve(strict=False).relative_to(root)
        except ValueError:
            continue
        raise ExecutionError(f"{label} must be outside repository and resource manager")
    return path


def require_official_resource_manager(resource_manager: Path) -> Path:
    resolved = resource_manager.resolve(strict=True)
    if resolved != RESOURCE_MANAGER or str(resolved) != str(RESOURCE_MANAGER):
        raise ExecutionError("formal execution requires the official resource-manager root")
    return resolved


def live_formal_argv() -> list[str]:
    """Reconstruct flags stripped by Python before exposing ``sys.argv``."""

    return [
        str(Path(sys.executable).resolve(strict=True)),
        "-I",
        "-B",
        str(Path(__file__).resolve(strict=True)),
        *sys.argv[1:],
    ]


def _live_protected_blob_record(repository: Path) -> dict[str, Any]:
    """Recompute the frozen straight-core boundary without C1 helper code."""

    rows: list[dict[str, str]] = []
    for relative, expected in sorted(FROZEN_PROTECTED_STRAIGHT_BLOBS.items()):
        target = repository / relative
        raw = _regular_bytes(target, f"protected straight-core blob {relative}")
        normalized = raw.replace(b"\r\n", b"\n")
        if b"\r" in normalized:
            raise ExecutionError(f"protected straight-core blob has a bare carriage return: {relative}")
        header = f"blob {len(normalized)}\0".encode("ascii")
        working = hashlib.sha1(header + normalized).hexdigest()
        head = str(_git(repository, "rev-parse", f"HEAD:{relative}"))
        status = "PASS" if head == expected and working == expected else "FAIL"
        rows.append(
            {
                "expected_git_blob": expected,
                "head_git_blob": head,
                "path": relative,
                "status": status,
                "working_git_blob": working,
            }
        )
    if any(row["status"] != "PASS" for row in rows):
        raise ExecutionError("post-cycle protected straight-core blobs differ")
    return {
        "count": len(rows),
        "sha256": _sha(canonical_bytes(rows)),
        "status": "PASS",
    }


def run_scientific_cycles(
    validated: ValidatedAuthority,
    work_root: Path,
) -> tuple[list[dict[str, Any]], list[bytes], dict[str, Any]]:
    """Run the frozen C1 low-level cycle exactly twice; never call C1 ``run_gate``."""

    work_root = work_root.absolute()
    if work_root.exists():
        raise ExecutionError("formal work root already exists")
    runner = _load_runner(validated)
    harness = validated.authority["harness"]
    manifest, manifest_sha = runner._verify_authority_inputs(
        validated.repository,
        expected_authority_manifest_sha256=harness["authority_manifest_sha256"],
        require_clean_inputs=True,
    )
    if manifest_sha != harness["authority_manifest_sha256"]:
        raise ExecutionError("frozen C1 authority-manifest check disagrees")
    work_root.mkdir(parents=True, exist_ok=False)
    manifest_path = work_root / "authority-manifest.json"
    _write_exclusive_bytes(manifest_path, runner._canonical_bytes(manifest))
    deadline = time.monotonic() + BOUNDS["wave_timeout_seconds"]
    here = validated.repository / "docs/reference_cases"
    cycles: list[dict[str, Any]] = []
    raws: list[bytes] = []
    for index in (1, 2):
        cycle_dir = work_root / f"cycle-{index}"
        cycle = runner._cycle(
            cycle_dir,
            reference_module=validated.repository / "src/anysolver/ge_beam3_curved_reference.py",
            cases_definition=here / "ge_beam3_curved_p4_cases.json",
            contract=here / "ge_beam3_curved_p4_contract.json",
            authority_manifest=manifest_path,
            authority_sha256=manifest_sha,
            manifest_value=manifest,
            producer=validated.repository / harness["producer"]["path"],
            checker=validated.repository / harness["checker"]["path"],
            independent_checker_authority=True,
            child_timeout_seconds=BOUNDS["child_timeout_seconds"],
            inactivity_seconds=BOUNDS["inactivity_seconds"],
            memory_limit_bytes=BOUNDS["memory_limit_bytes"],
            wave_deadline=deadline,
        )
        if cycle.get("status") == "COMPLETE":
            cycle_raw, on_disk = strict_json(cycle_dir / "cycle.json", f"cycle {index}")
            if on_disk != cycle:
                raise ExecutionError("frozen C1 returned a different cycle than it wrote")
        else:
            cycle_raw = canonical_bytes(cycle)
        _validate_cycle_record(cycle, cycle_raw, cycle_dir)
        cycles.append(cycle)
        raws.append(cycle_raw)
        if cycle.get("status") != "COMPLETE":
            break
    protected_record = _live_protected_blob_record(validated.repository)
    return cycles, raws, protected_record


def build_result(
    validated: ValidatedAuthority,
    cycles: Sequence[Mapping[str, Any]],
    cycle_raws: Sequence[bytes],
    protected: Mapping[str, Any],
) -> dict[str, Any]:
    terminal = adjudicate_diagnostic_cycles(cycles, cycle_raws)
    complete = len(cycles) == 2 and all(cycle.get("status") == "COMPLETE" for cycle in cycles)
    if terminal == PASS and not complete:
        terminal = BLOCKED_PROCESS
    return {
        "attempt_id": validated.authority["request"]["attempt_id"],
        "authority": {
            "commit": validated.c5["commit"],
            "sha256": _sha(validated.authority_raw),
            "tree": validated.c5["tree"],
        },
        "candidate_id": CANDIDATE_ID,
        "checks": {
            "all_launched_processes_terminal": True,
            "byte_identical_canonical_cycles": len(cycle_raws) == 2 and cycle_raws[0] == cycle_raws[1],
            "formal_execution_authorized": True,
            "independent_checker_replicas": all(cycle.get("process", {}).get("fresh_checker_processes") is True for cycle in cycles),
            "post_cycle_protected_blobs": protected.get("status") == "PASS",
            "production_activation_authorized": False,
        },
        "counts": {
            "cycles_complete": sum(cycle.get("status") == "COMPLETE" for cycle in cycles),
            "cycles_launched": len(cycles),
            "registered_obligations": 26,
        },
        "cycle_diagnostic_terminals": [str(cycle.get("diagnostic_checker_terminal", "UNAVAILABLE")) for cycle in cycles],
        "cycle_sha256": [_sha(raw) for raw in cycle_raws],
        "post_cycle_protected_blobs": dict(protected),
        "production_restriction": RESTRICTION,
        "request_id": validated.authority["request"]["request_id"],
        "schema": RESULT_SCHEMA,
        "terminal": terminal,
    }


def _validate_result_record(
    validated: ValidatedAuthority,
    result: Any,
) -> dict[str, Any]:
    """Validate a staged canonical result without trusting the producing process."""

    made = _exact(
        result,
        {
            "attempt_id", "authority", "candidate_id", "checks", "counts",
            "cycle_diagnostic_terminals", "cycle_sha256", "post_cycle_protected_blobs",
            "production_restriction", "request_id", "schema", "terminal",
        },
        "scientific result",
    )
    if (
        made["schema"] != RESULT_SCHEMA
        or made["candidate_id"] != CANDIDATE_ID
        or made["attempt_id"] != validated.authority["request"]["attempt_id"]
        or made["request_id"] != validated.authority["request"]["request_id"]
        or made["production_restriction"] != RESTRICTION
        or made["terminal"] not in {
            BLOCKED_PROCESS, NO_GO_REGULARITY, NO_GO_FRAME, NO_GO_COVARIANCE, PASS,
        }
    ):
        raise ExecutionError("scientific result identity or terminal differs")
    if made["authority"] != {
        "commit": validated.c5["commit"],
        "sha256": _sha(validated.authority_raw),
        "tree": validated.c5["tree"],
    }:
        raise ExecutionError("scientific result authority binding differs")
    checks = _exact(
        made["checks"],
        {
            "all_launched_processes_terminal", "byte_identical_canonical_cycles",
            "formal_execution_authorized", "independent_checker_replicas",
            "post_cycle_protected_blobs", "production_activation_authorized",
        },
        "scientific result checks",
    )
    if (
        not all(type(value) is bool for value in checks.values())
        or checks["all_launched_processes_terminal"] is not True
        or checks["formal_execution_authorized"] is not True
        or checks["production_activation_authorized"] is not False
    ):
        raise ExecutionError("scientific result process or authority checks differ")
    counts = _exact(
        made["counts"],
        {"cycles_complete", "cycles_launched", "registered_obligations"},
        "scientific result counts",
    )
    if (
        any(type(counts[key]) is not int for key in counts)
        or not 0 <= counts["cycles_complete"] <= counts["cycles_launched"] <= 2
        or counts["registered_obligations"] != 26
    ):
        raise ExecutionError("scientific result counts differ")
    diagnostics = made["cycle_diagnostic_terminals"]
    digests = made["cycle_sha256"]
    if (
        type(diagnostics) is not list
        or type(digests) is not list
        or len(diagnostics) != counts["cycles_launched"]
        or len(digests) != counts["cycles_launched"]
        or any(value not in {"UNAVAILABLE", NO_GO_REGULARITY, NO_GO_FRAME, NO_GO_COVARIANCE, PASS} for value in diagnostics)
        or any(type(value) is not str or SHA256.fullmatch(value) is None for value in digests)
    ):
        raise ExecutionError("scientific result cycle inventory differs")
    if checks["byte_identical_canonical_cycles"] is not (
        len(digests) == 2 and digests[0] == digests[1]
    ):
        raise ExecutionError("scientific result deterministic-cycle claim differs")
    protected = _exact(
        made["post_cycle_protected_blobs"],
        {"count", "sha256", "status"},
        "post-cycle protected blobs",
    )
    if (
        type(protected["count"]) is not int
        or protected["count"] <= 0
        or SHA256.fullmatch(str(protected["sha256"])) is None
        or protected["status"] != "PASS"
        or checks["post_cycle_protected_blobs"] is not True
    ):
        raise ExecutionError("post-cycle protected-blob result differs")
    if made["terminal"] != BLOCKED_PROCESS:
        if (
            counts["cycles_complete"] != 2
            or counts["cycles_launched"] != 2
            or checks["byte_identical_canonical_cycles"] is not True
            or checks["independent_checker_replicas"] is not True
            or diagnostics != [made["terminal"], made["terminal"]]
        ):
            raise ExecutionError("scientific terminal lacks two identical complete cycles")
    return made


def _terminal_ledger_fields(
    validated: ValidatedAuthority,
    *,
    pending_manifest_sha256: str,
    terminal: str,
) -> list[str]:
    request = validated.request
    status = "COMPLETED_PASS" if terminal == PASS else "COMPLETED_FAIL"
    return [
        validated.authority["request"]["request_id"],
        status,
        request["task"],
        request["repository"],
        "Exact immutable request executed once",
        f"{request['estimate_minutes']} minutes",
        (
            f"GE-Beam3 P4 terminal {terminal}; pending manifest SHA-256 "
            f"{pending_manifest_sha256}; attempt {validated.authority['request']['attempt_id']}."
        ),
    ]


def _append_terminal_ledger(path: Path, fields: Sequence[str]) -> list[str]:
    if len(fields) != 7 or any(type(field) is not str or not field or "|" in field or "\n" in field or "\r" in field for field in fields):
        raise ExecutionError("terminal ledger fields are malformed")
    timestamp = _utc_now()
    row = [timestamp, *fields]
    encoded = ("| " + " | ".join(row) + " |\n").encode("utf-8")
    with path.open("ab") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    matches = [made for made in _ledger_rows(_regular_bytes(path, "resource ledger")) if made == row]
    if len(matches) != 1:
        raise ExecutionError("terminal ledger append did not verify exactly")
    return row


def _receipt_value(
    validated: ValidatedAuthority,
    claim: Claim,
    result: Mapping[str, Any],
    pending_manifest: Mapping[str, Any],
    terminal_fields: Sequence[str],
) -> dict[str, Any]:
    return {
        "active_lock_owner_sha256": _sha(claim.owner_raw),
        "attempt_id": claim.attempt_id,
        "authority_commit": validated.c5["commit"],
        "authority_sha256": _sha(validated.authority_raw),
        "claim_sha256": _sha(claim.claim_raw),
        "pending_manifest": {
            "bytes": len(canonical_bytes(pending_manifest)),
            "sha256": _sha(canonical_bytes(pending_manifest)),
        },
        "request_id": claim.request_id,
        "request_record_sha256": _sha(validated.request_raw),
        "result": {"bytes": len(canonical_bytes(result)), "sha256": _sha(canonical_bytes(result))},
        "schema": RECEIPT_SCHEMA,
        "terminal": result["terminal"],
        "terminal_ledger_fields": list(terminal_fields),
    }


def _pending_paths(output: Path, attempt_id: str) -> tuple[Path, Path, Path]:
    pending = output.with_name(f".{output.name}.{attempt_id}.pending")
    manifest = output.with_name(f".{output.name}.{attempt_id}.pending-manifest.json")
    final_manifest = output.with_name(f"{output.name}.manifest.json")
    return pending, manifest, final_manifest


def _pending_manifest_value(
    validated: ValidatedAuthority,
    result: Mapping[str, Any],
    result_raw: bytes,
) -> dict[str, Any]:
    return {
        "attempt_id": validated.authority["request"]["attempt_id"],
        "authority_sha256": _sha(validated.authority_raw),
        "request_id": validated.authority["request"]["request_id"],
        "result": {"bytes": len(result_raw), "sha256": _sha(result_raw)},
        "schema": PENDING_SCHEMA,
        "terminal": result["terminal"],
    }


def _validate_pending_manifest(
    validated: ValidatedAuthority,
    manifest: Any,
    result: Mapping[str, Any],
    result_raw: bytes,
) -> dict[str, Any]:
    made = _exact(
        manifest,
        {"attempt_id", "authority_sha256", "request_id", "result", "schema", "terminal"},
        "pending manifest",
    )
    if made != _pending_manifest_value(validated, result, result_raw):
        raise ExecutionError("pending-manifest binding differs")
    return made


def _validate_receipt(
    validated: ValidatedAuthority,
    claim_raw: bytes,
    owner_raw: bytes,
    receipt: Mapping[str, Any],
) -> None:
    expected_keys = {
        "active_lock_owner_sha256", "attempt_id", "authority_commit", "authority_sha256", "claim_sha256",
        "pending_manifest", "request_id", "request_record_sha256", "result", "schema",
        "terminal", "terminal_ledger_fields",
    }
    if type(receipt) is not dict or set(receipt) != expected_keys or receipt["schema"] != RECEIPT_SCHEMA:
        raise ExecutionError("execution receipt schema differs")
    if (
        receipt["active_lock_owner_sha256"] != _sha(owner_raw)
        or receipt["attempt_id"] != validated.authority["request"]["attempt_id"]
        or receipt["request_id"] != validated.authority["request"]["request_id"]
        or receipt["authority_commit"] != validated.c5["commit"]
        or receipt["authority_sha256"] != _sha(validated.authority_raw)
        or receipt["request_record_sha256"] != _sha(validated.request_raw)
        or receipt["claim_sha256"] != _sha(claim_raw)
        or receipt["terminal"] not in TERMINALS[1:]
    ):
        raise ExecutionError("execution receipt binding differs")
    _validate_claim_record(validated, claim_raw, owner_raw)
    _validate_identity(receipt["pending_manifest"], "pending manifest receipt")
    _validate_identity(receipt["result"], "result receipt")
    fields = receipt["terminal_ledger_fields"]
    expected_fields = _terminal_ledger_fields(
        validated,
        pending_manifest_sha256=receipt["pending_manifest"]["sha256"],
        terminal=receipt["terminal"],
    )
    if type(fields) is not list or fields != expected_fields:
        raise ExecutionError("receipt terminal ledger fields differ")


def publish_or_recover(
    validated: ValidatedAuthority,
    claim: Claim | None,
    result: Mapping[str, Any] | None,
    output: Path,
    *,
    resource_manager: Path = RESOURCE_MANAGER,
) -> dict[str, Any] | None:
    """Publish after receipt+terminal row, or recover publication without rerunning."""

    output = output.absolute()
    request_id = validated.authority["request"]["request_id"]
    attempt_id = validated.authority["request"]["attempt_id"]
    claim_path = resource_manager / "claims" / f"{request_id}.json"
    attempt_path = resource_manager / "attempts" / f"{attempt_id}.json"
    receipt_path = resource_manager / "receipts" / f"{request_id}.json"
    pending, manifest_path, final_manifest = _pending_paths(output, attempt_id)
    if receipt_path.exists():
        _active, owner_raw = validate_active_lock(
            validated.authority, validated.request, resource_manager=resource_manager
        )
        receipt_raw, receipt = strict_json(receipt_path, "execution receipt")
        del receipt_raw
        claim_raw = _regular_bytes(claim_path, "request claim")
        if claim_raw != _regular_bytes(attempt_path, "attempt claim"):
            raise ExecutionError("recovery claims differ")
        _validate_receipt(validated, claim_raw, owner_raw, receipt)
        if output.exists() and pending.exists():
            raise ExecutionError("canonical and pending results both exist")
        if final_manifest.exists() and manifest_path.exists():
            raise ExecutionError("canonical and pending manifests both exist")
        manifest_source = final_manifest if final_manifest.exists() else manifest_path
        manifest_raw, manifest = strict_json(manifest_source, "pending manifest")
        if {"bytes": len(manifest_raw), "sha256": _sha(manifest_raw)} != receipt["pending_manifest"]:
            raise ExecutionError("recovery pending manifest differs")
        result_source = output if output.exists() else pending
        result_raw, recovered = strict_json(result_source, "canonical or pending result")
        recovered = _validate_result_record(validated, recovered)
        _validate_pending_manifest(validated, manifest, recovered, result_raw)
        if manifest["terminal"] != receipt["terminal"] or manifest["result"] != receipt["result"]:
            raise ExecutionError("recovery pending-manifest receipt binding differs")
        fields = receipt["terminal_ledger_fields"]
        rows = _ledger_rows(_regular_bytes(resource_manager / "ledger.md", "resource ledger"))
        all_request_terminals = [
            row for row in rows
            if row[1] == request_id and row[2] in {"COMPLETED_PASS", "COMPLETED_FAIL"}
        ]
        terminal_rows = [row for row in all_request_terminals if row[1:] == fields]
        if len(terminal_rows) == 0:
            if all_request_terminals:
                raise ExecutionError("mismatched terminal ledger row blocks recovery")
            _append_terminal_ledger(resource_manager / "ledger.md", fields)
        elif len(terminal_rows) != 1:
            raise ExecutionError("terminal ledger row is duplicated")
        if output.exists():
            if {"bytes": len(result_raw), "sha256": _sha(result_raw)} != receipt["result"]:
                raise ExecutionError("canonical result differs from receipt")
        else:
            if {"bytes": len(result_raw), "sha256": _sha(result_raw)} != receipt["result"]:
                raise ExecutionError("pending result differs from receipt")
            os.replace(pending, output)
        if not final_manifest.exists():
            os.replace(manifest_path, final_manifest)
        return recovered
    if claim is None or result is None:
        if any(
            path.exists() or path.is_symlink()
            for path in (
                claim_path, attempt_path, output, pending, manifest_path, final_manifest,
            )
        ):
            raise ExecutionError(
                "pre-receipt transaction is consumed and unrecoverable; preserve all artifacts"
            )
        return None
    if (
        claim.request_claim != claim_path
        or claim.attempt_claim != attempt_path
        or claim.receipt != receipt_path
        or output.exists()
        or pending.exists()
        or manifest_path.exists()
    ):
        raise ExecutionError("new publication paths differ or already exist")
    _verify_claim(claim, validated, resource_manager)
    result = _validate_result_record(validated, result)
    output.parent.mkdir(parents=True, exist_ok=True)
    result_raw = canonical_bytes(dict(result))
    _write_exclusive_bytes(pending, result_raw)
    manifest = _pending_manifest_value(validated, result, result_raw)
    manifest_raw = canonical_bytes(manifest)
    _write_exclusive_bytes(manifest_path, manifest_raw)
    reread_result_raw, reread_result = strict_json(pending, "staged result")
    reread_manifest_raw, reread_manifest = strict_json(manifest_path, "staged pending manifest")
    if (
        reread_result != dict(result)
        or reread_result_raw != result_raw
        or reread_manifest != manifest
        or reread_manifest_raw != manifest_raw
    ):
        raise ExecutionError("staged result or pending manifest changed before receipt")
    _validate_result_record(validated, reread_result)
    _validate_pending_manifest(validated, reread_manifest, reread_result, reread_result_raw)
    _verify_claim(claim, validated, resource_manager)
    terminal_fields = _terminal_ledger_fields(
        validated, pending_manifest_sha256=_sha(manifest_raw), terminal=str(result["terminal"])
    )
    receipt = _receipt_value(validated, claim, result, manifest, terminal_fields)
    _write_exclusive_bytes(claim.receipt, canonical_bytes(receipt))
    # The ledger's terminal row binds the pending manifest and is durable before
    # either canonical artifact is atomically promoted.
    _append_terminal_ledger(resource_manager / "ledger.md", terminal_fields)
    os.replace(pending, output)
    os.replace(manifest_path, final_manifest)
    return dict(result)


# Backward-neutral alias used by the independent synthetic harness.
adjudicate_cycles = adjudicate_diagnostic_cycles


def execute(
    repository: Path,
    authority_path: Path,
    review_path: Path,
    resource_manager: Path,
    work_root: Path,
    output: Path,
    *,
    invocation_argv: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Validate twice, consume once, run two cycles, and publish transactionally."""

    repository = repository.resolve(strict=True)
    resource_manager = require_official_resource_manager(resource_manager)
    work_root = _external_location(work_root, repository, resource_manager, "formal work root")
    output = _external_location(output, repository, resource_manager, "canonical output")
    # A receipt is the sole permission to enter publication recovery with a
    # terminal ledger row.  Merely having a claim cannot weaken pre-run checks.
    _pre_raw, pre = strict_json(authority_path.resolve(strict=True), "scientific authority")
    pre = _validate_authority_schema(pre)
    request_id = pre["request"]["request_id"]
    receipt_exists = (resource_manager / "receipts" / f"{request_id}.json").exists()
    first = validate_authority(
        repository,
        authority_path,
        review_path,
        resource_manager=resource_manager,
        invocation_argv=invocation_argv,
        allow_terminal=receipt_exists,
    )
    second = validate_authority(
        repository,
        authority_path,
        review_path,
        resource_manager=resource_manager,
        invocation_argv=invocation_argv,
        allow_terminal=receipt_exists,
    )
    if (
        first.authority_raw != second.authority_raw
        or first.review_raw != second.review_raw
        or first.request_raw != second.request_raw
        or first.c5 != second.c5
    ):
        raise ExecutionError("two complete authority checks disagree")
    # Explicit pre-import lifecycle checks follow.
    _ = BOUNDS
    validate_request_and_ledger(
        first.authority,
        repository=repository,
        resource_manager=resource_manager,
        allow_terminal=receipt_exists,
    )
    validate_active_lock(
        first.authority, first.request, resource_manager=resource_manager
    )
    # Only now may run_scientific_cycles call _load_runner and the frozen
    # low-level _cycle; the exact BOUNDS are forwarded without relaxation.
    recovered = publish_or_recover(
        first, None, None, output, resource_manager=resource_manager
    )
    if recovered is not None:
        return recovered
    locations = first.authority["locations"]
    if work_root != Path(locations["work_root"]) or output != Path(locations["output"]):
        raise ExecutionError("live work/output paths differ from authority")
    if work_root.exists() or output.exists():
        raise ExecutionError("formal work or output already exists")
    claim = acquire_claim(first, resource_manager=resource_manager)
    try:
        cycles, raws, protected = run_scientific_cycles(first, work_root)
        # Re-run all live trust, Git, request, ledger, and official-lock checks
        # after the last child and before any result becomes canonical.
        final = validate_authority(
            repository,
            authority_path,
            review_path,
            resource_manager=resource_manager,
            invocation_argv=invocation_argv,
            allow_terminal=False,
        )
        if first.authority_raw != final.authority_raw or first.review_raw != final.review_raw or first.request_raw != final.request_raw or first.c5 != final.c5:
            raise ExecutionError("frozen authority changed during scientific execution")
        _verify_claim(claim, final, resource_manager)
        result = build_result(final, cycles, raws, protected)
        made = publish_or_recover(
            final, claim, result, output, resource_manager=resource_manager
        )
        if made is None:
            raise ExecutionError("canonical publication did not complete")
        return made
    finally:
        # Claims are immutable consumption records.  This verification does not
        # delete the official lock, which remains under acquire/release-test.ps1.
        release_claim(claim, first, resource_manager=resource_manager)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", required=True)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--resource-manager", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    if not sys.flags.isolated or not sys.dont_write_bytecode:
        raise ExecutionError("formal executor requires Python isolated/no-bytecode mode (-I -B)")
    arguments = _parser().parse_args()
    live_argv = live_formal_argv()
    execute(
        arguments.repository,
        arguments.authority,
        arguments.review,
        arguments.resource_manager,
        arguments.work_root,
        arguments.output,
        invocation_argv=live_argv,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
