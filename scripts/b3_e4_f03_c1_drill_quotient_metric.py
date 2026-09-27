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
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def _relative(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a-b)/max(1., np.linalg.norm(b)))


def evaluate(shell_cells: int = 8) -> dict:
    if shell_cells not in (4, 8, 16):
        raise ValueError("bounded C1 drill-quotient shell level required")
    started = monotonic()
    deadline = started+120.
    xs, ys = local_grid(shell_cells, transverse_cells=4)
    shell, physical = raw_e4_tangent(xs, ys, thickness=prior.T)
    beam = build(12, z_offset=.0675,
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
    k_beam = beam.tangent.toarray()[np.ix_(beam_free, beam_free)]
    k_primal = linalg.block_diag(quotient, k_beam)
    r_primal = linalg.block_diag(r_shell, r_beam)
    free_physical = np.r_[shell_physical, ns+beam_free]
    free_full = np.r_[shell_free, ns+beam_free]
    cases = {}
    for intervals in (shell_cells//2, shell_cells):
        for kind in prior.KINDS:
            if monotonic() > deadline:
                raise TimeoutError("bounded drill quotient mixed deadline")
            rows, masses, _ = c1_hybrid_line_space(
                xs, ys, beam, kind=kind, intervals=intervals)
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
            r_line, line_info = prior._line_metric(kind, intervals, masses)
            chol_line = linalg.cholesky(r_line, lower=True)
            chol_primal = linalg.cholesky(r_primal, lower=True)
            scaled_c = linalg.solve_triangular(chol_line, c, lower=True)
            scaled_c = linalg.solve_triangular(
                chol_primal, scaled_c.T, lower=True).T
            rank = int(np.linalg.matrix_rank(scaled_c))
            if rank != len(c):
                raise ArithmeticError("quotient line row rank lost")
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
            report = prior._case(a, r, pieces, len(c), deadline)
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
        Path("scripts/_b3_e4_f03_dual_linear_norm.py")]
    return {
        "classification": "bounded drill-quotient native retained KKT diagnostic, not G0B acceptance",
        "question": "Was the prior smallest native KKT mode only a numerical drilling metric mode, and do line-coupled modes decline under growing rows?",
        "model": (f"C1 Q4 x{shell_cells}/y4 35 mm shell, native B3-12, "
                  f"P0/P1/dual m{shell_cells//2}/m{shell_cells}"),
        "operator": "actual E4 tangent with exact free-drilling Schur complement; actual native retained B3 tangent and line rows",
        "metric": "physical E4 energy on non-drilling coordinates; previous native B3 and basis-specific line norms",
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
                   "two interface resolutions on one shell grid, not registered ratio/refinement acceptance",
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
    parser.add_argument("--shell-cells", type=int, choices=(4, 8, 16), default=8)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    with threadpool_limits(limits=1):
        result = evaluate(args.shell_cells)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"elapsed_s": result["elapsed_s"],
                      "minima": {key: value["beta_min"]
                                 for key, value in result["cases"].items()}}))


if __name__ == "__main__":
    main()
