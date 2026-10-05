"""Bounded P0/P1/dual reference work rows from one top-face trace."""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import platform
from time import monotonic
from types import SimpleNamespace

import numpy as np
from scipy import linalg
from threadpoolctl import threadpool_info

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts.b3_e4_f03_distributed_surface_finite import FiniteSurfaceTopFaceLine
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts.b3_e4_f03_square_section_control import square_torsion_constant
from scripts.b3_e4_f03_top_face_common_trace import _raw_rows, _supported_scale


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assemble(patches, frame, kind: str, intervals: int):
    space = LineMultiplierSpace(kind, tuple(np.linspace(0., 1., intervals+1)))
    n = patches[0].shell_size+patches[0].beam.context.count
    rows = np.zeros((space.count, 6, n))
    basis_masses = np.zeros(space.count)
    basis_first = np.zeros(space.count)
    basis_second = np.zeros(space.count)
    for patch in patches:
        length = patch.x_interval[1]-patch.x_interval[0]
        for index in range(space.count):
            selected = []
            for point in patch.points:
                basis = space.values((point.x-.9)/.1)[index]
                if basis:
                    selected.append(replace(point,
                                            weight=point.weight*basis))
                mass = length*point.weight*basis
                basis_masses[index] += mass
                basis_first[index] += mass*(point.x-.95)
                basis_second[index] += mass*(point.x-.95)**2
            if selected:
                weighted = SimpleNamespace(
                    shell_size=patch.shell_size, beam=patch.beam,
                    points=selected, top=patch.top)
                rows[index] += length*_raw_rows(weighted, frame)
    return rows.reshape(space.count*6, n), basis_masses, basis_first, basis_second


def _rank(matrix):
    unit = matrix/np.linalg.norm(matrix, axis=1)[:, None]
    singular = linalg.svdvals(unit, check_finite=True)
    return int(np.count_nonzero(singular > 1e-10*singular[0]))


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
            work = {}
            for kind in ("piecewise_constant", "continuous_linear",
                         "dual_linear"):
                rows, masses, first, second = _assemble(
                    patches, frame, kind, intervals)
                active = rows[:, free]*scale[free]
                if not np.isfinite(active).all():
                    raise ArithmeticError("nonfinite signed raw work rows")
                work[kind] = (rows, masses, first, second)
                cases[f"b3_half_{half_cells}_{kind}_{intervals}"] = {
                    "supported_rank": _rank(active),
                    "row_count": int(rows.shape[0]),
                    "basis_integrals_m": masses.tolist(),
                    "basis_first_m2": first.tolist(),
                    "basis_second_m3": second.tolist(),
                    "all_basis_integrals_positive": bool(np.all(masses > 0.)),
                }
            p0_total = work["piecewise_constant"][0].reshape(
                intervals, 6, -1).sum(axis=0)
            for kind in ("continuous_linear", "dual_linear"):
                total = work[kind][0].reshape(
                    intervals+1, 6, -1).sum(axis=0)
                difference = np.linalg.norm(total-p0_total)
                relative = difference/max(np.linalg.norm(p0_total), 1e-30)
                cases[f"b3_half_{half_cells}_{kind}_{intervals}"][
                    "partition_work_relative_error"] = float(relative)
                if relative > 1e-12:
                    raise ArithmeticError("common trace partition work failed")
            # Integrating affine scalar fields is independent of the
            # kinematic gap map and tests signed quadrature/reproduction.
            for kind, (_, masses, first, second) in work.items():
                basis = LineMultiplierSpace(
                    kind, tuple(np.linspace(0., 1., intervals+1)))
                if (abs(masses.sum()-.1) > 1e-13 or
                        abs(first.sum()) > 1e-13 or
                        abs(second.sum()-.1**3/12) > 1e-13):
                    raise ArithmeticError("constant/affine/quadratic partition failed")
                if len(masses) != basis.count:
                    raise AssertionError("basis row count changed")
    return {
        "classification": "same-integrand reference work and signed-basis feasibility; no F03 selection",
        "question": "Can P0/P1/dual use one fixed-frame raw six-moment integrand, including signed dual weights, without a positive-covariance guard?",
        "model": "Q4 x16/y4 35mm, C1 B3-12/B3-24, x=.95 fixed frame, P0/P1/dual at 4 and 8 intervals",
        "normalization": "physical longitudinal integrals, supported coordinate scales for rank, relative rank cutoff 1e-10",
        "cases": cases,
        "elapsed_s_not_benchmark": monotonic()-started,
        "limitations": ["reference chart only", "row rank/partition do not prove inf-sup, locking, or physical fidelity",
                        "finite-chart work and tangent remain required"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate()
    if result["elapsed_s_not_benchmark"] > 120.:
        raise TimeoutError("bounded common trace basis check exceeded 120 s")
    result["source_sha256"] = {str(path): _sha(path) for path in (
        Path(__file__), Path("scripts/b3_e4_f03_top_face_common_trace.py"),
        Path("scripts/b3_e4_f03_distributed_surface_finite.py"))}
    result["python"] = platform.python_version()
    result["numpy"] = np.__version__
    result["threadpool_info"] = threadpool_info()
    result["thread_env"] = {key: os.environ.get(key) for key in
                            ("NUMBA_DISABLE_JIT", "OPENBLAS_NUM_THREADS",
                             "MKL_NUM_THREADS", "OMP_NUM_THREADS")}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"summary": {key: {
        "supported_rank": value["supported_rank"],
        "row_count": value["row_count"],
        "partition_work_relative_error": value.get(
            "partition_work_relative_error")}
        for key, value in result["cases"].items()},
        "elapsed_s": result["elapsed_s_not_benchmark"]}, sort_keys=True))


if __name__ == "__main__":
    main()
