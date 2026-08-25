"""Opt-in flat MITC3+ companion for the qualified E4-PL Q4 shell.

This module implements the frozen formulation and its formulation-native
stiffness, nonlinear, mass, initial-stress and physical-recovery operators.  It
does not inherit the legacy TRI3 strain, assumed-shear, drilling, nonlinear,
dynamic, buckling or recovery mechanics.  Capabilities that still need
formulation-native work fail closed; see :data:`CAPABILITY_GAPS`.

The assumed-shear equations are Eqs. (7), (13), (15)--(17) of Lee, Lee and
Bathe, *Computers & Structures* 138 (2014) 12--23.  The public author copy
used for the equation map is bound below by byte count and SHA-256.
"""

from __future__ import annotations

import math
from types import MappingProxyType
from typing import Any, Callable, Dict, Mapping, Optional, Sequence

import numpy as np

from ._native_rotation_state import (
    NativeElementRotationView,
    rotation_exponential,
)
from .elements import (
    ShellElement,
    _copy_state_fields,
    _elastic_symmetry,
    _shell_field_rows,
    _shell_material_matrices,
)
from .element_capabilities import (
    STATEFUL_MATERIAL_RESPONSE_MODE,
    STATELESS_FIXED_GENERALIZED_SECTION_RESPONSE_MODE,
)
from .e4_pl_s3_state import (
    BUBBLE_CONVENTION,
    BUBBLE_CONDITION_LIMIT,
    BUBBLE_FORCE_CONDENSATION_ID,
    BUBBLE_LINE_SEARCH_MIN_FACTOR,
    BUBBLE_LINE_SEARCH_REDUCTION,
    BUBBLE_MAX_ITERATIONS,
    BUBBLE_OFFSET_D,
    BUBBLE_POLYNOMIAL_SCALE,
    BUBBLE_RELATIVE_TOLERANCE,
    BUBBLE_STEP_TOLERANCE,
    INITIAL_FIELD_NAMES,
    canonical_json_bytes,
    build_element_configuration_descriptor,
    build_generalized_element_configuration_descriptor,
    build_generalized_state_identity,
    build_state_identity,
    DIRECTOR_GAUGE_ID,
    DIRECTOR_POLARITY_POLICY_ID,
    DIRECTOR_REVERSAL_TRANSFORM_ID,
    DRILL_SCALE_INVERSE_METRIC_SQRT,
    DRILL_SCALE_PROJECTOR,
    EXTERNAL_ROTATION_MAP_ID,
    FORMULATION_ID,
    FORMULATION_SCHEMA,
    MITC3_PLUS_EQUATION_MAP,
    MITC3_PLUS_NONLINEAR_EQUATION_MAP,
    MITC3_PLUS_NONLINEAR_SOURCE_BYTES,
    MITC3_PLUS_NONLINEAR_SOURCE_SHA256,
    MITC3_PLUS_NONLINEAR_SOURCE_URL,
    MITC3_PLUS_SOURCE_BYTES,
    MITC3_PLUS_SOURCE_SHA256,
    MITC3_PLUS_SOURCE_URL,
    MINIMUM_OWNER_NORMAL_ALIGNMENT,
    NODAL_ROTATION_UPDATE_POLICY_ID,
    NONLINEAR_PL_ENERGY_POLICY_ID,
    NONLINEAR_POLICY_ID,
    PL_MINIMUM_TWIST_DENOMINATOR,
    PL_PHASE_POLICY_ID,
    PL_PHASE_MARGIN,
    PL_GRAM_NUMERATOR,
    PL_TWIST_POLICY_ID,
    QUADRATURE_ID,
    RECOVERY_POLICY_ID,
    REFERENCE_SURFACE_MASS_SHIFT_ID,
    REFERENCE_SURFACE_OFFSET_POLICY_ID,
    REFERENCE_SURFACE_STRAIN_TRANSFORM_ID,
    S3CommittedStateError,
    STIFFNESS_STATION_TABLE,
    SURFACE_ROTATION_POLICY_ID,
    TYING_POINTS,
    qualified_s3_lobatto_layers,
    qualified_s3_triangle_frame,
    reconstruct_director_triad,
    require_qualified_s3_quality,
    initialize_zero_committed_s3_state,
    initialize_zero_committed_s3_generalized_state,
    resolved_material_descriptor,
    require_stateless_generalized_section,
    seal_committed_s3_state,
    validate_committed_s3_generalized_state,
    validate_committed_s3_state,
)
from .material_curves import DNVC208MaterialCurve
from .materials import Hill48Yield, is_isotropic_material
from .plasticity import plane_stress_return_map
from .shell_sections import (
    SHELL_MEMBRANE_VOIGT_ORDER,
    SHELL_TRANSVERSE_SHEAR_ORDER,
)


DYNAMIC_REDUCTION_POLICY = "GUYAN_STATIC_BUBBLE_FULL_CONSISTENT_MASS_V1"
MASS_MOMENT_ID = "ANALYTIC_BARYCENTRIC_B2_DEGREE6_V1"
ALGEBRAIC_COORDINATE_POLICY_ID = "S3_NODAL_DRILL_ZERO_INERTIA_V1"
GEOMETRIC_STIFFNESS_POLICY_ID = (
    "TOTAL_LAGRANGIAN_MINDLIN_BUBBLE_SCHUR_INITIAL_STRESS_V1"
)
HOMOGENEOUS_ELASTIC_STRESS_PROFILE_ID = (
    "HOMOGENEOUS_ELASTIC_LINEAR_THROUGH_THICKNESS_V1"
)
REFERENCE_ELASTIC_BUBBLE_LINEARIZATION_ID = (
    "REFERENCE_ELASTIC_BUBBLE_SCHUR_DERIVATIVE_V1"
)
RESULTANT_SUMMARY_POLICY_ID = "QUADRATURE_WEIGHTED_INTEGRATION_STATION_MEAN_V1"
STATE_LAYOUT_ID = "S3_EXTERNAL18_BUBBLE2_PL3_LINEAR_V1"
CURRENT_STATE_TANGENT_DECOMPOSITION_POLICY_ID = (
    "COMMITTED_NATIVE_MATERIAL_PLUS_STRESS_HESSIAN_SINGLE_BUBBLE_MAP_V1"
)
CURRENT_STATE_BUBBLE_PROJECTION_POLICY_ID = (
    "TOTAL_KAA_KAQ_SENSITIVITY_PROJECTS_EACH_TANGENT_PIECE_V1"
)

_INITIAL_SHELL_STATE_KEYS = (
    "initial_membrane_stress",
    "initial_bending_stress",
    "initial_membrane_prestrain",
    "initial_curvature_prestrain",
    "initial_field_provenance",
)
_BUBBLE_MAX_ITERATIONS = BUBBLE_MAX_ITERATIONS
_BUBBLE_RELATIVE_TOLERANCE = BUBBLE_RELATIVE_TOLERANCE
_BUBBLE_STEP_TOLERANCE = BUBBLE_STEP_TOLERANCE

TRIANGLE_QUADRATURE = STIFFNESS_STATION_TABLE

PHYSICAL_EXTERNAL_INDICES = np.asarray(
    [6 * node + component for node in range(3) for component in range(5)],
    dtype=np.intp,
)

CAPABILITY_GAPS = frozenset(
    {
        "buckling",
        "committed_state_recovery",
        "contact_state",
        "initial_fields",
        "material_nonlinearity",
        "nonlinear_geometry",
        "patch_recovery",
        "physical_director_reversal",
        "restart_history",
        "static_restart_history",
        "arc_length_restart_history",
    }
)

_LAYERED_NATIVE_CLOSED_CAPABILITIES = frozenset(
    {
        "arc_length_restart_history",
        "committed_state_recovery",
        "contact_state",
        "initial_fields",
        "material_nonlinearity",
        "nonlinear_geometry",
        "patch_recovery",
        "physical_director_reversal",
        "static_restart_history",
    }
)

_GENERALIZED_NATIVE_CLOSED_CAPABILITIES = frozenset(
    {
        "arc_length_restart_history",
        "committed_state_recovery",
        "contact_state",
        "initial_fields",
        "nonlinear_geometry",
        "physical_director_reversal",
        "static_restart_history",
    }
)


def _normalize(vector: np.ndarray, label: str) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    if not math.isfinite(norm) or norm <= np.finfo(float).tiny:
        raise ValueError(f"cannot normalize S3 {label}")
    return vector / norm


def _matrix_rank(matrix: np.ndarray) -> int:
    equilibrated = _equilibrated_symmetric(matrix)
    singular = np.linalg.svd(equilibrated, compute_uv=False)
    if singular.size == 0 or singular[0] == 0.0:
        return 0
    tolerance = 4096.0 * max(matrix.shape) * np.finfo(float).eps * singular[0]
    return int(np.count_nonzero(singular > tolerance))


def _inertia(matrix: np.ndarray) -> tuple[int, int, int]:
    equilibrated = _equilibrated_symmetric(matrix)
    eigenvalues = np.linalg.eigvalsh(equilibrated)
    scale = max(float(np.max(np.abs(eigenvalues))), 1.0)
    tolerance = 4096.0 * max(matrix.shape) * np.finfo(float).eps * scale
    return (
        int(np.count_nonzero(eigenvalues > tolerance)),
        int(np.count_nonzero(eigenvalues < -tolerance)),
        int(np.count_nonzero(np.abs(eigenvalues) <= tolerance)),
    )


def _rectangular_rank(matrix: np.ndarray) -> int:
    """Rank of an already nondimensional kinematic/coupling operator."""

    made = np.asarray(matrix, dtype=float)
    if made.ndim != 2 or not np.all(np.isfinite(made)):
        raise ValueError("S3 structural-rank operator must be a finite matrix")
    singular = np.linalg.svd(made, compute_uv=False)
    if singular.size == 0 or singular[0] == 0.0:
        return 0
    tolerance = 4096.0 * max(made.shape) * np.finfo(float).eps * singular[0]
    return int(np.count_nonzero(singular > tolerance))


def _structural_rank_certificate(
    operators: Sequence[np.ndarray],
    constraint: np.ndarray,
    characteristic_length: float,
) -> Dict[str, Any]:
    """Certify staged ranks from the dimensionless kinematic subspaces.

    For a positive section and positive quadrature, ``rank(K)=rank(B)``.
    Working with B avoids declaring the legitimate ``(t/L)^2`` separation of
    membrane and bending energy to be a zero mode.  The condensed physical
    range is the part of the external operator outside the two bubble columns;
    PL rank addition is then checked on that quotient directly.
    """

    length = float(characteristic_length)
    if not math.isfinite(length) or length <= 0.0:
        raise ValueError("S3 characteristic length must be finite and positive")
    column_scale_17 = np.ones(17, dtype=float)
    for node in range(3):
        column_scale_17[5 * node : 5 * node + 3] = length
    row_scale = np.asarray((1.0, 1.0, 1.0, length, length, length, 1.0, 1.0))
    made = np.vstack(
        [row_scale[:, None] * np.asarray(item) * column_scale_17[None, :] for item in operators]
    )
    external = made[:, :15]
    bubble = made[:, 15:]
    bubble_solution, *_ = np.linalg.lstsq(bubble, external, rcond=None)
    condensed = external - bubble @ bubble_solution

    embedded = np.zeros((condensed.shape[0], 18), dtype=float)
    embedded[:, PHYSICAL_EXTERNAL_INDICES] = condensed
    column_scale_18 = np.ones(18, dtype=float)
    for node in range(3):
        column_scale_18[6 * node : 6 * node + 3] = length
    pl_operator = np.asarray(constraint, dtype=float) * column_scale_18[None, :]
    total_operator = np.vstack((embedded, pl_operator))

    uncondensed_20 = np.zeros((made.shape[0], 20), dtype=float)
    combined = np.concatenate((PHYSICAL_EXTERNAL_INDICES, np.asarray((18, 19))))
    uncondensed_20[:, combined] = made
    pl_20 = np.zeros((3, 20), dtype=float)
    pl_20[:, :18] = pl_operator
    positive_saddle_rank = _rectangular_rank(np.vstack((uncondensed_20, pl_20)))
    nullity = 20 - positive_saddle_rank
    return {
        "uncondensed_physical_rank": _rectangular_rank(made),
        "bubble_rank": _rectangular_rank(bubble),
        "condensed_physical_rank": _rectangular_rank(condensed),
        "embedded_physical_rank": _rectangular_rank(embedded),
        "pl_rank": _rectangular_rank(pl_operator),
        "total_rank": _rectangular_rank(total_operator),
        "saddle_rank": positive_saddle_rank + 3,
        "saddle_inertia": (positive_saddle_rank, 3, nullity),
    }


def _equilibrated_symmetric(matrix: np.ndarray) -> np.ndarray:
    """Return a unit- and DOF-scaled congruence for rank/inertia diagnostics.

    Raw shell matrices mix translational, rotational, bubble, and multiplier
    coordinates and span membrane/bending scales.  A raw SVD therefore changes
    its reported rank under passive unit conversion.  Positive diagonal energy
    is the natural congruence scale; the row maximum is a fail-closed fallback
    for an indefinite saddle coordinate whose diagonal is exactly zero.
    """

    made = np.asarray(matrix, dtype=float)
    if made.ndim != 2 or made.shape[0] != made.shape[1]:
        raise ValueError("S3 rank diagnostics require a square matrix")
    if not np.all(np.isfinite(made)):
        raise ValueError("S3 rank diagnostics require finite entries")
    symmetric = 0.5 * (made + made.T)
    equilibrated = symmetric.copy()
    # Symmetric Ruiz max-norm equilibration also balances the q/tau coupling
    # of the indefinite PL saddle, where diagonal-only Jacobi scaling leaves
    # a dimensioned off-diagonal block many orders larger than unity.
    for _iteration in range(32):
        row_scale = np.max(np.abs(equilibrated), axis=1)
        active = row_scale > 0.0
        scaling = np.ones_like(row_scale)
        scaling[active] = 1.0 / np.sqrt(row_scale[active])
        equilibrated = scaling[:, None] * equilibrated * scaling[None, :]
    return 0.5 * (equilibrated + equilibrated.T)


def triangle_frame(
    nodes: Sequence[Sequence[float]],
    reference_normal: Optional[Sequence[float]] = None,
) -> tuple[np.ndarray, np.ndarray, Dict[str, float]]:
    """Return the numbered flat-triangle frame, local nodes and quality data."""

    try:
        return qualified_s3_triangle_frame(
            nodes,
            reference_normal,
            enforce_admission=False,
        )
    except S3CommittedStateError as exc:
        raise ValueError(str(exc)) from exc


def _require_admitted_quality(
    quality: Mapping[str, float], *, enforce_positive_winding: bool = True
) -> None:
    try:
        require_qualified_s3_quality(
            quality,
            enforce_positive_winding=enforce_positive_winding,
        )
    except S3CommittedStateError as exc:
        raise ValueError(str(exc)) from exc


def invariant_drilling_scale(membrane_matrix: np.ndarray) -> float:
    """Return the frozen basis-invariant membrane shear scale ``k_D``."""

    membrane = np.asarray(membrane_matrix, dtype=float)
    if membrane.shape != (3, 3) or not np.all(np.isfinite(membrane)):
        raise ValueError("S3 membrane matrix A must be a finite 3x3 matrix")
    membrane = 0.5 * (membrane + membrane.T)
    membrane_eigenvalues = np.linalg.eigvalsh(membrane)
    if float(membrane_eigenvalues[0]) <= 0.0:
        raise ValueError("S3 membrane matrix A must be positive definite")
    projector = np.asarray(DRILL_SCALE_PROJECTOR, dtype=float)
    restricted = projector.T @ membrane @ projector
    inverse_metric_sqrt = np.asarray(DRILL_SCALE_INVERSE_METRIC_SQRT, dtype=float)
    canonical = inverse_metric_sqrt @ restricted @ inverse_metric_sqrt
    value = 0.5 * float(np.linalg.eigvalsh(0.5 * (canonical + canonical.T))[0])
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError("S3 invariant drilling scale must be finite and positive")
    return value


def _is_isotropic_engineering_matrix(matrix: np.ndarray) -> bool:
    values = np.asarray(matrix, dtype=float)
    if values.shape != (3, 3):
        return False
    scale = max(float(np.linalg.norm(values, ord=np.inf)), 1.0)
    tolerance = 1.0e-10 * scale
    target = np.asarray(
        (
            (values[0, 0], values[0, 1], 0.0),
            (values[0, 1], values[0, 0], 0.0),
            (0.0, 0.0, 0.5 * (values[0, 0] - values[0, 1])),
        ),
        dtype=float,
    )
    return bool(np.linalg.norm(values - target, ord=np.inf) <= tolerance)


def _is_rotation_invariant_section(section: Any) -> bool:
    if not all(
        _is_isotropic_engineering_matrix(matrix)
        for matrix in (section.A, section.B, section.D)
    ):
        return False
    shear = np.asarray(section.As, dtype=float)
    scale = max(float(np.linalg.norm(shear, ord=np.inf)), 1.0)
    target = float(np.trace(shear) / 2.0) * np.eye(2)
    return bool(np.linalg.norm(shear - target, ord=np.inf) <= 1.0e-10 * scale)


def _reference_fields(r: float, s: float) -> tuple[np.ndarray, np.ndarray, np.ndarray, float, float, float]:
    shape = np.asarray((1.0 - r - s, r, s), dtype=float)
    derivative_r = np.asarray((-1.0, 1.0, 0.0), dtype=float)
    derivative_s = np.asarray((-1.0, 0.0, 1.0), dtype=float)
    bubble = BUBBLE_POLYNOMIAL_SCALE * r * s * (1.0 - r - s)
    bubble_r = BUBBLE_POLYNOMIAL_SCALE * s * (1.0 - 2.0 * r - s)
    bubble_s = BUBBLE_POLYNOMIAL_SCALE * r * (1.0 - r - 2.0 * s)
    return shape, derivative_r, derivative_s, bubble, bubble_r, bubble_s


def _jacobian(local: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
    jacobian = np.asarray(
        (
            (local[1, 0] - local[0, 0], local[1, 1] - local[0, 1]),
            (local[2, 0] - local[0, 0], local[2, 1] - local[0, 1]),
        ),
        dtype=float,
    )
    determinant = float(np.linalg.det(jacobian))
    if not math.isfinite(determinant) or abs(determinant) <= np.finfo(float).tiny:
        raise ValueError("qualified S3 local Jacobian must be nonzero")
    return jacobian, np.linalg.inv(jacobian), determinant


def _compatible_kinematics(
    local: np.ndarray,
    r: float,
    s: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    shape, derivative_r, derivative_s, bubble, bubble_r, bubble_s = _reference_fields(r, s)
    _jac, inverse, _determinant = _jacobian(local)
    derivative_x = inverse[0, 0] * derivative_r + inverse[0, 1] * derivative_s
    derivative_y = inverse[1, 0] * derivative_r + inverse[1, 1] * derivative_s
    bubble_x = inverse[0, 0] * bubble_r + inverse[0, 1] * bubble_s
    bubble_y = inverse[1, 0] * bubble_r + inverse[1, 1] * bubble_s

    membrane = np.zeros((3, 17), dtype=float)
    bending = np.zeros((3, 17), dtype=float)
    shear = np.zeros((2, 17), dtype=float)
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

    # Hierarchical internal coordinates are theta_bubble minus the mean corner
    # rotation, making the published f_i=L_i-b/3, f_4=b interpolation equal
    # to sum(L_i theta_i) + b alpha.
    bending[0, 16] = bubble_x
    bending[1, 15] = -bubble_y
    bending[2, 16] = bubble_y
    bending[2, 15] = -bubble_x
    shear[0, 16] = bubble
    shear[1, 15] = -bubble
    return membrane, bending, shear


def _covariant_shear(local: np.ndarray, point: tuple[float, float]) -> np.ndarray:
    jacobian, _inverse, _determinant = _jacobian(local)
    _membrane, _bending, cartesian = _compatible_kinematics(local, *point)
    return jacobian @ cartesian


def _assumed_shear_samples(local: np.ndarray) -> Dict[str, np.ndarray]:
    return {name: _covariant_shear(local, point) for name, point in TYING_POINTS.items()}


def _assumed_shear(
    local: np.ndarray,
    r: float,
    s: float,
    samples: Optional[Mapping[str, np.ndarray]] = None,
) -> np.ndarray:
    if samples is None:
        samples = _assumed_shear_samples(local)
    constant_r = (
        (2.0 / 3.0) * (samples["B"][0] - 0.5 * samples["B"][1])
        + (1.0 / 3.0) * (samples["C"][0] + samples["C"][1])
    )
    constant_s = (
        (2.0 / 3.0) * (samples["A"][1] - 0.5 * samples["A"][0])
        + (1.0 / 3.0) * (samples["C"][0] + samples["C"][1])
    )
    twisting = (
        samples["F"][0]
        - samples["D"][0]
        - samples["F"][1]
        + samples["E"][1]
    )
    covariant = np.vstack(
        (
            constant_r + (twisting / 3.0) * (3.0 * s - 1.0),
            constant_s + (twisting / 3.0) * (1.0 - 3.0 * r),
        )
    )
    _jac, inverse, _determinant = _jacobian(local)
    return inverse @ covariant


def _kinematic_matrix(
    local: np.ndarray,
    r: float,
    s: float,
    shear_samples: Optional[Mapping[str, np.ndarray]] = None,
) -> np.ndarray:
    membrane, bending, _compatible_shear = _compatible_kinematics(local, r, s)
    return np.vstack((membrane, bending, _assumed_shear(local, r, s, shear_samples)))


def _pl_operators(local: np.ndarray, k_d: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    _jac, inverse, determinant = _jacobian(local)
    derivative_r = np.asarray((-1.0, 1.0, 0.0), dtype=float)
    derivative_s = np.asarray((-1.0, 0.0, 1.0), dtype=float)
    derivative_x = inverse[0, 0] * derivative_r + inverse[0, 1] * derivative_s
    derivative_y = inverse[1, 0] * derivative_r + inverse[1, 1] * derivative_s
    constraint = np.zeros((3, 18), dtype=float)
    for row in range(3):
        constraint[row, 0::6] = 0.5 * derivative_y
        constraint[row, 1::6] = -0.5 * derivative_x
        constraint[row, 6 * row + 5] = 1.0
    area = 0.5 * abs(determinant)
    gram = (area / 12.0) * np.asarray(PL_GRAM_NUMERATOR, dtype=float)
    condensed = k_d * (constraint.T @ gram @ constraint)
    return constraint, gram, 0.5 * (condensed + condensed.T)


def _analytic_mass_moments(area: float) -> tuple[np.ndarray, np.ndarray, float]:
    """Return exact barycentric moments for ``(L1,L2,L3,b)``.

    The stiffness rule is degree five, while ``b**2`` is degree six.  Dynamic
    formulation identity therefore uses the closed-form triangle moments

    ``integral(L_i L_j)``, ``integral(L_i b)``, and ``integral(b**2)``

    with ``b = 27 L1 L2 L3``.  Keeping this helper independent of
    :data:`TRIANGLE_QUADRATURE` prevents accidental under-integration.
    """

    made = float(area)
    if not math.isfinite(made) or made <= 0.0:
        raise ValueError("qualified S3 mass integration requires a positive finite area")
    corner = (made / 12.0) * np.asarray(
        ((2.0, 1.0, 1.0), (1.0, 2.0, 1.0), (1.0, 1.0, 2.0)),
        dtype=float,
    )
    corner_bubble = np.full(3, 3.0 * made / 20.0, dtype=float)
    bubble = 81.0 * made / 280.0
    return corner, corner_bubble, bubble


def _reference_surface_strain_transform(offset: float) -> np.ndarray:
    """Map nodal-reference generalized strain to the section origin.

    ``offset`` is positive from the section origin to the nodal reference
    surface along the physical director.  With the frozen curvature sign,
    ``epsilon_section = epsilon_reference - offset * kappa``; curvature and
    transverse shear are unchanged.
    """

    made = float(offset)
    if not math.isfinite(made):
        raise ValueError("qualified S3 reference_surface_offset must be finite")
    transform = np.eye(8, dtype=float)
    if made != 0.0:
        transform[:3, 3:6] = -made * np.eye(3, dtype=float)
    return transform


def _shift_native_station_kinematics_to_section_origin(
    values: np.ndarray,
    gradients: np.ndarray,
    hessians: np.ndarray,
    offset: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Apply the same exact linear offset map to values, B and N data."""

    transform = _reference_surface_strain_transform(offset)
    if float(offset) == 0.0:
        # Preserve the established zero-offset binary64 arrays exactly.
        return values, gradients, hessians
    return (
        np.einsum("ab,gb->ga", transform, values),
        np.einsum("ab,gbj->gaj", transform, gradients),
        np.einsum("ab,gbjk->gajk", transform, hessians),
    )


class _SecondOrderJet:
    """Scalar value with exact first and second derivatives.

    The native nonlinear S3 strain map is a low-order polynomial in the 18
    external increments and two hierarchical bubble increments.  Carrying its
    gradient and Hessian explicitly keeps the implementation close to the
    published ``B U + 1/2 U.T N U`` equations and avoids numerical
    differentiation in the production tangent.
    """

    __slots__ = ("value", "gradient", "hessian")

    def __init__(
        self,
        value: float,
        gradient: np.ndarray,
        hessian: np.ndarray,
    ) -> None:
        self.value = float(value)
        self.gradient = np.asarray(gradient, dtype=float)
        self.hessian = np.asarray(hessian, dtype=float)

    @classmethod
    def constant(cls, value: float, size: int) -> "_SecondOrderJet":
        return cls(
            value,
            np.zeros(size, dtype=float),
            np.zeros((size, size), dtype=float),
        )

    @classmethod
    def variable(
        cls, value: float, index: int, size: int
    ) -> "_SecondOrderJet":
        gradient = np.zeros(size, dtype=float)
        gradient[int(index)] = 1.0
        return cls(value, gradient, np.zeros((size, size), dtype=float))

    def _coerce(self, other: Any) -> "_SecondOrderJet":
        if isinstance(other, _SecondOrderJet):
            return other
        return _SecondOrderJet.constant(float(other), self.gradient.size)

    def __add__(self, other: Any) -> "_SecondOrderJet":
        made = self._coerce(other)
        return _SecondOrderJet(
            self.value + made.value,
            self.gradient + made.gradient,
            self.hessian + made.hessian,
        )

    __radd__ = __add__

    def __neg__(self) -> "_SecondOrderJet":
        return _SecondOrderJet(-self.value, -self.gradient, -self.hessian)

    def __sub__(self, other: Any) -> "_SecondOrderJet":
        return self + (-self._coerce(other))

    def __rsub__(self, other: Any) -> "_SecondOrderJet":
        return self._coerce(other) + (-self)

    def __mul__(self, other: Any) -> "_SecondOrderJet":
        made = self._coerce(other)
        return _SecondOrderJet(
            self.value * made.value,
            self.gradient * made.value + made.gradient * self.value,
            self.hessian * made.value
            + made.hessian * self.value
            + np.outer(self.gradient, made.gradient)
            + np.outer(made.gradient, self.gradient),
        )

    __rmul__ = __mul__

    def __truediv__(self, other: Any) -> "_SecondOrderJet":
        if isinstance(other, _SecondOrderJet):
            raise TypeError("native S3 jet division by a variable is not defined")
        divisor = float(other)
        if divisor == 0.0:
            raise ZeroDivisionError("native S3 jet division by zero")
        return self * (1.0 / divisor)


def _jet_unary(
    value: _SecondOrderJet,
    function_value: float,
    first_derivative: float,
    second_derivative: float,
) -> _SecondOrderJet:
    """Compose a scalar jet with a twice differentiable scalar function."""

    return _SecondOrderJet(
        function_value,
        first_derivative * value.gradient,
        first_derivative * value.hessian
        + second_derivative * np.outer(value.gradient, value.gradient),
    )


def _jet_reciprocal(value: _SecondOrderJet) -> _SecondOrderJet:
    scalar = float(value.value)
    if not math.isfinite(scalar) or scalar == 0.0:
        raise ValueError("native S3 jet reciprocal requires a finite nonzero value")
    return _jet_unary(
        value,
        1.0 / scalar,
        -1.0 / (scalar * scalar),
        2.0 / (scalar * scalar * scalar),
    )


def _jet_sqrt(value: _SecondOrderJet) -> _SecondOrderJet:
    scalar = float(value.value)
    if not math.isfinite(scalar) or scalar <= 0.0:
        raise ValueError("native S3 jet square root requires a positive finite value")
    root = math.sqrt(scalar)
    return _jet_unary(
        value,
        root,
        0.5 / root,
        -0.25 / (scalar * root),
    )


def _jet_atan2(y_value: _SecondOrderJet, x_value: _SecondOrderJet) -> _SecondOrderJet:
    """Return ``atan2(y, x)`` with exact first and second derivatives."""

    x = float(x_value.value)
    y = float(y_value.value)
    radius2 = x * x + y * y
    if (
        not math.isfinite(radius2)
        or math.sqrt(radius2) < PL_MINIMUM_TWIST_DENOMINATOR
    ):
        raise ValueError(
            "qualified S3 relative twist is undefined at an antipodal swing"
        )
    inverse = 1.0 / radius2
    inverse2 = inverse * inverse
    derivative_x = -y * inverse
    derivative_y = x * inverse
    derivative_xx = 2.0 * x * y * inverse2
    derivative_xy = (y * y - x * x) * inverse2
    derivative_yy = -2.0 * x * y * inverse2
    gradient = (
        derivative_x * x_value.gradient
        + derivative_y * y_value.gradient
    )
    hessian = (
        derivative_x * x_value.hessian
        + derivative_y * y_value.hessian
        + derivative_xx * np.outer(x_value.gradient, x_value.gradient)
        + derivative_xy
        * (
            np.outer(x_value.gradient, y_value.gradient)
            + np.outer(y_value.gradient, x_value.gradient)
        )
        + derivative_yy * np.outer(y_value.gradient, y_value.gradient)
    )
    return _SecondOrderJet(math.atan2(y, x), gradient, hessian)


def _jet_rodrigues_coefficients(
    squared_angle: _SecondOrderJet,
) -> tuple[_SecondOrderJet, _SecondOrderJet]:
    """Return ``sin(a)/a`` and ``(1-cos(a))/a**2`` as jets."""

    scalar = float(squared_angle.value)
    if not math.isfinite(scalar) or scalar < -256.0 * np.finfo(float).eps:
        raise ValueError("native S3 rotation has an invalid squared angle")
    if scalar < 1.0e-4:
        s = squared_angle
        s2 = s * s
        s3 = s2 * s
        s4 = s3 * s
        sine_ratio = (
            1.0 - s / 6.0 + s2 / 120.0 - s3 / 5040.0 + s4 / 362880.0
        )
        cosine_ratio = (
            0.5 - s / 24.0 + s2 / 720.0 - s3 / 40320.0 + s4 / 3628800.0
        )
        return sine_ratio, cosine_ratio

    angle = math.sqrt(scalar)
    sine = math.sin(angle)
    cosine = math.cos(angle)
    sine_ratio_value = sine / angle
    sine_numerator = angle * cosine - sine
    sine_first = sine_numerator / (2.0 * angle**3)
    sine_second = 0.25 * (
        -sine / angle**3 - 3.0 * sine_numerator / angle**5
    )
    cosine_numerator = angle * sine - 2.0 + 2.0 * cosine
    cosine_ratio_value = (1.0 - cosine) / scalar
    cosine_first = cosine_numerator / (2.0 * angle**4)
    cosine_second = 0.25 * (
        (angle * cosine - sine) / angle**5
        - 4.0 * cosine_numerator / angle**6
    )
    return (
        _jet_unary(
            squared_angle,
            sine_ratio_value,
            sine_first,
            sine_second,
        ),
        _jet_unary(
            squared_angle,
            cosine_ratio_value,
            cosine_first,
            cosine_second,
        ),
    )


def _jet_linear_combination(
    coefficients: Sequence[float],
    values: Sequence[_SecondOrderJet],
) -> _SecondOrderJet:
    if len(coefficients) != len(values) or not values:
        raise ValueError("native S3 jet linear combination has incompatible inputs")
    result = _SecondOrderJet.constant(0.0, values[0].gradient.size)
    for coefficient, value in zip(coefficients, values):
        result = result + float(coefficient) * value
    return result


def _jet_dot(
    left: Sequence[_SecondOrderJet | float],
    right: Sequence[_SecondOrderJet | float],
    size: int,
) -> _SecondOrderJet:
    if len(left) != len(right):
        raise ValueError("native S3 jet dot product has incompatible inputs")
    result = _SecondOrderJet.constant(0.0, size)
    for first, second in zip(left, right):
        first_jet = (
            first
            if isinstance(first, _SecondOrderJet)
            else _SecondOrderJet.constant(float(first), size)
        )
        result = result + first_jet * second
    return result


def _jet_rodrigues_matrix(
    rotation: Sequence[_SecondOrderJet],
) -> list[list[_SecondOrderJet]]:
    if len(rotation) != 3:
        raise ValueError("native S3 rotation jet requires three components")
    size = rotation[0].gradient.size
    zero = _SecondOrderJet.constant(0.0, size)
    one = _SecondOrderJet.constant(1.0, size)
    x, y, z = rotation
    skew = [
        [zero, -z, y],
        [z, zero, -x],
        [-y, x, zero],
    ]
    skew2 = [
        [
            sum((skew[row][inner] * skew[inner][column] for inner in range(3)), zero)
            for column in range(3)
        ]
        for row in range(3)
    ]
    squared_angle = x * x + y * y + z * z
    sine_ratio, cosine_ratio = _jet_rodrigues_coefficients(squared_angle)
    return [
        [
            (one if row == column else zero)
            + sine_ratio * skew[row][column]
            + cosine_ratio * skew2[row][column]
            for column in range(3)
        ]
        for row in range(3)
    ]


def _jet_matrix_times_constant(
    matrix: Sequence[Sequence[_SecondOrderJet]],
    constant: np.ndarray,
) -> list[list[_SecondOrderJet]]:
    made = np.asarray(constant, dtype=float)
    rows = len(matrix)
    inner_count = len(matrix[0]) if rows else 0
    if made.ndim != 2 or made.shape[0] != inner_count:
        raise ValueError("native S3 jet matrix product has incompatible inputs")
    size = matrix[0][0].gradient.size
    zero = _SecondOrderJet.constant(0.0, size)
    return [
        [
            sum(
                (
                    matrix[row][inner] * made[inner, column]
                    for inner in range(inner_count)
                ),
                zero,
            )
            for column in range(made.shape[1])
        ]
        for row in range(rows)
    ]


def _objective_surface_frame_jets(
    reference_nodes: np.ndarray,
    reference_frame: np.ndarray,
    trial_nodes: Sequence[Sequence[_SecondOrderJet]],
) -> list[list[_SecondOrderJet]]:
    """Return the 3x3 proper surface frame from a rectangular right polar map."""

    reference = np.asarray(reference_nodes, dtype=float).reshape(3, 3)
    frame = np.asarray(reference_frame, dtype=float).reshape(3, 3)
    if not np.all(np.isfinite(reference)) or not np.all(np.isfinite(frame)):
        raise ValueError("qualified S3 objective surface inputs must be finite")
    if not np.allclose(frame.T @ frame, np.eye(3), rtol=0.0, atol=1.0e-12):
        raise ValueError("qualified S3 reference frame must be orthonormal")
    if float(np.linalg.det(frame)) <= 0.0:
        raise ValueError("qualified S3 reference frame must be proper")
    local = (reference - reference[0]) @ frame[:, :2]
    _jacobian_matrix, inverse, _determinant = _jacobian(local)
    derivative_r = np.asarray((-1.0, 1.0, 0.0), dtype=float)
    derivative_s = np.asarray((-1.0, 0.0, 1.0), dtype=float)
    derivative_x = inverse[0, 0] * derivative_r + inverse[0, 1] * derivative_s
    derivative_y = inverse[1, 0] * derivative_r + inverse[1, 1] * derivative_s
    size = trial_nodes[0][0].gradient.size
    first = [
        _jet_linear_combination(
            derivative_x,
            [trial_nodes[node][axis] for node in range(3)],
        )
        for axis in range(3)
    ]
    second = [
        _jet_linear_combination(
            derivative_y,
            [trial_nodes[node][axis] for node in range(3)],
        )
        for axis in range(3)
    ]
    c00 = _jet_dot(first, first, size)
    c01 = _jet_dot(first, second, size)
    c11 = _jet_dot(second, second, size)
    determinant = c00 * c11 - c01 * c01
    scale = max(abs(c00.value * c11.value), 1.0)
    if determinant.value <= 256.0 * np.finfo(float).eps * scale:
        raise ValueError("qualified S3 current surface map is singular or inverted")
    determinant_root = _jet_sqrt(determinant)
    trace_root = _jet_sqrt(c00 + c11 + 2.0 * determinant_root)
    a00 = c00 + determinant_root
    a11 = c11 + determinant_root
    determinant_a = a00 * a11 - c01 * c01
    inverse_determinant_a = _jet_reciprocal(determinant_a)
    inverse_root = [
        [trace_root * a11 * inverse_determinant_a, -trace_root * c01 * inverse_determinant_a],
        [-trace_root * c01 * inverse_determinant_a, trace_root * a00 * inverse_determinant_a],
    ]
    zero = _SecondOrderJet.constant(0.0, size)
    tangent_first = [
        first[axis] * inverse_root[0][0]
        + second[axis] * inverse_root[1][0]
        for axis in range(3)
    ]
    tangent_second = [
        first[axis] * inverse_root[0][1]
        + second[axis] * inverse_root[1][1]
        for axis in range(3)
    ]
    normal = [
        tangent_first[1] * tangent_second[2]
        - tangent_first[2] * tangent_second[1],
        tangent_first[2] * tangent_second[0]
        - tangent_first[0] * tangent_second[2],
        tangent_first[0] * tangent_second[1]
        - tangent_first[1] * tangent_second[0],
    ]
    columns = (tangent_first, tangent_second, normal)
    result = [
        [columns[column][row] for column in range(3)]
        for row in range(3)
    ]
    numeric = np.asarray(
        [[result[row][column].value for column in range(3)] for row in range(3)],
        dtype=float,
    )
    if not np.allclose(numeric.T @ numeric, np.eye(3), rtol=0.0, atol=2.0e-11):
        raise ValueError("qualified S3 objective surface polar frame lost orthogonality")
    if float(np.linalg.det(numeric)) <= 0.0:
        raise ValueError("qualified S3 objective surface polar frame is improper")
    del zero
    return result


def _objective_pl_energy_response(
    reference_nodes: np.ndarray,
    reference_frame: np.ndarray,
    current_nodes: np.ndarray,
    committed_rotation_matrices: np.ndarray,
    external_increment: np.ndarray,
    committed_twist: np.ndarray,
    k_d: float,
    *,
    native_rotation_trial: NativeElementRotationView,
) -> Dict[str, Any]:
    """Return objective finite-rotation PL energy, force, and exact Hessian.

    The midsurface rotation is the proper rectangular right-polar factor of
    the 3x2 surface deformation gradient.  Each nodal rotation is updated by
    left-multiplying its committed proper operator with the spatial increment.
    The relative swing/twist angle is unwrapped to the unique phase nearest
    the committed value.  At the identity configuration this linearizes
    exactly to ``theta_D - (v_,x-u_,y)/2``.
    """

    if not isinstance(native_rotation_trial, NativeElementRotationView):
        raise TypeError(
            "objective S3 PL kinematics requires NativeElementRotationView"
        )
    if native_rotation_trial.trial_serial is None:
        raise ValueError("objective S3 PL kinematics requires an active trial view")
    reference = np.asarray(reference_nodes, dtype=float).reshape(3, 3)
    frame = np.asarray(reference_frame, dtype=float).reshape(3, 3)
    current = np.asarray(current_nodes, dtype=float).reshape(3, 3)
    rotations = np.asarray(committed_rotation_matrices, dtype=float)
    increment = np.asarray(external_increment, dtype=float).reshape(-1)
    committed = np.asarray(committed_twist, dtype=float).reshape(-1)
    drilling_scale = float(k_d)
    if rotations.shape != (3, 3, 3):
        raise ValueError("qualified S3 committed nodal rotations must have shape (3,3,3)")
    if increment.size != 18 or committed.size != 3:
        raise ValueError("qualified S3 objective PL inputs have incompatible shapes")
    if (
        not np.all(np.isfinite(reference))
        or not np.all(np.isfinite(current))
        or not np.all(np.isfinite(rotations))
        or not np.all(np.isfinite(increment))
        or not np.all(np.isfinite(committed))
        or not math.isfinite(drilling_scale)
        or drilling_scale <= 0.0
    ):
        raise ValueError("qualified S3 objective PL inputs must be finite and positive")
    if not np.array_equal(current, native_rotation_trial.committed_coordinates):
        raise ValueError(
            "qualified S3 objective PL committed coordinates disagree with the "
            "solver-owned trial"
        )
    if not np.array_equal(rotations, native_rotation_trial.committed_rotation_matrices):
        raise ValueError(
            "qualified S3 objective PL committed rotations disagree with the "
            "solver-owned trial"
        )
    external = increment.reshape(3, 6)
    if not np.array_equal(
        external[:, :3], native_rotation_trial.coordinate_increment
    ):
        raise ValueError(
            "qualified S3 objective PL translation increment disagrees with the "
            "solver-owned trial"
        )
    if not np.array_equal(
        external[:, 3:6], native_rotation_trial.rotation_coordinate_increment
    ):
        raise ValueError(
            "qualified S3 objective PL rotation increment disagrees with the "
            "solver-owned trial"
        )
    for matrix in rotations:
        if not np.allclose(matrix.T @ matrix, np.eye(3), rtol=0.0, atol=1.0e-12):
            raise ValueError("qualified S3 committed nodal rotation is not orthogonal")
        if abs(float(np.linalg.det(matrix)) - 1.0) > 1.0e-12:
            raise ValueError("qualified S3 committed nodal rotation is not proper")

    size = 18
    variables = [
        _SecondOrderJet.variable(float(value), index, size)
        for index, value in enumerate(increment)
    ]
    trial_nodes = [
        [
            _anchor_jet_value(
                _SecondOrderJet.constant(float(current[node, axis]), size)
                + variables[6 * node + axis],
                float(native_rotation_trial.trial_coordinates[node, axis]),
                label=f"objective PL trial coordinate[{node},{axis}]",
            )
            for axis in range(3)
        ]
        for node in range(3)
    ]
    surface_frame = _objective_surface_frame_jets(
        reference,
        frame,
        trial_nodes,
    )
    trial_rotations: list[list[list[_SecondOrderJet]]] = []
    constraints: list[_SecondOrderJet] = []
    turn_counts: list[int] = []
    for node in range(3):
        update = _jet_rodrigues_matrix(variables[6 * node + 3 : 6 * node + 6])
        trial_rotation = _jet_matrix_times_constant(update, rotations[node])
        for row in range(3):
            for column in range(3):
                trial_rotation[row][column] = _anchor_jet_value(
                    trial_rotation[row][column],
                    float(
                        native_rotation_trial.trial_rotation_matrices[
                            node, row, column
                        ]
                    ),
                    label=f"objective PL trial Q[{node},{row},{column}]",
                )
        trial_rotations.append(trial_rotation)
        # S_ref.T R_surface.T Q_node S_ref == S_surface.T Q_node S_ref.
        q_reference = _jet_matrix_times_constant(trial_rotation, frame)
        relative = [
            [
                sum(
                    (
                        surface_frame[axis][row] * q_reference[axis][column]
                        for axis in range(3)
                    ),
                    _SecondOrderJet.constant(0.0, size),
                )
                for column in range(3)
            ]
            for row in range(3)
        ]
        x_value = relative[0][0] + relative[1][1]
        y_value = relative[1][0] - relative[0][1]
        principal = _jet_atan2(y_value, x_value)
        turns = int(
            math.floor((committed[node] - principal.value) / (2.0 * math.pi) + 0.5)
        )
        unwrapped = principal + 2.0 * math.pi * turns
        if abs(unwrapped.value - committed[node]) >= math.pi - PL_PHASE_MARGIN:
            raise ValueError(
                "qualified S3 relative twist crossed the unique phase boundary"
            )
        constraints.append(unwrapped)
        turn_counts.append(
            int(math.ceil((float(unwrapped.value) - math.pi) / (2.0 * math.pi)))
        )

    local = (reference - reference[0]) @ frame[:, :2]
    _jacobian_matrix, _inverse, determinant = _jacobian(local)
    area = 0.5 * abs(float(determinant))
    gram = (area / 12.0) * np.asarray(PL_GRAM_NUMERATOR, dtype=float)
    multipliers = [drilling_scale * constraint for constraint in constraints]
    mixed_constraint_forces = [
        sum(
            (
                gram[row, column] * multipliers[column]
                for column in range(3)
            ),
            _SecondOrderJet.constant(0.0, size),
        )
        for row in range(3)
    ]
    energy = sum(
        (
            0.5 * constraints[row] * mixed_constraint_forces[row]
            for row in range(3)
        ),
        _SecondOrderJet.constant(0.0, size),
    )
    surface_numeric = np.asarray(
        [
            [surface_frame[row][column].value for column in range(3)]
            for row in range(3)
        ],
        dtype=float,
    )
    rotation_numeric = np.asarray(
        [
            [
                [trial_rotations[node][row][column].value for column in range(3)]
                for row in range(3)
            ]
            for node in range(3)
        ],
        dtype=float,
    )
    constraint_numeric = np.asarray(
        [item.value for item in constraints], dtype=np.float64
    )
    multiplier_numeric = drilling_scale * constraint_numeric
    mixed_force_numeric = np.asarray(
        [
            sum(
                float(gram[row, column]) * float(multiplier_numeric[column])
                for column in range(3)
            )
            for row in range(3)
        ],
        dtype=np.float64,
    )
    energy_numeric = sum(
        0.5
        * float(constraint_numeric[row])
        * float(mixed_force_numeric[row])
        for row in range(3)
    )
    jet_mixed_numeric = np.asarray(
        [item.value for item in mixed_constraint_forces], dtype=np.float64
    )
    numeric_scale = max(
        1.0,
        abs(float(energy_numeric)),
        float(np.max(np.abs(mixed_force_numeric))),
    )
    if (
        not np.allclose(
            jet_mixed_numeric,
            mixed_force_numeric,
            rtol=0.0,
            atol=32.0 * np.finfo(np.float64).eps * numeric_scale,
        )
        or abs(float(energy.value) - float(energy_numeric))
        > 32.0 * np.finfo(np.float64).eps * numeric_scale
    ):
        raise ValueError(
            "qualified S3 objective PL canonical value disagrees with its exact jet"
        )
    hessian = np.asarray(energy.hessian, dtype=float)
    hessian_scale = max(1.0, float(np.max(np.abs(hessian))))
    if not np.all(np.isfinite(hessian)) or not np.allclose(
        hessian,
        hessian.T,
        rtol=0.0,
        atol=512.0 * np.finfo(np.float64).eps * hessian_scale,
    ):
        raise ValueError("qualified S3 objective PL Hessian is non-finite or asymmetric")
    tangent = 0.5 * (hessian + hessian.T)
    result = {
        "constraint": constraint_numeric,
        "constraint_jacobian": np.asarray(
            [item.gradient for item in constraints], dtype=float
        ),
        "constraint_hessian": np.asarray(
            [item.hessian for item in constraints], dtype=float
        ),
        "multiplier": multiplier_numeric,
        "mixed_constraint_force": mixed_force_numeric,
        "constraint_conjugate": mixed_force_numeric.copy(),
        "energy": float(energy_numeric),
        "force": np.asarray(energy.gradient, dtype=float),
        "tangent": np.asarray(tangent, dtype=float),
        "surface_frame": surface_numeric,
        "trial_rotation_matrices": rotation_numeric,
        "turn_count": np.asarray(turn_counts, dtype=np.int64),
        "gram": gram,
        "surface_rotation_policy_id": SURFACE_ROTATION_POLICY_ID,
        "twist_policy_id": PL_TWIST_POLICY_ID,
        "rotation_update_policy_id": NODAL_ROTATION_UPDATE_POLICY_ID,
        "phase_policy_id": PL_PHASE_POLICY_ID,
        "energy_policy_id": NONLINEAR_PL_ENERGY_POLICY_ID,
    }
    for name, value in result.items():
        if isinstance(value, np.ndarray) and value.dtype.kind in {"f", "c"}:
            if not np.all(np.isfinite(value)):
                raise ValueError(
                    f"qualified S3 objective PL output {name!r} is non-finite"
                )
        elif isinstance(value, (float, np.floating)) and not math.isfinite(
            float(value)
        ):
            raise ValueError(
                f"qualified S3 objective PL output {name!r} is non-finite"
            )
    return result


def _anchor_jet_value(
    value: _SecondOrderJet,
    authoritative_value: float,
    *,
    label: str,
) -> _SecondOrderJet:
    """Anchor a differentiated construction to a solver-owned binary64 value."""

    authoritative = float(authoritative_value)
    if not math.isfinite(authoritative):
        raise ValueError(f"{label} must be finite")
    tolerance = 128.0 * np.finfo(np.float64).eps * max(
        1.0,
        abs(authoritative),
        abs(float(value.value)),
    )
    if abs(float(value.value) - authoritative) > tolerance:
        raise ValueError(
            f"{label} disagrees with the solver-owned native rotation trial"
        )
    return _SecondOrderJet(
        authoritative,
        np.asarray(value.gradient, dtype=float),
        np.asarray(value.hessian, dtype=float),
    )


def _validate_native_physical_trial(
    native_rotation_trial: NativeElementRotationView,
    current_nodes: np.ndarray,
    director_triads: np.ndarray,
    increment20: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Validate one element's redundant inputs against the node-shared trial."""

    if not isinstance(native_rotation_trial, NativeElementRotationView):
        raise TypeError(
            "native S3 physical kinematics requires NativeElementRotationView"
        )
    if native_rotation_trial.trial_serial is None:
        raise ValueError("native S3 physical kinematics requires an active trial view")
    if len(native_rotation_trial.node_ids) != 3:
        raise ValueError("native S3 physical kinematics requires three native nodes")
    nodes = np.asarray(current_nodes, dtype=np.float64)
    triads = np.asarray(director_triads, dtype=np.float64)
    increment = np.asarray(increment20, dtype=np.float64).reshape(-1)
    if nodes.shape != (3, 3) or triads.shape != (4, 3, 3):
        raise ValueError("native S3 physical kinematics requires 3 nodes and 4 triads")
    if increment.size != 20:
        raise ValueError("native S3 increment must contain 20 coordinates")
    if (
        not np.all(np.isfinite(nodes))
        or not np.all(np.isfinite(triads))
        or not np.all(np.isfinite(increment))
    ):
        raise ValueError("native S3 physical trial inputs must be finite")
    view_shapes = {
        "committed_coordinates": (3, 3),
        "trial_coordinates": (3, 3),
        "coordinate_increment": (3, 3),
        "committed_rotation_coordinates": (3, 3),
        "trial_rotation_coordinates": (3, 3),
        "rotation_coordinate_increment": (3, 3),
        "committed_rotation_matrices": (3, 3, 3),
        "trial_rotation_matrices": (3, 3, 3),
        "reference_directors": (3, 3),
        "committed_directors": (3, 3),
        "trial_directors": (3, 3),
    }
    for name, shape in view_shapes.items():
        made = np.asarray(getattr(native_rotation_trial, name), dtype=np.float64)
        if made.shape != shape or not np.all(np.isfinite(made)):
            raise ValueError(f"native rotation trial {name} is incompatible")

    external = increment[:18].reshape(3, 6)
    if not np.array_equal(nodes, native_rotation_trial.committed_coordinates):
        raise ValueError(
            "native S3 committed coordinates disagree with the solver-owned trial"
        )
    if not np.array_equal(
        external[:, :3], native_rotation_trial.coordinate_increment
    ):
        raise ValueError(
            "native S3 translational increment disagrees with the solver-owned trial"
        )
    if not np.array_equal(
        external[:, 3:6], native_rotation_trial.rotation_coordinate_increment
    ):
        raise ValueError(
            "native S3 rotational increment disagrees with the solver-owned trial"
        )
    if not np.allclose(
        triads[:3, :, 2],
        native_rotation_trial.committed_directors,
        rtol=0.0,
        atol=2.0e-13,
    ):
        raise ValueError(
            "native S3 committed corner directors disagree with node-shared history"
        )
    if not np.allclose(
        np.einsum(
            "nij,nj->ni",
            native_rotation_trial.committed_rotation_matrices,
            native_rotation_trial.reference_directors,
        ),
        native_rotation_trial.committed_directors,
        rtol=0.0,
        atol=2.0e-13,
    ):
        raise ValueError("native S3 committed Q/reference-director relation is invalid")

    committed_raw_normal = np.cross(nodes[1] - nodes[0], nodes[2] - nodes[0])
    committed_raw_norm = float(np.linalg.norm(committed_raw_normal))
    committed_director = np.sum(native_rotation_trial.committed_directors, axis=0)
    committed_director_norm = float(np.linalg.norm(committed_director))
    trial_nodes = np.asarray(native_rotation_trial.trial_coordinates, dtype=np.float64)
    raw_normal = np.cross(trial_nodes[1] - trial_nodes[0], trial_nodes[2] - trial_nodes[0])
    raw_norm = float(np.linalg.norm(raw_normal))
    transported = np.sum(native_rotation_trial.trial_directors, axis=0)
    transported_norm = float(np.linalg.norm(transported))
    if (
        not math.isfinite(committed_raw_norm)
        or not math.isfinite(committed_director_norm)
        or not math.isfinite(raw_norm)
        or not math.isfinite(transported_norm)
        or committed_raw_norm <= 0.0
        or committed_director_norm <= 0.0
        or raw_norm <= 0.0
        or transported_norm <= 0.0
    ):
        raise ValueError("native S3 current surface or transported director is singular")
    committed_alignment = float(
        np.dot(
            committed_raw_normal / committed_raw_norm,
            committed_director / committed_director_norm,
        )
    )
    signed_alignment = float(
        np.dot(raw_normal / raw_norm, transported / transported_norm)
    )
    if (
        abs(committed_alignment) <= MINIMUM_OWNER_NORMAL_ALIGNMENT
        or abs(signed_alignment) <= MINIMUM_OWNER_NORMAL_ALIGNMENT
        or committed_alignment * signed_alignment <= 0.0
    ):
        raise ValueError(
            "native S3 current surface is inverted relative to transported directors"
        )
    return nodes, triads, increment


def _native_source_increment_jets(
    native_rotation_trial: NativeElementRotationView,
    director_triads: np.ndarray,
    increment: np.ndarray,
) -> tuple[
    list[list[_SecondOrderJet]],
    list[list[_SecondOrderJet]],
]:
    """Return translation and exact director-increment jets for four sources.

    Corner values come exclusively from the solver-owned shared-Q view.  Their
    first and second derivatives are those of the same left exponential map
    used by that store.  Only the hierarchical bubble rotation remains
    element-owned; it is updated by the mean spatial nodal increment plus its
    two tangent coordinates and differentiated through the same exponential.
    """

    made = np.asarray(increment, dtype=float).reshape(-1)
    if made.size != 20 or not np.all(np.isfinite(made)):
        raise ValueError("native S3 increment must contain 20 finite coordinates")
    triads = np.asarray(director_triads, dtype=float).reshape(4, 3, 3)
    variables = [
        _SecondOrderJet.variable(value, index, 20)
        for index, value in enumerate(made)
    ]
    translations: list[list[_SecondOrderJet]] = []
    director_increments: list[list[_SecondOrderJet]] = []
    size = 20
    for node in range(3):
        base = 6 * node
        translations.append(
            [
                _anchor_jet_value(
                    _SecondOrderJet.constant(
                        float(native_rotation_trial.committed_coordinates[node, axis]),
                        size,
                    )
                    + variables[base + axis],
                    float(native_rotation_trial.trial_coordinates[node, axis]),
                    label=f"native trial coordinate[{node},{axis}]",
                )
                - float(native_rotation_trial.committed_coordinates[node, axis])
                for axis in range(3)
            ]
        )
        update = _jet_rodrigues_matrix(variables[base + 3 : base + 6])
        trial_q = _jet_matrix_times_constant(
            update,
            native_rotation_trial.committed_rotation_matrices[node],
        )
        for row in range(3):
            for column in range(3):
                trial_q[row][column] = _anchor_jet_value(
                    trial_q[row][column],
                    float(native_rotation_trial.trial_rotation_matrices[node, row, column]),
                    label=f"native trial Q[{node},{row},{column}]",
                )
        trial_director = [
            _anchor_jet_value(
                sum(
                    (
                        trial_q[row][column]
                        * float(native_rotation_trial.reference_directors[node, column])
                        for column in range(3)
                    ),
                    _SecondOrderJet.constant(0.0, size),
                ),
                float(native_rotation_trial.trial_directors[node, row]),
                label=f"native trial director[{node},{row}]",
            )
            for row in range(3)
        ]
        director_increments.append(
            [
                trial_director[axis]
                - float(native_rotation_trial.committed_directors[node, axis])
                for axis in range(3)
            ]
        )

    bubble_rotation = [
        sum(
            (variables[6 * node + 3 + axis] for node in range(3)),
            _SecondOrderJet.constant(0.0, size),
        )
        / 3.0
        + variables[18] * float(triads[3, axis, 0])
        + variables[19] * float(triads[3, axis, 1])
        for axis in range(3)
    ]
    bubble_update = _jet_rodrigues_matrix(bubble_rotation)
    bubble_trial = _jet_matrix_times_constant(
        bubble_update,
        triads[3, :, 2].reshape(3, 1),
    )
    bubble_rotation_value = np.asarray(
        [item.value for item in bubble_rotation], dtype=np.float64
    )
    authoritative_bubble = (
        rotation_exponential(bubble_rotation_value) @ triads[3, :, 2]
    )
    director_increments.append(
        [
            _anchor_jet_value(
                bubble_trial[axis][0],
                float(authoritative_bubble[axis]),
                label=f"native bubble trial director[{axis}]",
            )
            - float(triads[3, axis, 2])
            for axis in range(3)
        ]
    )
    return translations, director_increments


def _native_point_incremental_covariants(
    current_nodes: np.ndarray,
    director_triads: np.ndarray,
    r: float,
    s: float,
    translations: Sequence[Sequence[_SecondOrderJet]],
    director_increments: Sequence[Sequence[_SecondOrderJet]],
) -> tuple[
    tuple[_SecondOrderJet, _SecondOrderJet, _SecondOrderJet],
    tuple[_SecondOrderJet, _SecondOrderJet, _SecondOrderJet],
    tuple[_SecondOrderJet, _SecondOrderJet],
]:
    """Return midsurface, curvature and compatible-shear covariants."""

    nodes = np.asarray(current_nodes, dtype=float).reshape(3, 3)
    triads = np.asarray(director_triads, dtype=float).reshape(4, 3, 3)
    (
        shape,
        derivative_r,
        derivative_s,
        bubble,
        bubble_r,
        bubble_s,
    ) = _reference_fields(float(r), float(s))
    functions = np.concatenate((shape - bubble / 3.0, (bubble,)))
    functions_r = np.concatenate(
        (derivative_r - bubble_r / 3.0, (bubble_r,))
    )
    functions_s = np.concatenate(
        (derivative_s - bubble_s / 3.0, (bubble_s,))
    )

    size = 20
    translation_r = [
        _jet_linear_combination(derivative_r, [translations[node][axis] for node in range(3)])
        for axis in range(3)
    ]
    translation_s = [
        _jet_linear_combination(derivative_s, [translations[node][axis] for node in range(3)])
        for axis in range(3)
    ]

    director = np.einsum("i,iaj->aj", functions, triads)[:, 2]
    director_r = np.einsum("i,iaj->aj", functions_r, triads)[:, 2]
    director_s = np.einsum("i,iaj->aj", functions_s, triads)[:, 2]
    increment_director = [
        _jet_linear_combination(
            functions,
            [director_increments[node][axis] for node in range(4)],
        )
        for axis in range(3)
    ]
    increment_director_r = [
        _jet_linear_combination(
            functions_r,
            [director_increments[node][axis] for node in range(4)],
        )
        for axis in range(3)
    ]
    increment_director_s = [
        _jet_linear_combination(
            functions_s,
            [director_increments[node][axis] for node in range(4)],
        )
        for axis in range(3)
    ]

    tangent_r = nodes[1] - nodes[0]
    tangent_s = nodes[2] - nodes[0]
    membrane_rr = _jet_dot(tangent_r, translation_r, size) + 0.5 * _jet_dot(
        translation_r, translation_r, size
    )
    membrane_ss = _jet_dot(tangent_s, translation_s, size) + 0.5 * _jet_dot(
        translation_s, translation_s, size
    )
    membrane_rs = (
        _jet_dot(tangent_r, translation_s, size)
        + _jet_dot(tangent_s, translation_r, size)
        + _jet_dot(translation_r, translation_s, size)
    )

    curvature_rr = (
        _jet_dot(tangent_r, increment_director_r, size)
        + _jet_dot(director_r, translation_r, size)
        + _jet_dot(translation_r, increment_director_r, size)
    )
    curvature_ss = (
        _jet_dot(tangent_s, increment_director_s, size)
        + _jet_dot(director_s, translation_s, size)
        + _jet_dot(translation_s, increment_director_s, size)
    )
    curvature_rs = (
        _jet_dot(tangent_r, increment_director_s, size)
        + _jet_dot(director_r, translation_s, size)
        + _jet_dot(tangent_s, increment_director_r, size)
        + _jet_dot(director_s, translation_r, size)
        + _jet_dot(translation_r, increment_director_s, size)
        + _jet_dot(increment_director_r, translation_s, size)
    )

    shear_r = (
        _jet_dot(tangent_r, increment_director, size)
        + _jet_dot(director, translation_r, size)
        + _jet_dot(translation_r, increment_director, size)
    )
    shear_s = (
        _jet_dot(tangent_s, increment_director, size)
        + _jet_dot(director, translation_s, size)
        + _jet_dot(translation_s, increment_director, size)
    )
    return (
        (membrane_rr, membrane_ss, membrane_rs),
        (curvature_rr, curvature_ss, curvature_rs),
        (shear_r, shear_s),
    )


def _covariant_inplane_to_cartesian(
    covariant: Sequence[_SecondOrderJet],
    inverse_jacobian: np.ndarray,
) -> tuple[_SecondOrderJet, _SecondOrderJet, _SecondOrderJet]:
    inverse = np.asarray(inverse_jacobian, dtype=float).reshape(2, 2)
    rr, ss, rs = covariant
    xx = (
        inverse[0, 0] ** 2 * rr
        + inverse[0, 1] ** 2 * ss
        + inverse[0, 0] * inverse[0, 1] * rs
    )
    yy = (
        inverse[1, 0] ** 2 * rr
        + inverse[1, 1] ** 2 * ss
        + inverse[1, 0] * inverse[1, 1] * rs
    )
    xy = (
        2.0 * inverse[0, 0] * inverse[1, 0] * rr
        + 2.0 * inverse[0, 1] * inverse[1, 1] * ss
        + (
            inverse[0, 0] * inverse[1, 1]
            + inverse[0, 1] * inverse[1, 0]
        )
        * rs
    )
    return xx, yy, xy


def _native_incremental_strain_jets(
    current_nodes: np.ndarray,
    director_triads: np.ndarray,
    r: float,
    s: float,
    increment20: np.ndarray,
    *,
    reference_nodes: np.ndarray,
    reference_frame: np.ndarray,
    native_rotation_trial: NativeElementRotationView,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Evaluate the published incremental TL strain and its exact B/N data.

    Output ordering is membrane engineering strain, curvature engineering
    strain and assumed engineering transverse shear.  Derivatives are with
    respect to the 18 global external increments followed by the two
    hierarchical bubble increments.
    """

    nodes, triads, increment = _validate_native_physical_trial(
        native_rotation_trial,
        current_nodes,
        director_triads,
        increment20,
    )
    basis_nodes = np.asarray(reference_nodes, dtype=float).reshape(3, 3)
    if not np.all(np.isfinite(basis_nodes)):
        raise ValueError("native S3 reference nodes must be finite")
    frame = np.asarray(reference_frame, dtype=float).reshape(3, 3)
    if not np.all(np.isfinite(frame)):
        raise ValueError("native S3 reference frame must be finite")
    local = (basis_nodes - basis_nodes[0]) @ frame[:, :2]
    _jacobian_matrix, inverse, _determinant = _jacobian(local)
    translations, director_increments = _native_source_increment_jets(
        native_rotation_trial,
        triads,
        increment,
    )
    membrane_covariant, curvature_covariant, _compatible = (
        _native_point_incremental_covariants(
            nodes,
            triads,
            float(r),
            float(s),
            translations,
            director_increments,
        )
    )
    membrane = _covariant_inplane_to_cartesian(membrane_covariant, inverse)
    curvature = _covariant_inplane_to_cartesian(curvature_covariant, inverse)

    samples: Dict[str, tuple[_SecondOrderJet, _SecondOrderJet]] = {}
    for name, point in TYING_POINTS.items():
        _membrane, _curvature, compatible = _native_point_incremental_covariants(
            nodes,
            triads,
            float(point[0]),
            float(point[1]),
            translations,
            director_increments,
        )
        samples[name] = compatible
    constant_r = (
        (2.0 / 3.0) * (samples["B"][0] - 0.5 * samples["B"][1])
        + (1.0 / 3.0) * (samples["C"][0] + samples["C"][1])
    )
    constant_s = (
        (2.0 / 3.0) * (samples["A"][1] - 0.5 * samples["A"][0])
        + (1.0 / 3.0) * (samples["C"][0] + samples["C"][1])
    )
    twisting = (
        samples["F"][0]
        - samples["D"][0]
        - samples["F"][1]
        + samples["E"][1]
    )
    shear_covariant = (
        constant_r + (twisting / 3.0) * (3.0 * float(s) - 1.0),
        constant_s + (twisting / 3.0) * (1.0 - 3.0 * float(r)),
    )
    shear = (
        inverse[0, 0] * shear_covariant[0]
        + inverse[0, 1] * shear_covariant[1],
        inverse[1, 0] * shear_covariant[0]
        + inverse[1, 1] * shear_covariant[1],
    )
    jets = (*membrane, *curvature, *shear)
    values = np.asarray([item.value for item in jets], dtype=float)
    gradients = np.asarray([item.gradient for item in jets], dtype=float)
    hessians = np.asarray([item.hessian for item in jets], dtype=float)
    if (
        not np.all(np.isfinite(values))
        or not np.all(np.isfinite(gradients))
        or not np.all(np.isfinite(hessians))
    ):
        raise ValueError("native S3 incremental strain evaluation is non-finite")
    return values, gradients, hessians


def _rodrigues_rotation(rotation_vector: np.ndarray) -> np.ndarray:
    """Private compatibility alias for the solver-owned exponential map."""

    return rotation_exponential(rotation_vector)


def _update_native_director_triads(
    director_triads: np.ndarray,
    increment20: np.ndarray,
    *,
    native_rotation_trial: NativeElementRotationView,
) -> np.ndarray:
    """Commit shared-Q corners and the sole element-owned bubble director."""

    _nodes, triads, increment = _validate_native_physical_trial(
        native_rotation_trial,
        native_rotation_trial.committed_coordinates,
        director_triads,
        increment20,
    )
    updated = np.empty_like(triads)
    for node in range(3):
        updated[node] = reconstruct_director_triad(
            native_rotation_trial.trial_directors[node]
        )
    external = increment[:18].reshape(3, 6)
    bubble_rotation = (
        np.mean(external[:, 3:6], axis=0)
        + increment[18] * triads[3, :, 0]
        + increment[19] * triads[3, :, 1]
    )
    updated[3] = reconstruct_director_triad(
        rotation_exponential(bubble_rotation) @ triads[3, :, 2]
    )
    return updated


class S3BubbleEquilibriumError(RuntimeError):
    """A native S3 trial whose two internal rotations did not equilibrate."""


def _solve_native_bubble_equilibrium(
    external_increment: np.ndarray,
    initial_bubble_increment: np.ndarray,
    response_builder: Callable[
        [np.ndarray],
        Any,
    ],
) -> tuple[
    np.ndarray,
    np.ndarray,
    Dict[str, Any],
    Dict[str, Any],
]:
    """Solve and consistently condense the two source bubble equations.

    ``response_builder`` must always evaluate from the same committed material
    state.  The deterministic backtracking is a local trial safeguard only;
    failed candidates are discarded and cannot mutate that state.
    """

    external = np.asarray(external_increment, dtype=float).reshape(-1)
    bubble = np.asarray(initial_bubble_increment, dtype=float).reshape(-1).copy()
    if external.size != 18 or not np.all(np.isfinite(external)):
        raise ValueError("native S3 external increment must contain 18 finite values")
    if bubble.size != 2 or not np.all(np.isfinite(bubble)):
        raise ValueError("native S3 bubble predictor must contain two finite values")

    evaluations = 0

    def unpack_response(
        response: Any,
    ) -> tuple[
        np.ndarray,
        np.ndarray,
        Dict[str, Any],
        Mapping[str, np.ndarray],
    ]:
        if not isinstance(response, tuple) or len(response) not in (3, 4):
            raise S3BubbleEquilibriumError(
                "native S3 response builder must return three or four values"
            )
        response_force = np.asarray(response[0], dtype=float)
        response_tangent = np.asarray(response[1], dtype=float)
        response_state = response[2]
        pieces = (
            {
                "material": response_tangent,
                "geometric": np.zeros_like(response_tangent),
            }
            if len(response) == 3
            else response[3]
        )
        if not isinstance(pieces, Mapping):
            raise S3BubbleEquilibriumError(
                "native S3 tangent pieces must be a mapping"
            )
        return response_force, response_tangent, response_state, pieces

    accepted: Optional[
        tuple[
            np.ndarray,
            np.ndarray,
            Dict[str, Any],
            Mapping[str, np.ndarray],
        ]
    ] = None
    residual_norm = math.inf
    residual_scale = 1.0
    for iteration in range(1, _BUBBLE_MAX_ITERATIONS + 1):
        if accepted is None:
            force, tangent, trial_state, tangent_pieces = unpack_response(
                response_builder(np.concatenate((external, bubble)))
            )
            evaluations += 1
        else:
            force, tangent, trial_state, tangent_pieces = accepted
            accepted = None
        force = np.asarray(force, dtype=float)
        tangent = np.asarray(tangent, dtype=float)
        material_tangent = np.asarray(
            tangent_pieces.get("material", ()), dtype=float
        )
        geometric_tangent = np.asarray(
            tangent_pieces.get("geometric", ()), dtype=float
        )
        if force.shape != (20,) or tangent.shape != (20, 20):
            raise S3BubbleEquilibriumError(
                "native S3 uncondensed response has an incompatible shape"
            )
        if (
            material_tangent.shape != (20, 20)
            or geometric_tangent.shape != (20, 20)
            or not np.all(np.isfinite(force))
            or not np.all(np.isfinite(tangent))
            or not np.all(np.isfinite(material_tangent))
            or not np.all(np.isfinite(geometric_tangent))
        ):
            raise S3BubbleEquilibriumError(
                "native S3 uncondensed response is non-finite"
            )
        decomposition_error = float(
            np.linalg.norm(
                tangent - material_tangent - geometric_tangent,
                ord="fro",
            )
            / max(float(np.linalg.norm(tangent, ord="fro")), 1.0)
        )
        if decomposition_error > 256.0 * np.finfo(np.float64).eps:
            raise S3BubbleEquilibriumError(
                "native S3 uncondensed tangent decomposition is inconsistent"
            )
        residual = force[18:].copy()
        residual_norm = float(np.linalg.norm(residual, ord=np.inf))
        bubble_block = tangent[18:, 18:]
        residual_scale = max(
            1.0,
            float(np.linalg.norm(force[:18], ord=np.inf)),
            float(np.linalg.norm(bubble_block, ord=np.inf))
            * max(1.0, float(np.linalg.norm(bubble, ord=np.inf))),
        )
        condition = float(np.linalg.cond(bubble_block))
        if not math.isfinite(condition) or condition > BUBBLE_CONDITION_LIMIT:
            raise S3BubbleEquilibriumError(
                "native S3 bubble tangent is singular or ill-conditioned"
            )
        if residual_norm <= _BUBBLE_RELATIVE_TOLERANCE * residual_scale:
            coupling = tangent[18:, :18]
            try:
                total_sensitivity = -np.linalg.solve(bubble_block, coupling)
                residual_correction = np.linalg.solve(bubble_block, residual)
            except np.linalg.LinAlgError as exc:
                raise S3BubbleEquilibriumError(
                    "native S3 converged bubble block is singular"
                ) from exc
            projection = np.vstack(
                (np.eye(18, dtype=np.float64), total_sensitivity)
            )
            condensed_material = projection.T @ material_tangent @ projection
            condensed_geometric = projection.T @ geometric_tangent @ projection
            # Preserve the established binary64 Schur evaluation order for
            # the total tangent.  The two audited pieces are nevertheless
            # projected independently by the one total sensitivity above.
            condensed = (
                tangent[:18, :18]
                - tangent[:18, 18:] @ (-total_sensitivity)
            )
            condensed_force = (
                force[:18] - tangent[:18, 18:] @ residual_correction
            )
            metadata = {
                "bubble_increment": bubble.copy(),
                "bubble_iterations": iteration,
                "bubble_evaluations": evaluations,
                "bubble_residual": residual.copy(),
                "bubble_residual_norm": residual_norm,
                "bubble_residual_scale": residual_scale,
                "bubble_condition": condition,
                "bubble_force_correction": (
                    tangent[:18, 18:] @ residual_correction
                ).copy(),
                "bubble_force_correction_excluded": False,
                "bubble_force_condensation_id": BUBBLE_FORCE_CONDENSATION_ID,
                "bubble_condensation": "G_TRANSPOSE_K_G_SINGLE_TOTAL_SENSITIVITY",
                "bubble_projection_policy_id": (
                    CURRENT_STATE_BUBBLE_PROJECTION_POLICY_ID
                ),
                "bubble_total_sensitivity": total_sensitivity.copy(),
                "bubble_projection": projection.copy(),
                "uncondensed_material_tangent": material_tangent.copy(),
                "uncondensed_geometric_tangent": geometric_tangent.copy(),
                "uncondensed_total_tangent": tangent.copy(),
                "condensed_material_tangent": condensed_material.copy(),
                "condensed_geometric_tangent": condensed_geometric.copy(),
                "uncondensed_decomposition_relative_error": decomposition_error,
            }
            return condensed_force, condensed, trial_state, metadata
        try:
            step = np.linalg.solve(bubble_block, -residual)
        except np.linalg.LinAlgError as exc:
            raise S3BubbleEquilibriumError(
                "native S3 bubble tangent solve failed"
            ) from exc
        step_norm = float(np.linalg.norm(step, ord=np.inf))
        if step_norm <= _BUBBLE_STEP_TOLERANCE * max(
            1.0, float(np.linalg.norm(bubble, ord=np.inf))
        ):
            raise S3BubbleEquilibriumError(
                "native S3 bubble equilibrium stagnated above tolerance"
            )

        factor = 1.0
        accepted_candidate: Optional[
            tuple[
                np.ndarray,
                np.ndarray,
                Dict[str, Any],
                Mapping[str, np.ndarray],
            ]
        ] = None
        accepted_bubble: Optional[np.ndarray] = None
        while factor >= BUBBLE_LINE_SEARCH_MIN_FACTOR:
            candidate_bubble = bubble + factor * step
            candidate = unpack_response(
                response_builder(np.concatenate((external, candidate_bubble)))
            )
            evaluations += 1
            candidate_force = np.asarray(candidate[0], dtype=float)
            candidate_tangent = np.asarray(candidate[1], dtype=float)
            if (
                candidate_force.shape == (20,)
                and candidate_tangent.shape == (20, 20)
                and np.all(np.isfinite(candidate_force))
                and np.all(np.isfinite(candidate_tangent))
            ):
                candidate_norm = float(
                    np.linalg.norm(candidate_force[18:], ord=np.inf)
                )
                if candidate_norm < residual_norm:
                    accepted_candidate = (
                        candidate_force,
                        candidate_tangent,
                        candidate[2],
                        candidate[3],
                    )
                    accepted_bubble = candidate_bubble
                    break
            factor *= BUBBLE_LINE_SEARCH_REDUCTION
        if accepted_candidate is None or accepted_bubble is None:
            raise S3BubbleEquilibriumError(
                "native S3 safeguarded bubble Newton found no residual decrease"
            )
        bubble = accepted_bubble
        accepted = accepted_candidate

    raise S3BubbleEquilibriumError(
        "native S3 bubble equilibrium exceeded the iteration limit "
        f"with residual {residual_norm:.6g} and scale {residual_scale:.6g}"
    )


def _native_station_kinematics(
    current_nodes: np.ndarray,
    director_triads: np.ndarray,
    increment20: np.ndarray,
    reference_nodes: np.ndarray,
    reference_frame: np.ndarray,
    *,
    native_rotation_trial: NativeElementRotationView,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ordered station strains, first derivatives, and Hessians."""

    values = np.zeros((len(TRIANGLE_QUADRATURE), 8), dtype=float)
    gradients = np.zeros((len(TRIANGLE_QUADRATURE), 8, 20), dtype=float)
    hessians = np.zeros((len(TRIANGLE_QUADRATURE), 8, 20, 20), dtype=float)
    for index, (r, s, _weight) in enumerate(TRIANGLE_QUADRATURE):
        values[index], gradients[index], hessians[index] = (
            _native_incremental_strain_jets(
                current_nodes,
                director_triads,
                r,
                s,
                increment20,
                reference_nodes=reference_nodes,
                reference_frame=reference_frame,
                native_rotation_trial=native_rotation_trial,
            )
        )
    return values, gradients, hessians


def _native_generalized_uncondensed_response_components(
    current_nodes: np.ndarray,
    director_triads: np.ndarray,
    increment20: np.ndarray,
    reference_nodes: np.ndarray,
    reference_frame: np.ndarray,
    constitutive: np.ndarray,
    committed_station_strain: np.ndarray,
    reference_surface_offset: float = 0.0,
    initial_generalized_prestrain: Optional[np.ndarray] = None,
    initial_generalized_resultant: Optional[np.ndarray] = None,
    *,
    native_rotation_trial: NativeElementRotationView,
) -> tuple[
    np.ndarray,
    np.ndarray,
    Dict[str, Any],
    Dict[str, np.ndarray],
]:
    """Integrate one stateless generalized section in source coordinates."""

    reference = np.asarray(reference_nodes, dtype=float).reshape(3, 3)
    frame = np.asarray(reference_frame, dtype=float).reshape(3, 3)
    local = (reference - reference[0]) @ frame[:, :2]
    _jacobian_matrix, _inverse, determinant = _jacobian(local)
    section = np.asarray(constitutive, dtype=float).reshape(8, 8)
    committed = np.asarray(committed_station_strain, dtype=float)
    if committed.shape != (len(TRIANGLE_QUADRATURE), 8):
        raise ValueError("native S3 generalized committed strain has an invalid shape")
    initial_prestrain = np.zeros_like(committed)
    if initial_generalized_prestrain is not None:
        initial_prestrain = np.asarray(
            initial_generalized_prestrain, dtype=float
        )
        if (
            initial_prestrain.shape != committed.shape
            or not np.all(np.isfinite(initial_prestrain))
        ):
            raise ValueError(
                "native S3 generalized initial prestrain has an invalid shape"
            )
    initial_resultant = np.zeros_like(committed)
    if initial_generalized_resultant is not None:
        initial_resultant = np.asarray(
            initial_generalized_resultant, dtype=float
        )
        if (
            initial_resultant.shape != committed.shape
            or not np.all(np.isfinite(initial_resultant))
        ):
            raise ValueError(
                "native S3 generalized initial resultant has an invalid shape"
            )
    delta, gradients, hessians = _native_station_kinematics(
        current_nodes,
        director_triads,
        increment20,
        reference,
        frame,
        native_rotation_trial=native_rotation_trial,
    )
    delta, gradients, hessians = _shift_native_station_kinematics_to_section_origin(
        delta,
        gradients,
        hessians,
        reference_surface_offset,
    )
    total_strain = committed + delta
    resultants = (
        (total_strain - initial_prestrain) @ section.T
        + initial_resultant
    )
    force = np.zeros(20, dtype=float)
    material_tangent = np.zeros((20, 20), dtype=float)
    geometric_tangent = np.zeros((20, 20), dtype=float)
    for station, (_r, _s, weight) in enumerate(TRIANGLE_QUADRATURE):
        integration_weight = abs(determinant) * float(weight)
        gradient = gradients[station]
        resultant = resultants[station]
        force += integration_weight * (gradient.T @ resultant)
        material_tangent += integration_weight * (
            gradient.T @ section @ gradient
        )
        geometric_tangent += integration_weight * (
            np.einsum("a,aij->ij", resultant, hessians[station])
        )
    tangent = material_tangent + geometric_tangent
    return force, tangent, {
        "generalized_section": True,
        "station_generalized_strain": total_strain.copy(),
        "station_generalized_resultant": resultants.copy(),
        "initial_generalized_prestrain": initial_prestrain.copy(),
        "initial_generalized_resultant": initial_resultant.copy(),
        "membrane_strain": total_strain[:, :3].copy(),
        "curvature": total_strain[:, 3:6].copy(),
        "transverse_shear_strain": total_strain[:, 6:].copy(),
        "membrane_resultants": resultants[:, :3].copy(),
        "bending_resultants": resultants[:, 3:6].copy(),
        "transverse_shear_resultants": resultants[:, 6:].copy(),
        "membrane_resultant_order": SHELL_MEMBRANE_VOIGT_ORDER,
        "transverse_shear_resultant_order": SHELL_TRANSVERSE_SHEAR_ORDER,
        "recovery_scope": "section_resultants_only",
    }, {
        "material": material_tangent,
        "geometric": geometric_tangent,
    }


def _native_generalized_uncondensed_response(
    *args: Any,
    **kwargs: Any,
) -> tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """Compatibility view of the native generalized total response."""

    force, tangent, trial_state, _pieces = (
        _native_generalized_uncondensed_response_components(*args, **kwargs)
    )
    return force, tangent, trial_state


def _native_layered_uncondensed_response_components(
    current_nodes: np.ndarray,
    director_triads: np.ndarray,
    increment20: np.ndarray,
    reference_nodes: np.ndarray,
    reference_frame: np.ndarray,
    material: Any,
    material_angle: float,
    thickness: float,
    state: Mapping[str, Any],
    num_layers: int,
    reference_surface_offset: float = 0.0,
    *,
    native_rotation_trial: NativeElementRotationView,
) -> tuple[
    np.ndarray,
    np.ndarray,
    Dict[str, Any],
    Dict[str, np.ndarray],
]:
    """Integrate the native seven-station layered physical response.

    Geometry is incremental total Lagrangian, while the existing plane-stress
    return maps retain their explicitly bounded large-rotation/small-material-
    strain role.  Every call starts from the unchanged committed history in
    ``state``; callers may therefore evaluate multiple bubble candidates
    without chaining trial plasticity.
    """

    reference = np.asarray(reference_nodes, dtype=float).reshape(3, 3)
    frame = np.asarray(reference_frame, dtype=float).reshape(3, 3)
    local = (reference - reference[0]) @ frame[:, :2]
    _jacobian_matrix, _inverse, determinant = _jacobian(local)
    delta, gradients, hessians = _native_station_kinematics(
        current_nodes,
        director_triads,
        increment20,
        reference,
        frame,
        native_rotation_trial=native_rotation_trial,
    )
    delta, gradients, hessians = _shift_native_station_kinematics_to_section_origin(
        delta,
        gradients,
        hessians,
        reference_surface_offset,
    )
    station_count = len(TRIANGLE_QUADRATURE)
    try:
        z_layers, layer_weights = qualified_s3_lobatto_layers(
            num_layers,
            thickness,
        )
    except S3CommittedStateError as exc:
        raise ValueError(str(exc)) from exc
    layer_count = int(z_layers.size)
    total_points = station_count * layer_count

    committed_kinematic = np.asarray(
        state.get("kinematic_layer_strain", ()), dtype=float
    )
    if committed_kinematic.shape != (total_points, 3):
        raise ValueError(
            "native S3 committed kinematic_layer_strain has an invalid shape"
        )
    committed_station = np.asarray(
        state.get("station_generalized_strain", ()), dtype=float
    )
    if committed_station.shape != (station_count, 8):
        raise ValueError(
            "native S3 committed station_generalized_strain has an invalid shape"
        )
    total_station = committed_station + delta
    trial_kinematic = (
        committed_kinematic.reshape(station_count, layer_count, 3)
        + delta[:, None, :3]
        + z_layers[None, :, None] * delta[:, None, 3:6]
    )

    symmetry = _elastic_symmetry(material)
    curve = getattr(material, "hardening_curve", None)
    hill_yield = getattr(material, "hill_yield", None)
    if symmetry == "orthotropic" and curve is not None and hill_yield is None:
        raise ValueError(
            f"Orthotropic material {getattr(material, 'name', '<unnamed>')!r} "
            "requires hill_yield when hardening_curve is active."
        )
    hill_plasticity = symmetry == "orthotropic" and hill_yield is not None
    constitutive_plasticity = curve is not None or hill_plasticity
    elastic, shear_elastic, strain_to_material, stress_to_local = (
        _shell_material_matrices(material, float(material_angle))
    )
    material_elastic, _material_shear, _identity_strain, _identity_stress = (
        _shell_material_matrices(material, 0.0)
    )

    initial_state = _copy_state_fields(dict(state), _INITIAL_SHELL_STATE_KEYS)
    zero_rows = np.zeros((station_count, 3), dtype=float)
    membrane_stress = _shell_field_rows(
        initial_state.get("initial_membrane_stress", zero_rows),
        station_count,
        "initial_membrane_stress",
    )
    bending_stress = _shell_field_rows(
        initial_state.get("initial_bending_stress", zero_rows),
        station_count,
        "initial_bending_stress",
    )
    membrane_prestrain = _shell_field_rows(
        initial_state.get("initial_membrane_prestrain", zero_rows),
        station_count,
        "initial_membrane_prestrain",
    )
    curvature_prestrain = _shell_field_rows(
        initial_state.get("initial_curvature_prestrain", zero_rows),
        station_count,
        "initial_curvature_prestrain",
    )
    initial_stress = (
        membrane_stress[:, None, :]
        + (2.0 * z_layers[None, :, None] / float(thickness))
        * bending_stress[:, None, :]
    )
    eigenstrain = (
        membrane_prestrain[:, None, :]
        + z_layers[None, :, None] * curvature_prestrain[:, None, :]
    )
    if symmetry == "orthotropic":
        initial_stress_material = np.einsum(
            "ij,glj->gli", np.linalg.inv(stress_to_local), initial_stress
        )
        kinematic_material = np.einsum(
            "ij,glj->gli", strain_to_material, trial_kinematic
        )
        eigenstrain_material = np.einsum(
            "ij,glj->gli", strain_to_material, eigenstrain
        )
        material_offset = np.einsum(
            "ij,glj->gli",
            np.linalg.inv(material_elastic),
            initial_stress_material,
        )
        layer_strain_material = (
            kinematic_material - eigenstrain_material + material_offset
        ).reshape(total_points, 3)
        local_offset = np.einsum(
            "ij,glj->gli", np.linalg.inv(elastic), initial_stress
        )
        layer_strain = (
            trial_kinematic - eigenstrain + local_offset
        ).reshape(total_points, 3)
    else:
        local_offset = np.einsum(
            "ij,glj->gli", np.linalg.inv(elastic), initial_stress
        )
        layer_strain = (
            trial_kinematic - eigenstrain + local_offset
        ).reshape(total_points, 3)
        layer_strain_material = layer_strain.copy()

    plastic_strain = np.asarray(state.get("plastic_strain", ()), dtype=float)
    hardening = np.asarray(state.get("alpha", ()), dtype=float)
    if plastic_strain.shape != (total_points, 3) or hardening.shape != (total_points,):
        raise ValueError("native S3 committed plastic history has an invalid shape")
    if not constitutive_plasticity:
        if symmetry == "orthotropic":
            stress_material = layer_strain_material @ material_elastic.T
            stress = stress_material @ stress_to_local.T
            tangent_material = np.broadcast_to(
                material_elastic, (total_points, 3, 3)
            )
            tangent_local = np.einsum(
                "ij,njk,kl->nil",
                stress_to_local,
                tangent_material,
                strain_to_material,
            )
        else:
            stress = layer_strain @ elastic.T
            stress_material = stress.copy()
            tangent_local = np.broadcast_to(
                elastic, (total_points, 3, 3)
            ).copy()
        plastic_new = plastic_strain.copy()
        hardening_new = hardening.copy()
    elif hill_plasticity:
        from .plasticity import hill48_plane_stress_return_map

        stress_material, tangent_material, plastic_new, hardening_new = (
            hill48_plane_stress_return_map(
                layer_strain_material,
                plastic_strain,
                hardening,
                material_elastic,
                hill_yield,
                curve,
                compute_tangent=True,
            )
        )
        stress = stress_material @ stress_to_local.T
        tangent_local = np.einsum(
            "ij,njk,kl->nil",
            stress_to_local,
            tangent_material,
            strain_to_material,
        )
    else:
        if isinstance(curve, DNVC208MaterialCurve):
            stress, tangent_local, plastic_new, hardening_new = (
                plane_stress_return_map(
                    layer_strain,
                    plastic_strain,
                    hardening,
                    float(material.elastic_modulus),
                    float(material.poisson_ratio),
                    curve,
                    compute_tangent=True,
                )
            )
        else:
            # The generic Hill-48 return map consumes the public hardening-
            # curve protocol without approximating or converting its law.  In
            # the isotropic limit X=Y=Z=flow(0) and
            # S12=S13=S23=flow(0)/sqrt(3), its quadratic is exactly the
            # plane-stress von-Mises metric.  Its associated-flow multiplier
            # and alpha evolution are the same discrete equations as the
            # established isotropic return map under the exact rescaling
            # gamma=(2/3)*delta_lambda.
            from .plasticity import hill48_plane_stress_return_map

            flow_method = getattr(curve, "flow_stress", None)
            if not callable(flow_method):
                raise TypeError(
                    "qualified S3 isotropic hardening curve must provide "
                    "flow_stress()"
                )
            initial_flow_values = np.asarray(
                flow_method(np.zeros(1, dtype=np.float64)), dtype=np.float64
            ).reshape(-1)
            if (
                initial_flow_values.size != 1
                or not math.isfinite(float(initial_flow_values[0]))
                or float(initial_flow_values[0]) <= 0.0
            ):
                raise ValueError(
                    "qualified S3 isotropic hardening curve flow_stress(0) "
                    "must be finite and strictly positive"
                )
            reference_flow = float(initial_flow_values[0])
            shear_flow = reference_flow / math.sqrt(3.0)
            isotropic_yield = Hill48Yield(
                X=reference_flow,
                Y=reference_flow,
                Z=reference_flow,
                S12=shear_flow,
                S13=shear_flow,
                S23=shear_flow,
            )
            stress, tangent_local, plastic_new, hardening_new = (
                hill48_plane_stress_return_map(
                    layer_strain,
                    plastic_strain,
                    hardening,
                    elastic,
                    isotropic_yield,
                    curve,
                    compute_tangent=True,
                )
            )
        stress_material = stress.copy()

    stress_layers = np.asarray(stress, dtype=float).reshape(
        station_count, layer_count, 3
    )
    tangent_layers = np.asarray(tangent_local, dtype=float).reshape(
        station_count, layer_count, 3, 3
    )
    membrane_resultants = np.einsum("l,gli->gi", layer_weights, stress_layers)
    bending_resultants = np.einsum(
        "l,l,gli->gi", layer_weights, z_layers, stress_layers
    )
    shear_stiffness = (5.0 / 6.0) * float(thickness) * shear_elastic
    shear_resultants = total_station[:, 6:] @ shear_stiffness.T
    station_resultants = np.concatenate(
        (membrane_resultants, bending_resultants, shear_resultants), axis=1
    )

    force = np.zeros(20, dtype=float)
    material_tangent = np.zeros((20, 20), dtype=float)
    geometric_tangent = np.zeros((20, 20), dtype=float)
    for station, (_r, _s, weight) in enumerate(TRIANGLE_QUADRATURE):
        area_weight = abs(determinant) * float(weight)
        for layer in range(layer_count):
            gradient = (
                gradients[station, :3]
                + z_layers[layer] * gradients[station, 3:6]
            )
            hessian = (
                hessians[station, :3]
                + z_layers[layer] * hessians[station, 3:6]
            )
            layer_stress = stress_layers[station, layer]
            layer_weight = area_weight * float(layer_weights[layer])
            force += layer_weight * (gradient.T @ layer_stress)
            material_tangent += layer_weight * (
                gradient.T @ tangent_layers[station, layer] @ gradient
            )
            geometric_tangent += layer_weight * (
                np.einsum("a,aij->ij", layer_stress, hessian)
            )
        shear_gradient = gradients[station, 6:]
        shear_hessian = hessians[station, 6:]
        shear_resultant = shear_resultants[station]
        force += area_weight * (shear_gradient.T @ shear_resultant)
        material_tangent += area_weight * (
            shear_gradient.T @ shear_stiffness @ shear_gradient
        )
        geometric_tangent += area_weight * (
            np.einsum("a,aij->ij", shear_resultant, shear_hessian)
        )

    trial_state: Dict[str, Any] = {
        "plastic_strain": np.asarray(plastic_new, dtype=float).copy(),
        "alpha": np.asarray(hardening_new, dtype=float).copy(),
        "layer_strain": np.asarray(layer_strain, dtype=float).copy(),
        "layer_strain_material": np.asarray(
            layer_strain_material, dtype=float
        ).copy(),
        "kinematic_layer_strain": trial_kinematic.reshape(
            total_points, 3
        ).copy(),
        "layer_stress": np.asarray(stress, dtype=float).copy(),
        "station_generalized_strain": total_station.copy(),
        "station_generalized_resultant": station_resultants.copy(),
        "membrane_strain": total_station[:, :3].copy(),
        "curvature": total_station[:, 3:6].copy(),
        "transverse_shear_strain": total_station[:, 6:].copy(),
        "membrane_resultants": membrane_resultants.copy(),
        "bending_resultants": bending_resultants.copy(),
        "transverse_shear_resultants": shear_resultants.copy(),
        "membrane_resultant_order": SHELL_MEMBRANE_VOIGT_ORDER,
        "transverse_shear_resultant_order": SHELL_TRANSVERSE_SHEAR_ORDER,
        **initial_state,
    }
    if symmetry == "orthotropic":
        trial_state["layer_stress_material"] = np.asarray(
            stress_material, dtype=float
        ).copy()
        trial_state["equivalent_stress_measure"] = (
            "hill48" if hill_yield is not None else "von_mises"
        )
    else:
        trial_state["layer_stress_material"] = np.asarray(
            stress_material, dtype=float
        ).copy()
        trial_state["equivalent_stress_measure"] = "von_mises"
    tangent = material_tangent + geometric_tangent
    return force, tangent, trial_state, {
        "material": material_tangent,
        "geometric": geometric_tangent,
    }


def _native_layered_uncondensed_response(
    *args: Any,
    **kwargs: Any,
) -> tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """Compatibility view of the native layered total response."""

    force, tangent, trial_state, _pieces = (
        _native_layered_uncondensed_response_components(*args, **kwargs)
    )
    return force, tangent, trial_state


class QualifiedE4PLS3ShellElement(ShellElement):
    """Opt-in three-node flat MITC3+ shell with three-mode PL completion."""

    formulation_id = FORMULATION_ID
    formulation_native_total_lagrangian = True
    dynamic_algebraic_nullity = 3
    dynamic_algebraic_policy = ALGEBRAIC_COORDINATE_POLICY_ID
    dynamic_algebraic_mass_witness = "S3_LOCAL_DRILL_ROWS_EXACT_ZERO_V1"
    dynamic_algebraic_local_zero_indices = (5, 11, 17)
    legacy_stiffness_batch_eligible = False
    legacy_nonlinear_batch_eligible = False
    recovery_errors_fail_closed = True

    def __init__(
        self,
        element_id: int,
        node_ids: list[int],
        material_name: str = "default",
        thickness: float = 0.01,
        drilling_stabilization: Optional[float] = None,
        reduced_integration: bool = False,
        hourglass_stabilization: Optional[float] = None,
        material_direction: Optional[np.ndarray] = None,
        material_angle_deg: float = 0.0,
        shell_section: Optional[Any] = None,
        reference_normal: Optional[Sequence[float]] = None,
        director_polarity: int = 1,
        reference_surface_offset: float = 0.0,
    ) -> None:
        if len(node_ids) != 3:
            raise ValueError("QualifiedE4PLS3ShellElement requires exactly three nodes")
        if material_direction is None and float(material_angle_deg) != 0.0:
            raise ValueError(
                "qualified S3 material_angle_deg requires a physical material_direction"
            )
        if drilling_stabilization not in {None, 0, 0.0}:
            raise ValueError(
                "qualified S3 has no user drilling coefficient; use formulation='legacy-s3'"
            )
        if hourglass_stabilization not in {None, 0, 0.0}:
            raise ValueError(
                "qualified S3 has no hourglass coefficient; use formulation='legacy-s3'"
            )
        if bool(reduced_integration):
            raise ValueError(
                "qualified S3 uses its frozen seven-point rule; use formulation='legacy-s3' "
                "for reduced_integration"
            )
        if shell_section is not None:
            require_stateless_generalized_section(shell_section)
        super().__init__(
            element_id,
            node_ids,
            material_name,
            thickness,
            0.0,
            False,
            0.0,
            material_direction,
            material_angle_deg,
            shell_section,
        )
        if reference_normal is None:
            raise ValueError(
                "qualified S3 requires an authoritative reference_normal; "
                "connectivity winding is not a physical director"
            )
        normal = np.asarray(reference_normal, dtype=float).reshape(-1)
        if normal.size != 3 or not np.all(np.isfinite(normal)):
            raise ValueError("qualified S3 reference_normal must be a finite 3-vector")
        self.reference_normal = _normalize(normal, "reference normal")
        if isinstance(director_polarity, (bool, np.bool_)) or not isinstance(
            director_polarity, (int, np.integer)
        ) or int(director_polarity) not in (-1, 1):
            raise ValueError("qualified S3 director_polarity must be the integer -1 or +1")
        self.director_polarity = int(director_polarity)
        if isinstance(reference_surface_offset, (bool, np.bool_)) or not isinstance(
            reference_surface_offset,
            (int, float, np.integer, np.floating),
        ):
            raise ValueError(
                "qualified S3 reference_surface_offset must be a finite real scalar"
            )
        offset = float(reference_surface_offset)
        if not math.isfinite(offset):
            raise ValueError(
                "qualified S3 reference_surface_offset must be a finite real scalar"
            )
        self.reference_surface_offset = 0.0 if offset == 0.0 else offset
        self._qualified_components: Optional[Dict[str, Any]] = None
        self._qualified_cache_key: Optional[tuple[Any, ...]] = None

    @property
    def capability_gaps(self) -> frozenset[str]:
        if self.shell_section is None:
            return CAPABILITY_GAPS - _LAYERED_NATIVE_CLOSED_CAPABILITIES
        return CAPABILITY_GAPS - _GENERALIZED_NATIVE_CLOSED_CAPABILITIES

    @property
    def nonlinear_material_response_mode(self) -> str:
        """Declare stateful layers versus a stateless fixed section."""

        if self.shell_section is None:
            return STATEFUL_MATERIAL_RESPONSE_MODE
        return STATELESS_FIXED_GENERALIZED_SECTION_RESPONSE_MODE

    @property
    def gauss_points(self) -> np.ndarray:
        return np.asarray([(r, s) for r, s, _weight in TRIANGLE_QUADRATURE], dtype=float)

    @property
    def gauss_weights(self) -> np.ndarray:
        return np.asarray([weight for _r, _s, weight in TRIANGLE_QUADRATURE], dtype=float)

    @property
    def shear_gauss_points(self) -> np.ndarray:
        return self.gauss_points

    @property
    def shear_gauss_weights(self) -> np.ndarray:
        return self.gauss_weights

    def capability_matrix(self) -> Dict[str, str]:
        return {
            "consistent_mass": "PARITY_REPLACED",
            "linear_stiffness": "PARITY_REPLACED",
            "linear_internal_force": "PARITY_REPLACED",
            "reference_surface_offset": "PARITY_REPLACED",
            "local_physical_recovery": "PARITY_REPLACED",
            "global_recovery": "PARITY_REPLACED",
            "orthotropic_physical_recovery": "PARITY_REPLACED",
            "generalized_sections": "PARITY_REPLACED",
            "geometric_stiffness": "PARITY_REPLACED",
            "reference_elastic_prestressed_modal": "PARITY_REPLACED",
            "reference_elastic_buckling": "PARITY_REPLACED",
            "current_state_modal": "PARITY_REPLACED",
            "current_state_buckling": "PARITY_REPLACED",
            "transient_algebraic_dynamics": "PARITY_REPLACED",
            **(
                {
                    "stateless_generalized_section_nonlinear_geometry": (
                        "PARITY_REPLACED"
                    )
                }
                if self.shell_section is not None
                else {}
            ),
            **{name: "PARITY_GAP" for name in sorted(self.capability_gaps)},
            **{
                name: "PARITY_REPLACED"
                for name in sorted(
                    (
                        _LAYERED_NATIVE_CLOSED_CAPABILITIES
                        if self.shell_section is None
                        else _GENERALIZED_NATIVE_CLOSED_CAPABILITIES
                    )
                    - self.capability_gaps
                )
            },
        }

    def to_dict(self) -> Dict[str, Any]:
        payload = super().to_dict()
        payload.update(
            {
                "formulation_id": FORMULATION_ID,
                "formulation_schema": FORMULATION_SCHEMA,
                "bubble_convention": BUBBLE_CONVENTION,
                "quadrature_id": QUADRATURE_ID,
                "dynamic_reduction_policy": DYNAMIC_REDUCTION_POLICY,
                "algebraic_coordinate_policy": ALGEBRAIC_COORDINATE_POLICY_ID,
                "geometric_stiffness_policy": GEOMETRIC_STIFFNESS_POLICY_ID,
                "mass_moment_id": MASS_MOMENT_ID,
                "recovery_policy_id": RECOVERY_POLICY_ID,
                "state_layout_id": STATE_LAYOUT_ID,
                "director_polarity_policy_id": DIRECTOR_POLARITY_POLICY_ID,
                "director_reversal_transform_id": DIRECTOR_REVERSAL_TRANSFORM_ID,
                "director_polarity": int(self.director_polarity),
                "reference_surface_offset_policy_id": (
                    REFERENCE_SURFACE_OFFSET_POLICY_ID
                ),
                "reference_surface_strain_transform_id": (
                    REFERENCE_SURFACE_STRAIN_TRANSFORM_ID
                ),
                "reference_surface_mass_shift_id": (
                    REFERENCE_SURFACE_MASS_SHIFT_ID
                ),
                "reference_surface_offset": float(self.reference_surface_offset),
                "reference_normal": (
                    None
                    if self.reference_normal is None
                    else np.asarray(self.reference_normal, dtype=float).tolist()
                ),
            }
        )
        return payload

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "QualifiedE4PLS3ShellElement":
        data = dict(payload)
        if data.get("formulation_id") != FORMULATION_ID:
            raise ValueError("serialized qualified S3 formulation_id is missing or incompatible")
        if data.get("formulation_schema") != FORMULATION_SCHEMA:
            raise ValueError("serialized qualified S3 formulation schema is incompatible")
        if data.get("bubble_convention") != BUBBLE_CONVENTION:
            raise ValueError("serialized qualified S3 bubble convention is incompatible")
        if data.get("quadrature_id") != QUADRATURE_ID:
            raise ValueError("serialized qualified S3 quadrature identity is incompatible")
        if data.get("dynamic_reduction_policy") != DYNAMIC_REDUCTION_POLICY:
            raise ValueError("serialized qualified S3 dynamic policy is incompatible")
        if data.get("algebraic_coordinate_policy") != ALGEBRAIC_COORDINATE_POLICY_ID:
            raise ValueError("serialized qualified S3 algebraic coordinate policy is incompatible")
        if data.get("geometric_stiffness_policy") != GEOMETRIC_STIFFNESS_POLICY_ID:
            raise ValueError("serialized qualified S3 geometric stiffness policy is incompatible")
        if data.get("mass_moment_id") != MASS_MOMENT_ID:
            raise ValueError("serialized qualified S3 mass moment identity is incompatible")
        if data.get("recovery_policy_id") != RECOVERY_POLICY_ID:
            raise ValueError("serialized qualified S3 recovery policy is incompatible")
        if data.get("state_layout_id") != STATE_LAYOUT_ID:
            raise ValueError("serialized qualified S3 state layout is incompatible")
        if data.get("director_polarity_policy_id") != DIRECTOR_POLARITY_POLICY_ID:
            raise ValueError("serialized qualified S3 director polarity policy is incompatible")
        if data.get("director_reversal_transform_id") != DIRECTOR_REVERSAL_TRANSFORM_ID:
            raise ValueError("serialized qualified S3 director reversal transform is incompatible")
        if data.get("reference_surface_offset_policy_id") != REFERENCE_SURFACE_OFFSET_POLICY_ID:
            raise ValueError(
                "serialized qualified S3 reference-surface offset policy is incompatible"
            )
        if data.get("reference_surface_strain_transform_id") != REFERENCE_SURFACE_STRAIN_TRANSFORM_ID:
            raise ValueError(
                "serialized qualified S3 reference-surface strain transform is incompatible"
            )
        if data.get("reference_surface_mass_shift_id") != REFERENCE_SURFACE_MASS_SHIFT_ID:
            raise ValueError(
                "serialized qualified S3 reference-surface mass shift is incompatible"
            )
        serialized_offset = data.get("reference_surface_offset")
        if isinstance(serialized_offset, (bool, np.bool_)) or not isinstance(
            serialized_offset,
            (int, float, np.integer, np.floating),
        ) or not math.isfinite(float(serialized_offset)):
            raise ValueError(
                "serialized qualified S3 reference_surface_offset is incompatible"
            )
        serialized_polarity = data.get("director_polarity")
        if isinstance(serialized_polarity, (bool, np.bool_)) or not isinstance(
            serialized_polarity, (int, np.integer)
        ) or int(serialized_polarity) not in (-1, 1):
            raise ValueError("serialized qualified S3 director_polarity is incompatible")
        if data.get("type") not in {cls.__name__, "e4-pl-s3", "qualified-s3"}:
            raise ValueError("serialized qualified S3 type is incompatible")
        return cls(
            element_id=int(data["element_id"]),
            node_ids=[int(value) for value in data["node_ids"]],
            material_name=str(data.get("material_name", "default")),
            thickness=float(data.get("thickness", 0.01)),
            drilling_stabilization=data.get("drilling_stabilization"),
            reduced_integration=data.get("reduced_integration", False),
            hourglass_stabilization=data.get("hourglass_stabilization"),
            material_direction=data.get("material_direction"),
            material_angle_deg=float(data.get("material_angle_deg", 0.0)),
            shell_section=data.get("shell_section"),
            reference_normal=data.get("reference_normal"),
            director_polarity=int(serialized_polarity),
            reference_surface_offset=float(serialized_offset),
        )

    def _cache_key(self, mesh: Any, material: Any, coordinates: np.ndarray) -> tuple[Any, ...]:
        revisions = getattr(mesh, "revision_signature", lambda: {})()
        relative = coordinates - np.mean(coordinates, axis=0)
        return (
            id(mesh),
            id(material),
            int(revisions.get("geometry", 0)),
            int(revisions.get("material", 0)),
            np.ascontiguousarray(relative, dtype=float).tobytes(),
            float(self.thickness),
            float(self.material_angle_deg),
            None
            if self.material_direction is None
            else tuple(np.asarray(self.material_direction, dtype=float)),
            id(self.shell_section),
            None
            if self.reference_normal is None
            else tuple(np.asarray(self.reference_normal, dtype=float)),
            int(self.director_polarity),
            float(self.reference_surface_offset),
        )

    @property
    def physical_reference_director(self) -> np.ndarray:
        """Return the element-owned director, independent of sheet winding."""

        return (
            float(self.director_polarity)
            * np.asarray(self.reference_normal, dtype=float)
        ).copy()

    @property
    def material_mid_surface_offset_from_reference(self) -> float:
        """Signed distance from nodal reference to the section origin."""

        return -float(self.reference_surface_offset)

    def material_surface_offset_from_reference(
        self,
        normalized_thickness_coordinate: float,
    ) -> float:
        """Return a material-surface distance along the physical director.

        The normalized coordinate is ``-1`` at physical bottom and ``+1`` at
        physical top.  The nodal reference surface is at section coordinate
        ``reference_surface_offset``.
        """

        if isinstance(normalized_thickness_coordinate, (bool, np.bool_)):
            raise ValueError("qualified S3 surface coordinate must be finite")
        coordinate = float(normalized_thickness_coordinate)
        if not math.isfinite(coordinate) or coordinate < -1.0 or coordinate > 1.0:
            raise ValueError(
                "qualified S3 surface coordinate must be finite and in [-1, 1]"
            )
        return (
            0.5 * float(self.thickness) * coordinate
            - float(self.reference_surface_offset)
        )

    def _director_generalized_transform(self) -> np.ndarray:
        """Map owner-frame generalized fields into physical-director fields."""

        transform = np.eye(8, dtype=float)
        transform[3:, 3:] *= float(self.director_polarity)
        return transform

    def _initial_fields_in_physical_director_convention(
        self,
        initial_fields: Optional[Mapping[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Map owner-defined first moments/curvatures to physical thickness."""

        if initial_fields is None:
            return None
        mapped = dict(initial_fields)
        polarity = float(self.director_polarity)
        for name in ("initial_bending_stress", "initial_curvature_prestrain"):
            if name in mapped:
                try:
                    mapped[name] = polarity * np.asarray(mapped[name], dtype=float)
                except (TypeError, ValueError) as exc:
                    raise S3CommittedStateError(
                        f"{name} must contain numeric values"
                    ) from exc
        return mapped

    def _constitutive(self, material: Any, frame: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        constitutive = np.zeros((8, 8), dtype=float)
        if self.shell_section is not None:
            if self.material_direction is None and not _is_rotation_invariant_section(
                self.shell_section
            ):
                raise ValueError(
                    "qualified S3 anisotropic generalized sections require a physical "
                    "material_direction"
                )
            section = self._generalized_section_in_frame(frame)
            assert section is not None
            constitutive[:3, :3] = section.A
            constitutive[:3, 3:6] = section.B
            constitutive[3:6, :3] = section.B.T
            constitutive[3:6, 3:6] = section.D
            constitutive[6:, 6:] = section.As
            reversal = self._director_generalized_transform()
            constitutive = reversal @ constitutive @ reversal
            membrane = np.asarray(section.A, dtype=float)
        else:
            if self.material_direction is None and not is_isotropic_material(material):
                raise ValueError(
                    "qualified S3 anisotropic materials require a physical material_direction"
                )
            membrane_material, shear, _strain_transform, _stress_transform = (
                _shell_material_matrices(material, self._material_angle(frame))
            )
            membrane = self.thickness * membrane_material
            constitutive[:3, :3] = membrane
            constitutive[3:6, 3:6] = self.thickness**3 / 12.0 * membrane_material
            constitutive[6:, 6:] = (5.0 / 6.0) * self.thickness * shear
        if not np.all(np.isfinite(constitutive)):
            raise ValueError("qualified S3 constitutive matrix must be finite")
        if float(np.linalg.eigvalsh(0.5 * (constitutive + constitutive.T))[0]) <= 0.0:
            raise ValueError("qualified S3 constitutive matrix must be positive definite")
        return constitutive, membrane

    def _compute_stiffness_components(
        self,
        mesh: Any,
        material: Any,
        *,
        enforce_positive_winding: bool,
    ) -> Dict[str, Any]:
        coordinates = self.get_node_coordinates(mesh)
        cache_key = (*self._cache_key(mesh, material, coordinates), enforce_positive_winding)
        if self._qualified_components is not None and self._qualified_cache_key == cache_key:
            return self._qualified_components

        frame, local, quality = triangle_frame(coordinates, self.reference_normal)
        _require_admitted_quality(
            quality, enforce_positive_winding=enforce_positive_winding
        )
        _jac, _inverse, determinant = _jacobian(local)
        constitutive, membrane = self._constitutive(material, frame)
        k_d = invariant_drilling_scale(membrane)

        shear_samples = _assumed_shear_samples(local)
        director_generalized_transform = self._director_generalized_transform()
        reference_surface_transform = _reference_surface_strain_transform(
            self.reference_surface_offset
        )
        uncondensed = np.zeros((17, 17), dtype=float)
        kinematic_operators = []
        for r, s, weight in TRIANGLE_QUADRATURE:
            physical_reference_operator = (
                director_generalized_transform
                @ _kinematic_matrix(local, r, s, shear_samples)
            )
            operator = (
                physical_reference_operator
                if self.reference_surface_offset == 0.0
                else reference_surface_transform @ physical_reference_operator
            )
            kinematic_operators.append(operator)
            uncondensed += abs(determinant) * weight * (operator.T @ constitutive @ operator)
        uncondensed = 0.5 * (uncondensed + uncondensed.T)
        external_block = uncondensed[:15, :15]
        external_internal = uncondensed[:15, 15:]
        internal_block = uncondensed[15:, 15:]
        if _matrix_rank(internal_block) != 2:
            raise ValueError("qualified S3 bubble block is singular")
        if float(np.linalg.eigvalsh(internal_block)[0]) <= 0.0:
            raise ValueError("qualified S3 bubble block is not positive definite")
        bubble_map = -np.linalg.solve(internal_block, external_internal.T)
        physical_15 = external_block + external_internal @ bubble_map
        physical_15 = 0.5 * (physical_15 + physical_15.T)
        physical_local = np.zeros((18, 18), dtype=float)
        physical_local[np.ix_(PHYSICAL_EXTERNAL_INDICES, PHYSICAL_EXTERNAL_INDICES)] = physical_15

        constraint, multiplier_gram, pl_local = _pl_operators(local, k_d)
        total_local = physical_local + pl_local
        transform = self._local_dof_transform(frame)
        physical = transform.T @ physical_local @ transform
        pl = transform.T @ pl_local @ transform
        total = transform.T @ total_local @ transform
        for matrix in (physical, pl, total):
            matrix[:] = 0.5 * (matrix + matrix.T)

        embedded_uncondensed = np.zeros((20, 20), dtype=float)
        combined_indices = np.concatenate((PHYSICAL_EXTERNAL_INDICES, np.asarray((18, 19))))
        embedded_uncondensed[np.ix_(combined_indices, combined_indices)] = uncondensed
        coupling = np.zeros((20, 3), dtype=float)
        coupling[:18] = constraint.T @ multiplier_gram
        saddle = np.zeros((23, 23), dtype=float)
        saddle[:20, :20] = embedded_uncondensed
        saddle[:20, 20:] = coupling
        saddle[20:, :20] = coupling.T
        saddle[20:, 20:] = -multiplier_gram / k_d

        characteristic_length = float(
            max(
                np.linalg.norm(local[1] - local[0]),
                np.linalg.norm(local[2] - local[1]),
                np.linalg.norm(local[0] - local[2]),
            )
        )
        ranks = _structural_rank_certificate(
            kinematic_operators, constraint, characteristic_length
        )
        result: Dict[str, Any] = {
            "physical": physical,
            "core": physical,
            "pl": pl,
            "hourglass": np.zeros((18, 18), dtype=float),
            "numerical": pl,
            "total": total,
            "frame": frame,
            "local_nodes": local,
            "quality": quality,
            "constitutive": constitutive,
            "director_polarity": int(self.director_polarity),
            "director_reversal_transform_id": DIRECTOR_REVERSAL_TRANSFORM_ID,
            "reference_surface_offset": float(self.reference_surface_offset),
            "reference_surface_offset_policy_id": REFERENCE_SURFACE_OFFSET_POLICY_ID,
            "reference_surface_strain_transform_id": (
                REFERENCE_SURFACE_STRAIN_TRANSFORM_ID
            ),
            "reference_surface_strain_transform": reference_surface_transform,
            "k_d": k_d,
            "uncondensed_physical": uncondensed,
            "condensed_physical_15": physical_15,
            "bubble_block": internal_block,
            "bubble_map": bubble_map,
            "pl_constraint": constraint,
            "pl_multiplier_gram": multiplier_gram,
            "full_saddle": saddle,
            "assumed_shear_samples": shear_samples,
            "ranks": ranks,
            "rank_certificate": "DIMENSIONLESS_KINEMATIC_SUBSPACE_V1",
            "floating_matrix_diagnostics": {
                "bubble_rank": _matrix_rank(internal_block),
                "saddle_inertia": _inertia(saddle),
            },
            "mixed_condensed": True,
            "legacy_fallback": False,
            "formulation_id": FORMULATION_ID,
        }
        self._qualified_components = result
        self._qualified_cache_key = cache_key
        self._hourglass_stiffness_matrix = np.zeros((18, 18), dtype=float)
        self._stiffness_matrix = total
        return result

    def compute_stiffness_components(self, mesh: Any, material: Any) -> Dict[str, Any]:
        """Return the production-admitted linear component split."""

        return self._compute_stiffness_components(
            mesh, material, enforce_positive_winding=True
        )

    def compute_stiffness_matrix(self, mesh: Any, material: Any) -> np.ndarray:
        return np.asarray(self.compute_stiffness_components(mesh, material)["total"])

    def compute_internal_forces(
        self,
        mesh: Any,
        displacements: np.ndarray,
        material: Any,
    ) -> np.ndarray:
        vector = self._get_element_displacements(mesh, displacements)
        return self.compute_stiffness_matrix(mesh, material) @ vector

    def numerical_internal_force(self, displacement: np.ndarray) -> Dict[str, np.ndarray]:
        if self._qualified_components is None:
            raise RuntimeError("compute_stiffness_matrix must run before numerical force recovery")
        vector = np.asarray(displacement, dtype=float).reshape(self.total_dofs)
        pl = np.asarray(self._qualified_components["pl"]) @ vector
        return {
            "pl": pl,
            "hourglass": np.zeros_like(pl),
            "numerical": pl.copy(),
        }

    def _compute_stresses(
        self,
        mesh: Any,
        displacements: np.ndarray,
        material: Any,
        *,
        return_global: bool,
        enforce_positive_winding: bool,
    ) -> Dict[str, Any]:
        """Recover native local/global physical fields at seven points.

        The two bubble rotations are recovered from the same elastic Schur
        map used by the tangent.  PL forces never enter section resultants or
        physical stresses.  Global surface tensors are passive rotations of
        the numbered-frame stresses and therefore remain invariant under D3
        connectivity re-expression.
        """

        element_displacements = self._get_element_displacements(mesh, displacements)
        if not np.all(np.isfinite(element_displacements)):
            raise ValueError("qualified S3 recovery requires finite displacements")
        components = self._compute_stiffness_components(
            mesh,
            material,
            enforce_positive_winding=enforce_positive_winding,
        )
        frame = np.asarray(components["frame"], dtype=float)
        local_external = self._local_dof_transform(frame) @ element_displacements
        physical_external = local_external[PHYSICAL_EXTERNAL_INDICES]
        bubble = np.asarray(components["bubble_map"]) @ physical_external
        coordinates = np.concatenate((physical_external, bubble))
        strains = np.zeros((len(TRIANGLE_QUADRATURE), 8), dtype=float)
        resultants = np.zeros_like(strains)
        director_generalized_transform = self._director_generalized_transform()
        reference_surface_transform = _reference_surface_strain_transform(
            self.reference_surface_offset
        )
        for index, (r, s, _weight) in enumerate(TRIANGLE_QUADRATURE):
            physical_reference_strain = (
                director_generalized_transform
                @ _kinematic_matrix(
                    components["local_nodes"],
                    r,
                    s,
                    components["assumed_shear_samples"],
                )
                @ coordinates
            )
            strains[index] = (
                physical_reference_strain
                if self.reference_surface_offset == 0.0
                else reference_surface_transform @ physical_reference_strain
            )
            resultants[index] = np.asarray(components["constitutive"]) @ strains[index]
        recovered: Dict[str, Any] = {
            "recovery_scope": (
                "qualified_s3_local_and_global_physical"
                if return_global and self.shell_section is None
                else "qualified_s3_local_physical_only"
                if self.shell_section is None
                else "section_resultants_only"
            ),
            "physical_stress_available": self.shell_section is None,
            "membrane_resultant_order": SHELL_MEMBRANE_VOIGT_ORDER,
            "transverse_shear_resultant_order": SHELL_TRANSVERSE_SHEAR_ORDER,
            "membrane_strain": strains[:, :3],
            "curvature": strains[:, 3:6],
            "transverse_shear_strain": strains[:, 6:],
            "membrane_resultants": resultants[:, :3],
            "bending_resultants": resultants[:, 3:6],
            "transverse_shear_resultants": resultants[:, 6:],
            "bubble_rotations": bubble.copy(),
            "numerical_fields_excluded": True,
            "reference_surface_offset": float(self.reference_surface_offset),
            "reference_surface_offset_policy_id": REFERENCE_SURFACE_OFFSET_POLICY_ID,
            "section_origin_offset_from_reference": (
                self.material_mid_surface_offset_from_reference
            ),
            "physical_bottom_offset_from_reference": (
                self.material_surface_offset_from_reference(-1.0)
            ),
            "physical_top_offset_from_reference": (
                self.material_surface_offset_from_reference(1.0)
            ),
        }
        if self.shell_section is not None:
            recovered["generalized_stress_scope"] = "section_resultants_only"
        else:
            recovered.update(
                {
                    "bubble_linearization_policy": (
                        REFERENCE_ELASTIC_BUBBLE_LINEARIZATION_ID
                    ),
                    "through_thickness_stress_profile": (
                        HOMOGENEOUS_ELASTIC_STRESS_PROFILE_ID
                    ),
                }
            )
        if return_global:
            global_membrane = np.zeros((len(TRIANGLE_QUADRATURE), 3, 3), dtype=float)
            global_bending = np.zeros_like(global_membrane)
            global_shear = np.zeros((len(TRIANGLE_QUADRATURE), 3), dtype=float)
            for index in range(len(TRIANGLE_QUADRATURE)):
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
                global_bending[index] = (
                    float(self.director_polarity)
                    * (frame @ bending_tensor @ frame.T)
                )
                global_shear[index] = (
                    float(self.director_polarity)
                    * (
                        resultants[index, 6] * frame[:, 0]
                        + resultants[index, 7] * frame[:, 1]
                    )
                )
            recovered.update(
                {
                    "global_membrane_resultant_tensors": global_membrane,
                    "global_bending_resultant_tensors": global_bending,
                    "global_transverse_shear_resultants": global_shear,
                }
            )
        if self.shell_section is None:
            membrane_material, shear, _strain_transform, stress_to_local = (
                _shell_material_matrices(material, self._material_angle(components["frame"]))
            )
            membrane_stress = strains[:, :3] @ membrane_material.T
            moment = resultants[:, 3:6]
            bending_stress = 6.0 * moment / (self.thickness * self.thickness)
            transverse = strains[:, 6:] @ ((5.0 / 6.0) * shear).T
            recovered.update(
                {
                    "membrane_xx": membrane_stress[:, 0],
                    "membrane_yy": membrane_stress[:, 1],
                    "membrane_xy": membrane_stress[:, 2],
                    "bending_xx": bending_stress[:, 0],
                    "bending_yy": bending_stress[:, 1],
                    "bending_xy": bending_stress[:, 2],
                    "shear_xz": transverse[:, 0],
                    "shear_yz": transverse[:, 1],
                }
            )
            top = membrane_stress + bending_stress
            bottom = membrane_stress - bending_stress
            vm_top = np.sqrt(
                top[:, 0] ** 2
                - top[:, 0] * top[:, 1]
                + top[:, 1] ** 2
                + 3.0 * (top[:, 2] ** 2 + transverse[:, 0] ** 2 + transverse[:, 1] ** 2)
            )
            vm_bottom = np.sqrt(
                bottom[:, 0] ** 2
                - bottom[:, 0] * bottom[:, 1]
                + bottom[:, 1] ** 2
                + 3.0
                * (bottom[:, 2] ** 2 + transverse[:, 0] ** 2 + transverse[:, 1] ** 2)
            )
            recovered["von_mises"] = np.maximum(vm_top, vm_bottom)
            recovered["hill_utilization"] = np.zeros(len(TRIANGLE_QUADRATURE), dtype=float)
            hill_yield = getattr(material, "hill_yield", None)
            if hill_yield is not None:
                from .plasticity import hill48_plane_stress_equivalent_stress

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
                    local_tensors = np.zeros(
                        (len(TRIANGLE_QUADRATURE), 3, 3),
                        dtype=float,
                    )
                    local_tensors[:, 0, 0] = values[:, 0]
                    local_tensors[:, 1, 1] = values[:, 1]
                    local_tensors[:, 0, 1] = values[:, 2]
                    local_tensors[:, 1, 0] = values[:, 2]
                    owner_shear = float(self.director_polarity) * transverse
                    local_tensors[:, 0, 2] = owner_shear[:, 0]
                    local_tensors[:, 2, 0] = owner_shear[:, 0]
                    local_tensors[:, 1, 2] = owner_shear[:, 1]
                    local_tensors[:, 2, 1] = owner_shear[:, 1]
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
                    f"qualified S3 recovery produced non-finite field {name!r}"
                )
        return recovered

    def compute_stresses(
        self,
        mesh: Any,
        displacements: np.ndarray,
        material: Any,
        return_global: bool = False,
    ) -> Dict[str, Any]:
        """Recover production-admitted formulation-native physical fields."""

        return self._compute_stresses(
            mesh,
            displacements,
            material,
            return_global=return_global,
            enforce_positive_winding=True,
        )

    @staticmethod
    def _gap(name: str) -> NotImplementedError:
        return NotImplementedError(
            f"qualified S3 {name} is a PARITY_GAP and cannot use legacy TRI3 mechanics"
        )

    def compute_mass_matrix(self, mesh: Any, material: Any) -> np.ndarray:
        return np.asarray(self.compute_mass_components(mesh, material)["global"])

    def _compute_mass_components(
        self,
        mesh: Any,
        material: Any,
        *,
        enforce_positive_winding: bool,
    ) -> Dict[str, Any]:
        """Build the analytic nodal-plus-bubble mass and Guyan reduction."""

        stiffness = self._compute_stiffness_components(
            mesh,
            material,
            enforce_positive_winding=enforce_positive_winding,
        )
        local_nodes = np.asarray(stiffness["local_nodes"], dtype=float)
        _jacobian_matrix, _inverse, determinant = _jacobian(local_nodes)
        area = 0.5 * abs(float(determinant))
        corner, corner_bubble, bubble = _analytic_mass_moments(area)

        density = float(material.density)
        mass_per_area = (
            float(self.shell_section.mass_per_area)
            if self.shell_section is not None
            and self.shell_section.mass_per_area is not None
            else density * float(self.thickness)
        )
        section_rotary_inertia_per_area = (
            float(self.shell_section.rotary_inertia_per_area)
            if self.shell_section is not None
            and self.shell_section.rotary_inertia_per_area is not None
            else density * float(self.thickness) ** 3 / 12.0
        )
        physical_first_mass_moment_per_area = (
            -float(self.reference_surface_offset) * mass_per_area
        )
        owner_first_mass_moment_per_area = (
            float(self.director_polarity) * physical_first_mass_moment_per_area
        )
        rotary_inertia_per_area = (
            section_rotary_inertia_per_area
            + float(self.reference_surface_offset) ** 2 * mass_per_area
        )
        for label, value in (
            ("mass_per_area", mass_per_area),
            (
                "section_rotary_inertia_per_area",
                section_rotary_inertia_per_area,
            ),
            ("rotary_inertia_per_area", rotary_inertia_per_area),
        ):
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"qualified S3 {label} must be finite and nonnegative")

        full_local = np.zeros((20, 20), dtype=float)
        for component in range(3):
            indices = np.asarray(
                [6 * node + component for node in range(3)], dtype=np.intp
            )
            full_local[np.ix_(indices, indices)] = mass_per_area * corner

        rotation_moment = np.zeros((4, 4), dtype=float)
        rotation_moment[:3, :3] = corner
        rotation_moment[:3, 3] = corner_bubble
        rotation_moment[3, :3] = corner_bubble
        rotation_moment[3, 3] = bubble
        for component, bubble_index in ((3, 18), (4, 19)):
            indices = np.asarray(
                [6 * node + component for node in range(3)] + [bubble_index],
                dtype=np.intp,
            )
            full_local[np.ix_(indices, indices)] = (
                rotary_inertia_per_area * rotation_moment
            )

        if owner_first_mass_moment_per_area != 0.0:
            translation_rotation_moment = np.empty((3, 4), dtype=float)
            translation_rotation_moment[:, :3] = corner
            translation_rotation_moment[:, 3] = corner_bubble
            translation_u = np.asarray((0, 6, 12), dtype=np.intp)
            translation_v = np.asarray((1, 7, 13), dtype=np.intp)
            rotation_x = np.asarray((3, 9, 15, 18), dtype=np.intp)
            rotation_y = np.asarray((4, 10, 16, 19), dtype=np.intp)
            coupling_u_ry = (
                owner_first_mass_moment_per_area * translation_rotation_moment
            )
            coupling_v_rx = -coupling_u_ry
            full_local[np.ix_(translation_u, rotation_y)] = coupling_u_ry
            full_local[np.ix_(rotation_y, translation_u)] = coupling_u_ry.T
            full_local[np.ix_(translation_v, rotation_x)] = coupling_v_rx
            full_local[np.ix_(rotation_x, translation_v)] = coupling_v_rx.T

        full_local = 0.5 * (full_local + full_local.T)
        full_mass_eigenvalues = np.linalg.eigvalsh(full_local)
        full_mass_scale = max(
            float(np.max(np.abs(full_mass_eigenvalues))),
            1.0,
        )
        if float(full_mass_eigenvalues[0]) < (
            -4096.0 * full_local.shape[0] * np.finfo(float).eps * full_mass_scale
        ):
            raise ValueError(
                "qualified S3 offset nodal-plus-bubble mass is not positive semidefinite"
            )

        bubble_map_18 = np.zeros((2, 18), dtype=float)
        bubble_map_18[:, PHYSICAL_EXTERNAL_INDICES] = np.asarray(
            stiffness["bubble_map"], dtype=float
        )
        guyan = np.vstack((np.eye(18, dtype=float), bubble_map_18))
        condensed_local = guyan.T @ full_local @ guyan
        condensed_local = 0.5 * (condensed_local + condensed_local.T)
        transform = self._local_dof_transform(np.asarray(stiffness["frame"], dtype=float))
        global_mass = transform.T @ condensed_local @ transform
        global_mass = 0.5 * (global_mass + global_mass.T)
        self._mass_matrix = global_mass

        return {
            "area": area,
            "bubble_map_18": bubble_map_18,
            "condensed_local": condensed_local,
            "corner_bubble_moment": corner_bubble,
            "corner_moment": corner,
            "full_local": full_local,
            "global": global_mass,
            "guyan": guyan,
            "mass_moment_id": MASS_MOMENT_ID,
            "mass_per_area": mass_per_area,
            "physical_first_mass_moment_per_area": (
                physical_first_mass_moment_per_area
            ),
            "owner_first_mass_moment_per_area": owner_first_mass_moment_per_area,
            "section_rotary_inertia_per_area": section_rotary_inertia_per_area,
            "rotary_inertia_per_area": rotary_inertia_per_area,
            "reference_surface_offset": float(self.reference_surface_offset),
            "reference_surface_mass_shift_id": REFERENCE_SURFACE_MASS_SHIFT_ID,
            "bubble_moment": bubble,
            "full_rank": _matrix_rank(full_local),
            "full_minimum_eigenvalue": float(full_mass_eigenvalues[0]),
            "condensed_rank": _matrix_rank(condensed_local),
            "formulation_id": FORMULATION_ID,
            "zero_drill_inertia": True,
        }

    def compute_mass_components(self, mesh: Any, material: Any) -> Dict[str, Any]:
        """Return the admitted analytic mass and its Guyan audit blocks."""

        return self._compute_mass_components(
            mesh,
            material,
            enforce_positive_winding=True,
        )

    def dynamic_algebraic_directions(
        self, mesh: Any, material: Any
    ) -> np.ndarray:
        """Return the three global nodal rotations with exactly zero inertia."""

        components = self._compute_stiffness_components(
            mesh, material, enforce_positive_winding=True
        )
        local = np.zeros((18, 3), dtype=float)
        local[5, 0] = 1.0
        local[11, 1] = 1.0
        local[17, 2] = 1.0
        transform = self._local_dof_transform(
            np.asarray(components["frame"], dtype=float)
        )
        return np.asarray(transform.T @ local, dtype=float)

    def _compute_geometric_stiffness_components(
        self,
        mesh: Any,
        material: Any,
        state: Optional[Any],
        *,
        enforce_positive_winding: bool,
    ) -> Dict[str, Any]:
        """Build and condense the formulation-native initial-stress operator.

        The uncondensed 20-coordinate field contains the 18 nodal coordinates
        and the two hierarchical bubble rotations.  The physical Mindlin
        displacement through the thickness is

        ``[u + z*theta_y, v - z*theta_x, w]``.

        Membrane, bending, and second stress moments therefore act on the
        corresponding translation/director gradients.  The derivative of the
        bubble Schur complement is exactly ``G_b.T @ K_G @ G_b`` at the
        reference material tangent, with ``G_b`` equal to the frozen linear
        bubble equilibrium map.  This method therefore rejects material-
        history/current-tangent prestress.  Numerical PL/drill coordinates do
        not enter this physical operator.
        """

        point_count = len(TRIANGLE_QUADRATURE)
        if state is None:
            normalized_state: Dict[str, Any] = {}
        elif isinstance(state, Mapping):
            normalized_state = dict(state)
        else:
            raise ValueError(
                "qualified S3 geometric state must be a mapping or None"
            )

        membrane_compression_vectors = (
            "membrane_compression_at_gauss",
            "membrane_compression",
        )
        membrane_tension_vectors = (
            "membrane_forces_at_gauss",
            "membrane_forces",
            "membrane_resultants",
        )
        membrane_compression_scalars = (
            "membrane_compression_x",
            "membrane_compression_y",
            "membrane_compression_xy",
            "Nx_compression",
            "Ny_compression",
            "Nxy_compression",
        )
        membrane_tension_scalars = (
            "membrane_force_x",
            "membrane_force_y",
            "membrane_force_xy",
            "Nx",
            "Ny",
            "Nxy",
        )
        membrane_groups = (
            tuple(key for key in membrane_compression_vectors if key in normalized_state),
            tuple(key for key in membrane_tension_vectors if key in normalized_state),
            tuple(key for key in membrane_compression_scalars if key in normalized_state),
            tuple(key for key in membrane_tension_scalars if key in normalized_state),
        )
        compression_present = bool(membrane_groups[0] or membrane_groups[2])
        tension_present = bool(membrane_groups[1] or membrane_groups[3])
        if (
            (compression_present and tension_present)
            or len(membrane_groups[0]) > 1
            or len(membrane_groups[1]) > 1
        ):
            raise ValueError(
                "qualified S3 geometric state has ambiguous membrane resultant representations"
            )
        for alternatives in (
            ("membrane_compression_x", "Nx_compression"),
            ("membrane_compression_y", "Ny_compression"),
            ("membrane_compression_xy", "Nxy_compression"),
            ("membrane_force_x", "Nx"),
            ("membrane_force_y", "Ny"),
            ("membrane_force_xy", "Nxy"),
        ):
            if sum(key in normalized_state for key in alternatives) > 1:
                raise ValueError(
                    "qualified S3 geometric state has ambiguous membrane "
                    "component aliases"
                )

        bending_compression_keys = (
            "bending_compression_at_gauss",
            "bending_compression",
            "bending_compression_moments_at_gauss",
            "bending_compression_moments",
        )
        bending_tension_keys = (
            "bending_moments_at_gauss",
            "bending_moments",
            "bending_resultants",
        )
        if sum(
            key in normalized_state
            for key in bending_compression_keys + bending_tension_keys
        ) > 1:
            raise ValueError(
                "qualified S3 geometric state has ambiguous bending resultant representations"
            )
        second_moment_keys = (
            "stress_second_moment_at_gauss",
            "stress_second_moment",
            "membrane_compression_second_moment_at_gauss",
            "membrane_compression_second_moment",
        )
        if sum(key in normalized_state for key in second_moment_keys) > 1:
            raise ValueError(
                "qualified S3 geometric state has ambiguous stress second moment representations"
            )

        alias_pairs = (
            ("membrane_resultants", "membrane_forces_at_gauss"),
            ("bending_resultants", "bending_moments_at_gauss"),
        )
        for source_key, target_key in alias_pairs:
            if source_key not in normalized_state:
                continue
            if target_key in normalized_state:
                raise ValueError(
                    f"qualified S3 geometric state contains both {source_key} "
                    f"and {target_key}"
                )
            normalized_state[target_key] = normalized_state[source_key]

        at_gauss_keys = (
            "membrane_compression_at_gauss",
            "membrane_forces_at_gauss",
            "bending_compression_at_gauss",
            "bending_compression_moments_at_gauss",
            "bending_moments_at_gauss",
            "stress_second_moment_at_gauss",
            "membrane_compression_second_moment_at_gauss",
        )
        uniform_or_gauss_keys = (
            "membrane_compression",
            "membrane_forces",
            "bending_compression",
            "bending_compression_moments",
            "bending_moments",
            "stress_second_moment",
            "membrane_compression_second_moment",
        )
        for key in at_gauss_keys:
            if key not in normalized_state:
                continue
            values = np.asarray(normalized_state[key], dtype=float)
            if values.shape != (point_count, 3) or np.any(~np.isfinite(values)):
                raise ValueError(
                    f"qualified S3 geometric {key} must be a finite "
                    f"({point_count}, 3) array"
                )
        for key in uniform_or_gauss_keys:
            if key not in normalized_state:
                continue
            values = np.asarray(normalized_state[key], dtype=float)
            if values.shape not in {(3,), (point_count, 3)} or np.any(
                ~np.isfinite(values)
            ):
                raise ValueError(
                    f"qualified S3 geometric {key} must be a finite (3,) or "
                    f"({point_count}, 3) array"
                )
        scalar_keys = (
            "membrane_compression_x",
            "membrane_compression_y",
            "membrane_compression_xy",
            "Nx_compression",
            "Ny_compression",
            "Nxy_compression",
            "membrane_force_x",
            "membrane_force_y",
            "membrane_force_xy",
            "Nx",
            "Ny",
            "Nxy",
        )
        for key in scalar_keys:
            if key not in normalized_state:
                continue
            values = np.asarray(normalized_state[key], dtype=float)
            if values.shape != () or not math.isfinite(float(values)):
                raise ValueError(
                    f"qualified S3 geometric {key} must be a finite scalar"
                )
        summary_policy = normalized_state.get("resultant_summary_policy")
        if (
            summary_policy is not None
            and summary_policy != RESULTANT_SUMMARY_POLICY_ID
        ):
            raise ValueError(
                "qualified S3 geometric resultant_summary_policy is incompatible"
            )

        def require_consistent_scalar_summary(
            vector_keys: Sequence[str],
            scalar_alternatives: Sequence[Sequence[str]],
        ) -> None:
            vector_key = next(
                (key for key in vector_keys if key in normalized_state),
                None,
            )
            if vector_key is None:
                return
            vector = np.asarray(normalized_state[vector_key], dtype=float)
            summary = (
                vector
                if vector.ndim == 1
                else np.average(
                    vector,
                    axis=0,
                    weights=np.asarray(self.gauss_weights, dtype=float),
                )
            )
            for component, alternatives in enumerate(scalar_alternatives):
                scalar_key = next(
                    (key for key in alternatives if key in normalized_state),
                    None,
                )
                if scalar_key is None:
                    continue
                scalar = float(normalized_state[scalar_key])
                expected = float(summary[component])
                tolerance = (
                    64.0
                    * np.finfo(float).eps
                    * max(abs(scalar), abs(expected), 1.0)
                )
                if abs(scalar - expected) > tolerance:
                    raise ValueError(
                        "qualified S3 geometric state has an inconsistent "
                        f"{scalar_key} summary for {vector_key}"
                    )

        require_consistent_scalar_summary(
            membrane_compression_vectors,
            (
                ("membrane_compression_x", "Nx_compression"),
                ("membrane_compression_y", "Ny_compression"),
                ("membrane_compression_xy", "Nxy_compression"),
            ),
        )
        require_consistent_scalar_summary(
            membrane_tension_vectors,
            (
                ("membrane_force_x", "Nx"),
                ("membrane_force_y", "Ny"),
                ("membrane_force_xy", "Nxy"),
            ),
        )

        membrane_compression = self._membrane_compression_samples(
            normalized_state,
            point_count,
        )
        bending_compression = self._bending_compression_samples(
            normalized_state,
            point_count,
        )
        explicit_second_moment = any(
            key in normalized_state for key in second_moment_keys
        )
        stress_profile = normalized_state.get("through_thickness_stress_profile")
        if (
            stress_profile is not None
            and stress_profile != HOMOGENEOUS_ELASTIC_STRESS_PROFILE_ID
        ):
            raise ValueError(
                "qualified S3 geometric through_thickness_stress_profile is incompatible"
            )
        bubble_linearization = normalized_state.get(
            "bubble_linearization_policy"
        )
        if (
            bubble_linearization is not None
            and bubble_linearization
            != REFERENCE_ELASTIC_BUBBLE_LINEARIZATION_ID
        ):
            raise ValueError(
                "qualified S3 geometric bubble_linearization_policy is incompatible"
            )
        stress_second_moment = self._stress_second_moment_samples(
            normalized_state,
            point_count,
            membrane_compression,
            self.thickness,
        )
        for label, values in (
            ("membrane resultants", membrane_compression),
            ("bending resultants", bending_compression),
            ("stress second moments", stress_second_moment),
        ):
            if values.shape != (point_count, 3) or np.any(~np.isfinite(values)):
                raise ValueError(
                    f"qualified S3 geometric {label} must be finite at all seven points"
                )
        if (
            (
                self.shell_section is not None
                or stress_profile != HOMOGENEOUS_ELASTIC_STRESS_PROFILE_ID
            )
            and not explicit_second_moment
            and (
                np.any(membrane_compression)
                or np.any(bending_compression)
            )
        ):
            source = (
                "generalized shell sections"
                if self.shell_section is not None
                else "resultants without homogeneous-elastic provenance"
            )
            raise ValueError(
                "qualified S3 geometric "
                f"{source} require an explicit stress_second_moment; "
                "N and M do not determine the through-thickness second moment H"
            )
        nonzero_initial_stress = bool(
            np.any(membrane_compression)
            or np.any(bending_compression)
            or np.any(stress_second_moment)
        )
        if (
            nonzero_initial_stress
            and bubble_linearization
            != REFERENCE_ELASTIC_BUBBLE_LINEARIZATION_ID
        ):
            raise ValueError(
                "qualified S3 geometric nonzero prestress requires "
                "bubble_linearization_policy="
                f"{REFERENCE_ELASTIC_BUBBLE_LINEARIZATION_ID}; material-history "
                "or current-tangent bubble condensation remains a PARITY_GAP"
            )

        offset = float(self.reference_surface_offset)
        bending_compression_about_reference = (
            bending_compression
            if offset == 0.0
            else bending_compression - offset * membrane_compression
        )
        stress_second_moment_about_reference = (
            stress_second_moment
            if offset == 0.0
            else (
                stress_second_moment
                - 2.0 * offset * bending_compression
                + offset * offset * membrane_compression
            )
        )

        stiffness = self._compute_stiffness_components(
            mesh,
            material,
            enforce_positive_winding=enforce_positive_winding,
        )
        local_nodes = np.asarray(stiffness["local_nodes"], dtype=float)
        _jacobian_matrix, inverse, determinant = _jacobian(local_nodes)
        full_local = np.zeros((20, 20), dtype=float)
        for point_index, (r, s, weight) in enumerate(TRIANGLE_QUADRATURE):
            (
                _shape,
                derivative_r,
                derivative_s,
                _bubble,
                bubble_r,
                bubble_s,
            ) = _reference_fields(r, s)
            derivative_x = (
                inverse[0, 0] * derivative_r
                + inverse[0, 1] * derivative_s
            )
            derivative_y = (
                inverse[1, 0] * derivative_r
                + inverse[1, 1] * derivative_s
            )
            bubble_x = inverse[0, 0] * bubble_r + inverse[0, 1] * bubble_s
            bubble_y = inverse[1, 0] * bubble_r + inverse[1, 1] * bubble_s

            membrane = membrane_compression[point_index]
            bending = bending_compression_about_reference[point_index]
            second = stress_second_moment_about_reference[point_index]
            membrane_matrix = np.asarray(
                ((membrane[0], membrane[2]), (membrane[2], membrane[1])),
                dtype=float,
            )
            bending_matrix = np.asarray(
                ((bending[0], bending[2]), (bending[2], bending[1])),
                dtype=float,
            )
            second_matrix = np.asarray(
                ((second[0], second[2]), (second[2], second[1])),
                dtype=float,
            )

            translation_gradients = []
            point_operator = np.zeros((20, 20), dtype=float)
            for component in range(3):
                gradient = np.zeros((2, 20), dtype=float)
                gradient[0, component:18:6] = derivative_x
                gradient[1, component:18:6] = derivative_y
                translation_gradients.append(gradient)
                point_operator += gradient.T @ membrane_matrix @ gradient

            rotation_x_gradient = np.zeros((2, 20), dtype=float)
            rotation_y_gradient = np.zeros((2, 20), dtype=float)
            rotation_x_gradient[0, 3:18:6] = derivative_x
            rotation_x_gradient[1, 3:18:6] = derivative_y
            rotation_x_gradient[:, 18] = (bubble_x, bubble_y)
            rotation_y_gradient[0, 4:18:6] = derivative_x
            rotation_y_gradient[1, 4:18:6] = derivative_y
            rotation_y_gradient[:, 19] = (bubble_x, bubble_y)
            rotation_x_gradient *= float(self.director_polarity)
            rotation_y_gradient *= float(self.director_polarity)
            point_operator += (
                rotation_x_gradient.T
                @ second_matrix
                @ rotation_x_gradient
            )
            point_operator += (
                rotation_y_gradient.T
                @ second_matrix
                @ rotation_y_gradient
            )
            coupling_u_ry = (
                translation_gradients[0].T
                @ bending_matrix
                @ rotation_y_gradient
            )
            coupling_v_rx = (
                translation_gradients[1].T
                @ bending_matrix
                @ rotation_x_gradient
            )
            point_operator += coupling_u_ry + coupling_u_ry.T
            point_operator -= coupling_v_rx + coupling_v_rx.T
            full_local += abs(determinant) * float(weight) * point_operator
        full_local = 0.5 * (full_local + full_local.T)
        bubble_map_18 = np.zeros((2, 18), dtype=float)
        bubble_map_18[:, PHYSICAL_EXTERNAL_INDICES] = np.asarray(
            stiffness["bubble_map"],
            dtype=float,
        )
        bubble_schur_map = np.vstack((np.eye(18, dtype=float), bubble_map_18))
        condensed_local = bubble_schur_map.T @ full_local @ bubble_schur_map
        condensed_local = 0.5 * (condensed_local + condensed_local.T)
        transform = self._local_dof_transform(
            np.asarray(stiffness["frame"], dtype=float)
        )
        global_operator = transform.T @ condensed_local @ transform
        global_operator = 0.5 * (global_operator + global_operator.T)
        return {
            "bubble_schur_map": bubble_schur_map,
            "condensed_local": condensed_local,
            "formulation_id": FORMULATION_ID,
            "frame": np.asarray(stiffness["frame"], dtype=float),
            "full_local": full_local,
            "global": global_operator,
            "membrane_compression": membrane_compression.copy(),
            "bending_compression": bending_compression.copy(),
            "bending_compression_about_reference_surface": (
                bending_compression_about_reference.copy()
            ),
            "bubble_linearization_policy": (
                REFERENCE_ELASTIC_BUBBLE_LINEARIZATION_ID
                if nonzero_initial_stress
                else None
            ),
            "stress_second_moment": stress_second_moment.copy(),
            "stress_second_moment_about_reference_surface": (
                stress_second_moment_about_reference.copy()
            ),
            "reference_surface_offset": offset,
            "reference_surface_offset_policy_id": REFERENCE_SURFACE_OFFSET_POLICY_ID,
            "second_moment_authority": (
                None
                if not nonzero_initial_stress
                else (
                    "EXPLICIT_H"
                    if explicit_second_moment
                    else HOMOGENEOUS_ELASTIC_STRESS_PROFILE_ID
                )
            ),
            "numerical_fields_excluded": True,
            "policy_id": GEOMETRIC_STIFFNESS_POLICY_ID,
            "director_polarity": int(self.director_polarity),
            "bending_resultant_convention": "physical_director_first_moment",
        }

    def compute_geometric_stiffness_components(
        self,
        mesh: Any,
        material: Any,
        state: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Return auditable admitted initial-stress blocks and condensation."""

        return self._compute_geometric_stiffness_components(
            mesh,
            material,
            state,
            enforce_positive_winding=True,
        )

    def compute_geometric_stiffness_matrix(
        self, mesh: Any, material: Any, state: Optional[Any] = None
    ) -> np.ndarray:
        return np.asarray(
            self.compute_geometric_stiffness_components(
                mesh,
                material,
                state,
            )["global"],
            dtype=float,
        )

    def init_model_bound_nonlinear_state(
        self,
        mesh: Any,
        material: Any,
        num_layers: int,
        *,
        initial_fields: Optional[Mapping[str, Any]] = None,
        initial_field_provenance: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a complete qualified state bound to the current model."""

        if self.shell_section is not None:
            if isinstance(num_layers, (bool, np.bool_)) or not isinstance(
                num_layers, (int, np.integer)
            ) or int(num_layers) <= 0:
                raise S3CommittedStateError(
                    "generalized S3 solver num_layers parameter must be a "
                    "positive integer"
                )
            (
                coordinates,
                frame,
                element_descriptor,
                constitutive,
                drilling_scale,
            ) = self._model_bound_generalized_nonlinear_context(mesh, material)
            return initialize_zero_committed_s3_generalized_state(
                element_id=self.element_id,
                node_ids=self.node_ids,
                reference_coordinates=coordinates,
                reference_frame=frame,
                element_descriptor=element_descriptor,
                constitutive=constitutive,
                drilling_scale=drilling_scale,
                initial_fields=(
                    self._initial_fields_in_physical_director_convention(
                        initial_fields
                    )
                ),
                initial_field_provenance=initial_field_provenance,
            )

        (
            coordinates,
            frame,
            element_descriptor,
            material_descriptor,
        ) = self._model_bound_nonlinear_context(mesh, material)
        return initialize_zero_committed_s3_state(
            element_id=self.element_id,
            node_ids=self.node_ids,
            reference_coordinates=coordinates,
            reference_frame=frame,
            element_descriptor=element_descriptor,
            material_descriptor=material_descriptor,
            num_layers=num_layers,
            material_symmetry=str(material_descriptor["material_symmetry"]),
            equivalent_stress_measure=str(
                material_descriptor["equivalent_stress_measure"]
            ),
            initial_fields=self._initial_fields_in_physical_director_convention(
                initial_fields
            ),
            initial_field_provenance=initial_field_provenance,
        )

    def native_reference_directors(self, mesh: Any) -> np.ndarray:
        """Return element-owned corner directors for node-shared rotations."""

        coordinates = self.get_node_coordinates(mesh)
        frame, _local, quality = triangle_frame(
            coordinates,
            self.reference_normal,
        )
        # This accessor transports element identity through D3 numbering; it
        # is not the production mesh-admission gate.  Odd permutations retain
        # the same owner normal and physical director.
        _require_admitted_quality(quality, enforce_positive_winding=False)
        return np.repeat(
            (float(self.director_polarity) * frame[:, 2])[None, :],
            3,
            axis=0,
        )

    def sheet_area_orientation_sign(self, mesh: Any) -> float:
        """Orient pressure by the sheet owner, independently of D3/polarity."""

        coordinates = np.asarray(
            self.get_node_coordinates(mesh), dtype=float
        ).reshape(3, 3)
        raw = np.cross(
            coordinates[1] - coordinates[0],
            coordinates[2] - coordinates[0],
        )
        signed = float(raw @ np.asarray(self.reference_normal, dtype=float))
        scale = float(np.linalg.norm(raw))
        if (
            not math.isfinite(signed)
            or not math.isfinite(scale)
            or scale <= np.finfo(float).tiny
            or abs(signed) <= MINIMUM_OWNER_NORMAL_ALIGNMENT * scale
        ):
            raise ValueError(
                "qualified S3 sheet area orientation is unresolved against "
                "the authoritative owner normal"
            )
        return 1.0 if signed > 0.0 else -1.0

    def _model_bound_nonlinear_context(
        self,
        mesh: Any,
        material: Any,
    ) -> tuple[np.ndarray, np.ndarray, Dict[str, Any], Dict[str, Any]]:
        if self.shell_section is not None:
            raise self._gap("material_nonlinearity")
        coordinates = self.get_node_coordinates(mesh)
        frame, _local, quality = triangle_frame(
            coordinates,
            self.reference_normal,
        )
        _require_admitted_quality(quality, enforce_positive_winding=True)
        element_descriptor = build_element_configuration_descriptor(
            thickness=self.thickness,
            reference_surface_offset=self.reference_surface_offset,
            reference_normal=self.reference_normal,
            director_polarity=self.director_polarity,
            material_direction=self.material_direction,
            material_angle_deg=self.material_angle_deg,
            shell_section=None,
        )
        material_descriptor = resolved_material_descriptor(material)
        return coordinates, frame, element_descriptor, material_descriptor

    def _model_bound_generalized_nonlinear_context(
        self,
        mesh: Any,
        material: Any,
    ) -> tuple[np.ndarray, np.ndarray, Dict[str, Any], np.ndarray, float]:
        if self.shell_section is None:
            raise S3CommittedStateError(
                "generalized qualified S3 state requires a shell section"
            )
        coordinates = self.get_node_coordinates(mesh)
        frame, _local, quality = triangle_frame(
            coordinates,
            self.reference_normal,
        )
        _require_admitted_quality(quality, enforce_positive_winding=True)
        element_descriptor = build_generalized_element_configuration_descriptor(
            thickness=self.thickness,
            reference_surface_offset=self.reference_surface_offset,
            reference_normal=self.reference_normal,
            director_polarity=self.director_polarity,
            material_direction=self.material_direction,
            material_angle_deg=self.material_angle_deg,
            shell_section=self.shell_section,
        )
        constitutive, membrane = self._constitutive(material, frame)
        drilling_scale = invariant_drilling_scale(membrane)
        return (
            coordinates,
            frame,
            element_descriptor,
            constitutive,
            drilling_scale,
        )

    def validate_model_bound_nonlinear_state(
        self,
        mesh: Any,
        material: Any,
        state: Mapping[str, Any],
        num_layers: int,
        *,
        expected_committed_total_u: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Validate a committed state against current element/model identity."""

        if self.shell_section is not None:
            if isinstance(num_layers, (bool, np.bool_)) or not isinstance(
                num_layers, (int, np.integer)
            ) or int(num_layers) <= 0:
                raise S3CommittedStateError(
                    "generalized S3 solver num_layers parameter must be a "
                    "positive integer"
                )
            (
                coordinates,
                frame,
                element_descriptor,
                constitutive,
                drilling_scale,
            ) = self._model_bound_generalized_nonlinear_context(mesh, material)
            initial_fields = {
                name: state[name]
                for name in INITIAL_FIELD_NAMES
                if isinstance(state, Mapping) and name in state
            }
            provenance = (
                state.get("initial_field_provenance", {})
                if isinstance(state, Mapping)
                else {}
            )
            identity = build_generalized_state_identity(
                element_id=self.element_id,
                node_ids=self.node_ids,
                reference_coordinates=coordinates,
                reference_frame=frame,
                element_descriptor=element_descriptor,
                initial_fields=initial_fields,
                initial_field_provenance=provenance,
            )
            area = 0.5 * float(
                np.linalg.norm(
                    np.cross(
                        coordinates[1] - coordinates[0],
                        coordinates[2] - coordinates[0],
                    )
                )
            )
            return validate_committed_s3_generalized_state(
                state,
                expected_identity=identity,
                expected_constitutive=constitutive,
                expected_drilling_scale=drilling_scale,
                expected_reference_area=area,
                expected_committed_total_u=expected_committed_total_u,
            )

        (
            coordinates,
            frame,
            element_descriptor,
            material_descriptor,
        ) = self._model_bound_nonlinear_context(mesh, material)
        initial_fields = {
            name: state[name]
            for name in INITIAL_FIELD_NAMES
            if isinstance(state, Mapping) and name in state
        }
        provenance = (
            state.get("initial_field_provenance", {})
            if isinstance(state, Mapping)
            else {}
        )
        identity = build_state_identity(
            element_id=self.element_id,
            node_ids=self.node_ids,
            reference_coordinates=coordinates,
            reference_frame=frame,
            element_descriptor=element_descriptor,
            material_descriptor=material_descriptor,
            num_layers=num_layers,
            material_symmetry=str(material_descriptor["material_symmetry"]),
            equivalent_stress_measure=str(
                material_descriptor["equivalent_stress_measure"]
            ),
            initial_fields=initial_fields,
            initial_field_provenance=provenance,
        )
        return validate_committed_s3_state(
            state,
            expected_identity=identity,
            expected_num_layers=num_layers,
            expected_committed_total_u=expected_committed_total_u,
        )

    def init_nonlinear_state(
        self,
        num_layers: int,
        *,
        mesh: Optional[Any] = None,
        material: Optional[Any] = None,
        initial_fields: Optional[Mapping[str, Any]] = None,
        initial_field_provenance: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        if mesh is None or material is None:
            raise ValueError(
                "qualified S3 nonlinear state is model-bound; provide mesh and material"
            )
        return self.init_model_bound_nonlinear_state(
            mesh,
            material,
            num_layers,
            initial_fields=initial_fields,
            initial_field_provenance=initial_field_provenance,
        )

    def _validated_native_nonlinear_trial(
        self,
        mesh: Any,
        material: Any,
        u_elem: Any,
        state: Optional[Mapping[str, Any]],
        num_layers: int,
        native_rotation_trial: NativeElementRotationView,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
        """Bind one direct element call to the complete node-shared trial.

        Every redundant copy is compared bit-for-bit.  This makes the public
        additive coordinate vector a checked transport carrier only; the
        physical corner rotations and directors remain owned by the solver's
        multiplicative transaction.
        """

        if not isinstance(native_rotation_trial, NativeElementRotationView):
            raise TypeError(
                "qualified S3 nonlinear response requires "
                "NativeElementRotationView"
            )
        if native_rotation_trial.trial_serial is None:
            raise ValueError(
                "qualified S3 nonlinear response requires an active native "
                "rotation trial"
            )
        if native_rotation_trial.element_id != self.element_id:
            raise ValueError(
                "qualified S3 native rotation view belongs to another element"
            )
        if tuple(native_rotation_trial.node_ids) != tuple(self.node_ids):
            raise ValueError(
                "qualified S3 native rotation view has incompatible connectivity"
            )

        total_u = np.asarray(u_elem, dtype=np.float64)
        if total_u.shape != (18,) or not np.all(np.isfinite(total_u)):
            raise ValueError(
                "qualified S3 nonlinear displacement must contain 18 finite values"
            )
        total_u = np.array(total_u, dtype=np.float64, order="C", copy=True)
        if self.shell_section is None:
            (
                reference_coordinates,
                reference_frame,
                _element_descriptor,
                _material_descriptor,
            ) = self._model_bound_nonlinear_context(mesh, material)
        else:
            (
                reference_coordinates,
                reference_frame,
                _element_descriptor,
                _constitutive,
                _drilling_scale,
            ) = self._model_bound_generalized_nonlinear_context(mesh, material)
        reference_coordinates = np.asarray(
            reference_coordinates, dtype=np.float64
        ).reshape(3, 3)
        reference_frame = np.asarray(reference_frame, dtype=np.float64).reshape(3, 3)
        expected_reference_directors = np.repeat(
            (
                float(self.director_polarity)
                * reference_frame[:, 2]
            )[None, :],
            3,
            axis=0,
        )

        view_shapes = {
            "committed_coordinates": (3, 3),
            "trial_coordinates": (3, 3),
            "coordinate_increment": (3, 3),
            "committed_rotation_coordinates": (3, 3),
            "trial_rotation_coordinates": (3, 3),
            "rotation_coordinate_increment": (3, 3),
            "committed_rotation_matrices": (3, 3, 3),
            "trial_rotation_matrices": (3, 3, 3),
            "reference_directors": (3, 3),
            "committed_directors": (3, 3),
            "trial_directors": (3, 3),
        }
        view_arrays: Dict[str, np.ndarray] = {}
        for name, shape in view_shapes.items():
            made = np.asarray(
                getattr(native_rotation_trial, name), dtype=np.float64
            )
            if made.shape != shape or not np.all(np.isfinite(made)):
                raise ValueError(
                    f"qualified S3 native rotation view {name} is incompatible"
                )
            view_arrays[name] = made
        if not np.array_equal(
            view_arrays["reference_directors"], expected_reference_directors
        ):
            raise ValueError(
                "qualified S3 native reference directors disagree with the model"
            )
        if not np.array_equal(
            view_arrays["coordinate_increment"],
            view_arrays["trial_coordinates"]
            - view_arrays["committed_coordinates"],
        ) or not np.array_equal(
            view_arrays["rotation_coordinate_increment"],
            view_arrays["trial_rotation_coordinates"]
            - view_arrays["committed_rotation_coordinates"],
        ):
            raise ValueError(
                "qualified S3 native rotation view carries inconsistent increments"
            )
        expected_committed_directors = np.einsum(
            "nij,nj->ni",
            view_arrays["committed_rotation_matrices"],
            view_arrays["reference_directors"],
        )
        expected_trial_directors = np.einsum(
            "nij,nj->ni",
            view_arrays["trial_rotation_matrices"],
            view_arrays["reference_directors"],
        )
        if not np.array_equal(
            view_arrays["committed_directors"], expected_committed_directors
        ) or not np.array_equal(
            view_arrays["trial_directors"], expected_trial_directors
        ):
            raise ValueError(
                "qualified S3 native directors contradict Q/reference-director history"
            )
        for node in range(3):
            expected_trial_q = (
                rotation_exponential(
                    view_arrays["rotation_coordinate_increment"][node]
                )
                @ view_arrays["committed_rotation_matrices"][node]
            )
            if not np.array_equal(
                view_arrays["trial_rotation_matrices"][node], expected_trial_q
            ):
                raise ValueError(
                    "qualified S3 native trial Q contradicts its shared SO(3) "
                    "increment"
                )

        total_by_node = total_u.reshape(3, 6)
        if not np.array_equal(
            total_by_node[:, 3:6], view_arrays["trial_rotation_coordinates"]
        ) or not np.array_equal(
            reference_coordinates + total_by_node[:, :3],
            view_arrays["trial_coordinates"],
        ):
            raise ValueError(
                "qualified S3 trial element displacement disagrees with the "
                "solver-owned native trial"
            )

        if state is None:
            identity_stack = np.repeat(
                np.eye(3, dtype=np.float64)[None, :, :], 3, axis=0
            )
            unambiguous_zero = bool(
                native_rotation_trial.generation == 0
                and np.array_equal(
                    view_arrays["committed_coordinates"], reference_coordinates
                )
                and np.array_equal(
                    view_arrays["committed_rotation_coordinates"],
                    np.zeros((3, 3), dtype=np.float64),
                )
                and np.array_equal(
                    view_arrays["committed_rotation_matrices"], identity_stack
                )
                and np.array_equal(
                    view_arrays["committed_directors"],
                    expected_reference_directors,
                )
            )
            if not unambiguous_zero:
                raise S3CommittedStateError(
                    "qualified S3 model-bound state may be initialized only from an "
                    "unambiguous zero committed configuration"
                )
            committed = self.init_model_bound_nonlinear_state(
                mesh, material, num_layers
            )
        else:
            if not isinstance(state, Mapping):
                raise S3CommittedStateError(
                    "qualified S3 committed state must be a mapping"
                )
            committed = self.validate_model_bound_nonlinear_state(
                mesh, material, state, num_layers
            )

        committed_u = np.asarray(
            committed["committed_total_u"], dtype=np.float64
        ).reshape(18)
        committed_by_node = committed_u.reshape(3, 6)
        if not np.array_equal(
            committed_by_node[:, 3:6],
            view_arrays["committed_rotation_coordinates"],
        ) or not np.array_equal(
            reference_coordinates + committed_by_node[:, :3],
            view_arrays["committed_coordinates"],
        ):
            raise S3CommittedStateError(
                "qualified S3 committed element displacement disagrees with the "
                "solver-owned native history"
            )
        if not np.array_equal(
            total_by_node[:, 3:6] - committed_by_node[:, 3:6],
            view_arrays["rotation_coordinate_increment"],
        ):
            raise S3CommittedStateError(
                "qualified S3 additive and native rotational increments disagree"
            )
        if not np.array_equal(
            committed["reference_corner_directors"],
            view_arrays["reference_directors"],
        ) or not np.array_equal(
            committed["committed_nodal_rotation_matrices"],
            view_arrays["committed_rotation_matrices"],
        ):
            raise S3CommittedStateError(
                "qualified S3 committed Q/reference-director identity disagrees "
                "with the solver-owned native history"
            )
        committed_triads = np.asarray(
            committed["committed_director_triads"], dtype=np.float64
        ).reshape(4, 3, 3)
        for node in range(3):
            expected_triad = reconstruct_director_triad(
                view_arrays["committed_directors"][node]
            )
            if not np.array_equal(committed_triads[node], expected_triad):
                raise S3CommittedStateError(
                    "qualified S3 committed corner triad disagrees with shared Q"
                )
        return (
            total_u,
            reference_coordinates,
            reference_frame,
            committed,
        )

    def compute_nonlinear_response(
        self,
        mesh: Any,
        material: Any,
        u_elem: Any,
        state: Optional[Mapping[str, Any]] = None,
        num_layers: int = 5,
        tangent: bool = True,
        *,
        native_rotation_trial: NativeElementRotationView,
        _return_tangent_components: bool = False,
    ) -> Any:
        """Return one formulation-native layered or stateless-section trial."""

        (
            total_u,
            reference_coordinates,
            reference_frame,
            committed,
        ) = self._validated_native_nonlinear_trial(
            mesh,
            material,
            u_elem,
            state,
            num_layers,
            native_rotation_trial,
        )
        external_increment = np.empty(18, dtype=np.float64)
        external_by_node = external_increment.reshape(3, 6)
        external_by_node[:, :3] = native_rotation_trial.coordinate_increment
        external_by_node[:, 3:6] = (
            native_rotation_trial.rotation_coordinate_increment
        )
        committed_triads = np.asarray(
            committed["committed_director_triads"], dtype=np.float64
        ).reshape(4, 3, 3)
        if self.shell_section is None:
            material_angle = self._material_angle(reference_frame)

            def physical_builder(
                increment20: np.ndarray,
            ) -> tuple[
                np.ndarray,
                np.ndarray,
                Dict[str, Any],
                Dict[str, np.ndarray],
            ]:
                return _native_layered_uncondensed_response_components(
                    native_rotation_trial.committed_coordinates,
                    committed_triads,
                    increment20,
                    reference_coordinates,
                    reference_frame,
                    material,
                    material_angle,
                    float(self.thickness),
                    committed,
                    num_layers,
                    float(self.reference_surface_offset),
                    native_rotation_trial=native_rotation_trial,
                )

        else:
            constitutive, _membrane = self._constitutive(
                material, reference_frame
            )

            def physical_builder(
                increment20: np.ndarray,
            ) -> tuple[
                np.ndarray,
                np.ndarray,
                Dict[str, Any],
                Dict[str, np.ndarray],
            ]:
                return _native_generalized_uncondensed_response_components(
                    native_rotation_trial.committed_coordinates,
                    committed_triads,
                    increment20,
                    reference_coordinates,
                    reference_frame,
                    constitutive,
                    np.asarray(
                        committed["station_generalized_strain"],
                        dtype=np.float64,
                    ),
                    float(self.reference_surface_offset),
                    np.asarray(
                        committed["initial_generalized_prestrain"],
                        dtype=np.float64,
                    ),
                    np.asarray(
                        committed["initial_generalized_resultant"],
                        dtype=np.float64,
                    ),
                    native_rotation_trial=native_rotation_trial,
                )

        (
            physical_force,
            physical_tangent,
            physical_trial,
            bubble_metadata,
        ) = _solve_native_bubble_equilibrium(
            external_increment,
            np.asarray(
                committed["bubble_rotation_last_increment"], dtype=np.float64
            ),
            physical_builder,
        )
        bubble_increment = np.asarray(
            bubble_metadata["bubble_increment"], dtype=np.float64
        ).reshape(2)
        physical_material_tangent = np.asarray(
            bubble_metadata["condensed_material_tangent"],
            dtype=np.float64,
        )
        physical_geometric_tangent = np.asarray(
            bubble_metadata["condensed_geometric_tangent"],
            dtype=np.float64,
        )
        physical_decomposition_error = float(
            np.linalg.norm(
                np.asarray(physical_tangent, dtype=np.float64)
                - physical_material_tangent
                - physical_geometric_tangent,
                ord="fro",
            )
            / max(
                float(
                    np.linalg.norm(
                        np.asarray(physical_tangent, dtype=np.float64),
                        ord="fro",
                    )
                ),
                1.0,
            )
        )
        if physical_decomposition_error > 256.0 * np.finfo(np.float64).eps:
            raise ValueError(
                "qualified S3 condensed physical tangent decomposition is inconsistent"
            )
        full_increment = np.concatenate((external_increment, bubble_increment))

        _section, membrane = self._constitutive(material, reference_frame)
        drilling_scale = invariant_drilling_scale(membrane)
        pl_trial = _objective_pl_energy_response(
            reference_coordinates,
            reference_frame,
            native_rotation_trial.committed_coordinates,
            native_rotation_trial.committed_rotation_matrices,
            external_increment,
            np.asarray(committed["committed_pl_twist"], dtype=np.float64),
            drilling_scale,
            native_rotation_trial=native_rotation_trial,
        )
        pl_force = np.asarray(pl_trial["force"], dtype=np.float64).reshape(18)
        pl_tangent = np.asarray(pl_trial["tangent"], dtype=np.float64).reshape(
            18, 18
        )
        pl_constraint = np.asarray(
            pl_trial["constraint"], dtype=np.float64
        ).reshape(3)
        pl_multiplier = np.asarray(
            pl_trial["multiplier"], dtype=np.float64
        ).reshape(3)
        pl_gram = np.asarray(pl_trial["gram"], dtype=np.float64).reshape(3, 3)
        expected_multiplier = drilling_scale * pl_constraint
        expected_mixed_force = np.asarray(
            [
                sum(
                    float(pl_gram[row, column])
                    * float(expected_multiplier[column])
                    for column in range(3)
                )
                for row in range(3)
            ],
            dtype=np.float64,
        )
        mixed_force = np.asarray(
            pl_trial["mixed_constraint_force"], dtype=np.float64
        ).reshape(3)
        expected_pl_energy = sum(
            0.5 * float(pl_constraint[row]) * float(expected_mixed_force[row])
            for row in range(3)
        )
        canonical_turns = np.asarray(
            [
                math.ceil((float(value) - math.pi) / (2.0 * math.pi))
                for value in pl_constraint
            ],
            dtype=np.int64,
        )
        if (
            not np.array_equal(pl_multiplier, expected_multiplier)
            or not np.array_equal(mixed_force, expected_mixed_force)
            or float(pl_trial["energy"]) != float(expected_pl_energy)
            or not np.array_equal(pl_trial["turn_count"], canonical_turns)
        ):
            raise ValueError(
                "qualified S3 objective PL multiplier, mixed force, energy, or "
                "phase identity is inconsistent"
            )
        total_force = np.asarray(physical_force, dtype=np.float64) + pl_force
        material_tangent = (
            np.asarray(physical_material_tangent, dtype=np.float64)
            + pl_tangent
        )
        geometric_tangent = np.asarray(
            physical_geometric_tangent, dtype=np.float64
        )
        material_tangent = 0.5 * (material_tangent + material_tangent.T)
        geometric_tangent = 0.5 * (geometric_tangent + geometric_tangent.T)
        total_tangent = np.asarray(physical_tangent, dtype=np.float64) + pl_tangent
        total_tangent = 0.5 * (total_tangent + total_tangent.T)
        if (
            not np.all(np.isfinite(total_force))
            or not np.all(np.isfinite(total_tangent))
            or total_force.shape != (18,)
            or total_tangent.shape != (18, 18)
        ):
            raise ValueError("qualified S3 nonlinear response is non-finite")

        trial_state = dict(committed)
        physical_state_fields = (
            (
                "plastic_strain",
                "alpha",
                "layer_strain",
                "layer_strain_material",
                "kinematic_layer_strain",
                "layer_stress",
                "layer_stress_material",
                "station_generalized_strain",
                "station_generalized_resultant",
            )
            if self.shell_section is None
            else (
                "station_generalized_strain",
                "station_generalized_resultant",
            )
        )
        for name in physical_state_fields:
            trial_state[name] = np.asarray(
                physical_trial[name], dtype=np.float64
            ).copy()
        trial_state["committed_total_u"] = total_u.copy()
        trial_state["committed_nodal_rotation_matrices"] = np.asarray(
            native_rotation_trial.trial_rotation_matrices, dtype=np.float64
        ).copy()
        trial_state["committed_pl_twist"] = np.asarray(
            pl_constraint, dtype=np.float64
        ).copy()
        trial_state["committed_pl_turn_count"] = np.asarray(
            pl_trial["turn_count"], dtype=np.int64
        ).copy()
        trial_state["committed_pl_multiplier"] = np.asarray(
            pl_multiplier, dtype=np.float64
        ).copy()
        trial_state["committed_pl_internal_force"] = pl_force.copy()
        trial_state["committed_pl_energy"] = float(pl_trial["energy"])
        trial_state["committed_director_triads"] = _update_native_director_triads(
            committed_triads,
            full_increment,
            native_rotation_trial=native_rotation_trial,
        )
        trial_state["bubble_rotation_last_increment"] = np.zeros(
            2, dtype=np.float64
        )
        trial_state["committed_internal_force"] = total_force.copy()
        sealed = seal_committed_s3_state(trial_state)
        validated = self.validate_model_bound_nonlinear_state(
            mesh,
            material,
            sealed,
            num_layers,
            expected_committed_total_u=total_u,
        )
        if bool(_return_tangent_components):
            return (
                total_force,
                total_tangent if bool(tangent) else None,
                validated,
                {
                    "material": material_tangent.copy(),
                    "geometric": geometric_tangent.copy(),
                    "total": total_tangent.copy(),
                    "physical_material": np.asarray(
                        physical_material_tangent, dtype=np.float64
                    ).copy(),
                    "physical_geometric": np.asarray(
                        physical_geometric_tangent, dtype=np.float64
                    ).copy(),
                    "objective_pl_material_numerical": pl_tangent.copy(),
                    "bubble_total_sensitivity": np.asarray(
                        bubble_metadata["bubble_total_sensitivity"],
                        dtype=np.float64,
                    ).copy(),
                    "bubble_projection": np.asarray(
                        bubble_metadata["bubble_projection"],
                        dtype=np.float64,
                    ).copy(),
                    "uncondensed_material": np.asarray(
                        bubble_metadata["uncondensed_material_tangent"],
                        dtype=np.float64,
                    ).copy(),
                    "uncondensed_geometric": np.asarray(
                        bubble_metadata["uncondensed_geometric_tangent"],
                        dtype=np.float64,
                    ).copy(),
                    "uncondensed_total": np.asarray(
                        bubble_metadata["uncondensed_total_tangent"],
                        dtype=np.float64,
                    ).copy(),
                    "bubble_projection_policy_id": str(
                        bubble_metadata["bubble_projection_policy_id"]
                    ),
                    "decomposition_policy_id": (
                        CURRENT_STATE_TANGENT_DECOMPOSITION_POLICY_ID
                    ),
                },
            )
        return total_force, total_tangent if bool(tangent) else None, validated

    def compute_committed_current_tangent_components(
        self,
        mesh: Any,
        material: Any,
        committed_u_elem: Any,
        committed_state: Mapping[str, Any],
        num_layers: int = 5,
        *,
        native_rotation_trial: NativeElementRotationView,
    ) -> Mapping[str, Any]:
        """Return a transient decomposition at one exact committed state.

        The caller must provide a solver-owned native rotation transaction at
        zero increment.  This method validates the complete model-bound state,
        evaluates the same bubble equilibrium and consistent tangent used by
        nonlinear assembly, and returns owned read-only arrays.  No matrix,
        sensitivity, factorization, or candidate state is attached to the
        element or committed-state payload.
        """

        if not isinstance(committed_state, Mapping):
            raise S3CommittedStateError(
                "qualified S3 committed current tangent requires a state mapping"
            )
        displacement = np.asarray(committed_u_elem, dtype=np.float64)
        state_displacement = np.asarray(
            committed_state.get("committed_total_u", ()), dtype=np.float64
        )
        if (
            displacement.shape != (18,)
            or state_displacement.shape != (18,)
            or not np.all(np.isfinite(displacement))
            or not np.array_equal(displacement, state_displacement)
        ):
            raise S3CommittedStateError(
                "qualified S3 committed current tangent requires the exact "
                "model-bound committed element displacement"
            )
        if not isinstance(native_rotation_trial, NativeElementRotationView):
            raise TypeError(
                "qualified S3 committed current tangent requires "
                "NativeElementRotationView"
            )
        if (
            not np.array_equal(
                native_rotation_trial.coordinate_increment,
                np.zeros((3, 3), dtype=np.float64),
            )
            or not np.array_equal(
                native_rotation_trial.rotation_coordinate_increment,
                np.zeros((3, 3), dtype=np.float64),
            )
            or not np.array_equal(
                native_rotation_trial.trial_rotation_matrices,
                native_rotation_trial.committed_rotation_matrices,
            )
        ):
            raise S3CommittedStateError(
                "qualified S3 committed current tangent is read-only and "
                "requires an exact zero-increment native trial"
            )

        committed_bytes_before = canonical_json_bytes(committed_state)
        source_digest = str(committed_state.get("state_integrity_sha256", ""))
        force, total, _candidate_state, components = self.compute_nonlinear_response(
            mesh,
            material,
            displacement,
            committed_state,
            int(num_layers),
            True,
            native_rotation_trial=native_rotation_trial,
            _return_tangent_components=True,
        )
        if total is None:
            raise RuntimeError("qualified S3 committed current tangent is missing")
        committed_bytes_after = canonical_json_bytes(committed_state)
        if committed_bytes_after != committed_bytes_before or not source_digest:
            raise S3CommittedStateError(
                "qualified S3 committed current tangent mutated its input or "
                "was not bound to an integrity-sealed committed state"
            )

        readonly: Dict[str, Any] = {
            "state_digest": source_digest,
            "state_storage": "transient_read_only_not_persisted",
            "decomposition_policy_id": (
                CURRENT_STATE_TANGENT_DECOMPOSITION_POLICY_ID
            ),
            "bubble_projection_policy_id": (
                CURRENT_STATE_BUBBLE_PROJECTION_POLICY_ID
            ),
            "force": np.asarray(force, dtype=np.float64).copy(),
        }
        for name, value in components.items():
            if isinstance(value, np.ndarray):
                made = np.asarray(value, dtype=np.float64).copy()
                made.setflags(write=False)
                readonly[name] = made
            else:
                readonly[name] = value
        force_array = np.asarray(readonly["force"], dtype=np.float64)
        force_array.setflags(write=False)
        readonly["force"] = force_array

        material_tangent = np.asarray(readonly["material"], dtype=np.float64)
        geometric_tangent = np.asarray(readonly["geometric"], dtype=np.float64)
        total_tangent = np.asarray(readonly["total"], dtype=np.float64)
        relative_decomposition_error = float(
            np.linalg.norm(
                total_tangent - material_tangent - geometric_tangent,
                ord="fro",
            )
            / max(float(np.linalg.norm(total_tangent, ord="fro")), 1.0)
        )
        relative_symmetry_error = max(
            float(
                np.linalg.norm(matrix - matrix.T, ord="fro")
                / max(float(np.linalg.norm(matrix, ord="fro")), 1.0)
            )
            for matrix in (
                material_tangent,
                geometric_tangent,
                total_tangent,
            )
        )
        if (
            relative_decomposition_error > 256.0 * np.finfo(np.float64).eps
            or relative_symmetry_error > 512.0 * np.finfo(np.float64).eps
        ):
            raise ValueError(
                "qualified S3 committed tangent components violate their "
                "decomposition or symmetry bound"
            )
        readonly["relative_decomposition_error"] = (
            relative_decomposition_error
        )
        readonly["relative_symmetry_error"] = relative_symmetry_error
        return MappingProxyType(readonly)


__all__ = [
    "ALGEBRAIC_COORDINATE_POLICY_ID",
    "BUBBLE_CONVENTION",
    "BUBBLE_CONDITION_LIMIT",
    "BUBBLE_FORCE_CONDENSATION_ID",
    "BUBBLE_LINE_SEARCH_MIN_FACTOR",
    "BUBBLE_LINE_SEARCH_REDUCTION",
    "BUBBLE_MAX_ITERATIONS",
    "BUBBLE_OFFSET_D",
    "BUBBLE_RELATIVE_TOLERANCE",
    "BUBBLE_STEP_TOLERANCE",
    "CAPABILITY_GAPS",
    "CURRENT_STATE_BUBBLE_PROJECTION_POLICY_ID",
    "CURRENT_STATE_TANGENT_DECOMPOSITION_POLICY_ID",
    "DIRECTOR_GAUGE_ID",
    "DYNAMIC_REDUCTION_POLICY",
    "EXTERNAL_ROTATION_MAP_ID",
    "FORMULATION_ID",
    "FORMULATION_SCHEMA",
    "GEOMETRIC_STIFFNESS_POLICY_ID",
    "HOMOGENEOUS_ELASTIC_STRESS_PROFILE_ID",
    "MITC3_PLUS_EQUATION_MAP",
    "MITC3_PLUS_NONLINEAR_EQUATION_MAP",
    "MITC3_PLUS_NONLINEAR_SOURCE_BYTES",
    "MITC3_PLUS_NONLINEAR_SOURCE_SHA256",
    "MITC3_PLUS_NONLINEAR_SOURCE_URL",
    "MITC3_PLUS_SOURCE_BYTES",
    "MITC3_PLUS_SOURCE_SHA256",
    "MITC3_PLUS_SOURCE_URL",
    "MASS_MOMENT_ID",
    "MINIMUM_OWNER_NORMAL_ALIGNMENT",
    "NONLINEAR_POLICY_ID",
    "PHYSICAL_EXTERNAL_INDICES",
    "QUADRATURE_ID",
    "RECOVERY_POLICY_ID",
    "REFERENCE_ELASTIC_BUBBLE_LINEARIZATION_ID",
    "RESULTANT_SUMMARY_POLICY_ID",
    "S3BubbleEquilibriumError",
    "STATE_LAYOUT_ID",
    "TRIANGLE_QUADRATURE",
    "TYING_POINTS",
    "QualifiedE4PLS3ShellElement",
    "invariant_drilling_scale",
    "triangle_frame",
]
