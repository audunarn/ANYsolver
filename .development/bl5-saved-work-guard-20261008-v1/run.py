"""One bounded saved-state virtual-work guard; no equilibrium or formal F03 run."""

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
source = root / "scripts/b3_e4_f03_saved_mode_patch_work.py"
saved = Path(
    "C:/Github/ANYsolver/.perf2-worktrees/b3-ge-e4-pl-coupling/"
    ".qualification/b3-ge-e4-pl/"
    "r7-f03-fy-saved-projection-dev-20260929-v1/source-mode.json")
output = here / "comparison-guarded.json"
assert not output.exists(), "preserve prior evidence"
saved_hash = hashlib.sha256(saved.read_bytes()).hexdigest()
assert saved_hash == "40aeaf34a38ffcf6cba5fcd7675597b1a18b86f48cf0fc9b62b11c53b3f4d19d"
env = os.environ.copy()
env.update({name: "1" for name in (
    "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS")})
env["NUMBA_DISABLE_JIT"] = "1"
env["PYTHONPATH"] = os.pathsep.join((str(root / "src"), str(root)))
temp = here / "tmp"
temp.mkdir(exist_ok=True)
env["TEMP"] = env["TMP"] = str(temp)
psutil.Process().cpu_affinity([0])
command = [sys.executable, "-m", "scripts.b3_e4_f03_saved_mode_patch_work",
           str(saved), str(output)]
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
        if peak_rss > 2 * 1024 ** 3 or time.perf_counter() - started > 30:
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
receipt = {
    "status": status, "exit_code": code, "command": command,
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "saved_input_sha256": saved_hash,
    "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
    "wall_seconds": wall, "process_cap_seconds": 30,
    "peak_sampled_process_tree_rss_bytes": peak_rss,
    "memory_cap_bytes": 2 * 1024 ** 3,
    "cpu_affinity_observed": psutil.Process().cpu_affinity(),
    "threads_requested": 1, "jit_disabled_requested": True,
    "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest() if output.exists() else None,
}
(here / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
if status != "COMPLETED" or code:
    raise RuntimeError(f"saved-state guard failed: {status}, exit {code}")
print(json.dumps({"status": "PASSED", "receipt": str(here / "receipt.json")}))
