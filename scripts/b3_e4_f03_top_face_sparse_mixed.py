"""Bounded sparse cross-check of the actual native retained mixed tangent.

This is a development diagnostic in the inherited auxiliary work norm. It
does not establish a mesh-uniform inf-sup bound or qualify a line space.
"""

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
from scipy import linalg, sparse
from scipy.sparse import linalg as spla
from threadpoolctl import threadpool_info

from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_c1_native_mixed_metric import (
    T, _beam_metric, _drilling_metric, _line_metric,
)
from scripts.b3_e4_f03_distributed_surface_finite import FiniteSurfaceTopFaceLine
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant
from scripts.b3_e4_f03_top_face_common_trace import _supported_scale


PREVIOUS = Path(
    "docs/agent_plans/B3_GE_E4_PL_F03_TOP_FACE_X8_MIXED_METRIC_20260927.json")
MAX_DENSE_ROWS = 1900
MAX_WALL_S = 120.
MAX_RSS_BYTES = 2*1024**3


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _peak_rss() -> int:
    info = psutil.Process().memory_info()
    return int(info.peak_wset if os.name == "nt" else info.rss)


def evaluate(nx: int) -> dict:
    started = monotonic()
    intervals = nx//2
    xs, ys = local_grid(nx, transverse_cells=4)
    shell, physical = raw_e4_tangent(xs, ys, thickness=T)
    if len(shell) > MAX_DENSE_ROWS:
        raise ValueError("dense shell-local operator exceeds the retained cap")
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    ns = len(shell)
    shell_free = np.array([i for i in range(ns)
                           if (i//6) % len(xs) != 0])
    beam_free = np.asarray(beam.context.free)
    free = np.r_[shell_free, ns+beam_free]
    shell_n, beam_n = len(shell_free), len(beam_free)

    drill = _drilling_metric(xs, ys)
    R_shell = physical.copy()
    drill_ids = 6*np.arange(len(xs)*len(ys))+5
    R_shell[np.ix_(drill_ids, drill_ids)] += drill
    R_beam, R_resultant, layout = _beam_metric(beam)
    R_shell_free = R_shell[np.ix_(shell_free, shell_free)]
    R_beam_free = R_beam[np.ix_(beam_free, beam_free)]
    linalg.cholesky((R_shell_free+R_shell_free.T)/2, lower=True)
    linalg.cholesky((R_beam_free+R_beam_free.T)/2, lower=True)
    R_primal = sparse.block_diag((sparse.csc_matrix(R_shell_free),
                                  sparse.csc_matrix(R_beam_free)), format="csc")
    K = sparse.block_diag((
        sparse.csc_matrix(shell[np.ix_(shell_free, shell_free)]),
        beam.tangent.tocsc()[beam_free, :][:, beam_free]), format="csc")
    if monotonic()-started > MAX_WALL_S:
        raise TimeoutError("bounded sparse mixed setup deadline")

    knots = np.linspace(.9, 1., intervals+1)
    patches = [FiniteSurfaceTopFaceLine(
        xs, ys, beam, thickness=T,
        x_interval=(float(low), float(high)))
        for low, high in zip(knots[:-1], knots[1:])]
    masses = np.asarray([patch.basis_integral_m for patch in patches])
    gap = max(float(np.max(np.abs(patch.evaluate_e4_total(
        np.zeros(patch.shell_size),
        beam.context.initial.mechanical)[:, 0]))) for patch in patches)
    if gap > 1e-12:
        raise ArithmeticError("top-face reference line opened")
    C_dense = np.vstack([patch.reference_trace() for patch in patches])[:, free]
    _, scales = _supported_scale(xs, ys, beam)
    scaled_rows = C_dense*scales[free]
    row_norm = np.linalg.norm(scaled_rows, axis=1)
    if np.any(row_norm == 0):
        raise ArithmeticError("physical work row vanished")
    row_sv = linalg.svdvals(scaled_rows/row_norm[:, None])
    rank = int(np.count_nonzero(row_sv > 1e-10*row_sv[0]))
    if rank != len(C_dense):
        raise ArithmeticError("co-refined P0 rows lost physical scaled rank")
    C = sparse.csc_matrix(C_dense)
    R_line, line_info = _line_metric(
        "piecewise_constant", intervals, masses)
    R = sparse.block_diag((R_primal, sparse.csc_matrix(R_line)), format="csc")
    A = sparse.bmat([[K, C.T], [C, None]], format="csc")
    if A.shape[0] <= MAX_DENSE_ROWS and nx == 16:
        raise ArithmeticError("the larger diagnostic no longer needs sparse extension")
    if _peak_rss() > MAX_RSS_BYTES:
        raise MemoryError("sparse diagnostic exceeded registered memory")
    skew = float(spla.norm(A-A.T)/max(1., spla.norm(A)))
    if skew > 1e-9:
        raise ArithmeticError("native mixed tangent is not conservative symmetric")
    d = 1/np.sqrt(R.diagonal())
    D = sparse.diags(d, format="csc")
    A_scaled = D@A@D
    R_scaled = D@R@D
    if monotonic()-started > MAX_WALL_S:
        raise TimeoutError("bounded sparse mixed eigensolve deadline")
    eigenvalues, vectors = spla.eigsh(
        A_scaled, M=R_scaled, sigma=0., which="LM", k=6,
        tol=1e-9, maxiter=1000)
    order = np.argsort(np.abs(eigenvalues))
    eigenvalues, vectors = eigenvalues[order], vectors[:, order]
    y = vectors[:, 0]
    x = d*y
    lam = float(eigenvalues[0])
    residual = A_scaled@y-lam*(R_scaled@y)
    normalized_residual = float(np.linalg.norm(residual)/max(
        np.linalg.norm(A_scaled@y), abs(lam)*np.linalg.norm(R_scaled@y),
        1e-300))
    if normalized_residual > 1e-6:
        raise ArithmeticError("near-zero generalized eigenpair did not converge")
    primal, dual = x[:-len(C_dense)], x[-len(C_dense):]
    left_work = float(dual@(C@primal))
    right_work = float(primal@(C.T@dual))
    if abs(left_work-right_work) > 1e-10*max(1., abs(left_work), abs(right_work)):
        raise ArithmeticError("interface transpose work failed")
    shell_x = x[:shell_n]
    beam_x = x[shell_n:shell_n+beam_n]
    physical_shell_free = physical[np.ix_(shell_free, shell_free)]
    shares = {
        "shell_physical": float(shell_x@physical_shell_free@shell_x),
        "shell_drilling_chart": float(shell_x@(
            R_shell_free-physical_shell_free)@shell_x),
        "beam_kinematic": float(beam_x@(
            R_beam_free-R_resultant[np.ix_(beam_free, beam_free)])@beam_x),
        "beam_complementary": float(beam_x@R_resultant[np.ix_(beam_free, beam_free)]@beam_x),
        "line_dual": float(dual@R_line@dual),
    }
    previous_beta = None
    if nx == 8:
        old = json.loads(PREVIOUS.read_text())
        if (old["shell_rows"], old["beam_rows"]) != (shell_n, beam_n):
            raise ArithmeticError("saved dense cross-check uses another model")
        previous_beta = float(old["cases"]["p0_m4"]["beta_min"])
        if abs(abs(lam)-previous_beta)/previous_beta > 1e-5:
            raise ArithmeticError("sparse generalized eigenvalue disagrees with dense SVD")
    elapsed = monotonic()-started
    peak = _peak_rss()
    if elapsed > MAX_WALL_S:
        raise TimeoutError("sparse mixed diagnostic exceeded registered wall limit")
    if peak > MAX_RSS_BYTES:
        raise MemoryError("sparse mixed diagnostic exceeded registered memory")
    return {
        "classification": "bounded sparse native retained mixed diagnostic, not F03/G0B acceptance",
        "question": "Does co-refined P0 retain a mixed mode away from zero on the actual native tangent?",
        "model": f"C1 Q4 x{nx}/y4 35 mm, B3-12 2 um tangent, P0-{intervals}, fixed left roots",
        "operator": "actual virgin E4 and full native B3 retained indefinite tangents with exact top-face work",
        "norm": "inherited auxiliary physical/chart primal and P0 H^-1/2 dual norm; not an independent canonical norm",
        "previous_dense_beta_x8_p0_m4": previous_beta,
        "previous_dense_sha256": _sha(PREVIOUS) if nx == 8 else None,
        "row_rank": rank,
        "row_count": len(C_dense),
        "row_tail_relative": (row_sv[-6:]/row_sv[0]).tolist(),
        "max_reference_gap_m_rad": gap,
        "mixed_rows": A.shape[0],
        "mixed_nnz": A.nnz,
        "norm_nnz": R.nnz,
        "assembly_relative_skew": skew,
        "nearest_signed_generalized_eigenvalues": eigenvalues.tolist(),
        "beta_min": abs(lam),
        "near_eigenpair_relative_residual": normalized_residual,
        "near_mode_metric_norm_sq": float(x@(R@x)),
        "near_mode_metric_shares": shares,
        "work_left_J": left_work,
        "work_right_J": right_work,
        "weak_constraint_euclidean": float(np.linalg.norm(C@primal)),
        "line_norm": line_info,
        "layout": layout,
        "elapsed_s_not_benchmark": elapsed,
        "peak_rss_bytes": peak,
        "limits": {"max_dense_rows": MAX_DENSE_ROWS,
                   "wall_s": MAX_WALL_S, "rss_bytes": MAX_RSS_BYTES},
        "limitations": ["one beam resolution; no mesh-uniform or ratio-uniform result",
                        "near mode and row rank do not establish physical transfer or absence of locking",
                        "auxiliary drilling/chart and beam norms are diagnostic"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nx", type=int, choices=(8, 16), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate(args.nx)
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
    print(json.dumps({"beta_min": result["beta_min"],
                      "relative_residual": result["near_eigenpair_relative_residual"],
                      "rows": result["mixed_rows"],
                      "nnz": result["mixed_nnz"],
                      "elapsed_s": result["elapsed_s_not_benchmark"],
                      "peak_rss_bytes": result["peak_rss_bytes"]}, sort_keys=True))


if __name__ == "__main__":
    main()
