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
