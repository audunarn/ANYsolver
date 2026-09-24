"""Resource-bounded exploratory 64/128/256-grid classical F03 comparison.

The child owns one sparse solve. Raw stdout, stderr, status and sampled RSS
stay in a new output directory even if the case fails or exceeds the limit.
This is development evidence, not a formal F03 assessment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import numpy as np
import psutil
import scipy


MAX_RSS = 8*1024**3
MAX_SECONDS = 300
SOURCE = (
    "b3_e4_f03_classical_axial_guarded.py",
    "b3_e4_f03_classical_axial_refinement.py",
    "_b3_e4_f03_independent_coupled.py",
    "_b3_e4_f03_independent_shell.py",
    "_b3_e4_f03_independent_beam.py",
    "_b3_e4_f03_independent_line.py",
)
CHILD_CODE = (
    "import json,sys; "
    "from scripts.b3_e4_f03_classical_axial_refinement import one_case; "
    "print(json.dumps(one_case(sys.argv[1],int(sys.argv[2]),equilibrate=True),"
    "sort_keys=True,allow_nan=False))"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--topology", required=True, choices=("Q4", "CST"))
    parser.add_argument("--n", required=True, type=int, choices=(64, 128, 256))
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    root.mkdir(parents=True, exist_ok=False)
    source_dir = Path(__file__).resolve().parent
    command = [sys.executable, "-B", "-c", CHILD_CODE,
               args.topology, str(args.n)]
    environment = os.environ.copy()
    environment.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1",
                       MKL_NUM_THREADS="1", NUMBA_NUM_THREADS="1")
    manifest = dict(
        purpose="UNREGISTERED_RESOURCE_BOUNDED_CLASSICAL_F03_DIAGNOSTIC",
        source_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True).strip(),
        source_sha256={name: hashlib.sha256((source_dir/name).read_bytes()).hexdigest()
                       for name in SOURCE},
        topology=args.topology, n=args.n, command=command,
        sampled_rss_limit_bytes=MAX_RSS, wall_limit_seconds=MAX_SECONDS,
        memory_sampling_seconds=.1, threads=1,
        python=platform.python_version(), numpy=np.__version__,
        scipy=scipy.__version__, psutil=psutil.__version__,
        limitations=("sampled RSS is not a hard peak", "classical planar model",
                     "not native B3-GE/E4-PL", "not formal F03 assessment"))
    (root/"manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n",
                                      encoding="utf-8")
    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    process = subprocess.Popen(
        command, cwd=source_dir.parent, env=environment,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        creationflags=creationflags)
    observed = psutil.Process(process.pid)
    started = time.monotonic()
    peak = 0
    failure = None
    try:
        while process.poll() is None:
            try:
                peak = max(peak, observed.memory_info().rss)
            except psutil.NoSuchProcess:
                pass
            if peak > MAX_RSS:
                failure = "sampled child RSS exceeded 8 GiB"
                process.terminate()
                break
            if time.monotonic()-started > MAX_SECONDS:
                failure = "child exceeded 300 seconds"
                process.terminate()
                break
            time.sleep(.1)
        try:
            stdout, stderr = process.communicate(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            failure = "child failed to stop within 15 seconds"
    except BaseException as exc:
        if process.poll() is None:
            process.terminate()
            try:
                stdout, stderr = process.communicate(timeout=15)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
        else:
            stdout, stderr = process.communicate()
        failure = f"supervisor exception: {type(exc).__name__}: {exc}"
    (root/"stdout.json").write_text(stdout, encoding="utf-8")
    (root/"stderr.txt").write_text(stderr, encoding="utf-8")
    status = dict(exit_code=process.returncode, failure=failure,
                  sampled_peak_child_rss_bytes=peak,
                  elapsed_seconds=time.monotonic()-started)
    if failure is None and process.returncode == 0:
        try:
            result = json.loads(stdout)
            if (result["status"] != "UNREGISTERED_CLASSICAL_AXIAL_REFERENCE_DIAGNOSTIC"
                    or result["topology"] != args.topology
                    or result["shell_hosts"] != args.n
                    or result["numerical_solver"] !=
                    "symmetric_row_equilibration_6_passes"):
                raise ValueError("child result identity mismatch")
            (root/"result.json").write_text(
                json.dumps(result, indent=2, sort_keys=True)+"\n",
                encoding="utf-8")
            status["status"] = "EXPLORATORY_COMPLETE"
        except (ValueError, KeyError, TypeError) as exc:
            status.update(status="EXPLORATORY_FAILURE",
                          failure=f"invalid child result: {exc}")
    else:
        status.update(status="EXPLORATORY_FAILURE",
                      failure=failure or "child exited nonzero")
    (root/"status.json").write_text(json.dumps(status, indent=2, sort_keys=True)+"\n",
                                    encoding="utf-8")
    print(json.dumps(status, sort_keys=True))
    return 0 if status["status"] == "EXPLORATORY_COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
