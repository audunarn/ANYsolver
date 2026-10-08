"""Exact shell-drill Schur diagnostic for a native top-face mixed problem.

Only an auxiliary chart coordinate is eliminated from the *same* tangent.
This is not a production formulation or G0 qualification result.
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
        raise ValueError("dense shell operator exceeds the existing cap")
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    ns = len(shell)
    shell_free = np.array([i for i in range(ns)
                           if (i//6) % len(xs) != 0])
    beam_free = np.asarray(beam.context.free)
    free, column_scale = _supported_scale(xs, ys, beam)
    if not np.array_equal(free[:len(shell_free)], shell_free):
        raise ArithmeticError("supported shell layout changed")
    n_shell, n_beam = len(shell_free), len(beam_free)

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
    C_full = np.vstack([patch.reference_trace() for patch in patches])[:, free]
    physical_shell = np.flatnonzero(shell_free % 6 != 5)
    drill_shell = np.flatnonzero(shell_free % 6 == 5)
    if np.max(np.abs(C_full[:, drill_shell])) > 1e-13:
        raise ArithmeticError("connection rows couple directly to shell drill")
    chosen = np.r_[physical_shell, n_shell+np.arange(n_beam)]
    C = C_full[:, chosen]
    row_norm = np.linalg.norm(C*column_scale[free[chosen]], axis=1)
    if np.any(row_norm == 0):
        raise ArithmeticError("work row vanished on physical quotient")
    row_sv = linalg.svdvals((C*column_scale[free[chosen]])/row_norm[:, None])
    row_rank = int(np.count_nonzero(row_sv > 1e-10*row_sv[0]))
    if row_rank != len(C):
        raise ArithmeticError("co-refined physical interface rows are dependent")

    Ks = shell[np.ix_(shell_free, shell_free)]
    Kpp = Ks[np.ix_(physical_shell, physical_shell)]
    Kpd = Ks[np.ix_(physical_shell, drill_shell)]
    Kdd = Ks[np.ix_(drill_shell, drill_shell)]
    drill_skew = float(linalg.norm(Kdd-Kdd.T)/max(linalg.norm(Kdd), 1e-300))
    if drill_skew > 1e-9:
        raise ArithmeticError("shell drilling block is not conservative symmetric")
    drill_eigs = linalg.eigvalsh(Kdd, check_finite=True)
    if drill_eigs[0] <= 0:
        raise ArithmeticError("shell drilling block is not positive definite")
    factor = linalg.cho_factor(Kdd, lower=True, check_finite=True)
    lift = linalg.cho_solve(factor, Kpd.T, check_finite=True)
    drill_elimination_residual = float(linalg.norm(Kdd@lift-Kpd.T)/max(
        linalg.norm(Kpd.T), 1e-300))
    if drill_elimination_residual > 1e-9:
        raise ArithmeticError("drill chart elimination did not solve its block")
    Kcond = Kpp-Kpd@lift
    condensed_skew = float(linalg.norm(Kcond-Kcond.T)/max(
        linalg.norm(Kcond), 1e-300))
    if condensed_skew > 1e-9:
        raise ArithmeticError("exact Schur tangent is not conservative symmetric")
    Kbeam = beam.tangent.tocsc()[beam_free, :][:, beam_free]
    K = sparse.block_diag((sparse.csc_matrix(Kcond), Kbeam), format="csc")
    R_shell = physical.copy()
    drill_dofs = 6*np.arange(len(xs)*len(ys))+5
    R_shell[np.ix_(drill_dofs, drill_dofs)] += _drilling_metric(xs, ys)
    Rs = R_shell[np.ix_(shell_free[physical_shell],
                        shell_free[physical_shell])]
    R_beam, R_resultant, layout = _beam_metric(beam)
    Rb = R_beam[np.ix_(beam_free, beam_free)]
    Rline, line_info = _line_metric("piecewise_constant", intervals, masses)
    R = sparse.block_diag((sparse.csc_matrix(Rs),
                           sparse.csc_matrix(Rb),
                           sparse.csc_matrix(Rline)), format="csc")
    C_sparse = sparse.csc_matrix(C)
    A = sparse.bmat([[K, C_sparse.T], [C_sparse, None]], format="csc")
    if A.shape[0] > MAX_DENSE_ROWS:
        raise ValueError("diagnostic physical quotient exceeds dense row cap")
    if monotonic()-started > MAX_WALL_S or _peak_rss() > MAX_RSS_BYTES:
        raise RuntimeError("bounded Schur setup exceeded resource limits")
    d = 1/np.sqrt(R.diagonal())
    D = sparse.diags(d, format="csc")
    As = D@A@D
    Rn = D@R@D
    eigenvalues, vectors = spla.eigsh(
        As, M=Rn, sigma=0., which="LM", k=6, tol=1e-9, maxiter=1000)
    order = np.argsort(np.abs(eigenvalues))
    eigenvalues, vectors = eigenvalues[order], vectors[:, order]
    lam = float(eigenvalues[0])
    y = vectors[:, 0]
    x = d*y
    residual = As@y-lam*(Rn@y)
    residual_relative = float(np.linalg.norm(residual)/max(
        np.linalg.norm(As@y), abs(lam)*np.linalg.norm(Rn@y), 1e-300))
    if residual_relative > 1e-6:
        raise ArithmeticError("physical quotient near mode did not converge")
    n_phys = len(physical_shell)
    n_primal = n_phys+n_beam
    ps = x[:n_phys]
    pb = x[n_phys:n_primal]
    dual = x[n_primal:]
    drill_recovered = -lift@ps
    full_shell = np.zeros(n_shell)
    full_shell[physical_shell] = ps
    full_shell[drill_shell] = drill_recovered
    full_primal = np.r_[full_shell, pb]
    reduced_response = A@x
    full_drill_residual = Ks[np.ix_(drill_shell, np.arange(n_shell))]@full_shell
    full_physical_response = (
        Ks[np.ix_(physical_shell, np.arange(n_shell))]@full_shell +
        C_full[:, physical_shell].T@dual)
    response_discrepancy = float(np.linalg.norm(
        full_physical_response-reduced_response[:n_phys])/max(
            np.linalg.norm(reduced_response[:n_phys]), 1e-300))
    if response_discrepancy > 1e-8:
        raise ArithmeticError("exact Schur physical response mismatch")
    work_left = float(dual@(C@x[:n_primal]))
    work_right = float(x[:n_primal]@(C.T@dual))
    if abs(work_left-work_right) > 1e-10*max(1., abs(work_left), abs(work_right)):
        raise ArithmeticError("physical interface transpose work failed")
    Rresult = R_resultant[np.ix_(beam_free, beam_free)]
    shares = {
        "shell_physical": float(ps@Rs@ps),
        "beam_kinematic": float(pb@(Rb-Rresult)@pb),
        "beam_complementary": float(pb@Rresult@pb),
        "line_dual": float(dual@Rline@dual),
    }
    elapsed = monotonic()-started
    peak = _peak_rss()
    if elapsed > MAX_WALL_S or peak > MAX_RSS_BYTES:
        raise RuntimeError("bounded Schur diagnostic exceeded resource limits")
    return {
        "classification": "bounded exact shell-drill Schur physical mixed diagnostic, not F03/G0B acceptance",
        "question": "After exact chart elimination, does a physical/interface mixed mode approach zero under co-refinement?",
        "model": f"C1 Q4 x{nx}/y4 35 mm, B3-12 2 um tangent, P0-{intervals}, fixed left roots",
        "shell_drill_dofs": len(drill_shell),
        "shell_physical_dofs": n_phys,
        "native_beam_free_dofs": n_beam,
        "line_rows": len(C),
        "line_scaled_rank": row_rank,
        "reference_gap_m_rad": gap,
        "drill_block_min_eigenvalue_raw": float(drill_eigs[0]),
        "drill_block_condition_raw": float(drill_eigs[-1]/drill_eigs[0]),
        "drill_block_relative_skew": drill_skew,
        "schur_relative_skew": condensed_skew,
        "drill_lift_relative_residual": drill_elimination_residual,
        "full_drill_equilibrium_residual": float(np.linalg.norm(full_drill_residual)),
        "physical_response_relative_discrepancy": response_discrepancy,
        "schur_vs_uneliminated_physical_K_relative": float(linalg.norm(
            Kcond-Kpp)/max(linalg.norm(Kpp), 1e-300)),
        "mixed_rows": A.shape[0],
        "mixed_nnz": A.nnz,
        "beta_min_physical_quotient": abs(lam),
        "nearest_signed_generalized_eigenvalues": eigenvalues.tolist(),
        "near_eigenpair_relative_residual": residual_relative,
        "near_mode_metric_norm_sq": float(x@(R@x)),
        "near_mode_metric_shares": shares,
        "work_left_J": work_left,
        "work_right_J": work_right,
        "weak_constraint_euclidean": float(np.linalg.norm(C_full@full_primal)),
        "line_norm": line_info,
        "layout": layout,
        "elapsed_s_not_benchmark": elapsed,
        "peak_rss_bytes": peak,
        "limits": {"max_dense_rows": MAX_DENSE_ROWS, "wall_s": MAX_WALL_S,
                   "rss_bytes": MAX_RSS_BYTES},
        "limitations": ["reference-state diagnostic physical quotient, not a nonlinear formulation",
                        "inherited auxiliary physical/beam/dual norm is not canonical or mesh-uniform",
                        "full production tangent and native beam retained variables remain unchanged",
                        "no physical-transfer, locking or registered ratio claim"],
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
    print(json.dumps({"beta": result["beta_min_physical_quotient"],
                      "residual": result["near_eigenpair_relative_residual"],
                      "shares": result["near_mode_metric_shares"],
                      "rows": result["mixed_rows"],
                      "elapsed_s": result["elapsed_s_not_benchmark"],
                      "peak_rss_bytes": result["peak_rss_bytes"]}, sort_keys=True))


if __name__ == "__main__":
    main()
