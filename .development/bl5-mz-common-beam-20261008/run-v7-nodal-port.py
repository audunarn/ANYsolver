"""One guarded saved-solution nodal-port diagnostic; no authority in this file."""

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
REGISTRATION = HERE / "v7-nodal-port-registration.json"
RECEIPT = HERE / "receipt-v7-nodal-port.json"
SOURCE = ROOT / "scripts/r8_bl5_saved_nodal_port_dev.py"
OUTPUT = HERE / "case-v7-nodal-port/result.json"
LIMIT = 30.0
MAX_RSS = 2 * 1024**3


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    registration = json.loads(REGISTRATION.read_text(encoding="utf-8"))
    if registration.get("status") != "AUTHORIZED":
        raise SystemExit("V7 authority is pending; do not execute")
    if registration["runner_sha256"] != digest(Path(__file__)):
        raise SystemExit("V7 runner binding changed; do not execute")
    head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if (subprocess.run(["git", "merge-base", "--is-ancestor",
                        registration["source_commit"], head],
                       cwd=ROOT, check=False).returncode != 0 or
            registration["source_sha256"] != digest(SOURCE)):
        raise SystemExit("V7 source binding changed; do not execute")
    for relative, expected in registration["input_sha256"].items():
        path = ROOT / relative
        if not path.is_file() or digest(path) != expected:
            raise SystemExit("V7 saved input changed: " + relative)
    if RECEIPT.exists() or OUTPUT.exists() or OUTPUT.parent.exists():
        raise SystemExit("V7 attempt exists; preserve its evidence")
    if (registration["process_cap_seconds"] != LIMIT or
            registration["memory_limit_bytes"] != MAX_RSS):
        raise SystemExit("V7 resource binding changed")

    environment = os.environ.copy()
    environment.update({name: "1" for name in (
        "NUMBA_DISABLE_JIT", "NUMBA_NUM_THREADS", "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS")})
    parent = psutil.Process()
    parent.cpu_affinity([0])
    OUTPUT.parent.mkdir(parents=True)
    command = [sys.executable, "-I", str(SOURCE), "--output", str(OUTPUT)]
    start = time.perf_counter()
    peak = 0
    stop = None
    with (HERE / "stdout-v7-nodal-port.txt").open("wb") as stdout, (
            HERE / "stderr-v7-nodal-port.txt").open("wb") as stderr:
        process = subprocess.Popen(command, cwd=ROOT, env=environment,
                                   stdout=stdout, stderr=stderr)
        while process.poll() is None:
            try:
                owner = psutil.Process(process.pid)
                members = [owner, *owner.children(recursive=True)]
                peak = max(peak, sum(item.memory_info().rss for item in members
                                     if item.is_running()))
            except psutil.Error:
                members = []
            if peak > MAX_RSS:
                stop = "memory_limit"
            elif time.perf_counter() - start >= LIMIT:
                stop = "time_limit"
            if stop:
                for item in reversed(members):
                    try:
                        item.kill()
                    except psutil.Error:
                        pass
                break
            time.sleep(.05)
        exit_code = process.wait()
    wall = time.perf_counter() - start
    record = dict(command=command, cwd=str(ROOT),
                  source_commit=registration["source_commit"], actual_head=head,
                  source_sha256=digest(SOURCE),
                  registration_sha256=digest(REGISTRATION),
                  input_sha256=registration["input_sha256"],
                  effective_parent_affinity=parent.cpu_affinity(),
                  environment={key: environment[key] for key in (
                      "NUMBA_DISABLE_JIT", "NUMBA_NUM_THREADS", "OMP_NUM_THREADS",
                      "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "BLIS_NUM_THREADS",
                      "VECLIB_MAXIMUM_THREADS")},
                  process_wall_seconds=wall, process_cap_seconds=LIMIT,
                  sampled_peak_process_tree_rss_bytes=peak,
                  memory_limit_bytes=MAX_RSS, exit_code=exit_code,
                  stop_reason=stop,
                  output="case-v7-nodal-port/result.json" if OUTPUT.exists() else None,
                  stdout="stdout-v7-nodal-port.txt",
                  stderr="stderr-v7-nodal-port.txt")
    RECEIPT.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: record[key] for key in (
        "process_wall_seconds", "exit_code", "stop_reason",
        "sampled_peak_process_tree_rss_bytes", "output")}))
    raise SystemExit(0 if exit_code == 0 and stop is None else 1)


if __name__ == "__main__":
    main()
