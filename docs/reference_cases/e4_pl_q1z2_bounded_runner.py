#!/usr/bin/env python3
"""Run the two missing Q1Z Q3-star checker replicas and compose 56 cases."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Sequence

from e4_pl_q1w_bounded_runner import ProcessResult, run_bounded_process
from e4_pl_q1z_common import (
    CHECK_SCHEMA,
    Q1ZError,
    canonical_bytes,
    read_json,
    sha256,
    validate_contract as validate_q1z_contract,
    validate_environment,
    verify_file,
    write_exclusive,
)


CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1z2-completion-contract-v1"
AGGREGATE_SCHEMA = "anysolver.s4.e4-pl-q1z2-completion-result-v1"
GEOMETRY_ID = "Q3_TAPERED_SKEW_RSTAR_TRANSLATED"
CHECK_KEYS = {
    "base_support_system_count",
    "case_count",
    "exact_kkt_reaction_contradictions",
    "exact_support_boundary_contradictions",
    "exact_support_covariance_contradictions",
    "geometry_id",
    "proper_global_exact",
    "proof_disagreement",
    "schema",
    "support_proof_sha256",
}


def _keys(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise Q1ZError(f"{label} exact-key mismatch")
    return value


def validate_completion_contract(root: Path, path: Path, caller_sha256: str) -> dict[str, Any]:
    raw, value = read_json(path)
    if sha256(raw) != caller_sha256.upper() or raw != canonical_bytes(value):
        raise Q1ZError("Q1Z2 contract identity mismatch")
    contract = _keys(
        value,
        {
            "base_commit",
            "candidate_id",
            "coverage",
            "frozen_repository_inputs",
            "parallelism",
            "predecessor_checker_pairs",
            "production",
            "q1b_execution",
            "q1z_contract_sha256",
            "q1z_predecessor_aggregate",
            "q3star_proof",
            "schema",
            "scope",
            "study_id",
            "terminals",
        },
        "Q1Z2 contract",
    )
    if contract["schema"] != CONTRACT_SCHEMA or contract["base_commit"] != "d325ea8f787509a056b51aa21b07107a40bdfae0":
        raise Q1ZError("Q1Z2 contract authority mismatch")
    if contract["coverage"] != {
        "composed_numbering_cases": 56,
        "new_numbering_cases": 8,
        "predecessor_numbering_cases": 48,
        "q3star_checker_replicas": 2,
    }:
        raise Q1ZError("Q1Z2 coverage mismatch")
    if contract["parallelism"] != {
        "global_timeout_seconds": 210,
        "memory_limit_gib_per_process": 8,
        "numerical_threads_per_process": 1,
        "replicas": 2,
        "timeout_seconds_per_process": 180,
    }:
        raise Q1ZError("Q1Z2 process policy mismatch")
    if contract["scope"] != {
        "full_local_qualification": False,
        "producer_execution": False,
        "q1b_authorized": False,
        "q3star_support_completion": True,
    }:
        raise Q1ZError("Q1Z2 scope mismatch")
    if contract["production"] != "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED" or contract["q1b_execution"] != "UNAUTHORIZED":
        raise Q1ZError("Q1Z2 production boundary mismatch")
    repository = root.resolve(strict=True)
    rows = contract["frozen_repository_inputs"]
    if not isinstance(rows, list) or len(rows) != 4:
        raise Q1ZError("Q1Z2 repository inventory mismatch")
    for row in rows:
        _keys(row, {"bytes", "path", "sha256"}, "Q1Z2 repository row")
        verify_file(repository / row["path"], size=int(row["bytes"]), digest=str(row["sha256"]))
    pairs = contract["predecessor_checker_pairs"]
    if not isinstance(pairs, list) or len(pairs) != 6:
        raise Q1ZError("Q1Z predecessor checker inventory mismatch")
    return contract


def _validate_predecessor(root: Path, contract: dict[str, Any]) -> None:
    result_path = root / "docs/reference_cases/e4_pl_q1z_bounded_result.json"
    raw, result = read_json(result_path)
    expected = contract["q1z_predecessor_aggregate"]
    if len(raw) != expected["bytes"] or sha256(raw) != expected["sha256"]:
        raise Q1ZError("Q1Z predecessor aggregate mismatch")
    complete = result.get("shards", [])[:6]
    if len(complete) != 6 or any(not row.get("checker_byte_identical") for row in complete):
        raise Q1ZError("Q1Z predecessor coverage mismatch")
    if any(
        row.get(key)
        for row in complete
        for key in (
            "support_boundary_contradiction",
            "kkt_reaction_contradiction",
            "support_covariance_contradiction",
            "proof_disagreement",
        )
    ):
        raise Q1ZError("Q1Z predecessor contradiction/disagreement")


def _validate_external(root: Path, contract: dict[str, Any]) -> Path:
    evidence = root.resolve(strict=True)
    if evidence.is_symlink() or not evidence.is_dir():
        raise Q1ZError("Q1Z evidence root must be a nonsymlink directory")
    for row in contract["predecessor_checker_pairs"]:
        _keys(row, {"bytes", "filenames", "geometry_id", "sha256"}, "checker pair row")
        names = row["filenames"]
        if not isinstance(names, list) or len(names) != 2:
            raise Q1ZError("checker pair filenames mismatch")
        values = []
        for name in names:
            path = evidence / name
            verify_file(path, size=int(row["bytes"]), digest=str(row["sha256"]))
            values.append(path.read_bytes())
        if values[0] != values[1]:
            raise Q1ZError("predecessor checker replicas differ")
        check = json.loads(values[0])
        if (
            set(check) != CHECK_KEYS
            or check["schema"] != CHECK_SCHEMA
            or check["geometry_id"] != row["geometry_id"]
            or check["case_count"] != 8
            or check["base_support_system_count"] != 1
            or check["proof_disagreement"]
            or check["exact_support_boundary_contradictions"]
            or check["exact_kkt_reaction_contradictions"]
            or check["exact_support_covariance_contradictions"]
        ):
            raise Q1ZError("predecessor checker content mismatch")
    proof_row = contract["q3star_proof"]
    _keys(proof_row, {"bytes", "filename", "geometry_id", "payload_sha256", "sha256"}, "Q3-star proof row")
    proof = evidence / proof_row["filename"]
    verify_file(proof, size=int(proof_row["bytes"]), digest=str(proof_row["sha256"]))
    _, wrapper = read_json(proof)
    if wrapper.get("geometry_id") != GEOMETRY_ID or wrapper.get("proof_sha256") != proof_row["payload_sha256"]:
        raise Q1ZError("Q3-star proof payload authority mismatch")
    return proof


def _environment() -> dict[str, str]:
    value = dict(os.environ)
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        value[name] = "1"
    value["PYTHONHASHSEED"] = "0"
    return value


def select_terminal(contract: dict[str, Any], *, blocked: bool, support: bool, kkt: bool, covariance: bool) -> str:
    terminals = contract["terminals"]
    if blocked:
        return terminals["blocked"]
    if support:
        return terminals["support_boundary"]
    if kkt:
        return terminals["kkt_reaction"]
    if covariance:
        return terminals["support_covariance"]
    return terminals["success"]


def execute_completion(
    *,
    repository_root: Path,
    contract_path: Path,
    contract_sha256: str,
    q1z_evidence_root: Path,
    q1y3_evidence_root: Path,
    environment_root: Path,
    output_directory: Path,
) -> dict[str, Any]:
    contract = validate_completion_contract(repository_root, contract_path, contract_sha256)
    _validate_predecessor(repository_root, contract)
    proof = _validate_external(q1z_evidence_root, contract)
    q1z_contract_path = repository_root / "docs/reference_cases/e4_pl_q1z_support_contract.json"
    q1z_contract = validate_q1z_contract(repository_root, q1z_contract_path, contract["q1z_contract_sha256"])
    validate_environment(repository_root, environment_root, q1z_contract)
    checker = repository_root / "docs/reference_cases/e4_pl_q1z_support_checker.py"
    checker.resolve(strict=True)
    output_directory.mkdir(parents=False, exist_ok=False)
    deadline = time.monotonic() + 210.0
    environment = _environment()

    def replica(replica_id: int) -> tuple[int, ProcessResult, Path]:
        directory = output_directory / f"replica{replica_id}"
        directory.mkdir(exist_ok=False)
        output = directory / "q3star.check.json"
        stdout = directory / "stdout.log"
        stderr = directory / "stderr.log"
        timeout = max(0.05, min(180.0, deadline - time.monotonic()))
        result = run_bounded_process(
            [
                sys.executable,
                str(checker),
                "--verify-support-proof",
                "--repository-root",
                str(repository_root),
                "--contract",
                str(q1z_contract_path),
                "--contract-sha256",
                contract["q1z_contract_sha256"],
                "--q1y3-evidence-root",
                str(q1y3_evidence_root),
                "--proof",
                str(proof),
                "--environment-root",
                str(environment_root),
                "--output",
                str(output),
            ],
            cwd=repository_root,
            environment=environment,
            stdout_path=stdout,
            stderr_path=stderr,
            timeout_seconds=timeout,
            memory_limit_bytes=8 * 1024**3,
        )
        if result.status != "COMPLETE" and output.is_file():
            output.unlink()
        return replica_id, result, output

    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = sorted(future.result() for future in [pool.submit(replica, index) for index in (1, 2)])
    complete = all(result.status == "COMPLETE" and output.is_file() for _, result, output in rows)
    raw = [output.read_bytes() for _, _, output in rows] if complete else []
    byte_identical = complete and raw[0] == raw[1]
    check: dict[str, Any] = {}
    if byte_identical:
        check = json.loads(raw[0])
        byte_identical = (
            set(check) == CHECK_KEYS
            and check.get("schema") == CHECK_SCHEMA
            and check.get("geometry_id") == GEOMETRY_ID
            and check.get("base_support_system_count") == 1
            and check.get("case_count") == 8
            and check.get("support_proof_sha256") == contract["q3star_proof"]["payload_sha256"]
        )
    blocked = not byte_identical or bool(check.get("proof_disagreement", False))
    support = bool(check.get("exact_support_boundary_contradictions", []))
    kkt = bool(check.get("exact_kkt_reaction_contradictions", []))
    covariance = bool(check.get("exact_support_covariance_contradictions", [])) or (
        not blocked and not bool(check.get("proper_global_exact", False))
    )
    terminal = select_terminal(contract, blocked=blocked, support=support, kkt=kkt, covariance=covariance)
    return {
        "candidate_id": contract["candidate_id"],
        "checker_byte_identical": byte_identical,
        "checker_sha256": sha256(raw[0]) if byte_identical else "",
        "checker_statuses": [result.status for _, result, _ in rows],
        "contract_sha256": contract_sha256.upper(),
        "coverage": {
            "case_count": 56 if not blocked else 0,
            "geometry_count": 7 if not blocked else 0,
            "new_case_count": 8 if not blocked else 0,
            "predecessor_case_count": 48 if not blocked else 0,
        },
        "kkt_reaction_contradiction": kkt,
        "predecessor_aggregate_sha256": contract["q1z_predecessor_aggregate"]["sha256"],
        "production": contract["production"],
        "q1b_execution": contract["q1b_execution"],
        "q3star_proof_sha256": contract["q3star_proof"]["sha256"],
        "q3star_proper_global_support_identity": bool(check.get("proper_global_exact", False)),
        "schema": AGGREGATE_SCHEMA,
        "study_id": contract["study_id"],
        "support_boundary_contradiction": support,
        "support_covariance_contradiction": covariance,
        "terminal": terminal,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-q3star-support-completion", action="store_true", required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--q1z-evidence-root", type=Path, required=True)
    parser.add_argument("--q1y3-evidence-root", type=Path, required=True)
    parser.add_argument("--environment-root", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replicas", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--global-timeout-seconds", type=int, default=210)
    parser.add_argument("--memory-limit-gib", type=int, default=8)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if (args.replicas, args.timeout_seconds, args.global_timeout_seconds, args.memory_limit_gib) != (2, 180, 210, 8):
        print("Q1Z2 process controls are frozen", file=sys.stderr)
        return 2
    try:
        value = execute_completion(
            repository_root=args.repository_root.resolve(strict=True),
            contract_path=args.contract,
            contract_sha256=args.contract_sha256,
            q1z_evidence_root=args.q1z_evidence_root,
            q1y3_evidence_root=args.q1y3_evidence_root,
            environment_root=args.environment_root,
            output_directory=args.output_directory,
        )
        write_exclusive(args.output, canonical_bytes(value))
        return 0
    except (OSError, TypeError, ValueError, Q1ZError) as exc:
        print(f"BLOCKED_E4_PL_Q1Z2_PROOF_OR_REVIEW: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
