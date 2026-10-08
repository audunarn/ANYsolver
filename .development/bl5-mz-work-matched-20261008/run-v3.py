"""One bounded source-development Mz comparison; preserve the sole attempt."""

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
SOURCE = ROOT / "scripts/r8_bl5_mz_work_matched_dev.py"
RECEIPT = HERE / "receipt-v3.json"
LIMIT = 60.0
MAX_RSS = 2 * 1024**3

if RECEIPT.exists() or (HERE / "stdout-v3.txt").exists():
    raise SystemExit("attempt exists; preserve its evidence")
environment = os.environ.copy()
environment.update({name: "1" for name in (
    "NUMBA_DISABLE_JIT", "NUMBA_NUM_THREADS", "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS")})
process_self = psutil.Process()
process_self.cpu_affinity([0])
command = [sys.executable, "-I", str(SOURCE), "--output", str(HERE / "case-v3")]
start = time.perf_counter()
with (HERE / "stdout-v3.txt").open("wb") as stdout, (HERE / "stderr-v3.txt").open("wb") as stderr:
    process = subprocess.Popen(command, cwd=ROOT, env=environment,
                               stdout=stdout, stderr=stderr)
    peak = 0
    stop = None
    while process.poll() is None:
        try:
            owner = psutil.Process(process.pid)
            members = [owner, *owner.children(recursive=True)]
            peak = max(peak, sum(p.memory_info().rss for p in members
                                 if p.is_running()))
        except psutil.Error:
            pass
        if peak > MAX_RSS:
            stop = "memory_limit"
        elif time.perf_counter() - start >= LIMIT:
            stop = "time_limit"
        if stop:
            try:
                for child in owner.children(recursive=True):
                    child.kill()
                owner.kill()
            except psutil.Error:
                pass
            break
        time.sleep(.05)
    exit_code = process.wait()
wall = time.perf_counter() - start
record = dict(command=command, cwd=str(ROOT),
              source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              source_commit=subprocess.check_output(
                  ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              effective_cpu_affinity=process_self.cpu_affinity(),
              environment={key: environment[key] for key in (
                  "NUMBA_DISABLE_JIT", "NUMBA_NUM_THREADS", "OMP_NUM_THREADS",
                  "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS",
                  "VECLIB_MAXIMUM_THREADS")},
              process_wall_seconds=wall, process_cap_seconds=LIMIT,
              cumulative_allowance_seconds=90., consumed_seconds=wall,
              remaining_seconds=max(0., 90.-wall), reserve_seconds=30.,
              sampled_peak_rss_bytes=peak, memory_limit_bytes=MAX_RSS,
              exit_code=exit_code, stop_reason=stop,
              output="case-v3/result.json" if (HERE / "case-v3/result.json").exists() else None,
              stdout="stdout-v3.txt", stderr="stderr-v3.txt")
RECEIPT.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: record[key] for key in (
    "process_wall_seconds", "remaining_seconds", "exit_code",
    "stop_reason", "sampled_peak_rss_bytes", "output")}))
raise SystemExit(0 if exit_code == 0 and not stop else 1)
