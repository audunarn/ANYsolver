"""Compare resolved-solid and native six-channel actions on one E4 shell.

This replays physical plate-side forces from the exact linear solid KKT
reconstruction and native material duals on the *same* E4 Q4 x4/y4 shell.
It separates action shape from shell response without claiming that the
solid, E4 shell, and retained B3 sections have identical kinematics.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import linalg

from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_ccx_six_channel_compliance import _source
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_distributed_surface_finite import c1_hybrid_line_space
from scripts.b3_e4_f03_factor5_shell_action import (
    _generalized_wrench, _solve_shell, _top_response,
)
from scripts.b3_e4_f03_local_footprint_work import structured_q4_point_shape
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / ".qualification/b3-ge-e4-pl"
RECON = (BASE / "f03-c1-six-channel-compliance-dev-20260927-v1/"
         "reconstruction_v5.json")
SOURCE = BASE / "f03-c1-detached-port-dev-20260926-v2/tip_mx"
NATIVE = (ROOT / "docs/agent_plans/"
          "B3_GE_E4_PL_F03_NATIVE_LOADED_CONTINUOUS_X4_M2_DEV_V1.json")
KINDS = {"line_hybrid_p0_weighted": "piecewise_constant",
         "line_hybrid_p1_weighted": "continuous_linear",
         "line_hybrid_dual_p1_weighted": "dual_linear"}


def _project_plate_action(coords, rows, dual, plate_nodes, xs, ys):
    shell = np.zeros((len(xs) * len(ys), 6))
    force_by_node = {}
    for multiplier, row in zip(dual, rows):
        for (node, axis), value in row.items():
            if node in plate_nodes:
                force_by_node.setdefault(node, np.zeros(3))[axis] -= multiplier*value
    for node, force in force_by_node.items():
        x, y, z = coords[node]
        if not (.9-1e-12 <= x <= 1.+1e-12 and
                -.05-1e-12 <= y <= .05+1e-12 and
                abs(abs(z)-.0175) < 1e-12):
            raise ValueError("solid plate action lies outside declared sided patch")
        host, shape = structured_q4_point_shape(xs, ys, float(x), float(y))
        shell[host, :3] += shape[:, None] * force
        shell[host, 3] -= shape * z * force[1]
        shell[host, 4] += shape * z * force[0]
    return shell


def evaluate() -> dict:
    recon = json.loads(RECON.read_text())
    native = json.loads(NATIVE.read_text())
    if (recon["status"] != "EXPLORATORY_COMPLETE" or
            native["shell_bond_cells"] != 4 or
            native["line_multiplier_intervals"] != 2 or
            native["line_quadrature_order"] != 3):
        raise ValueError("saved six-channel x4/m2 identities changed")
    deck, _, coords, solid_rows, _, _ = _source(SOURCE)
    plate_nodes, bar_nodes = _element_domain_nodes(deck)
    if plate_nodes & bar_nodes:
        raise ValueError("external solid sides are not distinct")
    xs, ys = local_grid(4, transverse_cells=4)
    nodes = np.array([(x, y, 0.) for y in ys for x in xs])
    tangent, physical = raw_e4_tangent(xs, ys, thickness=.035)
    fixed = {6*j*len(xs)+axis for j in range(len(ys)) for axis in range(6)}
    free = np.array([i for i in range(len(tangent)) if i not in fixed])
    factor = linalg.lu_factor(tangent[np.ix_(free, free)], check_finite=True)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    shell_size = len(nodes) * 6
    records = {}
    for label in ("tip_mx", "tip_fz"):
        solid_case = recon["cases"][label]
        solid_action = _project_plate_action(
            coords, solid_rows, np.asarray(solid_case["dual_physical"]),
            plate_nodes, xs, ys)
        np.testing.assert_allclose(
            _generalized_wrench(solid_action, nodes),
            solid_case["plate_interface_wrench_N_Nm"], rtol=0, atol=1e-7)
        solid_state, solid_shell = _solve_shell(
            tangent, physical, solid_action, free, factor)
        comparisons = {}
        for family, kind in KINDS.items():
            source_family = native["families"][family]
            saved_case = source_family["cases"][label]
            trace, masses, _ = c1_hybrid_line_space(
                xs, ys, beam, kind=kind, intervals=2,
                thickness=.035, quadrature_order=3)
            np.testing.assert_allclose(masses,
                                       source_family["basis_integrals_m"],
                                       rtol=0, atol=1e-12)
            dual = np.asarray(saved_case["constraint_multiplier_material_N_Nm"])
            if dual.shape != (len(masses), 6):
                raise ValueError("native six-channel dual shape changed")
            native_action = (-trace[:, :shell_size].T @ dual.ravel()
                             ).reshape(-1, 6)
            np.testing.assert_allclose(
                _generalized_wrench(native_action, nodes),
                saved_case["interface_shell_wrench_N_Nm"],
                rtol=0, atol=1e-7)
            native_state, native_shell = _solve_shell(
                tangent, physical, native_action, free, factor)
            if (abs(native_shell["applied_final_state_work_j"] -
                    saved_case["interface_shell_work_j"]) > 1e-8 or
                    abs(native_shell["physical_shell_work_j"] -
                        saved_case["physical_shell_work_j"]) > 1e-8):
                raise ArithmeticError("saved native E4 work parity changed")
            cross_a = float(solid_action.ravel() @ native_state.ravel())
            cross_b = float(native_action.ravel() @ solid_state.ravel())
            if abs(cross_a-cross_b) > 1e-8:
                raise ArithmeticError("same-shell reciprocal work failed")
            samples = {}
            for x in (.9, .95, 1.):
                solid_face = np.array([_top_response(solid_state, xs, ys, x, y)
                                       for y in (-.05, 0., .05)])
                native_face = np.array([_top_response(native_state, xs, ys, x, y)
                                        for y in (-.05, 0., .05)])
                samples[str(x)] = {
                    "rms_action_response_difference_m": float(np.sqrt(
                        np.mean(np.sum((solid_face-native_face)**2, axis=1))))}
            comparisons[family] = {
                "native_action_shell": {key: value for key, value in
                                        native_shell.items() if key != "support_rows"},
                "native_total_load_work_J": saved_case["total_external_work_j"],
                "solid_total_load_work_J": solid_case["applied_load_work_J"],
                "same_shell_cross_work_defect_J": cross_a-cross_b,
                "samples": samples,
            }
        records[label] = {
            "solid_action_shell": {key: value for key, value in
                                   solid_shell.items() if key != "support_rows"},
            "solid_plate_work_J": solid_case["plate_interface_work_J"],
            "solid_plate_wrench_N_Nm": solid_case["plate_interface_wrench_N_Nm"],
            "comparisons": comparisons,
        }
    return {
        "classification": "same E4 shell replay of detached-solid and native six-channel plate actions; development only",
        "status": "EXPLORATORY_COMPLETE", "cases": records,
        "inputs_sha256": {str(path): digest(path) for path in (RECON, NATIVE)},
        "source_sha256": digest(Path(__file__)),
        "limitations": ["external plate action comes from a linear detached 3D solid model",
                        "native action uses retained B3 and E4 material duals",
                        "same-shell action comparison alone cannot allocate beam versus joint-law error",
                        "no line-space selection, mesh-convergence or F03/G0B acceptance"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve prior same-shell result")
    report = evaluate()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True,
                                      allow_nan=False) + "\n")
    print(json.dumps({"status": report["status"], "cases": {
        key: {family: {
            "solid_E4_work_J": value["solid_action_shell"]["applied_final_state_work_j"],
            "native_E4_work_J": case["native_action_shell"]["applied_final_state_work_j"]}
              for family, case in value["comparisons"].items()}
        for key, value in report["cases"].items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
