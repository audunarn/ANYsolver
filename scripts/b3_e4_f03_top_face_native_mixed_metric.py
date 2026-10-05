"""Bounded top-face C1 retained-KKT norm comparison; no F03 acceptance.

Uses the existing auxiliary physical/chart primal norm and P0 H^-1/2 dual
norm to inspect the actual indefinite E4/B3 retained mixed tangent. These
norms are diagnostic and are never assembled into the mechanics operator.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
from time import monotonic

import numpy as np
from scipy import linalg
from threadpoolctl import threadpool_info

from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_c1_native_mixed_metric import (
    L_LINE, T, _beam_metric, _case, _drilling_metric, _line_metric,
)
from scripts.b3_e4_f03_distributed_surface_finite import FiniteSurfaceTopFaceLine
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate() -> dict:
    started = monotonic()
    deadline = started+120.
    xs, ys = local_grid(8, transverse_cells=4)
    shell, physical = raw_e4_tangent(xs, ys, thickness=T)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    ns = len(shell)
    shell_free = np.array([i for i in range(ns)
                           if (i//6) % len(xs) != 0])
    beam_free = np.asarray(beam.context.free)
    free = np.r_[shell_free, ns+beam_free]

    drill = _drilling_metric(xs, ys)
    R_shell = physical.copy()
    drill_ids = 6*np.arange(len(xs)*len(ys))+5
    R_shell[np.ix_(drill_ids, drill_ids)] += drill
    R_beam, R_resultant, layout = _beam_metric(beam)
    R_primal = linalg.block_diag(
        R_shell[np.ix_(shell_free, shell_free)],
        R_beam[np.ix_(beam_free, beam_free)])
    linalg.cholesky((R_primal+R_primal.T)/2, lower=True,
                    check_finite=True)
    K = linalg.block_diag(
        shell[np.ix_(shell_free, shell_free)],
        beam.tangent.toarray()[np.ix_(beam_free, beam_free)])
    if monotonic() > deadline:
        raise TimeoutError("bounded top-face assembly deadline")

    reports = {}
    for intervals in (2, 4):
        if monotonic() > deadline:
            raise TimeoutError("bounded top-face mixed deadline")
        knots = np.linspace(.9, 1., intervals+1)
        patches = [FiniteSurfaceTopFaceLine(
            xs, ys, beam, thickness=T,
            x_interval=(float(low), float(high)))
            for low, high in zip(knots[:-1], knots[1:])]
        masses = np.asarray([patch.basis_integral_m for patch in patches])
        gaps = [patch.evaluate_e4_total(
            np.zeros(patch.shell_size), beam.context.initial.mechanical)[:, 0]
            for patch in patches]
        max_gap = float(max(np.max(np.abs(gap)) for gap in gaps))
        if max_gap > 1e-12:
            raise ArithmeticError("top-face reference line opened")
        rows = np.vstack([patch.reference_trace() for patch in patches])
        C = rows[:, free]
        if len(C) != 6*intervals:
            raise ArithmeticError("top-face row inventory changed")
        R_line, line_info = _line_metric(
            "piecewise_constant", intervals, masses)
        line_chol = linalg.cholesky(R_line, lower=True)
        primal_chol = linalg.cholesky(R_primal, lower=True)
        normalized_C = linalg.solve_triangular(line_chol, C, lower=True)
        normalized_C = linalg.solve_triangular(
            primal_chol, normalized_C.T, lower=True).T
        scaled_rank = int(np.linalg.matrix_rank(normalized_C))
        if scaled_rank != len(C):
            raise ArithmeticError("norm-scaled top-face rows lost rank")
        A = np.block([[K, C.T],
                      [C, np.zeros((len(C), len(C)))]] )
        R = linalg.block_diag(R_primal, R_line)
        shell_n = len(shell_free)
        beam_n = len(beam_free)
        beam_resultant = R_resultant[np.ix_(beam_free, beam_free)]
        pieces = {"C": C, "blocks": [
            ("shell_physical", slice(0, shell_n),
             physical[np.ix_(shell_free, shell_free)]),
            ("shell_drilling_chart", slice(0, shell_n),
             R_shell[np.ix_(shell_free, shell_free)]-
             physical[np.ix_(shell_free, shell_free)]),
            ("beam_kinematic", slice(shell_n, shell_n+beam_n),
             R_beam[np.ix_(beam_free, beam_free)]-beam_resultant),
            ("beam_complementary", slice(shell_n, shell_n+beam_n),
             beam_resultant),
            ("line_dual", slice(shell_n+beam_n, None), R_line),
        ]}
        report = _case(A, R, pieces, len(C), deadline)
        report["normalized_constraint_rank"] = scaled_rank
        report["max_reference_gap_m_rad"] = max_gap
        report["line_norm"] = line_info
        reports[f"p0_m{intervals}"] = report
    return {
        "classification": "bounded top-face native retained mixed-KKT diagnostic, not G0B/F03 acceptance",
        "question": "Does two-to-four interval growth expose a weak mode in the actual indefinite retained E4/B3 system?",
        "elapsed_s_not_benchmark": monotonic()-started,
        "model": "C1 E4 Q4 x8/y4 35 mm, native B3-12 and 2 um tangent axis, left shell/root beam fixed",
        "loads": "operator-only metric; loaded torque/shear results are a separate saved screen",
        "operator": "actual virgin E4 tangent, full native B3 retained tangent, exact weak top-face position-moment rows",
        "norm": "E4 physical energy + independent drill chart; B3 kinematic and complementary metric; P0 physical-density H^-1/2 dual / Et",
        "layout": layout,
        "shell_rows": len(shell_free),
        "beam_rows": len(beam_free),
        "cases": reports,
        "limitations": [
            "one x8 shell and B3-12 ratio, not mesh-uniform well-posedness",
            "auxiliary drilling chart norm is not physical drilling stiffness",
            "beam kinematic H1 norm is diagnostic, not a replacement for the native half-cell trace",
            "floating H^-1/2 Gram is not an interval certificate",
            "smallest mixed singular value alone cannot establish physical transfer or locking absence",
        ],
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
               Path("scripts/_b3_e4_f03_native_fixture.py")]
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
                      "cases": {key: {
                          "beta_min": case["beta_min"],
                          "normed_condition": case["normed_condition"],
                          "near_null_metric_share": case["near_null_metric_share"],
                          "normalized_constraint_rank": case["normalized_constraint_rank"],
                      } for key, case in result["cases"].items()}},
                     sort_keys=True))


if __name__ == "__main__":
    main()
