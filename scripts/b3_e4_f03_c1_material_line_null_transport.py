"""Transport bounded material-line null actions to a finer native beam trace.

This is a G0 development discriminator, not a coupled solve or a multiplier
selection. The shell grid and continuous connection law remain fixed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import scipy
from scipy import linalg
from threadpoolctl import threadpool_info, threadpool_limits

from scripts import b3_e4_f03_c1_native_mixed_metric as metric
from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_c1_drill_quotient_metric import _material_line_space
from scripts.b3_e4_f03_material_line_loaded import _scales
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def _fixture(half_cells: int, xs, ys):
    beam = build(half_cells, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    ns = 6*len(xs)*len(ys)
    shell_free = np.array([i for i in range(ns)
                           if (i//6) % len(xs) != 0 and i % 6 != 5])
    beam_free = np.asarray(beam.context.free, dtype=int)
    free = np.r_[shell_free, ns+beam_free]
    scales, _ = _scales(ns, beam, free, row_count=1)
    return beam, shell_free, beam_free, free, scales[:len(free)]


def _shear_field(beam) -> np.ndarray:
    """Declared non-equilibrium transverse shear: lateral motion, zero yaw."""
    state = beam.context.initial.mechanical
    positions = state.positions+state.position_low
    result = np.zeros(beam.context.count)
    for i, x in enumerate(positions[:, 0]):
        if .9 <= x <= 1.+1e-12:
            result[6*i+1] = 1e-4*np.sin(np.pi*(x-.9)/.1)
    if np.max(np.abs(result)) <= 0.:
        raise ArithmeticError("analytic beam shear field has no resolved node")
    return result


def evaluate() -> dict:
    xs, ys = local_grid(8, transverse_cells=4)
    old, shell_free, _, old_free, old_scale = _fixture(12, xs, ys)
    new, new_shell_free, _, new_free, new_scale = _fixture(18, xs, ys)
    ns = 6*len(xs)*len(ys)
    if not np.array_equal(shell_free, new_shell_free):
        raise ArithmeticError("null transport changed the supported shell")
    shear = _shear_field(new)
    cases = {}
    for kind in metric.KINDS:
        old_rows, old_masses = _material_line_space(
            xs, ys, old, kind=kind, intervals=8)
        new_rows, new_masses = _material_line_space(
            xs, ys, new, kind=kind, intervals=8)
        if not np.allclose(old_masses, new_masses, rtol=0., atol=1e-14):
            raise ArithmeticError("null transport changed basis measures")
        row_scaled = old_rows[:, old_free]*old_scale[None, :]
        row_norm = np.linalg.norm(row_scaled, axis=1)
        if np.min(row_norm) <= 0. or not np.isfinite(row_norm).all():
            raise ArithmeticError("nonfinite or zero supported line row")
        normalized = row_scaled/row_norm[:, None]
        left, singular, _ = linalg.svd(normalized, full_matrices=False)
        tolerance = max(normalized.shape)*np.finfo(float).eps*singular[0]
        rank = int(np.sum(singular > tolerance))
        if rank == len(old_rows):
            raise ArithmeticError("selected old trace no longer has null actions")
        old_integrated = left[:, rank:]/row_norm[:, None]
        line_norm, _ = metric._line_metric(kind, 8, old_masses)
        modes = []
        transported_actions = []
        for j in range(old_integrated.shape[1]):
            dual = old_integrated[:, j]
            dual /= np.sqrt(dual@line_norm@dual)
            old_action = old_rows[:, old_free].T@dual
            new_action = new_rows[:, new_free].T@dual
            transported_actions.append(new_scale*new_action)
            density = dual.reshape(-1, 6)/old_masses[:, None]
            new_shell_n = len(new_shell_free)
            constraint_work = float(dual@(new_rows[:, ns:]@shear))
            modes.append({
                "integrated_action_N_Nm": dual.reshape(-1, 6).tolist(),
                "physical_density_N_per_m_Nm_per_m": density.tolist(),
                "old_scaled_action_norm_J": float(np.linalg.norm(
                    old_scale*old_action)),
                "new_shell_scaled_action_norm_J": float(np.linalg.norm(
                    new_scale[:new_shell_n]*new_action[:new_shell_n])),
                "new_beam_scaled_action_norm_J": float(np.linalg.norm(
                    new_scale[new_shell_n:]*new_action[new_shell_n:])),
                "constraint_term_analytic_shear_work_J": constraint_work,
                "physical_interface_analytic_shear_work_J": -constraint_work,
                "density_max_abs_by_channel_N_per_m_Nm_per_m":
                    np.max(np.abs(density), axis=0).tolist(),
            })
        transported_singular = linalg.svdvals(
            np.column_stack(transported_actions))
        transport_tolerance = (max(new_free.size, len(modes)) *
                               np.finfo(float).eps*transported_singular[0])
        cases[kind] = {
            "old_row_count": len(old_rows),
            "old_rank": rank,
            "old_smallest_singular": float(singular[-1]),
            "rank_tolerance": float(tolerance),
            "basis_integrals_m": old_masses.tolist(),
            "shell_row_change_max": float(np.max(np.abs(
                new_rows[:, :ns]-old_rows[:, :ns]))),
            "null_dual_R_norm_J": 1.,
            "transported_action_singular_values_J": transported_singular.tolist(),
            "transported_action_rank": int(np.sum(
                transported_singular > transport_tolerance)),
            "transported_action_rank_tolerance_J": float(transport_tolerance),
            "modes": modes,
        }
    return {
        "classification": "bounded material-line projected-null transport, not F03/G0B acceptance",
        "decision": "Do old supported null duals acquire beam action and shear work when only native beam resolution changes?",
        "geometry": "Q4 x8/y4, 35 mm shell, 100 mm square beam, 67.5 mm offset, 0.9-1.0 m material line",
        "old_beam_half_cells": old.n_half_cells,
        "new_beam_half_cells": new.n_half_cells,
        "shear_field": "beam nodal uy=1e-4*sin(pi*(x-.9)/.1) m for x>=.9; all beam rotations and shell coordinates zero; virtual field, not equilibrium",
        "dual_normalization": "each integrated mean-gap multiplier has unit energy in the existing physical-density line Riesz norm; density=integrated action/basis measure",
        "work_sign": "+lambda.T C u is KKT constraint-term work; physical interface traction is -C.T lambda and its work has the opposite sign",
        "cases": cases,
        "limitations": ["one flat reference and one beam refinement",
                       "null bases are SVD-dependent; no multiplier selection",
                       "analytic shear work is virtual work, not a coupled solution"],
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_git": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "python": sys.version.split()[0],
        "numpy": np.__version__, "scipy": scipy.__version__,
        "effective_threadpools": threadpool_info(),
        "env": {k: os.environ.get(k) for k in
                ("NUMBA_DISABLE_JIT", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS")},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    with threadpool_limits(limits=1):
        result = evaluate()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({kind: {
        "rank": value["old_rank"], "rows": value["old_row_count"],
        "max_new_beam_action_J": max(m["new_beam_scaled_action_norm_J"]
                                 for m in value["modes"]),
        "transported_action_rank": value["transported_action_rank"],
        "max_shear_work_J": max(abs(m["physical_interface_analytic_shear_work_J"])
                                for m in value["modes"])}
        for kind, value in result["cases"].items()}))


if __name__ == "__main__":
    main()
