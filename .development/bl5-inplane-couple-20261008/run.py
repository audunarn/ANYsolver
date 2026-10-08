"""Bound one BL5 development probe and retain precise execution evidence."""

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
PROBE = HERE / "probe.py"
RECEIPT = HERE / "receipt.json"
TIME_LIMIT = 60.0
MEMORY_LIMIT = 2 * 1024**3

if RECEIPT.exists() or (HERE / "stdout.txt").exists():
    raise SystemExit("Existing attempt evidence must be preserved")

environment = os.environ.copy()
environment.update({
    "NUMBA_DISABLE_JIT": "1",
    "NUMBA_NUM_THREADS": "1",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
    "BLIS_NUM_THREADS": "1",
})
command = [sys.executable, "-I", str(PROBE)]
start = time.perf_counter()
with (HERE / "stdout.txt").open("wb") as stdout, (HERE / "stderr.txt").open("wb") as stderr:
    process = subprocess.Popen(command, cwd=ROOT, env=environment,
                               stdout=stdout, stderr=stderr)
    observed_peak = 0
    stop_reason = None
    while process.poll() is None:
        owner = psutil.Process(process.pid)
        try:
            members = [owner, *owner.children(recursive=True)]
            observed_peak = max(observed_peak, sum(
                p.memory_info().rss for p in members if p.is_running()))
        except psutil.Error:
            pass
        if observed_peak > MEMORY_LIMIT:
            stop_reason = "memory_limit"
        elif time.perf_counter() - start >= TIME_LIMIT:
            stop_reason = "time_limit"
        if stop_reason:
            try:
                for child in owner.children(recursive=True):
                    child.kill()
                owner.kill()
            except psutil.Error:
                pass
            break
        time.sleep(0.05)
    exit_code = process.wait()
elapsed = time.perf_counter() - start
receipt = {
    "candidate_commit": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "probe_sha256": hashlib.sha256(PROBE.read_bytes()).hexdigest(),
    "command": command,
    "cwd": str(ROOT),
    "effective_affinity": psutil.Process().cpu_affinity(),
    "environment": {key: environment[key] for key in (
        "NUMBA_DISABLE_JIT", "NUMBA_NUM_THREADS", "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS", "BLIS_NUM_THREADS")},
    "wall_seconds": elapsed,
    "limit_seconds": TIME_LIMIT,
    "allowance_seconds": 90.0,
    "reserve_seconds": 30.0,
    "remaining_seconds": max(0.0, 90.0 - elapsed),
    "memory_limit_bytes": MEMORY_LIMIT,
    "observed_peak_rss_bytes": observed_peak,
    "exit_code": exit_code,
    "stop_reason": stop_reason,
    "stdout": "stdout.txt",
    "stderr": "stderr.txt",
    "result": "result.json" if (HERE / "result.json").exists() else None,
}
RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: receipt[key] for key in (
    "wall_seconds", "remaining_seconds", "exit_code", "stop_reason",
    "observed_peak_rss_bytes", "result")}))
raise SystemExit(0 if exit_code == 0 and not stop_reason else 1)
