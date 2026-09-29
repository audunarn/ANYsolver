"""Experimental overlap-local conservative Q4/S3 gap bounds.

Instantaneous and swept bounds use original bilinear Q4 geometry. The swept
form assumes a linear path in physical nodal positions and is selected only
by the explicit development certificate profile.
"""

from __future__ import annotations

import numpy as np

from .q4_source_overlap import (
    projected_q4_source_face,
)


def _outward(value, direction):
    return np.nextafter(value, direction)


def _interval(value):
    value = np.asarray(value, dtype=float)
    return value, value


def _add(a, b):
    return (_outward(a[0]+b[0], -np.inf),
            _outward(a[1]+b[1], np.inf))


def _neg(a):
    return -a[1], -a[0]


def _sub(a, b):
    return _add(a, _neg(b))


def _mul(a, b):
    products = np.stack((a[0]*b[0], a[0]*b[1],
                         a[1]*b[0], a[1]*b[1]))
    return (_outward(np.min(products, axis=0), -np.inf),
            _outward(np.max(products, axis=0), np.inf))


def _dot(a, b):
    products = _mul(a, b)
    value = (products[0][..., 0], products[1][..., 0])
    for index in (1, 2):
        value = _add(value, (products[0][..., index],
                             products[1][..., index]))
    return value


def _cross(a, b):
    values = []
    for j, k in ((1, 2), (2, 0), (0, 1)):
        values.append(_sub(
            _mul((a[0][..., j], a[1][..., j]),
                 (b[0][..., k], b[1][..., k])),
            _mul((a[0][..., k], a[1][..., k]),
                 (b[0][..., j], b[1][..., j]))))
    return tuple(np.stack([value[side] for value in values], axis=-1)
                 for side in (0, 1))


def _normal_controls_interval(start, end, corner=0,
                              start_error=0.0, end_error=0.0):
    # For affine edges e(t), f(t), the middle quadratic Bernstein
    # coefficient of e x f is (e0 x f1 + e1 x f0)/2.
    next_corner, previous_corner = ((corner+1) % len(start),
                                    (corner-1) % len(start))
    first_positions = _enclose_positions(start, start_error)
    last_positions = _enclose_positions(end, end_error)
    def at(positions, index):
        return positions[0][index], positions[1][index]
    e0 = _sub(at(first_positions, next_corner), at(first_positions, corner))
    f0 = _sub(at(first_positions, previous_corner), at(first_positions, corner))
    e1 = _sub(at(last_positions, next_corner), at(last_positions, corner))
    f1 = _sub(at(last_positions, previous_corner), at(last_positions, corner))
    first, last = _cross(e0, f0), _cross(e1, f1)
    middle = _mul(_add(_cross(e0, f1), _cross(e1, f0)), _interval(0.5))
    return tuple(np.stack((first[side], middle[side], last[side]))
                 for side in (0, 1))


def _norm_upper(a):
    magnitude = np.maximum(np.abs(a[0]), np.abs(a[1]))
    squared = _mul(_interval(magnitude), _interval(magnitude))
    total = _add(_add((squared[0][..., 0], squared[1][..., 0]),
                      (squared[0][..., 1], squared[1][..., 1])),
                 (squared[0][..., 2], squared[1][..., 2]))
    return _outward(np.sqrt(total[1]), np.inf)


def _positive_divide_upper(numerator, denominator):
    return _outward(numerator/denominator, np.inf)


def _enclose_positions(positions, error):
    error = np.broadcast_to(np.asarray(error, dtype=float), positions.shape)
    if not np.all(np.isfinite(error)) or np.any(error < 0.0):
        raise ValueError("swept endpoint enclosure must be finite and nonnegative")
    if not np.any(error):
        return _interval(positions)
    return (_outward(positions-error, -np.inf),
            _outward(positions+error, np.inf))

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
        depth: int, *, endpoint_errors=None) -> tuple[float, int]:
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
    errors = ((0.0,)*4 if endpoint_errors is None else endpoint_errors)
    if len(errors) != 4:
        raise ValueError("swept gap needs four endpoint enclosures")
    input_bounds = tuple(_enclose_positions(item, error)
                         for item, error in zip((a0, a1, b0, b1), errors))
    if (a0.shape != (4, 3) or a1.shape != (4, 3)
            or b0.shape != (3, 3) or b1.shape != (3, 3)
            or not all(np.all(np.isfinite(item)) for item in (a0, a1, b0, b1))):
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
    # Treat stored endpoint/frame floats as exact inputs to this bound.
    # Directed outward arithmetic encloses normal controls and denominators;
    # a positive rounded normal height alone cannot certify a grazing path.
    parent = _normal_controls_interval(a0, a1,
                                       start_error=errors[0], end_error=errors[1])
    if not all(np.all(np.isfinite(value)) for value in parent):
        return -float("inf"), 1
    parent_height_min = float(np.min(_dot(parent, _interval(reference))[0]))
    if not np.isfinite(parent_height_min) or parent_height_min <= 0.0:
        return -float("inf"), 1
    lateral = [_dot(parent, _interval(frame[:, axis_index]))
               for axis_index in (0, 1)]
    drift_slope = np.asarray([
        _positive_divide_upper(
            np.max(np.maximum(np.abs(value[0]), np.abs(value[1]))),
            parent_height_min) for value in lateral])
    if not np.all(np.isfinite(drift_slope)):
        return -float("inf"), 1
    axis = np.cross(b0[1]-b0[0], b0[2]-b0[0])
    axis_length = np.linalg.norm(axis)
    if not np.isfinite(axis_length) or axis_length <= 0.0:
        return -float("inf"), 1
    axis /= axis_length
    if axis @ reference < 0.0:
        axis = -axis

    axis_norm_upper = float(_norm_upper(_interval(axis)))

    def cone_cosine(values):
        maximum = float(np.max(_norm_upper(values)))
        denominator = _outward(maximum*axis_norm_upper, np.inf)
        numerator = float(np.min(_dot(values, _interval(axis))[0]))
        return (float(_outward(numerator/denominator, -np.inf))
                if np.isfinite(numerator) and np.isfinite(denominator)
                and denominator > 0.0 else -float("inf"))

    parent_cosine = cone_cosine(parent)
    physical_cosines = [cone_cosine(_normal_controls_interval(
        a0, a1, corner, errors[0], errors[1]))
                        for corner in range(4)]
    if parent_cosine <= 0.75 or min(physical_cosines) <= 0.75:
        return -float("inf"), 1
    target_endpoints = tuple(np.vstack((input_bounds[2][side],
                                       input_bounds[3][side]))
                             for side in (0, 1))
    target_box = [_dot(target_endpoints, _interval(frame[:, index]))
                  for index in (0, 1)]
    target_low = np.asarray([np.min(value[0]) for value in target_box])
    target_high = np.asarray([np.max(value[1]) for value in target_box])
    target_heights = _dot(target_endpoints, _interval(reference))
    if not all(np.all(np.isfinite(value))
               for bounds in (*target_box, target_heights) for value in bounds):
        return -float("inf"), 1
    # Dyadic subdivision coordinates through depth 7 have exact shape
    # coefficients. Seven rounded multiply/add operations evaluate _point;
    # gamma_8 bounds its componentwise error for the convex Q1 weights.
    unit = np.finfo(float).eps/2.0
    point_error = _outward((8*unit/(1-8*unit))*scale + np.maximum(
        np.max(np.broadcast_to(np.asarray(errors[0]), a0.shape), axis=0),
        np.max(np.broadcast_to(np.asarray(errors[1]), a1.shape), axis=0)), np.inf)
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
        endpoints = np.vstack((a_start, a_end))
        positions = (_outward(endpoints-point_error, -np.inf),
                     _outward(endpoints+point_error, np.inf))
        heights = _dot(positions, _interval(reference))
        difference_max = max(
            float(_outward(np.max(heights[1])-np.min(target_heights[0]), np.inf)),
            float(_outward(np.max(target_heights[1])-np.min(heights[0]), np.inf)),
        )
        drift = _outward(difference_max*drift_slope, np.inf)
        box = [_dot(positions, _interval(frame[:, index])) for index in (0, 1)]
        box_low = np.asarray([np.min(value[0]) for value in box])
        box_high = np.asarray([np.max(value[1]) for value in box])
        if np.any(_outward(box_high+drift, np.inf) < target_low) or np.any(
                _outward(target_high+drift, np.inf) < box_low):
            return float("inf")
        if remaining == 0:
            differences = _sub(
                (positions[0].reshape(2, 4, 3)[:, :, None],
                 positions[1].reshape(2, 4, 3)[:, :, None]),
                tuple(np.stack((input_bounds[2][side],
                                input_bounds[3][side]))[:, None, :]
                      for side in (0, 1)))
            numerator = float(np.min(_dot(differences, _interval(axis))[0]))
            denominator = _outward(parent_cosine*axis_norm_upper, -np.inf)
            if (not np.isfinite(numerator) or not np.isfinite(denominator)
                    or denominator <= 0.0):
                return -float("inf")
            return float(_outward(min(0.0, numerator)/denominator, -np.inf))
        um, vm = 0.5*(u0+u1), 0.5*(v0+v1)
        return min(recurse(*bounds, remaining-1) for bounds in (
            (u0, um, v0, vm), (um, u1, v0, vm),
            (um, u1, vm, v1), (u0, um, vm, v1),
        ))

    return recurse(0.0, 1.0, 0.0, 1.0, depth), visited
