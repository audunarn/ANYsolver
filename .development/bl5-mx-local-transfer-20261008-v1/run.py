"""One bounded same-body 80/160 row local work-transfer comparison."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil

here = Path(__file__).resolve().parent
root = here.parents[1]
source = root / "scripts/r8_bl5_mx_local_transfer_dev.py"
fine = root / ".development/bl5-mx-beam-interface-20261008-v1/result.json"
coarse = root / ".development/bl5-mx-interface-aggregation-20261008-v1/result.json"
output = here / "result.json"
receipt_path = here / "receipt.json"
if output.exists() or receipt_path.exists():
    raise FileExistsError("preserve previous local-transfer attempt")
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
env = os.environ.copy()
env.update({name: "1" for name in (
    "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS",
    "NUMBA_NUM_THREADS", "NUMBA_DISABLE_JIT")})
env["PYTHONPATH"] = os.pathsep.join((str(root / "src"), str(root)))
tmp = here / "tmp"
tmp.mkdir(exist_ok=True)
env["TEMP"] = env["TMP"] = str(tmp)
psutil.Process().cpu_affinity([0])
command = [sys.executable, "-m", "scripts.r8_bl5_mx_local_transfer_dev",
           "--fine", str(fine), "--coarse", str(coarse), "--output", str(output)]
started = time.perf_counter()
peak = 0
status = "START_FAILURE"
code = None
error = None
with (here / "stdout.log").open("wb") as stdout, (here / "stderr.log").open("wb") as stderr:
    try:
        process = subprocess.Popen(command, cwd=root, env=env, stdout=stdout, stderr=stderr)
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
    except OSError as exc:
        error = repr(exc)
wall = time.perf_counter()-started
receipt = {"identity": "R8_BL5_MX_LOCAL_TRANSFER_RUN_V1",
           "status": status, "exit_code": code, "launch_error": error,
           "command": command, "source_sha256": sha(source),
           "fine_result_sha256": sha(fine),
           "coarse_result_sha256": sha(coarse),
           "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                    cwd=root, text=True).strip(),
           "result_sha256": sha(output) if output.is_file() else None,
           "process_started": status != "START_FAILURE", "wall_seconds": wall,
           "process_cap_seconds": 120, "cumulative_allowance_seconds": 180,
           "cumulative_used_seconds": wall,
           "cumulative_remaining_seconds": 180-wall,
           "memory_cap_bytes": 2*1024**3, "peak_sampled_process_tree_rss_bytes": peak,
           "cpu_affinity_observed": psutil.Process().cpu_affinity(),
           "threads_requested": 1, "jit_disabled_requested": True}
receipt_path.write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
if status != "EXITED" or code:
    raise RuntimeError(f"local-transfer comparison incomplete: {status}, exit {code}, error {error}")
print(json.dumps({"status": "EXITED", "wall_seconds": wall,
                  "result_sha256": receipt["result_sha256"]}))
