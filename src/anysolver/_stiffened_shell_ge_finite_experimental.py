"""Bounded finite-step trial driver for the experimental GE point panel.

All shell, beam and joint evaluations use one accepted predecessor per load
increment. This is an elastic development slice, not a qualified mixed owner.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import warnings

import numpy as np
from scipy import sparse
from scipy.sparse import linalg as spla

from ._ge_beam3_generalized_static_boundary import spatial_jacobian
from ._ge_beam3_p5.algebra import rotation
from .control import cancellation_safe_point
from .corotational import corotational_element_response
from ._stiffened_shell_ge_experimental import (
    NodalAction, _owned, _relative_equilibrium, _scaled_constraint_gap,
)
from ._stiffened_shell_ge_checkpoint_binary import encode as _encode_binary_checkpoint


MAX_JSON_CHECKPOINT_BYTES = 2_000_000
MAX_JSON_CHECKPOINT_VALUES = 50_000


@dataclass(frozen=True)
class FinitePointResult:
    """Experimental finite result with dimensionless work/row-scaled errors."""
    status: str
    load_factor: float
    shell_displacement: np.ndarray
    beam_positions: np.ndarray
    beam_frames: np.ndarray
    cell_frames: np.ndarray
    cell_resultants: np.ndarray
    multipliers: np.ndarray
    support_reactions: np.ndarray
    free_equilibrium_ratio: float
    constraint_max: float
    iterations: int
    generation: int
    accepted_factors: tuple[float, ...]
    production_qualified: bool = False


@dataclass(frozen=True)
class _State:
    q: np.ndarray
    frames: np.ndarray
    cells: np.ndarray
    resultants: np.ndarray
    multipliers: np.ndarray


class _RotationStepTooLarge(ValueError):
    """Candidate update lies outside the admitted local rotation chart."""


class FinitePointDriver:
    """Finite updates with globally retained native B3 coordinates."""

    def __init__(self, owner):
        self.owner = owner
        beam_ids = owner._beam_ids
        self._beam_nodal = 6*len(beam_ids)
        self._reference_frames = np.array(
            [owner._beam_nodes[node][1] for node in beam_ids], dtype=float)
        self._reference_positions = np.array(
            [owner._beam_nodes[node][0] for node in beam_ids], dtype=float)
        self._state = _State(
            np.zeros(owner._K.shape[0]), self._reference_frames.copy(),
            np.tile(np.eye(3), (len(owner._beam_parts), 2, 1, 1)),
            np.zeros((len(owner._beam_parts), 18)),
            np.zeros(6*len(owner._connections)))
        self._shell_origins = tuple(part[3] for part in owner._shell_parts)
        self._beam_origins = tuple(part[2] for part in owner._beam_parts)
        self._pattern = None
        self._load_factor = 0.
        self._accepted = None
        self._accepted_factors = ()

    def _load(self, actions):
        owner = self.owner
        load = np.zeros(owner._K.shape[0])
        for action in actions:
            if type(action) is not NodalAction or action.domain not in ("shell", "beam"):
                raise ValueError("declared shell or beam nodal action required")
            index = owner._shell_index if action.domain == "shell" else owner._beam_index
            if action.node not in index:
                raise ValueError("action references unknown physical node")
            wrench = _owned(action.wrench, (6,))
            if np.any(wrench[3:] != 0.):
                raise ValueError("finite experimental path admits translation forces only")
            offset = 0 if action.domain == "shell" else owner._shell_count
            load[offset+6*index[action.node]:offset+6*index[action.node]+6] += wrench
        return _owned(load)

    def _assemble(self, state, factor, shell_origins, beam_origins, *, pattern=None):
        owner = self.owner
        load_pattern = self._pattern if pattern is None else pattern
        if load_pattern is None:
            raise RuntimeError("finite load pattern has not been supplied")
        count = owner._K.shape[0]
        size = count+len(state.multipliers)
        residual = np.zeros(size)
        rows, columns, data = [], [], []
        shell_candidates = []
        beam_candidates = []

        def scatter(slots, force, tangent):
            slots = np.asarray(slots, dtype=int)
            force = np.asarray(force, dtype=float)
            tangent = np.asarray(tangent, dtype=float)
            if (force.shape != (len(slots),) or
                    tangent.shape != (len(slots), len(slots)) or
                    not np.isfinite(force).all() or not np.isfinite(tangent).all()):
                raise RuntimeError("finite local mixed trial operator required")
            np.add.at(residual, slots, force)
            rows.extend(np.repeat(slots, len(slots)))
            columns.extend(np.tile(slots, len(slots)))
            data.extend(tangent.ravel())

        for (eid, element, slots, _), origin in zip(owner._shell_parts, shell_origins):
            if len(slots) == 18:
                force, tangent, candidate = element.compute_nonlinear_response(
                    owner._shell_model.mesh,
                    owner._shell_model.get_material("shell"),
                    state.q[slots], origin, 3, True)
            else:
                force, tangent, candidate = corotational_element_response(
                    owner._shell_model, eid, element, state.q[slots], True,
                    committed_state=origin, num_layers=3,
                    tangent_mode="consistent")
            scatter(slots, force, tangent)
            shell_candidates.append(candidate)

        for i, ((element, slots, _), origin) in enumerate(
                zip(owner._beam_parts, beam_origins)):
            nodes = np.array([owner._beam_index[node] for node in element.node_ids])
            positions = self._reference_positions[nodes].copy()
            for local, node in enumerate(nodes):
                offset = owner._shell_count+6*node
                positions[local] += state.q[offset:offset+3]
            response = element.operator.evaluate(
                positions, np.zeros((3, 3)), state.frames[nodes],
                state.cells[i], state.resultants[i], origin=origin,
                check=element.operator.guard)
            tangent = spatial_jacobian(
                response.residual, response.hessian+response.hessian_low)
            scatter(slots+owner._shell_count, response.residual, tangent)
            beam_candidates.append(response.history)

        for i, (joint, slots) in enumerate(zip(owner._connections,
                                               owner._joint_slots)):
            shell_node = slots[0]//6
            beam_node = (slots[6]-owner._shell_count)//6
            positions = np.array((
                owner._shell_xyz[shell_node]+state.q[slots[:3]],
                self._reference_positions[beam_node]+state.q[slots[6:9]]))
            anchors = np.array((np.eye(3), state.frames[beam_node]))
            coordinates = np.zeros((2, 3))
            coordinates[0] = state.q[slots[3:6]]
            trial = joint.evaluate_ports(
                positions, anchors, state.multipliers[6*i:6*i+6],
                rotation_coordinates=coordinates,
                charted_ports=(True, False))
            extended = np.r_[slots, np.arange(count+6*i, count+6*i+6)]
            scatter(extended, trial.residual, trial.tangent)

        residual[:count] -= factor*load_pattern
        matrix = sparse.coo_matrix(
            (data, (rows, columns)), shape=(size, size)).tocsc()
        if not np.isfinite(residual).all() or not np.isfinite(matrix.data).all():
            raise RuntimeError("finite global mixed trial required")
        relative = _relative_equilibrium(
            residual[owner._free], (factor*load_pattern)[owner._free],
            owner._coordinate_scale[owner._free], owner._reference_length)
        constraint = _scaled_constraint_gap(
            residual[count:], owner._constraint_scale)
        return residual, matrix, relative, constraint, tuple(shell_candidates), tuple(beam_candidates)

    def _advance(self, state, increment, amount):
        owner = self.owner
        delta = amount*increment
        q = state.q.copy()
        frames = state.frames.copy()
        cells = state.cells.copy()
        resultants = state.resultants.copy()
        q[:owner._shell_count] += delta[:owner._shell_count]
        for node in range(len(owner._beam_ids)):
            slot = owner._shell_count+6*node
            q[slot:slot+3] += delta[slot:slot+3]
            angle = delta[slot+3:slot+6]
            if np.linalg.norm(angle) >= .9*np.pi:
                raise _RotationStepTooLarge("finite beam rotation increment requires cutback")
            frames[node] = rotation(angle)@frames[node]
        retained = owner._shell_count+self._beam_nodal
        for i in range(len(owner._beam_parts)):
            base = retained+24*i
            for cell in range(2):
                angle = delta[base+3*cell:base+3*cell+3]
                if np.linalg.norm(angle) >= .9*np.pi:
                    raise _RotationStepTooLarge("finite cell rotation increment requires cutback")
                cells[i, cell] = rotation(angle)@cells[i, cell]
            resultants[i] += delta[base+6:base+24]
        multipliers = state.multipliers+delta[len(q):]
        return _State(q, frames, cells, resultants, multipliers)

    def solve(self, actions, targets, *, cancellation_token=None,
              max_iterations=12, max_backtracks=8):
        owner = self.owner
        if (type(targets) is not tuple or not targets or
                any(not np.isfinite(v) or v <= self._load_factor
                    for v in targets) or
                tuple(targets) != tuple(sorted(set(targets)))):
            raise ValueError("strictly increasing finite load factors required")
        if (type(max_iterations) is not int or not 1 <= max_iterations <= 24 or
                type(max_backtracks) is not int or not 0 <= max_backtracks <= 12):
            raise ValueError("bounded finite Newton controls required")
        pattern = self._load(actions)
        if self._pattern is not None and not np.array_equal(self._pattern, pattern):
            raise ValueError("finite load pattern changed after first increment")
        free = np.r_[owner._free,
                     np.arange(owner._K.shape[0],
                               owner._K.shape[0]+len(self._state.multipliers))]
        for factor in targets:
            cancellation_safe_point(cancellation_token, "stiffened-shell.finite.increment")
            trial = self._state
            for iteration in range(max_iterations+1):
                cancellation_safe_point(cancellation_token, "stiffened-shell.finite.trial")
                residual, matrix, relative, gap, shell_next, beam_next = (
                    self._assemble(trial, factor, self._shell_origins,
                                   self._beam_origins, pattern=pattern))
                if relative <= 1e-8 and gap <= 1e-9:
                    if any(station.accumulated != (0., 0.)
                           for history in beam_next
                           for station in history.stations):
                        raise RuntimeError(
                            "experimental finite point path admits elastic B3 response only")
                    cancellation_safe_point(cancellation_token,
                                            "stiffened-shell.finite.commit")
                    support = np.zeros(owner._K.shape[0])
                    support[owner._fixed] = residual[owner._fixed]
                    next_factors = self._accepted_factors+(float(factor),)
                    next_result = FinitePointResult(
                        "completed", float(factor),
                        _owned(trial.q[:owner._shell_count]),
                        _owned(self._beam_positions(trial)),
                        _owned(trial.frames), _owned(trial.cells),
                        _owned(trial.resultants), _owned(trial.multipliers),
                        _owned(support), relative, gap, iteration,
                        owner._generation+1, next_factors)
                    cancellation_safe_point(cancellation_token,
                                            "stiffened-shell.finite.publish")
                    self._state = trial
                    self._shell_origins = shell_next
                    self._beam_origins = beam_next
                    self._load_factor = float(factor)
                    self._accepted_factors = next_factors
                    self._pattern = pattern
                    owner._generation += 1
                    self._accepted = next_result
                    break
                if iteration == max_iterations:
                    raise RuntimeError("finite mixed Newton iteration limit")
                with warnings.catch_warnings():
                    warnings.simplefilter("error", spla.MatrixRankWarning)
                    step = spla.spsolve(matrix[free, :][:, free],
                                       -residual[free])
                if not np.isfinite(step).all():
                    raise RuntimeError("finite mixed Newton correction required")
                full = np.zeros(matrix.shape[0])
                full[free] = step
                old_merit = max(relative, gap)
                for backtrack in range(max_backtracks+1):
                    cancellation_safe_point(
                        cancellation_token, "stiffened-shell.finite.backtrack")
                    try:
                        candidate = self._advance(trial, full, .5**backtrack)
                    except _RotationStepTooLarge:
                        continue
                    changed = self._assemble(
                        candidate, factor, self._shell_origins,
                        self._beam_origins, pattern=pattern)
                    if max(changed[2], changed[3]) < old_merit:
                        trial = candidate
                        break
                else:
                    raise RuntimeError("finite mixed backtrack budget exhausted")
        return self._accepted

    def _beam_positions(self, state):
        positions = self._reference_positions.copy()
        for node in range(len(self.owner._beam_ids)):
            slot = self.owner._shell_count+6*node
            positions[node] += state.q[slot:slot+3]
        return positions

    def recover(self):
        if self._accepted is None:
            raise RuntimeError("no accepted finite mixed increment")
        return self._accepted

    def checkpoint(self):
        if self._accepted is None:
            raise RuntimeError("no accepted finite mixed increment")
        state = self._state
        arrays = (("q", state.q), ("frames", state.frames),
                  ("cells", state.cells), ("resultants", state.resultants),
                  ("multipliers", state.multipliers),
                  ("pattern", self._pattern),
                  ("accepted_factors", np.asarray(self._accepted_factors)))
        if sum(value.size for _name, value in arrays) > MAX_JSON_CHECKPOINT_VALUES:
            return _encode_binary_checkpoint(
                "finite", self.owner._identity, self.owner._generation, arrays)
        payload = {
            "schema": "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_FINITE_V1",
            "model": self.owner._identity,
            "generation": self.owner._generation,
            "accepted_factors": self._accepted_factors,
            "q": state.q.tolist(),
            "frames": state.frames.tolist(),
            "cells": state.cells.tolist(),
            "resultants": state.resultants.tolist(),
            "multipliers": state.multipliers.tolist(),
            "pattern": self._pattern.tolist(),
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                         allow_nan=False).encode("ascii")
        if len(raw) > MAX_JSON_CHECKPOINT_BYTES:
            return _encode_binary_checkpoint(
                "finite", self.owner._identity, self.owner._generation, arrays)
        return raw

    def restore(self, value):
        owner = self.owner
        if (type(value) is not dict or set(value) != {
                "schema", "model", "generation", "accepted_factors", "q",
                "frames", "cells", "resultants", "multipliers", "pattern"} or
                value["schema"] !=
                "B3_GE_E4_PL_STIFFENED_SHELL_EXPERIMENTAL_FINITE_V1" or
                value["model"] != owner._identity or
                type(value["generation"]) is not int or
                value["generation"] < 1):
            raise ValueError("incompatible experimental finite checkpoint")
        factors = value["accepted_factors"]
        if (type(factors) is not list or len(factors) != value["generation"] or
                not factors or any(type(v) is not float or not np.isfinite(v)
                                   for v in factors) or
                factors[0] <= 0. or any(b <= a for a, b in zip(factors, factors[1:]))):
            raise ValueError("invalid accepted finite load history")
        q = _owned(value["q"], (owner._K.shape[0],))
        frames = _owned(value["frames"], self._reference_frames.shape)
        cells = _owned(value["cells"], self._state.cells.shape)
        resultants = _owned(value["resultants"], self._state.resultants.shape)
        multipliers = _owned(value["multipliers"], self._state.multipliers.shape)
        pattern = _owned(value["pattern"], (owner._K.shape[0],))
        beam_nodal = q[owner._shell_count:
                       owner._shell_count+self._beam_nodal].reshape(-1, 6)
        if (np.any(q[owner._fixed] != 0.) or
                np.any(beam_nodal[:, 3:] != 0.) or
                np.any(q[owner._shell_count+self._beam_nodal:] != 0.) or
                np.any(pattern[owner._shell_count+self._beam_nodal:] != 0.) or
                np.any(pattern[:owner._shell_count+self._beam_nodal]
                       .reshape(-1, 6)[:, 3:] != 0.)):
            raise ValueError("invalid finite checkpoint coordinate or load layout")
        for family in (frames.reshape(-1, 3, 3), cells.reshape(-1, 3, 3)):
            if any(np.linalg.norm(frame.T@frame-np.eye(3)) > 1e-9 or
                   abs(np.linalg.det(frame)-1.) > 1e-9 for frame in family):
                raise ValueError("nonphysical finite checkpoint rotation")
        trial = _State(q, frames, cells, resultants, multipliers)
        residual, _, relative, gap, shell_next, beam_next = self._assemble(
            trial, factors[-1], self._shell_origins, self._beam_origins,
            pattern=pattern)
        if (not np.isfinite(relative) or relative > 1e-8 or gap > 1e-9 or
                any(station.accumulated != (0., 0.)
                    for history in beam_next for station in history.stations)):
            raise ValueError("mechanically inconsistent finite checkpoint")
        support = np.zeros(owner._K.shape[0])
        support[owner._fixed] = residual[owner._fixed]
        result = FinitePointResult(
            "completed", factors[-1], _owned(q[:owner._shell_count]),
            _owned(self._beam_positions(trial)), frames, cells, resultants,
            multipliers, _owned(support), relative, gap, 0,
            value["generation"], tuple(factors))
        self._state = trial
        self._pattern = pattern
        self._shell_origins = shell_next
        self._beam_origins = beam_next
        self._load_factor = factors[-1]
        self._accepted_factors = tuple(factors)
        self._accepted = result
        owner._generation = value["generation"]
        return result
