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
import threading
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
from .current_state_tangent import (
    _guarded_owned_input_snapshot as _guarded_owned_nonlinear_snapshot,
    require_exact_qualified_component_lifecycle_api as _EXACT_QUALIFIED_LIFECYCLE_GUARD,
)
from .e4_pl_element import QualifiedE4PLShellElement as _QualifiedE4PLShellElement
from .e4_pl_s3_element import (
    QualifiedE4PLS3ShellElement as _QualifiedE4PLS3ShellElement,
)
from .element_capabilities import (
    require_model_element_capabilities,
    require_model_nonlinear_workflow_capabilities,
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
from .initial_field_state import state_has_active_initial_fields
from .jit_compiler import numba_thread_scope
from .matrix_assembly import (
    _run_with_qualified_assembly_runtime_lease,
    _scatter_element_matrix,
    _triplets_to_csr,
    assemble_external_load_system,
    assemble_load_vector,
    assemble_stiffness_matrix,
)
from .nonlinear_analysis_diagnostics import (
    capture_nonlinear_analysis_diagnostics,
    record_nonlinear_assembly_execution,
)
from .nonlinear_state import (
    NonlinearStateStore,
    StateMaterializationPolicy,
    StateTransactionError,
    commit_state_candidate,
    discard_active_state_candidate,
    materialize_state_mapping,
)
from .nonlinear_restart import (
    canonical_checkpoint_json_bytes,
    create_nonlinear_checkpoint,
    load_case_descriptor,
    load_nonlinear_checkpoint,
    validate_nonlinear_checkpoint,
)
from .recovery import ResourceConfig, _owned_resource_config_snapshot
from .threading_policy import resource_threaded, thread_policy_diagnostics

if TYPE_CHECKING:
    from .boundary import LoadCase
    from .fe_core import FEModel


_DOF_INDEX = {"ux": 0, "uy": 1, "uz": 2, "rx": 3, "ry": 4, "rz": 5}
_FAST_NL_BOOTSTRAPPED = False
_FAST_NL_BOOTSTRAP_ERROR: Optional[str] = None
_FAST_NL_BOOTSTRAP_LOCK = threading.RLock()
_INITIAL_FIELD_STATE_KEYS = (
    "initial_membrane_stress",
    "initial_bending_stress",
    "initial_membrane_prestrain",
    "initial_curvature_prestrain",
    "initial_fiber_stress",
    "initial_fiber_prestrain",
)
_Q4_COMMITTED_BINDING_KEY = "qualified_q4_committed_binding"
_Q4_COMMITTED_INTEGRITY_KEY = "state_integrity_sha256"
_Q4_ACTIVITY_DISPOSITION_KEY = "qualified_q4_activity_disposition"
_Q4_COMMITTED_STATE_LIFECYCLE_SCHEMA = (
    "ANYSOLVER_Q4_COMMITTED_STATE_LIFECYCLE_V1"
)
_S3_ACTIVITY_DISPOSITION_KEY = "qualified_s3_activity_disposition"
_S3_COMMITTED_STATE_LIFECYCLE_SCHEMA = (
    "ANYSOLVER_S3_COMMITTED_STATE_LIFECYCLE_V1"
)


def _ensure_nonlinear_acceleration() -> None:
    """Install optional nonlinear acceleration on first nonlinear use."""

    global _FAST_NL_BOOTSTRAPPED, _FAST_NL_BOOTSTRAP_ERROR
    if _FAST_NL_BOOTSTRAPPED:
        return
    with _FAST_NL_BOOTSTRAP_LOCK:
        if _FAST_NL_BOOTSTRAPPED:
            return
        _FAST_NL_BOOTSTRAP_ERROR = None
        if os.environ.get("FE_SOLVER_DISABLE_FAST_NL", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }:
            _FAST_NL_BOOTSTRAPPED = True
            return
        try:
            from .nonlinear_performance_bootstrap import (
                install_nonlinear_performance_optimizations,
            )

            install_nonlinear_performance_optimizations()
        except Exception as exc:  # Optional acceleration must not disable the solver.
            _FAST_NL_BOOTSTRAP_ERROR = f"{type(exc).__name__}: {exc}"
        finally:
            # Publish completion only after the composite install attempt has
            # finished, so another first-use caller cannot observe a partially
            # patched nonlinear stack.
            _FAST_NL_BOOTSTRAPPED = True


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


def _coerce_convergence_settings(
    value: Optional[
        Union[str, Mapping[str, Any], NonlinearConvergenceSettings]
    ],
    *,
    _post_observation: Optional[Callable[[], Any]] = None,
) -> NonlinearConvergenceSettings:
    def observed() -> None:
        if _post_observation is not None:
            _post_observation()

    if value is None:
        return NonlinearConvergenceSettings.for_profile("auto")
    if isinstance(value, NonlinearConvergenceSettings):
        observed()
        return value
    if isinstance(value, str):
        result = NonlinearConvergenceSettings.for_profile(value)
        observed()
        return result
    if isinstance(value, Mapping):
        data = dict(value)
        observed()
        profile = str(data.pop("profile", "auto")).lower()
        observed()
        base = NonlinearConvergenceSettings.for_profile(profile).to_dict()
        base.update(data)
        observed()
        result = NonlinearConvergenceSettings(**base)
        observed()
        return result
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
    support_reactions: Dict[str, Tuple[float, ...]] = field(default_factory=dict)

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
            "support_reactions": {
                str(name): [float(value) for value in values]
                for name, values in self.support_reactions.items()
            },
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
    if isinstance(element_states, NonlinearStateStore):
        element_states = element_states.materialize_owned(
            policy=StateMaterializationPolicy.SAVED_STATE
        )
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
    restart_checkpoint: Optional[Dict[str, Any]] = field(default=None, repr=False)

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
        payload = {
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
        if self.restart_checkpoint is not None:
            payload["restart_checkpoint"] = {
                "schema": self.restart_checkpoint["schema"],
                "version": self.restart_checkpoint["version"],
                "analysis_kind": self.restart_checkpoint["analysis_kind"],
                "checkpoint_sha256": self.restart_checkpoint["checkpoint_sha256"],
            }
        return payload

    def to_restart_checkpoint(self) -> Dict[str, Any]:
        """Return an owned complete checkpoint of the last committed step."""

        if self.restart_checkpoint is None:
            raise ValueError("this result does not contain a nonlinear restart checkpoint")
        return copy.deepcopy(self.restart_checkpoint)

    def restart_checkpoint_bytes(self) -> bytes:
        """Return the complete checkpoint as strict canonical JSON."""

        return canonical_checkpoint_json_bytes(self.to_restart_checkpoint())

    @property
    def quantity_metadata(self) -> Tuple[Any, ...]:
        from .quantities import describe_result_quantities

        return describe_result_quantities(self)


def _static_restart_analysis_contract(
    *,
    model: "FEModel",
    load_case: Optional["LoadCase"],
    constant_load_case: Optional["LoadCase"],
    load_program: Optional[NonlinearLoadProgram],
    control_name: str,
    displacement_control: Optional[DisplacementControl],
    num_layers: int,
    max_iterations: int,
    tolerance: float,
    effective_min_step_fraction: float,
    settings: NonlinearConvergenceSettings,
    fracture_config: Optional[FractureConfig],
    resource_config: Optional[ResourceConfig],
    kinematics: str,
    resolved_corotational_tangent: str,
) -> Dict[str, Any]:
    """Return invariant inputs required to continue the same static path.

    Target load/displacement and the number of additional increments are
    intentionally excluded.  The checkpoint owns the accepted path position
    and adaptive increment state; a resumed call may extend that same path.
    """

    if load_program is None:
        stages: List[Dict[str, Any]] = []
    else:
        stages = [
            {
                "name": stage.name,
                "target_factor": float(stage.target_factor),
                "load_case": load_case_descriptor(stage.load_case),
            }
            for stage in load_program.stages
        ]
    control_descriptor: Optional[Dict[str, Any]] = None
    if control_name == "displacement":
        if displacement_control is None:
            raise ValueError("displacement_control is required when control='displacement'")
        control_descriptor = {
            # The row defines the physical continuation coordinate.  Its new
            # target is deliberately not part of the invariant contract.
            "full_row": displacement_control.full_row(model).tolist(),
        }
    return {
        "schema": "ANYSOLVER_STATIC_RESTART_CONTRACT_V1",
        "control": control_name,
        "load_case": load_case_descriptor(load_case),
        "constant_load_case": load_case_descriptor(constant_load_case),
        "load_program": stages,
        "displacement_control": control_descriptor,
        "num_layers": int(num_layers),
        "max_iterations": int(max_iterations),
        "tolerance": float(tolerance),
        "effective_min_step_fraction": float(effective_min_step_fraction),
        "convergence_settings": settings.to_dict(),
        "fracture_config": (
            None if fracture_config is None else fracture_config.to_dict()
        ),
        "resource_config": (
            None if resource_config is None else resource_config.to_dict()
        ),
        "kinematics": str(kinematics),
        "corotational_tangent": str(resolved_corotational_tangent),
    }


def _static_step_from_restart(value: Any) -> NonlinearStaticStep:
    if not isinstance(value, Mapping):
        raise ValueError("checkpoint static step must be a mapping")
    expected = {
        "step_index",
        "load_factor",
        "iterations",
        "residual_norm",
        "displacement_norm",
        "max_equivalent_plastic_strain",
        "control_value",
        "active_stage",
        "deleted_element_count",
        "max_fracture_utilization",
        "support_reactions",
    }
    if set(value) != expected:
        raise ValueError("checkpoint static step schema is incompatible")
    reactions = value["support_reactions"]
    if not isinstance(reactions, Mapping):
        raise ValueError("checkpoint static step reactions must be a mapping")
    return NonlinearStaticStep(
        step_index=int(value["step_index"]),
        load_factor=float(value["load_factor"]),
        iterations=int(value["iterations"]),
        residual_norm=float(value["residual_norm"]),
        displacement_norm=float(value["displacement_norm"]),
        max_equivalent_plastic_strain=float(value["max_equivalent_plastic_strain"]),
        control_value=(
            None if value["control_value"] is None else float(value["control_value"])
        ),
        active_stage=(
            None if value["active_stage"] is None else str(value["active_stage"])
        ),
        deleted_element_count=int(value["deleted_element_count"]),
        max_fracture_utilization=float(value["max_fracture_utilization"]),
        support_reactions={
            str(name): tuple(float(item) for item in components)
            for name, components in reactions.items()
        },
    )


def _restore_static_path_state(
    value: Mapping[str, Any],
    *,
    control_name: str,
    n_red: Optional[int] = None,
    total_dofs: Optional[int] = None,
) -> Dict[str, Any]:
    """Validate static continuation state before solver assembly."""

    if not isinstance(value, Mapping):
        raise ValueError("static checkpoint path_state must be a mapping")
    common = {
        "mode",
        "load_factor",
        "step_index",
        "total_iterations",
        "steps",
        "force_displacement_history",
        "reduced_coordinates",
        "terminal_status",
        "failure_reason",
    }
    expected = (
        common
        | {
            "base_step",
            "minimum_step",
            "maximum_step",
            "next_step_size",
            "force_line_search_next",
            "convergence_adaptation",
            "deletion_records",
            "fracture_warnings",
            "max_fracture_utilization",
            "affine_path_mode",
            "exact_base_offset",
        }
        if control_name == "force"
        else common
    )
    legacy_expected = (
        expected - {"affine_path_mode", "exact_base_offset"}
        if control_name == "force"
        else expected
    )
    if frozenset(value) not in {
        frozenset(expected),
        frozenset(legacy_expected),
    } or value.get("mode") != control_name:
        raise ValueError("static checkpoint path schema is incompatible")
    steps_raw = value["steps"]
    history = value["force_displacement_history"]
    if not isinstance(steps_raw, list) or not isinstance(history, list):
        raise ValueError("static checkpoint histories must be lists")
    steps = [_static_step_from_restart(item) for item in steps_raw]
    step_index = int(value["step_index"])
    if step_index < 0 or len(steps) != step_index:
        raise ValueError("static checkpoint step count is inconsistent")
    if len(history) != step_index:
        raise ValueError("static checkpoint force/displacement history is incomplete")
    if [step.step_index for step in steps] != list(range(1, step_index + 1)):
        raise ValueError("static checkpoint step ordering is inconsistent")
    load_factor = float(value["load_factor"])
    if steps and steps[-1].load_factor != load_factor:
        raise ValueError("static checkpoint load factor differs from its last step")
    restored: Dict[str, Any] = {
        "mode": control_name,
        "load_factor": load_factor,
        "step_index": step_index,
        "total_iterations": int(value["total_iterations"]),
        "steps": steps,
        "force_displacement_history": copy.deepcopy(history),
        "terminal_status": str(value["terminal_status"]),
        "failure_reason": (
            None if value["failure_reason"] is None else str(value["failure_reason"])
        ),
    }
    reduced_coordinates = np.asarray(value["reduced_coordinates"], dtype=float)
    if (
        reduced_coordinates.ndim != 1
        or not np.all(np.isfinite(reduced_coordinates))
        or (n_red is not None and reduced_coordinates.shape != (int(n_red),))
    ):
        raise ValueError("static checkpoint reduced coordinates are incompatible")
    restored["reduced_coordinates"] = reduced_coordinates.copy()
    if restored["total_iterations"] < 0:
        raise ValueError("static checkpoint iteration count is invalid")
    if control_name == "force":
        from .fracture import DeletedElementRecord

        deletion_records_raw = value["deletion_records"]
        if not isinstance(deletion_records_raw, list):
            raise ValueError("static checkpoint deletion records must be a list")
        deletion_records = [
            DeletedElementRecord(**record) for record in deletion_records_raw
        ]
        deletion_ids = [int(record.element_id) for record in deletion_records]
        if len(deletion_ids) != len(set(deletion_ids)):
            raise ValueError("static checkpoint deletion records contain duplicate IDs")
        for record in deletion_records:
            record_step = int(record.step_index)
            if record_step < 1 or record_step > len(steps):
                raise ValueError(
                    "static checkpoint deletion step lies outside its history"
                )
            if float(record.load_factor) != float(
                steps[record_step - 1].load_factor
            ):
                raise ValueError(
                    "static checkpoint deletion load factor differs from its step"
                )
        for step in steps:
            cumulative_deleted = sum(
                int(record.step_index) <= int(step.step_index)
                for record in deletion_records
            )
            if int(step.deleted_element_count) != cumulative_deleted:
                raise ValueError(
                    "static checkpoint cumulative deletion history is inconsistent"
                )
        if steps and steps[-1].deleted_element_count != len(deletion_ids):
            raise ValueError("static checkpoint deletion count differs from its last step")
        restored.update(
            {
                "base_step": float(value["base_step"]),
                "minimum_step": float(value["minimum_step"]),
                "maximum_step": float(value["maximum_step"]),
                "next_step_size": float(value["next_step_size"]),
                "force_line_search_next": bool(value["force_line_search_next"]),
                "convergence_adaptation": copy.deepcopy(value["convergence_adaptation"]),
                "deletion_records": deletion_records,
                "fracture_warnings": [str(item) for item in value["fracture_warnings"]],
                "max_fracture_utilization": float(value["max_fracture_utilization"]),
                "affine_path_mode": value.get("affine_path_mode"),
                "exact_base_offset": (
                    None
                    if value.get("exact_base_offset") is None
                    else np.asarray(
                        value["exact_base_offset"], dtype=np.float64
                    ).copy()
                ),
            }
        )
        affine_mode = restored["affine_path_mode"]
        exact_base = restored["exact_base_offset"]
        if affine_mode is not None and affine_mode not in {
            "PROPORTIONAL_PRESCRIBED_FIELD",
            "FIXED_RESTART_AFFINE_STATE",
        }:
            raise ValueError("static checkpoint affine path mode is incompatible")
        if exact_base is not None and (
            exact_base.ndim != 1
            or not np.all(np.isfinite(exact_base))
            or (
                total_dofs is not None
                and exact_base.shape != (int(total_dofs),)
            )
        ):
            raise ValueError("static checkpoint exact base offset is incompatible")
        if (affine_mode is None) != (exact_base is None):
            raise ValueError("static checkpoint affine path state is incomplete")
        positive_names = ("base_step", "minimum_step", "maximum_step", "next_step_size")
        if any(restored[name] <= 0.0 for name in positive_names):
            raise ValueError("static checkpoint adaptive step sizes must be positive")
        if restored["minimum_step"] > restored["maximum_step"]:
            raise ValueError("static checkpoint adaptive step bounds are inconsistent")
        if not isinstance(restored["convergence_adaptation"], list):
            raise ValueError("static checkpoint convergence history must be a list")
    return restored


def _static_restart_path_payload(
    *,
    control_name: str,
    load_factor: float,
    step_index: int,
    total_iterations: int,
    steps: Sequence[NonlinearStaticStep],
    force_displacement_history: Sequence[Mapping[str, Any]],
    reduced_coordinates: np.ndarray,
    terminal_status: str,
    failure_reason: Optional[str],
    **force_values: Any,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "mode": str(control_name),
        "load_factor": float(load_factor),
        "step_index": int(step_index),
        "total_iterations": int(total_iterations),
        "steps": [step.to_dict() for step in steps],
        "force_displacement_history": copy.deepcopy(list(force_displacement_history)),
        "reduced_coordinates": np.asarray(
            reduced_coordinates, dtype=float
        ).reshape(-1).tolist(),
        "terminal_status": str(terminal_status),
        "failure_reason": None if failure_reason is None else str(failure_reason),
    }
    if control_name == "force":
        payload.update(force_values)
    return payload


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


def _has_follower_pressure(
    load_case: Optional["LoadCase"],
    *,
    model: Optional["FEModel"] = None,
    _exact_guard: Any = None,
) -> bool:
    """Whether a load case contains current-area pressure.

    A custom mapping or descriptor may execute caller code while the policy is
    observed.  Qualified orchestration passes its original non-renewable guard
    so no subsequent load-case or model observation can occur after a
    transient authority mutation.
    """

    def observed(context: str) -> None:
        if _exact_guard is not None and model is not None:
            _exact_guard(model, context=context)

    if load_case is None:
        return False
    pressure_loads = getattr(load_case, "pressure_loads", None)
    observed("nonlinear follower-pressure mapping observation")
    has_pressure = bool(pressure_loads)
    observed("nonlinear follower-pressure mapping disposition")
    if not has_pressure:
        return False
    follower_pressure = getattr(load_case, "follower_pressure", False)
    observed("nonlinear follower-pressure policy observation")
    result = bool(follower_pressure)
    observed("nonlinear follower-pressure policy disposition")
    return result


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


def _assemble_nonlinear_system_unchecked(
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
    require_full_coordinates: bool = False,
) -> Tuple[np.ndarray, Any, Dict[int, Any]]:
    """Assemble F_int (and the tangent K_T when requested) at a state.

    ``kinematics`` selects between the default von Karman element response and
    the element-independent corotational formulation for large rigid
    rotations. ``corotational_tangent`` is already resolved to either
    ``"rotated"`` or ``"consistent"`` by the public solver.
    """
    assembly_start = time.perf_counter()
    if require_full_coordinates:
        assembly_fallback_reason = "full_coordinates_explicitly_required"
    elif str(kinematics) != "von_karman":
        assembly_fallback_reason = "kinematics_not_von_karman"
    elif tuple(deleted_element_ids or ()):
        assembly_fallback_reason = "deleted_elements_require_reference_assembly"
    elif element_stiffness_scales:
        assembly_fallback_reason = "element_stiffness_scales_require_reference_assembly"
    else:
        assembly_fallback_reason = "persistent_assembly_plan_not_selected"
    del require_full_coordinates  # consumed by the direct-reduction adapter
    from .nonlinear_state import begin_state_evaluation, finish_state_evaluation

    state_token = begin_state_evaluation(
        committed_states,
        model=model,
        displacements=displacements,
    )
    mesh = model.mesh
    total_dofs = mesh.dof_manager.total_dofs
    F_int = np.zeros(total_dofs, dtype=float)
    data: list = []
    trial_states: Dict[int, Any] = {}
    deleted_set = {int(element_id) for element_id in (deleted_element_ids or ())}
    residual_fraction = float(residual_stiffness_fraction)
    freeze_deleted = getattr(committed_states, "freeze_deleted", None)
    if deleted_set and callable(freeze_deleted):
        freeze_deleted(tuple(sorted(deleted_set)))
    element_scales = {
        int(element_id): min(max(float(scale), 0.0), 1.0)
        for element_id, scale in (element_stiffness_scales or {}).items()
    }

    if tangent:
        from .matrix_assembly import _get_cached_sparsity_pattern
        rows_concat, cols_concat = _get_cached_sparsity_pattern(mesh, "tangent_stiffness")

    from .elements import ShellElement
    from .materials import is_isotropic_material
    from .nonlinear_element_evaluation import evaluate_nonlinear_element
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

        correction_cache: Dict[tuple[Any, ...], np.ndarray] = {}
        for idx, (elem_id, element) in enumerate(elem_list):
            correction_builder = getattr(element, "_qualified_linear_correction", None)
            if callable(correction_builder):
                cache_key_builder = getattr(
                    element, "_qualified_stiffness_cache_key", None
                )
                correction_key = (
                    int(num_layers),
                    cache_key_builder(mesh, material)
                    if callable(cache_key_builder)
                    else (int(elem_id),),
                )
                correction = correction_cache.get(correction_key)
                if correction is None:
                    correction = np.asarray(
                        correction_builder(mesh, material, int(num_layers)),
                        dtype=float,
                    )
                    correction_cache[correction_key] = correction
                F_int_batch[idx] += correction @ u_elem_batch[idx]
                if tangent:
                    K_T_batch[idx] += correction
            precomputed_F[elem_id] = F_int_batch[idx]
            if tangent:
                precomputed_K[elem_id] = K_T_batch[idx]

            # Reconstruct trial state to be compatible with single-element API
            trial_state = {
                "plastic_strain": ep_new[idx],
                "alpha": alpha_new[idx],
                "layer_strain": layer_strain_batch[idx * n_gp * num_layers : (idx + 1) * n_gp * num_layers].copy(),
            }
            attach_algorithmic_origin = getattr(
                element,
                "attach_current_tangent_algorithmic_origin",
                None,
            )
            if callable(attach_algorithmic_origin):
                trial_state = attach_algorithmic_origin(
                    material,
                    {
                        "plastic_strain": plastic_strain_batch[idx],
                        "alpha": alpha_batch[idx],
                    },
                    trial_state,
                    int(num_layers),
                    tangent_evaluated=bool(tangent),
                )
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
        evaluated_deleted_noncurrent = False

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
                deleted_operator = (
                    getattr(
                        element,
                        "compute_noncurrent_deleted_residual_operator",
                        None,
                    )
                    if elem_id in deleted_set
                    else None
                )
                if callable(deleted_operator):
                    f_elem, k_elem = deleted_operator(
                        mesh,
                        material,
                        u_elem,
                        committed_states.get(elem_id),
                        int(num_layers),
                        tangent=bool(tangent),
                    )
                    evaluated_deleted_noncurrent = True
                else:
                    f_elem, k_elem, trial_state = evaluate_nonlinear_element(
                        element,
                        mesh,
                        material,
                        u_elem,
                        committed_states.get(elem_id),
                        num_layers,
                        tangent,
                        committed_states=committed_states,
                        state_token=state_token,
                        element_id=elem_id,
                    )
                    if trial_state is not None:
                        trial_states[elem_id] = trial_state

        if elem_id in deleted_set:
            f_elem = residual_fraction * np.asarray(f_elem, dtype=float)
            if tangent and k_elem is not None:
                k_elem = residual_fraction * np.asarray(k_elem, dtype=float)
            if elem_id in committed_states and (
                not evaluated_deleted_noncurrent
                or not isinstance(committed_states, NonlinearStateStore)
            ):
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

    state_payload = finish_state_evaluation(
        committed_states,
        state_token,
        trial_states,
    )
    record_nonlinear_assembly_execution(
        path="reference_full_coordinate",
        tangent=bool(tangent),
        elapsed_seconds=time.perf_counter() - assembly_start,
        fallback_reason=assembly_fallback_reason,
    )
    return F_int, K_T, state_payload


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
    require_full_coordinates: bool = False,
) -> Tuple[np.ndarray, Any, Dict[int, Any]]:
    """Run one reference assembly as an all-or-nothing state evaluation.

    The reference assembler opens a persistent trial transaction before it
    invokes any element.  An element exception must not strand that token:
    retries, cutbacks, and cancellation cleanup all require the committed
    state to be immediately reusable.
    """

    try:
        return _assemble_nonlinear_system_unchecked(
            model,
            displacements,
            committed_states,
            num_layers,
            tangent=tangent,
            deleted_element_ids=deleted_element_ids,
            residual_stiffness_fraction=residual_stiffness_fraction,
            element_stiffness_scales=element_stiffness_scales,
            kinematics=kinematics,
            corotational_tangent=corotational_tangent,
            require_full_coordinates=require_full_coordinates,
        )
    except BaseException:
        _discard_nonlinear_state_candidate(committed_states)
        raise


def _support_reaction_dof_plan(
    model: "FEModel",
) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """Precompute named support DOFs and their six result components."""

    manager = model.mesh.dof_manager
    entries: Dict[str, Tuple[List[int], List[int]]] = {}
    for index, boundary in enumerate(getattr(model, "boundary_conditions", ()) or ()):
        name = str(getattr(boundary, "name", "") or f"support {index + 1}")
        dofs, components = entries.setdefault(name, ([], []))
        indices = getattr(boundary, "_dof_indices", {})
        constraints = getattr(boundary, "dof_constraints", {})
        for node_id in getattr(boundary, "node_ids", ()) or ():
            node_dofs = manager.get_node_dofs(int(node_id))
            for component in constraints:
                local = indices.get(component)
                if local is None or local >= len(node_dofs):
                    continue
                dof = int(node_dofs[local])
                if dof >= 0:
                    dofs.append(dof)
                    components.append(int(local))
    return {
        name: (
            np.asarray(dofs, dtype=np.intp),
            np.asarray(components, dtype=np.intp),
        )
        for name, (dofs, components) in entries.items()
    }


def _support_reaction_resultants(
    model: "FEModel",
    imbalance: np.ndarray,
    *,
    dof_plan: Optional[Mapping[str, Tuple[np.ndarray, np.ndarray]]] = None,
) -> Dict[str, Tuple[float, ...]]:
    """Sum nonlinear residual forces by named support boundary condition."""

    residual = np.asarray(imbalance, dtype=float).reshape(-1)
    plan = _support_reaction_dof_plan(model) if dof_plan is None else dof_plan
    result: Dict[str, Tuple[float, ...]] = {}
    for name, (dofs, components) in plan.items():
        if dofs.size <= 32:
            values = [0.0] * 6
            for entry_index in range(int(dofs.size)):
                dof = int(dofs[entry_index])
                if dof < residual.size:
                    component = int(components[entry_index])
                    values[component] += float(residual[dof])
            result[name] = tuple(values)
            continue
        valid = dofs < residual.size
        if np.all(valid):
            selected_dofs = dofs
            selected_components = components
        else:
            selected_dofs = dofs[valid]
            selected_components = components[valid]
        vector = np.bincount(
            selected_components,
            weights=residual[selected_dofs],
            minlength=6,
        )[:6]
        result[name] = tuple(float(value) for value in vector)
    return result


def _support_reaction_resultants_from_forces(
    model: "FEModel",
    internal_force: np.ndarray,
    constant_force: np.ndarray,
    proportional_force: np.ndarray,
    load_factor: float,
    *,
    dof_plan: Optional[Mapping[str, Tuple[np.ndarray, np.ndarray]]] = None,
) -> Dict[str, Tuple[float, ...]]:
    """Recover named support reactions without full residual temporaries."""

    internal = np.asarray(internal_force, dtype=float).reshape(-1)
    constant = np.asarray(constant_force, dtype=float).reshape(-1)
    proportional = np.asarray(proportional_force, dtype=float).reshape(-1)
    available = min(internal.size, constant.size, proportional.size)
    factor = float(load_factor)
    plan = _support_reaction_dof_plan(model) if dof_plan is None else dof_plan
    result: Dict[str, Tuple[float, ...]] = {}
    for name, (dofs, components) in plan.items():
        if dofs.size <= 32:
            values = [0.0] * 6
            for entry_index in range(int(dofs.size)):
                dof = int(dofs[entry_index])
                if dof < available:
                    component = int(components[entry_index])
                    values[component] += float(
                        internal[dof]
                        - (constant[dof] + factor * proportional[dof])
                    )
            result[name] = tuple(values)
            continue
        valid = dofs < available
        if np.all(valid):
            selected_dofs = dofs
            selected_components = components
        else:
            selected_dofs = dofs[valid]
            selected_components = components[valid]
        weights = internal[selected_dofs] - (
            constant[selected_dofs] + factor * proportional[selected_dofs]
        )
        vector = np.bincount(
            selected_components,
            weights=weights,
            minlength=6,
        )[:6]
        result[name] = tuple(float(value) for value in vector)
    return result


def _max_plastic_strain(states: Mapping[int, Any]) -> float:
    if isinstance(states, NonlinearStateStore):
        return states.max_equivalent_plastic_strain()
    alpha_parts: List[np.ndarray] = []
    for state in states.values():
        if not isinstance(state, dict):
            continue
        alpha = np.asarray(state.get("alpha", ()), dtype=float).reshape(-1)
        if alpha.size:
            alpha_parts.append(alpha)
    if not alpha_parts:
        return 0.0
    return float(np.max(np.concatenate(alpha_parts)))


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


def _owned_initial_element_states(
    model: "FEModel",
    initial_element_states: Optional[Mapping[int, Any]],
    *,
    _exact_guard: Any,
) -> Optional[Dict[int, Any]]:
    """Detach caller restart states before any model/mechanics observation."""

    if initial_element_states is None:
        return None
    if not isinstance(initial_element_states, Mapping):
        raise TypeError("initial_element_states must be a mapping or None")
    observed_items = tuple(initial_element_states.items())
    _exact_guard(model, context="nonlinear static initial-state mapping observation")
    owned: Dict[int, Any] = {}
    for raw_element_id, state in observed_items:
        if isinstance(raw_element_id, (bool, np.bool_)):
            raise ValueError("initial_element_states IDs must be canonical integers")
        element_id = int(raw_element_id)
        _exact_guard(model, context="nonlinear static initial-state ID observation")
        if element_id in owned:
            raise ValueError("initial_element_states contains duplicate element IDs")
        owned[element_id] = _guarded_owned_nonlinear_snapshot(
            model,
            state,
            path=f"initial_element_states[{element_id}]",
            _exact_guard=_exact_guard,
        )
    return owned


def _owned_initial_displacements(
    model: "FEModel",
    initial_displacements: Any,
    *,
    _exact_guard: Any,
) -> Optional[np.ndarray]:
    """Capture a bit-exact caller displacement vector under the operation lease."""

    if initial_displacements is None:
        return None
    observed = np.asarray(initial_displacements, dtype=np.float64)
    _exact_guard(model, context="nonlinear static initial-displacement observation")
    contiguous = np.ascontiguousarray(observed, dtype=np.float64)
    return np.frombuffer(
        contiguous.tobytes(order="C"),
        dtype=np.float64,
    ).reshape(contiguous.shape)


def _copy_initial_states(initial_element_states: Optional[Mapping[int, Any]]) -> Dict[int, Any]:
    return copy.deepcopy(dict(initial_element_states or {}))


def _qualified_q4_committed_state_hooks(element: Any) -> Optional[Tuple[Any, Any]]:
    """Return the closed Q4 state hooks without importing formulation code.

    The nonlinear driver deliberately discovers this private, formulation-
    versioned protocol from the element.  That keeps legacy Q4 and qualified
    S3 state lifecycles unchanged and avoids putting changing displacement
    seals into Newton's packed constitutive-state buffers.
    """

    schema = str(getattr(element, "current_state_binding_schema_id", ""))
    seal = getattr(element, "seal_committed_current_tangent_state", None)
    validate = getattr(element, "validate_committed_current_tangent_state", None)
    if (
        schema.startswith("E4_PL_Q4_COMMITTED_STATE_")
        and callable(seal)
        and callable(validate)
    ):
        return seal, validate
    return None


def _qualified_s3_committed_state_validator(element: Any) -> Optional[Any]:
    """Return the formulation-owned S3 committed-state validator."""

    formulation = str(getattr(element, "formulation_id", ""))
    validator = getattr(element, "validate_model_bound_nonlinear_state", None)
    if formulation in {
        "E4_PL_QUALIFIED_S3_COMPANION_V1",
        "CANDIDATE_E4_PL_S3_V2D_NATIVE_PARITY_V1",
    } and callable(validator):
        return validator
    return None


def _is_explicit_q4_initial_material_seed(state: Mapping[str, Any]) -> bool:
    """Whether an unbound payload is a material seed rather than a restart.

    The public virgin layered state consists only of plastic history arrays;
    callers have historically been allowed to seed those arrays before a
    zero-displacement analysis.  Recovery/kinematic/origin fields identify a
    previously evaluated committed result and therefore still require an
    exact displacement binding.
    """

    allowed = {
        "plastic_strain",
        "alpha",
        *_INITIAL_FIELD_STATE_KEYS,
        "initial_field_provenance",
    }
    keys = {str(key) for key in state}
    return {"plastic_strain", "alpha"}.issubset(keys) and keys <= allowed


def _prepare_qualified_q4_states_for_nonlinear_solve(
    model: "FEModel",
    displacements: np.ndarray,
    element_states: Mapping[int, Any],
    num_layers: int,
    info: Dict[str, Any],
    *,
    supplied_element_ids: Sequence[int],
    ordinary_restart: bool,
    allow_explicit_initial_material_states: bool = False,
    expected_deleted_element_ids: Sequence[int] = (),
    deletion_records: Sequence[Any] = (),
    residual_stiffness_fraction: Optional[float] = None,
    deleted_dispositions: Optional[Dict[int, Any]] = None,
) -> Dict[int, Any]:
    """Validate supplied Q4 seals, then remove them from an owned copy.

    A Q4 seal binds a *committed* constitutive payload to one exact global
    displacement/configuration.  It must therefore be checked before the
    first nonlinear element evaluation, but it must not travel through the
    packed trial-state machinery.  Historical Q4 states that predate the seal
    are accepted only on the ordinary restart path where an exact committed
    displacement is supplied.  They are identified explicitly and receive a
    fresh seal on the returned final state.
    """

    full = np.asarray(displacements, dtype=np.float64)
    if (
        full.ndim != 1
        or full.size != int(model.mesh.dof_manager.total_dofs)
        or not np.all(np.isfinite(full))
    ):
        raise ValueError(
            "qualified Q4 state preflight requires the complete finite "
            "committed displacement"
        )
    supplied = {int(value) for value in supplied_element_ids}
    expected_deleted = {int(value) for value in expected_deleted_element_ids}
    records_by_id = {
        int(record.element_id): record
        for record in deletion_records
    }
    if set(records_by_id) != expected_deleted:
        raise ValueError(
            "qualified Q4 deleted IDs and deletion records are inconsistent"
        )
    # This second deep copy is intentional.  _prepare_initial_states currently
    # owns its result too, but the binding boundary must remain safe if that
    # implementation changes or a future state-store adapter calls us directly.
    prepared = copy.deepcopy(dict(element_states))
    validated: List[int] = []
    migrated: List[int] = []
    stripped: List[int] = []
    fresh: List[int] = []
    explicit_seeds: List[int] = []
    restored_deleted: List[int] = []

    for raw_element_id, element in sorted(
        model.mesh.elements.items(), key=lambda item: int(item[0])
    ):
        hooks = _qualified_q4_committed_state_hooks(element)
        if hooks is None:
            continue
        element_id = int(raw_element_id)
        if element_id not in prepared:
            continue
        state = prepared[element_id]
        if state is None:
            # A caller-supplied None is a virgin state, not historical material
            # history.  The final materializer will create and seal it.
            continue
        if not isinstance(state, Mapping):
            raise TypeError(
                f"qualified Q4 state for element {element_id} must be a mapping"
            )
        has_binding = _Q4_COMMITTED_BINDING_KEY in state
        has_integrity = _Q4_COMMITTED_INTEGRITY_KEY in state
        has_disposition = _Q4_ACTIVITY_DISPOSITION_KEY in state
        if has_binding != has_integrity:
            raise ValueError(
                f"qualified Q4 state for element {element_id} has a partial "
                "committed-state binding"
            )

        dofs = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
        if dofs.shape != (24,):
            raise ValueError(
                f"qualified Q4 element {element_id} must map exactly 24 DOFs"
            )
        local_u = np.asarray(full[dofs], dtype=np.float64)
        if has_disposition:
            if not has_binding or element_id not in expected_deleted:
                raise ValueError(
                    f"qualified Q4 noncurrent disposition for element "
                    f"{element_id} disagrees with checkpoint deletion state"
                )
            validate_deleted = getattr(
                element,
                "validate_noncurrent_deleted_state",
                None,
            )
            if not callable(validate_deleted):
                raise ValueError(
                    f"qualified Q4 element {element_id} cannot validate its "
                    "deleted/frozen disposition"
                )
            record = records_by_id[element_id]
            validate_deleted(
                model.mesh,
                model.get_material(element.material_name),
                state,
                int(num_layers),
                expected_deletion_step_index=int(record.step_index),
                expected_deletion_load_factor=float(record.load_factor),
                expected_residual_stiffness_fraction=(
                    residual_stiffness_fraction
                ),
                expected_trigger_name=str(record.trigger_name),
            )
            if deleted_dispositions is not None:
                deleted_dispositions[element_id] = copy.deepcopy(
                    state[_Q4_ACTIVITY_DISPOSITION_KEY]
                )
            restored_deleted.append(element_id)
        elif element_id in expected_deleted:
            raise ValueError(
                f"deleted qualified Q4 element {element_id} lacks its "
                "frozen noncurrent disposition"
            )
        elif has_binding:
            _seal, validate = hooks
            validate(
                model.mesh,
                model.get_material(element.material_name),
                local_u,
                state,
                int(num_layers),
            )
            validated.append(element_id)
        elif element_id in supplied:
            if (
                allow_explicit_initial_material_states
                and _is_explicit_q4_initial_material_seed(state)
            ):
                explicit_seeds.append(element_id)
            elif not ordinary_restart:
                raise ValueError(
                    f"historical unbound qualified Q4 state for element "
                    f"{element_id} requires an exact ordinary-restart "
                    "displacement and equilibrate_initial_state=False"
                )
            else:
                migrated.append(element_id)
        else:
            # State freshly constructed from an initial-field declaration.
            fresh.append(element_id)

        owned_state = copy.deepcopy(dict(state))
        if has_binding:
            owned_state.pop(_Q4_COMMITTED_BINDING_KEY, None)
            owned_state.pop(_Q4_COMMITTED_INTEGRITY_KEY, None)
            stripped.append(element_id)
        owned_state.pop(_Q4_ACTIVITY_DISPOSITION_KEY, None)
        # Older experimental records sometimes mirrored the whole-state
        # digest under this cache name.  It is never trial-state input, even
        # when the two closed binding fields are absent during migration.
        owned_state.pop("state_digest", None)
        prepared[element_id] = owned_state

    s3_validated: List[int] = []
    s3_restored_deleted: List[int] = []
    s3_elements_present = False
    for raw_element_id, element in sorted(
        model.mesh.elements.items(), key=lambda item: int(item[0])
    ):
        validate_active = _qualified_s3_committed_state_validator(element)
        if validate_active is None:
            continue
        s3_elements_present = True
        element_id = int(raw_element_id)
        if element_id not in prepared:
            if element_id in expected_deleted:
                raise ValueError(
                    f"deleted qualified S3 element {element_id} lacks its "
                    "frozen noncurrent state"
                )
            continue
        state = prepared[element_id]
        if not isinstance(state, Mapping):
            raise TypeError(
                f"qualified S3 state for element {element_id} must be a mapping"
            )
        dofs = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
        if dofs.shape != (18,):
            raise ValueError(
                f"qualified S3 element {element_id} must map exactly 18 DOFs"
            )
        local_u = np.asarray(full[dofs], dtype=np.float64)
        has_disposition = _S3_ACTIVITY_DISPOSITION_KEY in state
        if has_disposition:
            if element_id not in expected_deleted:
                raise ValueError(
                    f"qualified S3 noncurrent disposition for element "
                    f"{element_id} disagrees with checkpoint deletion state"
                )
            record = records_by_id[element_id]
            validate_deleted = getattr(
                element, "validate_noncurrent_deleted_state", None
            )
            restore_deleted = getattr(
                element,
                "restore_noncurrent_deleted_state_for_internal_use",
                None,
            )
            if not callable(validate_deleted) or not callable(restore_deleted):
                raise ValueError(
                    f"qualified S3 element {element_id} cannot restore its "
                    "deleted/frozen state"
                )
            material = model.get_material(element.material_name)
            expected_keywords = {
                "expected_deletion_step_index": int(record.step_index),
                "expected_deletion_load_factor": float(record.load_factor),
                "expected_residual_stiffness_fraction": (
                    residual_stiffness_fraction
                ),
                "expected_trigger_name": str(record.trigger_name),
            }
            validate_deleted(
                model.mesh,
                material,
                state,
                int(num_layers),
                **expected_keywords,
            )
            if deleted_dispositions is not None:
                deleted_dispositions[element_id] = copy.deepcopy(
                    state[_S3_ACTIVITY_DISPOSITION_KEY]
                )
            prepared[element_id] = restore_deleted(
                model.mesh,
                material,
                state,
                int(num_layers),
                **expected_keywords,
            )
            s3_restored_deleted.append(element_id)
        elif element_id in expected_deleted:
            raise ValueError(
                f"deleted qualified S3 element {element_id} lacks its "
                "frozen noncurrent disposition"
            )
        else:
            validate_active(
                model.mesh,
                model.get_material(element.material_name),
                state,
                int(num_layers),
                expected_committed_total_u=local_u,
            )
            s3_validated.append(element_id)

    previous = info.get("qualified_q4_committed_state_lifecycle", {})

    def cumulative_ids(name: str, values: Sequence[int]) -> List[int]:
        prior = previous.get(name, ()) if isinstance(previous, Mapping) else ()
        return sorted({int(value) for value in (*prior, *values)})

    info["qualified_q4_committed_state_lifecycle"] = {
        "schema": _Q4_COMMITTED_STATE_LIFECYCLE_SCHEMA,
        "ordinary_restart": bool(ordinary_restart),
        "preflight_count": int(previous.get("preflight_count", 0)) + 1
        if isinstance(previous, Mapping)
        else 1,
        "validated_bound_element_ids": cumulative_ids(
            "validated_bound_element_ids", validated
        ),
        "migrated_historical_unbound_element_ids": cumulative_ids(
            "migrated_historical_unbound_element_ids", migrated
        ),
        "stripped_internal_binding_element_ids": cumulative_ids(
            "stripped_internal_binding_element_ids", stripped
        ),
        "fresh_unbound_element_ids": cumulative_ids(
            "fresh_unbound_element_ids", fresh
        ),
        "explicit_initial_material_state_element_ids": cumulative_ids(
            "explicit_initial_material_state_element_ids", explicit_seeds
        ),
        "restored_deleted_frozen_element_ids": cumulative_ids(
            "restored_deleted_frozen_element_ids", restored_deleted
        ),
        "input_states_deep_copied": True,
        "final_state_policy": "DETERMINISTIC_RESEAL_AFTER_MATERIALIZATION",
    }
    if s3_elements_present:
        previous_s3 = info.get("qualified_s3_committed_state_lifecycle", {})

        def cumulative_s3_ids(name: str, values: Sequence[int]) -> List[int]:
            prior = (
                previous_s3.get(name, ())
                if isinstance(previous_s3, Mapping)
                else ()
            )
            return sorted({int(value) for value in (*prior, *values)})

        info["qualified_s3_committed_state_lifecycle"] = {
            "schema": _S3_COMMITTED_STATE_LIFECYCLE_SCHEMA,
            "ordinary_restart": bool(ordinary_restart),
            "preflight_count": int(previous_s3.get("preflight_count", 0)) + 1
            if isinstance(previous_s3, Mapping)
            else 1,
            "validated_active_element_ids": cumulative_s3_ids(
                "validated_active_element_ids", s3_validated
            ),
            "restored_deleted_frozen_element_ids": cumulative_s3_ids(
                "restored_deleted_frozen_element_ids", s3_restored_deleted
            ),
            "input_states_deep_copied": True,
            "final_state_policy": (
                "ACTIVE_ONLY_OR_EXPLICIT_NONCURRENT_DISPOSITION"
            ),
        }
    return prepared


def _seal_final_qualified_q4_states(
    model: "FEModel",
    displacements: np.ndarray,
    element_states: Mapping[int, Any],
    num_layers: int,
    info: Optional[Dict[str, Any]] = None,
    *,
    kinematics: str = "von_karman",
    deleted_element_ids: Sequence[int] = (),
    deleted_dispositions: Optional[Mapping[int, Any]] = None,
    deletion_records: Sequence[Any] = (),
    residual_stiffness_fraction: Optional[float] = None,
) -> Dict[int, Any]:
    """Materialize and seal every finalized additive-von-Karman Q4 state."""

    states = dict(element_states)
    normalized_kinematics = str(kinematics)
    has_solver_integrated_s3 = any(
        _qualified_s3_committed_state_validator(element) is not None
        and callable(
            getattr(element, "seal_solver_integrated_nonlinear_state", None)
        )
        for element in model.mesh.elements.values()
    )
    if normalized_kinematics != "von_karman" and not has_solver_integrated_s3:
        return states
    full = np.asarray(displacements, dtype=np.float64)
    if (
        full.ndim != 1
        or full.size != int(model.mesh.dof_manager.total_dofs)
        or not np.all(np.isfinite(full))
    ):
        raise ValueError(
            "qualified Q4 finalization requires the complete finite displacement"
        )
    sealed_ids: List[int] = []
    deleted_sealed_ids: List[int] = []
    origin_materialized_ids: List[int] = []
    digests: List[Dict[str, Any]] = []
    s3_sealed_ids: List[int] = []
    s3_deleted_sealed_ids: List[int] = []
    s3_digests: List[Dict[str, Any]] = []
    s3_elements_present = False
    deleted = {int(value) for value in deleted_element_ids}
    disposition_by_id = {
        int(key): copy.deepcopy(value)
        for key, value in (deleted_dispositions or {}).items()
    }
    record_by_id = {int(record.element_id): record for record in deletion_records}
    for raw_element_id, element in sorted(
        model.mesh.elements.items(), key=lambda item: int(item[0])
    ):
        if normalized_kinematics != "von_karman":
            break
        hooks = _qualified_q4_committed_state_hooks(element)
        if hooks is None:
            continue
        element_id = int(raw_element_id)
        dofs = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
        if dofs.shape != (24,):
            raise ValueError(
                f"qualified Q4 element {element_id} must map exactly 24 DOFs"
            )
        local_u = np.asarray(full[dofs], dtype=np.float64)
        state = states.get(element_id)
        if element_id in deleted:
            if state is None or element_id not in disposition_by_id:
                raise ValueError(
                    f"deleted qualified Q4 element {element_id} lacks its "
                    "frozen-state lifecycle record"
                )
            record = record_by_id.get(element_id)
            if record is None:
                raise ValueError(
                    f"deleted qualified Q4 element {element_id} lacks its "
                    "deletion authority record"
                )
            disposition = disposition_by_id[element_id]
            deletion_u = np.asarray(
                disposition.get("accepted_local_u", ()), dtype=np.float64
            )
            seal_deleted = getattr(element, "seal_noncurrent_deleted_state", None)
            validate_deleted = getattr(
                element, "validate_noncurrent_deleted_state", None
            )
            if not callable(seal_deleted) or not callable(validate_deleted):
                raise ValueError(
                    f"qualified Q4 element {element_id} lacks deleted-state hooks"
                )
            material = model.get_material(element.material_name)
            sealed = seal_deleted(
                model.mesh,
                material,
                deletion_u,
                state,
                int(num_layers),
                deletion_step_index=int(record.step_index),
                deletion_load_factor=float(record.load_factor),
                residual_stiffness_fraction=float(
                    residual_stiffness_fraction
                ),
                trigger_name=str(record.trigger_name),
            )
            digest = validate_deleted(
                model.mesh,
                material,
                sealed,
                int(num_layers),
                expected_deletion_step_index=int(record.step_index),
                expected_deletion_load_factor=float(record.load_factor),
                expected_residual_stiffness_fraction=float(
                    residual_stiffness_fraction
                ),
                expected_trigger_name=str(record.trigger_name),
            )
            states[element_id] = sealed
            deleted_sealed_ids.append(element_id)
            digests.append(
                {"element_id": element_id, "state_integrity_sha256": digest}
            )
            continue
        if state is None:
            # Fully constrained and zero-step/stopped solves can legitimately
            # have no Newton candidate.  Recover their result state once at
            # the accepted displacement; this is outside the iteration path.
            # Request the tangent too so plastic-capable Q4 records the virgin
            # discrete-update origin required by the committed-state seal.
            material = model.get_material(element.material_name)
            _force, _tangent, recovered = element.compute_nonlinear_response(
                model.mesh,
                material,
                local_u,
                None,
                int(num_layers),
                True,
            )
            state = recovered
        if not isinstance(state, Mapping):
            raise TypeError(
                f"qualified Q4 finalized state for element {element_id} "
                "must be a mapping"
            )
        seal, validate = hooks
        material = model.get_material(element.material_name)
        requires_origin = getattr(
            element, "_requires_algorithmic_return_map_origin", None
        )
        if (
            "qualified_q4_algorithmic_origin" not in state
            and callable(requires_origin)
            and bool(requires_origin(material))
        ):
            if not _is_explicit_q4_initial_material_seed(state):
                raise ValueError(
                    f"qualified Q4 finalized plastic state for element "
                    f"{element_id} lacks its accepted algorithmic origin and "
                    "is not an unevaluated initial material parent"
                )
            # The only safe reconstruction is from an unevaluated explicit
            # parent.  A residual-only output contains derived/recovery fields
            # and is deliberately rejected above: replaying from that output
            # would perform a second return map from converged history.
            _force, tangent_matrix, tangent_state = (
                element.compute_nonlinear_response(
                    model.mesh,
                    material,
                    local_u,
                    state,
                    int(num_layers),
                    True,
                )
            )
            if tangent_matrix is None or not isinstance(tangent_state, Mapping):
                raise ValueError(
                    f"qualified Q4 initial material parent for element "
                    f"{element_id} did not produce a tangent-evaluated state"
                )
            state = tangent_state
            origin_materialized_ids.append(element_id)
        sealed = seal(
            model.mesh,
            material,
            local_u,
            state,
            int(num_layers),
        )
        digest = validate(
            model.mesh,
            material,
            local_u,
            sealed,
            int(num_layers),
        )
        states[element_id] = sealed
        sealed_ids.append(element_id)
        digests.append({"element_id": element_id, "state_integrity_sha256": digest})

    for raw_element_id, element in sorted(
        model.mesh.elements.items(), key=lambda item: int(item[0])
    ):
        validate_active = _qualified_s3_committed_state_validator(element)
        if validate_active is None:
            continue
        s3_elements_present = True
        element_id = int(raw_element_id)
        solver_sealer = getattr(
            element, "seal_solver_integrated_nonlinear_state", None
        )
        if normalized_kinematics != "von_karman" and not callable(
            solver_sealer
        ):
            continue
        dofs = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
        if dofs.shape != (18,):
            raise ValueError(
                f"qualified S3 element {element_id} must map exactly 18 DOFs"
            )
        local_u = np.asarray(full[dofs], dtype=np.float64)
        state = states.get(element_id)
        material = model.get_material(element.material_name)
        if element_id in deleted:
            if state is None or element_id not in disposition_by_id:
                raise ValueError(
                    f"deleted qualified S3 element {element_id} lacks its "
                    "frozen-state lifecycle record"
                )
            record = record_by_id.get(element_id)
            if record is None:
                raise ValueError(
                    f"deleted qualified S3 element {element_id} lacks its "
                    "deletion authority record"
                )
            disposition = disposition_by_id[element_id]
            deletion_u = np.asarray(
                disposition.get("accepted_local_u", ()), dtype=np.float64
            )
            seal_deleted = getattr(element, "seal_noncurrent_deleted_state", None)
            validate_deleted = getattr(
                element, "validate_noncurrent_deleted_state", None
            )
            if not callable(seal_deleted) or not callable(validate_deleted):
                raise ValueError(
                    f"qualified S3 element {element_id} lacks deleted-state hooks"
                )
            sealed = seal_deleted(
                model.mesh,
                material,
                deletion_u,
                state,
                int(num_layers),
                deletion_step_index=int(record.step_index),
                deletion_load_factor=float(record.load_factor),
                residual_stiffness_fraction=float(
                    residual_stiffness_fraction
                ),
                trigger_name=str(record.trigger_name),
            )
            digest = validate_deleted(
                model.mesh,
                material,
                sealed,
                int(num_layers),
                expected_deletion_step_index=int(record.step_index),
                expected_deletion_load_factor=float(record.load_factor),
                expected_residual_stiffness_fraction=float(
                    residual_stiffness_fraction
                ),
                expected_trigger_name=str(record.trigger_name),
            )
            states[element_id] = sealed
            s3_deleted_sealed_ids.append(element_id)
            s3_digests.append(
                {"element_id": element_id, "state_integrity_sha256": digest}
            )
            continue
        if not isinstance(state, Mapping):
            raise TypeError(
                f"qualified S3 finalized state for element {element_id} "
                "must be a mapping"
            )
        if callable(solver_sealer):
            validated = solver_sealer(
                model.mesh,
                material,
                state,
                int(num_layers),
                local_u,
                kinematics=str(kinematics),
            )
        else:
            validated = validate_active(
                model.mesh,
                material,
                state,
                int(num_layers),
                expected_committed_total_u=local_u,
            )
        states[element_id] = validated
        s3_sealed_ids.append(element_id)
        s3_digests.append(
            {
                "element_id": element_id,
                "state_integrity_sha256": str(
                    validated["state_integrity_sha256"]
                ),
            }
        )

    if info is not None:
        lifecycle = dict(
            info.get(
                "qualified_q4_committed_state_lifecycle",
                {
                    "schema": _Q4_COMMITTED_STATE_LIFECYCLE_SCHEMA,
                    "ordinary_restart": False,
                    "preflight_count": 0,
                    "validated_bound_element_ids": [],
                    "migrated_historical_unbound_element_ids": [],
                    "stripped_internal_binding_element_ids": [],
                    "fresh_unbound_element_ids": [],
                    "input_states_deep_copied": True,
                    "final_state_policy": (
                        "DETERMINISTIC_RESEAL_AFTER_MATERIALIZATION"
                    ),
                },
            )
        )
        lifecycle["sealed_final_element_ids"] = sealed_ids
        lifecycle["sealed_deleted_frozen_element_ids"] = deleted_sealed_ids
        lifecycle[
            "origin_materialized_from_unevaluated_parent_element_ids"
        ] = origin_materialized_ids
        lifecycle["sealed_final_state_digests"] = digests
        info["qualified_q4_committed_state_lifecycle"] = lifecycle
        if s3_elements_present:
            s3_lifecycle = dict(
                info.get(
                    "qualified_s3_committed_state_lifecycle",
                    {
                        "schema": _S3_COMMITTED_STATE_LIFECYCLE_SCHEMA,
                        "ordinary_restart": False,
                        "preflight_count": 0,
                        "validated_active_element_ids": [],
                        "restored_deleted_frozen_element_ids": [],
                        "input_states_deep_copied": True,
                        "final_state_policy": (
                            "ACTIVE_ONLY_OR_EXPLICIT_NONCURRENT_DISPOSITION"
                        ),
                    },
                )
            )
            s3_lifecycle["sealed_active_element_ids"] = s3_sealed_ids
            s3_lifecycle[
                "sealed_deleted_frozen_element_ids"
            ] = s3_deleted_sealed_ids
            s3_lifecycle["sealed_final_state_digests"] = s3_digests
            info["qualified_s3_committed_state_lifecycle"] = s3_lifecycle
    return states


def _mark_failed_qualified_q4_states(
    model: "FEModel",
    displacements: np.ndarray,
    element_states: Mapping[int, Any],
    num_layers: int,
    info: Dict[str, Any],
    *,
    failure_reason: str,
    kinematics: str,
) -> Dict[int, Any]:
    """Own failed Q4 output while denying it ACTIVE current-state authority."""

    states = dict(element_states)
    if str(kinematics) != "von_karman":
        return states
    full = np.asarray(displacements, dtype=np.float64)
    marked_ids: List[int] = []
    s3_marked_ids: List[int] = []
    for raw_element_id, element in sorted(
        model.mesh.elements.items(), key=lambda item: int(item[0])
    ):
        if _qualified_q4_committed_state_hooks(element) is None:
            continue
        element_id = int(raw_element_id)
        state = states.get(element_id)
        if state is None:
            initializer = getattr(element, "init_nonlinear_state", None)
            if callable(initializer):
                state = initializer(int(num_layers))
        if not isinstance(state, Mapping):
            continue
        marker = getattr(element, "mark_noncurrent_failed_state", None)
        if not callable(marker):
            raise ValueError(
                f"qualified Q4 element {element_id} lacks failed-state lifecycle"
            )
        dofs = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
        states[element_id] = marker(
            model.mesh,
            model.get_material(element.material_name),
            np.asarray(full[dofs], dtype=np.float64),
            state,
            int(num_layers),
            failure_reason=str(failure_reason),
        )
        marked_ids.append(element_id)
    for raw_element_id, element in sorted(
        model.mesh.elements.items(), key=lambda item: int(item[0])
    ):
        if _qualified_s3_committed_state_validator(element) is None:
            continue
        element_id = int(raw_element_id)
        material = model.get_material(element.material_name)
        state = states.get(element_id)
        if state is None:
            initializer = getattr(
                element, "init_model_bound_nonlinear_state", None
            )
            if callable(initializer):
                state = initializer(
                    model.mesh,
                    material,
                    int(num_layers),
                )
        if not isinstance(state, Mapping):
            continue
        marker = getattr(element, "mark_noncurrent_failed_state", None)
        if not callable(marker):
            if str(getattr(element, "formulation_id", "")) == (
                "CANDIDATE_E4_PL_S3_V2D_NATIVE_PARITY_V1"
            ):
                # V2D active restart is qualified in V6C; fracture/activity
                # disposition remains an explicit later gate. Preserve the
                # last accepted active state on an ordinary failed solve.
                continue
            raise ValueError(
                f"qualified S3 element {element_id} lacks failed-state lifecycle"
            )
        dofs = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
        if dofs.shape != (18,):
            raise ValueError(
                f"qualified S3 element {element_id} must map exactly 18 DOFs"
            )
        states[element_id] = marker(
            model.mesh,
            material,
            np.asarray(full[dofs], dtype=np.float64),
            state,
            int(num_layers),
            failure_reason=str(failure_reason),
        )
        s3_marked_ids.append(element_id)
    lifecycle = dict(
        info.get(
            "qualified_q4_committed_state_lifecycle",
            {"schema": _Q4_COMMITTED_STATE_LIFECYCLE_SCHEMA},
        )
    )
    lifecycle["failed_nonauthoritative_element_ids"] = marked_ids
    lifecycle["final_state_policy"] = "FAILED_NONAUTHORITATIVE_NO_ACTIVE_SEAL"
    info["qualified_q4_committed_state_lifecycle"] = lifecycle
    if s3_marked_ids:
        s3_lifecycle = dict(
            info.get(
                "qualified_s3_committed_state_lifecycle",
                {"schema": _S3_COMMITTED_STATE_LIFECYCLE_SCHEMA},
            )
        )
        s3_lifecycle["failed_nonauthoritative_element_ids"] = s3_marked_ids
        s3_lifecycle[
            "final_state_policy"
        ] = "FAILED_NONAUTHORITATIVE_NO_ACTIVE_SEAL"
        info["qualified_s3_committed_state_lifecycle"] = s3_lifecycle
    return states


def _state_has_initial_field(state: Any) -> bool:
    return state_has_active_initial_fields(state, _INITIAL_FIELD_STATE_KEYS)


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


def _initialize_missing_model_bound_states(
    model: "FEModel",
    states: Dict[int, Any],
    num_layers: int,
) -> None:
    """Materialize virgin native states before the shared-SO(3) store.

    Legacy elements deliberately retain their established lazy ``state=None``
    path.  A formulation-native element whose state is model-bound cannot do
    that: the node-shared rotation store must bind its reference directors and
    identity before the first trial begins.
    """

    for raw_element_id, element in model.mesh.elements.items():
        element_id = int(raw_element_id)
        if element_id in states:
            continue
        initializer = getattr(
            element,
            "init_model_bound_nonlinear_state",
            None,
        )
        if not (
            bool(
                getattr(
                    element,
                    "formulation_native_total_lagrangian",
                    False,
                )
            )
            and callable(initializer)
        ):
            continue
        initialized = initializer(
            model.mesh,
            model.get_material(element.material_name),
            num_layers,
        )
        if not isinstance(initialized, Mapping):
            raise TypeError(
                f"Model-bound initializer for element {element_id} must "
                "return a mapping"
            )
        states[element_id] = initialized


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
        _initialize_missing_model_bound_states(model, states, num_layers)
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
            if state is not None and not isinstance(state, Mapping):
                raise TypeError(f"Initial state for shell element {element_id} must be a mapping")
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
        field_provenance = {
            "kind": field_type,
            "source": field_value.source,
            "components": sorted(values),
        }
        for key, array in values.items():
            if array.size == 0 or np.any(~np.isfinite(array)):
                raise ValueError(
                    f"{key} for element {element_id} must contain finite values"
                )
        initialized_atomically = False
        if isinstance(field_value, ShellInitialField):
            model_bound_initializer = getattr(
                element,
                "init_model_bound_nonlinear_state",
                None,
            )
            if callable(model_bound_initializer):
                if state is not None:
                    raise ValueError(
                        "Cannot replace qualified model-bound initial fields on an "
                        f"existing state for element {element_id}; rebuild the virgin "
                        "state atomically or continue the stored restart history."
                    )
                state = model_bound_initializer(
                    model.mesh,
                    model.get_material(element.material_name),
                    num_layers,
                    initial_fields=values,
                    initial_field_provenance=field_provenance,
                )
                if not isinstance(state, Mapping):
                    raise TypeError(
                        f"Model-bound initializer for element {element_id} must return a mapping"
                    )
                initialized_atomically = True
            elif state is None:
                state = element.init_nonlinear_state(num_layers)
        if not isinstance(state, Mapping):
            raise TypeError(
                f"Initial state for element {element_id} must be a mapping"
            )
        if not initialized_atomically:
            state = copy.deepcopy(dict(state))
        # Supplying a field for an element replaces its complete prior field
        # definition. Mixing old components with a new source would make both
        # the constitutive input and its provenance ambiguous; callers that
        # want multiple components must provide them together in one field.
        if not initialized_atomically:
            for key in (*_INITIAL_FIELD_STATE_KEYS, "initial_field_provenance"):
                state.pop(key, None)
            for key, array in values.items():
                state[key] = array
            state["initial_field_provenance"] = field_provenance
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
    _initialize_missing_model_bound_states(model, states, num_layers)
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


def _activate_nonlinear_state_storage(
    model: "FEModel",
    committed_states: Mapping[int, Any],
    num_layers: int,
    info: Dict[str, Any],
    *,
    kinematics: str,
    committed_displacements: Optional[np.ndarray] = None,
    noncurrent_native_element_ids: Sequence[int] = (),
) -> Mapping[int, Any]:
    """Create one solver-owned material/native-rotation transaction store."""

    previous_diagnostic = info.get("nonlinear_state_storage")
    noncurrent_native = {
        int(value) for value in noncurrent_native_element_ids
    }
    native_required = any(
        bool(getattr(element, "formulation_native_total_lagrangian", False))
        and int(element_id) not in noncurrent_native
        for element_id, element in model.mesh.elements.items()
    )
    if native_required and not isinstance(committed_states, NonlinearStateStore):
        initialized_states = copy.deepcopy(dict(committed_states))
        _initialize_missing_model_bound_states(
            model,
            initialized_states,
            num_layers,
        )
        committed_states = initialized_states
    diagnostic: Dict[str, Any] = {
        "activated": False,
        "eligible_batch_count": 0,
        "fallback_reason": None,
    }
    if native_required:
        diagnostic.update(
            {
                "native_rotation_required": True,
                "native_rotation_activated": False,
                "noncurrent_native_element_ids": sorted(noncurrent_native),
            }
        )
    info["nonlinear_state_storage"] = diagnostic
    if isinstance(committed_states, NonlinearStateStore):
        if isinstance(previous_diagnostic, Mapping):
            for key in (
                "eligible_batch_count",
                "batch_eligibility",
                "array_batch_fallback_reason",
            ):
                if key in previous_diagnostic:
                    diagnostic[key] = copy.deepcopy(previous_diagnostic[key])
        if native_required and not committed_states.has_native_rotations:
            if committed_displacements is None:
                raise StateTransactionError(
                    "Native state storage requires committed displacements"
                )
            from .nonlinear_state import create_model_native_rotation_store

            rotation_store = create_model_native_rotation_store(
                model,
                committed_states,
                committed_displacements,
                noncurrent_element_ids=tuple(sorted(noncurrent_native)),
            )
            if rotation_store is None:
                raise StateTransactionError(
                    "Native elements were present but no rotation store was created"
                )
            committed_states.attach_native_rotation_store(rotation_store)
        diagnostic["activated"] = True
        if native_required:
            diagnostic["native_rotation_activated"] = (
                committed_states.has_native_rotations
            )
        diagnostic.update(committed_states.diagnostics())
        return committed_states
    if str(kinematics) != "von_karman":
        if native_required:
            raise NotImplementedError(
                "Formulation-native total-Lagrangian elements cannot use the "
                f"generic {kinematics!r} nonlinear kinematics path"
            )
        diagnostic["fallback_reason"] = "kinematics_not_von_karman"
        return committed_states
    persistent_disabled = os.environ.get(
        "FE_SOLVER_DISABLE_PERSISTENT_STATE", ""
    ).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    acceleration_disabled = os.environ.get(
        "FE_SOLVER_DISABLE_FAST_NL", ""
    ).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    allow_array_batches = not persistent_disabled and not acceleration_disabled
    if not native_required and persistent_disabled:
        diagnostic["fallback_reason"] = "persistent_state_storage_disabled"
        return committed_states
    if not native_required and acceleration_disabled:
        diagnostic["fallback_reason"] = "nonlinear_acceleration_disabled"
        return committed_states
    try:
        plastic_batches: tuple[Any, ...] = ()
        if allow_array_batches:
            from .nonlinear_performance_bootstrap import get_nonlinear_assembly_plan

            plan = get_nonlinear_assembly_plan(model, int(num_layers))
            plastic_batches = tuple(
                batch for batch in plan.shell_batches if batch.has_plasticity
            )
        store = NonlinearStateStore.from_shell_layouts(
            tuple(batch.state_layout for batch in plastic_batches),
            committed_states,
        )
        eligibility = []
        for batch in plastic_batches:
            state_batch = store.shell_batch_for_layout(batch.state_layout)
            eligible, reason = batch.persistent_state_eligibility(state_batch)
            eligibility.append(
                {
                    "element_ids": list(batch.state_layout.element_ids),
                    "eligible": bool(eligible),
                    "fallback_reason": reason,
                }
            )
        eligible_count = sum(int(item["eligible"]) for item in eligibility)
        diagnostic.update(
            {
                "eligible_batch_count": int(eligible_count),
                "batch_eligibility": eligibility,
            }
        )
        if not native_required and eligible_count == 0:
            if persistent_disabled:
                diagnostic["fallback_reason"] = "persistent_state_storage_disabled"
            elif acceleration_disabled:
                diagnostic["fallback_reason"] = "nonlinear_acceleration_disabled"
            elif not plastic_batches:
                diagnostic["fallback_reason"] = "no_plastic_shell_batch"
            else:
                diagnostic["fallback_reason"] = "no_persistent_state_batch_eligible"
            return committed_states
        if native_required:
            if committed_displacements is None:
                raise StateTransactionError(
                    "Native state storage requires committed displacements"
                )
            from .nonlinear_state import create_model_native_rotation_store

            rotation_store = create_model_native_rotation_store(
                model,
                committed_states,
                committed_displacements,
                noncurrent_element_ids=tuple(sorted(noncurrent_native)),
            )
            if rotation_store is None:
                raise StateTransactionError(
                    "Native elements were present but no rotation store was created"
                )
            store.attach_native_rotation_store(rotation_store)
            diagnostic["native_rotation_activated"] = True
            if not allow_array_batches:
                diagnostic["array_batch_fallback_reason"] = (
                    "persistent_state_storage_disabled"
                    if persistent_disabled
                    else "nonlinear_acceleration_disabled"
                )
        diagnostic["activated"] = True
        diagnostic.update(store.diagnostics())
        return store
    except Exception as exc:
        if native_required:
            diagnostic["fallback_reason"] = (
                f"native_state_store_setup_failed:{type(exc).__name__}:{exc}"
            )
            raise
        diagnostic["fallback_reason"] = (
            f"state_store_setup_failed:{type(exc).__name__}:{exc}"
        )
        return committed_states


def _commit_nonlinear_state_candidate(
    committed_states: Mapping[int, Any],
    candidate_states: Mapping[int, Any],
    *,
    model: Any = None,
    accepted_displacements: Any = None,
) -> Mapping[int, Any]:
    return commit_state_candidate(
        committed_states,
        candidate_states,
        model=model,
        accepted_full_displacement=accepted_displacements,
    )


def _discard_nonlinear_state_candidate(
    committed_states: Mapping[int, Any],
) -> None:
    discard_active_state_candidate(committed_states)


def _materialize_final_nonlinear_states(
    committed_states: Mapping[int, Any],
    info: Dict[str, Any],
) -> Dict[int, Any]:
    store = committed_states if isinstance(committed_states, NonlinearStateStore) else None
    result = materialize_state_mapping(
        committed_states,
        policy=StateMaterializationPolicy.FINAL_RESULT,
    )
    if store is not None:
        activation = dict(info.get("nonlinear_state_storage", {}))
        activation.update(store.diagnostics())
        activation["activated"] = True
        info["nonlinear_state_storage"] = activation
    return result


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


def _equilibrate_initial_fields_candidate(
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
    _exact_guard: Any = None,
) -> Tuple[np.ndarray, Dict[int, Any], List[Dict[str, Any]], Optional[str]]:
    """Equilibrate prescribed residual fields before any external load.

    The residual field is held fixed while compatible displacements and the
    material history are solved from ``F_int = 0``.  Only a converged trial
    state is committed.  This is intentionally a separate zero-load phase so
    permanent/environmental loading cannot silently absorb an unbalanced
    manufacturing field in its first increment.
    """
    exact_guard = _exact_guard or _EXACT_QUALIFIED_LIFECYCLE_GUARD
    exact_guard(
        model,
        context="nonlinear static initial equilibration preflight",
    )
    n_red = int(T.shape[1])
    if initial_reduced_displacements is None:
        q = np.zeros(n_red, dtype=float)
    else:
        q = np.asarray(initial_reduced_displacements, dtype=float).reshape(-1).copy()
        exact_guard(
            model,
            context="nonlinear static initial displacement observation",
        )
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
        exact_guard(
            model,
            context="nonlinear static initial equilibration cancellation",
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
        exact_guard(
            model,
            context="nonlinear static initial equilibration assembly",
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
            exact_guard(
                model,
                context="nonlinear static initial equilibration trial assembly",
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
    _exact_guard: Any = None,
) -> Tuple[np.ndarray, Dict[int, Any], List[Dict[str, Any]], Optional[str]]:
    """Commit exactly one accepted zero-load state and discard every other trial."""

    try:
        q, candidate_states, history, failure = (
            _equilibrate_initial_fields_candidate(
                model=model,
                T=T,
                u0=u0,
                committed_states=committed_states,
                num_layers=num_layers,
                max_iterations=max_iterations,
                tolerance=tolerance,
                kinematics=kinematics,
                corotational_tangent=corotational_tangent,
                general_tangent=general_tangent,
                initial_reduced_displacements=initial_reduced_displacements,
                cancellation_token=cancellation_token,
                _exact_guard=_exact_guard,
            )
        )
        if failure is not None:
            return q, committed_states, history, failure
        accepted_states = _commit_nonlinear_state_candidate(
            committed_states,
            candidate_states,
            model=model,
            accepted_displacements=np.asarray(T @ q + u0, dtype=float).reshape(-1),
        )
        return q, accepted_states, history, None
    finally:
        # This is a no-op after a successful persistent commit and for legacy
        # dictionaries.  Every failure return, cancellation, and exception
        # therefore leaves the input state reusable without duplicating
        # cleanup at each exit site in the Newton/backtracking implementation.
        _discard_nonlinear_state_candidate(committed_states)


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


def _reduced_coordinates_with_affine_scale(
    T: sparse.csr_matrix,
    u0: np.ndarray,
    displacements: Optional[np.ndarray],
) -> Tuple[np.ndarray, float]:
    """Recover a restart state and its proportional affine-constraint scale.

    A force-control restart must preserve the supplied physical support/MPC
    state while a new proportional load path starts at zero.  Solving the
    augmented compatible representation ``u = T q + s u0`` recovers both the
    free coordinates and the already-committed affine scale ``s`` without
    guessing it from one selected support row.
    """

    if displacements is None:
        return np.zeros(int(T.shape[1]), dtype=float), 0.0
    full = np.asarray(displacements, dtype=float).reshape(-1)
    if full.size != T.shape[0]:
        raise ValueError(
            f"initial_displacements has {full.size} entries; expected {T.shape[0]}"
        )
    if np.any(~np.isfinite(full)):
        raise ValueError("initial_displacements must contain only finite values")
    affine = np.asarray(u0, dtype=float).reshape(-1)
    if float(np.linalg.norm(affine)) <= 1.0e-30:
        return _reduced_coordinates(T, np.zeros_like(affine), full), 0.0

    augmented = sparse.hstack(
        (T, sparse.csr_matrix(affine.reshape(-1, 1))),
        format="csr",
    )
    solution = sparse.linalg.lsqr(
        augmented,
        full,
        atol=1.0e-12,
        btol=1.0e-12,
    )
    values = np.asarray(solution[0], dtype=float).reshape(-1)
    q = values[:-1]
    affine_scale = float(values[-1])
    if np.any(~np.isfinite(q)) or not np.isfinite(affine_scale):
        raise ValueError(
            "initial_displacements could not be reduced to finite coordinates"
        )
    reconstructed = np.asarray(augmented @ values, dtype=float).reshape(-1)
    error = float(np.linalg.norm(reconstructed - full))
    scale = max(float(np.linalg.norm(full)), 1.0)
    if error > 1.0e-9 * scale:
        raise ValueError(
            "initial_displacements is incompatible with the active "
            "supports/MPC affine path "
            f"(projection residual {error:.3e})"
        )
    return q, affine_scale


def _exact_binary64_additive_offset(
    target: np.ndarray,
    projected: np.ndarray,
    *,
    context: str,
) -> np.ndarray:
    """Return an offset whose binary64 addition reconstructs ``target``.

    The reduced-coordinate solve is a compatibility proof, not serialization
    authority: sparse projections may differ from the caller/checkpoint vector
    by a few ulps.  Retaining the exact additive residual keeps the public
    committed displacement bit-identical without changing the established
    reduced coordinates or projecting the state a second time.
    """

    expected = np.asarray(target, dtype=np.float64).reshape(-1)
    base = np.asarray(projected, dtype=np.float64).reshape(-1)
    if expected.shape != base.shape or not (
        np.all(np.isfinite(expected)) and np.all(np.isfinite(base))
    ):
        raise ValueError(f"{context} requires compatible finite vectors")
    offset = expected - base
    for _pass in range(4):
        reconstructed = base + offset
        if np.array_equal(reconstructed, expected):
            return offset
        offset += expected - reconstructed
    raise ValueError(f"{context} cannot be reconstructed bit-exactly")


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
    initial_load_factor: float = 0.0,
    step_index_offset: int = 0,
    initial_steps: Sequence[NonlinearStaticStep] = (),
    initial_history: Sequence[Mapping[str, Any]] = (),
    initial_total_iterations: int = 0,
    restart_analysis_contract: Optional[Mapping[str, Any]] = None,
    _exact_guard: Any = None,
) -> NonlinearStaticResult:
    """Displacement-control Newton solve with load factor as an unknown."""
    exact_guard = _exact_guard or _EXACT_QUALIFIED_LIFECYCLE_GUARD
    exact_guard(
        model,
        context="nonlinear static displacement-control preflight",
    )
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
    lam = float(initial_load_factor)
    steps: List[NonlinearStaticStep] = list(initial_steps)
    snapshots: List[NonlinearIncrementSnapshot] = []
    history: List[Dict[str, Any]] = copy.deepcopy(list(initial_history))
    status = "completed"
    failure_reason: Optional[str] = None
    total_iterations = int(initial_total_iterations)

    row_full = displacement_control.full_row(model)
    exact_guard(model, context="nonlinear static displacement-control row")
    row_red = np.asarray(row_full @ T, dtype=float).reshape(-1)
    row_u0 = float(row_full @ u0)
    if float(np.linalg.norm(row_red)) <= 0.0:
        raise ValueError("Displacement control target is fixed or dependent and cannot be used as an unknown")

    initial_u = np.asarray(u0, dtype=float).reshape(-1)
    follower_active = any(
        _has_follower_pressure(
            case,
            model=model,
            _exact_guard=exact_guard,
        )
        for case, _factor in [*constant_terms, proportional_term]
    )
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
        exact_guard(
            model,
            context="nonlinear static displacement-control initial load",
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
        for local_step_index in range(1, num_steps + 1):
            step_index = int(step_index_offset) + local_step_index
            cancellation_safe_point(
                cancellation_token,
                f"nonlinear_static.displacement.step:{step_index}",
            )
            exact_guard(
                model,
                context="nonlinear static displacement-control step cancellation",
            )
            q_step_start = q.copy()
            lam_step_start = float(lam)
            target = initial_control + target_increment * local_step_index / num_steps
            residual_norm = float("inf")
            constraint_error = float("inf")
            states_new = committed_states

            for iteration in range(1, max_iterations + 1):
                cancellation_safe_point(
                    cancellation_token,
                    f"nonlinear_static.displacement.step:{step_index}.iteration:{iteration}",
                )
                exact_guard(
                    model,
                    context=(
                        "nonlinear static displacement-control iteration cancellation"
                    ),
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
                exact_guard(
                    model,
                    context="nonlinear static displacement-control assembly",
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
                    exact_guard(
                        model,
                        context="nonlinear static displacement-control loads",
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
                _discard_nonlinear_state_candidate(committed_states)
                q = q_step_start
                lam = lam_step_start
                status = "stopped_at_limit" if steps else "diverged"
                break

            committed_states = _commit_nonlinear_state_candidate(
                committed_states,
                states_new,
                model=model,
                accepted_displacements=np.asarray(T @ q + u0, dtype=float).reshape(-1),
            )
            u = np.asarray(T @ q + u0, dtype=float).reshape(-1)
            current = float(row_red @ q + row_u0)
            reaction_internal, _unused, _reaction_states = _assemble_nonlinear_system(
                model,
                u,
                committed_states,
                num_layers,
                tangent=False,
                kinematics=kinematics,
                corotational_tangent=corotational_tangent,
                require_full_coordinates=True,
            )
            exact_guard(
                model,
                context="nonlinear static displacement-control reaction assembly",
            )
            # Reaction recovery is diagnostic-only; do not leave its trial
            # constitutive state active for the next accepted increment.
            _discard_nonlinear_state_candidate(committed_states)
            if follower_active:
                reaction_constant, _unused = _weighted_external_load_system(
                    model, constant_terms, u, tangent=False
                )
                reaction_proportional, _unused = _weighted_external_load_system(
                    model, [proportional_term], u, tangent=False
                )
                exact_guard(
                    model,
                    context="nonlinear static displacement-control reaction loads",
                )
            else:
                reaction_constant = F_const_static
                reaction_proportional = F_prop_static
            support_reactions = _support_reaction_resultants(
                model,
                reaction_internal
                - (reaction_constant + lam * reaction_proportional),
            )
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
                    support_reactions=support_reactions,
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
                    "support_reactions": {
                        name: list(values)
                        for name, values in support_reactions.items()
                    },
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
                    completed=local_step_index,
                    total=num_steps,
                    iteration=iteration,
                    control="displacement",
                    step_index=int(step_index),
                    load_factor=float(lam),
                    control_value=float(current),
                    displacement_norm=float(np.linalg.norm(u)),
                    max_equivalent_plastic_strain=float(_max_plastic_strain(committed_states)),
                    support_reactions={
                        name: list(values)
                        for name, values in support_reactions.items()
                    },
                )
                exact_guard(
                    model,
                    context="nonlinear static displacement-control progress callback",
                )

    u_final = np.asarray(T @ q + u0, dtype=float).reshape(-1)
    committed_states = _materialize_final_nonlinear_states(committed_states, info)
    committed_states = _finalize_nonlinear_element_states(
        model,
        u_final,
        committed_states,
        num_layers,
        kinematics=kinematics,
    )
    committed_states = _seal_final_qualified_q4_states(
        model,
        u_final,
        committed_states,
        num_layers,
        info,
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
    exact_guard(
        model,
        context="nonlinear static displacement-control constraint postcheck",
    )
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
    restart_payload = None
    if restart_analysis_contract is not None:
        restart_payload = create_nonlinear_checkpoint(
            analysis_kind="static",
            model=model,
            analysis_contract=restart_analysis_contract,
            displacements=u_final,
            element_states=committed_states,
            deleted_element_ids=(),
            path_state=_static_restart_path_payload(
                control_name="displacement",
                load_factor=float(lam),
                step_index=len(steps),
                total_iterations=total_iterations,
                steps=steps,
                force_displacement_history=history,
                reduced_coordinates=q,
                terminal_status=status,
                failure_reason=failure_reason,
            ),
        )
        exact_guard(
            model,
            context="nonlinear static displacement-control checkpoint output",
        )
    return NonlinearStaticResult(
        steps,
        status,
        u_final,
        float(lam),
        committed_states,
        info,
        tuple(snapshots),
        restart_payload,
    )


@dataclass(frozen=True)
class _NonlinearStaticOperationConfig:
    max_load_factor: float
    num_steps: int
    max_iterations: int
    tolerance: float
    num_layers: int
    min_step_fraction: float
    control: str
    kinematics: str
    corotational_tangent: str
    equilibrate_initial_state: Optional[bool]
    record_increment_snapshots: bool
    emit_restart_checkpoint: bool


def _owned_nonlinear_static_operation_config(
    model: "FEModel",
    *,
    max_load_factor: Any,
    num_steps: Any,
    max_iterations: Any,
    tolerance: Any,
    num_layers: Any,
    min_step_fraction: Any,
    control: Any,
    kinematics: Any,
    corotational_tangent: Any,
    equilibrate_initial_state: Any,
    record_increment_snapshots: Any,
    emit_restart_checkpoint: Any,
    _exact_guard: Any,
) -> _NonlinearStaticOperationConfig:
    """Own scalar nonlinear policy before model/capability observation."""

    def converted(value: Any, converter: Any, name: str) -> Any:
        made = converter(value)
        _exact_guard(model, context=f"nonlinear static {name} conversion")
        return made

    def canonical_int(value: Any, name: str) -> int:
        if isinstance(value, (bool, np.bool_)) or not isinstance(
            value,
            (int, np.integer),
        ):
            raise ValueError(f"{name} must be an integer")
        return converted(value, int, name)

    owned_equilibrate = (
        None
        if equilibrate_initial_state is None
        else converted(
            equilibrate_initial_state,
            bool,
            "equilibrate_initial_state",
        )
    )
    owned = _NonlinearStaticOperationConfig(
        max_load_factor=converted(
            max_load_factor,
            float,
            "max_load_factor",
        ),
        num_steps=canonical_int(num_steps, "num_steps"),
        max_iterations=canonical_int(max_iterations, "max_iterations"),
        tolerance=converted(tolerance, float, "tolerance"),
        num_layers=canonical_int(num_layers, "num_layers"),
        min_step_fraction=converted(
            min_step_fraction,
            float,
            "min_step_fraction",
        ),
        control=converted(control, str, "control").lower(),
        kinematics=converted(kinematics, str, "kinematics").lower(),
        corotational_tangent=converted(
            corotational_tangent,
            str,
            "corotational_tangent",
        ),
        equilibrate_initial_state=owned_equilibrate,
        record_increment_snapshots=converted(
            record_increment_snapshots,
            bool,
            "record_increment_snapshots",
        ),
        emit_restart_checkpoint=converted(
            emit_restart_checkpoint,
            bool,
            "emit_restart_checkpoint",
        ),
    )
    _exact_guard(model, context="nonlinear static owned configuration")
    return owned


def _guarded_config_sequence(
    model: "FEModel",
    value: Any,
    *,
    context: str,
    _exact_guard: Any,
) -> Tuple[Any, ...]:
    iterator = iter(value)
    _exact_guard(model, context=f"{context} iterator")
    observed = []
    while True:
        try:
            member = next(iterator)
        except StopIteration:
            _exact_guard(model, context=f"{context} end")
            break
        _exact_guard(model, context=f"{context} member")
        observed.append(member)
    return tuple(observed)


def _guarded_plain_config_snapshot(
    model: "FEModel",
    value: Any,
    *,
    context: str,
    _exact_guard: Any,
) -> Any:
    if value is None or type(value) in {bool, int, float, str, bytes}:
        return value
    if isinstance(value, np.ndarray):
        detached = np.array(value, copy=True)
        _exact_guard(model, context=f"{context} array observation")
        return detached
    if isinstance(value, np.generic):
        detached = value.item()
        _exact_guard(model, context=f"{context} scalar observation")
        return detached
    if isinstance(value, Mapping):
        iterator = iter(value)
        _exact_guard(model, context=f"{context} mapping iterator")
        detached_mapping: Dict[Any, Any] = {}
        while True:
            try:
                key = next(iterator)
            except StopIteration:
                _exact_guard(model, context=f"{context} mapping end")
                break
            _exact_guard(model, context=f"{context} mapping key")
            detached_key = _guarded_plain_config_snapshot(
                model,
                key,
                context=f"{context}.key",
                _exact_guard=_exact_guard,
            )
            member = value[key]
            _exact_guard(model, context=f"{context} mapping value")
            detached_member = _guarded_plain_config_snapshot(
                model,
                member,
                context=f"{context}[{key!r}]",
                _exact_guard=_exact_guard,
            )
            detached_mapping[detached_key] = detached_member
            _exact_guard(model, context=f"{context} mapping insertion")
        return detached_mapping
    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return tuple(
            _guarded_plain_config_snapshot(
                model,
                member,
                context=f"{context}[{index}]",
                _exact_guard=_exact_guard,
            )
            for index, member in enumerate(
                _guarded_config_sequence(
                    model,
                    value,
                    context=context,
                    _exact_guard=_exact_guard,
                )
            )
        )
    detached = copy.deepcopy(value)
    _exact_guard(model, context=f"{context} copy observation")
    return detached


def _owned_nonlinear_load_program(
    model: "FEModel",
    value: Any,
    *,
    _exact_guard: Any,
) -> Optional[NonlinearLoadProgram]:
    if value is None:
        return None
    raw_stages = getattr(value, "stages")
    _exact_guard(model, context="nonlinear load-program stages observation")
    stages = []
    for index, raw_stage in enumerate(
        _guarded_config_sequence(
            model,
            raw_stages,
            context="nonlinear load-program stages",
            _exact_guard=_exact_guard,
        )
    ):
        raw_name = getattr(raw_stage, "name")
        _exact_guard(
            model,
            context=f"nonlinear load-program stage {index} name observation",
        )
        name = str(raw_name)
        _exact_guard(
            model,
            context=f"nonlinear load-program stage {index} name conversion",
        )
        load_case = getattr(raw_stage, "load_case")
        _exact_guard(
            model,
            context=f"nonlinear load-program stage {index} load-case observation",
        )
        raw_factor = getattr(raw_stage, "target_factor")
        _exact_guard(
            model,
            context=f"nonlinear load-program stage {index} factor observation",
        )
        target_factor = float(raw_factor)
        _exact_guard(
            model,
            context=f"nonlinear load-program stage {index} factor conversion",
        )
        stages.append(
            NonlinearLoadStage(
                name=name,
                load_case=load_case,
                target_factor=target_factor,
            )
        )
        _exact_guard(
            model,
            context=f"nonlinear load-program stage {index} construction",
        )
    owned = NonlinearLoadProgram(tuple(stages))
    _exact_guard(model, context="nonlinear load-program construction")
    return owned


def _owned_displacement_control(
    model: "FEModel",
    value: Any,
    *,
    _exact_guard: Any,
) -> Optional[DisplacementControl]:
    if value is None:
        return None

    def observed(name: str) -> Any:
        member = getattr(value, name)
        _exact_guard(
            model,
            context=f"nonlinear displacement control {name} observation",
        )
        return member

    raw_node_id = observed("node_id")
    node_id = None if raw_node_id is None else int(raw_node_id)
    if raw_node_id is not None:
        _exact_guard(
            model,
            context="nonlinear displacement control node_id conversion",
        )
    raw_dof = observed("dof")
    if raw_dof is None:
        dof: Optional[Union[str, int]] = None
    elif isinstance(raw_dof, str):
        dof = str(raw_dof)
        _exact_guard(
            model,
            context="nonlinear displacement control dof conversion",
        )
    else:
        dof = int(raw_dof)
        _exact_guard(
            model,
            context="nonlinear displacement control dof conversion",
        )
    target = float(observed("target_displacement"))
    _exact_guard(
        model,
        context="nonlinear displacement control target conversion",
    )
    raw_weighted = observed("weighted_dofs")
    weighted: Optional[Dict[Any, float]] = None
    if raw_weighted is not None:
        if not isinstance(raw_weighted, Mapping):
            raise TypeError("weighted_dofs must be a mapping when supplied")
        weighted = {}
        iterator = iter(raw_weighted)
        _exact_guard(
            model,
            context="nonlinear displacement control weights iterator",
        )
        while True:
            try:
                raw_key = next(iterator)
            except StopIteration:
                _exact_guard(
                    model,
                    context="nonlinear displacement control weights end",
                )
                break
            _exact_guard(
                model,
                context="nonlinear displacement control weight key observation",
            )
            raw_weight = raw_weighted[raw_key]
            _exact_guard(
                model,
                context="nonlinear displacement control weight observation",
            )
            if isinstance(raw_key, tuple):
                if len(raw_key) != 2:
                    raise ValueError(
                        "weighted displacement-control node keys must have two members"
                    )
                owned_node = int(raw_key[0])
                _exact_guard(
                    model,
                    context="nonlinear displacement control weight node conversion",
                )
                raw_key_dof = raw_key[1]
                owned_dof = (
                    str(raw_key_dof)
                    if isinstance(raw_key_dof, str)
                    else int(raw_key_dof)
                )
                _exact_guard(
                    model,
                    context="nonlinear displacement control weight dof conversion",
                )
                key: Any = (owned_node, owned_dof)
            else:
                key = int(raw_key)
                _exact_guard(
                    model,
                    context="nonlinear displacement control weight key conversion",
                )
            weight = float(raw_weight)
            _exact_guard(
                model,
                context="nonlinear displacement control weight conversion",
            )
            weighted[key] = weight
            _exact_guard(
                model,
                context="nonlinear displacement control weight insertion",
            )
    owned = DisplacementControl(
        node_id=node_id,
        dof=dof,
        target_displacement=target,
        weighted_dofs=weighted,
    )
    _exact_guard(model, context="nonlinear displacement control construction")
    return owned


def _owned_fracture_config(
    model: "FEModel",
    value: Any,
    *,
    _exact_guard: Any,
) -> Optional[FractureConfig]:
    if value is None:
        return None
    if not isinstance(value, FractureConfig):
        raise TypeError("fracture_config must be a FractureConfig or None")

    def observed(name: str) -> Any:
        member = getattr(value, name)
        _exact_guard(model, context=f"fracture config {name} observation")
        return member

    def converted(name: str, converter: Any) -> Any:
        made = converter(observed(name))
        _exact_guard(model, context=f"fracture config {name} conversion")
        return made

    raw_scope = observed("element_scope")
    scope = tuple(
        str(member)
        for member in _guarded_config_sequence(
            model,
            raw_scope,
            context="fracture config element_scope",
            _exact_guard=_exact_guard,
        )
    )
    _exact_guard(model, context="fracture config element_scope conversion")
    owned = FractureConfig(
        threshold=converted("threshold", float),
        residual_stiffness_fraction=converted(
            "residual_stiffness_fraction",
            float,
        ),
        max_deleted_fraction=converted("max_deleted_fraction", float),
        min_load_factor=converted("min_load_factor", float),
        element_scope=scope,
        delete_after_converged_increment=converted(
            "delete_after_converged_increment",
            bool,
        ),
        record_history=converted("record_history", bool),
    )
    _exact_guard(model, context="fracture config construction")
    return owned


def _owned_imperfection_input(
    model: "FEModel",
    value: Any,
    *,
    _exact_guard: Any,
) -> Any:
    if value is None:
        return None
    from .imperfections import ImperfectionField

    candidate = value
    if not isinstance(candidate, (ImperfectionField, Mapping)):
        converter = getattr(candidate, "to_field", None)
        _exact_guard(model, context="imperfection converter observation")
        if converter is None:
            raise TypeError(
                f"Cannot convert {type(candidate).__name__} to ImperfectionField"
            )
        candidate = converter(model)
        _exact_guard(model, context="imperfection converter callback")

    if isinstance(candidate, Mapping):
        raw_offsets = candidate
        raw_name: Any = "imperfection"
        raw_metadata: Any = {}
    elif isinstance(candidate, ImperfectionField):
        raw_offsets = getattr(candidate, "offsets")
        _exact_guard(model, context="imperfection offsets observation")
        raw_name = getattr(candidate, "name")
        _exact_guard(model, context="imperfection name observation")
        raw_metadata = getattr(candidate, "metadata")
        _exact_guard(model, context="imperfection metadata observation")
    else:
        arrays_provider = getattr(candidate, "as_arrays")
        _exact_guard(model, context="imperfection array provider observation")
        raw_offsets = arrays_provider()
        _exact_guard(model, context="imperfection array provider callback")
        raw_name = getattr(candidate, "name", "imperfection")
        _exact_guard(model, context="imperfection name observation")
        raw_metadata = getattr(candidate, "metadata", {})
        _exact_guard(model, context="imperfection metadata observation")

    if not isinstance(raw_offsets, Mapping):
        raise TypeError("imperfection offsets must be a mapping")
    offsets: Dict[int, np.ndarray] = {}
    iterator = iter(raw_offsets)
    _exact_guard(model, context="imperfection offsets iterator")
    while True:
        try:
            raw_node_id = next(iterator)
        except StopIteration:
            _exact_guard(model, context="imperfection offsets end")
            break
        _exact_guard(model, context="imperfection node observation")
        node_id = int(raw_node_id)
        _exact_guard(model, context="imperfection node conversion")
        raw_offset = raw_offsets[raw_node_id]
        _exact_guard(model, context="imperfection offset observation")
        offset = np.asarray(raw_offset, dtype=np.float64).reshape(-1).copy()
        _exact_guard(model, context="imperfection offset conversion")
        offsets[node_id] = offset
    name = str(raw_name)
    _exact_guard(model, context="imperfection name conversion")
    metadata = _guarded_plain_config_snapshot(
        model,
        raw_metadata,
        context="imperfection metadata",
        _exact_guard=_exact_guard,
    )
    if not isinstance(metadata, Mapping):
        raise TypeError("imperfection metadata must be a mapping")
    owned = ImperfectionField(offsets, name=name, metadata=metadata)
    _exact_guard(model, context="imperfection construction")
    return owned


@resource_threaded
@capture_nonlinear_analysis_diagnostics
def _solve_static_nonlinear_under_lease(
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
    restart_checkpoint: Optional[Any] = None,
    emit_restart_checkpoint: bool = False,
    _qualified_runtime_guard: Any = None,
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

    ``restart_checkpoint`` resumes the last committed solver transaction.  It
    is mutually exclusive with the lower-level initial-state arguments and is
    fingerprint-validated before stiffness or load assembly.
    """
    raw_exact_guard = _EXACT_QUALIFIED_LIFECYCLE_GUARD
    lease_model = model

    def exact_guard(
        observed_model: "FEModel",
        *,
        context: str,
    ) -> Dict[str, Any]:
        result = raw_exact_guard(observed_model, context=context)
        # Imperfection handling may replace ``model`` with a solver-owned
        # copy.  The non-renewable lease remains bound to the caller's model
        # and global authority generation, while the exact lifecycle guard
        # validates whichever owned model is being observed.
        _qualified_runtime_guard(lease_model, context=context)
        return result

    lease_namespace = getattr(_qualified_runtime_guard, "__dict__", {})
    owned_items_provider = (
        dict.get(lease_namespace, "_qualified_owned_element_items")
        if type(lease_namespace) is dict
        else None
    )
    trusted_runtime_guard = (
        dict.get(lease_namespace, "_qualified_trusted_require")
        if type(lease_namespace) is dict
        else None
    )
    owned_items = (
        owned_items_provider()
        if callable(owned_items_provider)
        else None
    )
    exact_qualified_internal_fast_path = bool(
        type(owned_items) is tuple
        and owned_items
        and callable(trusted_runtime_guard)
        and all(
            type(element)
            in {_QualifiedE4PLShellElement, _QualifiedE4PLS3ShellElement}
            for element_id, element in owned_items
            if type(element_id) is int
        )
        and all(type(element_id) is int for element_id, _element in owned_items)
    )

    def internal_guard(
        observed_model: "FEModel",
        *,
        context: str,
    ) -> Dict[str, Any]:
        """Use the captured lease only across exact built-in solver work.

        Caller-controlled observations retain ``exact_guard``.  Mixed,
        generic, and imperfection-owned models also fail closed to that full
        lifecycle scan.  The lease is non-renewable and still rejects every
        Q4, S3, assembly, numerical, and model-input generation change.
        """

        if (
            not exact_qualified_internal_fast_path
            or observed_model is not lease_model
        ):
            return exact_guard(observed_model, context=context)
        trusted_runtime_guard(lease_model, context=context)
        return {}

    def cancellation_guard(*, context: str) -> Dict[str, Any]:
        """Treat an absent token as internal; arbitrary tokens remain hostile."""

        guard = internal_guard if cancellation_token is None else exact_guard
        return guard(model, context=context)

    exact_guard(model, context="nonlinear static solve preflight")
    cancellation_safe_point(cancellation_token, "nonlinear_static.start")
    exact_guard(model, context="nonlinear static start cancellation")
    owned_config = _owned_nonlinear_static_operation_config(
        model,
        max_load_factor=max_load_factor,
        num_steps=num_steps,
        max_iterations=max_iterations,
        tolerance=tolerance,
        num_layers=num_layers,
        min_step_fraction=min_step_fraction,
        control=control,
        kinematics=kinematics,
        corotational_tangent=corotational_tangent,
        equilibrate_initial_state=equilibrate_initial_state,
        record_increment_snapshots=record_increment_snapshots,
        emit_restart_checkpoint=emit_restart_checkpoint,
        _exact_guard=exact_guard,
    )
    max_load_factor = owned_config.max_load_factor
    num_steps = owned_config.num_steps
    max_iterations = owned_config.max_iterations
    tolerance = owned_config.tolerance
    num_layers = owned_config.num_layers
    min_step_fraction = owned_config.min_step_fraction
    control = owned_config.control
    kinematics = owned_config.kinematics
    corotational_tangent = owned_config.corotational_tangent
    equilibrate_initial_state = owned_config.equilibrate_initial_state
    record_increment_snapshots = owned_config.record_increment_snapshots
    emit_restart_checkpoint = owned_config.emit_restart_checkpoint
    load_program = _owned_nonlinear_load_program(
        model,
        load_program,
        _exact_guard=exact_guard,
    )
    displacement_control = _owned_displacement_control(
        model,
        displacement_control,
        _exact_guard=exact_guard,
    )
    fracture_config = _owned_fracture_config(
        model,
        fracture_config,
        _exact_guard=exact_guard,
    )
    imperfection = _owned_imperfection_input(
        model,
        imperfection,
        _exact_guard=exact_guard,
    )
    if num_steps <= 0:
        raise ValueError("num_steps must be positive")
    control_name = control
    if control_name not in {"force", "displacement"}:
        raise ValueError("control must be 'force' or 'displacement'")
    if kinematics not in {"von_karman", "corotational"}:
        raise ValueError("kinematics must be 'von_karman' or 'corotational'")
    parsed_restart_checkpoint: Optional[Dict[str, Any]] = None
    if restart_checkpoint is not None:
        emit_restart_checkpoint = True
        if initial_element_states is not None:
            raise ValueError(
                "restart_checkpoint cannot be combined with initial_element_states"
            )
        if initial_displacements is not None:
            raise ValueError(
                "restart_checkpoint cannot be combined with initial_displacements"
            )
        if initial_fields is not None:
            raise ValueError("restart_checkpoint cannot be combined with initial_fields")
        if equilibrate_initial_state not in {None, False}:
            raise ValueError(
                "restart_checkpoint cannot request initial-state re-equilibration"
            )
        parsed_restart_checkpoint = load_nonlinear_checkpoint(
            restart_checkpoint,
            _exact_guard=exact_guard,
            _guard_model=model,
        )
        require_model_element_capabilities(
            model,
            "static_restart_history",
            context="solve_static_nonlinear",
        )
    elif emit_restart_checkpoint:
        require_model_element_capabilities(
            model,
            "static_restart_history",
            context="solve_static_nonlinear",
        )
    initial_element_states = _owned_initial_element_states(
        model,
        initial_element_states,
        _exact_guard=exact_guard,
    )
    initial_displacements = _owned_initial_displacements(
        model,
        initial_displacements,
        _exact_guard=exact_guard,
    )
    if initial_fields is not None:
        initial_fields = dict(initial_fields)
        exact_guard(model, context="nonlinear static initial-fields ownership")
    initial_fields_present = initial_fields is not None and len(initial_fields) > 0
    exact_guard(model, context="nonlinear static initial-fields disposition")
    if imperfection is not None:
        require_model_element_capabilities(
            model,
            "initial_fields",
            context="solve_static_nonlinear",
        )
    elif initial_fields_present:
        require_model_element_capabilities(
            model,
            "initial_fields",
            context="solve_static_nonlinear",
            element_ids=initial_fields,
        )
    if initial_element_states is not None:
        require_model_element_capabilities(
            model,
            "static_restart_history",
            context="solve_static_nonlinear",
            element_ids=initial_element_states,
        )
    require_model_nonlinear_workflow_capabilities(
        model,
        context="solve_static_nonlinear",
    )
    specified_load_cases = [
        case
        for case in (
            [load_case, constant_load_case]
            + ([] if load_program is None else [stage.load_case for stage in load_program.stages])
        )
        if case is not None
    ]
    follower_active = any(
        _has_follower_pressure(
            case,
            model=model,
            _exact_guard=exact_guard,
        )
        for case in specified_load_cases
    )
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
    settings = _coerce_convergence_settings(
        convergence_settings,
        _post_observation=lambda: exact_guard(
            model,
            context="nonlinear static convergence-settings observation",
        ),
    )
    exact_guard(model, context="nonlinear static convergence settings")
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
        exact_guard(model, context="nonlinear static imperfection observation")
    restart_analysis_contract = _static_restart_analysis_contract(
        model=model,
        load_case=load_case,
        constant_load_case=constant_load_case,
        load_program=load_program,
        control_name=control_name,
        displacement_control=displacement_control,
        num_layers=num_layers,
        max_iterations=max_iterations,
        tolerance=tolerance,
        effective_min_step_fraction=effective_min_step_fraction,
        settings=settings,
        fracture_config=fracture_config,
        resource_config=resource_config,
        kinematics=kinematics,
        resolved_corotational_tangent=resolved_corotational_tangent,
    )
    restored_static_path: Optional[Dict[str, Any]] = None
    validated_restart = None
    if parsed_restart_checkpoint is not None:
        validated_restart = validate_nonlinear_checkpoint(
            parsed_restart_checkpoint,
            analysis_kind="static",
            model=model,
            analysis_contract=restart_analysis_contract,
            num_layers=num_layers,
        )
        exact_guard(model, context="nonlinear static checkpoint validation")
        restored_static_path = _restore_static_path_state(
            validated_restart.path_state,
            control_name=control_name,
            total_dofs=int(model.mesh.dof_manager.total_dofs),
        )
        if restored_static_path["terminal_status"] != "completed":
            raise ValueError(
                "restart checkpoint does not end at a continuable completed static target"
            )
        if control_name == "force":
            requested_target = (
                load_program.total_factor
                if load_program is not None and max_load_factor == 1.0
                else float(max_load_factor)
            )
            if restored_static_path["load_factor"] > requested_target + 1.0e-12:
                raise ValueError(
                    "restart checkpoint is beyond the requested maximum load factor"
                )
            recorded_deleted = {
                int(record.element_id)
                for record in restored_static_path["deletion_records"]
            }
            if recorded_deleted != validated_restart.deleted_element_ids:
                raise ValueError(
                    "restart checkpoint deletion records and deleted IDs disagree"
                )
            if fracture_config is None and recorded_deleted:
                raise ValueError(
                    "restart checkpoint contains fracture history without fracture_config"
                )
        if validated_restart.activity is not None:
            model.set_element_activity(validated_restart.activity)
        initial_element_states = validated_restart.element_states
        initial_displacements = validated_restart.displacements
        equilibrate_initial_state = False
    _ensure_nonlinear_acceleration()
    model.apply_boundary_conditions()
    exact_guard(model, context="nonlinear static boundary conditions")

    # The constraint transformation only depends on supports/MPCs; the
    # elastic stiffness is assembled once to build it (and warms the element
    # caches used by the nonlinear kernels).
    K0, stiffness_info = assemble_stiffness_matrix(model)
    exact_guard(model, context="nonlinear static stiffness assembly")
    stage_vectors: List[np.ndarray] = []
    stage_infos: List[Dict[str, Any]] = []
    if load_program is not None:
        for stage in load_program.stages:
            vector, stage_info = assemble_load_vector(model, stage.load_case)
            exact_guard(model, context="nonlinear static stage-load assembly")
            stage_vectors.append(vector)
            stage_infos.append({"name": stage.name, "target_factor": stage.target_factor, **stage_info})
        F_prop = np.sum(np.vstack(stage_vectors), axis=0) if stage_vectors else np.zeros(K0.shape[0], dtype=float)
        load_info = {"vector_type": "load_program", "stages": stage_infos}
    else:
        F_prop, load_info = assemble_load_vector(model, load_case)
        exact_guard(model, context="nonlinear static proportional-load assembly")

    if constant_load_case is not None:
        F_const, constant_load_info = assemble_load_vector(model, constant_load_case)
        exact_guard(model, context="nonlinear static constant-load assembly")
    else:
        F_const = np.zeros_like(F_prop)
        constant_load_info = None
    _, _, T, u0, _, constraint_info = build_constraint_transformation(K0, F_prop, model)
    exact_guard(model, context="nonlinear static constraint transformation")
    if restored_static_path is not None:
        restored_static_path = _restore_static_path_state(
            validated_restart.path_state,
            control_name=control_name,
            n_red=int(T.shape[1]),
            total_dofs=int(model.mesh.dof_manager.total_dofs),
        )

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
    if validated_restart is not None:
        info["restart"] = {
            "schema": validated_restart.payload["schema"],
            "checkpoint_sha256": validated_restart.payload["checkpoint_sha256"],
            "resumed_load_factor": float(restored_static_path["load_factor"]),
            "resumed_step_index": int(restored_static_path["step_index"]),
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
    checkpoint_resume = validated_restart is not None
    force_restart = (
        control_name == "force"
        and initial_displacements is not None
        and not checkpoint_resume
    )
    if control_name == "force" and checkpoint_resume:
        resumed_lam = float(restored_static_path["load_factor"])
        q = np.asarray(
            restored_static_path["reduced_coordinates"], dtype=float
        ).copy()
        supplied_full = np.asarray(
            initial_displacements, dtype=np.float64
        ).reshape(-1)
        restored_mode = restored_static_path.get("affine_path_mode")
        restored_base = restored_static_path.get("exact_base_offset")
        projected_free = np.asarray(T @ q, dtype=np.float64).reshape(-1)
        proportional_affine = np.asarray(
            resumed_lam * np.asarray(u0, dtype=np.float64).reshape(-1),
            dtype=np.float64,
        )
        if restored_mode is None:
            # Pre-schema checkpoints are migrated from their independently
            # hash-bound committed displacement.  Exact equality identifies
            # the proportional path; every other compatible legacy state is
            # retained as a fixed affine restart rather than projected onto a
            # different path.
            proportional_projection = projected_free + proportional_affine
            if np.array_equal(proportional_projection, supplied_full):
                force_affine_path_mode = "PROPORTIONAL_PRESCRIBED_FIELD"
                force_exact_base_offset = np.zeros_like(supplied_full)
            else:
                force_affine_path_mode = "FIXED_RESTART_AFFINE_STATE"
                force_exact_base_offset = _exact_binary64_additive_offset(
                    supplied_full,
                    projected_free,
                    context="legacy static restart affine state",
                )
            info_migration = "MIGRATED_FROM_BOUND_COMMITTED_DISPLACEMENT"
        else:
            force_affine_path_mode = str(restored_mode)
            force_exact_base_offset = np.asarray(
                restored_base, dtype=np.float64
            ).reshape(-1).copy()
            info_migration = "CURRENT_EXACT_BASE_SCHEMA"
        path_projection = projected_free.copy()
        if force_affine_path_mode == "PROPORTIONAL_PRESCRIBED_FIELD":
            path_projection = path_projection + proportional_affine
            initial_affine_scale = resumed_lam
        else:
            # The scale is diagnostic-only for constraint reporting.  The
            # exact fixed base below remains the sole reconstruction authority.
            _unused_q, initial_affine_scale = (
                _reduced_coordinates_with_affine_scale(T, u0, supplied_full)
            )
        initial_affine_offset = force_exact_base_offset
        initial_committed_displacement = np.asarray(
            path_projection + force_exact_base_offset, dtype=np.float64
        ).reshape(-1)
        if not np.array_equal(initial_committed_displacement, supplied_full):
            raise ValueError(
                "restart checkpoint affine path does not exactly reconstruct "
                "its committed displacement"
            )
    elif control_name == "force":
        q, initial_affine_scale = _reduced_coordinates_with_affine_scale(
            T,
            u0,
            initial_displacements,
        )
        if initial_displacements is None:
            force_affine_path_mode = "PROPORTIONAL_PRESCRIBED_FIELD"
            force_exact_base_offset = np.zeros(int(T.shape[0]), dtype=float)
            initial_affine_offset = force_exact_base_offset
            initial_committed_displacement = np.asarray(
                T @ q, dtype=np.float64
            ).reshape(-1)
            info_migration = "NOT_A_RESTART"
        else:
            # Retain the supplied committed vector bit for bit.  LSQR proves
            # compatibility but its reconstructed affine scale can differ by
            # a few ulps; binding a state to that rounded projection would
            # reject a checkpoint/result produced by this same solver.  The
            # exact residual is a constant restart offset, so
            # ``T @ q + offset`` reconstructs the supplied state exactly while
            # keeping the established fixed-affine restart path.
            supplied_full = np.asarray(
                initial_displacements, dtype=np.float64
            ).reshape(-1)
            projected_free = np.asarray(T @ q, dtype=np.float64).reshape(-1)
            force_affine_path_mode = "FIXED_RESTART_AFFINE_STATE"
            force_exact_base_offset = _exact_binary64_additive_offset(
                supplied_full,
                projected_free,
                context="initial_displacements fixed-affine restart path",
            )
            initial_affine_offset = force_exact_base_offset
            initial_committed_displacement = np.asarray(
                projected_free + force_exact_base_offset,
                dtype=np.float64,
            ).reshape(-1)
            info_migration = "DIRECT_EXACT_INITIAL_DISPLACEMENT"
    else:
        q = (
            np.asarray(restored_static_path["reduced_coordinates"], dtype=float).copy()
            if checkpoint_resume
            else _reduced_coordinates(T, u0, initial_displacements)
        )
        initial_affine_scale = 1.0
        initial_affine_offset = np.asarray(u0, dtype=float).reshape(-1)
        initial_committed_displacement = np.asarray(
            T @ q + np.asarray(u0, dtype=float).reshape(-1),
            dtype=float,
        ).reshape(-1)
    if checkpoint_resume and not np.array_equal(
        initial_committed_displacement,
        np.asarray(initial_displacements, dtype=float).reshape(-1),
    ):
        raise ValueError(
            "restart checkpoint reduced coordinates do not exactly reconstruct "
            "its committed displacement"
        )
    supplied_state_ids = tuple(
        sorted(int(value) for value in (initial_element_states or {}))
    )
    preflight_deleted_ids = (
        tuple(sorted(int(value) for value in validated_restart.deleted_element_ids))
        if validated_restart is not None
        else ()
    )
    preflight_deletion_records = (
        tuple(restored_static_path["deletion_records"])
        if restored_static_path is not None and control_name == "force"
        else ()
    )
    deleted_qualified_dispositions: Dict[int, Any] = {}
    committed_states = _prepare_qualified_q4_states_for_nonlinear_solve(
        model,
        initial_committed_displacement,
        committed_states,
        num_layers,
        info,
        supplied_element_ids=supplied_state_ids,
        ordinary_restart=bool(
            initial_element_states is not None
            and initial_displacements is not None
            and equilibrate_initial_state is not True
        ),
        allow_explicit_initial_material_states=bool(
            validated_restart is None
            and initial_element_states is not None
            and initial_displacements is None
        ),
        expected_deleted_element_ids=preflight_deleted_ids,
        deletion_records=preflight_deletion_records,
        residual_stiffness_fraction=(
            None
            if fracture_config is None
            else float(fracture_config.residual_stiffness_fraction)
        ),
        deleted_dispositions=deleted_qualified_dispositions,
    )
    # Native multiplicative rotations are solver-owned and must exist before
    # the first possible constitutive evaluation (initial-field equilibrium or
    # a fully constrained prescribed state).  Q4-only models retain the prior
    # dictionary/array activation behavior.
    committed_states = _activate_nonlinear_state_storage(
        model,
        committed_states,
        num_layers,
        info,
        kinematics=kinematics,
        committed_displacements=initial_committed_displacement,
        noncurrent_native_element_ids=preflight_deleted_ids,
    )
    if (
        initial_fields_present
        and initial_displacements is not None
        and equilibrate_initial_state is not False
    ):
        raise ValueError(
            "initial_fields combined with initial_displacements is ambiguous during "
            "automatic equilibration; pass equilibrate_initial_state=False for an "
            "already-equilibrated restart."
        )
    if n_red == 0:
        fully_constrained_displacement = (
            initial_committed_displacement.copy()
            if checkpoint_resume
            else (
                initial_affine_offset
                if force_restart
                else np.asarray(u0, dtype=float).reshape(-1)
            )
        )
        has_initial_fields = any(
            _state_has_initial_field(state) for state in committed_states.values()
        )
        requires_native_tl_evaluation = any(
            bool(
                getattr(
                    element,
                    "formulation_native_total_lagrangian",
                    False,
                )
            )
            for element in model.mesh.elements.values()
        )
        requested_equilibration = (
            initial_fields_present
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
        if has_initial_fields or requires_native_tl_evaluation:
            # There are no admissible displacement corrections, so the
            # prescribed field/native kinematics are already equilibrated in
            # the free-DOF sense; any imbalance is carried by reactions.
            # Native-TL elements still require one real evaluation so their
            # accepted element-owned kinematic state is not silently omitted.
            internal_force, _unused_tangent, trial_states = (
                _assemble_nonlinear_system(
                    model,
                    fully_constrained_displacement,
                    committed_states,
                    num_layers,
                    # A fully constrained plastic Q4 still needs the exact
                    # accepted return-map parent for its committed tangent.
                    # Evaluate that one accepted candidate with its tangent;
                    # never promote an origin-less residual-only output.
                    tangent=True,
                    kinematics=kinematics,
                    corotational_tangent=resolved_corotational_tangent,
                )
            )
            internal_guard(
                model,
                context="nonlinear static fully-constrained assembly",
            )
            committed_states = _commit_nonlinear_state_candidate(
                committed_states,
                trial_states,
                model=model,
                accepted_displacements=fully_constrained_displacement,
            )
            info["initial_state_equilibration"][
                "constrained_internal_force_norm"
            ] = float(np.linalg.norm(internal_force))
            if requires_native_tl_evaluation:
                info["initial_state_equilibration"]["native_tl_evaluated"] = True
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
        final_committed_states = _materialize_final_nonlinear_states(
            committed_states,
            info,
        )
        final_committed_states = _finalize_nonlinear_element_states(
            model,
            fully_constrained_displacement,
            final_committed_states,
            num_layers,
            kinematics=kinematics,
        )
        final_committed_states = _seal_final_qualified_q4_states(
            model,
            fully_constrained_displacement,
            final_committed_states,
            num_layers,
            info,
            kinematics=kinematics,
        )
        return NonlinearStaticResult(
            [],
            "empty_reduced_system",
            fully_constrained_displacement.copy(),
            0.0,
            final_committed_states,
            info,
        )

    has_initial_fields = any(_state_has_initial_field(state) for state in committed_states.values())
    restored_initial_fields = has_initial_fields and not initial_fields_present
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
    should_equilibrate = (
        initial_fields_present
        if equilibrate_initial_state is None
        else bool(equilibrate_initial_state)
    )
    if should_equilibrate and has_initial_fields:
        q, committed_states, initialization_history, initialization_failure = _equilibrate_initial_fields(
            model=model,
            T=T,
            u0=initial_affine_offset,
            committed_states=committed_states,
            num_layers=num_layers,
            max_iterations=max_iterations,
            tolerance=tolerance,
            kinematics=kinematics,
            corotational_tangent=resolved_corotational_tangent,
            general_tangent=general_tangent,
            initial_reduced_displacements=q,
            cancellation_token=cancellation_token,
            _exact_guard=exact_guard,
        )
        exact_guard(model, context="nonlinear static initial equilibration")
        info["initial_state_equilibration"] = {
            "requested": True,
            "converged": initialization_failure is None,
            "iterations": len(initialization_history),
            "history": initialization_history,
            "failure_reason": initialization_failure,
        }
        if initialization_failure is not None:
            u_failed = np.asarray(
                T @ q + initial_affine_offset,
                dtype=float,
            ).reshape(-1)
            info["failure_reason"] = initialization_failure
            info["stop_reason"] = initialization_failure
            info["status_category"] = _nonlinear_status_category("diverged", initialization_failure)
            committed_states = _materialize_final_nonlinear_states(
                committed_states,
                info,
            )
            # The installed result-recovery finalizer may evaluate mechanics
            # and add displacement-derived fields.  No candidate was accepted
            # on this failure path, so the last committed materialized pair is
            # the only honest output and is marked nonauthoritative below.
            committed_states = _mark_failed_qualified_q4_states(
                model,
                u_failed,
                committed_states,
                num_layers,
                info,
                failure_reason=initialization_failure,
                kinematics=kinematics,
            )
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
    steps: List[NonlinearStaticStep] = (
        list(restored_static_path["steps"])
        if restored_static_path is not None
        else []
    )
    status = "completed"
    deleted_element_ids: set[int] = (
        set(validated_restart.deleted_element_ids)
        if validated_restart is not None
        else set()
    )
    deletion_records: List[DeletedElementRecord] = (
        list(restored_static_path["deletion_records"])
        if restored_static_path is not None and control_name == "force"
        else []
    )
    fracture_warnings: List[str] = (
        list(restored_static_path["fracture_warnings"])
        if restored_static_path is not None and control_name == "force"
        else []
    )
    max_fracture_utilization = (
        float(restored_static_path["max_fracture_utilization"])
        if restored_static_path is not None and control_name == "force"
        else 0.0
    )

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

    def external_load_guard(*, context: str) -> Dict[str, Any]:
        """Use the lease for the preassembled affine load path only."""

        guard = (
            internal_guard
            if not follower_active and not deleted_element_ids
            else exact_guard
        )
        return guard(model, context=context)

    if control_name == "displacement":
        if displacement_control is None:
            raise ValueError("displacement_control is required when control='displacement'")
        preload_result: Optional[NonlinearStaticResult] = None
        if (
            load_program is not None
            and len(load_program.stages) > 1
            and not checkpoint_resume
        ):
            # Each permanent stage is first solved by force control and its
            # displacement/material state committed.  The final stage then
            # starts from that exact checkpoint under displacement control;
            # the earlier loads remain constant in the controlled equilibrium.
            preload_program = NonlinearLoadProgram(tuple(load_program.stages[:-1]))
            preload_result = _solve_static_nonlinear_under_lease(
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
                _qualified_runtime_guard=_qualified_runtime_guard,
            )
            exact_guard(model, context="nonlinear static preload result")
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
            committed_states = _prepare_qualified_q4_states_for_nonlinear_solve(
                model,
                np.asarray(preload_result.displacements, dtype=float).reshape(-1),
                committed_states,
                num_layers,
                info,
                supplied_element_ids=tuple(sorted(int(value) for value in committed_states)),
                ordinary_restart=True,
            )
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

        committed_states = _activate_nonlinear_state_storage(
            model,
            committed_states,
            num_layers,
            info,
            kinematics=kinematics,
            committed_displacements=np.asarray(T @ q + u0, dtype=float).reshape(-1),
        )
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
            initial_load_factor=(
                float(restored_static_path["load_factor"])
                if restored_static_path is not None
                else 0.0
            ),
            step_index_offset=(
                int(restored_static_path["step_index"])
                if restored_static_path is not None
                else 0
            ),
            initial_steps=(
                restored_static_path["steps"]
                if restored_static_path is not None
                else ()
            ),
            initial_history=(
                restored_static_path["force_displacement_history"]
                if restored_static_path is not None
                else ()
            ),
            initial_total_iterations=(
                int(restored_static_path["total_iterations"])
                if restored_static_path is not None
                else 0
            ),
            restart_analysis_contract=(
                restart_analysis_contract if emit_restart_checkpoint else None
            ),
            _exact_guard=exact_guard,
        )
        exact_guard(model, context="nonlinear static displacement-control result")
        controlled_result.element_states = _seal_final_qualified_q4_states(
            model,
            controlled_result.displacements,
            controlled_result.element_states,
            num_layers,
            controlled_result.info,
            kinematics=kinematics,
        )
        if controlled_result.restart_checkpoint is not None:
            # An accelerated displacement-control implementation may have
            # built its checkpoint immediately before the public lifecycle
            # seam. Recreate it over the sealed states without changing its
            # already canonical path transaction.
            prior_checkpoint = controlled_result.restart_checkpoint
            controlled_result.restart_checkpoint = create_nonlinear_checkpoint(
                analysis_kind="static",
                model=model,
                analysis_contract=restart_analysis_contract,
                displacements=controlled_result.displacements,
                element_states=controlled_result.element_states,
                deleted_element_ids=tuple(
                    int(value)
                    for value in prior_checkpoint.get("deleted_element_ids", ())
                ),
                path_state=prior_checkpoint["path_state"],
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
            if emit_restart_checkpoint:
                checkpoint_history = copy.deepcopy(
                    preload_result.info.get("force_displacement_history", [])
                ) + copy.deepcopy(
                    controlled_result.info.get("force_displacement_history", [])
                )
                for index, item in enumerate(checkpoint_history, start=1):
                    if isinstance(item, dict):
                        item["step_index"] = index
                controlled_result.info[
                    "force_displacement_history"
                ] = checkpoint_history
                controlled_result.restart_checkpoint = create_nonlinear_checkpoint(
                    analysis_kind="static",
                    model=model,
                    analysis_contract=restart_analysis_contract,
                    displacements=controlled_result.displacements,
                    element_states=controlled_result.element_states,
                    deleted_element_ids=(),
                    path_state=_static_restart_path_payload(
                        control_name="displacement",
                        load_factor=controlled_result.load_factor,
                        step_index=len(controlled_result.steps),
                        total_iterations=int(
                            controlled_result.info.get("total_newton_iterations", 0)
                        ),
                        steps=controlled_result.steps,
                        force_displacement_history=checkpoint_history,
                        reduced_coordinates=np.asarray(
                            controlled_result.restart_checkpoint["path_state"][
                                "reduced_coordinates"
                            ],
                            dtype=float,
                        ),
                        terminal_status=controlled_result.status,
                        failure_reason=controlled_result.failure_reason,
                    ),
                )
        return controlled_result

    committed_states = _activate_nonlinear_state_storage(
        model,
        committed_states,
        num_layers,
        info,
        kinematics=kinematics,
        committed_displacements=initial_committed_displacement,
        noncurrent_native_element_ids=preflight_deleted_ids,
    )
    if restored_static_path is not None:
        base_step = float(restored_static_path["base_step"])
        min_step = float(restored_static_path["minimum_step"])
        max_step = float(restored_static_path["maximum_step"])
        step_size = float(restored_static_path["next_step_size"])
        lam = float(restored_static_path["load_factor"])
        step_index = int(restored_static_path["step_index"])
        total_iterations = int(restored_static_path["total_iterations"])
    else:
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
    prescribed_base = np.asarray(
        force_exact_base_offset, dtype=np.float64
    ).reshape(-1).copy()
    prescribed_slope = (
        prescribed_offset
        if force_affine_path_mode == "PROPORTIONAL_PRESCRIBED_FIELD"
        else np.zeros_like(prescribed_offset)
    )
    info["prescribed_displacement_path"] = {
        "mode": (
            "proportional_to_load_factor"
            if force_affine_path_mode == "PROPORTIONAL_PRESCRIBED_FIELD"
            else "restart_fixed_affine_state"
        ),
        "schema_mode": force_affine_path_mode,
        "restart_schema_disposition": info_migration,
        "initial_affine_scale": float(initial_affine_scale),
        "affine_scale_slope": (
            1.0
            if force_affine_path_mode == "PROPORTIONAL_PRESCRIBED_FIELD"
            else 0.0
        ),
        "target_max_abs": float(np.max(np.abs(prescribed_offset)))
        if prescribed_offset.size
        else 0.0,
    }

    def full_displacement(q_reduced: np.ndarray, path_factor: float) -> np.ndarray:
        """Expand a force-control state on its affine constraint path."""
        return np.asarray(
            T @ q_reduced + prescribed_base + float(path_factor) * prescribed_slope,
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
        cancellation_guard(
            context="nonlinear static force increment cancellation",
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
        internal_guard(model, context="nonlinear static force tangent assembly")
        F_ext, K_ext, _stage_factors, _active_stage = external_load_at(
            path_factor,
            u,
            tangent=True,
        )
        external_load_guard(context="nonlinear static force external load")
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
            cancellation_guard(
                context="nonlinear static force iteration cancellation",
            )
            if status_callback is not None:
                # ``num_steps`` defines the initial load partition, not a hard
                # count: adaptive cutbacks/growth may produce far more or
                # fewer converged increments.  A fraction such as 1459/10 was
                # therefore numerically valid but semantically misleading.
                status_callback(
                    f"Increment trial {step_index + 1} | "
                    f"load factor {path_factor:.6g} / {target_load_factor:.6g} | "
                    f"increment {path_factor - lam:.3g} | "
                    f"Newton iteration {iteration} | residual {residual_norm:.3e}"
                )
                exact_guard(
                    model,
                    context="nonlinear static status callback",
                )
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
                internal_guard(model, context="nonlinear static force tangent assembly")
                F_ext, K_ext, _stage_factors, _active_stage = external_load_at(
                    path_factor,
                    u,
                    tangent=True,
                )
                external_load_guard(context="nonlinear static force external load")
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
                cancellation_guard(
                    context="nonlinear static line-search cancellation",
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
                internal_guard(model, context="nonlinear static line-search assembly")
                F_ext_c, K_ext_c, _stage_factors, _active_stage = external_load_at(
                    path_factor,
                    u,
                    tangent=with_tangent,
                )
                external_load_guard(context="nonlinear static line-search load")
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
                        internal_guard(
                            model,
                            context="nonlinear static accepted line-search assembly",
                        )
                        F_ext_c, K_ext_c, _stage_factors, _active_stage = external_load_at(
                            path_factor,
                            u,
                            tangent=True,
                        )
                        external_load_guard(
                            context="nonlinear static accepted line-search load",
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

    force_displacement_history: List[Dict[str, Any]] = (
        copy.deepcopy(restored_static_path["force_displacement_history"])
        if restored_static_path is not None
        else []
    )
    convergence_adaptation: List[Dict[str, Any]] = (
        copy.deepcopy(restored_static_path["convergence_adaptation"])
        if restored_static_path is not None
        else []
    )
    snapshots: List[NonlinearIncrementSnapshot] = []
    force_line_search_next = (
        bool(restored_static_path["force_line_search_next"])
        if restored_static_path is not None
        else False
    )

    assembly_threads = None if resource_config is None else resource_config.assembly_threads
    with numba_thread_scope(assembly_threads):
        while lam < target_load_factor - 1.0e-12:
            cancellation_safe_point(
                cancellation_token,
                f"nonlinear_static.force.step:{step_index + 1}",
            )
            cancellation_guard(
                context="nonlinear static force step cancellation",
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
            external_load_guard(context="nonlinear static step external load")
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
                committed_states = _commit_nonlinear_state_candidate(
                    committed_states,
                    states_new,
                    model=model,
                    accepted_displacements=full_displacement(q_new, lam_trial),
                )
                internal_guard(
                    model,
                    context="nonlinear static committed-state observation",
                )
                force_line_search_next = False
                step_index += 1
                u = full_displacement(q, lam)
                control_value = float(np.linalg.norm(u))
                reaction_internal, _unused, _reaction_states = _assemble_nonlinear_system(
                    model,
                    u,
                    committed_states,
                    num_layers,
                    tangent=False,
                    deleted_element_ids=tuple(deleted_element_ids),
                    residual_stiffness_fraction=(
                        fracture_config.residual_stiffness_fraction
                        if fracture_config is not None else 1.0
                    ),
                    kinematics=kinematics,
                    corotational_tangent=resolved_corotational_tangent,
                    require_full_coordinates=True,
                )
                internal_guard(model, context="nonlinear static reaction assembly")
                # Reaction recovery is diagnostic-only; do not leave its trial
                # constitutive state active for the next accepted increment.
                _discard_nonlinear_state_candidate(committed_states)
                reaction_external, _unused_tangent, _unused_factors, _unused_stage = (
                    external_load_at(lam, u, tangent=False)
                )
                external_load_guard(context="nonlinear static reaction load")
                support_reactions = _support_reaction_resultants(
                    model, reaction_internal - reaction_external
                )
                exact_guard(model, context="nonlinear static support reactions")
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
                    exact_guard(
                        model,
                        context="nonlinear static fracture observation",
                    )
                    max_fracture_utilization = max(max_fracture_utilization, step_fracture_utilization)
                    if new_records:
                        for record in new_records:
                            deleted_element = model.mesh.get_element(
                                int(record.element_id)
                            )
                            if (
                                deleted_element is None
                                or (
                                    _qualified_q4_committed_state_hooks(
                                        deleted_element
                                    )
                                    is None
                                    and _qualified_s3_committed_state_validator(
                                        deleted_element
                                    )
                                    is None
                                )
                            ):
                                continue
                            deleted_dofs = np.asarray(
                                deleted_element.get_dof_mapping(model.mesh),
                                dtype=np.intp,
                            )
                            deleted_qualified_dispositions[int(record.element_id)] = {
                                "accepted_local_u": np.asarray(
                                    u[deleted_dofs], dtype=np.float64
                                ).tolist(),
                                "deletion_step_index": int(record.step_index),
                                "deletion_load_factor": float(record.load_factor),
                                "residual_stiffness_fraction": float(
                                    fracture_config.residual_stiffness_fraction
                                ),
                                "trigger_name": str(record.trigger_name),
                            }
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
                        support_reactions=support_reactions,
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
                        "support_reactions": {
                            name: list(values)
                            for name, values in support_reactions.items()
                        },
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
                    internal_guard(
                        model,
                        context="nonlinear static increment snapshot",
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
                    exact_guard(
                        model,
                        context="nonlinear static progress-state observation",
                    )
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
                        nominal_increment_count=int(num_steps),
                        load_increment=float(attempted_step_size),
                        support_reactions={
                            name: list(values)
                            for name, values in support_reactions.items()
                        },
                    )
                    exact_guard(
                        model,
                        context="nonlinear static progress callback",
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
                _discard_nonlinear_state_candidate(committed_states)
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
    committed_states = _materialize_final_nonlinear_states(committed_states, info)
    committed_states = _finalize_nonlinear_element_states(
        model,
        u_final,
        committed_states,
        num_layers,
        kinematics=kinematics,
    )
    committed_states = _seal_final_qualified_q4_states(
        model,
        u_final,
        committed_states,
        num_layers,
        info,
        kinematics=kinematics,
        deleted_element_ids=tuple(sorted(deleted_element_ids)),
        deleted_dispositions=deleted_qualified_dispositions,
        deletion_records=deletion_records,
        residual_stiffness_fraction=(
            None
            if fracture_config is None
            else float(fracture_config.residual_stiffness_fraction)
        ),
    )
    exact_guard(model, context="nonlinear static final state recovery")
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
        exact_guard(model, context="nonlinear static fracture summary")
    if load_program is not None:
        info["load_program_stage_factors"] = load_program.stage_factors(lam)
        exact_guard(model, context="nonlinear static load-program output")
    info["total_newton_iterations"] = total_iterations
    info["solve_time"] = time.time() - start_time
    final_affine_scale = (
        float(lam)
        if force_affine_path_mode == "PROPORTIONAL_PRESCRIBED_FIELD"
        else float(initial_affine_scale)
    )
    info["constraint_postcheck"] = constraint_residual_summary(
        model,
        u_final,
        affine_scale=final_affine_scale,
    )
    exact_guard(model, context="nonlinear static constraint postcheck")
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
    restart_payload = None
    if emit_restart_checkpoint:
        restart_payload = create_nonlinear_checkpoint(
            analysis_kind="static",
            model=model,
            analysis_contract=restart_analysis_contract,
            displacements=u_final,
            element_states=committed_states,
            deleted_element_ids=tuple(sorted(deleted_element_ids)),
            path_state=_static_restart_path_payload(
                control_name="force",
                load_factor=float(lam),
                step_index=int(step_index),
                total_iterations=int(total_iterations),
                steps=steps,
                force_displacement_history=force_displacement_history,
                reduced_coordinates=q,
                terminal_status=status,
                failure_reason=failure_reason,
                base_step=float(base_step),
                minimum_step=float(min_step),
                maximum_step=float(max_step),
                next_step_size=float(step_size),
                force_line_search_next=bool(force_line_search_next),
                convergence_adaptation=convergence_adaptation,
                deletion_records=[record.to_dict() for record in deletion_records],
                fracture_warnings=list(fracture_warnings),
                max_fracture_utilization=float(max_fracture_utilization),
                affine_path_mode=force_affine_path_mode,
                exact_base_offset=np.asarray(
                    prescribed_base, dtype=np.float64
                ).reshape(-1).tolist(),
            ),
        )
        exact_guard(model, context="nonlinear static checkpoint output")
    return NonlinearStaticResult(
        steps,
        status,
        u_final,
        float(lam),
        committed_states,
        info,
        tuple(snapshots),
        restart_payload,
    )


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
    convergence_settings: Optional[
        Union[str, Mapping[str, Any], NonlinearConvergenceSettings]
    ] = None,
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
    restart_checkpoint: Optional[Any] = None,
    emit_restart_checkpoint: bool = False,
) -> NonlinearStaticResult:
    """Run nonlinear static analysis under one non-renewable family lease."""

    exact_guard = _EXACT_QUALIFIED_LIFECYCLE_GUARD
    run_under_lease = _run_with_qualified_assembly_runtime_lease
    own_resource_config = _owned_resource_config_snapshot
    solve_under_lease = _solve_static_nonlinear_under_lease
    exact_guard(
        model,
        context="solve_static_nonlinear preflight",
    )

    def operation(lease: Any) -> NonlinearStaticResult:
        def post_observation() -> None:
            exact_guard(
                model,
                context="solve_static_nonlinear resource configuration",
            )
            lease(
                model,
                context="solve_static_nonlinear resource configuration",
            )

        owned_resource_config = own_resource_config(
            resource_config,
            post_observation=post_observation,
        )

        return solve_under_lease(
            model,
            load_case=load_case,
            constant_load_case=constant_load_case,
            max_load_factor=max_load_factor,
            num_steps=num_steps,
            max_iterations=max_iterations,
            tolerance=tolerance,
            num_layers=num_layers,
            min_step_fraction=min_step_fraction,
            imperfection=imperfection,
            load_program=load_program,
            control=control,
            displacement_control=displacement_control,
            initial_element_states=initial_element_states,
            convergence_settings=convergence_settings,
            resource_config=owned_resource_config,
            fracture_config=fracture_config,
            kinematics=kinematics,
            corotational_tangent=corotational_tangent,
            status_callback=status_callback,
            progress_callback=progress_callback,
            initial_fields=initial_fields,
            initial_displacements=initial_displacements,
            equilibrate_initial_state=equilibrate_initial_state,
            cancellation_token=cancellation_token,
            record_increment_snapshots=record_increment_snapshots,
            restart_checkpoint=restart_checkpoint,
            emit_restart_checkpoint=emit_restart_checkpoint,
            _qualified_runtime_guard=lease,
        )

    return run_under_lease(
        model,
        context="solve_static_nonlinear",
        operation=operation,
    )
