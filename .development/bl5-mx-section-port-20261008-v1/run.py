"""One bounded saved C3D20 Mx root/traction section-port contrast."""

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
source = root / "scripts/r8_bl5_mx_section_port_dev.py"
prior = root / ".development/bl5-mx-beam-only-20261008-v5/result.json"
saved = root / ".development/bl5-ccx-weak-p0-20261008-mx-v2"
output = here / "contrast.json"
assert not output.exists(), "preserve prior screen"
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
command = [sys.executable, "-m", "scripts.r8_bl5_mx_section_port_dev",
           "--saved", str(saved), "--earlier", str(prior), "--output", str(output)]
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
        if peak_rss > 2 * 1024 ** 3 or time.perf_counter() - started > 90:
            status = "MEMORY_LIMIT" if peak_rss > 2 * 1024 ** 3 else "TIMEOUT"
            try:
                for item in family.children(recursive=True):
                    item.kill()
                family.kill()
            except psutil.NoSuchProcess:
                pass
            break
        time.sleep(0.05)
    code = process.wait()
wall = time.perf_counter() - started
receipt = {"status": status, "exit_code": code, "command": command,
           "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
           "prior_sha256": hashlib.sha256(prior.read_bytes()).hexdigest(),
           "saved_deck_sha256": hashlib.sha256((saved / "weak.inp").read_bytes()).hexdigest(),
           "saved_metadata_sha256": hashlib.sha256((saved / "metadata.json").read_bytes()).hexdigest(),
           "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
           "wall_seconds": wall, "process_cap_seconds": 90,
           "cumulative_allowance_seconds": 120,
           "cumulative_used_seconds": wall,
           "cumulative_remaining_seconds": 120 - wall,
           "peak_sampled_process_tree_rss_bytes": peak_rss,
           "memory_cap_bytes": 2 * 1024 ** 3,
           "cpu_affinity_observed": psutil.Process().cpu_affinity(),
           "threads_requested": 1, "jit_disabled_requested": True,
           "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest() if output.exists() else None}
(here / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
if status != "COMPLETED" or code:
    raise RuntimeError(f"section-port contrast failed: {status}, exit {code}")
print(json.dumps({"status": "PASSED", "receipt": str(here / "receipt.json")}))
