"""One separately authorized post-face-correction BL5 diagnostic attempt."""

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
SOURCE = ROOT / "scripts/r8_bl5_mz_common_beam_action_dev.py"
FACE_SOURCE = ROOT / "scripts/r8_bl5_weak_continuum_reference.py"
REGISTRATION = HERE / "v5-registration.json"
RECEIPT = HERE / "receipt-v5.json"
LIMIT = 30.0
MAX_RSS = 2 * 1024**3

registration = json.loads(REGISTRATION.read_text(encoding="utf-8"))
if registration.get("status") != "AUTHORIZED":
    raise SystemExit("V5 authority is pending; do not execute")
if (registration.get("source_sha256") != hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        or registration.get("face_source_sha256") != hashlib.sha256(FACE_SOURCE.read_bytes()).hexdigest()):
    raise SystemExit("V5 source binding changed; do not execute")
if RECEIPT.exists() or (HERE / "stdout-v5.txt").exists() or (HERE / "case-v5").exists():
    raise SystemExit("attempt exists; preserve its evidence")
environment = os.environ.copy()
environment.update({name: "1" for name in (
    "NUMBA_DISABLE_JIT", "NUMBA_NUM_THREADS", "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS")})
process_self = psutil.Process()
process_self.cpu_affinity([0])
command = [sys.executable, "-I", str(SOURCE), "--output", str(HERE / "case-v5")]
start = time.perf_counter()
with (HERE / "stdout-v5.txt").open("wb") as stdout, (HERE / "stderr-v5.txt").open("wb") as stderr:
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
              face_source_sha256=hashlib.sha256(FACE_SOURCE.read_bytes()).hexdigest(),
              authority=registration.get("authority"),
              source_commit=subprocess.check_output(
                  ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              effective_cpu_affinity=process_self.cpu_affinity(),
              environment={key: environment[key] for key in (
                  "NUMBA_DISABLE_JIT", "NUMBA_NUM_THREADS", "OMP_NUM_THREADS",
                  "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS",
                  "VECLIB_MAXIMUM_THREADS")},
              process_wall_seconds=wall, process_cap_seconds=LIMIT,
              cumulative_allowance_seconds=30., prior_consumed_seconds=0.,
              consumed_seconds=wall, remaining_seconds=max(0., 30.-wall),
              sampled_peak_rss_bytes=peak, memory_limit_bytes=MAX_RSS,
              exit_code=exit_code, stop_reason=stop,
              output="case-v5/result.json" if (HERE / "case-v5/result.json").exists() else None,
              stdout="stdout-v5.txt", stderr="stderr-v5.txt")
RECEIPT.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
print(json.dumps({key: record[key] for key in (
    "process_wall_seconds", "remaining_seconds", "exit_code",
    "stop_reason", "sampled_peak_rss_bytes", "output")}))
raise SystemExit(0 if exit_code == 0 and not stop else 1)
