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
