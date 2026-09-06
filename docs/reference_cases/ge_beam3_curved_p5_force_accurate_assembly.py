"""Opt-in P5 local-accuracy assembly; no production or restart codec.

The original assembly remains unmodified. This successor reuses its scatter,
global equations and atomic transactions, with explicit local error estimates
bound into each response and independently recomputed during accepted replay.
"""

from dataclasses import dataclass, fields, replace
import math

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_assembly_history_probe import (
    NonlinearAssemblyHistoryProbe, AssemblyTransactionError,
)
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _readonly
from docs.reference_cases.ge_beam3_curved_p5_nonlinear_mixed_probe import (
    NonlinearMixedBeamProbe, NonlinearCondensedResponse, LocalForceAccuracy, _accuracy_metrics,
)


SCHEMA = 'GE_BEAM3_P5_ASSEMBLY_LOCAL_FORCE_ACCURACY_V1'
TOTAL_FORCE_BUDGET = 1e-12


@dataclass(frozen=True)
class ForceAccurateElementResponse(NonlinearCondensedResponse):
    accuracy_schema: str
    force_accuracy: LocalForceAccuracy
    estimated_force_error: float


class ForceAccurateAssemblyHistoryProbe(NonlinearAssemblyHistoryProbe):
    """Explicit successor, fixed one-tenth global-equilibrium error budget.

Each of N elements receives 1e-12/N in absolute force units using the full
assembly diameter for moment scaling. Force normalization is conservatively
one; the existing global normalization is at least one. These are linearized
estimates, not rigorous bounds on residual arithmetic or nonlinear remainder.
"""

    _mixed_type = NonlinearMixedBeamProbe
    _accuracy_schema = SCHEMA

    @property
    def local_accuracy(self):
        return LocalForceAccuracy(TOTAL_FORCE_BUDGET/len(self._maps), float(self._length), 1.)

    def _check_element_accuracy(self, response):
        expected = self.local_accuracy
        if (type(response) is not ForceAccurateElementResponse or
                response.accuracy_schema != self._accuracy_schema or response.force_accuracy != expected or
                type(response.estimated_force_error) is not float or
                not math.isfinite(response.estimated_force_error) or
                not 0 <= response.estimated_force_error <= expected.limit):
            raise AssemblyTransactionError('local force accuracy policy/estimate mismatch')

    def _scatter(self, elements):
        for response in elements:
            self._check_element_accuracy(response)
        if math.fsum(e.estimated_force_error for e in elements) > TOTAL_FORCE_BUDGET:
            raise AssemblyTransactionError('aggregate local force error budget exceeded')
        return super()._scatter(elements)

    def _solve_all(self, positions, rotations, origins, budget):
        if len(origins) != len(self._maps):
            raise ValueError('complete element history inventory required')

        class CountedMixed(self._mixed_type):
            def evaluate(inner, *args, **kwargs):
                budget.consume()
                result = super().evaluate(*args, **kwargs)
                inner.last_evaluation = result
                return result

        responses = []
        accuracy = self.local_accuracy
        for ref, row, section, history in zip(self._references, self._maps, self._sections, origins):
            model = CountedMixed(ref, section, order=self._order, origins=history)
            solved = model.solve(positions[row], rotations[row] @ ref.nodal_triads,
                                 force_accuracy=accuracy)
            # The local solve returns its last evaluated iterate. Retain only
            # the scalar estimate, not a cached matrix as replay authority.
            error = _accuracy_metrics(model.last_evaluation, accuracy)[1]
            values = {f.name: getattr(solved, f.name) for f in fields(NonlinearCondensedResponse)}
            responses.append(ForceAccurateElementResponse(**values, accuracy_schema=self._accuracy_schema,
                             force_accuracy=accuracy, estimated_force_error=error))
        return self._scatter(responses)

    def _reconstruct_element(self, index, trial):
        ref, row, section = self._references[index], self._maps[index], self._sections[index]
        old = trial.response.elements[index]
        self._check_element_accuracy(old)
        model = self._mixed_type(ref, section, order=self._order, origins=trial.origins[index])
        made = model.evaluate(trial.positions[row], trial.rotations[row] @ ref.nodal_triads,
                              old.local_rotations, old.moments)
        error = _accuracy_metrics(made, self.local_accuracy)[1]
        h = made.hessian
        np.linalg.cholesky(-h[24:, 24:])
        np.linalg.cholesky(h[18:24, 18:24]-h[18:24, 24:] @ np.linalg.solve(h[24:, 24:], h[24:, 18:24]))
        tangent = h[:18, :18]-h[:18, 18:] @ np.linalg.solve(h[18:, 18:], h[18:, :18])
        result = replace(old, potential=made.potential, residual=_readonly(made.residual[:18]),
            tangent=_readonly(tangent), local_rotations=_readonly(old.local_rotations),
            moments=_readonly(old.moments), stations=made.stations,
            local_residual_norm=float(np.linalg.norm(made.residual[18:], np.inf)),
            estimated_force_error=error)
        self._check_element_accuracy(result)
        return result
