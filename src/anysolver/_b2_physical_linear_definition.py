"""Private, owned physical B2 reference definition; no public dispatch.

The optional inertia and geometric records are independent of stiffness.
This module performs definition admission only; it does not claim mass,
prestress, attachment, graph, or F09 qualification.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math

import numpy as np

from ._b2_physical_flexibility_linear import (
    LinearOperator, LinearSection, RepresentabilityError,
)


PROFILE_ID = "B2_E4_PL_FAST_LINEAR_V1"
SCHEMA_ID = "B2_PHYSICAL_LINEAR_DEFINITION_V1"


def _identifier(value, label):
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"nonempty canonical {label} required")
    return value


def _vector(value, label):
    try:
        vector = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"finite three-component {label} required") from exc
    if vector.shape != (3,) or not np.isfinite(vector).all():
        raise ValueError(f"finite three-component {label} required")
    return tuple(float(v) for v in vector)


def _exact_psd(matrix):
    """Check the owned binary64 matrix as exact rational input, no floor."""
    a = [[Fraction(float(value)) for value in row] for row in matrix]
    if not any(a[i][i] > 0 for i in range(6)):
        raise ValueError("nonzero positive-semidefinite sectional inertia required")
    for k in range(6):
        pivot = a[k][k]
        if pivot < 0 or (pivot == 0 and any(a[k][j] != 0 for j in range(k+1,6))):
            raise ValueError("positive-semidefinite sectional inertia required")
        if pivot == 0:
            continue
        for i in range(k+1,6):
            for j in range(i,6):
                a[i][j] -= a[i][k]*a[k][j]/pivot
                a[j][i] = a[i][j]
        for i in range(k+1,6):
            a[k][i] = a[i][k] = Fraction(0)


@dataclass(frozen=True)
class MassMetadata:
    """Explicit velocity-order sectional inertia per unit length.

    Entries are in local [vx, vy, vz, wx, wy, wz] coordinates, with velocity
    evaluated at ``origin_local_m`` relative to the member reference axis.
    No density or geometry is inferred.
    """

    source_id: str
    origin_local_m: tuple[float, float, float]
    matrix_per_m: tuple[tuple[float, ...], ...]

    def __post_init__(self):
        _identifier(self.source_id, "mass source ID")
        object.__setattr__(self, "origin_local_m", _vector(self.origin_local_m, "mass origin"))
        try:
            matrix = np.asarray(self.matrix_per_m, dtype=float)
        except (TypeError, ValueError) as exc:
            raise ValueError("finite symmetric 6x6 mass per length required") from exc
        if (matrix.shape != (6, 6) or not np.isfinite(matrix).all()
                or not np.array_equal(matrix, matrix.T)):
            raise ValueError("finite symmetric 6x6 mass per length required")
        _exact_psd(matrix)
        object.__setattr__(self, "matrix_per_m", tuple(
            tuple(float(v) for v in row) for row in matrix))

    def matrix_at_reference_axis(self) -> np.ndarray:
        """Pull sectional kinetic work back to the member reference axis.

        For the declared origin r, v_origin = v_axis + omega cross r.  The
        returned owned array has velocity order [v_axis, omega].  This is a
        kinematic transformation of supplied inertia, not inertia inferred
        from the section stiffness or geometry.
        """
        x, y, z = self.origin_local_m
        pullback = np.eye(6)
        pullback[:3, 3:] = ((0., z, -y), (-z, 0., x), (y, -x, 0.))
        with np.errstate(over="ignore", invalid="ignore"):
            matrix = pullback.T @ np.asarray(self.matrix_per_m) @ pullback
        if not np.isfinite(matrix).all():
            raise RepresentabilityError("B2 mass-origin pullback is not representable")
        return matrix


@dataclass(frozen=True)
class GeometricMetadata:
    """Explicit local section positions and optional polar datum, independent of S."""

    source_id: str
    section_origin_local_m: tuple[float, float, float]
    centroid_local_m: tuple[float, float, float]
    shear_center_local_m: tuple[float, float, float]
    geometric_polar_radius_squared_m2: float | None = None

    def __post_init__(self):
        _identifier(self.source_id, "geometry source ID")
        for label in ("section_origin_local_m", "centroid_local_m",
                      "shear_center_local_m"):
            object.__setattr__(self, label, _vector(getattr(self, label), label))
        radius = self.geometric_polar_radius_squared_m2
        if radius is None:
            return
        if type(radius) not in (int, float) or not math.isfinite(radius) or radius <= 0:
            raise ValueError("explicit positive geometric polar radius squared required")
        object.__setattr__(self, "geometric_polar_radius_squared_m2", float(radius))


@dataclass(frozen=True)
class GlobalLinearTrace:
    """Owned global point reference, pose, and global-coordinate pullback."""

    stations: np.ndarray
    reference_points_m: np.ndarray
    pose: np.ndarray
    jacobian: np.ndarray
    profile_id: str = PROFILE_ID
    production_qualified: bool = False


@dataclass(frozen=True)
class PhysicalB2Member:
    """A straight, explicitly oriented member with owned source identity."""

    member_id: str
    source_id: str
    node_ids: tuple[int, int]
    reference_points_m: tuple[tuple[float, float, float], ...]
    local_y_global: tuple[float, float, float]
    section_id: str
    section: LinearSection
    mass: MassMetadata | None = None
    geometric: GeometricMetadata | None = None
    profile_id: str = PROFILE_ID
    schema_id: str = SCHEMA_ID
    unit_system: str = "SI"

    def __post_init__(self):
        for label in ("member_id", "source_id", "section_id"):
            _identifier(getattr(self, label), label)
        if self.profile_id != PROFILE_ID or self.schema_id != SCHEMA_ID:
            raise ValueError("explicit physical B2 profile/schema identity required")
        if self.unit_system != "SI":
            raise ValueError("explicit SI unit convention required")
        if (not isinstance(self.node_ids, (tuple, list)) or len(self.node_ids) != 2
                or any(type(v) is not int for v in self.node_ids)
                or self.node_ids[0] == self.node_ids[1]):
            raise ValueError("two distinct integer model node IDs required")
        object.__setattr__(self, "node_ids", tuple(self.node_ids))
        if (not isinstance(self.reference_points_m, (tuple, list, np.ndarray))
                or len(self.reference_points_m) != 2):
            raise ValueError("two reference positions required")
        points = tuple(_vector(p, "reference point") for p in self.reference_points_m)
        direction = np.subtract(points[1], points[0])
        length = float(np.linalg.norm(direction))
        if not math.isfinite(length) or length <= 0:
            raise ValueError("nondegenerate finite straight member required")
        tangent = direction/length
        y = np.asarray(_vector(self.local_y_global, "physical local y axis"))
        if abs(float(np.linalg.norm(y))-1.) > 1e-10 or abs(float(tangent@y)) > 1e-10:
            raise ValueError("unit local y axis perpendicular to member required")
        # Canonicalize admitted roundoff so the execution map is orthonormal.
        y = y-tangent*float(tangent@y)
        y = y/np.linalg.norm(y)
        if not isinstance(self.section, LinearSection):
            raise ValueError("physical linear B2 section required")
        if self.mass is not None and not isinstance(self.mass, MassMetadata):
            raise ValueError("explicit mass metadata required")
        if self.geometric is not None and not isinstance(self.geometric, GeometricMetadata):
            raise ValueError("explicit geometric metadata required")
        object.__setattr__(self, "reference_points_m", points)
        object.__setattr__(self, "local_y_global", tuple(float(v) for v in y))

    @property
    def length_m(self) -> float:
        p0, p1 = self.reference_points_m
        return float(np.linalg.norm(np.subtract(p1, p0)))

    def local_frame_rows(self) -> np.ndarray:
        x = np.subtract(self.reference_points_m[1], self.reference_points_m[0])
        x = x/np.linalg.norm(x)
        y = np.asarray(self.local_y_global)
        z = np.cross(x, y)
        return np.array((x, y, z), dtype=float, copy=True)

    def local_dof_map(self) -> np.ndarray:
        """Return a fresh 12x12 global-to-local translation/rotation map."""
        return np.kron(np.eye(4), self.local_frame_rows())

    def local_operator(self) -> LinearOperator:
        return LinearOperator(self.length_m, self.section)

    def local_candidate_mass_matrix(self) -> np.ndarray:
        """Integrate explicit sectional inertia through the static station trace.

        This private candidate retains the supplied mass origin and the
        physical B2 station kinematics. It does not admit coupled dynamics.
        """
        if self.mass is None:
            raise ValueError("explicit B2 mass metadata required")
        mass_per_m = self.mass.matrix_at_reference_axis()
        abscissae, weights = np.polynomial.legendre.leggauss(4)
        stations = tuple(float((x+1.)/2.) for x in abscissae)
        trace = self.local_operator().trace(np.zeros(12), stations=stations)
        matrix = np.zeros((12, 12))
        with np.errstate(over="ignore", invalid="ignore"):
            for weight, jacobian in zip(weights, trace.jacobian):
                matrix += (self.length_m*weight/2.) * (
                    jacobian.T @ mass_per_m @ jacobian)
        if not np.isfinite(matrix).all():
            raise RepresentabilityError("physical B2 candidate mass is not representable")
        return matrix

    def trace_global(self, displacement, *, stations=(0.0, 0.5, 1.0),
                     offset_local_m=(0.0, 0.0, 0.0)) -> GlobalLinearTrace:
        """Private physical station port in the declared global nodal basis."""
        try:
            u = np.asarray(displacement, dtype=float)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("twelve finite global coordinates required") from exc
        if u.shape != (12,) or not np.isfinite(u).all():
            raise ValueError("twelve finite global coordinates required")
        frame = self.local_frame_rows()
        transform = self.local_dof_map()
        local = self.local_operator().trace(
            transform@u, stations=stations, offset_local_m=offset_local_m)
        six = np.zeros((6, 6))
        six[:3, :3] = six[3:, 3:] = frame.T
        with np.errstate(over="ignore", invalid="ignore", under="ignore"):
            points = local.reference_points@frame + np.asarray(self.reference_points_m[0])
            pose = local.pose@six.T
            jacobian = np.einsum("ab,nbc,cd->nad", six, local.jacobian, transform)
        if not all(np.isfinite(v).all() for v in (points, pose, jacobian)):
            raise RepresentabilityError("global physical B2 trace is not representable")
        return GlobalLinearTrace(local.stations.copy(), points.copy(), pose.copy(),
                                 jacobian.copy())
