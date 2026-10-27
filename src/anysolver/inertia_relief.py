"""Mass-based linear inertia relief for a single free-free beam/shell body.

Rigid accelerations use physical translations/rotations; the orthonormal
nullspace basis fixes only the elastic displacement gauge. All loads retain
the model's canonical mass and load assembly conventions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from types import SimpleNamespace
from typing import Any, Optional
import weakref

import numpy as np
from scipy import linalg, sparse
from scipy.sparse.linalg import ArpackError, ArpackNoConvergence, LinearOperator, eigsh

from .assembly import (
    _backward_error, _compute_constraint_force_diagnostics_under_lease,
    _node_components, _solve_nullspace_augmented_system,
    assemble_system, build_constraint_transformation, build_reduced_rigid_body_modes,
)
from .boundary import LoadCase
from .cases import make_result_case
from .constraint_audit import require_valid_constraints
from .control import cancellation_safe_point, emit_progress
from .elements import BeamElement, CoupledBeamShellElement, QuadraticBeamElement, ShellElement
from .element_capabilities import require_model_element_capabilities
from .fe_core import FEModel
from .mass_properties import (
    _project_rigid_inertia, _rigid_body_modes, _spatial_inertia_components,
    _validated_point_masses,
)
from .matrix_assembly import assemble_mass_matrix
from .nonlinear_state import require_no_native_total_lagrangian_elements
from .recovery_batches import _run_with_qualified_recovery_runtime_lease
from .threading_policy import resource_threaded

_ERROR_LIMIT = 1.0e-10
_ELASTIC_MARGIN = 1.0e-12
_EIGENPAIR_LIMIT = 1.0e-13
_METHOD = "linear_mass_based_inertia_relief_v1"


class InertiaReliefError(ValueError):
    """Invalid/unsupported relief input; no accepted solution was produced."""

    def __init__(self, message: str, *, code: str = "invalid_input", **details: Any):
        super().__init__(message)
        self.code = code
        self.details = details


def _readonly(values: Any) -> np.ndarray:
    made = np.array(values, dtype=float, copy=True)
    return np.frombuffer(made.tobytes(), dtype=float).reshape(made.shape)


def _mass_identity(model: FEModel) -> tuple:
    return tuple((int(k), float(v)) for k, v in sorted(model.mesh.point_masses.items()))


def _constraint_identity(model: FEModel) -> tuple:
    return tuple((e.dependent_dof, e.coefficients, e.value, e.kind, e.origin)
                 for e in require_valid_constraints(model).equations)


def _identity_token(identity: Any) -> str:
    return hashlib.sha256(repr(identity).encode("utf-8")).hexdigest()


def _json_summary(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_summary(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_summary(item) for item in value]
    if isinstance(value, np.generic):
        value = value.item()
    return None if isinstance(value, float) and not np.isfinite(value) else value


@dataclass(frozen=True)
class InertiaReliefResult:
    """Gauge-fixed elastic response and the physical loads that produced it.

    Accelerations are global Cartesian components in m/s² and rad/s². Large
    vectors are read-only result data, deliberately excluded from ``to_dict``.
    Stress/strain recovery is available through ``recover`` on a current model.
    """

    status: str
    displacements: Optional[np.ndarray] = None
    acceleration_at_reference: Optional[np.ndarray] = None
    acceleration_at_center_of_mass: Optional[np.ndarray] = None
    angular_acceleration: Optional[np.ndarray] = None
    rigid_acceleration: Optional[np.ndarray] = None
    applied_loads: Optional[np.ndarray] = None
    inertial_loads: Optional[np.ndarray] = None
    effective_loads: Optional[np.ndarray] = None
    total_mass: Optional[float] = None
    center_of_mass: Optional[np.ndarray] = None
    reference_point: Optional[np.ndarray] = None
    inertia_tensor_center_of_mass: Optional[np.ndarray] = None
    rigid_body_mass_matrix: Optional[np.ndarray] = None
    load_resultants: dict[str, Any] = field(default_factory=dict)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    constraint_forces: dict[str, Any] = field(default_factory=dict)
    solver_info: dict[str, Any] = field(default_factory=dict)
    result_case: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    _model_ref: Any = field(default=None, repr=False, compare=False)
    _revision: Any = field(default=None, repr=False, compare=False)
    _point_masses: Any = field(default=None, repr=False, compare=False)
    _constraints: Any = field(default=None, repr=False, compare=False)

    @property
    def converged(self) -> bool:
        return self.status == "converged"

    def to_dict(self) -> dict[str, Any]:
        """JSON-compatible summary; no DOF-sized vectors or live model objects."""
        arrays = ("acceleration_at_reference", "acceleration_at_center_of_mass",
                  "angular_acceleration", "center_of_mass", "reference_point",
                  "inertia_tensor_center_of_mass", "rigid_body_mass_matrix")
        return _json_summary({
            "status": self.status, "converged": self.converged, "error": self.error,
            "method": _METHOD, "total_mass": self.total_mass,
            **{name: None if getattr(self, name) is None else getattr(self, name).tolist()
               for name in arrays},
            "units": {"length": "m", "mass": "kg", "force": "N", "moment": "N m",
                      "linear_acceleration": "m/s^2", "angular_acceleration": "rad/s^2"},
            "load_resultants": self.load_resultants, "diagnostics": self.diagnostics,
            "result_case": self.result_case,
        })

    def summary(self) -> str:
        return (f"Inertia relief: {self.status}\n"
                f"Acceleration at reference [m/s^2]: {self.acceleration_at_reference}\n"
                f"Angular acceleration [rad/s^2]: {self.angular_acceleration}\n"
                f"Force balance error: {self.diagnostics.get('force_balance_error')}\n"
                f"Moment balance error: {self.diagnostics.get('moment_balance_error')}")

    def recover(self, model: Optional[FEModel] = None, *, recovery_config: Any = None,
                resource_config: Any = None) -> Any:
        """Recover physical elastic stresses using the solved, unchanged model.

        This free-free profile has no support reactions. Internal MPC forces
        are in ``constraint_forces``, evaluated against ``effective_loads``.
        """
        owned = None if self._model_ref is None else self._model_ref()
        model = owned if model is None else model
        if not self.converged or self.displacements is None:
            raise InertiaReliefError("Cannot recover a non-successful inertia-relief result",
                                     code="unaccepted_result")
        if model is None or model is not owned or model.revision_signature() != self._revision or _mass_identity(model) != self._point_masses:
            raise InertiaReliefError("Recovery requires the unchanged model used by the solve",
                                     code="stale_model")
        try:
            constraints_match = _constraint_identity(model) == self._constraints
        except (ValueError, TypeError, RuntimeError):
            constraints_match = False
        if not constraints_match:
            raise InertiaReliefError("Recovery requires unchanged model constraints", code="stale_model")
        from .results import create_fe_result
        # No load_case key: generic recovery must never reconstruct reactions
        # from the original, unbalanced external load.
        info = dict(self.solver_info)
        info.pop("load_case", None)
        return create_fe_result(model, self.displacements, info,
                                assembly_info=info.get("assembly", {}),
                                recovery_config=recovery_config,
                                resource_config=resource_config)


def _admit(model: Any, load_case: Any) -> None:
    if getattr(type(model), "_solid_model_protocol", False) or not isinstance(model, FEModel):
        raise InertiaReliefError("Inertia relief requires a beam/shell FEModel", code="unsupported_model")
    if load_case is not None and type(load_case) is not LoadCase:
        raise InertiaReliefError("Inertia relief accepts a single built-in LoadCase", code="unsupported_load")
    if load_case is not None and (load_case.follower_pressure or load_case.added_node_masses):
        raise InertiaReliefError("Follower pressure and load-case-only added masses are unsupported; attach physical masses to the model",
                                 code="unsupported_load")
    try:
        require_no_native_total_lagrangian_elements(model, context="linear inertia relief")
        require_model_element_capabilities(model, ("linear_static", "mass"), context="linear inertia relief")
        _validated_point_masses(model)
        audit = require_valid_constraints(model)
    except (ValueError, TypeError, RuntimeError) as exc:
        raise InertiaReliefError(str(exc), code="invalid_model") from exc
    if audit.fixed_dofs or not audit.homogeneous:
        raise InertiaReliefError("Inertia relief requires no physical supports and homogeneous MPCs",
                                 code="unsupported_constraints")
    if not model.mesh.nodes or not model.mesh.elements:
        raise InertiaReliefError("An inertia-relief body requires nodes and elastic elements", code="empty_model")
    components = _node_components(model)
    if len(components) != 1:
        raise InertiaReliefError("Inertia relief requires one connected body; disconnected node groups found",
                                 code="disconnected_body", node_groups=components)
    for eid, element in model.mesh.elements.items():
        if not isinstance(element, (BeamElement, ShellElement, CoupledBeamShellElement)):
            raise InertiaReliefError(f"Element {eid} has no admitted linear beam/shell profile", code="unsupported_element")
    for node in model.mesh.nodes.values():
        if (len(node.dofs) != 6 or len(set(node.dofs)) != 6
                or not all(isinstance(dof, (int, np.integer)) and not isinstance(dof, (bool, np.bool_)) for dof in node.dofs)
                or any(dof < 0 or dof >= model.mesh.dof_manager.total_dofs for dof in node.dofs)
                or not np.all(np.isfinite(node.coords()))):
            raise InertiaReliefError(f"Node {node.id} requires six DOFs and finite coordinates", code="invalid_node")
    dofs = [dof for node in model.mesh.nodes.values() for dof in node.dofs]
    if len(dofs) != model.mesh.dof_manager.total_dofs or len(set(dofs)) != len(dofs):
        raise InertiaReliefError("Node DOF mappings must cover the full system without aliases", code="invalid_node")


def _finite_symmetric(matrix: sparse.spmatrix, name: str) -> None:
    if not np.all(np.isfinite(matrix.data)):
        raise InertiaReliefError(f"{name} contains nonfinite values", code="invalid_matrix")
    difference = matrix - matrix.T
    scale = float(np.max(np.abs(matrix.data), initial=0.))
    error = float(np.max(np.abs(difference.data), initial=0.))
    if error > _ERROR_LIMIT * scale:
        raise InertiaReliefError(f"{name} is nonsymmetric", code="invalid_matrix")


def _relative(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator > 0 else (0. if numerator == 0 else float("inf"))


def _balance(R: np.ndarray, applied: np.ndarray, inertial: np.ndarray) -> tuple[dict, dict]:
    external = R.T @ applied
    inertia = R.T @ inertial
    residual = R.T @ (applied + inertial)
    # Absolute virtual-work contributions remain meaningful when resultants
    # themselves cancel, including already self-equilibrated applied loads.
    contributions = np.abs(R).T @ (np.abs(applied) + np.abs(inertial))
    errors = {}
    for name, block in (("force", slice(0, 3)), ("moment", slice(3, 6))):
        errors[name+"_balance_error"] = _relative(
            float(np.linalg.norm(residual[block])), float(np.linalg.norm(contributions[block])))
        errors[name+"_balance_absolute"] = float(np.linalg.norm(residual[block]))
        errors[name+"_balance_scale"] = float(np.linalg.norm(contributions[block]))
    resultants = {name: {"force": value[:3].tolist(), "moment": value[3:].tolist()}
                  for name, value in (("applied", external), ("inertial", inertia), ("effective", residual))}
    return resultants, errors


def _mechanism_check(K: sparse.csr_matrix, R: np.ndarray, scale: np.ndarray,
                     token: Any) -> dict[str, Any]:
    """Converged extremal Ritz pair on the scaled elastic complement.

    H=P A P+U U.T has the elastic spectrum of A and six unit eigenvalues.
    U is n-by-six; no full complement or full dense stiffness is formed.
    The lift belongs solely to this numerical classification, not the solve.
    """
    n = K.shape[0]
    if n == 6:
        return {"status": "resolved", "elastic_dimension": 0, "minimum_eigenvalue": None,
                "eigenpair_residual": 0., "iterations": 0}
    modes = R / scale[:, None]
    modes /= np.linalg.norm(modes, axis=0)
    U, _ = np.linalg.qr(modes, mode="reduced")
    rows = np.asarray(abs(K).sum(axis=1)).ravel()
    empty = np.flatnonzero(rows == 0.)
    if empty.size:
        # An MPC can make a single independent coordinate an entire rigid
        # translation. A zero row is an extra mechanism only outside span(U).
        # More than six independent zero rows cannot fit a rank-six space.
        extra = empty.tolist() if empty.size > 6 else []
        if empty.size <= 6:
            for index in empty:
                residual = -U @ U[index, :]
                residual[index] += 1.
                if np.linalg.norm(residual) > _ERROR_LIMIT:
                    extra.append(int(index))
        if extra:
            return {"status": "mechanism", "zero_stiffness_reduced_dofs": extra}
    A = sparse.diags(scale) @ K @ sparse.diags(scale)
    norm = float(np.max(np.asarray(abs(A).sum(axis=1)).ravel()))
    if not np.isfinite(norm) or norm <= 0:
        return {"status": "unresolved", "error": "No finite positive stiffness scale"}
    A = sparse.csr_matrix(A / norm)
    calls = 0

    def multiply(vector: np.ndarray) -> np.ndarray:
        nonlocal calls
        calls += 1
        cancellation_safe_point(token, "inertia_relief.mechanism_iteration")
        projected = vector - U @ (U.T @ vector)
        action = A @ projected
        return action - U @ (U.T @ action) + U @ (U.T @ vector)

    operator = LinearOperator((n, n), matvec=multiply, dtype=float)
    # Refined bodies need a larger Krylov space for clustered elastic modes.
    # This changes neither physical stiffness nor numerical acceptance gates.
    ncv = min(n, max(128, min(256, 8*int(np.sqrt(n)))))
    try:
        values, vectors = eigsh(operator, k=1, which="SA", tol=1.e-15,
                               maxiter=2000, ncv=ncv,
                               v0=np.random.default_rng(80613).normal(size=n))
    except ArpackNoConvergence:
        return {"status": "unresolved", "operator_applications": calls,
                "max_iterations": 2000, "krylov_dimension": ncv,
                "error": "Lanczos did not converge"}
    except ArpackError as exc:
        return {"status": "unresolved", "operator_applications": calls, "error": str(exc)}
    value = float(values[0])
    residual = float(np.linalg.norm(multiply(vectors[:, 0]) - value * vectors[:, 0]))
    resolved = np.isfinite(value) and residual <= _EIGENPAIR_LIMIT and value-residual > _ELASTIC_MARGIN
    return {"status": "resolved" if resolved else "unresolved", "elastic_dimension": n-6,
            "minimum_eigenvalue": value, "eigenpair_residual": residual,
            "eigenvalue_lower_margin": value-residual, "operator_applications": calls,
            "max_iterations": 2000, "krylov_dimension": ncv,
            "stiffness_scale": norm, "eigenvalue_gate": _ELASTIC_MARGIN,
            "residual_gate": _EIGENPAIR_LIMIT, "method": "scaled_projected_lanczos"}


@resource_threaded
def solve_inertia_relief(
    model: FEModel, load_case: Optional[LoadCase] = None, *, reference_point: Any = None,
    session: Any = None, resource_config: Any = None, cancellation_token: Any = None,
    progress_callback: Any = None,
) -> InertiaReliefResult:
    """Solve mass-balanced linear elasticity in a freely accelerating frame.

    Supports one connected free-free beam/shell assembly and homogeneous MPCs.
    Invalid input raises InertiaReliefError; numerical non-success has no accepted
    displacement. No time integration, centrifugal or gyroscopic terms are used.
    """
    cancellation_safe_point(cancellation_token, "inertia_relief.start")
    _admit(model, load_case)
    requested = None
    if reference_point is not None:
        try:
            requested = np.asarray(reference_point, dtype=float)
            if requested.shape != (3,) or not np.all(np.isfinite(requested)):
                raise ValueError("expected three finite coordinates")
        except (ValueError, TypeError) as exc:
            raise InertiaReliefError("reference_point requires three finite coordinates", code="invalid_reference") from exc
    emit_progress(progress_callback, "inertia_relief_started", "inertia_relief.assembly")
    try:
        if session is None:
            K, F, assembly_info = assemble_system(model, load_case)
            M, mass_info = assemble_mass_matrix(model)
            Kr, _, T, u0, independent, ci = build_constraint_transformation(K, F, model)
            constraint = SimpleNamespace(T=T, info=ci)
            Q, qi = build_reduced_rigid_body_modes(model, independent, K.shape[0], transformation=T)
        else:
            # Refresh mass first: mass invalidation may clear the operator.
            mass = session.mass_plan(model)
            M, mass_info = mass.matrix, dict(mass.info)
            K, F, assembly_info, constraint, _ = session.linear_system(load_case, model)
            Kr, T, u0, independent, ci = (constraint.K_red, constraint.T, constraint.u0,
                                         constraint.independent_dofs, dict(constraint.info))
            Q, qi = session.rigid_body_modes(constraint, model)
    except (ValueError, TypeError, NotImplementedError) as exc:
        raise InertiaReliefError(str(exc), code="assembly_input") from exc
    cancellation_safe_point(cancellation_token, "inertia_relief.after_assembly")
    for name, matrix in (("stiffness", K), ("mass", M)):
        _finite_symmetric(matrix, name)
    F = np.asarray(F, dtype=float)
    if F.shape != (K.shape[0],) or not np.all(np.isfinite(F)):
        raise InertiaReliefError("Applied load must be a finite full-DOF vector", code="invalid_load")
    if ci["num_fixed_dofs"] or np.any(u0 != 0) or Q.shape[1] != 6 or qi["constraint_compatibility_rank"] != 6:
        raise InertiaReliefError("MPCs must preserve all six free rigid-body directions", code="incompatible_constraints")
    coords = np.array([node.coords() for node in model.mesh.nodes.values()])
    centroid = coords[0] + np.mean(coords-coords[0], axis=0)
    geometric_length = float(np.sqrt(np.mean(np.sum((coords-centroid)**2, axis=1))))
    _, Gseed = _project_rigid_inertia(model, M, centroid)
    try:
        mass, first, _ = _spatial_inertia_components(
            Gseed, label="Rigid-body inertia", reference_length=geometric_length)
        if mass <= 0:
            raise ValueError("Inertia relief requires strictly positive total mass")
        center = centroid + first/mass
        R, G = _project_rigid_inertia(model, M, center)
        _, _, inertia = _spatial_inertia_components(
            G, label="Central rigid-body inertia", reference_length=geometric_length)
        length = float(np.sqrt(np.trace(inertia)/mass))
        if not np.isfinite(length) or length <= 0:
            raise ValueError("Rigid-body inertia has no positive radius of gyration")
        D = np.diag([1., 1., 1., 1./length, 1./length, 1./length])
        Gs = D.T @ G @ D / mass
        spectrum = np.linalg.eigvalsh(Gs)
        if spectrum[0] <= 6*np.finfo(float).eps*spectrum[-1]:
            raise ValueError("Rigid-body inertia is singular or numerically unresolved")
        factor = linalg.cho_factor(Gs, lower=True)
    except (ValueError, linalg.LinAlgError) as exc:
        raise InertiaReliefError(str(exc), code="invalid_rigid_inertia") from exc
    reference = center if requested is None else requested
    Rref = _rigid_body_modes(model, reference)
    _, Gref = _project_rigid_inertia(model, M, reference)
    # Centering is an exact generalized-coordinate congruence of G_ref a=p_ref,
    # not a replacement by an uncoupled approximate inertia model.
    p = R.T @ F
    rhs = D.T @ p / mass
    scaled_acceleration = linalg.cho_solve(factor, rhs)
    acceleration = D @ scaled_acceleration
    rigid_acceleration = R @ acceleration
    Fi = -np.asarray(M @ rigid_acceleration)
    effective = F + Fi
    ar = acceleration[:3] + np.cross(acceleration[3:], reference-center)
    resultants, balance = _balance(Rref, F, Fi)
    central_resultants, central_balance = _balance(R, F, Fi)
    Rr = R[np.asarray(independent), :]
    physical_scale = np.ones(K.shape[0])
    for node in model.mesh.nodes.values():
        physical_scale[node.dofs[:3]] = length
    scale = physical_scale[independent]
    columns = np.array([length, length, length, 1., 1., 1.])
    compat = np.linalg.norm((T @ Rr-R)/physical_scale[:, None]*columns) / np.linalg.norm(R/physical_scale[:, None]*columns)
    scaled_K = sparse.csr_matrix(sparse.diags(scale) @ Kr @ sparse.diags(scale))
    scaled_K_norm = float(np.max(np.asarray(abs(scaled_K).sum(axis=1)).ravel()))
    scaled_R = Rr/scale[:, None]*columns
    stiffness_error = _relative(float(np.linalg.norm(scaled_K @ scaled_R)), scaled_K_norm*float(np.linalg.norm(scaled_R)))
    acceleration_error = _backward_error(sparse.csr_matrix(Gs), scaled_acceleration, rhs)
    diagnostics = {**balance, "central_balance": central_balance,
                   "central_resultants": central_resultants,
                   "acceleration_backward_error": acceleration_error,
                   "rigid_inertia_condition": float(spectrum[-1]/spectrum[0]),
                   "rigid_mode_stiffness_error": stiffness_error,
                   "mpc_compatibility_error": float(compat), "rigid_mode_count": 6,
                   "length_scale": length, "error_gate": _ERROR_LIMIT,
                   "element_formulations": sorted({str(getattr(e, "formulation_id", type(e).__name__))
                                                   for e in model.mesh.elements.values()}),
                   "mass_formulations": sorted({("consistent" if isinstance(e, (ShellElement, QuadraticBeamElement))
                                                 or (isinstance(e, BeamElement) and (e.generalized_section is not None or e.cross_section.get("consistent_mass", False)))
                                                 else "lumped" if isinstance(e, BeamElement) else "massless_coupling")
                                                for e in model.mesh.elements.values()}),
                   "beam_mass_selection": {str(i): ("consistent" if isinstance(e, QuadraticBeamElement) or e.generalized_section is not None or e.cross_section.get("consistent_mass", False) else "lumped")
                                           for i, e in model.mesh.elements.items() if isinstance(e, BeamElement)}}
    assembly_info = {**assembly_info, "mass": mass_info}
    common = dict(acceleration_at_reference=_readonly(ar),
                  acceleration_at_center_of_mass=_readonly(acceleration[:3]),
                  angular_acceleration=_readonly(acceleration[3:]),
                  rigid_acceleration=_readonly(rigid_acceleration), applied_loads=_readonly(F),
                  inertial_loads=_readonly(Fi), effective_loads=_readonly(effective),
                  total_mass=mass, center_of_mass=_readonly(center), reference_point=_readonly(reference),
                  inertia_tensor_center_of_mass=_readonly(inertia), rigid_body_mass_matrix=_readonly(Gref),
                  load_resultants=resultants, diagnostics=diagnostics,
                  _model_ref=weakref.ref(model), _revision=model.revision_signature().copy(),
                  _point_masses=_mass_identity(model), _constraints=_constraint_identity(model))

    def finish(status: str, error: Optional[str] = None, **extra: Any) -> InertiaReliefResult:
        info = {"solver_type": "direct", "assembly": assembly_info,
                "convergence_info": {"status": status, "error": error},
                "inertia_relief": {"method": _METHOD, "diagnostics": diagnostics},
                "nullspace_info": qi, "constraint_info": ci}
        if "convergence_info" in extra:
            info["convergence_info"].update(extra.pop("convergence_info"))
            info["convergence_info"]["status"] = status
        case = make_result_case(name="inertia_relief:"+getattr(load_case, "name", "none"),
            analysis_type="inertia_relief", load_cases=() if load_case is None else (load_case,),
            assembly_info=assembly_info, solver_info=info,
            recovery={"displacements": status == "converged", "stresses": "on_demand", "reactions": "no_supports"},
            settings={"method": _METHOD, "reference_point": reference.tolist(), "error_gate": _ERROR_LIMIT},
            metadata={"status": status, "mass_formulations": diagnostics["mass_formulations"],
                      "model_revisions": common["_revision"],
                      "point_mass_identity": _identity_token(common["_point_masses"]),
                      "constraint_identity": _identity_token(common["_constraints"])})
        info["result_case"] = case.to_dict()
        cancellation_safe_point(cancellation_token, "inertia_relief.before_result")
        emit_progress(progress_callback, "inertia_relief_complete", "inertia_relief.complete", status=status)
        return InertiaReliefResult(status=status, error=error, solver_info=info,
                                   result_case=info["result_case"], **common, **extra)

    checks = [acceleration_error, float(compat), stiffness_error,
              balance["force_balance_error"], balance["moment_balance_error"],
              central_balance["force_balance_error"], central_balance["moment_balance_error"]]
    if not all(np.isfinite(v) and v <= _ERROR_LIMIT for v in checks):
        return finish("numerical_failure", "Rigid inertia, compatibility or load-balance accuracy gate failed")
    emit_progress(progress_callback, "inertia_relief_balanced", "inertia_relief.mechanism_check")
    mechanism = _mechanism_check(Kr, Rr, scale, cancellation_token)
    diagnostics["mechanism"] = mechanism
    if mechanism["status"] != "resolved":
        return finish("unresolved_elastic_stiffness", "Elastic stiffness could not be resolved at the required spectral margin and eigenpair accuracy")
    cancellation_safe_point(cancellation_token, "inertia_relief.before_factorization")
    prepared = None if session is None else session.static_operator_plan(constraint_mode="nullspace", model=model)
    Fr = np.asarray(T.T @ effective).ravel()
    # Cancel the legacy unit-valued floor in this caller's tolerance. The
    # resulting test is ||Q.T Fr|| <= 1e-10 (||F_red||+||Fi_red||), retaining
    # the existing refusal path and the prior physical force/moment gates.
    original_reduced_scale = (float(np.linalg.norm(np.asarray(T.T @ F)))
                              +float(np.linalg.norm(np.asarray(T.T @ Fi))))
    imbalance_tolerance = _ERROR_LIMIT*original_reduced_scale/max(float(np.linalg.norm(Fr)), 1.)
    q, convergence = _solve_nullspace_augmented_system(Kr, Fr, Q,
        load_imbalance_tolerance=imbalance_tolerance, prepared_operator=prepared)
    cancellation_safe_point(cancellation_token, "inertia_relief.after_factorization")
    if convergence.get("status") != "converged":
        return finish("numerical_failure", "Balanced nullspace solve failed", convergence_info=convergence)
    # Remove only roundoff in the permitted gauge; physical stiffness is unchanged.
    q = q-Q @ (Q.T @ q)
    displacement = np.asarray(T @ q).ravel()
    scaled_q = q/scale
    scaled_rhs = scale*Fr
    scaled_residual = scale*np.asarray(Kr @ q-Fr)
    # Backward error of Ku=F+F_inertia uses those original physical data,
    # not their cancellation-dominated difference. Report the latter too;
    # do not project any rigid load component out of the effective load.
    physical_load_scale = (float(np.linalg.norm(scale*np.asarray(T.T @ F).ravel(), ord=np.inf))
                           +float(np.linalg.norm(scale*np.asarray(T.T @ Fi).ravel(), ord=np.inf)))
    elastic_error = _relative(float(np.linalg.norm(scaled_residual, ord=np.inf)),
        scaled_K_norm*float(np.linalg.norm(scaled_q, ord=np.inf))+physical_load_scale)
    effective_error = _backward_error(scaled_K, scaled_q, scaled_rhs)
    cancellation_ratio = _relative(float(np.linalg.norm(scaled_rhs, ord=np.inf)), physical_load_scale)
    augmented = sparse.bmat([[Kr, sparse.csr_matrix(Q)], [sparse.csr_matrix(Q.T), sparse.csr_matrix((6, 6))]], format="csr")
    multipliers = np.asarray(convergence["rigid_body_lagrange_multipliers"])
    augmented_error = _backward_error(augmented, np.r_[q, multipliers], np.r_[Fr, np.zeros(6)])
    gauge = _relative(float(np.linalg.norm(Q.T @ q)), float(np.linalg.norm(q)))
    diagnostics.update(elastic_backward_error=elastic_error, augmented_backward_error=augmented_error,
                       effective_load_relative_backward_error=effective_error,
                       elastic_backward_error_normalization="scaled_K_u_applied_plus_inertial",
                       elastic_load_cancellation_ratio=cancellation_ratio,
                       elastic_accuracy_reference="applied_plus_inertial_loads",
                       gauge_error=gauge, backend=convergence.get("backend", {}),
                       reduced_equilibrium_residual_norm=float(np.linalg.norm(Kr @ q-Fr)))
    if not all(np.isfinite(v) and v <= _ERROR_LIMIT for v in (elastic_error, augmented_error, gauge)):
        return finish("numerical_failure", "Elastic equilibrium or gauge accuracy gate failed", convergence_info=convergence)
    cancellation_safe_point(cancellation_token, "inertia_relief.before_recovery")
    constraint_forces = _run_with_qualified_recovery_runtime_lease(model,
        context="inertia-relief effective-load constraint diagnostics",
        operation=lambda guard: _compute_constraint_force_diagnostics_under_lease(
            model, displacement, qualified_runtime_guard=guard,
            prepared_system=(K, effective, constraint, Q, qi)))
    return finish("converged", displacements=_readonly(displacement),
                  constraint_forces=constraint_forces, convergence_info=convergence)
