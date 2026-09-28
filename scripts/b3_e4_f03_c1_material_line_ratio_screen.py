"""Bounded material-line row screen over declared beam:shell bond ratios.

This tests one provisional resolution rule only. It does not assemble a KKT
system or establish physical transfer, locking, or uniform inf-sup stability.
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

import anysolver
import numpy as np
import scipy
from threadpoolctl import threadpool_info, threadpool_limits

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts.b3_e4_f03_material_line_loaded import _scales
from scripts.b3_e4_f03_material_line_position import MaterialLinePosition
from scripts.b3_e4_f03_material_line_space_screen import (
    _rows, _scaled_row_diagnostics,
)
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


# Existing C1 fixture bond cuts give 2, 4, 8, or 16 native half-cells.
# Every declared ratio uses the same 0.9–1.0 m physical material line.
CASES = (
    (2, 26, "1:8"),
    (4, 26, "1:4"),
    (4, 18, "1:2"),
    (8, 18, "1:1"),
    (8, 14, "2:1"),
    (8, 12, "4:1"),
    (16, 12, "8:1"),
)
KINDS = ("piecewise_constant", "continuous_linear", "dual_linear")


def evaluate() -> dict:
    expected = (Path(__file__).resolve().parents[1]/"src"/"anysolver").resolve()
    if Path(anysolver.__file__).resolve().parent != expected:
        raise RuntimeError("ratio screen imported another ANYsolver checkout")
    started = monotonic()
    deadline = started+120.
    cases = {}
    for shell_cells, beam_halves, label in CASES:
        if monotonic() > deadline:
            raise TimeoutError("bounded C1 ratio row-screen deadline")
        xs, ys = local_grid(shell_cells, transverse_cells=4)
        beam = build(beam_halves, z_offset=.0675,
                     torsion_constant=square_torsion_constant(),
                     reference_profile="c1_tangent_2um", assemble=False)
        bond_halves = int(np.sum(np.diff(beam.abscissae)[
            beam.abscissae[:-1] >= .9-1e-12] > 0.))
        if (shell_cells*1 != int(label.split(":")[0])*bond_halves /
                int(label.split(":")[1])):
            raise ArithmeticError("declared beam:shell bond ratio changed")
        intervals = min(shell_cells, 2*bond_halves)
        if shell_cells % intervals:
            raise ArithmeticError("provisional multiplier cuts leave shell hosts")
        line = MaterialLinePosition(xs, ys, beam)
        ns = 6*len(xs)*len(ys)
        fixed_shell = {6*(j*len(xs)+i)+axis
                       for j in range(len(ys)) for i, x in enumerate(xs)
                       if abs(x+.5) < 1e-12 for axis in range(6)}
        fixed_beam = {ns+int(i) for i in beam.context.fixed}
        free = np.setdiff1d(np.arange(ns+beam.context.count),
                            np.array(sorted(fixed_shell|fixed_beam)))
        row_results = {}
        for kind in KINDS:
            space = LineMultiplierSpace(
                kind, tuple(np.linspace(0., 1., intervals+1)))
            rows, masses = _rows(line, space)
            scales, _ = _scales(ns, beam, free, row_count=len(rows))
            diagnostic = _scaled_row_diagnostics(rows, free, scales[:len(free)])
            if diagnostic["scaled_row_rank"] > len(rows):
                raise ArithmeticError("reported line rank exceeds row count")
            row_results[kind] = {
                "rows": len(rows),
                "rank": diagnostic["scaled_row_rank"],
                "smallest_unit_row_singular": min(
                    diagnostic["scaled_row_singular_values"]),
                "rank_tolerance": diagnostic["rank_tolerance"],
                "active_primal_columns": diagnostic["active_primal_columns"],
                "basis_integrals_m": masses.tolist(),
            }
        cases[label] = {
            "shell_bond_cells": shell_cells,
            "beam_half_cells_total": beam_halves,
            "beam_bond_half_cells": bond_halves,
            "multiplier_intervals": intervals,
            "station_count": len(line.stations),
            "spaces": row_results,
        }
    return {
        "classification": "bounded material-line ratio row screen, not mixed stability or F03 acceptance",
        "question": "Does m=min(shell bond cells,2*beam bond half-cells) avoid dependent projected rows at registered ratios?",
        "ratio_convention": "shell bond cell count : native beam half-cell count on the same 0.9-1.0 m line",
        "geometry": "Q4/y4, 35 mm shell, 100 mm square beam, 67.5 mm eccentricity, same C1 taper and root supports",
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "cases": cases,
        "elapsed_s": monotonic()-started,
        "limits": ["existing <=60-row and <=1200-active-column unit-row diagnostic",
                   "no tangent, KKT solve, physical load, or mesh-uniform stability claim",
                   "one provisional policy and one shell/beam grid per ratio",
                   "rank alone cannot select P0, P1, or dual"],
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_git": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "python": sys.version.split()[0], "numpy": np.__version__,
        "scipy": scipy.__version__, "anysolver_import_path": str(
            Path(anysolver.__file__).resolve()),
        "effective_threadpools": threadpool_info(),
        "env": {k: os.environ.get(k) for k in
                ("NUMBA_DISABLE_JIT", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS")},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    with threadpool_limits(limits=1):
        result = evaluate()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({ratio: {name: [item["rank"], item["rows"]]
                             for name, item in case["spaces"].items()}
                      for ratio, case in result["cases"].items()}))


if __name__ == "__main__":
    main()
