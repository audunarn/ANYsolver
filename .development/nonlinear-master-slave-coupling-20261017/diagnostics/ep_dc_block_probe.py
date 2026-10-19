"""Probe: characterize the obstruction beyond the last accepted EP DC state.

Runs one EP coupling toward -0.20 with the production adaptive subdivision,
then at the terminal accepted state checks:

* consistency of the reduced tangent against central finite differences of
  the reduced residual (defect discriminator), with the same check at the
  healthy -0.10 half state as an in-run control;
* the smallest singular values of the reduced tangent and of the augmented
  control matrix (singularity discriminator);
* the linear Newton prediction for a minimum-size control increment.

Usage: ep_dc_block_probe.py <direct|interp>
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


def reduced_system(model, load, probe):
    K0, _ = assemble_stiffness_matrix(model)
    F_prop, _ = assemble_load_vector(model, load)
    _, _, T, u0, _, _ = build_constraint_transformation(K0, F_prop, model)
    mpc_map = build_nonlinear_rotating_mpc_map(model, T)
    row_full = DisplacementControl(
        node_id=probe, dof="uz", target_displacement=0.0
    ).full_row(model)
    return T, u0, F_prop, mpc_map, row_full


def residual_at(model, mpc_map, T, u0, F_prop, states, q, lam):
    u = mpc_map.apply_kinematics(np.asarray(T @ q + u0, dtype=float).reshape(-1))
    f_int, _, _ = _assemble_nonlinear_system(
        model, u, states, 5, tangent=False, kinematics="corotational",
        corotational_tangent="work_conjugate",
    )
    return mpc_map.reduce_force(u, lam * F_prop - f_int), u, f_int


def tangent_at(model, mpc_map, u, states, f_int, lam, F_prop):
    _, K_T, _ = _assemble_nonlinear_system(
        model, u, states, 5, tangent=True, kinematics="corotational",
        corotational_tangent="work_conjugate",
    )
    return mpc_map.reduce_tangent(u, K_T, f_int - lam * F_prop, None)


def fd_check(model, load, probe, u, states, lam, F_prop, T, u0, mpc_map, tag):
    """Central-FD columns of dR/dq vs the assembled reduced tangent."""
    q = np.linalg.lstsq(T.toarray(), (mpc_map.to_linear_displacement(u) - u0), rcond=None)[0]
    base, _, f_int = residual_at(model, mpc_map, T, u0, F_prop, states, q, lam)
    K_red = np.asarray(
        tangent_at(model, mpc_map, u, states, f_int, lam, F_prop).todense()
    )
    n = q.size
    rng = np.random.default_rng(20261018)
    dirs = [int(np.argmax(np.abs(mpc_map.reduce_force(u, F_prop))))]
    dirs += [int(i) for i in rng.choice(n, size=min(3, n - 1), replace=False)]
    errors = []
    for col in dirs:
        h = 1.0e-7
        qp = q.copy(); qp[col] += h
        qm = q.copy(); qm[col] -= h
        Rp, _, _ = residual_at(model, mpc_map, T, u0, F_prop, states, qp, lam)
        Rm, _, _ = residual_at(model, mpc_map, T, u0, F_prop, states, qm, lam)
        fd = (Rp - Rm) / (2.0 * h)
        scale = max(float(np.linalg.norm(fd)), float(np.linalg.norm(K_red[:, col])), 1e-30)
        errors.append({
            "column": int(col),
            "relative_error": float(np.linalg.norm(fd - K_red[:, col]) / scale),
        })
    sv = np.linalg.svd(K_red, compute_uv=False)
    print(json.dumps({
        "stage": "fd_check", "tag": tag, "lam": float(lam),
        "columns": errors,
        "kred_smallest_singular_values": [float(v) for v in sv[-4:]],
        "kred_largest_singular_value": float(sv[0]),
    }), flush=True)
    return K_red


def main() -> None:
    coupling = sys.argv[1] if len(sys.argv) > 1 else "direct"
    model, load, probe, grid = _build_ep_model(coupling)
    _add_tip_load(model, load, grid)
    result = solve_static_nonlinear(
        model, load, control="displacement",
        displacement_control=DisplacementControl(
            node_id=probe, dof="uz", target_displacement=-0.20
        ),
        kinematics="corotational", num_steps=12, max_iterations=40,
        tolerance=1.0e-8,
    )
    dofs = model.mesh.dof_manager.get_node_dofs(probe)
    print(json.dumps({
        "stage": "terminal", "coupling": coupling,
        "status": result.status,
        "stop_reason": result.info.get("stop_reason"),
        "adaptation": result.info.get("displacement_control_adaptation"),
        "lam": float(result.load_factor),
        "uz": float(np.asarray(result.displacements)[dofs[2]]),
        "accepted_increments": len(result.steps),
        "total_iterations": result.info.get("total_newton_iterations"),
    }), flush=True)

    T, u0, F_prop, mpc_map, row_full = reduced_system(model, load, probe)
    states = copy.deepcopy(dict(result.element_states))
    u = np.asarray(result.displacements, dtype=float)
    lam = float(result.load_factor)

    # In-run control: the same FD check at the healthy -0.10 half state.
    half_model, half_load, half_probe, _grid = _build_ep_model(coupling)
    _add_tip_load(half_model, half_load, _grid)
    half = solve_static_nonlinear(
        half_model, half_load, control="displacement",
        displacement_control=DisplacementControl(
            node_id=half_probe, dof="uz", target_displacement=-0.10
        ),
        kinematics="corotational", num_steps=6, max_iterations=40,
        tolerance=1.0e-8,
    )
    hT, hu0, hF, hmap, _row = reduced_system(half_model, half_load, half_probe)
    hu = np.asarray(half.displacements, dtype=float)
    fd_check(
        half_model, half_load, half_probe, hu,
        copy.deepcopy(dict(half.element_states)), float(half.load_factor),
        hF, hT, hu0, hmap, "half_-0.10",
    )

    # Terminal-state FD check and augmented-matrix singularity measures.
    K_red = fd_check(
        model, load, probe, u, states, lam, F_prop, T, u0, mpc_map, "terminal",
    )
    q = np.linalg.lstsq(T.toarray(), (mpc_map.to_linear_displacement(u) - u0), rcond=None)[0]
    F_prop_red = mpc_map.reduce_force(u, F_prop)
    row_jac = np.asarray(row_full @ mpc_map.jacobian(u), dtype=float).reshape(-1)
    aug = np.zeros((K_red.shape[0] + 1, K_red.shape[0] + 1), dtype=float)
    aug[:K_red.shape[0], :K_red.shape[0]] = K_red
    aug[:K_red.shape[0], -1] = -F_prop_red
    aug[-1, :-1] = row_jac
    sv_aug = np.linalg.svd(aug, compute_uv=False)
    # Linear prediction for a minimum-size control increment.
    rhs = np.concatenate([
        np.zeros(K_red.shape[0]), np.array([6.510416666666667e-05]),
    ])
    delta = np.linalg.lstsq(aug, rhs, rcond=None)[0]
    q_trial = q + delta[:-1]
    lam_trial = lam + float(delta[-1])
    R_trial, u_trial, _f = residual_at(
        model, mpc_map, T, u0, F_prop, states, q_trial, lam_trial
    )
    print(json.dumps({
        "stage": "augmented", "tag": "terminal",
        "aug_smallest_singular_values": [float(v) for v in sv_aug[-4:]],
        "aug_largest_singular_value": float(sv_aug[0]),
        "tiny_step_dq_norm": float(np.linalg.norm(delta[:-1])),
        "tiny_step_dlam": float(delta[-1]),
        "tiny_step_trial_residual": float(np.linalg.norm(R_trial)),
        "tiny_step_trial_uz": float(row_full @ u_trial),
    }), flush=True)


if __name__ == "__main__":
    main()
