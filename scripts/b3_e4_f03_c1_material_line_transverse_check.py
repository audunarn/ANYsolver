"""One fixed-dual E4 y4→y8 check after the stopped x-resolution series."""

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


def evaluate(reconstruction_path: Path, longitudinal_path: Path) -> dict:
    reconstruction = json.loads(reconstruction_path.read_text())
    previous = json.loads(longitudinal_path.read_text())
    if (reconstruction["status"] != "EXPLORATORY_COMPLETE" or
            previous["status"] != "DEVELOPMENT_DIAGNOSTIC_COMPLETE" or
            previous["solid_reconstruction_sha256"] != digest(reconstruction_path) or
            previous["transverse_cells"] != 4):
        raise ValueError("same fixed-dual x8/y4 predecessor required")
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um", assemble=False)
    xs, ys = local_grid(8, transverse_cells=8)
    line = MaterialLinePosition(xs, ys, beam)
    space = LineMultiplierSpace("piecewise_constant", tuple(np.linspace(0., 1., 5)))
    rows, measure = _rows(line, space)
    if not np.allclose(measure, .025, rtol=0., atol=1e-12):
        raise ArithmeticError("fixed P0 measure changed")
    shell_size = 6*line.shell_count
    stiffness, _ = raw_e4_tangent(xs, ys, thickness=.035)
    fixed = {6*(j*len(xs)+i)+axis
             for j in range(len(ys)) for i, x in enumerate(xs)
             if abs(x+.5) < 1e-12 for axis in range(6)}
    cases = {}
    for label in ("tip_mx", "tip_fz"):
        dual = np.asarray(reconstruction["cases"][label]["dual_physical_line_density"])
        native_dual = (dual.reshape(4, 6)*measure[:, None]).ravel()
        force = -(rows[:, :shell_size].T@native_dual)
        response, error = _solve_component(stiffness, force, fixed)
        work = float(force@response)
        reference_work = previous["levels"]["8"]["cases"][label]["solid_plate_action_only_work_J"]
        if abs(work+native_dual@(rows[:, :shell_size]@response)) > 1e-10:
            raise ArithmeticError("fixed-dual transverse work changed")
        cases[label] = {
            "x8_y4_work_J": previous["levels"]["8"]["cases"][label]["native_shell_action_only_work_J"],
            "x8_y8_work_J": work,
            "solid_plate_work_J": reference_work,
            "x8_y4_relative_to_solid": previous["levels"]["8"]["cases"][label]["native_vs_solid_relative"],
            "x8_y8_relative_to_solid": work/reference_work-1.,
            "equilibrium_ratio": error,
        }
    return {
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "classification": "fixed material-line dual and x8 E4; y4→y8 only",
        "solid_reconstruction_sha256": digest(reconstruction_path),
        "longitudinal_result_sha256": digest(longitudinal_path),
        "shell_nodes": line.shell_count,
        "shell_dof": shell_size,
        "cases": cases,
        "limitations": [
            "one y doubling is a discriminator, not convergence evidence",
            "fixed solid dual and P0; not a re-equilibrated coupled model",
            "no physical accuracy, connection-law or G0B acceptance",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reconstruction", type=Path, required=True)
    parser.add_argument("--longitudinal", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve previous transverse diagnostic")
    result = evaluate(args.reconstruction.resolve(), args.longitudinal.resolve())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "relative": {
        case: record["x8_y8_relative_to_solid"]
        for case, record in result["cases"].items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
