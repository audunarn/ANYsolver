"""Internal traction-point Coulomb return map for a material surface frame.

The caller owns material-point correspondence and supplies the *relative*
increment in the current spatial frame. Frame columns are material tangent
directions followed by the physical normal. This local law has no public
contact admission until a surface adapter and solver transaction use it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def _vector3(values, name: str) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    if result.shape != (3,) or not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must contain three finite values")
    return result


def _frame3(values) -> np.ndarray:
    result = np.asarray(values, dtype=float)
    if result.shape != (3, 3) or not np.all(np.isfinite(result)):
        raise ValueError("material frame must be a finite 3 by 3 matrix")
    if (not np.allclose(result.T @ result, np.eye(3), rtol=0.0, atol=1.0e-9)
            or not np.isclose(np.linalg.det(result), 1.0,
                              rtol=0.0, atol=1.0e-9)):
        raise ValueError("material frame must be right-handed and orthonormal")
    return result


def _frozen_vector(values: np.ndarray) -> tuple[float, float, float]:
    return tuple(float(value) for value in values)


def _frozen_frame(values: np.ndarray) -> tuple[tuple[float, float, float], ...]:
    return tuple(_frozen_vector(row) for row in values)


@dataclass(frozen=True)
class FrictionPointState:
    """Committed physical history at one persistent material contact point."""

    material_frame: tuple[tuple[float, float, float], ...]
    elastic_slip: tuple[float, float, float]
    partner_key: str | None = None
    cumulative_plastic_slip: float = 0.0
    cumulative_dissipation_density: float = 0.0

    def __post_init__(self) -> None:
        frame = _frame3(self.material_frame)
        elastic = _vector3(self.elastic_slip, "elastic slip")
        if abs(float(elastic @ frame[:, 2])) > (
                1.0e-10 * float(np.linalg.norm(elastic)) + 1.0e-15):
            raise ValueError("elastic slip must be tangent to its material frame")
        if self.partner_key is not None and (
                not isinstance(self.partner_key, str) or not self.partner_key):
            raise ValueError("partner_key must be a nonempty string or None")
        if self.partner_key is None and np.any(elastic):
            raise ValueError("an open friction point cannot retain elastic slip")
        for name in ("cumulative_plastic_slip",
                     "cumulative_dissipation_density"):
            value = float(getattr(self, name))
            if not np.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and nonnegative")
            object.__setattr__(self, name, value)
        object.__setattr__(self, "material_frame", _frozen_frame(frame))
        object.__setattr__(self, "elastic_slip", _frozen_vector(elastic))


@dataclass(frozen=True)
class FrictionPointTrial:
    """Disposable response; commit ``candidate_state`` only with the increment."""

    branch: str
    traction: tuple[float, float, float]
    displacement_tangent: tuple[tuple[float, float, float], ...]
    pressure_derivative: tuple[float, float, float]
    candidate_state: FrictionPointState
    plastic_slip_increment: tuple[float, float, float]
    dissipated_increment_density: float
    stored_energy_density: float
    released_storage_density: float


def initial_friction_point(material_frame) -> FrictionPointState:
    """Zero-traction state, with material axes supplied by the geometry owner."""

    return FrictionPointState(
        _frozen_frame(_frame3(material_frame)), (0.0, 0.0, 0.0),
    )


def trial_coulomb_point(
    committed: FrictionPointState,
    *,
    material_frame,
    relative_increment,
    normal_pressure: float,
    friction_coefficient: float,
    tangential_stiffness: float,
    partner_key: str | None,
) -> FrictionPointTrial:
    """Return the local stick/slip response without mutating committed state.

    Pressure and traction have units Pa, ``relative_increment`` and elastic
    slip have units m, and tangential stiffness has units Pa/m. Traction acts
    on the source and opposes positive source-relative tangential motion.
    Material-frame transport represents rigid rotation, including spin about
    the normal. A changed partner or opening starts later contact with zero
    elastic traction; accumulated slip/dissipation remains reportable.
    """

    if not isinstance(committed, FrictionPointState):
        raise TypeError("committed must be a FrictionPointState")
    frame = _frame3(material_frame)
    increment = _vector3(relative_increment, "relative increment")
    scalars = {}
    for name, value, positive in (
            ("normal_pressure", normal_pressure, False),
            ("friction_coefficient", friction_coefficient, False),
            ("tangential_stiffness", tangential_stiffness, True)):
        try:
            scalar = float(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f"{name} must be a scalar") from error
        if not np.isfinite(scalar) or scalar < 0.0 or (positive and scalar == 0.0):
            raise ValueError(f"{name} must be finite and " +
                             ("positive" if positive else "nonnegative"))
        scalars[name] = scalar
    if scalars["normal_pressure"] > 0.0 and (
            not isinstance(partner_key, str) or not partner_key):
        raise ValueError("active friction requires a persistent partner_key")
    if partner_key is not None and (
            not isinstance(partner_key, str) or not partner_key):
        raise ValueError("partner_key must be a nonempty string or None")

    stiffness = scalars["tangential_stiffness"]
    pressure = scalars["normal_pressure"]
    coefficient = scalars["friction_coefficient"]
    prior_frame = _frame3(committed.material_frame)
    same_partner = (committed.partner_key is not None
                    and committed.partner_key == partner_key)
    prior_elastic = _vector3(committed.elastic_slip, "elastic slip")
    released = (0.0 if same_partner else
                0.5 * stiffness * float(prior_elastic @ prior_elastic))
    old = prior_elastic if same_partner else np.zeros(3)
    material_rotation = frame @ prior_frame.T
    transported = material_rotation @ old
    projector = frame[:, :2] @ frame[:, :2].T
    elastic_trial = projector @ (transported + increment)
    if not np.all(np.isfinite(elastic_trial)):
        raise ValueError("tangential trial slip exceeded finite range")
    zero = np.zeros(3)
    zero_matrix = np.zeros((3, 3))

    if pressure == 0.0:
        # Motion after opening stores no tangential regularization energy.
        released = 0.5 * stiffness * float(prior_elastic @ prior_elastic)
        state = FrictionPointState(
            _frozen_frame(frame), _frozen_vector(zero), None,
            committed.cumulative_plastic_slip,
            committed.cumulative_dissipation_density,
        )
        return FrictionPointTrial(
            "open", _frozen_vector(zero), _frozen_frame(zero_matrix),
            _frozen_vector(zero), state, _frozen_vector(zero),
            0.0, 0.0, released,
        )

    cap = coefficient * pressure
    magnitude = float(np.linalg.norm(elastic_trial))
    if not np.isfinite(cap) or not np.isfinite(magnitude):
        raise ValueError("friction trial exceeded finite range")
    if stiffness * magnitude <= cap:
        elastic = elastic_trial
        traction = -stiffness * elastic
        tangent = -stiffness * projector
        pressure_derivative = zero
        plastic = zero
        dissipated = 0.0
        branch = "stick"
    else:
        direction = elastic_trial / magnitude
        elastic = (cap / stiffness) * direction
        traction = -cap * direction
        tangent = -(cap / magnitude) * (
            projector - np.outer(direction, direction)
        )
        pressure_derivative = -coefficient * direction
        plastic = elastic_trial - elastic
        dissipated = cap * float(np.linalg.norm(plastic))
        branch = "slip"
    state = FrictionPointState(
        _frozen_frame(frame), _frozen_vector(elastic), partner_key,
        committed.cumulative_plastic_slip + float(np.linalg.norm(plastic)),
        committed.cumulative_dissipation_density + dissipated,
    )
    return FrictionPointTrial(
        branch, _frozen_vector(traction), _frozen_frame(tangent),
        _frozen_vector(pressure_derivative), state,
        _frozen_vector(plastic), dissipated,
        0.5 * stiffness * float(elastic @ elastic), released,
    )
