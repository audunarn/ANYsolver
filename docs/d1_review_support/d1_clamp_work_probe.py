"""Measure whether accepted free-target poses resolve constrained contact couples."""

import json

import numpy as np

from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import linearize
from test_general_contact_monolithic_cycle_restart import _case, _solve


full = _solve(snapshots=True)
assert full.status == "completed"
model, definition, settings, _ = _case()
manager = GeneralS3PatchManager(model, definition, settings)
rows = []
for step in (4, 8):
    snapshot = full.snapshots[step-1]
    record = full.info["force_displacement_history"][step-1]["contact"]
    nodal_forces = (np.asarray(record["numerical_pressure_pa"])
                    * np.asarray(record["reference_support_m2"]))
    base = linearize(manager, snapshot.displacements, nodal_forces,
                     tangent=True)
    for node in (11, 14):
        for axis in (2, 3, 4, 5):
            direction = np.zeros_like(snapshot.displacements)
            direction[model.mesh.dof_manager.get_node_dofs(node)[axis]] = 1.0
            h = 1e-7
            plus = linearize(manager, snapshot.displacements+h*direction,
                             nodal_forces, tangent=False)
            minus = linearize(manager, snapshot.displacements-h*direction,
                              nodal_forces, tangent=False)
            observed = (plus.force-minus.force)/(2*h)
            predicted = base.tangent @ direction
            scale = max(np.linalg.norm(observed), np.linalg.norm(predicted))
            rows.append({
                "step": step, "node": node, "axis": axis,
                "force_action_norm": float(scale),
                "relative_directional_error": float(
                    np.linalg.norm(observed-predicted)/scale)
                    if scale > 0 else None,
                "branch_equal": bool(base.state.overlap_signature
                                     == plus.state.overlap_signature
                                     == minus.state.overlap_signature),
                "triangles_equal": bool(base.state.integration_triangles
                                        == plus.state.integration_triangles
                                        == minus.state.integration_triangles),
                "mapped_contact_generalized_force": float(
                    base.force @ direction),
            })
print(json.dumps({"status": "development_clamp_work_probe",
                  "rows": rows}, indent=2))
