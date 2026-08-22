"""Run seven Q1X geometry producers and fourteen checker replicas under bounds."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path
import sys
from typing import Any, Sequence

from e4_pl_q1w_bounded_runner import ProcessResult, run_bounded_process
from e4_pl_q1x_common import (
    AGGREGATE_SCHEMA,
    CHECK_SCHEMA,
    GEOMETRY_IDS,
    OPERATION_IDS,
    Q1XError,
    canonical_bytes,
    read_json,
    sha256,
    validate_contract,
    validate_environment,
    verify_file,
    write_exclusive,
)


THREAD_ENVIRONMENT = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}


def _progress(phase: str, **extra: Any) -> None:
    sys.stderr.buffer.write(canonical_bytes({"phase": phase, **extra}))
    sys.stderr.buffer.flush()


def select_terminal(
    case_order: Sequence[str],
    contradiction_cases: Sequence[str],
    *,
    blocked: bool,
    terminals: dict[str, str],
) -> tuple[str, str]:
    if blocked:
        return terminals["blocked"], ""
    selected = next((case_id for case_id in case_order if case_id in contradiction_cases), "")
    if selected:
        return terminals["exact_counterexample"], selected
    return terminals["transport_closed_only"], ""


def _status(result: ProcessResult) -> dict[str, Any]:
    return {"returncode": result.returncode if result.returncode is not None else -1, "status": result.status}


def discard_incomplete_output(path: Path, result: ProcessResult) -> None:
    """Remove only a fresh shard output when its bounded child did not finish."""

    if result.status != "COMPLETE":
        path.unlink(missing_ok=True)


def execute_bounded(
    *,
    repository_root: Path,
    contract_path: Path,
    contract_sha256: str,
    historical_reference: Path,
    historical_reference_sha256: str,
    environment_root: Path,
    producer_path: Path,
    checker_path: Path,
    output_directory: Path,
) -> dict[str, Any]:
    contract = validate_contract(repository_root, contract_path, contract_sha256)
    historical = contract["historical_reference"]
    verify_file(historical_reference, size=int(historical["bytes"]), digest=historical_reference_sha256)
    if historical_reference_sha256.upper() != historical["sha256"]:
        raise Q1XError("historical wrapper caller hash mismatch")
    validate_environment(repository_root, environment_root, contract)
    producer = producer_path.resolve(strict=True)
    checker = checker_path.resolve(strict=True)
    if producer.is_symlink() or checker.is_symlink() or not producer.is_file() or not checker.is_file():
        raise Q1XError("producer/checker path is not a regular nonsymlink file")
    output_directory.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    environment.update(THREAD_ENVIRONMENT)
    timeout = int(contract["parallelism"]["timeout_seconds_per_process"])
    memory = int(contract["parallelism"]["memory_limit_gib_per_process"]) * 1024**3
    geometries = list(GEOMETRY_IDS)
    _progress("PRODUCER_WAVE_INITIALIZED", geometry_count=7, workers=3)

    def producer_job(geometry_id: str) -> tuple[str, ProcessResult, Path]:
        proof = output_directory / f"{geometry_id}.proof.json"
        command = [
            sys.executable,
            str(producer),
            "--emit-proof",
            "--repository-root",
            str(repository_root),
            "--transport-contract",
            str(contract_path),
            "--transport-contract-sha256",
            contract_sha256,
            "--historical-reference",
            str(historical_reference),
            "--historical-reference-sha256",
            historical_reference_sha256,
            "--geometry-id",
            geometry_id,
            "--output",
            str(proof),
        ]
        result = run_bounded_process(
            command,
            cwd=repository_root,
            environment=environment,
            stdout_path=output_directory / f"{geometry_id}.producer.stdout.log",
            stderr_path=output_directory / f"{geometry_id}.producer.progress.jsonl",
            timeout_seconds=timeout,
            memory_limit_bytes=memory,
        )
        discard_incomplete_output(proof, result)
        return geometry_id, result, proof

    producers: dict[str, tuple[ProcessResult, Path]] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(producer_job, geometry_id) for geometry_id in geometries]
        for future in as_completed(futures):
            geometry_id, result, proof = future.result()
            producers[geometry_id] = (result, proof)
            _progress("PRODUCER_COMPLETED", geometry_id=geometry_id, status=result.status)

    checker_results: dict[str, list[tuple[int, ProcessResult, Path]]] = {geometry_id: [] for geometry_id in geometries}

    def checker_job(geometry_id: str, proof: Path, replica: int) -> tuple[str, int, ProcessResult, Path]:
        output = output_directory / f"{geometry_id}.check{replica}.json"
        command = [
            sys.executable,
            str(checker),
            "--verify-proof",
            "--repository-root",
            str(repository_root),
            "--transport-contract",
            str(contract_path),
            "--transport-contract-sha256",
            contract_sha256,
            "--historical-reference",
            str(historical_reference),
            "--historical-reference-sha256",
            historical_reference_sha256,
            "--proof",
            str(proof),
            "--environment-root",
            str(environment_root),
            "--output",
            str(output),
        ]
        result = run_bounded_process(
            command,
            cwd=repository_root,
            environment=environment,
            stdout_path=output_directory / f"{geometry_id}.check{replica}.stdout.log",
            stderr_path=output_directory / f"{geometry_id}.check{replica}.stderr.log",
            timeout_seconds=timeout,
            memory_limit_bytes=memory,
        )
        discard_incomplete_output(output, result)
        return geometry_id, replica, result, output

    # Two geometry pairs (four processes) at a time guarantees that each
    # geometry's two independent replicas overlap without admitting more than
    # 96 GiB of bounded checker memory.
    completed_geometries = [geometry_id for geometry_id in geometries if producers[geometry_id][0].status == "COMPLETE" and producers[geometry_id][1].is_file()]
    for offset in range(0, len(completed_geometries), 2):
        batch = completed_geometries[offset : offset + 2]
        _progress("CHECKER_BATCH_INITIALIZED", geometry_ids=batch, workers=len(batch) * 2)
        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [
                pool.submit(checker_job, geometry_id, producers[geometry_id][1], replica)
                for geometry_id in batch
                for replica in (1, 2)
            ]
            for future in as_completed(futures):
                geometry_id, replica, result, output = future.result()
                checker_results[geometry_id].append((replica, result, output))
                _progress("CHECKER_COMPLETED", geometry_id=geometry_id, replica=replica, status=result.status)
    for rows in checker_results.values():
        rows.sort(key=lambda item: item[0])

    blocked = False
    contradiction_cases: list[str] = []
    shards: list[dict[str, Any]] = []
    for geometry_id in geometries:
        producer_result, proof = producers[geometry_id]
        checkers = checker_results[geometry_id]
        proof_sha = sha256(proof.read_bytes()) if proof.is_file() else ""
        checker_identical = False
        checker_sha = ""
        checker_terminal = ""
        case_count = 0
        station_count = 0
        if producer_result.status != "COMPLETE" or len(checkers) != 2:
            blocked = True
        elif any(result.status != "COMPLETE" or not path.is_file() for _, result, path in checkers):
            blocked = True
        else:
            first = checkers[0][2].read_bytes()
            second = checkers[1][2].read_bytes()
            checker_identical = first == second
            if not checker_identical:
                blocked = True
            else:
                value = read_json(checkers[0][2])[1]
                if value.get("schema") != CHECK_SCHEMA or value.get("geometry_id") != geometry_id:
                    blocked = True
                else:
                    checker_sha = sha256(first)
                    checker_terminal = str(value["terminal"])
                    case_count = int(value["case_count"])
                    station_count = int(value["station_count"])
                    contradiction_cases.extend(str(item) for item in value["exact_counterexample_cases"])
        shards.append(
            {
                "case_count": case_count,
                "checker_byte_identical": checker_identical,
                "checker_processes": [_status(result) for _, result, _ in checkers],
                "checker_sha256": checker_sha,
                "checker_terminal": checker_terminal,
                "geometry_id": geometry_id,
                "producer_process": _status(producer_result),
                "proof_sha256": proof_sha,
                "station_count": station_count,
            }
        )
    case_order = [f"{geometry_id}::{operation_id}" for geometry_id in GEOMETRY_IDS for operation_id in OPERATION_IDS]
    selected_order = case_order + ["Q3_TAPERED_SKEW_RSTAR_TRANSLATED::GLOBAL"]
    terminal, selected = select_terminal(selected_order, contradiction_cases, blocked=blocked, terminals=contract["terminals"])
    return {
        "bounded_result": {
            "case_count": sum(row["case_count"] for row in shards),
            "case_order": case_order,
            "exact_counterexample_cases": contradiction_cases,
            "geometry_count": sum(row["producer_process"]["status"] == "COMPLETE" for row in shards),
            "production": contract["production"],
            "q1b_execution": contract["q1b_execution"],
            "selected_counterexample": selected,
            "station_count": sum(row["station_count"] for row in shards),
            "terminal": terminal,
        },
        "historical_reference_sha256": historical_reference_sha256.upper(),
        "process_policy": contract["parallelism"],
        "schema": AGGREGATE_SCHEMA,
        "shards": shards,
        "transport_contract_sha256": contract_sha256.upper(),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-bounded", action="store_true", required=True)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--memory-limit-gib", type=int, default=24)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--transport-contract", type=Path, required=True)
    parser.add_argument("--transport-contract-sha256", required=True)
    parser.add_argument("--historical-reference", type=Path, required=True)
    parser.add_argument("--historical-reference-sha256", required=True)
    parser.add_argument("--environment-root", type=Path, required=True)
    parser.add_argument("--producer", type=Path, required=True)
    parser.add_argument("--checker", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--aggregate", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if (args.workers, args.timeout_seconds, args.memory_limit_gib) != (3, 600, 24):
            raise Q1XError("formal controls are fixed at workers=3, timeout=600, memory=24 GiB")
        if args.aggregate.resolve().is_relative_to(args.output_directory.resolve()):
            raise Q1XError("canonical aggregate must be outside diagnostic directory")
        value = execute_bounded(
            repository_root=args.repository_root,
            contract_path=args.transport_contract,
            contract_sha256=args.transport_contract_sha256,
            historical_reference=args.historical_reference,
            historical_reference_sha256=args.historical_reference_sha256,
            environment_root=args.environment_root,
            producer_path=args.producer,
            checker_path=args.checker,
            output_directory=args.output_directory,
        )
        write_exclusive(args.aggregate, canonical_bytes(value))
        return 2 if value["bounded_result"]["terminal"] == "BLOCKED_E4_PL_Q1X_PROOF_OR_REVIEW" else 0
    except (Q1XError, KeyError, TypeError, ValueError, OSError) as exc:
        print(f"BLOCKED_E4_PL_Q1X_PROOF_OR_REVIEW: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
