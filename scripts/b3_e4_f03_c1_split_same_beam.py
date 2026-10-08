"""Replay global-six, split-twelve and native P0 actions on one retained B3."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts.b3_e4_f03_c1_six_channel_same_beam import (
    _physical_wrench, _solid_action_on_beam, _solve_beam,
)
from scripts.b3_e4_f03_c1_six_channel_same_shell import (
    BASE, NATIVE, RECON,
)
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_distributed_surface_finite import c1_hybrid_line_space
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


SPLIT = (BASE / "f03-c1-split-six-channel-dev-20260927-v1/"
         "reconstruction_v2.json")


def _split_action_on_beam(beam, dual, order):
    if dual.shape != (12,) or order not in (3, 5):
        raise ValueError("twelve duals and bounded quadrature required")
    roots, weights = np.polynomial.legendre.leggauss(order)
    points = (.9, .925, .95, .975, 1.)
    dofs = np.zeros(beam.context.count)
    force = np.zeros(3)
    moment = np.zeros(3)
    state = beam.context.initial.mechanical
    for x0, x1 in zip(points[:-1], points[1:]):
        for xi, wx in zip(roots, weights):
            x = (x0+x1)/2+(x1-x0)*float(xi)/2
            interval = 0 if x < .95 else 1
            physical = dual[6*interval:6*interval+6]
            element, cell, fraction, _ = beam._locate(x)
            port = NativeHalfCellSpatialPort(
                beam.context, element, cell, fraction)
            high, low, frame = port.pose_pair(state)
            axis = high+low
            if (np.linalg.norm(axis-np.array((x,0.,.0675))) > 2e-9 or
                    np.linalg.norm(frame-np.eye(3)) > 2e-7):
                raise ValueError("split solid/native bar reference mismatch")
            tangent = port.tangent(state)
            for eta, wy in zip(roots, weights):
                y = .05*float(eta)
                area = (x1-x0)*.1*float(wx*wy)/4
                variance_y = .1**2/12
                bottom = np.array((
                    physical[0]-physical[5]*y/variance_y-physical[4]/.1,
                    physical[1],
                    physical[2]+physical[3]*y/variance_y))
                top = np.array((physical[4]/.1, 0., 0.))
                for z_rel, density in ((-.05, bottom), (.05, top)):
                    position = axis+frame@np.array((0., y, z_rel))
                    local_force = density*(area/.005)
                    local_moment = np.cross(position-axis, local_force)
                    dofs += tangent.T@np.r_[local_force, local_moment]
                    force += local_force
                    moment += np.cross(position, local_force)
    return dofs, np.r_[force, moment]


def evaluate():
    split = json.loads(SPLIT.read_text())
    global_six = json.loads(RECON.read_text())
    native = json.loads(NATIVE.read_text())
    if (split["status"] != "EXPLORATORY_COMPLETE" or
            global_six["status"] != "EXPLORATORY_COMPLETE" or
            native["shell_bond_cells"] != 4 or
            native["line_multiplier_intervals"] != 2):
        raise ValueError("three matched development inputs required")
    xs, ys = local_grid(4, transverse_cells=4)
    shell_size = len(xs)*len(ys)*6
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
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
        split_dual = np.asarray(split_case["dual_physical"])
        split_action, split_wrench = _split_action_on_beam(
            beam, split_dual, 5)
        lower, _ = _split_action_on_beam(beam, split_dual, 3)
        quadrature_defect = float(np.linalg.norm(split_action-lower)/
                                  max(1., np.linalg.norm(split_action)))
        if quadrature_defect > 1e-8:
            raise ArithmeticError("split B3 action quadrature failed")
        global_action, global_wrench = _solid_action_on_beam(
            beam, np.asarray(global_case["dual_physical"]), 5)
        native_dual = np.asarray(saved["constraint_multiplier_material_N_Nm"])
        native_action = -trace[:, shell_size:].T@native_dual.ravel()
        for action, wrench in (
                (split_action, split_case["bar_interface_wrench_N_Nm"]),
                (global_action, global_case["bar_interface_wrench_N_Nm"]),
                (native_action, saved["interface_beam_wrench_N_Nm"])):
            np.testing.assert_allclose(_physical_wrench(beam, action),
                                       wrench, rtol=0, atol=1e-7)
        np.testing.assert_allclose(split_wrench,
                                   split_case["bar_interface_wrench_N_Nm"],
                                   rtol=0, atol=1e-7)
        np.testing.assert_allclose(global_wrench,
                                   global_case["bar_interface_wrench_N_Nm"],
                                   rtol=0, atol=1e-7)
        split_state, split_result = _solve_beam(beam, split_action)
        _, global_result = _solve_beam(beam, global_action)
        native_state, native_result = _solve_beam(beam, native_action)
        cross = float(split_action@native_state-native_action@split_state)
        if abs(cross) > 1e-8:
            raise ArithmeticError("split/native same-beam reciprocity failed")
        cases[label] = {
            "global_six_beam_work_J": global_result["action_work_J"],
            "split_twelve_beam_work_J": split_result["action_work_J"],
            "native_p0_beam_work_J": native_result["action_work_J"],
            "split_native_cross_work_defect_J": cross,
            "split_quadrature_relative_defect": quadrature_defect,
            "split_bar_wrench_N_Nm": split_case["bar_interface_wrench_N_Nm"],
            "global_bar_wrench_N_Nm": global_case["bar_interface_wrench_N_Nm"],
            "native_bar_wrench_N_Nm": saved["interface_beam_wrench_N_Nm"],
        }
    return {
        "classification": "three physical actions on the same retained B3 beam; development only",
        "status": "EXPLORATORY_COMPLETE", "cases": cases,
        "inputs_sha256": {str(path): digest(path)
                          for path in (SPLIT, RECON, NATIVE)},
        "source_sha256": digest(Path(__file__)),
        "limitations": ["same beam separates action shape, not continuum fidelity",
                        "open half-cell ports avoid arbitrary shared-node side allocation",
                        "raw mixed-unit covector norms are not used for physical comparison",
                        "one grid, no multiplier selection or F03/G0B acceptance"],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve previous split same-beam result")
    report = evaluate()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n")
    print(json.dumps({key: value["split_twelve_beam_work_J"]
                      for key, value in report["cases"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
