"""Sparse/dense free-vibration modal analysis."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import linalg, sparse
from scipy.sparse import linalg as sparse_linalg

from .assembly import build_constraint_transformation, build_reduced_rigid_body_modes
from .algebraic_dynamics import (
    AlgebraicDynamicsError,
    DESCRIPTOR_MODAL_POLICY_ID,
    build_declared_algebraic_basis,
    declared_algebraic_mass_elements,
    solve_descriptor_spectrum,
)
from .cases import make_result_case
from .constraint_audit import constraint_residual_summary
from .control import CancellationToken, ProgressCallback, cancellation_safe_point, emit_progress
from .element_capabilities import require_model_element_capabilities
from .linalg import FactorizationCache, MatrixClass, cached_inverse_operator
from .matrix_assembly import (
    assemble_geometric_stiffness_matrix,
    assemble_mass_matrix,
    assemble_stiffness_matrix,
)
from .recovery import ResourceConfig
from .threading_policy import resource_threaded, thread_policy_diagnostics

if TYPE_CHECKING:
    from .analysis_session import AnalysisSession
    from .fe_core import FEModel


PRESTRESSED_MODAL_POLICY_ID = (
    "MATERIAL_TANGENT_MINUS_COMPRESSION_POSITIVE_GEOMETRIC_V1"
)
CURRENT_STATE_MODAL_POLICY_ID = (
    "COMMITTED_NATIVE_TOTAL_TANGENT_WITH_REFERENCE_CONSISTENT_MASS_V1"
)


def _assemble_committed_current_tangent(
    model: "FEModel",
    displacements: Any,
    element_states: Any,
    num_layers: int,
) -> tuple[sparse.csr_matrix, Dict[str, Any]]:
    """Evaluate one read-only zero-increment committed nonlinear tangent."""

    full = np.asarray(displacements, dtype=np.float64)
    total_dofs = int(model.mesh.dof_manager.total_dofs)
    if full.shape != (total_dofs,) or not np.all(np.isfinite(full)):
        raise ValueError(
            "current-state modal analysis requires the complete finite "
            "committed displacement vector"
        )
    if not isinstance(element_states, Mapping):
        raise TypeError(
            "current-state modal analysis requires an element-state mapping"
        )
    if isinstance(num_layers, (bool, np.bool_)) or not isinstance(
        num_layers, (int, np.integer)
    ) or int(num_layers) <= 0:
        raise ValueError("current_state_num_layers must be a positive integer")

    from .nonlinear_state import (
        NonlinearStateStore,
        create_model_native_rotation_store,
        discard_active_state_candidate,
    )

    store = NonlinearStateStore.from_shell_layouts((), element_states)
    rotation_store = create_model_native_rotation_store(model, store, full)
    if rotation_store is not None:
        store.attach_native_rotation_store(rotation_store)
    try:
        from .nonlinear_static import _assemble_nonlinear_system

        _force, tangent, _candidate = _assemble_nonlinear_system(
            model,
            full,
            store,
            int(num_layers),
            tangent=True,
            kinematics="von_karman",
            require_full_coordinates=True,
        )
    finally:
        discard_active_state_candidate(store)
    if tangent is None:
        raise ValueError("current-state nonlinear assembly returned no tangent")
    made = sparse.csr_matrix(tangent, dtype=float)
    if made.shape != (total_dofs, total_dofs) or np.any(~np.isfinite(made.data)):
        raise ValueError("current-state nonlinear tangent is incompatible")
    skew = made - made.T
    tangent_norm = max(float(sparse_linalg.norm(made)), 1.0)
    relative_skew = float(sparse_linalg.norm(skew) / tangent_norm)
    skew_limit = 512.0 * np.finfo(np.float64).eps
    if relative_skew > skew_limit:
        raise ValueError(
            "current-state nonlinear tangent is not symmetric within its "
            "binary64 assembly bound"
        )
    made = (0.5 * (made + made.T)).tocsr()
    state_digests = {
        str(int(element_id)): str(
            state.get(
                "state_digest",
                state.get("state_integrity_sha256", ""),
            )
        )
        for element_id, state in sorted(
            element_states.items(), key=lambda item: int(item[0])
        )
        if isinstance(state, Mapping)
        and (
            "state_digest" in state
            or "state_integrity_sha256" in state
        )
    }
    return made, {
        "matrix_type": "committed_nonlinear_tangent",
        "policy_id": CURRENT_STATE_MODAL_POLICY_ID,
        "relative_symmetry_error": relative_skew,
        "state_digests": state_digests,
        "state_storage": store.diagnostics(),
    }


@dataclass
class ModalMode:
    """One free-vibration mode."""

    mode_number: int
    eigenvalue: float
    angular_frequency: float
    frequency_hz: float
    period: Optional[float]
    mode_shape: np.ndarray
    reduced_mode_shape: np.ndarray
    modal_mass: float
    modal_stiffness: float
    residual_norm: float
    rigid_body_correlation: float
    is_rigid_body: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode_number": int(self.mode_number),
            "eigenvalue": float(self.eigenvalue),
            "angular_frequency": float(self.angular_frequency),
            "frequency_hz": float(self.frequency_hz),
            "period": None if self.period is None else float(self.period),
            "mode_shape": self.mode_shape.tolist(),
            "modal_mass": float(self.modal_mass),
            "modal_stiffness": float(self.modal_stiffness),
            "residual_norm": float(self.residual_norm),
            "rigid_body_correlation": float(self.rigid_body_correlation),
            "is_rigid_body": bool(self.is_rigid_body),
        }


@dataclass
class ModalResult:
    """Result bundle from modal analysis."""

    modes: List[ModalMode]
    num_modes_requested: int
    solver_status: str
    constraint_info: Dict[str, Any]
    nullspace_info: Dict[str, Any]
    assembly_info: Dict[str, Any]
    diagnostics: Dict[str, Any]
    result_case: Optional[Dict[str, Any]] = None

    @property
    def num_modes_returned(self) -> int:
        return len(self.modes)

    @property
    def quantity_metadata(self) -> Tuple[Any, ...]:
        from .quantities import describe_result_quantities

        return describe_result_quantities(self)

    @property
    def frequencies_hz(self) -> np.ndarray:
        return np.asarray([mode.frequency_hz for mode in self.modes], dtype=float)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "solver_status": self.solver_status,
            "num_modes_requested": int(self.num_modes_requested),
            "num_modes_returned": int(self.num_modes_returned),
            "frequencies_hz": self.frequencies_hz.tolist(),
            "constraint_info": self.constraint_info,
            "nullspace_info": self.nullspace_info,
            "assembly_info": self.assembly_info,
            "diagnostics": self.diagnostics,
            "result_case": self.result_case,
            "modes": [mode.to_dict() for mode in self.modes],
        }


def _sym(matrix: sparse.spmatrix) -> sparse.csr_matrix:
    return (0.5 * (matrix + matrix.T)).tocsr()


def _dense_eigensolve(K: sparse.spmatrix, M: sparse.spmatrix) -> Tuple[np.ndarray, np.ndarray]:
    Kd = np.asarray(K.toarray(), dtype=float)
    Md = np.asarray(M.toarray(), dtype=float)
    Kd = 0.5 * (Kd + Kd.T)
    Md = 0.5 * (Md + Md.T)
    return linalg.eigh(Kd, Md)


def _sparse_eigensolve(
    K: sparse.spmatrix,
    M: sparse.spmatrix,
    num_modes: int,
    shift: Optional[float],
    factorization_cache: Optional[FactorizationCache] = None,
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    n = int(K.shape[0])
    k = min(max(num_modes + 4, num_modes), n - 1)
    if shift is None:
        values, vectors = sparse_linalg.eigsh(K.tocsc(), k=k, M=M.tocsc(), which="SM")
        return values, vectors, {"shift_invert": False}
    shift_matrix = (K - float(shift) * M).tocsc()
    cache = factorization_cache or FactorizationCache(name="modal_shift_invert", max_entries=2)
    operator, handle = cached_inverse_operator(
        shift_matrix,
        MatrixClass.SYMMETRIC_INDEFINITE,
        cache=cache,
    )
    values, vectors = sparse_linalg.eigsh(K.tocsc(), k=k, M=M.tocsc(), sigma=float(shift), which="LM", OPinv=operator)
    return values, vectors, {
        "shift_invert": True,
        "shift_factorization": handle.diagnostics(),
        "factorization_cache": cache.diagnostics(),
    }


def _deterministic_sign(vector: np.ndarray) -> np.ndarray:
    idx = int(np.argmax(np.abs(vector))) if vector.size else 0
    if vector.size and vector[idx] < 0.0:
        return -vector
    return vector


def _orthogonality_error(modes: List[ModalMode], M_red: sparse.spmatrix) -> float:
    if not modes:
        return 0.0
    Phi = np.column_stack([mode.reduced_mode_shape for mode in modes])
    gram = np.asarray(Phi.T @ (M_red @ Phi), dtype=float)
    return float(np.max(np.abs(gram - np.eye(gram.shape[0]))))


@resource_threaded
def solve_free_vibration(
    model: "FEModel",
    num_modes: int = 6,
    shift: Optional[float] = None,
    dense_size_limit: int = 200,
    eigen_tolerance: float = 1.0e-9,
    rigid_body_frequency_tolerance: float = 1.0e-6,
    factorization_cache: Optional[FactorizationCache] = None,
    resource_config: Optional[ResourceConfig] = None,
    cancellation_token: Optional[CancellationToken] = None,
    progress_callback: Optional[ProgressCallback] = None,
    session: Optional["AnalysisSession"] = None,
    prestress_states: Optional[Any] = None,
    current_state_displacements: Optional[Any] = None,
    current_state_element_states: Optional[Any] = None,
    current_state_num_layers: int = 5,
) -> ModalResult:
    """Solve ``K phi = omega^2 M phi`` with the common constraint transform.

    ``prestress_states`` activates the stress-stiffened tangent
    ``K_material - K_G``.  ``K_G`` uses the same compression-positive
    convention as linear buckling.  Element operators own bubble/internal
    condensation; this solver only assembles their final nodal matrices.

    ``current_state_displacements`` plus ``current_state_element_states``
    instead evaluate the formulation-native committed total tangent through
    a read-only zero-increment state transaction.  That path retains the
    current material, geometric, bubble-Schur and objective-PL tangent while
    continuing to use the formulation's consistent reference mass.
    """
    cancellation_safe_point(cancellation_token, "modal.start")
    if num_modes <= 0:
        raise ValueError("num_modes must be positive")
    current_state = (
        current_state_displacements is not None
        or current_state_element_states is not None
    )
    if (current_state_displacements is None) != (
        current_state_element_states is None
    ):
        raise ValueError(
            "current-state modal analysis requires both committed "
            "displacements and element states"
        )
    if current_state and prestress_states is not None:
        raise ValueError(
            "current-state modal tangent and reference-elastic prestress_states "
            "are mutually exclusive"
        )
    if current_state:
        require_model_element_capabilities(
            model,
            "current_state_modal",
            context="solve_free_vibration",
        )
    if prestress_states is not None:
        require_model_element_capabilities(
            model,
            "reference_elastic_prestressed_modal",
            context="solve_free_vibration",
        )
    model.apply_boundary_conditions()
    current_state_info = None
    if session is None or current_state:
        if current_state:
            K, current_state_info = _assemble_committed_current_tangent(
                model,
                current_state_displacements,
                current_state_element_states,
                current_state_num_layers,
            )
            stiffness_info = dict(current_state_info)
        else:
            K, stiffness_info = assemble_stiffness_matrix(model)
        M, mass_info = assemble_mass_matrix(model)
        geometric_info = None
        if prestress_states is not None:
            geometric, geometric_info = assemble_geometric_stiffness_matrix(
                model, prestress_states
            )
            K = (K - geometric).tocsr()
        zero = np.zeros(model.mesh.dof_manager.total_dofs, dtype=float)
        K_red, _, T, _, independent_dofs, constraint_info = (
            build_constraint_transformation(K, zero, model)
        )
        M_red = (T.T @ M @ T).tocsr()
        Q, nullspace_info = build_reduced_rigid_body_modes(
            model,
            independent_dofs,
            int(K.shape[0]),
            transformation=T,
        )
    else:
        stiffness_plan = session.stiffness_plan(model)
        constraint_plan = session.constraint_plan(stiffness_plan, model)
        mass_plan = session.mass_plan(model)
        K = stiffness_plan.matrix
        M = mass_plan.matrix
        stiffness_info = dict(stiffness_plan.info)
        mass_info = dict(mass_plan.info)
        geometric_info = None
        if prestress_states is None:
            K_red = constraint_plan.K_red
        else:
            geometric, geometric_info = assemble_geometric_stiffness_matrix(
                model, prestress_states
            )
            K = (K - geometric).tocsr()
            K_red = (constraint_plan.T.T @ K @ constraint_plan.T).tocsr()
        M_red, _ = session.reduced_mass(constraint_plan, model)
        T = constraint_plan.T
        independent_dofs = constraint_plan.independent_dofs
        constraint_info = dict(constraint_plan.info)
        Q, nullspace_info = session.rigid_body_modes(constraint_plan, model)
    cancellation_safe_point(cancellation_token, "modal.after_assembly")

    assembly_info = {
        "stiffness": stiffness_info,
        "mass": mass_info,
        "total_dofs": model.mesh.dof_manager.total_dofs,
        "reduced_dofs": int(K_red.shape[0]),
    }
    if geometric_info is not None:
        assembly_info["geometric_stiffness"] = geometric_info
        assembly_info["prestressed_modal_policy_id"] = (
            PRESTRESSED_MODAL_POLICY_ID
        )
    if current_state_info is not None:
        assembly_info["current_state_tangent"] = current_state_info
        assembly_info["current_state_modal_policy_id"] = (
            CURRENT_STATE_MODAL_POLICY_ID
        )
        if session is not None:
            assembly_info["analysis_session_bypass_reason"] = (
                "committed_current_state_tangent_is_not_cacheable"
            )
    if session is not None:
        assembly_info["analysis_session"] = session.diagnostics()
    settings = {
        "num_modes": int(num_modes),
        "shift": None if shift is None else float(shift),
        "dense_size_limit": int(dense_size_limit),
        "eigen_tolerance": float(eigen_tolerance),
        "rigid_body_frequency_tolerance": float(rigid_body_frequency_tolerance),
        "factorization_cache": (
            (session.factorization_cache.name if session is not None else None)
            if factorization_cache is None
            else factorization_cache.name
        ),
        "resource_config": None if resource_config is None else resource_config.to_dict(),
    }
    if prestress_states is not None:
        settings.update(
            {
                "prestress_state_source": type(prestress_states).__name__,
                "prestressed_modal_policy_id": PRESTRESSED_MODAL_POLICY_ID,
            }
        )
    if current_state:
        settings.update(
            {
                "current_state_modal_policy_id": CURRENT_STATE_MODAL_POLICY_ID,
                "current_state_num_layers": int(current_state_num_layers),
            }
        )
    descriptor_formulations = [
        {
            "element_id": int(element_id),
            "formulation_id": str(getattr(element, "formulation_id", "")),
            "algebraic_coordinate_policy": str(
                getattr(element, "dynamic_algebraic_policy", "")
            ),
        }
        for element_id, element in sorted(model.mesh.elements.items())
        if str(getattr(element, "dynamic_algebraic_policy", ""))
    ]

    if K_red.shape[0] == 0:
        diagnostics = {"status": "empty_reduced_system"}
        result_case = make_result_case(
            name="modal",
            analysis_type="modal",
            assembly_info=assembly_info,
            solver_info={"convergence_info": diagnostics},
            recovery={"modes": num_modes},
            settings=settings,
            metadata=(
                {
                    "descriptor_modal_provenance": {
                        "policy_id": DESCRIPTOR_MODAL_POLICY_ID,
                        "elements": descriptor_formulations,
                    }
                }
                if descriptor_formulations
                else None
            ),
        ).to_dict()
        return ModalResult([], num_modes, "empty_reduced_system", constraint_info, nullspace_info, assembly_info, diagnostics, result_case)

    K_sym = _sym(K_red)
    M_sym = _sym(M_red)
    n_red = int(K_sym.shape[0])
    descriptor_elements: Tuple[int, ...] = ()
    descriptor_modal = False
    descriptor_certificate = None
    try:
        sparse_diagnostics: Dict[str, Any] = {}
        descriptor_elements = declared_algebraic_mass_elements(model)
        descriptor_modal = bool(descriptor_elements)
        if descriptor_modal:
            descriptor_basis = build_declared_algebraic_basis(
                model,
                M,
                M_sym,
                T,
                independent_dofs,
                dense_size_limit=dense_size_limit,
            )
            descriptor_certificate = descriptor_basis.diagnostics
            descriptor = solve_descriptor_spectrum(
                K_sym,
                M_sym,
                num_modes=num_modes,
                dense_size_limit=dense_size_limit,
                algebraic_nullity=int(descriptor_basis.reduced_basis.shape[1]),
                algebraic_basis=descriptor_basis.reduced_basis,
                target_shift=shift,
                factorization_cache=(
                    factorization_cache
                    or (session.factorization_cache if session is not None else None)
                ),
            )
            eigenvalues = descriptor.eigenvalues
            eigenvectors = descriptor.eigenvectors
            sparse_diagnostics = dict(descriptor.diagnostics)
            sparse_diagnostics["declared_algebraic_element_ids"] = list(
                descriptor_elements
            )
            sparse_diagnostics["declared_algebraic_formulations"] = (
                descriptor_formulations
            )
            sparse_diagnostics["declared_algebraic_mass_certificate"] = (
                descriptor_certificate
            )
            solver_kind = str(descriptor.diagnostics["solver"])
        elif n_red <= dense_size_limit or n_red <= num_modes + 1:
            eigenvalues, eigenvectors = _dense_eigensolve(K_sym, M_sym)
            solver_kind = "dense_scipy_eigh"
        else:
            eigenvalues, eigenvectors, sparse_diagnostics = _sparse_eigensolve(
                K_sym,
                M_sym,
                num_modes,
                shift,
                factorization_cache=(
                    factorization_cache
                    or (session.factorization_cache if session is not None else None)
                ),
            )
            solver_kind = "sparse_scipy_eigsh"
    except Exception as exc:
        diagnostics = {
            "status": "failed",
            "error": str(exc),
            "error_type": type(exc).__name__,
        }
        if isinstance(exc, AlgebraicDynamicsError):
            diagnostics.update(
                {
                    "error_code": "ALGEBRAIC_DESCRIPTOR_INVALID",
                    "policy_id": DESCRIPTOR_MODAL_POLICY_ID,
                    "declared_algebraic_element_ids": list(descriptor_elements),
                    "declared_algebraic_formulations": descriptor_formulations,
                }
            )
        result_case = make_result_case(
            name="modal",
            analysis_type="modal",
            assembly_info=assembly_info,
            solver_info={"convergence_info": diagnostics},
            recovery={"modes": num_modes},
            settings=settings,
            metadata=(
                {
                    "descriptor_modal_provenance": {
                        "policy_id": DESCRIPTOR_MODAL_POLICY_ID,
                        "elements": descriptor_formulations,
                    }
                }
                if descriptor_formulations
                else None
            ),
        ).to_dict()
        return ModalResult([], num_modes, "failed", constraint_info, nullspace_info, assembly_info, diagnostics, result_case)

    cancellation_safe_point(cancellation_token, "modal.after_eigensolve")

    order = np.argsort(np.real(eigenvalues))
    eigenvalues = np.real(eigenvalues[order])
    eigenvectors = np.real(eigenvectors[:, order])
    stiffness_operator_norm = (
        float(sparse_linalg.norm(K_sym)) if descriptor_modal else 0.0
    )
    mass_operator_norm = float(sparse_linalg.norm(M_sym)) if descriptor_modal else 0.0
    if descriptor_modal and Q.shape[1]:
        mass_times_rigid = np.asarray(M_sym @ Q, dtype=float)
        rigid_mass_gram = np.asarray(Q.T @ mass_times_rigid, dtype=float)
        rigid_mass_inverse = np.linalg.pinv(
            0.5 * (rigid_mass_gram + rigid_mass_gram.T), rcond=1.0e-12
        )
    else:
        mass_times_rigid = np.zeros((n_red, 0), dtype=float)
        rigid_mass_inverse = np.zeros((0, 0), dtype=float)

    modes: List[ModalMode] = []
    descriptor_backward_errors: List[float] = []
    for value, vector in zip(eigenvalues, eigenvectors.T):
        cancellation_safe_point(
            cancellation_token,
            f"modal.recovery:{len(modes) + 1}",
        )
        if len(modes) >= num_modes:
            break
        if not np.isfinite(value):
            continue
        reduced = np.asarray(vector, dtype=float).reshape(-1)
        modal_mass = float(reduced @ (M_sym @ reduced))
        if modal_mass <= eigen_tolerance:
            continue
        reduced = reduced / np.sqrt(modal_mass)
        reduced = _deterministic_sign(reduced)
        modal_mass = float(reduced @ (M_sym @ reduced))
        raw_modal_stiffness = float(reduced @ (K_sym @ reduced))
        if descriptor_modal:
            # The descriptor solver may obtain the certified finite value from
            # a statically condensed quotient.  Recomputing x^T K x in a
            # strongly sheared algebraic coordinate system can catastrophically
            # cancel even when the full residual is at componentwise roundoff.
            modal_stiffness = float(value)
        else:
            modal_stiffness = raw_modal_stiffness
        eig = (
            float(modal_stiffness)
            if descriptor_modal
            else (
                max(float(value), 0.0)
                if abs(float(value)) <= eigen_tolerance
                else float(value)
            )
        )
        reduced_norm = float(np.linalg.norm(reduced))
        if descriptor_modal:
            if Q.shape[1]:
                coefficients = rigid_mass_inverse @ (mass_times_rigid.T @ reduced)
                projected = Q @ coefficients
                projected_mass = float(projected @ (M_sym @ projected))
                rigid_corr = float(
                    np.sqrt(max(projected_mass, 0.0) / max(modal_mass, np.finfo(float).tiny))
                )
            else:
                rigid_corr = 0.0
            rigid_corr = min(max(rigid_corr, 0.0), 1.0)
        else:
            # Preserve the established Q4/legacy/beam result semantics exactly.
            rigid_corr = float(np.max(np.abs(Q.T @ reduced))) if Q.shape[1] else 0.0
        omega = float(np.sqrt(max(eig, 0.0)))
        frequency = omega / (2.0 * np.pi)
        residual = np.asarray(K_sym @ reduced - eig * (M_sym @ reduced), dtype=float).reshape(-1)
        denominator = max(
            float(np.linalg.norm(K_sym @ reduced))
            + abs(eig) * float(np.linalg.norm(M_sym @ reduced)),
            1.0,
        )
        if descriptor_modal:
            backward_denominator = max(
                (stiffness_operator_norm + abs(eig) * mass_operator_norm)
                * reduced_norm,
                1.0,
            )
            descriptor_backward_errors.append(
                float(np.linalg.norm(residual) / backward_denominator)
            )
        residual_norm = float(np.linalg.norm(residual) / denominator)
        is_rigid = bool(frequency <= rigid_body_frequency_tolerance or rigid_corr > 0.90)
        full = np.asarray(T @ reduced, dtype=float).reshape(-1)
        modes.append(
            ModalMode(
                mode_number=len(modes) + 1,
                eigenvalue=eig,
                angular_frequency=omega,
                frequency_hz=frequency,
                period=None if frequency <= 0.0 else 1.0 / frequency,
                mode_shape=full,
                reduced_mode_shape=reduced,
                modal_mass=modal_mass,
                modal_stiffness=modal_stiffness,
                residual_norm=residual_norm,
                rigid_body_correlation=rigid_corr,
                is_rigid_body=is_rigid,
            )
        )

    status = "ok" if modes else "no_modes"
    diagnostics = {
        "status": status,
        "thread_policy": thread_policy_diagnostics(resource_config),
        "solver": solver_kind,
        **sparse_diagnostics,
        "max_residual_norm": max((mode.residual_norm for mode in modes), default=0.0),
        "mass_orthogonality_error": _orthogonality_error(modes, M_sym),
        "num_rigid_body_modes": int(sum(1 for mode in modes if mode.is_rigid_body)),
        "constraint_postcheck": constraint_residual_summary(
            model,
            np.column_stack([mode.mode_shape for mode in modes])
            if modes
            else np.zeros((model.mesh.dof_manager.total_dofs, 0), dtype=float),
            homogeneous_variation=True,
        ),
    }
    if descriptor_modal:
        diagnostics["descriptor_modal"] = True
        diagnostics["max_normwise_backward_error"] = max(
            descriptor_backward_errors, default=0.0
        )
    if session is not None:
        diagnostics["analysis_session"] = session.diagnostics()
    result_case = make_result_case(
        name="modal",
        analysis_type="modal",
        assembly_info=assembly_info,
        solver_info={"convergence_info": diagnostics},
        recovery={"modes": num_modes, "num_modes_returned": len(modes)},
        settings=settings,
        metadata=(
            {
                "descriptor_modal_provenance": {
                    "policy_id": DESCRIPTOR_MODAL_POLICY_ID,
                    "elements": descriptor_formulations,
                }
            }
            if descriptor_modal
            else None
        ),
    ).to_dict()
    emit_progress(
        progress_callback,
        "modal_complete",
        "modal.complete",
        completed=len(modes),
        total=num_modes,
        status=status,
        num_modes_returned=len(modes),
    )
    return ModalResult(modes, num_modes, status, constraint_info, nullspace_info, assembly_info, diagnostics, result_case)
