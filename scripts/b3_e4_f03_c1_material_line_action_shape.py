"""Decompose saved matched-line plate action work without a solver run.

The longitudinal six-channel mean and zero-mean parts use the same
physical P0 line dual. This diagnoses action-shape sensitivity; it does
not qualify an interface law or select a multiplier space.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

import numpy as np

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts.b3_e4_f03_c1_material_line_p0_reference import integrated_rows
from scripts.b3_e4_f03_c1_material_line_same_action import _solve_component
from scripts.b3_e4_f03_ccx_six_channel_compliance import _source
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_material_line_position import MaterialLinePosition
from scripts.b3_e4_f03_material_line_space_screen import _rows
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


def _parts(force, displacement):
    low, high = force
    u_low, u_high = displacement
    return {
        "mean_self_J": float(low @ u_low),
        "mean_variation_cross_J": float(low @ u_high + high @ u_low),
        "variation_self_J": float(high @ u_high),
    }


def evaluate(reconstruction_path: Path, same_action_path: Path) -> dict:
    reconstruction = json.loads(reconstruction_path.read_text())
    same_action = json.loads(same_action_path.read_text())
    if (reconstruction["status"] != "EXPLORATORY_COMPLETE" or
            same_action["solid_reconstruction_sha256"] != digest(reconstruction_path)):
        raise ValueError("unchanged completed source comparison required")
    source_root = Path(reconstruction["source_root"])
    response_root = Path(reconstruction["response_root"])
    deck, _, coords, _, _, _ = _source(source_root / "tip_mx")
    if digest(deck) != same_action["solid_source_deck_sha256"]:
        raise ValueError("solid source deck changed")
    plate, bar = _element_domain_nodes(deck)
    solid_nodes, solid_rows, _ = integrated_rows(coords, plate, bar)
    plate_selector = np.repeat([node in plate for node in solid_nodes], 3)
    if solid_rows.shape[0] != 24 or int(np.sum(plate_selector)) == 0:
        raise ValueError("four-interval solid plate inventory changed")
    scale = np.array([40000. if j % 6 < 3 else 4000.
                      for j in range(24)])
    unit = []
    for j, record in enumerate(reconstruction["unit_records"]):
        if record["channel"] != j:
            raise ValueError("solid unit response order changed")
        frd = response_root / f"channel-{j}" / f"material-line-p0-{j}.frd"
        if digest(frd) != record["frd_sha256"]:
            raise ValueError("solid unit field changed")
        field = _read_frd_u(frd)
        if not set(solid_nodes) <= set(field):
            raise ValueError("solid unit field incomplete")
        unit.append(np.array([field[node] for node in solid_nodes]).ravel())
    unit = np.stack(unit)

    xs, ys = local_grid(4, transverse_cells=4)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    line = MaterialLinePosition(xs, ys, beam)
    space = LineMultiplierSpace("piecewise_constant", tuple(np.linspace(0., 1., 5)))
    native_rows, measure = _rows(line, space)
    if not np.allclose(measure, .025, rtol=0., atol=1e-12):
        raise ArithmeticError("native and solid interval measures differ")
    shell_k, _ = raw_e4_tangent(xs, ys, thickness=.035)
    shell_size = 6*line.shell_count
    fixed_shell = {6*(j*len(xs)+i)+axis
                   for j in range(len(ys)) for i, x in enumerate(xs)
                   if abs(x+.5) < 1e-12 for axis in range(6)}

    cases = {}
    for label in ("tip_mx", "tip_fz"):
        dual = np.asarray(reconstruction["cases"][label]["dual_physical_line_density"])
        if dual.shape != (24,):
            raise ValueError("dual shape changed")
        density = dual.reshape(4, 6)
        mean = np.broadcast_to(np.mean(density, axis=0), density.shape).ravel().copy()
        variation = dual-mean
        if not np.allclose(mean+variation, dual, rtol=0., atol=1e-10):
            raise ArithmeticError("dual decomposition changed the action")
        solid_force = []
        solid_u = []
        native_force = []
        native_u = []
        for part in (mean, variation):
            solid_force.append((-(solid_rows.T@part))[plate_selector])
            solid_u.append((-(part/scale)@unit)[plate_selector])
            shell_force = -(native_rows.T@(part.reshape(4, 6)*measure[:, None]).ravel())[:shell_size]
            response, equilibrium = _solve_component(shell_k, shell_force, fixed_shell)
            if equilibrium > 1e-9:
                raise ArithmeticError("native shell equilibrium failed")
            native_force.append(shell_force)
            native_u.append(response)
        solid = _parts(solid_force, solid_u)
        native = _parts(native_force, native_u)
        solid_total = sum(solid.values())
        native_total = sum(native.values())
        previous = same_action["cases"][label]
        if (abs(solid_total-previous["solid_shell_action_only_work_J"]) > 1e-9 or
                abs(native_total-previous["native_shell_action_only_work_J"]) > 1e-9):
            raise ArithmeticError("decomposition does not recover saved total work")
        difference = {key: native[key]-solid[key] for key in solid}
        cases[label] = {
            "solid_plate": solid,
            "native_E4": native,
            "native_minus_solid_J": difference,
            "solid_reconstructed_total_J": solid_total,
            "native_reconstructed_total_J": native_total,
            "mean_density": mean.reshape(4, 6)[0].tolist(),
            "maximum_zero_mean_density_sum": float(np.max(np.abs(
                variation.reshape(4, 6).sum(axis=0)))),
        }
    return {
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "classification": "saved fixed-line-dual plate action-shape decomposition",
        "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                                 text=True).strip(),
        "solid_reconstruction_sha256": digest(reconstruction_path),
        "same_action_sha256": digest(same_action_path),
        "solid_source_deck_sha256": digest(deck),
        "unit_frd_sha256": [r["frd_sha256"] for r in reconstruction["unit_records"]],
        "cases": cases,
        "limitations": [
            "mean/variation is a descriptive longitudinal action split, not a physical material law",
            "same fixed dual and saved linear action fields; no new external execution",
            "different native and 3D plate discretizations, support spaces and theories",
            "not interface-space selection, F03 or G0B acceptance",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reconstruction", type=Path, required=True)
    parser.add_argument("--same-action", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve prior action-shape result")
    result = evaluate(args.reconstruction.resolve(), args.same_action.resolve())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({label: case["native_minus_solid_J"]
                      for label, case in result["cases"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
