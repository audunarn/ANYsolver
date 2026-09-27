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
from .q4_s3_overlap_derivatives import (
    UnsupportedQ4S3Branch, q4_s3_overlap_derivatives,
)
from .s3_overlap_derivatives import UnsupportedOverlapBranch, s3_overlap_derivatives
from .s3_patch_mortar_energy import (
    MovingS3PatchMortarWork,
    MovingS3PatchPrimalMortarPenalty,
)


def _touching_projected_boundaries(first: PlanarFace, second: PlanarFace) -> bool:
    """Conservatively identify a zero-area projection branch transition."""
    tangent = first.corners[1] - first.corners[0]
    tangent /= np.linalg.norm(tangent)
    normal = np.cross(first.corners[1] - first.corners[0],
                      first.corners[-1] - first.corners[0])
    normal /= np.linalg.norm(normal)
    binormal = np.cross(normal, tangent)
    origin = first.corners[0]
    polygons = tuple(np.column_stack(((face.corners-origin) @ tangent,
                                      (face.corners-origin) @ binormal))
                     for face in (first, second))
    scale = max(float(np.max(np.linalg.norm(p-p[0], axis=1))) for p in polygons)
    tolerance = 1.0e-11*scale
    for vertices, edges in ((polygons[0], polygons[1]),
                            (polygons[1], polygons[0])):
        for point in vertices:
            for start, end in zip(edges, np.roll(edges, -1, axis=0)):
                edge = end-start
                fraction = np.clip(np.dot(point-start, edge)/np.dot(edge, edge),
                                   0.0, 1.0)
                if np.linalg.norm(point-(start+fraction*edge)) <= tolerance:
                    return True
    return False


def _touching_shared_target_edge(first: PlanarFace,
                                 target_positions: np.ndarray,
                                 target_node_ids: np.ndarray,
                                 shared_node_ids: set[int]) -> bool:
    """Require the touching target edge, excluding exterior/endpoint ties."""
    edge = first.corners[1]-first.corners[0]
    tangent = edge/np.linalg.norm(edge)
    normal = np.cross(edge, first.corners[-1]-first.corners[0])
    normal /= np.linalg.norm(normal)
    binormal = np.cross(normal, tangent)
    origin = first.corners[0]
    source_xy = np.column_stack(((first.corners-origin) @ tangent,
                                 (first.corners-origin) @ binormal))
    target_xy = np.column_stack(((target_positions-origin) @ tangent,
                                 (target_positions-origin) @ binormal))
    scale = max(float(np.max(np.linalg.norm(source_xy-source_xy[0], axis=1))),
                float(np.max(np.linalg.norm(target_xy-target_xy[0], axis=1))))
    tolerance = 1.0e-11*scale

    def near_segment(point, start, end):
        span = end-start
        squared = float(np.dot(span, span))
        if squared <= 0.0:
            return False
        fraction = np.clip(np.dot(point-start, span)/squared,
                           0.0, 1.0)
        return np.linalg.norm(point-(start+fraction*span)) <= tolerance

    shared_touch = False
    exterior_touch = False
    for point in source_xy:
        for edge_index in range(3):
            following = (edge_index+1) % 3
            if near_segment(point, target_xy[edge_index], target_xy[following]):
                if (int(target_node_ids[edge_index]) in shared_node_ids
                        and int(target_node_ids[following]) in shared_node_ids):
                    shared_touch = True
                else:
                    exterior_touch = True
    # A target vertex on a source edge is an endpoint tie; it does not
    # uniquely identify the shared material edge's one-sided branch.
    for point in target_xy:
        for start, end in zip(source_xy, np.roll(source_xy, -1, axis=0)):
            if near_segment(point, start, end):
                exterior_touch = True
    return shared_touch and not exterior_touch


def _q4_s3_pair_value_rtol(local_area: float, derivative_area: float,
                           area_resolution: float) -> float:
    """Bound a float/Jet2 value comparison by resolved polygon disagreement."""
    if min(local_area, derivative_area) <= 0.0:
        raise UnsupportedQ4S3Branch("Q4/S3 paired overlap area is not positive")
    difference = abs(local_area-derivative_area)
    relative = 2.0*difference/min(local_area, derivative_area)
    if (not np.isfinite(relative) or not np.isfinite(area_resolution)
            or difference > area_resolution or relative > 1.0e-6):
        raise UnsupportedQ4S3Branch(
            "Q4/S3 paired overlap area agreement is unresolved "
            f"(area_difference_m2={difference:.12g}, "
            f"area_resolution_m2={area_resolution:.12g}, "
            f"relative_value_allowance={relative:.12g})"
        )
    return 1.0e-9+relative


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
                if self.geometry.differentiation in {"pair_local", "jet2_s3", "jet2_q4_s3"} else 1,
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
            for target_position, target_index in enumerate(self.target_face_indices):
                target = np.asarray(current_target)[target_index]
                projected = target-((target-first.corners[0])@normal)[:, None]*normal
                second = PlanarFace((2, 1), projected)
                overlap = planar_projected_overlap(first, second)
                if (overlap is not None
                        and _has_shared_edge_transition(first, second, overlap)):
                    raise ValueError("S3 patch shared-edge derivative is nonunique")
                if (overlap is None
                        and self.geometry.differentiation in {"jet2_s3", "jet2_q4_s3"}
                        and _touching_projected_boundaries(first, second)):
                    if self.geometry.differentiation == "jet2_s3":
                        raise UnsupportedOverlapBranch(
                            "S3 patch zero-area touching overlap has no smooth derivative"
                        )
                    # Use the inactive one-sided branch only for an artificial
                    # diagonal with an overlapping material-edge neighbor.
                    # Exterior rims and unmatched seams remain unresolved.
                    target_nodes = set(map(int, target_index))
                    adjacent_positive = False
                    for other_position, other_index in enumerate(self.target_face_indices):
                        shared = target_nodes.intersection(map(int, other_index))
                        if other_position == target_position or len(shared) != 2:
                            continue
                        if not _touching_shared_target_edge(
                                first, target, target_index, shared):
                            continue
                        other = np.asarray(current_target)[other_index]
                        first_target_normal = np.cross(target[1]-target[0],
                                                       target[2]-target[0])
                        other_target_normal = np.cross(other[1]-other[0],
                                                       other[2]-other[0])
                        normal_product = (np.linalg.norm(first_target_normal)
                                          * np.linalg.norm(other_target_normal))
                        if (normal_product <= 0.0 or
                                np.dot(first_target_normal, other_target_normal)
                                < (1.0-1.0e-10)*normal_product):
                            continue
                        other_projected = other-((other-first.corners[0]) @ normal)[:, None]*normal
                        other_face = PlanarFace((2, 1), other_projected)
                        if planar_projected_overlap(first, other_face) is not None:
                            adjacent_positive = True
                            break
                    if not adjacent_positive:
                        raise UnsupportedQ4S3Branch(
                            "Q4/S3 zero-area touch has no positive adjacent target face"
                        )
        if self.geometry.differentiation == "pair_local":
            return self._pair_local_work(current_source, current_target,
                                         base, tangent=tangent)
        if self.geometry.differentiation in {"jet2_s3", "jet2_q4_s3"}:
            return self._jet2_s3_work(current_source, current_target,
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

    def _jet2_s3_work(self, current_source, current_target, base, *, tangent):
        """Assemble differentiated pair geometry into shared pressure nodes."""
        count = self.n_coordinates
        source_count = len(self.source_node_ids)
        active_coordinates = (
            np.arange(count, dtype=np.intp)
            if self.tangent_active_coordinates is None else
            self.tangent_active_coordinates
        )
        jw = np.zeros((source_count, count))
        js = np.zeros_like(jw)
        assembled_support = np.zeros(source_count)
        assembled_gap = np.zeros(source_count)
        support_magnitude = np.zeros(source_count)
        gap_magnitude = np.zeros(source_count)
        support_roundoff_budget = np.zeros(source_count)
        gap_roundoff_budget = np.zeros(source_count)
        weighted_hessian = np.zeros((len(active_coordinates),
                                     len(active_coordinates))) if tangent else None
        support_hessian = np.zeros_like(weighted_hessian) if tangent else None
        evaluations = len(self.geometry.pair_laws)
        zero_area_overlap_pairs = []
        source = np.asarray(current_source, dtype=float)
        target = np.asarray(current_target, dtype=float)
        for pair_index, law in enumerate(self.geometry.pair_laws):
            source_face = pair_index // len(self.geometry.target_faces)
            target_face = pair_index % len(self.geometry.target_faces)
            source_nodes = self.source_face_indices[source_face]
            target_nodes = self.target_face_indices[target_face]
            local_source = source[source_nodes]
            local_target = target[target_nodes]
            local = law.evaluate(local_source, local_target)
            evaluations += 1
            if local.reference_overlap_area == 0.0:
                if local.overlap_vertices > 0:
                    zero_area_overlap_pairs.append(pair_index)
                continue
            if len(source_nodes) == 4:
                try:
                    derivative = q4_s3_overlap_derivatives(
                        self.geometry.source_faces[source_face].reference_positions,
                        local_source, local_target,
                        area_tolerance=self.geometry.q4_source_area_tolerance,
                        weighted_gap_tolerance=self.geometry.q4_source_weighted_gap_tolerance,
                        maximum_triangles=self.geometry.maximum_q4_source_integration_triangles,
                        allow_warped_source=True,
                        **dict(zip((
                            "support_gradient_tolerance",
                            "support_hessian_tolerance",
                            "weighted_gap_gradient_tolerance",
                            "weighted_gap_hessian_tolerance",
                        ), self.geometry.q4_source_derivative_tolerances or (None,)*4)),
                    )
                except UnsupportedQ4S3Branch as exc:
                    raise UnsupportedQ4S3Branch(
                        f"pair={pair_index}, overlap_area_m2={local.overlap_area:.12g}, "
                        f"reference_overlap_area_m2={local.reference_overlap_area:.12g}, "
                        f"integration_triangles={local.integration_triangles}: {exc}"
                    ) from exc
            else:
                derivative = s3_overlap_derivatives(
                    self.geometry.source_faces[source_face].reference_positions,
                    local_source, local_target,
                )
            evaluations += 1
            support_scale = max(float(np.max(np.abs(local.reference_support))),
                                float(np.max(np.abs(derivative.reference_support))))
            weighted_gap_scale = max(
                float(np.max(np.abs(local.reference_weighted_gap))),
                float(np.max(np.abs(derivative.reference_weighted_gap))),
            )
            # Both integrations sum work over the adaptive overlap triangles.
            # Bound cancellation near zero by that operation count; the
            # separate quadrature tolerances still govern approximation error.
            roundoff_factor = (512.0*np.finfo(float).eps
                               * max(1, local.integration_triangles))
            support_roundoff = roundoff_factor*support_scale
            weighted_gap_roundoff = roundoff_factor*weighted_gap_scale
            value_rtol = 1.0e-9
            if len(source_nodes) == 4:
                # The float and Jet2 clippers use different arithmetic paths.
                # For a tiny wedge, compare their area discrepancy with the
                # propagated polygon-coordinate resolution first. Permit only
                # twice that observed relative discrepancy in the per-node
                # integrals; this does not relax quadrature or tangent gates.
                value_rtol = _q4_s3_pair_value_rtol(
                    local.overlap_area, derivative.overlap_area,
                    derivative.overlap_area_resolution,
                )
            if (not np.allclose(derivative.reference_support,
                                local.reference_support, rtol=value_rtol,
                                atol=support_roundoff)
                    or not np.allclose(derivative.reference_weighted_gap,
                                       local.reference_weighted_gap,
                                       rtol=value_rtol,
                                       atol=weighted_gap_roundoff)):
                support_error = float(np.max(np.abs(
                    derivative.reference_support-local.reference_support,
                )))
                gap_error = float(np.max(np.abs(
                    derivative.reference_weighted_gap-local.reference_weighted_gap,
                )))
                raise ValueError(
                    "differentiated S3 overlap disagrees with mortar geometry "
                    f"(pair={pair_index}, support_error_m2={support_error:.12g}, "
                    f"weighted_gap_error_m3={gap_error:.12g}, "
                    f"support_scale_m2={support_scale:.12g}, "
                    f"weighted_gap_scale_m3={weighted_gap_scale:.12g}, "
                    f"support_roundoff_m2={support_roundoff:.12g}, "
                    f"weighted_gap_roundoff_m3={weighted_gap_roundoff:.12g}, "
                    f"geometry_value_rtol={value_rtol:.12g}, "
                    f"integration_triangles={local.integration_triangles}, "
                    f"overlap_area_local_m2={local.overlap_area:.12g}, "
                    f"overlap_area_m2={derivative.overlap_area:.12g}, "
                    f"overlap_area_resolution_m2={derivative.overlap_area_resolution:.12g}, "
                    f"support_local_m2={local.reference_support.tolist()}, "
                    f"support_derivative_m2={derivative.reference_support.tolist()}, "
                    f"weighted_gap_local_m3={local.reference_weighted_gap.tolist()}, "
                    f"weighted_gap_derivative_m3={derivative.reference_weighted_gap.tolist()})"
                )
            assembled_support[source_nodes] += derivative.reference_support
            assembled_gap[source_nodes] += derivative.reference_weighted_gap
            support_magnitude[source_nodes] += np.abs(derivative.reference_support)
            gap_magnitude[source_nodes] += np.abs(derivative.reference_weighted_gap)
            support_roundoff_budget[source_nodes] += support_roundoff
            gap_roundoff_budget[source_nodes] += weighted_gap_roundoff
            if not np.any(base.pressure[source_nodes]):
                continue
            coordinate_map = np.asarray(
                [3*int(node)+axis for node in source_nodes for axis in range(3)]
                + [3*(source_count+int(node))+axis
                   for node in target_nodes for axis in range(3)],
                dtype=np.intp,
            )
            jw[np.ix_(source_nodes, coordinate_map)] += derivative.weighted_gap_gradient
            js[np.ix_(source_nodes, coordinate_map)] += derivative.support_gradient
            if tangent:
                local_active = np.flatnonzero(np.isin(coordinate_map, active_coordinates))
                if len(local_active):
                    global_active = coordinate_map[local_active]
                    indices = np.searchsorted(active_coordinates, global_active)
                    local_pressure = base.pressure[source_nodes]
                    weighted = np.einsum(
                        "i,ijk->jk", local_pressure,
                        derivative.weighted_gap_hessian[:, local_active][:, :, local_active],
                    )
                    supported = np.einsum(
                        "i,ijk->jk",
                        local_pressure*base.normalized_gap[source_nodes],
                        derivative.support_hessian[:, local_active][:, :, local_active],
                    )
                    weighted_hessian[np.ix_(indices, indices)] += weighted
                    support_hessian[np.ix_(indices, indices)] += supported
        # Pair-wise integration has already matched at 1e-9 relative error.
        # Summing signed contributions can make the assembled total tiny;
        # compare against the sum of contribution magnitudes so roundoff and
        # allowed pair errors do not turn into a false zero-scale mismatch.
        summation_tolerance = 1.0e-9 + 64.0*np.finfo(float).eps
        if (not all(np.all(np.isfinite(values)) for values in (
                    assembled_support, base.reference_support,
                    assembled_gap, base.reference_weighted_gap,
                    support_magnitude, gap_magnitude,
                    support_roundoff_budget, gap_roundoff_budget))
                or np.any(np.abs(assembled_support-base.reference_support)
                   > summation_tolerance*support_magnitude
                     + support_roundoff_budget)
                or np.any(np.abs(assembled_gap-base.reference_weighted_gap)
                          > summation_tolerance*gap_magnitude
                            + gap_roundoff_budget)):
            raise ValueError(
                "differentiated S3 patch disagrees with shared pressure support: "
                f"support_error={np.max(np.abs(assembled_support-base.reference_support)):.9g}, "
                f"weighted_gap_error={np.max(np.abs(assembled_gap-base.reference_weighted_gap)):.9g}, "
                f"zero_area_overlap_pairs={zero_area_overlap_pairs}"
            )
        gap_variation = jw - base.normalized_gap[:, None]*js
        residual = -(base.pressure @ gap_variation)
        if not tangent:
            return MovingS3PatchMortarWork(base, residual, None, evaluations)
        active = base.pressure > 0.0
        dg = np.zeros((source_count, len(active_coordinates)))
        dg[active] = (gap_variation[np.ix_(active, active_coordinates)]
                      / base.reference_support[active, None])
        dp = -self.stiffness*dg
        cross = np.einsum("i,ij,ik->jk", base.pressure,
                          js[:, active_coordinates], dg)
        tangent_matrix = np.zeros((count, count))
        tangent_matrix[np.ix_(active_coordinates, active_coordinates)] = -(
            gap_variation[:, active_coordinates].T @ dp
            + weighted_hessian - cross - support_hessian
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
