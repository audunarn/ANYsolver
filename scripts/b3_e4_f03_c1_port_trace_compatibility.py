"""Bounded native-port versus saved-solid cut trace compatibility audit.

Only shared-node trace algebra and a declared equal-side projection are tested.
Broken side fields are not admissible intact bonded-solid variations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts.b3_e4_f03_c3d20r_bond_force_recovery import read_deck
from scripts.b3_e4_f03_c3d20r_stress_force_recovery import integrate, read_stress
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


ROOT = Path(".qualification/b3-ge-e4-pl/f03-c1-factor5-sided-port-cut-dev-20260926-v1")
AXIS = np.array((.95, 0., .0675))
LENGTH = .1


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _trace_matrix(points: np.ndarray) -> np.ndarray:
    radius = points - AXIS
    matrix = np.zeros((len(points), 3, 6))
    matrix[:, :, :3] = np.eye(3)
    for axis in range(3):
        matrix[:, :, 3 + axis] = np.cross(np.eye(3)[axis], radius) / LENGTH
    return matrix.reshape(3 * len(points), 6)


def evaluate() -> dict:
    stem = ROOT / "solid-5-sided-port"
    inp, dat = stem.with_suffix(".inp"), stem.with_suffix(".dat")
    model_path, run_path = ROOT / "model.json", ROOT / "run_result.json"
    model, run = json.loads(model_path.read_text()), json.loads(run_path.read_text())
    if (model.get("sided_port_cut_at_095_m") is not True or
            run["status"] != "EXECUTED_OUTPUT_PENDING_MECHANICAL_VALIDATION"):
        raise ValueError("validated side-cut source required")
    x, elements = read_deck(inp)
    stress = read_stress(dat, first_element=len(elements["Plate"]) + 1,
                         element_count=len(elements["Stiffener"]))
    conn = elements["Stiffener"]
    ends = x[conn, 0]
    left = np.flatnonzero(np.max(ends, axis=1) <= AXIS[0] + 1e-12)
    right = np.flatnonzero(np.min(ends, axis=1) >= AXIS[0] - 1e-12)
    if len(left) + len(right) != len(conn):
        raise ArithmeticError("solid cells do not partition at native station")
    f_left, _ = integrate(x, conn[left], stress[left])
    f_right, _ = integrate(x, conn[right], stress[right])
    bar_nodes = np.unique(conn.ravel())
    cut = np.intersect1d(np.flatnonzero(np.isclose(x[:, 0], AXIS[0],
                                                  rtol=0, atol=1e-12)), bar_nodes)
    seam = np.asarray(model["shared_interface_node_ids"], dtype=int)
    shared = np.intersect1d(cut, seam)
    if len(cut) != 341 or len(shared) != 21:
        raise ArithmeticError("cut trace topology changed")
    q = _trace_matrix(x[cut])
    qs = _trace_matrix(x[shared])
    rank_full = int(np.linalg.matrix_rank(q, tol=1e-10))
    rank_seam = int(np.linalg.matrix_rank(qs, tol=1e-10))
    mismatch = np.column_stack((q, -q))
    if rank_full != 6 or np.linalg.matrix_rank(mismatch, tol=1e-10) != 6:
        raise ArithmeticError("independent rigid traces unexpectedly conform")
    native = build(12, z_offset=.0675,
                   torsion_constant=square_torsion_constant(),
                   reference_profile="c1_tangent_2um")
    if abs(native.abscissae[11] - .95) > 1e-12:
        raise ValueError("native retained-port station changed")
    context = native.context
    state = context.initial.mechanical
    ports = (NativeHalfCellSpatialPort(context, 5, 0, 1.),
             NativeHalfCellSpatialPort(context, 5, 1, 0.))
    left_column = context.nodal_count + 24 * 5
    right_column = left_column + 3
    left_tangent, right_tangent = (port.tangent(state) for port in ports)
    expected = np.r_[np.zeros(3), [1., 0., 0.]]
    if (np.max(np.abs(left_tangent[:, left_column] - expected)) > 1e-12 or
            np.max(np.abs(right_tangent[:, right_column] - expected)) > 1e-12 or
            np.max(np.abs(left_tangent[:, right_column])) > 1e-12 or
            np.max(np.abs(right_tangent[:, left_column])) > 1e-12):
        raise ArithmeticError("one-sided native half-cell tangent changed")
    xyz_left = sum(ports[0].pose_pair(state)[:2])
    xyz_right = sum(ports[1].pose_pair(state)[:2])
    if np.linalg.norm(xyz_left - xyz_right) > 1e-12:
        raise ArithmeticError("native centerline position is not shared at port")
    # Unit physical twist at x=.95 m. The symmetric left-only projection onto
    # one common solid trace is v=.5 U on both sides; this equal-side choice
    # is declared for diagnosis, not implied by the native formulation.
    twist = np.cross(np.array((1., 0., 0.)), x[cut] - AXIS)
    w_left = float(np.sum(f_left[cut] * twist))
    w_right = float(np.sum(f_right[cut] * twist))
    omitted_left_only = .5 * (w_left - w_right)
    jump_bar_only = w_left - w_right
    rms_jump = float(np.sqrt(np.mean(np.sum(twist**2, axis=1))))
    return {
        "classification": "bounded native endpoint and shared-solid trace compatibility, not connection qualification",
        "decision": "Can independent native retained half-cell twists be scored as exact admissible sided motions of the saved shared-node solid?",
        "native": {"half_cell_abscissa_m": float(native.abscissae[11]),
                   "left_port": [5, 0, 1.], "right_port": [5, 1, 0.],
                   "left_retained_rotation_column": left_column,
                   "right_retained_rotation_column": right_column,
                   "shared_centerline_position_difference_m": float(np.linalg.norm(xyz_left - xyz_right)),
                   "left_right_spatial_tangent_columns_independent": True},
        "solid": {"cut_nodes": len(cut), "bonded_cut_nodes": len(shared),
                  "normalized_rigid_trace_rank_full": rank_full,
                  "normalized_rigid_trace_rank_bonded_seam": rank_seam,
                  "left_minus_right_trace_rank": 6,
                  "compatible_subspace_dimension_of_twelve_rigid_port_coordinates": 6,
                  "rotation_normalization_length_m": LENGTH,
                  "unit_twist_cut_trace_rms_m_per_rad": rms_jump},
        "work": {"left_bar_broken_twist_Nm_per_rad": w_left,
                 "right_bar_broken_twist_Nm_per_rad": w_right,
                 "equal_side_projection_omitted_bar_work_Nm_per_rad": omitted_left_only,
                 "antisymmetric_jump_bar_only_work_Nm_per_rad": jump_bar_only},
        "conclusion": "Exact independent rigid-section port traces are incompatible on the intact shared solid cut. The chosen common projection has a material broken-bar complement, but its total physical work is unidentified without a side allocation of seam action and a specified conforming warping/transition extension. Stop direct sided-port accuracy scoring.",
        "limits": ["rank is exact finite-dimensional trace geometry with a declared coordinate scale, not a stability constant",
                   "the equal-side projection is arbitrary and its bar-only omitted work is not admissible total assembly work",
                   "the net seam-cut moment cannot bound unknown side-local seam work",
                   "conforming regional gradient fields are possible but depend on a separately defined extension"],
        "inputs_sha256": {str(path): sha(path) for path in (inp, dat, model_path, run_path)},
        "runner_sha256": sha(Path(__file__)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"full_rank": result["solid"]["normalized_rigid_trace_rank_full"],
                      "seam_rank": result["solid"]["normalized_rigid_trace_rank_bonded_seam"],
                      "compatible_dim": result["solid"]["compatible_subspace_dimension_of_twelve_rigid_port_coordinates"],
                      "omitted_bar_work": result["work"]["equal_side_projection_omitted_bar_work_Nm_per_rad"]}))


if __name__ == "__main__":
    main()
