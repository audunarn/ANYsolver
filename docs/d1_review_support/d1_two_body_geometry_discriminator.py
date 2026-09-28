"""Offline effect of target physical-skin XY motion on the independent oracle."""

import hashlib
import json
from pathlib import Path

import numpy as np

from d1_two_body_reference_oracle import solve_reference
from test_general_contact_monolithic_cycle_restart import _case


saved_path = Path("reports/general_contact_d1_two_body_reference_compare_full_20260928.json")
saved_bytes = saved_path.read_bytes()
saved = json.loads(saved_bytes.decode("utf-8-sig"))
pose = np.asarray(saved["production_displacements"])
production_pressure = np.asarray(saved["production_pressure_pa"])
production_support = np.asarray(saved["production_support_m2"])
production_gap = np.asarray(saved["production_normalized_gap_m"])
model, definition, _settings, program = _case()
target_ids = sorted({node for element_id in definition.surfaces[1].element_ids
                     for node in model.mesh.elements[element_id].node_ids})
target_element = model.mesh.elements[definition.surfaces[1].element_ids[0]]
assert np.allclose(target_element.physical_reference_director,
                   (0.0, 0.0, 1.0), atol=1e-12)
offset = 0.5*target_element.thickness-target_element.reference_surface_offset
skin = {}
for node in target_ids:
    dofs = model.mesh.dof_manager.get_node_dofs(node)
    reference = model.mesh.nodes[node]
    skin[node] = np.array((
        reference.x+pose[dofs[0]]+offset*pose[dofs[4]],
        reference.y+pose[dofs[1]]-offset*pose[dofs[3]],
    ))
max_skin_xy_shift = max(float(np.linalg.norm(
    skin[node]-np.array((model.mesh.nodes[node].x, model.mesh.nodes[node].y))))
    for node in target_ids)

def summarize(label, override):
    fresh_model, fresh_definition, _settings, fresh_program = _case()
    oracle = solve_reference(fresh_model, fresh_definition, fresh_program, 4,
                             override)
    gap_at_pose = (oracle["initial_gap"]
                   +oracle["weighted_gap_work"] @ pose/oracle["support"])
    return {
        "model": label,
        "area_m2": oracle["integrated_area"],
        "support_relative_l2": float(
            np.linalg.norm(production_support-oracle["support"])
            /np.linalg.norm(production_support)),
        "gap_at_production_pose_max_abs_error_m": float(
            np.max(abs(production_gap-gap_at_pose))),
        "integrated_force_n": oracle["integrated_force"],
        "force_relative_error": float(
            abs(saved["production_integrated_force_n"]
                -oracle["integrated_force"])
            /abs(saved["production_integrated_force_n"])),
        "pressure_relative_l2": float(
            np.linalg.norm(production_pressure-oracle["pressure"])
            /np.linalg.norm(production_pressure)),
        "active_modes": int(np.count_nonzero(oracle["pressure"] > 0)),
    }

print(json.dumps({
    "status": "development_frozen_target_skin_geometry_discriminator",
    "saved_comparison_sha256": hashlib.sha256(saved_bytes).hexdigest(),
    "oracle_source_sha256": hashlib.sha256(Path(
        "docs/d1_review_support/d1_two_body_reference_oracle.py").read_bytes()
    ).hexdigest(),
    "maximum_target_skin_xy_shift_m": max_skin_xy_shift,
    "reference_footprint": summarize("reference_footprint", None),
    "frozen_production_target_skin_xy": summarize(
        "frozen_production_target_skin_xy", skin),
}, indent=2))
