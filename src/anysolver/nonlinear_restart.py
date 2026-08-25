"""Canonical checkpoints for nonlinear static continuation.

The checkpoint is deliberately solver-owned.  Element state serializers are
responsible for the contents of one committed element state, while this module
binds those states to the complete model, load/control contract, committed
global displacement, activity/deletion state, and continuation path.

Only canonical JSON is accepted at the serialized boundary.  A mapping may be
passed directly by an in-process caller, but it is normalized and its complete
integrity hash is verified in exactly the same way as serialized input.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import fields, is_dataclass
from enum import Enum
from typing import Any, Dict, Mapping, NamedTuple, Optional, Sequence

import numpy as np


NONLINEAR_CHECKPOINT_SCHEMA = "ANYSOLVER_NONLINEAR_CHECKPOINT_V1"
NONLINEAR_CHECKPOINT_VERSION = 1
NONLINEAR_CHECKPOINT_INTEGRITY_ID = "SHA256_CANONICAL_JSON_EXCLUDING_SELF_V1"
_CHECKPOINT_HASH_KEY = "checkpoint_sha256"
_CHECKPOINT_KEYS = {
    "schema",
    "version",
    "integrity_id",
    "analysis_kind",
    "model_fingerprint",
    "analysis_fingerprint",
    "total_dofs",
    "displacements",
    "element_states",
    "deleted_element_ids",
    "activity_state",
    "path_state",
    _CHECKPOINT_HASH_KEY,
}


class NonlinearCheckpointError(ValueError):
    """A checkpoint is malformed, noncanonical, or incompatible."""


class ValidatedNonlinearCheckpoint(NamedTuple):
    """Owned, model-validated checkpoint values ready for a solver."""

    payload: Dict[str, Any]
    displacements: np.ndarray
    element_states: Dict[int, Any]
    deleted_element_ids: set[int]
    activity: Optional[Any]
    path_state: Dict[str, Any]


def _class_id(value: Any) -> str:
    cls = type(value)
    return f"{cls.__module__}.{cls.__qualname__}"


def _normalize_json(value: Any, *, path: str = "$") -> Any:
    """Return an owned canonical-JSON value and reject ambiguous inputs."""

    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, (int, np.integer)) and not isinstance(value, (bool, np.bool_)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        result = float(value)
        if not math.isfinite(result):
            raise NonlinearCheckpointError(f"{path} contains a nonfinite value")
        return 0.0 if result == 0.0 else result
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.ndarray):
        if value.dtype.kind in {"O", "V", "S", "U"}:
            return _normalize_json(value.tolist(), path=path)
        if value.dtype.kind in {"f", "c"} and not np.all(np.isfinite(value)):
            raise NonlinearCheckpointError(f"{path} contains a nonfinite array value")
        if value.dtype.kind == "c":
            raise NonlinearCheckpointError(f"{path} contains complex values")
        return _normalize_json(value.tolist(), path=path)
    if isinstance(value, Enum):
        return _normalize_json(value.value, path=path)
    if isinstance(value, Mapping):
        result: Dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise NonlinearCheckpointError(
                    f"{path} contains non-string mapping key {key!r}"
                )
            if key in result:
                raise NonlinearCheckpointError(f"{path} contains duplicate key {key!r}")
            result[key] = _normalize_json(item, path=f"{path}.{key}")
        return result
    if isinstance(value, (list, tuple)):
        return [
            _normalize_json(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _normalize_json(
                getattr(value, item.name), path=f"{path}.{item.name}"
            )
            for item in fields(value)
            if not item.name.startswith("_")
        }
    raise NonlinearCheckpointError(
        f"{path} contains unsupported value type {_class_id(value)}"
    )


def canonical_checkpoint_json_bytes(value: Any) -> bytes:
    """Encode one value as strict deterministic UTF-8 JSON plus LF."""

    normalized = _normalize_json(value)
    try:
        text = json.dumps(
            normalized,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise NonlinearCheckpointError("checkpoint is not canonical-JSON encodable") from exc
    return (text + "\n").encode("utf-8")


def _strict_json_loads(raw: bytes | bytearray | memoryview | str) -> Any:
    if isinstance(raw, str):
        encoded = raw.encode("utf-8")
    elif isinstance(raw, (bytes, bytearray, memoryview)):
        encoded = bytes(raw)
    else:
        raise TypeError("serialized checkpoint must be bytes or str")

    def reject_duplicate(pairs: Sequence[tuple[str, Any]]) -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise NonlinearCheckpointError(f"duplicate JSON key {key!r}")
            result[key] = value
        return result

    def reject_constant(token: str) -> Any:
        raise NonlinearCheckpointError(f"nonfinite JSON constant {token!r}")

    try:
        value = json.loads(
            encoded.decode("utf-8"),
            object_pairs_hook=reject_duplicate,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NonlinearCheckpointError("checkpoint is not valid UTF-8 JSON") from exc
    if canonical_checkpoint_json_bytes(value) != encoded:
        raise NonlinearCheckpointError("serialized checkpoint is not canonical JSON")
    return value


def _sha256(value: Any) -> str:
    return hashlib.sha256(canonical_checkpoint_json_bytes(value)).hexdigest().upper()


def _object_payload(value: Any, *, path: str) -> Dict[str, Any]:
    """Describe one model object without private caches or object identity."""

    payload: Dict[str, Any] = {"class": _class_id(value)}
    public: Dict[str, Any] = {}
    if is_dataclass(value) and not isinstance(value, type):
        for item in fields(value):
            if not item.name.startswith("_"):
                public[item.name] = getattr(value, item.name)
    else:
        try:
            values = vars(value)
        except TypeError:
            values = {}
        for name, item in values.items():
            if name.startswith("_") or callable(item):
                continue
            public[name] = item
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        try:
            public["serialized"] = to_dict()
        except TypeError:
            pass
    if not public:
        raise NonlinearCheckpointError(
            f"{path} has no deterministic public configuration descriptor"
        )
    payload["configuration"] = _normalize_json(public, path=path)
    return payload


def load_case_descriptor(load_case: Any) -> Optional[Dict[str, Any]]:
    """Return the exact deterministic identity of a load case."""

    if load_case is None:
        return None

    def records(values: Any, value_name: str) -> list[Dict[str, Any]]:
        if not isinstance(values, Mapping):
            raise NonlinearCheckpointError(
                f"load case {value_name} must be a mapping"
            )
        return [
            {
                "id": int(key),
                value_name: _normalize_json(value, path=f"load_case.{value_name}[{key}]")
            }
            for key, value in sorted(values.items(), key=lambda item: int(item[0]))
        ]

    return {
        "class": _class_id(load_case),
        "name": str(getattr(load_case, "name", "")),
        "nodal_loads": records(getattr(load_case, "nodal_loads", {}), "load"),
        "element_loads": records(getattr(load_case, "element_loads", {}), "load"),
        "pressure_loads": records(getattr(load_case, "pressure_loads", {}), "pressure"),
        "added_node_masses": records(
            getattr(load_case, "added_node_masses", {}), "mass"
        ),
        "gravity": _normalize_json(getattr(load_case, "gravity", None), path="load_case.gravity"),
        "follower_pressure": bool(getattr(load_case, "follower_pressure", False)),
    }


def model_configuration_descriptor(model: Any) -> Dict[str, Any]:
    """Describe mechanics-affecting model configuration, excluding history."""

    mesh = getattr(model, "mesh", None)
    nodes = getattr(mesh, "nodes", None)
    elements = getattr(mesh, "elements", None)
    materials = getattr(model, "materials", None)
    if not isinstance(nodes, Mapping) or not isinstance(elements, Mapping):
        raise NonlinearCheckpointError("model must expose node and element mappings")
    if not isinstance(materials, Mapping):
        raise NonlinearCheckpointError("model must expose a material mapping")

    node_records = []
    for node_id, node in sorted(nodes.items(), key=lambda item: int(item[0])):
        coords = np.asarray(node.coords(), dtype=np.float64)
        dofs = np.asarray(getattr(node, "dofs", ()), dtype=np.int64)
        if coords.shape != (3,) or not np.all(np.isfinite(coords)):
            raise NonlinearCheckpointError(f"node {node_id} has invalid coordinates")
        node_records.append(
            {"id": int(node_id), "coordinates": coords.tolist(), "dofs": dofs.tolist()}
        )

    element_records = []
    for element_id, element in sorted(elements.items(), key=lambda item: int(item[0])):
        descriptor = _object_payload(element, path=f"model.elements[{element_id}]")
        descriptor["id"] = int(element_id)
        element_records.append(descriptor)

    material_records = []
    for name, material in sorted(materials.items(), key=lambda item: str(item[0])):
        descriptor = _object_payload(material, path=f"model.materials[{name!r}]")
        descriptor["name"] = str(name)
        material_records.append(descriptor)

    boundary_records = [
        _object_payload(item, path=f"model.boundary_conditions[{index}]")
        for index, item in enumerate(getattr(model, "boundary_conditions", ()))
    ]
    constraint_records = [
        _object_payload(item, path=f"model.constraint_equations[{index}]")
        for index, item in enumerate(getattr(model, "constraint_equations", ()))
    ]
    total_dofs = int(getattr(getattr(mesh, "dof_manager", None), "total_dofs", -1))
    if total_dofs < 0:
        raise NonlinearCheckpointError("model has no valid DOF layout")
    return {
        "model_class": _class_id(model),
        "name": str(getattr(model, "name", "")),
        "current_material": str(getattr(model, "current_material", "")),
        "total_dofs": total_dofs,
        "nodes": node_records,
        "elements": element_records,
        "materials": material_records,
        "boundary_conditions": boundary_records,
        "constraint_equations": constraint_records,
        "point_masses": [
            {"node_id": int(key), "mass": float(value)}
            for key, value in sorted(
                getattr(mesh, "point_masses", {}).items(), key=lambda item: int(item[0])
            )
        ],
    }


def model_configuration_fingerprint(model: Any) -> str:
    return _sha256(model_configuration_descriptor(model))


def analysis_configuration_fingerprint(contract: Mapping[str, Any]) -> str:
    return _sha256(_normalize_json(contract, path="analysis_contract"))


def _state_records(element_states: Mapping[int, Any]) -> list[Dict[str, Any]]:
    records: list[Dict[str, Any]] = []
    seen: set[int] = set()
    for raw_id, state in sorted(element_states.items(), key=lambda item: int(item[0])):
        element_id = int(raw_id)
        if element_id in seen:
            raise NonlinearCheckpointError(f"duplicate element state ID {element_id}")
        seen.add(element_id)
        records.append(
            {
                "element_id": element_id,
                "state": _normalize_json(state, path=f"element_states[{element_id}].state"),
            }
        )
    return records


def _checkpoint_without_hash(payload: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: copy.deepcopy(value) for key, value in payload.items() if key != _CHECKPOINT_HASH_KEY}


def create_nonlinear_checkpoint(
    *,
    analysis_kind: str,
    model: Any,
    analysis_contract: Mapping[str, Any],
    displacements: Any,
    element_states: Mapping[int, Any],
    path_state: Mapping[str, Any],
    deleted_element_ids: Sequence[int] = (),
) -> Dict[str, Any]:
    """Create one complete canonical checkpoint from committed solver state."""

    kind = str(analysis_kind)
    if kind not in {"static", "arc_length"}:
        raise NonlinearCheckpointError("analysis_kind must be 'static' or 'arc_length'")
    total_dofs = int(model.mesh.dof_manager.total_dofs)
    displacement = np.asarray(displacements, dtype=np.float64)
    if (
        displacement.ndim != 1
        or displacement.size != total_dofs
        or not np.all(np.isfinite(displacement))
    ):
        raise NonlinearCheckpointError(
            "checkpoint displacement must be the complete finite global vector"
        )
    deleted = sorted(int(value) for value in deleted_element_ids)
    if len(deleted) != len(set(deleted)):
        raise NonlinearCheckpointError("deleted element IDs must be unique")
    activity = getattr(model.mesh, "element_activity", None)
    activity_state = None
    if activity is not None:
        serializer = getattr(activity, "to_restart", None)
        if not callable(serializer):
            raise NonlinearCheckpointError(
                "attached element activity does not expose a restart serializer"
            )
        activity_state = serializer(include_history=True)
    payload: Dict[str, Any] = {
        "schema": NONLINEAR_CHECKPOINT_SCHEMA,
        "version": NONLINEAR_CHECKPOINT_VERSION,
        "integrity_id": NONLINEAR_CHECKPOINT_INTEGRITY_ID,
        "analysis_kind": kind,
        "model_fingerprint": model_configuration_fingerprint(model),
        "analysis_fingerprint": analysis_configuration_fingerprint(analysis_contract),
        "total_dofs": total_dofs,
        "displacements": displacement.tolist(),
        "element_states": _state_records(element_states),
        "deleted_element_ids": deleted,
        "activity_state": _normalize_json(activity_state, path="activity_state"),
        "path_state": _normalize_json(path_state, path="path_state"),
    }
    payload[_CHECKPOINT_HASH_KEY] = _sha256(payload)
    return _normalize_json(payload)


def load_nonlinear_checkpoint(value: Any) -> Dict[str, Any]:
    """Parse and verify one checkpoint without consulting a model."""

    if isinstance(value, (bytes, bytearray, memoryview, str)):
        payload = _strict_json_loads(value)
    elif isinstance(value, Mapping):
        payload = _normalize_json(value, path="checkpoint")
    else:
        raise TypeError("restart_checkpoint must be a mapping, bytes, or str")
    if not isinstance(payload, dict):
        raise NonlinearCheckpointError("checkpoint root must be a JSON object")
    keys = set(payload)
    if keys != _CHECKPOINT_KEYS:
        missing = sorted(_CHECKPOINT_KEYS - keys)
        extra = sorted(keys - _CHECKPOINT_KEYS)
        raise NonlinearCheckpointError(
            f"checkpoint keys are invalid; missing={missing}, extra={extra}"
        )
    if payload["schema"] != NONLINEAR_CHECKPOINT_SCHEMA:
        raise NonlinearCheckpointError("unsupported nonlinear checkpoint schema")
    if payload["version"] != NONLINEAR_CHECKPOINT_VERSION:
        raise NonlinearCheckpointError("unsupported nonlinear checkpoint version")
    if payload["integrity_id"] != NONLINEAR_CHECKPOINT_INTEGRITY_ID:
        raise NonlinearCheckpointError("unsupported nonlinear checkpoint integrity policy")
    claimed = payload[_CHECKPOINT_HASH_KEY]
    if not isinstance(claimed, str) or len(claimed) != 64:
        raise NonlinearCheckpointError("checkpoint SHA-256 is malformed")
    expected = _sha256(_checkpoint_without_hash(payload))
    if claimed != expected:
        raise NonlinearCheckpointError("checkpoint SHA-256 does not match its contents")
    return payload


def validate_nonlinear_checkpoint(
    value: Any,
    *,
    analysis_kind: str,
    model: Any,
    analysis_contract: Mapping[str, Any],
    num_layers: int,
) -> ValidatedNonlinearCheckpoint:
    """Validate a checkpoint completely before any solver assembly."""

    payload = load_nonlinear_checkpoint(value)
    if payload["analysis_kind"] != str(analysis_kind):
        raise NonlinearCheckpointError("checkpoint analysis kind is incompatible")
    if payload["model_fingerprint"] != model_configuration_fingerprint(model):
        raise NonlinearCheckpointError("checkpoint model fingerprint is incompatible")
    if payload["analysis_fingerprint"] != analysis_configuration_fingerprint(analysis_contract):
        raise NonlinearCheckpointError("checkpoint analysis contract is incompatible")
    total_dofs = int(model.mesh.dof_manager.total_dofs)
    if payload["total_dofs"] != total_dofs:
        raise NonlinearCheckpointError("checkpoint DOF count is incompatible")
    displacement = np.asarray(payload["displacements"], dtype=np.float64)
    if (
        displacement.ndim != 1
        or displacement.size != total_dofs
        or not np.all(np.isfinite(displacement))
    ):
        raise NonlinearCheckpointError("checkpoint displacement vector is invalid")

    records = payload["element_states"]
    if not isinstance(records, list):
        raise NonlinearCheckpointError("element_states must be an ordered record list")
    states: Dict[int, Any] = {}
    order: list[int] = []
    model_ids = {int(value) for value in model.mesh.elements}
    for index, record in enumerate(records):
        if not isinstance(record, Mapping) or set(record) != {"element_id", "state"}:
            raise NonlinearCheckpointError(f"element state record {index} is malformed")
        element_id = int(record["element_id"])
        if element_id in states:
            raise NonlinearCheckpointError(f"duplicate element state ID {element_id}")
        if element_id not in model_ids:
            raise NonlinearCheckpointError(
                f"checkpoint state references missing element {element_id}"
            )
        order.append(element_id)
        states[element_id] = copy.deepcopy(record["state"])
    if order != sorted(order):
        raise NonlinearCheckpointError("element state records are not in canonical ID order")

    deleted_raw = payload["deleted_element_ids"]
    if not isinstance(deleted_raw, list):
        raise NonlinearCheckpointError("deleted_element_ids must be a list")
    deleted = [int(value) for value in deleted_raw]
    if deleted != sorted(set(deleted)):
        raise NonlinearCheckpointError("deleted_element_ids must be sorted and unique")
    if not set(deleted).issubset(model_ids):
        raise NonlinearCheckpointError("checkpoint deletion state references missing elements")

    activity_payload = payload["activity_state"]
    current_activity = getattr(model.mesh, "element_activity", None)
    restored_activity = None
    if activity_payload is None:
        if current_activity is not None:
            raise NonlinearCheckpointError(
                "checkpoint has no activity state but the model has an activity manager"
            )
    else:
        from .activity import ElementActivity

        try:
            restored_activity = ElementActivity.from_restart(activity_payload)
        except Exception as exc:
            raise NonlinearCheckpointError("checkpoint activity state is invalid") from exc
        restored_ids = {int(value) for value in restored_activity.element_ids}
        if restored_ids != model_ids:
            raise NonlinearCheckpointError(
                "checkpoint activity IDs differ from the current mesh"
            )
        if current_activity is not None:
            current_ids = {int(value) for value in current_activity.element_ids}
            if current_ids != model_ids or current_activity.policy != restored_activity.policy:
                raise NonlinearCheckpointError(
                    "checkpoint activity policy differs from the current model"
                )

    normalized_states: Dict[int, Any] = {}
    for element_id, state in states.items():
        element = model.mesh.elements[element_id]
        validator = getattr(element, "validate_model_bound_nonlinear_state", None)
        if callable(validator):
            material_name = str(getattr(element, "material_name", model.current_material))
            try:
                material = model.materials[material_name]
                mapping = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
                local_u = displacement[mapping]
                normalized_states[element_id] = validator(
                    model.mesh,
                    material,
                    state,
                    int(num_layers),
                    expected_committed_total_u=local_u,
                )
            except Exception as exc:
                raise NonlinearCheckpointError(
                    f"checkpoint state for element {element_id} is incompatible"
                ) from exc
        else:
            normalized_states[element_id] = copy.deepcopy(state)

    # Reconstructing the node-shared store is the final pre-assembly check. It
    # rejects missing native states and any redundant per-element Q/director
    # copies that disagree at a shared node.
    from .nonlinear_state import create_model_native_rotation_store

    try:
        create_model_native_rotation_store(model, normalized_states, displacement)
    except Exception as exc:
        raise NonlinearCheckpointError(
            "checkpoint node-shared rotation history is inconsistent"
        ) from exc

    path_state = payload["path_state"]
    if not isinstance(path_state, dict):
        raise NonlinearCheckpointError("checkpoint path_state must be a JSON object")
    return ValidatedNonlinearCheckpoint(
        payload=copy.deepcopy(payload),
        displacements=displacement.copy(),
        element_states=copy.deepcopy(normalized_states),
        deleted_element_ids=set(deleted),
        activity=restored_activity,
        path_state=copy.deepcopy(path_state),
    )


__all__ = [
    "NONLINEAR_CHECKPOINT_INTEGRITY_ID",
    "NONLINEAR_CHECKPOINT_SCHEMA",
    "NONLINEAR_CHECKPOINT_VERSION",
    "NonlinearCheckpointError",
    "ValidatedNonlinearCheckpoint",
    "analysis_configuration_fingerprint",
    "canonical_checkpoint_json_bytes",
    "create_nonlinear_checkpoint",
    "load_case_descriptor",
    "load_nonlinear_checkpoint",
    "model_configuration_descriptor",
    "model_configuration_fingerprint",
    "validate_nonlinear_checkpoint",
]
