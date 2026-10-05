"""Bounded fixed-dual E4 physical/completion work diagnostic.

This uses the unchanged production zero-state tangent for the response.
The element-reported physical operator only partitions that response's
quadratic work; no stiffness is retuned or substituted in the solve.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

import numpy as np

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts.b3_e4_f03_c1_material_line_loaded import (
    _validated_solid_reconstruction,
)
from scripts.b3_e4_f03_c1_material_line_same_action import _solve_component
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_material_line_position import MaterialLinePosition
from scripts.b3_e4_f03_material_line_space_screen import _rows
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def evaluate(reconstruction_path: Path) -> dict:
    solid = _validated_solid_reconstruction(reconstruction_path)
    xs, ys = local_grid(4, transverse_cells=4)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um", assemble=False)
    line = MaterialLinePosition(xs, ys, beam)
    space = LineMultiplierSpace("piecewise_constant", tuple(np.linspace(0., 1., 5)))
    rows, measure = _rows(line, space)
    if rows.shape[0] != 24 or not np.allclose(measure, .025, rtol=0., atol=1e-12):
        raise ArithmeticError("same P0 m4 line layout changed")
    tangent, physical = raw_e4_tangent(xs, ys, thickness=.035)
    shell_size = 6 * line.shell_count
    fixed = {6*(j*len(xs)+i)+axis for j in range(len(ys))
             for i, x in enumerate(xs) if abs(x+.5) < 1e-12
             for axis in range(6)}
    skew_t = float(np.linalg.norm(tangent-tangent.T)/np.linalg.norm(tangent))
    skew_p = float(np.linalg.norm(physical-physical.T)/np.linalg.norm(physical))
    if max(skew_t, skew_p) > 1e-9:
        raise ArithmeticError("zero-state E4 work partition requires symmetric operators")
    cases = {}
    for label in ("tip_mx", "tip_fz"):
        density = np.asarray(solid["cases"][label]["dual_physical_line_density"])
        dual = (density.reshape(4, 6)*measure[:, None]).ravel()
        force = -rows[:, :shell_size].T@dual
        response, equilibrium = _solve_component(tangent, force, fixed)
        total = float(force@response)
        physical_work = float(response@physical@response)
        completion_work = float(response@(tangent-physical)@response)
        rz_work = float(force[5::6]@response[5::6])
        if not np.isclose(total, physical_work+completion_work,
                          rtol=1e-10, atol=1e-12):
            raise ArithmeticError("E4 response work does not partition")
        cases[label] = {
            "total_action_work_J": total,
            "physical_operator_work_J": physical_work,
            "completion_operator_work_J": completion_work,
            "completion_fraction_of_total": completion_work/total,
            "drilling_coordinate_force_work_J": rz_work,
            "drilling_coordinate_force_work_fraction": rz_work/total,
            "equilibrium_ratio": equilibrium,
        }
    return {
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "classification": "fixed-dual E4 physical and completion quadratic work",
        "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                                 text=True).strip(),
        "solid_reconstruction_sha256": digest(reconstruction_path),
        "shell_tangent_relative_skew": skew_t,
        "shell_physical_relative_skew": skew_p,
        "cases": cases,
        "limitations": [
            "fixed dual and unchanged full-tangent response only",
            "drilling coordinate work is not the same as completion energy",
            "no source of E4/3D difference is established by this partition alone",
            "not F03/G0B acceptance or multiplier selection",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reconstruction", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve previous shell completion diagnostic")
    result = evaluate(args.reconstruction.resolve())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({key: {"completion_fraction": value["completion_fraction_of_total"],
                            "drilling_work_fraction": value["drilling_coordinate_force_work_fraction"]}
                      for key, value in result["cases"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
