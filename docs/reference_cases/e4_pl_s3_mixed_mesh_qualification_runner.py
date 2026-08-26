"""Executable, fail-closed foundation for mixed qualified-Q4/S3 campaigns.

The committed input is intentionally a cheap N=20/N=40 smoke tier.  It uses
the production element factories, stiffness assembly, linear solver and
physical recovery, but it is *not* a qualification cycle.  In particular,
observing a quantity named by the preregistered contract does not execute that
formal gate.  Every contract gate therefore remains explicitly UNEXECUTED in
the emitted aggregate.

The smoke mechanics include a force-loaded constant in-plane shear patch using
analytic boundary point forces.  A separate affine transverse-shear trace is
explicitly nonclassifying: it audits assumed-shear, bubble condensation and
recovery algebra but is not substituted for a published force-loaded test.

No result or provenance file is created until every selected case has reached
a terminal smoke status.  Canonical input, authority digests, topology hashes
and formulation identities all fail closed before mechanics are launched.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
from scipy import sparse


ROOT = Path(__file__).resolve().parents[2]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
DEFAULT_INPUT = REFERENCE_CASES / "e4_pl_s3_mixed_mesh_smoke_input.json"
INPUT_SCHEMA_PATH = REFERENCE_CASES / "e4_pl_s3_mixed_mesh_runner_schema.json"
MANIFEST_GENERATOR_PATH = REFERENCE_CASES / "e4_pl_s3_mixed_mesh_manifest.py"

INPUT_SCHEMA = "anysolver.e4-pl-s3-mixed-mesh-runner-input-v1"
RESULT_SCHEMA = "anysolver.e4-pl-s3-mixed-mesh-smoke-result-v1"
PROVENANCE_SCHEMA = "anysolver.e4-pl-s3-mixed-mesh-smoke-provenance-v1"
CLASSIFICATION = "SMOKE_ONLY_NOT_QUALIFICATION"
EXECUTOR_ID = "LINEAR_PATCH_EQUILIBRIUM_SMOKE_V1"
TERMINAL_RECORDED = "TERMINAL_SMOKE_OBSERVATIONS_RECORDED"
TERMINAL_FAILED = "TERMINAL_SMOKE_EXECUTION_FAILED"
Q4_FORMULATION_ID = "E4_PL_QUALIFIED_Q4_HYBRID_V2"
S3_FORMULATION_ID = "E4_PL_QUALIFIED_S3_COMPANION_V1"
EXPECTED_MANIFEST_SCHEMA = "anysolver.e4-pl-s3-mixed-mesh-connectivity-manifest-v1"
EXPECTED_CONTRACT_SCHEMA = "anysolver.e4-pl-s3-mixed-mesh-qualification-contract-v1"
SUPPORTED_SMOKE_LEVELS = frozenset((20, 40))
FUTURE_EXECUTOR_IDS = (
    "MIXED_BATCH_THROUGHPUT_V1",
    "MIXED_BUCKLING_V1",
    "MIXED_CONVERGENCE_V1",
    "MIXED_INTERFACE_RESULTANTS_V1",
    "MIXED_LOCKING_V1",
    "MIXED_MODAL_V1",
    "MIXED_PERFORMANCE_V1",
)


class CampaignInputError(ValueError):
    """The campaign input or one of its frozen authorities is invalid."""


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _pretty_canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _strict_json(raw: bytes, *, label: str) -> object:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        made: dict[str, object] = {}
        for key, value in pairs:
            if key in made:
                raise CampaignInputError(f"{label} contains duplicate key {key!r}")
            made[key] = value
        return made

    def reject_constant(value: str) -> object:
        raise CampaignInputError(f"{label} contains nonfinite constant {value!r}")

    try:
        return json.loads(
            raw,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CampaignInputError(f"{label} is not strict UTF-8 JSON: {exc}") from exc


def _read_canonical_json(path: Path, *, style: str, label: str) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = _strict_json(raw, label=label)
    if not isinstance(value, dict):
        raise CampaignInputError(f"{label} must be a JSON object")
    expected = _canonical_bytes(value) if style == "compact" else _pretty_canonical_bytes(value)
    if raw != expected:
        raise CampaignInputError(f"{label} is not canonical {style} JSON with one LF terminator")
    return value, raw


def _keys(value: Mapping[str, Any], expected: Iterable[str], label: str) -> None:
    actual = set(value)
    wanted = set(expected)
    if actual != wanted:
        raise CampaignInputError(
            f"{label} keys differ: missing={sorted(wanted - actual)}, extra={sorted(actual - wanted)}"
        )


def _mapping(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CampaignInputError(f"{label} must be an object")
    return value


def _list(value: object, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise CampaignInputError(f"{label} must be an array")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise CampaignInputError(f"{label} must be a nonempty string")
    return value


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CampaignInputError(f"{label} must be an integer")
    return int(value)


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CampaignInputError(f"{label} must be a number")
    made = float(value)
    if not math.isfinite(made):
        raise CampaignInputError(f"{label} must be finite")
    return made


def _vector(value: object, size: int, label: str) -> tuple[float, ...]:
    items = _list(value, label)
    if len(items) != size:
        raise CampaignInputError(f"{label} must contain exactly {size} values")
    return tuple(_number(item, f"{label}[{index}]") for index, item in enumerate(items))


def _hex_digest(value: object, label: str) -> str:
    made = _text(value, label)
    if len(made) != 64 or any(character not in "0123456789ABCDEF" for character in made):
        raise CampaignInputError(f"{label} must be an uppercase SHA-256 digest")
    return made


def _authority_path(relative: object, expected_name: str, label: str) -> Path:
    made = _text(relative, label)
    expected = f"docs/reference_cases/{expected_name}"
    if made != expected:
        raise CampaignInputError(f"{label} must be exactly {expected!r}")
    path = (ROOT / Path(made)).resolve()
    if path.parent != REFERENCE_CASES.resolve():
        raise CampaignInputError(f"{label} escapes the reference-case directory")
    return path


@dataclass(frozen=True)
class CampaignAuthorities:
    input_payload: dict[str, Any]
    input_raw: bytes
    input_path: Path
    manifest: dict[str, Any]
    manifest_raw: bytes
    manifest_path: Path
    contract: dict[str, Any]
    contract_raw: bytes
    contract_path: Path


@dataclass
class BuiltCase:
    model: Any
    load_case: Any | None
    record: dict[str, Any]
    case_spec: dict[str, Any]
    element_kinds: dict[int, str]
    topology_sha256: str
    model_input_sha256: str
    model_input_descriptor: dict[str, Any]


def _load_manifest_generator() -> Any:
    spec = importlib.util.spec_from_file_location(
        "_e4_pl_s3_mixed_mesh_manifest_for_runner", MANIFEST_GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise CampaignInputError("cannot load the mixed-mesh manifest generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_input_structure(payload: dict[str, Any]) -> None:
    _keys(payload, ("authority", "cases", "execution", "factories", "model", "schema"), "input")
    if payload["schema"] != INPUT_SCHEMA:
        raise CampaignInputError(f"input schema must be {INPUT_SCHEMA!r}")

    authority = _mapping(payload["authority"], "authority")
    _keys(authority, ("connectivity_manifest", "qualification_contract"), "authority")
    for name in ("connectivity_manifest", "qualification_contract"):
        item = _mapping(authority[name], f"authority.{name}")
        _keys(item, ("path", "sha256"), f"authority.{name}")
        _text(item["path"], f"authority.{name}.path")
        _hex_digest(item["sha256"], f"authority.{name}.sha256")

    execution = _mapping(payload["execution"], "execution")
    _keys(
        execution,
        ("canonical_cycles", "classification", "executor", "numerical_library_threads_per_process"),
        "execution",
    )
    if execution["classification"] != CLASSIFICATION:
        raise CampaignInputError(f"execution.classification must be {CLASSIFICATION!r}")
    if execution["executor"] != EXECUTOR_ID:
        known = (EXECUTOR_ID, *FUTURE_EXECUTOR_IDS)
        if execution["executor"] in known:
            raise CampaignInputError(f"executor {execution['executor']!r} is registered but not implemented")
        raise CampaignInputError(f"unknown executor {execution['executor']!r}")
    if _integer(execution["canonical_cycles"], "execution.canonical_cycles") != 1:
        raise CampaignInputError("the smoke executor launches exactly one non-qualifying cycle")
    if _integer(
        execution["numerical_library_threads_per_process"],
        "execution.numerical_library_threads_per_process",
    ) != 1:
        raise CampaignInputError("the smoke executor requires one numerical-library thread")

    factories = _mapping(payload["factories"], "factories")
    _keys(factories, ("default_s3_expected", "q4", "s3"), "factories")
    if factories["default_s3_expected"] != "legacy-s3":
        raise CampaignInputError("factories.default_s3_expected must remain 'legacy-s3'")
    expected_factories = {
        "q4": ("anysolver.e4_pl_element", "QualifiedE4PLShellElement", Q4_FORMULATION_ID, "e4-pl"),
        "s3": ("anysolver.e4_pl_s3_element", "QualifiedE4PLS3ShellElement", S3_FORMULATION_ID, "e4-pl-s3"),
    }
    for kind, expected in expected_factories.items():
        item = _mapping(factories[kind], f"factories.{kind}")
        _keys(item, ("class_module", "class_name", "formulation_id", "selector"), f"factories.{kind}")
        actual = tuple(item[key] for key in ("class_module", "class_name", "formulation_id", "selector"))
        if actual != expected:
            raise CampaignInputError(f"factories.{kind} is not the frozen qualified factory identity")

    model = _mapping(payload["model"], "model")
    _keys(
        model,
        ("boundary_conditions", "coordinates", "material", "patches", "section", "static_probe"),
        "model",
    )
    coordinates = _mapping(model["coordinates"], "model.coordinates")
    _keys(coordinates, ("length_x", "length_y", "origin", "owner_normal", "rule"), "model.coordinates")
    if coordinates["rule"] != "ROW_MAJOR_UNIT_RECTANGLE_BINARY64_V1":
        raise CampaignInputError("unsupported coordinate rule")
    if _vector(coordinates["origin"], 3, "model.coordinates.origin") != (0.0, 0.0, 0.0):
        raise CampaignInputError("the smoke coordinate origin must be [0,0,0]")
    if _vector(coordinates["owner_normal"], 3, "model.coordinates.owner_normal") != (0.0, 0.0, 1.0):
        raise CampaignInputError("the smoke owner normal must be [0,0,1]")
    if _number(coordinates["length_x"], "model.coordinates.length_x") <= 0.0:
        raise CampaignInputError("length_x must be positive")
    if _number(coordinates["length_y"], "model.coordinates.length_y") <= 0.0:
        raise CampaignInputError("length_y must be positive")

    material = _mapping(model["material"], "model.material")
    _keys(material, ("density", "elastic_modulus", "name", "poisson_ratio"), "model.material")
    _text(material["name"], "model.material.name")
    if _number(material["elastic_modulus"], "model.material.elastic_modulus") <= 0.0:
        raise CampaignInputError("elastic_modulus must be positive")
    nu = _number(material["poisson_ratio"], "model.material.poisson_ratio")
    if not (-1.0 < nu < 0.5):
        raise CampaignInputError("poisson_ratio must lie in (-1,0.5)")
    if _number(material["density"], "model.material.density") < 0.0:
        raise CampaignInputError("density must be nonnegative")

    section = _mapping(model["section"], "model.section")
    _keys(
        section,
        (
            "q4_drilling_stabilization",
            "q4_hourglass_stabilization",
            "q4_planar_tolerance",
            "q4_pl_stabilization",
            "q4_warped_formulation",
            "s3_director_polarity",
            "thickness",
        ),
        "model.section",
    )
    for key in (
        "q4_drilling_stabilization",
        "q4_hourglass_stabilization",
        "q4_planar_tolerance",
        "q4_pl_stabilization",
        "thickness",
    ):
        if _number(section[key], f"model.section.{key}") <= 0.0:
            raise CampaignInputError(f"model.section.{key} must be positive")
    if section["q4_warped_formulation"] != "varying_frame":
        raise CampaignInputError("the Q4 warped formulation identity changed")
    if _integer(section["s3_director_polarity"], "model.section.s3_director_polarity") != 1:
        raise CampaignInputError("the smoke S3 director polarity must be +1")

    boundary = _list(model["boundary_conditions"], "model.boundary_conditions")
    expected_boundary = (
        ("plane", "all_nodes", ("uz", "rx", "ry")),
        ("left_axial", "left_edge", ("ux",)),
        ("origin_transverse", "origin", ("uy",)),
    )
    if len(boundary) != len(expected_boundary):
        raise CampaignInputError("the smoke model requires exactly three boundary-condition records")
    for index, (item_value, expected) in enumerate(zip(boundary, expected_boundary)):
        item = _mapping(item_value, f"model.boundary_conditions[{index}]")
        _keys(item, ("dofs", "name", "selection", "value"), f"model.boundary_conditions[{index}]")
        actual = (item["name"], item["selection"], tuple(_list(item["dofs"], f"boundary[{index}].dofs")))
        if actual != expected or _number(item["value"], f"boundary[{index}].value") != 0.0:
            raise CampaignInputError("the smoke boundary-condition identity changed")

    static_probe = _mapping(model["static_probe"], "model.static_probe")
    _keys(static_probe, ("distribution", "name", "right_edge_resultant"), "model.static_probe")
    if static_probe["distribution"] != "CONSISTENT_UNIFORM_RIGHT_EDGE_LINE_RESULTANT_V1":
        raise CampaignInputError("unsupported static-probe distribution")
    _text(static_probe["name"], "model.static_probe.name")
    resultant = _vector(static_probe["right_edge_resultant"], 6, "model.static_probe.right_edge_resultant")
    if resultant[0] == 0.0 or any(resultant[index] != 0.0 for index in range(1, 6)):
        raise CampaignInputError("the smoke static probe must be a nonzero global-x force resultant")

    patches = _mapping(model["patches"], "model.patches")
    _keys(patches, ("bending", "membrane", "shear"), "model.patches")
    membrane = _mapping(patches["membrane"], "model.patches.membrane")
    _keys(membrane, ("eps_x", "eps_y", "gamma_xy"), "model.patches.membrane")
    bending = _mapping(patches["bending"], "model.patches.bending")
    _keys(bending, ("kappa_x",), "model.patches.bending")
    shear = _mapping(patches["shear"], "model.patches.shear")
    _keys(shear, ("gamma_xz", "gamma_yz"), "model.patches.shear")
    for group_name, group in (("membrane", membrane), ("bending", bending), ("shear", shear)):
        for key, value in group.items():
            _number(value, f"model.patches.{group_name}.{key}")

    cases = _list(payload["cases"], "cases")
    if not cases:
        raise CampaignInputError("at least one smoke case is required")
    case_ids: set[str] = set()
    for index, case_value in enumerate(cases):
        case = _mapping(case_value, f"cases[{index}]")
        _keys(case, ("case_id", "topology"), f"cases[{index}]")
        case_id = _text(case["case_id"], f"cases[{index}].case_id")
        if case_id in case_ids:
            raise CampaignInputError(f"duplicate case_id {case_id!r}")
        case_ids.add(case_id)
        topology = _mapping(case["topology"], f"cases[{index}].topology")
        _keys(
            topology,
            ("connectivity_sha256", "diagonal", "level", "mask", "split_base_cell_count"),
            f"cases[{index}].topology",
        )
        level = _integer(topology["level"], f"cases[{index}].topology.level")
        if level not in SUPPORTED_SMOKE_LEVELS:
            raise CampaignInputError(
                f"level {level} belongs to a future formal executor; smoke supports only {sorted(SUPPORTED_SMOKE_LEVELS)}"
            )
        _text(topology["mask"], f"cases[{index}].topology.mask")
        _text(topology["diagonal"], f"cases[{index}].topology.diagonal")
        _integer(topology["split_base_cell_count"], f"cases[{index}].topology.split_base_cell_count")
        _hex_digest(topology["connectivity_sha256"], f"cases[{index}].topology.connectivity_sha256")


def load_authorities(input_path: Path = DEFAULT_INPUT) -> CampaignAuthorities:
    payload, input_raw = _read_canonical_json(
        Path(input_path), style="pretty", label="mixed-mesh runner input"
    )
    _validate_input_structure(payload)
    authority = payload["authority"]
    manifest_path = _authority_path(
        authority["connectivity_manifest"]["path"],
        "e4_pl_s3_mixed_mesh_connectivity_manifest.json",
        "authority.connectivity_manifest.path",
    )
    contract_path = _authority_path(
        authority["qualification_contract"]["path"],
        "e4_pl_s3_mixed_mesh_qualification_contract.json",
        "authority.qualification_contract.path",
    )
    manifest, manifest_raw = _read_canonical_json(
        manifest_path, style="compact", label="connectivity manifest"
    )
    contract, contract_raw = _read_canonical_json(
        contract_path, style="pretty", label="qualification contract"
    )
    if _sha256(manifest_raw) != authority["connectivity_manifest"]["sha256"]:
        raise CampaignInputError("connectivity manifest digest disagrees with runner input")
    if _sha256(contract_raw) != authority["qualification_contract"]["sha256"]:
        raise CampaignInputError("qualification contract digest disagrees with runner input")
    if manifest.get("schema") != EXPECTED_MANIFEST_SCHEMA:
        raise CampaignInputError("connectivity manifest schema is incompatible")
    if contract.get("schema") != EXPECTED_CONTRACT_SCHEMA:
        raise CampaignInputError("qualification contract schema is incompatible")
    connectivity_authority = _mapping(contract.get("connectivity_authority"), "contract.connectivity_authority")
    if connectivity_authority != {
        "bytes": len(manifest_raw),
        "gated_record_count": len(_list(manifest.get("records"), "manifest.records")),
        "path": "docs/reference_cases/e4_pl_s3_mixed_mesh_connectivity_manifest.json",
        "research_control_record_count": len(
            _list(_mapping(manifest.get("research_control"), "manifest.research_control").get("records"), "manifest.research_control.records")
        ),
        "schema": manifest["schema"],
        "sha256": _sha256(manifest_raw),
    }:
        raise CampaignInputError("qualification contract no longer binds the exact connectivity authority")
    candidate = _mapping(contract.get("candidate"), "contract.candidate")
    if candidate.get("qualified_q4_formulation_id") != Q4_FORMULATION_ID:
        raise CampaignInputError("qualification contract Q4 formulation identity changed")
    if candidate.get("qualified_s3_formulation_id") != S3_FORMULATION_ID:
        raise CampaignInputError("qualification contract S3 formulation identity changed")
    gates = _mapping(contract.get("acceptance_gates"), "contract.acceptance_gates")
    if not gates:
        raise CampaignInputError("qualification contract has no acceptance gates")

    records = _list(manifest["records"], "manifest.records")
    record_index: dict[tuple[int, str, str, int], dict[str, Any]] = {}
    for record_value in records:
        record = _mapping(record_value, "manifest record")
        key = (
            int(record["level"]),
            str(record["mask"]),
            str(record["diagonal"]),
            int(record["split_base_cell_count"]),
        )
        if key in record_index:
            raise CampaignInputError(f"duplicate manifest topology key {key!r}")
        record_index[key] = record
    for case in payload["cases"]:
        topology = case["topology"]
        key = (
            topology["level"],
            topology["mask"],
            topology["diagonal"],
            topology["split_base_cell_count"],
        )
        record = record_index.get(key)
        if record is None:
            raise CampaignInputError(f"case {case['case_id']!r} is absent from the gated manifest")
        if topology["connectivity_sha256"] != record["connectivity_sha256"]:
            raise CampaignInputError(f"case {case['case_id']!r} connectivity digest disagrees with the manifest")
    return CampaignAuthorities(
        input_payload=payload,
        input_raw=input_raw,
        input_path=Path(input_path).resolve(),
        manifest=manifest,
        manifest_raw=manifest_raw,
        manifest_path=manifest_path,
        contract=contract,
        contract_raw=contract_raw,
        contract_path=contract_path,
    )


def _manifest_record(authorities: CampaignAuthorities, case_spec: Mapping[str, Any]) -> dict[str, Any]:
    topology = case_spec["topology"]
    for record in authorities.manifest["records"]:
        if (
            record["level"] == topology["level"]
            and record["mask"] == topology["mask"]
            and record["diagonal"] == topology["diagonal"]
            and record["split_base_cell_count"] == topology["split_base_cell_count"]
        ):
            return dict(record)
    raise CampaignInputError(f"manifest record disappeared for case {case_spec['case_id']!r}")


def _node_id(i: int, j: int, level: int) -> int:
    return j * (level + 1) + i + 1


def _cell_connectivity(
    i: int,
    j: int,
    level: int,
    *,
    split: bool,
    diagonal: str,
) -> tuple[tuple[str, tuple[int, ...]], ...]:
    n00 = _node_id(i, j, level)
    n10 = _node_id(i + 1, j, level)
    n11 = _node_id(i + 1, j + 1, level)
    n01 = _node_id(i, j + 1, level)
    if not split:
        return (("Q4", (n00, n10, n11, n01)),)
    made = diagonal
    if made == "alternating":
        made = "backslash" if (i + j) % 2 == 0 else "slash"
    if made == "backslash":
        return (("S3", (n00, n10, n11)), ("S3", (n00, n11, n01)))
    if made == "slash":
        return (("S3", (n00, n10, n01)), ("S3", (n10, n11, n01)))
    raise CampaignInputError(f"unsupported diagonal {diagonal!r}")


def topology_sha256(level: int, elements: Iterable[tuple[int, str, Sequence[int]]]) -> str:
    digest = hashlib.sha256(f"level:{int(level)}\n".encode("ascii"))
    for element_id, kind, node_ids in elements:
        nodes = ",".join(str(int(node_id)) for node_id in node_ids)
        digest.update(f"{int(element_id)}:{kind}:{nodes}\n".encode("ascii"))
    return digest.hexdigest().upper()


def _float_hex(value: float) -> str:
    made = float(value)
    if not math.isfinite(made):
        raise CampaignInputError("model input contains a nonfinite binary64 value")
    return made.hex()


def _rotation_or_identity(rotation: np.ndarray | None) -> np.ndarray:
    made = np.eye(3, dtype=float) if rotation is None else np.asarray(rotation, dtype=float)
    if made.shape != (3, 3) or not np.all(np.isfinite(made)):
        raise CampaignInputError("model rotation must be a finite 3x3 matrix")
    if np.linalg.norm(made.T @ made - np.eye(3), ord=np.inf) > 1.0e-14 or np.linalg.det(made) < 1.0 - 1.0e-14:
        raise CampaignInputError("model rotation must be proper orthogonal")
    return made


def build_case_model(
    authorities: CampaignAuthorities,
    case_spec: Mapping[str, Any],
    *,
    rotation: np.ndarray | None = None,
    include_auxiliary_inputs: bool = True,
) -> BuiltCase:
    """Construct one complete production model and bind its exact topology."""

    from anysolver.boundary import BoundaryCondition, LoadCase
    from anysolver.elements import create_shell_element
    from anysolver.fe_core import FEModel

    generator = _load_manifest_generator()
    record = _manifest_record(authorities, case_spec)
    topology = case_spec["topology"]
    level = int(topology["level"])
    split_count = int(topology["split_base_cell_count"])
    mask = str(topology["mask"])
    diagonal = str(topology["diagonal"])
    base_cells = () if split_count == 0 else generator.selected_base_cells(mask, split_count)
    split_cells = set(generator.expanded_split_cells(base_cells, level))
    if len(split_cells) != int(record["split_refined_cell_count"]):
        raise CampaignInputError("refined split-cell count disagrees with the manifest")

    model_input = authorities.input_payload["model"]
    coordinates_spec = model_input["coordinates"]
    material_spec = model_input["material"]
    section = model_input["section"]
    length_x = float(coordinates_spec["length_x"])
    length_y = float(coordinates_spec["length_y"])
    origin = np.asarray(coordinates_spec["origin"], dtype=float)
    owner_normal = np.asarray(coordinates_spec["owner_normal"], dtype=float)
    rotation_matrix = _rotation_or_identity(rotation)
    rotated_owner_normal = rotation_matrix @ owner_normal

    model = FEModel(name=f"mixed_q4_s3:{case_spec['case_id']}")
    model.add_material(
        str(material_spec["name"]),
        float(material_spec["elastic_modulus"]),
        float(material_spec["poisson_ratio"]),
        density=float(material_spec["density"]),
    )
    coordinate_records: list[list[Any]] = []
    for j in range(level + 1):
        for i in range(level + 1):
            node_id = _node_id(i, j, level)
            point = origin + np.asarray((length_x * i / level, length_y * j / level, 0.0))
            point = rotation_matrix @ point
            model.add_node(node_id, float(point[0]), float(point[1]), float(point[2]))
            coordinate_records.append([node_id, *(_float_hex(value) for value in point)])

    element_kinds: dict[int, str] = {}
    element_records: list[list[Any]] = []
    element_id = 0
    factories = authorities.input_payload["factories"]
    for j in range(level):
        for i in range(level):
            for kind, node_ids_tuple in _cell_connectivity(
                i,
                j,
                level,
                split=(i, j) in split_cells,
                diagonal=diagonal,
            ):
                element_id += 1
                node_ids = list(node_ids_tuple)
                if kind == "Q4":
                    element = create_shell_element(
                        element_id,
                        node_ids,
                        str(material_spec["name"]),
                        formulation=str(factories["q4"]["selector"]),
                        thickness=float(section["thickness"]),
                        drilling_stabilization=float(section["q4_drilling_stabilization"]),
                        hourglass_stabilization=float(section["q4_hourglass_stabilization"]),
                        pl_stabilization=float(section["q4_pl_stabilization"]),
                        planar_tolerance=float(section["q4_planar_tolerance"]),
                        warped_formulation=str(section["q4_warped_formulation"]),
                    )
                    normal_record: list[str] | None = None
                else:
                    element = create_shell_element(
                        element_id,
                        node_ids,
                        str(material_spec["name"]),
                        formulation=str(factories["s3"]["selector"]),
                        thickness=float(section["thickness"]),
                        reference_normal=rotated_owner_normal,
                        director_polarity=int(section["s3_director_polarity"]),
                    )
                    normal_record = [_float_hex(value) for value in rotated_owner_normal]
                expected_factory = factories[kind.lower()]
                actual_identity = (
                    type(element).__module__,
                    type(element).__name__,
                    getattr(element, "formulation_id", None),
                )
                expected_identity = (
                    expected_factory["class_module"],
                    expected_factory["class_name"],
                    expected_factory["formulation_id"],
                )
                if actual_identity != expected_identity:
                    raise CampaignInputError(
                        f"element {element_id} factory identity {actual_identity!r} != {expected_identity!r}"
                    )
                model.add_element(element_id, element)
                element_kinds[element_id] = kind
                element_records.append(
                    [element_id, kind, node_ids, str(element.formulation_id), normal_record]
                )

    topology_digest = topology_sha256(
        level,
        (
            (element_id_value, element_kinds[element_id_value], model.mesh.elements[element_id_value].node_ids)
            for element_id_value in model.mesh.elements
        ),
    )
    if topology_digest != record["connectivity_sha256"]:
        raise CampaignInputError(
            f"constructed topology {topology_digest} disagrees with manifest {record['connectivity_sha256']}"
        )
    counts = {
        "Q4": sum(kind == "Q4" for kind in element_kinds.values()),
        "S3": sum(kind == "S3" for kind in element_kinds.values()),
    }
    if counts != {"Q4": int(record["q4_element_count"]), "S3": int(record["s3_element_count"])}:
        raise CampaignInputError("constructed element counts disagree with the manifest")
    if model.mesh.num_nodes != int(record["node_count"]):
        raise CampaignInputError("constructed node count disagrees with the manifest")

    boundary_records: list[dict[str, Any]] = []
    load_records: list[list[Any]] = []
    load_case = None
    if include_auxiliary_inputs:
        selections = {
            "all_nodes": list(model.mesh.nodes),
            "left_edge": [_node_id(0, j, level) for j in range(level + 1)],
            "origin": [_node_id(0, 0, level)],
        }
        for spec in model_input["boundary_conditions"]:
            node_ids = selections[str(spec["selection"])]
            dof_constraints = {str(dof): float(spec["value"]) for dof in spec["dofs"]}
            model.add_boundary_condition(
                BoundaryCondition(str(spec["name"]), node_ids, dof_constraints)
            )
            boundary_records.append(
                {
                    "dof_constraints": {key: _float_hex(value) for key, value in sorted(dof_constraints.items())},
                    "name": str(spec["name"]),
                    "node_ids": node_ids,
                }
            )
        static_probe = model_input["static_probe"]
        load_case = LoadCase(str(static_probe["name"]))
        resultant = np.asarray(static_probe["right_edge_resultant"], dtype=float)
        for j in range(level + 1):
            node_id = _node_id(level, j, level)
            weight = 0.5 / level if j in (0, level) else 1.0 / level
            nodal = weight * resultant
            load_case.add_nodal_load(node_id, nodal)
            load_records.append([node_id, [_float_hex(value) for value in nodal]])
        model.add_load_case(load_case)

    descriptor = {
        "boundary_conditions": boundary_records,
        "case_id": str(case_spec["case_id"]),
        "connectivity_sha256": topology_digest,
        "coordinates": coordinate_records,
        "elements": element_records,
        "loads": load_records,
        "material": {
            "density": _float_hex(float(material_spec["density"])),
            "elastic_modulus": _float_hex(float(material_spec["elastic_modulus"])),
            "name": str(material_spec["name"]),
            "poisson_ratio": _float_hex(float(material_spec["poisson_ratio"])),
        },
        "patches": model_input["patches"],
        "rotation": [[_float_hex(value) for value in row] for row in rotation_matrix],
        "section": {
            key: (_float_hex(float(value)) if isinstance(value, (int, float)) and not isinstance(value, bool) else value)
            for key, value in sorted(section.items())
        },
    }
    return BuiltCase(
        model=model,
        load_case=load_case,
        record=record,
        case_spec=dict(case_spec),
        element_kinds=element_kinds,
        topology_sha256=topology_digest,
        model_input_sha256=_sha256(_canonical_bytes(descriptor)),
        model_input_descriptor=descriptor,
    )


def _frobenius_sparse(matrix: sparse.spmatrix) -> float:
    data = np.asarray(matrix.data, dtype=float)
    return float(math.sqrt(float(data @ data))) if data.size else 0.0


def _relative_sparse_residual(numerator: sparse.spmatrix, denominator: sparse.spmatrix) -> float:
    return _frobenius_sparse(numerator) / max(_frobenius_sparse(denominator), np.finfo(float).tiny)


def _patch_displacement(model: Any, patch_name: str, patch: Mapping[str, Any]) -> np.ndarray:
    displacement = np.zeros(model.mesh.dof_manager.total_dofs, dtype=float)
    for node in model.mesh.nodes.values():
        x, y, _z = node.coords()
        if patch_name == "membrane":
            eps_x = float(patch["eps_x"])
            eps_y = float(patch["eps_y"])
            gamma_xy = float(patch["gamma_xy"])
            displacement[node.dofs[0]] = eps_x * x
            displacement[node.dofs[1]] = eps_y * y + gamma_xy * x
            # E4-PL's scalar constraint is theta_D-(v_x-u_y)/2.
            displacement[node.dofs[5]] = 0.5 * gamma_xy
        elif patch_name == "bending":
            kappa_x = float(patch["kappa_x"])
            displacement[node.dofs[2]] = -0.5 * kappa_x * x * x
            displacement[node.dofs[4]] = kappa_x * x
        elif patch_name == "shear":
            displacement[node.dofs[2]] = float(patch["gamma_xz"]) * x + float(patch["gamma_yz"]) * y
        else:
            raise AssertionError(patch_name)
    return displacement


def _rotation_only_shear_displacement(model: Any, patch: Mapping[str, Any]) -> np.ndarray:
    """Return the same compatible transverse shear using rotations only.

    With the production convention ``gamma_xz=w,x+ry`` and
    ``gamma_yz=w,y-rx``, this field is kinematically identical to the affine
    ``w`` trace used by :func:`_patch_displacement`.  Comparing both fields is
    an explicit sign-convention diagnostic; it is not a qualification patch.
    """

    displacement = np.zeros(model.mesh.dof_manager.total_dofs, dtype=float)
    gamma_xz = float(patch["gamma_xz"])
    gamma_yz = float(patch["gamma_yz"])
    for node in model.mesh.nodes.values():
        displacement[node.dofs[3]] = -gamma_yz
        displacement[node.dofs[4]] = gamma_xz
    return displacement


def _patch_targets(material: Any, thickness: float, patch_name: str, patch: Mapping[str, Any]) -> dict[str, float]:
    elastic_modulus = float(material.elastic_modulus)
    poisson_ratio = float(material.poisson_ratio)
    shear_modulus = float(material.shear_modulus)
    if patch_name == "membrane":
        eps_x = float(patch["eps_x"])
        eps_y = float(patch["eps_y"])
        gamma_xy = float(patch["gamma_xy"])
        scale = elastic_modulus / (1.0 - poisson_ratio**2)
        return {
            "xx": scale * (eps_x + poisson_ratio * eps_y),
            "xy": shear_modulus * gamma_xy,
            "yy": scale * (eps_y + poisson_ratio * eps_x),
        }
    if patch_name == "bending":
        scale = elastic_modulus * thickness / (2.0 * (1.0 - poisson_ratio**2))
        kappa_x = float(patch["kappa_x"])
        return {"xx": scale * kappa_x, "xy": 0.0, "yy": scale * poisson_ratio * kappa_x}
    if patch_name == "shear":
        scale = (5.0 / 6.0) * shear_modulus
        return {"xz": scale * float(patch["gamma_xz"]), "yz": scale * float(patch["gamma_yz"])}
    raise AssertionError(patch_name)


def _expected_patch_energy(
    material: Any,
    thickness: float,
    area: float,
    patch_name: str,
    patch: Mapping[str, Any],
    targets: Mapping[str, float],
) -> float:
    if patch_name == "membrane":
        density = (
            targets["xx"] * float(patch["eps_x"])
            + targets["yy"] * float(patch["eps_y"])
            + targets["xy"] * float(patch["gamma_xy"])
        )
        return 0.5 * thickness * area * density
    if patch_name == "bending":
        rigidity = (
            float(material.elastic_modulus)
            * thickness**3
            / (12.0 * (1.0 - float(material.poisson_ratio) ** 2))
        )
        return 0.5 * area * rigidity * float(patch["kappa_x"]) ** 2
    if patch_name == "shear":
        density = (
            targets["xz"] * float(patch["gamma_xz"])
            + targets["yz"] * float(patch["gamma_yz"])
        )
        return 0.5 * thickness * area * density
    raise AssertionError(patch_name)


def _recovered_components(recovery: Mapping[str, Any], patch_name: str) -> dict[str, np.ndarray]:
    if patch_name == "membrane":
        return {
            component: 0.5
            * (
                np.asarray(recovery[f"global_{component}_top"], dtype=float)
                + np.asarray(recovery[f"global_{component}_bot"], dtype=float)
            )
            for component in ("xx", "xy", "yy")
        }
    if patch_name == "bending":
        return {
            component: 0.5
            * (
                np.asarray(recovery[f"global_{component}_top"], dtype=float)
                - np.asarray(recovery[f"global_{component}_bot"], dtype=float)
            )
            for component in ("xx", "xy", "yy")
        }
    if patch_name == "shear":
        return {
            component: 0.5
            * (
                np.asarray(recovery[f"global_{component}_top"], dtype=float)
                + np.asarray(recovery[f"global_{component}_bot"], dtype=float)
            )
            for component in ("xz", "yz")
        }
    raise AssertionError(patch_name)


def _resultant_residual(model: Any, vector: np.ndarray) -> tuple[float, float, list[float], list[float]]:
    nodal = np.asarray(vector, dtype=float).reshape(model.mesh.num_nodes, 6)
    forces = nodal[:, :3]
    couples = nodal[:, 3:]
    coordinates = np.asarray([node.coords() for node in model.mesh.nodes.values()], dtype=float)
    force_resultant = np.sum(forces, axis=0)
    moment_resultant = np.sum(couples + np.cross(coordinates, forces), axis=0)
    force_scale = max(float(np.sum(np.linalg.norm(forces, axis=1))), 1.0)
    length_scale = max(float(np.ptp(coordinates, axis=0).max()), 1.0)
    moment_scale = max(
        float(np.sum(np.linalg.norm(couples, axis=1))) + length_scale * force_scale,
        1.0,
    )
    return (
        float(np.linalg.norm(force_resultant) / force_scale),
        float(np.linalg.norm(moment_resultant) / moment_scale),
        [float(value) for value in force_resultant],
        [float(value) for value in moment_resultant],
    )


def _patch_observables(built: BuiltCase, stiffness: sparse.csr_matrix) -> dict[str, Any]:
    from anysolver.e4_pl_s3_element import (
        PHYSICAL_EXTERNAL_INDICES,
        TRIANGLE_QUADRATURE,
        _kinematic_matrix,
    )

    model = built.model
    material = model.get_material(str(built.model_input_descriptor["material"]["name"]))
    thickness = authorities_float(built.model_input_descriptor["section"]["thickness"])
    coordinates = np.asarray([node.coords() for node in model.mesh.nodes.values()], dtype=float)
    area = float(np.ptp(coordinates[:, 0]) * np.ptp(coordinates[:, 1]))
    patch_specs = built.model_input_descriptor["patches"]
    results: dict[str, Any] = {}
    for patch_name in ("membrane", "bending", "shear"):
        patch = patch_specs[patch_name]
        displacement = _patch_displacement(model, patch_name, patch)
        rotation_only_shear = (
            _rotation_only_shear_displacement(model, patch)
            if patch_name == "shear"
            else None
        )
        targets = _patch_targets(material, thickness, patch_name, patch)
        topology_error = {"Q4": 0.0, "S3": 0.0}
        integration_point_count = {"Q4": 0, "S3": 0}
        energies = {
            "physical": 0.0,
            "q4_physical": 0.0,
            "q4_pl": 0.0,
            "q4_residual_hourglass": 0.0,
            "s3_physical": 0.0,
            "s3_pl": 0.0,
            "total": 0.0,
        }
        element_work = 0.0
        maximum_s3_bubble_rotation_norm = 0.0
        maximum_s3_bubble_equilibrium_residual = 0.0
        maximum_s3_bubble_force_coupling_ratio = 0.0
        maximum_s3_bubble_shear_operator_mean_norm = 0.0
        maximum_s3_kinematic_decomposition_bubble_residual = 0.0
        maximum_s3_kinematic_decomposition_stress_residual = 0.0
        maximum_s3_uncondensed_trace_stress_residual = 0.0
        s3_bubble_relaxation_energy = 0.0
        s3_recovered_physical_energy = 0.0
        target_scale = max(max(abs(value) for value in targets.values()), 1.0)
        for element_id, element in model.mesh.elements.items():
            kind = built.element_kinds[int(element_id)]
            mapping = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
            local_displacement = displacement[mapping]
            components = element.compute_stiffness_components(model.mesh, material)
            component_energy = {
                name: 0.5 * float(local_displacement @ np.asarray(components[name]) @ local_displacement)
                for name in ("physical", "pl", "hourglass", "total")
            }
            energies["physical"] += component_energy["physical"]
            energies["total"] += component_energy["total"]
            element_work += 2.0 * component_energy["total"]
            if kind == "S3":
                energies["s3_physical"] += component_energy["physical"]
                energies["s3_pl"] += component_energy["pl"]
            else:
                energies["q4_physical"] += component_energy["physical"]
                energies["q4_pl"] += component_energy["pl"]
                energies["q4_residual_hourglass"] += component_energy["hourglass"]
            recovery = element.compute_stresses(
                model.mesh,
                local_displacement,
                material,
                return_global=True,
            )
            recovered = _recovered_components(recovery, patch_name)
            if kind == "S3":
                maximum_s3_bubble_rotation_norm = max(
                    maximum_s3_bubble_rotation_norm,
                    float(np.linalg.norm(np.asarray(recovery["bubble_rotations"], dtype=float))),
                )
                if patch_name == "shear":
                    assert rotation_only_shear is not None
                    frame = np.asarray(components["frame"], dtype=float)
                    transform = element._local_dof_transform(frame)
                    local_external_18 = transform @ local_displacement
                    physical_external = local_external_18[
                        np.asarray(PHYSICAL_EXTERNAL_INDICES, dtype=np.intp)
                    ]
                    uncondensed = np.asarray(components["uncondensed_physical"], dtype=float)
                    bubble_block = np.asarray(components["bubble_block"], dtype=float)
                    bubble = np.asarray(recovery["bubble_rotations"], dtype=float)
                    bubble_force = uncondensed[15:, :15] @ physical_external
                    bubble_equilibrium = bubble_force + bubble_block @ bubble
                    element_coordinates = np.asarray(
                        element.get_node_coordinates(model.mesh), dtype=float
                    )
                    element_area = 0.5 * float(
                        np.linalg.norm(
                            np.cross(
                                element_coordinates[1] - element_coordinates[0],
                                element_coordinates[2] - element_coordinates[0],
                            )
                        )
                    )
                    shear_force_scale = max(
                        float(np.linalg.norm(tuple(targets.values())))
                        * thickness
                        * element_area,
                        np.finfo(float).tiny,
                    )
                    maximum_s3_bubble_force_coupling_ratio = max(
                        maximum_s3_bubble_force_coupling_ratio,
                        float(np.linalg.norm(bubble_force)) / shear_force_scale,
                    )
                    maximum_s3_bubble_equilibrium_residual = max(
                        maximum_s3_bubble_equilibrium_residual,
                        float(np.linalg.norm(bubble_equilibrium))
                        / max(float(np.linalg.norm(bubble_force)), np.finfo(float).tiny),
                    )
                    unrelaxed_energy = 0.5 * float(
                        physical_external @ uncondensed[:15, :15] @ physical_external
                    )
                    s3_bubble_relaxation_energy += max(
                        unrelaxed_energy - component_energy["physical"],
                        0.0,
                    )

                    shear_operator_mean = np.zeros((2, 2), dtype=float)
                    uncondensed_coordinates = np.concatenate(
                        (physical_external, np.zeros(2, dtype=float))
                    )
                    director_transform = element._director_generalized_transform()
                    determinant = abs(
                        float(
                            np.linalg.det(
                                np.asarray(
                                    (
                                        components["local_nodes"][1]
                                        - components["local_nodes"][0],
                                        components["local_nodes"][2]
                                        - components["local_nodes"][0],
                                    ),
                                    dtype=float,
                                )
                            )
                        )
                    )
                    recovered_strains = np.hstack(
                        (
                            np.asarray(recovery["membrane_strain"], dtype=float),
                            np.asarray(recovery["curvature"], dtype=float),
                            np.asarray(recovery["transverse_shear_strain"], dtype=float),
                        )
                    )
                    recovered_resultants = np.hstack(
                        (
                            np.asarray(recovery["membrane_resultants"], dtype=float),
                            np.asarray(recovery["bending_resultants"], dtype=float),
                            np.asarray(recovery["transverse_shear_resultants"], dtype=float),
                        )
                    )
                    for point_index, (r, s, weight) in enumerate(TRIANGLE_QUADRATURE):
                        operator = director_transform @ _kinematic_matrix(
                            np.asarray(components["local_nodes"], dtype=float),
                            r,
                            s,
                            components["assumed_shear_samples"],
                        )
                        shear_operator_mean += 2.0 * float(weight) * operator[6:, 15:]
                        uncondensed_strain = operator @ uncondensed_coordinates
                        uncondensed_resultant = (
                            np.asarray(components["constitutive"], dtype=float)
                            @ uncondensed_strain
                        )
                        uncondensed_local_stress = uncondensed_resultant[6:] / thickness
                        uncondensed_global_shear = float(element.director_polarity) * (
                            uncondensed_local_stress[0] * frame[:, 0]
                            + uncondensed_local_stress[1] * frame[:, 1]
                        )
                        maximum_s3_uncondensed_trace_stress_residual = max(
                            maximum_s3_uncondensed_trace_stress_residual,
                            float(
                                np.linalg.norm(
                                    uncondensed_global_shear
                                    - np.asarray((targets["xz"], targets["yz"], 0.0))
                                )
                            )
                            / target_scale,
                        )
                        s3_recovered_physical_energy += (
                            0.5
                            * determinant
                            * float(weight)
                            * float(
                                recovered_strains[point_index]
                                @ recovered_resultants[point_index]
                            )
                        )
                    maximum_s3_bubble_shear_operator_mean_norm = max(
                        maximum_s3_bubble_shear_operator_mean_norm,
                        float(np.linalg.norm(shear_operator_mean)),
                    )

                    alternate_local = rotation_only_shear[
                        np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
                    ]
                    alternate_recovery = element.compute_stresses(
                        model.mesh,
                        alternate_local,
                        material,
                        return_global=True,
                    )
                    alternate_components = _recovered_components(
                        alternate_recovery,
                        "shear",
                    )
                    for component, values in alternate_components.items():
                        maximum_s3_kinematic_decomposition_stress_residual = max(
                            maximum_s3_kinematic_decomposition_stress_residual,
                            float(np.max(np.abs(values - recovered[component]))) / target_scale,
                        )
                    gamma_scale = max(
                        float(
                            np.linalg.norm(
                                (float(patch["gamma_xz"]), float(patch["gamma_yz"]))
                            )
                        ),
                        np.finfo(float).tiny,
                    )
                    maximum_s3_kinematic_decomposition_bubble_residual = max(
                        maximum_s3_kinematic_decomposition_bubble_residual,
                        float(
                            np.linalg.norm(
                                np.asarray(
                                    alternate_recovery["bubble_rotations"], dtype=float
                                )
                                - bubble
                            )
                        )
                        / gamma_scale,
                    )
            integration_point_count[kind] += int(next(iter(recovered.values())).size)
            for component, values in recovered.items():
                topology_error[kind] = max(
                    topology_error[kind],
                    float(np.max(np.abs(values - targets[component])) / target_scale),
                )
        internal = np.asarray(stiffness @ displacement, dtype=float)
        force_residual, moment_residual, force_resultant, moment_resultant = _resultant_residual(
            model, internal
        )
        global_work = float(displacement @ internal)
        work_residual = abs(global_work - element_work) / max(abs(global_work), abs(element_work), 1.0)
        denominator = max(abs(energies["total"]), np.finfo(float).tiny)
        expected_energy = _expected_patch_energy(
            material,
            thickness,
            area,
            patch_name,
            patch,
            targets,
        )
        s3_fraction = float(built.record["s3_area_fraction_percent"]) / 100.0
        expected_by_topology = {
            "Q4": (1.0 - s3_fraction) * expected_energy,
            "S3": s3_fraction * expected_energy,
        }
        observed_by_topology = {
            "Q4": energies["q4_physical"],
            "S3": energies["s3_physical"],
        }
        topology_energy_residual = {
            kind: abs(observed_by_topology[kind] - expected_by_topology[kind])
            / max(abs(expected_by_topology[kind]), np.finfo(float).tiny)
            for kind in ("Q4", "S3")
        }
        interpretation = {
            "membrane": "VALID_CONSTANT_MEMBRANE_STRAIN_PATCH",
            "bending": "VALID_CONSTANT_CURVATURE_PATCH_WITH_COMPATIBLE_QUADRATIC_W_NODAL_TRACE",
            "shear": "NONCLASSIFYING_AFFINE_TRANSVERSE_SHEAR_TRACE_DIAGNOSTIC",
        }[patch_name]
        patch_result = {
            "equilibrium": {
                "force_residual": force_residual,
                "force_resultant": force_resultant,
                "moment_residual": moment_residual,
                "moment_resultant": moment_resultant,
            },
            "integration_point_count": integration_point_count,
            "interpretation": interpretation,
            "maximum_s3_bubble_rotation_norm": maximum_s3_bubble_rotation_norm,
            "patch_residual": max(topology_error.values()),
            "pl_participation": {
                "Q4_PL": energies["q4_pl"] / denominator,
                "Q4_RESIDUAL_HOURGLASS": energies["q4_residual_hourglass"] / denominator,
                "S3_PL": energies["s3_pl"] / denominator,
            },
            "target_global_stress_pa": targets,
            "topology_energy_patch_residual": topology_energy_residual,
            "topology_patch_residual": topology_error,
            "work": {
                "assembled_internal_work_j": global_work,
                "element_internal_work_j": element_work,
                "expected_continuum_physical_energy_j": expected_energy,
                "physical_energy_j": energies["physical"],
                "physical_energy_patch_residual": abs(energies["physical"] - expected_energy)
                / max(abs(expected_energy), np.finfo(float).tiny),
                "total_energy_j": energies["total"],
                "work_residual": work_residual,
            },
        }
        if patch_name == "shear":
            patch_result["diagnostic_classification"] = (
                "NONCLASSIFYING_NOT_THE_PUBLISHED_FORCE_LOADED_PATCH"
            )
            patch_result["s3_bubble_coupling"] = {
                "cause": (
                    "HIERARCHICAL_BUBBLE_SCHUR_RELAXATION_AFTER_AN_EXACT_"
                    "UNCONDENSED_ASSUMED_SHEAR_TRACE"
                ),
                "kinematic_decomposition_bubble_residual": (
                    maximum_s3_kinematic_decomposition_bubble_residual
                ),
                "kinematic_decomposition_stress_residual": (
                    maximum_s3_kinematic_decomposition_stress_residual
                ),
                "maximum_equilibrated_bubble_residual": (
                    maximum_s3_bubble_equilibrium_residual
                ),
                "maximum_force_coupling_ratio": (
                    maximum_s3_bubble_force_coupling_ratio
                ),
                "maximum_mean_shear_operator_frobenius": (
                    maximum_s3_bubble_shear_operator_mean_norm
                ),
                "relaxation_energy_j": s3_bubble_relaxation_energy,
                "recovery_vs_condensed_stiffness_energy_residual": abs(
                    s3_recovered_physical_energy - energies["s3_physical"]
                )
                / max(
                    abs(s3_recovered_physical_energy),
                    abs(energies["s3_physical"]),
                    np.finfo(float).tiny,
                ),
                "uncondensed_trace_stress_residual": (
                    maximum_s3_uncondensed_trace_stress_residual
                ),
            }
        results[patch_name] = patch_result
    return results


def authorities_float(value: object) -> float:
    """Decode exact binary64 tokens used only inside model-input descriptors."""

    if isinstance(value, str) and (value.startswith("0x") or value.startswith("-0x")):
        return float.fromhex(value)
    return float(value)


def _force_loaded_in_plane_shear_patch_observable(
    authorities: CampaignAuthorities,
    built: BuiltCase,
    stiffness: sparse.csr_matrix,
) -> dict[str, Any]:
    """Execute the boundary-point-force constant-stress shear protocol.

    The published shell patch-test protocol uses only the restraints needed to
    remove rigid motion and applies nodal point forces on the boundary that
    correspond to the requested constant stress.  Here the stress state is
    constant *in-plane* shear.  It is deliberately reported separately from
    the affine transverse-shear trace diagnostic.
    """

    from anysolver.assembly import solve_linear
    from anysolver.boundary import FixedSupport, LoadCase
    from anysolver.matrix_assembly import assemble_load_vector

    patch_built = build_case_model(authorities, built.case_spec)
    model = patch_built.model
    material = model.get_material(str(patch_built.model_input_descriptor["material"]["name"]))
    thickness = authorities_float(patch_built.model_input_descriptor["section"]["thickness"])
    gamma_xy = authorities_float(
        patch_built.model_input_descriptor["patches"]["membrane"]["gamma_xy"]
    )
    target_xy = float(material.shear_modulus) * gamma_xy
    target_stress = {"xx": 0.0, "xy": target_xy, "yy": 0.0}

    origin_nodes = [
        node
        for node in model.mesh.nodes.values()
        if tuple(float(value) for value in node.coords()) == (0.0, 0.0, 0.0)
    ]
    if len(origin_nodes) != 1:
        raise RuntimeError("force-loaded shear patch requires exactly one origin node")
    origin = origin_nodes[0]
    model.boundary_conditions = [
        FixedSupport("minimal_origin_rigid_restraint", [int(origin.id)])
    ]
    model.constraint_equations = []
    model.load_cases = []

    boundary_load = LoadCase("constant_in_plane_shear_boundary_point_forces")
    edge_definitions = (
        ("left", 0, 0.0, 1, np.asarray((0.0, -target_xy, 0.0))),
        ("right", 0, 1.0, 1, np.asarray((0.0, target_xy, 0.0))),
        ("bottom", 1, 0.0, 0, np.asarray((-target_xy, 0.0, 0.0))),
        ("top", 1, 1.0, 0, np.asarray((target_xy, 0.0, 0.0))),
    )
    edge_resultants: dict[str, list[float]] = {}
    expected_edge_nodes = int(patch_built.record["level"]) + 1
    for edge_name, fixed_axis, fixed_value, tangent_axis, traction in edge_definitions:
        edge_nodes = sorted(
            (
                node
                for node in model.mesh.nodes.values()
                if float(node.coords()[fixed_axis]) == fixed_value
            ),
            key=lambda node: (float(node.coords()[tangent_axis]), int(node.id)),
        )
        if len(edge_nodes) != expected_edge_nodes:
            raise RuntimeError(
                f"force-loaded shear edge {edge_name!r} has {len(edge_nodes)} nodes, "
                f"expected {expected_edge_nodes}"
            )
        resultant = np.zeros(3, dtype=float)
        for first, second in zip(edge_nodes[:-1], edge_nodes[1:]):
            edge_length = float(
                np.linalg.norm(np.asarray(second.coords()) - np.asarray(first.coords()))
            )
            nodal_force = 0.5 * thickness * edge_length * traction
            boundary_load.add_nodal_load(int(first.id), forces=nodal_force)
            boundary_load.add_nodal_load(int(second.id), forces=nodal_force)
            resultant += 2.0 * nodal_force
        edge_resultants[edge_name] = [float(value) for value in resultant]
    model.add_load_case(boundary_load)

    displacement, solver_info = solve_linear(
        model,
        boundary_load,
        constraint_mode="transformation",
    )
    status = str((solver_info.get("convergence_info") or {}).get("status", "unknown"))
    if status != "converged":
        raise RuntimeError(
            f"force-loaded in-plane shear production solve ended with status {status!r}"
        )
    external, _load_info = assemble_load_vector(model, boundary_load)
    internal = np.asarray(stiffness @ displacement, dtype=float)
    residual = internal - external
    fixed_dofs = np.asarray(origin.dofs, dtype=np.intp)
    free_dofs = np.setdiff1d(np.arange(stiffness.shape[0]), fixed_dofs)
    free_residual = float(
        np.linalg.norm(residual[free_dofs]) / max(float(np.linalg.norm(external)), 1.0)
    )
    support = np.zeros_like(residual)
    support[fixed_dofs] = residual[fixed_dofs]
    balanced = external + support
    force_residual, moment_residual, force_resultant, moment_resultant = _resultant_residual(
        model,
        balanced,
    )

    exact_displacement = np.zeros_like(displacement)
    for node in model.mesh.nodes.values():
        x, y, _z = node.coords()
        exact_displacement[node.dofs[0]] = 0.5 * gamma_xy * y
        exact_displacement[node.dofs[1]] = 0.5 * gamma_xy * x
    exact_displacement_residual = float(
        np.linalg.norm(displacement - exact_displacement)
        / max(float(np.linalg.norm(exact_displacement)), np.finfo(float).tiny)
    )

    topology_error = {"Q4": 0.0, "S3": 0.0}
    integration_point_count = {"Q4": 0, "S3": 0}
    energies = {
        "q4_pl": 0.0,
        "q4_residual_hourglass": 0.0,
        "s3_pl": 0.0,
        "total": 0.0,
    }
    target_scale = max(abs(target_xy), 1.0)
    for element_id, element in model.mesh.elements.items():
        kind = patch_built.element_kinds[int(element_id)]
        mapping = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
        local_displacement = displacement[mapping]
        components = element.compute_stiffness_components(model.mesh, material)
        total_energy = 0.5 * float(
            local_displacement @ np.asarray(components["total"]) @ local_displacement
        )
        energies["total"] += total_energy
        if kind == "S3":
            energies["s3_pl"] += 0.5 * float(
                local_displacement @ np.asarray(components["pl"]) @ local_displacement
            )
        else:
            energies["q4_pl"] += 0.5 * float(
                local_displacement @ np.asarray(components["pl"]) @ local_displacement
            )
            energies["q4_residual_hourglass"] += 0.5 * float(
                local_displacement @ np.asarray(components["hourglass"]) @ local_displacement
            )
        recovery = element.compute_stresses(
            model.mesh,
            local_displacement,
            material,
            return_global=True,
        )
        recovered = _recovered_components(recovery, "membrane")
        integration_point_count[kind] += int(next(iter(recovered.values())).size)
        for component, values in recovered.items():
            topology_error[kind] = max(
                topology_error[kind],
                float(np.max(np.abs(values - target_stress[component]))) / target_scale,
            )

    internal_work = float(displacement @ internal)
    external_work = float(displacement @ external)
    expected_work = thickness * target_xy * gamma_xy
    denominator = max(abs(energies["total"]), np.finfo(float).tiny)
    applied = np.asarray(external).reshape(model.mesh.num_nodes, 6).sum(axis=0)
    reaction = np.asarray(support).reshape(model.mesh.num_nodes, 6).sum(axis=0)
    return {
        "action_reaction_residual": max(force_residual, moment_residual),
        "applied_nodal_resultant": [float(value) for value in applied],
        "boundary_loaded_node_count": len(boundary_load.nodal_loads),
        "boundary_traction_resultants": edge_resultants,
        "classification": "SMOKE_DIAGNOSTIC_NOT_FORMAL_GATE",
        "edge_work_residual": abs(internal_work - external_work)
        / max(abs(internal_work), abs(external_work), 1.0),
        "exact_affine_solution_relative_residual": exact_displacement_residual,
        "expected_constant_stress_work_j": expected_work,
        "force_residual": free_residual,
        "integration_point_count": integration_point_count,
        "interpretation": "VALID_FORCE_LOADED_CONSTANT_IN_PLANE_SHEAR_PATCH",
        "moment_residual": moment_residual,
        "net_force_resultant": force_resultant,
        "net_moment_resultant": moment_resultant,
        "patch_residual": max(topology_error.values()),
        "pl_participation": {
            "Q4_PL": energies["q4_pl"] / denominator,
            "Q4_RESIDUAL_HOURGLASS": energies["q4_residual_hourglass"] / denominator,
            "S3_PL": energies["s3_pl"] / denominator,
        },
        "protocol": (
            "MINIMAL_RIGID_RESTRAINT_PLUS_ANALYTIC_BOUNDARY_POINT_FORCES_"
            "FOR_CONSTANT_STRESS"
        ),
        "solver_status": status,
        "support_dof_count": len(fixed_dofs),
        "support_node_id": int(origin.id),
        "support_reaction_resultant": [float(value) for value in reaction],
        "target_global_stress_pa": target_stress,
        "topology_patch_residual": topology_error,
        "work": {
            "assembled_internal_work_j": internal_work,
            "boundary_external_work_j": external_work,
            "continuum_work_residual": abs(internal_work - expected_work)
            / max(abs(internal_work), abs(expected_work), np.finfo(float).tiny),
        },
    }


def _static_probe_observables(built: BuiltCase, stiffness: sparse.csr_matrix) -> dict[str, Any]:
    from anysolver.assembly import solve_linear
    from anysolver.matrix_assembly import assemble_load_vector

    if built.load_case is None:
        raise RuntimeError("static probe was not constructed")
    displacement, solver_info = solve_linear(
        built.model,
        built.load_case,
        constraint_mode="transformation",
    )
    status = str((solver_info.get("convergence_info") or {}).get("status", "unknown"))
    if status != "converged":
        raise RuntimeError(f"production linear solver ended with status {status!r}")
    external, _load_info = assemble_load_vector(built.model, built.load_case)
    residual = np.asarray(stiffness @ displacement - external, dtype=float)
    free_dofs = np.asarray(built.model.mesh.dof_manager.get_free_dofs(), dtype=np.intp)
    free_residual = float(np.linalg.norm(residual[free_dofs]) / max(np.linalg.norm(external), 1.0))
    support = residual.copy()
    support[free_dofs] = 0.0
    balanced = external + support
    force_residual, moment_residual, force_resultant, moment_resultant = _resultant_residual(
        built.model, balanced
    )
    work_internal = float(displacement @ (stiffness @ displacement))
    work_external = float(displacement @ external)
    edge_work_residual = abs(work_internal - work_external) / max(
        abs(work_internal), abs(work_external), 1.0
    )
    applied = np.asarray(external).reshape(built.model.mesh.num_nodes, 6).sum(axis=0)
    reaction = np.asarray(support).reshape(built.model.mesh.num_nodes, 6).sum(axis=0)
    return {
        "action_reaction_residual": max(force_residual, moment_residual),
        "applied_nodal_resultant": [float(value) for value in applied],
        "edge_work_residual": edge_work_residual,
        "external_work_j": work_external,
        "force_residual": free_residual,
        "internal_work_j": work_internal,
        "maximum_abs_displacement": float(np.max(np.abs(displacement))),
        "moment_residual": moment_residual,
        "net_force_resultant": force_resultant,
        "net_moment_resultant": moment_resultant,
        "solver_status": status,
        "support_reaction_resultant": [float(value) for value in reaction],
    }


def _covariance_observable(
    authorities: CampaignAuthorities,
    built: BuiltCase,
    stiffness: sparse.csr_matrix,
) -> dict[str, Any]:
    from anysolver.matrix_assembly import assemble_stiffness_matrix

    rotation = np.asarray(((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
    rotated = build_case_model(
        authorities,
        built.case_spec,
        rotation=rotation,
        include_auxiliary_inputs=False,
    )
    rotated_stiffness, _info = assemble_stiffness_matrix(rotated.model)
    block = np.zeros((6, 6), dtype=float)
    block[:3, :3] = rotation
    block[3:, 3:] = rotation
    transform = sparse.kron(
        sparse.eye(built.model.mesh.num_nodes, format="csr"),
        sparse.csr_matrix(block),
        format="csr",
    )
    expected = (transform @ stiffness @ transform.T).tocsr()
    difference = (rotated_stiffness - expected).tocsr()
    difference.eliminate_zeros()
    return {
        "proper_rotation": [[float(value) for value in row] for row in rotation],
        "relative_frobenius_residual": _relative_sparse_residual(difference, expected),
        "rotated_owner_normal": [float(value) for value in rotation @ np.asarray((0.0, 0.0, 1.0))],
        "rotated_topology_sha256": rotated.topology_sha256,
    }


def _finite_tree(value: object, label: str = "result") -> None:
    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise RuntimeError(f"{label} contains nonfinite float")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            _finite_tree(item, f"{label}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _finite_tree(item, f"{label}[{index}]")
        return
    raise RuntimeError(f"{label} contains unsupported value type {type(value).__name__}")


def _run_case(authorities: CampaignAuthorities, case_spec: Mapping[str, Any]) -> dict[str, Any]:
    from anysolver.elements import DEFAULT_S3_FORMULATION
    from anysolver.matrix_assembly import assemble_stiffness_matrix

    if DEFAULT_S3_FORMULATION != authorities.input_payload["factories"]["default_s3_expected"]:
        raise CampaignInputError("production S3 default changed; smoke input forbids implicit activation")
    built = build_case_model(authorities, case_spec)
    stiffness, assembly_info = assemble_stiffness_matrix(built.model)
    symmetry = _relative_sparse_residual(stiffness - stiffness.T, stiffness)
    static_probe = _static_probe_observables(built, stiffness)
    patches = _patch_observables(built, stiffness)
    force_loaded_in_plane_shear_patch = _force_loaded_in_plane_shear_patch_observable(
        authorities,
        built,
        stiffness,
    )
    covariance = _covariance_observable(authorities, built, stiffness)
    observed_factory_identities: dict[str, dict[str, str]] = {}
    for element_id, kind in built.element_kinds.items():
        if kind in observed_factory_identities:
            continue
        element = built.model.mesh.elements[element_id]
        observed_factory_identities[kind] = {
            "class_module": type(element).__module__,
            "class_name": type(element).__name__,
            "formulation_id": str(element.formulation_id),
        }
    result = {
        "assembly": {
            "assembled_element_count": int(assembly_info["num_elements"]),
            "matrix_nnz": int(stiffness.nnz),
            "total_dofs": int(stiffness.shape[0]),
        },
        "case_id": str(case_spec["case_id"]),
        "classification": CLASSIFICATION,
        "connectivity_sha256": built.topology_sha256,
        "covariance": covariance,
        "element_counts": {
            "Q4": int(built.record["q4_element_count"]),
            "S3": int(built.record["s3_element_count"]),
        },
        "factory_identities": observed_factory_identities,
        "force_loaded_in_plane_shear_patch": force_loaded_in_plane_shear_patch,
        "level": int(built.record["level"]),
        "model_input_sha256": built.model_input_sha256,
        "node_count": int(built.record["node_count"]),
        "patches": patches,
        "s3_area_fraction_percent": int(built.record["s3_area_fraction_percent"]),
        "static_probe": static_probe,
        "symmetry_relative_frobenius_residual": symmetry,
        "terminal_status": TERMINAL_RECORDED,
    }
    _finite_tree(result)
    return result


def run_all_cases(
    authorities: CampaignAuthorities,
    *,
    case_ids: Sequence[str] | None = None,
) -> list[dict[str, Any]]:
    requested = None if case_ids is None else set(case_ids)
    known = {str(case["case_id"]) for case in authorities.input_payload["cases"]}
    if requested is not None:
        unknown = requested - known
        if unknown:
            raise CampaignInputError(f"unknown selected case IDs: {sorted(unknown)}")
    launched = [
        case
        for case in authorities.input_payload["cases"]
        if requested is None or str(case["case_id"]) in requested
    ]
    if not launched:
        raise CampaignInputError("case selection launched no cases")
    terminal: list[dict[str, Any]] = []
    for case in launched:
        try:
            terminal.append(_run_case(authorities, case))
        except Exception as exc:  # terminal evidence must survive a mechanics failure
            terminal.append(
                {
                    "case_id": str(case["case_id"]),
                    "classification": CLASSIFICATION,
                    "failure": {
                        "exception_type": type(exc).__name__,
                        "message": str(exc),
                    },
                    "terminal_status": TERMINAL_FAILED,
                }
            )
    if len(terminal) != len(launched) or any(
        result.get("terminal_status") not in {TERMINAL_RECORDED, TERMINAL_FAILED}
        for result in terminal
    ):
        raise RuntimeError("not every launched smoke case reached a terminal state")
    return terminal


def _aggregate_documents(
    authorities: CampaignAuthorities,
    terminal_cases: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    gate_names = sorted(authorities.contract["acceptance_gates"])
    failures = [case["case_id"] for case in terminal_cases if case["terminal_status"] == TERMINAL_FAILED]
    result = {
        "all_launched_cases_terminal": True,
        "case_count": len(terminal_cases),
        "cases": list(terminal_cases),
        "classification": CLASSIFICATION,
        "formal_gate_status": {name: "UNEXECUTED" for name in gate_names},
        "mechanics_scope": {
            "bending_patch": "EXECUTED_VALID_CONSTANT_CURVATURE_PATCH_WITH_COMPATIBLE_QUADRATIC_W_NODAL_TRACE",
            "force_loaded_in_plane_shear_patch": (
                "EXECUTED_VALID_CONSTANT_STRESS_PATCH_USING_ANALYTIC_BOUNDARY_POINT_FORCES"
            ),
            "membrane_patch": "EXECUTED_VALID_CONSTANT_MEMBRANE_STRAIN_PATCH",
            "transverse_shear_affine_trace": (
                "EXECUTED_NONCLASSIFYING_DIAGNOSTIC: THE_UNCONDENSED_ASSUMED_"
                "SHEAR_TRACE_IS_EXACT; HIERARCHICAL_BUBBLE_SCHUR_RELAXATION_"
                "CHANGES_THE_CONDENSED_TRACE"
            ),
            "transverse_shear_force_loaded_patch": (
                "UNEXECUTED_NO_FROZEN_CONTINUUM_LOAD_AND_RESTRAINT_"
                "SPECIFICATION_IN_THE_SMOKE_INPUT"
            ),
        },
        "qualification_claim": "NONE",
        "qualification_decision": "NO_QUALIFICATION_OR_DEFAULT_ACTIVATION",
        "schema": RESULT_SCHEMA,
        "smoke_failure_case_ids": failures,
        "smoke_terminal": "SMOKE_EXECUTION_FAILED" if failures else "SMOKE_OBSERVATIONS_RECORDED",
        "unexecuted_contract_gates": gate_names,
    }
    from anysolver import __version__ as anysolver_version
    from anysolver.elements import DEFAULT_Q4_FORMULATION, DEFAULT_S3_FORMULATION
    import scipy

    provenance = {
        "authority": {
            "connectivity_manifest": {
                "bytes": len(authorities.manifest_raw),
                "path": "docs/reference_cases/e4_pl_s3_mixed_mesh_connectivity_manifest.json",
                "sha256": _sha256(authorities.manifest_raw),
            },
            "qualification_contract": {
                "bytes": len(authorities.contract_raw),
                "path": "docs/reference_cases/e4_pl_s3_mixed_mesh_qualification_contract.json",
                "sha256": _sha256(authorities.contract_raw),
            },
            "runner_input": {
                "bytes": len(authorities.input_raw),
                "path": "docs/reference_cases/e4_pl_s3_mixed_mesh_smoke_input.json",
                "sha256": _sha256(authorities.input_raw),
            },
            "runner_schema": {
                "bytes": INPUT_SCHEMA_PATH.stat().st_size,
                "path": "docs/reference_cases/e4_pl_s3_mixed_mesh_runner_schema.json",
                "sha256": _sha256(INPUT_SCHEMA_PATH.read_bytes()),
            },
            "runner_source": {
                "bytes": Path(__file__).stat().st_size,
                "path": "docs/reference_cases/e4_pl_s3_mixed_mesh_qualification_runner.py",
                "sha256": _sha256(Path(__file__).read_bytes()),
            },
        },
        "case_terminals": [
            {"case_id": case["case_id"], "terminal_status": case["terminal_status"]}
            for case in terminal_cases
        ],
        "classification": CLASSIFICATION,
        "default_activation": {
            "q4_default": str(DEFAULT_Q4_FORMULATION),
            "s3_default": str(DEFAULT_S3_FORMULATION),
            "s3_qualified_default_activated": False,
        },
        "executor": EXECUTOR_ID,
        "future_executor_slots": list(FUTURE_EXECUTOR_IDS),
        "numerical_runtime": {
            "anysolver": str(anysolver_version),
            "numpy": str(np.__version__),
            "python": ".".join(str(value) for value in sys.version_info[:3]),
            "scipy": str(scipy.__version__),
            "threads_per_process": 1,
        },
        "schema": PROVENANCE_SCHEMA,
    }
    _finite_tree(result)
    _finite_tree(provenance)
    return result, provenance


def _atomic_write(path: Path, payload: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_bytes(payload)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def execute_to_paths(
    input_path: Path,
    result_path: Path,
    provenance_path: Path,
    *,
    case_ids: Sequence[str] | None = None,
) -> int:
    if Path(result_path).resolve() == Path(provenance_path).resolve():
        raise CampaignInputError("result and provenance paths must be distinct")
    authorities = load_authorities(Path(input_path))
    terminal_cases = run_all_cases(authorities, case_ids=case_ids)
    # Aggregate construction is deliberately after all cases are terminal.
    result, provenance = _aggregate_documents(authorities, terminal_cases)
    result_bytes = _canonical_bytes(result)
    provenance_bytes = _canonical_bytes(provenance)
    _atomic_write(Path(result_path), result_bytes)
    _atomic_write(Path(provenance_path), provenance_bytes)
    return 1 if result["smoke_failure_case_ids"] else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--provenance", type=Path)
    parser.add_argument("--case-id", action="append", dest="case_ids")
    parser.add_argument("--check-input", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.check_input:
            if args.result is not None or args.provenance is not None or args.case_ids:
                parser.error("--check-input cannot be combined with outputs or --case-id")
            load_authorities(args.input)
            return 0
        if args.result is None or args.provenance is None:
            parser.error("execution requires both --result and --provenance")
        return execute_to_paths(
            args.input,
            args.result,
            args.provenance,
            case_ids=args.case_ids,
        )
    except CampaignInputError as exc:
        print(f"mixed-mesh campaign input rejected: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
