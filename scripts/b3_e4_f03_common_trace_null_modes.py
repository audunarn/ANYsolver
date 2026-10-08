"""Identify the single supported near-null P1/dual reference traction mode."""

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


CHANNELS = ("mean_x", "mean_y", "mean_z",
            "first_x", "first_y", "first_z")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
        for intervals in (4, 8):
            knots = np.linspace(.9, 1., intervals+1)
            patches = [FiniteSurfaceTopFaceLine(
                xs, ys, beam, thickness=.035,
                x_interval=(float(low), float(high)))
                for low, high in zip(knots[:-1], knots[1:])]
            for kind in (("continuous_linear", "dual_linear")
                         if intervals == 8 else ("continuous_linear",)):
                rows, _, _, _ = _assemble(patches, frame, kind, intervals)
                active = rows[:, free]*scale[free]
                norms = np.linalg.norm(active, axis=1)
                unit = active/norms[:, None]
                left, singular, _ = linalg.svd(
                    unit, full_matrices=False, check_finite=True,
                    lapack_driver="gesvd")
                vector = left[:, -1]
                vector /= np.max(np.abs(vector))
                traction = vector/norms
                channel_strength = {
                    name: float(np.linalg.norm(vector[i::6]))
                    for i, name in enumerate(CHANNELS)}
                cases[f"b3_half_{half_cells}_{kind}_{intervals}"] = {
                    "relative_smallest_singular": float(singular[-1]/singular[0]),
                    "five_smallest_singular": singular[-5:].tolist(),
                    "normalised_left_mode_by_basis": vector.reshape(-1, 6).tolist(),
                    "raw_dual_by_basis": traction.reshape(-1, 6).tolist(),
                    "normalised_channel_strength": channel_strength,
                    "unit_row_mode_residual": float(np.linalg.norm(vector@unit)),
                    "relative_rank_cutoff": 1e-10,
                }
    return {
        "classification": "supported reference-chart one-mode diagnosis, not a multiplier choice",
        "question": "Is the apparent one-row P1/dual loss a longitudinal mean/first-moment identity or a different mode?",
        "model": "same x16/y4 C1 Q4/B3 reference work, supported coordinate scales",
        "cases": cases,
        "elapsed_s_not_benchmark": monotonic()-started,
        "limitations": ["SVD null traction is chart/scaling dependent",
                        "finite-chart work and mixed-system stability remain open"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate()
    if result["elapsed_s_not_benchmark"] > 120.:
        raise TimeoutError("bounded null-mode check exceeded 120 s")
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
    print(json.dumps({"cases": {key: {
        "relative_smallest_singular": value["relative_smallest_singular"],
        "normalised_channel_strength": value["normalised_channel_strength"]}
        for key, value in result["cases"].items()},
        "elapsed_s": result["elapsed_s_not_benchmark"]}, sort_keys=True))


if __name__ == "__main__":
    main()
