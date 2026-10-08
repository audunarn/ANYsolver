"""Fixed-dual E4 longitudinal-resolution discriminator for the matched line."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts.b3_e4_f03_c1_material_line_same_action import _solve_component
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_material_line_position import MaterialLinePosition
from scripts.b3_e4_f03_material_line_space_screen import _rows
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def evaluate(reconstruction_path: Path, same_action_path: Path) -> dict:
    reconstruction = json.loads(reconstruction_path.read_text())
    prior = json.loads(same_action_path.read_text())
    if (reconstruction["status"] != "EXPLORATORY_COMPLETE" or
            prior["status"] != "DEVELOPMENT_DIAGNOSTIC_COMPLETE" or
            prior["solid_reconstruction_sha256"] != digest(reconstruction_path)):
        raise ValueError("same fixed solid dual/action result required")
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um", assemble=False)
    space = LineMultiplierSpace("piecewise_constant", tuple(np.linspace(0., 1., 5)))
    levels = {}
    for shell_cells in (4, 8, 16):
        xs, ys = local_grid(shell_cells, transverse_cells=4)
        line = MaterialLinePosition(xs, ys, beam)
        rows, measure = _rows(line, space)
        if not np.allclose(measure, .025, rtol=0., atol=1e-12):
            raise ArithmeticError("fixed P0 interval measure changed")
        shell_size = 6*line.shell_count
        shell_k, _ = raw_e4_tangent(xs, ys, thickness=.035)
        fixed = {6*(j*len(xs)+i)+axis
                 for j in range(len(ys)) for i, x in enumerate(xs)
                 if abs(x+.5) < 1e-12 for axis in range(6)}
        cases = {}
        for label in ("tip_mx", "tip_fz"):
            dual = np.asarray(reconstruction["cases"][label]["dual_physical_line_density"])
            native_dual = (dual.reshape(4, 6)*measure[:, None]).ravel()
            force = -(rows[:, :shell_size].T@native_dual)
            response, equilibrium = _solve_component(shell_k, force, fixed)
            work = float(force@response)
            if abs(work+native_dual@(rows[:, :shell_size]@response)) > 1e-10:
                raise ArithmeticError("E4 material-line dual work changed")
            if shell_cells == 4:
                np.testing.assert_allclose(
                    work, prior["cases"][label]["native_shell_action_only_work_J"],
                    rtol=1e-11, atol=1e-12)
            cases[label] = {
                "native_shell_action_only_work_J": work,
                "solid_plate_action_only_work_J": prior["cases"][label]["solid_shell_action_only_work_J"],
                "native_vs_solid_relative": work/prior["cases"][label]["solid_shell_action_only_work_J"]-1.,
                "equilibrium_ratio": equilibrium,
            }
        levels[str(shell_cells)] = {"shell_nodes": line.shell_count,
                                    "shell_dof": shell_size,
                                    "line_rows": len(rows),
                                    "cases": cases}
    return {
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "classification": "fixed matched-line dual and P0 policy; E4 x-resolution only",
        "solid_reconstruction_sha256": digest(reconstruction_path),
        "same_action_sha256": digest(same_action_path),
        "transverse_cells": 4,
        "beam_half_cells_for_trace": 12,
        "levels": levels,
        "limitations": [
            "fixed dual is the x4 solid-constrained result; not a re-equilibrated coupled refinement",
            "fixed y4 and one 3D plate mesh; no physical convergence or accuracy claim",
            "support/clamp and E4 versus 3D plate idealization remain distinct",
            "not F03/G0B acceptance or multiplier selection",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reconstruction", type=Path, required=True)
    parser.add_argument("--same-action", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve previous resolution diagnostic")
    result = evaluate(args.reconstruction.resolve(), args.same_action.resolve())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "relative": {
        level: {case: item["native_vs_solid_relative"]
                for case, item in record["cases"].items()}
        for level, record in result["levels"].items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
