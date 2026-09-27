"""Bounded loaded screen for channel-compatible material-line row growth.

The native reference local-z yaw (Mz) trace has two values on the aligned
two-cell grid. This diagnostic retains two P0 Mz rows while enriching the other five
channels with P1 or dual-P1. It is not a selected production space.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import anysolver
import numpy as np
import scipy
from scipy import sparse
from scipy.sparse.linalg import MatrixRankWarning

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts.b3_e4_f03_material_line_loaded import _scales, _solve
from scripts.b3_e4_f03_material_line_position import MaterialLinePosition
from scripts.b3_e4_f03_material_line_space_screen import (
    _rows, _scaled_row_diagnostics,
)
from scripts.b3_e4_f03_plate_patch_work import (
    local_grid, raw_e4_mixed_c1_tangent, raw_e4_tangent,
)
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def _channel_basis_rows(line: MaterialLinePosition,
                        kinds: tuple[str, ...],
                        knots: tuple[float, ...]) -> np.ndarray:
    """Group exact weak rows by their declared physical-channel basis."""
    if (len(kinds) != 6 or any(kind not in (
            "piecewise_constant", "continuous_linear", "dual_linear")
            for kind in kinds)):
        raise ValueError("six declared line-channel spaces required")
    cache = {}
    for kind in set(kinds):
        cache[kind], _ = _rows(line, LineMultiplierSpace(kind, knots))
    return np.vstack([cache[kind][axis::6]
                      for axis, kind in enumerate(kinds)]).copy()


def _channel_rows(line: MaterialLinePosition, kind: str,
                  knots: tuple[float, ...] = (0., .5, 1.)) -> np.ndarray:
    if kind == "p0":
        kinds = ("piecewise_constant",)*6
    elif kind in ("continuous_linear", "dual_linear"):
        kinds = (kind,)*5+("piecewise_constant",)
    else:
        raise ValueError("bounded candidate space required")
    return _channel_basis_rows(line, kinds, knots)


def _one_topology(xs, ys, beam, *, mixed_s3: bool,
                  diagonal: str,
                  knots: tuple[float, ...] = (0., .5, 1.),
                  extra_policies: tuple[tuple[str, tuple[str, ...]], ...] = (),
                  ) -> dict:
    shell_size = 6*len(xs)*len(ys)
    shell_tangent, shell_physical = (
        raw_e4_mixed_c1_tangent(xs, ys, thickness=.035,
                                diagonal=diagonal)
        if mixed_s3 else raw_e4_tangent(xs, ys, thickness=.035))
    if beam.tangent is None or beam.residual is None:
        raise ArithmeticError("native assembled fixture required")
    primal = sparse.block_diag((sparse.csr_matrix(shell_tangent),
                                beam.tangent), format="csr")
    residual = np.r_[np.zeros(shell_size), beam.residual]
    line = MaterialLinePosition(xs, ys, beam, mixed_s3=mixed_s3,
                                diagonal=diagonal)
    fixed_shell = {6*(j*len(xs)+i)+axis
                   for j in range(len(ys)) for i, x in enumerate(xs)
                   if abs(x+.5) < 1e-12 for axis in range(6)}
    fixed_beam = {shell_size+int(index) for index in beam.context.fixed}
    free = np.setdiff1d(
        np.arange(primal.shape[0]), np.array(sorted(fixed_shell|fixed_beam)))
    shell_reference = line.reference_nodes
    beam_reference = (beam.context.initial.mechanical.positions
                      + beam.context.initial.mechanical.position_low)
    station_position = line.reference_jacobian().reshape(len(line.stations), 3, -1)
    station_orientation = line.reference_orientation_jacobian().reshape(
        len(line.stations), 3, -1)
    weights = np.array([station.weight for station in line.stations])
    result = {}
    p0_label = "p0_two" if len(knots) == 3 else f"p0_{len(knots)-1}"
    policies = ((p0_label, "p0"),
                ("p1_non_yaw_p0_yaw", "continuous_linear"),
                ("dual_non_yaw_p0_yaw", "dual_linear")) + extra_policies
    for label, kind in policies:
        if isinstance(kind, tuple):
            channel_kinds = kind
            constraint = _channel_basis_rows(line, channel_kinds, knots)
        else:
            constraint = _channel_rows(line, kind, knots)
            channel_kinds = (("piecewise_constant",)*6 if kind == "p0" else
                             (kind,)*5+("piecewise_constant",))
        scales, energy_scale = _scales(
            shell_size, beam, free, row_count=len(constraint))
        rank = _scaled_row_diagnostics(
            constraint, free, scales[:len(free)])
        loads = {}
        for load_name, axis, magnitude in (("tip_mx_100nm", 3, 100.),
                                           ("tip_fz_1000n", 2, 1000.)):
            if rank["scaled_row_rank"] != len(constraint):
                loads[load_name] = {
                    "status": "FAILED_DEPENDENT_ROWS",
                    "reason": "scaled supported rows dependent; no solve accepted",
                }
                continue
            load = np.zeros(primal.shape[0])
            terminal = shell_size+6*beam.n_half_cells
            load[terminal+axis] = magnitude
            try:
                state, equation, diagnostics = _solve(
                    primal, residual, constraint, free, scales,
                    energy_scale, load)
            except (ArithmeticError, MatrixRankWarning) as error:
                loads[load_name] = {
                    "status": "FAILED_NUMERICAL",
                    "reason": str(error),
                }
                continue
            shell_support = equation[:shell_size].reshape(-1, 6)
            beam_support = equation[shell_size:shell_size+
                                    beam.context.nodal_count].reshape(-1, 6)
            support_force = (shell_support[:, :3].sum(axis=0)
                             +beam_support[:, :3].sum(axis=0))
            support_moment = (
                np.sum(np.cross(shell_reference, shell_support[:, :3])
                       + shell_support[:, 3:], axis=0)
                + np.sum(np.cross(beam_reference, beam_support[:, :3])
                         + beam_support[:, 3:], axis=0))
            applied_force = np.zeros(3)
            applied_moment = np.zeros(3)
            if axis < 3:
                applied_force[axis] = magnitude
                applied_moment = np.cross(beam_reference[-1], applied_force)
            else:
                applied_moment[axis-3] = magnitude
            position_gap = np.einsum("kij,j->ki", station_position, state)
            orientation_gap = np.einsum("kij,j->ki", station_orientation, state)
            diagnostics.update({
                "support_force_balance_n": float(np.linalg.norm(
                    support_force+applied_force)),
                "support_moment_balance_nm": float(np.linalg.norm(
                    support_moment+applied_moment)),
                "shell_physical_work_j": float(
                    state[:shell_size]@shell_physical@state[:shell_size]),
                "tip_translation_m": state[terminal:terminal+3].tolist(),
                "tip_rotation_rad": state[terminal+3:terminal+6].tolist(),
                "position_rms_m": float(np.sqrt(
                    np.sum(weights*np.sum(position_gap**2, axis=1))/.1)),
                "orientation_rms_rad": float(np.sqrt(
                    np.sum(weights*np.sum(orientation_gap**2, axis=1))/.1)),
            })
            if (diagnostics["support_force_balance_n"] > 1e-5 or
                    diagnostics["support_moment_balance_nm"] > 1e-5 or
                    diagnostics["shell_physical_work_j"] <= 0.):
                loads[load_name] = {"status": "FAILED_BALANCE",
                                    "diagnostics": diagnostics}
                continue
            diagnostics["status"] = "BOUNDED_SOLVE_PASSED"
            loads[load_name] = diagnostics
        channel_rows = [len(knots)-1 if basis == "piecewise_constant"
                        else len(knots) for basis in channel_kinds]
        result[label] = {"row_count": int(len(constraint)),
                         "channel_basis_fx_fy_fz_mx_my_mz": channel_kinds,
                         "channel_rows_fx_fy_fz_mx_my_mz": channel_rows,
                         "rank": rank, "loads": loads}
    return {"station_count": len(line.stations),
            "multiplier_knots": knots, "spaces": result}


def run(*, off_edge: bool = False) -> dict:
    expected = (Path(__file__).resolve().parents[1]/"src"/"anysolver").resolve()
    actual = Path(anysolver.__file__).resolve().parent
    if actual != expected:
        raise RuntimeError("channel screen imported another ANYsolver checkout")
    xs, ys = local_grid(2, transverse_cells=4)
    if off_edge:
        ys = ys.copy()
        center = np.flatnonzero(np.abs(ys) < 1e-12)
        if len(center) != 1:
            raise ArithmeticError("single transverse center row required")
        ys[center[0]] = .01
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    topologies = {
        "q4": _one_topology(xs, ys, beam, mixed_s3=False,
                             diagonal="bl_tr"),
        "mixed_s3_bl_tr": _one_topology(
            xs, ys, beam, mixed_s3=True, diagonal="bl_tr"),
        "mixed_s3_br_tl": _one_topology(
            xs, ys, beam, mixed_s3=True, diagonal="br_tl"),
    }
    return {
        "classification": "private channel-compatible material-line loaded screen",
        "qualification": "development only; no multiplier selection or G0B pass",
        "anysolver_import_path": str(Path(anysolver.__file__).resolve()),
        "python_version": sys.version.split()[0],
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "numba_disable_jit": os.environ.get("NUMBA_DISABLE_JIT"),
        "thread_settings": {key: os.environ.get(key) for key in (
            "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")},
        "shell_nodes": len(xs)*len(ys),
        "beam_half_cells": beam.n_half_cells,
        "transverse_grid_m": ys.tolist(),
        "material_line_y_m": 0.,
        "off_edge": off_edge,
        "topologies": topologies,
    }


if __name__ == "__main__":
    if len(sys.argv) > 2 or (len(sys.argv) == 2 and
                              sys.argv[1] != "--off-edge"):
        raise SystemExit("usage: channel_screen.py [--off-edge]")
    print(json.dumps(run(off_edge=len(sys.argv) == 2), indent=2,
                     sort_keys=True))
