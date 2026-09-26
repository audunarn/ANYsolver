"""Development owner for a coupled, prescribed shell-contact trajectory.

The path keeps several prescribed coordinates in one nonlinear transaction.
Their conjugate forces are unknowns, so an opened patch has no unsupported
rigid translation. This owner admits restricted planar and bounded general
S3 patch static profiles; its checkpoint binds the complete path definition.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass

import numpy as np
from scipy import sparse

from anysolver.assembly import build_constraint_transformation
from anysolver.control import CancellationToken, SolveCancelled, cancellation_safe_point
from anysolver.linalg import MatrixClass, factorize
from anysolver.matrix_assembly import (
    _run_with_qualified_assembly_runtime_lease,
    assemble_stiffness_matrix,
)
from anysolver.nonlinear_restart import (
    create_nonlinear_checkpoint,
    validate_nonlinear_checkpoint,
)
from anysolver.nonlinear_state import _run_with_nonlinear_state_cleanup
from anysolver.nonlinear_static import (
    NonlinearStaticResult,
    NonlinearStaticStep,
    _activate_nonlinear_state_storage,
    _assemble_nonlinear_system,
    _commit_nonlinear_state_candidate,
    _discard_nonlinear_state_candidate,
    _finalize_nonlinear_element_states,
    _materialize_final_nonlinear_states,
    _max_plastic_strain,
    _prepare_initial_states,
    _prepare_qualified_q4_states_for_nonlinear_solve,
    _seal_final_qualified_q4_states,
    _static_step_from_restart,
    _support_reaction_resultants,
)

from .core import (
    ContactDefinition,
    ContactSolverSettings,
    contact_scope,
    validate_general_contact,
)
from .augmentation import ProjectedAugmentationSecant
from .linearized_pivot import refined_patch_pivot, refined_patch_supported_schur
from .equilibrated_pressure_pivot import equilibrated_pressure_pivot


PROFILE = "PLANAR_Q4_S3_MULTI_CONTROL_CONTACT_PATH_DEV_V0"
AUGMENTED_PROFILE = "PLANAR_Q4_S3_MULTI_CONTROL_AUGMENTED_PATH_DEV_V0"
GENERAL_S3_PATCH_PROFILE = "S3_PATCH_GENERAL_NODAL_MULTI_CONTROL_PENALTY_PATH_DEV_V0"
GENERAL_S3_PATCH_AUGMENTED_PROFILE = "S3_PATCH_GENERAL_AUGMENTED_PATH_DEV_V1"
GENERAL_S3_Q4_PATCH_AUGMENTED_PROFILE = "S3_Q4_PATCH_GENERAL_AUGMENTED_PATH_DEV_V1"
GENERAL_Q4_S3_PATCH_AUGMENTED_PROFILE = "Q4_S3_PATCH_GENERAL_AUGMENTED_PATH_DEV_V1"
GENERAL_Q4_S3_PATCH_PROJECTED_AUGMENTED_PROFILE = "Q4_S3_PATCH_GENERAL_AUGMENTED_PATH_DEV_V2"
GENERAL_Q4_Q4_PATCH_AUGMENTED_PROFILE = "Q4_Q4_PATCH_GENERAL_AUGMENTED_PATH_DEV_V1"
GENERAL_Q4_Q4_PATCH_PROJECTED_AUGMENTED_PROFILE = "Q4_Q4_PATCH_GENERAL_AUGMENTED_PATH_DEV_V2"
GENERAL_S3_PATCH_REFINED_AUGMENTED_PROFILE = "S3_PATCH_REFINED_AUGMENTED_PATH_DEV_V1"
GENERAL_Q4_S3_PATCH_REFINED_AUGMENTED_PROFILE = "Q4_S3_PATCH_REFINED_AUGMENTED_PATH_DEV_V1"
GENERAL_Q4_S3_PATCH_REFINED_ROUNDOFF_AUGMENTED_PROFILE = "Q4_S3_PATCH_REFINED_ROUNDOFF_AUGMENTED_PATH_DEV_V2"
GENERAL_Q4_S3_PATCH_REFINED_GRAPH_AUGMENTED_PROFILE = "Q4_S3_PATCH_REFINED_FIXED_PROJECTION_GRAPH_AUGMENTED_PATH_DEV_V0"
GENERAL_S3_Q4_PATCH_PROFILE = "S3_Q4_PATCH_GENERAL_NODAL_MULTI_CONTROL_PENALTY_PATH_DEV_V0"
GENERAL_Q4_S3_PATCH_PROFILE = "Q4_S3_PATCH_GENERAL_NODAL_MULTI_CONTROL_PENALTY_PATH_DEV_V0"
GENERAL_Q4_Q4_PROFILE = "Q4_Q4_GENERAL_NODAL_MULTI_CONTROL_PENALTY_PATH_DEV_V0"
_DOF = {"ux": 0, "uy": 1, "uz": 2}


def _reported_lower_gap(certificate) -> float:
    """Read the physical gap certificate from either admitted path manager."""
    if hasattr(certificate, "minimum_gap"):
        return float(certificate.minimum_gap)
    return float(certificate.conservative_lower_gap)


@dataclass(frozen=True)
class ContactPathControl:
    terms: tuple[tuple[int, str, float], ...]

    def __post_init__(self) -> None:
        terms = tuple(self.terms)
        if not terms or any(
            type(term) is not tuple or len(term) != 3
            or type(term[0]) is not int or term[0] <= 0
            or term[1] not in _DOF
            or not np.isfinite(term[2])
            for term in terms
        ):
            raise ValueError("contact path terms need positive nodes, translation DOFs and finite weights")
        if len({(node, dof) for node, dof, _weight in terms}) != len(terms):
            raise ValueError("contact path control terms must be unique")
        if all(weight == 0.0 for _node, _dof, weight in terms):
            raise ValueError("contact path control cannot be zero")
        object.__setattr__(self, "terms", tuple(
            (node, dof, float(weight)) for node, dof, weight in terms
        ))

    @classmethod
    def node(cls, node_id: int, dof: str) -> ContactPathControl:
        return cls(((node_id, dof, 1.0),))


@dataclass(frozen=True)
class ContactPathNodalForce:
    """One nodal translation-force history in N at the path waypoints."""

    node_id: int
    dof: str
    values_n: tuple[float, ...]

    def __post_init__(self) -> None:
        if type(self.node_id) is not int or self.node_id <= 0 or self.dof not in _DOF:
            raise ValueError("path force needs a positive node and translation DOF")
        values = tuple(float(value) for value in self.values_n)
        if not values or not np.all(np.isfinite(values)):
            raise ValueError("path force values must be finite and nonempty")
        object.__setattr__(self, "values_n", values)


@dataclass(frozen=True)
class ContactPathProgram:
    controls: tuple[ContactPathControl, ...]
    waypoints: tuple[tuple[float, ...], ...]
    steps_per_segment: int = 2
    nodal_forces: tuple[ContactPathNodalForce, ...] = ()

    def __post_init__(self) -> None:
        controls = tuple(self.controls)
        if not 2 <= len(controls) <= 3 or any(
            type(item) is not ContactPathControl for item in controls
        ) or len({item.terms for item in controls}) != len(controls):
            raise ValueError("contact path requires two or three distinct controls")
        points = tuple(tuple(float(value) for value in row)
                       for row in self.waypoints)
        if len(points) < 2 or any(len(row) != len(controls) for row in points):
            raise ValueError("contact path waypoints must match the control count")
        if any(not np.all(np.isfinite(row)) for row in points):
            raise ValueError("contact path waypoints must be finite")
        if any(value != 0.0 for value in points[0]):
            raise ValueError("contact path must start at the reference pose")
        forces = tuple(self.nodal_forces)
        if any(type(item) is not ContactPathNodalForce for item in forces):
            raise TypeError("nodal_forces must contain ContactPathNodalForce")
        if len({(item.node_id, item.dof) for item in forces}) != len(forces):
            raise ValueError("contact path nodal forces must have unique DOFs")
        if any(len(item.values_n) != len(points) or item.values_n[0] != 0.0
               for item in forces):
            raise ValueError("path force values must match waypoints and start at zero")
        if any(points[index] == points[index - 1]
               and all(item.values_n[index] == item.values_n[index - 1]
                       for item in forces)
               for index in range(1, len(points))):
            raise ValueError("contact path cannot contain a zero-change segment")
        if type(self.steps_per_segment) is not int or self.steps_per_segment < 1:
            raise ValueError("steps_per_segment must be a positive integer")
        if (len(points) - 1) * self.steps_per_segment > 10_000:
            raise MemoryError("contact path exceeds 10000 accepted-step slots")
        object.__setattr__(self, "controls", controls)
        object.__setattr__(self, "waypoints", points)
        object.__setattr__(self, "nodal_forces", forces)

    @property
    def total_steps(self) -> int:
        return (len(self.waypoints) - 1) * self.steps_per_segment

    def target_at(self, accepted_step: int) -> np.ndarray:
        step = int(accepted_step)
        if not 0 <= step <= self.total_steps:
            raise ValueError("contact path step lies outside the program")
        if step == self.total_steps:
            return np.asarray(self.waypoints[-1], dtype=float)
        segment, local = divmod(step, self.steps_per_segment)
        fraction = local / self.steps_per_segment
        return ((1.0 - fraction) * np.asarray(self.waypoints[segment])
                + fraction * np.asarray(self.waypoints[segment + 1]))

    def force_values_at(self, accepted_step: int) -> np.ndarray:
        step = int(accepted_step)
        if not 0 <= step <= self.total_steps:
            raise ValueError("contact path step lies outside the program")
        if not self.nodal_forces:
            return np.zeros(0)
        if step == self.total_steps:
            return np.asarray([item.values_n[-1] for item in self.nodal_forces])
        segment, local = divmod(step, self.steps_per_segment)
        fraction = local / self.steps_per_segment
        return np.asarray([
            (1.0-fraction)*item.values_n[segment]
            + fraction*item.values_n[segment+1]
            for item in self.nodal_forces
        ])

    def contract(self) -> dict[str, object]:
        result = {
            "controls": [{"terms": [list(term) for term in item.terms]}
                         for item in self.controls],
            "waypoints": [list(row) for row in self.waypoints],
            "steps_per_segment": self.steps_per_segment,
        }
        if self.nodal_forces:
            result["nodal_forces"] = [
                {"node_id": item.node_id, "dof": item.dof,
                 "values_n": list(item.values_n)}
                for item in self.nodal_forces
            ]
        return result


def solve_static_contact_path(
        model, definition: ContactDefinition, settings: ContactSolverSettings,
        program: ContactPathProgram, *, max_path_fraction: float = 1.0,
        max_iterations: int = 18, tolerance: float = 1.0e-7,
        num_layers: int = 5, restart_checkpoint=None,
        emit_restart_checkpoint: bool = False,
        cancellation_token: CancellationToken | None = None,
        ) -> NonlinearStaticResult:
    """Solve one multi-control path under an admitted static contact profile."""

    if type(definition) is not ContactDefinition or type(settings) is not ContactSolverSettings:
        raise TypeError("contact path needs exact contact definitions and settings")
    if type(program) is not ContactPathProgram:
        raise TypeError("contact path needs ContactPathProgram")
    report = validate_general_contact(model, definition, settings)
    if not report.valid:
        raise ValueError("unsupported contact path: " + "; ".join(report.issues))
    from .s3_patch_static import MIXED_PROFILE as mixed_patch_profile
    from .s3_patch_static import PROFILE as s3_patch_profile
    from .s3_patch_static import SOURCE_Q4_PROFILE as source_q4_patch_profile
    from .s3_patch_static import Q4_PAIR_PROFILE as q4_pair_profile
    from .s3_patch_static import AUGMENTED_PROFILE as general_augmented_profile
    from .s3_patch_static import AUGMENTED_MIXED_PROFILE as mixed_augmented_profile
    from .s3_patch_static import SOURCE_Q4_AUGMENTED_PROFILE as source_q4_augmented_profile
    from .s3_patch_static import SOURCE_Q4_PROJECTED_AUGMENTED_PROFILE as source_q4_projected_augmented_profile
    from .s3_patch_static import Q4_PAIR_AUGMENTED_PROFILE as q4_pair_augmented_profile
    from .s3_patch_static import Q4_PAIR_PROJECTED_AUGMENTED_PROFILE as q4_pair_projected_augmented_profile
    from .s3_patch_static import REFINED_AUGMENTED_PROFILE as refined_augmented_profile
    from .s3_patch_static import REFINED_Q4_S3_AUGMENTED_PROFILE as refined_q4_s3_augmented_profile
    from .s3_patch_static import REFINED_Q4_S3_ROUNDOFF_AUGMENTED_PROFILE as refined_q4_s3_roundoff_profile
    from .s3_patch_static import REFINED_Q4_S3_GRAPH_AUGMENTED_PROFILE as refined_q4_s3_graph_profile
    from .s3_patch_static import SupportResetForceBudgetExceeded

    general_s3_patch = report.profile in {
        s3_patch_profile, mixed_patch_profile, source_q4_patch_profile,
        q4_pair_profile, general_augmented_profile, mixed_augmented_profile,
        refined_augmented_profile, refined_q4_s3_augmented_profile,
        refined_q4_s3_roundoff_profile, refined_q4_s3_graph_profile,
        source_q4_augmented_profile,
        source_q4_projected_augmented_profile,
        q4_pair_augmented_profile, q4_pair_projected_augmented_profile,
    }
    if not general_s3_patch and "RESTRICTED_SLIDING" not in report.profile:
        raise ValueError("unsupported contact path profile: " + report.profile)
    if (definition.rigid_bodies or
            settings.pair_motion != ("general" if general_s3_patch
                                    else "restricted_sliding")):
        raise ValueError("contact path currently requires a deformable shell pair")
    augmented = definition.interactions[0].normal_law == "augmented"
    if settings.augmentation_acceleration != "none" and not augmented:
        raise ValueError("augmentation acceleration requires augmented contact")
    if (settings.augmentation_acceleration == "active_secant_pivot"
            and report.profile not in {
                refined_q4_s3_augmented_profile, refined_q4_s3_roundoff_profile,
            }):
        raise ValueError("active-set pivot requires the refined Q4/S3 augmented patch profile")
    if (settings.augmentation_acceleration == "supported_schur_dev"
            and report.profile != refined_q4_s3_augmented_profile):
        raise ValueError("supported Schur route requires the refined Q4/S3 augmented patch profile")
    profile = (GENERAL_Q4_Q4_PROFILE
               if report.profile == q4_pair_profile else
               GENERAL_Q4_S3_PATCH_PROFILE
               if report.profile == source_q4_patch_profile else
               GENERAL_S3_Q4_PATCH_PROFILE
               if report.profile == mixed_patch_profile else
               GENERAL_S3_Q4_PATCH_AUGMENTED_PROFILE
               if report.profile == mixed_augmented_profile else
               GENERAL_Q4_S3_PATCH_AUGMENTED_PROFILE
               if report.profile == source_q4_augmented_profile else
               GENERAL_Q4_S3_PATCH_PROJECTED_AUGMENTED_PROFILE
               if report.profile == source_q4_projected_augmented_profile else
               GENERAL_Q4_Q4_PATCH_AUGMENTED_PROFILE
               if report.profile == q4_pair_augmented_profile else
               GENERAL_Q4_Q4_PATCH_PROJECTED_AUGMENTED_PROFILE
               if report.profile == q4_pair_projected_augmented_profile else
               GENERAL_S3_PATCH_REFINED_AUGMENTED_PROFILE
               if report.profile == refined_augmented_profile else
               GENERAL_Q4_S3_PATCH_REFINED_AUGMENTED_PROFILE
               if report.profile == refined_q4_s3_augmented_profile else
               GENERAL_Q4_S3_PATCH_REFINED_ROUNDOFF_AUGMENTED_PROFILE
               if report.profile == refined_q4_s3_roundoff_profile else
               GENERAL_Q4_S3_PATCH_REFINED_GRAPH_AUGMENTED_PROFILE
               if report.profile == refined_q4_s3_graph_profile else
               GENERAL_S3_PATCH_AUGMENTED_PROFILE
               if report.profile == general_augmented_profile else
               GENERAL_S3_PATCH_PROFILE if general_s3_patch else
               AUGMENTED_PROFILE if augmented else PROFILE)
    from anymaterial.isotropic import IsotropicMaterial

    for element in model.mesh.elements.values():
        material = model.get_material(element.material_name)
        if type(material) is not IsotropicMaterial or material.hardening_curve is not None:
            raise ValueError("contact path currently admits elastic isotropic materials only")
    fraction = float(max_path_fraction)
    if not np.isfinite(fraction) or not 0.0 < fraction <= 1.0:
        raise ValueError("max_path_fraction must lie in (0, 1]")
    requested_step = round(fraction * program.total_steps)
    if (requested_step < 1 or
            abs(requested_step / program.total_steps - fraction) > 1.0e-12):
        raise ValueError("max_path_fraction must end at a registered path step")
    if type(max_iterations) is not int or max_iterations < 1:
        raise ValueError("max_iterations must be a positive integer")
    if type(num_layers) is not int or num_layers < 1:
        raise ValueError("num_layers must be a positive integer")
    if not np.isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("tolerance must be finite and positive")

    def operation(_lease):
        def run():
            with contact_scope(model, definition, settings,
                               allow_augmented=augmented) as manager:
                contract = {
                    "schema": "ANYSOLVER_STATIC_RESTART_CONTRACT_V2",
                    "control": "contact_path",
                    "profile": profile,
                    "general_contact": manager.restart_contract(),
                    "program": program.contract(),
                    "num_layers": num_layers,
                    "max_iterations": max_iterations,
                    "tolerance": float(tolerance),
                }
                if settings.augmentation_acceleration != "none":
                    contract["augmentation_acceleration"] = settings.augmentation_acceleration
                validated = None
                if restart_checkpoint is not None:
                    validated = validate_nonlinear_checkpoint(
                        restart_checkpoint, analysis_kind="static", model=model,
                        analysis_contract=contract, num_layers=num_layers,
                    )
                model.apply_boundary_conditions()
                stiffness, _stiffness_info = assemble_stiffness_matrix(model)
                zeros = np.zeros(model.mesh.dof_manager.total_dofs)
                _, _, T, u0, _independent, _constraint_info = (
                    build_constraint_transformation(stiffness, zeros, model)
                )
                if hasattr(manager, "restrict_tangent_to_reduced_variations"):
                    manager.restrict_tangent_to_reduced_variations(T)
                controls = np.zeros((len(program.controls), len(zeros)))
                for index, control in enumerate(program.controls):
                    for node_id, dof_name, weight in control.terms:
                        if model.mesh.get_node(node_id) is None:
                            raise ValueError(f"missing contact path node {node_id}")
                        dof = model.mesh.dof_manager.get_node_dofs(node_id)[
                            _DOF[dof_name]
                        ]
                        controls[index, dof] += weight
                rows = np.asarray(controls @ T, dtype=float)
                if np.linalg.matrix_rank(rows) != len(program.controls):
                    raise ValueError("contact path controls are constrained or dependent")
                if np.any(np.abs(controls @ u0) > 1.0e-12):
                    raise ValueError("contact path requires zero reference control offsets")
                reactions = rows.T
                force_dofs = np.empty(len(program.nodal_forces), dtype=np.intp)
                for index, force in enumerate(program.nodal_forces):
                    if model.mesh.get_node(force.node_id) is None:
                        raise ValueError(f"missing contact path force node {force.node_id}")
                    dof = model.mesh.dof_manager.get_node_dofs(force.node_id)[
                        _DOF[force.dof]
                    ]
                    force_dofs[index] = dof
                info = {"control": "contact_path", "profile": profile,
                        "general_contact_profile": manager.profile}
                accepted_step = 0
                multipliers = np.zeros(len(program.controls))
                previous_steps: list[NonlinearStaticStep] = []
                history: list[dict[str, object]] = []
                total_iterations = 0
                if restart_checkpoint is None:
                    q = np.zeros(T.shape[1])
                    committed_states, _ = _prepare_initial_states(
                        model, None, None, num_layers,
                    )
                else:
                    assert validated is not None
                    state = validated.path_state
                    expected_keys = {"mode", "accepted_step", "multipliers",
                                     "reduced_coordinates", "steps", "history",
                                     "total_iterations", "terminal_status"}
                    if augmented:
                        expected_keys.add("normal_multipliers")
                    if set(state) != expected_keys or state["mode"] != "contact_path":
                        raise ValueError("contact path checkpoint state is incompatible")
                    if state["terminal_status"] != "completed":
                        raise ValueError("contact path checkpoint is not continuable")
                    accepted_step = int(state["accepted_step"])
                    if not 0 <= accepted_step <= program.total_steps:
                        raise ValueError("contact path checkpoint step is invalid")
                    q = np.asarray(state["reduced_coordinates"], dtype=float)
                    multipliers = np.asarray(state["multipliers"], dtype=float)
                    if (q.shape != (T.shape[1],) or
                            multipliers.shape != (len(program.controls),) or
                            not np.all(np.isfinite(q)) or
                            not np.all(np.isfinite(multipliers))):
                        raise ValueError("contact path checkpoint coordinates are invalid")
                    if not np.array_equal(
                        np.asarray(T @ q + u0).reshape(-1),
                        validated.displacements,
                    ):
                        raise ValueError("contact path checkpoint pose is incompatible")
                    if not np.allclose(rows @ q, program.target_at(accepted_step),
                                       rtol=0.0, atol=1.0e-10):
                        raise ValueError("contact path checkpoint target is incompatible")
                    previous_steps = [_static_step_from_restart(item)
                                      for item in state["steps"]]
                    history = copy.deepcopy(state["history"])
                    total_iterations = int(state["total_iterations"])
                    if (len(previous_steps) != accepted_step or
                             len(history) != accepted_step or total_iterations < 0):
                        raise ValueError("contact path checkpoint history is incomplete")
                    if augmented:
                        manager.set_normal_multipliers(
                            np.asarray(state["normal_multipliers"], dtype=float)
                        )
                    committed_states = validated.element_states
                if accepted_step > requested_step:
                    raise ValueError("contact path checkpoint is beyond requested target")
                initial_u = np.asarray(T @ q + u0).reshape(-1)
                committed_states = _prepare_qualified_q4_states_for_nonlinear_solve(
                    model, initial_u, committed_states, num_layers, info,
                    supplied_element_ids=tuple(sorted(int(k) for k in committed_states)),
                    ordinary_restart=restart_checkpoint is not None,
                )
                committed_states = _activate_nonlinear_state_storage(
                    model, committed_states, num_layers, info,
                    kinematics="von_karman", committed_displacements=initial_u,
                )
                status = "completed"
                failure_reason = None
                scale = max(1.0e-9, max(abs(value) for row in program.waypoints
                                        for value in row))
                for step in range(accepted_step + 1, requested_step + 1):
                    cancellation_safe_point(cancellation_token,
                                            f"contact_path.step:{step}")
                    start_q = q.copy()
                    start_multipliers = multipliers.copy()
                    start_normal_multipliers = manager.normal_multipliers.copy() if augmented else None
                    target = program.target_at(step)
                    force_values = program.force_values_at(step)
                    external = np.zeros_like(zeros)
                    external[force_dofs] = force_values
                    reduced_external = np.asarray(T.T @ external).reshape(-1)
                    candidate_states = committed_states
                    normal_multiplier_change = 0.0
                    accelerator = (ProjectedAugmentationSecant()
                                   if settings.augmentation_acceleration in {
                                       "active_secant", "active_secant_pivot",
                                   }
                                   else None)
                    pivot_attempts = 0
                    pivot_applied = 0
                    pivot_rejected = 0
                    pressure_map_attempts = 0
                    pivot_backup = None
                    support_resets: list[dict[str, object]] = []
                    augmentation_trace: list[dict[str, object]] = []
                    certificate = None
                    residual_norm = float("inf")
                    constraint_norm = float("inf")
                    iteration = 0
                    augmentation_limit = (settings.maximum_augmentations
                                          if augmented else 1)
                    for augmentation in range(1, augmentation_limit + 1):
                        cancellation_safe_point(
                            cancellation_token,
                            f"contact_path.step:{step}.augmentation:{augmentation}",
                        )
                        equilibrated = False
                        for iteration in range(1, max_iterations + 1):
                            cancellation_safe_point(
                                cancellation_token,
                                f"contact_path.step:{step}.augmentation:{augmentation}.iteration:{iteration}",
                            )
                            total_iterations += 1
                            u = np.asarray(T @ q + u0).reshape(-1)
                            internal, tangent, trial = _assemble_nonlinear_system(
                                model, u, committed_states, num_layers,
                                kinematics="von_karman",
                            )
                            residual = (reduced_external + reactions @ multipliers
                                        - np.asarray(T.T @ internal).reshape(-1))
                            constraint = target - rows @ q
                            residual_norm = float(np.linalg.norm(residual))
                            constraint_norm = float(np.max(np.abs(constraint)))
                            force_scale = max(1.0, float(np.linalg.norm(
                                reduced_external + reactions @ multipliers)))
                            if (residual_norm <= tolerance * force_scale and
                                    constraint_norm <= tolerance * scale):
                                certificate = manager.evaluate(u, tangent=False)[2]
                                candidate_states = trial
                                equilibrated = True
                                break
                            reduced_tangent = (T.T @ tangent @ T).tocsr()
                            matrix = sparse.bmat([
                                [reduced_tangent, sparse.csr_matrix(-reactions)],
                                [sparse.csr_matrix(rows),
                                 sparse.csr_matrix((len(rows), len(rows)))],
                            ], format="csr")
                            rhs = np.r_[residual, constraint]
                            try:
                                delta = np.asarray(factorize(
                                    matrix, MatrixClass.GENERAL,
                                    signature=f"contact_path:{step}:{augmentation}:{iteration}",
                                ).solve(rhs)).reshape(-1)
                            except Exception:
                                failure_reason = "singular_contact_path_tangent"
                                break
                            if not np.all(np.isfinite(delta)):
                                failure_reason = "nonfinite_contact_path_increment"
                                break
                            proposed = np.asarray(T @ (q + delta[:len(q)]) + u0).reshape(-1)
                            fraction = manager.admissible_step_fraction(u, proposed)
                            if fraction <= 1.0e-12:
                                failure_reason = "contact_gap_exceeded"
                                break
                            q += fraction * delta[:len(q)]
                            multipliers += fraction * delta[len(q):]
                        if failure_reason is not None:
                            if pivot_backup is not None:
                                q, multipliers, fallback_pressure, _prior_change, _retained = pivot_backup
                                manager.set_normal_multipliers(fallback_pressure)
                                pivot_backup = None
                                pivot_rejected += 1
                                augmentation_trace.append({
                                    ("schur_rejected" if settings.augmentation_acceleration
                                     == "supported_schur_dev" else "pivot_rejected"): failure_reason,
                                    "augmentation": augmentation,
                                })
                                failure_reason = None
                                accelerator = (ProjectedAugmentationSecant()
                                               if settings.augmentation_acceleration == "active_secant_pivot"
                                               else None)
                                continue
                            break
                        if not equilibrated:
                            if pivot_backup is not None:
                                q, multipliers, fallback_pressure, _prior_change, _retained = pivot_backup
                                manager.set_normal_multipliers(fallback_pressure)
                                pivot_backup = None
                                pivot_rejected += 1
                                augmentation_trace.append({
                                    ("schur_rejected" if settings.augmentation_acceleration
                                     == "supported_schur_dev" else "pivot_rejected"):
                                    "maximum_iterations_reached",
                                    "augmentation": augmentation,
                                })
                                accelerator = (ProjectedAugmentationSecant()
                                               if settings.augmentation_acceleration == "active_secant_pivot"
                                               else None)
                                continue
                            failure_reason = "maximum_iterations_reached"
                            break
                        if augmented:
                            if settings.augmentation_support_resolution == "roundoff":
                                try:
                                    projected = manager.projected_normal_multipliers(u)
                                except SupportResetForceBudgetExceeded as exc:
                                    failure_reason = "contact_multiplier_reset_force_budget_exceeded"
                                    augmentation_trace.append({
                                        "augmentation": augmentation,
                                        "support_reset_failure": str(exc),
                                    })
                                    break
                            else:
                                projected = manager.projected_normal_multipliers(u)
                            normal_multiplier_change = float(np.max(np.abs(
                                projected - manager.normal_multipliers
                            )))
                            verified_schur = False
                            if pivot_backup is not None:
                                (fallback_q, fallback_controls, fallback_pressure,
                                 prior_change, retained) = pivot_backup
                                pivot_backup = None
                                actual_active = tuple(np.flatnonzero(
                                    np.asarray(certificate.numerical_pressure_pa) > 0.0,
                                ))
                                active_changed = (
                                    actual_active != retained if isinstance(retained, tuple)
                                    else certificate.active_pressure_dofs > retained
                                )
                                if (not certificate.gap_tolerance_met
                                        or active_changed
                                        or normal_multiplier_change >= 0.75*prior_change):
                                    q = fallback_q
                                    multipliers = fallback_controls
                                    manager.set_normal_multipliers(fallback_pressure)
                                    pivot_rejected += 1
                                    augmentation_trace.append({
                                        ("schur_rejected" if settings.augmentation_acceleration
                                         == "supported_schur_dev" else "pivot_rejected"):
                                        "nonlinear_verification",
                                        "augmentation": augmentation,
                                        "pressure_change": normal_multiplier_change,
                                        "minimum_gap": _reported_lower_gap(certificate),
                                    })
                                    accelerator = (ProjectedAugmentationSecant()
                                                   if settings.augmentation_acceleration == "active_secant_pivot"
                                                   else None)
                                    continue
                                pivot_applied += 1
                                verified_schur = (settings.augmentation_acceleration
                                                  == "supported_schur_dev")
                                accelerator = (ProjectedAugmentationSecant()
                                               if settings.augmentation_acceleration == "active_secant_pivot"
                                               else None)
                            augmentation_trace.append({
                                **({"schur_verified": True} if verified_schur else {}),
                                "pressure_change": normal_multiplier_change,
                                "minimum_gap": _reported_lower_gap(certificate),
                                "residual_norm": residual_norm,
                                "active_pressure_dofs": certificate.active_pressure_dofs,
                                "source_contact_force_n": (
                                    None if not hasattr(certificate, "integration_force")
                                    else list(certificate.integration_force)
                                ),
                                "sampled_overlap_gap_m": getattr(
                                    certificate, "sampled_overlap_gap", None,
                                ),
                                "pressure_rank": getattr(
                                    certificate, "pressure_rank", None,
                                ),
                                "pressure_gram_rank": getattr(
                                    certificate, "pressure_gram_rank", None,
                                ),
                                "pressure_gradient_condition": getattr(
                                    certificate, "pressure_gradient_condition", None,
                                ),
                                "pressure_gram_condition_estimate": getattr(
                                    certificate, "pressure_gram_condition_estimate", None,
                                ),
                                "pressure_gram_supported_modes": getattr(
                                    certificate, "pressure_gram_supported_modes", None,
                                ),
                                "pressure_gram_scaled_rank": getattr(
                                    certificate, "pressure_gram_scaled_rank", None,
                                ),
                                "pressure_gram_scaled_condition_estimate": getattr(
                                    certificate, "pressure_gram_scaled_condition_estimate", None,
                                ),
                                "minimum_weighted_gap_m": getattr(
                                    certificate, "minimum_weighted_gap_m", None,
                                ),
                                "normalized_weighted_gap_m": list(
                                    getattr(certificate, "normalized_weighted_gap_m", ())
                                ),
                                "normal_multiplier_estimate_pa": list(
                                    getattr(certificate, "normal_multiplier_estimate_pa", ())
                                ),
                                "source_pressure_node_ids": list(
                                    getattr(certificate, "source_pressure_node_ids", ())
                                ),
                            })
                            if (settings.augmentation_support_resolution == "roundoff"
                                    and manager.last_support_reset is not None):
                                reset = {"augmentation": augmentation,
                                         **manager.last_support_reset}
                                augmentation_trace[-1]["support_reset"] = reset
                                support_resets.append(reset)
                            if (hasattr(manager, "has_unresolved_weak_open_gap")
                                    and manager.has_unresolved_weak_open_gap(
                                        certificate, projected,
                                    )):
                                failure_reason = "contact_pressure_space_underresolved"
                                break
                            if (normal_multiplier_change <= settings.pressure_tolerance
                                    and certificate.gap_tolerance_met):
                                if (certificate.active_pressure_dofs == 0
                                        and not np.any(projected)):
                                    # A fully open state has no contact work at
                                    # either multiplier estimate. Store the
                                    # exact projected zero for restart and
                                    # report the certificate for that state.
                                    manager.set_normal_multipliers(projected)
                                    _force, _tangent, certificate = manager.evaluate(
                                        u, tangent=False,
                                    )
                                break
                            proposal = (None if accelerator is None else
                                        accelerator.propose(manager.normal_multipliers,
                                                            projected))
                            augmentation_trace[-1]["acceleration_applied"] = proposal is not None
                            if (proposal is None
                                    and settings.augmentation_acceleration == "supported_schur_dev"
                                    and pivot_attempts < settings.augmentation_schur_maximum_attempts
                                    and augmentation >= 2
                                    and augmentation <= augmentation_limit - 2
                                    and certificate.active_pressure_dofs > 0):
                                pivot_attempts += 1
                                try:
                                    schur = refined_patch_supported_schur(
                                        manager, u, tangent, T, rows,
                                        difference_step=settings.augmentation_schur_difference_step_m,
                                        maximum_pressure=settings.augmentation_schur_maximum_pressure_pa,
                                        maximum_pressure_step=settings.augmentation_schur_maximum_step_pa,
                                        maximum_modes=settings.augmentation_schur_maximum_modes,
                                        diagnostics=augmentation_trace[-1],
                                        check_cancel=lambda: cancellation_safe_point(
                                            cancellation_token,
                                            f"contact_path.step:{step}.augmentation:{augmentation}.schur",
                                        ),
                                    )
                                except SolveCancelled:
                                    raise
                                except (ValueError, MemoryError, np.linalg.LinAlgError) as exc:
                                    augmentation_trace[-1]["schur_ineligible"] = str(exc)
                                    schur = None
                                except Exception as exc:
                                    failure_reason = "contact_supported_schur_linearization_failed"
                                    augmentation_trace[-1]["schur_failure"] = str(exc)
                                    break
                                augmentation_trace[-1]["schur_proposed"] = schur is not None
                                if schur is not None:
                                    pivot_backup = (q.copy(), multipliers.copy(),
                                                    projected.copy(),
                                                    normal_multiplier_change,
                                                    schur.active_indices)
                                    augmentation_trace[-1]["schur_active_indices"] = list(
                                        schur.active_indices)
                                    augmentation_trace[-1]["schur_scaled_condition"] = (
                                        schur.scaled_condition)
                                    augmentation_trace[-1]["schur_predicted_residual_pa"] = (
                                        schur.predicted_residual_after)
                                    augmentation_trace[-1]["schur_predicted_residual_before_pa"] = (
                                        schur.predicted_residual_before)
                                    augmentation_trace[-1]["schur_step_fraction"] = (
                                        schur.step_fraction)
                                    manager.set_normal_multipliers(schur.multipliers)
                                    continue
                            if (proposal is None
                                    and settings.augmentation_acceleration == "active_secant_pivot"
                                    and pivot_attempts == 0
                                    and augmentation >= 10
                                    and augmentation <= augmentation_limit - 5
                                    and 2 <= certificate.active_pressure_dofs <= 4):
                                pivot_attempts = 1
                                try:
                                    pivot = refined_patch_pivot(
                                        manager, u, tangent, T, rows,
                                        difference_step=settings.augmentation_pivot_difference_step_m,
                                        maximum_pressure=settings.augmentation_pivot_max_pressure_pa,
                                        pressure_tolerance=settings.pressure_tolerance,
                                        check_cancel=lambda: cancellation_safe_point(
                                            cancellation_token,
                                            f"contact_path.step:{step}.augmentation:{augmentation}.pivot",
                                        ),
                                    )
                                except SolveCancelled:
                                    raise
                                except ValueError as exc:
                                    failure_reason = "contact_active_set_pivot_resource_or_geometry_failure"
                                    augmentation_trace[-1]["pivot_failure"] = str(exc)
                                    break
                                except Exception as exc:
                                    failure_reason = "contact_active_set_pivot_linearization_failed"
                                    augmentation_trace[-1]["pivot_failure"] = str(exc)
                                    break
                                augmentation_trace[-1]["pivot_proposed"] = pivot is not None
                                if pivot is not None:
                                    pivot_backup = (q.copy(), multipliers.copy(),
                                                    projected.copy(),
                                                    normal_multiplier_change,
                                                    len(pivot.retained_local_indices))
                                    augmentation_trace[-1]["pivot_retained_local_indices"] = list(
                                        pivot.retained_local_indices)
                                    augmentation_trace[-1]["pivot_schur_condition"] = pivot.schur_condition
                                    manager.set_normal_multipliers(pivot.multipliers)
                                    continue
                            if (proposal is None
                                    and settings.augmentation_equilibrated_pressure_step_pa is not None
                                    and pressure_map_attempts == 0
                                    and augmentation >= 10
                                    and augmentation <= augmentation_limit - 2
                                    and np.count_nonzero(projected > 0.0) == 2):
                                pressure_map_attempts = 1
                                try:
                                    mapped = equilibrated_pressure_pivot(
                                        manager, model, u, q, multipliers,
                                        committed_states, num_layers, T, u0,
                                        rows, reduced_external, target,
                                        pressure_step=(
                                            settings.augmentation_equilibrated_pressure_step_pa
                                        ),
                                        maximum_pressure=settings.augmentation_pivot_max_pressure_pa,
                                        max_iterations=max_iterations,
                                        tolerance=tolerance,
                                        check_cancel=lambda: cancellation_safe_point(
                                            cancellation_token,
                                            f"contact_path.step:{step}.augmentation:{augmentation}.pressure_map",
                                        ),
                                    )
                                except SolveCancelled:
                                    raise
                                except (ValueError, np.linalg.LinAlgError) as exc:
                                    augmentation_trace[-1]["pressure_map_failure"] = str(exc)
                                    mapped = None
                                augmentation_trace[-1]["pressure_map_proposed"] = mapped is not None
                                if mapped is not None:
                                    pivot_backup = (q.copy(), multipliers.copy(),
                                                    projected.copy(),
                                                    normal_multiplier_change,
                                                    len(mapped.retained_local_indices))
                                    augmentation_trace[-1]["pressure_map_condition"] = mapped.schur_condition
                                    manager.set_normal_multipliers(mapped.multipliers)
                                    continue
                            manager.set_normal_multipliers(
                                projected if proposal is None else proposal
                            )
                        elif certificate.gap_tolerance_met:
                            break
                        else:
                            failure_reason = "contact_gap_exceeded"
                            break
                    else:
                        failure_reason = "maximum_augmentations_reached"
                    if failure_reason is not None:
                        info["contact_failure"] = {
                            "step_index": step,
                            "augmentation_iterations": augmentation,
                            "newton_iterations_last_augmentation": iteration,
                            "residual_norm": residual_norm,
                            "constraint_norm": constraint_norm,
                            "normal_multiplier_change": normal_multiplier_change,
                            "augmentation_trace": augmentation_trace,
                            "augmentation_acceleration_attempts": (
                                0 if accelerator is None else accelerator.attempts
                            ),
                            "augmentation_acceleration_applied": (
                                0 if accelerator is None else accelerator.applied
                            ),
                            "pivot_attempts": pivot_attempts,
                            "pivot_applied": pivot_applied,
                            "pivot_rejected": pivot_rejected,
                            **({"schur_attempts": pivot_attempts,
                                "schur_applied": pivot_applied,
                                "schur_rejected": pivot_rejected}
                               if settings.augmentation_acceleration == "supported_schur_dev"
                               else {}),
                            "pressure_map_attempts": pressure_map_attempts,
                            "minimum_gap": (
                                None if certificate is None else
                                _reported_lower_gap(certificate)
                            ),
                            "sampled_overlap_gap": (
                                None if certificate is None else
                                getattr(certificate, "sampled_overlap_gap", None)
                            ),
                            "gap_tolerance_met": (
                                None if certificate is None else
                                certificate.gap_tolerance_met
                            ),
                            "active_pressure_dofs": (
                                None if certificate is None else
                                certificate.active_pressure_dofs
                            ),
                        }
                        _discard_nonlinear_state_candidate(committed_states)
                        q = start_q
                        multipliers = start_multipliers
                        if augmented:
                            manager.set_normal_multipliers(start_normal_multipliers)
                        status = "stopped_at_limit" if previous_steps else "diverged"
                        break
                    accepted_u = np.asarray(T @ q + u0).reshape(-1)
                    committed_states = _commit_nonlinear_state_candidate(
                        committed_states, candidate_states,
                        model=model, accepted_displacements=accepted_u,
                    )
                    recovered, _K, _states = _assemble_nonlinear_system(
                        model, accepted_u, committed_states, num_layers,
                        tangent=False, kinematics="von_karman",
                        require_full_coordinates=True,
                    )
                    _discard_nonlinear_state_candidate(committed_states)
                    support = _support_reaction_resultants(
                        model, recovered - controls.T @ multipliers - external,
                    )
                    accepted_step = step
                    record = {
                        "step_index": step,
                        "target": target.tolist(),
                        "reaction_generalized": multipliers.tolist(),
                        "residual_norm": residual_norm,
                        "constraint_error": constraint_norm,
                        "augmentation_iterations": augmentation,
                        "normal_multiplier_change": normal_multiplier_change,
                        "contact": certificate.to_dict(),
                    }
                    if settings.augmentation_support_resolution == "roundoff":
                        record["support_resets"] = support_resets
                    if accelerator is not None:
                        record["augmentation_acceleration"] = settings.augmentation_acceleration
                        record["augmentation_acceleration_attempts"] = accelerator.attempts
                        record["augmentation_acceleration_applied"] = accelerator.applied
                    if settings.augmentation_acceleration == "active_secant_pivot":
                        record["pivot_attempts"] = pivot_attempts
                        record["pivot_applied"] = pivot_applied
                        record["pivot_rejected"] = pivot_rejected
                        if settings.augmentation_equilibrated_pressure_step_pa is not None:
                            record["pressure_map_attempts"] = pressure_map_attempts
                    if settings.augmentation_acceleration == "supported_schur_dev":
                        record["augmentation_acceleration"] = "supported_schur_dev"
                        record["schur_attempts"] = pivot_attempts
                        record["schur_applied"] = pivot_applied
                        record["schur_rejected"] = pivot_rejected
                        record["augmentation_trace"] = augmentation_trace
                    if program.nodal_forces:
                        previous_force_values = program.force_values_at(step-1)
                        start_u = np.asarray(T @ start_q + u0).reshape(-1)
                        record["nodal_forces_n"] = force_values.tolist()
                        record["external_nodal_work_trapezoid_j"] = float(
                            0.5*(previous_force_values + force_values)
                            @ (accepted_u-start_u)[force_dofs]
                        )
                    history.append(record)
                    previous_steps.append(NonlinearStaticStep(
                        step_index=step,
                        load_factor=step / program.total_steps,
                        iterations=iteration,
                        residual_norm=residual_norm,
                        displacement_norm=float(np.linalg.norm(accepted_u)),
                        max_equivalent_plastic_strain=_max_plastic_strain(
                            committed_states
                        ),
                        active_stage=f"segment_{(step - 1) // program.steps_per_segment + 1}",
                        support_reactions=support,
                    ))
                final_u = np.asarray(T @ q + u0).reshape(-1)
                finished_states = _materialize_final_nonlinear_states(
                    committed_states, info,
                )
                if previous_steps:
                    finished_states = _finalize_nonlinear_element_states(
                        model, final_u, finished_states, num_layers,
                        kinematics="von_karman",
                    )
                    finished_states = _seal_final_qualified_q4_states(
                        model, final_u, finished_states, num_layers, info,
                        kinematics="von_karman",
                    )
                info.update({
                    "failure_reason": failure_reason,
                    "status_category": status,
                    "stop_reason": failure_reason,
                    "total_newton_iterations": total_iterations,
                    "force_displacement_history": history,
                    "contact_path": {
                        "accepted_step": accepted_step,
                        "total_steps": program.total_steps,
                        "targets": program.target_at(accepted_step).tolist(),
                        "reaction_generalized": multipliers.tolist(),
                        "profile": profile,
                        **({"augmentation_acceleration": settings.augmentation_acceleration}
                           if settings.augmentation_acceleration != "none" else {}),
                        **({"nodal_forces_n": program.force_values_at(
                            accepted_step,
                        ).tolist()} if program.nodal_forces else {}),
                    },
                    "general_contact": manager.evaluate(final_u, tangent=False)[2].to_dict(),
                })
                checkpoint = None
                if emit_restart_checkpoint and status == "completed":
                    checkpoint = create_nonlinear_checkpoint(
                        analysis_kind="static", model=model,
                        analysis_contract=contract, displacements=final_u,
                        element_states=finished_states,
                        path_state={
                            "mode": "contact_path",
                            "accepted_step": accepted_step,
                            "multipliers": multipliers.tolist(),
                            "reduced_coordinates": q.tolist(),
                            "steps": [item.to_dict() for item in previous_steps],
                            "history": history,
                            "total_iterations": total_iterations,
                            "terminal_status": status,
                            **({"normal_multipliers": manager.normal_multipliers.tolist()}
                               if augmented else {}),
                        },
                    )
                return NonlinearStaticResult(
                    previous_steps, status, final_u,
                    accepted_step / program.total_steps,
                    finished_states, info, restart_checkpoint=checkpoint,
                )

        return _run_with_nonlinear_state_cleanup(run)

    return _run_with_qualified_assembly_runtime_lease(
        model, context="solve_static_contact_path", operation=operation,
    )
