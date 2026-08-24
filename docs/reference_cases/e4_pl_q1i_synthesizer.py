#!/usr/bin/env python3
"""Compose frozen Q1E and Q1H evidence without executing mechanics."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Sequence


BASE_COMMIT = "cf7fd051d7f6387f3167b3ae4da87969ffd9131d"
CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1i-synthesis-contract-v1"
EVIDENCE_SCHEMA = "anysolver.s4.e4-pl-q1i-synthesis-evidence-v1"
STUDY_ID = "study_e4_pl_q1i.q1e_q1h_assembled_qualification_synthesis_v1"
CANDIDATE_ID = "candidate_e4_pl_q1i.wg2020_assembled_qualification_synthesis_v1"
PRODUCTION = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
TERMINALS = [
    "BLOCKED_E4_PL_Q1I_EVIDENCE_OR_REVIEW",
    "NO_GO_E4_PL_Q1I_LOCKING_OR_SOLVER_EQUIVALENCE",
    "NO_GO_E4_PL_Q1I_STABILITY_OR_NONINTRUSION",
    "NO_GO_E4_PL_Q1I_DOMAIN_COERCIVITY",
    "UNCLASSIFIED_E4_PL_Q1I_ASSEMBLED_QUALIFICATION",
    "PROVISIONAL_GO_E4_PL_Q1I_DORMANT_IMPLEMENTATION_PLAN",
]
EXTENT = {
    "docs/agent_plans/S4_E4_PL_Q1I_ASSEMBLED_QUALIFICATION_SYNTHESIS_PLAN.md",
    "docs/reference_cases/e4_pl_q1i_status.json",
    "docs/reference_cases/e4_pl_q1i_synthesis_contract.json",
    "docs/reference_cases/e4_pl_q1i_synthesis_evidence.json",
    "docs/reference_cases/e4_pl_q1i_synthesizer.py",
    "tests/test_e4_pl_q1i_assembled_qualification.py",
}


class SynthesisError(RuntimeError):
    """Fail-closed Q1I synthesis error."""


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise SynthesisError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_json(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(SynthesisError(f"non-finite JSON: {token}")),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SynthesisError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise SynthesisError(f"noncanonical JSON: {path}")
    return raw, value


def expect(condition: bool, label: str) -> None:
    if not condition:
        raise SynthesisError(label)


def git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=root, check=False, capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode:
        raise SynthesisError(f"git {' '.join(arguments)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def validate_repository_boundary(root: Path) -> None:
    repository = root.resolve(strict=True)
    top = Path(git(repository, "rev-parse", "--show-toplevel")).resolve(strict=True)
    expect(os.path.normcase(str(top)) == os.path.normcase(str(repository)), "repository root mismatch")
    head = git(repository, "rev-parse", "HEAD")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE_COMMIT, head],
        cwd=repository, check=False, capture_output=True,
    )
    expect(ancestor.returncode == 0, "Q1H base is not an ancestor of HEAD")
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=repository, check=False, capture_output=True,
    )
    expect(status.returncode == 0, "cannot read repository status")
    dirty_tracked = False
    untracked: set[str] = set()
    for row in (entry for entry in status.stdout.split(b"\0") if entry):
        if row.startswith(b"?? "):
            path = row[3:].decode("utf-8").replace("\\", "/")
            if not path.startswith((".pytest", "docs/reference_cases/__pycache__", "tests/__pycache__")):
                untracked.add(path)
        else:
            dirty_tracked = True
    expect(not dirty_tracked, "tracked or staged worktree changes are forbidden during synthesis")
    committed = {
        path.replace("\\", "/")
        for path in git(repository, "diff", "--name-only", f"{BASE_COMMIT}..HEAD").splitlines()
        if path
    }
    expect(committed <= EXTENT and untracked <= EXTENT and not (committed & untracked), "Q1I closed-world extent mismatch")
    author_inputs = {
        "docs/agent_plans/S4_E4_PL_Q1I_ASSEMBLED_QUALIFICATION_SYNTHESIS_PLAN.md",
        "docs/reference_cases/e4_pl_q1i_synthesis_contract.json",
        "docs/reference_cases/e4_pl_q1i_synthesizer.py",
    }
    expect(
        committed | untracked in (
            author_inputs,
            author_inputs | {"docs/reference_cases/e4_pl_q1i_synthesis_evidence.json"},
            author_inputs
            | {
                "docs/reference_cases/e4_pl_q1i_synthesis_evidence.json",
                "tests/test_e4_pl_q1i_assembled_qualification.py",
            },
            EXTENT,
        ),
        "Q1I stage is incomplete or contains an unexpected path",
    )
    production = git(repository, "diff", "--name-only", BASE_COMMIT, "--", ".gitattributes", ".github", "pyproject.toml", "src")
    expect(not production, "production boundary changed")


def validate_contract(root: Path, contract_path: Path, claimed_sha256: str) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    validate_repository_boundary(root)
    raw, contract = read_json(contract_path)
    expect(sha256(raw) == claimed_sha256.upper(), "contract caller hash mismatch")
    expect(contract.get("schema") == CONTRACT_SCHEMA, "contract schema mismatch")
    expect(contract.get("base", {}).get("commit") == BASE_COMMIT, "contract base mismatch")
    expect(contract.get("candidate_id") == CANDIDATE_ID and contract.get("study_id") == STUDY_ID, "contract identity mismatch")
    expect(contract.get("production") == PRODUCTION, "contract production mismatch")
    expect(contract.get("terminals") == TERMINALS, "terminal precedence mismatch")
    expect(set(contract.get("extent", {}).get("paths", [])) == EXTENT and contract.get("extent", {}).get("path_count") == 6, "contract extent mismatch")
    rows = contract.get("inputs")
    expect(isinstance(rows, list) and len(rows) == 7, "contract input count mismatch")
    expect(len({row.get("role") for row in rows}) == 7 and len({row.get("path") for row in rows}) == 7, "duplicate contract input")
    values: dict[str, dict[str, Any]] = {}
    for row in rows:
        path = root / row["path"]
        source_raw, value = read_json(path)
        expect(len(source_raw) == row["bytes"] and sha256(source_raw) == row["sha256"], f"input identity mismatch: {path}")
        expect(value.get("schema") == row["schema"], f"input schema mismatch: {path}")
        expect(git(root, "rev-parse", f"HEAD:{row['path']}") == row["git_blob"], f"input Git blob mismatch: {path}")
        values[row["role"]] = value
    return contract, values


def recompute_q1e(root: Path, inputs: dict[str, dict[str, Any]]) -> dict[str, bool]:
    contract = inputs["Q1E_CONTRACT"]
    evidence = inputs["Q1E_EVIDENCE"]
    review = inputs["Q1E_REVIEW"]
    status = inputs["Q1E_STATUS"]
    expect(review.get("verdict") == "ACCEPT_Q1E_ASSEMBLED_READJUDICATION_NO_P0_P1" and review.get("findings") == [], "Q1E review mismatch")
    expect(status.get("terminal") == "UNCLASSIFIED_E4_PL_Q1E_DOMAIN_COERCIVITY", "Q1E terminal mismatch")
    expect(status.get("evidence_sha256") == sha256(canonical_bytes(evidence)), "Q1E status/evidence mismatch")
    cases = Path(__file__).resolve().parent
    if str(cases) not in sys.path:
        sys.path.insert(0, str(cases))
    q1e = importlib.import_module("e4_pl_q1e_synthesizer")
    raw_inputs: dict[str, dict[str, Any]] = {}
    for row in contract.get("evidence_inputs", []):
        source_raw, value = read_json(root / row["path"])
        expect(len(source_raw) == row["bytes"] and sha256(source_raw) == row["sha256"], f"Q1E underlying identity mismatch: {row['path']}")
        expect(git(root, "rev-parse", f"HEAD:{row['path']}") == row["git_blob"], f"Q1E underlying Git blob mismatch: {row['path']}")
        raw_inputs[row["role"]] = value
    gates = q1e.recompute_gates(raw_inputs)
    expect(gates == evidence.get("gates"), "Q1E gate recomputation mismatch")
    return gates


def recompute_q1h(root: Path, inputs: dict[str, dict[str, Any]]) -> dict[str, bool]:
    contract = inputs["Q1H_CONTRACT"]
    evidence = inputs["Q1H_EVIDENCE"]
    status = inputs["Q1H_STATUS"]
    expect(contract.get("alpha_star") == [1, 1_000_000], "Q1H alpha mismatch")
    expect(contract.get("production") == PRODUCTION and evidence.get("production") == PRODUCTION and status.get("production") == PRODUCTION, "Q1H production mismatch")
    for row in contract.get("inputs", []):
        source = (root / row["path"]).read_bytes()
        expect(len(source) == row["bytes"] and sha256(source) == row["sha256"], f"Q1H inherited input mismatch: {row['path']}")
    for row in evidence.get("implementation_inputs", []):
        source = (root / row["path"]).read_bytes()
        expect(len(source) == row["bytes"] and sha256(source) == row["sha256"], f"Q1H implementation input mismatch: {row['path']}")
    cycles = evidence.get("cycles", [])
    coverage = evidence.get("domain_coverage", {})
    symbolic = evidence.get("symbolic_control", {})
    kernel = evidence.get("h_kernel", {})
    expected_evidence_hash = sha256(canonical_bytes(evidence))
    expect(status.get("evidence", {}).get("sha256") == expected_evidence_hash, "Q1H status/evidence mismatch")
    return {
        "alpha_exact": coverage.get("alpha_star") == [1, 1_000_000],
        "control_invertible": symbolic == {"anchored_dimension": 18, "determinant": "32*q**12/729", "residual": "0", "status": "PASS"},
        "coverage_complete": coverage.get("coverage_complete") is True and coverage.get("pending_count") == 0 and coverage.get("unresolved_leaf_count") == 0,
        "h_kernel_exact": kernel.get("status") == "PASS" and kernel.get("factor_rigid_residual_nonzero_count") == 0 and kernel.get("rigid_range_authority") == "Q1G_ESTABLISHED_NOT_REVISITED",
        "partition_bound": coverage.get("partition_sha256") == "1365DAB7F792C1920C4F8AB10DF2E8F65395D613EFFAE5CD51E323AA4092AA00" and coverage.get("positive_leaf_count") == 3_955 and coverage.get("excluded_leaf_count") == 868,
        "two_cycle_deterministic": len(cycles) == 2 and cycles[0].get("bytes") == cycles[1].get("bytes") == 1_984_603 and cycles[0].get("sha256") == cycles[1].get("sha256") == "150975B3F362691CC2670C5CC36DE7F63430DBCA7E46576F2866C7D7B56765CF",
    }


def select_terminal(q1e: dict[str, bool], q1h: dict[str, bool]) -> str:
    locking_closed = q1e["q1b_resolved_finest_rows_below_limit"] and q1e["q1c_resolved_range_locking_closed"] and q1e["q1d_ultrathin_locking_closed"] and q1e["q1d_solver_equivalence_closed"]
    if not locking_closed:
        return TERMINALS[1]
    if not (q1e["stability_finite_samples_closed"] and q1e["nonintrusion_recovery_closed"]):
        return TERMINALS[2]
    if not all(q1h.values()):
        return TERMINALS[3]
    return TERMINALS[5]


def synthesize(root: Path, contract_path: Path, claimed_sha256: str) -> dict[str, Any]:
    contract, inputs = validate_contract(root, contract_path, claimed_sha256)
    q1e = recompute_q1e(root, inputs)
    q1h = recompute_q1h(root, inputs)
    terminal = select_terminal(q1e, q1h)
    expect(terminal == TERMINALS[5], "unexpected assembled qualification disposition")
    return {
        "authorization": "PREPARE_DORMANT_PRODUCTION_IMPLEMENTATION_AND_PARITY_PLAN_ONLY",
        "candidate_id": CANDIDATE_ID,
        "contract_sha256": claimed_sha256.upper(),
        "input_hashes": {row["role"]: row["sha256"] for row in contract["inputs"]},
        "production": PRODUCTION,
        "q1b_execution": "UNAUTHORIZED",
        "q1e_gates": q1e,
        "q1h_gates": q1h,
        "schema": EVIDENCE_SCHEMA,
        "study_id": STUDY_ID,
        "terminal": terminal,
    }


def write_exclusive(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(canonical_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthesize-assembled-qualification", action="store_true", required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        value = synthesize(args.repository_root.resolve(strict=True), args.contract, args.contract_sha256)
        write_exclusive(args.output, value)
        return 0
    except (OSError, TypeError, ValueError, SynthesisError) as exc:
        print(f"{TERMINALS[0]}: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
