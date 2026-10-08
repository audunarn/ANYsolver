"""Bounded V10 development diagnostic supervisor; registration grants scope."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REGISTRATION = HERE / "v10-nodal-warping-registration-v2.json"
SOURCE = ROOT / "scripts/r8_bl5_nodal_port_and_warping_dev.py"
LIMIT = 30.0
MAX_RSS = 2 * 1024**3


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    record = json.loads(REGISTRATION.read_text(encoding="utf-8"))
    if record["status"] != "AUTHORIZED" or record["runner_sha256"] != digest(Path(__file__)):
        raise SystemExit("registration or runner binding changed")
    if record["source_sha256"] != digest(SOURCE):
        raise SystemExit("source binding changed")
    for path, expected in record["inputs_sha256"].items():
        if digest(ROOT / path) != expected:
            raise SystemExit("input binding changed: " + path)
    attempts = sorted(HERE.glob("receipt-v10-nodal-warping-attempt-*.json"))
    ordinal = len(attempts) + 1
    if ordinal > record["max_attempts"]:
        raise SystemExit("attempt limit exhausted")
    elapsed = sum(json.loads(p.read_text())["process_wall_seconds"] for p in attempts)
    remaining = record["cumulative_seconds"] - record["reserve_seconds"] - elapsed
    if remaining <= 0.:
        raise SystemExit("cumulative budget exhausted")
    cap = min(LIMIT, remaining)
    output = HERE / f"case-v10-nodal-warping-attempt-{ordinal}/result.json"
    if output.parent.exists():
        raise SystemExit("attempt path already exists")
    output.parent.mkdir(parents=True)
    environment = os.environ.copy()
    environment.update({name: "1" for name in (
        "NUMBA_DISABLE_JIT", "NUMBA_NUM_THREADS", "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS")})
    parent = psutil.Process()
    parent.cpu_affinity([0])
    command = [sys.executable, "-I", str(SOURCE), "--output", str(output)]
    start = time.perf_counter()
    peak, reason = 0, None
    stdout_path = HERE / f"stdout-v10-nodal-warping-attempt-{ordinal}.txt"
    stderr_path = HERE / f"stderr-v10-nodal-warping-attempt-{ordinal}.txt"
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        process = subprocess.Popen(command, cwd=ROOT, env=environment,
                                   stdout=stdout, stderr=stderr)
        while process.poll() is None:
            try:
                owner = psutil.Process(process.pid)
                members = [owner, *owner.children(recursive=True)]
                peak = max(peak, sum(p.memory_info().rss for p in members
                                     if p.is_running()))
            except psutil.Error:
                members = []
            if peak > MAX_RSS:
                reason = "memory_limit"
            elif time.perf_counter() - start >= cap:
                reason = "time_limit"
            if reason:
                for p in reversed(members):
                    try:
                        p.kill()
                    except psutil.Error:
                        pass
                break
            time.sleep(.05)
        exit_code = process.wait()
    wall = time.perf_counter() - start
    receipt = dict(command=command, cwd=str(ROOT), attempt=ordinal,
        registration_sha256=digest(REGISTRATION), source_sha256=digest(SOURCE),
        inputs_sha256=record["inputs_sha256"], effective_parent_affinity=parent.cpu_affinity(),
        environment={name: environment[name] for name in (
            "NUMBA_DISABLE_JIT", "NUMBA_NUM_THREADS", "OMP_NUM_THREADS",
            "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS")}, process_wall_seconds=wall,
        cumulative_wall_seconds=elapsed+wall,
        remaining_including_reserve_seconds=record["cumulative_seconds"]-elapsed-wall,
        process_cap_seconds=cap, sampled_peak_process_tree_rss_bytes=peak,
        memory_limit_bytes=MAX_RSS, exit_code=exit_code, stop_reason=reason,
        output=str(output.relative_to(HERE)) if output.exists() else None,
        stdout=stdout_path.name, stderr=stderr_path.name)
    receipt_path = HERE / f"receipt-v10-nodal-warping-attempt-{ordinal}.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in (
        "attempt", "process_wall_seconds", "exit_code", "stop_reason", "output")}))
    raise SystemExit(0 if exit_code == 0 and reason is None else 1)


if __name__ == "__main__":
    main()
