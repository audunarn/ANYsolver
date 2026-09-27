"""Bounded dual-eight near-null check on complete and supported primal rows."""

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

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts.b3_e4_f03_common_trace_spaces import _assemble
from scripts.b3_e4_f03_distributed_surface_finite import FiniteSurfaceTopFaceLine
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts.b3_e4_f03_square_section_control import square_torsion_constant
from scripts.b3_e4_f03_top_face_common_trace import _supported_scale


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _spectrum(matrix: np.ndarray) -> dict:
    singular = linalg.svdvals(matrix, check_finite=True)
    return {
        "rank_at_1e_10": int(np.count_nonzero(singular > 1e-10*singular[0])),
        "smallest_relative": float(singular[-1]/singular[0]),
        "next_relative": float(singular[-2]/singular[0]),
    }


def evaluate() -> dict:
    started = monotonic()
    xs, ys = local_grid(16, transverse_cells=4)
    cases = {}
    for half_cells in (12, 24):
        beam = build(half_cells, z_offset=.0675,
                     torsion_constant=square_torsion_constant(),
                     reference_profile="c1_tangent_2um")
        state = beam.context.initial.mechanical
        element, cell, fraction, _ = beam._locate(.95)
        frame = NativeHalfCellSpatialPort(
            beam.context, element, cell, fraction).pose_pair(state)[2]
        free, scale = _supported_scale(xs, ys, beam)
        knots = np.linspace(.9, 1., 9)
        patches = [FiniteSurfaceTopFaceLine(
            xs, ys, beam, thickness=.035,
            x_interval=(float(low), float(high)))
            for low, high in zip(knots[:-1], knots[1:])]
        rows, _, _, _ = _assemble(patches, frame, "dual_linear", 8)
        scaled = rows*scale
        row_norms = np.linalg.norm(scaled[:, free], axis=1)
        supported = scaled[:, free]/row_norms[:, None]
        complete = scaled/row_norms[:, None]
        left, singular, _ = linalg.svd(
            supported, full_matrices=False, check_finite=True,
            lapack_driver="gesvd")
        near_null = left[:, -1]
        fixed = np.ones(complete.shape[1], dtype=bool)
        fixed[free] = False
        supported_residual = near_null@supported
        complete_residual = near_null@complete
        cases[f"b3_half_{half_cells}"] = {
            "complete": _spectrum(complete),
            "supported": _spectrum(supported),
            "supported_near_null_norm": float(np.linalg.norm(supported_residual)),
            "complete_near_null_norm": float(np.linalg.norm(complete_residual)),
            "fixed_column_residual_norm": float(np.linalg.norm(
                complete_residual[fixed])),
            "supported_columns": len(free),
            "fixed_columns": int(fixed.sum()),
            "near_null_channel_strength": {
                name: float(np.linalg.norm(near_null[index::6]))
                for index, name in enumerate(("mean_x", "mean_y", "mean_z",
                                              "first_x", "first_y", "first_z"))},
            "smallest_singular": float(singular[-1]),
        }
    return {
        "classification": "bounded dual-eight support discriminator; no F03 selection",
        "question": "Does the dual-eight near-null persist on the complete primal columns, or arise from support elimination?",
        "model": "same x16/y4 C1 Q4/B3-12/B3-24 reference trace; all columns versus registered root supports",
        "normalization": "same supported row norms for both matrices and fixture coordinate column scales",
        "cases": cases,
        "elapsed_s_not_benchmark": monotonic()-started,
        "limitations": ["complete-versus-supported rank does not prove uniform inf-sup or locking",
                        "finite-chart law and physical dual map remain open"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate()
    if result["elapsed_s_not_benchmark"] > 120.:
        raise TimeoutError("bounded support check exceeded 120 s")
    result["source_sha256"] = {str(path): _sha(path) for path in (
        Path(__file__), Path("scripts/b3_e4_f03_common_trace_spaces.py"),
        Path("scripts/b3_e4_f03_top_face_common_trace.py"))}
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
