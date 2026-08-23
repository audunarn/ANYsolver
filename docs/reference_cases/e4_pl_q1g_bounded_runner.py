"""Bounded concurrent coordinator for Q1G proof and checker processes."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import e4_pl_q1g_common as common


AGGREGATE_SCHEMA = "anysolver.s4.e4-pl-q1g-domain-aggregate-v1"


@dataclass(frozen=True)
class ProcessSpec:
    name: str
    command: tuple[str, ...]
    directory: Path
    output: Path


@dataclass(frozen=True)
class ProcessResult:
    name: str
    returncode: int
    state: str
    started_ns: int
    ended_ns: int
    peak_rss: int


def _rss_bytes(pid: int) -> int:
    if os.name == "nt":
        class Counters(ctypes.Structure):
            _fields_ = [
                ("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
            ]
        handle = ctypes.windll.kernel32.OpenProcess(0x1000 | 0x0400, False, pid)
        if not handle:
            return 0
        try:
            counters = Counters()
            counters.cb = ctypes.sizeof(counters)
            if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                return int(counters.WorkingSetSize)
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
        return 0
    status = Path(f"/proc/{pid}/status")
    if status.is_file():
        for line in status.read_text(encoding="utf-8").splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    return 0


def _terminate_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


def _child_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        environment[name] = "1"
    environment["PYTHONHASHSEED"] = "0"
    return environment


def _run_wave(specs: Sequence[ProcessSpec], timeout_seconds: int, memory_limit_bytes: int, global_deadline: float) -> list[ProcessResult]:
    if not specs or len({spec.name for spec in specs}) != len(specs):
        raise common.Q1GError("invalid process wave")
    active: dict[str, tuple[ProcessSpec, subprocess.Popen[bytes], Any, Any, int, int]] = {}
    results: list[ProcessResult] = []
    for spec in specs:
        spec.directory.mkdir(parents=True, exist_ok=False)
        stdout_handle = (spec.directory / "stdout.log").open("xb")
        stderr_handle = (spec.directory / "stderr.log").open("xb")
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
        process = subprocess.Popen(
            list(spec.command), cwd=spec.directory, env=_child_environment(),
            stdout=stdout_handle, stderr=stderr_handle, creationflags=flags,
            start_new_session=os.name != "nt",
        )
        now = time.monotonic_ns()
        active[spec.name] = (spec, process, stdout_handle, stderr_handle, now, 0)
    while active:
        if time.monotonic() > global_deadline:
            for spec, process, stdout_handle, stderr_handle, started, peak in active.values():
                _terminate_tree(process)
                stdout_handle.close(); stderr_handle.close()
                spec.output.unlink(missing_ok=True)
                results.append(ProcessResult(spec.name, process.returncode or -9, "GLOBAL_TIMEOUT", started, time.monotonic_ns(), peak))
            active.clear()
            break
        for name in list(active):
            spec, process, stdout_handle, stderr_handle, started, peak = active[name]
            peak = max(peak, _rss_bytes(process.pid))
            elapsed = (time.monotonic_ns() - started) / 1_000_000_000
            state: str | None = None
            if peak > memory_limit_bytes:
                state = "MEMORY_LIMIT"
                _terminate_tree(process)
            elif elapsed > timeout_seconds:
                state = "TIMEOUT"
                _terminate_tree(process)
            elif process.poll() is not None:
                state = "COMPLETE" if process.returncode == 0 and spec.output.is_file() else "FAILED"
            if state is not None:
                stdout_handle.close(); stderr_handle.close()
                if state != "COMPLETE":
                    spec.output.unlink(missing_ok=True)
                results.append(ProcessResult(name, process.returncode or 0, state, started, time.monotonic_ns(), peak))
                del active[name]
            else:
                active[name] = (spec, process, stdout_handle, stderr_handle, started, peak)
        time.sleep(0.02)
    return sorted(results, key=lambda row: row.name)


def _diagnostic_record(producers: Sequence[ProcessResult], checkers: Sequence[ProcessResult]) -> dict[str, Any]:
    return {
        "checker_processes": [row.__dict__ for row in checkers],
        "producer_overlap": bool(producers) and min(row.ended_ns for row in producers) > max(row.started_ns for row in producers),
        "producer_processes": [row.__dict__ for row in producers],
    }


def run_cycle(repository_root: Path, contract_path: Path, contract_sha256: str, output_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    contract = common.validate_contract(root, contract_path, contract_sha256)
    target = output_root.resolve()
    target.mkdir(parents=True, exist_ok=False)
    progress = target / "progress.log"
    progress.write_text("INITIALIZED\n", encoding="utf-8", newline="\n")
    cases_dir = root / "docs" / "reference_cases"
    python = Path(sys.executable).resolve()
    deadline = time.monotonic() + contract["execution"]["global_timeout_seconds"]
    producer_specs: list[ProcessSpec] = []
    for shard in contract["domain"]["root_shards"]:
        shard_id = shard["shard_id"]
        directory = target / "producers" / shard_id
        output = directory / "proof.json"
        command = (
            str(python), str(cases_dir / "e4_pl_q1g_domain_producer.py"), "--emit-domain-proof",
            "--repository-root", str(root), "--contract", str(contract_path.resolve()),
            "--contract-sha256", contract_sha256.upper(), "--shard-id", shard_id, "--output", str(output),
        )
        producer_specs.append(ProcessSpec(shard_id, command, directory, output))
    producers = _run_wave(producer_specs, contract["execution"]["producer_timeout_seconds"], contract["execution"]["memory_limit_gib"] * 1024**3, deadline)
    progress.write_text(progress.read_text(encoding="utf-8") + "PRODUCERS_TERMINAL\n", encoding="utf-8", newline="\n")
    checker_specs: list[ProcessSpec] = []
    for spec, result in zip(producer_specs, producers):
        if result.state != "COMPLETE":
            continue
        for replica in range(2):
            directory = target / "checkers" / spec.name / f"replica_{replica + 1}"
            output = directory / "check.json"
            command = (
                str(python), str(cases_dir / "e4_pl_q1g_domain_checker.py"), "--verify-domain-proof",
                "--repository-root", str(root), "--contract", str(contract_path.resolve()),
                "--contract-sha256", contract_sha256.upper(), "--proof", str(spec.output),
                "--replica-id", "REPLICA", "--output", str(output),
            )
            checker_specs.append(ProcessSpec(f"{spec.name}_R{replica + 1}", command, directory, output))
    checkers = _run_wave(checker_specs, contract["execution"]["producer_timeout_seconds"], contract["execution"]["memory_limit_gib"] * 1024**3, deadline) if checker_specs else []
    progress.write_text(progress.read_text(encoding="utf-8") + "CHECKERS_TERMINAL\n", encoding="utf-8", newline="\n")
    failures = [row.name for row in [*producers, *checkers] if row.state != "COMPLETE"]
    disagreements: list[str] = []
    proof_hashes: list[str] = []
    unresolved = 0
    negative = 0
    rigid_exact = True
    for spec in producer_specs:
        if not spec.output.is_file():
            continue
        proof_raw, proof = common.read_json(spec.output)
        proof_hashes.append(common.sha256(proof_raw))
        classification = proof["domain_leaf"]["classification"]
        unresolved += int(classification == "UNRESOLVED")
        negative += int(classification == "NEGATIVE")
        outputs = [target / "checkers" / spec.name / f"replica_{number}" / "check.json" for number in (1, 2)]
        if not all(path.is_file() for path in outputs):
            continue
        bytes_pair = [path.read_bytes() for path in outputs]
        if bytes_pair[0] != bytes_pair[1]:
            disagreements.append(spec.name)
        check = common.strict_json_bytes(bytes_pair[0])
        rigid_exact = rigid_exact and check["status"] == "PASS" and check["rigid_range_exact"] is True
    if failures or disagreements or len(proof_hashes) != 3 or len(checkers) != 6:
        terminal, classification = "BLOCKED_E4_PL_Q1G_PROOF_OR_NONDETERMINISM", "BLOCKED"
    elif negative:
        terminal, classification = "NO_GO_E4_PL_Q1G_DOMAIN_COERCIVITY", "NO_GO"
    elif unresolved:
        terminal, classification = "UNCLASSIFIED_E4_PL_Q1G_DOMAIN_COVERAGE", "UNCLASSIFIED"
    else:
        terminal, classification = "PROVISIONAL_GO_E4_PL_Q1G_DOMAIN_COERCIVITY_CLOSED", "PROVISIONAL_GO"
    aggregate = {
        "candidate_id": common.CANDIDATE_ID,
        "checker_agreement": {"byte_identical_pairs": len(disagreements) == 0 and len(checkers) == 6, "disagreements": disagreements, "replicas": len(checkers)},
        "classification": classification,
        "contract_sha256": contract_sha256.upper(),
        "coverage": {"domain_positive_leaves": 0, "domain_unresolved_leaves": unresolved, "proof_hashes": sorted(proof_hashes), "shards_completed": len(proof_hashes), "shards_registered": 3},
        "local_reduction": {"basis_change_nonsingular": rigid_exact, "coercivity_certified": terminal == "PROVISIONAL_GO_E4_PL_Q1G_DOMAIN_COERCIVITY_CLOSED", "h_kernel_certified": False, "rigid_range_exact": rigid_exact},
        "production":"NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "q1b_execution":"UNAUTHORIZED",
        "schema": AGGREGATE_SCHEMA,
        "study_id": common.STUDY_ID,
        "terminal": terminal,
    }
    common.write_exclusive(target / "aggregate.json", aggregate)
    (target / "run_diagnostics.json").write_text(json.dumps(_diagnostic_record(producers, checkers), sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
    progress.write_text(progress.read_text(encoding="utf-8") + "AGGREGATE_COMPLETE\n", encoding="utf-8", newline="\n")
    return aggregate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-bounded-domain", action="store_true")
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--contract-sha256", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.run_bounded_domain:
        return 2
    try:
        aggregate = run_cycle(args.repository_root, args.contract, args.contract_sha256, args.output_root)
    except common.Q1GError as exc:
        print(f"BLOCKED_E4_PL_Q1G_AUTHORITY_OR_REVIEW: {exc}", file=sys.stderr)
        return 2
    print(common.canonical_bytes(aggregate).decode("utf-8"), end="")
    return 0 if aggregate["classification"] != "BLOCKED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
