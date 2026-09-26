"""Bounded general-nodal S3 patch mortar development static owner."""

from __future__ import annotations

from dataclasses import dataclass

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
from .fixed_projection_graph import fixed_projection_graph_swept_certificate
from .pressure_space import supported_pressure_gram


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
REFINED_Q4_S3_ROUNDOFF_AUGMENTED_PROFILE = "Q4_S3_PATCH_REFINED_NODAL_PRIMAL_MORTAR_ROUNDOFF_AUGMENTED_STATIC_DEV_V2"
REFINED_Q4_S3_GRAPH_AUGMENTED_PROFILE = "Q4_S3_PATCH_REFINED_FIXED_PROJECTION_GRAPH_AUGMENTED_STATIC_DEV_V0"


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
    if (interaction.normal_law not in {"penalty", "augmented"}
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
    refined_s3 = (augmented and not source_q4 and not target_q4
                  and len(source.element_ids) >= 2
                  and len(target.element_ids) >= 1
                  and (len(source.element_ids) > 2 or len(target.element_ids) > 2))
    refined_q4 = (augmented and len(source.element_ids) >= 2
                  and len(source_q4) == len(source.element_ids)
                  and not target_q4 and len(target.element_ids) >= 1)
    refined = refined_s3 or refined_q4
    if (settings.general_s3_differentiation == "jet2_s3_dev"
            and not (augmented and not source_q4 and not target_q4
                     and len(source.element_ids)+len(target.element_ids) >= 3)):
        issues.append("Jet2 S3 development derivative needs an augmented S3/S3 patch of at least three faces")
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
    if augmented:
        profile = (REFINED_Q4_S3_GRAPH_AUGMENTED_PROFILE
                   if refined_q4 and settings.q4_source_gap_certificate == "fixed_projection_graph" else
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
    if (settings.q4_source_gap_certificate == "projected_matching"
            and not (augmented and (q4_pair or source_q4))):
        issues.append("projected-matching Q4 gap certificate requires augmented Q4/Q4 or Q4/two-S3")
    if refined_q4 and settings.q4_source_gap_certificate == "projected_matching":
        issues.append("refined Q4/S3 patch has no projected-matching gap profile")
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
            differentiation=("jet2_s3"
                             if settings.general_s3_differentiation == "jet2_s3_dev"
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

    def to_dict(self):
        result = dict(vars(self))
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
        return result


class GeneralS3PatchManager:
    def __init__(self, model, definition: ContactDefinition,
                 settings: ContactSolverSettings | None = None,
                 initial_displacement: np.ndarray | None = None):
        self.settings = ContactSolverSettings() if settings is None else settings
        report = validate_general_s3_patch(model, definition, self.settings)
        if not report.valid:
            raise ValueError("unsupported general S3 patch: " + "; ".join(report.issues))
        self.definition = definition
        self.profile = report.profile
        source, target, interaction = _selected(definition)
        adapters = _adapters(model, (source, target))
        faces = _patch_faces(adapters)
        self.stiffness = interaction.normal_stiffness
        self.augmented = interaction.normal_law == "augmented"
        self.gap_tolerance = interaction.gap_tolerance
        self.swept_trial_cutbacks = 0
        self.law = MovingS3PatchPrimalMortarPenalty(
            faces[0], faces[1], self.stiffness,
            difference_step=self.settings.general_s3_difference_step,
            maximum_energy_evaluations=self.settings.maximum_general_s3_energy_evaluations,
            q4_weighted_gap_tolerance=self.settings.q4_target_weighted_gap_tolerance,
            maximum_q4_integration_triangles=self.settings.maximum_q4_target_integration_triangles,
            q4_source_area_tolerance=self.settings.q4_source_area_tolerance,
            q4_source_weighted_gap_tolerance=self.settings.q4_source_weighted_gap_tolerance,
            maximum_q4_source_integration_triangles=self.settings.maximum_q4_source_integration_triangles,
            differentiation="jet2_s3" if self.settings.general_s3_differentiation == "jet2_s3_dev" else "pair_local" if self.profile in {
                REFINED_AUGMENTED_PROFILE, REFINED_Q4_S3_AUGMENTED_PROFILE,
                REFINED_Q4_S3_ROUNDOFF_AUGMENTED_PROFILE,
                REFINED_Q4_S3_GRAPH_AUGMENTED_PROFILE,
            }
            else "global",
            maximum_candidate_pairs=self.settings.maximum_candidate_pairs,
        )
        if self.augmented:
            from .s3_patch_augmented import MovingS3PatchProjectedNormal

            self.law = MovingS3PatchProjectedNormal(
                self.law,
                support_resolution=self.settings.augmentation_support_resolution,
            )
            self.normal_multipliers = np.zeros(len(self.law.source_node_ids))
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

    def _gap_lower(self, positions):
        source, target = positions
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
        lower = self._gap_lower((source, target))
        state = (self.law.evaluate(source, target, self.normal_multipliers)
                 if self.augmented else self.law.evaluate(source, target))
        local_derivatives = (self.augmented
                             and self.law.geometry.differentiation
                             in {"pair_local", "jet2_s3"})
        pair_evaluations = len(self.law.geometry.pair_laws) if local_derivatives else 0
        if state.active_pressure_dofs == 0:
            local_force = np.zeros(self.law.n_coordinates)
            local_tangent = (sparse.csr_matrix((self.law.n_coordinates, self.law.n_coordinates))
                             if tangent else None)
            evaluations = pair_evaluations if local_derivatives else 1
        else:
            work = (self.law.work(source, target, self.normal_multipliers, tangent=tangent)
                    if self.augmented else self.law.work(source, target, tangent=tangent))
            local_force = work.residual
            local_tangent = sparse.csr_matrix(work.tangent) if tangent else None
            evaluations = work.energy_evaluations
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
                            REFINED_Q4_S3_ROUNDOFF_AUGMENTED_PROFILE,
                            REFINED_Q4_S3_GRAPH_AUGMENTED_PROFILE}:
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
                    self.law.source_node_ids, state.reference_support, supported)
                if area > 0.0 and not active
            )
        result = _PatchResults(
            self.profile, lower, state.minimum_physical_gap,
            0.0 if self.augmented else state.energy,
            state.overlap_area, state.reference_overlap_area,
            state.overlapping_pairs,
            tuple(map(float, source_force)), tuple(map(float, target_force)),
            tuple(map(float, source_moment)), tuple(map(float, target_moment)),
            lower >= -self.gap_tolerance, state.active_pressure_dofs,
            self.law.source_node_ids,
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
        )
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
        """Keep Q4-source Hessian work on axes reached by free coordinates."""
        if self.profile not in {SOURCE_Q4_AUGMENTED_PROFILE,
                                SOURCE_Q4_PROJECTED_AUGMENTED_PROFILE,
                                Q4_PAIR_AUGMENTED_PROFILE,
                                Q4_PAIR_PROJECTED_AUGMENTED_PROFILE,
                                REFINED_Q4_S3_AUGMENTED_PROFILE,
                                REFINED_Q4_S3_ROUNDOFF_AUGMENTED_PROFILE,
                                REFINED_Q4_S3_GRAPH_AUGMENTED_PROFILE}:
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
                    "source_node_ids": [self.law.source_node_ids[int(j)] for j in reset],
                    "local_force_change_n": force_change,
                    "force_budget_n": self.settings.augmentation_support_force_budget_n,
                }
        return projected

    def _swept_admissible(self, start, end):
        first = self._positions(start)
        last = self._positions(end)
        if self._gap_lower(first) < -self.gap_tolerance:
            raise ValueError("committed general S3 patch gap exceeds tolerance")
        if self._gap_lower(last) < -self.gap_tolerance:
            return False

        def certify(left, right, depth):
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
                        controls = _normal_controls(left[side][local], right[side][local])
                        if min(float(item@reference) for item in controls) <= 0.0:
                            orientation_ok = False
            if self.settings.q4_source_gap_certificate == "fixed_projection_graph":
                gap_ok = all(
                    fixed_projection_graph_swept_certificate(
                        left[0][si], right[0][si],
                        left[1][ti], right[1][ti],
                        self.gap_tolerance,
                    ).admissible
                    for si in self.law.source_face_indices
                    for ti in self.law.target_face_indices
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
            if depth >= self.settings.maximum_swept_subdivisions:
                return False
            middle = tuple(0.5*(a+b) for a, b in zip(left, right))
            if self._gap_lower(middle) < -self.gap_tolerance:
                return False
            return certify(left, middle, depth+1) and certify(middle, right, depth+1)

        return certify(first, last, 0)

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
            "settings": {"pair_motion": self.settings.pair_motion,
                         "normal_discretization": self.settings.normal_discretization,
                         **({"pressure_tolerance": self.settings.pressure_tolerance,
                             "maximum_augmentations": self.settings.maximum_augmentations}
                            if self.augmented else {}),
                         "general_s3_difference_step": self.settings.general_s3_difference_step,
                         **({"general_s3_differentiation": self.settings.general_s3_differentiation}
                            if self.settings.general_s3_differentiation != "existing" else {}),
                         "maximum_general_s3_energy_evaluations": self.settings.maximum_general_s3_energy_evaluations,
                         "q4_target_weighted_gap_tolerance": self.settings.q4_target_weighted_gap_tolerance,
                         "maximum_q4_target_integration_triangles": self.settings.maximum_q4_target_integration_triangles,
                         "q4_source_area_tolerance": self.settings.q4_source_area_tolerance,
                         "q4_source_weighted_gap_tolerance": self.settings.q4_source_weighted_gap_tolerance,
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
                             "augmentation_schur_difference_step_m": self.settings.augmentation_schur_difference_step_m}
                            if self.settings.augmentation_acceleration == "supported_schur_dev" else {}),
                         "maximum_swept_subdivisions": self.settings.maximum_swept_subdivisions,
                         "maximum_candidate_pairs": self.settings.maximum_candidate_pairs},
        }
