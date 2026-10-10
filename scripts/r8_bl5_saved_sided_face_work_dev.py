"""Prospective two-sided C3D20 cut-face action from the saved V5 solution.

This reconstructs stresses from the already-solved conforming solid beam. It
does not solve another model, impose a seam law, or accept a BL5 formulation.
Numerical execution requires a separate development authority after V5.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys

import numpy as np
import numba
import psutil
from threadpoolctl import threadpool_info

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from scripts import r8_bl5_weak_continuum_reference as continuum


SAVED = ROOT / ".development/bl5-mz-common-beam-20261008/case-v5"
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


def evaluate() -> dict:
    affinity = psutil.Process().cpu_affinity()
    pools = threadpool_info()
    if (affinity != [0] or numba.config.DISABLE_JIT != 1 or
            numba.get_num_threads() != 1 or not pools or
            any(pool["num_threads"] != 1 for pool in pools)):
        raise ValueError("Effective CPU/thread/JIT settings differ")
    preflight, preflight_sha = _saved(SAVED / "preflight.json")
    resolved, resolved_sha = _saved(SAVED / "reference-beam-solved.json")
    native, native_sha = _saved(SAVED / "beam-solved.json")
    seam, seam_sha = _saved(SAVED.parent / "v5-native-seam-work-postprocess-v1.json")
    model = continuum.specimen()
    if (model["model_sha256"] != preflight["model_sha256"]
            or resolved["status"] != "DEVELOPMENT_BODY_SOLVED_NOT_ACCEPTED"
            or native["status"] != "DEVELOPMENT_BODY_SOLVED_NOT_ACCEPTED"
            or seam["identity"] != "BL5_V5_SAVED_NATIVE_SEAM_WORK_POSTPROCESS_V1"):
        raise ValueError("Saved V5 identity or solved-body status changed")

    q = np.asarray(resolved["physical_coordinates"], dtype=float)
    beam_nodes = tuple(model["beam_nodes"])
    if q.shape != (3 * len(beam_nodes),) or not np.isfinite(q).all():
        raise ValueError("Expected finite saved beam-only C3D20 coordinates")
    index = {node: 3 * i for i, node in enumerate(beam_nodes)}
    coordinates = model["physical_nodes"]
    section = np.asarray([coordinates[node] for node in beam_nodes], dtype=float)
    center = np.array((CUT_X,
                       .5 * (section[:, 1].min() + section[:, 1].max()),
                       .5 * (section[:, 2].min() + section[:, 2].max())))
    material = continuum.original._elastic_matrix()
    gauss, weights = np.polynomial.legendre.leggauss(3)
    sides = {name: dict(force=np.zeros(3), moment=np.zeros(3),
                        area=0., elements=[]) for name in ("left", "right")}

    for element in model["beam_elements"]:
        ids, low, high, _, _ = continuum.original._brick(
            model["elements"][element], coordinates)
        if abs(high[0] - CUT_X) <= 1e-14:
            side, xi, normal = "left", 1., 1.
        elif abs(low[0] - CUT_X) <= 1e-14:
            side, xi, normal = "right", -1., -1.
        else:
            continue
        xyz = np.asarray([coordinates[node] for node in ids], dtype=float)
        u = np.concatenate([q[index[node]:index[node] + 3] for node in ids])
        record = sides[side]
        record["elements"].append(element)
        for iy, iz in itertools.product(range(3), repeat=2):
            shape, natural_gradient = continuum.original._shape(
                (xi, gauss[iy], gauss[iz]))
            jacobian = xyz.T @ natural_gradient
            if np.linalg.det(jacobian) <= 0.:
                raise ValueError("Nonpositive C3D20 Jacobian on cut face")
            gradient = np.linalg.solve(jacobian.T, natural_gradient.T).T
            stress = material @ (_strain_matrix(gradient) @ u)
            traction = normal * np.array((stress[0], stress[3], stress[5]))
            area = float(np.linalg.norm(np.cross(jacobian[:, 1], jacobian[:, 2]))
                         * weights[iy] * weights[iz])
            point = shape @ xyz
            if abs(point[0] - CUT_X) > 1e-12 or not np.isfinite(stress).all():
                raise ValueError("Cut-point geometry or stress changed")
            record["area"] += area
            record["force"] += traction * area
            record["moment"] += np.cross(point - center, traction) * area

    area_expected = .04 * .06
    for side in sides.values():
        if len(side["elements"]) != 2 or abs(side["area"] - area_expected) > 1e-12:
            raise ValueError("Expected two complete rectangular beam faces per side")
        side["elements"] = sorted(side["elements"])
        side["force"] = side["force"].tolist()
        side["moment"] = side["moment"].tolist()

    # These are test variations, not a lift of the solid's solved displacement.
    # The beam nodal position is shared; retained spins are independent.
    native_q = np.asarray(native["physical_coordinates"], dtype=float)
    if native_q.shape != (78,):
        raise ValueError("Unexpected native retained-coordinate layout")
    translation = native_q[12:15]
    shared_spin = native_q[15:18]
    left_spin = native_q[33:36]
    right_spin = native_q[54:57]
    left_force, right_force = (np.asarray(sides[name]["force"]) for name in ("left", "right"))
    left_moment, right_moment = (np.asarray(sides[name]["moment"]) for name in ("left", "right"))
    force_sum = left_force + right_force
    moment_sum = left_moment + right_moment
    split_work = float(force_sum @ translation + left_moment @ left_spin
                       + right_moment @ right_spin)
    common_work = float(force_sum @ translation + moment_sum @ shared_spin)
    native_station = next(row for row in seam["stations"] if row["x_m"] == CUT_X)
    if not all(math.isfinite(value) for value in (*force_sum, *moment_sum, split_work, common_work)):
        raise ValueError("Nonfinite sided action or work")
    return dict(identity="BL5_V5_SAVED_SIDED_C3D20_FACE_WORK_DEV_V1",
                runtime=dict(cpu_affinity=affinity,
                             numba_disable_jit=int(numba.config.DISABLE_JIT),
                             numba_threads=int(numba.get_num_threads()),
                             loaded_threadpools=pools),
                source_sha256=dict(preflight=preflight_sha, resolved=resolved_sha,
                                   native=native_sha, native_seam=seam_sha),
                cut_x_m=CUT_X, center_m=center.tolist(), sides=sides,
                force_sum_N=force_sum.tolist(), moment_sum_Nm=moment_sum.tolist(),
                shared_translation_m=translation.tolist(),
                shared_nodal_spin_rad=shared_spin.tolist(),
                left_cell_spin_rad=left_spin.tolist(),
                right_cell_spin_rad=right_spin.tolist(),
                split_virtual_work_J=split_work,
                common_virtual_work_J=common_work,
                broken_trace_virtual_work_J=split_work - common_work,
                native_reference_linearized_station_work_J=(
                    native_station["balanced_first_variation_work_J"]),
                solver_executions=0,
                interpretation=("Element-side C3D20 stress resultants act on "
                                "separate virtual section rotations at one cut. "
                                "Outward cut-face work uses the opposite action "
                                "sign from the native endpoint-log convention; "
                                "compare magnitudes or reconcile signs explicitly. "
                                "This is a saved-solution diagnostic, not a "
                                "split-solid equilibrium solve, seam constitutive "
                                "law, matched compliance, or BL5 acceptance."))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Output exists; preserve the earlier attempt")
    result = evaluate()
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "cut_x_m", "broken_trace_virtual_work_J", "native_reference_linearized_station_work_J",
        "force_sum_N", "moment_sum_Nm")}))


if __name__ == "__main__":
    main()
