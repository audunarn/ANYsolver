"""Bounded native KKT diagnostic after exact elimination of E4 drilling.

The product tangent and the exact line rows are unchanged. This diagnostic
removes only unconstrained numerical drilling coordinates from the metric
problem; it is not production condensation or an interface inf-sup proof.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from time import monotonic

import numpy as np
import scipy
from scipy import linalg
import threadpoolctl
from threadpoolctl import threadpool_info, threadpool_limits

from scripts import b3_e4_f03_c1_native_mixed_metric as prior
from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_distributed_surface_finite import c1_hybrid_line_space
from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts.b3_e4_f03_material_line_position import MaterialLinePosition
from scripts.b3_e4_f03_material_line_space_screen import _rows as material_line_rows
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def _relative(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a-b)/max(1., np.linalg.norm(b)))


def _p0_l2_line_metric(masses: np.ndarray) -> tuple[np.ndarray, dict]:
    """Exact P0 physical-density L2 comparator with the frozen force scale."""
    if masses.ndim != 1 or not np.all(np.isfinite(masses)) or np.any(masses <= 0.):
        raise ValueError("finite positive P0 basis lengths required")
    scales = np.tile(np.r_[np.ones(3), np.full(3, 1/prior.L_LINE)],
                     len(masses))
    diagonal = scales**2/(np.repeat(masses, 6)*prior.K_REF)
    return np.diag(diagonal), {
        "kind": "exact_P0_L2_physical_density_sensitivity",
        "basis_integrals_m": masses.tolist(),
        "physical_density_units": ["N/m"]*3+["Nm/m"]*3,
        "moment_to_force_equivalent_length_m": prior.L_LINE,
        "analytic_L2_gram_diagonal_m": masses.tolist(),
        "not_registered_acceptance_norm": True,
    }


def _material_line_space(xs, ys, beam, *, kind: str, intervals: int):
    """Mean-gap rows for the declared top material line, with fixed cuts."""
    knots = np.linspace(0., 1., intervals+1)
    if any(not np.any(np.isclose(xs, .9+.1*k, rtol=0., atol=1e-12))
           for k in knots):
        raise ValueError("material-line multiplier knots must match shell cuts")
    line = MaterialLinePosition(xs, ys, beam)
    return material_line_rows(line, LineMultiplierSpace(kind, tuple(knots)))


def evaluate(shell_cells: int = 8, *, weak_mode_only: bool = False,
             weak_mode_line_norm: str = "hminus_half",
             line_law: str = "hybrid", beam_half_cells: int = 12,
             matched_p0_only: bool = False,
             trace_only: bool = False) -> dict:
    if shell_cells not in ((2, 4, 8) if matched_p0_only else (4, 8, 16)):
        raise ValueError("bounded C1 drill-quotient shell level required")
    if beam_half_cells not in (12, 14, 18):
        raise ValueError("bounded native beam half-cell count required")
    if not (matched_p0_only or trace_only) and beam_half_cells != 12:
        raise ValueError("beam refinement is only admitted for bounded matched diagnostics")
    if trace_only and ((shell_cells, beam_half_cells) not in ((8, 12), (16, 14)) or
                       line_law != "material_line" or weak_mode_only or
                       matched_p0_only or weak_mode_line_norm != "hminus_half"):
        raise ValueError("bounded fixed-4:1 material-line trace diagnostic required")
    if matched_p0_only and (line_law != "material_line" or weak_mode_only or
                            weak_mode_line_norm != "hminus_half"):
        raise ValueError("matched P0 diagnostic requires the material-line law and standard norm")
    if weak_mode_only and shell_cells != 16:
        raise ValueError("bounded P0 weak-mode inspection requires x16")
    if (weak_mode_line_norm not in ("hminus_half", "p0_l2") or
            (weak_mode_line_norm != "hminus_half" and not weak_mode_only)):
        raise ValueError("alternate line norm is only a selected P0 weak-mode sensitivity")
    if line_law not in ("hybrid", "material_line"):
        raise ValueError("bounded line law required")
    if line_law == "material_line" and weak_mode_only:
        raise ValueError("hybrid weak-mode reconstruction does not describe the material line")
    started = monotonic()
    deadline = started+120.
    xs, ys = local_grid(shell_cells, transverse_cells=4)
    shell, physical = raw_e4_tangent(xs, ys, thickness=prior.T)
    beam = build(beam_half_cells, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    ns = len(shell)
    shell_free = np.array([i for i in range(ns) if (i//6) % len(xs) != 0])
    shell_drill = shell_free[shell_free % 6 == 5]
    shell_physical = shell_free[shell_free % 6 != 5]
    beam_free = np.asarray(beam.context.free, dtype=int)
    shell_pp = shell[np.ix_(shell_physical, shell_physical)]
    shell_pd = shell[np.ix_(shell_physical, shell_drill)]
    shell_dp = shell[np.ix_(shell_drill, shell_physical)]
    shell_dd = shell[np.ix_(shell_drill, shell_drill)]
    if (_relative(shell_dd, shell_dd.T) > 1e-10 or
            _relative(shell_pd, shell_dp.T) > 1e-10):
        raise ArithmeticError("drilling partition is not conservative")
    linalg.cholesky(shell_dd, lower=True, check_finite=True)
    lift = linalg.solve(shell_dd, shell_dp, assume_a="pos", check_finite=True)
    quotient = shell_pp-shell_pd@lift
    # A deterministic physical field verifies both the eliminated drill
    # equilibrium and the reconstructed physical action of the original K.
    test = np.sin(np.arange(len(shell_physical))*.173)
    companion = -lift@test
    full = np.zeros(ns)
    full[shell_physical], full[shell_drill] = test, companion
    drilling_residual = float(np.linalg.norm(
        shell_dd@companion+shell_dp@test) /
        max(1., np.linalg.norm(shell_dp@test)))
    schur_residual = _relative((shell@full)[shell_physical], quotient@test)
    if max(drilling_residual, schur_residual) > 1e-8:
        raise ArithmeticError("actual shell tangent Schur reconstruction failed")
    if monotonic() > deadline:
        raise TimeoutError("bounded drill quotient construction deadline")

    r_shell = physical[np.ix_(shell_physical, shell_physical)]
    linalg.cholesky((r_shell+r_shell.T)/2, lower=True, check_finite=True)
    r_beam, r_resultant, layout = prior._beam_metric(beam)
    r_beam = r_beam[np.ix_(beam_free, beam_free)]
    r_resultant = r_resultant[np.ix_(beam_free, beam_free)]
    k_primal = None if trace_only else linalg.block_diag(
        quotient, beam.tangent.toarray()[np.ix_(beam_free, beam_free)])
    r_primal = linalg.block_diag(r_shell, r_beam)
    free_physical = np.r_[shell_physical, ns+beam_free]
    free_full = np.r_[shell_free, ns+beam_free]
    cases = {}
    tested_intervals = ((shell_cells//2,) if trace_only else
                        (shell_cells,) if (weak_mode_only or matched_p0_only) else
                        (shell_cells//2, shell_cells))
    tested_kinds = (("piecewise_constant",) if (weak_mode_only or matched_p0_only)
                    else prior.KINDS)
    for intervals in tested_intervals:
        for kind in tested_kinds:
            if monotonic() > deadline:
                raise TimeoutError("bounded drill quotient mixed deadline")
            if line_law == "hybrid":
                rows, masses, patches = c1_hybrid_line_space(
                    xs, ys, beam, kind=kind, intervals=intervals)
            else:
                rows, masses = _material_line_space(
                    xs, ys, beam, kind=kind, intervals=intervals)
                patches = ()
            cd = rows[:, shell_drill]
            drill_column_max = float(np.max(np.abs(cd)))
            if drill_column_max > 1e-12:
                raise ArithmeticError("line acts on numerical drilling coordinate")
            c = rows[:, free_physical]
            old = rows[:, free_full]
            if _relative(c, old[:, np.r_[
                    np.flatnonzero(shell_free % 6 != 5),
                    len(shell_free)+np.arange(len(beam_free))]]) > 1e-12:
                raise ArithmeticError("physical line-column extraction changed")
            r_line, line_info = (
                _p0_l2_line_metric(masses)
                if weak_mode_line_norm == "p0_l2" else
                prior._line_metric(kind, intervals, masses))
            chol_line = linalg.cholesky(r_line, lower=True)
            chol_primal = linalg.cholesky(r_primal, lower=True)
            scaled_c = linalg.solve_triangular(chol_line, c, lower=True)
            scaled_c = linalg.solve_triangular(
                chol_primal, scaled_c.T, lower=True).T
            row_singular = linalg.svdvals(scaled_c)
            rank_tolerance = max(scaled_c.shape)*np.finfo(float).eps*row_singular[0]
            rank = int(np.sum(row_singular > rank_tolerance))
            if rank != len(c):
                if line_law == "hybrid":
                    raise ArithmeticError("quotient line row rank lost")
                cases[f"{kind}_m{intervals}"] = {
                    "status": "ROW_RANK_DEFICIENT",
                    "constraint_rows": len(c),
                    "normalized_constraint_rank": rank,
                    "rank_tolerance": float(rank_tolerance),
                    "smallest_scaled_constraint_singular": float(row_singular[-1]),
                    "line_norm": line_info,
                    "drill_constraint_column_max": drill_column_max,
                }
                continue
            if trace_only:
                probe_primal = np.sin(np.arange(c.shape[1])*.173)
                probe_dual = np.cos(np.arange(c.shape[0])*.219)
                work_left = float(probe_dual@(c@probe_primal))
                work_right = float(probe_primal@(c.T@probe_dual))
                if abs(work_left-work_right) > 1e-10*max(
                        1., abs(work_left), abs(work_right)):
                    raise ArithmeticError("trace transpose work changed")
                cases[f"{kind}_m{intervals}"] = {
                    "status": "TRACE_NORM_DIAGNOSTIC_COMPUTED",
                    "constraint_rows": len(c),
                    "normalized_constraint_rank": rank,
                    "trace_singular_min": float(row_singular[-1]),
                    "trace_singular_max": float(row_singular[0]),
                    "trace_singular_condition": float(row_singular[0]/row_singular[-1]),
                    "rank_tolerance": float(rank_tolerance),
                    "line_norm": line_info,
                    "drill_constraint_column_max": drill_column_max,
                    "transpose_work_discrepancy_J": abs(work_left-work_right),
                    "scope": "single-grid auxiliary-norm trace map, not full KKT or uniform inf-sup",
                }
                if monotonic() > deadline:
                    raise TimeoutError("bounded native trace diagnostic deadline")
                continue
            a = np.block([[k_primal, c.T],
                          [c, np.zeros((len(c), len(c)))]])
            r = linalg.block_diag(r_primal, r_line)
            shell_n, beam_n = len(shell_physical), len(beam_free)
            pieces = {"C": c, "blocks": [
                ("shell_physical", slice(0, shell_n), r_shell),
                ("beam_kinematic", slice(shell_n, shell_n+beam_n),
                 r_beam-r_resultant),
                ("beam_complementary", slice(shell_n, shell_n+beam_n),
                 r_resultant),
                ("line_dual", slice(shell_n+beam_n, None), r_line)]}
            report = prior._case(a, r, pieces, len(c), deadline,
                                 include_weak_vector=weak_mode_only)
            if weak_mode_only:
                vector = np.asarray(report.pop("weak_vector"))
                primal = vector[:-len(c)]
                material_dual = vector[-len(c):].reshape(-1, 6)
                shell_vector = np.zeros(ns)
                shell_vector[shell_physical] = primal[:shell_n]
                shell_vector[shell_drill] = -lift@primal[:shell_n]
                beam_vector = np.zeros(beam.context.count)
                beam_vector[beam_free] = primal[shell_n:shell_n+beam_n]
                # The singular vector is R-normalized and sign-arbitrary.
                # Its dual entries are integrated material actions, not
                # display-ready spatial point wrenches.
                report["weak_mode"] = {
                    "normalization": "x.T R x = 1; sign arbitrary",
                    "shell_full_coordinates": shell_vector.tolist(),
                    "beam_full_native_coordinates": beam_vector.tolist(),
                    "line_material_actions_N_Nm": material_dual.tolist(),
                    "line_material_densities_N_per_m_Nm_per_m":
                        (material_dual/masses[:, None]).tolist(),
                    "line_basis_support_intervals_m": [
                        [.9+.1*i/intervals, .9+.1*(i+1)/intervals]
                        for i in range(intervals)],
                    "basis_support_check": all(
                        low < point.x < high
                        for patch, (low, high) in zip(
                            patches, ([.9+.1*i/intervals,
                                       .9+.1*(i+1)/intervals]
                                      for i in range(intervals)))
                        for point in patch.points),
                    "weak_constraint_gap_by_basis":
                        (c@primal).reshape(-1, 6).tolist(),
                    "physical_shell_and_beam_coordinate_reaction":
                        (-c.T@vector[-len(c):]).tolist(),
                    "sampled_unprojected_gaps": [
                        p.linearized_continuous_gap_statistics(
                            shell_vector, beam_vector) for p in patches],
                    "scope": ("reference-linearized weak KKT mode in exact "
                              "drill quotient; coordinate reactions include "
                              "native retained B3 variables, not recovered "
                              "spatial point tractions"),
                }
            report["drill_constraint_column_max"] = drill_column_max
            report["normalized_constraint_rank"] = rank
            report["line_norm"] = line_info
            cases[f"{kind}_m{intervals}"] = report
    sources = [Path(__file__), Path(prior.__file__),
        Path("scripts/_b3_e4_f03_native_fixture.py"),
        Path("scripts/b3_e4_f03_distributed_surface_finite.py"),
        Path("scripts/b3_e4_f03_plate_patch_work.py"),
        Path("scripts/b3_e4_f03_square_section_control.py"),
        Path("scripts/_b3_e4_f03_p0_dual_norm.py"),
        Path("scripts/_b3_e4_f03_p1_dual_norm.py"),
        Path("scripts/_b3_e4_f03_dual_linear_norm.py"),
        Path("scripts/b3_e4_f03_material_line_position.py"),
        Path("scripts/b3_e4_f03_material_line_space_screen.py"),
        Path("scripts/_b3_e4_f03_weak_line_candidate.py")]
    return {
        "classification": ("bounded drill-quotient native trace diagnostic, not G0B acceptance"
                           if trace_only else
                           "bounded drill-quotient native retained KKT diagnostic, not G0B acceptance"),
        "line_law": line_law,
        "trace_only": trace_only,
        "question": ("Does the actual retained, drill-quotiented material-line "
                     "P0 mixed KKT remain supported over three matched 1:1 "
                     "refinement levels?" if matched_p0_only else
                     "How do three line spaces compare on the same fixed-4:1 "
                     "auxiliary-norm trace map?" if trace_only else
                     "Do the declared material-line P0/P1/dual spaces retain "
                     "supported rows and normed mixed-system behavior as their "
                     "interface resolution grows?" if line_law == "material_line"
                     else "Does the selected P0 high-frequency line mode persist under "
                     "the exact physical-density L2 sensitivity norm?"
                     if weak_mode_line_norm == "p0_l2" else
                     "Was the prior smallest native KKT mode only a numerical drilling metric mode, and do line-coupled modes decline under growing rows?"),
        "model": (f"C1 Q4 x{shell_cells}/y4 35 mm shell, native B3-{beam_half_cells}, " +
                  ("material-line " if line_law == "material_line" else "hybrid ") +
                  (f"P0 m{shell_cells} weak-mode inspection" if weak_mode_only
                   else f"P0 m{shell_cells} matched 1:1 level" if matched_p0_only
                   else f"P0/P1/dual m{shell_cells//2} fixed-primal trace norm"
                   if trace_only
                   else f"P0/P1/dual m{shell_cells//2}/m{shell_cells}")),
        "beam_half_cells": beam_half_cells,
        "matched_p0_only": matched_p0_only,
        "operator": "actual E4 tangent with exact free-drilling Schur complement; actual native retained B3 tangent and declared line-law rows",
        "metric": ("physical E4 energy on non-drilling coordinates; previous "
                   "native B3 norm; exact P0 physical-density L2 line comparator"
                   if weak_mode_line_norm == "p0_l2" else
                   "physical E4 energy on non-drilling coordinates; previous native B3 and basis-specific line norms"),
        "shell_physical_rows": len(shell_physical),
        "shell_drilling_rows_eliminated": len(shell_drill),
        "beam_rows": len(beam_free),
        "maximum_rows": prior.MAX_ROWS,
        "drilling_equilibrium_relative_residual": drilling_residual,
        "schur_action_relative_residual": schur_residual,
        "beam_layout": layout,
        "cases": cases,
        "elapsed_s": monotonic()-started,
        "limits": ["exact bounded diagnostic elimination, not a production assembler or changed mechanics",
                   "physical-coordinate restriction is not a full continuum quotient proof",
                   ("one-grid trace singular values, not mixed KKT or mesh-uniform stability"
                    if trace_only else
                    "one R-normalized P0 weak mode, not a locking or stability verdict"
                    if weak_mode_only else
                    "one matched 1:1 refinement series, not registered ratio/refinement acceptance"
                    if matched_p0_only else
                    "two interface resolutions on one shell grid, not registered ratio/refinement acceptance"),
                   "no multiplier selection or physical connection accuracy claim"],
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "provenance": {
            "source_git": subprocess.check_output(["git", "rev-parse", "HEAD"],
                text=True).strip(),
            "source_sha256": {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sources},
            "python": sys.version.split()[0], "executable": sys.executable,
            "numpy": np.__version__, "scipy": scipy.__version__,
            "threadpoolctl": threadpoolctl.__version__,
            "effective_threadpools": threadpool_info(),
            "env": {key: os.environ.get(key) for key in
                    ("PYTHONPATH", "NUMBA_DISABLE_JIT",
                     "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS")},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--shell-cells", type=int, choices=(2, 4, 8, 16), default=8)
    parser.add_argument("--beam-half-cells", type=int, choices=(12, 14, 18), default=12)
    parser.add_argument("--matched-p0-only", action="store_true")
    parser.add_argument("--trace-only", action="store_true")
    parser.add_argument("--weak-mode-only", action="store_true")
    parser.add_argument("--weak-mode-line-norm", choices=("hminus_half", "p0_l2"),
                        default="hminus_half")
    parser.add_argument("--line-law", choices=("hybrid", "material_line"),
                        default="hybrid")
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    with threadpool_limits(limits=1):
        result = evaluate(args.shell_cells,
                          weak_mode_only=args.weak_mode_only,
                          weak_mode_line_norm=args.weak_mode_line_norm,
                          line_law=args.line_law,
                          beam_half_cells=args.beam_half_cells,
                          matched_p0_only=args.matched_p0_only,
                          trace_only=args.trace_only)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"elapsed_s": result["elapsed_s"],
                      "cases": {key: {
                          "status": value.get("status", "MIXED_METRIC_COMPUTED"),
                          "beta_min": value.get("beta_min"),
                          "trace_singular_min": value.get("trace_singular_min"),
                          "rank": value["normalized_constraint_rank"]}
                          for key, value in result["cases"].items()}}))


if __name__ == "__main__":
    main()
