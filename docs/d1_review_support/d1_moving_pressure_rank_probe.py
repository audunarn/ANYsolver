"""Independent scaled Gram rank readout at accepted deformable-target poses."""

import json
import runpy

import numpy as np

from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager


case = runpy.run_path("tests/test_general_contact_monolithic_cycle_restart.py")
full = case["_solve"](snapshots=True)
assert full.status == "completed", full.failure_reason
assert len(full.snapshots) == 8
model, definition, settings, _program = case["_case"]()
manager = GeneralS3PatchManager(model, definition, settings)
rows = []
for snapshot, history in zip(full.snapshots,
                             full.info["force_displacement_history"], strict=True):
    source, target = manager._positions(snapshot.displacements)
    state = manager.law.geometry.evaluate(source, target)
    support = np.asarray(state.reference_support)
    gram = np.asarray(state.pressure_gram)
    selected = np.flatnonzero(support > 0.0)
    block = gram[np.ix_(selected, selected)]
    assert len(selected) > 0
    diagonal = np.diag(block)
    assert np.all(diagonal > 0.0)
    normalized = block / np.sqrt(diagonal[:, None]*diagonal[None, :])
    eigen = np.linalg.eigvalsh(normalized)
    floor = len(selected)*np.finfo(float).eps*eigen[-1]
    rank = int(np.count_nonzero(eigen > floor))
    reported = history["contact"]
    assert rank == len(selected)
    assert rank == reported["pressure_gram_scaled_rank"]
    assert rank == reported["pressure_gram_supported_modes"]
    rows.append({
        "step": int(snapshot.step_index),
        "supported_modes": len(selected),
        "scaled_rank": rank,
        "smallest_scaled_eigenvalue": float(eigen[0]),
        "scaled_condition": float(eigen[-1]/eigen[0]),
        "active_pressure_modes": int(reported["active_pressure_dofs"]),
        "overlap_area_m2": float(state.overlap_area),
        "reference_support_sum_m2": float(np.sum(support)),
    })
print(json.dumps({"status": "development_moving_pressure_rank",
                  "steps": rows}, indent=2))
