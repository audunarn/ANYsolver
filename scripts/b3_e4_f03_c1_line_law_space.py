"""Check whether two bounded C1 line laws span the same supported rows.

Development identity check only. Rank or an angle does not establish an
interface inf-sup bound, loaded accuracy, or a multiplier policy.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

import numpy as np

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts.b3_e4_f03_distributed_surface_finite import c1_hybrid_line_space
from scripts.b3_e4_f03_material_line_position import MaterialLinePosition
from scripts.b3_e4_f03_material_line_space_screen import _rows
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def row_space_comparison(first, second) -> dict:
    """Compare finite row spans after common column and row scaling."""
    a, b = np.asarray(first, dtype=float), np.asarray(second, dtype=float)
    if (a.ndim != 2 or b.ndim != 2 or a.shape[1] != b.shape[1] or
            a.shape[0] == 0 or b.shape[0] == 0 or
            not np.isfinite(a).all() or not np.isfinite(b).all()):
        raise ValueError("finite row operators with common variables required")
    common = np.maximum(np.linalg.norm(np.vstack((a, b)), axis=0), 1e-14)
    a = a/common
    b = b/common
    a /= np.linalg.norm(a, axis=1)[:, None]
    b /= np.linalg.norm(b, axis=1)[:, None]

    def basis(rows):
        _, singular, right = np.linalg.svd(rows, full_matrices=False)
        threshold = 1e-10*singular[0]
        rank = int(np.count_nonzero(singular > threshold))
        return right[:rank].T, rank, float(singular[rank-1])

    qa, rank_a, smallest_a = basis(a)
    qb, rank_b, smallest_b = basis(b)
    _, union, _ = basis(np.vstack((a, b)))
    a_defect = np.linalg.norm(a-(a@qb)@qb.T)/np.linalg.norm(a)
    b_defect = np.linalg.norm(b-(b@qa)@qa.T)/np.linalg.norm(b)
    return {
        "first_rank": rank_a,
        "second_rank": rank_b,
        "union_rank": union,
        "first_rows": int(len(a)),
        "second_rows": int(len(b)),
        "first_smallest_retained_singular": smallest_a,
        "second_smallest_retained_singular": smallest_b,
        "first_outside_second_relative": float(a_defect),
        "second_outside_first_relative": float(b_defect),
        "same_row_space_at_1e-9": bool(rank_a == rank_b == union and
                                      max(a_defect, b_defect) <= 1e-9),
    }


def evaluate() -> dict:
    xs, ys = local_grid(4, transverse_cells=4)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um", assemble=False)
    line = MaterialLinePosition(xs, ys, beam)
    space = LineMultiplierSpace("piecewise_constant", tuple(np.linspace(0., 1., 5)))
    material, material_measure = _rows(line, space)
    hybrid, hybrid_measure, _ = c1_hybrid_line_space(
        xs, ys, beam, kind="piecewise_constant", intervals=4,
        thickness=.035, quadrature_order=3)
    if (material.shape != hybrid.shape or material.shape[0] != 24 or
            not np.allclose(material_measure, hybrid_measure,
                            rtol=0., atol=1e-12)):
        raise ArithmeticError("bounded P0 m4 law layouts differ")
    shell_size = 6*line.shell_count
    total = shell_size+beam.context.count
    if material.shape[1] != total:
        raise ArithmeticError("complete retained B3 coordinates required")
    shell_fixed = {6*(j*len(xs)+i)+axis for j in range(len(ys))
                   for i, x in enumerate(xs) if abs(x+.5) < 1e-12
                   for axis in range(6)}
    beam_fixed = {shell_size+int(index) for index in beam.context.fixed}
    free = np.array(sorted(set(range(total))-shell_fixed-beam_fixed))
    shell_free = free[free < shell_size]
    beam_free = free[free >= shell_size]
    length = np.tile((1., 1., 1., .1, .1, .1), 4)
    a, b = material*length[:, None], hybrid*length[:, None]
    return {
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "classification": "fixed C1 P0 m4 material-line versus finite-strip row-space identity",
        "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                                 text=True).strip(),
        "geometry": "Q4 x4/y4, native B3-12, 35 mm shell, 100 mm section, 67.5 mm axis",
        "p0_intervals": 4,
        "measure_m": material_measure.tolist(),
        "physical_free_variables": int(len(free)),
        "shell_free_variables": int(len(shell_free)),
        "beam_free_variables": int(len(beam_free)),
        "full_supported": row_space_comparison(a[:, free], b[:, free]),
        "shell_supported": row_space_comparison(a[:, shell_free], b[:, shell_free]),
        "beam_supported": row_space_comparison(a[:, beam_free], b[:, beam_free]),
        "limitations": [
            "row-space identity only; neither law is selected",
            "finite fixed supported fixture, not mesh-uniform stability",
            "no loaded response or physical accuracy inference",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve previous law-space diagnostic")
    result = evaluate()
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({key: result[key] for key in
                      ("full_supported", "shell_supported", "beam_supported")},
                     sort_keys=True))


if __name__ == "__main__":
    main()
