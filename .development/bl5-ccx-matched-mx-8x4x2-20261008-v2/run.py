"""One bounded matched Mx CalculiX deck preparation."""

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
source = root / "scripts/r8_bl5_ccx_matched_mx_deck_dev.py"
parent = root / ".development/bl5-mx-matched-refinement-20261008-v1/levels/8x4x2.json"
output = here / "case"
assert not output.exists() and not (here / "receipt.json").exists(), "preserve previous attempt"
env = os.environ.copy()
env.update({name: "1" for name in (
    "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS",
    "NUMBA_NUM_THREADS")})
env["NUMBA_DISABLE_JIT"] = "1"
env["PYTHONPATH"] = os.pathsep.join((str(root / "src"), str(root)))
temp = here / "tmp"
temp.mkdir(exist_ok=True)
env["TEMP"] = env["TMP"] = str(temp)
psutil.Process().cpu_affinity([0])
command = [sys.executable, "-m", "scripts.r8_bl5_ccx_matched_mx_deck_dev",
           "--independent", str(parent), "--output-dir", str(output)]
started = time.perf_counter()
peak_rss = 0
with (here / "stdout.log").open("wb") as stdout, (here / "stderr.log").open("wb") as stderr:
    process = subprocess.Popen(command, cwd=root, env=env, stdout=stdout, stderr=stderr)
    family = psutil.Process(process.pid)
    status = "COMPLETED"
    while process.poll() is None:
        try:
            peak_rss = max(peak_rss, sum(item.memory_info().rss for item in
                           [family, *family.children(recursive=True)]))
        except psutil.NoSuchProcess:
            pass
        if peak_rss > 2*1024**3 or time.perf_counter()-started > 60:
            status = "MEMORY_LIMIT" if peak_rss > 2*1024**3 else "TIMEOUT"
            try:
                for item in family.children(recursive=True):
                    item.kill()
                family.kill()
            except psutil.NoSuchProcess:
                pass
            break
        time.sleep(.05)
    code = process.wait()
wall = time.perf_counter()-started
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
levels = {p.name: sha(p) for p in sorted(output.glob("*")) if p.is_file()} if output.exists() else {}
receipt = {"status": status, "exit_code": code, "command": command,
           "source_sha256": sha(source), "parent_sha256": sha(parent),
           "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                     cwd=root, text=True).strip(),
           "wall_seconds": wall, "process_cap_seconds": 60,
           "cumulative_allowance_seconds": 120,
           "cumulative_used_seconds": wall,
           "cumulative_remaining_seconds": 120-wall,
           "peak_sampled_process_tree_rss_bytes": peak_rss,
           "memory_cap_bytes": 2*1024**3,
           "cpu_affinity_observed": psutil.Process().cpu_affinity(),
           "threads_requested": 1, "jit_disabled_requested": True,
           "case_file_sha256": levels}
(here / "receipt.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
if status != "COMPLETED" or code or set(levels) != {"weak.inp", "metadata.json"}:
    raise RuntimeError(f"matched deck preparation incomplete: {status}, exit {code}, levels {len(levels)}")
print(json.dumps({"status": "PASSED", "levels": len(levels),
                  "receipt": str(here / "receipt.json")}))
