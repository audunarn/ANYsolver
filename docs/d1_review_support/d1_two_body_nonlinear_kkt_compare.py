"""Bounded nonlinear coupled Q1/S3 comparison with independent contact work.

The admitted shell structural residual/tangent are shared with production.
Contact gap and its work map come only from independent current-skin
quadrature and numerical derivatives. This is same-model code verification,
not an independent continuum or spatial-accuracy reference.
"""

import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from scipy import sparse

import anysolver
from anysolver.assembly import build_constraint_transformation
from anysolver.general_contact.core import suspend_contact
from anysolver.general_contact.s3_patch_static import GeneralS3PatchManager
from anysolver.general_contact.semismooth import linearize
from anysolver.matrix_assembly import assemble_stiffness_matrix
from anysolver.nonlinear_static import _assemble_nonlinear_system
from d1_two_body_current_skin_quadrature import integrate_current_skin
from scripts.general_contact_d1_free_target_press_probe import build_free_target_case


started = time.perf_counter()
path = Path(__file__).with_name("d1_two_body_reference_compare_full_20260928.json")
saved_bytes = path.read_bytes()
saved = json.loads(saved_bytes)
assert saved["production_status"] == "completed"
assert saved["production_accepted_steps"] == 4
model, definition, _settings, program = build_free_target_case(
    4, steps_per_segment=2, four_phase=True,
    enforcement_solver="monolithic_active_set",
)
model.apply_boundary_conditions()
ndof = model.mesh.dof_manager.total_dofs
stiffness, _info = assemble_stiffness_matrix(model)
_reduced, _rhs, transform, offset, _fixed, _constraint_info = (
    build_constraint_transformation(stiffness, np.zeros(ndof), model)
)
assert np.linalg.norm(offset) == 0.0
transform = transform.tocsr()
control_nodes = (1, 6)
control_dofs = tuple(int(model.mesh.dof_manager.get_node_dofs(node)[0])
                     for node in control_nodes)
control_values = np.asarray(program.target_at(4), dtype=float)
assert control_values.shape == (2,)
controlled_coordinates = []
for dof in control_dofs:
    row = transform.getrow(dof)
    assert row.nnz == 1 and row.data[0] == 1.0
    controlled_coordinates.append(int(row.indices[0]))
free_coordinates = np.setdiff1d(np.arange(transform.shape[1]),
                                controlled_coordinates)
physical_transform = transform[:, free_coordinates].tocsr()
columns = np.asarray(physical_transform.toarray())
assert np.all(np.sum(abs(columns) > 0.0, axis=0) == 1)
fixed_pose = np.zeros(ndof)
fixed_pose[list(control_dofs)] = control_values
external = np.zeros(ndof)
for force, value in zip(program.nodal_forces,
                        program.force_values_at(4), strict=True):
    assert force.dof == "uz"
    external[model.mesh.dof_manager.get_node_dofs(force.node_id)[2]] += value
active = np.flatnonzero(np.asarray(saved["production_pressure_pa"]) > 0.0)
oracle_pressure = np.asarray(saved["oracle_pressure_pa"])
assert np.array_equal(active, np.flatnonzero(oracle_pressure > 0.0))
oracle_pose = np.asarray(saved["oracle_displacements"])
q = np.asarray(physical_transform.T @ (oracle_pose-fixed_pose)).reshape(-1)
assert np.max(abs(fixed_pose+columns @ q-oracle_pose)) < 1e-12
z = (oracle_pressure*np.asarray(saved["oracle_support_m2"]))[active].copy()
assert np.all(z > 0.0)
steps = np.array([2e-5 if np.flatnonzero(columns[:, index])[0] % 6 >= 3
                  else 2e-6 for index in range(columns.shape[1])])
evaluation_count = 0
gradient_count = 0
topology_signature = None


def geometry(pose):
    global evaluation_count, topology_signature
    if time.perf_counter()-started > 165.0:
        raise TimeoutError("independent nonlinear KKT development budget exhausted")
    support, weighted, _area, _points, signature = (
        integrate_current_skin(model, definition, pose))
    evaluation_count += 1
    if topology_signature is None:
        topology_signature = signature
    elif signature != topology_signature:
        raise RuntimeError("independent current-skin clipping topology changed")
    return support, weighted/support


def independent_gap_gradient(pose):
    global gradient_count
    rows = len(saved["production_pressure_pa"])
    gradient = np.zeros((rows, columns.shape[1]))
    for index, step in enumerate(steps):
        plus = pose+step*columns[:, index]
        minus = pose-step*columns[:, index]
        _support, plus_gap = geometry(plus)
        _support, minus_gap = geometry(minus)
        gradient[:, index] = (plus_gap-minus_gap)/(2*step)
    gradient_count += 1
    return gradient


def state(coordinates, nodal_forces):
    pose = fixed_pose+columns @ coordinates
    support, gap = geometry(pose)
    gradient = independent_gap_gradient(pose)[active]
    with suspend_contact():
        internal, tangent, _states = _assemble_nonlinear_system(
            model, pose, {}, 5, tangent=True, kinematics="von_karman",
            require_full_coordinates=True,
        )
    structural = np.asarray(physical_transform.T @ (internal-external)).reshape(-1)
    residual = structural-gradient.T @ nodal_forces
    scaled_merit = float(np.hypot(np.linalg.norm(residual)/0.3,
                                  np.linalg.norm(gap[active])/5e-5))
    reduced_tangent = (physical_transform.T @ sparse.csr_matrix(tangent)
                       @ physical_transform).toarray()
    return pose, support, gap, gradient, residual, reduced_tangent, scaled_merit


trace = []
for iteration in range(8):
    pose, support, gap, gradient, residual, tangent, merit = state(q, z)
    trace.append({"iteration": iteration, "scaled_merit": merit,
                  "force_residual_norm_n": float(np.linalg.norm(residual)),
                  "active_gap_norm_m": float(np.linalg.norm(gap[active])),
                  "minimum_active_force_n": float(np.min(z))})
    if merit <= 1e-9:
        break
    size = len(q)
    active_count = len(active)
    matrix = np.block([
        [tangent, -gradient.T],
        [gradient, np.zeros((active_count, active_count))],
    ])
    correction = np.linalg.solve(matrix, -np.r_[residual, gap[active]])
    accepted = False
    for backtrack in range(8):
        fraction = 0.5**backtrack
        candidate_q = q+fraction*correction[:size]
        candidate_z = z+fraction*correction[size:]
        if np.min(candidate_z) <= 0.0:
            continue
        candidate_merit = state(candidate_q, candidate_z)[-1]
        if candidate_merit < merit*(1-1e-4*fraction):
            q, z = candidate_q, candidate_z
            accepted = True
            break
    if not accepted:
        raise RuntimeError("independent nonlinear KKT backtracking failed")
else:
    raise RuntimeError("independent nonlinear KKT iteration budget exhausted")

assert np.min(gap) >= -1e-9
pressure = np.zeros(len(support))
pressure[active] = z/support[active]
production_pose = np.asarray(saved["production_displacements"])
production_pressure = np.asarray(saved["production_pressure_pa"])
production_support = np.asarray(saved["production_support_m2"])
production_z = production_pressure*production_support
control_gradient = np.zeros((len(active), len(control_dofs)))
for column, dof in enumerate(control_dofs):
    step = 2e-6
    perturbation = np.zeros(ndof)
    perturbation[dof] = step
    _support, plus_gap = geometry(pose+perturbation)
    _support, minus_gap = geometry(pose-perturbation)
    control_gradient[:, column] = (
        plus_gap[active]-minus_gap[active])/(2*step)
with suspend_contact():
    independent_internal = _assemble_nonlinear_system(
        model, pose, {}, 5, tangent=False, kinematics="von_karman",
        require_full_coordinates=True,
    )[0]
    production_internal = _assemble_nonlinear_system(
        model, production_pose, {}, 5, tangent=False,
        kinematics="von_karman", require_full_coordinates=True,
    )[0]
independent_control_reaction = (
    independent_internal[list(control_dofs)]-external[list(control_dofs)]
    -control_gradient.T @ z)
manager = GeneralS3PatchManager(model, definition, _settings)
production_contact = linearize(
    manager, production_pose, production_z, tangent=False)
production_control_reaction = (
    production_internal[list(control_dofs)]-external[list(control_dofs)]
    +production_contact.force[list(control_dofs)])
reaction_scale = max(float(np.linalg.norm(production_control_reaction)), 1e-10)
record = {
    "status": "development_independent_contact_nonlinear_kkt",
    "source_commit": subprocess.check_output(("git", "rev-parse", "HEAD"),
                                              text=True).strip(),
    "command": "python docs/d1_review_support/d1_two_body_nonlinear_kkt_compare.py",
    "saved_source_sha256": hashlib.sha256(saved_bytes).hexdigest(),
    "current_skin_oracle_source_sha256": hashlib.sha256(Path(
        "docs/d1_review_support/d1_two_body_current_skin_quadrature.py"
    ).read_bytes()).hexdigest(),
    "python": sys.version.split()[0],
    "platform": platform.platform(),
    "anysolver_module": str(Path(anysolver.__file__).resolve()),
    "active_pressure_modes": active.tolist(),
    "free_structural_coordinates": len(q),
    "geometry_evaluations": evaluation_count,
    "gradient_evaluations": gradient_count,
    "elapsed_seconds": time.perf_counter()-started,
    "trace": trace,
    "final_scaled_merit": merit,
    "minimum_inactive_gap_m": float(np.min(np.delete(gap, active))),
    "relative_pressure_l2_difference": float(
        np.linalg.norm(pressure-production_pressure)
        /np.linalg.norm(production_pressure)),
    "relative_nodal_force_l2_difference": float(
        np.linalg.norm(np.bincount(active, weights=z,
                                   minlength=len(support))-production_z)
        /np.linalg.norm(production_z)),
    "maximum_displacement_difference_m_or_rad": float(
        np.max(abs(pose-production_pose))),
    "relative_displacement_l2_difference": float(
        np.linalg.norm(pose-production_pose)/np.linalg.norm(production_pose)),
    "integrated_normal_force_n": float(np.sum(z)),
    "production_integrated_normal_force_n": float(np.sum(production_z)),
    "relative_integrated_force_difference": float(
        abs(np.sum(z)-np.sum(production_z))/abs(np.sum(production_z))),
    "independent_control_reaction_n": independent_control_reaction.tolist(),
    "production_recovered_control_reaction_n": (
        production_control_reaction.tolist()),
    "control_reaction_relative_l2_difference": float(
        np.linalg.norm(independent_control_reaction
                       -production_control_reaction)/reaction_scale),
}
print(json.dumps(record, indent=2))
