"""Parallel bounded coordinator for Q1C locking diagnosis."""

from __future__ import annotations

import argparse
import ctypes
from dataclasses import dataclass
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from typing import Any, Sequence

import e4_pl_q1b_common as common


STUDY_ID = "study_e4_pl_q1c.q1b_locking_diagnosis_and_conditioning_repair_v1"
CANDIDATE_ID = "candidate_e4_pl_q1c.wg2020_locking_diagnosis_physical_block_scaling_v1"
CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1c-contract-v1"
CYCLE_SCHEMA = "anysolver.s4.e4-pl-q1c-bounded-cycle-v1"
SHARDS = ("SPATIAL_DISCRETIZATION", "THICKNESS_LOCKING", "CONDITIONING_SEPARATION")
TERMINALS = (
    "BLOCKED_E4_PL_Q1C_PROOF_OR_REVIEW",
    "NO_GO_E4_PL_Q1C_LOCKING",
    "NO_GO_E4_PL_Q1C_FORMULATION_REGRESSION",
    "UNCLASSIFIED_E4_PL_Q1C_NUMERICAL_CONDITIONING",
    "UNCLASSIFIED_E4_PL_Q1C_LOCKING_REPAIRED_ONLY",
)


@dataclass(frozen=True)
class ChildResult:
    name: str
    returncode: int
    timed_out: bool
    memory_exceeded: bool


def _memory_bytes(pid: int) -> int:
    if os.name != "nt":
        try:
            status = Path(f"/proc/{pid}/status").read_text(encoding="utf-8")
            return int(status.split("VmRSS:", 1)[1].splitlines()[0].strip().split()[0]) * 1024
        except (OSError, IndexError, ValueError):
            return 0
    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong), ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    handle = ctypes.windll.kernel32.OpenProcess(0x0410, False, pid)
    if not handle:
        return 0
    try:
        return int(counters.WorkingSetSize) if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb) else 0
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def _terminate_tree(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True, check=False, timeout=30)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        environment[name] = "1"
    return environment


def run_wave(commands: list[tuple[str, list[str], Path, str]], *, timeout_seconds: int, memory_limit_gib: int) -> list[ChildResult]:
    if not (1 <= timeout_seconds <= 120) or not (1 <= memory_limit_gib <= 8):
        raise common.Q1BError("Q1C child bounds exceed frozen limits")
    active: list[tuple[str, subprocess.Popen[Any], float, Any, Any, Path]] = []
    environment = _environment()
    memory_limit = memory_limit_gib * (1 << 30)
    for name, command, directory, canonical_name in commands:
        directory.mkdir(parents=True, exist_ok=False)
        stdout = (directory / "stdout.log").open("wb")
        stderr = (directory / "stderr.log").open("wb")
        process = subprocess.Popen(command, cwd=directory, env=environment, stdout=stdout, stderr=stderr, start_new_session=os.name != "nt")
        active.append((name, process, time.monotonic(), stdout, stderr, directory / canonical_name))
    results: list[ChildResult] = []
    while active:
        remaining = []
        for name, process, started, stdout, stderr, canonical_path in active:
            timed_out = time.monotonic() - started > timeout_seconds
            memory_exceeded = _memory_bytes(process.pid) > memory_limit
            if process.poll() is None and not (timed_out or memory_exceeded):
                remaining.append((name, process, started, stdout, stderr, canonical_path))
                continue
            if timed_out or memory_exceeded:
                _terminate_tree(process)
            stdout.close()
            stderr.close()
            returncode = process.returncode if process.returncode is not None else -9
            if returncode or timed_out or memory_exceeded:
                canonical_path.unlink(missing_ok=True)
            results.append(ChildResult(name, returncode, timed_out, memory_exceeded))
        active = remaining
        if active:
            time.sleep(0.05)
    return sorted(results, key=lambda row: row.name)


def validate_contract(repository_root: Path, contract_path: Path, contract_sha256: str) -> dict[str, Any]:
    repository_root = repository_root.resolve()
    expected_path = (repository_root / "docs/reference_cases/e4_pl_q1c_contract.json").resolve()
    if contract_path.resolve() != expected_path:
        raise common.Q1BError("Q1C contract path mismatch")
    raw, contract = common.read_json(expected_path)
    required = {"candidate_id", "classification", "commands", "q1b_authority", "repair", "runtime", "schema", "shards", "study_id", "terminals"}
    if not isinstance(contract, dict) or set(contract) != required:
        raise common.Q1BError("Q1C contract schema mismatch")
    if common.sha256(raw) != contract_sha256.upper() or contract.get("schema") != CONTRACT_SCHEMA:
        raise common.Q1BError("Q1C contract identity mismatch")
    if contract.get("candidate_id") != CANDIDATE_ID or contract.get("study_id") != STUDY_ID:
        raise common.Q1BError("Q1C contract study mismatch")
    if contract.get("shards") != list(SHARDS) or contract.get("terminals") != list(TERMINALS):
        raise common.Q1BError("Q1C contract inventory mismatch")
    if contract.get("runtime") != {"automatic_retry": False, "checker_replicas": 2, "memory_limit_gib": 8, "numerical_threads": 1, "timeout_seconds": 120, "workers": 3}:
        raise common.Q1BError("Q1C runtime contract mismatch")
    if contract.get("repair") != {"drill_coordinate": "EXACT_SCHUR_CONDENSATION_AND_BACK_SUBSTITUTION", "formulation_changes": False, "global_solve": "SYMMETRIC_DIAGONAL_EQUILIBRATION_OF_CONDENSED_PHYSICAL_SYSTEM", "hourglass_changes": False, "mitc_changes": False, "pl_changes": False}:
        raise common.Q1BError("Q1C repair contract mismatch")
    if contract.get("classification") != {"coarse_rows": "CONVERGENCE_EVIDENCE_NOT_DIRECT_LOCKING_TERMINAL", "finest_error_max": "2e-2", "resolved_thickness_range": ["1e-2", "1e-3", "1e-4", "1e-5"], "response_ratio_spread_max": "5e-3", "ultrathin_condition_limit": "1e14"}:
        raise common.Q1BError("Q1C classification contract mismatch")
    if contract.get("commands") != {"checker": "--verify-diagnostic --proof PATH --output PATH", "coordinator": "--run-bounded --workers 3 --timeout-seconds 120 --memory-limit-gib 8", "producer": "--emit-diagnostic --shard ID --output PATH"}:
        raise common.Q1BError("Q1C command contract mismatch")
    q1b = contract.get("q1b_authority", {})
    if not isinstance(q1b, dict) or set(q1b) != {"commit", "common_payload_sha256", "cycle1", "cycle2", "terminal"} or q1b.get("commit") != "3df23199893eb136b2682c5190d1405b52dbdd58" or q1b.get("common_payload_sha256") != "713CA8EF70EDCE5D009B12CF1BEB14B49884EEC01F2C71D4B1D6B2C100FDBDB7" or q1b.get("terminal") != "NO_GO_E4_PL_Q1B_LOCKING_OR_CATEGORY_DRIFT":
        raise common.Q1BError("Q1B authority commit mismatch")
    expected_cycles = {
        "cycle1": {"bytes": 19154, "path": "docs/reference_cases/e4_pl_q1b_cycle1.json", "sha256": "DF040D65A46820C7037111E0B85D6FF4C99E38338CEF9116A908A41F33888407"},
        "cycle2": {"bytes": 19154, "path": "docs/reference_cases/e4_pl_q1b_cycle2.json", "sha256": "945C1B95966836AA64A936AC0E40AE181C8FD3B4A261A894CC44A053332CA408"},
    }
    for key in ("cycle1", "cycle2"):
        row = q1b.get(key, {})
        if row != expected_cycles[key]:
            raise common.Q1BError("Q1B cycle authority mismatch")
        common.verify_file(repository_root / row.get("path", ""), bytes_count=row.get("bytes", -1), digest=row.get("sha256", ""))
    ancestry = subprocess.run(["git", "merge-base", "--is-ancestor", q1b["commit"], "HEAD"], cwd=repository_root, capture_output=True, check=False)
    if ancestry.returncode:
        raise common.Q1BError("Q1B closeout is not an ancestor of Q1C")
    return contract


def _command(repository_root: Path, script: str, *args: str) -> list[str]:
    return [sys.executable, str(repository_root / "docs/reference_cases" / script), *args]


def choose_terminal(*, blocked: bool, locking: bool, formulation: bool, unresolved: bool) -> str:
    if blocked:
        return TERMINALS[0]
    if locking:
        return TERMINALS[1]
    if formulation:
        return TERMINALS[2]
    if unresolved:
        return TERMINALS[3]
    return TERMINALS[4]


def run_cycle(*, repository_root: Path, contract_path: Path, contract_sha256: str, output_root: Path, workers: int, timeout_seconds: int, memory_limit_gib: int) -> dict[str, Any]:
    validate_contract(repository_root, contract_path, contract_sha256)
    if workers != 3 or output_root.exists():
        raise common.Q1BError("Q1C requires three workers and an exclusive output root")
    output_root.mkdir(parents=True, exist_ok=False)
    producer_commands = []
    for shard in SHARDS:
        directory = output_root / f"producer-{shard.lower()}"
        producer_commands.append((shard, _command(repository_root, "e4_pl_q1c_diagnostic_producer.py", "--emit-diagnostic", "--shard", shard, "--output", str(directory / "proof.json")), directory, "proof.json"))
    producer_results = run_wave(producer_commands, timeout_seconds=timeout_seconds, memory_limit_gib=memory_limit_gib)
    blocked = any(row.returncode or row.timed_out or row.memory_exceeded for row in producer_results)

    checker_results: list[ChildResult] = []
    if not blocked:
        checker_commands = []
        for shard in SHARDS:
            proof = output_root / f"producer-{shard.lower()}" / "proof.json"
            for replica in (1, 2):
                directory = output_root / f"checker{replica}-{shard.lower()}"
                checker_commands.append((f"{shard}:{replica}", _command(repository_root, "e4_pl_q1c_diagnostic_checker.py", "--verify-diagnostic", "--proof", str(proof), "--output", str(directory / "check.json")), directory, "check.json"))
        checker_results = run_wave(checker_commands, timeout_seconds=timeout_seconds, memory_limit_gib=memory_limit_gib)
        blocked = any(row.returncode or row.timed_out or row.memory_exceeded for row in checker_results)

    shards = []
    diagnostic_hashes = []
    locking = formulation = unresolved = False
    if not blocked:
        for shard in SHARDS:
            proof_path = output_root / f"producer-{shard.lower()}" / "proof.json"
            proof_raw, _ = common.read_json(proof_path)
            checks = [common.read_json(output_root / f"checker{replica}-{shard.lower()}" / "check.json") for replica in (1, 2)]
            if checks[0][0] != checks[1][0]:
                blocked = True
            check = checks[0][1]
            if check["disagreements"]:
                blocked = True
            contradictions = check["contradictions"]
            locking |= shard in SHARDS[:2] and bool(contradictions)
            formulation |= shard == SHARDS[2] and bool(contradictions)
            unresolved |= bool(check["conditioning_unresolved"])
            shards.append({"classification_facts": check["classification_facts"], "conditioning_unresolved": check["conditioning_unresolved"], "contradictions": contradictions, "disagreements": check["disagreements"], "shard": shard})
            diagnostic_hashes.append({"check_sha256": common.sha256(checks[0][0]), "proof_sha256": common.sha256(proof_raw), "shard": shard})
    terminal = choose_terminal(blocked=blocked, locking=locking, formulation=formulation, unresolved=unresolved)
    common_payload = {"candidate_id": CANDIDATE_ID, "coverage": {"checker_replicas": 2, "completed_shards": len(shards), "producer_shards": 3}, "production": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED", "shards": shards, "study_id": STUDY_ID, "terminal": terminal}
    aggregate = {"candidate_id": CANDIDATE_ID, "common_payload": common_payload, "common_payload_sha256": common.sha256(common.canonical_bytes(common_payload)), "contract_sha256": contract_sha256.upper(), "diagnostic_hashes": diagnostic_hashes, "schema": CYCLE_SCHEMA, "study_id": STUDY_ID}
    common.write_exclusive(output_root / "aggregate.json", aggregate)
    return aggregate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-bounded", action="store_true", required=True)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--memory-limit-gib", type=int, default=8)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        run_cycle(repository_root=args.repository_root.resolve(), contract_path=args.contract, contract_sha256=args.contract_sha256, output_root=args.output_root, workers=args.workers, timeout_seconds=args.timeout_seconds, memory_limit_gib=args.memory_limit_gib)
        return 0
    except (OSError, ValueError, common.Q1BError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
