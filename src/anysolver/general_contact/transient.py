"""Narrowly admitted nonlinear Newmark shell-contact development profiles.

The coupled residual is evaluated by the ordinary nonlinear structural
assembler inside one contact scope. The Q4 profile uses positive-definite
reduced mass; a separate guided single-S3 V2D profile retains declared
massless rotations and recovers their rates from algebraic equilibrium.
A distinct S3 history profile scales the same dead nodal load by a
piecewise-linear factor in time; its complete base load must lie in the
physical mass range so the scalar history never forces the algebraic
manifold. No profile here qualifies the broader C6 impact capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from bisect import bisect_right
from functools import wraps
from typing import Mapping

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve
from anymaterial.isotropic import IsotropicMaterial

from anysolver.algebraic_dynamics import build_declared_algebraic_basis
from anysolver.assembly import assemble_mass_matrix, build_constraint_transformation
from anysolver.boundary import LoadCase
from anysolver.control import CancellationToken
from anysolver.dynamics import TransientConfig
from anysolver.e4_pl_element import QualifiedE4PLShellElement
from anysolver.e4_pl_s3_v2d_element import NativeParityE4PLS3V2DShellElement
from anysolver.matrix_assembly import assemble_load_vector, assemble_stiffness_matrix
from anysolver.nonlinear_state import (
    commit_state_candidate, discard_active_state_candidate,
    _run_with_nonlinear_state_cleanup,
)
from anysolver.nonlinear_restart import (
    analysis_configuration_fingerprint, model_configuration_fingerprint,
)
from anysolver.nonlinear_static import (
    _assemble_nonlinear_system, _is_known_cancellation_checkpoint,
)

from .core import (
    ContactDefinition,
    ContactResults,
    ContactSolverSettings,
    _PlanarQ4PlaneManager,
    contact_scope,
    suspend_contact,
    validate_general_contact,
)
from .descriptor_rates import directional_descriptor_rate
from .algebraic_path import affine_descriptor_path
from .event_subdivision import EventNeedsCutback, localize_branch_event


_PROFILE = "PLANAR_Q4_FIXED_PLANE_NEWMARK_PENALTY_DEV_V1"
_S3_PROFILE = "PLANAR_S3_V2D_FIXED_PLANE_NEWMARK_DESCRIPTOR_DEV_V0"
_S3_HISTORY_PROFILE = "PLANAR_S3_V2D_FIXED_PLANE_NEWMARK_DESCRIPTOR_HISTORY_DEV_V1"
_S3_DIRECTIONAL_PROFILE = "PLANAR_S3_V2D_FIXED_PLANE_NEWMARK_DIRECTIONAL_RATES_DEV_V1"
_S3_DIRECTIONAL_HISTORY_PROFILE = "PLANAR_S3_V2D_FIXED_PLANE_NEWMARK_DIRECTIONAL_HISTORY_DEV_V1"
_S3_ALGEBRAIC_PATH_PROFILE = "PLANAR_S3_V2D_FIXED_PLANE_NEWMARK_ALGEBRAIC_PATH_DEV_V1"
_S3_ALGEBRAIC_PATH_HISTORY_PROFILE = "PLANAR_S3_V2D_FIXED_PLANE_NEWMARK_ALGEBRAIC_PATH_HISTORY_DEV_V1"
_S3_EVENT_PROFILE = "PLANAR_S3_V2D_FIXED_PLANE_NEWMARK_EVENT_SUBDIVISION_DEV_V1"
_S3_EVENT_HISTORY_PROFILE = "PLANAR_S3_V2D_FIXED_PLANE_NEWMARK_EVENT_SUBDIVISION_HISTORY_DEV_V1"
_RESTART_SCHEMA = "ANYSOLVER_Q4_PLANE_TRANSIENT_CONTACT_DEV_CHECKPOINT_V1"
_HISTORY_RESTART_SCHEMA = "ANYSOLVER_Q4_PLANE_TRANSIENT_CONTACT_DEV_CHECKPOINT_V2"
_ALGEBRAIC_PATH_RESTART_SCHEMA = "ANYSOLVER_S3_ALGEBRAIC_PATH_TRANSIENT_CONTACT_DEV_CHECKPOINT_V3"
_EVENT_RESTART_SCHEMA = "ANYSOLVER_S3_EVENT_SUBDIVISION_TRANSIENT_CONTACT_DEV_CHECKPOINT_V4"


@dataclass(frozen=True)
class ContactNodalLoadHistory:
    """Piecewise-linear scale of one fixed nodal LoadCase in physical time."""

    points: tuple[tuple[float, float], ...]

    def __post_init__(self) -> None:
        try:
            points = tuple(tuple(point) for point in self.points)
        except TypeError as exc:
            raise ValueError("nodal load history needs time-factor pairs") from exc
        if (len(points) < 2 or any(len(point) != 2 for point in points)
                or any(not all(
                    type(value) is not bool
                    and isinstance(value, (int, float, np.integer, np.floating))
                    and np.isfinite(value)
                    for value in point)
                       for point in points)
                or points[0][0] != 0.0
                or any(right[0] <= left[0]
                       for left, right in zip(points, points[1:]))):
            raise ValueError("nodal load history needs finite increasing time-factor pairs from zero")
        object.__setattr__(self, "points", tuple((float(t), float(f))
                                                 for t, f in points))

    def factor(self, time_s: float) -> float:
        if time_s < 0.0 or time_s > self.points[-1][0]:
            raise ValueError("nodal load history does not cover the requested time")
        if time_s == self.points[-1][0]:
            return float(self.points[-1][1])
        index = max(0, bisect_right(self.points, (time_s, float("inf")))-1)
        first, last = self.points[index:index+2]
        fraction = (time_s-first[0])/(last[0]-first[0])
        return float(first[1]+fraction*(last[1]-first[1]))


def _hermite_linear_load_work(
    start: np.ndarray, end: np.ndarray,
    start_velocity: np.ndarray, end_velocity: np.ndarray,
    start_force: np.ndarray, end_force: np.ndarray, dt: float,
) -> float:
    """Exact work of linear dead load on the declared cubic Hermite step path."""
    total = 0.0
    for s in (0.5-0.5/np.sqrt(3.0), 0.5+0.5/np.sqrt(3.0)):
        derivative = (
            (6*s*s-6*s)*start + (3*s*s-4*s+1)*dt*start_velocity
            + (-6*s*s+6*s)*end + (3*s*s-2*s)*dt*end_velocity
        )
        force = (1-s)*start_force+s*end_force
        total += 0.5*float(force @ derivative)
    return total


@dataclass(frozen=True)
class ContactTransientSolverControls:
    """Nonlinear iteration limits for the developing contact driver."""

    maximum_newton_iterations: int = 20
    maximum_cutbacks: int = 8
    minimum_dt: float = 1.0e-8
    equilibrium_tolerance: float = 1.0e-8
    allow_s3_descriptor_dev: bool = False
    s3_descriptor_difference_step_s: float = 1.0e-5
    s3_one_sided_rates_dev: bool = False
    s3_algebraic_path_dev: bool = False
    s3_path_position_tolerance_m: float = 1.0e-10
    s3_path_rotation_tolerance_rad: float = 1.0e-9
    s3_event_subdivision_dev: bool = False
    s3_event_time_tolerance_s: float = 1.0e-10
    s3_event_gap_tolerance_m: float = 1.0e-10
    maximum_event_localizations: int = 12
    maximum_event_root_iterations: int = 64

    def __post_init__(self) -> None:
        if type(self.maximum_newton_iterations) is not int or self.maximum_newton_iterations < 1:
            raise ValueError("maximum_newton_iterations must be a positive integer")
        if type(self.maximum_cutbacks) is not int or self.maximum_cutbacks < 0:
            raise ValueError("maximum_cutbacks must be a nonnegative integer")
        if not np.isfinite(self.minimum_dt) or self.minimum_dt <= 0.0:
            raise ValueError("minimum_dt must be finite and positive")
        if not np.isfinite(self.equilibrium_tolerance) or self.equilibrium_tolerance <= 0.0:
            raise ValueError("equilibrium_tolerance must be finite and positive")
        if type(self.allow_s3_descriptor_dev) is not bool:
            raise ValueError("allow_s3_descriptor_dev must be boolean")
        if type(self.s3_one_sided_rates_dev) is not bool:
            raise ValueError("s3_one_sided_rates_dev must be boolean")
        if self.s3_one_sided_rates_dev and not self.allow_s3_descriptor_dev:
            raise ValueError("one-sided rates require the S3 descriptor opt-in")
        if type(self.s3_algebraic_path_dev) is not bool:
            raise ValueError("s3_algebraic_path_dev must be boolean")
        if self.s3_algebraic_path_dev and not self.s3_one_sided_rates_dev:
            raise ValueError("algebraic path requires the S3 one-sided-rate opt-in")
        for name in ("s3_path_position_tolerance_m", "s3_path_rotation_tolerance_rad"):
            value = getattr(self, name)
            if isinstance(value, (bool, np.bool_)) or not np.isfinite(value) or value <= 0.:
                raise ValueError(f"{name} must be finite and positive")
        if type(self.s3_event_subdivision_dev) is not bool:
            raise ValueError("s3_event_subdivision_dev must be boolean")
        if self.s3_event_subdivision_dev and not self.s3_algebraic_path_dev:
            raise ValueError("event subdivision requires the S3 algebraic-path opt-in")
        for name in ("s3_event_time_tolerance_s", "s3_event_gap_tolerance_m"):
            value = getattr(self, name)
            if isinstance(value, (bool, np.bool_)) or not np.isfinite(value) or value <= 0.:
                raise ValueError(f"{name} must be finite and positive")
        for name in ("maximum_event_localizations", "maximum_event_root_iterations"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError(f"{name} must be a positive integer")
        if (not np.isfinite(self.s3_descriptor_difference_step_s)
                or self.s3_descriptor_difference_step_s <= 0.0):
            raise ValueError("s3_descriptor_difference_step_s must be finite and positive")


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
    external_nodal_work_j: np.ndarray
    restart_checkpoint: dict | None = None
    represented_path_transition_times: tuple[float, ...] = ()
    localized_contact_event_times: tuple[float, ...] = ()
    event_endpoint_evaluations: int = 0


def _restart_analysis_contract(transient, controls, manager, profile,
                               base_load_case, external_load,
                               load_history) -> dict:
    # The requested end time is a continuation target, not a definition of
    # the already accepted state. All other integration inputs are bound.
    contract = {
        "profile": profile,
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
            "allow_s3_descriptor_dev": controls.allow_s3_descriptor_dev,
            "s3_descriptor_difference_step_s": controls.s3_descriptor_difference_step_s,
        },
        "contact": manager.restart_contract(),
    }
    if base_load_case is not None:
        contract["constant_nodal_load"] = {
            "name": base_load_case.name,
            "generalized_vector_si": np.asarray(external_load).tolist(),
        }
    if load_history is not None:
        contract["nodal_load_history"] = [list(point)
                                          for point in load_history.points]
    if controls.s3_one_sided_rates_dev:
        # Absent for historical profiles, preserving their checkpoint contract.
        contract["controls"]["s3_one_sided_rates_dev"] = True
    if controls.s3_algebraic_path_dev:
        contract["controls"]["s3_algebraic_path_dev"] = True
        contract["controls"]["s3_path_position_tolerance_m"] = controls.s3_path_position_tolerance_m
        contract["controls"]["s3_path_rotation_tolerance_rad"] = controls.s3_path_rotation_tolerance_rad
    if controls.s3_event_subdivision_dev:
        for name in ("s3_event_subdivision_dev", "s3_event_time_tolerance_s",
                     "s3_event_gap_tolerance_m", "maximum_event_localizations",
                     "maximum_event_root_iterations"):
            contract["controls"][name] = getattr(controls, name)
    return contract


def _new_restart_checkpoint(model_fingerprint, analysis_fingerprint,
                            current_time, q, velocity, acceleration,
                            accepted_steps, external_work_j=None, path_terminal_active=None,
                            event_boundary_support=None) -> dict:
    payload = {
        "schema": (_HISTORY_RESTART_SCHEMA if external_work_j is not None
                   else _RESTART_SCHEMA),
        "version": 2 if external_work_j is not None else 1,
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
    if external_work_j is not None:
        payload["state"]["external_work_j"] = float(external_work_j)
    if path_terminal_active is not None:
        payload["schema"] = _ALGEBRAIC_PATH_RESTART_SCHEMA
        payload["version"] = 3
        payload["state"]["path_terminal_active"] = list(path_terminal_active)
    if event_boundary_support is not None:
        payload["schema"] = _EVENT_RESTART_SCHEMA
        payload["version"] = 4
        payload["state"]["event_boundary_support"] = list(event_boundary_support)
    payload["checkpoint_sha256"] = analysis_configuration_fingerprint(payload)
    return payload


def _read_restart_checkpoint(value, model_fingerprint, analysis_fingerprint,
                             reduced_size, t_end, *, load_history, path_pressure_dofs=0,
                             event_subdivision=False):
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
    expected_version = 2 if load_history is not None else 1
    expected_schema = (_HISTORY_RESTART_SCHEMA if load_history is not None
                       else _RESTART_SCHEMA)
    if path_pressure_dofs:
        expected_version, expected_schema = 3, _ALGEBRAIC_PATH_RESTART_SCHEMA
    if event_subdivision:
        expected_version, expected_schema = 4, _EVENT_RESTART_SCHEMA
    if payload["schema"] != expected_schema or payload["version"] != expected_version:
        raise ValueError("transient contact checkpoint version is incompatible")
    if payload["model_fingerprint"] != model_fingerprint:
        raise ValueError("transient contact checkpoint model is incompatible")
    if payload["analysis_fingerprint"] != analysis_fingerprint:
        raise ValueError("transient contact checkpoint analysis is incompatible")
    state = payload["state"]
    expected_state_keys = {
        "time", "q", "velocity", "acceleration", "accepted_steps",
    }
    if load_history is not None:
        expected_state_keys.add("external_work_j")
    if path_pressure_dofs:
        expected_state_keys.add("path_terminal_active")
    if event_subdivision:
        expected_state_keys.add("event_boundary_support")
    if not isinstance(state, Mapping) or set(state) != expected_state_keys:
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
    work = float(state["external_work_j"]) if load_history is not None else None
    if work is not None and not np.isfinite(work):
        raise ValueError("transient contact checkpoint external work is invalid")
    terminal = None
    if path_pressure_dofs:
        terminal = state["path_terminal_active"]
        if (type(terminal) is not list or len(terminal) != path_pressure_dofs
                or any(type(flag) is not bool for flag in terminal)):
            raise ValueError("transient contact checkpoint path activity is invalid")
        terminal = tuple(terminal)
    values = (time, steps, *arrays, work, terminal)
    if event_subdivision:
        boundary = state["event_boundary_support"]
        if (type(boundary) is not list or any(type(i) is not int
                or not 0 <= i < path_pressure_dofs for i in boundary)
                or boundary != sorted(set(boundary))):
            raise ValueError("transient contact checkpoint event boundary is invalid")
        values += (tuple(boundary),)
    return values


def _consistent_s3_descriptor_rates(
    model, T, Mred, basis, full_position, reduced_velocity,
    reduced_acceleration, full_tangent, committed_states, difference_step_s,
    *, one_sided_manager=None, maximum_iterations=20,
    event_touch_indices=(), event_gap_tolerance=None,
):
    """Recover massless rates from the current nonlinear algebraic manifold.

    The physical mass equation fixes rates modulo the certified null basis Z.
    For G(q)=Z.T*F(q)=0, smooth-branch rates satisfy
    Z.T*K(q)*v=0 and Z.T*(K(q)*a+F''(q)[v,v])=0. The contact-plane
    penalty tangent is constant on a fixed active branch, so the directional
    second derivative comes only from the smooth structural force here.
    """
    Z = basis.reduced_basis.toarray()
    gram = Z.T @ Z
    K = (T.T @ full_tangent @ T).toarray()
    algebraic = Z.T @ K @ Z
    if one_sided_manager is not None:
        manager = one_sided_manager
        _, contact_tangent, _ = manager.evaluate(full_position, tangent=True)
        structural = K-(T.T @ contact_tangent @ T).toarray()
        B = (sparse.diags(1./manager.support) @ manager.gap_gradient @ T).toarray()
        shift = -float((manager.point-manager.reference_point) @ manager.normal)
        reference_gap = manager.reference_weighted_gap/manager.support+shift
        normalized_gap = (reference_gap
                          +np.asarray(manager.gap_gradient @ full_position).reshape(-1)/manager.support)
        # Tie budget follows arithmetic operands, not the physical gap budget.
        operand_scale = (np.abs(reference_gap)
                         +np.asarray(abs(manager.gap_gradient) @ np.abs(full_position)).reshape(-1)/manager.support)
        touch = np.abs(normalized_gap) <= 64*np.finfo(float).eps*operand_scale
        if event_touch_indices:
            indices = list(event_touch_indices)
            if (event_gap_tolerance is None
                    or np.any(np.abs(normalized_gap[indices]) > event_gap_tolerance)):
                raise ValueError("resolved S3 event touch exceeds its gap budget")
            touch[indices] = True
        closed = (normalized_gap < 0.) & ~touch
        weights = manager.stiffness*manager.support

    def physical_part(value):
        return value - Z @ np.linalg.solve(gram, Z.T @ value)

    try:
        if one_sided_manager is None:
            physical_velocity = physical_part(reduced_velocity)
            velocity = physical_velocity + Z @ np.linalg.solve(
                algebraic, -Z.T @ K @ physical_velocity,
            )
        else:
            velocity = directional_descriptor_rate(
                structural, Z, reduced_velocity, B, weights, closed, touch,
                maximum_iterations=maximum_iterations,
            )
    except np.linalg.LinAlgError as exc:
        raise ValueError("S3 descriptor algebraic velocity solve is singular") from exc
    full_velocity = np.asarray(T @ velocity).reshape(-1)
    h = float(difference_step_s)
    with suspend_contact():
        _, plus, _ = _assemble_nonlinear_system(
            model, full_position+h*full_velocity, committed_states, 3,
            tangent=True, kinematics="von_karman",
        )
        discard_active_state_candidate(committed_states)
        _, minus, _ = _assemble_nonlinear_system(
            model, full_position-h*full_velocity, committed_states, 3,
            tangent=True, kinematics="von_karman",
        )
        discard_active_state_candidate(committed_states)
    structural_curvature = np.asarray(
        T.T @ ((plus-minus) @ full_velocity)
    ).reshape(-1)/(2.0*h)
    try:
        if one_sided_manager is None:
            physical_acceleration = physical_part(reduced_acceleration)
            acceleration = physical_acceleration + Z @ np.linalg.solve(
                algebraic,
                -Z.T @ (K @ physical_acceleration+structural_curvature),
            )
        else:
            gap_rate = B @ velocity
            rate_roundoff = 64*np.finfo(float).eps*(np.abs(B) @ np.abs(velocity))
            stationary_touch = touch & (np.abs(gap_rate) <= rate_roundoff)
            closing_touch = touch & (gap_rate < -rate_roundoff)
            acceleration = directional_descriptor_rate(
                structural, Z, reduced_acceleration, B, weights,
                closed | closing_touch, stationary_touch,
                offset=structural_curvature, maximum_iterations=maximum_iterations,
            )
    except np.linalg.LinAlgError as exc:
        raise ValueError("S3 descriptor algebraic acceleration solve is singular") from exc
    if (not np.all(np.isfinite(velocity)) or not np.all(np.isfinite(acceleration))
            or np.linalg.norm(Mred @ (acceleration-reduced_acceleration))
            > 1.0e-8*max(1.0, np.linalg.norm(Mred @ reduced_acceleration))):
        raise ValueError("S3 descriptor rate recovery changed physical inertia")
    return velocity, acceleration


@dataclass(frozen=True)
class _S3AffinePathAdapter:
    structural: np.ndarray
    null_basis: np.ndarray
    gradient: np.ndarray
    reference_gap: np.ndarray
    weights: np.ndarray
    force_offset: np.ndarray
    corner_reference: np.ndarray
    corner_gradient: np.ndarray

    @classmethod
    def prepare(cls, model, T, basis, manager, committed_states):
        # The admitted exact elastic S3 local operator is reference-linear.
        # This would be a tangent approximation for a generic nonlinear owner;
        # _admit deliberately does not permit that substitution.
        with suspend_contact():
            force, stiffness, _ = _assemble_nonlinear_system(
                model, np.zeros(T.shape[0]), committed_states, 3,
                tangent=True, kinematics="von_karman",
            )
            discard_active_state_candidate(committed_states)
        structural = (T.T @ stiffness @ T).toarray()
        Z = basis.reduced_basis.toarray()
        try:
            np.linalg.cholesky(Z.T @ structural @ Z)
        except np.linalg.LinAlgError as exc:
            raise ValueError("S3 affine path requires positive definite algebraic work") from exc
        B = (sparse.diags(1./manager.support) @ manager.gap_gradient @ T).toarray()
        shift = -float((manager.point-manager.reference_point) @ manager.normal)
        g = manager.reference_weighted_gap/manager.support+shift
        corners, gradients = [], []
        for reference, dofs, _shape, skin_offset, gradient in manager.patches:
            corners.extend((reference+skin_offset-manager.point) @ manager.normal)
            for corner_dofs in dofs:
                full_gradient = np.zeros(T.shape[0])
                full_gradient[corner_dofs] = gradient
                gradients.append(np.asarray(full_gradient @ T).reshape(-1))
        return cls(structural, Z, B, g, manager.stiffness*manager.support,
                   np.asarray(T.T @ force).reshape(-1), np.asarray(corners), np.asarray(gradients))

    def evaluate(self, start, end, velocity, dt, load):
        coefficients = np.stack((start, dt*velocity, end-start-dt*velocity))
        path = affine_descriptor_path(
            self.structural, self.null_basis, coefficients, self.gradient,
            self.reference_gap, self.weights, force=load-self.force_offset,
        )
        return path, path.minimum_gap(self.corner_reference, self.corner_gradient)

    def check_endpoints(self, path, start, end, transform, controls):
        for lifted, actual in ((path.segments[0].position(0.), start),
                               (path.segments[-1].position(1.), end)):
            error = np.asarray(transform @ (lifted-actual)).reshape(-1, 6)
            if (np.max(np.abs(error[:, :3])) > controls.s3_path_position_tolerance_m
                    or np.max(np.abs(error[:, 3:])) > controls.s3_path_rotation_tolerance_rad):
                raise ValueError("S3 lifted path endpoint mismatch exceeds its numerical budget")

    def endpoint_force(self, position, load):
        gap = self.reference_gap+self.gradient @ position
        return (self.structural @ position+self.force_offset-load
                +self.gradient.T @ (self.weights*np.minimum(gap, 0.)))


def _accepted_path_transition_times(previous_active, path, start_time, step):
    times = []
    if previous_active is not None and previous_active != path.segments[0].active:
        times.append(float(start_time))
    times.extend(float(start_time+step*s) for s in path.transition_fractions)
    return tuple(times)


def _event_continuation_segments(path, step, boundary_support, start_gaps,
                                 time_tolerance, gap_tolerance):
    """Coalesce only contiguous transitions of the committed numerical boundary.

    The original path remains authoritative for force/work and interval minima.
    This changes which transition still requires a new physical event step.
    """
    index = 0
    resolved = frozenset(boundary_support)
    while resolved and index+1 < len(path.segments):
        left,right = path.segments[index:index+2]
        changed = tuple(i for i,(a,b) in enumerate(zip(left.active,right.active)) if a != b)
        if (left.end*step > time_tolerance or not changed
                or any(i not in resolved for i in changed)
                or np.any(np.abs(start_gaps[list(changed)]) > gap_tolerance)):
            break
        index += 1
    return path.segments[index:]


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


def _admit(model, definition: ContactDefinition, settings: ContactSolverSettings,
           controls: ContactTransientSolverControls) -> str:
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
    if set(surface.element_ids) != set(model.mesh.elements):
        raise ValueError("transient development profile requires every shell element on the surface")
    elements = tuple(model.mesh.elements.values())
    if all(type(element) is QualifiedE4PLShellElement for element in elements):
        if controls.allow_s3_descriptor_dev:
            raise ValueError("S3 descriptor opt-in requires one qualified S3 V2D element")
        profile = _PROFILE
    elif (len(elements) == 1
          and type(elements[0]) is NativeParityE4PLS3V2DShellElement
          and controls.allow_s3_descriptor_dev):
        profile = _S3_PROFILE
    else:
        raise ValueError("transient development profile requires qualified Q4 or opted-in single S3 V2D")
    for element in model.mesh.elements.values():
        material = model.get_material(element.material_name)
        if (type(material) is not IsotropicMaterial
                or float(material.yield_stress) != 0.0
                or material.hardening_curve is not None):
            raise ValueError("transient development profile admits only isotropic elastic material")
    return profile


def _with_transient_state_cleanup(operation):
    @wraps(operation)
    def wrapped(*args, **kwargs):
        return _run_with_nonlinear_state_cleanup(operation, *args, **kwargs)
    return wrapped


@_with_transient_state_cleanup
def solve_transient_contact(
    model,
    definition: ContactDefinition,
    transient: TransientConfig | TransientContactSettings,
    *,
    contact_settings: ContactSolverSettings | None = None,
    base_load_case: LoadCase | None = None,
    nodal_load_history: ContactNodalLoadHistory | None = None,
    solver_controls: ContactTransientSolverControls | None = None,
    restart_checkpoint: Mapping | None = None,
    emit_restart_checkpoint: bool = False,
    cancellation_token: CancellationToken | None = None,
) -> TransientContactResults:
    """Solve bounded elastic Q4 or S3 V2D fixed-plane impact.

    Every Newton evaluation starts from the last committed material state.
    A rejected step leaves both the displacement and material state at the
    last accepted time. The fixed-plane gap is checked independently at each
    accepted endpoint and over its declared cubic Hermite integration path.
    S3 descriptor admission additionally requires explicit opt-in and a
    strictly open, stress-free rigid-normal initial state.
    The S3 descriptor profiles admit a piecewise-linear nodal load history
    only when the complete base load has zero algebraic projection; the
    distinct history profile is bound into restart contracts.
    The separate S3 algebraic-path opt-in instead lifts the physical Newmark
    quadratic through reference-linear elastic/penalty algebraic equilibrium.
    Full endpoint agreement and corner minima are checked; reported transitions
    describe this discrete path, not exact continuum event times.
    Cancellation admits only the solver's exact unmodified token. It raises
    SolveCancelled at a safe boundary, discards solve-owned pending trials and
    returns no partial result or checkpoint. Completed increments remain committed.
    """

    def check_cancel(stage):
        if not _is_known_cancellation_checkpoint(cancellation_token):
            raise TypeError("transient contact requires an exact unmodified CancellationToken")
        if cancellation_token is not None:
            cancellation_token.raise_if_cancelled(stage)

    check_cancel("transient contact entry")
    transient, controls = _resolve_transient_inputs(transient, solver_controls)
    if (restart_checkpoint is not None or emit_restart_checkpoint) and transient.save_every != 1:
        raise ValueError("transient contact development restart requires save_every=1")
    if emit_restart_checkpoint and transient.t_end <= 0.0:
        raise ValueError("transient contact checkpoint needs one accepted time step")
    settings = ContactSolverSettings() if contact_settings is None else contact_settings
    profile = _admit(model, definition, settings, controls)
    if nodal_load_history is not None:
        if type(nodal_load_history) is not ContactNodalLoadHistory:
            raise TypeError("nodal_load_history must be ContactNodalLoadHistory")
        if base_load_case is None or profile not in (_PROFILE, _S3_PROFILE):
            raise ValueError("nodal load history requires one Q4 plane nodal LoadCase or opted-in S3 plane nodal LoadCase")
        if nodal_load_history.points[-1][0] < transient.t_end:
            raise ValueError("nodal load history must cover t_end")
        if any(
            right[0]-left[0] < max(
                controls.minimum_dt,
                16.0*np.finfo(float).eps*max(1.0, abs(right[0])),
            )
            for left, right in zip(nodal_load_history.points,
                                   nodal_load_history.points[1:])
        ):
            raise ValueError("nodal load history knots are closer than the admitted minimum_dt or time resolution")
        if profile == _S3_PROFILE:
            profile = _S3_HISTORY_PROFILE
    s3_descriptor = profile in (_S3_PROFILE, _S3_HISTORY_PROFILE)
    if controls.s3_one_sided_rates_dev:
        profile = (_S3_DIRECTIONAL_HISTORY_PROFILE if nodal_load_history is not None
                   else _S3_DIRECTIONAL_PROFILE)
    if controls.s3_algebraic_path_dev:
        profile = (_S3_ALGEBRAIC_PATH_HISTORY_PROFILE if nodal_load_history is not None
                   else _S3_ALGEBRAIC_PATH_PROFILE)
    if controls.s3_event_subdivision_dev:
        profile = (_S3_EVENT_HISTORY_PROFILE if nodal_load_history is not None
                   else _S3_EVENT_PROFILE)
    if base_load_case is not None:
        if (type(base_load_case) is not LoadCase
                or not base_load_case.nodal_loads
                or base_load_case.element_loads
                or base_load_case.pressure_loads
                or base_load_case.gravity is not None
                or base_load_case.added_node_masses
                or base_load_case.follower_pressure):
            raise ValueError("transient development loads require one nodal-only dead LoadCase")
    model.apply_boundary_conditions()
    size = model.mesh.dof_manager.total_dofs
    external_load, _load_info = assemble_load_vector(model, base_load_case)
    if external_load.shape != (size,) or not np.all(np.isfinite(external_load)):
        raise ValueError("transient development load vector is invalid")
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
    external_reduced = np.asarray(T.T @ external_load).reshape(-1)
    if np.linalg.norm(u0, ord=np.inf) > 1.0e-13:
        raise ValueError("transient development profile requires zero prescribed displacements")
    if not len(independent_dofs):
        raise ValueError("transient contact requires at least one free coordinate")
    if s3_descriptor:
        element = next(iter(model.mesh.elements.values()))
        expected_free = sorted(
            int(model.mesh.dof_manager.get_node_dofs(node)[local])
            for node in element.node_ids for local in (2, 3, 4, 5)
        )
        if (sorted(map(int, independent_dofs)) != expected_free
                or (T - sparse.eye(size, format="csr")[:, independent_dofs]).nnz):
            raise ValueError(
                "S3 descriptor development requires each node guided in-plane "
                "with free normal displacement and rotations"
            )
    Mred = (T.T @ M @ T).tocsr()
    if Mred.shape[0] > 512:
        raise ValueError("transient development profile admits at most 512 free coordinates")
    descriptor_basis = None
    if profile == _PROFILE:
        try:
            np.linalg.cholesky(Mred.toarray())
        except np.linalg.LinAlgError as exc:
            raise ValueError("reduced mass is not positive definite; algebraic dynamics are not admitted") from exc
    else:
        descriptor_basis = build_declared_algebraic_basis(
            model, M, Mred, T, independent_dofs, dense_size_limit=512,
        )
        nullity = descriptor_basis.reduced_basis.shape[1]
        spectrum = np.linalg.eigvalsh(Mred.toarray())
        mass_scale = float(np.max(np.abs(spectrum)))
        if not np.isfinite(mass_scale) or mass_scale <= 0.0:
            raise ValueError("S3 descriptor needs positive physical mass")
        threshold = 1.0e-10*mass_scale
        if (nullity < 1 or int(np.count_nonzero(spectrum <= threshold)) != nullity
                or np.any(spectrum < -threshold)):
            raise ValueError("S3 descriptor mass nullity disagrees with declared algebraic basis")
        if s3_descriptor and nodal_load_history is not None:
            # The complete base load must satisfy Z.T f_base = 0 so the scalar
            # history cannot force the algebraic manifold; a zero initial
            # scale must not hide an algebraic base load.
            algebraic_base_force = np.asarray(
                descriptor_basis.reduced_basis.T @ external_reduced
            ).reshape(-1)
            # History amplitude and slope are not bounded. A tolerance-sized
            # nonzero algebraic base force could be amplified later, and its
            # time derivatives are absent from the admitted rate equations.
            if np.any(algebraic_base_force != 0.0):
                raise ValueError(
                    "S3 descriptor base load has unresolved algebraic force"
                )
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
    if s3_descriptor:
        # This first descriptor impact admits a stress-free rigid normal
        # approach. General DAE initial states require a separate consistency
        # solve for algebraic displacement, velocity and acceleration.
        if np.linalg.norm(full_initial, ord=np.inf) > 1.0e-13:
            raise ValueError("S3 descriptor development needs zero initial displacement")
        normal = np.asarray(definition.rigid_bodies[0].normal, dtype=float)
        nodal_velocity = np.asarray([
            initial_velocity[model.mesh.dof_manager.get_node_dofs(node)[:6]]
            for node in model.mesh.elements[
                definition.surfaces[0].element_ids[0]
            ].node_ids
        ])
        speed = float(nodal_velocity[0, :3] @ normal)
        expected_velocity = np.r_[speed*normal, np.zeros(3)]
        if not np.allclose(nodal_velocity, expected_velocity[None, :],
                           rtol=0.0, atol=1.0e-12):
            raise ValueError("S3 descriptor development needs uniform rigid-normal initial velocity")
    committed_states = {}
    # The manager's fresh-start guard checks the original configured pose.
    # The resumed pose is validated separately against its accepted gap budget.
    with contact_scope(model, definition, settings,
                       initial_displacement=full_initial) as manager:
        if type(manager) is not _PlanarQ4PlaneManager:
            raise ValueError("transient development profile selected an unsupported contact owner")
        path_adapter = (_S3AffinePathAdapter.prepare(
            model, T, descriptor_basis, manager, committed_states,
        ) if controls.s3_algebraic_path_dev else None)

        if restart_checkpoint is not None or emit_restart_checkpoint:
            model_fingerprint = model_configuration_fingerprint(model)
            analysis_fingerprint = analysis_configuration_fingerprint(
                _restart_analysis_contract(
                    transient, controls, manager, profile,
                    base_load_case, external_load, nodal_load_history,
                )
            )
        if restart_checkpoint is None:
            current_time = 0.0
            accepted_steps = 0
            resumed_acceleration = None
            resumed_work = None
            last_path_active = None
            event_boundary_support = ()
        else:
            resumed = _read_restart_checkpoint(
                    restart_checkpoint, model_fingerprint,
                    analysis_fingerprint, Mred.shape[0], transient.t_end,
                    load_history=nodal_load_history,
                    path_pressure_dofs=(manager.support.size if path_adapter is not None else 0),
                    event_subdivision=controls.s3_event_subdivision_dev,
                )
            current_time, accepted_steps, q, vred, resumed_acceleration, resumed_work, last_path_active = resumed[:7]
            event_boundary_support = resumed[7] if controls.s3_event_subdivision_dev else ()
            if event_boundary_support:
                boundary_gaps = path_adapter.reference_gap+path_adapter.gradient @ q
                if np.any(np.abs(boundary_gaps[list(event_boundary_support)])
                          > controls.s3_event_gap_tolerance_m):
                    raise ValueError("transient contact checkpoint event boundary exceeds its gap budget")

        def load_at(time_s: float) -> np.ndarray:
            if nodal_load_history is None:
                return external_reduced
            return nodal_load_history.factor(time_s)*external_reduced

        def evaluate(position: np.ndarray, time_s: float, *, tangent: bool):
            full = np.asarray(T @ position).reshape(-1)
            force, stiffness, trial = _assemble_nonlinear_system(
                model, full, committed_states, 3, tangent=tangent,
                kinematics="von_karman",
            )
            return (full, np.asarray(T.T @ force).reshape(-1)
                    - load_at(time_s), stiffness, trial)

        check_cancel("transient contact initial evaluation")
        full0, force0, initial_tangent, trial0 = evaluate(
            q, current_time,
            tangent=(s3_descriptor and restart_checkpoint is None),
        )
        contact0 = manager.evaluate(full0, tangent=False)[2]
        if not contact0.gap_tolerance_met:
            raise ValueError("initial contact gap exceeds the registered tolerance")
        if (s3_descriptor and restart_checkpoint is None
                and contact0.minimum_gap <= 1.0e-10):
            raise ValueError("S3 descriptor development requires a strictly open initial gap")
        if resumed_acceleration is None:
            if s3_descriptor:
                basis = descriptor_basis.reduced_basis
                reduced_tangent = (T.T @ initial_tangent @ T).tocsr()
                algebraic_velocity_work = np.asarray(
                    basis.T @ (reduced_tangent @ vred)
                ).reshape(-1)
                if float(np.linalg.norm(algebraic_velocity_work)) > controls.equilibrium_tolerance:
                    raise ValueError("S3 descriptor initial algebraic state is inconsistent")
                if base_load_case is None:
                    if float(np.linalg.norm(force0)) > controls.equilibrium_tolerance:
                        raise ValueError("S3 descriptor initial algebraic state is inconsistent")
                    # Rigid-normal free motion has zero initial acceleration.
                    acceleration = np.zeros_like(q)
                else:
                    force_scale = max(1.0, float(np.linalg.norm(force0)))
                    algebraic_force = np.asarray(basis.T @ force0).reshape(-1)
                    if (float(np.linalg.norm(algebraic_force))
                            > controls.equilibrium_tolerance*force_scale):
                        raise ValueError("S3 descriptor initial load has unresolved algebraic force")
                    physical_acceleration = -np.linalg.pinv(
                        Mred.toarray(), rcond=1.0e-10,
                    ) @ force0
                    mass_balance = Mred @ physical_acceleration + force0
                    if (not np.all(np.isfinite(physical_acceleration))
                            or float(np.linalg.norm(mass_balance))
                            > controls.equilibrium_tolerance*force_scale):
                        raise ValueError("S3 descriptor initial load is outside the physical mass range")
                    recovered_velocity, acceleration = _consistent_s3_descriptor_rates(
                        model, T, Mred, descriptor_basis, full0, vred,
                        physical_acceleration, initial_tangent,
                        committed_states, controls.s3_descriptor_difference_step_s,
                        one_sided_manager=(manager if controls.s3_one_sided_rates_dev else None),
                        maximum_iterations=controls.maximum_newton_iterations,
                    )
                    if not np.allclose(recovered_velocity, vred,
                                       rtol=0.0, atol=1.0e-10):
                        raise ValueError("S3 descriptor initial loaded velocity is inconsistent")
            else:
                acceleration = np.asarray(spsolve(Mred, -force0)).reshape(-1)
        else:
            acceleration = resumed_acceleration
            balance = Mred @ acceleration + force0
            scale = max(1.0, float(np.linalg.norm(Mred @ acceleration)),
                        float(np.linalg.norm(force0)))
            if float(np.linalg.norm(balance)) > controls.equilibrium_tolerance*scale:
                raise ValueError("transient contact checkpoint acceleration is inconsistent")
        check_cancel("transient contact initial acceptance")
        committed_states = commit_state_candidate(committed_states, trial0)
        times = [current_time]
        positions = [full0.copy()]
        velocities = [np.asarray(T @ vred).reshape(-1)]
        accelerations = [np.asarray(T @ acceleration).reshape(-1)]
        contacts = [contact0]
        accumulated_work = (
            float(resumed_work) if resumed_work is not None
            else float(external_load @ (full0 - full_initial))
            if nodal_load_history is None else 0.0
        )
        external_work = [accumulated_work]
        swept_gaps = [contact0.minimum_gap]
        residuals = [float(np.linalg.norm(Mred @ acceleration + force0))]
        iterations = []
        path_transitions = []
        localized_events = []
        event_evaluations = 0
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
            if nodal_load_history is not None:
                knot_index = bisect_right(
                    nodal_load_history.points, (current_time, float("inf")),
                )
                next_knot = (nodal_load_history.points[knot_index][0]
                             if knot_index < len(nodal_load_history.points)
                             else transient.t_end)
                if (knot_index < len(nodal_load_history.points)
                        and next_knot-current_time < controls.minimum_dt):
                    raise ValueError(
                        "nodal load history knot is too close to the current time"
                    )
                step = min(step, next_knot-current_time)
            end_truncated = (
                remaining < transient.dt
                - 128.0*np.finfo(float).eps*max(1.0, abs(transient.t_end))
                and (nodal_load_history is None or not any(
                    transient.t_end == point[0]
                    for point in nodal_load_history.points
                ))
            )
            local_cutbacks = 0
            event_targets = ()
            event_seed = None
            event_localizations = 0
            last_event_failure = None
            while True:
                predictor = q + step * vred + step * step * (0.5 - beta) * acceleration
                velocity_predictor = vred + step * (1.0 - gamma) * acceleration
                # In the event profile iterate on acceleration as well as its
                # Newmark position. Subtracting two positions after each solve
                # amplifies endpoint roundoff by 1/h² at short event steps.
                # Always start from the same predictor, including at a requested
                # checkpoint boundary; the localized position is not a separate
                # numerical initialization for the same physical endpoint.
                candidate = predictor.copy() if controls.s3_event_subdivision_dev or event_seed is None else event_seed.copy()
                event_acceleration = np.zeros_like(candidate)
                event_seed = None
                converged = False
                requested_event_step = None
                for iteration in range(1, controls.maximum_newton_iterations + 1):
                    check_cancel("transient contact Newton evaluation")
                    full, internal, tangent, trial = evaluate(
                        candidate, current_time+step, tangent=True,
                    )
                    candidate_acceleration = (event_acceleration.copy() if controls.s3_event_subdivision_dev
                                              else (candidate - predictor) / (beta * step * step))
                    residual = Mred @ candidate_acceleration + internal
                    scale = max(1.0, float(np.linalg.norm(Mred @ candidate_acceleration)),
                                float(np.linalg.norm(internal)))
                    if float(np.linalg.norm(residual)) <= controls.equilibrium_tolerance * scale:
                        contact_result = manager.evaluate(full, tangent=False)[2]
                        candidate_velocity = velocity_predictor + gamma * step * candidate_acceleration
                        if s3_descriptor:
                            rate_touch_targets = event_targets
                            candidate_velocity, candidate_acceleration = (
                                _consistent_s3_descriptor_rates(
                                    model, T, Mred, descriptor_basis, full,
                                    candidate_velocity, candidate_acceleration,
                                    tangent, committed_states,
                                    controls.s3_descriptor_difference_step_s,
                                    one_sided_manager=(manager if controls.s3_one_sided_rates_dev else None),
                                    maximum_iterations=controls.maximum_newton_iterations,
                                    event_touch_indices=(event_targets if controls.s3_event_subdivision_dev else ()),
                                    event_gap_tolerance=controls.s3_event_gap_tolerance_m,
                                )
                            )
                        full_velocity = np.asarray(T @ candidate_velocity).reshape(-1)
                        if path_adapter is None:
                            swept_gap = _minimum_hermite_gap(
                                manager, previous_full, full,
                                previous_velocity, full_velocity, step,
                            )
                        else:
                            if (np.linalg.norm(path_adapter.endpoint_force(candidate, load_at(current_time+step))-internal)
                                    > controls.equilibrium_tolerance*scale):
                                raise ValueError("S3 reference-linear path disagrees with endpoint work")
                            candidate_path, swept_gap = path_adapter.evaluate(
                                q, candidate, vred, step, load_at(current_time),
                            )
                            path_adapter.check_endpoints(candidate_path, q, candidate, T, controls)
                            if controls.s3_event_subdivision_dev:
                                event_gaps = path_adapter.reference_gap+path_adapter.gradient @ candidate
                                start_gaps = path_adapter.reference_gap+path_adapter.gradient @ q
                                continuation = _event_continuation_segments(
                                    candidate_path,step,event_boundary_support,start_gaps,
                                    controls.s3_event_time_tolerance_s,controls.s3_event_gap_tolerance_m,
                                )
                                transitions = tuple(segment.end for segment in continuation[:-1])
                                early = tuple(s for s in transitions
                                              if (1.-s)*step > controls.s3_event_time_tolerance_s)
                                event_matches = (event_targets and np.all(
                                    np.abs(event_gaps[list(event_targets)]) <= controls.s3_event_gap_tolerance_m))
                                if transitions and (early or not event_matches):
                                    if event_localizations >= controls.maximum_event_localizations:
                                        raise RuntimeError("S3 event localization budget exhausted before commit")
                                    event_localizations += 1
                                    first, second = continuation[:2]
                                    changed = tuple(i for i,(left,right) in enumerate(zip(first.active, second.active))
                                                    if left != right)
                                    try:
                                        event = localize_branch_event(
                                            path_adapter.structural, Mred.toarray(), path_adapter.gradient,
                                            path_adapter.reference_gap, path_adapter.weights,
                                            path_adapter.force_offset, q, vred, acceleration,
                                            load_at(current_time), load_at(current_time+step), step,
                                            first.active, changed, minimum_dt=controls.minimum_dt,
                                            time_tolerance=controls.s3_event_time_tolerance_s,
                                            gap_tolerance=controls.s3_event_gap_tolerance_m,
                                            maximum_iterations=controls.maximum_event_root_iterations,
                                            check_cancel=check_cancel,
                                            null_basis=path_adapter.null_basis,
                                        )
                                    except EventNeedsCutback as exc:
                                        event_evaluations += exc.endpoint_evaluations
                                        last_event_failure = str(exc)
                                        if exc.diagnostics is not None:
                                            last_event_failure += f"; {exc.diagnostics}"
                                        break
                                    event_evaluations += event.endpoint_evaluations
                                    event_targets = event.support_indices
                                    if step-event.duration > 64*np.finfo(float).eps*step:
                                        requested_event_step = event.duration
                                        event_seed = event.position
                                        break
                                    if early:
                                        break
                                if event_targets and not np.all(
                                        np.abs(event_gaps[list(event_targets)]) <= controls.s3_event_gap_tolerance_m):
                                    raise RuntimeError("reequilibrated S3 event exceeds its dimensional gap budget")
                                if not event_targets:
                                    gap_rate = path_adapter.gradient @ candidate_velocity
                                    rate_budget = 64*np.finfo(float).eps*(np.abs(path_adapter.gradient) @ np.abs(candidate_velocity))
                                    touched = np.abs(event_gaps) <= controls.s3_event_gap_tolerance_m
                                    approaching = np.sign(start_gaps)*gap_rate < -rate_budget
                                    near_boundary = tuple(np.flatnonzero(touched & approaching
                                        & (np.abs(start_gaps) > controls.s3_event_gap_tolerance_m)).tolist())
                                    if near_boundary:
                                        if event_localizations >= controls.maximum_event_localizations:
                                            raise RuntimeError("S3 event localization budget exhausted before commit")
                                        event_localizations += 1
                                        try:
                                            boundary = localize_branch_event(
                                                path_adapter.structural,Mred.toarray(),path_adapter.gradient,
                                                path_adapter.reference_gap,path_adapter.weights,
                                                path_adapter.force_offset,q,vred,acceleration,
                                                load_at(current_time),load_at(current_time+step),step,
                                                continuation[0].active,near_boundary,
                                                minimum_dt=controls.minimum_dt,
                                                time_tolerance=controls.s3_event_time_tolerance_s,
                                                gap_tolerance=controls.s3_event_gap_tolerance_m,
                                                maximum_iterations=controls.maximum_event_root_iterations,
                                                check_cancel=check_cancel,null_basis=path_adapter.null_basis,
                                            )
                                        except EventNeedsCutback as exc:
                                            # A nearby endpoint is not a resolved event. Preserve
                                            # ordinary truncation truth when the time bracket fails.
                                            event_evaluations += exc.endpoint_evaluations
                                        else:
                                            event_evaluations += boundary.endpoint_evaluations
                                            event_targets = boundary.support_indices
                                            if step-boundary.duration > controls.s3_event_time_tolerance_s:
                                                requested_event_step = boundary.duration
                                                event_seed = boundary.position
                                                break
                        if (contact_result.gap_tolerance_met
                                and swept_gap >= -manager.gap_tolerance):
                            converged = True
                        break
                    jacobian = (Mred / (beta * step * step) + T.T @ tangent @ T).tocsr()
                    correction = np.asarray(spsolve(jacobian, -residual)).reshape(-1)
                    if not np.all(np.isfinite(correction)):
                        break
                    candidate += correction
                    if controls.s3_event_subdivision_dev:
                        event_acceleration += correction / (beta * step * step)
                    discard_active_state_candidate(committed_states)
                if requested_event_step is not None:
                    discard_active_state_candidate(committed_states)
                    step = requested_event_step
                    end_truncated = False
                    continue
                if converged:
                    if (controls.s3_event_subdivision_dev and event_targets
                            and event_targets != rate_touch_targets):
                        candidate_velocity,candidate_acceleration = _consistent_s3_descriptor_rates(
                            model,T,Mred,descriptor_basis,full,candidate_velocity,candidate_acceleration,
                            tangent,committed_states,controls.s3_descriptor_difference_step_s,
                            one_sided_manager=manager,maximum_iterations=controls.maximum_newton_iterations,
                            event_touch_indices=event_targets,
                            event_gap_tolerance=controls.s3_event_gap_tolerance_m,
                        )
                    step_work = 0.0
                    if nodal_load_history is not None:
                        start_force = (nodal_load_history.factor(current_time)
                                       * external_load)
                        end_force = (nodal_load_history.factor(current_time+step)
                                     * external_load)
                        if path_adapter is None:
                            step_work = _hermite_linear_load_work(
                                previous_full, full, previous_velocity,
                                full_velocity, start_force, end_force, step,
                            )
                        else:
                            step_work = candidate_path.linear_load_work(
                                load_at(current_time), load_at(current_time+step),
                            )
                    check_cancel("transient contact step acceptance")
                    committed_states = commit_state_candidate(committed_states, trial)
                    if controls.s3_event_subdivision_dev:
                        event_boundary_support = event_targets
                    if controls.s3_event_subdivision_dev and event_targets:
                        localized_events.append(float(current_time+step))
                        end_truncated = False
                    if path_adapter is not None:
                        for event_time in _accepted_path_transition_times(
                                last_path_active, candidate_path, current_time, step):
                            if not path_transitions or event_time != path_transitions[-1]:
                                path_transitions.append(event_time)
                        last_path_active = candidate_path.segments[-1].active
                    accumulated_work += step_work
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
                        if nodal_load_history is None:
                            # Constant dead-load path integral is exact.
                            accumulated_work = float(
                                external_load @ (full - full_initial)
                            )
                        external_work.append(accumulated_work)
                        swept_gaps.append(pending_swept_gap)
                        residuals.append(pending_residual)
                        pending_swept_gap = float("inf")
                        pending_residual = 0.0
                    iterations.append(iteration)
                    break
                discard_active_state_candidate(committed_states)
                event_targets = ()
                event_seed = None
                local_cutbacks += 1
                cutbacks += 1
                step *= 0.5
                if local_cutbacks > controls.maximum_cutbacks or step < controls.minimum_dt:
                    raise RuntimeError(
                        f"transient contact step failed at t={current_time:.9g} s "
                        f"after {local_cutbacks} cutbacks; committed state retained"
                        +(f"; event: {last_event_failure}" if last_event_failure else "")
                    )
    if emit_restart_checkpoint and (accepted_steps == 0 or last_step_was_end_truncated):
        raise ValueError(
            "transient contact checkpoint requires an accepted untruncated final time step"
        )
    check_cancel("transient contact result export")
    checkpoint = (
        _new_restart_checkpoint(
            model_fingerprint, analysis_fingerprint, current_time,
            q, vred, acceleration, accepted_steps,
            accumulated_work if nodal_load_history is not None else None,
            last_path_active if path_adapter is not None else None,
            event_boundary_support if controls.s3_event_subdivision_dev else None,
        ) if emit_restart_checkpoint else None
    )
    return TransientContactResults(
        profile, np.asarray(times), np.asarray(positions),
        np.asarray(velocities), np.asarray(accelerations), tuple(contacts),
        np.asarray(swept_gaps), np.asarray(residuals), cutbacks, tuple(iterations),
        np.asarray(external_work), checkpoint, tuple(path_transitions),
        tuple(localized_events), event_evaluations,
    )
