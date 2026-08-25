"""Dormant production implementation of the qualified E4-PL four-node shell.

The class reuses the mature :class:`~anysolver.elements.ShellElement`
infrastructure for mass, geometric stiffness, state, nonlinear, dynamics,
contact and serialization behavior.  Planar facets use the qualified 35+3
stationary E4-PL formulation for both tangent and physical recovery.  Genuinely
warped facets use the established varying-frame Q4 surface kernel explicitly,
because a single projected plane does not retain the six physical rigid modes
on a warped bilinear surface.

The physical condensed tangent, centre-PL term and retained drilling
hourglass term are exposed separately so numerical fields cannot silently
enter physical recovery or reaction reporting.
"""

from __future__ import annotations

import math
import warnings
from typing import Any, Dict, Mapping, Optional, Sequence

import numpy as np

from .elements import ShellElement, _shell_material_matrices
from .shell_sections import (
    GeneralizedShellSection,
    SHELL_MEMBRANE_VOIGT_ORDER,
    SHELL_TRANSVERSE_SHEAR_ORDER,
    coerce_generalized_shell_section,
)


FORMULATION_ID = "E4_PL_QUALIFIED_Q4_HYBRID_V2"
IMPLEMENTATION_ID = "E4_PL_Q4_HYBRID_STATIONARY_RECOVERY_DIRECTOR_RUIZ_V5"
RECOVERY_POLICY_ID = (
    "Q4_HYBRID_PLANAR_STATIONARY_WARPED_VARYING_FRAME_"
    "PHYSICAL_DIRECTOR_RECOVERY_V3"
)
STATIONARY_SOLVE_POLICY_ID = (
    "Q4_SYMMETRIC_RUIZ_8_ORIGINAL_BACKWARD_ERROR_V2"
)
DIRECTOR_POLARITY_POLICY_ID = (
    "Q4_ELEMENT_OWNED_PHYSICAL_DIRECTOR_INDEPENDENT_OF_D4_NUMBERING_V1"
)
DIRECTOR_REVERSAL_TRANSFORM_ID = (
    "Q4_EPS_S_KAPPA_SIGN_S_SHEAR_SIGN_P_ABD_CONGRUENCE_V1"
)
_PLANAR_FORMULATION_ID = "E4_PL_QUALIFIED_PLANAR_LINEAR_V1"
_WARPED_FORMULATIONS = frozenset({"varying_frame", "reject"})
_STATIONARY_RUIZ_ITERATIONS = 8
_STATIONARY_RUIZ_ROW_NORM_RATIO_LIMIT = 2.0
_STATIONARY_BACKWARD_ERROR_LIMIT = 1.0e-10
_GAUSS = tuple(
    (r, s)
    for r, s in (
        (-1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
        (1.0 / math.sqrt(3.0), -1.0 / math.sqrt(3.0)),
        (1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)),
        (-1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)),
    )
)


class QualifiedQ4MigrationWarning(UserWarning):
    """Warn that a safe uncoupled pre-policy Q4 record was migrated."""


def _shape(r: float, s: float) -> np.ndarray:
    return np.asarray(
        ((1.0 - r) * (1.0 - s), (1.0 + r) * (1.0 - s),
         (1.0 + r) * (1.0 + s), (1.0 - r) * (1.0 + s)),
        dtype=float,
    ) / 4.0


def _shape_derivatives(r: float, s: float) -> tuple[np.ndarray, np.ndarray]:
    return (
        np.asarray((-(1.0 - s), 1.0 - s, 1.0 + s, -(1.0 + s)), dtype=float) / 4.0,
        np.asarray((-(1.0 - r), -(1.0 + r), 1.0 + r, 1.0 - r), dtype=float) / 4.0,
    )


def _normalize(vector: np.ndarray, label: str) -> np.ndarray:
    values = np.asarray(vector, dtype=float)
    component_scale = float(np.max(np.abs(values)))
    if not math.isfinite(component_scale) or component_scale <= 0.0:
        raise ValueError(f"cannot normalize E4-PL {label}")
    scaled = values / component_scale
    norm = float(np.linalg.norm(scaled))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ValueError(f"cannot normalize E4-PL {label}")
    return scaled / norm


def _characteristic_length(coordinates: np.ndarray) -> float:
    """Return a translation- and scale-covariant nodal diameter."""

    values = np.asarray(coordinates, dtype=float)
    length = max(
        (
            float(np.linalg.norm(values[first] - values[second]))
            for first in range(len(values))
            for second in range(first)
        ),
        default=0.0,
    )
    if not math.isfinite(length) or length <= 0.0:
        raise ValueError("E4-PL nodes must have positive finite diameter")
    return length


def _local_jacobian_scale(local: np.ndarray) -> float:
    """Return the squared local diameter for dimensionless Jacobian guards."""

    length = _characteristic_length(np.asarray(local, dtype=float))
    scale = length * length
    if not math.isfinite(scale) or scale <= 0.0:
        raise ValueError("E4-PL local Jacobian scale must be positive and finite")
    return scale


def equation7_frame(nodes: Sequence[Sequence[float]]) -> tuple[np.ndarray, np.ndarray, float]:
    """Return the frozen numbered-frame basis, local nodes and warpage ratio."""

    coordinates = np.asarray(nodes, dtype=float)
    if coordinates.shape != (4, 3) or not np.all(np.isfinite(coordinates)):
        raise ValueError("E4-PL nodes must be a finite 4x3 array")
    diagonal_1 = coordinates[2] - coordinates[0]
    diagonal_2 = coordinates[1] - coordinates[3]
    length = _characteristic_length(coordinates)
    angular_floor = 64.0 * np.finfo(float).eps
    if (
        float(np.linalg.norm(diagonal_1)) <= angular_floor * length
        or float(np.linalg.norm(diagonal_2)) <= angular_floor * length
    ):
        raise ValueError("E4-PL diagonals are degenerate relative to the facet size")
    normalized_1 = _normalize(diagonal_1, "first diagonal")
    normalized_2 = _normalize(diagonal_2, "second diagonal")
    tangent_1_source = normalized_1 + normalized_2
    tangent_2_source = normalized_1 - normalized_2
    if (
        float(np.linalg.norm(tangent_1_source)) <= angular_floor
        or float(np.linalg.norm(tangent_2_source)) <= angular_floor
    ):
        raise ValueError("E4-PL diagonals cannot establish two stable tangents")
    tangent_1 = _normalize(tangent_1_source, "first tangent")
    tangent_2 = _normalize(tangent_2_source, "second tangent")
    normal = _normalize(np.cross(tangent_1, tangent_2), "normal")
    tangent_2 = _normalize(np.cross(normal, tangent_1), "orthogonal tangent")
    tangent_1 = _normalize(np.cross(tangent_2, normal), "renormalized tangent")
    frame = np.column_stack((tangent_1, tangent_2, normal))
    centre = np.mean(coordinates, axis=0)
    relative = coordinates - centre
    local = relative @ frame[:, :2]
    warpage = float(np.max(np.abs(relative @ normal)) / length)
    return frame, local, warpage


def _coefficients(local: np.ndarray) -> Dict[str, float]:
    modal = np.asarray(
        ((1, 1, 1, 1), (-1, 1, 1, -1), (-1, -1, 1, 1), (1, -1, 1, -1)),
        dtype=float,
    ) / 4.0
    x0, xr, xs, xrs = modal @ local[:, 0]
    y0, yr, ys, yrs = modal @ local[:, 1]
    return {
        "x0": float(x0), "xr": float(xr), "xs": float(xs), "xrs": float(xrs),
        "y0": float(y0), "yr": float(yr), "ys": float(ys), "yrs": float(yrs),
        "jc": float(xr * ys - xs * yr),
        "jr": float(xr * yrs - xrs * yr),
        "js": float(xrs * ys - xs * yrs),
    }


def _jacobian(c: Mapping[str, float], r: float, s: float) -> tuple[float, float, float, float, float]:
    xr = c["xr"] + c["xrs"] * s
    xs = c["xs"] + c["xrs"] * r
    yr = c["yr"] + c["yrs"] * s
    ys = c["ys"] + c["yrs"] * r
    return xr, xs, yr, ys, xr * ys - xs * yr


def _natural_shear(local: np.ndarray, r: float, s: float, direction: int) -> np.ndarray:
    shape = _shape(r, s)
    nr, ns = _shape_derivatives(r, s)
    derivative = nr if direction == 0 else ns
    x_direction = float(local[:, 0] @ derivative)
    y_direction = float(local[:, 1] @ derivative)
    row = np.zeros(20, dtype=float)
    for index in range(4):
        base = 5 * index
        row[base + 2] = derivative[index]
        row[base + 3] = -y_direction * shape[index]
        row[base + 4] = x_direction * shape[index]
    return row


def _compatible(local: np.ndarray, c: Mapping[str, float], r: float, s: float) -> np.ndarray:
    nr, ns = _shape_derivatives(r, s)
    xr, xs, yr, ys, determinant = _jacobian(c, r, s)
    nx = (ys * nr - yr * ns) / determinant
    ny = (-xs * nr + xr * ns) / determinant
    result = np.zeros((8, 20), dtype=float)
    for index in range(4):
        base = 5 * index
        result[0, base] = nx[index]
        result[1, base + 1] = ny[index]
        result[2, base] = ny[index]
        result[2, base + 1] = nx[index]
        result[3, base + 4] = nx[index]
        result[4, base + 3] = -ny[index]
        result[5, base + 4] = ny[index]
        result[5, base + 3] = -nx[index]
    row_r_minus = _natural_shear(local, 0.0, -1.0, 0)
    row_r_plus = _natural_shear(local, 0.0, 1.0, 0)
    row_s_plus = _natural_shear(local, 1.0, 0.0, 1)
    row_s_minus = _natural_shear(local, -1.0, 0.0, 1)
    row_r = 0.5 * (1.0 - s) * row_r_minus + 0.5 * (1.0 + s) * row_r_plus
    row_s = 0.5 * (1.0 + r) * row_s_plus + 0.5 * (1.0 - r) * row_s_minus
    result[6] = (ys * row_r - yr * row_s) / determinant
    result[7] = (-xs * row_r + xr * row_s) / determinant
    return result


def _tensor_transform(xr: float, xs: float, yr: float, ys: float, a: float, b: float) -> np.ndarray:
    return np.asarray(
        (
            (xr * xr, xs * xs, a * xr * xs),
            (yr * yr, ys * ys, a * yr * ys),
            (b * xr * yr, b * xs * ys, xr * ys + yr * xs),
        ),
        dtype=float,
    )


def _source_fields(c: Mapping[str, float], r: float, s: float) -> tuple[np.ndarray, np.ndarray]:
    jc, jr, js = c["jc"], c["jr"], c["js"]
    r_bar, s_bar = jr / (3.0 * jc), js / (3.0 * jc)
    stress_transform = _tensor_transform(c["xr"], c["xs"], c["yr"], c["ys"], 2.0, 1.0)
    strain_transform = _tensor_transform(c["xr"], c["xs"], c["yr"], c["ys"], 1.0, 2.0)
    shear_transform = np.asarray(((c["xr"], c["xs"]), (c["yr"], c["ys"])), dtype=float)
    n_sigma = np.zeros((8, 14), dtype=float)
    n_epsilon = np.zeros((8, 21), dtype=float)
    n_sigma[:, :8] = np.eye(8)
    n_epsilon[:, :8] = np.eye(8)
    seed = np.asarray(((s - s_bar, 0.0), (0.0, r - r_bar), (0.0, 0.0)), dtype=float)
    stress_vary = stress_transform @ seed
    strain_vary = strain_transform @ seed
    for row, column in ((0, 8), (3, 10)):
        n_sigma[row : row + 3, column : column + 2] = stress_vary
        n_epsilon[row : row + 3, column : column + 2] = strain_vary
    shear_seed = np.asarray(((s - s_bar, 0.0), (0.0, r - r_bar)), dtype=float)
    n_sigma[6:8, 12:14] = shear_transform @ shear_seed
    n_epsilon[6:8, 12:14] = shear_transform @ shear_seed
    enrichment = np.asarray(
        ((r, 0, 0, 0, r * s, 0, 0), (0, s, 0, 0, 0, r * s, 0), (0, 0, r, s, 0, 0, r * s)),
        dtype=float,
    )
    determinant = _jacobian(c, r, s)[4]
    n_epsilon[:3, 14:21] = (jc / determinant) * (strain_transform @ enrichment)
    return n_sigma, n_epsilon


def _centre_taylor(c: Mapping[str, float]) -> np.ndarray:
    f0 = np.ones(4, dtype=float) / 4.0
    fr = np.asarray((-1, 1, 1, -1), dtype=float) / 4.0
    fs = np.asarray((-1, -1, 1, 1), dtype=float) / 4.0
    frs = np.asarray((1, -1, 1, -1), dtype=float) / 4.0
    result = np.zeros((3, 24), dtype=float)
    jc, jr, js = c["jc"], c["jr"], c["js"]
    for coordinate in range(24):
        node, component = divmod(coordinate, 6)
        ur = fr[node] if component == 0 else 0.0
        us = fs[node] if component == 0 else 0.0
        urs = frs[node] if component == 0 else 0.0
        vr = fr[node] if component == 1 else 0.0
        vs = fs[node] if component == 1 else 0.0
        vrs = frs[node] if component == 1 else 0.0
        d0 = f0[node] if component == 5 else 0.0
        dr = fr[node] if component == 5 else 0.0
        ds = fs[node] if component == 5 else 0.0
        n0 = -c["xs"] * ur + c["xr"] * us - c["ys"] * vr + c["yr"] * vs
        nr = -c["xrs"] * ur + c["xr"] * urs - c["yrs"] * vr + c["yr"] * vrs
        ns = -c["xs"] * urs + c["xrs"] * us - c["ys"] * vrs + c["yrs"] * vs
        result[0, coordinate] = d0 + n0 / (2.0 * jc)
        result[1, coordinate] = dr + (nr * jc - n0 * jr) / (2.0 * jc * jc)
        result[2, coordinate] = ds + (ns * jc - n0 * js) / (2.0 * jc * jc)
    return result


def _residual_mode(local: np.ndarray, c: Mapping[str, float]) -> np.ndarray:
    x = local[:, 0]
    y = local[:, 1]
    centred_x = x - c["x0"]
    centred_y = y - c["y0"]
    xi = np.asarray((-1, 1, 1, -1), dtype=float)
    eta = np.asarray((-1, -1, 1, 1), dtype=float)
    alternating = np.asarray((1, -1, 1, -1), dtype=float)
    area = 4.0 * c["jc"]
    b1 = ((eta @ centred_y) * xi - (xi @ centred_y) * eta) / (4.0 * area)
    b2 = (-(eta @ centred_x) * xi + (xi @ centred_x) * eta) / (4.0 * area)
    return (alternating - (alternating @ centred_x) * b1 - (alternating @ centred_y) * b2) / 4.0


def _global_transform(frame: np.ndarray) -> np.ndarray:
    transform = np.zeros((24, 24), dtype=float)
    for node in range(4):
        transform[6 * node : 6 * node + 3, 6 * node : 6 * node + 3] = frame
        transform[6 * node + 3 : 6 * node + 6, 6 * node + 3 : 6 * node + 6] = frame
    return transform


def _stationary_blocks(
    local: np.ndarray,
    c: Mapping[str, float],
    constitutive: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Assemble the frozen 35-field stationary system and its physical coupling.

    This is the single floating-point implementation of the Q1A/Q1Y mixed
    blocks.  Both stiffness condensation and physical recovery call this
    helper so recovery cannot silently drift back to the inherited compatible
    MITC4 fields.
    """

    f_matrix = np.zeros((21, 14), dtype=float)
    coupling_20 = np.zeros((14, 20), dtype=float)
    strain_gram = np.zeros((21, 21), dtype=float)
    gram = np.zeros((3, 3), dtype=float)
    for r, s in _GAUSS:
        determinant = _jacobian(c, r, s)[4]
        n_sigma, n_epsilon = _source_fields(c, r, s)
        compatible = _compatible(local, c, r, s)
        f_matrix -= determinant * (n_epsilon.T @ n_sigma)
        coupling_20 += determinant * (n_sigma.T @ compatible)
        strain_gram += determinant * (n_epsilon.T @ constitutive @ n_epsilon)
        polynomial = np.asarray((1.0, r, s), dtype=float)
        gram += determinant * np.outer(polynomial, polynomial)
    stationary = np.zeros((35, 35), dtype=float)
    stationary[:14, 14:] = f_matrix.T
    stationary[14:, :14] = f_matrix
    stationary[14:, 14:] = strain_gram
    coupling = np.zeros((24, 35), dtype=float)
    physical_coupling = np.zeros((20, 35), dtype=float)
    physical_coupling[:, :14] = coupling_20.T
    for node in range(4):
        coupling[6 * node : 6 * node + 5] = physical_coupling[
            5 * node : 5 * node + 5
        ]
    return stationary, coupling, gram


def _invariant_generalized_drilling_scale(membrane_matrix: np.ndarray) -> float:
    """Return the physical, basis-invariant generalized-section drill scale.

    This is the same generalized eigenvalue invariant used by the qualified
    S3 companion.  It equals ``A66`` for isotropy and, unlike a numbered
    ``A[2, 2]`` lookup, is unchanged by proper or reflected in-plane frame
    re-expression.
    """

    membrane = np.asarray(membrane_matrix, dtype=float)
    if membrane.shape != (3, 3) or not np.all(np.isfinite(membrane)):
        raise ValueError("qualified Q4 membrane matrix A must be finite 3x3")
    membrane = 0.5 * (membrane + membrane.T)
    if float(np.linalg.eigvalsh(membrane)[0]) <= 0.0:
        raise ValueError("qualified Q4 membrane matrix A must be positive definite")
    projector = np.asarray(((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0)), dtype=float)
    inverse_metric_sqrt = np.diag((1.0 / math.sqrt(2.0), math.sqrt(2.0)))
    restricted = projector.T @ membrane @ projector
    canonical = inverse_metric_sqrt @ restricted @ inverse_metric_sqrt
    value = 0.5 * float(np.linalg.eigvalsh(0.5 * (canonical + canonical.T))[0])
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError("qualified Q4 invariant drilling scale must be positive")
    return value


def _symmetric_ruiz_congruence(
    matrix: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """Balance a symmetric mixed system through a fixed Ruiz congruence.

    Q4 stationary coordinates combine stress and generalized-strain fields
    with different physical units.  At ``t/L=1e-6`` the raw 35-coordinate
    matrix can be ill-conditioned solely because of those units.  The fixed
    congruence preserves the exact equation while making the binary64 solve
    insensitive to length and stiffness units::

        H_eq = D H D,  rhs_eq = D rhs,  x = D x_eq.

    Exactly eight max-row Ruiz steps are used.  The fixed count is deterministic,
    while the final row-norm certificate prevents a partially equilibrated
    system from reaching the solve.  The six-step bound was established over
    all registered Q4 geometries at coordinate scales ``1e-6``, ``1`` and
    ``1e6``.  Eight steps also retain the row-norm certificate for ordinary
    thick facets at extreme coordinate scales; further iterations do not
    materially improve the condition bound but do regress the cold element
    path.
    """

    made = np.asarray(matrix, dtype=np.float64)
    if made.ndim != 2 or made.shape[0] != made.shape[1]:
        raise ValueError("E4-PL stationary system must be square")
    if not np.all(np.isfinite(made)):
        raise ValueError("E4-PL stationary system must be finite")
    with np.errstate(over="ignore", invalid="ignore"):
        input_norm = float(np.linalg.norm(made, ord=np.inf))
        asymmetry = float(np.linalg.norm(made - made.T, ord=np.inf))
    if not math.isfinite(input_norm) or not math.isfinite(asymmetry):
        raise ValueError("E4-PL stationary system norm is non-finite")
    if asymmetry > 64.0 * np.finfo(np.float64).eps * input_norm:
        raise ValueError("E4-PL stationary system is not symmetric")
    equilibrated = 0.5 * (made + made.T)
    accumulated = np.ones(made.shape[0], dtype=np.float64)
    for _iteration in range(_STATIONARY_RUIZ_ITERATIONS):
        row_norms = np.max(np.abs(equilibrated), axis=1)
        if np.any(~np.isfinite(row_norms)) or np.any(row_norms <= 0.0):
            raise ValueError("E4-PL stationary system is singular")
        step = 1.0 / np.sqrt(row_norms)
        accumulated *= step
        equilibrated = step[:, None] * equilibrated * step[None, :]
    equilibrated = 0.5 * (equilibrated + equilibrated.T)
    final_row_norms = np.max(np.abs(equilibrated), axis=1)
    if (
        np.any(~np.isfinite(accumulated))
        or np.any(accumulated <= 0.0)
        or np.any(~np.isfinite(equilibrated))
        or np.any(~np.isfinite(final_row_norms))
        or np.any(final_row_norms <= 0.0)
    ):
        raise ValueError("E4-PL stationary equilibration is unresolved")
    row_norm_ratio = float(np.max(final_row_norms) / np.min(final_row_norms))
    if (
        not math.isfinite(row_norm_ratio)
        or row_norm_ratio > _STATIONARY_RUIZ_ROW_NORM_RATIO_LIMIT
    ):
        raise ValueError(
            "E4-PL stationary equilibration exceeded the row-norm ratio limit"
        )
    return equilibrated, accumulated, {
        "id": STATIONARY_SOLVE_POLICY_ID,
        "iterations": _STATIONARY_RUIZ_ITERATIONS,
        "input_asymmetry_relative": asymmetry / max(input_norm, np.finfo(float).tiny),
        "row_norm_ratio": row_norm_ratio,
        "row_norm_ratio_limit": _STATIONARY_RUIZ_ROW_NORM_RATIO_LIMIT,
        "scale_max": float(np.max(accumulated)),
        "scale_min": float(np.min(accumulated)),
    }


def _stationary_backward_error(
    matrix: np.ndarray,
    solution: np.ndarray,
    rhs: np.ndarray,
) -> float:
    """Return a fail-closed normwise backward error in original coordinates."""

    made_matrix = np.asarray(matrix, dtype=np.float64)
    made_solution = np.asarray(solution, dtype=np.float64)
    made_rhs = np.asarray(rhs, dtype=np.float64)
    if (
        np.any(~np.isfinite(made_matrix))
        or np.any(~np.isfinite(made_solution))
        or np.any(~np.isfinite(made_rhs))
    ):
        return math.inf
    with np.errstate(over="ignore", invalid="ignore"):
        residual = made_matrix @ made_solution - made_rhs
        matrix_norm = float(np.linalg.norm(made_matrix, ord=np.inf))
        solution_norm = float(np.linalg.norm(made_solution, ord=np.inf))
        rhs_norm = float(np.linalg.norm(made_rhs, ord=np.inf))
        residual_norm = float(np.linalg.norm(residual, ord=np.inf))
        denominator = matrix_norm * solution_norm + rhs_norm
    if not all(
        math.isfinite(value)
        for value in (
            matrix_norm,
            solution_norm,
            rhs_norm,
            residual_norm,
            denominator,
        )
    ):
        return math.inf
    if denominator <= 0.0:
        return 0.0 if residual_norm == 0.0 else math.inf
    return residual_norm / denominator


def _solve_stationary_system(
    stationary: np.ndarray,
    coupling: np.ndarray,
) -> tuple[np.ndarray, Dict[str, Any]]:
    """Solve the Q4 mixed condensation with deterministic certification."""

    made_stationary = np.asarray(stationary, dtype=np.float64)
    made_coupling = np.asarray(coupling, dtype=np.float64)
    if (
        made_stationary.ndim != 2
        or made_stationary.shape[0] != made_stationary.shape[1]
        or made_coupling.ndim != 2
        or made_coupling.shape[1] != made_stationary.shape[0]
    ):
        raise ValueError("E4-PL stationary coupling dimensions are incompatible")
    if not np.all(np.isfinite(made_coupling)):
        raise ValueError("E4-PL stationary coupling must be finite")
    equilibrated, scaling, diagnostics = _symmetric_ruiz_congruence(
        made_stationary
    )
    rhs = made_coupling.T
    scaled_rhs = scaling[:, None] * rhs
    try:
        equilibrated_solution = np.linalg.solve(equilibrated, scaled_rhs)
    except np.linalg.LinAlgError as exc:
        raise ValueError("E4-PL stationary system is singular") from exc
    solution = scaling[:, None] * equilibrated_solution
    backward_error = _stationary_backward_error(
        made_stationary,
        solution,
        rhs,
    )
    if (
        not np.all(np.isfinite(solution))
        or not math.isfinite(backward_error)
        or backward_error > _STATIONARY_BACKWARD_ERROR_LIMIT
    ):
        raise ValueError(
            "E4-PL stationary solve has uncertified original-system accuracy"
        )
    return solution, {
        **diagnostics,
        "relative_backward_error": backward_error,
        "relative_backward_error_limit": _STATIONARY_BACKWARD_ERROR_LIMIT,
        "disposition": "CERTIFIED",
    }


class QualifiedE4PLShellElement(ShellElement):
    """Dormant qualified E4-PL element for four-node shell facets."""

    formulation_id = FORMULATION_ID
    implementation_id = IMPLEMENTATION_ID
    recovery_policy_id = RECOVERY_POLICY_ID
    stationary_solve_policy_id = STATIONARY_SOLVE_POLICY_ID
    director_polarity_policy_id = DIRECTOR_POLARITY_POLICY_ID
    director_reversal_transform_id = DIRECTOR_REVERSAL_TRANSFORM_ID
    legacy_stiffness_batch_eligible = False
    legacy_nonlinear_batch_eligible = True

    def __init__(
        self,
        element_id: int,
        node_ids: list[int],
        material_name: str = "default",
        thickness: float = 0.01,
        drilling_stabilization: float = 1.0e-3,
        reduced_integration: bool = False,
        hourglass_stabilization: float = 1.0e-3,
        material_direction: Optional[np.ndarray] = None,
        material_angle_deg: float = 0.0,
        shell_section: Optional[Any] = None,
        *,
        pl_stabilization: float = 1.0,
        planar_tolerance: float = 1.0e-10,
        warped_formulation: str = "varying_frame",
        legacy_warped_fallback: Optional[bool] = None,
        reference_normal: Optional[Sequence[float]] = None,
        director_polarity: int = 1,
    ) -> None:
        if len(node_ids) != 4:
            raise ValueError("QualifiedE4PLShellElement requires exactly four nodes")
        super().__init__(
            element_id,
            node_ids,
            material_name,
            thickness,
            drilling_stabilization,
            reduced_integration,
            hourglass_stabilization,
            material_direction,
            material_angle_deg,
            shell_section,
        )
        if isinstance(director_polarity, (bool, np.bool_)) or not isinstance(
            director_polarity, (int, np.integer)
        ) or int(director_polarity) not in (-1, 1):
            raise ValueError(
                "qualified Q4 director_polarity must be the integer -1 or +1"
            )
        self.director_polarity = int(director_polarity)
        if reference_normal is None:
            self.reference_normal = None
            if self.director_polarity != 1:
                raise ValueError(
                    "qualified Q4 director_polarity requires an authoritative "
                    "reference_normal"
                )
        else:
            normal = np.asarray(reference_normal, dtype=float).reshape(-1)
            if normal.size != 3 or not np.all(np.isfinite(normal)):
                raise ValueError(
                    "qualified Q4 reference_normal must be a finite 3-vector"
                )
            self.reference_normal = _normalize(normal, "reference normal").copy()
        if (
            self.shell_section is not None
            and np.any(np.asarray(self.shell_section.B, dtype=float) != 0.0)
            and self.reference_normal is None
        ):
            raise ValueError(
                "B-coupled qualified Q4 sections require an authoritative "
                "reference_normal; connectivity winding is not a physical director"
            )
        self.pl_stabilization = float(pl_stabilization)
        self.planar_tolerance = float(planar_tolerance)
        if legacy_warped_fallback is not None:
            warped_formulation = (
                "varying_frame" if bool(legacy_warped_fallback) else "reject"
            )
        self.warped_formulation = str(warped_formulation).strip().lower()
        if not math.isfinite(self.pl_stabilization) or self.pl_stabilization < 0.0:
            raise ValueError("pl_stabilization must be finite and nonnegative")
        if not math.isfinite(self.planar_tolerance) or self.planar_tolerance < 0.0:
            raise ValueError("planar_tolerance must be finite and nonnegative")
        if self.warped_formulation not in _WARPED_FORMULATIONS:
            raise ValueError(
                "warped_formulation must be one of "
                f"{sorted(_WARPED_FORMULATIONS)}"
            )
        self._qualified_components: Optional[Dict[str, Any]] = None
        self._qualified_cache_key: Optional[tuple[Any, ...]] = None

    def _local_frame_and_derivatives(
        self,
        coords: np.ndarray,
        derivative_xi: np.ndarray,
        derivative_eta: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
        """Scale-invariant varying-frame geometry for the qualified Q4.

        The inherited shell guard is expressed in absolute square-length
        units.  Q4 uses the same frame and derivatives, but judges every
        degeneracy against the nodal diameter so geometrically similar facets
        at micrometre, metre and megametre scales receive the same decision.
        """

        coordinates = np.asarray(coords, dtype=float)
        length = _characteristic_length(coordinates)
        length_floor = 64.0 * np.finfo(float).eps * length
        area_floor = 64.0 * np.finfo(float).eps * length * length
        jacobian = self.compute_jacobian(
            coordinates,
            np.asarray(derivative_xi, dtype=float),
            np.asarray(derivative_eta, dtype=float),
        )
        tangent_xi = jacobian[0]
        tangent_eta = jacobian[1]
        cross = np.cross(tangent_xi, tangent_eta)
        cross_scale = float(np.max(np.abs(cross)))
        determinant = (
            0.0
            if cross_scale <= 0.0
            else cross_scale * float(np.linalg.norm(cross / cross_scale))
        )
        inherited: Optional[tuple[np.ndarray, np.ndarray, np.ndarray, float]]
        try:
            inherited = ShellElement._local_frame_and_derivatives(
                self,
                coordinates,
                derivative_xi,
                derivative_eta,
            )
        except ValueError:
            inherited = None
        if inherited is not None and math.isfinite(determinant) and determinant > area_floor:
            inherited_frame = np.asarray(inherited[0], dtype=float)
            inherited_first_source = (
                tangent_xi
                - float(tangent_xi @ inherited_frame[:, 2]) * inherited_frame[:, 2]
            )
            inherited_local_jacobian = np.asarray(
                (
                    (
                        float(tangent_xi @ inherited_frame[:, 0]),
                        float(tangent_xi @ inherited_frame[:, 1]),
                    ),
                    (
                        float(tangent_eta @ inherited_frame[:, 0]),
                        float(tangent_eta @ inherited_frame[:, 1]),
                    ),
                ),
                dtype=float,
            )
            inherited_local_determinant = float(
                np.linalg.det(inherited_local_jacobian)
            )
            if (
                float(np.linalg.norm(inherited_first_source)) > length_floor
                and math.isfinite(inherited_local_determinant)
                and abs(inherited_local_determinant) > area_floor
            ):
                # Preserve the established admitted response byte-for-byte,
                # but only after the dimensionless certificate has passed.
                return inherited
        if not math.isfinite(determinant) or determinant <= area_floor:
            raise ValueError(
                f"Shell element {self.element_id} has a dimensionless near-zero "
                "surface Jacobian"
            )
        normal = _normalize(cross, "varying-frame normal")
        first_source = tangent_xi - float(tangent_xi @ normal) * normal
        first_norm = float(np.linalg.norm(first_source))
        if not math.isfinite(first_norm) or first_norm <= length_floor:
            first = None
            for begin, end in (
                (0, 1),
                (0, 2),
                (1, 2),
                (3, 2),
                (0, 3),
                (1, 3),
            ):
                edge = coordinates[end] - coordinates[begin]
                projected = edge - float(edge @ normal) * normal
                if float(np.linalg.norm(projected)) > length_floor:
                    first = _normalize(projected, "fallback in-plane direction")
                    break
            if first is None:
                raise ValueError(
                    f"Shell element {self.element_id} has no stable in-plane direction"
                )
        else:
            first = _normalize(first_source, "varying-frame first tangent")
        second_source = np.cross(normal, first)
        if float(np.linalg.norm(second_source)) <= 64.0 * np.finfo(float).eps:
            raise ValueError(
                f"Shell element {self.element_id} has an invalid local y direction"
            )
        second = _normalize(second_source, "varying-frame second tangent")
        first = _normalize(
            np.cross(second, normal),
            "varying-frame renormalized first tangent",
        )
        frame = np.column_stack((first, second, normal))
        local_jacobian = np.asarray(
            (
                (
                    float(tangent_xi @ first),
                    float(tangent_xi @ second),
                ),
                (
                    float(tangent_eta @ first),
                    float(tangent_eta @ second),
                ),
            ),
            dtype=float,
        )
        local_determinant = float(np.linalg.det(local_jacobian))
        if (
            not math.isfinite(local_determinant)
            or abs(local_determinant) <= area_floor
        ):
            raise ValueError(
                f"Shell element {self.element_id} has a dimensionless singular "
                "local Jacobian"
            )
        inverse = np.linalg.inv(local_jacobian)
        dshape_x = inverse[0, 0] * derivative_xi + inverse[0, 1] * derivative_eta
        dshape_y = inverse[1, 0] * derivative_xi + inverse[1, 1] * derivative_eta
        return frame, dshape_x, dshape_y, determinant

    def _inverse_planar_jacobian(
        self,
        planar: np.ndarray,
        jacobian: np.ndarray,
        label: str,
    ) -> tuple[np.ndarray, float]:
        length = _characteristic_length(np.asarray(planar, dtype=float))
        determinant = float(np.linalg.det(np.asarray(jacobian, dtype=float)))
        if (
            not math.isfinite(determinant)
            or abs(determinant)
            <= 64.0 * np.finfo(float).eps * length * length
        ):
            raise ValueError(
                f"Shell element {self.element_id} has a dimensionless singular {label}"
            )
        return np.linalg.inv(np.asarray(jacobian, dtype=float)), determinant

    def _mitc4_shear_b_matrix(
        self,
        planar: np.ndarray,
        samples: Dict[str, tuple[np.ndarray, np.ndarray]],
        xi: float,
        eta: float,
    ) -> tuple[np.ndarray, float]:
        """Qualified scale-invariant form of the established MITC4 map."""

        _shape, derivative_xi, derivative_eta = self.compute_shape_functions(
            float(xi), float(eta)
        )
        jacobian = np.asarray(
            (
                (
                    float(derivative_xi @ planar[:, 0]),
                    float(derivative_xi @ planar[:, 1]),
                ),
                (
                    float(derivative_eta @ planar[:, 0]),
                    float(derivative_eta @ planar[:, 1]),
                ),
            ),
            dtype=float,
        )
        try:
            inherited = ShellElement._mitc4_shear_b_matrix(
                self,
                planar,
                samples,
                xi,
                eta,
            )
        except ValueError:
            inherited = None
        if inherited is not None:
            length = _characteristic_length(np.asarray(planar, dtype=float))
            inherited_determinant = float(inherited[1])
            if (
                math.isfinite(inherited_determinant)
                and abs(inherited_determinant)
                > 64.0 * np.finfo(float).eps * length * length
            ):
                return inherited
        inverse, determinant = self._inverse_planar_jacobian(
            planar,
            jacobian,
            "MITC4 in-plane Jacobian",
        )
        covariant = np.vstack(
            (
                0.5 * (1.0 - eta) * samples["A"][0]
                + 0.5 * (1.0 + eta) * samples["C"][0],
                0.5 * (1.0 - xi) * samples["D"][1]
                + 0.5 * (1.0 + xi) * samples["B"][1],
            )
        )
        return inverse @ covariant, determinant

    def _nonlinear_geometry(self, mesh: Any) -> Dict[str, Any]:
        """Qualified Q4 nonlinear geometry with dimensionless 2x2 guards."""

        cache = getattr(self, "_nl_cache", None)
        if cache is not None:
            return cache
        try:
            return ShellElement._nonlinear_geometry(self, mesh)
        except np.linalg.LinAlgError:
            # The inherited 2x2 helper alone rejected a dimensionally small,
            # otherwise regular geometry.  Rebuild the same arrays using the
            # qualified dimensionless inverse below.
            pass
        coordinates = self.get_node_coordinates(mesh)
        frame = self._center_frame(coordinates)
        transform = self._local_dof_transform(frame)
        planar = coordinates @ frame[:, :2]
        gauss_data = []
        for (xi, eta), weight in zip(self.gauss_points, self.gauss_weights):
            shape, derivative_xi, derivative_eta = self.compute_shape_functions(
                float(xi), float(eta)
            )
            jacobian = np.asarray(
                (
                    (
                        float(derivative_xi @ planar[:, 0]),
                        float(derivative_xi @ planar[:, 1]),
                    ),
                    (
                        float(derivative_eta @ planar[:, 0]),
                        float(derivative_eta @ planar[:, 1]),
                    ),
                ),
                dtype=float,
            )
            inverse, determinant = self._inverse_planar_jacobian(
                planar,
                jacobian,
                "nonlinear in-plane Jacobian",
            )
            derivative_x = (
                inverse[0, 0] * derivative_xi + inverse[0, 1] * derivative_eta
            )
            derivative_y = (
                inverse[1, 0] * derivative_xi + inverse[1, 1] * derivative_eta
            )
            membrane, bending, shear = self._build_shell_b_matrices(
                shape,
                derivative_x,
                derivative_y,
            )
            drilling = self._build_drilling_b_matrix(
                shape,
                derivative_x,
                derivative_y,
            )
            transverse_gradient = np.zeros((2, self.total_dofs), dtype=float)
            transverse_gradient[0, 2::6] = derivative_x
            transverse_gradient[1, 2::6] = derivative_y
            gauss_data.append(
                {
                    "B_m": membrane,
                    "B_b": bending,
                    "B_s": shear,
                    "B_d": drilling,
                    "Gw": transverse_gradient,
                    "detw": abs(determinant) * float(weight),
                }
            )

        _planar, samples = self._mitc4_shear_samples(coordinates, frame)
        shear_data = []
        for (xi, eta), weight in zip(
            self.GAUSS_POINTS_2x2,
            self.GAUSS_WEIGHTS_2x2,
        ):
            shear, determinant = self._mitc4_shear_b_matrix(
                planar,
                samples,
                float(xi),
                float(eta),
            )
            shear_data.append(
                {
                    "B_s": shear,
                    "detw": abs(determinant) * float(weight),
                }
            )

        count = len(gauss_data)
        membrane_all = np.zeros((count, 3, self.total_dofs), dtype=float)
        bending_all = np.zeros_like(membrane_all)
        drilling_all = np.zeros((count, 1, self.total_dofs), dtype=float)
        gradient_all = np.zeros((count, 2, self.total_dofs), dtype=float)
        determinant_all = np.zeros(count, dtype=float)
        for index, data in enumerate(gauss_data):
            membrane_all[index] = data["B_m"]
            bending_all[index] = data["B_b"]
            drilling_all[index] = data["B_d"]
            gradient_all[index] = data["Gw"]
            determinant_all[index] = data["detw"]
        shear_all = np.asarray([data["B_s"] for data in shear_data], dtype=float)
        shear_determinant_all = np.asarray(
            [data["detw"] for data in shear_data],
            dtype=float,
        )
        cache = {
            "R0": frame,
            "T0": transform,
            "gp": gauss_data,
            "shear": shear_data,
            "B_m_all": membrane_all,
            "B_b_all": bending_all,
            "B_d_all": drilling_all,
            "Gw_all": gradient_all,
            "detw_all": determinant_all,
            "B_s_all": shear_all,
            "detw_shear_all": shear_determinant_all,
        }
        self._nl_cache = cache
        return cache

    def to_dict(self) -> Dict[str, Any]:
        payload = super().to_dict()
        payload.update(
            {
                "drilling_stabilization": float(self.drilling_stabilization),
                "implementation_id": IMPLEMENTATION_ID,
                "formulation_id": FORMULATION_ID,
                "hourglass_stabilization": float(self.hourglass_stabilization),
                "planar_tolerance": self.planar_tolerance,
                "pl_stabilization": self.pl_stabilization,
                "reduced_integration": bool(self.reduced_integration),
                "recovery_policy_id": RECOVERY_POLICY_ID,
                "stationary_solve_policy_id": STATIONARY_SOLVE_POLICY_ID,
                "director_polarity_policy_id": DIRECTOR_POLARITY_POLICY_ID,
                "director_reversal_transform_id": DIRECTOR_REVERSAL_TRANSFORM_ID,
                "director_polarity": int(self.director_polarity),
                "reference_normal": (
                    None
                    if self.reference_normal is None
                    else np.asarray(self.reference_normal, dtype=float).tolist()
                ),
                "warped_formulation": self.warped_formulation,
            }
        )
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "QualifiedE4PLShellElement":
        """Reconstruct a candidate from its lossless JSON-compatible record."""

        data = dict(payload)
        if data.get("formulation_id") not in {FORMULATION_ID, _PLANAR_FORMULATION_ID}:
            raise ValueError("serialized E4-PL formulation_id is missing or incompatible")
        if data.get("type") not in {cls.__name__, "e4-pl"}:
            raise ValueError("serialized E4-PL type is incompatible")
        identity = {
            "implementation_id": IMPLEMENTATION_ID,
            "recovery_policy_id": RECOVERY_POLICY_ID,
            "stationary_solve_policy_id": STATIONARY_SOLVE_POLICY_ID,
            "director_polarity_policy_id": DIRECTOR_POLARITY_POLICY_ID,
            "director_reversal_transform_id": DIRECTOR_REVERSAL_TRANSFORM_ID,
        }
        present = {name for name in identity if name in data}
        if present and present != set(identity):
            raise ValueError(
                "serialized E4-PL Q4 implementation/recovery/director identity is incomplete"
            )
        if present:
            for name, expected in identity.items():
                if data.get(name) != expected:
                    raise ValueError(
                        f"serialized E4-PL Q4 {name} is incompatible"
                    )
            required_director_state = {"director_polarity", "reference_normal"}
            retained_director_state = required_director_state & data.keys()
            if retained_director_state != required_director_state:
                raise ValueError(
                    "serialized E4-PL Q4 current director state is incomplete"
                )
        else:
            legacy_section = coerce_generalized_shell_section(data.get("shell_section"))
            if legacy_section is not None and np.any(legacy_section.B != 0.0):
                raise ValueError(
                    "pre-policy B-coupled qualified Q4 records cannot be migrated: "
                    "their physical director is not authoritative"
                )
            if any(
                name in data
                for name in ("reference_normal", "director_polarity")
            ):
                raise ValueError(
                    "pre-policy qualified Q4 records cannot contain partial director data"
                )
            warnings.warn(
                "Migrated a pre-policy uncoupled qualified Q4 record with its "
                "connectivity-relative director behavior preserved; B-coupled "
                "records require an authoritative reference_normal.",
                QualifiedQ4MigrationWarning,
                stacklevel=2,
            )
        return cls(
            element_id=int(data["element_id"]),
            node_ids=[int(value) for value in data["node_ids"]],
            material_name=str(data.get("material_name", "default")),
            thickness=float(data.get("thickness", 0.01)),
            drilling_stabilization=float(data.get("drilling_stabilization", 1.0e-3)),
            reduced_integration=bool(data.get("reduced_integration", False)),
            hourglass_stabilization=float(data.get("hourglass_stabilization", 1.0e-3)),
            material_direction=data.get("material_direction"),
            material_angle_deg=float(data.get("material_angle_deg", 0.0)),
            shell_section=data.get("shell_section"),
            pl_stabilization=float(data.get("pl_stabilization", 1.0)),
            planar_tolerance=float(data.get("planar_tolerance", 1.0e-10)),
            warped_formulation=str(
                data.get(
                    "warped_formulation",
                    "varying_frame"
                    if bool(data.get("legacy_warped_fallback", True))
                    else "reject",
                )
            ),
            reference_normal=data.get("reference_normal"),
            director_polarity=int(data.get("director_polarity", 1)),
        )

    @property
    def physical_reference_director(self) -> Optional[np.ndarray]:
        """Return the persisted physical director authority, when supplied."""

        if self.reference_normal is None:
            return None
        return (
            float(self.director_polarity)
            * np.asarray(self.reference_normal, dtype=float)
        ).copy()

    def _physical_director_context(
        self,
        numbered_frame: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]:
        """Map numbered Equation-7 fields to a physical-director frame.

        A reflected D4 numbering reverses the Equation-7 normal and one local
        tangent.  With ``s = sign(n_numbered . d_physical)``, the exact
        numbered-to-physical engineering maps are

        ``E = diag(1, 1, s)``, ``K = s E`` and
        ``H = s diag(1, s)``.

        ``E`` acts on membrane fields, ``K`` on curvatures/moments and ``H``
        on transverse shear.  All three are orthogonal involutions, so the
        same matrices map conjugate resultants in the reverse direction.
        """

        frame = np.asarray(numbered_frame, dtype=float).reshape(3, 3)
        if self.reference_normal is None:
            return (
                frame.copy(),
                np.eye(3, dtype=float),
                np.eye(3, dtype=float),
                np.eye(2, dtype=float),
                1,
            )
        director = self.physical_reference_director
        assert director is not None
        alignment = float(frame[:, 2] @ director)
        if not math.isfinite(alignment) or abs(alignment) <= 1.0e-8:
            raise ValueError(
                "qualified Q4 reference_normal is tangential to the local facet "
                "and cannot establish physical director polarity"
            )
        sign = 1 if alignment > 0.0 else -1
        physical_frame = frame.copy()
        physical_frame[:, 1] *= float(sign)
        physical_frame[:, 2] *= float(sign)
        membrane = np.diag((1.0, 1.0, float(sign)))
        curvature = float(sign) * membrane
        shear = float(sign) * np.diag((1.0, float(sign)))
        return physical_frame, membrane, curvature, shear, sign

    def _generalized_section_in_frame(
        self,
        local_frame: np.ndarray,
    ) -> Optional[GeneralizedShellSection]:
        """Return ABD/As in numbered axes with physical-director covariance."""

        if self.shell_section is None:
            return None
        if (
            np.any(np.asarray(self.shell_section.B, dtype=float) != 0.0)
            and self.reference_normal is None
        ):
            raise ValueError(
                "B-coupled qualified Q4 sections require an authoritative "
                "reference_normal; connectivity winding is not a physical director"
            )
        physical_frame, membrane, curvature, shear, _sign = (
            self._physical_director_context(local_frame)
        )
        physical = self.shell_section.rotated(self._material_angle(physical_frame))
        physical_abd = physical.ABD
        generalized = np.block(
            [
                [membrane, np.zeros((3, 3), dtype=float)],
                [np.zeros((3, 3), dtype=float), curvature],
            ]
        )
        numbered_abd = generalized.T @ physical_abd @ generalized
        numbered_abd = 0.5 * (numbered_abd + numbered_abd.T)
        numbered_shear = shear.T @ physical.As @ shear
        numbered_shear = 0.5 * (numbered_shear + numbered_shear.T)
        return GeneralizedShellSection(
            A=numbered_abd[:3, :3],
            B=numbered_abd[:3, 3:],
            D=numbered_abd[3:, 3:],
            As=numbered_shear,
            name=physical.name,
            mass_per_area=physical.mass_per_area,
            rotary_inertia_per_area=physical.rotary_inertia_per_area,
        )

    def _constitutive_and_drill_stiffness(
        self, material: Any, frame: np.ndarray
    ) -> tuple[np.ndarray, float]:
        constitutive = np.zeros((8, 8), dtype=float)
        if self.shell_section is not None:
            section = self._generalized_section_in_frame(frame)
            assert section is not None
            constitutive[:3, :3] = section.A
            constitutive[:3, 3:6] = section.B
            constitutive[3:6, :3] = section.B.T
            constitutive[3:6, 3:6] = section.D
            constitutive[6:, 6:] = section.As
            drill_stiffness = float(section.A[2, 2])
        else:
            membrane, shear, _strain_transform, _stress_transform = _shell_material_matrices(
                material, self._material_angle(frame)
            )
            constitutive[:3, :3] = self.thickness * membrane
            constitutive[3:6, 3:6] = self.thickness**3 / 12.0 * membrane
            constitutive[6:, 6:] = (5.0 / 6.0) * self.thickness * shear
            drill_stiffness = float(self.thickness * membrane[2, 2])
        if not np.all(np.isfinite(constitutive)) or drill_stiffness <= 0.0:
            raise ValueError("E4-PL constitutive matrix must be finite with positive in-plane shear")
        return constitutive, drill_stiffness

    def _qualified_stiffness_cache_key(
        self,
        mesh: Any,
        material: Any,
        coordinates: Optional[np.ndarray] = None,
    ) -> tuple[Any, ...]:
        coordinates = (
            self.get_node_coordinates(mesh)
            if coordinates is None
            else np.asarray(coordinates, dtype=float)
        )
        revisions = getattr(mesh, "revision_signature", lambda: {})()
        relative = coordinates - np.mean(coordinates, axis=0)
        return (
            id(mesh),
            id(material),
            int(revisions.get("geometry", 0)),
            int(revisions.get("material", 0)),
            np.ascontiguousarray(relative, dtype=float).tobytes(),
            float(self.thickness),
            float(self.drilling_stabilization),
            float(self.hourglass_stabilization),
            float(self.material_angle_deg),
            None
            if self.material_direction is None
            else tuple(np.asarray(self.material_direction, dtype=float)),
            id(self.shell_section),
            None
            if self.reference_normal is None
            else tuple(np.asarray(self.reference_normal, dtype=float)),
            int(self.director_polarity),
            IMPLEMENTATION_ID,
            RECOVERY_POLICY_ID,
            DIRECTOR_POLARITY_POLICY_ID,
            DIRECTOR_REVERSAL_TRANSFORM_ID,
            float(self.pl_stabilization),
            float(self.planar_tolerance),
            self.warped_formulation,
        )

    def _adopt_qualified_components(
        self,
        cache_key: tuple[Any, ...],
        components: Mapping[str, Any],
    ) -> np.ndarray:
        copied: Dict[str, Any] = {}
        for name, value in components.items():
            copied[name] = value.copy() if isinstance(value, np.ndarray) else value
        self._qualified_components = copied
        self._qualified_cache_key = cache_key
        self._hourglass_stiffness_matrix = np.asarray(copied["hourglass"], dtype=float)
        self._stiffness_matrix = np.asarray(copied["total"], dtype=float)
        return self._stiffness_matrix

    def _warped_generalized_drilling_correction(
        self,
        mesh: Any,
        coordinates: np.ndarray,
    ) -> np.ndarray:
        """Replace numbered ``A66`` drilling by its physical invariant."""

        correction = np.zeros((self.total_dofs, self.total_dofs), dtype=float)
        if (
            self.shell_section is None
            or self.reference_normal is None
            or float(self.drilling_stabilization) == 0.0
        ):
            return correction
        coords = np.asarray(coordinates, dtype=float)
        for (xi, eta), weight in zip(self.gauss_points, self.gauss_weights):
            shape, derivative_xi, derivative_eta = self.compute_shape_functions(
                float(xi), float(eta)
            )
            frame, derivative_x, derivative_y, determinant = (
                self._local_frame_and_derivatives(
                    coords,
                    derivative_xi,
                    derivative_eta,
                )
            )
            section = self._generalized_section_in_frame(frame)
            assert section is not None
            numbered_scale = float(section.A[2, 2])
            invariant_scale = _invariant_generalized_drilling_scale(section.A)
            delta = float(self.drilling_stabilization) * (
                invariant_scale - numbered_scale
            )
            if delta == 0.0:
                continue
            drilling = self._build_drilling_b_matrix(
                shape,
                derivative_x,
                derivative_y,
            )
            local = (drilling.T @ (delta * np.eye(1)) @ drilling) * (
                float(determinant) * float(weight)
            )
            transform = self._local_dof_transform(frame)
            correction += transform.T @ local @ transform
        correction[:] = 0.5 * (correction + correction.T)
        return correction

    def compute_stiffness_components(self, mesh: Any, material: Any) -> Dict[str, Any]:
        coordinates = self.get_node_coordinates(mesh)
        cache_key = self._qualified_stiffness_cache_key(mesh, material, coordinates)
        if (
            self._qualified_components is not None
            and self._qualified_cache_key == cache_key
        ):
            return self._qualified_components
        frame, local, warpage = equation7_frame(coordinates)
        if warpage > self.planar_tolerance:
            if self.warped_formulation == "reject":
                raise ValueError(
                    f"E4-PL element {self.element_id} is warped by {warpage:.6e}, "
                    f"above planar_tolerance={self.planar_tolerance:.6e}"
                )
            physical = ShellElement.compute_stiffness_matrix(self, mesh, material)
            director_drilling_correction = self._warped_generalized_drilling_correction(
                mesh,
                coordinates,
            )
            if np.any(director_drilling_correction != 0.0):
                physical = (
                    np.asarray(physical, dtype=float)
                    + director_drilling_correction
                )
                physical = 0.5 * (physical + physical.T)
            zero = np.zeros_like(physical)
            result = {
                "core": physical.copy(),
                "physical": physical.copy(),
                "pl": zero.copy(),
                "hourglass": zero.copy(),
                "numerical": zero.copy(),
                "total": physical.copy(),
                "frame": frame,
                "jacobian_centre": math.nan,
                "mixed_condensed": False,
                "legacy_fallback": False,
                "warped_direct": True,
                "warped_formulation": "varying_frame",
                "warpage_ratio": warpage,
                "director_drilling_correction": director_drilling_correction,
            }
            self._qualified_components = result
            self._qualified_cache_key = cache_key
            return result

        c = _coefficients(local)
        determinants = [c["jc"], *(_jacobian(c, r, s)[4] for r, s in _GAUSS)]
        jacobian_scale = _local_jacobian_scale(local)
        if min(determinants) <= 1.0e-12 * jacobian_scale:
            raise ValueError(f"E4-PL element {self.element_id} has a nonpositive local Jacobian")
        constitutive, drill_stiffness = self._constitutive_and_drill_stiffness(material, frame)
        stationary, coupling, gram = _stationary_blocks(local, c, constitutive)
        solution, stationary_solve_diagnostics = _solve_stationary_system(
            stationary,
            coupling,
        )
        core_local = -coupling @ solution
        core_local = 0.5 * (core_local + core_local.T)
        centre = _centre_taylor(c)
        pl_local = self.pl_stabilization * drill_stiffness * (centre.T @ gram @ centre)
        gamma = _residual_mode(local, c)
        gamma_24 = np.zeros(24, dtype=float)
        gamma_24[5::6] = gamma
        area = 4.0 * c["jc"]
        hourglass_local = (
            2.0
            * float(self.hourglass_stabilization)
            * drill_stiffness
            * area
            * np.outer(gamma_24, gamma_24)
        )
        transform = _global_transform(frame)
        core = transform @ core_local @ transform.T
        pl = transform @ pl_local @ transform.T
        hourglass = transform @ hourglass_local @ transform.T
        for matrix in (core, pl, hourglass):
            matrix[:] = 0.5 * (matrix + matrix.T)
        numerical = pl + hourglass
        total = core + numerical
        result = {
            "core": core,
            "physical": core,
            "pl": pl,
            "hourglass": hourglass,
            "numerical": numerical,
            "total": total,
            "frame": frame,
            "jacobian_centre": c["jc"],
            "mixed_condensed": True,
            "legacy_fallback": False,
            "warped_direct": False,
            "warped_formulation": "planar_e4_pl",
            "warpage_ratio": warpage,
            "stationary_solve_policy_id": STATIONARY_SOLVE_POLICY_ID,
            "stationary_solve_diagnostics": stationary_solve_diagnostics,
        }
        self._qualified_components = result
        self._qualified_cache_key = cache_key
        return result

    def compute_stiffness_matrix(self, mesh: Any, material: Any) -> np.ndarray:
        components = self.compute_stiffness_components(mesh, material)
        self._hourglass_stiffness_matrix = np.asarray(components["hourglass"], dtype=float)
        self._stiffness_matrix = np.asarray(components["total"], dtype=float)
        return self._stiffness_matrix

    def compute_internal_forces(
        self,
        mesh: Any,
        displacements: np.ndarray,
        material: Any,
    ) -> np.ndarray:
        """Return the qualified linear internal force for local or global input."""

        vector = self._get_element_displacements(mesh, displacements)
        return self.compute_stiffness_matrix(mesh, material) @ vector

    def _qualified_linear_correction(
        self,
        mesh: Any,
        material: Any,
        num_layers: int,
    ) -> np.ndarray:
        """Difference between the qualified and inherited elastic tangents.

        The mature ``ShellElement`` nonlinear implementation supplies the
        geometric, material-state and generalized-section increments.  Its
        zero-displacement tangent is the legacy elastic shell, however.  On a
        planar element the constant correction below replaces that baseline
        with E4-PL without disturbing the established nonlinear/state
        algorithms.

        Warped elements without a physical director authority deliberately
        retain the established varying-frame nonlinear mechanics byte for
        byte.  An authoritative generalized section instead receives the
        complete physical-director elastic baseline: the inherited nonlinear
        increments already call ``_generalized_section_in_frame``, while this
        delta removes the numbered zero-state baseline (including its A66
        drill) and installs the covariant varying-frame tangent.
        """

        coordinates = self.get_node_coordinates(mesh)
        _frame, _local, warpage = equation7_frame(coordinates)
        if warpage > self.planar_tolerance and (
            self.shell_section is None or self.reference_normal is None
        ):
            return np.zeros((self.total_dofs, self.total_dofs), dtype=float)

        # The correction is an elastic tangent delta and is independent of
        # the caller's through-thickness integration count.  Use a fixed valid
        # Lobatto rule for the inherited zero-state nonlinear tangent: this
        # preserves the generalized-section baseline while permitting plan
        # cache bookkeeping probes to use arbitrary layer identifiers.
        self._hourglass_stiffness_matrix = None
        _force, legacy, _state = ShellElement.compute_nonlinear_response(
            self,
            mesh,
            material,
            np.zeros(self.total_dofs, dtype=float),
            None,
            5,
            True,
        )
        if legacy is None:
            raise RuntimeError("ShellElement returned no zero-state tangent")
        qualified = np.asarray(self.compute_stiffness_matrix(mesh, material), dtype=float)
        return qualified - np.asarray(legacy, dtype=float)

    def compute_nonlinear_response(
        self,
        mesh: Any,
        material: Any,
        u_elem: np.ndarray,
        state: Optional[Any] = None,
        num_layers: int = 5,
        tangent: bool = True,
    ) -> tuple[np.ndarray, Optional[np.ndarray], Optional[Any]]:
        """Use mature nonlinear/state mechanics with the qualified baseline.

        This additive construction is exact at zero displacement and retains
        the existing von-Karman, plasticity, orthotropy, initial-field and
        generalized-section increments.  Numerical PL/hourglass contributions
        remain a constant separately recoverable part of the tangent.
        """

        vector = np.asarray(u_elem, dtype=float).reshape(self.total_dofs)
        self._hourglass_stiffness_matrix = None
        force, inherited_tangent, trial_state = super().compute_nonlinear_response(
            mesh,
            material,
            vector,
            state,
            num_layers,
            tangent,
        )
        correction = self._qualified_linear_correction(mesh, material, num_layers)
        force = np.asarray(force, dtype=float) + correction @ vector
        if not tangent:
            return force, None, trial_state
        if inherited_tangent is None:
            raise RuntimeError("ShellElement returned no tangent with tangent=True")
        return force, np.asarray(inherited_tangent, dtype=float) + correction, trial_state

    def _recover_planar_mixed_fields(
        self,
        mesh: Any,
        displacements: np.ndarray,
        material: Any,
        natural_points: Sequence[Sequence[float]],
    ) -> Dict[str, np.ndarray]:
        """Evaluate the planar mixed fields at arbitrary natural coordinates.

        This private entry point is intentionally point-agnostic so bounded
        research checks can compare Q4 and S3 resultants at common physical
        locations.  The public recovery contract remains the established four
        Gauss records.
        """

        element_displacements = self._get_element_displacements(mesh, displacements)
        if not np.all(np.isfinite(element_displacements)):
            raise ValueError("qualified Q4 recovery requires finite displacements")
        points = np.asarray(tuple(tuple(point) for point in natural_points), dtype=float)
        if points.size == 0:
            points = np.empty((0, 2), dtype=float)
        if points.ndim != 2 or points.shape[1] != 2 or not np.all(np.isfinite(points)):
            raise ValueError("qualified Q4 recovery points must be a finite Nx2 array")

        coordinates = self.get_node_coordinates(mesh)
        frame, local, warpage = equation7_frame(coordinates)
        if warpage > self.planar_tolerance:
            raise ValueError("planar mixed recovery is unavailable for a warped-direct Q4")
        local_displacement = _global_transform(frame).T @ element_displacements
        c = _coefficients(local)
        determinants = [c["jc"], *(_jacobian(c, r, s)[4] for r, s in _GAUSS)]
        jacobian_scale = _local_jacobian_scale(local)
        if min(determinants) <= 1.0e-12 * jacobian_scale:
            raise ValueError(f"E4-PL element {self.element_id} has a nonpositive local Jacobian")
        constitutive = self._constitutive_and_drill_stiffness(material, frame)[0]
        stationary, coupling, _gram = _stationary_blocks(local, c, constitutive)
        solution, _stationary_solve_diagnostics = _solve_stationary_system(
            stationary,
            coupling,
        )
        stationary_parameters = -solution @ local_displacement
        stress_parameters = stationary_parameters[:14]
        strain_parameters = stationary_parameters[14:]
        stationarity_residual = (
            stationary @ stationary_parameters + coupling.T @ local_displacement
        )
        physical_displacement = np.concatenate(
            tuple(local_displacement[6 * node : 6 * node + 5] for node in range(4))
        )

        compatible = np.zeros((len(points), 8), dtype=float)
        independent = np.zeros_like(compatible)
        resultants = np.zeros_like(compatible)
        point_determinants = np.zeros(len(points), dtype=float)
        for index, (r, s) in enumerate(points):
            determinant = _jacobian(c, float(r), float(s))[4]
            if determinant <= 1.0e-12 * jacobian_scale:
                raise ValueError(
                    f"E4-PL element {self.element_id} has a nonpositive recovery Jacobian"
                )
            n_sigma, n_epsilon = _source_fields(c, float(r), float(s))
            compatible[index] = (
                _compatible(local, c, float(r), float(s)) @ physical_displacement
            )
            independent[index] = n_epsilon @ strain_parameters
            resultants[index] = n_sigma @ stress_parameters
            point_determinants[index] = determinant

        recovered = {
            "frame": frame,
            "local_nodes": local,
            "natural_points": points,
            "local_displacement": local_displacement,
            "physical_displacement": physical_displacement,
            "constitutive": constitutive,
            "stationary_matrix": stationary,
            "stationary_coupling": coupling,
            "stationary_parameters": stationary_parameters,
            "stress_parameters": stress_parameters,
            "strain_parameters": strain_parameters,
            "stationarity_residual": stationarity_residual,
            "compatible": compatible,
            "independent": independent,
            "resultants": resultants,
            "jacobian_determinants": point_determinants,
        }
        for name, values in recovered.items():
            if not np.all(np.isfinite(values)):
                raise ValueError(
                    f"qualified Q4 mixed recovery produced non-finite field {name!r}"
                )
        return recovered

    def _recover_warped_generalized_section(
        self,
        mesh: Any,
        displacements: np.ndarray,
        *,
        return_global: bool,
    ) -> Dict[str, Any]:
        """Physicalize inherited varying-frame generalized Q4 recovery."""

        raw = ShellElement._compute_generalized_section_results(
            self,
            mesh,
            displacements,
            return_global=False,
        )
        coordinates = self.get_node_coordinates(mesh)
        center_numbered = self._center_frame(coordinates)
        center_frame, _center_membrane, _center_curvature, center_shear, center_sign = (
            self._physical_director_context(center_numbered)
        )
        membrane_strain = np.asarray(raw["membrane_strain"], dtype=float).copy()
        curvature = np.asarray(raw["curvature"], dtype=float).copy()
        membrane_resultants = np.asarray(raw["membrane_resultants"], dtype=float).copy()
        bending_resultants = np.asarray(raw["bending_resultants"], dtype=float).copy()
        transverse_shear_strain = (
            np.asarray(raw["transverse_shear_strain"], dtype=float)
            @ center_shear.T
        )
        transverse_shear_resultants = (
            np.asarray(raw["transverse_shear_resultants"], dtype=float)
            @ center_shear.T
        )
        physical_frames = np.zeros((len(self.gauss_points), 3, 3), dtype=float)
        director_signs = np.zeros(len(self.gauss_points), dtype=int)
        for index, (xi, eta) in enumerate(self.gauss_points):
            _shape, derivative_xi, derivative_eta = self.compute_shape_functions(
                float(xi), float(eta)
            )
            numbered, _dx, _dy, _determinant = self._local_frame_and_derivatives(
                coordinates,
                derivative_xi,
                derivative_eta,
            )
            physical, membrane_map, curvature_map, _shear_map, sign = (
                self._physical_director_context(numbered)
            )
            membrane_strain[index] = membrane_map @ membrane_strain[index]
            curvature[index] = curvature_map @ curvature[index]
            membrane_resultants[index] = membrane_map @ membrane_resultants[index]
            bending_resultants[index] = curvature_map @ bending_resultants[index]
            physical_frames[index] = physical
            director_signs[index] = sign

        recovered: Dict[str, Any] = dict(raw)
        recovered.update(
            {
                "membrane_strain": membrane_strain,
                "curvature": curvature,
                "transverse_shear_strain": transverse_shear_strain,
                "membrane_resultants": membrane_resultants,
                "bending_resultants": bending_resultants,
                "transverse_shear_resultants": transverse_shear_resultants,
                "implementation_id": IMPLEMENTATION_ID,
                "recovery_policy_id": RECOVERY_POLICY_ID,
                "director_polarity_policy_id": DIRECTOR_POLARITY_POLICY_ID,
                "director_reversal_transform_id": DIRECTOR_REVERSAL_TRANSFORM_ID,
                "physical_director_authoritative": True,
                "physical_director": center_frame[:, 2].copy(),
                "physical_directors": physical_frames[:, :, 2].copy(),
                "numbered_frame_director_sign": int(center_sign),
                "numbered_frame_director_signs": director_signs,
                "warped_direct": True,
            }
        )
        if return_global:
            global_membrane = np.zeros((len(self.gauss_points), 3, 3), dtype=float)
            global_bending = np.zeros_like(global_membrane)
            for index, frame in enumerate(physical_frames):
                membrane = membrane_resultants[index]
                bending = bending_resultants[index]
                membrane_tensor = np.asarray(
                    (
                        (membrane[0], membrane[2], 0.0),
                        (membrane[2], membrane[1], 0.0),
                        (0.0, 0.0, 0.0),
                    ),
                    dtype=float,
                )
                bending_tensor = np.asarray(
                    (
                        (bending[0], bending[2], 0.0),
                        (bending[2], bending[1], 0.0),
                        (0.0, 0.0, 0.0),
                    ),
                    dtype=float,
                )
                global_membrane[index] = frame @ membrane_tensor @ frame.T
                global_bending[index] = frame @ bending_tensor @ frame.T
            global_shear = (
                transverse_shear_resultants[:, :1] * center_frame[:, 0][None, :]
                + transverse_shear_resultants[:, 1:] * center_frame[:, 1][None, :]
            )
            recovered.update(
                {
                    "global_membrane_resultant_tensors": global_membrane,
                    "global_bending_resultant_tensors": global_bending,
                    "global_transverse_shear_resultants": global_shear,
                }
            )
        for name, values in recovered.items():
            if isinstance(values, np.ndarray) and not np.all(np.isfinite(values)):
                raise ValueError(
                    f"qualified warped Q4 recovery produced non-finite field {name!r}"
                )
        return recovered

    def _recover_warped_homogeneous_section(
        self,
        mesh: Any,
        displacements: np.ndarray,
        material: Any,
        *,
        return_global: bool,
    ) -> Dict[str, Any]:
        """Return warped homogeneous stresses in physical-director frames."""

        raw = ShellElement.compute_stresses(
            self,
            mesh,
            displacements,
            material,
            return_global=False,
        )
        coordinates = self.get_node_coordinates(mesh)
        center_numbered = self._center_frame(coordinates)
        center_frame, _center_membrane, _center_curvature, center_shear, center_sign = (
            self._physical_director_context(center_numbered)
        )
        numbered_membrane = np.column_stack(
            (raw["membrane_xx"], raw["membrane_yy"], raw["membrane_xy"])
        )
        numbered_bending = np.column_stack(
            (raw["bending_xx"], raw["bending_yy"], raw["bending_xy"])
        )
        numbered_shear = np.column_stack((raw["shear_xz"], raw["shear_yz"]))
        membrane = numbered_membrane.copy()
        bending = numbered_bending.copy()
        shear = numbered_shear @ center_shear.T
        physical_frames = np.zeros((len(self.gauss_points), 3, 3), dtype=float)
        director_signs = np.zeros(len(self.gauss_points), dtype=int)
        for index, (xi, eta) in enumerate(self.gauss_points):
            _shape, derivative_xi, derivative_eta = self.compute_shape_functions(
                float(xi), float(eta)
            )
            numbered, _dx, _dy, _determinant = self._local_frame_and_derivatives(
                coordinates,
                derivative_xi,
                derivative_eta,
            )
            physical, membrane_map, curvature_map, _shear_map, sign = (
                self._physical_director_context(numbered)
            )
            membrane[index] = membrane_map @ numbered_membrane[index]
            bending[index] = curvature_map @ numbered_bending[index]
            physical_frames[index] = physical
            director_signs[index] = sign

        recovered: Dict[str, Any] = dict(raw)
        recovered.update(
            {
                "membrane_xx": membrane[:, 0].copy(),
                "membrane_yy": membrane[:, 1].copy(),
                "membrane_xy": membrane[:, 2].copy(),
                "bending_xx": bending[:, 0].copy(),
                "bending_yy": bending[:, 1].copy(),
                "bending_xy": bending[:, 2].copy(),
                "shear_xz": shear[:, 0].copy(),
                "shear_yz": shear[:, 1].copy(),
                "implementation_id": IMPLEMENTATION_ID,
                "recovery_policy_id": RECOVERY_POLICY_ID,
                "director_polarity_policy_id": DIRECTOR_POLARITY_POLICY_ID,
                "director_reversal_transform_id": DIRECTOR_REVERSAL_TRANSFORM_ID,
                "physical_director_authoritative": True,
                "physical_director": center_frame[:, 2].copy(),
                "physical_directors": physical_frames[:, :, 2].copy(),
                "numbered_frame_director_sign": int(center_sign),
                "numbered_frame_director_signs": director_signs,
                "warped_direct": True,
            }
        )
        von_mises = np.zeros(len(self.gauss_points), dtype=float)
        equivalent = np.zeros_like(von_mises)
        utilization = np.zeros_like(von_mises)
        hill_yield = getattr(material, "hill_yield", None)
        global_shear = (
            shear[:, :1] * center_frame[:, 0][None, :]
            + shear[:, 1:] * center_frame[:, 1][None, :]
        )
        for index, frame in enumerate(physical_frames):
            tangent_shear = global_shear[index] - (
                float(global_shear[index] @ frame[:, 2]) * frame[:, 2]
            )
            local_shear = np.asarray(
                (
                    float(tangent_shear @ frame[:, 0]),
                    float(tangent_shear @ frame[:, 1]),
                ),
                dtype=float,
            )
            top = membrane[index] + bending[index]
            bottom = membrane[index] - bending[index]
            vm_top = math.sqrt(
                top[0] * top[0]
                - top[0] * top[1]
                + top[1] * top[1]
                + 3.0
                * (
                    top[2] * top[2]
                    + local_shear[0] * local_shear[0]
                    + local_shear[1] * local_shear[1]
                )
            )
            vm_bottom = math.sqrt(
                bottom[0] * bottom[0]
                - bottom[0] * bottom[1]
                + bottom[1] * bottom[1]
                + 3.0
                * (
                    bottom[2] * bottom[2]
                    + local_shear[0] * local_shear[0]
                    + local_shear[1] * local_shear[1]
                )
            )
            von_mises[index] = max(vm_top, vm_bottom)
            if hill_yield is None:
                equivalent[index] = von_mises[index]
            else:
                from .plasticity import hill48_plane_stress_equivalent_stress

                _membrane, _shear, _strain_to_material, stress_to_local = (
                    _shell_material_matrices(material, self._material_angle(frame))
                )
                material_stresses = np.linalg.solve(
                    stress_to_local,
                    np.vstack((top, bottom)).T,
                ).T
                values = hill48_plane_stress_equivalent_stress(
                    material_stresses,
                    hill_yield,
                )
                equivalent[index] = float(np.max(values))
                utilization[index] = equivalent[index] / max(
                    float(hill_yield.X),
                    np.finfo(float).tiny,
                )
            if return_global:
                for surface, values in (("top", top), ("bot", bottom)):
                    local_tensor = np.asarray(
                        (
                            (values[0], values[2], local_shear[0]),
                            (values[2], values[1], local_shear[1]),
                            (local_shear[0], local_shear[1], 0.0),
                        ),
                        dtype=float,
                    )
                    global_tensor = frame @ local_tensor @ frame.T
                    for first, second, label in (
                        (0, 0, "xx"),
                        (1, 1, "yy"),
                        (2, 2, "zz"),
                        (0, 1, "xy"),
                        (1, 2, "yz"),
                        (0, 2, "xz"),
                    ):
                        recovered[f"local_{label}_{surface}"] = recovered.get(
                            f"local_{label}_{surface}",
                            np.zeros(len(self.gauss_points), dtype=float),
                        )
                        recovered[f"global_{label}_{surface}"] = recovered.get(
                            f"global_{label}_{surface}",
                            np.zeros(len(self.gauss_points), dtype=float),
                        )
                        recovered[f"local_{label}_{surface}"][index] = local_tensor[
                            first, second
                        ]
                        recovered[f"global_{label}_{surface}"][index] = global_tensor[
                            first, second
                        ]
        recovered["von_mises"] = von_mises
        recovered["equivalent_stress"] = equivalent
        recovered["hill_utilization"] = utilization
        for name, values in recovered.items():
            if isinstance(values, np.ndarray) and not np.all(np.isfinite(values)):
                raise ValueError(
                    f"qualified warped Q4 recovery produced non-finite field {name!r}"
                )
        return recovered

    def compute_stresses(
        self,
        mesh: Any,
        displacements: np.ndarray,
        material: Any,
        return_global: bool = False,
    ) -> Dict[str, Any]:
        """Recover formulation-native planar physical fields at four points.

        Planar resultants come from the same 35-field stationary system used
        by the condensed tangent.  PL and drilling-hourglass fields are not
        present in this recovery.  The established varying-frame implementation
        remains authoritative for genuinely warped facets.
        """

        coordinates = self.get_node_coordinates(mesh)
        _frame, _local, warpage = equation7_frame(coordinates)
        if warpage > self.planar_tolerance:
            if self.warped_formulation == "reject":
                raise ValueError(
                    f"E4-PL element {self.element_id} is warped by {warpage:.6e}, "
                    f"above planar_tolerance={self.planar_tolerance:.6e}"
                )
            if self.reference_normal is None:
                return ShellElement.compute_stresses(
                    self,
                    mesh,
                    displacements,
                    material,
                    return_global=return_global,
                )
            if self.shell_section is not None:
                return self._recover_warped_generalized_section(
                    mesh,
                    displacements,
                    return_global=return_global,
                )
            return self._recover_warped_homogeneous_section(
                mesh,
                displacements,
                material,
                return_global=return_global,
            )

        mixed = self._recover_planar_mixed_fields(
            mesh,
            displacements,
            material,
            _GAUSS,
        )
        numbered_frame = mixed["frame"]
        frame, membrane_map, curvature_map, shear_map, director_sign = (
            self._physical_director_context(numbered_frame)
        )
        numbered_independent = mixed["independent"]
        numbered_compatible = mixed["compatible"]
        numbered_resultants = mixed["resultants"]
        independent = np.column_stack(
            (
                numbered_independent[:, :3] @ membrane_map.T,
                numbered_independent[:, 3:6] @ curvature_map.T,
                numbered_independent[:, 6:] @ shear_map.T,
            )
        )
        compatible = np.column_stack(
            (
                numbered_compatible[:, :3] @ membrane_map.T,
                numbered_compatible[:, 3:6] @ curvature_map.T,
                numbered_compatible[:, 6:] @ shear_map.T,
            )
        )
        resultants = np.column_stack(
            (
                numbered_resultants[:, :3] @ membrane_map.T,
                numbered_resultants[:, 3:6] @ curvature_map.T,
                numbered_resultants[:, 6:] @ shear_map.T,
            )
        )
        recovered: Dict[str, Any] = {
            "recovery_scope": (
                "section_resultants_only"
                if self.shell_section is not None
                else "qualified_q4_local_and_global_physical"
                if return_global
                else "qualified_q4_local_physical_only"
            ),
            "physical_stress_available": self.shell_section is None,
            "membrane_resultant_order": SHELL_MEMBRANE_VOIGT_ORDER,
            "transverse_shear_resultant_order": SHELL_TRANSVERSE_SHEAR_ORDER,
            "membrane_strain": independent[:, :3].copy(),
            "curvature": independent[:, 3:6].copy(),
            "transverse_shear_strain": independent[:, 6:].copy(),
            "compatible_membrane_strain": compatible[:, :3].copy(),
            "compatible_curvature": compatible[:, 3:6].copy(),
            "compatible_transverse_shear_strain": compatible[:, 6:].copy(),
            "membrane_resultants": resultants[:, :3].copy(),
            "bending_resultants": resultants[:, 3:6].copy(),
            "transverse_shear_resultants": resultants[:, 6:].copy(),
            "numerical_fields_excluded": True,
            "implementation_id": IMPLEMENTATION_ID,
            "recovery_policy_id": RECOVERY_POLICY_ID,
            "director_polarity_policy_id": DIRECTOR_POLARITY_POLICY_ID,
            "director_reversal_transform_id": DIRECTOR_REVERSAL_TRANSFORM_ID,
            "physical_director_authoritative": self.reference_normal is not None,
            "physical_director": frame[:, 2].copy(),
            "numbered_frame_director_sign": int(director_sign),
        }
        if self.shell_section is not None:
            recovered["generalized_stress_scope"] = "section_resultants_only"

        if return_global:
            global_membrane = np.zeros((len(_GAUSS), 3, 3), dtype=float)
            global_bending = np.zeros_like(global_membrane)
            global_shear = np.zeros((len(_GAUSS), 3), dtype=float)
            for index in range(len(_GAUSS)):
                membrane = resultants[index, :3]
                bending = resultants[index, 3:6]
                membrane_tensor = np.asarray(
                    (
                        (membrane[0], membrane[2], 0.0),
                        (membrane[2], membrane[1], 0.0),
                        (0.0, 0.0, 0.0),
                    ),
                    dtype=float,
                )
                bending_tensor = np.asarray(
                    (
                        (bending[0], bending[2], 0.0),
                        (bending[2], bending[1], 0.0),
                        (0.0, 0.0, 0.0),
                    ),
                    dtype=float,
                )
                global_membrane[index] = frame @ membrane_tensor @ frame.T
                global_bending[index] = frame @ bending_tensor @ frame.T
                global_shear[index] = (
                    resultants[index, 6] * frame[:, 0]
                    + resultants[index, 7] * frame[:, 1]
                )
            recovered.update(
                {
                    "global_membrane_resultant_tensors": global_membrane,
                    "global_bending_resultant_tensors": global_bending,
                    "global_transverse_shear_resultants": global_shear,
                }
            )

        if self.shell_section is None:
            thickness = float(self.thickness)
            if not math.isfinite(thickness) or thickness <= 0.0:
                raise ValueError("qualified Q4 recovery requires positive finite thickness")
            membrane_stress = resultants[:, :3] / thickness
            bending_stress = 6.0 * resultants[:, 3:6] / (thickness * thickness)
            transverse = resultants[:, 6:] / thickness
            recovered.update(
                {
                    "membrane_xx": membrane_stress[:, 0].copy(),
                    "membrane_yy": membrane_stress[:, 1].copy(),
                    "membrane_xy": membrane_stress[:, 2].copy(),
                    "bending_xx": bending_stress[:, 0].copy(),
                    "bending_yy": bending_stress[:, 1].copy(),
                    "bending_xy": bending_stress[:, 2].copy(),
                    "shear_xz": transverse[:, 0].copy(),
                    "shear_yz": transverse[:, 1].copy(),
                }
            )
            top = membrane_stress + bending_stress
            bottom = membrane_stress - bending_stress
            vm_top = np.sqrt(
                top[:, 0] ** 2
                - top[:, 0] * top[:, 1]
                + top[:, 1] ** 2
                + 3.0
                * (top[:, 2] ** 2 + transverse[:, 0] ** 2 + transverse[:, 1] ** 2)
            )
            vm_bottom = np.sqrt(
                bottom[:, 0] ** 2
                - bottom[:, 0] * bottom[:, 1]
                + bottom[:, 1] ** 2
                + 3.0
                * (
                    bottom[:, 2] ** 2
                    + transverse[:, 0] ** 2
                    + transverse[:, 1] ** 2
                )
            )
            recovered["von_mises"] = np.maximum(vm_top, vm_bottom)
            recovered["hill_utilization"] = np.zeros(len(_GAUSS), dtype=float)
            hill_yield = getattr(material, "hill_yield", None)
            if hill_yield is not None:
                from .plasticity import hill48_plane_stress_equivalent_stress

                _membrane, _shear, _strain_to_material, stress_to_local = (
                    _shell_material_matrices(material, self._material_angle(frame))
                )
                top_material = np.linalg.solve(stress_to_local, top.T).T
                bottom_material = np.linalg.solve(stress_to_local, bottom.T).T
                hill_top = hill48_plane_stress_equivalent_stress(
                    top_material,
                    hill_yield,
                )
                hill_bottom = hill48_plane_stress_equivalent_stress(
                    bottom_material,
                    hill_yield,
                )
                equivalent = np.maximum(hill_top, hill_bottom)
                recovered["equivalent_stress"] = equivalent
                recovered["hill_utilization"] = equivalent / max(
                    float(hill_yield.X),
                    np.finfo(float).tiny,
                )
                recovered["equivalent_stress_measure"] = "hill48"
            else:
                recovered["equivalent_stress"] = recovered["von_mises"].copy()
                recovered["equivalent_stress_measure"] = "von_mises"

            if return_global:
                for surface, values in (("top", top), ("bot", bottom)):
                    local_tensors = np.zeros((len(_GAUSS), 3, 3), dtype=float)
                    local_tensors[:, 0, 0] = values[:, 0]
                    local_tensors[:, 1, 1] = values[:, 1]
                    local_tensors[:, 0, 1] = values[:, 2]
                    local_tensors[:, 1, 0] = values[:, 2]
                    local_tensors[:, 0, 2] = transverse[:, 0]
                    local_tensors[:, 2, 0] = transverse[:, 0]
                    local_tensors[:, 1, 2] = transverse[:, 1]
                    local_tensors[:, 2, 1] = transverse[:, 1]
                    global_tensors = np.asarray(
                        [frame @ tensor @ frame.T for tensor in local_tensors],
                        dtype=float,
                    )
                    for first, second, label in (
                        (0, 0, "xx"),
                        (1, 1, "yy"),
                        (2, 2, "zz"),
                        (0, 1, "xy"),
                        (1, 2, "yz"),
                        (0, 2, "xz"),
                    ):
                        recovered[f"local_{label}_{surface}"] = local_tensors[
                            :, first, second
                        ].copy()
                        recovered[f"global_{label}_{surface}"] = global_tensors[
                            :, first, second
                        ].copy()

        for name, values in recovered.items():
            if isinstance(values, np.ndarray) and not np.all(np.isfinite(values)):
                raise ValueError(
                    f"qualified Q4 recovery produced non-finite field {name!r}"
                )
        return recovered

    def numerical_internal_force(self, displacement: np.ndarray) -> Dict[str, np.ndarray]:
        """Return PL/hourglass forces separately from physical recovery."""

        if self._qualified_components is None:
            raise RuntimeError("compute_stiffness_matrix must run before numerical force recovery")
        vector = np.asarray(displacement, dtype=float).reshape(self.total_dofs)
        return {
            "pl": np.asarray(self._qualified_components["pl"]) @ vector,
            "hourglass": np.asarray(self._qualified_components["hourglass"]) @ vector,
            "numerical": np.asarray(self._qualified_components["numerical"]) @ vector,
        }


__all__ = [
    "DIRECTOR_POLARITY_POLICY_ID",
    "DIRECTOR_REVERSAL_TRANSFORM_ID",
    "FORMULATION_ID",
    "IMPLEMENTATION_ID",
    "QualifiedE4PLShellElement",
    "QualifiedQ4MigrationWarning",
    "RECOVERY_POLICY_ID",
    "STATIONARY_SOLVE_POLICY_ID",
    "equation7_frame",
]
