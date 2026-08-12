"""Numeric, sheet-aware reference-director preparation for improved Q4 shells.

This is a model-preparation module, not an element integration kernel.  It
accepts only numeric mesh arrays and compact integer region indices.  The
returned field is immutable and stores one director per element corner, so a
shared global node may legitimately carry different directors on different
sheets, parts, creases, or declared continuity regions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Iterable, Sequence

import numpy as np

from .mitc4_plus_d_quality import (
    CornerDirectorQuality,
    corner_director_quality,
    numeric_payload_fingerprint,
    q4_geometry_quality,
)


class DirectorProvenanceCode(str, Enum):
    """Permanent provenance labels for Q4 reference directors."""

    SOURCE_SURFACE_EXACT = "source_surface_exact"
    SOURCE_SURFACE_SAMPLED = "source_surface_sampled"
    SHEET_AWARE_MESH_RECONSTRUCTION = "sheet_aware_mesh_reconstruction"
    LOCAL_ELEMENT_RECONSTRUCTION = "local_element_reconstruction"
    LEGACY_CENTER_FRAME = "legacy_center_frame"
    USER_SUPPLIED = "user_supplied"


DIRECTOR_PROVENANCE_NUMERIC_CODE: dict[DirectorProvenanceCode, int] = {
    code: index for index, code in enumerate(DirectorProvenanceCode)
}
DIRECTOR_PROVENANCE_FROM_NUMERIC_CODE: dict[int, DirectorProvenanceCode] = {
    value: key for key, value in DIRECTOR_PROVENANCE_NUMERIC_CODE.items()
}


@dataclass(frozen=True)
class DirectorValidationLimits:
    """Finite-element-scale acceptance limits for a prepared director field."""

    normalization_atol: float = 1.0e-10
    minimum_geometry_alignment: float = 1.0e-8
    maximum_corner_spread_degrees: float = 85.0
    crease_angle_degrees: float = 35.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.normalization_atol) or self.normalization_atol < 0.0:
            raise ValueError("normalization_atol must be finite and nonnegative")
        if not -1.0 < self.minimum_geometry_alignment <= 1.0:
            raise ValueError("minimum_geometry_alignment must lie in (-1, 1]")
        if not 0.0 <= self.maximum_corner_spread_degrees <= 180.0:
            raise ValueError("maximum_corner_spread_degrees must lie in [0, 180]")
        if not 0.0 <= self.crease_angle_degrees <= 180.0:
            raise ValueError("crease_angle_degrees must lie in [0, 180]")


@dataclass(frozen=True)
class DirectorFieldQuality:
    """Whole-field diagnostics produced during one-time preparation."""

    minimum_geometry_alignment: float
    maximum_corner_spread_degrees: float
    minimum_smoothing_component_size: int
    maximum_smoothing_component_size: int
    smoothing_component_count: int
    smooth_interior_edge_count: int
    angular_crease_edge_count: int
    declared_crease_edge_count: int
    region_boundary_edge_count: int
    boundary_edge_count: int
    nonmanifold_edge_count: int


@dataclass(frozen=True)
class PreparedDirectorField:
    """Immutable per-element-corner directors and compact provenance codes."""

    directors: np.ndarray
    provenance_codes: np.ndarray
    element_quality: tuple[CornerDirectorQuality, ...]
    quality: DirectorFieldQuality
    diagnostics: tuple[str, ...]
    numeric_fingerprint: str

    def __post_init__(self) -> None:
        directors = np.array(self.directors, dtype=np.float64, order="C", copy=True)
        provenance_codes = np.array(self.provenance_codes, dtype=np.uint8, order="C", copy=True)
        if directors.ndim != 3 or directors.shape[1:] != (4, 3):
            raise ValueError("prepared directors must have shape (n_element, 4, 3)")
        if provenance_codes.shape != directors.shape[:2]:
            raise ValueError("director provenance codes must have shape (n_element, 4)")
        if len(self.element_quality) != directors.shape[0]:
            raise ValueError("element_quality must contain one record per element")
        unknown_codes = set(int(value) for value in np.unique(provenance_codes)) - set(
            DIRECTOR_PROVENANCE_FROM_NUMERIC_CODE
        )
        if unknown_codes:
            raise ValueError(f"unknown numeric director provenance codes: {sorted(unknown_codes)}")
        fingerprint = str(self.numeric_fingerprint).strip()
        if not fingerprint:
            raise ValueError("numeric director fingerprint must be nonempty")
        directors.setflags(write=False)
        provenance_codes.setflags(write=False)
        object.__setattr__(self, "directors", directors)
        object.__setattr__(self, "provenance_codes", provenance_codes)
        object.__setattr__(self, "element_quality", tuple(self.element_quality))
        object.__setattr__(self, "diagnostics", tuple(str(value) for value in self.diagnostics))
        object.__setattr__(self, "numeric_fingerprint", fingerprint)

    @property
    def provenance_labels(self) -> tuple[tuple[str, str, str, str], ...]:
        """Return cold-path labels corresponding to the compact numeric codes."""

        return tuple(
            tuple(DIRECTOR_PROVENANCE_FROM_NUMERIC_CODE[int(code)].value for code in row)
            for row in self.provenance_codes
        )


@dataclass(frozen=True)
class SourceCornerSamples:
    """Optional immutable UV/tangent samples retained for cold qualification.

    These arrays never replace FE interpolation or enter an element hot loop.
    Tangent vectors, when supplied, must be present as a linearly independent
    pair at every corner.
    """

    source_uv: np.ndarray | None = None
    source_tangent_1: np.ndarray | None = None
    source_tangent_2: np.ndarray | None = None
    numeric_fingerprint: str = field(init=False)

    def __post_init__(self) -> None:
        uv = _optional_corner_array(self.source_uv, trailing_size=2, label="source_uv")
        tangent_1 = _optional_corner_array(
            self.source_tangent_1,
            trailing_size=3,
            label="source_tangent_1",
        )
        tangent_2 = _optional_corner_array(
            self.source_tangent_2,
            trailing_size=3,
            label="source_tangent_2",
        )
        if (tangent_1 is None) != (tangent_2 is None):
            raise ValueError("source tangent 1 and source tangent 2 must be supplied together")
        present = tuple(array for array in (uv, tangent_1, tangent_2) if array is not None)
        if not present:
            raise ValueError("at least one source corner sample array is required")
        element_counts = {array.shape[0] for array in present}
        if len(element_counts) != 1:
            raise ValueError("source UV and tangent samples must have the same element count")
        if tangent_1 is not None and tangent_2 is not None:
            norm_1 = np.linalg.norm(tangent_1, axis=2)
            norm_2 = np.linalg.norm(tangent_2, axis=2)
            cross_norm = np.linalg.norm(np.cross(tangent_1, tangent_2), axis=2)
            if np.any(norm_1 <= np.finfo(np.float64).tiny) or np.any(
                norm_2 <= np.finfo(np.float64).tiny
            ):
                raise ValueError("source corner tangents must have nonzero length")
            relative_cross = cross_norm / (norm_1 * norm_2)
            if np.any(relative_cross <= 128.0 * np.finfo(np.float64).eps):
                raise ValueError("source corner tangent pairs must be linearly independent")
        object.__setattr__(self, "source_uv", uv)
        object.__setattr__(self, "source_tangent_1", tangent_1)
        object.__setattr__(self, "source_tangent_2", tangent_2)
        object.__setattr__(self, "numeric_fingerprint", numeric_payload_fingerprint(*present))

    @property
    def element_count(self) -> int:
        for array in (self.source_uv, self.source_tangent_1, self.source_tangent_2):
            if array is not None:
                return int(array.shape[0])
        raise RuntimeError("source corner samples were not initialized")


def _optional_corner_array(
    values: Sequence[Sequence[Sequence[float]]] | np.ndarray | None,
    *,
    trailing_size: int,
    label: str,
) -> np.ndarray | None:
    if values is None:
        return None
    array = np.asarray(values, dtype=np.float64)
    if array.shape == (4, trailing_size):
        array = array[None, :, :]
    if array.ndim != 3 or array.shape[1:] != (4, trailing_size) or array.shape[0] == 0:
        raise ValueError(
            f"{label} must have shape (n_element, 4, {trailing_size}), got {array.shape}"
        )
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{label} must be finite")
    made = np.array(array, dtype=np.float64, order="C", copy=True)
    made.setflags(write=False)
    return made


def _batch_corner_coordinates(values: Sequence[Sequence[Sequence[float]]] | np.ndarray) -> np.ndarray:
    corners = np.asarray(values, dtype=np.float64)
    if corners.shape == (4, 3):
        corners = corners[None, :, :]
    if corners.ndim != 3 or corners.shape[1:] != (4, 3):
        raise ValueError(f"corner coordinates must have shape (n_element, 4, 3), got {corners.shape}")
    if corners.shape[0] == 0:
        raise ValueError("at least one Q4 element is required")
    if not np.all(np.isfinite(corners)):
        raise ValueError("corner coordinates must be finite")
    return np.ascontiguousarray(corners)


def _orientation_signs(values: Sequence[int] | np.ndarray | None, count: int) -> np.ndarray:
    if values is None:
        signs = np.ones(count, dtype=np.int8)
    else:
        signs = np.asarray(values)
        if signs.shape != (count,):
            raise ValueError(f"face-use orientation signs must have shape ({count},)")
        if np.issubdtype(signs.dtype, np.bool_) or not np.issubdtype(signs.dtype, np.integer):
            raise ValueError("face-use orientation signs must be integers")
        signs = np.asarray(signs, dtype=np.int8)
    if not np.all(np.isin(signs, (-1, 1))):
        raise ValueError("face-use orientation signs must contain only +1 or -1")
    return signs


def validate_element_corner_directors(
    corner_coordinates: Sequence[Sequence[float]] | np.ndarray,
    reference_directors: Sequence[Sequence[float]] | np.ndarray,
    *,
    orientation_sign: int = 1,
    limits: DirectorValidationLimits = DirectorValidationLimits(),
) -> CornerDirectorQuality:
    """Fail closed unless one element's supplied directors meet the contract."""

    quality = corner_director_quality(
        corner_coordinates,
        reference_directors,
        orientation_sign=orientation_sign,
    )
    if quality.maximum_norm_error > limits.normalization_atol:
        raise ValueError(
            "reference directors must be normalized before solver handoff "
            f"(maximum norm error {quality.maximum_norm_error:.3e})"
        )
    if quality.minimum_geometry_alignment <= limits.minimum_geometry_alignment:
        raise ValueError(
            "reference director orientation is incompatible with the oriented Q4 geometry "
            f"(minimum alignment {quality.minimum_geometry_alignment:.6g})"
        )
    if quality.maximum_pair_angle_degrees > limits.maximum_corner_spread_degrees:
        raise ValueError(
            "reference director angular variation exceeds the element acceptance limit "
            f"({quality.maximum_pair_angle_degrees:.6g} degrees)"
        )
    return quality


def prepare_supplied_corner_directors(
    corner_coordinates: Sequence[Sequence[Sequence[float]]] | np.ndarray,
    reference_directors: Sequence[Sequence[Sequence[float]]] | np.ndarray,
    *,
    orientation_signs: Sequence[int] | np.ndarray | None = None,
    provenance: DirectorProvenanceCode | str = DirectorProvenanceCode.USER_SUPPLIED,
    limits: DirectorValidationLimits = DirectorValidationLimits(),
) -> PreparedDirectorField:
    """Validate already-normalized numeric directors without reconstructing them."""

    corners = _batch_corner_coordinates(corner_coordinates)
    directors = np.asarray(reference_directors, dtype=np.float64)
    if directors.shape == (4, 3) and corners.shape[0] == 1:
        directors = directors[None, :, :]
    if directors.shape != corners.shape:
        raise ValueError(f"reference directors must have shape {corners.shape}, got {directors.shape}")
    if not np.all(np.isfinite(directors)):
        raise ValueError("reference directors must be finite")
    signs = _orientation_signs(orientation_signs, corners.shape[0])
    try:
        provenance_code = DirectorProvenanceCode(provenance)
    except ValueError as exc:
        raise ValueError(f"unsupported director provenance code: {provenance!r}") from exc
    if provenance_code in {
        DirectorProvenanceCode.SHEET_AWARE_MESH_RECONSTRUCTION,
        DirectorProvenanceCode.LOCAL_ELEMENT_RECONSTRUCTION,
    }:
        raise ValueError("reconstruction provenance may only be emitted by reconstruct_corner_directors")

    element_quality = tuple(
        validate_element_corner_directors(
            corners[element],
            directors[element],
            orientation_sign=int(signs[element]),
            limits=limits,
        )
        for element in range(corners.shape[0])
    )
    code = DIRECTOR_PROVENANCE_NUMERIC_CODE[provenance_code]
    codes = np.full((corners.shape[0], 4), code, dtype=np.uint8)
    minimum_alignment = min(item.minimum_geometry_alignment for item in element_quality)
    maximum_spread = max(item.maximum_pair_angle_degrees for item in element_quality)
    quality = DirectorFieldQuality(
        minimum_geometry_alignment=minimum_alignment,
        maximum_corner_spread_degrees=maximum_spread,
        minimum_smoothing_component_size=1,
        maximum_smoothing_component_size=1,
        smoothing_component_count=4 * corners.shape[0],
        smooth_interior_edge_count=0,
        angular_crease_edge_count=0,
        declared_crease_edge_count=0,
        region_boundary_edge_count=0,
        boundary_edge_count=0,
        nonmanifold_edge_count=0,
    )
    return PreparedDirectorField(
        directors=directors,
        provenance_codes=codes,
        element_quality=element_quality,
        quality=quality,
        diagnostics=("validated_numeric_input", f"provenance={provenance_code.value}"),
        numeric_fingerprint=numeric_payload_fingerprint(corners, directors, signs),
    )


def _compact_indices(
    values: Sequence[int] | np.ndarray | None,
    count: int,
    *,
    label: str,
) -> np.ndarray:
    if values is None:
        return np.full(count, -1, dtype=np.int64)
    array = np.asarray(values)
    if array.shape != (count,):
        raise ValueError(f"{label} must have shape ({count},)")
    if np.issubdtype(array.dtype, np.bool_) or not np.issubdtype(array.dtype, np.integer):
        raise ValueError(f"{label} must contain compact integer indices")
    return np.asarray(array, dtype=np.int64)


def _edge_set(edges: Iterable[Sequence[int]], node_count: int, *, label: str) -> set[tuple[int, int]]:
    result: set[tuple[int, int]] = set()
    for raw_edge in edges:
        edge = tuple(int(value) for value in raw_edge)
        if len(edge) != 2 or edge[0] == edge[1]:
            raise ValueError(f"{label} entries must be pairs of distinct node indices")
        if min(edge) < 0 or max(edge) >= node_count:
            raise ValueError(f"{label} contains a node index outside the coordinate array")
        result.add((min(edge), max(edge)))
    return result


def _coerce_mesh(
    node_coordinates: Sequence[Sequence[float]] | np.ndarray,
    connectivity: Sequence[Sequence[int]] | np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    coordinates = np.asarray(node_coordinates, dtype=np.float64)
    if coordinates.ndim != 2 or coordinates.shape[1] != 3 or coordinates.shape[0] == 0:
        raise ValueError("node_coordinates must have shape (n_node, 3)")
    if not np.all(np.isfinite(coordinates)):
        raise ValueError("node_coordinates must be finite")
    elements = np.asarray(connectivity)
    if elements.ndim != 2 or elements.shape[1] != 4 or elements.shape[0] == 0:
        raise ValueError("connectivity must have shape (n_element, 4)")
    if np.issubdtype(elements.dtype, np.bool_) or not np.issubdtype(elements.dtype, np.integer):
        raise ValueError("connectivity must contain integer node indices")
    elements = np.asarray(elements, dtype=np.int64)
    if np.min(elements) < 0 or np.max(elements) >= coordinates.shape[0]:
        raise ValueError("connectivity contains a node index outside node_coordinates")
    if any(len(set(int(value) for value in row)) != 4 for row in elements):
        raise ValueError("each Q4 connectivity row must contain four distinct nodes")
    return np.ascontiguousarray(coordinates), np.ascontiguousarray(elements)


def reconstruct_corner_directors(
    node_coordinates: Sequence[Sequence[float]] | np.ndarray,
    connectivity: Sequence[Sequence[int]] | np.ndarray,
    *,
    part_indices: Sequence[int] | np.ndarray | None = None,
    sheet_indices: Sequence[int] | np.ndarray | None = None,
    continuity_indices: Sequence[int] | np.ndarray | None = None,
    orientation_signs: Sequence[int] | np.ndarray | None = None,
    crease_edges: Iterable[Sequence[int]] = (),
    declared_intersection_edges: Iterable[Sequence[int]] = (),
    limits: DirectorValidationLimits = DirectorValidationLimits(),
) -> PreparedDirectorField:
    """Reconstruct deterministic crease- and source-region-aware directors.

    Smoothing connectivity is created only across a manifold shared edge when
    the part, sheet, and declared continuity indices all agree, the edge is not
    explicitly blocked, and its oriented facet-normal jump does not exceed the
    crease limit.  Smoothing is then performed separately for every
    ``(element corner, global node)`` fan.  Consequently, one global node may
    produce several directors without duplicating its global rotation DOFs.
    """

    coordinates, elements = _coerce_mesh(node_coordinates, connectivity)
    element_count = elements.shape[0]
    signs = _orientation_signs(orientation_signs, element_count)
    parts = _compact_indices(part_indices, element_count, label="part_indices")
    sheets = _compact_indices(sheet_indices, element_count, label="sheet_indices")
    continuity = _compact_indices(continuity_indices, element_count, label="continuity_indices")
    declared_creases = _edge_set(crease_edges, coordinates.shape[0], label="crease_edges")
    intersections = _edge_set(
        declared_intersection_edges,
        coordinates.shape[0],
        label="declared_intersection_edges",
    )
    blocked_edges = declared_creases | intersections

    corners = coordinates[elements]
    geometry = tuple(q4_geometry_quality(corners[element]) for element in range(element_count))
    oriented_normals = np.asarray(
        [signs[element] * np.asarray(geometry[element].unit_normal) for element in range(element_count)],
        dtype=np.float64,
    )
    corner_weights = np.asarray(
        [
            geometry[element].area * np.asarray(geometry[element].corner_angles_radians)
            for element in range(element_count)
        ],
        dtype=np.float64,
    )

    edge_to_elements: dict[tuple[int, int], list[int]] = {}
    local_corner_by_node: list[dict[int, int]] = []
    for element, row in enumerate(elements):
        local_corner_by_node.append({int(node): local for local, node in enumerate(row)})
        for local in range(4):
            first = int(row[local])
            second = int(row[(local + 1) % 4])
            edge = (min(first, second), max(first, second))
            edge_to_elements.setdefault(edge, []).append(element)

    smooth_neighbors: dict[tuple[int, int], set[int]] = {
        (int(node), element): set()
        for element, row in enumerate(elements)
        for node in row
    }
    smooth_interior_edges = 0
    angular_creases = 0
    region_boundaries = 0
    boundary_edges = 0
    nonmanifold_edges = 0
    crease_cosine = math.cos(math.radians(limits.crease_angle_degrees))
    for edge, attached in edge_to_elements.items():
        if len(attached) == 1:
            boundary_edges += 1
            continue
        if len(attached) != 2:
            nonmanifold_edges += 1
            continue
        first, second = attached
        if edge in blocked_edges:
            continue
        first_region = (int(parts[first]), int(sheets[first]), int(continuity[first]))
        second_region = (int(parts[second]), int(sheets[second]), int(continuity[second]))
        if first_region != second_region:
            region_boundaries += 1
            continue
        alignment = float(np.dot(oriented_normals[first], oriented_normals[second]))
        if alignment < crease_cosine:
            angular_creases += 1
            continue
        smooth_interior_edges += 1
        for node in edge:
            smooth_neighbors[(node, first)].add(second)
            smooth_neighbors[(node, second)].add(first)

    directors = np.empty((element_count, 4, 3), dtype=np.float64)
    component_sizes = np.empty((element_count, 4), dtype=np.int64)
    smoothing_component_count = 0
    incident_elements: dict[int, set[int]] = {}
    for element, row in enumerate(elements):
        for node in row:
            incident_elements.setdefault(int(node), set()).add(element)
    for node, incident in incident_elements.items():
        remaining = set(incident)
        while remaining:
            smoothing_component_count += 1
            seed = min(remaining)
            component: set[int] = set()
            pending = [seed]
            while pending:
                candidate = pending.pop()
                if candidate in component:
                    continue
                component.add(candidate)
                pending.extend(smooth_neighbors[(node, candidate)] - component)
            remaining.difference_update(component)

            weighted_normals: list[np.ndarray] = []
            for candidate in sorted(component):
                candidate_local = local_corner_by_node[candidate][node]
                weighted_normals.append(
                    corner_weights[candidate, candidate_local] * oriented_normals[candidate]
                )
            averaged = np.asarray(
                [math.fsum(float(vector[axis]) for vector in weighted_normals) for axis in range(3)],
                dtype=np.float64,
            )
            averaged_norm = float(np.linalg.norm(averaged))
            if not math.isfinite(averaged_norm) or averaged_norm <= np.finfo(np.float64).tiny:
                raise ValueError("smooth director fan has a zero or unresolved weighted normal")
            director = averaged / averaged_norm
            for candidate in component:
                candidate_local = local_corner_by_node[candidate][node]
                directors[candidate, candidate_local] = director
                component_sizes[candidate, candidate_local] = len(component)

    element_quality = tuple(
        validate_element_corner_directors(
            corners[element],
            directors[element],
            orientation_sign=int(signs[element]),
            limits=limits,
        )
        for element in range(element_count)
    )
    has_source_regions = any(value is not None for value in (part_indices, sheet_indices, continuity_indices))
    provenance = (
        DirectorProvenanceCode.SHEET_AWARE_MESH_RECONSTRUCTION
        if has_source_regions
        else DirectorProvenanceCode.LOCAL_ELEMENT_RECONSTRUCTION
    )
    provenance_codes = np.full(
        (element_count, 4),
        DIRECTOR_PROVENANCE_NUMERIC_CODE[provenance],
        dtype=np.uint8,
    )
    field_quality = DirectorFieldQuality(
        minimum_geometry_alignment=min(item.minimum_geometry_alignment for item in element_quality),
        maximum_corner_spread_degrees=max(item.maximum_pair_angle_degrees for item in element_quality),
        minimum_smoothing_component_size=int(np.min(component_sizes)),
        maximum_smoothing_component_size=int(np.max(component_sizes)),
        smoothing_component_count=smoothing_component_count,
        smooth_interior_edge_count=smooth_interior_edges,
        angular_crease_edge_count=angular_creases,
        declared_crease_edge_count=len(blocked_edges),
        region_boundary_edge_count=region_boundaries,
        boundary_edge_count=boundary_edges,
        nonmanifold_edge_count=nonmanifold_edges,
    )
    diagnostics = (
        "numeric_mesh_only",
        "element_corner_storage",
        f"provenance={provenance.value}",
        f"smooth_edges={smooth_interior_edges}",
        f"blocked_edges={len(blocked_edges)}",
        f"nonmanifold_edges={nonmanifold_edges}",
    )
    return PreparedDirectorField(
        directors=directors,
        provenance_codes=provenance_codes,
        element_quality=element_quality,
        quality=field_quality,
        diagnostics=diagnostics,
        numeric_fingerprint=numeric_payload_fingerprint(
            coordinates,
            elements,
            signs,
            parts,
            sheets,
            continuity,
            np.asarray(sorted(blocked_edges), dtype=np.int64).reshape((-1, 2)),
            directors,
        ),
    )
