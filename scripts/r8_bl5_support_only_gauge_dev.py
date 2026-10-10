"""One saved-operator BL5 support-only nullity and explicit yaw-gauge diagnostic.

This development tool does not import OpenSees or change any product/source gate.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import struct
import sys
import time
import traceback
import zipfile

import r8_bl5_external_operator_dev as identity
import r8_bl5_external_operator_crosscase_dev as crosscase


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PARENT = ROOT / "docs/agent_plans/development/r8-bl5-support-only-gauge-20261009"
NATIVE = crosscase.NATIVE
CAPTURE = crosscase.CAPTURE
CROSSCASE = crosscase.REPORT / "crosscase-v1"
PYTHON = Path(r"C:\Python\Python314\python.exe")
SITE = Path(r"C:\Python\Python314\Lib\site-packages")
ENV = {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
       "NUMBA_NUM_THREADS": "1", "NUMBA_DISABLE_JIT": "1"}
MAX_WALL = 30.0
MAX_RSS = 2 * 1024**3
VARIANTS = (0.1, 1.0, 10.0)
ZERO_THRESHOLDS = (1e-8, 1e-10, 1e-12)
HELPERS = {"r8_bl5_external_operator_dev.py": identity,
           "r8_bl5_external_operator_crosscase_dev.py": crosscase}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def require_exact_binding(actual: str, expected: str, name: str) -> None:
    identity.require(isinstance(expected, str) and len(expected) == 64 and actual == expected,
                     f"{name} SHA-256 missing or changed")


def archived_integer_array(archive: Path, name: str) -> list[int]:
    """Read only a constrained integer NPY member without importing a numeric runtime."""
    with zipfile.ZipFile(archive) as bundle:
        raw = bundle.read(f"{name}.npy")
    identity.require(raw[:6] == b"\x93NUMPY" and raw[6] in (1, 2, 3),
                     f"{name} NPY format changed")
    prefix = 10 if raw[6] == 1 else 12
    header_size = struct.unpack("<H" if prefix == 10 else "<I", raw[8:prefix])[0]
    header = ast.literal_eval(raw[prefix:prefix+header_size].decode("latin1"))
    count, = header["shape"]
    fmt = {"<i8": "q", "<i4": "i"}.get(header["descr"])
    identity.require(fmt is not None and not header["fortran_order"] and count == 35,
                     f"{name} saved integer shape/type changed")
    return list(struct.unpack(f"<{count}{fmt}", raw[prefix+header_size:]))


def layout_fixed_indices(layout: dict) -> list[int]:
    shell_nodes = layout["shell_node_ids"]
    beam_nodes = layout["beam_node_ids"]
    mapped = []
    for role, node, dof in layout["fixed_coordinates"]:
        identity.require(type(node) is int and type(dof) is int and 0 <= dof < 6,
                         "layout fixed coordinate malformed")
        if role == "shell":
            identity.require(node in shell_nodes, "layout fixed shell node absent")
            mapped.append(6*shell_nodes.index(node)+dof)
        elif role == "beam":
            identity.require(node in beam_nodes, "layout fixed beam node absent")
            mapped.append(6*len(shell_nodes)+6*beam_nodes.index(node)+dof)
        else:
            raise identity.IdentityError("layout fixed role unsupported")
    identity.require(len(mapped) == len(set(mapped)) == 35, "layout fixed index count changed")
    return sorted(mapped)


def helper_source_binding() -> dict[str, str]:
    bound = {}
    for filename, module in HELPERS.items():
        source = ROOT / "scripts" / filename
        identity.require(Path(module.__file__).resolve() == source.resolve(),
                         f"{filename} imported from unexpected location")
        blob = subprocess.run(["git", "show", f"HEAD:scripts/{filename}"], cwd=ROOT,
                              check=True, capture_output=True).stdout
        require_exact_binding(sha(source), hashlib.sha256(blob).hexdigest(), filename)
        bound[filename] = sha(source)
    return bound


def validate_saved_context(context: dict) -> None:
    identity.require(context.get("head", "").startswith("75a185b2"),
                     "frozen worktree commit 75a185b2 required")
    identity.require(context.get("native_dimension") == 1092 and
                     context.get("external_dimension") == 708 and
                     context.get("native_fixed") == context.get("external_fixed") == 35 and
                     context.get("cases") == ["fy", "mx", "mz"],
                     "fixed support, dimensions or saved load family changed")
    for key in ("native_operator_sha256", "external_raw_sha256", "crosscase_arrays_sha256",
                "crosscase_result_sha256", "native_layout_sha256"):
        identity.require(isinstance(context.get(key), str) and len(context[key]) == 64,
                         f"{key} identity absent")
    identity.require(context.get("native_fixed_indices") == context.get("native_layout_fixed_indices") and
                     len(context.get("native_fixed_indices", [])) == 35,
                     "archived native fixed indices differ from declared layout")
    sources = context.get("helper_sources_sha256", {})
    identity.require(set(sources) == set(HELPERS) and
                     all(isinstance(value, str) and len(value) == 64 for value in sources.values()),
                     "imported helper source identity absent")


def preflight() -> dict:
    spec = identity.fixture_preflight()
    captured_path = CAPTURE / "raw.json"
    captured_receipt = json.loads((CAPTURE / "receipt.json").read_text())
    require_exact_binding(sha(captured_path), captured_receipt.get("raw_sha256"), "external raw")
    require_exact_binding(sha(CAPTURE / "executed-capture-source.py"),
                          captured_receipt.get("source_sha256"), "executed capture source")
    identity.require(captured_receipt.get("status") == "completed", "completed external capture required")
    mapped = identity.validate_fullgeneral_capture(spec, json.loads(captured_path.read_text()))
    native_inputs = json.loads((NATIVE / "inputs.json").read_text())
    require_exact_binding(sha(NATIVE / "operators.npz"), native_inputs.get("operators_sha256"),
                          "native operator")
    layout = json.loads((NATIVE / "layout.json").read_text())
    identity.require(layout["nx"] == 16 and layout["ny"] == 4 and
                     layout["counts"]["full_q"] == 1092 and len(layout["fixed_coordinates"]) == 35,
                     "matched native 16x4 layout required")
    declared_fixed = layout_fixed_indices(layout)
    archived_fixed = sorted(archived_integer_array(NATIVE / "operators.npz", "fixed"))
    identity.require(archived_fixed == declared_fixed,
                     "archived native fixed indices differ from declared layout")
    result_path, arrays_path, receipt_path = (CROSSCASE / name for name in
                                             ("result.json", "arrays.npz", "receipt.json"))
    prior = json.loads(result_path.read_text())
    prior_receipt = json.loads(receipt_path.read_text())
    identity.require(prior.get("status") == "crosscase_and_support_checks_passed_development_only"
                     and prior_receipt.get("status") == "completed", "completed saved cross-case required")
    require_exact_binding(sha(result_path), prior_receipt.get("result_sha256"), "cross-case result")
    require_exact_binding(sha(arrays_path), prior.get("arrays_sha256"), "cross-case arrays")
    require_exact_binding(sha(CROSSCASE / "executed-source.py"), prior_receipt.get("source_sha256"),
                          "executed cross-case source")
    native_loads = {case: crosscase.bound_native_load(case) for case in ("fy", "mx", "mz")}
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout.strip()
    context = {"status": "saved_input_preflight_passed", "head": head,
               "native_dimension": 1092, "external_dimension": 708,
               "native_fixed": 35, "external_fixed": len(spec["fixed_dofs"]),
               "native_fixed_indices": archived_fixed,
               "native_layout_fixed_indices": declared_fixed,
               "helper_sources_sha256": helper_source_binding(),
               "cases": ["fy", "mx", "mz"],
               "native_operator_sha256": sha(NATIVE / "operators.npz"),
               "native_inputs_sha256": sha(NATIVE / "inputs.json"),
               "native_layout_sha256": sha(NATIVE / "layout.json"),
               "external_raw_sha256": sha(captured_path),
               "external_receipt_sha256": sha(CAPTURE / "receipt.json"),
               "crosscase_arrays_sha256": sha(arrays_path),
               "crosscase_result_sha256": sha(result_path),
               "crosscase_receipt_sha256": sha(receipt_path),
               "physical_equation_ids_sha256": mapped["physical_equation_ids_sha256"],
               "native_loads": native_loads,
               "reference_scales": "native saved coordinate_scale; external translations 1 m, rotations 1 rad; positive row-absolute congruence equilibration",
               "variants_translation_factor": VARIANTS,
               "zero_thresholds_relative_to_scaled_operator": ZERO_THRESHOLDS}
    validate_saved_context(context)
    return context


def spectrum(k, free, base_scale, translation_indices, np, name):
    """Complete signed spectra under work-conjugate, row-equilibrated scales."""
    base = np.asarray(base_scale, dtype=float)
    identity.require(np.isfinite(base).all() and np.all(base > 0), f"{name} positive scales required")
    reports = []
    for factor in VARIANTS:
        scale = base.copy()
        scale[translation_indices] *= factor
        d = scale[free]
        physical = (d[:, None]*k[np.ix_(free, free)])*d[None, :]
        row_sum = np.sum(abs(physical), axis=1)
        identity.require(np.all(row_sum > 0) and np.isfinite(row_sum).all(),
                         f"{name} zero/nonfinite equilibrated row")
        e = 1.0/np.sqrt(row_sum)
        balanced = (e[:, None]*physical)*e[None, :]
        eig = np.linalg.eigvalsh(balanced)
        largest = float(np.max(abs(eig)))
        ordered = np.sort(abs(eig))
        counts = {str(t): int(np.count_nonzero(ordered <= t*largest)) for t in ZERO_THRESHOLDS}
        nearest = float(ordered[1]/largest)
        reports.append({"translation_factor": factor, "counts": counts,
                        "smallest_abs_ratio": float(ordered[0]/largest),
                        "next_abs_ratio": nearest,
                        "negative_count": int(np.count_nonzero(eig < -1e-10*largest)),
                        "positive_count": int(np.count_nonzero(eig > 1e-10*largest)),
                        "largest_abs_scaled": largest,
                        "scale_min": float(np.min(d)), "scale_max": float(np.max(d)),
                        "row_equilibration_min": float(np.min(e)),
                        "row_equilibration_max": float(np.max(e))})
    identity.require(all(all(value == 1 for value in report["counts"].values())
                         for report in reports),
                     f"{name} support-only numerical nullity differs from one yaw or is scale-sensitive")
    return reports


def gauge_solve(k, fixed, gauge, yaw, rhs_by_case, reference_by_case, scale, np, la, name, reports):
    n = k.shape[0]
    identity.require(gauge not in set(fixed) and abs(float(yaw[gauge])-1.0) <= 1e-15,
                     f"{name} one free unit yaw gauge required")
    solve_ids = np.asarray([i for i in range(n) if i not in set(fixed) and i != gauge], dtype=int)
    original_free = np.asarray([i for i in range(n) if i not in set(fixed)], dtype=int)
    factor = la.lu_factor(k[np.ix_(solve_ids, solve_ids)])
    for case, rhs in rhs_by_case.items():
        report = reports.setdefault(case, {"status": "started"})
        work = float(yaw @ rhs)
        work_scale = max(float(np.sum(abs(yaw*rhs))), 1e-12)
        report.update({"yaw_load_work_Nm": work, "yaw_work_scale_Nm": work_scale})
        identity.require(abs(work)/work_scale <= 1e-8,
                         f"{name} {case} incompatible yaw work")
        q = np.zeros(n)
        q[solve_ids] = la.lu_solve(factor, rhs[solve_ids])
        residual = k@q-rhs
        weighted = abs(residual[original_free]*scale[original_free])
        denominator = max(float(np.sum(abs(rhs[original_free]*scale[original_free]))), 1e-12)
        ratio = float(np.sum(weighted)/denominator)
        gauge_reaction = float(residual[gauge]*scale[gauge])
        shifted = q+1e-6*yaw
        gauge_invariance = float(np.max(abs(k@shifted-k@q)))
        row_scale = np.asarray(abs(k)@abs(1e-6*yaw)).reshape(-1)
        invariant_ratio = gauge_invariance/max(1.0, float(np.max(row_scale)))
        reference = reference_by_case[case]
        aligned_reference = reference-reference[gauge]*yaw
        difference = q-aligned_reference
        relative = float(np.linalg.norm(difference/scale)/max(1e-12, np.linalg.norm(aligned_reference/scale)))
        report.update({"original_free_work_scaled_residual_ratio": ratio,
                       "original_free_work_scaled_residual_abs_sum": float(np.sum(weighted)),
                       "original_free_max_abs_dual": float(np.max(abs(residual[original_free]))),
                       "gauge_reaction_work_scaled": gauge_reaction,
                       "Kq_yaw_shift_max_abs": gauge_invariance,
                       "Kq_yaw_shift_row_relative": invariant_ratio,
                       "aligned_saved_coupled_state_relative_scaled_difference_context_only": relative,
                       "fixed_reaction_dual_original_units": residual[fixed].tolist(),
                       "fixed_reaction_work_norm": float(np.sum(abs(residual[fixed]*scale[fixed]))),
                       "saved_yaw_coordinate": float(reference[gauge])})
        identity.require(ratio <= 1e-8, f"{name} {case} original-free equilibrium failed")
        identity.require(abs(gauge_reaction) <= 1e-8*work_scale,
                         f"{name} {case} non-negligible gauge reaction")
        identity.require(invariant_ratio <= 1e-8,
                         f"{name} {case} Kq changes under yaw representative")
        report["status"] = "passed_development_only"
    return reports


def child(folder: Path) -> None:
    result = {"status": "failed", "classification": "saved support-only quotient diagnostic, not F03 acceptance",
              "source_sha256": sha(Path(__file__)), "environment": {k: os.environ.get(k) for k in ENV},
              "python": sys.version, "cases": {}}
    try:
        identity.require(all(result["environment"][k] == v for k, v in ENV.items()),
                         "one-thread/JIT-off environment missing")
        import numpy as np
        import scipy.linalg as la
        import scipy.sparse as sparse
        import psutil
        from threadpoolctl import threadpool_info
        pools = threadpool_info()
        identity.require(pools and all(pool["num_threads"] == 1 for pool in pools),
                         "one effective BLAS thread required")
        identity.require(psutil.Process().cpu_affinity() == [0], "CPU0 affinity required")
        result["runtime"] = {"affinity": [0], "blas_pools": pools,
                             "numpy": np.__version__, "scipy": __import__("scipy").__version__}
        binding = preflight()
        result["bound_inputs"] = binding
        spec = identity.fixture_preflight()
        raw = json.loads((CAPTURE / "raw.json").read_text())
        mat = np.asarray(raw["printA"], dtype=float).reshape((783, 783))
        physical_ids = np.asarray([raw["node_dofs"][str(node)][dof-1] for node, dof in spec["dof_order"]], dtype=int)
        other_ids = np.asarray(sorted(set(range(783))-set(physical_ids)), dtype=int)
        ke = mat[np.ix_(physical_ids, physical_ids)]
        be = mat[np.ix_(physical_ids, other_ids)]/spec["alpha_mp"]
        fixed_e = np.asarray([spec["dof_order"].index(pair) for pair in spec["fixed_dofs"]], dtype=int)
        gauge_e = spec["dof_order"].index((100001, 6))
        with np.load(NATIVE / "operators.npz", allow_pickle=False) as archive:
            op = {key: np.array(archive[key], copy=True) for key in archive.files}
        kn = sparse.csr_matrix((op["K_data"], op["K_indices"], op["K_indptr"]),
                               shape=tuple(op["K_shape"])).toarray()
        cn = sparse.csr_matrix((op["C_data"], op["C_indices"], op["C_indptr"]),
                               shape=tuple(op["C_shape"]))
        fixed_n = np.asarray(op["fixed"], dtype=int)
        gauge_n = 6*85+5
        yaw_n = np.asarray(op["beam_rigid_work_map"][5], dtype=float)
        with np.load(CROSSCASE / "arrays.npz", allow_pickle=False) as saved:
            yaw_e = np.array(saved["external_yaw"], copy=True)
            yaw_n_saved = np.array(saved["native_yaw"], copy=True)
            identity.require(np.array_equal(yaw_n, yaw_n_saved), "native full retained yaw changed")
            mu = {case: np.array(saved[f"{case}_inferred_normalized_mu"], copy=True) for case in ("fy", "mx", "mz")}
            native_density = {case: np.array(saved[f"{case}_native_density"], copy=True) for case in ("fy", "mx", "mz")}
            external_load = {case: np.array(saved[f"{case}_frozen_load"], copy=True) for case in ("fy", "mx", "mz")}
            native_load = {case: np.array(saved[f"{case}_native_load"], copy=True) for case in ("fy", "mx", "mz")}
        identity.require(kn.shape == (1092, 1092) and ke.shape == (708, 708) and
                         cn.shape == (40, 1092) and yaw_n.shape == (1092,) and yaw_e.shape == (708,),
                         "saved operators, connections or yaw dimensions changed")
        identity.require(np.array_equal(np.sort(np.r_[op["fixed"], op["free"]]), np.arange(1092)) and
                         not set(op["fixed"]) & set(op["free"]),
                         "native original fixed/free partition changed")
        symmetry = {"native": float(np.max(abs(kn-kn.T))),
                    "external": float(np.max(abs(ke-ke.T)))}
        identity.require(symmetry["native"] <= 1e-12*float(np.max(abs(kn))) and
                         symmetry["external"] <= 1e-12*float(np.max(abs(ke))),
                         "saved physical operator is not symmetric")
        result["operator_symmetry_max_abs"] = symmetry
        identity.require(np.max(abs(yaw_e[fixed_e]), initial=0.0) == 0.0 and
                         np.max(abs(yaw_n[fixed_n]), initial=0.0) == 0.0 and
                         yaw_e[gauge_e] == yaw_n[gauge_n] == 1.0,
                         "known physical yaw must satisfy original supports and unit gauge")
        result["physical_yaw_annihilation"] = {
            "native": crosscase.yaw_annihilation(kn, yaw_n, np, "native"),
            "external": crosscase.yaw_annihilation(ke, yaw_e, np, "external")}
        # Full physical work-conjugate scales; original native resultant roles remain.
        scale_n = np.asarray(op["coordinate_scale"], dtype=float)
        scale_e = np.ones(708)
        translation_n = np.asarray([i for i in range(708) if i % 6 < 3], dtype=int)
        translation_e = np.asarray([i for i, (_, dof) in enumerate(spec["dof_order"]) if dof <= 3], dtype=int)
        result["spectra"] = {
            "native": spectrum(kn, np.asarray(op["free"], dtype=int), scale_n, translation_n, np, "native"),
            "external": spectrum(ke, np.asarray([i for i in range(708) if i not in set(fixed_e)], dtype=int),
                                 scale_e, translation_e, np, "external")}
        # A complete signed-spectrum screen must pass before any quotient solve.
        mp_columns = [i for i, row in enumerate(identity.validate_fullgeneral_capture(spec, raw)["constraint_equations"])
                      if row["kind"] == "MP"]
        rhs_e = {case: external_load[case]-be[:, mp_columns]@mu[case][mp_columns]
                 for case in ("fy", "mx", "mz")}
        rhs_n = {case: native_load[case]-cn.T@native_density[case]
                 for case in ("fy", "mx", "mz")}
        saved_e = {case: np.asarray(spec["cases"][case]["displacement"], dtype=float)
                   for case in ("fy", "mx", "mz")}
        saved_n = {}
        for case in ("fy", "mx", "mz"):
            with np.load(NATIVE / case / "raw-state.npz", allow_pickle=False) as archive:
                saved_n[case] = np.asarray(archive["q"], dtype=float)
        result["gauge_solve"] = {}
        result["gauge_solve"]["external"] = {}
        gauge_solve(ke, fixed_e, gauge_e, yaw_e, rhs_e, saved_e, scale_e, np, la,
                    "external", result["gauge_solve"]["external"])
        result["gauge_solve"]["native"] = {}
        gauge_solve(kn, fixed_n, gauge_n, yaw_n, rhs_n, saved_n, scale_n, np, la,
                    "native", result["gauge_solve"]["native"])
        result["status"] = "one_yaw_quotient_passed_development_only"
    except BaseException as error:
        result["failure"] = {"type": type(error).__name__, "message": str(error),
                             "traceback": traceback.format_exc()}
    finally:
        save(folder / "result.json", result)
    if result["status"] != "one_yaw_quotient_passed_development_only":
        raise RuntimeError(result["failure"]["message"])


def supervise(folder: Path) -> None:
    if folder.exists():
        raise FileExistsError("fresh output directory required")
    binding = preflight()
    sys.path.insert(0, str(SITE))
    import psutil
    identity.require(PYTHON.is_file() and 0 in psutil.Process().cpu_affinity(),
                     "Python3.14/CPU0 unavailable")
    folder.mkdir(parents=True)
    shutil.copyfile(__file__, folder / "executed-source.py")
    for filename in HELPERS:
        shutil.copyfile(ROOT / "scripts" / filename, folder / filename)
        require_exact_binding(sha(folder / filename), binding["helper_sources_sha256"][filename],
                              f"executed helper snapshot {filename}")
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
            identity.require(affinity == [0], "child CPU0 affinity missing")
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
               "helper_sources_sha256": {filename: sha(folder / filename) for filename in HELPERS},
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
        raise RuntimeError("support-only diagnostic failed; inspect retained result/receipt/logs")


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
