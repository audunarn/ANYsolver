#!/usr/bin/env python3
"""Pipelined bounded coordinator for Q1Z support/KKT proofs."""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Sequence

from e4_pl_q1w_bounded_runner import ProcessResult, run_bounded_process
from e4_pl_q1z_common import (
    AGGREGATE_SCHEMA,
    CHECK_SCHEMA,
    GEOMETRY_IDS,
    Q1ZError,
    canonical_bytes,
    sha256,
    validate_contract,
    validate_environment,
    write_exclusive,
)


class WeightedAdmission:
    """Atomic weighted admission; one checker pair consumes two slots."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self._available = capacity
        self._condition = threading.Condition()

    @contextmanager
    def hold(self, weight: int) -> Iterator[None]:
        if weight <= 0 or weight > self.capacity:
            raise ValueError("invalid admission weight")
        with self._condition:
            while self._available < weight:
                self._condition.wait()
            self._available -= weight
        try:
            yield
        finally:
            with self._condition:
                self._available += weight
                self._condition.notify_all()


def _environment() -> dict[str, str]:
    environment = dict(os.environ)
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        environment[name] = "1"
    environment["PYTHONHASHSEED"] = "0"
    return environment


def _remaining(deadline: float) -> float:
    return max(0.05, min(180.0, deadline - time.monotonic()))


def _blocked(stdout: Path, stderr: Path) -> ProcessResult:
    return ProcessResult(
        status="TIMEOUT",
        returncode=None,
        elapsed_ms=0,
        peak_rss_bytes=None,
        stdout_path=stdout.name,
        stderr_path=stderr.name,
    )


def _discard(path: Path, result: ProcessResult) -> None:
    if result.status != "COMPLETE" and path.is_file():
        path.unlink()


def select_terminal(
    contract: dict[str, Any], *, blocked: bool, support: bool, kkt: bool, covariance: bool
) -> str:
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


def execute_bounded(
    *,
    repository_root: Path,
    contract_path: Path,
    contract_sha256: str,
    q1y3_evidence_root: Path,
    environment_root: Path,
    producer_path: Path,
    checker_path: Path,
    output_directory: Path,
    cycle_id: str,
) -> dict[str, Any]:
    contract = validate_contract(repository_root, contract_path, contract_sha256)
    validate_environment(repository_root, environment_root, contract)
    evidence_root = q1y3_evidence_root.resolve(strict=True)
    producer = producer_path.resolve(strict=True)
    checker = checker_path.resolve(strict=True)
    if any(path.is_symlink() or not path.is_file() for path in (producer, checker)):
        raise Q1ZError("producer/checker must be regular nonsymlink files")
    output_directory.mkdir(parents=False, exist_ok=False)
    deadline = time.monotonic() + 300.0
    admission = WeightedAdmission(8)
    environment = _environment()
    memory = 8 * 1024**3

    def producer_job(geometry_id: str) -> tuple[str, ProcessResult, Path]:
        proof = output_directory / f"{geometry_id}.support-proof.json"
        stdout = output_directory / f"{geometry_id}.producer.stdout.log"
        stderr = output_directory / f"{geometry_id}.producer.progress.jsonl"
        with admission.hold(1):
            if time.monotonic() >= deadline:
                return geometry_id, _blocked(stdout, stderr), proof
            result = run_bounded_process(
                [
                    sys.executable,
                    str(producer),
                    "--emit-support-proof",
                    "--repository-root",
                    str(repository_root),
                    "--contract",
                    str(contract_path),
                    "--contract-sha256",
                    contract_sha256,
                    "--q1y3-evidence-root",
                    str(evidence_root),
                    "--geometry-id",
                    geometry_id,
                    "--output",
                    str(proof),
                ],
                cwd=repository_root,
                environment=environment,
                stdout_path=stdout,
                stderr_path=stderr,
                timeout_seconds=_remaining(deadline),
                memory_limit_bytes=memory,
            )
        _discard(proof, result)
        return geometry_id, result, proof

    def checker_pair_job(
        geometry_id: str, proof: Path
    ) -> tuple[str, list[tuple[int, ProcessResult, Path]]]:
        def replica_job(replica: int) -> tuple[int, ProcessResult, Path]:
            output = output_directory / f"{geometry_id}.check{replica}.json"
            stdout = output_directory / f"{geometry_id}.check{replica}.stdout.log"
            stderr = output_directory / f"{geometry_id}.check{replica}.stderr.log"
            if time.monotonic() >= deadline:
                return replica, _blocked(stdout, stderr), output
            result = run_bounded_process(
                [
                    sys.executable,
                    str(checker),
                    "--verify-support-proof",
                    "--repository-root",
                    str(repository_root),
                    "--contract",
                    str(contract_path),
                    "--contract-sha256",
                    contract_sha256,
                    "--q1y3-evidence-root",
                    str(evidence_root),
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
                timeout_seconds=_remaining(deadline),
                memory_limit_bytes=memory,
            )
            _discard(output, result)
            return replica, result, output

        with admission.hold(2):
            with ThreadPoolExecutor(max_workers=2) as replicas:
                values = [replicas.submit(replica_job, replica) for replica in (1, 2)]
                rows = [future.result() for future in values]
        return geometry_id, sorted(rows)

    producers: dict[str, tuple[ProcessResult, Path]] = {}
    checker_futures: dict[str, Future[tuple[str, list[tuple[int, ProcessResult, Path]]]]] = {}
    with ThreadPoolExecutor(max_workers=7) as producer_pool, ThreadPoolExecutor(max_workers=2) as checker_pool:
        producer_futures = [producer_pool.submit(producer_job, geometry_id) for geometry_id in GEOMETRY_IDS]
        for future in as_completed(producer_futures):
            geometry_id, result, proof = future.result()
            producers[geometry_id] = (result, proof)
            if result.status == "COMPLETE" and proof.is_file():
                checker_futures[geometry_id] = checker_pool.submit(checker_pair_job, geometry_id, proof)
        checker_results = {
            geometry_id: future.result()[1] for geometry_id, future in checker_futures.items()
        }

    blocked = False
    support = False
    kkt = False
    covariance = False
    q3_global = False
    shards: list[dict[str, Any]] = []
    for geometry_id in GEOMETRY_IDS:
        producer_result, proof = producers[geometry_id]
        checks = checker_results.get(geometry_id, [])
        complete = producer_result.status == "COMPLETE" and proof.is_file() and len(checks) == 2
        if complete:
            complete = all(result.status == "COMPLETE" and path.is_file() for _, result, path in checks)
        raw_checks = [path.read_bytes() for _, _, path in checks] if complete else []
        if complete:
            complete = raw_checks[0] == raw_checks[1]
        check: dict[str, Any] = {}
        if complete:
            check = json.loads(raw_checks[0])
            complete = (
                isinstance(check, dict)
                and set(check)
                == {
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
                and check.get("schema") == CHECK_SCHEMA
                and check.get("geometry_id") == geometry_id
                and check.get("base_support_system_count") == 1
                and check.get("case_count") == 8
            )
        blocked = blocked or not complete
        if complete:
            blocked = blocked or bool(check["proof_disagreement"])
            support = support or bool(check["exact_support_boundary_contradictions"])
            kkt = kkt or bool(check["exact_kkt_reaction_contradictions"])
            covariance = covariance or bool(check["exact_support_covariance_contradictions"])
            if geometry_id == "Q3_TAPERED_SKEW_RSTAR_TRANSLATED":
                q3_global = bool(check["proper_global_exact"])
        shards.append(
            {
                "case_count": int(check.get("case_count", 0)),
                "checker_byte_identical": bool(complete),
                "checker_sha256": sha256(raw_checks[0]) if complete else "",
                "checker_statuses": [result.status for _, result, _ in checks],
                "geometry_id": geometry_id,
                "kkt_reaction_contradiction": bool(check.get("exact_kkt_reaction_contradictions", [])),
                "producer_status": producer_result.status,
                "proof_disagreement": bool(check.get("proof_disagreement", False)),
                "proof_sha256": sha256(proof.read_bytes()) if proof.is_file() else "",
                "support_boundary_contradiction": bool(
                    check.get("exact_support_boundary_contradictions", [])
                ),
                "support_covariance_contradiction": bool(
                    check.get("exact_support_covariance_contradictions", [])
                ),
            }
        )
    covariance = covariance or (not blocked and not q3_global)
    terminal = select_terminal(
        contract, blocked=blocked, support=support, kkt=kkt, covariance=covariance
    )
    return {
        "candidate_id": contract["candidate_id"],
        "contract_sha256": contract_sha256.upper(),
        "coverage": {
            "case_count": sum(row["case_count"] for row in shards) if not blocked else 0,
            "geometry_count": sum(row["checker_byte_identical"] for row in shards) if not blocked else 0,
            "kkt_dimension": 44 if not blocked else 0,
            "physical_support_rows": 20 if not blocked else 0,
        },
        "cycle_id": cycle_id,
        "kkt_reaction_contradiction": kkt,
        "production": contract["production"],
        "q1b_execution": contract["q1b_execution"],
        "q3_proper_global_support_identity": q3_global,
        "schema": AGGREGATE_SCHEMA,
        "shards": shards,
        "study_id": contract["study_id"],
        "support_boundary_contradiction": support,
        "support_covariance_contradiction": covariance,
        "terminal": terminal,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-bounded-support-kkt", action="store_true", required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--q1y3-evidence-root", type=Path, required=True)
    parser.add_argument("--environment-root", type=Path, required=True)
    parser.add_argument("--producer", type=Path, required=True)
    parser.add_argument("--checker", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cycle-id", required=True)
    parser.add_argument("--workers", type=int, default=7)
    parser.add_argument("--checker-workers", type=int, default=4)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument("--memory-limit-gib", type=int, default=8)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if (args.workers, args.checker_workers, args.timeout_seconds, args.memory_limit_gib) != (7, 4, 300, 8):
        print("formal Q1Z controls are frozen", file=sys.stderr)
        return 2
    try:
        value = execute_bounded(
            repository_root=args.repository_root.resolve(strict=True),
            contract_path=args.contract,
            contract_sha256=args.contract_sha256,
            q1y3_evidence_root=args.q1y3_evidence_root,
            environment_root=args.environment_root,
            producer_path=args.producer,
            checker_path=args.checker,
            output_directory=args.output_directory,
            cycle_id=args.cycle_id,
        )
        write_exclusive(args.output, canonical_bytes(value))
        return 0
    except (OSError, TypeError, ValueError, Q1ZError) as exc:
        print(f"BLOCKED_E4_PL_Q1Z_PROOF_OR_REVIEW: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
