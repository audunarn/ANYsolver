"""One bounded, new 16x4 Fy FullGeneral BL5 operator development capture.

The archived BandGeneral recipe supplies every model/load command; only `system`
changes to FullGeneral. The parent supervises one child and retains its raw data.
This is neither a replay of the old one-use Mz case nor a formal F03 execution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

import r8_bl5_external_operator_dev as identity


ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(r"C:\Users\AudunArnesenNyhus\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe")
SITE = Path(r"C:\Python\Python314\Lib\site-packages")
MAX_WALL = 30.0
MAX_RSS = 2 * 1024**3
ENV = {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
       "NUMBA_NUM_THREADS": "1", "NUMBA_DISABLE_JIT": "1"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def candidate():
    spec = identity.fixture_preflight()
    recipe = identity.import_recipe()
    p0, frozen, service, reference, paths = recipe.services()
    model = recipe.geometry(16, reference)
    rows, supports = recipe.aggregate_rows(model, reference, p0)
    commands = identity.fullgeneral_commands(recipe, model, reference, rows, "fy")
    identity.require(identity.digest(commands) == spec["capture_commands_sha256"],
                     "FullGeneral command identity changed after preflight")
    return spec, recipe, p0, frozen, service, reference, model, rows, supports, commands


def supervisor_preflight() -> dict:
    sys.path.insert(0, str(SITE))
    import psutil
    identity.require(PYTHON.is_file() and SITE.is_dir(), "configured runtime/site absent")
    affinity = psutil.Process().cpu_affinity()
    identity.require(0 in affinity, "CPU0 unavailable to supervisor")
    return {"psutil_version": psutil.__version__, "available_affinity": affinity,
            "python_executable": str(PYTHON), "site": str(SITE)}


def child(raw_path: Path) -> None:
    result = {"status": "failed", "case": "fy", "capture_source_sha256": sha(Path(__file__)),
              "environment": {key: os.environ.get(key) for key in ENV},
              "python": sys.version, "python_executable": sys.executable}
    recorder = None
    try:
        spec, recipe, p0, frozen, service, reference, model, rows, supports, commands = candidate()
        identity.require(sys.version_info[:2] == (3, 12), "frozen OpenSees route requires Python 3.12")
        identity.require(all(result["environment"][key] == wanted for key, wanted in ENV.items()),
                         "one-thread/JIT-off environment missing")
        sys.path.insert(0, str(SITE))
        import psutil
        import openseespy.opensees as ops
        from openseespywin import opensees as core
        process = psutil.Process()
        result.update(affinity=process.cpu_affinity(), opensees_version=ops.version(),
                      binary=str(Path(core.__file__).resolve()),
                      binary_sha256=sha(Path(core.__file__)),
                      recipe_sha256=spec["recipe_sha256"],
                      capture_commands_sha256=spec["capture_commands_sha256"],
                      source_mechanics_sha256=spec["mechanics_sha256"])
        identity.require(result["affinity"] == [0], "CPU0 affinity required before model build")
        identity.require(result["binary_sha256"] == spec["binary_sha256"] and
                         result["opensees_version"].startswith("3.8"),
                         "verified OpenSees 3.8 binary required")
        recorder = service.RecordingOps(ops)
        recipe.solve(recorder, commands, model, reference)
        result["analyze_code"] = 0
        result["system_size"] = int(ops.systemSize())
        result["node_dofs"] = {str(node): list(ops.nodeDOFs(node)) for node in model["physical_node_order"]}
        matrix = ops.printA("-ret")
        result["printA_type"] = type(matrix).__name__
        result["printA"] = None if matrix is None else [float(value) for value in matrix]
        result["poses"] = recorder.raw["poses"]
        result["raw_inventory"] = recorder.raw
        result["status"] = "captured_unvalidated"
    except BaseException as error:
        result["failure"] = {"type": type(error).__name__, "message": str(error),
                             "traceback": traceback.format_exc()}
    finally:
        if recorder is not None:
            try:
                recorder.wipe()
            except BaseException as error:
                result["cleanup_failure"] = {"type": type(error).__name__, "message": str(error)}
                result["status"] = "failed"
        save(raw_path, result)
    if result["status"] != "captured_unvalidated":
        raise RuntimeError(result.get("failure", result.get("cleanup_failure", "capture failed")))


def numeric_difference(new, old):
    if isinstance(old, dict):
        identity.require(isinstance(new, dict) and set(new) == set(old), "saved observable keys differ")
        return [item for key in old for item in numeric_difference(new[key], old[key])]
    if isinstance(old, list):
        identity.require(isinstance(new, list) and len(new) == len(old), "saved observable shape differs")
        return [item for a, b in zip(new, old) for item in numeric_difference(a, b)]
    if isinstance(old, (int, float)) and not isinstance(old, bool):
        identity.require(isinstance(new, (int, float)) and math.isfinite(float(new)),
                         "nonfinite or absent physical observable")
        return [(abs(float(new)-float(old)), abs(float(old)))]
    identity.require(new == old, "non-numeric observable differs")
    return []


def parity(new, old, relative: float, floor: float, name: str):
    samples = numeric_difference(new, old)
    peak_error = max((x for x, _ in samples), default=0.0)
    scale = max((x for _, x in samples), default=0.0)
    limit = max(floor, relative*scale)
    identity.require(peak_error <= limit, f"{name} differs from saved BandGeneral: {peak_error} > {limit}")
    return {"max_abs_difference": peak_error, "saved_abs_scale": scale, "limit": limit,
            "numeric_entries": len(samples)}


def postprocess(folder: Path) -> dict:
    spec, recipe, p0, frozen, service, reference, model, rows, supports, commands = candidate()
    raw_path = folder / "raw.json"
    raw = json.loads(raw_path.read_text())
    receipt = json.loads((folder / "receipt.json").read_text())
    identity.require(receipt["status"] == "completed" and receipt["raw_sha256"] == sha(raw_path)
                     and receipt["source_sha256"] == raw["capture_source_sha256"],
                     "source-bound completed raw capture required")
    mapped = identity.validate_fullgeneral_capture(spec, raw)
    inventory = raw["raw_inventory"]
    expected = recipe.planned_inventory(commands)
    identity.require(all(identity.digest(inventory.get(key)) == identity.digest(
                     {str(k): v for k, v in wanted.items()} if isinstance(wanted, dict) else wanted)
                     for key, wanted in expected.items()),
                     "FullGeneral recorded commands/mechanics differ from single-system-change recipe")
    saved_dir = identity.FIXTURE / "fy"
    saved_raw = json.loads((saved_dir / "raw-inventory.json").read_text())
    checks = {"poses": parity(inventory["poses"], saved_raw["poses"], 1e-8, 1e-14, "poses"),
              "element_global_covectors": parity(inventory["element_global_covectors"],
                                                  saved_raw["element_global_covectors"],
                                                  1e-8, 1e-8, "element global covectors")}
    if saved_raw.get("unverified_node_reaction_queries"):
        checks["unverified_reaction_queries"] = parity(
            inventory["unverified_node_reaction_queries"], saved_raw["unverified_node_reaction_queries"],
            1e-8, 1e-8, "unverified reaction queries")
    # Independent linear-element consistency: the physical K applied to the
    # captured pose must equal the assembly of the recorded element covectors.
    ids = [raw["node_dofs"][str(node)][dof-1] for node, dof in spec["dof_order"]]
    m = spec["kkt_dimension"]
    flat = raw["printA"]
    u = [inventory["poses"][str(node)][dof-1] for node, dof in spec["dof_order"]]
    assembled = {tuple(pair): 0.0 for pair in spec["dof_order"]}
    for tag, element in inventory["elements"].items():
        forces = inventory["element_global_covectors"][tag]
        for slot, node in enumerate(element["nodes"]):
            for dof in range(1, 7):
                assembled[int(node), dof] += forces[6*slot+dof-1]
    residuals = [abs(math.fsum(flat[ids[i]*m+ids[j]]*u[j] for j in range(len(u))) - assembled[pair])
                 for i, pair in enumerate(spec["dof_order"])]
    force_scale = max(1.0, max(abs(v) for v in assembled.values()))
    identity.require(max(residuals) <= 1e-6*force_scale,
                     "physical K times captured pose differs from element force assembly")
    checks["physical_Ku_vs_element_forces"] = {"max_abs_residual": max(residuals),
                                               "force_scale": force_scale,
                                               "relative_limit": 1e-6}
    # Recompute the archived source's recovered physical actions from the new
    # raw force/pose inventory, preserving the derivation and saved comparison.
    runtime_inventory = dict(inventory)
    for key in ("nodes", "elements", "fixes", "loads", "poses",
                "element_global_covectors", "unverified_node_reaction_queries"):
        runtime_inventory[key] = {int(tag): value for tag, value in inventory[key].items()}
    recovery_dir = folder / "recovery-source-only"
    recovery_dir.mkdir(exist_ok=True)
    derived = recipe.recover(runtime_inventory, model, reference, rows, supports,
                             "fy", frozen, service, p0, recovery_dir)
    derived_saved_shape = json.loads(json.dumps(derived, allow_nan=False))
    save(recovery_dir / "recovered-actions.json", derived_saved_shape)
    saved_actions = json.loads((saved_dir / "recovered-actions.json").read_text())
    checks["recovered_physical_actions"] = parity(derived_saved_shape, saved_actions,
                                                   1e-8, 1e-8, "recovered physical actions")
    result = {"status": "development_capture_validated", "mapping": mapped, "parity": checks,
              "receipt_sha256": sha(folder / "receipt.json"), "raw_sha256": sha(raw_path),
              "classification": "one new 16x4 Fy FullGeneral development diagnostic; no F03/accuracy acceptance"}
    save(folder / "validation.json", result)
    return result


def supervise(folder: Path) -> None:
    if folder.exists():
        raise FileExistsError("fresh output directory required")
    spec, *_ = candidate()  # Source-only preflight before one external process.
    supervisor_preflight()
    import psutil
    folder.mkdir(parents=True)
    parent = psutil.Process()
    original_affinity = parent.cpu_affinity()
    parent.cpu_affinity([0])
    env = os.environ.copy()
    env.update(ENV)
    command = [str(PYTHON), "-u", str(Path(__file__).resolve()), "--child", "--raw", str(folder / "raw.json")]
    started = time.perf_counter()
    peak_rss, peak_threads, reason, affinity = 0, 0, None, None
    proc = None
    try:
        with (folder / "stdout.log").open("wb") as stdout, (folder / "stderr.log").open("wb") as stderr:
            proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                                    creationflags=0x4)
            child_process = psutil.Process(proc.pid)
            child_process.cpu_affinity([0])
            affinity = child_process.cpu_affinity()
            identity.require(affinity == [0], "child CPU0 affinity not established")
            child_process.resume()
            while proc.poll() is None:
                elapsed = time.perf_counter()-started
                try:
                    tree = [child_process]+child_process.children(recursive=True)
                    live = [p for p in tree if p.is_running()]
                    peak_rss = max(peak_rss, sum(p.memory_info().rss for p in live))
                    peak_threads = max(peak_threads, sum(p.num_threads() for p in live))
                    if any(p.cpu_affinity() != [0] for p in live):
                        reason = "affinity_changed"
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                if elapsed >= MAX_WALL or peak_rss > MAX_RSS:
                    reason = "timeout" if elapsed >= MAX_WALL else "memory_limit"
                if reason:
                    for p in reversed([child_process]+child_process.children(recursive=True)):
                        try:
                            p.kill()
                        except psutil.NoSuchProcess:
                            pass
                    break
                time.sleep(0.01)
            proc.wait(timeout=3)
    finally:
        elapsed = time.perf_counter()-started
        parent.cpu_affinity(original_affinity)
    raw_path = folder / "raw.json"
    receipt = {"status": reason or ("completed" if proc and proc.returncode == 0 and raw_path.exists() else "failed"),
               "command": command, "source_sha256": sha(Path(__file__)),
               "preflight_recipe_sha256": spec["recipe_sha256"],
               "preflight_commands_sha256": spec["capture_commands_sha256"],
               "requested_environment": ENV, "child_affinity_before_resume": affinity,
               "process_wall_seconds": elapsed, "max_wall_seconds": MAX_WALL,
               "peak_process_tree_rss_bytes": peak_rss, "max_process_tree_rss_bytes": MAX_RSS,
               "peak_process_tree_threads": peak_threads,
               "exit_code": proc.returncode if proc else None,
               "raw_sha256": sha(raw_path) if raw_path.exists() else None,
               "cumulative_diagnostic_wall_seconds": elapsed,
               "remaining_of_90_seconds": 90.0-elapsed,
               "reserved_final_seconds": 60.0}
    save(folder / "receipt.json", receipt)
    if receipt["status"] == "completed":
        try:
            result = postprocess(folder)
            receipt["validation_status"] = result["status"]
        except BaseException as error:
            receipt["validation_status"] = "failed"
            receipt["validation_failure"] = {"type": type(error).__name__, "message": str(error),
                                             "traceback": traceback.format_exc()}
        save(folder / "receipt.json", receipt)
    print(json.dumps({key: receipt.get(key) for key in
                      ("status", "validation_status", "process_wall_seconds",
                       "peak_process_tree_rss_bytes", "peak_process_tree_threads", "exit_code")}))
    if receipt["status"] != "completed" or receipt.get("validation_status") != "development_capture_validated":
        raise RuntimeError("capture or source-bound validation failed; inspect retained receipt/raw/logs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--raw", type=Path)
    args = parser.parse_args()
    if args.preflight:
        spec, *_ = candidate()
        save(args.preflight, {key: value for key, value in spec.items()
                              if key not in ("dof_order", "fixed_dofs", "rows", "cases")}
             | {"supervisor_preflight": supervisor_preflight()})
    elif args.child and args.raw:
        child(args.raw)
    elif args.output_dir:
        supervise(args.output_dir)
    else:
        parser.error("provide --preflight or a fresh --output-dir")
