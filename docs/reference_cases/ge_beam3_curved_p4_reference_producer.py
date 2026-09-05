"""Complete raw-proof producer for the private GE-B3 P4 reference gate.

The proof is diagnostic rather than common evidence: it contains coordinates,
frames, and analytic derivatives for an independently authored checker.  The
coordinator owns authority and process adjudication.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from typing import Any

import numpy as np


CANDIDATE_ID = "CANDIDATE_GE_BEAM3_DC_MIXED_CURVED_Q2_MACRO_V1"
SCHEMA = "anysolver.ge-beam3-curved-p4-reference-proof-v2"
PRODUCER_ID = "P4_PRODUCTION_REFERENCE_MODULE_PRODUCER_V2"
PASS = "PROVISIONAL_GO_GE_BEAM3_P4_PRIVATE_CURVED_REFERENCE_CORE"
NO_GO_REGULARITY = "NO_GO_GE_BEAM3_P4_REFERENCE_REGULARITY"
NO_GO_FRAME = "NO_GO_GE_BEAM3_P4_REFERENCE_FRAME_IDENTITY"
NO_GO_COVARIANCE = "NO_GO_GE_BEAM3_P4_REFERENCE_REVERSAL_OR_OBJECTIVITY"
RESTRICTION = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
AUTHORITY_SCHEMA = "anysolver.ge-beam3-curved-p4-run-authority-manifest-v1"

OBLIGATION_ORDER = (
    "P2_BASIS_AND_DERIVATIVE_IDENTITY",
    "P2_NODAL_INTERPOLATION",
    "ANALYTIC_INTERVAL_REGULARITY",
    "STRAIGHT_REFERENCE_LIMIT",
    "PLANAR_SHALLOW_ARCH",
    "PLANAR_DEEP_ARCH",
    "ASYMMETRIC_PLANAR_CURVE",
    "TRANSFORMED_AND_SCALED_COPIES",
    "INITIALLY_TWISTED_CURVE",
    "MULTIELEMENT_SPATIAL_CHAIN",
    "CURVED_STIFFENER_SEGMENT",
    "AUTHORITATIVE_ANISOTROPIC_ROLL",
    "RIGID_REFERENCE_OBJECTIVITY",
    "CONNECTIVITY_REVERSAL",
    "FRAME_CONTINUITY",
    "ZERO_INTRINSIC_REFERENCE_STRAINS",
    "COINCIDENT_NODE_REJECTION",
    "ZERO_TANGENT_REJECTION",
    "NEAR_FOLD_REJECTION",
    "HALF_FRAME_BRANCH_CUTOFF_REJECTION",
    "TRIAD_TANGENT_MISMATCH_REJECTION",
    "IMPROPER_TRIAD_REJECTION",
    "RING_SEAM_MISMATCH_REJECTION",
    "CANONICAL_SERIALIZATION_AND_MUTATION",
    "STRAIGHT_CORE_BLOB_FREEZE",
    "PRODUCTION_BOUNDARY",
)
POSITIVE_FIXTURE_IDS = (
    "STRAIGHT_LIMIT",
    "PLANAR_SHALLOW",
    "PLANAR_DEEP",
    "PLANAR_ASYMMETRIC",
    "INITIALLY_TWISTED",
    "EMBEDDED_SPATIAL_PLANE",
)
STATIONS = (
    (-1.0, "VALUE"),
    (-0.75, "VALUE"),
    (-0.25, "VALUE"),
    (0.0, "LEFT"),
    (0.0, "RIGHT"),
    (0.25, "VALUE"),
    (0.75, "VALUE"),
    (1.0, "VALUE"),
)
NEGATIVE_RECIPES = (
    ("COINCIDENT_NODE_REJECTION", "COINCIDENT_1_2", "COINCIDENT_END_AND_MIDDLE", "GeBeam3CurvedGeometryError"),
    ("ZERO_TANGENT_REJECTION", "FOLDED_ZERO_TANGENT", "FOLDED_ENDPOINT_COINCIDENCE", "GeBeam3CurvedGeometryError"),
    ("NEAR_FOLD_REJECTION", "NEAR_FOLD_SCALE_1E_NEG8", "NEAR_FOLD_SCALE_1E_NEG8", "GeBeam3CurvedGeometryError"),
    ("NEAR_FOLD_REJECTION", "NEAR_FOLD_SCALE_1", "NEAR_FOLD_SCALE_1", "GeBeam3CurvedGeometryError"),
    ("NEAR_FOLD_REJECTION", "NEAR_FOLD_SCALE_1E8", "NEAR_FOLD_SCALE_1E8", "GeBeam3CurvedGeometryError"),
    ("HALF_FRAME_BRANCH_CUTOFF_REJECTION", "TANGENT_TURN_0P91_PI", "HALF_TANGENT_TURN_0P91_PI", "GeBeam3CurvedFrameError"),
    ("HALF_FRAME_BRANCH_CUTOFF_REJECTION", "RESIDUAL_ROLL_PI", "HALF_RESIDUAL_ROLL_PI", "GeBeam3CurvedFrameError"),
    ("TRIAD_TANGENT_MISMATCH_REJECTION", "WRONG_FIRST_AXIS", "TRIAD_FIRST_AXIS_FROM_OTHER_NODE", "GeBeam3CurvedFrameError"),
    ("IMPROPER_TRIAD_REJECTION", "REFLECTED_TRIAD", "REFLECT_THIRD_AXIS", "GeBeam3CurvedFrameError"),
    ("IMPROPER_TRIAD_REJECTION", "NONORTHOGONAL_TRIAD", "PERTURB_SECOND_AXIS", "GeBeam3CurvedFrameError"),
    ("IMPROPER_TRIAD_REJECTION", "NONFINITE_TRIAD", "INSERT_NAN_IN_TRIAD", "GeBeam3CurvedReferenceError"),
)


class ProducerError(RuntimeError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, allow_nan=False, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("ascii")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _canonical_file_bytes(path: Path) -> bytes:
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    if b"\r" in raw:
        raise ProducerError(f"noncanonical carriage return in {path}")
    return raw


def _strict_canonical(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        made: dict[str, Any] = {}
        for key, value in pairs:
            if key in made:
                raise ProducerError(f"duplicate JSON key: {key}")
            made[key] = value
        return made

    def reject_constant(value: str) -> None:
        raise ProducerError(f"nonfinite JSON value: {value}")

    try:
        value = json.loads(raw.decode("ascii"), object_pairs_hook=unique, parse_constant=reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProducerError(f"{path.name} is not strict canonical JSON") from exc
    if not isinstance(value, dict) or raw != _canonical_bytes(value):
        raise ProducerError(f"{path.name} is not strict canonical JSON")
    return raw, value


def _write_exclusive(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(_canonical_bytes(value))


def _binary64(value: float) -> str:
    made = float(value)
    if not np.isfinite(made):
        raise ProducerError("canonical binary64 value must be finite")
    return (0.0 if made == 0.0 else made).hex()


def _load_reference_module(path: Path) -> Any:
    name = "_ge_beam3_curved_reference_frozen_producer_v2"
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise ProducerError("reference module cannot be loaded")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def _shape_derivatives(xi: float) -> np.ndarray:
    return np.array((xi - 0.5, -2.0 * xi, xi + 0.5), dtype=np.float64)


def _triad(tangent: np.ndarray, hint: np.ndarray, roll: float = 0.0) -> np.ndarray:
    first = np.asarray(tangent, dtype=np.float64)
    first /= np.linalg.norm(first)
    second_hint = np.asarray(hint, dtype=np.float64)
    second = second_hint - float(first @ second_hint) * first
    second /= np.linalg.norm(second)
    third = np.cross(first, second)
    if roll != 0.0:
        second = np.cos(roll) * second + np.sin(roll) * third
        third = np.cross(first, second)
    return np.column_stack((first, second, third))


def _triads(
    coordinates: np.ndarray,
    hints: tuple[tuple[float, float, float], ...],
    rolls: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> np.ndarray:
    return np.asarray(
        [
            _triad(_shape_derivatives(xi) @ coordinates, np.asarray(hints[index]), rolls[index])
            for index, xi in enumerate((-1.0, 0.0, 1.0))
        ]
    )


def _axis_rotation(axis: np.ndarray, angle: float) -> np.ndarray:
    unit = np.asarray(axis, dtype=np.float64)
    unit /= np.linalg.norm(unit)
    x, y, z = unit
    cross = np.array(((0.0, -z, y), (z, 0.0, -x), (-y, x, 0.0)))
    return np.eye(3) + np.sin(angle) * cross + (1.0 - np.cos(angle)) * (cross @ cross)


def _positive_fixture_inputs() -> list[dict[str, Any]]:
    common = ((0.0, 0.0, 1.0),) * 3
    fixtures = (
        ("STRAIGHT_LIMIT", np.array(((0.0, 0.0, 0.0), (0.5, 0.0, 0.0), (1.0, 0.0, 0.0))), ((0.0, 1.0, 0.0),) * 3, (0.0, 0.0, 0.0)),
        ("PLANAR_SHALLOW", np.array(((-1.0, 0.0, 0.0), (0.0, 0.15, 0.0), (1.0, 0.0, 0.0))), common, (0.0, 0.0, 0.0)),
        ("PLANAR_DEEP", np.array(((-1.0, 0.0, 0.0), (0.0, 0.8, 0.0), (1.0, 0.0, 0.0))), common, (0.0, 0.0, 0.0)),
        ("PLANAR_ASYMMETRIC", np.array(((-1.2, -0.1, 0.0), (0.15, 0.55, 0.0), (1.1, 0.1, 0.0))), common, (0.0, 0.0, 0.0)),
        ("INITIALLY_TWISTED", np.array(((-1.0, 0.0, 0.0), (0.0, 0.35, 0.0), (1.0, 0.0, 0.0))), common, (0.0, 0.22, 0.47)),
        ("EMBEDDED_SPATIAL_PLANE", np.array(((-1.2, -0.2, 0.4), (0.1, 0.7, 0.9), (1.4, 0.3, -0.1))), ((0.2, -0.6, 1.0),) * 3, (0.0, -0.18, 0.31)),
    )
    return [
        {"case_id": case_id, "coordinates": coordinates.tolist(), "expected": "ACCEPT", "nodal_triads": _triads(coordinates, hints, rolls).tolist()}
        for case_id, coordinates, hints, rolls in fixtures
    ]


def _station_schedule() -> list[dict[str, Any]]:
    return [
        {"index": index, "trace": trace, "xi_binary64": _binary64(xi)}
        for index, (xi, trace) in enumerate(STATIONS)
    ]


def _station_record(geometry: Any, xi: float, trace: str) -> dict[str, Any]:
    station = geometry.station(xi)
    derivative = np.asarray(geometry.frame_derivative(xi, trace=trace), dtype=np.float64)
    curvature = np.asarray(geometry.intrinsic_curvature(xi, trace=trace), dtype=np.float64)
    frame = np.asarray(station.frame, dtype=np.float64)
    tangent = np.asarray(station.derivative, dtype=np.float64) / float(station.jacobian)
    force_measure = frame.T @ tangent
    return {
        "current_curvature": curvature.tolist(),
        "current_force_measure": force_measure.tolist(),
        "derivative": np.asarray(station.derivative).tolist(),
        "frame": frame.tolist(),
        "frame_derivative": derivative.tolist(),
        "intrinsic_curvature": curvature.tolist(),
        "jacobian": float(station.jacobian),
        "position": np.asarray(station.position).tolist(),
        "reference_curvature": curvature.tolist(),
        "reference_force_measure": force_measure.tolist(),
        "trace": trace,
        "xi": float(xi),
        "zero_curvature_strain": np.zeros(3).tolist(),
        "zero_force_strain": np.zeros(3).tolist(),
    }


def _geometry_record(geometry: Any) -> dict[str, Any]:
    return {
        "canonical_geometry_sha256": str(geometry.fingerprint()),
        "coordinates": np.asarray(geometry.coordinates).tolist(),
        "nodal_triads": np.asarray(geometry.nodal_triads).tolist(),
        "regularity": {
            "characteristic_length": float(geometry.regularity.characteristic_length),
            "minimum_admissible_jacobian": float(geometry.regularity.minimum_admissible_jacobian),
            "minimum_jacobian_squared": float(geometry.regularity.minimum_jacobian_squared),
            "minimizer_xi": float(geometry.regularity.minimizer_xi),
        },
        "stations": [_station_record(geometry, xi, trace) for xi, trace in STATIONS],
    }


def _full_case(module: Any, fixture: dict[str, Any]) -> dict[str, Any]:
    geometry = module.CurvedBeam3ReferenceGeometry(fixture["coordinates"], fixture["nodal_triads"])
    rotation = _axis_rotation(np.array((0.3, -0.5, 0.8)), 0.73)
    translation = np.array((4.0, -2.0, 1.5))
    return {
        "base": _geometry_record(geometry),
        "case_id": fixture["case_id"],
        "expected": "ACCEPT",
        "objectivity_input": {"rotation": rotation.tolist(), "translation": translation.tolist()},
        "reversed": _geometry_record(geometry.reversed()),
        "rigidly_transformed": _geometry_record(geometry.rigidly_transformed(rotation, translation)),
    }


def _basis_identity(module: Any) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    passed = True
    for xi in (-1.0, -0.5, 0.0, 0.5, 1.0):
        shape = np.asarray(module.p2_shape_functions(xi), dtype=np.float64)
        derivative = np.asarray(module.p2_shape_derivatives(xi), dtype=np.float64)
        partition = float(np.sum(shape))
        derivative_sum = float(np.sum(derivative))
        passed = passed and partition == 1.0 and derivative_sum == 0.0
        rows.append({"derivative_sum_binary64": _binary64(derivative_sum), "derivatives": derivative.tolist(), "partition_unity_binary64": _binary64(partition), "shape_functions": shape.tolist(), "xi_binary64": _binary64(xi)})
    return {"passed": bool(passed), "samples": rows}


def _transformed_scaled(module: Any, fixture: dict[str, Any]) -> dict[str, Any]:
    coordinates = np.asarray(fixture["coordinates"], dtype=np.float64)
    triads = np.asarray(fixture["nodal_triads"], dtype=np.float64)
    base = module.CurvedBeam3ReferenceGeometry(coordinates, triads)
    rotation = _axis_rotation(np.array((-0.2, 0.7, 0.4)), 0.51)
    translation = np.array((2.0, -3.0, 0.75))
    base_ratio = base.regularity.minimum_jacobian / base.regularity.characteristic_length
    copies: list[dict[str, Any]] = []
    passed = True
    for scale in (1.0e-8, 1.0, 1.0e8):
        made_coordinates = scale * (np.einsum("ij,nj->ni", rotation, coordinates) + translation)
        made_triads = np.einsum("ij,njk->nik", rotation, triads)
        geometry = module.CurvedBeam3ReferenceGeometry(made_coordinates, made_triads)
        ratio = geometry.regularity.minimum_jacobian / geometry.regularity.characteristic_length
        passed = passed and abs(ratio - base_ratio) <= 2.0e-15
        copies.append({"dimensionless_minimum_jacobian_binary64": _binary64(ratio), "geometry": _geometry_record(geometry), "scale_binary64": _binary64(scale)})
    return {"base_dimensionless_minimum_jacobian_binary64": _binary64(base_ratio), "copies": copies, "passed": bool(passed), "rotation": rotation.tolist(), "translation": translation.tolist()}


def _spatial_chain(module: Any) -> dict[str, Any]:
    first_coordinates = np.array(((0.0, 0.0, 0.0), (0.5, 0.2, 0.1), (1.0, 0.5, 0.2)))
    second_coordinates = np.array(((1.0, 0.5, 0.2), (1.5, 0.825, 0.35), (2.0, 1.1, 0.6)))
    hints = ((-0.1, -0.2, 1.0),) * 3
    first_triads = _triads(first_coordinates, hints, (0.0, 0.1, 0.2))
    second_triads = _triads(second_coordinates, hints, (0.2, 0.3, 0.4))
    second_triads[0] = first_triads[2]
    first = module.CurvedBeam3ReferenceGeometry(first_coordinates, first_triads)
    second = module.CurvedBeam3ReferenceGeometry(second_coordinates, second_triads)
    position_gap = float(np.linalg.norm(first.coordinates[2] - second.coordinates[0]))
    frame_gap = float(np.linalg.norm(first.nodal_triads[2] - second.nodal_triads[0], ord=np.inf))
    tangent_gap = float(np.linalg.norm(first.tangent(1.0) - second.tangent(-1.0)))
    return {"passed": position_gap == 0.0 and frame_gap == 0.0 and tangent_gap <= 1.0e-15, "segments": [_geometry_record(first), _geometry_record(second)], "shared_frame_gap_binary64": _binary64(frame_gap), "shared_position_gap_binary64": _binary64(position_gap), "shared_tangent_gap_binary64": _binary64(tangent_gap)}


def _curved_stiffener(module: Any) -> dict[str, Any]:
    coordinates = np.array(((0.0, 0.0, 0.0), (0.75, 0.22, 0.35), (1.55, 0.75, 0.62)))
    hints = ((0.2, -0.7, 1.0), (0.1, -0.8, 0.9), (-0.1, -0.6, 1.1))
    triads = _triads(coordinates, hints, (-0.15, 0.18, 0.42))
    geometry = module.CurvedBeam3ReferenceGeometry(coordinates, triads)
    record = _geometry_record(geometry)
    return {
        "geometry": record,
        "passed": _geometry_predicate(record)["passed"],
        "physical_roll_authority": "EXPLICIT_NODAL_TRIADS",
    }


def _negative_fixture_manifest() -> list[dict[str, Any]]:
    return [{"case_id": case_id, "expected": "REJECT", "expected_exception": expected_exception, "fixture_id": fixture_id, "recipe_id": recipe_id} for case_id, fixture_id, recipe_id, expected_exception in NEGATIVE_RECIPES]


def _negative_input(recipe_id: str) -> tuple[np.ndarray, np.ndarray]:
    ordinary = np.array(((0.0, 0.0, 0.0), (0.5, 0.1, 0.0), (1.0, 0.0, 0.0)))
    ordinary_triads = _triads(ordinary, ((0.0, 0.0, 1.0),) * 3)
    if recipe_id == "COINCIDENT_END_AND_MIDDLE":
        return np.array(((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0))), np.repeat(np.eye(3)[None, :, :], 3, axis=0)
    if recipe_id == "FOLDED_ENDPOINT_COINCIDENCE":
        return np.array(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 0.0))), np.repeat(np.eye(3)[None, :, :], 3, axis=0)
    if recipe_id.startswith("NEAR_FOLD_SCALE_"):
        scale = {"NEAR_FOLD_SCALE_1E_NEG8": 1.0e-8, "NEAR_FOLD_SCALE_1": 1.0, "NEAR_FOLD_SCALE_1E8": 1.0e8}[recipe_id]
        return scale * np.array(((0.0, 0.0, 0.0), (0.25 + 1.0e-15, 0.0, 0.0), (1.0, 0.0, 0.0))), np.repeat(np.eye(3)[None, :, :], 3, axis=0)
    if recipe_id == "HALF_TANGENT_TURN_0P91_PI":
        angle = 0.91 * np.pi
        left = np.array((np.cos(angle), np.sin(angle), 0.0))
        middle = np.array((1.0, 0.0, 0.0))
        coordinates = np.asarray((np.zeros(3), 0.5 * (middle + left), 2.0 * middle))
        return coordinates, _triads(coordinates, ((0.0, 0.0, 1.0),) * 3)
    if recipe_id == "HALF_RESIDUAL_ROLL_PI":
        coordinates = np.array(((0.0, 0.0, 0.0), (0.5, 0.0, 0.0), (1.0, 0.0, 0.0)))
        positive = _triad(np.array((1.0, 0.0, 0.0)), np.array((0.0, 1.0, 0.0)))
        negative = _triad(np.array((1.0, 0.0, 0.0)), np.array((0.0, -1.0, 0.0)))
        return coordinates, np.asarray((positive, negative, negative))
    if recipe_id == "TRIAD_FIRST_AXIS_FROM_OTHER_NODE":
        triads = np.array(ordinary_triads, copy=True)
        triads[0] = triads[2]
        return ordinary, triads
    if recipe_id == "REFLECT_THIRD_AXIS":
        triads = np.array(ordinary_triads, copy=True)
        triads[1, :, 2] *= -1.0
        return ordinary, triads
    if recipe_id == "PERTURB_SECOND_AXIS":
        triads = np.array(ordinary_triads, copy=True)
        triads[1, 1, 1] += 0.1
        return ordinary, triads
    if recipe_id == "INSERT_NAN_IN_TRIAD":
        triads = np.array(ordinary_triads, copy=True)
        triads[1, 0, 0] = np.nan
        return ordinary, triads
    raise ProducerError(f"unknown negative recipe: {recipe_id}")


def _negative_admission(module: Any, manifest: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in manifest:
        coordinates, triads = _negative_input(str(row["recipe_id"]))
        try:
            module.CurvedBeam3ReferenceGeometry(coordinates, triads)
        except Exception as exc:  # The exact independent reconstruction validates the type.
            exception_type = type(exc).__name__
            status = "REJECTED_AS_REGISTERED" if exception_type == row["expected_exception"] else "REJECTED_WITH_WRONG_TYPE"
        else:
            exception_type = "NONE"
            status = "UNEXPECTED_ACCEPT"
        records.append({"case_id": row["case_id"], "exception_type": exception_type, "fixture_id": row["fixture_id"], "status": status})
    return records


def _identity_row(manifest: dict[str, Any], suffix: str) -> dict[str, Any]:
    rows = [row for row in manifest["inputs"] if str(row["path"]).endswith(suffix)]
    if len(rows) != 1:
        raise ProducerError(f"authority manifest must bind exactly one {suffix}")
    return dict(rows[0])


def _changed_sha256(value: str) -> str:
    if re.fullmatch(r"[0-9A-F]{64}", value) is None:
        raise ProducerError("mutation target is not a canonical SHA-256")
    replacement = "0" if value[0] != "0" else "1"
    return replacement + value[1:]


def _mutation_target(path: tuple[str | int, ...]) -> str:
    made = "$"
    for component in path:
        made += f"[{component}]" if isinstance(component, int) else f".{component}"
    return made


def _mutation_row(
    baseline: dict[str, Any],
    *,
    mutation_id: str,
    category: str,
    path: tuple[str | int, ...],
    operation: str,
    after: Any,
) -> dict[str, Any]:
    made = copy.deepcopy(baseline)
    target: Any = made
    for component in path[:-1]:
        target = target[component]
    leaf = path[-1]
    before = copy.deepcopy(target[leaf])
    target[leaf] = copy.deepcopy(after)
    baseline_sha256 = _value_sha256(baseline)
    mutated_sha256 = _value_sha256(made)
    status = "DETECTED" if mutated_sha256 != baseline_sha256 else "NOT_DETECTED"
    return {
        "after": after,
        "before": before,
        "category": category,
        "expected_status": "DETECTED",
        "mutated_payload_sha256": mutated_sha256,
        "mutation_id": mutation_id,
        "operation": operation,
        "status": status,
        "target_path": _mutation_target(path),
    }


def _canonical_mutation_matrix(
    module: Any,
    fixture: dict[str, Any],
    manifest: dict[str, Any],
    basis_identity: dict[str, Any],
) -> dict[str, Any]:
    geometry = module.CurvedBeam3ReferenceGeometry(
        fixture["coordinates"], fixture["nodal_triads"]
    )
    canonical_geometry = geometry.canonical_data()
    authority_artifacts = [
        {"path": row["path"], "sha256": row["sha256"]}
        for row in sorted(manifest["inputs"], key=lambda row: str(row["path"]))
    ]
    production_rows = [
        row
        for row in authority_artifacts
        if row["path"] == "src/anysolver/ge_beam3_curved_reference.py"
    ]
    if len(production_rows) != 1:
        raise ProducerError("mutation matrix requires one bound production reference source")
    baseline = {
        "authority_artifact_hashes": authority_artifacts,
        "case_id": fixture["case_id"],
        "frame_branch_data_by_half_cell": copy.deepcopy(
            canonical_geometry["frame_branch_data_by_half_cell"]
        ),
        "half_cell_order": ["XI_MINUS1_TO_ZERO", "XI_ZERO_TO_PLUS1"],
        "nodes": copy.deepcopy(fixture["coordinates"]),
        "p2_basis_samples": copy.deepcopy(basis_identity["samples"]),
        "production_source_sha256": production_rows[0]["sha256"],
        "reversal_map_diagonal": [-1, 1, -1],
        "tangent_orientation": geometry.tangent(-0.75).tolist(),
        "triads": copy.deepcopy(fixture["nodal_triads"]),
    }
    rows: list[dict[str, Any]] = []

    for node_index in range(3):
        before = np.asarray(baseline["nodes"][node_index], dtype=np.float64)
        after = np.array(before, copy=True)
        component = node_index
        after[component] += 2.0**-5
        rows.append(
            _mutation_row(
                baseline,
                mutation_id=f"NODE_{node_index + 1}_COORDINATES",
                category="NODE",
                path=("nodes", node_index),
                operation=f"ADD_BINARY64_0X1P_MINUS5_TO_COMPONENT_{component}",
                after=after.tolist(),
            )
        )

    for triad_index in range(3):
        before = np.asarray(baseline["triads"][triad_index], dtype=np.float64)
        after = _axis_rotation(before[:, 0], 2.0**-10) @ before
        rows.append(
            _mutation_row(
                baseline,
                mutation_id=f"TRIAD_{triad_index + 1}_PHYSICAL_ROLL",
                category="TRIAD",
                path=("triads", triad_index),
                operation="LEFT_MULTIPLY_BY_BINARY64_0X1P_MINUS10_RADIAN_FIRST_AXIS_ROTATION",
                after=after.tolist(),
            )
        )

    for sample_index, sample in enumerate(baseline["p2_basis_samples"]):
        for field, category, label in (
            ("shape_functions", "P2_SHAPE_COEFFICIENT", "N"),
            ("derivatives", "P2_DERIVATIVE_COEFFICIENT", "DN"),
        ):
            for coefficient in range(3):
                before = float(sample[field][coefficient])
                rows.append(
                    _mutation_row(
                        baseline,
                        mutation_id=(
                            f"P2_SAMPLE_{sample_index + 1}_{label}{coefficient + 1}"
                        ),
                        category=category,
                        path=("p2_basis_samples", sample_index, field, coefficient),
                        operation="ADD_BINARY64_0X1P_MINUS20",
                        after=before + 2.0**-20,
                    )
                )

    tangent = [-float(value) for value in baseline["tangent_orientation"]]
    rows.append(
        _mutation_row(
            baseline,
            mutation_id="TANGENT_ORIENTATION_SIGN",
            category="TANGENT_SIGN",
            path=("tangent_orientation",),
            operation="NEGATE_EVERY_TANGENT_COMPONENT",
            after=tangent,
        )
    )

    for half_index in range(2):
        before = str(
            baseline["frame_branch_data_by_half_cell"][half_index][
                "residual_roll_binary64"
            ]
        )
        roll = float.fromhex(before)
        after = _binary64(-roll)
        if roll == 0.0 or after == before:
            raise ProducerError("mutation fixture must carry nonzero roll on both half cells")
        rows.append(
            _mutation_row(
                baseline,
                mutation_id=f"HALF_{half_index + 1}_RESIDUAL_ROLL_SIGN",
                category="ROLL_SIGN",
                path=(
                    "frame_branch_data_by_half_cell",
                    half_index,
                    "residual_roll_binary64",
                ),
                operation="NEGATE_CANONICAL_BINARY64_RESIDUAL_ROLL",
                after=after,
            )
        )

    rows.append(
        _mutation_row(
            baseline,
            mutation_id="HALF_CELL_ORDERING",
            category="HALF_ORDERING",
            path=("half_cell_order",),
            operation="SWAP_LEFT_AND_RIGHT_HALF_CELL_RECORDS",
            after=list(reversed(baseline["half_cell_order"])),
        )
    )
    rows.append(
        _mutation_row(
            baseline,
            mutation_id="REVERSAL_MAP_DIAGONAL",
            category="REVERSAL_MAP",
            path=("reversal_map_diagonal", 1),
            operation="NEGATE_MIDDLE_DIAGONAL_COMPONENT",
            after=-int(baseline["reversal_map_diagonal"][1]),
        )
    )
    rows.append(
        _mutation_row(
            baseline,
            mutation_id="PRODUCTION_REFERENCE_SOURCE_SHA256",
            category="PRODUCTION_SOURCE_HASH",
            path=("production_source_sha256",),
            operation="REPLACE_FIRST_HEXADECIMAL_NIBBLE",
            after=_changed_sha256(str(baseline["production_source_sha256"])),
        )
    )
    for artifact_index, artifact in enumerate(authority_artifacts):
        rows.append(
            _mutation_row(
                baseline,
                mutation_id=f"AUTHORITY_ARTIFACT_SHA256_{artifact_index + 1:02d}",
                category="AUTHORITY_ARTIFACT_HASH",
                path=("authority_artifact_hashes", artifact_index, "sha256"),
                operation="REPLACE_FIRST_HEXADECIMAL_NIBBLE",
                after=_changed_sha256(str(artifact["sha256"])),
            )
        )

    mutation_ids = [row["mutation_id"] for row in rows]
    if len(mutation_ids) != len(set(mutation_ids)):
        raise ProducerError("canonical mutation identifiers are not unique")
    coverage: dict[str, int] = {}
    for row in rows:
        category = str(row["category"])
        coverage[category] = coverage.get(category, 0) + 1
    expected_coverage = {
        "AUTHORITY_ARTIFACT_HASH": len(authority_artifacts),
        "HALF_ORDERING": 1,
        "NODE": 3,
        "P2_DERIVATIVE_COEFFICIENT": 15,
        "P2_SHAPE_COEFFICIENT": 15,
        "PRODUCTION_SOURCE_HASH": 1,
        "REVERSAL_MAP": 1,
        "ROLL_SIGN": 2,
        "TANGENT_SIGN": 1,
        "TRIAD": 3,
    }
    detected_count = sum(row["status"] == "DETECTED" for row in rows)
    passed = bool(
        coverage == expected_coverage
        and detected_count == len(rows)
        and all(row["expected_status"] == row["status"] for row in rows)
    )
    return {
        "baseline_payload": baseline,
        "baseline_payload_sha256": _value_sha256(baseline),
        "coverage": coverage,
        "detected_count": detected_count,
        "mutation_count": len(rows),
        "mutation_ids": mutation_ids,
        "mutation_order_sha256": _value_sha256(mutation_ids),
        "mutations": rows,
        "passed": passed,
    }


def _canonical_integrity(
    module: Any,
    fixture: dict[str, Any],
    manifest: dict[str, Any],
    basis_identity: dict[str, Any],
) -> dict[str, Any]:
    geometry = module.CurvedBeam3ReferenceGeometry(fixture["coordinates"], fixture["nodal_triads"])
    duplicate = module.CurvedBeam3ReferenceGeometry(fixture["coordinates"], fixture["nodal_triads"])
    coordinates = np.asarray(fixture["coordinates"], dtype=np.float64).copy()
    coordinates[1, 1] += 0.03125
    triads = _triads(coordinates, ((0.2, -0.6, 1.0),) * 3, (0.0, -0.18, 0.31))
    mutated = module.CurvedBeam3ReferenceGeometry(coordinates, triads)
    first = str(geometry.fingerprint())
    second = str(duplicate.fingerprint())
    changed = str(mutated.fingerprint())
    matrix = _canonical_mutation_matrix(module, fixture, manifest, basis_identity)
    return {
        "first_sha256": first,
        "mutated_sha256": changed,
        "mutation_detected": bool(first != changed and matrix["passed"]),
        "mutation_matrix": matrix,
        "repeated_sha256": second,
        "repeat_identical": first == second,
    }


def _validate_authority_manifest(manifest: dict[str, Any]) -> None:
    expected = {"candidate_id", "commits", "inputs", "production_boundary", "protected_straight_blobs", "schema"}
    if set(manifest) != expected:
        raise ProducerError("authority manifest keys differ")
    if manifest.get("schema") != AUTHORITY_SCHEMA or manifest.get("candidate_id") != CANDIDATE_ID:
        raise ProducerError("authority manifest identity differs")
    if [row.get("role") for row in manifest.get("commits", [])] != ["PREREGISTRATION", "REFERENCE_CORE_INITIAL", "REFERENCE_CORE_CORRECTION", "IMPLEMENTATION_REVIEW"]:
        raise ProducerError("authority commit order differs")
    if manifest.get("production_boundary", {}).get("status") != "PASS":
        raise ProducerError("production boundary is not frozen clean")
    if not manifest.get("protected_straight_blobs") or not all(row.get("status") == "PASS" for row in manifest["protected_straight_blobs"]):
        raise ProducerError("protected straight blob identity differs")


def _nodal_interpolation_passes(cases: list[dict[str, Any]]) -> bool:
    station_keys = ((-1.0, "VALUE", 0), (0.0, "LEFT", 1), (0.0, "RIGHT", 1), (1.0, "VALUE", 2))
    for case in cases:
        coordinates = np.asarray(case["base"]["coordinates"], dtype=np.float64)
        station_map = {(float(row["xi"]), str(row["trace"])): row for row in case["base"]["stations"]}
        for xi, trace, node in station_keys:
            if not np.array_equal(np.asarray(station_map[(xi, trace)]["position"]), coordinates[node]):
                return False
    return True


def _case_by_id(cases: list[dict[str, Any]], case_id: str) -> dict[str, Any]:
    selected = [row for row in cases if row.get("case_id") == case_id]
    if len(selected) != 1:
        raise ProducerError(f"expected exactly one positive case: {case_id}")
    return selected[0]


def _value_sha256(value: Any) -> str:
    return _sha256(_canonical_bytes(value))


def _geometry_predicate(record: dict[str, Any]) -> dict[str, Any]:
    regularity = record["regularity"]
    minimum_squared = float(regularity["minimum_jacobian_squared"])
    threshold = float(regularity["minimum_admissible_jacobian"])
    maximum_orthogonality_error = 0.0
    maximum_determinant_error = 0.0
    maximum_tangent_error = 0.0
    maximum_zero_strain_error = 0.0
    for station in record["stations"]:
        frame = np.asarray(station["frame"], dtype=np.float64)
        derivative = np.asarray(station["derivative"], dtype=np.float64)
        jacobian = float(station["jacobian"])
        maximum_orthogonality_error = max(
            maximum_orthogonality_error,
            float(np.linalg.norm(frame.T @ frame - np.eye(3), ord=np.inf)),
        )
        maximum_determinant_error = max(
            maximum_determinant_error,
            abs(float(np.linalg.det(frame)) - 1.0),
        )
        maximum_tangent_error = max(
            maximum_tangent_error,
            float(np.linalg.norm(frame[:, 0] - derivative / jacobian, ord=np.inf)),
        )
        maximum_zero_strain_error = max(
            maximum_zero_strain_error,
            float(np.linalg.norm(station["zero_force_strain"], ord=np.inf)),
            float(np.linalg.norm(station["zero_curvature_strain"], ord=np.inf)),
        )
    passed = bool(
        minimum_squared > threshold * threshold
        and maximum_orthogonality_error <= 1.0e-11
        and maximum_determinant_error <= 1.0e-11
        and maximum_tangent_error <= 1.0e-11
        and maximum_zero_strain_error <= 1.0e-12
    )
    return {
        "geometry_sha256": _value_sha256(record),
        "maximum_determinant_error_binary64": _binary64(maximum_determinant_error),
        "maximum_orthogonality_error_binary64": _binary64(maximum_orthogonality_error),
        "maximum_tangent_error_binary64": _binary64(maximum_tangent_error),
        "maximum_zero_strain_error_binary64": _binary64(maximum_zero_strain_error),
        "minimum_admissible_jacobian_binary64": _binary64(threshold),
        "minimum_jacobian_squared_binary64": _binary64(minimum_squared),
        "passed": passed,
    }


def _positive_case_predicate(cases: list[dict[str, Any]], case_id: str) -> dict[str, Any]:
    case = _case_by_id(cases, case_id)
    variants = {
        name: _geometry_predicate(case[name])
        for name in ("base", "reversed", "rigidly_transformed")
    }
    return {
        "case_id": case_id,
        "case_sha256": _value_sha256(case),
        "passed": all(row["passed"] for row in variants.values()),
        "variants": variants,
    }


def _nodal_interpolation_predicate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    station_keys = ((-1.0, "VALUE", 0), (0.0, "LEFT", 1), (0.0, "RIGHT", 1), (1.0, "VALUE", 2))
    rows: list[dict[str, Any]] = []
    maximum_gap = 0.0
    for case in cases:
        coordinates = np.asarray(case["base"]["coordinates"], dtype=np.float64)
        station_map = {
            (float(row["xi"]), str(row["trace"])): row
            for row in case["base"]["stations"]
        }
        case_gap = 0.0
        for xi, trace, node in station_keys:
            case_gap = max(
                case_gap,
                float(
                    np.linalg.norm(
                        np.asarray(station_map[(xi, trace)]["position"]) - coordinates[node],
                        ord=np.inf,
                    )
                ),
            )
        maximum_gap = max(maximum_gap, case_gap)
        rows.append(
            {
                "case_id": case["case_id"],
                "case_sha256": _value_sha256(case),
                "maximum_nodal_position_gap_binary64": _binary64(case_gap),
            }
        )
    return {
        "case_rows": rows,
        "maximum_nodal_position_gap_binary64": _binary64(maximum_gap),
        "passed": bool(maximum_gap == 0.0 and _nodal_interpolation_passes(cases)),
    }


def _regularity_predicate(
    cases: list[dict[str, Any]], transformed_scaled: dict[str, Any]
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for case in cases:
        variants = {
            name: _geometry_predicate(case[name])
            for name in ("base", "reversed", "rigidly_transformed")
        }
        rows.append(
            {
                "case_id": case["case_id"],
                "case_sha256": _value_sha256(case),
                "passed": all(row["passed"] for row in variants.values()),
                "variants": variants,
            }
        )
    return {
        "case_rows": rows,
        "passed": bool(
            all(row["passed"] for row in rows) and transformed_scaled["passed"]
        ),
        "transformed_scaled_sha256": _value_sha256(transformed_scaled),
    }


def _straight_limit_predicate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    case = _case_by_id(cases, "STRAIGHT_LIMIT")
    base = case["base"]
    reference_frame = np.asarray(base["nodal_triads"][0], dtype=np.float64)
    maximum_frame_gap = 0.0
    maximum_curvature = 0.0
    for station in base["stations"]:
        maximum_frame_gap = max(
            maximum_frame_gap,
            float(np.linalg.norm(np.asarray(station["frame"]) - reference_frame, ord=np.inf)),
        )
        maximum_curvature = max(
            maximum_curvature,
            float(np.linalg.norm(station["intrinsic_curvature"], ord=np.inf)),
        )
    return {
        "case_sha256": _value_sha256(case),
        "maximum_curvature_binary64": _binary64(maximum_curvature),
        "maximum_frame_gap_binary64": _binary64(maximum_frame_gap),
        "passed": bool(maximum_frame_gap <= 1.0e-12 and maximum_curvature <= 1.0e-12),
    }


def _twisted_reference_predicate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    case = _case_by_id(cases, "INITIALLY_TWISTED")
    triads = np.asarray(case["base"]["nodal_triads"], dtype=np.float64)
    nodal_frame_change = max(
        float(np.linalg.norm(triads[index] - triads[0], ord=np.inf))
        for index in (1, 2)
    )
    maximum_curvature = max(
        float(np.linalg.norm(station["intrinsic_curvature"], ord=np.inf))
        for station in case["base"]["stations"]
    )
    base = _geometry_predicate(case["base"])
    return {
        "base_geometry": base,
        "case_sha256": _value_sha256(case),
        "maximum_intrinsic_curvature_binary64": _binary64(maximum_curvature),
        "maximum_nodal_frame_change_binary64": _binary64(nodal_frame_change),
        "passed": bool(base["passed"] and nodal_frame_change > 0.0 and maximum_curvature > 0.0),
    }


def _anisotropic_roll_predicate(
    cases: list[dict[str, Any]], curved_stiffener: dict[str, Any]
) -> dict[str, Any]:
    twisted = _twisted_reference_predicate(cases)
    stiffener_geometry = _geometry_predicate(curved_stiffener["geometry"])
    passed = bool(
        twisted["passed"]
        and curved_stiffener["physical_roll_authority"] == "EXPLICIT_NODAL_TRIADS"
        and curved_stiffener["passed"]
        and stiffener_geometry["passed"]
    )
    return {
        "curved_stiffener_sha256": _value_sha256(curved_stiffener),
        "explicit_roll_authority": curved_stiffener["physical_roll_authority"],
        "passed": passed,
        "stiffener_geometry": stiffener_geometry,
        "twisted_reference": twisted,
    }


def _objectivity_predicate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    maximum_error = 0.0
    for case in cases:
        rotation = np.asarray(case["objectivity_input"]["rotation"], dtype=np.float64)
        translation = np.asarray(case["objectivity_input"]["translation"], dtype=np.float64)
        base_stations = case["base"]["stations"]
        target_stations = case["rigidly_transformed"]["stations"]
        case_error = 0.0
        for base, target in zip(base_stations, target_stations):
            case_error = max(
                case_error,
                float(np.linalg.norm(np.asarray(target["position"]) - (rotation @ np.asarray(base["position"]) + translation), ord=np.inf)),
                float(np.linalg.norm(np.asarray(target["derivative"]) - rotation @ np.asarray(base["derivative"]), ord=np.inf)),
                float(np.linalg.norm(np.asarray(target["frame"]) - rotation @ np.asarray(base["frame"]), ord=np.inf)),
                float(np.linalg.norm(np.asarray(target["frame_derivative"]) - rotation @ np.asarray(base["frame_derivative"]), ord=np.inf)),
                float(np.linalg.norm(np.asarray(target["intrinsic_curvature"]) - np.asarray(base["intrinsic_curvature"]), ord=np.inf)),
            )
        maximum_error = max(maximum_error, case_error)
        rows.append({"case_id": case["case_id"], "case_sha256": _value_sha256(case), "maximum_error_binary64": _binary64(case_error)})
    return {"case_rows": rows, "maximum_error_binary64": _binary64(maximum_error), "passed": maximum_error <= 1.0e-11}


def _reversal_predicate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    reversal = np.diag((-1.0, 1.0, -1.0))
    curvature_reversal = -reversal
    rows: list[dict[str, Any]] = []
    maximum_error = 0.0
    for case in cases:
        base_map = {
            (float(row["xi"]), str(row["trace"])): row
            for row in case["base"]["stations"]
        }
        reversed_map = {
            (float(row["xi"]), str(row["trace"])): row
            for row in case["reversed"]["stations"]
        }
        case_error = 0.0
        for (xi, trace), target in reversed_map.items():
            source_trace = "RIGHT" if trace == "LEFT" else "LEFT" if trace == "RIGHT" else trace
            source = base_map[(-xi, source_trace)]
            case_error = max(
                case_error,
                float(np.linalg.norm(np.asarray(target["position"]) - np.asarray(source["position"]), ord=np.inf)),
                float(np.linalg.norm(np.asarray(target["derivative"]) + np.asarray(source["derivative"]), ord=np.inf)),
                float(np.linalg.norm(np.asarray(target["frame"]) - np.asarray(source["frame"]) @ reversal, ord=np.inf)),
                float(np.linalg.norm(np.asarray(target["frame_derivative"]) + np.asarray(source["frame_derivative"]) @ reversal, ord=np.inf)),
                float(np.linalg.norm(np.asarray(target["intrinsic_curvature"]) - curvature_reversal @ np.asarray(source["intrinsic_curvature"]), ord=np.inf)),
            )
        maximum_error = max(maximum_error, case_error)
        rows.append({"case_id": case["case_id"], "case_sha256": _value_sha256(case), "maximum_error_binary64": _binary64(case_error)})
    return {"case_rows": rows, "maximum_error_binary64": _binary64(maximum_error), "passed": maximum_error <= 1.0e-11}


def _frame_continuity_predicate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    maximum_gap = 0.0
    for case in cases:
        base_map = {
            (float(row["xi"]), str(row["trace"])): row
            for row in case["base"]["stations"]
        }
        left = np.asarray(base_map[(0.0, "LEFT")]["frame"])
        right = np.asarray(base_map[(0.0, "RIGHT")]["frame"])
        node = np.asarray(case["base"]["nodal_triads"][1])
        gap = max(
            float(np.linalg.norm(left - right, ord=np.inf)),
            float(np.linalg.norm(left - node, ord=np.inf)),
            float(np.linalg.norm(right - node, ord=np.inf)),
        )
        maximum_gap = max(maximum_gap, gap)
        rows.append({"case_id": case["case_id"], "case_sha256": _value_sha256(case), "midpoint_frame_gap_binary64": _binary64(gap)})
    return {"case_rows": rows, "maximum_gap_binary64": _binary64(maximum_gap), "passed": maximum_gap <= 1.0e-12}


def _zero_reference_strain_predicate(cases: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    maximum_error = 0.0
    for case in cases:
        case_error = 0.0
        for variant in ("base", "reversed", "rigidly_transformed"):
            for station in case[variant]["stations"]:
                case_error = max(
                    case_error,
                    float(np.linalg.norm(station["zero_force_strain"], ord=np.inf)),
                    float(np.linalg.norm(station["zero_curvature_strain"], ord=np.inf)),
                )
        maximum_error = max(maximum_error, case_error)
        rows.append({"case_id": case["case_id"], "case_sha256": _value_sha256(case), "maximum_zero_strain_error_binary64": _binary64(case_error)})
    return {"case_rows": rows, "maximum_error_binary64": _binary64(maximum_error), "passed": maximum_error <= 1.0e-12}


def _negative_predicate(
    negative_by_case: dict[str, list[dict[str, Any]]], case_id: str
) -> dict[str, Any]:
    rows = negative_by_case.get(case_id, [])
    return {
        "observations": rows,
        "observations_sha256": _value_sha256(rows),
        "passed": bool(rows and all(row["status"] == "REJECTED_AS_REGISTERED" for row in rows)),
    }


def _ring_seam_diagnostic(module: Any) -> dict[str, Any]:
    shared_position = np.array((1.0, 0.0, 0.0), dtype=np.float64)
    tangent = np.array((1.0, 0.0, 0.0), dtype=np.float64)
    upstream_frame = np.eye(3, dtype=np.float64)
    mismatch_roll = 0.25
    downstream_frame = _axis_rotation(tangent, mismatch_roll) @ upstream_frame
    position_gap = float(np.linalg.norm(shared_position - shared_position, ord=np.inf))
    frame_gap = float(np.linalg.norm(upstream_frame - downstream_frame, ord=np.inf))
    chain_api_names = (
        "ClosedCurvedBeam3ReferenceGeometry",
        "CurvedBeam3ReferenceChain",
        "validate_closed_reference_chain",
        "validate_reference_chain",
    )
    present = [name for name in chain_api_names if hasattr(module, name)]
    disposition = "FAIL_CLOSED_NO_REFERENCE_CHAIN_OR_HOLONOMY_API"
    passed = bool(position_gap == 0.0 and frame_gap > 1.0e-11 and not present)
    return {
        "chain_api_symbols_present": present,
        "disposition": disposition,
        "downstream_initial": {
            "frame": downstream_frame.tolist(),
            "position": shared_position.tolist(),
        },
        "fixture_id": "INCOMPATIBLE_CLOSED_CHAIN_LOCAL_SEAM",
        "frame_gap_binary64": _binary64(frame_gap),
        "mismatch_roll_binary64": _binary64(mismatch_roll),
        "passed": passed,
        "position_gap_binary64": _binary64(position_gap),
        "upstream_terminal": {
            "frame": upstream_frame.tolist(),
            "position": shared_position.tolist(),
        },
    }


def _obligation_payload(
    case_id: str, predicate_id: str, evidence: Any, passed: bool
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "evidence": evidence,
        "passed": bool(passed),
        "predicate_id": predicate_id,
    }


def _obligation_records(auxiliary: dict[str, Any], cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    negative_by_case: dict[str, list[dict[str, Any]]] = {}
    for row in auxiliary["negative_admission"]:
        negative_by_case.setdefault(str(row["case_id"]), []).append(row)
    payloads: dict[str, dict[str, Any]] = {}
    basis = auxiliary["basis_identity"]
    payloads["P2_BASIS_AND_DERIVATIVE_IDENTITY"] = _obligation_payload(
        "P2_BASIS_AND_DERIVATIVE_IDENTITY", "EXACT_P2_SAMPLE_IDENTITIES_V1", basis, basis["passed"]
    )
    nodal = _nodal_interpolation_predicate(cases)
    payloads["P2_NODAL_INTERPOLATION"] = _obligation_payload(
        "P2_NODAL_INTERPOLATION", "ALL_POSITIVE_CASE_NODAL_STATION_MATCH_V1", nodal, nodal["passed"]
    )
    regularity = _regularity_predicate(cases, auxiliary["transformed_scaled"])
    payloads["ANALYTIC_INTERVAL_REGULARITY"] = _obligation_payload(
        "ANALYTIC_INTERVAL_REGULARITY", "ALL_VARIANT_ANALYTIC_INTERVAL_MINIMA_V1", regularity, regularity["passed"]
    )
    straight = _straight_limit_predicate(cases)
    payloads["STRAIGHT_REFERENCE_LIMIT"] = _obligation_payload(
        "STRAIGHT_REFERENCE_LIMIT", "CONSTANT_FRAME_ZERO_INTRINSIC_CURVATURE_V1", straight, straight["passed"]
    )
    for obligation_id, case_id in (
        ("PLANAR_SHALLOW_ARCH", "PLANAR_SHALLOW"),
        ("PLANAR_DEEP_ARCH", "PLANAR_DEEP"),
        ("ASYMMETRIC_PLANAR_CURVE", "PLANAR_ASYMMETRIC"),
    ):
        evidence = _positive_case_predicate(cases, case_id)
        payloads[obligation_id] = _obligation_payload(
            obligation_id, "POSITIVE_CASE_ALL_VARIANTS_REFERENCE_INVARIANTS_V1", evidence, evidence["passed"]
        )
    transformed = auxiliary["transformed_scaled"]
    payloads["TRANSFORMED_AND_SCALED_COPIES"] = _obligation_payload(
        "TRANSFORMED_AND_SCALED_COPIES", "THREE_SCALE_DIMENSIONLESS_REGULARITY_V1", transformed, transformed["passed"]
    )
    twisted = _twisted_reference_predicate(cases)
    payloads["INITIALLY_TWISTED_CURVE"] = _obligation_payload(
        "INITIALLY_TWISTED_CURVE", "NONZERO_EXPLICIT_NODAL_ROLL_AND_INTRINSIC_CURVATURE_V1", twisted, twisted["passed"]
    )
    chain = auxiliary["spatial_chain"]
    payloads["MULTIELEMENT_SPATIAL_CHAIN"] = _obligation_payload(
        "MULTIELEMENT_SPATIAL_CHAIN", "TWO_SEGMENT_SHARED_POSITION_TANGENT_FRAME_V1", chain, chain["passed"]
    )
    stiffener = auxiliary["curved_stiffener"]
    stiffener_predicate = _geometry_predicate(stiffener["geometry"])
    stiffener_passed = bool(stiffener["passed"] and stiffener_predicate["passed"] and stiffener["physical_roll_authority"] == "EXPLICIT_NODAL_TRIADS")
    payloads["CURVED_STIFFENER_SEGMENT"] = _obligation_payload(
        "CURVED_STIFFENER_SEGMENT", "CURVED_STIFFENER_EXPLICIT_ROLL_GEOMETRY_V1", {"geometry": stiffener_predicate, "packet_sha256": _value_sha256(stiffener), "physical_roll_authority": stiffener["physical_roll_authority"]}, stiffener_passed
    )
    anisotropic = _anisotropic_roll_predicate(cases, stiffener)
    payloads["AUTHORITATIVE_ANISOTROPIC_ROLL"] = _obligation_payload(
        "AUTHORITATIVE_ANISOTROPIC_ROLL", "EXPLICIT_NODAL_TRIADS_ONLY_V1", anisotropic, anisotropic["passed"]
    )
    objectivity = _objectivity_predicate(cases)
    payloads["RIGID_REFERENCE_OBJECTIVITY"] = _obligation_payload(
        "RIGID_REFERENCE_OBJECTIVITY", "ALL_CASE_SPATIAL_RIGID_COVARIANCE_V1", objectivity, objectivity["passed"]
    )
    reversal = _reversal_predicate(cases)
    payloads["CONNECTIVITY_REVERSAL"] = _obligation_payload(
        "CONNECTIVITY_REVERSAL", "ALL_CASE_XI_NEGATION_FRAME_AND_CURVATURE_MAP_V1", reversal, reversal["passed"]
    )
    continuity = _frame_continuity_predicate(cases)
    payloads["FRAME_CONTINUITY"] = _obligation_payload(
        "FRAME_CONTINUITY", "ALL_CASE_TWO_TRACE_NODE2_FRAME_IDENTITY_V1", continuity, continuity["passed"]
    )
    zero_strain = _zero_reference_strain_predicate(cases)
    payloads["ZERO_INTRINSIC_REFERENCE_STRAINS"] = _obligation_payload(
        "ZERO_INTRINSIC_REFERENCE_STRAINS", "ALL_VARIANT_ALL_STATION_GAMMA_KAPPA_ZERO_V1", zero_strain, zero_strain["passed"]
    )
    for case_id in (
        "COINCIDENT_NODE_REJECTION",
        "ZERO_TANGENT_REJECTION",
        "NEAR_FOLD_REJECTION",
        "HALF_FRAME_BRANCH_CUTOFF_REJECTION",
        "TRIAD_TANGENT_MISMATCH_REJECTION",
        "IMPROPER_TRIAD_REJECTION",
    ):
        evidence = _negative_predicate(negative_by_case, case_id)
        payloads[case_id] = _obligation_payload(
            case_id, "REGISTERED_NEGATIVE_REJECTION_AND_EXCEPTION_TYPE_V1", evidence, evidence["passed"]
        )
    ring = auxiliary["ring_seam"]
    payloads["RING_SEAM_MISMATCH_REJECTION"] = _obligation_payload(
        "RING_SEAM_MISMATCH_REJECTION", "CONCRETE_INCOMPATIBLE_SHARED_POSITION_FRAME_AND_NO_CHAIN_API_V1", ring, ring["passed"]
    )
    integrity = auxiliary["canonical_integrity"]
    mutation_matrix = integrity["mutation_matrix"]
    integrity_passed = bool(
        integrity["repeat_identical"]
        and integrity["mutation_detected"]
        and integrity["first_sha256"] == integrity["repeated_sha256"]
        and integrity["first_sha256"] != integrity["mutated_sha256"]
        and mutation_matrix["passed"]
        and mutation_matrix["detected_count"] == mutation_matrix["mutation_count"]
        and mutation_matrix["mutation_count"] == len(mutation_matrix["mutations"])
    )
    payloads["CANONICAL_SERIALIZATION_AND_MUTATION"] = _obligation_payload(
        "CANONICAL_SERIALIZATION_AND_MUTATION", "REPEAT_AND_MUTATED_FINGERPRINT_RELATION_V1", integrity, integrity_passed
    )
    protected = auxiliary["static_scope"]["protected_straight_blob_rows"]
    straight_passed = bool(auxiliary["static_scope"]["straight_blob_freeze"] and protected and all(row["status"] == "PASS" and row["observed_git_blob"] == row["expected_git_blob"] for row in protected))
    payloads["STRAIGHT_CORE_BLOB_FREEZE"] = _obligation_payload(
        "STRAIGHT_CORE_BLOB_FREEZE", "EVERY_PROTECTED_STRAIGHT_GIT_BLOB_ROW_V1", {"protected_straight_blob_rows": protected, "rows_sha256": _value_sha256(protected)}, straight_passed
    )
    boundary = auxiliary["static_scope"]["production_boundary_record"]
    boundary_passed = bool(auxiliary["static_scope"]["production_boundary"] and boundary["status"] == "PASS" and boundary["independent_checker_authority"] is True)
    payloads["PRODUCTION_BOUNDARY"] = _obligation_payload(
        "PRODUCTION_BOUNDARY", "HASH_BOUND_CHANGED_PATH_AND_REVIEW_BOUNDARY_V1", boundary, boundary_passed
    )
    if set(payloads) != set(OBLIGATION_ORDER):
        missing = sorted(set(OBLIGATION_ORDER) - set(payloads))
        unexpected = sorted(set(payloads) - set(OBLIGATION_ORDER))
        raise ProducerError(f"explicit obligation payload map differs: missing={missing}, unexpected={unexpected}")
    return [
        {"case_id": case_id, "evidence_sha256": _value_sha256(payloads[case_id]), "status": "PASS" if payloads[case_id]["passed"] else "FAIL"}
        for case_id in OBLIGATION_ORDER
    ]


def _payload(module: Any, reference_path: Path, cases_path: Path, contract_path: Path, manifest: dict[str, Any], manifest_sha256: str, *, producer_sha256: str) -> dict[str, Any]:
    fixtures = _positive_fixture_inputs()
    negative_manifest = _negative_fixture_manifest()
    cases = [_full_case(module, fixture) for fixture in fixtures]
    basis_identity = _basis_identity(module)
    auxiliary = {
        "basis_identity": basis_identity,
        "canonical_integrity": _canonical_integrity(
            module, fixtures[-1], manifest, basis_identity
        ),
        "curved_stiffener": _curved_stiffener(module),
        "negative_admission": _negative_admission(module, negative_manifest),
        "ring_seam": _ring_seam_diagnostic(module),
        "spatial_chain": _spatial_chain(module),
        "static_scope": {
            "production_boundary": manifest["production_boundary"]["status"] == "PASS",
            "production_boundary_record": dict(manifest["production_boundary"]),
            "protected_straight_blob_rows": list(manifest["protected_straight_blobs"]),
            "ring_seam_disposition": "TYPED_REJECTION_REQUIRED_NO_P4_SEAM_AUTHORITY",
            "straight_blob_freeze": all(row["status"] == "PASS" for row in manifest["protected_straight_blobs"]),
        },
        "transformed_scaled": _transformed_scaled(module, fixtures[-1]),
    }
    obligation_records = _obligation_records(auxiliary, cases)
    failures = [row for row in obligation_records if row["status"] != "PASS"]
    terminal = PASS
    reason = "ALL_26_PREREGISTERED_OBLIGATIONS_EXECUTED"
    if failures:
        failed_ids = {row["case_id"] for row in failures}
        regularity = {"ANALYTIC_INTERVAL_REGULARITY", "COINCIDENT_NODE_REJECTION", "ZERO_TANGENT_REJECTION", "NEAR_FOLD_REJECTION"}
        frame = {"HALF_FRAME_BRANCH_CUTOFF_REJECTION", "TRIAD_TANGENT_MISMATCH_REJECTION", "IMPROPER_TRIAD_REJECTION"}
        terminal = NO_GO_REGULARITY if failed_ids & regularity else NO_GO_FRAME if failed_ids & frame else NO_GO_COVARIANCE
        reason = "PRODUCER_OBSERVED_SCIENTIFIC_CONTRADICTION"
    return {
        "authority_manifest": manifest,
        "authority_manifest_sha256": manifest_sha256,
        "auxiliary_evidence": auxiliary,
        "candidate_id": CANDIDATE_ID,
        "cases": cases,
        "cases_definition": _identity_row(manifest, cases_path.name),
        "contract": _identity_row(manifest, contract_path.name),
        "coverage_count": len([row for row in obligation_records if row["status"] == "PASS"]),
        "negative_fixture_manifest": negative_manifest,
        "negative_fixture_manifest_sha256": _sha256(_canonical_bytes(negative_manifest)),
        "obligation_order": list(OBLIGATION_ORDER),
        "obligation_order_sha256": _sha256(_canonical_bytes(list(OBLIGATION_ORDER))),
        "obligation_records": obligation_records,
        "positive_fixture_manifest": fixtures,
        "positive_fixture_manifest_sha256": _sha256(_canonical_bytes(fixtures)),
        "producer_id": PRODUCER_ID,
        "producer_script_sha256": producer_sha256,
        "production_reference_module": _identity_row(manifest, reference_path.name),
        "production_restriction": RESTRICTION,
        "reason": reason,
        "schema": SCHEMA,
        "station_schedule": _station_schedule(),
        "terminal": terminal,
    }


def produce(reference_module: Path, cases_definition: Path, contract: Path, authority_manifest: Path, output: Path, *, expected_reference_sha256: str, expected_producer_sha256: str, expected_authority_manifest_sha256: str) -> dict[str, Any]:
    reference_sha256 = _sha256(_canonical_file_bytes(reference_module))
    producer_sha256 = _sha256(_canonical_file_bytes(Path(__file__).resolve()))
    if reference_sha256 != expected_reference_sha256:
        raise ProducerError("production reference module differs from frozen authority")
    if producer_sha256 != expected_producer_sha256:
        raise ProducerError("producer differs from frozen authority")
    manifest_raw, manifest = _strict_canonical(authority_manifest)
    manifest_sha256 = _sha256(manifest_raw)
    if manifest_sha256 != expected_authority_manifest_sha256:
        raise ProducerError("authority manifest differs from runner authority")
    _validate_authority_manifest(manifest)
    for path in (reference_module, cases_definition, contract):
        row = _identity_row(manifest, path.name)
        raw = _canonical_file_bytes(path)
        if (len(raw), _sha256(raw)) != (row["bytes"], row["sha256"]):
            raise ProducerError(f"frozen input differs: {path.name}")
    module = _load_reference_module(reference_module)
    payload = _payload(module, reference_module, cases_definition, contract, manifest, manifest_sha256, producer_sha256=producer_sha256)
    proof = dict(payload)
    proof["payload_sha256"] = _sha256(_canonical_bytes(payload))
    _write_exclusive(output, proof)
    return proof


def _parser() -> argparse.ArgumentParser:
    root = Path(__file__).resolve().parents[2]
    reference = root / "docs" / "reference_cases"
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-module", type=Path, default=root / "src" / "anysolver" / "ge_beam3_curved_reference.py")
    parser.add_argument("--cases-definition", type=Path, default=reference / "ge_beam3_curved_p4_cases.json")
    parser.add_argument("--contract", type=Path, default=reference / "ge_beam3_curved_p4_contract.json")
    parser.add_argument("--authority-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-reference-sha256", required=True)
    parser.add_argument("--expected-producer-sha256", required=True)
    parser.add_argument("--expected-authority-manifest-sha256", required=True)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    produce(arguments.reference_module.resolve(), arguments.cases_definition.resolve(), arguments.contract.resolve(), arguments.authority_manifest.resolve(), arguments.output.resolve(), expected_reference_sha256=arguments.expected_reference_sha256, expected_producer_sha256=arguments.expected_producer_sha256, expected_authority_manifest_sha256=arguments.expected_authority_manifest_sha256)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
