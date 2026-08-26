"""Independent numerical reference for the flat linear MITC3+ companion.

This research-only module is an independent transcription of the equation map
bound in ``e4_pl_s3_formulation_contract.json``.  It intentionally imports no
ANYsolver module and shares no producer helper, cache, or serialized state.
The reference exposes the uncondensed physical operator before the two bubble
rotations are eliminated, the bubble Schur complement, the barycentric PL
blocks, and the complete 23-coordinate saddle operator.

The module is a binary64 reference, not the independent exact oracle and not a
continuous-domain interval certificate.  Those are separate qualification
artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

import numpy as np


REFERENCE_IMPLEMENTATION_ID = "INDEPENDENT_MITC3_PLUS_LINEAR_BINARY64_V1"
BUBBLE_SCALE = 27.0
TYING_OFFSET = 1.0e-4

TYING_POINTS: Mapping[str, tuple[float, float]] = {
    "A": (1.0 / 6.0, 2.0 / 3.0),
    "B": (2.0 / 3.0, 1.0 / 6.0),
    "C": (1.0 / 6.0, 1.0 / 6.0),
    "D": (1.0 / 3.0 + TYING_OFFSET, 1.0 / 3.0 - 2.0 * TYING_OFFSET),
    "E": (1.0 / 3.0 - 2.0 * TYING_OFFSET, 1.0 / 3.0 + TYING_OFFSET),
    "F": (1.0 / 3.0 + TYING_OFFSET, 1.0 / 3.0 + TYING_OFFSET),
}

SEVEN_POINT_RULE: tuple[tuple[float, float, float], ...] = (
    (1.0 / 3.0, 1.0 / 3.0, 0.1125),
    (0.470142064105115, 0.470142064105115, 0.066197076394253),
    (0.059715871789770, 0.470142064105115, 0.066197076394253),
    (0.470142064105115, 0.059715871789770, 0.066197076394253),
    (0.101286507323456, 0.101286507323456, 0.062969590272414),
    (0.797426985353087, 0.101286507323456, 0.062969590272414),
    (0.101286507323456, 0.797426985353087, 0.062969590272414),
)

PHYSICAL_EXTERNAL_INDICES = np.asarray(
    [6 * node + component for node in range(3) for component in range(5)],
    dtype=np.intp,
)


@dataclass(frozen=True)
class LinearReferenceBlocks:
    """Complete independently reconstructed local linear block set."""

    uncondensed_physical: np.ndarray
    bubble_block: np.ndarray
    bubble_map: np.ndarray
    condensed_physical_15: np.ndarray
    physical_local_18: np.ndarray
    pl_constraint: np.ndarray
    pl_multiplier_gram: np.ndarray
    pl_local_18: np.ndarray
    total_local_18: np.ndarray
    full_saddle_23: np.ndarray
    k_d: float


def _finite_matrix(value: Sequence[Sequence[float]], shape: tuple[int, int], name: str) -> np.ndarray:
    matrix = np.asarray(value, dtype=np.float64)
    if matrix.shape != shape or not np.all(np.isfinite(matrix)):
        raise ValueError(f"{name} must be a finite {shape[0]}x{shape[1]} matrix")
    return matrix


def _geometry(local_nodes: Sequence[Sequence[float]]) -> tuple[np.ndarray, np.ndarray, float]:
    local = _finite_matrix(local_nodes, (3, 2), "local_nodes")
    jacobian = np.asarray(
        (
            (local[1, 0] - local[0, 0], local[1, 1] - local[0, 1]),
            (local[2, 0] - local[0, 0], local[2, 1] - local[0, 1]),
        ),
        dtype=np.float64,
    )
    determinant = float(jacobian[0, 0] * jacobian[1, 1] - jacobian[0, 1] * jacobian[1, 0])
    if not math.isfinite(determinant) or abs(determinant) <= np.finfo(np.float64).tiny:
        raise ValueError("local_nodes define a singular triangle")
    inverse = np.asarray(
        (
            (jacobian[1, 1], -jacobian[0, 1]),
            (-jacobian[1, 0], jacobian[0, 0]),
        ),
        dtype=np.float64,
    ) / determinant
    return local, inverse, determinant


def invariant_drill_scale(membrane_matrix: Sequence[Sequence[float]]) -> float:
    """Evaluate one half of lambda_min(P.T A P, diag(2, 1/2))."""

    membrane = _finite_matrix(membrane_matrix, (3, 3), "membrane_matrix")
    membrane = 0.5 * (membrane + membrane.T)
    if float(np.linalg.eigvalsh(membrane)[0]) <= 0.0:
        raise ValueError("membrane_matrix must be positive definite")
    projector = np.asarray(((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0)))
    metric_inverse_sqrt = np.asarray(((1.0 / math.sqrt(2.0), 0.0), (0.0, math.sqrt(2.0))))
    restricted = projector.T @ membrane @ projector
    canonical = metric_inverse_sqrt @ restricted @ metric_inverse_sqrt
    value = 0.5 * float(np.linalg.eigvalsh(0.5 * (canonical + canonical.T))[0])
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError("invariant drill scale must be positive")
    return value


def _reference_polynomials(r: float, s: float) -> tuple[np.ndarray, float, float, float]:
    shape = np.asarray((1.0 - r - s, r, s), dtype=np.float64)
    bubble = BUBBLE_SCALE * r * s * (1.0 - r - s)
    bubble_r = BUBBLE_SCALE * s * (1.0 - 2.0 * r - s)
    bubble_s = BUBBLE_SCALE * r * (1.0 - r - 2.0 * s)
    return shape, bubble, bubble_r, bubble_s


def _compatible(local: np.ndarray, inverse: np.ndarray, r: float, s: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    del local
    derivative_r = np.asarray((-1.0, 1.0, 0.0))
    derivative_s = np.asarray((-1.0, 0.0, 1.0))
    derivative_x = inverse[0, 0] * derivative_r + inverse[0, 1] * derivative_s
    derivative_y = inverse[1, 0] * derivative_r + inverse[1, 1] * derivative_s
    shape, bubble, bubble_r, bubble_s = _reference_polynomials(r, s)
    bubble_x = inverse[0, 0] * bubble_r + inverse[0, 1] * bubble_s
    bubble_y = inverse[1, 0] * bubble_r + inverse[1, 1] * bubble_s

    membrane = np.zeros((3, 17), dtype=np.float64)
    bending = np.zeros((3, 17), dtype=np.float64)
    shear = np.zeros((2, 17), dtype=np.float64)
    for node in range(3):
        base = 5 * node
        membrane[0, base] = derivative_x[node]
        membrane[1, base + 1] = derivative_y[node]
        membrane[2, base] = derivative_y[node]
        membrane[2, base + 1] = derivative_x[node]
        bending[0, base + 4] = derivative_x[node]
        bending[1, base + 3] = -derivative_y[node]
        bending[2, base + 4] = derivative_y[node]
        bending[2, base + 3] = -derivative_x[node]
        shear[0, base + 2] = derivative_x[node]
        shear[0, base + 4] = shape[node]
        shear[1, base + 2] = derivative_y[node]
        shear[1, base + 3] = -shape[node]
    bending[0, 16] = bubble_x
    bending[1, 15] = -bubble_y
    bending[2, 16] = bubble_y
    bending[2, 15] = -bubble_x
    shear[0, 16] = bubble
    shear[1, 15] = -bubble
    return membrane, bending, shear


def _covariant_sample(local: np.ndarray, inverse: np.ndarray, point: tuple[float, float]) -> np.ndarray:
    jacobian = np.linalg.inv(inverse)
    compatible = _compatible(local, inverse, *point)[2]
    return jacobian @ compatible


def _assumed_shear(local: np.ndarray, inverse: np.ndarray, r: float, s: float) -> np.ndarray:
    samples = {
        name: _covariant_sample(local, inverse, point)
        for name, point in TYING_POINTS.items()
    }
    constant_r = (
        (2.0 / 3.0) * (samples["B"][0] - 0.5 * samples["B"][1])
        + (1.0 / 3.0) * (samples["C"][0] + samples["C"][1])
    )
    constant_s = (
        (2.0 / 3.0) * (samples["A"][1] - 0.5 * samples["A"][0])
        + (1.0 / 3.0) * (samples["C"][0] + samples["C"][1])
    )
    twisting = samples["F"][0] - samples["D"][0] - samples["F"][1] + samples["E"][1]
    covariant = np.vstack(
        (
            constant_r + (twisting / 3.0) * (3.0 * s - 1.0),
            constant_s + (twisting / 3.0) * (1.0 - 3.0 * r),
        )
    )
    return inverse @ covariant


def _kinematic(local: np.ndarray, inverse: np.ndarray, r: float, s: float) -> np.ndarray:
    membrane, bending, _compatible_shear = _compatible(local, inverse, r, s)
    return np.vstack((membrane, bending, _assumed_shear(local, inverse, r, s)))


def _pl_blocks(inverse: np.ndarray, determinant: float, k_d: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    derivative_r = np.asarray((-1.0, 1.0, 0.0))
    derivative_s = np.asarray((-1.0, 0.0, 1.0))
    derivative_x = inverse[0, 0] * derivative_r + inverse[0, 1] * derivative_s
    derivative_y = inverse[1, 0] * derivative_r + inverse[1, 1] * derivative_s
    constraint = np.zeros((3, 18), dtype=np.float64)
    for row in range(3):
        constraint[row, 0::6] = 0.5 * derivative_y
        constraint[row, 1::6] = -0.5 * derivative_x
        constraint[row, 6 * row + 5] = 1.0
    gram = (abs(determinant) / 24.0) * np.asarray(
        ((2.0, 1.0, 1.0), (1.0, 2.0, 1.0), (1.0, 1.0, 2.0)),
        dtype=np.float64,
    )
    condensed = k_d * constraint.T @ gram @ constraint
    return constraint, gram, 0.5 * (condensed + condensed.T)


def reconstruct_linear_blocks(
    local_nodes: Sequence[Sequence[float]],
    constitutive: Sequence[Sequence[float]],
    membrane_matrix: Sequence[Sequence[float]],
    *,
    director_polarity: int = 1,
) -> LinearReferenceBlocks:
    """Reconstruct the complete local block hierarchy independently.

    ``constitutive`` is expressed in the selected physical-director
    convention.  ``director_polarity`` independently applies the corresponding
    kinematic curvature/shear map, matching the frozen transport contract.
    """

    local, inverse, determinant = _geometry(local_nodes)
    section = _finite_matrix(constitutive, (8, 8), "constitutive")
    section = 0.5 * (section + section.T)
    if float(np.linalg.eigvalsh(section)[0]) <= 0.0:
        raise ValueError("constitutive must be positive definite")
    if director_polarity not in (-1, 1):
        raise ValueError("director_polarity must be -1 or +1")
    reversal = np.eye(8)
    reversal[3:, 3:] *= float(director_polarity)

    uncondensed = np.zeros((17, 17), dtype=np.float64)
    for r, s, weight in SEVEN_POINT_RULE:
        operator = reversal @ _kinematic(local, inverse, r, s)
        uncondensed += abs(determinant) * weight * (operator.T @ section @ operator)
    uncondensed = 0.5 * (uncondensed + uncondensed.T)

    bubble_block = uncondensed[15:, 15:]
    if float(np.linalg.eigvalsh(bubble_block)[0]) <= 0.0:
        raise ValueError("bubble block must be positive definite")
    coupling = uncondensed[:15, 15:]
    bubble_map = -np.linalg.solve(bubble_block, coupling.T)
    condensed_15 = uncondensed[:15, :15] + coupling @ bubble_map
    condensed_15 = 0.5 * (condensed_15 + condensed_15.T)

    physical_18 = np.zeros((18, 18), dtype=np.float64)
    physical_18[np.ix_(PHYSICAL_EXTERNAL_INDICES, PHYSICAL_EXTERNAL_INDICES)] = condensed_15
    k_d = invariant_drill_scale(membrane_matrix)
    constraint, gram, pl_18 = _pl_blocks(inverse, determinant, k_d)
    total_18 = physical_18 + pl_18

    embedded = np.zeros((20, 20), dtype=np.float64)
    combined = np.concatenate((PHYSICAL_EXTERNAL_INDICES, np.asarray((18, 19))))
    embedded[np.ix_(combined, combined)] = uncondensed
    multiplier_coupling = np.zeros((20, 3), dtype=np.float64)
    multiplier_coupling[:18] = constraint.T @ gram
    saddle = np.zeros((23, 23), dtype=np.float64)
    saddle[:20, :20] = embedded
    saddle[:20, 20:] = multiplier_coupling
    saddle[20:, :20] = multiplier_coupling.T
    saddle[20:, 20:] = -gram / k_d

    return LinearReferenceBlocks(
        uncondensed_physical=uncondensed,
        bubble_block=bubble_block,
        bubble_map=bubble_map,
        condensed_physical_15=condensed_15,
        physical_local_18=physical_18,
        pl_constraint=constraint,
        pl_multiplier_gram=gram,
        pl_local_18=pl_18,
        total_local_18=total_18,
        full_saddle_23=saddle,
        k_d=k_d,
    )


__all__ = [
    "LinearReferenceBlocks",
    "REFERENCE_IMPLEMENTATION_ID",
    "SEVEN_POINT_RULE",
    "TYING_POINTS",
    "invariant_drill_scale",
    "reconstruct_linear_blocks",
]
