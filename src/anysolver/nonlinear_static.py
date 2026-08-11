"""Incremental Newton-Raphson solver with geometric and material nonlinearity.

Geometric nonlinearity: total-Lagrangian von Karman kinematics in the shell
elements (membrane-bending coupling from transverse-deflection gradients,
initial-stress stiffness from the current membrane resultants) and a
consistent beam-column axial coupling in the 2-node beam.

Material nonlinearity: layered J2 plane-stress plasticity in the shells with
the isotropic hardening curve attached to the material
(``Material.hardening_curve``, e.g. a DNV-RP-C208 curve from
:mod:`anysolver.material_curves`).  Materials without a curve stay elastic.

Solution strategy (chosen for speed):

* full Newton-Raphson per load increment (quadratic-ish convergence, one
  sparse factorization per iteration),
* vectorized element kernels with cached reference geometry,
* COO-triplet assembly of tangent and internal force in a single element loop,
* adaptive load stepping: the increment halves on non-convergence and grows
  again after fast steps, so the run survives limit points gracefully and
  reports the last converged load factor as the capacity estimate.

The external load is ``F = F_constant + lambda * F_proportional`` so dead
loads or imperfection loads can be held while the proportional part ramps.
"""

from __future__ import annotations

import copy
import os
import time
from dataclasses import dataclass, field, replace as dataclass_replace
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple, Union

import numpy as np
from scipy import sparse

from .assembly import build_constraint_transformation
from .cases import make_result_case
from .constraint_audit import constraint_residual_summary
from .control import (
    CancellationToken,
    ProgressCallback,
    cancellation_safe_point,
    emit_progress,
)
from .fracture import (
    DeletedElementRecord,
    FractureConfig,
    detect_new_deletions,
    deleted_pressure_load_resultant,
    element_fracture_category,
    filtered_load_case_for_deleted_elements,
    fracture_summary,
    mpc_warning_for_deleted_shells,
)
from .linalg import MatrixClass, factorize
from .jit_compiler import numba_thread_scope
from .matrix_assembly import (
    _scatter_element_matrix,
    _triplets_to_csr,
    assemble_external_load_system,
    assemble_load_vector,
    assemble_stiffness_matrix,
)
from .recovery import ResourceConfig
from .threading_policy import resource_threaded, thread_policy_diagnostics

if TYPE_CHECKING:
    from .boundary import LoadCase
    from .fe_core import FEModel


_DOF_INDEX = {"ux": 0, "uy": 1, "uz": 2, "rx": 3, "ry": 4, "rz": 5}
_FAST_NL_BOOTSTRAPPED = False
_FAST_NL_BOOTSTRAP_ERROR: Optional[str] = None
_INITIAL_FIELD_STATE_KEYS = (
    "initial_membrane_stress",
    "initial_bending_stress",
    "initial_membrane_prestrain",
    "initial_curvature_prestrain",
    "initial_fiber_stress",
    "initial_fiber_prestrain",
)


def _ensure_nonlinear_acceleration() -> None:
    """Install optional nonlinear acceleration on first nonlinear use."""

    global _FAST_NL_BOOTSTRAPPED, _FAST_NL_BOOTSTRAP_ERROR
    if _FAST_NL_BOOTSTRAPPED:
        return
    _FAST_NL_BOOTSTRAPPED = True
    if os.environ.get("FE_SOLVER_DISABLE_FAST_NL", "").strip().lower() in {"1", "true", "yes", "on"}:
        return
    try:
        from .nonlinear_performance_bootstrap import install_nonlinear_performance_optimizations

        install_nonlinear_performance_optimizations()
    except Exception as exc:  # Optional acceleration must not disable the solver.
        _FAST_NL_BOOTSTRAP_ERROR = f"{type(exc).__name__}: {exc}"


@dataclass(frozen=True)
class NonlinearLoadStage:
    """One ordered load stage in a nonlinear load program."""

    name: str
    load_case: "LoadCase"
    target_factor: float = 1.0

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise ValueError("NonlinearLoadStage name must not be empty")
        factor = float(self.target_factor)
        if not np.isfinite(factor) or factor <= 0.0:
            raise ValueError("target_factor must be finite and positive")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "target_factor", factor)


@dataclass(frozen=True)
class NonlinearLoadProgram:
    """Ordered nonlinear load path, e.g. permanent then environmental load."""

    stages: Sequence[NonlinearLoadStage]

    def __post_init__(self) -> None:
        stages = tuple(self.stages)
        if not stages:
            raise ValueError("NonlinearLoadProgram requires at least one stage")
        names = [stage.name for stage in stages]
        if len(set(names)) != len(names):
            duplicates = sorted({name for name in names if names.count(name) > 1})
            raise ValueError(
                "NonlinearLoadProgram stage names must be unique; duplicates: "
                + ", ".join(duplicates)
            )
        object.__setattr__(self, "stages", stages)

    @property
    def total_factor(self) -> float:
        return float(sum(stage.target_factor for stage in self.stages))

    def stage_factors(self, path_factor: float) -> Dict[str, float]:
        remaining = max(float(path_factor), 0.0)
        factors: Dict[str, float] = {}
        for stage in self.stages:
            value = min(remaining, stage.target_factor)
            factors[stage.name] = max(value, 0.0)
            remaining -= value
        return factors

    def active_stage(self, path_factor: float) -> str:
        remaining = max(float(path_factor), 0.0)
        for stage in self.stages:
            if remaining <= stage.target_factor + 1.0e-12:
                return stage.name
            remaining -= stage.target_factor
        return self.stages[-1].name


@dataclass(frozen=True)
class ShellInitialField:
    """Prescribed shell residual stress and/or eigenstrain field.

    Each stress or strain component uses shell-local engineering-vector order
    ``[xx, yy, xy]``.  A three-value vector is uniform over the element;
    arrays with one row per integration point are also accepted.

    ``membrane_stress`` is the through-thickness-uniform stress.  The
    ``bending_stress`` value is the antisymmetric stress at the positive
    surface, varying linearly from its negative at ``-t/2``.  Prestrain is
    subtracted from the kinematic strain; ``curvature_prestrain`` has units
    of inverse length.
    """

    membrane_stress: Optional[Any] = None
    bending_stress: Optional[Any] = None
    membrane_prestrain: Optional[Any] = None
    curvature_prestrain: Optional[Any] = None
    source: str = "user"

    def __post_init__(self) -> None:
        if all(
            value is None
            for value in (
                self.membrane_stress,
                self.bending_stress,
                self.membrane_prestrain,
                self.curvature_prestrain,
            )
        ):
            raise ValueError("ShellInitialField requires at least one stress or prestrain component")
        if not str(self.source).strip():
            raise ValueError("ShellInitialField source must not be empty")

    def state_values(self) -> Dict[str, Any]:
        values = {
            "initial_membrane_stress": self.membrane_stress,
            "initial_bending_stress": self.bending_stress,
            "initial_membrane_prestrain": self.membrane_prestrain,
            "initial_curvature_prestrain": self.curvature_prestrain,
        }
        return {
            key: np.asarray(value, dtype=float).copy()
            for key, value in values.items()
            if value is not None
        }


@dataclass(frozen=True)
class BeamInitialField:
    """Prescribed beam-fiber residual stress and/or eigenstrain distribution.

    Values may be scalar, one value per section fiber, or one value per
    Gauss-point/fiber pair.  Arbitrary self-equilibrated distributions are
    therefore representable.  Beam fiber fields require the element's
    ``cross_section["fiber_plasticity"]`` configuration.
    """

    fiber_stress: Optional[Any] = None
    fiber_prestrain: Optional[Any] = None
    source: str = "user"

    def __post_init__(self) -> None:
        if self.fiber_stress is None and self.fiber_prestrain is None:
            raise ValueError("BeamInitialField requires fiber_stress or fiber_prestrain")
        if not str(self.source).strip():
            raise ValueError("BeamInitialField source must not be empty")

    def state_values(self) -> Dict[str, Any]:
        values = {
            "initial_fiber_stress": self.fiber_stress,
            "initial_fiber_prestrain": self.fiber_prestrain,
        }
        return {
            key: np.asarray(value, dtype=float).copy()
            for key, value in values.items()
            if value is not None
        }


@dataclass(frozen=True)
class DisplacementControl:
    """Scalar displacement constraint used with load-factor continuation."""

    node_id: Optional[int] = None
    dof: Optional[Union[str, int]] = None
    target_displacement: float = 0.0
    weighted_dofs: Optional[Mapping[Any, float]] = None

    def full_row(self, model: "FEModel") -> np.ndarray:
        row = np.zeros(model.mesh.dof_manager.total_dofs, dtype=float)
        if self.weighted_dofs:
            for key, weight in self.weighted_dofs.items():
                if isinstance(key, tuple):
                    node_id, dof = key
                    dof_index = _local_dof_index(dof)
                    node = model.mesh.get_node(int(node_id))
                    if node is None:
                        raise ValueError(f"Displacement control references missing node {node_id}")
                    row[node.dofs[dof_index]] += float(weight)
                else:
                    row[int(key)] += float(weight)
        else:
            if self.node_id is None or self.dof is None:
                raise ValueError("DisplacementControl requires node_id and dof, or weighted_dofs")
            node = model.mesh.get_node(int(self.node_id))
            if node is None:
                raise ValueError(f"Displacement control references missing node {self.node_id}")
            row[node.dofs[_local_dof_index(self.dof)]] = 1.0
        if float(np.linalg.norm(row)) <= 0.0:
            raise ValueError("Displacement control row is empty")
        return row


@dataclass(frozen=True)
class NonlinearConvergenceSettings:
    """Automatic convergence controls for force-control nonlinear static solves.

    The settings do not change element theory.  They tune globalization and load
    increment adaptation: line-search usage, step growth after fast convergence,
    and cutback after difficult increments.
    """

    profile: str = "auto"
    line_search: str = "auto"
    fast_iterations: int = 4
    slow_iterations: int = 9
    growth_factor: float = 1.5
    cutback_factor: float = 0.5
    max_step_factor: float = 2.0
    min_step_fraction: Optional[float] = None
    max_line_search_cuts: int = 16
    line_search_reduction: float = 0.5

    def __post_init__(self) -> None:
        profile = str(self.profile).lower()
        line_search = str(self.line_search).lower()
        if profile not in {"legacy", "auto", "balanced", "fast", "robust"}:
            raise ValueError("profile must be one of 'legacy', 'auto', 'balanced', 'fast', or 'robust'")
        if line_search not in {"never", "rescue", "auto", "always"}:
            raise ValueError("line_search must be one of 'never', 'rescue', 'auto', or 'always'")
        if self.fast_iterations <= 0 or self.slow_iterations <= 0:
            raise ValueError("iteration thresholds must be positive")
        if self.growth_factor < 1.0:
            raise ValueError("growth_factor must be at least 1.0")
        if not (0.0 < self.cutback_factor < 1.0):
            raise ValueError("cutback_factor must be between 0 and 1")
        if self.max_step_factor <= 0.0:
            raise ValueError("max_step_factor must be positive")
        if self.min_step_fraction is not None and self.min_step_fraction <= 0.0:
            raise ValueError("min_step_fraction must be positive when supplied")
        if self.max_line_search_cuts <= 0:
            raise ValueError("max_line_search_cuts must be positive")
        if not (0.0 < self.line_search_reduction < 1.0):
            raise ValueError("line_search_reduction must be between 0 and 1")

    @staticmethod
    def for_profile(profile: str) -> "NonlinearConvergenceSettings":
        name = str(profile).lower()
        if name in {"auto", "balanced"}:
            return NonlinearConvergenceSettings(profile=name)
        if name == "fast":
            return NonlinearConvergenceSettings(
                profile="fast",
                line_search="auto",
                fast_iterations=3,
                slow_iterations=8,
                growth_factor=2.0,
                cutback_factor=0.5,
                max_step_factor=4.0,
                max_line_search_cuts=10,
            )
        if name == "robust":
            return NonlinearConvergenceSettings(
                profile="robust",
                line_search="always",
                fast_iterations=5,
                slow_iterations=7,
                growth_factor=1.25,
                cutback_factor=0.5,
                max_step_factor=1.0,
                max_line_search_cuts=20,
            )
        if name == "legacy":
            return NonlinearConvergenceSettings(
                profile="legacy",
                line_search="rescue",
                fast_iterations=5,
                slow_iterations=25,
                growth_factor=2.0,
                cutback_factor=0.5,
                max_step_factor=1.0,
                max_line_search_cuts=16,
            )
        raise ValueError("Unknown nonlinear convergence profile")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile": self.profile,
            "line_search": self.line_search,
            "fast_iterations": int(self.fast_iterations),
            "slow_iterations": int(self.slow_iterations),
            "growth_factor": float(self.growth_factor),
            "cutback_factor": float(self.cutback_factor),
            "max_step_factor": float(self.max_step_factor),
            "min_step_fraction": self.min_step_fraction,
            "max_line_search_cuts": int(self.max_line_search_cuts),
            "line_search_reduction": float(self.line_search_reduction),
        }


def _coerce_convergence_settings(value: Optional[Union[str, Mapping[str, Any], NonlinearConvergenceSettings]]) -> NonlinearConvergenceSettings:
    if value is None:
        return NonlinearConvergenceSettings.for_profile("auto")
    if isinstance(value, NonlinearConvergenceSettings):
        return value
    if isinstance(value, str):
        return NonlinearConvergenceSettings.for_profile(value)
    if isinstance(value, Mapping):
        data = dict(value)
        profile = str(data.pop("profile", "auto")).lower()
        base = NonlinearConvergenceSettings.for_profile(profile).to_dict()
        base.update(data)
        return NonlinearConvergenceSettings(**base)
    raise TypeError("convergence_settings must be None, a profile string, a mapping, or NonlinearConvergenceSettings")


@dataclass
class NonlinearStaticStep:
    """One converged load increment."""

    step_index: int
    load_factor: float
    iterations: int
    residual_norm: float
    displacement_norm: float
    max_equivalent_plastic_strain: float
    control_value: Optional[float] = None
    active_stage: Optional[str] = None
    deleted_element_count: int = 0
    max_fracture_utilization: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "load_factor": self.load_factor,
            "iterations": self.iterations,
            "residual_norm": self.residual_norm,
            "displacement_norm": self.displacement_norm,
            "max_equivalent_plastic_strain": self.max_equivalent_plastic_strain,
            "control_value": self.control_value,
            "active_stage": self.active_stage,
            "deleted_element_count": int(self.deleted_element_count),
            "max_fracture_utilization": float(self.max_fracture_utilization),
        }


@dataclass(frozen=True)
class NonlinearIncrementSnapshot:
    """Opt-in committed state at one converged nonlinear increment.

    Snapshots own defensive copies of the displacement vector and element
    state map.  They are therefore suitable for true step animation and
    material-history-aware recovery without reconstructing intermediate
    states from the final solution.
    """

    step_index: int
    load_factor: float
    displacements: np.ndarray
    element_states: Mapping[int, Any]
    control_value: Optional[float] = None

    def __post_init__(self) -> None:
        values = np.asarray(self.displacements, dtype=float).reshape(-1).copy()
        values.setflags(write=False)
        object.__setattr__(self, "displacements", values)
        object.__setattr__(self, "element_states", copy.deepcopy(dict(self.element_states)))

    def to_dict(self, *, include_displacements: bool = False) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "step_index": int(self.step_index),
            "load_factor": float(self.load_factor),
            "control_value": self.control_value,
            "num_dofs": int(self.displacements.size),
            "element_state_ids": sorted(int(value) for value in self.element_states),
        }
        if include_displacements:
            payload["displacements"] = self.displacements.tolist()
        return payload


def _increment_snapshot(
    step_index: int,
    load_factor: float,
    displacements: np.ndarray,
    element_states: Mapping[int, Any],
    *,
    control_value: Optional[float] = None,
) -> NonlinearIncrementSnapshot:
    return NonlinearIncrementSnapshot(
        step_index=int(step_index),
        load_factor=float(load_factor),
        displacements=displacements,
        element_states=element_states,
        control_value=control_value,
    )


@dataclass
class NonlinearStaticResult:
    """Result of the incremental geometric/material nonlinear solve."""

    steps: List[NonlinearStaticStep]
    status: str
    displacements: np.ndarray
    load_factor: float
    element_states: Dict[int, Any] = field(default_factory=dict)
    info: Dict[str, Any] = field(default_factory=dict)
    snapshots: Tuple[NonlinearIncrementSnapshot, ...] = field(default_factory=tuple)

    @property
    def converged(self) -> bool:
        return self.status in {"completed", "stopped_at_limit"}

    @property
    def capacity_estimate(self) -> float:
        """Last converged proportional load factor."""
        return self.load_factor

    @property
    def peak_load_factor(self) -> float:
        return float(self.info.get("peak_load_factor", max((step.load_factor for step in self.steps), default=self.load_factor)))

    @property
    def last_converged_load_factor(self) -> float:
        return float(self.info.get("last_converged_load_factor", self.load_factor))

    @property
    def failure_reason(self) -> Optional[str]:
        return self.info.get("failure_reason")

    @property
    def status_category(self) -> str:
        return str(self.info.get("status_category", self.status))

    @property
    def stop_reason(self) -> Optional[str]:
        return self.info.get("stop_reason", self.failure_reason)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "status_category": self.status_category,
            "converged": self.converged,
            "load_factor": self.load_factor,
            "peak_load_factor": self.peak_load_factor,
            "last_converged_load_factor": self.last_converged_load_factor,
            "failure_reason": self.failure_reason,
            "stop_reason": self.stop_reason,
            "info": self.info,
            "steps": [step.to_dict() for step in self.steps],
            "snapshots": [snapshot.to_dict() for snapshot in self.snapshots],
        }

    @property
    def quantity_metadata(self) -> Tuple[Any, ...]:
        from .quantities import describe_result_quantities

        return describe_result_quantities(self)


def _local_dof_index(dof: Union[str, int]) -> int:
    if isinstance(dof, str):
        key = dof.lower()
        if key not in _DOF_INDEX:
            raise ValueError(f"Unknown DOF {dof!r}; use one of {sorted(_DOF_INDEX)}")
        return _DOF_INDEX[key]
    index = int(dof)
    if not (0 <= index < 6):
        raise ValueError("DOF index must be in [0, 5]")
    return index


def _has_follower_pressure(load_case: Optional["LoadCase"]) -> bool:
    """Whether a load case contains current-area pressure."""
    return bool(
        load_case is not None
        and getattr(load_case, "pressure_loads", None)
        and getattr(load_case, "follower_pressure", False)
    )


def _weighted_external_load_system(
    model: "FEModel",
    weighted_load_cases: Sequence[Tuple[Optional["LoadCase"], float]],
    displacements: np.ndarray,
    *,
    tangent: bool,
) -> Tuple[np.ndarray, Optional[sparse.csr_matrix]]:
    """Assemble a weighted external force and its displacement derivative."""
    total_dofs = model.mesh.dof_manager.total_dofs
    force = np.zeros(total_dofs, dtype=float)
    load_tangent = sparse.csr_matrix((total_dofs, total_dofs), dtype=float) if tangent else None
    for load_case, raw_factor in weighted_load_cases:
        factor = float(raw_factor)
        if load_case is None or factor == 0.0:
            continue
        vector, case_tangent, _info = assemble_external_load_system(
            model,
            load_case,
            displacements,
            tangent=tangent,
        )
        force += factor * vector
        if tangent and case_tangent is not None and case_tangent.nnz:
            load_tangent = load_tangent + factor * case_tangent
    return force, load_tangent


def _assemble_nonlinear_system(
    model: "FEModel",
    displacements: np.ndarray,
    committed_states: Dict[int, Any],
    num_layers: int,
    tangent: bool = True,
    deleted_element_ids: Optional[Sequence[int]] = None,
    residual_stiffness_fraction: float = 1.0,
    element_stiffness_scales: Optional[Mapping[int, float]] = None,
    kinematics: str = "von_karman",
    corotational_tangent: str = "rotated",
) -> Tuple[np.ndarray, Any, Dict[int, Any]]:
    """Assemble F_int (and the tangent K_T when requested) at a state.

    ``kinematics`` selects between the default von Karman element response and
    the element-independent corotational formulation for large rigid
    rotations. ``corotational_tangent`` is already resolved to either
    ``"rotated"`` or ``"consistent"`` by the public solver.
    """
    mesh = model.mesh
    total_dofs = mesh.dof_manager.total_dofs
    F_int = np.zeros(total_dofs, dtype=float)
    data: list = []
    trial_states: Dict[int, Any] = {}
    deleted_set = {int(element_id) for element_id in (deleted_element_ids or ())}
    residual_fraction = float(residual_stiffness_fraction)
    element_scales = {
        int(element_id): min(max(float(scale), 0.0), 1.0)
        for element_id, scale in (element_stiffness_scales or {}).items()
    }

    if tangent:
        from .matrix_assembly import _get_cached_sparsity_pattern
        rows_concat, cols_concat = _get_cached_sparsity_pattern(mesh, "tangent_stiffness")

    from .elements import ShellElement
    from .materials import is_isotropic_material
    from .vectorized_nonlinear import batch_shell_nonlinear_response, shell_nonlinear_batch_eligible

    groups = {}
    for elem_id, element in mesh.elements.items():
        if kinematics == "corotational":
            break
        # Initial stress/eigenstrain fields are deliberately evaluated by the
        # scalar element kernel.  The ordinary batched path stays untouched
        # and fast, while field-bearing elements can retain their immutable
        # offsets alongside the committed material history.
        if (
            isinstance(element, ShellElement)
            and shell_nonlinear_batch_eligible(element)
            and is_isotropic_material(model.get_material(element.material_name))
            and not _state_has_initial_field(committed_states.get(elem_id))
        ):
            key = (
                element.num_nodes,
                element.thickness,
                element.drilling_stabilization,
                element.reduced_integration,
                element.hourglass_stabilization,
                element.material_name,
            )
            if key not in groups:
                groups[key] = []
            groups[key].append((elem_id, element))

    precomputed_F = {}
    precomputed_K = {}

    for key, elem_list in groups.items():
        num_nodes, thickness, drilling_stabilization, _reduced_integration, _hourglass_stabilization, material_name = key
        material = model.get_material(material_name)
        E = float(material.elastic_modulus)
        nu = float(material.poisson_ratio)
        G_mod = float(material.shear_modulus)
        curve = getattr(material, "hardening_curve", None)

        n_elem = len(elem_list)
        first_element = elem_list[0][1]
        n_dof = first_element.total_dofs

        # We need to extract the caches
        cache_first = first_element._nonlinear_geometry(mesh)
        n_gp = cache_first["detw_all"].shape[0]
        n_shear = cache_first["detw_shear_all"].shape[0]

        u_elem_batch = np.zeros((n_elem, n_dof))
        T0_batch = np.zeros((n_elem, n_dof, n_dof))
        B_m_all_batch = np.zeros((n_elem, n_gp, 3, n_dof))
        B_b_all_batch = np.zeros((n_elem, n_gp, 3, n_dof))
        B_d_all_batch = np.zeros((n_elem, n_gp, 1, n_dof))
        Gw_all_batch = np.zeros((n_elem, n_gp, 2, n_dof))
        detw_all_batch = np.zeros((n_elem, n_gp))
        B_s_all_batch = np.zeros((n_elem, n_shear, 2, n_dof))
        detw_shear_all_batch = np.zeros((n_elem, n_shear))

        plastic_strain_batch = np.zeros((n_elem, n_gp * num_layers, 3))
        alpha_batch = np.zeros((n_elem, n_gp * num_layers))

        dof_mappings = []
        for idx, (elem_id, element) in enumerate(elem_list):
            dof_mapping = np.asarray(element.get_dof_mapping(mesh), dtype=np.intp)
            dof_mappings.append(dof_mapping)
            if dof_mapping.size > 0:
                u_elem_batch[idx] = displacements[dof_mapping]

            cache = element._nonlinear_geometry(mesh)
            T0_batch[idx] = cache["T0"]
            B_m_all_batch[idx] = cache["B_m_all"]
            B_b_all_batch[idx] = cache["B_b_all"]
            B_d_all_batch[idx] = cache["B_d_all"]
            Gw_all_batch[idx] = cache["Gw_all"]
            detw_all_batch[idx] = cache["detw_all"]
            B_s_all_batch[idx] = cache["B_s_all"]
            detw_shear_all_batch[idx] = cache["detw_shear_all"]

            state = committed_states.get(elem_id)
            if state is None:
                state = element.init_nonlinear_state(num_layers)
            plastic_strain_batch[idx] = state["plastic_strain"]
            alpha_batch[idx] = state["alpha"]

        F_int_batch, K_T_batch, ep_new, alpha_new, layer_strain_batch = batch_shell_nonlinear_response(
            u_elem_batch,
            T0_batch,
            B_m_all_batch,
            B_b_all_batch,
            B_d_all_batch,
            Gw_all_batch,
            detw_all_batch,
            B_s_all_batch,
            detw_shear_all_batch,
            E,
            nu,
            G_mod,
            thickness,
            drilling_stabilization,
            tangent,
            curve,
            plastic_strain_batch,
            alpha_batch,
            num_layers,
        )

        for idx, (elem_id, element) in enumerate(elem_list):
            precomputed_F[elem_id] = F_int_batch[idx]
            if tangent:
                precomputed_K[elem_id] = K_T_batch[idx]

            # Reconstruct trial state to be compatible with single-element API
            trial_state = {
                "plastic_strain": ep_new[idx],
                "alpha": alpha_new[idx],
                "layer_strain": layer_strain_batch[idx * n_gp * num_layers : (idx + 1) * n_gp * num_layers].copy(),
            }
            if curve is not None:
                # We need layer_stress for outputs if people use it, let's keep it simple: we can omit it if not strictly required,
                # but let's see if elements.py returned it. We didn't return it from batch_shell_nonlinear_response.
                pass
            if elem_id in deleted_set:
                trial_state = committed_states.get(elem_id, trial_state)
            trial_states[elem_id] = trial_state

    for elem_id, element in mesh.elements.items():
        dof_mapping = np.asarray(element.get_dof_mapping(mesh), dtype=np.intp)
        if dof_mapping.size == 0:
            continue

        if elem_id in precomputed_F:
            f_elem = precomputed_F[elem_id]
            k_elem = precomputed_K.get(elem_id) if tangent else None
            # trial_state already in trial_states dict
        else:
            f_elem = None
            k_elem = None
            if kinematics == "corotational":
                from .corotational import corotational_element_response

                f_elem, k_elem, cr_trial_state = corotational_element_response(
                    model,
                    int(elem_id),
                    element,
                    displacements[dof_mapping],
                    tangent,
                    committed_state=committed_states.get(elem_id),
                    num_layers=num_layers,
                    tangent_mode=corotational_tangent,
                )
                if f_elem is not None and cr_trial_state is not None:
                    trial_states[elem_id] = cr_trial_state
            if f_elem is None:
                material = model.get_material(element.material_name)
                u_elem = displacements[dof_mapping]
                f_elem, k_elem, trial_state = element.compute_nonlinear_response(
                    mesh, material, u_elem, committed_states.get(elem_id), num_layers, tangent
                )
                if trial_state is not None:
                    trial_states[elem_id] = trial_state

        if elem_id in deleted_set:
            f_elem = residual_fraction * np.asarray(f_elem, dtype=float)
            if tangent and k_elem is not None:
                k_elem = residual_fraction * np.asarray(k_elem, dtype=float)
            if elem_id in committed_states:
                trial_states[elem_id] = committed_states[elem_id]
        elif elem_id in element_scales:
            scale = float(element_scales[elem_id])
            f_elem = scale * np.asarray(f_elem, dtype=float)
            if tangent and k_elem is not None:
                k_elem = scale * np.asarray(k_elem, dtype=float)

        np.add.at(F_int, dof_mapping, np.asarray(f_elem, dtype=float))
        if tangent and k_elem is not None:
            data.append(np.asarray(k_elem, dtype=float).ravel())

    if tangent:
        if not data:
            K_T = sparse.csr_matrix((total_dofs, total_dofs), dtype=float)
        else:
            K_T = sparse.coo_matrix(
                (np.concatenate(data), (rows_concat, cols_concat)),
                shape=(total_dofs, total_dofs),
                dtype=float,
            ).tocsr()
    else:
        K_T = None

    return F_int, K_T, trial_states


def _max_plastic_strain(states: Dict[int, Any]) -> float:
    return float(_nonlinear_state_summary(states)["max_equivalent_plastic_strain"])


def state_von_mises_envelope(state: Any, E: float, nu: float) -> Optional[float]:
    """Max von Mises stress reconstructed from a committed layered shell state.

    ``sigma = C_el (eps_layer - eps_p)`` reproduces the return-mapped stress
    at the last commit exactly, so the value respects the material hardening
    curve -- unlike an elastic recovery from total displacements, which keeps
    growing with plastic strain.  Returns ``None`` for states without layered
    strain data (e.g. beam fiber states) so callers can fall back to elastic
    recovery.
    """
    if not isinstance(state, Mapping):
        return None
    fiber_stress = np.asarray(state.get("fiber_stress", ()), dtype=float).reshape(-1)
    if fiber_stress.size:
        # Beam fiber sections store the return-mapped uniaxial stress
        # directly; its magnitude is the von Mises equivalent.
        return float(np.max(np.abs(fiber_stress)))
    layer = np.asarray(state.get("layer_strain", ()), dtype=float)
    plastic = np.asarray(state.get("plastic_strain", ()), dtype=float)
    if layer.size == 0 or layer.shape != plastic.shape:
        return None
    layer = layer.reshape(-1, layer.shape[-1]) if layer.ndim > 1 else layer.reshape(-1, 1)
    if layer.shape[-1] != 3:
        return None
    plastic = plastic.reshape(layer.shape)
    elastic = layer - plastic
    factor = float(E) / (1.0 - float(nu) ** 2)
    sxx = factor * (elastic[:, 0] + float(nu) * elastic[:, 1])
    syy = factor * (elastic[:, 1] + float(nu) * elastic[:, 0])
    sxy = factor * (1.0 - float(nu)) / 2.0 * elastic[:, 2]
    von_mises = np.sqrt(np.maximum(sxx * sxx - sxx * syy + syy * syy + 3.0 * sxy * sxy, 0.0))
    return float(np.max(von_mises)) if von_mises.size else None


def states_von_mises_map(model: Any, states: Mapping[int, Any]) -> Dict[int, float]:
    """Per-element von Mises envelope from committed plastic states.

    Layered shell states are batched per (material, layer-count) group and
    reduced with one vectorized pass; this runs once per saved transient step
    over every element state, so per-element numpy calls dominate on large
    models.  Values match :func:`state_von_mises_envelope` exactly.
    """
    constants: Dict[str, Tuple[float, float]] = {}
    values: Dict[int, float] = {}
    layered_groups: Dict[Tuple[str, int], Tuple[List[int], List[np.ndarray], List[np.ndarray]]] = {}
    for element_id, state in states.items():
        element = model.mesh.elements.get(int(element_id))
        if element is None or not isinstance(state, Mapping):
            continue
        fiber_stress = np.asarray(state.get("fiber_stress", ()), dtype=float).reshape(-1)
        if fiber_stress.size:
            values[int(element_id)] = float(np.max(np.abs(fiber_stress)))
            continue
        stored_stress = np.asarray(state.get("layer_stress", ()), dtype=float)
        if stored_stress.size:
            try:
                stored_stress = stored_stress.reshape(-1, 3)
            except ValueError:
                stored_stress = np.empty((0, 3), dtype=float)
            if stored_stress.size:
                sxx = stored_stress[:, 0]
                syy = stored_stress[:, 1]
                sxy = stored_stress[:, 2]
                von_mises = np.sqrt(
                    np.maximum(
                        sxx * sxx - sxx * syy + syy * syy + 3.0 * sxy * sxy,
                        0.0,
                    )
                )
                values[int(element_id)] = float(np.max(von_mises))
                continue
        layer = np.asarray(state.get("layer_strain", ()), dtype=float)
        plastic = np.asarray(state.get("plastic_strain", ()), dtype=float)
        if layer.size == 0 or layer.shape != plastic.shape:
            continue
        layer = layer.reshape(-1, layer.shape[-1]) if layer.ndim > 1 else layer.reshape(-1, 1)
        if layer.shape[-1] != 3:
            continue
        name = str(element.material_name)
        from .materials import is_isotropic_material

        # Modern orthotropic states always retain converged physical layer
        # stress.  An incomplete legacy/restart state must not be reconstructed
        # with fictitious isotropic constants.
        if not is_isotropic_material(model.get_material(name)):
            continue
        ids, layers, plastics = layered_groups.setdefault((name, layer.shape[0]), ([], [], []))
        ids.append(int(element_id))
        layers.append(layer)
        plastics.append(plastic.reshape(layer.shape))
    for (name, rows), (ids, layers, plastics) in layered_groups.items():
        if name not in constants:
            material = model.get_material(name)
            constants[name] = (float(material.elastic_modulus), float(material.poisson_ratio))
        E, nu = constants[name]
        elastic = np.concatenate(layers) - np.concatenate(plastics)
        factor = E / (1.0 - nu**2)
        sxx = factor * (elastic[:, 0] + nu * elastic[:, 1])
        syy = factor * (elastic[:, 1] + nu * elastic[:, 0])
        sxy = factor * (1.0 - nu) / 2.0 * elastic[:, 2]
        von_mises = np.sqrt(np.maximum(sxx * sxx - sxx * syy + syy * syy + 3.0 * sxy * sxy, 0.0))
        per_element = von_mises.reshape(len(ids), rows).max(axis=1)
        for element_id, value in zip(ids, per_element):
            values[element_id] = float(value)
    return values


def _nonlinear_state_summary(states: Dict[int, Any]) -> Dict[str, Any]:
    """Summarize plastic strain and layer/fiber strain data from element states.

    Vectorized: the per-state arrays are gathered once and reduced with a
    handful of concatenated numpy calls.  The previous per-element reductions
    ran once per element per saved transient step and rivalled the cost of
    the Newton solves on large impact models.
    """
    alpha_parts: List[np.ndarray] = []
    plastic_parts: List[np.ndarray] = []
    layer_parts: List[np.ndarray] = []
    fiber_parts: List[np.ndarray] = []
    # (alpha, compression-measure) pairs with row alignment, grouped by the
    # number of in-plane strain columns participating in the compression test.
    comp_layer_pairs: Dict[int, Tuple[List[np.ndarray], List[np.ndarray]]] = {}
    comp_fiber_alpha: List[np.ndarray] = []
    comp_fiber_measure: List[np.ndarray] = []

    for state in states.values():
        if not isinstance(state, dict):
            continue
        alpha = np.asarray(state.get("alpha", ()), dtype=float).reshape(-1)
        if alpha.size:
            alpha_parts.append(alpha)
        plastic = np.asarray(state.get("plastic_strain", ()), dtype=float)
        if plastic.size:
            plastic_parts.append(plastic.reshape(-1))
        layer = np.asarray(state.get("layer_strain", ()), dtype=float)
        if layer.size:
            layer_2d = layer.reshape((-1, layer.shape[-1] if layer.ndim > 1 else 1))
            layer_parts.append(layer_2d.reshape(-1))
            if alpha.size == layer_2d.shape[0]:
                width = min(2, layer_2d.shape[1])
                alphas, measures = comp_layer_pairs.setdefault(width, ([], []))
                alphas.append(alpha)
                measures.append(layer_2d[:, :width])
        fiber = np.asarray(state.get("fiber_strain", ()), dtype=float).reshape(-1)
        if fiber.size:
            fiber_parts.append(fiber)
            if alpha.size == fiber.size:
                comp_fiber_alpha.append(alpha)
                comp_fiber_measure.append(fiber)

    max_alpha = 0.0
    yielded = 0
    if alpha_parts:
        alpha_all = np.concatenate(alpha_parts)
        max_alpha = float(np.max(alpha_all))
        sizes = np.asarray([part.size for part in alpha_parts], dtype=np.intp)
        offsets = np.concatenate(([0], np.cumsum(sizes[:-1])))
        yielded = int(np.count_nonzero(np.maximum.reduceat(alpha_all, offsets) > 0.0))
    max_plastic_component = float(np.max(np.abs(np.concatenate(plastic_parts)))) if plastic_parts else 0.0
    layer_min = float("inf")
    layer_max = float("-inf")
    if layer_parts:
        layer_all = np.concatenate(layer_parts)
        layer_min = float(np.min(layer_all))
        layer_max = float(np.max(layer_all))
    fiber_min = float("inf")
    fiber_max = float("-inf")
    if fiber_parts:
        fiber_all = np.concatenate(fiber_parts)
        fiber_min = float(np.min(fiber_all))
        fiber_max = float(np.max(fiber_all))
    max_compressed_alpha = 0.0
    for _width, (alphas, measures) in comp_layer_pairs.items():
        alpha_all = np.concatenate(alphas)
        compression = np.min(np.concatenate(measures), axis=1) < 0.0
        if np.any(compression):
            max_compressed_alpha = max(max_compressed_alpha, float(np.max(alpha_all[compression])))
    if comp_fiber_alpha:
        alpha_all = np.concatenate(comp_fiber_alpha)
        compression = np.concatenate(comp_fiber_measure) < 0.0
        if np.any(compression):
            max_compressed_alpha = max(max_compressed_alpha, float(np.max(alpha_all[compression])))

    return {
        "max_equivalent_plastic_strain": max_alpha,
        "max_plastic_strain_component": max_plastic_component,
        "max_compressed_side_plastic_strain": max_compressed_alpha,
        "layer_strain_min": None if layer_min == float("inf") else layer_min,
        "layer_strain_max": None if layer_max == float("-inf") else layer_max,
        "fiber_strain_min": None if fiber_min == float("inf") else fiber_min,
        "fiber_strain_max": None if fiber_max == float("-inf") else fiber_max,
        "yielded_element_count": yielded,
    }


def _copy_initial_states(initial_element_states: Optional[Mapping[int, Any]]) -> Dict[int, Any]:
    return copy.deepcopy(dict(initial_element_states or {}))


def _state_has_initial_field(state: Any) -> bool:
    return isinstance(state, Mapping) and any(key in state for key in _INITIAL_FIELD_STATE_KEYS)


def _initial_value_summary(value: Any) -> Dict[str, Any]:
    array = np.asarray(value, dtype=float)
    return {
        "shape": list(array.shape),
        "minimum": float(np.min(array)),
        "maximum": float(np.max(array)),
    }


def _coerce_initial_field(value: Any) -> Union[ShellInitialField, BeamInitialField]:
    if isinstance(value, (ShellInitialField, BeamInitialField)):
        return value
    if not isinstance(value, Mapping):
        raise TypeError("Initial fields must be ShellInitialField, BeamInitialField, or mappings")
    data = dict(value)
    kind = str(data.pop("kind", "")).strip().lower()
    shell_names = {"membrane_stress", "bending_stress", "membrane_prestrain", "curvature_prestrain"}
    beam_names = {"fiber_stress", "fiber_prestrain"}
    supplied = set(data) - {"source"}
    if kind == "shell" or (not kind and supplied and supplied <= shell_names):
        return ShellInitialField(**data)
    if kind == "beam" or (not kind and supplied and supplied <= beam_names):
        return BeamInitialField(**data)
    raise ValueError(
        "Initial-field mapping requires kind='shell' or kind='beam', or unambiguous field names"
    )


def _prepare_initial_states(
    model: "FEModel",
    initial_element_states: Optional[Mapping[int, Any]],
    initial_fields: Optional[Mapping[int, Any]],
    num_layers: int,
) -> Tuple[Dict[int, Any], List[Dict[str, Any]]]:
    """Merge prescribed residual fields into committed element state.

    Initial fields remain immutable state offsets while plastic strain and
    hardening variables are committed normally.  This separation prevents a
    geometric imperfection from being mislabeled as residual stress and lets
    restart states retain the manufacturing-field provenance.
    """
    states = _copy_initial_states(initial_element_states)
    provenance: List[Dict[str, Any]] = []
    for raw_element_id, state in states.items():
        if not _state_has_initial_field(state):
            continue
        stored = state.get("initial_field_provenance", {}) if isinstance(state, Mapping) else {}
        components = {
            key.removeprefix("initial_"): _initial_value_summary(state[key])
            for key in _INITIAL_FIELD_STATE_KEYS
            if key in state
        }
        provenance.append(
            {
                "element_id": int(raw_element_id),
                "kind": str(stored.get("kind", "unknown")),
                "source": str(stored.get("source", "restart_state")),
                "components": components,
                "restored_from_committed_state": True,
            }
        )
    if not initial_fields:
        return states, provenance

    from .elements import (
        BeamElement,
        QuadraticBeamElement,
        ShellElement,
        validate_initial_field_state,
    )

    for raw_element_id, raw_field in initial_fields.items():
        element_id = int(raw_element_id)
        provenance = [
            entry for entry in provenance
            if int(entry["element_id"]) != element_id
        ]
        element = model.mesh.get_element(element_id)
        if element is None:
            raise ValueError(f"Initial field references missing element {element_id}")
        field_value = _coerce_initial_field(raw_field)
        previous_state = states.get(element_id)
        if isinstance(previous_state, Mapping):
            previous_plastic = np.asarray(
                previous_state.get("plastic_strain", ()),
                dtype=float,
            )
            previous_alpha = np.asarray(
                previous_state.get("alpha", ()),
                dtype=float,
            )
            if (
                previous_plastic.size
                and np.any(np.abs(previous_plastic) > 1.0e-14)
            ) or (
                previous_alpha.size
                and np.any(previous_alpha > 1.0e-14)
            ):
                raise ValueError(
                    f"Cannot superpose a new initial field on nonzero plastic history for "
                    f"element {element_id}; restart with the already-committed field state instead."
                )
        if isinstance(field_value, ShellInitialField):
            if not isinstance(element, ShellElement):
                raise TypeError(f"ShellInitialField requires a shell element; {element_id} is {type(element).__name__}")
            state = states.get(element_id)
            if state is None:
                state = element.init_nonlinear_state(num_layers)
            elif not isinstance(state, Mapping):
                raise TypeError(f"Initial state for shell element {element_id} must be a mapping")
            state = copy.deepcopy(dict(state))
            values = field_value.state_values()
            field_type = "shell"
        else:
            if not isinstance(element, (BeamElement, QuadraticBeamElement)):
                raise TypeError(f"BeamInitialField requires a beam element; {element_id} is {type(element).__name__}")
            if getattr(element, "_fiber_plasticity_config")(model.get_material(element.material_name)) is None:
                raise ValueError(
                    f"Beam initial fiber fields require fiber plasticity on element {element_id}"
                )
            state = states.get(element_id)
            if state is None:
                state = {}
            elif not isinstance(state, Mapping):
                raise TypeError(f"Initial state for beam element {element_id} must be a mapping")
            state = copy.deepcopy(dict(state))
            values = field_value.state_values()
            field_type = "beam"
        # Supplying a field for an element replaces its complete prior field
        # definition. Mixing old components with a new source would make both
        # the constitutive input and its provenance ambiguous; callers that
        # want multiple components must provide them together in one field.
        for key in (*_INITIAL_FIELD_STATE_KEYS, "initial_field_provenance"):
            state.pop(key, None)
        for key, array in values.items():
            if array.size == 0 or np.any(~np.isfinite(array)):
                raise ValueError(f"{key} for element {element_id} must contain finite values")
            state[key] = array
        state["initial_field_provenance"] = {
            "kind": field_type,
            "source": field_value.source,
            "components": sorted(values),
        }
        validate_initial_field_state(
            element,
            model.get_material(element.material_name),
            state,
            num_layers,
            model.mesh,
        )
        states[element_id] = state
        provenance.append(
            {
                "element_id": element_id,
                "kind": field_type,
                "source": field_value.source,
                "components": {
                    key.removeprefix("initial_"): _initial_value_summary(array)
                    for key, array in values.items()
                },
            }
        )
    return states, provenance


def _finalize_nonlinear_element_states(
    model: "FEModel",
    displacements: np.ndarray,
    element_states: Dict[int, Any],
    num_layers: int,
    *,
    kinematics: str = "von_karman",
) -> Dict[int, Any]:
    """Return result-ready element states.

    The default assembly paths already return complete recovery state. Optional
    acceleration layers may replace this no-op with a final-displacement
    recovery pass for data deliberately omitted inside Newton iterations.
    """

    del model, displacements, num_layers, kinematics
    return element_states


def _nonlinear_status_category(status: str, failure_reason: Optional[str]) -> str:
    if status == "completed":
        return "converged"
    if status == "empty_reduced_system":
        return "invalid_model"
    reason = str(failure_reason or "")
    if reason.startswith("fracture_") or "deleted_fraction" in reason:
        return "fracture_limit"
    if "singular" in reason or "factorization" in reason:
        return "singular_tangent"
    if "nonfinite" in reason:
        return "numerical_instability"
    if "maximum_iterations" in reason:
        return "iteration_failure"
    if "minimum_load_increment" in reason:
        return "limit_point_or_nonconvergence"
    if status == "stopped_at_limit":
        return "limit_point_or_nonconvergence"
    return "failed"


def _equilibrate_initial_fields(
    *,
    model: "FEModel",
    T: sparse.csr_matrix,
    u0: np.ndarray,
    committed_states: Dict[int, Any],
    num_layers: int,
    max_iterations: int,
    tolerance: float,
    kinematics: str,
    corotational_tangent: str,
    general_tangent: bool,
    initial_reduced_displacements: Optional[np.ndarray] = None,
    cancellation_token: Optional[CancellationToken] = None,
) -> Tuple[np.ndarray, Dict[int, Any], List[Dict[str, Any]], Optional[str]]:
    """Equilibrate prescribed residual fields before any external load.

    The residual field is held fixed while compatible displacements and the
    material history are solved from ``F_int = 0``.  Only a converged trial
    state is committed.  This is intentionally a separate zero-load phase so
    permanent/environmental loading cannot silently absorb an unbalanced
    manufacturing field in its first increment.
    """
    n_red = int(T.shape[1])
    if initial_reduced_displacements is None:
        q = np.zeros(n_red, dtype=float)
    else:
        q = np.asarray(initial_reduced_displacements, dtype=float).reshape(-1).copy()
        if q.size != n_red:
            raise ValueError(
                f"initial_reduced_displacements has {q.size} entries; expected {n_red}"
            )
    committed_q = q.copy()
    history: List[Dict[str, Any]] = []
    reference: Optional[float] = None
    for iteration in range(1, max_iterations + 1):
        cancellation_safe_point(
            cancellation_token,
            f"nonlinear_static.initial_equilibration.iteration:{iteration}",
        )
        u = np.asarray(T @ q + u0, dtype=float).reshape(-1)
        F_int, K_T, trial_states = _assemble_nonlinear_system(
            model,
            u,
            committed_states,
            num_layers,
            tangent=True,
            kinematics=kinematics,
            corotational_tangent=corotational_tangent,
        )
        residual = -np.asarray(T.T @ F_int, dtype=float).reshape(-1)
        residual_norm = float(np.linalg.norm(residual))
        if reference is None:
            reference = max(residual_norm, 1.0)
        history.append(
            {
                "iteration": iteration,
                "residual_norm": residual_norm,
                "displacement_norm": float(np.linalg.norm(u)),
            }
        )
        if not np.isfinite(residual_norm):
            return committed_q, committed_states, history, "nonfinite_initial_state_residual"
        if residual_norm <= tolerance * reference:
            return q, trial_states, history, None
        K_red = (T.T @ K_T @ T).tocsr()
        try:
            with np.errstate(all="ignore"):
                handle = factorize(
                    K_red,
                    MatrixClass.GENERAL if general_tangent else MatrixClass.SYMMETRIC_INDEFINITE,
                    signature=f"nonlinear.initial_state:{iteration}",
                )
                dq = np.asarray(handle.solve(residual), dtype=float).reshape(-1)
        except Exception:
            return committed_q, committed_states, history, "singular_initial_state_tangent"
        if np.any(~np.isfinite(dq)):
            return committed_q, committed_states, history, "nonfinite_initial_state_increment"

        # Residual-norm backtracking makes non-equilibrated user fields
        # predictable without affecting the ordinary load-step fast path.
        accepted = False
        scale = 1.0
        for _ in range(16):
            q_candidate = q + scale * dq
            u_candidate = np.asarray(T @ q_candidate + u0, dtype=float).reshape(-1)
            F_candidate, _unused, _candidate_states = _assemble_nonlinear_system(
                model,
                u_candidate,
                committed_states,
                num_layers,
                tangent=False,
                kinematics=kinematics,
                corotational_tangent=corotational_tangent,
            )
            candidate_norm = float(
                np.linalg.norm(-np.asarray(T.T @ F_candidate, dtype=float).reshape(-1))
            )
            if np.isfinite(candidate_norm) and candidate_norm < residual_norm:
                q = q_candidate
                accepted = True
                break
            scale *= 0.5
        if not accepted:
            return committed_q, committed_states, history, "initial_state_line_search_failed"
    return committed_q, committed_states, history, "maximum_initial_state_iterations_reached"


def _reduced_coordinates(
    T: sparse.csr_matrix,
    u0: np.ndarray,
    displacements: Optional[np.ndarray],
) -> np.ndarray:
    """Recover reduced coordinates for a compatible full displacement state."""
    if displacements is None:
        return np.zeros(int(T.shape[1]), dtype=float)
    full = np.asarray(displacements, dtype=float).reshape(-1)
    if full.size != T.shape[0]:
        raise ValueError(f"initial_displacements has {full.size} entries; expected {T.shape[0]}")
    if np.any(~np.isfinite(full)):
        raise ValueError("initial_displacements must contain only finite values")
    rhs = full - np.asarray(u0, dtype=float).reshape(-1)
    if int(T.shape[1]) == 0:
        error = float(np.linalg.norm(rhs))
        scale = max(float(np.linalg.norm(full)), 1.0)
        if error > 1.0e-9 * scale:
            raise ValueError(
                "initial_displacements is incompatible with the fully "
                f"constrained state (residual {error:.3e})"
            )
        return np.zeros(0, dtype=float)
    solution = sparse.linalg.lsqr(T, rhs, atol=1.0e-12, btol=1.0e-12)
    q = np.asarray(solution[0], dtype=float).reshape(-1)
    if np.any(~np.isfinite(q)):
        raise ValueError("initial_displacements could not be reduced to finite coordinates")
    error = float(np.linalg.norm(np.asarray(T @ q, dtype=float).reshape(-1) - rhs))
    scale = max(float(np.linalg.norm(rhs)), 1.0)
    if error > 1.0e-9 * scale:
        raise ValueError(
            "initial_displacements is incompatible with the active supports/MPC constraints "
            f"(projection residual {error:.3e})"
        )
    return q


def _solve_static_displacement_control(
    *,
    model: "FEModel",
    T: sparse.csr_matrix,
    u0: np.ndarray,
    F_const: np.ndarray,
    F_prop: np.ndarray,
    stage_vectors: Sequence[np.ndarray],
    load_case: Optional["LoadCase"],
    constant_load_case: Optional["LoadCase"],
    load_program: Optional[NonlinearLoadProgram],
    displacement_control: DisplacementControl,
    committed_states: Dict[int, Any],
    num_layers: int,
    num_steps: int,
    max_iterations: int,
    tolerance: float,
    info: Dict[str, Any],
    start_time: float,
    resource_config: Optional[ResourceConfig] = None,
    kinematics: str = "von_karman",
    corotational_tangent: str = "not_applicable",
    initial_reduced_displacements: Optional[np.ndarray] = None,
    cancellation_token: Optional[CancellationToken] = None,
    progress_callback: Optional[ProgressCallback] = None,
    record_increment_snapshots: bool = False,
) -> NonlinearStaticResult:
    """Displacement-control Newton solve with load factor as an unknown."""
    if load_program is not None:
        if len(load_program.stages) == 1:
            constant_terms = [(constant_load_case, 1.0)]
            proportional_term = (
                load_program.stages[0].load_case,
                load_program.stages[0].target_factor,
            )
            F_const_static = F_const
            F_prop_static = load_program.stages[0].target_factor * stage_vectors[0]
            active_stage = load_program.stages[0].name
        else:
            constant_terms = [(constant_load_case, 1.0)] + [
                (stage.load_case, stage.target_factor)
                for stage in load_program.stages[:-1]
            ]
            proportional_term = (
                load_program.stages[-1].load_case,
                load_program.stages[-1].target_factor,
            )
            F_const_static = F_const.copy()
            for stage, vector in zip(load_program.stages[:-1], stage_vectors[:-1]):
                F_const_static += stage.target_factor * vector
            F_prop_static = load_program.stages[-1].target_factor * stage_vectors[-1]
            active_stage = load_program.stages[-1].name
        info["displacement_control_load_split"] = {
            "constant_stages": [stage.name for stage in load_program.stages[:-1]],
            "proportional_stage": active_stage,
        }
    else:
        constant_terms = [(constant_load_case, 1.0)]
        proportional_term = (load_case, 1.0)
        F_const_static = F_const
        F_prop_static = F_prop
        active_stage = "displacement_control"

    n_red = int(T.shape[1])
    if initial_reduced_displacements is None:
        q = np.zeros(n_red, dtype=float)
    else:
        q = np.asarray(initial_reduced_displacements, dtype=float).reshape(-1).copy()
        if q.size != n_red:
            raise ValueError(
                f"initial_reduced_displacements has {q.size} entries; expected {n_red}"
            )
    lam = 0.0
    steps: List[NonlinearStaticStep] = []
    snapshots: List[NonlinearIncrementSnapshot] = []
    history: List[Dict[str, Any]] = []
    status = "completed"
    failure_reason: Optional[str] = None
    total_iterations = 0

    row_full = displacement_control.full_row(model)
    row_red = np.asarray(row_full @ T, dtype=float).reshape(-1)
    row_u0 = float(row_full @ u0)
    if float(np.linalg.norm(row_red)) <= 0.0:
        raise ValueError("Displacement control target is fixed or dependent and cannot be used as an unknown")

    initial_u = np.asarray(u0, dtype=float).reshape(-1)
    follower_active = any(_has_follower_pressure(case) for case, _factor in [*constant_terms, proportional_term])
    general_tangent = follower_active or (
        str(kinematics) == "corotational"
        and str(corotational_tangent) == "consistent"
    )
    if follower_active:
        F_prop_initial, _ = _weighted_external_load_system(
            model,
            [proportional_term],
            initial_u,
            tangent=False,
        )
    else:
        F_prop_initial = F_prop_static
    F_prop_red = np.asarray(T.T @ F_prop_initial, dtype=float).reshape(-1)
    if float(np.linalg.norm(F_prop_red)) <= 0.0:
        raise ValueError("Displacement control requires a non-zero proportional load vector")
    zero_load_tangent = sparse.csr_matrix(
        (model.mesh.dof_manager.total_dofs, model.mesh.dof_manager.total_dofs),
        dtype=float,
    )

    target_total = float(displacement_control.target_displacement)
    initial_control = float(row_red @ q + row_u0)
    target_increment = target_total - initial_control
    target_scale = max(abs(target_increment), abs(target_total), 1.0e-9)
    info["displacement_control_initial_value"] = initial_control

    assembly_threads = None if resource_config is None else resource_config.assembly_threads
    with numba_thread_scope(assembly_threads):
        for step_index in range(1, num_steps + 1):
            cancellation_safe_point(
                cancellation_token,
                f"nonlinear_static.displacement.step:{step_index}",
            )
            q_step_start = q.copy()
            lam_step_start = float(lam)
            target = initial_control + target_increment * step_index / num_steps
            residual_norm = float("inf")
            constraint_error = float("inf")
            states_new = committed_states

            for iteration in range(1, max_iterations + 1):
                cancellation_safe_point(
                    cancellation_token,
                    f"nonlinear_static.displacement.step:{step_index}.iteration:{iteration}",
                )
                total_iterations += 1
                u = np.asarray(T @ q + u0, dtype=float).reshape(-1)
                F_int, K_T, trial_states = _assemble_nonlinear_system(
                    model,
                    u,
                    committed_states,
                    num_layers,
                    kinematics=kinematics,
                    corotational_tangent=corotational_tangent,
                )
                if follower_active:
                    F_const_current, K_const = _weighted_external_load_system(
                        model,
                        constant_terms,
                        u,
                        tangent=True,
                    )
                    F_prop_current, K_prop = _weighted_external_load_system(
                        model,
                        [proportional_term],
                        u,
                        tangent=True,
                    )
                else:
                    F_const_current, F_prop_current = F_const_static, F_prop_static
                    K_const = K_prop = zero_load_tangent
                F_external = F_const_current + lam * F_prop_current
                residual = (
                    np.asarray(T.T @ F_external, dtype=float).reshape(-1)
                    - np.asarray(T.T @ F_int, dtype=float).reshape(-1)
                )
                residual_norm = float(np.linalg.norm(residual))
                current = float(row_red @ q + row_u0)
                constraint = target - current
                constraint_error = abs(constraint)
                reference = max(
                    float(
                        np.linalg.norm(
                            np.asarray(
                                T.T @ (F_const_current + max(abs(lam), 1.0) * F_prop_current),
                                dtype=float,
                            )
                        )
                    ),
                    1.0,
                )

                if residual_norm <= tolerance * reference and constraint_error <= tolerance * target_scale:
                    states_new = trial_states
                    break

                K_red = (
                    (T.T @ K_T @ T)
                    - (T.T @ K_const @ T)
                    - lam * (T.T @ K_prop @ T)
                ).tocsr()
                F_prop_red = np.asarray(T.T @ F_prop_current, dtype=float).reshape(-1)
                aug = sparse.bmat(
                    [
                        [K_red, sparse.csr_matrix((-F_prop_red).reshape(-1, 1))],
                        [sparse.csr_matrix(row_red.reshape(1, -1)), sparse.csr_matrix((1, 1))],
                    ],
                    format="csr",
                )
                rhs = np.concatenate([residual, np.array([constraint], dtype=float)])
                try:
                    with np.errstate(all="ignore"):
                        handle = factorize(
                            aug,
                            (
                                MatrixClass.GENERAL
                                if general_tangent
                                else MatrixClass.SYMMETRIC_INDEFINITE
                            ),
                            signature=f"nonlinear.displacement_control:{step_index}:{iteration}",
                        )
                        delta = np.asarray(handle.solve(rhs), dtype=float).reshape(-1)
                except Exception:
                    failure_reason = "singular_augmented_tangent"
                    break
                if np.any(~np.isfinite(delta)):
                    failure_reason = "nonfinite_augmented_solution"
                    break
                q += delta[:-1]
                lam += float(delta[-1])
            else:
                failure_reason = "maximum_iterations_reached"

            if failure_reason is not None:
                q = q_step_start
                lam = lam_step_start
                status = "stopped_at_limit" if steps else "diverged"
                break

            committed_states = states_new
            u = np.asarray(T @ q + u0, dtype=float).reshape(-1)
            current = float(row_red @ q + row_u0)
            steps.append(
                NonlinearStaticStep(
                    step_index=step_index,
                    load_factor=float(lam),
                    iterations=iteration,
                    residual_norm=residual_norm,
                    displacement_norm=float(np.linalg.norm(u)),
                    max_equivalent_plastic_strain=_max_plastic_strain(committed_states),
                    control_value=current,
                    active_stage=active_stage,
                )
            )
            history.append(
                {
                    "step_index": step_index,
                    "load_factor": float(lam),
                    "control_value": current,
                    "target_displacement": target,
                    "residual_norm": residual_norm,
                    "constraint_error": constraint_error,
                    "iterations": iteration,
                    "active_stage": active_stage,
                }
            )
            if record_increment_snapshots:
                snapshots.append(
                    _increment_snapshot(
                        step_index,
                        lam,
                        u,
                        committed_states,
                        control_value=current,
                    )
                )
            if progress_callback is not None:
                emit_progress(
                    progress_callback,
                    "nonlinear_static_step",
                    "nonlinear_static.displacement",
                    completed=step_index,
                    total=num_steps,
                    iteration=iteration,
                    control="displacement",
                    step_index=int(step_index),
                    load_factor=float(lam),
                    control_value=float(current),
                    displacement_norm=float(np.linalg.norm(u)),
                    max_equivalent_plastic_strain=float(_max_plastic_strain(committed_states)),
                )

    u_final = np.asarray(T @ q + u0, dtype=float).reshape(-1)
    committed_states = _finalize_nonlinear_element_states(
        model,
        u_final,
        committed_states,
        num_layers,
        kinematics=kinematics,
    )
    info["failure_reason"] = failure_reason
    info["stop_reason"] = "target_displacement_reached" if failure_reason is None else failure_reason
    info["status_category"] = _nonlinear_status_category(status, failure_reason)
    info["last_converged_load_factor"] = float(lam)
    info["peak_load_factor"] = max((step.load_factor for step in steps), default=float(lam))
    info["force_displacement_history"] = history
    info["strain_summary"] = _nonlinear_state_summary(committed_states)
    info["total_newton_iterations"] = total_iterations
    info["solve_time"] = time.time() - start_time
    info["constraint_postcheck"] = constraint_residual_summary(model, u_final)
    info["result_case"] = make_result_case(
        name="nonlinear_static_displacement_control",
        analysis_type="nonlinear_static",
        load_cases=tuple(stage.load_case for stage in load_program.stages) if load_program is not None else (),
        assembly_info={"load": {"vector_type": "load_program" if load_program is not None else "load"}, **info},
        solver_info={"convergence_info": {"status": status}},
        recovery={"displacements": True, "element_states": True, "force_displacement_history": True},
        settings={
            "control": "displacement",
            "num_steps": num_steps,
            "num_layers": num_layers,
            "kinematics": kinematics,
            "corotational_tangent": corotational_tangent,
        },
    ).to_dict()
    return NonlinearStaticResult(
        steps,
        status,
        u_final,
        float(lam),
        committed_states,
        info,
        tuple(snapshots),
    )


@resource_threaded
def solve_static_nonlinear(
    model: "FEModel",
    load_case: Optional["LoadCase"] = None,
    constant_load_case: Optional["LoadCase"] = None,
    max_load_factor: float = 1.0,
    num_steps: int = 10,
    max_iterations: int = 25,
    tolerance: float = 1.0e-6,
    num_layers: int = 5,
    min_step_fraction: float = 1.0 / 1024.0,
    imperfection: Optional[Any] = None,
    load_program: Optional[NonlinearLoadProgram] = None,
    control: str = "force",
    displacement_control: Optional[DisplacementControl] = None,
    initial_element_states: Optional[Mapping[int, Any]] = None,
    convergence_settings: Optional[Union[str, Mapping[str, Any], NonlinearConvergenceSettings]] = None,
    resource_config: Optional[ResourceConfig] = None,
    fracture_config: Optional[FractureConfig] = None,
    kinematics: str = "von_karman",
    corotational_tangent: str = "auto",
    status_callback: Optional[Callable[[str], None]] = None,
    progress_callback: Optional[ProgressCallback] = None,
    initial_fields: Optional[Mapping[int, Any]] = None,
    initial_displacements: Optional[np.ndarray] = None,
    equilibrate_initial_state: Optional[bool] = None,
    cancellation_token: Optional[CancellationToken] = None,
    record_increment_snapshots: bool = False,
) -> NonlinearStaticResult:
    """Incremental nonlinear static solve with adaptive load stepping.

    The proportional load case is ramped from 0 to ``max_load_factor`` while
    ``constant_load_case`` (if given) is applied in full from the first
    increment.  Plastic state is committed per element only on increment
    convergence, so every Newton iteration return-maps from the last
    converged state (standard backward-Euler incremental plasticity).

    ``kinematics="corotational"`` accepts ``corotational_tangent="rotated"``
    for the lower-cost historical approximation or ``"consistent"`` for the
    full generally nonsymmetric chain-rule Jacobian.  ``"auto"`` selects the
    consistent tangent whenever a supplied load case uses current-area
    follower pressure and otherwise preserves the rotated tangent.

    ``initial_fields`` maps element IDs to :class:`ShellInitialField` or
    :class:`BeamInitialField` values. New fields are equilibrated at zero
    external load by default. A true restart with field-bearing
    ``initial_element_states`` must also supply the matching
    ``initial_displacements``; alternatively pass
    ``equilibrate_initial_state=True`` to deliberately re-equilibrate the
    restored field from the supplied (or zero) displacement state.
    """
    cancellation_safe_point(cancellation_token, "nonlinear_static.start")
    if num_steps <= 0:
        raise ValueError("num_steps must be positive")
    control_name = str(control).lower()
    if control_name not in {"force", "displacement"}:
        raise ValueError("control must be 'force' or 'displacement'")
    kinematics = str(kinematics).lower()
    if kinematics not in {"von_karman", "corotational"}:
        raise ValueError("kinematics must be 'von_karman' or 'corotational'")
    specified_load_cases = [
        case
        for case in (
            [load_case, constant_load_case]
            + ([] if load_program is None else [stage.load_case for stage in load_program.stages])
        )
        if case is not None
    ]
    follower_active = any(_has_follower_pressure(case) for case in specified_load_cases)
    from .corotational import resolve_corotational_tangent_mode

    resolved_corotational_tangent = resolve_corotational_tangent_mode(
        kinematics,
        corotational_tangent,
        follower_pressure=follower_active,
    )
    if kinematics == "corotational":
        from .corotational import validate_corotational_scope

        validate_corotational_scope(model)
        if fracture_config is not None:
            raise ValueError("Corotational kinematics v1 does not support fracture/erosion")
        if follower_active and resolved_corotational_tangent != "consistent":
            raise NotImplementedError(
                "Follower pressure with corotational kinematics requires "
                "corotational_tangent='consistent'."
            )
    if max_load_factor <= 0.0:
        raise ValueError("max_load_factor must be positive")
    if fracture_config is not None and not isinstance(fracture_config, FractureConfig):
        raise TypeError("fracture_config must be a FractureConfig or None")
    settings = _coerce_convergence_settings(convergence_settings)
    if kinematics == "corotational" and settings.line_search in {"auto", "rescue"}:
        # Corotational Newton necessarily passes through a large intermediate
        # residual while the element frames rotate toward the new state;
        # residual-norm backtracking rejects that excursion and grinds the
        # increment adaptation.  Plain Newton converges in a few iterations.
        settings = dataclass_replace(settings, line_search="never")
    effective_min_step_fraction = settings.min_step_fraction if settings.min_step_fraction is not None else min_step_fraction

    start_time = time.time()
    if imperfection is not None:
        from .imperfections import apply_imperfection

        model = apply_imperfection(model, imperfection, copy_model=True)
    _ensure_nonlinear_acceleration()
    model.apply_boundary_conditions()

    # The constraint transformation only depends on supports/MPCs; the
    # elastic stiffness is assembled once to build it (and warms the element
    # caches used by the nonlinear kernels).
    K0, stiffness_info = assemble_stiffness_matrix(model)
    stage_vectors: List[np.ndarray] = []
    stage_infos: List[Dict[str, Any]] = []
    if load_program is not None:
        for stage in load_program.stages:
            vector, stage_info = assemble_load_vector(model, stage.load_case)
            stage_vectors.append(vector)
            stage_infos.append({"name": stage.name, "target_factor": stage.target_factor, **stage_info})
        F_prop = np.sum(np.vstack(stage_vectors), axis=0) if stage_vectors else np.zeros(K0.shape[0], dtype=float)
        load_info = {"vector_type": "load_program", "stages": stage_infos}
    else:
        F_prop, load_info = assemble_load_vector(model, load_case)

    if constant_load_case is not None:
        F_const, constant_load_info = assemble_load_vector(model, constant_load_case)
    else:
        F_const = np.zeros_like(F_prop)
        constant_load_info = None
    _, _, T, u0, _, constraint_info = build_constraint_transformation(K0, F_prop, model)

    info: Dict[str, Any] = {
        "stiffness": stiffness_info,
        "load": load_info,
        "constant_load": constant_load_info,
        "constraint_info": constraint_info,
        "num_layers": int(num_layers),
        "total_dofs": model.mesh.dof_manager.total_dofs,
        "reduced_dofs": int(T.shape[1]),
        "control": str(control),
        "kinematics": kinematics,
        "corotational_tangent_requested": str(corotational_tangent).lower(),
        "corotational_tangent": resolved_corotational_tangent,
        "follower_pressure": follower_active,
        "equilibrium_tangent": "K_internal-K_external" if follower_active else "K_internal",
        "convergence_settings": settings.to_dict(),
        "resource_config": None if resource_config is None else resource_config.to_dict(),
        "thread_policy": thread_policy_diagnostics(resource_config),
    }
    general_tangent = follower_active or (
        kinematics == "corotational"
        and resolved_corotational_tangent == "consistent"
    )
    imperfection_provenance: List[Dict[str, Any]] = []
    if imperfection is not None:
        imperfection_provenance = list(getattr(model, "imperfection_metadata", []))
        info["imperfection"] = imperfection_provenance

    committed_states, residual_field_provenance = _prepare_initial_states(
        model,
        initial_element_states,
        initial_fields,
        num_layers,
    )
    if kinematics == "corotational" and any(
        _state_has_initial_field(state) for state in committed_states.values()
    ):
        raise NotImplementedError(
            "Initial stress/prestrain fields are currently qualified only for "
            "kinematics='von_karman' in element-local reference coordinates."
        )
    info["initial_condition_provenance"] = {
        "geometric_imperfection": imperfection_provenance,
        "residual_stress_or_prestrain": residual_field_provenance,
        "coordinate_system": {
            "geometric_imperfection": "global nodal coordinates",
            "residual_stress_or_prestrain": "element-local reference coordinates",
        },
    }

    if fracture_config is not None and control_name != "force":
        raise ValueError("fracture_config is currently supported only with force control")

    n_red = int(T.shape[1])
    q = _reduced_coordinates(T, u0, initial_displacements)
    if (
        initial_fields
        and initial_displacements is not None
        and equilibrate_initial_state is not False
    ):
        raise ValueError(
            "initial_fields combined with initial_displacements is ambiguous during "
            "automatic equilibration; pass equilibrate_initial_state=False for an "
            "already-equilibrated restart."
        )
    if n_red == 0:
        has_initial_fields = any(
            _state_has_initial_field(state) for state in committed_states.values()
        )
        requested_equilibration = (
            bool(initial_fields)
            if equilibrate_initial_state is None
            else bool(equilibrate_initial_state)
        )
        info["initial_state_equilibration"] = {
            "requested": requested_equilibration,
            "converged": True,
            "iterations": 0,
            "history": [],
            "failure_reason": None,
            "free_dof_residual_norm": 0.0,
            "fully_constrained": True,
        }
        if has_initial_fields:
            # There are no admissible displacement corrections, so the
            # prescribed field is already equilibrated in the free-DOF
            # sense; its imbalance is carried entirely by reactions. Retain
            # the evaluated constitutive state and provenance in the result.
            internal_force, _unused_tangent, trial_states = (
                _assemble_nonlinear_system(
                    model,
                    np.asarray(u0, dtype=float).reshape(-1),
                    committed_states,
                    num_layers,
                    tangent=False,
                    kinematics=kinematics,
                    corotational_tangent=resolved_corotational_tangent,
                )
            )
            committed_states = trial_states
            info["initial_state_equilibration"][
                "constrained_internal_force_norm"
            ] = float(np.linalg.norm(internal_force))
            info["strain_summary"] = _nonlinear_state_summary(committed_states)
        info["failure_reason"] = "empty_reduced_system"
        info["stop_reason"] = "empty_reduced_system"
        info["status_category"] = _nonlinear_status_category("empty_reduced_system", "empty_reduced_system")
        info["result_case"] = make_result_case(
            name="nonlinear_static",
            analysis_type="nonlinear_static",
            load_cases=tuple(stage.load_case for stage in load_program.stages) if load_program is not None else (() if load_case is None else (load_case,)),
            assembly_info={"stiffness": stiffness_info, "load": load_info},
            solver_info={"convergence_info": {"status": "empty_reduced_system"}},
            recovery={"displacements": True, "element_states": True},
            settings={
                "control": control_name,
                "num_steps": num_steps,
                "num_layers": num_layers,
                "kinematics": kinematics,
                "corotational_tangent": resolved_corotational_tangent,
            },
        ).to_dict()
        return NonlinearStaticResult(
            [],
            "empty_reduced_system",
            u0.copy(),
            0.0,
            committed_states,
            info,
        )

    has_initial_fields = any(_state_has_initial_field(state) for state in committed_states.values())
    restored_initial_fields = has_initial_fields and not bool(initial_fields)
    if (
        restored_initial_fields
        and initial_displacements is None
        and equilibrate_initial_state is not True
    ):
        raise ValueError(
            "Field-bearing initial_element_states require matching "
            "initial_displacements for a restart. Pass "
            "equilibrate_initial_state=True only when re-equilibration from "
            "zero displacement is intended."
        )
    should_equilibrate = bool(initial_fields) if equilibrate_initial_state is None else bool(equilibrate_initial_state)
    if should_equilibrate and has_initial_fields:
        q, committed_states, initialization_history, initialization_failure = _equilibrate_initial_fields(
            model=model,
            T=T,
            u0=u0,
            committed_states=committed_states,
            num_layers=num_layers,
            max_iterations=max_iterations,
            tolerance=tolerance,
            kinematics=kinematics,
            corotational_tangent=resolved_corotational_tangent,
            general_tangent=general_tangent,
            initial_reduced_displacements=q,
            cancellation_token=cancellation_token,
        )
        info["initial_state_equilibration"] = {
            "requested": True,
            "converged": initialization_failure is None,
            "iterations": len(initialization_history),
            "history": initialization_history,
            "failure_reason": initialization_failure,
        }
        if initialization_failure is not None:
            u_failed = np.asarray(T @ q + u0, dtype=float).reshape(-1)
            info["failure_reason"] = initialization_failure
            info["stop_reason"] = initialization_failure
            info["status_category"] = _nonlinear_status_category("diverged", initialization_failure)
            info["strain_summary"] = _nonlinear_state_summary(committed_states)
            info["solve_time"] = time.time() - start_time
            return NonlinearStaticResult([], "diverged", u_failed, 0.0, committed_states, info)
    else:
        info["initial_state_equilibration"] = {
            "requested": should_equilibrate,
            "converged": True,
            "iterations": 0,
            "history": [],
            "failure_reason": None,
        }
    steps: List[NonlinearStaticStep] = []
    status = "completed"
    deleted_element_ids: set[int] = set()
    deletion_records: List[DeletedElementRecord] = []
    fracture_warnings: List[str] = []
    max_fracture_utilization = 0.0

    if load_program is not None and max_load_factor == 1.0:
        target_load_factor = load_program.total_factor
    else:
        target_load_factor = float(max_load_factor)

    def _active_load_case(case: Optional["LoadCase"]) -> Optional["LoadCase"]:
        if not deleted_element_ids:
            return case
        return filtered_load_case_for_deleted_elements(case, deleted_element_ids)

    def external_load_at(
        path_factor: float,
        displacements: np.ndarray,
        *,
        tangent: bool,
    ) -> Tuple[np.ndarray, Optional[sparse.csr_matrix], Dict[str, float], Optional[str]]:
        if not follower_active and not deleted_element_ids:
            if load_program is None:
                factors = {"proportional": float(path_factor)}
                force = F_const + float(path_factor) * F_prop
                active_stage = None
            else:
                factors = load_program.stage_factors(path_factor)
                force = F_const.copy()
                for stage, vector in zip(load_program.stages, stage_vectors):
                    force += factors[stage.name] * vector
                active_stage = load_program.active_stage(path_factor)
            zero_tangent = (
                sparse.csr_matrix((force.size, force.size), dtype=float)
                if tangent
                else None
            )
            return force, zero_tangent, factors, active_stage

        weighted_cases: List[Tuple[Optional["LoadCase"], float]] = [
            (_active_load_case(constant_load_case), 1.0)
        ]
        if load_program is None:
            factors = {"proportional": float(path_factor)}
            weighted_cases.append((_active_load_case(load_case), float(path_factor)))
            active_stage = None
        else:
            factors = load_program.stage_factors(path_factor)
            weighted_cases.extend(
                (_active_load_case(stage.load_case), factors[stage.name])
                for stage in load_program.stages
            )
            active_stage = load_program.active_stage(path_factor)
        force, load_tangent = _weighted_external_load_system(
            model,
            weighted_cases,
            displacements,
            tangent=tangent,
        )
        return force, load_tangent, factors, active_stage

    if control_name == "displacement":
        if displacement_control is None:
            raise ValueError("displacement_control is required when control='displacement'")
        preload_result: Optional[NonlinearStaticResult] = None
        if load_program is not None and len(load_program.stages) > 1:
            # Each permanent stage is first solved by force control and its
            # displacement/material state committed.  The final stage then
            # starts from that exact checkpoint under displacement control;
            # the earlier loads remain constant in the controlled equilibrium.
            preload_program = NonlinearLoadProgram(tuple(load_program.stages[:-1]))
            preload_result = solve_static_nonlinear(
                model,
                constant_load_case=constant_load_case,
                max_load_factor=preload_program.total_factor,
                num_steps=max(num_steps, len(preload_program.stages)),
                max_iterations=max_iterations,
                tolerance=tolerance,
                num_layers=num_layers,
                min_step_fraction=min_step_fraction,
                load_program=preload_program,
                control="force",
                initial_element_states=committed_states,
                initial_displacements=np.asarray(T @ q + u0, dtype=float).reshape(-1),
                equilibrate_initial_state=False,
                convergence_settings=settings,
                resource_config=resource_config,
                kinematics=kinematics,
                corotational_tangent=(
                    "auto" if kinematics == "von_karman" else resolved_corotational_tangent
                ),
                status_callback=status_callback,
                progress_callback=progress_callback,
                cancellation_token=cancellation_token,
                record_increment_snapshots=record_increment_snapshots,
            )
            if not preload_result.converged or (
                preload_result.load_factor < preload_program.total_factor - 1.0e-10
            ):
                preload_result.info["requested_control"] = "displacement"
                preload_result.info["failed_phase"] = "load_program_preload"
                preload_result.info["initial_condition_provenance"] = info[
                    "initial_condition_provenance"
                ]
                return preload_result
            committed_states = _copy_initial_states(preload_result.element_states)
            q = _reduced_coordinates(T, u0, preload_result.displacements)
            info["load_program_preload"] = {
                "status": preload_result.status,
                "load_factor": preload_result.load_factor,
                "stage_factors": preload_result.info.get("load_program_stage_factors", {}),
                "steps": len(preload_result.steps),
                "total_newton_iterations": preload_result.info.get("total_newton_iterations", 0),
                "strain_summary": preload_result.info.get("strain_summary", {}),
                "force_displacement_history": preload_result.info.get(
                    "force_displacement_history",
                    [],
                ),
            }
            info["material_history_reused_from_preload"] = True

        controlled_result = _solve_static_displacement_control(
            model=model,
            T=T,
            u0=u0,
            F_const=F_const,
            F_prop=F_prop,
            stage_vectors=stage_vectors,
            load_case=load_case,
            constant_load_case=constant_load_case,
            load_program=load_program,
            displacement_control=displacement_control,
            committed_states=committed_states,
            num_layers=num_layers,
            num_steps=num_steps,
            max_iterations=max_iterations,
            tolerance=tolerance,
            kinematics=kinematics,
            corotational_tangent=resolved_corotational_tangent,
            info=info,
            start_time=start_time,
            resource_config=resource_config,
            initial_reduced_displacements=q,
            cancellation_token=cancellation_token,
            progress_callback=progress_callback,
            record_increment_snapshots=record_increment_snapshots,
        )
        if load_program is not None:
            stage_factors = {
                stage.name: stage.target_factor
                for stage in load_program.stages[:-1]
            }
            stage_factors[load_program.stages[-1].name] = (
                controlled_result.load_factor * load_program.stages[-1].target_factor
            )
            controlled_result.info["load_program_stage_factors"] = stage_factors
        if preload_result is not None:
            preload_steps = [
                dataclass_replace(step, step_index=index)
                for index, step in enumerate(preload_result.steps, start=1)
            ]
            offset = len(preload_steps)
            controlled_steps = [
                dataclass_replace(step, step_index=offset + index)
                for index, step in enumerate(controlled_result.steps, start=1)
            ]
            controlled_result.steps = preload_steps + controlled_steps
            preload_snapshots = [
                dataclass_replace(snapshot, step_index=index)
                for index, snapshot in enumerate(preload_result.snapshots, start=1)
            ]
            controlled_snapshots = [
                dataclass_replace(snapshot, step_index=offset + index)
                for index, snapshot in enumerate(controlled_result.snapshots, start=1)
            ]
            controlled_result.snapshots = tuple(preload_snapshots + controlled_snapshots)
            controlled_result.info["total_newton_iterations"] = int(
                controlled_result.info.get("total_newton_iterations", 0)
            ) + int(preload_result.info.get("total_newton_iterations", 0))
        return controlled_result

    base_step = target_load_factor / num_steps
    min_step = max(float(effective_min_step_fraction) * base_step, 1.0e-12)
    max_step = max(base_step * settings.max_step_factor, min_step)
    step_size = base_step
    lam = 0.0
    step_index = 0
    total_iterations = 0
    stage_boundaries = (
        np.cumsum([stage.target_factor for stage in load_program.stages], dtype=float)
        if load_program is not None
        else np.empty(0, dtype=float)
    )

    prescribed_offset = np.asarray(u0, dtype=float).reshape(-1)
    info["prescribed_displacement_path"] = {
        "mode": "proportional_to_load_factor",
        "target_max_abs": float(np.max(np.abs(prescribed_offset)))
        if prescribed_offset.size
        else 0.0,
    }

    def full_displacement(q_reduced: np.ndarray, path_factor: float) -> np.ndarray:
        """Expand a force-control state on its affine constraint path."""
        return np.asarray(
            T @ q_reduced + float(path_factor) * prescribed_offset,
            dtype=float,
        ).reshape(-1)

    def newton_increment(q_start, path_factor, reference, line_search):
        """One load increment.  Plain full Newton when ``line_search`` is
        False (the fast path); backtracking-line-search Newton otherwise.
        Returns (converged, q, states, residual_norm, iterations_used, failure_reason).
        """
        nonlocal total_iterations
        cancellation_safe_point(
            cancellation_token,
            f"nonlinear_static.force.step:{step_index}.start",
        )
        q_trial = q_start.copy()
        u = full_displacement(q_trial, path_factor)
        F_int, K_T, trial_states = _assemble_nonlinear_system(
            model,
            u,
            committed_states,
            num_layers,
            kinematics=kinematics,
            corotational_tangent=resolved_corotational_tangent,
            deleted_element_ids=tuple(deleted_element_ids),
            residual_stiffness_fraction=(
                fracture_config.residual_stiffness_fraction if fracture_config is not None else 1.0
            ),
        )
        F_ext, K_ext, _stage_factors, _active_stage = external_load_at(
            path_factor,
            u,
            tangent=True,
        )
        residual = (
            np.asarray(T.T @ F_ext, dtype=float).reshape(-1)
            - np.asarray(T.T @ F_int, dtype=float).reshape(-1)
        )
        residual_norm = float(np.linalg.norm(residual))

        for iteration in range(1, max_iterations + 1):
            cancellation_safe_point(
                cancellation_token,
                f"nonlinear_static.force.step:{step_index}.iteration:{iteration}",
            )
            if status_callback:
                status_callback(f"\r  Step {step_index}/{num_steps}, Iteration {iteration}: Res {residual_norm:.2e}")
            total_iterations += 1
            if residual_norm <= tolerance * reference:
                return True, q_trial, trial_states, residual_norm, iteration, None

            K_red = ((T.T @ K_T @ T) - (T.T @ K_ext @ T)).tocsr()
            try:
                with np.errstate(all="ignore"):
                    handle = factorize(
                        K_red,
                        (
                            MatrixClass.GENERAL
                            if general_tangent
                            else MatrixClass.SYMMETRIC_INDEFINITE
                        ),
                        signature=f"nonlinear.static_newton:{lam:.16g}:{iteration}",
                    )
                    dq = np.asarray(handle.solve(residual), dtype=float).reshape(-1)
            except Exception:
                return False, q_start, committed_states, residual_norm, iteration, "singular_tangent_factorization"
            if np.any(~np.isfinite(dq)):
                return False, q_start, committed_states, residual_norm, iteration, "nonfinite_newton_increment"

            if not line_search:
                q_trial = q_trial + dq
                u = full_displacement(q_trial, path_factor)
                F_int, K_T, trial_states = _assemble_nonlinear_system(
                    model,
                    u,
                    committed_states,
                    num_layers,
                    kinematics=kinematics,
                    corotational_tangent=resolved_corotational_tangent,
                    deleted_element_ids=tuple(deleted_element_ids),
                    residual_stiffness_fraction=(
                        fracture_config.residual_stiffness_fraction if fracture_config is not None else 1.0
                    ),
                )
                F_ext, K_ext, _stage_factors, _active_stage = external_load_at(
                    path_factor,
                    u,
                    tangent=True,
                )
                residual = (
                    np.asarray(T.T @ F_ext, dtype=float).reshape(-1)
                    - np.asarray(T.T @ F_int, dtype=float).reshape(-1)
                )
                residual_norm = float(np.linalg.norm(residual))
                if not np.isfinite(residual_norm):
                    return False, q_start, committed_states, residual_norm, iteration, "nonfinite_residual"
                continue

            # Backtracking line search on the residual norm.  Von Karman
            # membrane terms can make full Newton steps overshoot violently
            # when an iterate moves many plate thicknesses at once; halving
            # until the residual decreases restores global convergence.
            # Rejected trials skip the tangent assembly (residual only).
            accepted = False
            scale = 1.0
            for trial in range(settings.max_line_search_cuts):
                cancellation_safe_point(
                    cancellation_token,
                    f"nonlinear_static.force.step:{step_index}.line_search:{trial + 1}",
                )
                q_candidate = q_trial + scale * dq
                u = full_displacement(q_candidate, path_factor)
                with_tangent = trial == 0
                F_c, K_c, states_c = _assemble_nonlinear_system(
                    model,
                    u,
                    committed_states,
                    num_layers,
                    tangent=with_tangent,
                    kinematics=kinematics,
                    corotational_tangent=resolved_corotational_tangent,
                    deleted_element_ids=tuple(deleted_element_ids),
                    residual_stiffness_fraction=(
                        fracture_config.residual_stiffness_fraction if fracture_config is not None else 1.0
                    ),
                )
                F_ext_c, K_ext_c, _stage_factors, _active_stage = external_load_at(
                    path_factor,
                    u,
                    tangent=with_tangent,
                )
                r_c = (
                    np.asarray(T.T @ F_ext_c, dtype=float).reshape(-1)
                    - np.asarray(T.T @ F_c, dtype=float).reshape(-1)
                )
                rn_c = float(np.linalg.norm(r_c))
                if np.isfinite(rn_c) and rn_c < residual_norm:
                    if not with_tangent:
                        F_c, K_c, states_c = _assemble_nonlinear_system(
                            model,
                            u,
                            committed_states,
                            num_layers,
                            tangent=True,
                            kinematics=kinematics,
                            corotational_tangent=resolved_corotational_tangent,
                            deleted_element_ids=tuple(deleted_element_ids),
                            residual_stiffness_fraction=(
                                fracture_config.residual_stiffness_fraction if fracture_config is not None else 1.0
                            ),
                        )
                        F_ext_c, K_ext_c, _stage_factors, _active_stage = external_load_at(
                            path_factor,
                            u,
                            tangent=True,
                        )
                        r_c = (
                            np.asarray(T.T @ F_ext_c, dtype=float).reshape(-1)
                            - np.asarray(T.T @ F_c, dtype=float).reshape(-1)
                        )
                        rn_c = float(np.linalg.norm(r_c))
                    q_trial = q_candidate
                    F_int, K_T, trial_states = F_c, K_c, states_c
                    K_ext = K_ext_c
                    residual, residual_norm = r_c, rn_c
                    accepted = True
                    break
                scale *= settings.line_search_reduction
            if not accepted:
                return False, q_start, committed_states, residual_norm, iteration, "line_search_failed"

        return False, q_start, committed_states, residual_norm, max_iterations, "maximum_iterations_reached"

    force_displacement_history: List[Dict[str, Any]] = []
    convergence_adaptation: List[Dict[str, Any]] = []
    snapshots: List[NonlinearIncrementSnapshot] = []
    force_line_search_next = False

    assembly_threads = None if resource_config is None else resource_config.assembly_threads
    with numba_thread_scope(assembly_threads):
        while lam < target_load_factor - 1.0e-12:
            cancellation_safe_point(
                cancellation_token,
                f"nonlinear_static.force.step:{step_index + 1}",
            )
            step_size = min(step_size, max(target_load_factor - lam, min_step))
            next_stage_boundary = target_load_factor
            for boundary in stage_boundaries:
                if boundary > lam + 1.0e-12:
                    next_stage_boundary = min(float(boundary), target_load_factor)
                    break
            # Never jump across a cumulative stage boundary.  Converging and
            # committing that endpoint is what makes the permanent-to-
            # environmental material path independent of adaptive step growth.
            lam_trial = min(lam + step_size, target_load_factor, next_stage_boundary)
            attempted_step_size = lam_trial - lam
            u_start = full_displacement(q, lam_trial)
            F_ext, _K_ext, stage_factors, active_stage = external_load_at(
                lam_trial,
                u_start,
                tangent=False,
            )
            F_ext_red = np.asarray(T.T @ F_ext, dtype=float).reshape(-1)
            reference = max(float(np.linalg.norm(F_ext_red)), 1.0)

            policy = settings.line_search
            line_search_first = policy == "always" or (
                policy == "auto" and (force_line_search_next or attempted_step_size > base_step * 1.000001)
            )
            converged, q_new, states_new, residual_norm, iterations_used, failure_reason = newton_increment(
                q, lam_trial, reference, line_search=line_search_first
            )
            line_search_used = bool(line_search_first)
            if not converged and not line_search_first and policy in {"rescue", "auto", "always"}:
                # Rescue retry with globalized (line-search) Newton before
                # cutting the load increment.
                converged, q_new, states_new, residual_norm, extra, failure_reason = newton_increment(
                    q, lam_trial, reference, line_search=True
                )
                iterations_used += extra
                line_search_used = True

            if converged:
                q = q_new
                lam = lam_trial
                committed_states = states_new
                force_line_search_next = False
                step_index += 1
                u = full_displacement(q, lam)
                control_value = float(np.linalg.norm(u))
                new_records: Tuple[DeletedElementRecord, ...] = ()
                if fracture_config is not None:
                    new_records, step_fracture_utilization = detect_new_deletions(
                        model,
                        committed_states,
                        fracture_config,
                        deleted_element_ids,
                        step_index=step_index,
                        load_factor=float(lam),
                    )
                    max_fracture_utilization = max(max_fracture_utilization, step_fracture_utilization)
                    if new_records:
                        deletion_records.extend(new_records)
                        deleted_element_ids.update(record.element_id for record in new_records)
                        warning = mpc_warning_for_deleted_shells(model, (record.element_id for record in new_records))
                        if warning is not None and warning not in fracture_warnings:
                            fracture_warnings.append(warning)
                steps.append(
                    NonlinearStaticStep(
                        step_index=step_index,
                        load_factor=float(lam),
                        iterations=iterations_used,
                        residual_norm=residual_norm,
                        displacement_norm=float(np.linalg.norm(u)),
                        max_equivalent_plastic_strain=_max_plastic_strain(committed_states),
                        control_value=control_value,
                        active_stage=active_stage,
                        deleted_element_count=len(deleted_element_ids),
                        max_fracture_utilization=max_fracture_utilization,
                    )
                )
                removed_load = np.zeros(3, dtype=float)
                if fracture_config is not None and deleted_element_ids:
                    if load_program is None:
                        removed_load += float(lam) * deleted_pressure_load_resultant(
                            model,
                            load_case,
                            deleted_element_ids,
                            u,
                        )
                    else:
                        for stage in load_program.stages:
                            removed_load += stage_factors[stage.name] * deleted_pressure_load_resultant(
                                model,
                                stage.load_case,
                                deleted_element_ids,
                                u,
                            )
                    if constant_load_case is not None:
                        removed_load += deleted_pressure_load_resultant(
                            model,
                            constant_load_case,
                            deleted_element_ids,
                            u,
                        )
                force_displacement_history.append(
                    {
                        "step_index": step_index,
                        "load_factor": float(lam),
                        "control_value": control_value,
                        "displacement_norm": float(np.linalg.norm(u)),
                        "residual_norm": residual_norm,
                        "iterations": iterations_used,
                        "step_size": float(attempted_step_size),
                        "line_search_used": line_search_used,
                        "stage_factors": stage_factors,
                        "active_stage": active_stage,
                        "stage_endpoint_committed": bool(
                            np.any(np.isclose(lam, stage_boundaries, rtol=0.0, atol=1.0e-12))
                        ),
                        "deleted_element_count": len(deleted_element_ids),
                        "newly_deleted_element_ids": [record.element_id for record in new_records],
                        "max_fracture_utilization": max_fracture_utilization,
                        "deleted_pressure_force_resultant": removed_load.tolist(),
                    }
                )
                if record_increment_snapshots:
                    snapshots.append(
                        _increment_snapshot(
                            step_index,
                            lam,
                            u,
                            committed_states,
                            control_value=control_value,
                        )
                    )
                if progress_callback is not None:
                    max_translation = 0.0
                    size = int(u.size)
                    for node in model.mesh.nodes.values():
                        dofs = np.asarray(node.dofs[:3], dtype=np.intp)
                        if dofs.size == 0 or int(dofs.max()) >= size:
                            continue
                        value = float(np.linalg.norm(u[dofs]))
                        if value > max_translation:
                            max_translation = value
                    emit_progress(
                        progress_callback,
                        "nonlinear_static_step",
                        "nonlinear_static.force",
                        completed=float(lam),
                        total=float(target_load_factor),
                        iteration=int(iterations_used),
                        control="force",
                        step_index=int(step_index),
                        load_factor=float(lam),
                        displacement_norm=float(np.linalg.norm(u)),
                        max_translation=float(max_translation),
                        iterations=int(iterations_used),
                        max_equivalent_plastic_strain=float(_max_plastic_strain(committed_states)),
                    )
                if fracture_config is not None and deleted_element_ids:
                    scoped_total = sum(
                        1
                        for element in model.mesh.elements.values()
                        if element_fracture_category(element) in fracture_config.element_scope
                    )
                    deleted_fraction = len(deleted_element_ids) / max(scoped_total, 1)
                    if deleted_fraction > fracture_config.max_deleted_fraction + 1.0e-12:
                        status = "stopped_at_limit"
                        info["failure_reason"] = "max_deleted_fraction_reached"
                        info["deleted_fraction"] = float(deleted_fraction)
                        break
                next_step = step_size
                action = "keep"
                if iterations_used <= settings.fast_iterations and step_size < max_step:
                    next_step = min(step_size * settings.growth_factor, max_step)
                    action = "grow"
                elif iterations_used >= settings.slow_iterations:
                    next_step = max(step_size * settings.cutback_factor, min_step)
                    action = "shrink_after_slow_convergence"
                    if policy == "auto":
                        force_line_search_next = True
                convergence_adaptation.append(
                    {
                        "step_index": step_index,
                        "load_factor": float(lam),
                        "iterations": int(iterations_used),
                        "line_search_used": line_search_used,
                        "attempted_step_size": float(attempted_step_size),
                        "next_step_size": float(next_step),
                        "action": action,
                    }
                )
                step_size = next_step
            else:
                if fracture_config is not None and deleted_element_ids and failure_reason in {
                    "singular_tangent_factorization",
                    "maximum_iterations_reached",
                    "line_search_failed",
                }:
                    failure_reason = "fracture_instability"
                    status = "stopped_at_limit" if steps else "diverged"
                    info["failure_reason"] = failure_reason
                    info["first_failed_load_factor"] = float(lam_trial)
                    info["first_failed_step_size"] = float(attempted_step_size)
                    break
                previous_step_size = step_size
                step_size *= 0.5
                force_line_search_next = True
                convergence_adaptation.append(
                    {
                        "step_index": step_index + 1,
                        "load_factor": float(lam_trial),
                        "iterations": int(iterations_used),
                        "line_search_used": line_search_used,
                        "attempted_step_size": float(attempted_step_size),
                        "next_step_size": float(step_size),
                        "action": "cutback_after_nonconvergence",
                        "previous_step_size": float(previous_step_size),
                        "residual_norm": float(residual_norm),
                    }
                )
                if step_size < min_step:
                    status = "stopped_at_limit" if steps else "diverged"
                    info["failure_reason"] = "minimum_load_increment_reached"
                    info["first_failed_load_factor"] = float(lam_trial)
                    info["first_failed_step_size"] = float(attempted_step_size)
                    info["first_failed_iteration_reason"] = failure_reason
                    break

    u_final = full_displacement(q, lam)
    committed_states = _finalize_nonlinear_element_states(
        model,
        u_final,
        committed_states,
        num_layers,
        kinematics=kinematics,
    )
    if "failure_reason" not in info and status == "completed":
        info["failure_reason"] = None
    failure_reason = info.get("failure_reason")
    info["stop_reason"] = "target_load_factor_reached" if failure_reason is None else failure_reason
    info["status_category"] = _nonlinear_status_category(status, failure_reason)
    info["last_converged_load_factor"] = float(lam)
    info["peak_load_factor"] = max((step.load_factor for step in steps), default=float(lam))
    info["force_displacement_history"] = force_displacement_history
    info["convergence_adaptation"] = convergence_adaptation
    info["strain_summary"] = _nonlinear_state_summary(committed_states)
    if fracture_config is not None:
        info["fracture_summary"] = fracture_summary(
            model,
            fracture_config,
            deletion_records,
            deleted_element_ids,
            max_utilization=max_fracture_utilization,
            warnings=fracture_warnings,
        )
    if load_program is not None:
        info["load_program_stage_factors"] = load_program.stage_factors(lam)
    info["total_newton_iterations"] = total_iterations
    info["solve_time"] = time.time() - start_time
    info["constraint_postcheck"] = constraint_residual_summary(model, u_final)
    info["result_case"] = make_result_case(
        name="nonlinear_static",
        analysis_type="nonlinear_static",
        load_cases=tuple(stage.load_case for stage in load_program.stages) if load_program is not None else (() if load_case is None else (load_case,)),
        assembly_info={"stiffness": stiffness_info, "load": load_info},
        solver_info={"convergence_info": {"status": status}},
        recovery={"displacements": True, "element_states": True, "force_displacement_history": True},
        settings={
            "control": control_name,
            "max_load_factor": max_load_factor,
            "num_steps": num_steps,
            "num_layers": num_layers,
            "kinematics": kinematics,
            "corotational_tangent": resolved_corotational_tangent,
            "convergence_settings": settings.to_dict(),
            "fracture": None if fracture_config is None else fracture_config.to_dict(),
        },
    ).to_dict()
    return NonlinearStaticResult(
        steps,
        status,
        u_final,
        float(lam),
        committed_states,
        info,
        tuple(snapshots),
    )
