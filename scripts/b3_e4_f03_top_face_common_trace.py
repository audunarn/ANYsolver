"""Bounded reference-chart comparison of P0 top-face work spaces.

This is a mechanical discriminator, not a production line law or a G0 pass.
The raw six rows use one reference material frame and arm convention over
the whole bond; the old rows use their interval-specific frame and inertia.
"""

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
from scripts.b3_e4_f03_local_footprint_work import skew
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _raw_rows(patch: FiniteSurfaceTopFaceLine, common_frame: np.ndarray
              ) -> np.ndarray:
    """Unnormalised transverse zeroth/first position moments at reference."""
    shell_size = patch.shell_size
    total = shell_size+patch.beam.context.count
    rows = np.zeros((6, total))
    state = patch.beam.context.initial.mechanical
    qc = common_frame.T
    for point in patch.points:
        _, _, frame = point.port.pose_pair(state)
        port = point.port.tangent(state)
        gap = np.zeros((3, total))
        for node, shape in zip(point.nodes, point.shape):
            start = 6*int(node)
            gap[:, start:start+3] += shape*np.eye(3)
            gap[:, start+3:start+6] -= shape*skew(
                np.array((0., 0., patch.top)))
        offset = frame@np.array((0., point.y, -.05))
        gap[:, shell_size:] -= np.column_stack((
            np.eye(3), -skew(offset)))@port
        material_gap = qc@gap
        # Reference shell-top arm from the fixed x=.95, y=0 material point.
        arm = qc@np.array((point.x-.95, point.y, 0.))
        rows[:3] += point.weight*material_gap
        rows[3:] += point.weight*skew(arm)@material_gap
    return rows


def _supported_scale(xs: np.ndarray, ys: np.ndarray, beam) -> tuple:
    shell_size = 6*len(xs)*len(ys)
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
                       beam.n_half_cells//2)
    scale = np.r_[nodal_scale, retained]
    if len(scale) != shell_size+beam.context.count:
        raise ArithmeticError("retained-coordinate scale changed")
    return free, scale


def _space_comparison(old: np.ndarray, raw: np.ndarray) -> dict:
    old_norm = np.linalg.norm(old, axis=1)
    raw_norm = np.linalg.norm(raw, axis=1)
    if min(old_norm.min(), raw_norm.min()) <= 0.:
        raise ArithmeticError("a physical work row vanished")
    old_unit = old/old_norm[:, None]
    raw_unit = raw/raw_norm[:, None]
    raw_to_old = linalg.lstsq(old_unit.T, raw_unit.T,
                             cond=1e-11, check_finite=True)[0]
    old_to_raw = linalg.lstsq(raw_unit.T, old_unit.T,
                             cond=1e-11, check_finite=True)[0]
    raw_error = np.linalg.norm(raw_unit-raw_to_old.T@old_unit, axis=1)
    old_error = np.linalg.norm(old_unit-old_to_raw.T@raw_unit, axis=1)
    old_sv = linalg.svdvals(old_unit, check_finite=True)
    raw_sv = linalg.svdvals(raw_unit, check_finite=True)
    union_sv = linalg.svdvals(np.vstack((old_unit, raw_unit)),
                              check_finite=True)
    cutoff = 1e-10*max(old_sv[0], raw_sv[0])
    return {
        "old_rank": int(np.count_nonzero(old_sv > cutoff)),
        "common_trace_rank": int(np.count_nonzero(raw_sv > cutoff)),
        "union_rank": int(np.count_nonzero(union_sv > cutoff)),
        "max_common_in_old_row_defect": float(raw_error.max()),
        "max_old_in_common_row_defect": float(old_error.max()),
        "common_in_old_row_defects": raw_error.tolist(),
        "old_in_common_row_defects": old_error.tolist(),
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
        center_element, center_cell, center_fraction, _ = beam._locate(.95)
        from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
        center = NativeHalfCellSpatialPort(
            beam.context, center_element, center_cell, center_fraction)
        common_frame = center.pose_pair(state)[2]
        free, scale = _supported_scale(xs, ys, beam)
        for intervals in (4, 8):
            knots = np.linspace(.9, 1., intervals+1)
            old_parts = []
            raw_parts = []
            for low, high in zip(knots[:-1], knots[1:]):
                patch = FiniteSurfaceTopFaceLine(
                    xs, ys, beam, thickness=.035,
                    x_interval=(float(low), float(high)))
                old_parts.append(patch.reference_trace())
                raw_parts.append(_raw_rows(patch, common_frame))
            old = np.vstack(old_parts)[:, free]*scale[free]
            raw = np.vstack(raw_parts)[:, free]*scale[free]
            cases[f"b3_half_{half_cells}_p0_{intervals}"] = (
                _space_comparison(old, raw))
    return {
        "classification": "bounded reference-chart continuous-law discriminator; no loaded solve or F03 acceptance",
        "question": "Does one fixed material-frame raw six-moment trace reproduce the old interval-frame P0 supported constraint spaces?",
        "model": "Q4 x16/y4 35mm, C1 tangent 2um B3-12/B3-24, common x=.95 reference frame and shell-top arm",
        "normalization": "fixture coordinate scales, unit row norms, relative singular cutoff 1e-10",
        "cases": cases,
        "elapsed_s_not_benchmark": monotonic()-started,
        "limitations": ["linear reference chart only", "no P1/dual or finite-chart work proof",
                        "a row-space difference requires frame/arm derivation, not automatic formulation failure"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate()
    if result["elapsed_s_not_benchmark"] > 120.:
        raise TimeoutError("bounded trace comparison exceeded 120 s")
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
    print(json.dumps({"cases": {key: {k: v for k, v in case.items()
                                       if not k.endswith("defects")}
                                 for key, case in result["cases"].items()},
                      "elapsed_s": result["elapsed_s_not_benchmark"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
