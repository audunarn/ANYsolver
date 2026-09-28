"""Compare saved same-action solid/E4 shell traces at fixed material stations."""

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


def thickness_mean_and_director(top, bottom, thickness):
    """Return midplane translation and small physical rx/ry in +z frame."""
    top = np.asarray(top, dtype=float)
    bottom = np.asarray(bottom, dtype=float)
    if (top.shape != (3,) or bottom.shape != (3,) or
            not np.isfinite(top).all() or not np.isfinite(bottom).all() or
            not np.isfinite(thickness) or thickness <= 0.):
        raise ValueError("finite three-component face fields and positive thickness required")
    chord = (top-bottom)/thickness
    return .5*(top+bottom), np.array((-chord[1], chord[0]))


def evaluate(reconstruction_path: Path) -> dict:
    solid = _validated_solid_reconstruction(reconstruction_path)
    source_root = Path(solid["source_root"])
    response_root = Path(solid["response_root"])
    deck, _, coords, _, _, _ = _source(source_root / "tip_mx")
    if digest(deck) != solid["cases"]["tip_mx"]["source_deck_sha256"]:
        raise ValueError("matched solid source deck changed")
    plate, bar = _element_domain_nodes(deck)
    solid_nodes, _, ports = integrated_rows(coords, plate, bar)
    all_nodes = tuple(sorted(coords))
    index = {node: i for i, node in enumerate(all_nodes)}
    unit = []
    for channel, record in enumerate(solid["unit_records"]):
        frd = response_root / f"channel-{channel}" / f"material-line-p0-{channel}.frd"
        if record["channel"] != channel or digest(frd) != record["frd_sha256"]:
            raise ValueError("solid unit-action field identity changed")
        field = _read_frd_u(frd)
        if set(field) != set(coords):
            raise ValueError("incomplete solid unit-action field")
        unit.append(np.array([field[node] for node in all_nodes]))
    unit = np.stack(unit)

    xs, ys = local_grid(4, transverse_cells=4)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um", assemble=False)
    line = MaterialLinePosition(xs, ys, beam)
    space = LineMultiplierSpace("piecewise_constant", tuple(np.linspace(0., 1., 5)))
    rows, measure = _rows(line, space)
    if rows.shape[0] != 24 or not np.allclose(measure, .025, rtol=0., atol=1e-12):
        raise ArithmeticError("matched native P0 layout changed")
    if len(line.stations) != 12:
        raise ArithmeticError("matched three-point station layout changed")
    tangent, _ = raw_e4_tangent(xs, ys, thickness=.035)
    shell_size = 6*line.shell_count
    fixed = {6*(j*len(xs)+i)+axis for j in range(len(ys))
             for i, x in enumerate(xs) if abs(x+.5) < 1e-12
             for axis in range(6)}
    position = line.reference_jacobian().reshape(12, 3, -1)
    orientation = line.reference_orientation_jacobian().reshape(12, 3, -1)
    scale = np.array([40000. if j % 6 < 3 else 4000. for j in range(24)])
    cases = {}
    for label in ("tip_mx", "tip_fz"):
        density = np.asarray(solid["cases"][label]["dual_physical_line_density"])
        coefficient = density/scale
        solid_delta = -np.tensordot(coefficient, unit, axes=(0, 0))
        dual = (density.reshape(4, 6)*measure[:, None]).ravel()
        shell_force = -rows[:, :shell_size].T@dual
        shell_u, equilibrium = _solve_component(tangent, shell_force, fixed)
        interval = []
        for i, group in enumerate(ports):
            solid_integral = np.zeros(6)
            native_integral = np.zeros(6)
            maximum_scaled_gap = 0.
            for j, (weight, port) in enumerate(group):
                station = line.stations[3*i+j]
                if abs(port.station_x_m-station.x) > 1e-12 or abs(weight-station.weight) > 1e-12:
                    raise ArithmeticError("solid/native material stations changed")
                values = solid_delta[[index[node] for node in port.node_ids]].ravel()
                # The gap uses shell-minus-beam position and beam-minus-shell
                # rotation. Compare each shell's contribution in gap rows.
                solid_trace = np.r_[port.shell_top_jacobian@values,
                                    -port.shell_orientation_jacobian@values]
                native_trace = np.r_[position[3*i+j, :, :shell_size]@shell_u,
                                     orientation[3*i+j, :, :shell_size]@shell_u]
                difference = native_trace-solid_trace
                maximum_scaled_gap = max(maximum_scaled_gap,
                    float(np.max(np.abs(difference*np.array((1., 1., 1., .1, .1, .1))))))
                solid_integral += weight*solid_trace
                native_integral += weight*native_trace
            physical_dual = density.reshape(4, 6)[i]
            solid_work = float(-physical_dual@solid_integral)
            native_work = float(-physical_dual@native_integral)
            interval.append({
                "x_interval_m": [float(.9+.025*i), float(.925+.025*i)],
                "solid_shell_action_work_J": solid_work,
                "native_shell_action_work_J": native_work,
                "native_minus_solid_work_J": native_work-solid_work,
                "maximum_station_gap_with_0p1m_moment_scale_m": maximum_scaled_gap,
                "integrated_gap_side_difference_m_rad_times_m": (
                    native_integral-solid_integral).tolist(),
            })
        total_solid = sum(item["solid_shell_action_work_J"] for item in interval)
        total_native = sum(item["native_shell_action_work_J"] for item in interval)
        if not np.isclose(total_native, float(shell_force@shell_u),
                          rtol=1e-10, atol=1e-12):
            raise ArithmeticError("native shell trace work changed")
        fixed_distance = []
        shell_nodes = line.reference_nodes
        nodal = shell_u.reshape(-1, 6)
        for x in (.5, .75, .9, .95):
            shell_ids = np.flatnonzero(
                (np.abs(shell_nodes[:, 0]-x) < 1e-10) &
                (np.abs(shell_nodes[:, 1]) < 1e-10))
            face_ids = {}
            for side, z in (("top", .0175), ("bottom", -.0175)):
                face_ids[side] = [node for node in plate
                                  if abs(coords[node][0]-x) < 1e-10 and
                                  abs(coords[node][1]) < 1e-10 and
                                  abs(coords[node][2]-z) < 1e-10]
            if (len(shell_ids) != 1 or len(face_ids["top"]) != 1 or
                    len(face_ids["bottom"]) != 1):
                raise ValueError("fixed-distance physical plate/shell probe changed")
            top = solid_delta[index[face_ids["top"][0]]]
            bottom = solid_delta[index[face_ids["bottom"][0]]]
            solid_mid, solid_rotation = thickness_mean_and_director(
                top, bottom, .035)
            native_mid = nodal[int(shell_ids[0]), :3]
            native_rotation = nodal[int(shell_ids[0]), 3:5]
            fixed_distance.append({
                "x_m": x,
                "solid_thickness_mean_translation_m": solid_mid.tolist(),
                "native_midplane_translation_m": native_mid.tolist(),
                "solid_director_rotation_xy_rad": solid_rotation.tolist(),
                "native_director_rotation_xy_rad": native_rotation.tolist(),
                "translation_difference_m": (native_mid-solid_mid).tolist(),
                "director_rotation_difference_rad": (
                    native_rotation-solid_rotation).tolist(),
            })
        cases[label] = {
            "intervals": interval,
            "fixed_distance_probes": fixed_distance,
            "solid_shell_action_work_J": total_solid,
            "native_shell_action_work_J": total_native,
            "native_shell_equilibrium_ratio": equilibrium,
        }
    return {
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "classification": "fixed-action shell material-station trace comparison",
        "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                                 text=True).strip(),
        "solid_reconstruction_sha256": digest(reconstruction_path),
        "solid_unit_field_count": len(unit),
        "solid_action_node_count": len(solid_nodes),
        "cases": cases,
        "limitations": [
            "same P0 action but E4 and 3D plate kinematics/supports differ",
            "linear fixed-dual action-only responses, not coupled loaded sensitivity",
            "interval work terms may cancel; they are not independent strain energies",
            "four fixed-distance probes compare physical poses, not stress convergence",
            "not F03/G0B acceptance or multiplier selection",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reconstruction", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve prior shell trace result")
    result = evaluate(args.reconstruction.resolve())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({label: [item["native_minus_solid_work_J"]
                              for item in case["intervals"]]
                      for label, case in result["cases"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
