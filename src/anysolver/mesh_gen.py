"""ANYsolver adapters for neutral meshes produced by ANYmesher.

ANYmesher owns geometry, numbering, mesh quality and beam-shell coupling
records.  This module retains the solver decisions: converting those records to
FEModel elements and MPCs, assigning the legacy default material, and
interpreting the historical support labels.  Public 0.1 mesh helpers remain
available through this adapter for the 0.2.x compatibility line.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import numpy as np

from anymesher import (
    Mesh as NeutralMesh,
    PanelMeshConfig as NeutralPanelMeshConfig,
    StiffenedPanel as NeutralStiffenedPanel,
    StiffenerCrossSection,
    beam_mesh as neutral_beam_mesh,
    panel_edge_nodes,
    simple_panel_mesh as neutral_simple_panel_mesh,
    stiffened_panel_mesh as neutral_stiffened_panel_mesh,
    verify_mesh_quality as verify_neutral_mesh_quality,
)

if TYPE_CHECKING:
    from .fe_core import FEModel, FEMesh, Material

@dataclass
class MeshConfig:
    """Configuration for mesh generation."""

    shell_num_divisions_x: int = 4
    shell_num_divisions_y: int = 4
    beam_num_divisions: int = 1

    use_coupling_elements: bool = True
    coupling_stiffness: float = 0.0
    use_shared_nodes: bool = False

    tolerance: float = 1.0e-6

    default_material: str = "steel"
    plate_material: str = "steel"
    stiffener_material: str = "steel"

    use_8node_shells: bool = False
    align_mesh_to_stiffeners: bool = False


@dataclass
class PanelGeometry:
    """Geometry and load metadata for a rectangular stiffened panel."""

    length: float = 0.0
    width: float = 0.0

    plate_thickness: float = 0.0
    plate_material: str = "steel"

    stiffener_type: str = "T-bar"
    stiffener_spacing: float = 0.0
    stiffener_height: float = 0.0
    stiffener_web_thickness: float = 0.0
    stiffener_flange_width: float = 0.0
    stiffener_flange_thickness: float = 0.0
    stiffener_material: str = "steel"
    num_stiffeners: int = 1

    in_plane_support: str = "Integrated"
    rotational_support: str = "SS"

    axial_stress: float = 0.0
    transverse_stress: float = 0.0
    shear_stress: float = 0.0
    pressure: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "length": self.length,
            "width": self.width,
            "plate_thickness": self.plate_thickness,
            "plate_material": self.plate_material,
            "stiffener_type": self.stiffener_type,
            "stiffener_spacing": self.stiffener_spacing,
            "stiffener_height": self.stiffener_height,
            "stiffener_web_thickness": self.stiffener_web_thickness,
            "stiffener_flange_width": self.stiffener_flange_width,
            "stiffener_flange_thickness": self.stiffener_flange_thickness,
            "stiffener_material": self.stiffener_material,
            "num_stiffeners": self.num_stiffeners,
            "in_plane_support": self.in_plane_support,
            "rotational_support": self.rotational_support,
            "axial_stress": self.axial_stress,
            "transverse_stress": self.transverse_stress,
            "shear_stress": self.shear_stress,
            "pressure": self.pressure,
        }

    @classmethod
    def from_anystructure(cls, anystructure_data: Any) -> "PanelGeometry":
        geometry = cls()
        if hasattr(anystructure_data, "Plate"):
            plate = anystructure_data.Plate
            geometry.length = getattr(plate, "span", 0.0)
            geometry.width = getattr(plate, "spacing", 0.0)
            geometry.plate_thickness = getattr(plate, "t", 0.0)
            geometry.plate_material = "steel"
        if hasattr(anystructure_data, "Stiffener"):
            stiffener = anystructure_data.Stiffener
            geometry.stiffener_type = getattr(stiffener, "stiffener_type", "T-bar")
            geometry.stiffener_spacing = getattr(stiffener, "spacing", 0.0)
            geometry.stiffener_height = getattr(stiffener, "hw", 0.0)
            geometry.stiffener_web_thickness = getattr(stiffener, "tw", 0.0)
            geometry.stiffener_flange_width = getattr(stiffener, "b", 0.0)
            geometry.stiffener_flange_thickness = getattr(stiffener, "tf", 0.0)
            geometry.stiffener_material = "steel"
        if hasattr(anystructure_data, "sigma_x1"):
            geometry.axial_stress = anystructure_data.sigma_x1
        if hasattr(anystructure_data, "sigma_y1"):
            geometry.transverse_stress = anystructure_data.sigma_y1
        if hasattr(anystructure_data, "tau_xy"):
            geometry.shear_stress = anystructure_data.tau_xy
        if hasattr(anystructure_data, "pressure"):
            geometry.pressure = anystructure_data.pressure
        return geometry

class InterpolatedBeamShellMPCElement:
    """
    Duck-typed MPC-only element for eccentric beam-to-shell coupling.

    The first node is the beam slave node.  The remaining nodes are the shell
    master nodes of the shell element underneath the beam node.  Shape weights
    are evaluated at the projected beam-node location in the shell element.
    """

    def __init__(
        self,
        element_id: int,
        beam_node_id: int,
        shell_node_ids: List[int],
        shape_weights: np.ndarray,
        eccentricity: np.ndarray,
        material_name: str = "steel",
    ):
        self.element_id = element_id
        self.beam_node_id = beam_node_id
        self.shell_node_ids = list(shell_node_ids)
        self.shape_weights = np.asarray(shape_weights, dtype=float)
        self.eccentricity = np.asarray(eccentricity, dtype=float)
        self.material_name = material_name
        self.node_ids = [beam_node_id] + self.shell_node_ids
        self._stiffness_matrix = None
        self._mass_matrix = None

    @property
    def num_nodes(self) -> int:
        return 1 + len(self.shell_node_ids)

    @property
    def dofs_per_node(self) -> int:
        return 6

    @property
    def total_dofs(self) -> int:
        return self.num_nodes * self.dofs_per_node

    def get_node_coordinates(self, mesh: "FEMesh") -> np.ndarray:
        coords = []
        for node_id in self.node_ids:
            node = mesh.get_node(node_id)
            if node is None:
                raise ValueError(f"MPC element {self.element_id} references missing node {node_id}")
            coords.append(node.coords())
        return np.asarray(coords, dtype=float)

    def get_dof_mapping(self, mesh: "FEMesh") -> List[int]:
        dofs: List[int] = []
        for node_id in self.node_ids:
            node = mesh.get_node(node_id)
            if node is not None:
                dofs.extend(node.dofs)
        return dofs

    def compute_stiffness_matrix(self, mesh: "FEMesh", material: "Material") -> np.ndarray:
        # Constraint is enforced exactly by assembly.build_constraint_transformation().
        K = np.zeros((self.total_dofs, self.total_dofs), dtype=float)
        self._stiffness_matrix = K
        return K

    def compute_mass_matrix(self, mesh: "FEMesh", material: "Material") -> np.ndarray:
        return np.zeros((self.total_dofs, self.total_dofs), dtype=float)

    def compute_geometric_stiffness_matrix(self, mesh: "FEMesh", material: "Material", state: Any = None) -> np.ndarray:
        return np.zeros((self.total_dofs, self.total_dofs), dtype=float)

    def compute_nonlinear_response(
        self,
        mesh: "FEMesh",
        material: "Material",
        u_elem: np.ndarray,
        state: Any = None,
        num_layers: int = 5,
        tangent: bool = True,
    ) -> Tuple[np.ndarray, Optional[np.ndarray], Any]:
        force = np.zeros(self.total_dofs, dtype=float)
        stiffness = np.zeros((self.total_dofs, self.total_dofs), dtype=float) if tangent else None
        return force, stiffness, state

    def compute_stresses(
        self,
        mesh: "FEMesh",
        displacements: np.ndarray,
        material: "Material",
        return_global: bool = False,
    ) -> Dict[str, np.ndarray]:
        return {}

    def get_mpc_constraints(self, mesh: "FEMesh") -> List[Dict[str, Any]]:
        beam_node = mesh.get_node(self.beam_node_id)
        if beam_node is None:
            return []

        beam_dofs = beam_node.dofs
        rx, ry, rz = self.eccentricity
        translational_masters = [{}, {}, {}]
        rotational_masters = [{}, {}, {}]

        for shell_node_id, weight in zip(self.shell_node_ids, self.shape_weights):
            shell_node = mesh.get_node(shell_node_id)
            if shell_node is None or abs(float(weight)) == 0.0:
                continue
            s = shell_node.dofs
            w = float(weight)

            translational_masters[0][s[0]] = translational_masters[0].get(s[0], 0.0) + w
            translational_masters[0][s[4]] = translational_masters[0].get(s[4], 0.0) + w * rz
            translational_masters[0][s[5]] = translational_masters[0].get(s[5], 0.0) - w * ry

            translational_masters[1][s[1]] = translational_masters[1].get(s[1], 0.0) + w
            translational_masters[1][s[3]] = translational_masters[1].get(s[3], 0.0) - w * rz
            translational_masters[1][s[5]] = translational_masters[1].get(s[5], 0.0) + w * rx

            translational_masters[2][s[2]] = translational_masters[2].get(s[2], 0.0) + w
            translational_masters[2][s[3]] = translational_masters[2].get(s[3], 0.0) + w * ry
            translational_masters[2][s[4]] = translational_masters[2].get(s[4], 0.0) - w * rx

            rotational_masters[0][s[3]] = rotational_masters[0].get(s[3], 0.0) + w
            rotational_masters[1][s[4]] = rotational_masters[1].get(s[4], 0.0) + w
            rotational_masters[2][s[5]] = rotational_masters[2].get(s[5], 0.0) + w

        return [
            {"slave": beam_dofs[0], "masters": translational_masters[0], "value": 0.0, "label": f"interp_beam_shell_ux_{self.element_id}"},
            {"slave": beam_dofs[1], "masters": translational_masters[1], "value": 0.0, "label": f"interp_beam_shell_uy_{self.element_id}"},
            {"slave": beam_dofs[2], "masters": translational_masters[2], "value": 0.0, "label": f"interp_beam_shell_uz_{self.element_id}"},
            {"slave": beam_dofs[3], "masters": rotational_masters[0], "value": 0.0, "label": f"interp_beam_shell_rx_{self.element_id}"},
            {"slave": beam_dofs[4], "masters": rotational_masters[1], "value": 0.0, "label": f"interp_beam_shell_ry_{self.element_id}"},
            {"slave": beam_dofs[5], "masters": rotational_masters[2], "value": 0.0, "label": f"interp_beam_shell_rz_{self.element_id}"},
        ]


class RigidLidMPCElement:
    """
    Constraint-only rigid end diaphragm.

    The element ties an end ring to a free center reference node using rigid-body
    kinematics. It adds end-ring coupling without adding lid shell elements, so
    lid stresses and lid pressure loads are not recovered.
    """

    def __init__(
        self,
        element_id: int,
        center_node_id: int,
        ring_node_ids: List[int],
        material_name: str = "steel",
    ):
        self.element_id = int(element_id)
        self.center_node_id = int(center_node_id)
        self.ring_node_ids = [int(node_id) for node_id in ring_node_ids if int(node_id) != int(center_node_id)]
        self.material_name = material_name
        self.node_ids = [self.center_node_id] + self.ring_node_ids

    @property
    def num_nodes(self) -> int:
        return len(self.node_ids)

    @property
    def dofs_per_node(self) -> int:
        return 6

    @property
    def total_dofs(self) -> int:
        return self.num_nodes * self.dofs_per_node

    def get_node_coordinates(self, mesh: "FEMesh") -> np.ndarray:
        coords = []
        for node_id in self.node_ids:
            node = mesh.get_node(node_id)
            if node is None:
                raise ValueError(f"Rigid lid element {self.element_id} references missing node {node_id}")
            coords.append(node.coords())
        return np.asarray(coords, dtype=float)

    def get_dof_mapping(self, mesh: "FEMesh") -> List[int]:
        return []

    def compute_stiffness_matrix(self, mesh: "FEMesh", material: "Material") -> np.ndarray:
        return np.zeros((0, 0), dtype=float)

    def compute_mass_matrix(self, mesh: "FEMesh", material: "Material") -> np.ndarray:
        return np.zeros((0, 0), dtype=float)

    def compute_geometric_stiffness_matrix(self, mesh: "FEMesh", material: "Material", state: Any = None) -> np.ndarray:
        return np.zeros((0, 0), dtype=float)

    def compute_stresses(
        self,
        mesh: "FEMesh",
        displacements: np.ndarray,
        material: "Material",
        return_global: bool = False,
    ) -> Dict[str, np.ndarray]:
        return {}

    @staticmethod
    def _nonzero_masters(items: Dict[int, float]) -> Dict[int, float]:
        return {int(dof): float(value) for dof, value in items.items() if abs(float(value)) > 0.0}

    def get_mpc_constraints(self, mesh: "FEMesh") -> List[Dict[str, Any]]:
        center = mesh.get_node(self.center_node_id)
        if center is None:
            return []
        center_dofs = center.dofs
        constraints: List[Dict[str, Any]] = []
        for ring_node_id in self.ring_node_ids:
            node = mesh.get_node(ring_node_id)
            if node is None:
                continue
            rx, ry, rz = (node.coords() - center.coords()).tolist()
            node_dofs = node.dofs
            translation_masters = (
                {center_dofs[0]: 1.0, center_dofs[4]: rz, center_dofs[5]: -ry},
                {center_dofs[1]: 1.0, center_dofs[3]: -rz, center_dofs[5]: rx},
                {center_dofs[2]: 1.0, center_dofs[3]: ry, center_dofs[4]: -rx},
            )
            for local_index, masters in enumerate(translation_masters):
                constraints.append(
                    {
                        "slave": node_dofs[local_index],
                        "masters": self._nonzero_masters(masters),
                        "value": 0.0,
                        "label": f"rigid_lid_{self.element_id}_u{local_index + 1}",
                    }
                )
            for local_index in range(3, 6):
                constraints.append(
                    {
                        "slave": node_dofs[local_index],
                        "masters": {center_dofs[local_index]: 1.0},
                        "value": 0.0,
                        "label": f"rigid_lid_{self.element_id}_r{local_index - 2}",
                    }
                )
        return constraints

def _neutral_panel(panel: PanelGeometry) -> NeutralStiffenedPanel:
    """Copy geometry-only panel fields into the canonical mesher contract."""

    return NeutralStiffenedPanel(
        length=float(panel.length),
        width=float(panel.width),
        plate_thickness=float(panel.plate_thickness),
        stiffener_type=str(panel.stiffener_type),
        stiffener_spacing=float(panel.stiffener_spacing),
        stiffener_height=float(panel.stiffener_height),
        stiffener_web_thickness=float(panel.stiffener_web_thickness),
        stiffener_flange_width=float(panel.stiffener_flange_width),
        stiffener_flange_thickness=float(panel.stiffener_flange_thickness),
        num_stiffeners=int(panel.num_stiffeners),
    )


def _neutral_config(config: MeshConfig) -> NeutralPanelMeshConfig:
    """Copy mesh-only options into ANYmesher without analysis metadata."""

    return NeutralPanelMeshConfig(
        shell_num_divisions_x=int(config.shell_num_divisions_x),
        shell_num_divisions_y=int(config.shell_num_divisions_y),
        beam_num_divisions=int(config.beam_num_divisions),
        use_coupling_elements=bool(config.use_coupling_elements),
        tolerance=float(config.tolerance),
        use_8node_shells=bool(config.use_8node_shells),
        align_mesh_to_stiffeners=bool(config.align_mesh_to_stiffeners),
    )


def _add_legacy_steel(
    model: "FEModel",
    *,
    density: float = 0.0,
    yield_stress: float = 0.0,
) -> None:
    """Install the material historically supplied by generated test models."""

    model.add_material(
        name="steel",
        elastic_modulus=210.0e9,
        poisson_ratio=0.3,
        density=float(density),
        yield_stress=float(yield_stress),
    )
    model.current_material = "steel"


def _install_nodes(model: "FEModel", mesh: NeutralMesh) -> None:
    for node_id, coordinates in mesh.nodes.items():
        x, y, z = np.asarray(coordinates, dtype=float).reshape(3)
        model.add_node(int(node_id), float(x), float(y), float(z))


def _install_shells(
    model: "FEModel",
    mesh: NeutralMesh,
    *,
    thickness: float,
    material_name: str = "steel",
) -> None:
    from .elements import ShellElement

    for element_id, node_ids in {**mesh.quads, **mesh.tris}.items():
        model.add_element(
            int(element_id),
            ShellElement(
                int(element_id),
                list(node_ids),
                material_name=material_name,
                thickness=float(thickness),
            ),
        )


def _install_panel_beams(
    model: "FEModel",
    mesh: NeutralMesh,
    panel: PanelGeometry,
    *,
    material_name: str = "steel",
) -> None:
    from .elements import BeamElement, QuadraticBeamElement

    section = StiffenerCrossSection.from_geometry(
        panel.stiffener_type,
        panel.stiffener_height,
        panel.stiffener_web_thickness,
        panel.stiffener_flange_width,
        panel.stiffener_flange_thickness,
    ).as_dict()
    for element_id, node_ids in mesh.beams.items():
        element_type = QuadraticBeamElement if len(node_ids) == 3 else BeamElement
        model.add_element(
            int(element_id),
            element_type(
                int(element_id),
                list(node_ids),
                material_name=material_name,
                cross_section=dict(section),
            ),
        )


def _install_couplings(
    model: "FEModel",
    mesh: NeutralMesh,
    *,
    material_name: str = "steel",
) -> None:
    for element_id, coupling in mesh.couplings.items():
        model.add_element(
            int(element_id),
            InterpolatedBeamShellMPCElement(
                int(element_id),
                beam_node_id=int(coupling.beam_node),
                shell_node_ids=list(coupling.plate_nodes),
                shape_weights=np.asarray(coupling.weights, dtype=float),
                eccentricity=np.asarray(coupling.eccentricity, dtype=float),
                material_name=material_name,
            ),
        )


def _unique_node_ids(*node_lists: List[int]) -> List[int]:
    seen: set[int] = set()
    ordered: List[int] = []
    for node_list in node_lists:
        for node_id in node_list:
            if node_id not in seen:
                seen.add(node_id)
                ordered.append(node_id)
    return ordered


def _add_custom_support(
    model: "FEModel",
    name: str,
    node_ids: List[int],
    dof_constraints: Dict[str, float],
) -> None:
    from .boundary import BoundaryCondition

    unique_ids = _unique_node_ids(node_ids)
    if unique_ids:
        model.add_boundary_condition(BoundaryCondition(name, unique_ids, dof_constraints))


def _add_panel_boundary_conditions(
    model: "FEModel",
    panel: PanelGeometry,
    edges: Dict[str, List[int]],
) -> None:
    """Interpret legacy support labels against ANYmesher's panel node sets."""

    support = (panel.in_plane_support or "").strip().lower()
    rotational = (panel.rotational_support or "").strip().upper()
    longitudinal_edges = _unique_node_ids(edges["y0"], edges["yW"])
    transverse_edges = _unique_node_ids(edges["x0"], edges["xL"])
    all_edge_nodes = edges["all"]

    if support == "integrated":
        _add_custom_support(
            model,
            "Integrated_edge_translations",
            all_edge_nodes,
            {"ux": 0.0, "uy": 0.0, "uz": 0.0},
        )
    elif support == "girder - long":
        _add_custom_support(
            model,
            "Longitudinal_girder_edges",
            longitudinal_edges,
            {"ux": 0.0, "uy": 0.0, "uz": 0.0},
        )
        _add_custom_support(model, "Transverse_reference_ux", edges["x0"][:1], {"ux": 0.0})
    elif support == "girder - trans":
        _add_custom_support(
            model,
            "Transverse_girder_edges",
            transverse_edges,
            {"ux": 0.0, "uy": 0.0, "uz": 0.0},
        )
        _add_custom_support(model, "Longitudinal_reference_uy", edges["y0"][:1], {"uy": 0.0})
    else:
        _add_custom_support(model, "Reference_out_of_plane", all_edge_nodes[:1], {"uz": 0.0})

    if rotational == "CL":
        _add_custom_support(
            model,
            "Clamped_edge_rotations",
            all_edge_nodes,
            {"rx": 0.0, "ry": 0.0, "rz": 0.0},
        )
    elif rotational == "FS":
        _add_custom_support(
            model,
            "Fixed_simple_longitudinal_rotations",
            longitudinal_edges,
            {"rx": 0.0, "ry": 0.0, "rz": 0.0},
        )


def generate_stiffened_panel_mesh(
    panel: PanelGeometry,
    config: Optional[MeshConfig] = None,
) -> "FEModel":
    """Build a solver model from ANYmesher's neutral stiffened-panel mesh."""

    from .fe_core import FEModel

    config = config or MeshConfig()
    if config.use_shared_nodes:
        raise ValueError(
            "use_shared_nodes=True is no longer supported for eccentric stiffeners. "
            "Use separate beam nodes with interpolated beam-shell MPC constraints instead."
        )

    neutral = neutral_stiffened_panel_mesh(_neutral_panel(panel), _neutral_config(config))
    model = FEModel(name=f"StiffenedPanel_{panel.length}x{panel.width}")
    _add_legacy_steel(model, density=7850.0, yield_stress=235.0e6)
    _install_nodes(model, neutral)
    _install_shells(model, neutral, thickness=panel.plate_thickness)
    _install_panel_beams(model, neutral, panel)
    _install_couplings(model, neutral)
    _add_panel_boundary_conditions(model, panel, panel_edge_nodes(neutral))
    return model


def generate_simple_panel_mesh(
    length: float,
    width: float,
    thickness: float,
    num_divisions_x: int = 4,
    num_divisions_y: int = 4,
    use_8node_elements: bool = False,
) -> "FEModel":
    """Build the legacy solver panel from an ANYmesher neutral primitive."""

    from .fe_core import FEModel

    neutral = neutral_simple_panel_mesh(
        length,
        width,
        thickness,
        num_divisions_x=num_divisions_x,
        num_divisions_y=num_divisions_y,
        use_8node_elements=use_8node_elements,
    )
    panel = PanelGeometry(length=length, width=width, plate_thickness=thickness)
    model = FEModel(name=f"SimplePanel_{length}x{width}")
    _add_legacy_steel(model)
    _install_nodes(model, neutral)
    _install_shells(model, neutral, thickness=thickness)
    _add_panel_boundary_conditions(model, panel, panel_edge_nodes(neutral))
    return model


def generate_beam_mesh(
    length: float,
    num_divisions: int = 10,
    cross_section: Optional[Dict[str, float]] = None,
) -> "FEModel":
    """Build the legacy fixed-end solver beam from an ANYmesher primitive."""

    from .boundary import FixedSupport
    from .elements import BeamElement
    from .fe_core import FEModel

    neutral = neutral_beam_mesh(length, num_divisions=num_divisions)
    model = FEModel(name=f"SimpleBeam_{length}")
    _add_legacy_steel(model)
    _install_nodes(model, neutral)
    section = cross_section or {
        "area": 0.01,
        "Iy": 1.0e-6,
        "Iz": 1.0e-6,
        "J": 1.0e-6,
    }
    for element_id, node_ids in neutral.beams.items():
        model.add_element(
            int(element_id),
            BeamElement(
                int(element_id),
                list(node_ids),
                material_name="steel",
                cross_section=section,
            ),
        )
    model.add_boundary_condition(FixedSupport("Fixed_1", [1]))
    return model


def _neutral_shell_mesh_from_model(model: "FEModel") -> NeutralMesh:
    """Flatten solver shell geometry for canonical ANYmesher quality checks."""

    from .elements import ShellElement

    neutral = NeutralMesh()
    for element_id, element in model.mesh.elements.items():
        if not isinstance(element, ShellElement):
            continue
        node_ids = tuple(int(node_id) for node_id in element.node_ids)
        target = neutral.tris if len(node_ids) in (3, 6) else neutral.quads
        target[int(element_id)] = node_ids
        for node_id in node_ids:
            neutral.nodes[node_id] = np.asarray(model.mesh.nodes[node_id].coords(), dtype=float)
    return neutral


def verify_mesh_quality(model: "FEModel") -> Dict[str, Any]:
    """Return the historical dict facade over ANYmesher's quality report."""

    return verify_neutral_mesh_quality(_neutral_shell_mesh_from_model(model)).as_dict()


__all__ = [
    "InterpolatedBeamShellMPCElement",
    "MeshConfig",
    "PanelGeometry",
    "RigidLidMPCElement",
    "StiffenerCrossSection",
    "generate_beam_mesh",
    "generate_simple_panel_mesh",
    "generate_stiffened_panel_mesh",
    "verify_mesh_quality",
]
