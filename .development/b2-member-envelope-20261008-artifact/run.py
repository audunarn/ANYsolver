"""Bounded, serial installed-wheel development verification with retained receipts."""

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
python = Path(sys.executable).resolve()
wheel_dir = here / "wheel"
site = here / "site"
wheel_dir.mkdir(exist_ok=True)
site.mkdir(exist_ok=True)
psutil.Process().cpu_affinity([0])
env = os.environ.copy()
env.update({name: "1" for name in (
    "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS")})
env["NUMBA_DISABLE_JIT"] = "1"
temp_dir = here / "tmp"
temp_dir.mkdir(exist_ok=True)
env["TEMP"] = env["TMP"] = str(temp_dir)
budget = 180.0 - 16.1057862
reserve = 60.0
previous = json.loads((here / "receipt.json").read_text(encoding="utf-8"))
used = sum(item["wall_seconds"] for item in previous)
attempts = list(previous)


def run(name, command, cap):
    global used
    deadline = min(cap, budget - used - reserve)
    if deadline <= 0:
        raise RuntimeError("development verification reserve reached")
    started = time.perf_counter()
    with (here / f"{name}.stdout.log").open("wb") as stdout, (here / f"{name}.stderr.log").open("wb") as stderr:
        process = subprocess.Popen(command, cwd=here, env=env, stdout=stdout, stderr=stderr)
        status = "COMPLETED"
        peak_rss = 0
        family = psutil.Process(process.pid)
        while process.poll() is None:
            try:
                members = [family, *family.children(recursive=True)]
                peak_rss = max(peak_rss, sum(member.memory_info().rss for member in members))
            except psutil.NoSuchProcess:
                pass
            if peak_rss > 2 * 1024 ** 3 or time.perf_counter() - started > deadline:
                status = "MEMORY_LIMIT" if peak_rss > 2 * 1024 ** 3 else "TIMEOUT"
                try:
                    for child in family.children(recursive=True):
                        child.kill()
                    family.kill()
                except psutil.NoSuchProcess:
                    pass
                break
            time.sleep(0.05)
        code = process.wait()
    wall = time.perf_counter() - started
    used += wall
    record = {"name": name, "command": [str(arg) for arg in command],
              "status": status, "exit_code": code, "wall_seconds": wall,
              "cumulative_used_seconds": 16.1057862 + used,
              "cumulative_remaining_seconds": budget - used,
              "process_cap_seconds": deadline, "cpu_affinity_observed": psutil.Process().cpu_affinity(),
              "threads_requested": 1, "jit_disabled_requested": True,
              "memory_cap_bytes": 2 * 1024 ** 3, "peak_sampled_tree_rss_bytes": peak_rss}
    attempts.append(record)
    (here / "receipt-v2.json").write_text(json.dumps(attempts, indent=2), encoding="utf-8")
    if status != "COMPLETED" or code:
        raise RuntimeError(f"{name}: {status}, exit {code}")


run("build-v2", [python, "-m", "build", "--wheel", "--no-isolation", "--outdir", wheel_dir, root], 60)
wheels = tuple(wheel_dir.glob("*.whl"))
assert len(wheels) == 1
wheel = wheels[0]
run("install-v2", [python, "-m", "pip", "install", "--no-deps", "--target", site, wheel], 60)
run("probe-v2", [python, here / "installed_probe.py", site, wheel], 60)
(here / "identity.json").write_text(json.dumps({
    "wheel": wheel.name, "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
    "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip(),
    "product_sha256": hashlib.sha256((root / "src/anysolver/_stiffened_shell_b2_q4_panel_experimental.py").read_bytes()).hexdigest(),
}, indent=2), encoding="utf-8")
print(json.dumps({"status": "PASSED", "identity": str(here / "identity.json"),
                  "receipt": str(here / "receipt-v2.json")}))
