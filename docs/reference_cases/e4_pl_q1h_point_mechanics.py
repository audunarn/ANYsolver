"""Point evaluator for the Q1H continuous-domain K/H campaign.

The evaluator is diagnostic until paired with outward interval coverage.  It
uses the frozen Q1F gauge and Q1Y3 binary64 candidate transcription and adds
the exact Q1F norm matrix ``H``.  No finite collection of calls to this module
is itself a domain certificate.
"""

from __future__ import annotations

import math
from typing import Mapping, Sequence

import numpy as np
from scipy import linalg

import e4_pl_q1b_assembled_producer as candidate


ALPHA_STAR = 1.0e-6
GAUSS = tuple(
    (r, s)
    for r, s in (
        (-1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
        (1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
        (1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)),
        (-1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)),
    )
)


def gauge_nodes(p: float, q: float, u: float, v: float) -> np.ndarray:
    return np.asarray(
        (
            (-1.0 - p + u, -q + v, 0.0),
            (1.0 - p - u, -q - v, 0.0),
            (1.0 + p + u, q + v, 0.0),
            (-1.0 + p - u, q - v, 0.0),
        ),
        dtype=float,
    )


def admissible_predicates(p: float, q: float, u: float, v: float) -> dict[str, float | bool]:
    """Evaluate the exact scalar forms of the frozen Q1F shape predicates."""

    centre_ratio_polynomial = q * q / (1.0 + p * p + q * q) ** 2
    variation_squared = ((u * q - p * v) ** 2 + v * v) / (q * q)
    determinant_minimum = q - abs(v) - abs(u * q - p * v)
    return {
        "centre_condition_margin": centre_ratio_polynomial - 16.0 / 289.0,
        "variation_margin": 1.0 / 8.0 - variation_squared,
        "determinant_minimum": determinant_minimum,
        "admissible_superset": bool(
            q > 0.0
            and centre_ratio_polynomial >= 16.0 / 289.0
            and variation_squared <= 1.0 / 8.0
        ),
    }


def _shape(r: float, s: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n = candidate._shape(r, s)
    nr, ns = candidate._shape_derivatives(r, s)
    nrs = np.asarray((1.0, -1.0, 1.0, -1.0), dtype=float) / 4.0
    return n, nr, ns, nrs


def _jacobian(local: np.ndarray, nr: np.ndarray, ns: np.ndarray) -> np.ndarray:
    return np.asarray(
        (
            (float(local[:, 0] @ nr), float(local[:, 0] @ ns)),
            (float(local[:, 1] @ nr), float(local[:, 1] @ ns)),
        ),
        dtype=float,
    )


def _shape_gradients_and_hessians(
    local: np.ndarray, r: float, s: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    _n, nr, ns, nrs = _shape(r, s)
    jacobian = _jacobian(local, nr, ns)
    determinant = float(np.linalg.det(jacobian))
    inverse_transpose = np.linalg.inv(jacobian).T
    gradients = np.zeros((4, 2), dtype=float)
    hessians = np.zeros((4, 2, 2), dtype=float)
    xrs = float(local[:, 0] @ nrs)
    yrs = float(local[:, 1] @ nrs)
    jacobian_r = np.asarray(((0.0, xrs), (0.0, yrs)), dtype=float)
    jacobian_s = np.asarray(((xrs, 0.0), (yrs, 0.0)), dtype=float)
    inverse = np.linalg.inv(jacobian)
    for node in range(4):
        natural = np.asarray((nr[node], ns[node]), dtype=float)
        gradient = inverse_transpose @ natural
        gradients[node] = gradient
        natural_r = np.asarray((0.0, nrs[node]), dtype=float)
        natural_s = np.asarray((nrs[node], 0.0), dtype=float)
        gradient_r = inverse_transpose @ (
            natural_r - jacobian_r.T @ gradient
        )
        gradient_s = inverse_transpose @ (
            natural_s - jacobian_s.T @ gradient
        )
        hessians[node] = np.column_stack((gradient_r, gradient_s)) @ inverse
    return gradients[:, 0], gradients[:, 1], hessians, determinant


def _embed_physical(matrix20: np.ndarray) -> np.ndarray:
    result = np.zeros((matrix20.shape[0], 24), dtype=float)
    for node in range(4):
        result[:, 6 * node : 6 * node + 5] = matrix20[:, 5 * node : 5 * node + 5]
    return result


def norm_matrix(nodes: Sequence[Sequence[float]], thickness: float = 2.0 / 3.0) -> np.ndarray:
    coordinates = np.asarray(nodes, dtype=float)
    _frame, local = candidate._frame(coordinates)
    coefficients = candidate._coefficients(local)
    constitutive = candidate._constitutive(thickness)
    shear_modulus = 6.0
    rows: list[tuple[float, np.ndarray, np.ndarray, np.ndarray]] = []
    area = 0.0
    for r, s in GAUSS:
        n = candidate._shape(r, s)
        nx, ny, hessians, determinant = _shape_gradients_and_hessians(local, r, s)
        compatible = _embed_physical(candidate._compatible(local, coefficients, r, s))
        delta = np.zeros((1, 24), dtype=float)
        delta_x = np.zeros((1, 24), dtype=float)
        delta_y = np.zeros((1, 24), dtype=float)
        for node in range(4):
            base = 6 * node
            delta[0, base] = 0.5 * ny[node]
            delta[0, base + 1] = -0.5 * nx[node]
            delta[0, base + 5] = n[node]
            delta_x[0, base] = 0.5 * hessians[node, 1, 0]
            delta_x[0, base + 1] = -0.5 * hessians[node, 0, 0]
            delta_x[0, base + 5] = nx[node]
            delta_y[0, base] = 0.5 * hessians[node, 1, 1]
            delta_y[0, base + 1] = -0.5 * hessians[node, 0, 1]
            delta_y[0, base + 5] = ny[node]
        rows.append((determinant, compatible, delta, np.vstack((delta_x, delta_y))))
        area += determinant

    result = np.zeros((24, 24), dtype=float)
    for determinant, compatible, delta, gradient_delta in rows:
        result += determinant * (
            compatible.T @ constitutive @ compatible
            + shear_modulus * thickness * (delta.T @ delta)
            + area * (gradient_delta.T @ gradient_delta)
        )
    transform = np.zeros((24, 24), dtype=float)
    frame, _local = candidate._frame(coordinates)
    for node in range(4):
        transform[6 * node : 6 * node + 3, 6 * node : 6 * node + 3] = frame
        transform[6 * node + 3 : 6 * node + 6, 6 * node + 3 : 6 * node + 6] = frame
    result = transform @ result @ transform.T
    return 0.5 * (result + result.T)


def rigid_matrix(nodes: Sequence[Sequence[float]]) -> np.ndarray:
    coordinates = np.asarray(nodes, dtype=float)
    result = np.zeros((24, 6), dtype=float)
    for node, coordinate in enumerate(coordinates):
        x, y, _z = coordinate
        base = 6 * node
        result[base + 0, 0] = 1.0
        result[base + 1, 1] = 1.0
        result[base + 2, 2] = 1.0
        result[base + 2, 3] = y
        result[base + 3, 3] = 1.0
        result[base + 2, 4] = -x
        result[base + 4, 4] = 1.0
        result[base + 0, 5] = -y
        result[base + 1, 5] = x
        result[base + 5, 5] = 1.0
    return result


def point_certificate(p: float, q: float, u: float, v: float) -> dict[str, float | bool]:
    nodes = gauge_nodes(p, q, u, v)
    components = candidate.local_components(nodes)
    stiffness = np.asarray(components["total"], dtype=float)
    norm = norm_matrix(nodes)
    quotient = np.arange(6, 24, dtype=int)
    stiffness_q = stiffness[np.ix_(quotient, quotient)]
    norm_q = norm[np.ix_(quotient, quotient)]
    delta_q = stiffness_q - ALPHA_STAR * norm_q
    rigid = rigid_matrix(nodes)
    scale_k = max(float(np.linalg.norm(stiffness, ord=2)), 1.0)
    scale_h = max(float(np.linalg.norm(norm, ord=2)), 1.0)
    generalized = linalg.eigvalsh(stiffness_q, norm_q)
    predicates = admissible_predicates(p, q, u, v)
    return {
        **predicates,
        "h_quotient_minimum": float(np.linalg.eigvalsh(norm_q)[0]),
        "delta_quotient_minimum": float(np.linalg.eigvalsh(delta_q)[0]),
        "coercivity_ratio": float(generalized[0]),
        "k_rigid_residual": float(np.linalg.norm(stiffness @ rigid, ord=np.inf)) / scale_k,
        "h_rigid_residual": float(np.linalg.norm(norm @ rigid, ord=np.inf)) / scale_h,
        "h_kernel_numeric": bool(np.linalg.eigvalsh(norm_q)[0] > 0.0),
        "coercive_numeric": bool(generalized[0] >= ALPHA_STAR),
    }


__all__ = [
    "ALPHA_STAR",
    "admissible_predicates",
    "gauge_nodes",
    "norm_matrix",
    "point_certificate",
    "rigid_matrix",
]
