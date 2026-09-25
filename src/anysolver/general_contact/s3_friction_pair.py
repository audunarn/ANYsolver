"""Internal fixed-material S3 pair friction work, with prescribed pressure."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .friction_point import (
    FrictionPointState, FrictionPointTrial,
    objective_relative_tangent_increment,
    objective_relative_tangent_variation,
    trial_coulomb_point,
)
from .s3_friction_point import S3SkinMaterialPoint


@dataclass(frozen=True)
class S3FrictionPairEvaluation:
    trial: FrictionPointTrial
    relative_increment: tuple[float, float, float]
    structural_force: np.ndarray
    slip_map: np.ndarray
    active_columns: tuple[int, ...]


@dataclass(frozen=True)
class S3FrictionPointPair:
    """One fixed material pair; no search, normal law, or public admission."""

    source: S3SkinMaterialPoint
    target: S3SkinMaterialPoint
    reference_weight_m2: float
    friction_coefficient: float
    tangential_stiffness_Pa_per_m: float
    maximum_active_columns: int

    def __post_init__(self) -> None:
        if (not isinstance(self.source, S3SkinMaterialPoint)
                or not isinstance(self.target, S3SkinMaterialPoint)):
            raise TypeError("S3 friction pair needs two physical material points")
        if (self.source.adapter.element_id == self.target.adapter.element_id
                and self.source.adapter.body_id == self.target.adapter.body_id):
            raise ValueError("a fixed S3 friction pair needs distinct material elements")
        if self.source.adapter.work_map.shape[1] != self.target.adapter.work_map.shape[1]:
            raise ValueError("S3 friction points must share structural DOF ownership")
        for name, positive in (("reference_weight_m2", True),
                               ("friction_coefficient", False),
                               ("tangential_stiffness_Pa_per_m", True)):
            value = float(getattr(self, name))
            if not np.isfinite(value) or value < 0.0 or (positive and value == 0.0):
                raise ValueError(f"{name} must be finite and " +
                                 ("positive" if positive else "nonnegative"))
            object.__setattr__(self, name, value)
        if (type(self.maximum_active_columns) is not int
                or self.maximum_active_columns < 1):
            raise ValueError("maximum_active_columns must be a positive integer")

    @property
    def partner_key(self) -> str:
        first, second = self.source, self.target
        return (
            f"s3:{first.adapter.body_id}:{first.adapter.element_id}:"
            f"{first.adapter.side}:{first.barycentric!r}|"
            f"s3:{second.adapter.body_id}:{second.adapter.element_id}:"
            f"{second.adapter.side}:{second.barycentric!r}"
        )

    def evaluate(
        self,
        committed_displacement: np.ndarray,
        candidate_displacement: np.ndarray,
        committed_history: FrictionPointState,
        *,
        normal_pressure_Pa: float,
    ) -> S3FrictionPairEvaluation:
        """Return a disposable candidate and physical nodal force vector.

        The work map is the derivative of the same objective relative slip
        consumed by the traction law. This includes target-frame terms needed
        for zero work under common rigid motion at a separated material pair.
        It does not include the derivative of pressure or a contact tangent.
        """

        if not isinstance(committed_history, FrictionPointState):
            raise TypeError("committed_history must be a FrictionPointState")
        if committed_history.partner_key not in {None, self.partner_key}:
            raise ValueError("friction history belongs to a different material pair")
        source_old = self.source.physical_pose(committed_displacement)
        target_old = self.target.physical_pose(committed_displacement)
        source_new = self.source.physical_pose(candidate_displacement)
        target_new = self.target.physical_pose(candidate_displacement)
        if not np.allclose(
                committed_history.material_frame, target_old.material_frame,
                rtol=0.0, atol=1.0e-9):
            raise ValueError("friction history frame differs from committed target pose")
        relative = objective_relative_tangent_increment(
            source_committed=source_old.position,
            target_committed=target_old.position,
            source_candidate=source_new.position,
            target_candidate=target_new.position,
            target_frame_committed=target_old.material_frame,
            target_frame_candidate=target_new.material_frame,
        )
        trial = trial_coulomb_point(
            committed_history,
            material_frame=target_new.material_frame,
            relative_increment=relative,
            normal_pressure=normal_pressure_Pa,
            friction_coefficient=self.friction_coefficient,
            tangential_stiffness=self.tangential_stiffness_Pa_per_m,
            partner_key=self.partner_key,
        )
        count = self.source.adapter.work_map.shape[1]
        if trial.branch == "open":
            force = np.zeros(count)
            slip_map = np.zeros((3, count))
            force.setflags(write=False)
            slip_map.setflags(write=False)
            return S3FrictionPairEvaluation(
                trial, relative, force, slip_map, (),
            )
        source_map = self.source.position_map
        target_map = self.target.position_map
        slip_map = np.zeros((3, count))
        active = np.unique(np.concatenate((
            source_map.indices,
            target_map.indices,
            self.target.adapter.work_map.indices,
        )))
        if active.size > self.maximum_active_columns:
            raise MemoryError("S3 friction pair active-column budget exceeded")
        for column in active:
            direction = np.zeros(count)
            direction[column] = 1.0
            slip_map[:, column] = objective_relative_tangent_variation(
                source_committed=source_old.position,
                target_committed=target_old.position,
                source_candidate=source_new.position,
                target_candidate=target_new.position,
                target_frame_committed=target_old.material_frame,
                target_frame_candidate=target_new.material_frame,
                source_position_variation=np.asarray(
                    source_map @ direction).reshape(3),
                target_position_variation=np.asarray(
                    target_map @ direction).reshape(3),
                target_frame_variation=(
                    self.target.frame_directional_variation(
                        candidate_displacement, direction,
                    )
                ),
            )
        force = self.reference_weight_m2 * (
            slip_map.T @ np.asarray(trial.traction)
        )
        if not np.all(np.isfinite(force)):
            raise ValueError("S3 friction structural force exceeded finite range")
        force.setflags(write=False)
        slip_map.setflags(write=False)
        return S3FrictionPairEvaluation(
            trial, relative, force, slip_map,
            tuple(int(column) for column in active),
        )
