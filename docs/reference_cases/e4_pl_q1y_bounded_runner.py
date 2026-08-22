"""Run seven Q1Y algebra producers and fourteen checker replicas under bounds."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
import sys
from typing import Any, Sequence

from e4_pl_q1w_bounded_runner import ProcessResult, run_bounded_process
from e4_pl_q1y_common import (
    AGGREGATE_SCHEMA, CHECK_SCHEMA, GEOMETRY_IDS, Q1YError, canonical_bytes,
    read_json, sha256, validate_contract, validate_environment, write_exclusive,
)


THREAD_ENVIRONMENT = {
    "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1", "NUMEXPR_NUM_THREADS": "1",
}


def _progress(phase: str, **extra: Any) -> None:
    sys.stderr.buffer.write(canonical_bytes({"phase": phase, **extra}))
    sys.stderr.buffer.flush()


def _status(result: ProcessResult) -> dict[str, Any]:
    return {"returncode": result.returncode if result.returncode is not None else -1, "status": result.status}


def discard_incomplete_output(path: Path, result: ProcessResult) -> None:
    if result.status != "COMPLETE":
        path.unlink(missing_ok=True)


def select_terminal(
    *, blocked: bool, local_contradictions: Sequence[str], operator_contradictions: Sequence[str],
    ordered_unresolved: bool, terminals: dict[str, str],
) -> str:
    if blocked:
        return terminals["blocked"]
    if local_contradictions:
        return terminals["local_algebra"]
    if operator_contradictions:
        return terminals["operator_covariance"]
    if ordered_unresolved:
        return terminals["ordered_sign"]
    return terminals["success"]


def execute_bounded(
    *, repository_root: Path, contract_path: Path, contract_sha256: str,
    environment_root: Path, producer_path: Path, checker_path: Path, output_directory: Path,
) -> dict[str, Any]:
    contract = validate_contract(repository_root, contract_path, contract_sha256)
    validate_environment(repository_root, environment_root, contract)
    producer = producer_path.resolve(strict=True)
    checker = checker_path.resolve(strict=True)
    if producer.is_symlink() or checker.is_symlink() or not producer.is_file() or not checker.is_file():
        raise Q1YError("producer/checker must be regular nonsymlink files")
    output_directory.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    environment.update(THREAD_ENVIRONMENT)
    timeout = int(contract["parallelism"]["timeout_seconds_per_process"])
    memory = int(contract["parallelism"]["memory_limit_gib_per_process"]) * 1024**3
    geometries = list(GEOMETRY_IDS)

    def producer_job(geometry_id: str) -> tuple[str, ProcessResult, Path]:
        proof = output_directory / f"{geometry_id}.proof.json"
        result = run_bounded_process(
            [sys.executable, str(producer), "--emit-algebra-proof", "--repository-root", str(repository_root),
             "--contract", str(contract_path), "--contract-sha256", contract_sha256,
             "--geometry-id", geometry_id, "--output", str(proof)],
            cwd=repository_root, environment=environment,
            stdout_path=output_directory / f"{geometry_id}.producer.stdout.log",
            stderr_path=output_directory / f"{geometry_id}.producer.progress.jsonl",
            timeout_seconds=timeout, memory_limit_bytes=memory,
        )
        discard_incomplete_output(proof, result)
        return geometry_id, result, proof

    _progress("PRODUCER_WAVE_INITIALIZED", geometry_count=7, workers=3)
    producers: dict[str, tuple[ProcessResult, Path]] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(producer_job, geometry_id) for geometry_id in geometries]
        for future in as_completed(futures):
            geometry_id, result, proof = future.result()
            producers[geometry_id] = (result, proof)
            _progress("PRODUCER_COMPLETED", geometry_id=geometry_id, status=result.status)

    def checker_job(geometry_id: str, proof: Path, replica: int) -> tuple[str, int, ProcessResult, Path]:
        output = output_directory / f"{geometry_id}.check{replica}.json"
        result = run_bounded_process(
            [sys.executable, str(checker), "--verify-algebra-proof", "--repository-root", str(repository_root),
             "--contract", str(contract_path), "--contract-sha256", contract_sha256, "--proof", str(proof),
             "--environment-root", str(environment_root), "--output", str(output)],
            cwd=repository_root, environment=environment,
            stdout_path=output_directory / f"{geometry_id}.check{replica}.stdout.log",
            stderr_path=output_directory / f"{geometry_id}.check{replica}.stderr.log",
            timeout_seconds=timeout, memory_limit_bytes=memory,
        )
        discard_incomplete_output(output, result)
        return geometry_id, replica, result, output

    checker_results: dict[str, list[tuple[int, ProcessResult, Path]]] = {geometry_id: [] for geometry_id in geometries}
    completed = [g for g in geometries if producers[g][0].status == "COMPLETE" and producers[g][1].is_file()]
    for offset in range(0, len(completed), 2):
        batch = completed[offset:offset + 2]
        _progress("CHECKER_BATCH_INITIALIZED", geometry_ids=batch, workers=2 * len(batch))
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(checker_job, g, producers[g][1], replica) for g in batch for replica in (1, 2)]
            for future in as_completed(futures):
                geometry_id, replica, result, output = future.result()
                checker_results[geometry_id].append((replica, result, output))
                _progress("CHECKER_COMPLETED", geometry_id=geometry_id, replica=replica, status=result.status)
    for rows in checker_results.values():
        rows.sort(key=lambda row: row[0])

    blocked = False
    local_contradictions: list[str] = []
    operator_contradictions: list[str] = []
    unresolved = False
    shards: list[dict[str, Any]] = []
    k_hashes: dict[str, str] = {}
    for geometry_id in geometries:
        producer_result, proof = producers[geometry_id]
        checks = checker_results[geometry_id]
        identical = False
        check_hash = ""
        value: dict[str, Any] = {}
        if producer_result.status != "COMPLETE" or not proof.is_file() or len(checks) != 2:
            blocked = True
        elif any(result.status != "COMPLETE" or not path.is_file() for _, result, path in checks):
            blocked = True
        else:
            first, second = checks[0][2].read_bytes(), checks[1][2].read_bytes()
            identical = first == second
            if not identical:
                blocked = True
            else:
                value = read_json(checks[0][2])[1]
                if value.get("schema") != CHECK_SCHEMA or value.get("geometry_id") != geometry_id:
                    blocked = True
                else:
                    check_hash = sha256(first)
                    local_contradictions.extend(str(item) for item in value["exact_local_contradictions"])
                    operator_contradictions.extend(str(item) for item in value["exact_operator_contradictions"])
                    unresolved = unresolved or bool(value["ordered_unresolved"])
                    k_hashes[geometry_id] = str(value["local_k_sha256"])
        shards.append({
            "case_count": int(value.get("case_count", 0)), "checker_byte_identical": identical,
            "checker_processes": [_status(result) for _, result, _ in checks], "checker_sha256": check_hash,
            "geometry_id": geometry_id, "producer_process": _status(producer_result),
            "proof_sha256": sha256(proof.read_bytes()) if proof.is_file() else "",
            "station_count": int(value.get("station_count", 0)),
        })

    q3 = k_hashes.get("Q3_TAPERED_SKEW")
    q3_star = k_hashes.get("Q3_TAPERED_SKEW_RSTAR_TRANSLATED")
    if q3 and q3_star and q3 != q3_star:
        operator_contradictions.append("Q3_TAPERED_SKEW_RSTAR_TRANSLATED::GLOBAL")
    elif not blocked and (not q3 or not q3_star):
        blocked = True
    terminal = select_terminal(
        blocked=blocked, local_contradictions=local_contradictions,
        operator_contradictions=operator_contradictions, ordered_unresolved=unresolved,
        terminals=contract["terminals"],
    )
    return {
        "bounded_result": {
            "case_count": sum(row["case_count"] for row in shards),
            "exact_local_contradictions": local_contradictions,
            "exact_operator_contradictions": operator_contradictions,
            "geometry_count": sum(row["producer_process"]["status"] == "COMPLETE" for row in shards),
            "ordered_unresolved": unresolved, "production": contract["production"],
            "q1b_execution": contract["q1b_execution"], "rigid_mode_count": 6,
            "station_count": sum(row["station_count"] for row in shards), "terminal": terminal,
            "quotient_dimension": 18,
        },
        "contract_sha256": contract_sha256.upper(), "process_policy": contract["parallelism"],
        "schema": AGGREGATE_SCHEMA, "shards": shards,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-bounded-local-algebra", action="store_true", required=True)
    parser.add_argument("--workers", type=int, default=3); parser.add_argument("--timeout-seconds", type=int, default=600); parser.add_argument("--memory-limit-gib", type=int, default=24)
    parser.add_argument("--repository-root", type=Path, required=True); parser.add_argument("--contract", type=Path, required=True); parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--environment-root", type=Path, required=True); parser.add_argument("--producer", type=Path, required=True); parser.add_argument("--checker", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True); parser.add_argument("--aggregate", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if (args.workers, args.timeout_seconds, args.memory_limit_gib) != (3, 600, 24):
            raise Q1YError("formal controls are fixed at workers=3, timeout=600, memory=24 GiB")
        if args.aggregate.resolve().is_relative_to(args.output_directory.resolve()):
            raise Q1YError("canonical aggregate must be outside diagnostic directory")
        value = execute_bounded(
            repository_root=args.repository_root.resolve(strict=True), contract_path=args.contract,
            contract_sha256=args.contract_sha256, environment_root=args.environment_root,
            producer_path=args.producer, checker_path=args.checker, output_directory=args.output_directory,
        )
        write_exclusive(args.aggregate, canonical_bytes(value))
        return 2 if value["bounded_result"]["terminal"] == "BLOCKED_E4_PL_Q1Y_PROOF_OR_REVIEW" else 0
    except (Q1YError, KeyError, TypeError, ValueError, ZeroDivisionError, OSError) as exc:
        print(f"BLOCKED_E4_PL_Q1Y_PROOF_OR_REVIEW: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
