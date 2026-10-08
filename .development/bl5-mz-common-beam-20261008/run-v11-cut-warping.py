"""One bounded V11 development response check with immutable attempt evidence."""
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
REGISTRATION = HERE / "v11-cut-warping-registration.json"
SOURCE = ROOT / "scripts/r8_bl5_v11_cut_warping_response_dev.py"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    record = json.loads(REGISTRATION.read_text(encoding="utf-8"))
    if record["status"] != "AUTHORIZED" or record["runner_sha256"] != digest(__file__):
        raise SystemExit("V11 registration or runner binding changed")
    if record["source_sha256"] != digest(SOURCE):
        raise SystemExit("V11 source binding changed")
    for path, expected in record["inputs_sha256"].items():
        if digest(ROOT / path) != expected:
            raise SystemExit("V11 input binding changed: " + path)
    attempts = sorted(HERE.glob("receipt-v11-cut-warping-attempt-*.json"))
    ordinal = len(attempts) + 1
    if ordinal > record["max_attempts"]:
        raise SystemExit("V11 attempt limit exhausted")
    used = sum(json.loads(path.read_text())["process_wall_seconds"] for path in attempts)
    cap = min(record["process_cap_seconds"],
              record["cumulative_seconds"]-record["reserve_seconds"]-used)
    if cap <= 0:
        raise SystemExit("V11 cumulative allowance exhausted")
    output = HERE / f"case-v11-cut-warping-attempt-{ordinal}/result.json"
    if output.parent.exists():
        raise SystemExit("V11 attempt path already exists")
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
    stdout_path = HERE / f"stdout-v11-cut-warping-attempt-{ordinal}.txt"
    stderr_path = HERE / f"stderr-v11-cut-warping-attempt-{ordinal}.txt"
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
            if peak > record["memory_limit_bytes"]:
                reason = "memory_limit"
            elif time.perf_counter()-start >= cap:
                reason = "time_limit"
            if reason:
                for member in reversed(members):
                    try:
                        member.kill()
                    except psutil.Error:
                        pass
                break
            time.sleep(.05)
        exit_code = process.wait()
    wall = time.perf_counter()-start
    receipt = dict(command=command,cwd=str(ROOT),attempt=ordinal,
        registration_sha256=digest(REGISTRATION),source_sha256=digest(SOURCE),
        inputs_sha256=record["inputs_sha256"],effective_parent_affinity=parent.cpu_affinity(),
        environment={name:environment[name] for name in (
            "NUMBA_DISABLE_JIT", "NUMBA_NUM_THREADS", "OMP_NUM_THREADS",
            "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS")},process_wall_seconds=wall,
        cumulative_wall_seconds=used+wall,
        remaining_including_reserve_seconds=record["cumulative_seconds"]-used-wall,
        process_cap_seconds=cap,sampled_peak_process_tree_rss_bytes=peak,
        memory_limit_bytes=record["memory_limit_bytes"],exit_code=exit_code,
        stop_reason=reason,output=str(output.relative_to(HERE)) if output.exists() else None,
        stdout=stdout_path.name,stderr=stderr_path.name)
    (HERE/f"receipt-v11-cut-warping-attempt-{ordinal}.json").write_text(
        json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({key:receipt[key] for key in (
        "attempt","process_wall_seconds","exit_code","stop_reason","output")}))
    raise SystemExit(0 if exit_code == 0 and reason is None else 1)


if __name__ == "__main__":
    main()
