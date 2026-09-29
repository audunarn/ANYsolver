"""Experimental overlap-local conservative Q4/S3 gap bounds.

Instantaneous and swept bounds use original bilinear Q4 geometry. The swept
form assumes a linear path in physical nodal positions and is selected only
by the explicit development certificate profile.
"""

from __future__ import annotations

import numpy as np

from .q4_source_overlap import (
    _q4_corner_normals,
    projected_q4_source_face,
    q4_source_swept_gap_lower,
)

def _point(corners: np.ndarray, u: float, v: float) -> np.ndarray:
    return ((1-u)*(1-v)*corners[0] + u*(1-v)*corners[1]
            + u*v*corners[2] + (1-u)*v*corners[3])


def overlap_local_lower(source: np.ndarray, target: np.ndarray,
                        depth: int) -> tuple[float, int]:
    if depth < 0 or depth > 7:
        raise ValueError("experimental subdivision depth must be in [0, 7]")
    _, normal = projected_q4_source_face(source)
    tangent = source[1]-source[0]
    tangent -= float(tangent @ normal)*normal
    tangent /= np.linalg.norm(tangent)
    bitangent = np.cross(normal, tangent)
    frame = np.stack((tangent, bitangent), axis=1)
    axis = np.cross(target[1]-target[0], target[2]-target[0])
    if axis @ normal < 0.0:
        axis = -axis
    denominator = float(axis @ normal)
    if denominator <= 0.25*np.linalg.norm(axis):
        raise ValueError("target plane is nearly grazing")
    target_plane = target - ((target-source[0]) @ normal)[:, None]*normal
    target_2d = target_plane @ frame
    target_low = np.min(target_2d, axis=0)
    target_high = np.max(target_2d, axis=0)
    scale = max(1.0, float(np.max(np.abs(source))),
                float(np.max(np.abs(target))))
    margin = 1024.0*np.finfo(float).eps*scale
    visited = 0

    def recurse(u0: float, u1: float, v0: float, v1: float,
                remaining: int) -> float:
        nonlocal visited
        visited += 1
        corners = np.asarray((
            _point(source, u0, v0), _point(source, u1, v0),
            _point(source, u1, v1), _point(source, u0, v1),
        ))
        projected = corners - ((corners-source[0]) @ normal)[:, None]*normal
        box = projected @ frame
        if np.any(np.max(box, axis=0) + margin < target_low) or np.any(
                target_high + margin < np.min(box, axis=0)):
            return float("inf")
        if remaining == 0:
            # Target-plane height is affine in world position; source Q1
            # position is bilinear. Its minimum on a parametric rectangle is
            # therefore at one of these four corners, even if the projected
            # overlap occupies only a subset of the rectangle.
            numerator = float(np.min(corners @ axis)-np.max(target @ axis))
            return min(0.0, numerator/denominator) - margin
        um, vm = 0.5*(u0+u1), 0.5*(v0+v1)
        return min(recurse(*bounds, remaining-1) for bounds in (
            (u0, um, v0, vm), (um, u1, v0, vm),
            (um, u1, vm, v1), (u0, um, vm, v1),
        ))

    return recurse(0.0, 1.0, 0.0, 1.0, depth), visited
def overlap_local_swept_lower(
        source_start: np.ndarray, source_end: np.ndarray,
        target_start: np.ndarray, target_end: np.ndarray,
        depth: int) -> tuple[float, int]:
    """Experimental bound along a *linear physical nodal* Q4/S3 path.

    A fixed frame encloses moving projected boxes. The expansion bounds the
    lateral drift of a matched pair under the parent Q4 projection normal.
    Every retained source subrectangle is bounded over space and time; no
    quadrature sample or instantaneous-only clipping decides path safety.
    """
    if depth < 0 or depth > 7:
        raise ValueError("experimental subdivision depth must be in [0, 7]")
    a0, a1, b0, b1 = (np.asarray(item, dtype=float) for item in (
        source_start, source_end, target_start, target_end,
    ))
    if (a0.shape != (4, 3) or a1.shape != (4, 3)
            or b0.shape != (3, 3) or b1.shape != (3, 3)):
        raise ValueError("experimental sweep needs Q4/S3 endpoints")
    _, reference = projected_q4_source_face(a0)
    projected_q4_source_face(a1)
    tangent = a0[1]-a0[0]
    tangent -= float(tangent @ reference)*reference
    tangent /= np.linalg.norm(tangent)
    bitangent = np.cross(reference, tangent)
    frame = np.stack((tangent, bitangent), axis=1)
    scale = max(1.0, *(float(np.max(np.abs(item)))
                       for item in (a0, a1, b0, b1)))
    margin = 1024.0*np.finfo(float).eps*scale

    def normal(corners):
        return np.cross(corners[1]-corners[0], corners[3]-corners[0])

    def controls(start, middle, end):
        return np.stack((start, 2.0*middle-0.5*(start+end), end))

    parent = controls(normal(a0), normal(0.5*(a0+a1)), normal(a1))
    parent_height_min = float(np.min(parent @ reference))
    if parent_height_min <= 0.0:
        return q4_source_swept_gap_lower(a0, a1, b0, b1, reference), 1
    drift_slope = np.max(np.abs(parent @ frame), axis=0)/parent_height_min
    axis = np.cross(b0[1]-b0[0], b0[2]-b0[0])
    axis /= np.linalg.norm(axis)
    if axis @ reference < 0.0:
        axis = -axis

    def cone_cosine(values):
        maximum = float(np.max(np.linalg.norm(values, axis=-1)))
        return (float(np.min(values @ axis))/maximum
                if maximum > 0.0 else -float("inf"))

    parent_cosine = cone_cosine(parent)
    target_box = np.vstack((b0 @ frame, b1 @ frame))
    target_low, target_high = (np.min(target_box, axis=0),
                               np.max(target_box, axis=0))
    visited = 0

    def recurse(u0: float, u1: float, v0: float, v1: float,
                remaining: int) -> float:
        nonlocal visited
        visited += 1
        a_start = np.asarray((
            _point(a0, u0, v0), _point(a0, u1, v0),
            _point(a0, u1, v1), _point(a0, u0, v1),
        ))
        a_end = np.asarray((
            _point(a1, u0, v0), _point(a1, u1, v0),
            _point(a1, u1, v1), _point(a1, u0, v1),
        ))
        heights = np.r_[a_start @ reference, a_end @ reference]
        target_heights = np.r_[b0 @ reference, b1 @ reference]
        difference_max = max(
            abs(float(np.max(heights)-np.min(target_heights))),
            abs(float(np.min(heights)-np.max(target_heights))),
        )
        drift = difference_max*drift_slope + margin
        box = np.vstack((a_start @ frame, a_end @ frame))
        if np.any(np.max(box, axis=0) + drift < target_low) or np.any(
                target_high + drift < np.min(box, axis=0)):
            return float("inf")
        if remaining == 0:
            middle = 0.5*(a_start+a_end)
            first_normals = _q4_corner_normals(a_start)
            middle_normals = _q4_corner_normals(middle)
            last_normals = _q4_corner_normals(a_end)
            physical = np.stack([
                controls(first_normals[index], middle_normals[index],
                         last_normals[index])
                for index in range(4)
            ])
            if (parent_cosine <= 0.75
                    or any(cone_cosine(item) <= 0.75 for item in physical)):
                return q4_source_swept_gap_lower(
                    a_start, a_end, b0, b1, reference,
                )
            numerator = min(
                float(np.min((a_start[:, None]-b0[None, :]) @ axis)),
                float(np.min((a_end[:, None]-b1[None, :]) @ axis)),
            )
            return min(0.0, numerator/parent_cosine) - margin/parent_cosine
        um, vm = 0.5*(u0+u1), 0.5*(v0+v1)
        return min(recurse(*bounds, remaining-1) for bounds in (
            (u0, um, v0, vm), (um, u1, v0, vm),
            (um, u1, vm, v1), (u0, um, vm, v1),
        ))

    return recurse(0.0, 1.0, 0.0, 1.0, depth), visited
