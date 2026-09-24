"""Global primal-pressure state for moving planar shell patch pairs.

This internal kernel aggregates all geometric face overlaps onto one stable
integration-side nodal pressure space. It owns no structural solver state.
Its moving-boundary translation derivative supports the restricted static
patch profile; face-boundary transition derivatives remain outside it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .moving import (
    _moving_pair_integrals,
    _moving_pair_transport,
    certify_moving_mortar_gap,
)
from .overlap import PlanarFace, planar_projected_overlap


@dataclass(frozen=True)
class PatchFace:
    geometry: PlanarFace
    node_ids: tuple[int, ...]

    def __post_init__(self) -> None:
        if any(not isinstance(node, (int, np.integer)) for node in self.node_ids):
            raise ValueError("patch node identities must be integers")
        ids = tuple(int(node) for node in self.node_ids)
        if len(ids) != len(self.geometry.corners) or len(set(ids)) != len(ids):
            raise ValueError("patch face needs one distinct node ID per corner")
        object.__setattr__(self, "node_ids", ids)


@dataclass(frozen=True)
class MovingPatchMortarState:
    overlap_area: float
    overlapping_pairs: int
    candidate_pairs: int
    source_node_ids: tuple[int, ...]
    target_node_ids: tuple[int, ...]
    support: np.ndarray
    weighted_gap: np.ndarray
    normalized_gap: np.ndarray
    gap_gradient: np.ndarray
    energy: float
    normal_residual: np.ndarray
    normal_tangent: np.ndarray
    minimum_vertex_gap: float
    pressure_rank: int


@dataclass(frozen=True)
class MovingPatchGapCertificate:
    minimum_sampled_gap: float
    conservative_lower_gap: float
    tolerance_met: bool
    overlap_pairs_checked: int
    triangles_checked: int
    resource_exhausted: bool = False
    methods: tuple[str, ...] = ()


@dataclass(frozen=True)
class MovingPatchReducedSystem:
    state: MovingPatchMortarState
    residual: np.ndarray
    tangent: np.ndarray
    relative_tangent_asymmetry: float


class MovingPatchMortar:
    """Integrate all pairs while retaining one nodal pressure space."""

    def __init__(self, source_faces: tuple[PatchFace, ...],
                 target_faces: tuple[PatchFace, ...], normal: np.ndarray,
                 stiffness: float, *, maximum_candidate_pairs: int = 100_000,
                 maximum_normal_dofs: int = 256):
        self.source_faces = tuple(source_faces)
        self.target_faces = tuple(target_faces)
        if not self.source_faces or not self.target_faces:
            raise ValueError("patch mortar needs two nonempty surfaces")
        if (type(maximum_candidate_pairs) is not int
                or maximum_candidate_pairs < 1):
            raise ValueError("maximum_candidate_pairs must be a positive integer")
        self.candidate_pairs = len(self.source_faces) * len(self.target_faces)
        if self.candidate_pairs > maximum_candidate_pairs:
            raise MemoryError("contact candidate limit exceeded; no pair was discarded")
        intra_pairs = sum(len(faces) * (len(faces) - 1) // 2
                          for faces in (self.source_faces, self.target_faces))
        if intra_pairs > maximum_candidate_pairs:
            raise MemoryError("patch topology validation pair limit exceeded")
        direction = np.asarray(normal, dtype=float)
        if direction.shape != (3,) or not np.all(np.isfinite(direction)):
            raise ValueError("contact normal must be a finite 3-vector")
        length = float(np.linalg.norm(direction))
        if length <= 0.0:
            raise ValueError("contact normal must be nonzero")
        self.normal = direction / length
        self.stiffness = float(stiffness)
        if not np.isfinite(self.stiffness) or self.stiffness <= 0.0:
            raise ValueError("normal stiffness must be finite and positive")
        self.source_node_ids = tuple(sorted({node for face in self.source_faces
                                              for node in face.node_ids}))
        self.target_node_ids = tuple(sorted({node for face in self.target_faces
                                              for node in face.node_ids}))
        if type(maximum_normal_dofs) is not int or maximum_normal_dofs < 1:
            raise ValueError("maximum_normal_dofs must be a positive integer")
        if len(self.source_node_ids) + len(self.target_node_ids) > maximum_normal_dofs:
            raise MemoryError("dense patch normal-DOF limit exceeded; no contact was dropped")
        if set(self.source_node_ids) & set(self.target_node_ids):
            raise ValueError("paired patch surfaces must have disjoint material nodes")
        self.source_index = {node: index for index, node in
                             enumerate(self.source_node_ids)}
        self.target_index = {node: index for index, node in
                             enumerate(self.target_node_ids)}
        self._validate_reference_geometry()

    def _validate_reference_geometry(self) -> None:
        all_faces = (*self.source_faces, *self.target_faces)
        scale = max(float(np.max(np.linalg.norm(
            face.geometry.corners - face.geometry.corners[0], axis=1
        ))) for face in all_faces)
        for name, faces in (("source", self.source_faces),
                            ("target", self.target_faces)):
            origin = faces[0].geometry.corners[0]
            positions: dict[int, np.ndarray] = {}
            for face in faces:
                geometry = face.geometry
                face_normal = np.cross(geometry.corners[1] - geometry.corners[0],
                                       geometry.corners[-1] - geometry.corners[0])
                face_normal /= np.linalg.norm(face_normal)
                if abs(float(face_normal @ self.normal)) < 1.0 - 1.0e-10:
                    raise ValueError(f"{name} face must be parallel to contact plane")
                if float(np.max(np.abs((geometry.corners - origin) @ self.normal))) > 1.0e-10 * scale:
                    raise ValueError(f"{name} patch faces must occupy one physical plane")
                for node, corner in zip(face.node_ids, geometry.corners):
                    prior = positions.setdefault(node, corner)
                    if float(np.linalg.norm(prior - corner)) > 1.0e-10 * scale:
                        raise ValueError(f"{name} node {node} has inconsistent physical corners")
            for index, first in enumerate(faces):
                for second in faces[index + 1:]:
                    if planar_projected_overlap(first.geometry, second.geometry) is not None:
                        raise ValueError(f"{name} patch faces overlap each other")

    def _fields(self, source_translation: np.ndarray,
                target_translation: np.ndarray,
                source_normal_dofs: np.ndarray,
                target_normal_dofs: np.ndarray):
        translations = (np.asarray(source_translation, dtype=float),
                        np.asarray(target_translation, dtype=float))
        heights = (np.asarray(source_normal_dofs, dtype=float),
                   np.asarray(target_normal_dofs, dtype=float))
        if (any(value.shape != (3,) or not np.all(np.isfinite(value))
                for value in translations)
                or heights[0].shape != (len(self.source_node_ids),)
                or heights[1].shape != (len(self.target_node_ids),)
                or not all(np.all(np.isfinite(value)) for value in heights)):
            raise ValueError("patch mortar fields have invalid size or nonfinite values")
        moved = tuple(
            tuple(PlanarFace(face.geometry.feature_id,
                             face.geometry.corners + translation)
                  for face in faces)
            for faces, translation in zip(
                (self.source_faces, self.target_faces), translations
            )
        )
        return moved, heights

    def evaluate(self, source_translation: np.ndarray,
                 target_translation: np.ndarray,
                 source_normal_dofs: np.ndarray,
                 target_normal_dofs: np.ndarray) -> MovingPatchMortarState:
        moved, heights = self._fields(
            source_translation, target_translation,
            source_normal_dofs, target_normal_dofs,
        )
        source_count = len(self.source_node_ids)
        target_count = len(self.target_node_ids)
        support = np.zeros(source_count)
        weighted_gap = np.zeros(source_count)
        gradient = np.zeros((source_count, source_count + target_count))
        overlap_area = 0.0
        minimum_vertex_gap = float("inf")
        overlapping_pairs = 0
        for face_a, moved_a in zip(self.source_faces, moved[0]):
            rows = np.asarray([self.source_index[node] for node in face_a.node_ids])
            for face_b, moved_b in zip(self.target_faces, moved[1]):
                target_columns = np.asarray([
                    source_count + self.target_index[node]
                    for node in face_b.node_ids
                ])
                local = _moving_pair_integrals(
                    moved_a, moved_b, self.normal,
                    heights[0][rows], heights[1][target_columns - source_count],
                )
                if local.overlap_area <= 0.0:
                    continue
                overlapping_pairs += 1
                overlap_area += local.overlap_area
                minimum_vertex_gap = min(minimum_vertex_gap,
                                         local.minimum_vertex_gap)
                support[rows] += local.support
                weighted_gap[rows] += local.weighted_gap
                columns = np.r_[rows, target_columns]
                gradient[np.ix_(rows, columns)] += local.gap_gradient
        active_support = support > 0.0
        scale = max(float(np.max(np.linalg.norm(
            face.geometry.corners - face.geometry.corners[0], axis=1
        ))) for face in (*self.source_faces, *self.target_faces))
        roundoff = 256.0 * np.finfo(float).eps * scale
        weighted_gap[np.abs(weighted_gap) <= roundoff * support] = 0.0
        normalized = np.zeros(source_count)
        normalized[active_support] = weighted_gap[active_support] / support[active_support]
        active_gap = np.minimum(normalized, 0.0)
        closed = active_support & (normalized <= 0.0)
        energy = 0.5 * self.stiffness * float(support @ (active_gap * active_gap))
        residual = gradient.T @ (self.stiffness * active_gap)
        tangent = np.zeros((source_count + target_count, source_count + target_count))
        if np.any(closed):
            tangent = (self.stiffness * gradient[closed].T
                       @ np.diag(1.0 / support[closed]) @ gradient[closed])
        if np.any(active_support):
            singular = np.linalg.svd(gradient[active_support], compute_uv=False)
            pressure_rank = int(np.count_nonzero(
                singular > singular[0] * 1.0e-10
            ))
        else:
            pressure_rank = 0
        return MovingPatchMortarState(
            overlap_area, overlapping_pairs, self.candidate_pairs,
            self.source_node_ids, self.target_node_ids,
            support, weighted_gap, normalized, gradient, energy,
            residual, tangent, minimum_vertex_gap, pressure_rank,
        )

    def certify_gap(self, source_translation: np.ndarray,
                    target_translation: np.ndarray,
                    source_normal_dofs: np.ndarray,
                    target_normal_dofs: np.ndarray,
                    *, gap_tolerance: float,
                    maximum_triangles_per_pair: int,
                    maximum_total_triangles: int | None = None,
                    ) -> MovingPatchGapCertificate:
        if type(maximum_triangles_per_pair) is not int or maximum_triangles_per_pair < 1:
            raise ValueError("maximum_triangles_per_pair must be a positive integer")
        if maximum_total_triangles is None:
            maximum_total_triangles = maximum_triangles_per_pair
        if type(maximum_total_triangles) is not int or maximum_total_triangles < 1:
            raise ValueError("maximum_total_triangles must be a positive integer")
        moved, heights = self._fields(
            source_translation, target_translation,
            source_normal_dofs, target_normal_dofs,
        )
        minimum_sampled = float("inf")
        conservative_lower = float("inf")
        tolerance_met = True
        overlap_pairs = 0
        triangles = 0
        methods: set[str] = set()
        for face_a, moved_a in zip(self.source_faces, moved[0]):
            rows = np.asarray([self.source_index[node] for node in face_a.node_ids])
            for face_b, moved_b in zip(self.target_faces, moved[1]):
                columns = np.asarray([self.target_index[node]
                                      for node in face_b.node_ids])
                certificate = certify_moving_mortar_gap(
                    moved_a, moved_b, self.normal,
                    np.zeros(3), np.zeros(3),
                    heights[0][rows], heights[1][columns],
                    gap_tolerance=gap_tolerance,
                    maximum_triangles=max(
                        1, min(maximum_triangles_per_pair,
                               maximum_total_triangles - triangles),
                    ),
                )
                if certificate.method == "empty":
                    continue
                methods.add(certificate.method)
                overlap_pairs += 1
                triangles += certificate.triangles_checked
                if triangles > maximum_total_triangles:
                    return MovingPatchGapCertificate(
                        minimum_sampled, float("-inf"), False,
                        overlap_pairs, triangles, True, tuple(sorted(methods)),
                    )
                minimum_sampled = min(minimum_sampled,
                                      certificate.minimum_sampled_gap)
                conservative_lower = min(conservative_lower,
                                         certificate.conservative_lower_gap)
                tolerance_met = tolerance_met and certificate.tolerance_met
                if certificate.conservative_lower_gap == float("-inf"):
                    return MovingPatchGapCertificate(
                        minimum_sampled, float("-inf"), False,
                        overlap_pairs, triangles, True, tuple(sorted(methods)),
                    )
        return MovingPatchGapCertificate(
            minimum_sampled, conservative_lower,
            tolerance_met, overlap_pairs, triangles, False,
            tuple(sorted(methods)),
        )

    def translation_residual(self, source_translation: np.ndarray,
                             target_translation: np.ndarray,
                             source_normal_dofs: np.ndarray,
                             target_normal_dofs: np.ndarray,
                             ) -> tuple[np.ndarray, np.ndarray]:
        """Differentiate the globally normalized pressure potential."""

        state = self.evaluate(
            source_translation, target_translation,
            source_normal_dofs, target_normal_dofs,
        )
        if state.overlap_area == 0.0:
            return np.zeros(3), np.zeros(3)
        moved, heights = self._fields(
            source_translation, target_translation,
            source_normal_dofs, target_normal_dofs,
        )
        count = len(self.source_node_ids)
        dm_a = np.zeros((count, 3))
        dm_b = np.zeros((count, 3))
        dW_a = np.zeros((count, 3))
        dW_b = np.zeros((count, 3))
        for face_a, moved_a in zip(self.source_faces, moved[0]):
            rows = np.asarray([self.source_index[node] for node in face_a.node_ids])
            for face_b, moved_b in zip(self.target_faces, moved[1]):
                columns = np.asarray([self.target_index[node]
                                      for node in face_b.node_ids])
                transport = _moving_pair_transport(
                    moved_a, moved_b, self.normal,
                    heights[0][rows], heights[1][columns],
                )
                dm_a[rows] += transport.source_support_derivative
                dm_b[rows] += transport.target_support_derivative
                dW_a[rows] += transport.source_weighted_gap_derivative
                dW_b[rows] += transport.target_weighted_gap_derivative
        closed = (state.support > 0.0) & (state.normalized_gap < 0.0)
        pressure = self.stiffness * state.normalized_gap[closed]
        source_tangent = np.sum(
            pressure[:, None] * dW_a[closed]
            - 0.5 * self.stiffness * state.normalized_gap[closed, None] ** 2
            * dm_a[closed], axis=0,
        )
        target_tangent = np.sum(
            pressure[:, None] * dW_b[closed]
            - 0.5 * self.stiffness * state.normalized_gap[closed, None] ** 2
            * dm_b[closed], axis=0,
        )
        source_normal = float(np.sum(state.normal_residual[:count])) * self.normal
        target_normal = float(np.sum(state.normal_residual[count:])) * self.normal
        return source_tangent + source_normal, target_tangent + target_normal

    def reduced_system(self, source_translation: np.ndarray,
                       target_translation: np.ndarray,
                       source_normal_dofs: np.ndarray,
                       target_normal_dofs: np.ndarray,
                       *, difference_step: float) -> MovingPatchReducedSystem:
        """Differentiate the global-pressure residual on a smooth branch."""

        step = float(difference_step)
        if not np.isfinite(step) or step <= 0.0:
            raise ValueError("difference_step must be finite and positive")
        source = np.asarray(source_translation, dtype=float).reshape(3)
        target = np.asarray(target_translation, dtype=float).reshape(3)
        heights_a = np.asarray(source_normal_dofs, dtype=float).reshape(-1)
        heights_b = np.asarray(target_normal_dofs, dtype=float).reshape(-1)
        values = np.r_[source, target, heights_a, heights_b]
        split = 6 + len(heights_a)

        def evaluate_at(current: np.ndarray):
            translation_a, translation_b = current[:3], current[3:6]
            height_a, height_b = current[6:split], current[split:]
            state = self.evaluate(
                translation_a, translation_b, height_a, height_b,
            )
            force_a, force_b = self.translation_residual(
                translation_a, translation_b, height_a, height_b,
            )
            return state, np.r_[force_a, force_b, state.normal_residual]

        state, residual = evaluate_at(values)
        active = (state.support > 0.0) & (state.normalized_gap <= 0.0)
        tangent = np.zeros((len(values), len(values)))
        for column in range(len(values)):
            delta = np.zeros_like(values)
            delta[column] = step
            plus_state, plus_residual = evaluate_at(values + delta)
            minus_state, minus_residual = evaluate_at(values - delta)
            plus_active = ((plus_state.support > 0.0)
                           & (plus_state.normalized_gap <= 0.0))
            minus_active = ((minus_state.support > 0.0)
                            & (minus_state.normalized_gap <= 0.0))
            plus_matches = np.array_equal(plus_active, active)
            minus_matches = np.array_equal(minus_active, active)
            if plus_matches and minus_matches:
                tangent[:, column] = (plus_residual - minus_residual) / (2.0 * step)
            elif plus_matches:
                tangent[:, column] = (plus_residual - residual) / step
            elif minus_matches:
                tangent[:, column] = (residual - minus_residual) / step
            else:
                # Several pressure modes can touch zero together.  The
                # positive chart direction then defines a valid one-sided
                # generalized column even though neither perturbed active
                # set equals the current convention at every mode.
                tangent[:, column] = (plus_residual - residual) / step
        scale = max(np.finfo(float).tiny, float(np.linalg.norm(tangent)))
        asymmetry = float(np.linalg.norm(tangent - tangent.T) / scale)
        return MovingPatchReducedSystem(state, residual, tangent, asymmetry)
