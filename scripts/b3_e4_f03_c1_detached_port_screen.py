"""Bounded C1 detached-bar section/end-port discriminator.

The plate and bar are disconnected in this diagnostic. Pure torque here
tests the bare bar; it does not supply a bonded/contact reference.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

import numpy as np
from scipy.sparse.linalg import spsolve
from scipy.spatial.transform import Rotation
from threadpoolctl import threadpool_limits

from scripts._b3_e4_f03_native_fixture import build as build_native
from scripts.b3_e4_f03_c3d20r_bond_force_recovery import read_deck
from scripts.b3_e4_f03_ccx_solid_bond_screen import (
    EXE, EXE_SHA, TIMEOUT_SECONDS, build as build_solid, digest,
    parse_nodal_vectors, parse_probe_displacements, recover,
    unexpected_solver_diagnostics, _wrench,
)
from scripts.b3_e4_f03_factor5_station_comparison import _section_rotation_at
from scripts.b3_e4_f03_saved_six_gap_replay import _ports
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u
from scripts.b3_e4_f03_square_section_control import square_torsion_constant


WORKTREE = Path(__file__).resolve().parents[1]
STATIONS = (.9, .95, 1.)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _native_case(beam, load: str) -> dict:
    rhs = np.zeros(beam.context.count)
    tip = 6 * beam.n_half_cells
    rhs[tip + (3 if load == "tip_mx" else 2)] = (
        100. if load == "tip_mx" else -1000.)
    free = np.r_[beam.physical, beam.internal]
    step = np.zeros_like(rhs)
    step[free] = spsolve(beam.tangent[free, :][:, free].tocsc(),
                        (rhs - beam.residual)[free])
    relative = beam.tangent @ step + beam.residual - rhs
    if (not np.isfinite(step).all() or
            np.max(np.abs(relative[free])) > 1e-5):
        raise ArithmeticError("native bare B3 residual or state invalid")
    stations = {}
    for x in STATIONS:
        reference, reference_frame = beam.pose(x)
        position, frame = beam.pose(x, step)
        stations[str(round(x * 1000))] = {
            "rx_rad": float(Rotation.from_matrix(
                frame @ reference_frame.T).as_rotvec()[0]),
            "uz_m": float((position - reference)[2]),
        }
    work = float(rhs @ step)
    return {"tip_work_j": work,
            "tip_work_coordinate": float(step[tip + (3 if load == "tip_mx" else 2)]),
            "stations": stations,
            "free_max_residual": float(np.max(np.abs(relative[free]))),
            "root_reaction_N_Nm": relative[:6].tolist(),
            "dense_local_oracle_max_error": beam.dense_oracle_max_error}


def _solid_case(root: Path, load: str) -> dict:
    folder = root / load
    folder.mkdir()
    name = f"c1-detached-{load}"
    deck, model = build_solid(
        4, load, boundary_policy="left_root", bond_policy="detached",
        contact_policy="none", element_family="C3D20R",
        reverse_tip_fz=load == "tip_fz", bar_clearance_um=2,
        plate_thickness_mm=35, tip_load_map="quadratic_face",
        full_displacement_output=True, bar_reference_profile="c1_tangent")
    if (model["shared_interface_nodes"] != 0 or
            set(model["beam_root_node_ids"]) &
            set(model["plate_boundary_node_ids"])):
        raise ValueError("solid bar is not detached and independently supported")
    applied = {int(key): np.asarray(value) for key, value in
               model["applied_nodal_forces_N"].items()}
    expected = np.array((0., 0., 0., 100., 0., 0.) if load == "tip_mx"
                        else (0., 0., -1000., 0., 1000., 0.))
    if np.max(np.abs(_wrench(applied, model["probe_coordinates_m"])-expected)) > 1e-9:
        raise ValueError("detached end-face wrench differs from native load")
    deck_path = folder / f"{name}.inp"
    deck_path.write_text(deck, encoding="ascii")
    (folder / "model.json").write_text(json.dumps(model, indent=2, sort_keys=True) + "\n")
    environment = os.environ.copy()
    environment.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                       MKL_NUM_THREADS="1")
    start = time.perf_counter()
    try:
        run = subprocess.run((str(EXE), "-i", name), cwd=folder,
                             env=environment, capture_output=True,
                             timeout=TIMEOUT_SECONDS, check=False)
        exit_code, stdout, stderr = run.returncode, run.stdout, run.stderr
        failure = None
    except subprocess.TimeoutExpired as exc:
        exit_code, stdout, stderr = None, exc.stdout or b"", exc.stderr or b""
        failure = "TIMEOUT_120_SECONDS"
    (folder / "stdout.log").write_bytes(stdout)
    (folder / "stderr.log").write_bytes(stderr)
    elapsed = time.perf_counter() - start
    if failure is not None:
        raise RuntimeError(f"{load}: {failure}; raw files preserved in {folder}")
    if exit_code != 0:
        raise RuntimeError(f"{load}: CalculiX exit {exit_code}; raw files preserved in {folder}")
    out = stdout.decode(errors="replace")
    sta = (folder / f"{name}.sta").read_text(errors="replace")
    dat = (folder / f"{name}.dat").read_text(errors="replace")
    status = [re.match(r"^\s*1\s+1\s+1\s+\d+\s+([\d.Ee+-]+)\s+([\d.Ee+-]+)\s+([\d.Ee+-]+)\s*$", line)
              for line in sta.splitlines()]
    complete = [m for m in status if m is not None]
    diagnostics = unexpected_solver_diagnostics(
        out + sta + dat + stderr.decode(errors="replace"), c1_penalty=False)
    if (out.count("Job finished") != 1 or len(complete) != 1 or
            abs(float(complete[0].group(1)) - 1.) > 1e-10 or diagnostics):
        raise RuntimeError(f"{load}: incomplete job or diagnostics {diagnostics[:3]}")
    probes = parse_probe_displacements(dat, set(model["probe_node_ids"]))
    reactions = parse_nodal_vectors(dat, set(model["boundary_node_ids"]),
                                    "forces", model["support_set"])
    recovered = recover(model, probes, reactions)
    xyz, elements = read_deck(deck_path)
    u = _read_frd_u(folder / f"{name}.frd")
    if set(u) != set(range(1, len(xyz))):
        raise ValueError("detached full-field output incomplete")
    coords = {node: xyz[node] for node in range(1, len(xyz))}
    _, rotations, fit_rms = _ports(coords, u, elements, method="area")
    sections = {str(round(x * 1000)): _section_rotation_at(x, rotations)
                for x in STATIONS}
    work = float(sum(force @ u[node] for node, force in applied.items()))
    if abs(work - recovered["applied_load_work_j"]) > 1e-7:
        raise ArithmeticError("printed/full-field load work disagrees")
    return {"status": "EXPLORATORY_COMPLETE", "seconds": elapsed,
            "tip_work_j": work, "tip_work_coordinate": recovered[
                "tip_work_conjugate_displacement"],
            "section_rx_rad": sections,
            "section_fit_rms_m": fit_rms.tolist(),
            "support_wrench_N_Nm": recovered["support_wrench_N_Nm"],
            "model": model,
            "files_sha256": {path.name: _sha(path) for path in folder.iterdir()
                             if path.is_file()}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.evidence_root.resolve()
    if root.exists():
        raise FileExistsError(root)
    if digest(EXE) != EXE_SHA:
        raise ValueError("pinned CalculiX executable changed")
    source = subprocess.check_output(("git", "rev-parse", "HEAD"),
                                     cwd=WORKTREE, text=True).strip()
    if subprocess.check_output(("git", "status", "--porcelain"),
                               cwd=WORKTREE, text=True).strip():
        raise RuntimeError("source must be clean before external diagnostic")
    root.mkdir(parents=True)
    manifest = {
        "classification": "bounded detached C1 section/end-port development screen; no connection or G0B acceptance",
        "question": "Does native bare B3 differ from a matched C1 3D square bar under torque and opening-force end loads, without any shell connection?",
        "outcome_rule": "Bare mismatch prioritizes section/warping/end-port diagnosis; bare agreement shifts the coupled discrepancy toward the attachment trace. One solid mesh does not qualify either conclusion as convergence.",
        "source_git": source, "runner_sha256": _sha(Path(__file__)),
        "solid_builder_sha256": _sha(WORKTREE / "scripts/b3_e4_f03_ccx_solid_bond_screen.py"),
        "calculix_sha256": EXE_SHA, "threads": 1,
        "timeout_seconds_per_case": TIMEOUT_SECONDS,
        "load_cases": ["tip_mx", "tip_fz"],
        "geometry": "C1 2um tangent reference, 100mm square bar, 35mm plate disconnected, x=0–1m, root clamped, factor-4 C3D20R solid vs native B3-12 Saint-Venant square section",
        "limits": ["detached bare bar does not validate the shell connection",
                   "solid distributed end traction differs from native nodal resultant",
                   "one 3D mesh level; pure torque is admissible only as a detached-bar load, not as the previously bonded no-contact reference"],
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    with threadpool_limits(limits=1):
        beam = build_native(12, z_offset=.0675,
                            torsion_constant=square_torsion_constant(),
                            reference_profile="c1_tangent_2um")
        results = {}
        for load in manifest["load_cases"]:
            native = _native_case(beam, load)
            solid = _solid_case(root, load)
            results[load] = {"native": native, "solid": solid}
            (root / f"{load}-result.json").write_text(
                json.dumps(results[load], indent=2, sort_keys=True) + "\n")
            print(load, "native work", native["tip_work_j"],
                  "solid work", solid["tip_work_j"], flush=True)
    (root / "result.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
