"""Independent flat DKMT reference for the S3 E4-PL V2A candidate.

This research-only module implements the printed DKMT equations in Katili,
Maknun, and Katili (2019), pp. 529--531, Eqs. (12)--(16), (20)--(41).  The
hash-bound source is ``katili_2019_dkmt_review.pdf`` with SHA-256
``CAACAB9E0DF9B4F8B55887E84FAFA923899677F7D0F285EB2EEB46FBDFF8D17A``.

The supported scope is deliberately narrow: a flat triangle, an uncoupled
isotropic membrane/bending/shear section, the paper's three-point Hammer
rule, and the separately derived barycentric PL completion.  Generalized
coupling and anisotropy fail closed.  Curved, nonlinear, dynamic, and
recovery mechanics are outside this reference's authority.

Shell nodal coordinates are ``(u, v, w, theta_x, theta_y, theta_D)``.  The
paper's rotations are embedded as ``beta_x=theta_y`` and
``beta_y=-theta_x`` so that ``gamma=(w,x+beta_x,w,y+beta_y)`` vanishes for
the two transverse rigid rotations.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping, Sequence

import numpy as np


REFERENCE_IMPLEMENTATION_ID = "INDEPENDENT_S3_V2A_FLAT_DKMT_EQ12_41_V1"
PROOF_SCHEMA = "E4_PL_S3_V2A_FLAT_DKMT_PROOF_V1"
SOURCE_PDF_SHA256 = "CAACAB9E0DF9B4F8B55887E84FAFA923899677F7D0F285EB2EEB46FBDFF8D17A"
SOURCE_EQUATION_MAP = {
    "edge_projection": "pp529:Eqs12-16",
    "edge_compatible_shear": "pp529:Eqs20-22",
    "hierarchical_rotations": "pp530:Eqs24-31",
    "phi_and_discrete_constraint": "pp530-531:Eqs32-38",
    "curvature_and_assumed_shear": "pp531:Eqs39-41",
}

DOFS_PER_NODE = 6
NODE_COUNT = 3
TOTAL_DOFS = DOFS_PER_NODE * NODE_COUNT
PHYSICAL_COMPONENTS = (0, 1, 2, 3, 4)
PHYSICAL_INDICES = np.asarray(
    [DOFS_PER_NODE * node + component for node in range(NODE_COUNT) for component in PHYSICAL_COMPONENTS],
    dtype=np.intp,
)
ORIENTED_EDGES = ((0, 1), (1, 2), (2, 0))

# Degree-two exact Hammer rule.  Weights sum to one and are multiplied by A.
TRIANGLE_RULE = (
    ((2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0), 1.0 / 3.0),
    ((1.0 / 6.0, 2.0 / 3.0, 1.0 / 6.0), 1.0 / 3.0),
    ((1.0 / 6.0, 1.0 / 6.0, 2.0 / 3.0), 1.0 / 3.0),
)


@dataclass(frozen=True)
class IsotropicSectionParameters:
    young: float
    poisson: float
    thickness: float
    shear_correction: float
    membrane_rigidity: float
    bending_rigidity: float
    shear_rigidity: float


@dataclass(frozen=True)
class FlatReference:
    """Complete 18-coordinate CST + DKMT + PL reference."""

    nodes: np.ndarray
    section: np.ndarray
    section_parameters: IsotropicSectionParameters
    area: float
    shape_gradients: np.ndarray
    edge_directions: np.ndarray
    edge_lengths: np.ndarray
    membrane_operator: np.ndarray
    bending_beta_operator: np.ndarray
    au_operator: np.ndarray
    phi: np.ndarray
    a_delta: np.ndarray
    delta_beta_operator: np.ndarray
    curvature_operators: np.ndarray
    shear_operators: np.ndarray
    membrane_stiffness: np.ndarray
    bending_stiffness: np.ndarray
    shear_stiffness: np.ndarray
    physical_stiffness: np.ndarray
    pl_constraint: np.ndarray
    pl_gram: np.ndarray
    pl_scale: float
    pl_stiffness: np.ndarray
    condensed_stiffness: np.ndarray
    saddle_stiffness: np.ndarray
    rigid_modes: np.ndarray


def _finite_matrix(value: object, shape: tuple[int, int], name: str) -> np.ndarray:
    matrix = np.asarray(value, dtype=np.float64)
    if matrix.shape != shape or not np.all(np.isfinite(matrix)):
        raise ValueError(f"{name} must be a finite {shape[0]}x{shape[1]} matrix")
    return matrix


def _symmetric_positive_definite(value: object, shape: tuple[int, int], name: str) -> np.ndarray:
    matrix = _finite_matrix(value, shape, name)
    scale = max(float(np.linalg.norm(matrix, ord=np.inf)), 1.0)
    tolerance = 4096.0 * np.finfo(float).eps * scale
    if float(np.linalg.norm(matrix - matrix.T, ord=np.inf)) > tolerance:
        raise ValueError(f"{name} must be symmetric")
    matrix = 0.5 * (matrix + matrix.T)
    try:
        np.linalg.cholesky(matrix)
    except np.linalg.LinAlgError as exc:
        raise ValueError(f"{name} must be positive definite") from exc
    return matrix


def geometry(nodes: Sequence[Sequence[float]]) -> tuple[np.ndarray, float, np.ndarray]:
    """Return nodes, positive area, and physical barycentric gradients."""

    points = _finite_matrix(nodes, (3, 2), "nodes")
    jacobian = np.column_stack((points[1] - points[0], points[2] - points[0]))
    determinant = float(np.linalg.det(jacobian))
    scale = max(float(np.linalg.norm(jacobian, ord=np.inf)) ** 2, 1.0)
    if not math.isfinite(determinant) or abs(determinant) <= 64.0 * np.finfo(float).eps * scale:
        raise ValueError("nodes must define a nondegenerate triangle")
    reference_gradients = np.asarray(((-1.0, -1.0), (1.0, 0.0), (0.0, 1.0)))
    gradients = reference_gradients @ np.linalg.inv(jacobian)
    return points, 0.5 * abs(determinant), gradients


def isotropic_generalized_section(
    young: float,
    poisson: float,
    thickness: float,
    shear_correction: float = 5.0 / 6.0,
) -> np.ndarray:
    """Construct the only generalized section admitted by this reference."""

    values = (float(young), float(poisson), float(thickness), float(shear_correction))
    if not all(math.isfinite(value) for value in values):
        raise ValueError("isotropic section parameters must be finite")
    young, poisson, thickness, shear_correction = values
    if young <= 0.0 or thickness <= 0.0 or shear_correction <= 0.0 or not (-1.0 < poisson < 0.5):
        raise ValueError("unsupported isotropic section parameters")
    membrane_rigidity = young * thickness / (1.0 - poisson * poisson)
    membrane = membrane_rigidity * np.asarray(
        ((1.0, poisson, 0.0), (poisson, 1.0, 0.0), (0.0, 0.0, 0.5 * (1.0 - poisson)))
    )
    bending = (thickness * thickness / 12.0) * membrane
    shear_rigidity = shear_correction * membrane[2, 2]
    section = np.zeros((8, 8), dtype=np.float64)
    section[:3, :3] = membrane
    section[3:6, 3:6] = bending
    section[6:, 6:] = shear_rigidity * np.eye(2)
    return section


def validate_supported_section(section: Sequence[Sequence[float]]) -> tuple[np.ndarray, IsotropicSectionParameters]:
    """Validate an uncoupled isotropic flat section or fail closed."""

    matrix = _symmetric_positive_definite(section, (8, 8), "section")
    scale = max(float(np.linalg.norm(matrix, ord=np.inf)), 1.0)
    tolerance = 8192.0 * np.finfo(float).eps * scale
    allowed = np.zeros((8, 8), dtype=bool)
    allowed[:3, :3] = True
    allowed[3:6, 3:6] = True
    allowed[6:, 6:] = True
    if np.any(np.abs(matrix[~allowed]) > tolerance):
        raise ValueError("unsupported generalized section coupling")

    membrane = matrix[:3, :3]
    bending = matrix[3:6, 3:6]
    shear = matrix[6:, 6:]
    poisson = float(membrane[0, 1] / membrane[0, 0])
    membrane_target = membrane[0, 0] * np.asarray(
        ((1.0, poisson, 0.0), (poisson, 1.0, 0.0), (0.0, 0.0, 0.5 * (1.0 - poisson)))
    )
    if not (-1.0 < poisson < 0.5) or not np.allclose(membrane, membrane_target, rtol=2.0e-13, atol=tolerance):
        raise ValueError("unsupported non-isotropic membrane section")
    ratio = float(bending[0, 0] / membrane[0, 0])
    if ratio <= 0.0 or not np.allclose(bending, ratio * membrane, rtol=2.0e-13, atol=tolerance):
        raise ValueError("unsupported non-isotropic bending section")
    if not np.allclose(shear, shear[0, 0] * np.eye(2), rtol=2.0e-13, atol=tolerance):
        raise ValueError("unsupported non-isotropic transverse shear section")

    thickness = math.sqrt(12.0 * ratio)
    shear_correction = float(shear[0, 0] / membrane[2, 2])
    young = float(membrane[0, 0] * (1.0 - poisson * poisson) / thickness)
    if shear_correction <= 0.0 or not all(math.isfinite(value) for value in (thickness, shear_correction, young)):
        raise ValueError("unsupported isotropic thickness or shear correction")
    parameters = IsotropicSectionParameters(
        young=young,
        poisson=poisson,
        thickness=thickness,
        shear_correction=shear_correction,
        membrane_rigidity=float(membrane[0, 0]),
        bending_rigidity=float(bending[0, 0]),
        shear_rigidity=float(shear[0, 0]),
    )
    return matrix, parameters


def invariant_pl_scale(membrane: Sequence[Sequence[float]]) -> float:
    """Return ``1/2 lambda_min(P.T A P, diag(2,1/2))``."""

    constitutive = _symmetric_positive_definite(membrane, (3, 3), "membrane")
    projector = np.asarray(((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0)))
    metric_inverse_sqrt = np.asarray(((1.0 / math.sqrt(2.0), 0.0), (0.0, math.sqrt(2.0))))
    canonical = metric_inverse_sqrt @ (projector.T @ constitutive @ projector) @ metric_inverse_sqrt
    value = 0.5 * float(np.linalg.eigvalsh(0.5 * (canonical + canonical.T))[0])
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError("PL scale must be strictly positive")
    return value


def membrane_operator(gradients: np.ndarray) -> np.ndarray:
    operator = np.zeros((3, TOTAL_DOFS), dtype=np.float64)
    for node, (dx, dy) in enumerate(gradients):
        base = DOFS_PER_NODE * node
        operator[0, base] = dx
        operator[1, base + 1] = dy
        operator[2, base] = dy
        operator[2, base + 1] = dx
    return operator


def bending_beta_operator(gradients: np.ndarray) -> np.ndarray:
    """Paper Eq. (6), embedded with beta_x=theta_y, beta_y=-theta_x."""

    operator = np.zeros((3, TOTAL_DOFS), dtype=np.float64)
    for node, (dx, dy) in enumerate(gradients):
        base = DOFS_PER_NODE * node
        operator[0, base + 4] = dx
        operator[1, base + 3] = -dy
        operator[2, base + 4] = dy
        operator[2, base + 3] = -dx
    return operator


def edge_geometry(nodes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    directions = np.zeros((3, 2), dtype=np.float64)
    lengths = np.zeros(3, dtype=np.float64)
    for row, (left, right) in enumerate(ORIENTED_EDGES):
        edge = nodes[right] - nodes[left]
        length = float(np.linalg.norm(edge))
        if not math.isfinite(length) or length <= 0.0:
            raise ValueError("every DKMT edge must have positive length")
        lengths[row] = length
        directions[row] = edge / length
    return directions, lengths


def au_operator(directions: np.ndarray, lengths: np.ndarray) -> np.ndarray:
    """Paper Eq. (22), mapped into the full 18-coordinate shell vector."""

    operator = np.zeros((3, TOTAL_DOFS), dtype=np.float64)
    for row, ((left, right), ((cosine, sine), length)) in enumerate(
        zip(ORIENTED_EDGES, zip(directions, lengths), strict=True)
    ):
        left_base = DOFS_PER_NODE * left
        right_base = DOFS_PER_NODE * right
        operator[row, left_base + 2] = -1.0 / length
        operator[row, right_base + 2] = 1.0 / length
        for base in (left_base, right_base):
            operator[row, base + 3] = -0.5 * sine
            operator[row, base + 4] = 0.5 * cosine
    return operator


def quadratic_edge_shape_gradients(barycentric: Sequence[float], gradients: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Paper Eq. (27): P4=4*L1*L2, P5=4*L2*L3, P6=4*L1*L3."""

    shapes = np.asarray(barycentric, dtype=np.float64)
    if shapes.shape != (3,) or not np.all(np.isfinite(shapes)) or not math.isclose(float(shapes.sum()), 1.0, abs_tol=2e-14):
        raise ValueError("barycentric must be a finite three-vector summing to one")
    pairs = ((0, 1), (1, 2), (0, 2))
    values = np.asarray([4.0 * shapes[left] * shapes[right] for left, right in pairs])
    physical_gradients = np.asarray(
        [4.0 * (shapes[left] * gradients[right] + shapes[right] * gradients[left]) for left, right in pairs]
    )
    return values, physical_gradients


def bending_delta_operator(barycentric: Sequence[float], gradients: np.ndarray, directions: np.ndarray) -> np.ndarray:
    """Paper Eq. (31) for midside tangential rotation enhancements."""

    _values, p_gradients = quadratic_edge_shape_gradients(barycentric, gradients)
    operator = np.zeros((3, 3), dtype=np.float64)
    for edge, ((px, py), (cosine, sine)) in enumerate(zip(p_gradients, directions, strict=True)):
        operator[:, edge] = (px * cosine, py * sine, py * cosine + px * sine)
    return operator


def edge_shear_projection(barycentric: Sequence[float], directions: np.ndarray) -> np.ndarray:
    """Paper Eqs. (12)--(16), mapping side shears (12,23,31) to (x,y)."""

    n1, n2, n3 = np.asarray(barycentric, dtype=np.float64)
    c12, s12 = directions[0]
    c23, s23 = directions[1]
    c31, s31 = directions[2]
    a1 = c12 * s31 - c31 * s12
    a2 = c23 * s12 - c12 * s23
    a3 = c31 * s23 - c23 * s31
    if min(abs(a1), abs(a2), abs(a3)) <= 64.0 * np.finfo(float).eps:
        raise ValueError("DKMT edge projection denominators must be nonzero")
    return np.asarray(
        (
            (
                s31 * n1 / a1 - s23 * n2 / a2,
                s12 * n2 / a2 - s31 * n3 / a3,
                s23 * n3 / a3 - s12 * n1 / a1,
            ),
            (
                -(c31 * n1 / a1 - c23 * n2 / a2),
                -(c12 * n2 / a2 - c31 * n3 / a3),
                -(c23 * n3 / a3 - c12 * n1 / a1),
            ),
        )
    )


def dkmt_operators_at(
    barycentric: Sequence[float],
    gradients: np.ndarray,
    directions: np.ndarray,
    b_beta: np.ndarray,
    a_u: np.ndarray,
    delta_beta: np.ndarray,
    phi: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return paper Eqs. (39) and (40)--(41) at one point."""

    b_delta = bending_delta_operator(barycentric, gradients, directions)
    curvature = b_beta + b_delta @ delta_beta
    rho = phi / (1.0 + phi)
    shear = edge_shear_projection(barycentric, directions) @ (rho[:, None] * a_u)
    return curvature, shear


def pl_blocks(gradients: np.ndarray, area: float, scale: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    constraint = np.zeros((3, TOTAL_DOFS), dtype=np.float64)
    for row in range(3):
        for node, (dx, dy) in enumerate(gradients):
            base = DOFS_PER_NODE * node
            constraint[row, base] = 0.5 * dy
            constraint[row, base + 1] = -0.5 * dx
        constraint[row, DOFS_PER_NODE * row + 5] = 1.0
    gram = (area / 12.0) * np.asarray(((2.0, 1.0, 1.0), (1.0, 2.0, 1.0), (1.0, 1.0, 2.0)))
    stiffness = scale * constraint.T @ gram @ constraint
    return constraint, gram, 0.5 * (stiffness + stiffness.T)


def rigid_mode_matrix(nodes: np.ndarray) -> np.ndarray:
    modes = np.zeros((TOTAL_DOFS, 6), dtype=np.float64)
    for node, (x, y) in enumerate(nodes):
        base = DOFS_PER_NODE * node
        modes[base, 0] = 1.0
        modes[base + 1, 1] = 1.0
        modes[base + 2, 2] = 1.0
        modes[base + 2, 3] = y
        modes[base + 3, 3] = 1.0
        modes[base + 2, 4] = -x
        modes[base + 4, 4] = 1.0
        modes[base, 5] = -y
        modes[base + 1, 5] = x
        modes[base + 5, 5] = 1.0
    return modes


def assemble_flat_reference(nodes: Sequence[Sequence[float]], section: Sequence[Sequence[float]]) -> FlatReference:
    """Assemble the supported flat CST + DKMT + barycentric-PL element."""

    points, area, gradients = geometry(nodes)
    constitutive, parameters = validate_supported_section(section)
    directions, lengths = edge_geometry(points)
    b_membrane = membrane_operator(gradients)
    b_beta = bending_beta_operator(gradients)
    a_u = au_operator(directions, lengths)
    phi = 12.0 * parameters.bending_rigidity / (parameters.shear_rigidity * lengths * lengths)
    if not np.all(np.isfinite(phi)) or not np.all(phi > 0.0):
        raise ValueError("DKMT phi values must be finite and strictly positive")
    a_delta = -(2.0 / 3.0) * np.diag(1.0 + phi)
    delta_beta = np.linalg.solve(a_delta, a_u)

    membrane_stiffness = area * (b_membrane.T @ constitutive[:3, :3] @ b_membrane)
    bending_stiffness = np.zeros((TOTAL_DOFS, TOTAL_DOFS), dtype=np.float64)
    shear_stiffness = np.zeros_like(bending_stiffness)
    curvatures: list[np.ndarray] = []
    shears: list[np.ndarray] = []
    for barycentric, weight in TRIANGLE_RULE:
        curvature, shear = dkmt_operators_at(barycentric, gradients, directions, b_beta, a_u, delta_beta, phi)
        curvatures.append(curvature)
        shears.append(shear)
        bending_stiffness += area * weight * (curvature.T @ constitutive[3:6, 3:6] @ curvature)
        shear_stiffness += area * weight * (shear.T @ constitutive[6:, 6:] @ shear)
    physical = membrane_stiffness + bending_stiffness + shear_stiffness
    physical = 0.5 * (physical + physical.T)

    pl_scale = invariant_pl_scale(constitutive[:3, :3])
    constraint, gram, pl_stiffness = pl_blocks(gradients, area, pl_scale)
    condensed = physical + pl_stiffness
    coupling = constraint.T @ gram
    saddle = np.zeros((TOTAL_DOFS + 3, TOTAL_DOFS + 3), dtype=np.float64)
    saddle[:TOTAL_DOFS, :TOTAL_DOFS] = physical
    saddle[:TOTAL_DOFS, TOTAL_DOFS:] = coupling
    saddle[TOTAL_DOFS:, :TOTAL_DOFS] = coupling.T
    saddle[TOTAL_DOFS:, TOTAL_DOFS:] = -gram / pl_scale
    return FlatReference(
        nodes=points,
        section=constitutive,
        section_parameters=parameters,
        area=area,
        shape_gradients=gradients,
        edge_directions=directions,
        edge_lengths=lengths,
        membrane_operator=b_membrane,
        bending_beta_operator=b_beta,
        au_operator=a_u,
        phi=phi,
        a_delta=a_delta,
        delta_beta_operator=delta_beta,
        curvature_operators=np.asarray(curvatures),
        shear_operators=np.asarray(shears),
        membrane_stiffness=0.5 * (membrane_stiffness + membrane_stiffness.T),
        bending_stiffness=0.5 * (bending_stiffness + bending_stiffness.T),
        shear_stiffness=0.5 * (shear_stiffness + shear_stiffness.T),
        physical_stiffness=physical,
        pl_constraint=constraint,
        pl_gram=gram,
        pl_scale=pl_scale,
        pl_stiffness=pl_stiffness,
        condensed_stiffness=0.5 * (condensed + condensed.T),
        saddle_stiffness=0.5 * (saddle + saddle.T),
        rigid_modes=rigid_mode_matrix(points),
    )


def generalized_fields(
    reference: FlatReference,
    dofs: Sequence[float],
    station: int | Sequence[float],
) -> dict[str, np.ndarray]:
    """Evaluate direct variational fields at a Hammer station or barycentric point."""

    vector = np.asarray(dofs, dtype=np.float64)
    if vector.shape != (TOTAL_DOFS,) or not np.all(np.isfinite(vector)):
        raise ValueError("dofs must be a finite 18-vector")
    if isinstance(station, (int, np.integer)):
        index = int(station)
        if index not in range(len(TRIANGLE_RULE)):
            raise ValueError("station must identify one of the three Hammer points")
        curvature = reference.curvature_operators[index]
        shear = reference.shear_operators[index]
    else:
        curvature, shear = dkmt_operators_at(
            station,
            reference.shape_gradients,
            reference.edge_directions,
            reference.bending_beta_operator,
            reference.au_operator,
            reference.delta_beta_operator,
            reference.phi,
        )
    operator = np.vstack((reference.membrane_operator, curvature, shear))
    strains = operator @ vector
    resultants = reference.section @ strains
    return {
        "strains": strains,
        "resultants": resultants,
        "N": resultants[:3],
        "M": resultants[3:6],
        "Q": resultants[6:],
        "operator": operator,
    }


def direct_internal_force(reference: FlatReference, dofs: Sequence[float]) -> np.ndarray:
    """Integrate direct N/M/Q virtual work, excluding numerical PL work."""

    vector = np.asarray(dofs, dtype=np.float64)
    if vector.shape != (TOTAL_DOFS,) or not np.all(np.isfinite(vector)):
        raise ValueError("dofs must be a finite 18-vector")
    force = np.zeros(TOTAL_DOFS, dtype=np.float64)
    for station, (_barycentric, weight) in enumerate(TRIANGLE_RULE):
        fields = generalized_fields(reference, vector, station)
        force += reference.area * weight * (fields["operator"].T @ fields["resultants"])
    return force


def block_permutation(permutation: Sequence[int]) -> np.ndarray:
    order = tuple(int(value) for value in permutation)
    if sorted(order) != [0, 1, 2]:
        raise ValueError("permutation must contain 0, 1, and 2 exactly once")
    transform = np.zeros((TOTAL_DOFS, TOTAL_DOFS), dtype=np.float64)
    for new_node, old_node in enumerate(order):
        rows = slice(DOFS_PER_NODE * new_node, DOFS_PER_NODE * (new_node + 1))
        columns = slice(DOFS_PER_NODE * old_node, DOFS_PER_NODE * (old_node + 1))
        transform[rows, columns] = np.eye(DOFS_PER_NODE)
    return transform


def _canonical_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return [_canonical_value(item) for item in value.tolist()]
    if isinstance(value, (np.floating, float)):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("canonical records forbid nonfinite numbers")
        return {"binary64": number.hex()}
    if isinstance(value, (np.integer, int)) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, Mapping):
        return {str(key): _canonical_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    if value is None or isinstance(value, (str, bool)):
        return value
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")


def canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(_canonical_value(value), sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def canonical_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest().upper()


def make_proof(nodes: Sequence[Sequence[float]], section: Sequence[Sequence[float]]) -> dict[str, Any]:
    """Emit primitive inputs and producer hashes for an independent checker."""

    assembled = assemble_flat_reference(nodes, section)
    probe = np.asarray(
        (3, -5, 7, 11, -13, 17, -19, 23, 29, -31, 37, 41, 43, -47, 53, 59, -61, 67),
        dtype=np.float64,
    ) / 32.0
    direct_force = direct_internal_force(assembled, probe)
    station_resultants = [generalized_fields(assembled, probe, station)["resultants"] for station in range(3)]
    matrices = {
        "physical": assembled.physical_stiffness,
        "pl": assembled.pl_stiffness,
        "condensed": assembled.condensed_stiffness,
        "saddle": assembled.saddle_stiffness,
        "direct_force": direct_force,
    }
    return {
        "schema": PROOF_SCHEMA,
        "nodes": np.asarray(nodes, dtype=np.float64),
        "section": np.asarray(section, dtype=np.float64),
        "claims": {
            "reference": REFERENCE_IMPLEMENTATION_ID,
            "source_pdf_sha256": SOURCE_PDF_SHA256,
            "hashes": {
                **{name: canonical_sha256({"matrix": matrix}) for name, matrix in matrices.items()},
                "station_resultants": canonical_sha256({"rows": station_resultants}),
            },
        },
    }


__all__ = [
    "FlatReference",
    "IsotropicSectionParameters",
    "REFERENCE_IMPLEMENTATION_ID",
    "PROOF_SCHEMA",
    "SOURCE_EQUATION_MAP",
    "SOURCE_PDF_SHA256",
    "TRIANGLE_RULE",
    "assemble_flat_reference",
    "au_operator",
    "bending_beta_operator",
    "bending_delta_operator",
    "block_permutation",
    "canonical_bytes",
    "canonical_sha256",
    "direct_internal_force",
    "dkmt_operators_at",
    "edge_geometry",
    "edge_shear_projection",
    "generalized_fields",
    "geometry",
    "invariant_pl_scale",
    "isotropic_generalized_section",
    "make_proof",
    "membrane_operator",
    "quadratic_edge_shape_gradients",
    "rigid_mode_matrix",
    "validate_supported_section",
]
