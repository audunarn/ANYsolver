#!/usr/bin/env python3
"""Guarded Q1S scientific-test runner.

This program contains no shell mechanics.  It authenticates the exact three-
commit execution authority before pytest can collect any scientific test and
then invokes only the five preregistered nodes in a fresh process.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
from typing import Any, Mapping, Sequence


CANDIDATE_ID = "candidate_e4_pl_q1s.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1"
STUDY_ID = "study_e4_pl_q1s.q1r_frozen_identity_implementation_completion_v1"
RUNNER_ID = "SCIENTIFIC_TEST_RUNNER"
AUTHORIZATION = "AUTHORIZE_E4_PL_Q1S_SCIENTIFIC_EXECUTION"
COMMIT3_SUBJECT = "docs: authorize E4 PL Q1S scientific execution"
COMMIT2_SUBJECT = "docs: freeze E4 PL Q1S independent implementations"
COMMIT1_SUBJECT = "docs: preregister E4 PL Q1S implementation completion"
Q1R_CLOSEOUT = "46231c56d4c7d24000421fc3ba0f4800239e64bd"
CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1s-execution-contract-v1"
AUTHORITY_SCHEMA = "anysolver.s4.e4-pl-q1s-execution-authority-v1"
RESULT_SCHEMA = "anysolver.s4.e4-pl-q1s-scientific-test-result-v1"

CONTRACT_KEYS = {
    "agreement",
    "authorization",
    "candidate_id",
    "commit_ancestry",
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
AUTHORITY_KEYS = {
    "authorization",
    "candidate_id",
    "commit",
    "contract_review_sha256",
    "execution_contract_sha256",
    "implementation_review_sha256",
    "plan_review_sha256",
    "review_verdicts",
    "runner_ids",
    "schema",
    "study_id",
    "tree",
}
COMMIT3_PATHS = [
    "docs/reference_cases/e4_pl_q1s_execution_contract.json",
    "docs/reference_cases/e4_pl_q1s_contract_review.json",
    "tests/test_e4_pl_q1s_contract.py",
]
OUTCOME_PATHS = [
    "docs/reference_cases/e4_pl_q1s_reference_raw.json",
    "docs/reference_cases/e4_pl_q1s_oracle_raw.json",
    "docs/reference_cases/e4_pl_q1s_agreement.json",
    "docs/reference_cases/e4_pl_q1s_output.json",
    "docs/reference_cases/e4_pl_q1s_status.json",
    "docs/reference_cases/e4_pl_q1s_execution_authority.json",
    "docs/reference_cases/e4_pl_q1s_scientific_test_result.json",
    "docs/E4_PL_Q1S_LOCAL_QUALIFICATION.md",
    "docs/reference_cases/e4_pl_q1s_scientific_review.json",
    "docs/E4_PL_Q1S_COMPLETION.md",
    "tests/test_e4_pl_q1s_closeout.py",
]
NODE_IDS = [
    "tests/test_e4_pl_q1s_frame_and_fields.py::test_q1s_all_56_numbered_frames_and_field_work",
    "tests/test_e4_pl_q1s_local_algebra.py::test_q1s_actual_38_field_condensation_rank_and_rigid_modes",
    "tests/test_e4_pl_q1s_recovery.py::test_q1s_all_224_station_recovery_and_numerical_separation",
    "tests/test_e4_pl_q1s_global_supports.py::test_q1s_global_transform_load_support_solution_and_reactions",
    "tests/test_e4_pl_q1s_terminal_and_agreement.py::test_q1s_evidence_terminal_and_cross_implementation_contract",
]
REVIEW_EXPECTATIONS = {
    "plan": (
        "anysolver.s4.e4-pl-q1s-plan-review-v1",
        "ACCEPT_Q1S_PREREGISTRATION_NO_P0_P1",
    ),
    "implementation": (
        "anysolver.s4.e4-pl-q1s-implementation-review-v1",
        "ACCEPT_Q1S_IMPLEMENTATION_FREEZE_NO_P0_P1",
    ),
    "contract": (
        "anysolver.s4.e4-pl-q1s-contract-review-v1",
        "ACCEPT_Q1S_EXECUTION_CONTRACT_NO_P0_P1",
    ),
}
REVIEW_KEYS = {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"}


class AuthorityError(RuntimeError):
    """Raised before collection when execution authority is invalid."""


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


def _load_canonical(path: Path, expected_sha256: str) -> tuple[dict[str, Any], bytes]:
    if path.is_symlink() or not path.is_file():
        raise AuthorityError(f"authority input is not a regular non-symlink file: {path}")
    raw = path.read_bytes()
    if sha256_bytes(raw) != expected_sha256.upper():
        raise AuthorityError(f"caller hash mismatch: {path}")
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or not raw.endswith(b"\n"):
        raise AuthorityError(f"noncanonical transport: {path}")
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
        raise AuthorityError("not in the Q1S Git worktree")
    return Path(completed.stdout.strip()).resolve()


def _worktree_roots(root: Path) -> list[Path]:
    raw = _run_git(root, "worktree", "list", "--porcelain")
    return [Path(line[9:]).resolve() for line in raw.splitlines() if line.startswith("worktree ")]


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _require_exact_keys(value: Mapping[str, Any], keys: set[str], label: str) -> None:
    if set(value) != keys:
        raise AuthorityError(f"wrong exact keys for {label}")


def _row_path_hash(root: Path, row: Mapping[str, Any]) -> None:
    if set(row) - {"path", "bytes", "sha256", "schema", "verdict", "id", "node_ids", "implementation_id", "runner_id", "registered_role", "fresh_processes", "evaluation", "terminal_count"}:
        raise AuthorityError("unexpected bound-row key")
    path = root / str(row["path"])
    if path.is_symlink() or not path.is_file():
        raise AuthorityError(f"missing bound path: {row['path']}")
    raw = path.read_bytes()
    if len(raw) != int(row["bytes"]) or sha256_bytes(raw) != str(row["sha256"]):
        raise AuthorityError(f"bound path drift: {row['path']}")


def _canonical_review(root: Path, row: Mapping[str, Any], kind: str) -> dict[str, Any]:
    path = root / str(row["path"])
    raw = path.read_bytes()
    if len(raw) != int(row["bytes"]) or sha256_bytes(raw) != str(row["sha256"]):
        raise AuthorityError(f"{kind} review hash drift")
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique_pairs,
        parse_constant=_reject_constant,
    )
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise AuthorityError(f"{kind} review is not canonical")
    _require_exact_keys(value, REVIEW_KEYS, f"{kind} review")
    expected_schema, expected_verdict = REVIEW_EXPECTATIONS[kind]
    if value.get("schema") != expected_schema or value.get("verdict") != expected_verdict:
        raise AuthorityError(f"wrong exact {kind} review verdict")
    return value


def verify_authority(
    authority_path: Path,
    authority_sha256: str,
    contract_path: Path,
    contract_sha256: str,
    requested_runner: str,
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    if requested_runner != RUNNER_ID:
        raise AuthorityError("wrong runner id")
    root = _repo_root()
    if authority_path.is_symlink() or contract_path.is_symlink():
        raise AuthorityError("symlink authority inputs are forbidden")
    authority_resolved = authority_path.resolve(strict=True)
    if any(_is_within(authority_resolved, item) for item in _worktree_roots(root)):
        raise AuthorityError("authority record must be outside every Git worktree")
    contract_resolved = contract_path.resolve(strict=True)
    if contract_resolved != (root / COMMIT3_PATHS[0]).resolve():
        raise AuthorityError("contract path is not the committed Q1S contract")

    authority, authority_raw = _load_canonical(authority_resolved, authority_sha256)
    contract, contract_raw = _load_canonical(contract_resolved, contract_sha256)
    _require_exact_keys(authority, AUTHORITY_KEYS, "execution authority")
    _require_exact_keys(contract, CONTRACT_KEYS, "execution contract")
    if authority["schema"] != AUTHORITY_SCHEMA or contract["schema"] != CONTRACT_SCHEMA:
        raise AuthorityError("wrong authority or contract schema")
    for value in (authority, contract):
        if value["candidate_id"] != CANDIDATE_ID or value["study_id"] != STUDY_ID:
            raise AuthorityError("program identity mismatch")
    if authority["authorization"] != AUTHORIZATION:
        raise AuthorityError("wrong authority token")
    if authority["execution_contract_sha256"] != sha256_bytes(contract_raw):
        raise AuthorityError("authority does not bind contract")

    authz = contract["authorization"]
    _require_exact_keys(
        authz,
        {
            "token",
            "commit3_subject",
            "commit3_path_count",
            "commit3_paths",
            "external_authority_schema",
            "external_authority_exact_keys",
        },
        "contract authorization",
    )
    if authz != {
        "token": AUTHORIZATION,
        "commit3_subject": COMMIT3_SUBJECT,
        "commit3_path_count": 3,
        "commit3_paths": COMMIT3_PATHS,
        "external_authority_schema": AUTHORITY_SCHEMA,
        "external_authority_exact_keys": sorted(AUTHORITY_KEYS),
    }:
        raise AuthorityError("wrong contract authorization")

    head = _run_git(root, "rev-parse", "HEAD")
    tree = _run_git(root, "rev-parse", "HEAD^{tree}")
    subject = _run_git(root, "show", "-s", "--format=%s", "HEAD")
    if authority["commit"] != head or authority["tree"] != tree or subject != COMMIT3_SUBJECT:
        raise AuthorityError("HEAD is not the caller-bound Commit 3")
    commit2 = _run_git(root, "rev-parse", "HEAD^")
    commit1 = _run_git(root, "rev-parse", "HEAD^^")
    if _run_git(root, "rev-list", "--parents", "-n", "1", "HEAD").split() != [head, commit2]:
        raise AuthorityError("Commit 3 must have one parent")
    if _run_git(root, "rev-parse", "HEAD^^^") != Q1R_CLOSEOUT:
        raise AuthorityError("wrong Q1S ancestry")
    if _run_git(root, "show", "-s", "--format=%s", commit2) != COMMIT2_SUBJECT:
        raise AuthorityError("wrong Commit 2 subject")
    if _run_git(root, "show", "-s", "--format=%s", commit1) != COMMIT1_SUBJECT:
        raise AuthorityError("wrong Commit 1 subject")

    ancestry = contract["commit_ancestry"]
    _require_exact_keys(ancestry, {"commit1", "commit2"}, "commit ancestry")
    for name, expected_commit, expected_parent, expected_subject in (
        ("commit1", commit1, Q1R_CLOSEOUT, COMMIT1_SUBJECT),
        ("commit2", commit2, commit1, COMMIT2_SUBJECT),
    ):
        row = ancestry[name]
        _require_exact_keys(row, {"commit", "tree", "parent", "subject", "path_count", "paths"}, name)
        if row["commit"] != expected_commit or row["parent"] != expected_parent or row["subject"] != expected_subject:
            raise AuthorityError(f"wrong {name} binding")
        if row["tree"] != _run_git(root, "rev-parse", f"{expected_commit}^{{tree}}"):
            raise AuthorityError(f"wrong {name} tree")
        actual = sorted(
            line
            for line in _run_git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", expected_commit).splitlines()
            if line
        )
        if actual != sorted(row["paths"]) or len(actual) != int(row["path_count"]):
            raise AuthorityError(f"wrong exact {name} path extent")
    actual_commit3 = sorted(
        line
        for line in _run_git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").splitlines()
        if line
    )
    if actual_commit3 != sorted(COMMIT3_PATHS):
        raise AuthorityError("wrong exact Commit 3 path extent")

    if subprocess.run(["git", "diff", "--quiet"], cwd=root, check=False).returncode:
        raise AuthorityError("tracked worktree is dirty")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=root, check=False).returncode:
        raise AuthorityError("index is dirty")

    plan_inputs = contract["plan_inputs"]
    inherited_inputs = contract["inherited_inputs"]
    _require_exact_keys(plan_inputs, {"count", "rows"}, "plan inputs")
    _require_exact_keys(inherited_inputs, {"count", "rows"}, "inherited inputs")
    if len(plan_inputs["rows"]) != int(plan_inputs["count"]) or int(plan_inputs["count"]) != 11:
        raise AuthorityError("wrong plan input count")
    if len(inherited_inputs["rows"]) != int(inherited_inputs["count"]) or int(inherited_inputs["count"]) != 23:
        raise AuthorityError("wrong inherited input count")
    for row in plan_inputs["rows"]:
        _row_path_hash(root, row)
    for row in inherited_inputs["rows"]:
        path = root / str(row["path"])
        raw = path.read_bytes()
        if len(raw) != int(row["bytes"]) or sha256_bytes(raw) != row["sha256"]:
            raise AuthorityError(f"inherited input drift: {row['path']}")
        blob = _run_git(root, "rev-parse", f"{row['source_commit']}:{row['path']}")
        if blob != row["git_blob"]:
            raise AuthorityError(f"inherited Git-object drift: {row['path']}")

    implementation = contract["implementation_inputs"]
    _require_exact_keys(
        implementation,
        {"reference", "oracle", "scientific_runner", "manifest", "implementation_review", "scientific_tests"},
        "implementation inputs",
    )
    for key in ("reference", "oracle", "scientific_runner", "manifest", "implementation_review"):
        _row_path_hash(root, implementation[key])
    if len(implementation["scientific_tests"]) != 5:
        raise AuthorityError("wrong scientific test count")
    for row in implementation["scientific_tests"]:
        _row_path_hash(root, row)

    reviews = contract["review_authorities"]
    _require_exact_keys(reviews, {"plan", "implementation", "contract"}, "review authorities")
    plan_review = _canonical_review(root, reviews["plan"], "plan")
    implementation_review = _canonical_review(root, reviews["implementation"], "implementation")
    contract_review_spec = reviews["contract"]
    if contract_review_spec != {
        "path": COMMIT3_PATHS[1],
        "schema": REVIEW_EXPECTATIONS["contract"][0],
        "verdict": REVIEW_EXPECTATIONS["contract"][1],
        "hash_binding": "EXTERNAL_AUTHORITY_RECORD",
    }:
        raise AuthorityError("wrong non-self-referential contract review specification")
    contract_review_path = root / COMMIT3_PATHS[1]
    contract_review_raw = contract_review_path.read_bytes()
    contract_review = json.loads(
        contract_review_raw.decode("utf-8"),
        object_pairs_hook=_unique_pairs,
        parse_constant=_reject_constant,
    )
    if contract_review_raw != canonical_bytes(contract_review):
        raise AuthorityError("contract review is not canonical")
    _require_exact_keys(contract_review, REVIEW_KEYS, "contract review")
    if contract_review.get("schema") != REVIEW_EXPECTATIONS["contract"][0] or contract_review.get("verdict") != REVIEW_EXPECTATIONS["contract"][1]:
        raise AuthorityError("wrong exact contract review verdict")
    if authority["plan_review_sha256"] != sha256_bytes((root / reviews["plan"]["path"]).read_bytes()):
        raise AuthorityError("authority does not bind plan review")
    if authority["implementation_review_sha256"] != sha256_bytes((root / reviews["implementation"]["path"]).read_bytes()):
        raise AuthorityError("authority does not bind implementation review")
    if authority["contract_review_sha256"] != sha256_bytes(contract_review_raw):
        raise AuthorityError("authority does not bind contract review")
    verdicts = {
        "plan": plan_review["verdict"],
        "implementation": implementation_review["verdict"],
        "contract": contract_review["verdict"],
    }
    if authority["review_verdicts"] != verdicts:
        raise AuthorityError("authority review-verdict map mismatch")

    runner_inventory = contract["runner_inventory"]
    _require_exact_keys(runner_inventory, {"count", "rows"}, "runner inventory")
    if int(runner_inventory["count"]) != 3 or len(runner_inventory["rows"]) != 3:
        raise AuthorityError("wrong runner inventory")
    expected_runners = [
        {
            "fresh_processes": 2,
            "id": "REFERENCE_RUNNER",
            "path": "docs/reference_cases/e4_pl_q1s_reference.py",
            "registered_role": "REFERENCE_CERTIFICATE",
        },
        {
            "fresh_processes": 2,
            "id": "ORACLE_RUNNER",
            "path": "docs/reference_cases/e4_pl_q1s_oracle.py",
            "registered_role": "ORACLE_CERTIFICATE",
        },
        {
            "fresh_processes": 1,
            "id": "SCIENTIFIC_TEST_RUNNER",
            "path": "docs/reference_cases/e4_pl_q1s_scientific_test_runner.py",
            "registered_role": "EXACT_FIVE_NODE_PYTEST_INVENTORY",
        },
    ]
    if runner_inventory["rows"] != expected_runners:
        raise AuthorityError("runner inventory details drifted")
    runner_ids = [row["id"] for row in runner_inventory["rows"]]
    if authority["runner_ids"] != runner_ids or RUNNER_ID not in runner_ids:
        raise AuthorityError("runner is not caller-authorized")

    scientific = contract["scientific_inventory"]
    if scientific != {"count": 5, "node_ids": NODE_IDS, "inventories_separate": True}:
        raise AuthorityError("wrong scientific inventory")
    runtime = contract["runtime"]
    expected_runtime = {
        "environment": {
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "PYTHONHASHSEED": "0",
        },
        "mpmath": "FORBIDDEN",
        "numpy_for_categorical_evidence": "FORBIDDEN",
        "precision_bits": [256, 512, 1024],
        "python_executable_observed_diagnostic": "C:\\Python\\Python313\\python.exe",
        "python_executable_path_authority": "DIAGNOSTIC_ONLY",
        "python_implementation": "CPython",
        "python_version": "3.13.9",
        "standard_library_only": True,
        "sympy": "FORBIDDEN",
    }
    if runtime != expected_runtime:
        raise AuthorityError("wrong runtime authority")
    if platform.python_implementation() != "CPython" or platform.python_version() != "3.13.9":
        raise AuthorityError("active runtime mismatch")
    if runtime.get("standard_library_only") is not True:
        raise AuthorityError("numeric runtime is not standard-library-only")

    agreement = contract["agreement"]
    if agreement != {
        "cross_implementation": "BYTE_IDENTICAL_CANONICAL_CERTIFICATE_PAYLOAD",
        "payload_schema": "anysolver.s4.e4-pl-q1s-certificate-payload-v1",
        "within_oracle_fresh_processes": 2,
        "within_reference_fresh_processes": 2,
        "wrapper_schema": "anysolver.s4.e4-pl-q1s-certificate-wrapper-v1",
    }:
        raise AuthorityError("agreement contract drift")
    terminal = contract["terminal_authority"]
    _require_exact_keys(
        terminal,
        {"path", "bytes", "sha256", "schema", "evaluation", "terminal_count"},
        "terminal authority",
    )
    _row_path_hash(root, terminal)
    if terminal["schema"] != "anysolver.s4.e4-pl-q1s-terminal-table-v1" or terminal["evaluation"] != "FIRST_MATCH_IN_ASCENDING_PRECEDENCE_WINS" or terminal["terminal_count"] != 12:
        raise AuthorityError("terminal authority drift")

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

    production = contract["production_restriction"]
    if production != {
        "production": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "q1b_execution": "UNAUTHORIZED",
        "legacy_default": "ShellElement",
        "post_execution_source_changes": "FORBIDDEN_REQUIRES_NEW_SUCCESSOR",
    }:
        raise AuthorityError("production restriction drift")
    return root, authority, contract


def _execute_pytest(root: Path, authority_sha256: str, contract_sha256: str) -> dict[str, Any]:
    temp_root = Path(tempfile.mkdtemp(prefix="anysolver-q1s-scientific-"))
    basetemp = temp_root / "pytest"
    env = os.environ.copy()
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
    stdout = completed.stdout
    stderr = completed.stderr
    summary = (stdout + b"\n" + stderr).decode("utf-8", errors="replace")
    if completed.returncode != 0:
        raise AuthorityError("guarded scientific inventory failed")
    if re.search(r"\b(skipped|xfailed|xpassed)\b", summary, flags=re.IGNORECASE):
        raise AuthorityError("skip/xfail/xpass is forbidden")
    if not re.search(r"\b5 passed\b", summary):
        raise AuthorityError("scientific inventory did not report exactly five passes")
    return {
        "authority_sha256": authority_sha256.upper(),
        "candidate_id": CANDIDATE_ID,
        "contract_sha256": contract_sha256.upper(),
        "node_count": 5,
        "node_ids": NODE_IDS,
        "pytest_result": "5_PASSED_NO_SKIP_XFAIL_XPASS",
        "returncode": completed.returncode,
        "runner_id": RUNNER_ID,
        "schema": RESULT_SCHEMA,
        "stderr_sha256": sha256_bytes(stderr),
        "stdout_sha256": sha256_bytes(stdout),
        "study_id": STUDY_ID,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authority-record", required=True, type=Path)
    parser.add_argument("--authority-sha256", required=True)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--runner-id", required=True)
    parser.add_argument("--authority-check-only", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        root, authority, contract = verify_authority(
            args.authority_record,
            args.authority_sha256,
            args.contract,
            args.contract_sha256,
            args.runner_id,
        )
        if args.authority_check_only:
            result: dict[str, Any] = {
                "authority_commit": authority["commit"],
                "candidate_id": CANDIDATE_ID,
                "contract_sha256": args.contract_sha256.upper(),
                "runner_id": RUNNER_ID,
                "schema": "anysolver.s4.e4-pl-q1s-runner-authority-check-v1",
                "status": "AUTHORIZED_NO_MECHANICS_RUN",
                "study_id": STUDY_ID,
            }
        else:
            result = _execute_pytest(root, args.authority_sha256, args.contract_sha256)
        sys.stdout.buffer.write(canonical_bytes(result))
        return 0
    except (AuthorityError, OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"BLOCKED_E4_PL_Q1S_CONTRACT_OR_NONDETERMINISM: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
