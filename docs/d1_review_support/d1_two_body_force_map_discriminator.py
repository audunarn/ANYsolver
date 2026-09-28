"""Compare production contact work with independent frozen-skin vertical work."""

import hashlib
import json
from pathlib import Path

import numpy as np

from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import linearize
from d1_two_body_reference_oracle import independent_gap_work
from test_general_contact_monolithic_cycle_restart import _case


saved_path = Path("reports/general_contact_d1_two_body_reference_compare_full_20260928.json")
saved_bytes = saved_path.read_bytes()
saved = json.loads(saved_bytes.decode("utf-8-sig"))
pose = np.asarray(saved["production_displacements"])
pressure = np.asarray(saved["production_pressure_pa"])
support = np.asarray(saved["production_support_m2"])
model, definition, settings, program = _case()
manager = GeneralS3PatchManager(model, definition, settings)
production = linearize(manager, pose, pressure*support, tangent=False)
target_ids = sorted({node for element_id in definition.surfaces[1].element_ids
                     for node in model.mesh.elements[element_id].node_ids})
target_element = model.mesh.elements[definition.surfaces[1].element_ids[0]]
offset = 0.5*target_element.thickness-target_element.reference_surface_offset
target_skin_xy = {}
for node in target_ids:
    dofs = model.mesh.dof_manager.get_node_dofs(node)
    reference = model.mesh.nodes[node]
    target_skin_xy[node] = np.array((
        reference.x+pose[dofs[0]]+offset*pose[dofs[4]],
        reference.y+pose[dofs[1]]-offset*pose[dofs[3]],
    ))
source_ids, oracle_support, work, area = independent_gap_work(
    model, definition, program.target_at(4)[0], target_skin_xy)
assert source_ids == tuple(manager.law.pressure_mode_ids)
oracle_residual = -work.T @ pressure
production_residual = production.force
difference = production_residual-oracle_residual
components = {}
for name, nodes in (("source", source_ids), ("target", target_ids)):
    values = {}
    for local, label in enumerate(("ux", "uy", "uz", "rx", "ry", "rz")):
        selected = [model.mesh.dof_manager.get_node_dofs(node)[local]
                    for node in nodes]
        values[label] = {
            "production_norm": float(np.linalg.norm(
                production_residual[selected])),
            "difference_norm": float(np.linalg.norm(difference[selected])),
        }
    components[name] = values
print(json.dumps({
    "status": "development_two_body_force_map_discriminator",
    "saved_comparison_sha256": hashlib.sha256(saved_bytes).hexdigest(),
    "support_relative_l2": float(
        np.linalg.norm(support-oracle_support)/np.linalg.norm(support)),
    "complete_residual_difference_norm": float(np.linalg.norm(difference)),
    "contact_residual_norm": float(np.linalg.norm(production_residual)),
    "component_norms": components,
}, indent=2))
