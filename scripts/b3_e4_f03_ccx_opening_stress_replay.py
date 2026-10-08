"""Output-only C1 F5 opening stress replay under the frozen development cap.

This makes the saved opening influence's weak bond action available for
subtraction from the pre-opened combined action. It does not qualify the
zero-preload pure-torque field as a physical contact reference.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import time

import numpy as np

from scripts.b3_e4_f03_ccx_saved_stress_replay import (
    EXE, EXPECTED_EXE, LIMIT_SECONDS, sha)
from scripts.b3_e4_f03_ccx_solid_bond_screen import (
    parse_nodal_vectors, split_left_root_support_wrenches)
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/".qualification/b3-ge-e4-pl"
SOURCE = BASE/"f03-ccx-c1-factor5-opening-influence-dev-20260926-v1/solid-5-tip_fz"
TARGET = BASE/"f03-c1-factor5-opening-ip-stress-dev-20260926-v1"
STEM = "solid-5-tip_fz"
INSERT = "*EL PRINT,ELSET=Stiffener\nS\n"


def source() -> dict:
    model_path = SOURCE/"model.json"
    model = json.loads(model_path.read_text())
    required = {"factor":5, "element_family":"C3D20R",
                "bond_policy":"terminal", "contact_policy":"none",
                "boundary_policy":"left_root", "tip_load_map":"quadratic_face",
                "bar_clearance_um":2, "shear":"tip_fz", "reverse_tip_fz":True}
    if any(model.get(key)!=value for key,value in required.items()):
        raise ValueError("opening source differs from frozen C1 F5 model")
    if not (SOURCE/(STEM+".inp")).is_file() or sha(EXE)!=EXPECTED_EXE:
        raise ValueError("saved source or pinned CalculiX executable unavailable")
    return model


def prepare() -> None:
    model = source()
    original = SOURCE/(STEM+".inp")
    deck = original.read_text()
    if deck.count("*END STEP\n")!=1 or "*EL PRINT" in deck:
        raise ValueError("unique output-only stress insertion unavailable")
    edited = deck.replace("*END STEP\n", INSERT+"*END STEP\n")
    if edited.replace(INSERT,"")!=deck:
        raise ArithmeticError("physical deck changed during output insertion")
    if TARGET.exists():
        raise FileExistsError("versioned output already exists")
    TARGET.mkdir(parents=True)
    stress_deck = TARGET/(STEM+".inp")
    stress_deck.write_text(edited)
    manifest = {
        "classification":"bounded development output-only replay; not G0B acceptance",
        "question":"Does the opening influence account for the combined solid bond work remainder, leaving a distinct torsional remainder?",
        "outcome_rule":"Require exact physical-deck preservation, source/replay support-reaction and full-displacement parity; then subtract opening and combined weak nodal actions to attribute linear torque work. A material torque residual directs section/end-port scrutiny; a small residual shifts attention to transverse connection mechanics. No result alone selects a line space.",
        "source_git":subprocess.run(("git","rev-parse","HEAD"),cwd=ROOT,
                                    capture_output=True,text=True,check=True).stdout.strip(),
        "runner_sha256":sha(Path(__file__)),
        "source_deck_sha256":sha(original),
        "stress_deck_sha256":sha(stress_deck),
        "source_model_sha256":sha(SOURCE/"model.json"),
        "source_frd_sha256":sha(SOURCE/(STEM+".frd")),
        "executable_sha256":sha(EXE),
        "output_only_deck_diff":INSERT,
        "omp_threads":1,"timeout_seconds":LIMIT_SECONDS,
        "source_folder":str(SOURCE.relative_to(ROOT)),
        "limitations":["pure opening is a saved linear influence",
                       "the torque influence obtained by subtraction remains contact-inadmissible without pre-opening",
                       "integration-point stress gives weak nodal action, not face traction density"]}
    (TARGET/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print("prepared",TARGET,"deck",manifest["stress_deck_sha256"])


def execute() -> None:
    model = source()
    manifest = json.loads((TARGET/"manifest.json").read_text())
    deck = TARGET/(STEM+".inp")
    if (sha(deck)!=manifest["stress_deck_sha256"] or
            sha(SOURCE/(STEM+".inp"))!=manifest["source_deck_sha256"] or
            sha(SOURCE/(STEM+".frd"))!=manifest["source_frd_sha256"] or
            sha(EXE)!=manifest["executable_sha256"] or
            (TARGET/"result.json").exists()):
        raise ValueError("prepared source changed or replay already executed")
    environment = os.environ.copy()
    environment["OMP_NUM_THREADS"] = "1"
    start = time.monotonic()
    timed_out = False
    code = None
    try:
        process = subprocess.run((str(EXE),"-i",STEM),cwd=TARGET,
                                 env=environment,capture_output=True,
                                 timeout=LIMIT_SECONDS,check=False)
        code,stdout,stderr = process.returncode,process.stdout,process.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout,stderr = exc.stdout or b"",exc.stderr or b""
    elapsed = time.monotonic()-start
    (TARGET/"stdout.log").write_bytes(stdout)
    (TARGET/"stderr.log").write_bytes(stderr)
    result = {"elapsed_s":elapsed,"timed_out":timed_out,"exit_code":code,
              "status":"FAILED_OR_INCOMPLETE","source_git":manifest["source_git"]}
    dat,frd = TARGET/(STEM+".dat"),TARGET/(STEM+".frd")
    if code==0 and dat.is_file() and frd.is_file():
        supports = set(model["boundary_node_ids"])
        old_rf = parse_nodal_vectors((SOURCE/(STEM+".dat")).read_text(errors="replace"),
                                     supports,"forces","SUPPORTS")
        new_rf = parse_nodal_vectors(dat.read_text(errors="replace"),
                                     supports,"forces","SUPPORTS")
        rf_error = max(float(np.max(abs(new_rf[n]-old_rf[n]))) for n in supports)
        old_u,new_u = (_read_frd_u(SOURCE/(STEM+".frd")),_read_frd_u(frd))
        if set(old_u)!=set(new_u):
            raise ValueError("replay displacement inventory changed")
        u_error = max(float(np.max(abs(new_u[n]-old_u[n]))) for n in old_u)
        result.update({"maximum_support_RF_difference_N":rf_error,
                       "maximum_saved_U_difference_m":u_error,
                       "original_support_wrenches_N_Nm":split_left_root_support_wrenches(model,old_rf),
                       "replay_support_wrenches_N_Nm":split_left_root_support_wrenches(model,new_rf),
                       "stress_header_present":"stresses" in dat.read_text(errors="replace").lower(),
                       "dat_sha256":sha(dat),"frd_sha256":sha(frd)})
        if rf_error<1e-4 and u_error<5e-10 and result["stress_header_present"]:
            result["status"] = "COMPLETE_OUTPUT_ONLY_REPLAY"
    (TARGET/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(result["status"],f"{elapsed:.3f} s",
          "RF difference",result.get("maximum_support_RF_difference_N"),
          "U difference",result.get("maximum_saved_U_difference_m"))
    if result["status"]!="COMPLETE_OUTPUT_ONLY_REPLAY":
        raise RuntimeError("opening stress replay did not preserve the saved state")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("prepare","execute"))
    args = parser.parse_args()
    (prepare if args.mode=="prepare" else execute)()


if __name__=="__main__":
    main()
