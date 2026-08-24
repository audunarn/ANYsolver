"""Typed result-quantity descriptors for solver/UI interchange.

The descriptors intentionally describe *available* arrays rather than
inventing zero-valued fields.  They are small, serializable contracts that a
postprocessor can use to build its tree without hard-coding each result class.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Mapping, Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class ResultQuantity:
    """Metadata for one result field or history."""

    quantity_id: str
    label: str
    location: str
    components: Tuple[str, ...]
    unit: str
    basis: str = "global"
    frame_count: int = 1
    has_history: bool = False
    data_path: str = ""
    recovery: str = "native"
    availability: str = "available"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.quantity_id:
            raise ValueError("quantity_id must not be empty")
        if self.frame_count < 0:
            raise ValueError("frame_count must be non-negative")
        object.__setattr__(self, "components", tuple(str(value) for value in self.components))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["components"] = list(self.components)
        payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(frozen=True)
class ResolvedResultQuantity:
    """One available descriptor paired with its authoritative data."""

    descriptor: ResultQuantity
    data: Any


class QuantityUnavailableError(LookupError):
    """Raised when a result genuinely carries no requested quantity."""


@dataclass(frozen=True)
class ReactionFrame:
    """Nodal and support reactions at one committed result frame."""

    frame_index: int
    abscissa: float
    abscissa_kind: str
    reactions: Mapping[int, Any]
    support_resultants: Mapping[str, Any]


_REGISTERED_QUANTITY_IDS = (
    "displacement",
    "velocity",
    "acceleration",
    "stress",
    "stress_history",
    "reaction",
    "reaction_history",
    "equivalent_plastic_strain",
    "equivalent_plastic_strain_history",
    "load_factor",
    "mode_shape",
    "frequency",
    "buckling_factor",
    "time",
    "contact_force",
    "impactor_position",
    "force_impulse",
    "moment_impulse",
    "load_impulse",
    "kinetic_energy",
    "strain_energy",
    "internal_work",
    "impactor_kinetic_energy",
    "displacement_envelope",
    "velocity_envelope",
    "acceleration_envelope",
)


def registered_result_quantity_ids() -> Tuple[str, ...]:
    """Stable canonical IDs that callers may resolve fail-closed."""

    return _REGISTERED_QUANTITY_IDS


def _array_frames(value: Any, *, default: int = 1) -> int:
    if value is None:
        return 0
    array = np.asarray(value)
    if array.ndim >= 2:
        return int(array.shape[0])
    return int(default)


def _stress_components(result: Any) -> Tuple[str, ...]:
    components = set()
    element_stresses = getattr(result, "element_stresses", None)
    if isinstance(element_stresses, Mapping):
        for values in element_stresses.values():
            if isinstance(values, Mapping):
                components.update(str(component) for component in values)
    return tuple(sorted(components))


def describe_result_quantities(result: Any) -> Tuple[ResultQuantity, ...]:
    """Return typed descriptors for arrays actually available on ``result``.

    The function is deliberately duck-typed so sidecar readers and downstream
    adapters can participate without inheriting solver result classes.
    """

    quantities = []
    class_name = type(result).__name__

    displacements = getattr(result, "displacements", None)
    snapshots = tuple(getattr(result, "snapshots", ()) or ())
    if displacements is not None and np.asarray(displacements).size > 0:
        frames = len(snapshots) if snapshots else _array_frames(displacements)
        history_mode = str(getattr(result, "history_storage_mode", "full"))
        quantities.append(
            ResultQuantity(
                "displacement",
                "Displacement",
                "node",
                ("UX", "UY", "UZ", "RX", "RY", "RZ"),
                "mixed:m,rad",
                frame_count=frames,
                has_history=frames > 1,
                data_path="snapshots[].displacements" if snapshots else "displacements",
                recovery="committed_state" if snapshots else "native",
                metadata={
                    "history_storage_mode": history_mode,
                    "committed_state_snapshots": bool(snapshots),
                },
            )
        )

    if getattr(result, "velocities", None) is not None and np.asarray(result.velocities).size > 0:
        frames = _array_frames(result.velocities)
        quantities.append(
            ResultQuantity(
                "velocity",
                "Velocity",
                "node",
                ("VX", "VY", "VZ", "WX", "WY", "WZ"),
                "mixed:m/s,rad/s",
                frame_count=frames,
                has_history=True,
                data_path="velocities",
            )
        )
    if getattr(result, "accelerations", None) is not None and np.asarray(result.accelerations).size > 0:
        frames = _array_frames(result.accelerations)
        quantities.append(
            ResultQuantity(
                "acceleration",
                "Acceleration",
                "node",
                ("AX", "AY", "AZ", "ALPHAX", "ALPHAY", "ALPHAZ"),
                "mixed:m/s^2,rad/s^2",
                frame_count=frames,
                has_history=True,
                data_path="accelerations",
            )
        )

    stress_components = _stress_components(result)
    if stress_components:
        quantities.append(
            ResultQuantity(
                "stress",
                "Stress",
                "element",
                stress_components,
                "Pa",
                basis="element_local",
                data_path="element_stresses",
                recovery="recovered",
            )
        )
    stress_history = getattr(result, "stress_history", None)
    if stress_history is not None and len(stress_history) > 0:
        quantities.append(
            ResultQuantity(
                "stress_history",
                "Stress history",
                "element",
                (),
                "Pa",
                basis="element_local",
                frame_count=len(stress_history),
                has_history=True,
                data_path="stress_history",
                recovery="recovered",
            )
        )
    reactions = getattr(result, "reactions", None)
    if isinstance(reactions, Mapping) and reactions:
        quantities.append(
            ResultQuantity(
                "reaction",
                "Reaction",
                "node",
                ("FX", "FY", "FZ", "MX", "MY", "MZ"),
                "mixed:N,N*m",
                data_path="reactions",
            )
        )

    steps = getattr(result, "steps", None)
    if steps is not None and len(steps) > 0:
        quantities.append(
            ResultQuantity(
                "load_factor",
                "Load factor",
                "global",
                ("FACTOR",),
                "1",
                frame_count=len(steps),
                has_history=True,
                data_path="steps[].load_factor",
            )
        )

    modes = getattr(result, "modes", None)
    if modes is not None and len(modes) > 0:
        mode_components = ("UX", "UY", "UZ", "RX", "RY", "RZ")
        quantities.append(
            ResultQuantity(
                "mode_shape",
                "Mode shape",
                "node",
                mode_components,
                "normalized",
                frame_count=len(modes),
                has_history=len(modes) > 1,
                data_path="modes[].mode_shape",
            )
        )
        if class_name == "ModalResult":
            quantities.append(ResultQuantity("frequency", "Frequency", "global", ("F",), "Hz", frame_count=len(modes), has_history=True, data_path="modes[].frequency_hz"))
        elif class_name == "BucklingResult":
            quantities.append(ResultQuantity("buckling_factor", "Buckling factor", "global", ("FACTOR",), "1", frame_count=len(modes), has_history=True, data_path="modes[].load_factor"))

    times = getattr(result, "times", None)
    if times is not None:
        quantities.append(
            ResultQuantity(
                "time",
                "Time",
                "global",
                ("T",),
                "s",
                frame_count=int(np.asarray(times).size),
                has_history=True,
                data_path="times",
            )
        )
    if getattr(result, "contact_force_history", None) is not None:
        quantities.append(
            ResultQuantity(
                "contact_force",
                "Contact force",
                "contact",
                ("FX", "FY", "FZ"),
                "N",
                frame_count=_array_frames(result.contact_force_history),
                has_history=True,
                data_path="contact_force_history",
            )
        )
    if getattr(result, "sphere_positions", None) is not None:
        quantities.append(ResultQuantity("impactor_position", "Impactor position", "contact", ("X", "Y", "Z"), "m", frame_count=_array_frames(result.sphere_positions), has_history=True, data_path="sphere_positions"))
    if getattr(result, "force_impulse", None) is not None:
        quantities.append(ResultQuantity("force_impulse", "Force impulse", "global", ("IX", "IY", "IZ"), "N*s", data_path="force_impulse"))
    if getattr(result, "moment_impulse", None) is not None:
        quantities.append(ResultQuantity("moment_impulse", "Moment impulse", "global", ("IX", "IY", "IZ"), "N*m*s", data_path="moment_impulse"))

    for attribute, quantity_id, label, unit in (
        ("displacement_envelope", "displacement_envelope", "Displacement envelope", "mixed:m,rad"),
        ("velocity_envelope", "velocity_envelope", "Velocity envelope", "mixed:m/s,rad/s"),
        ("acceleration_envelope", "acceleration_envelope", "Acceleration envelope", "mixed:m/s^2,rad/s^2"),
    ):
        values = getattr(result, attribute, None)
        if values is not None and np.asarray(values).size > 0:
            quantities.append(
                ResultQuantity(
                    quantity_id,
                    label,
                    "node",
                    ("X", "Y", "Z", "RX", "RY", "RZ"),
                    unit,
                    data_path=attribute,
                    recovery="envelope",
                )
            )

    return tuple(quantities)


def _resolved(descriptor: ResultQuantity, data: Any) -> ResolvedResultQuantity:
    return ResolvedResultQuantity(descriptor=descriptor, data=data)


def _nonempty_array(value: Any) -> bool:
    if value is None:
        return False
    try:
        return bool(np.asarray(value).size)
    except (TypeError, ValueError):
        return False


def _described_data(result: Any, quantity_id: str) -> Any:
    attribute_by_id = {
        "displacement": "displacements",
        "velocity": "velocities",
        "acceleration": "accelerations",
        "stress": "element_stresses",
        "stress_history": "stress_history",
        "reaction": "reactions",
        "time": "times",
        "contact_force": "contact_force_history",
        "impactor_position": "sphere_positions",
        "force_impulse": "force_impulse",
        "moment_impulse": "moment_impulse",
        "displacement_envelope": "displacement_envelope",
        "velocity_envelope": "velocity_envelope",
        "acceleration_envelope": "acceleration_envelope",
    }
    attribute = attribute_by_id.get(quantity_id)
    if attribute is not None:
        return getattr(result, attribute, None)
    if quantity_id == "load_factor":
        return tuple(getattr(step, "load_factor", None) for step in result.steps)
    if quantity_id == "mode_shape":
        return tuple(getattr(mode, "mode_shape", None) for mode in result.modes)
    if quantity_id == "frequency":
        return tuple(getattr(mode, "frequency_hz", None) for mode in result.modes)
    if quantity_id == "buckling_factor":
        return tuple(getattr(mode, "load_factor", None) for mode in result.modes)
    return None


def _state_peeq(state: Any) -> float | None:
    if not isinstance(state, Mapping):
        return None
    for key in (
        "equivalent_plastic_strain",
        "max_equivalent_plastic_strain",
        "peeq",
        "alpha",
    ):
        value = state.get(key)
        if value is None:
            continue
        try:
            values = np.asarray(value, dtype=float)
        except (TypeError, ValueError):
            continue
        if values.size and np.all(np.isfinite(values)):
            return float(np.max(np.abs(values)))
    return None


def _element_peeq(states: Any) -> Dict[int, float]:
    if not isinstance(states, Mapping):
        return {}
    resolved: Dict[int, float] = {}
    for raw_element_id, state in states.items():
        try:
            element_id = int(raw_element_id)
        except (TypeError, ValueError, OverflowError):
            continue
        value = _state_peeq(state)
        if value is not None:
            resolved[element_id] = value
    return resolved


def _plastic_strain_quantity(
    result: Any, quantity_id: str
) -> ResolvedResultQuantity:
    snapshots = tuple(getattr(result, "snapshots", ()) or ())
    if quantity_id == "equivalent_plastic_strain":
        data = _element_peeq(getattr(result, "element_states", None))
        if not data and snapshots:
            data = _element_peeq(getattr(snapshots[-1], "element_states", None))
        if not data:
            raise QuantityUnavailableError("equivalent plastic strain is unavailable")
        descriptor = ResultQuantity(
            quantity_id,
            "Equivalent plastic strain",
            "element",
            ("PEEQ",),
            "1",
            data_path="element_states",
            recovery="committed_state",
            metadata={"reduction": "maximum committed integration-point value"},
        )
        return _resolved(descriptor, data)

    frames = []
    frame_indices = []
    for ordinal, snapshot in enumerate(snapshots):
        data = _element_peeq(getattr(snapshot, "element_states", None))
        if not data:
            continue
        frames.append(data)
        frame_indices.append(int(getattr(snapshot, "step_index", ordinal)))
    if not frames:
        raise QuantityUnavailableError("equivalent plastic strain history is unavailable")
    descriptor = ResultQuantity(
        quantity_id,
        "Equivalent plastic strain history",
        "element",
        ("PEEQ",),
        "1",
        frame_count=len(frames),
        has_history=True,
        data_path="snapshots[].element_states",
        recovery="committed_state",
        metadata={
            "frame_indices": frame_indices,
            "reduction": "maximum committed integration-point value",
        },
    )
    return _resolved(descriptor, tuple(frames))


def _reaction_history_quantity(result: Any) -> ResolvedResultQuantity:
    frames = tuple(getattr(result, "reaction_history", ()) or ())
    if not frames:
        raise QuantityUnavailableError("reaction history is unavailable")
    descriptor = ResultQuantity(
        "reaction_history",
        "Reaction history",
        "node",
        ("FX", "FY", "FZ", "MX", "MY", "MZ"),
        "mixed:N,N*m",
        frame_count=len(frames),
        has_history=True,
        data_path="reaction_history",
        metadata={"abscissa_kind": getattr(frames[0], "abscissa_kind", "frame")},
    )
    return _resolved(descriptor, frames)


def _energy_quantity(result: Any, quantity_id: str) -> ResolvedResultQuantity:
    diagnostics = getattr(result, "diagnostics", None)
    if not isinstance(diagnostics, Mapping):
        raise QuantityUnavailableError(f"{quantity_id} is unavailable")
    measure = str(diagnostics.get("strain_energy_measure", ""))
    if quantity_id == "kinetic_energy":
        source_key = "kinetic_energy"
        label = "Kinetic energy"
    elif quantity_id == "strain_energy":
        if measure != "elastic_strain_energy":
            raise QuantityUnavailableError("elastic strain energy is unavailable")
        source_key = "strain_energy"
        label = "Strain energy"
    elif quantity_id == "internal_work":
        if measure != "internal_work_proxy":
            raise QuantityUnavailableError("internal work is unavailable")
        source_key = "strain_energy"
        label = "Internal work"
    else:
        source_key = "sphere_kinetic_energy"
        label = "Impactor kinetic energy"
    values = diagnostics.get(source_key)
    if not _nonempty_array(values):
        raise QuantityUnavailableError(f"{quantity_id} is unavailable")
    array = np.asarray(values, dtype=float)
    if not np.all(np.isfinite(array)):
        raise QuantityUnavailableError(f"{quantity_id} contains nonfinite values")
    times = getattr(result, "times", None)
    if times is not None and int(np.asarray(times).size) != int(array.size):
        raise QuantityUnavailableError(f"{quantity_id} is not aligned with result frames")
    descriptor = ResultQuantity(
        quantity_id,
        label,
        "global",
        ("VALUE",),
        "J",
        frame_count=int(array.size),
        has_history=True,
        data_path=f"diagnostics.{source_key}",
        metadata={"measure": measure or quantity_id},
    )
    return _resolved(descriptor, values)


def resolve_result_quantity(result: Any, quantity_id: str) -> ResolvedResultQuantity:
    """Resolve one canonical quantity without inventing absent values."""

    key = str(quantity_id)
    if key not in _REGISTERED_QUANTITY_IDS:
        raise QuantityUnavailableError(f"unknown result quantity {key!r}")
    if key in {
        "equivalent_plastic_strain",
        "equivalent_plastic_strain_history",
    }:
        return _plastic_strain_quantity(result, key)
    if key == "reaction_history":
        return _reaction_history_quantity(result)
    if key in {
        "kinetic_energy",
        "strain_energy",
        "internal_work",
        "impactor_kinetic_energy",
    }:
        return _energy_quantity(result, key)
    if key == "load_impulse":
        value = getattr(result, "load_impulse", None)
        if not _nonempty_array(value):
            raise QuantityUnavailableError("load impulse is unavailable")
        descriptor = ResultQuantity(
            key,
            "Load impulse",
            "node",
            ("IX", "IY", "IZ", "IRX", "IRY", "IRZ"),
            "mixed:N*s,N*m*s",
            data_path="load_impulse",
        )
        return _resolved(descriptor, value)

    descriptors = {
        descriptor.quantity_id: descriptor
        for descriptor in describe_result_quantities(result)
    }
    descriptor = descriptors.get(key)
    if descriptor is None:
        raise QuantityUnavailableError(
            f"{type(result).__name__} carries no result quantity {key!r}"
        )
    data = _described_data(result, key)
    if data is None:
        raise QuantityUnavailableError(
            f"{type(result).__name__} carries no data for result quantity {key!r}"
        )
    if isinstance(data, Mapping):
        available = bool(data)
    elif isinstance(data, (tuple, list)):
        available = bool(data) and all(value is not None for value in data)
    else:
        available = _nonempty_array(data)
    if not available:
        raise QuantityUnavailableError(
            f"{type(result).__name__} carries no data for result quantity {key!r}"
        )
    return _resolved(descriptor, data)
