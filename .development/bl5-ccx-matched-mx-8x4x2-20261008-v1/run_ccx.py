"""One bounded pinned CalculiX execution for the prepared matched Mx deck."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import psutil


here = Path(__file__).resolve().parent
case = here / "case"
ccx = Path("C:/Github/ANYsolver/.qualification/b3-ge-e4-pl/calculix-223/CalculiX-2.23.0-win-x64/bin/ccx.exe")
expected_binary = "27a9426a1ee2f72c38fbe892e0ffaf38e14867628ffd0235770261b6f3ec9c5f"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
metadata = json.loads((case / "metadata.json").read_text(encoding="utf-8"))
prepared = json.loads((here / "receipt.json").read_text(encoding="utf-8"))
if (not ccx.is_file() or sha(ccx) != expected_binary or
        metadata["status"] != "PREPARED_NOT_EXECUTED" or
        sha(case / "weak.inp") != metadata["deck_sha256"] or
        sha(case / "weak.inp") != prepared["case_file_sha256"]["weak.inp"] or
        sha(case / "metadata.json") != prepared["case_file_sha256"]["metadata.json"] or
        prepared["status"] != "COMPLETED" or prepared["exit_code"] != 0 or
        (case / "ccx.receipt.json").exists() or (case / "weak.frd").exists()):
    raise ValueError("exact unconsumed prepared deck and pinned executable required")
env = os.environ.copy()
env.update({name: "1" for name in (
    "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS",
    "NUMBA_NUM_THREADS", "NUMBA_DISABLE_JIT")})
windows = Path(env.get("SystemRoot", "C:/Windows"))
env["PATH"] = os.pathsep.join((str(ccx.parent), str(windows / "System32"), str(windows)))
psutil.Process().cpu_affinity([0])
command = [str(ccx), "-i", "weak"]
started = time.perf_counter()
peak = 0
with (case / "ccx.stdout.txt").open("wb") as stdout, (case / "ccx.stderr.txt").open("wb") as stderr:
    process = subprocess.Popen(command, cwd=case, env=env, stdout=stdout, stderr=stderr)
    family = psutil.Process(process.pid)
    status = "EXITED"
    while process.poll() is None:
        try:
            members = [family, *family.children(recursive=True)]
            peak = max(peak, sum(item.memory_info().rss for item in members))
        except psutil.NoSuchProcess:
            members = [family]
        if peak > 2*1024**3 or time.perf_counter()-started > 120:
            status = "MEMORY_LIMIT" if peak > 2*1024**3 else "TIME_LIMIT"
            for item in reversed(members):
                try:
                    item.kill()
                except psutil.NoSuchProcess:
                    pass
            break
        time.sleep(.05)
    code = process.wait()
wall = time.perf_counter()-started
if code != 0 and status == "EXITED":
    status = "FAILED"
files = {p.name: sha(p) for p in case.glob("weak.*") if p.is_file()}
receipt = {"identity": "R8_BL5_CCX_MATCHED_MX_8X4X2_EXECUTION_DEV_V1",
           "status": status, "exit_code": code, "command": command,
           "cwd": str(case.resolve()), "executable_sha256": expected_binary,
           "deck_sha256": metadata["deck_sha256"],
           "prep_receipt_sha256": sha(here / "receipt.json"),
           "wall_seconds": wall, "process_cap_seconds": 120,
           "cumulative_allowance_seconds": 180,
           "cumulative_used_seconds": wall,
           "cumulative_remaining_seconds": 180-wall,
           "peak_sampled_process_tree_rss_bytes": peak,
           "memory_cap_bytes": 2*1024**3,
           "cpu_affinity_observed": psutil.Process().cpu_affinity(),
           "requested_threads": 1, "jit_disabled_requested": True,
           "environment": {name: env[name] for name in (
               "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
               "NUMBA_NUM_THREADS", "NUMBA_DISABLE_JIT", "PATH")},
           "file_sha256": files}
(case / "ccx.receipt.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
if status != "EXITED" or code:
    raise RuntimeError(f"pinned matched CalculiX execution failed: {status}, exit {code}")
print(json.dumps({"status": status, "exit_code": code,
                  "wall_seconds": wall, "files": sorted(files)}))
