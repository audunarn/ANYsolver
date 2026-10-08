"""Work-dual transport of the bounded native P0 mixed metric."""

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
from scripts.b3_e4_f03_c1_native_mixed_metric import (
    T as THICKNESS, _beam_metric, _case, _drilling_metric, _line_metric,
)
from scripts.b3_e4_f03_distributed_surface_finite import FiniteSurfaceTopFaceLine
from scripts.b3_e4_f03_local_footprint_work import skew
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant
from scripts.b3_e4_f03_top_face_common_trace import _raw_rows


OLD_RESULT = Path(
    "docs/agent_plans/B3_GE_E4_PL_F03_TOP_FACE_X8_MIXED_METRIC_20260927.json")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _block(patch: FiniteSurfaceTopFaceLine):
    length = patch.basis_integral_m
    arm_shift = np.array((patch.moment_center_x-.95, 0., 0.))
    transform = np.zeros((6, 6))
    transform[:3, :3] = length*np.eye(3)
    transform[3:, :3] = length*skew(arm_shift)
    transform[3:, 3:] = length*patch.inertia
    return transform


def evaluate() -> dict:
    started = monotonic()
    deadline = started+120.
    old = json.loads(OLD_RESULT.read_text())
    xs, ys = local_grid(8, transverse_cells=4)
    shell, physical = raw_e4_tangent(xs, ys, thickness=THICKNESS)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    ns = len(shell)
    shell_free = np.array([i for i in range(ns)
                           if (i//6) % len(xs) != 0])
    beam_free = np.asarray(beam.context.free)
    free = np.r_[shell_free, ns+beam_free]
    drill = _drilling_metric(xs, ys)
    shell_metric = physical.copy()
    drill_ids = 6*np.arange(len(xs)*len(ys))+5
    shell_metric[np.ix_(drill_ids, drill_ids)] += drill
    beam_metric, beam_resultant, layout = _beam_metric(beam)
    primal_metric = linalg.block_diag(
        shell_metric[np.ix_(shell_free, shell_free)],
        beam_metric[np.ix_(beam_free, beam_free)])
    K = linalg.block_diag(
        shell[np.ix_(shell_free, shell_free)],
        beam.tangent.toarray()[np.ix_(beam_free, beam_free)])
    reports = {}
    for intervals in (2, 4):
        if monotonic() > deadline:
            raise TimeoutError("bounded P0 norm construction deadline")
        knots = np.linspace(.9, 1., intervals+1)
        patches = [FiniteSurfaceTopFaceLine(
            xs, ys, beam, thickness=THICKNESS,
            x_interval=(float(low), float(high)))
            for low, high in zip(knots[:-1], knots[1:])]
        old_rows = np.vstack([patch.reference_trace() for patch in patches])
        raw_rows = np.vstack([
            patch.basis_integral_m*_raw_rows(patch, np.eye(3))
            for patch in patches])
        transforms = [_block(patch) for patch in patches]
        transform = linalg.block_diag(*transforms)
        defect = raw_rows-transform@old_rows
        relative_row_error = float(
            np.linalg.norm(defect)/np.linalg.norm(raw_rows))
        if relative_row_error > 1e-11:
            raise ArithmeticError("raw P0 row transform changed the constraint space")
        masses = np.array([patch.basis_integral_m for patch in patches])
        old_line_metric, old_line_info = _line_metric(
            "piecewise_constant", intervals, masses)
        raw_line_metric = transform@old_line_metric@transform.T
        linalg.cholesky(raw_line_metric, lower=True)
        C = raw_rows[:, free]
        A = np.block([[K, C.T],
                      [C, np.zeros((len(C), len(C)))]])
        R = linalg.block_diag(primal_metric, raw_line_metric)
        shell_n = len(shell_free)
        beam_n = len(beam_free)
        resultant = beam_resultant[np.ix_(beam_free, beam_free)]
        pieces = {"C": C, "blocks": [
            ("shell_physical", slice(0, shell_n),
             physical[np.ix_(shell_free, shell_free)]),
            ("shell_drilling_chart", slice(0, shell_n),
             shell_metric[np.ix_(shell_free, shell_free)]-
             physical[np.ix_(shell_free, shell_free)]),
            ("beam_kinematic", slice(shell_n, shell_n+beam_n),
             beam_metric[np.ix_(beam_free, beam_free)]-resultant),
            ("beam_complementary", slice(shell_n, shell_n+beam_n),
             resultant),
            ("raw_line_dual", slice(shell_n+beam_n, None),
             raw_line_metric),
        ]}
        report = _case(A, R, pieces, len(C), deadline)
        reference_beta = old["cases"][f"p0_m{intervals}"]["beta_min"]
        beta_relative = abs(report["beta_min"]-reference_beta)/reference_beta
        if beta_relative > 1e-8:
            raise ArithmeticError("work-dual norm transport changed mixed spectrum")
        rng = np.random.default_rng(112+intervals)
        primal = rng.normal(size=len(free))
        raw_dual = rng.normal(size=len(C))
        raw_work = float(raw_dual@(C@primal))
        old_work = float((transform.T@raw_dual)@(
            old_rows[:, free]@primal))
        work_relative = abs(raw_work-old_work)/max(
            abs(raw_work), abs(old_work), 1.)
        if work_relative > 1e-12:
            raise ArithmeticError("raw/centered multiplier work differs")
        reports[f"p0_m{intervals}"] = {
            "raw_beta_min": report["beta_min"],
            "saved_centered_beta_min": reference_beta,
            "beta_relative_difference": beta_relative,
            "raw_normed_condition": report["normed_condition"],
            "raw_row_transform_relative_error": relative_row_error,
            "dual_work_relative_error": work_relative,
            "constraint_rows": len(C),
            "line_block_determinants": [
                float(np.linalg.det(block)) for block in transforms],
            "transported_line_norm": old_line_info,
            "near_null_metric_share": report["near_null_metric_share"],
        }
    return {
        "classification": "bounded work-dual norm transport, not mesh-uniform stability or F03 acceptance",
        "question": "Are centered P0 and common raw P0 identical mixed operators under the physical work-dual row/metric transformation?",
        "model": "x8/y4 C1 Q4/B3-12, P0 two and four intervals, native indefinite retained tangent",
        "saved_centered_result_sha256": _sha(OLD_RESULT),
        "layout": layout,
        "cases": reports,
        "elapsed_s_not_benchmark": monotonic()-started,
        "limitations": ["transports the existing diagnostic line norm; not an independent norm derivation",
                        "one fixed mesh ratio; physical transfer and growing-space well-posedness remain open"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate()
    if result["elapsed_s_not_benchmark"] > 120.:
        raise TimeoutError("bounded P0 metric check exceeded 120 s")
    result["source_sha256"] = {str(path): _sha(path) for path in (
        Path(__file__), Path("scripts/b3_e4_f03_top_face_common_trace.py"),
        Path("scripts/b3_e4_f03_c1_native_mixed_metric.py"))}
    result["python"] = platform.python_version()
    result["numpy"] = np.__version__
    result["threadpool_info"] = threadpool_info()
    result["thread_env"] = {key: os.environ.get(key) for key in
                            ("NUMBA_DISABLE_JIT", "OPENBLAS_NUM_THREADS",
                             "MKL_NUM_THREADS", "OMP_NUM_THREADS")}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"cases": {key: {
        "beta_relative_difference": value["beta_relative_difference"],
        "raw_row_transform_relative_error": value[
            "raw_row_transform_relative_error"],
        "dual_work_relative_error": value["dual_work_relative_error"]}
        for key, value in result["cases"].items()},
        "elapsed_s": result["elapsed_s_not_benchmark"]}, sort_keys=True))


if __name__ == "__main__":
    main()
