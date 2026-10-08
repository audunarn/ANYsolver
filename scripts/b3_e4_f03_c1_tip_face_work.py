"""Split saved matched-line solid tip-load work by a declared rigid face fit.

This is a read-only development diagnostic. The rigid least-squares fit uses
equal weights on loaded tip-face nodes; its residual work is fit-dependent,
not a constitutive energy or an accuracy bound.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

import numpy as np

from scripts.b3_e4_f03_ccx_six_channel_compliance import _source
from scripts.b3_e4_f03_ccx_six_channel_preflight import _element_domain_nodes
from scripts.b3_e4_f03_ccx_solid_bond_screen import digest
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


def split_tip_work(coords: np.ndarray, force: np.ndarray,
                   displacement: np.ndarray, origin: np.ndarray) -> dict:
    """Audit exact load work against an equal-node rigid section fit."""
    xyz, applied, u, center = (np.asarray(value, dtype=float) for value in
                               (coords, force, displacement, origin))
    if (xyz.ndim != 2 or xyz.shape[1] != 3 or applied.shape != xyz.shape or
            u.shape != xyz.shape or center.shape != (3,) or
            len(xyz) < 3 or not all(np.isfinite(value).all() for value in
                                    (xyz, applied, u, center))):
        raise ValueError("complete finite tip-face fields required")
    lever = xyz-center
    matrix = np.zeros((3*len(xyz), 6))
    for j, (x, y, z) in enumerate(lever):
        matrix[3*j:3*j+3, :3] = np.eye(3)
        matrix[3*j:3*j+3, 3:] = ((0., z, -y), (-z, 0., x), (y, -x, 0.))
    pose, _, rank, singular = np.linalg.lstsq(matrix, u.ravel(), rcond=None)
    if rank != 6:
        raise ArithmeticError("tip-face rigid pose is unidentifiable")
    rigid_u = (matrix@pose).reshape(-1, 3)
    force_resultant = applied.sum(axis=0)
    moment_resultant = np.cross(lever, applied).sum(axis=0)
    full = float(np.sum(applied*u))
    rigid = float(np.sum(applied*rigid_u))
    generalized = float(force_resultant@pose[:3]+moment_resultant@pose[3:])
    warp = float(np.sum(applied*(u-rigid_u)))
    if abs(full-rigid-warp) > 1e-10*max(1., abs(full)) or abs(
            rigid-generalized) > 1e-10*max(1., abs(full)):
        raise ArithmeticError("tip-face work split lost virtual work")
    return {
        "loaded_nodes": int(len(xyz)),
        "rigid_fit_rank": int(rank),
        "rigid_fit_condition": float(singular[0]/singular[-1]),
        "force_N": force_resultant.tolist(),
        "moment_Nm_about_origin": moment_resultant.tolist(),
        "fitted_translation_m": pose[:3].tolist(),
        "fitted_rotation_rad": pose[3:].tolist(),
        "full_tip_load_work_J": full,
        "rigid_fit_load_work_J": rigid,
        "nonrigid_fit_load_work_J": warp,
        "nonrigid_fraction_of_abs_full_work": abs(warp)/max(abs(full), 1e-30),
        "tip_displacement_fit_rms_m": float(np.sqrt(np.mean((u-rigid_u)**2))),
    }


def evaluate(reconstruction_path: Path) -> dict:
    reconstruction = json.loads(reconstruction_path.read_text())
    if reconstruction["status"] != "EXPLORATORY_COMPLETE":
        raise ValueError("saved completed 24-column reconstruction required")
    scale = np.array([40000. if j % 6 < 3 else 4000. for j in range(24)])
    cases = {}
    for label in ("tip_mx", "tip_fz"):
        folder = Path(reconstruction["source_root"])/label
        deck, meta, coords, _, _, _ = _source(folder)
        case = reconstruction["cases"][label]
        if digest(deck) != case["source_deck_sha256"]:
            raise ValueError("saved source deck changed")
        _, bar = _element_domain_nodes(deck)
        loaded = tuple(sorted(int(node) for node in meta["applied_nodal_forces_N"]))
        if (not loaded or not set(loaded) <= bar or
                any(abs(coords[node][0]-1.) > 1e-10 for node in loaded)):
            raise ValueError("declared bar tip-face load changed")
        force = np.array([meta["applied_nodal_forces_N"][str(node)]
                          for node in loaded])
        source_files = list(folder.glob("*.frd"))
        if len(source_files) != 1 or digest(source_files[0]) != case["source_frd_sha256"]:
            raise ValueError("saved source displacement changed")
        source_u = _read_frd_u(source_files[0])
        u = np.array([source_u[node] for node in loaded])
        dual = np.asarray(case["dual_physical_line_density"])
        if dual.shape != (24,):
            raise ValueError("saved dual inventory changed")
        for j, record in enumerate(reconstruction["unit_records"]):
            if record["channel"] != j:
                raise ValueError("unit response order changed")
            frd = (Path(reconstruction["response_root"])/f"channel-{j}"/
                   f"material-line-p0-{j}.frd")
            if digest(frd) != record["frd_sha256"]:
                raise ValueError("saved unit response changed")
            field = _read_frd_u(frd)
            u -= (dual[j]/scale[j])*np.array([field[node] for node in loaded])
        origin = np.array((1., 0., float(meta["bar_tip_axis_z_m"])))
        result = split_tip_work(np.array([coords[node] for node in loaded]),
                                force, u, origin)
        saved = case["applied_load_work_J"]
        if abs(result["full_tip_load_work_J"]-saved) > 1e-8*max(1., abs(saved)):
            raise ArithmeticError("tip-face work does not reproduce saved result")
        result["saved_applied_load_work_J"] = saved
        result["source_deck_sha256"] = digest(deck)
        result["source_frd_sha256"] = digest(source_files[0])
        cases[label] = result
    return {
        "status": "DEVELOPMENT_DIAGNOSTIC_COMPLETE",
        "classification": "same saved P0 solid response, tip-face rigid-fit work split",
        "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                                 text=True).strip(),
        "reconstruction_sha256": digest(reconstruction_path),
        "cases": cases,
        "limitations": [
            "equal-loaded-node rigid fit is a declared kinematic split, not a unique beam port",
            "nonrigid load work is not a stiffness-energy allocation or an accuracy bound",
            "saved external linear response only; no new solve or connection qualification",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reconstruction", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve previous tip-face work result")
    result = evaluate(args.reconstruction.resolve())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True,
                                      allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({key: {"nonrigid_work_J": value[
        "nonrigid_fit_load_work_J"], "full_work_J": value["full_tip_load_work_J"]}
                      for key, value in result["cases"].items()}, sort_keys=True))


if __name__ == "__main__":
    main()
