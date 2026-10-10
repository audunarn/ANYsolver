"""One bounded offline BL5 external-K cross-case and support-yaw discriminator.

Uses only saved Fy FullGeneral KKT, archived external Fy/Mx/Mz responses and
archived native 16x4 operators. It never imports or launches OpenSees.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

import r8_bl5_external_operator_dev as identity


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/agent_plans/development/r8-bl5-external-operator-20261009"
CAPTURE = REPORT / "fy-fullgeneral-v3"
NATIVE = (ROOT / "docs/agent_plans/development/r8-bl5-matched-comparison-20261001"
          / "refinement-v1-raw/native/n16")
PYTHON = Path(r"C:\Python\Python314\python.exe")
SITE = Path(r"C:\Python\Python314\Lib\site-packages")
MAX_WALL = 30.0
MAX_RSS = 2 * 1024**3
ENV = {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
       "NUMBA_NUM_THREADS": "1", "NUMBA_DISABLE_JIT": "1"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")


def check_native_load_binding(case: str, result: dict, actual_raw_sha256: str) -> None:
    """Refuse a different case, failed run, or altered native load archive."""
    identity.require(case in ("fy", "mx", "mz") and result.get("case") == case and
                     result.get("status") == "completed",
                     f"{case}: completed exact native case required")
    expected = result.get("raw_state_sha256")
    identity.require(isinstance(expected, str) and len(expected) == 64 and
                     expected == actual_raw_sha256,
                     f"{case}: native raw-state SHA-256 mismatch or absent")


def bound_native_load(case: str) -> dict:
    result_path = NATIVE / case / "result.json"
    raw_path = NATIVE / case / "raw-state.npz"
    result = json.loads(result_path.read_text())
    raw_sha256 = sha(raw_path)
    check_native_load_binding(case, result, raw_sha256)
    return {"case": case, "result_sha256": sha(result_path),
            "raw_state_sha256": raw_sha256}


def preflight() -> dict:
    spec = identity.fixture_preflight()
    raw_path, receipt_path = CAPTURE / "raw.json", CAPTURE / "receipt.json"
    raw = json.loads(raw_path.read_text())
    receipt = json.loads(receipt_path.read_text())
    identity.require(receipt["status"] == "completed" and
                     receipt["raw_sha256"] == sha(raw_path) and
                     receipt["source_sha256"] == sha(CAPTURE / "executed-capture-source.py"),
                     "unchanged source-bound Fy capture required")
    mapped = identity.validate_fullgeneral_capture(spec, raw)
    native_inputs = json.loads((NATIVE / "inputs.json").read_text())
    identity.require(native_inputs["operators_sha256"] == sha(NATIVE / "operators.npz"),
                     "native operator archive identity mismatch")
    layout = json.loads((NATIVE / "layout.json").read_text())
    identity.require(layout["nx"] == 16 and layout["counts"]["full_q"] == 1092 and
                     layout["counts"]["multipliers"] == 40 and
                     len(layout["fixed_coordinates"]) == 35,
                     "matched native 16x4 support/coordinate family required")
    return {"status": "source_preflight_passed", "external_raw_sha256": sha(raw_path),
            "external_receipt_sha256": sha(receipt_path),
            "executed_capture_source_sha256": receipt["source_sha256"],
            "native_operators_sha256": sha(NATIVE / "operators.npz"),
            "native_inputs_sha256": sha(NATIVE / "inputs.json"),
            "native_layout_sha256": sha(NATIVE / "layout.json"),
            "native_case_loads": {case: bound_native_load(case) for case in ("fy", "mx", "mz")},
            "model_source_sha256": spec["recipe_sha256"],
            "binary_sha256": spec["binary_sha256"],
            "capture_commands_sha256": spec["capture_commands_sha256"],
            "physical_equation_ids_sha256": mapped["physical_equation_ids_sha256"],
            "physical_dimension": 708, "kkt_dimension": 783,
            "cases": {case: {key: value for key, value in data.items()
                              if key in ("raw_sha256", "summary_sha256", "response_sha256")}
                      for case, data in spec["cases"].items()}}


def assemble(raw, dofs, np):
    values = {(int(node), int(dof)): 0.0 for node, dof in dofs}
    for tag, element in raw["elements"].items():
        force = raw["element_global_covectors"][str(tag)]
        identity.require(len(force) == 6*len(element["nodes"]), "element covector shape mismatch")
        for slot, node in enumerate(element["nodes"]):
            for dof in range(1, 7):
                values[int(node), dof] += float(force[6*slot+dof-1])
    return np.asarray([values[tuple(pair)] for pair in dofs], dtype=float)


def physical_residual(residual, reference, dofs, name, *, relative=1e-8, floor=1e-8):
    result = {}
    for kind, select in (("force_N", lambda d: d <= 3), ("moment_Nm", lambda d: d > 3)):
        slots = [i for i, (_, dof) in enumerate(dofs) if select(dof)]
        peak = max((abs(float(residual[i])) for i in slots), default=0.0)
        scale = max((abs(float(reference[i])) for i in slots), default=0.0)
        limit = max(floor, relative*scale)
        identity.require(peak <= limit, f"{name} {kind} residual {peak} > {limit}")
        result[kind] = {"max_abs": peak, "scale": scale, "limit": limit, "rows": len(slots)}
    return result


def yaw_annihilation(k, yaw, np, name):
    residual = k @ yaw
    contribution = abs(k) @ abs(yaw)
    active = contribution > 1e-12
    ratio = float(np.max(abs(residual[active])/contribution[active], initial=0.0))
    peak = float(np.max(abs(residual), initial=0.0))
    identity.require(ratio <= 1e-8 and
                     float(np.max(abs(residual[~active]), initial=0.0)) <= 1e-8,
                     f"{name} declared rigid yaw not annihilated by support-only K")
    return {"max_row_relative": ratio, "max_abs_dual": peak,
            "active_rows": int(np.count_nonzero(active))}


def compatibility(yaw, applied, connection, np, name):
    net = applied-connection
    work = float(yaw @ net)
    scale = max(float(np.sum(abs(yaw*applied))),
                float(np.sum(abs(yaw*connection))), 1e-12)
    ratio = abs(work)/scale
    identity.require(ratio <= 1e-8,
                     f"{name} fixed-density rigid-yaw load work incompatible")
    return {"rigid_work_Nm": work, "physical_work_scale_Nm": scale,
            "compatibility_ratio": ratio}


def child(folder: Path) -> None:
    result = {"status": "failed", "classification": "saved-operator cross-case development only",
              "source_sha256": sha(Path(__file__)), "environment": {k: os.environ.get(k) for k in ENV},
              "python": sys.version, "python_executable": sys.executable,
              "cases": {}}
    try:
        identity.require(all(result["environment"][k] == v for k, v in ENV.items()),
                         "one-thread/JIT-off environment missing")
        import numpy as np
        import scipy.linalg as la
        import scipy.sparse as sparse
        import psutil
        from threadpoolctl import threadpool_info
        runtime = threadpool_info()
        identity.require(runtime and all(pool["num_threads"] == 1 for pool in runtime),
                         "effective BLAS pool must have one thread")
        identity.require(psutil.Process().cpu_affinity() == [0], "CPU0 affinity required")
        result["runtime"] = {"affinity": [0], "blas_pools": runtime,
                             "numpy": np.__version__, "scipy": __import__("scipy").__version__}
        binding = preflight()
        result["bound_inputs"] = binding
        spec = identity.fixture_preflight()
        raw = json.loads((CAPTURE / "raw.json").read_text())
        mapping = identity.validate_fullgeneral_capture(spec, raw)
        m = spec["kkt_dimension"]
        matrix = np.asarray(raw["printA"], dtype=float).reshape((m, m))
        physical_ids = np.asarray([raw["node_dofs"][str(node)][dof-1]
                                   for node, dof in spec["dof_order"]], dtype=int)
        constraint_ids = np.asarray(sorted(set(range(m))-set(physical_ids)), dtype=int)
        k = matrix[np.ix_(physical_ids, physical_ids)]
        b = matrix[np.ix_(physical_ids, constraint_ids)] / spec["alpha_mp"]
        matches = mapping["constraint_equations"]
        identity.require([v["equation_id"] for v in matches] == list(constraint_ids),
                         "constraint classification/order changed")
        with np.load(NATIVE / "operators.npz", allow_pickle=False) as archive:
            op = {key: np.array(archive[key], copy=True) for key in archive.files}
        kn = sparse.csr_matrix((op["K_data"], op["K_indices"], op["K_indptr"]),
                               shape=tuple(op["K_shape"]))
        cn = sparse.csr_matrix((op["C_data"], op["C_indices"], op["C_indptr"]),
                               shape=tuple(op["C_shape"]))
        identity.require(kn.shape == (1092, 1092) and cn.shape == (40, 1092),
                         "native full retained operator dimensions changed")
        native_yaw = np.asarray(op["beam_rigid_work_map"][5], dtype=float)
        identity.require(np.max(abs(native_yaw[op["fixed"]]), initial=0.0) == 0.0 and
                         abs(native_yaw[6*85+5]-1.0) <= 1e-15,
                         "native root-free retained yaw identity mismatch")
        model = identity.import_recipe().geometry(16, identity.import_recipe().services()[3])
        origin = model["nodes"][model["beam_root"]]
        external_yaw = np.zeros(len(spec["dof_order"]))
        for i, (node, dof) in enumerate(spec["dof_order"]):
            if node in set(model["beam_node_ids"]):
                xyz = model["nodes"][node]
                external_yaw[i] = (-(xyz[1]-origin[1]) if dof == 1 else
                                   xyz[0]-origin[0] if dof == 2 else
                                   1.0 if dof == 6 else 0.0)
        fixed_idx = [spec["dof_order"].index(pair) for pair in spec["fixed_dofs"]]
        identity.require(np.max(abs(external_yaw[fixed_idx]), initial=0.0) == 0.0,
                         "external rigid yaw violates original supports")
        result["support_only_yaw"] = {
            "external": yaw_annihilation(k, external_yaw, np, "external"),
            "native": yaw_annihilation(kn, native_yaw, np, "native"),
            "native_retained_cell_rotation_slots_nonzero": int(sum(
                abs(native_yaw[i]) > 0 for row in json.loads((NATIVE / "layout.json").read_text())["retained_members"]
                for i in row["cell_rotation_slots"]))}
        arrays = {"physical_equation_ids": physical_ids, "constraint_equation_ids": constraint_ids,
                  "external_yaw": external_yaw, "native_yaw": native_yaw}
        for case in ("fy", "mx", "mz"):
            saved = json.loads((identity.FIXTURE / case / "raw-inventory.json").read_text())
            u = np.asarray(spec["cases"][case]["displacement"], dtype=float)
            g = assemble(saved, spec["dof_order"], np)
            ku = k @ u
            source_check = identity.validate_physical_force_assembly(
                k.tolist(), u.tolist(), g.tolist(), spec["dof_order"])
            f = np.asarray(spec["cases"][case]["applied_load"], dtype=float)
            mu_normalized, _, rank, _ = la.lstsq(b, f-ku, cond=1e-12, lapack_driver="gelsy")
            identity.require(rank == 75, f"{case}: mapped KKT constraints rank deficient")
            kkt_residual = ku+b@mu_normalized-f
            residual_report = physical_residual(kkt_residual, f, spec["dof_order"],
                                                f"{case} KKT load")
            gap = b.T@u
            identity.require(float(np.max(abs(gap), initial=0.0)) <= 1e-9,
                             f"{case}: mapped KKT constraint gap exceeds 1e-9 m/rad")
            mu_source = np.zeros(40)
            mp_positions = []
            for column, row in enumerate(matches):
                if row["kind"] != "MP":
                    continue
                source_row = row["source_row"]
                dependent = spec["rows"][source_row][2]
                mu_source[source_row] = row["orientation"]*mu_normalized[column]/dependent
                mp_positions.append(column)
            archive_actions = json.loads((identity.FIXTURE / case / "recovered-actions.json").read_text())
            archived_mu = np.asarray(archive_actions["row_density_multipliers"], dtype=float)
            mu_difference = float(np.max(abs(mu_source-archived_mu), initial=0.0))
            mu_scale = max(1.0, float(np.max(abs(archived_mu))))
            identity.require(mu_difference <= 1e-6*mu_scale,
                             f"{case}: inferred external source-row densities differ from archive")
            external_connection = b[:, mp_positions] @ mu_normalized[mp_positions]
            external_compatibility = compatibility(external_yaw, f, external_connection,
                                                   np, f"{case} external")
            native_density = np.zeros(40)
            for j in range(8):
                native_density[j] = -mu_source[5*j]
                native_density[8+j] = -mu_source[5*j+1]
                native_density[16+j] = -mu_source[5*j+2]
                native_density[24+j] = -mu_source[5*j+4]
                native_density[32+j] = mu_source[5*j+3]
            load_binding = bound_native_load(case)
            identity.require(load_binding == binding["native_case_loads"][case],
                             f"{case}: native load changed after preflight")
            with np.load(NATIVE / case / "raw-state.npz", allow_pickle=False) as native_state:
                native_load = np.asarray(native_state["load"], dtype=float)
            native_connection = cn.T@native_density
            native_compatibility = compatibility(native_yaw, native_load, native_connection,
                                                 np, f"{case} native")
            result["cases"][case] = {"physical_Ku_vs_archived_element_covectors": source_check,
                                      "kkt_load_residual": residual_report,
                                      "kkt_constraint_max_abs_gap_normalized": float(np.max(abs(gap))),
                                      "inferred_multiplier_rank": int(rank),
                                      "inferred_external_density_max_abs_difference": mu_difference,
                                      "inferred_external_density_archive_scale": mu_scale,
                                      "support_only_external_yaw_compatibility": external_compatibility,
                                      "support_only_native_yaw_compatibility": native_compatibility}
            for name, value in (("u", u), ("Ku", ku), ("assembled_element_force", g),
                                ("frozen_load", f), ("inferred_normalized_mu", mu_normalized),
                                ("inferred_source_density", mu_source),
                                ("native_density", native_density), ("native_load", native_load)):
                arrays[f"{case}_{name}"] = value
        np.savez_compressed(folder / "arrays.npz", **arrays)
        result["arrays_sha256"] = sha(folder / "arrays.npz")
        result["status"] = "crosscase_and_support_checks_passed_development_only"
    except BaseException as error:
        result["failure"] = {"type": type(error).__name__, "message": str(error),
                             "traceback": traceback.format_exc()}
    finally:
        save(folder / "result.json", result)
    if result["status"] != "crosscase_and_support_checks_passed_development_only":
        raise RuntimeError(result["failure"]["message"])


def supervise(folder: Path) -> None:
    if folder.exists():
        raise FileExistsError("fresh offline output directory required")
    binding = preflight()  # Saved-only, before one numerical process.
    sys.path.insert(0, str(SITE))
    import psutil
    identity.require(PYTHON.is_file() and 0 in psutil.Process().cpu_affinity(),
                     "offline runtime/CPU0 unavailable")
    folder.mkdir(parents=True)
    shutil.copyfile(__file__, folder / "executed-source.py")
    save(folder / "preflight.json", binding)
    parent = psutil.Process()
    original_affinity = parent.cpu_affinity()
    parent.cpu_affinity([0])
    env = os.environ.copy()
    env.update(ENV)
    command = [str(PYTHON), "-u", str(Path(__file__).resolve()), "--child", "--output-dir", str(folder)]
    started = time.perf_counter()
    peak_rss, peak_threads, reason, affinity = 0, 0, None, None
    proc = None
    try:
        with (folder / "stdout.log").open("wb") as stdout, (folder / "stderr.log").open("wb") as stderr:
            proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                                    creationflags=0x4)
            process = psutil.Process(proc.pid)
            process.cpu_affinity([0])
            affinity = process.cpu_affinity()
            identity.require(affinity == [0], "offline child affinity not set")
            process.resume()
            while proc.poll() is None:
                elapsed = time.perf_counter()-started
                try:
                    live = [p for p in [process]+process.children(recursive=True) if p.is_running()]
                    peak_rss = max(peak_rss, sum(p.memory_info().rss for p in live))
                    peak_threads = max(peak_threads, sum(p.num_threads() for p in live))
                    if any(p.cpu_affinity() != [0] for p in live):
                        reason = "affinity_changed"
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                if elapsed >= MAX_WALL or peak_rss > MAX_RSS:
                    reason = "timeout" if elapsed >= MAX_WALL else "memory_limit"
                if reason:
                    for p in reversed([process]+process.children(recursive=True)):
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
    result_path = folder / "result.json"
    receipt = {"status": reason or ("completed" if proc and proc.returncode == 0 and result_path.exists() else "failed"),
               "command": command, "source_sha256": sha(folder / "executed-source.py"),
               "requested_environment": ENV, "child_affinity_before_resume": affinity,
               "process_wall_seconds": elapsed, "max_wall_seconds": MAX_WALL,
               "peak_process_tree_rss_bytes": peak_rss, "max_process_tree_rss_bytes": MAX_RSS,
               "peak_process_tree_threads": peak_threads, "exit_code": proc.returncode if proc else None,
               "result_sha256": sha(result_path) if result_path.exists() else None,
               "cumulative_90_second_ledger_consumed": elapsed,
               "remaining_of_90_seconds": 90.0-elapsed, "reserved_final_seconds": 60.0}
    save(folder / "receipt.json", receipt)
    print(json.dumps({k: receipt[k] for k in ("status", "process_wall_seconds",
                                        "peak_process_tree_rss_bytes", "exit_code")}))
    if receipt["status"] != "completed":
        raise RuntimeError("offline numerical check failed; retained result/receipt/logs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--child", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        save(args.preflight, preflight())
    elif args.child and args.output_dir:
        child(args.output_dir)
    elif args.output_dir:
        supervise(args.output_dir)
    else:
        parser.error("provide --preflight or fresh --output-dir")
