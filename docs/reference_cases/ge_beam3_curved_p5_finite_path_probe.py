"""Bounded one-element elastic load path and transactions, author research only.

No production solver/section-state/restart API, independent qualification,
arc-length solver, shell coupling or nonlinear material adapter is supplied.
Existing failed prescribed-state probes and their limits remain unchanged.
"""

from dataclasses import dataclass
import hashlib

import numpy as np

from anysolver.ge_beam3_curved_reference import CurvedBeam3ReferenceGeometry
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import canonical_bytes, rotation, validate_section
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _array, _readonly, LocalStationarityError
from docs.reference_cases.ge_beam3_curved_p5_retained_response_probe import RetainedFiniteResponseProbe


class FinitePathError(RuntimeError):
    """Bounded global trial failed; no committed configuration was changed."""


class TransactionError(RuntimeError):
    """Stale, foreign, absent or altered trial state cannot be committed."""


@dataclass(frozen=True)
class ElasticPathState:
    epoch: int
    positions: np.ndarray
    vertex_frames: np.ndarray
    forces: np.ndarray


@dataclass(frozen=True)
class ElasticPathTrial:
    origin_epoch: int
    positions: np.ndarray
    vertex_frames: np.ndarray
    forces: np.ndarray
    reactions: np.ndarray
    local_rotations: np.ndarray
    potential: float
    residual_norm: float
    iterations: int
    evaluations: int


def _trial_digest(trial):
    record = {name: value.tolist() if isinstance(value, np.ndarray) else value
              for name, value in vars(trial).items()}
    return hashlib.sha256(canonical_bytes(record)).hexdigest()


class FiniteCantileverPathProbe:
    """One three-node macro, first vertex fixed, spatial dead nodal forces only.

    Nodal matrices are authoritative; each Newton trial uses Exp(dtheta) Q.
    There is no accumulated rotation vector. Internal equilibrium and its
    Schur tangent come from the unchanged retained scalar-potential probe.
    Only a successful owned trial can be committed. No automatic load cutback
    or repeated external request is performed.
    """

    def __init__(self, reference, section):
        self._reference = CurvedBeam3ReferenceGeometry(reference.coordinates, reference.nodal_triads)
        self._section = _readonly(validate_section(section))
        self._state = ElasticPathState(0, _readonly(self._reference.coordinates),
                                       _readonly(self._reference.nodal_triads), _readonly(np.zeros((3, 3))))
        self._pending = None
        self._pending_digest = None
        nodes = self._reference.coordinates
        self._length = max(float(np.linalg.norm(a-b)) for a in nodes for b in nodes)

    @property
    def committed(self):
        """Copy out state; modifying the copy cannot modify authoritative data."""
        return ElasticPathState(self._state.epoch, _readonly(self._state.positions),
                                 _readonly(self._state.vertex_frames), _readonly(self._state.forces))

    def _norm(self, residual, forces):
        physical = residual.reshape(3, 6)[1:].copy()
        physical[:, 3:] /= self._length
        return float(np.max(np.abs(physical))/max(1., float(np.max(np.abs(forces)))))

    def trial(self, forces, *, max_iterations=16, max_evaluations=48):
        """Return a converged trial without changing committed state.

        Each local solve retains its 25-iteration/12-backtrack bounds. Global
        Newton has at most 16 iterations, 10 trials per line search and 48
        complete local/Schur evaluations. Failed evaluations count too.
        Budget arguments can only reduce these limits. No partial solution
        is returned on failure. A new attempt invalidates any older trial.
        """
        self._pending = None
        self._pending_digest = None
        forces = _array(forces, (3, 3), "spatial dead forces")
        for value, upper, label in ((max_iterations, 16, "iteration"),
                                    (max_evaluations, 48, "evaluation")):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= upper:
                raise ValueError(f"{label} limit must be an integer from 0 to {upper}")
        x, q = self._state.positions.copy(), self._state.vertex_frames.copy()
        external = np.zeros((3, 6))
        external[:, :3] = forces
        external = external.ravel()
        evaluations = 0

        def evaluate(positions, frames):
            nonlocal evaluations
            if evaluations == max_evaluations:
                raise FinitePathError("global evaluation budget exhausted")
            evaluations += 1
            return RetainedFiniteResponseProbe(self._reference, self._section, positions, frames).evaluate()

        try:
            response = evaluate(x, q)
        except (ValueError, LocalStationarityError, np.linalg.LinAlgError) as exc:
            raise FinitePathError("initial local equilibrium failed") from exc
        for iteration in range(max_iterations+1):
            residual = response.residual-external
            norm = self._norm(residual, forces)
            if norm <= 1e-11:
                trial = ElasticPathTrial(self._state.epoch, _readonly(x), _readonly(q),
                                         _readonly(forces), _readonly(residual.reshape(3, 6)),
                                         _readonly(response.rotations), response.potential, norm,
                                         iteration, evaluations)
                self._pending_digest = _trial_digest(trial)
                self._pending = trial
                return trial
            if iteration == max_iterations:
                raise FinitePathError("global iteration budget exhausted")
            step = np.zeros(18)
            try:
                step[6:] = np.linalg.solve(response.tangent[6:, 6:], -residual[6:])
            except np.linalg.LinAlgError as exc:
                raise FinitePathError("singular global tangent") from exc
            if not np.isfinite(step).all():
                raise FinitePathError("nonfinite global Newton step")
            accepted = False
            for backtrack in range(10):
                increment = (step*(.5**backtrack)).reshape(3, 6)
                # Check the increment path, not only wrapped endpoint matrices.
                if np.max(np.linalg.norm(increment[:, 3:], axis=1)) >= .9*np.pi:
                    continue
                made_x = x+increment[:, :3]
                made_q = np.array([rotation(increment[i, 3:]) @ q[i] for i in range(3)])
                try:
                    made = evaluate(made_x, made_q)
                except (ValueError, LocalStationarityError, np.linalg.LinAlgError):
                    continue
                if self._norm(made.residual-external, forces) < norm:
                    x, q, response = made_x, made_q, made
                    accepted = True
                    break
            if not accepted:
                raise FinitePathError("global line search exhausted; explicit cutback required")
        raise AssertionError("unreachable bounded path")

    def _require_pending(self, trial):
        if trial is not self._pending or trial is None or trial.origin_epoch != self._state.epoch:
            raise TransactionError("owned current trial required")

    def commit(self, trial):
        self._require_pending(trial)
        try:
            altered = _trial_digest(trial) != self._pending_digest
        except (ValueError, TypeError, OverflowError) as exc:
            raise TransactionError("altered trial cannot be committed") from exc
        if altered:
            raise TransactionError("altered trial cannot be committed")
        self._state = ElasticPathState(self._state.epoch+1, _readonly(trial.positions),
                                       _readonly(trial.vertex_frames), _readonly(trial.forces))
        self._pending = None
        self._pending_digest = None
        return self.committed

    def discard(self, trial):
        self._require_pending(trial)
        self._pending = None
        self._pending_digest = None
