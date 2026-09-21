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

from ._b2_physical_flexibility_linear import LinearOperator, LinearSection


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

    Entries are in local [vx, vy, vz, wx, wy, wz] coordinates; source and
    origin identify the physical data. No density or geometry is inferred.
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
