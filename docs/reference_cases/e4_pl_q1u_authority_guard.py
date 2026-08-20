#!/usr/bin/env python3
"""Shared, mechanics-free execution authority guard for E4-PL-Q1U.

This module intentionally uses only the Python standard library.  It may be
imported before authority exists, but :func:`validate_execution_authority`
must complete before a registered geometry is constructed, an exact backend
is activated, a solve is attempted, or scientific pytest collection starts.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import stat
import subprocess
from typing import Any, Iterable, Iterator, Mapping


CANDIDATE_ID = "candidate_e4_pl_q1u.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1"
STUDY_ID = "study_e4_pl_q1u.q1t_frozen_mechanics_execution_guard_completion_v1"
AUTHORIZATION = "AUTHORIZE_E4_PL_Q1U_SCIENTIFIC_EXECUTION"
Q1T_CLOSEOUT = "850733cc9d2f9185d0a73c5fa6c0acd89067caba"
COMMIT1 = "2404ec3cec03fe9ddef131d9bfd39a24e4e7eabc"
COMMIT1_TREE = "25bc45287495e9349eeebf552e76f88ec70c13b6"
COMMIT1_SUBJECT = "docs: preregister E4 PL Q1U execution-guard completion"
COMMIT2_SUBJECT = "docs: freeze E4 PL Q1U guard-corrected implementations"
COMMIT3_SUBJECT = "docs: authorize E4 PL Q1U scientific execution"
AUTHORITY_SCHEMA = "anysolver.s4.e4-pl-q1u-execution-authority-v1"
CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1u-execution-contract-v1"
ENVIRONMENT_SCHEMA = "e4_pl_q1t_environment_record_v1"
AGREEMENT_MODE = "BYTE_IDENTICAL_CANONICAL_CERTIFICATE_PAYLOAD"
ENVIRONMENT_RECORD = "docs/reference_cases/e4_pl_q1t_environment.json"
ENVIRONMENT_SHA256 = "5461206324E7FC2A52B334CE736A512EE71313ED79181438047E3E20069A9746"

RUNNER_IDS = ["REFERENCE_RUNNER", "ORACLE_RUNNER", "SCIENTIFIC_TEST_RUNNER"]
INVOCATION_MODES = {"AUTHORITY_CHECK_ONLY", "EXECUTE"}

PLAN_PATHS = [
    "docs/agent_plans/S4_E4_PL_Q1U_EXECUTION_GUARD_COMPLETION_PLAN.md",
    "docs/reference_cases/e4_pl_q1u_plan_review.json",
    "docs/reference_cases/e4_pl_q1u_baseline.json",
    "docs/reference_cases/e4_pl_q1u_inheritance_manifest.json",
    "docs/reference_cases/e4_pl_q1u_allowed_extent.json",
    "docs/reference_cases/e4_pl_q1u_contract_vocabulary.json",
    "docs/reference_cases/e4_pl_q1u_review_schema.json",
    "docs/reference_cases/e4_pl_q1u_mechanics_equivalence_contract.json",
    "docs/reference_cases/e4_pl_q1u_authority_contract.json",
    "docs/reference_cases/e4_pl_q1u_terminal_table.json",
    "docs/reference_cases/e4_pl_q1u_test_inventory.json",
    "tests/test_e4_pl_q1u_preregistration_authority.py",
]
IMPLEMENTATION_PATHS = [
    "docs/reference_cases/e4_pl_q1u_authority_guard.py",
    "docs/reference_cases/e4_pl_q1u_reference.py",
    "docs/reference_cases/e4_pl_q1u_oracle.py",
    "docs/reference_cases/e4_pl_q1u_scientific_test_runner.py",
    "docs/reference_cases/e4_pl_q1u_implementation_manifest.json",
    "docs/reference_cases/e4_pl_q1u_mechanics_equivalence.json",
    "docs/reference_cases/e4_pl_q1u_implementation_review.json",
    "tests/test_e4_pl_q1u_frame_and_fields.py",
    "tests/test_e4_pl_q1u_local_algebra.py",
    "tests/test_e4_pl_q1u_recovery.py",
    "tests/test_e4_pl_q1u_global_supports.py",
    "tests/test_e4_pl_q1u_terminal_and_agreement.py",
    "tests/test_e4_pl_q1u_exact_backend.py",
    "tests/test_e4_pl_q1u_authority_guard.py",
]
CONTRACT_PATHS = [
    "docs/reference_cases/e4_pl_q1u_execution_contract.json",
    "docs/reference_cases/e4_pl_q1u_contract_review.json",
    "tests/test_e4_pl_q1u_contract.py",
]
OUTCOME_PATHS = [
    "docs/reference_cases/e4_pl_q1u_reference_raw.json",
    "docs/reference_cases/e4_pl_q1u_oracle_raw.json",
    "docs/reference_cases/e4_pl_q1u_agreement.json",
    "docs/reference_cases/e4_pl_q1u_output.json",
    "docs/reference_cases/e4_pl_q1u_status.json",
    "docs/reference_cases/e4_pl_q1u_execution_authority.json",
    "docs/reference_cases/e4_pl_q1u_scientific_test_result.json",
    "docs/E4_PL_Q1U_LOCAL_QUALIFICATION.md",
    "docs/reference_cases/e4_pl_q1u_scientific_review.json",
    "docs/E4_PL_Q1U_COMPLETION.md",
    "tests/test_e4_pl_q1u_closeout.py",
]
SCIENTIFIC_REQUIRED = OUTCOME_PATHS[:4] + [OUTCOME_PATHS[5]]
SCIENTIFIC_FORBIDDEN = [OUTCOME_PATHS[index] for index in (4, 6, 7, 8, 9, 10)]
SCIENTIFIC_NODE_IDS = [
    "tests/test_e4_pl_q1u_frame_and_fields.py::test_q1u_all_56_numbered_frames_and_field_work",
    "tests/test_e4_pl_q1u_local_algebra.py::test_q1u_actual_38_field_condensation_rank_and_rigid_modes",
    "tests/test_e4_pl_q1u_recovery.py::test_q1u_all_224_station_recovery_and_numerical_separation",
    "tests/test_e4_pl_q1u_global_supports.py::test_q1u_global_transform_load_support_solution_and_reactions",
    "tests/test_e4_pl_q1u_terminal_and_agreement.py::test_q1u_evidence_terminal_and_cross_implementation_contract",
]

AUTHORITY_KEYS = {
    "authorization",
    "candidate_id",
    "commit",
    "contract_review_sha256",
    "environment_sha256",
    "execution_contract_sha256",
    "implementation_review_sha256",
    "plan_review_sha256",
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
        "path": "docs/reference_cases/e4_pl_q1u_plan_review.json",
        "schema": "anysolver.s4.e4-pl-q1u-plan-review-v1",
        "verdict": "ACCEPT_Q1U_PREREGISTRATION_NO_P0_P1",
        "role": "INDEPENDENT_PLAN_ONLY_REVIEWER",
        "inputs": [path for path in PLAN_PATHS if not path.endswith("plan_review.json")],
    },
    "implementation": {
        "path": "docs/reference_cases/e4_pl_q1u_implementation_review.json",
        "schema": "anysolver.s4.e4-pl-q1u-implementation-review-v1",
        "verdict": "ACCEPT_Q1U_IMPLEMENTATION_FREEZE_NO_P0_P1",
        "role": "INDEPENDENT_IMPLEMENTATION_REVIEWER",
        "inputs": [path for path in IMPLEMENTATION_PATHS if not path.endswith("implementation_review.json")],
    },
    "contract": {
        "path": "docs/reference_cases/e4_pl_q1u_contract_review.json",
        "schema": "anysolver.s4.e4-pl-q1u-contract-review-v1",
        "verdict": "ACCEPT_Q1U_EXECUTION_CONTRACT_NO_P0_P1",
        "role": "INDEPENDENT_EXECUTION_CONTRACT_REVIEWER",
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
        "manifest",
        "mechanics_equivalence",
        "implementation_review",
        "exact_backend_test",
        "authority_guard_test",
        "scientific_tests",
    }
    value = _require_keys(value, expected_keys, "implementation inputs")
    row_keys = {
        "authority_guard": {"path", "bytes", "sha256", "entrypoint"},
        "reference": {"path", "bytes", "sha256", "implementation_id"},
        "oracle": {"path", "bytes", "sha256", "implementation_id"},
        "scientific_runner": {"path", "bytes", "sha256", "runner_id"},
        "manifest": {"path", "bytes", "sha256", "schema"},
        "mechanics_equivalence": {"path", "bytes", "sha256", "schema"},
        "implementation_review": {"path", "bytes", "sha256", "schema", "verdict"},
        "exact_backend_test": {"path", "bytes", "sha256", "node_ids"},
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
        raise AuthorityGuardError("implementation inputs do not cover exact IMPLEMENTATION14")
    if value["authority_guard"]["entrypoint"] != "validate_execution_authority":
        raise AuthorityGuardError("shared guard entrypoint drift")
    if value["reference"]["implementation_id"] != "Q1U_REFERENCE_STDLIB_FIELD_ALG":
        raise AuthorityGuardError("reference implementation identity drift")
    if value["oracle"]["implementation_id"] != "Q1U_ORACLE_SYMPY_ALGEBRAIC_FIELD":
        raise AuthorityGuardError("oracle implementation identity drift")
    if value["scientific_runner"]["runner_id"] != "SCIENTIFIC_TEST_RUNNER":
        raise AuthorityGuardError("scientific runner identity drift")
    expected_nodes = {path.split("::", 1)[0]: path for path in SCIENTIFIC_NODE_IDS}
    for row in tests:
        if row["node_ids"] != [expected_nodes.get(row["path"])]:
            raise AuthorityGuardError("scientific-test node binding drift")


def _verify_inherited_inputs(root: Path, value: Any) -> None:
    value = _require_keys(value, {"count", "rows"}, "inherited inputs")
    manifest_path = root / "docs/reference_cases/e4_pl_q1u_inheritance_manifest.json"
    manifest = strict_json_bytes(manifest_path.read_bytes())
    _require_keys(
        manifest,
        {"candidate_id", "classifications", "counts", "git_object_format", "inputs", "q1t_authority", "rule", "schema", "study_id"},
        "inheritance manifest",
    )
    rows = value["rows"]
    if value["count"] != 82 or rows != manifest["inputs"] or not isinstance(rows, list):
        raise AuthorityGuardError("contract must bind exact 82-row inheritance manifest")
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
    independence = {
        "authored_review_only": True,
        "mechanics_executed": False,
        "reviewed_input_authorship": False,
        "role": expected["role"],
    }
    if review["reviewer_independence"] != independence:
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
        expected_parent=Q1T_CLOSEOUT,
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
        "common_payload_schema": "e4_pl_q1u_common_certificate_payload_v1",
        "cross_implementation": AGREEMENT_MODE,
        "oracle_wrapper_schema": "anysolver.s4.e4-pl-q1u-oracle-raw-v1",
        "reference_wrapper_schema": "anysolver.s4.e4-pl-q1u-reference-raw-v1",
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
    if terminal["path"] != "docs/reference_cases/e4_pl_q1u_terminal_table.json" or terminal["schema"] != "anysolver.s4.e4-pl-q1u-terminal-table-v1" or terminal["evaluation"] != "FIRST_MATCH_IN_ASCENDING_PRECEDENCE_WINS" or terminal["terminal_count"] != 11:
        raise AuthorityGuardError("terminal authority drift")
    terminal_table = strict_json_bytes((root / str(terminal["path"])).read_bytes())
    expected_terminal_ids = [
        "BLOCKED_E4_PL_Q1U_BASELINE_MISMATCH",
        "BLOCKED_E4_PL_Q1U_INHERITANCE_MISMATCH",
        "BLOCKED_E4_PL_Q1U_PLAN_AUTHORITY",
        "BLOCKED_E4_PL_Q1U_EXACT_ORACLE_IDENTITY",
        "BLOCKED_E4_PL_Q1U_IMPLEMENTATION_IDENTITY",
        "BLOCKED_E4_PL_Q1U_CONTRACT_OR_NONDETERMINISM",
        "BLOCKED_E4_PL_Q1U_ORACLE_OR_REVIEW",
        "NO_GO_E4_PL_Q1U_LOCAL_ALGEBRA",
        "NO_GO_E4_PL_Q1U_PATCH_OR_COVARIANCE",
        "UNCLASSIFIED_E4_PL_Q1U_LOCAL_PLANAR_IDENTITY",
        "PROVISIONAL_GO_E4_PL_Q1U_Q1B_PLAN",
    ]
    rows = terminal_table.get("terminals") if isinstance(terminal_table, Mapping) else None
    if not isinstance(rows, list) or [row.get("precedence") for row in rows] != list(range(1, 12)) or [row.get("id") for row in rows] != expected_terminal_ids:
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
            raise AuthorityGuardError("contract path is not the committed Q1U path")
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
        if _run_git(root, "rev-list", "--parents", "-n", "1", head).split() != [head, commit2]:
            raise AuthorityGuardError("Commit 3 parent drift")
        if _run_git(root, "show", "-s", "--format=%s", head) != COMMIT3_SUBJECT:
            raise AuthorityGuardError("Commit 3 subject drift")
        if _changed_paths(root, head) != sorted(CONTRACT_PATHS):
            raise AuthorityGuardError("Commit 3 exact path extent drift")

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
