"""Probe: per-iteration Newton behaviour of the failing EP DC step.

Runs the direct EP case to -0.1667 (10 steps, same increment as the 12-step
run), then reproduces the failing step to -0.1833 with a manual Newton loop
using exactly the solver's own pieces (work_conjugate assembly, rotating-map
reduction, augmented control row), printing the residual trajectory.
"""
from __future__ import annotations

import copy
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "tests"))

import numpy as np
from scipy import sparse

from test_nonlinear_beam_shell_slice3_continuation import (  # noqa: E402
    _add_tip_load,
    _build_ep_model,
)
from anysolver import DisplacementControl, solve_static_nonlinear  # noqa: E402
from anysolver.assembly import build_constraint_transformation  # noqa: E402
from anysolver.corotational import build_nonlinear_rotating_mpc_map  # noqa: E402
from anysolver.matrix_assembly import (  # noqa: E402
    assemble_load_vector,
    assemble_stiffness_matrix,
)
from anysolver.nonlinear_static import _assemble_nonlinear_system  # noqa: E402
from anysolver.linalg import MatrixClass, factorize  # noqa: E402


def main() -> None:
    coupling = sys.argv[1] if len(sys.argv) > 1 else "direct"
    tangent_mode = sys.argv[2] if len(sys.argv) > 2 else "work_conjugate"
    model, load, probe, grid = _build_ep_model(coupling)
    _add_tip_load(model, load, grid)
    prefix = solve_static_nonlinear(
        model, load, control="displacement",
        displacement_control=DisplacementControl(
            node_id=probe, dof="uz", target_displacement=-0.1666666666666667
        ),
        kinematics="corotational", num_steps=10, max_iterations=40,
        tolerance=1.0e-8,
    )
    print(json.dumps({
        "stage": "prefix", "coupling": coupling,
        "status": prefix.status, "uz": float(prefix.displacements[
            model.mesh.dof_manager.get_node_dofs(probe)[2]
        ]), "lam": prefix.load_factor,
    }), flush=True)

    # Rebuild a fresh model for the manual step (element storage on the
    # prefix model has served its purpose).
    model, load, probe, grid = _build_ep_model(coupling)
    _add_tip_load(model, load, grid)
    K0, _ = assemble_stiffness_matrix(model)
    F_prop, _ = assemble_load_vector(model, load)
    _, _, T, u0, _, _ = build_constraint_transformation(K0, F_prop, model)
    mpc_map = build_nonlinear_rotating_mpc_map(model, T)
    control = DisplacementControl(
        node_id=probe, dof="uz", target_displacement=-0.1833333333333333
    )
    row_full = control.full_row(model)

    committed = copy.deepcopy(dict(prefix.element_states))
    u_initial = np.asarray(prefix.displacements, dtype=float)
    # Recover the reduced coordinates of the mapped restart state.
    u_lin = mpc_map.to_linear_displacement(u_initial)
    q = np.linalg.lstsq(T.toarray(), (u_lin - u0), rcond=None)[0]
    lam = float(prefix.load_factor)
    target = -0.1833333333333333
    target_scale = max(abs(target - float(row_full @ u_initial)), abs(target), 1e-9)

    def full_u(q_vec):
        return mpc_map.apply_kinematics(np.asarray(T @ q_vec + u0).reshape(-1))

    u = full_u(q)
    print(json.dumps({
        "stage": "restart_check", "uz": float(row_full @ u),
        "recovery_error": float(np.max(np.abs(u - u_initial))),
        "lam": lam,
    }), flush=True)

    for iteration in range(1, 41):
        u = full_u(q)
        F_int, K_T, trial_states = _assemble_nonlinear_system(
            model, u, committed, 5, tangent=True, kinematics="corotational",
            corotational_tangent=tangent_mode,
        )
        residual = mpc_map.reduce_force(u, lam * F_prop - F_int)
        current = float(row_full @ u)
        constraint = target - current
        ref_vec = mpc_map.reduce_force(u, max(abs(lam), 1.0) * F_prop)
        reference = max(float(np.linalg.norm(ref_vec)), 1.0)
        residual_norm = float(np.linalg.norm(residual))
        print(json.dumps({
            "iter": iteration, "residual": residual_norm,
            "criterion": 1.0e-8 * reference, "constraint": abs(constraint),
            "constraint_criterion": 1.0e-8 * target_scale, "lam": lam,
        }), flush=True)
        if residual_norm <= 1.0e-8 * reference and abs(constraint) <= 1.0e-8 * target_scale:
            print(json.dumps({"stage": "converged", "iteration": iteration}),
                  flush=True)
            return
        K_red = mpc_map.reduce_tangent(u, K_T, F_int - lam * F_prop, None)
        F_prop_red = mpc_map.reduce_force(u, F_prop)
        row_jac = np.asarray(row_full @ mpc_map.jacobian(u)).reshape(-1)
        aug = sparse.bmat([
            [K_red, sparse.csr_matrix((-F_prop_red).reshape(-1, 1))],
            [sparse.csr_matrix(row_jac.reshape(1, -1)), sparse.csr_matrix((1, 1))],
        ], format="csr")
        rhs = np.concatenate([residual, np.array([constraint])])
        handle = factorize(aug, MatrixClass.GENERAL,
                           signature="probe.dc.step")
        delta = np.asarray(handle.solve(rhs)).reshape(-1)
        q = q + delta[:-1]
        lam = lam + float(delta[-1])
    print(json.dumps({"stage": "stalled"}), flush=True)


if __name__ == "__main__":
    main()
