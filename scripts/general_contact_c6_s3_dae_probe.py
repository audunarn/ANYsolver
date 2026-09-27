"""Development diagnostic for differentiated S3 algebraic velocity work."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from test_general_contact_transient_plane import _guided_s3_descriptor_impact

from anysolver import ContactTransientSolverControls, TransientConfig, solve_transient_contact
from anysolver.algebraic_dynamics import build_declared_algebraic_basis
from anysolver.assembly import assemble_mass_matrix, build_constraint_transformation
from anysolver.general_contact.core import contact_scope
from anysolver.matrix_assembly import assemble_stiffness_matrix
from anysolver.nonlinear_static import _assemble_nonlinear_system


def run(dt: float) -> dict:
    model, contact, velocity = _guided_s3_descriptor_impact(tilt=.002, span=.1)
    result = solve_transient_contact(
        model, contact, TransientConfig(dt, .012, initial_velocity=velocity),
        solver_controls=ContactTransientSolverControls(
            allow_s3_descriptor_dev=True,
        ),
    )
    K0, _ = assemble_stiffness_matrix(model)
    M, _ = assemble_mass_matrix(model)
    _, _, T, _, independent, _ = build_constraint_transformation(
        K0, np.zeros(M.shape[0]), model,
    )
    Z = build_declared_algebraic_basis(
        model, M, (T.T @ M @ T).tocsr(), T, independent,
        dense_size_limit=512,
    ).reduced_basis
    with contact_scope(model, contact,
                       initial_displacement=np.zeros(M.shape[0])):
        full = result.displacements[-1]
        _, tangent, _ = _assemble_nonlinear_system(
            model, full, {}, 3, tangent=True, kinematics="von_karman",
        )
        independent_step_s = 5.0e-6
        step_direction = independent_step_s*result.velocities[-1]
        _, tangent_plus, _ = _assemble_nonlinear_system(
            model, full+step_direction, {}, 3, tangent=True,
            kinematics="von_karman",
        )
        _, tangent_minus, _ = _assemble_nonlinear_system(
            model, full-step_direction, {}, 3, tangent=True,
            kinematics="von_karman",
        )
    reduced_tangent = (T.T @ tangent @ T).tocsr()
    reduced_velocity = result.velocities[-1, independent]
    tangent_velocity = np.asarray(
        reduced_tangent @ reduced_velocity,
    ).reshape(-1)
    algebraic_rate = np.asarray(Z.T @ tangent_velocity).reshape(-1)
    tangent_acceleration = np.asarray(
        reduced_tangent @ result.accelerations[-1, independent]
    ).reshape(-1)
    hessian_velocity = np.asarray(
        T.T @ ((tangent_plus-tangent_minus) @ result.velocities[-1])
    ).reshape(-1)/(2.0*independent_step_s)
    acceleration_defect = np.asarray(
        Z.T @ (tangent_acceleration+hessian_velocity)
    ).reshape(-1)
    return {
        "dt_s": dt,
        "final_time_s": float(result.times[-1]),
        "final_minimum_gap_m": float(result.contact[-1].minimum_gap),
        "active_pressure_nodes": result.contact[-1].active_pressure_dofs,
        "algebraic_velocity_defect_n_per_s": float(np.linalg.norm(algebraic_rate)),
        "full_force_rate_scale_n_per_s": float(np.linalg.norm(tangent_velocity)),
        "relative_algebraic_velocity_defect": float(
            np.linalg.norm(algebraic_rate)
            / max(1.0e-30, np.linalg.norm(tangent_velocity))
        ),
        "algebraic_acceleration_defect_n_per_s2": float(
            np.linalg.norm(acceleration_defect)
        ),
        "full_acceleration_rate_scale_n_per_s2": float(
            np.linalg.norm(tangent_acceleration+hessian_velocity)
        ),
    }


if __name__ == "__main__":
    for step in (.0002, .0001, .00005):
        print(run(step))
