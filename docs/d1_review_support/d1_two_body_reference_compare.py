"""One bounded production/oracle comparison for the free-target D1 slide pose."""

import hashlib
import json
import subprocess
import time
from pathlib import Path

import numpy as np
import anysolver

from d1_two_body_reference_oracle import solve_reference
from test_general_contact_monolithic_cycle_restart import _case, _solve


started = time.perf_counter()
model, definition, _settings, program = _case()
oracle = solve_reference(model, definition, program, 4)
oracle_seconds = time.perf_counter()-started
production = _solve(stop=0.5, snapshots=True)
if production.status != "completed" or len(production.snapshots) != 4:
    raise RuntimeError(
        f"bounded production comparison failed: {production.status}, "
        f"{production.failure_reason}, {len(production.snapshots)} snapshots")
pose = production.snapshots[3].displacements
certificate = production.info["force_displacement_history"][3]["contact"]
ids = tuple(certificate["source_pressure_node_ids"])
assert ids == oracle["source_pressure_nodes"]
production_pressure = np.asarray(certificate["numerical_pressure_pa"])
production_support = np.asarray(certificate["reference_support_m2"])
production_gap = np.asarray(certificate["normalized_weighted_gap_m"])
source_ids = sorted({node for element_id in definition.surfaces[0].element_ids
                     for node in model.mesh.elements[element_id].node_ids})
target_ids = sorted({node for element_id in definition.surfaces[1].element_ids
                     for node in model.mesh.elements[element_id].node_ids})

def coordinates(node_ids, local):
    return np.array([model.mesh.dof_manager.get_node_dofs(node)[local]
                     for node in node_ids], dtype=int)

source_ux = coordinates(source_ids, 0)
source_uy = coordinates(source_ids, 1)
source_uz = coordinates(source_ids, 2)
target_ux = coordinates(target_ids, 0)
target_uy = coordinates(target_ids, 1)
target_uz = coordinates(target_ids, 2)
target_rotations = np.concatenate([coordinates(target_ids, axis)
                                    for axis in (3, 4, 5)])
reference_pose = oracle["displacement"]
reference_gap_at_production = (
    oracle["initial_gap"]
    + oracle["weighted_gap_work"] @ pose/oracle["support"])
pressure_scale = max(np.linalg.norm(oracle["pressure"]), 1e-15)
force_scale = max(abs(oracle["integrated_force"]), 1e-15)
record = {
    "status": "development_two_body_reference_footprint_comparison",
    "source_commit": subprocess.check_output(
        ("git", "rev-parse", "HEAD"), text=True).strip(),
    "anysolver_module": str(Path(anysolver.__file__).resolve()),
    "oracle_source_sha256": hashlib.sha256(Path(
        "docs/d1_review_support/d1_two_body_reference_oracle.py").read_bytes()
    ).hexdigest(),
    "production_accepted_steps": len(production.snapshots),
    "production_status": production.status,
    "production_displacements": pose.tolist(),
    "production_pressure_pa": production_pressure.tolist(),
    "production_support_m2": production_support.tolist(),
    "production_normalized_gap_m": production_gap.tolist(),
    "oracle_displacements": reference_pose.tolist(),
    "oracle_pressure_pa": oracle["pressure"].tolist(),
    "oracle_support_m2": oracle["support"].tolist(),
    "oracle_seconds": oracle_seconds,
    "complete_elapsed_seconds": time.perf_counter()-started,
    "reference_overlap_area_m2": oracle["integrated_area"],
    "production_support_sum_m2": float(np.sum(production_support)),
    "reference_support_sum_m2": float(np.sum(oracle["support"])),
    "support_relative_l2": float(
        np.linalg.norm(production_support-oracle["support"])
        /np.linalg.norm(oracle["support"])),
    "reference_active_modes": int(np.count_nonzero(oracle["pressure"] > 0)),
    "production_active_modes": int(np.count_nonzero(production_pressure > 0)),
    "reference_integrated_force_n": oracle["integrated_force"],
    "production_integrated_force_n": float(
        certificate["integration_force"][2]),
    "integrated_force_relative_error": float(
        abs(certificate["integration_force"][2]-oracle["integrated_force"])
        /force_scale),
    "pressure_relative_l2_error": float(
        np.linalg.norm(production_pressure-oracle["pressure"])
        /pressure_scale),
    "maximum_gap_difference_at_production_pose_m": float(
        np.max(abs(production_gap-reference_gap_at_production))),
    "source_free_inplane_motion_max_m": float(
        max(np.max(abs(pose[source_ux]-program.target_at(4)[0])),
            np.max(abs(pose[source_uy])))),
    "target_inplane_motion_max_m": float(
        max(np.max(abs(pose[target_ux])), np.max(abs(pose[target_uy])))),
    "target_rotation_max_rad": float(np.max(abs(pose[target_rotations]))),
    "source_uz_max_difference_m": float(
        np.max(abs(pose[source_uz]-reference_pose[source_uz]))),
    "target_uz_max_difference_m": float(
        np.max(abs(pose[target_uz]-reference_pose[target_uz]))),
    "target_rotation_max_difference_rad": float(
        np.max(abs(pose[target_rotations]-reference_pose[target_rotations]))),
}
print(json.dumps(record, indent=2))
