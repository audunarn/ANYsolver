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
    _cross2,
    _q4_shape,
    _signed_area,
    _to_frame,
    planar_overlap_translation_derivatives,
    planar_projected_overlap,
    swept_planar_overlap_interval,
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


@dataclass(frozen=True)
class MovingGapCertificate:
    minimum_sampled_gap: float
    conservative_lower_gap: float
    tolerance_met: bool
    triangles_checked: int


@dataclass(frozen=True)
class MovingSweptGapBound:
    overlap_interval: tuple[float, float] | None
    conservative_lower_gap: float
    tolerance_certified: bool


def bound_swept_moving_mortar_gap(
        source_face: PlanarFace, target_face: PlanarFace,
        normal: np.ndarray,
        source_start: np.ndarray, source_end: np.ndarray,
        target_start: np.ndarray, target_end: np.ndarray,
        source_heights_start: np.ndarray, source_heights_end: np.ndarray,
        target_heights_start: np.ndarray, target_heights_end: np.ndarray,
        *, gap_tolerance: float) -> MovingSweptGapBound:
    """Certify a linear trial path against missed projected overlap.

    For each time in the swept overlap interval, the physical gap is at least
    plane separation plus the lowest source nodal height minus the highest
    target nodal height. Its minimum over the interval occurs at an endpoint:
    it is the minimum of affine source/target nodal-pair differences. A failed
    bound means unresolved, not confirmed penetration. Event subdivision is
    still required before this path can enter the nonlinear solver.
    """

    tolerance = float(gap_tolerance)
    if not np.isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("gap_tolerance must be finite and positive")
    direction = np.asarray(normal, dtype=float)
    if direction.shape != (3,) or not np.all(np.isfinite(direction)):
        raise ValueError("contact normal must be a finite 3-vector")
    magnitude = float(np.linalg.norm(direction))
    if magnitude <= 0.0:
        raise ValueError("contact normal must be nonzero")
    direction = direction / magnitude
    translations = tuple(np.asarray(value, dtype=float) for value in (
        source_start, source_end, target_start, target_end,
    ))
    heights = tuple(np.asarray(value, dtype=float) for value in (
        source_heights_start, source_heights_end,
        target_heights_start, target_heights_end,
    ))
    if (any(value.shape != (3,) or not np.all(np.isfinite(value))
            for value in translations)
            or any(value.shape != (size,) or not np.all(np.isfinite(value))
                   for value, size in zip(heights, (
                       len(source_face.corners), len(source_face.corners),
                       len(target_face.corners), len(target_face.corners),
                   )))):
        raise ValueError("swept moving mortar fields have invalid size or nonfinite values")
    for face in (source_face, target_face):
        face_normal = np.cross(face.corners[1] - face.corners[0],
                               face.corners[-1] - face.corners[0])
        face_normal /= np.linalg.norm(face_normal)
        if abs(float(face_normal @ direction)) < 1.0 - 1.0e-10:
            raise ValueError("swept moving mortar face must be parallel to contact plane")
    interval = swept_planar_overlap_interval(
        source_face, target_face, *translations,
    )
    if interval is None:
        return MovingSweptGapBound(None, float("inf"), True)

    reference_gap = float((source_face.corners[0] - target_face.corners[0])
                          @ direction)
    bounds = []
    for time in interval:
        source_translation = (1.0 - time) * translations[0] + time * translations[1]
        target_translation = (1.0 - time) * translations[2] + time * translations[3]
        source_height = (1.0 - time) * heights[0] + time * heights[1]
        target_height = (1.0 - time) * heights[2] + time * heights[3]
        bounds.append(
            reference_gap + float((source_translation - target_translation) @ direction)
            + float(np.min(source_height)) - float(np.max(target_height))
        )
    lower = min(bounds)
    return MovingSweptGapBound(interval, lower, lower >= -tolerance)


_TRIANGLE_RULE = (
    ((1.0/3.0, 1.0/3.0, 1.0/3.0), 0.225),
    ((0.059715871789770, 0.470142064105115, 0.470142064105115),
     0.132394152788506),
    ((0.470142064105115, 0.059715871789770, 0.470142064105115),
     0.132394152788506),
    ((0.470142064105115, 0.470142064105115, 0.059715871789770),
     0.132394152788506),
    ((0.797426985353087, 0.101286507323456, 0.101286507323456),
     0.125939180544827),
    ((0.101286507323456, 0.797426985353087, 0.101286507323456),
     0.125939180544827),
    ((0.101286507323456, 0.101286507323456, 0.797426985353087),
     0.125939180544827),
)


def _triangle_samples(triangle: tuple[np.ndarray, np.ndarray, np.ndarray],
                      area: float):
    for bary, relative_weight in _TRIANGLE_RULE:
        point = sum(coefficient * vertex
                    for coefficient, vertex in zip(bary, triangle))
        yield point, area * relative_weight


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
        for point, weight in _triangle_samples(triangle, area):
            shape_a = overlap.shape_values(moved_a, point)
            shape_b = overlap.shape_values(moved_b, point)
            gap = float(direction @ (
                shape_a @ moved_a.corners - shape_b @ moved_b.corners
            ) + shape_a @ height_a - shape_b @ height_b)
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


def _height_lipschitz(face: PlanarFace, heights: np.ndarray, overlap) -> float:
    xy = _to_frame(face.corners, overlap.origin,
                   overlap.tangent, overlap.binormal)
    if len(face.corners) == 3:
        _, gradient = overlap.shape_values_and_gradient(
            face, np.mean(face.corners, axis=0)
        )
        return float(np.linalg.norm(heights @ gradient))
    minimum_determinant = float("inf")
    maximum_jacobian_norm = 0.0
    maximum_height_derivative = 0.0
    determinant_sign = None
    for natural in ((-1.0, -1.0), (1.0, -1.0),
                    (1.0, 1.0), (-1.0, 1.0)):
        _shape, derivatives = _q4_shape(np.asarray(natural))
        jacobian = derivatives @ xy
        determinant = float(np.linalg.det(jacobian))
        sign = np.sign(determinant)
        if determinant_sign is None:
            determinant_sign = sign
        if sign != determinant_sign or determinant == 0.0:
            raise ValueError("projected Q4 Jacobian changes sign")
        minimum_determinant = min(minimum_determinant, abs(determinant))
        maximum_jacobian_norm = max(maximum_jacobian_norm,
                                    float(np.linalg.norm(jacobian)))
        maximum_height_derivative = max(
            maximum_height_derivative,
            float(np.linalg.norm(derivatives @ heights)),
        )
    return (maximum_jacobian_norm / minimum_determinant
            * maximum_height_derivative)


def certify_moving_mortar_gap(
        source_face: PlanarFace, target_face: PlanarFace,
        normal: np.ndarray, source_translation: np.ndarray,
        target_translation: np.ndarray,
        source_normal_dofs: np.ndarray, target_normal_dofs: np.ndarray,
        *, gap_tolerance: float, maximum_triangles: int,
        ) -> MovingGapCertificate:
    """Bound the represented normal gap over a moving convex overlap.

    A global shape-gradient bound limits unsampled gap variation in each
    triangle. Longest-edge subdivision continues until every lower bound meets
    the dimensional tolerance, a sampled violation is found, or the declared
    resource budget is exhausted. Failure to certify is never a passing gap.
    """

    tolerance = float(gap_tolerance)
    if not np.isfinite(tolerance) or tolerance <= 0.0:
        raise ValueError("gap_tolerance must be finite and positive")
    if type(maximum_triangles) is not int or maximum_triangles < 1:
        raise ValueError("maximum_triangles must be a positive integer")
    direction = np.asarray(normal, dtype=float)
    if direction.shape != (3,) or not np.all(np.isfinite(direction)):
        raise ValueError("contact normal must be a finite 3-vector")
    magnitude = float(np.linalg.norm(direction))
    if magnitude <= 0.0:
        raise ValueError("contact normal must be nonzero")
    direction = direction / magnitude
    translations = (np.asarray(source_translation, dtype=float),
                    np.asarray(target_translation, dtype=float))
    heights = (np.asarray(source_normal_dofs, dtype=float),
               np.asarray(target_normal_dofs, dtype=float))
    for name, face, translation, values in zip(
        ("source", "target"), (source_face, target_face), translations, heights
    ):
        if (translation.shape != (3,) or values.shape != (len(face.corners),)
                or not np.all(np.isfinite(translation))
                or not np.all(np.isfinite(values))):
            raise ValueError(f"moving mortar {name} field has invalid size or nonfinite values")
        face_normal = np.cross(face.corners[1] - face.corners[0],
                               face.corners[-1] - face.corners[0])
        face_normal /= np.linalg.norm(face_normal)
        if abs(float(face_normal @ direction)) < 1.0 - 1.0e-10:
            raise ValueError(f"moving mortar {name} face must be parallel to the contact plane")
    moved_a = PlanarFace(source_face.feature_id,
                         source_face.corners + translations[0])
    moved_b = PlanarFace(target_face.feature_id,
                         target_face.corners + translations[1])
    heights_a, heights_b = heights
    overlap = planar_projected_overlap(moved_a, moved_b)
    if overlap is None:
        return MovingGapCertificate(float("inf"), float("inf"), True, 0)
    lipschitz = (_height_lipschitz(moved_a, heights_a, overlap)
                 + _height_lipschitz(moved_b, heights_b, overlap))

    def gap(point: np.ndarray) -> float:
        shape_a = overlap.shape_values(moved_a, point)
        shape_b = overlap.shape_values(moved_b, point)
        return float(direction @ (
            shape_a @ moved_a.corners - shape_b @ moved_b.corners
        ) + shape_a @ heights_a - shape_b @ heights_b)

    polygon = overlap.polygon
    centre = np.mean(polygon, axis=0)
    pending = [
        (centre, polygon[index], polygon[(index + 1) % len(polygon)])
        for index in range(len(polygon))
    ]
    minimum_sampled = float("inf")
    conservative_lower = float("inf")
    checked = 0
    while pending:
        if checked >= maximum_triangles:
            return MovingGapCertificate(
                minimum_sampled, float("-inf"), False, checked,
            )
        triangle = pending.pop()
        checked += 1
        values = tuple(gap(point) for point in triangle)
        minimum_sampled = min(minimum_sampled, *values)
        edges = (
            float(np.linalg.norm(triangle[1] - triangle[0])),
            float(np.linalg.norm(triangle[2] - triangle[1])),
            float(np.linalg.norm(triangle[0] - triangle[2])),
        )
        longest = max(edges)
        bound = min(values) - lipschitz * longest
        if minimum_sampled < -tolerance:
            return MovingGapCertificate(minimum_sampled, bound, False, checked)
        if bound >= -tolerance:
            conservative_lower = min(conservative_lower, bound)
            continue
        index = int(np.argmax(edges))
        first, second = ((0, 1), (1, 2), (2, 0))[index]
        remaining = 3 - first - second
        midpoint = 0.5 * (triangle[first] + triangle[second])
        pending.append((triangle[first], midpoint, triangle[remaining]))
        pending.append((midpoint, triangle[second], triangle[remaining]))
    return MovingGapCertificate(minimum_sampled, conservative_lower, True, checked)


def _boundary_quadrature(subject: PlanarFace, clip_face: PlanarFace,
                         overlap) -> list[tuple[np.ndarray, np.ndarray]]:
    """Return (point, outward-normal times line weight) on clipped edges."""

    subject_xy = _to_frame(subject.corners, overlap.origin,
                           overlap.tangent, overlap.binormal)
    clip_xy = _to_frame(clip_face.corners, overlap.origin,
                        overlap.tangent, overlap.binormal)
    if _signed_area(subject_xy) < 0.0:
        subject_xy = subject_xy[::-1].copy()
    if _signed_area(clip_xy) < 0.0:
        clip_xy = clip_xy[::-1].copy()
    span = max(float(np.max(np.linalg.norm(subject_xy - subject_xy[0], axis=1))),
               float(np.max(np.linalg.norm(clip_xy - clip_xy[0], axis=1))))
    tolerance = 1.0e-12 * span * span
    gauss = (-np.sqrt(3.0 / 5.0), 0.0, np.sqrt(3.0 / 5.0))
    weights = (5.0 / 9.0, 8.0 / 9.0, 5.0 / 9.0)
    samples = []
    for index, start in enumerate(subject_xy):
        edge = subject_xy[(index + 1) % len(subject_xy)] - start
        lower, upper = 0.0, 1.0
        for clip_index, clip_start in enumerate(clip_xy):
            clip_edge = clip_xy[(clip_index + 1) % len(clip_xy)] - clip_start
            distance = _cross2(clip_edge, start - clip_start)
            slope = _cross2(clip_edge, edge)
            if abs(slope) <= tolerance:
                if distance < -tolerance:
                    lower, upper = 1.0, 0.0
                    break
                continue
            crossing = -distance / slope
            if slope > 0.0:
                lower = max(lower, crossing)
            else:
                upper = min(upper, crossing)
            if lower >= upper:
                break
        if upper <= lower:
            continue
        outward = edge[1] * overlap.tangent - edge[0] * overlap.binormal
        for abscissa, weight in zip(gauss, weights):
            fraction = 0.5 * (lower + upper + (upper - lower) * abscissa)
            xy = start + fraction * edge
            point = (overlap.origin + xy[0] * overlap.tangent
                     + xy[1] * overlap.binormal)
            samples.append((point, 0.5 * (upper - lower) * weight * outward))
    return samples


def _has_shared_edge_transition(source: PlanarFace, target: PlanarFace,
                                overlap) -> bool:
    """Detect positive-length coincident boundaries with nonunique transport."""

    first = _to_frame(source.corners, overlap.origin,
                      overlap.tangent, overlap.binormal)
    second = _to_frame(target.corners, overlap.origin,
                       overlap.tangent, overlap.binormal)
    scale = max(float(np.max(np.linalg.norm(first - first[0], axis=1))),
                float(np.max(np.linalg.norm(second - second[0], axis=1))))
    area_tolerance = 1.0e-12 * scale * scale
    length_tolerance = 1.0e-12 * scale
    for index, start in enumerate(first):
        edge = first[(index + 1) % len(first)] - start
        length = float(np.linalg.norm(edge))
        axis = edge / length
        for other_index, other_start in enumerate(second):
            other_edge = second[(other_index + 1) % len(second)] - other_start
            if (abs(_cross2(edge, other_edge)) > area_tolerance
                    or abs(_cross2(edge, other_start - start)) > area_tolerance):
                continue
            extent = sorted((float((other_start - start) @ axis),
                             float((other_start + other_edge - start) @ axis)))
            if min(length, extent[1]) - max(0.0, extent[0]) > length_tolerance:
                return True
    return False


def moving_mortar_translation_residual(
        source_face: PlanarFace, target_face: PlanarFace,
        normal: np.ndarray, stiffness: float,
        source_translation: np.ndarray, target_translation: np.ndarray,
        source_normal_dofs: np.ndarray, target_normal_dofs: np.ndarray,
        ) -> tuple[np.ndarray, np.ndarray]:
    """Differentiate the moving pressure-space potential by transport.

    This includes shape changes at fixed spatial points and motion of both
    polygon boundaries. The current integration rule is fixed; smooth-branch
    projection derivatives are represented by the shape gradients. Boundary
    integration has its own finite three-point line rule and must be refined
    before engineering qualification.
    """

    state = moving_mortar_state(
        source_face, target_face, normal, stiffness,
        source_translation, target_translation,
        source_normal_dofs, target_normal_dofs,
    )
    if state.overlap_area == 0.0:
        return np.zeros(3), np.zeros(3)
    direction = np.asarray(normal, dtype=float)
    direction = direction / np.linalg.norm(direction)
    moved_a = PlanarFace(source_face.feature_id,
                         source_face.corners + np.asarray(source_translation))
    moved_b = PlanarFace(target_face.feature_id,
                         target_face.corners + np.asarray(target_translation))
    overlap = planar_projected_overlap(moved_a, moved_b)
    if _has_shared_edge_transition(moved_a, moved_b, overlap):
        raise ValueError("shared-edge overlap transition needs a one-sided derivative")
    heights_a = np.asarray(source_normal_dofs, dtype=float)
    heights_b = np.asarray(target_normal_dofs, dtype=float)
    rows = len(heights_a)
    dm_a = np.zeros((rows, 3))
    dm_b = np.zeros((rows, 3))
    dW_a = np.zeros((rows, 3))
    dW_b = np.zeros((rows, 3))
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
        for point, weight in _triangle_samples(triangle, area):
            shape_a, gradient_a = overlap.shape_values_and_gradient(moved_a, point)
            shape_b, gradient_b = overlap.shape_values_and_gradient(moved_b, point)
            gap = float(direction @ (
                shape_a @ moved_a.corners - shape_b @ moved_b.corners
            ) + shape_a @ heights_a - shape_b @ heights_b)
            grad_gap_a = -(heights_a @ gradient_a)
            grad_gap_b = heights_b @ gradient_b
            dm_a -= weight * gradient_a
            dW_a += weight * (-gradient_a * gap
                              + shape_a[:, None] * grad_gap_a)
            dW_b += weight * shape_a[:, None] * grad_gap_b
    for point, weighted_outward in _boundary_quadrature(moved_a, moved_b, overlap):
        shape_a = overlap.shape_values(moved_a, point)
        shape_b = overlap.shape_values(moved_b, point)
        gap = float(direction @ (
            shape_a @ moved_a.corners - shape_b @ moved_b.corners
        ) + shape_a @ heights_a - shape_b @ heights_b)
        dm_a += np.outer(shape_a, weighted_outward)
        dW_a += gap * np.outer(shape_a, weighted_outward)
    for point, weighted_outward in _boundary_quadrature(moved_b, moved_a, overlap):
        shape_a = overlap.shape_values(moved_a, point)
        shape_b = overlap.shape_values(moved_b, point)
        gap = float(direction @ (
            shape_a @ moved_a.corners - shape_b @ moved_b.corners
        ) + shape_a @ heights_a - shape_b @ heights_b)
        dm_b += np.outer(shape_a, weighted_outward)
        dW_b += gap * np.outer(shape_a, weighted_outward)
    closed = (state.support > 0.0) & (state.normalized_gap < 0.0)
    pressure = float(stiffness) * state.normalized_gap[closed]
    source_tangent = np.sum(
        pressure[:, None] * dW_a[closed]
        - 0.5 * float(stiffness) * state.normalized_gap[closed, None] ** 2
        * dm_a[closed], axis=0,
    )
    target_tangent = np.sum(
        pressure[:, None] * dW_b[closed]
        - 0.5 * float(stiffness) * state.normalized_gap[closed, None] ** 2
        * dm_b[closed], axis=0,
    )
    source_normal = float(np.sum(state.normal_residual[:rows])) * direction
    target_normal = float(np.sum(state.normal_residual[rows:])) * direction
    return source_tangent + source_normal, target_tangent + target_normal


@dataclass(frozen=True)
class MovingMortarReducedSystem:
    state: MovingMortarState
    residual: np.ndarray
    tangent: np.ndarray
    relative_tangent_asymmetry: float


def moving_mortar_reduced_system(
        source_face: PlanarFace, target_face: PlanarFace,
        normal: np.ndarray, stiffness: float,
        source_translation: np.ndarray, target_translation: np.ndarray,
        source_normal_dofs: np.ndarray, target_normal_dofs: np.ndarray,
        *, difference_step: float) -> MovingMortarReducedSystem:
    """Differentiate the restricted moving mortar residual on a smooth branch.

    The first derivative uses transport of current pressure-space integrals;
    its tangent is a centred directional differentiation of that residual.
    This bounded control is not a deformable-shell tangent or public solver
    profile. The caller declares a dimensional perturbation and must refine
    it for its scale before using the result as evidence.
    """

    step = float(difference_step)
    if not np.isfinite(step) or step <= 0.0:
        raise ValueError("difference_step must be finite and positive")
    source = np.asarray(source_translation, dtype=float).reshape(3)
    target = np.asarray(target_translation, dtype=float).reshape(3)
    heights_a = np.asarray(source_normal_dofs, dtype=float).reshape(-1)
    heights_b = np.asarray(target_normal_dofs, dtype=float).reshape(-1)
    variables = np.r_[source, target, heights_a, heights_b]
    split = 6 + len(heights_a)

    def evaluate_at(values: np.ndarray):
        translation_a = values[:3]
        translation_b = values[3:6]
        normal_a = values[6:split]
        normal_b = values[split:]
        state = moving_mortar_state(
            source_face, target_face, normal, stiffness,
            translation_a, translation_b, normal_a, normal_b,
        )
        residual_a, residual_b = moving_mortar_translation_residual(
            source_face, target_face, normal, stiffness,
            translation_a, translation_b, normal_a, normal_b,
        )
        return state, np.r_[residual_a, residual_b, state.normal_residual]

    base_state, residual = evaluate_at(variables)
    tangent = np.zeros((len(variables), len(variables)), dtype=float)
    base_active = (base_state.support > 0.0) & (base_state.normalized_gap <= 0.0)
    for column in range(len(variables)):
        delta = np.zeros_like(variables)
        delta[column] = step
        plus_state, plus_residual = evaluate_at(variables + delta)
        minus_state, minus_residual = evaluate_at(variables - delta)
        if (not np.array_equal(
                (plus_state.support > 0.0) & (plus_state.normalized_gap <= 0.0),
                base_active)
                or not np.array_equal(
                    (minus_state.support > 0.0) & (minus_state.normalized_gap <= 0.0),
                    base_active)):
            raise ValueError("moving mortar tangent crosses an active-set transition")
        tangent[:, column] = (plus_residual - minus_residual) / (2.0 * step)
    scale = max(np.finfo(float).tiny, float(np.linalg.norm(tangent)))
    asymmetry = float(np.linalg.norm(tangent - tangent.T) / scale)
    return MovingMortarReducedSystem(base_state, residual, tangent, asymmetry)
