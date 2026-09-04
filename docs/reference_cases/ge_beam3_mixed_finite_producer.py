"""Emit deterministic finite-case proof packets from the private mixed candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from pathlib import Path
import sys
from typing import Any

import numpy as np

from anysolver._ge_beam3_mixed_ad import rotation_exponential
from anysolver.beam_sections import GeneralizedBeamSection, generalized_beam_stiffness
from anysolver.fe_core import FEModel
from anysolver.ge_beam3_mixed_element import (
    GE_BEAM3_MIXED_CANDIDATE_ID,
    GeometricallyExactBeam3D3NElement,
)


SCHEMA = "anysolver.ge-beam3-mixed-finite-proof-v2"
ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIRECTORY = Path(__file__).resolve().parent
BASE_COMMIT = "09351645ba17a0a5b130a1c7a48007d36dd08ada"
BASE_TREE = "cfb0cf9a19f6519abf335694253efa264cd2e695"
AUTHORITY_INPUTS = (
    "ge_beam3_mixed_baseline.json",
    "ge_beam3_mixed_equation_map_a.json",
    "ge_beam3_mixed_equation_map_b.json",
    "ge_beam3_mixed_local_contract.json",
    "ge_beam3_mixed_source_ledger.json",
)
PROGRAM_INPUTS = (
    "docs/reference_cases/ge_beam3_mixed_finite_producer.py",
    "docs/reference_cases/ge_beam3_mixed_finite_checker.py",
    "src/anysolver/_ge_beam3_mixed_ad.py",
    "src/anysolver/ge_beam3_mixed_element.py",
)


def _canonical_bytes(value: Any) -> bytes:
    def visit(item: Any) -> None:
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("nonfinite proof value")
        if isinstance(item, dict):
            for child in item.values():
                visit(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                visit(child)

    visit(value)
    return (json.dumps(value, allow_nan=False, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n").encode()


def _hex_array(values: Any) -> Any:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim == 0:
        return float(array).hex()
    return [_hex_array(entry) for entry in array]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _hashed(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest().upper()


def _strict_json(path: Path) -> dict[str, Any]:
    def pairs(entries: list[tuple[str, Any]]) -> dict[str, Any]:
        made: dict[str, Any] = {}
        for key, value in entries:
            if key in made:
                raise ValueError(f"duplicate JSON key in {path.name}: {key}")
            made[key] = value
        return made

    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"nonfinite {value}")),
    )


def _bindings() -> dict[str, Any]:
    source_ledger = _strict_json(REFERENCE_DIRECTORY / "ge_beam3_mixed_source_ledger.json")
    environment = {
        "byteorder": sys.byteorder,
        "machine": platform.machine(),
        "numpy_version": np.__version__,
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "system": platform.system(),
    }
    base = {"commit": BASE_COMMIT, "tree": BASE_TREE}
    return {
        "authority_inputs": {
            name: _sha256(REFERENCE_DIRECTORY / name) for name in AUTHORITY_INPUTS
        },
        "base": {**base, "identity_sha256": _hashed(base)},
        "environment": {**environment, "identity_sha256": _hashed(environment)},
        "programs": {path: _sha256(ROOT / path) for path in PROGRAM_INPUTS},
        "source_artifacts": {
            source["id"]: source["artifact"]
            for source in source_ledger["sources"]
            if source.get("artifact") is not None
        },
    }


def _section() -> GeneralizedBeamSection:
    lower = np.array(
        (
            (2, 0, 0, 0, 0, 0),
            (1, 3, 0, 0, 0, 0),
            (0, 1, 2, 0, 0, 0),
            (1, 0, 0, 3, 0, 0),
            (0, 1, 0, 1, 2, 0),
            (0, 0, 1, 0, 1, 2),
        ),
        dtype=float,
    )
    return GeneralizedBeamSection(lower @ lower.T, name="mixed-finite-oracle-section")


def _case_definitions() -> tuple[tuple[str, np.ndarray], ...]:
    reference = np.zeros((3, 6))
    rigid = np.zeros((3, 6))
    rigid[:, 3:] = (0.37, -0.21, 0.19)
    rotation = rotation_exponential(rigid[0, 3:])
    coordinates = np.array(((0.0, 0.0, 0.0), (0.5, 0.0, 0.0), (1.0, 0.0, 0.0)))
    rigid[:, :3] = coordinates @ rotation.T + (0.8, -0.4, 0.6) - coordinates
    axial_shear = np.array(
        (
            (0.000, 0.000, 0.000, 0.02, -0.01, 0.015),
            (0.012, 0.026, -0.013, -0.01, 0.025, -0.035),
            (0.031, 0.081, -0.029, 0.015, -0.02, 0.045),
        )
    )
    bend_twist = np.array(
        (
            (0.000, 0.000, 0.000, 0.05, -0.04, 0.03),
            (-0.007, 0.061, 0.028, -0.16, 0.12, -0.21),
            (-0.022, 0.184, 0.091, 0.24, -0.19, 0.29),
        )
    )
    noncommuting = np.array(
        (
            (0.000, 0.000, 0.000, 0.20, -0.14, 0.10),
            (-0.019, 0.086, 0.044, 0.42, 0.24, -0.18),
            (0.028, 0.203, -0.129, -0.22, 0.38, 0.31),
        )
    )
    return (
        ("REFERENCE", reference),
        ("RIGID_COMMON", rigid),
        ("AXIAL_SHEAR", axial_shear),
        ("BEND_TWIST", bend_twist),
        ("NONCOMMUTING", noncommuting),
    )


def _make_element(
    *,
    reversed_nodes: bool = False,
    length: float = 1.0,
    origin: Any = (0.0, 0.0, 0.0),
    axis: Any = (1.0, 0.0, 0.0),
    orientation: Any = (0.0, 1.0, 0.0),
    section: GeneralizedBeamSection | None = None,
):
    made_axis = np.asarray(axis, dtype=np.float64)
    made_axis /= np.linalg.norm(made_axis)
    made_origin = np.asarray(origin, dtype=np.float64)
    model = FEModel("ge-beam3-mixed-proof")
    model.add_material("mat", 1.0, 0.25, density=1.0)
    for node, fraction in enumerate((0.0, 0.5, 1.0), start=1):
        coordinate = made_origin + fraction * length * made_axis
        model.add_node(node, *coordinate)
    element = GeometricallyExactBeam3D3NElement(
        1,
        [3, 2, 1] if reversed_nodes else [1, 2, 3],
        "mat",
        section=_section() if section is None else section,
        reference_orientation=orientation,
        reference_axis_direction=made_axis,
    )
    return model, element


def _record(case_id: str, values: np.ndarray, *, reversed_nodes: bool = False) -> dict[str, Any]:
    model, element = _make_element(reversed_nodes=reversed_nodes)
    ordered = np.array(values[::-1] if reversed_nodes else values, copy=True)
    frame = element.reference_triad(model.mesh)
    rotations = np.asarray([rotation_exponential(row[3:]) @ frame for row in ordered])
    ordered[:, 3:] = 0.0
    local_values = ordered.reshape(18)
    energy, residual, tangent, fields = element.evaluate_candidate(
        model.mesh, local_values, rotation_matrices=rotations
    )
    assert tangent is not None
    reference = element.get_node_coordinates(model.mesh)
    nodal = local_values.reshape(3, 6)
    positions = reference + nodal[:, :3]
    section = element._section_stiffness(model.mesh)
    content = {
        "case_id": case_id + ("_REVERSED" if reversed_nodes else ""),
        "cell_length": float(0.5).hex(),
        "energy": float(energy).hex(),
        "local_iterations": int(fields["local_iterations"]),
        "local_moments": _hex_array(fields["local_moments"]),
        "local_residual_norm": float(fields["local_residual_norm"]).hex(),
        "local_rotations": _hex_array(fields["local_rotations"]),
        "positions": _hex_array(positions),
        "residual": _hex_array(residual),
        "section": _hex_array(section),
        "tangent": _hex_array(tangent),
        "vertex_rotations": _hex_array(rotations),
    }
    content["content_sha256"] = hashlib.sha256(_canonical_bytes(content)).hexdigest().upper()
    return content


def _material_case_record(
    case_id: str,
    local_values: np.ndarray,
    *,
    axis: Any = (1.0, 0.0, 0.0),
    orientation: Any = (0.0, 1.0, 0.0),
    primary_component: str,
) -> dict[str, Any]:
    model, element = _make_element(axis=axis, orientation=orientation)
    frame = element.reference_triad(model.mesh)
    values = np.asarray(local_values, dtype=np.float64).reshape(3, 6)
    displacement = np.zeros((3, 6))
    displacement[:, :3] = values[:, :3] @ frame.T
    rotations = np.asarray(
        [rotation_exponential(frame @ row[3:]) @ frame for row in values]
    )
    energy, residual, tangent, fields = element.evaluate_candidate(
        model.mesh,
        displacement.reshape(18),
        rotation_matrices=rotations,
    )
    assert tangent is not None
    section = element._section_stiffness(model.mesh)
    content = {
        "axis": _hex_array(np.asarray(axis, dtype=np.float64) / np.linalg.norm(axis)),
        "case_id": case_id,
        "cell_length": float(0.5).hex(),
        "energy": float(energy).hex(),
        "generalized_resultant": _hex_array(fields["generalized_resultant"]),
        "generalized_strain": _hex_array(fields["generalized_strain"]),
        "local_iterations": int(fields["local_iterations"]),
        "local_moments": _hex_array(fields["local_moments"]),
        "local_residual_norm": float(fields["local_residual_norm"]).hex(),
        "local_rotations": _hex_array(fields["local_rotations"]),
        "nodal_input_local": _hex_array(values),
        "orientation": _hex_array(orientation),
        "origin": _hex_array((0.0, 0.0, 0.0)),
        "primary_component": primary_component,
        "residual": _hex_array(residual),
        "residual_inf": float(np.linalg.norm(residual, ord=np.inf)).hex(),
        "section": _hex_array(section),
        "tangent": _hex_array(tangent),
        "total_length": float(1.0).hex(),
    }
    content["content_sha256"] = _hashed(content)
    return content


def _isolated_mode_records() -> list[dict[str, Any]]:
    stations = np.asarray((0.0, 0.5, 1.0))
    amplitude = 2.0e-4
    patterns: list[tuple[str, str, np.ndarray]] = []

    axial = np.zeros((3, 6))
    axial[:, 0] = amplitude * stations
    patterns.append(("ISOLATED_AXIAL", "eps_x", axial))

    shear_y = np.zeros((3, 6))
    shear_y[:, 1] = amplitude * stations
    patterns.append(("ISOLATED_SHEAR_Y", "gamma_xy", shear_y))

    shear_z = np.zeros((3, 6))
    shear_z[:, 2] = amplitude * stations
    patterns.append(("ISOLATED_SHEAR_Z", "gamma_xz", shear_z))

    torsion = np.zeros((3, 6))
    torsion[:, 3] = amplitude * stations
    patterns.append(("ISOLATED_TORSION", "kappa_x", torsion))

    bend_y = np.zeros((3, 6))
    bend_y[:, 2] = -0.5 * amplitude * stations**2
    bend_y[:, 4] = amplitude * stations
    patterns.append(("ISOLATED_BENDING_Y", "kappa_y", bend_y))

    bend_z = np.zeros((3, 6))
    bend_z[:, 1] = 0.5 * amplitude * stations**2
    bend_z[:, 5] = amplitude * stations
    patterns.append(("ISOLATED_BENDING_Z", "kappa_z", bend_z))

    return [
        _material_case_record(case_id, values, primary_component=component)
        for case_id, component, values in patterns
    ]


def _orientation_records() -> list[dict[str, Any]]:
    local = np.array(
        (
            (0.000, 0.000, 0.000, 0.08, -0.05, 0.03),
            (0.004, 0.011, -0.008, -0.04, 0.09, -0.07),
            (0.013, 0.027, 0.016, 0.11, 0.04, -0.10),
        )
    )
    definitions = (
        ("ORIENTATION_ROLLED_X", (1.0, 0.0, 0.0), (0.0, 1.0, 1.0)),
        ("ORIENTATION_SKEW_A", (1.0, 2.0, 3.0), (-2.0, 1.0, 0.4)),
        ("ORIENTATION_SKEW_B", (-2.0, 1.0, 4.0), (0.3, 1.0, -0.1)),
    )
    return [
        _material_case_record(
            case_id,
            local,
            axis=axis,
            orientation=orientation,
            primary_component="GENERAL_COUPLED_RESPONSE",
        )
        for case_id, axis, orientation in definitions
    ]


def _normalized_spectrum(matrix: np.ndarray) -> tuple[np.ndarray, int]:
    diagonal = np.abs(np.diag(matrix))
    floor = max(float(np.max(diagonal)) * np.finfo(np.float64).eps, np.finfo(np.float64).tiny)
    scale = np.sqrt(np.maximum(diagonal, floor))
    normalized = matrix / scale[:, None] / scale[None, :]
    eigenvalues = np.linalg.eigvalsh(0.5 * (normalized + normalized.T))
    threshold = 2.0e-9 * max(1.0, float(np.max(np.abs(eigenvalues))))
    return eigenvalues, int(np.count_nonzero(np.abs(eigenvalues) > threshold))


def _slender_section(ratio: float) -> GeneralizedBeamSection:
    height = 1.0 / ratio
    area = height**2
    inertia = height**4 / 12.0
    shear_modulus = 0.4
    torsion_constant = height**4 / 6.0
    diagonal = (
        area,
        (5.0 / 6.0) * shear_modulus * area,
        (5.0 / 6.0) * shear_modulus * area,
        shear_modulus * torsion_constant,
        inertia,
        inertia,
    )
    return GeneralizedBeamSection(np.diag(diagonal), name=f"slender-{ratio:.0f}")


def _slenderness_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for ratio in (10.0, 100.0, 10_000.0, 1_000_000.0):
        made_section = _slender_section(ratio)
        model, element = _make_element(section=made_section)
        energy, residual, tangent, _fields = element.evaluate_candidate(model.mesh, np.zeros(18))
        assert tangent is not None
        # Fixing all six coordinates of end vertex 1 gives a deterministic
        # 12-dimensional representative of the quotient by rigid motion.  It
        # avoids misclassifying roundoff in nominally zero full-space modes as
        # a physical slender-beam mode.
        anchored_complement = tangent[6:, 6:]
        eigenvalues, rank = _normalized_spectrum(anchored_complement)
        unit_tip_force = np.zeros(12)
        unit_tip_force[7] = 1.0
        anchored_displacement = np.linalg.solve(anchored_complement, unit_tip_force)
        tip_response = float(anchored_displacement[7])
        height = 1.0 / ratio
        area = height**2
        bending_inertia = height**4 / 12.0
        shear_stiffness = (5.0 / 6.0) * 0.4 * area
        independent_tip_reference = 1.0 / (3.0 * bending_inertia) + 1.0 / shear_stiffness
        tip_relative_error = abs(tip_response - independent_tip_reference) / independent_tip_reference
        content = {
            "anchored_complement": "NODE_1_ALL_SIX_COORDINATES_ZERO",
            "anchored_complement_normalized_eigenvalues": _hex_array(eigenvalues),
            "anchored_complement_rank": rank,
            "anchored_displacement": _hex_array(anchored_displacement),
            "axis": _hex_array((1.0, 0.0, 0.0)),
            "case_id": f"SLENDERNESS_L_OVER_H_{int(ratio)}",
            "energy": float(energy).hex(),
            "l_over_h": float(ratio).hex(),
            "orientation": _hex_array((0.0, 1.0, 0.0)),
            "origin": _hex_array((0.0, 0.0, 0.0)),
            "residual_inf": float(np.linalg.norm(residual, ord=np.inf)).hex(),
            "section": _hex_array(element._section_stiffness(model.mesh)),
            "stiffness": _hex_array(tangent),
            "stiffness_sha256": _hashed(_hex_array(tangent)),
            "tip_response": tip_response.hex(),
            "tip_response_independent_reference": float(independent_tip_reference).hex(),
            "tip_response_relative_error": float(tip_relative_error).hex(),
            "total_length": float(1.0).hex(),
            "unit_tip_force": _hex_array(unit_tip_force),
        }
        content["content_sha256"] = _hashed(content)
        records.append(content)
    return records


def _multi_element_spectrum() -> dict[str, Any]:
    model = FEModel("ge-beam3-mixed-two-macro-spectrum")
    model.add_material("mat", 1.0, 0.25, density=1.0)
    for node, coordinate in enumerate((0.0, 0.5, 1.0, 1.5, 2.0), start=1):
        model.add_node(node, coordinate, 0.0, 0.0)
    elements = (
        GeometricallyExactBeam3D3NElement(
            1,
            (1, 2, 3),
            "mat",
            section=_section(),
            reference_orientation=(0.0, 1.0, 0.0),
            reference_axis_direction=(1.0, 0.0, 0.0),
        ),
        GeometricallyExactBeam3D3NElement(
            2,
            (3, 4, 5),
            "mat",
            section=_section(),
            reference_orientation=(0.0, 1.0, 0.0),
            reference_axis_direction=(1.0, 0.0, 0.0),
        ),
    )
    assembled = np.zeros((30, 30))
    for element in elements:
        tangent = element.compute_candidate_stiffness_matrix(model.mesh)
        indices = np.asarray(
            [6 * (node_id - 1) + dof for node_id in element.node_ids for dof in range(6)]
        )
        assembled[np.ix_(indices, indices)] += tangent
    eigenvalues, rank = _normalized_spectrum(assembled)
    content = {
        "assembled_stiffness": _hex_array(assembled),
        "axis": _hex_array((1.0, 0.0, 0.0)),
        "case_id": "TWO_MACRO_COLLINEAR_LINEAR_SPECTRUM",
        "dof_count": 30,
        "element_count": 2,
        "element_node_indices": [[0, 1, 2], [2, 3, 4]],
        "node_coordinates": _hex_array(
            np.asarray(((0.0, 0.0, 0.0), (0.5, 0.0, 0.0), (1.0, 0.0, 0.0), (1.5, 0.0, 0.0), (2.0, 0.0, 0.0)))
        ),
        "normalized_eigenvalues": _hex_array(eigenvalues),
        "normalized_rank": rank,
        "orientation": _hex_array((0.0, 1.0, 0.0)),
        "section": _hex_array(generalized_beam_stiffness(_section())),
        "stiffness_sha256": _hashed(_hex_array(assembled)),
    }
    content["content_sha256"] = _hashed(content)
    return content


def _coverage_diagnostics() -> dict[str, Any]:
    content = {
        "classification_authority": True,
        "geometry_scope": "GLOBALLY_STRAIGHT_COLLINEAR_TWO_EQUAL_CELL_ZERO_REFERENCE_JUMP_ONLY",
        "isolated_modes": _isolated_mode_records(),
        "multi_element_spectrum": _multi_element_spectrum(),
        "physical_reference_orientations": _orientation_records(),
        "schema": "anysolver.ge-beam3-mixed-finite-coverage-diagnostics-v1",
        "slenderness": _slenderness_records(),
    }
    content["content_sha256"] = _hashed(content)
    return content


def build_proof(*, mutate: str | None = None) -> dict[str, Any]:
    records = [_record(case_id, values) for case_id, values in _case_definitions()]
    records.append(_record("NONCOMMUTING", _case_definitions()[-1][1], reversed_nodes=True))
    if mutate is not None:
        allowed = {"energy", "local_moment", "residual", "section", "tangent"}
        if mutate not in allowed:
            raise ValueError(f"unknown mutation {mutate}")
        target = records[2]
        if mutate == "energy":
            target["energy"] = float(float.fromhex(target["energy"]) + 1.0e-3).hex()
        elif mutate == "local_moment":
            target["local_moments"][0][0][0] = float(float.fromhex(target["local_moments"][0][0][0]) + 1.0e-3).hex()
        elif mutate == "residual":
            target["residual"][0] = float(float.fromhex(target["residual"][0]) + 1.0e-3).hex()
        elif mutate == "section":
            target["section"][0][0] = float(float.fromhex(target["section"][0][0]) + 1.0e-3).hex()
        else:
            target["tangent"][6][6] = float(float.fromhex(target["tangent"][6][6]) + 1.0e-2).hex()
    return {
        "bindings": _bindings(),
        "candidate_id": GE_BEAM3_MIXED_CANDIDATE_ID,
        "case_order": [record["case_id"] for record in records],
        "coverage_diagnostics": _coverage_diagnostics(),
        "mutation": mutate,
        "records": records,
        "schema": SCHEMA,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mutate", choices=("energy", "local_moment", "residual", "section", "tangent"))
    args = parser.parse_args()
    payload = _canonical_bytes(build_proof(mutate=args.mutate))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
