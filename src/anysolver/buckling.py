"""Linear eigenvalue buckling helpers.

The first production buckling path is intentionally modest: element routines
assemble a reference geometric stiffness matrix ``KG`` and this module solves
the constrained generalized problem

    K phi = lambda KG phi

Positive eigenvalues are critical load multipliers relative to the supplied
reference compression state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy import linalg
from scipy import sparse
from scipy.sparse import linalg as sparse_linalg

from .assembly import build_constraint_transformation, build_reduced_rigid_body_modes
from .cases import make_result_case
from .constraint_audit import constraint_residual_summary
from .control import CancellationToken, ProgressCallback, cancellation_safe_point, emit_progress
from .linalg import FactorizationCache, MatrixClass, cached_inverse_operator
from .matrix_assembly import (
    assemble_external_load_tangent,
    assemble_geometric_stiffness_matrix,
    assemble_stiffness_matrix,
)
from .recovery import ResourceConfig
from .threading_policy import resource_threaded

if TYPE_CHECKING:
    from .analysis_session import AnalysisSession
    from .boundary import LoadCase
    from .fe_core import FEModel


@dataclass
class BucklingMode:
    """One positive eigenvalue buckling mode."""

    mode_number: int
    load_factor: float
    eigenvalue: float
    mode_shape: np.ndarray
    reduced_mode_shape: np.ndarray
    modal_stiffness: float
    modal_geometric_stiffness: float
    residual_norm: float = 0.0
    rigid_body_correlation: float = 0.0
    validity_status: str = "ok"
    repeated_group: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode_number": self.mode_number,
            "load_factor": self.load_factor,
            "eigenvalue": self.eigenvalue,
            "modal_stiffness": self.modal_stiffness,
            "modal_geometric_stiffness": self.modal_geometric_stiffness,
            "residual_norm": self.residual_norm,
            "rigid_body_correlation": self.rigid_body_correlation,
            "validity_status": self.validity_status,
            "repeated_group": self.repeated_group,
            "mode_shape": self.mode_shape.tolist(),
        }


@dataclass
class BucklingResult:
    """Result bundle from the linear eigenvalue buckling solve."""

    modes: List[BucklingMode]
    num_modes_requested: int
    solver_status: str
    constraint_info: Dict[str, Any]
    assembly_info: Dict[str, Any]
    result_case: Optional[Dict[str, Any]] = None
    diagnostics: Optional[Dict[str, Any]] = None

    @property
    def num_modes_returned(self) -> int:
        return len(self.modes)

    @property
    def quantity_metadata(self) -> Tuple[Any, ...]:
        from .quantities import describe_result_quantities

        return describe_result_quantities(self)

    @property
    def critical_load_factor(self) -> Optional[float]:
        if not self.modes:
            return None
        return self.modes[0].load_factor

    def to_dict(self) -> Dict[str, Any]:
        return {
            "solver_status": self.solver_status,
            "num_modes_requested": self.num_modes_requested,
            "num_modes_returned": self.num_modes_returned,
            "critical_load_factor": self.critical_load_factor,
            "constraint_info": self.constraint_info,
            "assembly_info": self.assembly_info,
            "result_case": self.result_case,
            "diagnostics": self.diagnostics or {},
            "modes": [mode.to_dict() for mode in self.modes],
        }


def _as_symmetric_dense(matrix: sparse.spmatrix) -> np.ndarray:
    dense = np.asarray(matrix.toarray(), dtype=float)
    return 0.5 * (dense + dense.T)


_FLOAT64_EPS = 2.220446049250313e-16
_FLOAT64_SMALLEST_NORMAL = float(np.finfo(np.float64).tiny)
_RIGID_METRIC_VERSION = "dimensionless_full_dof_bbox_v1"


def _rank_threshold(matrix: np.ndarray) -> float:
    """Return the frozen scale-aware float64 rank threshold."""
    array = np.asarray(matrix, dtype=np.float64)
    if array.size == 0:
        return 0.0
    singular_values = np.linalg.svd(array, compute_uv=False)
    sigma_max = float(singular_values[0]) if singular_values.size else 0.0
    if sigma_max == 0.0:
        return 0.0
    return float(64.0 * max(array.shape) * _FLOAT64_EPS * sigma_max)


def _relative_frobenius_action(matrix: np.ndarray, basis: np.ndarray) -> float:
    denominator = max(float(np.linalg.norm(matrix, ord="fro")), _FLOAT64_SMALLEST_NORMAL)
    return float(np.linalg.norm(matrix @ basis, ord="fro") / denominator)


def _relative_frobenius_cross(matrix: np.ndarray, left: np.ndarray, right: np.ndarray) -> float:
    denominator = max(float(np.linalg.norm(matrix, ord="fro")), _FLOAT64_SMALLEST_NORMAL)
    return float(np.linalg.norm(left.T @ matrix @ right, ord="fro") / denominator)


def _relative_symmetry_residual(matrix: np.ndarray) -> float:
    denominator = max(float(np.linalg.norm(matrix, ord="fro")), _FLOAT64_SMALLEST_NORMAL)
    return float(np.linalg.norm(matrix - matrix.T, ord="fro") / denominator)


def _rigid_projection_diagnostics(
    *,
    applied: bool,
    characteristic_length: Optional[float],
    original_dofs: int,
    projected_dofs: Optional[int],
    rigid_rank: int,
) -> Dict[str, Any]:
    """Create the stable diagnostics schema for the rigid quotient."""
    return {
        "applied": bool(applied),
        "metric_version": _RIGID_METRIC_VERSION,
        "characteristic_length": characteristic_length,
        "original_dofs": int(original_dofs),
        "projected_dofs": None if projected_dofs is None else int(projected_dofs),
        "rigid_rank": int(rigid_rank),
        "orthonormality_residual": None,
        "elastic_null_residual": None,
        "geometric_null_residual": None,
        "elastic_cross_residual": None,
        "geometric_cross_residual": None,
        "elastic_min_eigenvalue": None,
        "elastic_max_eigenvalue": None,
        "spd_tolerance": None,
        "spd_sensitivity": {},
    }


def _normalize_mode(full_mode: np.ndarray, reduced_mode: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    scale = float(np.max(np.abs(full_mode))) if full_mode.size else 0.0
    if scale <= 0.0:
        return full_mode, reduced_mode
    return full_mode / scale, reduced_mode / scale


def _mode_residual(
    K: sparse.spmatrix,
    KG: sparse.spmatrix,
    reduced_mode: np.ndarray,
    load_factor: float,
) -> float:
    residual = np.asarray(K @ reduced_mode - float(load_factor) * (KG @ reduced_mode), dtype=float).reshape(-1)
    denominator = max(
        float(np.linalg.norm(K @ reduced_mode))
        + abs(float(load_factor)) * float(np.linalg.norm(KG @ reduced_mode)),
        1.0,
    )
    return float(np.linalg.norm(residual) / denominator)


def _factor_in_range(value: float, load_factor_range: Optional[Tuple[Optional[float], Optional[float]]]) -> bool:
    if load_factor_range is None:
        return True
    lower, upper = load_factor_range
    if lower is not None and value < float(lower):
        return False
    if upper is not None and value > float(upper):
        return False
    return True


def _sort_key(value: float, shift_load_factor: Optional[float]) -> Tuple[float, float]:
    if shift_load_factor is None:
        return (float(value), 0.0)
    return (abs(float(value) - float(shift_load_factor)), float(value))


def _assign_repeated_groups(modes: List[BucklingMode], tolerance: float) -> List[Dict[str, Any]]:
    groups: List[Dict[str, Any]] = []
    if not modes:
        return groups
    current = [modes[0]]
    group_index = 1
    for mode in modes[1:]:
        reference = current[0].load_factor
        relative = abs(mode.load_factor - reference) / max(abs(reference), 1.0)
        if relative <= tolerance:
            current.append(mode)
        else:
            if len(current) > 1:
                for item in current:
                    item.repeated_group = group_index
                groups.append(
                    {
                        "group": group_index,
                        "mode_numbers": [int(item.mode_number) for item in current],
                        "load_factors": [float(item.load_factor) for item in current],
                        "relative_spread": float(
                            (max(item.load_factor for item in current) - min(item.load_factor for item in current))
                            / max(abs(reference), 1.0)
                        ),
                    }
                )
                group_index += 1
            current = [mode]
    if len(current) > 1:
        reference = current[0].load_factor
        for item in current:
            item.repeated_group = group_index
        groups.append(
            {
                "group": group_index,
                "mode_numbers": [int(item.mode_number) for item in current],
                "load_factors": [float(item.load_factor) for item in current],
                "relative_spread": float(
                    (max(item.load_factor for item in current) - min(item.load_factor for item in current))
                    / max(abs(reference), 1.0)
                ),
            }
        )
    return groups


@resource_threaded
def solve_eigenvalue_buckling(
    model: "FEModel",
    element_states: Optional[Any] = None,
    num_modes: int = 3,
    eigen_tolerance: float = 1.0e-8,
    dense_size_limit: int = 200,
    shift_load_factor: Optional[float] = None,
    load_factor_range: Optional[Tuple[Optional[float], Optional[float]]] = None,
    search_factor: int = 4,
    repeated_tolerance: float = 1.0e-3,
    allow_dense_fallback: bool = False,
    allow_free_mechanisms: bool = False,
    factorization_cache: Optional[FactorizationCache] = None,
    reference_load_case: Optional["LoadCase"] = None,
    reference_displacements: Optional[np.ndarray] = None,
    follower_symmetry_tolerance: float = 1.0e-10,
    resource_config: Optional[ResourceConfig] = None,
    cancellation_token: Optional[CancellationToken] = None,
    progress_callback: Optional[ProgressCallback] = None,
    session: Optional["AnalysisSession"] = None,
) -> BucklingResult:
    """Solve ``K phi = lambda (KG + Kload) phi`` for positive factors.

    ``element_states`` is passed to
    :func:`anysolver.matrix_assembly.assemble_geometric_stiffness_matrix`.
    Beam elements accept axial reference compression and shell elements accept
    membrane resultant prestress (compression positive, or tension-positive
    ``membrane_forces``).

    When ``reference_load_case`` carries follower pressure, its exact
    current-area external-load stiffness is added to the destabilizing
    right-hand operator.  This symmetric eigensolver accepts that extension
    only when the *constrained* follower tangent is symmetric to
    ``follower_symmetry_tolerance`` (for example, a conservative closed
    pressure surface or boundary-restrained equivalent).  Open,
    nonconservative pressure patches require a general complex eigenanalysis
    and return an explicit unsupported status.
    """
    cancellation_safe_point(cancellation_token, "buckling.start")
    if num_modes <= 0:
        raise ValueError("num_modes must be positive")
    if follower_symmetry_tolerance < 0.0:
        raise ValueError("follower_symmetry_tolerance must be non-negative")

    # Make the solve independent of whether a caller happened to run another
    # constrained analysis first.  Rigid-mode filtering reads the active DOF
    # constraints, so boundary conditions must be applied here explicitly.
    model.apply_boundary_conditions()
    if session is None:
        K, stiffness_info = assemble_stiffness_matrix(model)
        stiffness_plan = None
    else:
        stiffness_plan = session.stiffness_plan(model)
        K = stiffness_plan.matrix
        stiffness_info = dict(stiffness_plan.info)
    KG, geometric_info = assemble_geometric_stiffness_matrix(model, element_states)
    K_load, load_tangent_info = assemble_external_load_tangent(
        model,
        reference_load_case,
        reference_displacements,
    )
    cancellation_safe_point(cancellation_token, "buckling.after_assembly")
    zero_load = np.zeros(model.mesh.dof_manager.total_dofs, dtype=float)

    if session is None:
        K_red, _, T, _, independent_dofs, constraint_info = (
            build_constraint_transformation(K, zero_load, model)
        )
        constraint_plan = None
    else:
        constraint_plan = session.constraint_plan(stiffness_plan, model)
        K_red = constraint_plan.K_red
        T = constraint_plan.T
        independent_dofs = constraint_plan.independent_dofs
        constraint_info = dict(constraint_plan.info)
    KG_red = (T.T @ KG @ T).tocsr()
    K_load_red = (T.T @ K_load @ T).tocsr()
    follower_symmetry_error = float(
        sparse.linalg.norm(K_load_red - K_load_red.T)
        / max(float(sparse.linalg.norm(K_load_red)), 1.0)
    )
    KG_red = (KG_red + K_load_red).tocsr()

    assembly_info = {
        "stiffness": stiffness_info,
        "geometric_stiffness": geometric_info,
        "external_load_tangent": load_tangent_info,
        "total_dofs": model.mesh.dof_manager.total_dofs,
        "reduced_dofs": int(K_red.shape[0]),
    }
    if session is not None:
        assembly_info["analysis_session"] = session.diagnostics()

    settings = {
        "num_modes": num_modes,
        "dense_size_limit": dense_size_limit,
        "eigen_tolerance": eigen_tolerance,
        "shift_load_factor": shift_load_factor,
        "load_factor_range": None if load_factor_range is None else list(load_factor_range),
        "search_factor": search_factor,
        "repeated_tolerance": repeated_tolerance,
        "allow_dense_fallback": allow_dense_fallback,
        "allow_free_mechanisms": allow_free_mechanisms,
        "factorization_cache": (
            (session.factorization_cache.name if session is not None else None)
            if factorization_cache is None
            else factorization_cache.name
        ),
        "reference_load_case": None if reference_load_case is None else reference_load_case.name,
        "follower_symmetry_tolerance": float(follower_symmetry_tolerance),
        "resource_config": None if resource_config is None else resource_config.to_dict(),
    }

    if follower_symmetry_error > float(follower_symmetry_tolerance):
        diagnostics = {
            "status": "unsupported_nonsymmetric_follower_pencil",
            "reason": (
                "The constrained follower-pressure load tangent is nonsymmetric; "
                "general complex nonconservative eigenanalysis is not implemented."
            ),
            "follower_tangent_symmetry_error": follower_symmetry_error,
            "follower_symmetry_tolerance": float(follower_symmetry_tolerance),
        }
        result_case = make_result_case(
            name="linear_buckling",
            analysis_type="linear_buckling",
            load_cases=() if reference_load_case is None else (reference_load_case,),
            assembly_info=assembly_info,
            solver_info={"convergence_info": diagnostics},
            recovery={"modes": num_modes},
            settings=settings,
            metadata={"prestress_state_source": "none" if element_states is None else type(element_states).__name__},
        ).to_dict()
        return BucklingResult(
            [],
            num_modes,
            "unsupported_nonsymmetric_follower_pencil",
            constraint_info,
            assembly_info,
            result_case,
            diagnostics,
        )

    if K_red.shape[0] == 0:
        diagnostics = {"status": "empty_reduced_system"}
        result_case = make_result_case(
            name="linear_buckling",
            analysis_type="linear_buckling",
            assembly_info=assembly_info,
            solver_info={"convergence_info": diagnostics},
            recovery={"modes": num_modes},
            settings=settings,
            metadata={"prestress_state_source": "none" if element_states is None else type(element_states).__name__},
        ).to_dict()
        return BucklingResult([], num_modes, "empty_reduced_system", constraint_info, assembly_info, result_case, diagnostics)
    if KG_red.nnz == 0:
        diagnostics = {"status": "zero_geometric_stiffness"}
        result_case = make_result_case(
            name="linear_buckling",
            analysis_type="linear_buckling",
            assembly_info=assembly_info,
            solver_info={"convergence_info": diagnostics},
            recovery={"modes": num_modes},
            settings=settings,
            metadata={"prestress_state_source": "none" if element_states is None else type(element_states).__name__},
        ).to_dict()
        return BucklingResult([], num_modes, "zero_geometric_stiffness", constraint_info, assembly_info, result_case, diagnostics)

    if session is None:
        Q_rigid, nullspace_info = build_reduced_rigid_body_modes(
            model,
            independent_dofs,
            int(K.shape[0]),
            transformation=T,
        )
    else:
        Q_rigid, nullspace_info = session.rigid_body_modes(constraint_plan, model)
    assembly_info["nullspace"] = nullspace_info

    # Work with the inverted symmetric pencil KG phi = mu K phi.  Constrained
    # systems without an analytic rigid space retain the existing sparse/dense
    # selection.  Free systems are first reduced to the dimensionless rigid
    # quotient so a known singular elastic pencil is never sent to an
    # eigensolver.
    n_red = int(K_red.shape[0])
    K_sym = (0.5 * (K_red + K_red.T)).tocsr()
    KG_sym = (0.5 * (KG_red + KG_red.T)).tocsr()
    k = min(max(num_modes * max(int(search_factor), 1), num_modes + 2), n_red - 1)

    eigenvectors = None
    projection_y_vectors = None
    projected_rigid_basis = None
    projection_diagnostics = None
    solver_kind = "not_started"
    sparse_error = None
    shift_invert_diagnostics: Dict[str, Any] = {"shift_invert": False}

    def _projection_failure(status: str, reason: str) -> BucklingResult:
        diagnostics = {
            "status": status,
            "reason": reason,
            "solver": "dense_scipy_eigh_rigid_quotient",
            "follower_load_stiffness_included": bool(K_load_red.nnz),
            "follower_tangent_symmetry_error": follower_symmetry_error,
            "nullspace_rank": int(Q_rigid.shape[1]),
            "nullspace_info": nullspace_info,
            "free_mechanism_handling": (
                "retained" if allow_free_mechanisms else "rigid_body_roots_filtered"
            ),
            "rigid_body_handling": "projected",
            "rigid_projection": projection_diagnostics,
        }
        result_case = make_result_case(
            name="linear_buckling",
            analysis_type="linear_buckling",
            load_cases=() if reference_load_case is None else (reference_load_case,),
            assembly_info=assembly_info,
            solver_info={"convergence_info": diagnostics},
            recovery={"modes": num_modes, "num_modes_returned": 0},
            settings=settings,
            metadata={"prestress_state_source": "none" if element_states is None else type(element_states).__name__},
        ).to_dict()
        return BucklingResult(
            [],
            num_modes,
            status,
            constraint_info,
            assembly_info,
            result_case,
            diagnostics,
        )

    if Q_rigid.shape[1]:
        coordinates = np.asarray(model.mesh.get_node_coordinates(), dtype=np.float64)
        characteristic_length: Optional[float] = None
        if coordinates.ndim == 2 and coordinates.shape[0] > 0 and coordinates.shape[1] == 3:
            coordinate_extent = np.max(coordinates, axis=0) - np.min(coordinates, axis=0)
            characteristic_length = float(np.linalg.norm(coordinate_extent))
        projection_diagnostics = _rigid_projection_diagnostics(
            applied=False,
            characteristic_length=characteristic_length,
            original_dofs=n_red,
            projected_dofs=None,
            rigid_rank=int(Q_rigid.shape[1]),
        )
        if (
            not np.all(np.isfinite(coordinates))
            or characteristic_length is None
            or not np.isfinite(characteristic_length)
            or characteristic_length <= 0.0
        ):
            return _projection_failure(
                "invalid_rigid_quotient",
                "The dimensionless rigid metric requires a finite, positive bounding-box diagonal.",
            )
        if n_red > dense_size_limit and not allow_dense_fallback:
            return _projection_failure(
                "rigid_projection_requires_dense",
                "The analytic rigid space requires the dense quotient, but dense fallback is disabled for this reduced size.",
            )

        transformation = np.asarray(T.toarray(), dtype=np.float64)
        full_scale = np.ones(transformation.shape[0], dtype=np.float64)
        for node in model.mesh.nodes.values():
            node_dofs = np.asarray(node.dofs[:3], dtype=np.intp)
            full_scale[node_dofs] = 1.0 / characteristic_length
        scaled_transformation = full_scale[:, None] * transformation
        if not (
            np.all(np.isfinite(transformation))
            and np.all(np.isfinite(scaled_transformation))
            and np.all(np.isfinite(Q_rigid))
        ):
            return _projection_failure(
                "invalid_rigid_quotient",
                "The constraint transformation or rigid basis contains non-finite values.",
            )

        _Q_transformation, R_transformation = linalg.qr(
            scaled_transformation,
            mode="economic",
            check_finite=True,
        )
        transformation_singular_values = np.linalg.svd(R_transformation, compute_uv=False)
        transformation_threshold = _rank_threshold(R_transformation)
        if (
            R_transformation.shape != (n_red, n_red)
            or transformation_singular_values.size != n_red
            or float(transformation_singular_values[-1]) <= transformation_threshold
        ):
            return _projection_failure(
                "invalid_rigid_quotient",
                "The dimensionless constraint transformation is rank deficient.",
            )

        identity = np.eye(n_red, dtype=np.float64)
        R_inverse = linalg.solve_triangular(
            R_transformation,
            identity,
            lower=False,
            check_finite=True,
        )
        K_dense = _as_symmetric_dense(K_red)
        KG_dense = _as_symmetric_dense(KG_red)
        K_y_raw = R_inverse.T @ K_dense @ R_inverse
        KG_y_raw = R_inverse.T @ KG_dense @ R_inverse
        dimension_tolerance = float(4096.0 * n_red * _FLOAT64_EPS)
        if (
            not np.all(np.isfinite(K_y_raw))
            or not np.all(np.isfinite(KG_y_raw))
            or _relative_symmetry_residual(K_y_raw) > dimension_tolerance
            or _relative_symmetry_residual(KG_y_raw) > dimension_tolerance
        ):
            return _projection_failure(
                "invalid_rigid_quotient",
                "A transformed operator is non-finite or violates the frozen symmetry residual.",
            )
        K_y = 0.5 * (K_y_raw + K_y_raw.T)
        KG_y = 0.5 * (KG_y_raw + KG_y_raw.T)

        rigid_y = R_transformation @ np.asarray(Q_rigid, dtype=np.float64)
        rigid_singular_values = np.linalg.svd(rigid_y, compute_uv=False)
        rigid_threshold = _rank_threshold(rigid_y)
        rigid_rank = int(np.count_nonzero(rigid_singular_values > rigid_threshold))
        if rigid_rank != int(Q_rigid.shape[1]):
            return _projection_failure(
                "invalid_rigid_quotient",
                "The transformed analytic rigid basis is rank deficient.",
            )
        Q_complete, _R_rigid = linalg.qr(rigid_y, mode="full", check_finite=True)
        projected_rigid_basis = np.asarray(Q_complete[:, :rigid_rank], dtype=np.float64)
        flexible_basis = np.asarray(Q_complete[:, rigid_rank:], dtype=np.float64)
        projection_diagnostics["applied"] = True
        projection_diagnostics["projected_dofs"] = int(flexible_basis.shape[1])
        if flexible_basis.shape[1] == 0:
            return _projection_failure(
                "empty_flexible_subspace",
                "The analytic rigid space spans the complete reduced system.",
            )

        orthonormality_residual = float(
            np.linalg.norm(Q_complete.T @ Q_complete - identity, ord="fro")
        )
        elastic_null_residual = _relative_frobenius_action(K_y, projected_rigid_basis)
        geometric_null_residual = _relative_frobenius_action(KG_y, projected_rigid_basis)
        elastic_cross_residual = _relative_frobenius_cross(
            K_y,
            projected_rigid_basis,
            flexible_basis,
        )
        geometric_cross_residual = _relative_frobenius_cross(
            KG_y,
            projected_rigid_basis,
            flexible_basis,
        )
        projection_diagnostics.update(
            {
                "orthonormality_residual": orthonormality_residual,
                "elastic_null_residual": elastic_null_residual,
                "geometric_null_residual": geometric_null_residual,
                "elastic_cross_residual": elastic_cross_residual,
                "geometric_cross_residual": geometric_cross_residual,
            }
        )
        if orthonormality_residual > dimension_tolerance:
            return _projection_failure(
                "invalid_rigid_quotient",
                "The complete dimensionless quotient basis is not orthonormal under the frozen residual.",
            )
        if (
            elastic_null_residual > dimension_tolerance
            or geometric_null_residual > dimension_tolerance
            or elastic_cross_residual > dimension_tolerance
            or geometric_cross_residual > dimension_tolerance
        ):
            return _projection_failure(
                "invalid_rigid_quotient",
                "The elastic or combined geometric operator does not descend to the analytic rigid quotient.",
            )

        K_f_raw = flexible_basis.T @ K_y @ flexible_basis
        KG_f_raw = flexible_basis.T @ KG_y @ flexible_basis
        if (
            _relative_symmetry_residual(K_f_raw) > dimension_tolerance
            or _relative_symmetry_residual(KG_f_raw) > dimension_tolerance
        ):
            return _projection_failure(
                "invalid_rigid_quotient",
                "A quotient operator violates the frozen symmetry residual.",
            )
        K_f = 0.5 * (K_f_raw + K_f_raw.T)
        KG_f = 0.5 * (KG_f_raw + KG_f_raw.T)
        elastic_eigenvalues = np.linalg.eigvalsh(K_f)
        elastic_minimum = float(elastic_eigenvalues[0])
        elastic_maximum = float(elastic_eigenvalues[-1])
        spd_tolerance = _rank_threshold(K_f)
        spd_sensitivity = {
            key: {
                "threshold": float(multiplier * spd_tolerance),
                "positive_definite": bool(elastic_minimum > multiplier * spd_tolerance),
            }
            for key, multiplier in (("0.25", 0.25), ("1", 1.0), ("4", 4.0))
        }
        projection_diagnostics.update(
            {
                "elastic_min_eigenvalue": elastic_minimum,
                "elastic_max_eigenvalue": elastic_maximum,
                "spd_tolerance": float(spd_tolerance),
                "spd_sensitivity": spd_sensitivity,
            }
        )
        positive_definite_values = {
            bool(item["positive_definite"])
            for item in spd_sensitivity.values()
        }
        if positive_definite_values != {True}:
            return _projection_failure(
                "singular_projected_stiffness",
                "The quotient elastic operator is not stably positive definite at all frozen sensitivity multipliers.",
            )

        try:
            _inverted_eigenvalues, flexible_eigenvectors = linalg.eigh(
                KG_f,
                K_f,
                check_finite=True,
            )
        except linalg.LinAlgError:
            return _projection_failure(
                "singular_projected_stiffness",
                "The symmetric quotient pencil rejected the verified elastic operator.",
            )
        projection_y_vectors = flexible_basis @ flexible_eigenvectors
        eigenvectors = R_inverse @ projection_y_vectors
        solver_kind = "dense_scipy_eigh_rigid_quotient"

    if not Q_rigid.shape[1] and n_red > dense_size_limit and 1 <= k < n_red:
        try:
            if shift_load_factor is None:
                _, eigenvectors = sparse_linalg.eigsh(KG_sym.tocsc(), k=k, M=K_sym.tocsc(), which="LA")
            else:
                sigma = 1.0 / float(shift_load_factor)
                shift_matrix = (KG_sym - sigma * K_sym).tocsc()
                cache = (
                    factorization_cache
                    or (session.factorization_cache if session is not None else None)
                    or FactorizationCache(name="buckling_shift_invert", max_entries=2)
                )
                operator, handle = cached_inverse_operator(
                    shift_matrix,
                    MatrixClass.SYMMETRIC_INDEFINITE,
                    cache=cache,
                )
                _, eigenvectors = sparse_linalg.eigsh(
                    KG_sym.tocsc(),
                    k=k,
                    M=K_sym.tocsc(),
                    sigma=sigma,
                    which="LM",
                    OPinv=operator,
                )
                shift_invert_diagnostics = {
                    "shift_invert": True,
                    "shift_inverse_sigma": float(sigma),
                    "shift_factorization": handle.diagnostics(),
                    "factorization_cache": cache.diagnostics(),
                }
            solver_kind = "sparse_scipy_eigsh_inverted_pencil"
        except Exception as exc:
            sparse_error = str(exc)
            eigenvectors = None
    if not Q_rigid.shape[1] and eigenvectors is None and (n_red <= dense_size_limit or allow_dense_fallback):
        K_dense = _as_symmetric_dense(K_red)
        KG_dense = _as_symmetric_dense(KG_red)
        try:
            _, eigenvectors = linalg.eigh(KG_dense, K_dense)
            solver_kind = "dense_scipy_eigh_inverted_pencil"
        except linalg.LinAlgError:
            # Singular K (e.g. unconstrained model): fall back to the general
            # nonsymmetric pencil and let the Rayleigh filtering sort it out.
            _, eigenvectors = linalg.eig(K_dense, KG_dense)
            solver_kind = "dense_scipy_eig_general_pencil"
    if eigenvectors is None:
        diagnostics = {
            "status": "failed",
            "solver": solver_kind,
            "sparse_error": sparse_error,
            "reason": "sparse eigensolve failed and dense fallback is disabled for this reduced size",
        }
        result_case = make_result_case(
            name="linear_buckling",
            analysis_type="linear_buckling",
            assembly_info=assembly_info,
            solver_info={"convergence_info": diagnostics},
            recovery={"modes": num_modes},
            settings=settings,
            metadata={"prestress_state_source": "none" if element_states is None else type(element_states).__name__},
        ).to_dict()
        return BucklingResult([], num_modes, "failed", constraint_info, assembly_info, result_case, diagnostics)

    cancellation_safe_point(cancellation_token, "buckling.after_eigensolve")

    candidates: List[tuple[float, np.ndarray, float, float, float, float]] = []
    rejected: List[Dict[str, Any]] = []
    for i in range(eigenvectors.shape[1]):
        cancellation_safe_point(
            cancellation_token,
            f"buckling.root:{i + 1}",
        )
        reduced_mode = np.asarray(np.real(eigenvectors[:, i]), dtype=float)
        mode_norm = float(np.linalg.norm(reduced_mode))
        if not np.isfinite(mode_norm) or mode_norm <= 0.0:
            rejected.append({"root_index": int(i), "reason": "invalid_or_zero_norm"})
            continue
        reduced_mode = reduced_mode / mode_norm
        if projection_y_vectors is not None:
            y_mode = np.asarray(np.real(projection_y_vectors[:, i]), dtype=np.float64)
            y_mode_norm = float(np.linalg.norm(y_mode))
            if not np.isfinite(y_mode_norm) or y_mode_norm <= 0.0:
                rejected.append({"root_index": int(i), "reason": "invalid_or_zero_dimensionless_norm"})
                continue
            y_mode = y_mode / y_mode_norm
            rigid_body_correlation = float(
                np.max(np.abs(projected_rigid_basis.T @ y_mode))
            )
        else:
            rigid_body_correlation = (
                float(np.max(np.abs(Q_rigid.T @ reduced_mode)))
                if Q_rigid.shape[1]
                else 0.0
            )
        if projection_y_vectors is None and rigid_body_correlation > 0.90 and not allow_free_mechanisms:
            rejected.append(
                {
                    "root_index": int(i),
                    "reason": "rigid_body_mode",
                    "rigid_body_correlation": rigid_body_correlation,
                }
            )
            continue
        modal_geometric = float(reduced_mode @ (KG_sym @ reduced_mode))
        modal_stiffness = float(reduced_mode @ (K_sym @ reduced_mode))
        if modal_geometric <= eigen_tolerance or modal_stiffness <= 0.0:
            rejected.append(
                {
                    "root_index": int(i),
                    "reason": "nonpositive_modal_terms",
                    "modal_stiffness": float(modal_stiffness),
                    "modal_geometric_stiffness": float(modal_geometric),
                }
            )
            continue
        rayleigh_value = modal_stiffness / modal_geometric
        if rayleigh_value <= eigen_tolerance or not np.isfinite(rayleigh_value):
            rejected.append({"root_index": int(i), "reason": "invalid_load_factor", "load_factor": float(rayleigh_value)})
            continue
        if not _factor_in_range(rayleigh_value, load_factor_range):
            rejected.append({"root_index": int(i), "reason": "outside_load_factor_range", "load_factor": float(rayleigh_value)})
            continue
        residual_norm = _mode_residual(K_sym, KG_sym, reduced_mode, rayleigh_value)
        candidates.append((rayleigh_value, reduced_mode, modal_stiffness, modal_geometric, residual_norm, rigid_body_correlation))

    candidates.sort(key=lambda item: _sort_key(item[0], shift_load_factor))
    modes: List[BucklingMode] = []
    for mode_number, (value, reduced_mode, _modal_stiffness, _modal_geometric, _residual_norm, rigid_body_correlation) in enumerate(
        candidates[:num_modes],
        start=1,
    ):
        full_mode = np.asarray(T @ reduced_mode, dtype=float).reshape(-1)
        full_mode, reduced_mode = _normalize_mode(full_mode, reduced_mode)
        modal_stiffness = float(reduced_mode @ (K_sym @ reduced_mode))
        modal_geometric = float(reduced_mode @ (KG_sym @ reduced_mode))
        residual_norm = _mode_residual(K_sym, KG_sym, reduced_mode, value)
        validity = "ok" if residual_norm <= max(1.0e-6, 100.0 * eigen_tolerance) else "high_residual"
        modes.append(
            BucklingMode(
                mode_number=mode_number,
                load_factor=float(value),
                eigenvalue=float(value),
                mode_shape=full_mode,
                reduced_mode_shape=reduced_mode,
                modal_stiffness=modal_stiffness,
                modal_geometric_stiffness=modal_geometric,
                residual_norm=residual_norm,
                rigid_body_correlation=rigid_body_correlation,
                validity_status=validity,
            )
        )

    repeated_groups = _assign_repeated_groups(modes, repeated_tolerance)
    status = "ok" if modes else "no_positive_modes"
    diagnostics = {
        "status": status,
        "solver": solver_kind,
        "follower_load_stiffness_included": bool(K_load_red.nnz),
        "follower_tangent_symmetry_error": follower_symmetry_error,
        **shift_invert_diagnostics,
        "sparse_error": sparse_error,
        "nullspace_rank": int(Q_rigid.shape[1]),
        "nullspace_info": nullspace_info,
        "free_mechanism_handling": "retained" if allow_free_mechanisms else "rigid_body_roots_filtered",
        "num_roots_considered": int(eigenvectors.shape[1]),
        "num_rejected_roots": int(len(rejected)),
        "rejected_roots": rejected[:50],
        "max_residual_norm": max((mode.residual_norm for mode in modes), default=0.0),
        "repeated_mode_groups": repeated_groups,
        "num_repeated_mode_groups": int(len(repeated_groups)),
        "sorting": "nearest_shift" if shift_load_factor is not None else "ascending_load_factor",
        "constraint_postcheck": constraint_residual_summary(
            model,
            np.column_stack([mode.mode_shape for mode in modes])
            if modes
            else np.zeros((model.mesh.dof_manager.total_dofs, 0), dtype=float),
            homogeneous_variation=True,
        ),
    }
    if projection_diagnostics is not None:
        diagnostics["rigid_body_handling"] = "projected"
        diagnostics["rigid_projection"] = projection_diagnostics
    if session is not None:
        diagnostics["analysis_session"] = session.diagnostics()
    result_case = make_result_case(
        name="linear_buckling",
        analysis_type="linear_buckling",
        load_cases=() if reference_load_case is None else (reference_load_case,),
        assembly_info=assembly_info,
        solver_info={"convergence_info": diagnostics},
        recovery={"modes": num_modes, "num_modes_returned": len(modes)},
        settings=settings,
        metadata={"prestress_state_source": "none" if element_states is None else type(element_states).__name__},
    ).to_dict()
    emit_progress(
        progress_callback,
        "buckling_complete",
        "buckling.complete",
        completed=len(modes),
        total=num_modes,
        status=status,
        num_modes_returned=len(modes),
    )
    return BucklingResult(modes, num_modes, status, constraint_info, assembly_info, result_case, diagnostics)
