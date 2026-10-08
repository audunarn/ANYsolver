"""Read-only linear-versus-nonlinear structural work at saved free-target pose."""

import hashlib
import json
from pathlib import Path

import numpy as np

from anysolver.assembly import build_constraint_transformation
from anysolver.matrix_assembly import assemble_stiffness_matrix
from anysolver.nonlinear_static import _assemble_nonlinear_system
from test_general_contact_monolithic_cycle_restart import _case


saved_path = Path("reports/general_contact_d1_two_body_reference_compare_full_20260928.json")
saved_bytes = saved_path.read_bytes()
saved = json.loads(saved_bytes.decode("utf-8-sig"))
pose = np.asarray(saved["production_displacements"])
model, definition, _settings, program = _case()
model.apply_boundary_conditions()
stiffness, _ = assemble_stiffness_matrix(model)
internal, _tangent, _states = _assemble_nonlinear_system(
    model, pose, {}, 5, tangent=False, kinematics="von_karman",
    require_full_coordinates=True)
linear = np.asarray(stiffness @ pose).reshape(-1)
_, _, transform, offset, _, _ = build_constraint_transformation(
    stiffness, np.zeros_like(pose), model)
assert np.linalg.norm(offset) == 0.0
transform = transform.tocsr()
controlled_coordinates = []
for control in program.controls:
    assert len(control.terms) == 1
    node, name, weight = control.terms[0]
    assert name == "ux" and weight == 1.0
    dof = model.mesh.dof_manager.get_node_dofs(node)[0]
    row = transform.getrow(dof)
    assert row.nnz == 1 and row.data[0] == 1.0
    controlled_coordinates.append(int(row.indices[0]))
free = np.setdiff1d(np.arange(transform.shape[1]), controlled_coordinates)
physical_transform = transform[:, free]
defect = internal-linear
reduced = np.asarray(physical_transform.T @ defect).reshape(-1)
source_ids = sorted({node for element_id in definition.surfaces[0].element_ids
                     for node in model.mesh.elements[element_id].node_ids})
target_ids = sorted({node for element_id in definition.surfaces[1].element_ids
                     for node in model.mesh.elements[element_id].node_ids})
components = {}
for name, nodes in (("source", source_ids), ("target", target_ids)):
    values = {}
    for local, label in enumerate(("ux", "uy", "uz", "rx", "ry", "rz")):
        selected = [model.mesh.dof_manager.get_node_dofs(node)[local]
                    for node in nodes]
        masked = np.zeros_like(defect)
        masked[selected] = defect[selected]
        values[label] = float(np.linalg.norm(
            np.asarray(physical_transform.T @ masked).reshape(-1)))
    components[name] = values
print(json.dumps({
    "status": "development_free_target_structural_defect",
    "saved_comparison_sha256": hashlib.sha256(saved_bytes).hexdigest(),
    "model_bc_free_coordinates": transform.shape[1],
    "program_controlled_coordinates": controlled_coordinates,
    "physical_free_coordinates": physical_transform.shape[1],
    "reduced_structural_defect_norm_n": float(np.linalg.norm(reduced)),
    "source_and_target_component_norms": components,
}, indent=2))
