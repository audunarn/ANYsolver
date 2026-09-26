"""Projected normal work for a moving, primal-pressure S3 or Q4 shell patch.

Multipliers are held during structural equilibrium. The residual acts through
reference support times the normalized-gap variation, not the derivative of
moving overlap support; this avoids frictionless boundary-motion work.
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from .moving import _has_shared_edge_transition
from .overlap import PlanarFace, planar_projected_overlap
from .q4_source_overlap import projected_q4_source_face
from .s3_patch_mortar_energy import (
    MovingS3PatchMortarWork,
    MovingS3PatchPrimalMortarPenalty,
)


class MovingS3PatchProjectedNormal:
    def __init__(self, geometry: MovingS3PatchPrimalMortarPenalty, *,
                 support_resolution: str = "exact"):
        if any(len(face.node_ids) not in {3, 4} for face in geometry.source_faces):
            raise ValueError("projected normal pressure space requires S3 or Q4 source faces")
        if support_resolution not in {"exact", "roundoff"}:
            raise ValueError("projected normal support resolution is invalid")
        self.geometry = geometry
        self.support_resolution = support_resolution
        self.n_coordinates = geometry.n_coordinates
        self.source_node_ids = geometry.source_node_ids
        self.target_node_ids = geometry.target_node_ids
        self.source_face_indices = geometry.source_face_indices
        self.target_face_indices = geometry.target_face_indices
        self.reference_source = geometry.reference_source
        self.reference_target = geometry.reference_target
        self.stiffness = geometry.stiffness
        self.tangent_active_coordinates: np.ndarray | None = None

    def set_tangent_active_coordinates(self, coordinates):
        """Limit Hessian work to physical axes reached by reduced unknowns."""
        indices = np.asarray(coordinates, dtype=np.intp).reshape(-1)
        if (np.any(indices < 0) or np.any(indices >= self.n_coordinates)
                or len(np.unique(indices)) != len(indices)):
            raise ValueError("projected patch tangent coordinate selection is invalid")
        self.tangent_active_coordinates = np.sort(indices)

    def _multipliers(self, multipliers):
        values = np.asarray(multipliers, dtype=float)
        if (values.shape != (len(self.source_node_ids),)
                or not np.all(np.isfinite(values)) or np.any(values < 0.0)):
            raise ValueError("patch normal multipliers must be finite nonnegative pressures")
        return values

    def resolved_support(self, state):
        """Return resolved support for algorithmic multiplier transfer only."""

        support = state.reference_support
        floor = (0.0 if self.support_resolution == "exact" else
                 np.finfo(float).eps*float(np.sum(support)))
        supported = support > floor
        return supported, floor

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
        supported, _floor = self.resolved_support(state)
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
            raise ValueError("patch work has invalid physical coordinate count")
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
                base, np.zeros(count), np.zeros((count, count)) if tangent else None,
                len(self.geometry.pair_laws)
                if self.geometry.differentiation == "pair_local" else 1,
            )
        for source_index in self.source_face_indices:
            source_positions = np.asarray(current_source)[source_index]
            if len(source_positions) == 4:
                first, normal = projected_q4_source_face(source_positions)
            else:
                first = PlanarFace((1, 1), source_positions)
                normal = np.cross(first.corners[1]-first.corners[0],
                                  first.corners[2]-first.corners[0])
                normal /= np.linalg.norm(normal)
            for target_index in self.target_face_indices:
                target = np.asarray(current_target)[target_index]
                projected = target-((target-first.corners[0])@normal)[:, None]*normal
                second = PlanarFace((2, 1), projected)
                overlap = planar_projected_overlap(first, second)
                if (overlap is not None
                        and _has_shared_edge_transition(first, second, overlap)):
                    raise ValueError("S3 patch shared-edge derivative is nonunique")
        if self.geometry.differentiation == "pair_local":
            return self._pair_local_work(current_source, current_target,
                                         base, tangent=tangent)
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
        js = np.column_stack([
            (plus.reference_support-minus.reference_support)/(2*step)
            for plus, minus in zip(positive, negative)
        ])
        gap_variation = jw-base.normalized_gap[:, None]*js
        residual = -(base.pressure @ gap_variation)
        if not tangent:
            return MovingS3PatchMortarWork(base, residual, None, evaluations)
        active_coordinates = (
            np.arange(count, dtype=np.intp)
            if self.tangent_active_coordinates is None else
            self.tangent_active_coordinates
        )
        hessian_w = np.empty((len(self.source_node_ids),
                              len(active_coordinates), len(active_coordinates)))
        hessian_s = np.empty_like(hessian_w)
        for local_j, j in enumerate(active_coordinates):
            hessian_w[:, local_j, local_j] = (
                positive[j].reference_weighted_gap
                - 2*base.reference_weighted_gap
                + negative[j].reference_weighted_gap
            )/step**2
            hessian_s[:, local_j, local_j] = (
                positive[j].reference_support
                - 2*base.reference_support
                + negative[j].reference_support
            )/step**2
            for local_k in range(local_j+1, len(active_coordinates)):
                k = int(active_coordinates[local_k])
                mixed = (
                    geometry_at(((j, 1), (k, 1))).reference_weighted_gap
                    - geometry_at(((j, 1), (k, -1))).reference_weighted_gap
                    - geometry_at(((j, -1), (k, 1))).reference_weighted_gap
                    + geometry_at(((j, -1), (k, -1))).reference_weighted_gap
                )/(4*step**2)
                hessian_w[:, local_j, local_k] = mixed
                hessian_w[:, local_k, local_j] = mixed
                mixed_support = (
                    geometry_at(((j, 1), (k, 1))).reference_support
                    - geometry_at(((j, 1), (k, -1))).reference_support
                    - geometry_at(((j, -1), (k, 1))).reference_support
                    + geometry_at(((j, -1), (k, -1))).reference_support
                )/(4*step**2)
                hessian_s[:, local_j, local_k] = mixed_support
                hessian_s[:, local_k, local_j] = mixed_support
        dp = np.zeros((len(self.source_node_ids), len(active_coordinates)))
        dg = np.zeros_like(dp)
        active = base.pressure > 0.0
        support = base.reference_support[active, None]
        dg[active] = gap_variation[np.ix_(active, active_coordinates)]/support
        dp[active] = -self.stiffness*dg[active]
        support_variation = (
            hessian_w
            - np.einsum("ij,ik->ijk", js[:, active_coordinates], dg)
            - base.normalized_gap[:, None, None]*hessian_s
        )
        reduced_tangent = -(
            gap_variation[:, active_coordinates].T @ dp
            + np.einsum("i,ijk->jk", base.pressure, support_variation)
        )
        tangent_matrix = np.zeros((count, count))
        tangent_matrix[np.ix_(active_coordinates, active_coordinates)] = (
            reduced_tangent
        )
        return MovingS3PatchMortarWork(base, residual, tangent_matrix, evaluations)

    def _pair_local_work(self, current_source, current_target, base, *, tangent):
        """Assemble integral derivatives per face pair into shared pressure nodes."""
        count = self.n_coordinates
        active_coordinates = (
            np.arange(count, dtype=np.intp)
            if self.tangent_active_coordinates is None else
            self.tangent_active_coordinates
        )
        source_count = len(self.source_node_ids)
        pressure_count = source_count
        jw = np.zeros((pressure_count, count))
        js = np.zeros_like(jw)
        weighted_hessian = np.zeros((count, count)) if tangent else None
        support_hessian = np.zeros((count, count)) if tangent else None
        step = self.geometry.difference_step
        evaluations = len(self.geometry.pair_laws)  # Base patch integration.
        source = np.asarray(current_source, dtype=float)
        target = np.asarray(current_target, dtype=float)

        for pair_index, law in enumerate(self.geometry.pair_laws):
            source_face = pair_index // len(self.geometry.target_faces)
            target_face = pair_index % len(self.geometry.target_faces)
            source_nodes = self.source_face_indices[source_face]
            target_nodes = self.target_face_indices[target_face]
            if not np.any(base.pressure[source_nodes]):
                continue
            local_positions = np.concatenate((source[source_nodes],
                                              target[target_nodes])).reshape(-1)
            source_local_count = 3*len(source_nodes)
            coordinate_map = np.asarray(
                [3*int(node)+axis for node in source_nodes for axis in range(3)]
                + [3*(source_count+int(node))+axis
                   for node in target_nodes for axis in range(3)],
                dtype=np.intp,
            )
            local_count = len(coordinate_map)
            local_active = np.flatnonzero(np.isin(coordinate_map,
                                                  active_coordinates))
            cache = {}

            def state_at(steps):
                nonlocal evaluations
                key = tuple(sorted(steps))
                if key in cache:
                    return cache[key]
                evaluations += 1
                if evaluations > self.geometry.maximum_energy_evaluations:
                    raise MemoryError("S3 patch pair-local differentiation budget exhausted")
                trial = local_positions.copy()
                for coordinate, sign in steps:
                    trial[coordinate] += sign*step
                cache[key] = law.evaluate(
                    trial[:source_local_count].reshape(-1, 3),
                    trial[source_local_count:].reshape(-1, 3),
                )
                return cache[key]

            middle = state_at(())
            positive = [state_at(((j, 1),)) for j in range(local_count)]
            negative = [state_at(((j, -1),)) for j in range(local_count)]
            local_jw = np.column_stack([
                (plus.reference_weighted_gap-minus.reference_weighted_gap)/(2*step)
                for plus, minus in zip(positive, negative)
            ])
            jw[np.ix_(source_nodes, coordinate_map)] += local_jw
            local_js = np.column_stack([
                (plus.reference_support-minus.reference_support)/(2*step)
                for plus, minus in zip(positive, negative)
            ])
            js[np.ix_(source_nodes, coordinate_map)] += local_js
            if not tangent:
                continue
            if not len(local_active):
                continue
            active_map = coordinate_map[local_active]
            local_pressure = base.pressure[source_nodes]
            local_support_weight = (
                local_pressure*base.normalized_gap[source_nodes]
            )
            local_hessian = np.empty((len(local_active), len(local_active)))
            local_support_hessian = np.empty_like(local_hessian)
            for local_j, j in enumerate(local_active):
                local_hessian[local_j, local_j] = float(local_pressure @ (
                    positive[j].reference_weighted_gap
                    - 2*middle.reference_weighted_gap
                    + negative[j].reference_weighted_gap
                ))/step**2
                local_support_hessian[local_j, local_j] = float(
                    local_support_weight @ (
                        positive[j].reference_support
                        - 2*middle.reference_support
                        + negative[j].reference_support
                    )
                )/step**2
                for local_k in range(local_j+1, len(local_active)):
                    k = int(local_active[local_k])
                    mixed = (
                        state_at(((j, 1), (k, 1))).reference_weighted_gap
                        - state_at(((j, 1), (k, -1))).reference_weighted_gap
                        - state_at(((j, -1), (k, 1))).reference_weighted_gap
                        + state_at(((j, -1), (k, -1))).reference_weighted_gap
                    )/(4*step**2)
                    local_hessian[local_j, local_k] = local_hessian[local_k, local_j] = float(
                        local_pressure @ mixed
                    )
                    mixed_support = (
                        state_at(((j, 1), (k, 1))).reference_support
                        - state_at(((j, 1), (k, -1))).reference_support
                        - state_at(((j, -1), (k, 1))).reference_support
                        + state_at(((j, -1), (k, -1))).reference_support
                    )/(4*step**2)
                    weighted_support = float(local_support_weight @ mixed_support)
                    local_support_hessian[local_j, local_k] = weighted_support
                    local_support_hessian[local_k, local_j] = weighted_support
            weighted_hessian[np.ix_(active_map, active_map)] += local_hessian
            support_hessian[np.ix_(active_map, active_map)] += local_support_hessian

        gap_variation = jw-base.normalized_gap[:, None]*js
        residual = -(base.pressure @ gap_variation)
        if not tangent:
            return MovingS3PatchMortarWork(base, residual, None, evaluations)
        dp = np.zeros((pressure_count, len(active_coordinates)))
        dg = np.zeros_like(dp)
        active = base.pressure > 0.0
        support = base.reference_support[active, None]
        dg[active] = gap_variation[np.ix_(active, active_coordinates)]/support
        dp[active] = -self.stiffness*dg[active]
        cross = np.einsum("i,ij,ik->jk", base.pressure,
                          js[:, active_coordinates], dg)
        tangent_matrix = np.zeros((count, count))
        tangent_matrix[np.ix_(active_coordinates, active_coordinates)] = -(
            gap_variation[:, active_coordinates].T @ dp
            + weighted_hessian[np.ix_(active_coordinates, active_coordinates)]
            - cross
            - support_hessian[np.ix_(active_coordinates, active_coordinates)]
        )
        return MovingS3PatchMortarWork(base, residual, tangent_matrix, evaluations)
