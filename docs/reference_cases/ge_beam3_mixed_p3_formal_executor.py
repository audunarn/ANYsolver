"""One-use formal executor for GE-Beam3 P3 package and performance gates.

This program deliberately cannot author an authority.  It accepts one of two
closed, committed authority overlays, checks the repository and runtime twice,
claims the request and attempt durably, and only then invokes the frozen P3
gate.  Package and performance are separate serial requests; the latter must
bind the accepted package receipt, aggregate, and exact wheel.

The v2 harness also binds the consumed v1 package incident and materializes
the frozen candidate from raw Git blobs.  Checkout attributes therefore cannot
change evidence bytes before the package worker starts.
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
from decimal import Decimal, InvalidOperation
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
from typing import Any, Mapping, Sequence


SCHEMA = "anysolver.ge-beam3-mixed-p3-execution-authority-v2"
REVIEW_SCHEMA = "anysolver.ge-beam3-mixed-p3-execution-review-v2"
CHECK_SCHEMA = "anysolver.ge-beam3-mixed-p3-authority-check-v2"
CLAIM_SCHEMA = "anysolver.ge-beam3-mixed-p3-execution-claim-v1"
REQUEST_SCHEMA = "anysolver.ge-beam3-mixed-p3-execution-request-v1"
RECEIPT_SCHEMA = "anysolver.ge-beam3-mixed-p3-execution-receipt-v1"
RESULT_SCHEMA = "anysolver.ge-beam3-mixed-p3-formal-result-v1"
CLOSEOUT_SCHEMA = "anysolver.ge-beam3-mixed-p3-formal-evidence-v1"
STUDY_ID = "study_ge_beam3.mixed_straight_optin_integration_v1"
CANDIDATE_COMMIT = "f63b2fc000c87003ae5c322dbd881e98f64b22ab"
CANDIDATE_TREE = "3402268699829119cc9f4abce711535323f84a4a"
CANDIDATE_SUBJECT = "fix: correct GE Beam3 P3 Windows RSS diagnostics"
CANDIDATE_ID = "CANDIDATE_GE_BEAM3_DC_MIXED_K1_MACRO_V2"
FORMULATION_ID = "GE_BEAM3_DC_MIXED_K1_MACRO_V2"
GATE_RELATIVE = "docs/reference_cases/ge_beam3_mixed_p3_package_gate.py"
GATE_SHA256 = "1CA1D26A1994EDEB4C407948FF9BED00CE5F3435E8F280674F175589D8D7C90B"
CONTRACT_RELATIVE = "docs/reference_cases/ge_beam3_mixed_p3_formal_contract.json"
EXECUTOR_RELATIVE = "docs/reference_cases/ge_beam3_mixed_p3_formal_executor.py"
TEST_RELATIVE = "tests/test_ge_beam3_mixed_p3_formal_executor.py"
HARNESS_PATHS = (CONTRACT_RELATIVE, EXECUTOR_RELATIVE, TEST_RELATIVE)
HARNESS_SUBJECT = "docs: repair GE Beam3 P3 exact materialization harness"
HARNESS_V1_COMMIT = "ecf4cfe228d7513e9bb99f885c42da198a2d7fe5"
HARNESS_V1_TREE = "3e40cd5b158b027e8f1f5491399f7e8639d9ed7f"
HARNESS_V1_SUBJECT = "docs: freeze GE Beam3 P3 formal execution harness"
FAILED_PACKAGE_AUTHORITY_COMMIT = "48a3eba3347d9ebe0fd15cac6a8c7db64c1f743e"
FAILED_PACKAGE_AUTHORITY_TREE = "da4848f06678783e7f1e420c8b12f24050544470"
FAILED_PACKAGE_AUTHORITY_SHA256 = "4FA0230776029CAE990F37A710F8684A3D5C13320087A27FADC626A2A6948E73"
FAILED_PACKAGE_AUTHORITY_BYTES = 7_373
FAILED_PACKAGE_REVIEW_SHA256 = "DEE4F805EFF3ED606BDA4B7FCBFF6E3157D19007264D0D8D08DB396C002C3157"
FAILED_PACKAGE_REVIEW_BYTES = 478
PRIOR_INCIDENT = {
    "attempt_id": "2049501e1f29489eaef40c2d079c046d",
    "authority_commit": FAILED_PACKAGE_AUTHORITY_COMMIT,
    "bytes": 1_693,
    "classification": "FORMAL_HARNESS_CHECKOUT_EOL_TRANSFORM_DEFECT",
    "path": (r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease"
             r"\ge-beam3-p3-formal-20260905\incident\package-cycle1-root-cause.json"),
    "request_id": "902862c1b4354c398da8cc2f3bb2a487",
    "sha256": "AEB6431DE2CCE7CDDBC166E747B1245C11C755BAEE03FA8F4752A87FD3B071C1",
    "terminal": "BLOCKED_GE_BEAM3_P3_PROCESS_OR_EVIDENCE",
}
FAILED_INCIDENT_RECORD = {
    "a1": {
        "attempt_id": PRIOR_INCIDENT["attempt_id"],
        "authority": {
            "bytes": FAILED_PACKAGE_AUTHORITY_BYTES,
            "commit": FAILED_PACKAGE_AUTHORITY_COMMIT,
            "sha256": FAILED_PACKAGE_AUTHORITY_SHA256,
            "tree": FAILED_PACKAGE_AUTHORITY_TREE,
        },
        "receipt": {
            "bytes": 1_531,
            "sha256": "C19A51D05F8CFD5CD61B1E265138504053F2786D4DB6F494427E81665F1013C7",
        },
        "request": {
            "bytes": 2_668,
            "request_id": PRIOR_INCIDENT["request_id"],
            "sha256": "642A611E51DAE6000175D5DABE0B0BE8D935510C2CB2A21D47DDC932CE5745F3",
        },
        "result": {
            "bytes": 1_000,
            "sha256": "A21002ACDCC57AB474BF7C059E93C8F36CBD126DA77A79F485581EFAD6963C01",
        },
        "review": {
            "bytes": FAILED_PACKAGE_REVIEW_BYTES,
            "sha256": FAILED_PACKAGE_REVIEW_SHA256,
        },
        "synthesis": {
            "bytes": 2_078,
            "sha256": "C171E1618E33D7439209F25A44202DFBB9E7FA696287F0BE5A565891DB9EB602",
        },
    },
    "archive_ref": "refs/archive/ge-beam3-p3-package-cycle1-blocked-20260905",
    "candidate": {"commit": CANDIDATE_COMMIT, "tree": CANDIDATE_TREE},
    "diagnosis": {
        "checkout_bytes": 12_745,
        "checkout_path": "docs/S4_NULLSPACE_SEMANTICS_PROOF.md",
        "checkout_sha256": "713465F03BE6221119C1CCB7539301BE01324445DE54FC466D398185B7B481CD",
        "classification": PRIOR_INCIDENT["classification"],
        "gate_started": False,
        "git_attribute": "text eol=crlf",
        "git_blob_bytes": 12_414,
        "git_blob_sha256": "64895E2B56B81C3D5FB4318D026F049CA0BD8EE3591FAA434E2CC81C20F84754",
        "worker_started": False,
    },
    "production_boundary": {
        "activation_authorized": False,
        "candidate_mechanics_changed": False,
        "defaults_changed": False,
        "publication_authorized": False,
    },
    "schema": "anysolver.ge-beam3-mixed-p3-package-cycle1-incident-v1",
    "terminal": PRIOR_INCIDENT["terminal"],
}
AUTHORITY_PATHS = {
    "package": (
        "docs/reference_cases/ge_beam3_mixed_p3_package_execution_authority.json",
        "docs/reference_cases/ge_beam3_mixed_p3_package_execution_review.json",
    ),
    "performance": (
        "docs/reference_cases/ge_beam3_mixed_p3_performance_execution_authority.json",
        "docs/reference_cases/ge_beam3_mixed_p3_performance_execution_review.json",
    ),
}
AUTHORITY_SUBJECTS = {
    "package": "docs: authorize GE Beam3 P3 package execution",
    "performance": "docs: authorize GE Beam3 P3 performance execution",
}
REVIEW_VERDICTS = {
    "package": "ACCEPT_GE_BEAM3_P3_PACKAGE_EXECUTION_AUTHORITY_NO_P0_P1",
    "performance": "ACCEPT_GE_BEAM3_P3_PERFORMANCE_EXECUTION_AUTHORITY_NO_P0_P1",
}
BOUNDS = {
    "activity_timeout_seconds": 300,
    "child_wall_seconds": 600,
    "complete_wave_wall_seconds": 1800,
    "maximum_concurrent_workers": 3,
    "memory_limit_gib_per_process_tree": 24,
    "numerical_library_threads_per_worker": 1,
}
WHEELHOUSE_FILE_COUNT = 10
WHEELHOUSE_TOTAL_BYTES = 53_154_856
WHEELHOUSE_SHA256 = "CCD08F829BD604F0877BE71F689B1413288A1D470C3ECA0747A6BC07CDDCE39D"
THREAD_VARIABLES = (
    "BLIS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS",
    "NUMEXPR_NUM_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
    "TBB_NUM_THREADS",
)
PACKAGE_ACCEPTED = "ACCEPTED_GE_BEAM3_P3_PACKAGE_GATE"
TERMINAL_BLOCKED_AUTHORITY = "BLOCKED_GE_BEAM3_P3_BASELINE_OR_AUTHORITY"
TERMINAL_BLOCKED_PROCESS = "BLOCKED_GE_BEAM3_P3_PROCESS_OR_EVIDENCE"
TERMINAL_PACKAGE_NO_GO = "NO_GO_GE_BEAM3_P3_PACKAGE_ISOLATION"
TERMINAL_PERFORMANCE = "UNCLASSIFIED_GE_BEAM3_P3_PERFORMANCE"
TERMINAL_GO = "PROVISIONAL_GO_GE_BEAM3_STRAIGHT_STANDALONE_OPT_IN"
PACKAGE_GATE_SCHEMA = "anysolver.ge-beam3-mixed-p3-package-gate-v1"
PERFORMANCE_GATE_SCHEMA = "anysolver.ge-beam3-mixed-p3-performance-summary-v1"
HEX32 = re.compile(r"^[0-9a-f]{32}$")
SHA256 = re.compile(r"^[0-9A-F]{64}$")
OID = re.compile(r"^[0-9a-f]{40}$")


class FormalExecutionError(RuntimeError):
    """The frozen authority, environment, process, or evidence is invalid."""


@dataclasses.dataclass(frozen=True)
class ValidatedAuthority:
    mode: str
    authority: dict[str, Any]
    authority_identity: dict[str, Any]
    authority_commit: str
    authority_tree: str
    review_identity: dict[str, Any]
    runtime_sha256: str
    wheelhouse_sha256: str


@dataclasses.dataclass(frozen=True)
class Claim:
    external_request_path: Path
    request_path: Path
    attempt_path: Path
    receipt_path: Path
    lock_path: Path
    lock_raw: bytes
    claim_raw: bytes


def canonical_bytes(value: Any) -> bytes:
    def visit(item: Any) -> None:
        if item is None or type(item) in (bool, int, str):
            return
        if type(item) is float:
            if not math.isfinite(item):
                raise FormalExecutionError("nonfinite JSON number")
            return
        if type(item) is list:
            for child in item:
                visit(child)
            return
        if type(item) is dict:
            if any(type(key) is not str for key in item):
                raise FormalExecutionError("JSON keys must be strings")
            for child in item.values():
                visit(child)
            return
        raise FormalExecutionError(f"unsupported JSON type: {type(item).__name__}")

    visit(value)
    return (json.dumps(value, allow_nan=False, ensure_ascii=True,
                       separators=(",", ":"), sort_keys=True) + "\n").encode()


def _strict_json_bytes(raw: bytes, label: str) -> dict[str, Any]:
    def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
        made: dict[str, Any] = {}
        for key, value in rows:
            if key in made:
                raise FormalExecutionError(f"duplicate JSON key: {key}")
            made[key] = value
        return made

    def nonfinite(token: str) -> None:
        raise FormalExecutionError(f"nonfinite JSON token: {token}")

    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                           parse_constant=nonfinite)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise FormalExecutionError(f"invalid JSON: {label}") from exc
    if type(value) is not dict or canonical_bytes(value) != raw:
        raise FormalExecutionError(f"noncanonical JSON: {label}")
    return value


def strict_json(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = _regular_bytes(path)
    value = _strict_json_bytes(raw, path.name)
    return raw, value


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _is_sha(value: Any) -> bool:
    return type(value) is str and SHA256.fullmatch(value) is not None


def _is_oid(value: Any) -> bool:
    return type(value) is str and OID.fullmatch(value) is not None


def _is_plain_file(path: Path) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    reparse = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
    attrs = int(getattr(info, "st_file_attributes", 0))
    return stat.S_ISREG(info.st_mode) and not path.is_symlink() and not attrs & reparse


def _regular_bytes(path: Path) -> bytes:
    absolute = path.absolute()
    if not _is_plain_file(absolute) or absolute.resolve(strict=True) != absolute:
        raise FormalExecutionError(f"not an exact regular file: {path}")
    return absolute.read_bytes()


def file_identity(path: Path) -> dict[str, Any]:
    raw = _regular_bytes(path)
    if not raw:
        raise FormalExecutionError(f"empty file: {path.name}")
    return {"bytes": len(raw), "filename": path.name, "sha256": _sha(raw)}


def _artifact_identity(path: Path) -> dict[str, Any]:
    raw = _regular_bytes(path)
    return {"bytes": len(raw), "filename": path.name, "sha256": _sha(raw)}


def _identity_matches(path: Path, expected: Mapping[str, Any]) -> None:
    if set(expected) != {"bytes", "filename", "sha256"}:
        raise FormalExecutionError("file identity keys differ")
    if file_identity(path) != dict(expected):
        raise FormalExecutionError(f"file identity changed: {path.name}")


def _git_executable() -> Path:
    found = shutil.which("git")
    if found is None:
        raise FormalExecutionError("Git executable unavailable")
    return Path(found).resolve(strict=True)


def _base_environment() -> dict[str, str]:
    root = os.environ.get("SystemRoot", r"C:\Windows")
    path_rows = [
        str(_git_executable().parent), str(Path(sys.executable).resolve().parent),
        str(Path(sys.base_prefix) / "Scripts"), str(Path(root) / "System32"), root,
    ]
    deduplicated = list(dict.fromkeys(row for row in path_rows if Path(row).exists()))
    environment = {
        "COMSPEC": os.environ.get("COMSPEC", str(Path(root) / "System32/cmd.exe")),
        "GIT_ATTR_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0",
        "PATH": os.pathsep.join(deduplicated), "PATHEXT": os.environ.get("PATHEXT", ".EXE"),
        "PYTHONHASHSEED": "0", "PYTHONNOUSERSITE": "1", "PYTHONSAFEPATH": "1",
        "PYTHONDONTWRITEBYTECODE": "1", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "SystemRoot": root,
    }
    environment.update({name: "1" for name in THREAD_VARIABLES})
    return environment


def _git(repository: Path, *arguments: str, binary: bool = False) -> bytes | str:
    command = [str(_git_executable()), "--no-replace-objects", "-c",
               "core.attributesFile=NUL" if os.name == "nt" else "core.attributesFile=/dev/null",
               "-c", "core.hooksPath=NUL" if os.name == "nt" else "core.hooksPath=/dev/null",
               "-c", f"safe.directory={repository.resolve(strict=True)}", *arguments]
    result = subprocess.run(command, cwd=repository, env=_base_environment(),
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, timeout=120, check=False)
    if result.returncode:
        raise FormalExecutionError(result.stderr.decode(errors="replace").strip()
                                   or "Git command failed")
    return result.stdout if binary else result.stdout.decode("utf-8").strip()


def _changed_paths(repository: Path, commit: str) -> tuple[str, ...]:
    raw = str(_git(repository, "diff-tree", "--no-commit-id", "--name-only", "-r", commit))
    return tuple(sorted(row for row in raw.splitlines() if row))


def _require_commit_overlay(repository: Path, commit: str, *, parent: str,
                            subject: str, paths: Sequence[str]) -> str:
    if _git(repository, "rev-parse", f"{commit}^") != parent:
        raise FormalExecutionError("authority overlay parent differs")
    if _git(repository, "show", "-s", "--format=%s", commit) != subject:
        raise FormalExecutionError("authority overlay subject differs")
    if _changed_paths(repository, commit) != tuple(sorted(paths)):
        raise FormalExecutionError("authority overlay path extent differs")
    return str(_git(repository, "rev-parse", f"{commit}^{{tree}}"))


def _tree_rows(repository: Path, commit: str) -> list[dict[str, str]]:
    raw = _git(repository, "ls-tree", "-rz", "--full-tree", commit, binary=True)
    rows: list[dict[str, str]] = []
    assert isinstance(raw, bytes)
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, name = record.split(b"\t", 1)
        mode, kind, oid = metadata.decode("ascii").split()
        if kind != "blob" or mode == "120000":
            raise FormalExecutionError("symlinks, gitlinks, and non-blobs are forbidden")
        rows.append({"mode": mode, "oid": oid, "path": name.decode("utf-8")})
    return sorted(rows, key=lambda row: row["path"])


def tree_manifest(repository: Path, commit: str) -> dict[str, Any]:
    rows = _tree_rows(repository, commit)
    return {"file_count": len(rows), "sha256": _sha(canonical_bytes(rows))}


def _blob_identity(repository: Path, commit: str, relative: str) -> dict[str, Any]:
    raw = _git(repository, "cat-file", "blob", f"{commit}:{relative}", binary=True)
    assert isinstance(raw, bytes)
    return {"bytes": len(raw), "path": relative, "sha256": _sha(raw)}


def _require_unmodified_git_graph(repository: Path) -> None:
    if _git(repository, "status", "--porcelain=v1", "--untracked-files=all"):
        raise FormalExecutionError("authority repository is dirty")
    if _git(repository, "for-each-ref", "--format=%(refname)", "refs/replace"):
        raise FormalExecutionError("replacement objects are forbidden")
    git_dir = Path(str(_git(repository, "rev-parse", "--absolute-git-dir")))
    common = Path(str(_git(repository, "rev-parse", "--git-common-dir")))
    if not common.is_absolute():
        common = (repository / common).resolve()
    for path in (git_dir / "info/grafts", common / "objects/info/alternates",
                 common / "shallow"):
        if path.exists() and path.read_bytes().strip():
            raise FormalExecutionError(f"Git graph indirection is forbidden: {path.name}")


def _distribution_identity(name: str) -> dict[str, Any]:
    try:
        distribution = importlib.metadata.distribution(name)
    except importlib.metadata.PackageNotFoundError as exc:
        raise FormalExecutionError(f"required distribution unavailable: {name}") from exc
    metadata = Path(distribution._path) / "METADATA"  # type: ignore[attr-defined]
    identity = file_identity(metadata)
    return {"metadata_sha256": identity["sha256"], "name": name,
            "version": distribution.version}


def runtime_identity() -> dict[str, Any]:
    python = Path(sys.executable).resolve(strict=True)
    git = _git_executable()
    git_result = subprocess.run([str(git), "--version"], env=_base_environment(),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                check=True, timeout=30, text=True)
    pip_result = subprocess.run([str(python), "-I", "-m", "pip", "--version"],
                                env=_base_environment(), stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, check=True, timeout=30, text=True)
    return {
        "controlled_environment": {
            "git_configuration": "DISABLED", "hash_seed": "0",
            "numerical_library_threads": 1, "pip_configuration": "DISABLED",
            "pip_index": "DISABLED", "python_injection": "DISABLED",
            "pytest_injection": "DISABLED", "user_site": "DISABLED",
        },
        "distributions": [_distribution_identity(name) for name in
                          ("pip", "setuptools", "wheel", "packaging", "numpy", "scipy")],
        "git": {**file_identity(git), "version": git_result.stdout.strip()},
        "python": {**file_identity(python), "cache_tag": sys.implementation.cache_tag,
                   "implementation": sys.implementation.name,
                   "version": platform.python_version()},
        "windows": {"architecture": platform.machine(), "release": platform.release(),
                    "version": platform.version(), "win32_ver": list(platform.win32_ver())},
        "pip_command": pip_result.stdout.strip(),
    }


def wheelhouse_identity(root: Path) -> dict[str, Any]:
    absolute = root.absolute()
    if not absolute.is_dir() or absolute.is_symlink() or absolute.resolve() != absolute:
        raise FormalExecutionError("wheelhouse must be an exact ordinary directory")
    rows = []
    for path in sorted(absolute.rglob("*")):
        information = path.lstat()
        reparse = int(getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
        if stat.S_ISDIR(information.st_mode) and not path.is_symlink() \
                and not int(getattr(information, "st_file_attributes", 0)) & reparse:
            continue
        if path.suffix.lower() != ".whl" or not _is_plain_file(path):
            raise FormalExecutionError("wheelhouse contains a non-wheel or indirection")
        identity = file_identity(path)
        rows.append({"bytes": identity["bytes"],
                     "path": path.relative_to(absolute).as_posix(),
                     "sha256": identity["sha256"]})
    if not rows:
        raise FormalExecutionError("wheelhouse is empty")
    made = {"file_count": len(rows), "files": rows,
            "sha256": _sha(canonical_bytes(rows)),
            "total_bytes": sum(row["bytes"] for row in rows)}
    if (made["file_count"], made["total_bytes"], made["sha256"]) != (
            WHEELHOUSE_FILE_COUNT, WHEELHOUSE_TOTAL_BYTES, WHEELHOUSE_SHA256):
        raise FormalExecutionError("wheelhouse differs from the frozen ten-wheel set")
    return made


def _validate_file_rows(rows: Any, required_paths: Sequence[str]) -> None:
    if type(rows) is not list or len(rows) != len(required_paths):
        raise FormalExecutionError("harness file inventory differs")
    expected = set(required_paths)
    for row in rows:
        if type(row) is not dict or set(row) != {"bytes", "path", "sha256"}:
            raise FormalExecutionError("harness file row is malformed")
        if row["path"] not in expected or type(row["bytes"]) is not int or row["bytes"] <= 0 \
                or not _is_sha(row["sha256"]):
            raise FormalExecutionError("harness file identity is malformed")
        expected.remove(row["path"])
    if expected:
        raise FormalExecutionError("harness path is missing")


def _validate_authority(value: Any, *, mode: str, runtime: dict[str, Any],
                        wheelhouse: dict[str, Any]) -> dict[str, Any]:
    keys = {"activation_authorized", "candidate", "execution", "execution_authorized",
            "formal_argv", "harness", "locations", "mode", "overlay",
            "package_input", "prior_incident", "publication_authorized", "request", "runtime",
            "schema", "study_id", "wheelhouse"}
    if type(value) is not dict or set(value) != keys:
        raise FormalExecutionError("authority keys differ")
    if value["schema"] != SCHEMA or value["study_id"] != STUDY_ID or value["mode"] != mode:
        raise FormalExecutionError("authority identity differs")
    if value["execution_authorized"] is not True or value["activation_authorized"] is not False \
            or value["publication_authorized"] is not False:
        raise FormalExecutionError("authority scope differs")
    candidate = value["candidate"]
    if type(candidate) is not dict or set(candidate) != {
        "candidate_id", "commit", "formulation_id", "gate_sha256",
        "manifest_sha256", "selector", "tree"
    } or candidate["candidate_id"] != CANDIDATE_ID or candidate["commit"] != CANDIDATE_COMMIT \
            or candidate["tree"] != CANDIDATE_TREE or candidate["formulation_id"] != FORMULATION_ID \
            or candidate["selector"] != "ge-beam3" or candidate["gate_sha256"] != GATE_SHA256 \
            or not _is_sha(candidate["manifest_sha256"]):
        raise FormalExecutionError("candidate binding differs")
    if value["execution"] != BOUNDS:
        raise FormalExecutionError("execution bounds differ")
    harness = value["harness"]
    if type(harness) is not dict or set(harness) != {"commit", "files", "tree"} \
            or not _is_oid(harness["commit"]) or not _is_oid(harness["tree"]):
        raise FormalExecutionError("harness identity is malformed")
    _validate_file_rows(harness["files"], HARNESS_PATHS)
    overlay = value["overlay"]
    if type(overlay) is not dict or set(overlay) != {"exact_paths", "expected_parent", "subject"} \
            or overlay["exact_paths"] != list(AUTHORITY_PATHS[mode]) \
            or overlay["subject"] != AUTHORITY_SUBJECTS[mode] \
            or not _is_oid(overlay["expected_parent"]):
        raise FormalExecutionError("overlay binding differs")
    request = value["request"]
    if type(request) is not dict or set(request) != {"attempt_id", "record_sha256", "request_id"} \
            or HEX32.fullmatch(str(request["request_id"])) is None \
            or HEX32.fullmatch(str(request["attempt_id"])) is None \
            or request["request_id"] == request["attempt_id"] \
            or not _is_sha(request["record_sha256"]):
        raise FormalExecutionError("request identity is malformed")
    if request["request_id"] in {PRIOR_INCIDENT["request_id"], PRIOR_INCIDENT["attempt_id"]} \
            or request["attempt_id"] in {
                PRIOR_INCIDENT["request_id"], PRIOR_INCIDENT["attempt_id"]}:
        raise FormalExecutionError("prior failed-package request or attempt was reused")
    runtime_binding = value["runtime"]
    if type(runtime_binding) is not dict or set(runtime_binding) != {"identity", "sha256"} \
            or runtime_binding["identity"] != runtime \
            or runtime_binding["sha256"] != _sha(canonical_bytes(runtime)):
        raise FormalExecutionError("runtime identity differs")
    if value["wheelhouse"] != wheelhouse:
        raise FormalExecutionError("wheelhouse identity differs")
    if value["prior_incident"] != PRIOR_INCIDENT:
        raise FormalExecutionError("prior failed-package incident binding differs")
    locations = value["locations"]
    location_keys = {"authority", "candidate_wheel", "executor", "output",
                     "package_aggregate", "package_receipt", "registry", "repository",
                     "review", "wheelhouse", "work_root"}
    if type(locations) is not dict or set(locations) != location_keys:
        raise FormalExecutionError("registered location inventory differs")
    for key, path in locations.items():
        if path is None and key in {"candidate_wheel", "package_aggregate", "package_receipt"}:
            continue
        if type(path) is not str or not Path(path).is_absolute() or str(Path(path)) != path:
            raise FormalExecutionError("registered location is not an exact absolute path")
    if locations["executor"] != str(Path(locations["repository"]) / EXECUTOR_RELATIVE) \
            or locations["authority"] != str(Path(locations["repository"]) / AUTHORITY_PATHS[mode][0]) \
            or locations["review"] != str(Path(locations["repository"]) / AUTHORITY_PATHS[mode][1]):
        raise FormalExecutionError("registered repository program paths differ")
    if mode == "package" and any(locations[key] is not None for key in
                                 ("candidate_wheel", "package_aggregate", "package_receipt")):
        raise FormalExecutionError("package registered inputs must be null")
    if mode == "performance" and any(locations[key] is None for key in
                                     ("candidate_wheel", "package_aggregate", "package_receipt")):
        raise FormalExecutionError("performance registered inputs are incomplete")
    if value["formal_argv"] != _expected_formal_argv(mode, locations):
        raise FormalExecutionError("formal invocation differs")
    package_input = value["package_input"]
    if mode == "package" and package_input is not None:
        raise FormalExecutionError("package mode must not bind package input")
    if mode == "performance":
        if type(package_input) is not dict or set(package_input) != {
            "aggregate", "package_authority_sha256", "package_request_id", "receipt", "wheel"
        } or HEX32.fullmatch(str(package_input["package_request_id"])) is None:
            raise FormalExecutionError("performance package input differs")
        if not _is_sha(package_input["package_authority_sha256"]):
            raise FormalExecutionError("package authority hash is malformed")
        for key in ("aggregate", "receipt", "wheel"):
            row = package_input[key]
            if type(row) is not dict or set(row) != {"bytes", "filename", "sha256"} \
                    or type(row["bytes"]) is not int or row["bytes"] <= 0 \
                    or type(row["filename"]) is not str or Path(row["filename"]).name != row["filename"] \
                    or not _is_sha(row["sha256"]):
                raise FormalExecutionError("performance package file identity differs")
    return value


def _expected_formal_argv(mode: str, locations: Mapping[str, Any]) -> list[str]:
    argv = [str(Path(sys.executable).resolve()), "-I", "-B", locations["executor"],
            "--execute", "--mode", mode, "--repository", locations["repository"],
            "--authority", locations["authority"], "--review", locations["review"],
            "--wheelhouse", locations["wheelhouse"], "--registry", locations["registry"],
            "--work-root", locations["work_root"], "--output", locations["output"]]
    if mode == "performance":
        argv.extend(("--package-receipt", locations["package_receipt"],
                     "--package-aggregate", locations["package_aggregate"],
                     "--candidate-wheel", locations["candidate_wheel"]))
    return argv


def _validate_review(value: Any, authority_identity: Mapping[str, Any], mode: str) -> None:
    if type(value) is not dict or set(value) != {
        "findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"
    } or value["schema"] != REVIEW_SCHEMA or value["findings"] != [] \
            or value["verdict"] != REVIEW_VERDICTS[mode]:
        raise FormalExecutionError("independent review differs")
    expected_input = {"bytes": authority_identity["bytes"],
                      "path": AUTHORITY_PATHS[mode][0],
                      "sha256": authority_identity["sha256"]}
    if value["reviewed_inputs"] != [expected_input]:
        raise FormalExecutionError("reviewed authority identity differs")
    independence = value["reviewer_independence"]
    if independence != {
        "authority_authorship": False, "execution_performed": False,
        "role": f"INDEPENDENT_GE_BEAM3_P3_{mode.upper()}_EXECUTION_REVIEWER",
    }:
        raise FormalExecutionError("reviewer independence differs")


def _validate_prior_incident(repository: Path) -> None:
    incident_path = Path(PRIOR_INCIDENT["path"])
    raw, incident = strict_json(incident_path)
    if {"bytes": len(raw), "path": str(incident_path), "sha256": _sha(raw)} != {
        "bytes": PRIOR_INCIDENT["bytes"], "path": PRIOR_INCIDENT["path"],
        "sha256": PRIOR_INCIDENT["sha256"],
    } or incident != FAILED_INCIDENT_RECORD:
        raise FormalExecutionError("prior failed-package incident record differs")
    if _git(repository, "rev-parse", FAILED_INCIDENT_RECORD["archive_ref"]) \
            != FAILED_PACKAGE_AUTHORITY_COMMIT:
        raise FormalExecutionError("prior failed-package archive ref differs")
    if _require_commit_overlay(
            repository, FAILED_PACKAGE_AUTHORITY_COMMIT,
            parent=HARNESS_V1_COMMIT, subject=AUTHORITY_SUBJECTS["package"],
            paths=AUTHORITY_PATHS["package"]) != FAILED_PACKAGE_AUTHORITY_TREE:
        raise FormalExecutionError("prior failed-package authority commit differs")
    old_authority = _blob_identity(
        repository, FAILED_PACKAGE_AUTHORITY_COMMIT, AUTHORITY_PATHS["package"][0])
    old_review = _blob_identity(
        repository, FAILED_PACKAGE_AUTHORITY_COMMIT, AUTHORITY_PATHS["package"][1])
    if old_authority != {
            "bytes": FAILED_PACKAGE_AUTHORITY_BYTES,
            "path": AUTHORITY_PATHS["package"][0],
            "sha256": FAILED_PACKAGE_AUTHORITY_SHA256,
    } or old_review != {
            "bytes": FAILED_PACKAGE_REVIEW_BYTES,
            "path": AUTHORITY_PATHS["package"][1],
            "sha256": FAILED_PACKAGE_REVIEW_SHA256,
    }:
        raise FormalExecutionError("prior failed-package authority blobs differ")

    release_root = incident_path.parent.parent
    registry = Path(r"C:\Github\.resource-manager")
    request_id = PRIOR_INCIDENT["request_id"]
    paths = {
        "request": registry / "requests" / f"{request_id}.json",
        "receipt": registry / "receipts" / f"{request_id}.json",
        "result": release_root / "canonical" / f"package-result-{request_id}.json",
        "synthesis_one": release_root / "incident" / "package-blocked-synthesis-1.json",
        "synthesis_two": release_root / "incident" / "package-blocked-synthesis-2.json",
    }
    for key, path in paths.items():
        raw_value = _regular_bytes(path)
        expected_key = "synthesis" if key.startswith("synthesis_") else key
        expected = FAILED_INCIDENT_RECORD["a1"][expected_key]
        if len(raw_value) != expected["bytes"] or _sha(raw_value) != expected["sha256"]:
            raise FormalExecutionError(f"prior failed-package {expected_key} differs")
        _strict_json_bytes(raw_value, path.name)
    request = _strict_json_bytes(_regular_bytes(paths["request"]), "prior request")
    receipt = _strict_json_bytes(_regular_bytes(paths["receipt"]), "prior receipt")
    result = _strict_json_bytes(_regular_bytes(paths["result"]), "prior result")
    if request.get("request_id") != request_id \
            or request.get("attempt_id") != PRIOR_INCIDENT["attempt_id"] \
            or receipt.get("request_id") != request_id \
            or receipt.get("attempt_id") != PRIOR_INCIDENT["attempt_id"] \
            or receipt.get("authority_commit") != FAILED_PACKAGE_AUTHORITY_COMMIT \
            or receipt.get("terminal") != PRIOR_INCIDENT["terminal"] \
            or result.get("request_id") != request_id \
            or result.get("authority", {}).get("commit") != FAILED_PACKAGE_AUTHORITY_COMMIT \
            or result.get("terminal") != PRIOR_INCIDENT["terminal"]:
        raise FormalExecutionError("prior failed-package provenance differs")


def _validate_git_chain(repository: Path, validated: ValidatedAuthority,
                        *, commit: str | None = None) -> None:
    _require_unmodified_git_graph(repository)
    authority = validated.authority
    head = str(_git(repository, "rev-parse", "HEAD" if commit is None else commit))
    if str(_git(repository, "rev-parse", f"{CANDIDATE_COMMIT}^{{tree}}")) != CANDIDATE_TREE \
            or _git(repository, "show", "-s", "--format=%s", CANDIDATE_COMMIT) != CANDIDATE_SUBJECT:
        raise FormalExecutionError("candidate Git identity differs")
    if tree_manifest(repository, CANDIDATE_COMMIT)["sha256"] != authority["candidate"]["manifest_sha256"]:
        raise FormalExecutionError("candidate tree manifest differs")
    gate_raw = _git(repository, "cat-file", "blob",
                    f"{CANDIDATE_COMMIT}:{GATE_RELATIVE}", binary=True)
    assert isinstance(gate_raw, bytes)
    if _sha(gate_raw) != authority["candidate"]["gate_sha256"]:
        raise FormalExecutionError("candidate package gate differs")
    _validate_gate_safeguards(gate_raw)
    if _require_commit_overlay(
            repository, HARNESS_V1_COMMIT, parent=CANDIDATE_COMMIT,
            subject=HARNESS_V1_SUBJECT, paths=HARNESS_PATHS) != HARNESS_V1_TREE:
        raise FormalExecutionError("original harness tree differs")
    _validate_prior_incident(repository)
    harness = authority["harness"]
    if _require_commit_overlay(
            repository, harness["commit"], parent=FAILED_PACKAGE_AUTHORITY_COMMIT,
            subject=HARNESS_SUBJECT, paths=HARNESS_PATHS) != harness["tree"]:
        raise FormalExecutionError("harness tree differs")
    for row in harness["files"]:
        if _blob_identity(repository, harness["commit"], row["path"]) != row:
            raise FormalExecutionError("harness blob differs")
    overlay = authority["overlay"]
    if overlay["expected_parent"] != str(_git(repository, "rev-parse", f"{head}^")):
        raise FormalExecutionError("authority HEAD or parent differs")
    authority_tree = _require_commit_overlay(
        repository, head, parent=overlay["expected_parent"], subject=overlay["subject"],
        paths=overlay["exact_paths"])
    if validated.mode == "package" and overlay["expected_parent"] != harness["commit"]:
        raise FormalExecutionError("package authority does not directly follow harness")
    if validated.mode == "performance":
        package_commit = overlay["expected_parent"]
        if _require_commit_overlay(repository, package_commit, parent=harness["commit"],
                                   subject=AUTHORITY_SUBJECTS["package"],
                                   paths=AUTHORITY_PATHS["package"]) != str(
                _git(repository, "rev-parse", f"{package_commit}^{{tree}}")):
            raise FormalExecutionError("package authority predecessor differs")
        package_authority = _blob_identity(
            repository, package_commit, AUTHORITY_PATHS["package"][0])
        if package_authority["sha256"] != authority["package_input"]["package_authority_sha256"]:
            raise FormalExecutionError("bound package authority predecessor differs")
    if authority_tree != validated.authority_tree:
        raise FormalExecutionError("authority tree changed")
    for relative, identity in zip(AUTHORITY_PATHS[validated.mode],
                                  (validated.authority_identity, validated.review_identity)):
        blob = _blob_identity(repository, head, relative)
        expected = {"bytes": identity["bytes"], "path": relative,
                    "sha256": identity["sha256"]}
        if blob != expected:
            raise FormalExecutionError("authority overlay blob differs")


def _validate_gate_safeguards(raw: bytes) -> None:
    try:
        tree = ast.parse(raw.decode("utf-8"))
    except (UnicodeError, SyntaxError) as exc:
        raise FormalExecutionError("candidate package gate cannot be parsed") from exc
    found: dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            try:
                found[node.targets[0].id] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                pass
    expected = {
        "CHILD_TIMEOUT_SECONDS": 600, "WAVE_TIMEOUT_SECONDS": 1800,
        "INACTIVITY_SECONDS": 300, "MEMORY_LIMIT_GIB": 24,
        "PROCESS_CONTAINMENT_ID": "WINDOWS_JOB_OBJECT_SUSPENDED_ASSIGN_V1",
        "MINIMUM_PAIRS": 11,
    }
    if any(found.get(key) != value for key, value in expected.items()):
        raise FormalExecutionError("candidate gate safeguards differ")
    text = raw.decode("utf-8")
    for flag in ("--run-package-gate", "--run-performance-gate",
                 "--candidate-wheel", "--package-aggregate"):
        if flag not in text:
            raise FormalExecutionError("candidate gate interface differs")


def authority_check(repository: Path, authority_path: Path, review_path: Path,
                    wheelhouse: Path, *, mode: str) -> tuple[ValidatedAuthority, dict[str, Any]]:
    if mode not in AUTHORITY_PATHS:
        raise FormalExecutionError("unsupported formal mode")
    repository = repository.resolve(strict=True)
    expected_paths = tuple((repository / row).absolute() for row in AUTHORITY_PATHS[mode])
    if (authority_path.absolute(), review_path.absolute()) != expected_paths:
        raise FormalExecutionError("authority paths are not the registered overlay paths")
    authority_raw, authority = strict_json(authority_path)
    review_raw, review = strict_json(review_path)
    runtime = runtime_identity()
    wheelhouse_record = wheelhouse_identity(wheelhouse)
    _validate_authority(authority, mode=mode, runtime=runtime, wheelhouse=wheelhouse_record)
    locations = authority["locations"]
    actual_known = {
        "authority": str(authority_path.absolute()),
        "executor": str((repository / EXECUTOR_RELATIVE).absolute()),
        "repository": str(repository), "review": str(review_path.absolute()),
        "wheelhouse": str(wheelhouse.resolve(strict=True)),
    }
    if any(locations[key] != value for key, value in actual_known.items()):
        raise FormalExecutionError("invocation differs from registered locations")
    authority_id = {"bytes": len(authority_raw), "filename": authority_path.name,
                    "sha256": _sha(authority_raw)}
    review_id = {"bytes": len(review_raw), "filename": review_path.name,
                 "sha256": _sha(review_raw)}
    _validate_review(review, authority_id, mode)
    head = str(_git(repository, "rev-parse", "HEAD"))
    validated = ValidatedAuthority(
        mode, authority, authority_id, head,
        str(_git(repository, "rev-parse", "HEAD^{tree}")), review_id,
        _sha(canonical_bytes(runtime)), wheelhouse_record["sha256"],
    )
    _validate_git_chain(repository, validated)
    check = {
        "authority_commit": validated.authority_commit,
        "authority_sha256": authority_id["sha256"], "mode": mode,
        "request_id": authority["request"]["request_id"], "schema": CHECK_SCHEMA,
        "validated": True,
    }
    return validated, check


def _validate_registered_execution(validated: ValidatedAuthority, registry: Path,
                                   work_root: Path, output: Path,
                                   package_receipt: Path | None,
                                   package_aggregate: Path | None,
                                   candidate_wheel: Path | None) -> None:
    locations = validated.authority["locations"]
    actual = {
        "registry": str(registry.resolve(strict=True)),
        "work_root": str(work_root.absolute()), "output": str(output.absolute()),
        "package_receipt": None if package_receipt is None else str(package_receipt.absolute()),
        "package_aggregate": None if package_aggregate is None else str(package_aggregate.absolute()),
        "candidate_wheel": None if candidate_wheel is None else str(candidate_wheel.absolute()),
    }
    if any(locations[key] != value for key, value in actual.items()):
        raise FormalExecutionError("execution paths differ from registered locations")


def _request_record(validated: ValidatedAuthority) -> dict[str, Any]:
    authority = validated.authority
    return {
        "attempt_id": authority["request"]["attempt_id"], "bounds": BOUNDS,
        "formal_argv": authority["formal_argv"], "locations": authority["locations"],
        "mode": validated.mode, "request_id": authority["request"]["request_id"],
        "schema": REQUEST_SCHEMA, "study_id": STUDY_ID,
    }


def _validate_request(validated: ValidatedAuthority, registry: Path) -> tuple[Path, bytes]:
    request_id = validated.authority["request"]["request_id"]
    path = registry.resolve(strict=True) / "requests" / f"{request_id}.json"
    raw, value = strict_json(path)
    if value != _request_record(validated) \
            or _sha(raw) != validated.authority["request"]["record_sha256"]:
        raise FormalExecutionError("immutable external request differs")
    return path, raw


def _fsync_exclusive(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb", buffering=0) as stream:
        stream.write(raw)
        os.fsync(stream.fileno())


def _acquire_claim(validated: ValidatedAuthority, registry: Path) -> Claim:
    registry = registry.resolve(strict=True)
    external_request_path, external_request_raw = _validate_request(validated, registry)
    lock_path = registry / "active.lock"
    request = validated.authority["request"]
    lock_record = {"attempt_id": request["attempt_id"], "mode": validated.mode,
                   "request_id": request["request_id"], "schema": CLAIM_SCHEMA}
    lock_raw = canonical_bytes(lock_record)
    _fsync_exclusive(lock_path, lock_raw)
    try:
        claims = registry / "claims"
        attempts = registry / "attempts"
        receipts = registry / "receipts"
        for path in (claims, attempts, receipts):
            path.mkdir(exist_ok=True)
            if path.is_symlink():
                raise FormalExecutionError("registry indirection is forbidden")
        record = {
            "attempt_id": request["attempt_id"],
            "authority_commit": validated.authority_commit,
            "authority_sha256": validated.authority_identity["sha256"],
            "mode": validated.mode, "request_id": request["request_id"],
            "runtime_sha256": validated.runtime_sha256, "schema": CLAIM_SCHEMA,
            "wheelhouse_sha256": validated.wheelhouse_sha256,
        }
        raw = canonical_bytes(record)
        request_path = claims / f"{request['request_id']}.json"
        attempt_path = attempts / f"{request['attempt_id']}.json"
        receipt_path = receipts / f"{request['request_id']}.json"
        if any(path.exists() for path in (request_path, attempt_path, receipt_path)):
            raise FormalExecutionError("request or attempt is already consumed")
        record["request_record_sha256"] = _sha(external_request_raw)
        raw = canonical_bytes(record)
        _fsync_exclusive(request_path, raw)
        try:
            _fsync_exclusive(attempt_path, raw)
        except BaseException:
            # The request remains consumed even if the second uniqueness claim fails.
            raise
        return Claim(external_request_path, request_path, attempt_path, receipt_path,
                     lock_path, lock_raw, raw)
    except BaseException:
        if lock_path.exists() and _regular_bytes(lock_path) == lock_raw:
            lock_path.unlink()
        raise


def _release_lock(claim: Claim) -> None:
    if not claim.lock_path.exists() or _regular_bytes(claim.lock_path) != claim.lock_raw:
        raise FormalExecutionError("global execution lock changed")
    claim.lock_path.unlink()


def _verify_claim(claim: Claim) -> None:
    if _regular_bytes(claim.request_path) != claim.claim_raw \
            or _regular_bytes(claim.attempt_path) != claim.claim_raw \
            or _sha(_regular_bytes(claim.external_request_path)) != _strict_json_bytes(
                claim.claim_raw, "claim")["request_record_sha256"]:
        raise FormalExecutionError("immutable execution claim changed")


def _verify_checkout(repository: Path) -> None:
    rows = _tree_rows(repository, CANDIDATE_COMMIT)
    expected = {row["path"] for row in rows}
    actual = {path.relative_to(repository).as_posix() for path in repository.rglob("*")
              if path.is_file() and ".git" not in path.relative_to(repository).parts}
    if actual != expected:
        raise FormalExecutionError("materialized candidate path inventory differs")
    for row in rows:
        path = repository / row["path"]
        raw = _regular_bytes(path)
        blob = _git(repository, "cat-file", "blob", row["oid"], binary=True)
        if raw != blob:
            raise FormalExecutionError(f"materialized candidate blob differs: {row['path']}")
    if _git(repository, "rev-parse", "HEAD") != CANDIDATE_COMMIT \
            or _git(repository, "rev-parse", "HEAD^{tree}") != CANDIDATE_TREE \
            or _git(repository, "status", "--porcelain=v1", "--untracked-files=all"):
        raise FormalExecutionError("materialized candidate topology differs")


def _populate_exact_worktree(repository: Path) -> None:
    """Populate the index and worktree from raw blobs, bypassing EOL filters."""
    _git(repository, "config", "--local", "core.autocrlf", "false")
    _git(repository, "config", "--local", "core.eol", "lf")
    _git(repository, "config", "--local", "core.safecrlf", "true")
    _git(repository, "update-ref", "--no-deref", "HEAD", CANDIDATE_COMMIT)
    _git(repository, "read-tree", "--reset", CANDIDATE_COMMIT)
    for row in _tree_rows(repository, CANDIDATE_COMMIT):
        path = repository / row["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = _git(repository, "cat-file", "blob", row["oid"], binary=True)
        assert isinstance(raw, bytes)
        with path.open("xb", buffering=0) as stream:
            stream.write(raw)
        if row["mode"] == "100755" and os.name != "nt":
            path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _materialize(repository: Path, destination: Path) -> Path:
    if destination.exists():
        raise FormalExecutionError("candidate materialization path already exists")
    environment = _base_environment()
    command = [str(_git_executable()), "--no-replace-objects", "-c",
               "core.attributesFile=NUL" if os.name == "nt" else "core.attributesFile=/dev/null",
               "-c", "core.hooksPath=NUL" if os.name == "nt" else "core.hooksPath=/dev/null",
               "clone", "--local", "--no-hardlinks", "--no-checkout",
               str(repository.resolve(strict=True)), str(destination)]
    result = subprocess.run(command, env=environment, stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=120, check=False)
    if result.returncode:
        raise FormalExecutionError("candidate clone failed")
    _populate_exact_worktree(destination)
    _verify_checkout(destination)
    return destination


def _child_environment(wheelhouse: Path, temp: Path) -> dict[str, str]:
    environment = _base_environment()
    temp.mkdir(parents=True, exist_ok=False)
    environment.update({
        "PIP_CONFIG_FILE": os.devnull, "PIP_DISABLE_PIP_VERSION_CHECK": "1",
        "PIP_FIND_LINKS": str(wheelhouse.resolve(strict=True)), "PIP_NO_CACHE_DIR": "1",
        "PIP_NO_INDEX": "1", "TEMP": str(temp), "TMP": str(temp),
    })
    return environment


@dataclasses.dataclass(frozen=True)
class ProcessResult:
    returncode: int
    forced_reason: str | None


def _terminate_tree(process: subprocess.Popen[bytes]) -> None:
    if os.name == "nt":
        subprocess.run([r"C:\Windows\System32\taskkill.exe", "/PID", str(process.pid),
                        "/T", "/F"], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=False, timeout=30)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def _run_bounded(command: Sequence[str], *, cwd: Path, environment: Mapping[str, str],
                 log_path: Path, wall_seconds: int = 1830) -> ProcessResult:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    with log_path.open("xb", buffering=0) as log:
        process = subprocess.Popen(tuple(command), cwd=cwd, env=dict(environment),
                                   stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                   creationflags=flags,
                                   start_new_session=os.name != "nt")
        deadline = time.monotonic() + wall_seconds
        while process.poll() is None and time.monotonic() < deadline:
            time.sleep(0.1)
        reason = None
        if process.poll() is None:
            reason = "COMPLETE_WAVE_WALL_LIMIT"
            _terminate_tree(process)
        try:
            code = process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            reason = "PROCESS_TREE_DRAIN_FAILURE"
            _terminate_tree(process)
            code = process.wait(timeout=30)
    if reason is not None and code == 0:
        # Windows can report zero after taskkill closes a sleeping interpreter.
        # A forced termination is never a successful process outcome.
        code = 1
    return ProcessResult(code, reason)


def _gate_command(mode: str, materialized: Path, gate_root: Path,
                  package_aggregate: Path | None, wheel: Path | None) -> tuple[str, ...]:
    gate = materialized / GATE_RELATIVE
    command = [str(Path(sys.executable).resolve()), "-I", "-B", str(gate)]
    if mode == "package":
        command.extend(("--run-package-gate", "--repository", str(materialized),
                        "--output-root", str(gate_root)))
    else:
        assert package_aggregate is not None and wheel is not None
        command.extend(("--run-performance-gate", "--repository", str(materialized),
                        "--output-root", str(gate_root), "--candidate-wheel", str(wheel),
                        "--package-aggregate", str(package_aggregate), "--pair-count", "11"))
    return tuple(command)


def _validate_package_inputs(validated: ValidatedAuthority, receipt: Path | None,
                             aggregate: Path | None, wheel: Path | None) -> None:
    if validated.mode == "package":
        if any(item is not None for item in (receipt, aggregate, wheel)):
            raise FormalExecutionError("package mode rejects prior-package arguments")
        return
    if receipt is None or aggregate is None or wheel is None:
        raise FormalExecutionError("performance mode requires package receipt, aggregate, and wheel")
    bound = validated.authority["package_input"]
    for key, path in (("receipt", receipt), ("aggregate", aggregate), ("wheel", wheel)):
        _identity_matches(path, bound[key])
    _raw, receipt_value = strict_json(receipt)
    if set(receipt_value) != {"aggregate_core", "aggregate_core_sha256", "attempt_id",
                              "authority_commit", "authority_sha256", "claim_sha256",
                              "request_id", "request_record_sha256", "runtime_sha256", "schema", "terminal",
                              "wheelhouse_sha256"} \
            or receipt_value.get("schema") != RECEIPT_SCHEMA \
            or receipt_value.get("request_id") != bound["package_request_id"] \
            or receipt_value.get("terminal") != PACKAGE_ACCEPTED \
            or receipt_value.get("authority_commit") != validated.authority["overlay"]["expected_parent"] \
            or receipt_value.get("authority_sha256") != bound["package_authority_sha256"] \
            or receipt_value.get("runtime_sha256") != validated.runtime_sha256 \
            or receipt_value.get("wheelhouse_sha256") != validated.wheelhouse_sha256 \
            or not _is_sha(receipt_value.get("authority_sha256")) \
            or not _is_sha(receipt_value.get("claim_sha256")) \
            or not _is_sha(receipt_value.get("request_record_sha256")) \
            or HEX32.fullmatch(str(receipt_value.get("attempt_id"))) is None:
        raise FormalExecutionError("package receipt is not accepted")
    if receipt_value["aggregate_core_sha256"] != _sha(
            canonical_bytes(receipt_value["aggregate_core"])):
        raise FormalExecutionError("package receipt aggregate-core hash differs")
    _raw, package_value = strict_json(aggregate)
    _validate_package_gate(package_value, wheel)
    core = receipt_value.get("aggregate_core")
    if type(core) is not dict or core.get("gate", {}).get("aggregate") != bound["aggregate"] \
            or core.get("gate", {}).get("wheel") != bound["wheel"]:
        raise FormalExecutionError("package receipt does not bind aggregate and wheel")


def _revalidate_inputs(validated: ValidatedAuthority, repository: Path,
                       wheelhouse: Path, receipt: Path | None,
                       aggregate: Path | None, wheel: Path | None) -> None:
    runtime = runtime_identity()
    if _sha(canonical_bytes(runtime)) != validated.runtime_sha256 \
            or wheelhouse_identity(wheelhouse)["sha256"] != validated.wheelhouse_sha256:
        raise FormalExecutionError("frozen runtime or wheelhouse changed")
    _validate_git_chain(repository, validated)
    _validate_package_inputs(validated, receipt, aggregate, wheel)


def _within(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=True))
    except ValueError:
        return False
    return True


def _require_external_paths(repository: Path, wheelhouse: Path, registry: Path,
                            work_root: Path, output: Path) -> None:
    repository = repository.resolve(strict=True)
    wheelhouse = wheelhouse.resolve(strict=True)
    registry = registry.resolve(strict=True)
    for path in (registry, work_root, output):
        if _within(path, repository) or _within(path, wheelhouse):
            raise FormalExecutionError("formal state and output paths must be external")
    if _within(work_root, registry) or _within(output, registry):
        raise FormalExecutionError("work and canonical output must be outside registry")


def _validate_package_gate(value: Any, wheel: Path | None = None) -> None:
    keys = {"candidate_commit", "candidate_tree", "canonical_run_count",
            "correctness_record_sha256", "correctness_records_byte_identical",
            "formulation_id", "installed_runner_sha256", "package_gate_passed",
            "process_containment", "schema", "selector", "wheel"}
    if type(value) is not dict or set(value) != keys or value.get("schema") != PACKAGE_GATE_SCHEMA \
            or value.get("candidate_commit") != CANDIDATE_COMMIT \
            or value.get("candidate_tree") != CANDIDATE_TREE \
            or value.get("formulation_id") != FORMULATION_ID \
            or value.get("selector") != "ge-beam3" \
            or value.get("package_gate_passed") is not True \
            or value.get("canonical_run_count") != 2 \
            or value.get("correctness_records_byte_identical") is not True \
            or value.get("process_containment") != "WINDOWS_JOB_OBJECT_SUSPENDED_ASSIGN_V1" \
            or not _is_sha(value.get("correctness_record_sha256")) \
            or value.get("installed_runner_sha256") != GATE_SHA256:
        raise FormalExecutionError("package gate aggregate is not accepted")
    wheel_record = value.get("wheel")
    if type(wheel_record) is not dict or set(wheel_record) != {"bytes", "filename", "sha256"} \
            or type(wheel_record["bytes"]) is not int or wheel_record["bytes"] <= 0 \
            or type(wheel_record["filename"]) is not str \
            or Path(wheel_record["filename"]).name != wheel_record["filename"] \
            or not wheel_record["filename"].endswith(".whl") \
            or not _is_sha(wheel_record["sha256"]):
        raise FormalExecutionError("package gate wheel identity is malformed")
    if wheel is not None and file_identity(wheel) != wheel_record:
        raise FormalExecutionError("package wheel differs from aggregate")


def _validate_performance_gate(value: Any) -> bool:
    keys = {"all_existing_paths_pass", "base_commit", "base_wheel", "candidate_commit",
            "candidate_tree", "candidate_wheel", "families", "ge_beam3_speed_gate",
            "installed_runner_sha256", "order_sha256", "package_aggregate_sha256",
            "pair_count", "performance_diagnostics_sha256", "process_containment",
            "raw_record_count", "raw_record_graph_sha256", "schema",
            "warmup_count_per_role"}
    if type(value) is not dict or set(value) != keys or value.get("schema") != PERFORMANCE_GATE_SCHEMA \
            or value.get("candidate_commit") != CANDIDATE_COMMIT \
            or value.get("candidate_tree") != CANDIDATE_TREE \
            or value.get("pair_count") != 11 or value.get("warmup_count_per_role") != 1 \
            or value.get("ge_beam3_speed_gate") != "NONE" \
            or value.get("base_commit") != "e31c9e292a2fc9f6b57472bb8c5b90919a535492" \
            or value.get("process_containment") != "WINDOWS_JOB_OBJECT_SUSPENDED_ASSIGN_V1" \
            or value.get("raw_record_count") != 22 \
            or value.get("installed_runner_sha256") != GATE_SHA256 \
            or value.get("order_sha256") != "F80E4B923BB150F580F4774620C39E2CCF1B0AF02CCB2F462E0C06E119044B2D" \
            or type(value.get("all_existing_paths_pass")) is not bool:
        raise FormalExecutionError("performance gate aggregate is malformed")
    for key in ("installed_runner_sha256", "order_sha256", "package_aggregate_sha256",
                "performance_diagnostics_sha256", "raw_record_graph_sha256"):
        if not _is_sha(value[key]):
            raise FormalExecutionError("performance aggregate hash is malformed")
    for key in ("base_wheel", "candidate_wheel"):
        row = value[key]
        if type(row) is not dict or set(row) != {"bytes", "filename", "sha256"} \
                or type(row["bytes"]) is not int or row["bytes"] <= 0 \
                or type(row["filename"]) is not str or not row["filename"].endswith(".whl") \
                or Path(row["filename"]).name != row["filename"] or not _is_sha(row["sha256"]):
            raise FormalExecutionError("performance wheel identity is malformed")
    families = value["families"]
    if type(families) is not dict or set(families) != {"B2", "B3"}:
        raise FormalExecutionError("performance family inventory differs")
    computed = True
    for family in families.values():
        if type(family) is not dict or set(family) != {
            "all_operations_pass", "maximum_median_ratio", "operations", "ratios", "schema"
        } or family["schema"] != PERFORMANCE_GATE_SCHEMA \
                or family["maximum_median_ratio"] != "1.05" \
                or family["operations"] != ["CONSTRUCTION", "STIFFNESS", "INTERNAL_FORCE",
                                             "ASSEMBLY", "SOLVE", "RECOVERY", "RESTART"] \
                or type(family["all_operations_pass"]) is not bool:
            raise FormalExecutionError("performance family record differs")
        if type(family["ratios"]) is not dict or set(family["ratios"]) != set(family["operations"]):
            raise FormalExecutionError("performance ratio inventory differs")
        passed = True
        for ratio in family["ratios"].values():
            if type(ratio) is not str or re.fullmatch(r"[0-9]+\.[0-9]{12}", ratio) is None:
                raise FormalExecutionError("performance ratio is malformed")
            try:
                passed = passed and Decimal(ratio) <= Decimal("1.05")
            except InvalidOperation as exc:
                raise FormalExecutionError("performance ratio is malformed") from exc
        if family["all_operations_pass"] is not passed:
            raise FormalExecutionError("performance family adjudication differs")
        computed = computed and passed
    if value["all_existing_paths_pass"] is not computed:
        raise FormalExecutionError("performance terminal predicate differs")
    return value["all_existing_paths_pass"]


def _gate_evidence(mode: str, gate_root: Path) -> tuple[dict[str, Any], str]:
    aggregate = gate_root / ("package-aggregate.json" if mode == "package"
                             else "performance-aggregate.json")
    raw, value = strict_json(aggregate)
    identity = {"bytes": len(raw), "filename": aggregate.name, "sha256": _sha(raw)}
    if mode == "package":
        wheel_files = sorted((gate_root / "wheel").glob("*.whl"))
        if len(wheel_files) != 1:
            raise FormalExecutionError("package gate did not retain one wheel")
        _validate_package_gate(value, wheel_files[0])
        return {"aggregate": identity, "wheel": file_identity(wheel_files[0])}, PACKAGE_ACCEPTED
    passed = _validate_performance_gate(value)
    return {"aggregate": identity, "wheel": None}, TERMINAL_GO if passed else TERMINAL_PERFORMANCE


def _diagnostic_artifacts(work_root: Path, mode: str) -> list[dict[str, Any]]:
    candidates = [work_root / "formal-gate.log"]
    gate_root = work_root / "gate"
    candidates.append(gate_root / ("package-aggregate.json" if mode == "package"
                                   else "performance-aggregate.json"))
    if gate_root.exists():
        candidates.extend(sorted(gate_root.rglob("*.whl")))
    rows = []
    seen: set[Path] = set()
    for path in candidates:
        if path in seen or not _is_plain_file(path):
            continue
        seen.add(path)
        identity = _artifact_identity(path)
        rows.append({**identity, "kind": "LOG" if path.suffix == ".log" else
                     "WHEEL" if path.suffix == ".whl" else "PARTIAL_OR_FINAL_AGGREGATE"})
    return sorted(rows, key=lambda row: (row["kind"], row["filename"], row["sha256"]))


def _publish(claim: Claim, validated: ValidatedAuthority, core: dict[str, Any], output: Path) -> dict[str, Any]:
    _verify_claim(claim)
    receipt = {
        "aggregate_core": core, "aggregate_core_sha256": _sha(canonical_bytes(core)),
        "attempt_id": validated.authority["request"]["attempt_id"],
        "authority_commit": validated.authority_commit,
        "authority_sha256": validated.authority_identity["sha256"],
        "claim_sha256": _sha(claim.claim_raw),
        "request_record_sha256": validated.authority["request"]["record_sha256"],
        "request_id": validated.authority["request"]["request_id"],
        "runtime_sha256": validated.runtime_sha256, "schema": RECEIPT_SCHEMA,
        "terminal": core["terminal"], "wheelhouse_sha256": validated.wheelhouse_sha256,
    }
    receipt_raw = canonical_bytes(receipt)
    _fsync_exclusive(claim.receipt_path, receipt_raw)
    result = dict(core)
    result["consumption"] = {
        "attempt_claim_sha256": _sha(claim.claim_raw),
        "receipt_sha256": _sha(receipt_raw),
        "request_claim_sha256": _sha(claim.claim_raw),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    pending = output.with_name(f".{output.name}.{validated.authority['request']['attempt_id']}.pending")
    _fsync_exclusive(pending, canonical_bytes(result))
    os.replace(pending, output)
    return result


def recover_publication(validated: ValidatedAuthority, registry: Path,
                        output: Path) -> dict[str, Any] | None:
    request = validated.authority["request"]
    registry = registry.resolve(strict=True)
    request_path = registry / "claims" / f"{request['request_id']}.json"
    attempt_path = registry / "attempts" / f"{request['attempt_id']}.json"
    receipt_path = registry / "receipts" / f"{request['request_id']}.json"
    if not receipt_path.exists():
        if output.exists():
            raise FormalExecutionError("canonical output exists without an immutable receipt")
        return None
    receipt_raw, receipt = strict_json(receipt_path)
    if set(receipt) != {"aggregate_core", "aggregate_core_sha256", "attempt_id",
                        "authority_commit", "authority_sha256", "claim_sha256",
                        "request_id", "request_record_sha256", "runtime_sha256", "schema", "terminal",
                        "wheelhouse_sha256"} \
            or receipt["schema"] != RECEIPT_SCHEMA \
            or receipt["request_id"] != request["request_id"] \
            or receipt["attempt_id"] != request["attempt_id"] \
            or receipt["authority_commit"] != validated.authority_commit \
            or receipt["authority_sha256"] != validated.authority_identity["sha256"] \
            or receipt["request_record_sha256"] != request["record_sha256"] \
            or receipt["runtime_sha256"] != validated.runtime_sha256 \
            or receipt["wheelhouse_sha256"] != validated.wheelhouse_sha256:
        raise FormalExecutionError("immutable receipt differs")
    claim_raw = _regular_bytes(request_path)
    claim = _strict_json_bytes(claim_raw, "claim")
    expected_claim = {
        "attempt_id": request["attempt_id"], "authority_commit": validated.authority_commit,
        "authority_sha256": validated.authority_identity["sha256"], "mode": validated.mode,
        "request_id": request["request_id"], "request_record_sha256": request["record_sha256"],
        "runtime_sha256": validated.runtime_sha256, "schema": CLAIM_SCHEMA,
        "wheelhouse_sha256": validated.wheelhouse_sha256,
    }
    if claim != expected_claim or claim_raw != _regular_bytes(attempt_path) \
            or _sha(claim_raw) != receipt["claim_sha256"]:
        raise FormalExecutionError("receipt claim binding differs")
    if _sha(_regular_bytes(registry / "requests" / f"{request['request_id']}.json")) \
            != receipt["request_record_sha256"]:
        raise FormalExecutionError("external request changed")
    core = receipt["aggregate_core"]
    if receipt["aggregate_core_sha256"] != _sha(canonical_bytes(core)) \
            or core.get("terminal") != receipt["terminal"]:
        raise FormalExecutionError("receipt aggregate binding differs")
    result = dict(core)
    result["consumption"] = {
        "attempt_claim_sha256": _sha(claim_raw), "receipt_sha256": _sha(receipt_raw),
        "request_claim_sha256": _sha(claim_raw),
    }
    raw = canonical_bytes(result)
    if output.exists():
        if _regular_bytes(output) != raw:
            raise FormalExecutionError("canonical output differs from immutable receipt")
        return result
    output.parent.mkdir(parents=True, exist_ok=True)
    pending = output.with_name(f".{output.name}.{request['attempt_id']}.pending")
    if pending.exists():
        if _regular_bytes(pending) != raw:
            raise FormalExecutionError("pending publication differs from immutable receipt")
    else:
        _fsync_exclusive(pending, raw)
    os.replace(pending, output)
    return result


def _validated_result(result_path: Path, receipt_path: Path, mode: str) -> tuple[
        dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    result_raw, result = strict_json(result_path)
    receipt_raw, receipt = strict_json(receipt_path)
    result_keys = {"authority", "candidate", "consumption", "diagnostic_artifacts",
                   "gate", "mode", "request_id", "runtime_sha256", "schema",
                   "terminal", "wheelhouse_sha256"}
    receipt_keys = {"aggregate_core", "aggregate_core_sha256", "attempt_id",
                    "authority_commit", "authority_sha256", "claim_sha256",
                    "request_id", "request_record_sha256", "runtime_sha256", "schema", "terminal",
                    "wheelhouse_sha256"}
    if set(result) != result_keys or result["schema"] != RESULT_SCHEMA \
            or result["mode"] != mode or result["candidate"] != {
                "commit": CANDIDATE_COMMIT, "tree": CANDIDATE_TREE}:
        raise FormalExecutionError("formal result schema or provenance differs")
    if set(receipt) != receipt_keys or receipt["schema"] != RECEIPT_SCHEMA:
        raise FormalExecutionError("formal receipt schema differs")
    authority = result["authority"]
    if type(authority) is not dict or set(authority) != {"commit", "sha256", "tree"} \
            or not _is_oid(authority["commit"]) or not _is_oid(authority["tree"]) \
            or not _is_sha(authority["sha256"]) \
            or HEX32.fullmatch(str(result["request_id"])) is None \
            or not _is_sha(result["runtime_sha256"]) \
            or result["wheelhouse_sha256"] != WHEELHOUSE_SHA256:
        raise FormalExecutionError("formal result authority/request binding differs")
    gate = result["gate"]
    if type(gate) is not dict or set(gate) != {"aggregate", "wheel"}:
        raise FormalExecutionError("formal result gate binding differs")
    for value in gate.values():
        if value is not None and (type(value) is not dict or set(value) != {
                "bytes", "filename", "sha256"} or type(value["bytes"]) is not int
                or value["bytes"] <= 0 or type(value["filename"]) is not str
                or Path(value["filename"]).name != value["filename"]
                or not _is_sha(value["sha256"])):
            raise FormalExecutionError("formal result gate artifact is malformed")
    diagnostics = result["diagnostic_artifacts"]
    if type(diagnostics) is not list:
        raise FormalExecutionError("formal diagnostic inventory is malformed")
    for row in diagnostics:
        if type(row) is not dict or set(row) != {"bytes", "filename", "kind", "sha256"} \
                or type(row["bytes"]) is not int or row["bytes"] < 0 \
                or type(row["filename"]) is not str or Path(row["filename"]).name != row["filename"] \
                or row["kind"] not in {"LOG", "PARTIAL_OR_FINAL_AGGREGATE", "WHEEL"} \
                or not _is_sha(row["sha256"]):
            raise FormalExecutionError("formal diagnostic artifact is malformed")
    allowed = ({PACKAGE_ACCEPTED, TERMINAL_PACKAGE_NO_GO, TERMINAL_BLOCKED_PROCESS,
                TERMINAL_BLOCKED_AUTHORITY} if mode == "package" else
               {TERMINAL_GO, TERMINAL_PERFORMANCE, TERMINAL_BLOCKED_PROCESS,
                TERMINAL_BLOCKED_AUTHORITY})
    if result["terminal"] not in allowed \
            or (result["terminal"] in {TERMINAL_BLOCKED_PROCESS, TERMINAL_BLOCKED_AUTHORITY}
                and gate != {"aggregate": None, "wheel": None}) \
            or (result["terminal"] not in {TERMINAL_BLOCKED_PROCESS, TERMINAL_BLOCKED_AUTHORITY}
                and gate["aggregate"] is None):
        raise FormalExecutionError("formal result terminal/gate relation differs")
    consumption = result["consumption"]
    if type(consumption) is not dict or set(consumption) != {
            "attempt_claim_sha256", "receipt_sha256", "request_claim_sha256"} \
            or any(not _is_sha(value) for value in consumption.values()):
        raise FormalExecutionError("formal consumption binding differs")
    for key in ("aggregate_core_sha256", "authority_sha256", "claim_sha256",
                "request_record_sha256", "runtime_sha256", "wheelhouse_sha256"):
        if not _is_sha(receipt.get(key)):
            raise FormalExecutionError("formal receipt hash is malformed")
    if HEX32.fullmatch(str(receipt.get("attempt_id"))) is None \
            or HEX32.fullmatch(str(receipt.get("request_id"))) is None:
        raise FormalExecutionError("formal receipt ID is malformed")
    core = dict(result)
    consumption = core.pop("consumption")
    if receipt["aggregate_core"] != core \
            or receipt["aggregate_core_sha256"] != _sha(canonical_bytes(core)) \
            or receipt["request_id"] != result["request_id"] \
            or receipt["terminal"] != result["terminal"] \
            or receipt["authority_commit"] != result["authority"]["commit"] \
            or receipt["authority_sha256"] != result["authority"]["sha256"] \
            or receipt["runtime_sha256"] != result["runtime_sha256"] \
            or receipt["wheelhouse_sha256"] != result["wheelhouse_sha256"] \
            or consumption != {
                "attempt_claim_sha256": receipt["claim_sha256"],
                "receipt_sha256": _sha(receipt_raw),
                "request_claim_sha256": receipt["claim_sha256"],
            }:
        raise FormalExecutionError("formal result and receipt disagree")
    return result, receipt, _artifact_identity(result_path), _artifact_identity(receipt_path)


def _committed_authority(repository: Path, commit: str, mode: str) -> ValidatedAuthority:
    authority_relative, review_relative = AUTHORITY_PATHS[mode]
    authority_raw = _git(repository, "cat-file", "blob", f"{commit}:{authority_relative}", binary=True)
    review_raw = _git(repository, "cat-file", "blob", f"{commit}:{review_relative}", binary=True)
    assert isinstance(authority_raw, bytes) and isinstance(review_raw, bytes)
    authority = _strict_json_bytes(authority_raw, authority_relative)
    review = _strict_json_bytes(review_raw, review_relative)
    runtime = runtime_identity()
    wheelhouse = wheelhouse_identity(Path(authority.get("locations", {}).get("wheelhouse", "")))
    _validate_authority(authority, mode=mode, runtime=runtime, wheelhouse=wheelhouse)
    authority_id = {"bytes": len(authority_raw), "filename": Path(authority_relative).name,
                    "sha256": _sha(authority_raw)}
    review_id = {"bytes": len(review_raw), "filename": Path(review_relative).name,
                 "sha256": _sha(review_raw)}
    _validate_review(review, authority_id, mode)
    validated = ValidatedAuthority(
        mode, authority, authority_id, commit,
        str(_git(repository, "rev-parse", f"{commit}^{{tree}}")), review_id,
        _sha(canonical_bytes(runtime)), wheelhouse["sha256"],
    )
    _validate_git_chain(repository, validated, commit=commit)
    return validated


def _validate_closeout_chain(repository: Path, package: Mapping[str, Any],
                             package_receipt: Mapping[str, Any],
                             performance: Mapping[str, Any] | None,
                             performance_receipt: Mapping[str, Any] | None) -> tuple[
                                 ValidatedAuthority, ValidatedAuthority | None]:
    repository = repository.resolve(strict=True)
    _require_unmodified_git_graph(repository)
    package_authority = _committed_authority(repository, package["authority"]["commit"], "package")
    if package_authority.authority_identity["sha256"] != package["authority"]["sha256"] \
            or package_authority.authority_tree != package["authority"]["tree"] \
            or package_authority.authority["request"]["request_id"] != package["request_id"] \
            or package_authority.authority["request"]["attempt_id"] != package_receipt["attempt_id"] \
            or package_authority.authority["request"]["record_sha256"] != package_receipt["request_record_sha256"]:
        raise FormalExecutionError("package authority/result/request provenance differs")
    if performance is None:
        if _git(repository, "rev-parse", "HEAD") != package_authority.authority_commit:
            raise FormalExecutionError("package-only closeout HEAD differs")
        return package_authority, None
    performance_authority = _committed_authority(
        repository, performance["authority"]["commit"], "performance")
    if performance_authority.authority["overlay"]["expected_parent"] != package_authority.authority_commit \
            or performance_authority.authority_identity["sha256"] != performance["authority"]["sha256"] \
            or performance_authority.authority_tree != performance["authority"]["tree"] \
            or performance_authority.authority["request"]["request_id"] != performance["request_id"] \
            or performance_authority.authority["request"]["attempt_id"] != performance_receipt["attempt_id"] \
            or performance_authority.authority["request"]["record_sha256"] != performance_receipt["request_record_sha256"] \
            or _git(repository, "rev-parse", "HEAD") != performance_authority.authority_commit:
        raise FormalExecutionError("performance authority/result/request provenance differs")
    return package_authority, performance_authority


def _validate_registry_provenance(validated: ValidatedAuthority,
                                  result_path: Path, receipt_path: Path,
                                  result: Mapping[str, Any],
                                  receipt: Mapping[str, Any]) -> None:
    locations = validated.authority["locations"]
    registry = Path(locations["registry"]).resolve(strict=True)
    request = validated.authority["request"]
    expected_receipt = registry / "receipts" / f"{request['request_id']}.json"
    if result_path.resolve(strict=True) != Path(locations["output"]).resolve(strict=True) \
            or receipt_path.resolve(strict=True) != expected_receipt.resolve(strict=True):
        raise FormalExecutionError("formal result/receipt path differs from authority")
    _validate_request(validated, registry)
    claim_path = registry / "claims" / f"{request['request_id']}.json"
    attempt_path = registry / "attempts" / f"{request['attempt_id']}.json"
    claim_raw, claim = strict_json(claim_path)
    if claim_raw != _regular_bytes(attempt_path) \
            or set(claim) != {"attempt_id", "authority_commit", "authority_sha256", "mode",
                              "request_id", "request_record_sha256", "runtime_sha256",
                              "schema", "wheelhouse_sha256"} \
            or claim != {
                "attempt_id": request["attempt_id"],
                "authority_commit": validated.authority_commit,
                "authority_sha256": validated.authority_identity["sha256"],
                "mode": validated.mode, "request_id": request["request_id"],
                "request_record_sha256": request["record_sha256"],
                "runtime_sha256": validated.runtime_sha256, "schema": CLAIM_SCHEMA,
                "wheelhouse_sha256": validated.wheelhouse_sha256,
            } or receipt["claim_sha256"] != _sha(claim_raw) \
            or result["request_id"] != request["request_id"]:
        raise FormalExecutionError("formal registry claim provenance differs")


def synthesize_closeout(repository: Path, package_result: Path, package_receipt: Path,
                        performance_result: Path | None, performance_receipt: Path | None,
                        package_aggregate: Path | None, performance_aggregate: Path | None,
                        candidate_wheel: Path | None, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FormalExecutionError("closeout output already exists")
    package, _package_receipt, package_result_id, package_receipt_id = _validated_result(
        package_result, package_receipt, "package")
    if package["terminal"] in {TERMINAL_BLOCKED_AUTHORITY, TERMINAL_BLOCKED_PROCESS,
                                TERMINAL_PACKAGE_NO_GO}:
        if any(item is not None for item in (performance_result, performance_receipt,
                                             performance_aggregate)):
            raise FormalExecutionError("package-only BLOCKED closeout forbids A2 inputs")
        package_authority, _none = _validate_closeout_chain(
            repository, package, _package_receipt, None, None)
        _validate_registry_provenance(package_authority, package_result,
                                      package_receipt, package, _package_receipt)
        evidence = {
            "authorities": {"package": {"commit": package_authority.authority_commit,
                                           "review_sha256": package_authority.review_identity["sha256"],
                                           "sha256": package_authority.authority_identity["sha256"]},
                            "performance": None},
            "candidate": {"candidate_id": CANDIDATE_ID, "commit": CANDIDATE_COMMIT,
                          "formulation_id": FORMULATION_ID, "tree": CANDIDATE_TREE},
            "inputs": {"candidate_wheel": None, "package_aggregate": None,
                       "package_receipt": package_receipt_id,
                       "package_result": package_result_id,
                       "performance_aggregate": None, "performance_receipt": None,
                       "performance_result": None},
            "package_terminal": package["terminal"], "performance_terminal": None,
            "requests": {"package": {"attempt_id": _package_receipt["attempt_id"],
                                        "request_id": package["request_id"]},
                         "performance": None},
            "runtime_sha256": package["runtime_sha256"],
            "production_boundary": {
                "activation_authorized": False, "default_change_authorized": False,
                "ecosystem_exposure_authorized": False, "publication_authorized": False,
                "qualified_q4_unchanged": True, "qualified_s3_v2d_unchanged": True,
            },
            "schema": CLOSEOUT_SCHEMA, "study_id": STUDY_ID,
            "terminal": (TERMINAL_PACKAGE_NO_GO if package["terminal"] == TERMINAL_PACKAGE_NO_GO
                         else TERMINAL_BLOCKED_PROCESS),
            "terminal_precedence": [TERMINAL_BLOCKED_AUTHORITY, TERMINAL_BLOCKED_PROCESS,
                                    "NO_GO_GE_BEAM3_P3_SELECTOR_OR_SERIALIZATION",
                                    "NO_GO_GE_BEAM3_P3_LINEAR_INTEGRATION",
                                    TERMINAL_PACKAGE_NO_GO, TERMINAL_PERFORMANCE, TERMINAL_GO],
            "wheelhouse_sha256": package["wheelhouse_sha256"],
        }
        _fsync_exclusive(output, canonical_bytes(evidence))
        return evidence
    if any(item is None for item in (performance_result, performance_receipt,
                                     package_aggregate, candidate_wheel)):
        raise FormalExecutionError("accepted package closeout requires complete A2 inputs")
    performance, _performance_receipt, performance_result_id, performance_receipt_id = \
        _validated_result(performance_result, performance_receipt, "performance")
    package_authority, performance_authority = _validate_closeout_chain(
        repository, package, _package_receipt, performance, _performance_receipt)
    _validate_registry_provenance(package_authority, package_result,
                                  package_receipt, package, _package_receipt)
    _validate_registry_provenance(performance_authority, performance_result,
                                  performance_receipt, performance, _performance_receipt)
    _validate_registered_execution(
        performance_authority, Path(performance_authority.authority["locations"]["registry"]),
        Path(performance_authority.authority["locations"]["work_root"]), performance_result,
        package_receipt, package_aggregate, candidate_wheel)
    _validate_package_inputs(performance_authority, package_receipt,
                             package_aggregate, candidate_wheel)
    package_raw, package_gate = strict_json(package_aggregate)
    _validate_package_gate(package_gate, candidate_wheel)
    package_gate_id = _artifact_identity(package_aggregate)
    wheel_id = file_identity(candidate_wheel)
    if package["gate"] != {"aggregate": package_gate_id, "wheel": wheel_id} \
            or package["runtime_sha256"] != performance["runtime_sha256"] \
            or package["wheelhouse_sha256"] != performance["wheelhouse_sha256"] \
            or package["request_id"] == performance["request_id"]:
        raise FormalExecutionError("formal package/performance provenance differs")
    terminal = ""
    if performance["terminal"] in {TERMINAL_BLOCKED_AUTHORITY, TERMINAL_BLOCKED_PROCESS}:
        if performance_aggregate is not None \
                or performance["gate"] != {"aggregate": None, "wheel": None}:
            raise FormalExecutionError("BLOCKED performance must not claim an aggregate")
        performance_gate_id = None
        performance_passed = False
        terminal = TERMINAL_BLOCKED_PROCESS
    else:
        if performance_aggregate is None:
            raise FormalExecutionError("classifying performance result requires its aggregate")
        performance_raw, performance_gate = strict_json(performance_aggregate)
        performance_passed = _validate_performance_gate(performance_gate)
        performance_gate_id = _artifact_identity(performance_aggregate)
        if performance["gate"] != {"aggregate": performance_gate_id, "wheel": None} \
                or performance_gate.get("package_aggregate_sha256") != _sha(package_raw) \
                or performance_gate.get("candidate_wheel") != wheel_id:
            raise FormalExecutionError("performance aggregate provenance differs")
    if package["terminal"] != PACKAGE_ACCEPTED:
        raise FormalExecutionError("package terminal is not recognized")
    if terminal == TERMINAL_BLOCKED_PROCESS:
        pass
    elif performance["terminal"] == TERMINAL_PERFORMANCE and not performance_passed:
        terminal = TERMINAL_PERFORMANCE
    elif performance["terminal"] == TERMINAL_GO and performance_passed:
        terminal = TERMINAL_GO
    else:
        raise FormalExecutionError("performance terminal contradicts gate evidence")
    evidence = {
        "authorities": {
            "package": {"commit": package_authority.authority_commit,
                        "review_sha256": package_authority.review_identity["sha256"],
                        "sha256": package_authority.authority_identity["sha256"]},
            "performance": {"commit": performance_authority.authority_commit,
                            "review_sha256": performance_authority.review_identity["sha256"],
                            "sha256": performance_authority.authority_identity["sha256"]},
        },
        "candidate": {"candidate_id": CANDIDATE_ID, "commit": CANDIDATE_COMMIT,
                      "formulation_id": FORMULATION_ID, "tree": CANDIDATE_TREE},
        "inputs": {
            "candidate_wheel": wheel_id,
            "package_aggregate": package_gate_id, "package_receipt": package_receipt_id,
            "package_result": package_result_id,
            "performance_aggregate": performance_gate_id,
            "performance_receipt": performance_receipt_id,
            "performance_result": performance_result_id,
        },
        "package_terminal": package["terminal"],
        "performance_terminal": performance["terminal"],
        "requests": {
            "package": {"attempt_id": _package_receipt["attempt_id"],
                        "request_id": package["request_id"]},
            "performance": {"attempt_id": _performance_receipt["attempt_id"],
                            "request_id": performance["request_id"]},
        },
        "runtime_sha256": package["runtime_sha256"],
        "production_boundary": {
            "activation_authorized": False, "default_change_authorized": False,
            "ecosystem_exposure_authorized": False, "publication_authorized": False,
            "qualified_q4_unchanged": True, "qualified_s3_v2d_unchanged": True,
        },
        "schema": CLOSEOUT_SCHEMA, "study_id": STUDY_ID, "terminal": terminal,
        "terminal_precedence": [TERMINAL_BLOCKED_AUTHORITY, TERMINAL_BLOCKED_PROCESS,
                                "NO_GO_GE_BEAM3_P3_SELECTOR_OR_SERIALIZATION",
                                "NO_GO_GE_BEAM3_P3_LINEAR_INTEGRATION",
                                TERMINAL_PACKAGE_NO_GO, TERMINAL_PERFORMANCE, TERMINAL_GO],
        "wheelhouse_sha256": package["wheelhouse_sha256"],
    }
    _fsync_exclusive(output, canonical_bytes(evidence))
    return evidence


def execute(repository: Path, authority_path: Path, review_path: Path, wheelhouse: Path,
            registry: Path, work_root: Path, output: Path, *, mode: str,
            package_receipt: Path | None = None, package_aggregate: Path | None = None,
            candidate_wheel: Path | None = None) -> dict[str, Any]:
    if os.name != "nt":
        raise FormalExecutionError("formal P3 execution requires Windows")
    _require_external_paths(repository, wheelhouse, registry, work_root, output)
    first, check_one = authority_check(repository, authority_path, review_path, wheelhouse, mode=mode)
    second, check_two = authority_check(repository, authority_path, review_path, wheelhouse, mode=mode)
    if first != second or canonical_bytes(check_one) != canonical_bytes(check_two):
        raise FormalExecutionError("two authority checks disagree")
    _validate_registered_execution(first, registry, work_root, output, package_receipt,
                                   package_aggregate, candidate_wheel)
    _validate_package_inputs(first, package_receipt, package_aggregate, candidate_wheel)
    _validate_request(first, registry)
    recovered = recover_publication(first, registry, output)
    if recovered is not None:
        return recovered
    if work_root.exists() or output.exists():
        raise FormalExecutionError("formal work/output path already exists")
    claim = _acquire_claim(first, registry)
    try:
        core = {
            "authority": {"commit": first.authority_commit,
                          "sha256": first.authority_identity["sha256"],
                          "tree": first.authority_tree},
            "candidate": {"commit": CANDIDATE_COMMIT, "tree": CANDIDATE_TREE},
            "gate": {"aggregate": None, "wheel": None}, "mode": mode,
            "diagnostic_artifacts": [],
            "request_id": first.authority["request"]["request_id"],
            "runtime_sha256": first.runtime_sha256, "schema": RESULT_SCHEMA,
            "terminal": TERMINAL_BLOCKED_PROCESS,
            "wheelhouse_sha256": first.wheelhouse_sha256,
        }
        try:
            work_root.mkdir(parents=True, exist_ok=False)
            materialized = _materialize(repository, work_root / "candidate")
            _revalidate_inputs(first, repository, wheelhouse, package_receipt,
                               package_aggregate, candidate_wheel)
            gate_root = work_root / "gate"
            environment = _child_environment(wheelhouse, work_root / "temp")
            command = _gate_command(mode, materialized, gate_root,
                                    package_aggregate, candidate_wheel)
            process = _run_bounded(command, cwd=work_root, environment=environment,
                                   log_path=work_root / "formal-gate.log")
            if process.returncode != 0 or process.forced_reason is not None:
                raise FormalExecutionError(process.forced_reason or "FORMAL_GATE_NONZERO_EXIT")
            _revalidate_inputs(first, repository, wheelhouse, package_receipt,
                               package_aggregate, candidate_wheel)
            evidence, terminal = _gate_evidence(mode, gate_root)
            core["gate"] = evidence
            core["terminal"] = terminal
        except BaseException:
            # A claimed attempt is terminal and cannot be retried.  Raw diagnostics stay external.
            core["gate"] = {"aggregate": None, "wheel": None}
            core["terminal"] = TERMINAL_BLOCKED_PROCESS
        core["diagnostic_artifacts"] = _diagnostic_artifacts(work_root, mode)
        if core["terminal"] != TERMINAL_BLOCKED_PROCESS:
            try:
                _revalidate_inputs(first, repository, wheelhouse, package_receipt,
                                   package_aggregate, candidate_wheel)
            except BaseException:
                core["gate"] = {"aggregate": None, "wheel": None}
                core["terminal"] = TERMINAL_BLOCKED_PROCESS
        return _publish(claim, first, core, output)
    finally:
        _release_lock(claim)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--authority-check", action="store_true")
    action.add_argument("--execute", action="store_true")
    action.add_argument("--synthesize-closeout", action="store_true")
    parser.add_argument("--mode", choices=tuple(AUTHORITY_PATHS))
    parser.add_argument("--repository", type=Path)
    parser.add_argument("--authority", type=Path)
    parser.add_argument("--review", type=Path)
    parser.add_argument("--wheelhouse", type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--package-receipt", type=Path)
    parser.add_argument("--package-aggregate", type=Path)
    parser.add_argument("--candidate-wheel", type=Path)
    parser.add_argument("--package-result", type=Path)
    parser.add_argument("--performance-result", type=Path)
    parser.add_argument("--performance-receipt", type=Path)
    parser.add_argument("--performance-aggregate", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    supplied = list(sys.argv[1:] if argv is None else argv)
    args = _parser().parse_args(supplied)
    if args.synthesize_closeout:
        required = (args.repository, args.package_result, args.package_receipt, args.output)
        if any(item is None for item in required):
            raise FormalExecutionError("closeout synthesis inputs are incomplete")
        result = synthesize_closeout(
            args.repository, args.package_result, args.package_receipt, args.performance_result,
            args.performance_receipt, args.package_aggregate,
            args.performance_aggregate, args.candidate_wheel, args.output)
        sys.stdout.buffer.write(canonical_bytes(result))
        return 0
    if any(item is None for item in
           (args.mode, args.repository, args.authority, args.review, args.wheelhouse)):
        raise FormalExecutionError("authority operations require mode, repository, authority, review, and wheelhouse")
    if args.authority_check:
        _validated, check = authority_check(args.repository, args.authority, args.review,
                                            args.wheelhouse, mode=args.mode)
        sys.stdout.buffer.write(canonical_bytes(check))
        return 0
    if args.registry is None or args.work_root is None or args.output is None:
        raise FormalExecutionError("--execute requires --registry, --work-root, and --output")
    _raw, preliminary = strict_json(args.authority)
    actual_argv = [str(Path(sys.executable).resolve()), "-I", "-B",
                   str(Path(__file__).resolve()), *supplied]
    if preliminary.get("formal_argv") != actual_argv:
        raise FormalExecutionError("live formal argv differs from authority")
    if not sys.flags.isolated or not sys.flags.dont_write_bytecode:
        raise FormalExecutionError("formal executor requires Python -I -B")
    result = execute(args.repository, args.authority, args.review, args.wheelhouse,
                     args.registry, args.work_root, args.output, mode=args.mode,
                     package_receipt=args.package_receipt,
                     package_aggregate=args.package_aggregate,
                     candidate_wheel=args.candidate_wheel)
    sys.stdout.buffer.write(canonical_bytes(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
