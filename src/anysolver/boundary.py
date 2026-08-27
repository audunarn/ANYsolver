"""
Boundary Conditions and Load Cases

This module provides classes for defining boundary conditions and loads
for the FE model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .matrix_assembly import (
    _CAPTURE_QUALIFIED_ASSEMBLY_RUNTIME_LEASE as _CAPTURE_QUALIFIED_LOAD_RUNTIME_LEASE,
)
from .fe_core import _QualifiedMutationEpoch, _QualifiedStateMapping

if TYPE_CHECKING:
    from .fe_core import DOFManager, FEMesh, Material, Node


_SMALL = 1.0e-12


class _MeshLeaseModel:
    """Closure-private adapter for direct mesh-level load operations."""

    __slots__ = ("mesh",)

    def __init__(self, mesh: "FEMesh") -> None:
        self.mesh = mesh


def _run_with_qualified_load_runtime_lease(
    mesh: "FEMesh",
    *,
    context: str,
    operation: Callable[[Callable[..., None]], Any],
) -> Any:
    proxy = _MeshLeaseModel(mesh)
    lease = _CAPTURE_QUALIFIED_LOAD_RUNTIME_LEASE(
        proxy,
        context=f"{context} preflight",
    )

    def require(*, stage: str) -> None:
        lease(proxy, context=f"{context} {stage}")

    try:
        result = operation(require)
    except BaseException:
        require(stage="exceptional output")
        raise
    require(stage="output")
    return result


class _GravityFallbackMaterial:
    """Minimal material used when loads are assembled without model context."""

    density = 7850.0
    elastic_modulus = 210.0e9
    poisson_ratio = 0.3

    @property
    def shear_modulus(self) -> float:
        return self.elastic_modulus / (2.0 * (1.0 + self.poisson_ratio))


@dataclass
class BoundaryCondition:
    """
    Base class for boundary conditions.

    Boundary conditions constrain specific DOFs of nodes.
    """

    name: str
    node_ids: List[int]
    dof_constraints: Dict[str, float]

    def __post_init__(self):
        dof_names = ["ux", "uy", "uz", "rx", "ry", "rz"]
        self._dof_indices = {}
        for dof_name, value in self.dof_constraints.items():
            if dof_name in dof_names:
                self._dof_indices[dof_name] = dof_names.index(dof_name)

    def apply(self, dof_manager: "DOFManager"):
        """Apply this boundary condition to the DOF manager."""
        for node_id in self.node_ids:
            node_dofs = dof_manager.get_node_dofs(node_id)
            if not node_dofs:
                continue
            for dof_name, value in self.dof_constraints.items():
                if dof_name in self._dof_indices:
                    local_idx = self._dof_indices[dof_name]
                    global_dof = node_dofs[local_idx]
                    dof_manager.constrain_dof(global_dof)

    def get_constrained_dofs(self, dof_manager: "DOFManager") -> List[Tuple[int, float]]:
        """Get list of (global_dof, prescribed_value) pairs."""
        constrained = []
        for node_id in self.node_ids:
            node_dofs = dof_manager.get_node_dofs(node_id)
            if not node_dofs:
                continue
            for dof_name, value in self.dof_constraints.items():
                if dof_name in self._dof_indices:
                    local_idx = self._dof_indices[dof_name]
                    global_dof = node_dofs[local_idx]
                    constrained.append((global_dof, value))
        return constrained


@dataclass
class FixedSupport(BoundaryCondition):
    """Fully fixed support: all DOFs constrained to zero."""

    def __init__(self, name: str, node_ids: List[int]):
        dof_constraints = {dof: 0.0 for dof in ["ux", "uy", "uz", "rx", "ry", "rz"]}
        super().__init__(name, node_ids, dof_constraints)


@dataclass
class PinnedSupport(BoundaryCondition):
    """Pinned support: translational DOFs fixed, rotations free."""

    def __init__(self, name: str, node_ids: List[int]):
        dof_constraints = {dof: 0.0 for dof in ["ux", "uy", "uz"]}
        super().__init__(name, node_ids, dof_constraints)


@dataclass
class RollerSupport(BoundaryCondition):
    """Roller support constraining selected translational DOFs."""

    def __init__(self, name: str, node_ids: List[int], constrained_directions: Optional[List[str]] = None):
        if constrained_directions is None:
            constrained_directions = ["uy", "uz"]
        dof_constraints = {dof: 0.0 for dof in constrained_directions}
        super().__init__(name, node_ids, dof_constraints)


@dataclass
class SymmetryBC(BoundaryCondition):
    """Symmetry boundary condition in a global coordinate plane."""

    def __init__(self, name: str, node_ids: List[int], symmetry_plane: str = "xy"):
        if symmetry_plane == "xy":
            dof_constraints = {"uz": 0.0, "rx": 0.0, "ry": 0.0}
        elif symmetry_plane == "xz":
            dof_constraints = {"uy": 0.0, "rx": 0.0, "rz": 0.0}
        elif symmetry_plane == "yz":
            dof_constraints = {"ux": 0.0, "ry": 0.0, "rz": 0.0}
        else:
            dof_constraints = {}
        super().__init__(name, node_ids, dof_constraints)


@dataclass
class LoadCase:
    """
    Load case for the FE model.

    Contains nodal loads, element loads, pressure loads and optional gravity.
    Pressure loads on shell elements are assembled as consistent nodal loads by
    Gauss integration over the element surface, instead of equal area shares.
    Pressure is a reference-configuration dead load by default.
    ``follower_pressure=True`` switches every pressure in the load case to the
    current-area formulation used by nonlinear static and arc-length analysis.
    """

    name: str
    nodal_loads: Dict[int, np.ndarray] = field(default_factory=dict)
    element_loads: Dict[int, np.ndarray] = field(default_factory=dict)
    pressure_loads: Dict[int, float] = field(default_factory=dict)
    gravity: Optional[np.ndarray] = None
    added_node_masses: Dict[int, float] = field(default_factory=dict)
    follower_pressure: bool = False

    def __post_init__(self) -> None:
        """Install one monotonic token across the mutable load policy.

        The mappings remain public ``dict`` subclasses with ordinary mapping
        semantics.  Their shared token exists only so a qualified operation
        can reject supported mutate-then-restore changes after admission.
        """

        token = _QualifiedMutationEpoch()
        object.__setattr__(self, "_qualified_load_state_token", token)
        namespace = object.__getattribute__(self, "__dict__")
        for name in (
            "nodal_loads",
            "element_loads",
            "pressure_loads",
            "added_node_masses",
        ):
            value = dict.get(namespace, name)
            if type(value) in {dict, _QualifiedStateMapping}:
                object.__setattr__(
                    self,
                    name,
                    _QualifiedStateMapping(
                        tuple(dict.items(value)),
                        token,
                        "detached",
                    ),
                )

    def __setattr__(self, name: str, value: Any) -> None:
        """Advance the private load-policy token on supported replacement."""

        namespace = object.__getattribute__(self, "__dict__")
        token = dict.get(namespace, "_qualified_load_state_token")
        if (
            type(token) is _QualifiedMutationEpoch
            and name
            in {
                "nodal_loads",
                "element_loads",
                "pressure_loads",
                "added_node_masses",
            }
            and type(value) in {dict, _QualifiedStateMapping}
        ):
            value = _QualifiedStateMapping(
                tuple(dict.items(value)),
                token,
                "detached",
            )
        object.__setattr__(self, name, value)
        if (
            type(token) is _QualifiedMutationEpoch
            and name
            in {
                "nodal_loads",
                "element_loads",
                "pressure_loads",
                "added_node_masses",
                "gravity",
                "follower_pressure",
            }
        ):
            token[0] = int(list.__getitem__(token, 0)) + 1

    def add_nodal_load(
        self,
        node_id: int,
        load_vector: Optional[np.ndarray] = None,
        forces: Optional[np.ndarray] = None,
        moments: Optional[np.ndarray] = None,
    ):
        """
        Add a nodal load.

        Args:
            node_id: Node ID to apply load to.
            load_vector: [Fx, Fy, Fz] or [Fx, Fy, Fz, Mx, My, Mz].
            forces: Alternative force vector [Fx, Fy, Fz].
            moments: Optional moment vector [Mx, My, Mz].
        """
        if load_vector is not None:
            load_vector = np.asarray(load_vector, dtype=float)
            if len(load_vector) == 6:
                load = load_vector.copy()
            else:
                if moments is None:
                    moments = np.zeros(3)
                load = np.concatenate([load_vector[:3], np.asarray(moments, dtype=float)[:3]])
        elif forces is not None:
            if moments is None:
                moments = np.zeros(3)
            load = np.concatenate([np.asarray(forces, dtype=float)[:3], np.asarray(moments, dtype=float)[:3]])
        elif moments is not None:
            load = np.concatenate([np.zeros(3), np.asarray(moments, dtype=float)[:3]])
        else:
            load = np.zeros(6)

        if node_id in self.nodal_loads:
            self.nodal_loads[node_id] += load
        else:
            self.nodal_loads[node_id] = load

    def add_pressure_load(self, element_id: int, pressure: float):
        """
        Add a pressure load to a shell element.

        Positive pressure follows the element normal as defined by the element
        node ordering and natural-coordinate surface Jacobian.

        Pressure is a dead load by default.  Set ``follower_pressure=True`` on
        the load case to integrate it over the current nodal interpolation
        surface during a
        nonlinear solve.  The flag is load-case-wide so one proportional load
        pattern cannot accidentally mix reference- and current-configuration
        pressure semantics.
        """
        self.pressure_loads[element_id] = float(pressure)

    def set_gravity(self, gx: float = 0.0, gy: float = 0.0, gz: float = -9.81):
        """Set gravity acceleration."""
        self.gravity = np.array([gx, gy, gz], dtype=float)

    def set_acceleration(self, ax: float = 0.0, ay: float = 0.0, az: float = 0.0):
        """Set a body-load acceleration field in x/y/z.

        Produces the consistent inertial load ``M a`` over the structural mass
        (element mass matrices) plus ``m_i a`` for any added nodal masses.  This
        is the same mechanism as :meth:`set_gravity`; use it to describe design
        accelerations (e.g. ship motions) in an arbitrary direction.
        """
        self.gravity = np.array([ax, ay, az], dtype=float)

    def add_node_mass(self, node_id: int, mass: float):
        """Add a lumped translational mass at a node.

        The added mass contributes an inertial load ``mass * acceleration`` at
        the node's translational DOFs whenever an acceleration/gravity field is
        set.  Use the frontend edge/ring helpers to distribute a total mass
        along a plate edge or a cylinder top/bottom ring.
        """
        mass = float(mass)
        if mass == 0.0:
            return
        self.added_node_masses[int(node_id)] = self.added_node_masses.get(int(node_id), 0.0) + mass

    def add_distributed_edge_mass(self, node_ids: Sequence[int], total_mass: float):
        """Distribute ``total_mass`` equally over the given nodes."""
        node_ids = [int(node_id) for node_id in node_ids]
        if not node_ids or float(total_mass) == 0.0:
            return
        share = float(total_mass) / float(len(node_ids))
        for node_id in node_ids:
            self.add_node_mass(node_id, share)

    @staticmethod
    def _surface_jacobian_and_normal(coords: np.ndarray, dN_dxi: np.ndarray, dN_deta: np.ndarray) -> Tuple[float, np.ndarray]:
        """
        Compute surface Jacobian magnitude and unit normal from shape derivatives.
        """
        tangent_xi = coords.T @ dN_dxi
        tangent_eta = coords.T @ dN_deta
        normal_raw = np.array(
            [
                tangent_xi[1] * tangent_eta[2] - tangent_xi[2] * tangent_eta[1],
                tangent_xi[2] * tangent_eta[0] - tangent_xi[0] * tangent_eta[2],
                tangent_xi[0] * tangent_eta[1] - tangent_xi[1] * tangent_eta[0],
            ]
        )
        det_j = float(np.linalg.norm(normal_raw))
        if det_j < _SMALL:
            return 0.0, np.array([0.0, 0.0, 1.0])
        return det_j, normal_raw / det_j

    @staticmethod
    def _fallback_lumped_pressure_load(
        element,
        mesh: "FEMesh",
        pressure: float,
        coords: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Fallback for unsupported element topologies.

        This keeps old behaviour available for non-shell or future custom elements,
        but all 4/8-node shell elements should use the consistent path.
        """
        if coords is None:
            coords = element.get_node_coordinates(mesh)
        coords = np.asarray(coords, dtype=float)
        num_nodes = len(element.node_ids)
        f_elem = np.zeros(num_nodes * 6)
        if num_nodes < 3:
            return f_elem

        if num_nodes in (4, 8):
            tri1_area = 0.5 * np.linalg.norm(np.cross(coords[1] - coords[0], coords[2] - coords[0]))
            tri2_area = 0.5 * np.linalg.norm(np.cross(coords[0] - coords[2], coords[3] - coords[2]))
            area = tri1_area + tri2_area
        else:
            area = 0.5 * np.linalg.norm(np.cross(coords[1] - coords[0], coords[2] - coords[0]))

        normal_raw = np.cross(coords[1] - coords[0], coords[2] - coords[0])
        normal_norm = np.linalg.norm(normal_raw)
        normal = normal_raw / normal_norm if normal_norm > _SMALL else np.array([0.0, 0.0, 1.0])
        nodal_force = pressure * area / max(num_nodes, 1) * normal
        for i in range(num_nodes):
            f_elem[i * 6:i * 6 + 3] += nodal_force
        return f_elem

    @staticmethod
    def _skew(vector: np.ndarray) -> np.ndarray:
        """Return ``[vector]_x`` such that ``[vector]_x @ x = vector x x``."""
        x, y, z = np.asarray(vector, dtype=float).reshape(3)
        return np.array(
            [
                [0.0, -z, y],
                [z, 0.0, -x],
                [-y, x, 0.0],
            ],
            dtype=float,
        )

    @staticmethod
    def _current_element_coordinates(
        element,
        mesh: "FEMesh",
        displacements: Optional[np.ndarray],
    ) -> np.ndarray:
        """Return nodal interpolation-surface coordinates after translations."""
        coords = np.asarray(element.get_node_coordinates(mesh), dtype=float).copy()
        if displacements is None:
            return coords
        u = np.asarray(displacements, dtype=float).reshape(-1)
        for local_index, node_id in enumerate(element.node_ids):
            node = mesh.get_node(int(node_id))
            if node is None:
                continue
            translational_dofs = np.asarray(node.dofs[:3], dtype=np.intp)
            if translational_dofs.size == 3 and int(np.max(translational_dofs)) < u.size:
                coords[local_index] += u[translational_dofs]
        return coords

    def _consistent_pressure_load(
        self,
        element,
        mesh: "FEMesh",
        pressure: float,
        coords: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """
        Assemble a consistent element pressure vector.

        For a shell element with shape functions N_i, the translational nodal
        load is:

            f_i = integral_A N_i * p * n dA

        When ``coords`` are current nodal interpolation-surface coordinates this is a follower
        load.  No independent rotational pressure moments are introduced:
        pressure virtual work is conjugate to interpolation-surface translations.
        """
        if not hasattr(element, "compute_shape_functions") or not hasattr(element, "gauss_points"):
            return self._fallback_lumped_pressure_load(element, mesh, pressure, coords)

        if coords is None:
            coords = element.get_node_coordinates(mesh)
        coords = np.asarray(coords, dtype=float)
        num_nodes = len(element.node_ids)
        f_elem = np.zeros(num_nodes * 6)
        gauss_points = getattr(element, "gauss_points")
        gauss_weights = getattr(element, "gauss_weights")
        orientation_provider = getattr(
            element, "sheet_area_orientation_sign", None
        )
        orientation_sign = (
            float(orientation_provider(mesh))
            if callable(orientation_provider)
            else 1.0
        )
        if orientation_sign not in (-1.0, 1.0):
            raise ValueError("shell sheet area orientation sign must be -1 or +1")

        for (xi, eta), weight in zip(gauss_points, gauss_weights):
            N, dN_dxi, dN_deta = element.compute_shape_functions(float(xi), float(eta))
            tangent_xi = coords.T @ dN_dxi
            tangent_eta = coords.T @ dN_deta
            area_vector = orientation_sign * np.cross(tangent_xi, tangent_eta)
            if float(np.linalg.norm(area_vector)) < _SMALL:
                continue
            for i in range(num_nodes):
                f_elem[i * 6:i * 6 + 3] += N[i] * pressure * area_vector * float(weight)
        return f_elem

    def _consistent_pressure_tangent(
        self,
        element,
        mesh: "FEMesh",
        pressure: float,
        coords: Optional[np.ndarray] = None,
    ) -> np.ndarray:
        """Return the exact current-area follower-pressure load tangent.

        For ``f_i = integral N_i p (a_xi x a_eta) dxi deta``, the 3x3 block
        derivative with respect to node ``j`` is

        ``p N_i (-N_j,xi [a_eta]_x + N_j,eta [a_xi]_x)``.

        The matrix is generally nonsymmetric for an open pressure patch.  It is
        the derivative of the external force, so equilibrium Newton systems use
        ``K_internal - K_external``.
        """
        if not hasattr(element, "compute_shape_functions") or not hasattr(element, "gauss_points"):
            raise ValueError(
                f"Follower pressure requires a shell interpolation with shape functions; "
                f"element {getattr(element, 'element_id', '?')} is unsupported."
            )

        if coords is None:
            coords = element.get_node_coordinates(mesh)
        coords = np.asarray(coords, dtype=float)
        num_nodes = len(element.node_ids)
        tangent = np.zeros((num_nodes * 6, num_nodes * 6), dtype=float)
        gauss_points = getattr(element, "gauss_points")
        gauss_weights = getattr(element, "gauss_weights")
        orientation_provider = getattr(
            element, "sheet_area_orientation_sign", None
        )
        orientation_sign = (
            float(orientation_provider(mesh))
            if callable(orientation_provider)
            else 1.0
        )
        if orientation_sign not in (-1.0, 1.0):
            raise ValueError("shell sheet area orientation sign must be -1 or +1")

        for (xi, eta), weight in zip(gauss_points, gauss_weights):
            N, dN_dxi, dN_deta = element.compute_shape_functions(float(xi), float(eta))
            tangent_xi = coords.T @ dN_dxi
            tangent_eta = coords.T @ dN_deta
            if float(np.linalg.norm(np.cross(tangent_xi, tangent_eta))) < _SMALL:
                continue
            skew_xi = self._skew(tangent_xi)
            skew_eta = self._skew(tangent_eta)
            scale = orientation_sign * float(pressure) * float(weight)
            for i in range(num_nodes):
                row = slice(6 * i, 6 * i + 3)
                for j in range(num_nodes):
                    col = slice(6 * j, 6 * j + 3)
                    tangent[row, col] += (
                        scale
                        * float(N[i])
                        * (-float(dN_dxi[j]) * skew_eta + float(dN_deta[j]) * skew_xi)
                    )
        return tangent

    def _consistent_gravity_load(
        self,
        element,
        mesh: "FEMesh",
        material: "Material",
    ) -> np.ndarray:
        """
        Assemble element body force from the element mass matrix.

        With translational acceleration a, the consistent nodal load is M a.
        Rotational acceleration components are zero for ordinary gravity.
        """
        f_elem = np.zeros(len(element.node_ids) * 6)
        if self.gravity is None:
            return f_elem

        mass_matrix = element.compute_mass_matrix(mesh, material)
        acceleration = np.zeros_like(f_elem)
        for i in range(len(element.node_ids)):
            acceleration[i * 6:i * 6 + 3] = self.gravity
        return np.asarray(mass_matrix @ acceleration, dtype=float).reshape(-1)

    def _get_load_vector_under_lease(
        self,
        mesh: "FEMesh",
        dof_manager: "DOFManager",
        material_getter: Optional[Callable[[str], "Material"]] = None,
        displacements: Optional[np.ndarray] = None,
        element_activity: Optional[object] = None,
        *,
        qualified_runtime_guard: Callable[..., None],
    ) -> np.ndarray:
        """Assemble the global load vector.

        ``displacements`` affects only pressure loads when
        :attr:`follower_pressure` is true.  Dead pressure, nodal, element and
        gravity loads retain their reference-configuration semantics.
        """
        qualified_runtime_guard(stage="load-vector preflight")
        total_dofs = dof_manager.total_dofs

        # Narrow callback-free route for the dominant mixed-qualification
        # load: a dead pressure applied to an exact all-qualified Q4/S3 mesh.
        # The outer non-renewable lease has already validated formulation,
        # mesh and numerical authority.  Capture every plain load/input value
        # before starting and do not fall back after admission.
        exact_dead_pressure = None
        load_namespace = object.__getattribute__(self, "__dict__")
        load_state_token = (
            dict.get(load_namespace, "_qualified_load_state_token")
            if type(load_namespace) is dict
            else None
        )
        follower_pressure = (
            dict.get(load_namespace, "follower_pressure")
            if type(load_namespace) is dict
            else None
        )
        gravity = (
            dict.get(load_namespace, "gravity")
            if type(load_namespace) is dict
            else None
        )
        nodal_loads = (
            dict.get(load_namespace, "nodal_loads")
            if type(load_namespace) is dict
            else None
        )
        element_loads = (
            dict.get(load_namespace, "element_loads")
            if type(load_namespace) is dict
            else None
        )
        pressure_loads = (
            dict.get(load_namespace, "pressure_loads")
            if type(load_namespace) is dict
            else None
        )
        added_node_masses = (
            dict.get(load_namespace, "added_node_masses")
            if type(load_namespace) is dict
            else None
        )
        load_mappings = (
            nodal_loads,
            element_loads,
            pressure_loads,
            added_node_masses,
        )
        mapping_namespaces = tuple(
            object.__getattribute__(mapping, "__dict__")
            if type(mapping) is _QualifiedStateMapping
            else None
            for mapping in load_mappings
        )
        load_mapping_items = tuple(
            tuple(dict.items(mapping))
            if type(mapping) is _QualifiedStateMapping
            else ()
            for mapping in load_mappings
        )
        load_state_value = (
            int(list.__getitem__(load_state_token, 0))
            if type(load_state_token) is _QualifiedMutationEpoch
            and len(load_state_token) == 1
            else None
        )
        if (
            type(self) is LoadCase
            and type(load_namespace) is dict
            and displacements is None
            and element_activity is None
            and type(load_state_token) is _QualifiedMutationEpoch
            and load_state_value is not None
            and follower_pressure is False
            and gravity is None
            and all(
                type(mapping) is _QualifiedStateMapping
                and type(namespace) is dict
                and dict.get(namespace, "_qualified_token")
                is load_state_token
                and dict.get(namespace, "_qualified_kind") == "detached"
                for mapping, namespace in zip(
                    load_mappings,
                    mapping_namespaces,
                )
            )
            and not load_mapping_items[0]
            and not load_mapping_items[1]
            and bool(load_mapping_items[2])
            and not load_mapping_items[3]
        ):
            from .e4_pl_element import (
                QualifiedE4PLShellElement,
                _Q4_QUADRATURE_CLASS_ARRAY_AUTHORITY,
            )
            from .e4_pl_s3_element import (
                MINIMUM_OWNER_NORMAL_ALIGNMENT,
                QualifiedE4PLS3ShellElement,
                _S3_QUADRATURE_POINTS,
                _S3_QUADRATURE_WEIGHTS,
            )
            from .fe_core import (
                DOFManager,
                FEMesh,
                Node,
            )

            mesh_namespace = object.__getattribute__(mesh, "__dict__")
            dof_namespace = object.__getattribute__(dof_manager, "__dict__")
            elements = (
                dict.get(mesh_namespace, "elements")
                if type(mesh_namespace) is dict
                else None
            )
            nodes = (
                dict.get(mesh_namespace, "nodes")
                if type(mesh_namespace) is dict
                else None
            )
            pressure_items = load_mapping_items[2]
            admitted = (
                type(mesh) is FEMesh
                and type(dof_manager) is DOFManager
                and type(mesh_namespace) is dict
                and type(dof_namespace) is dict
                and dict.get(mesh_namespace, "dof_manager") is dof_manager
                and type(elements) is _QualifiedStateMapping
                and type(nodes) is _QualifiedStateMapping
                and type(dict.get(dof_namespace, "_total_dofs")) is int
                and int(dict.get(dof_namespace, "_total_dofs")) == total_dofs
                and all(
                    type(element_id) is int
                    and type(pressure) in {int, float}
                    and type(pressure) is not bool
                    and np.isfinite(float(pressure))
                    and type(dict.get(elements, element_id))
                    in {QualifiedE4PLShellElement, QualifiedE4PLS3ShellElement}
                    for element_id, pressure in pressure_items
                )
            )
            if admitted:
                F_fast = np.zeros(total_dofs, dtype=float)
                for element_id, raw_pressure in pressure_items:
                    element = dict.__getitem__(elements, element_id)
                    element_namespace = object.__getattribute__(
                        element, "__dict__"
                    )
                    node_ids = (
                        dict.get(element_namespace, "node_ids")
                        if type(element_namespace) is dict
                        else None
                    )
                    expected_nodes = (
                        4
                        if type(element) is QualifiedE4PLShellElement
                        else 3
                    )
                    if (
                        type(element_namespace) is not dict
                        or type(node_ids) is not tuple
                        or len(node_ids) != expected_nodes
                        or not all(type(node_id) is int for node_id in node_ids)
                    ):
                        raise ValueError(
                            "exact qualified dead-pressure routing is incompatible"
                        )
                    coordinates = np.empty((expected_nodes, 3), dtype=float)
                    dof_rows: list[tuple[int, ...]] = []
                    for local_index, node_id in enumerate(node_ids):
                        node = dict.get(nodes, node_id)
                        if type(node) is not Node:
                            raise ValueError(
                                "exact qualified dead-pressure node is incompatible"
                            )
                        node_namespace = object.__getattribute__(node, "__dict__")
                        if type(node_namespace) is not dict:
                            raise ValueError(
                                "exact qualified dead-pressure node state is incompatible"
                            )
                        values = tuple(
                            dict.get(node_namespace, name)
                            for name in ("x", "y", "z")
                        )
                        dofs = dict.get(node_namespace, "dofs")
                        if (
                            any(
                                (
                                    type(value) not in {int, float}
                                    and not isinstance(
                                        value,
                                        (np.integer, np.floating),
                                    )
                                )
                                or isinstance(value, (bool, np.bool_))
                                or not np.isfinite(float(value))
                                for value in values
                            )
                            or type(dofs) is not list
                            or len(dofs) != 6
                            or not all(type(dof) is int for dof in dofs)
                        ):
                            raise ValueError(
                                "exact qualified dead-pressure node values are incompatible"
                            )
                        coordinates[local_index] = values
                        dof_rows.append(tuple(dofs))

                    if type(element) is QualifiedE4PLShellElement:
                        points = _Q4_QUADRATURE_CLASS_ARRAY_AUTHORITY[
                            "GAUSS_POINTS_2x2"
                        ]
                        weights = _Q4_QUADRATURE_CLASS_ARRAY_AUTHORITY[
                            "GAUSS_WEIGHTS_2x2"
                        ]
                        orientation_sign = 1.0
                    else:
                        points = _S3_QUADRATURE_POINTS
                        weights = _S3_QUADRATURE_WEIGHTS
                        reference_normal = dict.get(
                            element_namespace, "reference_normal"
                        )
                        if (
                            type(reference_normal) is not np.ndarray
                            or reference_normal.shape != (3,)
                        ):
                            raise ValueError(
                                "exact qualified S3 owner normal is incompatible"
                            )
                        raw = np.cross(
                            coordinates[1] - coordinates[0],
                            coordinates[2] - coordinates[0],
                        )
                        signed = float(raw @ reference_normal)
                        scale = float(np.linalg.norm(raw))
                        if (
                            not np.isfinite(signed)
                            or not np.isfinite(scale)
                            or scale <= np.finfo(float).tiny
                            or abs(signed)
                            <= float(MINIMUM_OWNER_NORMAL_ALIGNMENT) * scale
                        ):
                            raise ValueError(
                                "exact qualified S3 pressure orientation is unresolved"
                            )
                        orientation_sign = 1.0 if signed > 0.0 else -1.0

                    pressure = float(raw_pressure)
                    f_elem = np.zeros(expected_nodes * 6, dtype=float)
                    for (xi, eta), weight in zip(points, weights):
                        xi = float(xi)
                        eta = float(eta)
                        if expected_nodes == 4:
                            shape = 0.25 * np.asarray(
                                (
                                    (1.0 - xi) * (1.0 - eta),
                                    (1.0 + xi) * (1.0 - eta),
                                    (1.0 + xi) * (1.0 + eta),
                                    (1.0 - xi) * (1.0 + eta),
                                ),
                                dtype=float,
                            )
                            derivative_xi = 0.25 * np.asarray(
                                (
                                    -(1.0 - eta),
                                    1.0 - eta,
                                    1.0 + eta,
                                    -(1.0 + eta),
                                ),
                                dtype=float,
                            )
                            derivative_eta = 0.25 * np.asarray(
                                (
                                    -(1.0 - xi),
                                    -(1.0 + xi),
                                    1.0 + xi,
                                    1.0 - xi,
                                ),
                                dtype=float,
                            )
                        else:
                            shape = np.asarray(
                                (1.0 - xi - eta, xi, eta), dtype=float
                            )
                            derivative_xi = np.asarray(
                                (-1.0, 1.0, 0.0), dtype=float
                            )
                            derivative_eta = np.asarray(
                                (-1.0, 0.0, 1.0), dtype=float
                            )
                        tangent_xi = coordinates.T @ derivative_xi
                        tangent_eta = coordinates.T @ derivative_eta
                        area_vector = orientation_sign * np.cross(
                            tangent_xi, tangent_eta
                        )
                        if float(np.linalg.norm(area_vector)) < _SMALL:
                            continue
                        for local_index in range(len(dof_rows)):
                            start = 6 * local_index
                            f_elem[start : start + 3] += (
                                shape[local_index]
                                * pressure
                                * area_vector
                                * float(weight)
                            )
                    dof_mapping = tuple(
                        dof for dofs in dof_rows for dof in dofs
                    )
                    for local_index, dof in enumerate(dof_mapping):
                        if local_index < len(f_elem):
                            F_fast[dof] += f_elem[local_index]

                qualified_runtime_guard(stage="exact dead-pressure output")
                current_namespace = object.__getattribute__(self, "__dict__")
                if (
                    current_namespace is not load_namespace
                    or dict.get(load_namespace, "_qualified_load_state_token")
                    is not load_state_token
                    or type(load_state_token) is not _QualifiedMutationEpoch
                    or len(load_state_token) != 1
                    or int(list.__getitem__(load_state_token, 0))
                    != load_state_value
                    or dict.get(load_namespace, "follower_pressure")
                    is not follower_pressure
                    or dict.get(load_namespace, "gravity") is not gravity
                    or any(
                        dict.get(load_namespace, name) is not mapping
                        or object.__getattribute__(mapping, "__dict__")
                        is not mapping_namespace
                        or tuple(dict.items(mapping)) != expected_items
                        for name, mapping, mapping_namespace, expected_items in zip(
                            (
                                "nodal_loads",
                                "element_loads",
                                "pressure_loads",
                                "added_node_masses",
                            ),
                            load_mappings,
                            mapping_namespaces,
                            load_mapping_items,
                        )
                    )
                ):
                    raise ValueError(
                        "exact qualified dead-pressure inputs changed"
                    )
                exact_dead_pressure = F_fast

        if exact_dead_pressure is not None:
            return exact_dead_pressure

        F = np.zeros(total_dofs)

        def activity_scale(element_id: int) -> float:
            if element_activity is None:
                return 1.0
            values = element_activity.load_scales([int(element_id)])
            qualified_runtime_guard(stage="load activity observation")
            return float(np.asarray(values, dtype=float).reshape(-1)[0])

        # Nodal loads.
        for node_id, load in self.nodal_loads.items():
            node = mesh.get_node(node_id)
            if node:
                for i, dof in enumerate(node.dofs):
                    if i < len(load):
                        F[dof] += load[i]

        # User-provided element load vectors.
        for element_id, load in self.element_loads.items():
            element = mesh.get_element(element_id)
            if element is None:
                continue
            dof_mapping = element.get_dof_mapping(mesh)
            load = np.asarray(load, dtype=float)
            scale = activity_scale(int(element_id))
            for i, dof in enumerate(dof_mapping):
                if i < len(load):
                    F[dof] += scale * load[i]

        # Consistent pressure loads for shell elements.
        for element_id, pressure in self.pressure_loads.items():
            element = mesh.get_element(element_id)
            if element is None or not hasattr(element, "node_ids"):
                continue
            coords = None
            if self.follower_pressure:
                coords = self._current_element_coordinates(element, mesh, displacements)
            f_elem = self._consistent_pressure_load(element, mesh, pressure, coords)
            scale = activity_scale(int(element_id))
            dof_mapping = element.get_dof_mapping(mesh)
            for i, dof in enumerate(dof_mapping):
                if i < len(f_elem):
                    F[dof] += scale * f_elem[i]

        # Gravity loads from element mass matrices.
        if self.gravity is not None:
            for element_id, element in mesh.elements.items():
                if not hasattr(element, "node_ids"):
                    continue
                if material_getter is None:
                    material = _GravityFallbackMaterial()
                else:
                    material = material_getter(element.material_name)
                    qualified_runtime_guard(
                        stage=(
                            "load material observation for element "
                            f"{element_id}"
                        )
                    )
                f_elem = self._consistent_gravity_load(element, mesh, material)
                qualified_runtime_guard(
                    stage=f"gravity-load element observation for element {element_id}"
                )
                scale = activity_scale(int(element_id))
                dof_mapping = element.get_dof_mapping(mesh)
                for i, dof in enumerate(dof_mapping):
                    if i < len(f_elem):
                        F[dof] += scale * f_elem[i]

        # Inertial load from added masses under the acceleration field: both
        # model-level point masses (which also enter the mass matrix) and any
        # load-case-only added masses.
        if self.gravity is not None:
            acceleration = np.asarray(self.gravity, dtype=float)
            combined_masses: Dict[int, float] = {}
            for node_id, mass in getattr(mesh, "point_masses", {}).items():
                combined_masses[int(node_id)] = combined_masses.get(int(node_id), 0.0) + float(mass)
            for node_id, mass in self.added_node_masses.items():
                combined_masses[int(node_id)] = combined_masses.get(int(node_id), 0.0) + float(mass)
            for node_id, mass in combined_masses.items():
                node = mesh.get_node(int(node_id))
                if node is None or mass == 0.0:
                    continue
                for axis in range(3):
                    F[node.dofs[axis]] += float(mass) * acceleration[axis]

        return F

    def get_load_vector(
        self,
        mesh: "FEMesh",
        dof_manager: "DOFManager",
        material_getter: Optional[Callable[[str], "Material"]] = None,
        displacements: Optional[np.ndarray] = None,
        element_activity: Optional[object] = None,
    ) -> np.ndarray:
        """Assemble a direct load vector under one mesh-family authority lease."""

        return _run_with_qualified_load_runtime_lease(
            mesh,
            context="direct load-vector assembly",
            operation=lambda guard: self._get_load_vector_under_lease(
                mesh,
                dof_manager,
                material_getter,
                displacements,
                element_activity,
                qualified_runtime_guard=guard,
            ),
        )


@dataclass
class InPlaneLoad:
    """
    In-plane load for stiffened panels.

    Represents axial, transverse and shear stresses applied to the panel.
    """

    axial_stress: float = 0.0
    transverse_stress: float = 0.0
    shear_stress: float = 0.0
    pressure: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "axial_stress": self.axial_stress,
            "transverse_stress": self.transverse_stress,
            "shear_stress": self.shear_stress,
            "pressure": self.pressure,
        }


class LoadCombination:
    """Linear combination of load cases."""

    def __init__(self, name: str, factors: Dict[str, float]):
        self.name = name
        self.factors = factors

    def get_combined_load_vector(
        self,
        load_cases: List[LoadCase],
        mesh: "FEMesh",
        dof_manager: "DOFManager",
        material_getter: Optional[Callable[[str], "Material"]] = None,
        element_activity: Optional[object] = None,
    ) -> np.ndarray:
        """Assemble the factored load vector.

        Pass ``model.get_material`` when combinations include gravity so each
        element uses its assigned density.
        """
        F_total = np.zeros(dof_manager.total_dofs)
        for load_case in load_cases:
            if load_case.name in self.factors:
                factor = self.factors[load_case.name]
                F_total += factor * load_case.get_load_vector(
                    mesh,
                    dof_manager,
                    material_getter,
                    element_activity=element_activity,
                )
        return F_total


# Common boundary condition factory functions

def create_fixed_support(name: str, node_ids: List[int]) -> FixedSupport:
    """Create a fixed support boundary condition."""
    return FixedSupport(name, node_ids)


def create_pinned_support(name: str, node_ids: List[int]) -> PinnedSupport:
    """Create a pinned support boundary condition."""
    return PinnedSupport(name, node_ids)


def create_roller_support(
    name: str,
    node_ids: List[int],
    constrained_directions: Optional[List[str]] = None,
) -> RollerSupport:
    """Create a roller support boundary condition."""
    return RollerSupport(name, node_ids, constrained_directions)


def create_symmetry_bc(name: str, node_ids: List[int], symmetry_plane: str = "xy") -> SymmetryBC:
    """Create a symmetry boundary condition."""
    return SymmetryBC(name, node_ids, symmetry_plane)
