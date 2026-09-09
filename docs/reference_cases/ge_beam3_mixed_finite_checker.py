"""Independent finite checker for the two-cell mixed GE-B3 proof packet.

This module reconstructs the printed mixed potential and differentiates it
numerically in a fixed left-multiplicative chart.  It imports no ANYsolver,
legacy beam, V1 beam, or production automatic-differentiation code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any

import numpy as np


CANDIDATE_ID = "CANDIDATE_GE_BEAM3_DC_MIXED_K1_MACRO_V2"
PROOF_SCHEMA = "anysolver.ge-beam3-mixed-finite-proof-v2"
SCHEMA = "anysolver.ge-beam3-mixed-finite-check-v2"
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
CELLS = ((0, 1), (1, 2))
MASS = np.array(((1.0 / 3.0, 1.0 / 6.0), (1.0 / 6.0, 1.0 / 3.0)))
REFERENCE_COORDINATES = np.array(((0.0, 0.0, 0.0), (0.5, 0.0, 0.0), (1.0, 0.0, 0.0)))
REFERENCE_SECTION = np.array(
    (
        (4.0, 2.0, 0.0, 2.0, 0.0, 0.0),
        (2.0, 10.0, 3.0, 1.0, 3.0, 0.0),
        (0.0, 3.0, 5.0, 0.0, 1.0, 2.0),
        (2.0, 1.0, 0.0, 10.0, 3.0, 0.0),
        (0.0, 3.0, 1.0, 3.0, 6.0, 2.0),
        (0.0, 0.0, 2.0, 0.0, 2.0, 6.0),
    )
)
REVERSAL_STRAIN_MAP = np.diag((1.0, -1.0, 1.0, 1.0, -1.0, 1.0))
REVERSED_REFERENCE_FRAME = np.diag((-1.0, 1.0, -1.0))
RECORD_KEYS = {
    "case_id",
    "cell_length",
    "content_sha256",
    "energy",
    "local_iterations",
    "local_moments",
    "local_residual_norm",
    "local_rotations",
    "positions",
    "residual",
    "section",
    "tangent",
    "vertex_rotations",
}
MATERIAL_COVERAGE_KEYS = {
    "axis",
    "case_id",
    "cell_length",
    "content_sha256",
    "energy",
    "generalized_resultant",
    "generalized_strain",
    "local_iterations",
    "local_moments",
    "local_residual_norm",
    "local_rotations",
    "nodal_input_local",
    "orientation",
    "origin",
    "primary_component",
    "residual",
    "residual_inf",
    "section",
    "tangent",
    "total_length",
}
SLENDERNESS_KEYS = {
    "anchored_complement",
    "anchored_complement_normalized_eigenvalues",
    "anchored_complement_rank",
    "anchored_displacement",
    "axis",
    "case_id",
    "content_sha256",
    "energy",
    "l_over_h",
    "orientation",
    "origin",
    "residual_inf",
    "section",
    "stiffness",
    "stiffness_sha256",
    "tip_response",
    "tip_response_independent_reference",
    "tip_response_relative_error",
    "total_length",
    "unit_tip_force",
}
SPECTRUM_KEYS = {
    "assembled_stiffness",
    "axis",
    "case_id",
    "content_sha256",
    "dof_count",
    "element_count",
    "element_node_indices",
    "node_coordinates",
    "normalized_eigenvalues",
    "normalized_rank",
    "orientation",
    "section",
    "stiffness_sha256",
}


def _pairs_rejecting_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise ValueError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def _canonical_bytes(value: Any) -> bytes:
    def clean(item: Any) -> Any:
        if isinstance(item, np.generic):
            return item.item()
        if isinstance(item, dict):
            return {key: clean(child) for key, child in item.items()}
        if isinstance(item, (list, tuple)):
            return [clean(child) for child in item]
        return item

    return (json.dumps(clean(value), allow_nan=False, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n").encode()


def _canonical_lf_text_bytes(data: bytes) -> bytes:
    if b"\0" in data:
        raise ValueError("repository text input contains NUL")
    normalized = data.replace(b"\r\n", b"\n")
    if b"\r" in normalized:
        raise ValueError("repository text input contains a lone carriage return")
    return normalized


def _repository_text_binding(relative_path: str) -> dict[str, Any]:
    path = ROOT / relative_path
    raw = subprocess.check_output(
        ("git", "ls-files", "--stage", "-z", "--", relative_path),
        cwd=ROOT,
        stderr=subprocess.DEVNULL,
    )
    entries = [entry for entry in raw.split(b"\0") if entry]
    regular = path.is_file() and not path.is_symlink()
    try:
        working = _canonical_lf_text_bytes(path.read_bytes()) if regular else None
    except (OSError, ValueError):
        working = None
    if len(entries) != 1 or b"\t" not in entries[0]:
        return {
            "git_blob_is_canonical_lf_text": False,
            "git_blob_oid": None,
            "sha256": None,
            "working_tree_matches_git_blob": False,
        }
    metadata, registered_path = entries[0].split(b"\t", 1)
    fields = metadata.split()
    registered = registered_path.decode("utf-8", errors="surrogateescape").replace("\\", "/")
    if len(fields) != 3 or fields[2] != b"0" or registered != relative_path:
        return {
            "git_blob_is_canonical_lf_text": False,
            "git_blob_oid": None,
            "sha256": None,
            "working_tree_matches_git_blob": False,
        }
    oid = fields[1].decode("ascii")
    blob = subprocess.check_output(
        ("git", "cat-file", "blob", oid), cwd=ROOT, stderr=subprocess.DEVNULL
    )
    try:
        canonical_blob = _canonical_lf_text_bytes(blob)
        canonical_blob_ok = canonical_blob == blob
    except ValueError:
        canonical_blob = b""
        canonical_blob_ok = False
    return {
        "git_blob_is_canonical_lf_text": canonical_blob_ok,
        "git_blob_oid": oid,
        "sha256": hashlib.sha256(canonical_blob).hexdigest().upper(),
        "working_tree_matches_git_blob": bool(
            canonical_blob_ok and working is not None and working == blob
        ),
    }


def _hashed(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest().upper()


def _load(path: Path) -> dict[str, Any]:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_pairs_rejecting_duplicates,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"nonfinite {value}")),
    )


def _expected_bindings() -> dict[str, Any]:
    source_ledger = _load(REFERENCE_DIRECTORY / "ge_beam3_mixed_source_ledger.json")
    repository_paths = tuple(
        f"docs/reference_cases/{name}" for name in AUTHORITY_INPUTS
    ) + PROGRAM_INPUTS
    repository_bindings = {
        path: _repository_text_binding(path) for path in repository_paths
    }
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
            name: repository_bindings[f"docs/reference_cases/{name}"]["sha256"]
            for name in AUTHORITY_INPUTS
        },
        "base": {**base, "identity_sha256": _hashed(base)},
        "environment": {**environment, "identity_sha256": _hashed(environment)},
        "programs": {
            path: repository_bindings[path]["sha256"] for path in PROGRAM_INPUTS
        },
        "repository_git_blob_oids": {
            path: binding["git_blob_oid"]
            for path, binding in repository_bindings.items()
        },
        "repository_git_blobs_are_canonical_lf_text": {
            path: binding["git_blob_is_canonical_lf_text"]
            for path, binding in repository_bindings.items()
        },
        "repository_working_tree_matches_git_blobs": {
            path: binding["working_tree_matches_git_blob"]
            for path, binding in repository_bindings.items()
        },
        "source_artifacts": {
            source["id"]: source["artifact"]
            for source in source_ledger["sources"]
            if source.get("artifact") is not None
        },
    }


def _decode(value: Any) -> Any:
    if isinstance(value, str) and value.startswith(("0x", "-0x")):
        return float.fromhex(value)
    if isinstance(value, list):
        return [_decode(entry) for entry in value]
    return value


def _hex_array(values: Any) -> Any:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim == 0:
        return float(array).hex()
    return [_hex_array(entry) for entry in array]


def _exp(vector: np.ndarray) -> np.ndarray:
    theta2 = float(vector @ vector)
    cross = np.array(((0.0, -vector[2], vector[1]), (vector[2], 0.0, -vector[0]), (-vector[1], vector[0], 0.0)))
    if theta2 < 1.0e-16:
        a = 1.0 - theta2 / 6.0 + theta2**2 / 120.0
        b = 0.5 - theta2 / 24.0 + theta2**2 / 720.0
    else:
        theta = math.sqrt(theta2)
        a = math.sin(theta) / theta
        b = (1.0 - math.cos(theta)) / theta2
    return np.eye(3) + a * cross + b * cross @ cross


def _log(rotation: np.ndarray) -> np.ndarray:
    cosine = float(np.clip(0.5 * (np.trace(rotation) - 1.0), -1.0, 1.0))
    angle = math.acos(cosine)
    axial = 0.5 * np.array((rotation[2, 1] - rotation[1, 2], rotation[0, 2] - rotation[2, 0], rotation[1, 0] - rotation[0, 1]))
    if angle < 1.0e-8:
        return (1.0 + angle**2 / 6.0 + 7.0 * angle**4 / 360.0) * axial
    if angle >= 0.9 * math.pi:
        raise ValueError("proof leaves admitted principal-log chart")
    return angle / math.sin(angle) * axial


def _context(record: dict[str, Any]) -> dict[str, Any]:
    decoded = {key: _decode(value) for key, value in record.items() if key != "content_sha256"}
    for key in ("positions", "vertex_rotations", "local_rotations", "local_moments", "section", "residual", "tangent"):
        decoded[key] = np.asarray(decoded[key], dtype=np.float64)
    shapes = {
        "positions": (3, 3),
        "vertex_rotations": (3, 3, 3),
        "local_rotations": (2, 3, 3),
        "local_moments": (2, 2, 3),
        "section": (6, 6),
        "residual": (18,),
        "tangent": (18, 18),
    }
    for key, shape in shapes.items():
        if decoded[key].shape != shape or not np.all(np.isfinite(decoded[key])):
            raise ValueError(f"finite proof {key} must have finite shape {shape}")
    decoded["cell_length"] = float(decoded["cell_length"])
    decoded["energy"] = float(decoded["energy"])
    if not math.isfinite(decoded["cell_length"]) or not math.isfinite(decoded["energy"]):
        raise ValueError("finite proof scalar is nonfinite")
    decoded["d_inverse"] = np.linalg.inv(decoded["section"][3:, 3:])
    return decoded


def _registered_displacements() -> dict[str, np.ndarray]:
    """Independently reconstruct the six frozen finite-case inputs.

    These literals intentionally do not inspect the producer.  The rigid
    translation follows directly from the registered common spatial rotation
    and translation, while every other row is the registered nodal input.
    """

    reference = np.zeros((3, 6))
    rigid = np.zeros((3, 6))
    rigid[:, 3:] = (0.37, -0.21, 0.19)
    common_rotation = _exp(rigid[0, 3:])
    rigid[:, :3] = (
        REFERENCE_COORDINATES @ common_rotation.T
        + np.array((0.8, -0.4, 0.6))
        - REFERENCE_COORDINATES
    )
    return {
        "REFERENCE": reference,
        "RIGID_COMMON": rigid,
        "AXIAL_SHEAR": np.array(
            (
                (0.000, 0.000, 0.000, 0.02, -0.01, 0.015),
                (0.012, 0.026, -0.013, -0.01, 0.025, -0.035),
                (0.031, 0.081, -0.029, 0.015, -0.02, 0.045),
            )
        ),
        "BEND_TWIST": np.array(
            (
                (0.000, 0.000, 0.000, 0.05, -0.04, 0.03),
                (-0.007, 0.061, 0.028, -0.16, 0.12, -0.21),
                (-0.022, 0.184, 0.091, 0.24, -0.19, 0.29),
            )
        ),
        "NONCOMMUTING": np.array(
            (
                (0.000, 0.000, 0.000, 0.20, -0.14, 0.10),
                (-0.019, 0.086, 0.044, 0.42, 0.24, -0.18),
                (0.028, 0.203, -0.129, -0.22, 0.38, 0.31),
            )
        ),
    }


def _registered_context(
    record: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, bool], dict[str, float], str]:
    """Bind a record to the independently registered geometry and loading.

    Producer-supplied geometry, nodal rotations, section, and cell length are
    compared with the registry but are never used to evaluate the source
    potential.  Local rotations and moments remain proof outputs whose
    stationarity is checked independently.
    """

    if set(record) != RECORD_KEYS:
        raise ValueError("finite proof record field set mismatch")
    supplied = _context(record)
    case_id = record["case_id"]
    reversed_case = case_id.endswith("_REVERSED")
    base_case_id = case_id.removesuffix("_REVERSED")
    try:
        nodal = np.array(_registered_displacements()[base_case_id], copy=True)
    except KeyError as error:
        raise ValueError(f"unregistered finite case {case_id}") from error
    coordinates = np.array(REFERENCE_COORDINATES, copy=True)
    frame = np.eye(3)
    section = np.array(REFERENCE_SECTION, copy=True)
    if reversed_case:
        if base_case_id != "NONCOMMUTING":
            raise ValueError(f"unregistered reversed finite case {case_id}")
        nodal = nodal[::-1]
        coordinates = coordinates[::-1]
        frame = REVERSED_REFERENCE_FRAME
        section = REVERSAL_STRAIN_MAP @ section @ REVERSAL_STRAIN_MAP
    positions = coordinates + nodal[:, :3]
    vertex_rotations = np.asarray([_exp(row[3:]) @ frame for row in nodal])
    metrics = {
        "cell_length_absolute": abs(supplied["cell_length"] - 0.5),
        "positions_inf": float(np.linalg.norm(supplied["positions"] - positions, ord=np.inf)),
        "section_inf": float(np.linalg.norm(supplied["section"] - section, ord=np.inf)),
        "vertex_rotations_inf": float(np.max(np.abs(supplied["vertex_rotations"] - vertex_rotations))),
    }
    predicates = {
        "registered_cell_length": metrics["cell_length_absolute"] == 0.0,
        "registered_positions": metrics["positions_inf"] <= 2.0e-15,
        "registered_section": metrics["section_inf"] == 0.0,
        "registered_vertex_rotations": metrics["vertex_rotations_inf"] <= 2.0e-15,
    }
    supplied["cell_length"] = 0.5
    supplied["positions"] = positions
    supplied["section"] = section
    supplied["vertex_rotations"] = vertex_rotations
    supplied["d_inverse"] = np.linalg.inv(section[3:, 3:])
    identity = {
        "case_id": case_id,
        "cell_length": float(0.5).hex(),
        "positions": _hex_array(positions),
        "section": _hex_array(section),
        "vertex_rotations": _hex_array(vertex_rotations),
    }
    identity_sha256 = hashlib.sha256(_canonical_bytes(identity)).hexdigest().upper()
    return supplied, predicates, metrics, identity_sha256


def _potential(context: dict[str, Any], increment: np.ndarray) -> float:
    positions = np.array(context["positions"], copy=True)
    vertices = np.array(context["vertex_rotations"], copy=True)
    local_rotations = np.array(context["local_rotations"], copy=True)
    moments = np.array(context["local_moments"], copy=True)
    for node in range(3):
        positions[node] += increment[node * 6 : node * 6 + 3]
        vertices[node] = _exp(increment[node * 6 + 3 : node * 6 + 6]) @ vertices[node]
    for cell in range(2):
        start = 18 + cell * 9
        local_rotations[cell] = _exp(increment[start : start + 3]) @ local_rotations[cell]
        moments[cell, 0] += increment[start + 3 : start + 6]
        moments[cell, 1] += increment[start + 6 : start + 9]
    section = context["section"]
    a = section[:3, :3]
    b = section[:3, 3:]
    d_inverse = context["d_inverse"]
    length = context["cell_length"]
    total = 0.0
    for cell, (left, right) in enumerate(CELLS):
        qe = local_rotations[cell]
        gamma = qe.T @ ((positions[right] - positions[left]) / length) - np.array((1.0, 0.0, 0.0))
        total += 0.5 * length * float(gamma @ a @ gamma)
        complementary = moments[cell] - (b.T @ gamma)[None, :]
        for row in range(2):
            for column in range(2):
                total -= 0.5 * length * MASS[row, column] * float(complementary[row] @ d_inverse @ complementary[column])
        total += float(_log(qe.T @ vertices[right]) @ moments[cell, 1])
        total -= float(_log(qe.T @ vertices[left]) @ moments[cell, 0])
    return total


def _gradient(context: dict[str, Any], steps: np.ndarray) -> np.ndarray:
    dimension = steps.size
    made = np.zeros(dimension)
    for index, step in enumerate(steps):
        direction = np.zeros(dimension)
        direction[index] = step
        made[index] = (
            -_potential(context, 2.0 * direction)
            + 8.0 * _potential(context, direction)
            - 8.0 * _potential(context, -direction)
            + _potential(context, -2.0 * direction)
        ) / (12.0 * step)
    return made


def _hessian(context: dict[str, Any], steps: np.ndarray) -> np.ndarray:
    dimension = steps.size
    made = np.zeros((dimension, dimension))
    origin = np.zeros(dimension)
    centre = _potential(context, origin)
    for row in range(dimension):
        dr = np.zeros(dimension)
        dr[row] = steps[row]
        made[row, row] = (
            -_potential(context, 2.0 * dr)
            + 16.0 * _potential(context, dr)
            - 30.0 * centre
            + 16.0 * _potential(context, -dr)
            - _potential(context, -2.0 * dr)
        ) / (12.0 * steps[row] ** 2)
        for column in range(row):
            dc = np.zeros(dimension)
            dc[column] = steps[column]
            value = (
                _potential(context, dr + dc)
                - _potential(context, dr - dc)
                - _potential(context, -dr + dc)
                + _potential(context, -dr - dc)
            ) / (4.0 * steps[row] * steps[column])
            made[row, column] = made[column, row] = value
    return made


def _relative(left: Any, right: Any) -> float:
    a = np.asarray(left, dtype=np.float64)
    b = np.asarray(right, dtype=np.float64)
    return float(np.linalg.norm(a - b) / max(1.0, float(np.linalg.norm(b))))


def _relative_max(left: Any, right: Any) -> float:
    a = np.asarray(left, dtype=np.float64)
    b = np.asarray(right, dtype=np.float64)
    return float(np.max(np.abs(a - b)) / max(1.0, float(np.max(np.abs(b)))))


def _metric(value: float) -> str:
    return f"{value:.12E}"


def _entry_hash_ok(record: dict[str, Any]) -> bool:
    stored = record.get("content_sha256")
    content = {key: value for key, value in record.items() if key != "content_sha256"}
    return isinstance(stored, str) and _hashed(content) == stored


def _coverage_case_registry() -> dict[str, dict[str, Any]]:
    stations = np.asarray((0.0, 0.5, 1.0))
    amplitude = 2.0e-4
    cases: dict[str, dict[str, Any]] = {}

    def register(case_id: str, component: str, values: np.ndarray) -> None:
        cases[case_id] = {
            "axis": np.array((1.0, 0.0, 0.0)),
            "component": component,
            "nodal": values,
            "orientation": np.array((0.0, 1.0, 0.0)),
        }

    axial = np.zeros((3, 6))
    axial[:, 0] = amplitude * stations
    register("ISOLATED_AXIAL", "eps_x", axial)
    shear_y = np.zeros((3, 6))
    shear_y[:, 1] = amplitude * stations
    register("ISOLATED_SHEAR_Y", "gamma_xy", shear_y)
    shear_z = np.zeros((3, 6))
    shear_z[:, 2] = amplitude * stations
    register("ISOLATED_SHEAR_Z", "gamma_xz", shear_z)
    torsion = np.zeros((3, 6))
    torsion[:, 3] = amplitude * stations
    register("ISOLATED_TORSION", "kappa_x", torsion)
    bend_y = np.zeros((3, 6))
    bend_y[:, 2] = -0.5 * amplitude * stations**2
    bend_y[:, 4] = amplitude * stations
    register("ISOLATED_BENDING_Y", "kappa_y", bend_y)
    bend_z = np.zeros((3, 6))
    bend_z[:, 1] = 0.5 * amplitude * stations**2
    bend_z[:, 5] = amplitude * stations
    register("ISOLATED_BENDING_Z", "kappa_z", bend_z)

    orientation_nodal = np.array(
        (
            (0.000, 0.000, 0.000, 0.08, -0.05, 0.03),
            (0.004, 0.011, -0.008, -0.04, 0.09, -0.07),
            (0.013, 0.027, 0.016, 0.11, 0.04, -0.10),
        )
    )
    for case_id, axis, orientation in (
        ("ORIENTATION_ROLLED_X", (1.0, 0.0, 0.0), (0.0, 1.0, 1.0)),
        ("ORIENTATION_SKEW_A", (1.0, 2.0, 3.0), (-2.0, 1.0, 0.4)),
        ("ORIENTATION_SKEW_B", (-2.0, 1.0, 4.0), (0.3, 1.0, -0.1)),
    ):
        made_axis = np.asarray(axis, dtype=np.float64)
        made_axis /= np.linalg.norm(made_axis)
        cases[case_id] = {
            "axis": made_axis,
            "component": "GENERAL_COUPLED_RESPONSE",
            "nodal": np.array(orientation_nodal, copy=True),
            "orientation": np.asarray(orientation, dtype=np.float64),
        }
    return cases


def _reference_frame(axis: np.ndarray, orientation: np.ndarray) -> np.ndarray:
    e1 = np.asarray(axis, dtype=np.float64)
    e1 = e1 / np.linalg.norm(e1)
    material_two = np.asarray(orientation, dtype=np.float64)
    projected = material_two - float(material_two @ e1) * e1
    if np.linalg.norm(projected) <= 1.0e-14:
        raise ValueError("registered material orientation is parallel to axis")
    e2 = projected / np.linalg.norm(projected)
    e3 = np.cross(e1, e2)
    e3 /= np.linalg.norm(e3)
    return np.column_stack((e1, e2, e3))


def _source_fields(context: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    strains = []
    resultants = []
    section = context["section"]
    d_inverse = np.linalg.inv(section[3:, 3:])
    for cell, (left, right) in enumerate(CELLS):
        gamma = (
            context["local_rotations"][cell].T
            @ ((context["positions"][right] - context["positions"][left]) / context["cell_length"])
            - np.array((1.0, 0.0, 0.0))
        )
        for endpoint in range(2):
            moment = context["local_moments"][cell, endpoint]
            curvature = d_inverse @ (moment - section[:3, 3:].T @ gamma)
            strain = np.concatenate((gamma, curvature))
            strains.append(strain)
            resultants.append(section @ strain)
    return np.asarray(strains), np.asarray(resultants)


def _material_coverage_check(record: Any, expected: dict[str, Any]) -> tuple[bool, bool, tuple[float, np.ndarray, np.ndarray]]:
    if not isinstance(record, dict) or set(record) != MATERIAL_COVERAGE_KEYS:
        return False, False, (math.nan, np.empty((0, 6)), np.empty((0, 6)))
    try:
        supplied_axis = np.asarray(_decode(record["axis"]), dtype=np.float64)
        supplied_orientation = np.asarray(_decode(record["orientation"]), dtype=np.float64)
        supplied_origin = np.asarray(_decode(record["origin"]), dtype=np.float64)
        supplied_nodal = np.asarray(_decode(record["nodal_input_local"]), dtype=np.float64)
        supplied_section = np.asarray(_decode(record["section"]), dtype=np.float64)
        input_ok = bool(
            _entry_hash_ok(record)
            and record["case_id"] in _coverage_case_registry()
            and record["primary_component"] == expected["component"]
            and float.fromhex(record["cell_length"]) == 0.5
            and float.fromhex(record["total_length"]) == 1.0
            and supplied_axis.shape == (3,)
            and supplied_orientation.shape == (3,)
            and supplied_origin.shape == (3,)
            and supplied_nodal.shape == (3, 6)
            and supplied_section.shape == (6, 6)
            and np.max(np.abs(supplied_axis - expected["axis"])) <= 2.0e-15
            and np.max(np.abs(supplied_orientation - expected["orientation"])) <= 2.0e-15
            and np.max(np.abs(supplied_origin)) == 0.0
            and np.max(np.abs(supplied_nodal - expected["nodal"])) == 0.0
            and np.max(np.abs(supplied_section - REFERENCE_SECTION)) == 0.0
        )
        frame = _reference_frame(expected["axis"], expected["orientation"])
        coordinates = np.asarray(
            [fraction * expected["axis"] for fraction in (0.0, 0.5, 1.0)]
        )
        positions = coordinates + expected["nodal"][:, :3] @ frame.T
        rotations = np.asarray(
            [_exp(frame @ row[3:]) @ frame for row in expected["nodal"]]
        )
        context = {
            "cell_length": 0.5,
            "d_inverse": np.linalg.inv(REFERENCE_SECTION[3:, 3:]),
            "energy": float.fromhex(record["energy"]),
            "local_moments": np.asarray(_decode(record["local_moments"]), dtype=np.float64),
            "local_rotations": np.asarray(_decode(record["local_rotations"]), dtype=np.float64),
            "positions": positions,
            "residual": np.asarray(_decode(record["residual"]), dtype=np.float64),
            "section": np.array(REFERENCE_SECTION, copy=True),
            "tangent": np.asarray(_decode(record["tangent"]), dtype=np.float64),
            "vertex_rotations": rotations,
        }
        shapes_ok = (
            context["local_moments"].shape == (2, 2, 3)
            and context["local_rotations"].shape == (2, 3, 3)
            and context["residual"].shape == (18,)
            and context["tangent"].shape == (18, 18)
            and all(np.all(np.isfinite(context[key])) for key in ("local_moments", "local_rotations", "residual", "tangent"))
        )
        gradient_steps = np.full(36, 2.0e-6)
        gradient_steps[21:27] = 2.0e-5
        gradient_steps[30:36] = 2.0e-5
        gradient = _gradient(context, gradient_steps)
        hessian_steps = np.full(36, 2.0e-4)
        hessian_steps[21:27] = 2.0e-3
        hessian_steps[30:36] = 2.0e-3
        full = _hessian(context, hessian_steps)
        tangent = full[:18, :18] - full[:18, 18:] @ np.linalg.solve(
            full[18:, 18:], full[18:, :18]
        )
        source_strains, source_resultants = _source_fields(context)
        stored_strains = np.asarray(_decode(record["generalized_strain"]), dtype=np.float64)
        stored_resultants = np.asarray(_decode(record["generalized_resultant"]), dtype=np.float64)
        source_energy = _potential(context, np.zeros(36))
        response_ok = bool(
            shapes_ok
            and stored_strains.shape == (4, 6)
            and stored_resultants.shape == (4, 6)
            and abs(source_energy - context["energy"]) / max(1.0, abs(source_energy)) <= 2.0e-11
            and _relative(gradient[:18], context["residual"]) <= 2.0e-6
            and np.linalg.norm(gradient[18:], ord=np.inf) <= 2.0e-7
            and _relative(tangent, context["tangent"]) <= 1.0e-7
            and _relative_max(tangent, context["tangent"]) <= 1.0e-7
            and _relative(context["tangent"], context["tangent"].T) <= 2.0e-12
            and _relative(source_strains, stored_strains) <= 2.0e-11
            and _relative(source_resultants, stored_resultants) <= 2.0e-11
            and abs(float.fromhex(record["residual_inf"]) - np.linalg.norm(context["residual"], ord=np.inf)) <= 2.0e-15
            and float.fromhex(record["local_residual_norm"]) <= 2.0e-10
        )
        return input_ok, response_ok, (context["energy"], stored_strains, stored_resultants)
    except (KeyError, TypeError, ValueError, np.linalg.LinAlgError):
        return False, False, (math.nan, np.empty((0, 6)), np.empty((0, 6)))


def _linear_condensed_tangent(section: np.ndarray) -> np.ndarray:
    """Independently assemble the reference-linear mixed Hessian and Schur complement."""

    total_dofs = 36
    length = 0.5
    full = np.zeros((total_dofs, total_dofs))
    a = section[:3, :3]
    b = section[:3, 3:]
    d_inverse = np.linalg.inv(section[3:, 3:])
    for cell, (left, right) in enumerate(CELLS):
        start = 18 + 9 * cell
        gamma = np.zeros((3, total_dofs))
        for component in range(3):
            gamma[component, right * 6 + component] += 1.0 / length
            gamma[component, left * 6 + component] -= 1.0 / length
        gamma[1, start + 2] -= 1.0
        gamma[2, start + 1] += 1.0
        full += length * gamma.T @ a @ gamma
        endpoints = []
        for moment_start in (start + 3, start + 6):
            endpoint = np.zeros((3, total_dofs))
            endpoint[:, moment_start : moment_start + 3] = np.eye(3)
            endpoint -= b.T @ gamma
            endpoints.append(endpoint)
        for row in range(2):
            for column in range(2):
                full -= length * MASS[row, column] * endpoints[row].T @ d_inverse @ endpoints[column]
        for sign, node, moment_start in ((-1.0, left, start + 3), (1.0, right, start + 6)):
            for component in range(3):
                rotation = np.zeros(total_dofs)
                rotation[node * 6 + 3 + component] = 1.0
                rotation[start + component] = -1.0
                moment = np.zeros(total_dofs)
                moment[moment_start + component] = 1.0
                full += sign * (np.outer(rotation, moment) + np.outer(moment, rotation))
    condensed = full[:18, :18] - full[:18, 18:] @ np.linalg.solve(
        full[18:, 18:], full[18:, :18]
    )
    return 0.5 * (condensed + condensed.T)


def _normalized_operator(matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray, int]:
    diagonal = np.abs(np.diag(matrix))
    floor = max(float(np.max(diagonal)) * np.finfo(np.float64).eps, np.finfo(np.float64).tiny)
    scale = np.sqrt(np.maximum(diagonal, floor))
    normalized = matrix / scale[:, None] / scale[None, :]
    eigenvalues = np.linalg.eigvalsh(0.5 * (normalized + normalized.T))
    threshold = 2.0e-9 * max(1.0, float(np.max(np.abs(eigenvalues))))
    return normalized, eigenvalues, int(np.count_nonzero(np.abs(eigenvalues) > threshold))


def _slender_section(ratio: float) -> np.ndarray:
    height = 1.0 / ratio
    area = height**2
    inertia = height**4 / 12.0
    return np.diag(
        (
            area,
            (5.0 / 6.0) * 0.4 * area,
            (5.0 / 6.0) * 0.4 * area,
            0.4 * height**4 / 6.0,
            inertia,
            inertia,
        )
    )


def _verify_coverage(coverage: Any) -> dict[str, bool]:
    if not isinstance(coverage, dict):
        raise ValueError("finite coverage must be an object")
    required_keys = {
        "classification_authority",
        "content_sha256",
        "geometry_scope",
        "isolated_modes",
        "multi_element_spectrum",
        "physical_reference_orientations",
        "schema",
        "slenderness",
    }
    if set(coverage) != required_keys:
        raise ValueError("finite coverage field set mismatch")

    predicates: dict[str, bool] = {
        "coverage_content_hash": _entry_hash_ok(coverage),
        "coverage_classifies": coverage["classification_authority"] is True,
        "coverage_geometry_scope": coverage["geometry_scope"]
        == "GLOBALLY_STRAIGHT_COLLINEAR_TWO_EQUAL_CELL_ZERO_REFERENCE_JUMP_ONLY",
        "coverage_schema": coverage["schema"]
        == "anysolver.ge-beam3-mixed-finite-coverage-diagnostics-v1",
    }

    registry = _coverage_case_registry()
    modes = coverage["isolated_modes"]
    expected_modes = (
        ("ISOLATED_AXIAL", "eps_x", 0),
        ("ISOLATED_SHEAR_Y", "gamma_xy", 1),
        ("ISOLATED_SHEAR_Z", "gamma_xz", 2),
        ("ISOLATED_TORSION", "kappa_x", 3),
        ("ISOLATED_BENDING_Y", "kappa_y", 4),
        ("ISOLATED_BENDING_Z", "kappa_z", 5),
    )
    predicates["isolated_mode_order"] = isinstance(modes, list) and [
        (record.get("case_id"), record.get("primary_component"))
        for record in modes
        if isinstance(record, dict)
    ] == [(case_id, component) for case_id, component, _index in expected_modes]
    isolated_inputs = predicates["isolated_mode_order"]
    isolated_source = predicates["isolated_mode_order"]
    for record, (case_id, _component, component_index) in zip(
        modes if isinstance(modes, list) else (), expected_modes
    ):
        input_ok, source_ok, (_energy, strains, _resultants) = _material_coverage_check(
            record, registry[case_id]
        )
        isolated_inputs = bool(isolated_inputs and input_ok)
        isolated_source = bool(
            isolated_source
            and source_ok
            and strains.shape == (4, 6)
            and np.max(np.abs(strains[:, component_index])) >= 1.0e-5
        )
    predicates["isolated_modes_registered_inputs"] = isolated_inputs
    predicates["isolated_modes_independent_source"] = isolated_source
    predicates["isolated_modes_physical"] = isolated_inputs and isolated_source

    orientations = coverage["physical_reference_orientations"]
    expected_orientations = ["ORIENTATION_ROLLED_X", "ORIENTATION_SKEW_A", "ORIENTATION_SKEW_B"]
    predicates["orientation_case_order"] = isinstance(orientations, list) and [
        record.get("case_id") for record in orientations if isinstance(record, dict)
    ] == expected_orientations
    orientation_inputs = predicates["orientation_case_order"]
    orientation_source = predicates["orientation_case_order"]
    orientation_fields: list[tuple[float, np.ndarray, np.ndarray]] = []
    for record, case_id in zip(
        orientations if isinstance(orientations, list) else (), expected_orientations
    ):
        input_ok, source_ok, fields = _material_coverage_check(record, registry[case_id])
        orientation_inputs = bool(orientation_inputs and input_ok)
        orientation_source = bool(orientation_source and source_ok)
        orientation_fields.append(fields)
    if len(orientation_fields) == 3:
        first_energy, first_strains, first_resultants = orientation_fields[0]
        orientation_source = bool(
            orientation_source
            and all(
                abs(energy - first_energy) / max(1.0, abs(first_energy)) <= 2.0e-11
                and _relative(strains, first_strains) <= 2.0e-11
                and _relative(resultants, first_resultants) <= 2.0e-11
                for energy, strains, resultants in orientation_fields[1:]
            )
        )
    else:
        orientation_source = False
    predicates["orientation_registered_inputs"] = orientation_inputs
    predicates["orientation_independent_source"] = orientation_source
    predicates["physical_orientation_objectivity"] = orientation_inputs and orientation_source

    slenderness = coverage["slenderness"]
    expected_ratios = (10.0, 100.0, 10_000.0, 1_000_000.0)
    predicates["slenderness_order"] = isinstance(slenderness, list) and [
        float.fromhex(record.get("l_over_h", "nan"))
        for record in slenderness
        if isinstance(record, dict)
    ] == list(expected_ratios)
    slender_inputs = predicates["slenderness_order"]
    slender_source = predicates["slenderness_order"]
    for record, ratio in zip(
        slenderness if isinstance(slenderness, list) else (), expected_ratios
    ):
        try:
            section = _slender_section(ratio)
            supplied_section = np.asarray(_decode(record["section"]), dtype=np.float64)
            supplied_stiffness = np.asarray(_decode(record["stiffness"]), dtype=np.float64)
            supplied_force = np.asarray(_decode(record["unit_tip_force"]), dtype=np.float64)
            supplied_displacement = np.asarray(_decode(record["anchored_displacement"]), dtype=np.float64)
            supplied_eigenvalues = np.asarray(
                _decode(record["anchored_complement_normalized_eigenvalues"]), dtype=np.float64
            )
            expected_force = np.zeros(12)
            expected_force[7] = 1.0
            input_ok = bool(
                isinstance(record, dict)
                and set(record) == SLENDERNESS_KEYS
                and _entry_hash_ok(record)
                and record["case_id"] == f"SLENDERNESS_L_OVER_H_{int(ratio)}"
                and record["anchored_complement"] == "NODE_1_ALL_SIX_COORDINATES_ZERO"
                and np.max(np.abs(np.asarray(_decode(record["axis"])) - np.array((1.0, 0.0, 0.0)))) == 0.0
                and np.max(np.abs(np.asarray(_decode(record["orientation"])) - np.array((0.0, 1.0, 0.0)))) == 0.0
                and np.max(np.abs(np.asarray(_decode(record["origin"])))) == 0.0
                and float.fromhex(record["total_length"]) == 1.0
                and supplied_section.shape == (6, 6)
                and np.max(np.abs(supplied_section - section))
                <= 4.0 * np.finfo(np.float64).eps * max(float(np.max(np.abs(section))), np.finfo(np.float64).tiny)
                and supplied_force.shape == (12,)
                and np.max(np.abs(supplied_force - expected_force)) == 0.0
            )
            expected_stiffness = _linear_condensed_tangent(section)
            expected_anchored = expected_stiffness[6:, 6:]
            expected_displacement = np.linalg.solve(expected_anchored, expected_force)
            normalized_expected, expected_eigenvalues, expected_rank = _normalized_operator(expected_anchored)
            normalized_supplied, _discarded_eigenvalues, _discarded_rank = _normalized_operator(
                supplied_stiffness[6:, 6:]
            )
            response = float.fromhex(record["tip_response"])
            height = 1.0 / ratio
            analytical_reference = 1.0 / (3.0 * height**4 / 12.0) + 1.0 / (
                (5.0 / 6.0) * 0.4 * height**2
            )
            recomputed_error = abs(expected_displacement[7] - analytical_reference) / analytical_reference
            source_ok = bool(
                supplied_stiffness.shape == (18, 18)
                and supplied_displacement.shape == (12,)
                and supplied_eigenvalues.shape == (12,)
                and _relative(normalized_supplied, normalized_expected) <= 2.0e-10
                and _relative(supplied_displacement, expected_displacement) <= 2.0e-11
                and _relative(supplied_eigenvalues, expected_eigenvalues) <= 2.0e-10
                and record["anchored_complement_rank"] == expected_rank == 12
                and record["stiffness_sha256"] == _hashed(_hex_array(supplied_stiffness))
                and abs(response - expected_displacement[7]) / max(1.0, abs(expected_displacement[7])) <= 2.0e-11
                and abs(float.fromhex(record["tip_response_independent_reference"]) - analytical_reference)
                / analytical_reference
                <= 2.0e-15
                and abs(float.fromhex(record["tip_response_relative_error"]) - recomputed_error) <= 2.0e-15
                and recomputed_error <= 0.02
                and abs(float.fromhex(record["energy"])) <= 2.0e-13
                and float.fromhex(record["residual_inf"]) <= 2.0e-11
                and np.all(expected_eigenvalues > 1.0e-10)
            )
            slender_inputs = bool(slender_inputs and input_ok)
            slender_source = bool(slender_source and source_ok)
        except (KeyError, TypeError, ValueError, np.linalg.LinAlgError):
            slender_inputs = False
            slender_source = False
    predicates["slenderness_registered_inputs"] = slender_inputs
    predicates["slenderness_independent_operator"] = slender_source
    predicates["slenderness_rank_and_reference_response"] = slender_inputs and slender_source

    spectrum = coverage["multi_element_spectrum"]
    spectrum_inputs = isinstance(spectrum, dict) and set(spectrum) == SPECTRUM_KEYS
    spectrum_source = spectrum_inputs
    try:
        expected_nodes = np.asarray(
            ((0.0, 0.0, 0.0), (0.5, 0.0, 0.0), (1.0, 0.0, 0.0), (1.5, 0.0, 0.0), (2.0, 0.0, 0.0))
        )
        expected_maps = ((0, 1, 2), (2, 3, 4))
        supplied_nodes = np.asarray(_decode(spectrum["node_coordinates"]), dtype=np.float64)
        supplied_section = np.asarray(_decode(spectrum["section"]), dtype=np.float64)
        supplied_assembled = np.asarray(_decode(spectrum["assembled_stiffness"]), dtype=np.float64)
        supplied_eigenvalues = np.asarray(_decode(spectrum["normalized_eigenvalues"]), dtype=np.float64)
        spectrum_inputs = bool(
            spectrum_inputs
            and _entry_hash_ok(spectrum)
            and spectrum["case_id"] == "TWO_MACRO_COLLINEAR_LINEAR_SPECTRUM"
            and spectrum["dof_count"] == 30
            and spectrum["element_count"] == 2
            and spectrum["element_node_indices"] == [list(item) for item in expected_maps]
            and supplied_nodes.shape == (5, 3)
            and np.max(np.abs(supplied_nodes - expected_nodes)) == 0.0
            and np.max(np.abs(np.asarray(_decode(spectrum["axis"])) - np.array((1.0, 0.0, 0.0)))) == 0.0
            and np.max(np.abs(np.asarray(_decode(spectrum["orientation"])) - np.array((0.0, 1.0, 0.0)))) == 0.0
            and supplied_section.shape == (6, 6)
            and np.max(np.abs(supplied_section - REFERENCE_SECTION)) == 0.0
        )
        element_stiffness = _linear_condensed_tangent(REFERENCE_SECTION)
        expected_assembled = np.zeros((30, 30))
        for node_map in expected_maps:
            indices = np.asarray([6 * node + dof for node in node_map for dof in range(6)])
            expected_assembled[np.ix_(indices, indices)] += element_stiffness
        normalized_expected, expected_eigenvalues, expected_rank = _normalized_operator(expected_assembled)
        normalized_supplied, _discarded_eigenvalues, _discarded_rank = _normalized_operator(supplied_assembled)
        spectrum_source = bool(
            spectrum_source
            and supplied_assembled.shape == (30, 30)
            and supplied_eigenvalues.shape == (30,)
            and _relative(normalized_supplied, normalized_expected) <= 2.0e-10
            and _relative(supplied_eigenvalues, expected_eigenvalues) <= 2.0e-10
            and spectrum["normalized_rank"] == expected_rank == 24
            and spectrum["stiffness_sha256"] == _hashed(_hex_array(supplied_assembled))
            and np.max(np.abs(expected_eigenvalues[:6])) <= 2.0e-12
            and np.all(expected_eigenvalues[6:] > 1.0e-8)
        )
    except (KeyError, TypeError, ValueError, np.linalg.LinAlgError):
        spectrum_inputs = False
        spectrum_source = False
    predicates["multi_element_registered_inputs"] = spectrum_inputs
    predicates["multi_element_independent_operator"] = spectrum_source
    predicates["multi_element_six_rigid_modes"] = spectrum_inputs and spectrum_source
    return predicates


def _verify_record(record: dict[str, Any]) -> dict[str, Any]:
    stored_hash = record.get("content_sha256")
    unhashed = {key: value for key, value in record.items() if key != "content_sha256"}
    hash_ok = hashlib.sha256(_canonical_bytes(unhashed)).hexdigest().upper() == stored_hash
    context, input_predicates, input_metrics, input_sha256 = _registered_context(record)
    zero = np.zeros(36)
    direct_energy = _potential(context, zero)
    gradient_steps = np.full(36, 2.0e-6)
    gradient_steps[21:27] = 2.0e-5
    gradient_steps[30:36] = 2.0e-5
    gradient = _gradient(context, gradient_steps)
    energy_error = abs(direct_energy - context["energy"]) / max(1.0, abs(direct_energy))
    residual_error = _relative(gradient[:18], context["residual"])
    stationarity = float(np.linalg.norm(gradient[18:], ord=np.inf))
    # A 36-coordinate Hessian independently differentiates the complete mixed
    # source potential.  Translational/rotational steps of 2e-4 and moment
    # steps of 2e-3 stay small relative to the registered states while avoiding
    # the cancellation observed with sub-1e-4 binary64 second differences.
    # The full 18x18 Schur complement is compared in normalized Frobenius norm;
    # this is strictly stronger than a few selected directional contractions.
    hessian_steps = np.full(36, 2.0e-4)
    hessian_steps[21:27] = 2.0e-3
    hessian_steps[30:36] = 2.0e-3
    full = _hessian(context, hessian_steps)
    condensed = full[:18, :18] - full[:18, 18:] @ np.linalg.solve(full[18:, 18:], full[18:, :18])
    tangent_error = _relative(condensed, context["tangent"])
    tangent_max_error = _relative_max(condensed, context["tangent"])
    source_tangent_symmetry = _relative(condensed, condensed.T)
    rigid = record["case_id"] == "RIGID_COMMON"
    predicates = {
        "content_hash": hash_ok,
        "energy": energy_error <= 2.0e-11,
        "internal_stationarity": stationarity <= 2.0e-7,
        "residual": residual_error <= 2.0e-6,
        "rigid_energy": (not rigid) or abs(direct_energy) <= 2.0e-11,
        "rigid_force": (not rigid) or np.linalg.norm(context["residual"], ord=np.inf) <= 2.0e-10,
        "tangent_full": tangent_error <= 1.0e-7,
        "tangent_full_max": tangent_max_error <= 1.0e-7,
        "source_tangent_symmetry": source_tangent_symmetry <= 2.0e-12,
        "tangent_symmetry": _relative(context["tangent"], context["tangent"].T) <= 2.0e-12,
        **input_predicates,
    }
    return {
        "case_id": record["case_id"],
        "metrics": {
            "energy_relative": _metric(energy_error),
            "internal_stationarity_inf": _metric(stationarity),
            **{key: _metric(value) for key, value in input_metrics.items()},
            "residual_relative": _metric(residual_error),
            "source_tangent_symmetry_relative": _metric(source_tangent_symmetry),
            "tangent_full_relative": _metric(tangent_error),
            "tangent_full_max_relative": _metric(tangent_max_error),
        },
        "predicates": predicates,
        "registered_input_sha256": input_sha256,
    }


def verify(proof: dict[str, Any]) -> dict[str, Any]:
    if set(proof) != {
        "bindings",
        "candidate_id",
        "case_order",
        "coverage_diagnostics",
        "mutation",
        "records",
        "schema",
    }:
        raise ValueError("finite proof field set mismatch")
    if proof.get("schema") != PROOF_SCHEMA or proof.get("candidate_id") != CANDIDATE_ID:
        raise ValueError("proof schema or candidate identity mismatch")
    expected_bindings = _expected_bindings()
    supplied_bindings = proof.get("bindings")
    binding_checks = {
        key: isinstance(supplied_bindings, dict)
        and set(supplied_bindings) == set(expected_bindings)
        and supplied_bindings.get(key) == value
        and (
            key
            not in {
                "repository_git_blobs_are_canonical_lf_text",
                "repository_working_tree_matches_git_blobs",
            }
            or all(value.values())
        )
        for key, value in expected_bindings.items()
    }
    coverage_checks = _verify_coverage(proof.get("coverage_diagnostics"))
    records = proof.get("records")
    if not isinstance(records, list) or len(records) != 6:
        raise ValueError("proof must contain exactly six ordered records")
    expected = ["REFERENCE", "RIGID_COMMON", "AXIAL_SHEAR", "BEND_TWIST", "NONCOMMUTING", "NONCOMMUTING_REVERSED"]
    if [record.get("case_id") for record in records] != expected or proof.get("case_order") != expected:
        raise ValueError("proof case order mismatch")
    checked = [_verify_record(record) for record in records]
    forward, _forward_inputs, _forward_metrics, _forward_sha256 = _registered_context(records[4])
    reversed_context, _reversed_inputs, _reversed_metrics, _reversed_sha256 = _registered_context(records[5])
    permutation = np.zeros((18, 18))
    for new_node, old_node in enumerate((2, 1, 0)):
        permutation[new_node * 6 : new_node * 6 + 6, old_node * 6 : old_node * 6 + 6] = np.eye(6)
    reversal = {
        "energy": abs(forward["energy"] - reversed_context["energy"]) <= 2.0e-11,
        "residual": _relative(permutation.T @ reversed_context["residual"], forward["residual"]) <= 2.0e-9,
        "tangent": _relative(permutation.T @ reversed_context["tangent"] @ permutation, forward["tangent"]) <= 2.0e-8,
    }
    passed = (
        all(binding_checks.values())
        and all(coverage_checks.values())
        and all(all(case["predicates"].values()) for case in checked)
        and all(reversal.values())
        and proof.get("mutation") is None
    )
    return {
        "authority_bindings": binding_checks,
        "candidate_id": CANDIDATE_ID,
        "cases": checked,
        "checker_import_boundary": {"anysolver":False,"legacy_beam":False,"production_ad":False,"v1_beam":False},
        "coverage": coverage_checks,
        "reversal": reversal,
        "schema": SCHEMA,
        "terminal": "NONCLASSIFYING_FINITE_GATE_PASS" if passed else "NONCLASSIFYING_FINITE_GATE_FINDING",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify(_load(args.proof))
    payload = _canonical_bytes(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(payload)
    return 0 if result["terminal"] == "NONCLASSIFYING_FINITE_GATE_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
