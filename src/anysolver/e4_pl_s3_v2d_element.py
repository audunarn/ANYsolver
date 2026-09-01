"""Opt-in S3 V2D native-parity successor.

V2D preserves the accepted V2C MIN3/CST/PL small-strain operator and adds a
native generalized-section integration surface.  This first implementation
gate is intentionally linear and stateless.  Nonlinear geometry, material
history, restart, offsets and activation remain fail-closed until their own
reviewed gates are complete.

No legacy TRI3 or qualified-Q4 mechanics are dispatched from this module.
"""

from __future__ import annotations

import math
from types import MappingProxyType
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

import numpy as np

from .element_capabilities import ElementCapabilityError
from .elements import ShellElement
from .e4_pl_element import QualifiedE4PLShellElement
from .e4_pl_s3_v2c_element import (
    HAMMER_POINTS,
    HAMMER_REFERENCE_WEIGHTS,
    PL_COMPLETION_POLICY_ID,
    RELAXATION_AUTHORITY_SHA256,
    RESULTANT_POLICY_ID,
    StrictFlatLinearE4PLS3V2CShellElement,
)
from .fe_core import FEMesh, Material


SELECTOR = "e4-pl-s3-v2d"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V2D_NATIVE_PARITY_V1"
IMPLEMENTATION_ID = "E4_PL_S3_V2D_MIN3_NATIVE_SECTION_LINEAR_GATE_V1"
FORMULATION_SCHEMA = "anysolver.e4-pl-s3-v2d-native-parity-element-v1"
SOURCE_SELECTION_SHA256 = (
    "DB5750539FB87CA4E4DDA1B37ECEACD65B76DF9A64969808712A4BDD44A45E3D"
)
V2C_OPERATOR_SHA256 = (
    "84FB0B881F0F795BB9FC315A27FF53998BADE58CBAA1EF0A48785A5BE5E086F4"
)
NATIVE_SECTION_POLICY_ID = "S3_V2D_NATIVE_MIN3_GENERALIZED_SECTION_STATIONS_V1"
SERIALIZATION_POLICY_ID = "S3_V2D_STATELESS_LINEAR_FINGERPRINT_V1"
DRILL_SCALE_POLICY_ID = "S3_BASIS_INVARIANT_GENERALIZED_EIGENVALUE_V1"
MASS_POLICY_ID = "S3_V2D_TRANSLATIONAL_LUMPED_SECTION_AREAL_MASS_V1"
CBMIN3 = 2.0

_NORMAL_TOLERANCE = 1.0e-10
_DEGENERACY_FACTOR = 64.0 * np.finfo(np.float64).eps
_ROTATIONAL_INDICES = np.asarray((3, 4, 9, 10, 15, 16), dtype=np.intp)
_DRILL_PROJECTOR = np.asarray(((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0)))
_DRILL_INVERSE_METRIC_SQRT = np.diag((1.0 / math.sqrt(2.0), math.sqrt(2.0)))


class NativeParityCapabilityError(ElementCapabilityError):
    """An operation is outside the currently accepted V2D gate."""


SUPPORTED_OPERATIONS = frozenset(
    {
        "accepted_v2c_linear_stiffness",
        "accepted_v2c_linear_internal_force",
        "native_linear_generalized_section",
        "native_variational_resultants",
        "dead_uniform_pressure",
        "lumped_translational_mass",
        "stateless_serialization",
    }
)
BLOCKED_OPERATIONS = frozenset(
    {
        "nonlinear_geometry",
        "material_nonlinearity",
        "nonlinear_state",
        "restart",
        "reference_surface_offset",
        "director_polarity_reversal",
        "follower_pressure",
        "distributed_couple",
        "contact_state",
        "activity_state",
        "qualified_batch_path",
        "default_activation",
    }
)
CAPABILITY_MATRIX = MappingProxyType(
    {
        **{name: "SUPPORTED_V6A_LINEAR_NATIVE_PARITY" for name in SUPPORTED_OPERATIONS},
        **{name: "BLOCKED_PENDING_SUCCESSOR_GATE" for name in BLOCKED_OPERATIONS},
    }
)


def _real_scalar(value: Any, label: str) -> float:
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, float, np.integer, np.floating)
    ):
        raise TypeError(f"S3 V2D {label} must be a finite real scalar")
    made = float(value)
    if not math.isfinite(made):
        raise ValueError(f"S3 V2D {label} must be finite")
    return made


def _immutable_vector(value: Any, label: str) -> np.ndarray:
    try:
        vector = np.asarray(value, dtype=np.float64).reshape(-1)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"S3 V2D {label} must be a finite 3-vector") from exc
    if vector.size != 3 or not np.all(np.isfinite(vector)):
        raise ValueError(f"S3 V2D {label} must be a finite 3-vector")
    norm = float(np.linalg.norm(vector))
    if not math.isfinite(norm) or norm <= 0.0:
        raise ValueError(f"S3 V2D {label} must be nonzero")
    contiguous = np.ascontiguousarray(vector / norm, dtype=np.float64)
    return np.frombuffer(contiguous.tobytes(order="C"), dtype=np.float64)


def _block_permutation(order: Tuple[int, int, int]) -> np.ndarray:
    permutation = np.zeros((18, 18), dtype=np.float64)
    identity = np.eye(6, dtype=np.float64)
    for internal, external in enumerate(order):
        permutation[
            6 * internal : 6 * internal + 6,
            6 * external : 6 * external + 6,
        ] = identity
    return permutation


def _local_component_transform(frame: np.ndarray) -> np.ndarray:
    transform = np.zeros((18, 18), dtype=np.float64)
    local_from_global = np.asarray(frame, dtype=np.float64).T
    for node in range(3):
        base = 6 * node
        transform[base : base + 3, base : base + 3] = local_from_global
        transform[base + 3 : base + 6, base + 3 : base + 6] = local_from_global
    return transform


def _invariant_drill_scale(membrane: np.ndarray) -> float:
    matrix = np.asarray(membrane, dtype=np.float64)
    if matrix.shape != (3, 3) or not np.all(np.isfinite(matrix)):
        raise ValueError("S3 V2D membrane A must be a finite 3x3 matrix")
    matrix = 0.5 * (matrix + matrix.T)
    if float(np.linalg.eigvalsh(matrix)[0]) <= 0.0:
        raise ValueError("S3 V2D membrane A must be positive definite")
    restricted = _DRILL_PROJECTOR.T @ matrix @ _DRILL_PROJECTOR
    canonical = (
        _DRILL_INVERSE_METRIC_SQRT
        @ restricted
        @ _DRILL_INVERSE_METRIC_SQRT
    )
    value = 0.5 * float(np.linalg.eigvalsh(0.5 * (canonical + canonical.T))[0])
    if not math.isfinite(value) or value <= 0.0:
        raise ValueError("S3 V2D drill scale must be finite and positive")
    return value


class NativeParityE4PLS3V2DShellElement(ShellElement):
    """Explicit V2D candidate; no public alias or default selects it."""

    formulation_id = FORMULATION_ID
    selector = SELECTOR
    _legacy_shell_dispatch_forbidden = FORMULATION_ID
    TRI_GAUSS_POINTS_3 = HAMMER_POINTS
    TRI_GAUSS_WEIGHTS_3 = HAMMER_REFERENCE_WEIGHTS

    # These functions are the reviewed V2C source functions themselves, not
    # copied/re-authored equation implementations.
    _membrane_operator = staticmethod(
        StrictFlatLinearE4PLS3V2CShellElement._membrane_operator
    )
    _pl_constraint = staticmethod(
        StrictFlatLinearE4PLS3V2CShellElement._pl_constraint
    )
    _operators = StrictFlatLinearE4PLS3V2CShellElement._operators

    def __init__(
        self,
        element_id: int,
        node_ids: Sequence[int],
        material_name: str = "default",
        *,
        thickness: float = 0.01,
        reference_normal: Sequence[float],
        director_polarity: int = 1,
        reference_surface_offset: float = 0.0,
        material_direction: Optional[Sequence[float]] = None,
        material_angle_deg: float = 0.0,
        shell_section: Optional[Any] = None,
    ) -> None:
        if type(element_id) is not int:
            raise TypeError("S3 V2D element_id must be an exact integer")
        owned_nodes = tuple(node_ids)
        if (
            len(owned_nodes) != 3
            or not all(type(node_id) is int for node_id in owned_nodes)
            or len(set(owned_nodes)) != 3
        ):
            raise ValueError("S3 V2D requires three distinct exact-integer nodes")
        if type(director_polarity) is not int or director_polarity != 1:
            raise NativeParityCapabilityError(
                "S3 V2D director reversal is pending its dedicated native-state gate"
            )
        if _real_scalar(reference_surface_offset, "reference_surface_offset") != 0.0:
            raise NativeParityCapabilityError(
                "S3 V2D reference_surface_offset is pending its dedicated work gate"
            )
        thickness_value = _real_scalar(thickness, "thickness")
        if thickness_value <= 0.0:
            raise ValueError("S3 V2D thickness must be positive")
        normal = _immutable_vector(reference_normal, "reference_normal")
        super().__init__(
            element_id,
            owned_nodes,
            material_name,
            thickness=thickness_value,
            drilling_stabilization=0.0,
            reduced_integration=False,
            hourglass_stabilization=0.0,
            material_direction=(
                None
                if material_direction is None
                else np.asarray(material_direction, dtype=np.float64)
            ),
            material_angle_deg=material_angle_deg,
            shell_section=shell_section,
        )
        self.node_ids = owned_nodes
        self.reference_normal = normal
        self.director_polarity = 1
        self.reference_surface_offset = 0.0

    @property
    def physical_reference_director(self) -> np.ndarray:
        return np.asarray(self.reference_normal, dtype=np.float64).copy()

    @property
    def gauss_points(self) -> np.ndarray:
        return HAMMER_POINTS

    @property
    def gauss_weights(self) -> np.ndarray:
        return HAMMER_REFERENCE_WEIGHTS

    @property
    def shear_gauss_points(self) -> np.ndarray:
        return HAMMER_POINTS

    @property
    def shear_gauss_weights(self) -> np.ndarray:
        return HAMMER_REFERENCE_WEIGHTS

    def capability_matrix(self) -> Dict[str, str]:
        return dict(CAPABILITY_MATRIX)

    def _material_angle(self, local_frame: np.ndarray) -> float:
        """Resolve the physical material direction without legacy mechanics."""

        angle = math.radians(float(self.material_angle_deg))
        if self.material_direction is None:
            return angle
        frame = np.asarray(local_frame, dtype=np.float64).reshape(3, 3)
        direction = np.asarray(self.material_direction, dtype=np.float64)
        components = np.asarray(
            (float(direction @ frame[:, 0]), float(direction @ frame[:, 1])),
            dtype=np.float64,
        )
        norm = float(np.linalg.norm(components))
        if norm <= 1.0e-10 * max(float(np.linalg.norm(direction)), 1.0):
            raise ValueError("S3 V2D material_direction is parallel to the normal")
        return float(math.atan2(components[1], components[0]) + angle)

    def _generalized_section_in_frame(self, local_frame: np.ndarray) -> Any:
        if self.shell_section is None:
            return None
        return self.shell_section.rotated(self._material_angle(local_frame))

    @staticmethod
    def _unsupported(operation: str) -> None:
        raise NativeParityCapabilityError(
            f"S3 V2D capability {operation!r} is pending a successor gate"
        )

    def _validate_configuration(self) -> None:
        if type(self) is not NativeParityE4PLS3V2DShellElement:
            raise NativeParityCapabilityError("S3 V2D requires its exact production class")
        if (
            self.formulation_id != FORMULATION_ID
            or self.selector != SELECTOR
            or self._legacy_shell_dispatch_forbidden != FORMULATION_ID
        ):
            raise NativeParityCapabilityError("S3 V2D class identity changed")
        if (
            type(self.node_ids) is not tuple
            or len(self.node_ids) != 3
            or len(set(self.node_ids)) != 3
        ):
            raise ValueError("S3 V2D connectivity authority changed")
        if self.drilling_stabilization != 0.0 or self.hourglass_stabilization != 0.0:
            raise NativeParityCapabilityError("S3 V2D forbids legacy stabilizations")
        if self.reduced_integration is not False:
            raise NativeParityCapabilityError("S3 V2D quadrature authority changed")
        normal = self.reference_normal
        if (
            type(normal) is not np.ndarray
            or normal.shape != (3,)
            or normal.dtype != np.dtype(np.float64)
            or normal.flags.writeable
            or not np.all(np.isfinite(normal))
        ):
            raise ValueError("S3 V2D reference-normal authority changed")
        if not math.isclose(
            float(np.linalg.norm(normal)),
            1.0,
            rel_tol=0.0,
            abs_tol=8.0 * np.finfo(np.float64).eps,
        ):
            raise ValueError("S3 V2D reference normal is not unit length")

    def _coordinates(self, mesh: FEMesh) -> np.ndarray:
        if type(mesh) is not FEMesh:
            raise TypeError("S3 V2D requires an exact FEMesh")
        coordinates = np.empty((3, 3), dtype=np.float64)
        for index, node_id in enumerate(self.node_ids):
            node = mesh.get_node(node_id)
            if node is None:
                raise ValueError(f"S3 V2D references missing node {node_id}")
            value = np.asarray(node.coords(), dtype=np.float64)
            if value.shape != (3,) or not np.all(np.isfinite(value)):
                raise ValueError(f"S3 V2D node {node_id} has invalid coordinates")
            coordinates[index] = value
        return coordinates

    def _validate_model_scope(self, mesh: FEMesh) -> None:
        if type(mesh) is not FEMesh:
            raise TypeError("S3 V2D requires an exact FEMesh")
        elements = object.__getattribute__(mesh, "__dict__").get("elements")
        if not elements:
            return
        if not isinstance(elements, dict) or elements.get(self.element_id) is not self:
            raise NativeParityCapabilityError(
                "S3 V2D evaluation requires exact model-registry ownership"
            )
        allowed = (
            NativeParityE4PLS3V2DShellElement,
            StrictFlatLinearE4PLS3V2CShellElement,
            QualifiedE4PLShellElement,
        )
        if any(type(element) not in allowed for element in elements.values()):
            raise NativeParityCapabilityError(
                "S3 V2D mixed scope admits only exact V2D, accepted V2C and qualified Q4"
            )

    def _geometry(self, mesh: FEMesh) -> Dict[str, Any]:
        self._validate_configuration()
        self._validate_model_scope(mesh)
        external = self._coordinates(mesh)
        normal = np.asarray(self.reference_normal, dtype=np.float64)
        edge_12 = external[1] - external[0]
        edge_13 = external[2] - external[0]
        edge_scale = max(
            float(edge_12 @ edge_12),
            float(edge_13 @ edge_13),
            float((external[2] - external[1]) @ (external[2] - external[1])),
            np.finfo(np.float64).tiny,
        )
        cross = np.cross(edge_12, edge_13)
        doubled_area = float(np.linalg.norm(cross))
        if doubled_area <= _DEGENERACY_FACTOR * edge_scale:
            raise ValueError("S3 V2D requires a nondegenerate flat triangle")
        tangency = max(abs(float(edge_12 @ normal)), abs(float(edge_13 @ normal)))
        if tangency > _NORMAL_TOLERANCE * math.sqrt(edge_scale):
            raise NativeParityCapabilityError("S3 V2D reference normal is not facet-normal")
        signed = float(cross @ normal)
        if abs(signed) < (1.0 - _NORMAL_TOLERANCE) * doubled_area:
            raise NativeParityCapabilityError("S3 V2D reference normal is incompatible")
        order: Tuple[int, int, int] = (0, 1, 2) if signed > 0.0 else (0, 2, 1)
        coordinates = external[np.asarray(order, dtype=np.intp)]
        x_axis = coordinates[1] - coordinates[0]
        x_axis /= float(np.linalg.norm(x_axis))
        y_axis = np.cross(normal, x_axis)
        y_axis /= float(np.linalg.norm(y_axis))
        frame = np.column_stack((x_axis, y_axis, normal))
        relative = coordinates - coordinates[0]
        local = np.column_stack((relative @ x_axis, relative @ y_axis))
        jacobian = np.asarray(
            (
                (local[1, 0] - local[0, 0], local[2, 0] - local[0, 0]),
                (local[1, 1] - local[0, 1], local[2, 1] - local[0, 1]),
            ),
            dtype=np.float64,
        )
        determinant = float(np.linalg.det(jacobian))
        if not math.isfinite(determinant) or determinant <= 0.0:
            raise RuntimeError("S3 V2D failed to construct a positive local chart")
        natural_gradients = np.asarray(
            ((-1.0, -1.0), (1.0, 0.0), (0.0, 1.0)), dtype=np.float64
        )
        gradients = natural_gradients @ np.linalg.inv(jacobian)
        permutation = _block_permutation(order)
        local_from_external = _local_component_transform(frame) @ permutation
        return {
            "external_coordinates": external,
            "internal_order": order,
            "local_coordinates": local,
            "shape_gradients": gradients,
            "area": 0.5 * determinant,
            "frame": frame,
            "local_from_external": local_from_external,
        }

    def _constitutive(self, material: Material) -> Dict[str, Any]:
        if self.shell_section is not None:
            raise NativeParityCapabilityError(
                "S3 V2D generalized sections use the native station integrator"
            )
        # The exact reviewed V2C function supplies the elastic matrices and
        # binary64 operation ordering required by the overlap certificate.
        return StrictFlatLinearE4PLS3V2CShellElement._constitutive(self, material)

    def _native_section(self, geometry: Mapping[str, Any]) -> Dict[str, np.ndarray]:
        section = self._generalized_section_in_frame(
            np.asarray(geometry["frame"], dtype=np.float64)
        )
        if section is None:
            raise NativeParityCapabilityError("S3 V2D native section is absent")
        matrices = {
            "A": np.asarray(section.A, dtype=np.float64),
            "B": np.asarray(section.B, dtype=np.float64),
            "D": np.asarray(section.D, dtype=np.float64),
            "H": np.asarray(section.As, dtype=np.float64),
        }
        if not all(np.all(np.isfinite(value)) for value in matrices.values()):
            raise ValueError("S3 V2D generalized section is nonfinite")
        return matrices

    @staticmethod
    def _globalize(matrix: np.ndarray, transform: np.ndarray) -> np.ndarray:
        made = transform.T @ matrix @ transform
        return 0.5 * (made + made.T)

    def _native_generalized_components(
        self, mesh: FEMesh, material: Material
    ) -> Dict[str, Any]:
        del material  # A generalized section is the complete constitutive authority.
        geometry = self._geometry(mesh)
        section = self._native_section(geometry)
        operators = self._operators(geometry, section)
        area = float(geometry["area"])
        weight = area / 3.0
        membrane_local = operators["B_m"].T @ section["A"] @ operators["B_m"] * area
        bending_local = np.zeros((18, 18), dtype=np.float64)
        coupling_local = np.zeros((18, 18), dtype=np.float64)
        shear_local = np.zeros((18, 18), dtype=np.float64)
        for bending, shear in zip(operators["B_b"], operators["B_s"]):
            bending_local += bending.T @ section["D"] @ bending * weight
            coupling_local += (
                operators["B_m"].T @ section["B"] @ bending
                + bending.T @ section["B"].T @ operators["B_m"]
            ) * weight
            shear_local += shear.T @ section["H"] @ shear * weight
        bending_sum = float(sum(bending_local[i, i] for i in _ROTATIONAL_INDICES))
        shear_sum = float(sum(shear_local[i, i] for i in _ROTATIONAL_INDICES))
        if bending_sum <= 0.0 or shear_sum <= 0.0:
            raise ValueError("S3 V2D native MIN3 relaxation traces must be positive")
        psi_hat = bending_sum / shear_sum
        phi_squared = CBMIN3 * psi_hat / (1.0 + CBMIN3 * psi_hat)
        if not math.isfinite(phi_squared) or not 0.0 < phi_squared <= 1.0:
            raise ValueError("S3 V2D native MIN3 relaxation is invalid")
        shear_local *= phi_squared
        barycentric_mass = (area / 12.0) * np.asarray(
            ((2.0, 1.0, 1.0), (1.0, 2.0, 1.0), (1.0, 1.0, 2.0)),
            dtype=np.float64,
        )
        drill_scale = _invariant_drill_scale(section["A"])
        constraint = operators["C"]
        pl_local = drill_scale * constraint.T @ barycentric_mass @ constraint
        physical_local = membrane_local + coupling_local + bending_local + shear_local
        total_local = physical_local + pl_local
        transform = np.asarray(geometry["local_from_external"], dtype=np.float64)
        membrane = self._globalize(membrane_local, transform)
        coupling = self._globalize(coupling_local, transform)
        bending = self._globalize(bending_local, transform)
        shear = self._globalize(shear_local, transform)
        physical = self._globalize(physical_local, transform)
        pl = self._globalize(pl_local, transform)
        total = self._globalize(total_local, transform)
        return {
            "membrane": membrane,
            "membrane_bending_coupling": coupling,
            "bending": bending,
            "shear": shear,
            "physical": physical,
            "pl": pl,
            "numerical": pl.copy(),
            "hourglass": np.zeros((18, 18), dtype=np.float64),
            "total": total,
            "frame": np.asarray(geometry["frame"], dtype=np.float64).copy(),
            "area": area,
            "phi": np.asarray(operators["phi"], dtype=np.float64).copy(),
            "phi_squared": phi_squared,
            "drill_scale": drill_scale,
            "quadrature_authority_id": "S3_V2D_MIN3_HAMMER3_V1",
            "pl_completion_policy_id": PL_COMPLETION_POLICY_ID,
            "native_section_policy_id": NATIVE_SECTION_POLICY_ID,
            "relaxation_authority_sha256": RELAXATION_AUTHORITY_SHA256,
        }

    def compute_stiffness_components(
        self, mesh: FEMesh, material: Material
    ) -> Mapping[str, Any]:
        self._validate_configuration()
        if self.shell_section is None:
            return StrictFlatLinearE4PLS3V2CShellElement.compute_stiffness_components(
                self, mesh, material
            )
        return self._native_generalized_components(mesh, material)

    def compute_stiffness_matrix(self, mesh: FEMesh, material: Material) -> np.ndarray:
        return np.asarray(
            self.compute_stiffness_components(mesh, material)["total"],
            dtype=np.float64,
        ).copy()

    def compute_internal_forces(
        self, mesh: FEMesh, displacements: np.ndarray, material: Material
    ) -> np.ndarray:
        vector = self._get_element_displacements(mesh, displacements)
        if vector.shape != (18,) or not np.all(np.isfinite(vector)):
            raise ValueError("S3 V2D displacement must resolve to a finite 18-vector")
        return self.compute_stiffness_matrix(mesh, material) @ vector

    def compute_variational_resultants(
        self, mesh: FEMesh, displacements: np.ndarray, material: Material
    ) -> Dict[str, Any]:
        if self.shell_section is None:
            return StrictFlatLinearE4PLS3V2CShellElement.compute_variational_resultants(
                self, mesh, displacements, material
            )
        geometry = self._geometry(mesh)
        section = self._native_section(geometry)
        operators = self._operators(geometry, section)
        phi_squared = float(self.compute_stiffness_components(mesh, material)["phi_squared"])
        vector = self._get_element_displacements(mesh, displacements)
        local_vector = np.asarray(geometry["local_from_external"]) @ vector
        epsilon = np.broadcast_to(operators["B_m"] @ local_vector, (3, 3)).copy()
        kappa = np.einsum("gij,j->gi", operators["B_b"], local_vector)
        gamma = np.einsum("gij,j->gi", operators["B_s"], local_vector)
        membrane_resultants = epsilon @ section["A"].T + kappa @ section["B"].T
        bending_resultants = epsilon @ section["B"] + kappa @ section["D"].T
        shear_resultants = phi_squared * gamma @ section["H"].T
        order = tuple(int(value) for value in geometry["internal_order"])

        def external_order(values: np.ndarray) -> np.ndarray:
            made = np.empty_like(values)
            for internal, external in enumerate(order):
                made[external] = values[internal]
            return made

        barycentric = np.column_stack(
            (
                1.0 - HAMMER_POINTS[:, 0] - HAMMER_POINTS[:, 1],
                HAMMER_POINTS[:, 0],
                HAMMER_POINTS[:, 1],
            )
        )
        return {
            "recovery_scope": RESULTANT_POLICY_ID,
            "qualified_recovery": False,
            "physical_stress_available": False,
            "numerical_fields_excluded": True,
            "membrane_strain": external_order(epsilon),
            "curvature": external_order(kappa),
            "transverse_shear_strain": external_order(gamma),
            "membrane_resultants": external_order(membrane_resultants),
            "bending_resultants": external_order(bending_resultants),
            "transverse_shear_resultants": external_order(shear_resultants),
            "min3_relaxation_phi_squared": phi_squared,
            "hammer_points": np.asarray(HAMMER_POINTS, dtype=np.float64).copy(),
            "external_barycentric_coordinates": barycentric,
            "physical_station_coordinates": barycentric
            @ np.asarray(geometry["external_coordinates"], dtype=np.float64),
            "internal_order": order,
            "physical_weights": np.full(3, float(geometry["area"]) / 3.0),
            "frame": np.asarray(geometry["frame"], dtype=np.float64).copy(),
            "resultant_policy_id": RESULTANT_POLICY_ID,
            "native_section_policy_id": NATIVE_SECTION_POLICY_ID,
        }

    def compute_stresses(
        self,
        mesh: FEMesh,
        displacements: np.ndarray,
        material: Material,
        return_global: bool = False,
    ) -> Dict[str, Any]:
        if return_global:
            raise NativeParityCapabilityError(
                "S3 V2D global tensor recovery is pending a successor gate"
            )
        return {
            **self.compute_variational_resultants(mesh, displacements, material),
            "formulation_id": FORMULATION_ID,
            "implementation_id": IMPLEMENTATION_ID,
            "recovery_scope": "PHYSICAL_LOCAL_RESULTANTS_ONLY",
        }

    def compute_dead_transverse_pressure_load(self, mesh: FEMesh, pressure: Any) -> np.ndarray:
        return StrictFlatLinearE4PLS3V2CShellElement.compute_dead_transverse_pressure_load(
            self, mesh, pressure
        )

    def compute_mass_matrix(self, mesh: FEMesh, material: Material, **kwargs: Any) -> np.ndarray:
        if kwargs:
            raise NativeParityCapabilityError("S3 V2D mass gate accepts no options")
        if self.shell_section is None:
            return StrictFlatLinearE4PLS3V2CShellElement.compute_mass_matrix(
                self, mesh, material
            )
        geometry = self._geometry(mesh)
        section = self._generalized_section_in_frame(geometry["frame"])
        assert section is not None
        if section.mass_per_area is None:
            density = _real_scalar(getattr(material, "density", None), "density")
            mass_per_area = density * self.thickness
        else:
            mass_per_area = _real_scalar(section.mass_per_area, "mass_per_area")
        if mass_per_area <= 0.0:
            raise ValueError("S3 V2D mass_per_area must be positive")
        nodal_mass = mass_per_area * float(geometry["area"]) / 3.0
        local = np.zeros((18, 18), dtype=np.float64)
        for node in range(3):
            for axis in range(3):
                local[6 * node + axis, 6 * node + axis] = nodal_mass
        transform = np.asarray(geometry["local_from_external"], dtype=np.float64)
        return self._globalize(local, transform)

    def compute_nonlinear_response(
        self,
        mesh: FEMesh,
        material: Material,
        u_elem: np.ndarray,
        state: Optional[Any] = None,
        num_layers: int = 5,
        tangent: bool = True,
    ) -> Tuple[np.ndarray, Optional[np.ndarray], Optional[Any]]:
        del mesh, material, u_elem, state, num_layers, tangent
        self._unsupported("nonlinear_geometry")

    def init_nonlinear_state(self, num_layers: int) -> Dict[str, Any]:
        del num_layers
        self._unsupported("nonlinear_state")

    def to_dict(self) -> Dict[str, Any]:
        self._validate_configuration()
        return {
            "element_id": int(self.element_id),
            "formulation_id": FORMULATION_ID,
            "formulation_schema": FORMULATION_SCHEMA,
            "implementation_id": IMPLEMENTATION_ID,
            "material_name": self.material_name,
            "node_ids": [int(value) for value in self.node_ids],
            "reference_normal": np.asarray(self.reference_normal).tolist(),
            "director_polarity": 1,
            "reference_surface_offset": 0.0,
            "material_direction": (
                None
                if self.material_direction is None
                else np.asarray(self.material_direction).tolist()
            ),
            "material_angle_deg": float(self.material_angle_deg),
            "shell_section": (
                None if self.shell_section is None else self.shell_section.to_dict()
            ),
            "selector": SELECTOR,
            "serialization_policy_id": SERIALIZATION_POLICY_ID,
            "source_selection_sha256": SOURCE_SELECTION_SHA256,
            "thickness": float(self.thickness),
            "type": type(self).__name__,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "NativeParityE4PLS3V2DShellElement":
        if cls is not NativeParityE4PLS3V2DShellElement:
            raise NativeParityCapabilityError("S3 V2D deserialization requires exact class")
        if not isinstance(payload, Mapping):
            raise TypeError("S3 V2D serialized payload must be a mapping")
        data = dict(payload)
        required = {
            "element_id",
            "formulation_id",
            "formulation_schema",
            "implementation_id",
            "material_name",
            "node_ids",
            "reference_normal",
            "director_polarity",
            "reference_surface_offset",
            "material_direction",
            "material_angle_deg",
            "shell_section",
            "selector",
            "serialization_policy_id",
            "source_selection_sha256",
            "thickness",
            "type",
        }
        if set(data) != required:
            raise ValueError("S3 V2D serialized schema keys mismatch")
        identities = {
            "formulation_id": FORMULATION_ID,
            "formulation_schema": FORMULATION_SCHEMA,
            "implementation_id": IMPLEMENTATION_ID,
            "selector": SELECTOR,
            "serialization_policy_id": SERIALIZATION_POLICY_ID,
            "source_selection_sha256": SOURCE_SELECTION_SHA256,
            "type": "NativeParityE4PLS3V2DShellElement",
        }
        if any(data[name] != value for name, value in identities.items()):
            raise ValueError("S3 V2D serialized fingerprint mismatch")
        return cls(
            data["element_id"],
            data["node_ids"],
            data["material_name"],
            thickness=data["thickness"],
            reference_normal=data["reference_normal"],
            director_polarity=data["director_polarity"],
            reference_surface_offset=data["reference_surface_offset"],
            material_direction=data["material_direction"],
            material_angle_deg=data["material_angle_deg"],
            shell_section=data["shell_section"],
        )

    def __getstate__(self) -> Dict[str, Any]:
        self._unsupported("restart")

    def __setstate__(self, state: Mapping[str, Any]) -> None:
        del state
        self._unsupported("restart")

    def __reduce_ex__(self, protocol: int) -> Any:
        del protocol
        self._unsupported("restart")


__all__ = [
    "BLOCKED_OPERATIONS",
    "CAPABILITY_MATRIX",
    "DRILL_SCALE_POLICY_ID",
    "FORMULATION_ID",
    "FORMULATION_SCHEMA",
    "IMPLEMENTATION_ID",
    "MASS_POLICY_ID",
    "NATIVE_SECTION_POLICY_ID",
    "NativeParityCapabilityError",
    "NativeParityE4PLS3V2DShellElement",
    "SELECTOR",
    "SERIALIZATION_POLICY_ID",
    "SOURCE_SELECTION_SHA256",
    "SUPPORTED_OPERATIONS",
    "V2C_OPERATOR_SHA256",
]
