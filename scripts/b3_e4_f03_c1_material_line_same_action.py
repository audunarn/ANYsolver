"""Compare native and solid sides under one fixed matched interface dual.

The source load and constrained displacement are excluded from these
action-only component responses. This allocates a difference between
the E4/3D plate and B3/3D bar idealizations without claiming accuracy.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.sparse.linalg import spsolve

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts.b3_e4_f03_c1_material_line_p0_reference import integrated_rows
from scripts.b3_e4_f03_ccx_six_channel_compliance import _source
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_material_line_position import MaterialLinePosition
from scripts.b3_e4_f03_material_line_space_screen import _rows
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def _solve_component(stiffness, force, fixed):
    free = np.setdiff1d(np.arange(len(force)), np.asarray(sorted(fixed), dtype=int))
    u = np.zeros(len(force))
    operator = stiffness[free, :][:, free] if hasattr(stiffness, "tocsr") else np.asarray(stiffness)[np.ix_(free, free)]
    u[free] = (spsolve(operator, force[free]) if hasattr(operator, "tocsr")
               else np.linalg.solve(operator, force[free]))
    if not np.isfinite(u).all():
        raise ArithmeticError("nonfinite native component response")
    residual = stiffness@u-force
    error = float(np.linalg.norm(residual[free]) /
                  max(np.linalg.norm(force[free]), 1.))
    if error > 1e-9:
        raise ArithmeticError("native component equilibrium failed")
    return u, error


def evaluate(reconstruction_path: Path, source_root: Path,
             response_root: Path) -> dict:
    reconstruction = json.loads(reconstruction_path.read_text())
    if reconstruction["status"] != "EXPLORATORY_COMPLETE":
        raise ValueError("complete matched-law solid reconstruction required")
    deck, _, coords, _, _, _ = _source(source_root / "tip_mx")
    if reconstruction["cases"]["tip_mx"]["source_deck_sha256"] != digest(deck):
        raise ValueError("solid source deck changed")
    plate, bar = _element_domain_nodes(deck)
    solid_nodes, solid_rows, _ = integrated_rows(coords, plate, bar)
    unit = []
    for j, record in enumerate(reconstruction["unit_records"]):
        if j != record["channel"]:
            raise ValueError("ordered solid action inventory changed")
        stem = f"material-line-p0-{j}.frd"
        frd = response_root / f"channel-{j}" / stem
        if digest(frd) != record["frd_sha256"]:
            raise ValueError("solid action displacement changed")
        field = _read_frd_u(frd)
        if not set(solid_nodes) <= set(field):
            raise ValueError("incomplete solid action trace")
        unit.append(np.array([field[node] for node in solid_nodes]))
    unit = np.stack(unit)

    xs, ys = local_grid(4, transverse_cells=4)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    line = MaterialLinePosition(xs, ys, beam)
    space = LineMultiplierSpace("piecewise_constant", tuple(np.linspace(0., 1., 5)))
    native_rows, measure = _rows(line, space)
    if not np.allclose(measure, .025, rtol=0., atol=1e-12):
        raise ArithmeticError("native/solid interval measures differ")
    shell_k, _ = raw_e4_tangent(xs, ys, thickness=.035)
    shell_size = 6*line.shell_count
    if beam.tangent is None:
        raise ArithmeticError("assembled B3 tangent required")
    fixed_shell = {6*(j*len(xs)+i)+axis
                   for j in range(len(ys)) for i, x in enumerate(xs)
                   if abs(x+.5) < 1e-12 for axis in range(6)}
    fixed_beam = set(beam.context.fixed)
    scale = np.array([40000. if j % 6 < 3 else 4000.
                      for j in range(len(solid_rows))])
    plate_selector = np.array([node in plate for node in solid_nodes])
    cases = {}
    for label in ("tip_mx", "tip_fz"):
        dual = np.array(reconstruction["cases"][label]["dual_physical_line_density"])
        if dual.shape != (len(solid_rows),):
            raise ValueError("solid line dual inventory changed")
        coefficient = dual/scale
        solid_delta = -np.tensordot(coefficient, unit, axes=(0, 0))
        solid_force = -(solid_rows.T@dual).reshape(-1, 3)
        solid_shell_work = float(np.sum(solid_force[plate_selector]*
                                        solid_delta[plate_selector]))
        solid_beam_work = float(np.sum(solid_force[~plate_selector]*
                                       solid_delta[~plate_selector]))
        solid_total_work = float(np.sum(solid_force*solid_delta))
        if abs(solid_total_work-solid_shell_work-solid_beam_work) > 1e-9:
            raise ArithmeticError("solid action-only work partition failed")
        native_dual = (dual.reshape(4, 6)*measure[:, None]).ravel()
        native_force = -native_rows.T@native_dual
        shell_force, beam_force = native_force[:shell_size], native_force[shell_size:]
        shell_u, shell_error = _solve_component(shell_k, shell_force, fixed_shell)
        beam_u, beam_error = _solve_component(beam.tangent, beam_force, fixed_beam)
        shell_work = float(shell_force@shell_u)
        beam_work = float(beam_force@beam_u)
        if (abs(shell_work+native_dual@(native_rows[:, :shell_size]@shell_u)) > 1e-10 or
                abs(beam_work+native_dual@(native_rows[:, shell_size:]@beam_u)) > 1e-10):
            raise ArithmeticError("native trace/dual work mismatch")
        cases[label] = {
            "solid_shell_action_only_work_J": solid_shell_work,
            "native_shell_action_only_work_J": shell_work,
            "native_shell_vs_solid_relative": shell_work/solid_shell_work-1.,
            "solid_beam_action_only_work_J": solid_beam_work,
            "native_beam_action_only_work_J": beam_work,
            "native_beam_vs_solid_relative": beam_work/solid_beam_work-1.,
            "solid_total_action_only_work_J": solid_total_work,
            "native_shell_equilibrium_ratio": shell_error,
            "native_beam_equilibrium_ratio": beam_error,
        }
    return {
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "classification": "matched line-dual separate-component action-only comparison",
        "solid_reconstruction_sha256": digest(reconstruction_path),
        "solid_source_deck_sha256": digest(deck),
        "solid_action_source_commit": reconstruction["unit_source_commit"],
        "native_shell_cells": 4,
        "native_beam_half_cells": 12,
        "native_interval_measures_m": measure.tolist(),
        "cases": cases,
        "limitations": [
            "same projected line dual, but E4 and B3 versus 3D plate/bar idealizations differ",
            "action-only linear component compliance, not a loaded coupled solution",
            "no connection-law acceptance or multiplier-space selection",
            "not F03 or G0B acceptance",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reconstruction", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--responses", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve prior same-action comparison")
    result = evaluate(args.reconstruction.resolve(), args.source_root.resolve(),
                      args.responses.resolve())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "cases": {
        key: {"shell_relative": value["native_shell_vs_solid_relative"],
              "beam_relative": value["native_beam_vs_solid_relative"]}
        for key, value in result["cases"].items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
