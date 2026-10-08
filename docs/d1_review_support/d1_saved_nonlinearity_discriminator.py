"""Read-only structural small-motion check at the saved 16x8 coupled pose."""

import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.sparse.linalg import spsolve

from anysolver.assembly import build_constraint_transformation
from anysolver.matrix_assembly import assemble_stiffness_matrix
from anysolver.nonlinear_static import _assemble_nonlinear_system
from scripts.general_contact_d1_mixed_mesh_jet2_schur_press import build_case


path = Path(__file__).with_name("d1_saved_16x8_near_rim_field_20260928.json")
source_bytes = path.read_bytes()
saved = json.loads(source_bytes)
assert saved["status"] == "completed" and saved["accepted_steps"] == 2
assert saved["source_y_profile"] == "near_rim8"
assert saved["load_profile"] == "distributed"
model, definition, _settings, program = build_case(
    saved["columns"], source_rows=saved["source_rows"],
    source_y_profile=saved["source_y_profile"],
    target_right_x_m=saved["target_right_x_m"],
    target_reference_slope=saved["target_reference_slope"],
    target_columns=saved["target_columns"],
    full_width_target=saved["full_width_target"],
    load_profile=saved["load_profile"],
    total_force_n=saved["total_downward_force_n"],
    steps_per_segment=saved["steps_per_segment"],
    four_phase=saved["four_phase"],
)
model.apply_boundary_conditions()
pose = np.asarray(saved["final_displacements"], dtype=float)
assert pose.shape == (model.mesh.dof_manager.total_dofs,)
stiffness, _info = assemble_stiffness_matrix(model)
nonlinear, _tangent, _states = _assemble_nonlinear_system(
    model, pose, {}, 5, tangent=False, kinematics="von_karman",
    require_full_coordinates=True,
)
linear = np.asarray(stiffness @ pose).reshape(-1)
_, _, transform, offset, _, _ = build_constraint_transformation(
    stiffness, np.zeros_like(pose), model,
)
assert np.linalg.norm(offset) == 0.0
assert len(program.controls) == 2 and program.waypoints[-1] == (0.0, 0.0)
controlled_nodes = (1, saved["columns"]+2)
controlled_dofs = tuple(int(model.mesh.dof_manager.get_node_dofs(node)[0])
                        for node in controlled_nodes)
assert max(abs(pose[dof]) for dof in controlled_dofs) < 1.0e-12
transform = transform.tocsr()
controlled_coordinates = []
for dof in controlled_dofs:
    row = transform.getrow(dof)
    assert row.nnz == 1 and row.data[0] == 1.0
    controlled_coordinates.append(int(row.indices[0]))
assert len(set(controlled_coordinates)) == len(controlled_coordinates)
free_coordinates = np.setdiff1d(np.arange(transform.shape[1]),
                                controlled_coordinates)
physical_transform = transform[:, free_coordinates]
reduced_difference = np.asarray(physical_transform.T @ (nonlinear-linear)).reshape(-1)
reduced_nonlinear = np.asarray(physical_transform.T @ nonlinear).reshape(-1)
reduced_stiffness = (physical_transform.T @ stiffness @ physical_transform).tocsc()
linear_response_to_difference = np.asarray(
    physical_transform @ spsolve(reduced_stiffness, reduced_difference),
).reshape(-1)
source_nodes = tuple(range(1, (saved["source_rows"]+1)*(saved["columns"]+1)+1))
source = {}
for node in source_nodes:
    dofs = model.mesh.dof_manager.get_node_dofs(node)
    source[node] = pose[dofs]
max_inplane = max(float(np.linalg.norm(source[node][:2])) for node in source_nodes)
max_rotation = max(float(np.max(np.abs(source[node][3:6]))) for node in source_nodes)
component_force_difference = {}
component_response = {}
for local_index, label in enumerate(("ux", "uy", "uz", "rx", "ry", "rz")):
    indices = [int(model.mesh.dof_manager.get_node_dofs(node)[local_index])
               for node in source_nodes]
    masked = np.zeros_like(pose)
    masked[indices] = nonlinear[indices]-linear[indices]
    component_force_difference[label] = float(np.linalg.norm(
        np.asarray(physical_transform.T @ masked).reshape(-1)))
    component_response[label] = float(np.max(abs(linear_response_to_difference[indices])))
max_slope = 0.0
for row in range(saved["source_rows"]+1):
    for column in range(saved["columns"]+1):
        node = 1+row*(saved["columns"]+1)+column
        for other in (node+1 if column < saved["columns"] else None,
                      node+saved["columns"]+1 if row < saved["source_rows"] else None):
            if other is None:
                continue
            first, second = model.mesh.nodes[node], model.mesh.nodes[other]
            span = np.linalg.norm(np.asarray(first.coords())-np.asarray(second.coords()))
            max_slope = max(max_slope, abs(source[node][2]-source[other][2])/span)
record = {
    "status": "development_saved_pose_structural_linearization_check",
    "saved_source_sha256": hashlib.sha256(source_bytes).hexdigest(),
    "saved_runtime_identity": saved["runtime_identity"],
    "source_nodes": len(source_nodes),
    "structural_dofs": len(pose),
    "model_bc_free_coordinates": transform.shape[1],
    "controlled_nodes": controlled_nodes,
    "controlled_dofs": controlled_dofs,
    "authoritative_free_coordinates": physical_transform.shape[1],
    "maximum_source_inplane_displacement_m": max_inplane,
    "maximum_source_rotation_rad": max_rotation,
    "maximum_transverse_secant_slope": max_slope,
    "maximum_source_deflection_m": max(abs(source[node][2]) for node in source_nodes),
    "reduced_nonlinear_force_norm_n": float(np.linalg.norm(reduced_nonlinear)),
    "reduced_nonlinear_minus_linear_norm_n": float(np.linalg.norm(reduced_difference)),
    "relative_to_total_applied_force": float(
        np.linalg.norm(reduced_difference)/saved["total_downward_force_n"]),
    "maximum_reduced_force_difference_n": float(np.max(abs(reduced_difference))),
    "source_component_force_difference_norm_n": component_force_difference,
    "source_component_linear_response_max": component_response,
    "linear_compliance_estimate_max_displacement_m": float(
        np.max(abs(linear_response_to_difference))),
    "linear_compliance_estimate_relative_to_max_source_deflection": float(
        np.max(abs(linear_response_to_difference))
        /max(abs(source[node][2]) for node in source_nodes)),
    "contact_reaction_n": float(saved["contact"]["integration_force"][2]),
}
print(json.dumps(record, indent=2))
