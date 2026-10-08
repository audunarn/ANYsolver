"""Bounded general-nodal S3 patch mortar development static owner."""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from scipy import sparse

from .core import ContactDefinition, ContactSolverSettings, ContactValidationReport
from .s3_patch_mortar_energy import MovingS3PatchPrimalMortarPenalty, S3PatchFace
from .s3_pair_static import _normal, _normal_controls, _swept_gap_lower, _vertex_gap_lower
from .s3_skin_work import S3SkinWorkAdapter
from .q4_source_overlap import (
    q4_source_gap_lower, q4_source_projected_gap_lower,
    q4_source_projected_swept_gap_lower, q4_source_swept_gap_lower,
)
from .q4_overlap_local_bound import (
    overlap_local_lower, overlap_local_swept_lower,
    _normal_controls_interval, _dot, _interval,
)
from .fixed_projection_graph import fixed_projection_graph_swept_certificate
from .pressure_space import supported_pressure_gram
from .pressure_basis import (
    build_q4_source_macro_q1_pair_basis,
    build_q4_source_selected_q1_basis,
)
from .d1_interior_profile import (
    active_boundary_issue, physical_q4_rim_node_ids,
    projected_coverage_issue, swept_projected_coverage_admissible,
)


def _affine_midpoint_with_error(left, right, left_error, right_error):
    """Enclose the original path midpoint, including rounded representatives."""
    middle = tuple(0.5*(a+b) for a, b in zip(left, right))
    if left_error is None:
        return middle, None
    errors = []
    for a, b, ae, be, value in zip(left, right, left_error, right_error, middle):
        low = np.nextafter(0.5*np.nextafter(
            np.nextafter(a-ae, -np.inf)
            + np.nextafter(b-be, -np.inf), -np.inf), -np.inf)
        high = np.nextafter(0.5*np.nextafter(
            np.nextafter(a+ae, np.inf)
            + np.nextafter(b+be, np.inf), np.inf), np.inf)
        errors.append(np.nextafter(np.maximum(value-low, high-value), np.inf))
    return middle, tuple(errors)


PROFILE = "S3_PATCH_GENERAL_NODAL_PRIMAL_MORTAR_PENALTY_STATIC_DEV_V0"
MIXED_PROFILE = "S3_Q4_PATCH_GENERAL_NODAL_PRIMAL_MORTAR_PENALTY_STATIC_DEV_V0"
SOURCE_Q4_PROFILE = "Q4_S3_PATCH_GENERAL_NODAL_PRIMAL_MORTAR_PENALTY_STATIC_DEV_V0"
Q4_PAIR_PROFILE = "Q4_Q4_GENERAL_NODAL_PRIMAL_MORTAR_PENALTY_STATIC_DEV_V0"
AUGMENTED_PROFILE = "S3_PATCH_GENERAL_NODAL_PRIMAL_MORTAR_AUGMENTED_STATIC_DEV_V1"
AUGMENTED_MIXED_PROFILE = "S3_Q4_PATCH_GENERAL_NODAL_PRIMAL_MORTAR_AUGMENTED_STATIC_DEV_V1"
SOURCE_Q4_AUGMENTED_PROFILE = "Q4_S3_PATCH_GENERAL_NODAL_PRIMAL_MORTAR_AUGMENTED_STATIC_DEV_V1"
SOURCE_Q4_PROJECTED_AUGMENTED_PROFILE = "Q4_S3_PATCH_GENERAL_NODAL_PRIMAL_MORTAR_AUGMENTED_STATIC_DEV_V2"
Q4_PAIR_AUGMENTED_PROFILE = "Q4_Q4_GENERAL_NODAL_PRIMAL_MORTAR_AUGMENTED_STATIC_DEV_V1"
Q4_PAIR_PROJECTED_AUGMENTED_PROFILE = "Q4_Q4_GENERAL_NODAL_PRIMAL_MORTAR_AUGMENTED_STATIC_DEV_V2"
REFINED_AUGMENTED_PROFILE = "S3_PATCH_REFINED_NODAL_PRIMAL_MORTAR_AUGMENTED_STATIC_DEV_V1"
REFINED_Q4_S3_AUGMENTED_PROFILE = "Q4_S3_PATCH_REFINED_NODAL_PRIMAL_MORTAR_AUGMENTED_STATIC_DEV_V1"
REFINED_Q4_S3_PROJECTED_AUGMENTED_PROFILE = "Q4_S3_PATCH_REFINED_PROJECTED_NODAL_PRIMAL_MORTAR_AUGMENTED_STATIC_DEV_V0"
REFINED_Q4_S3_OVERLAP_LOCAL_AUGMENTED_PROFILE = "Q4_S3_PATCH_REFINED_OVERLAP_LOCAL_AUGMENTED_STATIC_DEV_V0"
REFINED_Q4_S3_ROUNDOFF_AUGMENTED_PROFILE = "Q4_S3_PATCH_REFINED_NODAL_PRIMAL_MORTAR_ROUNDOFF_AUGMENTED_STATIC_DEV_V2"
REFINED_Q4_S3_GRAPH_AUGMENTED_PROFILE = "Q4_S3_PATCH_REFINED_FIXED_PROJECTION_GRAPH_AUGMENTED_STATIC_DEV_V0"

REFINED_Q4_S3_PROJECTED_PENALTY_PROFILE = "Q4_S3_PATCH_REFINED_PROJECTED_FINITE_PENALTY_STATIC_DEV_V0"
S3_Q4_PROJECTED_PENALTY_PROFILE = "S3_Q4_PROJECTED_FINITE_PENALTY_STATIC_DEV_V0"
S3_PROJECTED_PENALTY_PROFILE = "S3_PATCH_PROJECTED_FINITE_PENALTY_STATIC_DEV_V0"


class SupportResetForceBudgetExceeded(ValueError):
    """A proposed algorithmic multiplier reset changes too much local work."""


def _selected(definition: ContactDefinition):
    if len(definition.interactions) != 1:
        raise ValueError("S3 patch needs one interaction")
    interaction = definition.interactions[0]
    names = {surface.name: surface for surface in definition.surfaces}
    if (interaction.surface not in names or interaction.target not in names
            or interaction.surface == interaction.target):
        raise ValueError("S3 patch interaction must name different source and target surfaces")
    return names[interaction.surface], names[interaction.target], interaction


def _adapters(model, selected):
    from anysolver.e4_pl_element import QualifiedE4PLShellElement
    from .q4_skin_work import Q4SkinWorkAdapter

    return tuple(tuple(
        (Q4SkinWorkAdapter if type(model.mesh.elements.get(element_id))
         is QualifiedE4PLShellElement else S3SkinWorkAdapter).from_model(
            model, side+1, element_id, surface.side,
        )
        for element_id in surface.element_ids
    ) for side, surface in enumerate(selected))


def _patch_faces(adapters):
    return tuple(tuple(S3PatchFace(item.node_ids, item.reference_positions)
                       for item in side) for side in adapters)


def _unique_work_map(adapters, node_ids):
    blocks = {}
    positions = {}
    for adapter in adapters:
        for local, node in enumerate(adapter.node_ids):
            block = adapter.work_map[3*local:3*local+3, :].tocsr()
            position = adapter.reference_positions[local]
            if node in blocks:
                delta = (blocks[node]-block).tocsr()
                if delta.nnz and np.max(np.abs(delta.data)) > 1e-12:
                    raise ValueError("shared S3 patch node has inconsistent skin work map")
                if np.linalg.norm(positions[node]-position) > 1e-12*max(
                    1.0, float(np.max(np.abs(position))),
                ):
                    raise ValueError("shared S3 patch node has inconsistent skin position")
            else:
                blocks[node] = block
                positions[node] = position
    mapping = sparse.vstack([blocks[node] for node in node_ids]).tocsr()
    reference = np.asarray([positions[node] for node in node_ids], dtype=float)
    return reference, mapping


def validate_general_s3_patch(model, definition: ContactDefinition,
                              settings: ContactSolverSettings) -> ContactValidationReport:
    return _validate_general_s3_patch(model, definition, settings)


def _validate_general_s3_patch(model, definition, settings, *, prepared=None):
    # A manager may consume this preparation immediately in the same call.
    # There is no model/global cache or reuse across poses or definitions.
    issues: list[str] = []
    from anysolver.e4_pl_element import QualifiedE4PLShellElement
    from anysolver.e4_pl_s3_v2d_element import NativeParityE4PLS3V2DShellElement

    profile = PROFILE
    if (len(definition.surfaces) != 2 or definition.rigid_bodies
            or len(definition.interactions) != 1):
        return ContactValidationReport("invalid", (
            "general S3 patch needs two surfaces, no rigid body and one interaction",
        ), profile)
    if (settings.pair_motion != "general"
            or settings.normal_discretization != "primal_mortar"):
        issues.append("general S3 patch needs general primal-mortar settings")
    if settings.general_s3_difference_step is None:
        issues.append("general S3 patch needs explicit general_s3_difference_step")
    if settings.sliding_difference_step is not None:
        issues.append("general S3 patch does not use sliding_difference_step")
    try:
        source, target, interaction = _selected(definition)
    except ValueError as exc:
        return ContactValidationReport("invalid", (str(exc),), profile)
    augmented = interaction.normal_law == "augmented"
    projected_penalty = interaction.normal_law == "projected_penalty"
    if (interaction.normal_law not in {"penalty", "augmented", "projected_penalty"}
            or interaction.normal_stiffness is None
            or interaction.line_stiffness is not None
            or interaction.endpoint_stiffness is not None):
        issues.append("general S3 patch needs surface-pressure stiffness only")
    if augmented and settings.pressure_tolerance is None:
        issues.append("augmented S3 patch needs explicit pressure_tolerance")
    from anymaterial import IsotropicMaterial
    target_q4 = [element_id for element_id in target.element_ids
                 if type(model.mesh.elements.get(element_id)) is QualifiedE4PLShellElement]
    source_q4 = [element_id for element_id in source.element_ids
                 if type(model.mesh.elements.get(element_id)) is QualifiedE4PLShellElement]
    q4_pair = (len(source.element_ids) == len(target.element_ids) == 1
               and len(source_q4) == len(target_q4) == 1)
    bounded = (1 <= len(source.element_ids) <= 2
               and 1 <= len(target.element_ids) <= 2
               and (len(source.element_ids)+len(target.element_ids) >= 3
                    or q4_pair))
    projected_s3_q4 = (projected_penalty and not source_q4
                       and len(source.element_ids) == 2
                       and len(target.element_ids) == len(target_q4) == 1)
    if settings.general_s3_differentiation == "jet2_s3_q4_dev" and not projected_s3_q4:
        issues.append("S3/Q4 Jet2 requires two source S3 and one target Q4 with projected penalty")
    projected_s3 = projected_penalty and not source_q4 and not target_q4
    refined_s3 = ((augmented or projected_s3) and not source_q4 and not target_q4
                  and len(source.element_ids) >= 2
                  and len(target.element_ids) >= 1
                  and (len(source.element_ids) > 2 or len(target.element_ids) > 2))
    refined_q4 = ((augmented or projected_penalty) and len(source.element_ids) >= 2
                  and len(source_q4) == len(source.element_ids)
                  and not target_q4 and len(target.element_ids) >= 1)
    refined = refined_s3 or refined_q4
    if (settings.general_s3_differentiation == "jet2_s3_dev"
            and not ((augmented or projected_s3) and not source_q4 and not target_q4
                     and len(source.element_ids)+len(target.element_ids) >= 3)):
        issues.append("Jet2 S3 development derivative needs an augmented S3/S3 patch of at least three faces")
    if (settings.general_s3_differentiation == "jet2_q4_s3_dev"
            and not refined_q4):
        issues.append("Jet2 Q4/S3 development derivative needs a refined augmented Q4/S3 patch")
    if settings.q4_source_pressure_basis == "macro_q1_pair_dev":
        if (not refined_q4
                or settings.general_s3_differentiation != "jet2_q4_s3_dev"
                or settings.augmentation_support_resolution != "exact"):
            issues.append("macro Q1 pressure needs refined augmented Q4/S3 Jet2 with exact support")
        else:
            try:
                build_q4_source_macro_q1_pair_basis(tuple(
                    tuple(int(node) for node in model.mesh.elements[element_id].node_ids)
                    for element_id in source.element_ids
                ))
            except ValueError as exc:
                issues.append(f"macro Q1 pressure topology: {exc}")
    if settings.q4_source_pressure_basis == "selected_q1_knots_dev":
        if (not refined_q4
                or settings.general_s3_differentiation != "jet2_q4_s3_dev"
                or settings.augmentation_support_resolution != "exact"):
            issues.append("selected Q1 pressure needs refined augmented Q4/S3 Jet2 with exact support")
        else:
            try:
                build_q4_source_selected_q1_basis(
                    tuple(tuple(int(node) for node in
                                model.mesh.elements[element_id].node_ids)
                          for element_id in source.element_ids),
                    settings.q4_source_pressure_knot_columns,
                )
            except ValueError as exc:
                issues.append(f"selected Q1 pressure topology: {exc}")
    if settings.general_s3_differentiation in {"jet2_q4_s3_dev", "jet2_s3_q4_dev"} and any(
        getattr(settings, name) is None for name in (
            "q4_source_support_gradient_tolerance",
            "q4_source_support_hessian_tolerance",
            "q4_source_weighted_gap_gradient_tolerance",
            "q4_source_weighted_gap_hessian_tolerance",
        )
    ):
        issues.append("Jet2 Q4/S3 development derivative needs four explicit derivative tolerances")
    if not (bounded or refined):
        issues.append("general shell patch needs three faces or one Q4/Q4 pair")
    if len(source.element_ids)*len(target.element_ids) > settings.maximum_candidate_pairs:
        issues.append("general S3 patch exceeds candidate pair resource budget")
    if (source_q4 and not refined_q4 and
            (len(source.element_ids) != 1
             or len(target.element_ids) != 2
             or target_q4) and not q4_pair):
        issues.append("Q4 pressure-side patch needs one source Q4 and two target S3 faces")
    if source_q4 and (settings.q4_source_area_tolerance is None
                      or settings.q4_source_weighted_gap_tolerance is None
                      or settings.maximum_q4_source_integration_triangles is None):
        issues.append("Q4 pressure-side patch needs explicit area/gap tolerances and triangle budget")
    if target_q4 and (len(target.element_ids) != 1 or len(source.element_ids) != 2) and not q4_pair:
        issues.append("mixed S3/Q4 patch needs two source S3 faces and one target Q4 face")
    if target_q4 and len(target_q4) != len(target.element_ids):
        issues.append("mixed S3/Q4 patch cannot mix target formulations")
    if target_q4 and not q4_pair and (settings.q4_target_weighted_gap_tolerance is None
                      or settings.maximum_q4_target_integration_triangles is None):
        issues.append("mixed S3/Q4 patch needs explicit Q4 weighted-gap tolerance and triangle budget")
    profile = (Q4_PAIR_PROFILE if q4_pair else
               SOURCE_Q4_PROFILE if source_q4 else
               MIXED_PROFILE if target_q4 else PROFILE)
    if projected_penalty:
        profile = (S3_Q4_PROJECTED_PENALTY_PROFILE if projected_s3_q4 else
                   S3_PROJECTED_PENALTY_PROFILE if projected_s3 else
                   REFINED_Q4_S3_PROJECTED_PENALTY_PROFILE)
        if projected_s3_q4:
            if (settings.general_s3_differentiation != "jet2_s3_q4_dev"
                    or settings.q4_source_gap_certificate != "whole_face"
                    or settings.q4_source_pressure_basis != "fine_nodal_q1"
                    or settings.augmentation_support_resolution != "exact"
                    or settings.augmentation_acceleration != "none"
                    or settings.enforcement_solver != "nested_augmented"
                    or settings.q4_s3_shared_edge_tie_step_m is not None
                    or settings.d1_interior_profile
                    or any(value is None for value in (
                        settings.q4_source_area_tolerance,
                        settings.q4_source_weighted_gap_tolerance,
                        settings.maximum_q4_source_integration_triangles))):
                issues.append("projected S3/Q4 needs explicit Jet2 integration controls, whole-face nodal geometry and no augmentation/tie/D1 admission")
        elif projected_s3:
            if (settings.general_s3_differentiation != "jet2_s3_dev"
                    or settings.q4_source_gap_certificate != "whole_face"
                    or settings.q4_source_pressure_basis != "fine_nodal_q1"
                    or settings.augmentation_support_resolution != "exact"
                    or settings.augmentation_acceleration != "none"
                    or settings.enforcement_solver != "nested_augmented"
                    or settings.q4_s3_shared_edge_tie_step_m is not None
                    or settings.d1_interior_profile):
                issues.append("projected S3 penalty needs S3 Jet2 whole-face nodal geometry with exact support and no augmentation, tie or D1 admission")
        elif (not refined_q4
                or settings.general_s3_differentiation != "jet2_q4_s3_dev"
                or settings.q4_source_gap_certificate != "overlap_local_dev"
                or settings.q4_source_pressure_basis != "fine_nodal_q1"
                or settings.augmentation_support_resolution != "exact"
                or settings.augmentation_acceleration != "none"
                or settings.enforcement_solver != "nested_augmented"
                or settings.d1_interior_profile):
            issues.append("projected penalty needs refined Q4/S3 fine-Q1 Jet2 overlap-local geometry without augmentation or D1 admission")
    if augmented:
        profile = (REFINED_Q4_S3_OVERLAP_LOCAL_AUGMENTED_PROFILE
                   if refined_q4 and settings.q4_source_gap_certificate == "overlap_local_dev" else
                   REFINED_Q4_S3_GRAPH_AUGMENTED_PROFILE
                   if refined_q4 and settings.q4_source_gap_certificate == "fixed_projection_graph" else
                   REFINED_Q4_S3_PROJECTED_AUGMENTED_PROFILE
                   if refined_q4 and settings.q4_source_gap_certificate == "projected_matching" else
                   REFINED_Q4_S3_ROUNDOFF_AUGMENTED_PROFILE
                   if refined_q4 and settings.augmentation_support_resolution == "roundoff" else
                   REFINED_Q4_S3_AUGMENTED_PROFILE if refined_q4 else
                   REFINED_AUGMENTED_PROFILE if refined_s3 else
                   Q4_PAIR_PROJECTED_AUGMENTED_PROFILE
                   if q4_pair and settings.q4_source_gap_certificate == "projected_matching" else
                   Q4_PAIR_AUGMENTED_PROFILE if q4_pair else
                   SOURCE_Q4_PROJECTED_AUGMENTED_PROFILE
                   if source_q4 and settings.q4_source_gap_certificate == "projected_matching" else
                   SOURCE_Q4_AUGMENTED_PROFILE if source_q4 else
                   AUGMENTED_MIXED_PROFILE if target_q4 else AUGMENTED_PROFILE)
    if (settings.q4_source_gap_certificate in {"projected_matching", "overlap_local_dev"}
            and not ((augmented or projected_penalty) and (q4_pair or source_q4))):
        issues.append("projected-matching Q4 gap certificate requires augmented Q4/Q4 or Q4/two-S3")
    if (settings.q4_source_gap_certificate == "overlap_local_dev"
            and not refined_q4):
        issues.append("overlap-local development gap requires a refined Q4/S3 patch")
    if settings.q4_source_gap_certificate == "fixed_projection_graph" and not (
            refined_q4 and augmented
            and settings.augmentation_support_resolution == "exact"
            and settings.augmentation_acceleration == "none"):
        issues.append("fixed-projection graph gap requires refined augmented Q4/S3 with exact support and no acceleration")
    for side_index, surface in enumerate((source, target)):
        if surface.beam_radius is not None:
            issues.append(f"surface {surface.name} cannot declare beam radius")
        for element_id in surface.element_ids:
            element = model.mesh.elements.get(element_id)
            if (type(element) is not NativeParityE4PLS3V2DShellElement
                    and not (type(element) is QualifiedE4PLShellElement
                             and (side_index == 1 or bool(source_q4)))):
                issues.append(f"element {element_id} is not admitted S3 source or S3/Q4 target")
                continue
            material = model.materials.get(element.material_name)
            if (type(material) is not IsotropicMaterial
                    or material.yield_stress != 0.0
                    or material.hardening_curve is not None
                    or (type(element) is QualifiedE4PLShellElement
                        and element.shell_section is not None)):
                issues.append(f"element {element_id} needs isotropic elastic material")
    if settings.enforcement_solver == "monolithic_active_set" and (
            not augmented
            or profile not in {REFINED_Q4_S3_AUGMENTED_PROFILE,
                               REFINED_Q4_S3_PROJECTED_AUGMENTED_PROFILE,
                               REFINED_Q4_S3_OVERLAP_LOCAL_AUGMENTED_PROFILE}
            or settings.general_s3_differentiation != "jet2_q4_s3_dev"
            or settings.q4_source_pressure_basis != "fine_nodal_q1"
            or settings.augmentation_support_resolution != "exact"):
        issues.append("monolithic_active_set requires fine Q1 refined Q4/S3 Jet2 augmented contact")
    if issues:
        return ContactValidationReport("invalid", tuple(issues), profile)
    try:
        adapters = _adapters(model, (source, target))
        faces = _patch_faces(adapters)
        potential = MovingS3PatchPrimalMortarPenalty(
            faces[0], faces[1], interaction.normal_stiffness,
            difference_step=settings.general_s3_difference_step,
            maximum_energy_evaluations=settings.maximum_general_s3_energy_evaluations,
            q4_weighted_gap_tolerance=settings.q4_target_weighted_gap_tolerance,
            maximum_q4_integration_triangles=settings.maximum_q4_target_integration_triangles,
            q4_source_area_tolerance=settings.q4_source_area_tolerance,
            q4_source_weighted_gap_tolerance=settings.q4_source_weighted_gap_tolerance,
            maximum_q4_source_integration_triangles=settings.maximum_q4_source_integration_triangles,
            q4_source_derivative_tolerances=(
                settings.q4_source_support_gradient_tolerance,
                settings.q4_source_support_hessian_tolerance,
                settings.q4_source_weighted_gap_gradient_tolerance,
                settings.q4_source_weighted_gap_hessian_tolerance,
            ),
            differentiation=("jet2_s3"
                             if settings.general_s3_differentiation == "jet2_s3_dev"
                             else "jet2_q4_s3"
                             if settings.general_s3_differentiation == "jet2_q4_s3_dev"
                             else "jet2_s3_q4"
                             if settings.general_s3_differentiation == "jet2_s3_q4_dev"
                             else "pair_local" if refined else "global"),
            maximum_candidate_pairs=settings.maximum_candidate_pairs,
        )
        if settings.q4_source_gap_certificate == "fixed_projection_graph":
            represented = False
            for si in potential.source_face_indices:
                for ti in potential.target_face_indices:
                    certificate = fixed_projection_graph_swept_certificate(
                        potential.reference_source[si],
                        potential.reference_source[si],
                        potential.reference_target[ti],
                        potential.reference_target[ti],
                        interaction.gap_tolerance,
                    )
                    represented |= certificate.expanded_overlap_vertices > 0
            if not represented:
                issues.append("fixed-projection graph patch needs reference projected overlap")
        _unique_work_map(adapters[0], potential.source_node_ids)
        _unique_work_map(adapters[1], potential.target_node_ids)
        normal = _normal(adapters[0][0].reference_positions)
        for side_index, side_adapters in enumerate(adapters):
            for adapter in side_adapters:
                local_normal = _normal(adapter.reference_positions)
                if float(local_normal @ normal) <= 0.0:
                    issues.append("S3 patch faces need consistent reference polarity")
                side_sign = (-1.0 if adapter.side == "bottom" else 1.0)
                if adapter.side != "midsurface":
                    directed = side_sign*float(adapter.director @ normal)
                    if (directed >= 0.0 if side_index == 0 else directed <= 0.0):
                        issues.append(f"element {adapter.element_id} physical side faces away from pair")
        roundoff = 256.0*np.finfo(float).eps*max(
            1.0, float(np.max(np.abs(potential.reference_source))),
            float(np.max(np.abs(potential.reference_target))),
        )
        if min(_vertex_gap_lower(
            potential.reference_source[si], potential.reference_target[ti],
        ) for si in potential.source_face_indices
              for ti in potential.target_face_indices) < -roundoff:
            issues.append("source S3 patch reference normal must point from target to source")
    except (ValueError, MemoryError) as exc:
        issues.append(str(exc))
    if not issues and prepared is not None:
        prepared.append((adapters, faces, potential))
    return ContactValidationReport("invalid" if issues else "ok", tuple(issues), profile)


@dataclass(frozen=True)
class _PatchResults:
    profile: str
    minimum_gap: float
    sampled_overlap_gap: float | None
    penalty_energy: float
    current_overlap_area: float
    reference_overlap_area: float
    overlapping_pairs: int
    integration_force: tuple[float, float, float]
    target_force: tuple[float, float, float]
    integration_moment: tuple[float, float, float]
    target_moment: tuple[float, float, float]
    gap_tolerance_met: bool
    active_pressure_dofs: int
    source_pressure_node_ids: tuple[int, ...]
    normalized_weighted_gap_m: tuple[float, ...]
    numerical_pressure_pa: tuple[float, ...]
    reference_support_m2: tuple[float, ...]
    energy_evaluations: int
    weighted_gap_integration_error_m3: float = 0.0
    integration_triangles: int = 0
    area_integration_error_m2: float = 0.0
    augmented_merit_j: float = 0.0
    normal_multiplier_estimate_pa: tuple[float, ...] = ()
    pair_geometry_evaluations: int = 0
    pressure_gram_rank: int | None = None
    pressure_gram_condition_estimate: float | None = None
    multiplier_support_floor_m2: float = 0.0
    unresolved_multiplier_node_ids: tuple[int, ...] = ()
    pressure_gram_supported_modes: int | None = None
    pressure_gram_scaled_rank: int | None = None
    pressure_gram_scaled_condition_estimate: float | None = None
    tie_resolution_relative_error: float | None = None
    pressure_basis_version: str | None = None
    source_geometry_node_ids: tuple[int, ...] = ()
    contact_work_convention: str | None = None
    regularization_storage_j: float | None = None

    @property
    def wrench_origin_m(self):
        """Global origin used by the physical-position cross-force sums."""
        return (0.0, 0.0, 0.0)

    def to_dict(self):
        result = dict(vars(self))
        result["wrench_origin_m"] = list(self.wrench_origin_m)
        for name in ("integration_force", "target_force", "integration_moment",
                     "target_moment", "source_pressure_node_ids",
                     "normalized_weighted_gap_m", "numerical_pressure_pa",
                     "reference_support_m2", "normal_multiplier_estimate_pa"):
            result[name] = list(result[name])
        if self.multiplier_support_floor_m2 > 0.0:
            result["unresolved_multiplier_node_ids"] = list(
                self.unresolved_multiplier_node_ids)
        else:
            for name in ("multiplier_support_floor_m2",
                         "unresolved_multiplier_node_ids"):
                result.pop(name)
        if self.pressure_gram_rank is None:
            result.pop("pressure_gram_rank")
            result.pop("pressure_gram_condition_estimate")
        if self.pressure_gram_scaled_rank is None:
            for name in ("pressure_gram_supported_modes", "pressure_gram_scaled_rank",
                         "pressure_gram_scaled_condition_estimate"):
                result.pop(name)
        if self.tie_resolution_relative_error is None:
            result.pop("tie_resolution_relative_error")
        if self.pressure_basis_version is None:
            result.pop("pressure_basis_version")
            result.pop("source_geometry_node_ids")
        else:
            result["source_geometry_node_ids"] = list(self.source_geometry_node_ids)
        if self.contact_work_convention is None:
            result.pop("contact_work_convention")
            result.pop("regularization_storage_j")
        return result


class GeneralS3PatchManager:
    def __init__(self, model, definition: ContactDefinition,
                 settings: ContactSolverSettings | None = None,
                 initial_displacement: np.ndarray | None = None):
        self.settings = ContactSolverSettings() if settings is None else settings
        prepared = []
        report = _validate_general_s3_patch(
            model, definition, self.settings, prepared=prepared)
        if not report.valid:
            raise ValueError("unsupported general S3 patch: " + "; ".join(report.issues))
        self.definition = definition
        self.profile = report.profile
        source, target, interaction = _selected(definition)
        adapters, faces, potential = prepared[0]
        source_faces = tuple(face.node_ids for face in faces[0])
        self.d1_physical_rim_node_ids = (
            physical_q4_rim_node_ids(model, faces[0])
            if self.settings.d1_interior_profile else frozenset()
        )
        pressure_basis = (
            build_q4_source_macro_q1_pair_basis(source_faces)
            if self.settings.q4_source_pressure_basis == "macro_q1_pair_dev"
            else build_q4_source_selected_q1_basis(
                source_faces, self.settings.q4_source_pressure_knot_columns,
            ) if self.settings.q4_source_pressure_basis == "selected_q1_knots_dev"
            else None
        )
        self.stiffness = interaction.normal_stiffness
        self.augmented = interaction.normal_law == "augmented"
        self.projected_work = self.augmented or interaction.normal_law == "projected_penalty"
        self.gap_tolerance = interaction.gap_tolerance
        self.swept_trial_cutbacks = 0
        self.law = potential
        if self.projected_work:
            from .s3_patch_augmented import MovingS3PatchProjectedNormal

            self.law = MovingS3PatchProjectedNormal(
                self.law,
                support_resolution=self.settings.augmentation_support_resolution,
                pressure_basis=pressure_basis,
            )
            if self.settings.q4_s3_shared_edge_tie_step_m is not None:
                self.law.set_shared_edge_tie(
                    self.settings.q4_s3_shared_edge_tie_step_m,
                    self.settings.q4_s3_shared_edge_tie_direction,
                    self.settings.q4_s3_shared_edge_tie_relative_tolerance,
                )
            self.normal_multipliers = np.zeros(len(self.law.pressure_mode_ids))
            if not self.augmented:
                self.normal_multipliers.setflags(write=False)
            self.last_support_reset = None
        source_ref, source_map = _unique_work_map(adapters[0], self.law.source_node_ids)
        target_ref, target_map = _unique_work_map(adapters[1], self.law.target_node_ids)
        self.reference = source_ref, target_ref
        self.map = sparse.vstack((source_map, target_map)).tocsr()
        self.n_dof = model.mesh.dof_manager.total_dofs
        self.source_coordinates = len(self.law.source_node_ids)*3
        self.reference_normals = (
            _normal(adapters[0][0].reference_positions),
            _normal(adapters[1][0].reference_positions),
        )
        initial = np.zeros(self.n_dof) if initial_displacement is None else initial_displacement
        current = self._positions(initial)
        self.require_d1_coverage(*current)
        lower = self._gap_lower(current)
        scale = max(1.0, *(float(np.max(np.abs(item))) for item in current))
        if lower < -256.0*np.finfo(float).eps*scale:
            raise ValueError(f"general S3 patch initial penetration unresolved: lower bound {lower:.6g} m")

    def _positions(self, displacement):
        u = np.asarray(displacement, dtype=float).reshape(-1)
        if u.size != self.n_dof or not np.all(np.isfinite(u)):
            raise ValueError("general S3 patch displacement has invalid size or values")
        current = np.concatenate(self.reference) + np.asarray(
            self.map @ u,
        ).reshape(-1, 3)
        source_count = len(self.law.source_node_ids)
        return current[:source_count], current[source_count:]

    def require_d1_coverage(self, source, target):
        if not self.settings.d1_interior_profile:
            return
        issue = projected_coverage_issue(
            source, target, self.law.source_face_indices,
            self.law.target_face_indices,
            self.settings.d1_interior_coverage_tolerance_m2,
        )
        if issue is not None:
            raise ValueError("D1 interior profile: " + issue)

    def d1_interior_admission_issue(self, certificate, displacement,
                                    transform, *, control_rows=None):
        if not self.settings.d1_interior_profile:
            return None
        source, target = self._positions(displacement)
        issue = projected_coverage_issue(
            source, target, self.law.source_face_indices,
            self.law.target_face_indices,
            self.settings.d1_interior_coverage_tolerance_m2,
        )
        if issue is not None:
            return issue
        return active_boundary_issue(
            certificate, source, self.law.source_face_indices,
            self.law.source_node_ids, self.d1_physical_rim_node_ids,
            self.map, transform,
            self.settings.d1_interior_boundary_force_tolerance_n,
            control_rows=control_rows,
        )

    def _gap_lower(self, positions):
        source, target = positions
        if self.profile == S3_Q4_PROJECTED_PENALTY_PROFILE:
            from .s3_q4_swept import s3_q4_affine_lower
            bounds = [s3_q4_affine_lower(source[si], source[si], target[ti], target[ti])
                      for si in self.law.source_face_indices for ti in self.law.target_face_indices]
            if not all(np.isfinite(value) for value in bounds):
                raise ValueError("invalid or unresolved S3/Q4 projected corner Jacobian")
            return min(bounds)
        if self.settings.q4_source_gap_certificate == "overlap_local_dev":
            geometry = self.law.geometry if self.projected_work else self.law
            # Validate every feature before pruning: a remote invalid face
            # cannot disappear from admission merely because it is far away.
            geometry._check_same_side_overlap(source, geometry.source_face_indices)
            geometry._check_same_side_overlap(target, geometry.target_face_indices)
            candidates = geometry._candidate_pair_indices(source, target)
            target_count = len(geometry.target_face_indices)
            pairs = (range(len(geometry.pair_laws)) if candidates is None
                     else sorted(candidates))
            # The bound applies to matched points over represented overlap.
            # The existing full-depth projection prisms enclose the actual
            # bilinear corners at any normal separation, including warping.
            return min(
                (max(q4_source_projected_gap_lower(
                    source[geometry.source_face_indices[index // target_count]],
                    target[geometry.target_face_indices[index % target_count]]),
                    overlap_local_lower(
                    source[geometry.source_face_indices[index // target_count]],
                    target[geometry.target_face_indices[index % target_count]], 3)[0])
                 for index in pairs), default=float("inf")
            )
        if self.settings.q4_source_gap_certificate == "fixed_projection_graph":
            lowers = []
            for si in self.law.source_face_indices:
                for ti in self.law.target_face_indices:
                    certificate = fixed_projection_graph_swept_certificate(
                        source[si], source[si], target[ti], target[ti],
                        self.gap_tolerance,
                    )
                    if certificate.expanded_overlap_vertices == 0:
                        continue
                    if certificate.admissible:
                        vertical = certificate.vertical_lower_m
                        lowers.append(vertical/certificate.normal_cosine_lower
                                      if vertical < 0. else
                                      vertical*certificate.normal_cosine_lower)
                    else:
                        lowers.append(q4_source_gap_lower(source[si], target[ti]))
            return min(lowers) if lowers else float("inf")
        q4_lower = (q4_source_projected_gap_lower
                    if self.settings.q4_source_gap_certificate == "projected_matching"
                    else q4_source_gap_lower)
        return min((q4_lower(source[si], target[ti])
                    if len(si) == 4 else
                    _vertex_gap_lower(source[si], target[ti]))
                   for si in self.law.source_face_indices
                   for ti in self.law.target_face_indices)

    def evaluate(self, displacement, *, tangent=True):
        source, target = self._positions(displacement)
        self.require_d1_coverage(source, target)
        lower = self._gap_lower((source, target))
        prepared = (self.law.prepare_work_state(
            source, target, self.normal_multipliers,
        ) if self.projected_work else None)
        state = prepared.state if self.projected_work else self.law.evaluate(source, target)
        local_derivatives = (self.projected_work
                             and self.law.geometry.differentiation
                             in {"pair_local", "jet2_s3", "jet2_q4_s3", "jet2_s3_q4"})
        pair_evaluations = len(self.law.geometry.pair_laws) if local_derivatives else 0
        if state.active_pressure_dofs == 0:
            local_force = np.zeros(self.law.n_coordinates)
            local_tangent = (sparse.csr_matrix((self.law.n_coordinates, self.law.n_coordinates))
                             if tangent else None)
            evaluations = pair_evaluations if local_derivatives else 1
            tie_error = None
        else:
            work = (self.law.work(source, target, self.normal_multipliers,
                                  tangent=tangent, _prepared_state=prepared)
                    if self.projected_work else self.law.work(source, target, tangent=tangent))
            local_force = work.residual
            local_tangent = sparse.csr_matrix(work.tangent) if tangent else None
            evaluations = work.energy_evaluations
            tie_error = work.tie_resolution_relative_error
            if local_derivatives:
                pair_evaluations += work.energy_evaluations
        force = np.asarray(self.map.T @ local_force).reshape(-1)
        stiffness = ((self.map.T @ local_tangent @ self.map).tocsr()
                     if tangent else None)
        physical = -local_force.reshape(-1, 3)
        source_count = len(self.law.source_node_ids)
        source_force = np.sum(physical[:source_count], axis=0)
        target_force = np.sum(physical[source_count:], axis=0)
        source_moment = np.sum(np.cross(source, physical[:source_count]), axis=0)
        target_moment = np.sum(np.cross(target, physical[source_count:]), axis=0)
        gram_rank = gram_condition = None
        gram_scaled = None
        if self.profile in {Q4_PAIR_PROJECTED_AUGMENTED_PROFILE,
                            SOURCE_Q4_PROJECTED_AUGMENTED_PROFILE,
                            REFINED_Q4_S3_AUGMENTED_PROFILE,
                            REFINED_Q4_S3_PROJECTED_AUGMENTED_PROFILE,
                            REFINED_Q4_S3_OVERLAP_LOCAL_AUGMENTED_PROFILE,
                            REFINED_Q4_S3_ROUNDOFF_AUGMENTED_PROFILE,
                            REFINED_Q4_S3_GRAPH_AUGMENTED_PROFILE,
                            REFINED_Q4_S3_PROJECTED_PENALTY_PROFILE,
                            S3_PROJECTED_PENALTY_PROFILE, S3_Q4_PROJECTED_PENALTY_PROFILE}:
            eigenvalues = np.linalg.eigvalsh(state.pressure_gram)
            greatest = max(0.0, float(eigenvalues[-1]))
            threshold = (len(eigenvalues)*np.finfo(float).eps*greatest)
            positive = eigenvalues[eigenvalues > threshold]
            gram_rank = int(len(positive))
            if gram_rank == len(eigenvalues):
                gram_condition = float(greatest/positive[0])
            gram_scaled = supported_pressure_gram(
                state.pressure_gram, state.reference_support,
            )
        support_floor = 0.0
        unresolved_nodes = ()
        if self.augmented and self.settings.augmentation_support_resolution == "roundoff":
            supported, support_floor = self.law.resolved_support(state)
            unresolved_nodes = tuple(
                node_id for node_id, area, active in zip(
                    self.law.pressure_mode_ids, state.reference_support, supported)
                if area > 0.0 and not active
            )
        result = _PatchResults(
            self.profile, lower, state.minimum_physical_gap,
            0.0 if self.projected_work else state.energy,
            state.overlap_area, state.reference_overlap_area,
            state.overlapping_pairs,
            tuple(map(float, source_force)), tuple(map(float, target_force)),
            tuple(map(float, source_moment)), tuple(map(float, target_moment)),
            lower >= -self.gap_tolerance, state.active_pressure_dofs,
            self.law.pressure_mode_ids if self.projected_work else self.law.source_node_ids,
            tuple(map(float, state.normalized_gap)),
            tuple(map(float, state.pressure)),
            tuple(map(float, state.reference_support)), evaluations,
            state.weighted_gap_integration_error,
            state.integration_triangles,
            state.area_integration_error,
            state.energy if self.augmented else 0.0,
            tuple(map(float, self.normal_multipliers)) if self.augmented else (),
            pair_evaluations,
            gram_rank, gram_condition,
            support_floor, unresolved_nodes,
            gram_scaled.supported_modes if gram_scaled is not None else None,
            gram_scaled.scaled_rank if gram_scaled is not None else None,
            gram_scaled.scaled_condition if gram_scaled is not None else None,
            tie_error,
            self.law.pressure_basis.version if self.augmented and self.law.pressure_basis is not None else None,
            self.law.source_node_ids if self.augmented and self.law.pressure_basis is not None else (),
        )
        if self.projected_work and not self.augmented:
            result = replace(result,
                contact_work_convention="projected_weak_gap_nonpotential_v1",
                regularization_storage_j=float(state.energy))
        return force, stiffness, result

    def set_normal_multipliers(self, values):
        if not self.augmented:
            raise ValueError("penalty patch has no normal multipliers")
        self.normal_multipliers = self.law._multipliers(values).copy()

    def has_unresolved_weak_open_gap(self, result, projected_multipliers):
        """Identify a sampled penetration that the pressure space cannot see.

        A conservative lower bound alone is insufficient: it can lie below
        the true minimum. Require an actual overlap sample beyond the gap
        budget, nonzero supported area, no active pressure, and an unchanged
        projected augmented update. No physical state is changed here.
        """

        if not self.augmented or type(result) is not _PatchResults:
            return False
        sampled = result.sampled_overlap_gap
        projected = np.asarray(projected_multipliers, dtype=float)
        return bool(
            sampled is not None
            and sampled < -self.gap_tolerance
            and not result.gap_tolerance_met
            and result.active_pressure_dofs == 0
            and any(area > 0.0 for area in result.reference_support_m2)
            and projected.shape == self.normal_multipliers.shape
            and np.array_equal(projected, self.normal_multipliers)
        )

    def restrict_tangent_to_reduced_variations(self, transform):
        """Keep selected Jet2 Hessian columns on reachable free variations."""
        if self.profile not in {SOURCE_Q4_AUGMENTED_PROFILE,
                                SOURCE_Q4_PROJECTED_AUGMENTED_PROFILE,
                                Q4_PAIR_AUGMENTED_PROFILE,
                                Q4_PAIR_PROJECTED_AUGMENTED_PROFILE,
                                REFINED_Q4_S3_AUGMENTED_PROFILE,
                                REFINED_Q4_S3_PROJECTED_AUGMENTED_PROFILE,
                                REFINED_Q4_S3_OVERLAP_LOCAL_AUGMENTED_PROFILE,
                                REFINED_Q4_S3_ROUNDOFF_AUGMENTED_PROFILE,
                                REFINED_Q4_S3_GRAPH_AUGMENTED_PROFILE,
                                REFINED_Q4_S3_PROJECTED_PENALTY_PROFILE,
                                S3_PROJECTED_PENALTY_PROFILE, S3_Q4_PROJECTED_PENALTY_PROFILE}:
            return
        variations = (self.map @ transform).tocsr()
        variations.eliminate_zeros()
        active = np.flatnonzero(np.diff(variations.indptr))
        self.law.set_tangent_active_coordinates(active)

    def projected_normal_multipliers(self, displacement):
        if not self.augmented:
            raise ValueError("penalty patch has no normal multipliers")
        source, target = self._positions(displacement)
        state = self.law.evaluate(source, target, self.normal_multipliers)
        projected = self.law.projected_multiplier(state, self.normal_multipliers)
        self.last_support_reset = None
        if self.settings.augmentation_support_resolution == "roundoff":
            ordinary = np.zeros_like(projected)
            positive = state.reference_support > 0.0
            ordinary[positive] = np.maximum(
                0.0, self.normal_multipliers[positive]
                - self.stiffness*state.normalized_gap[positive],
            )
            reset = np.flatnonzero(ordinary != projected)
            if len(reset):
                original_force = self.law.work(
                    source, target, ordinary, tangent=False,
                ).residual
                transferred_force = self.law.work(
                    source, target, projected, tangent=False,
                ).residual
                force_change = float(np.linalg.norm(
                    original_force-transferred_force,
                ))
                if force_change > self.settings.augmentation_support_force_budget_n:
                    raise SupportResetForceBudgetExceeded(
                        "roundoff multiplier reset exceeds local force budget"
                    )
                self.last_support_reset = {
                    "source_node_ids": [self.law.pressure_mode_ids[int(j)] for j in reset],
                    "local_force_change_n": force_change,
                    "force_budget_n": self.settings.augmentation_support_force_budget_n,
                }
        return projected

    def _swept_admissible(self, start, end):
        first = self._positions(start)
        last = self._positions(end)
        if self._gap_lower(first) < -self.gap_tolerance:
            raise ValueError("committed general S3 patch gap exceeds tolerance")
        try:
            last_lower = self._gap_lower(last)
        except ValueError:
            # A Newton proposal may leave the projection/geometry domain.
            # Reject it so the existing bounded path cutback can shorten it;
            # the committed endpoint above must still validate normally.
            return False
        if np.isnan(last_lower) or last_lower < -self.gap_tolerance:
            return False

        if self.settings.d1_interior_profile:
            # Certify material polarity on the original path as well. A
            # rounded child's positive orientation cannot repair ambiguity
            # in the true path near a reference-normal sign change.
            for side, indices, reference in (
                (0, self.law.source_face_indices, self.reference_normals[0]),
                (1, self.law.target_face_indices, self.reference_normals[1]),
            ):
                for face in indices:
                    for corner in range(len(face)):
                        bounds = _normal_controls_interval(
                            first[side][face], last[side][face], corner)
                        lower = _dot(bounds, _interval(reference))[0]
                        if not np.all(np.isfinite(lower)) or np.min(lower) <= 0.0:
                            return False

        # Certify union coverage on the original path, never rounded child
        # paths. Gap bounds may still subdivide with endpoint enclosures.
        if (self.settings.d1_interior_profile
                and not swept_projected_coverage_admissible(
                    first[0], last[0], first[1], last[1],
                    self.law.source_face_indices, self.law.target_face_indices)):
            return False

        def certify(left, right, depth, left_error=None, right_error=None):
            orientation_ok = True
            for side, indices, reference in (
                (0, self.law.source_face_indices, self.reference_normals[0]),
                (1, self.law.target_face_indices, self.reference_normals[1]),
            ):
                for face in indices:
                    corners = ((0, 1, 2),) if len(face) == 3 else (
                        (0, 1, 2), (1, 2, 3), (2, 3, 0), (3, 0, 1),
                    )
                    for triple in corners:
                        local = face[list(triple)]
                        if left_error is not None:
                            controls = _normal_controls_interval(
                                left[side][local], right[side][local],
                                start_error=left_error[side][local],
                                end_error=right_error[side][local])
                            lower = _dot(controls, _interval(reference))[0]
                            positive = (np.all(np.isfinite(lower))
                                        and np.min(lower) > 0.0)
                        else:
                            controls = _normal_controls(left[side][local], right[side][local])
                            positive = min(float(item@reference) for item in controls) > 0.0
                        if not positive:
                            orientation_ok = False
            if self.profile == S3_Q4_PROJECTED_PENALTY_PROFILE:
                from .s3_q4_swept import s3_q4_affine_lower
                gap_ok = all(s3_q4_affine_lower(
                    left[0][si], right[0][si], left[1][ti], right[1][ti],
                    endpoint_errors=(left_error[0][si], right_error[0][si],
                                     left_error[1][ti], right_error[1][ti])
                    if left_error is not None else None) >= -self.gap_tolerance
                    for si in self.law.source_face_indices for ti in self.law.target_face_indices)
            elif self.settings.q4_source_gap_certificate == "fixed_projection_graph":
                gap_ok = all(
                    fixed_projection_graph_swept_certificate(
                        left[0][si], right[0][si],
                        left[1][ti], right[1][ti],
                        self.gap_tolerance,
                    ).admissible
                    for si in self.law.source_face_indices
                    for ti in self.law.target_face_indices
                )
            elif self.settings.q4_source_gap_certificate == "overlap_local_dev":
                from .swept_patch_broadphase import conservative_swept_pair_indices
                geometry = self.law.geometry if self.projected_work else self.law
                target_count = len(self.law.target_face_indices)
                count = len(self.law.source_face_indices)*target_count
                candidates = None
                if geometry.pair_broadphase and count > 64:
                    try:
                        candidates = conservative_swept_pair_indices(
                            left[0], right[0], left[1], right[1],
                            self.law.source_face_indices, self.law.target_face_indices,
                            endpoint_errors=(left_error[0], right_error[0],
                                             left_error[1], right_error[1])
                            if left_error is not None else None)
                    except ValueError:
                        # Invalid proposed/subdivision geometry is a rejected
                        # path, never an empty candidate set. The committed
                        # endpoint and original global guards already ran.
                        return False
                pairs = range(count) if candidates is None else sorted(candidates)
                gap_ok = all(
                    overlap_local_swept_lower(
                        left[0][self.law.source_face_indices[index // target_count]],
                        right[0][self.law.source_face_indices[index // target_count]],
                        left[1][self.law.target_face_indices[index % target_count]],
                        right[1][self.law.target_face_indices[index % target_count]], 3,
                        endpoint_errors=(
                            left_error[0][self.law.source_face_indices[index // target_count]],
                            right_error[0][self.law.source_face_indices[index // target_count]],
                            left_error[1][self.law.target_face_indices[index % target_count]],
                            right_error[1][self.law.target_face_indices[index % target_count]])
                        if left_error is not None else None,
                    )[0] >= -self.gap_tolerance
                    for index in pairs
                )
            else:
                q4_swept_lower = (
                    q4_source_projected_swept_gap_lower
                    if self.settings.q4_source_gap_certificate == "projected_matching"
                    else q4_source_swept_gap_lower
                )
                gap_ok = all(
                    (q4_swept_lower(
                        left[0][si], right[0][si],
                        left[1][ti], right[1][ti], self.reference_normals[0],
                    ) if len(si) == 4 else
                     _swept_gap_lower(left[0][si], right[0][si],
                                      left[1][ti], right[1][ti])) >= -self.gap_tolerance
                    for si in self.law.source_face_indices
                    for ti in self.law.target_face_indices
                )
            if orientation_ok and gap_ok:
                return True
            if (self.settings.d1_interior_profile
                    and self.settings.q4_source_gap_certificate != "overlap_local_dev"):
                # Other development bounds do not yet enclose rounded
                # subdivision endpoints. Retry a shorter complete trial.
                return False
            if depth >= self.settings.maximum_swept_subdivisions:
                return False
            middle, middle_error = _affine_midpoint_with_error(
                left, right, left_error, right_error)
            try:
                if self._gap_lower(middle) < -self.gap_tolerance:
                    return False
            except ValueError:
                if self.profile == S3_Q4_PROJECTED_PENALTY_PROFILE:
                    return False
                raise
            return (certify(left, middle, depth+1, left_error, middle_error)
                    and certify(middle, right, depth+1, middle_error, right_error))

        # A rounded child endpoint represents the original affine path only
        # with its enclosure. This also applies to partial-overlap development
        # profiles, which do not require the D1 interior coverage guard.
        errors = (tuple(np.zeros_like(item) for item in first)
                  if (self.settings.d1_interior_profile
                      or self.settings.q4_source_gap_certificate == "overlap_local_dev"
                      or self.profile == S3_Q4_PROJECTED_PENALTY_PROFILE)
                  else None)
        return certify(first, last, 0, errors, errors)

    def swept_increment_admissible(self, start, end, _start_factor, _end_factor):
        admitted = self._swept_admissible(start, end)
        if not admitted:
            self.swept_trial_cutbacks += 1
        return admitted

    def admissible_step_fraction(self, start, end):
        first = np.asarray(start, dtype=float).reshape(-1)
        last = np.asarray(end, dtype=float).reshape(-1)
        if self._swept_admissible(first, last):
            return 1.0
        self.swept_trial_cutbacks += 1
        fraction = 0.5
        for _ in range(self.settings.maximum_swept_subdivisions):
            if self._swept_admissible(first, first+fraction*(last-first)):
                return fraction
            fraction *= 0.5
        return 0.0

    def restart_contract(self):
        interaction = self.definition.interactions[0]
        return {
            "profile": self.profile,
            "surfaces": [{"name": surface.name,
                          "element_ids": list(surface.element_ids),
                          "side": surface.side}
                         for surface in self.definition.surfaces],
            "interaction": {"name": interaction.name,
                            "surface": interaction.surface,
                            "target": interaction.target,
                            "normal_stiffness": self.stiffness,
                            "gap_tolerance": self.gap_tolerance,
                            "normal_law": interaction.normal_law},
            **({"projected_penalty_contract": {
                "revision": "finite_projected_weak_gap_v1",
                "multipliers": "identically_zero",
                "work": "projected_weak_gap_nonpotential_v1",
                "storage": "support_weighted_penalty_not_work",
            }} if self.projected_work and not self.augmented else {}),
            "settings": {"pair_motion": self.settings.pair_motion,
                         "normal_discretization": self.settings.normal_discretization,
                         **({"s3_q4_swept_certificate_revision":
                             "affine_all_projected_corners_outward_v1",
                             "s3_q4_value_resolution_revision":
                             "measured_bilinear_inverse_operand_v1"}
                            if self.profile == S3_Q4_PROJECTED_PENALTY_PROFILE else {}),
                         **({"partial_overlap_swept_certificate_revision":
                             "affine_outward_endpoint_enclosures_v1"}
                            if (not self.settings.d1_interior_profile
                                and self.settings.q4_source_gap_certificate == "overlap_local_dev")
                            else {}),
                         **({"d1_interior_profile": True,
                             "d1_normal_admission_revision": "model_and_path_constraints_v2",
                             "d1_swept_certificate_revision":
                             ("affine_union_outward_swept_search_v2"
                              if self.settings.q4_source_gap_certificate == "overlap_local_dev"
                              else "affine_union_outward_v1"),
                             "d1_interior_coverage_tolerance_m2":
                             self.settings.d1_interior_coverage_tolerance_m2,
                             "d1_interior_boundary_force_tolerance_n":
                             self.settings.d1_interior_boundary_force_tolerance_n}
                            if self.settings.d1_interior_profile else {}),
                         **({"enforcement_solver": self.settings.enforcement_solver}
                            if self.settings.enforcement_solver != "nested_augmented" else {}),
                         **({"complementarity_force_scale_n":
                             self.settings.complementarity_force_scale_n}
                            if self.settings.enforcement_solver == "monolithic_active_set" else {}),
                         **({"monolithic_maximum_pivots":
                             self.settings.monolithic_maximum_pivots}
                            if self.settings.enforcement_solver == "monolithic_active_set" else {}),
                         **({"monolithic_linear_solver":
                             self.settings.monolithic_linear_solver}
                            if self.settings.enforcement_solver == "monolithic_active_set" else {}),
                         **({"q4_source_pressure_basis": self.settings.q4_source_pressure_basis,
                             **({"q4_source_pressure_knot_columns": list(
                                 self.settings.q4_source_pressure_knot_columns)}
                                if self.settings.q4_source_pressure_basis == "selected_q1_knots_dev"
                                else {}),
                             "pressure_basis_version": self.law.pressure_basis.version,
                             "pressure_basis_fine_ids": list(self.law.pressure_basis.fine_source_node_ids),
                             "pressure_basis_mode_ids": list(self.law.pressure_basis.mode_ids),
                             "pressure_basis_matrix": [list(row) for row in self.law.pressure_basis.B]}
                            if self.augmented and self.law.pressure_basis is not None else {}),
                         **({"pressure_tolerance": self.settings.pressure_tolerance,
                             "maximum_augmentations": self.settings.maximum_augmentations}
                            if self.augmented else {}),
                         "general_s3_difference_step": self.settings.general_s3_difference_step,
                         **({"general_s3_differentiation": self.settings.general_s3_differentiation}
                            if self.settings.general_s3_differentiation != "existing" else {}),
                         "maximum_general_s3_energy_evaluations": self.settings.maximum_general_s3_energy_evaluations,
                         **({"q4_s3_shared_edge_tie_step_m": self.settings.q4_s3_shared_edge_tie_step_m,
                             "q4_s3_shared_edge_tie_direction": list(self.settings.q4_s3_shared_edge_tie_direction),
                             "q4_s3_shared_edge_tie_relative_tolerance": self.settings.q4_s3_shared_edge_tie_relative_tolerance}
                            if self.settings.q4_s3_shared_edge_tie_step_m is not None else {}),
                         "q4_target_weighted_gap_tolerance": self.settings.q4_target_weighted_gap_tolerance,
                         "maximum_q4_target_integration_triangles": self.settings.maximum_q4_target_integration_triangles,
                         "q4_source_area_tolerance": self.settings.q4_source_area_tolerance,
                         "q4_source_weighted_gap_tolerance": self.settings.q4_source_weighted_gap_tolerance,
                         "q4_source_support_gradient_tolerance": self.settings.q4_source_support_gradient_tolerance,
                         "q4_source_support_hessian_tolerance": self.settings.q4_source_support_hessian_tolerance,
                         "q4_source_weighted_gap_gradient_tolerance": self.settings.q4_source_weighted_gap_gradient_tolerance,
                         "q4_source_weighted_gap_hessian_tolerance": self.settings.q4_source_weighted_gap_hessian_tolerance,
                         "maximum_q4_source_integration_triangles": self.settings.maximum_q4_source_integration_triangles,
                         **({"q4_source_gap_certificate": self.settings.q4_source_gap_certificate}
                            if self.settings.q4_source_gap_certificate != "whole_face" else {}),
                         **({"augmentation_support_resolution": self.settings.augmentation_support_resolution,
                             "augmentation_support_force_budget_n": self.settings.augmentation_support_force_budget_n}
                            if self.settings.augmentation_support_resolution != "exact" else {}),
                         **({"augmentation_acceleration": self.settings.augmentation_acceleration,
                             "augmentation_pivot_max_pressure_pa": self.settings.augmentation_pivot_max_pressure_pa,
                             "augmentation_pivot_difference_step_m": self.settings.augmentation_pivot_difference_step_m,
                             **({"augmentation_equilibrated_pressure_step_pa":
                                 self.settings.augmentation_equilibrated_pressure_step_pa}
                                if self.settings.augmentation_equilibrated_pressure_step_pa is not None
                                else {})}
                            if self.settings.augmentation_acceleration == "active_secant_pivot" else {}),
                         **({"augmentation_acceleration": self.settings.augmentation_acceleration,
                             "augmentation_schur_maximum_modes": self.settings.augmentation_schur_maximum_modes,
                             "augmentation_schur_maximum_pressure_pa": self.settings.augmentation_schur_maximum_pressure_pa,
                             "augmentation_schur_maximum_step_pa": self.settings.augmentation_schur_maximum_step_pa,
                             "augmentation_schur_difference_step_m": self.settings.augmentation_schur_difference_step_m,
                             "augmentation_schur_maximum_attempts": self.settings.augmentation_schur_maximum_attempts,
                             "augmentation_schur_maximum_relinearizations": self.settings.augmentation_schur_maximum_relinearizations,
                             **({"augmentation_schur_nonlinear_backtrack_dev": True}
                                if self.settings.augmentation_schur_nonlinear_backtrack_dev
                                else {})}
                            if self.settings.augmentation_acceleration == "supported_schur_dev" else {}),
                         "maximum_swept_subdivisions": self.settings.maximum_swept_subdivisions,
                         "maximum_candidate_pairs": self.settings.maximum_candidate_pairs},
        }
