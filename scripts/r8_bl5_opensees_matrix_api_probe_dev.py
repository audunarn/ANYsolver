"""Bounded toy OpenSees matrix/DOF API discriminator; no BL5 model is solved."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

SITE = Path(r"C:\Python\Python314\Lib\site-packages")
PYTHON = Path(r"C:\Users\AudunArnesenNyhus\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe")
MAX_WALL = 30.0
MAX_RSS = 2 * 1024**3
ENV_KEYS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
            "NUMBA_NUM_THREADS", "NUMBA_DISABLE_JIT")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def child(out: Path) -> None:
    sys.path.insert(0, str(SITE))
    import psutil
    import openseespy.opensees as ops
    from openseespywin import opensees as core

    result = {"probe": "three-node two-spring one-SP one-MP FullGeneral V1",
              "python": sys.version, "python_executable": sys.executable,
              "opensees_version": ops.version(), "binary": str(Path(core.__file__).resolve()),
              "binary_sha256": sha(Path(core.__file__)),
              "affinity": psutil.Process().cpu_affinity(),
              "environment": {key: os.environ.get(key) for key in ENV_KEYS}}
    try:
        ops.wipe()
        ops.model("basic", "-ndm", 1, "-ndf", 1)
        for tag in (1, 2, 3):
            ops.node(tag, 0.0)
        ops.uniaxialMaterial("Elastic", 1, 100.0)
        ops.element("zeroLength", 1, 1, 2, "-mat", 1, "-dir", 1)
        ops.element("zeroLength", 2, 1, 3, "-mat", 1, "-dir", 1)
        ops.fix(1, 1)
        ops.equalDOF(2, 3, 1)
        ops.timeSeries("Linear", 1)
        ops.pattern("Plain", 1, 1)
        ops.load(3, 10.0)
        ops.constraints("Lagrange", 1e9, 1e9)
        ops.numberer("RCM")
        ops.system("FullGeneral")
        ops.test("NormUnbalance", 1e-8, 20)
        ops.algorithm("Linear")
        ops.integrator("LoadControl", 1.0)
        ops.analysis("Static")
        result["analyze_code"] = int(ops.analyze(1))
        result["system_size"] = int(ops.systemSize())
        result["node_dofs"] = {str(tag): list(ops.nodeDOFs(tag)) for tag in (1, 2, 3)}
        result["node_disp"] = {str(tag): list(ops.nodeDisp(tag)) for tag in (1, 2, 3)}
        matrix = ops.printA("-ret")
        result["printA_type"] = type(matrix).__name__
        result["printA"] = (None if matrix is None else
                            [float(value) for value in matrix])
        result["status"] = "api_returned"
    except BaseException as exc:
        result["status"] = "api_failure"
        result["error"] = {"type": type(exc).__name__, "message": str(exc),
                           "traceback": traceback.format_exc()}
    finally:
        save(out, result)
        ops.wipe()


def supervise(folder: Path) -> None:
    if folder.exists():
        raise FileExistsError("unique output directory required")
    folder.mkdir(parents=True)
    sys.path.insert(0, str(SITE))
    import psutil

    psutil.Process().cpu_affinity([0])
    env = os.environ.copy()
    env.update({"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1",
                "MKL_NUM_THREADS": "1", "NUMBA_NUM_THREADS": "1", "NUMBA_DISABLE_JIT": "1"})
    cmd = [str(PYTHON), "-u", str(Path(__file__).resolve()), "--child",
           "--raw", str(folder / "raw.json")]
    reason, peak_rss, peak_threads, observed_affinity = None, 0, 0, None
    started = time.perf_counter()
    with (folder / "stdout.log").open("wb") as stdout, (folder / "stderr.log").open("wb") as stderr:
        proc = subprocess.Popen(cmd, cwd=Path(__file__).resolve().parents[1],
                                env=env, stdout=stdout, stderr=stderr)
        process = psutil.Process(proc.pid)
        try:
            while proc.poll() is None:
                elapsed = time.perf_counter() - started
                try:
                    tree = [process] + process.children(recursive=True)
                    rss = sum(p.memory_info().rss for p in tree if p.is_running())
                    threads = sum(p.num_threads() for p in tree if p.is_running())
                    observed_affinity = process.cpu_affinity()
                    peak_rss, peak_threads = max(peak_rss, rss), max(peak_threads, threads)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                if elapsed >= MAX_WALL or peak_rss > MAX_RSS:
                    reason = "timeout" if elapsed >= MAX_WALL else "memory_limit"
                    for p in process.children(recursive=True):
                        try:
                            p.kill()
                        except psutil.NoSuchProcess:
                            pass
                    try:
                        process.kill()
                    except psutil.NoSuchProcess:
                        pass
                    break
                time.sleep(0.01)
            proc.wait(timeout=3)
        finally:
            elapsed = time.perf_counter() - started
    raw = folder / "raw.json"
    receipt = {"source_sha256": sha(Path(__file__)), "command": cmd,
               "requested_environment": {key: env[key] for key in ENV_KEYS},
               "child_affinity_observed": observed_affinity,
               "process_wall_seconds": elapsed, "peak_process_tree_rss_bytes": peak_rss,
               "peak_process_tree_threads": peak_threads, "max_wall_seconds": MAX_WALL,
               "max_process_tree_rss_bytes": MAX_RSS, "exit_code": proc.returncode,
               "status": reason or ("completed" if proc.returncode == 0 and raw.exists() else "failed"),
               "raw_sha256": sha(raw) if raw.exists() else None}
    save(folder / "receipt.json", receipt)
    print(json.dumps({key: receipt[key] for key in ("status", "process_wall_seconds",
                     "peak_process_tree_rss_bytes", "peak_process_tree_threads", "exit_code")}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--raw", type=Path)
    args = parser.parse_args()
    if args.child:
        if args.raw is None:
            raise ValueError("child output required")
        child(args.raw)
    elif args.output is not None:
        supervise(args.output)
    else:
        raise ValueError("unique output directory required")
