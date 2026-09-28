"""Bounded native retained-KKT metric for the current C1 material-line rows.

This is a private G0 diagnostic. The auxiliary Riesz metric is not assembled
into the mechanics tangent and these three 1:1 levels are not a stability
certificate or a multiplier-space selection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from time import monotonic

import anysolver
import numpy as np
from scipy import linalg
from threadpoolctl import threadpool_info, threadpool_limits

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts.b3_e4_f03_c1_native_mixed_metric import (
    _beam_metric, _case, _drilling_metric, _line_metric, L_LINE, MAX_ROWS, T,
)
from scripts.b3_e4_f03_material_line_position import MaterialLinePosition
from scripts.b3_e4_f03_material_line_space_screen import _rows
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


BEAM_HALVES = {2: 12, 4: 14, 8: 18}
KINDS = ("piecewise_constant", "continuous_linear", "dual_linear")


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _channel(metric: np.ndarray, axis: int, count: int) -> np.ndarray:
    ids = 6*np.arange(count)+axis
    return metric[np.ix_(ids, ids)]


def evaluate(shell_cells: int, kind: str, *, exact_drill_quotient: bool = False) -> dict:
    if shell_cells not in BEAM_HALVES or kind not in KINDS:
        raise ValueError("registered 1:1 material-line fixture required")
    expected = (Path(__file__).resolve().parents[1]/"src"/"anysolver").resolve()
    if Path(anysolver.__file__).resolve().parent != expected:
        raise RuntimeError("mixed metric imported another ANYsolver checkout")
    start = monotonic()
    deadline = start+120.
    beam_halves = BEAM_HALVES[shell_cells]
    xs, ys = local_grid(shell_cells, transverse_cells=4)
    shell, shell_physical = raw_e4_tangent(xs, ys, thickness=T)
    beam = build(beam_halves, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    if beam.tangent is None:
        raise ArithmeticError("native retained tangent required")
    ns = len(shell)
    shell_free = np.array([i for i in range(ns)
                           if (i//6) % len(xs) != 0])
    beam_free = np.asarray(beam.context.free, dtype=int)
    drill_check = None
    if exact_drill_quotient:
        drill = shell_free[shell_free % 6 == 5]
        shell_active = shell_free[shell_free % 6 != 5]
        dd = shell[np.ix_(drill, drill)]
        dp = shell[np.ix_(drill, shell_active)]
        pd = shell[np.ix_(shell_active, drill)]
        pp = shell[np.ix_(shell_active, shell_active)]
        linalg.cholesky(dd, lower=True, check_finite=True)
        lift = linalg.solve(dd, dp, assume_a="pos", check_finite=True)
        shell_quotient = pp-pd@lift
        quotient_skew = float(np.linalg.norm(shell_quotient-shell_quotient.T)/
                              max(1., np.linalg.norm(shell_quotient)))
        if quotient_skew > 1e-10:
            raise ArithmeticError("exact shell drilling quotient is asymmetric")
        linalg.cholesky(shell_quotient, lower=True, check_finite=True)
        probe = np.sin(np.arange(len(shell_active))*.173)
        full_probe = np.zeros(ns)
        full_probe[shell_active] = probe
        full_probe[drill] = -lift@probe
        drill_check = {
            "quotient_relative_skew": quotient_skew,
            "drill_equation_relative": float(np.linalg.norm(
                (shell@full_probe)[drill])/max(1., np.linalg.norm(dp@probe))),
            "physical_action_relative": float(np.linalg.norm(
                (shell@full_probe)[shell_active]-shell_quotient@probe)/
                max(1., np.linalg.norm(shell_quotient@probe))),
            "drill_rows": len(drill),
        }
        if max(drill_check["drill_equation_relative"],
               drill_check["physical_action_relative"]) > 1e-8:
            raise ArithmeticError("exact shell drilling reconstruction failed")
        shell_metric_active = shell_quotient
        shell_tangent_active = shell_quotient
        shell_physical_active = shell_quotient
        shell_chart_active = np.zeros_like(shell_quotient)
    else:
        shell_active = shell_free
        R_shell = shell_physical.copy()
        drill_ids = 6*np.arange(len(xs)*len(ys))+5
        R_shell[np.ix_(drill_ids, drill_ids)] += _drilling_metric(xs, ys)
        shell_metric_active = R_shell[np.ix_(shell_free, shell_free)]
        shell_tangent_active = shell[np.ix_(shell_free, shell_free)]
        shell_physical_active = shell_physical[np.ix_(shell_free, shell_free)]
        shell_chart_active = shell_metric_active-shell_physical_active
    free = np.r_[shell_active, ns+beam_free]
    R_beam, R_resultant, layout = _beam_metric(beam)
    R_primal = linalg.block_diag(
        shell_metric_active,
        R_beam[np.ix_(beam_free, beam_free)])
    K = linalg.block_diag(
        shell_tangent_active,
        beam.tangent.toarray()[np.ix_(beam_free, beam_free)])
    line = MaterialLinePosition(xs, ys, beam)
    p0_rows, p0_masses = _rows(line, LineMultiplierSpace(
        "piecewise_constant", tuple(np.linspace(0., 1., shell_cells+1))))
    if abs(np.sum(p0_masses)-L_LINE) > 1e-12:
        raise ArithmeticError("P0 line measure changed")
    p0_metric, p0_info = _line_metric(
        "piecewise_constant", shell_cells, p0_masses)
    if kind == "piecewise_constant":
        rows, R_line = p0_rows, p0_metric
        yaw_info = None
    else:
        yaw_intervals = shell_cells//2
        yaw_rows, yaw_masses = _rows(line, LineMultiplierSpace(
            kind, tuple(np.linspace(0., 1., yaw_intervals+1))))
        if abs(np.sum(yaw_masses)-L_LINE) > 1e-12:
            raise ArithmeticError("yaw line measure changed")
        yaw_metric, yaw_info = _line_metric(kind, yaw_intervals, yaw_masses)
        rows = np.vstack([p0_rows[axis::6] for axis in range(5)] +
                         [yaw_rows[5::6]])
        R_line = linalg.block_diag(*[
            _channel(p0_metric, axis, len(p0_masses)) for axis in range(5)
        ], _channel(yaw_metric, 5, len(yaw_masses)))
    if exact_drill_quotient and np.max(np.abs(rows[:, drill])) > 1e-12:
        raise ArithmeticError("line rows unexpectedly act on shell drilling")
    C = rows[:, free]
    R = linalg.block_diag(R_primal, R_line)
    A = np.block([[K, C.T], [C, np.zeros((len(C), len(C)))]])
    if len(A) > MAX_ROWS or monotonic() > deadline:
        raise TimeoutError("bounded native KKT resource limit reached")
    primal_chol = linalg.cholesky(R_primal, lower=True, check_finite=True)
    line_chol = linalg.cholesky(R_line, lower=True, check_finite=True)
    normed_C = linalg.solve_triangular(line_chol, C, lower=True)
    normed_C = linalg.solve_triangular(
        primal_chol, normed_C.T, lower=True).T
    row_rank = int(np.linalg.matrix_rank(normed_C))
    if row_rank != len(C):
        raise ArithmeticError("normed material-line rows lost rank")
    shell_n = len(shell_active)
    beam_n = len(beam_free)
    beam_resultant = R_resultant[np.ix_(beam_free, beam_free)]
    pieces = {"C": C, "blocks": [
        ("shell_physical", slice(0, shell_n), shell_physical_active),
        ("shell_drilling_chart", slice(0, shell_n), shell_chart_active),
        ("beam_kinematic", slice(shell_n, shell_n+beam_n),
         R_beam[np.ix_(beam_free, beam_free)]-beam_resultant),
        ("beam_complementary", slice(shell_n, shell_n+beam_n),
         beam_resultant),
        ("line_dual", slice(shell_n+beam_n, None), R_line),
    ]}
    report = _case(A, R, pieces, len(C), deadline)
    if monotonic() > deadline:
        raise TimeoutError("bounded native mixed metric deadline")
    return {
        "classification": "private material-line native retained KKT metric",
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "decision": "three-level mixed behavior only; no uniform stability or multiplier selection",
        "geometry": f"C1 Q4 x{shell_cells}/y4; B3-{beam_halves}; 1:1 bond",
        "space_kind": kind,
        "representation": ("exact_drilling_quotient" if exact_drill_quotient
                           else "full_shell_chart"),
        "drilling_quotient_check": drill_check,
        "p0_intervals": shell_cells,
        "yaw_intervals": shell_cells//2 if kind != "piecewise_constant" else None,
        "row_rank": row_rank,
        "primal_rows": len(K),
        "beam_layout": layout,
        "p0_line_norm": p0_info,
        "yaw_line_norm": yaw_info,
        "report": report,
        "elapsed_s": monotonic()-start,
        "runner_sha256": _hash(Path(__file__)),
        "source_git": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True).strip(),
        "imported_anysolver": str(Path(anysolver.__file__).resolve()),
        "effective_threadpools": threadpool_info(),
        "env": {name: os.environ.get(name) for name in (
            "NUMBA_DISABLE_JIT", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS")},
        "limits": ["one level per run", "1900 dense KKT rows", "120 s wall deadline",
                   "auxiliary Riesz norm not added to tangent",
                   "no physical transfer or mesh-uniform claim"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shell-cells", type=int, required=True)
    parser.add_argument("--space-kind", choices=KINDS, required=True)
    parser.add_argument("--exact-drill-quotient", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    with threadpool_limits(limits=1):
        result = evaluate(args.shell_cells, args.space_kind,
                          exact_drill_quotient=args.exact_drill_quotient)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n")
    print(json.dumps({"rows": result["report"]["rows"],
                      "row_rank": result["row_rank"],
                      "beta_min": result["report"]["beta_min"],
                      "elapsed_s": result["elapsed_s"]}))


if __name__ == "__main__":
    main()
