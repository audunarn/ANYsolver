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

from .current_state_tangent import (
    require_exact_qualified_component_lifecycle_api as _EXACT_QUALIFIED_COMPONENT_LIFECYCLE_GUARD,
)
from .element_capabilities import ElementCapabilityError


NONLINEAR_CHECKPOINT_SCHEMA = "ANYSOLVER_NONLINEAR_CHECKPOINT_V1"
NONLINEAR_CHECKPOINT_VERSION = 1
NONLINEAR_CHECKPOINT_INTEGRITY_ID = "SHA256_CANONICAL_JSON_EXCLUDING_SELF_V1"
QUALIFIED_CHECKPOINT_LIFECYCLE_POLICY_ID = (
    "EXACT_Q4_S3_ACTIVE_OR_DELETED_SEAL_NO_FAILED_DOWNGRADE_V1"
)
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


def _validate_complete_activity_history(activity: Any) -> None:
    """Replay checkpoint activity history exactly from its derived initial state."""

    from .activity import ElementActivity

    history = tuple(activity.history)
    if int(activity.sequence) != len(history) or tuple(
        int(entry.sequence) for entry in history
    ) != tuple(range(1, len(history) + 1)):
        raise NonlinearCheckpointError(
            "checkpoint activity history is incomplete"
        )
    element_ids = np.asarray(activity.element_ids, dtype=np.int64)
    positions = {
        int(element_id): index
        for index, element_id in enumerate(element_ids)
    }
    initial = np.asarray(activity.activity, dtype=np.float64).copy()
    for entry in reversed(history):
        indices = np.asarray(
            [positions[int(element_id)] for element_id in entry.element_ids],
            dtype=np.intp,
        )
        recorded_activity = np.asarray(entry.activity, dtype=np.float64)
        if not np.array_equal(initial[indices], recorded_activity):
            raise NonlinearCheckpointError(
                "checkpoint activity history does not reproduce its final state"
            )
        initial[indices] = np.asarray(
            entry.previous_activity, dtype=np.float64
        )

    replay = ElementActivity(element_ids, initial, policy=activity.policy)
    for entry in history:
        previous = np.asarray(entry.previous_activity, dtype=np.float64)
        next_activity = np.asarray(entry.activity, dtype=np.float64)
        hard_deleted = np.asarray(
            [
                int(element_id) in set(entry.newly_hard_deleted_ids)
                for element_id in entry.element_ids
            ],
            dtype=bool,
        )
        replay.set_activity(
            entry.element_ids,
            next_activity,
            hard_delete=hard_deleted,
            allow_healing=bool(np.any(next_activity > previous)),
            step=entry.step,
            time=entry.time,
            reason=entry.reason,
        )
        if not replay.history or replay.history[-1].to_dict() != entry.to_dict():
            raise NonlinearCheckpointError(
                "checkpoint activity history replay is inconsistent"
            )
    if (
        not np.array_equal(replay.activity, activity.activity)
        or not np.array_equal(
            replay.minimum_activity, activity.minimum_activity
        )
        or not np.array_equal(
            replay.hard_deleted_mask, activity.hard_deleted_mask
        )
        or int(replay.sequence) != int(activity.sequence)
    ):
        raise NonlinearCheckpointError(
            "checkpoint activity history replay differs from its stored state"
        )


def _class_id(value: Any) -> str:
    cls = type(value)
    return f"{cls.__module__}.{cls.__qualname__}"


def _checkpoint_observation_guard(
    exact_guard: Any,
    model: Any,
    *,
    context: str,
) -> None:
    if exact_guard is None:
        return
    try:
        exact_guard(model, context=context)
    except ElementCapabilityError as exc:
        raise NonlinearCheckpointError(
            "checkpoint qualified element API authority changed during input observation"
        ) from exc


def _normalize_json(
    value: Any,
    *,
    path: str = "$",
    _exact_guard: Any = None,
    _guard_model: Any = None,
) -> Any:
    """Return an owned canonical-JSON value and reject ambiguous inputs."""

    guard_arguments = {
        "_exact_guard": _exact_guard,
        "_guard_model": _guard_model,
    }
    if value is None or type(value) in {str, bool}:
        return value
    if isinstance(value, (int, np.integer)) and not isinstance(value, (bool, np.bool_)):
        result = int(value)
        _checkpoint_observation_guard(
            _exact_guard,
            _guard_model,
            context=f"nonlinear checkpoint scalar observation at {path}",
        )
        return result
    if isinstance(value, (float, np.floating)):
        result = float(value)
        _checkpoint_observation_guard(
            _exact_guard,
            _guard_model,
            context=f"nonlinear checkpoint scalar observation at {path}",
        )
        if not math.isfinite(result):
            raise NonlinearCheckpointError(f"{path} contains a nonfinite value")
        return 0.0 if result == 0.0 else result
    if isinstance(value, np.bool_):
        result = bool(value)
        _checkpoint_observation_guard(
            _exact_guard,
            _guard_model,
            context=f"nonlinear checkpoint scalar observation at {path}",
        )
        return result
    if isinstance(value, np.ndarray):
        observed = np.asarray(value)
        _checkpoint_observation_guard(
            _exact_guard,
            _guard_model,
            context=f"nonlinear checkpoint array observation at {path}",
        )
        if observed.dtype.kind in {"O", "V", "S", "U"}:
            return _normalize_json(observed.tolist(), path=path, **guard_arguments)
        if observed.dtype.kind in {"f", "c"} and not np.all(np.isfinite(observed)):
            raise NonlinearCheckpointError(f"{path} contains a nonfinite array value")
        if observed.dtype.kind == "c":
            raise NonlinearCheckpointError(f"{path} contains complex values")
        return _normalize_json(observed.tolist(), path=path, **guard_arguments)
    if isinstance(value, Enum):
        observed = value.value
        _checkpoint_observation_guard(
            _exact_guard,
            _guard_model,
            context=f"nonlinear checkpoint enum observation at {path}",
        )
        return _normalize_json(observed, path=path, **guard_arguments)
    if isinstance(value, Mapping):
        observed_items = tuple(value.items())
        _checkpoint_observation_guard(
            _exact_guard,
            _guard_model,
            context=f"nonlinear checkpoint mapping observation at {path}",
        )
        result: Dict[str, Any] = {}
        for key, item in observed_items:
            if not isinstance(key, str):
                raise NonlinearCheckpointError(
                    f"{path} contains non-string mapping key {key!r}"
                )
            if key in result:
                raise NonlinearCheckpointError(f"{path} contains duplicate key {key!r}")
            result[key] = _normalize_json(
                item,
                path=f"{path}.{key}",
                **guard_arguments,
            )
        return result
    if isinstance(value, (list, tuple)):
        observed_items = tuple(value)
        _checkpoint_observation_guard(
            _exact_guard,
            _guard_model,
            context=f"nonlinear checkpoint sequence observation at {path}",
        )
        return [
            _normalize_json(
                item,
                path=f"{path}[{index}]",
                **guard_arguments,
            )
            for index, item in enumerate(observed_items)
        ]
    if is_dataclass(value) and not isinstance(value, type):
        result: Dict[str, Any] = {}
        for item in fields(value):
            if item.name.startswith("_"):
                continue
            observed = getattr(value, item.name)
            _checkpoint_observation_guard(
                _exact_guard,
                _guard_model,
                context=(
                    "nonlinear checkpoint dataclass observation at "
                    f"{path}.{item.name}"
                ),
            )
            result[item.name] = _normalize_json(
                observed,
                path=f"{path}.{item.name}",
                **guard_arguments,
            )
        return result
    raise NonlinearCheckpointError(
        f"{path} contains unsupported value type {_class_id(value)}"
    )


def canonical_checkpoint_json_bytes(
    value: Any,
    *,
    _exact_guard: Any = None,
    _guard_model: Any = None,
) -> bytes:
    """Encode one value as strict deterministic UTF-8 JSON plus LF."""

    normalized = _normalize_json(
        value,
        _exact_guard=_exact_guard,
        _guard_model=_guard_model,
    )
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


def _sha256(
    value: Any,
    *,
    _exact_guard: Any = None,
    _guard_model: Any = None,
) -> str:
    return hashlib.sha256(
        canonical_checkpoint_json_bytes(
            value,
            _exact_guard=_exact_guard,
            _guard_model=_guard_model,
        )
    ).hexdigest().upper()


def _object_payload(
    value: Any,
    *,
    path: str,
    _exact_guard: Any = None,
    _guard_model: Any = None,
) -> Dict[str, Any]:
    """Describe one model object without private caches or object identity."""

    payload: Dict[str, Any] = {"class": _class_id(value)}
    public: Dict[str, Any] = {}
    if is_dataclass(value) and not isinstance(value, type):
        for item in fields(value):
            if not item.name.startswith("_"):
                observed = getattr(value, item.name)
                _checkpoint_observation_guard(
                    _exact_guard,
                    _guard_model,
                    context=f"nonlinear checkpoint object observation at {path}.{item.name}",
                )
                public[item.name] = observed
    else:
        try:
            values = vars(value)
        except TypeError:
            values = {}
        observed_items = tuple(values.items())
        _checkpoint_observation_guard(
            _exact_guard,
            _guard_model,
            context=f"nonlinear checkpoint object namespace observation at {path}",
        )
        for name, item in observed_items:
            if name.startswith("_") or callable(item):
                continue
            public[name] = item
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        try:
            serialized = to_dict()
            _checkpoint_observation_guard(
                _exact_guard,
                _guard_model,
                context=f"nonlinear checkpoint serializer observation at {path}",
            )
            public["serialized"] = serialized
        except TypeError:
            _checkpoint_observation_guard(
                _exact_guard,
                _guard_model,
                context=f"nonlinear checkpoint serializer observation at {path}",
            )
            pass
    if not public:
        raise NonlinearCheckpointError(
            f"{path} has no deterministic public configuration descriptor"
        )
    payload["configuration"] = _normalize_json(
        public,
        path=path,
        _exact_guard=_exact_guard,
        _guard_model=_guard_model,
    )
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


def model_configuration_descriptor(
    model: Any,
    *,
    _exact_guard: Any = None,
) -> Dict[str, Any]:
    """Describe mechanics-affecting model configuration, excluding history."""

    mesh = getattr(model, "mesh", None)
    nodes = getattr(mesh, "nodes", None)
    elements = getattr(mesh, "elements", None)
    materials = getattr(model, "materials", None)
    if not isinstance(nodes, Mapping) or not isinstance(elements, Mapping):
        raise NonlinearCheckpointError("model must expose node and element mappings")
    if not isinstance(materials, Mapping):
        raise NonlinearCheckpointError("model must expose a material mapping")

    node_items = tuple(nodes.items())
    _checkpoint_observation_guard(
        _exact_guard,
        model,
        context="nonlinear checkpoint node mapping observation",
    )
    node_records = []
    for node_id, node in sorted(node_items, key=lambda item: int(item[0])):
        observed_coords = node.coords()
        _checkpoint_observation_guard(
            _exact_guard,
            model,
            context=f"nonlinear checkpoint node {node_id} coordinate observation",
        )
        coords = np.asarray(observed_coords, dtype=np.float64)
        _checkpoint_observation_guard(
            _exact_guard,
            model,
            context=f"nonlinear checkpoint node {node_id} coordinate array observation",
        )
        observed_dofs = getattr(node, "dofs", ())
        _checkpoint_observation_guard(
            _exact_guard,
            model,
            context=f"nonlinear checkpoint node {node_id} DOF observation",
        )
        dofs = np.asarray(observed_dofs, dtype=np.int64)
        _checkpoint_observation_guard(
            _exact_guard,
            model,
            context=f"nonlinear checkpoint node {node_id} DOF array observation",
        )
        if coords.shape != (3,) or not np.all(np.isfinite(coords)):
            raise NonlinearCheckpointError(f"node {node_id} has invalid coordinates")
        node_records.append(
            {"id": int(node_id), "coordinates": coords.tolist(), "dofs": dofs.tolist()}
        )

    element_items = tuple(elements.items())
    _checkpoint_observation_guard(
        _exact_guard,
        model,
        context="nonlinear checkpoint element mapping observation",
    )
    element_records = []
    for element_id, element in sorted(element_items, key=lambda item: int(item[0])):
        descriptor = _object_payload(
            element,
            path=f"model.elements[{element_id}]",
            _exact_guard=_exact_guard,
            _guard_model=model,
        )
        descriptor["id"] = int(element_id)
        element_records.append(descriptor)

    material_items = tuple(materials.items())
    _checkpoint_observation_guard(
        _exact_guard,
        model,
        context="nonlinear checkpoint material mapping observation",
    )
    material_records = []
    for name, material in sorted(material_items, key=lambda item: str(item[0])):
        descriptor = _object_payload(
            material,
            path=f"model.materials[{name!r}]",
            _exact_guard=_exact_guard,
            _guard_model=model,
        )
        descriptor["name"] = str(name)
        material_records.append(descriptor)

    boundary_items = tuple(getattr(model, "boundary_conditions", ()))
    _checkpoint_observation_guard(
        _exact_guard,
        model,
        context="nonlinear checkpoint boundary-condition observation",
    )
    boundary_records = [
        _object_payload(
            item,
            path=f"model.boundary_conditions[{index}]",
            _exact_guard=_exact_guard,
            _guard_model=model,
        )
        for index, item in enumerate(boundary_items)
    ]
    constraint_items = tuple(getattr(model, "constraint_equations", ()))
    _checkpoint_observation_guard(
        _exact_guard,
        model,
        context="nonlinear checkpoint constraint observation",
    )
    constraint_records = [
        _object_payload(
            item,
            path=f"model.constraint_equations[{index}]",
            _exact_guard=_exact_guard,
            _guard_model=model,
        )
        for index, item in enumerate(constraint_items)
    ]
    total_dofs = int(getattr(getattr(mesh, "dof_manager", None), "total_dofs", -1))
    if total_dofs < 0:
        raise NonlinearCheckpointError("model has no valid DOF layout")
    point_mass_items = tuple(getattr(mesh, "point_masses", {}).items())
    _checkpoint_observation_guard(
        _exact_guard,
        model,
        context="nonlinear checkpoint point-mass mapping observation",
    )
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
                point_mass_items, key=lambda item: int(item[0])
            )
        ],
    }


def model_configuration_fingerprint(
    model: Any,
    *,
    _exact_guard: Any = None,
) -> str:
    return _sha256(
        model_configuration_descriptor(model, _exact_guard=_exact_guard)
    )


def analysis_configuration_fingerprint(
    contract: Mapping[str, Any],
    *,
    _exact_guard: Any = None,
    _guard_model: Any = None,
) -> str:
    return _sha256(
        _normalize_json(
            contract,
            path="analysis_contract",
            _exact_guard=_exact_guard,
            _guard_model=_guard_model,
        )
    )


def _state_records(
    element_states: Mapping[int, Any],
    *,
    _exact_guard: Any = None,
    _guard_model: Any = None,
) -> list[Dict[str, Any]]:
    records: list[Dict[str, Any]] = []
    seen: set[int] = set()
    observed_items = tuple(element_states.items())
    _checkpoint_observation_guard(
        _exact_guard,
        _guard_model,
        context="nonlinear checkpoint element-state mapping observation",
    )
    for raw_id, state in sorted(observed_items, key=lambda item: int(item[0])):
        element_id = int(raw_id)
        _checkpoint_observation_guard(
            _exact_guard,
            _guard_model,
            context="nonlinear checkpoint element-state ID observation",
        )
        if element_id in seen:
            raise NonlinearCheckpointError(f"duplicate element state ID {element_id}")
        seen.add(element_id)
        records.append(
            {
                "element_id": element_id,
                "state": _normalize_json(
                    state,
                    path=f"element_states[{element_id}].state",
                    _exact_guard=_exact_guard,
                    _guard_model=_guard_model,
                ),
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

    exact_guard = _EXACT_QUALIFIED_COMPONENT_LIFECYCLE_GUARD
    checkpoint_validator = validate_nonlinear_checkpoint
    try:
        exact_guard(
            model,
            context="nonlinear checkpoint creation",
        )
    except ElementCapabilityError as exc:
        raise NonlinearCheckpointError(
            "checkpoint qualified element API authority is incompatible"
        ) from exc
    if type(analysis_kind) is not str:
        raise NonlinearCheckpointError("analysis_kind must be 'static' or 'arc_length'")
    kind = analysis_kind
    if kind not in {"static", "arc_length"}:
        raise NonlinearCheckpointError("analysis_kind must be 'static' or 'arc_length'")
    normalized_analysis_contract = _normalize_json(
        analysis_contract,
        path="analysis_contract",
        _exact_guard=exact_guard,
        _guard_model=model,
    )
    if type(normalized_analysis_contract) is not dict:
        raise NonlinearCheckpointError("analysis_contract must be a JSON object")
    total_dofs = int(model.mesh.dof_manager.total_dofs)
    displacement = np.asarray(displacements, dtype=np.float64)
    _checkpoint_observation_guard(
        exact_guard,
        model,
        context="nonlinear checkpoint displacement observation",
    )
    if (
        displacement.ndim != 1
        or displacement.size != total_dofs
        or not np.all(np.isfinite(displacement))
    ):
        raise NonlinearCheckpointError(
            "checkpoint displacement must be the complete finite global vector"
        )
    observed_deleted_ids = tuple(deleted_element_ids)
    _checkpoint_observation_guard(
        exact_guard,
        model,
        context="nonlinear checkpoint deletion-ID observation",
    )
    deleted = sorted(int(value) for value in observed_deleted_ids)
    _checkpoint_observation_guard(
        exact_guard,
        model,
        context="nonlinear checkpoint deletion-ID normalization",
    )
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
        try:
            exact_guard(
                model,
                context="nonlinear checkpoint activity serialization",
            )
        except ElementCapabilityError as exc:
            raise NonlinearCheckpointError(
                "checkpoint qualified element API authority changed during activity serialization"
            ) from exc
    payload: Dict[str, Any] = {
        "schema": NONLINEAR_CHECKPOINT_SCHEMA,
        "version": NONLINEAR_CHECKPOINT_VERSION,
        "integrity_id": NONLINEAR_CHECKPOINT_INTEGRITY_ID,
        "analysis_kind": kind,
        "model_fingerprint": model_configuration_fingerprint(
            model,
            _exact_guard=exact_guard,
        ),
        "analysis_fingerprint": analysis_configuration_fingerprint(
            normalized_analysis_contract
        ),
        "total_dofs": total_dofs,
        "displacements": displacement.tolist(),
        "element_states": _state_records(
            element_states,
            _exact_guard=exact_guard,
            _guard_model=model,
        ),
        "deleted_element_ids": deleted,
        "activity_state": _normalize_json(
            activity_state,
            path="activity_state",
            _exact_guard=exact_guard,
            _guard_model=model,
        ),
        "path_state": _normalize_json(
            path_state,
            path="path_state",
            _exact_guard=exact_guard,
            _guard_model=model,
        ),
    }
    payload[_CHECKPOINT_HASH_KEY] = _sha256(payload)
    made = _normalize_json(payload)
    # Producer and consumer share one fail-closed lifecycle boundary.  A
    # hash-valid payload is not a checkpoint unless its qualified element
    # records, deletion authority, activity state, and path metadata validate
    # against the exact model before it leaves the solver.
    try:
        exact_guard(
            model,
            context="nonlinear checkpoint payload construction",
        )
    except ElementCapabilityError as exc:
        raise NonlinearCheckpointError(
            "checkpoint qualified element API authority changed during payload construction"
        ) from exc
    checkpoint_validator(
        made,
        analysis_kind=kind,
        model=model,
        analysis_contract=normalized_analysis_contract,
        num_layers=int(normalized_analysis_contract.get("num_layers", 5)),
    )
    try:
        exact_guard(model, context="nonlinear checkpoint output")
    except ElementCapabilityError as exc:
        raise NonlinearCheckpointError(
            "checkpoint qualified element API authority changed before output"
        ) from exc
    return made


def load_nonlinear_checkpoint(
    value: Any,
    *,
    _exact_guard: Any = None,
    _guard_model: Any = None,
) -> Dict[str, Any]:
    """Parse and verify one checkpoint without consulting a model."""

    if isinstance(value, (bytes, bytearray, memoryview, str)):
        payload = _strict_json_loads(value)
    elif isinstance(value, Mapping):
        payload = _normalize_json(
            value,
            path="checkpoint",
            _exact_guard=_exact_guard,
            _guard_model=_guard_model,
        )
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

    exact_guard = _EXACT_QUALIFIED_COMPONENT_LIFECYCLE_GUARD
    try:
        exact_guard(model, context="nonlinear checkpoint validation preflight")
    except ElementCapabilityError as exc:
        raise NonlinearCheckpointError(
            "checkpoint qualified element API authority is incompatible"
        ) from exc
    payload = load_nonlinear_checkpoint(
        value,
        _exact_guard=exact_guard,
        _guard_model=model,
    )
    try:
        exact_guard(model, context="nonlinear checkpoint input observation")
    except ElementCapabilityError as exc:
        raise NonlinearCheckpointError(
            "checkpoint qualified element API authority changed during input observation"
        ) from exc
    if payload["analysis_kind"] != str(analysis_kind):
        raise NonlinearCheckpointError("checkpoint analysis kind is incompatible")
    try:
        qualified_api_authority = exact_guard(
            model,
            context="nonlinear checkpoint validation",
        )
    except ElementCapabilityError as exc:
        raise NonlinearCheckpointError(
            "checkpoint qualified element API authority is incompatible"
        ) from exc
    observed_model_fingerprint = model_configuration_fingerprint(
        model,
        _exact_guard=exact_guard,
    )
    try:
        exact_guard(model, context="nonlinear checkpoint model fingerprint")
    except ElementCapabilityError as exc:
        raise NonlinearCheckpointError(
            "checkpoint qualified element API authority changed during model fingerprinting"
        ) from exc
    if payload["model_fingerprint"] != observed_model_fingerprint:
        raise NonlinearCheckpointError("checkpoint model fingerprint is incompatible")
    normalized_analysis_contract = _normalize_json(
        analysis_contract,
        path="analysis_contract",
        _exact_guard=exact_guard,
        _guard_model=model,
    )
    if type(normalized_analysis_contract) is not dict:
        raise NonlinearCheckpointError("analysis_contract must be a JSON object")
    observed_analysis_fingerprint = analysis_configuration_fingerprint(
        normalized_analysis_contract
    )
    try:
        exact_guard(model, context="nonlinear checkpoint analysis fingerprint")
    except ElementCapabilityError as exc:
        raise NonlinearCheckpointError(
            "checkpoint qualified element API authority changed during analysis fingerprinting"
        ) from exc
    if payload["analysis_fingerprint"] != observed_analysis_fingerprint:
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
        if type(record["element_id"]) is not int:
            raise NonlinearCheckpointError(
                f"element state record {index} has a non-integer element ID"
            )
        element_id = record["element_id"]
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
    if not all(type(value) is int for value in deleted_raw):
        raise NonlinearCheckpointError(
            "deleted_element_ids must contain exact integers"
        )
    deleted = list(deleted_raw)
    if deleted != sorted(set(deleted)):
        raise NonlinearCheckpointError("deleted_element_ids must be sorted and unique")
    if not set(deleted).issubset(model_ids):
        raise NonlinearCheckpointError("checkpoint deletion state references missing elements")

    path_state = payload["path_state"]
    if not isinstance(path_state, dict):
        raise NonlinearCheckpointError("checkpoint path_state must be a JSON object")
    deletion_record_keys = {
        "element_id",
        "element_type",
        "step_index",
        "load_factor",
        "trigger_name",
        "trigger_value",
        "threshold",
        "location",
        "measure",
    }
    deletion_authority: Dict[int, Dict[str, Any]] = {}
    raw_deletion_records = path_state.get("deletion_records")
    if raw_deletion_records is not None:
        if str(analysis_kind) != "static" or not isinstance(
            raw_deletion_records, list
        ):
            raise NonlinearCheckpointError(
                "checkpoint deletion records are incompatible"
            )
        for index, record in enumerate(raw_deletion_records):
            if not isinstance(record, Mapping) or set(record) != deletion_record_keys:
                raise NonlinearCheckpointError(
                    f"checkpoint deletion record {index} is malformed"
                )
            if type(record["element_id"]) is not int:
                raise NonlinearCheckpointError(
                    f"checkpoint deletion record {index} has an invalid element ID"
                )
            element_id = record["element_id"]
            if element_id in deletion_authority:
                raise NonlinearCheckpointError(
                    "checkpoint deletion records contain duplicate element IDs"
                )
            if (
                type(record["step_index"]) is not int
                or int(record["step_index"]) <= 0
                or type(record["element_type"]) is not str
                or not record["element_type"]
                or type(record["trigger_name"]) is not str
                or not record["trigger_name"]
                or type(record["location"]) is not str
                or not record["location"]
            ):
                raise NonlinearCheckpointError(
                    f"checkpoint deletion record {index} has invalid identity fields"
                )
            for name in (
                "load_factor",
                "trigger_value",
                "threshold",
                "measure",
            ):
                raw_value = record[name]
                if type(raw_value) is not float or not math.isfinite(raw_value):
                    raise NonlinearCheckpointError(
                        f"checkpoint deletion record {index} has invalid {name}"
                    )
            if float(record["threshold"]) <= 0.0 or float(record["measure"]) < 0.0:
                raise NonlinearCheckpointError(
                    f"checkpoint deletion record {index} has invalid bounds"
                )
            deletion_authority[element_id] = copy.deepcopy(dict(record))
    if set(deletion_authority) != set(deleted):
        raise NonlinearCheckpointError(
            "checkpoint deletion records and deleted_element_ids disagree"
        )
    fracture_contract = normalized_analysis_contract.get("fracture_config")
    if deleted and not isinstance(fracture_contract, Mapping):
        raise NonlinearCheckpointError(
            "checkpoint deletion history lacks its fracture contract"
        )
    try:
        fracture_threshold = (
            None
            if not deleted
            else float(fracture_contract["threshold"])
        )
        residual_stiffness_fraction = (
            None
            if not deleted
            else float(fracture_contract["residual_stiffness_fraction"])
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise NonlinearCheckpointError(
            "checkpoint residual stiffness fraction is malformed"
        ) from exc
    if residual_stiffness_fraction is not None and (
        not math.isfinite(residual_stiffness_fraction)
        or not 0.0 <= residual_stiffness_fraction <= 1.0
    ):
        raise NonlinearCheckpointError(
            "checkpoint residual stiffness fraction is invalid"
        )
    if fracture_threshold is not None and (
        not math.isfinite(fracture_threshold) or fracture_threshold <= 0.0
    ):
        raise NonlinearCheckpointError("checkpoint fracture threshold is invalid")

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
            _validate_complete_activity_history(restored_activity)
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

    if restored_activity is not None:
        activity_ids = np.asarray(restored_activity.element_ids, dtype=np.int64)
        activity_deleted_ids = {
            int(value)
            for value in activity_ids[
                np.asarray(restored_activity.hard_deleted_mask, dtype=bool)
            ]
        }
        qualified_element_ids = {
            int(value)
            for value in qualified_api_authority["qualified_element_ids"]
        }
        recorded_deleted_ids = set(deleted)
        if not recorded_deleted_ids.issubset(activity_deleted_ids):
            raise NonlinearCheckpointError(
                "checkpoint deleted_element_ids are not hard-deleted in "
                "the activity state"
            )
        if (
            activity_deleted_ids - recorded_deleted_ids
        ) & qualified_element_ids:
            raise NonlinearCheckpointError(
                "checkpoint qualified hard-deleted activity IDs disagree "
                "with deleted_element_ids"
            )

    normalized_states: Dict[int, Any] = {}
    # Qualified shell history is a closed lifecycle contract.  Dispatch the
    # exact production validators explicitly so a missing convenience hook or
    # an unexpected instance attribute cannot downgrade an ACTIVE,
    # FAILED, or DELETED record to an opaque legacy state.
    from .e4_pl_element import QualifiedE4PLShellElement
    from .e4_pl_s3_element import QualifiedE4PLS3ShellElement
    from .fracture import (
        element_fracture_category,
        element_measure,
        state_equivalent_plastic_strain,
    )

    for element_id in sorted(model_ids):
        element = model.mesh.elements[element_id]
        if type(element) in {
            QualifiedE4PLShellElement,
            QualifiedE4PLS3ShellElement,
        } and element_id not in states:
            lifecycle = "deleted" if element_id in deleted else "active"
            raise NonlinearCheckpointError(
                f"checkpoint {lifecycle} qualified element {element_id} has no "
                "committed state"
            )

    for element_id, state in states.items():
        element = model.mesh.elements[element_id]
        element_namespace = vars(element)
        raw_material_name = element_namespace.get("material_name")
        if type(raw_material_name) is not str:
            raise NonlinearCheckpointError(
                f"checkpoint element {element_id} lacks exact instance-owned "
                "material_name"
            )
        material_name = raw_material_name
        try:
            material = model.materials[material_name]
            mapping = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
            local_u = displacement[mapping]

            if element_id in deleted:
                record = deletion_authority[element_id]
                category = element_fracture_category(element)
                trigger_value, location = state_equivalent_plastic_strain(state)
                measure = element_measure(model.mesh, element)
                if (
                    category is None
                    or record["element_type"] != category
                    or record["trigger_name"]
                    != "max_equivalent_plastic_strain"
                    or float(record["trigger_value"]) != float(trigger_value)
                    or float(record["threshold"]) != fracture_threshold
                    or record["location"] != location
                    or float(record["measure"]) != float(measure)
                ):
                    raise ValueError(
                        "deletion record does not reproduce its exact model/state authority"
                    )

            if type(element) is QualifiedE4PLShellElement:
                disposition = (
                    state.get("qualified_q4_activity_disposition")
                    if isinstance(state, Mapping)
                    else None
                )
                if element_id in deleted:
                    if not isinstance(disposition, Mapping) or disposition.get(
                        "status"
                    ) != "DELETED_FROZEN_NONCURRENT":
                        raise ValueError(
                            "deleted qualified Q4 state lacks its exact frozen "
                            "disposition"
                        )
                    QualifiedE4PLShellElement.validate_noncurrent_deleted_state(
                        element,
                        model.mesh,
                        material,
                        state,
                        int(num_layers),
                        expected_deletion_step_index=int(
                            deletion_authority[element_id]["step_index"]
                        ),
                        expected_deletion_load_factor=float(
                            deletion_authority[element_id]["load_factor"]
                        ),
                        expected_residual_stiffness_fraction=(
                            residual_stiffness_fraction
                        ),
                        expected_trigger_name=str(
                            deletion_authority[element_id]["trigger_name"]
                        ),
                    )
                else:
                    if disposition is not None:
                        raise ValueError(
                            "noncurrent qualified Q4 state is not continuable"
                        )
                    QualifiedE4PLShellElement.validate_committed_current_tangent_state(
                        element,
                        model.mesh,
                        material,
                        local_u,
                        state,
                        int(num_layers),
                    )
                normalized_states[element_id] = copy.deepcopy(state)
                continue

            if type(element) is QualifiedE4PLS3ShellElement:
                disposition = (
                    state.get("qualified_s3_activity_disposition")
                    if isinstance(state, Mapping)
                    else None
                )
                if element_id in deleted:
                    if not isinstance(disposition, Mapping) or disposition.get(
                        "status"
                    ) != "DELETED_FROZEN_NONCURRENT":
                        raise ValueError(
                            "deleted qualified S3 state lacks its exact frozen "
                            "disposition"
                        )
                    QualifiedE4PLS3ShellElement.validate_noncurrent_deleted_state(
                        element,
                        model.mesh,
                        material,
                        state,
                        int(num_layers),
                        expected_deletion_step_index=int(
                            deletion_authority[element_id]["step_index"]
                        ),
                        expected_deletion_load_factor=float(
                            deletion_authority[element_id]["load_factor"]
                        ),
                        expected_residual_stiffness_fraction=(
                            residual_stiffness_fraction
                        ),
                        expected_trigger_name=str(
                            deletion_authority[element_id]["trigger_name"]
                        ),
                    )
                    normalized_states[element_id] = copy.deepcopy(state)
                else:
                    if disposition is not None:
                        raise ValueError(
                            "noncurrent qualified S3 state is not continuable"
                        )
                    normalized_states[element_id] = (
                        QualifiedE4PLS3ShellElement.validate_model_bound_nonlinear_state(
                            element,
                            model.mesh,
                            material,
                            state,
                            int(num_layers),
                            expected_committed_total_u=local_u,
                        )
                    )
                continue

            validator = getattr(
                element, "validate_model_bound_nonlinear_state", None
            )
            if callable(validator):
                normalized_states[element_id] = validator(
                    model.mesh,
                    material,
                    state,
                    int(num_layers),
                    expected_committed_total_u=local_u,
                )
            else:
                normalized_states[element_id] = copy.deepcopy(state)
        except Exception as exc:
            raise NonlinearCheckpointError(
                f"checkpoint state for element {element_id} is incompatible"
            ) from exc

    # Reconstructing the node-shared store is the final pre-assembly check. It
    # rejects missing native states and any redundant per-element Q/director
    # copies that disagree at a shared node.
    from .nonlinear_state import create_model_native_rotation_store

    try:
        create_model_native_rotation_store(
            model,
            normalized_states,
            displacement,
            noncurrent_element_ids=tuple(deleted),
        )
    except Exception as exc:
        raise NonlinearCheckpointError(
            "checkpoint node-shared rotation history is inconsistent"
        ) from exc

    try:
        exact_guard(model, context="nonlinear checkpoint validated output")
    except ElementCapabilityError as exc:
        raise NonlinearCheckpointError(
            "checkpoint qualified element API authority changed before validated output"
        ) from exc
    return ValidatedNonlinearCheckpoint(
        payload=copy.deepcopy(payload),
        displacements=displacement.copy(),
        element_states=copy.deepcopy(normalized_states),
        deleted_element_ids=set(deleted),
        activity=restored_activity,
        path_state=copy.deepcopy(path_state),
    )


def _publish_checkpoint_public_signatures() -> None:
    """Keep authority plumbing private while preserving the v1 API."""

    from inspect import signature

    private_parameters = {
        canonical_checkpoint_json_bytes: {"_exact_guard", "_guard_model"},
        model_configuration_descriptor: {"_exact_guard"},
        model_configuration_fingerprint: {"_exact_guard"},
        analysis_configuration_fingerprint: {
            "_exact_guard",
            "_guard_model",
        },
        load_nonlinear_checkpoint: {"_exact_guard", "_guard_model"},
    }
    for function, hidden in private_parameters.items():
        public = signature(function)
        function.__signature__ = public.replace(
            parameters=tuple(
                parameter
                for parameter in public.parameters.values()
                if parameter.name not in hidden
            )
        )


_publish_checkpoint_public_signatures()
del _publish_checkpoint_public_signatures


__all__ = [
    "NONLINEAR_CHECKPOINT_INTEGRITY_ID",
    "NONLINEAR_CHECKPOINT_SCHEMA",
    "NONLINEAR_CHECKPOINT_VERSION",
    "QUALIFIED_CHECKPOINT_LIFECYCLE_POLICY_ID",
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
