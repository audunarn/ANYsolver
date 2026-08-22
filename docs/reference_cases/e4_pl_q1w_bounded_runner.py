"""Run the three Q1W proof shards and checker replicas under hard bounds."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Sequence

from e4_pl_q1w_common import (
    AGGREGATE_SCHEMA,
    CHECK_SCHEMA,
    Q1WError,
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


@dataclass(frozen=True)
class ProcessResult:
    status: str
    returncode: int | None
    elapsed_ms: int
    peak_rss_bytes: int | None
    stdout_path: str
    stderr_path: str


def _rss_bytes_windows(pid: int) -> int | None:
    if os.name != "nt":
        return None

    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    handle = kernel32.OpenProcess(0x0400 | 0x0010, False, pid)
    if not handle:
        return None
    try:
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            return None
        return int(counters.WorkingSetSize)
    finally:
        kernel32.CloseHandle(handle)


def _terminate_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        process.kill()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


def run_bounded_process(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    stdout_path: Path,
    stderr_path: Path,
    timeout_seconds: float,
    memory_limit_bytes: int,
    rss_reader: Any = _rss_bytes_windows,
) -> ProcessResult:
    started = time.monotonic()
    peak: int | None = None
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(
            list(command),
            cwd=cwd,
            env=environment,
            stdout=stdout,
            stderr=stderr,
            stdin=subprocess.DEVNULL,
        )
        status = "RUNNING"
        while process.poll() is None:
            elapsed = time.monotonic() - started
            if elapsed > timeout_seconds:
                status = "TIMEOUT"
                _terminate_tree(process)
                break
            rss = rss_reader(process.pid)
            if rss is not None:
                peak = rss if peak is None else max(peak, rss)
                if rss > memory_limit_bytes:
                    status = "MEMORY_LIMIT"
                    _terminate_tree(process)
                    break
            time.sleep(0.05)
        returncode = process.poll()
        if status == "RUNNING":
            status = "COMPLETE" if returncode == 0 else "FAILED"
    return ProcessResult(
        status=status,
        returncode=returncode,
        elapsed_ms=int((time.monotonic() - started) * 1000),
        peak_rss_bytes=peak,
        stdout_path=stdout_path.name,
        stderr_path=stderr_path.name,
    )


def _process_row(case_id: str, role: str, result: ProcessResult) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "role": role,
        "status": result.status,
        "returncode": result.returncode if result.returncode is not None else -1,
        "elapsed_ms": result.elapsed_ms,
        "peak_rss_bytes": result.peak_rss_bytes if result.peak_rss_bytes is not None else -1,
        "stdout_log": result.stdout_path,
        "stderr_log": result.stderr_path,
    }


def select_terminal(
    case_order: Sequence[str],
    contradiction_cases: Sequence[str],
    *,
    blocked: bool,
    terminals: dict[str, str],
) -> tuple[str, str]:
    selected = next((case_id for case_id in case_order if case_id in contradiction_cases), "")
    if blocked:
        return terminals["blocked"], ""
    if selected:
        return terminals["exact_counterexample"], selected
    return terminals["no_bounded_counterexample"], ""


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
        raise Q1WError("historical reference caller hash mismatch")
    validate_environment(repository_root, environment_root, contract)
    producer = producer_path.resolve(strict=True)
    checker = checker_path.resolve(strict=True)
    if producer.is_symlink() or checker.is_symlink() or not producer.is_file() or not checker.is_file():
        raise Q1WError("producer/checker must be regular nonsymlink files")
    output_directory.mkdir(parents=True, exist_ok=False)
    environment = os.environ.copy()
    environment.update(THREAD_ENVIRONMENT)
    timeout = int(contract["parallelism"]["timeout_seconds_per_process"])
    memory = int(contract["parallelism"]["memory_limit_gib_per_producer"]) * 1024**3
    cases = list(contract["shards"])

    def producer_job(case_id: str) -> tuple[str, ProcessResult, Path]:
        slug = case_id.replace("::", "_")
        proof = output_directory / f"{slug}.proof.json"
        command = [
            sys.executable,
            str(producer),
            "--emit-proof",
            "--repository-root",
            str(repository_root),
            "--proof-contract",
            str(contract_path),
            "--proof-contract-sha256",
            contract_sha256,
            "--historical-reference",
            str(historical_reference),
            "--historical-reference-sha256",
            historical_reference_sha256,
            "--case-id",
            case_id,
            "--output",
            str(proof),
        ]
        result = run_bounded_process(
            command,
            cwd=repository_root,
            environment=environment,
            stdout_path=output_directory / f"{slug}.producer.stdout.log",
            stderr_path=output_directory / f"{slug}.producer.stderr.jsonl",
            timeout_seconds=timeout,
            memory_limit_bytes=memory,
        )
        return case_id, result, proof

    producers: dict[str, tuple[ProcessResult, Path]] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(producer_job, case_id) for case_id in cases]
        for future in as_completed(futures):
            case_id, result, proof = future.result()
            producers[case_id] = (result, proof)

    checker_results: dict[str, list[tuple[ProcessResult, Path]]] = {case_id: [] for case_id in cases}

    def checker_job(case_id: str, proof: Path, replica: int) -> tuple[str, int, ProcessResult, Path]:
        slug = case_id.replace("::", "_")
        output = output_directory / f"{slug}.check{replica}.json"
        command = [
            sys.executable,
            str(checker),
            "--verify-proof",
            "--repository-root",
            str(repository_root),
            "--proof-contract",
            str(contract_path),
            "--proof-contract-sha256",
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
            stdout_path=output_directory / f"{slug}.check{replica}.stdout.log",
            stderr_path=output_directory / f"{slug}.check{replica}.stderr.log",
            timeout_seconds=timeout,
            memory_limit_bytes=memory,
        )
        return case_id, replica, result, output

    checker_futures = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for case_id in cases:
            producer_result, proof = producers[case_id]
            if producer_result.status == "COMPLETE" and proof.is_file():
                checker_futures.extend(pool.submit(checker_job, case_id, proof, replica) for replica in (1, 2))
        for future in as_completed(checker_futures):
            case_id, replica, result, output = future.result()
            checker_results[case_id].append((result, output))
    for rows in checker_results.values():
        rows.sort(key=lambda item: item[1].name)

    diagnostics: list[dict[str, Any]] = []
    shards: list[dict[str, Any]] = []
    blocked = False
    contradiction_cases: list[str] = []
    for case_id in cases:
        producer_result, proof = producers[case_id]
        diagnostics.append(_process_row(case_id, "PRODUCER", producer_result))
        checks = checker_results[case_id]
        proof_hash = sha256(proof.read_bytes()) if proof.is_file() else ""
        checker_identical = False
        check_terminal = ""
        check_hash = ""
        for replica, (result, output) in enumerate(checks, start=1):
            diagnostics.append(_process_row(case_id, f"CHECKER_{replica}", result))
        if producer_result.status != "COMPLETE" or len(checks) != 2:
            blocked = True
        elif any(result.status != "COMPLETE" or not output.is_file() for result, output in checks):
            blocked = True
        else:
            raw1 = checks[0][1].read_bytes()
            raw2 = checks[1][1].read_bytes()
            checker_identical = raw1 == raw2
            if not checker_identical:
                blocked = True
            else:
                value = read_json(checks[0][1])[1]
                if value.get("schema") != CHECK_SCHEMA:
                    blocked = True
                else:
                    check_terminal = value["terminal"]
                    check_hash = sha256(raw1)
                    if value["exact_nonzero_transport_residuals"]:
                        contradiction_cases.append(case_id)
        shards.append(
            {
                "case_id": case_id,
                "producer_status": producer_result.status,
                "proof_sha256": proof_hash,
                "checker_replicas": len(checks),
                "checker_byte_identical": checker_identical,
                "checker_sha256": check_hash,
                "checker_terminal": check_terminal,
            }
        )

    terminal, selected = select_terminal(
        cases,
        contradiction_cases,
        blocked=blocked,
        terminals=contract["terminals"],
    )
    bounded_result = {
        "candidate_id": contract["candidate_id"],
        "study_id": contract["study_id"],
        "case_order": cases,
        "completed_shards": sum(row["producer_status"] == "COMPLETE" for row in shards),
        "exact_counterexample_cases": contradiction_cases,
        "selected_counterexample": selected,
        "production": contract["production"],
        "q1b_execution": contract["q1b_execution"],
        "terminal": terminal,
    }
    return {
        "schema": AGGREGATE_SCHEMA,
        "bounded_result": bounded_result,
        "shards": shards,
        "execution_diagnostics": diagnostics,
        "proof_contract_sha256": contract_sha256.upper(),
        "historical_reference_sha256": historical_reference_sha256.upper(),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-bounded", action="store_true", required=True)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument("--memory-limit-gib", type=int, default=24)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--proof-contract", type=Path, required=True)
    parser.add_argument("--proof-contract-sha256", required=True)
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
            raise Q1WError("formal bounded controls are fixed at workers=3, timeout=600, memory=24 GiB")
        if args.aggregate.resolve().is_relative_to(args.output_directory.resolve()):
            raise Q1WError("aggregate must be outside the fresh diagnostic output directory")
        result = execute_bounded(
            repository_root=args.repository_root,
            contract_path=args.proof_contract,
            contract_sha256=args.proof_contract_sha256,
            historical_reference=args.historical_reference,
            historical_reference_sha256=args.historical_reference_sha256,
            environment_root=args.environment_root,
            producer_path=args.producer,
            checker_path=args.checker,
            output_directory=args.output_directory,
        )
        write_exclusive(args.aggregate, canonical_bytes(result))
        return 0 if result["bounded_result"]["terminal"] != "BLOCKED_E4_PL_Q1W_PROOF_OR_REVIEW" else 2
    except (Q1WError, KeyError, ValueError, OSError) as exc:
        print(f"BLOCKED_E4_PL_Q1W_PROOF_OR_REVIEW: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
