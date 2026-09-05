"""Atomic nonlinear cantilever history research; no production/restart API."""

from copy import deepcopy
from dataclasses import asdict, dataclass, replace
import hashlib
import json

import numpy as np

from anysolver.ge_beam3_curved_reference import CurvedBeam3ReferenceGeometry
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _array, _readonly
from docs.reference_cases.ge_beam3_curved_p5_section_probe import SectionHistory, _history
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import NonlinearMixedBeamProbe, NonlinearLocalError


def digest(value):
    return hashlib.sha256(json.dumps(asdict(value), sort_keys=True, separators=(',', ':'),
        allow_nan=False, default=lambda array: array.tolist()).encode('ascii')).hexdigest()


@dataclass(frozen=True)
class NonlinearPathState:
    epoch: int
    positions: np.ndarray
    frames: np.ndarray
    forces: np.ndarray
    histories: tuple


@dataclass(frozen=True)
class NonlinearPathTrial:
    origin_epoch: int
    positions: np.ndarray
    frames: np.ndarray
    forces: np.ndarray
    origins: tuple
    response: object
    residual_norm: float
    iterations: int
    mixed_evaluations: int


class HistoryPathError(RuntimeError):
    """No accepted global nonlinear step; committed state remains unchanged."""


class HistoryTransactionError(RuntimeError):
    """Absent, stale, foreign, altered or nonreproducible history transaction."""


class NonlinearCantileverHistoryProbe:
    """One macro, first vertex clamped, spatial dead nodal forces only.

    Every local solve and global line-search candidate uses the same committed
    station origins. Geometry and all station histories publish in one tuple
    assignment only after global convergence and accepted-origin validation.
    No automatic load cutback, restart, arc length or nonlinear dynamics.
    """

    def __init__(self, reference, section, *, order=24):
        self._reference = CurvedBeam3ReferenceGeometry(reference.coordinates, reference.nodal_triads)
        self._section, self._order = section, order
        initial_model = NonlinearMixedBeamProbe(self._reference, section, order=order)
        state = NonlinearPathState(0, _readonly(self._reference.coordinates),
            _readonly(self._reference.nodal_triads), _readonly(np.zeros((3, 3))), initial_model.origins)
        self._checkpoint = (state, None)
        self._pending = self._pending_digest = None
        nodes = self._reference.coordinates
        self._length = max(np.linalg.norm(a-b) for a in nodes for b in nodes)

    @property
    def committed(self):
        # Defensive copy: no caller-owned arrays are authoritative.
        return deepcopy(self._checkpoint[0])

    def _norm(self, residual, forces):
        physical = residual.reshape(3, 6)[1:].copy()
        physical[:, 3:] /= self._length
        return float(np.max(np.abs(physical))/max(1., float(np.max(np.abs(forces)))))

    def trial(self, forces, *, max_iterations=16, max_mixed_evaluations=256):
        self._pending = self._pending_digest = None
        forces = _array(forces, (3, 3), "spatial dead forces")
        for value, bound in ((max_iterations, 16), (max_mixed_evaluations, 256)):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= bound:
                raise ValueError("global history iteration/evaluation bound exceeded")
        state = self._checkpoint[0]
        x, q = state.positions.copy(), state.frames.copy()
        external = np.zeros((3, 6))
        external[:, :3] = forces
        external = external.ravel()
        count = 0

        class CountedMixed(NonlinearMixedBeamProbe):
            def evaluate(inner, *args, **kwargs):
                nonlocal count
                if count == max_mixed_evaluations:
                    raise HistoryPathError("global mixed-evaluation budget exhausted")
                count += 1
                return super().evaluate(*args, **kwargs)

        model = CountedMixed(self._reference, self._section, order=self._order, origins=state.histories)
        try:
            response = model.solve(x, q)
        except (ValueError, NonlinearLocalError, np.linalg.LinAlgError) as exc:
            raise HistoryPathError("initial nonlinear local solve failed") from exc
        for iteration in range(max_iterations+1):
            residual = response.residual-external
            norm = self._norm(residual, forces)
            if norm <= 1e-11:
                result = NonlinearPathTrial(state.epoch, _readonly(x), _readonly(q), _readonly(forces),
                    tuple(_history(h) for h in state.histories), response, norm, iteration, count)
                self._pending_digest = digest(result)
                self._pending = result
                return result
            if iteration == max_iterations:
                raise HistoryPathError("global iteration budget exhausted")
            step = np.zeros(18)
            try:
                step[6:] = np.linalg.solve(response.tangent[6:, 6:], -residual[6:])
            except np.linalg.LinAlgError as exc:
                raise HistoryPathError("singular nonlinear global tangent") from exc
            if not np.isfinite(step).all():
                raise HistoryPathError("nonfinite nonlinear global step")
            accepted = False
            for backtrack in range(10):
                increment = (step*(.5**backtrack)).reshape(3, 6)
                if np.max(np.linalg.norm(increment[:, 3:], axis=1)) >= .9*np.pi:
                    continue
                made_x = x+increment[:, :3]
                made_q = np.array([rotation(increment[i, 3:]) @ q[i] for i in range(3)])
                try:
                    made = model.solve(made_x, made_q)
                except (ValueError, NonlinearLocalError, np.linalg.LinAlgError):
                    continue
                if self._norm(made.residual-external, forces) < norm:
                    x, q, response = made_x, made_q, made
                    accepted = True
                    break
            if not accepted:
                raise HistoryPathError("global line search failed; explicit cutback required")
        raise AssertionError("unreachable global iteration")

    def _owned(self, trial):
        if trial is None or trial is not self._pending or trial.origin_epoch != self._checkpoint[0].epoch:
            raise HistoryTransactionError("owned current global trial required")

    def _reconstruct(self, trial):
        """One functional evaluation, not a repeated local/global Newton solve."""
        model = NonlinearMixedBeamProbe(self._reference, self._section, order=self._order, origins=trial.origins)
        response = trial.response
        made = model.evaluate(trial.positions, trial.frames, response.local_rotations, response.moments)
        h = made.hessian
        np.linalg.cholesky(-h[24:, 24:])
        np.linalg.cholesky(h[18:24, 18:24]-h[18:24, 24:] @ np.linalg.solve(h[24:, 24:], h[24:, 18:24]))
        tangent = h[:18, :18]-h[:18, 18:] @ np.linalg.solve(h[18:, 18:], h[18:, :18])
        return replace(response, potential=made.potential, residual=_readonly(made.residual[:18]),
            tangent=_readonly(tangent), stations=made.stations,
            local_residual_norm=float(np.linalg.norm(made.residual[18:], np.inf)),
            local_rotations=_readonly(response.local_rotations), moments=_readonly(response.moments))

    def commit(self, trial):
        self._owned(trial)
        try:
            if digest(trial) != self._pending_digest:
                raise HistoryTransactionError("altered global/station trial")
            response = self._reconstruct(trial)
            if digest(response) != digest(trial.response):
                raise HistoryTransactionError("accepted-origin response mismatch")
            external = np.column_stack((trial.forces, np.zeros((3, 3)))).ravel()
            norm = self._norm(response.residual-external, trial.forces)
            if (norm > 1e-11 or norm != trial.residual_norm or response.local_residual_norm > 1e-11
                    or not np.array_equal(trial.positions[0], self._reference.coordinates[0])
                    or not np.array_equal(trial.frames[0], self._reference.nodal_triads[0])):
                raise HistoryTransactionError("global/local equilibrium or clamp mismatch")
            histories = tuple(_history(station.response.history) for station in response.stations)
            expected = [(c, i) for c in (0, 1) for i in range(self._order)]
            if [(s.cell, s.index) for s in response.stations] != expected:
                raise HistoryTransactionError("station identity/order mismatch")
            state = NonlinearPathState(trial.origin_epoch+1, _readonly(trial.positions),
                _readonly(trial.frames), _readonly(trial.forces), histories)
            accepted = deepcopy(replace(trial, response=response))
            exported = deepcopy(state)
        except (ValueError, TypeError, np.linalg.LinAlgError) as exc:
            raise HistoryTransactionError("global commit validation failed") from exc
        # No authoritative mutation occurred above, including during allocation
        # or validation of the last station. Geometry/history/replay publish once.
        self._checkpoint = (state, accepted)
        self._pending = self._pending_digest = None
        return exported

    def discard(self, trial):
        self._owned(trial)
        self._pending = self._pending_digest = None

    def replay(self):
        accepted = self._checkpoint[1]
        if accepted is None:
            raise HistoryTransactionError("no accepted nonlinear increment to replay")
        try:
            response = self._reconstruct(accepted)
            if digest(response) != digest(accepted.response):
                raise HistoryTransactionError("accepted global replay mismatch")
        except (ValueError, TypeError, np.linalg.LinAlgError) as exc:
            raise HistoryTransactionError("accepted global replay validation failed") from exc
        return response
