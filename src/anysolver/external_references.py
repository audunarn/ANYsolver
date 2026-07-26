"""Generated and executable CalculiX reference cases.

Deck generation is deliberately separate from validation.  A generated deck
has status ``not_executed``.  It only becomes a numerical validation result
after CalculiX has run, the requested FRD/DAT observables have been parsed, and
every declared comparison has met its tolerance.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from .boundary import BoundaryCondition, LoadCase
from .elements import BeamElement, ShellElement
from .fe_core import FEModel, Material
from .mesh_gen import generate_simple_panel_mesh


DEFAULT_EXTERNAL_REFERENCE_PATH = Path("reports/external_references/external_reference_report.json")
DEFAULT_CALCULIX_RUN_PATH = Path("reports/external_references/runs")
CALCULIX_EXECUTABLE_ENV = "ANYSOLVER_CALCULIX_EXECUTABLE"
_DOF_TO_CALCULIX = {"ux": 1, "uy": 2, "uz": 3, "rx": 4, "ry": 5, "rz": 6}
_FLOAT_RE = re.compile(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[EeDd][+-]?\d+)?")
_COMPONENT_INDEX = {
    "x": 0,
    "ux": 0,
    "u1": 0,
    "fx": 0,
    "rf1": 0,
    "y": 1,
    "uy": 1,
    "u2": 1,
    "fy": 1,
    "rf2": 1,
    "z": 2,
    "uz": 2,
    "u3": 2,
    "fz": 2,
    "rf3": 2,
}


@dataclass(frozen=True)
class ExternalReferenceCase:
    """One generated external-reference input deck."""

    name: str
    kind: str
    inp_path: Path
    metadata_path: Path
    model_summary: Mapping[str, Any]
    load_summary: Mapping[str, Any]
    assumptions: Tuple[str, ...] = ()
    comparisons: Tuple[Mapping[str, Any], ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "inp_path": str(self.inp_path),
            "metadata_path": str(self.metadata_path),
            "model_summary": dict(self.model_summary),
            "load_summary": dict(self.load_summary),
            "assumptions": list(self.assumptions),
            "comparisons": [dict(item) for item in self.comparisons],
        }


@dataclass
class CalculixParsedResults:
    """The result fields needed by the external-reference comparisons."""

    coordinates: Dict[int, Tuple[float, float, float]] = field(default_factory=dict)
    displacements: Dict[int, Tuple[float, float, float]] = field(default_factory=dict)
    reaction_forces: Dict[int, Tuple[float, float, float]] = field(default_factory=dict)
    stresses: Dict[int, Tuple[float, ...]] = field(default_factory=dict)
    reaction_total: Optional[Tuple[float, float, float]] = None
    buckling_factors: List[float] = field(default_factory=list)
    frequencies_hz: List[float] = field(default_factory=list)
    source_files: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def has_results(self) -> bool:
        return bool(
            self.displacements
            or self.reaction_forces
            or self.stresses
            or self.reaction_total is not None
            or self.buckling_factors
            or self.frequencies_hz
        )

    def summary(self) -> Dict[str, Any]:
        return {
            "coordinate_nodes": len(self.coordinates),
            "displacement_nodes": len(self.displacements),
            "reaction_nodes": len(self.reaction_forces),
            "stress_nodes": len(self.stresses),
            "has_reaction_total": self.reaction_total is not None,
            "buckling_factors": list(self.buckling_factors),
            "frequencies_hz": list(self.frequencies_hz),
            "source_files": list(self.source_files),
            "warnings": list(self.warnings),
        }


def _fmt(value: float) -> str:
    return f"{float(value):.16g}"


def _material_block(materials: Mapping[str, Material]) -> List[str]:
    lines: List[str] = []
    for material in materials.values():
        lines.extend(
            [
                f"*MATERIAL, NAME={material.name}",
                "*ELASTIC",
                f"{_fmt(material.elastic_modulus)}, {_fmt(material.poisson_ratio)}",
            ]
        )
        if material.density:
            lines.extend(["*DENSITY", _fmt(material.density)])
    return lines


def _element_type(element: Any) -> str:
    if isinstance(element, ShellElement):
        return "S8" if len(element.node_ids) == 8 else "S4"
    if isinstance(element, BeamElement):
        return "B31"
    return "UNKNOWN"


def _element_sets_by_type_and_material(model: FEModel) -> Dict[Tuple[str, str], List[int]]:
    groups: Dict[Tuple[str, str], List[int]] = {}
    for element_id, element in model.mesh.elements.items():
        groups.setdefault((_element_type(element), element.material_name), []).append(int(element_id))
    return groups


def _section_blocks(model: FEModel) -> Tuple[List[str], List[str]]:
    lines: List[str] = []
    assumptions: List[str] = []
    for (element_type, material_name), element_ids in _element_sets_by_type_and_material(model).items():
        elset = f"E_{element_type}_{material_name}"
        lines.append(f"*ELSET, ELSET={elset}")
        for start in range(0, len(element_ids), 16):
            lines.append(", ".join(str(element_id) for element_id in element_ids[start : start + 16]))
        first = model.mesh.elements[element_ids[0]]
        if isinstance(first, ShellElement):
            lines.extend([f"*SHELL SECTION, ELSET={elset}, MATERIAL={material_name}", _fmt(first.thickness)])
        elif isinstance(first, BeamElement):
            area = float(first.cross_section.get("area", 0.01))
            side = np.sqrt(max(area, 1.0e-18))
            lines.extend([f"*BEAM SECTION, ELSET={elset}, MATERIAL={material_name}, SECTION=RECT", f"{_fmt(side)}, {_fmt(side)}"])
            square_inertia = area**2 / 12.0
            iy = float(first.cross_section.get("Iy", square_inertia))
            iz = float(first.cross_section.get("Iz", square_inertia))
            if np.isclose(iy, square_inertia, rtol=1.0e-12, atol=0.0) and np.isclose(
                iz, square_inertia, rtol=1.0e-12, atol=0.0
            ):
                assumptions.append(
                    f"Beam element set {elset} uses a square RECT section preserving area and both bending inertias; "
                    "the source J value is not represented independently."
                )
            else:
                assumptions.append(
                    f"Beam element set {elset} is exported as an equivalent square RECT section preserving area; "
                    "Iy/Iz/J exact matching is not represented in this deck writer."
                )
    return lines, assumptions


def _boundary_block(model: FEModel) -> List[str]:
    lines: List[str] = []
    if not model.boundary_conditions:
        return lines
    lines.append("*BOUNDARY")
    for bc in model.boundary_conditions:
        for node_id in bc.node_ids:
            for dof_name, value in bc.dof_constraints.items():
                if abs(float(value)) > 0.0:
                    continue
                dof = _DOF_TO_CALCULIX.get(dof_name)
                if dof is not None:
                    lines.append(f"{int(node_id)}, {dof}, {dof}, 0.")
    return lines


def _load_block(load_case: Optional[LoadCase]) -> Tuple[List[str], Dict[str, Any]]:
    if load_case is None:
        return [], {"name": None, "nodal_loads": 0, "pressure_loads": 0}
    lines: List[str] = []
    if load_case.nodal_loads:
        lines.append("*CLOAD")
        for node_id, values in sorted(load_case.nodal_loads.items()):
            for idx, value in enumerate(np.asarray(values, dtype=float), start=1):
                if abs(float(value)) > 0.0:
                    lines.append(f"{int(node_id)}, {idx}, {_fmt(value)}")
    if load_case.pressure_loads:
        lines.append("*DLOAD")
        for element_id, pressure in sorted(load_case.pressure_loads.items()):
            lines.append(f"{int(element_id)}, P, {_fmt(pressure)}")
    if load_case.gravity is not None:
        gx, gy, gz = np.asarray(load_case.gravity, dtype=float).reshape(3)
        magnitude = float(np.linalg.norm([gx, gy, gz]))
        if magnitude > 0.0:
            direction = np.asarray([gx, gy, gz], dtype=float) / magnitude
            lines.append("*DLOAD")
            lines.append(
                f"ALL, GRAV, {_fmt(magnitude)}, "
                f"{_fmt(direction[0])}, {_fmt(direction[1])}, {_fmt(direction[2])}"
            )
    return lines, {
        "name": load_case.name,
        "nodal_loads": len(load_case.nodal_loads),
        "pressure_loads": len(load_case.pressure_loads),
        "has_gravity": load_case.gravity is not None,
    }


def write_calculix_input_deck(
    model: FEModel,
    load_case: Optional[LoadCase],
    output_path: Path | str,
    *,
    analysis: str = "static",
    metadata: Optional[Mapping[str, Any]] = None,
    comparisons: Optional[Sequence[Mapping[str, Any]]] = None,
) -> ExternalReferenceCase:
    """Write a deterministic CalculiX-style input deck and sidecar metadata."""

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    model.apply_boundary_conditions()
    lines: List[str] = [
        "** Generated by anysolver.external_references",
        f"** Model: {model.name}",
        "*NODE",
    ]
    for node_id, node in sorted(model.mesh.nodes.items()):
        lines.append(f"{int(node_id)}, {_fmt(node.x)}, {_fmt(node.y)}, {_fmt(node.z)}")
    lines.append("*NSET, NSET=NALL")
    all_node_ids = [int(node_id) for node_id in sorted(model.mesh.nodes)]
    for start in range(0, len(all_node_ids), 16):
        lines.append(", ".join(str(node_id) for node_id in all_node_ids[start : start + 16]))
    support_node_ids = sorted(
        {
            int(node_id)
            for boundary_condition in model.boundary_conditions
            for node_id in boundary_condition.node_ids
            if boundary_condition.dof_constraints
        }
    )
    if support_node_ids:
        lines.append("*NSET, NSET=SUPPORT")
        for start in range(0, len(support_node_ids), 16):
            lines.append(", ".join(str(node_id) for node_id in support_node_ids[start : start + 16]))
    reaction_set = "SUPPORT" if support_node_ids else "NALL"
    for (element_type, _material_name), element_ids in sorted(_element_sets_by_type_and_material(model).items()):
        if element_type == "UNKNOWN":
            continue
        lines.append(f"*ELEMENT, TYPE={element_type}")
        for element_id in element_ids:
            element = model.mesh.elements[element_id]
            lines.append(f"{int(element_id)}, " + ", ".join(str(int(node_id)) for node_id in element.node_ids))
    supported_element_ids = [
        int(element_id)
        for element_id, element in sorted(model.mesh.elements.items())
        if _element_type(element) != "UNKNOWN"
    ]
    if supported_element_ids:
        lines.append("*ELSET, ELSET=ALL")
        for start in range(0, len(supported_element_ids), 16):
            lines.append(", ".join(str(element_id) for element_id in supported_element_ids[start : start + 16]))
    lines.extend(_material_block(model.materials))
    section_lines, assumptions = _section_blocks(model)
    lines.extend(section_lines)
    lines.extend(_boundary_block(model))
    load_lines, load_summary = _load_block(load_case)
    if analysis == "buckling":
        lines.extend(["*STEP", "*BUCKLE", "5"])
    elif analysis == "frequency":
        lines.extend(["*STEP", "*FREQUENCY", "5"])
    else:
        lines.extend(["*STEP", "*STATIC"])
    lines.extend(load_lines)
    lines.extend(
        [
            "*NODE FILE",
            "U, RF",
            "*EL FILE",
            "S",
            f"*NODE PRINT, NSET={reaction_set}, TOTALS=ONLY",
            "RF",
            "*END STEP",
            "",
        ]
    )
    output.write_text("\n".join(lines), encoding="utf-8")

    model_summary = {
        "name": model.name,
        "nodes": len(model.mesh.nodes),
        "elements": len(model.mesh.elements),
        "materials": sorted(model.materials),
        "analysis": analysis,
    }
    sidecar = output.with_suffix(".json")
    payload = {
        "name": output.stem,
        "kind": analysis,
        "model_summary": model_summary,
        "load_summary": load_summary,
        "assumptions": assumptions,
        "metadata": dict(metadata or {}),
        "comparisons": [dict(item) for item in comparisons or ()],
    }
    sidecar.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ExternalReferenceCase(
        name=output.stem,
        kind=analysis,
        inp_path=output,
        metadata_path=sidecar,
        model_summary=model_summary,
        load_summary=load_summary,
        assumptions=tuple(assumptions),
        comparisons=tuple(dict(item) for item in comparisons or ()),
    )


def _navier_plate_observables(
    *,
    length: float,
    width: float,
    thickness: float,
    pressure: float,
    elastic_modulus: float,
    poisson_ratio: float,
    series_terms: int = 99,
) -> Tuple[float, float]:
    """Return center deflection and surface von Mises stress for an SSSS plate."""

    rigidity = elastic_modulus * thickness**3 / (12.0 * (1.0 - poisson_ratio**2))
    displacement_sum = 0.0
    moment_x = 0.0
    moment_y = 0.0
    for m in range(1, int(series_terms) + 1, 2):
        for n in range(1, int(series_terms) + 1, 2):
            center_shape = math.sin(m * math.pi / 2.0) * math.sin(n * math.pi / 2.0)
            wave = (m / length) ** 2 + (n / width) ** 2
            denominator = m * n * wave**2
            displacement_sum += center_shape / denominator
            moment_scale = 16.0 * pressure * center_shape / (math.pi**4 * denominator)
            moment_x += moment_scale * ((m / length) ** 2 + poisson_ratio * (n / width) ** 2)
            moment_y += moment_scale * ((n / width) ** 2 + poisson_ratio * (m / length) ** 2)
    displacement = 16.0 * pressure * displacement_sum / (math.pi**6 * rigidity)
    stress_x = 6.0 * moment_x / thickness**2
    stress_y = 6.0 * moment_y / thickness**2
    von_mises = math.sqrt(stress_x**2 - stress_x * stress_y + stress_y**2)
    return float(abs(displacement)), float(von_mises)


def _analytical_comparison(
    name: str,
    quantity: str,
    expected: float,
    *,
    relative_tolerance: float,
    absolute_tolerance: float = 0.0,
    component: Optional[str] = None,
    absolute: bool = False,
    description: str,
    parameters: Mapping[str, Any],
) -> Dict[str, Any]:
    comparison: Dict[str, Any] = {
        "name": name,
        "quantity": quantity,
        "expected": float(expected),
        "relative_tolerance": float(relative_tolerance),
        "absolute_tolerance": float(absolute_tolerance),
        "absolute": bool(absolute),
        "reference": {
            "kind": "analytical",
            "description": description,
            "parameters": dict(parameters),
        },
    }
    if component is not None:
        comparison["component"] = component
    return comparison


def _pressure_plate_case(output_dir: Path) -> ExternalReferenceCase:
    length = 2.0
    width = 1.0
    thickness = 0.01
    pressure = 1000.0
    elastic_modulus = 210.0e9
    poisson_ratio = 0.3
    # The original 2x1 mesh put every node on a supported edge and therefore
    # had identically zero transverse displacement.  The 24x12 mesh includes
    # the analytical center point and resolves CalculiX S4 bending without the
    # severe coarse-mesh stiffness seen in the original deck.
    model = generate_simple_panel_mesh(
        length,
        width,
        thickness,
        num_divisions_x=24,
        num_divisions_y=12,
    )
    model.name = "external_pressure_plate_s4"
    load_case = LoadCase("pressure")
    for element_id in model.mesh.elements:
        load_case.add_pressure_load(element_id, pressure)
    center_displacement, center_von_mises = _navier_plate_observables(
        length=length,
        width=width,
        thickness=thickness,
        pressure=pressure,
        elastic_modulus=elastic_modulus,
        poisson_ratio=poisson_ratio,
    )
    reference_parameters = {
        "length_m": length,
        "width_m": width,
        "thickness_m": thickness,
        "pressure_pa": pressure,
        "elastic_modulus_pa": elastic_modulus,
        "poisson_ratio": poisson_ratio,
        "series_max_odd_index": 99,
    }
    comparisons = [
        _analytical_comparison(
            "plate_max_abs_uz",
            "max_abs_displacement",
            center_displacement,
            component="z",
            relative_tolerance=0.10,
            absolute_tolerance=1.0e-12,
            description="Navier double-sine series at the center of a simply supported thin rectangular plate",
            parameters=reference_parameters,
        ),
        _analytical_comparison(
            "plate_max_von_mises",
            "max_von_mises_stress",
            center_von_mises,
            relative_tolerance=0.15,
            absolute_tolerance=1.0,
            description="Navier plate center moments converted to top/bottom surface plane-stress von Mises stress",
            parameters=reference_parameters,
        ),
        _analytical_comparison(
            "plate_nodal_force_balance_z",
            "sum_nodal_force_balance",
            0.0,
            component="z",
            relative_tolerance=0.0,
            absolute_tolerance=0.1,
            description="Static vertical equilibrium from the complete FRD nodal applied-plus-reaction force field",
            parameters={"pressure_pa": pressure, "loaded_area_m2": length * width},
        ),
    ]
    return write_calculix_input_deck(
        model,
        load_case,
        output_dir / "pressure_plate_s4.inp",
        analysis="static",
        metadata={"purpose": "S4 simply supported pressure-plate external reference"},
        comparisons=comparisons,
    )


def _beam_buckling_case(output_dir: Path) -> ExternalReferenceCase:
    model = FEModel("external_beam_column_buckling")
    elastic_modulus = 210.0e9
    length = 4.0
    second_moment = 5.0e-6
    # The generic writer emits an equivalent square RECT section.  Choose its
    # area from I=A^2/12 so that both the generated deck and the analytical
    # Euler reference have exactly the same section stiffness.
    area = math.sqrt(12.0 * second_moment)
    num_elements = 10
    model.add_material("steel", elastic_modulus, 0.3, density=7850.0)
    section = {"area": area, "Iy": second_moment, "Iz": second_moment, "J": 2.0 * second_moment}
    for i in range(num_elements + 1):
        model.add_node(i + 1, length * i / num_elements, 0.0, 0.0)
    for i in range(num_elements):
        model.add_element(i + 1, BeamElement(i + 1, [i + 1, i + 2], "steel", section))
    all_nodes = list(model.mesh.nodes)
    # Keep the axial field free except for node 1.  The previous deck fixed ux
    # at every node and applied the compression to a constrained node, so it
    # could not establish a geometric-stiffness reference state.
    model.add_boundary_condition(BoundaryCondition("suppress", all_nodes, {"uz": 0.0, "rx": 0.0, "ry": 0.0}))
    model.add_boundary_condition(BoundaryCondition("axial_reference", [1], {"ux": 0.0}))
    end_node = num_elements + 1
    model.add_boundary_condition(BoundaryCondition("pins", [1, end_node], {"uy": 0.0}))
    load_case = LoadCase("unit_compression")
    load_case.add_nodal_load(end_node, [-1.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    critical_load = math.pi**2 * elastic_modulus * second_moment / length**2
    comparisons = [
        _analytical_comparison(
            "column_first_buckling_factor",
            "first_buckling_factor",
            critical_load,
            relative_tolerance=0.05,
            absolute_tolerance=1.0,
            description="Euler pinned-pinned column critical load divided by the unit reference compression",
            parameters={
                "length_m": length,
                "elastic_modulus_pa": elastic_modulus,
                "second_moment_m4": second_moment,
                "reference_compression_n": 1.0,
            },
        )
    ]
    return write_calculix_input_deck(
        model,
        load_case,
        output_dir / "beam_column_buckling.inp",
        analysis="buckling",
        metadata={"purpose": "Pinned-pinned Euler beam-column buckling external reference"},
        comparisons=comparisons,
    )


def _cylindrical_shell_case(output_dir: Path) -> ExternalReferenceCase:
    model = FEModel("external_cylinder_s4_pressure")
    elastic_modulus = 210.0e9
    poisson_ratio = 0.3
    thickness = 0.02
    pressure = 1000.0
    model.add_material("steel", elastic_modulus, poisson_ratio, density=7850.0)
    radius = 1.0
    height = 2.0
    n_circ = 32
    n_z = 8
    node_id = 1
    grid: Dict[Tuple[int, int], int] = {}
    for iz in range(n_z + 1):
        z = height * iz / n_z
        for it in range(n_circ):
            theta = 2.0 * np.pi * it / n_circ
            grid[(iz, it)] = node_id
            model.add_node(node_id, radius * np.cos(theta), radius * np.sin(theta), z)
            node_id += 1
    elem_id = 1
    for iz in range(n_z):
        for it in range(n_circ):
            n1 = grid[(iz, it)]
            n2 = grid[(iz, (it + 1) % n_circ)]
            n3 = grid[(iz + 1, (it + 1) % n_circ)]
            n4 = grid[(iz + 1, it)]
            model.add_element(elem_id, ShellElement(elem_id, [n1, n2, n3, n4], "steel", thickness=thickness))
            elem_id += 1
    bottom = [grid[(0, it)] for it in range(n_circ)]
    top = [grid[(n_z, it)] for it in range(n_circ)]
    model.add_boundary_condition(BoundaryCondition("bottom_uz", bottom, {"uz": 0.0}))
    model.add_boundary_condition(BoundaryCondition("top_uz", top, {"uz": 0.0}))
    # Radially restrain both end rings to eliminate every shell rigid-body and
    # ovalization mechanism.  Comparisons use only the central gauge region,
    # away from these deliberately conservative end restraints.
    model.add_boundary_condition(BoundaryCondition("bottom_xy", bottom, {"ux": 0.0, "uy": 0.0}))
    model.add_boundary_condition(BoundaryCondition("top_xy", top, {"ux": 0.0, "uy": 0.0}))
    load_case = LoadCase("internal_pressure")
    for element_id in model.mesh.elements:
        load_case.add_pressure_load(element_id, pressure)
    hoop_stress = pressure * radius / thickness
    axial_stress = poisson_ratio * hoop_stress
    von_mises = math.sqrt(hoop_stress**2 - hoop_stress * axial_stress + axial_stress**2)
    radial_displacement = pressure * radius**2 * (1.0 - poisson_ratio**2) / (elastic_modulus * thickness)
    reference_parameters = {
        "radius_m": radius,
        "thickness_m": thickness,
        "pressure_pa": pressure,
        "elastic_modulus_pa": elastic_modulus,
        "poisson_ratio": poisson_ratio,
        "axial_condition": "zero axial strain",
        "central_gauge_z_m": [0.75, 1.25],
    }
    radial_comparison = _analytical_comparison(
            "cylinder_mean_abs_radial_displacement",
            "mean_radial_displacement",
            radial_displacement,
            absolute=True,
            relative_tolerance=0.12,
            absolute_tolerance=1.0e-12,
            description="Thin closed-cylinder membrane displacement with axially restrained ends",
            parameters=reference_parameters,
        )
    radial_comparison.update(
        {
            "reference_radius": radius,
            "radial_coordinate_tolerance": 0.015,
            "z_min": 0.75,
            "z_max": 1.25,
        }
    )
    stress_comparison = _analytical_comparison(
            "cylinder_median_von_mises",
            "median_von_mises_stress",
            von_mises,
            relative_tolerance=0.15,
            absolute_tolerance=1.0,
            description="Thin-cylinder membrane hoop stress with Poisson axial stress from zero axial strain",
            parameters=reference_parameters,
        )
    stress_comparison.update(
        {
            "reference_radius": radius,
            "radial_coordinate_tolerance": 0.015,
            "z_min": 0.75,
            "z_max": 1.25,
        }
    )
    comparisons = [radial_comparison, stress_comparison]
    return write_calculix_input_deck(
        model,
        load_case,
        output_dir / "cylinder_s4_pressure.inp",
        analysis="static",
        metadata={"purpose": "Axially restrained cylindrical shell membrane reference"},
        comparisons=comparisons,
    )


def generate_external_reference_cases(output_dir: Path | str = Path("reports/external_references/decks")) -> List[ExternalReferenceCase]:
    """Generate the default external reference decks."""

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    return [_pressure_plate_case(root), _beam_buckling_case(root), _cylindrical_shell_case(root)]


def _numbers(line: str) -> List[float]:
    return [float(token.replace("D", "E").replace("d", "e")) for token in _FLOAT_RE.findall(line)]


def _finalize_frd_dataset(
    parsed: CalculixParsedResults,
    name: Optional[str],
    values: Mapping[int, Tuple[float, ...]],
) -> None:
    label = (name or "").strip().upper()
    if label.startswith("DISP"):
        parsed.displacements.update({node: tuple(row[:3]) for node, row in values.items() if len(row) >= 3})
    elif label.startswith("STRESS"):
        parsed.stresses.update({node: tuple(row[:6]) for node, row in values.items() if len(row) >= 6})
    elif label in {"RF", "FORC", "FORCE", "REACTION"} or label.startswith("FORC"):
        parsed.reaction_forces.update({node: tuple(row[:3]) for node, row in values.items() if len(row) >= 3})


def parse_calculix_frd(path: Path | str) -> CalculixParsedResults:
    """Parse ASCII FRD coordinates, displacements, reactions, and stresses.

    CalculiX ``*NODE FILE``/``*EL FILE`` output is ASCII FRD.  Both short and
    long record widths are accepted; numeric extraction also handles adjacent
    signed fixed-width fields and Fortran ``D`` exponents.
    """

    source = Path(path)
    parsed = CalculixParsedResults(source_files=[str(source)])
    lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    reading_coordinates = False
    dataset_name: Optional[str] = None
    dataset_components = 0
    dataset_header_components = 0
    dataset_values: Dict[int, Tuple[float, ...]] = {}
    pending_node: Optional[int] = None
    pending_values: List[float] = []

    def finish_dataset() -> None:
        nonlocal dataset_name, dataset_components, dataset_header_components, dataset_values, pending_node, pending_values
        _finalize_frd_dataset(parsed, dataset_name, dataset_values)
        dataset_name = None
        dataset_components = 0
        dataset_header_components = 0
        dataset_values = {}
        pending_node = None
        pending_values = []

    for line in lines:
        stripped = line.strip()
        upper = stripped.upper()
        if re.match(r"^2C(?:\s|$)", upper):
            finish_dataset()
            reading_coordinates = True
            continue
        if re.match(r"^(?:3C|100C|9999)(?:\s|$)", upper):
            reading_coordinates = False
        if stripped.startswith("-4"):
            finish_dataset()
            fields = stripped.split()
            dataset_name = fields[1] if len(fields) >= 2 else ""
            if len(fields) >= 3:
                try:
                    dataset_header_components = int(fields[2])
                except ValueError:
                    dataset_header_components = 0
            dataset_components = 0
            reading_coordinates = False
            continue
        if stripped.startswith("-5"):
            fields = stripped.split()
            # FRD header counts can include derived entities such as displacement
            # magnitude ``ALL``.  Derived entities are not present in data rows.
            if len(fields) >= 2 and fields[1].upper() != "ALL":
                dataset_components += 1
            continue
        if stripped.startswith("-3"):
            if dataset_name is not None:
                finish_dataset()
            reading_coordinates = False
            continue
        if not stripped.startswith(("-1", "-2")):
            continue

        values = _numbers(line)
        if reading_coordinates and stripped.startswith("-1") and len(values) >= 5:
            parsed.coordinates[int(values[1])] = (float(values[2]), float(values[3]), float(values[4]))
            continue
        if dataset_name is None or len(values) < 2:
            continue
        if dataset_components <= 0:
            dataset_components = dataset_header_components
        if stripped.startswith("-1"):
            pending_node = int(values[1])
            pending_values = [float(value) for value in values[2:]]
        elif pending_node is not None:
            continuation = [float(value) for value in values[1:]]
            # Material-dependent records contain a material identifier before
            # the actual tensor.  Keeping the final N components handles that
            # form as well as ordinary continuation records.
            if dataset_components and len(continuation) >= dataset_components:
                pending_values = continuation[-dataset_components:]
            else:
                pending_values.extend(continuation)
        if pending_node is not None and dataset_components and len(pending_values) >= dataset_components:
            dataset_values[pending_node] = tuple(pending_values[-dataset_components:])
            pending_node = None
            pending_values = []
    finish_dataset()
    if not parsed.has_results:
        parsed.warnings.append("No recognized result dataset was found in the FRD file")
    return parsed


def _spaced_heading(line: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", line.upper())


def parse_calculix_dat(path: Path | str) -> CalculixParsedResults:
    """Parse DAT buckling/frequency tables and printed reaction totals."""

    source = Path(path)
    parsed = CalculixParsedResults(source_files=[str(source)])
    lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    index = 0
    while index < len(lines):
        compact = _spaced_heading(lines[index])
        if "BUCKLINGFACTOROUTPUT" in compact or ("MODENO" in compact and "BUCKLING" in compact):
            factors: List[float] = []
            for candidate in lines[index + 1 : index + 60]:
                candidate_compact = _spaced_heading(candidate)
                if factors and any(
                    token in candidate_compact
                    for token in ("EIGENVALUEOUTPUT", "DISPLACEMENTS", "STRESSES", "FORCES")
                ):
                    break
                values = _numbers(candidate)
                if len(values) >= 2 and re.match(r"^\s*\d+\s", candidate):
                    factors.append(float(values[1]))
            if factors:
                parsed.buckling_factors = factors
        elif "EIGENVALUEOUTPUT" in compact:
            frequencies: List[float] = []
            for candidate in lines[index + 1 : index + 80]:
                candidate_compact = _spaced_heading(candidate)
                if frequencies and any(token in candidate_compact for token in ("DISPLACEMENTS", "STRESSES", "FORCES")):
                    break
                values = _numbers(candidate)
                if len(values) >= 4 and re.match(r"^\s*\d+\s", candidate):
                    # CalculiX tables list mode, eigenvalue, angular frequency,
                    # and cycles/time.  The fourth numeric field is frequency.
                    frequencies.append(float(values[3]))
            if frequencies:
                parsed.frequencies_hz = frequencies
        elif (
            ("FORCE" in compact or "REACTIONFORCE" in compact)
            and "FX" in compact
            and "FY" in compact
            and "FZ" in compact
        ):
            reactions: Dict[int, Tuple[float, float, float]] = {}
            totals_only = compact.startswith("TOTALFORCE")
            blank_after_data = 0
            for candidate in lines[index + 1 : index + 10000]:
                candidate_compact = _spaced_heading(candidate)
                values = _numbers(candidate)
                if "TOTAL" in candidate_compact and len(values) >= 3:
                    parsed.reaction_total = tuple(float(value) for value in values[-3:])
                    continue
                if totals_only and len(values) >= 3:
                    parsed.reaction_total = tuple(float(value) for value in values[-3:])
                    break
                if len(values) >= 4 and re.match(r"^\s*\d+\s", candidate):
                    reactions[int(values[0])] = tuple(float(value) for value in values[-3:])
                    blank_after_data = 0
                    continue
                if reactions and not candidate.strip():
                    blank_after_data += 1
                    if blank_after_data >= 2:
                        break
                elif reactions and candidate.strip() and any(
                    token in candidate_compact
                    for token in ("DISPLACEMENTS", "STRESSES", "EIGENVALUEOUTPUT", "BUCKLINGFACTOROUTPUT")
                ):
                    break
            parsed.reaction_forces.update(reactions)
        index += 1
    if not parsed.has_results:
        parsed.warnings.append("No recognized result table was found in the DAT file")
    return parsed


def merge_calculix_results(*results: CalculixParsedResults) -> CalculixParsedResults:
    merged = CalculixParsedResults()
    for result in results:
        merged.coordinates.update(result.coordinates)
        merged.displacements.update(result.displacements)
        merged.reaction_forces.update(result.reaction_forces)
        merged.stresses.update(result.stresses)
        if result.reaction_total is not None:
            merged.reaction_total = result.reaction_total
        if result.buckling_factors:
            merged.buckling_factors = list(result.buckling_factors)
        if result.frequencies_hz:
            merged.frequencies_hz = list(result.frequencies_hz)
        merged.source_files.extend(result.source_files)
        merged.warnings.extend(result.warnings)
    return merged


def _component_index(component: Any) -> int:
    key = str(component or "").strip().lower()
    if key not in _COMPONENT_INDEX:
        raise ValueError(f"Unsupported vector component '{component}'")
    return _COMPONENT_INDEX[key]


def _von_mises(stress: Sequence[float]) -> float:
    if len(stress) < 6:
        raise ValueError("A six-component stress tensor is required")
    sxx, syy, szz, sxy, syz, szx = (float(value) for value in stress[:6])
    return math.sqrt(
        max(
            0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2)
            + 3.0 * (sxy**2 + syz**2 + szx**2),
            0.0,
        )
    )


def _filtered_result_nodes(
    results: CalculixParsedResults,
    specification: Mapping[str, Any],
    candidates: Iterable[int],
) -> List[int]:
    node_ids = sorted(int(node_id) for node_id in candidates)
    uses_coordinate_filter = any(
        key in specification
        for key in ("z_min", "z_max", "reference_radius", "radial_coordinate_tolerance")
    )
    if not uses_coordinate_filter:
        return node_ids
    if not results.coordinates:
        raise ValueError("FRD coordinates are required by the observable filter")
    z_min = float(specification.get("z_min", -math.inf))
    z_max = float(specification.get("z_max", math.inf))
    reference_radius = specification.get("reference_radius")
    radial_tolerance = float(specification.get("radial_coordinate_tolerance", math.inf))
    filtered: List[int] = []
    for node_id in node_ids:
        coordinates = results.coordinates.get(node_id)
        if coordinates is None:
            continue
        x, y, z = coordinates
        if not (z_min <= z <= z_max):
            continue
        if reference_radius is not None and abs(math.hypot(x, y) - float(reference_radius)) > radial_tolerance:
            continue
        filtered.append(node_id)
    if not filtered:
        raise ValueError("No result nodes satisfy the declared coordinate filter")
    return filtered


def _extract_observable(results: CalculixParsedResults, specification: Mapping[str, Any]) -> float:
    quantity = str(specification.get("quantity", "")).strip().lower()
    if quantity == "max_abs_displacement":
        if not results.displacements:
            raise ValueError("FRD displacement results are missing")
        component = specification.get("component")
        if component is None or str(component).lower() in {"all", "magnitude"}:
            return max(float(np.linalg.norm(row[:3])) for row in results.displacements.values())
        index = _component_index(component)
        return max(abs(float(row[index])) for row in results.displacements.values())
    if quantity in {"max_von_mises_stress", "median_von_mises_stress"}:
        if not results.stresses:
            raise ValueError("FRD stress results are missing")
        node_ids = _filtered_result_nodes(results, specification, results.stresses)
        values = sorted(_von_mises(results.stresses[node_id]) for node_id in node_ids)
        if quantity == "max_von_mises_stress":
            return float(values[-1])
        middle = len(values) // 2
        return float(values[middle]) if len(values) % 2 else float(0.5 * (values[middle - 1] + values[middle]))
    if quantity == "sum_reaction":
        index = _component_index(specification.get("component"))
        if results.reaction_total is not None:
            return float(results.reaction_total[index])
        if not results.reaction_forces:
            raise ValueError("FRD/DAT reaction results are missing")
        return float(sum(row[index] for row in results.reaction_forces.values()))
    if quantity == "sum_nodal_force_balance":
        index = _component_index(specification.get("component"))
        if not results.reaction_forces:
            raise ValueError("FRD nodal force results are missing")
        return float(sum(row[index] for row in results.reaction_forces.values()))
    if quantity == "mean_radial_displacement":
        shared_nodes = _filtered_result_nodes(
            results,
            specification,
            set(results.coordinates) & set(results.displacements),
        )
        if not shared_nodes:
            raise ValueError("FRD coordinates and displacements are required for radial displacement")
        center_x = float(specification.get("center_x", 0.0))
        center_y = float(specification.get("center_y", 0.0))
        radial_values: List[float] = []
        for node_id in shared_nodes:
            x, y, _z = results.coordinates[node_id]
            ux, uy, _uz = results.displacements[node_id]
            dx = x - center_x
            dy = y - center_y
            radius = math.hypot(dx, dy)
            if radius > 1.0e-15:
                radial_values.append((ux * dx + uy * dy) / radius)
        if not radial_values:
            raise ValueError("No off-axis nodes are available for radial displacement")
        return float(sum(radial_values) / len(radial_values))
    if quantity == "first_buckling_factor":
        if not results.buckling_factors:
            raise ValueError("DAT buckling factors are missing")
        return float(results.buckling_factors[0])
    if quantity == "first_frequency_hz":
        if not results.frequencies_hz:
            raise ValueError("DAT eigenfrequencies are missing")
        return float(results.frequencies_hz[0])
    raise ValueError(f"Unsupported external-reference quantity '{quantity}'")


def evaluate_calculix_comparisons(
    results: CalculixParsedResults,
    specifications: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    """Evaluate parsed observables against explicit absolute/relative tolerances."""

    comparisons: List[Dict[str, Any]] = []
    for specification in specifications:
        row = dict(specification)
        expected = float(specification["expected"])
        relative_tolerance = float(specification.get("relative_tolerance", 0.0))
        absolute_tolerance = float(specification.get("absolute_tolerance", 0.0))
        try:
            actual = _extract_observable(results, specification)
            if bool(specification.get("absolute", False)):
                actual = abs(actual)
            error = abs(actual - expected)
            limit = absolute_tolerance + relative_tolerance * abs(expected)
            row.update(
                {
                    "status": "passed" if math.isfinite(actual) and error <= limit else "failed",
                    "actual": float(actual),
                    "absolute_error": float(error),
                    "relative_error": None if expected == 0.0 else float(error / abs(expected)),
                    "tolerance_limit": float(limit),
                }
            )
        except (KeyError, TypeError, ValueError) as exc:
            row.update({"status": "missing", "error": str(exc)})
        comparisons.append(row)
    return comparisons


def resolve_calculix_executable(executable: Optional[Path | str] = None) -> Path:
    """Resolve an explicit executable, environment override, or PATH command."""

    requested: Optional[str]
    if executable is not None:
        requested = str(executable)
    else:
        requested = os.environ.get(CALCULIX_EXECUTABLE_ENV)
    if requested:
        requested = requested.strip().strip('"')
        candidate = Path(requested).expanduser()
        if candidate.is_file():
            return candidate.resolve()
        located = shutil.which(requested)
        if located:
            return Path(located).resolve()
        raise FileNotFoundError(f"CalculiX executable was not found: {requested}")

    candidate_names = ["ccx", "ccx.exe"]
    for minor in range(30, 9, -1):
        candidate_names.extend(
            [
                f"ccx_2.{minor}",
                f"ccx_2.{minor}.exe",
                f"ccx_2.{minor}_MT",
                f"ccx_2.{minor}_MT.exe",
            ]
        )
    for candidate_name in candidate_names:
        located = shutil.which(candidate_name)
        if located:
            return Path(located).resolve()
    raise FileNotFoundError(
        f"CalculiX executable was not found on PATH; pass an explicit path or set {CALCULIX_EXECUTABLE_ENV}"
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _version_from_text(text: str) -> Optional[str]:
    for line in text.splitlines():
        if "calculix" in line.lower() or re.search(r"\bccx\b", line, re.IGNORECASE):
            match = re.search(r"(?:version\s*)?(\d+\.\d+(?:\.\d+)?)", line, re.IGNORECASE)
            return match.group(1) if match else line.strip()[:200]
    return None


def calculix_solver_provenance(
    executable: Path | str,
    *,
    executable_args: Sequence[str] = (),
    probe_timeout_seconds: float = 10.0,
) -> Dict[str, Any]:
    """Capture executable identity and a best-effort non-blocking version probe."""

    resolved = resolve_calculix_executable(executable)
    stat = resolved.stat()
    probe_command = [str(resolved), *[str(arg) for arg in executable_args], "--version"]
    probe: Dict[str, Any] = {"command": probe_command}
    try:
        completed = subprocess.run(
            probe_command,
            cwd=str(resolved.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=float(probe_timeout_seconds),
            check=False,
        )
        combined = "\n".join(part for part in (completed.stdout, completed.stderr) if part)
        probe.update({"returncode": int(completed.returncode), "output": combined[:4000]})
        version = _version_from_text(combined)
    except (OSError, subprocess.TimeoutExpired) as exc:
        probe.update({"error": str(exc)})
        version = None
    return {
        "name": "CalculiX CrunchiX",
        "executable": str(resolved),
        "sha256": _sha256(resolved),
        "size_bytes": int(stat.st_size),
        "version": version,
        "version_probe": probe,
    }


def _safe_case_directory_name(name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._")
    return safe or "case"


def _timeout_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def run_calculix_reference_case(
    case: ExternalReferenceCase,
    *,
    executable: Path | str,
    run_root: Path | str = DEFAULT_CALCULIX_RUN_PATH,
    executable_args: Sequence[str] = (),
    timeout_seconds: float = 300.0,
    solver_provenance: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Execute one deck in an isolated case directory and validate its results."""

    if float(timeout_seconds) <= 0.0:
        raise ValueError("timeout_seconds must be positive")
    resolved = resolve_calculix_executable(executable)
    root = Path(run_root)
    root.mkdir(parents=True, exist_ok=True)
    work_dir = root / _safe_case_directory_name(case.name)
    work_dir.mkdir(parents=True, exist_ok=True)
    job_name = case.name
    for suffix in (".frd", ".dat", ".sta", ".cvg", ".12d", ".eig", ".stdout.log", ".stderr.log"):
        stale = work_dir / f"{job_name}{suffix}"
        if stale.is_file():
            stale.unlink()
    input_path = work_dir / f"{job_name}.inp"
    metadata_path = work_dir / f"{job_name}.json"
    shutil.copy2(case.inp_path, input_path)
    shutil.copy2(case.metadata_path, metadata_path)

    command = [str(resolved), *[str(arg) for arg in executable_args], "-i", job_name]
    started = time.perf_counter()
    stdout = ""
    stderr = ""
    returncode: Optional[int] = None
    execution_error: Optional[str] = None
    timed_out = False
    try:
        completed = subprocess.run(
            command,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=float(timeout_seconds),
            check=False,
        )
        stdout = completed.stdout
        stderr = completed.stderr
        returncode = int(completed.returncode)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = _timeout_text(exc.stdout)
        stderr = _timeout_text(exc.stderr)
        execution_error = f"CalculiX exceeded the {float(timeout_seconds):g} s timeout"
    except OSError as exc:
        execution_error = str(exc)
    duration = time.perf_counter() - started
    stdout_path = work_dir / f"{job_name}.stdout.log"
    stderr_path = work_dir / f"{job_name}.stderr.log"
    stdout_path.write_text(stdout, encoding="utf-8")
    stderr_path.write_text(stderr, encoding="utf-8")

    result: Dict[str, Any] = {
        "status": "execution_failed",
        "executed": True,
        "command": command,
        "working_directory": str(work_dir),
        "returncode": returncode,
        "timed_out": timed_out,
        "timeout_seconds": float(timeout_seconds),
        "duration_seconds": float(duration),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "solver_version": (solver_provenance or {}).get("version") or _version_from_text(stdout + "\n" + stderr),
        "comparisons": [],
    }
    if execution_error is not None:
        result["error"] = execution_error
        return result
    if returncode != 0:
        result["error"] = f"CalculiX exited with code {returncode}"
        return result

    parsed_parts: List[CalculixParsedResults] = []
    parse_errors: List[str] = []
    frd_path = work_dir / f"{job_name}.frd"
    dat_path = work_dir / f"{job_name}.dat"
    if frd_path.is_file():
        try:
            parsed_parts.append(parse_calculix_frd(frd_path))
        except (OSError, UnicodeError, ValueError) as exc:
            parse_errors.append(f"{frd_path.name}: {exc}")
    if dat_path.is_file():
        try:
            parsed_parts.append(parse_calculix_dat(dat_path))
        except (OSError, UnicodeError, ValueError) as exc:
            parse_errors.append(f"{dat_path.name}: {exc}")
    parsed = merge_calculix_results(*parsed_parts)
    comparisons = evaluate_calculix_comparisons(parsed, case.comparisons)
    result.update(
        {
            "output_files": {
                "frd": str(frd_path) if frd_path.is_file() else None,
                "dat": str(dat_path) if dat_path.is_file() else None,
            },
            "parsed_results": parsed.summary(),
            "parse_errors": parse_errors,
            "comparisons": comparisons,
        }
    )
    if parse_errors:
        result["status"] = "parse_failed"
    elif not parsed.has_results:
        result["status"] = "results_missing"
        result["error"] = "CalculiX returned success but no recognized FRD/DAT result was parsed"
    elif not comparisons:
        result["status"] = "not_validated"
        result["error"] = "No numerical comparison specifications were declared"
    elif all(item.get("status") == "passed" for item in comparisons):
        result["status"] = "passed"
    elif any(item.get("status") == "missing" for item in comparisons):
        result["status"] = "incomplete_results"
    else:
        result["status"] = "failed"
    return result


def generate_external_reference_report(
    output_dir: Path | str = Path("reports/external_references/decks"),
    *,
    execute: bool = False,
    calculix_executable: Optional[Path | str] = None,
    calculix_args: Sequence[str] = (),
    run_dir: Path | str = DEFAULT_CALCULIX_RUN_PATH,
    timeout_seconds: float = 300.0,
) -> Dict[str, Any]:
    """Generate decks and optionally execute tolerance-controlled validation."""

    cases = generate_external_reference_cases(output_dir)
    case_rows: List[Dict[str, Any]] = []
    report: Dict[str, Any] = {
        "status": "not_executed",
        "schema_version": 2,
        "validation_performed": False,
        "execution_mode": "calculix" if execute else "deck_only",
        "cases": case_rows,
        "known_limitations": [
            "Deck-only mode generates reproducible inputs but is explicitly not numerical validation.",
            "The reference pack covers linear static shell response and linear eigenvalue buckling; nonlinear external comparisons remain out of scope.",
        ],
    }
    if not execute:
        for case in cases:
            row = case.to_dict()
            row["validation"] = {"status": "not_executed", "executed": False, "comparisons": []}
            case_rows.append(row)
        return report

    try:
        resolved = resolve_calculix_executable(calculix_executable)
        provenance = calculix_solver_provenance(resolved, executable_args=calculix_args)
    except (FileNotFoundError, OSError, ValueError) as exc:
        report["status"] = "solver_unavailable"
        report["error"] = str(exc)
        for case in cases:
            row = case.to_dict()
            row["validation"] = {
                "status": "solver_unavailable",
                "executed": False,
                "error": str(exc),
                "comparisons": [],
            }
            case_rows.append(row)
        return report

    report["solver"] = provenance
    report["validation_performed"] = True
    for case in cases:
        validation = run_calculix_reference_case(
            case,
            executable=resolved,
            run_root=run_dir,
            executable_args=calculix_args,
            timeout_seconds=timeout_seconds,
            solver_provenance=provenance,
        )
        row = case.to_dict()
        row["validation"] = validation
        case_rows.append(row)
        if provenance.get("version") is None and validation.get("solver_version"):
            provenance["version"] = validation["solver_version"]
    report["status"] = "passed" if cases and all(
        row.get("validation", {}).get("status") == "passed" for row in case_rows
    ) else "failed"
    return report


def _markdown(report: Mapping[str, Any]) -> str:
    lines = ["# External FE Reference Report", "", f"- Status: {report.get('status')}"]
    lines.append(f"- Execution mode: {report.get('execution_mode')}")
    solver = report.get("solver")
    if isinstance(solver, Mapping):
        lines.append(f"- Solver: {solver.get('name')} {solver.get('version') or '(version not reported)'}")
        lines.append(f"- Executable: `{solver.get('executable')}`")
        lines.append(f"- Executable SHA-256: `{solver.get('sha256')}`")
    lines.extend(["", "## Cases", ""])
    for case in report.get("cases", []):
        summary = case.get("model_summary", {})
        validation = case.get("validation", {})
        lines.append(f"### {case.get('name')}")
        lines.append(f"- Kind: {case.get('kind')}")
        lines.append(f"- Input: `{case.get('inp_path')}`")
        lines.append(f"- Nodes: {summary.get('nodes')}")
        lines.append(f"- Elements: {summary.get('elements')}")
        lines.append(f"- Validation: {validation.get('status')}")
        for comparison in validation.get("comparisons", []):
            lines.append(
                f"- `{comparison.get('name')}`: {comparison.get('status')} "
                f"(actual={comparison.get('actual')}, expected={comparison.get('expected')})"
            )
        if validation.get("error"):
            lines.append(f"- Error: {validation.get('error')}")
        lines.append("")
    lines.extend(["## Known Limitations", ""])
    for item in report.get("known_limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def write_external_reference_report(
    output: Path | str = DEFAULT_EXTERNAL_REFERENCE_PATH,
    *,
    deck_dir: Path | str = Path("reports/external_references/decks"),
    markdown: Optional[Path | str] = None,
    execute: bool = False,
    calculix_executable: Optional[Path | str] = None,
    calculix_args: Sequence[str] = (),
    run_dir: Path | str = DEFAULT_CALCULIX_RUN_PATH,
    timeout_seconds: float = 300.0,
) -> Dict[str, Any]:
    """Generate decks and write a JSON/Markdown report."""

    report = generate_external_reference_report(
        deck_dir,
        execute=execute,
        calculix_executable=calculix_executable,
        calculix_args=calculix_args,
        run_dir=run_dir,
        timeout_seconds=timeout_seconds,
    )
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if markdown is not None:
        markdown_path = Path(markdown)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(_markdown(report), encoding="utf-8")
    return report
