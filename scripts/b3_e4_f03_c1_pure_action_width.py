"""Bounded width/thickness probes under the saved same-law pure P0 actions.

This is a component response of an open interface, not a coupled/contact
state or a qualification of the native connection or multiplier space.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

from scripts.b3_e4_f03_c1_material_line_loaded import _validated_solid_reconstruction
from scripts.b3_e4_f03_c1_material_line_p0_reference import integrated_rows
from scripts.b3_e4_f03_c1_material_line_same_action import _solve_component
from scripts.b3_e4_f03_ccx_six_channel_compliance import _source
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_material_line_position import MaterialLinePosition
from scripts.b3_e4_f03_material_line_space_screen import _rows
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u
from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts._b3_e4_f03_native_fixture import build
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


REFERENCE = Path("docs/agent_plans/B3_E4_F03_C1_PURE_ACTION_MODES_DEV_V3.json")
STATIONS = (.5, .75, .9, .95)
THICKNESS = .035


def _rms(values: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.asarray(values, dtype=float)**2)))


def _coord(point) -> tuple[float, float, float]:
    return tuple(round(float(value), 12) for value in point)


def _width_metrics(solid_field: np.ndarray, nodal: np.ndarray,
                   coordinates: dict, plate_nodes: set[int],
                   node_index: dict[int, int], shell_nodes: np.ndarray,
                   ys: np.ndarray, x: float, primary: str) -> dict:
    physical = {}
    for node in plate_nodes:
        key = _coord(coordinates[node])
        if abs(key[0]-x) < 1e-10 and key[1] in {_coord((0, y, 0))[1] for y in ys}:
            if key in physical:
                raise ArithmeticError("duplicate solid physical probe")
            physical[key] = node
    solid_primary, native_primary = [], []
    warp, face_scale = [], []
    regions = {"under_0p1m_stiffener": [], "outside_stiffener": []}
    for y in ys:
        ids = [physical.get(_coord((x, y, z)))
               for z in (-THICKNESS/2, 0., THICKNESS/2)]
        if any(node is None for node in ids):
            raise ValueError("exact plate thickness probe missing")
        bottom, middle, top = (solid_field[node_index[node]] for node in ids)
        mid = (top+bottom)/2
        rotation = np.array((-(top-bottom)[1]/THICKNESS,
                             (top-bottom)[0]/THICKNESS))
        matches = np.flatnonzero(
            (np.abs(shell_nodes[:, 0]-x) < 1e-10) &
            (np.abs(shell_nodes[:, 1]-y) < 1e-10))
        if len(matches) != 1:
            raise ValueError("exact shell physical probe missing")
        state = nodal[int(matches[0])]
        if primary == "torsion_Mx":
            solid_value, native_value = rotation[0], state[3]
        else:
            solid_value, native_value = mid[2], state[2]
        solid_primary.append(solid_value)
        native_primary.append(native_value)
        warp.append(middle-mid)
        face_scale.extend((bottom, top))
        region = ("under_0p1m_stiffener" if abs(y) <= .05+1e-12
                  else "outside_stiffener")
        regions[region].append(len(solid_primary)-1)
    solid_primary = np.asarray(solid_primary)
    native_primary = np.asarray(native_primary)
    difference = native_primary-solid_primary
    result = {
        "x_m": x,
        "width_samples": len(ys),
        "solid_primary_rms": _rms(solid_primary),
        "native_primary_rms": _rms(native_primary),
        "native_minus_solid_primary_rms": _rms(difference),
        "native_minus_solid_primary_max": float(np.max(np.abs(difference))),
        "relative_primary_rms": _rms(difference)/max(_rms(solid_primary), 1e-12),
        "solid_mid_thickness_linear_director_residual_vector_rms_m": _rms(warp),
        "solid_mid_thickness_linear_director_residual_max_m": float(
            np.max(np.linalg.norm(warp, axis=1))),
        "solid_face_displacement_vector_rms_m": _rms(face_scale),
        "regions": {},
    }
    for name, indices in regions.items():
        values = difference[indices]
        result["regions"][name] = {
            "count": len(indices),
            "solid_primary_rms": _rms(solid_primary[indices]),
            "native_minus_solid_primary_rms": _rms(values),
            "native_minus_solid_primary_max": float(np.max(np.abs(values))),
        }
    return result


def evaluate(reconstruction_path: Path) -> dict:
    solid = _validated_solid_reconstruction(reconstruction_path)
    if digest(reconstruction_path) != "118aef26cf0766fa50a6d42929a095440e142f7177216e5b85dc2c7e51fa7f92":
        raise ValueError("reviewed solid reconstruction identity required")
    prior = json.loads(REFERENCE.read_text())
    if prior.get("solid_reconstruction_sha256") != digest(reconstruction_path):
        raise ValueError("pure-action work reference changed")
    deck, _, coords, _, _, _ = _source(Path(solid["source_root"])/"tip_mx")
    if digest(deck) != solid["cases"]["tip_mx"]["source_deck_sha256"]:
        raise ValueError("reviewed source deck changed")
    plate, bar = _element_domain_nodes(deck)
    solid_nodes, solid_rows, _ = integrated_rows(coords, plate, bar)
    all_nodes = tuple(sorted(coords))
    index = {node: i for i, node in enumerate(all_nodes)}
    unit = []
    for channel, record in enumerate(solid["unit_records"]):
        frd = (Path(solid["response_root"])/f"channel-{channel}"/
               f"material-line-p0-{channel}.frd")
        if record["channel"] != channel or digest(frd) != record["frd_sha256"]:
            raise ValueError("reviewed unit-action identity changed")
        field = _read_frd_u(frd)
        if set(field) != set(coords):
            raise ValueError("incomplete solid unit-action field")
        unit.append(np.asarray([field[node] for node in all_nodes]))
    unit = np.stack(unit)
    xs, ys = local_grid(4, transverse_cells=4)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um", assemble=False)
    line = MaterialLinePosition(xs, ys, beam)
    space = LineMultiplierSpace("piecewise_constant", tuple(np.linspace(0., 1., 5)))
    rows, measure = _rows(line, space)
    if rows.shape[0] != 24 or not np.allclose(measure, .025, atol=1e-12, rtol=0):
        raise ArithmeticError("reviewed P0 basis changed")
    shell, _ = raw_e4_tangent(xs, ys, thickness=THICKNESS)
    shell_size = 6*line.shell_count
    fixed = {6*(j*len(xs)+i)+axis for j in range(len(ys))
             for i, x in enumerate(xs) if abs(x+.5) < 1e-12
             for axis in range(6)}
    selected = np.asarray([index[node] for node in solid_nodes])
    plate_selector = np.asarray([node in plate for node in solid_nodes])
    cases = {}
    for label, channel, magnitude in (("torsion_Mx", 3, 100.),
                                      ("transverse_Fz", 2, 1000.)):
        density = np.zeros(24)
        density[channel::6] = magnitude/.1
        scale = 4000. if channel >= 3 else 40000.
        coefficient = density/scale
        field = -np.tensordot(coefficient, unit, axes=(0, 0))
        solid_force = -(solid_rows.T@density).reshape(-1, 3)
        solid_work = float(np.sum(
            solid_force[plate_selector]*field[selected][plate_selector]))
        dual = (density.reshape(4, 6)*measure[:, None]).ravel()
        shell_force = -rows[:, :shell_size].T@dual
        shell_state, equilibrium = _solve_component(shell, shell_force, fixed)
        shell_work = float(shell_force@shell_state)
        expected = prior["cases"][label]["uniform_component_work_J"]
        for name, actual, target in (("solid", solid_work, expected["solid_plate"]),
                                     ("native", shell_work, expected["native_E4"])):
            if not np.isclose(actual, target, atol=1e-10, rtol=1e-9):
                raise ArithmeticError(f"{name} pure-action work changed")
        cases[label] = {
            "applied_resultant": magnitude,
            "applied_resultant_unit": "Nm" if channel >= 3 else "N",
            "solid_plate_work_j": solid_work,
            "native_e4_work_j": shell_work,
            "native_e4_equilibrium_ratio": equilibrium,
            "primary_observable": ("director_rx_rad" if channel == 3
                                   else "thickness_mean_uz_m"),
            "cross_sections": [_width_metrics(
                field, shell_state.reshape(-1, 6), coords, set(plate), index,
                line.reference_nodes, ys, x, label) for x in STATIONS],
        }
    return {
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "classification": "same-P0-action pure torque/shear physical-width and thickness probe",
        "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                                 text=True).strip(),
        "solid_reconstruction_sha256": digest(reconstruction_path),
        "prior_pure_action_sha256": digest(REFERENCE),
        "unit_fields": len(unit),
        "cases": cases,
        "limits": ["open-interface component influence, not a coupled or contact state",
                   "different 3D-plate and E4 shell kinematic idealizations",
                   "displacement probe and through-thickness chord, not strain energy decomposition",
                   "one width grid and four longitudinal planes, not convergence or F03/G0B acceptance"],
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reconstruction", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate(args.reconstruction.resolve())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({name: {
        "solid_work_j": case["solid_plate_work_j"],
        "native_work_j": case["native_e4_work_j"],
        "relative_primary_rms_by_x": [part["relative_primary_rms"]
                                      for part in case["cross_sections"]]}
        for name, case in result["cases"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
