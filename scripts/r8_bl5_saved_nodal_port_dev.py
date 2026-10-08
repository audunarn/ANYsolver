"""Prospective saved-state C3D20 nodal-action audit at the V5 midspan cut.

Integrate B.T sigma over the original beam elements from the saved displacement.
This does not solve a model, repair the V6 stress resultants, or qualify BL5.
Numerical execution requires a distinct authorization after consumed V6.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys

import numba
import numpy as np
import psutil
from threadpoolctl import threadpool_info

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from scripts import r8_bl5_weak_continuum_reference as continuum
from scripts import r8_bl5_mz_work_matched_dev as mz


SAVED = ROOT / ".development/bl5-mz-common-beam-20261008"
CUT_X = .5


def _saved(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    return json.loads(raw), hashlib.sha256(raw).hexdigest()


def _strain_matrix(gradient: np.ndarray) -> np.ndarray:
    matrix = np.zeros((6, 60))
    for node, (gx, gy, gz) in enumerate(gradient):
        matrix[:, 3 * node:3 * node + 3] = (
            (gx, 0., 0.), (0., gy, 0.), (0., 0., gz),
            (gy, gx, 0.), (0., gz, gy), (gz, 0., gx))
    return matrix


def _wrench(nodes: tuple[int, ...], index: dict[int, int],
            coordinates: dict, action: np.ndarray,
            center: np.ndarray) -> np.ndarray:
    result = np.zeros(6)
    for node in nodes:
        force = action[index[node]:index[node] + 3]
        result[:3] += force
        result[3:] += np.cross(np.asarray(coordinates[node]) - center, force)
    return result


def evaluate() -> dict:
    affinity = psutil.Process().cpu_affinity()
    pools = threadpool_info()
    if (affinity != [0] or numba.config.DISABLE_JIT != 1 or
            numba.get_num_threads() != 1 or not pools or
            any(pool["num_threads"] != 1 for pool in pools)):
        raise ValueError("Effective CPU/thread/JIT settings differ")

    preflight, preflight_sha = _saved(SAVED / "case-v5/preflight.json")
    resolved, resolved_sha = _saved(SAVED / "case-v5/reference-beam-solved.json")
    face, face_sha = _saved(SAVED / "case-v6-sided-face/result.json")
    model = continuum.specimen()
    if (model["model_sha256"] != preflight["model_sha256"] or
            resolved["status"] != "DEVELOPMENT_BODY_SOLVED_NOT_ACCEPTED" or
            face["identity"] != "BL5_V5_SAVED_SIDED_C3D20_FACE_WORK_DEV_V1" or
            face["source_sha256"]["resolved"] != resolved_sha or
            face["source_sha256"]["preflight"] != preflight_sha or
            face["cut_x_m"] != CUT_X):
        raise ValueError("Saved model, solved state, or V6 binding changed")
    for name, module in (("continuum", continuum), ("mz", mz)):
        if hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest() != (
                preflight["source_sha256"][name]):
            raise ValueError("V5 source binding changed: " + name)

    nodes = tuple(model["beam_nodes"])
    coordinates = model["physical_nodes"]
    index = {node: 3 * i for i, node in enumerate(nodes)}
    q = np.asarray(resolved["physical_coordinates"], dtype=float)
    load = np.asarray(resolved["full_physical_load_covector"], dtype=float)
    gauge = np.asarray(resolved["gauge_covector"], dtype=float)
    saved_residual = np.asarray(resolved["full_unscaled_residual"], dtype=float)
    if any(v.shape != (3 * len(nodes),) or not np.isfinite(v).all()
           for v in (q, load, gauge, saved_residual)):
        raise ValueError("Saved beam coordinate or covector layout changed")
    if resolved["support_covector"]:
        raise ValueError("This bounded beam-only audit expects a free body gauge")

    # V5's beam load is a physical end traction plus the four P0 weak
    # interface-edge actions. Edges 0,1 lie left of the cut; 2,3 lie right.
    # This splits shared cut-node loading by its source integration interval,
    # not by an arbitrary half-share of an already assembled nodal vector.
    density = np.asarray(preflight["projected_common_density_channel_major"],
                         dtype=float)
    if density.shape != (5, 4) or not np.isfinite(density).all():
        raise ValueError("V5 projected five-channel density layout changed")
    c, _ = continuum.constraints(model, "weak")
    order, global_index, _, _, _ = continuum.layout(model)
    beam_slots = np.asarray([global_index[node] + axis for node in nodes
                             for axis in range(3)], dtype=int)
    if c.shape != (20, 3 * len(order)):
        raise ValueError("V5 weak operator layout changed")
    left_density = density.copy()
    left_density[:, 2:] = 0.
    right_density = density.copy()
    right_density[:, :2] = 0.
    left_interface = np.asarray(-c.T @ left_density.reshape(-1))[beam_slots]
    right_interface = np.asarray(-c.T @ right_density.reshape(-1))[beam_slots]
    end_traction, _, _, _ = mz.end_traction(model)
    end_traction = end_traction[beam_slots]
    reconstructed_load = left_interface + right_interface + end_traction
    reconstruction_delta = float(np.max(np.abs(reconstructed_load - load)))
    if (reconstruction_delta / max(float(np.max(np.abs(load))), 1.) > 1e-11 or
            not np.isfinite(reconstruction_delta)):
        raise ValueError("V5 physical load does not reconstruct from bound sources")
    tip_nodes = {node for node in nodes
                 if abs(coordinates[node][0] - 1.) <= 1e-14}
    if (not tip_nodes or any(np.max(np.abs(end_traction[index[node]:index[node] + 3]))
                             > 1e-9 for node in nodes if node not in tip_nodes)):
        raise ValueError("Saved physical load has an unexpected non-tip source")
    physical_side_load = dict(left=left_interface,
                              right=right_interface + end_traction)

    section = np.asarray([coordinates[node] for node in nodes], dtype=float)
    center = np.array((CUT_X,
                       .5 * (section[:, 1].min() + section[:, 1].max()),
                       .5 * (section[:, 2].min() + section[:, 2].max())))
    if not np.allclose(center, face["center_m"], rtol=0., atol=1e-14):
        raise ValueError("V6 section center changed")
    cut_nodes = tuple(node for node in nodes
                      if abs(coordinates[node][0] - CUT_X) <= 1e-14)
    if not cut_nodes:
        raise ValueError("No native midspan cut nodes")
    cut_slots = np.asarray([index[node] + axis for node in cut_nodes
                            for axis in range(3)], dtype=int)
    internal = np.zeros_like(q)
    sided = {name: np.zeros_like(q) for name in ("left", "right")}
    side_ids = {name: [] for name in sided}
    element_rigid_wrench = {}
    material = continuum.original._elastic_matrix()
    gauss, weights = np.polynomial.legendre.leggauss(3)
    for element in model["beam_elements"]:
        ids, low, high, _, _ = continuum.original._brick(
            model["elements"][element], coordinates)
        if high[0] <= CUT_X + 1e-14:
            side = "left"
        elif low[0] >= CUT_X - 1e-14:
            side = "right"
        else:
            raise ValueError("Beam element crosses the prescribed material cut")
        xyz = np.asarray([coordinates[node] for node in ids], dtype=float)
        local_q = np.concatenate([q[index[node]:index[node] + 3] for node in ids])
        local_internal = np.zeros(60)
        for ix, iy, iz in itertools.product(range(3), repeat=3):
            _, natural_gradient = continuum.original._shape(
                (gauss[ix], gauss[iy], gauss[iz]))
            jacobian = xyz.T @ natural_gradient
            determinant = float(np.linalg.det(jacobian))
            if determinant <= 0. or not np.isfinite(determinant):
                raise ValueError("Nonpositive C3D20 volume Jacobian")
            gradient = np.linalg.solve(jacobian.T, natural_gradient.T).T
            b = _strain_matrix(gradient)
            local_internal += (b.T @ (material @ (b @ local_q)) * determinant
                               * weights[ix] * weights[iy] * weights[iz])
        local_wrench = np.zeros(6)
        for j, node in enumerate(ids):
            force = local_internal[3 * j:3 * j + 3]
            slot = index[node]
            internal[slot:slot + 3] += force
            sided[side][slot:slot + 3] += force
            local_wrench[:3] += force
            local_wrench[3:] += np.cross(xyz[j] - center, force)
        side_ids[side].append(element)
        element_rigid_wrench[str(element)] = local_wrench.tolist()

    if (len(side_ids["left"]) != 2 or len(side_ids["right"]) != 2 or
            any(not np.isfinite(v).all() for v in (internal, *sided.values()))):
        raise ValueError("Expected four finite resolved beam elements, two per side")
    # The saved K/q/load residual uses the same physical displacement and
    # constitutive operator, but a different floating-point summation order.
    assembled_residual = internal - load
    source_at_cut = load[cut_slots] - gauge[cut_slots]
    sided_cut_sum = sided["left"][cut_slots] + sided["right"][cut_slots]
    local_cut_equilibrium = sided_cut_sum - source_at_cut
    sides = {}
    for name in ("left", "right"):
        action = sided[name]
        physical_load = physical_side_load[name]
        port = action - physical_load
        cut_only = np.zeros_like(q)
        cut_only[cut_slots] = port[cut_slots]
        noncut_port = port - cut_only
        sides[name] = dict(
            element_ids=sorted(side_ids[name]),
            all_node_wrench_N_Nm=_wrench(nodes, index, coordinates,
                                         action, center).tolist(),
            physical_load_wrench_N_Nm=_wrench(nodes, index, coordinates,
                                               physical_load, center).tolist(),
            cut_port_wrench_N_Nm=_wrench(cut_nodes, index, coordinates,
                                         cut_only, center).tolist(),
            noncut_port_wrench_N_Nm=_wrench(nodes, index, coordinates,
                                            noncut_port, center).tolist(),
            cut_port_nodal_action_N={
                str(node): port[index[node]:index[node] + 3].tolist()
                for node in cut_nodes},
            noncut_port_max_N=float(np.max(np.abs(noncut_port))),
            internal_pairing_J=float(q @ action),
            physical_load_pairing_J=float(q @ physical_load),
            port_pairing_J=float(q @ port),
            cut_port_pairing_J=float(q @ cut_only),
            noncut_port_pairing_J=float(q @ noncut_port))

    return dict(
        identity="BL5_V7_SAVED_C3D20_NODAL_PORT_DEV_V1",
        status="DEVELOPMENT_SAVED_STATE_ONLY_NOT_QUALIFIED",
        runtime=dict(cpu_affinity=affinity,
                     numba_disable_jit=int(numba.config.DISABLE_JIT),
                     numba_threads=int(numba.get_num_threads()),
                     loaded_threadpools=pools),
        source_sha256=dict(preflight=preflight_sha, resolved=resolved_sha,
                           v6_face=face_sha),
        cut_x_m=CUT_X, center_m=center.tolist(),
        cut_node_ids=list(cut_nodes), sides=sides,
        element_rigid_wrenches_N_Nm=element_rigid_wrench,
        volume_internal_pairing_J=float(q @ internal),
        saved_internal_pairing_J=float(resolved["internal_pairing_J"]),
        saved_residual_reconstruction_max_N=float(np.max(
            np.abs(assembled_residual - saved_residual))),
        saved_equilibrium_max_N=float(np.max(np.abs(assembled_residual + gauge))),
        cut_equilibrium_max_N=float(np.max(np.abs(local_cut_equilibrium))),
        gauge_max_N=float(np.max(np.abs(gauge))),
        physical_load_reconstruction_max_N=reconstruction_delta,
        physical_end_traction_wrench_N_Nm=_wrench(
            nodes, index, coordinates, end_traction, center).tolist(),
        left_right_cut_port_wrench_sum_N_Nm=(
            np.asarray(sides["left"]["cut_port_wrench_N_Nm"]) +
            np.asarray(sides["right"]["cut_port_wrench_N_Nm"])).tolist(),
        cut_external_minus_gauge_wrench_N_Nm=_wrench(
            cut_nodes, index, coordinates, load - gauge, center).tolist(),
        cut_gauge_wrench_N_Nm=_wrench(
            cut_nodes, index, coordinates, gauge, center).tolist(),
        raw_v6_face_force_sum_N=face["force_sum_N"],
        raw_v6_face_moment_sum_Nm=face["moment_sum_Nm"],
        solver_executions=0,
        interpretation=(
            "Finite-element volume internal nodal actions are work-conjugate "
            "to the saved nodal displacement field. The physical P0 interface "
            "load is split by its original edge integration interval; the end "
            "traction belongs to the right side. The small global gauge "
            "covector remains separately reported, not silently partitioned. "
            "Each cut port is internal minus that side's physical load. A "
            "section wrench is only its rigid-trace projection. This diagnostic "
            "does not establish a finite-state native B3 port law, BL5 "
            "accuracy, external agreement, or formal F03 acceptance."))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Output exists; preserve the earlier attempt")
    result = evaluate()
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n",
                           encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "saved_residual_reconstruction_max_N", "saved_equilibrium_max_N",
        "cut_equilibrium_max_N", "volume_internal_pairing_J")}))


if __name__ == "__main__":
    main()
