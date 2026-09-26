"""Separate F5 linear torque weak action from saved combined/opening stresses.

The combined +100 Nm/−1000 N state is the pre-opened physical reference.
Pure torque is used only as its linear influence; its zero-preload contact
gap is negative. Work here means a final-state force/displacement pairing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c3d20r_bond_force_recovery import read_deck, wrench
from scripts.b3_e4_f03_c3d20r_stress_force_recovery import read_stress, integrate
from scripts.b3_e4_f03_ccx_solid_bond_screen import parse_nodal_vectors
from scripts.b3_e4_f03_saved_six_gap_replay import GRID, _ports
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _action(stem: Path, model: dict) -> tuple[np.ndarray, np.ndarray, dict]:
    xyz,elements = read_deck(stem.with_suffix(".inp"))
    conn = elements["Stiffener"]
    stresses = read_stress(stem.with_suffix(".dat"),
                           first_element=len(elements["Plate"])+1,
                           element_count=len(conn))
    internal,_ = integrate(xyz,conn,stresses)
    load = np.zeros_like(xyz)
    for key,value in model["applied_nodal_forces_N"].items():
        load[int(key)] = value
    seam = np.array(model["shared_interface_node_ids"],dtype=int)
    return xyz,-(internal-load)[seam],elements


def _predict(reference: np.ndarray, translations: np.ndarray,
             rotations: np.ndarray) -> np.ndarray:
    projected = []
    for xyz in reference:
        j = min(4,max(0,int(np.floor((xyz[0]-.9)/.02+1e-8))))
        alpha = float(np.clip((xyz[0]-GRID[j])/(GRID[j+1]-GRID[j]),0.,1.))
        move = (1-alpha)*translations[j]+alpha*translations[j+1]
        spin = (1-alpha)*rotations[j]+alpha*rotations[j+1]
        projected.append(move+np.cross(spin,xyz-
                                      np.array((xyz[0],0.,.0675))))
    return np.array(projected)


def _work(action: np.ndarray, actual: np.ndarray,
          projected: np.ndarray) -> dict:
    total = float(np.sum(action*actual))
    rigid = float(np.sum(action*projected))
    remainder = total-rigid
    if not np.isfinite((total,rigid,remainder)).all() or abs(total)<1e-12:
        raise ArithmeticError("invalid torque weak work pairing")
    return {"actual_final_state_pairing_J":total,
            "rigid_section_projected_pairing_J":rigid,
            "nonrigid_remainder_pairing_J":remainder,
            "remainder_fraction_of_actual":remainder/total,
            "displacement_remainder_vector_rms_m":float(np.sqrt(
                np.mean(np.sum((actual-projected)**2,axis=1)))),
            "displacement_remainder_max_m":float(np.max(
                np.linalg.norm(actual-projected,axis=1)))}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-root",type=Path,required=True)
    args = parser.parse_args()
    root = args.evidence_root.resolve()
    if root.exists():
        raise FileExistsError(root)
    base = root.parent
    combined = base/"f03-c1-factor5-stiffener-ip-stress-dev-20260926-v1/solid-5-tip_mx"
    opening = base/"f03-c1-factor5-opening-ip-stress-dev-20260926-v1/solid-5-tip_fz"
    torque = base/"f03-ccx-c1-factor5-torque-influence-dev-20260926-v1/solid-5-tip_mx/solid-5-tip_mx"
    combined_model_path = base/"f03-ccx-c1-preopen-combined-factor5-dev-20260926-v1/solid-5-tip_mx/model.json"
    opening_model_path = base/"f03-ccx-c1-factor5-opening-influence-dev-20260926-v1/solid-5-tip_fz/model.json"
    torque_model_path = base/"f03-ccx-c1-factor5-torque-influence-dev-20260926-v1/solid-5-tip_mx/model.json"
    combined_recovery_path = base/"f03-c1-factor5-stress-force-recovery-dev-20260926-v1/result.json"
    opening_recovery_path = base/"f03-c1-factor5-opening-stress-force-recovery-dev-20260926-v1/result.json"
    split_path = base/"f03-c1-factor5-native-six-gap-dev-20260926-v6/result.json"
    models = [json.loads(path.read_text()) for path in
              (combined_model_path,opening_model_path,torque_model_path)]
    recoveries = [json.loads(path.read_text()) for path in
                  (combined_recovery_path,opening_recovery_path)]
    split = json.loads(split_path.read_text())["saved_linear_influence_split"]
    if (any(r["validation"]["status"]!="PASSED_SAVED_STATE_AND_WEAK_FORCE_CHECKS"
            for r in recoveries) or not split["same_structure_and_support"] or
            split["max_saved_displacement_superposition_difference_m"]>
            split["displacement_superposition_bound_m"]):
        raise ValueError("validated matching saved predecessors required")
    xyz_c,action_c,elements_c = _action(combined,models[0])
    xyz_o,action_o,elements_o = _action(opening,models[1])
    xyz_t,elements_t = read_deck(torque.with_suffix(".inp"))
    if (not np.array_equal(xyz_c,xyz_o) or not np.array_equal(xyz_c,xyz_t)
            or any(not np.array_equal(elements_c[k],elements_o[k]) or
                   not np.array_equal(elements_c[k],elements_t[k])
                   for k in elements_c)):
        raise ValueError("influence geometry or element map differs")
    seam = np.array(models[0]["shared_interface_node_ids"],dtype=int)
    if any(np.array(model["shared_interface_node_ids"],dtype=int).tolist()!=seam.tolist()
           for model in models[1:]):
        raise ValueError("shared bond inventory differs")
    action_t = action_c-action_o
    torque_reactions = parse_nodal_vectors(
        torque.with_suffix(".dat").read_text(errors="replace"),
        set(models[2]["boundary_node_ids"]),"forces","SUPPORTS")
    printed = np.zeros_like(xyz_c)
    for node,value in torque_reactions.items():
        printed[node] = value
    plate_root = np.array(models[2]["plate_boundary_node_ids"],dtype=int)
    complete_action = np.zeros_like(xyz_c)
    complete_action[seam] = action_t
    inferred = wrench(complete_action,xyz_c,seam)
    printed_wrench = -wrench(printed,xyz_c,plate_root)
    wrench_error = inferred-printed_wrench
    if np.max(np.abs(wrench_error))>=1e-3:
        raise ArithmeticError("torque weak action disagrees with independent support")
    torque_u = _read_frd_u(torque.with_suffix(".frd"))
    if set(torque_u)!=set(range(1,len(xyz_c))):
        raise ValueError("pure torque influence displacement inventory incomplete")
    actual = np.array([torque_u[int(node)] for node in seam])
    coords = {node:xyz_c[node] for node in range(1,len(xyz_c))}
    reports = {}
    for method in ("area","nonbond"):
        translation,rotation,fit_rms = _ports(
            coords,torque_u,elements_c,method=method)
        predicted = _predict(xyz_c[seam],translation,rotation)
        reports[method] = {"work":_work(action_t,actual,predicted),
                           "section_vector_rms_fit_m":fit_rms.tolist()}
    paths = [combined.with_suffix(suffix) for suffix in (".inp",".dat",".frd")]
    paths += [opening.with_suffix(suffix) for suffix in (".inp",".dat",".frd")]
    paths += [torque.with_suffix(suffix) for suffix in (".inp",".dat",".frd")]
    paths += [combined_model_path,opening_model_path,torque_model_path,
              combined_recovery_path,opening_recovery_path,split_path]
    result = {
        "classification":"bounded saved linear torque weak-action and work projection; not G0B acceptance",
        "decision_question":"Does rigid-section reduction omit material torque bond pairing under the same F5 physical model?",
        "outcome_rule":"A material projection remainder makes the B3 section/end port a priority, but cannot alone explain the native total-work difference. A small remainder would leave the transverse trace law as the main hypothesis. Neither outcome selects a multiplier.",
        "physical_model":"F5 35 mm plate and square bar with shared terminal 0.1 m bond; combined +100 Nm/−1000 N pre-opened field is physical; pure torque is an algebraic linear influence only",
        "inventory":{"shared_bond_nodes":len(seam),"stiffener_elements":len(elements_c["Stiffener"])},
        "torque_bar_on_plate_wrench_from_stress_N_Nm":inferred.tolist(),
        "torque_bar_on_plate_wrench_from_independent_support_N_Nm":printed_wrench.tolist(),
        "maximum_torque_wrench_difference_N_Nm":float(np.max(np.abs(wrench_error))),
        "projection":reports,
        "interpretation_limits":["force-displacement pairing is final-state bilinear work, not path-integrated energy",
                                 "pure torque alone closes sampled unbonded faces; only the pre-opened combined field has the archived positive face bound",
                                 "rigid-section fit is a projection, not the native retained B3 port",
                                 "the torque influence is stress subtraction from two individually validated linear solves, not contact traction density"],
        "inputs_sha256":{str(path.relative_to(base)):_sha(path) for path in paths},
        "runner_sha256":_sha(Path(__file__))}
    root.mkdir(parents=True)
    (root/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("torque wrench max difference",result["maximum_torque_wrench_difference_N_Nm"])
    for method,report in reports.items():
        print(method,report["work"])


if __name__=="__main__":
    main()
