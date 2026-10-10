"""Saved-state BL5 common P0 density admission and physical-port work screen.

Development evidence only.  In particular, this script never builds an external
stiffness, invokes OpenSees, or solves a fixed-density response.  The required
external operator must be an independently bound saved input to do that.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PureWindowsPath
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/agent_plans/development/r8-bl5-matched-comparison-20261001/refinement-v1-raw"
DEFAULT_OUTPUT = ROOT / ".development/bl5-common-density-transfer-20261009-v1"
LEVELS = (16, 32, 64)
CASES = ("fy", "mx", "mz")
NATIVE_MEMBERS = {"K_data.npy", "K_indices.npy", "K_indptr.npy", "K_shape.npy",
                  "C_data.npy", "C_indices.npy", "C_indptr.npy", "C_shape.npy",
                  "fixed.npy", "free.npy", "beam_rigid_work_map.npy",
                  "shell_rigid_work_map.npy"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def map_external_to_native(mu, supports: int):
    """External support-major (t,x,y,dx,dy) to native channel-major.

    The physical work map applies only to the admitted straight virgin frames.
    Coefficients are densities; no support-width or row-scale factor is applied.
    """
    if len(mu) != 5 * supports:
        raise ValueError("five external density coefficients per support required")
    mapped = [0.0] * (5 * supports)
    for j in range(supports):
        mapped[j] = -mu[5*j]
        mapped[supports+j] = -mu[5*j+1]
        mapped[2*supports+j] = -mu[5*j+2]
        mapped[3*supports+j] = -mu[5*j+4]
        mapped[4*supports+j] = mu[5*j+3]
    return mapped


def map_native_to_external(lam, supports: int):
    if len(lam) != 5 * supports:
        raise ValueError("five native density coefficients per support required")
    mu = [0.0] * (5 * supports)
    for j in range(supports):
        mu[5*j:5*j+5] = [-lam[j], -lam[supports+j], -lam[2*supports+j],
                         lam[4*supports+j], -lam[3*supports+j]]
    return mu


def inventory():
    """Check bounded frozen inputs before any numerical calculation."""
    bound, missing, records = {}, [], []
    source_hashes = {}
    for side in ("native", "external"):
        for path in sorted((DATA / side).glob("*.py")):
            source_hashes[str(path.relative_to(ROOT))] = sha256(path)
    for nx in LEVELS:
        nr = DATA / "native" / f"n{nx}"
        er = DATA / "external" / f"n{nx}"
        npaths = [nr / name for name in ("operators.npz", "layout.json", "inputs.json",
                                         "station-traces.json", "identity.json", "imports.json")]
        for path in npaths:
            if not path.is_file():
                missing.append(str(path.relative_to(ROOT)))
            else:
                bound[str(path.relative_to(ROOT))] = sha256(path)
        if npaths[0].is_file():
            with zipfile.ZipFile(npaths[0]) as archive:
                absent = sorted(NATIVE_MEMBERS - set(archive.namelist()))
            missing.extend(f"{npaths[0].relative_to(ROOT)}::{name}" for name in absent)
        if (nr / "inputs.json").is_file():
            declared = read(nr / "inputs.json").get("helper_sources", {})
            for original, expected in declared.items():
                frozen = DATA / "native" / PureWindowsPath(original).name
                if not frozen.is_file() or sha256(frozen) != expected:
                    missing.append(f"native n{nx}: frozen helper hash {frozen.name}")
        for case in CASES:
            nc, ec = nr / case, er / case
            paths = [nc / "raw-state.npz", nc / "raw-state.json",
                     ec / "inputs.json", ec / "raw-inventory.json",
                     ec / "recovered-actions.json", ec / "summary.json"]
            for path in paths:
                if not path.is_file():
                    missing.append(str(path.relative_to(ROOT)))
                else:
                    bound[str(path.relative_to(ROOT))] = sha256(path)
            if (ec / "summary.json").is_file():
                declared = read(ec / "summary.json").get("helper_sources", {})
                for original, expected in declared.items():
                    frozen = DATA / "external" / PureWindowsPath(original).name
                    if not frozen.is_file() or sha256(frozen) != expected:
                        missing.append(f"external n{nx}/{case}: frozen helper hash {frozen.name}")
            # No frozen external K archive is present in this family.  A single
            # converged q and element force inventory cannot identify its tangent.
            possible = [ec / "operators.npz", er / "operators.npz"]
            external_k = next((p for p in possible if p.is_file()), None)
            if external_k is None:
                missing.append(f"external n{nx}/{case}: exact K_E (complete free/free "
                               "shell+beam stiffness with fixed/free coupling), "
                               "plus its DOF order and source/binary identity")
            else:
                bound[str(external_k.relative_to(ROOT))] = sha256(external_k)
            records.append({"nx": nx, "case": case,
                            "native_operator_saved": npaths[0].is_file(),
                            "external_operator_saved": external_k is not None})
    return {"cases": records, "bound_sha256": bound,
            "frozen_source_sha256": source_hashes, "missing": missing,
            "fixed_density_response_admitted": not missing}


def _csr(archive, name):
    import scipy.sparse as sparse

    return sparse.csr_matrix((archive[name + "_data"], archive[name + "_indices"],
                              archive[name + "_indptr"]),
                             shape=tuple(archive[name + "_shape"]))


def _admit_native_stations(stations, endpoints, supports):
    """Bind the frozen c2 P0 quadrature to each physical support interval."""
    if len(endpoints) != supports + 1 or len(stations) != 8 * supports:
        raise ValueError("complete four-halfcell/two-point support quadrature required")
    if sorted(station["sample_index"] for station in stations) != list(range(len(stations))):
        raise ValueError("native station sample identity is missing or duplicated")
    grouped = [[] for _ in range(supports)]
    for station in stations:
        rows = station["multiplier_rows"]
        if len(rows) != 5 or not 0 <= rows[0] < supports or rows != [c*supports + rows[0] for c in range(5)]:
            raise ValueError("native P0 station row/support identity changed")
        support = rows[0]
        lo, hi = endpoints[support:support+2]
        if not math.isfinite(lo) or not math.isfinite(hi) or hi <= lo:
            raise ValueError("finite positive support interval required")
        x0, x1 = (point[0] for point in station["shell_reference_m"])
        alpha = station["shell_alpha"]
        measure = station["measure_m"]
        if not all(math.isfinite(value) for value in (x0, x1, alpha, measure)) or not (0 <= alpha <= 1) or measure <= 0:
            raise ValueError("finite native station location and measure required")
        tolerance = max(1e-14, 128*math.ulp(1.)*max(1., abs(lo), abs(hi)))
        x = (1-alpha)*x0 + alpha*x1
        if x0 < lo-tolerance or x1 > hi+tolerance or x1 <= x0 or x < lo-tolerance or x > hi+tolerance:
            raise ValueError("native station lies outside its declared P0 support")
        grouped[support].append((x, measure))
    for support, group in enumerate(grouped):
        if len(group) != 8:
            raise ValueError("native P0 support has missing or extra stations")
        positions = sorted(x for x, _ in group)
        if any(right-left <= 1e-12 for left, right in zip(positions, positions[1:])):
            raise ValueError("native P0 support has duplicate station locations")
        width = endpoints[support+1] - endpoints[support]
        if not math.isclose(math.fsum(measure for _, measure in group), width,
                            rel_tol=1e-12, abs_tol=1e-14):
            raise ValueError("native station measures do not integrate the support width")


def _native_independent_action(stations, lam, q_size):
    """Integrate the physical virgin BL5 port on all active slots.

    Slots are [shell endpoint 6+6, beam endpoint translations 3+3,
    retained cell rotation 3].  The actual compiled C is checked separately.
    """
    import numpy as np

    out = np.zeros(q_size)
    supports = len(lam) // 5
    for station in stations:
        rows = station["multiplier_rows"]
        if rows != [c*supports + rows[0] for c in range(5)]:
            raise ValueError("native channel-major station row order changed")
        if not np.array_equal(station["density_basis"], np.eye(5)):
            raise ValueError("native constant P0 density basis required")
        if (station["reference_arm_m"] != [0.0, 0.0, -0.05]
                or station["reference_director"] != [0.0, 0.0, 1.0]
                or station["director_basis"] != [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
                or not np.array_equal(station["beam_port"]["frame"], np.eye(3))
                or station["beam_port"]["lift_m"] != [0.0, 0.0, 0.0]):
            raise ValueError("straight virgin physical frame/arm contract required")
        t = np.asarray([lam[row] for row in rows[:3]])
        dx, dy = lam[rows[3]], lam[rows[4]]
        alpha = station["shell_alpha"]
        beta = station["beam_port"]["weight"]
        h = station["thickness_m"] / 2
        shell = np.r_[t, [-h*t[1]-dy, h*t[0]+dx, 0.0]]
        beam_t = -t
        beam_r = np.asarray([-0.05*t[1]+dy, 0.05*t[0]-dx, 0.0])
        slots = station["full_slots"]
        weight = station["measure_m"]
        if len(slots) != 21 or weight <= 0:
            raise ValueError("complete positive native station measure required")
        for k, factor in ((0, 1-alpha), (6, alpha)):
            out[slots[k:k+6]] += weight*factor*shell
        for k, factor in ((12, 1-beta), (15, beta)):
            out[slots[k:k+3]] += weight*factor*beam_t
        out[slots[18:21]] += weight*beam_r
    return out


def _external_independent_action(inputs, mu, nodes):
    """Assemble the saved integrated P0 rows, retaining fixed-root covectors."""
    import numpy as np

    order = list(nodes)
    lookup = {str(node): i for i, node in enumerate(order)}
    action = np.zeros((len(order), 6))
    if len(inputs["rows"]) != len(mu):
        raise ValueError("external support-major row count mismatch")
    for i, entries in enumerate(inputs["rows"]):
        if len(entries) % 3:
            raise ValueError("external row triplets required")
        for k in range(0, len(entries), 3):
            node, dof, coefficient = entries[k:k+3]
            action[lookup[str(node)], int(dof)-1] += float(coefficient)*mu[i]
    return {str(node): action[i] for i, node in enumerate(order)}


def _native_beam_yaw(layout, state, size):
    """Whole retained rigid yaw: nodal translations and both cell rotations."""
    import numpy as np

    yaw = np.zeros(size)
    shell_count = len(layout["shell_node_ids"])
    beam_xyz = state["beam_xyz_m"]
    if len(beam_xyz) != len(layout["beam_node_ids"]):
        raise ValueError("complete typed beam-node coordinates required")
    root = beam_xyz[0]
    for j, xyz in enumerate(beam_xyz):
        slot = 6 * (shell_count + j)
        yaw[slot:slot+3] = [-(xyz[1]-root[1]), xyz[0]-root[0], 0.0]
        yaw[slot+5] = 1.0
    retained = layout["counts"]["physical_dofs"]
    for member in range(layout["counts"]["members"]):
        yaw[retained+24*member+2] = 1.0
        yaw[retained+24*member+5] = 1.0
    return yaw


def _external_beam_yaw(inputs, raw, applied, port_action):
    import numpy as np

    beam = inputs["model"]["beam_node_ids"]
    root = np.asarray(raw["nodes"][str(beam[0])])
    load_work = action_work = 0.0
    for node in beam:
        key = str(node)
        xyz = np.asarray(raw["nodes"][key])
        yaw = np.asarray([-(xyz[1]-root[1]), xyz[0]-root[0], 0., 0., 0., 1.])
        load_work += float(yaw @ np.asarray(applied[key]))
        action_work += float(yaw @ port_action[key])
    return {"applied_virtual_work": load_work,
            "port_virtual_work": action_work,
            "rhs_virtual_work": load_work-action_work}


def _external_domain_wrench(inputs, raw, port_action, domain):
    import numpy as np

    origin = np.asarray(inputs["model"]["moment_origin_m"])
    force = np.zeros(3)
    moment = np.zeros(3)
    for node in inputs["model"][domain + "_node_ids"]:
        key = str(node)
        action = port_action[key]
        force += action[:3]
        moment += action[3:] + np.cross(np.asarray(raw["nodes"][key])-origin,
                                        action[:3])
    return np.r_[force, moment]


def work_screen(nx: int, case: str):
    """Two common density probes; full transposes only, no response solve."""
    import numpy as np

    nr = DATA / "native" / f"n{nx}"
    nc = nr / case
    ec = DATA / "external" / f"n{nx}" / case
    inputs, actions = read(ec / "inputs.json"), read(ec / "recovered-actions.json")
    stations = read(nr / "station-traces.json")
    raw = read(ec / "raw-inventory.json")
    native_inputs = read(nr / "inputs.json")
    external_summary = read(ec / "summary.json")
    layout = read(nr / "layout.json")
    constants = native_inputs["reference_constants"]
    if (inputs["load"] != native_inputs["loads"][case]
            or external_summary["case"] != case
            or inputs["model"]["nx"] != nx
            or inputs["arms_m"] != {"beam_normal": -0.05, "shell_top": 0.0175}
            or constants["BEAM_BOTTOM_ARM_M"] != -0.05
            or constants["SHELL_THICKNESS_M"] != 0.035
            or constants["BEAM_AXIS_Z_M"] != 0.0675
            or "density N/m,Nm/m" not in actions["units"]):
        raise ValueError("matched physical idealization, load and density units required")
    supports = nx // 2
    if len(inputs["supports"]) != supports or len(actions["support_records"]) != supports:
        raise ValueError("matching support count required")
    endpoints = native_inputs["policy"]["support_endpoints_m"]
    _admit_native_stations(stations, endpoints, supports)
    for j, (support, record) in enumerate(zip(inputs["supports"], actions["support_records"])):
        if (support["support_id"] != j or record["support_id"] != j
                or support["row_indices"] != list(range(5*j, 5*j+5))
                or support["interval_m"] != endpoints[j:j+2]
                or record["interval_m"] != endpoints[j:j+2]
                or support["width_m"] != endpoints[j+1]-endpoints[j]):
            raise ValueError("external/native P0 support order or measure mismatch")
    with np.load(nr / "operators.npz", allow_pickle=False) as op, \
            np.load(nc / "raw-state.npz", allow_pickle=False) as state:
        C = _csr(op, "C")
        K = _csr(op, "K")
        q = state["q"]
        if C.shape != (5*supports, len(q)):
            raise ValueError("native full retained C dimensions mismatch")
        yaw = _native_beam_yaw(layout, state, len(q))
        if np.max(np.abs(yaw[op["fixed"]])) != 0:
            raise ValueError("rigid yaw must honor all fixed coordinates")
        yaw_kernel = K @ yaw
        probes = {"external_saved": actions["row_density_multipliers"],
                  "native_saved": map_native_to_external(state["multipliers"], supports)}
        result = {}
        for name, mu in probes.items():
            lam = np.asarray(map_external_to_native(mu, supports))
            native = C.T @ lam
            physical = _native_independent_action(stations, lam, len(q))
            external = _external_independent_action(inputs, mu, raw["nodes"])
            native_error = float(np.max(np.abs(native-physical)))
            # Saved per-support forces are independent of the row transpose for
            # the external-saved probe and explicitly contain both root nodes.
            external_error = None
            if name == "external_saved":
                independent = {key: np.zeros(6) for key in external}
                for support in actions["support_records"]:
                    for node, exerted in support["independent_exerted_loads"].items():
                        independent[node] += exerted
                external_error = max(float(np.max(np.abs(external[node]+independent[node])))
                                     for node in external)
            root = {"native_shell": physical[:6].tolist(),
                    "native_beam": physical[6*len(layout["shell_node_ids"]):][:6].tolist(),
                    "external_shell": external["1"].tolist(),
                    "external_beam": external["100001"].tolist()}
            wrench_error = {}
            for domain in ("shell", "beam"):
                native_wrench = op[domain + "_rigid_work_map"] @ native
                external_wrench = _external_domain_wrench(inputs, raw, external, domain)
                wrench_error[domain] = float(np.max(np.abs(native_wrench-external_wrench)))
            native_yaw_load = float(yaw @ state["load"])
            native_yaw_port = float(yaw @ native)
            result[name] = {"native_full_transpose_max_abs": native_error,
                            "external_support_action_max_abs": external_error,
                            "native_external_full_domain_wrench_max_abs": wrench_error,
                            "fixed_root_Ct_density": root,
                            "native_retained_rotation_nonzero": bool(np.any(physical[op["shell_rigid_work_map"].shape[1]-24*nx:])),
                            "beam_yaw": {
                                "native_full_retained_K_yaw_max_abs": float(np.max(np.abs(yaw_kernel))),
                                "native_applied_virtual_work": native_yaw_load,
                                "native_port_virtual_work": native_yaw_port,
                                "native_rhs_virtual_work": native_yaw_load-native_yaw_port,
                                "external": _external_beam_yaw(
                                    inputs, raw, actions["applied_nodal_L"], external),
                                "common_gauge": "not applied: exact external K/kernel unavailable; "
                                                "full retained load compatibility reported"},
                            "density_sha256": hashlib.sha256(np.asarray(mu, dtype="<f8").tobytes()).hexdigest()}
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--inventory-only", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"preserve prior evidence: {args.output}")
    report = {"classification": "development saved-state port-work discriminator",
              "source_sha256": sha256(Path(__file__)), "inventory": inventory(),
              "response_decision": "stop: exact external K_E not saved; no fixed-density response solve",
              "work_checks": {}, "failed_work_checks": {},
              "limits": "No continuum truth, F03 acceptance, or law/space selection"}
    if not args.inventory_only:
        import psutil

        process = psutil.Process()
        process.cpu_affinity([0])
        controls = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                    "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS")
        effective = {name: os.environ.get(name) for name in controls}
        effective["NUMBA_DISABLE_JIT"] = os.environ.get("NUMBA_DISABLE_JIT")
        if (list(process.cpu_affinity()) != [0]
                or any(effective[name] != "1" for name in controls)
                or effective["NUMBA_DISABLE_JIT"] != "1"):
            raise RuntimeError("CPU0, one-thread, JIT-off controls required")
        report["effective_runtime"] = {"affinity": process.cpu_affinity(),
                                       "environment": effective}
        for nx in LEVELS:
            for case in CASES:
                key = f"n{nx}/{case}"
                try:
                    report["work_checks"][key] = work_screen(nx, case)
                except Exception as exc:
                    report["failed_work_checks"][key] = f"{type(exc).__name__}: {exc}"
        from threadpoolctl import threadpool_info

        report["effective_runtime"]["threadpools"] = [
            {"internal_api": row.get("internal_api"), "num_threads": row.get("num_threads")}
            for row in threadpool_info()]
        if any(row["num_threads"] != 1 for row in report["effective_runtime"]["threadpools"]):
            report["failed_work_checks"]["runtime"] = "threadpool reported more than one thread"
    args.output.mkdir(parents=True)
    destination = args.output / "report.json"
    destination.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(destination), "cases": len(report["work_checks"]),
                      "failures": len(report["failed_work_checks"]),
                      "missing": len(report["inventory"]["missing"]),
                      "response_admitted": report["inventory"]["fixed_density_response_admitted"]}))
    if report["failed_work_checks"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
