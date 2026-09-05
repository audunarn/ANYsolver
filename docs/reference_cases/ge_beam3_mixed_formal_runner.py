"""Bounded two-cycle orchestration for the private GE Beam3 mixed gate.

This module deliberately imports only the Python standard library.  Producer
and checker programs are child processes and are hash-bound by an external
execution-authority record before either program can start.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import ctypes
from ctypes import wintypes
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import signal
import stat
import subprocess
import sys
import time
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
PRODUCER = ROOT / "docs" / "reference_cases" / "ge_beam3_mixed_finite_producer.py"
CHECKER = ROOT / "docs" / "reference_cases" / "ge_beam3_mixed_finite_checker.py"
RUNNER = Path(__file__).resolve()

STUDY_ID = "study_ge_beam3.dc_mixed_k1_macro_v2"
CANDIDATE_ID = "CANDIDATE_GE_BEAM3_DC_MIXED_K1_MACRO_V2"
AUTHORITY_SCHEMA = "anysolver.ge-beam3-mixed-execution-authority-v1"
REHEARSAL_AUTHORITY_SCHEMA = "anysolver.ge-beam3-mixed-rehearsal-authority-v1"
AUTHORITY_CHECK_SCHEMA = "anysolver.ge-beam3-mixed-authority-check-v1"
AGGREGATE_SCHEMA = "anysolver.ge-beam3-mixed-formal-aggregate-v1"
CHECK_SCHEMA = "anysolver.ge-beam3-mixed-finite-check-v2"

FORMAL_MODE = "FORMAL_TWO_CYCLE"
REHEARSAL_MODE = "NONCLASSIFYING_REHEARSAL"
FORMAL_AUTHORITY_TERMINAL = "AUTHORIZED_GE_BEAM3_MIXED_TWO_CYCLE_EXECUTION"
REHEARSAL_AUTHORITY_TERMINAL = "NONCLASSIFYING_GE_BEAM3_MIXED_REHEARSAL_ONLY"

BASE_COMMIT = "09351645ba17a0a5b130a1c7a48007d36dd08ada"
MECHANICS_COMMIT = "ce6f460109bcec4253da044397222704c48cec1d"
MECHANICS_TREE = "0b1666ea7b55d2fcd495b60c347a7f4472c434c0"
AUTHORIZATION_SUBJECT = "docs: authorize GE Beam3 mixed formal cycles"
AUTHORITY_RELATIVE_PATH = "docs/reference_cases/ge_beam3_mixed_execution_authority.json"
REVIEW_RELATIVE_PATH = "docs/reference_cases/ge_beam3_mixed_execution_review.json"
AUTHORIZATION_PATHS = (AUTHORITY_RELATIVE_PATH, REVIEW_RELATIVE_PATH)
REVIEW_SCHEMA = "anysolver.ge-beam3-mixed-execution-review-v1"
REVIEW_VERDICT = "ACCEPT_GE_BEAM3_MIXED_FORMAL_EXECUTION_NO_P0_P1"
REVIEWER_INDEPENDENCE = {
    "mechanics_executed": False,
    "review_method": "CANONICAL_GIT_BLOB_MANIFEST_AND_NEGATIVE_AUTHORITY_REVIEW",
    "reviewed_input_authorship": False,
    "role": "INDEPENDENT_GE_BEAM3_MIXED_EXECUTION_REVIEWER",
}

SOURCE_INPUT_PATHS = (
    "docs/reference_cases/ge_beam3_mixed_baseline.json",
    "docs/reference_cases/ge_beam3_mixed_equation_map_a.json",
    "docs/reference_cases/ge_beam3_mixed_equation_map_b.json",
    "docs/reference_cases/ge_beam3_mixed_local_contract.json",
    "docs/reference_cases/ge_beam3_mixed_source_ledger.json",
    "docs/reference_cases/ge_beam3_mixed_status.json",
)
PROGRAM_PATHS = (
    "docs/reference_cases/ge_beam3_mixed_authority_runner.py",
    "docs/reference_cases/ge_beam3_mixed_exact_reference.py",
    "docs/reference_cases/ge_beam3_mixed_finite_checker.py",
    "docs/reference_cases/ge_beam3_mixed_finite_producer.py",
    "docs/reference_cases/ge_beam3_mixed_formal_runner.py",
    "docs/reference_cases/ge_beam3_mixed_independent_checker.py",
    "src/anysolver/_ge_beam3_mixed_ad.py",
    "src/anysolver/ge_beam3_mixed_element.py",
)
TEST_PATHS = (
    "tests/test_ge_beam3_mixed_authority_runner.py",
    "tests/test_ge_beam3_mixed_core.py",
    "tests/test_ge_beam3_mixed_exact_reference.py",
    "tests/test_ge_beam3_mixed_finite_gate.py",
    "tests/test_ge_beam3_mixed_formal_runner.py",
    "tests/test_ge_beam3_mixed_independent_checker.py",
)
CANDIDATE_PATHS = tuple(sorted(SOURCE_INPUT_PATHS + PROGRAM_PATHS + TEST_PATHS))
PATH_ROLES = {
    **{path: "SOURCE_INPUT" for path in SOURCE_INPUT_PATHS},
    **{path: "PROGRAM" for path in PROGRAM_PATHS},
    **{path: "TEST" for path in TEST_PATHS},
}

AUTHORITY_CHECK_FIELDS = {
    "base_checks",
    "base_blob_checks",
    "candidate_boundary_checks",
    "candidate_extent",
    "candidate_extent_components",
    "candidate_id",
    "current_boundary_checks",
    "current_protected_blob_checks",
    "equation_route_checks",
    "exact_agreement",
    "input_hashes",
    "input_git_blob_oids",
    "input_validation_checks",
    "input_working_hashes",
    "policy_checks",
    "pytest_diagnostic_exclusion_policy",
    "record_identity_checks",
    "schema",
    "source_checks",
    "source_semantic_checks",
    "source_verification_mode",
    "study_id",
    "terminal",
}
AUTHORITY_BOOLEAN_GROUPS = (
    "base_checks",
    "base_blob_checks",
    "candidate_boundary_checks",
    "current_boundary_checks",
    "current_protected_blob_checks",
    "equation_route_checks",
    "exact_agreement",
    "input_validation_checks",
    "policy_checks",
    "record_identity_checks",
    "source_checks",
    "source_semantic_checks",
)

AUTHORITY_INPUT_NAMES = tuple(Path(path).name for path in SOURCE_INPUT_PATHS)
AUTHORITY_BOOLEAN_GROUP_FIELDS: dict[str, set[str]] = {
    "base_checks": {
        "archive_ref_exact",
        "archive_ref_resolves_to_v1",
        "base_commit_exists",
        "base_tree",
        "baseline_base_exact",
        "head_descends_from_base",
        "v1_closeout_exact",
        "v1_commit_exists",
        "v1_terminal_preserved",
    },
    "base_blob_checks": {
        "ledger_rows_exact",
        "src/anysolver/__init__.py",
        "src/anysolver/_native_rotation_state.py",
        "src/anysolver/beam_sections.py",
        "src/anysolver/corotational.py",
        "src/anysolver/current_state_tangent.py",
        "src/anysolver/elements.py",
    },
    "candidate_boundary_checks": {
        "complete_extent_exact",
        "every_allowed_path_is_regular",
        "no_existing_path_in_candidate_extent",
    },
    "current_boundary_checks": {
        "all_protected_current_blobs_equal_base",
        "no_candidate_token_in_public_or_assembly_routes",
        "protected_path_set_complete",
    },
    "current_protected_blob_checks": {
        "pyproject.toml",
        "src/anysolver/__init__.py",
        "src/anysolver/_native_rotation_state.py",
        "src/anysolver/beam_sections.py",
        "src/anysolver/corotational.py",
        "src/anysolver/current_state_tangent.py",
        "src/anysolver/elements.py",
        "src/anysolver/matrix_assembly.py",
        "src/anysolver/nonlinear_element_evaluation.py",
        "src/anysolver/nonlinear_static.py",
    },
    "equation_route_checks": {
        "map_a_reference_routes",
        "map_b_artifact",
        "map_b_cell_functional_route",
        "map_b_equation_audit",
        "map_b_reference_jump_route",
        "map_b_source_id",
    },
    "exact_agreement": {"condensed_hash", "counts", "predicates", "section_hash"},
    "policy_checks": {
        "authority_state_is_draft",
        "baseline_production_boundary",
        "candidate_is_two_cell_macro",
        "contract_production_boundary",
        "execution_bounds_exact",
        "forbidden_set_exact",
        "no_scientific_execution_authority",
        "paper_cannot_authorize_dynamics",
        "selector_absent",
        "status_exact",
        "terminal_precedence_exact",
        "v1_gauss5_forbidden",
    },
    "record_identity_checks": set(AUTHORITY_INPUT_NAMES),
    "source_checks": {
        "ATTACHED_ORIGINAL_PLAN",
        "HUMER_STEINBRECHER_PECHSTEIN_2026",
        "MEIER_WALL_POPP_2016",
    },
    "source_semantic_checks": {
        "authority_classes_exact",
        "base_exact",
        "derived_authority_exact",
        "source_artifacts_exact",
        "source_authorities_exact",
        "source_equation_routes_exact",
        "source_ids_unique_and_ordered",
        "source_policy_exact",
    },
}
AUTHORITY_INPUT_VALIDATION_FIELDS = {
    "complete_field_set_and_values",
    "exact_schema",
    "exact_top_level_fields",
    "git_blob_is_canonical_lf_text",
    "strict_json_object",
    "working_tree_matches_git_blob",
}

CHECK_FIELDS = {
    "authority_bindings",
    "candidate_id",
    "cases",
    "checker_import_boundary",
    "coverage",
    "reversal",
    "schema",
    "terminal",
}
CHECK_BINDING_KEYS = {
    "authority_inputs",
    "base",
    "environment",
    "programs",
    "repository_git_blob_oids",
    "repository_git_blobs_are_canonical_lf_text",
    "repository_working_tree_matches_git_blobs",
    "source_artifacts",
}
CASE_FIELDS = {"case_id", "metrics", "predicates", "registered_input_sha256"}
CASE_ORDER = (
    "REFERENCE",
    "RIGID_COMMON",
    "AXIAL_SHEAR",
    "BEND_TWIST",
    "NONCOMMUTING",
    "NONCOMMUTING_REVERSED",
)
CASE_METRIC_KEYS = {
    "cell_length_absolute",
    "energy_relative",
    "internal_stationarity_inf",
    "positions_inf",
    "residual_relative",
    "section_inf",
    "source_tangent_symmetry_relative",
    "tangent_full_max_relative",
    "tangent_full_relative",
    "vertex_rotations_inf",
}
CASE_EVIDENCE_PREDICATES = {
    "content_hash",
    "registered_cell_length",
    "registered_positions",
    "registered_section",
    "registered_vertex_rotations",
}
CASE_SCIENTIFIC_PREDICATES = {
    "energy",
    "internal_stationarity",
    "residual",
    "rigid_energy",
    "rigid_force",
    "source_tangent_symmetry",
    "tangent_full",
    "tangent_full_max",
    "tangent_symmetry",
}
CASE_VARIATIONAL_PREDICATES = {
    "source_tangent_symmetry",
    "tangent_full",
    "tangent_full_max",
    "tangent_symmetry",
}
COVERAGE_EVIDENCE_PREDICATES = {
    "coverage_classifies",
    "coverage_content_hash",
    "coverage_geometry_scope",
    "coverage_schema",
    "isolated_mode_order",
    "isolated_modes_registered_inputs",
    "multi_element_registered_inputs",
    "orientation_case_order",
    "orientation_registered_inputs",
    "slenderness_order",
    "slenderness_registered_inputs",
}
COVERAGE_SCIENTIFIC_PREDICATES = {
    "isolated_modes_independent_source",
    "isolated_modes_physical",
    "multi_element_independent_operator",
    "multi_element_six_rigid_modes",
    "orientation_independent_source",
    "physical_orientation_objectivity",
    "slenderness_independent_operator",
    "slenderness_rank_and_reference_response",
}
COVERAGE_REFERENCE_LINEAR_PREDICATES = {
    "isolated_modes_independent_source",
    "isolated_modes_physical",
    "multi_element_independent_operator",
    "multi_element_six_rigid_modes",
    "slenderness_independent_operator",
    "slenderness_rank_and_reference_response",
}

NUMERICAL_THREAD_VARIABLES = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)

PYTEST_DIAGNOSTIC_EXCLUSION_POLICY = (
    "NON_CODE_DATA_OR_LOG_FILES_UNDER_TOP_LEVEL_DOT_PYTEST_DIRECTORIES_ONLY"
)

# ``subprocess`` exposes CREATE_NEW_PROCESS_GROUP but not CREATE_SUSPENDED on
# every supported Python/Windows combination.  This is the documented Win32
# creation flag; using it is essential because a child must not execute before
# it has been assigned to the mandatory kill-on-close Job Object.
WINDOWS_CREATE_SUSPENDED = 0x00000004


@dataclass(frozen=True)
class ExecutionBounds:
    child_wall_seconds: float = 600.0
    complete_wave_wall_seconds: float = 1800.0
    inactivity_seconds: float = 300.0
    memory_limit_bytes: int = 24 * 1024**3
    numerical_library_threads: int = 1

    def authority_value(self) -> dict[str, Any]:
        return {
            "child_wall_seconds": int(self.child_wall_seconds),
            "complete_wave_wall_seconds": int(self.complete_wave_wall_seconds),
            "inactivity_seconds": int(self.inactivity_seconds),
            # The preregistered contract permits at most three workers.  This
            # coordinator deliberately uses only two replicas at a time.
            "maximum_concurrent_workers": 3,
            "memory_limit_gib_per_process_tree": self.memory_limit_bytes // 1024**3,
            "no_automatic_retry": True,
            "numerical_library_threads_per_worker": self.numerical_library_threads,
            "required_cycle_count_after_freeze": 2,
        }


FROZEN_BOUNDS = ExecutionBounds()


class AuthorityError(ValueError):
    """Raised before process launch when execution authority is not exact."""


class ExclusiveOutputError(FileExistsError):
    """Raised when an output location is not fresh."""


@dataclass(frozen=True)
class ChildSpec:
    role: str
    cycle: int
    command: tuple[str, ...]
    directory: Path
    watched_output: Path


@dataclass
class ChildState:
    spec: ChildSpec
    process: subprocess.Popen[bytes]
    stdout_path: Path
    stderr_path: Path
    stdout_stream: Any
    stderr_stream: Any
    started: float
    last_activity: float
    last_signature: tuple[int, int, int]
    job: "_WindowsJob | None"
    known_pids: set[int]
    forced_reason: str | None = None
    tree_drained: bool = False


def _pairs(entries: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in entries:
        if key in made:
            raise AuthorityError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def _validate_finite(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("nonfinite canonical JSON value")
    if isinstance(value, dict):
        for child in value.values():
            _validate_finite(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _validate_finite(child)


def _canonical_bytes(value: Any) -> bytes:
    _validate_finite(value)
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("ascii")


def _strict_json_bytes(payload: bytes) -> dict[str, Any]:
    try:
        made = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(
                AuthorityError(f"nonfinite JSON token: {value}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuthorityError("malformed JSON") from exc
    if not isinstance(made, dict):
        raise AuthorityError("JSON record must be an object")
    return made


def _read_canonical_record(path: Path, *, label: str) -> tuple[bytes, dict[str, Any]]:
    if not path.is_file() or path.is_symlink():
        raise AuthorityError(f"{label} must be a regular non-symlink file")
    payload = path.read_bytes()
    record = _strict_json_bytes(payload)
    if payload != _canonical_bytes(record):
        raise AuthorityError(f"{label} is not canonical JSON")
    return payload, record


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_lf_text_bytes(payload: bytes) -> bytes:
    if b"\0" in payload:
        raise AuthorityError("repository text input contains NUL")
    normalized = payload.replace(b"\r\n", b"\n")
    if b"\r" in normalized:
        raise AuthorityError("repository text input contains a lone carriage return")
    return normalized


def _is_hex(value: Any, length: int) -> bool:
    return (
        isinstance(value, str)
        and len(value) == length
        and all(character in "0123456789abcdefABCDEF" for character in value)
    )


def _is_within(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
    except ValueError:
        return False
    return True


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
    return subprocess.check_output(
        (
            "git",
            "--no-replace-objects",
            "-c",
            "core.autocrlf=input",
            *arguments,
        ),
        cwd=repository,
        env=_git_environment(),
        stderr=subprocess.DEVNULL,
    )


def _git_text(repository: Path, *arguments: str) -> str:
    return _git_bytes(repository, *arguments).decode("utf-8").strip()


def _git_paths(repository: Path, *arguments: str) -> tuple[str, ...]:
    return tuple(
        entry.decode("utf-8", errors="surrogateescape").replace("\\", "/")
        for entry in _git_bytes(repository, *arguments, "-z").split(b"\0")
        if entry
    )


def _checkout_has_changes(repository: Path) -> bool:
    """Check content, index, merge, and untracked state without stat-cache noise."""

    checks = (
        _git_bytes(
            repository,
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            "--name-only",
            "-z",
            "--",
        ),
        _git_bytes(
            repository,
            "diff",
            "--cached",
            "--no-ext-diff",
            "--no-textconv",
            "--name-only",
            "-z",
            "HEAD",
            "--",
        ),
        _git_bytes(repository, "ls-files", "--unmerged", "-z"),
        _git_bytes(repository, "ls-files", "--others", "--exclude-standard", "-z"),
    )
    return any(checks)


def _reject_git_overrides(repository: Path) -> None:
    common = Path(_git_text(repository, "rev-parse", "--git-common-dir"))
    if not common.is_absolute():
        common = repository / common
    for relative in ("info/grafts", "objects/info/alternates"):
        path = common / relative
        if path.exists():
            raise AuthorityError(f"Git authority override is present: {relative}")


def _commit_identity(repository: Path, commit: str) -> dict[str, str]:
    try:
        commit_type = _git_text(repository, "cat-file", "-t", commit)
        tree = _git_text(repository, "show", "-s", "--format=%T", commit)
    except (OSError, subprocess.CalledProcessError) as exc:
        raise AuthorityError(f"unresolvable commit: {commit}") from exc
    if commit_type != "commit":
        raise AuthorityError(f"registered object is not a commit: {commit}")
    return {"commit": commit.lower(), "tree": tree.lower()}


def _blob_binding(repository: Path, commit: str, path: str, role: str) -> dict[str, str]:
    raw = _git_bytes(repository, "ls-tree", "-z", commit, "--", path)
    entries = [entry for entry in raw.split(b"\0") if entry]
    if len(entries) != 1 or b"\t" not in entries[0]:
        raise AuthorityError(f"missing or ambiguous candidate path: {path}")
    metadata, registered = entries[0].split(b"\t", 1)
    fields = metadata.split()
    made_path = registered.decode("utf-8", errors="strict").replace("\\", "/")
    if len(fields) != 3 or fields[0] not in {b"100644", b"100755"} or fields[1] != b"blob":
        raise AuthorityError(f"candidate path is not a regular Git blob: {path}")
    if made_path != path:
        raise AuthorityError(f"candidate path spelling mismatch: {path}")
    oid = fields[2].decode("ascii").lower()
    content = _git_bytes(repository, "cat-file", "blob", oid)
    if b"\0" in content or b"\r" in content:
        raise AuthorityError(f"candidate text blob is not canonical LF text: {path}")
    return {
        "git_blob_oid": oid,
        "git_mode": fields[0].decode("ascii"),
        "path": path,
        "role": role,
        "sha256": _sha256_bytes(content),
    }


def candidate_manifest(repository: Path, harness_commit: str) -> list[dict[str, str]]:
    """Build the exact canonical 20-path manifest from a committed tree."""

    return [
        _blob_binding(repository, harness_commit, path, PATH_ROLES[path])
        for path in CANDIDATE_PATHS
    ]


def _runtime_binding() -> dict[str, Any]:
    executable = Path(sys.executable).resolve()
    if not executable.is_file() or executable.is_symlink():
        raise AuthorityError("Python executable is not a regular non-symlink file")
    payload = executable.read_bytes()
    return {
        "bytes": len(payload),
        "executable": str(executable),
        "implementation": platform.python_implementation(),
        "sha256": _sha256_bytes(payload),
        "version": platform.python_version(),
    }


def _all_boolean_leaves_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, dict) and value:
        return all(_all_boolean_leaves_true(child) for child in value.values())
    if isinstance(value, list) and value:
        return all(_all_boolean_leaves_true(child) for child in value)
    return False


def _validate_bound_file(
    binding: Any, authority_path: Path, *, label: str
) -> tuple[bytes, dict[str, Any], Path]:
    if not isinstance(binding, dict) or set(binding) != {
        "bytes",
        "path",
        "sha256",
        "terminal",
    }:
        raise AuthorityError(f"{label} binding field set mismatch")
    path = Path(binding["path"])
    if not path.is_absolute():
        path = authority_path.parent / path
    payload, record = _read_canonical_record(path, label=label)
    if (
        binding["bytes"] != len(payload)
        or binding["sha256"] != _sha256_bytes(payload)
        or binding["terminal"] != record.get("terminal")
    ):
        raise AuthorityError(f"{label} byte binding mismatch")
    return payload, record, path


def _validate_authority_check(
    binding: Any,
    authority_path: Path,
    manifest: list[dict[str, str]],
) -> dict[str, Any]:
    payload, record, path = _validate_bound_file(
        binding, authority_path, label="authority-check record"
    )
    if _is_within(path, ROOT):
        raise AuthorityError("authority-check record must be external")
    if set(record) != AUTHORITY_CHECK_FIELDS:
        raise AuthorityError("authority-check full schema field set mismatch")
    if (
        record["schema"] != AUTHORITY_CHECK_SCHEMA
        or record["study_id"] != STUDY_ID
        or record["candidate_id"] != CANDIDATE_ID
        or record["source_verification_mode"] != "EXTERNAL_FILES_HASHED"
        or record["pytest_diagnostic_exclusion_policy"]
        != PYTEST_DIAGNOSTIC_EXCLUSION_POLICY
        or record["terminal"] != "AUTHORITY_CHECK_ONLY_PASS"
        or binding["terminal"] != "AUTHORITY_CHECK_ONLY_PASS"
    ):
        raise AuthorityError("authority-check identity or terminal mismatch")
    for group, expected_keys in AUTHORITY_BOOLEAN_GROUP_FIELDS.items():
        value = record[group]
        if (
            not isinstance(value, dict)
            or set(value) != expected_keys
            or not all(isinstance(item, bool) and item for item in value.values())
        ):
            raise AuthorityError(
                f"authority-check {group} contains a false or malformed predicate"
            )
    input_validation = record["input_validation_checks"]
    if (
        not isinstance(input_validation, dict)
        or set(input_validation) != set(AUTHORITY_INPUT_NAMES)
        or any(
            not isinstance(value, dict)
            or set(value) != AUTHORITY_INPUT_VALIDATION_FIELDS
            or not all(isinstance(item, bool) and item for item in value.values())
            for value in input_validation.values()
        )
    ):
        raise AuthorityError(
            "authority-check input validation contains a false or malformed predicate"
        )
    if record["candidate_extent"] != list(CANDIDATE_PATHS):
        raise AuthorityError("authority-check candidate extent mismatch")
    components = record["candidate_extent_components"]
    if not isinstance(components, dict) or set(components) != {
        "committed_since_base",
        "index",
        "untracked",
        "working_tree",
    }:
        raise AuthorityError("authority-check extent components malformed")
    if (
        components["committed_since_base"] != list(CANDIDATE_PATHS)
        or components["index"] != []
        or components["untracked"] != []
        or components["working_tree"] != []
    ):
        raise AuthorityError("authority-check was not produced from the clean harness tree")
    by_path = {row["path"]: row for row in manifest}
    expected_hashes = {
        Path(path).name: by_path[path]["sha256"] for path in SOURCE_INPUT_PATHS
    }
    expected_oids = {
        Path(path).name: by_path[path]["git_blob_oid"] for path in SOURCE_INPUT_PATHS
    }
    if (
        record["input_hashes"] != expected_hashes
        or record["input_working_hashes"] != expected_hashes
        or record["input_git_blob_oids"] != expected_oids
    ):
        raise AuthorityError("authority-check input Git bindings mismatch")
    return {
        "bytes": len(payload),
        "path": str(path.resolve()),
        "sha256": _sha256_bytes(payload),
        "terminal": record["terminal"],
    }


def _validate_review(
    repository: Path,
    head: str,
    binding: Any,
    manifest: list[dict[str, str]],
    preauthorization: dict[str, Any],
) -> dict[str, Any]:
    expected_blob = _blob_binding(
        repository, head, REVIEW_RELATIVE_PATH, "EXECUTION_REVIEW"
    )
    if not isinstance(binding, dict) or set(binding) != {
        "git_blob_oid",
        "path",
        "sha256",
        "verdict",
    }:
        raise AuthorityError("review binding field set mismatch")
    expected = {
        "git_blob_oid": expected_blob["git_blob_oid"],
        "path": REVIEW_RELATIVE_PATH,
        "sha256": expected_blob["sha256"],
        "verdict": REVIEW_VERDICT,
    }
    if binding != expected:
        raise AuthorityError("review Git-blob binding mismatch")
    blob = _git_bytes(repository, "cat-file", "blob", expected_blob["git_blob_oid"])
    review = _strict_json_bytes(blob)
    if blob != _canonical_bytes(review) or set(review) != {
        "findings",
        "reviewed_inputs",
        "reviewer_independence",
        "schema",
        "verdict",
    }:
        raise AuthorityError("review is not canonical five-key JSON")
    if (
        review["findings"] != []
        or review["reviewed_inputs"]
        != {
            "candidate_manifest": manifest,
            "preauthorization_records": preauthorization,
        }
        or review["reviewer_independence"] != REVIEWER_INDEPENDENCE
        or review["schema"] != REVIEW_SCHEMA
        or review["verdict"] != REVIEW_VERDICT
    ):
        raise AuthorityError("review contents do not accept the exact harness manifest")
    return {
        "git_blob_oid": expected_blob["git_blob_oid"],
        "path": REVIEW_RELATIVE_PATH,
        "sha256": expected_blob["sha256"],
        "verdict": REVIEW_VERDICT,
    }


def _validate_request(value: Any, repository: Path) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "attempt_id",
        "no_retry",
        "one_time",
        "registry_root",
        "request_id",
    }:
        raise AuthorityError("one-time request field set mismatch")
    for name in ("request_id", "attempt_id"):
        identifier = value[name]
        if not _is_hex(identifier, 32) or identifier != identifier.lower():
            raise AuthorityError(f"{name} must be 32 lowercase hexadecimal characters")
    if value["request_id"] == value["attempt_id"]:
        raise AuthorityError("request and attempt IDs must differ")
    if value["one_time"] is not True or value["no_retry"] is not True:
        raise AuthorityError("request must be one-time with no retry")
    registry = Path(value["registry_root"])
    if (
        not registry.is_absolute()
        or not registry.is_dir()
        or registry.is_symlink()
        or _is_within(registry, repository)
    ):
        raise AuthorityError("request registry must be an existing external directory")
    return {**value, "registry_root": str(registry.resolve())}


@dataclass(frozen=True)
class ValidatedAuthority:
    binding: dict[str, Any]
    harness_commit: str
    harness_tree: str
    request: dict[str, Any]
    manifest: tuple[dict[str, str], ...]
    python_runtime: dict[str, Any]


def validate_execution_authority(
    authority_path: Path,
    *,
    mode: str,
    repository: Path = ROOT,
) -> ValidatedAuthority:
    """Validate authority, review, topology, and frozen blobs before launch."""

    _reject_git_overrides(repository)
    payload, authority = _read_canonical_record(authority_path, label="execution authority")
    common_fields = {
        "candidate_id",
        "cycle_count",
        "execution_bounds",
        "harness",
        "mechanics_origin",
        "mode",
        "program_bindings",
        "python_runtime",
        "request",
        "schema",
        "scientific_execution_authorized",
        "source_input_bindings",
        "study_id",
        "terminal",
    }
    formal_fields = common_fields | {
        "authorization_commit",
        "preauthorization_records",
        "review",
    }
    rehearsal_fields = common_fields | {"authority_check"}
    expected_fields = formal_fields if mode == FORMAL_MODE else rehearsal_fields
    if set(authority) != expected_fields:
        raise AuthorityError("execution-authority full field set mismatch")
    expected_schema = AUTHORITY_SCHEMA if mode == FORMAL_MODE else REHEARSAL_AUTHORITY_SCHEMA
    if authority["schema"] != expected_schema or authority["mode"] != mode:
        raise AuthorityError("execution-authority schema or mode mismatch")
    if authority["study_id"] != STUDY_ID or authority["candidate_id"] != CANDIDATE_ID:
        raise AuthorityError("execution-authority study/candidate mismatch")
    if authority["cycle_count"] != 2 or authority["execution_bounds"] != FROZEN_BOUNDS.authority_value():
        raise AuthorityError("execution cycle count or bounds mismatch")
    formal = mode == FORMAL_MODE
    expected_terminal = FORMAL_AUTHORITY_TERMINAL if formal else REHEARSAL_AUTHORITY_TERMINAL
    if authority["scientific_execution_authorized"] is not formal or authority["terminal"] != expected_terminal:
        raise AuthorityError("execution authorization disposition mismatch")

    mechanics = authority["mechanics_origin"]
    expected_mechanics = {
        "commit": MECHANICS_COMMIT,
        "parent": BASE_COMMIT,
        "tree": MECHANICS_TREE,
    }
    if mechanics != expected_mechanics or _commit_identity(repository, MECHANICS_COMMIT) != {
        "commit": MECHANICS_COMMIT,
        "tree": MECHANICS_TREE,
    }:
        raise AuthorityError("mechanics-origin binding mismatch")
    if _git_text(repository, "show", "-s", "--format=%P", MECHANICS_COMMIT) != BASE_COMMIT:
        raise AuthorityError("mechanics-origin parent mismatch")

    harness = authority["harness"]
    if not isinstance(harness, dict) or set(harness) != {
        "candidate_manifest",
        "commit",
        "parent",
        "subject",
        "tree",
    }:
        raise AuthorityError("harness binding field set mismatch")
    if not _is_hex(harness["commit"], 40) or not _is_hex(harness["tree"], 40):
        raise AuthorityError("harness identity is not hexadecimal")
    harness_commit = harness["commit"].lower()
    harness_identity = _commit_identity(repository, harness_commit)
    if (
        harness_identity["tree"] != harness["tree"].lower()
        or harness["parent"] != MECHANICS_COMMIT
        or _git_text(repository, "show", "-s", "--format=%P", harness_commit) != MECHANICS_COMMIT
        or _git_text(repository, "show", "-s", "--format=%s", harness_commit) != harness["subject"]
    ):
        raise AuthorityError("harness commit topology mismatch")
    changed_from_base = tuple(sorted(_git_paths(repository, "diff", "--name-only", f"{BASE_COMMIT}...{harness_commit}")))
    if changed_from_base != CANDIDATE_PATHS:
        raise AuthorityError("harness does not freeze the exact 20-path candidate")
    manifest = candidate_manifest(repository, harness_commit)
    if harness["candidate_manifest"] != manifest:
        raise AuthorityError("harness candidate manifest mismatch")
    runner_path = (repository / "docs/reference_cases/ge_beam3_mixed_formal_runner.py").resolve()
    runner_row = next(
        row
        for row in manifest
        if row["path"] == "docs/reference_cases/ge_beam3_mixed_formal_runner.py"
    )
    if (
        RUNNER.resolve() != runner_path
        or not runner_path.is_file()
        or runner_path.is_symlink()
        or _sha256_bytes(_canonical_lf_text_bytes(runner_path.read_bytes()))
        != runner_row["sha256"]
    ):
        raise AuthorityError("running coordinator differs from its authorized Git blob")
    if authority["source_input_bindings"] != [
        row for row in manifest if row["role"] == "SOURCE_INPUT"
    ]:
        raise AuthorityError("source/input Git-blob bindings mismatch")
    if authority["program_bindings"] != [
        row for row in manifest if row["role"] == "PROGRAM"
    ]:
        raise AuthorityError("program Git-blob bindings mismatch")
    python_runtime = _runtime_binding()
    if authority["python_runtime"] != python_runtime:
        raise AuthorityError("Python executable identity mismatch")
    request = _validate_request(authority["request"], repository)

    head = _git_text(repository, "rev-parse", "HEAD").lower()
    if _checkout_has_changes(repository):
        raise AuthorityError("current execution checkout is not fully clean")
    if formal:
        preauthorization = _validate_preauthorization_records(
            authority["preauthorization_records"],
            authority_path,
            manifest,
            harness_commit=harness_commit,
            harness_tree=harness_identity["tree"],
        )
        rehearsal_request = preauthorization["rehearsal_aggregate"]["request"]
        if (
            not isinstance(rehearsal_request, dict)
            or set(rehearsal_request) != {"attempt_id", "request_id"}
            or request["request_id"] in rehearsal_request.values()
            or request["attempt_id"] in rehearsal_request.values()
        ):
            raise AuthorityError("formal request reuses preauthorization execution identity")
        expected_authority_path = (repository / AUTHORITY_RELATIVE_PATH).resolve()
        if authority_path.resolve() != expected_authority_path:
            raise AuthorityError("formal authority must be the registered overlay path")
        authorization = authority["authorization_commit"]
        expected_authorization = {
            "exact_paths": list(AUTHORIZATION_PATHS),
            "expected_parent": harness_commit,
            "expected_subject": AUTHORIZATION_SUBJECT,
        }
        if authorization != expected_authorization:
            raise AuthorityError("authorization-commit preregistration mismatch")
        if (
            _git_text(repository, "show", "-s", "--format=%P", head) != harness_commit
            or _git_text(repository, "show", "-s", "--format=%s", head) != AUTHORIZATION_SUBJECT
            or tuple(sorted(_git_paths(repository, "diff-tree", "--no-commit-id", "--name-only", "-r", head)))
            != tuple(sorted(AUTHORIZATION_PATHS))
        ):
            raise AuthorityError("current HEAD is not the exact authorization overlay")
        authority_blob = _git_bytes(
            repository,
            "cat-file",
            "blob",
            _blob_binding(repository, head, AUTHORITY_RELATIVE_PATH, "EXECUTION_AUTHORITY")["git_blob_oid"],
        )
        if authority_blob != payload:
            raise AuthorityError("working authority differs from authorization commit")
        review_binding = _validate_review(
            repository,
            head,
            authority["review"],
            manifest,
            preauthorization,
        )
        authorization_binding: dict[str, Any] | None = {
            "commit": head,
            "exact_paths": list(AUTHORIZATION_PATHS),
            "parent": harness_commit,
            "subject": AUTHORIZATION_SUBJECT,
            "tree": _git_text(repository, "show", "-s", "--format=%T", head).lower(),
        }
    else:
        if _is_within(authority_path, repository):
            raise AuthorityError("rehearsal authority must be an explicit external record")
        if head != harness_commit:
            raise AuthorityError("rehearsal must run from the clean harness commit")
        check_binding = _validate_authority_check(
            authority["authority_check"], authority_path, manifest
        )
        preauthorization = None
        review_binding = None
        authorization_binding = None

    binding = {
        "authorization": authorization_binding,
        "preauthorization_records": preauthorization,
        "bytes": len(payload),
        "harness": harness_identity,
        "mode": mode,
        "request": {
            "attempt_id": request["attempt_id"],
            "request_id": request["request_id"],
        },
        "review": review_binding,
        "sha256": _sha256_bytes(payload),
        "terminal": authority["terminal"],
    }
    return ValidatedAuthority(
        binding=binding,
        harness_commit=harness_commit,
        harness_tree=harness_identity["tree"],
        request=request,
        manifest=tuple(manifest),
        python_runtime=python_runtime,
    )


def _full_tree_manifest(repository: Path, commit: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen_casefolded: set[str] = set()
    raw = _git_bytes(repository, "ls-tree", "-r", "-z", "--full-tree", commit)
    for entry in (item for item in raw.split(b"\0") if item):
        if b"\t" not in entry:
            raise AuthorityError("malformed Git tree entry")
        metadata, encoded_path = entry.split(b"\t", 1)
        fields = metadata.split()
        if len(fields) != 3 or fields[0] not in {b"100644", b"100755"} or fields[1] != b"blob":
            raise AuthorityError("materialized tree may contain regular blobs only")
        path = encoded_path.decode("utf-8", errors="strict").replace("\\", "/")
        parts = Path(path).parts
        if not parts or Path(path).is_absolute() or ".." in parts:
            raise AuthorityError("unsafe path in materialized tree")
        folded = path.casefold()
        if folded in seen_casefolded:
            raise AuthorityError("case-colliding paths in materialized tree")
        seen_casefolded.add(folded)
        oid = fields[2].decode("ascii").lower()
        content = _git_bytes(repository, "cat-file", "blob", oid)
        rows.append(
            {
                "git_blob_oid": oid,
                "mode": fields[0].decode("ascii"),
                "path": path,
                "sha256": _sha256_bytes(content),
            }
        )
    return sorted(rows, key=lambda row: row["path"])


def _make_read_only(root: Path) -> None:
    for path in sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        try:
            if path.is_file():
                path.chmod(stat.S_IREAD)
            elif path.is_dir():
                path.chmod(stat.S_IREAD | stat.S_IEXEC)
        except OSError as exc:
            raise AuthorityError(f"could not freeze materialized path: {path}") from exc
    root.chmod(stat.S_IREAD | stat.S_IEXEC)


def _restore_exact_blob_bytes(
    source_repository: Path,
    destination: Path,
    rows: list[dict[str, Any]],
) -> None:
    """Replace checkout-smudged text with the exact committed blob bytes."""

    for row in rows:
        path = (destination / row["path"]).resolve()
        try:
            path.relative_to(destination.resolve())
        except ValueError as exc:
            raise AuthorityError("materialized blob path escaped destination") from exc
        if not path.is_file() or path.is_symlink():
            raise AuthorityError(f"materialized path is not a regular file: {row['path']}")
        content = _git_bytes(
            source_repository, "cat-file", "blob", row["git_blob_oid"]
        )
        if _sha256_bytes(content) != row["sha256"]:
            raise AuthorityError(f"source blob hash mismatch: {row['path']}")
        path.write_bytes(content)


def _materialize_harness(
    repository: Path,
    validated: ValidatedAuthority,
    work_root: Path,
) -> tuple[Path, Path, str]:
    destination = work_root / "materialized-harness"
    command = (
        "git",
        "--no-replace-objects",
        "-c",
        "core.autocrlf=input",
        "clone",
        "--no-hardlinks",
        "--no-checkout",
        "--quiet",
        str(repository.resolve()),
        str(destination),
    )
    completed = subprocess.run(
        command,
        cwd=work_root,
        env=_git_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise AuthorityError("failed to create private harness clone")
    subprocess.run(
        (
            "git",
            "--no-replace-objects",
            "-c",
            "core.autocrlf=input",
            "checkout",
            "--detach",
            "--force",
            "--quiet",
            validated.harness_commit,
        ),
        cwd=destination,
        env=_git_environment(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    if (
        _git_text(destination, "rev-parse", "HEAD") != validated.harness_commit
        or _git_text(destination, "show", "-s", "--format=%T", "HEAD")
        != validated.harness_tree
        or _checkout_has_changes(destination)
    ):
        raise AuthorityError("private materialization is not the exact clean harness")
    rows = _full_tree_manifest(repository, validated.harness_commit)
    _restore_exact_blob_bytes(repository, destination, rows)
    if _checkout_has_changes(destination):
        raise AuthorityError("canonical blob restoration changed Git content")
    for row in rows:
        path = destination / row["path"]
        if not path.is_file() or path.is_symlink() or _sha256(path) != row["sha256"]:
            raise AuthorityError(f"materialized blob mismatch: {row['path']}")
    record = {
        "commit": validated.harness_commit,
        "files": rows,
        "schema": "anysolver.ge-beam3-mixed-materialized-tree-v1",
        "tree": validated.harness_tree,
    }
    payload = _canonical_bytes(record)
    manifest_path = work_root / "materialized-tree-manifest.json"
    with manifest_path.open("xb") as stream:
        stream.write(payload)
    _make_read_only(destination)
    return destination, manifest_path, _sha256_bytes(payload)


ISOLATED_BOOTSTRAP = r'''
import hashlib,json,os,pathlib,platform,runpy,site,subprocess,sys
root=pathlib.Path(sys.argv[1]).resolve()
manifest_path=pathlib.Path(sys.argv[2]).resolve()
manifest_sha=sys.argv[3]
expected_executable=pathlib.Path(sys.argv[4]).resolve()
expected_executable_sha=sys.argv[5]
expected_implementation=sys.argv[6]
expected_version=sys.argv[7]
role=sys.argv[8]
origin_output=pathlib.Path(sys.argv[9]).resolve()
script=pathlib.Path(sys.argv[10]).resolve()
script_arguments=sys.argv[11:]
def pairs(entries):
    made={}
    for key,value in entries:
        if key in made: raise RuntimeError('duplicate materialization key')
        made[key]=value
    return made
payload=manifest_path.read_bytes()
if hashlib.sha256(payload).hexdigest().upper()!=manifest_sha: raise RuntimeError('materialization manifest hash mismatch')
manifest=json.loads(payload.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda value:(_ for _ in ()).throw(RuntimeError('nonfinite manifest')))
canonical=(json.dumps(manifest,allow_nan=False,ensure_ascii=True,separators=(',',':'),sort_keys=True)+'\n').encode('ascii')
if canonical!=payload: raise RuntimeError('noncanonical materialization manifest')
if set(manifest)!={'commit','files','schema','tree'} or manifest['schema']!='anysolver.ge-beam3-mixed-materialized-tree-v1': raise RuntimeError('materialization schema mismatch')
for row in manifest['files']:
    if set(row)!={'git_blob_oid','mode','path','sha256'}: raise RuntimeError('materialization row mismatch')
    path=(root/row['path']).resolve()
    path.relative_to(root)
    if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest().upper()!=row['sha256']: raise RuntimeError('materialized file mismatch')
git_env={key:value for key,value in os.environ.items() if not key.upper().startswith('GIT_')}
git_env.update({'GIT_CONFIG_GLOBAL':os.devnull,'GIT_CONFIG_NOSYSTEM':'1','GIT_NO_REPLACE_OBJECTS':'1','GIT_OPTIONAL_LOCKS':'0','GIT_TERMINAL_PROMPT':'0'})
git_command=['git','--no-replace-objects','-c','core.autocrlf=input']
head=subprocess.check_output([*git_command,'rev-parse','HEAD'],cwd=root,env=git_env,stderr=subprocess.DEVNULL).decode().strip()
tree=subprocess.check_output([*git_command,'show','-s','--format=%T','HEAD'],cwd=root,env=git_env,stderr=subprocess.DEVNULL).decode().strip()
def dirty_checkout():
    commands=([
        *git_command,'diff','--no-ext-diff','--no-textconv','--name-only','-z','--'],[
        *git_command,'diff','--cached','--no-ext-diff','--no-textconv','--name-only','-z','HEAD','--'],[
        *git_command,'ls-files','--unmerged','-z'],[
        *git_command,'ls-files','--others','--exclude-standard','-z'])
    return any(subprocess.check_output(command,cwd=root,env=git_env,stderr=subprocess.DEVNULL) for command in commands)
dirty=dirty_checkout()
if head!=manifest['commit'] or tree!=manifest['tree'] or dirty: raise RuntimeError('materialized Git identity mismatch')
script.relative_to(root)
if not script.is_file() or script.is_symlink(): raise RuntimeError('script origin mismatch')
executable=pathlib.Path(sys.executable).resolve()
if executable!=expected_executable or hashlib.sha256(executable.read_bytes()).hexdigest().upper()!=expected_executable_sha or platform.python_implementation()!=expected_implementation or platform.python_version()!=expected_version: raise RuntimeError('Python runtime identity mismatch')
sys.argv=[str(script),*script_arguments]
code=0
try:
    runpy.run_path(str(script),run_name='__main__')
except SystemExit as outcome:
    code=outcome.code if isinstance(outcome.code,int) else (0 if outcome.code is None else 1)
# Recheck every committed byte after program evaluation.  Read-only materialization
# is the primary barrier; this closes the evidence path if a child nevertheless
# managed to mutate or add anything while it ran.
for row in manifest['files']:
    path=(root/row['path']).resolve()
    path.relative_to(root)
    if not path.is_file() or path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest().upper()!=row['sha256']: raise RuntimeError('post-execution materialized file mismatch')
dirty=dirty_checkout()
if dirty: raise RuntimeError('post-execution materialized Git state mismatch')
package_root=(root/'src'/'anysolver').resolve()
anysolver_origins=[]
for name,module in sorted(sys.modules.items()):
    if name=='anysolver' or name.startswith('anysolver.'):
        origin=getattr(module,'__file__',None)
        if origin is not None:
            resolved=pathlib.Path(origin).resolve();resolved.relative_to(package_root);anysolver_origins.append(str(resolved))
if role=='producer' and not anysolver_origins: raise RuntimeError('producer did not import materialized anysolver')
if role=='checker' and anysolver_origins: raise RuntimeError('checker imported anysolver')
numpy_module=sys.modules.get('numpy')
numpy_origin=None if numpy_module is None else str(pathlib.Path(numpy_module.__file__).resolve())
user_site=pathlib.Path(site.getusersitepackages()).resolve()
if site.ENABLE_USER_SITE or (numpy_origin is not None and user_site in pathlib.Path(numpy_origin).resolve().parents): raise RuntimeError('user-site injection detected')
record={'anysolver_origins':anysolver_origins,'candidate_commit':head,'candidate_tree':tree,'executable':str(executable),'executable_sha256':hashlib.sha256(executable.read_bytes()).hexdigest().upper(),'isolated':sys.flags.isolated==1,'numpy_origin':numpy_origin,'role':role,'schema':'anysolver.ge-beam3-mixed-child-origin-v1','user_site_enabled':bool(site.ENABLE_USER_SITE)}
origin_payload=(json.dumps(record,allow_nan=False,ensure_ascii=True,separators=(',',':'),sort_keys=True)+'\n').encode('ascii')
with origin_output.open('xb') as stream: stream.write(origin_payload)
raise SystemExit(code)
'''.strip()


def _isolated_command(
    *,
    validated: ValidatedAuthority,
    materialized: Path,
    materialization_manifest: Path,
    materialization_sha256: str,
    role: str,
    origin_output: Path,
    script_relative: str,
    arguments: tuple[str, ...],
) -> tuple[str, ...]:
    return (
        sys.executable,
        "-I",
        "-B",
        "-c",
        ISOLATED_BOOTSTRAP,
        str(materialized),
        str(materialization_manifest),
        materialization_sha256,
        validated.python_runtime["executable"],
        validated.python_runtime["sha256"],
        validated.python_runtime["implementation"],
        validated.python_runtime["version"],
        role,
        str(origin_output),
        str(materialized / script_relative),
        *arguments,
    )


def _validate_origin_record(
    path: Path, *, role: str, validated: ValidatedAuthority
) -> dict[str, Any]:
    payload, record = _read_canonical_record(path, label=f"{role} origin record")
    if set(record) != {
        "anysolver_origins",
        "candidate_commit",
        "candidate_tree",
        "executable",
        "executable_sha256",
        "isolated",
        "numpy_origin",
        "role",
        "schema",
        "user_site_enabled",
    }:
        raise AuthorityError("child origin record field set mismatch")
    runtime = validated.python_runtime
    origins = record["anysolver_origins"]
    materialized_marker = f"{os.sep}materialized-harness{os.sep}src{os.sep}anysolver{os.sep}"
    if (
        record["schema"] != "anysolver.ge-beam3-mixed-child-origin-v1"
        or record["role"] != role
        or record["candidate_commit"] != validated.harness_commit
        or record["candidate_tree"] != validated.harness_tree
        or record["executable"] != runtime["executable"]
        or record["executable_sha256"] != runtime["sha256"]
        or record["isolated"] is not True
        or record["user_site_enabled"] is not False
        or not isinstance(origins, list)
        or (role == "producer" and (not origins or not all(materialized_marker in item for item in origins)))
        or (role == "checker" and origins != [])
        or not isinstance(record["numpy_origin"], str)
    ):
        raise AuthorityError("child process import-origin verification failed")
    return {"bytes": len(payload), "sha256": _sha256_bytes(payload)}


@dataclass(frozen=True)
class OneTimeClaim:
    claim_path: Path
    claim_binding: dict[str, Any]
    lock_directory: Path
    owner_path: Path
    receipt_path: Path


def _reconcile_stale_global_slot(registry: Path) -> None:
    """Clear only a proven-dead, receipt-backed or terminalized slot owner."""

    lock = registry / "global-slot.lock"
    if not lock.exists():
        return
    if not lock.is_dir() or lock.is_symlink():
        raise AuthorityError("global execution slot route is malformed")
    owner_path = lock / "owner.json"
    _owner_payload, owner = _read_canonical_record(owner_path, label="global-slot owner")
    owner_fields = {
        "attempt_id",
        "authority_sha256",
        "boot_identity",
        "host",
        "intended_output",
        "mode",
        "owner_pid",
        "owner_process_start",
        "request_id",
        "schema",
        "work_root",
    }
    if (
        set(owner) != owner_fields
        or owner["schema"] != "anysolver.ge-beam3-mixed-global-slot-v2"
        or not _is_hex(owner["request_id"], 32)
        or not _is_hex(owner["attempt_id"], 32)
        or not _is_hex(owner["authority_sha256"], 64)
        or owner["mode"] not in {FORMAL_MODE, REHEARSAL_MODE}
        or not isinstance(owner["owner_pid"], int)
        or owner["owner_pid"] <= 0
        or not all(
            isinstance(owner[name], str) and owner[name]
            for name in (
                "boot_identity",
                "host",
                "intended_output",
                "owner_process_start",
                "work_root",
            )
        )
    ):
        raise AuthorityError("global-slot owner record is malformed")
    current_host = platform.node().strip()
    if owner["host"] != current_host:
        raise AuthorityError("cannot prove a foreign-host global-slot owner is dead")
    current_boot = _boot_identity()
    owner_alive = False
    if owner["boot_identity"] == current_boot:
        observed_start = _process_start_identity(owner["owner_pid"])
        owner_alive = observed_start == owner["owner_process_start"]
    if owner_alive:
        raise AuthorityError("global execution slot is occupied by a live owner")

    claims = registry / "claims"
    receipts = registry / "receipts"
    claim_path = claims / f"{owner['request_id']}.{owner['attempt_id']}.claim.json"
    receipt_path = receipts / f"{owner['request_id']}.{owner['attempt_id']}.receipt.json"
    claim_payload, claim = _read_canonical_record(
        claim_path, label="stale-owner one-time claim"
    )
    expected_claim = {
        "attempt_id": owner["attempt_id"],
        "authority_sha256": owner["authority_sha256"],
        "harness_commit": claim.get("harness_commit"),
        "request_id": owner["request_id"],
        "schema": "anysolver.ge-beam3-mixed-one-time-claim-v1",
    }
    if (
        claim != expected_claim
        or not _is_hex(expected_claim["harness_commit"], 40)
    ):
        raise AuthorityError("stale-owner claim binding is malformed")
    claim_binding = {
        "bytes": len(claim_payload),
        "sha256": _sha256_bytes(claim_payload),
    }
    if receipt_path.exists():
        _receipt_payload, receipt = _read_canonical_record(
            receipt_path, label="stale-owner terminal receipt"
        )
        core = receipt.get("aggregate_core") if isinstance(receipt, dict) else None
        allowed_stale_terminals = (
            {
                "BLOCKED_GE_BEAM3_MIXED_PROCESS_OR_EVIDENCE",
                "NO_GO_GE_BEAM3_MIXED_VARIATIONAL_IDENTITY",
                "NO_GO_GE_BEAM3_MIXED_REFERENCE_LINEAR_ALGEBRA",
                "NO_GO_GE_BEAM3_MIXED_FINITE_STATIC",
                "PROVISIONAL_GO_GE_BEAM3_MIXED_STRAIGHT_STATIC_CORE",
            }
            if owner["mode"] == FORMAL_MODE
            else {
                "NONCLASSIFYING_GE_BEAM3_MIXED_REHEARSAL_BLOCKED",
                "NONCLASSIFYING_GE_BEAM3_MIXED_REHEARSAL_FINDING",
                "NONCLASSIFYING_GE_BEAM3_MIXED_REHEARSAL_PASS",
            }
        )
        if (
            set(receipt)
            != {
                "aggregate_core",
                "attempt_id",
                "claim",
                "intended_output",
                "request_id",
                "schema",
                "work_root",
            }
            or receipt["schema"]
            != "anysolver.ge-beam3-mixed-one-time-receipt-v1"
            or receipt["request_id"] != owner["request_id"]
            or receipt["attempt_id"] != owner["attempt_id"]
            or receipt["claim"] != claim_binding
            or receipt["intended_output"] != owner["intended_output"]
            or receipt["work_root"] != owner["work_root"]
            or not isinstance(core, dict)
            or not isinstance(core.get("authority"), dict)
            or core["authority"].get("sha256") != owner["authority_sha256"]
            or core.get("mode") != owner["mode"]
            or core.get("terminal") not in allowed_stale_terminals
        ):
            raise AuthorityError("stale-owner terminal receipt is malformed")
    else:
        orphaned = registry / "orphaned"
        orphaned.mkdir(exist_ok=True)
        if not orphaned.is_dir() or orphaned.is_symlink():
            raise AuthorityError("orphan terminalization route is malformed")
        orphan_path = (
            orphaned
            / f"{owner['request_id']}.{owner['attempt_id']}.orphaned.json"
        )
        orphan = {
            "claim": claim_binding,
            "owner": owner,
            "reason": "PROVEN_DEAD_OWNER_BEFORE_TERMINAL_RECEIPT",
            "schema": "anysolver.ge-beam3-mixed-orphaned-execution-v1",
            "terminal": (
                "BLOCKED_GE_BEAM3_MIXED_PROCESS_OR_EVIDENCE"
                if owner["mode"] == FORMAL_MODE
                else "NONCLASSIFYING_GE_BEAM3_MIXED_REHEARSAL_BLOCKED"
            ),
        }
        orphan_payload = _canonical_bytes(orphan)
        if orphan_path.exists():
            if (
                not orphan_path.is_file()
                or orphan_path.is_symlink()
                or orphan_path.read_bytes() != orphan_payload
            ):
                raise AuthorityError("orphan terminalization record conflicts")
        else:
            with orphan_path.open("xb") as stream:
                stream.write(orphan_payload)

    _archive_global_slot(lock, owner_path, owner)


def _archive_global_slot(
    lock: Path,
    owner_path: Path,
    owner: dict[str, Any],
) -> None:
    """Atomically free a slot while preserving its authenticated owner record."""

    if set(lock.iterdir()) != {owner_path}:
        raise AuthorityError("global-slot directory contains unregistered entries")
    released = lock.parent / "released-slots"
    released.mkdir(exist_ok=True)
    if not released.is_dir() or released.is_symlink():
        raise AuthorityError("released-slot archive route is malformed")
    archive = (
        released
        / f"{owner['request_id']}.{owner['attempt_id']}.released-slot"
    )
    if archive.exists():
        raise AuthorityError("released-slot archive already exists")
    # Directory rename is same-volume and atomic: a crash leaves either the
    # authenticated live/stale lock or a freed slot with its owner preserved,
    # never an ownerless global-slot directory.
    lock.rename(archive)


def _acquire_one_time_claim(
    validated: ValidatedAuthority,
    *,
    output_path: Path,
    work_root: Path,
) -> OneTimeClaim:
    registry = Path(validated.request["registry_root"])
    claims = registry / "claims"
    receipts = registry / "receipts"
    for directory in (claims, receipts):
        directory.mkdir(exist_ok=True)
        if not directory.is_dir() or directory.is_symlink():
            raise AuthorityError("request registry contains a non-directory route")
    lock = registry / "global-slot.lock"
    try:
        lock.mkdir(exist_ok=False)
    except FileExistsError:
        _reconcile_stale_global_slot(registry)
        try:
            lock.mkdir(exist_ok=False)
        except FileExistsError as exc:
            raise AuthorityError("global execution slot is occupied") from exc
    owner = lock / "owner.json"
    request_id = validated.request["request_id"]
    attempt_id = validated.request["attempt_id"]
    claim_path = claims / f"{request_id}.{attempt_id}.claim.json"
    receipt_path = receipts / f"{request_id}.{attempt_id}.receipt.json"
    try:
        if any(claims.glob(f"{request_id}.*.claim.json")) or any(
            receipts.glob(f"{request_id}.*.receipt.json")
        ):
            raise AuthorityError("one-time request ID was already consumed")
        if any(claims.glob(f"*.{attempt_id}.claim.json")) or any(
            receipts.glob(f"*.{attempt_id}.receipt.json")
        ):
            raise AuthorityError("attempt ID was already consumed")
        if receipt_path.exists():
            raise AuthorityError("attempt already has a terminal receipt")
        owner_record = _owner_record(
            validated,
            output_path=output_path,
            work_root=work_root,
        )
        with owner.open("xb") as stream:
            stream.write(_canonical_bytes(owner_record))
        claim_record = {
            "attempt_id": attempt_id,
            "authority_sha256": validated.binding["sha256"],
            "harness_commit": validated.harness_commit,
            "request_id": request_id,
            "schema": "anysolver.ge-beam3-mixed-one-time-claim-v1",
        }
        claim_payload = _canonical_bytes(claim_record)
        with claim_path.open("xb") as stream:
            stream.write(claim_payload)
    except BaseException:
        if owner.exists():
            owner.unlink()
        lock.rmdir()
        raise
    return OneTimeClaim(
        claim_path=claim_path,
        claim_binding={"bytes": len(claim_payload), "sha256": _sha256_bytes(claim_payload)},
        lock_directory=lock,
        owner_path=owner,
        receipt_path=receipt_path,
    )


def _write_receipt(
    claim: OneTimeClaim,
    validated: ValidatedAuthority,
    *,
    aggregate_core: dict[str, Any],
    output_path: Path,
    work_root: Path,
) -> dict[str, Any]:
    record = {
        "aggregate_core": aggregate_core,
        "attempt_id": validated.request["attempt_id"],
        "claim": claim.claim_binding,
        "intended_output": str(output_path.resolve()),
        "request_id": validated.request["request_id"],
        "schema": "anysolver.ge-beam3-mixed-one-time-receipt-v1",
        "work_root": str(work_root.resolve()),
    }
    payload = _canonical_bytes(record)
    with claim.receipt_path.open("xb") as stream:
        stream.write(payload)
    return {
        "bytes": len(payload),
        "path": str(claim.receipt_path.resolve()),
        "sha256": _sha256_bytes(payload),
        "terminal": aggregate_core["terminal"],
    }


def _release_claim_lock(claim: OneTimeClaim) -> None:
    _owner_payload, owner = _read_canonical_record(
        claim.owner_path, label="released global-slot owner"
    )
    _archive_global_slot(claim.lock_directory, claim.owner_path, owner)


def _publish_exclusive(
    output_path: Path,
    payload: bytes,
    *,
    attempt_id: str,
) -> None:
    """Publish complete bytes without overwrite or a visible partial record."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    staging = output_path.with_name(f".{output_path.name}.{attempt_id}.pending")
    if staging.exists():
        if not staging.is_file() or staging.is_symlink() or staging.read_bytes() != payload:
            raise ExclusiveOutputError("publication staging path is already occupied")
    else:
        with staging.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    try:
        os.link(staging, output_path)
    except FileExistsError as exc:
        raise ExclusiveOutputError(f"aggregate output already exists: {output_path}") from exc
    if not output_path.is_file() or output_path.is_symlink() or output_path.read_bytes() != payload:
        raise OSError("exclusive aggregate publication verification failed")
    staging.unlink()


def _validate_recovery_evidence(
    validated: ValidatedAuthority,
    aggregate_core: dict[str, Any],
    *,
    work_root: Path,
) -> None:
    """Recompute every recoverable classification from immutable raw evidence."""

    if not work_root.is_absolute() or _is_within(work_root, ROOT):
        raise AuthorityError("recovery work root is not external")
    if work_root.exists() and (not work_root.is_dir() or work_root.is_symlink()):
        raise AuthorityError("recovery work root is not a regular directory")
    expected_core_fields = {
        "adjudication",
        "authority",
        "candidate_id",
        "cycles",
        "determinism",
        "execution_bounds",
        "failure_class",
        "materialization",
        "mode",
        "processes",
        "production_restriction",
        "schema",
        "study_id",
        "terminal",
    }
    if (
        not isinstance(aggregate_core, dict)
        or set(aggregate_core) != expected_core_fields
        or aggregate_core["authority"] != validated.binding
        or aggregate_core["candidate_id"] != CANDIDATE_ID
        or aggregate_core["study_id"] != STUDY_ID
        or aggregate_core["mode"] != validated.binding["mode"]
        or aggregate_core["schema"] != AGGREGATE_SCHEMA
        or aggregate_core["execution_bounds"] != FROZEN_BOUNDS.authority_value()
        or aggregate_core["production_restriction"]
        != "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    ):
        raise AuthorityError("recoverable aggregate core identity mismatch")

    materialization = aggregate_core["materialization"]
    if (
        not isinstance(materialization, dict)
        or set(materialization) != {"manifest_sha256", "tree"}
        or materialization["tree"] != validated.harness_tree
        or (
            materialization["manifest_sha256"] is not None
            and not _is_hex(materialization["manifest_sha256"], 64)
        )
    ):
        raise AuthorityError("recoverable materialization binding is malformed")
    if (
        aggregate_core["failure_class"] is None
        and materialization["manifest_sha256"] is None
    ):
        raise AuthorityError(
            "recoverable success/finding evidence lacks a materialized candidate"
        )
    if materialization["manifest_sha256"] is not None:
        manifest_path = work_root / "materialized-tree-manifest.json"
        manifest_payload, manifest = _read_canonical_record(
            manifest_path, label="materialized-tree manifest"
        )
        if (
            _sha256_bytes(manifest_payload) != materialization["manifest_sha256"]
            or set(manifest) != {"commit", "files", "schema", "tree"}
            or manifest["schema"]
            != "anysolver.ge-beam3-mixed-materialized-tree-v1"
            or manifest["commit"] != validated.harness_commit
            or manifest["tree"] != validated.harness_tree
        ):
            raise AuthorityError("recoverable materialized-tree manifest mismatch")
        materialized = work_root / "materialized-harness"
        if (
            not materialized.is_dir()
            or materialized.is_symlink()
            or _git_text(materialized, "rev-parse", "HEAD")
            != validated.harness_commit
            or _git_text(materialized, "show", "-s", "--format=%T", "HEAD")
            != validated.harness_tree
            or _checkout_has_changes(materialized)
        ):
            raise AuthorityError("recoverable materialized Git identity mismatch")
        if manifest["files"] != _full_tree_manifest(
            materialized, validated.harness_commit
        ):
            raise AuthorityError("recoverable materialized Git tree mismatch")
        for row in manifest["files"]:
            if not isinstance(row, dict) or set(row) != {
                "git_blob_oid",
                "mode",
                "path",
                "sha256",
            }:
                raise AuthorityError("recoverable materialized file row is malformed")
            path = materialized / row["path"]
            if (
                not path.is_file()
                or path.is_symlink()
                or _sha256(path) != row["sha256"]
            ):
                raise AuthorityError(
                    f"recoverable materialized file mismatch: {row['path']}"
                )
        if tuple(candidate_manifest(materialized, validated.harness_commit)) != tuple(
            validated.manifest
        ):
            raise AuthorityError("recoverable candidate manifest mismatch")

    cycles = aggregate_core["cycles"]
    if (
        not isinstance(cycles, list)
        or len(cycles) != 2
        or any(
            not isinstance(cycle, dict)
            or set(cycle)
            != {"check", "checker_origin", "cycle", "producer_origin", "proof"}
            or cycle["cycle"] != index + 1
            for index, cycle in enumerate(cycles)
        )
    ):
        raise AuthorityError("recoverable cycle field set mismatch")
    cycle_directories = tuple(work_root / f"cycle-{cycle}" for cycle in (1, 2))
    raw_paths = [
        {
            "check": directory / "checker/check.json",
            "checker_origin": directory / "checker/checker-origin.json",
            "producer_origin": directory / "producer-origin.json",
            "proof": directory / "proof.json",
        }
        for directory in cycle_directories
    ]
    for index, cycle in enumerate(cycles):
        for name, path in raw_paths[index].items():
            if cycle[name] != _output_binding(path):
                raise AuthorityError(f"recoverable raw {name} binding mismatch")

    processes = aggregate_core["processes"]
    if not isinstance(processes, dict) or set(processes) != {"checkers", "producers"}:
        raise AuthorityError("recoverable process groups are malformed")
    for plural, role in (("producers", "producer"), ("checkers", "checker")):
        records = processes[plural]
        if not isinstance(records, list) or len(records) > 2:
            raise AuthorityError("recoverable process record count is malformed")
        for record in records:
            if (
                not isinstance(record, dict)
                or set(record)
                != {
                    "cycle",
                    "output",
                    "reason",
                    "returncode",
                    "role",
                    "stderr",
                    "stdout",
                    "tree_drained",
                }
                or record["role"] != role
                or record["cycle"] not in {1, 2}
                or not isinstance(record["returncode"], int)
                or record["tree_drained"] is not True
                or (
                    record["reason"] is not None
                    and not isinstance(record["reason"], str)
                )
            ):
                raise AuthorityError("recoverable process record is malformed")
            directory = cycle_directories[record["cycle"] - 1]
            if role == "checker":
                directory = directory / "checker"
                watched = directory / "check.json"
            else:
                watched = directory / "proof.json"
            if (
                record["output"] != _output_binding(watched)
                or record["stdout"] != _output_binding(directory / "stdout.log")
                or record["stderr"] != _output_binding(directory / "stderr.log")
            ):
                raise AuthorityError("recoverable process/log binding mismatch")
        if [record["cycle"] for record in records] != list(
            range(1, len(records) + 1)
        ):
            raise AuthorityError("recoverable process ordering mismatch")

    proof_paths = tuple(row["proof"] for row in raw_paths)
    producer_origin_paths = tuple(row["producer_origin"] for row in raw_paths)
    check_paths = tuple(row["check"] for row in raw_paths)
    checker_origin_paths = tuple(row["checker_origin"] for row in raw_paths)
    proof_identical = _identical_regular_files(proof_paths)
    check_identical = _identical_regular_files(check_paths)
    producer_origin_identical = _identical_regular_files(producer_origin_paths)
    checker_origin_identical = _identical_regular_files(checker_origin_paths)
    expected_determinism = {
        "check_bytes_identical": check_identical,
        "checker_origin_bytes_identical": checker_origin_identical,
        "producer_origin_bytes_identical": producer_origin_identical,
        "proof_bytes_identical": proof_identical,
    }
    if aggregate_core["determinism"] != expected_determinism:
        raise AuthorityError("recoverable determinism was not recomputed exactly")

    check_dispositions: list[str] = []
    check_details: list[dict[str, Any] | None] = []
    if len(processes["checkers"]) == 2:
        results = [
            _validate_check_record(path, process)
            for path, process in zip(check_paths, processes["checkers"])
        ]
        check_dispositions = [result[0] for result in results]
        check_details = [result[1] for result in results]
    finding_groups = sorted(
        {
            group
            for detail in check_details
            if detail is not None
            for group in detail["finding_groups"]
        },
        key=(
            "VARIATIONAL_IDENTITY",
            "REFERENCE_LINEAR_ALGEBRA",
            "FINITE_STATIC",
        ).index,
    )
    producer_processes_passed = bool(
        len(processes["producers"]) == 2
        and all(
            process["returncode"] == 0
            and process["reason"] is None
            and process["output"] is not None
            and process["tree_drained"] is True
            for process in processes["producers"]
        )
    )
    checker_processes_terminal = bool(
        len(processes["checkers"]) == 2
        and all(
            process["returncode"] in {0, 2}
            and process["reason"] is None
            and process["output"] is not None
            and process["tree_drained"] is True
            for process in processes["checkers"]
        )
    )
    producer_origins_valid = False
    if producer_processes_passed:
        try:
            for path in producer_origin_paths:
                _validate_origin_record(path, role="producer", validated=validated)
            producer_origins_valid = True
        except AuthorityError:
            pass
    checker_origins_valid = False
    if checker_processes_terminal:
        try:
            for path in checker_origin_paths:
                _validate_origin_record(path, role="checker", validated=validated)
            checker_origins_valid = True
        except AuthorityError:
            pass

    def registered_failure_token(value: Any, prefix: str) -> bool:
        if not isinstance(value, str) or not value.startswith(prefix):
            return False
        suffix = value[len(prefix) :]
        return bool(suffix) and all(
            character in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
            for character in suffix
        )

    recorded_failure = aggregate_core["failure_class"]
    expected_failure: str | None
    if materialization["manifest_sha256"] is None:
        if (
            processes != {"checkers": [], "producers": []}
            or any(cycle[name] is not None for cycle in cycles for name in raw_paths[0])
            or aggregate_core["determinism"]
            != {
                "check_bytes_identical": False,
                "checker_origin_bytes_identical": False,
                "producer_origin_bytes_identical": False,
                "proof_bytes_identical": False,
            }
            or not registered_failure_token(recorded_failure, "MATERIALIZATION_")
        ):
            raise AuthorityError("recoverable materialization failure is inconsistent")
        expected_failure = recorded_failure
    elif len(processes["producers"]) != 2:
        if not registered_failure_token(recorded_failure, "COORDINATOR_"):
            raise AuthorityError("recoverable producer launch failure is inconsistent")
        expected_failure = recorded_failure
    elif not producer_processes_passed:
        expected_failure = "PRODUCER_PROCESS"
    elif not producer_origins_valid:
        expected_failure = "PRODUCER_ORIGIN_BINDING"
    elif not proof_identical:
        expected_failure = "PRODUCER_NONDETERMINISM"
    elif not producer_origin_identical:
        expected_failure = "PRODUCER_ORIGIN_NONDETERMINISM"
    elif len(processes["checkers"]) != 2:
        if not registered_failure_token(recorded_failure, "COORDINATOR_"):
            raise AuthorityError("recoverable checker launch failure is inconsistent")
        expected_failure = recorded_failure
    elif not checker_processes_terminal:
        expected_failure = "CHECKER_PROCESS"
    elif not checker_origins_valid:
        expected_failure = "CHECKER_ORIGIN_BINDING"
    elif "MALFORMED_EVIDENCE" in check_dispositions:
        expected_failure = "CHECKER_EVIDENCE_MALFORMED"
    elif not check_identical:
        expected_failure = "CHECKER_NONDETERMINISM"
    elif not checker_origin_identical:
        expected_failure = "CHECKER_ORIGIN_NONDETERMINISM"
    elif len(set(check_dispositions)) != 1:
        expected_failure = "CHECKER_DISAGREEMENT"
    else:
        expected_failure = None
    if recorded_failure != expected_failure:
        raise AuthorityError("recoverable failure classification was not recomputed exactly")

    complete = expected_failure is None
    scientific_finding = bool(
        complete
        and check_dispositions
        and check_dispositions[0] == "SCIENTIFIC_FINDING"
    )
    expected_adjudication = {
        "checker_dispositions": check_dispositions,
        "finding_groups": finding_groups,
        "scientific_finding": scientific_finding,
    }
    if aggregate_core["adjudication"] != expected_adjudication:
        raise AuthorityError("recoverable adjudication was not recomputed exactly")
    if expected_failure is None:
        if not complete:
            raise AuthorityError("recoverable success/finding evidence is incomplete")
        expected_terminal = (
            _finding_terminal(aggregate_core["mode"], finding_groups)
            if scientific_finding
            else (
                "PROVISIONAL_GO_GE_BEAM3_MIXED_STRAIGHT_STATIC_CORE"
                if aggregate_core["mode"] == FORMAL_MODE
                else "NONCLASSIFYING_GE_BEAM3_MIXED_REHEARSAL_PASS"
            )
        )
    else:
        expected_terminal = (
            "BLOCKED_GE_BEAM3_MIXED_PROCESS_OR_EVIDENCE"
            if aggregate_core["mode"] == FORMAL_MODE
            else "NONCLASSIFYING_GE_BEAM3_MIXED_REHEARSAL_BLOCKED"
        )
    if aggregate_core["terminal"] != expected_terminal:
        raise AuthorityError("recoverable terminal does not follow precedence")


def _recover_publication(
    validated: ValidatedAuthority,
    *,
    output_path: Path,
    work_root: Path,
) -> dict[str, Any] | None:
    """Recover publication from an authoritative receipt without rerunning workers."""

    registry = Path(validated.request["registry_root"])
    # A crash can leave the exclusive slot behind after the terminal receipt is
    # durable.  Reconcile only a kernel-proven-dead owner; this never releases a
    # live or unidentifiable owner and never removes the one-time claim.
    _reconcile_stale_global_slot(registry)
    request_id = validated.request["request_id"]
    attempt_id = validated.request["attempt_id"]
    receipt_path = registry / "receipts" / f"{request_id}.{attempt_id}.receipt.json"
    if not receipt_path.exists():
        return None
    receipt_payload, receipt = _read_canonical_record(
        receipt_path, label="terminal execution receipt"
    )
    if set(receipt) != {
        "aggregate_core",
        "attempt_id",
        "claim",
        "intended_output",
        "request_id",
        "schema",
        "work_root",
    }:
        raise AuthorityError("terminal receipt field set mismatch")
    if (
        receipt["schema"] != "anysolver.ge-beam3-mixed-one-time-receipt-v1"
        or receipt["request_id"] != request_id
        or receipt["attempt_id"] != attempt_id
        or receipt["intended_output"] != str(output_path.resolve())
        or receipt["work_root"] != str(work_root.resolve())
    ):
        raise AuthorityError("terminal receipt execution identity mismatch")
    core = receipt["aggregate_core"]
    expected_core_fields = {
        "adjudication",
        "authority",
        "candidate_id",
        "cycles",
        "determinism",
        "execution_bounds",
        "failure_class",
        "materialization",
        "mode",
        "processes",
        "production_restriction",
        "schema",
        "study_id",
        "terminal",
    }
    allowed_terminals = (
        {
            "BLOCKED_GE_BEAM3_MIXED_PROCESS_OR_EVIDENCE",
            "NO_GO_GE_BEAM3_MIXED_VARIATIONAL_IDENTITY",
            "NO_GO_GE_BEAM3_MIXED_REFERENCE_LINEAR_ALGEBRA",
            "NO_GO_GE_BEAM3_MIXED_FINITE_STATIC",
            "PROVISIONAL_GO_GE_BEAM3_MIXED_STRAIGHT_STATIC_CORE",
        }
        if validated.binding["mode"] == FORMAL_MODE
        else {
            "NONCLASSIFYING_GE_BEAM3_MIXED_REHEARSAL_BLOCKED",
            "NONCLASSIFYING_GE_BEAM3_MIXED_REHEARSAL_FINDING",
            "NONCLASSIFYING_GE_BEAM3_MIXED_REHEARSAL_PASS",
        }
    )
    if (
        not isinstance(core, dict)
        or set(core) != expected_core_fields
        or core["authority"] != validated.binding
        or core["candidate_id"] != CANDIDATE_ID
        or core["study_id"] != STUDY_ID
        or core["mode"] != validated.binding["mode"]
        or core["schema"] != AGGREGATE_SCHEMA
        or core["execution_bounds"] != FROZEN_BOUNDS.authority_value()
        or core["production_restriction"]
        != "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
        or core["terminal"] not in allowed_terminals
    ):
        raise AuthorityError("terminal receipt aggregate core mismatch")
    claim_path = registry / "claims" / f"{request_id}.{attempt_id}.claim.json"
    claim_payload, claim = _read_canonical_record(claim_path, label="one-time claim")
    expected_claim_binding = {
        "bytes": len(claim_payload),
        "sha256": _sha256_bytes(claim_payload),
    }
    if (
        receipt["claim"] != expected_claim_binding
        or claim
        != {
            "attempt_id": attempt_id,
            "authority_sha256": validated.binding["sha256"],
            "harness_commit": validated.harness_commit,
            "request_id": request_id,
            "schema": "anysolver.ge-beam3-mixed-one-time-claim-v1",
        }
    ):
        raise AuthorityError("terminal receipt claim binding mismatch")
    _validate_recovery_evidence(
        validated,
        core,
        work_root=Path(receipt["work_root"]),
    )
    receipt_binding = {
        "bytes": len(receipt_payload),
        "path": str(receipt_path.resolve()),
        "sha256": _sha256_bytes(receipt_payload),
        "terminal": core["terminal"],
    }
    aggregate = {
        **core,
        "consumption": {
            "claim": {
                **expected_claim_binding,
                "path": str(claim_path.resolve()),
            },
            "receipt": receipt_binding,
        },
    }
    _publish_exclusive(
        output_path,
        _canonical_bytes(aggregate),
        attempt_id=attempt_id,
    )
    return aggregate


def _size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return -1


def _linux_process_tree(root_pid: int) -> set[int]:
    parent_by_pid: dict[int, int] = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / "stat").read_text(encoding="ascii").split()
            parent_by_pid[int(fields[0])] = int(fields[3])
        except (OSError, ValueError, IndexError):
            continue
    tree = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid, parent in parent_by_pid.items():
            if parent in tree and pid not in tree:
                tree.add(pid)
                changed = True
    return tree


if os.name == "nt":
    TH32CS_SNAPPROCESS = 0x00000002
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    PROCESS_VM_READ = 0x0010
    PROCESS_TERMINATE = 0x0001
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    class _PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * 260),
        ]

    class _FILETIME(ctypes.Structure):
        _fields_ = (("low", wintypes.DWORD), ("high", wintypes.DWORD))

    class _PROCESS_MEMORY_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    class _IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class _SYSTEM_TIMEOFDAY_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BootTime", ctypes.c_longlong),
            ("CurrentTime", ctypes.c_longlong),
            ("TimeZoneBias", ctypes.c_longlong),
            ("CurrentTimeZoneId", wintypes.ULONG),
            ("Reserved", wintypes.ULONG),
            ("BootTimeBias", ctypes.c_ulonglong),
            ("SleepTimeBias", ctypes.c_ulonglong),
        ]

    class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
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

    class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", _IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    class _JOBOBJECT_BASIC_ACCOUNTING_INFORMATION(ctypes.Structure):
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

    # ctypes defaults handle-returning functions to a 32-bit integer, which
    # truncates real handles in 64-bit Python.  Declare every native boundary
    # used below before the first call.
    _KERNEL32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _PSAPI = ctypes.WinDLL("psapi", use_last_error=True)
    _KERNEL32.CreateToolhelp32Snapshot.argtypes = (wintypes.DWORD, wintypes.DWORD)
    _KERNEL32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    _KERNEL32.Process32FirstW.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(_PROCESSENTRY32W),
    )
    _KERNEL32.Process32FirstW.restype = wintypes.BOOL
    _KERNEL32.Process32NextW.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(_PROCESSENTRY32W),
    )
    _KERNEL32.Process32NextW.restype = wintypes.BOOL
    _KERNEL32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    _KERNEL32.OpenProcess.restype = wintypes.HANDLE
    _KERNEL32.CloseHandle.argtypes = (wintypes.HANDLE,)
    _KERNEL32.CloseHandle.restype = wintypes.BOOL
    _KERNEL32.GetProcessTimes.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(_FILETIME),
        ctypes.POINTER(_FILETIME),
        ctypes.POINTER(_FILETIME),
        ctypes.POINTER(_FILETIME),
    )
    _KERNEL32.GetProcessTimes.restype = wintypes.BOOL
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
    _KERNEL32.TerminateProcess.argtypes = (wintypes.HANDLE, wintypes.UINT)
    _KERNEL32.TerminateProcess.restype = wintypes.BOOL
    _PSAPI.GetProcessMemoryInfo.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(_PROCESS_MEMORY_COUNTERS),
        wintypes.DWORD,
    )
    _PSAPI.GetProcessMemoryInfo.restype = wintypes.BOOL
    _NTDLL = ctypes.WinDLL("ntdll", use_last_error=True)
    _NTDLL.NtResumeProcess.argtypes = (wintypes.HANDLE,)
    _NTDLL.NtResumeProcess.restype = ctypes.c_long
    _NTDLL.NtQuerySystemInformation.argtypes = (
        wintypes.ULONG,
        ctypes.c_void_p,
        wintypes.ULONG,
        ctypes.POINTER(wintypes.ULONG),
    )
    _NTDLL.NtQuerySystemInformation.restype = ctypes.c_long


def _windows_process_tree(root_pid: int) -> set[int]:
    if os.name != "nt":
        return {root_pid}
    kernel32 = _KERNEL32
    snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == INVALID_HANDLE_VALUE:
        return {root_pid}
    parents: dict[int, int] = {}
    entry = _PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(entry)
    try:
        if kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
            while True:
                parents[int(entry.th32ProcessID)] = int(entry.th32ParentProcessID)
                if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                    break
    finally:
        kernel32.CloseHandle(snapshot)
    tree = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid, parent in parents.items():
            if parent in tree and pid not in tree:
                tree.add(pid)
                changed = True
    return tree


def _process_tree(root_pid: int) -> set[int]:
    if os.name == "nt":
        return _windows_process_tree(root_pid)
    if sys.platform.startswith("linux"):
        return _linux_process_tree(root_pid)
    return {root_pid}


def _linux_metrics(pids: Iterable[int]) -> tuple[int, int]:
    ticks = os.sysconf("SC_CLK_TCK")
    cpu_ticks = 0
    rss_bytes = 0
    page_size = os.sysconf("SC_PAGE_SIZE")
    for pid in pids:
        try:
            stat = (Path("/proc") / str(pid) / "stat").read_text(encoding="ascii").split()
            cpu_ticks += int(stat[13]) + int(stat[14])
            statm = (Path("/proc") / str(pid) / "statm").read_text(encoding="ascii").split()
            rss_bytes += int(statm[1]) * page_size
        except (OSError, ValueError, IndexError):
            continue
    return int(cpu_ticks * 1_000_000_000 / ticks), rss_bytes


def _windows_metrics(pids: Iterable[int]) -> tuple[int, int]:
    if os.name != "nt":
        return 0, 0
    kernel32 = _KERNEL32
    psapi = _PSAPI
    cpu_100ns = 0
    rss_bytes = 0
    for pid in pids:
        handle = kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ, False, pid
        )
        if not handle:
            continue
        try:
            created = _FILETIME()
            exited = _FILETIME()
            kernel = _FILETIME()
            user = _FILETIME()
            if kernel32.GetProcessTimes(
                handle,
                ctypes.byref(created),
                ctypes.byref(exited),
                ctypes.byref(kernel),
                ctypes.byref(user),
            ):
                cpu_100ns += (
                    (kernel.high << 32)
                    + kernel.low
                    + (user.high << 32)
                    + user.low
                )
            memory = _PROCESS_MEMORY_COUNTERS()
            memory.cb = ctypes.sizeof(memory)
            if psapi.GetProcessMemoryInfo(handle, ctypes.byref(memory), memory.cb):
                rss_bytes += int(memory.WorkingSetSize)
        finally:
            kernel32.CloseHandle(handle)
    return cpu_100ns * 100, rss_bytes


def _tree_metrics(root_pid: int) -> tuple[int, int]:
    pids = _process_tree(root_pid)
    if os.name == "nt":
        return _windows_metrics(pids)
    if sys.platform.startswith("linux"):
        return _linux_metrics(pids)
    return 0, 0


def _boot_identity() -> str:
    """Return a kernel-provided identity that changes across host boots."""

    if os.name == "nt":
        information = _SYSTEM_TIMEOFDAY_INFORMATION()
        returned = wintypes.ULONG()
        status = _NTDLL.NtQuerySystemInformation(
            3,
            ctypes.byref(information),
            ctypes.sizeof(information),
            ctypes.byref(returned),
        )
        if status != 0 or information.BootTime <= 0:
            raise AuthorityError(
                f"could not obtain Windows boot identity (NTSTATUS {status:#x})"
            )
        return f"WINDOWS_NT_BOOT_TIME:{int(information.BootTime)}"
    if sys.platform.startswith("linux"):
        path = Path("/proc/sys/kernel/random/boot_id")
        try:
            value = path.read_text(encoding="ascii").strip().lower()
        except OSError as exc:
            raise AuthorityError("could not obtain Linux boot identity") from exc
        if len(value) != 36 or any(
            character not in "0123456789abcdef-" for character in value
        ):
            raise AuthorityError("Linux boot identity is malformed")
        return f"LINUX_BOOT_ID:{value}"
    raise AuthorityError("this platform has no registered boot-identity provider")


def _process_start_identity(pid: int) -> str | None:
    """Return the kernel start identity, None only when the PID is absent."""

    if not isinstance(pid, int) or pid <= 0:
        return None
    if os.name == "nt":
        handle = _KERNEL32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            error = ctypes.get_last_error()
            if error == 87:  # ERROR_INVALID_PARAMETER: no such PID.
                return None
            raise AuthorityError(
                f"could not prove Windows process identity for PID {pid}: {error}"
            )
        try:
            created = _FILETIME()
            exited = _FILETIME()
            kernel = _FILETIME()
            user = _FILETIME()
            if not _KERNEL32.GetProcessTimes(
                handle,
                ctypes.byref(created),
                ctypes.byref(exited),
                ctypes.byref(kernel),
                ctypes.byref(user),
            ):
                raise AuthorityError(
                    f"could not read Windows process start identity for PID {pid}"
                )
            value = (int(created.high) << 32) + int(created.low)
            return f"WINDOWS_PROCESS_CREATION:{value}"
        finally:
            _KERNEL32.CloseHandle(handle)
    if sys.platform.startswith("linux"):
        try:
            fields = (Path("/proc") / str(pid) / "stat").read_text(
                encoding="ascii"
            ).split()
        except FileNotFoundError:
            return None
        except (OSError, PermissionError) as exc:
            raise AuthorityError(
                f"could not prove Linux process identity for PID {pid}"
            ) from exc
        if len(fields) <= 21:
            raise AuthorityError("Linux process start identity is malformed")
        try:
            start_ticks = int(fields[21])
        except ValueError as exc:
            raise AuthorityError("Linux process start identity is malformed") from exc
        return f"LINUX_PROCESS_START_TICKS:{start_ticks}"
    raise AuthorityError("this platform has no registered process-identity provider")


def _owner_record(
    validated: ValidatedAuthority,
    *,
    output_path: Path,
    work_root: Path,
) -> dict[str, Any]:
    host = platform.node().strip()
    start = _process_start_identity(os.getpid())
    if not host or start is None:
        raise AuthorityError("could not construct execution-owner identity")
    return {
        "attempt_id": validated.request["attempt_id"],
        "authority_sha256": validated.binding["sha256"],
        "boot_identity": _boot_identity(),
        "host": host,
        "intended_output": str(output_path.resolve()),
        "mode": validated.binding["mode"],
        "owner_pid": os.getpid(),
        "owner_process_start": start,
        "request_id": validated.request["request_id"],
        "schema": "anysolver.ge-beam3-mixed-global-slot-v2",
        "work_root": str(work_root.resolve()),
    }


class _WindowsJob:
    """Mandatory Windows Job Object assigned before a child may execute."""

    def __init__(self, process: subprocess.Popen[bytes], memory_limit: int):
        self.handle: int | None = None
        if os.name != "nt":
            return
        kernel32 = _KERNEL32
        handle = kernel32.CreateJobObjectW(None, None)
        if not handle:
            raise OSError(ctypes.get_last_error(), "CreateJobObjectW failed")
        information = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        # JOB_OBJECT_LIMIT_JOB_MEMORY | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        information.BasicLimitInformation.LimitFlags = 0x00000200 | 0x00002000
        information.JobMemoryLimit = memory_limit
        configured = kernel32.SetInformationJobObject(
            handle, 9, ctypes.byref(information), ctypes.sizeof(information)
        )
        assigned = configured and kernel32.AssignProcessToJobObject(
            handle, wintypes.HANDLE(process._handle)  # type: ignore[attr-defined]
        )
        if not assigned:
            kernel32.CloseHandle(handle)
            raise OSError(ctypes.get_last_error(), "AssignProcessToJobObject failed")
        self.handle = handle

    def resume(self, process: subprocess.Popen[bytes]) -> None:
        if os.name == "nt":
            if self.handle is None:
                raise OSError("Windows child has no Job Object")
            status = _NTDLL.NtResumeProcess(
                wintypes.HANDLE(process._handle)  # type: ignore[attr-defined]
            )
            if status != 0:
                self.terminate()
                raise OSError(f"NtResumeProcess failed with NTSTATUS {status:#x}")

    def terminate(self) -> None:
        if self.handle is not None:
            if not _KERNEL32.TerminateJobObject(self.handle, 2):
                raise OSError(ctypes.get_last_error(), "TerminateJobObject failed")

    def drain(self, *, timeout_seconds: float = 10.0) -> None:
        """Terminate the job and prove that it has no active processes."""

        if os.name != "nt" or self.handle is None:
            return
        self.terminate()
        deadline = time.monotonic() + timeout_seconds
        while True:
            accounting = _JOBOBJECT_BASIC_ACCOUNTING_INFORMATION()
            returned = wintypes.DWORD()
            if not _KERNEL32.QueryInformationJobObject(
                self.handle,
                1,
                ctypes.byref(accounting),
                ctypes.sizeof(accounting),
                ctypes.byref(returned),
            ):
                raise OSError(
                    ctypes.get_last_error(), "QueryInformationJobObject failed"
                )
            if accounting.ActiveProcesses == 0:
                return
            if time.monotonic() >= deadline:
                raise RuntimeError("Windows Job Object did not drain")
            time.sleep(0.01)

    def close(self) -> None:
        if self.handle is not None:
            _KERNEL32.CloseHandle(self.handle)
            self.handle = None


def _terminate_tree(state: ChildState) -> None:
    if state.process.poll() is not None:
        return
    if os.name == "nt":
        if state.job is None or state.job.handle is None:
            raise RuntimeError("Windows process tree escaped mandatory Job Object")
        state.job.terminate()
    else:
        try:
            os.killpg(state.process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            try:
                state.process.kill()
            except ProcessLookupError:
                pass


def _signature(state: ChildState) -> tuple[int, int, int]:
    state.known_pids.update(_process_tree(state.process.pid))
    cpu_ns, _rss = _tree_metrics(state.process.pid)
    return (_size(state.stdout_path) + _size(state.stderr_path), _size(state.spec.watched_output), cpu_ns)


def _start_child(spec: ChildSpec, bounds: ExecutionBounds) -> ChildState:
    spec.directory.mkdir(parents=False, exist_ok=False)
    stdout_path = spec.directory / "stdout.log"
    stderr_path = spec.directory / "stderr.log"
    stdout_stream = stdout_path.open("xb")
    stderr_stream = stderr_path.open("xb")
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("PYTHON")
        and key.upper() != "VIRTUAL_ENV"
        and not key.upper().startswith("GIT_")
    }
    for name in NUMERICAL_THREAD_VARIABLES:
        environment[name] = str(bounds.numerical_library_threads)
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_TERMINAL_PROMPT": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONNOUSERSITE": "1",
            "PYTHONSAFEPATH": "1",
        }
    )
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | WINDOWS_CREATE_SUSPENDED
    preexec_fn = None
    if os.name != "nt":
        def apply_memory_limit() -> None:
            # RLIMIT_AS is inherited by descendants.  The monitor separately
            # enforces the aggregate process-tree resident-memory bound.
            import resource

            resource.setrlimit(
                resource.RLIMIT_AS,
                (bounds.memory_limit_bytes, bounds.memory_limit_bytes),
            )

        preexec_fn = apply_memory_limit
    try:
        process = subprocess.Popen(
            spec.command,
            cwd=spec.directory,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=stdout_stream,
            stderr=stderr_stream,
            creationflags=creationflags,
            start_new_session=os.name != "nt",
            preexec_fn=preexec_fn,
        )
    except BaseException:
        stdout_stream.close()
        stderr_stream.close()
        raise
    job: _WindowsJob | None = None
    try:
        job = _WindowsJob(process, bounds.memory_limit_bytes)
        if os.name == "nt":
            job.resume(process)
    except BaseException:
        try:
            process.kill()
            process.wait(timeout=10)
        finally:
            if job is not None:
                job.close()
            stdout_stream.close()
            stderr_stream.close()
        raise
    now = time.monotonic()
    state = ChildState(
        spec=spec,
        process=process,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        stdout_stream=stdout_stream,
        stderr_stream=stderr_stream,
        started=now,
        last_activity=now,
        last_signature=(0, -1, 0),
        job=job,
        known_pids={process.pid},
    )
    state.last_signature = _signature(state)
    return state


def _finish_child(state: ChildState) -> None:
    first_error: BaseException | None = None
    try:
        try:
            state.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _terminate_tree(state)
            state.process.wait(timeout=10)
    except BaseException as exc:
        first_error = exc

    try:
        # Drain descendants even if a nominally successful parent neglected
        # to join them.  Windows requires successful Job Object accounting;
        # there is deliberately no PID-only fallback on that platform.
        if os.name == "nt":
            if state.job is None or state.job.handle is None:
                raise RuntimeError("Windows process completed outside mandatory Job Object")
            state.job.drain()
            state.tree_drained = True
        else:
            try:
                os.killpg(state.process.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            deadline = time.monotonic() + 10.0
            while True:
                try:
                    os.killpg(state.process.pid, 0)
                except ProcessLookupError:
                    state.tree_drained = True
                    break
                except PermissionError:
                    raise RuntimeError("could not prove POSIX process-group drainage")
                if time.monotonic() >= deadline:
                    raise RuntimeError("POSIX process group did not drain")
                time.sleep(0.01)
    except BaseException as exc:
        if first_error is None:
            first_error = exc
    finally:
        # Closing a kill-on-close Windows Job handle is the last-resort tree
        # termination mechanism.  It and both log streams must be closed even
        # when termination, accounting, or drainage itself fails.
        for resource in (state.stdout_stream, state.stderr_stream, state.job):
            if resource is None:
                continue
            try:
                resource.close()
            except BaseException as exc:
                if first_error is None:
                    first_error = exc

    if first_error is not None:
        raise first_error


def _cleanup_wave_states(states: list[ChildState]) -> None:
    """Attempt termination and finalization for every launched child."""

    first_error: BaseException | None = None
    for state in states:
        if state.process.poll() is None:
            state.forced_reason = state.forced_reason or "COORDINATOR_EXCEPTION"
            try:
                _terminate_tree(state)
            except BaseException as exc:
                if first_error is None:
                    first_error = exc
    for state in states:
        try:
            _finish_child(state)
        except BaseException as exc:
            if first_error is None:
                first_error = exc
    if first_error is not None:
        raise first_error


def _child_record(state: ChildState) -> dict[str, Any]:
    output = state.spec.watched_output
    output_binding: dict[str, Any] | None = None
    if output.is_file() and not output.is_symlink():
        payload = output.read_bytes()
        output_binding = {"bytes": len(payload), "sha256": _sha256_bytes(payload)}
    return {
        "cycle": state.spec.cycle,
        "output": output_binding,
        "reason": state.forced_reason,
        "returncode": state.process.returncode,
        "role": state.spec.role,
        "stderr": {"bytes": _size(state.stderr_path), "sha256": _sha256(state.stderr_path)},
        "stdout": {"bytes": _size(state.stdout_path), "sha256": _sha256(state.stdout_path)},
        "tree_drained": state.tree_drained,
    }


def _run_wave(
    specs: tuple[ChildSpec, ...],
    *,
    bounds: ExecutionBounds,
    poll_seconds: float = 0.1,
    absolute_deadline: float | None = None,
) -> list[dict[str, Any]]:
    if len(specs) > 2:
        raise ValueError("this runner permits at most two concurrent children")
    states: list[ChildState] = []
    wave_started = time.monotonic()
    deadline = (
        wave_started + bounds.complete_wave_wall_seconds
        if absolute_deadline is None
        else min(absolute_deadline, wave_started + bounds.complete_wave_wall_seconds)
    )
    try:
        for spec in specs:
            states.append(_start_child(spec, bounds))
        while any(state.process.poll() is None for state in states):
            now = time.monotonic()
            wave_expired = now > deadline
            for state in states:
                if state.process.poll() is not None:
                    continue
                signature = _signature(state)
                _cpu_ns, rss_bytes = _tree_metrics(state.process.pid)
                if signature != state.last_signature:
                    state.last_signature = signature
                    state.last_activity = now
                reason: str | None = None
                if wave_expired:
                    reason = "COMPLETE_WAVE_WALL_LIMIT"
                elif now - state.started > bounds.child_wall_seconds:
                    reason = "CHILD_WALL_LIMIT"
                elif rss_bytes > bounds.memory_limit_bytes:
                    reason = "PROCESS_TREE_MEMORY_LIMIT"
                elif now - state.last_activity > bounds.inactivity_seconds:
                    reason = "PROCESS_TREE_INACTIVITY_LIMIT"
                if reason is not None:
                    state.forced_reason = reason
                    _terminate_tree(state)
            if any(state.process.poll() is None for state in states):
                time.sleep(poll_seconds)
    finally:
        _cleanup_wave_states(states)
    return [_child_record(state) for state in sorted(states, key=lambda item: item.spec.cycle)]


def _output_binding(path: Path) -> dict[str, Any] | None:
    try:
        if not path.is_file() or path.is_symlink():
            return None
        payload = path.read_bytes()
    except OSError:
        return None
    return {"bytes": len(payload), "sha256": _sha256_bytes(payload)}


def _identical_regular_files(paths: tuple[Path, Path]) -> bool:
    try:
        return all(path.is_file() and not path.is_symlink() for path in paths) and (
            paths[0].read_bytes() == paths[1].read_bytes()
        )
    except OSError:
        return False


def _bool_dict(value: Any, exact_keys: set[str]) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == exact_keys
        and all(isinstance(item, bool) for item in value.values())
    )


def _validate_check_record(
    path: Path, process_record: dict[str, Any]
) -> tuple[str, dict[str, Any] | None]:
    """Return PASS, SCIENTIFIC_FINDING, or MALFORMED_EVIDENCE."""

    try:
        payload, record = _read_canonical_record(path, label="finite-check record")
        if set(record) != CHECK_FIELDS or record["schema"] != CHECK_SCHEMA:
            return "MALFORMED_EVIDENCE", None
        if record["candidate_id"] != CANDIDATE_ID:
            return "MALFORMED_EVIDENCE", None
        if not _bool_dict(record["authority_bindings"], CHECK_BINDING_KEYS):
            return "MALFORMED_EVIDENCE", None
        if not all(record["authority_bindings"].values()):
            return "MALFORMED_EVIDENCE", None
        expected_import_boundary = {
            "anysolver": False,
            "legacy_beam": False,
            "production_ad": False,
            "v1_beam": False,
        }
        if record["checker_import_boundary"] != expected_import_boundary:
            return "MALFORMED_EVIDENCE", None
        if not _bool_dict(
            record["coverage"],
            COVERAGE_EVIDENCE_PREDICATES | COVERAGE_SCIENTIFIC_PREDICATES,
        ):
            return "MALFORMED_EVIDENCE", None
        if not _bool_dict(record["reversal"], {"energy", "residual", "tangent"}):
            return "MALFORMED_EVIDENCE", None
        cases = record["cases"]
        if not isinstance(cases, list) or len(cases) != len(CASE_ORDER):
            return "MALFORMED_EVIDENCE", None
        if tuple(case.get("case_id") for case in cases if isinstance(case, dict)) != CASE_ORDER:
            return "MALFORMED_EVIDENCE", None
        evidence_predicates: list[bool] = []
        scientific_predicates: list[bool] = []
        false_variational: list[str] = []
        false_reference_linear: list[str] = []
        false_finite_static: list[str] = []
        for case in cases:
            if not isinstance(case, dict) or set(case) != CASE_FIELDS:
                return "MALFORMED_EVIDENCE", None
            if not _bool_dict(
                case["predicates"],
                CASE_EVIDENCE_PREDICATES | CASE_SCIENTIFIC_PREDICATES,
            ):
                return "MALFORMED_EVIDENCE", None
            metrics = case["metrics"]
            if not isinstance(metrics, dict) or set(metrics) != CASE_METRIC_KEYS:
                return "MALFORMED_EVIDENCE", None
            if not all(
                isinstance(value, str) and math.isfinite(float(value))
                for value in metrics.values()
            ):
                return "MALFORMED_EVIDENCE", None
            if not _is_hex(case["registered_input_sha256"], 64):
                return "MALFORMED_EVIDENCE", None
            evidence_predicates.extend(
                case["predicates"][name] for name in CASE_EVIDENCE_PREDICATES
            )
            scientific_predicates.extend(
                case["predicates"][name] for name in CASE_SCIENTIFIC_PREDICATES
            )
            for name in CASE_SCIENTIFIC_PREDICATES:
                if case["predicates"][name]:
                    continue
                target = (
                    false_variational
                    if name in CASE_VARIATIONAL_PREDICATES
                    else false_finite_static
                )
                target.append(f"case:{case['case_id']}:{name}")
        evidence_predicates.extend(
            record["coverage"][name] for name in COVERAGE_EVIDENCE_PREDICATES
        )
        scientific_predicates.extend(
            record["coverage"][name] for name in COVERAGE_SCIENTIFIC_PREDICATES
        )
        scientific_predicates.extend(record["reversal"].values())
        for name in COVERAGE_SCIENTIFIC_PREDICATES:
            if record["coverage"][name]:
                continue
            target = (
                false_reference_linear
                if name in COVERAGE_REFERENCE_LINEAR_PREDICATES
                else false_finite_static
            )
            target.append(f"coverage:{name}")
        false_variational.extend(
            f"reversal:{name}"
            for name, passed in record["reversal"].items()
            if not passed
        )
        if not all(evidence_predicates):
            return "MALFORMED_EVIDENCE", None
        scientific_pass = all(scientific_predicates)
        expected_terminal = (
            "NONCLASSIFYING_FINITE_GATE_PASS"
            if scientific_pass
            else "NONCLASSIFYING_FINITE_GATE_FINDING"
        )
        expected_returncode = 0 if scientific_pass else 2
        if (
            record["terminal"] != expected_terminal
            or process_record.get("returncode") != expected_returncode
            or process_record.get("reason") is not None
        ):
            return "MALFORMED_EVIDENCE", None
        disposition = "PASS" if scientific_pass else "SCIENTIFIC_FINDING"
        finding_groups = []
        if false_variational:
            finding_groups.append("VARIATIONAL_IDENTITY")
        if false_reference_linear:
            finding_groups.append("REFERENCE_LINEAR_ALGEBRA")
        if false_finite_static:
            finding_groups.append("FINITE_STATIC")
        return disposition, {
            "bytes": len(payload),
            "finding_groups": finding_groups,
            "false_predicates": sorted(
                false_variational + false_reference_linear + false_finite_static
            ),
            "sha256": _sha256_bytes(payload),
        }
    except (AuthorityError, KeyError, TypeError, ValueError, OverflowError):
        return "MALFORMED_EVIDENCE", None


def _finalize_claimed_execution(
    *,
    aggregate_core: dict[str, Any],
    claim: OneTimeClaim,
    output_path: Path,
    validated: ValidatedAuthority,
    work_root: Path,
) -> dict[str, Any]:
    """Write the authoritative receipt, then publish its recoverable aggregate."""

    # The receipt is the durable point of no return and can later reconstruct
    # publication without rerunning a consumed request.  Therefore validate the
    # complete core against raw evidence *before* making that receipt durable.
    _validate_recovery_evidence(
        validated,
        aggregate_core,
        work_root=work_root,
    )
    receipt_binding = _write_receipt(
        claim,
        validated,
        aggregate_core=aggregate_core,
        output_path=output_path,
        work_root=work_root,
    )
    aggregate = {
        **aggregate_core,
        "consumption": {
            "claim": {
                **claim.claim_binding,
                "path": str(claim.claim_path.resolve()),
            },
            "receipt": receipt_binding,
        },
    }
    _publish_exclusive(
        output_path,
        _canonical_bytes(aggregate),
        attempt_id=validated.request["attempt_id"],
    )
    return aggregate


def _finding_terminal(mode: str, finding_groups: list[str]) -> str:
    if mode == REHEARSAL_MODE:
        return "NONCLASSIFYING_GE_BEAM3_MIXED_REHEARSAL_FINDING"
    if "VARIATIONAL_IDENTITY" in finding_groups:
        return "NO_GO_GE_BEAM3_MIXED_VARIATIONAL_IDENTITY"
    if "REFERENCE_LINEAR_ALGEBRA" in finding_groups:
        return "NO_GO_GE_BEAM3_MIXED_REFERENCE_LINEAR_ALGEBRA"
    return "NO_GO_GE_BEAM3_MIXED_FINITE_STATIC"


def run_bounded(
    *,
    authority_path: Path,
    output_path: Path,
    work_root: Path,
    mode: str,
    repository: Path = ROOT,
    bounds: ExecutionBounds = FROZEN_BOUNDS,
) -> dict[str, Any]:
    """Run two producer replicas, then two checker replicas, exactly once."""

    # Authority is validated before output directories or child processes exist.
    validated = validate_execution_authority(
        authority_path, mode=mode, repository=repository
    )
    if bounds != FROZEN_BOUNDS:
        raise AuthorityError("formal entry point requires the frozen execution bounds")
    if _is_within(output_path, repository) or _is_within(work_root, repository):
        raise AuthorityError("evidence outputs must be external to the repository")
    registry = Path(validated.request["registry_root"])
    if _is_within(output_path, registry) or _is_within(work_root, registry):
        raise AuthorityError("evidence outputs must be separate from the request registry")
    if _is_within(output_path, work_root):
        raise AuthorityError("canonical aggregate and diagnostic work root must be separate")
    if output_path.exists():
        raise ExclusiveOutputError(f"aggregate output already exists: {output_path}")
    recovered = _recover_publication(
        validated,
        output_path=output_path,
        work_root=work_root,
    )
    if recovered is not None:
        return recovered
    if work_root.exists():
        raise ExclusiveOutputError(f"work root already exists: {work_root}")
    claim = _acquire_one_time_claim(
        validated,
        output_path=output_path,
        work_root=work_root,
    )
    try:
        work_root.mkdir(parents=True, exist_ok=False)
        (
            materialized,
            materialization_manifest,
            materialization_sha256,
        ) = _materialize_harness(repository, validated, work_root)
    except BaseException as exc:
        terminal = (
            "BLOCKED_GE_BEAM3_MIXED_PROCESS_OR_EVIDENCE"
            if mode == FORMAL_MODE
            else "NONCLASSIFYING_GE_BEAM3_MIXED_REHEARSAL_BLOCKED"
        )
        empty_cycles = [
            {
                "check": None,
                "checker_origin": None,
                "cycle": cycle,
                "producer_origin": None,
                "proof": None,
            }
            for cycle in (1, 2)
        ]
        core = {
            "adjudication": {
                "checker_dispositions": [],
                "finding_groups": [],
                "scientific_finding": False,
            },
            "authority": validated.binding,
            "candidate_id": CANDIDATE_ID,
            "cycles": empty_cycles,
            "determinism": {
                "check_bytes_identical": False,
                "checker_origin_bytes_identical": False,
                "producer_origin_bytes_identical": False,
                "proof_bytes_identical": False,
            },
            "execution_bounds": FROZEN_BOUNDS.authority_value(),
            "failure_class": f"MATERIALIZATION_{type(exc).__name__.upper()}",
            "materialization": {
                "manifest_sha256": None,
                "tree": validated.harness_tree,
            },
            "mode": mode,
            "processes": {"checkers": [], "producers": []},
            "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
            "schema": AGGREGATE_SCHEMA,
            "study_id": STUDY_ID,
            "terminal": terminal,
        }
        try:
            return _finalize_claimed_execution(
                aggregate_core=core,
                claim=claim,
                output_path=output_path,
                validated=validated,
                work_root=work_root,
            )
        finally:
            _release_claim_lock(claim)
    cycle_directories = tuple(work_root / f"cycle-{cycle}" for cycle in (1, 2))
    complete_deadline = time.monotonic() + bounds.complete_wave_wall_seconds
    proof_paths = tuple(directory / "proof.json" for directory in cycle_directories)
    producer_origin_paths = tuple(
        directory / "producer-origin.json" for directory in cycle_directories
    )
    checker_records: list[dict[str, Any]] = []
    check_paths = tuple(
        directory / "checker" / "check.json" for directory in cycle_directories
    )
    checker_origin_paths = tuple(
        directory / "checker" / "checker-origin.json"
        for directory in cycle_directories
    )
    producer_records: list[dict[str, Any]] = []
    failure_class: str | None = None
    terminal = (
        "BLOCKED_GE_BEAM3_MIXED_PROCESS_OR_EVIDENCE"
        if mode == FORMAL_MODE
        else "NONCLASSIFYING_GE_BEAM3_MIXED_REHEARSAL_BLOCKED"
    )
    check_dispositions: list[str] = []
    check_details: list[dict[str, Any] | None] = []
    origin_bindings: dict[str, list[dict[str, Any]]] = {
        "checkers": [],
        "producers": [],
    }
    proof_identical = False
    check_identical = False
    producer_origin_identical = False
    checker_origin_identical = False
    try:
        producer_specs = tuple(
            ChildSpec(
                role="producer",
                cycle=cycle,
                command=_isolated_command(
                    validated=validated,
                    materialized=materialized,
                    materialization_manifest=materialization_manifest,
                    materialization_sha256=materialization_sha256,
                    role="producer",
                    origin_output=origin,
                    script_relative="docs/reference_cases/ge_beam3_mixed_finite_producer.py",
                    arguments=("--output", str(proof)),
                ),
                directory=directory,
                watched_output=proof,
            )
            for cycle, directory, proof, origin in zip(
                (1, 2), cycle_directories, proof_paths, producer_origin_paths
            )
        )
        producer_records = _run_wave(
            producer_specs, bounds=bounds, absolute_deadline=complete_deadline
        )
        producers_passed = all(
            record["returncode"] == 0
            and record["reason"] is None
            and record["output"] is not None
            and record["tree_drained"] is True
            for record in producer_records
        )
        if producers_passed:
            try:
                origin_bindings["producers"] = [
                    _validate_origin_record(path, role="producer", validated=validated)
                    for path in producer_origin_paths
                ]
            except AuthorityError:
                producers_passed = False
                failure_class = "PRODUCER_ORIGIN_BINDING"
        if producers_passed:
            proof_identical = _identical_regular_files(proof_paths)
            producer_origin_identical = _identical_regular_files(
                producer_origin_paths
            )
            if not proof_identical:
                producers_passed = False
                failure_class = "PRODUCER_NONDETERMINISM"
            elif not producer_origin_identical:
                producers_passed = False
                failure_class = "PRODUCER_ORIGIN_NONDETERMINISM"
        if producers_passed:
            checker_specs = tuple(
                ChildSpec(
                    role="checker",
                    cycle=cycle,
                    command=_isolated_command(
                        validated=validated,
                        materialized=materialized,
                        materialization_manifest=materialization_manifest,
                        materialization_sha256=materialization_sha256,
                        role="checker",
                        origin_output=origin,
                        script_relative="docs/reference_cases/ge_beam3_mixed_finite_checker.py",
                        arguments=("--proof", str(proof), "--output", str(check)),
                    ),
                    directory=directory / "checker",
                    watched_output=check,
                )
                for cycle, directory, proof, check, origin in zip(
                    (1, 2),
                    cycle_directories,
                    proof_paths,
                    check_paths,
                    checker_origin_paths,
                )
            )
            checker_records = _run_wave(
                checker_specs, bounds=bounds, absolute_deadline=complete_deadline
            )
            checker_processes_terminal = all(
                record["returncode"] in {0, 2}
                and record["reason"] is None
                and record["output"] is not None
                and record["tree_drained"] is True
                for record in checker_records
            )
            if not checker_processes_terminal:
                failure_class = "CHECKER_PROCESS"
            else:
                try:
                    origin_bindings["checkers"] = [
                        _validate_origin_record(
                            path, role="checker", validated=validated
                        )
                        for path in checker_origin_paths
                    ]
                except AuthorityError:
                    failure_class = "CHECKER_ORIGIN_BINDING"
                check_results = [
                    _validate_check_record(path, process)
                    for path, process in zip(check_paths, checker_records)
                ]
                check_dispositions = [result[0] for result in check_results]
                check_details = [result[1] for result in check_results]
        else:
            failure_class = failure_class or "PRODUCER_PROCESS"
    except BaseException as exc:
        failure_class = f"COORDINATOR_{type(exc).__name__.upper()}"

    proof_identical = proof_identical and len(producer_records) == 2
    producer_origin_identical = (
        producer_origin_identical and len(origin_bindings["producers"]) == 2
    )
    check_identical = len(checker_records) == 2 and _identical_regular_files(
        check_paths
    )
    checker_origin_identical = (
        len(origin_bindings["checkers"]) == 2
        and _identical_regular_files(checker_origin_paths)
    )
    if checker_records and failure_class is None:
        if "MALFORMED_EVIDENCE" in check_dispositions:
            failure_class = "CHECKER_EVIDENCE_MALFORMED"
        elif not check_identical:
            failure_class = "CHECKER_NONDETERMINISM"
        elif not checker_origin_identical:
            failure_class = "CHECKER_ORIGIN_NONDETERMINISM"
        elif len(set(check_dispositions)) != 1:
            failure_class = "CHECKER_DISAGREEMENT"
    complete_and_deterministic = (
        proof_identical
        and check_identical
        and producer_origin_identical
        and checker_origin_identical
        and len(check_dispositions) == 2
        and check_dispositions[0] == check_dispositions[1]
        and check_dispositions[0] != "MALFORMED_EVIDENCE"
        and failure_class is None
    )
    finding_groups = sorted(
        {
            group
            for detail in check_details
            if detail is not None
            for group in detail["finding_groups"]
        },
        key=(
            "VARIATIONAL_IDENTITY",
            "REFERENCE_LINEAR_ALGEBRA",
            "FINITE_STATIC",
        ).index,
    )
    if complete_and_deterministic and check_dispositions[0] == "SCIENTIFIC_FINDING":
        terminal = _finding_terminal(mode, finding_groups)
    elif complete_and_deterministic:
        terminal = (
            "PROVISIONAL_GO_GE_BEAM3_MIXED_STRAIGHT_STATIC_CORE"
            if mode == FORMAL_MODE
            else "NONCLASSIFYING_GE_BEAM3_MIXED_REHEARSAL_PASS"
        )

    cycle_bindings = [
        {
            "check": _output_binding(check_paths[index]),
            "checker_origin": _output_binding(checker_origin_paths[index]),
            "cycle": index + 1,
            "producer_origin": _output_binding(producer_origin_paths[index]),
            "proof": _output_binding(proof_paths[index]),
        }
        for index in range(2)
    ]
    process_records = {"checkers": checker_records, "producers": producer_records}
    aggregate_core = {
        "adjudication": {
            "checker_dispositions": check_dispositions,
            "finding_groups": finding_groups,
            "scientific_finding": (
                complete_and_deterministic
                and check_dispositions == ["SCIENTIFIC_FINDING", "SCIENTIFIC_FINDING"]
            ),
        },
        "authority": validated.binding,
        "candidate_id": CANDIDATE_ID,
        "cycles": cycle_bindings,
        "determinism": {
            "check_bytes_identical": check_identical,
            "checker_origin_bytes_identical": checker_origin_identical,
            "producer_origin_bytes_identical": producer_origin_identical,
            "proof_bytes_identical": proof_identical,
        },
        "execution_bounds": FROZEN_BOUNDS.authority_value(),
        "failure_class": failure_class,
        "materialization": {
            "manifest_sha256": materialization_sha256,
            "tree": validated.harness_tree,
        },
        "mode": mode,
        "processes": process_records,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": AGGREGATE_SCHEMA,
        "study_id": STUDY_ID,
        "terminal": terminal,
    }
    try:
        return _finalize_claimed_execution(
            aggregate_core=aggregate_core,
            claim=claim,
            output_path=output_path,
            validated=validated,
            work_root=work_root,
        )
    finally:
        _release_claim_lock(claim)


def _validate_rehearsal_aggregate(
    binding: Any,
    authority_path: Path,
    *,
    harness_commit: str,
    harness_tree: str,
) -> dict[str, Any]:
    payload, record, path = _validate_bound_file(
        binding, authority_path, label="preauthorization rehearsal aggregate"
    )
    if _is_within(path, ROOT):
        raise AuthorityError("preauthorization rehearsal aggregate must be external")
    expected_fields = {
        "adjudication",
        "authority",
        "candidate_id",
        "consumption",
        "cycles",
        "determinism",
        "execution_bounds",
        "failure_class",
        "materialization",
        "mode",
        "processes",
        "production_restriction",
        "schema",
        "study_id",
        "terminal",
    }
    if set(record) != expected_fields:
        raise AuthorityError("preauthorization rehearsal aggregate field set mismatch")
    if (
        record["schema"] != AGGREGATE_SCHEMA
        or record["study_id"] != STUDY_ID
        or record["candidate_id"] != CANDIDATE_ID
        or record["mode"] != REHEARSAL_MODE
        or record["terminal"] != "NONCLASSIFYING_GE_BEAM3_MIXED_REHEARSAL_PASS"
        or binding["terminal"] != record["terminal"]
        or record["failure_class"] is not None
        or record["execution_bounds"] != FROZEN_BOUNDS.authority_value()
        or record["production_restriction"]
        != "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    ):
        raise AuthorityError("preauthorization rehearsal did not pass cleanly")
    if record["adjudication"] != {
        "checker_dispositions": ["PASS", "PASS"],
        "finding_groups": [],
        "scientific_finding": False,
    }:
        raise AuthorityError("preauthorization rehearsal contains a finding")
    expected_determinism = {
        "check_bytes_identical": True,
        "checker_origin_bytes_identical": True,
        "producer_origin_bytes_identical": True,
        "proof_bytes_identical": True,
    }
    if record["determinism"] != expected_determinism:
        raise AuthorityError("preauthorization rehearsal is nondeterministic")
    def valid_output_binding(value: Any, *, allow_empty: bool = False) -> bool:
        return bool(
            isinstance(value, dict)
            and set(value) == {"bytes", "sha256"}
            and isinstance(value["bytes"], int)
            and value["bytes"] >= (0 if allow_empty else 1)
            and _is_hex(value["sha256"], 64)
        )

    cycles = record["cycles"]
    if (
        not isinstance(cycles, list)
        or len(cycles) != 2
        or [cycle.get("cycle") for cycle in cycles if isinstance(cycle, dict)] != [1, 2]
        or any(
            not isinstance(cycle, dict)
            or set(cycle)
            != {"check", "checker_origin", "cycle", "producer_origin", "proof"}
            or any(cycle[name] is None for name in ("check", "checker_origin", "producer_origin", "proof"))
            or any(
                not valid_output_binding(cycle[name])
                for name in ("check", "checker_origin", "producer_origin", "proof")
            )
            for cycle in cycles
        )
    ):
        raise AuthorityError("preauthorization rehearsal cycle evidence is incomplete")
    processes = record["processes"]
    if (
        not isinstance(processes, dict)
        or set(processes) != {"checkers", "producers"}
        or any(
            not isinstance(processes[role], list)
            or len(processes[role]) != 2
            or any(
                not isinstance(process, dict)
                or set(process)
                != {
                    "cycle",
                    "output",
                    "reason",
                    "returncode",
                    "role",
                    "stderr",
                    "stdout",
                    "tree_drained",
                }
                or process.get("reason") is not None
                or process.get("returncode") != 0
                or process.get("role") != role[:-1]
                or process.get("cycle") not in {1, 2}
                or process.get("tree_drained") is not True
                or not valid_output_binding(process.get("output"))
                or not valid_output_binding(process.get("stdout"), allow_empty=True)
                or not valid_output_binding(process.get("stderr"), allow_empty=True)
                for process in processes[role]
            )
            for role in ("checkers", "producers")
        )
    ):
        raise AuthorityError("preauthorization rehearsal process evidence is incomplete")
    for index in range(2):
        if (
            processes["producers"][index]["cycle"] != index + 1
            or processes["checkers"][index]["cycle"] != index + 1
            or processes["producers"][index]["output"] != cycles[index]["proof"]
            or processes["checkers"][index]["output"] != cycles[index]["check"]
        ):
            raise AuthorityError("preauthorization rehearsal process/cycle binding mismatch")
    authority = record["authority"]
    if (
        not isinstance(authority, dict)
        or set(authority)
        != {
            "authorization",
            "bytes",
            "harness",
            "mode",
            "preauthorization_records",
            "request",
            "review",
            "sha256",
            "terminal",
        }
        or authority.get("authorization") is not None
        or authority.get("mode") != REHEARSAL_MODE
        or authority.get("review") is not None
        or authority.get("preauthorization_records") is not None
        or authority.get("harness")
        != {"commit": harness_commit, "tree": harness_tree}
        or not isinstance(authority.get("bytes"), int)
        or authority["bytes"] <= 0
        or not _is_hex(authority.get("sha256"), 64)
        or not isinstance(authority.get("request"), dict)
        or set(authority["request"]) != {"attempt_id", "request_id"}
        or not all(_is_hex(value, 32) for value in authority["request"].values())
        or authority.get("terminal") != REHEARSAL_AUTHORITY_TERMINAL
    ):
        raise AuthorityError("preauthorization rehearsal authority provenance mismatch")
    consumption = record["consumption"]
    if (
        not isinstance(consumption, dict)
        or set(consumption) != {"claim", "receipt"}
        or not isinstance(consumption["claim"], dict)
        or set(consumption["claim"]) != {"bytes", "path", "sha256"}
        or not isinstance(consumption["receipt"], dict)
        or set(consumption["receipt"])
        != {"bytes", "path", "sha256", "terminal"}
        or consumption["receipt"].get("terminal") != record["terminal"]
    ):
        raise AuthorityError("preauthorization rehearsal consumption receipt mismatch")
    claim_path = Path(consumption["claim"]["path"])
    receipt_path = Path(consumption["receipt"]["path"])
    if (
        not claim_path.is_absolute()
        or not receipt_path.is_absolute()
        or _is_within(claim_path, ROOT)
        or _is_within(receipt_path, ROOT)
    ):
        raise AuthorityError("preauthorization consumption records are not external")
    claim_payload, claim_record = _read_canonical_record(
        claim_path, label="preauthorization one-time claim"
    )
    receipt_payload, receipt_record = _read_canonical_record(
        receipt_path, label="preauthorization terminal receipt"
    )
    if (
        consumption["claim"]
        != {
            "bytes": len(claim_payload),
            "path": str(claim_path.resolve()),
            "sha256": _sha256_bytes(claim_payload),
        }
        or consumption["receipt"]
        != {
            "bytes": len(receipt_payload),
            "path": str(receipt_path.resolve()),
            "sha256": _sha256_bytes(receipt_payload),
            "terminal": record["terminal"],
        }
    ):
        raise AuthorityError("preauthorization consumption byte binding mismatch")
    request = authority["request"]
    expected_claim = {
        "attempt_id": request["attempt_id"],
        "authority_sha256": authority["sha256"],
        "harness_commit": harness_commit,
        "request_id": request["request_id"],
        "schema": "anysolver.ge-beam3-mixed-one-time-claim-v1",
    }
    aggregate_core = {
        key: value for key, value in record.items() if key != "consumption"
    }
    expected_receipt = {
        "aggregate_core": aggregate_core,
        "attempt_id": request["attempt_id"],
        "claim": {
            "bytes": len(claim_payload),
            "sha256": _sha256_bytes(claim_payload),
        },
        "intended_output": str(path.resolve()),
        "request_id": request["request_id"],
        "schema": "anysolver.ge-beam3-mixed-one-time-receipt-v1",
        "work_root": receipt_record.get("work_root"),
    }
    if (
        claim_record != expected_claim
        or receipt_record != expected_receipt
        or not isinstance(receipt_record.get("work_root"), str)
        or not Path(receipt_record["work_root"]).is_absolute()
        or _is_within(Path(receipt_record["work_root"]), ROOT)
    ):
        raise AuthorityError("preauthorization terminal receipt contents mismatch")
    return {
        "bytes": len(payload),
        "path": str(path.resolve()),
        "request": authority.get("request"),
        "sha256": _sha256_bytes(payload),
        "terminal": record["terminal"],
    }


def _validate_preauthorization_records(
    value: Any,
    authority_path: Path,
    manifest: list[dict[str, str]],
    *,
    harness_commit: str,
    harness_tree: str,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "authority_checks",
        "rehearsal_aggregate",
    }:
        raise AuthorityError("preauthorization-record group field set mismatch")
    checks = value["authority_checks"]
    if not isinstance(checks, list) or len(checks) != 2:
        raise AuthorityError("exactly two preauthorization authority checks are required")
    normalized_checks = [
        _validate_authority_check(binding, authority_path, manifest)
        for binding in checks
    ]
    check_paths = [row["path"] for row in normalized_checks]
    if len(set(check_paths)) != 2:
        raise AuthorityError("preauthorization authority-check paths must be distinct")
    try:
        if os.path.samefile(check_paths[0], check_paths[1]):
            raise AuthorityError(
                "preauthorization authority checks must be distinct files"
            )
    except OSError as exc:
        raise AuthorityError("preauthorization authority-check identity failed") from exc
    if normalized_checks[0]["sha256"] != normalized_checks[1]["sha256"]:
        raise AuthorityError("preauthorization authority checks are not byte-identical")
    rehearsal = _validate_rehearsal_aggregate(
        value["rehearsal_aggregate"],
        authority_path,
        harness_commit=harness_commit,
        harness_tree=harness_tree,
    )
    return {"authority_checks": normalized_checks, "rehearsal_aggregate": rehearsal}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execution-authority", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--rehearsal", action="store_true")
    args = parser.parse_args()
    mode = REHEARSAL_MODE if args.rehearsal else FORMAL_MODE
    try:
        aggregate = run_bounded(
            authority_path=args.execution_authority,
            output_path=args.output,
            work_root=args.work_root,
            mode=mode,
        )
    except (AuthorityError, ExclusiveOutputError, OSError) as exc:
        print(f"ge-beam3 mixed execution blocked before completion: {exc}", file=sys.stderr)
        return 2
    if aggregate["terminal"] in {
        "PROVISIONAL_GO_GE_BEAM3_MIXED_STRAIGHT_STATIC_CORE",
        "NONCLASSIFYING_GE_BEAM3_MIXED_REHEARSAL_PASS",
    }:
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
