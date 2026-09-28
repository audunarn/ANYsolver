"""One static contact-path increment with coupled primal/dual Newton work."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import sparse

from anysolver.control import cancellation_safe_point
from anysolver.linalg import MatrixClass, factorize
from anysolver.nonlinear_static import _assemble_nonlinear_system
from anysolver.nonlinear_static import _discard_nonlinear_state_candidate

from .core import suspend_contact
from .semismooth import complementarity, linearize, reference_nodal_support
from .semismooth_block import prepare_frozen_block_response


@dataclass(frozen=True)
class SemismoothStep:
    completed: bool
    reason: str | None
    q: np.ndarray
    reactions: np.ndarray
    nodal_forces: np.ndarray
    candidate_states: object | None
    contact: object | None
    iterations: int
    residual_norm: float
    constraint_norm: float
    complementarity_norm: float
    candidate_evaluations: int
    backtracks: int
    diagnostics: dict | None = None


def solve_increment(*, model, manager, settings, q, reactions, nodal_forces,
                    committed_states, transform, offset, control_rows,
                    control_reactions, target, reduced_external, num_layers,
                    max_iterations, tolerance, control_scale,
                    path_force_magnitude, cancellation_token, step):
    """Solve one declared path step without committing its material state."""
    q = np.asarray(q, dtype=float).copy()
    mu = np.asarray(reactions, dtype=float).copy()
    z = np.asarray(nodal_forces, dtype=float).copy()
    scale = settings.complementarity_force_scale_n
    support_ref = reference_nodal_support(manager.law)
    c = manager.stiffness*support_ref
    modes = len(z)
    if z.shape != (len(support_ref),):
        raise ValueError("active-set checkpoint has incompatible pressure modes")
    evaluations = 0
    backtracks = 0

    def evaluate(at_q, at_mu, at_z, *, tangent):
        nonlocal evaluations
        cancellation_safe_point(cancellation_token,
                                f"contact_path.step:{step}.semismooth.candidate")
        u = np.asarray(transform @ at_q + offset).reshape(-1)
        with suspend_contact():
            internal, stiffness, material_trial = _assemble_nonlinear_system(
                model, u, committed_states, num_layers, tangent=tangent,
                kinematics="von_karman",
            )
        contact = linearize(manager, u, at_z, tangent=tangent)
        evaluations += 1
        total_internal = np.asarray(internal).reshape(-1) + contact.force
        residual = (reduced_external + control_reactions @ at_mu
                    - np.asarray(transform.T @ total_internal).reshape(-1))
        constraint = target - control_rows @ at_q
        ncp, active, ncp_q, ncp_z = complementarity(
            contact.state, at_z, c, contact.gap_gradient, tangent=tangent,
        )
        value = max(float(np.linalg.norm(residual))/scale,
                    float(np.max(np.abs(constraint)))/control_scale,
                    float(np.sum(np.abs(ncp)))/scale)
        return (u, material_trial, contact, stiffness, residual, constraint,
                ncp, active, ncp_q, ncp_z, value)

    for iteration in range(1, max_iterations+1):
        cancellation_safe_point(cancellation_token,
                                f"contact_path.step:{step}.semismooth.iteration:{iteration}")
        try:
            (u, trial, contact, structural_k, residual, constraint, ncp,
             active, ncp_q, ncp_z, merit) = evaluate(q, mu, z, tangent=True)
        except (ValueError, MemoryError) as exc:
            _discard_nonlinear_state_candidate(committed_states)
            return SemismoothStep(False, f"contact_semismooth_candidate_failed: {exc}",
                                  q, mu, z, None, None, iteration, np.inf,
                                  np.inf, np.inf, evaluations, backtracks)
        residual_norm = float(np.linalg.norm(residual))
        constraint_norm = float(np.max(np.abs(constraint)))
        ncp_force = float(np.sum(np.abs(ncp)))
        ncp_norm = ncp_force/scale
        instantaneous_force_scale = max(
            float(path_force_magnitude),
            float(np.linalg.norm(control_reactions @ mu)),
        )
        instantaneous_ncp_met = (
            ncp_force <= 1.0e-8*instantaneous_force_scale
            if instantaneous_force_scale > 0.0 else ncp_force == 0.0
        )
        unsupported = np.asarray(contact.state.reference_support) <= 0.0
        force_limit = tolerance*max(
            1.0, float(np.linalg.norm(reduced_external
                                      + control_reactions @ mu)),
        )
        if (residual_norm <= force_limit
                and constraint_norm <= tolerance*control_scale
                and ncp_norm <= 1.0e-8
                and instantaneous_ncp_met
                and np.all(z[~unsupported] >= 0.0)
                and np.all(np.abs(z[unsupported])
                           <= 64.0*np.finfo(float).eps*scale)):
            positions = manager._positions(u)
            if manager._gap_lower(positions) >= -manager.gap_tolerance:
                z[unsupported] = 0.0
                return SemismoothStep(True, None, q, mu, z, trial, contact,
                                      iteration, residual_norm, constraint_norm,
                                      ncp_norm, evaluations, backtracks)
        stiffness = structural_k + contact.tangent
        kqq = (transform.T @ stiffness @ transform).tocsr()
        kqz = sparse.csr_matrix(-transform.T @ contact.gap_gradient.T)
        q_size, mu_size = len(q), len(mu)
        block_response = None
        if settings.monolithic_linear_solver == "block_response_dev":
            try:
                block_response = prepare_frozen_block_response(
                    kqq=kqq, control_reactions=control_reactions,
                    control_rows=control_rows, kqz=kqz,
                    gap_q=np.asarray(contact.gap_gradient @ transform),
                    residual=residual, constraint=constraint,
                    signature=f"contact_path:{step}:semismooth:{iteration}:block",
                )
            except Exception as exc:
                _discard_nonlinear_state_candidate(committed_states)
                return SemismoothStep(
                    False, "contact_semismooth_block_response_failed",
                    q, mu, z, None, None, iteration, residual_norm,
                    constraint_norm, ncp_norm, evaluations, backtracks,
                    {"detail": f"{type(exc).__name__}: {exc}"[:200]},
                )
        pivot_active = active.copy()
        seen_sets = set()
        pivot_trace = []
        pivot_limit = min(settings.monolithic_maximum_pivots, modes+2)
        for pivot in range(pivot_limit):
            cancellation_safe_point(cancellation_token,
                                    f"contact_path.step:{step}.semismooth.pivot:{pivot}")
            signature = tuple(np.flatnonzero(pivot_active))
            if signature in seen_sets:
                _discard_nonlinear_state_candidate(committed_states)
                return SemismoothStep(False, "contact_semismooth_pivot_cycle",
                                      q, mu, z, None, None, iteration, residual_norm,
                                      constraint_norm, ncp_norm, evaluations, backtracks,
                                      {"pivot_trace": pivot_trace})
            seen_sets.add(signature)
            try:
                if block_response is None:
                    branch_c = np.where(pivot_active,
                                        c*contact.state.normalized_gap, z)
                    branch_q = np.zeros_like(contact.gap_gradient)
                    branch_q[pivot_active] = (
                        c[pivot_active, None]*contact.gap_gradient[pivot_active]
                    )
                    branch_z = np.ones(modes)
                    branch_z[pivot_active] = 0.0
                    matrix = sparse.bmat((
                        (kqq, sparse.csr_matrix(-control_reactions), kqz),
                        (sparse.csr_matrix(control_rows),
                         sparse.csr_matrix((len(target), len(target))),
                         sparse.csr_matrix((len(target), modes))),
                        (sparse.csr_matrix(branch_q @ transform),
                         sparse.csr_matrix((modes, len(target))),
                         sparse.diags(branch_z, format="csr")),
                    ), format="csr")
                    rhs = np.r_[residual, constraint, -branch_c]
                    delta = np.asarray(factorize(
                        matrix, MatrixClass.GENERAL,
                        signature=f"contact_path:{step}:semismooth:{iteration}:pivot:{pivot}",
                    ).solve(rhs)).reshape(-1)
                else:
                    parts = block_response.direction(
                        pivot_active, z, contact.state.normalized_gap,
                    )
                    delta = np.concatenate(parts)
            except ArithmeticError as exc:
                _discard_nonlinear_state_candidate(committed_states)
                return SemismoothStep(False, "contact_semismooth_block_backward_error",
                                      q, mu, z, None, None, iteration, residual_norm,
                                      constraint_norm, ncp_norm, evaluations, backtracks,
                                      {"pivot_trace": pivot_trace,
                                       "detail": f"{type(exc).__name__}: {exc}"[:200]})
            except Exception as exc:
                _discard_nonlinear_state_candidate(committed_states)
                return SemismoothStep(False, "singular_contact_semismooth_tangent",
                                      q, mu, z, None, None, iteration, residual_norm,
                                      constraint_norm, ncp_norm, evaluations, backtracks,
                                      {"pivot_trace": pivot_trace,
                                       "detail": f"{type(exc).__name__}: {exc}"[:200]})
            if not np.all(np.isfinite(delta)):
                _discard_nonlinear_state_candidate(committed_states)
                return SemismoothStep(False, "nonfinite_contact_semismooth_increment",
                                      q, mu, z, None, None, iteration, residual_norm,
                                      constraint_norm, ncp_norm, evaluations, backtracks,
                                      {"pivot_trace": pivot_trace})
            dq = delta[:q_size]
            dmu = delta[q_size:q_size+mu_size]
            dz = delta[q_size+mu_size:]
            predicted_gap = (contact.state.normalized_gap
                             + contact.gap_gradient @ (transform @ dq))
            predicted_z = z+dz
            predicted_active = (
                (contact.state.reference_support > 0.0)
                & (predicted_z-c*predicted_gap > 0.0)
            )
            pivot_trace.append({"from": list(signature),
                                "to": np.flatnonzero(predicted_active).tolist()})
            if np.array_equal(predicted_active, pivot_active):
                break
            pivot_active = predicted_active
        else:
            _discard_nonlinear_state_candidate(committed_states)
            return SemismoothStep(False, "contact_semismooth_pivot_limit",
                                  q, mu, z, None, None, iteration, residual_norm,
                                  constraint_norm, ncp_norm, evaluations, backtracks,
                                  {"pivot_limit": pivot_limit,
                                   "pivot_trace": pivot_trace})
        proposed_u = np.asarray(transform @ (q+dq) + offset).reshape(-1)
        fraction = min(1.0, manager.admissible_step_fraction(u, proposed_u))
        _discard_nonlinear_state_candidate(committed_states)
        improved = False
        attempts = []
        last_candidate = None
        last_z = None
        for attempt in range(12):
            cancellation_safe_point(cancellation_token,
                                    f"contact_path.step:{step}.semismooth.backtrack:{attempt}")
            if fraction <= 1.0e-12:
                break
            trial_q = q + fraction*dq
            trial_mu = mu + fraction*dmu
            trial_z = z + fraction*dz
            try:
                candidate = evaluate(trial_q, trial_mu, trial_z, tangent=False)
                last_candidate, last_z = candidate, trial_z
                new_merit = candidate[-1]
                candidate_error = None
                candidate_norms = {
                    "equilibrium": float(np.linalg.norm(candidate[4]))/scale,
                    "constraint": float(np.max(np.abs(candidate[5])))/control_scale,
                    "complementarity": float(np.sum(np.abs(candidate[6])))/scale,
                    "active_modes": int(np.count_nonzero(candidate[7])),
                }
            except (ValueError, MemoryError) as exc:
                new_merit = np.inf
                candidate_error = f"{type(exc).__name__}: {exc}"[:200]
                candidate_norms = {}
            attempts.append({
                "fraction": float(fraction), "merit": float(new_merit),
                "error": candidate_error, **candidate_norms,
            })
            _discard_nonlinear_state_candidate(committed_states)
            if np.isfinite(new_merit) and new_merit < merit*(1.0-1.0e-4*fraction):
                q, mu, z = trial_q, trial_mu, trial_z
                improved = True
                break
            backtracks += 1
            fraction *= 0.5
        if not improved:
            # The projected complementarity map is smooth only up to the
            # first active-set event. A narrow rim mode may cross before the
            # geometric half-step grid samples that smooth branch.
            y = z-c*contact.state.normalized_gap
            dy = dz-c*(contact.gap_gradient @ (transform @ dq))
            crossing = active & (dy < 0.0)
            if np.any(crossing):
                event = float(np.min(y[crossing]/(-dy[crossing])))
                event_fraction = min(1.0, 0.5*event)
                if 1.0e-12 < event_fraction < attempts[-1]["fraction"]:
                    event_q = q + event_fraction*dq
                    event_mu = mu + event_fraction*dmu
                    event_z = z + event_fraction*dz
                    try:
                        event_candidate = evaluate(event_q, event_mu, event_z,
                                                   tangent=False)
                        event_merit = float(event_candidate[-1])
                        event_error = None
                    except (ValueError, MemoryError) as exc:
                        event_merit = np.inf
                        event_error = f"{type(exc).__name__}: {exc}"[:200]
                    _discard_nonlinear_state_candidate(committed_states)
                    attempts.append({"fraction": event_fraction,
                                     "merit": event_merit,
                                     "error": event_error,
                                     "kind": "before_active_event"})
                    if (np.isfinite(event_merit)
                            and event_merit < merit*(1.0-1.0e-4*event_fraction)):
                        q, mu, z = event_q, event_mu, event_z
                        improved = True
        if not improved:
            return SemismoothStep(False, "contact_semismooth_backtracking_failed",
                                  q, mu, z, None, None, iteration, residual_norm,
                                  constraint_norm, ncp_norm, evaluations, backtracks,
                                  {"iteration": iteration, "merit": merit,
                                   "equilibrium": residual_norm/scale,
                                   "constraint": constraint_norm/control_scale,
                                   "complementarity": ncp_norm,
                                   "active_modes": int(np.count_nonzero(active)),
                                   "z": z.tolist(),
                                   "c": c.tolist(),
                                   "support": contact.state.reference_support.tolist(),
                                   "gap": contact.state.normalized_gap.tolist(),
                                   "y": (z-c*contact.state.normalized_gap).tolist(),
                                   "ncp": ncp.tolist(),
                                   "last_trial": ({
                                       "z": last_z.tolist(),
                                       "support": last_candidate[2].state.reference_support.tolist(),
                                       "gap": last_candidate[2].state.normalized_gap.tolist(),
                                       "y": (last_z-c*last_candidate[2].state.normalized_gap).tolist(),
                                   } if last_candidate is not None else None),
                                   "direction_q_norm": float(np.linalg.norm(dq)),
                                   "direction_z_min": float(np.min(dz)),
                                   "direction_z_max": float(np.max(dz)),
                                   "attempts": attempts})
    return SemismoothStep(False, "contact_semismooth_iterations_exhausted",
                          q, mu, z, None, None, max_iterations, residual_norm,
                          constraint_norm, ncp_norm, evaluations, backtracks)
