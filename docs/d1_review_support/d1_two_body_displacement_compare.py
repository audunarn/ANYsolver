"""Bounded ordinary-displacement free-target solve versus independent Q1/S3 KKT."""

import hashlib
import json
import subprocess
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

from anysolver import solve_static_nonlinear
from anysolver.boundary import BoundaryCondition
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import linearize
from anysolver.nonlinear_static import DisplacementControl
from scripts.general_contact_d1_free_target_press_probe import build_free_target_case

from d1_two_body_displacement_oracle import solve_displacement_reference


def case():
    model, definition, settings, _program = build_free_target_case(
        4, steps_per_segment=2, four_phase=True,
        enforcement_solver="monolithic_active_set")
    model.add_boundary_condition(BoundaryCondition(
        "source_x_support", (1, 6), {"ux": 0.0}))
    settings = replace(settings, complementarity_force_scale_n=0.01)
    control = DisplacementControl(
        node_id=5, dof="uz", target_displacement=-8.0e-5)
    return model, definition, settings, control


started = time.perf_counter()
model, definition, settings, control = case()
oracle = solve_displacement_reference(model, definition, control)
oracle_seconds = time.perf_counter()-started
production_model, production_definition, production_settings, production_control = case()
production = solve_static_nonlinear(
    production_model, control="displacement",
    displacement_control=production_control, num_steps=4,
    contact=production_definition, contact_settings=production_settings,
    max_iterations=18, emit_restart_checkpoint=True)
assert production.status == "completed", production.failure_reason
contact = production.info["general_contact"]
production_pressure = np.asarray(contact["numerical_pressure_pa"])
production_support = np.asarray(contact["reference_support_m2"])
production_gap = np.asarray(contact["normalized_weighted_gap_m"])
assert tuple(contact["source_pressure_node_ids"]) == oracle["source_pressure_nodes"]
manager = GeneralS3PatchManager(production_model, production_definition,
                                 production_settings)
mapped = linearize(manager, production.displacements,
                   production_pressure*production_support, tangent=False)
production_work = float(-mapped.force @ production.displacements)
target_ids = sorted({node for element_id in definition.surfaces[1].element_ids
                     for node in model.mesh.elements[element_id].node_ids})
target_translation = [model.mesh.dof_manager.get_node_dofs(node)[:3]
                      for node in target_ids]
target_rotation = [model.mesh.dof_manager.get_node_dofs(node)[3:6]
                   for node in target_ids]
target_translation = np.asarray(target_translation).ravel()
target_rotation = np.asarray(target_rotation).ravel()
source_ids = sorted({node for element_id in definition.surfaces[0].element_ids
                     for node in model.mesh.elements[element_id].node_ids})
source_inplane = np.asarray([
    model.mesh.dof_manager.get_node_dofs(node)[axis]
    for node in source_ids for axis in (0, 1)])
control_reaction = float(production.info[
    "force_displacement_history"][-1]["reaction_generalized"][0])
record = {
    "status": "development_free_target_ordinary_displacement_oracle",
    "source_commit": subprocess.check_output(
        ("git", "rev-parse", "HEAD"), text=True).strip(),
    "oracle_source_sha256": hashlib.sha256(Path(
        "docs/d1_review_support/d1_two_body_displacement_oracle.py"
    ).read_bytes()).hexdigest(),
    "production_status": production.status,
    "accepted_steps": len(production.steps),
    "has_checkpoint": production.restart_checkpoint is not None,
    "oracle_seconds": oracle_seconds,
    "complete_elapsed_seconds": time.perf_counter()-started,
    "oracle_active_modes": int(np.count_nonzero(oracle["pressure"] > 0)),
    "production_active_modes": int(np.count_nonzero(production_pressure > 0)),
    "oracle_integrated_force_n": oracle["integrated_force"],
    "production_integrated_force_n": float(contact["integration_force"][2]),
    "integrated_force_relative_error": float(
        abs(contact["integration_force"][2]-oracle["integrated_force"])
        /abs(oracle["integrated_force"])),
    "pressure_relative_l2_error": float(
        np.linalg.norm(production_pressure-oracle["pressure"])
        /np.linalg.norm(oracle["pressure"])),
    "support_relative_l2_error": float(
        np.linalg.norm(production_support-oracle["support"])
        /np.linalg.norm(oracle["support"])),
    "maximum_gap_difference_at_production_pose_m": float(np.max(abs(
        production_gap-(oracle["reference_gap"]
                        +oracle["weighted_gap_work"]
                        @ production.displacements/oracle["support"])))),
    "oracle_control_reaction_n": oracle["control_reaction"],
    "production_control_reaction_n": control_reaction,
    "control_reaction_relative_error": float(
        abs(control_reaction+oracle["control_reaction"])
        /abs(oracle["control_reaction"])),
    "oracle_mapped_contact_work_j": oracle["mapped_contact_work"],
    "production_mapped_contact_work_j": production_work,
    "mapped_work_relative_error": float(
        abs(production_work-oracle["mapped_contact_work"])
        /abs(oracle["mapped_contact_work"])),
    "target_translation_max_difference_m": float(np.max(abs(
        production.displacements[target_translation]
        -oracle["displacement"][target_translation]))),
    "target_rotation_max_difference_rad": float(np.max(abs(
        production.displacements[target_rotation]
        -oracle["displacement"][target_rotation]))),
    "source_inplane_max_m": float(np.max(
        abs(production.displacements[source_inplane]))),
}
print(json.dumps(record, indent=2))
