"""Check supported C1 top-face row containment; no loaded solve."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
from time import monotonic

import numpy as np
from scipy import linalg
from threadpoolctl import threadpool_info

from scripts._b3_e4_f03_native_fixture import SECTION_DIAGONAL, build
from scripts.b3_e4_f03_distributed_surface_finite import FiniteSurfaceTopFaceLine
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(xs, ys, beam, intervals: int) -> np.ndarray:
    knots = np.linspace(.9, 1., intervals+1)
    return np.vstack([FiniteSurfaceTopFaceLine(
        xs, ys, beam, thickness=.035,
        x_interval=(float(low), float(high))).reference_trace()
        for low, high in zip(knots[:-1], knots[1:])])


def evaluate() -> dict:
    started = monotonic()
    xs, ys = local_grid(16, transverse_cells=4)
    shell_size = 6*len(xs)*len(ys)
    reports = {}
    for half_cells in (12, 24):
        beam = build(half_cells, z_offset=.0675,
                     torsion_constant=square_torsion_constant(),
                     reference_profile="c1_tangent_2um")
        free_shell = np.array([i for i in range(shell_size)
                               if (i//6) % len(xs) != 0], dtype=int)
        free = np.r_[free_shell,
                     shell_size+np.asarray(beam.context.free, dtype=int)]
        displacement_scale = 1e6/(210e9*.035)
        nodal_scale = np.tile(np.full(6, displacement_scale),
                              len(xs)*len(ys)+beam.context.nodal_count//6)
        resultants = np.r_[np.tile(SECTION_DIAGONAL[:3]*displacement_scale, 2),
                           np.tile(SECTION_DIAGONAL[3:]*displacement_scale, 4)]
        retained = np.tile(np.r_[np.full(6, displacement_scale), resultants],
                           half_cells//2)
        scale = np.r_[nodal_scale, retained]
        if len(scale) != shell_size+beam.context.count:
            raise ArithmeticError("retained-coordinate scale changed")
        four = _rows(xs, ys, beam, 4)[:, free]*scale[free]
        eight = _rows(xs, ys, beam, 8)[:, free]*scale[free]
        four /= np.linalg.norm(four, axis=1)[:, None]
        eight /= np.linalg.norm(eight, axis=1)[:, None]
        coefficients, _, _, _ = linalg.lstsq(eight.T, four.T,
                                              cond=1e-11, check_finite=True)
        projection = coefficients.T@eight
        defect = np.linalg.norm(four-projection, axis=1)
        singular_eight = linalg.svdvals(eight, check_finite=True)
        singular_union = linalg.svdvals(np.vstack((eight, four)),
                                        check_finite=True)
        cutoff = 1e-10*singular_eight[0]
        reports[f"b3_half_{half_cells}"] = {
            "supported_four_rank": int(np.count_nonzero(
                linalg.svdvals(four) > cutoff)),
            "supported_eight_rank": int(np.count_nonzero(
                singular_eight > cutoff)),
            "supported_union_rank": int(np.count_nonzero(
                singular_union > cutoff)),
            "max_four_in_eight_projection_defect": float(np.max(defect)),
            "rms_four_in_eight_projection_defect": float(
                np.sqrt(np.mean(defect**2))),
            "free_primal_coordinates": len(free),
        }
    return {
        "classification": "bounded supported row-space nesting diagnostic, not interface stability or F03 acceptance",
        "question": "Is x16/four top-face enforcement an algebraic subspace of x16/eight for both native beam traces?",
        "model": "Q4 x16/y4 35mm plate, C1 tangent 2um B3-12/B3-24, same fixed shell/beam roots",
        "normalization": "fixture displacement/resultant column scales and unit row norms; relative singular cutoff 1e-10",
        "cases": reports,
        "elapsed_s_not_benchmark": monotonic()-started,
        "limitations": ["algebraic inclusion is not a physical inf-sup or locking test",
                        "reference-chart rows only; finite updated charts need separate work checks"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate()
    if result["elapsed_s_not_benchmark"] > 120.:
        raise TimeoutError("bounded row nesting check exceeded 120 s")
    result["source_sha256"] = {str(path): _sha(path) for path in (
        Path(__file__), Path("scripts/b3_e4_f03_distributed_surface_finite.py"),
        Path("scripts/_b3_e4_f03_native_fixture.py"))}
    result["python"] = platform.python_version()
    result["numpy"] = np.__version__
    result["threadpool_info"] = threadpool_info()
    result["thread_env"] = {key: os.environ.get(key) for key in
                            ("NUMBA_DISABLE_JIT", "OPENBLAS_NUM_THREADS",
                             "MKL_NUM_THREADS", "OMP_NUM_THREADS")}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"cases": result["cases"],
                      "elapsed_s": result["elapsed_s_not_benchmark"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
