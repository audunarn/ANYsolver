"""Bounded moving S3 patch mortar penalty with shared material-node pressure."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .moving import _has_shared_edge_transition
from .overlap import PlanarFace, planar_projected_overlap
from .triangle_mortar_energy import MovingS3PrimalMortarPenalty


@dataclass(frozen=True)
class S3PatchFace:
    node_ids: tuple[int, int, int]
    reference_positions: np.ndarray

    def __post_init__(self):
        nodes = tuple(self.node_ids)
        if (len(nodes) not in {3, 4} or len(set(nodes)) != len(nodes)
                or any(type(node) is not int or node <= 0 for node in nodes)):
            raise ValueError("shell patch face needs three or four distinct material nodes")
        face = PlanarFace((1, 1), self.reference_positions)
        if len(face.corners) != len(nodes):
            raise ValueError("shell patch face topology and geometry disagree")
        object.__setattr__(self, "node_ids", nodes)
        object.__setattr__(self, "reference_positions", face.corners)


@dataclass(frozen=True)
class MovingS3PatchMortarState:
    energy: float
    reference_support: np.ndarray
    reference_weighted_gap: np.ndarray
    normalized_gap: np.ndarray
    pressure: np.ndarray
    pressure_gram: np.ndarray
    overlap_area: float
    reference_overlap_area: float
    minimum_physical_gap: float | None
    overlap_signature: tuple[int, ...]
    overlapping_pairs: int
    weighted_gap_integration_error: float = 0.0
    integration_triangles: int = 0

    @property
    def active_pressure_dofs(self):
        return int(np.count_nonzero(self.pressure))


@dataclass(frozen=True)
class MovingS3PatchMortarWork:
    state: MovingS3PatchMortarState
    residual: np.ndarray
    tangent: np.ndarray | None
    energy_evaluations: int


class MovingS3PatchPrimalMortarPenalty:
    """Aggregate pair integrals before normalizing shared source P1 gaps."""

    def __init__(self, source_faces: tuple[S3PatchFace, ...],
                 target_faces: tuple[S3PatchFace, ...], stiffness: float,
                 *, difference_step: float,
                 maximum_energy_evaluations: int = 1500,
                 q4_weighted_gap_tolerance: float | None = None,
                 maximum_q4_integration_triangles: int | None = None):
        self.source_faces = tuple(source_faces)
        self.target_faces = tuple(target_faces)
        if not (1 <= len(self.source_faces) <= 2
                and 1 <= len(self.target_faces) <= 2
                and len(self.source_faces)+len(self.target_faces) >= 3):
            raise ValueError("development S3 patch needs one or two faces per side and at least three total")
        if any(len(face.node_ids) != 3 for face in self.source_faces):
            raise ValueError("development patch pressure side needs S3 triangles")
        self.source_node_ids = tuple(sorted({node for face in self.source_faces
                                             for node in face.node_ids}))
        self.target_node_ids = tuple(sorted({node for face in self.target_faces
                                             for node in face.node_ids}))
        if set(self.source_node_ids) & set(self.target_node_ids):
            raise ValueError("S3 patch sides must have disjoint material nodes")
        self.reference_source = self._unique_reference(
            self.source_faces, self.source_node_ids,
        )
        self.reference_target = self._unique_reference(
            self.target_faces, self.target_node_ids,
        )
        self.source_face_indices = tuple(np.asarray([
            self.source_node_ids.index(node) for node in face.node_ids
        ], dtype=np.intp) for face in self.source_faces)
        self.target_face_indices = tuple(np.asarray([
            self.target_node_ids.index(node) for node in face.node_ids
        ], dtype=np.intp) for face in self.target_faces)
        self.stiffness = float(stiffness)
        self.difference_step = float(difference_step)
        if (type(maximum_energy_evaluations) is not int
                or maximum_energy_evaluations < 1):
            raise ValueError("S3 patch energy evaluation budget must be positive")
        self.maximum_energy_evaluations = maximum_energy_evaluations
        self.n_coordinates = 3*(len(self.source_node_ids)+len(self.target_node_ids))
        self.required_hessian_evaluations = 1+2*self.n_coordinates**2
        if self.required_hessian_evaluations > self.maximum_energy_evaluations:
            raise MemoryError(
                "S3 patch Hessian exceeds declared energy evaluation budget"
            )
        self.pair_laws = tuple(
            MovingS3PrimalMortarPenalty(
                source.reference_positions, target.reference_positions,
                self.stiffness, difference_step=self.difference_step,
                maximum_energy_evaluations=self.maximum_energy_evaluations,
                q4_weighted_gap_tolerance=q4_weighted_gap_tolerance,
                maximum_q4_integration_triangles=maximum_q4_integration_triangles,
            )
            for source in self.source_faces for target in self.target_faces
        )
        self._check_same_side_overlap(self.reference_source, self.source_face_indices)
        self._check_same_side_overlap(self.reference_target, self.target_face_indices)

    @staticmethod
    def _unique_reference(faces: tuple[S3PatchFace, ...],
                          node_ids: tuple[int, ...]) -> np.ndarray:
        positions: dict[int, np.ndarray] = {}
        scale = max(1.0, *(float(np.max(np.abs(face.reference_positions)))
                           for face in faces))
        for face in faces:
            for node, position in zip(face.node_ids, face.reference_positions):
                if node in positions and (float(np.linalg.norm(positions[node]-position))
                                          > 1e-12*scale):
                    raise ValueError("shared S3 patch node has inconsistent physical skin position")
                positions[node] = position
        return np.asarray([positions[node] for node in node_ids], dtype=float)

    @staticmethod
    def _check_same_side_overlap(positions: np.ndarray,
                                 indices: tuple[np.ndarray, ...]) -> None:
        if len(indices) < 2:
            return
        first = PlanarFace((1, 1), positions[indices[0]])
        second = PlanarFace((1, 2), positions[indices[1]])
        overlap = planar_projected_overlap(first, second)
        if overlap is not None:
            scale = max(1.0, float(np.max(np.abs(positions))))
            if overlap.area > 1e-12*scale**2:
                raise ValueError("S3 patch has overlapping faces on one side")

    def evaluate(self, current_source: np.ndarray,
                 current_target: np.ndarray) -> MovingS3PatchMortarState:
        source = np.asarray(current_source, dtype=float)
        target = np.asarray(current_target, dtype=float)
        if (source.shape != self.reference_source.shape
                or target.shape != self.reference_target.shape
                or not np.all(np.isfinite(source))
                or not np.all(np.isfinite(target))):
            raise ValueError("S3 patch current coordinates have invalid size or values")
        self._check_same_side_overlap(source, self.source_face_indices)
        self._check_same_side_overlap(target, self.target_face_indices)
        support = np.zeros(len(self.source_node_ids))
        weighted_gap = np.zeros_like(support)
        gram = np.zeros((len(support), len(support)))
        overlap_area = reference_overlap_area = 0.0
        minimum = None
        signature: list[int] = []
        overlapping_pairs = 0
        weighted_error = 0.0
        integration_triangles = 0
        for index, law in enumerate(self.pair_laws):
            source_face = index // len(self.target_faces)
            target_face = index % len(self.target_faces)
            state = law.evaluate(source[self.source_face_indices[source_face]],
                                 target[self.target_face_indices[target_face]])
            signature.append(state.overlap_vertices)
            if state.overlap_vertices == 0:
                continue
            overlapping_pairs += 1
            weighted_error += state.weighted_gap_integration_error
            integration_triangles += state.integration_triangles
            dofs = self.source_face_indices[source_face]
            support[dofs] += state.reference_support
            weighted_gap[dofs] += state.reference_weighted_gap
            gram[np.ix_(dofs, dofs)] += state.pressure_gram
            overlap_area += state.overlap_area
            reference_overlap_area += state.reference_overlap_area
            minimum = (state.minimum_physical_gap if minimum is None
                       else min(minimum, state.minimum_physical_gap))
        normalized = np.zeros_like(support)
        supported = support > 0.0
        normalized[supported] = weighted_gap[supported]/support[supported]
        pressure = np.zeros_like(support)
        pressure[supported] = self.stiffness*np.maximum(-normalized[supported], 0.0)
        energy = 0.5*self.stiffness*float(
            support @ np.minimum(normalized, 0.0)**2
        )
        return MovingS3PatchMortarState(
            energy, support, weighted_gap, normalized, pressure, gram,
            overlap_area, reference_overlap_area, minimum,
            tuple(signature), overlapping_pairs,
            weighted_error, integration_triangles,
        )

    def work(self, current_source: np.ndarray, current_target: np.ndarray,
             *, tangent: bool = True) -> MovingS3PatchMortarWork:
        coordinates = np.concatenate((np.asarray(current_source, dtype=float),
                                      np.asarray(current_target, dtype=float))).reshape(-1)
        if coordinates.size != self.n_coordinates:
            raise ValueError("S3 patch work has invalid physical coordinate count")
        source_count = 3*len(self.source_node_ids)
        def state_at(values):
            return self.evaluate(values[:source_count].reshape(-1, 3),
                                 values[source_count:].reshape(-1, 3))
        base = state_at(coordinates)
        if base.energy == 0.0:
            return MovingS3PatchMortarWork(
                base, np.zeros(self.n_coordinates),
                np.zeros((self.n_coordinates, self.n_coordinates)) if tangent else None,
                1,
            )
        for index, law in enumerate(self.pair_laws):
            source_face = index // len(self.target_faces)
            target_face = index % len(self.target_faces)
            first = PlanarFace((1, 1),
                               np.asarray(current_source)[self.source_face_indices[source_face]])
            second = PlanarFace((2, 1),
                                np.asarray(current_target)[self.target_face_indices[target_face]])
            overlap = planar_projected_overlap(first, second)
            if _has_shared_edge_transition(first, second, overlap):
                raise ValueError("S3 patch shared-edge derivative is nonunique")
        evaluations = 1
        cache: dict[tuple[tuple[int, int], ...], float] = {}
        def energy_at(steps):
            nonlocal evaluations
            key = tuple(sorted(steps))
            if key in cache:
                return cache[key]
            evaluations += 1
            if evaluations > self.maximum_energy_evaluations:
                raise MemoryError("S3 patch differentiation budget exhausted")
            trial = coordinates.copy()
            for coordinate, sign in steps:
                trial[coordinate] += sign*self.difference_step
            result = state_at(trial)
            # Internal clipping diagonals can switch polygon combinatorics while
            # the shared-node patch potential remains smooth. Differentiate the
            # aggregate energy; same-side overlap and true shared-edge contacts
            # are checked independently above.
            cache[key] = result.energy
            return result.energy
        positive = np.empty(self.n_coordinates)
        negative = np.empty(self.n_coordinates)
        residual = np.empty(self.n_coordinates)
        for coordinate in range(self.n_coordinates):
            positive[coordinate] = energy_at(((coordinate, 1),))
            negative[coordinate] = energy_at(((coordinate, -1),))
            residual[coordinate] = ((positive[coordinate]-negative[coordinate])
                                    /(2.0*self.difference_step))
        hessian = None
        if tangent:
            hessian = np.empty((self.n_coordinates, self.n_coordinates))
            for first in range(self.n_coordinates):
                hessian[first, first] = (
                    positive[first]-2.0*base.energy+negative[first]
                )/self.difference_step**2
                for second in range(first+1, self.n_coordinates):
                    hessian[first, second] = hessian[second, first] = (
                        energy_at(((first, 1), (second, 1)))
                        - energy_at(((first, 1), (second, -1)))
                        - energy_at(((first, -1), (second, 1)))
                        + energy_at(((first, -1), (second, -1)))
                    )/(4.0*self.difference_step**2)
        return MovingS3PatchMortarWork(base, residual, hessian, evaluations)
