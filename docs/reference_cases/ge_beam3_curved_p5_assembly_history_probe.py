"""Small connected nonlinear beam assembly; author research, not a solver API.

Shared nodes own spatial deformation rotations U. Each element uses Q=U R0
with its own reference material triad, including at a shared curved junction.
Only spatial dead nodal forces and initially fixed node clamps are supported.
"""

from copy import deepcopy
from dataclasses import dataclass, replace

import numpy as np

from anysolver.ge_beam3_curved_reference import CurvedBeam3ReferenceGeometry
from docs.reference_cases.ge_beam3_curved_p5_algebra_probe import rotation
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _array, _frames, _readonly
from docs.reference_cases.ge_beam3_curved_p5_history_path_probe import digest
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import NonlinearMixedBeamProbe, NonlinearLocalError
from docs.reference_cases.ge_beam3_curved_p5_section_probe import _history


class AssemblyPathError(RuntimeError):
    """No converged global trial; previous checkpoint is unchanged."""


class AssemblyTransactionError(RuntimeError):
    """No valid owned trial or accepted-origin assembly replay."""


@dataclass(frozen=True)
class AssemblyState:
    epoch: int
    positions: np.ndarray
    rotations: np.ndarray
    forces: np.ndarray
    histories: tuple


@dataclass(frozen=True)
class AssemblyResponse:
    potential: float
    residual: np.ndarray
    tangent: np.ndarray
    elements: tuple


@dataclass(frozen=True)
class AssemblyTrial:
    origin_epoch: int
    positions: np.ndarray
    rotations: np.ndarray
    forces: np.ndarray
    origins: tuple
    response: AssemblyResponse
    residual_norm: float
    iterations: int
    mixed_evaluations: int


class _Budget:
    def __init__(self, limit):
        self.limit, self.count = limit, 0

    def consume(self):
        if self.count >= self.limit:
            raise AssemblyPathError('assembly mixed-evaluation budget exhausted')
        self.count += 1


class NonlinearAssemblyHistoryProbe:
    """At most eight connected 3-node elements with one atomic state tuple.

No history is committed by local convergence or a successful element replay.
All elements are replayed and checked before one whole-model publication.
No load cutback/retry, arc length, dynamics, restart codec or shell coupling.
"""

    def __init__(self, references, connectivity, sections, *, fixed_nodes=(0,), order=24):
        references, connectivity, sections = tuple(references), tuple(connectivity), tuple(sections)
        if not 1 <= len(references) <= 8 or len(connectivity) != len(references) or len(sections) != len(references):
            raise ValueError('one through eight elements with matching maps/sections required')
        maps = []
        for row in connectivity:
            row = tuple(row)
            if (len(row) != 3 or any(type(n) is not int or not 0 <= n < 24 for n in row)
                    or len(set(row)) != 3):
                raise ValueError('three distinct bounded integer node IDs required')
            maps.append(row)
        if len({frozenset(row) for row in maps}) != len(maps):
            raise ValueError('duplicate element node set')
        used = set(n for row in maps for n in row)
        self._nodes = len(used)
        if used != set(range(self._nodes)):
            raise ValueError('contiguous node IDs without orphan slots required')
        reached = {0}
        for _ in maps:
            for row in maps:
                if reached.intersection(row):
                    reached.update(row)
        if reached != used:
            raise ValueError('connected beam graph required')
        fixed_nodes = tuple(fixed_nodes)
        if (not fixed_nodes or len(set(fixed_nodes)) != len(fixed_nodes)
                or any(type(n) is not int or n not in used for n in fixed_nodes)
                or len(fixed_nodes) == self._nodes):
            raise ValueError('distinct valid clamps with at least one free node required')
        self._maps = tuple(np.array(row, dtype=int) for row in maps)
        self._dofs = tuple((6*row[:, None]+np.arange(6)).ravel() for row in self._maps)
        self._fixed = np.array(sorted(fixed_nodes), dtype=int)
        self._free_nodes = np.array(sorted(used-set(fixed_nodes)), dtype=int)
        self._free = (6*self._free_nodes[:, None]+np.arange(6)).ravel()
        self._references = tuple(CurvedBeam3ReferenceGeometry(r.coordinates, r.nodal_triads) for r in references)
        self._sections, self._order = deepcopy(sections), order
        coordinates = np.zeros((self._nodes, 3))
        seen, histories = set(), []
        for ref, row, section in zip(self._references, self._maps, self._sections):
            for n, x in zip(row, ref.coordinates):
                if n in seen and not np.array_equal(coordinates[n], x):
                    raise ValueError('shared reference coordinates must agree exactly')
                coordinates[n] = x
                seen.add(n)
            histories.append(NonlinearMixedBeamProbe(ref, section, order=order).origins)
        self._coordinates = _readonly(coordinates)
        self._length = max(np.linalg.norm(a-b) for a in coordinates for b in coordinates)
        initial = AssemblyState(0, _readonly(coordinates), _readonly(np.tile(np.eye(3), (self._nodes, 1, 1))),
                                _readonly(np.zeros((self._nodes, 3))), tuple(histories))
        self._checkpoint = (initial, None)
        self._pending = self._pending_digest = None

    @property
    def committed(self):
        return deepcopy(self._checkpoint[0])

    def _scatter(self, elements):
        if len(elements) != len(self._maps):
            raise ValueError('complete element response inventory required')
        residual = np.zeros(6*self._nodes)
        tangent = np.zeros((6*self._nodes, 6*self._nodes))
        potential = 0.
        for dofs, response in zip(self._dofs, elements):
            residual[dofs] += response.residual
            tangent[np.ix_(dofs, dofs)] += response.tangent
            potential += response.potential
        if not np.isfinite(potential) or not np.isfinite(residual).all() or not np.isfinite(tangent).all():
            raise ValueError('nonfinite assembled response')
        return AssemblyResponse(float(potential), _readonly(residual), _readonly(tangent), tuple(elements))

    def _solve_all(self, positions, rotations, origins, budget):
        if len(origins) != len(self._maps):
            raise ValueError('complete element history inventory required')
        class CountedMixed(NonlinearMixedBeamProbe):
            def evaluate(inner, *args, **kwargs):
                budget.consume()
                return super().evaluate(*args, **kwargs)
        responses = []
        for ref, row, section, history in zip(self._references, self._maps, self._sections, origins):
            model = CountedMixed(ref, section, order=self._order, origins=history)
            frames = rotations[row] @ ref.nodal_triads
            responses.append(model.solve(positions[row], frames))
        return self._scatter(responses)

    def response_at(self, positions, rotations):
        """Fixed current geometry with committed origins; no global solve/commit."""
        x = _array(positions, (self._nodes, 3), 'assembled positions')
        u = _frames(rotations, self._nodes, 'shared spatial rotations')
        return self._solve_all(x, u, self._checkpoint[0].histories, _Budget(64*len(self._maps)))

    def _external(self, forces):
        return np.column_stack((forces, np.zeros_like(forces))).ravel()

    def _norm(self, residual, forces):
        physical = residual.reshape(self._nodes, 6)[self._free_nodes].copy()
        physical[:, 3:] /= self._length
        # Euclidean force/length-scaled moment norm also controls the combined
        # residual as the assembly grows and is invariant under spatial rotation.
        return float(np.linalg.norm(physical)/max(1., float(np.linalg.norm(forces))))

    def trial(self, forces, *, max_iterations=16, max_mixed_evaluations=None):
        self._pending = self._pending_digest = None
        cap = 256*len(self._maps)
        if max_mixed_evaluations is None:
            max_mixed_evaluations = cap
        for value, bound in ((max_iterations, 16), (max_mixed_evaluations, cap)):
            if type(value) is not int or not 0 <= value <= bound:
                raise ValueError('bounded global assembly iterations/evaluations required')
        forces = _array(forces, (self._nodes, 3), 'spatial dead forces')
        state = self._checkpoint[0]
        x, u = state.positions.copy(), state.rotations.copy()
        external, budget = self._external(forces), _Budget(max_mixed_evaluations)
        try:
            response = self._solve_all(x, u, state.histories, budget)
        except (ValueError, NonlinearLocalError, np.linalg.LinAlgError) as exc:
            raise AssemblyPathError('initial assembly local solve failed') from exc
        for iteration in range(max_iterations+1):
            residual = response.residual-external
            norm = self._norm(residual, forces)
            if norm <= 1e-11:
                result = AssemblyTrial(state.epoch, _readonly(x), _readonly(u), _readonly(forces),
                    deepcopy(state.histories), response, norm, iteration, budget.count)
                self._pending_digest, self._pending = digest(result), result
                return result
            if iteration == max_iterations:
                raise AssemblyPathError('global assembly iteration budget exhausted')
            step = np.zeros(6*self._nodes)
            try:
                step[self._free] = np.linalg.solve(response.tangent[np.ix_(self._free, self._free)], -residual[self._free])
            except np.linalg.LinAlgError as exc:
                raise AssemblyPathError('singular global assembly tangent') from exc
            if not np.isfinite(step).all():
                raise AssemblyPathError('nonfinite global assembly step')
            for backtrack in range(10):
                delta = (step*.5**backtrack).reshape(self._nodes, 6)
                if np.max(np.linalg.norm(delta[:, 3:], axis=1)) >= .9*np.pi:
                    continue
                made_x = x+delta[:, :3]
                made_u = np.array([rotation(d[3:]) @ old for d, old in zip(delta, u)])
                try:
                    made = self._solve_all(made_x, made_u, state.histories, budget)
                except (ValueError, NonlinearLocalError, np.linalg.LinAlgError):
                    continue
                if self._norm(made.residual-external, forces) < norm:
                    x, u, response = made_x, made_u, made
                    break
            else:
                raise AssemblyPathError('assembly line search failed; explicit cutback required')
        raise AssertionError('unreachable assembly iteration')

    def _owned(self, trial):
        if trial is None or trial is not self._pending or trial.origin_epoch != self._checkpoint[0].epoch:
            raise AssemblyTransactionError('owned current assembly trial required')

    def _reconstruct_element(self, index, trial):
        ref, row, section = self._references[index], self._maps[index], self._sections[index]
        old = trial.response.elements[index]
        model = NonlinearMixedBeamProbe(ref, section, order=self._order, origins=trial.origins[index])
        made = model.evaluate(trial.positions[row], trial.rotations[row] @ ref.nodal_triads,
                              old.local_rotations, old.moments)
        h = made.hessian
        np.linalg.cholesky(-h[24:, 24:])
        np.linalg.cholesky(h[18:24, 18:24]-h[18:24, 24:] @ np.linalg.solve(h[24:, 24:], h[24:, 18:24]))
        tangent = h[:18, :18]-h[:18, 18:] @ np.linalg.solve(h[18:, 18:], h[18:, :18])
        return replace(old, potential=made.potential, residual=_readonly(made.residual[:18]), tangent=_readonly(tangent),
            local_rotations=_readonly(old.local_rotations), moments=_readonly(old.moments), stations=made.stations,
            local_residual_norm=float(np.linalg.norm(made.residual[18:], np.inf)))

    def _reconstruct(self, trial):
        if len(trial.response.elements) != len(self._maps) or len(trial.origins) != len(self._maps):
            raise ValueError('complete replay element/history inventory required')
        return self._scatter(tuple(self._reconstruct_element(i, trial) for i in range(len(self._maps))))

    def _validated(self, trial):
        response = self._reconstruct(trial)
        if digest(response) != digest(trial.response):
            raise AssemblyTransactionError('accepted-origin assembly replay mismatch')
        norm = self._norm(response.residual-self._external(trial.forces), trial.forces)
        if (norm > 1e-11 or norm != trial.residual_norm
                or not np.array_equal(trial.positions[self._fixed], self._coordinates[self._fixed])
                or not np.array_equal(trial.rotations[self._fixed], np.tile(np.eye(3), (len(self._fixed), 1, 1)))):
            raise AssemblyTransactionError('assembled equilibrium or fixed-node mismatch')
        histories = []
        for element in response.elements:
            if element.local_residual_norm > 1e-11:
                raise AssemblyTransactionError('element local equilibrium mismatch')
            if [(s.cell, s.index) for s in element.stations] != [(c, i) for c in (0, 1) for i in range(self._order)]:
                raise AssemblyTransactionError('element station order mismatch')
            histories.append(tuple(_history(s.response.history) for s in element.stations))
        return response, tuple(histories)

    def commit(self, trial):
        self._owned(trial)
        try:
            if digest(trial) != self._pending_digest:
                raise AssemblyTransactionError('altered assembly trial')
            response, histories = self._validated(trial)
            state = AssemblyState(trial.origin_epoch+1, _readonly(trial.positions), _readonly(trial.rotations),
                                  _readonly(trial.forces), histories)
            accepted = deepcopy(replace(trial, response=response))
            exported = deepcopy(state)
        except (ValueError, TypeError, np.linalg.LinAlgError) as exc:
            raise AssemblyTransactionError('all-element commit validation failed') from exc
        self._checkpoint = (state, accepted)
        self._pending = self._pending_digest = None
        return exported

    def discard(self, trial):
        self._owned(trial)
        self._pending = self._pending_digest = None

    def replay(self):
        accepted = self._checkpoint[1]
        if accepted is None:
            raise AssemblyTransactionError('no accepted assembly increment')
        try:
            response, histories = self._validated(accepted)
            if histories != self._checkpoint[0].histories:
                raise AssemblyTransactionError('committed assembly histories mismatch')
            return response
        except (ValueError, TypeError, np.linalg.LinAlgError) as exc:
            raise AssemblyTransactionError('accepted assembly replay validation failed') from exc
