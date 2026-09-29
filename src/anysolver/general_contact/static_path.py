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
    _increment_snapshot,
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
    suspend_contact,
    validate_general_contact,
)
from .augmentation import ProjectedAugmentationSecant
from .linearized_pivot import (
    _projected_clip_signature,
    refined_patch_pivot,
    refined_patch_supported_schur,
)
from .supported_schur import (
    propose_supported_schur_backtrack,
    propose_supported_schur_secant_backtrack,
)
from .equilibrated_pressure_pivot import equilibrated_pressure_pivot
from .semismooth_path import solve_increment as solve_semismooth_increment
from .semismooth import raw_certificate


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
GENERAL_Q4_S3_PATCH_REFINED_PROJECTED_AUGMENTED_PROFILE = "Q4_S3_PATCH_REFINED_PROJECTED_AUGMENTED_PATH_DEV_V0"
GENERAL_Q4_S3_PATCH_REFINED_OVERLAP_LOCAL_AUGMENTED_PROFILE = "Q4_S3_PATCH_REFINED_OVERLAP_LOCAL_AUGMENTED_PATH_DEV_V0"
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
        if len(controls) not in {0, 1, 2, 3} or any(
            type(item) is not ContactPathControl for item in controls
        ) or len({item.terms for item in controls}) != len(controls):
            raise ValueError("contact path requires at most three distinct controls")
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


def _program_from_dead_nodal_load_case(load_case, num_steps: int) -> ContactPathProgram:
    """Own a narrow ordinary force load as a zero-control contact path."""
    from anysolver.boundary import LoadCase

    if type(load_case) is not LoadCase or type(num_steps) is not int or num_steps < 1:
        raise ValueError("monolithic ordinary force contact needs a LoadCase and positive num_steps")
    if any(type(value) is not dict for value in (
            load_case.nodal_loads, load_case.element_loads,
            load_case.pressure_loads, load_case.added_node_masses)):
        raise ValueError("monolithic ordinary force contact needs owned load mappings")
    if (load_case.element_loads or load_case.pressure_loads
            or load_case.gravity is not None or load_case.added_node_masses
            or load_case.follower_pressure or not load_case.nodal_loads):
        raise ValueError("monolithic ordinary force contact admits dead nodal loads only")
    forces = []
    if any(type(node_id) is not int or node_id <= 0
           for node_id in load_case.nodal_loads):
        raise ValueError("monolithic nodal load needs exact positive node IDs")
    for node_id, value in sorted(load_case.nodal_loads.items()):
        if type(value) is not np.ndarray or value.dtype.kind not in {"f", "i", "u"}:
            raise ValueError("monolithic nodal load needs primitive numeric arrays")
        vector = np.asarray(value, dtype=float)
        if (vector.shape != (6,) or not np.all(np.isfinite(vector))
                or np.any(vector[3:] != 0.0)):
            raise ValueError("monolithic ordinary force contact admits finite translation forces only")
        for component, dof in enumerate(("ux", "uy", "uz")):
            if vector[component] != 0.0:
                forces.append(ContactPathNodalForce(
                    node_id, dof, (0.0, float(vector[component])),
                ))
    if not forces:
        raise ValueError("monolithic ordinary force contact needs a nonzero nodal force")
    return ContactPathProgram(controls=(), waypoints=((), ()),
                              steps_per_segment=num_steps,
                              nodal_forces=tuple(forces))


def _program_from_simple_displacement_control(control, num_steps: int) -> ContactPathProgram:
    """Own one ordinary nodal translation displacement without applied loads."""
    from anysolver.nonlinear_static import DisplacementControl

    if (type(control) is not DisplacementControl
            or type(num_steps) is not int or num_steps < 1
            or type(control.node_id) is not int or control.node_id <= 0
            or type(control.dof) is not str or control.dof not in _DOF
            or control.weighted_dofs is not None
            or type(control.target_displacement) not in {int, float}
            or not np.isfinite(control.target_displacement)
            or control.target_displacement == 0.0):
        raise ValueError(
            "monolithic ordinary displacement contact needs one finite "
            "nonzero nodal translation target"
        )
    return ContactPathProgram(
        controls=(ContactPathControl.node(control.node_id, control.dof),),
        waypoints=((0.0,), (float(control.target_displacement),)),
        steps_per_segment=num_steps,
    )


def _elastic_displacement_force_predictor(stiffness, transform, row,
                                          target) -> float:
    """Bound a declared force scale by the contact-free control reactions.

    For several controls, use the maximum absolute reaction sum over path
    waypoints. This retains the one-control value and one physical force unit.
    """
    reduced = sparse.csr_matrix(transform.T @ stiffness @ transform)
    rows = np.asarray(row, dtype=float)
    if rows.ndim == 1:
        rows = rows[None, :]
    targets = np.asarray(target, dtype=float)
    if targets.ndim == 0:
        targets = targets.reshape(1, 1)
    elif targets.ndim == 1:
        targets = targets[None, :]
    controls, coordinates = rows.shape
    if (reduced.shape != (coordinates, coordinates)
            or not 1 <= controls <= 3
            or targets.ndim != 2 or targets.shape[1] != controls
            or not np.all(np.isfinite(targets))
            or not np.any(targets != 0.0)):
        raise ValueError("displacement force predictor has incompatible dimensions")
    saddle = sparse.bmat((
        (reduced, sparse.csr_matrix(-rows.T)),
        (sparse.csr_matrix(rows), sparse.csr_matrix((controls, controls))),
    ), format="csr")
    try:
        solve = factorize(
            saddle, MatrixClass.GENERAL,
            signature="contact_path:elastic_displacement_force_predictor",
        ).solve
    except Exception as exc:
        raise ValueError("contact-free displacement force predictor is unavailable") from exc
    maximum_reaction = 0.0
    for waypoint in targets:
        rhs = np.zeros(coordinates+controls)
        rhs[-controls:] = waypoint
        try:
            response = np.asarray(solve(rhs)).reshape(-1)
        except Exception as exc:
            raise ValueError("contact-free displacement force predictor is unavailable") from exc
        residual = np.asarray(saddle @ response - rhs).reshape(-1)
        scale = abs(saddle) @ abs(response) + abs(rhs)
        reactions = response[-controls:]
        if (not np.all(np.isfinite(response))
                or np.any(abs(residual) > 1e-12 + 1e-9*scale)
                or not np.all(np.isfinite(reactions))):
            raise ValueError("contact-free displacement force predictor is unresolved")
        maximum_reaction = max(maximum_reaction,
                               float(np.sum(np.abs(reactions))))
    if maximum_reaction <= 0.0:
        raise ValueError("contact-free displacement force predictor is unresolved")
    return maximum_reaction


def solve_static_contact_path(
        model, definition: ContactDefinition, settings: ContactSolverSettings,
        program: ContactPathProgram, *, max_path_fraction: float = 1.0,
        max_iterations: int = 18, tolerance: float = 1.0e-7,
        num_layers: int = 5, restart_checkpoint=None,
        emit_restart_checkpoint: bool = False,
        record_increment_snapshots: bool = False,
        cancellation_token: CancellationToken | None = None,
        ) -> NonlinearStaticResult:
    """Solve one multi-control path under an admitted static contact profile.

    Opt-in snapshots contain accepted increments produced by this invocation;
    a resumed call does not recreate the checkpoint's earlier poses.
    """

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
    from .s3_patch_static import REFINED_Q4_S3_PROJECTED_AUGMENTED_PROFILE as refined_q4_s3_projected_profile
    from .s3_patch_static import REFINED_Q4_S3_OVERLAP_LOCAL_AUGMENTED_PROFILE as refined_q4_s3_overlap_local_profile
    from .s3_patch_static import REFINED_Q4_S3_ROUNDOFF_AUGMENTED_PROFILE as refined_q4_s3_roundoff_profile
    from .s3_patch_static import REFINED_Q4_S3_GRAPH_AUGMENTED_PROFILE as refined_q4_s3_graph_profile
    from .s3_patch_static import SupportResetForceBudgetExceeded
    from .q4_s3_overlap_derivatives import UnsupportedQ4S3Branch

    general_s3_patch = report.profile in {
        s3_patch_profile, mixed_patch_profile, source_q4_patch_profile,
        q4_pair_profile, general_augmented_profile, mixed_augmented_profile,
        refined_augmented_profile, refined_q4_s3_augmented_profile,
        refined_q4_s3_projected_profile,
        refined_q4_s3_overlap_local_profile,
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
    semismooth = settings.enforcement_solver == "monolithic_active_set"
    displacement_only = bool(program.controls) and not program.nodal_forces
    if len(program.controls) < 2 and not semismooth:
        raise ValueError("zero/one-control contact path requires monolithic_active_set")
    if len(program.controls) == 1 and program.nodal_forces:
        raise ValueError("one-control mixed force/displacement path is not admitted")
    if displacement_only and len(program.controls) == 1:
        terms = program.controls[0].terms
        if (len(terms) != 1 or terms[0][2] != 1.0
                or len(program.waypoints) != 2
                or program.waypoints[1][0] == 0.0):
            raise ValueError(
                "one-control contact path requires one unit-weight nodal "
                "translation and one nonzero target waypoint"
            )
    if semismooth and (
            not augmented
            or report.profile not in {
                refined_q4_s3_augmented_profile,
                refined_q4_s3_projected_profile,
                refined_q4_s3_overlap_local_profile,
            }
            or settings.general_s3_differentiation != "jet2_q4_s3_dev"
            or settings.q4_source_pressure_basis != "fine_nodal_q1"
            or settings.augmentation_support_resolution != "exact"):
        raise ValueError("monolithic_active_set requires fine Q1 refined Q4/S3 Jet2 augmented contact")
    if semismooth:
        declared_force = max(
            (sum(abs(item.values_n[index]) for item in program.nodal_forces)
             for index in range(len(program.waypoints))),
            default=0.0,
        )
        if (not displacement_only and
                (declared_force <= 0.0
                 or settings.complementarity_force_scale_n
                 > declared_force*(1.0+1.0e-12))):
            raise ValueError(
                "monolithic_active_set force scale must be bounded by the "
                "declared maximum absolute path load; displacement-only "
                "paths need a separate physical force reference"
            )
    if settings.augmentation_acceleration != "none" and not augmented:
        raise ValueError("augmentation acceleration requires augmented contact")
    if (settings.augmentation_acceleration == "active_secant_pivot"
            and report.profile not in {
                refined_q4_s3_augmented_profile, refined_q4_s3_roundoff_profile,
            }):
        raise ValueError("active-set pivot requires the refined Q4/S3 augmented patch profile")
    if (settings.augmentation_acceleration == "supported_schur_dev"
            and report.profile not in {
                refined_q4_s3_augmented_profile, refined_q4_s3_projected_profile,
                refined_q4_s3_overlap_local_profile,
            }):
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
               GENERAL_Q4_S3_PATCH_REFINED_PROJECTED_AUGMENTED_PROFILE
               if report.profile == refined_q4_s3_projected_profile else
               GENERAL_Q4_S3_PATCH_REFINED_OVERLAP_LOCAL_AUGMENTED_PROFILE
               if report.profile == refined_q4_s3_overlap_local_profile else
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
    if type(record_increment_snapshots) is not bool:
        raise TypeError("record_increment_snapshots must be bool")
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
                if semismooth:
                    contract["enforcement_solver"] = "monolithic_active_set"
                    contract["control_residual_scaling"] = "per_control_waypoint_max_v1"
                if displacement_only:
                    contract["force_reference_method"] = (
                        "contact_free_elastic_displacement_v1"
                    )
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
                displacement_force_predictor = None
                if displacement_only:
                    displacement_force_predictor = (
                        _elastic_displacement_force_predictor(
                            stiffness, T, rows, program.waypoints[1:],
                        )
                    )
                    if (semismooth and settings.complementarity_force_scale_n
                            > displacement_force_predictor*(1.0+1.0e-12)):
                        raise ValueError(
                            "monolithic displacement force scale exceeds "
                            "the contact-free elastic reaction predictor "
                            f"(declared={settings.complementarity_force_scale_n:.9g} N, "
                            f"predictor={displacement_force_predictor:.9g} N)"
                        )
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
                if displacement_force_predictor is not None:
                    info["contact_free_elastic_force_predictor_n"] = (
                        displacement_force_predictor
                    )
                accepted_step = 0
                multipliers = np.zeros(len(program.controls))
                normal_forces = np.zeros(len(manager.law.pressure_mode_ids)) if semismooth else None
                previous_steps: list[NonlinearStaticStep] = []
                snapshots = []
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
                    if semismooth:
                        expected_keys.add("normal_forces")
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
                    if semismooth:
                        normal_forces = np.asarray(state["normal_forces"], dtype=float)
                        if (normal_forces.shape != (len(manager.law.pressure_mode_ids),)
                                or not np.all(np.isfinite(normal_forces))
                                or np.any(normal_forces < 0.0)):
                            raise ValueError("contact path checkpoint nodal forces are invalid")
                    committed_states = validated.element_states
                if accepted_step > requested_step:
                    raise ValueError("contact path checkpoint is beyond requested target")
                initial_u = np.asarray(T @ q + u0).reshape(-1)
                if semismooth and restart_checkpoint is not None:
                    source, target_points = manager._positions(initial_u)
                    support_area = manager.law.geometry.evaluate(
                        source, target_points,
                    ).reference_support
                    if np.any((support_area <= 0.0) & (normal_forces != 0.0)):
                        raise ValueError("contact path checkpoint nodal forces are unsupported")
                    expected_pressure = np.zeros_like(support_area)
                    np.divide(normal_forces, support_area, out=expected_pressure,
                              where=support_area > 0.0)
                    if not np.allclose(manager.normal_multipliers, expected_pressure,
                                       rtol=1.0e-10, atol=1.0e-12):
                        raise ValueError("contact path checkpoint pressure and nodal forces are incompatible")
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
                scale = max(1.0e-9, max((abs(value) for row in program.waypoints
                                         for value in row), default=0.0))
                control_scales = np.maximum(
                    1.0e-9, np.max(np.abs(np.asarray(program.waypoints)), axis=0),
                ) if semismooth else None
                if semismooth:
                    info["contact_path_control_scales_m"] = control_scales.tolist()
                for step in range(accepted_step + 1, requested_step + 1):
                    cancellation_safe_point(cancellation_token,
                                            f"contact_path.step:{step}")
                    start_q = q.copy()
                    start_multipliers = multipliers.copy()
                    start_normal_multipliers = manager.normal_multipliers.copy() if augmented else None
                    start_normal_forces = normal_forces.copy() if semismooth else None
                    target = program.target_at(step)
                    force_values = program.force_values_at(step)
                    external = np.zeros_like(zeros)
                    external[force_dofs] = force_values
                    reduced_external = np.asarray(T.T @ external).reshape(-1)
                    if semismooth:
                        step_result = solve_semismooth_increment(
                            model=model, manager=manager, settings=settings,
                            q=q, reactions=multipliers,
                            nodal_forces=normal_forces,
                            committed_states=committed_states,
                            transform=T, offset=u0, control_rows=rows,
                            control_reactions=reactions, target=target,
                            reduced_external=reduced_external,
                            num_layers=num_layers, max_iterations=max_iterations,
                            tolerance=tolerance, control_scales=control_scales,
                            path_force_magnitude=float(np.sum(np.abs(force_values))),
                            cancellation_token=cancellation_token, step=step,
                        )
                        total_iterations += step_result.iterations
                        if not step_result.completed:
                            failure_reason = step_result.reason
                            info["contact_failure"] = step_result.diagnostics
                            _discard_nonlinear_state_candidate(committed_states)
                            q = start_q
                            multipliers = start_multipliers
                            manager.set_normal_multipliers(start_normal_multipliers)
                            status = "stopped_at_limit" if previous_steps else "diverged"
                            break
                        q = step_result.q
                        multipliers = step_result.reactions
                        normal_forces = step_result.nodal_forces
                        accepted_u = np.asarray(T @ q + u0).reshape(-1)
                        raw_contact = step_result.contact
                        support_area = np.asarray(raw_contact.state.reference_support)
                        pressure = np.zeros_like(support_area)
                        np.divide(normal_forces, support_area, out=pressure,
                                  where=support_area > 0.0)
                        manager.set_normal_multipliers(pressure)
                        reported_force, _reported_tangent, certificate = (
                            manager.evaluate(accepted_u, tangent=False)
                        )
                        force_scale = max(1.0, float(np.linalg.norm(
                            reduced_external + reactions @ multipliers)))
                        if (np.linalg.norm(reported_force-raw_contact.force)
                                > tolerance*force_scale
                                or not certificate.gap_tolerance_met
                                or manager.has_unresolved_weak_open_gap(
                                    certificate, manager.normal_multipliers)):
                            failure_reason = "contact_semismooth_report_or_gap_mismatch"
                            _discard_nonlinear_state_candidate(committed_states)
                            q = start_q
                            multipliers = start_multipliers
                            normal_forces = start_normal_forces
                            manager.set_normal_multipliers(start_normal_multipliers)
                            status = "stopped_at_limit" if previous_steps else "diverged"
                            break
                        projected_pair_evaluations = certificate.pair_geometry_evaluations
                        certificate = raw_certificate(
                            manager, accepted_u, raw_contact, certificate,
                        )
                        admission = getattr(manager,
                                            "d1_interior_admission_issue", None)
                        issue = (admission(certificate, accepted_u, T)
                                 if admission is not None else None)
                        if issue is not None:
                            failure_reason = "contact_d1_interior_profile_rejected"
                            info["contact_failure"] = {
                                "step_index": step, "issue": issue,
                            }
                            _discard_nonlinear_state_candidate(committed_states)
                            q = start_q
                            multipliers = start_multipliers
                            normal_forces = start_normal_forces
                            manager.set_normal_multipliers(start_normal_multipliers)
                            status = "stopped_at_limit" if previous_steps else "diverged"
                            break
                        committed_states = _commit_nonlinear_state_candidate(
                            committed_states, step_result.candidate_states,
                            model=model, accepted_displacements=accepted_u,
                        )
                        with suspend_contact():
                            recovered, _K, _states = _assemble_nonlinear_system(
                                model, accepted_u, committed_states, num_layers,
                                tangent=False, kinematics="von_karman",
                                require_full_coordinates=True,
                            )
                        _discard_nonlinear_state_candidate(committed_states)
                        support = _support_reaction_resultants(
                            model, recovered + raw_contact.force
                            - controls.T @ multipliers - external,
                        )
                        accepted_step = step
                        record = {
                            "step_index": step,
                            "target": target.tolist(),
                            "reaction_generalized": multipliers.tolist(),
                            "residual_norm": step_result.residual_norm,
                            "constraint_error": step_result.constraint_norm,
                            "augmentation_iterations": 0,
                            "semismooth_iterations": step_result.iterations,
                            "semismooth_linear_solver": settings.monolithic_linear_solver,
                            "semismooth_maximum_pivots": settings.monolithic_maximum_pivots,
                            "complementarity_relative_force":
                            step_result.complementarity_norm,
                            "candidate_evaluations": step_result.candidate_evaluations,
                            "projected_diagnostic_pair_evaluations":
                            projected_pair_evaluations,
                            "backtracks": step_result.backtracks,
                            "contact": certificate.to_dict(),
                        }
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
                            iterations=step_result.iterations,
                            residual_norm=step_result.residual_norm,
                            displacement_norm=float(np.linalg.norm(accepted_u)),
                            max_equivalent_plastic_strain=_max_plastic_strain(
                                committed_states),
                            active_stage=f"segment_{(step - 1) // program.steps_per_segment + 1}",
                            support_reactions=support,
                        ))
                        if record_increment_snapshots:
                            snapshots.append(_increment_snapshot(
                                step, step / program.total_steps,
                                accepted_u, committed_states,
                                control_value=(float(target[0])
                                               if target.size else None),
                            ))
                        continue
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
                    schur_relinearizations = 0
                    schur_epoch_attempts = 0
                    schur_epoch_relinearizations = 0
                    schur_active_signature = None
                    pressure_map_attempts = 0
                    pivot_backup = None
                    schur_backtrack_source = None
                    schur_backtrack_signature = None
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
                            try:
                                internal, tangent, trial = _assemble_nonlinear_system(
                                    model, u, committed_states, num_layers,
                                    kinematics="von_karman",
                                )
                            except UnsupportedQ4S3Branch as exc:
                                candidate_evaluation_error = str(exc)
                                failure_reason = (
                                    "contact_candidate_evaluation_failed"
                                    if pivot_backup is not None else
                                    "contact_derivative_branch_unresolved"
                                )
                                if pivot_backup is None:
                                    augmentation_trace.append({
                                        "augmentation": augmentation,
                                        "derivative_branch_failure": str(exc),
                                    })
                                break
                            except ValueError as exc:
                                if (pivot_backup is None or
                                        settings.augmentation_acceleration
                                        != "supported_schur_dev"):
                                    raise
                                failure_reason = "contact_candidate_evaluation_failed"
                                candidate_evaluation_error = str(exc)
                                break
                            residual = (reduced_external + reactions @ multipliers
                                        - np.asarray(T.T @ internal).reshape(-1))
                            constraint = target - rows @ q
                            residual_norm = float(np.linalg.norm(residual))
                            constraint_norm = float(np.max(np.abs(constraint)))
                            force_scale = max(1.0, float(np.linalg.norm(
                                reduced_external + reactions @ multipliers)))
                            equilibrium_force_limit = tolerance * force_scale
                            if (residual_norm <= equilibrium_force_limit and
                                    constraint_norm <= tolerance * scale):
                                proposed_certificate = manager.evaluate(
                                    u, tangent=False,
                                )[2]
                                if (augmented and getattr(
                                        manager.law, "pressure_basis", None) is not None):
                                    supported_area = np.asarray(
                                        proposed_certificate.reference_support_m2,
                                        dtype=float,
                                    )
                                    supported_area = supported_area[supported_area > 0.0]
                                    if len(supported_area):
                                        equilibrium_force_limit = min(
                                            equilibrium_force_limit,
                                            0.1*settings.pressure_tolerance
                                            *float(np.min(supported_area)),
                                        )
                                if residual_norm <= equilibrium_force_limit:
                                    certificate = proposed_certificate
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
                                rejected_candidate = {}
                                if (failure_reason == "contact_candidate_evaluation_failed"
                                        and settings.q4_s3_shared_edge_tie_step_m is not None):
                                    # Retain the bounded failed development pose
                                    # before restoring the accepted algorithmic
                                    # origin. No candidate state is committed.
                                    candidate_source, candidate_target = manager._positions(u)
                                    rejected_candidate = {
                                        "candidate_source_positions_m": candidate_source.tolist(),
                                        "candidate_target_positions_m": candidate_target.tolist(),
                                        "candidate_normal_multipliers_pa":
                                        manager.normal_multipliers.tolist(),
                                    }
                                q, multipliers, fallback_pressure, _prior_change, _retained = pivot_backup
                                manager.set_normal_multipliers(fallback_pressure)
                                pivot_backup = None
                                schur_backtrack_source = None
                                schur_backtrack_signature = None
                                pivot_rejected += 1
                                augmentation_trace.append({
                                    ("schur_rejected" if settings.augmentation_acceleration
                                     == "supported_schur_dev" else "pivot_rejected"): failure_reason,
                                    "augmentation": augmentation,
                                    **({"candidate_evaluation_error":
                                        candidate_evaluation_error}
                                       if failure_reason == "contact_candidate_evaluation_failed"
                                       else {}),
                                    **rejected_candidate,
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
                                schur_backtrack_source = None
                                schur_backtrack_signature = None
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
                                signature_changed = False
                                signature_error = None
                                if schur_backtrack_signature is not None:
                                    try:
                                        source_pose, target_pose = manager._positions(u)
                                        signature_changed = (
                                            (manager.law.geometry.evaluate(
                                                source_pose, target_pose,
                                            ).overlap_signature,
                                             _projected_clip_signature(
                                                 manager.law.geometry,
                                                 source_pose, target_pose))
                                            != schur_backtrack_signature
                                        )
                                    except Exception as exc:
                                        signature_changed = True
                                        signature_error = (
                                            f"{type(exc).__name__}: {exc}")[:240]
                                if (not certificate.gap_tolerance_met
                                        or active_changed
                                        or signature_changed
                                        or normal_multiplier_change >= 0.75*prior_change):
                                    if (settings.augmentation_acceleration == "supported_schur_dev"
                                            and settings.augmentation_schur_maximum_relinearizations
                                            > schur_epoch_relinearizations
                                            and certificate.gap_tolerance_met
                                            and not active_changed
                                            and not signature_changed
                                            and normal_multiplier_change < prior_change
                                            and augmentation <= augmentation_limit-2):
                                        schur_relinearizations += 1
                                        schur_epoch_relinearizations += 1
                                        correction_trace = {
                                            "augmentation": augmentation,
                                            "schur_relinearization": schur_relinearizations,
                                            "schur_intermediate_pressure_change":
                                            normal_multiplier_change,
                                            "schur_prior_pressure_change": prior_change,
                                        }
                                        try:
                                            corrected = refined_patch_supported_schur(
                                                manager, u, tangent, T, rows,
                                                difference_step=settings.augmentation_schur_difference_step_m,
                                                maximum_pressure=settings.augmentation_schur_maximum_pressure_pa,
                                                maximum_pressure_step=settings.augmentation_schur_maximum_step_pa,
                                                maximum_modes=settings.augmentation_schur_maximum_modes,
                                                diagnostics=correction_trace,
                                                check_cancel=lambda: cancellation_safe_point(
                                                    cancellation_token,
                                                    f"contact_path.step:{step}.augmentation:{augmentation}.schur_relinearization",
                                                ),
                                            )
                                        except SolveCancelled:
                                            q = fallback_q
                                            multipliers = fallback_controls
                                            manager.set_normal_multipliers(
                                                fallback_pressure)
                                            raise
                                        except (ValueError, MemoryError, np.linalg.LinAlgError) as exc:
                                            correction_trace["schur_relinearization_ineligible"] = str(exc)
                                            corrected = None
                                        except Exception as exc:
                                            q = fallback_q
                                            multipliers = fallback_controls
                                            manager.set_normal_multipliers(
                                                fallback_pressure)
                                            correction_trace["schur_relinearization_failure"] = str(exc)
                                            augmentation_trace.append(correction_trace)
                                            failure_reason = "contact_supported_schur_relinearization_failed"
                                            break
                                        correction_trace["schur_relinearization_proposed"] = (
                                            corrected is not None)
                                        augmentation_trace.append(correction_trace)
                                        if corrected is not None:
                                            schur_backtrack_source = None
                                            schur_backtrack_signature = None
                                            pivot_backup = (
                                                fallback_q, fallback_controls,
                                                fallback_pressure, prior_change,
                                                corrected.active_indices,
                                            )
                                            manager.set_normal_multipliers(
                                                corrected.multipliers)
                                            continue
                                    q = fallback_q
                                    multipliers = fallback_controls
                                    manager.set_normal_multipliers(fallback_pressure)
                                    pivot_rejected += 1
                                    rejection_trace = {
                                        ("schur_rejected" if settings.augmentation_acceleration
                                         == "supported_schur_dev" else "pivot_rejected"):
                                        "nonlinear_verification",
                                        "augmentation": augmentation,
                                        "pressure_change": normal_multiplier_change,
                                        "minimum_gap": _reported_lower_gap(certificate),
                                        **({"schur_prior_pressure_change": prior_change,
                                            "schur_actual_to_prior_ratio": (
                                                normal_multiplier_change/prior_change
                                                if prior_change > 0.0 else None),
                                            "schur_predicted_active_indices": list(retained),
                                            "schur_actual_active_indices": [
                                                int(index) for index in actual_active],
                                            "schur_active_changed": active_changed,
                                            "schur_overlap_signature_changed": signature_changed,
                                            **({"schur_overlap_signature_error": signature_error}
                                               if signature_error is not None else {}),
                                            "schur_gap_tolerance_met": bool(
                                                certificate.gap_tolerance_met)}
                                           if settings.augmentation_acceleration
                                           == "supported_schur_dev" else {}),
                                    }
                                    augmentation_trace.append(rejection_trace)
                                    if (schur_backtrack_source is not None
                                            and certificate.gap_tolerance_met
                                            and not active_changed
                                            and not signature_changed
                                            and schur_backtrack_signature[1] is not None
                                            and schur_epoch_attempts
                                            < settings.augmentation_schur_maximum_attempts
                                            and augmentation <= augmentation_limit-2):
                                        cancellation_safe_point(
                                            cancellation_token,
                                            f"contact_path.step:{step}.augmentation:{augmentation}.schur_backtrack",
                                        )
                                        schur_epoch_attempts += 1
                                        pivot_attempts += 1
                                        try:
                                            backtrack = propose_supported_schur_secant_backtrack(
                                                schur_backtrack_source,
                                                getattr(certificate,
                                                        "normalized_weighted_gap_m",
                                                        None),
                                                diagnostics=rejection_trace,
                                            )
                                            if backtrack is not None:
                                                rejection_trace["schur_backtrack_model"] = (
                                                    "full_trial_gap_secant")
                                            else:
                                                backtrack = propose_supported_schur_backtrack(
                                                    schur_backtrack_source,
                                                    diagnostics=rejection_trace,
                                                )
                                                if backtrack is not None:
                                                    rejection_trace["schur_backtrack_model"] = (
                                                        "local_linear")
                                        except (ValueError, MemoryError,
                                                np.linalg.LinAlgError) as exc:
                                            rejection_trace["schur_backtrack_ineligible"] = str(exc)
                                            backtrack = None
                                        schur_backtrack_source = None
                                        rejection_trace["schur_backtrack_proposed"] = (
                                            backtrack is not None)
                                        if backtrack is not None:
                                            pivot_backup = (
                                                fallback_q.copy(),
                                                fallback_controls.copy(),
                                                fallback_pressure.copy(),
                                                prior_change,
                                                backtrack.active_indices,
                                            )
                                            rejection_trace["schur_backtrack_fraction"] = (
                                                backtrack.step_fraction)
                                            rejection_trace["schur_backtrack_predicted_residual_pa"] = (
                                                backtrack.predicted_residual_after)
                                            rejection_trace["schur_backtrack_predicted_active_indices"] = (
                                                list(backtrack.active_indices))
                                            manager.set_normal_multipliers(
                                                backtrack.multipliers)
                                            continue
                                    schur_backtrack_source = None
                                    schur_backtrack_signature = None
                                    accelerator = (ProjectedAugmentationSecant()
                                                   if settings.augmentation_acceleration == "active_secant_pivot"
                                                   else None)
                                    continue
                                pivot_applied += 1
                                schur_backtrack_source = None
                                schur_backtrack_signature = None
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
                                **({"macro_equilibrium_force_limit_n": equilibrium_force_limit}
                                   if getattr(manager.law, "pressure_basis", None) is not None else {}),
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
                                "reference_support_m2": list(
                                    getattr(certificate, "reference_support_m2", ())
                                ),
                                "normal_multiplier_estimate_pa": list(
                                    getattr(certificate, "normal_multiplier_estimate_pa", ())
                                ),
                                "source_pressure_node_ids": list(
                                    getattr(certificate, "source_pressure_node_ids", ())
                                ),
                            })
                            if settings.augmentation_acceleration == "supported_schur_dev":
                                active_signature = tuple(np.flatnonzero(
                                    np.asarray(certificate.numerical_pressure_pa) > 0.0,
                                ))
                                if active_signature != schur_active_signature:
                                    if schur_active_signature is not None:
                                        augmentation_trace[-1]["schur_active_epoch_reset"] = {
                                            "prior_active_indices": [
                                                int(index) for index in schur_active_signature
                                            ],
                                            "current_active_indices": [
                                                int(index) for index in active_signature
                                            ],
                                            "prior_epoch_attempts": schur_epoch_attempts,
                                            "prior_epoch_relinearizations": (
                                                schur_epoch_relinearizations
                                            ),
                                        }
                                    schur_active_signature = active_signature
                                    schur_epoch_attempts = 0
                                    schur_epoch_relinearizations = 0
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
                                    and schur_epoch_attempts < settings.augmentation_schur_maximum_attempts
                                    and augmentation >= 2
                                    and augmentation <= augmentation_limit - 2
                                    and certificate.active_pressure_dofs > 0):
                                pivot_attempts += 1
                                schur_epoch_attempts += 1
                                try:
                                    schur = refined_patch_supported_schur(
                                        manager, u, tangent, T, rows,
                                        difference_step=settings.augmentation_schur_difference_step_m,
                                        maximum_pressure=settings.augmentation_schur_maximum_pressure_pa,
                                        maximum_pressure_step=settings.augmentation_schur_maximum_step_pa,
                                        maximum_modes=settings.augmentation_schur_maximum_modes,
                                        retain_backtrack=settings.augmentation_schur_nonlinear_backtrack_dev,
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
                                    if (settings.q4_s3_shared_edge_tie_step_m is not None
                                            and "pressure response derivative disagrees"
                                            in str(exc)):
                                        source_pose, target_pose = manager._positions(u)
                                        augmentation_trace[-1]["schur_ineligible_pose"] = {
                                            "source_positions_m": source_pose.tolist(),
                                            "target_positions_m": target_pose.tolist(),
                                            "normal_multipliers_pa":
                                            manager.normal_multipliers.tolist(),
                                        }
                                    schur = None
                                except Exception as exc:
                                    failure_reason = "contact_supported_schur_linearization_failed"
                                    augmentation_trace[-1]["schur_failure"] = str(exc)
                                    break
                                augmentation_trace[-1]["schur_proposed"] = schur is not None
                                if schur is not None:
                                    schur_backtrack_source = (
                                        schur if settings.augmentation_schur_nonlinear_backtrack_dev
                                        else None
                                    )
                                    if schur_backtrack_source is not None:
                                        try:
                                            source_pose, target_pose = manager._positions(u)
                                            schur_backtrack_signature = (
                                                manager.law.geometry.evaluate(
                                                    source_pose, target_pose,
                                                ).overlap_signature,
                                                _projected_clip_signature(
                                                    manager.law.geometry,
                                                    source_pose, target_pose,
                                                ),
                                            )
                                        except Exception as exc:
                                            schur_backtrack_source = None
                                            schur_backtrack_signature = None
                                            augmentation_trace[-1][
                                                "schur_backtrack_signature_unavailable"
                                            ] = f"{type(exc).__name__}: {exc}"[:240]
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
                                "schur_relinearizations": schur_relinearizations,
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
                    admission = getattr(manager,
                                        "d1_interior_admission_issue", None)
                    issue = (admission(certificate, accepted_u, T)
                             if admission is not None else None)
                    if issue is not None:
                        failure_reason = "contact_d1_interior_profile_rejected"
                        info["contact_failure"] = {
                            "step_index": step, "issue": issue,
                        }
                        _discard_nonlinear_state_candidate(committed_states)
                        q = start_q
                        multipliers = start_multipliers
                        if augmented:
                            manager.set_normal_multipliers(start_normal_multipliers)
                        status = "stopped_at_limit" if previous_steps else "diverged"
                        break
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
                        record["schur_relinearizations"] = schur_relinearizations
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
                    if record_increment_snapshots:
                        snapshots.append(_increment_snapshot(
                            step, step / program.total_steps,
                            accepted_u, committed_states,
                            control_value=(float(target[0])
                                           if target.size else None),
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
                        **({"enforcement_solver": settings.enforcement_solver}
                           if semismooth else {}),
                        **({"monolithic_linear_solver": settings.monolithic_linear_solver,
                            "monolithic_maximum_pivots": settings.monolithic_maximum_pivots}
                           if semismooth else {}),
                        **({"augmentation_acceleration": settings.augmentation_acceleration}
                           if settings.augmentation_acceleration != "none" else {}),
                        **({"nodal_forces_n": program.force_values_at(
                            accepted_step,
                        ).tolist()} if program.nodal_forces else {}),
                    },
                    "general_contact": (history[-1]["contact"] if semismooth and history
                                        else manager.evaluate(final_u, tangent=False)[2].to_dict()),
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
                            **({"normal_forces": normal_forces.tolist()}
                               if semismooth else {}),
                        },
                    )
                return NonlinearStaticResult(
                    previous_steps, status, final_u,
                    accepted_step / program.total_steps,
                    finished_states, info, snapshots=tuple(snapshots),
                    restart_checkpoint=checkpoint,
                )

        return _run_with_nonlinear_state_cleanup(run)

    return _run_with_qualified_assembly_runtime_lease(
        model, context="solve_static_contact_path", operation=operation,
    )
