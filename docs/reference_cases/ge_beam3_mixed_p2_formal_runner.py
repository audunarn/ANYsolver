"""Bounded deterministic runner for the private GE Beam3 P2 parity gate.

The runner has deliberately narrow authority.  It executes seven frozen pytest
modules in isolated child processes and emits a path-free canonical summary.
Rehearsal output is nonclassifying.  Formal execution is impossible unless a
separately authored canonical authorization binds the exact Git-blob manifest.

This module creates neither execution authority nor scientific evidence.  A
caller chooses an external diagnostic directory and an exclusive aggregate
destination.  Raw pytest logs stay in the diagnostic directory; only stable
IDs, counts, booleans, hashes, and enums enter the aggregate.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any, Callable, Iterable, Sequence


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

REHEARSAL_MODE = "NONCLASSIFYING_REHEARSAL"
FORMAL_MODE = "FORMAL_TWO_CYCLE"
FORMAL_AUTHORIZATION_TERMINAL = "AUTHORIZED_GE_BEAM3_P2_FORMAL_EXECUTION"
AUTHORITY_CHECK_TERMINAL = "AUTHORITY_CHECK_ONLY_PASS"

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


class RunnerError(RuntimeError):
    """Base class for deliberate fail-closed runner errors."""


class BaselineError(RunnerError):
    """The frozen repository or Git-blob authority does not match."""


class AuthorizationError(RunnerError):
    """Formal execution is not authorized by an exact external record."""


class ExclusiveOutputError(RunnerError):
    """A supposedly fresh or exclusive destination already exists."""


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


def _git_environment() -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("GIT_")
    }
    environment.update(
        {
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


@dataclass(frozen=True)
class RepositorySnapshot:
    harness_commit: str
    harness_tree: str
    manifest_sha256: str
    producer_input_bindings: dict[str, dict[str, Any]]
    test_bindings: dict[str, dict[str, Any]]


def validate_repository(repository: Path = ROOT) -> RepositorySnapshot:
    repository = repository.resolve()
    _require_clean(repository)
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
    tree = _git_text(repository, "show", "-s", "--format=%T", "HEAD")
    try:
        subprocess.run(
            (
                "git",
                "-c",
                f"safe.directory={repository}",
                "merge-base",
                "--is-ancestor",
                IMPLEMENTATION_REVIEW_COMMIT,
                head,
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
                f"{IMPLEMENTATION_REVIEW_COMMIT}..{head}",
            ).splitlines()
            if line
        )
    )
    if extent != HARNESS_PATHS:
        raise BaselineError("formal-runner commit has a noncanonical path extent")
    manifest = [git_blob_binding(repository, head, path) for path in BOUND_PATHS]
    manifest_sha256 = _sha256(canonical_bytes(manifest))
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
        harness_commit=head,
        harness_tree=tree,
        manifest_sha256=manifest_sha256,
        producer_input_bindings=producer_input_bindings,
        test_bindings=test_bindings,
    )


def expected_authority_check(snapshot: RepositorySnapshot) -> dict[str, Any]:
    return {
        "candidate_id": CANDIDATE_ID,
        "checks": {
            "bound_inputs_are_git_blobs": True,
            "frozen_commit_chain_exact": True,
            "frozen_path_extents_exact": True,
            "harness_extent_exact": True,
            "implementation_review_exact": True,
            "repository_clean": True,
        },
        "frozen_inputs": {
            "harness_commit": snapshot.harness_commit,
            "harness_tree": snapshot.harness_tree,
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "implementation_review_commit": IMPLEMENTATION_REVIEW_COMMIT,
            "implementation_tree": IMPLEMENTATION_TREE,
            "manifest_sha256": snapshot.manifest_sha256,
            "recovery_correction_commit": RECOVERY_CORRECTION_COMMIT,
            "recovery_correction_tree": RECOVERY_CORRECTION_TREE,
        },
        "schema": AUTHORITY_CHECK_SCHEMA,
        "scientific_checker_replica_count": 2,
        "scientific_producer_count": 1,
        "study_id": STUDY_ID,
        "terminal": AUTHORITY_CHECK_TERMINAL,
        "test_file_count": len(FOCUSED_TESTS),
    }


def write_authority_check(
    *, output_path: Path, repository: Path = ROOT
) -> dict[str, Any]:
    repository = repository.resolve()
    output_path = output_path.resolve()
    if _is_within(output_path, repository):
        raise ExclusiveOutputError("authority-check output must be external")
    if output_path.exists():
        raise ExclusiveOutputError("authority-check output must be exclusive")
    snapshot = validate_repository(repository)
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


def expected_authorization(
    snapshot: RepositorySnapshot, authority_check_sha256: str
) -> dict[str, Any]:
    """Return the exact shape a separately authored authority must match."""

    return {
        "candidate_id": CANDIDATE_ID,
        "authority_check": {
            "replica_count": 2,
            "replicas_byte_identical": True,
            "sha256": authority_check_sha256,
        },
        "execution_bounds": FROZEN_BOUNDS.authority_record(),
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


def validate_authorization(
    path: Path | None,
    snapshot: RepositorySnapshot,
    authority_check_sha256: str,
) -> tuple[bytes, dict[str, Any]]:
    if path is None:
        raise AuthorizationError("formal mode requires a separate authorization JSON")
    resolved = path.resolve()
    if not resolved.is_file() or resolved.is_symlink():
        raise AuthorizationError("formal authorization must be a regular file")
    raw, record = strict_canonical_json(resolved)
    if record != expected_authorization(snapshot, authority_check_sha256):
        raise AuthorizationError("formal authorization does not bind the frozen harness")
    return raw, record


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _child_environment(repository: Path, directory: Path) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("GIT_")
        and key.upper() not in {"VIRTUAL_ENV", "PYTHONHASHSEED", "PYTHONDONTWRITEBYTECODE"}
    }
    for name in THREAD_VARIABLES:
        environment[name] = "1"
    source = str((repository / "src").resolve())
    inherited_pythonpath = os.environ.get("PYTHONPATH", "")
    environment["PYTHONPATH"] = (
        source
        if not inherited_pythonpath
        else source + os.pathsep + inherited_pythonpath
    )
    environment.update(
        {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_KEY_0": "safe.directory",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_CONFIG_VALUE_0": str(repository.resolve()),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONNOUSERSITE": "1",
            "TEMP": str(directory),
            "TMP": str(directory),
            "TMPDIR": str(directory),
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
        if self.process.poll() is not None and os.name != "nt":
            return
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
    preexec_fn: Callable[[], None] | None = None
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | WINDOWS_CREATE_SUSPENDED
    else:
        def _apply_limit() -> None:
            import resource

            resource.setrlimit(
                resource.RLIMIT_AS,
                (bounds.memory_limit_bytes, bounds.memory_limit_bytes),
            )

        preexec_fn = _apply_limit
    process: subprocess.Popen[bytes] | None = None
    tree: _ProcessTree | None = None
    forced_reason: str | None = None
    try:
        process = subprocess.Popen(
            tuple(command),
            cwd=directory,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=stdout_stream,
            stderr=stderr_stream,
            creationflags=creationflags,
            start_new_session=os.name != "nt",
            preexec_fn=preexec_fn,
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
        return ProcessResult(forced_reason=forced_reason, returncode=process.returncode)
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
            tree.terminate()
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


def _worker(test_id: str, test_file: Path, output: Path) -> int:
    if test_id not in TEST_BY_ID or output.exists():
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
    repository: Path,
    runner: Path,
    directory: Path,
    spec: TestSpec,
    bounds: ExecutionBounds,
    absolute_deadline: float,
) -> dict[str, Any]:
    result_path = directory / "worker-result.json"
    command = (
        sys.executable,
        str(runner),
        "--worker",
        "--test-id",
        spec.test_id,
        "--test-file",
        str((repository / spec.relative).resolve()),
        "--output",
        str(result_path.resolve()),
    )
    try:
        process = run_bounded_process(
            command,
            directory=directory,
            result_path=result_path,
            environment=_child_environment(repository, directory),
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
    repository: Path,
    directory: Path,
    output: Path,
    bounds: ExecutionBounds,
    absolute_deadline: float,
) -> ProcessResult:
    return run_bounded_process(
        command,
        directory=directory,
        result_path=output,
        environment=_child_environment(repository, directory),
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
    repository: Path,
    cycle_directory: Path,
    snapshot: RepositorySnapshot,
    *,
    bounds: ExecutionBounds,
    absolute_deadline: float,
) -> dict[str, Any]:
    producer_directory = cycle_directory / "raw-proof"
    proof_path = producer_directory / "proof.json"
    producer_command = (
        sys.executable,
        str((repository / PRODUCER_RELATIVE).resolve()),
        "--output",
        str(proof_path.resolve()),
    )
    try:
        producer_process = _run_program(
            producer_command,
            repository=repository,
            directory=producer_directory,
            output=proof_path,
            bounds=bounds,
            absolute_deadline=absolute_deadline,
        )
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
        command = (
            sys.executable,
            str((repository / CHECKER_RELATIVE).resolve()),
            "--proof",
            str(proof_path.resolve()),
            "--output",
            str(output.resolve()),
        )
        try:
            process = _run_program(
                command,
                repository=repository,
                directory=directory,
                output=output,
                bounds=bounds,
                absolute_deadline=absolute_deadline,
            )
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
    repository: Path,
    runner: Path,
    cycle_directory: Path,
    *,
    snapshot: RepositorySnapshot,
    bounds: ExecutionBounds,
    absolute_deadline: float,
) -> dict[str, Any]:
    cycle_directory.mkdir(parents=False, exist_ok=False)
    records: dict[str, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=bounds.maximum_concurrent_workers) as pool:
        futures = {
            pool.submit(
                _run_one_test,
                repository,
                runner,
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
            except BaseException:
                records[spec.test_id] = {
                    "finding_group": "PROCESS_OR_EVIDENCE",
                    "outcome": "PROCESS_FAILURE",
                    "passed": False,
                    "reason": "COORDINATOR_FAILURE",
                    "test_id": spec.test_id,
                }
    ordered = [records[spec.test_id] for spec in FOCUSED_TESTS]
    if all(row["passed"] for row in ordered):
        scientific = _run_scientific_lane(
            repository,
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
    authorization_sha256: str | None,
) -> dict[str, Any]:
    terminal = adjudicate_cycle(cycle)
    if mode == REHEARSAL_MODE:
        terminal = (
            "NONCLASSIFYING_GE_BEAM3_P2_REHEARSAL_PASS"
            if terminal == TERMINAL_PRECEDENCE[-1]
            else "NONCLASSIFYING_GE_BEAM3_P2_REHEARSAL_FINDING"
        )
    elif terminal == TERMINAL_PRECEDENCE[-1] and not cycles_byte_identical:
        terminal = TERMINAL_PRECEDENCE[1]
    authority = {
        "authority_check_replica_count": 2,
        "authority_checks_byte_identical": True,
        "authority_check_sha256": authority_check_sha256,
        "formal_authorization_required": mode == FORMAL_MODE,
        "formal_authorization_validated": mode == FORMAL_MODE,
    }
    if authorization_sha256 is not None:
        authority["sha256"] = authorization_sha256
    return {
        "authority": authority,
        "candidate_id": CANDIDATE_ID,
        "cycle_replica_count": len(cycle_hashes),
        "cycle_result_sha256": cycle_hashes,
        "cycle_results_byte_identical": cycles_byte_identical,
        "frozen_inputs": {
            "harness_commit": snapshot.harness_commit,
            "harness_tree": snapshot.harness_tree,
            "implementation_commit": IMPLEMENTATION_COMMIT,
            "implementation_review_commit": IMPLEMENTATION_REVIEW_COMMIT,
            "implementation_tree": IMPLEMENTATION_TREE,
            "manifest_sha256": snapshot.manifest_sha256,
            "recovery_correction_commit": RECOVERY_CORRECTION_COMMIT,
            "recovery_correction_tree": RECOVERY_CORRECTION_TREE,
        },
        "mode": mode,
        "result": cycle,
        "schema": AGGREGATE_SCHEMA,
        "study_id": STUDY_ID,
        "terminal": terminal,
    }


def run(
    *,
    mode: str,
    output_path: Path,
    work_root: Path,
    authorization_path: Path | None = None,
    authority_check_paths: tuple[Path, Path] | None = None,
    repository: Path = ROOT,
    bounds: ExecutionBounds = FROZEN_BOUNDS,
    cycle_runner: Callable[..., dict[str, Any]] = run_cycle,
) -> dict[str, Any]:
    if mode not in {REHEARSAL_MODE, FORMAL_MODE}:
        raise AuthorizationError("unknown execution mode")
    if bounds != FROZEN_BOUNDS:
        raise AuthorizationError("entry point requires the frozen execution bounds")
    repository = repository.resolve()
    output_path = output_path.resolve()
    work_root = work_root.resolve()
    if _is_within(output_path, repository) or _is_within(work_root, repository):
        raise ExclusiveOutputError("outputs must be outside the repository")
    if _is_within(output_path, work_root):
        raise ExclusiveOutputError("canonical aggregate and diagnostic root must be separate")
    if output_path.exists() or work_root.exists():
        raise ExclusiveOutputError("aggregate and diagnostic destinations must be fresh")
    for check_path in authority_check_paths or ():
        if _is_within(check_path, repository):
            raise AuthorizationError("authority-check records must be external")
    if authorization_path is not None and _is_within(authorization_path, repository):
        raise AuthorizationError("formal authorization must be external")

    # All Git and authority checks precede any directory or child creation.
    snapshot = validate_repository(repository)
    authority_check_raw, _authority_check = validate_authority_checks(
        authority_check_paths, snapshot
    )
    authority_check_sha256 = _sha256(authority_check_raw)
    authorization_sha256: str | None = None
    if mode == FORMAL_MODE:
        authority_raw, _authority = validate_authorization(
            authorization_path,
            snapshot,
            authority_check_sha256,
        )
        authorization_sha256 = _sha256(authority_raw)
    elif authorization_path is not None:
        raise AuthorizationError("rehearsal mode cannot consume formal authorization")

    work_root.parent.mkdir(parents=True, exist_ok=True)
    work_root.mkdir(parents=False, exist_ok=False)
    deadline = time.monotonic() + bounds.complete_wave_wall_seconds
    runner = (repository / RUNNER_RELATIVE).resolve()
    first = cycle_runner(
        repository,
        runner,
        work_root / "cycle-1",
        snapshot=snapshot,
        bounds=bounds,
        absolute_deadline=deadline,
    )
    first = _decorate_cycle(first, snapshot)
    first_raw = canonical_bytes(first)
    cycle_hashes = [_sha256(first_raw)]
    cycles_byte_identical = mode == REHEARSAL_MODE
    selected = first
    if mode == FORMAL_MODE and adjudicate_cycle(first) == TERMINAL_PRECEDENCE[-1]:
        second = cycle_runner(
            repository,
            runner,
            work_root / "cycle-2",
            snapshot=snapshot,
            bounds=bounds,
            absolute_deadline=deadline,
        )
        second = _decorate_cycle(second, snapshot)
        second_raw = canonical_bytes(second)
        cycle_hashes.append(_sha256(second_raw))
        cycles_byte_identical = first_raw == second_raw
    aggregate = _aggregate(
        mode=mode,
        snapshot=snapshot,
        cycle=selected,
        cycle_hashes=cycle_hashes,
        cycles_byte_identical=cycles_byte_identical,
        authority_check_sha256=authority_check_sha256,
        authorization_sha256=authorization_sha256,
    )
    # A concurrent working-tree or ref mutation invalidates the complete run;
    # raw diagnostics remain, but no canonical aggregate may be published.
    if validate_repository(repository) != snapshot:
        raise BaselineError("repository identity changed during execution")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("xb") as stream:
        stream.write(canonical_bytes(aggregate))
    return aggregate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--rehearsal", action="store_true")
    modes.add_argument("--formal", action="store_true")
    modes.add_argument("--authority-check-only", action="store_true")
    modes.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--repository", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-root", type=Path)
    parser.add_argument("--authorization", type=Path)
    parser.add_argument("--authority-check-1", type=Path)
    parser.add_argument("--authority-check-2", type=Path)
    parser.add_argument("--test-id", choices=tuple(TEST_BY_ID), help=argparse.SUPPRESS)
    parser.add_argument("--test-file", type=Path, help=argparse.SUPPRESS)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.worker:
        if arguments.test_id is None or arguments.test_file is None:
            return 5
        return _worker(arguments.test_id, arguments.test_file, arguments.output)
    if arguments.authority_check_only:
        try:
            write_authority_check(
                output_path=arguments.output,
                repository=arguments.repository,
            )
        except RunnerError as exc:
            print(f"GE Beam3 P2 authority check refused: {exc}", file=sys.stderr)
            return 2
        print(AUTHORITY_CHECK_TERMINAL)
        return 0
    if arguments.work_root is None:
        raise SystemExit("--work-root is required")
    mode = FORMAL_MODE if arguments.formal else REHEARSAL_MODE
    try:
        result = run(
            mode=mode,
            output_path=arguments.output,
            work_root=arguments.work_root,
            authorization_path=arguments.authorization,
            authority_check_paths=(
                arguments.authority_check_1,
                arguments.authority_check_2,
            )
            if arguments.authority_check_1 is not None
            and arguments.authority_check_2 is not None
            else None,
            repository=arguments.repository,
        )
    except RunnerError as exc:
        print(f"GE Beam3 P2 runner refused execution: {exc}", file=sys.stderr)
        return 2
    print(result["terminal"])
    return 0 if result["terminal"].endswith(("PASS", "PRIVATE_PARITY")) else 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
