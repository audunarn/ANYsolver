"""Saved-byte detached five-channel Mz/Fy work and transfer comparator.

No solver is invoked. The external source is the archived OpenSees detached
ASDShellQ4/Timoshenko five-channel integral-row model; the native B3/Q4 model
is a different body discretization. This is development evidence only.
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

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/agent_plans/development/r8-bl5-five-channel-mz-reference-20261009"
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
import r8_bl5_external_operator_dev as identity
import r8_bl5_external_operator_crosscase_dev as crosscase
import r8_bl5_common_density_response_dev as common

NATIVE = crosscase.NATIVE
EXTERNAL = identity.FIXTURE
CROSSCASE = crosscase.REPORT / "crosscase-v1"
HELPERS = ("r8_bl5_external_operator_dev.py", "r8_bl5_external_operator_crosscase_dev.py",
           "r8_bl5_common_density_response_dev.py")
ENV = {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
       "NUMEXPR_NUM_THREADS": "1", "NUMBA_NUM_THREADS": "1", "NUMBA_DISABLE_JIT": "1"}
PYTHON = Path(r"C:\Python\Python314\python.exe")
MAX_WALL = 90.0
MAX_RSS = 2*1024**3


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value: bool, message: str) -> None:
    if not value:
        raise identity.IdentityError(message)


def close_vector(actual, expected, *, relative: float, floor: float, name: str) -> float:
    require(len(actual) == len(expected), f"{name} dimension mismatch")
    peak = max((abs(float(a)-float(b)) for a, b in zip(actual, expected)), default=0.0)
    scale = max((abs(float(b)) for b in expected), default=0.0)
    require(math.isfinite(peak) and peak <= relative*scale+floor,
            f"{name} mismatch {peak} > {relative*scale+floor}")
    return peak


def source_binding() -> dict[str, str]:
    result = {}
    for name in HELPERS:
        path = SCRIPTS / name
        committed = subprocess.run(["git", "show", f"HEAD:scripts/{name}"], cwd=ROOT,
                                   check=True, capture_output=True).stdout
        require(hashlib.sha256(committed).hexdigest() == sha(path), f"helper changed: {name}")
        result[name] = sha(path)
    return result


def preflight() -> dict:
    spec = identity.fixture_preflight()
    cross = crosscase.preflight()
    recipe = identity.import_recipe()
    reference = recipe.services()[3]
    model = recipe.geometry(16, reference)
    native_inputs = json.loads((NATIVE / "inputs.json").read_text())
    layout = json.loads((NATIVE / "layout.json").read_text())
    geometry = common.validate_native_geometry(native_inputs, layout, model)
    require(native_inputs["operators_sha256"] == sha(NATIVE / "operators.npz"),
            "native operator bytes changed")
    require(native_inputs["line"]["law"] == "BL5_PHYSICAL_DIRECTOR_WEAK_LINE_DEV_V1" and
            native_inputs["line"]["expected_beam_arm"] == [0.0, 0.0, -0.05],
            "native five-channel line/arm changed")
    for key, value in native_inputs["reference_constants"].items():
        require(float(getattr(reference, key)) == float(value), f"section/offset differs: {key}")
    require(model["nx"] == 16 and model["ny"] == 4 and model["beam_intervals"] == 32 and
            model["support_count"] == 8 and len(model["shell_node_ids"]) == 85 and
            len(model["beam_node_ids"]) == 33 and
            not set(model["shell_node_ids"]) & set(model["beam_node_ids"]),
            "detached physical body geometry changed")
    require(native_inputs["policy"]["support_endpoints_m"] == [i/8 for i in range(9)] and
            native_inputs["policy"]["span_halfcells"] == 4,
            "P0 support measure changed")
    triad = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    require(all(b["reference"]["nodal_triads"] == [triad]*3
                for b in native_inputs["beams"]),
            "native beam section frame changed")
    commands = recipe.command_recipe(model, reference, spec["rows"], "mz")
    require(("geomTransf", ("Linear", 1, 0.0, 0.0, 1.0)) in commands,
            "external beam frame changed")
    mapped_fixed = [[row["external_node"], dof+1]
                    for role, node, dof in layout["fixed_coordinates"]
                    for row in layout["typed_physical_nodes"]
                    if row["domain"] == role and row["native_node"] == node]
    require(mapped_fixed == [list(x) for x in spec["fixed_dofs"]] and len(mapped_fixed) == 35,
            "root support map changed")
    prior = json.loads((CROSSCASE / "result.json").read_text())
    receipt = json.loads((CROSSCASE / "receipt.json").read_text())
    require(prior["status"] == "crosscase_and_support_checks_passed_development_only" and
            receipt["status"] == "completed" and
            sha(CROSSCASE / "result.json") == receipt["result_sha256"] and
            sha(CROSSCASE / "arrays.npz") == prior["arrays_sha256"],
            "saved cross-case provenance changed")
    bound_cases = {}
    for case in ("fy", "mz"):
        ebase, nbase = EXTERNAL / case, NATIVE / case
        comparison = json.loads((nbase / "external-comparison.json").read_text())
        for name in ("raw-inventory.json", "recovered-actions.json", "summary.json"):
            require(sha(ebase / name) == comparison["external_files"][name],
                    f"{case} external archived file changed: {name}")
        native_result = json.loads((nbase / "result.json").read_text())
        require(native_result["case"] == case and native_result["status"] == "completed" and
                native_result["raw_state_sha256"] == sha(nbase / "raw-state.npz"),
                f"{case} native raw state unbound")
        bound_cases[case] = {"external_summary": sha(ebase / "summary.json"),
                             "external_raw": sha(ebase / "raw-inventory.json"),
                             "external_actions": sha(ebase / "recovered-actions.json"),
                             "native_result": sha(nbase / "result.json"),
                             "native_raw": sha(nbase / "raw-state.npz")}
    require(cross["physical_dimension"] == 708 and cross["kkt_dimension"] == 783 and
            len(spec["rows"]) == 40, "external KKT/row dimensions changed")
    return {"status": "source_preflight_passed", "source_sha256": sha(Path(__file__)),
            "helper_sha256": source_binding(), "binary_sha256": spec["binary_sha256"],
            "recipe_sha256": spec["recipe_sha256"],
            "mechanics_sha256": spec["mechanics_sha256"],
            "external_capture_raw_sha256": cross["external_raw_sha256"],
            "native_operators_sha256": sha(NATIVE / "operators.npz"),
            "physical_layout": geometry, "cases": bound_cases}


def row_matrix(rows, dofs, np, sparse):
    position = {tuple(x): i for i, x in enumerate(dofs)}
    data, rr, cc = [], [], []
    for index, row in enumerate(rows):
        require(len(row) % 3 == 0, "incomplete physical row triple")
        for j in range(0, len(row), 3):
            key = (int(row[j]), int(row[j+1]))
            require(key in position, "constraint node/DOF absent")
            rr.append(index); cc.append(position[key]); data.append(float(row[j+2]))
    return sparse.coo_matrix((np.asarray(data), (rr, cc)), shape=(40, 708)).tocsr()


def wrench(action, nodes, dofs, origin, np):
    total = np.zeros(6)
    for i, (node, dof) in enumerate(dofs):
        if node not in nodes:
            continue
        if dof <= 3:
            total[dof-1] += action[i]
            vec = np.zeros(3); vec[dof-1] = action[i]
            total[3:] += np.cross(np.asarray(nodes[node])-origin, vec)
        else:
            total[dof-1] += action[i]
    return total


def rigid_fields(nodes, dofs, origin, np):
    result = []
    for axis in range(6):
        field = np.zeros(len(dofs))
        for i, (node, dof) in enumerate(dofs):
            if axis < 3:
                field[i] = float(dof == axis+1)
            elif dof <= 3:
                spin = np.zeros(3); spin[axis-3] = 1.0
                field[i] = np.cross(spin, np.asarray(nodes[node])-origin)[dof-1]
            else:
                field[i] = float(dof == axis+1)
        result.append(field)
    return result


def case_check(case, spec, model, np, sparse) -> dict:
    ext = json.loads((EXTERNAL / case / "recovered-actions.json").read_text())
    raw = json.loads((EXTERNAL / case / "raw-inventory.json").read_text())
    dofs = spec["dof_order"]
    c = row_matrix(spec["rows"], dofs, np, sparse)
    density = np.asarray(ext["row_density_multipliers"], dtype=float)
    require(density.shape == (40,), f"{case} source density size changed")
    archived_density = np.asarray(common.npz_vector(CROSSCASE / "arrays.npz",
                                                    f"{case}_inferred_source_density"))
    density_error = close_vector(density, archived_density, relative=1e-8,
                                 floor=1e-9, name=f"{case} source density")
    q = np.asarray([raw["poses"][str(node)][dof-1] for node, dof in dofs])
    force = -np.asarray(c.T @ density).ravel()
    recorded = np.asarray([ext["connection_exerted_minus_C_transpose_lambda"][str(node)][dof-1]
                           for node, dof in dofs])
    force_error = close_vector(force, recorded, relative=1e-10, floor=1e-11,
                               name=f"{case} external exerted nodal action")
    require(float(np.max(np.abs(c @ q))) <= 1e-12, f"{case} weak five-channel gap")
    origin = np.asarray(model["moment_origin_m"])
    fields = rigid_fields(model["nodes"], dofs, origin, np)
    rigid_errors = [float(np.max(np.abs(c @ field))) for field in fields]
    require(max(rigid_errors) <= 1e-12, "five-channel rigid field not annihilated")
    shell_nodes, beam_nodes = set(model["shell_node_ids"]), set(model["beam_node_ids"])
    shell_w = wrench(force, {n: model["nodes"][n] for n in shell_nodes}, dofs, origin, np)
    beam_w = wrench(force, {n: model["nodes"][n] for n in beam_nodes}, dofs, origin, np)
    close_vector(shell_w+beam_w, np.zeros(6), relative=0, floor=1e-10,
                 name=f"{case} shell/beam common-origin wrench")
    virtual = np.asarray([ext["virtual_q"][str(node)][dof-1] for node, dof in dofs])
    virtual_gap = np.asarray(c @ virtual).ravel()
    virtual_error = close_vector(virtual_gap, ext["virtual_Cq"], relative=1e-10,
                                 floor=1e-12, name=f"{case} archived virtual row work")
    work_left = float(density @ virtual_gap)
    work_right = float((-force) @ virtual)
    require(abs(work_left-work_right) <= 1e-11*max(1.0, abs(work_left)),
            f"{case} work transpose failed")
    require(abs(float(force @ virtual)-ext["work_J"]["virtual_exerted"]) <= 1e-10,
            f"{case} signed archived virtual work changed")
    row_wrenches = []
    for j in range(8):
        action = -np.asarray(c[5*j:5*j+5, :].T @ density[5*j:5*j+5]).ravel()
        shell = wrench(action, {n: model["nodes"][n] for n in shell_nodes}, dofs, origin, np)
        beam = wrench(action, {n: model["nodes"][n] for n in beam_nodes}, dofs, origin, np)
        close_vector(shell+beam, np.zeros(6), relative=0, floor=1e-10,
                     name=f"{case} support {j} action wrench")
        row_wrenches.append(shell.tolist())
    # Native coupled response is independently archived, with all retained roles.
    nbase = NATIVE / case
    with np.load(nbase / "raw-state.npz") as saved, np.load(NATIVE / "operators.npz") as ops:
        nc = sparse.csr_matrix((ops["C_data"], ops["C_indices"], ops["C_indptr"]),
                               shape=tuple(ops["C_shape"]))
        nq, nlam = np.asarray(saved["q"]), np.asarray(saved["multipliers"])
        nforce = -np.asarray(nc.T @ nlam).ravel()
        native_force_error = close_vector(nforce, saved["connection_exerted"],
                                          relative=1e-10, floor=1e-9,
                                          name=f"{case} native full exerted action")
        require(nc.shape == (40, 1092) and nq.shape == (1092,) and
                nlam.shape == (40,), "native retained/constraint dimension changed")
        native_work_error = abs(float(nlam @ (nc @ nq))-float((nc.T @ nlam) @ nq))
        require(native_work_error <= 1e-10, "native signed full work transpose failed")
        native_q = nq[:708].copy()
        native_shell_w = wrench(nforce[:708],
                                {n: model["nodes"][n] for n in shell_nodes}, dofs, origin, np)
    tip_offset = dofs.index((model["beam_tip"], 1))
    shell_first_y = float(sum((model["nodes"][node][0]-origin[0])*force[i]
                              for i, (node, dof) in enumerate(dofs)
                              if node in shell_nodes and dof == 2))
    native_shell_first_y = float(sum((model["nodes"][node][0]-origin[0])*nforce[i]
                                     for i, (node, dof) in enumerate(dofs)
                                     if node in shell_nodes and dof == 2))
    return {"source_density_max_abs_difference": density_error,
            "exerted_action_max_abs_difference": force_error,
            "native_exerted_action_max_abs_difference": native_force_error,
            "external_rigid_row_gap_max": max(rigid_errors),
            "external_weak_row_gap_max": float(np.max(abs(c@q))),
            "external_virtual_row_error": virtual_error,
            "external_signed_virtual_work_J": float(force @ virtual),
            "native_full_work_transpose_error_J": native_work_error,
            "external_shell_wrench_N_Nm": shell_w.tolist(),
            "external_beam_wrench_N_Nm": beam_w.tolist(),
            "native_shell_wrench_N_Nm": native_shell_w.tolist(),
            "shell_first_x_moment_of_Fy_Nm": {"external": shell_first_y,
                                               "native": native_shell_first_y},
            "external_support_shell_wrenches_N_Nm": row_wrenches,
            "applied_work_J": {"external": ext["work_J"]["applied"],
                               "native": float(np.asarray(common.npz_vector(nbase / "raw-state.npz", "load")) @ nq)},
            "beam_tip_external_pose_m_rad": q[tip_offset:tip_offset+6].tolist(),
            "beam_tip_native_pose_m_rad": native_q[tip_offset:tip_offset+6].tolist()}


def adjudicate() -> dict:
    import numpy as np
    from scipy import sparse
    info = preflight()
    recipe = identity.import_recipe()
    model = recipe.geometry(16, recipe.services()[3])
    spec = identity.fixture_preflight()
    result = {"status": "saved_detached_five_channel_comparator_passed_development_only",
              "scope": "fixed 16x4 detached five-channel P0, distinct body discretizations; no accuracy/F03",
              "input_identity": info, "cases": {}}
    for case in ("fy", "mz"):
        result["cases"][case] = case_check(case, spec, model, np, sparse)
    return result


def child(folder: Path) -> None:
    import psutil
    import threadpoolctl
    require(psutil.Process().cpu_affinity() == [0], "child CPU0 affinity missing")
    require(all(os.environ.get(k) == v for k, v in ENV.items()),
            "one-thread/JIT environment not set")
    result = adjudicate()
    pools = threadpoolctl.threadpool_info()
    require(pools and all(p.get("num_threads") == 1 for p in pools),
            "numerical pool exceeds one thread")
    result["runtime"] = {"affinity": psutil.Process().cpu_affinity(),
                         "numerical_pools": pools, "jit_disabled": True}
    (folder / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")


def supervise(folder: Path) -> None:
    require(not folder.exists(), "fresh output folder required")
    binding = preflight()
    import psutil
    require(PYTHON.is_file() and 0 in psutil.Process().cpu_affinity(),
            "Python3.14/CPU0 unavailable")
    folder.mkdir(parents=True)
    shutil.copyfile(__file__, folder / "executed-source.py")
    (folder / "preflight.json").write_text(json.dumps(binding, indent=2, sort_keys=True)+"\n")
    for name, expected in binding["helper_sha256"].items():
        shutil.copyfile(SCRIPTS / name, folder / name)
        require(sha(folder / name) == expected, f"executed helper changed: {name}")
    parent = psutil.Process()
    original_affinity = parent.cpu_affinity()
    parent.cpu_affinity([0])
    env = os.environ.copy(); env.update(ENV)
    command = [str(PYTHON), "-u", str(Path(__file__).resolve()), "--child", "--output", str(folder)]
    started = time.perf_counter()
    peak_rss = peak_threads = 0
    reason = child_affinity = proc = None
    try:
        with (folder / "stdout.log").open("wb") as stdout, (folder / "stderr.log").open("wb") as stderr:
            proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                                    creationflags=0x4)
            process = psutil.Process(proc.pid)
            process.cpu_affinity([0]); child_affinity = process.cpu_affinity()
            require(child_affinity == [0], "child affinity setup failed")
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
    result = folder / "result.json"
    receipt = {"status": reason or ("completed" if proc and proc.returncode == 0 and result.exists()
                                    else "failed"), "command": command,
               "process_wall_seconds": elapsed, "max_wall_seconds": MAX_WALL,
               "fresh_180_second_ledger_consumed": elapsed,
               "remaining_of_180_seconds": 180.0-elapsed, "reserved_final_seconds": 60.0,
               "peak_process_tree_rss_bytes": peak_rss, "max_process_tree_rss_bytes": MAX_RSS,
               "peak_process_tree_threads": peak_threads, "child_affinity_before_resume": child_affinity,
               "requested_environment": ENV, "exit_code": proc.returncode if proc else None,
               "source_sha256": sha(folder / "executed-source.py"),
               "helper_sha256": {name: sha(folder / name) for name in HELPERS},
               "preflight_sha256": sha(folder / "preflight.json"),
               "result_sha256": sha(result) if result.exists() else None,
               "external_solver_children": 0, "historical_case_replays": 0}
    (folder / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True)+"\n")
    print(json.dumps({key: receipt[key] for key in ("status", "process_wall_seconds",
          "peak_process_tree_rss_bytes", "exit_code")}))
    require(receipt["status"] == "completed", "saved comparator failed; inspect retained receipt/logs")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--output", type=Path, default=OUT / "saved-adjudication-v1")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(), sort_keys=True))
    elif args.child:
        child(args.output)
    else:
        supervise(args.output)


if __name__ == "__main__":
    main()
