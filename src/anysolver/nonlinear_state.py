"""Persistent, solver-owned storage for nonlinear constitutive state.

The public nonlinear solver contract uses ``{element_id: state}`` mappings.  That
is a useful interchange format for restart, recovery, and result snapshots, but
packing and allocating those dictionaries in every Newton iteration is costly.
This module provides a deliberately small internal alternative:

* :class:`ShellStateLayout` is immutable geometry for one compatible shell batch;
* :class:`ShellStateBatch` owns contiguous committed and trial buffers;
* :class:`NonlinearStateStore` coordinates one or more batches for one solve.

The storage objects are solver-owned.  They must not be attached to cached
assembly plans: a plan can be shared by sequential analyses, while constitutive
history belongs to exactly one analysis.  Public mappings are always materialized
as owned copies so restart/recovery consumers cannot mutate the active solve.
Unsupported state dictionaries remain available through an explicit, diagnosed
legacy fallback.
"""

from __future__ import annotations

import copy
import threading
import time
from collections.abc import Hashable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Dict, Optional

import numpy as np


_CORE_FIELDS = ("plastic_strain", "alpha", "layer_strain")
_FIELD_INDEX = {name: index for index, name in enumerate(_CORE_FIELDS)}
_INITIAL_FIELD_KEYS = (
    "initial_membrane_stress",
    "initial_bending_stress",
    "initial_membrane_prestrain",
    "initial_curvature_prestrain",
)
_KNOWN_PROVENANCE_KEYS = (
    "provenance",
    "initial_field_provenance",
    "state_provenance",
    "material_provenance",
)


class NonlinearStateError(RuntimeError):
    """Base class for persistent nonlinear-state contract errors."""


class StateTransactionError(NonlinearStateError):
    """Raised when trial-state transaction ordering is invalid."""


class StaleStateTokenError(StateTransactionError):
    """Raised when a trial token no longer names the active generation."""


class ImmutableStateSidecarError(NonlinearStateError):
    """Raised when an update attempts to alter an immutable initial field."""


class PersistentStateEligibilityError(NonlinearStateError):
    """Raised when a caller requests an array path for a fallback state."""


class StateMaterializationPolicy(str, Enum):
    """Reason an owned public dictionary is being requested."""

    EXPLICIT = "explicit"
    FINAL_RESULT = "final_result"
    SAVED_STATE = "saved_state"
    RESTART = "restart"
    RECOVERY = "recovery"


@dataclass(frozen=True, slots=True)
class ShellStateLayout:
    """Immutable array layout for a homogeneous shell batch.

    Parameters match the persistent shell assembly plan vocabulary.  State is
    stored at ``n_gp * num_layers`` material points per element, with three
    engineering in-plane components for plastic and total layer strain.
    """

    element_ids: tuple[int, ...]
    n_gp: int
    num_layers: int
    _element_index: Mapping[int, int] = field(
        init=False,
        repr=False,
        compare=False,
        hash=False,
    )

    def __post_init__(self) -> None:
        element_ids = tuple(int(value) for value in self.element_ids)
        if not element_ids:
            raise ValueError("ShellStateLayout requires at least one element")
        if len(set(element_ids)) != len(element_ids):
            raise ValueError("ShellStateLayout element_ids must be unique")
        if int(self.n_gp) <= 0:
            raise ValueError("ShellStateLayout n_gp must be positive")
        if int(self.num_layers) <= 0:
            raise ValueError("ShellStateLayout num_layers must be positive")
        object.__setattr__(self, "element_ids", element_ids)
        object.__setattr__(self, "n_gp", int(self.n_gp))
        object.__setattr__(self, "num_layers", int(self.num_layers))
        object.__setattr__(
            self,
            "_element_index",
            MappingProxyType(
                {element_id: index for index, element_id in enumerate(element_ids)}
            ),
        )

    @classmethod
    def from_dimensions(
        cls,
        element_ids: Sequence[int],
        n_gp: int,
        num_layers: int,
    ) -> "ShellStateLayout":
        return cls(tuple(int(value) for value in element_ids), int(n_gp), int(num_layers))

    @property
    def n_elements(self) -> int:
        return len(self.element_ids)

    @property
    def points_per_element(self) -> int:
        return int(self.n_gp * self.num_layers)

    @property
    def state_point_count(self) -> int:
        return int(self.n_elements * self.points_per_element)

    @property
    def buffer_value_count(self) -> int:
        # plastic strain (3), alpha (1), and total layer strain (3).
        return int(self.state_point_count * 7)

    def index(self, element_id: int) -> int:
        try:
            return int(self._element_index[int(element_id)])
        except KeyError as exc:
            raise KeyError(f"Element {int(element_id)} is not in this shell layout") from exc

    def compatible_with(self, other: "ShellStateLayout") -> bool:
        return bool(
            isinstance(other, ShellStateLayout)
            and self.element_ids == other.element_ids
            and self.n_gp == other.n_gp
            and self.num_layers == other.num_layers
        )


@dataclass(frozen=True, slots=True)
class StateTrialToken:
    """Opaque generation-checked capability for one active trial update."""

    generation: int
    serial: int
    _owner: object = field(repr=False, compare=False, hash=False)


@dataclass(frozen=True, slots=True)
class ShellStateArrays:
    """Read-only array views of one committed shell-state buffer."""

    plastic_strain: np.ndarray
    alpha: np.ndarray
    layer_strain: np.ndarray


@dataclass(frozen=True, slots=True)
class _FrozenList:
    values: tuple[Any, ...]


@dataclass(frozen=True, slots=True)
class _FrozenTuple:
    values: tuple[Any, ...]


@dataclass(frozen=True, slots=True)
class _FrozenSet:
    values: frozenset[Any]


@dataclass(frozen=True, slots=True)
class _FrozenFrozenSet:
    values: frozenset[Any]


def _owned_copy(value: Any) -> Any:
    """Copy an arbitrary legacy state without exposing caller-owned arrays."""

    try:
        return copy.deepcopy(value)
    except Exception as exc:  # pragma: no cover - exotic third-party states
        raise TypeError("Nonlinear state must support owned deep-copy semantics") from exc


def _freeze_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        result = np.array(value, copy=True, order="C")
        result.setflags(write=False)
        return result
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_value(item) for key, item in value.items()})
    if isinstance(value, list):
        return _FrozenList(tuple(_freeze_value(item) for item in value))
    if isinstance(value, tuple):
        return _FrozenTuple(tuple(_freeze_value(item) for item in value))
    if isinstance(value, set):
        return _FrozenSet(frozenset(_freeze_value(item) for item in value))
    if isinstance(value, frozenset):
        return _FrozenFrozenSet(frozenset(_freeze_value(item) for item in value))
    return _owned_copy(value)


def _thaw_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return np.array(value, copy=True, order="C")
    if isinstance(value, Mapping):
        return {key: _thaw_value(item) for key, item in value.items()}
    if isinstance(value, _FrozenList):
        return [_thaw_value(item) for item in value.values]
    if isinstance(value, _FrozenTuple):
        return tuple(_thaw_value(item) for item in value.values)
    if isinstance(value, _FrozenSet):
        return {_thaw_value(item) for item in value.values}
    if isinstance(value, _FrozenFrozenSet):
        return frozenset(_thaw_value(item) for item in value.values)
    return _owned_copy(value)


def _state_values_equal(left: Any, right: Any) -> bool:
    if isinstance(left, np.ndarray) or isinstance(right, np.ndarray):
        try:
            return bool(np.array_equal(np.asarray(left), np.asarray(right), equal_nan=True))
        except (TypeError, ValueError):
            return False
    if isinstance(left, Mapping) and isinstance(right, Mapping):
        return bool(
            set(left) == set(right)
            and all(_state_values_equal(left[key], right[key]) for key in left)
        )
    if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
        return bool(
            len(left) == len(right)
            and all(_state_values_equal(a, b) for a, b in zip(left, right))
        )
    try:
        return bool(left == right)
    except (TypeError, ValueError):
        return False


def _is_sidecar_key(key: str) -> bool:
    return bool(
        key in _INITIAL_FIELD_KEYS
        or key in _KNOWN_PROVENANCE_KEYS
        or key.endswith("_provenance")
    )


def _fallback_reason(state: Any, layout: ShellStateLayout) -> Optional[str]:
    if state is None:
        return None
    if not isinstance(state, Mapping):
        return "state_not_mapping"
    unsupported = sorted(
        str(key)
        for key in state
        if str(key) not in _CORE_FIELDS and not _is_sidecar_key(str(key))
    )
    if unsupported:
        return "unsupported_state_keys:" + ",".join(unsupported)
    missing = [key for key in ("plastic_strain", "alpha") if key not in state]
    if missing:
        return "missing_required_core_fields:" + ",".join(missing)
    points = layout.points_per_element
    expected = {
        "plastic_strain": (points, 3),
        "alpha": (points,),
        "layer_strain": (points, 3),
    }
    for key, shape in expected.items():
        if key not in state:
            continue
        try:
            actual = np.asarray(state[key], dtype=float).shape
        except (TypeError, ValueError):
            return f"invalid_{key}_values"
        if actual != shape:
            return f"invalid_{key}_shape:{actual}"
    return None


def _extract_sidecar(state: Any) -> Mapping[str, Any]:
    if not isinstance(state, Mapping):
        return MappingProxyType({})
    return MappingProxyType(
        {
            str(key): _freeze_value(value)
            for key, value in state.items()
            if _is_sidecar_key(str(key))
        }
    )


def _readonly_view(array: np.ndarray) -> np.ndarray:
    result = array.view()
    result.setflags(write=False)
    return result


class ShellStateBatch(Mapping[int, Any]):
    """Contiguous committed/trial history for one compatible shell batch.

    ``begin_trial`` does not copy committed values.  Full-batch kernel updates
    overwrite the inactive buffer and ``commit`` swaps two pointers.  Partial
    updates copy only missing fields/elements at commit.  ``discard_trial`` is
    always O(1) with respect to state size.
    """

    def __init__(
        self,
        layout: ShellStateLayout,
        committed_states: Optional[Mapping[int, Any]] = None,
    ) -> None:
        if not isinstance(layout, ShellStateLayout):
            raise TypeError("layout must be a ShellStateLayout")
        self.layout = layout
        self._owner = object()
        self._lock = threading.RLock()
        self._committed_buffer = np.zeros(layout.buffer_value_count, dtype=np.float64)
        self._trial_buffer = np.empty_like(self._committed_buffer)
        self._packed_mask = np.ones(layout.n_elements, dtype=bool)
        self._deleted_mask = np.zeros(layout.n_elements, dtype=bool)
        self._present_committed = np.zeros(layout.n_elements, dtype=bool)
        self._present_trial_stamps = np.zeros(layout.n_elements, dtype=np.int64)
        self._sidecars: list[Mapping[str, Any]] = [
            MappingProxyType({}) for _ in range(layout.n_elements)
        ]
        self._fallback_committed: Dict[int, Any] = {}
        self._fallback_reasons: Dict[int, str] = {}
        self._trial_legacy: Dict[int, tuple[Any, str]] = {}
        # Generation stamps avoid clearing an O(elements) boolean mask at begin.
        self._write_stamps = np.zeros((len(_CORE_FIELDS), layout.n_elements), dtype=np.int64)
        self._generation = 0
        self._serial = 0
        self._active_token: Optional[StateTrialToken] = None
        self._metrics: Dict[str, Any] = {
            "state_pack_seconds": 0.0,
            "state_trial_update_seconds": 0.0,
            "state_commit_seconds": 0.0,
            "state_discard_seconds": 0.0,
            "state_materialization_seconds": 0.0,
            "state_materialization_count": 0,
            "state_trial_begin_count": 0,
            "state_trial_update_count": 0,
            "state_commit_count": 0,
            "state_discard_count": 0,
            "state_swap_commit_count": 0,
            "state_bounded_copy_commit_count": 0,
            "state_commit_copied_element_fields": 0,
            "state_trial_updated_point_count": 0,
            "stale_token_error_count": 0,
            "materialization_reasons": {},
        }
        self._pack(committed_states or {})

    @classmethod
    def from_mapping(
        cls,
        layout: ShellStateLayout,
        committed_states: Optional[Mapping[int, Any]] = None,
    ) -> "ShellStateBatch":
        return cls(layout, committed_states)

    @classmethod
    def pack(
        cls,
        layout: ShellStateLayout,
        committed_states: Optional[Mapping[int, Any]] = None,
    ) -> "ShellStateBatch":
        """Named constructor used by restart/import boundaries."""

        return cls(layout, committed_states)

    @property
    def generation(self) -> int:
        return int(self._generation)

    @property
    def has_active_trial(self) -> bool:
        return self._active_token is not None

    @property
    def all_packed(self) -> bool:
        return bool(np.all(self._packed_mask))

    @property
    def has_initial_fields(self) -> bool:
        return any(
            any(key in sidecar for key in _INITIAL_FIELD_KEYS)
            for sidecar in self._sidecars
        )

    @property
    def fallback_element_ids(self) -> tuple[int, ...]:
        return tuple(
            element_id
            for index, element_id in enumerate(self.layout.element_ids)
            if not bool(self._packed_mask[index])
        )

    @property
    def deleted_element_ids(self) -> tuple[int, ...]:
        return tuple(
            element_id
            for index, element_id in enumerate(self.layout.element_ids)
            if bool(self._deleted_mask[index])
        )

    @property
    def committed_buffer(self) -> np.ndarray:
        """Read-only view used for contiguity/memory diagnostics."""

        return _readonly_view(self._committed_buffer)

    @property
    def trial_buffer(self) -> np.ndarray:
        """Read-only view of the inactive/trial allocation."""

        return _readonly_view(self._trial_buffer)

    def _views(self, buffer: np.ndarray) -> ShellStateArrays:
        points = self.layout.state_point_count
        n_elements = self.layout.n_elements
        points_per_element = self.layout.points_per_element
        plastic_stop = points * 3
        alpha_stop = plastic_stop + points
        plastic = buffer[:plastic_stop].reshape(n_elements, points_per_element, 3)
        alpha = buffer[plastic_stop:alpha_stop].reshape(n_elements, points_per_element)
        layer = buffer[alpha_stop:].reshape(n_elements, points_per_element, 3)
        return ShellStateArrays(plastic, alpha, layer)

    def committed_arrays(self) -> ShellStateArrays:
        """Return read-only, zero-copy views for constitutive kernels."""

        views = self._views(self._committed_buffer)
        return ShellStateArrays(
            _readonly_view(views.plastic_strain),
            _readonly_view(views.alpha),
            _readonly_view(views.layer_strain),
        )

    def _pack(self, committed_states: Mapping[int, Any]) -> None:
        start = time.perf_counter()
        views = self._views(self._committed_buffer)
        points = self.layout.points_per_element
        for index, element_id in enumerate(self.layout.element_ids):
            present = element_id in committed_states
            self._present_committed[index] = present
            state = committed_states.get(element_id)
            self._sidecars[index] = _extract_sidecar(state)
            reason = (
                "state_is_explicit_none"
                if present and state is None
                else _fallback_reason(state, self.layout)
            )
            if reason is not None:
                self._packed_mask[index] = False
                self._fallback_committed[element_id] = _owned_copy(state)
                self._fallback_reasons[element_id] = reason
                continue
            if state is None:
                continue
            if "plastic_strain" in state:
                views.plastic_strain[index] = np.asarray(
                    state["plastic_strain"], dtype=float
                ).reshape(points, 3)
            if "alpha" in state:
                views.alpha[index] = np.asarray(state["alpha"], dtype=float).reshape(points)
            if "layer_strain" in state:
                views.layer_strain[index] = np.asarray(
                    state["layer_strain"], dtype=float
                ).reshape(points, 3)
        self._metrics["state_pack_seconds"] += time.perf_counter() - start

    def compatible_with(self, layout: ShellStateLayout) -> bool:
        return self.layout.compatible_with(layout)

    def persistent_eligibility(
        self,
        layout: Optional[ShellStateLayout] = None,
    ) -> tuple[bool, Optional[str]]:
        if layout is not None and not self.compatible_with(layout):
            return False, "shell_state_layout_mismatch"
        if not self.all_packed:
            return False, "legacy_dictionary_fallback"
        if self.has_initial_fields:
            return False, "immutable_initial_field_requires_exact_override"
        return True, None

    def begin_trial(self) -> StateTrialToken:
        with self._lock:
            if self._active_token is not None:
                raise StateTransactionError("A shell-state trial is already active")
            self._serial += 1
            token = StateTrialToken(self._generation, self._serial, self._owner)
            self._active_token = token
            self._trial_legacy = {}
            self._metrics["state_trial_begin_count"] += 1
            return token

    def begin(self) -> StateTrialToken:
        """Short transaction alias for :meth:`begin_trial`."""

        return self.begin_trial()

    def _require_active(self, token: StateTrialToken) -> None:
        valid = bool(
            isinstance(token, StateTrialToken)
            and token._owner is self._owner
            and token.generation == self._generation
            and self._active_token is token
        )
        if not valid:
            self._metrics["stale_token_error_count"] += 1
            raise StaleStateTokenError(
                "Trial token is stale, belongs to another store, or is not active"
            )

    def validate_trial_token(self, token: StateTrialToken) -> None:
        """Validate a token before a caller starts an expensive kernel."""

        with self._lock:
            self._require_active(token)

    def _indices(self, element_ids: Optional[Sequence[int]]) -> np.ndarray:
        if element_ids is None:
            return np.arange(self.layout.n_elements, dtype=np.intp)
        return np.asarray(
            [self.layout.index(int(element_id)) for element_id in element_ids],
            dtype=np.intp,
        )

    def _coerce_update(
        self,
        field_name: str,
        values: Any,
        count: int,
    ) -> np.ndarray:
        points = self.layout.points_per_element
        tail = (points,) if field_name == "alpha" else (points, 3)
        expected = (count, *tail)
        array = np.asarray(values, dtype=float)
        if count == 1 and array.shape == tail:
            array = array.reshape(expected)
        elif array.size == int(np.prod(expected, dtype=np.int64)):
            array = array.reshape(expected)
        if array.shape != expected:
            raise ValueError(
                f"{field_name} trial update must have shape {expected}; got {array.shape}"
            )
        return array

    def update_trial(
        self,
        token: StateTrialToken,
        *,
        plastic_strain: Any = None,
        alpha: Any = None,
        layer_strain: Any = None,
        element_ids: Optional[Sequence[int]] = None,
    ) -> int:
        """Write packed trial fields and return the number of active elements.

        Deleted elements are deliberately skipped.  A later commit copies their
        qualified committed rows into the trial allocation before swapping.
        """

        with self._lock:
            self._require_active(token)
            supplied = {
                "plastic_strain": plastic_strain,
                "alpha": alpha,
                "layer_strain": layer_strain,
            }
            supplied = {
                name: value for name, value in supplied.items() if value is not None
            }
            if not supplied:
                raise ValueError("At least one shell trial field must be supplied")
            indices = self._indices(element_ids)
            if np.any(~self._packed_mask[indices]):
                raise PersistentStateEligibilityError(
                    "Array trial updates cannot include legacy dictionary fallback elements"
                )
            active = indices[~self._deleted_mask[indices]]
            start = time.perf_counter()
            trial_views = self._views(self._trial_buffer)
            for field_name, values in supplied.items():
                array = self._coerce_update(field_name, values, int(indices.size))
                if active.size:
                    active_in_input = ~self._deleted_mask[indices]
                    getattr(trial_views, field_name)[active] = array[active_in_input]
                    self._write_stamps[_FIELD_INDEX[field_name], active] = self._serial
            self._present_trial_stamps[active] = self._serial
            elapsed = time.perf_counter() - start
            self._metrics["state_trial_update_seconds"] += elapsed
            self._metrics["state_trial_update_count"] += 1
            self._metrics["state_trial_updated_point_count"] += int(
                active.size * self.layout.points_per_element
            )
            return int(active.size)

    def _validate_or_merge_sidecar(self, index: int, state: Any) -> Any:
        if not isinstance(state, Mapping):
            if self._sidecars[index]:
                raise ImmutableStateSidecarError(
                    "A state carrying immutable initial fields must remain a mapping"
                )
            return _owned_copy(state)
        result = _owned_copy(dict(state))
        frozen = self._sidecars[index]
        for key in result:
            if _is_sidecar_key(str(key)) and str(key) not in frozen:
                raise ImmutableStateSidecarError(
                    f"Trial update cannot introduce immutable sidecar {key!r}"
                )
        for key, frozen_value in frozen.items():
            expected = _thaw_value(frozen_value)
            if key in result and not _state_values_equal(result[key], expected):
                raise ImmutableStateSidecarError(
                    f"Trial update cannot modify immutable sidecar {key!r}"
                )
            result[key] = expected
        return result

    def set_trial_state(
        self,
        token: StateTrialToken,
        element_id: int,
        state: Any,
    ) -> None:
        """Route one scalar/reference state through packed or dictionary storage."""

        with self._lock:
            self._require_active(token)
            index = self.layout.index(int(element_id))
            if self._deleted_mask[index]:
                return
            owned_state = self._validate_or_merge_sidecar(index, state)
            if not self._packed_mask[index]:
                self._trial_legacy[int(element_id)] = (
                    owned_state,
                    self._fallback_reasons.get(
                        int(element_id), "legacy_dictionary_fallback"
                    ),
                )
                self._present_trial_stamps[index] = self._serial
                return
            reason = _fallback_reason(owned_state, self.layout)
            if reason is not None:
                self._trial_legacy[int(element_id)] = (owned_state, reason)
                self._present_trial_stamps[index] = self._serial
                return
            updates = {
                key: owned_state[key]
                for key in _CORE_FIELDS
                if isinstance(owned_state, Mapping) and key in owned_state
            }
            if updates:
                self.update_trial(token, element_ids=(int(element_id),), **updates)

    def freeze_deleted(self, element_ids: Sequence[int]) -> None:
        """Permanently freeze the qualified committed state of deleted elements."""

        with self._lock:
            for element_id in element_ids:
                self._deleted_mask[self.layout.index(int(element_id))] = True

    def _materialized_packed_state(
        self,
        index: int,
        token: Optional[StateTrialToken],
    ) -> Dict[str, Any]:
        committed = self._views(self._committed_buffer)
        trial = self._views(self._trial_buffer)
        result: Dict[str, Any] = {}
        use_trial = token is not None and not bool(self._deleted_mask[index])
        for field_name in _CORE_FIELDS:
            field_index = _FIELD_INDEX[field_name]
            source = (
                getattr(trial, field_name)
                if use_trial and self._write_stamps[field_index, index] == self._serial
                else getattr(committed, field_name)
            )
            result[field_name] = np.array(source[index], copy=True, order="C")
        for key, value in self._sidecars[index].items():
            result[key] = _thaw_value(value)
        return result

    def _is_present(
        self,
        index: int,
        token: Optional[StateTrialToken],
    ) -> bool:
        return bool(
            self._present_committed[index]
            or (
                token is not None
                and self._present_trial_stamps[index] == self._serial
            )
        )

    def materialize(
        self,
        *,
        element_ids: Optional[Sequence[int]] = None,
        trial_token: Optional[StateTrialToken] = None,
        policy: StateMaterializationPolicy | str = StateMaterializationPolicy.EXPLICIT,
    ) -> Dict[int, Any]:
        """Materialize owned public dictionaries for restart/recovery/results."""

        with self._lock:
            if trial_token is not None:
                self._require_active(trial_token)
            reason = StateMaterializationPolicy(policy).value
            start = time.perf_counter()
            indices = self._indices(element_ids)
            result: Dict[int, Any] = {}
            for index_value in indices:
                index = int(index_value)
                element_id = self.layout.element_ids[index]
                if not self._is_present(index, trial_token):
                    continue
                if trial_token is not None and element_id in self._trial_legacy:
                    result[element_id] = _owned_copy(self._trial_legacy[element_id][0])
                elif not self._packed_mask[index]:
                    result[element_id] = _owned_copy(self._fallback_committed[element_id])
                else:
                    result[element_id] = self._materialized_packed_state(index, trial_token)
            elapsed = time.perf_counter() - start
            self._metrics["state_materialization_seconds"] += elapsed
            self._metrics["state_materialization_count"] += 1
            reasons = self._metrics["materialization_reasons"]
            reasons[reason] = int(reasons.get(reason, 0)) + 1
            return result

    def materialize_owned(
        self,
        *,
        element_ids: Optional[Sequence[int]] = None,
        trial_token: Optional[StateTrialToken] = None,
        policy: StateMaterializationPolicy | str = StateMaterializationPolicy.EXPLICIT,
    ) -> Dict[int, Any]:
        """Explicitly named alias emphasizing the ownership guarantee."""

        return self.materialize(
            element_ids=element_ids,
            trial_token=trial_token,
            policy=policy,
        )

    def commit(self, token: StateTrialToken) -> int:
        """Commit the active trial, using a pointer swap for full updates."""

        with self._lock:
            self._require_active(token)
            start = time.perf_counter()
            converted_indices = {
                self.layout.index(element_id) for element_id in self._trial_legacy
            }
            committed = self._views(self._committed_buffer)
            trial = self._views(self._trial_buffer)
            copied_element_fields = 0
            for field_name in _CORE_FIELDS:
                field_index = _FIELD_INDEX[field_name]
                missing = self._write_stamps[field_index] != self._serial
                missing = np.logical_or(missing, self._deleted_mask)
                if converted_indices:
                    missing[list(converted_indices)] = True
                if np.any(missing):
                    getattr(trial, field_name)[missing] = getattr(
                        committed, field_name
                    )[missing]
                    copied_element_fields += int(np.count_nonzero(missing))

            next_fallback = dict(self._fallback_committed)
            for element_id, (state, reason) in self._trial_legacy.items():
                index = self.layout.index(element_id)
                if self._deleted_mask[index]:
                    continue
                self._packed_mask[index] = False
                next_fallback[element_id] = _owned_copy(state)
                self._fallback_reasons[element_id] = reason
            self._fallback_committed = next_fallback
            self._present_committed = np.logical_or(
                self._present_committed,
                self._present_trial_stamps == self._serial,
            )

            self._committed_buffer, self._trial_buffer = (
                self._trial_buffer,
                self._committed_buffer,
            )
            self._generation += 1
            self._active_token = None
            self._trial_legacy = {}
            self._metrics["state_commit_count"] += 1
            if copied_element_fields:
                self._metrics["state_bounded_copy_commit_count"] += 1
                self._metrics["state_commit_copied_element_fields"] += copied_element_fields
            else:
                self._metrics["state_swap_commit_count"] += 1
            self._metrics["state_commit_seconds"] += time.perf_counter() - start
            return int(self._generation)

    def discard_trial(self, token: StateTrialToken) -> None:
        """Reject the active trial without copying any constitutive arrays."""

        with self._lock:
            self._require_active(token)
            start = time.perf_counter()
            self._active_token = None
            self._trial_legacy = {}
            self._metrics["state_discard_count"] += 1
            self._metrics["state_discard_seconds"] += time.perf_counter() - start

    def discard(self, token: StateTrialToken) -> None:
        """Short transaction alias for :meth:`discard_trial`."""

        self.discard_trial(token)

    def diagnostics(self) -> Dict[str, Any]:
        with self._lock:
            fallback_reasons: Dict[str, list[int]] = {}
            for element_id, reason in self._fallback_reasons.items():
                if not self._packed_mask[self.layout.index(element_id)]:
                    fallback_reasons.setdefault(reason, []).append(int(element_id))
            for element_ids in fallback_reasons.values():
                element_ids.sort()
            return {
                "state_batch_count": 1,
                "state_point_count": int(self.layout.state_point_count),
                "state_buffer_bytes": int(
                    self._committed_buffer.nbytes + self._trial_buffer.nbytes
                ),
                "state_pack_seconds": float(self._metrics["state_pack_seconds"]),
                "state_trial_update_seconds": float(
                    self._metrics["state_trial_update_seconds"]
                ),
                "state_commit_seconds": float(self._metrics["state_commit_seconds"]),
                "state_discard_seconds": float(self._metrics["state_discard_seconds"]),
                "state_materialization_seconds": float(
                    self._metrics["state_materialization_seconds"]
                ),
                "dictionary_fallback_element_count": len(self.fallback_element_ids),
                "dictionary_fallback_reasons": fallback_reasons,
                "deleted_element_count": int(np.count_nonzero(self._deleted_mask)),
                "committed_present_element_count": int(
                    np.count_nonzero(self._present_committed)
                ),
                "generation": int(self._generation),
                **{
                    key: (_owned_copy(value) if isinstance(value, dict) else int(value))
                    for key, value in self._metrics.items()
                    if key
                    not in {
                        "state_pack_seconds",
                        "state_trial_update_seconds",
                        "state_commit_seconds",
                        "state_discard_seconds",
                        "state_materialization_seconds",
                    }
                },
            }

    def __getitem__(self, element_id: int) -> Any:
        key = int(element_id)
        return self.materialize(element_ids=(key,))[key]

    def __iter__(self) -> Iterator[int]:
        return (
            element_id
            for index, element_id in enumerate(self.layout.element_ids)
            if bool(self._present_committed[index])
        )

    def __len__(self) -> int:
        return int(np.count_nonzero(self._present_committed))


class NonlinearStateStore(Mapping[int, Any]):
    """Solver-owned transaction coordinator for multiple state batches."""

    def __init__(self) -> None:
        self._owner = object()
        self._lock = threading.RLock()
        self._batches: Dict[Hashable, ShellStateBatch] = {}
        self._element_to_batch: Dict[int, Hashable] = {}
        self._fallback_committed: Dict[int, Any] = {}
        self._fallback_sidecars: Dict[int, Mapping[str, Any]] = {}
        self._deleted_fallback: set[int] = set()
        self._generation = 0
        self._serial = 0
        self._active_token: Optional[StateTrialToken] = None
        self._batch_trial_tokens: Dict[Hashable, StateTrialToken] = {}
        self._fallback_trial: Dict[int, Any] = {}
        self._pack_seconds = 0.0
        self._trial_update_seconds = 0.0
        self._commit_seconds = 0.0
        self._discard_seconds = 0.0
        self._materialization_seconds = 0.0
        self._materialization_count = 0
        self._stale_token_errors = 0

    @classmethod
    def from_shell_layouts(
        cls,
        layouts: Sequence[ShellStateLayout],
        committed_states: Optional[Mapping[int, Any]] = None,
    ) -> "NonlinearStateStore":
        store = cls()
        states = committed_states or {}
        consumed: set[int] = set()
        for index, layout in enumerate(layouts):
            store.add_shell_batch(layout, states, batch_key=index)
            consumed.update(layout.element_ids)
        remaining = {
            int(element_id): state
            for element_id, state in states.items()
            if int(element_id) not in consumed
        }
        store.add_dictionary_fallback(remaining)
        return store

    @classmethod
    def pack(
        cls,
        layouts: Sequence[ShellStateLayout],
        committed_states: Optional[Mapping[int, Any]] = None,
    ) -> "NonlinearStateStore":
        """Pack shell layouts and preserve every unbatched state as fallback."""

        return cls.from_shell_layouts(layouts, committed_states)

    @property
    def generation(self) -> int:
        return int(self._generation)

    @property
    def has_active_trial(self) -> bool:
        return self._active_token is not None

    def add_shell_batch(
        self,
        layout: ShellStateLayout,
        committed_states: Optional[Mapping[int, Any]] = None,
        *,
        batch_key: Optional[Hashable] = None,
    ) -> ShellStateBatch:
        with self._lock:
            if self._active_token is not None:
                raise StateTransactionError("Cannot add a shell batch during an active trial")
            key: Hashable = len(self._batches) if batch_key is None else batch_key
            if key in self._batches:
                raise KeyError(f"Duplicate shell-state batch key {key!r}")
            duplicates = set(layout.element_ids).intersection(self._element_to_batch)
            duplicates.update(set(layout.element_ids).intersection(self._fallback_committed))
            if duplicates:
                raise ValueError(f"Element states are already registered: {sorted(duplicates)}")
            batch = ShellStateBatch(layout, committed_states)
            self._batches[key] = batch
            for element_id in layout.element_ids:
                self._element_to_batch[element_id] = key
            return batch

    def add_dictionary_fallback(self, states: Mapping[int, Any]) -> None:
        with self._lock:
            if self._active_token is not None:
                raise StateTransactionError(
                    "Cannot add dictionary fallback states during an active trial"
                )
            start = time.perf_counter()
            for raw_element_id, state in states.items():
                element_id = int(raw_element_id)
                if element_id in self._element_to_batch or element_id in self._fallback_committed:
                    raise ValueError(f"Element state {element_id} is already registered")
                self._fallback_committed[element_id] = _owned_copy(state)
                self._fallback_sidecars[element_id] = _extract_sidecar(state)
            self._pack_seconds += time.perf_counter() - start

    def shell_batch(self, batch_key: Hashable) -> ShellStateBatch:
        return self._batches[batch_key]

    def shell_batch_for_layout(self, layout: ShellStateLayout) -> Optional[ShellStateBatch]:
        if not layout.element_ids:
            return None
        key = self._element_to_batch.get(layout.element_ids[0])
        if key is None:
            return None
        batch = self._batches[key]
        return batch if batch.compatible_with(layout) else None

    def begin_trial(self) -> StateTrialToken:
        with self._lock:
            if self._active_token is not None:
                raise StateTransactionError("A nonlinear-state trial is already active")
            self._serial += 1
            token = StateTrialToken(self._generation, self._serial, self._owner)
            child_tokens: Dict[Hashable, StateTrialToken] = {}
            try:
                for key, batch in self._batches.items():
                    child_tokens[key] = batch.begin_trial()
            except Exception:
                for key, child_token in child_tokens.items():
                    self._batches[key].discard_trial(child_token)
                raise
            self._batch_trial_tokens = child_tokens
            self._fallback_trial = {}
            self._active_token = token
            return token

    def begin(self) -> StateTrialToken:
        """Short transaction alias for :meth:`begin_trial`."""

        return self.begin_trial()

    def active_trial_token(self) -> StateTrialToken:
        """Return the active token for an assembly evaluator."""

        with self._lock:
            if self._active_token is None:
                raise StateTransactionError("No nonlinear-state trial is active")
            return self._active_token

    def replace_trial(self) -> StateTrialToken:
        """Reject any prior candidate and begin another from committed state."""

        with self._lock:
            if self._active_token is not None:
                self.discard_trial(self._active_token)
            return self.begin_trial()

    def _require_active(self, token: StateTrialToken) -> None:
        valid = bool(
            isinstance(token, StateTrialToken)
            and token._owner is self._owner
            and token.generation == self._generation
            and self._active_token is token
        )
        if not valid:
            self._stale_token_errors += 1
            raise StaleStateTokenError(
                "Trial token is stale, belongs to another store, or is not active"
            )

    def update_shell_trial(
        self,
        token: StateTrialToken,
        batch_key: Hashable,
        **fields: Any,
    ) -> int:
        with self._lock:
            self._require_active(token)
            result = self._batches[batch_key].update_trial(
                self._batch_trial_tokens[batch_key],
                **fields,
            )
            return result

    def shell_trial_for_layout(
        self,
        token: StateTrialToken,
        layout: ShellStateLayout,
    ) -> Optional[tuple[ShellStateBatch, StateTrialToken]]:
        """Resolve a registered batch and its child transaction token."""

        with self._lock:
            self._require_active(token)
            batch = self.shell_batch_for_layout(layout)
            if batch is None:
                return None
            key = self._element_to_batch[layout.element_ids[0]]
            return batch, self._batch_trial_tokens[key]

    def _validate_fallback_sidecar(self, element_id: int, state: Any) -> Any:
        sidecar = self._fallback_sidecars.get(element_id, MappingProxyType({}))
        if not isinstance(state, Mapping):
            if sidecar:
                raise ImmutableStateSidecarError(
                    "A state carrying immutable initial fields must remain a mapping"
                )
            return _owned_copy(state)
        result = _owned_copy(dict(state))
        for key in result:
            if _is_sidecar_key(str(key)) and str(key) not in sidecar:
                raise ImmutableStateSidecarError(
                    f"Trial update cannot introduce immutable sidecar {key!r}"
                )
        for key, frozen_value in sidecar.items():
            expected = _thaw_value(frozen_value)
            if key in result and not _state_values_equal(result[key], expected):
                raise ImmutableStateSidecarError(
                    f"Trial update cannot modify immutable sidecar {key!r}"
                )
            result[key] = expected
        return result

    def set_trial_state(
        self,
        token: StateTrialToken,
        element_id: int,
        state: Any,
    ) -> None:
        with self._lock:
            self._require_active(token)
            key = int(element_id)
            start = time.perf_counter()
            batch_key = self._element_to_batch.get(key)
            if batch_key is not None:
                self._batches[batch_key].set_trial_state(
                    self._batch_trial_tokens[batch_key], key, state
                )
            elif key in self._fallback_committed:
                if key not in self._deleted_fallback:
                    self._fallback_trial[key] = self._validate_fallback_sidecar(key, state)
                    self._trial_update_seconds += time.perf_counter() - start
            else:
                # Scalar/non-shell elements can acquire their first material
                # history during this candidate.  It becomes visible only if
                # the enclosing increment is committed.
                self._fallback_trial[key] = _owned_copy(state)
                self._trial_update_seconds += time.perf_counter() - start

    def set_trial_states(
        self,
        token: StateTrialToken,
        states: Mapping[int, Any],
    ) -> None:
        for element_id, state in states.items():
            self.set_trial_state(token, int(element_id), state)

    def freeze_deleted(self, element_ids: Sequence[int]) -> None:
        with self._lock:
            by_batch: Dict[Hashable, list[int]] = {}
            for raw_element_id in element_ids:
                element_id = int(raw_element_id)
                batch_key = self._element_to_batch.get(element_id)
                if batch_key is not None:
                    by_batch.setdefault(batch_key, []).append(element_id)
                elif element_id in self._fallback_committed:
                    self._deleted_fallback.add(element_id)
                else:
                    raise KeyError(f"Element state {element_id} is not registered")
            for batch_key, ids in by_batch.items():
                self._batches[batch_key].freeze_deleted(ids)

    def commit(self, token: StateTrialToken) -> int:
        with self._lock:
            self._require_active(token)
            # Validate every child before the first pointer swap for atomicity.
            for key, batch in self._batches.items():
                batch._require_active(self._batch_trial_tokens[key])
            start = time.perf_counter()
            for key, batch in self._batches.items():
                batch.commit(self._batch_trial_tokens[key])
            if self._fallback_trial:
                next_fallback = dict(self._fallback_committed)
                next_fallback.update(
                    {
                        element_id: _owned_copy(state)
                        for element_id, state in self._fallback_trial.items()
                        if element_id not in self._deleted_fallback
                    }
                )
                self._fallback_committed = next_fallback
                for element_id, state in self._fallback_trial.items():
                    if element_id not in self._fallback_sidecars:
                        self._fallback_sidecars[element_id] = _extract_sidecar(state)
            self._generation += 1
            self._active_token = None
            self._batch_trial_tokens = {}
            self._fallback_trial = {}
            self._commit_seconds += time.perf_counter() - start
            return int(self._generation)

    def discard_trial(self, token: StateTrialToken) -> None:
        with self._lock:
            self._require_active(token)
            start = time.perf_counter()
            for key, batch in self._batches.items():
                batch.discard_trial(self._batch_trial_tokens[key])
            self._active_token = None
            self._batch_trial_tokens = {}
            self._fallback_trial = {}
            self._discard_seconds += time.perf_counter() - start

    def discard(self, token: StateTrialToken) -> None:
        """Short transaction alias for :meth:`discard_trial`."""

        self.discard_trial(token)

    def materialize(
        self,
        *,
        trial_token: Optional[StateTrialToken] = None,
        policy: StateMaterializationPolicy | str = StateMaterializationPolicy.EXPLICIT,
    ) -> Dict[int, Any]:
        with self._lock:
            if trial_token is not None:
                self._require_active(trial_token)
            start = time.perf_counter()
            result: Dict[int, Any] = {}
            for key, batch in self._batches.items():
                result.update(
                    batch.materialize(
                        trial_token=(
                            self._batch_trial_tokens[key]
                            if trial_token is not None
                            else None
                        ),
                        policy=policy,
                    )
                )
            for element_id, state in self._fallback_committed.items():
                source = (
                    self._fallback_trial[element_id]
                    if trial_token is not None and element_id in self._fallback_trial
                    else state
                )
                result[element_id] = _owned_copy(source)
            if trial_token is not None:
                for element_id, state in self._fallback_trial.items():
                    if element_id not in result:
                        result[element_id] = _owned_copy(state)
            self._materialization_seconds += time.perf_counter() - start
            self._materialization_count += 1
            return result

    def trial_view(self, token: StateTrialToken) -> "NonlinearStateTrialView":
        with self._lock:
            self._require_active(token)
            return NonlinearStateTrialView(self, token)

    def _trial_keys(self, token: StateTrialToken) -> tuple[int, ...]:
        self._require_active(token)
        keys: list[int] = []
        for batch_key, batch in self._batches.items():
            child_token = self._batch_trial_tokens[batch_key]
            for index, element_id in enumerate(batch.layout.element_ids):
                if batch._is_present(index, child_token):
                    keys.append(element_id)
        keys.extend(
            element_id
            for element_id in self._fallback_committed
            if element_id not in keys
        )
        keys.extend(
            element_id
            for element_id in self._fallback_trial
            if element_id not in keys
        )
        return tuple(keys)

    def _materialize_trial_element(
        self,
        token: StateTrialToken,
        element_id: int,
    ) -> Any:
        with self._lock:
            self._require_active(token)
            key = int(element_id)
            batch_key = self._element_to_batch.get(key)
            if batch_key is not None:
                child_token = self._batch_trial_tokens[batch_key]
                result = self._batches[batch_key].materialize(
                    element_ids=(key,),
                    trial_token=child_token,
                )
                try:
                    return result[key]
                except KeyError as exc:
                    raise KeyError(key) from exc
            if key in self._fallback_trial:
                return _owned_copy(self._fallback_trial[key])
            try:
                return _owned_copy(self._fallback_committed[key])
            except KeyError as exc:
                raise KeyError(key) from exc

    def materialize_owned(
        self,
        *,
        trial_token: Optional[StateTrialToken] = None,
        policy: StateMaterializationPolicy | str = StateMaterializationPolicy.EXPLICIT,
    ) -> Dict[int, Any]:
        """Explicitly named alias emphasizing the ownership guarantee."""

        return self.materialize(trial_token=trial_token, policy=policy)

    def max_equivalent_plastic_strain(self) -> float:
        """Return the committed alpha envelope without public materialization.

        Accepted-increment progress reporting needs this scalar frequently.  A
        direct reduction keeps the normal lifecycle entirely in solver-owned
        arrays; dictionary fallbacks are inspected in place and remain exact.
        """

        with self._lock:
            maximum = 0.0
            for batch in self._batches.values():
                packed_present = np.logical_and(
                    batch._packed_mask,
                    batch._present_committed,
                )
                if np.any(packed_present):
                    alpha = batch._views(batch._committed_buffer).alpha[packed_present]
                    if alpha.size:
                        maximum = max(maximum, float(np.max(alpha)))
                for element_id, state in batch._fallback_committed.items():
                    index = batch.layout.index(element_id)
                    if not batch._present_committed[index]:
                        continue
                    if isinstance(state, Mapping):
                        alpha = np.asarray(state.get("alpha", ()), dtype=float)
                        if alpha.size:
                            maximum = max(maximum, float(np.max(alpha)))
            for state in self._fallback_committed.values():
                if isinstance(state, Mapping):
                    alpha = np.asarray(state.get("alpha", ()), dtype=float)
                    if alpha.size:
                        maximum = max(maximum, float(np.max(alpha)))
            return float(maximum)

    def diagnostics(self) -> Dict[str, Any]:
        with self._lock:
            batch_diagnostics = [
                batch.diagnostics() for batch in self._batches.values()
            ]
            fallback_reasons: Dict[str, list[int]] = {
                "unbatched_element_state": sorted(self._fallback_committed)
            }
            for diagnostic in batch_diagnostics:
                for reason, element_ids in diagnostic[
                    "dictionary_fallback_reasons"
                ].items():
                    fallback_reasons.setdefault(reason, []).extend(element_ids)
            fallback_reasons = {
                reason: sorted(set(ids))
                for reason, ids in fallback_reasons.items()
                if ids
            }
            return {
                "state_batch_count": len(self._batches),
                "state_point_count": int(
                    sum(item["state_point_count"] for item in batch_diagnostics)
                ),
                "state_buffer_bytes": int(
                    sum(item["state_buffer_bytes"] for item in batch_diagnostics)
                ),
                "state_pack_seconds": float(
                    self._pack_seconds
                    + sum(item["state_pack_seconds"] for item in batch_diagnostics)
                ),
                "state_trial_update_seconds": float(
                    self._trial_update_seconds
                    + sum(
                        item["state_trial_update_seconds"]
                        for item in batch_diagnostics
                    )
                ),
                "state_commit_seconds": float(
                    self._commit_seconds
                ),
                "state_discard_seconds": float(
                    self._discard_seconds
                ),
                "state_materialization_seconds": float(
                    self._materialization_seconds
                ),
                "state_materialization_count": int(
                    self._materialization_count
                ),
                "dictionary_fallback_element_count": int(
                    len(self._fallback_committed)
                    + sum(
                        item["dictionary_fallback_element_count"]
                        for item in batch_diagnostics
                    )
                ),
                "dictionary_fallback_reasons": fallback_reasons,
                "deleted_element_count": int(
                    len(self._deleted_fallback)
                    + sum(item["deleted_element_count"] for item in batch_diagnostics)
                ),
                "generation": int(self._generation),
                "stale_token_error_count": int(
                    self._stale_token_errors
                    + sum(item["stale_token_error_count"] for item in batch_diagnostics)
                ),
                "shell_batches": batch_diagnostics,
            }

    def __getitem__(self, element_id: int) -> Any:
        key = int(element_id)
        batch_key = self._element_to_batch.get(key)
        if batch_key is not None:
            return self._batches[batch_key][key]
        try:
            return _owned_copy(self._fallback_committed[key])
        except KeyError as exc:
            raise KeyError(key) from exc

    def __iter__(self) -> Iterator[int]:
        for batch in self._batches.values():
            yield from batch
        yield from self._fallback_committed

    def __len__(self) -> int:
        return sum(len(batch) for batch in self._batches.values()) + len(
            self._fallback_committed
        )

    def __deepcopy__(self, memo: Dict[int, Any]) -> Dict[int, Any]:
        del memo
        return self.materialize_owned()


class NonlinearStateTrialView(Mapping[int, Any]):
    """Owned-on-access mapping for one uncommitted candidate generation."""

    def __init__(self, store: NonlinearStateStore, token: StateTrialToken) -> None:
        self._store = store
        self._token = token

    @property
    def store(self) -> NonlinearStateStore:
        return self._store

    @property
    def token(self) -> StateTrialToken:
        return self._token

    def commit(self) -> NonlinearStateStore:
        self._store.commit(self._token)
        return self._store

    def discard(self) -> None:
        self._store.discard_trial(self._token)

    def materialize_owned(
        self,
        *,
        policy: StateMaterializationPolicy | str = StateMaterializationPolicy.EXPLICIT,
    ) -> Dict[int, Any]:
        return self._store.materialize(trial_token=self._token, policy=policy)

    def __getitem__(self, element_id: int) -> Any:
        return self._store._materialize_trial_element(
            self._token,
            int(element_id),
        )

    def __iter__(self) -> Iterator[int]:
        return iter(self._store._trial_keys(self._token))

    def __len__(self) -> int:
        return len(self._store._trial_keys(self._token))

    def __deepcopy__(self, memo: Dict[int, Any]) -> Dict[int, Any]:
        del memo
        return self.materialize_owned()


def begin_state_evaluation(
    committed_states: Mapping[int, Any],
) -> Optional[StateTrialToken]:
    """Begin a fresh candidate when ``committed_states`` is persistent."""

    if isinstance(committed_states, NonlinearStateStore):
        return committed_states.replace_trial()
    return None


def finish_state_evaluation(
    committed_states: Mapping[int, Any],
    token: Optional[StateTrialToken],
    legacy_trial_states: Mapping[int, Any],
) -> Mapping[int, Any]:
    """Route scalar fallbacks into a store and return a lazy trial mapping."""

    if not isinstance(committed_states, NonlinearStateStore):
        return dict(legacy_trial_states)
    if token is None:
        raise StateTransactionError("Persistent state evaluation has no trial token")
    committed_states.set_trial_states(token, legacy_trial_states)
    return committed_states.trial_view(token)


def commit_state_candidate(
    committed_states: Mapping[int, Any],
    candidate_states: Mapping[int, Any],
) -> Mapping[int, Any]:
    """Commit a lazy candidate or preserve the legacy mapping assignment."""

    if isinstance(committed_states, NonlinearStateStore):
        if not isinstance(candidate_states, NonlinearStateTrialView):
            raise StateTransactionError(
                "Persistent committed state requires a persistent trial candidate"
            )
        if candidate_states.store is not committed_states:
            raise StateTransactionError("Candidate belongs to another state store")
        return candidate_states.commit()
    return candidate_states


def discard_active_state_candidate(committed_states: Mapping[int, Any]) -> None:
    """Discard a pending persistent candidate, if any."""

    if isinstance(committed_states, NonlinearStateStore) and committed_states.has_active_trial:
        committed_states.discard_trial(committed_states.active_trial_token())


def materialize_state_mapping(
    states: Mapping[int, Any],
    *,
    policy: StateMaterializationPolicy | str = StateMaterializationPolicy.EXPLICIT,
) -> Dict[int, Any]:
    """Return an owned public mapping while preserving ordinary dict behavior."""

    if isinstance(states, NonlinearStateStore):
        discard_active_state_candidate(states)
        return states.materialize_owned(policy=policy)
    if isinstance(states, NonlinearStateTrialView):
        return states.materialize_owned(policy=policy)
    return _owned_copy(dict(states))


__all__ = [
    "ImmutableStateSidecarError",
    "begin_state_evaluation",
    "commit_state_candidate",
    "discard_active_state_candidate",
    "finish_state_evaluation",
    "materialize_state_mapping",
    "NonlinearStateError",
    "NonlinearStateStore",
    "NonlinearStateTrialView",
    "PersistentStateEligibilityError",
    "ShellStateArrays",
    "ShellStateBatch",
    "ShellStateLayout",
    "StaleStateTokenError",
    "StateMaterializationPolicy",
    "StateTransactionError",
    "StateTrialToken",
]
