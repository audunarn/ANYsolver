"""Bounded algorithmic proposals for a supported augmented pressure space.

The caller supplies the equilibrated normalized-gap response to multipliers.
This module never accepts a mechanical increment or commits physical history.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SupportedSchurProposal:
    multipliers: np.ndarray
    active_indices: tuple[int, ...]
    scaled_condition: float | None
    step_fraction: float
    predicted_residual_before: float
    predicted_residual_after: float


def propose_supported_schur_step(
    multipliers: np.ndarray,
    normalized_gap: np.ndarray,
    supported: np.ndarray,
    equilibrated_gap_response: np.ndarray,
    *,
    normal_stiffness: float,
    maximum_pressure: float,
    maximum_pressure_step: float,
    maximum_modes: int,
    diagnostics: dict[str, object] | None = None,
) -> SupportedSchurProposal | None:
    """Propose one projected-root Newton step on a stable active branch.

    On an active branch, ``R=max(0,lambda-epsilon*g)-lambda`` has derivative
    ``-epsilon*H`` where ``H=dg_equilibrated/dlambda``.  Inactive rows have
    derivative ``-I``.  A bounded backtracking trial must reduce the linearized
    projected residual without changing the active set.  The analysis owner
    must re-equilibrate and verify the actual residual and physical gap.
    """

    lam = np.asarray(multipliers, dtype=float).reshape(-1)
    gap = np.asarray(normalized_gap, dtype=float).reshape(-1)
    mask = np.asarray(supported, dtype=bool).reshape(-1)
    modes = np.flatnonzero(mask)
    count = len(modes)
    H = np.asarray(equilibrated_gap_response, dtype=float)
    if (gap.shape != lam.shape or mask.shape != lam.shape
            or H.shape != (count, count)
            or not all(np.all(np.isfinite(item)) for item in (lam, gap, H))
            or np.any(lam < 0.0) or np.any(lam[~mask] != 0.0)
            or type(maximum_modes) is not int or maximum_modes < 1):
        raise ValueError("supported Schur inputs are inconsistent")
    for name, value in (("normal_stiffness", normal_stiffness),
                        ("maximum_pressure", maximum_pressure),
                        ("maximum_pressure_step", maximum_pressure_step)):
        if not np.isfinite(value) or value <= 0.0:
            raise ValueError(f"{name} must be finite and positive")
    if count > maximum_modes:
        raise MemoryError("supported pressure modes exceed the declared Schur cap")
    def decline(reason: str) -> None:
        if diagnostics is not None:
            diagnostics["schur_ineligible"] = reason
        return None

    if not count:
        return decline("no_supported_pressure_modes")
    pressure = lam[modes]
    physical_gap = gap[modes]
    projected_argument = pressure - normal_stiffness*physical_gap
    roundoff = 64.0*np.finfo(float).eps*max(
        1.0, maximum_pressure, float(np.max(np.abs(projected_argument))),
    )
    if np.any(np.abs(projected_argument) <= roundoff):
        return decline("projected_active_set_kink")
    active = projected_argument > 0.0
    residual = np.maximum(0.0, projected_argument) - pressure
    before = float(np.linalg.norm(residual, ord=np.inf))
    if before == 0.0:
        return decline("projected_residual_zero")
    jacobian = -np.eye(count)
    jacobian[active] = -normal_stiffness*H[active]
    row_magnitude = np.max(np.abs(jacobian), axis=1)
    row_scale = np.where(row_magnitude > 0.0, row_magnitude, 1.0)
    column_magnitude = np.max(np.abs(jacobian/row_scale[:, None]), axis=0)
    column_scale = np.where(column_magnitude > 0.0, column_magnitude, 1.0)
    scaled = jacobian/row_scale[:, None]/column_scale[None, :]
    try:
        left_modes, singular_values, right_modes = np.linalg.svd(scaled)
        condition = (float(singular_values[0]/singular_values[-1])
                     if singular_values[-1] > 0.0 else float("inf"))
        if diagnostics is not None:
            diagnostics["schur_scaled_condition"] = (
                condition if np.isfinite(condition) else None
            )
            diagnostics["schur_scaled_singular_values"] = list(
                map(float, singular_values))
            scaled_rhs = -residual/row_scale
            modal_rhs = left_modes.T @ scaled_rhs
            diagnostics["schur_scaled_rhs_modal"] = list(map(float, modal_rhs))
            diagnostics["schur_scaled_weak_right_mode"] = list(
                map(float, right_modes[-1]))
            diagnostics["schur_scaled_weak_rhs_fraction"] = float(
                abs(modal_rhs[-1])/max(np.linalg.norm(scaled_rhs),
                                        np.finfo(float).tiny)
            )
        if not np.isfinite(singular_values[0]) or singular_values[0] <= 0.0:
            return decline("scaled_response_singular")
        retained = singular_values > singular_values[0]/1.0e8
        rank = int(np.count_nonzero(retained))
        if diagnostics is not None:
            diagnostics["schur_effective_rank"] = rank
            diagnostics["schur_truncated_response"] = rank < count
        if rank == 0:
            return decline("scaled_response_singular")
        if rank < count:
            direction = (
                right_modes[:rank].T
                @ ((left_modes[:, :rank].T @ (-residual/row_scale))
                   / singular_values[:rank])
            )/column_scale
        else:
            direction = np.linalg.solve(scaled, -residual/row_scale)/column_scale
    except np.linalg.LinAlgError:
        return decline("scaled_response_singular")
    if not np.all(np.isfinite(direction)):
        return decline("nonfinite_pressure_direction")
    for halvings in range(9):
        fraction = 0.5**halvings
        step = fraction*direction
        candidate = pressure + step
        if (np.max(np.abs(step)) > maximum_pressure_step
                or np.any(candidate < 0.0)
                or np.max(candidate) > maximum_pressure):
            continue
        predicted_gap = physical_gap + H @ step
        predicted_argument = candidate - normal_stiffness*predicted_gap
        if np.any((predicted_argument > 0.0) != active):
            continue
        after = float(np.linalg.norm(
            np.maximum(0.0, predicted_argument)-candidate,
            ord=np.inf,
        ))
        if after >= (1.0-1.0e-4*fraction)*before:
            continue
        proposed = lam.copy()
        proposed[modes] = candidate
        return SupportedSchurProposal(
            proposed, tuple(int(modes[index]) for index in np.flatnonzero(active)),
            condition if np.isfinite(condition) else None,
            fraction, before, after,
        )
    return decline("bounded_step_or_predicted_merit_failed")
