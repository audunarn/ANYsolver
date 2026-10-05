"""Fit saved pure-torque solid face motion into the existing clamped Q4 space.

The fit is kinematic and diagnostic. It is not an energy projection or a
qualified equivalence of 3D plate and E4-PL material/support models.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

from scripts._b3_e4_f03_native_fixture import build
from scripts._b3_e4_f03_weak_line_candidate import LineMultiplierSpace
from scripts.b3_e4_f03_c1_global_q4_fit import fit_field, fit_matrix
from scripts.b3_e4_f03_c1_material_line_loaded import _validated_solid_reconstruction
from scripts.b3_e4_f03_c1_material_line_same_action import _solve_component
from scripts.b3_e4_f03_ccx_six_channel_compliance import _source
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_material_line_position import MaterialLinePosition
from scripts.b3_e4_f03_material_line_space_screen import _rows
from scripts.b3_e4_f03_plate_patch_work import local_grid, raw_e4_tangent
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


WIDTH_RECORD = Path("docs/agent_plans/B3_E4_F03_C1_PURE_ACTION_WIDTH_DEV_V1.json")
WIDTH_SHA = "31aafbf3ad37f9e07afa08a6e45a86a69afff6e6d212d36ac0324298a4e4f166"
THICKNESS = .035


def evaluate(reconstruction_path: Path) -> dict:
    solid = _validated_solid_reconstruction(reconstruction_path)
    if digest(WIDTH_RECORD) != WIDTH_SHA:
        raise ValueError("reviewed pure-torque width evidence changed")
    width = json.loads(WIDTH_RECORD.read_text())
    if width["solid_reconstruction_sha256"] != digest(reconstruction_path):
        raise ValueError("pure-torque source identity changed")
    deck, _, coords, _, _, _ = _source(Path(solid["source_root"])/"tip_mx")
    if digest(deck) != solid["cases"]["tip_mx"]["source_deck_sha256"]:
        raise ValueError("reviewed solid deck changed")
    plate, _ = _element_domain_nodes(deck)
    faces = tuple(sorted(node for node in plate
                         if abs(abs(coords[node][2])-THICKNESS/2) < 1e-10))
    if not faces:
        raise ValueError("solid plate faces missing")
    xs, ys = local_grid(4, transverse_cells=4)
    matrix, free_fit = fit_matrix(coords, faces, xs, ys)
    beam = build(12, z_offset=.0675,
                 torsion_constant=square_torsion_constant(),
                 reference_profile="c1_tangent_2um", assemble=False)
    line = MaterialLinePosition(xs, ys, beam)
    rows, measures = _rows(line, LineMultiplierSpace(
        "piecewise_constant", tuple(np.linspace(0., 1., 5))))
    if rows.shape[0] != 24 or not np.allclose(measures, .025, rtol=0., atol=1e-12):
        raise ArithmeticError("reviewed P0 row basis changed")
    shell, _ = raw_e4_tangent(xs, ys, thickness=THICKNESS)
    shell_size = 6*line.shell_count
    fixed = {6*(j*len(xs)+i)+axis for j in range(len(ys))
             for i, x in enumerate(xs) if abs(x+.5) < 1e-12
             for axis in range(6)}
    density = np.zeros(24)
    density[3::6] = 100./.1  # 100 Nm uniform Mx over the 0.1 m line.
    dual = (density.reshape(4, 6)*measures[:, None]).ravel()
    force = -rows[:, :shell_size].T@dual
    equilibrium, equilibrium_error = _solve_component(shell, force, fixed)
    face_field = np.zeros((len(faces), 3))
    for channel in range(3, 24, 6):
        record = solid["unit_records"][channel]
        frd = (Path(solid["response_root"])/f"channel-{channel}"/
               f"material-line-p0-{channel}.frd")
        if record["channel"] != channel or digest(frd) != record["frd_sha256"]:
            raise ValueError("reviewed pure-torque unit field changed")
        field = _read_frd_u(frd)
        if not set(faces) <= set(field):
            raise ValueError("incomplete plate face response")
        face_field -= .25*np.asarray([field[node] for node in faces])
    fit, fit_diagnostic = fit_field(matrix, free_fit, face_field,
                                    line.shell_count)
    free = np.setdiff1d(np.arange(shell_size), np.asarray(sorted(fixed)))
    if np.max(np.abs(fit[list(fixed)])) != 0.:
        raise ArithmeticError("solid face fit changed the clamped Q4 root")
    difference = fit-equilibrium
    equilibrium_work = float(force@equilibrium)
    fitted_work = float(force@fit)
    fitted_energy = float(fit@shell@fit)
    difference_energy = float(difference@shell@difference)
    identity = fitted_energy-2*fitted_work+equilibrium_work
    if (equilibrium_work <= 0. or difference_energy < -1e-10 or
            abs(identity-difference_energy) > 1e-9*max(1., equilibrium_work)):
        raise ArithmeticError("Q4 fitted-field variational identity failed")
    if abs(equilibrium_work-width["cases"]["torsion_Mx"]["native_e4_work_j"]) > 1e-10:
        raise ArithmeticError("reviewed pure-torque Q4 work changed")
    scaled_force_defect = float(np.linalg.norm((shell@fit-force)[free]) /
                                max(1., np.linalg.norm(force[free])))
    return {
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "classification": "pure-torque solid-face kinematic fit and Q4 energy comparison",
        "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                                 text=True).strip(),
        "solid_reconstruction_sha256": digest(reconstruction_path),
        "pure_action_width_sha256": WIDTH_SHA,
        "pure_torque_unit_fields": 4,
        "face_fit": fit_diagnostic,
        "q4": {
            "free_coordinates": len(free),
            "equilibrium_residual_ratio": equilibrium_error,
            "equilibrium_action_work_j": equilibrium_work,
            "fitted_action_work_j": fitted_work,
            "fitted_internal_quadratic_work_j": fitted_energy,
            "fit_minus_equilibrium_q4_energy_j": difference_energy,
            "relative_energy_norm_distance": float(np.sqrt(max(0., difference_energy)/equilibrium_work)),
            "fitted_free_residual_ratio": scaled_force_defect,
            "variational_identity_defect_j": identity-difference_energy,
        },
        "solid_plate_action_work_j": width["cases"]["torsion_Mx"]["solid_plate_work_j"],
        "limits": ["kinematic least-squares fit, not an energy-orthogonal projection",
                   "E4 and 3D plate/support idealizations remain distinct",
                   "open-interface pure-action component response, not a coupled bond",
                   "one shell grid and load; no F03/G0B or multiplier acceptance"],
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
    print(json.dumps({"fit": result["face_fit"], "q4": result["q4"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
