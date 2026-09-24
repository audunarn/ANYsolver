"""Translation-space control for moving planar mortar overlap.

This kernel is an internal, restricted derivative control. Each selected
physical patch translates rigidly without rotation or deformation. Its scalar
gap is therefore constant on every overlap polygon, so the nonnegative P1/Q1
primal mortar penalty potential reduces exactly to overlap area times the
scalar normal penalty energy. The result is not the deformable-shell force
map needed for C1 admission.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .overlap import (
    PlanarFace,
    planar_overlap_translation_derivatives,
    planar_projected_overlap,
)


@dataclass(frozen=True)
class TranslatedPairResult:
    overlap_area: float
    gap: float
    energy: float
    source_residual: np.ndarray
    target_residual: np.ndarray
    relative_tangent: np.ndarray

    @property
    def tangent(self) -> np.ndarray:
        block = self.relative_tangent
        return np.block([[block, -block], [-block, block]])


class TranslatedPairMortar:
    """Exact smooth-branch penalty derivatives for two translating patches."""

    def __init__(self, source_faces: tuple[PlanarFace, ...],
                 target_faces: tuple[PlanarFace, ...], normal: np.ndarray,
                 stiffness: float, *, maximum_candidate_pairs: int = 100_000):
        self.source_faces = tuple(source_faces)
        self.target_faces = tuple(target_faces)
        if not self.source_faces or not self.target_faces:
            raise ValueError("translated pair needs two nonempty face patches")
        if (len(self.source_faces) * len(self.target_faces)
                > maximum_candidate_pairs):
            raise MemoryError("contact candidate limit exceeded; no pair was discarded")
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
        for name, faces in (("source", self.source_faces),
                            ("target", self.target_faces)):
            first = float(faces[0].corners[0] @ self.normal)
            scale = max(float(np.max(np.linalg.norm(face.corners - face.corners[0], axis=1)))
                        for face in faces)
            if max(float(np.max(np.abs(face.corners @ self.normal - first)))
                   for face in faces) > 1.0e-10 * scale:
                raise ValueError(f"translated {name} patch must occupy one plane")
        self.reference_gap = float(
            (self.source_faces[0].corners[0] - self.target_faces[0].corners[0])
            @ self.normal
        )

    def evaluate(self, source_translation: np.ndarray,
                 target_translation: np.ndarray) -> TranslatedPairResult:
        source = np.asarray(source_translation, dtype=float)
        target = np.asarray(target_translation, dtype=float)
        if (source.shape != (3,) or target.shape != (3,)
                or not np.all(np.isfinite(source))
                or not np.all(np.isfinite(target))):
            raise ValueError("pair translations must be finite 3-vectors")
        area = 0.0
        area_gradient = np.zeros(3, dtype=float)
        area_hessian = np.zeros((3, 3), dtype=float)
        for source_face in self.source_faces:
            moved_source = PlanarFace(source_face.feature_id,
                                      source_face.corners + source)
            for target_face in self.target_faces:
                moved_target = PlanarFace(target_face.feature_id,
                                          target_face.corners + target)
                overlap = planar_projected_overlap(moved_source, moved_target)
                if overlap is None:
                    continue
                area += overlap.area
                gradient, hessian = planar_overlap_translation_derivatives(
                    moved_source, moved_target
                )
                area_gradient += gradient
                area_hessian += hessian
        gap = self.reference_gap + float((source - target) @ self.normal)
        compression_gap = min(gap, 0.0)
        energy = 0.5 * self.stiffness * area * compression_gap ** 2
        relative_residual = self.stiffness * (
            0.5 * compression_gap ** 2 * area_gradient
            + area * compression_gap * self.normal
        )
        relative_tangent = np.zeros((3, 3), dtype=float)
        if gap <= 0.0 and area > 0.0:
            relative_tangent = self.stiffness * (
                0.5 * compression_gap ** 2 * area_hessian
                + compression_gap * (
                    np.outer(area_gradient, self.normal)
                    + np.outer(self.normal, area_gradient)
                )
                + area * np.outer(self.normal, self.normal)
            )
        return TranslatedPairResult(
            area, gap, energy, relative_residual, -relative_residual,
            relative_tangent,
        )


@dataclass(frozen=True)
class MovingMortarState:
    overlap_area: float
    support: np.ndarray
    weighted_gap: np.ndarray
    normalized_gap: np.ndarray
    energy: float
    normal_residual: np.ndarray
    normal_tangent: np.ndarray
    minimum_vertex_gap: float


def moving_mortar_state(source_face: PlanarFace, target_face: PlanarFace,
                        normal: np.ndarray, stiffness: float,
                        source_translation: np.ndarray,
                        target_translation: np.ndarray,
                        source_normal_dofs: np.ndarray,
                        target_normal_dofs: np.ndarray) -> MovingMortarState:
    """Integrate a moving P1/Q1 primal mortar gap on two planar projections.

    The normal fields may vary nodally while the projected outlines translate
    without in-plane distortion. The returned normal residual and tangent are
    derivatives of this discrete pressure-space potential at fixed tangential
    translations. Translation derivatives are a separate pending force map.
    """

    direction = np.asarray(normal, dtype=float)
    if direction.shape != (3,) or not np.all(np.isfinite(direction)):
        raise ValueError("contact normal must be a finite 3-vector")
    length = float(np.linalg.norm(direction))
    if length <= 0.0:
        raise ValueError("contact normal must be nonzero")
    direction = direction / length
    for name, face in (("source", source_face), ("target", target_face)):
        face_normal = np.cross(face.corners[1] - face.corners[0],
                               face.corners[-1] - face.corners[0])
        face_normal /= np.linalg.norm(face_normal)
        if abs(float(face_normal @ direction)) < 1.0 - 1.0e-10:
            raise ValueError(f"moving mortar {name} face must be parallel to the contact plane")
    penalty = float(stiffness)
    if not np.isfinite(penalty) or penalty <= 0.0:
        raise ValueError("normal stiffness must be finite and positive")
    translation_a = np.asarray(source_translation, dtype=float)
    translation_b = np.asarray(target_translation, dtype=float)
    height_a = np.asarray(source_normal_dofs, dtype=float)
    height_b = np.asarray(target_normal_dofs, dtype=float)
    if (translation_a.shape != (3,) or translation_b.shape != (3,)
            or height_a.shape != (len(source_face.corners),)
            or height_b.shape != (len(target_face.corners),)
            or not all(np.all(np.isfinite(item)) for item in
                       (translation_a, translation_b, height_a, height_b))):
        raise ValueError("moving mortar fields have invalid size or nonfinite values")
    moved_a = PlanarFace(source_face.feature_id,
                         source_face.corners + translation_a)
    moved_b = PlanarFace(target_face.feature_id,
                         target_face.corners + translation_b)
    overlap = planar_projected_overlap(moved_a, moved_b)
    rows = len(source_face.corners)
    columns = rows + len(target_face.corners)
    support = np.zeros(rows, dtype=float)
    weighted_gap = np.zeros(rows, dtype=float)
    gradient = np.zeros((rows, columns), dtype=float)
    if overlap is None:
        return MovingMortarState(
            0.0, support, weighted_gap, support.copy(), 0.0,
            np.zeros(columns), np.zeros((columns, columns)), float("inf"),
        )
    polygon = overlap.polygon
    centroid = np.mean(polygon, axis=0)
    for index, corner in enumerate(polygon):
        following = polygon[(index + 1) % len(polygon)]
        area = 0.5 * float(np.linalg.norm(
            np.cross(corner - centroid, following - centroid)
        ))
        if area <= 0.0:
            continue
        triangle = (centroid, corner, following)
        for bary in ((2.0/3.0, 1.0/6.0, 1.0/6.0),
                     (1.0/6.0, 2.0/3.0, 1.0/6.0),
                     (1.0/6.0, 1.0/6.0, 2.0/3.0)):
            point = sum(weight * vertex for weight, vertex in zip(bary, triangle))
            shape_a = overlap.shape_values(moved_a, point)
            shape_b = overlap.shape_values(moved_b, point)
            gap = float(direction @ (
                shape_a @ moved_a.corners - shape_b @ moved_b.corners
            ) + shape_a @ height_a - shape_b @ height_b)
            weight = area / 3.0
            support += weight * shape_a
            weighted_gap += weight * shape_a * gap
            gradient[:, :rows] += weight * np.outer(shape_a, shape_a)
            gradient[:, rows:] -= weight * np.outer(shape_a, shape_b)
    active_support = support > 0.0
    normalized_gap = np.zeros(rows, dtype=float)
    scale = max(float(np.max(np.linalg.norm(moved_a.corners - moved_a.corners[0], axis=1))),
                float(np.max(np.linalg.norm(moved_b.corners - moved_b.corners[0], axis=1))))
    roundoff = 256.0 * np.finfo(float).eps * scale
    weighted_gap[np.abs(weighted_gap) <= roundoff * support] = 0.0
    normalized_gap[active_support] = weighted_gap[active_support] / support[active_support]
    closed = active_support & (normalized_gap <= 0.0)
    active_gap = np.minimum(normalized_gap, 0.0)
    energy = 0.5 * penalty * float(support @ (active_gap * active_gap))
    residual = gradient.T @ (penalty * active_gap)
    tangent = np.zeros((columns, columns), dtype=float)
    if np.any(closed):
        tangent = (penalty * gradient[closed].T
                   @ np.diag(1.0 / support[closed]) @ gradient[closed])
    minimum_vertex_gap = float("inf")
    for point in polygon:
        shape_a = overlap.shape_values(moved_a, point)
        shape_b = overlap.shape_values(moved_b, point)
        minimum_vertex_gap = min(minimum_vertex_gap, float(direction @ (
            shape_a @ moved_a.corners - shape_b @ moved_b.corners
        ) + shape_a @ height_a - shape_b @ height_b))
    return MovingMortarState(
        overlap.area, support, weighted_gap, normalized_gap, energy,
        residual, tangent, minimum_vertex_gap,
    )
