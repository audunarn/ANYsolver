"""Pipelined seven-producer/four-checker coordinator for Q1Y2."""

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

import e4_pl_q1y_common as q1y
from e4_pl_q1w_bounded_runner import ProcessResult, run_bounded_process


CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1y2-local-algebra-contract-v1"
CHECK_SCHEMA = "anysolver.s4.e4-pl-q1y2-algebra-check-v1"
AGGREGATE_SCHEMA = "anysolver.s4.e4-pl-q1y2-algebra-aggregate-v1"


def validate_successor_contract(root: Path, path: Path, caller_sha256: str) -> dict[str, Any]:
    raw, contract = q1y.read_json(path)
    if q1y.sha256(raw) != caller_sha256.upper():
        raise q1y.Q1YError("successor contract caller hash mismatch")
    expected = {
        "base_commit", "candidate_id", "checker", "coverage", "diagnostic_proofs",
        "exact_environment", "frozen_inputs", "parallelism", "production",
        "q1b_execution", "schema", "scope", "study_id", "terminals",
    }
    if not isinstance(contract, dict) or set(contract) != expected or contract["schema"] != CONTRACT_SCHEMA:
        raise q1y.Q1YError("successor contract schema mismatch")
    if contract["parallelism"] != {
        "checker_workers": 4,
        "global_timeout_seconds": 600,
        "memory_admission_gib": 96,
        "memory_limit_gib_per_process": 12,
        "numerical_threads_per_process": 1,
        "producer_workers": 7,
        "replicas_per_geometry": 2,
        "weighted_process_slots": 8,
    }:
        raise q1y.Q1YError("successor process policy mismatch")
    if contract["coverage"] != {
        "base_factorizations": 7,
        "derived_numbering_cases": 56,
        "internal_fields": 38,
        "physical_dofs": 24,
        "quotient_dimension": 18,
        "rigid_modes": 6,
    }:
        raise q1y.Q1YError("successor coverage mismatch")
    if contract["production"] != "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED" or contract["q1b_execution"] != "UNAUTHORIZED":
        raise q1y.Q1YError("successor production boundary mismatch")
    if contract["scope"] != {"global_kkt": False, "q1v_rerun": False, "support_solve": False}:
        raise q1y.Q1YError("successor scope mismatch")
    rows = contract["frozen_inputs"]
    if not isinstance(rows, list) or len(rows) != 4:
        raise q1y.Q1YError("successor frozen-input count mismatch")
    repository = root.resolve(strict=True)
    for row in rows:
        if set(row) != {"bytes", "path", "sha256"}:
            raise q1y.Q1YError("successor frozen-input row mismatch")
        q1y.verify_file(repository / row["path"], size=int(row["bytes"]), digest=str(row["sha256"]))
    diagnostics = contract["diagnostic_proofs"]
    if not isinstance(diagnostics, list) or len(diagnostics) != 7:
        raise q1y.Q1YError("diagnostic inventory mismatch")
    if any(
        set(row) != {"bytes", "classification", "name", "sha256"}
        or row["classification"] != "NONCANONICAL_SCHEDULING_DIAGNOSTIC_ONLY"
        for row in diagnostics
    ):
        raise q1y.Q1YError("diagnostic disposition mismatch")
    return contract


class WeightedAdmission:
    """Atomic weighted admission; a checker replica pair consumes two slots."""

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


def discard_incomplete_output(path: Path, result: ProcessResult) -> None:
    if result.status != "COMPLETE" and path.is_file():
        path.unlink()


def select_terminal(contract: dict[str, Any], *, blocked: bool, local: bool, covariance: bool, unresolved: bool) -> str:
    terminals = contract["terminals"]
    if blocked:
        return terminals["blocked"]
    if local:
        return terminals["local_algebra"]
    if covariance:
        return terminals["operator_covariance"]
    if unresolved:
        return terminals["ordered_sign"]
    return terminals["success"]


def _environment() -> dict[str, str]:
    environment = dict(os.environ)
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        environment[name] = "1"
    environment["PYTHONHASHSEED"] = "0"
    return environment


def _remaining(deadline: float) -> float:
    return max(0.05, deadline - time.monotonic())


def _blocked_result(stdout_path: Path, stderr_path: Path) -> ProcessResult:
    return ProcessResult(
        status="TIMEOUT", returncode=None, elapsed_ms=0, peak_rss_bytes=None,
        stdout_path=stdout_path.name, stderr_path=stderr_path.name,
    )


def execute_pipelined(
    *,
    repository_root: Path,
    successor_contract_path: Path,
    successor_contract_sha256: str,
    q1y_contract_path: Path,
    q1y_contract_sha256: str,
    environment_root: Path,
    producer_path: Path,
    checker_path: Path,
    output_directory: Path,
    cycle_id: str,
) -> dict[str, Any]:
    contract = validate_successor_contract(repository_root, successor_contract_path, successor_contract_sha256)
    prior_contract = q1y.validate_contract(repository_root, q1y_contract_path, q1y_contract_sha256)
    q1y.validate_environment(repository_root, environment_root, prior_contract)
    producer = producer_path.resolve(strict=True)
    checker = checker_path.resolve(strict=True)
    if producer.is_symlink() or checker.is_symlink() or not producer.is_file() or not checker.is_file():
        raise q1y.Q1YError("producer/checker must be regular nonsymlink files")
    output_directory.mkdir(parents=False, exist_ok=False)
    started = time.monotonic()
    deadline = started + 600.0
    memory = 12 * 1024**3
    admission = WeightedAdmission(8)
    environment = _environment()

    def producer_job(geometry_id: str) -> tuple[str, ProcessResult, Path]:
        proof = output_directory / f"{geometry_id}.proof.json"
        stdout = output_directory / f"{geometry_id}.producer.stdout.log"
        stderr = output_directory / f"{geometry_id}.producer.progress.jsonl"
        with admission.hold(1):
            if time.monotonic() >= deadline:
                return geometry_id, _blocked_result(stdout, stderr), proof
            result = run_bounded_process(
                [
                    sys.executable, str(producer), "--emit-algebra-proof",
                    "--repository-root", str(repository_root),
                    "--contract", str(q1y_contract_path),
                    "--contract-sha256", q1y_contract_sha256,
                    "--geometry-id", geometry_id,
                    "--output", str(proof),
                ],
                cwd=repository_root,
                environment=environment,
                stdout_path=stdout,
                stderr_path=stderr,
                timeout_seconds=_remaining(deadline),
                memory_limit_bytes=memory,
            )
        discard_incomplete_output(proof, result)
        return geometry_id, result, proof

    def checker_pair_job(geometry_id: str, proof: Path) -> tuple[str, list[tuple[int, ProcessResult, Path]]]:
        def replica_job(replica: int) -> tuple[int, ProcessResult, Path]:
            output = output_directory / f"{geometry_id}.check{replica}.json"
            stdout = output_directory / f"{geometry_id}.check{replica}.stdout.log"
            stderr = output_directory / f"{geometry_id}.check{replica}.stderr.log"
            if time.monotonic() >= deadline:
                return replica, _blocked_result(stdout, stderr), output
            result = run_bounded_process(
                [
                    sys.executable, str(checker), "--verify-algebra-proof",
                    "--repository-root", str(repository_root),
                    "--q1y-contract", str(q1y_contract_path),
                    "--q1y-contract-sha256", q1y_contract_sha256,
                    "--successor-contract", str(successor_contract_path),
                    "--successor-contract-sha256", successor_contract_sha256,
                    "--proof", str(proof),
                    "--environment-root", str(environment_root),
                    "--output", str(output),
                ],
                cwd=repository_root,
                environment=environment,
                stdout_path=stdout,
                stderr_path=stderr,
                timeout_seconds=_remaining(deadline),
                memory_limit_bytes=memory,
            )
            discard_incomplete_output(output, result)
            return replica, result, output

        with admission.hold(2):
            with ThreadPoolExecutor(max_workers=2) as replicas:
                rows = [replicas.submit(replica_job, replica) for replica in (1, 2)]
                values = [future.result() for future in rows]
        return geometry_id, sorted(values)

    producers: dict[str, tuple[ProcessResult, Path]] = {}
    checker_futures: dict[str, Future[tuple[str, list[tuple[int, ProcessResult, Path]]]]] = {}
    with ThreadPoolExecutor(max_workers=7) as producer_pool, ThreadPoolExecutor(max_workers=2) as checker_pool:
        futures = [producer_pool.submit(producer_job, geometry_id) for geometry_id in q1y.GEOMETRY_IDS]
        for future in as_completed(futures):
            geometry_id, result, proof = future.result()
            producers[geometry_id] = (result, proof)
            if result.status == "COMPLETE" and proof.is_file():
                checker_futures[geometry_id] = checker_pool.submit(checker_pair_job, geometry_id, proof)
        checker_results = {geometry_id: future.result()[1] for geometry_id, future in checker_futures.items()}

    blocked = False
    local = False
    covariance = False
    unresolved = False
    shards: list[dict[str, Any]] = []
    local_k: dict[str, str] = {}
    for geometry_id in q1y.GEOMETRY_IDS:
        producer_result, proof = producers[geometry_id]
        checks = checker_results.get(geometry_id, [])
        complete = producer_result.status == "COMPLETE" and proof.is_file() and len(checks) == 2
        raw_checks: list[bytes] = []
        if complete:
            complete = all(result.status == "COMPLETE" and path.is_file() for _, result, path in checks)
        if complete:
            raw_checks = [path.read_bytes() for _, _, path in checks]
            complete = raw_checks[0] == raw_checks[1]
        check_value: dict[str, Any] = {}
        if complete:
            check_value = json.loads(raw_checks[0])
            complete = (
                check_value.get("schema") == CHECK_SCHEMA
                and check_value.get("geometry_id") == geometry_id
                and check_value.get("base_reconstruction_count") == 1
                and check_value.get("case_count") == 8
                and check_value.get("station_count") == 32
            )
        blocked = blocked or not complete
        if complete:
            blocked = blocked or bool(check_value.get("proof_disagreement", False))
            local = local or bool(check_value["exact_local_contradictions"])
            covariance = covariance or bool(check_value["exact_operator_contradictions"])
            unresolved = unresolved or bool(check_value["ordered_unresolved"])
            local_k[geometry_id] = check_value["local_k_sha256"]
        shards.append({
            "case_count": int(check_value.get("case_count", 0)),
            "checker_byte_identical": bool(complete),
            "checker_sha256": q1y.sha256(raw_checks[0]) if complete else "",
            "checker_statuses": [result.status for _, result, _ in checks],
            "geometry_id": geometry_id,
            "local_contradiction": bool(check_value.get("exact_local_contradictions", [])),
            "operator_contradiction": bool(check_value.get("exact_operator_contradictions", [])),
            "ordered_unresolved": bool(check_value.get("ordered_unresolved", False)),
            "proof_disagreement": bool(check_value.get("proof_disagreement", False)),
            "producer_status": producer_result.status,
            "proof_sha256": q1y.sha256(proof.read_bytes()) if proof.is_file() else "",
        })
    q3_relation = (
        local_k.get("Q3_TAPERED_SKEW", "") != ""
        and local_k.get("Q3_TAPERED_SKEW") == local_k.get("Q3_TAPERED_SKEW_RSTAR_TRANSLATED")
    )
    covariance = covariance or (not blocked and not q3_relation)
    terminal = select_terminal(contract, blocked=blocked, local=local, covariance=covariance, unresolved=unresolved)
    return {
        "candidate_id": contract["candidate_id"],
        "contract_sha256": successor_contract_sha256.upper(),
        "coverage": {
            "case_count": sum(row["case_count"] for row in shards) if not blocked else 0,
            "geometry_count": sum(row["checker_byte_identical"] for row in shards) if not blocked else 0,
            "rigid_mode_count": 6 if not blocked else 0,
        },
        "cycle_id": cycle_id,
        "local_algebra_contradiction": local,
        "operator_covariance_contradiction": covariance,
        "ordered_sign_unresolved": unresolved,
        "production": contract["production"],
        "q1b_execution": contract["q1b_execution"],
        "q3_proper_global_local_identity": q3_relation,
        "schema": AGGREGATE_SCHEMA,
        "shards": shards,
        "study_id": contract["study_id"],
        "terminal": terminal,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-pipelined-local-algebra", action="store_true")
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--successor-contract", type=Path, required=True)
    parser.add_argument("--successor-contract-sha256", required=True)
    parser.add_argument("--q1y-contract", type=Path, required=True)
    parser.add_argument("--q1y-contract-sha256", required=True)
    parser.add_argument("--environment-root", type=Path, required=True)
    parser.add_argument("--producer", type=Path, required=True)
    parser.add_argument("--checker", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--cycle-id", required=True)
    parser.add_argument("--producer-workers", type=int, default=7)
    parser.add_argument("--checker-workers", type=int, default=4)
    parser.add_argument("--overall-timeout-seconds", type=int, default=600)
    parser.add_argument("--memory-admission-gib", type=int, default=96)
    parser.add_argument("--process-memory-limit-gib", type=int, default=12)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.run_pipelined_local_algebra:
        return 2
    if (
        args.producer_workers,
        args.checker_workers,
        args.overall_timeout_seconds,
        args.memory_admission_gib,
        args.process_memory_limit_gib,
    ) != (7, 4, 600, 96, 12):
        print("formal Q1Y2 controls are frozen", file=sys.stderr)
        return 2
    try:
        value = execute_pipelined(
            repository_root=args.repository_root,
            successor_contract_path=args.successor_contract,
            successor_contract_sha256=args.successor_contract_sha256,
            q1y_contract_path=args.q1y_contract,
            q1y_contract_sha256=args.q1y_contract_sha256,
            environment_root=args.environment_root,
            producer_path=args.producer,
            checker_path=args.checker,
            output_directory=args.output_directory,
            cycle_id=args.cycle_id,
        )
        q1y.write_exclusive(args.output, q1y.canonical_bytes(value))
        return 0
    except (OSError, ValueError, q1y.Q1YError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
