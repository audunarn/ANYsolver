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
    scaled_condition: float
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
    if not count:
        return None
    pressure = lam[modes]
    physical_gap = gap[modes]
    projected_argument = pressure - normal_stiffness*physical_gap
    roundoff = 64.0*np.finfo(float).eps*max(
        1.0, maximum_pressure, float(np.max(np.abs(projected_argument))),
    )
    if np.any(np.abs(projected_argument) <= roundoff):
        return None
    active = projected_argument > 0.0
    residual = np.maximum(0.0, projected_argument) - pressure
    before = float(np.linalg.norm(residual, ord=np.inf))
    if before == 0.0:
        return None
    jacobian = -np.eye(count)
    jacobian[active] = -normal_stiffness*H[active]
    row_scale = np.maximum(np.max(np.abs(jacobian), axis=1), np.finfo(float).tiny)
    column_scale = np.maximum(
        np.max(np.abs(jacobian/row_scale[:, None]), axis=0), np.finfo(float).tiny,
    )
    scaled = jacobian/row_scale[:, None]/column_scale[None, :]
    try:
        condition = float(np.linalg.cond(scaled))
        if not np.isfinite(condition) or condition > 1.0e8:
            return None
        direction = np.linalg.solve(scaled, -residual/row_scale)/column_scale
    except np.linalg.LinAlgError:
        return None
    if not np.all(np.isfinite(direction)):
        return None
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
            condition, fraction, before, after,
        )
    return None
