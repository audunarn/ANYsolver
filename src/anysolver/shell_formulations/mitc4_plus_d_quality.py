"""Cold-path geometry and director quality checks for improved Q4 shells.

The routines in this module operate only on numeric finite-element input.  In
particular, they do not know about geometry documents, support-surface
objects, or a geometry-kernel tolerance policy.  Their tolerances are scaled
from the finite-element corner coordinates and machine precision.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import Iterable, Sequence

import numpy as np


@dataclass(frozen=True)
class Q4GeometryQuality:
    """Scale-aware reference-geometry metrics for one four-node shell."""

    area: float
    unit_normal: tuple[float, float, float]
    corner_angles_radians: tuple[float, float, float, float]
    minimum_edge_length: float
    maximum_edge_length: float
    warpage_angle_degrees: float
    characteristic_length: float
    minimum_surface_jacobian: float
    maximum_surface_jacobian: float
    minimum_jacobian_orientation: float


@dataclass(frozen=True)
class CornerDirectorQuality:
    """Compatibility metrics for the four directors of one Q4 element."""

    minimum_norm: float
    maximum_norm_error: float
    minimum_geometry_alignment: float
    maximum_pair_angle_degrees: float
    center_director_jacobian: float
    geometry: Q4GeometryQuality


def _q4_corners(corner_coordinates: Sequence[Sequence[float]] | np.ndarray) -> np.ndarray:
    corners = np.asarray(corner_coordinates, dtype=np.float64)
    if corners.shape != (4, 3):
        raise ValueError(f"Q4 corner coordinates must have shape (4, 3), got {corners.shape}")
    if not np.all(np.isfinite(corners)):
        raise ValueError("Q4 corner coordinates must be finite")
    return corners


def _unit(vector: np.ndarray, *, tolerance: float, label: str) -> tuple[np.ndarray, float]:
    norm = float(np.linalg.norm(vector))
    if not math.isfinite(norm) or norm <= tolerance:
        raise ValueError(f"{label} has zero or numerically unresolved length")
    return vector / norm, norm


def q4_area_vector(corner_coordinates: Sequence[Sequence[float]] | np.ndarray) -> np.ndarray:
    """Return the translation-invariant oriented area vector of a Q4.

    The cross-diagonal form is the sum of the two common triangle area
    vectors.  It remains meaningful for a valid warped quadrilateral and does
    not form cross products of absolute global positions.
    """

    corners = _q4_corners(corner_coordinates)
    return 0.5 * np.cross(corners[2] - corners[0], corners[3] - corners[1])


def q4_corner_angles(corner_coordinates: Sequence[Sequence[float]] | np.ndarray) -> np.ndarray:
    """Return the four unsigned corner angles in radians."""

    corners = _q4_corners(corner_coordinates)
    edge_lengths = np.linalg.norm(np.roll(corners, -1, axis=0) - corners, axis=1)
    scale = max(float(np.max(edge_lengths)), 1.0)
    tolerance = 64.0 * np.finfo(np.float64).eps * scale
    if np.any(edge_lengths <= tolerance):
        raise ValueError("Q4 has a zero or numerically unresolved edge")

    angles = np.empty(4, dtype=np.float64)
    for corner in range(4):
        previous = corners[(corner - 1) % 4] - corners[corner]
        following = corners[(corner + 1) % 4] - corners[corner]
        previous /= np.linalg.norm(previous)
        following /= np.linalg.norm(following)
        cosine = float(np.clip(np.dot(previous, following), -1.0, 1.0))
        angles[corner] = math.acos(cosine)
    return angles


def q4_geometry_quality(
    corner_coordinates: Sequence[Sequence[float]] | np.ndarray,
) -> Q4GeometryQuality:
    """Validate one Q4 and return FE-scale geometry metrics."""

    corners = _q4_corners(corner_coordinates)
    edges = np.roll(corners, -1, axis=0) - corners
    edge_lengths = np.linalg.norm(edges, axis=1)
    maximum_edge = float(np.max(edge_lengths))
    characteristic_length = max(maximum_edge, float(np.ptp(corners, axis=0).max()))
    if not math.isfinite(characteristic_length) or characteristic_length <= 0.0:
        raise ValueError("Q4 has no finite characteristic length")
    length_tolerance = 64.0 * np.finfo(np.float64).eps * characteristic_length
    minimum_edge = float(np.min(edge_lengths))
    if minimum_edge <= length_tolerance:
        raise ValueError("Q4 has a zero or numerically unresolved edge")

    area_vector = q4_area_vector(corners)
    area_tolerance = 128.0 * np.finfo(np.float64).eps * characteristic_length**2
    unit_normal, _projected_area = _unit(area_vector, tolerance=area_tolerance, label="Q4 area vector")

    triangle_a = np.cross(corners[1] - corners[0], corners[2] - corners[0])
    triangle_b = np.cross(corners[2] - corners[0], corners[3] - corners[0])
    triangle_a_unit, triangle_a_twice_area = _unit(
        triangle_a, tolerance=area_tolerance, label="first Q4 triangle"
    )
    triangle_b_unit, triangle_b_twice_area = _unit(
        triangle_b, tolerance=area_tolerance, label="second Q4 triangle"
    )
    warpage_cosine = float(np.clip(np.dot(triangle_a_unit, triangle_b_unit), -1.0, 1.0))

    evaluation_points = (
        (-1.0, -1.0),
        (1.0, -1.0),
        (1.0, 1.0),
        (-1.0, 1.0),
        (0.0, 0.0),
        *(
            (xi, eta)
            for xi in (-1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0))
            for eta in (-1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0))
        ),
    )
    jacobians: list[float] = []
    jacobian_orientations: list[float] = []
    for xi, eta in evaluation_points:
        derivative_xi = 0.25 * np.asarray((-(1.0 - eta), 1.0 - eta, 1.0 + eta, -(1.0 + eta)))
        derivative_eta = 0.25 * np.asarray((-(1.0 - xi), -(1.0 + xi), 1.0 + xi, 1.0 - xi))
        covariant_xi = derivative_xi @ corners
        covariant_eta = derivative_eta @ corners
        jacobian_vector = np.cross(covariant_xi, covariant_eta)
        jacobian = float(np.linalg.norm(jacobian_vector))
        signed_jacobian = float(np.dot(jacobian_vector, unit_normal))
        if not math.isfinite(jacobian) or signed_jacobian <= area_tolerance:
            raise ValueError("Q4 surface Jacobian is zero, unresolved, or reverses orientation")
        jacobians.append(jacobian)
        jacobian_orientations.append(signed_jacobian / jacobian)

    return Q4GeometryQuality(
        area=0.5 * (triangle_a_twice_area + triangle_b_twice_area),
        unit_normal=tuple(float(value) for value in unit_normal),
        corner_angles_radians=tuple(float(value) for value in q4_corner_angles(corners)),
        minimum_edge_length=minimum_edge,
        maximum_edge_length=maximum_edge,
        warpage_angle_degrees=math.degrees(math.acos(warpage_cosine)),
        characteristic_length=characteristic_length,
        minimum_surface_jacobian=min(jacobians),
        maximum_surface_jacobian=max(jacobians),
        minimum_jacobian_orientation=min(jacobian_orientations),
    )


def corner_director_quality(
    corner_coordinates: Sequence[Sequence[float]] | np.ndarray,
    reference_directors: Sequence[Sequence[float]] | np.ndarray,
) -> CornerDirectorQuality:
    """Return director metrics in the finalized element-connectivity frame.

    Source face-use orientation is deliberately absent here.  The upstream
    adapter has already used it to choose the element node order.  The
    continuum reference Jacobian is positive only when the interpolated
    director follows the normal induced by that final connectivity.
    """

    geometry = q4_geometry_quality(corner_coordinates)
    corners = _q4_corners(corner_coordinates)
    directors = np.asarray(reference_directors, dtype=np.float64)
    if directors.shape != (4, 3):
        raise ValueError(f"reference directors must have shape (4, 3), got {directors.shape}")
    if not np.all(np.isfinite(directors)):
        raise ValueError("reference directors must be finite")
    norms = np.linalg.norm(directors, axis=1)
    if np.any(norms <= np.finfo(np.float64).tiny):
        raise ValueError("reference directors must have nonzero length")
    unit_directors = directors / norms[:, None]
    connectivity_normal = np.asarray(geometry.unit_normal)
    alignments = unit_directors @ connectivity_normal

    derivative_xi = 0.25 * np.asarray((-1.0, 1.0, 1.0, -1.0))
    derivative_eta = 0.25 * np.asarray((-1.0, -1.0, 1.0, 1.0))
    covariant_xi = derivative_xi @ corners
    covariant_eta = derivative_eta @ corners
    center_director = np.mean(unit_directors, axis=0)
    center_director_jacobian = float(
        np.dot(np.cross(covariant_xi, covariant_eta), center_director)
    )

    maximum_angle = 0.0
    for first in range(4):
        for second in range(first + 1, 4):
            cosine = float(np.clip(np.dot(unit_directors[first], unit_directors[second]), -1.0, 1.0))
            maximum_angle = max(maximum_angle, math.degrees(math.acos(cosine)))

    return CornerDirectorQuality(
        minimum_norm=float(np.min(norms)),
        maximum_norm_error=float(np.max(np.abs(norms - 1.0))),
        minimum_geometry_alignment=float(np.min(alignments)),
        maximum_pair_angle_degrees=maximum_angle,
        center_director_jacobian=center_director_jacobian,
        geometry=geometry,
    )


def numeric_payload_fingerprint(*arrays: Iterable[float] | np.ndarray) -> str:
    """Hash numeric shape, dtype, and values for cache invalidation.

    Floating values are canonicalized as little-endian ``float64`` and integer
    values as little-endian ``int64``.  Preserving the numeric category avoids
    losing large compact indices through a float conversion.  Provenance
    metadata has its own canonical JSON hash.
    """

    digest = hashlib.sha256()
    digest.update(b"ANYsolver.numeric-payload.v1\0")
    for values in arrays:
        source = np.asarray(values)
        if np.issubdtype(source.dtype, np.bool_):
            array = np.ascontiguousarray(source, dtype=np.uint8)
            category = b"bool"
        elif np.issubdtype(source.dtype, np.integer):
            array = np.ascontiguousarray(source, dtype="<i8")
            category = b"int64"
        elif np.issubdtype(source.dtype, np.floating):
            array = np.ascontiguousarray(source, dtype="<f8")
            category = b"float64"
        else:
            raise TypeError("numeric payload fingerprint accepts only boolean, integer, or floating arrays")
        digest.update(category)
        digest.update(b"\0")
        digest.update(str(array.ndim).encode("ascii"))
        digest.update(b":")
        digest.update(",".join(str(int(size)) for size in array.shape).encode("ascii"))
        digest.update(b"\0")
        digest.update(array.tobytes(order="C"))
        digest.update(b"\0")
    return digest.hexdigest()
