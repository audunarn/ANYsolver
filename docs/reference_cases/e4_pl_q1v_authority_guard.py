#!/usr/bin/env python3
"""Shared, mechanics-free commissioning and execution guard for E4-PL-Q1V.

This module intentionally uses only the Python standard library.  It may be
imported before authority exists, but the applicable commissioning or
execution validator must complete before a registered geometry is constructed,
an exact backend is activated, a solve is attempted, or pytest collection
starts.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import stat
import subprocess
from typing import Any, Iterable, Iterator, Mapping


CANDIDATE_ID = "candidate_e4_pl_q1v.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1"
STUDY_ID = "study_e4_pl_q1v.q1u_backend_repair_and_local_completion_v1"
AUTHORIZATION = "AUTHORIZE_E4_PL_Q1V_SCIENTIFIC_EXECUTION"
PRE_CERTIFICATE_REAUTHORIZATION = (
    "REAUTHORIZE_E4_PL_Q1V_FIRST_SUCCESSFULLY_WRITTEN_REOPENED_HASH_VERIFIED_"
    "COMPLETE_SCHEMA_VALID_EXCLUSIVELY_CREATED_CANONICAL_REGISTERED_CERTIFICATE"
)
HARD_FREEZE_EVENT = (
    "FIRST_SUCCESSFULLY_WRITTEN_REOPENED_HASH_VERIFIED_COMPLETE_SCHEMA_VALID_"
    "EXCLUSIVELY_CREATED_CANONICAL_REGISTERED_CERTIFICATE"
)
Q1U_CLOSEOUT = "7d4ac30b4d50a1ee62edefbe5fb0198b47276360"
COMMIT1 = "7a33044aee429557d770b914130df47105d6bec9"
COMMIT1_TREE = "7ae5c3278aed1e5937d90c308db6f570e424b1f7"
COMMIT1_SUBJECT = "docs: preregister E4 PL Q1V local completion"
COMMIT2_SUBJECT = "docs: freeze E4 PL Q1V commissioned exact implementations"
COMMIT3_SUBJECT = "docs: authorize E4 PL Q1V scientific execution"
AUTHORITY_SCHEMA = "anysolver.s4.e4-pl-q1v-execution-authority-v1"
CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1v-execution-contract-v1"
ENVIRONMENT_SCHEMA = "e4_pl_q1t_environment_record_v1"
AGREEMENT_MODE = "BYTE_IDENTICAL_CANONICAL_CERTIFICATE_PAYLOAD"
ENVIRONMENT_RECORD = "docs/reference_cases/e4_pl_q1t_environment.json"
ENVIRONMENT_SHA256 = "5461206324E7FC2A52B334CE736A512EE71313ED79181438047E3E20069A9746"

RUNNER_IDS = ["REFERENCE_RUNNER", "ORACLE_RUNNER", "SCIENTIFIC_TEST_RUNNER"]
INVOCATION_MODES = {"AUTHORITY_CHECK_ONLY", "EXECUTE"}
COMMISSIONING_RUNNER_IDS = {
    "REFERENCE_COMMISSIONING_RUNNER",
    "ORACLE_COMMISSIONING_RUNNER",
}
COMMISSIONING_MODE = "COMMISSION"
COMMISSIONING_CONTRACT = "docs/reference_cases/e4_pl_q1v_commissioning_contract.json"
COMMISSIONING_CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1v-commissioning-contract-v1"
COMMISSIONING_CONTRACT_SHA256 = (
    "E32D7A31D62F622C191E4B572922F290A743452C7CE2BCF9D408AA1F9AF551A7"
)

PLAN_PATHS = [
    "docs/agent_plans/S4_E4_PL_Q1V_LOCAL_COMPLETION_PLAN.md",
    "docs/reference_cases/e4_pl_q1v_plan_review.json",
    "docs/reference_cases/e4_pl_q1v_baseline.json",
    "docs/reference_cases/e4_pl_q1v_inheritance_manifest.json",
    "docs/reference_cases/e4_pl_q1v_allowed_extent.json",
    "docs/reference_cases/e4_pl_q1v_q1u_backend_incident.json",
    "docs/reference_cases/e4_pl_q1v_exact_backend_contract.json",
    "docs/reference_cases/e4_pl_q1v_commissioning_contract.json",
    "docs/reference_cases/e4_pl_q1v_mechanics_equivalence_contract.json",
    "docs/reference_cases/e4_pl_q1v_certificate_schema.json",
    "docs/reference_cases/e4_pl_q1v_authority_contract.json",
    "docs/reference_cases/e4_pl_q1v_terminal_table.json",
    "docs/reference_cases/e4_pl_q1v_test_inventory.json",
    "tests/test_e4_pl_q1v_preregistration_authority.py",
]
IMPLEMENTATION_PATHS = [
    "docs/reference_cases/e4_pl_q1v_authority_guard.py",
    "docs/reference_cases/e4_pl_q1v_reference.py",
    "docs/reference_cases/e4_pl_q1v_oracle.py",
    "docs/reference_cases/e4_pl_q1v_scientific_test_runner.py",
    "docs/reference_cases/e4_pl_q1v_commissioning_runner.py",
    "docs/reference_cases/e4_pl_q1v_implementation_manifest.json",
    "docs/reference_cases/e4_pl_q1v_mechanics_equivalence.json",
    "docs/reference_cases/e4_pl_q1v_backend_conformance.json",
    "docs/reference_cases/e4_pl_q1v_commissioning_reference.json",
    "docs/reference_cases/e4_pl_q1v_commissioning_oracle.json",
    "docs/reference_cases/e4_pl_q1v_commissioning_agreement.json",
    "docs/reference_cases/e4_pl_q1v_implementation_review.json",
    "tests/test_e4_pl_q1v_exact_backend.py",
    "tests/test_e4_pl_q1v_commissioning.py",
    "tests/test_e4_pl_q1v_authority_guard.py",
    "tests/test_e4_pl_q1v_frame_and_fields.py",
    "tests/test_e4_pl_q1v_local_algebra.py",
    "tests/test_e4_pl_q1v_recovery.py",
    "tests/test_e4_pl_q1v_global_supports.py",
    "tests/test_e4_pl_q1v_terminal_and_agreement.py",
]
CONTRACT_PATHS = [
    "docs/reference_cases/e4_pl_q1v_execution_contract.json",
    "docs/reference_cases/e4_pl_q1v_contract_review.json",
    "tests/test_e4_pl_q1v_contract.py",
]
OUTCOME_PATHS = [
    "docs/reference_cases/e4_pl_q1v_reference_raw.json",
    "docs/reference_cases/e4_pl_q1v_oracle_raw.json",
    "docs/reference_cases/e4_pl_q1v_agreement.json",
    "docs/reference_cases/e4_pl_q1v_output.json",
    "docs/reference_cases/e4_pl_q1v_status.json",
    "docs/reference_cases/e4_pl_q1v_execution_authority.json",
    "docs/reference_cases/e4_pl_q1v_scientific_test_result.json",
    "docs/E4_PL_Q1V_LOCAL_QUALIFICATION.md",
    "docs/reference_cases/e4_pl_q1v_scientific_review.json",
    "docs/E4_PL_Q1V_COMPLETION.md",
    "tests/test_e4_pl_q1v_closeout.py",
]
SCIENTIFIC_REQUIRED = OUTCOME_PATHS[:4] + [OUTCOME_PATHS[5]]
SCIENTIFIC_FORBIDDEN = [OUTCOME_PATHS[index] for index in (4, 6, 7, 8, 9, 10)]
SCIENTIFIC_NODE_IDS = [
    "tests/test_e4_pl_q1v_frame_and_fields.py::test_q1v_all_56_numbered_frames_and_field_work",
    "tests/test_e4_pl_q1v_local_algebra.py::test_q1v_actual_38_field_condensation_rank_and_rigid_modes",
    "tests/test_e4_pl_q1v_recovery.py::test_q1v_all_224_station_recovery_and_numerical_separation",
    "tests/test_e4_pl_q1v_global_supports.py::test_q1v_global_transform_load_support_solution_and_reactions",
    "tests/test_e4_pl_q1v_terminal_and_agreement.py::test_q1v_evidence_terminal_and_cross_implementation_contract",
]

AUTHORITY_KEYS = {
    "authorization",
    "authorization_cycle",
    "authorization_parent",
    "authorization_subject",
    "backend_conformance_sha256",
    "candidate_id",
    "commissioning_agreement_sha256",
    "commit",
    "contract_review_sha256",
    "correction_history",
    "correction_cycles_used",
    "environment_sha256",
    "execution_contract_sha256",
    "implementation_review_sha256",
    "latest_accepted_authorization",
    "plan_review_sha256",
    "pre_certificate_reauthorization",
    "review_verdicts",
    "runner_ids",
    "schema",
    "study_id",
    "tree",
}
CONTRACT_KEYS = {
    "agreement",
    "authorization",
    "candidate_id",
    "commit_ancestry",
    "environment",
    "implementation_inputs",
    "inherited_inputs",
    "output_absences",
    "plan_inputs",
    "production_restriction",
    "review_authorities",
    "runner_inventory",
    "runtime",
    "schema",
    "scientific_inventory",
    "study_id",
    "terminal_authority",
}
REVIEW_KEYS = {
    "findings",
    "reviewed_inputs",
    "reviewer_independence",
    "schema",
    "verdict",
}
REVIEW_EXPECTATIONS = {
    "plan": {
        "path": "docs/reference_cases/e4_pl_q1v_plan_review.json",
        "schema": "anysolver.s4.e4-pl-q1v-plan-review-v1",
        "verdict": "ACCEPT_Q1V_PREREGISTRATION_NO_P0_P1",
        "independence": {
            "mechanics_executed": False,
            "reviewer_role": "INDEPENDENT_PLAN_REVIEWER",
            "same_agent_as_packet_author": False,
        },
        "inputs": [path for path in PLAN_PATHS if not path.endswith("plan_review.json")],
    },
    "implementation": {
        "path": "docs/reference_cases/e4_pl_q1v_implementation_review.json",
        "schema": "anysolver.s4.e4-pl-q1v-implementation-review-v1",
        "verdict": "ACCEPT_Q1V_IMPLEMENTATION_FREEZE_NO_P0_P1",
        "independence": {
            "authored_review_only": True,
            "mechanics_executed": False,
            "reviewed_input_authorship": False,
            "role": "INDEPENDENT_STATIC_IMPLEMENTATION_REVIEWER",
        },
        "inputs": [path for path in IMPLEMENTATION_PATHS if not path.endswith("implementation_review.json")],
    },
    "contract": {
        "path": "docs/reference_cases/e4_pl_q1v_contract_review.json",
        "schema": "anysolver.s4.e4-pl-q1v-contract-review-v1",
        "verdict": "ACCEPT_Q1V_EXECUTION_CONTRACT_NO_P0_P1",
        "independence": {
            "authored_review_only": True,
            "mechanics_executed": False,
            "reviewed_input_authorship": False,
            "role": "INDEPENDENT_EXECUTION_CONTRACT_REVIEWER",
        },
        "inputs": [CONTRACT_PATHS[0], CONTRACT_PATHS[2]],
    },
}


class AuthorityGuardError(RuntimeError):
    """Raised before scientific reachability when authority is invalid."""


@dataclass(frozen=True)
class GuardEvidence:
    authority: Mapping[str, Any]
    contract: Mapping[str, Any]
    environment: Mapping[str, Any]
    head: str
    tree: str
    runner_id: str


@dataclass(frozen=True)
class CommissioningGuardEvidence:
    """Inert authority returned before a commissioning backend is imported."""

    contract: Mapping[str, Any]
    environment: Mapping[str, Any]
    head: str
    tree: str
    runner_id: str
    output_path: Path


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def strict_json_bytes(raw: bytes) -> Any:
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw:
        raise AuthorityGuardError("JSON must be UTF-8 without BOM and LF-only")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_pairs,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise AuthorityGuardError(f"strict JSON rejection: {exc}") from exc
    if raw != canonical_bytes(value):
        raise AuthorityGuardError("JSON is not canonical UTF-8/LF transport")
    return value


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _require_keys(value: Any, expected: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != expected:
        raise AuthorityGuardError(f"{label} keys differ from frozen schema")
    return value


def _is_link(path: Path) -> bool:
    try:
        attributes = path.lstat().st_file_attributes
    except (AttributeError, OSError):
        attributes = 0
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return path.is_symlink() or bool(attributes & reparse)


def _load_canonical(path: Path, expected_sha256: str, label: str) -> tuple[Mapping[str, Any], bytes]:
    if _is_link(path) or not path.is_file():
        raise AuthorityGuardError(f"{label} must be a regular nonsymlink file")
    raw = path.read_bytes()
    if sha256_bytes(raw) != expected_sha256.upper():
        raise AuthorityGuardError(f"caller-supplied {label} SHA-256 mismatch")
    value = strict_json_bytes(raw)
    if not isinstance(value, Mapping):
        raise AuthorityGuardError(f"{label} must be a JSON object")
    return value, raw


def _run_git(root: Path, *args: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", "-c", "core.excludesFile=/dev/null", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if check and completed.returncode:
        raise AuthorityGuardError(f"Git authority command failed: {' '.join(args)}")
    return completed.stdout.strip()


def _git_object_exists(root: Path, specification: str) -> bool:
    return (
        subprocess.run(
            ["git", "-c", "core.excludesFile=/dev/null", "cat-file", "-e", specification],
            cwd=root,
            check=False,
            capture_output=True,
        ).returncode
        == 0
    )


def _safe_relative_path(value: Any) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise AuthorityGuardError("bound path is not canonical POSIX relative text")
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise AuthorityGuardError("bound path escapes or is not normalized")
    return pure.as_posix()


def _within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _worktree_roots(root: Path) -> list[Path]:
    roots: list[Path] = []
    for line in _run_git(root, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            roots.append(Path(line[9:]).resolve(strict=True))
    if not roots:
        raise AuthorityGuardError("Git returned no worktree roots")
    return roots


def _require_external(path: Path, worktrees: Iterable[Path], label: str, *, directory: bool) -> Path:
    if not path.is_absolute() or _is_link(path):
        raise AuthorityGuardError(f"{label} must be an absolute nonsymlink path")
    resolved = path.resolve(strict=True)
    if any(_within(resolved, worktree) for worktree in worktrees):
        raise AuthorityGuardError(f"{label} must be outside every Git worktree")
    if directory and not resolved.is_dir():
        raise AuthorityGuardError(f"{label} must be a directory")
    if not directory and not resolved.is_file():
        raise AuthorityGuardError(f"{label} must be a regular file")
    return resolved


def _bound_file(root: Path, row: Mapping[str, Any], *, exact_keys: set[str] | None = None) -> Path:
    if exact_keys is not None:
        _require_keys(row, exact_keys, "bound file row")
    if not {"path", "bytes", "sha256"}.issubset(row):
        raise AuthorityGuardError("bound file row lacks path/bytes/sha256")
    relative = _safe_relative_path(row["path"])
    path = root / relative
    if _is_link(path) or not path.is_file():
        raise AuthorityGuardError(f"bound file is absent, nonregular, or linked: {relative}")
    resolved = path.resolve(strict=True)
    if not _within(resolved, root):
        raise AuthorityGuardError(f"bound file escapes repository: {relative}")
    raw = resolved.read_bytes()
    if type(row["bytes"]) is not int or row["bytes"] != len(raw):
        raise AuthorityGuardError(f"bound byte count drift: {relative}")
    if not isinstance(row["sha256"], str) or row["sha256"] != sha256_bytes(raw):
        raise AuthorityGuardError(f"bound SHA-256 drift: {relative}")
    return resolved


def _row_for(root: Path, relative: str) -> dict[str, Any]:
    raw = (root / relative).read_bytes()
    return {"bytes": len(raw), "path": relative, "sha256": sha256_bytes(raw)}


def _changed_paths(root: Path, commit: str) -> list[str]:
    text = _run_git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit)
    return sorted(line.replace("\\", "/") for line in text.splitlines() if line)


def _verify_commit(
    root: Path,
    row: Any,
    *,
    expected_commit: str | None,
    expected_parent: str,
    expected_subject: str,
    expected_paths: list[str],
    label: str,
) -> str:
    row = _require_keys(row, {"commit", "tree", "parent", "subject", "path_count", "paths"}, label)
    commit = row["commit"]
    if not isinstance(commit, str) or len(commit) != 40:
        raise AuthorityGuardError(f"{label} commit identity is invalid")
    if expected_commit is not None and commit != expected_commit:
        raise AuthorityGuardError(f"{label} commit differs from frozen identity")
    if row["parent"] != expected_parent or row["subject"] != expected_subject:
        raise AuthorityGuardError(f"{label} parent or subject drift")
    if row["path_count"] != len(expected_paths) or row["paths"] != expected_paths:
        raise AuthorityGuardError(f"{label} path declaration drift")
    if _run_git(root, "rev-list", "--parents", "-n", "1", commit).split() != [commit, expected_parent]:
        raise AuthorityGuardError(f"{label} must have exactly the frozen parent")
    if _run_git(root, "rev-parse", f"{commit}^{{tree}}") != row["tree"]:
        raise AuthorityGuardError(f"{label} tree drift")
    if _run_git(root, "show", "-s", "--format=%s", commit) != expected_subject:
        raise AuthorityGuardError(f"{label} Git subject drift")
    if _changed_paths(root, commit) != sorted(expected_paths):
        raise AuthorityGuardError(f"{label} exact path extent drift")
    return commit


def _iter_bound_rows(value: Any) -> Iterator[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        if {"path", "bytes", "sha256"}.issubset(value):
            yield value
        for nested in value.values():
            yield from _iter_bound_rows(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_bound_rows(nested)


def _verify_plan_inputs(root: Path, value: Any) -> None:
    value = _require_keys(value, {"count", "rows"}, "plan inputs")
    rows = value["rows"]
    if value["count"] != len(PLAN_PATHS) or not isinstance(rows, list):
        raise AuthorityGuardError("plan input count drift")
    if [row.get("path") if isinstance(row, Mapping) else None for row in rows] != PLAN_PATHS:
        raise AuthorityGuardError("plan input order or extent drift")
    for row in rows:
        _bound_file(root, _require_keys(row, {"path", "bytes", "sha256"}, "plan input row"))


def _verify_implementation_inputs(root: Path, value: Any) -> None:
    expected_keys = {
        "authority_guard",
        "reference",
        "oracle",
        "scientific_runner",
        "commissioning_runner",
        "manifest",
        "mechanics_equivalence",
        "backend_conformance",
        "commissioning_reference",
        "commissioning_oracle",
        "commissioning_agreement",
        "implementation_review",
        "exact_backend_test",
        "commissioning_test",
        "authority_guard_test",
        "scientific_tests",
    }
    value = _require_keys(value, expected_keys, "implementation inputs")
    row_keys = {
        "authority_guard": {"path", "bytes", "sha256", "entrypoint"},
        "reference": {"path", "bytes", "sha256", "implementation_id"},
        "oracle": {"path", "bytes", "sha256", "implementation_id"},
        "scientific_runner": {"path", "bytes", "sha256", "runner_id"},
        "commissioning_runner": {"path", "bytes", "sha256", "runner_ids"},
        "manifest": {"path", "bytes", "sha256", "schema"},
        "mechanics_equivalence": {"path", "bytes", "sha256", "schema"},
        "backend_conformance": {"path", "bytes", "sha256", "schema", "verdict"},
        "commissioning_reference": {
            "path", "bytes", "sha256", "schema", "implementation_id",
            "record_kind", "determinism_payload_sha256",
        },
        "commissioning_oracle": {
            "path", "bytes", "sha256", "schema", "implementation_id",
            "record_kind", "determinism_payload_sha256",
        },
        "commissioning_agreement": {
            "path", "bytes", "sha256", "schema", "record_kind",
            "reference_sha256", "oracle_sha256",
        },
        "implementation_review": {"path", "bytes", "sha256", "schema", "verdict"},
        "exact_backend_test": {"path", "bytes", "sha256", "node_ids"},
        "commissioning_test": {"path", "bytes", "sha256", "node_ids"},
        "authority_guard_test": {"path", "bytes", "sha256", "node_ids"},
    }
    for key, keys in row_keys.items():
        _bound_file(root, _require_keys(value[key], keys, key), exact_keys=keys)
    tests = value["scientific_tests"]
    if not isinstance(tests, list) or len(tests) != 5:
        raise AuthorityGuardError("scientific-test input list must contain five rows")
    for row in tests:
        _bound_file(root, _require_keys(row, {"path", "bytes", "sha256", "node_ids"}, "scientific test"))
    rows = list(_iter_bound_rows(value))
    if sorted(str(row["path"]) for row in rows) != sorted(IMPLEMENTATION_PATHS):
        raise AuthorityGuardError("implementation inputs do not cover exact IMPLEMENTATION20")
    if value["authority_guard"]["entrypoint"] != "validate_execution_authority":
        raise AuthorityGuardError("shared guard entrypoint drift")
    if value["reference"]["implementation_id"] != "Q1V_REFERENCE_STDLIB_FIELD_ALG":
        raise AuthorityGuardError("reference implementation identity drift")
    if value["oracle"]["implementation_id"] != "Q1V_ORACLE_SYMPY_ALGEBRAIC_FIELD":
        raise AuthorityGuardError("oracle implementation identity drift")
    if value["scientific_runner"]["runner_id"] != "SCIENTIFIC_TEST_RUNNER":
        raise AuthorityGuardError("scientific runner identity drift")
    if value["commissioning_runner"]["runner_ids"] != sorted(COMMISSIONING_RUNNER_IDS):
        raise AuthorityGuardError("commissioning runner identities drift")
    backend = value["backend_conformance"]
    if (
        backend["path"] != "docs/reference_cases/e4_pl_q1v_backend_conformance.json"
        or backend["schema"] != "anysolver.s4.e4-pl-q1v-backend-conformance-v1"
        or backend["verdict"] != "ACCEPT_Q1V_EXACT_BACKEND_CONFORMANCE"
    ):
        raise AuthorityGuardError("backend-conformance authority drift")
    commissioning_profiles = {
        "commissioning_reference": (
            "docs/reference_cases/e4_pl_q1v_commissioning_reference.json",
            "anysolver.s4.e4-pl-q1v-reference-commissioning-v1",
            "Q1V_REFERENCE_STDLIB_FIELD_ALG",
        ),
        "commissioning_oracle": (
            "docs/reference_cases/e4_pl_q1v_commissioning_oracle.json",
            "anysolver.s4.e4-pl-q1v-oracle-commissioning-v1",
            "Q1V_ORACLE_SYMPY_ALGEBRAIC_FIELD",
        ),
    }
    for key, (path, schema, implementation_id) in commissioning_profiles.items():
        row = value[key]
        if (
            row["path"] != path
            or row["schema"] != schema
            or row["implementation_id"] != implementation_id
            or row["record_kind"] != "NONCLASSIFYING_IMPLEMENTATION_COMMISSIONING"
            or not isinstance(row["determinism_payload_sha256"], str)
            or len(row["determinism_payload_sha256"]) != 64
        ):
            raise AuthorityGuardError(f"{key} authority drift")
        record = strict_json_bytes((root / path).read_bytes())
        if not isinstance(record, Mapping) or record.get("determinism_payload_sha256") != row["determinism_payload_sha256"]:
            raise AuthorityGuardError(f"{key} construction digest drift")
    agreement_row = value["commissioning_agreement"]
    if (
        agreement_row["path"] != "docs/reference_cases/e4_pl_q1v_commissioning_agreement.json"
        or agreement_row["schema"] != "anysolver.s4.e4-pl-q1v-commissioning-agreement-v1"
        or agreement_row["record_kind"] != "NONCLASSIFYING_IMPLEMENTATION_COMMISSIONING"
        or agreement_row["reference_sha256"] != value["commissioning_reference"]["sha256"]
        or agreement_row["oracle_sha256"] != value["commissioning_oracle"]["sha256"]
    ):
        raise AuthorityGuardError("commissioning-agreement authority drift")
    expected_nodes = {path.split("::", 1)[0]: path for path in SCIENTIFIC_NODE_IDS}
    for row in tests:
        if row["node_ids"] != [expected_nodes.get(row["path"])]:
            raise AuthorityGuardError("scientific-test node binding drift")


def _verify_inherited_inputs(root: Path, value: Any) -> None:
    value = _require_keys(value, {"count", "rows"}, "inherited inputs")
    manifest_path = root / "docs/reference_cases/e4_pl_q1v_inheritance_manifest.json"
    manifest = strict_json_bytes(manifest_path.read_bytes())
    _require_keys(
        manifest,
        {"candidate_id", "classifications", "counts", "git_object_format", "input_groups", "inputs", "q1u_authority", "rule", "schema", "study_id"},
        "inheritance manifest",
    )
    rows = value["rows"]
    if value["count"] != 117 or rows != manifest["inputs"] or not isinstance(rows, list):
        raise AuthorityGuardError("contract must bind exact 117-row inheritance manifest")
    seen: set[str] = set()
    for row in rows:
        row = _require_keys(
            row,
            {"bytes", "classification", "git_blob", "path", "sha256", "source_commit", "source_tree"},
            "inherited row",
        )
        relative = _safe_relative_path(row["path"])
        if relative in seen:
            raise AuthorityGuardError("duplicate inherited path")
        seen.add(relative)
        _bound_file(root, row)
        if _run_git(root, "rev-parse", f"{row['source_commit']}^{{tree}}") != row["source_tree"]:
            raise AuthorityGuardError(f"inherited source-tree drift: {relative}")
        if _run_git(root, "rev-parse", f"{row['source_commit']}:{relative}") != row["git_blob"]:
            raise AuthorityGuardError(f"inherited blob drift: {relative}")


def _expected_review_inputs(root: Path, paths: list[str]) -> list[dict[str, Any]]:
    return sorted((_row_for(root, path) for path in paths), key=lambda row: row["path"])


def _verify_review(
    root: Path,
    stage: str,
    authority_row: Any,
    caller_sha256: str,
) -> Mapping[str, Any]:
    expected = REVIEW_EXPECTATIONS[stage]
    bound = stage != "contract"
    keys = {"path", "schema", "verdict"} | ({"bytes", "sha256"} if bound else {"hash_binding"})
    row = _require_keys(authority_row, keys, f"{stage} review authority")
    if row["path"] != expected["path"] or row["schema"] != expected["schema"] or row["verdict"] != expected["verdict"]:
        raise AuthorityGuardError(f"{stage} review authority drift")
    if bound:
        path = _bound_file(root, row)
        if row["sha256"] != caller_sha256:
            raise AuthorityGuardError(f"authority does not bind {stage} review hash")
    else:
        if row["hash_binding"] != "EXTERNAL_AUTHORITY_RECORD":
            raise AuthorityGuardError("contract review must be externally hash-bound")
        path = root / str(row["path"])
        if _is_link(path) or not path.is_file() or sha256_bytes(path.read_bytes()) != caller_sha256:
            raise AuthorityGuardError("contract review hash differs from external authority")
    review = strict_json_bytes(path.read_bytes())
    review = _require_keys(review, REVIEW_KEYS, f"{stage} review")
    if review["schema"] != expected["schema"] or review["verdict"] != expected["verdict"]:
        raise AuthorityGuardError(f"{stage} review identity drift")
    if review["findings"] != []:
        raise AuthorityGuardError(f"accepted {stage} review must have empty findings")
    if review["reviewer_independence"] != expected["independence"]:
        raise AuthorityGuardError(f"{stage} reviewer independence drift")
    if review["reviewed_inputs"] != _expected_review_inputs(root, expected["inputs"]):
        raise AuthorityGuardError(f"{stage} exact reviewed-input list drift")
    return review


def _verify_environment_graph(environment_root: Path, record: Mapping[str, Any]) -> None:
    if record.get("schema") != ENVIRONMENT_SCHEMA or record.get("candidate_id") != "candidate_e4_pl_q1t.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1":
        raise AuthorityGuardError("reused Q1T environment-record identity drift")
    expected = record.get("extracted_file_hash_graph")
    if not isinstance(expected, list) or len(expected) != 1662:
        raise AuthorityGuardError("environment record must bind 1662 extracted files")
    actual: list[dict[str, Any]] = []
    for directory, directory_names, file_names in os.walk(environment_root, topdown=True, followlinks=False):
        current = Path(directory)
        if _is_link(current):
            raise AuthorityGuardError("linked directory in exact environment")
        for name in directory_names:
            if _is_link(current / name):
                raise AuthorityGuardError("linked directory in exact environment")
        for name in file_names:
            path = current / name
            if _is_link(path):
                raise AuthorityGuardError("linked file in exact environment")
            mode = path.stat(follow_symlinks=False).st_mode
            if not stat.S_ISREG(mode):
                raise AuthorityGuardError("nonregular file in exact environment")
            raw = path.read_bytes()
            actual.append(
                {
                    "bytes": len(raw),
                    "path": path.relative_to(environment_root).as_posix(),
                    "sha256": hashlib.sha256(raw).hexdigest().lower(),
                }
            )
    actual.sort(key=lambda row: row["path"])
    if actual != expected:
        raise AuthorityGuardError("external exact-environment file graph drift")


def _working_tree_paths(root: Path) -> list[str]:
    text = _run_git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = [entry for entry in text.split("\0") if entry]
    paths: list[str] = []
    for entry in entries:
        if len(entry) < 4 or entry[2] != " ":
            raise AuthorityGuardError("unsupported Git status record")
        if entry[:2] in {"R ", " R", "C ", " C"}:
            raise AuthorityGuardError("rename/copy status is forbidden during commissioning")
        paths.append(_safe_relative_path(entry[3:].replace("\\", "/")))
    if len(paths) != len(set(paths)):
        raise AuthorityGuardError("duplicate working-tree path")
    return sorted(paths)


def _revision_paths_are_authorized(paths: list[str]) -> bool:
    mandatory = {
        "docs/reference_cases/e4_pl_q1v_implementation_manifest.json",
        "docs/reference_cases/e4_pl_q1v_mechanics_equivalence.json",
        "docs/reference_cases/e4_pl_q1v_backend_conformance.json",
        "docs/reference_cases/e4_pl_q1v_commissioning_reference.json",
        "docs/reference_cases/e4_pl_q1v_commissioning_oracle.json",
        "docs/reference_cases/e4_pl_q1v_commissioning_agreement.json",
        "docs/reference_cases/e4_pl_q1v_implementation_review.json",
    }
    affected = {
        "docs/reference_cases/e4_pl_q1v_authority_guard.py",
        "docs/reference_cases/e4_pl_q1v_reference.py",
        "docs/reference_cases/e4_pl_q1v_oracle.py",
        "docs/reference_cases/e4_pl_q1v_scientific_test_runner.py",
        "docs/reference_cases/e4_pl_q1v_commissioning_runner.py",
        "tests/test_e4_pl_q1v_exact_backend.py",
        "tests/test_e4_pl_q1v_commissioning.py",
        "tests/test_e4_pl_q1v_authority_guard.py",
    }
    observed = set(paths)
    return mandatory.issubset(observed) and observed.issubset(mandatory | affected)


def _authorization_cycle_from_commit(root: Path, commit: str) -> int:
    """Return the accepted authorization cycle, validating its exact DAG."""
    subject = _run_git(root, "show", "-s", "--format=%s", commit)
    parents = _run_git(root, "rev-list", "--parents", "-n", "1", commit).split()
    if len(parents) != 2 or parents[0] != commit:
        raise AuthorityGuardError("authorization commit must have one parent")
    if _changed_paths(root, commit) != sorted(CONTRACT_PATHS):
        raise AuthorityGuardError("authorization commit must have exact CONTRACT3 extent")
    parent = parents[1]
    if subject == COMMIT3_SUBJECT:
        if _run_git(root, "show", "-s", "--format=%s", parent) != COMMIT2_SUBJECT:
            raise AuthorityGuardError("cycle-zero authorization parent is not Commit 2")
        if _run_git(root, "rev-list", "--parents", "-n", "1", parent).split() != [parent, COMMIT1]:
            raise AuthorityGuardError("Commit 2 does not descend directly from Commit 1")
        if _changed_paths(root, parent) != sorted(IMPLEMENTATION_PATHS):
            raise AuthorityGuardError("Commit 2 exact IMPLEMENTATION20 extent drift")
        return 0
    prefix = "docs: reauthorize E4 PL Q1V scientific execution cycle "
    if not subject.startswith(prefix) or subject[len(prefix):] not in {"1", "2"}:
        raise AuthorityGuardError("authorization subject is not registered")
    cycle = int(subject[len(prefix):])
    revision_subject = _run_git(root, "show", "-s", "--format=%s", parent)
    if revision_subject != f"docs: revise E4 PL Q1V implementations before certificate cycle {cycle}":
        raise AuthorityGuardError("revision subject/cycle drift")
    revision_parents = _run_git(root, "rev-list", "--parents", "-n", "1", parent).split()
    if len(revision_parents) != 2 or revision_parents[0] != parent:
        raise AuthorityGuardError("revision commit must have one parent")
    if not _revision_paths_are_authorized(_changed_paths(root, parent)):
        raise AuthorityGuardError("revision extent exceeds the frozen correction policy")
    previous = revision_parents[1]
    previous_cycle = _authorization_cycle_from_commit(root, previous)
    if previous_cycle != cycle - 1:
        raise AuthorityGuardError("authorization cycles are not strictly monotonic")
    return cycle


def _authorization_history_from_commit(
    root: Path,
    commit: str,
) -> tuple[int, list[dict[str, Any]]]:
    """Return cycle and Git-derived correction rows in ascending order."""
    cycle = _authorization_cycle_from_commit(root, commit)
    if cycle == 0:
        return 0, []
    revision = _run_git(root, "rev-list", "--parents", "-n", "1", commit).split()[1]
    previous = _run_git(root, "rev-list", "--parents", "-n", "1", revision).split()[1]
    previous_cycle, rows = _authorization_history_from_commit(root, previous)
    if previous_cycle != cycle - 1:
        raise AuthorityGuardError("correction history has a cycle gap")
    rows.append(
        {
            "authorization_commit": commit,
            "authorization_subject": _run_git(root, "show", "-s", "--format=%s", commit),
            "authorization_tree": _run_git(root, "rev-parse", f"{commit}^{{tree}}"),
            "cycle": cycle,
            "revision_changed_paths": _changed_paths(root, revision),
            "revision_commit": revision,
            "revision_subject": _run_git(root, "show", "-s", "--format=%s", revision),
            "revision_tree": _run_git(root, "rev-parse", f"{revision}^{{tree}}"),
        }
    )
    return cycle, rows


def _cycle_zero_authorization(root: Path, commit: str) -> str:
    cycle = _authorization_cycle_from_commit(root, commit)
    current = commit
    while cycle:
        revision = _run_git(root, "rev-list", "--parents", "-n", "1", current).split()[1]
        current = _run_git(root, "rev-list", "--parents", "-n", "1", revision).split()[1]
        cycle -= 1
    return current


def _contains_exact_value(value: Any, expected: Any) -> bool:
    if value == expected:
        return True
    if isinstance(value, Mapping):
        return any(_contains_exact_value(nested, expected) for nested in value.values())
    if isinstance(value, list):
        return any(_contains_exact_value(nested, expected) for nested in value)
    return False


def _verify_correction_history(
    root: Path,
    authority: Mapping[str, Any],
    head: str,
) -> int:
    cycle, derived = _authorization_history_from_commit(root, head)
    history = authority["correction_history"]
    if type(authority["authorization_cycle"]) is not int or authority["authorization_cycle"] != cycle:
        raise AuthorityGuardError("authorization cycle drift")
    if type(authority["correction_cycles_used"]) is not int or authority["correction_cycles_used"] != cycle:
        raise AuthorityGuardError("correction-cycle usage drift")
    if not isinstance(history, list) or len(history) != cycle:
        raise AuthorityGuardError("correction-history length drift")
    manifest_path = root / "docs/reference_cases/e4_pl_q1v_implementation_manifest.json"
    manifest = strict_json_bytes(manifest_path.read_bytes())
    for expected, observed in zip(derived, history, strict=True):
        observed = _require_keys(
            observed,
            {
                "authorization_commit",
                "authorization_subject",
                "authorization_tree",
                "cycle",
                "incident_sha256",
                "revision_changed_paths",
                "revision_commit",
                "revision_subject",
                "revision_tree",
            },
            "correction-history row",
        )
        for key, value in expected.items():
            if observed[key] != value:
                raise AuthorityGuardError(f"correction-history Git binding drift: {key}")
        digest = observed["incident_sha256"]
        if (
            not isinstance(digest, str)
            or not re.fullmatch(r"[0-9A-F]{64}", digest)
            or not _contains_exact_value(manifest, digest)
        ):
            raise AuthorityGuardError("revision incident digest is not bound by the manifest")
    return cycle


def _require_external_output(
    path: Path,
    worktrees: Iterable[Path],
    label: str,
) -> Path:
    if not path.is_absolute() or path.exists() or path.is_symlink():
        raise AuthorityGuardError(f"{label} must be an absent absolute path")
    parent = path.parent.resolve(strict=True)
    if _is_link(path.parent) or not parent.is_dir():
        raise AuthorityGuardError(f"{label} parent must be a nonsymlink directory")
    resolved = parent / path.name
    if any(_within(resolved, worktree) for worktree in worktrees):
        raise AuthorityGuardError(f"{label} must be outside every Git worktree")
    return resolved


def _verify_commissioning_contract(contract: Mapping[str, Any]) -> None:
    exact_keys = {
        "allowed_common_fields",
        "candidate_id",
        "coverage",
        "forbidden_content",
        "forbidden_content_scan",
        "fresh_process_runs",
        "implementation_outputs",
        "record_kind",
        "recursive_forbidden_content_scan",
        "required_constructions",
        "result_schema",
        "runner",
        "schema",
        "study_id",
        "success_requires",
    }
    _require_keys(contract, exact_keys, "commissioning contract")
    if (
        contract["schema"] != COMMISSIONING_CONTRACT_SCHEMA
        or contract["candidate_id"] != CANDIDATE_ID
        or contract["study_id"] != STUDY_ID
        or contract["record_kind"] != "NONCLASSIFYING_IMPLEMENTATION_COMMISSIONING"
        or contract["runner"] != "docs/reference_cases/e4_pl_q1v_commissioning_runner.py"
        or contract["recursive_forbidden_content_scan"] is not True
    ):
        raise AuthorityGuardError("commissioning contract identity drift")
    forbidden = contract["forbidden_content"]
    if not isinstance(forbidden, list) or forbidden != [
        "CLASSIFICATION",
        "COVARIANCE_PASS_FAIL",
        "ENERGY",
        "GENERIC_PASS_FAIL",
        "NULLITY",
        "PATCH_PASS_FAIL",
        "PROPOSED_TERMINAL",
        "RANK",
        "RECOVERY_PASS_FAIL",
        "SCIENTIFIC_CLASSIFICATION",
        "SCIENTIFIC_PAYLOAD",
        "STIFFNESS_SIGN",
        "TERMINAL_INPUTS",
    ]:
        raise AuthorityGuardError("commissioning forbidden-content vocabulary drift")
    result_schema = _require_keys(
        contract["result_schema"],
        {
            "agreement_exact_keys",
            "implementation_exact_keys",
            "per_case_exact_keys",
            "record_kind",
        },
        "commissioning result schema",
    )
    if result_schema["record_kind"] != "NONCLASSIFYING_IMPLEMENTATION_COMMISSIONING":
        raise AuthorityGuardError("commissioning result kind drift")


def validate_commissioning_authority(
    *,
    repository_root: Path,
    runner_id: str,
    commissioning_contract_path: Path,
    commissioning_contract_sha256: str,
    environment_root: Path,
    environment_record_path: Path,
    environment_sha256: str,
    output_path: Path,
) -> CommissioningGuardEvidence:
    """Fail closed before backend activation or registered construction."""
    try:
        root = repository_root.resolve(strict=True)
        if not root.is_dir() or _is_link(root):
            raise AuthorityGuardError("repository root must be a nonsymlink directory")
        git_root = Path(_run_git(root, "rev-parse", "--show-toplevel")).resolve(strict=True)
        if os.path.normcase(os.path.normpath(git_root)) != os.path.normcase(os.path.normpath(root)):
            raise AuthorityGuardError("caller repository root differs from Git top level")
        if runner_id not in COMMISSIONING_RUNNER_IDS:
            raise AuthorityGuardError("commissioning runner id is not registered")
        worktrees = _worktree_roots(root)
        expected_contract = (root / COMMISSIONING_CONTRACT).resolve(strict=True)
        expected_environment = (root / ENVIRONMENT_RECORD).resolve(strict=True)
        if _is_link(commissioning_contract_path) or commissioning_contract_path.resolve(strict=True) != expected_contract:
            raise AuthorityGuardError("commissioning contract path is not the committed Q1V path")
        if _is_link(environment_record_path) or environment_record_path.resolve(strict=True) != expected_environment:
            raise AuthorityGuardError("environment record path is not the frozen Q1T path")
        external_environment = _require_external(
            environment_root, worktrees, "environment root", directory=True
        )
        external_output = _require_external_output(output_path, worktrees, "commissioning output")
        contract, contract_raw = _load_canonical(
            expected_contract, commissioning_contract_sha256, "commissioning contract"
        )
        if sha256_bytes(contract_raw) != COMMISSIONING_CONTRACT_SHA256:
            raise AuthorityGuardError("frozen commissioning-contract identity drift")
        _verify_commissioning_contract(contract)
        environment, environment_raw = _load_canonical(
            expected_environment, environment_sha256, "environment record"
        )
        if environment_sha256.upper() != ENVIRONMENT_SHA256 or sha256_bytes(environment_raw) != ENVIRONMENT_SHA256:
            raise AuthorityGuardError("frozen environment-record identity drift")

        head = _run_git(root, "rev-parse", "HEAD")
        tree = _run_git(root, "rev-parse", "HEAD^{tree}")
        if head == COMMIT1:
            if tree != COMMIT1_TREE:
                raise AuthorityGuardError("Commit 1 tree drift")
            allowed_dirty = set(IMPLEMENTATION_PATHS)
        else:
            cycle = _authorization_cycle_from_commit(root, head)
            if cycle >= 2:
                raise AuthorityGuardError("global implementation-correction budget is exhausted")
            allowed_dirty = set(IMPLEMENTATION_PATHS)
        dirty = _working_tree_paths(root)
        if not set(dirty).issubset(allowed_dirty):
            raise AuthorityGuardError("commissioning worktree changes exceed IMPLEMENTATION20")
        program = {
            "REFERENCE_COMMISSIONING_RUNNER": "docs/reference_cases/e4_pl_q1v_reference.py",
            "ORACLE_COMMISSIONING_RUNNER": "docs/reference_cases/e4_pl_q1v_oracle.py",
        }[runner_id]
        if program not in dirty and not _git_object_exists(root, f"HEAD:{program}"):
            raise AuthorityGuardError("commissioned implementation path is absent")
        for relative in OUTCOME_PATHS:
            if (root / relative).exists() or (root / relative).is_symlink() or _git_object_exists(root, f"HEAD:{relative}"):
                raise AuthorityGuardError(
                    f"hard-freeze/output path exists before commissioning: {relative}"
                )
        _verify_environment_graph(external_environment, environment)
        if platform.python_implementation() != "CPython" or platform.python_version() != "3.13.9":
            raise AuthorityGuardError("active CPython runtime drift")
        return CommissioningGuardEvidence(
            contract=contract,
            environment=environment,
            head=head,
            tree=tree,
            runner_id=runner_id,
            output_path=external_output,
        )
    except AuthorityGuardError:
        raise
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        raise AuthorityGuardError(str(exc)) from exc


def _verify_contract_content(
    root: Path,
    contract: Mapping[str, Any],
    environment: Mapping[str, Any],
) -> tuple[str, str]:
    _require_keys(contract, CONTRACT_KEYS, "execution contract")
    if contract["schema"] != CONTRACT_SCHEMA or contract["candidate_id"] != CANDIDATE_ID or contract["study_id"] != STUDY_ID:
        raise AuthorityGuardError("execution contract identity drift")

    authorization = _require_keys(
        contract["authorization"],
        {"token", "commit3_subject", "commit3_path_count", "commit3_paths", "external_authority_schema", "external_authority_exact_keys"},
        "authorization",
    )
    if authorization != {
        "token": AUTHORIZATION,
        "commit3_subject": COMMIT3_SUBJECT,
        "commit3_path_count": 3,
        "commit3_paths": CONTRACT_PATHS,
        "external_authority_schema": AUTHORITY_SCHEMA,
        "external_authority_exact_keys": sorted(AUTHORITY_KEYS),
    }:
        raise AuthorityGuardError("authorization block drift")

    ancestry = _require_keys(contract["commit_ancestry"], {"commit1", "commit2"}, "commit ancestry")
    commit1 = _verify_commit(
        root,
        ancestry["commit1"],
        expected_commit=COMMIT1,
        expected_parent=Q1U_CLOSEOUT,
        expected_subject=COMMIT1_SUBJECT,
        expected_paths=PLAN_PATHS,
        label="Commit 1",
    )
    commit2 = _verify_commit(
        root,
        ancestry["commit2"],
        expected_commit=None,
        expected_parent=commit1,
        expected_subject=COMMIT2_SUBJECT,
        expected_paths=IMPLEMENTATION_PATHS,
        label="Commit 2",
    )
    _verify_plan_inputs(root, contract["plan_inputs"])
    _verify_implementation_inputs(root, contract["implementation_inputs"])
    _verify_inherited_inputs(root, contract["inherited_inputs"])

    environment_spec = _require_keys(
        contract["environment"],
        {"record_path", "bytes", "sha256", "schema", "environment_id", "external_root_required", "extracted_file_count", "extracted_file_hash_graph_sha256"},
        "environment",
    )
    if "path" in environment_spec or environment_spec["record_path"] != ENVIRONMENT_RECORD:
        raise AuthorityGuardError("environment.record_path is the sole accepted field")
    record_raw = (root / ENVIRONMENT_RECORD).read_bytes()
    expected_environment = {
        "record_path": ENVIRONMENT_RECORD,
        "bytes": len(record_raw),
        "sha256": sha256_bytes(record_raw),
        "schema": ENVIRONMENT_SCHEMA,
        "environment_id": environment["environment_id"],
        "external_root_required": True,
        "extracted_file_count": 1662,
        "extracted_file_hash_graph_sha256": environment["extracted_file_hash_graph_sha256"],
    }
    if environment_spec != expected_environment:
        raise AuthorityGuardError("environment contract graph drift")

    reviews = _require_keys(contract["review_authorities"], {"plan", "implementation", "contract"}, "review authorities")
    for stage in ("plan", "implementation", "contract"):
        expected = REVIEW_EXPECTATIONS[stage]
        row = reviews[stage]
        keys = {"path", "schema", "verdict"} | ({"bytes", "sha256"} if stage != "contract" else {"hash_binding"})
        _require_keys(row, keys, f"{stage} review authority")
        if row["path"] != expected["path"] or row["schema"] != expected["schema"] or row["verdict"] != expected["verdict"]:
            raise AuthorityGuardError(f"{stage} review authority drift")
        if stage == "contract" and row["hash_binding"] != "EXTERNAL_AUTHORITY_RECORD":
            raise AuthorityGuardError("contract review hash binding drift")
        if stage != "contract":
            _bound_file(root, row)

    agreement = _require_keys(
        contract["agreement"],
        {"common_payload_schema", "cross_implementation", "oracle_wrapper_schema", "reference_wrapper_schema", "within_oracle_fresh_processes", "within_reference_fresh_processes"},
        "agreement",
    )
    if agreement != {
        "common_payload_schema": "e4_pl_q1v_common_certificate_payload_v1",
        "cross_implementation": AGREEMENT_MODE,
        "oracle_wrapper_schema": "anysolver.s4.e4-pl-q1v-oracle-raw-v1",
        "reference_wrapper_schema": "anysolver.s4.e4-pl-q1v-reference-raw-v1",
        "within_oracle_fresh_processes": 2,
        "within_reference_fresh_processes": 2,
    }:
        raise AuthorityGuardError("agreement vocabulary or schema drift")

    if contract["runner_inventory"] != {"count": 3, "runner_ids": RUNNER_IDS}:
        raise AuthorityGuardError("runner inventory drift")
    if contract["scientific_inventory"] != {"count": 5, "inventories_separate": True, "node_ids": SCIENTIFIC_NODE_IDS}:
        raise AuthorityGuardError("scientific inventory drift")
    if contract["output_absences"] != {"absent_from_commit3_tree": True, "paths": OUTCOME_PATHS}:
        raise AuthorityGuardError("output-absence contract drift")
    if contract["production_restriction"] != {
        "legacy_default": "ShellElement",
        "post_execution_source_changes": "FORBIDDEN_REQUIRES_NEW_SUCCESSOR",
        "production": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "q1b_execution": "UNAUTHORIZED",
    }:
        raise AuthorityGuardError("production restriction drift")
    if contract["runtime"] != {
        "environment": {
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "PYTHONHASHSEED": "0",
        },
        "mpmath": "1.3.0_IMPORT_DEPENDENCY_ONLY_CATEGORICAL_USE_FORBIDDEN",
        "precision_bits": [256, 512, 1024],
        "pytest_version": "9.0.1",
        "python_implementation": "CPython",
        "python_version": "3.13.9",
        "reference_categorical_backend": "STANDARD_LIBRARY_ONLY",
        "sympy_environment": "1.14.0_ORACLE_ONLY_REFERENCE_IMPORT_FORBIDDEN",
    }:
        raise AuthorityGuardError("runtime authority drift")
    terminal = _require_keys(
        contract["terminal_authority"],
        {"bytes", "evaluation", "path", "schema", "sha256", "terminal_count"},
        "terminal authority",
    )
    _bound_file(root, terminal)
    if terminal["path"] != "docs/reference_cases/e4_pl_q1v_terminal_table.json" or terminal["schema"] != "anysolver.s4.e4-pl-q1v-terminal-table-v1" or terminal["evaluation"] != "FIRST_MATCH_IN_ASCENDING_PRECEDENCE_WINS" or terminal["terminal_count"] != 12:
        raise AuthorityGuardError("terminal authority drift")
    terminal_table = strict_json_bytes((root / str(terminal["path"])).read_bytes())
    expected_terminal_ids = [
        "BLOCKED_E4_PL_Q1V_BASELINE_MISMATCH",
        "BLOCKED_E4_PL_Q1V_INHERITANCE_MISMATCH",
        "BLOCKED_E4_PL_Q1V_PLAN_AUTHORITY",
        "BLOCKED_E4_PL_Q1V_EXACT_BACKEND",
        "NO_GO_E4_PL_Q1V_FRAME_IDENTITY",
        "BLOCKED_E4_PL_Q1V_IMPLEMENTATION_IDENTITY",
        "BLOCKED_E4_PL_Q1V_CONTRACT_OR_NONDETERMINISM",
        "BLOCKED_E4_PL_Q1V_ORACLE_OR_REVIEW",
        "NO_GO_E4_PL_Q1V_LOCAL_ALGEBRA",
        "NO_GO_E4_PL_Q1V_PATCH_OR_COVARIANCE",
        "UNCLASSIFIED_E4_PL_Q1V_LOCAL_PLANAR_IDENTITY",
        "PROVISIONAL_GO_E4_PL_Q1V_Q1B_PLAN",
    ]
    rows = terminal_table.get("terminals") if isinstance(terminal_table, Mapping) else None
    if not isinstance(rows, list) or [row.get("precedence") for row in rows] != list(range(1, 13)) or [row.get("id") for row in rows] != expected_terminal_ids:
        raise AuthorityGuardError("terminal identities or first-match precedence drift")
    return commit1, commit2


def _verify_output_profile(
    root: Path,
    runner_id: str,
    invocation_mode: str,
    authority_raw: bytes,
) -> None:
    if invocation_mode == "AUTHORITY_CHECK_ONLY" or runner_id in {"REFERENCE_RUNNER", "ORACLE_RUNNER"}:
        forbidden = OUTCOME_PATHS
        required: list[str] = []
    else:
        forbidden = SCIENTIFIC_FORBIDDEN
        required = SCIENTIFIC_REQUIRED
    for relative in forbidden:
        path = root / relative
        if path.exists() or path.is_symlink():
            raise AuthorityGuardError(f"forbidden outcome path exists for runner profile: {relative}")
    if not required:
        return
    for relative in required:
        path = root / relative
        if _is_link(path) or not path.is_file():
            raise AuthorityGuardError(f"required promoted evidence is absent or linked: {relative}")
        strict_json_bytes(path.read_bytes())
    if (root / OUTCOME_PATHS[5]).read_bytes() != authority_raw:
        raise AuthorityGuardError("promoted execution-authority copy is not byte-identical")
    reference_raw = (root / OUTCOME_PATHS[0]).read_bytes()
    oracle_raw = (root / OUTCOME_PATHS[1]).read_bytes()
    agreement_raw = (root / OUTCOME_PATHS[2]).read_bytes()
    reference = strict_json_bytes(reference_raw)
    oracle = strict_json_bytes(oracle_raw)
    agreement = strict_json_bytes(agreement_raw)
    output = strict_json_bytes((root / OUTCOME_PATHS[3]).read_bytes())
    if agreement.get("byte_identical_certificate_payload") is not True:
        raise AuthorityGuardError("agreement does not certify byte-identical payloads")
    payload = reference.get("certificate_payload")
    if payload != oracle.get("certificate_payload") or payload != output.get("certificate_payload"):
        raise AuthorityGuardError("promoted certificate payload disagreement")
    payload_sha = sha256_bytes(canonical_bytes(payload))
    if reference.get("certificate_payload_sha256") != payload_sha or oracle.get("certificate_payload_sha256") != payload_sha or agreement.get("certificate_payload_sha256") != payload_sha:
        raise AuthorityGuardError("promoted certificate-payload hash drift")
    for name, raw in (("reference", reference_raw), ("oracle", oracle_raw)):
        row = agreement.get(name)
        digest = sha256_bytes(raw)
        if not isinstance(row, Mapping) or row.get("deterministic") is not True or row.get("sha256") != digest or row.get("run1_sha256") != digest or row.get("run2_sha256") != digest:
            raise AuthorityGuardError(f"{name} deterministic raw binding drift")
    if output.get("agreement_sha256") != sha256_bytes(agreement_raw):
        raise AuthorityGuardError("combined output does not bind agreement")


def validate_execution_authority(
    *,
    repository_root: Path,
    runner_id: str,
    authority_record_path: Path,
    authority_sha256: str,
    contract_path: Path,
    contract_sha256: str,
    environment_root: Path,
    environment_record_path: Path,
    environment_sha256: str,
    invocation_mode: str,
) -> GuardEvidence:
    """Validate all authority and return inert evidence, or fail closed."""
    try:
        root = repository_root.resolve(strict=True)
        if not root.is_dir() or _is_link(root):
            raise AuthorityGuardError("repository root must be a nonsymlink directory")
        git_root = Path(_run_git(root, "rev-parse", "--show-toplevel")).resolve(strict=True)
        if os.path.normcase(os.path.normpath(git_root)) != os.path.normcase(os.path.normpath(root)):
            raise AuthorityGuardError("caller repository root differs from Git top level")
        if runner_id not in RUNNER_IDS:
            raise AuthorityGuardError("runner id is not registered")
        if invocation_mode not in INVOCATION_MODES:
            raise AuthorityGuardError("invocation mode is not registered")
        worktrees = _worktree_roots(root)
        authority_path = _require_external(authority_record_path, worktrees, "authority record", directory=False)
        external_environment = _require_external(environment_root, worktrees, "environment root", directory=True)
        expected_contract = (root / CONTRACT_PATHS[0]).resolve(strict=True)
        expected_environment = (root / ENVIRONMENT_RECORD).resolve(strict=True)
        if _is_link(contract_path) or contract_path.resolve(strict=True) != expected_contract:
            raise AuthorityGuardError("contract path is not the committed Q1V path")
        if _is_link(environment_record_path) or environment_record_path.resolve(strict=True) != expected_environment:
            raise AuthorityGuardError("environment record path is not the frozen Q1T path")

        authority, authority_raw = _load_canonical(authority_path, authority_sha256, "authority record")
        contract, contract_raw = _load_canonical(expected_contract, contract_sha256, "execution contract")
        environment, environment_raw = _load_canonical(expected_environment, environment_sha256, "environment record")
        _require_keys(authority, AUTHORITY_KEYS, "execution authority")
        if authority["schema"] != AUTHORITY_SCHEMA or authority["authorization"] != AUTHORIZATION or authority["candidate_id"] != CANDIDATE_ID or authority["study_id"] != STUDY_ID:
            raise AuthorityGuardError("execution authority identity drift")
        if environment_sha256.upper() != ENVIRONMENT_SHA256 or sha256_bytes(environment_raw) != ENVIRONMENT_SHA256:
            raise AuthorityGuardError("frozen environment-record identity drift")
        if authority["execution_contract_sha256"] != sha256_bytes(contract_raw) or authority["environment_sha256"] != sha256_bytes(environment_raw):
            raise AuthorityGuardError("execution authority contract/environment binding drift")

        _commit1, commit2 = _verify_contract_content(root, contract, environment)
        head = _run_git(root, "rev-parse", "HEAD")
        tree = _run_git(root, "rev-parse", "HEAD^{tree}")
        if authority["commit"] != head or authority["tree"] != tree:
            raise AuthorityGuardError("execution authority does not bind HEAD/tree")
        cycle = _verify_correction_history(root, authority, head)
        if _cycle_zero_authorization(root, head) == head:
            initial_parent = _run_git(root, "rev-list", "--parents", "-n", "1", head).split()[1]
        else:
            cycle_zero = _cycle_zero_authorization(root, head)
            initial_parent = _run_git(root, "rev-list", "--parents", "-n", "1", cycle_zero).split()[1]
        if initial_parent != commit2:
            raise AuthorityGuardError("cycle-zero authorization does not descend from bound Commit 2")
        subject = _run_git(root, "show", "-s", "--format=%s", head)
        parent = _run_git(root, "rev-list", "--parents", "-n", "1", head).split()[1]
        if authority["authorization_subject"] != subject or authority["authorization_parent"] != parent:
            raise AuthorityGuardError("latest authorization subject/parent drift")
        if authority["latest_accepted_authorization"] != {
            "commit": head,
            "cycle": cycle,
            "subject": subject,
            "tree": tree,
        }:
            raise AuthorityGuardError("latest-accepted-authorization alias drift")
        if authority["pre_certificate_reauthorization"] != {
            "authorization_token": PRE_CERTIFICATE_REAUTHORIZATION,
            "cycle": cycle,
            "hard_freeze_event": HARD_FREEZE_EVENT,
            "all_outcome_paths_absent": True,
            "no_canonical_registered_certificate_exists": True,
            "correction_budget_valid": True,
        }:
            raise AuthorityGuardError("pre-certificate reauthorization drift")
        implementation_inputs = contract["implementation_inputs"]
        if authority["backend_conformance_sha256"] != implementation_inputs["backend_conformance"]["sha256"]:
            raise AuthorityGuardError("backend-conformance authority hash drift")
        if authority["commissioning_agreement_sha256"] != implementation_inputs["commissioning_agreement"]["sha256"]:
            raise AuthorityGuardError("commissioning-agreement authority hash drift")

        if subprocess.run(["git", "diff", "--quiet"], cwd=root, check=False).returncode:
            raise AuthorityGuardError("tracked worktree is dirty")
        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=root, check=False).returncode:
            raise AuthorityGuardError("index is dirty")
        for relative in OUTCOME_PATHS:
            if _git_object_exists(root, f"HEAD:{relative}"):
                raise AuthorityGuardError(f"outcome path existed in Commit 3: {relative}")

        reviews = contract["review_authorities"]
        review_values = {
            "plan": _verify_review(root, "plan", reviews["plan"], authority["plan_review_sha256"]),
            "implementation": _verify_review(root, "implementation", reviews["implementation"], authority["implementation_review_sha256"]),
            "contract": _verify_review(root, "contract", reviews["contract"], authority["contract_review_sha256"]),
        }
        if authority["review_verdicts"] != {stage: value["verdict"] for stage, value in review_values.items()}:
            raise AuthorityGuardError("execution authority review-verdict map drift")
        if authority["runner_ids"] != RUNNER_IDS:
            raise AuthorityGuardError("execution authority runner inventory drift")
        _verify_environment_graph(external_environment, environment)
        if platform.python_implementation() != "CPython" or platform.python_version() != "3.13.9":
            raise AuthorityGuardError("active CPython runtime drift")
        _verify_output_profile(root, runner_id, invocation_mode, authority_raw)
        return GuardEvidence(
            authority=authority,
            contract=contract,
            environment=environment,
            head=head,
            tree=tree,
            runner_id=runner_id,
        )
    except AuthorityGuardError:
        raise
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        raise AuthorityGuardError(str(exc)) from exc
