"""Project saved pre-opened F4 solid sections onto actual B3 half-cell ports.

This is a kinematic representability diagnostic. It neither partitions the
shared-node solid bond action nor measures interface work or G0B acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_native_spatial_port import NativeHalfCellSpatialPort
from scripts.b3_e4_f03_c3d20r_bond_force_recovery import read_deck
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u, project
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


PLANES = (.9, .925, .95, .975, 1.)
CELLS = ((.9, .925, .95), (.95, .975, 1.))
YS = tuple(np.linspace(-.05, .05, 9))
SIMPSON = (1., 4., 1.)
Y_WEIGHTS = np.array((.5, 1., 1., 1., 1., 1., 1., 1., .5))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bottom_trace(beam, state, half: int, fraction: float,
                  y: float, step: np.ndarray) -> np.ndarray:
    element, cell = divmod(half, 2)
    port = NativeHalfCellSpatialPort(beam.context, element, cell, fraction)
    _, _, frame = port.pose_pair(state)
    arm = frame @ np.array((0., y, -.05))
    pose = port.tangent(state) @ step
    return pose[:3] + np.cross(pose[3:], arm)


def _geometry_and_fields(base: Path):
    folder = (base / "f03-ccx-c1-preopen-combined-factor4-dev-20260926-v1" /
              "solid-4-tip_mx")
    stem = folder / "solid-4-tip_mx"
    model_path = folder / "model.json"
    paths = [stem.with_suffix(".inp"), stem.with_suffix(".frd"), model_path]
    model = json.loads(model_path.read_text())
    if (model["bond_policy"] != "terminal" or
            model["contact_policy"] != "none" or
            model["plate_thickness_m"] != .035 or
            model["shared_interface_nodes"] != 121 or
            model["bar_reference_profile"] !=
            "C1_TWO_QUADRATIC_TANGENT_ALIGNED_V1"):
        raise ValueError("saved physical F4 terminal C1 model changed")
    xyz, elements = read_deck(paths[0])
    u = _read_frd_u(paths[1])
    if set(u) != set(range(1, len(xyz))):
        raise ValueError("complete F4 solid displacement field required")
    if len(elements["Stiffener"]) != 1280:
        raise ValueError("F4 stiffener element inventory changed")
    coords = {i: xyz[i] for i in range(1, len(xyz))}
    lookup = {tuple(np.round(point, 9)): i for i, point in coords.items()}
    if len(lookup) != len(coords):
        raise ValueError("F4 coordinate lookup is ambiguous")
    face = {}
    for x in PLANES:
        for y in YS:
            node = lookup.get(tuple(np.round((x, y, .0175), 9)))
            if node is None or node not in model["shared_interface_node_ids"]:
                raise ValueError("matched F4 bond-face node missing")
            face[x, y] = u[node]
    return coords, u, face, paths


def evaluate(base: Path) -> dict:
    coords, u, face, inputs = _geometry_and_fields(base)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um")
    state = beam.context.initial.mechanical
    if (not np.allclose(beam.abscissae[10:], (.9, .95, 1.),
                        rtol=0., atol=1e-12) or
            not np.allclose(state.positions[10:13],
                            ((.9, 0., .0675), (.95, 0., .0675),
                             (1., 0., .0675)), rtol=0., atol=1e-12)):
        raise ValueError("native terminal B3 reference differs from F4")
    fits = {x: project(coords, u, section_x=x) for x in PLANES}
    translations = {x: np.asarray(fits[x]["beam_center_m"]) -
                    np.array((x, 0., .0675)) for x in PLANES}
    rotations = {x: np.asarray(fits[x]["beam_rotation_vector_rad"])
                 for x in PLANES}
    step = np.zeros(beam.context.count)
    for node, x in ((10, .9), (11, .95), (12, 1.)):
        step[6*node:6*node+3] = translations[x]
    cell_rotations = []
    for half, planes in zip((10, 11), CELLS):
        mean = sum(weight*rotations[x] for weight, x in
                   zip(SIMPSON, planes))/6.
        element, cell = divmod(half, 2)
        start = beam.context.nodal_count+24*element+3*cell
        step[start:start+3] = mean
        cell_rotations.append(mean.tolist())

    # The bonded native reference frames are identity. A common rigid
    # translation/rotation must be reproduced by both one-sided ports.
    rigid = np.zeros_like(step)
    translation = np.array((1e-5, -2e-5, 3e-5))
    rotation = np.array((2e-5, -3e-5, 4e-5))
    for node in (10, 11, 12):
        rigid[6*node:6*node+3] = translation + np.cross(
            rotation, state.positions[node]-state.positions[10])
    for half in (10, 11):
        element, cell = divmod(half, 2)
        start = beam.context.nodal_count+24*element+3*cell
        rigid[start:start+3] = rotation
        for fraction in (0., .5, 1.):
            for y in (-.05, 0., .05):
                x = beam.abscissae[half] + fraction*(
                    beam.abscissae[half+1]-beam.abscissae[half])
                expected = translation + np.cross(rotation,
                    np.array((x-.9, y, -.05)))
                actual = _bottom_trace(beam, state, half, fraction,
                                       y, rigid)
                if np.max(np.abs(actual-expected)) > 1e-12:
                    raise ArithmeticError("retained B3 rigid port check failed")

    by_cell = []
    weighted = np.zeros(4)
    weight_total = 0.
    max_error = 0.
    for half, planes in zip((10, 11), CELLS):
        station = []
        for i, x in enumerate(planes):
            differences = []
            for j, y in enumerate(YS):
                solid = face[x, y]
                arm = np.array((0., y, -.05))
                rigid_section = translations[x] + np.cross(rotations[x], arm)
                port = _bottom_trace(beam, state, half, i/2., y, step)
                differences.append((solid, rigid_section, port))
                weight = SIMPSON[i]*(0.5 if j in (0, len(YS)-1) else 1.)
                errors = (np.linalg.norm(solid)**2,
                          np.linalg.norm(solid-rigid_section)**2,
                          np.linalg.norm(rigid_section-port)**2,
                          np.linalg.norm(solid-port)**2)
                weighted += weight*np.asarray(errors)
                weight_total += weight
                max_error = max(max_error, float(np.linalg.norm(solid-port)))
            array = np.asarray(differences)
            station.append({"x_m": x,
                            "solid_face_trapezoid_mean_m": np.average(
                                array[:, 0, :], axis=0,
                                weights=Y_WEIGHTS).tolist(),
                            "b3_port_face_trapezoid_mean_m": np.average(
                                array[:, 2, :], axis=0,
                                weights=Y_WEIGHTS).tolist(),
                            "b3_minus_solid_face_rms_m": float(np.sqrt(np.mean(
                                np.sum((array[:, 2, :]-array[:, 0, :])**2,
                                       axis=1))))})
        by_cell.append({"half_cell": half,
                        "interval_m": [planes[0], planes[-1]],
                        "stations": station})
    rms = np.sqrt(weighted/weight_total)
    split_left = np.array([_bottom_trace(beam, state, 10, 1., y, step)
                           for y in YS])
    split_right = np.array([_bottom_trace(beam, state, 11, 0., y, step)
                            for y in YS])
    result = {
        "classification": "saved-F4 coupled-solid to actual retained-B3 kinematic projection; no bond-work or G0B acceptance",
        "question": "Can the actual two B3 half-cell ports represent the pre-opened coupled-solid bar-bottom motion, separately from rigid-section and shell idealization error?",
        "outcome_rule": "Material rigid-section residual implicates solid section/warping reduction; material port-versus-rigid residual implicates retained half-cell trace representation. Small kinematic residual shifts the next discriminator to sided action and coupled enforcement; neither outcome ranks a multiplier.",
        "physical_case": "F4 C1 35 mm plate/square bar, shared terminal 0.1 m bond, no contact outside, -1000 N Fz +100 Nm Mx pre-opened combined load, left plate and bar-root supports, quadratic end-face loading",
        "projection": "area-weighted Q20 solid section fits at actual x=.9/.925/.95/.975/1 planes; native nodal translations from .9/.95/1 fits and independent retained half-cell rotations from Simpson means; linearized actual spatial ports on each side",
        "face_sample_rule": "nine mesh-aligned y nodes with trapezoid weights; cell-integrated RMS uses Simpson x weights; split jump is nine-node RMS",
        "section_fit_rms_m": {str(round(x*1000)): fits[x][
            "beam_section_rms_fit_residual_m"] for x in PLANES},
        "retained_cell_rotation_rad": cell_rotations,
        "area_weighted_rms_m": {
            "solid_face_motion": float(rms[0]),
            "solid_minus_rigid_section": float(rms[1]),
            "rigid_section_minus_b3_port": float(rms[2]),
            "solid_minus_b3_port": float(rms[3])},
        "maximum_solid_minus_b3_port_m": max_error,
        "split_port_jump_rms_m": float(np.sqrt(np.mean(np.sum(
            (split_left-split_right)**2, axis=1)))),
        "split_port_jump_max_m": float(np.max(np.linalg.norm(
            split_left-split_right, axis=1))),
        "cells": by_cell,
        "limits": ["kinematic projection, not an equilibrium B3 solve",
                   "solid section fit and Simpson cell means are declared projections, not exact 3D-to-B3 mechanics",
                   "no sided solid traction or interface-work comparison",
                   "one saved F4 physical load state; contact outside bond omitted"],
        "inputs_sha256": {str(path.relative_to(base)): _sha(path)
                          for path in inputs},
        "runner_sha256": _sha(Path(__file__)),
        "source_git": subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=Path(__file__).resolve().parents[1], text=True).strip(),
        "helper_sha256": {name: _sha(Path(__file__).with_name(name))
                          for name in (
                              "_b3_e4_f03_native_fixture.py",
                              "_b3_e4_f03_native_spatial_port.py",
                              "b3_e4_f03_c3d20r_bond_force_recovery.py",
                              "b3_e4_f03_ccx_solid_bond_screen.py",
                              "b3_e4_f03_solid_bond_pose_projection.py",
                              "b3_e4_f03_square_section_control.py")},
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", required=True, type=Path)
    args = parser.parse_args()
    root = args.evidence_root.resolve()
    if root.exists():
        raise FileExistsError(root)
    result = evaluate(root.parent)
    root.mkdir(parents=True)
    (root/"result.json").write_text(json.dumps(result, indent=2,
                                               sort_keys=True)+"\n")
    print(json.dumps(result["area_weighted_rms_m"], sort_keys=True))


if __name__ == "__main__":
    main()
