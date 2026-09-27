"""Compare P0-four/eight on one x16 native primal and two declared norms.

The E4 drilling chart is eliminated exactly from the same tangent. This
remains a bounded development diagnostic, not F03 or G0B acceptance.
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
from scripts.b3_e4_f03_common_trace_p0_metric import _block
from scripts.b3_e4_f03_distributed_surface_finite import FiniteSurfaceTopFaceLine
from scripts.b3_e4_f03_local_footprint_work import skew
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant
from scripts.b3_e4_f03_top_face_common_trace import _raw_rows, _supported_scale


MAX_WALL_S = 120.
MAX_RSS_BYTES = 2*1024**3
WIDTH_M = .1
E_PA = 210e9
TRACTION_COMPLIANCE_M3_PER_N = WIDTH_M**2/(E_PA*T)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _peak_rss() -> int:
    info = psutil.Process().memory_info()
    return int(info.peak_wset if os.name == "nt" else info.rss)


def _physical_traction_l2_metric(patches) -> tuple[np.ndarray, dict]:
    """Exact finite-width L2 traction Gram, in centered work coordinates.

    This is a dimensional sensitivity metric, not a trace-dual inf-sup norm.
    """
    blocks = []
    row_defects = []
    gram_defects = []
    roots = (-1/np.sqrt(3), 1/np.sqrt(3))
    for patch in patches:
        low, high = patch.x_interval
        h, center = high-low, (high+low)/2
        mean = np.array((center-.95, 0., 0.))
        ex2 = (center-.95)**2+h*h/12
        ey2 = WIDTH_M**2/12
        moment = np.diag((ey2, ex2, ex2+ey2))
        cross = -skew(mean)
        raw = TRACTION_COMPLIANCE_M3_PER_N*h/WIDTH_M*np.block([
            [np.eye(3), cross], [cross.T, moment]])
        # Independent two-point Gauss check; B is linear in x and y.
        quadrature = np.zeros((6, 6))
        for xi in roots:
            x = center+h*xi/2
            for eta in roots:
                y = WIDTH_M*eta/2
                arm = np.array((x-.95, y, 0.))
                B = np.column_stack((np.eye(3), -skew(arm)))
                quadrature += (TRACTION_COMPLIANCE_M3_PER_N*h /
                               (4*WIDTH_M))*(B.T@B)
        gram_defects.append(float(linalg.norm(raw-quadrature)/max(
            linalg.norm(raw), 1e-300)))
        transform = _block(patch)
        centered = patch.reference_trace()
        raw_rows = patch.basis_integral_m*_raw_rows(patch, np.eye(3))
        row_defects.append(float(linalg.norm(
            raw_rows-transform@centered)/max(linalg.norm(raw_rows), 1e-300)))
        first = linalg.solve(transform, raw)
        centered_gram = linalg.solve(transform, first.T).T
        linalg.cholesky(centered_gram, lower=True)
        blocks.append(centered_gram)
    if max(row_defects) > 1e-11 or max(gram_defects) > 1e-12:
        raise ArithmeticError("physical traction work or Gram transform failed")
    return linalg.block_diag(*blocks), {
        "law": "t=phi(x)/W [lambda_F+lambda_M cross (x-.95,y,0)]",
        "raw_dual_units": ["N/m"]*3+["N/m^2"]*3,
        "scale_m3_per_N": TRACTION_COMPLIANCE_M3_PER_N,
        "scale_definition": "W^2/(E*t), fixed for all line spaces",
        "max_exact_gram_quadrature_relative_defect": max(gram_defects),
        "max_centered_raw_work_row_relative_defect": max(row_defects),
        "purpose": "independent dimensional L2 traction sensitivity; not H^-1/2, true E4 compliance, or F03 acceptance",
    }


def _dual_shape(dual: np.ndarray, patches, inherited: np.ndarray,
                traction: np.ndarray) -> dict:
    """Compare physical P0 traction shapes without changing the eigenproblem."""
    raw = np.vstack([
        linalg.solve(_block(patch).T, dual[6*i:6*i+6])
        for i, patch in enumerate(patches)
    ])
    equivalent = raw.copy()
    equivalent[:, 3:] *= WIDTH_M
    peak = float(np.max(np.abs(equivalent)))
    shape = equivalent/max(peak, 1e-300)
    roughness = float(np.sqrt(np.sum(np.diff(shape, axis=0)**2)/max(
        np.sum(shape**2), 1e-300)))
    norm_inherited = float(dual@inherited@dual)
    norm_traction = float(dual@traction@dual)
    return {
        "raw_force_and_width_scaled_moment_shape": shape.tolist(),
        "shape_scale_N_per_m": peak,
        "adjacent_shape_roughness": roughness,
        "inherited_dual_norm_sq_J": norm_inherited,
        "traction_dual_norm_sq_J": norm_traction,
        "traction_over_inherited_dual_norm_sq": norm_traction/max(
            norm_inherited, 1e-300),
    }


def _near_mode(A: sparse.csc_matrix, R: sparse.csc_matrix,
               C: np.ndarray, n_shell: int, n_beam: int,
               R_shell_physical: np.ndarray, R_shell_chart: np.ndarray,
               R_beam: np.ndarray, R_resultant: np.ndarray,
               R_line: np.ndarray, patches, inherited_line: np.ndarray,
               traction_line: np.ndarray) -> dict:
    d = 1/np.sqrt(R.diagonal())
    D = sparse.diags(d, format="csc")
    As = D@A@D
    Rs = D@R@D
    eig, vec = spla.eigsh(As, M=Rs, sigma=0., which="LM",
                          k=6, tol=1e-9, maxiter=1000)
    order = np.argsort(np.abs(eig))
    eig, vec = eig[order], vec[:, order]
    lam = float(eig[0])
    y = vec[:, 0]
    x = d*y
    residual = As@y-lam*(Rs@y)
    relative = float(np.linalg.norm(residual)/max(
        np.linalg.norm(As@y), abs(lam)*np.linalg.norm(Rs@y), 1e-300))
    if relative > 1e-6:
        raise ArithmeticError("near-zero fixed-primal eigenpair did not converge")
    shell_x = x[:n_shell]
    beam_x = x[n_shell:n_shell+n_beam]
    dual = x[n_shell+n_beam:]
    primal = x[:n_shell+n_beam]
    work = float(dual@(C@primal))
    work_t = float(primal@(C.T@dual))
    if abs(work-work_t) > 1e-10*max(1., abs(work), abs(work_t)):
        raise ArithmeticError("fixed-primal interface work transpose failed")
    shares = {
        "shell_physical": float(shell_x@R_shell_physical@shell_x),
        "shell_chart_induced": float(shell_x@R_shell_chart@shell_x),
        "beam_kinematic": float(beam_x@(R_beam-R_resultant)@beam_x),
        "beam_complementary": float(beam_x@R_resultant@beam_x),
        "line_dual": float(dual@R_line@dual),
    }
    return {
        "beta_min": abs(lam),
        "nearest_signed_eigenvalues": eig.tolist(),
        "relative_eigen_residual": relative,
        "metric_norm_sq": float(x@(R@x)),
        "metric_shares": shares,
        "work_J": work,
        "work_transpose_J": work_t,
        "constraint_euclidean": float(np.linalg.norm(C@primal)),
        "dual_shape": _dual_shape(dual, patches, inherited_line,
                                  traction_line),
    }


def evaluate(beam_half_cells: int) -> dict:
    started = monotonic()
    xs, ys = local_grid(16, transverse_cells=4)
    shell, physical = raw_e4_tangent(xs, ys, thickness=T)
    if len(shell) > 1900:
        raise ValueError("dense shell-local operator exceeded existing cap")
    beam = build(beam_half_cells, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    ns = len(shell)
    shell_free = np.array([i for i in range(ns)
                           if (i//6) % len(xs) != 0])
    beam_free = np.asarray(beam.context.free)
    free, coordinate_scale = _supported_scale(xs, ys, beam)
    if not np.array_equal(free[:len(shell_free)], shell_free):
        raise ArithmeticError("supported physical shell layout changed")
    n_beam = len(beam_free)
    physical_shell = np.flatnonzero(shell_free % 6 != 5)
    drill_shell = np.flatnonzero(shell_free % 6 == 5)
    n_phys = len(physical_shell)
    Ks = shell[np.ix_(shell_free, shell_free)]
    Kpp = Ks[np.ix_(physical_shell, physical_shell)]
    Kpd = Ks[np.ix_(physical_shell, drill_shell)]
    Kdd = Ks[np.ix_(drill_shell, drill_shell)]
    if linalg.eigvalsh(Kdd, subset_by_index=[0, 0])[0] <= 0:
        raise ArithmeticError("supported E4 drill block is not positive definite")
    factor = linalg.cho_factor(Kdd, lower=True)
    lift = linalg.cho_solve(factor, Kpd.T)
    if linalg.norm(Kdd@lift-Kpd.T)/max(linalg.norm(Kpd.T), 1e-300) > 1e-9:
        raise ArithmeticError("same-tangent chart lift failed")
    Kcond = Kpp-Kpd@lift
    if linalg.norm(Kcond-Kcond.T)/max(linalg.norm(Kcond), 1e-300) > 1e-9:
        raise ArithmeticError("same-tangent Schur symmetry failed")
    Kbeam = beam.tangent.tocsc()[beam_free, :][:, beam_free]
    K = sparse.block_diag((sparse.csc_matrix(Kcond), Kbeam), format="csc")
    R_shell = physical.copy()
    drill_dofs = 6*np.arange(len(xs)*len(ys))+5
    R_shell[np.ix_(drill_dofs, drill_dofs)] += _drilling_metric(xs, ys)
    R_free = R_shell[np.ix_(shell_free, shell_free)]
    Rpp = R_free[np.ix_(physical_shell, physical_shell)]
    Rpd = R_free[np.ix_(physical_shell, drill_shell)]
    Rdd = R_free[np.ix_(drill_shell, drill_shell)]
    # Pull back the *whole* accepted diagnostic norm along d=-lift*p.
    Rchart = -Rpd@lift-lift.T@Rpd.T+lift.T@Rdd@lift
    Rpull = Rpp+Rchart
    if linalg.norm(Rpull-Rpull.T)/max(linalg.norm(Rpull), 1e-300) > 1e-9:
        raise ArithmeticError("pulled chart metric is not symmetric")
    linalg.cholesky(Rpp, lower=True)
    linalg.cholesky(Rpull, lower=True)
    Rbeam, Rresult, layout = _beam_metric(beam)
    Rb = Rbeam[np.ix_(beam_free, beam_free)]
    Rres = Rresult[np.ix_(beam_free, beam_free)]
    if monotonic()-started > MAX_WALL_S:
        raise TimeoutError("fixed-primal assembly deadline")
    reports = {}
    for intervals in (4, 8):
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
            raise ArithmeticError("reference top-face line opened")
        Cfull = np.vstack([patch.reference_trace() for patch in patches])[:, free]
        if np.max(np.abs(Cfull[:, drill_shell])) > 1e-13:
            raise ArithmeticError("top-face line unexpectedly uses E4 drill")
        chosen = np.r_[physical_shell, len(shell_free)+np.arange(n_beam)]
        C = Cfull[:, chosen]
        scaled = C*coordinate_scale[free[chosen]]
        norm = np.linalg.norm(scaled, axis=1)
        sv = linalg.svdvals(scaled/norm[:, None])
        rank = int(np.count_nonzero(sv > 1e-10*sv[0]))
        if rank != len(C):
            raise ArithmeticError("fixed-primal P0 row space lost rank")
        Rline, line_info = _line_metric(
            "piecewise_constant", intervals, masses)
        Rtraction, traction_info = _physical_traction_l2_metric(patches)
        smooth_raw = np.array((1., 0., 0., 0., 0., 0.))
        smooth_dual = np.concatenate([
            _block(patch).T@smooth_raw for patch in patches])
        smooth_control = {
            "raw_force_N_per_m": smooth_raw.tolist(),
            "inherited_dual_norm_sq_J": float(smooth_dual@Rline@smooth_dual),
            "traction_dual_norm_sq_J": float(smooth_dual@Rtraction@smooth_dual),
        }
        Csp = sparse.csc_matrix(C)
        A = sparse.bmat([[K, Csp.T], [Csp, None]], format="csc")
        # A is sparse; only the shell-local and Schur matrices are dense.
        if Kcond.shape[0] > 1900:
            raise ValueError("dense Schur diagnostic exceeds the row cap")
        cases = {}
        for variant, shell_norm, chart_part in (
                ("restricted_physical", Rpp, np.zeros_like(Rpp)),
                ("pulled_full", Rpull, Rchart),
                ("physical_traction_L2", Rpp, np.zeros_like(Rpp))):
            selected_line = Rtraction if variant == "physical_traction_L2" else Rline
            R = sparse.block_diag((sparse.csc_matrix(shell_norm),
                                   sparse.csc_matrix(Rb),
                                   sparse.csc_matrix(selected_line)), format="csc")
            cases[variant] = _near_mode(
                A, R, C, n_phys, n_beam, Rpp, chart_part,
                Rb, Rres, selected_line, patches, Rline, Rtraction)
            if monotonic()-started > MAX_WALL_S or _peak_rss() > MAX_RSS_BYTES:
                raise RuntimeError("fixed-primal spaces exceeded resource limits")
        reports[f"p0_m{intervals}"] = {
            "row_rank": rank,
            "row_count": len(C),
            "row_tail_relative": (sv[-6:]/sv[0]).tolist(),
            "reference_gap_m_rad": gap,
            "line_norm": line_info,
            "traction_norm": traction_info,
            "smooth_traction_control": smooth_control,
            "mixed_rows": A.shape[0],
            "mixed_nnz": A.nnz,
            "norm_cases": cases,
        }
    elapsed = monotonic()-started
    return {
        "classification": "same-primal exact-Schur P0 and norm sensitivity diagnostic; not F03/G0B acceptance",
        "question": "Does the P0-four/eight traction-norm change expose an oscillatory physical traction mode, or chiefly a norm conversion?",
        "model": (f"C1 Q4 x16/y4 35 mm, B3-{beam_half_cells} "
                  "2 um tangent, fixed left roots"),
        "norms": {"restricted_physical": "inherited physical shell+beam+P0 dual metric, excluding eliminated chart norm",
                  "pulled_full": "same metric with exact full shell chart norm pulled along static Schur lift",
                  "physical_traction_L2": "restricted physical primal metric plus independent finite-width L2 traction Gram; sensitivity only"},
        "shell_physical_dofs": n_phys,
        "shell_drill_dofs_eliminated": len(drill_shell),
        "beam_free_dofs": n_beam,
        "beam_half_cells": beam_half_cells,
        "pulled_chart_over_restricted_shell_norm_frobenius": float(
            linalg.norm(Rchart)/max(linalg.norm(Rpp), 1e-300)),
        "layout": layout,
        "cases": reports,
        "elapsed_s_not_benchmark": elapsed,
        "peak_rss_bytes": _peak_rss(),
        "limits": {"max_dense_rows": 1900, "wall_s": MAX_WALL_S,
                   "rss_bytes": MAX_RSS_BYTES},
        "limitations": ["one fixed shell/beam model, not mesh-uniform stability",
                        "inherited dual norm is a diagnostic, not independently qualified",
                        "near mode alone does not measure locking or physical accuracy"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--beam-half-cells", type=int, choices=(12, 24),
                        required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate(args.beam_half_cells)
    sources = [Path(__file__),
               Path("scripts/b3_e4_f03_c1_native_mixed_metric.py"),
               Path("scripts/b3_e4_f03_common_trace_p0_metric.py"),
               Path("scripts/b3_e4_f03_distributed_surface_finite.py"),
               Path("scripts/b3_e4_f03_local_footprint_work.py"),
               Path("scripts/b3_e4_f03_top_face_common_trace.py"),
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
    print(json.dumps({key: {name: value["beta_min"] for name, value in
                            case["norm_cases"].items()}
                      for key, case in result["cases"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
