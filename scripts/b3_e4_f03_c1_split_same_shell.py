"""Replay global-six, split-twelve and native P0 actions on one E4 shell."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import linalg

from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_c1_six_channel_same_shell import (
    BASE, NATIVE, RECON, SOURCE, _project_plate_action,
)
from scripts.b3_e4_f03_ccx_split_six_channel import split_rows
from scripts.b3_e4_f03_ccx_six_channel_compliance import _source
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_distributed_surface_finite import c1_hybrid_line_space
from scripts.b3_e4_f03_factor5_shell_action import (
    _generalized_wrench, _solve_shell,
)
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


SPLIT = (BASE / "f03-c1-split-six-channel-dev-20260927-v1/"
         "reconstruction_v2.json")


def evaluate():
    split = json.loads(SPLIT.read_text())
    global_six = json.loads(RECON.read_text())
    native = json.loads(NATIVE.read_text())
    if (split["status"] != "EXPLORATORY_COMPLETE" or
            global_six["status"] != "EXPLORATORY_COMPLETE" or
            native["shell_bond_cells"] != 4 or
            native["line_multiplier_intervals"] != 2):
        raise ValueError("three matched development inputs required")
    deck, _, coords, global_rows, _, _ = _source(SOURCE)
    plate, _ = _element_domain_nodes(deck)
    rows = split_rows(coords, plate, _element_domain_nodes(deck)[1])
    xs, ys = local_grid(4, transverse_cells=4)
    nodes = np.array([(x, y, 0.) for y in ys for x in xs])
    tangent, physical = raw_e4_tangent(xs, ys, thickness=.035)
    fixed = {6*j*len(xs)+axis for j in range(len(ys)) for axis in range(6)}
    free = np.array([i for i in range(len(tangent)) if i not in fixed])
    factor = linalg.lu_factor(tangent[np.ix_(free, free)], check_finite=True)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um", assemble=False)
    shell_size = len(nodes)*6
    trace, masses, _ = c1_hybrid_line_space(
        xs, ys, beam, kind="piecewise_constant", intervals=2,
        thickness=.035, quadrature_order=3)
    saved_family = native["families"]["line_hybrid_p0_weighted"]
    np.testing.assert_allclose(masses, saved_family["basis_integrals_m"],
                               rtol=0, atol=1e-12)
    cases = {}
    for label in ("tip_mx", "tip_fz"):
        split_case = split["cases"][label]
        global_case = global_six["cases"][label]
        saved = saved_family["cases"][label]
        split_action = _project_plate_action(
            coords, rows, np.asarray(split_case["dual_physical"]),
            plate, xs, ys)
        global_action = _project_plate_action(
            coords, global_rows, np.asarray(global_case["dual_physical"]),
            plate, xs, ys)
        native_dual = np.asarray(saved["constraint_multiplier_material_N_Nm"])
        native_action = (-trace[:, :shell_size].T@native_dual.ravel()
                         ).reshape(-1, 6)
        for action, wrench in (
                (split_action, split_case["plate_interface_wrench_N_Nm"]),
                (global_action, global_case["plate_interface_wrench_N_Nm"]),
                (native_action, saved["interface_shell_wrench_N_Nm"])):
            np.testing.assert_allclose(_generalized_wrench(action, nodes),
                                       wrench, rtol=0, atol=1e-7)
        split_state, split_result = _solve_shell(
            tangent, physical, split_action, free, factor)
        global_state, global_result = _solve_shell(
            tangent, physical, global_action, free, factor)
        native_state, native_result = _solve_shell(
            tangent, physical, native_action, free, factor)
        cross = float(split_action.ravel()@native_state.ravel()-
                      native_action.ravel()@split_state.ravel())
        if abs(cross) > 1e-8:
            raise ArithmeticError("split/native same-shell reciprocity failed")
        if (abs(native_result["applied_final_state_work_j"]-
                saved["interface_shell_work_j"]) > 1e-8 or
                abs(native_result["physical_shell_work_j"]-
                    saved["physical_shell_work_j"]) > 1e-8):
            raise ArithmeticError("saved native E4 action replay changed")
        cases[label] = {
            "global_six_shell_work_J": global_result["applied_final_state_work_j"],
            "split_twelve_shell_work_J": split_result["applied_final_state_work_j"],
            "native_p0_shell_work_J": native_result["applied_final_state_work_j"],
            "split_native_cross_work_defect_J": cross,
            "split_plate_wrench_N_Nm": split_case["plate_interface_wrench_N_Nm"],
            "global_plate_wrench_N_Nm": global_case["plate_interface_wrench_N_Nm"],
            "native_plate_wrench_N_Nm": saved["interface_shell_wrench_N_Nm"],
        }
    return {
        "classification": "three physical actions on the same E4 Q4 shell; development only",
        "status": "EXPLORATORY_COMPLETE", "cases": cases,
        "inputs_sha256": {str(path): digest(path)
                          for path in (SPLIT, RECON, NATIVE)},
        "source_sha256": digest(Path(__file__)),
        "limitations": ["same shell separates action shape, not continuum fidelity",
                        "raw mixed-unit covector norms are not used for physical comparison",
                        "one grid, no multiplier selection or F03/G0B acceptance"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve previous split same-shell result")
    report = evaluate()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n")
    print(json.dumps({key: value["split_twelve_shell_work_J"]
                      for key, value in report["cases"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
