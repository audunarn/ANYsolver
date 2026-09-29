"""Opt-in geometric and work-map admission checks for the D1 interior slice.

These checks limit the scope of a development candidate. They do not establish
pressure-space stability or replace the independent physical-gap certificate.
"""

from __future__ import annotations

from collections import Counter

import numpy as np

from .overlap import PlanarFace, planar_projected_overlap
from .q4_source_overlap import projected_q4_source_face


def physical_q4_rim_node_ids(model, selected_faces) -> frozenset[int]:
    """Find selected nodes on a physical Q4 edge, including adjoining Q4s."""
    from anysolver.e4_pl_element import QualifiedE4PLShellElement

    edge_counts: Counter[tuple[int, int]] = Counter()
    for element in model.mesh.elements.values():
        if type(element) is not QualifiedE4PLShellElement:
            continue
        nodes = element.node_ids
        edge_counts.update(tuple(sorted((a, b))) for a, b in
                           zip(nodes, nodes[1:] + nodes[:1]))
    rim = set()
    for face in selected_faces:
        nodes = face.node_ids
        for a, b in zip(nodes, nodes[1:] + nodes[:1]):
            if edge_counts[tuple(sorted((a, b)))] == 1:
                rim.update((a, b))
    return frozenset(rim)


def projected_coverage_issue(source: np.ndarray, target: np.ndarray,
                             source_indices, target_indices,
                             area_tolerance_m2: float) -> str | None:
    """Require every positively overlapping Q4 to be covered by S3 union."""
    for source_index, indices in enumerate(source_indices):
        face, normal = projected_q4_source_face(source[indices])
        corners = face.corners
        source_area = 0.5 * sum(float(np.cross(
            corners[j] - corners[0], corners[j + 1] - corners[0]) @ normal)
            for j in range(1, len(corners) - 1))
        if source_area <= 0.0:
            raise ValueError("D1 interior source projection has nonpositive area")
        overlap_area = 0.0
        for target_index, target_nodes in enumerate(target_indices):
            points = target[target_nodes]
            projected = points - ((points - corners[0]) @ normal)[:, None] * normal
            target_face = PlanarFace((2, target_index + 1), projected)
            overlap = planar_projected_overlap(face, target_face)
            if overlap is not None:
                overlap_area += overlap.area
        if overlap_area > source_area + area_tolerance_m2:
            return (f"source face {source_index + 1} has overlapping target "
                    f"coverage by {overlap_area - source_area:.6g} m2")
        if overlap_area > 0.0 and source_area - overlap_area > area_tolerance_m2:
            return (f"source face {source_index + 1} has partial target "
                    f"coverage; missing {source_area - overlap_area:.6g} m2")
    return None


def active_boundary_issue(certificate, source: np.ndarray,
                          source_indices, source_node_ids,
                          physical_rim_node_ids, work_map, transform,
                          force_tolerance_n: float) -> str | None:
    """Reject active rim pressure and zero physical normal work directions."""
    pressure_ids = tuple(certificate.source_pressure_node_ids)
    pressure = np.asarray(certificate.numerical_pressure_pa, dtype=float)
    support = np.asarray(certificate.reference_support_m2, dtype=float)
    if (pressure.shape != support.shape
            or pressure.shape != (len(pressure_ids),)):
        raise ValueError("D1 interior pressure report has inconsistent modes")
    source_index = {node: index for index, node in enumerate(source_node_ids)}
    normal_sums = np.zeros_like(source)
    for indices in source_indices:
        _face, normal = projected_q4_source_face(source[indices])
        for index in indices:
            normal_sums[index] += normal
    for node, nodal_force in zip(pressure_ids, pressure * support):
        if nodal_force <= force_tolerance_n:
            continue
        if node in physical_rim_node_ids:
            return f"active pressure at physical source rim node {node} ({nodal_force:.6g} N)"
        index = source_index[node]
        normal = normal_sums[index]
        normal /= np.linalg.norm(normal)
        rows = work_map[3 * index:3 * index + 3, :]
        full_variation = np.asarray(rows.T @ normal).reshape(-1)
        free_variation = np.asarray((rows @ transform).T @ normal).reshape(-1)
        numerical_zero = (256.0 * np.finfo(float).eps
                          * max(1.0, float(np.max(np.abs(full_variation)))))
        if np.max(np.abs(free_variation), initial=0.0) <= numerical_zero:
            return f"active pressure at prescribed-normal source node {node} ({nodal_force:.6g} N)"
    return None
