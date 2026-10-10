"""Source-bound BL5 common-density response and exact linear discrepancy diagnostic."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import time
import traceback
import zipfile

import r8_bl5_external_operator_dev as identity
import r8_bl5_external_operator_crosscase_dev as crosscase
import r8_bl5_support_only_gauge_dev as gauge


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/agent_plans/development/r8-bl5-common-density-response-20261009"
NATIVE = crosscase.NATIVE
CAPTURE = crosscase.CAPTURE
CROSSCASE = crosscase.REPORT / "crosscase-v1"
GAUGE = gauge.OUTPUT_PARENT / "run-v2"
PYTHON = Path(r"C:\Python\Python314\python.exe")
SITE = Path(r"C:\Python\Python314\Lib\site-packages")
ENV = {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
       "NUMBA_NUM_THREADS": "1", "NUMBA_DISABLE_JIT": "1"}
HELPERS = {"r8_bl5_external_operator_dev.py": identity,
           "r8_bl5_external_operator_crosscase_dev.py": crosscase,
           "r8_bl5_support_only_gauge_dev.py": gauge}
MAX_WALL = 40.0
MAX_RSS = 2*1024**3
TRANSLATION_FLOOR_M = 1e-12
ROTATION_FLOOR_RAD = 1e-12
FORCE_FLOOR_N = 1e-9
MOMENT_FLOOR_NM = 1e-9
TRANSLATION_CLOSURE_FLOOR_M = 1e-16
ROTATION_CLOSURE_FLOOR_RAD = 5e-16
WORK_CLOSURE_FLOOR_J = 1e-18
RELATIVE_CLOSURE_LIMIT = 1e-8


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def require_binding(actual: str, expected: str, name: str) -> None:
    identity.require(isinstance(expected, str) and len(expected) == 64 and actual == expected,
                     f"{name} SHA-256 absent or changed")


def npz_vector(path: Path, key: str) -> list[float]:
    """Decode a constrained one-dimensional float64 NPY member without NumPy."""
    with zipfile.ZipFile(path) as bundle:
        raw = bundle.read(f"{key}.npy")
    identity.require(raw[:6] == b"\x93NUMPY" and raw[6] in (1, 2, 3),
                     f"{key} NPY format changed")
    offset = 10 if raw[6] == 1 else 12
    size = struct.unpack("<H" if offset == 10 else "<I", raw[8:offset])[0]
    header = ast.literal_eval(raw[offset:offset+size].decode("latin1"))
    identity.require(header["descr"] == "<f8" and not header["fortran_order"] and
                     len(header["shape"]) == 1, f"{key} floating vector type changed")
    count = header["shape"][0]
    identity.require(len(raw) == offset+size+8*count, f"{key} NPY byte count changed")
    return list(struct.unpack(f"<{count}d", raw[offset+size:]))


def validate_native_geometry(native_inputs: dict, layout: dict, model: dict) -> dict:
    entries = layout["typed_physical_nodes"]
    xyz = native_inputs["xyz_m"]
    identity.require(len(entries) == len(xyz) == 118 and len(model["physical_node_order"]) == 118,
                     "native/external physical node count changed")
    identity.require([row["external_node"] for row in entries] == model["physical_node_order"],
                     "native/external physical node order changed")
    for row, point in zip(entries, xyz):
        expected = model["nodes"][row["external_node"]]
        identity.require(len(point) == 3 and max(abs(a-b) for a, b in zip(point, expected)) <= 1e-14,
                         f"physical geometry differs at {row['external_node']}")
    identity.require(entries[0]["q_offset"] == 0 and entries[-1]["q_offset"] == 702 and
                     all(row["q_offset"] == 6*i for i, row in enumerate(entries)),
                     "native physical coordinate mapping changed")
    return {"nodes": 118, "max_coordinate_difference_m": 1e-14,
            "physical_order_sha256": hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()}


def validate_density_mapping(source: list[float], native: list[float]) -> None:
    identity.require(len(source) == len(native) == 40, "P0 density size changed")
    expected = [0.0]*40
    for j in range(8):
        expected[j] = -source[5*j]
        expected[8+j] = -source[5*j+1]
        expected[16+j] = -source[5*j+2]
        expected[24+j] = -source[5*j+4]
        expected[32+j] = source[5*j+3]
    identity.require(native == expected, "P0 source/native density channel map changed")


def helper_binding() -> dict[str, str]:
    hashes = {}
    for filename, module in HELPERS.items():
        source = ROOT / "scripts" / filename
        identity.require(Path(module.__file__).resolve() == source.resolve(),
                         f"{filename} imported from unexpected path")
        blob = subprocess.run(["git", "show", f"HEAD:scripts/{filename}"], cwd=ROOT,
                              capture_output=True, check=True).stdout
        require_binding(sha(source), hashlib.sha256(blob).hexdigest(), filename)
        hashes[filename] = sha(source)
    return hashes


def preflight() -> dict:
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout.strip()
    identity.require(head.startswith("c64d189e"), "committed c64d189e input state required")
    spec = identity.fixture_preflight()
    raw_path = CAPTURE / "raw.json"
    captured_receipt = json.loads((CAPTURE / "receipt.json").read_text())
    require_binding(sha(raw_path), captured_receipt.get("raw_sha256"), "FullGeneral raw")
    require_binding(sha(CAPTURE / "executed-capture-source.py"),
                    captured_receipt.get("source_sha256"), "FullGeneral executed source")
    mapped = identity.validate_fullgeneral_capture(spec, json.loads(raw_path.read_text()))
    native_inputs = json.loads((NATIVE / "inputs.json").read_text())
    layout = json.loads((NATIVE / "layout.json").read_text())
    require_binding(sha(NATIVE / "operators.npz"), native_inputs.get("operators_sha256"),
                    "native operator")
    identity.require(layout["nx"] == 16 and layout["ny"] == 4 and
                     layout["counts"]["full_q"] == 1092 and
                     len(layout["fixed_coordinates"]) == len(spec["fixed_dofs"]) == 35,
                     "physical discretization/support count changed")
    fixed = gauge.layout_fixed_indices(layout)
    identity.require(fixed == sorted(gauge.archived_integer_array(NATIVE / "operators.npz", "fixed")),
                     "native archived support indices changed")
    model = identity.import_recipe().geometry(16, identity.import_recipe().services()[3])
    geometry = validate_native_geometry(native_inputs, layout, model)
    identity.require([list(row) for row in spec["fixed_dofs"]] ==
                     [[row["external_node"], dof+1] for role, node, dof in layout["fixed_coordinates"]
                      for row in layout["typed_physical_nodes"] if row["domain"] == role and
                      row["native_node"] == node], "fixed support coordinate map changed")
    prior = json.loads((CROSSCASE / "result.json").read_text())
    prior_receipt = json.loads((CROSSCASE / "receipt.json").read_text())
    identity.require(prior.get("status") == "crosscase_and_support_checks_passed_development_only" and
                     prior_receipt.get("status") == "completed", "saved cross-case status changed")
    require_binding(sha(CROSSCASE / "result.json"), prior_receipt.get("result_sha256"),
                    "cross-case result")
    require_binding(sha(CROSSCASE / "arrays.npz"), prior.get("arrays_sha256"),
                    "cross-case arrays")
    require_binding(sha(CROSSCASE / "executed-source.py"), prior_receipt.get("source_sha256"),
                    "cross-case executed source")
    gauge_result = json.loads((GAUGE / "result.json").read_text())
    gauge_receipt = json.loads((GAUGE / "receipt.json").read_text())
    identity.require(gauge_result.get("status") == "one_yaw_quotient_passed_development_only" and
                     gauge_receipt.get("status") == "completed", "prior one-yaw quotient missing")
    require_binding(sha(GAUGE / "result.json"), gauge_receipt.get("result_sha256"),
                    "one-yaw result")
    require_binding(sha(GAUGE / "executed-source.py"), gauge_receipt.get("source_sha256"),
                    "one-yaw executed source")
    cases = {}
    for case in ("fy", "mx", "mz"):
        load = npz_vector(CROSSCASE / "arrays.npz", f"{case}_frozen_load")
        native_load = npz_vector(CROSSCASE / "arrays.npz", f"{case}_native_load")
        native_archive = npz_vector(NATIVE / case / "raw-state.npz", "load")
        identity.require(load == spec["cases"][case]["applied_load"] and
                         len(load) == 708 and len(native_load) == 1092 and
                         native_load == native_archive and native_load[:708] == load and
                         all(value == 0 for value in native_load[708:]),
                         f"{case} physical load/retained load changed")
        load_binding = crosscase.bound_native_load(case)
        source = npz_vector(CROSSCASE / "arrays.npz", f"{case}_inferred_source_density")
        density = npz_vector(CROSSCASE / "arrays.npz", f"{case}_native_density")
        validate_density_mapping(source, density)
        cases[case] = {"native_load_binding": load_binding,
                       "source_density_sha256": hashlib.sha256(json.dumps(source).encode()).hexdigest()}
    return {"status": "source_only_preflight_passed", "head": head,
            "geometry": geometry, "cases": cases,
            "helpers_sha256": helper_binding(),
            "external_raw_sha256": sha(raw_path),
            "native_operator_sha256": sha(NATIVE / "operators.npz"),
            "native_inputs_sha256": sha(NATIVE / "inputs.json"),
            "native_layout_sha256": sha(NATIVE / "layout.json"),
            "crosscase_arrays_sha256": sha(CROSSCASE / "arrays.npz"),
            "gauge_result_sha256": sha(GAUGE / "result.json"),
            "physical_equation_ids_sha256": mapped["physical_equation_ids_sha256"],
            "fixed_indices": fixed,
            "unit_floors": {"translation_m": TRANSLATION_FLOOR_M,
                            "rotation_rad": ROTATION_FLOOR_RAD,
                            "force_N": FORCE_FLOOR_N, "moment_Nm": MOMENT_FLOOR_NM}}


def require_independent_domains(k, shell_size: int, name: str, np) -> dict:
    cross = k[:shell_size, shell_size:]
    peak = float(np.max(abs(cross), initial=0.0))
    scale = max(float(np.max(abs(k))), 1.0)
    identity.require(peak <= 1e-12*scale,
                     f"{name} shell/beam body cross block prevents independent attribution")
    return {"cross_max_abs": peak, "relative_to_operator_max": peak/scale}


def schur_effective_rhs(physical_rhs, retained_rhs, apply_coupling, solve_retained):
    """Include a retained dual load when reducing the signed mixed equations."""
    inverse_retained_rhs = solve_retained(retained_rhs)
    return physical_rhs-apply_coupling(inverse_retained_rhs), inverse_retained_rhs


def validate_fixed_support_map(fixed_indices: list[int], spec: dict) -> int:
    expected = [spec["dof_order"].index(pair) for pair in spec["fixed_dofs"]]
    gauge_index = spec["dof_order"].index((100001, 6))
    identity.require(len(expected) == len(fixed_indices) == 35 and
                     set(expected) == set(fixed_indices) and gauge_index not in fixed_indices and
                     sorted(pair for pair in spec["fixed_dofs"] if pair[0] == 100001) ==
                     [(100001, dof) for dof in range(1, 6)],
                     "original 30 shell + five beam fixed support map changed")
    return gauge_index


def response_closure(total, shell, beam, action) -> dict:
    identity.require(len(total) == len(shell) == len(beam) == len(action) == 708,
                     "physical response closure vector dimension changed")
    report = {}
    for label, slots, floor in (("translation_m", [i for i in range(708) if i%6 < 3],
                                 TRANSLATION_CLOSURE_FLOOR_M),
                                ("rotation_rad", [i for i in range(708) if i%6 >= 3],
                                 ROTATION_CLOSURE_FLOOR_RAD)):
        error = max(abs(float(total[i])-math.fsum((float(shell[i]), float(beam[i]),
                                                  float(action[i])))) for i in slots)
        scale = max(sum(abs(float(v[i])) for v in (shell, beam, action)) for i in slots)
        limit = RELATIVE_CLOSURE_LIMIT*scale+floor
        identity.require(error <= limit, f"{label} whole-signal response allocation does not close")
        report[label] = {"max_abs_error": error, "sum_abs_term_scale": scale,
                         "limit": limit}
    return report


def work_closure(delta: float, terms: dict[str, float]) -> dict:
    identity.require(set(terms) == {"shell_body", "beam_body", "constraint_action_mapping",
                                    "direct_action_work_J", "retained_source_work_J"},
                     "work-allocation terms absent")
    error = abs(math.fsum(float(value) for value in terms.values())-float(delta))
    scale = math.fsum(abs(float(value)) for value in terms.values())
    limit = RELATIVE_CLOSURE_LIMIT*scale+WORK_CLOSURE_FLOOR_J
    identity.require(error <= limit, "whole-signal mapped work allocation does not close")
    return {"absolute_error_J": error, "sum_abs_term_scale_J": scale, "limit_J": limit}


def saved_fixed_wrench(reactions: list[float], fixed_indices: list[int],
                       spec: dict, model: dict, domain: str) -> list[float]:
    identity.require(len(reactions) == len(fixed_indices) == 35,
                     "fixed reaction vector length changed")
    validate_fixed_support_map(fixed_indices, spec)
    origin = model["nodes"][model["beam_root"]]
    total = [0.0]*6
    for index, value in zip(fixed_indices, reactions):
        node, dof = spec["dof_order"][index]
        is_beam = node in model["beam_node_ids"]
        if is_beam != (domain == "beam"):
            continue
        arm = [model["nodes"][node][axis]-origin[axis] for axis in range(3)]
        if dof <= 3:
            j = dof-1
            total[j] += value
            # r cross F, with F confined to one component.
            total[3+(j+1)%3] += arm[(j+2)%3]*value
            total[3+(j+2)%3] -= arm[(j+1)%3]*value
        else:
            total[dof-1] += value
    return total


def adjudicate_saved_run(path: Path) -> dict:
    """Read-only original-byte adjudication; no solver, factorization or new child."""
    run = OUT / "run-v2"
    receipt = json.loads((run / "receipt.json").read_text())
    result = json.loads((run / "result.json").read_text())
    saved_preflight = json.loads((run / "preflight.json").read_text())
    identity.require(receipt.get("status") == "completed" and
                     result.get("status") == "three_case_common_density_allocation_passed_development_only",
                     "completed immutable common-density run-v2 required")
    for filename, expected in (("result.json", receipt.get("result_sha256")),
                               ("arrays.npz", receipt.get("arrays_sha256")),
                               ("executed-source.py", receipt.get("source_sha256"))):
        require_binding(sha(run / filename), expected, filename)
    require_binding(sha(run / "arrays.npz"), result.get("arrays_sha256"), "saved arrays")
    for filename, expected in receipt["helpers_sha256"].items():
        require_binding(sha(run / filename), expected, filename)
    spec = identity.fixture_preflight()
    model = identity.import_recipe().geometry(16, identity.import_recipe().services()[3])
    external_fixed = [spec["dof_order"].index(pair) for pair in spec["fixed_dofs"]]
    native_fixed = gauge.archived_integer_array(NATIVE / "operators.npz", "fixed")
    validate_fixed_support_map(external_fixed, spec)
    validate_fixed_support_map(native_fixed, spec)
    identity.require(sorted(saved_preflight["fixed_indices"]) == sorted(external_fixed) ==
                     sorted(native_fixed) and saved_preflight["head"].startswith("c64d189e"),
                     "saved support/commit map changed")
    native_scale = npz_vector(NATIVE / "operators.npz", "coordinate_scale")
    gauge_index = spec["dof_order"].index((100001, 6))
    identity.require(native_scale[gauge_index] == 1.0,
                     "native gauge moment scaling changed")
    derived = {"status": "saved_run_v2_source_only_adjudicated", "source_sha256": sha(Path(__file__)),
               "original": {"receipt_sha256": sha(run / "receipt.json"),
                            "result_sha256": sha(run / "result.json"),
                            "arrays_sha256": sha(run / "arrays.npz"),
                            "preflight_sha256": sha(run / "preflight.json"),
                            "executed_source_sha256": sha(run / "executed-source.py")},
               "support": {"fixed_shell_dofs": 30, "fixed_beam_dofs": 5,
                           "free_beam_root_rz_index": gauge_index,
                           "beam_root_rz_is_fixed": False},
               "cases": {}, "interpretation_limit":
               "n16 fixed-density external-resolvent identity only; no causal allocation of original coupled discrepancy or proof of drilling mechanism"}
    arrays_path = run / "arrays.npz"
    for case in ("fy", "mx", "mz"):
        saved_case = result["cases"][case]
        total, shell, beam, action = [npz_vector(arrays_path, f"{case}_{key}") for key in
                                      ("native_minus_external_physical_q", "shell_body_response",
                                       "beam_body_response", "constraint_action_mapping_response")]
        response = response_closure(total, shell, beam, action)
        allocation = saved_case["effective_work_exact_allocation_J"]
        work = work_closure(saved_case["effective_work_native_minus_external_J"], allocation)
        cases = {"response_closure": response, "work_closure": work,
                 "response_magnitude": {
                     "max_abs_translation_m": max(abs(total[i]) for i in range(708) if i%6 < 3),
                     "max_abs_rotation_rad": max(abs(total[i]) for i in range(708) if i%6 >= 3)},
                 "work_allocation_J": allocation,
                 "fixed_root_wrench_N_Nm": {}}
        for label, indices in (("external", external_fixed), ("native", native_fixed)):
            saved_model = saved_case[label]
            reactions = saved_model["fixed_reaction_dual_original_units"]
            shell_wrench = saved_fixed_wrench(reactions, indices, spec, model, "shell")
            beam_wrench = saved_fixed_wrench(reactions, indices, spec, model, "beam")
            old = saved_case["fixed_root_wrench"]
            identity.require(max(abs(a-b) for a, b in zip(shell_wrench, old[f"{label}_shell_N_Nm"])) <= 1e-8 and
                             max(abs(a-b) for a, b in zip(beam_wrench[:5], old[f"{label}_beam_N_Nm"][:5])) <= 1e-8 and
                             abs(old[f"{label}_beam_N_Nm"][5]-
                                 saved_model["gauge_reaction_work_scaled"]) <= 1e-8 and
                             beam_wrench[5] == 0.0,
                             f"{case} {label} saved reaction/gauge separation inconsistent")
            cases["fixed_root_wrench_N_Nm"][label] = {
                "shell_fixed_only": shell_wrench, "beam_five_fixed_only": beam_wrench,
                "free_beam_root_rz_equilibrium_residual_Nm":
                saved_model["gauge_reaction_work_scaled"]}
        derived["cases"][case] = cases
    snapshot = path.with_name(path.stem + "-source.py")
    identity.require(not path.exists() and not snapshot.exists(),
                     "fresh versioned adjudication/source paths required")
    shutil.copyfile(__file__, snapshot)
    require_binding(sha(snapshot), derived["source_sha256"], "adjudication executed source")
    derived["adjudication_source_snapshot"] = snapshot.name
    save(path, derived)
    return derived


def wrench(vector, model, origin, np, node_ids) -> list[float]:
    total = np.zeros(6)
    for node in node_ids:
        row = 6*model["physical_node_order"].index(node)
        force = vector[row:row+3]
        moment = vector[row+3:row+6]
        arm = np.asarray(model["nodes"][node])-origin
        total[:3] += force
        total[3:] += moment+np.cross(arm, force)
    return total.tolist()


def solve_gauged(k, rhs, fixed, gauge_index, yaw, scale, np, la, name, report):
    free = np.asarray([i for i in range(k.shape[0]) if i not in set(fixed)], dtype=int)
    active = free[free != gauge_index]
    identity.require(gauge_index in set(free) and yaw[gauge_index] == 1.0 and
                     float(np.max(abs(yaw[fixed]), initial=0.0)) == 0.0,
                     f"{name} explicit root-yaw gauge/support changed")
    work = float(yaw@rhs)
    work_scale = max(float(np.sum(abs(yaw*rhs))), 1e-12)
    report.update({"yaw_load_work_Nm": work, "yaw_work_scale_Nm": work_scale})
    identity.require(abs(work)/work_scale <= 1e-8, f"{name} incompatible yaw load")
    factor = la.lu_factor(k[np.ix_(active, active)])
    q = np.zeros(k.shape[0])
    q[active] = la.lu_solve(factor, rhs[active])
    residual = k@q-rhs
    weighted = abs(residual[free]*scale[free])
    ratio = float(np.sum(weighted)/max(float(np.sum(abs(rhs[free]*scale[free]))), 1e-12))
    reaction = float(residual[gauge_index]*scale[gauge_index])
    shift = 1e-6*yaw
    effect = float(np.max(abs(k@(q+shift)-k@q)))
    row_contribution = float(np.max(abs(k)@abs(shift)))
    shift_ratio = effect/max(1.0, row_contribution)
    report.update({"free_work_scaled_residual_ratio": ratio,
                   "free_max_abs_dual_original_units": float(np.max(abs(residual[free]))),
                   "fixed_reaction_dual_original_units": residual[fixed].tolist(),
                   "fixed_reaction_work_abs_sum": float(np.sum(abs(residual[fixed]*scale[fixed]))),
                   "gauge_reaction_work_scaled": reaction,
                   "yaw_shift_Kq_max_abs_dual": effect, "yaw_shift_row_relative": shift_ratio})
    identity.require(ratio <= 1e-8 and abs(reaction) <= 1e-8*work_scale and
                     shift_ratio <= 1e-8, f"{name} original-unit gauge equilibrium failed")
    return q, factor, active, residual


def tip_comparison(qe, qn, model, np) -> dict:
    nodes = [node for node in model["shell_node_ids"] if
             abs(model["nodes"][node][0]-1.0) <= 1e-14] + [model["beam_tip"]]
    values = {}
    for node in nodes:
        start = 6*model["physical_node_order"].index(node)
        a, b = qe[start:start+6], qn[start:start+6]
        floor = np.asarray([TRANSLATION_FLOOR_M]*3+[ROTATION_FLOOR_RAD]*3)
        values[str(node)] = {"xyz_m": list(model["nodes"][node]),
                             "external": a.tolist(), "native": b.tolist(),
                             "native_minus_external": (b-a).tolist(),
                             "component_relative_with_unit_floor":
                             (abs(b-a)/np.maximum(np.maximum(abs(a), abs(b)), floor)).tolist()}
    return values


def child(folder: Path) -> None:
    result = {"status": "failed", "classification": "saved common-density development only",
              "source_sha256": sha(Path(__file__)),
              "environment": {key: os.environ.get(key) for key in ENV}, "cases": {}}
    arrays = {}
    try:
        identity.require(result["environment"] == ENV, "one-thread/JIT-off environment changed")
        import numpy as np
        import scipy.linalg as la
        import scipy.sparse as sparse
        import psutil
        from threadpoolctl import threadpool_info
        pools = threadpool_info()
        identity.require(psutil.Process().cpu_affinity() == [0] and pools and
                         all(pool["num_threads"] == 1 for pool in pools),
                         "effective CPU0/one numerical thread unavailable")
        result["runtime"] = {"affinity": [0], "blas_pools": pools,
                             "numpy": np.__version__, "scipy": __import__("scipy").__version__}
        binding = preflight()
        result["bound_inputs"] = binding
        spec = identity.fixture_preflight()
        raw = json.loads((CAPTURE / "raw.json").read_text())
        mapping = identity.validate_fullgeneral_capture(spec, raw)
        matrix = np.asarray(raw["printA"], dtype=float).reshape((783, 783))
        ids = np.asarray([raw["node_dofs"][str(node)][dof-1]
                          for node, dof in spec["dof_order"]], dtype=int)
        other = np.asarray(sorted(set(range(783))-set(ids)), dtype=int)
        ke = matrix[np.ix_(ids, ids)]
        b = matrix[np.ix_(ids, other)]/spec["alpha_mp"]
        mp_columns = [i for i, row in enumerate(mapping["constraint_equations"])
                      if row["kind"] == "MP"]
        with np.load(NATIVE / "operators.npz", allow_pickle=False) as archive:
            op = {key: np.array(archive[key], copy=True) for key in archive.files}
        kn = sparse.csr_matrix((op["K_data"], op["K_indices"], op["K_indptr"]),
                               shape=tuple(op["K_shape"])).toarray()
        cn = sparse.csr_matrix((op["C_data"], op["C_indices"], op["C_indptr"]),
                               shape=tuple(op["C_shape"]))
        identity.require(ke.shape == (708, 708) and kn.shape == (1092, 1092) and
                         cn.shape == (40, 1092), "source operator dimensions changed")
        result["domain_independence"] = {
            "external": require_independent_domains(ke, 510, "external", np),
            "native": require_independent_domains(kn, 510, "native", np)}
        # Native retained variables are all in the beam body. Eliminate them only
        # for a common-physical-space discrepancy identity; retain signed full K
        # for the actual native solve and beam stationary quadratic work.
        rr = np.arange(708, 1092)
        pr = kn[:708, 708:]
        rr_factor = la.lu_factor(kn[np.ix_(rr, rr)])
        eliminated = la.lu_solve(rr_factor, kn[708:, :708])
        kn_effective = kn[:708, :708]-pr@eliminated
        result["condensed_domain_independence"] = require_independent_domains(
            kn_effective, 510, "native condensed", np)
        identity.require(float(np.max(abs(kn_effective-kn_effective.T))) <=
                         1e-10*max(1.0, float(np.max(abs(kn_effective)))),
                         "signed native condensation lost symmetry")
        model = identity.import_recipe().geometry(16, identity.import_recipe().services()[3])
        origin = np.asarray(model["nodes"][model["beam_root"]])
        shell_nodes, beam_nodes = model["shell_node_ids"], model["beam_node_ids"]
        with np.load(CROSSCASE / "arrays.npz", allow_pickle=False) as archive:
            saved = {key: np.array(archive[key], copy=True) for key in archive.files}
        fixed_e = np.asarray([spec["dof_order"].index(pair) for pair in spec["fixed_dofs"]], dtype=int)
        fixed_n = np.asarray(op["fixed"], dtype=int)
        validate_fixed_support_map(fixed_e.tolist(), spec)
        validate_fixed_support_map(fixed_n.tolist(), spec)
        identity.require(np.array_equal(fixed_e, fixed_n), "native/external fixed physical indices differ")
        yaw_e, yaw_n = saved["external_yaw"], saved["native_yaw"]
        identity.require(np.array_equal(yaw_n, op["beam_rigid_work_map"][5]),
                         "native full retained yaw field changed")
        ge, gn = spec["dof_order"].index((100001, 6)), 6*85+5
        identity.require(ge == gn, "common physical yaw-gauge index changed")
        scale_e = np.ones(708)
        scale_n = np.asarray(op["coordinate_scale"], dtype=float)
        external_active = np.asarray([i for i in range(708) if i not in set(fixed_e) and i != ge])
        for case in ("fy", "mx", "mz"):
            report = result["cases"].setdefault(case, {"status": "started"})
            f = saved[f"{case}_frozen_load"]
            fn = saved[f"{case}_native_load"]
            normalized = saved[f"{case}_inferred_normalized_mu"]
            source = saved[f"{case}_inferred_source_density"]
            density = saved[f"{case}_native_density"]
            validate_density_mapping(source.tolist(), density.tolist())
            ce = b[:, mp_columns]@normalized[mp_columns]
            cfull = cn.T@density
            cn_physical = cfull[:708]
            re, rn = f-ce, fn-cfull
            native_effective_rhs, retained_rhs_solution = schur_effective_rhs(
                rn[:708], rn[708:], lambda value: pr@value,
                lambda value: la.lu_solve(rr_factor, value))
            native_effective_connection = f-native_effective_rhs
            report["external"] = {}
            qe, ext_factor, _, ext_residual = solve_gauged(
                ke, re, fixed_e, ge, yaw_e, scale_e, np, la, f"external {case}", report["external"])
            report["native"] = {}
            qn, _, _, nat_residual = solve_gauged(
                kn, rn, fixed_n, gn, yaw_n, scale_n, np, la, f"native {case}", report["native"])
            qnp = qn[:708]
            condensed_residual = kn_effective@qnp-native_effective_rhs
            identity.require(float(np.max(abs(condensed_residual[external_active]))) <= 1e-8,
                             f"{case} retained-coordinate condensation fails physical equilibrium")
            reconstructed_retained = retained_rhs_solution-eliminated@qnp
            retained_reconstruction_ratio = float(np.linalg.norm(
                (reconstructed_retained-qn[708:])/scale_n[708:]) /
                max(1e-12, float(np.linalg.norm(qn[708:]/scale_n[708:]))))
            identity.require(retained_reconstruction_ratio <= 1e-8,
                             f"{case} native retained reconstruction differs from full signed solve")
            action_difference = ce-native_effective_connection
            drhs = native_effective_rhs-re
            h_shell = np.zeros(708)
            h_shell[:510] = (ke[:510, :510]-kn_effective[:510, :510])@qnp[:510]
            h_beam = np.zeros(708)
            h_beam[510:] = (ke[510:, 510:]-kn_effective[510:, 510:])@qnp[510:]
            contributions = {}
            for name, h in (("shell_body", h_shell), ("beam_body", h_beam),
                            ("constraint_action_mapping", drhs)):
                response = np.zeros(708)
                response[external_active] = la.lu_solve(ext_factor, h[external_active])
                contributions[name] = response
                arrays[f"{case}_{name}_response"] = response
            dq = qnp-qe
            response_closure_report = response_closure(
                dq, contributions["shell_body"], contributions["beam_body"],
                contributions["constraint_action_mapping"])
            decomposition_error = max(item["max_abs_error"] for item in response_closure_report.values())
            work = {}
            for label, q, k, load, connection, residual in (
                ("external", qe, ke, f, ce, ext_residual),
                ("native", qn, kn, fn, cfull, nat_residual)):
                domains = {}
                for domain, segment in (("shell", slice(0, 510)),
                                        ("beam", slice(510, len(q)))):
                    d = q[segment]
                    domains[domain] = {"applied_work_J": float(d@load[segment]),
                                       "connection_work_J": float(d@connection[segment]),
                                       "effective_work_J": float(d@(load[segment]-connection[segment])),
                                       "signed_stationary_quadratic_work_J": float(d@(k[segment, segment]@d))}
                net_work = float(q@(load-connection))
                internal = float(q@(k@q))
                identity.require(abs(net_work-internal) <= 1e-8*max(1.0, abs(net_work)),
                                 f"{case} {label} work/equilibrium mismatch")
                work[label] = {"applied_work_J": float(q@load),
                               "connection_work_J": float(q@connection),
                               "effective_work_J": net_work,
                               "signed_internal_stationary_quadratic_work_J": internal,
                               "yaw_applied_work_per_rad_J": float((yaw_e if label == "external" else yaw_n)@load),
                               "yaw_connection_work_per_rad_J": float((yaw_e if label == "external" else yaw_n)@connection),
                               "domains": domains}
            work_allocation = {name: float(re@response) for name, response in contributions.items()}
            work_allocation["direct_action_work_J"] = float(qnp@drhs)
            retained_source_work = float(rn[708:]@retained_rhs_solution)
            work_allocation["retained_source_work_J"] = retained_source_work
            identity.require(abs(work["native"]["effective_work_J"]-
                                 (float(qnp@native_effective_rhs)+retained_source_work)) <=
                             1e-8*max(1.0, abs(work["native"]["effective_work_J"])),
                             f"{case} full signed native work not reconstructed by Schur identity")
            work_difference = work["native"]["effective_work_J"]-work["external"]["effective_work_J"]
            work_closure_report = work_closure(work_difference, work_allocation)
            ext_fixed_only = np.zeros(708)
            nat_fixed_only = np.zeros(708)
            ext_fixed_only[fixed_e] = ext_residual[fixed_e]
            nat_fixed_only[fixed_n] = nat_residual[fixed_n]
            report.update({"work": work, "effective_work_native_minus_external_J": work_difference,
                           "effective_work_exact_allocation_J": work_allocation,
                           "physical_response_max_abs_decomposition_error": decomposition_error,
                           "physical_response_unit_separated_closure": response_closure_report,
                           "effective_work_relative_scale_closure": work_closure_report,
                           "retained_rhs_max_abs_dual_original_units": float(np.max(abs(rn[708:]))),
                           "retained_full_solution_reconstruction_scaled_ratio": retained_reconstruction_ratio,
                           "physical_response_mixed_unit_norm_context_only": {
                               name: float(np.linalg.norm(vector))
                               for name, vector in {**contributions, "total_difference": dq}.items()},
                           "tip": tip_comparison(qe, qnp, model, np),
                           "interface_action": {
                               "external_shell_wrench_N_Nm": wrench(ce, model, origin, np, shell_nodes),
                               "external_beam_wrench_N_Nm": wrench(ce, model, origin, np, beam_nodes),
                               "native_shell_wrench_N_Nm": wrench(cn_physical, model, origin, np, shell_nodes),
                               "native_beam_wrench_N_Nm": wrench(cn_physical, model, origin, np, beam_nodes),
                               "native_effective_shell_wrench_N_Nm": wrench(native_effective_connection, model, origin, np, shell_nodes),
                               "native_effective_beam_wrench_N_Nm": wrench(native_effective_connection, model, origin, np, beam_nodes),
                               "physical_covector_max_abs_difference": float(np.max(abs(ce-cn_physical))),
                               "effective_covector_max_abs_difference": float(np.max(abs(action_difference))),
                               "force_relative_with_floor": float(np.max(abs(action_difference[[i for i in range(708) if i%6<3]])) /
                                   max(FORCE_FLOOR_N, float(np.max(abs(ce[[i for i in range(708) if i%6<3]]))))),
                               "moment_relative_with_floor": float(np.max(abs(action_difference[[i for i in range(708) if i%6>=3]])) /
                                   max(MOMENT_FLOOR_NM, float(np.max(abs(ce[[i for i in range(708) if i%6>=3]])))))},
                           "fixed_root_wrench": {
                               "external_shell_N_Nm": wrench(ext_fixed_only, model, origin, np,
                                                            [node for node in shell_nodes if node in model["root_shell_nodes"]]),
                               "external_beam_N_Nm": wrench(ext_fixed_only, model, origin, np, [model["beam_root"]]),
                               "native_shell_N_Nm": wrench(nat_fixed_only, model, origin, np,
                                                          [node for node in shell_nodes if node in model["root_shell_nodes"]]),
                               "native_beam_N_Nm": wrench(nat_fixed_only, model, origin, np, [model["beam_root"]]),
                               "external_free_beam_root_rz_equilibrium_residual_Nm": float(ext_residual[ge]),
                               "native_free_beam_root_rz_equilibrium_residual_Nm": float(nat_residual[gn])}})
            for label, value in (("external_q", qe), ("native_full_q", qn),
                                 ("external_connection", ce), ("native_full_connection", cfull),
                                 ("native_minus_external_physical_q", dq)):
                arrays[f"{case}_{label}"] = value
            report["status"] = "three_way_exact_development_allocation_passed"
        result["status"] = "three_case_common_density_allocation_passed_development_only"
    except BaseException as error:
        result["failure"] = {"type": type(error).__name__, "message": str(error),
                             "traceback": traceback.format_exc()}
    finally:
        if arrays:
            np.savez_compressed(folder / "arrays.npz", **arrays)
            result["arrays_sha256"] = sha(folder / "arrays.npz")
        save(folder / "result.json", result)
    if result["status"] != "three_case_common_density_allocation_passed_development_only":
        raise RuntimeError(result["failure"]["message"])


def supervise(folder: Path) -> None:
    if folder.exists():
        raise FileExistsError("fresh diagnostic output required")
    binding = preflight()
    sys.path.insert(0, str(SITE))
    import psutil
    identity.require(PYTHON.is_file() and 0 in psutil.Process().cpu_affinity(),
                     "Python3.14/CPU0 unavailable")
    folder.mkdir(parents=True)
    shutil.copyfile(__file__, folder / "executed-source.py")
    for filename, expected in binding["helpers_sha256"].items():
        shutil.copyfile(ROOT / "scripts" / filename, folder / filename)
        require_binding(sha(folder / filename), expected, f"executed helper {filename}")
    save(folder / "preflight.json", binding)
    parent = psutil.Process()
    original_affinity = parent.cpu_affinity()
    parent.cpu_affinity([0])
    env = os.environ.copy()
    env.update(ENV)
    command = [str(PYTHON), "-u", str(Path(__file__).resolve()), "--child", "--output-dir", str(folder)]
    started = time.perf_counter()
    peak_rss, peak_threads, reason, child_affinity = 0, 0, None, None
    proc = None
    try:
        with (folder / "stdout.log").open("wb") as stdout, (folder / "stderr.log").open("wb") as stderr:
            proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=stdout, stderr=stderr,
                                    creationflags=0x4)
            process = psutil.Process(proc.pid)
            process.cpu_affinity([0])
            child_affinity = process.cpu_affinity()
            identity.require(child_affinity == [0], "child CPU0 affinity missing")
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
    arrays_path = folder / "arrays.npz"
    receipt = {"status": reason or ("completed" if proc and proc.returncode == 0 and
                result_path.exists() else "failed"), "command": command,
               "requested_environment": ENV, "source_sha256": sha(folder / "executed-source.py"),
               "helpers_sha256": {filename: sha(folder / filename) for filename in HELPERS},
               "child_affinity_before_resume": child_affinity,
               "process_wall_seconds": elapsed, "max_wall_seconds": MAX_WALL,
               "peak_process_tree_rss_bytes": peak_rss,
               "max_process_tree_rss_bytes": MAX_RSS,
               "peak_process_tree_threads": peak_threads,
               "exit_code": proc.returncode if proc else None,
               "result_sha256": sha(result_path) if result_path.exists() else None,
               "arrays_sha256": sha(arrays_path) if arrays_path.exists() else None,
               "fresh_120_second_ledger_consumed": elapsed,
               "remaining_of_120_seconds": 120.0-elapsed,
               "reserved_final_seconds": 60.0}
    save(folder / "receipt.json", receipt)
    print(json.dumps({key: receipt[key] for key in
                      ("status", "process_wall_seconds", "peak_process_tree_rss_bytes", "exit_code")}))
    if receipt["status"] != "completed":
        raise RuntimeError("common-density diagnostic failed; inspect retained receipt/result/logs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preflight", type=Path)
    parser.add_argument("--adjudicate-saved", type=Path)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    if args.adjudicate_saved:
        adjudicate_saved_run(args.adjudicate_saved)
    elif args.preflight:
        save(args.preflight, preflight())
    elif args.child and args.output_dir:
        child(args.output_dir)
    elif args.output_dir:
        supervise(args.output_dir)
    else:
        parser.error("provide --preflight or a fresh --output-dir")
