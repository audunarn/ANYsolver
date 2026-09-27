"""Replay the resolved-solid sided action and native action on one B3 beam.

The solid KKT action is known as a surface density before Q8 assembly. It
is integrated on open native half-cells, avoiding arbitrary allocation of
shared solid nodal loads to discontinuous one-sided retained B3 ports.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.sparse.linalg import spsolve

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts.b3_e4_f03_c1_six_channel_same_shell import (
    BASE, KINDS, NATIVE, RECON,
)
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_distributed_surface_finite import c1_hybrid_line_space
from scripts.b3_e4_f03_plate_patch_work import local_grid
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def _solid_action_on_beam(beam, dual: np.ndarray, order: int):
    """Integrate -C_bar^T dual over the exact terminal surface patch."""
    if dual.shape != (6,) or order not in (3, 5):
        raise ValueError("six physical duals and bounded quadrature required")
    roots, weights = np.polynomial.legendre.leggauss(order)
    points = sorted({.9, .95, 1., .925, .975})
    dofs = np.zeros(beam.context.count)
    force = np.zeros(3)
    moment = np.zeros(3)
    state = beam.context.initial.mechanical
    for x0, x1 in zip(points[:-1], points[1:]):
        for xi, wx in zip(roots, weights):
            x = (x0+x1)/2 + (x1-x0)*float(xi)/2
            element, cell, fraction, _ = beam._locate(x)
            port = NativeHalfCellSpatialPort(
                beam.context, element, cell, fraction)
            high, low, frame = port.pose_pair(state)
            axis = high+low
            if (np.linalg.norm(axis-np.array((x, 0., .0675))) > 2e-9 or
                    np.linalg.norm(frame-np.eye(3)) > 2e-7):
                raise ValueError("terminal B3 geometry differs from flat solid patch")
            tangent = port.tangent(state)
            for eta, wy in zip(roots, weights):
                y = .05*float(eta)
                # 1/.01 converts mean-action multipliers to area density.
                area = (x1-x0)*.1*float(wx*wy)/4
                bottom = np.array((dual[0]-dual[5]*y/(.1**2/12)-dual[4]/.1,
                                   dual[1],
                                   dual[2]+dual[3]*y/(.1**2/12)))
                top = np.array((dual[4]/.1, 0., 0.))
                for z_rel, density in ((-.05, bottom), (.05, top)):
                    position = axis + frame@np.array((0., y, z_rel))
                    local_force = density*(area/.01)
                    local_moment = np.cross(position-axis, local_force)
                    dofs += tangent.T@np.r_[local_force, local_moment]
                    force += local_force
                    moment += np.cross(position, local_force)
    return dofs, np.r_[force, moment]


def _solve_beam(beam, rhs):
    tangent = beam.tangent.tocsr()
    fixed = set(beam.context.fixed)
    free = np.array([i for i in range(beam.context.count) if i not in fixed])
    solution = np.zeros(beam.context.count)
    solution[free] = spsolve(tangent[free][:, free], rhs[free])
    residual = tangent@solution-rhs
    defect = float(np.linalg.norm(residual[free]) /
                   max(1., np.linalg.norm(rhs[free])))
    if not np.isfinite(solution).all() or defect > 1e-9:
        raise ArithmeticError("retained B3 beam-only solve failed")
    return solution, {"action_work_J": float(rhs@solution),
                      "free_relative_residual": defect,
                      "root_reaction_norm": float(np.linalg.norm(residual[list(fixed)]))}


def _physical_wrench(beam, generalized):
    """Test a retained-coordinate covector on global rigid variations."""
    nodes = (beam.context.initial.mechanical.positions +
             beam.context.initial.mechanical.position_low)
    result = np.zeros(6)
    for axis, direction in enumerate(np.eye(3)):
        shift = np.zeros(beam.context.count)
        spin = np.zeros(beam.context.count)
        for node, location in enumerate(nodes):
            start = 6*node
            shift[start:start+3] = direction
            spin[start:start+3] = np.cross(direction, location)
            spin[start+3:start+6] = direction
        for element in range(beam.n_half_cells//2):
            for cell in (0, 1):
                start = beam.context.nodal_count+24*element+3*cell
                spin[start:start+3] = direction
        result[axis] = generalized@shift
        result[3+axis] = generalized@spin
    return result


def evaluate() -> dict:
    recon = json.loads(RECON.read_text())
    native = json.loads(NATIVE.read_text())
    if (recon["status"] != "EXPLORATORY_COMPLETE" or
            native["shell_bond_cells"] != 4 or
            native["line_multiplier_intervals"] != 2):
        raise ValueError("saved six-channel comparison identities changed")
    xs, ys = local_grid(4, transverse_cells=4)
    shell_size = len(xs)*len(ys)*6
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    cases = {}
    for label in ("tip_mx", "tip_fz"):
        external = recon["cases"][label]
        dual = np.asarray(external["dual_physical"], dtype=float)
        solid_action, solid_wrench = _solid_action_on_beam(beam, dual, 5)
        lower, _ = _solid_action_on_beam(beam, dual, 3)
        quadrature_defect = float(np.linalg.norm(solid_action-lower) /
                                  max(1., np.linalg.norm(solid_action)))
        if quadrature_defect > 1e-8:
            raise ArithmeticError("solid action B3 projection is not quadrature-stable")
        np.testing.assert_allclose(solid_wrench,
                                   external["bar_interface_wrench_N_Nm"],
                                   rtol=0., atol=1e-7)
        np.testing.assert_allclose(_physical_wrench(beam, solid_action),
                                   solid_wrench, rtol=0., atol=1e-7)
        solid_state, solid_beam = _solve_beam(beam, solid_action)
        comparisons = {}
        for family, kind in KINDS.items():
            saved = native["families"][family]
            case = saved["cases"][label]
            trace, masses, _ = c1_hybrid_line_space(
                xs, ys, beam, kind=kind, intervals=2,
                thickness=.035, quadrature_order=3)
            np.testing.assert_allclose(masses, saved["basis_integrals_m"],
                                       rtol=0., atol=1e-12)
            native_dual = np.asarray(case["constraint_multiplier_material_N_Nm"])
            native_action = -trace[:, shell_size:].T@native_dual.ravel()
            np.testing.assert_allclose(
                _physical_wrench(beam, native_action),
                case["interface_beam_wrench_N_Nm"], rtol=0., atol=1e-7)
            native_state, native_beam = _solve_beam(beam, native_action)
            cross_a = float(solid_action@native_state)
            cross_b = float(native_action@solid_state)
            if abs(cross_a-cross_b) > 1e-8:
                raise ArithmeticError("same-beam reciprocal work failed")
            comparisons[family] = {
                "native_action_beam": native_beam,
                "same_beam_cross_work_defect_J": cross_a-cross_b,
                "action_vector_relative_difference": float(
                    np.linalg.norm(native_action-solid_action) /
                    max(1., np.linalg.norm(solid_action))),
            }
        cases[label] = {
            "solid_action_beam": solid_beam,
            "solid_bar_work_J": external["bar_interface_work_J"],
            "solid_bar_wrench_N_Nm": solid_wrench.tolist(),
            "quadrature_relative_defect": quadrature_defect,
            "comparisons": comparisons,
        }
    return {
        "classification": "same retained B3 beam replay of detached-solid and native six-channel bar actions; development only",
        "status": "EXPLORATORY_COMPLETE", "cases": cases,
        "inputs_sha256": {str(path): digest(path) for path in (RECON, NATIVE)},
        "source_sha256": digest(Path(__file__)),
        "limitations": ["solid action is mapped through a rigid native B3 section trace",
                        "bar solid warping and local continuum section distortion remain distinct",
                        "one-sided half-cell ports are sampled only in their open intervals",
                        "no mesh convergence, line-space choice, physical fidelity or F03/G0B acceptance"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve previous same-beam result")
    report = evaluate()
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True,
                                      allow_nan=False) + "\n")
    print(json.dumps({"status": report["status"], "cases": {
        key: {family: {"solid_B3_work_J": value["solid_action_beam"]["action_work_J"],
                       "native_B3_work_J": case["native_action_beam"]["action_work_J"]}
              for family, case in value["comparisons"].items()}
        for key, value in report["cases"].items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
