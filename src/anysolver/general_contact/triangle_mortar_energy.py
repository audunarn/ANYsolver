"""Moving S3/S3 primal P1 pressure-space penalty development kernel.

The three source pressure functions are the nonnegative physical S3 barycentric
functions. Clipping adds integration triangles but never multiplier unknowns.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .moving import _has_shared_edge_transition
from .overlap import PlanarFace, planar_projected_overlap
from .triangle_pair_energy import _triangle_area


@dataclass(frozen=True)
class MovingS3MortarState:
    energy: float
    reference_support: np.ndarray
    reference_weighted_gap: np.ndarray
    normalized_gap: np.ndarray
    pressure: np.ndarray
    pressure_gram: np.ndarray
    overlap_area: float
    reference_overlap_area: float
    minimum_physical_gap: float | None
    overlap_vertices: int

    @property
    def active_pressure_dofs(self) -> int:
        return int(np.count_nonzero(self.pressure))


@dataclass(frozen=True)
class MovingS3MortarGradient:
    state: MovingS3MortarState
    gradient: np.ndarray
    energy_evaluations: int


@dataclass(frozen=True)
class MovingS3MortarWork:
    state: MovingS3MortarState
    residual: np.ndarray
    tangent: np.ndarray | None
    energy_evaluations: int


class MovingS3PrimalMortarPenalty:
    """Reference-area normalized mortar penalty over exact affine overlap."""

    def __init__(self, reference_source: np.ndarray,
                 reference_target: np.ndarray, stiffness: float,
                 *, difference_step: float,
                 maximum_energy_evaluations: int = 1500):
        source = PlanarFace((1, 1), reference_source)
        target = PlanarFace((2, 1), reference_target)
        if len(source.corners) != 3 or len(target.corners) != 3:
            raise ValueError("moving S3 mortar requires two triangular faces")
        self.reference_source = source.corners
        self.reference_target = target.corners
        self.reference_area = _triangle_area(source.corners)
        self.reference_normal = np.cross(source.corners[1]-source.corners[0],
                                         source.corners[2]-source.corners[0])
        self.reference_normal /= np.linalg.norm(self.reference_normal)
        target_normal = np.cross(target.corners[1]-target.corners[0],
                                 target.corners[2]-target.corners[0])
        target_normal /= np.linalg.norm(target_normal)
        if float(self.reference_normal @ target_normal) <= 0.0:
            raise ValueError("moving S3 mortar reference face polarities conflict")
        if not np.isfinite(stiffness) or stiffness <= 0.0:
            raise ValueError("moving S3 mortar stiffness must be finite and positive")
        if not np.isfinite(difference_step) or difference_step <= 0.0:
            raise ValueError("moving S3 mortar difference step must be finite and positive")
        if (type(maximum_energy_evaluations) is not int
                or maximum_energy_evaluations < 1):
            raise ValueError("moving S3 mortar energy budget must be positive")
        self.stiffness = float(stiffness)
        self.difference_step = float(difference_step)
        self.maximum_energy_evaluations = maximum_energy_evaluations

    def evaluate(self, current_source: np.ndarray,
                 current_target: np.ndarray) -> MovingS3MortarState:
        source = PlanarFace((1, 1), current_source)
        target = PlanarFace((2, 1), current_target)
        if len(source.corners) != 3 or len(target.corners) != 3:
            raise ValueError("moving S3 mortar needs triangular current faces")
        normal = np.cross(source.corners[1]-source.corners[0],
                          source.corners[2]-source.corners[0])
        normal /= np.linalg.norm(normal)
        target_normal = np.cross(target.corners[1]-target.corners[0],
                                 target.corners[2]-target.corners[0])
        target_normal /= np.linalg.norm(target_normal)
        if (float(normal @ self.reference_normal) <= 0.0
                or float(normal @ target_normal) <= 0.0):
            raise ValueError("moving S3 mortar inverted or ambiguous face polarity")
        support = np.zeros(3)
        weighted_gap = np.zeros(3)
        gram = np.zeros((3, 3))
        normalized = np.zeros(3)
        pressure = np.zeros(3)
        overlap = planar_projected_overlap(source, target)
        if overlap is None:
            return MovingS3MortarState(
                0.0, support, weighted_gap, normalized, pressure, gram,
                0.0, 0.0, None, 0,
            )
        shapes = np.asarray([
            overlap.shape_values(source, point) for point in overlap.polygon
        ])
        gaps = np.asarray([
            float((point - overlap.shape_values(target, point)
                   @ target.corners) @ normal)
            for point in overlap.polygon
        ])
        for index in range(1, len(overlap.polygon)-1):
            corners = overlap.polygon[[0, index, index+1]]
            values = shapes[[0, index, index+1]]
            signed = gaps[[0, index, index+1]]
            area = _triangle_area(corners)
            sums = np.sum(values, axis=0)
            support += area/3.0 * sums
            weighted_gap += area/12.0 * (
                sums*np.sum(signed) + values.T @ signed
            )
            gram += area/12.0 * (
                np.outer(sums, sums) + values.T @ values
            )
        ratio = self.reference_area/_triangle_area(source.corners)
        support *= ratio
        weighted_gap *= ratio
        gram *= ratio
        if np.any(support <= 0.0) or not np.all(np.isfinite(support)):
            raise ValueError("moving S3 mortar has nonpositive pressure support")
        normalized = weighted_gap/support
        pressure = self.stiffness*np.maximum(-normalized, 0.0)
        energy = 0.5*self.stiffness*float(
            support @ np.minimum(normalized, 0.0)**2
        )
        return MovingS3MortarState(
            energy, support, weighted_gap, normalized, pressure, gram,
            overlap.area, ratio*overlap.area, float(np.min(gaps)),
            len(overlap.polygon),
        )

    def gradient(self, current_source: np.ndarray,
                 current_target: np.ndarray) -> MovingS3MortarGradient:
        work = self.work(current_source, current_target, tangent=False)
        return MovingS3MortarGradient(work.state, work.residual,
                                      work.energy_evaluations)

    def work(self, current_source: np.ndarray,
             current_target: np.ndarray, *, tangent: bool = True
             ) -> MovingS3MortarWork:
        positions = np.concatenate((np.asarray(current_source, dtype=float),
                                    np.asarray(current_target, dtype=float))).reshape(-1)
        if positions.size != 18:
            raise ValueError("moving S3 mortar work needs eighteen coordinates")
        base = self.evaluate(positions[:9].reshape(3, 3),
                             positions[9:].reshape(3, 3))
        if base.energy == 0.0:
            return MovingS3MortarWork(
                base, np.zeros(18), np.zeros((18, 18)) if tangent else None, 1,
            )
        if np.min(np.abs(base.normalized_gap)) <= 8.0*self.difference_step:
            raise ValueError("moving S3 mortar derivative is at a pressure branch")
        source = PlanarFace((1, 1), positions[:9].reshape(3, 3))
        target = PlanarFace((2, 1), positions[9:].reshape(3, 3))
        overlap = planar_projected_overlap(source, target)
        if _has_shared_edge_transition(source, target, overlap):
            raise ValueError("moving S3 mortar shared-edge derivative is nonunique")
        evaluations = 1
        cache: dict[tuple[tuple[int, int], ...], float] = {}

        def energy_at(steps: tuple[tuple[int, int], ...]) -> float:
            nonlocal evaluations
            key = tuple(sorted(steps))
            if key in cache:
                return cache[key]
            evaluations += 1
            if evaluations > self.maximum_energy_evaluations:
                raise MemoryError("moving S3 mortar differentiation budget exhausted")
            trial = positions.copy()
            for coordinate, sign in steps:
                trial[coordinate] += sign*self.difference_step
            state = self.evaluate(trial[:9].reshape(3, 3),
                                  trial[9:].reshape(3, 3))
            if (state.overlap_vertices != base.overlap_vertices
                    or not np.array_equal(state.pressure > 0.0,
                                          base.pressure > 0.0)):
                raise ValueError("moving S3 mortar derivative crosses an overlap/pressure branch")
            cache[key] = state.energy
            return state.energy

        gradient = np.empty(18)
        positive = np.empty(18)
        negative = np.empty(18)
        for coordinate in range(18):
            positive[coordinate] = energy_at(((coordinate, 1),))
            negative[coordinate] = energy_at(((coordinate, -1),))
            gradient[coordinate] = ((positive[coordinate]-negative[coordinate])
                                    /(2.0*self.difference_step))
        hessian = None
        if tangent:
            hessian = np.empty((18, 18))
            for first in range(18):
                hessian[first, first] = (
                    positive[first]-2.0*base.energy+negative[first]
                ) / self.difference_step**2
                for second in range(first+1, 18):
                    hessian[first, second] = hessian[second, first] = (
                        energy_at(((first, 1), (second, 1)))
                        - energy_at(((first, 1), (second, -1)))
                        - energy_at(((first, -1), (second, 1)))
                        + energy_at(((first, -1), (second, -1)))
                    ) / (4.0*self.difference_step**2)
        return MovingS3MortarWork(base, gradient, hessian, evaluations)
