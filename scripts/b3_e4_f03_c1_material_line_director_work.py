"""Split saved solid plate line work by local director-compatible motion.

At each paired top/bottom face site, the linear E4 director field can
represent both in-plane displacements but only one transverse displacement.
This projection removes local thickness-normal stretch; it does not impose
Q4 interpolation, plate equilibrium, or a global E4 state.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c1_material_line_p0_reference import integrated_rows
from scripts.b3_e4_f03_ccx_six_channel_compliance import _source
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


def evaluate(reconstruction_path: Path, same_action_path: Path,
             source_root: Path, response_root: Path) -> dict:
    reconstruction = json.loads(reconstruction_path.read_text())
    prior = json.loads(same_action_path.read_text())
    if (reconstruction["status"] != "EXPLORATORY_COMPLETE" or
            prior["solid_reconstruction_sha256"] != digest(reconstruction_path)):
        raise ValueError("same-action solid predecessor required")
    deck, _, coords, _, _, _ = _source(source_root / "tip_mx")
    if digest(deck) != reconstruction["cases"]["tip_mx"]["source_deck_sha256"]:
        raise ValueError("solid source deck changed")
    plate, bar = _element_domain_nodes(deck)
    nodes, rows, _ = integrated_rows(coords, plate, bar)
    index = {node: i for i, node in enumerate(nodes)}
    units = []
    for j, record in enumerate(reconstruction["unit_records"]):
        frd = response_root / f"channel-{j}" / f"material-line-p0-{j}.frd"
        if record["channel"] != j or digest(frd) != record["frd_sha256"]:
            raise ValueError("pinned solid action field changed")
        field = _read_frd_u(frd)
        if not set(nodes) <= set(field):
            raise ValueError("incomplete solid line trace")
        units.append(np.array([field[node] for node in nodes]))
    units = np.stack(units)
    sites = {}
    for node in nodes:
        if node not in plate:
            continue
        x, y, z = coords[node]
        if abs(abs(z)-.0175) > 1e-10:
            raise ValueError("unexpected plate face height")
        key = (round(float(x), 9), round(float(y), 9))
        pair = sites.setdefault(key, {})
        side = "top" if z > 0. else "bottom"
        if side in pair:
            raise ValueError("duplicate solid plate face site")
        pair[side] = index[node]
    if any(set(pair) != {"top", "bottom"} for pair in sites.values()):
        raise ValueError("unpaired solid plate face sites")
    cases = {}
    scale = np.array([40000. if j % 6 < 3 else 4000.
                      for j in range(len(rows))])
    for label in ("tip_mx", "tip_fz"):
        dual = np.asarray(reconstruction["cases"][label]["dual_physical_line_density"])
        coefficient = dual/scale
        displacement = -np.tensordot(coefficient, units, axes=(0, 0))
        force = -(rows.T@dual).reshape(-1, 3)
        projected = displacement.copy()
        thickness_stretch = []
        for pair in sites.values():
            top, bottom = pair["top"], pair["bottom"]
            mean_z = .5*(displacement[top, 2]+displacement[bottom, 2])
            thickness_stretch.append(displacement[top, 2]-displacement[bottom, 2])
            projected[top, 2] = mean_z
            projected[bottom, 2] = mean_z
        plate_indices = np.array([index[node] for node in nodes if node in plate])
        actual = float(np.sum(force[plate_indices]*displacement[plate_indices]))
        compatible = float(np.sum(force[plate_indices]*projected[plate_indices]))
        excluded = float(np.sum(force[plate_indices]*(
            displacement[plate_indices]-projected[plate_indices])))
        np.testing.assert_allclose(actual, compatible+excluded, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(actual,
            prior["cases"][label]["solid_shell_action_only_work_J"],
            rtol=1e-11, atol=1e-12)
        native = prior["cases"][label]["native_shell_action_only_work_J"]
        cases[label] = {
            "solid_plate_full_action_work_J": actual,
            "solid_plate_local_director_compatible_work_J": compatible,
            "solid_plate_excluded_thickness_work_J": excluded,
            "solid_minus_native_E4_work_J": actual-native,
            "excluded_fraction_of_solid_minus_native": excluded/(actual-native),
            "paired_face_sites": len(sites),
            "max_absolute_thickness_stretch_m": float(np.max(np.abs(thickness_stretch))),
            "rms_thickness_stretch_m": float(np.sqrt(np.mean(np.square(thickness_stretch)))),
            "work_identity_defect_J": actual-compatible-excluded,
        }
    return {
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "classification": "local through-thickness work split of fixed solid interface action",
        "solid_reconstruction_sha256": digest(reconstruction_path),
        "same_action_sha256": digest(same_action_path),
        "source_deck_sha256": digest(deck),
        "cases": cases,
        "limitations": [
            "local director-compatible projection is not a globally interpolated E4 response",
            "excluded work only diagnoses thickness-normal stretch at active line face sites",
            "does not allocate remaining E4/3D difference to support, transverse shear, or constitutive law",
            "not F03/G0B acceptance or multiplier selection",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reconstruction", type=Path, required=True)
    parser.add_argument("--same-action", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--responses", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve previous director-work diagnostic")
    result = evaluate(args.reconstruction.resolve(), args.same_action.resolve(),
                      args.source_root.resolve(), args.responses.resolve())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "fractions": {
        case: record["excluded_fraction_of_solid_minus_native"]
        for case, record in result["cases"].items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
