"""Offline active pressure-to-gap response at a saved near-rim pose.

Development discriminator only: a local active Jacobian is not a spatial or
nonlinear pressure-space qualification.
"""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import psutil
from scipy import sparse
from scipy.sparse.linalg import splu

import anysolver
from anysolver.assembly import build_constraint_transformation
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import linearize
from anysolver.matrix_assembly import assemble_stiffness_matrix
from anysolver.nonlinear_static import _assemble_nonlinear_system
from scripts.general_contact_d1_mixed_mesh_jet2_schur_press import build_case


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--saved", type=Path,
    default=Path(__file__).with_name("d1_saved_16x8_near_rim_field_20260928.json"),
)
args = parser.parse_args()
started = time.perf_counter()
path = args.saved.resolve()
saved_bytes = path.read_bytes()
saved = json.loads(saved_bytes)
assert saved["status"] == "completed" and saved["accepted_steps"] == 2
model, definition, settings, program = build_case(
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
assert len(program.controls) == 2 and program.waypoints[-1] == (0.0, 0.0)
model.apply_boundary_conditions()
pose = np.asarray(saved["final_displacements"], dtype=float)
certificate = saved["contact"]
pressure = np.asarray(certificate["numerical_pressure_pa"], dtype=float)
support = np.asarray(certificate["reference_support_m2"], dtype=float)
assert np.all(support > 0.0) and np.all(pressure >= 0.0)
manager = GeneralS3PatchManager(model, definition, settings)
assert list(manager.law.pressure_mode_ids) == certificate["source_pressure_node_ids"]
base = linearize(manager, pose, pressure*support, tangent=True)
np.testing.assert_allclose(base.state.reference_support, support,
                           rtol=1e-8, atol=1e-13)
np.testing.assert_allclose(base.state.normalized_gap,
                           certificate["normalized_weighted_gap_m"],
                           rtol=0.0, atol=1e-9)
geometry_seconds = time.perf_counter()-started

structural_tangent = _assemble_nonlinear_system(
    model, pose, {}, 5, tangent=True, kinematics="von_karman",
    require_full_coordinates=True,
)[1]
linear_stiffness = assemble_stiffness_matrix(model)[0]
_reduced, _rhs, transform, offset, _fixed, _info = (
    build_constraint_transformation(linear_stiffness, np.zeros_like(pose), model)
)
assert np.linalg.norm(offset) == 0.0
transform = transform.tocsr()
controlled_dofs = tuple(int(model.mesh.dof_manager.get_node_dofs(node)[0])
                        for node in (1, saved["columns"]+2))
controlled_coordinates = []
for dof in controlled_dofs:
    row = transform.getrow(dof)
    assert row.nnz == 1 and row.data[0] == 1.0
    controlled_coordinates.append(int(row.indices[0]))
free_coordinates = np.setdiff1d(np.arange(transform.shape[1]),
                                controlled_coordinates)
physical_transform = transform[:, free_coordinates]
active = np.flatnonzero(pressure > 0.0)
assert len(active) == certificate["active_pressure_dofs"]
full_tangent = sparse.csr_matrix(structural_tangent)+base.tangent
reduced_tangent = (physical_transform.T @ full_tangent
                   @ physical_transform).tocsc()
gradient = np.asarray(base.gap_gradient[active] @ physical_transform)
factor = splu(reduced_tangent)
response = factor.solve(gradient.T)
solve_residual = reduced_tangent @ response-gradient.T
relative_solve_residual = float(np.linalg.norm(solve_residual)
                                /max(np.linalg.norm(gradient.T), 1e-30))
compliance = gradient @ response
symmetry_defect = float(np.linalg.norm(compliance-compliance.T)
                        /max(np.linalg.norm(compliance), 1e-30))
singular = np.linalg.svd(compliance, compute_uv=False)
symmetric_eigen = np.linalg.eigvalsh((compliance+compliance.T)/2)
scaled = np.sqrt(support[active])[:, None]*compliance*np.sqrt(support[active])[None, :]
scaled_singular = np.linalg.svd(scaled, compute_uv=False)
diagonal = np.diag(compliance)
assert np.all(diagonal > 0.0)
unit_diagonal = (compliance/np.sqrt(diagonal)[:, None]
                 /np.sqrt(diagonal)[None, :])
unit_diagonal_eigen = np.linalg.eigvalsh(
    (unit_diagonal+unit_diagonal.T)/2)
record = {
    "status": "development_saved_active_pressure_compliance",
    "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                              text=True).strip(),
    "saved_source_file": str(path),
    "saved_source_sha256": hashlib.sha256(saved_bytes).hexdigest(),
    "saved_runtime_identity": saved["runtime_identity"],
    "python": sys.version.split()[0],
    "platform": platform.platform(),
    "anysolver_module": str(Path(anysolver.__file__).resolve()),
    "active_modes": len(active),
    "supported_modes": len(support),
    "controlled_dofs": controlled_dofs,
    "physical_free_coordinates": int(physical_transform.shape[1]),
    "reduced_tangent_nnz": int(reduced_tangent.nnz),
    "relative_linear_solve_residual": relative_solve_residual,
    "compliance_symmetry_defect": symmetry_defect,
    "minimum_symmetric_eigenvalue_m_per_n": float(symmetric_eigen[0]),
    "maximum_symmetric_eigenvalue_m_per_n": float(symmetric_eigen[-1]),
    "minimum_singular_value_m_per_n": float(singular[-1]),
    "maximum_singular_value_m_per_n": float(singular[0]),
    "unscaled_singular_ratio": float(singular[-1]/singular[0]),
    "support_scaled_singular_ratio": float(scaled_singular[-1]/scaled_singular[0]),
    "minimum_active_support_m2": float(np.min(support[active])),
    "maximum_active_support_m2": float(np.max(support[active])),
    "active_support_ratio": float(np.min(support[active])
                                  /np.max(support[active])),
    "unit_diagonal_minimum_eigenvalue": float(unit_diagonal_eigen[0]),
    "unit_diagonal_maximum_eigenvalue": float(unit_diagonal_eigen[-1]),
    "unit_diagonal_eigen_ratio": float(unit_diagonal_eigen[0]
                                       /unit_diagonal_eigen[-1]),
    "geometry_seconds": geometry_seconds,
    "elapsed_seconds": time.perf_counter()-started,
    "peak_process_working_set_mb": (
        psutil.Process().memory_info().peak_wset / 1.0e6
    ),
}
print(json.dumps(record, indent=2))
