"""Bounded loaded C1 longitudinal-resolution screen; not G0B acceptance."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

import numpy as np

from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_local_footprint_work import graded_terminal_coupling
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


FAMILIES = ("line_hybrid_p0_weighted", "line_hybrid_p1_weighted",
            "line_hybrid_dual_p1_weighted")


def evaluate(shell_cells: int, line_intervals: int, *,
             detailed: bool = False,
             quadrature_order: int = 3) -> dict:
    if shell_cells not in (4, 8, 16) or line_intervals not in (2, 4, 8, 16) or (
            line_intervals > shell_cells):
        raise ValueError("bounded aligned C1 shell/line resolution required")
    if quadrature_order not in (3, 5):
        raise ValueError("bounded C1 line quadrature order required")
    start = time.perf_counter()
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    result = graded_terminal_coupling(
        shell_cells, beam, transverse_cells=4, plate_thickness=.035,
        include_line_hybrid_spaces=True, sparse_line_only=True,
        line_multiplier_intervals=line_intervals,
        line_quadrature_order=quadrature_order, force_sign=-1.)
    elapsed = time.perf_counter()-start
    records = {}
    for family in FAMILIES:
        entry = result["results"][family]
        cases = {}
        for label in ("tip_mx", "tip_fz"):
            case = entry["cases"][label]
            cases[label] = {key: case[key] for key in (
                "tip_rx_rad", "tip_uz_m", "total_external_work_j",
                "physical_shell_work_j", "mechanics_error",
                "interface_shell_wrench_N_Nm",
                "shell_support_wrench_N_Nm",
                "sampled_line_position_gap")}
            if detailed:
                masses = np.asarray(entry["basis_integrals_m"], dtype=float)
                dual = np.asarray(
                    case["constraint_multiplier_material_N_Nm"],
                    dtype=float).reshape(-1, 6)
                if (dual.shape[0] != len(masses) or
                        not np.isfinite(dual).all() or
                        not np.isfinite(masses).all() or
                        np.any(masses <= 0.)):
                    raise ArithmeticError("invalid material line dual")
                cases[label].update({
                    "beam_root_wrench_N_Nm": case["beam_root_wrench_N_Nm"],
                    "interface_beam_wrench_N_Nm":
                        case["interface_beam_wrench_N_Nm"],
                    "interface_shell_work_j": case["interface_shell_work_j"],
                    "constraint_multiplier_material_N_Nm": dual.tolist(),
                    "basis_mean_material_dual_per_m":
                        (dual / masses[:, None]).tolist(),
                })
        records[family] = {
            "constraint_rank": entry["constraint_rank"],
            "scaled_row_inventory": entry["scaled_row_inventory"],
            "basis_integrals_m": entry["basis_integrals_m"],
            "cases": cases,
        }
    if not np.isfinite(elapsed) or elapsed <= 0.:
        raise ArithmeticError("invalid bounded elapsed time")
    return {
        "classification": "G0B loaded development screen; no interface stability or multiplier selection",
        "question": "Do growing longitudinal rows remain independent and balanced in the actual native retained-variable mixed solve?",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "operator_sources_sha256": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                                     for path in map(Path, (
                                         "scripts/b3_e4_f03_distributed_surface_finite.py",
                                         "scripts/b3_e4_f03_local_footprint_work.py",
                                         "scripts/_b3_e4_f03_native_fixture.py"))},
        "source_git": subprocess.check_output(
            ("git", "rev-parse", "HEAD"), text=True).strip(),
        "geometry": "C1 35 mm Q4 shell, native retained B3-12, 0.1 m terminal width and length, left supports",
        "loading": "+100 Nm tip Mx and -1000 N tip Fz as separate linear influences",
        "shell_bond_cells": shell_cells,
        "line_multiplier_intervals": line_intervals,
        "line_quadrature_order": quadrature_order,
        "elapsed_s_not_benchmark": elapsed,
        "families": records,
        "limitations": [
            "rank and loaded balance do not establish mesh-uniform inf-sup or full native mixed-system stability",
            "two shell resolutions are not a convergence qualification",
            "the shared-node F5 solid has a different full-width kinematic bond",
            "material line duals divided by basis integrals are not display-ready spatial traction wrenches",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shell-cells", type=int, required=True)
    parser.add_argument("--line-intervals", type=int, required=True)
    parser.add_argument("--quadrature-order", type=int, choices=(3, 5),
                        default=3)
    parser.add_argument("--detailed", action="store_true")
    args = parser.parse_args()
    print(json.dumps(evaluate(args.shell_cells, args.line_intervals,
                              detailed=args.detailed,
                              quadrature_order=args.quadrature_order),
                     indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
