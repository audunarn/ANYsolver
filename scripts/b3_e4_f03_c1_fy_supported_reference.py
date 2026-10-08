"""One supported C1 solid Fy influence, using the saved sided F5 geometry.

The broken cut work is diagnostic only: it is not an admissible native B3 port
variation or a qualification of the continuous connection or multiplier space.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import time

import numpy as np

from scripts.b3_e4_f03_c3d20r_bond_force_recovery import read_deck, wrench
from scripts.b3_e4_f03_c3d20r_stress_force_recovery import integrate, read_stress
from scripts.b3_e4_f03_ccx_solid_bond_screen import (
    EXE, EXE_SHA, TIMEOUT_SECONDS, _wrench, audit_unbonded_open, build,
    digest, parse_nodal_vectors, parse_probe_displacements,
    split_left_root_support_wrenches, unexpected_solver_diagnostics,
)


SOURCE = Path(
    ".qualification/b3-ge-e4-pl/"
    "f03-c1-factor5-sided-port-cut-dev-20260926-v1"
)
LOAD_N = 100.


def prepare() -> tuple[str, dict, dict]:
    """Change only the saved side-cut deck's end-face load to +Fy."""
    source = json.loads((SOURCE / "run_result.json").read_text())
    if source["status"] != "EXECUTED_OUTPUT_PENDING_MECHANICAL_VALIDATION":
        raise ValueError("completed saved side-cut reference required")
    for name in ("model.json", "solid-5-sided-port.inp"):
        if digest(SOURCE / name) != source["files_sha256"][name]:
            raise ValueError("saved side-cut geometry identity changed")
    model = json.loads((SOURCE / "model.json").read_text())
    _, opening = build(
        5, "tip_fz", boundary_policy="left_root", bond_policy="terminal",
        contact_policy="none", element_family="C3D20R", reverse_tip_fz=True,
        bar_clearance_um=2, plate_thickness_mm=35,
        tip_load_map="quadratic_face", full_displacement_output=True,
        bar_reference_profile="c1_tangent")
    for key in ("plate_thickness_m", "bar_tip_axis_z_m", "bond_interval_m",
                "bar_reference_profile", "boundary_policy", "element_family"):
        if opening[key] != model[key]:
            raise ValueError(f"C1 solid physical model differs in {key}")
    tip_coordinates = {
        tuple(position): int(node)
        for node, position in model["probe_coordinates_m"].items()
        if abs(position[0]-1.) < 1e-12
    }
    applied = {}
    for node, force in opening["applied_nodal_forces_N"].items():
        position = tuple(opening["probe_coordinates_m"][node])
        if position not in tip_coordinates or force[:2] != [0., 0.]:
            raise ValueError("quadratic tip-face load map changed")
        applied[tip_coordinates[position]] = np.array(
            (0., -LOAD_N/1000.*force[2], 0.))
    if len(applied) != 341 or set(applied) != set(tip_coordinates.values()):
        raise ValueError("incomplete side-cut end-face Fy distribution")
    physical_wrench = np.asarray(_wrench(applied, model["probe_coordinates_m"]))
    if not np.allclose(physical_wrench, (0., LOAD_N, 0.,
                                          -.0675*LOAD_N, 0., LOAD_N),
                       rtol=0., atol=1e-8):
        raise ArithmeticError("pure Fy end-face wrench is incorrect")
    original = (SOURCE / "solid-5-sided-port.inp").read_text()
    head, marker, load_and_tail = original.partition("*CLOAD\n")
    if not marker or original.count("*CLOAD\n") != 1:
        raise ValueError("one saved end-face load block required")
    _, next_card, tail = load_and_tail.partition("*NODE PRINT,NSET=Probe")
    if not next_card:
        raise ValueError("saved C1 output-card boundary changed")
    cards = "".join(f"{node},2,{force[1]:.12g}\n"
                    for node, force in sorted(applied.items()) if force[1] != 0.)
    deck = head + marker + cards + next_card + tail
    model = dict(model)
    model["shear"] = "tip_fy"
    model["applied_nodal_forces_N"] = {
        str(node): force.tolist() for node, force in sorted(applied.items())}
    model["reference_load"] = "+100 N Fy, quadratic end-face traction at x=1 m"
    model.pop("torque_with_opening_fz", None)
    manifest = {
        "classification": "bounded supported C1 Fy diagnostic; not F03 acceptance",
        "decision": "Does independently supported lateral/shear transfer distinguish the native 2:1 mode from physical compliance?",
        "physical_model": "saved F5 sided C3D20R geometry, 35 mm plate, 100 mm bar, x=.9-1 m terminal bond, 2 um pre-opening, left/root supports, no contact",
        "only_model_change": "+100 N Fy quadratic end-face nodal work; all nodes, elements, supports, materials and output cards retained",
        "source_deck_sha256": digest(SOURCE / "solid-5-sided-port.inp"),
        "source_model_sha256": digest(SOURCE / "model.json"),
        "generator_sha256": digest(Path(build.__code__.co_filename)),
        "runner_sha256": digest(Path(__file__)),
        "executable_sha256": digest(EXE),
        "limit": {"seconds": TIMEOUT_SECONDS, "omp_threads": 1},
        "applied_wrench_N_Nm": physical_wrench.tolist(),
        "limitations": ["one external grid and load", "the solid shared-node bond is stronger than a declared weak line", "broken side-cut work is not a native retained-port action"],
    }
    if manifest["executable_sha256"] != EXE_SHA:
        raise ValueError("CalculiX executable identity changed")
    return deck, model, manifest


def execute(root: Path) -> dict:
    if root.exists():
        raise FileExistsError(root)
    deck, model, manifest = prepare()
    root.mkdir(parents=True)
    stem = "solid-5-supported-fy"
    (root / f"{stem}.inp").write_text(deck, encoding="ascii")
    (root / "model.json").write_text(json.dumps(model, indent=2, sort_keys=True)+"\n")
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True)+"\n")
    started = time.monotonic()
    environment = os.environ.copy()
    environment["OMP_NUM_THREADS"] = "1"
    try:
        completed = subprocess.run((str(EXE), "-i", stem), cwd=root,
                                   env=environment, capture_output=True,
                                   timeout=TIMEOUT_SECONDS, check=False)
        code, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
        failure = None
    except subprocess.TimeoutExpired as exc:
        code, stdout, stderr = None, exc.stdout or b"", exc.stderr or b""
        failure = "TIMEOUT_120_SECONDS"
    (root / "stdout.log").write_bytes(stdout)
    (root / "stderr.log").write_bytes(stderr)
    if failure is None and (code != 0 or stdout.count(b"Job finished") != 1 or
            not all((root / f"{stem}.{suffix}").exists()
                    for suffix in ("sta", "frd", "dat"))):
        failure = "INCOMPLETE_EXTERNAL_RESULT"
    record = {
        "status": "EXECUTED_PENDING_VALIDATION" if failure is None else "FAILED",
        "failure": failure, "return_code": code,
        "elapsed_s": time.monotonic()-started,
        "unexpected_diagnostics": unexpected_solver_diagnostics(
            stdout.decode(errors="replace")+stderr.decode(errors="replace"),
            c1_penalty=False),
        "files_sha256": {path.name: digest(path) for path in root.iterdir()
                         if path.is_file()},
    }
    (root / "run_result.json").write_text(json.dumps(record, indent=2, sort_keys=True)+"\n")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    args = parser.parse_args()
    if args.root is None:
        _, _, manifest = prepare()
        print(json.dumps({"preflight": "PASSED", "wrench": manifest["applied_wrench_N_Nm"]}))
    else:
        result = execute(args.root)
        print(json.dumps({key: result[key] for key in
                          ("status", "failure", "return_code", "elapsed_s")}))


if __name__ == "__main__":
    main()
