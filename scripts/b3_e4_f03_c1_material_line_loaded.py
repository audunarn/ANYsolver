"""Bounded native C1 material-line solve against saved same-law solid P0.

This preserves the existing 1,900-row developmental limit. It is not a
production sparse owner, interface-space selection, or F03 acceptance.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

import numpy as np
from scipy import sparse

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_material_line_loaded import _scales, _solve
from scripts.b3_e4_f03_material_line_position import MaterialLinePosition
from scripts.b3_e4_f03_material_line_space_screen import _rows
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def evaluate(reconstruction_path: Path) -> dict:
    solid = json.loads(reconstruction_path.read_text())
    if solid["status"] != "EXPLORATORY_COMPLETE":
        raise ValueError("completed same-law solid P0 reconstruction required")
    xs, ys = local_grid(4, transverse_cells=4)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    line = MaterialLinePosition(xs, ys, beam)
    space = LineMultiplierSpace("piecewise_constant", tuple(np.linspace(0., 1., 5)))
    rows, measure = _rows(line, space)
    if rows.shape[0] != 24 or not np.allclose(measure, .025, rtol=0., atol=1e-12):
        raise ArithmeticError("same P0 m4 line layout changed")
    shell_k, _ = raw_e4_tangent(xs, ys, thickness=.035)
    shell_size = 6*line.shell_count
    if beam.tangent is None or beam.residual is None:
        raise ArithmeticError("assembled native B3 operator required")
    primal = sparse.block_diag((sparse.csr_matrix(shell_k), beam.tangent),
                               format="csr")
    residual = np.r_[np.zeros(shell_size), beam.residual]
    if rows.shape[1] != primal.shape[0]:
        raise ArithmeticError("line omits native retained B3 coordinates")
    shell_fixed = {6*(j*len(xs)+i)+axis for j in range(len(ys))
                   for i, x in enumerate(xs) if abs(x+.5) < 1e-12
                   for axis in range(6)}
    beam_fixed = {shell_size+int(index) for index in beam.context.fixed}
    free = np.array(sorted(set(range(primal.shape[0]))-shell_fixed-beam_fixed))
    scales, energy_scale = _scales(shell_size, beam, free, row_count=24)
    terminal = shell_size+6*beam.n_half_cells
    nodes = line.reference_nodes
    count = len(line.stations)
    position = line.reference_jacobian().reshape(count, 3, -1)
    orientation = line.reference_orientation_jacobian().reshape(count, 3, -1)
    cases = {}
    for label, axis, magnitude in (("tip_mx", 3, 100.),
                                    ("tip_fz", 2, -1000.)):
        load = np.zeros(primal.shape[0])
        load[terminal+axis] = magnitude
        state, equation, diagnostics = _solve(
            primal, residual, rows, free, scales, energy_scale, load)
        gap = rows@state
        if np.max(np.abs(gap)) > 1e-9:
            raise ArithmeticError("accepted weak material-line gap exceeds limit")
        # A solved multiplier is the dual of a mean gap. Its physical
        # piecewise-constant line density is lambda / interval length.
        station_gap = np.concatenate((
            np.einsum("kij,j->ki", position, state),
            np.einsum("kij,j->ki", orientation, state)), axis=1)
        # _solve does not return its multiplier; recover it from equilibrium
        # on free rows, keeping the exact retained-variable representation.
        reduced = rows[:, free].T
        right = (load-residual-primal@state)[free]
        dual, _, rank, _ = np.linalg.lstsq(reduced, right, rcond=1e-10)
        if rank != 24 or np.linalg.norm(reduced@dual-right) > (
                1e-8*max(1., np.linalg.norm(load[free]))):
            raise ArithmeticError("native material-line multiplier recovery failed")
        physical_interface = -(rows.T@dual)
        interface_work = float(physical_interface@state)
        if abs(interface_work) > 1e-8:
            raise ArithmeticError("material-line interface work does not cancel")
        interface = physical_interface[:shell_size].reshape(-1, 6)
        shell_force = interface[:, :3].sum(axis=0)
        shell_moment = (np.cross(nodes, interface[:, :3])+
                        interface[:, 3:]).sum(axis=0)
        support = equation[:shell_size].reshape(-1, 6)
        support_force = support[:, :3].sum(axis=0)
        support_moment = (np.cross(nodes, support[:, :3])+
                          support[:, 3:]).sum(axis=0)
        balance = np.r_[shell_force+support_force,
                        shell_moment+support_moment]
        if max(np.max(np.abs(balance[:3]))/1000.,
               np.max(np.abs(balance[3:]))/100.) > 1e-8:
            raise ArithmeticError("material-line shell support balance failed")
        work = float(load@state)
        cases[label] = {
            "diagnostics": diagnostics,
            "tip_rx_rad": float(state[terminal+3]),
            "tip_uz_m": float(state[terminal+2]),
            "applied_load_work_J": work,
            "solid_applied_load_work_J": float(solid["cases"][label][
                "applied_load_work_J"]),
            "native_vs_solid_applied_work_relative": work/float(
                solid["cases"][label]["applied_load_work_J"])-1.,
            "maximum_integrated_weak_gap": float(np.max(np.abs(gap))),
            "maximum_station_position_gap_m": float(np.max(np.abs(
                station_gap[:, :3]))),
            "maximum_station_orientation_gap_rad": float(np.max(np.abs(
                station_gap[:, 3:]))),
            "complete_interface_work_J": interface_work,
            "physical_line_dual_density": (dual.reshape(4, 6)/
                                           measure[:, None]).tolist(),
            "native_shell_interface_wrench_N_Nm": np.r_[shell_force,
                                                        shell_moment].tolist(),
            "native_shell_support_wrench_N_Nm": np.r_[support_force,
                                                      support_moment].tolist(),
            "solid_plate_interface_wrench_N_Nm": solid["cases"][label][
                "plate_interface_wrench_N_Nm"],
        }
    return {
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "classification": "same P0 material-line law, distinct native and 3D constitutive domains",
        "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                                 text=True).strip(),
        "solid_reconstruction_sha256": digest(reconstruction_path),
        "geometry": "Q4 x4/y4, B3-12, 35 mm plate, 100 mm square beam, 67.5 mm axis",
        "line_intervals": 4,
        "line_measure_m": measure.tolist(),
        "cases": cases,
        "limitations": [
            "same linear P0 trace law, but E4/B3 and 3D plate/bar mechanics differ",
            "terminal native wrench and distributed solid tip-face load differ",
            "small supported development solve, not mesh-ratio stability or accuracy",
            "not F03 or G0B acceptance",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reconstruction", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve previous native material-line result")
    result = evaluate(args.reconstruction.resolve())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({key: {"work_J": value["applied_load_work_J"],
                            "relative": value["native_vs_solid_applied_work_relative"]}
                      for key, value in result["cases"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
