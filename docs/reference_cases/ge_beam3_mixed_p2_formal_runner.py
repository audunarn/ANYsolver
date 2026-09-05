"""Bounded deterministic runner for the private GE Beam3 P2 parity gate.

The runner has deliberately narrow authority.  It executes seven frozen pytest
modules in isolated child processes and emits a path-free canonical summary.
Rehearsal output is nonclassifying.  Formal execution is impossible unless a
separately authored canonical authorization binds the exact Git-blob manifest.

This module never authors execution authority.  It coordinates an independently
checked raw proof in an external diagnostic directory and writes an exclusive
path-free aggregate; only stable IDs, counts, booleans, hashes, and enums enter
that aggregate.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import hashlib
from importlib import metadata as importlib_metadata
from importlib import util as importlib_util
import json
import os
from pathlib import Path
import platform
import runpy
import signal
import stat
import subprocess
import sys
import sysconfig
import time
from typing import Any, Callable, Iterable, Sequence

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


ROOT = Path(__file__).resolve().parents[2]
RUNNER_RELATIVE = "docs/reference_cases/ge_beam3_mixed_p2_formal_runner.py"
RUNNER_TEST_RELATIVE = "tests/test_ge_beam3_mixed_p2_formal_runner.py"
PRODUCER_RELATIVE = "docs/reference_cases/ge_beam3_mixed_p2_formal_producer.py"
CHECKER_RELATIVE = "docs/reference_cases/ge_beam3_mixed_p2_formal_checker.py"
PRODUCER_TEST_RELATIVE = "tests/test_ge_beam3_mixed_p2_formal_producer.py"
CHECKER_TEST_RELATIVE = "tests/test_ge_beam3_mixed_p2_formal_checker.py"

STUDY_ID = "study_ge_beam3.mixed_straight_solver_parity_v1"
CANDIDATE_ID = "CANDIDATE_GE_BEAM3_DC_MIXED_K1_MACRO_V2"
AGGREGATE_SCHEMA = "anysolver.ge-beam3-mixed-p2-formal-aggregate-v1"
WORKER_SCHEMA = "anysolver.ge-beam3-mixed-p2-pytest-worker-v1"
PROOF_SCHEMA = "anysolver.ge-beam3-mixed-p2-proof-v1"
CHECK_SCHEMA = "anysolver.ge-beam3-mixed-p2-check-v1"
AUTHORITY_CHECK_SCHEMA = "anysolver.ge-beam3-mixed-p2-authority-check-v1"
AUTHORIZATION_SCHEMA = "anysolver.ge-beam3-mixed-p2-execution-authorization-v1"
EXECUTION_REVIEW_SCHEMA = "anysolver.ge-beam3-mixed-p2-execution-review-v1"
REGISTRY_IDENTITY_SCHEMA = "anysolver.ge-beam3-mixed-p2-registry-identity-v1"
MATERIALIZATION_SCHEMA = "anysolver.ge-beam3-mixed-p2-materialization-v1"
CLAIM_SCHEMA = "anysolver.ge-beam3-mixed-p2-one-time-claim-v1"
RECEIPT_SCHEMA = "anysolver.ge-beam3-mixed-p2-terminal-receipt-v1"
TEST_DOUBLE_SCHEMA = "anysolver.ge-beam3-mixed-p2-nonclassifying-test-double-v1"
RUNTIME_IMPORT_AUDIT_SCHEMA = (
    "anysolver.ge-beam3-mixed-p2-runtime-import-audit-v1"
)

_ACTIVE_CLI_ARGV: tuple[str, ...] | None = None

REHEARSAL_MODE = "NONCLASSIFYING_REHEARSAL"
FORMAL_MODE = "FORMAL_TWO_CYCLE"
FORMAL_AUTHORIZATION_TERMINAL = "AUTHORIZED_GE_BEAM3_P2_FORMAL_EXECUTION"
AUTHORITY_CHECK_TERMINAL = "AUTHORITY_CHECK_ONLY_PASS"
AUTHORIZATION_SUBJECT = "docs: authorize GE Beam3 mixed P2 formal cycles"
AUTHORITY_RELATIVE_PATH = (
    "docs/reference_cases/ge_beam3_mixed_p2_execution_authority.json"
)
EXECUTION_REVIEW_RELATIVE_PATH = (
    "docs/reference_cases/ge_beam3_mixed_p2_execution_review.json"
)
AUTHORIZATION_PATHS = tuple(
    sorted((AUTHORITY_RELATIVE_PATH, EXECUTION_REVIEW_RELATIVE_PATH))
)
EXECUTION_REVIEW_VERDICT = "ACCEPT_GE_BEAM3_MIXED_P2_FORMAL_EXECUTION_NO_P0_P1"
EXECUTION_REVIEWER_INDEPENDENCE = {
    "authority_authorship": False,
    "harness_authorship": False,
    "review_method": "CANONICAL_GIT_BLOBS_RUNTIME_MANIFEST_AND_ONE_TIME_PROTOCOL",
    "role": "INDEPENDENT_GE_BEAM3_MIXED_P2_EXECUTION_REVIEWER",
}
REGISTRY_IDENTITY_NAME = "registry-identity.json"
RUNTIME_DISTRIBUTIONS = (
    ("NumPy", "numpy", "numpy"),
    ("SciPy", "scipy", "scipy"),
    ("Pytest", "pytest", "pytest"),
    ("threadpoolctl", "threadpoolctl", "threadpoolctl"),
    ("ANYmaterial", "ANYmaterial", "anymaterial"),
    ("ANYmesher", "ANYmesher", "anymesher"),
    ("ANYgeometry", "ANYgeometry", "anygeometry"),
    ("PyYAML", "PyYAML", "yaml"),
    ("charset-normalizer", "charset-normalizer", "charset_normalizer"),
    ("llvmlite", "llvmlite", "llvmlite"),
    ("numba", "numba", "numba"),
) + (
    (("pywin32", "pywin32", "win32api"),)
    if sys.platform == "win32"
    else ()
)

PREREGISTRATION_COMMIT = "448ae38cad85365f0058fca8174fb5a12aa57bbc"
RECOVERY_CORRECTION_COMMIT = "59c03266dae7d66daa2eb57e3041a511abc55d51"
RECOVERY_CORRECTION_TREE = "788bfb248766bb13ba98970e58747d334680b447"
IMPLEMENTATION_COMMIT = "dabead7253547f031293933a21dc41cd29fb70a9"
IMPLEMENTATION_TREE = "46c7d4018cd5cf4fd78e83ebb2f29fdab4ca2eab"
IMPLEMENTATION_REVIEW_COMMIT = "2bca66c4e535ce6d9f38913fcf1e70460367d875"
IMPLEMENTATION_REVIEW_TREE = "82637f39985f8d7bec7a7b9bc41deaed508ea833"
IMPLEMENTATION_REVIEW_RELATIVE = (
    "docs/reference_cases/ge_beam3_mixed_p2_implementation_review.json"
)
IMPLEMENTATION_REVIEW_BLOB_OID = "b20f4f23f74f04da34ec16c67f0a74fcc4e5849f"

RECOVERY_CORRECTION_PATHS = tuple(
    sorted(
        (
            "docs/agent_plans/GE_BEAM3_MIXED_P2_RECOVERY_CORRECTION.md",
            "docs/reference_cases/ge_beam3_mixed_p2_recovery_correction.json",
            "docs/reference_cases/ge_beam3_mixed_p2_recovery_correction_contract.json",
            "docs/reference_cases/ge_beam3_mixed_p2_recovery_correction_reference.py",
            "docs/reference_cases/ge_beam3_mixed_p2_recovery_correction_review.json",
            "tests/test_ge_beam3_mixed_p2_recovery_correction.py",
        )
    )
)
IMPLEMENTATION_PATHS = tuple(
    sorted(
        (
            "src/anysolver/ge_beam3_mixed_element.py",
            "src/anysolver/ge_beam3_mixed_state.py",
            "tests/test_ge_beam3_mixed_p2_load_mass_recovery.py",
            "tests/test_ge_beam3_mixed_p2_modal_buckling.py",
            "tests/test_ge_beam3_mixed_p2_solver_chart.py",
            "tests/test_ge_beam3_mixed_p2_state_restart.py",
        )
    )
)
IMPLEMENTATION_REVIEW_PATHS = (IMPLEMENTATION_REVIEW_RELATIVE,)
HARNESS_PATHS = tuple(
    sorted(
        (
            RUNNER_RELATIVE,
            RUNNER_TEST_RELATIVE,
            PRODUCER_RELATIVE,
            PRODUCER_TEST_RELATIVE,
            CHECKER_RELATIVE,
            CHECKER_TEST_RELATIVE,
        )
    )
)

PREREGISTRATION_INPUTS = (
    "docs/agent_plans/GE_BEAM3_MIXED_P2_SOLVER_PARITY_PLAN.md",
    "docs/reference_cases/ge_beam3_mixed_p2_baseline.json",
    "docs/reference_cases/ge_beam3_mixed_p2_cases.json",
    "docs/reference_cases/ge_beam3_mixed_p2_contract.json",
    "docs/reference_cases/ge_beam3_mixed_p2_independent_reference.py",
    "docs/reference_cases/ge_beam3_mixed_p2_plan_review.json",
    "docs/reference_cases/ge_beam3_mixed_p2_state_schema.json",
    "tests/test_ge_beam3_mixed_p2_preregistration.py",
)


@dataclass(frozen=True)
class TestSpec:
    test_id: str
    relative: str
    finding_group: str


FOCUSED_TESTS = (
    TestSpec(
        "PREREGISTRATION",
        "tests/test_ge_beam3_mixed_p2_preregistration.py",
        "BASELINE_OR_AUTHORITY",
    ),
    TestSpec(
        "RECOVERY_CORRECTION",
        "tests/test_ge_beam3_mixed_p2_recovery_correction.py",
        "BASELINE_OR_AUTHORITY",
    ),
    TestSpec(
        "SOLVER_CHART",
        "tests/test_ge_beam3_mixed_p2_solver_chart.py",
        "SOLVER_CHART_OR_STATE",
    ),
    TestSpec(
        "STATE_RESTART",
        "tests/test_ge_beam3_mixed_p2_state_restart.py",
        "SOLVER_CHART_OR_STATE",
    ),
    TestSpec(
        "LOAD_MASS_RECOVERY",
        "tests/test_ge_beam3_mixed_p2_load_mass_recovery.py",
        "LOAD_MASS_OR_RECOVERY",
    ),
    TestSpec(
        "MODAL_BUCKLING",
        "tests/test_ge_beam3_mixed_p2_modal_buckling.py",
        "MODAL_OR_BUCKLING",
    ),
    TestSpec(
        "ACCEPTED_STATIC_CORE",
        "tests/test_ge_beam3_mixed_core.py",
        "BASELINE_OR_AUTHORITY",
    ),
)
TEST_BY_ID = {spec.test_id: spec for spec in FOCUSED_TESTS}
if len(TEST_BY_ID) != len(FOCUSED_TESTS):  # pragma: no cover - source invariant
    raise RuntimeError("duplicate focused-test ID")

BOUND_PATHS = tuple(
    sorted(
        set(PREREGISTRATION_INPUTS)
        | set(RECOVERY_CORRECTION_PATHS)
        | set(IMPLEMENTATION_PATHS)
        | set(IMPLEMENTATION_REVIEW_PATHS)
        | set(HARNESS_PATHS)
        | {spec.relative for spec in FOCUSED_TESTS}
    )
)
PRODUCER_BOUND_RELATIVES = (
    "docs/reference_cases/ge_beam3_mixed_p2_baseline.json",
    "docs/reference_cases/ge_beam3_mixed_p2_cases.json",
    "docs/reference_cases/ge_beam3_mixed_p2_contract.json",
    "docs/reference_cases/ge_beam3_mixed_p2_independent_reference.py",
    "docs/reference_cases/ge_beam3_mixed_p2_plan_review.json",
    "docs/reference_cases/ge_beam3_mixed_p2_state_schema.json",
    "docs/reference_cases/ge_beam3_mixed_p2_recovery_correction.json",
    "docs/reference_cases/ge_beam3_mixed_p2_recovery_correction_contract.json",
    "docs/reference_cases/ge_beam3_mixed_p2_recovery_correction_reference.py",
    "docs/reference_cases/ge_beam3_mixed_p2_recovery_correction_review.json",
)
PROOF_COUNTS = {
    "load_mass_recovery": 11,
    "modal_buckling": 4,
    "solver_chart_state": 6,
    "total": 21,
}
RECOVERY_CASE_IDS = (
    "RECOVERY_MANUFACTURED_UNIFORM_SHEAR_Y_NATIVE_STATE",
    "RECOVERY_TORSION_SIDED_NATIVE_STATE",
    "RECOVERY_UNIFORM_AXIAL_NATIVE_STATE",
    "RECOVERY_ZERO_NATIVE_STATE",
)
SCIENTIFIC_GROUP_ORDER = (
    "SOLVER_CHART_OR_STATE",
    "LOAD_MASS_OR_RECOVERY",
    "MODAL_OR_BUCKLING",
)


@dataclass(frozen=True)
class ExecutionBounds:
    child_wall_seconds: float = 600.0
    complete_wave_wall_seconds: float = 1800.0
    inactivity_seconds: float = 300.0
    memory_limit_bytes: int = 24 * 1024**3
    maximum_concurrent_workers: int = 3
    numerical_library_threads: int = 1

    def authority_record(self) -> dict[str, Any]:
        return {
            "child_wall_seconds": int(self.child_wall_seconds),
            "complete_wave_wall_seconds": int(self.complete_wave_wall_seconds),
            "inactivity_seconds": int(self.inactivity_seconds),
            "maximum_concurrent_workers": self.maximum_concurrent_workers,
            "memory_limit_gib_per_process_tree": self.memory_limit_bytes // 1024**3,
            "no_automatic_retry": True,
            "numerical_library_threads_per_worker": self.numerical_library_threads,
            "required_formal_cycle_count": 2,
        }


FROZEN_BOUNDS = ExecutionBounds()
THREAD_VARIABLES = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)

TERMINAL_PRECEDENCE = (
    "BLOCKED_GE_BEAM3_P2_BASELINE_OR_AUTHORITY",
    "BLOCKED_GE_BEAM3_P2_PROCESS_OR_EVIDENCE",
    "NO_GO_GE_BEAM3_P2_SOLVER_CHART_OR_STATE",
    "NO_GO_GE_BEAM3_P2_LOAD_MASS_OR_RECOVERY",
    "NO_GO_GE_BEAM3_P2_MODAL_OR_BUCKLING",
    "PROVISIONAL_GO_GE_BEAM3_P2_PRIVATE_PARITY",
)

PROCESS_BOUND_REASONS = frozenset(
    {
        "CHILD_WALL_LIMIT",
        "COMPLETE_WAVE_WALL_LIMIT",
        "PROCESS_TREE_DRAIN_FAILURE",
        "PROCESS_TREE_INACTIVITY_LIMIT",
        "PROCESS_TREE_MEMORY_LIMIT",
    }
)
WORKER_PROCESS_REASONS = PROCESS_BOUND_REASONS | {
    "COORDINATOR_FAILURE",
    "MALFORMED_WORKER_RECORD",
    "WORKER_LAUNCH_OR_MONITOR_FAILURE",
    "WORKER_PROCESS_OR_OUTPUT_FAILURE",
}
SCIENTIFIC_PROCESS_REASONS = PROCESS_BOUND_REASONS | {
    "CHECKER_LAUNCH_OR_MONITOR_FAILURE",
    "CHECKER_PROCESS_OR_OUTPUT_FAILURE",
    "CHECKER_REJECTED_MALFORMED_PROOF",
    "CHECKER_REPLICA_DISAGREEMENT",
    "MALFORMED_CHECKER_RECORD",
    "MALFORMED_PROOF_RECORD",
    "PRODUCER_LAUNCH_OR_MONITOR_FAILURE",
    "PRODUCER_PROCESS_OR_OUTPUT_FAILURE",
    "SCIENTIFIC_LANE_NOT_LAUNCHED_AFTER_FOCUSED_GUARD",
}


class RunnerError(RuntimeError):
    """Base class for deliberate fail-closed runner errors."""


class BaselineError(RunnerError):
    """The frozen repository or Git-blob authority does not match."""


class AuthorizationError(RunnerError):
    """Formal execution is not authorized by an exact external record."""


class ExclusiveOutputError(RunnerError):
    """A supposedly fresh or exclusive destination already exists."""


class EvidenceError(RunnerError):
    """A child or cycle record is structurally invalid."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(token: str) -> None:
    raise ValueError(f"nonfinite JSON value: {token}")


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def strict_canonical_json(path: Path) -> tuple[bytes, dict[str, Any]]:
    if not path.is_file() or path.is_symlink() or _is_reparse(path):
        raise AuthorizationError(f"canonical JSON is missing or unsafe: {path.name}")
    try:
        raw = path.read_bytes()
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_nonfinite,
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise AuthorizationError(f"canonical JSON is unreadable or malformed: {path.name}") from exc
    if not isinstance(value, dict) or canonical_bytes(value) != raw:
        raise AuthorizationError(f"JSON is not a canonical object: {path.name}")
    return raw, value


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _is_hex(value: Any, length: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and all(character in "0123456789ABCDEF" for character in value)
    )


def _is_lower_hex(value: Any, length: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and all(character in "0123456789abcdef" for character in value)
    )


def _is_enum(value: Any) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and all(character in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_" for character in value)
    )


def _git_environment() -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("GIT_")
    }
    environment.update(
        {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    return environment


def _git_bytes(repository: Path, *arguments: str) -> bytes:
    try:
        completed = subprocess.run(
            ("git", "-c", f"safe.directory={repository.resolve()}", *arguments),
            cwd=repository,
            env=_git_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise BaselineError(f"Git authority check failed: {' '.join(arguments)}") from exc
    return completed.stdout


def _git_text(repository: Path, *arguments: str) -> str:
    try:
        return _git_bytes(repository, *arguments).decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise BaselineError("Git returned non-UTF-8 authority metadata") from exc


def _require_clean(repository: Path) -> None:
    dirty = _git_text(repository, "status", "--porcelain=v1", "--untracked-files=all")
    if dirty:
        raise BaselineError("repository is not clean")


def _verify_commit(
    repository: Path,
    commit: str,
    tree: str,
    *,
    parent: str | None = None,
    exact_paths: Sequence[str] | None = None,
) -> None:
    if _git_text(repository, "rev-parse", f"{commit}^{{commit}}") != commit:
        raise BaselineError(f"frozen commit does not resolve exactly: {commit}")
    if _git_text(repository, "show", "-s", "--format=%T", commit) != tree:
        raise BaselineError(f"frozen tree mismatch: {commit}")
    if parent is not None and _git_text(repository, "rev-parse", f"{commit}^") != parent:
        raise BaselineError(f"frozen parent mismatch: {commit}")
    if exact_paths is not None:
        changed = tuple(
            sorted(
                line
                for line in _git_text(
                    repository,
                    "diff-tree",
                    "--no-commit-id",
                    "--name-only",
                    "-r",
                    commit,
                ).splitlines()
                if line
            )
        )
        if changed != tuple(sorted(exact_paths)):
            raise BaselineError(f"frozen changed-path extent mismatch: {commit}")


def git_blob_binding(repository: Path, revision: str, relative: str) -> dict[str, Any]:
    """Bind committed blob bytes, never checkout bytes affected by CRLF rules."""

    listing = _git_text(repository, "ls-tree", revision, "--", relative)
    try:
        metadata, listed_relative = listing.split("\t", 1)
        mode, kind, listed_oid = metadata.split(" ", 2)
    except ValueError as exc:
        raise BaselineError(f"missing or malformed Git tree entry for {relative}") from exc
    if (
        mode not in {"100644", "100755"}
        or kind != "blob"
        or listed_relative != relative
    ):
        raise BaselineError(f"registered input is not a regular Git file: {relative}")
    oid = _git_text(repository, "rev-parse", f"{revision}:{relative}")
    if not _is_hex(oid.upper(), 40):
        raise BaselineError(f"invalid Git blob object ID for {relative}")
    kind = _git_text(repository, "cat-file", "-t", oid)
    if kind != "blob":
        raise BaselineError(f"registered input is not a Git blob: {relative}")
    if listed_oid != oid:
        raise BaselineError(f"Git tree/blob identity disagreement for {relative}")
    payload = _git_bytes(repository, "cat-file", "blob", oid)
    return {
        "bytes": len(payload),
        "git_blob_oid": oid.lower(),
        "path": relative,
        "sha256": _sha256(payload),
    }


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left.resolve())) == os.path.normcase(str(right.resolve()))


def _is_reparse(path: Path) -> bool:
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _is_regular_nonreparse(path: Path) -> bool:
    return path.is_file() and not path.is_symlink() and not _is_reparse(path)


def _path_entry_exists(path: Path) -> bool:
    """Return true for every directory entry, including a dangling link."""

    return os.path.lexists(path)


def validate_anyfileio_repository(
    anyfileio_repository: Path | None,
) -> DependencyIdentity:
    """Bind the exact clean ANYfileIO checkout used by isolated children."""

    if anyfileio_repository is None:
        raise AuthorizationError("an explicit ANYfileIO repository is required")
    repository = anyfileio_repository.resolve()
    if not repository.is_dir():
        raise AuthorizationError("the explicit ANYfileIO repository is missing")
    top = Path(_git_text(repository, "rev-parse", "--show-toplevel")).resolve()
    if not _same_path(top, repository):
        raise BaselineError("ANYfileIO dependency path is not its Git root")
    _require_clean(repository)
    commit = _git_text(repository, "rev-parse", "HEAD")
    tree = _git_text(repository, "show", "-s", "--format=%T", "HEAD")
    if not _is_hex(commit.upper(), 40) or not _is_hex(tree.upper(), 40):
        raise BaselineError("ANYfileIO dependency has invalid Git identities")

    raw_listing = _git_bytes(
        repository,
        "ls-tree",
        "-r",
        "-z",
        "--full-tree",
        commit,
        "--",
        "src/anyfileio",
    )
    entries = [entry for entry in raw_listing.split(b"\0") if entry]
    if not entries:
        raise BaselineError("ANYfileIO has no registered src/anyfileio manifest")
    manifest: list[dict[str, Any]] = []
    registered_paths: set[str] = set()
    for entry in entries:
        try:
            metadata_raw, relative_raw = entry.split(b"\t", 1)
            mode_raw, kind_raw, oid_raw = metadata_raw.split(b" ", 2)
            mode = mode_raw.decode("ascii")
            kind = kind_raw.decode("ascii")
            oid = oid_raw.decode("ascii").lower()
            relative = relative_raw.decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise BaselineError("ANYfileIO Git manifest is malformed") from exc
        if (
            mode not in {"100644", "100755"}
            or kind != "blob"
            or not relative.startswith("src/anyfileio/")
            or relative in registered_paths
            or not _is_hex(oid.upper(), 40)
        ):
            raise BaselineError("ANYfileIO Git manifest has a noncanonical entry")
        registered_paths.add(relative)
        path = repository / Path(relative)
        if (
            not path.is_file()
            or path.is_symlink()
            or _is_reparse(path)
            or not _is_within(path, repository / "src" / "anyfileio")
        ):
            raise BaselineError("ANYfileIO working source is not a regular registered file")
        working_oid = _git_text(
            repository,
            "-c",
            "core.autocrlf=true",
            "hash-object",
            f"--path={relative}",
            "--",
            relative,
        ).lower()
        if working_oid != oid:
            raise BaselineError("ANYfileIO working source differs from its Git blob")
        payload = _git_bytes(repository, "cat-file", "blob", oid)
        manifest.append(
            {
                "bytes": len(payload),
                "git_blob_oid": oid,
                "mode": mode,
                "path": relative,
                "sha256": _sha256(payload),
            }
        )

    # Ignored bytecode is harmless because every child uses a fresh explicit
    # PYTHONPYCACHEPREFIX.  Every other source-tree file must be registered.
    on_disk: set[str] = set()
    source_root = repository / "src" / "anyfileio"
    for path in source_root.rglob("*"):
        relative_parts = path.relative_to(source_root).parts
        if "__pycache__" in relative_parts:
            continue
        if path.is_symlink() or _is_reparse(path):
            raise BaselineError("ANYfileIO source tree contains an unregistered reparse point")
        if path.is_file():
            on_disk.add(path.relative_to(repository).as_posix())
    if on_disk != registered_paths:
        raise BaselineError("ANYfileIO source-tree inventory differs from its Git manifest")
    manifest.sort(key=lambda row: row["path"])
    return DependencyIdentity(
        commit=commit,
        file_count=len(manifest),
        files=tuple(manifest),
        manifest_sha256=_sha256(canonical_bytes(manifest)),
        total_bytes=sum(row["bytes"] for row in manifest),
        tree=tree,
        tree_files=_git_tree_manifest(repository, commit),
    )


@dataclass(frozen=True)
class DependencyIdentity:
    commit: str
    file_count: int
    files: tuple[dict[str, Any], ...]
    manifest_sha256: str
    total_bytes: int
    tree: str
    tree_files: tuple[dict[str, Any], ...]

    def record(self) -> dict[str, Any]:
        return {
            "commit": self.commit,
            "file_count": self.file_count,
            "manifest_sha256": self.manifest_sha256,
            "total_bytes": self.total_bytes,
            "tree": self.tree,
            "tree_file_count": len(self.tree_files),
            "tree_manifest_sha256": _sha256(canonical_bytes(list(self.tree_files))),
            "tree_total_bytes": sum(row["bytes"] for row in self.tree_files),
        }


@dataclass(frozen=True)
class RegistryIdentity:
    identity_sha256: str
    registry_id: str
    root_sha256: str

    def record(self) -> dict[str, Any]:
        return {
            "identity_sha256": self.identity_sha256,
            "registry_id": self.registry_id,
            "root_sha256": self.root_sha256,
        }


@dataclass(frozen=True)
class RuntimeIdentity:
    bootstrap_sha256: str
    distribution_seeds: tuple[str, ...]
    distributions: tuple[dict[str, Any], ...]
    interpreter: dict[str, Any]
    pytest_transitive_closure: tuple[str, ...]

    def record(self) -> dict[str, Any]:
        return {
            "bootstrap_sha256": self.bootstrap_sha256,
            "distribution_seeds": list(self.distribution_seeds),
            "distributions": [dict(row) for row in self.distributions],
            "interpreter": dict(self.interpreter),
            "pytest_transitive_closure": list(self.pytest_transitive_closure),
        }


@dataclass(frozen=True)
class RepositorySnapshot:
    anyfileio: DependencyIdentity
    harness_commit: str
    harness_tree: str
    manifest_sha256: str
    producer_input_bindings: dict[str, dict[str, Any]]
    registry: RegistryIdentity
    runtime: RuntimeIdentity
    solver_files: tuple[dict[str, Any], ...]
    test_bindings: dict[str, dict[str, Any]]


def _location_sha256(path: Path) -> str:
    normalized = os.path.normcase(str(path.resolve())).encode("utf-8")
    return _sha256(normalized)


def _git_tree_manifest(
    repository: Path,
    revision: str,
    *,
    prefix: str | None = None,
) -> tuple[dict[str, Any], ...]:
    arguments = ["ls-tree", "-r", "-z", "--full-tree", revision]
    if prefix is not None:
        arguments.extend(("--", prefix))
    raw = _git_bytes(repository, *arguments)
    rows: list[dict[str, Any]] = []
    folded: set[str] = set()
    for entry in (item for item in raw.split(b"\0") if item):
        try:
            metadata, encoded_path = entry.split(b"\t", 1)
            encoded_mode, encoded_kind, encoded_oid = metadata.split(b" ", 2)
            mode = encoded_mode.decode("ascii")
            kind = encoded_kind.decode("ascii")
            oid = encoded_oid.decode("ascii").lower()
            relative = encoded_path.decode("utf-8").replace("\\", "/")
        except (ValueError, UnicodeDecodeError) as exc:
            raise BaselineError("Git materialization manifest is malformed") from exc
        parts = Path(relative).parts
        key = relative.casefold()
        if (
            mode not in {"100644", "100755"}
            or kind != "blob"
            or not _is_hex(oid.upper(), 40)
            or not parts
            or Path(relative).is_absolute()
            or ".." in parts
            or key in folded
        ):
            raise BaselineError("Git materialization manifest is unsafe")
        folded.add(key)
        payload = _git_bytes(repository, "cat-file", "blob", oid)
        rows.append(
            {
                "bytes": len(payload),
                "git_blob_oid": oid,
                "mode": mode,
                "path": relative,
                "sha256": _sha256(payload),
            }
        )
    if not rows:
        raise BaselineError("Git materialization manifest is empty")
    return tuple(sorted(rows, key=lambda row: row["path"]))


def _validate_working_tree_files(
    repository: Path,
    rows: Sequence[dict[str, Any]],
) -> None:
    """Catch tracked substitution even when index flags suppress Git status."""

    for row in rows:
        path = repository / row["path"]
        if (
            not path.is_file()
            or path.is_symlink()
            or _is_reparse(path)
        ):
            raise BaselineError("a committed working file is missing or unsafe")
        oid = _git_text(
            repository,
            "-c",
            "core.autocrlf=true",
            "hash-object",
            f"--path={row['path']}",
            "--",
            row["path"],
        ).lower()
        if oid != row["git_blob_oid"]:
            raise BaselineError("a committed working file differs from its Git blob")


def validate_registry_root(registry_root: Path | None) -> RegistryIdentity:
    if registry_root is None:
        raise AuthorizationError("an explicit external registry root is required")
    root = registry_root.resolve()
    if (
        not root.is_dir()
        or root.is_symlink()
        or _is_reparse(root)
    ):
        raise AuthorizationError("the registry root must be a regular existing directory")
    marker = root / REGISTRY_IDENTITY_NAME
    if (
        not marker.is_file()
        or marker.is_symlink()
        or _is_reparse(marker)
    ):
        raise AuthorizationError("the registry identity marker is missing or unsafe")
    raw, record = strict_canonical_json(marker)
    if (
        set(record) != {"registry_id", "schema", "study_id", "terminal"}
        or record["schema"] != REGISTRY_IDENTITY_SCHEMA
        or record["study_id"] != STUDY_ID
        or record["terminal"] != "REGISTERED_GE_BEAM3_P2_EXECUTION_REGISTRY"
        or not _is_hex(record["registry_id"], 64)
    ):
        raise AuthorizationError("the registry identity marker is malformed")
    return RegistryIdentity(
        identity_sha256=_sha256(raw),
        registry_id=record["registry_id"],
        root_sha256=_location_sha256(root),
    )


def _runtime_distribution(
    distribution_name: str,
    import_name: str,
    label: str,
) -> dict[str, Any]:
    try:
        distribution = importlib_metadata.distribution(distribution_name)
        files = list(distribution.files or ())
        spec = importlib_util.find_spec(import_name)
    except (ImportError, importlib_metadata.PackageNotFoundError) as exc:
        raise BaselineError(f"required runtime distribution is missing: {label}") from exc
    if spec is None or spec.origin is None or not files:
        raise BaselineError(f"required runtime origin is unavailable: {label}")
    root = Path(distribution.locate_file("")).resolve()
    origin = Path(spec.origin).resolve()
    if (
        not origin.is_file()
        or origin.is_symlink()
        or _is_reparse(origin)
    ):
        raise BaselineError(f"required runtime origin is unsafe: {label}")
    rows: list[dict[str, Any]] = []
    record_files: list[Path] = []
    folded: set[str] = set()
    for registered in files:
        relative = str(registered).replace("\\", "/")
        key = relative.casefold()
        target = Path(distribution.locate_file(registered)).resolve()
        if key in folded or not relative or Path(relative).is_absolute():
            raise BaselineError(f"runtime file manifest is unsafe: {label}")
        folded.add(key)
        if (
            not target.is_file()
            or target.is_symlink()
            or _is_reparse(target)
        ):
            raise BaselineError(f"runtime file is missing or unsafe: {label}")
        payload = target.read_bytes()
        rows.append(
            {
                "bytes": len(payload),
                "path": relative,
                "sha256": _sha256(payload),
            }
        )
        if relative.endswith(".dist-info/RECORD"):
            record_files.append(target)
    if len(record_files) != 1:
        raise BaselineError(f"runtime RECORD manifest is ambiguous: {label}")
    rows.sort(key=lambda row: row["path"])
    import_roots = tuple(
        Path(value).resolve()
        for value in (spec.submodule_search_locations or (origin.parent,))
    )
    if len(import_roots) != 1:
        raise BaselineError(f"runtime import root is ambiguous: {label}")
    import_root = import_roots[0]
    if not import_root.is_dir() or import_root.is_symlink() or _is_reparse(import_root):
        raise BaselineError(f"runtime import root is unsafe: {label}")
    import_rows: list[dict[str, Any]] = []
    if spec.submodule_search_locations:
        prefix = import_name.replace(".", "/")
        candidates = import_root.rglob("*")
    else:
        prefix = ""
        candidates = (origin,)
    for target in candidates:
        if not target.is_file():
            continue
        relative_parts = target.relative_to(import_root).parts
        if "__pycache__" in relative_parts or target.suffix in {".pyc", ".pyo"}:
            continue
        if target.is_symlink() or _is_reparse(target):
            raise BaselineError(f"runtime import tree is unsafe: {label}")
        payload = target.read_bytes()
        logical = "/".join(
            part
            for part in (prefix, target.relative_to(import_root).as_posix())
            if part
        )
        import_rows.append(
            {"bytes": len(payload), "path": logical, "sha256": _sha256(payload)}
        )
    import_rows.sort(key=lambda row: row["path"])
    if not import_rows:
        raise BaselineError(f"runtime import tree is empty: {label}")
    origin_payload = origin.read_bytes()
    try:
        origin_relative = origin.relative_to(import_root).as_posix()
    except ValueError as exc:
        raise BaselineError(f"runtime origin escapes its import root: {label}") from exc
    return {
        "distribution": label,
        "distribution_root_sha256": _location_sha256(root),
        "file_count": len(rows),
        "file_manifest_sha256": _sha256(canonical_bytes(rows)),
        "import_file_count": len(import_rows),
        "import_manifest_sha256": _sha256(canonical_bytes(import_rows)),
        "import_root_location_sha256": _location_sha256(import_root),
        "import_total_bytes": sum(row["bytes"] for row in import_rows),
        "module": import_name,
        "origin_bytes": len(origin_payload),
        "origin_location_sha256": _location_sha256(origin),
        "origin_relative_sha256": _sha256(origin_relative.encode("utf-8")),
        "origin_sha256": _sha256(origin_payload),
        "record_sha256": _sha256(record_files[0].read_bytes()),
        "total_bytes": sum(row["bytes"] for row in rows),
        "version": distribution.version,
    }


def _active_distribution_closure(seed_names: Sequence[str]) -> tuple[str, ...]:
    pending = [canonicalize_name(name) for name in seed_names]
    visited: set[str] = set()
    while pending:
        normalized = pending.pop()
        if normalized in visited:
            continue
        try:
            distribution = importlib_metadata.distribution(normalized)
        except importlib_metadata.PackageNotFoundError as exc:
            raise BaselineError(
                f"required runtime distribution is missing: {normalized}"
            ) from exc
        visited.add(normalized)
        for raw_requirement in distribution.requires or ():
            try:
                requirement = Requirement(raw_requirement)
                active = requirement.marker is None or requirement.marker.evaluate(
                    {"extra": ""}
                )
            except Exception as exc:
                raise BaselineError("runtime requirement metadata is malformed") from exc
            required = canonicalize_name(requirement.name)
            if active and required not in visited:
                pending.append(required)
    return tuple(sorted(visited))


def _runtime_distribution_specs() -> tuple[tuple[str, str, str], ...]:
    seed_by_name = {
        canonicalize_name(distribution): (label, distribution, module)
        for label, distribution, module in RUNTIME_DISTRIBUTIONS
    }
    closure = _active_distribution_closure(tuple(seed_by_name))
    package_map = importlib_metadata.packages_distributions()
    specs: list[tuple[str, str, str]] = []
    for normalized in closure:
        if normalized in seed_by_name:
            specs.append(seed_by_name[normalized])
            continue
        distribution = importlib_metadata.distribution(normalized)
        metadata_name = distribution.metadata.get("Name") or normalized
        modules = sorted(
            package
            for package, distributions in package_map.items()
            if any(canonicalize_name(item) == normalized for item in distributions)
        )
        if not modules:
            candidate = normalized.replace("-", "_")
            if importlib_util.find_spec(candidate) is None:
                raise BaselineError(
                    f"runtime distribution has no importable top level: {normalized}"
                )
            modules = [candidate]
        specs.append((metadata_name, metadata_name, modules[0]))
    return tuple(sorted(specs, key=lambda row: canonicalize_name(row[1])))


def runtime_identity() -> RuntimeIdentity:
    executable = Path(sys.executable).resolve()
    if (
        not executable.is_file()
        or executable.is_symlink()
        or _is_reparse(executable)
    ):
        raise BaselineError("Python executable is missing or unsafe")
    payload = executable.read_bytes()
    interpreter = {
        "abi": sysconfig.get_config_var("SOABI") or sys.implementation.cache_tag,
        "bytes": len(payload),
        "cache_tag": sys.implementation.cache_tag,
        "executable_location_sha256": _location_sha256(executable),
        "executable_name": executable.name,
        "implementation": platform.python_implementation(),
        "sha256": _sha256(payload),
        "version": platform.python_version(),
    }
    distributions = tuple(
        _runtime_distribution(distribution, module, label)
        for label, distribution, module in _runtime_distribution_specs()
    )
    pytest_closure = _active_distribution_closure(("pytest",))
    labels = {
        canonicalize_name(row["distribution"]): row["distribution"]
        for row in distributions
    }
    return RuntimeIdentity(
        bootstrap_sha256=_sha256(ISOLATED_BOOTSTRAP.encode("utf-8")),
        distribution_seeds=tuple(
            distribution for _label, distribution, _module in RUNTIME_DISTRIBUTIONS
        ),
        distributions=distributions,
        interpreter=interpreter,
        pytest_transitive_closure=tuple(labels[name] for name in pytest_closure),
    )


def _manifest_identity(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    return {
        "file_count": len(rows),
        "manifest_sha256": _sha256(canonical_bytes(list(rows))),
        "total_bytes": sum(row["bytes"] for row in rows),
    }


def validate_repository(
    repository: Path = ROOT,
    anyfileio_repository: Path | None = None,
    registry_root: Path | None = None,
    *,
    revision: str = "HEAD",
    require_head: bool = True,
) -> RepositorySnapshot:
    repository = repository.resolve()
    if anyfileio_repository is None:
        raise AuthorizationError("an explicit ANYfileIO repository is required")
    if _same_path(repository, anyfileio_repository):
        raise AuthorizationError("ANYsolver and ANYfileIO repositories must be distinct")
    _require_clean(repository)
    anyfileio = validate_anyfileio_repository(anyfileio_repository)
    registry = validate_registry_root(registry_root)
    if registry_root is None:  # pragma: no cover - rejected by validation above
        raise AuthorizationError("an explicit external registry root is required")
    if (
        _is_within(registry_root, repository)
        or _is_within(registry_root, anyfileio_repository)
    ):
        raise AuthorizationError("the execution registry must be external")
    runtime = runtime_identity()
    _verify_commit(
        repository,
        RECOVERY_CORRECTION_COMMIT,
        RECOVERY_CORRECTION_TREE,
        parent=PREREGISTRATION_COMMIT,
        exact_paths=RECOVERY_CORRECTION_PATHS,
    )
    _verify_commit(
        repository,
        IMPLEMENTATION_COMMIT,
        IMPLEMENTATION_TREE,
        parent=RECOVERY_CORRECTION_COMMIT,
        exact_paths=IMPLEMENTATION_PATHS,
    )
    _verify_commit(
        repository,
        IMPLEMENTATION_REVIEW_COMMIT,
        IMPLEMENTATION_REVIEW_TREE,
        parent=IMPLEMENTATION_COMMIT,
        exact_paths=IMPLEMENTATION_REVIEW_PATHS,
    )
    if (
        _git_text(
            repository,
            "rev-parse",
            f"{IMPLEMENTATION_REVIEW_COMMIT}:{IMPLEMENTATION_REVIEW_RELATIVE}",
        )
        != IMPLEMENTATION_REVIEW_BLOB_OID
    ):
        raise BaselineError("implementation-review blob identity mismatch")
    head = _git_text(repository, "rev-parse", "HEAD")
    frozen = _git_text(repository, "rev-parse", f"{revision}^{{commit}}")
    if require_head and head != frozen:
        raise BaselineError("preauthorization requires HEAD at the frozen harness")
    tree = _git_text(repository, "show", "-s", "--format=%T", frozen)
    try:
        subprocess.run(
            (
                "git",
                "-c",
                f"safe.directory={repository}",
                "merge-base",
                "--is-ancestor",
                IMPLEMENTATION_REVIEW_COMMIT,
                frozen,
            ),
            cwd=repository,
            env=_git_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise BaselineError("runner head does not descend from the reviewed implementation") from exc
    extent = tuple(
        sorted(
            line
            for line in _git_text(
                repository,
                "diff",
                "--name-only",
                f"{IMPLEMENTATION_REVIEW_COMMIT}..{frozen}",
            ).splitlines()
            if line
        )
    )
    if extent != HARNESS_PATHS:
        raise BaselineError("formal-runner commit has a noncanonical path extent")
    manifest = [git_blob_binding(repository, frozen, path) for path in BOUND_PATHS]
    manifest_sha256 = _sha256(canonical_bytes(manifest))
    solver_files = _git_tree_manifest(repository, frozen)
    _validate_working_tree_files(repository, solver_files)
    by_path = {row["path"]: row for row in manifest}
    producer_input_bindings = {
        Path(path).name: {
            "bytes": by_path[path]["bytes"],
            "sha256": by_path[path]["sha256"],
        }
        for path in PRODUCER_BOUND_RELATIVES
    }
    test_bindings = {
        spec.test_id: {
            "git_blob_oid": by_path[spec.relative]["git_blob_oid"],
            "sha256": by_path[spec.relative]["sha256"],
        }
        for spec in FOCUSED_TESTS
    }
    return RepositorySnapshot(
        anyfileio=anyfileio,
        harness_commit=frozen,
        harness_tree=tree,
        manifest_sha256=manifest_sha256,
        producer_input_bindings=producer_input_bindings,
        registry=registry,
        runtime=runtime,
        solver_files=solver_files,
        test_bindings=test_bindings,
    )


def expected_authority_check(snapshot: RepositorySnapshot) -> dict[str, Any]:
    return {
        "candidate_id": CANDIDATE_ID,
        "checks": {
            "anyfileio_clean": True,
            "anyfileio_git_root_exact": True,
            "anyfileio_manifest_exact": True,
            "anyfileio_working_sources_equal_git_blobs": True,
            "bound_inputs_are_git_blobs": True,
            "frozen_commit_chain_exact": True,
            "frozen_path_extents_exact": True,
            "harness_extent_exact": True,
            "implementation_review_exact": True,
            "registry_identity_exact": True,
            "repository_clean": True,
            "runtime_distribution_manifests_exact": True,
            "runtime_interpreter_exact": True,
            "solver_working_files_equal_git_blobs": True,
        },
        "frozen_inputs": {
            "anyfileio": snapshot.anyfileio.record(),
            "harness_commit": snapshot.harness_commit,
            "harness_tree": snapshot.harness_tree,
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "implementation_review_commit": IMPLEMENTATION_REVIEW_COMMIT,
            "implementation_tree": IMPLEMENTATION_TREE,
            "manifest_sha256": snapshot.manifest_sha256,
            "registry": snapshot.registry.record(),
            "recovery_correction_commit": RECOVERY_CORRECTION_COMMIT,
            "recovery_correction_tree": RECOVERY_CORRECTION_TREE,
            "runtime": snapshot.runtime.record(),
            "solver_tree": _manifest_identity(snapshot.solver_files),
        },
        "schema": AUTHORITY_CHECK_SCHEMA,
        "scientific_checker_replica_count": 2,
        "scientific_producer_count": 1,
        "study_id": STUDY_ID,
        "terminal": AUTHORITY_CHECK_TERMINAL,
        "test_file_count": len(FOCUSED_TESTS),
    }


def write_authority_check(
    *,
    output_path: Path,
    repository: Path = ROOT,
    anyfileio_repository: Path | None = None,
    registry_root: Path | None = None,
) -> dict[str, Any]:
    repository = repository.resolve()
    if anyfileio_repository is None:
        raise AuthorizationError("an explicit ANYfileIO repository is required")
    anyfileio_repository = anyfileio_repository.resolve()
    if registry_root is None:
        raise AuthorizationError("an explicit external registry root is required")
    registry_root = registry_root.resolve()
    output_path = output_path.resolve()
    if _is_within(output_path, repository) or _is_within(
        output_path, anyfileio_repository
    ) or _is_within(output_path, registry_root):
        raise ExclusiveOutputError("authority-check output must be external")
    if _path_entry_exists(output_path):
        raise ExclusiveOutputError("authority-check output must be exclusive")
    snapshot = validate_repository(repository, anyfileio_repository, registry_root)
    record = expected_authority_check(snapshot)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("xb") as stream:
        stream.write(canonical_bytes(record))
    return record


def validate_authority_checks(
    paths: tuple[Path, Path] | None, snapshot: RepositorySnapshot
) -> tuple[bytes, dict[str, Any]]:
    if paths is None or len(paths) != 2:
        raise AuthorizationError("two authority-check-only records are required")
    if paths[0].resolve() == paths[1].resolve():
        raise AuthorizationError("authority-check replicas require distinct files")
    loaded: list[tuple[bytes, dict[str, Any]]] = []
    for path in paths:
        resolved = path.resolve()
        if not resolved.is_file() or resolved.is_symlink():
            raise AuthorizationError("authority check must be a regular file")
        loaded.append(strict_canonical_json(resolved))
    if loaded[0][0] != loaded[1][0]:
        raise AuthorizationError("authority-check replicas are not byte-identical")
    if loaded[0][1] != expected_authority_check(snapshot):
        raise AuthorizationError("authority check does not bind the frozen harness")
    return loaded[0]


def validate_rehearsal_aggregate(
    path: Path | None,
    snapshot: RepositorySnapshot,
    authority_check_sha256: str,
) -> dict[str, Any]:
    if path is None:
        raise AuthorizationError("formal mode requires a passing rehearsal aggregate")
    resolved = path.resolve()
    if not resolved.is_file() or resolved.is_symlink() or _is_reparse(resolved):
        raise AuthorizationError("formal rehearsal aggregate is missing or unsafe")
    raw, record = strict_canonical_json(resolved)
    fields = {
        "authority",
        "candidate_id",
        "cycle_replica_count",
        "cycle_result_sha256",
        "cycle_results_byte_identical",
        "frozen_inputs",
        "mode",
        "result",
        "schema",
        "study_id",
        "terminal",
    }
    materialization_sha = record.get("frozen_inputs", {}).get(
        "materialization_sha256"
    )
    expected_frozen = {
        "anyfileio": snapshot.anyfileio.record(),
        "harness_commit": snapshot.harness_commit,
        "harness_tree": snapshot.harness_tree,
        "implementation_commit": IMPLEMENTATION_COMMIT,
        "implementation_review_commit": IMPLEMENTATION_REVIEW_COMMIT,
        "implementation_tree": IMPLEMENTATION_TREE,
        "manifest_sha256": snapshot.manifest_sha256,
        "materialization_sha256": materialization_sha,
        "registry": snapshot.registry.record(),
        "recovery_correction_commit": RECOVERY_CORRECTION_COMMIT,
        "recovery_correction_tree": RECOVERY_CORRECTION_TREE,
        "runtime": snapshot.runtime.record(),
        "solver_tree": _manifest_identity(snapshot.solver_files),
    }
    expected_authority = {
        "authority_check_replica_count": 2,
        "authority_checks_byte_identical": True,
        "authority_check_sha256": authority_check_sha256,
        "formal_authorization_required": False,
        "formal_authorization_validated": False,
    }
    result = record.get("result")
    cycle_hashes = record.get("cycle_result_sha256")
    if (
        set(record) != fields
        or record.get("schema") != AGGREGATE_SCHEMA
        or record.get("mode") != REHEARSAL_MODE
        or record.get("terminal") != "NONCLASSIFYING_GE_BEAM3_P2_REHEARSAL_PASS"
        or record.get("candidate_id") != CANDIDATE_ID
        or record.get("study_id") != STUDY_ID
        or record.get("authority") != expected_authority
        or record.get("frozen_inputs") != expected_frozen
        or not _is_hex(materialization_sha, 64)
        or record.get("cycle_replica_count") != 1
        or record.get("cycle_results_byte_identical") is not True
        or not isinstance(cycle_hashes, list)
        or len(cycle_hashes) != 1
        or not _is_hex(cycle_hashes[0], 64)
        or not isinstance(result, dict)
        or cycle_hashes[0] != _sha256(canonical_bytes(result))
        or not _is_passing_rehearsal_cycle(result, snapshot)
    ):
        raise AuthorizationError("rehearsal aggregate does not bind a passing frozen run")
    return {
        "bytes": len(raw),
        "sha256": _sha256(raw),
        "terminal": record["terminal"],
    }


def _is_passing_rehearsal_cycle(
    cycle: dict[str, Any], snapshot: RepositorySnapshot
) -> bool:
    if set(cycle) != {
        "collected_count",
        "failed_test_file_count",
        "passed_test_file_count",
        "scientific",
        "test_file_count",
        "tests",
    }:
        return False
    tests = cycle.get("tests")
    if not isinstance(tests, list) or len(tests) != len(FOCUSED_TESTS):
        return False
    collected = 0
    for spec, row in zip(FOCUSED_TESTS, tests, strict=True):
        if (
            not isinstance(row, dict)
            or set(row)
            != {
                "collected_count",
                "finding_group",
                "git_blob_oid",
                "node_ids_sha256",
                "outcome",
                "passed",
                "record_sha256",
                "sha256",
                "test_id",
            }
            or row.get("test_id") != spec.test_id
            or row.get("finding_group") != "NONE"
            or row.get("outcome") != "PASS"
            or row.get("passed") is not True
            or type(row.get("collected_count")) is not int
            or row["collected_count"] <= 0
            or row.get("git_blob_oid")
            != snapshot.test_bindings[spec.test_id]["git_blob_oid"]
            or row.get("sha256") != snapshot.test_bindings[spec.test_id]["sha256"]
            or not _is_hex(row.get("node_ids_sha256"), 64)
            or not _is_hex(row.get("record_sha256"), 64)
        ):
            return False
        collected += row["collected_count"]
    scientific = cycle.get("scientific")
    if not isinstance(scientific, dict) or set(scientific) != {
        "checker_replica_count",
        "checker_replicas_byte_identical",
        "checker_sha256",
        "finding_groups",
        "outcome",
        "passed",
        "proof",
        "raw_record_count",
    }:
        return False
    proof = scientific.get("proof")
    return bool(
        cycle.get("collected_count") == collected
        and cycle.get("failed_test_file_count") == 0
        and cycle.get("passed_test_file_count") == len(FOCUSED_TESTS)
        and cycle.get("test_file_count") == len(FOCUSED_TESTS)
        and scientific.get("checker_replica_count") == 2
        and scientific.get("checker_replicas_byte_identical") is True
        and _is_hex(scientific.get("checker_sha256"), 64)
        and scientific.get("finding_groups") == []
        and scientific.get("outcome") == "PASS"
        and scientific.get("passed") is True
        and scientific.get("raw_record_count") == PROOF_COUNTS["total"]
        and isinstance(proof, dict)
        and set(proof)
        == {"bytes", "content_sha256", "proof_sha256", "raw_record_count"}
        and type(proof.get("bytes")) is int
        and proof["bytes"] > 0
        and _is_hex(proof.get("content_sha256"), 64)
        and _is_hex(proof.get("proof_sha256"), 64)
        and proof.get("raw_record_count") == PROOF_COUNTS["total"]
    )


def _executor_binding(repository: Path, revision: str) -> dict[str, Any]:
    return git_blob_binding(repository, revision, RUNNER_RELATIVE)


def normalized_formal_command(
    *,
    repository: Path,
    anyfileio_repository: Path,
    registry_root: Path,
    authority_check_paths: tuple[Path, Path],
    rehearsal_aggregate_path: Path,
    work_root: Path,
    output_path: Path,
) -> dict[str, Any]:
    argv = [
        str(Path(sys.executable).resolve()),
        str((repository / RUNNER_RELATIVE).resolve()),
        "--formal",
        "--repository",
        str(repository.resolve()),
        "--anyfileio-repository",
        str(anyfileio_repository.resolve()),
        "--registry-root",
        str(registry_root.resolve()),
        "--authority-check-1",
        str(authority_check_paths[0].resolve()),
        "--authority-check-2",
        str(authority_check_paths[1].resolve()),
        "--rehearsal-aggregate",
        str(rehearsal_aggregate_path.resolve()),
        "--work-root",
        str(work_root.resolve()),
        "--output",
        str(output_path.resolve()),
    ]
    return {"argv": argv, "sha256": _sha256(canonical_bytes(argv))}


def _attest_formal_cli(command: dict[str, Any]) -> None:
    if _ACTIVE_CLI_ARGV is None or list(_ACTIVE_CLI_ARGV) != command.get("argv"):
        raise AuthorizationError("formal execution requires the exact authorized CLI argv")


def _actual_cli_argv(raw_arguments: Sequence[str]) -> tuple[str, ...]:
    """Capture the literal script token as well as the executing interpreter.

    The formal command deliberately requires an absolute, nonsymlink spelling
    of the registered runner path.  Resolving ``sys.argv[0]`` here would hide a
    relative or alternate launcher spelling from the command attestation.
    """

    original = tuple(getattr(sys, "orig_argv", ()))
    expected_original = (
        original[0] if original else "",
        sys.argv[0],
        *raw_arguments,
    )
    if (
        original != expected_original
        or not original
        or not _same_path(Path(original[0]), Path(sys.executable))
        or sys.flags.optimize != 0
    ):
        raise AuthorizationError(
            "formal execution forbids interpreter switches or alternate launchers"
        )
    return (
        str(Path(sys.executable).resolve()),
        sys.argv[0],
        *raw_arguments,
    )


def expected_execution_review(
    snapshot: RepositorySnapshot,
    *,
    authority_check_sha256: str,
    command: dict[str, Any],
    executor: dict[str, Any],
    rehearsal_aggregate: dict[str, Any],
) -> dict[str, Any]:
    return {
        "findings": [],
        "reviewed_inputs": {
            "authority_check": {
                "replica_count": 2,
                "replicas_byte_identical": True,
                "sha256": authority_check_sha256,
            },
            "execution_bounds": FROZEN_BOUNDS.authority_record(),
            "execution_command": command,
            "executor": executor,
            "frozen_dependency": snapshot.anyfileio.record(),
            "frozen_harness": {
                "commit": snapshot.harness_commit,
                "manifest_sha256": snapshot.manifest_sha256,
                "tree": snapshot.harness_tree,
            },
            "registry": snapshot.registry.record(),
            "rehearsal_aggregate": rehearsal_aggregate,
            "runtime": snapshot.runtime.record(),
        },
        "reviewer_independence": EXECUTION_REVIEWER_INDEPENDENCE,
        "schema": EXECUTION_REVIEW_SCHEMA,
        "verdict": EXECUTION_REVIEW_VERDICT,
    }


def expected_authorization(
    snapshot: RepositorySnapshot,
    authority_check_sha256: str,
    *,
    request_id: str,
    attempt_id: str,
    registry_root: Path,
    command: dict[str, Any],
    executor: dict[str, Any],
    review: dict[str, Any],
    rehearsal_aggregate: dict[str, Any],
) -> dict[str, Any]:
    """Return the exact non-self-referential Git authorization record."""

    return {
        "authorization_commit": {
            "exact_paths": list(AUTHORIZATION_PATHS),
            "expected_parent": snapshot.harness_commit,
            "expected_subject": AUTHORIZATION_SUBJECT,
        },
        "candidate_id": CANDIDATE_ID,
        "authority_check": {
            "replica_count": 2,
            "replicas_byte_identical": True,
            "sha256": authority_check_sha256,
        },
        "execution_bounds": FROZEN_BOUNDS.authority_record(),
        "execution_command": command,
        "execution_review": review,
        "executor": executor,
        "frozen_dependency": {
            "distribution": "ANYfileio",
            "identity": snapshot.anyfileio.record(),
            "import_root": "SRC_ANYFILEIO",
        },
        "frozen_implementation": {
            "commit": IMPLEMENTATION_COMMIT,
            "tree": IMPLEMENTATION_TREE,
        },
        "frozen_implementation_review": {
            "commit": IMPLEMENTATION_REVIEW_COMMIT,
            "git_blob_oid": IMPLEMENTATION_REVIEW_BLOB_OID,
            "tree": IMPLEMENTATION_REVIEW_TREE,
        },
        "frozen_recovery_correction": {
            "commit": RECOVERY_CORRECTION_COMMIT,
            "tree": RECOVERY_CORRECTION_TREE,
        },
        "harness": {
            "commit": snapshot.harness_commit,
            "manifest_sha256": snapshot.manifest_sha256,
            "tree": snapshot.harness_tree,
        },
        "mode": FORMAL_MODE,
        "preauthorization_records": {
            "authority_check_replica_count": 2,
            "authority_checks_byte_identical": True,
            "authority_check_sha256": authority_check_sha256,
            "rehearsal_aggregate": rehearsal_aggregate,
        },
        "request": {
            "attempt_id": attempt_id,
            "no_retry": True,
            "one_time": True,
            "registry": snapshot.registry.record(),
            "registry_root": str(registry_root.resolve()),
            "request_id": request_id,
        },
        "runtime": snapshot.runtime.record(),
        "schema": AUTHORIZATION_SCHEMA,
        "scientific_lane": {
            "checker_replica_count_per_cycle": 2,
            "independent_checker_required": True,
            "producer_count_per_cycle": 1,
            "raw_record_count_per_cycle": PROOF_COUNTS["total"],
        },
        "study_id": STUDY_ID,
        "terminal": FORMAL_AUTHORIZATION_TERMINAL,
    }


@dataclass(frozen=True)
class ValidatedAuthorization:
    attempt_id: str
    authority_check_sha256: str
    binding: dict[str, Any]
    commit: str
    command: dict[str, Any]
    request_id: str
    review: dict[str, Any]
    tree: str


@dataclass(frozen=True)
class OneTimeClaim:
    binding: dict[str, Any]
    claim_path: Path
    lock_path: Path
    owner_path: Path
    receipt_path: Path


def _git_canonical_json(
    repository: Path,
    revision: str,
    relative: str,
) -> tuple[bytes, dict[str, Any], dict[str, Any]]:
    binding = git_blob_binding(repository, revision, relative)
    raw = _git_bytes(repository, "cat-file", "blob", binding["git_blob_oid"])
    try:
        record = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_nonfinite,
        )
    except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise AuthorizationError("committed authorization JSON is malformed") from exc
    if not isinstance(record, dict) or canonical_bytes(record) != raw:
        raise AuthorizationError("committed authorization JSON is noncanonical")
    return raw, record, binding


def validate_formal_overlay(
    *,
    repository: Path,
    snapshot: RepositorySnapshot,
    authority_check_sha256: str,
    command: dict[str, Any],
    registry_root: Path,
    rehearsal_aggregate: dict[str, Any],
) -> ValidatedAuthorization:
    head = _git_text(repository, "rev-parse", "HEAD")
    parents = _git_text(repository, "show", "-s", "--format=%P", head).split()
    changed = tuple(
        sorted(
            row
            for row in _git_text(
                repository,
                "diff-tree",
                "--no-commit-id",
                "--name-only",
                "-r",
                head,
            ).splitlines()
            if row
        )
    )
    if (
        len(parents) != 1
        or parents[0] != snapshot.harness_commit
        or _git_text(repository, "show", "-s", "--format=%s", head)
        != AUTHORIZATION_SUBJECT
        or changed != AUTHORIZATION_PATHS
    ):
        raise AuthorizationError("formal HEAD is not the exact authorization overlay")
    tree = _git_text(repository, "show", "-s", "--format=%T", head)
    executor = _executor_binding(repository, snapshot.harness_commit)
    review_raw, review_record, review_blob = _git_canonical_json(
        repository, head, EXECUTION_REVIEW_RELATIVE_PATH
    )
    expected_review = expected_execution_review(
        snapshot,
        authority_check_sha256=authority_check_sha256,
        command=command,
        executor=executor,
        rehearsal_aggregate=rehearsal_aggregate,
    )
    if review_record != expected_review or set(review_record) != {
        "findings",
        "reviewed_inputs",
        "reviewer_independence",
        "schema",
        "verdict",
    }:
        raise AuthorizationError("execution review is not the exact canonical five-key review")
    review_binding = {
        "bytes": len(review_raw),
        "git_blob_oid": review_blob["git_blob_oid"],
        "sha256": _sha256(review_raw),
        "verdict": EXECUTION_REVIEW_VERDICT,
    }
    authority_raw, authority_record, authority_blob = _git_canonical_json(
        repository, head, AUTHORITY_RELATIVE_PATH
    )
    request = authority_record.get("request")
    if not isinstance(request, dict):
        raise AuthorizationError("formal request is missing")
    request_id = request.get("request_id")
    attempt_id = request.get("attempt_id")
    if (
        not _is_lower_hex(request_id, 32)
        or not _is_lower_hex(attempt_id, 32)
        or request_id == attempt_id
    ):
        raise AuthorizationError("formal request identifiers are malformed")
    expected = expected_authorization(
        snapshot,
        authority_check_sha256,
        request_id=request_id,
        attempt_id=attempt_id,
        registry_root=registry_root,
        command=command,
        executor=executor,
        review=review_binding,
        rehearsal_aggregate=rehearsal_aggregate,
    )
    if authority_record != expected:
        raise AuthorizationError("formal authorization does not bind the sealed execution")
    return ValidatedAuthorization(
        attempt_id=attempt_id,
        authority_check_sha256=authority_check_sha256,
        binding={
            "bytes": len(authority_raw),
            "git_blob_oid": authority_blob["git_blob_oid"],
            "sha256": _sha256(authority_raw),
        },
        commit=head,
        command=command,
        request_id=request_id,
        review=review_binding,
        tree=tree,
    )


def _request_paths(
    registry_root: Path,
    request_id: str,
    attempt_id: str,
) -> tuple[Path, Path]:
    stem = f"{request_id}.{attempt_id}"
    return (
        registry_root / "claims" / f"{stem}.claim.json",
        registry_root / "receipts" / f"{stem}.receipt.json",
    )


def acquire_one_time_claim(
    validated: ValidatedAuthorization,
    snapshot: RepositorySnapshot,
    *,
    registry_root: Path,
    output_path: Path,
    work_root: Path,
) -> OneTimeClaim:
    claims = registry_root / "claims"
    receipts = registry_root / "receipts"
    for directory in (claims, receipts):
        directory.mkdir(exist_ok=True)
        if not directory.is_dir() or directory.is_symlink() or _is_reparse(directory):
            raise AuthorizationError("registry route is unsafe")
    # A same-filesystem directory create is the portable global mutex on
    # Windows (where advisory POSIX file locks are unavailable) and POSIX.  The
    # immutable claim itself is then created with ``xb`` while that mutex is
    # held, before any execution tree exists.
    lock = registry_root / "global-slot.lock"
    try:
        lock.mkdir(exist_ok=False)
    except FileExistsError as exc:
        raise AuthorizationError("global execution slot is occupied") from exc
    owner_path = lock / "owner.json"
    claim_path, receipt_path = _request_paths(
        registry_root, validated.request_id, validated.attempt_id
    )
    try:
        if any(claims.glob(f"{validated.request_id}.*.claim.json")) or any(
            receipts.glob(f"{validated.request_id}.*.receipt.json")
        ):
            raise AuthorizationError("one-time request ID was already consumed")
        if any(claims.glob(f"*.{validated.attempt_id}.claim.json")) or any(
            receipts.glob(f"*.{validated.attempt_id}.receipt.json")
        ):
            raise AuthorizationError("one-time attempt ID was already consumed")
        owner = {
            "attempt_id": validated.attempt_id,
            "authority_sha256": validated.binding["sha256"],
            "output_sha256": _location_sha256(output_path),
            "owner_pid": os.getpid(),
            "request_id": validated.request_id,
            "schema": "anysolver.ge-beam3-mixed-p2-global-slot-v1",
            "work_root_sha256": _location_sha256(work_root),
        }
        with owner_path.open("xb") as stream:
            stream.write(canonical_bytes(owner))
            stream.flush()
            os.fsync(stream.fileno())
        record = _expected_claim_record(
            validated,
            snapshot,
            output_path=output_path,
            work_root=work_root,
        )
        payload = canonical_bytes(record)
        with claim_path.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        _require_exact_regular_file(claim_path, payload, "one-time claim")
    except BaseException:
        if owner_path.exists():
            owner_path.unlink()
        lock.rmdir()
        raise
    return OneTimeClaim(
        binding={"bytes": len(payload), "sha256": _sha256(payload)},
        claim_path=claim_path,
        lock_path=lock,
        owner_path=owner_path,
        receipt_path=receipt_path,
    )


def _expected_claim_record(
    validated: ValidatedAuthorization,
    snapshot: RepositorySnapshot,
    *,
    output_path: Path,
    work_root: Path,
) -> dict[str, Any]:
    return {
        "attempt_id": validated.attempt_id,
        "authority_sha256": validated.binding["sha256"],
        "command_sha256": validated.command["sha256"],
        "harness_commit": snapshot.harness_commit,
        "output_sha256": _location_sha256(output_path),
        "request_id": validated.request_id,
        "runtime_sha256": _sha256(canonical_bytes(snapshot.runtime.record())),
        "schema": CLAIM_SCHEMA,
        "work_root_sha256": _location_sha256(work_root),
    }


def _validate_claim_file(
    claim: OneTimeClaim,
    validated: ValidatedAuthorization,
    snapshot: RepositorySnapshot,
    *,
    output_path: Path,
    work_root: Path,
) -> bytes:
    """Re-read the immutable claim before irreversible finalization."""

    if not _is_regular_nonreparse(claim.claim_path):
        raise AuthorizationError("one-time claim is missing or unsafe")
    raw, record = strict_canonical_json(claim.claim_path)
    binding = {"bytes": len(raw), "sha256": _sha256(raw)}
    if (
        binding != claim.binding
        or record
        != _expected_claim_record(
            validated,
            snapshot,
            output_path=output_path,
            work_root=work_root,
        )
    ):
        raise AuthorizationError("one-time claim changed after acquisition")
    return raw


def _release_slot(claim: OneTimeClaim) -> None:
    if claim.owner_path.exists():
        claim.owner_path.unlink()
    if claim.lock_path.exists():
        claim.lock_path.rmdir()


def write_terminal_receipt(
    claim: OneTimeClaim,
    validated: ValidatedAuthorization,
    snapshot: RepositorySnapshot,
    *,
    aggregate_core: dict[str, Any],
    output_path: Path,
    work_root: Path,
) -> tuple[bytes, dict[str, Any]]:
    _validate_recovery_core(
        aggregate_core,
        snapshot=snapshot,
        validated=validated,
        work_root=work_root,
    )
    _validate_claim_file(
        claim,
        validated,
        snapshot,
        output_path=output_path,
        work_root=work_root,
    )
    record = {
        "aggregate_core": aggregate_core,
        "attempt_id": validated.attempt_id,
        "claim": claim.binding,
        "intended_output": str(output_path.resolve()),
        "request_id": validated.request_id,
        "schema": RECEIPT_SCHEMA,
        "work_root": str(work_root.resolve()),
    }
    payload = canonical_bytes(record)
    with claim.receipt_path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    _require_exact_regular_file(claim.receipt_path, payload, "terminal receipt")
    return payload, {
        "bytes": len(payload),
        "sha256": _sha256(payload),
        "terminal": aggregate_core["terminal"],
    }


def _require_exact_regular_file(path: Path, payload: bytes, label: str) -> None:
    if not _is_regular_nonreparse(path) or path.read_bytes() != payload:
        raise AuthorizationError(f"{label} is unsafe or does not match its receipt")


def _publish_exclusive(
    output_path: Path,
    payload: bytes,
    attempt_id: str,
    *,
    recover: bool = False,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if (
        not output_path.parent.is_dir()
        or output_path.parent.is_symlink()
        or _is_reparse(output_path.parent)
    ):
        raise AuthorizationError("canonical output parent is unsafe")
    staging = output_path.with_name(f".{output_path.name}.{attempt_id}.pending")
    if _path_entry_exists(output_path):
        if not recover:
            raise ExclusiveOutputError("canonical output already exists")
        _require_exact_regular_file(output_path, payload, "canonical output")
        if _path_entry_exists(staging):
            _require_exact_regular_file(staging, payload, "pending publication")
            staging.unlink()
        return
    if _path_entry_exists(staging):
        if not recover:
            raise ExclusiveOutputError("pending publication already exists")
        _require_exact_regular_file(staging, payload, "pending publication")
    else:
        with staging.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    try:
        os.link(staging, output_path)
    except FileExistsError:
        if not recover:
            raise
        _require_exact_regular_file(output_path, payload, "canonical output")
    except BaseException:
        if _path_entry_exists(staging) and not recover:
            staging.unlink()
        raise
    _require_exact_regular_file(output_path, payload, "canonical output")
    if _path_entry_exists(staging):
        staging.unlink()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


@dataclass(frozen=True)
class MaterializedExecution:
    anyfileio: Path
    manifest_path: Path
    manifest_sha256: str
    root: Path
    solver: Path


def _materialization_record(snapshot: RepositorySnapshot) -> dict[str, Any]:
    return {
        "anyfileio": {
            "commit": snapshot.anyfileio.commit,
            "files": list(snapshot.anyfileio.tree_files),
            "tree": snapshot.anyfileio.tree,
        },
        "schema": MATERIALIZATION_SCHEMA,
        "solver": {
            "commit": snapshot.harness_commit,
            "files": list(snapshot.solver_files),
            "tree": snapshot.harness_tree,
        },
    }


def _materialize_git_tree(
    source: Path,
    destination: Path,
    *,
    commit: str,
    rows: Sequence[dict[str, Any]],
) -> None:
    # Local clone with --no-hardlinks gives the Windows runner an independent
    # object database.  Files are then populated from exact blobs rather than a
    # checkout, so autocrlf, attributes, filters, and working-tree substitutions
    # cannot rewrite the frozen bytes.
    try:
        subprocess.run(
            (
                "git",
                "--no-replace-objects",
                "clone",
                "--no-hardlinks",
                "--no-checkout",
                "--quiet",
                str(source.resolve()),
                str(destination.resolve()),
            ),
            cwd=destination.parent,
            env=_git_environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            check=True,
        )
        _git_bytes(destination, "update-ref", "--no-deref", "HEAD", commit)
        _git_bytes(destination, "read-tree", commit)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise BaselineError("failed to create closed-world Git materialization") from exc
    for row in rows:
        path = destination / row["path"]
        if path.exists():
            raise BaselineError("materialization destination was not exclusive")
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = _git_bytes(source, "cat-file", "blob", row["git_blob_oid"])
        if len(payload) != row["bytes"] or _sha256(payload) != row["sha256"]:
            raise BaselineError("source Git object changed during materialization")
        with path.open("xb") as stream:
            stream.write(payload)
        if row["mode"] == "100755":
            path.chmod(stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)


def materialize_execution(
    *,
    repository: Path,
    anyfileio_repository: Path,
    snapshot: RepositorySnapshot,
    work_root: Path,
) -> MaterializedExecution:
    materialized = work_root / "materialized"
    materialized.mkdir(parents=False, exist_ok=False)
    solver = materialized / "ANYsolver"
    anyfileio = materialized / "ANYfileIO"
    _materialize_git_tree(
        repository,
        solver,
        commit=snapshot.harness_commit,
        rows=snapshot.solver_files,
    )
    _materialize_git_tree(
        anyfileio_repository,
        anyfileio,
        commit=snapshot.anyfileio.commit,
        rows=snapshot.anyfileio.tree_files,
    )
    record = _materialization_record(snapshot)
    payload = canonical_bytes(record)
    manifest_path = work_root / "materialization.json"
    with manifest_path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    _require_exact_regular_file(manifest_path, payload, "materialization manifest")
    made = MaterializedExecution(
        anyfileio=anyfileio,
        manifest_path=manifest_path,
        manifest_sha256=_sha256(payload),
        root=materialized,
        solver=solver,
    )
    validate_materialization(made, snapshot)
    for root in (solver, anyfileio):
        for path in root.rglob("*"):
            if path.is_file() and ".git" not in path.relative_to(root).parts:
                path.chmod(stat.S_IREAD)
    return made


def _validate_materialized_tree(
    root: Path,
    *,
    commit: str,
    tree: str,
    rows: Sequence[dict[str, Any]],
) -> None:
    if (
        not root.is_dir()
        or root.is_symlink()
        or _is_reparse(root)
        or _git_text(root, "rev-parse", "HEAD") != commit
        or _git_text(root, "show", "-s", "--format=%T", "HEAD") != tree
        or _git_text(root, "status", "--porcelain=v1", "--untracked-files=all")
    ):
        raise BaselineError("materialized Git identity is not exact and clean")
    expected = {row["path"]: row for row in rows}
    observed: set[str] = set()
    for path in root.rglob("*"):
        relative_parts = path.relative_to(root).parts
        if relative_parts and relative_parts[0] == ".git":
            continue
        if path.is_symlink() or _is_reparse(path):
            raise BaselineError("materialization contains a link or reparse point")
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        observed.add(relative)
        row = expected.get(relative)
        if row is None:
            raise BaselineError("materialization contains an unregistered file")
        payload = path.read_bytes()
        if len(payload) != row["bytes"] or _sha256(payload) != row["sha256"]:
            raise BaselineError("materialized file bytes changed")
    if observed != set(expected):
        raise BaselineError("materialization inventory is incomplete")


def validate_materialization(
    made: MaterializedExecution,
    snapshot: RepositorySnapshot,
) -> None:
    raw, record = strict_canonical_json(made.manifest_path)
    if _sha256(raw) != made.manifest_sha256 or record != _materialization_record(snapshot):
        raise BaselineError("materialization manifest identity changed")
    _validate_materialized_tree(
        made.solver,
        commit=snapshot.harness_commit,
        tree=snapshot.harness_tree,
        rows=snapshot.solver_files,
    )
    _validate_materialized_tree(
        made.anyfileio,
        commit=snapshot.anyfileio.commit,
        tree=snapshot.anyfileio.tree,
        rows=snapshot.anyfileio.tree_files,
    )


def _runtime_search_roots() -> tuple[Path, ...]:
    roots: set[Path] = set()
    for _label, distribution, module in _runtime_distribution_specs():
        roots.add(
            Path(importlib_metadata.distribution(distribution).locate_file("")).resolve()
        )
        spec = importlib_util.find_spec(module)
        if spec is None or spec.origin is None:
            raise BaselineError(f"runtime import root is unavailable: {distribution}")
        if spec.submodule_search_locations:
            roots.update(Path(value).resolve().parent for value in spec.submodule_search_locations)
        else:
            roots.add(Path(spec.origin).resolve().parent)
    return tuple(sorted(roots, key=lambda path: os.path.normcase(str(path))))


ISOLATED_BOOTSTRAP = r'''
import hashlib,importlib.machinery,importlib.metadata,importlib.util,json,os,pathlib,platform,runpy,stat,sys,sysconfig
solver=pathlib.Path(sys.argv[1]).resolve(); dependency=pathlib.Path(sys.argv[2]).resolve()
runtime=json.loads(sys.argv[3]); bootstrap_sha=sys.argv[4]; root_count=int(sys.argv[5]); roots=[pathlib.Path(value).resolve() for value in sys.argv[6:6+root_count]]
script=pathlib.Path(sys.argv[6+root_count]).resolve(); arguments=sys.argv[7+root_count:]
sys.path[:0]=[str(solver/'src'),str(dependency/'src'),*[str(root) for root in roots]]
def sha(payload): return hashlib.sha256(payload).hexdigest().upper()
def canonical(value): return (json.dumps(value,allow_nan=False,ensure_ascii=True,separators=(',',':'),sort_keys=True)+'\n').encode('utf-8')
def location_sha(path): return sha(os.path.normcase(str(path.resolve())).encode('utf-8'))
def unsafe(path): return path.is_symlink() or bool(getattr(path.lstat(),'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0))
if bootstrap_sha!=runtime['bootstrap_sha256']: raise RuntimeError('bootstrap identity mismatch')
exe=pathlib.Path(sys.executable).resolve(); expected=runtime['interpreter']
if (not exe.is_file() or unsafe(exe) or sha(exe.read_bytes())!=expected['sha256'] or location_sha(exe)!=expected['executable_location_sha256'] or len(exe.read_bytes())!=expected['bytes'] or exe.name!=expected['executable_name'] or platform.python_version()!=expected['version'] or platform.python_implementation()!=expected['implementation'] or sys.implementation.cache_tag!=expected['cache_tag'] or (sysconfig.get_config_var('SOABI') or sys.implementation.cache_tag)!=expected['abi'] or sys.flags.optimize!=0): raise RuntimeError('interpreter identity mismatch')
bound_files=set(); bound_distributions={}
for expected_row in runtime['distributions']:
    matches=[]
    for candidate in importlib.metadata.distributions(name=expected_row['distribution']):
        candidate_root=pathlib.Path(candidate.locate_file('')).resolve(); candidate_files=list(candidate.files or ())
        if candidate_files and location_sha(candidate_root)==expected_row['distribution_root_sha256'] and candidate.version==expected_row['version']: matches.append((candidate,candidate_files))
    if len(matches)!=1: raise RuntimeError('distribution identity unavailable: '+expected_row['distribution'])
    dist,files=matches[0]; bound_distributions[expected_row['distribution'].casefold().replace('_','-')]=dist; spec=importlib.machinery.PathFinder.find_spec(expected_row['module'],sys.path)
    if spec is None or spec.origin is None: raise RuntimeError('distribution origin unavailable: '+expected_row['distribution'])
    root=pathlib.Path(dist.locate_file('')).resolve(); origin=pathlib.Path(spec.origin).resolve()
    if not origin.is_file() or unsafe(origin): raise RuntimeError('distribution origin unsafe')
    rows=[]; records=[]; folded=set()
    for registered in files:
        relative=str(registered).replace('\\','/'); key=relative.casefold(); target=pathlib.Path(dist.locate_file(registered)).resolve()
        if key in folded or not relative or pathlib.Path(relative).is_absolute() or not target.is_file() or unsafe(target): raise RuntimeError('distribution manifest unsafe')
        folded.add(key); payload=target.read_bytes(); rows.append({'bytes':len(payload),'path':relative,'sha256':sha(payload)}); bound_files.add(target)
        if relative.endswith('.dist-info/RECORD'): records.append(target)
    if len(records)!=1: raise RuntimeError('distribution RECORD ambiguous')
    rows.sort(key=lambda row:row['path']); locations=tuple(pathlib.Path(value).resolve() for value in (spec.submodule_search_locations or (origin.parent,)))
    if len(locations)!=1: raise RuntimeError('import root ambiguous')
    import_root=locations[0]
    if not import_root.is_dir() or unsafe(import_root): raise RuntimeError('import root unsafe')
    import_rows=[]; prefix=expected_row['module'].replace('.','/') if spec.submodule_search_locations else ''; candidates=import_root.rglob('*') if spec.submodule_search_locations else (origin,)
    for target in candidates:
        if not target.is_file(): continue
        relative_parts=target.relative_to(import_root).parts
        if '__pycache__' in relative_parts or target.suffix in ('.pyc','.pyo'): continue
        if unsafe(target): raise RuntimeError('import tree unsafe')
        payload=target.read_bytes(); logical='/'.join(part for part in (prefix,target.relative_to(import_root).as_posix()) if part); import_rows.append({'bytes':len(payload),'path':logical,'sha256':sha(payload)}); bound_files.add(target.resolve())
    import_rows.sort(key=lambda row:row['path'])
    if not import_rows: raise RuntimeError('import tree empty')
    try: origin_relative=origin.relative_to(import_root).as_posix()
    except ValueError as exc: raise RuntimeError('origin escapes import root') from exc
    origin_payload=origin.read_bytes()
    observed={'distribution':expected_row['distribution'],'distribution_root_sha256':location_sha(root),'file_count':len(rows),'file_manifest_sha256':sha(canonical(rows)),'import_file_count':len(import_rows),'import_manifest_sha256':sha(canonical(import_rows)),'import_root_location_sha256':location_sha(import_root),'import_total_bytes':sum(row['bytes'] for row in import_rows),'module':expected_row['module'],'origin_bytes':len(origin_payload),'origin_location_sha256':location_sha(origin),'origin_relative_sha256':sha(origin_relative.encode('utf-8')),'origin_sha256':sha(origin_payload),'record_sha256':sha(records[0].read_bytes()),'total_bytes':sum(row['bytes'] for row in rows),'version':dist.version}
    if observed!=expected_row: raise RuntimeError('distribution manifest mismatch')
_dll_handles=[]
if hasattr(os,'add_dll_directory'):
    for root in roots:
        candidate=root/'pywin32_system32'
        if candidate.is_dir(): _dll_handles.append(os.add_dll_directory(str(candidate)))
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name
def closure(seeds):
    pending=[canonicalize_name(name) for name in seeds]; visited=set()
    while pending:
        name=pending.pop()
        if name in visited: continue
        dist=bound_distributions.get(name) or importlib.metadata.distribution(name); visited.add(name)
        for raw in dist.requires or ():
            requirement=Requirement(raw); active=requirement.marker is None or requirement.marker.evaluate({'extra':''}); required=canonicalize_name(requirement.name)
            if active and required not in visited: pending.append(required)
    return sorted(visited)
labels={canonicalize_name(row['distribution']):row['distribution'] for row in runtime['distributions']}
if sorted(labels)!=closure(runtime['distribution_seeds']): raise RuntimeError('runtime closure mismatch')
if [labels[name] for name in closure(('pytest',))]!=runtime['pytest_transitive_closure']: raise RuntimeError('pytest closure mismatch')
if any(name in sys.modules for name in ('sitecustomize','usercustomize')): raise RuntimeError('ambient site customization loaded')
stdlib_roots=tuple(pathlib.Path(value).resolve() for value in {sysconfig.get_path('stdlib'),sysconfig.get_path('platstdlib')} if value)
dll_root=(pathlib.Path(sys.base_prefix)/'DLLs').resolve()
def permitted(path):
    path=path.resolve()
    if path in bound_files or path.is_relative_to(solver) or path.is_relative_to(dependency): return True
    if dll_root.is_dir() and path.is_relative_to(dll_root): return True
    for root in stdlib_roots:
        if path.is_relative_to(root) and not any(part.casefold() in ('site-packages','dist-packages') for part in path.relative_to(root).parts): return True
    return False
def check_spec(spec):
    origin=getattr(spec,'origin',None)
    if origin in (None,'built-in','frozen'): return
    path=pathlib.Path(origin).resolve()
    if not path.is_file() or unsafe(path) or not permitted(path): raise ImportError('unbound runtime module refused: '+str(getattr(spec,'name','UNKNOWN')))
class BoundPathFinder:
    @classmethod
    def find_spec(cls,fullname,path=None,target=None):
        spec=importlib.machinery.PathFinder.find_spec(fullname,path,target)
        if spec is not None: check_spec(spec)
        return spec
sys.meta_path=[BoundPathFinder if finder is importlib.machinery.PathFinder else finder for finder in sys.meta_path]
script.relative_to(solver)
sys.argv=[str(script),*arguments]
code=0
try: runpy.run_path(str(script),run_name='__main__')
except SystemExit as outcome: code=outcome.code if isinstance(outcome.code,int) else (0 if outcome.code is None else 1)
for name,module in tuple(sys.modules.items()):
    origin=getattr(module,'__file__',None)
    if origin and not permitted(pathlib.Path(origin)): raise RuntimeError('loaded module escaped bound runtime: '+name)
raise SystemExit(code)
'''.strip()


def _isolated_command(
    made: MaterializedExecution,
    snapshot: RepositorySnapshot,
    *,
    script_relative: str,
    arguments: Sequence[str],
) -> tuple[str, ...]:
    roots = _runtime_search_roots()
    return (
        sys.executable,
        "-I",
        "-S",
        "-B",
        "-c",
        ISOLATED_BOOTSTRAP,
        str(made.solver),
        str(made.anyfileio),
        canonical_bytes(snapshot.runtime.record()).decode("ascii").strip(),
        _sha256(ISOLATED_BOOTSTRAP.encode("utf-8")),
        str(len(roots)),
        *(str(path) for path in roots),
        str((made.solver / script_relative).resolve()),
        *arguments,
    )


def _child_environment(
    repository: Path,
    anyfileio_repository: Path,
    directory: Path,
) -> dict[str, str]:
    # Keep only variables required to locate the interpreter and core Windows
    # services.  In particular, ambient NUMBA/NPY/SCIPY/BLAS/JIT and ANY*
    # knobs must not silently alter a scientific lane.
    safe_names = {
        "COMSPEC",
        "PATH",
        "PATHEXT",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "WINDIR",
    }
    environment = {
        key: value for key, value in os.environ.items() if key.upper() in safe_names
    }
    for name in THREAD_VARIABLES:
        environment[name] = "1"
    solver_source = str((repository / "src").resolve())
    anyfileio_source = str((anyfileio_repository / "src").resolve())
    isolated_home = str(directory.resolve())
    home_drive, home_tail = os.path.splitdrive(isolated_home)
    environment["PYTHONPATH"] = solver_source + os.pathsep + anyfileio_source
    environment.update(
        {
            "APPDATA": str((directory / "appdata").resolve()),
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_KEY_0": "safe.directory",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_VALUE_0": str(repository.resolve()),
            "HOME": isolated_home,
            "HOMEDRIVE": home_drive,
            "HOMEPATH": home_tail,
            "LOCALAPPDATA": str((directory / "localappdata").resolve()),
            "PYTHONPYCACHEPREFIX": str((directory / "python-cache").resolve()),
            "PYTHONSAFEPATH": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONNOUSERSITE": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "Q1M_ANYFILEIO_ROOT": str(anyfileio_repository.resolve()),
            "TEMP": str(directory),
            "TMP": str(directory),
            "TMPDIR": str(directory),
            "USERPROFILE": isolated_home,
            "XDG_CACHE_HOME": str((directory / "xdg-cache").resolve()),
            "XDG_CONFIG_HOME": str((directory / "xdg-config").resolve()),
        }
    )
    return environment


# Windows children are created suspended, assigned to a kill-on-close Job
# Object with a hard aggregate-memory limit, then resumed.  POSIX children use
# a new session and inherited RLIMIT_AS; aggregate RSS is also monitored.
if os.name == "nt":
    WINDOWS_CREATE_SUSPENDED = 0x00000004

    class _IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class _JOB_BASIC_LIMIT(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD),
        ]

    class _JOB_EXTENDED_LIMIT(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _JOB_BASIC_LIMIT),
            ("IoInfo", _IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    class _JOB_ACCOUNTING(ctypes.Structure):
        _fields_ = [
            ("TotalUserTime", ctypes.c_longlong),
            ("TotalKernelTime", ctypes.c_longlong),
            ("ThisPeriodTotalUserTime", ctypes.c_longlong),
            ("ThisPeriodTotalKernelTime", ctypes.c_longlong),
            ("TotalPageFaultCount", wintypes.DWORD),
            ("TotalProcesses", wintypes.DWORD),
            ("ActiveProcesses", wintypes.DWORD),
            ("TotalTerminatedProcesses", wintypes.DWORD),
        ]

    _KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _NTDLL = ctypes.WinDLL("ntdll", use_last_error=True)
    _KERNEL32.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
    _KERNEL32.CreateJobObjectW.restype = wintypes.HANDLE
    _KERNEL32.SetInformationJobObject.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    )
    _KERNEL32.SetInformationJobObject.restype = wintypes.BOOL
    _KERNEL32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    _KERNEL32.AssignProcessToJobObject.restype = wintypes.BOOL
    _KERNEL32.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
    _KERNEL32.TerminateJobObject.restype = wintypes.BOOL
    _KERNEL32.QueryInformationJobObject.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    )
    _KERNEL32.QueryInformationJobObject.restype = wintypes.BOOL
    _KERNEL32.CloseHandle.argtypes = (wintypes.HANDLE,)
    _KERNEL32.CloseHandle.restype = wintypes.BOOL
    _NTDLL.NtResumeProcess.argtypes = (wintypes.HANDLE,)
    _NTDLL.NtResumeProcess.restype = ctypes.c_long


class _ProcessTree:
    def __init__(self, process: subprocess.Popen[bytes], memory_limit: int):
        self.process = process
        self.handle: int | None = None
        if os.name == "nt":
            handle = _KERNEL32.CreateJobObjectW(None, None)
            if not handle:
                raise OSError(ctypes.get_last_error(), "CreateJobObjectW failed")
            information = _JOB_EXTENDED_LIMIT()
            # JOB_OBJECT_LIMIT_JOB_MEMORY | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            information.BasicLimitInformation.LimitFlags = 0x00000200 | 0x00002000
            information.JobMemoryLimit = memory_limit
            configured = _KERNEL32.SetInformationJobObject(
                handle, 9, ctypes.byref(information), ctypes.sizeof(information)
            )
            assigned = configured and _KERNEL32.AssignProcessToJobObject(
                handle, wintypes.HANDLE(process._handle)  # type: ignore[attr-defined]
            )
            if not assigned:
                _KERNEL32.CloseHandle(handle)
                raise OSError(ctypes.get_last_error(), "AssignProcessToJobObject failed")
            self.handle = handle
            status = _NTDLL.NtResumeProcess(
                wintypes.HANDLE(process._handle)  # type: ignore[attr-defined]
            )
            if status != 0:
                self.terminate()
                raise OSError(f"NtResumeProcess failed with NTSTATUS {status:#x}")

    def metrics(self) -> tuple[int, int]:
        if os.name == "nt":
            if self.handle is None:
                return 0, 0
            accounting = _JOB_ACCOUNTING()
            extended = _JOB_EXTENDED_LIMIT()
            returned = wintypes.DWORD()
            ok_a = _KERNEL32.QueryInformationJobObject(
                self.handle,
                1,
                ctypes.byref(accounting),
                ctypes.sizeof(accounting),
                ctypes.byref(returned),
            )
            ok_e = _KERNEL32.QueryInformationJobObject(
                self.handle,
                9,
                ctypes.byref(extended),
                ctypes.sizeof(extended),
                ctypes.byref(returned),
            )
            if not ok_a or not ok_e:
                raise OSError(ctypes.get_last_error(), "QueryInformationJobObject failed")
            cpu_ns = int(accounting.TotalUserTime + accounting.TotalKernelTime) * 100
            return cpu_ns, int(extended.PeakJobMemoryUsed)
        return _posix_group_metrics(self.process.pid)

    def terminate(self) -> None:
        if os.name == "nt":
            if self.handle is not None:
                _KERNEL32.TerminateJobObject(self.handle, 2)
        else:
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                try:
                    self.process.kill()
                except ProcessLookupError:
                    pass

    def drain(self, timeout: float = 10.0) -> None:
        """Terminate and prove the complete group empty, even after leader exit."""

        self.terminate()
        deadline = time.monotonic() + timeout
        while True:
            if os.name == "nt":
                if self.handle is None:
                    raise RuntimeError("Windows Job Object is unavailable during drain")
                accounting = _JOB_ACCOUNTING()
                returned = wintypes.DWORD()
                ok = _KERNEL32.QueryInformationJobObject(
                    self.handle,
                    1,
                    ctypes.byref(accounting),
                    ctypes.sizeof(accounting),
                    ctypes.byref(returned),
                )
                if not ok:
                    raise OSError(ctypes.get_last_error(), "Job drain query failed")
                if accounting.ActiveProcesses == 0:
                    return
            else:
                try:
                    os.killpg(self.process.pid, 0)
                except ProcessLookupError:
                    return
                except PermissionError as exc:
                    raise RuntimeError("cannot prove POSIX process-group drainage") from exc
            if time.monotonic() >= deadline:
                raise RuntimeError("process tree did not drain")
            time.sleep(0.01)

    def close(self) -> None:
        if os.name == "nt" and self.handle is not None:
            # Kill-on-close also disposes a descendant neglected by pytest.
            _KERNEL32.CloseHandle(self.handle)
            self.handle = None


def _linux_process_group(root_pid: int) -> set[int]:
    if not sys.platform.startswith("linux"):
        return {root_pid}
    group: set[int] = set()
    proc = Path("/proc")
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / "stat").read_text(encoding="ascii").split()
            if int(fields[4]) == root_pid:
                group.add(int(fields[0]))
        except (OSError, ValueError, IndexError):
            continue
    return group or {root_pid}


def _posix_group_metrics(root_pid: int) -> tuple[int, int]:
    if not sys.platform.startswith("linux"):
        return 0, 0
    ticks = os.sysconf("SC_CLK_TCK")
    page_size = os.sysconf("SC_PAGE_SIZE")
    cpu_ticks = 0
    rss = 0
    for pid in _linux_process_group(root_pid):
        try:
            stat_fields = (Path("/proc") / str(pid) / "stat").read_text(
                encoding="ascii"
            ).split()
            statm = (Path("/proc") / str(pid) / "statm").read_text(
                encoding="ascii"
            ).split()
            cpu_ticks += int(stat_fields[13]) + int(stat_fields[14])
            rss += int(statm[1]) * page_size
        except (OSError, ValueError, IndexError):
            continue
    return int(cpu_ticks * 1_000_000_000 / ticks), rss


@dataclass(frozen=True)
class ProcessResult:
    forced_reason: str | None
    returncode: int | None
    tree_drained: bool = True


def run_bounded_process(
    command: Sequence[str],
    *,
    directory: Path,
    result_path: Path,
    environment: dict[str, str],
    bounds: ExecutionBounds,
    absolute_deadline: float,
    poll_seconds: float = 0.05,
) -> ProcessResult:
    directory.mkdir(parents=False, exist_ok=False)
    stdout_path = directory / "stdout.log"
    stderr_path = directory / "stderr.log"
    stdout_stream = stdout_path.open("xb")
    stderr_stream = stderr_path.open("xb")
    creationflags = 0
    launch_command = tuple(command)
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | WINDOWS_CREATE_SUSPENDED
    else:
        # A tiny exec wrapper applies RLIMIT_AS inside the new child.  Using
        # preexec_fn from concurrent coordinator threads is not fork-safe.
        limit_bootstrap = (
            "import os,resource,sys;"
            "limit=int(sys.argv[1]);"
            "resource.setrlimit(resource.RLIMIT_AS,(limit,limit));"
            "os.execvpe(sys.argv[2],sys.argv[2:],os.environ)"
        )
        launch_command = (
            sys.executable,
            "-I",
            "-S",
            "-c",
            limit_bootstrap,
            str(bounds.memory_limit_bytes),
            *launch_command,
        )
    process: subprocess.Popen[bytes] | None = None
    tree: _ProcessTree | None = None
    forced_reason: str | None = None
    tree_drained = False
    try:
        process = subprocess.Popen(
            launch_command,
            cwd=directory,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=stdout_stream,
            stderr=stderr_stream,
            creationflags=creationflags,
            start_new_session=os.name != "nt",
        )
        tree = _ProcessTree(process, bounds.memory_limit_bytes)
        started = time.monotonic()
        last_activity = started
        last_signature = (0, 0, 0)
        while process.poll() is None:
            now = time.monotonic()
            cpu_ns, memory = tree.metrics()
            signature = (
                stdout_path.stat().st_size,
                stderr_path.stat().st_size,
                cpu_ns,
            )
            if signature != last_signature:
                last_signature = signature
                last_activity = now
            if now >= absolute_deadline:
                forced_reason = "COMPLETE_WAVE_WALL_LIMIT"
            elif now - started > bounds.child_wall_seconds:
                forced_reason = "CHILD_WALL_LIMIT"
            elif memory > bounds.memory_limit_bytes:
                forced_reason = "PROCESS_TREE_MEMORY_LIMIT"
            elif now - last_activity > bounds.inactivity_seconds:
                forced_reason = "PROCESS_TREE_INACTIVITY_LIMIT"
            if forced_reason is not None:
                tree.terminate()
                break
            time.sleep(poll_seconds)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            forced_reason = forced_reason or "PROCESS_TREE_DRAIN_FAILURE"
            tree.terminate()
            process.wait(timeout=10)
        try:
            tree.drain()
            tree_drained = True
        except BaseException:
            forced_reason = forced_reason or "PROCESS_TREE_DRAIN_FAILURE"
        return ProcessResult(
            forced_reason=forced_reason,
            returncode=process.returncode,
            tree_drained=tree_drained,
        )
    except BaseException:
        if tree is not None:
            tree.terminate()
        elif process is not None and process.poll() is None:
            process.kill()
        if process is not None:
            try:
                process.wait(timeout=10)
            except (subprocess.TimeoutExpired, OSError):
                pass
        raise
    finally:
        if tree is not None:
            # Terminate any descendant that survived its pytest parent.
            if not tree_drained:
                try:
                    tree.drain()
                except BaseException:
                    pass
            tree.close()
        stdout_stream.close()
        stderr_stream.close()


class _PytestRecorder:
    def __init__(self, test_id: str):
        self.test_id = test_id
        self.nodeids: list[str] = []
        self.states: dict[str, str] = {}

    def pytest_collection_finish(self, session: Any) -> None:
        self.nodeids = [self._stable_id(item.nodeid) for item in session.items]

    def pytest_runtest_logreport(self, report: Any) -> None:
        node = self._stable_id(report.nodeid)
        previous = self.states.get(node)
        if report.failed:
            self.states[node] = "FAILED"
        elif report.skipped and previous != "FAILED":
            self.states[node] = "SKIPPED"
        elif report.when == "call" and report.passed and previous not in {"FAILED", "SKIPPED"}:
            self.states[node] = "PASSED"

    def _stable_id(self, nodeid: str) -> str:
        suffix = nodeid.split("::", 1)
        return self.test_id if len(suffix) == 1 else self.test_id + "::" + suffix[1]


def _worker(test_id: str, output: Path) -> int:
    if test_id not in TEST_BY_ID or output.exists():
        return 5
    test_file = ROOT / TEST_BY_ID[test_id].relative
    if not test_file.is_file() or test_file.is_symlink():
        return 5
    try:
        import pytest
    except Exception:
        return 6
    recorder = _PytestRecorder(test_id)
    code = pytest.main(
        [
            str(test_file),
            "-q",
            "--tb=short",
            "--disable-warnings",
            "-p",
            "no:cacheprovider",
        ],
        plugins=[recorder],
    )
    enum_by_exit = {
        0: "PASS",
        1: "TEST_FAILURE",
        2: "PROCESS_FAILURE",
        3: "PROCESS_FAILURE",
        4: "PROCESS_FAILURE",
        5: "PROCESS_FAILURE",
    }
    outcome = enum_by_exit.get(int(code), "PROCESS_FAILURE")
    counts = {
        "collected": len(recorder.nodeids),
        "failed": sum(state == "FAILED" for state in recorder.states.values()),
        "passed": sum(state == "PASSED" for state in recorder.states.values()),
        "skipped": sum(state == "SKIPPED" for state in recorder.states.values()),
    }
    if counts["collected"] == 0 or sum(counts[key] for key in ("failed", "passed", "skipped")) != counts["collected"]:
        outcome = "PROCESS_FAILURE"
    record = {
        "counts": counts,
        "node_ids_sha256": _sha256(canonical_bytes(recorder.nodeids)),
        "outcome": outcome,
        "schema": WORKER_SCHEMA,
        "test_id": test_id,
    }
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("xb") as stream:
            stream.write(canonical_bytes(record))
    except OSError:
        return 7
    return 0


def _runtime_import_audit_worker(output: Path) -> int:
    """Load every frozen lane without executing tests, for boundary testing."""

    if _path_entry_exists(output):
        return 5
    try:
        runtime_modules = (
            "anyfileio",
            "anygeometry",
            "anymaterial",
            "anymesher",
            "charset_normalizer",
            "llvmlite",
            "numba",
            "numpy",
            "pytest",
            "scipy",
            "threadpoolctl",
            "yaml",
        ) + (("win32api",) if sys.platform == "win32" else ()) + ("anysolver",)
        for module in runtime_modules:
            __import__(module)
        for index, relative in enumerate(
            (
                *(spec.relative for spec in FOCUSED_TESTS),
                PRODUCER_RELATIVE,
                CHECKER_RELATIVE,
            )
        ):
            runpy.run_path(
                str((ROOT / relative).resolve()),
                run_name=f"_ge_beam3_p2_import_audit_{index}",
            )
        record = {
            "candidate_id": CANDIDATE_ID,
            "loaded_lane_count": len(FOCUSED_TESTS) + 2,
            "schema": RUNTIME_IMPORT_AUDIT_SCHEMA,
            "study_id": STUDY_ID,
            "terminal": "NONCLASSIFYING_GE_BEAM3_P2_RUNTIME_IMPORT_AUDIT_PASS",
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("xb") as stream:
            stream.write(canonical_bytes(record))
        return 0
    except BaseException as exc:
        print(
            f"runtime import audit refused: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 6


def _validate_worker_record(
    path: Path, spec: TestSpec, process: ProcessResult
) -> dict[str, Any]:
    if process.forced_reason is not None:
        return {
            "finding_group": "PROCESS_OR_EVIDENCE",
            "outcome": "PROCESS_FAILURE",
            "passed": False,
            "reason": process.forced_reason,
            "test_id": spec.test_id,
        }
    if process.returncode != 0 or not path.is_file() or path.is_symlink():
        return {
            "finding_group": "PROCESS_OR_EVIDENCE",
            "outcome": "PROCESS_FAILURE",
            "passed": False,
            "reason": "WORKER_PROCESS_OR_OUTPUT_FAILURE",
            "test_id": spec.test_id,
        }
    try:
        raw, record = strict_canonical_json(path)
        if set(record) != {"counts", "node_ids_sha256", "outcome", "schema", "test_id"}:
            raise ValueError("worker keys")
        if record["schema"] != WORKER_SCHEMA or record["test_id"] != spec.test_id:
            raise ValueError("worker identity")
        counts = record["counts"]
        if (
            not isinstance(counts, dict)
            or set(counts) != {"collected", "failed", "passed", "skipped"}
            or any(type(value) is not int or value < 0 for value in counts.values())
            or counts["collected"] == 0
            or counts["failed"] + counts["passed"] + counts["skipped"] != counts["collected"]
            or not _is_hex(record["node_ids_sha256"], 64)
            or record["outcome"] not in {"PASS", "TEST_FAILURE", "PROCESS_FAILURE"}
        ):
            raise ValueError("worker values")
        if record["outcome"] == "PASS" and (
            counts["passed"] != counts["collected"]
            or counts["failed"] != 0
            or counts["skipped"] != 0
        ):
            raise ValueError("false pass")
        finding_group = (
            "NONE" if record["outcome"] == "PASS" else spec.finding_group
        )
        if record["outcome"] == "PROCESS_FAILURE":
            finding_group = "PROCESS_OR_EVIDENCE"
        return {
            "collected_count": counts["collected"],
            "finding_group": finding_group,
            "node_ids_sha256": record["node_ids_sha256"],
            "outcome": record["outcome"],
            "passed": record["outcome"] == "PASS",
            "record_sha256": _sha256(raw),
            "test_id": spec.test_id,
        }
    except (AuthorizationError, KeyError, TypeError, ValueError):
        return {
            "finding_group": "PROCESS_OR_EVIDENCE",
            "outcome": "PROCESS_FAILURE",
            "passed": False,
            "reason": "MALFORMED_WORKER_RECORD",
            "test_id": spec.test_id,
        }


def _run_one_test(
    made: MaterializedExecution,
    snapshot: RepositorySnapshot,
    directory: Path,
    spec: TestSpec,
    bounds: ExecutionBounds,
    absolute_deadline: float,
) -> dict[str, Any]:
    result_path = directory / "worker-result.json"
    try:
        validate_materialization(made, snapshot)
        if runtime_identity() != snapshot.runtime:
            raise BaselineError("runtime identity changed before worker launch")
    except (BaselineError, AuthorizationError):
        raise
    command = _isolated_command(
        made,
        snapshot,
        script_relative=RUNNER_RELATIVE,
        arguments=(
            "--worker",
            "--test-id",
            spec.test_id,
            "--output",
            str(result_path.resolve()),
        ),
    )
    try:
        process = run_bounded_process(
            command,
            directory=directory,
            result_path=result_path,
            environment=_child_environment(
                made.solver, made.anyfileio, directory
            ),
            bounds=bounds,
            absolute_deadline=absolute_deadline,
        )
    except BaseException:
        return {
            "finding_group": "PROCESS_OR_EVIDENCE",
            "outcome": "PROCESS_FAILURE",
            "passed": False,
            "reason": "WORKER_LAUNCH_OR_MONITOR_FAILURE",
            "test_id": spec.test_id,
        }
    return _validate_worker_record(result_path, spec, process)


def _program_process_failure(reason: str) -> dict[str, Any]:
    return {
        "checker_replica_count": 0,
        "checker_replicas_byte_identical": False,
        "finding_groups": ["PROCESS_OR_EVIDENCE"],
        "outcome": "PROCESS_FAILURE",
        "passed": False,
        "reason": reason,
        "raw_record_count": 0,
    }


def _run_program(
    command: Sequence[str],
    *,
    made: MaterializedExecution,
    snapshot: RepositorySnapshot,
    directory: Path,
    output: Path,
    bounds: ExecutionBounds,
    absolute_deadline: float,
) -> ProcessResult:
    validate_materialization(made, snapshot)
    if runtime_identity() != snapshot.runtime:
        raise BaselineError("runtime identity changed before program launch")
    return run_bounded_process(
        command,
        directory=directory,
        result_path=output,
        environment=_child_environment(made.solver, made.anyfileio, directory),
        bounds=bounds,
        absolute_deadline=absolute_deadline,
    )


def _validate_proof(
    path: Path,
    process: ProcessResult,
    snapshot: RepositorySnapshot,
) -> tuple[dict[str, Any] | None, bytes | None, dict[str, Any] | None]:
    if process.forced_reason is not None:
        return None, None, _program_process_failure(process.forced_reason)
    if process.returncode != 0 or not path.is_file() or path.is_symlink():
        return None, None, _program_process_failure("PRODUCER_PROCESS_OR_OUTPUT_FAILURE")
    try:
        raw, record = strict_canonical_json(path)
        if set(record) != {
            "bindings",
            "candidate_id",
            "content_sha256",
            "counts",
            "effective_recovery_case_ids",
            "predicates",
            "records",
            "schema",
            "study_id",
            "terminal",
        }:
            raise ValueError("proof fields")
        if (
            record["schema"] != PROOF_SCHEMA
            or record["study_id"] != STUDY_ID
            or record["candidate_id"] != CANDIDATE_ID
            or record["terminal"] != "NONCLASSIFYING_GE_BEAM3_P2_PROOF_COMPLETE"
            or record["bindings"] != snapshot.producer_input_bindings
            or record["counts"] != PROOF_COUNTS
            or record["effective_recovery_case_ids"] != list(RECOVERY_CASE_IDS)
            or record["predicates"]
            != {
                "producer_scientific_adjudication_present": False,
                "raw_binary64_values_encoded_little_endian": True,
            }
            or not _is_hex(record["content_sha256"], 64)
        ):
            raise ValueError("proof identity")
        body = dict(record)
        content_sha256 = body.pop("content_sha256")
        if content_sha256 != _sha256(canonical_bytes(body)):
            raise ValueError("proof self hash")
        records = record["records"]
        if (
            not isinstance(records, dict)
            or set(records) != {"load_mass_recovery", "modal_buckling", "solver_chart_state"}
            or any(not isinstance(value, list) for value in records.values())
            or any(len(records[key]) != PROOF_COUNTS[key] for key in records)
        ):
            raise ValueError("proof record coverage")
        case_ids: list[str] = []
        for group in ("solver_chart_state", "load_mass_recovery", "modal_buckling"):
            for item in records[group]:
                if not isinstance(item, dict) or not isinstance(item.get("case_id"), str):
                    raise ValueError("proof case record")
                case_ids.append(item["case_id"])
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("duplicate proof case ID")
        summary = {
            "bytes": len(raw),
            "content_sha256": content_sha256,
            "proof_sha256": _sha256(raw),
            "raw_record_count": PROOF_COUNTS["total"],
        }
        return summary, raw, None
    except (AuthorizationError, KeyError, TypeError, ValueError):
        return None, None, _program_process_failure("MALFORMED_PROOF_RECORD")


def _validate_check(
    path: Path,
    process: ProcessResult,
    *,
    proof_sha256: str,
    input_bindings: dict[str, dict[str, Any]],
) -> tuple[bytes | None, dict[str, Any]]:
    if process.forced_reason is not None:
        return None, _program_process_failure(process.forced_reason)
    if process.returncode not in {0, 2} or not path.is_file() or path.is_symlink():
        return None, _program_process_failure("CHECKER_PROCESS_OR_OUTPUT_FAILURE")
    try:
        raw, record = strict_canonical_json(path)
        common = {
            "bindings",
            "candidate_id",
            "counts",
            "finding_groups",
            "findings",
            "group_pass",
            "predicates",
            "proof_sha256",
            "schema",
            "study_id",
            "terminal",
        }
        terminal = record.get("terminal")
        expected_fields = common | ({"error_class"} if terminal == "NONCLASSIFYING_GE_BEAM3_P2_CHECK_MALFORMED_EVIDENCE" else set())
        if set(record) != expected_fields:
            raise ValueError("check fields")
        if (
            record["schema"] != CHECK_SCHEMA
            or record["study_id"] != STUDY_ID
            or record["candidate_id"] != CANDIDATE_ID
            or record["proof_sha256"] != proof_sha256
            or not isinstance(record["counts"], dict)
            or set(record["counts"]) != {"finding_count", "proof_record_count"}
            or any(type(value) is not int or value < 0 for value in record["counts"].values())
            or record["counts"]["proof_record_count"] not in {0, PROOF_COUNTS["total"]}
            or not isinstance(record["finding_groups"], list)
            or record["finding_groups"]
            != [group for group in SCIENTIFIC_GROUP_ORDER if group in record["finding_groups"]]
            or not isinstance(record["findings"], list)
            or record["counts"]["finding_count"] != len(record["findings"])
            or not isinstance(record["group_pass"], dict)
            or set(record["group_pass"]) != set(SCIENTIFIC_GROUP_ORDER)
            or any(type(value) is not bool for value in record["group_pass"].values())
            or not isinstance(record["predicates"], dict)
            or set(record["predicates"])
            != {"evidence_valid", "independent_recomputation_complete"}
            or any(type(value) is not bool for value in record["predicates"].values())
        ):
            raise ValueError("check identity")
        if terminal == "NONCLASSIFYING_GE_BEAM3_P2_CHECK_PASS":
            if (
                process.returncode != 0
                or record["bindings"] != input_bindings
                or record["counts"]
                != {"finding_count": 0, "proof_record_count": PROOF_COUNTS["total"]}
                or record["finding_groups"] != []
                or record["findings"] != []
                or not all(record["group_pass"].values())
                or record["predicates"]
                != {"evidence_valid": True, "independent_recomputation_complete": True}
            ):
                raise ValueError("false checker pass")
            outcome = "PASS"
        elif terminal == "NONCLASSIFYING_GE_BEAM3_P2_CHECK_SCIENTIFIC_FINDING":
            if (
                process.returncode != 2
                or record["bindings"] != input_bindings
                or record["counts"]["proof_record_count"] != PROOF_COUNTS["total"]
                or not record["finding_groups"]
                or not record["findings"]
                or record["predicates"]
                != {"evidence_valid": True, "independent_recomputation_complete": True}
                or record["finding_groups"]
                != [group for group in SCIENTIFIC_GROUP_ORDER if not record["group_pass"][group]]
            ):
                raise ValueError("malformed scientific finding")
            outcome = "SCIENTIFIC_FINDING"
        elif terminal == "NONCLASSIFYING_GE_BEAM3_P2_CHECK_MALFORMED_EVIDENCE":
            if (
                process.returncode != 2
                or record["bindings"] != {}
                or record["counts"] != {"finding_count": 0, "proof_record_count": 0}
                or record["predicates"]
                != {"evidence_valid": False, "independent_recomputation_complete": False}
                or not isinstance(record["error_class"], str)
            ):
                raise ValueError("malformed-evidence disposition")
            return raw, _program_process_failure("CHECKER_REJECTED_MALFORMED_PROOF")
        else:
            raise ValueError("unknown checker terminal")
        return raw, {
            "finding_groups": record["finding_groups"],
            "outcome": outcome,
            "passed": outcome == "PASS",
            "raw_record_count": record["counts"]["proof_record_count"],
        }
    except (AuthorizationError, KeyError, TypeError, ValueError):
        return None, _program_process_failure("MALFORMED_CHECKER_RECORD")


def _run_scientific_lane(
    made: MaterializedExecution,
    cycle_directory: Path,
    snapshot: RepositorySnapshot,
    *,
    bounds: ExecutionBounds,
    absolute_deadline: float,
) -> dict[str, Any]:
    producer_directory = cycle_directory / "raw-proof"
    proof_path = producer_directory / "proof.json"
    producer_command = (
        "--output", str(proof_path.resolve())
    )
    try:
        producer_process = _run_program(
            _isolated_command(
                made,
                snapshot,
                script_relative=PRODUCER_RELATIVE,
                arguments=producer_command,
            ),
            made=made,
            snapshot=snapshot,
            directory=producer_directory,
            output=proof_path,
            bounds=bounds,
            absolute_deadline=absolute_deadline,
        )
    except (BaselineError, AuthorizationError):
        raise
    except BaseException:
        return _program_process_failure("PRODUCER_LAUNCH_OR_MONITOR_FAILURE")
    proof_summary, _proof_raw, proof_error = _validate_proof(
        proof_path, producer_process, snapshot
    )
    if proof_error is not None or proof_summary is None:
        return proof_error or _program_process_failure("MALFORMED_PROOF_RECORD")

    def run_checker(replica: int) -> tuple[bytes | None, dict[str, Any]]:
        directory = cycle_directory / f"independent-check-{replica}"
        output = directory / "check.json"
        arguments = (
            "--proof",
            str(proof_path.resolve()),
            "--output",
            str(output.resolve()),
        )
        try:
            process = _run_program(
                _isolated_command(
                    made,
                    snapshot,
                    script_relative=CHECKER_RELATIVE,
                    arguments=arguments,
                ),
                made=made,
                snapshot=snapshot,
                directory=directory,
                output=output,
                bounds=bounds,
                absolute_deadline=absolute_deadline,
            )
        except (BaselineError, AuthorizationError):
            raise
        except BaseException:
            return None, _program_process_failure("CHECKER_LAUNCH_OR_MONITOR_FAILURE")
        return _validate_check(
            output,
            process,
            proof_sha256=proof_summary["proof_sha256"],
            input_bindings=snapshot.producer_input_bindings,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run_checker, replica) for replica in (1, 2)]
        checker_results = [future.result() for future in futures]
    raw_checks = [item[0] for item in checker_results]
    summaries = [item[1] for item in checker_results]
    byte_identical = (
        raw_checks[0] is not None
        and raw_checks[1] is not None
        and raw_checks[0] == raw_checks[1]
    )
    if not byte_identical or summaries[0] != summaries[1]:
        return {
            **_program_process_failure("CHECKER_REPLICA_DISAGREEMENT"),
            "checker_replica_count": 2,
            "proof": proof_summary,
        }
    summary = summaries[0]
    if summary["outcome"] == "PROCESS_FAILURE":
        return {
            **summary,
            "checker_replica_count": 2,
            "checker_replicas_byte_identical": True,
            "proof": proof_summary,
        }
    return {
        "checker_replica_count": 2,
        "checker_replicas_byte_identical": True,
        "checker_sha256": _sha256(raw_checks[0]),  # type: ignore[arg-type]
        "finding_groups": summary["finding_groups"],
        "outcome": summary["outcome"],
        "passed": summary["passed"],
        "proof": proof_summary,
        "raw_record_count": summary["raw_record_count"],
    }


def run_cycle(
    made: MaterializedExecution,
    cycle_directory: Path,
    *,
    snapshot: RepositorySnapshot,
    bounds: ExecutionBounds,
    absolute_deadline: float,
) -> dict[str, Any]:
    cycle_directory.mkdir(parents=False, exist_ok=False)
    records: dict[str, dict[str, Any]] = {}
    authority_failure: BaseException | None = None
    with ThreadPoolExecutor(max_workers=bounds.maximum_concurrent_workers) as pool:
        futures = {
            pool.submit(
                _run_one_test,
                made,
                snapshot,
                cycle_directory / spec.test_id.lower(),
                spec,
                bounds,
                absolute_deadline,
            ): spec
            for spec in FOCUSED_TESTS
        }
        for future in as_completed(futures):
            spec = futures[future]
            try:
                records[spec.test_id] = future.result()
            except (BaselineError, AuthorizationError) as exc:
                authority_failure = authority_failure or exc
                records[spec.test_id] = {
                    "finding_group": "BASELINE_OR_AUTHORITY",
                    "outcome": "PROCESS_FAILURE",
                    "passed": False,
                    "reason": "PRELAUNCH_IDENTITY_FAILURE",
                    "test_id": spec.test_id,
                }
            except BaseException:
                records[spec.test_id] = {
                    "finding_group": "PROCESS_OR_EVIDENCE",
                    "outcome": "PROCESS_FAILURE",
                    "passed": False,
                    "reason": "COORDINATOR_FAILURE",
                    "test_id": spec.test_id,
                }
    if authority_failure is not None:
        raise authority_failure
    ordered = [records[spec.test_id] for spec in FOCUSED_TESTS]
    if all(row["passed"] for row in ordered):
        scientific = _run_scientific_lane(
            made,
            cycle_directory,
            snapshot,
            bounds=bounds,
            absolute_deadline=absolute_deadline,
        )
    else:
        scientific = _program_process_failure(
            "SCIENTIFIC_LANE_NOT_LAUNCHED_AFTER_FOCUSED_GUARD"
        )
    return {
        "collected_count": sum(row.get("collected_count", 0) for row in ordered),
        "failed_test_file_count": sum(not row["passed"] for row in ordered),
        "passed_test_file_count": sum(row["passed"] for row in ordered),
        "scientific": scientific,
        "test_file_count": len(ordered),
        "tests": ordered,
    }


def adjudicate(test_records: Iterable[dict[str, Any]]) -> str:
    groups = {
        row.get("finding_group")
        for row in test_records
        if not bool(row.get("passed"))
    }
    if "BASELINE_OR_AUTHORITY" in groups:
        return TERMINAL_PRECEDENCE[0]
    if "PROCESS_OR_EVIDENCE" in groups:
        return TERMINAL_PRECEDENCE[1]
    if "SOLVER_CHART_OR_STATE" in groups:
        return TERMINAL_PRECEDENCE[2]
    if "LOAD_MASS_OR_RECOVERY" in groups:
        return TERMINAL_PRECEDENCE[3]
    if "MODAL_OR_BUCKLING" in groups:
        return TERMINAL_PRECEDENCE[4]
    return TERMINAL_PRECEDENCE[5]


def adjudicate_cycle(cycle: dict[str, Any]) -> str:
    records = list(cycle["tests"])
    scientific = cycle.get("scientific")
    if not isinstance(scientific, dict) or not scientific.get("passed", False):
        groups = (
            scientific.get("finding_groups", ["PROCESS_OR_EVIDENCE"])
            if isinstance(scientific, dict)
            else ["PROCESS_OR_EVIDENCE"]
        )
        records.extend(
            {"finding_group": group, "passed": False}
            for group in groups
        )
    return adjudicate(records)


def _valid_proof_summary(value: Any) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value)
        == {"bytes", "content_sha256", "proof_sha256", "raw_record_count"}
        and type(value.get("bytes")) is int
        and value["bytes"] > 0
        and _is_hex(value.get("content_sha256"), 64)
        and _is_hex(value.get("proof_sha256"), 64)
        and value.get("raw_record_count") == PROOF_COUNTS["total"]
    )


def _valid_scientific_summary(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    outcome = value.get("outcome")
    common = {
        "checker_replica_count",
        "checker_replicas_byte_identical",
        "finding_groups",
        "outcome",
        "passed",
        "raw_record_count",
    }
    if outcome == "PROCESS_FAILURE":
        if frozenset(value) not in {
            frozenset(common | {"reason"}),
            frozenset(common | {"reason", "proof"}),
        }:
            return False
        has_proof = "proof" in value
        return bool(
            type(value.get("checker_replica_count")) is int
            and value.get("checker_replica_count") == (2 if has_proof else 0)
            and type(value.get("checker_replicas_byte_identical")) is bool
            and (
                not has_proof
                and value.get("checker_replicas_byte_identical") is False
                or has_proof
                and value.get("checker_replicas_byte_identical") in {False, True}
            )
            and value.get("finding_groups") == ["PROCESS_OR_EVIDENCE"]
            and value.get("passed") is False
            and type(value.get("raw_record_count")) is int
            and value.get("raw_record_count") == 0
            and value.get("reason") in SCIENTIFIC_PROCESS_REASONS
            and (not has_proof or _valid_proof_summary(value["proof"]))
        )
    expected = common | {"checker_sha256", "proof"}
    if set(value) != expected or outcome not in {"PASS", "SCIENTIFIC_FINDING"}:
        return False
    groups = value.get("finding_groups")
    if not isinstance(groups, list) or groups != [
        group for group in SCIENTIFIC_GROUP_ORDER if group in groups
    ]:
        return False
    passing = outcome == "PASS"
    return bool(
        type(value.get("checker_replica_count")) is int
        and value.get("checker_replica_count") == 2
        and value.get("checker_replicas_byte_identical") is True
        and _is_hex(value.get("checker_sha256"), 64)
        and value.get("passed") is passing
        and type(value.get("raw_record_count")) is int
        and value.get("raw_record_count") == PROOF_COUNTS["total"]
        and _valid_proof_summary(value.get("proof"))
        and ((passing and groups == []) or (not passing and bool(groups)))
    )


def validate_cycle_record(
    cycle: dict[str, Any], snapshot: RepositorySnapshot
) -> str:
    """Validate a complete child-produced cycle before it can classify."""

    if set(cycle) != {
        "collected_count",
        "failed_test_file_count",
        "passed_test_file_count",
        "scientific",
        "test_file_count",
        "tests",
    }:
        raise EvidenceError("cycle record fields are malformed")
    tests = cycle.get("tests")
    if not isinstance(tests, list) or len(tests) != len(FOCUSED_TESTS):
        raise EvidenceError("cycle test coverage is malformed")
    passed = 0
    collected = 0
    for spec, row in zip(FOCUSED_TESTS, tests, strict=True):
        if not isinstance(row, dict):
            raise EvidenceError("cycle test record is malformed")
        binding = snapshot.test_bindings[spec.test_id]
        if (
            row.get("test_id") != spec.test_id
            or row.get("git_blob_oid") != binding["git_blob_oid"]
            or row.get("sha256") != binding["sha256"]
        ):
            raise EvidenceError("cycle test binding is malformed")
        if "reason" in row:
            reason = row.get("reason")
            expected_group = (
                "BASELINE_OR_AUTHORITY"
                if reason == "PRELAUNCH_IDENTITY_FAILURE"
                else "PROCESS_OR_EVIDENCE"
            )
            if (
                set(row)
                != {
                    "finding_group",
                    "git_blob_oid",
                    "outcome",
                    "passed",
                    "reason",
                    "sha256",
                    "test_id",
                }
                or row.get("finding_group") != expected_group
                or row.get("outcome") != "PROCESS_FAILURE"
                or row.get("passed") is not False
                or (
                    reason != "PRELAUNCH_IDENTITY_FAILURE"
                    and reason not in WORKER_PROCESS_REASONS
                )
            ):
                raise EvidenceError("cycle process record is malformed")
            continue
        if (
            set(row)
            != {
                "collected_count",
                "finding_group",
                "git_blob_oid",
                "node_ids_sha256",
                "outcome",
                "passed",
                "record_sha256",
                "sha256",
                "test_id",
            }
            or type(row.get("collected_count")) is not int
            or row["collected_count"] <= 0
            or not _is_hex(row.get("node_ids_sha256"), 64)
            or not _is_hex(row.get("record_sha256"), 64)
        ):
            raise EvidenceError("cycle pytest record is malformed")
        outcome = row.get("outcome")
        expected_group = {
            "PASS": "NONE",
            "TEST_FAILURE": spec.finding_group,
            "PROCESS_FAILURE": "PROCESS_OR_EVIDENCE",
        }.get(outcome)
        if (
            expected_group is None
            or row.get("finding_group") != expected_group
            or row.get("passed") is not (outcome == "PASS")
        ):
            raise EvidenceError("cycle pytest disposition is malformed")
        collected += row["collected_count"]
        passed += outcome == "PASS"
    scientific = cycle.get("scientific")
    guards_all_passed = passed == len(FOCUSED_TESTS)
    guard_skip_science = (
        isinstance(scientific, dict)
        and scientific.get("outcome") == "PROCESS_FAILURE"
        and scientific.get("reason")
        == "SCIENTIFIC_LANE_NOT_LAUNCHED_AFTER_FOCUSED_GUARD"
    )
    if (
        any(
            type(cycle.get(key)) is not int
            for key in (
                "collected_count",
                "failed_test_file_count",
                "passed_test_file_count",
                "test_file_count",
            )
        )
        or cycle.get("collected_count") != collected
        or cycle.get("failed_test_file_count") != len(FOCUSED_TESTS) - passed
        or cycle.get("passed_test_file_count") != passed
        or cycle.get("test_file_count") != len(FOCUSED_TESTS)
        or not _valid_scientific_summary(scientific)
        or (guards_all_passed and guard_skip_science)
        or (not guards_all_passed and not guard_skip_science)
    ):
        raise EvidenceError("cycle counts or scientific record are malformed")
    terminal = adjudicate_cycle(cycle)
    if terminal not in TERMINAL_PRECEDENCE:
        raise EvidenceError("cycle terminal is not registered")
    return terminal


def _decorate_cycle(
    cycle: dict[str, Any], snapshot: RepositorySnapshot
) -> dict[str, Any]:
    tests = []
    for row in cycle["tests"]:
        decorated = dict(row)
        decorated.update(snapshot.test_bindings[row["test_id"]])
        tests.append(decorated)
    return {**cycle, "tests": tests}


def _aggregate(
    *,
    mode: str,
    snapshot: RepositorySnapshot,
    cycle: dict[str, Any],
    cycle_hashes: list[str],
    cycles_byte_identical: bool,
    authority_check_sha256: str,
    authorization: ValidatedAuthorization | None,
    materialization_sha256: str | None,
) -> dict[str, Any]:
    if (mode == FORMAL_MODE) != (authorization is not None):
        raise AuthorizationError("aggregate authority does not match execution mode")
    terminal = adjudicate_cycle(cycle)
    if mode == REHEARSAL_MODE:
        terminal = (
            "NONCLASSIFYING_GE_BEAM3_P2_REHEARSAL_PASS"
            if terminal == TERMINAL_PRECEDENCE[-1]
            else "NONCLASSIFYING_GE_BEAM3_P2_REHEARSAL_FINDING"
        )
    elif terminal not in TERMINAL_PRECEDENCE[:2] and (
        not cycles_byte_identical
        or len(cycle_hashes) != 2
        or len(set(cycle_hashes)) != 1
    ):
        terminal = TERMINAL_PRECEDENCE[1]
    authority = {
        "authority_check_replica_count": 2,
        "authority_checks_byte_identical": True,
        "authority_check_sha256": authority_check_sha256,
        "formal_authorization_required": mode == FORMAL_MODE,
        "formal_authorization_validated": mode == FORMAL_MODE,
    }
    if authorization is not None:
        authority.update(
            {
                "authorization_commit": authorization.commit,
                "authorization_tree": authorization.tree,
                "command_sha256": authorization.command["sha256"],
                "review": authorization.review,
                "sha256": authorization.binding["sha256"],
            }
        )
    return {
        "authority": authority,
        "candidate_id": CANDIDATE_ID,
        "cycle_replica_count": len(cycle_hashes),
        "cycle_result_sha256": cycle_hashes,
        "cycle_results_byte_identical": cycles_byte_identical,
        "frozen_inputs": {
            "anyfileio": snapshot.anyfileio.record(),
            "harness_commit": snapshot.harness_commit,
            "harness_tree": snapshot.harness_tree,
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "implementation_review_commit": IMPLEMENTATION_REVIEW_COMMIT,
            "implementation_tree": IMPLEMENTATION_TREE,
            "manifest_sha256": snapshot.manifest_sha256,
            "materialization_sha256": materialization_sha256,
            "registry": snapshot.registry.record(),
            "recovery_correction_commit": RECOVERY_CORRECTION_COMMIT,
            "recovery_correction_tree": RECOVERY_CORRECTION_TREE,
            "runtime": snapshot.runtime.record(),
            "solver_tree": _manifest_identity(snapshot.solver_files),
        },
        "mode": mode,
        "result": cycle,
        "schema": AGGREGATE_SCHEMA,
        "study_id": STUDY_ID,
        "terminal": terminal,
    }


def _blocked_cycle(
    reason: str,
    finding_group: str = "PROCESS_OR_EVIDENCE",
) -> dict[str, Any]:
    scientific = _program_process_failure(reason)
    scientific["finding_groups"] = [finding_group]
    return {
        "collected_count": 0,
        "failed_test_file_count": 0,
        "passed_test_file_count": 0,
        "scientific": scientific,
        "test_file_count": 0,
        "tests": [],
    }


def _postclaim_failure_group(exc: BaseException) -> str:
    return (
        "BASELINE_OR_AUTHORITY"
        if isinstance(exc, (BaselineError, AuthorizationError))
        else "PROCESS_OR_EVIDENCE"
    )


def _required_cycle_count(mode: str, first_terminal: str) -> int:
    return (
        2
        if mode == FORMAL_MODE and first_terminal not in TERMINAL_PRECEDENCE[:2]
        else 1
    )


def _persist_cycle(directory: Path, cycle: dict[str, Any]) -> str:
    path = directory / "cycle-summary.json"
    payload = canonical_bytes(cycle)
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    _require_exact_regular_file(path, payload, "cycle summary")
    return _sha256(payload)


def _persist_blocked_cycle(work_root: Path, cycle: dict[str, Any]) -> str:
    """Persist the post-claim failure record used for publication recovery."""

    work_root.parent.mkdir(parents=True, exist_ok=True)
    work_root.mkdir(parents=False, exist_ok=True)
    path = work_root / "blocked-cycle-summary.json"
    payload = canonical_bytes(cycle)
    with path.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    _require_exact_regular_file(path, payload, "blocked-cycle summary")
    return _sha256(payload)


def _execute_frozen_cycles(
    made: MaterializedExecution,
    snapshot: RepositorySnapshot,
    *,
    mode: str,
    work_root: Path,
) -> tuple[dict[str, Any], list[str], bool]:
    deadline = time.monotonic() + FROZEN_BOUNDS.complete_wave_wall_seconds
    first = run_cycle(
        made,
        work_root / "cycle-1",
        snapshot=snapshot,
        bounds=FROZEN_BOUNDS,
        absolute_deadline=deadline,
    )
    first = _decorate_cycle(first, snapshot)
    first_terminal = validate_cycle_record(first, snapshot)
    first_hash = _persist_cycle(work_root / "cycle-1", first)
    hashes = [first_hash]
    identical = mode == REHEARSAL_MODE
    if _required_cycle_count(mode, first_terminal) == 2:
        second = run_cycle(
            made,
            work_root / "cycle-2",
            snapshot=snapshot,
            bounds=FROZEN_BOUNDS,
            absolute_deadline=deadline,
        )
        second = _decorate_cycle(second, snapshot)
        validate_cycle_record(second, snapshot)
        second_hash = _persist_cycle(work_root / "cycle-2", second)
        hashes.append(second_hash)
        identical = canonical_bytes(first) == canonical_bytes(second)
    return first, hashes, identical


def _with_consumption(
    core: dict[str, Any],
    *,
    claim: dict[str, Any],
    receipt: dict[str, Any],
    request_id: str,
    attempt_id: str,
) -> dict[str, Any]:
    return {
        **core,
        "consumption": {
            "attempt_id": attempt_id,
            "claim": claim,
            "receipt": receipt,
            "request_id": request_id,
        },
    }


def _is_embedded_blocked_cycle(cycle: dict[str, Any]) -> bool:
    if set(cycle) != {
        "collected_count",
        "failed_test_file_count",
        "passed_test_file_count",
        "scientific",
        "test_file_count",
        "tests",
    }:
        return False
    scientific = cycle.get("scientific")
    return bool(
        type(cycle.get("collected_count")) is int
        and cycle.get("collected_count") == 0
        and type(cycle.get("failed_test_file_count")) is int
        and cycle.get("failed_test_file_count") == 0
        and type(cycle.get("passed_test_file_count")) is int
        and cycle.get("passed_test_file_count") == 0
        and type(cycle.get("test_file_count")) is int
        and cycle.get("test_file_count") == 0
        and cycle.get("tests") == []
        and isinstance(scientific, dict)
        and set(scientific)
        == {
            "checker_replica_count",
            "checker_replicas_byte_identical",
            "finding_groups",
            "outcome",
            "passed",
            "reason",
            "raw_record_count",
        }
        and scientific.get("checker_replica_count") == 0
        and scientific.get("checker_replicas_byte_identical") is False
        and scientific.get("finding_groups")
        in (["BASELINE_OR_AUTHORITY"], ["PROCESS_OR_EVIDENCE"])
        and scientific.get("outcome") == "PROCESS_FAILURE"
        and scientific.get("passed") is False
        and _is_enum(scientific.get("reason"))
        and type(scientific.get("raw_record_count")) is int
        and scientific.get("raw_record_count") == 0
    )


def _validate_recovery_core(
    core: dict[str, Any],
    *,
    snapshot: RepositorySnapshot,
    validated: ValidatedAuthorization,
    work_root: Path,
) -> None:
    hashes = core.get("cycle_result_sha256")
    if not isinstance(hashes, list) or len(hashes) not in {1, 2}:
        raise AuthorizationError("terminal receipt cycle binding is malformed")
    cycle = core.get("result")
    if not isinstance(cycle, dict):
        raise AuthorizationError("terminal receipt result is malformed")
    materialization_sha = core.get("frozen_inputs", {}).get(
        "materialization_sha256"
    )
    try:
        expected_core = _aggregate(
            mode=FORMAL_MODE,
            snapshot=snapshot,
            cycle=cycle,
            cycle_hashes=hashes,
            cycles_byte_identical=core.get("cycle_results_byte_identical"),
            authority_check_sha256=validated.authority_check_sha256,
            authorization=validated,
            materialization_sha256=materialization_sha,
        )
    except (KeyError, TypeError, AuthorizationError) as exc:
        raise AuthorizationError("terminal receipt aggregate core is malformed") from exc
    if core != expected_core:
        raise AuthorizationError("terminal receipt aggregate core is not exact")
    synthetic_block = _is_embedded_blocked_cycle(cycle)
    if synthetic_block:
        if hashes != [_sha256(canonical_bytes(core.get("result")))]:
            raise AuthorizationError("receipt recovery blocked-result hash mismatch")
        if core.get("terminal") not in TERMINAL_PRECEDENCE[:2]:
            raise AuthorizationError("receipt recovery blocked terminal is malformed")
    else:
        if len(hashes) not in {1, 2} or any(
            not _is_hex(value, 64) for value in hashes
        ):
            raise AuthorizationError("receipt recovery cycle hashes are malformed")
        raw_cycles: list[bytes] = []
        terminals: list[str] = []
        for index, expected in enumerate(hashes, 1):
            path = work_root / f"cycle-{index}" / "cycle-summary.json"
            if not _is_regular_nonreparse(path):
                raise AuthorizationError("receipt recovery raw cycle is missing")
            raw, record = strict_canonical_json(path)
            if _sha256(raw) != expected:
                raise AuthorizationError("receipt recovery raw cycle hash mismatch")
            try:
                terminals.append(validate_cycle_record(record, snapshot))
            except EvidenceError as exc:
                raise AuthorizationError("receipt recovery cycle is malformed") from exc
            raw_cycles.append(raw)
        if raw_cycles[0] != canonical_bytes(cycle):
            raise AuthorizationError("receipt recovery selected cycle mismatch")
        first_classifies = terminals[0] not in TERMINAL_PRECEDENCE[:2]
        if first_classifies and len(raw_cycles) != 2:
            raise AuthorizationError("classifying result lacks two cycle records")
        if not first_classifies and len(raw_cycles) != 1:
            raise AuthorizationError("early blocked result has extra cycle records")
        identical = len(raw_cycles) == 2 and raw_cycles[0] == raw_cycles[1]
        if core.get("cycle_results_byte_identical") is not identical:
            raise AuthorizationError("cycle agreement disposition is malformed")
        expected_terminal = (
            terminals[0]
            if not first_classifies or identical
            else TERMINAL_PRECEDENCE[1]
        )
        if core.get("terminal") != expected_terminal:
            raise AuthorizationError("cycle terminal does not match raw evidence")
    if materialization_sha is None and synthetic_block:
        return
    if not _is_hex(materialization_sha, 64):
        raise AuthorizationError("receipt recovery materialization binding is missing")
    made = MaterializedExecution(
        anyfileio=work_root / "materialized" / "ANYfileIO",
        manifest_path=work_root / "materialization.json",
        manifest_sha256=materialization_sha,
        root=work_root / "materialized",
        solver=work_root / "materialized" / "ANYsolver",
    )
    validate_materialization(made, snapshot)


def recover_publication(
    *,
    validated: ValidatedAuthorization,
    snapshot: RepositorySnapshot,
    registry_root: Path,
    output_path: Path,
    work_root: Path,
) -> dict[str, Any] | None:
    claim_path, receipt_path = _request_paths(
        registry_root, validated.request_id, validated.attempt_id
    )
    pending_path = output_path.with_name(
        f".{output_path.name}.{validated.attempt_id}.pending"
    )
    if (
        not _path_entry_exists(claim_path)
        and not _path_entry_exists(receipt_path)
        and not _path_entry_exists(output_path)
        and not _path_entry_exists(pending_path)
    ):
        return None
    if not _is_regular_nonreparse(claim_path) or not _is_regular_nonreparse(
        receipt_path
    ):
        raise AuthorizationError("one-time request was consumed without a valid receipt")
    claim_raw, claim_record = strict_canonical_json(claim_path)
    if claim_record != _expected_claim_record(
        validated,
        snapshot,
        output_path=output_path,
        work_root=work_root,
    ):
        raise AuthorizationError("publication-recovery claim mismatch")
    receipt_raw, receipt_record = strict_canonical_json(receipt_path)
    if (
        set(receipt_record)
        != {
            "aggregate_core",
            "attempt_id",
            "claim",
            "intended_output",
            "request_id",
            "schema",
            "work_root",
        }
        or receipt_record["schema"] != RECEIPT_SCHEMA
        or receipt_record["request_id"] != validated.request_id
        or receipt_record["attempt_id"] != validated.attempt_id
        or receipt_record["claim"]
        != {"bytes": len(claim_raw), "sha256": _sha256(claim_raw)}
        or receipt_record["intended_output"] != str(output_path.resolve())
        or receipt_record["work_root"] != str(work_root.resolve())
    ):
        raise AuthorizationError("publication-recovery receipt mismatch")
    core = receipt_record["aggregate_core"]
    if not isinstance(core, dict):
        raise AuthorizationError("publication-recovery core is malformed")
    _validate_recovery_core(
        core,
        snapshot=snapshot,
        validated=validated,
        work_root=work_root,
    )
    receipt_binding = {
        "bytes": len(receipt_raw),
        "sha256": _sha256(receipt_raw),
        "terminal": core["terminal"],
    }
    result = _with_consumption(
        core,
        claim={"bytes": len(claim_raw), "sha256": _sha256(claim_raw)},
        receipt=receipt_binding,
        request_id=validated.request_id,
        attempt_id=validated.attempt_id,
    )
    _publish_exclusive(
        output_path,
        canonical_bytes(result),
        validated.attempt_id,
        recover=True,
    )
    return result


def run(
    *,
    mode: str,
    output_path: Path,
    work_root: Path,
    anyfileio_repository: Path | None = None,
    registry_root: Path | None = None,
    authority_check_paths: tuple[Path, Path] | None = None,
    rehearsal_aggregate_path: Path | None = None,
    repository: Path = ROOT,
) -> dict[str, Any]:
    if mode not in {REHEARSAL_MODE, FORMAL_MODE}:
        raise AuthorizationError("unknown execution mode")
    repository = repository.resolve()
    if anyfileio_repository is None:
        raise AuthorizationError("an explicit ANYfileIO repository is required")
    anyfileio_repository = anyfileio_repository.resolve()
    if registry_root is None:
        raise AuthorizationError("an explicit external registry root is required")
    registry_root = registry_root.resolve()
    if _same_path(repository, anyfileio_repository):
        raise AuthorizationError("ANYsolver and ANYfileIO repositories must be distinct")
    output_path = output_path.resolve()
    work_root = work_root.resolve()
    if (
        _is_within(output_path, repository)
        or _is_within(work_root, repository)
        or _is_within(output_path, anyfileio_repository)
        or _is_within(work_root, anyfileio_repository)
        or _is_within(output_path, registry_root)
        or _is_within(work_root, registry_root)
    ):
        raise ExclusiveOutputError("outputs must be outside the repository")
    if _is_within(output_path, work_root) or _is_within(work_root, output_path):
        raise ExclusiveOutputError("canonical aggregate and diagnostic root must be separate")
    for check_path in authority_check_paths or ():
        if _is_within(check_path, repository) or _is_within(
            check_path, anyfileio_repository
        ) or _is_within(check_path, registry_root):
            raise AuthorizationError("authority-check records must be external")
    if rehearsal_aggregate_path is not None:
        rehearsal_aggregate_path = rehearsal_aggregate_path.resolve()
        if (
            _is_within(rehearsal_aggregate_path, repository)
            or _is_within(rehearsal_aggregate_path, anyfileio_repository)
            or _is_within(rehearsal_aggregate_path, registry_root)
        ):
            raise AuthorizationError("rehearsal aggregate must be external")

    # All Git and authority checks precede any directory or child creation.
    if mode == FORMAL_MODE:
        head = _git_text(repository, "rev-parse", "HEAD")
        parents = _git_text(repository, "show", "-s", "--format=%P", head).split()
        if len(parents) != 1:
            raise AuthorizationError("formal HEAD must have exactly one parent")
        snapshot = validate_repository(
            repository,
            anyfileio_repository,
            registry_root,
            revision=parents[0],
            require_head=False,
        )
    else:
        snapshot = validate_repository(
            repository, anyfileio_repository, registry_root
        )
    authority_check_raw, _authority_check = validate_authority_checks(
        authority_check_paths, snapshot
    )
    authority_check_sha256 = _sha256(authority_check_raw)
    validated: ValidatedAuthorization | None = None
    if mode == FORMAL_MODE:
        if authority_check_paths is None:  # pragma: no cover - validated above
            raise AuthorizationError("formal authority-check records are required")
        rehearsal_aggregate = validate_rehearsal_aggregate(
            rehearsal_aggregate_path,
            snapshot,
            authority_check_sha256,
        )
        command = normalized_formal_command(
            repository=repository,
            anyfileio_repository=anyfileio_repository,
            registry_root=registry_root,
            authority_check_paths=authority_check_paths,
            rehearsal_aggregate_path=rehearsal_aggregate_path,
            work_root=work_root,
            output_path=output_path,
        )
        _attest_formal_cli(command)
        validated = validate_formal_overlay(
            repository=repository,
            snapshot=snapshot,
            authority_check_sha256=authority_check_sha256,
            command=command,
            registry_root=registry_root,
            rehearsal_aggregate=rehearsal_aggregate,
        )
        recovered = recover_publication(
            validated=validated,
            snapshot=snapshot,
            registry_root=registry_root,
            output_path=output_path,
            work_root=work_root,
        )
        if recovered is not None:
            return recovered
    if _path_entry_exists(output_path) or _path_entry_exists(work_root):
        raise ExclusiveOutputError("aggregate and diagnostic destinations must be fresh")

    if mode == REHEARSAL_MODE:
        work_root.parent.mkdir(parents=True, exist_ok=True)
        work_root.mkdir(parents=False, exist_ok=False)
        made = materialize_execution(
            repository=repository,
            anyfileio_repository=anyfileio_repository,
            snapshot=snapshot,
            work_root=work_root,
        )
        selected, hashes, identical = _execute_frozen_cycles(
            made, snapshot, mode=mode, work_root=work_root
        )
        core = _aggregate(
            mode=mode,
            snapshot=snapshot,
            cycle=selected,
            cycle_hashes=hashes,
            cycles_byte_identical=identical,
            authority_check_sha256=authority_check_sha256,
            authorization=None,
            materialization_sha256=made.manifest_sha256,
        )
        validate_materialization(made, snapshot)
        if validate_repository(
            repository, anyfileio_repository, registry_root
        ) != snapshot:
            raise BaselineError("frozen inputs changed during rehearsal")
        _publish_exclusive(output_path, canonical_bytes(core), "rehearsal")
        return core

    if validated is None:  # pragma: no cover - formal validation invariant
        raise AuthorizationError("formal execution authorization is unavailable")
    claim = acquire_one_time_claim(
        validated,
        snapshot,
        registry_root=registry_root,
        output_path=output_path,
        work_root=work_root,
    )
    made: MaterializedExecution | None = None
    try:
        work_root.parent.mkdir(parents=True, exist_ok=True)
        work_root.mkdir(parents=False, exist_ok=False)
        made = materialize_execution(
            repository=repository,
            anyfileio_repository=anyfileio_repository,
            snapshot=snapshot,
            work_root=work_root,
        )
        selected, hashes, identical = _execute_frozen_cycles(
            made, snapshot, mode=mode, work_root=work_root
        )
        core = _aggregate(
            mode=mode,
            snapshot=snapshot,
            cycle=selected,
            cycle_hashes=hashes,
            cycles_byte_identical=identical,
            authority_check_sha256=authority_check_sha256,
            authorization=validated,
            materialization_sha256=made.manifest_sha256,
        )
        validate_materialization(made, snapshot)
        final_snapshot = validate_repository(
            repository,
            anyfileio_repository,
            registry_root,
            revision=snapshot.harness_commit,
            require_head=False,
        )
        final_check_raw, _ = validate_authority_checks(
            authority_check_paths, final_snapshot
        )
        final_rehearsal = validate_rehearsal_aggregate(
            rehearsal_aggregate_path,
            final_snapshot,
            authority_check_sha256,
        )
        if (
            final_snapshot != snapshot
            or _sha256(final_check_raw) != authority_check_sha256
            or final_rehearsal != rehearsal_aggregate
        ):
            raise BaselineError("frozen inputs changed during formal execution")
        validate_formal_overlay(
            repository=repository,
            snapshot=snapshot,
            authority_check_sha256=authority_check_sha256,
            command=validated.command,
            registry_root=registry_root,
            rehearsal_aggregate=rehearsal_aggregate,
        )
    except BaseException as exc:
        blocked = _blocked_cycle(
            type(exc).__name__.upper(),
            _postclaim_failure_group(exc),
        )
        blocked_hash = _sha256(canonical_bytes(blocked))
        try:
            _persist_blocked_cycle(work_root, blocked)
        except (OSError, RunnerError):
            # The immutable terminal receipt embeds and hashes this result, so
            # publication recovery stays possible even when diagnostics cannot
            # be staged at the requested work root.
            pass
        blocked_materialization_sha: str | None = None
        if made is not None:
            try:
                validate_materialization(made, snapshot)
                blocked_materialization_sha = made.manifest_sha256
            except RunnerError:
                pass
        core = _aggregate(
            mode=mode,
            snapshot=snapshot,
            cycle=blocked,
            cycle_hashes=[blocked_hash],
            cycles_byte_identical=False,
            authority_check_sha256=authority_check_sha256,
            authorization=validated,
            materialization_sha256=blocked_materialization_sha,
        )
    try:
        try:
            receipt_raw, receipt_binding = write_terminal_receipt(
                claim,
                validated,
                snapshot,
                aggregate_core=core,
                output_path=output_path,
                work_root=work_root,
            )
        except BaseException as exc:
            # A failure before the immutable receipt exists is itself a formal
            # post-claim result.  Preserve terminal precedence and make one
            # bounded attempt to record that failure; an unsafe/pre-existing
            # receipt is never replaced.
            if _path_entry_exists(claim.receipt_path):
                raise
            blocked = _blocked_cycle(
                type(exc).__name__.upper(),
                _postclaim_failure_group(exc),
            )
            core = _aggregate(
                mode=mode,
                snapshot=snapshot,
                cycle=blocked,
                cycle_hashes=[_sha256(canonical_bytes(blocked))],
                cycles_byte_identical=False,
                authority_check_sha256=authority_check_sha256,
                authorization=validated,
                materialization_sha256=None,
            )
            receipt_raw, receipt_binding = write_terminal_receipt(
                claim,
                validated,
                snapshot,
                aggregate_core=core,
                output_path=output_path,
                work_root=work_root,
            )
        result = _with_consumption(
            core,
            claim=claim.binding,
            receipt=receipt_binding,
            request_id=validated.request_id,
            attempt_id=validated.attempt_id,
        )
        result_payload = canonical_bytes(result)
        # Re-read both registry records immediately before promotion.  A
        # cached binding is insufficient if an external actor substituted a
        # file while the formal children were running.
        _validate_claim_file(
            claim,
            validated,
            snapshot,
            output_path=output_path,
            work_root=work_root,
        )
        _require_exact_regular_file(
            claim.receipt_path, receipt_raw, "terminal receipt"
        )
        _publish_exclusive(output_path, result_payload, validated.attempt_id)
        return result
    finally:
        _release_slot(claim)


def run_nonclassifying_test_double(
    nonclassifying_factory: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    """Narrow test seam that can never emit formal evidence or terminals."""

    cycle = nonclassifying_factory()
    return {
        "candidate_id": CANDIDATE_ID,
        "result_sha256": _sha256(canonical_bytes(cycle)),
        "schema": TEST_DOUBLE_SCHEMA,
        "study_id": STUDY_ID,
        "terminal": "NONCLASSIFYING_GE_BEAM3_P2_TEST_DOUBLE_ONLY",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--rehearsal", action="store_true")
    modes.add_argument("--formal", action="store_true")
    modes.add_argument("--authority-check-only", action="store_true")
    modes.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    modes.add_argument(
        "--runtime-import-audit-worker", action="store_true", help=argparse.SUPPRESS
    )
    parser.add_argument("--repository", type=Path, default=ROOT)
    parser.add_argument("--anyfileio-repository", type=Path)
    parser.add_argument("--registry-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--authority-check-1", type=Path)
    parser.add_argument("--authority-check-2", type=Path)
    parser.add_argument("--rehearsal-aggregate", type=Path)
    parser.add_argument("--test-id", choices=tuple(TEST_BY_ID), help=argparse.SUPPRESS)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    global _ACTIVE_CLI_ARGV
    raw_arguments = list(sys.argv[1:] if argv is None else argv)
    arguments = _parser().parse_args(raw_arguments)
    if arguments.worker:
        if arguments.test_id is None:
            return 5
        return _worker(arguments.test_id, arguments.output)
    if arguments.runtime_import_audit_worker:
        return _runtime_import_audit_worker(arguments.output)
    if arguments.authority_check_only:
        try:
            write_authority_check(
                output_path=arguments.output,
                repository=arguments.repository,
                anyfileio_repository=arguments.anyfileio_repository,
                registry_root=arguments.registry_root,
            )
        except RunnerError as exc:
            print(f"GE Beam3 P2 authority check refused: {exc}", file=sys.stderr)
            return 2
        print(AUTHORITY_CHECK_TERMINAL)
        return 0
    if arguments.work_root is None:
        raise SystemExit("--work-root is required")
    mode = FORMAL_MODE if arguments.formal else REHEARSAL_MODE
    if arguments.formal and argv is None:
        _ACTIVE_CLI_ARGV = _actual_cli_argv(raw_arguments)
    try:
        result = run(
            mode=mode,
            output_path=arguments.output,
            work_root=arguments.work_root,
            anyfileio_repository=arguments.anyfileio_repository,
            registry_root=arguments.registry_root,
            authority_check_paths=(
                arguments.authority_check_1,
                arguments.authority_check_2,
            )
            if arguments.authority_check_1 is not None
            and arguments.authority_check_2 is not None
            else None,
            rehearsal_aggregate_path=arguments.rehearsal_aggregate,
            repository=arguments.repository,
        )
    except RunnerError as exc:
        print(f"GE Beam3 P2 runner refused execution: {exc}", file=sys.stderr)
        return 2
    finally:
        _ACTIVE_CLI_ARGV = None
    print(result["terminal"])
    return 0 if result["terminal"].endswith(("PASS", "PRIVATE_PARITY")) else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
