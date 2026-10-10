"""Versioned saved-data BL5 per-support shell wrench comparison; no solver."""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import r8_bl5_five_channel_mz_reference_dev as base

OUT = base.OUT / "stationwise-v2"
V1 = base.OUT / "saved-adjudication-v1"
MAX_WALL = 90.0
MAX_RSS = 2*1024**3


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value: bool, message: str) -> None:
    base.require(value, message)


def native_support_rows(j: int) -> tuple[int, ...]:
    require(isinstance(j, int) and 0 <= j < 8, "invalid physical support index")
    return (j, 8+j, 16+j, 24+j, 32+j)


def source_to_native_matrix(np):
    mapping = np.zeros((40, 40))
    # Native channel-major row ordering; the last two director signs/order differ.
    for j in range(8):
        for native_channel, source_channel, sign in ((0, 0, -1), (1, 1, -1),
                                                     (2, 2, -1), (3, 4, -1),
                                                     (4, 3, +1)):
            mapping[native_support_rows(j)[native_channel], 5*j+source_channel] = sign
    require(np.array_equal(abs(mapping).sum(axis=0), np.ones(40)) and
            np.array_equal(abs(mapping).sum(axis=1), np.ones(40)) and
            np.array_equal(mapping.T@mapping, np.eye(40)),
            "signed support/channel selector is not orthogonal")
    return mapping


def native_c(np, sparse):
    with np.load(base.NATIVE / "operators.npz") as archive:
        return sparse.csr_matrix((archive["C_data"], archive["C_indices"],
                                  archive["C_indptr"]), shape=tuple(archive["C_shape"]))


def measure_preflight() -> dict:
    import numpy as np
    from scipy import sparse
    prior = base.preflight()
    prior_receipt = json.loads((V1 / "receipt.json").read_text())
    prior_result = json.loads((V1 / "result.json").read_text())
    require(prior_receipt["status"] == "completed" and
            prior_result["status"] == "saved_detached_five_channel_comparator_passed_development_only" and
            prior_receipt["result_sha256"] == sha(V1 / "result.json") and
            prior_receipt["source_sha256"] == sha(ROOT / "scripts" /
                                                   "r8_bl5_five_channel_mz_reference_dev.py") and
            prior_receipt["preflight_sha256"] == sha(V1 / "preflight.json"),
            "prior saved comparator bytes/status changed")
    spec = base.identity.fixture_preflight()
    model = base.identity.import_recipe().geometry(16, base.identity.import_recipe().services()[3])
    cext = base.row_matrix(spec["rows"], spec["dof_order"], np, sparse)
    cn = native_c(np, sparse)
    require(cn.shape == (40, 1092) and cext.shape == (40, 708),
            "native/external row dimensions changed")
    mapping = source_to_native_matrix(np)
    shell_slots = np.asarray([i for i, (node, _) in enumerate(spec["dof_order"])
                              if node in set(model["shell_node_ids"])], dtype=int)
    require(len(shell_slots) == 510, "physical shell coordinate inventory changed")
    mapped = np.asarray((cn[:, shell_slots].T @ mapping))
    external = np.asarray(cext[:, shell_slots].T.toarray())
    # Both use the resisting-row sign here; exerted signs are identical after negation.
    error = float(np.max(abs(mapped-external)))
    require(error <= 1e-13, f"40-basis per-support shell covector work mismatch {error}")
    native_inputs = json.loads((base.NATIVE / "inputs.json").read_text())
    reference = base.identity.import_recipe().services()[3]
    rows, supports = base.identity.import_recipe().aggregate_rows(model, reference,
                     base.identity.import_recipe().services()[0])
    require(rows == spec["rows"] and len(supports) == 8, "source support rows changed")
    for j, support in enumerate(supports):
        interval = [j/8, (j+1)/8]
        require(list(support["interval_m"]) == interval and
                native_inputs["policy"]["support_endpoints_m"][j:j+2] == interval and
                support["row_indices"] == list(range(5*j, 5*j+5)),
                "physical interval measure or support order changed")
    return {"status": "stationwise_measure_preflight_passed", "source_sha256": sha(Path(__file__)),
            "base_source_sha256": sha(ROOT / "scripts" / "r8_bl5_five_channel_mz_reference_dev.py"),
            "base_result_sha256": sha(V1 / "result.json"),
            "base_receipt_sha256": sha(V1 / "receipt.json"),
            "native_operator_sha256": sha(base.NATIVE / "operators.npz"),
            "max_40_basis_shell_covector_error": error,
            "shell_dofs": len(shell_slots), "support_intervals_m": [[j/8, (j+1)/8] for j in range(8)],
            "measure": "integrated shell-exerted (N,Nm) per source interval about beam root; no width redivision",
            "source_identity": prior}


def shell_wrench_parts(action, model, dofs, np):
    origin = np.asarray(model["moment_origin_m"])
    force = np.zeros(3); arm = np.zeros(3); direct = np.zeros(3)
    shell = set(model["shell_node_ids"])
    for i, (node, dof) in enumerate(dofs):
        if node not in shell:
            continue
        if dof <= 3:
            component = np.zeros(3); component[dof-1] = action[i]
            force += component
            arm += np.cross(np.asarray(model["nodes"][node])-origin, component)
        else:
            direct[dof-4] += action[i]
    return force, arm, direct


def normalize_shape(values, np):
    values = np.asarray(values, dtype=float)
    l1 = float(np.sum(abs(values)))
    net = float(np.sum(values))
    require(l1 > 1e-9, "zero shell-side local-shape scale")
    return {"signed_L1_normalized": (values/l1).tolist(), "L1_N_or_Nm": l1,
            "net_N_or_Nm": net, "cancellation_L1_over_abs_net":
            l1/abs(net) if abs(net) > 1e-9 else None}


def validate_saved_preflight(saved: dict, current: dict) -> None:
    # Windows text-mode serialization writes CRLF. Compare decoded provenance,
    # while the receipt separately binds the exact saved preflight bytes.
    require(saved == current, "preflight changed before child")


def case_profile(case: str, binding: dict, np, sparse) -> dict:
    spec = base.identity.fixture_preflight()
    recipe = base.identity.import_recipe()
    model = recipe.geometry(16, recipe.services()[3])
    dofs = spec["dof_order"]
    cext = base.row_matrix(spec["rows"], dofs, np, sparse)
    cn = native_c(np, sparse)
    ext = json.loads((base.EXTERNAL / case / "recovered-actions.json").read_text())
    require(sha(base.EXTERNAL / case / "recovered-actions.json") ==
            binding["source_identity"]["cases"][case]["external_actions"],
            f"{case} external action bytes changed after preflight")
    e_density = np.asarray(ext["row_density_multipliers"])
    with np.load(base.NATIVE / case / "raw-state.npz") as archive:
        n_density = np.asarray(archive["multipliers"])
        n_q = np.asarray(archive["q"])
        archived_native_exerted = np.asarray(archive["connection_exerted"])
    require(sha(base.NATIVE / case / "raw-state.npz") ==
            binding["source_identity"]["cases"][case]["native_raw"],
            f"{case} native state bytes changed after preflight")
    raw = json.loads((base.EXTERNAL / case / "raw-inventory.json").read_text())
    e_q = np.asarray([raw["poses"][str(node)][dof-1] for node, dof in dofs])
    e_total = -np.asarray(cext.T@e_density).ravel()
    n_total = -np.asarray(cn.T@n_density).ravel()
    base.close_vector(n_total, archived_native_exerted, relative=1e-10, floor=1e-9,
                      name=f"{case} full native action")
    profiles = {"external": [], "native": []}
    sums = {"external": np.zeros(708), "native": np.zeros(1092)}
    for j in range(8):
        erows = list(range(5*j, 5*j+5)); nrows = list(native_support_rows(j))
        e_action = -np.asarray(cext[erows, :].T@e_density[erows]).ravel()
        n_action = -np.asarray(cn[nrows, :].T@n_density[nrows]).ravel()
        sums["external"] += e_action; sums["native"] += n_action
        for label, action, pose in (("external", e_action, e_q), ("native", n_action, n_q)):
            force, arm, direct = shell_wrench_parts(action[:708], model, dofs, np)
            profiles[label].append({"interval_m": [j/8, (j+1)/8],
                                    "shell_force_N": force.tolist(),
                                    "shell_arm_moment_Nm": arm.tolist(),
                                    "shell_direct_couple_Nm": direct.tolist(),
                                    "shell_wrench_N_Nm": np.r_[force, arm+direct].tolist(),
                                    "shell_action_work_J": float(action[:510]@pose[:510])})
    base.close_vector(sums["external"], e_total, relative=1e-10, floor=1e-11,
                      name=f"{case} external support sum")
    base.close_vector(sums["native"], n_total, relative=1e-10, floor=1e-9,
                      name=f"{case} native full support sum")
    old = json.loads((V1 / "result.json").read_text())["cases"][case]
    for label, total in (("external", e_total), ("native", n_total)):
        wrench = base.wrench(total[:708],
                   {n: model["nodes"][n] for n in model["shell_node_ids"]},
                   dofs, np.asarray(model["moment_origin_m"]), np)
        base.close_vector(wrench, old[f"{label}_shell_wrench_N_Nm"],
                          relative=1e-10, floor=1e-9,
                          name=f"{case} {label} archived shell wrench")
    for j, record in enumerate(profiles["external"]):
        base.close_vector(record["shell_wrench_N_Nm"],
                          old["external_support_shell_wrenches_N_Nm"][j],
                          relative=1e-10, floor=1e-10,
                          name=f"{case} external support {j} archived wrench")
    shape = {}
    for label in profiles:
        shape[label] = {key: normalize_shape([entry["shell_wrench_N_Nm"][component]
                                                 for entry in profiles[label]], np)
                        for key, component in (("Fy", 1), ("Mz", 5))}
    difference = {key: {"max_abs": max(abs(profiles["native"][j]["shell_wrench_N_Nm"][slot]-
                                          profiles["external"][j]["shell_wrench_N_Nm"][slot])
                                      for j in range(8)),
                        "L1_relative_to_external": sum(abs(profiles["native"][j]["shell_wrench_N_Nm"][slot]-
                                                           profiles["external"][j]["shell_wrench_N_Nm"][slot])
                                                       for j in range(8))/shape["external"][shape_key]["L1_N_or_Nm"]}
                  for key, shape_key, slot in (("Fy_N", "Fy", 1), ("Mz_Nm", "Mz", 5))}
    return {"profiles": profiles, "shape": shape, "native_minus_external": difference,
            "interpretation": "different coupled densities/body discretizations; matched physical per-interval shell wrench measure only"}


def child(folder: Path) -> None:
    import numpy as np
    from scipy import sparse
    import psutil, threadpoolctl
    require(psutil.Process().cpu_affinity() == [0], "child CPU0 affinity missing")
    require(all(os.environ.get(k) == v for k, v in base.ENV.items()),
            "one-thread/JIT environment missing")
    binding = measure_preflight()
    validate_saved_preflight(json.loads((folder / "preflight.json").read_text()), binding)
    cases = {case: case_profile(case, binding, np, sparse) for case in ("fy", "mz")}
    pools = threadpoolctl.threadpool_info()
    require(pools and all(p["num_threads"] == 1 for p in pools), "numerical pool exceeded one thread")
    result = {"status": "stationwise_saved_comparator_passed_development_only",
              "identity": binding, "cases": cases,
              "runtime": {"affinity": psutil.Process().cpu_affinity(),
                          "numerical_pools": pools, "jit_disabled": True}}
    (folder / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")


def supervise(folder: Path) -> None:
    require(not folder.exists(), "fresh stationwise output required")
    binding = measure_preflight()
    import psutil
    require(base.PYTHON.is_file() and 0 in psutil.Process().cpu_affinity(),
            "Python3.14/CPU0 unavailable")
    folder.mkdir(parents=True)
    shutil.copyfile(__file__, folder / "executed-source.py")
    shutil.copyfile(ROOT / "scripts" / "r8_bl5_five_channel_mz_reference_dev.py", folder /
                    "r8_bl5_five_channel_mz_reference_dev.py")
    (folder / "preflight.json").write_text(json.dumps(binding, indent=2, sort_keys=True)+"\n")
    parent = psutil.Process(); original = parent.cpu_affinity(); parent.cpu_affinity([0])
    env = os.environ.copy(); env.update(base.ENV)
    command = [str(base.PYTHON), "-u", str(Path(__file__).resolve()), "--child", "--output", str(folder)]
    begun = time.perf_counter(); peak = threads = 0; reason = affinity = proc = None
    try:
        with (folder / "stdout.log").open("wb") as stdout, (folder / "stderr.log").open("wb") as stderr:
            proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                                    creationflags=0x4)
            process = psutil.Process(proc.pid); process.cpu_affinity([0]); affinity = process.cpu_affinity()
            require(affinity == [0], "child CPU0 setup failed")
            process.resume()
            while proc.poll() is None:
                try:
                    live = [p for p in [process]+process.children(recursive=True) if p.is_running()]
                    peak = max(peak, sum(p.memory_info().rss for p in live))
                    threads = max(threads, sum(p.num_threads() for p in live))
                    if any(p.cpu_affinity() != [0] for p in live): reason = "affinity_changed"
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                if time.perf_counter()-begun >= MAX_WALL or peak > MAX_RSS:
                    reason = "timeout" if time.perf_counter()-begun >= MAX_WALL else "memory_limit"
                if reason:
                    for p in reversed([process]+process.children(recursive=True)):
                        try: p.kill()
                        except psutil.NoSuchProcess: pass
                    break
                time.sleep(0.01)
            proc.wait(timeout=3)
    finally:
        elapsed = time.perf_counter()-begun; parent.cpu_affinity(original)
    result = folder / "result.json"
    receipt = {"status": reason or ("completed" if proc and proc.returncode == 0 and result.exists()
                                    else "failed"), "command": command, "process_wall_seconds": elapsed,
               "max_wall_seconds": MAX_WALL, "peak_process_tree_rss_bytes": peak,
               "max_process_tree_rss_bytes": MAX_RSS, "peak_process_tree_threads": threads,
               "child_affinity_before_resume": affinity, "requested_environment": base.ENV,
               "exit_code": proc.returncode if proc else None,
               "source_sha256": sha(folder / "executed-source.py"),
               "base_source_sha256": sha(folder / "r8_bl5_five_channel_mz_reference_dev.py"),
               "preflight_sha256": sha(folder / "preflight.json"),
               "result_sha256": sha(result) if result.exists() else None,
               "fresh_180_second_ledger_consumed": elapsed,
               "remaining_of_180_seconds": 180.0-elapsed, "reserved_final_seconds": 60.0,
               "external_solver_children": 0, "historical_case_replays": 0}
    (folder / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n")
    print(json.dumps({key: receipt[key] for key in ("status", "process_wall_seconds",
          "peak_process_tree_rss_bytes", "exit_code")}))
    require(receipt["status"] == "completed", "stationwise child failed; preserve receipt/logs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    if args.preflight:
        pre = measure_preflight()
        print(json.dumps({key: pre[key] for key in ("status", "max_40_basis_shell_covector_error",
                                               "shell_dofs")}))
    elif args.child: child(args.output)
    else: supervise(args.output)
