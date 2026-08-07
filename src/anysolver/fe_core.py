"""
Core Finite Element Classes

This module contains the fundamental classes for FE analysis:
- DOFManager: Manages degrees of freedom and numbering
- FEMesh: Stores nodes, elements, and connectivity
- FEModel: Complete FE model with materials, loads, and results
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, List, Dict, Tuple, Optional, Union
import numpy as np

from anymaterial import IsotropicMaterial as Material

from .materials import (
    Hill48Yield,
    OrthotropicMaterial,
    StructuralMaterial,
    validate_material,
)

if TYPE_CHECKING:
    from .elements import Element
    from .boundary import BoundaryCondition, LoadCase


_ELEMENT_LOCAL_CACHE_NAMES = (
    "_stiffness_matrix",
    "_mass_matrix",
    "_internal_forces",
    "_nl_cache",
    "_hourglass_stiffness_matrix",
)


def _clear_element_local_caches(element: "Element") -> None:
    """Clear mesh/material-dependent state on one element in constant time."""

    for name in _ELEMENT_LOCAL_CACHE_NAMES:
        if hasattr(element, name):
            setattr(element, name, None)


class DOFManager:
    """
    Manages degrees of freedom for the FE model.

    Each node has 6 DOFs: [ux, uy, uz, rx, ry, rz]
    (displacements in x,y,z and rotations about x,y,z)
    """

    DOF_NAMES = ['ux', 'uy', 'uz', 'rx', 'ry', 'rz']
    DOF_PER_NODE = 6

    def __init__(self):
        self._node_to_dof: Dict[int, List[int]] = {}
        self._dof_to_node: Dict[int, int] = {}
        self._dof_to_local: Dict[int, int] = {}
        self._total_dofs = 0
        self._constrained_dofs: set = set()

    def add_node(self, node_id: int) -> List[int]:
        """Add a new node and return its DOF indices."""
        if node_id in self._node_to_dof:
            raise ValueError(f"Node {node_id} already has assigned DOFs")
        dofs = list(range(self._total_dofs, self._total_dofs + self.DOF_PER_NODE))
        self._node_to_dof[node_id] = dofs
        for i, dof in enumerate(dofs):
            self._dof_to_node[dof] = node_id
            self._dof_to_local[dof] = i
        self._total_dofs += self.DOF_PER_NODE
        return dofs

    def get_node_dofs(self, node_id: int) -> List[int]:
        """Get all DOF indices for a node."""
        return self._node_to_dof.get(node_id, [])

    def get_dof_info(self, dof: int) -> Tuple[int, int, str]:
        """Get node ID, local DOF index, and name for a global DOF."""
        node_id = self._dof_to_node.get(dof, -1)
        local_idx = self._dof_to_local.get(dof, -1)
        name = self.DOF_NAMES[local_idx] if 0 <= local_idx < 6 else "unknown"
        return node_id, local_idx, name

    @property
    def total_dofs(self) -> int:
        return self._total_dofs

    @property
    def active_dofs(self) -> int:
        return self._total_dofs - len(self._constrained_dofs)

    def constrain_dof(self, dof: int):
        """Mark a DOF as constrained."""
        self._constrained_dofs.add(dof)

    def is_constrained(self, dof: int) -> bool:
        return dof in self._constrained_dofs

    def get_free_dofs(self) -> List[int]:
        """Get list of free (unconstrained) DOFs."""
        return [dof for dof in range(self._total_dofs) if dof not in self._constrained_dofs]

    def create_dof_mask(self) -> Tuple[np.ndarray, np.ndarray]:
        """Create arrays for constrained and free DOFs."""
        free_dofs = np.array(self.get_free_dofs(), dtype=int)
        constrained_dofs = np.array(list(self._constrained_dofs), dtype=int)
        return free_dofs, constrained_dofs


@dataclass
class Node:
    """A node in the FE mesh."""
    id: int
    x: float
    y: float
    z: float
    dofs: List[int] = field(default_factory=list)

    def coords(self) -> np.ndarray:
        """Return node coordinates as numpy array."""
        return np.array([self.x, self.y, self.z])


@dataclass
class FEMesh:
    """
    Finite Element Mesh

    Stores nodes, elements, and connectivity for the FE model.
    """
    nodes: Dict[int, Node] = field(default_factory=dict)
    elements: Dict[int, 'Element'] = field(default_factory=dict)
    dof_manager: DOFManager = field(default_factory=DOFManager)
    point_masses: Dict[int, float] = field(default_factory=dict)
    revisions: Dict[str, int] = field(default_factory=lambda: {
        "topology": 0,
        "geometry": 0,
        "material": 0,
        "mass": 0,
        "load": 0,
        "boundary": 0,
        "mpc": 0,
        "result_state": 0,
    })

    def _advance_revision(self, category: str) -> None:
        """Increment one revision without applying invalidation policy."""

        self.revisions[category] = int(self.revisions.get(category, 0)) + 1

    def bump_revision(self, category: str) -> None:
        """Increment a mesh/model revision category and clear stale caches."""
        self._advance_revision(category)
        # Element-local matrices depend on an element's geometry and material,
        # not on unrelated elements or MPC topology.  Scanning every existing
        # element for every add_element() made model construction O(E**2).
        if category in {"geometry", "material"}:
            for element in self.elements.values():
                _clear_element_local_caches(element)
        if category in {"topology", "mpc"} and hasattr(self, "_sparsity_cache"):
            self._sparsity_cache = {}
        if category in {"topology", "mpc"} and hasattr(self, "_topology_signature_cache"):
            self._topology_signature_cache = {}

    def revision_signature(self) -> Dict[str, int]:
        return {key: int(value) for key, value in sorted(self.revisions.items())}

    def add_node(self, node_id: int, x: float, y: float, z: float) -> Node:
        """Add a node to the mesh."""
        if node_id in self.nodes:
            raise ValueError(f"Node {node_id} already exists")
        node = Node(id=node_id, x=x, y=y, z=z)
        node.dofs = self.dof_manager.add_node(node_id)
        self.nodes[node_id] = node
        self.bump_revision("topology")
        # A genuinely new node cannot be referenced by any already-valid
        # element, so existing element-local geometry caches remain valid.
        # The geometry revision still advances to invalidate model-wide plans.
        self._advance_revision("geometry")
        return node

    def add_element(self, element_id: int, element: 'Element'):
        """Add an element to the mesh."""
        # Elements can be precomputed before insertion (including against
        # another mesh).  Clear only the incoming element; revisiting every
        # existing element would turn construction into O(E**2).
        _clear_element_local_caches(element)
        self.elements[element_id] = element
        self.bump_revision("topology")
        self.bump_revision("mpc")

    def set_node_coordinates(self, node_id: int, x: float, y: float, z: float) -> None:
        """Update node coordinates and invalidate geometry-dependent caches."""
        node = self.get_node(node_id)
        if node is None:
            raise ValueError(f"Node {node_id} not found")
        node.x = float(x)
        node.y = float(y)
        node.z = float(z)
        self.bump_revision("geometry")

    def get_node(self, node_id: int) -> Optional[Node]:
        return self.nodes.get(node_id)

    def get_element(self, element_id: int) -> Optional['Element']:
        return self.elements.get(element_id)

    @property
    def num_nodes(self) -> int:
        return len(self.nodes)

    @property
    def num_elements(self) -> int:
        return len(self.elements)

    def get_connectivity(self) -> Dict[int, List[int]]:
        """Get element connectivity (element_id -> node_ids)."""
        return {eid: elem.node_ids for eid, elem in self.elements.items()}

    def get_node_coordinates(self) -> np.ndarray:
        """Get coordinates of all nodes as array (n_nodes, 3)."""
        coords = np.zeros((self.num_nodes, 3))
        for i, (_node_id, node) in enumerate(self.nodes.items()):
            coords[i] = node.coords()
        return coords


@dataclass
class FEModel:
    """
    Complete Finite Element Model

    Contains mesh, materials, boundary conditions, loads, and results.
    """
    name: str
    mesh: FEMesh = field(default_factory=FEMesh)
    materials: Dict[str, StructuralMaterial] = field(default_factory=dict)
    boundary_conditions: List['BoundaryCondition'] = field(default_factory=list)
    load_cases: List['LoadCase'] = field(default_factory=list)
    current_material: str = "default"

    def __post_init__(self):
        if "default" not in self.materials:
            self.materials["default"] = Material(
                name="default",
                elastic_modulus=210e9,  # Steel
                poisson_ratio=0.3
            )

    def add_material(self, name: str, elastic_modulus: float, poisson_ratio: float,
                    density: float = 0.0, yield_stress: float = 0.0,
                    hardening_curve: Optional[object] = None) -> Material:
        """Add a material to the model."""
        mat = Material(
            name=name,
            elastic_modulus=elastic_modulus,
            poisson_ratio=poisson_ratio,
            density=density,
            yield_stress=yield_stress,
            hardening_curve=hardening_curve
        )
        self.materials[name] = mat
        self.mesh.bump_revision("material")
        return mat

    def register_material(self, material: StructuralMaterial) -> StructuralMaterial:
        """Register a solver-compatible material object.

        Registration is structural rather than inheritance-based: a future
        ANYmaterial object can satisfy :class:`StructuralMaterial` directly.
        A same-name registration replaces the previous material, matching
        :meth:`add_material`, and invalidates material-dependent caches.
        """

        validate_material(material)
        self.materials[material.name] = material
        self.mesh.bump_revision("material")
        return material

    def add_orthotropic_material(
        self,
        name: str,
        elastic_modulus_1: float,
        elastic_modulus_2: float,
        elastic_modulus_3: float,
        poisson_ratio_12: float,
        poisson_ratio_13: float,
        poisson_ratio_23: float,
        shear_modulus_12: float,
        shear_modulus_13: float,
        shear_modulus_23: float,
        density: float = 0.0,
        hill_yield: Optional[Hill48Yield] = None,
        hardening_curve: Optional[object] = None,
    ) -> OrthotropicMaterial:
        """Construct and register a homogeneous orthotropic material."""

        material = OrthotropicMaterial(
            name=name,
            elastic_modulus_1=elastic_modulus_1,
            elastic_modulus_2=elastic_modulus_2,
            elastic_modulus_3=elastic_modulus_3,
            poisson_ratio_12=poisson_ratio_12,
            poisson_ratio_13=poisson_ratio_13,
            poisson_ratio_23=poisson_ratio_23,
            shear_modulus_12=shear_modulus_12,
            shear_modulus_13=shear_modulus_13,
            shear_modulus_23=shear_modulus_23,
            density=density,
            hill_yield=hill_yield,
            hardening_curve=hardening_curve,
        )
        self.register_material(material)
        return material

    def set_material(self, name: str):
        """Set the current material for new elements."""
        if name not in self.materials:
            raise ValueError(f"Material '{name}' not found")
        self.current_material = name

    def get_material(self, name: str = None) -> StructuralMaterial:
        """Get a material by name, or the current material."""
        name = name or self.current_material
        return self.materials.get(name, self.materials["default"])

    def add_node(self, node_id: int, x: float, y: float, z: float) -> Node:
        """Add a node to the model."""
        return self.mesh.add_node(node_id, x, y, z)

    def add_element(self, element_id: int, element: 'Element'):
        """Add an element to the model."""
        self.mesh.add_element(element_id, element)

    def add_point_mass(self, node_id: int, mass: float):
        """Attach a lumped translational point mass to a node.

        The mass enters the global mass matrix (so it shifts natural
        frequencies and participates in transient/collision dynamics) and, when
        an acceleration/gravity field is applied, produces the corresponding
        inertial load.
        """
        node_id = int(node_id)
        if self.mesh.get_node(node_id) is None:
            raise ValueError(f"Cannot attach point mass to missing node {node_id}")
        mass = float(mass)
        if not np.isfinite(mass) or mass < 0.0:
            raise ValueError("Point mass must be finite and non-negative")
        if mass == 0.0:
            return
        self.mesh.point_masses[node_id] = self.mesh.point_masses.get(node_id, 0.0) + mass
        self.mesh.bump_revision("mass")

    def add_boundary_condition(self, bc: 'BoundaryCondition'):
        """Add a boundary condition to the model."""
        self.boundary_conditions.append(bc)
        self.mesh.bump_revision("boundary")

    def add_load_case(self, load_case: 'LoadCase'):
        """Add a load case to the model."""
        self.load_cases.append(load_case)
        self.mesh.bump_revision("load")

    def apply_boundary_conditions(self):
        """Apply all boundary conditions to the mesh DOF manager."""
        for bc in self.boundary_conditions:
            bc.apply(self.mesh.dof_manager)

    def clear_boundary_conditions(self):
        """Clear all boundary conditions."""
        self.boundary_conditions.clear()
        self.mesh.dof_manager = DOFManager()
        # Re-add nodes to reset DOFs
        for node_id, node in self.mesh.nodes.items():
            node.dofs = self.mesh.dof_manager.add_node(node_id)
        self.mesh.bump_revision("boundary")
        self.mesh.bump_revision("topology")

    def set_node_coordinates(self, node_id: int, x: float, y: float, z: float) -> None:
        """Update node coordinates and invalidate geometry-dependent caches."""
        self.mesh.set_node_coordinates(node_id, x, y, z)

    def bump_revision(self, category: str) -> None:
        self.mesh.bump_revision(category)

    def revision_signature(self) -> Dict[str, int]:
        return self.mesh.revision_signature()
