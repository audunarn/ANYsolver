#!/usr/bin/env python3
"""Mechanics-free guarded launcher for the Q1U scientific inventory.

The launcher authenticates the caller-owned execution authority, committed
execution contract, exact external SymPy environment, and three-stage Git
authority chain before pytest is allowed to collect a scientific test.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import stat
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence

from e4_pl_q1u_authority_guard import (
    AuthorityGuardError,
    canonical_bytes as authority_check_bytes,
    validate_execution_authority,
)


CANDIDATE_ID = "candidate_e4_pl_q1u.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1"
STUDY_ID = "study_e4_pl_q1u.q1t_frozen_mechanics_execution_guard_completion_v1"
RUNNER_ID = "SCIENTIFIC_TEST_RUNNER"
AUTHORIZATION = "AUTHORIZE_E4_PL_Q1U_SCIENTIFIC_EXECUTION"
Q1S_CLOSEOUT = "914a9a633c585d45a419d97f92b4faf7fa1e4486"
COMMIT1_SUBJECT = "docs: preregister E4 PL Q1U exact-oracle completion"
COMMIT2_SUBJECT = "docs: freeze E4 PL Q1U exact reference and oracle"
COMMIT3_SUBJECT = "docs: authorize E4 PL Q1U scientific execution"
AUTHORITY_SCHEMA = "anysolver.s4.e4-pl-q1u-execution-authority-v1"
CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1u-execution-contract-v1"
ENVIRONMENT_SCHEMA = "e4_pl_q1u_environment_record_v1"
RESULT_SCHEMA = "anysolver.s4.e4-pl-q1u-scientific-test-result-v1"
BLOCKED_TERMINAL = "BLOCKED_E4_PL_Q1U_CONTRACT_OR_NONDETERMINISM"

AUTHORITY_KEYS = {
    "schema",
    "authorization",
    "candidate_id",
    "study_id",
    "commit",
    "tree",
    "execution_contract_sha256",
    "environment_sha256",
    "plan_review_sha256",
    "implementation_review_sha256",
    "contract_review_sha256",
    "review_verdicts",
    "runner_ids",
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
    "plan": (
        "anysolver.s4.e4-pl-q1u-plan-review-v1",
        "ACCEPT_Q1U_PREREGISTRATION_NO_P0_P1",
    ),
    "implementation": (
        "anysolver.s4.e4-pl-q1u-implementation-review-v1",
        "ACCEPT_Q1U_IMPLEMENTATION_FREEZE_NO_P0_P1",
    ),
    "contract": (
        "anysolver.s4.e4-pl-q1u-contract-review-v1",
        "ACCEPT_Q1U_EXECUTION_CONTRACT_NO_P0_P1",
    ),
}
REVIEW_PATHS = {
    "plan": "docs/reference_cases/e4_pl_q1u_plan_review.json",
    "implementation": "docs/reference_cases/e4_pl_q1u_implementation_review.json",
    "contract": "docs/reference_cases/e4_pl_q1u_contract_review.json",
}

PLAN_PATHS = [
    "docs/agent_plans/S4_E4_PL_Q1U_EXACT_ORACLE_COMPLETION_PLAN.md",
    "docs/reference_cases/e4_pl_q1u_plan_review.json",
    "docs/reference_cases/e4_pl_q1u_baseline.json",
    "docs/reference_cases/e4_pl_q1u_inheritance_manifest.json",
    "docs/reference_cases/e4_pl_q1u_rejected_evidence_manifest.json",
    "docs/reference_cases/e4_pl_q1u_allowed_extent.json",
    "docs/reference_cases/e4_pl_q1u_environment.json",
    "docs/reference_cases/e4_pl_q1u_environment_builder.py",
    "docs/reference_cases/e4_pl_q1u_exact_backend_contract.json",
    "docs/reference_cases/e4_pl_q1u_certificate_schema.json",
    "docs/reference_cases/e4_pl_q1u_authority_contract.json",
    "docs/reference_cases/e4_pl_q1u_terminal_table.json",
    "docs/reference_cases/e4_pl_q1u_test_inventory.json",
    "tests/test_e4_pl_q1u_preregistration_authority.py",
]
IMPLEMENTATION_PATHS = [
    "docs/reference_cases/e4_pl_q1u_reference.py",
    "docs/reference_cases/e4_pl_q1u_oracle.py",
    "docs/reference_cases/e4_pl_q1u_scientific_test_runner.py",
    "docs/reference_cases/e4_pl_q1u_implementation_manifest.json",
    "docs/reference_cases/e4_pl_q1u_implementation_review.json",
    "tests/test_e4_pl_q1u_exact_backend.py",
    "tests/test_e4_pl_q1u_frame_and_fields.py",
    "tests/test_e4_pl_q1u_local_algebra.py",
    "tests/test_e4_pl_q1u_recovery.py",
    "tests/test_e4_pl_q1u_global_supports.py",
    "tests/test_e4_pl_q1u_terminal_and_agreement.py",
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
NODE_IDS = [
    "tests/test_e4_pl_q1u_frame_and_fields.py::test_q1u_all_56_numbered_frames_and_field_work",
    "tests/test_e4_pl_q1u_local_algebra.py::test_q1u_actual_38_field_condensation_rank_and_rigid_modes",
    "tests/test_e4_pl_q1u_recovery.py::test_q1u_all_224_station_recovery_and_numerical_separation",
    "tests/test_e4_pl_q1u_global_supports.py::test_q1u_global_transform_load_support_solution_and_reactions",
    "tests/test_e4_pl_q1u_terminal_and_agreement.py::test_q1u_evidence_terminal_and_cross_implementation_contract",
]
RUNNER_IDS = ["REFERENCE_RUNNER", "ORACLE_RUNNER", RUNNER_ID]


class AuthorityError(RuntimeError):
    """Raised before collection when Q1U execution authority is invalid."""


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
        )
        + "\n"
    ).encode("utf-8")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _require_exact_keys(value: Mapping[str, Any], keys: set[str], label: str) -> None:
    if set(value) != keys:
        raise AuthorityError(f"wrong exact keys for {label}")


def _is_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction and is_junction())


def _load_canonical(path: Path, expected_sha256: str) -> tuple[dict[str, Any], bytes]:
    if _is_link(path) or not path.is_file():
        raise AuthorityError(f"input is not a regular non-symlink file: {path}")
    raw = path.read_bytes()
    if sha256_bytes(raw) != expected_sha256.upper():
        raise AuthorityError(f"caller hash mismatch: {path}")
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        raise AuthorityError(f"noncanonical UTF-8/LF transport: {path}")
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique_pairs,
        parse_constant=_reject_constant,
    )
    if not isinstance(value, dict) or canonical_bytes(value) != raw:
        raise AuthorityError(f"noncanonical JSON: {path}")
    return value, raw


def _run_git(root: Path, *args: str, check: bool = True) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if check and completed.returncode:
        raise AuthorityError(f"git {' '.join(args)} failed")
    return completed.stdout.strip()


def _repo_root() -> Path:
    probe = Path(__file__).resolve()
    completed = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=probe.parent,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode:
        raise AuthorityError("runner is not in the Q1U Git worktree")
    return Path(completed.stdout.strip()).resolve()


def _worktree_roots(root: Path) -> list[Path]:
    raw = _run_git(root, "worktree", "list", "--porcelain")
    roots = [
        Path(line[9:]).resolve()
        for line in raw.splitlines()
        if line.startswith("worktree ")
    ]
    if root not in roots:
        raise AuthorityError("current worktree is absent from Git worktree inventory")
    return roots


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _require_external(path: Path, worktrees: Iterable[Path], label: str) -> Path:
    if _is_link(path):
        raise AuthorityError(f"{label} must not be a symlink or junction")
    resolved = path.resolve(strict=True)
    if any(_is_within(resolved, item) for item in worktrees):
        raise AuthorityError(f"{label} must be outside every Git worktree")
    return resolved


def _safe_relative_path(value: Any) -> str:
    if not isinstance(value, str):
        raise AuthorityError("bound path is not a string")
    posix = PurePosixPath(value)
    if (
        posix.is_absolute()
        or not posix.parts
        or ".." in posix.parts
        or "\\" in value
        or ":" in value
    ):
        raise AuthorityError(f"unsafe bound path: {value}")
    return value


def _path_bytes_hash(root: Path, row: Mapping[str, Any]) -> None:
    required = {"path", "bytes", "sha256"}
    if not required.issubset(row):
        raise AuthorityError("incomplete bound path row")
    rel = _safe_relative_path(row["path"])
    path = root / Path(*PurePosixPath(rel).parts)
    if _is_link(path) or not path.is_file():
        raise AuthorityError(f"missing regular bound path: {rel}")
    raw = path.read_bytes()
    if len(raw) != int(row["bytes"]) or sha256_bytes(raw) != str(row["sha256"]).upper():
        raise AuthorityError(f"bound path drift: {rel}")


def _bound_rows(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        if {"path", "bytes", "sha256"}.issubset(value):
            yield value
        for child in value.values():
            yield from _bound_rows(child)
    elif isinstance(value, list):
        for child in value:
            yield from _bound_rows(child)


def _review(
    root: Path,
    spec: Mapping[str, Any],
    kind: str,
    authority_hash: str,
) -> dict[str, Any]:
    if "path" not in spec:
        raise AuthorityError(f"missing {kind} review path")
    rel = _safe_relative_path(spec["path"])
    if rel != REVIEW_PATHS[kind]:
        raise AuthorityError(f"wrong fixed {kind} review path")
    path = root / Path(*PurePosixPath(rel).parts)
    if _is_link(path) or not path.is_file():
        raise AuthorityError(f"missing {kind} review")
    raw = path.read_bytes()
    if sha256_bytes(raw) != authority_hash.upper():
        raise AuthorityError(f"authority does not bind {kind} review")
    if "bytes" in spec and len(raw) != int(spec["bytes"]):
        raise AuthorityError(f"{kind} review byte count drift")
    if "sha256" in spec and sha256_bytes(raw) != str(spec["sha256"]).upper():
        raise AuthorityError(f"{kind} review contract hash drift")
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique_pairs,
        parse_constant=_reject_constant,
    )
    if not isinstance(value, dict) or canonical_bytes(value) != raw:
        raise AuthorityError(f"{kind} review is not canonical")
    _require_exact_keys(value, REVIEW_KEYS, f"{kind} review")
    schema, verdict = REVIEW_EXPECTATIONS[kind]
    if value["schema"] != schema or value["verdict"] != verdict:
        raise AuthorityError(f"wrong exact {kind} review verdict")
    return value


def _changed_paths(root: Path, commit: str) -> list[str]:
    return sorted(
        line
        for line in _run_git(
            root,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            commit,
        ).splitlines()
        if line
    )


def _verify_commit_row(
    root: Path,
    row: Mapping[str, Any],
    commit: str,
    parent: str,
    subject: str,
    paths: Sequence[str],
    label: str,
) -> None:
    required = {"commit", "tree", "parent", "subject", "path_count", "paths"}
    _require_exact_keys(row, required, f"{label} ancestry row")
    if row["commit"] != commit or row["parent"] != parent or row["subject"] != subject:
        raise AuthorityError(f"wrong {label} identity")
    if row["tree"] != _run_git(root, "rev-parse", f"{commit}^{{tree}}"):
        raise AuthorityError(f"wrong {label} tree")
    if row["paths"] != list(paths) or int(row["path_count"]) != len(paths):
        raise AuthorityError(f"wrong {label} contract extent")
    if _changed_paths(root, commit) != sorted(paths):
        raise AuthorityError(f"wrong actual {label} path extent")


def _verify_environment_graph(environment_root: Path, record: Mapping[str, Any]) -> None:
    if record.get("schema") != ENVIRONMENT_SCHEMA:
        raise AuthorityError("wrong exact-environment schema")
    if record.get("candidate_id") != CANDIDATE_ID or record.get("study_id") != STUDY_ID:
        raise AuthorityError("exact-environment program identity mismatch")
    expected = record.get("extracted_file_hash_graph")
    if not isinstance(expected, list) or len(expected) != 1662:
        raise AuthorityError("wrong exact-environment file graph count")
    if record.get("extracted_file_count") != 1662:
        raise AuthorityError("wrong exact-environment declared file count")
    if expected != sorted(expected, key=lambda row: row["path"]):
        raise AuthorityError("exact-environment file graph is not sorted")
    graph_digest = sha256_bytes(canonical_bytes(expected))
    if graph_digest != str(record.get("extracted_file_hash_graph_sha256", "")).upper():
        raise AuthorityError("exact-environment file graph digest mismatch")

    actual: list[dict[str, Any]] = []
    for directory, directory_names, file_names in os.walk(
        environment_root,
        topdown=True,
        followlinks=False,
    ):
        current = Path(directory)
        if _is_link(current):
            raise AuthorityError("symlink or junction directory in exact environment")
        for name in directory_names:
            if _is_link(current / name):
                raise AuthorityError("symlink or junction directory in exact environment")
        for name in file_names:
            path = current / name
            if _is_link(path):
                raise AuthorityError("symlink file in exact environment")
            mode = path.stat(follow_symlinks=False).st_mode
            if not stat.S_ISREG(mode):
                raise AuthorityError("non-regular file in exact environment")
            rel = path.relative_to(environment_root).as_posix()
            raw = path.read_bytes()
            actual.append({"bytes": len(raw), "path": rel, "sha256": sha256_bytes(raw).lower()})
    actual.sort(key=lambda row: row["path"])
    if actual != expected:
        raise AuthorityError("external exact-environment file graph drift")


def _verify_inherited_rows(root: Path, inherited: Mapping[str, Any]) -> None:
    _require_exact_keys(inherited, {"count", "rows"}, "inherited inputs")
    rows = inherited["rows"]
    if int(inherited["count"]) != 49 or not isinstance(rows, list) or len(rows) != 49:
        raise AuthorityError("Q1U must bind exactly 49 inherited rows")
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise AuthorityError("invalid inherited row")
        _path_bytes_hash(root, row)
        rel = str(row["path"])
        if rel in seen:
            raise AuthorityError("duplicate inherited path")
        seen.add(rel)
        if not {"source_commit", "git_blob"}.issubset(row):
            raise AuthorityError("inherited row lacks Git-object authority")
        blob = _run_git(root, "rev-parse", f"{row['source_commit']}:{rel}")
        if blob != row["git_blob"]:
            raise AuthorityError(f"inherited Git-object drift: {rel}")
    manifest_path = root / "docs/reference_cases/e4_pl_q1u_inheritance_manifest.json"
    manifest_raw = manifest_path.read_bytes()
    manifest = json.loads(
        manifest_raw.decode("utf-8"),
        object_pairs_hook=_unique_pairs,
        parse_constant=_reject_constant,
    )
    if not isinstance(manifest, dict) or canonical_bytes(manifest) != manifest_raw:
        raise AuthorityError("inheritance manifest is not canonical")
    expected_rows = [
        *manifest["q1r_e4_inherited_inputs"],
        *manifest["q1s_commit1_inputs"],
        *manifest["q1s_closeout_inputs"],
    ]
    if rows != expected_rows:
        raise AuthorityError("contract does not bind the exact expanded 49-row inheritance")


def _verify_stage_bindings(root: Path, contract: Mapping[str, Any]) -> None:
    plan = contract["plan_inputs"]
    if not isinstance(plan, Mapping) or set(plan) != {"count", "rows"}:
        raise AuthorityError("wrong plan-input structure")
    if (
        not isinstance(plan["rows"], list)
        or int(plan["count"]) != len(plan["rows"])
        or len(plan["rows"]) != len(PLAN_PATHS)
    ):
        raise AuthorityError("wrong plan-input count")
    plan_bound = {str(row["path"]) for row in plan["rows"]}
    expected_plan_bound = set(PLAN_PATHS)
    if plan_bound != expected_plan_bound:
        raise AuthorityError("plan inputs do not bind exact PLAN14 paths")

    implementation = contract["implementation_inputs"]
    if not isinstance(implementation, Mapping):
        raise AuthorityError("wrong implementation-input structure")
    _require_exact_keys(
        implementation,
        {
            "reference",
            "oracle",
            "scientific_runner",
            "manifest",
            "implementation_review",
            "exact_backend_test",
            "scientific_tests",
        },
        "implementation inputs",
    )
    implementation_rows = list(_bound_rows(implementation))
    implementation_bound = {str(row["path"]) for row in implementation_rows}
    expected_implementation = set(IMPLEMENTATION_PATHS)
    if (
        implementation_bound != expected_implementation
        or len(implementation_rows) != len(IMPLEMENTATION_PATHS)
    ):
        raise AuthorityError("implementation inputs do not bind exact IMPLEMENTATION11")

    for row in _bound_rows(plan):
        _path_bytes_hash(root, row)
    for row in _bound_rows(implementation):
        _path_bytes_hash(root, row)


def verify_authority(
    authority_path: Path,
    authority_sha256: str,
    contract_path: Path,
    contract_sha256: str,
    environment_root: Path,
    environment_sha256: str,
    requested_runner: str,
) -> tuple[Path, dict[str, Any], dict[str, Any], Path]:
    """Authenticate Q1U execution without importing or collecting mechanics."""
    if requested_runner != RUNNER_ID:
        raise AuthorityError("wrong runner id")
    root = _repo_root()
    worktrees = _worktree_roots(root)
    authority_resolved = _require_external(authority_path, worktrees, "authority record")
    environment_resolved = _require_external(environment_root, worktrees, "environment root")
    if not environment_resolved.is_dir():
        raise AuthorityError("environment root is not a directory")
    if _is_link(contract_path):
        raise AuthorityError("contract path must not be a symlink")
    contract_resolved = contract_path.resolve(strict=True)
    committed_contract = (root / CONTRACT_PATHS[0]).resolve(strict=True)
    if contract_resolved != committed_contract:
        raise AuthorityError("contract path is not the committed Q1U contract")

    authority, _authority_raw = _load_canonical(authority_resolved, authority_sha256)
    contract, contract_raw = _load_canonical(contract_resolved, contract_sha256)
    environment_path = root / "docs/reference_cases/e4_pl_q1u_environment.json"
    environment, environment_raw = _load_canonical(environment_path, environment_sha256)
    _require_exact_keys(authority, AUTHORITY_KEYS, "execution authority")
    _require_exact_keys(contract, CONTRACT_KEYS, "execution contract")
    if authority["schema"] != AUTHORITY_SCHEMA or contract["schema"] != CONTRACT_SCHEMA:
        raise AuthorityError("wrong authority or contract schema")
    for value in (authority, contract, environment):
        if value["candidate_id"] != CANDIDATE_ID or value["study_id"] != STUDY_ID:
            raise AuthorityError("program identity mismatch")
    if authority["authorization"] != AUTHORIZATION:
        raise AuthorityError("wrong authority token")
    if authority["execution_contract_sha256"].upper() != sha256_bytes(contract_raw):
        raise AuthorityError("authority does not bind contract")
    if authority["environment_sha256"].upper() != sha256_bytes(environment_raw):
        raise AuthorityError("authority does not bind environment record")

    authorization = contract["authorization"]
    expected_authorization = {
        "token": AUTHORIZATION,
        "commit3_subject": COMMIT3_SUBJECT,
        "commit3_path_count": len(CONTRACT_PATHS),
        "commit3_paths": CONTRACT_PATHS,
        "external_authority_schema": AUTHORITY_SCHEMA,
        "external_authority_exact_keys": sorted(AUTHORITY_KEYS),
    }
    if authorization != expected_authorization:
        raise AuthorityError("wrong contract authorization")

    head = _run_git(root, "rev-parse", "HEAD")
    tree = _run_git(root, "rev-parse", "HEAD^{tree}")
    if authority["commit"] != head or authority["tree"] != tree:
        raise AuthorityError("authority does not bind HEAD Commit 3")
    if _run_git(root, "show", "-s", "--format=%s", head) != COMMIT3_SUBJECT:
        raise AuthorityError("HEAD is not the authorized Commit 3")
    commit2 = _run_git(root, "rev-parse", "HEAD^")
    commit1 = _run_git(root, "rev-parse", "HEAD^^")
    base = _run_git(root, "rev-parse", "HEAD^^^")
    if base != Q1S_CLOSEOUT:
        raise AuthorityError("wrong fixed Q1S closeout ancestry")
    for commit, parent in ((head, commit2), (commit2, commit1), (commit1, Q1S_CLOSEOUT)):
        if _run_git(root, "rev-list", "--parents", "-n", "1", commit).split() != [commit, parent]:
            raise AuthorityError("Q1U authority commits must have exactly one parent")
    ancestry = contract["commit_ancestry"]
    _require_exact_keys(ancestry, {"commit1", "commit2"}, "commit ancestry")
    _verify_commit_row(root, ancestry["commit1"], commit1, Q1S_CLOSEOUT, COMMIT1_SUBJECT, PLAN_PATHS, "Commit 1")
    _verify_commit_row(root, ancestry["commit2"], commit2, commit1, COMMIT2_SUBJECT, IMPLEMENTATION_PATHS, "Commit 2")
    if _changed_paths(root, head) != sorted(CONTRACT_PATHS):
        raise AuthorityError("wrong exact Commit 3 path extent")

    if subprocess.run(["git", "diff", "--quiet"], cwd=root, check=False).returncode:
        raise AuthorityError("tracked worktree is dirty")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=root, check=False).returncode:
        raise AuthorityError("index is dirty")

    _verify_stage_bindings(root, contract)
    _verify_inherited_rows(root, contract["inherited_inputs"])
    # Every content-addressed row in the contract is checked, including any
    # contract-test or terminal binding added outside the stage groupings.
    for row in _bound_rows(contract):
        _path_bytes_hash(root, row)

    reviews = contract["review_authorities"]
    _require_exact_keys(reviews, {"plan", "implementation", "contract"}, "review authorities")
    plan_review = _review(root, reviews["plan"], "plan", authority["plan_review_sha256"])
    implementation_review = _review(
        root,
        reviews["implementation"],
        "implementation",
        authority["implementation_review_sha256"],
    )
    contract_review = _review(
        root,
        reviews["contract"],
        "contract",
        authority["contract_review_sha256"],
    )
    verdicts = {
        "plan": plan_review["verdict"],
        "implementation": implementation_review["verdict"],
        "contract": contract_review["verdict"],
    }
    if authority["review_verdicts"] != verdicts:
        raise AuthorityError("authority review-verdict map mismatch")

    environment_spec = contract["environment"]
    if not isinstance(environment_spec, Mapping):
        raise AuthorityError("wrong environment contract")
    if environment_spec.get("record_path") != "docs/reference_cases/e4_pl_q1t_environment.json":
        raise AuthorityError("wrong committed environment-record path")
    if int(environment_spec.get("bytes", -1)) != len(environment_raw):
        raise AuthorityError("environment-record byte count mismatch")
    if str(environment_spec.get("sha256", "")).upper() != sha256_bytes(environment_raw):
        raise AuthorityError("environment-record contract hash mismatch")
    if environment_spec.get("extracted_file_count") != 1662:
        raise AuthorityError("environment contract must bind 1662 extracted files")
    if str(environment_spec.get("extracted_file_hash_graph_sha256", "")).upper() != str(
        environment["extracted_file_hash_graph_sha256"]
    ).upper():
        raise AuthorityError("environment graph contract digest mismatch")
    _verify_environment_graph(environment_resolved, environment)

    runner_inventory = contract["runner_inventory"]
    if runner_inventory != {"count": 3, "runner_ids": RUNNER_IDS}:
        raise AuthorityError("runner inventory details drifted")
    if authority["runner_ids"] != RUNNER_IDS:
        raise AuthorityError("authority runner inventory mismatch")
    if contract["scientific_inventory"] != {
        "count": 5,
        "node_ids": NODE_IDS,
        "inventories_separate": True,
    }:
        raise AuthorityError("wrong exact five-node scientific inventory")

    runtime = contract["runtime"]
    required_runtime = {
        "environment": {
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "PYTHONHASHSEED": "0",
        },
        "mpmath": "1.3.0_IMPORT_DEPENDENCY_ONLY_CATEGORICAL_USE_FORBIDDEN",
        "precision_bits": [256, 512, 1024],
        "python_implementation": "CPython",
        "python_version": "3.13.9",
        "pytest_version": "9.0.1",
        "reference_categorical_backend": "STANDARD_LIBRARY_ONLY",
        "sympy_environment": "1.14.0_ORACLE_ONLY_REFERENCE_IMPORT_FORBIDDEN",
    }
    if runtime != required_runtime:
        raise AuthorityError("wrong exact runtime authority")
    if platform.python_implementation() != "CPython" or platform.python_version() != "3.13.9":
        raise AuthorityError("active CPython runtime mismatch")
    if importlib.metadata.version("pytest") != "9.0.1":
        raise AuthorityError("active pytest runtime mismatch")

    output_absences = contract["output_absences"]
    if output_absences != {"paths": OUTCOME_PATHS, "absent_from_commit3_tree": True}:
        raise AuthorityError("wrong output-absence contract")
    for rel in OUTCOME_PATHS:
        probe = subprocess.run(
            ["git", "cat-file", "-e", f"HEAD:{rel}"],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if probe.returncode == 0:
            raise AuthorityError(f"outcome path existed in Commit 3: {rel}")

    agreement = contract["agreement"]
    if not isinstance(agreement, Mapping):
        raise AuthorityError("wrong agreement contract")
    if agreement.get("within_reference_fresh_processes") != 2 or agreement.get("within_oracle_fresh_processes") != 2:
        raise AuthorityError("wrong fresh-process agreement authority")
    if agreement.get("cross_implementation") != "BYTE_IDENTICAL_CANONICAL_CERTIFICATE_PAYLOAD":
        raise AuthorityError("wrong cross-implementation agreement authority")
    terminal = contract["terminal_authority"]
    if not isinstance(terminal, Mapping):
        raise AuthorityError("wrong terminal authority")
    if terminal.get("path") != "docs/reference_cases/e4_pl_q1u_terminal_table.json":
        raise AuthorityError("wrong terminal-table path")
    if terminal.get("schema") != "anysolver.s4.e4-pl-q1u-terminal-table-v1":
        raise AuthorityError("wrong terminal-table schema")
    if terminal.get("evaluation") != "FIRST_MATCH_IN_ASCENDING_PRECEDENCE_WINS":
        raise AuthorityError("wrong terminal precedence")
    if terminal.get("terminal_count") != 11:
        raise AuthorityError("wrong Q1U terminal count")
    production = contract["production_restriction"]
    required_production = {
        "production": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "q1b_execution": "UNAUTHORIZED",
        "legacy_default": "ShellElement",
        "post_execution_source_changes": "FORBIDDEN_REQUIRES_NEW_SUCCESSOR",
    }
    if production != required_production:
        raise AuthorityError("production restriction drift")
    return root, authority, contract, environment_resolved


def _execute_pytest(
    root: Path,
    environment_root: Path,
    authority_sha256: str,
    contract_sha256: str,
    environment_sha256: str,
) -> dict[str, Any]:
    temp_root = Path(tempfile.mkdtemp(prefix="anysolver-q1u-scientific-"))
    worktrees = _worktree_roots(root)
    if any(_is_within(temp_root.resolve(), item) for item in worktrees):
        raise AuthorityError("scientific basetemp must be outside every Git worktree")
    basetemp = temp_root / "pytest"
    env = os.environ.copy()
    previous_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = str(environment_root) + (
        os.pathsep + previous_pythonpath if previous_pythonpath else ""
    )
    env.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
        }
    )
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-ra",
        "-p",
        "no:cacheprovider",
        f"--basetemp={basetemp}",
        *NODE_IDS,
    ]
    completed = subprocess.run(
        command,
        cwd=root,
        env=env,
        check=False,
        capture_output=True,
        text=False,
    )
    summary = (completed.stdout + b"\n" + completed.stderr).decode("utf-8", errors="replace")
    if completed.returncode != 0:
        raise AuthorityError("guarded scientific inventory failed")
    if re.search(r"\b(skipped|xfailed|xpassed|xpass|xfail)\b", summary, flags=re.IGNORECASE):
        raise AuthorityError("skip/xfail/xpass is forbidden")
    if not re.search(r"\b5 passed\b", summary):
        raise AuthorityError("scientific inventory did not report exactly five passes")
    return {
        "authority_sha256": authority_sha256.upper(),
        "candidate_id": CANDIDATE_ID,
        "contract_sha256": contract_sha256.upper(),
        "environment_sha256": environment_sha256.upper(),
        "node_count": 5,
        "node_ids": NODE_IDS,
        "pytest_result": "5_PASSED_NO_SKIP_XFAIL_XPASS",
        "returncode": completed.returncode,
        "runner_id": RUNNER_ID,
        "schema": RESULT_SCHEMA,
        "study_id": STUDY_ID,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authority-record", required=True, type=Path)
    parser.add_argument("--authority-sha256", required=True)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--environment-root", required=True, type=Path)
    parser.add_argument("--environment-record", required=True, type=Path)
    parser.add_argument("--environment-sha256", required=True)
    parser.add_argument("--runner-id", required=True)
    parser.add_argument("--authority-check-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.runner_id != RUNNER_ID:
            raise AuthorityGuardError(f"scientific-test executable requires {RUNNER_ID}")
        evidence = validate_execution_authority(
            repository_root=Path(__file__).resolve().parents[2],
            runner_id=args.runner_id,
            authority_record_path=args.authority_record,
            authority_sha256=args.authority_sha256,
            contract_path=args.contract,
            contract_sha256=args.contract_sha256,
            environment_root=args.environment_root,
            environment_record_path=args.environment_record,
            environment_sha256=args.environment_sha256,
            invocation_mode="AUTHORITY_CHECK_ONLY" if args.authority_check_only else "EXECUTE",
        )
        if args.authority_check_only:
            result: dict[str, Any] = {
                "mode": "AUTHORITY_CHECK_ONLY",
                "runner_id": RUNNER_ID,
                "schema": "anysolver.s4.e4-pl-q1u-authority-check-v1",
                "status": "PASS",
            }
        else:
            result = _execute_pytest(
                Path(__file__).resolve().parents[2],
                args.environment_root.resolve(strict=True),
                args.authority_sha256,
                args.contract_sha256,
                args.environment_sha256,
            )
        sys.stdout.buffer.write(authority_check_bytes(result) if args.authority_check_only else canonical_bytes(result))
        return 0
    except AuthorityGuardError as exc:
        sys.stderr.write(f"{BLOCKED_TERMINAL}: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
