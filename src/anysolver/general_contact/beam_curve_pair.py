"""Local B3/B3 centreline distance geometry for distributed round-beam contact.

This work map is not a public pair-contact admission. It exposes all competing
closest points so an eventual line integrator can partition branch changes.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CurveProjection:
    distance: float
    minimizers: tuple[float, ...]
    stationary_candidates: tuple[float, ...]

    @property
    def unique(self) -> bool:
        return len(self.minimizers) == 1


@dataclass(frozen=True)
class CurveDistanceJet:
    gap: float
    source_parameter: float
    target_parameter: float
    gradient: np.ndarray
    hessian: np.ndarray
    target_branch: str


def _positions(value: np.ndarray, label: str) -> np.ndarray:
    positions = np.asarray(value, dtype=float)
    if positions.shape != (3, 3) or not np.all(np.isfinite(positions)):
        raise ValueError(f"{label} needs three finite B3 centreline positions")
    if float(np.linalg.norm(positions[2] - positions[0])) <= 0.0:
        raise ValueError(f"{label} B3 endpoints must be distinct")
    return positions


def _shape(t: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    return (
        np.array((2.0*t*t - 3.0*t + 1.0, 4.0*t - 4.0*t*t,
                  2.0*t*t - t)),
        np.array((4.0*t - 3.0, 4.0 - 8.0*t, 4.0*t - 1.0)),
        np.array((4.0, -8.0, 4.0)),
    )


def _curve(positions: np.ndarray, t: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    shape, first, second = _shape(t)
    return shape @ positions, first @ positions, second @ positions


def closest_on_b3(point: np.ndarray, target_positions: np.ndarray) -> CurveProjection:
    """Find all global closest stations on a quadratic B3 centreline."""

    point = np.asarray(point, dtype=float)
    target = _positions(target_positions, "target")
    if point.shape != (3,) or not np.all(np.isfinite(point)):
        raise ValueError("B3 projection point must be a finite three-vector")
    a = point - target[0]
    b = -3.0 * target[0] + 4.0 * target[1] - target[2]
    c = 2.0 * target[0] - 4.0 * target[1] + 2.0 * target[2]
    coefficients = np.array((
        float(a @ b),
        2.0 * float(a @ c) - float(b @ b),
        -3.0 * float(b @ c),
        -2.0 * float(c @ c),
    ))
    scale = float(np.max(np.abs(coefficients)))
    roots: list[float] = []
    if scale > 0.0:
        polynomial = np.polynomial.Polynomial(coefficients / scale).trim(
            tol=64.0 * np.finfo(float).eps,
        )
        for root in polynomial.roots():
            if abs(float(root.imag)) <= 1.0e-10 and 0.0 < float(root.real) < 1.0:
                roots.append(float(root.real))
    stations = [0.0]
    for root in sorted(roots):
        if root - stations[-1] > 1.0e-10:
            stations.append(root)
    stations.append(1.0)
    distances = [float(np.linalg.norm(point - _curve(target, t)[0]))
                 for t in stations]
    smallest = min(distances)
    length_scale = max(float(np.linalg.norm(b)), float(np.linalg.norm(c)),
                       float(np.linalg.norm(a)), smallest, np.finfo(float).tiny)
    threshold = 256.0 * np.finfo(float).eps * length_scale
    minimizers = tuple(float(t) for t, distance in zip(stations, distances)
                       if distance - smallest <= threshold)
    return CurveProjection(smallest, minimizers, tuple(stations))


def b3_distance_jet(source_positions: np.ndarray,
                    target_positions: np.ndarray, source_parameter: float,
                    radius: float, *, source_is_a: bool = True) -> CurveDistanceJet:
    """Differentiate the unique smooth closest-point branch in 18 nodal translations."""

    source = _positions(source_positions, "source")
    target = _positions(target_positions, "target")
    s = float(source_parameter)
    if not np.isfinite(s) or not 0.0 <= s <= 1.0:
        raise ValueError("B3 source parameter must lie in [0,1]")
    if not np.isfinite(radius) or radius <= 0.0:
        raise ValueError("combined round radius must be finite and positive")
    if type(source_is_a) is not bool:
        raise ValueError("source_is_a must be a boolean")
    source_shape = _shape(s)[0]
    source_position = source_shape @ source
    projection = closest_on_b3(source_position, target)
    if not projection.unique:
        raise ValueError("B3 projection has competing equal-distance minima")
    t = projection.minimizers[0]
    target_shape, target_shape_t, _target_shape_tt = _shape(t)
    target_position, target_tangent, target_second = _curve(target, t)
    separation = source_position - target_position
    distance = float(np.linalg.norm(separation))
    if distance <= 0.0:
        raise ValueError("coincident B3 centrelines cannot define a contact normal")
    normal = separation / distance
    projector = np.eye(3) - np.outer(normal, normal)
    coefficients = (np.r_[source_shape, -target_shape] if source_is_a
                    else np.r_[-target_shape, source_shape])
    coefficients_t = (np.r_[np.zeros(3), -target_shape_t] if source_is_a
                      else np.r_[-target_shape_t, np.zeros(3)])
    jacobian = np.hstack([value * np.eye(3) for value in coefficients])
    jacobian_t = np.hstack([value * np.eye(3) for value in coefficients_t])
    gradient = jacobian.T @ normal
    hessian = jacobian.T @ projector @ jacobian / distance
    branch = "endpoint" if t == 0.0 or t == 1.0 else "interior"
    if branch == "interior":
        distance_t = -target_tangent
        mixed = (jacobian_t.T @ normal
                 + jacobian.T @ projector @ distance_t / distance)
        curvature = (float(distance_t @ projector @ distance_t) / distance
                     - float(normal @ target_second))
        if curvature <= 0.0:
            raise ValueError("B3 closest-point branch lacks positive curvature")
        hessian -= np.outer(mixed, mixed) / curvature
    return CurveDistanceJet(
        distance - radius, s, t, gradient, hessian, branch,
    )
