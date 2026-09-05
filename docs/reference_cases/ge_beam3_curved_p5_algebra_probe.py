"""Preparatory algebra for an objective curved lift; no qualification authority.

The scalar complementary functional and reference Hessian are reconstructed
here from the P5 derivation. This module is not a production element, solver,
independent oracle, or formal runner. It imports no accepted beam mechanics.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import json
from typing import Any

import numpy as np


CANDIDATE = "CANDIDATE_GE_BEAM3_DC_CURVED_OBJECTIVE_LIFT_V1"
STUDY = "study_ge_beam3.curved_objective_lift_preparation_v1"
HALVES = ((0, 1), (1, 2))
S = np.diag((-1.0, 1.0, -1.0))
T3 = -S
T6 = np.kron(np.eye(2), T3)


def skew(vector: Any) -> np.ndarray:
    x, y, z = np.asarray(vector, dtype=float)
    return np.array(((0, -z, y), (z, 0, -x), (-y, x, 0)))


def rotation(vector: Any) -> np.ndarray:
    vector = np.asarray(vector, dtype=float)
    angle = np.linalg.norm(vector)
    cross = skew(vector)
    if angle < 1e-8:
        return np.eye(3) + np.sinc(angle / np.pi) * cross + (
            0.5 - angle**2 / 24.0 + angle**4 / 720.0
        ) * cross @ cross
    return np.eye(3) + np.sin(angle) / angle * cross + (
        (1 - np.cos(angle)) / angle**2
    ) * cross @ cross


def log_rotation(matrix: Any) -> np.ndarray:
    matrix = np.asarray(matrix, dtype=float)
    if matrix.shape != (3, 3) or not np.isfinite(matrix).all():
        raise ValueError("finite proper rotation required")
    if np.linalg.norm(matrix.T @ matrix - np.eye(3)) > 1e-11 or abs(
        np.linalg.det(matrix) - 1.0
    ) > 1e-11:
        raise ValueError("finite proper rotation required")
    angle = np.arccos(np.clip((np.trace(matrix) - 1) / 2, -1, 1))
    if angle >= 0.9 * np.pi:
        raise ValueError("relative rotation requires refinement or cutback")
    axial = np.array((matrix[2, 1]-matrix[1, 2], matrix[0, 2]-matrix[2, 0],
                      matrix[1, 0]-matrix[0, 1])) / 2
    factor = 1 + angle**2 / 6 + 7 * angle**4 / 360 if angle < 1e-5 else (
        angle / np.sin(angle)
    )
    return factor * axial


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False, ensure_ascii=True) + "\n").encode("ascii")


def validate_section(section: Any) -> np.ndarray:
    made = np.array(section, dtype=float, copy=True)
    if made.shape != (6, 6) or not np.isfinite(made).all():
        raise ValueError("section must be finite 6 by 6")
    if not np.array_equal(made, made.T):
        raise ValueError("probe section must be exactly symmetric")
    try:
        np.linalg.cholesky(made)
    except np.linalg.LinAlgError as exc:
        raise ValueError("positive definite section required") from exc
    return made


@dataclass(frozen=True)
class CellMetrics:
    force: np.ndarray
    compliance: np.ndarray
    coupling: np.ndarray
    # These arrays are diagnostics, not immutable production cache objects.


def metrics(reference: Any, section: Any, cell: int, order: int = 24) -> CellMetrics:
    section = validate_section(section)
    if cell not in (0, 1) or not 2 <= order <= 64:
        raise ValueError("probe cell/order outside registered diagnostic range")
    a, b, d = section[:3, :3], section[:3, 3:], section[3:, 3:]
    d_inverse = np.linalg.solve(d, np.eye(3))
    force = np.zeros((3, 3))
    compliance = np.zeros((6, 6))
    coupling = np.zeros((6, 3))
    stations, weights = np.polynomial.legendre.leggauss(order)
    for station, weight in zip(stations, weights):
        fraction = (station + 1) / 2
        xi = cell - 1 + fraction
        jacobian = reference.jacobian(xi)
        v = reference.frame(xi).T / jacobian
        l = np.hstack(((1-fraction)*np.eye(3), fraction*np.eye(3)))
        measure = weight * jacobian / 2
        force += measure * v.T @ (a - b @ d_inverse @ b.T) @ v
        compliance += measure * l.T @ d_inverse @ l
        coupling += measure * l.T @ d_inverse @ b.T @ v
    return CellMetrics(force, compliance, coupling)


def lift_position(reference: Any, positions: Any, cell_rotation: Any,
                  cell: int, fraction: float) -> np.ndarray:
    left, right = HALVES[cell]
    coords = reference.coordinates
    xi = cell - 1 + fraction
    interpolated_reference = (1-fraction)*coords[left] + fraction*coords[right]
    interpolated_current = (1-fraction)*positions[left] + fraction*positions[right]
    return interpolated_current + cell_rotation @ (
        reference.position(xi) - interpolated_reference
    )


def cell_coordinates(reference: Any, positions: Any, vertex_frames: Any,
                     cell_rotation: Any, cell: int) -> tuple[np.ndarray, np.ndarray]:
    left, right = HALVES[cell]
    coords, frames = reference.coordinates, reference.nodal_triads
    z = cell_rotation.T @ (positions[right]-positions[left]) - (coords[right]-coords[left])
    ell = np.concatenate((
        -log_rotation((cell_rotation @ frames[left]).T @ vertex_frames[left]),
        log_rotation((cell_rotation @ frames[right]).T @ vertex_frames[right]),
    ))
    return z, ell


def reduced_energy(reference: Any, section: Any, positions: Any,
                   vertex_frames: Any, cell_rotations: Any, order: int = 24
                   ) -> tuple[float, np.ndarray]:
    energy = 0.0
    moments = []
    for cell in (0, 1):
        data = metrics(reference, section, cell, order)
        z, ell = cell_coordinates(reference, positions, vertex_frames, cell_rotations[cell], cell)
        e = data.coupling @ z + ell
        m = np.linalg.solve(data.compliance, e)
        energy += (z @ data.force @ z + e @ m) / 2
        moments.append(m.reshape(2, 3))
    return float(energy), np.array(moments)


def mixed_energy(reference: Any, section: Any, positions: Any, vertex_frames: Any,
                 cell_rotations: Any, moments: Any, order: int = 24) -> float:
    """Reconstruct the uneliminated functional by station integration."""
    section = validate_section(section)
    d_inverse = np.linalg.solve(section[3:, 3:], np.eye(3))
    stations, weights = np.polynomial.legendre.leggauss(order)
    total = 0.0
    for cell in (0, 1):
        z, ell = cell_coordinates(reference, positions, vertex_frames, cell_rotations[cell], cell)
        total += ell @ np.asarray(moments[cell]).reshape(6)
        for station, weight in zip(stations, weights):
            fraction = (station+1)/2
            xi = cell-1+fraction
            jacobian = reference.jacobian(xi)
            gamma = reference.frame(xi).T @ z / jacobian
            moment = (1-fraction)*moments[cell, 0]+fraction*moments[cell, 1]
            complementary = moment-section[:3, 3:].T @ gamma
            total += weight*jacobian/4 * (
                gamma @ section[:3, :3] @ gamma
                - complementary @ d_inverse @ complementary
            )
    return float(total)


def reference_hessians(reference: Any, section: Any, order: int = 24
                       ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Analytic small-perturbation Hessians: full 36, moment-reduced 24, nodal 18."""
    full = np.zeros((36, 36))
    reduced = np.zeros((24, 24))
    coords, frames = reference.coordinates, reference.nodal_triads
    for cell, (left, right) in enumerate(HALVES):
        data = metrics(reference, section, cell, order)
        dz = np.zeros((3, 24))
        dz[:, left*6:left*6+3] = -np.eye(3)
        dz[:, right*6:right*6+3] = np.eye(3)
        dz[:, 18+cell*3:21+cell*3] = skew(coords[right]-coords[left])
        de = np.zeros((6, 24))
        de[:3, left*6+3:left*6+6] = -frames[left].T
        de[:3, 18+cell*3:21+cell*3] = frames[left].T
        de[3:, right*6+3:right*6+6] = frames[right].T
        de[3:, 18+cell*3:21+cell*3] = -frames[right].T
        de += data.coupling @ dz
        first = dz.T @ data.force @ dz
        reduced += first + de.T @ np.linalg.solve(data.compliance, de)
        full[:24, :24] += first
        moment_slice = slice(24+cell*6, 30+cell*6)
        full[:24, moment_slice] = de.T
        full[moment_slice, :24] = de
        full[moment_slice, moment_slice] = -data.compliance
    condensed = reduced[:18, :18] - reduced[:18, 18:] @ np.linalg.solve(
        reduced[18:, 18:], reduced[18:, :18]
    )
    return full, reduced, condensed


def rigid_matrix(coordinates: Any, local: bool = False) -> np.ndarray:
    result = np.zeros((24 if local else 18, 6))
    for node, coordinate in enumerate(coordinates):
        result[node*6:node*6+3, :3] = np.eye(3)
        result[node*6:node*6+3, 3:] = -skew(coordinate)
        result[node*6+3:node*6+6, 3:] = np.eye(3)
    if local:
        result[18:21, 3:] = result[21:24, 3:] = np.eye(3)
    return result


def fraction_rank(matrix: list[list[Fraction]]) -> int:
    rows = [[Fraction(item) for item in row] for row in matrix]
    pivot = 0
    for column in range(len(rows[0])):
        selected = next((row for row in range(pivot, len(rows)) if rows[row][column]), None)
        if selected is None:
            continue
        rows[pivot], rows[selected] = rows[selected], rows[pivot]
        divisor = rows[pivot][column]
        rows[pivot] = [item/divisor for item in rows[pivot]]
        for row in range(pivot+1, len(rows)):
            factor = rows[row][column]
            rows[row] = [a-factor*b for a, b in zip(rows[row], rows[pivot])]
        pivot += 1
        if pivot == len(rows):
            break
    return pivot


def force_constraint_rank(coordinates: Any, *, objective_lift: bool) -> int:
    """Exact rank of the zero force-strain constraints; invertible R0/J0 omitted.

    Unknowns are nine vertex translations and six local spatial rotations.
    Two rational stations on each half determine the affine control map
    completely. The lifted map is constant on each half before multiplication
    by invertible station factors. This is an exact rank, not a sampled
    floating-point stiffness rank or a domain coercivity certificate.
    """
    coords = [[Fraction(str(component)) for component in row] for row in coordinates]
    rows = []
    for cell, (left, right) in enumerate(HALVES):
        for fraction in (Fraction(1, 4), Fraction(3, 4)):
            xi = cell-1+fraction
            derivatives = [xi-Fraction(1, 2), -2*xi, xi+Fraction(1, 2)]
            if objective_lift:
                derivatives = [Fraction(0) for _ in range(3)]
                derivatives[left], derivatives[right] = Fraction(-1), Fraction(1)
            tangent = [sum(derivatives[n]*coords[n][i] for n in range(3)) for i in range(3)]
            x, y, z = tangent
            cross = ((0, -z, y), (z, 0, -x), (-y, x, 0))
            for component in range(3):
                row = [Fraction(0) for _ in range(15)]
                for node in range(3):
                    row[node*3+component] = derivatives[node]
                row[9+cell*3:12+cell*3] = cross[component]
                rows.append(row)
    return fraction_rank(rows)


def rank_diagnostic() -> dict[str, Any]:
    geometries = {
        "STRAIGHT": ((-1, 0, 0), (0, 0, 0), (1, 0, 0)),
        "PARABOLIC_ARCH": ((-1, 0, 0), (0, "0.5", 0), (1, 0, 0)),
        "ASYMMETRIC_ARCH": ((-1, 0, 0), ("0.2", "0.5", 0), (1, 0, 0)),
    }
    rows = []
    for name, coordinates in geometries.items():
        control = force_constraint_rank(coordinates, objective_lift=False)
        lift = force_constraint_rank(coordinates, objective_lift=True)
        rows.append({"case_id": name, "control_rank": control, "lift_rank": lift,
                     "control_nullity": 15-control, "lift_nullity": 15-lift})
    return {
        "candidate_id": CANDIDATE,
        "classification": "PREPARATORY_EXACT_LINEAR_FORCE_CONSTRAINT_DIAGNOSTIC_ONLY",
        "formal_execution_authorized": False,
        "independent_review": "PENDING",
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "rows": rows,
        "schema": "anysolver.ge-beam3-curved-p5-force-rank-diagnostic-v1",
        "study_id": STUDY,
    }


if __name__ == "__main__":
    import sys
    sys.stdout.buffer.write(canonical_bytes(rank_diagnostic()))
