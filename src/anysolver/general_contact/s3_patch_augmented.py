"""Projected normal work for a moving, primal-pressure S3 shell patch.

Multipliers are held during structural equilibrium.  The residual is the
weighted-gap virtual work, rather than the derivative of a shifted overlap
energy; this matters when the overlap support changes during sliding.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from .moving import _has_shared_edge_transition
from .overlap import PlanarFace, planar_projected_overlap
from .s3_patch_mortar_energy import (
    MovingS3PatchMortarWork,
    MovingS3PatchPrimalMortarPenalty,
)


class MovingS3PatchProjectedNormal:
    def __init__(self, geometry: MovingS3PatchPrimalMortarPenalty):
        if any(len(face.node_ids) != 3 for face in geometry.source_faces):
            raise ValueError("projected normal pressure space requires S3 source faces")
        self.geometry = geometry
        self.n_coordinates = geometry.n_coordinates
        self.source_node_ids = geometry.source_node_ids
        self.target_node_ids = geometry.target_node_ids
        self.source_face_indices = geometry.source_face_indices
        self.target_face_indices = geometry.target_face_indices
        self.reference_source = geometry.reference_source
        self.reference_target = geometry.reference_target
        self.stiffness = geometry.stiffness

    def _multipliers(self, multipliers):
        values = np.asarray(multipliers, dtype=float)
        if (values.shape != (len(self.source_node_ids),)
                or not np.all(np.isfinite(values)) or np.any(values < 0.0)):
            raise ValueError("S3 patch normal multipliers must be finite nonnegative pressures")
        return values

    def _project(self, state, multipliers):
        supported = state.reference_support > 0.0
        pressure = np.zeros_like(state.pressure)
        pressure[supported] = np.maximum(
            0.0, multipliers[supported]
            - self.stiffness*state.normalized_gap[supported],
        )
        # Algorithmic merit is useful for diagnostics, but its derivative is
        # not the virtual-work residual when overlap support changes.
        active_gap = np.zeros_like(state.normalized_gap)
        active_gap[supported] = np.minimum(
            state.normalized_gap[supported]
            - multipliers[supported]/self.stiffness, 0.0,
        )
        merit = 0.5*self.stiffness*float(
            state.reference_support @ (active_gap**2)
        )
        return replace(state, pressure=pressure, energy=merit)

    def evaluate(self, current_source, current_target, multipliers):
        multipliers = self._multipliers(multipliers)
        return self._project(
            self.geometry.evaluate(current_source, current_target), multipliers,
        )

    def projected_multiplier(self, state, multipliers):
        multipliers = self._multipliers(multipliers)
        result = np.zeros_like(multipliers)
        supported = state.reference_support > 0.0
        result[supported] = np.maximum(
            0.0, multipliers[supported]
            - self.stiffness*state.normalized_gap[supported],
        )
        return result

    def work(self, current_source, current_target, multipliers, *, tangent=True):
        multipliers = self._multipliers(multipliers)
        coordinates = np.concatenate((np.asarray(current_source, dtype=float),
                                      np.asarray(current_target, dtype=float))).reshape(-1)
        if coordinates.size != self.n_coordinates:
            raise ValueError("S3 patch work has invalid physical coordinate count")
        source_count = 3*len(self.source_node_ids)

        def state_at(values):
            return self.geometry.evaluate(
                values[:source_count].reshape(-1, 3),
                values[source_count:].reshape(-1, 3),
            )

        base_geometry = state_at(coordinates)
        base = self._project(base_geometry, multipliers)
        count = self.n_coordinates
        if not base.active_pressure_dofs:
            return MovingS3PatchMortarWork(
                base, np.zeros(count), np.zeros((count, count)) if tangent else None, 1,
            )
        for source_index in self.source_face_indices:
            first = PlanarFace((1, 1), np.asarray(current_source)[source_index])
            normal = np.cross(first.corners[1]-first.corners[0],
                              first.corners[2]-first.corners[0])
            normal /= np.linalg.norm(normal)
            for target_index in self.target_face_indices:
                target = np.asarray(current_target)[target_index]
                projected = target-((target-first.corners[0])@normal)[:, None]*normal
                second = PlanarFace((2, 1), projected)
                overlap = planar_projected_overlap(first, second)
                if _has_shared_edge_transition(first, second, overlap):
                    raise ValueError("S3 patch shared-edge derivative is nonunique")
        step = self.geometry.difference_step
        evaluations = 1
        cache = {}

        def geometry_at(steps):
            nonlocal evaluations
            key = tuple(sorted(steps))
            if key not in cache:
                evaluations += 1
                if evaluations > self.geometry.maximum_energy_evaluations:
                    raise MemoryError("S3 patch projected-work differentiation budget exhausted")
                trial = coordinates.copy()
                for coordinate, sign in steps:
                    trial[coordinate] += sign*step
                cache[key] = state_at(trial)
            return cache[key]

        positive = [geometry_at(((j, 1),)) for j in range(count)]
        negative = [geometry_at(((j, -1),)) for j in range(count)]
        jw = np.column_stack([
            (plus.reference_weighted_gap-minus.reference_weighted_gap)/(2*step)
            for plus, minus in zip(positive, negative)
        ])
        residual = -(base.pressure @ jw)
        if not tangent:
            return MovingS3PatchMortarWork(base, residual, None, evaluations)
        js = np.column_stack([
            (plus.reference_support-minus.reference_support)/(2*step)
            for plus, minus in zip(positive, negative)
        ])
        hessian_w = np.empty((len(self.source_node_ids), count, count))
        for j in range(count):
            hessian_w[:, j, j] = (
                positive[j].reference_weighted_gap
                - 2*base.reference_weighted_gap
                + negative[j].reference_weighted_gap
            )/step**2
            for k in range(j+1, count):
                mixed = (
                    geometry_at(((j, 1), (k, 1))).reference_weighted_gap
                    - geometry_at(((j, 1), (k, -1))).reference_weighted_gap
                    - geometry_at(((j, -1), (k, 1))).reference_weighted_gap
                    + geometry_at(((j, -1), (k, -1))).reference_weighted_gap
                )/(4*step**2)
                hessian_w[:, j, k] = mixed
                hessian_w[:, k, j] = mixed
        dp = np.zeros_like(jw)
        active = base.pressure > 0.0
        support = base.reference_support[active, None]
        dp[active] = -self.stiffness*(
            jw[active]/support
            - base.reference_weighted_gap[active, None]*js[active]/support**2
        )
        tangent_matrix = -(jw.T @ dp + np.einsum("i,ijk->jk", base.pressure, hessian_w))
        return MovingS3PatchMortarWork(base, residual, tangent_matrix, evaluations)
