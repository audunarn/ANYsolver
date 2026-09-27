"""Bounded row-growth screen for the private bonded material-line candidate.

P0, continuous-P1 and dual-P1 rows are provisional. This same-primal
linear solve checks row growth, work, response and unresolved continuous
gaps; it cannot select a stable production multiplier space alone.
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
from scripts.b3_e4_f03_material_line_loaded import (
    _scales, _solve, material_line_mean_rows,
)
from scripts.b3_e4_f03_material_line_position import MaterialLinePosition
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def _rows(line: MaterialLinePosition, space: LineMultiplierSpace):
    count = len(line.stations)
    position = line.reference_jacobian().reshape(count, 3, -1)
    orientation = line.reference_orientation_jacobian().reshape(count, 3, -1)
    weights = np.array([station.weight for station in line.stations])
    values = np.array([space.values((station.x-.9)/.1)
                       for station in line.stations])
    measure = weights@values
    if (measure.shape != (space.count,) or
            np.min(measure) <= 1e-12 or
            abs(np.sum(weights)-.1) > 1e-12):
        raise ArithmeticError("complete positive provisional line basis required")
    rows = np.zeros((6*space.count, position.shape[2]))
    for index in range(space.count):
        weighted = weights*values[:, index]/measure[index]
        rows[6*index:6*index+3] = np.einsum(
            "k,kij->ij", weighted, position)
        rows[6*index+3:6*index+6] = np.einsum(
            "k,kij->ij", weighted, orientation)
    if not np.isfinite(rows).all():
        raise ArithmeticError("finite provisional line rows required")
    return rows, measure


def _scaled_row_diagnostics(constraint, free, primal_scales):
    """Bounded physical-coordinate rank screen, never a stability verdict."""
    if (constraint.shape[0] > 60 or
            primal_scales.shape != (len(free),)):
        raise ValueError("bounded line row diagnostic only")
    mapped = constraint[:, free]*primal_scales[None, :]
    active = np.flatnonzero(np.any(mapped != 0., axis=0))
    if len(active) > 1200:
        raise ValueError("bounded line row diagnostic only")
    # Zero columns outside the attachment cannot affect row rank. Keep the
    # same 1200-column SVD cap while allowing a larger supported model.
    mapped = mapped[:, active]
    row_norms = np.linalg.norm(mapped, axis=1)
    if not np.isfinite(row_norms).all() or np.min(row_norms) <= 0.:
        raise ArithmeticError("zero or nonfinite physical line row")
    normalized = mapped/row_norms[:, None]
    left, singular, _ = np.linalg.svd(normalized, full_matrices=False)
    tolerance = max(normalized.shape)*np.finfo(float).eps*singular[0]
    return {
        "scaled_row_rank": int(np.sum(singular > tolerance)),
        "scaled_row_singular_values": singular.tolist(),
        "scaled_row_norm_min": float(np.min(row_norms)),
        "scaled_row_norm_max": float(np.max(row_norms)),
        "active_primal_columns": int(len(active)),
        "left_smallest_mode": left[:, -1].tolist(),
        "left_null_modes": left[:, singular <= tolerance].T.tolist(),
        "rank_tolerance": float(tolerance),
        "meaning": "bounded unit-row, physical-coordinate rank diagnostic; not inf-sup or mixed-system stability",
    }


def run() -> dict:
    expected = (Path(__file__).resolve().parents[1]/"src"/"anysolver").resolve()
    actual = Path(anysolver.__file__).resolve().parent
    if actual != expected:
        raise RuntimeError("line-space screen imported another ANYsolver checkout")
    xs, ys = local_grid(2, transverse_cells=4)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    shell_size = 6*len(xs)*len(ys)
    shell_tangent, shell_physical = raw_e4_tangent(xs, ys, thickness=.035)
    if beam.tangent is None or beam.residual is None:
        raise ArithmeticError("native assembled fixture required")
    primal = sparse.block_diag((sparse.csr_matrix(shell_tangent),
                                beam.tangent), format="csr")
    residual = np.r_[np.zeros(shell_size), beam.residual]
    line = MaterialLinePosition(xs, ys, beam)
    fixed_shell = {6*(j*len(xs)+i)+axis
                   for j in range(len(ys)) for i, x in enumerate(xs)
                   if abs(x+.5) < 1e-12 for axis in range(6)}
    fixed_beam = {shell_size+int(index) for index in beam.context.fixed}
    free = np.setdiff1d(
        np.arange(primal.shape[0]), np.array(sorted(fixed_shell|fixed_beam)))
    station_position = line.reference_jacobian().reshape(len(line.stations), 3, -1)
    station_orientation = line.reference_orientation_jacobian().reshape(
        len(line.stations), 3, -1)
    weights = np.array([station.weight for station in line.stations])
    shell_reference = line.reference_nodes
    beam_reference = (beam.context.initial.mechanical.positions
                      +beam.context.initial.mechanical.position_low)
    variants = (
        ("p0_one", LineMultiplierSpace("piecewise_constant", (0., 1.))),
        ("p0_two", LineMultiplierSpace("piecewise_constant", (0., .5, 1.))),
        ("p1_two", LineMultiplierSpace("continuous_linear", (0., .5, 1.))),
        ("dual_two", LineMultiplierSpace("dual_linear", (0., .5, 1.))),
    )
    p0_two_rows, _ = _rows(line, variants[1][1])
    results = {}
    for label, space in variants:
        constraint, measure = _rows(line, space)
        if label == "p0_one" and np.max(np.abs(
                constraint-material_line_mean_rows(line))) > 1e-12:
            raise ArithmeticError("P0 mean row changed from loaded screen")
        scales, energy_scale = _scales(
            shell_size, beam, free, row_count=len(constraint))
        row_diagnostic = _scaled_row_diagnostics(
            constraint, free, scales[:len(free)])
        if label in ("p1_two", "dual_two"):
            yaw = constraint[[5, 11, 17]]
            row_diagnostic["unscaled_yaw_identity_relative"] = float(
                np.linalg.norm(yaw[0]-2*yaw[1]+yaw[2]) /
                max(1., np.linalg.norm(yaw)))
            row_diagnostic["unscaled_yaw_p0_end_max"] = float(max(
                np.max(np.abs(yaw[0]-p0_two_rows[5])),
                np.max(np.abs(yaw[2]-p0_two_rows[11]))))
        outputs = {}
        for load_name, axis, magnitude in (("tip_mx_100nm", 3, 100.),
                                           ("tip_fz_1000n", 2, 1000.)):
            if row_diagnostic["scaled_row_rank"] != len(constraint):
                outputs[load_name] = {
                    "status": "FAILED_DEPENDENT_ROWS",
                    "reason": "scaled supported constraint rows are dependent; no solve accepted",
                }
                continue
            load = np.zeros(primal.shape[0])
            load[shell_size+6*beam.n_half_cells+axis] = magnitude
            try:
                state, equation, diagnostic = _solve(
                    primal, residual, constraint, free, scales,
                    energy_scale, load)
            except (ArithmeticError, MatrixRankWarning) as error:
                outputs[load_name] = {
                    "status": "FAILED_NUMERICAL",
                    "reason": f"{type(error).__name__}: {error}",
                }
                continue
            shell_support = equation[:shell_size].reshape(-1, 6)
            beam_support = equation[shell_size:shell_size+
                                    beam.context.nodal_count].reshape(-1, 6)
            support_force = (shell_support[:, :3].sum(axis=0)
                             +beam_support[:, :3].sum(axis=0))
            support_moment = (np.sum(np.cross(shell_reference,
                                              shell_support[:, :3])
                                     +shell_support[:, 3:], axis=0)
                              +np.sum(np.cross(beam_reference,
                                              beam_support[:, :3])
                                     +beam_support[:, 3:], axis=0))
            applied_force = np.zeros(3)
            applied_moment = np.zeros(3)
            if axis < 3:
                applied_force[axis] = magnitude
                applied_moment = np.cross(beam_reference[-1], applied_force)
            else:
                applied_moment[axis-3] = magnitude
            gap_position = np.einsum("kij,j->ki", station_position, state)
            gap_orientation = np.einsum("kij,j->ki", station_orientation, state)
            terminal = shell_size+6*beam.n_half_cells
            diagnostic.update({
                "support_force_balance_n": float(np.linalg.norm(
                    support_force+applied_force)),
                "support_moment_balance_nm": float(np.linalg.norm(
                    support_moment+applied_moment)),
                "tip_translation_m": state[terminal:terminal+3].tolist(),
                "tip_rotation_rad": state[terminal+3:terminal+6].tolist(),
                "shell_physical_work_j": float(
                    state[:shell_size]@shell_physical@state[:shell_size]),
                "position_rms_m": float(np.sqrt(
                    np.sum(weights*np.sum(gap_position**2, axis=1))/.1)),
                "orientation_rms_rad": float(np.sqrt(
                    np.sum(weights*np.sum(gap_orientation**2, axis=1))/.1)),
                "position_max_m": float(np.max(np.linalg.norm(
                    gap_position, axis=1))),
                "orientation_max_rad": float(np.max(np.linalg.norm(
                    gap_orientation, axis=1))),
            })
            if (diagnostic["support_force_balance_n"] > 1e-5 or
                    diagnostic["support_moment_balance_nm"] > 1e-5 or
                    diagnostic["shell_physical_work_j"] <= 0.):
                outputs[load_name] = {
                    "status": "FAILED_BALANCE",
                    "diagnostics": diagnostic,
                }
                continue
            diagnostic["status"] = "BOUNDED_SOLVE_PASSED"
            outputs[load_name] = diagnostic
        results[label] = {
            "space": space.kind,
            "row_count": int(len(constraint)),
            "basis_integrals_m": measure.tolist(),
            "row_diagnostic": row_diagnostic,
            "loads": outputs,
        }
    return {
        "classification": "private fixed-primal material-line row-growth screen",
        "qualification": "development only; not a multiplier selection or G0B pass",
        "anysolver_import_path": str(Path(anysolver.__file__).resolve()),
        "python_version": sys.version.split()[0],
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "numba_disable_jit": os.environ.get("NUMBA_DISABLE_JIT"),
        "thread_settings": {
            key: os.environ.get(key) for key in (
                "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")},
        "shell_nodes": int(len(shell_reference)),
        "beam_half_cells": int(beam.n_half_cells),
        "station_count": int(len(line.stations)),
        "result": results,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
