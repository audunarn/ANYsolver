"""Validate the bounded F5 side-cut field and recover discrete sided work.

The independent left/right element contributions are dual to a discontinuous
cut virtual field. They are not yet the native B3 retained-port work law.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.b3_e4_f03_c3d20r_bond_force_recovery import read_deck, wrench
from scripts.b3_e4_f03_c3d20r_stress_force_recovery import integrate, read_stress
from scripts.b3_e4_f03_ccx_solid_bond_screen import (
    audit_unbonded_open, parse_nodal_vectors, parse_probe_displacements,
    recover,
)
from scripts.b3_e4_f03_solid_bond_pose_projection import _read_frd_u


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cut_wrench(force: np.ndarray, x: np.ndarray, nodes: np.ndarray) -> np.ndarray:
    # Physical axis origin at the section station; moments are spatial.
    origin = np.array((.95, 0., .0675))
    return np.r_[force[nodes].sum(axis=0),
                 np.cross(x[nodes] - origin, force[nodes]).sum(axis=0)]


def evaluate(root: Path) -> dict:
    stem = root / "solid-5-sided-port"
    inp, dat, frd = (stem.with_suffix(suffix) for suffix in (".inp", ".dat", ".frd"))
    model_path = root / "model.json"
    manifest_path = root / "manifest.json"
    run_path = root / "run_result.json"
    model = json.loads(model_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    run = json.loads(run_path.read_text())
    if (run["status"] != "EXECUTED_OUTPUT_PENDING_MECHANICAL_VALIDATION" or
            model.get("sided_port_cut_at_095_m") is not True or
            manifest["cut_m"] != .95 or
            manifest["limit"] != {"seconds": 120, "omp_threads": 1}):
        raise ValueError("the bounded side-cut source is incomplete")
    for path in (inp, dat, frd, model_path, manifest_path):
        if path.name in run["files_sha256"] and sha(path) != run["files_sha256"][path.name]:
            raise ValueError("source or solver output changed since execution")
    x, elements = read_deck(inp)
    u_dict = _read_frd_u(frd)
    if set(u_dict) != set(range(1, len(x))):
        raise ValueError("incomplete saved side-cut displacements")
    u = np.array([[0., 0., 0.]] + [u_dict[i] for i in range(1, len(x))])
    text = dat.read_text(errors="replace")
    support = np.asarray(model["boundary_node_ids"], dtype=np.int32)
    reactions = parse_nodal_vectors(text, set(map(int, support)), "forces", model["support_set"])
    probes = parse_probe_displacements(text, set(model["probe_node_ids"]))
    response = recover(model, probes, reactions)
    interface_ids = {node for pair in model["unbonded_interface_pairs"] for node in pair}
    gap = audit_unbonded_open(model, {node: u_dict[node] for node in interface_ids})
    stiffener = elements["Stiffener"]
    stress = read_stress(dat, first_element=len(elements["Plate"]) + 1,
                         element_count=len(stiffener))
    bar_force, det_min = integrate(x, stiffener, stress)
    load = np.zeros_like(x)
    for key, value in model["applied_nodal_forces_N"].items():
        load[int(key)] = value
    printed = np.zeros_like(x)
    for node, force in reactions.items():
        printed[node] = force
    root_bar = np.asarray(model["beam_root_node_ids"], dtype=np.int32)
    root_plate = np.asarray(model["plate_boundary_node_ids"], dtype=np.int32)
    seam = np.asarray(model["shared_interface_node_ids"], dtype=np.int32)
    all_bar = np.unique(stiffener.ravel())
    free = np.setdiff1d(all_bar, np.r_[root_bar, seam])
    bar_residual = bar_force - load
    bar_on_plate = -bar_residual[seam]
    stress_wrench = wrench(-bar_residual, x, seam)
    support_wrench = -wrench(printed, x, root_plate)
    validation = {
        "bar_free_max_residual_N": float(np.max(np.abs(bar_residual[free]))),
        "bar_root_RF_max_difference_N": float(np.max(np.abs(bar_residual[root_bar] - printed[root_bar]))),
        "bond_vs_plate_support_max_wrench_difference_N_Nm": float(np.max(np.abs(stress_wrench - support_wrench))),
        "bar_on_plate_wrench_N_Nm": stress_wrench.tolist(),
        "plate_support_equivalent_wrench_N_Nm": support_wrench.tolist(),
        "bar_on_plate_work_J": float(np.sum(bar_on_plate * u[seam])),
        "minimum_jacobian_m3": det_min,
        "sampled_unbonded_gap": gap,
    }
    # This is the same numerical admission as the prior F5 printed-stress
    # recovery, plus a sampled positive-gap prerequisite. It is not an
    # outward-rounded deformed nonintersection proof.
    admitted = (validation["bar_free_max_residual_N"] < 1e-3 and
                validation["bar_root_RF_max_difference_N"] < 1e-3 and
                validation["bond_vs_plate_support_max_wrench_difference_N_Nm"] < 1e-3 and
                gap["negative_nodal_gaps"] == 0 and gap["sampled_face_negative_points"] == 0 and
                gap["sampled_face_minimum_reference_normal_gap_m"] > 0)
    ends = x[stiffener, 0]
    left = np.flatnonzero(np.max(ends, axis=1) <= .95 + 1e-12)
    right = np.flatnonzero(np.min(ends, axis=1) >= .95 - 1e-12)
    if len(left) + len(right) != len(stiffener):
        raise ArithmeticError("stiffener elements cross or duplicate the side cut")
    cut = np.flatnonzero(np.isclose(x[:, 0], .95, rtol=0, atol=1e-12))
    cut = np.intersect1d(cut, all_bar)
    side = {}
    side_forces = {}
    for label, ids in (("left", left), ("right", right)):
        values, minimum = integrate(x, stiffener[ids], stress[ids])
        side_forces[label] = values
        cut_wrench = _cut_wrench(values, x, cut)
        side[label] = {"elements": len(ids), "cut_wrench_N_Nm_about_axis": cut_wrench.tolist(),
                       "minimum_jacobian_m3": minimum,
                       "cut_twist_virtual_work_J_per_rad": float(cut_wrench[3])}
    recomposed = side_forces["left"] + side_forces["right"]
    side_sum = side_forces["left"] + side_forces["right"]
    nonbond = np.setdiff1d(cut, seam)
    shared_cut = np.intersect1d(cut, seam)
    interface_action = np.zeros_like(x)
    interface_action[seam] = bar_on_plate
    cut_wrench_balance = (_cut_wrench(side_sum, x, cut) +
                          _cut_wrench(interface_action, x, cut) -
                          _cut_wrench(load, x, cut))
    cut_balance = {
        "meaning": "element partition and seam action closure are algebraic bookkeeping identities, not independent force validation",
        "element_partition_max_force_difference_N": float(np.max(np.abs(recomposed - bar_force))),
        "nonbond_cut_max_left_plus_right_residual_N": float(np.max(np.abs(side_sum[nonbond] - load[nonbond]))),
        "shared_cut_max_left_plus_right_plus_interface_N": float(np.max(np.abs(
            side_sum[shared_cut] - load[shared_cut] + interface_action[shared_cut]))),
        "interface_cut_wrench_N_Nm_about_axis": _cut_wrench(interface_action, x, cut).tolist(),
        "left_right_interface_cut_wrench_defect_N_Nm": cut_wrench_balance.tolist(),
        "cut_nodes": len(cut), "shared_cut_nodes": len(shared_cut),
    }
    return {
        "classification": "bounded printed-stress sided solid work, not a native B3 port qualification",
        "status": "PASSED_BOUNDED_STRESS_AND_SAMPLED_GAP_GUARDS" if admitted else "REFERENCE_VALIDATION_FAILED",
        "validation": validation,
        "cut_sides": side,
        "cut_balance": cut_balance,
        "physical_response": {key: response[key] for key in (
            "applied_load_work_j", "applied_wrench_N_Nm",
            "support_wrench_N_Nm", "wrench_imbalance_N_Nm")
            if key in response},
        "limitations": ["element-side cut forces are dual to discontinuous solid virtual fields, not automatically native B3 retained-port rotations",
                       "the side-restricted twist at bonded cut nodes is not an admissible virtual displacement of the intact shared-node assembly unless companion plate/interface work is included",
                       "21 cut nodes share the plate/bar bond; side wrenches need not be opposite and cut closure is algebraic bookkeeping",
                       "local plate-side interface traction is not independently reconstructed",
                       "same x=.95 cut and physical setup but a changed terminal mesh; compare observables before accuracy scoring",
                       "sampled reference-normal gaps do not prove deformed nonintersection",
                       "one load and one grid; no line-space, G0B or external-accuracy acceptance"],
        "inputs_sha256": {str(path): sha(path) for path in
                          (inp, dat, frd, model_path, manifest_path, run_path)},
        "source_sha256": sha(Path(__file__)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    result = evaluate(args.root)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"],
                      "validation": {key: result["validation"][key]
                      for key in ("bar_free_max_residual_N", "bar_root_RF_max_difference_N",
                                  "bond_vs_plate_support_max_wrench_difference_N_Nm")},
                      "cut_balance": result["cut_balance"]}))


if __name__ == "__main__":
    main()
