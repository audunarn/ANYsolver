"""One bounded F5 solid execution with an explicit x=.95 m element-side cut.

This is a new reference construction for one-sided native port work. It does
not score a line law or consume formal F03 qualification authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import numpy as np

from scripts.b3_e4_f03_c3d20r_bond_force_recovery import read_deck, wrench
from scripts.b3_e4_f03_ccx_solid_bond_screen import EXE, EXE_SHA, TIMEOUT_SECONDS, build


HISTORICAL = Path(".qualification/b3-ge-e4-pl/f03-ccx-c1-preopen-combined-factor5-dev-20260926-v1/solid-5-tip_mx")
BUILD_ARGS = dict(boundary_policy="left_root", bond_policy="terminal",
                  contact_policy="none", element_family="C3D20R",
                  tip_mx_gap_audit=True, bar_clearance_um=2,
                  plate_thickness_mm=35, tip_load_map="quadratic_face",
                  full_displacement_output=True,
                  bar_reference_profile="c1_tangent",
                  torque_with_opening_fz=True)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(root: Path) -> dict:
    if root.exists():
        raise FileExistsError(root)
    root.mkdir(parents=True)
    started = time.monotonic()
    historical_deck, historical_model = build(5, "tip_mx", **BUILD_ARGS)
    if historical_deck != (HISTORICAL / "solid-5-tip_mx.inp").read_text():
        raise ArithmeticError("default generator no longer reproduces F5 deck")
    if json.loads(json.dumps(historical_model)) != json.loads(
            (HISTORICAL / "model.json").read_text()):
        raise ArithmeticError("default generator no longer reproduces F5 model")
    deck, model = build(5, "tip_mx", sided_port_cut=True, **BUILD_ARGS)
    if (model["sided_port_cut_at_095_m"] is not True or
            model["bond_interval_m"] != [.9, 1.] or
            model["bar_reference_profile"] != "C1_TWO_QUADRATIC_TANGENT_ALIGNED_V1"):
        raise ArithmeticError("new reference changed the physical contract")
    deck = deck.replace("*END STEP\n", "*EL PRINT,ELSET=Stiffener\nS\n*END STEP\n")
    if deck.count("*EL PRINT,ELSET=Stiffener") != 1:
        raise ArithmeticError("stress output was not inserted once")
    stem = "solid-5-sided-port"
    inp = root / (stem + ".inp")
    inp.write_text(deck, encoding="ascii")
    model_path = root / "model.json"
    model_path.write_text(json.dumps(model, indent=2, sort_keys=True) + "\n")
    xyz, elements = read_deck(inp)
    cut = .95
    bar_conn = elements["Stiffener"]
    ends = xyz[bar_conn, 0]
    left = np.max(ends, axis=1) <= cut + 1e-12
    right = np.min(ends, axis=1) >= cut - 1e-12
    if not np.all(left | right) or not np.any(left) or not np.any(right):
        raise ArithmeticError("bar elements still cross the sided-port cut")
    plate_conn = elements["Plate"]
    plate_x = xyz[plate_conn, 0]
    if np.any((np.min(plate_x, axis=1) < cut - 1e-12) &
              (np.max(plate_x, axis=1) > cut + 1e-12)):
        raise ArithmeticError("plate elements still cross the shared cut")
    applied = np.zeros_like(xyz)
    for key, value in model["applied_nodal_forces_N"].items():
        applied[int(key)] = value
    applied_wrench = wrench(applied, xyz, np.arange(1, len(xyz)))
    if np.max(np.abs(applied_wrench - np.array((0., 0., -1000., 100., 1000., 0.)))) > 1e-7:
        raise ArithmeticError("new mesh changed the applied physical wrench")
    if sha(EXE) != EXE_SHA:
        raise ArithmeticError("CalculiX executable identity changed")
    manifest = {
        "classification": "bounded F03 saved-solid sided-port reference, not G0B qualification",
        "decision": "Can an explicit x=.95 m element boundary produce validated left/right stress work for the native port question?",
        "outcomes": "A complete balanced and pre-opened field with recoverable side contributions advances to a one-sided work check; failure or timeout stops this reference without an automatic finer rerun.",
        "physical_model": "F5 C1 35 mm plate, 100 mm square bar, x=.9–1 m shared bond, 2 um clearance taper, left/root supports, consistent +100 Nm and -1000 N end-face loads, no contact",
        "only_mesh_change": "insert x=.95 m as a base cut in both domains; save integration-point stiffener stresses",
        "historical_deck_text_equal": True, "historical_model_json_equal": True,
        "cut_m": cut, "left_bar_elements": int(np.count_nonzero(left)),
        "right_bar_elements": int(np.count_nonzero(right)),
        "bar_elements": len(bar_conn), "plate_elements": len(plate_conn),
        "nodes": len(xyz) - 1, "shared_face_nodes": model["shared_interface_nodes"],
        "applied_wrench_N_Nm": applied_wrench.tolist(),
        "limit": {"seconds": TIMEOUT_SECONDS, "omp_threads": 1},
        "executable_sha256": sha(EXE),
        "source_sha256": sha(Path(__file__)),
        "generator_sha256": sha(Path(build.__code__.co_filename)),
        "historical_deck_sha256": sha(HISTORICAL / "solid-5-tip_mx.inp"),
        "input_deck_sha256": sha(inp),
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    environment = os.environ.copy()
    environment["OMP_NUM_THREADS"] = "1"
    try:
        result = subprocess.run((str(EXE), "-i", stem), cwd=root,
                                env=environment, capture_output=True,
                                timeout=TIMEOUT_SECONDS, check=False)
        code = result.returncode
        stdout, stderr = result.stdout, result.stderr
        failure = None
    except subprocess.TimeoutExpired as exc:
        code = None
        stdout, stderr = exc.stdout or b"", exc.stderr or b""
        failure = "TIMEOUT_120_SECONDS"
    (root / "stdout.log").write_bytes(stdout)
    (root / "stderr.log").write_bytes(stderr)
    sta = root / (stem + ".sta")
    frd = root / (stem + ".frd")
    dat = root / (stem + ".dat")
    if failure is None and (code != 0 or not sta.exists() or not frd.exists()
                            or not dat.exists() or stdout.count(b"Job finished") != 1):
        failure = "INCOMPLETE_EXTERNAL_RESULT"
    record = {
        "status": "EXECUTED_OUTPUT_PENDING_MECHANICAL_VALIDATION" if failure is None else "FAILED",
        "failure": failure, "return_code": code,
        "elapsed_s": time.monotonic() - started,
        "files_sha256": {p.name: sha(p) for p in root.iterdir() if p.is_file()},
        "limits": ["one new mesh; physical gap, support wrench, side cancellation and work are not yet checked",
                   "a completed external process is not a numerical comparison or G0B acceptance"],
    }
    (root / "run_result.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    record = run(args.root.resolve())
    print(json.dumps({key: record[key] for key in ("status", "failure", "return_code", "elapsed_s")}))


if __name__ == "__main__":
    main()
