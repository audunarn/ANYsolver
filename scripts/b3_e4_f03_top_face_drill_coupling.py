"""Bounded E4 drilling/chart coupling diagnosis for the x16 top-face line."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
from pathlib import Path
from time import monotonic

import numpy as np
import psutil
from scipy import linalg
from threadpoolctl import threadpool_info

from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_c1_native_mixed_metric import T, _drilling_metric
from scripts.b3_e4_f03_distributed_surface_finite import FiniteSurfaceTopFaceLine
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant
from scripts.b3_e4_f03_top_face_common_trace import _supported_scale


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate() -> dict:
    started = monotonic()
    xs, ys = local_grid(16, transverse_cells=4)
    shell, physical = raw_e4_tangent(xs, ys, thickness=T)
    if len(shell) > 1900:
        raise ValueError("dense E4 element operator exceeds existing row cap")
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    shell_free = np.array([i for i in range(len(shell))
                           if (i//6) % len(xs) != 0])
    free, coordinate_scale = _supported_scale(xs, ys, beam)
    if not np.array_equal(free[:len(shell_free)], shell_free):
        raise ArithmeticError("supported E4 layout changed")
    knots = np.linspace(.9, 1., 9)
    patches = [FiniteSurfaceTopFaceLine(
        xs, ys, beam, thickness=T,
        x_interval=(float(low), float(high)))
        for low, high in zip(knots[:-1], knots[1:])]
    C = np.vstack([patch.reference_trace() for patch in patches])[:, free]
    shell_C = C[:, :len(shell_free)]
    physical_positions = np.flatnonzero(shell_free % 6 != 5)
    drill_positions = np.flatnonzero(shell_free % 6 == 5)
    scaled_C = shell_C*coordinate_scale[shell_free]
    row_norm = np.linalg.norm(C*coordinate_scale[free], axis=1)
    if np.any(row_norm == 0):
        raise ArithmeticError("top-face work row vanished")
    drill_row = scaled_C[:, drill_positions]/row_norm[:, None]

    drill_metric = _drilling_metric(xs, ys)
    R_shell = physical.copy()
    drill_dofs = 6*np.arange(len(xs)*len(ys))+5
    R_shell[np.ix_(drill_dofs, drill_dofs)] += drill_metric
    K = shell[np.ix_(shell_free, shell_free)]
    R = R_shell[np.ix_(shell_free, shell_free)]
    if np.any(np.diag(R) <= 0):
        raise ArithmeticError("physical/chart reference metric lacks a diagonal")
    scale = 1/np.sqrt(np.diag(R))
    scaled_K = scale[:, None]*K*scale[None, :]
    K_pp = scaled_K[np.ix_(physical_positions, physical_positions)]
    K_pd = scaled_K[np.ix_(physical_positions, drill_positions)]
    K_dd = scaled_K[np.ix_(drill_positions, drill_positions)]
    numerator = float(linalg.norm(K_pd))
    total = float(linalg.norm(scaled_K))
    physical_norm = float(linalg.norm(K_pp))
    drill_norm = float(linalg.norm(K_dd))
    physical_drill = physical[np.ix_(shell_free, shell_free)][
        np.ix_(drill_positions, np.arange(len(shell_free)))]
    elapsed = monotonic()-started
    info = psutil.Process().memory_info()
    peak = int(info.peak_wset if os.name == "nt" else info.rss)
    if elapsed > 120. or peak > 2*1024**3:
        raise RuntimeError("bounded drilling diagnostic resource limit exceeded")
    return {
        "classification": "bounded reference-chart drilling coupling diagnosis; not F03/G0B acceptance",
        "question": "Can the chart-dominated weak mixed spectrum be quotiented without changing the physical connection operator?",
        "model": "C1 Q4 x16/y4, native B3-12, eight top-face P0 intervals, fixed left roots",
        "shell_free_dofs": len(shell_free),
        "physical_shell_dofs": len(physical_positions),
        "drilling_shell_dofs": len(drill_positions),
        "top_face_max_normalized_drill_row": float(np.max(np.abs(drill_row))),
        "top_face_drill_frobenius": float(linalg.norm(drill_row)),
        "physical_E4_drill_block_frobenius": float(linalg.norm(physical_drill)),
        "scaled_actual_E4_cross_frobenius": numerator,
        "scaled_actual_E4_cross_over_full": numerator/max(total, 1e-300),
        "scaled_actual_E4_cross_over_blocks": numerator/max(
            np.sqrt(physical_norm*drill_norm), 1e-300),
        "scaled_actual_E4_physical_block_frobenius": physical_norm,
        "scaled_actual_E4_drill_block_frobenius": drill_norm,
        "scaled_actual_E4_cross_max_absolute": float(np.max(np.abs(K_pd))),
        "elapsed_s_not_benchmark": elapsed,
        "peak_rss_bytes": peak,
        "limits": {"max_dense_rows": 1900, "wall_s": 120,
                   "rss_bytes": 2*1024**3},
        "limitations": ["reference chart only; finite-state drilling coupling not tested",
                        "zero top-face drill rows alone do not justify deleting coupled E4 coordinates",
                        "no new mixed eigenvalue or physical accuracy result"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate()
    sources = [Path(__file__),
               Path("scripts/b3_e4_f03_c1_native_mixed_metric.py"),
               Path("scripts/b3_e4_f03_distributed_surface_finite.py"),
               Path("scripts/_b3_e4_f03_native_fixture.py"),
               Path("scripts/b3_e4_f03_plate_patch_work.py")]
    result["source_git"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True).strip()
    result["source_sha256"] = {str(path): _sha(path) for path in sources}
    result["python"] = platform.python_version()
    result["numpy"] = np.__version__
    result["threadpool_info"] = threadpool_info()
    result["thread_env"] = {key: os.environ.get(key) for key in
                            ("NUMBA_DISABLE_JIT", "OPENBLAS_NUM_THREADS",
                             "MKL_NUM_THREADS", "OMP_NUM_THREADS")}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"elapsed_s": result["elapsed_s_not_benchmark"],
                      "max_drill_row": result["top_face_max_normalized_drill_row"],
                      "cross_over_full": result["scaled_actual_E4_cross_over_full"],
                      "cross_over_blocks": result["scaled_actual_E4_cross_over_blocks"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
