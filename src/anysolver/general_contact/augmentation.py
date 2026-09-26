"""Optional acceleration of a projected augmented-contact fixed point.

The secant predictor never accepts an increment. The caller must re-equilibrate
with the proposed multiplier and check the original projected residual and
independent physical gap before committing any state.
"""

from __future__ import annotations

import numpy as np


class ProjectedAugmentationSecant:
    """Fit the active projected-map residual within one physical increment."""

    def __init__(self) -> None:
        self._active: np.ndarray | None = None
        self._samples: list[tuple[np.ndarray, np.ndarray]] = []
        self.attempts = 0
        self.applied = 0

    def propose(self, current: np.ndarray, projected: np.ndarray) -> np.ndarray | None:
        current = np.asarray(current, dtype=float)
        projected = np.asarray(projected, dtype=float)
        if (current.ndim != 1 or current.shape != projected.shape
                or not np.all(np.isfinite(current))
                or not np.all(np.isfinite(projected))
                or np.any(current < 0.0) or np.any(projected < 0.0)):
            raise ValueError("projected augmentation samples must be finite nonnegative vectors")
        active = projected > 0.0
        count = int(np.count_nonzero(active))
        if (count < 1 or count > 4
                or np.any((current > 0.0) & ~active)):
            self._active = None
            self._samples.clear()
            return None
        if self._active is None or not np.array_equal(active, self._active):
            self._active = active.copy()
            self._samples.clear()
        self._samples.append((current[active].copy(),
                              (projected - current)[active].copy()))
        self._samples = self._samples[-(count + 2):]
        if len(self._samples) < count + 2:
            return None
        self.attempts += 1
        coordinates = np.vstack([sample[0] for sample in self._samples])
        residuals = np.vstack([sample[1] for sample in self._samples])
        origin = coordinates.mean(axis=0)
        centered = coordinates - origin
        values = residuals - residuals.mean(axis=0)
        try:
            slope, _, rank, singular = np.linalg.lstsq(centered, values, rcond=None)
        except np.linalg.LinAlgError:
            return None
        if (rank != count or singular[-1] <= 0.0
                or singular[0] / singular[-1] > 1.0e6):
            return None
        fit_error = np.linalg.norm(values - centered @ slope)
        if fit_error > 1.0e-3 * np.linalg.norm(values):
            return None
        derivative = slope.T
        try:
            if np.linalg.cond(derivative) > 1.0e8:
                return None
            step = np.linalg.solve(derivative, -residuals[-1])
        except np.linalg.LinAlgError:
            return None
        candidate = current[active] + step
        amplitude = max(float(np.max(current[active])),
                        float(np.max(projected[active])))
        if (not np.all(np.isfinite(candidate)) or np.any(candidate <= 0.0)
                or np.max(np.abs(step)) > 2.0 * amplitude):
            return None
        proposal = np.zeros_like(current)
        proposal[active] = candidate
        self.applied += 1
        return proposal
