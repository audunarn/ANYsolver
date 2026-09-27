"""A narrowly admitted nonlinear Newmark contact development profile.

The coupled residual is evaluated by the ordinary nonlinear structural
assembler inside one contact scope.  This first dynamic profile deliberately
admits only elastic planar Q4 shells, fixed rigid planes and positive definite
reduced mass.  It does not qualify the broader C6 impact capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
from anymaterial.isotropic import IsotropicMaterial

from anysolver.assembly import assemble_mass_matrix, build_constraint_transformation
from anysolver.dynamics import TransientConfig
from anysolver.e4_pl_element import QualifiedE4PLShellElement
from anysolver.matrix_assembly import assemble_stiffness_matrix
from anysolver.nonlinear_state import commit_state_candidate, discard_active_state_candidate
from anysolver.nonlinear_restart import (
    analysis_configuration_fingerprint, model_configuration_fingerprint,
)
from anysolver.nonlinear_static import _assemble_nonlinear_system

from .core import (
    ContactDefinition,
    ContactResults,
    ContactSolverSettings,
    _PlanarQ4PlaneManager,
    contact_scope,
    validate_general_contact,
)


_PROFILE = "PLANAR_Q4_FIXED_PLANE_NEWMARK_PENALTY_DEV_V1"
_RESTART_SCHEMA = "ANYSOLVER_Q4_PLANE_TRANSIENT_CONTACT_DEV_CHECKPOINT_V1"


@dataclass(frozen=True)
class ContactTransientSolverControls:
    """Nonlinear iteration limits for the developing contact driver."""

    maximum_newton_iterations: int = 20
    maximum_cutbacks: int = 8
    minimum_dt: float = 1.0e-8
    equilibrium_tolerance: float = 1.0e-8

    def __post_init__(self) -> None:
        if type(self.maximum_newton_iterations) is not int or self.maximum_newton_iterations < 1:
            raise ValueError("maximum_newton_iterations must be a positive integer")
        if type(self.maximum_cutbacks) is not int or self.maximum_cutbacks < 0:
            raise ValueError("maximum_cutbacks must be a nonnegative integer")
        if not np.isfinite(self.minimum_dt) or self.minimum_dt <= 0.0:
            raise ValueError("minimum_dt must be finite and positive")
        if not np.isfinite(self.equilibrium_tolerance) or self.equilibrium_tolerance <= 0.0:
            raise ValueError("equilibrium_tolerance must be finite and positive")


@dataclass(frozen=True)
class TransientContactSettings:
    """Compatibility adapter for the original fixed-plane development call."""

    dt: float
    t_end: float
    initial_velocity: np.ndarray
    maximum_newton_iterations: int = 20
    maximum_cutbacks: int = 8
    minimum_dt: float = 1.0e-8
    equilibrium_tolerance: float = 1.0e-8

    def __post_init__(self) -> None:
        if not np.isfinite(self.dt) or self.dt <= 0.0:
            raise ValueError("dt must be finite and positive")
        if not np.isfinite(self.t_end) or self.t_end < 0.0:
            raise ValueError("t_end must be finite and nonnegative")
        ContactTransientSolverControls(
            self.maximum_newton_iterations, self.maximum_cutbacks,
            self.minimum_dt, self.equilibrium_tolerance,
        )
        velocity = np.array(self.initial_velocity, dtype=float, copy=True).reshape(-1)
        if not np.all(np.isfinite(velocity)):
            raise ValueError("initial_velocity must be finite")
        velocity.setflags(write=False)
        object.__setattr__(self, "initial_velocity", velocity)


def _resolve_transient_inputs(transient, solver_controls):
    if type(transient) is TransientContactSettings:
        if solver_controls is not None:
            raise ValueError("legacy transient settings already contain solver controls")
        controls = ContactTransientSolverControls(
            transient.maximum_newton_iterations, transient.maximum_cutbacks,
            transient.minimum_dt, transient.equilibrium_tolerance,
        )
        transient = TransientConfig(
            dt=transient.dt, t_end=transient.t_end,
            initial_velocity=transient.initial_velocity,
        )
    elif type(transient) is TransientConfig:
        controls = (ContactTransientSolverControls() if solver_controls is None
                    else solver_controls)
        if type(controls) is not ContactTransientSolverControls:
            raise TypeError("ContactTransientSolverControls required")
    else:
        raise TypeError("TransientConfig required")
    if (not np.isfinite(transient.dt) or not np.isfinite(transient.t_end)
            or transient.beta != 0.25 or transient.gamma != 0.5
            or transient.hht_alpha != 0.0
            or transient.rayleigh_alpha != 0.0
            or transient.rayleigh_beta != 0.0):
        raise ValueError("fixed-plane contact admits only undamped average-acceleration Newmark")
    if (transient.output_nodes is not None or transient.output_elements is not None
            or transient.include_stress_history or transient.recovery is not None
            or transient.resource_config is not None):
        raise ValueError("selected recovery and resource options are not admitted in this contact profile")
    if type(transient.save_every) is not int or transient.save_every < 1:
        raise ValueError("save_every must be a positive integer")
    return transient, controls


@dataclass(frozen=True)
class TransientContactResults:
    """Accepted dynamic states; the profile remains developmental."""

    profile: str
    times: np.ndarray
    displacements: np.ndarray
    velocities: np.ndarray
    accelerations: np.ndarray
    contact: tuple[ContactResults, ...]
    swept_minimum_gaps: np.ndarray
    equilibrium_residuals: np.ndarray
    cutbacks: int
    newton_iterations: tuple[int, ...]
    restart_checkpoint: dict | None = None


def _restart_analysis_contract(transient, controls, manager) -> dict:
    # The requested end time is a continuation target, not a definition of
    # the already accepted state. All other integration inputs are bound.
    return {
        "profile": _PROFILE,
        "dt": float(transient.dt),
        "beta": float(transient.beta),
        "gamma": float(transient.gamma),
        "save_every": int(transient.save_every),
        "initial_displacement": (
            None if transient.initial_displacement is None
            else np.asarray(transient.initial_displacement).tolist()
        ),
        "initial_velocity": np.asarray(transient.initial_velocity).tolist(),
        "controls": {
            "maximum_newton_iterations": controls.maximum_newton_iterations,
            "maximum_cutbacks": controls.maximum_cutbacks,
            "minimum_dt": controls.minimum_dt,
            "equilibrium_tolerance": controls.equilibrium_tolerance,
        },
        "contact": manager.restart_contract(),
    }


def _new_restart_checkpoint(model_fingerprint, analysis_fingerprint,
                            current_time, q, velocity, acceleration,
                            accepted_steps) -> dict:
    payload = {
        "schema": _RESTART_SCHEMA,
        "version": 1,
        "model_fingerprint": model_fingerprint,
        "analysis_fingerprint": analysis_fingerprint,
        "state": {
            "time": float(current_time),
            "q": np.asarray(q).tolist(),
            "velocity": np.asarray(velocity).tolist(),
            "acceleration": np.asarray(acceleration).tolist(),
            "accepted_steps": int(accepted_steps),
        },
    }
    payload["checkpoint_sha256"] = analysis_configuration_fingerprint(payload)
    return payload


def _read_restart_checkpoint(value, model_fingerprint, analysis_fingerprint,
                             reduced_size, t_end):
    if not isinstance(value, Mapping) or set(value) != {
        "schema", "version", "model_fingerprint", "analysis_fingerprint",
        "state", "checkpoint_sha256",
    }:
        raise ValueError("transient contact checkpoint schema is incompatible")
    payload = dict(value)
    signature = payload.pop("checkpoint_sha256")
    if (type(signature) is not str
            or signature != analysis_configuration_fingerprint(payload)):
        raise ValueError("transient contact checkpoint integrity mismatch")
    if payload["schema"] != _RESTART_SCHEMA or payload["version"] != 1:
        raise ValueError("transient contact checkpoint version is incompatible")
    if payload["model_fingerprint"] != model_fingerprint:
        raise ValueError("transient contact checkpoint model is incompatible")
    if payload["analysis_fingerprint"] != analysis_fingerprint:
        raise ValueError("transient contact checkpoint analysis is incompatible")
    state = payload["state"]
    if not isinstance(state, Mapping) or set(state) != {
        "time", "q", "velocity", "acceleration", "accepted_steps",
    }:
        raise ValueError("transient contact checkpoint state is malformed")
    time = float(state["time"])
    steps = state["accepted_steps"]
    if (not np.isfinite(time) or time <= 0.0 or time >= t_end
            or type(steps) is not int or steps < 1):
        raise ValueError("transient contact checkpoint time or step is invalid")
    arrays = []
    for name in ("q", "velocity", "acceleration"):
        array = np.asarray(state[name], dtype=float)
        if array.shape != (reduced_size,) or not np.all(np.isfinite(array)):
            raise ValueError(f"transient contact checkpoint {name} is invalid")
        arrays.append(array.copy())
    return time, steps, *arrays


def _minimum_hermite_gap(
    manager: _PlanarQ4PlaneManager,
    start: np.ndarray,
    end: np.ndarray,
    start_velocity: np.ndarray,
    end_velocity: np.ndarray,
    dt: float,
) -> float:
    """Exact corner minimum on the declared cubic step path.

    Q4 skin gap against a fixed plane is bilinear over each face and cubic
    along the Hermite path defined by Newmark endpoint positions/velocities.
    Its face minimum is attained at a corner for each path parameter.
    """

    minimum = float("inf")
    for reference, dofs, _shape, skin_offset, gradient in manager.patches:
        base = (reference + skin_offset - manager.point) @ manager.normal
        g0 = base + start[dofs] @ gradient
        g1 = base + end[dofs] @ gradient
        dg0 = dt * (start_velocity[dofs] @ gradient)
        dg1 = dt * (end_velocity[dofs] @ gradient)
        a = 2.0 * g0 - 2.0 * g1 + dg0 + dg1
        b = -3.0 * g0 + 3.0 * g1 - 2.0 * dg0 - dg1
        c = dg0
        for i in range(len(g0)):
            values = [float(g0[i]), float(g1[i])]
            roots = np.roots([3.0 * a[i], 2.0 * b[i], c[i]])
            for root in roots:
                if abs(root.imag) <= 1.0e-12 and 0.0 < root.real < 1.0:
                    s = float(root.real)
                    values.append(float(((a[i] * s + b[i]) * s + c[i]) * s + g0[i]))
            minimum = min(minimum, *values)
    return minimum


def _admit(model, definition: ContactDefinition, settings: ContactSolverSettings) -> None:
    report = validate_general_contact(model, definition, settings)
    if not report.valid:
        raise ValueError("unsupported transient contact: " + "; ".join(report.issues))
    if (settings.pair_motion != "guided" or settings.warped_q4_plane
            or len(definition.surfaces) != 1 or len(definition.rigid_bodies) != 1
            or len(definition.interactions) != 1
            or definition.rigid_bodies[0].kind != "plane"
            or definition.rigid_bodies[0].path_translation is not None
            or definition.interactions[0].normal_law != "penalty"):
        raise ValueError("transient development profile requires one shell surface and one fixed penalty plane")
    surface = definition.surfaces[0]
    if (set(surface.element_ids) != set(model.mesh.elements)
            or any(type(element) is not QualifiedE4PLShellElement
                   for element in model.mesh.elements.values())):
        raise ValueError("transient development profile requires only qualified planar Q4 elements")
    for element in model.mesh.elements.values():
        material = model.get_material(element.material_name)
        if (type(material) is not IsotropicMaterial
                or float(material.yield_stress) != 0.0
                or material.hardening_curve is not None):
            raise ValueError("transient development profile admits only isotropic elastic material")


def solve_transient_contact(
    model,
    definition: ContactDefinition,
    transient: TransientConfig | TransientContactSettings,
    *,
    contact_settings: ContactSolverSettings | None = None,
    solver_controls: ContactTransientSolverControls | None = None,
    restart_checkpoint: Mapping | None = None,
    emit_restart_checkpoint: bool = False,
) -> TransientContactResults:
    """Solve elastic Q4 impact against a fixed plane with implicit Newmark.

    Every Newton evaluation starts from the last committed material state.
    A rejected step leaves both the displacement and material state at the
    last accepted time.  The affine fixed-plane gap is checked independently
    at every accepted endpoint and across the accepted displacement segment.
    """

    transient, controls = _resolve_transient_inputs(transient, solver_controls)
    if (restart_checkpoint is not None or emit_restart_checkpoint) and transient.save_every != 1:
        raise ValueError("transient contact development restart requires save_every=1")
    if emit_restart_checkpoint and transient.t_end <= 0.0:
        raise ValueError("transient contact checkpoint needs one accepted time step")
    settings = ContactSolverSettings() if contact_settings is None else contact_settings
    _admit(model, definition, settings)
    model.apply_boundary_conditions()
    size = model.mesh.dof_manager.total_dofs
    if transient.initial_velocity is None:
        raise ValueError("initial_velocity is required for transient contact")
    initial_velocity = np.asarray(transient.initial_velocity, dtype=float)
    if initial_velocity.shape != (size,) or not np.all(np.isfinite(initial_velocity)):
        raise ValueError(f"initial_velocity must have {size} structural components")
    initial_displacement = (
        np.zeros(size, dtype=float) if transient.initial_displacement is None
        else np.asarray(transient.initial_displacement, dtype=float)
    )
    if (initial_displacement.shape != (size,)
            or not np.all(np.isfinite(initial_displacement))):
        raise ValueError(f"initial_displacement must have {size} structural components")
    K0, _ = assemble_stiffness_matrix(model)
    M, _ = assemble_mass_matrix(model)
    _, _, T, u0, independent_dofs, _ = build_constraint_transformation(
        K0, np.zeros(size, dtype=float), model,
    )
    if np.linalg.norm(u0, ord=np.inf) > 1.0e-13:
        raise ValueError("transient development profile requires zero prescribed displacements")
    if not len(independent_dofs):
        raise ValueError("transient contact requires at least one free coordinate")
    Mred = (T.T @ M @ T).tocsr()
    # Reject massless algebraic coordinates rather than assigning fictitious
    # inertia.  The descriptor shell adapter belongs to a later C6 slice.
    if Mred.shape[0] > 512:
        raise ValueError("transient development profile admits at most 512 free coordinates")
    try:
        np.linalg.cholesky(Mred.toarray())
    except np.linalg.LinAlgError as exc:
        raise ValueError("reduced mass is not positive definite; algebraic dynamics are not admitted") from exc
    q = np.asarray(initial_displacement[independent_dofs], dtype=float).copy()
    full_initial = np.asarray(T @ q).reshape(-1)
    if not np.allclose(full_initial, initial_displacement,
                       atol=1.0e-12, rtol=1.0e-12):
        raise ValueError("initial_displacement does not satisfy structural constraints")
    vfull = initial_velocity
    vred = np.asarray(vfull[independent_dofs], dtype=float)
    if not np.allclose(np.asarray(T @ vred).reshape(-1), vfull,
                       atol=1.0e-12, rtol=1.0e-12):
        raise ValueError("initial_velocity does not satisfy structural constraints")
    committed_states = {}
    # The manager's fresh-start guard checks the original configured pose.
    # The resumed pose is validated separately against its accepted gap budget.
    with contact_scope(model, definition, settings,
                       initial_displacement=full_initial) as manager:
        if type(manager) is not _PlanarQ4PlaneManager:
            raise ValueError("transient development profile selected an unsupported contact owner")

        if restart_checkpoint is not None or emit_restart_checkpoint:
            model_fingerprint = model_configuration_fingerprint(model)
            analysis_fingerprint = analysis_configuration_fingerprint(
                _restart_analysis_contract(transient, controls, manager)
            )
        if restart_checkpoint is None:
            current_time = 0.0
            accepted_steps = 0
            resumed_acceleration = None
        else:
            current_time, accepted_steps, q, vred, resumed_acceleration = (
                _read_restart_checkpoint(
                    restart_checkpoint, model_fingerprint,
                    analysis_fingerprint, Mred.shape[0], transient.t_end,
                )
            )

        def evaluate(position: np.ndarray, *, tangent: bool):
            full = np.asarray(T @ position).reshape(-1)
            force, stiffness, trial = _assemble_nonlinear_system(
                model, full, committed_states, 3, tangent=tangent,
                kinematics="von_karman",
            )
            return full, np.asarray(T.T @ force).reshape(-1), stiffness, trial

        full0, force0, _, trial0 = evaluate(q, tangent=False)
        contact0 = manager.evaluate(full0, tangent=False)[2]
        if not contact0.gap_tolerance_met:
            raise ValueError("initial contact gap exceeds the registered tolerance")
        if resumed_acceleration is None:
            acceleration = np.asarray(spsolve(Mred, -force0)).reshape(-1)
        else:
            acceleration = resumed_acceleration
            balance = Mred @ acceleration + force0
            scale = max(1.0, float(np.linalg.norm(Mred @ acceleration)),
                        float(np.linalg.norm(force0)))
            if float(np.linalg.norm(balance)) > controls.equilibrium_tolerance*scale:
                raise ValueError("transient contact checkpoint acceleration is inconsistent")
        committed_states = commit_state_candidate(committed_states, trial0)
        times = [current_time]
        positions = [full0.copy()]
        velocities = [np.asarray(T @ vred).reshape(-1)]
        accelerations = [np.asarray(T @ acceleration).reshape(-1)]
        contacts = [contact0]
        swept_gaps = [contact0.minimum_gap]
        residuals = [float(np.linalg.norm(Mred @ acceleration + force0))]
        iterations = []
        cutbacks = 0
        previous_full = full0.copy()
        previous_velocity = np.asarray(T @ vred).reshape(-1)
        pending_swept_gap = float("inf")
        pending_residual = 0.0
        last_step_was_end_truncated = False
        _alpha, beta, gamma = transient.integration_parameters()
        while current_time < transient.t_end - 1.0e-14 * max(1.0, transient.t_end):
            remaining = transient.t_end - current_time
            step = min(transient.dt, remaining)
            end_truncated = (
                remaining < transient.dt
                - 128.0*np.finfo(float).eps*max(1.0, abs(transient.t_end))
            )
            local_cutbacks = 0
            while True:
                predictor = q + step * vred + step * step * (0.5 - beta) * acceleration
                velocity_predictor = vred + step * (1.0 - gamma) * acceleration
                candidate = predictor.copy()
                converged = False
                for iteration in range(1, controls.maximum_newton_iterations + 1):
                    full, internal, tangent, trial = evaluate(candidate, tangent=True)
                    candidate_acceleration = (candidate - predictor) / (beta * step * step)
                    residual = Mred @ candidate_acceleration + internal
                    scale = max(1.0, float(np.linalg.norm(Mred @ candidate_acceleration)),
                                float(np.linalg.norm(internal)))
                    if float(np.linalg.norm(residual)) <= controls.equilibrium_tolerance * scale:
                        contact_result = manager.evaluate(full, tangent=False)[2]
                        candidate_velocity = velocity_predictor + gamma * step * candidate_acceleration
                        full_velocity = np.asarray(T @ candidate_velocity).reshape(-1)
                        swept_gap = _minimum_hermite_gap(
                            manager, previous_full, full,
                            previous_velocity, full_velocity, step,
                        )
                        if (contact_result.gap_tolerance_met
                                and swept_gap >= -manager.gap_tolerance):
                            converged = True
                        break
                    jacobian = (Mred / (beta * step * step) + T.T @ tangent @ T).tocsr()
                    correction = np.asarray(spsolve(jacobian, -residual)).reshape(-1)
                    if not np.all(np.isfinite(correction)):
                        break
                    candidate += correction
                    discard_active_state_candidate(committed_states)
                if converged:
                    committed_states = commit_state_candidate(committed_states, trial)
                    q = candidate
                    vred = candidate_velocity
                    acceleration = candidate_acceleration
                    current_time += step
                    last_step_was_end_truncated = end_truncated
                    previous_full = full.copy()
                    previous_velocity = np.asarray(T @ vred).reshape(-1)
                    accepted_steps += 1
                    pending_swept_gap = min(pending_swept_gap, swept_gap)
                    pending_residual = max(pending_residual,
                                           float(np.linalg.norm(residual)))
                    if (accepted_steps % transient.save_every == 0
                            or current_time >= transient.t_end - 1.0e-14
                            * max(1.0, transient.t_end)):
                        times.append(current_time)
                        positions.append(full.copy())
                        velocities.append(np.asarray(T @ vred).reshape(-1))
                        accelerations.append(np.asarray(T @ acceleration).reshape(-1))
                        contacts.append(contact_result)
                        swept_gaps.append(pending_swept_gap)
                        residuals.append(pending_residual)
                        pending_swept_gap = float("inf")
                        pending_residual = 0.0
                    iterations.append(iteration)
                    break
                discard_active_state_candidate(committed_states)
                local_cutbacks += 1
                cutbacks += 1
                step *= 0.5
                if local_cutbacks > controls.maximum_cutbacks or step < controls.minimum_dt:
                    raise RuntimeError(
                        f"transient contact step failed at t={current_time:.9g} s "
                        f"after {local_cutbacks} cutbacks; committed state retained"
                    )
    if emit_restart_checkpoint and (accepted_steps == 0 or last_step_was_end_truncated):
        raise ValueError(
            "transient contact checkpoint requires an accepted untruncated final time step"
        )
    checkpoint = (
        _new_restart_checkpoint(
            model_fingerprint, analysis_fingerprint, current_time,
            q, vred, acceleration, accepted_steps,
        ) if emit_restart_checkpoint else None
    )
    return TransientContactResults(
        _PROFILE, np.asarray(times), np.asarray(positions),
        np.asarray(velocities), np.asarray(accelerations), tuple(contacts),
        np.asarray(swept_gaps), np.asarray(residuals), cutbacks, tuple(iterations),
        checkpoint,
    )
