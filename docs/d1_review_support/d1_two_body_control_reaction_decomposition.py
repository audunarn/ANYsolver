"""Discriminating decomposition of the two-body control-reaction KKT difference.

Replicates d1_two_body_nonlinear_kkt_compare.py's independent solve verbatim
(same arithmetic path, same landing point), then splits the
independent-vs-production control-reaction difference into exact first-order
terms:

    R_ind - R_prod = T1 + T2 + T3
    T1 = I(pose)[c] - I(ppose)[c]              (pose propagation, structural route)
    T2 = C_ind(pose,z) - C_prod(pose,z)        (route difference at common arguments)
    T3 = C_prod(pose,z) - C_prod(ppose,pz)     (solution difference, contact route)

with T3 further split into a z-part at common pose and a pose-part at common
production z. T2 is the production-work/FD-route discriminator; T1+T3 measure
solution-difference propagation into the cancelled reaction. A Newton polish
(up to three extra accepted iterations) tests whether the compare script's
1e-9 merit stopping point leaves the registered reaction under-resolved.
Diagnostic only: no acceptance gate, no tuning, frozen inputs unchanged.
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
oracle_pressure = np.asarray(saved["oracle_pressure_pa"])
active = np.flatnonzero(oracle_pressure > 0.0)
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


def numerical_gap_gradient(pose, directions, sizes, multiplier=1.0):
    global gradient_count
    rows = len(saved["production_pressure_pa"])
    gradient = np.zeros((rows, directions.shape[1]))
    for index, base_step in enumerate(sizes):
        step = multiplier*base_step
        plus = pose+step*directions[:, index]
        minus = pose-step*directions[:, index]
        _support, plus_gap = geometry(plus)
        _support, minus_gap = geometry(minus)
        gradient[:, index] = (plus_gap-minus_gap)/(2*step)
    gradient_count += 1
    return gradient


def independent_gap_gradient(pose):
    return numerical_gap_gradient(pose, columns, steps)


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
production_active = np.flatnonzero(
    np.asarray(saved["production_pressure_pa"]) > 0.0)
assert np.array_equal(active, production_active)
production_pose = np.asarray(saved["production_displacements"])
production_pressure = np.asarray(saved["production_pressure_pa"])
production_support = np.asarray(saved["production_support_m2"])
production_z = production_pressure*production_support

# --- decomposition at the compare script's stopping point -----------------
control_columns = np.eye(ndof)[:, list(control_dofs)]
control_steps = np.full(len(control_dofs), 2e-6)
control_list = list(control_dofs)
external_control = external[control_list]


def control_gradient_at(pose_value, multiplier=1.0):
    return numerical_gap_gradient(pose_value, control_columns, control_steps,
                                  multiplier=multiplier)[active]


with suspend_contact():
    independent_internal = _assemble_nonlinear_system(
        model, pose, {}, 5, tangent=False, kinematics="von_karman",
        require_full_coordinates=True,
    )[0]
    production_internal = _assemble_nonlinear_system(
        model, production_pose, {}, 5, tangent=False,
        kinematics="von_karman", require_full_coordinates=True,
    )[0]
manager = GeneralS3PatchManager(model, definition, _settings)


def production_contact_at(pose_value, weights):
    contact = linearize(manager, pose_value, weights, tangent=False)
    return (np.asarray(contact.force[control_list]),
            np.asarray(contact.gap_gradient[:, control_list])[active])


z_full = np.zeros(len(saved["production_pressure_pa"]))
z_full[active] = z
gradient_nominal = control_gradient_at(pose)
gradient_half = control_gradient_at(pose, multiplier=0.5)
gradient_double = control_gradient_at(pose, multiplier=2.0)
independent_control_reaction = (
    independent_internal[control_list]-external_control
    -gradient_nominal.T @ z)
independent_control_reaction_half = (
    independent_internal[control_list]-external_control
    -gradient_half.T @ z)
independent_control_reaction_double = (
    independent_internal[control_list]-external_control
    -gradient_double.T @ z)
contact_pose_z = production_contact_at(pose, z_full)
contact_pose_pz = production_contact_at(pose, production_z)
contact_ppose_z = production_contact_at(production_pose, z_full)
contact_ppose_pz = production_contact_at(production_pose, production_z)
production_control_reaction = (
    production_internal[control_list]-external_control+contact_ppose_pz[0])
reaction_difference = independent_control_reaction-production_control_reaction
structural_pose_term = (independent_internal[control_list]
                        -production_internal[control_list])
route_term = -gradient_nominal.T @ z-contact_pose_z[0]
solution_contact_term = contact_pose_z[0]-contact_ppose_pz[0]
solution_z_term = contact_pose_z[0]-contact_pose_pz[0]
solution_pose_term = contact_pose_pz[0]-contact_ppose_pz[0]
reaction_scale = max(float(np.linalg.norm(production_control_reaction)), 1e-10)

# --- Newton polish: is the registered reaction under-resolved at merit 1e-9?
polish_trace = []
polish_q, polish_z = q, z
polish_pose, polish_gap = pose, gap
polish_gradient, polish_residual, polish_tangent, polish_merit = (
    gradient, residual, tangent, merit)
for extra in range(3):
    size = len(q)
    active_count = len(active)
    matrix = np.block([
        [polish_tangent, -polish_gradient.T],
        [polish_gradient, np.zeros((active_count, active_count))],
    ])
    correction = np.linalg.solve(
        matrix, -np.r_[polish_residual, polish_gap[active]])
    accepted = False
    for backtrack in range(8):
        fraction = 0.5**backtrack
        candidate_q = polish_q+fraction*correction[:size]
        candidate_z = polish_z+fraction*correction[size:]
        if np.min(candidate_z) <= 0.0:
            continue
        candidate = state(candidate_q, candidate_z)
        if candidate[-1] < polish_merit*(1-1e-4*fraction):
            polish_q, polish_z = candidate_q, candidate_z
            (polish_pose, _polish_support, polish_gap, polish_gradient,
             polish_residual, polish_tangent, polish_merit) = candidate
            accepted = True
            break
    if not accepted:
        break
    with suspend_contact():
        polish_internal = _assemble_nonlinear_system(
            model, polish_pose, {}, 5, tangent=False, kinematics="von_karman",
            require_full_coordinates=True,
        )[0]
    polish_gradient_control = control_gradient_at(polish_pose)
    polish_reaction = (polish_internal[control_list]-external_control
                       -polish_gradient_control.T @ polish_z)
    polish_trace.append({
        "polish_iteration": extra,
        "scaled_merit": polish_merit,
        "force_residual_norm_n": float(np.linalg.norm(polish_residual)),
        "independent_control_reaction_n": polish_reaction.tolist(),
        "control_reaction_relative_l2_difference": float(
            np.linalg.norm(polish_reaction-production_control_reaction)
            /reaction_scale),
        "relative_z_difference": float(
            np.linalg.norm(polish_z-production_z[active])
            /np.linalg.norm(production_z)),
        "maximum_pose_difference_m": float(
            np.max(abs(polish_pose-production_pose))),
    })
    if polish_merit <= 1e-16:
        break

try:
    from threadpoolctl import threadpool_info
    pools = threadpool_info()
except Exception as error:  # pragma: no cover - metadata only
    pools = [{"error": repr(error)}]

record = {
    "status": "development_control_reaction_decomposition",
    "source_commit": subprocess.check_output(
        ("git", "rev-parse", "HEAD"), text=True).strip(),
    "saved_source_sha256": hashlib.sha256(saved_bytes).hexdigest(),
    "python": sys.version.split()[0],
    "platform": platform.platform(),
    "anysolver_module": str(Path(anysolver.__file__).resolve()),
    "threadpool_info": pools,
    "geometry_evaluations": evaluation_count,
    "gradient_evaluations": gradient_count,
    "elapsed_seconds": time.perf_counter()-started,
    "solve_trace": trace,
    "independent_control_reaction_n": independent_control_reaction.tolist(),
    "independent_control_reaction_half_step_n":
        independent_control_reaction_half.tolist(),
    "independent_control_reaction_double_step_n":
        independent_control_reaction_double.tolist(),
    "production_recovered_control_reaction_n":
        production_control_reaction.tolist(),
    "reaction_difference_n": reaction_difference.tolist(),
    "control_reaction_relative_l2_difference": float(
        np.linalg.norm(reaction_difference)/reaction_scale),
    "decomposition": {
        "structural_pose_term_n": structural_pose_term.tolist(),
        "route_term_n": route_term.tolist(),
        "solution_contact_term_n": solution_contact_term.tolist(),
        "solution_z_term_n": solution_z_term.tolist(),
        "solution_pose_term_n": solution_pose_term.tolist(),
        "identity_residual_n": (reaction_difference-structural_pose_term
                                -route_term-solution_contact_term).tolist(),
    },
    "fd_reaction_step_sensitivity": {
        "half_vs_nominal_n": (independent_control_reaction_half
                              -independent_control_reaction).tolist(),
        "double_vs_nominal_n": (independent_control_reaction_double
                                -independent_control_reaction).tolist(),
    },
    "control_gradient_independent": gradient_nominal.tolist(),
    "control_gradient_independent_half": gradient_half.tolist(),
    "control_gradient_production_at_pose": contact_pose_z[1].tolist(),
    "control_gradient_production_at_production_pose":
        contact_ppose_pz[1].tolist(),
    "production_contact_force_control_n": {
        "pose_independent_z": contact_pose_z[0].tolist(),
        "pose_production_z": contact_pose_pz[0].tolist(),
        "production_pose_independent_z": contact_ppose_z[0].tolist(),
        "production_pose_production_z": contact_ppose_pz[0].tolist(),
    },
    "independent_z_n": z.tolist(),
    "production_z_n": production_z[active].tolist(),
    "relative_z_difference": float(
        np.linalg.norm(z-production_z[active])
        /np.linalg.norm(production_z)),
    "maximum_pose_difference_m": float(
        np.max(abs(pose-production_pose))),
    "external_control_n": external_control.tolist(),
    "independent_internal_control_n":
        independent_internal[control_list].tolist(),
    "production_internal_control_n":
        production_internal[control_list].tolist(),
    "polish_trace": polish_trace,
}
print(json.dumps(record, indent=2))
