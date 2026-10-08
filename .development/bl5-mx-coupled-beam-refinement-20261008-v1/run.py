"""One bounded three-level fixed-shell weak-P0 coupled Mx beam-refinement batch."""

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
source = root / "scripts/r8_bl5_mx_coupled_body_refinement_dev.py"
parent = root / ".development/bl5-saved-local-transfer-20261008-v3/local-transfer.json"
torsion = root / ".development/bl5-mx-torsion-refinement-20261008-v1"
output = here / "levels"
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
command = [sys.executable, "-m", "scripts.r8_bl5_mx_coupled_body_refinement_dev",
           "--prior", str(parent), "--torsion-dir", str(torsion), "--output-dir", str(output)]
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
        if peak_rss > 2*1024**3 or time.perf_counter()-started > 180:
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
levels = {p.name: sha(p) for p in sorted(output.glob("*.json"))} if output.exists() else {}
receipt = {"status": status, "exit_code": code, "command": command,
           "source_sha256": sha(source), "parent_sha256": sha(parent),
           "torsion_receipt_sha256": sha(torsion / "receipt.json"),
           "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                     cwd=root, text=True).strip(),
           "wall_seconds": wall, "process_cap_seconds": 180,
           "cumulative_allowance_seconds": 240,
           "cumulative_used_seconds": wall,
           "cumulative_remaining_seconds": 240-wall,
           "peak_sampled_process_tree_rss_bytes": peak_rss,
           "memory_cap_bytes": 2*1024**3,
           "cpu_affinity_observed": psutil.Process().cpu_affinity(),
           "threads_requested": 1, "jit_disabled_requested": True,
           "level_output_sha256": levels}
(here / "receipt.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
if status != "COMPLETED" or code or len(levels) != 3:
    raise RuntimeError(f"coupled beam refinement incomplete: {status}, exit {code}, levels {len(levels)}")
print(json.dumps({"status": "PASSED", "levels": len(levels),
                  "receipt": str(here / "receipt.json")}))
