"""Small research reference-chain solve with compensated displacement storage.

One to two three-node macro elements only. No nonlinear assembly, solver
registration, performance claim, or qualification authority is supplied.
"""

from dataclasses import dataclass
import math

import numpy as np

from docs.reference_cases.ge_beam3_curved_p5_directional_probe import DirectionalResponseProbe
from docs.reference_cases.ge_beam3_curved_p5_finite_probe import _array, _readonly
from docs.reference_cases.ge_beam3_curved_p5_precise_reference_probe import PreciseReferenceAction


class ChainSolveError(RuntimeError):
    """The bounded reference-chain solve did not meet its residual check."""


def two_sum(a, b):
    total = a+b
    virtual_b = total-a
    error = (a-(total-virtual_b))+(b-virtual_b)
    return total, error


def add_expansion(high, low, increment):
    """Retain the rounding remainder; this does not introduce new DOFs."""
    summed, remainder = two_sum(high, increment)
    return two_sum(summed, low+remainder)


@dataclass(frozen=True)
class ChainResponse:
    displacement_high: np.ndarray
    displacement_low: np.ndarray
    reactions: np.ndarray
    residual_norm: float
    iterations: int


class ReferenceChainProbe:
    """Clamped first node, conforming ordered chain; dense K is preconditioner only."""

    def __init__(self, references, section, *, action_backend="directional"):
        if action_backend not in ("directional", "decimal-flexibility"):
            raise ValueError("explicit reference action backend required")
        self.action_backend = action_backend
        references = tuple(references)
        if len(references) not in (1, 2):
            raise ValueError("research chain is limited to one or two macro elements")
        for previous, current in zip(references, references[1:]):
            if (not np.array_equal(previous.coordinates[-1], current.coordinates[0])
                    or not np.array_equal(previous.nodal_triads[-1], current.nodal_triads[0])):
                raise ValueError("chain requires identical shared reference node and frame")
        self.references = references
        self.size = 6*(2*len(references)+1)
        self.coordinates = np.vstack((references[0].coordinates,
                                      *[ref.coordinates[1:] for ref in references[1:]]))
        self.models = tuple(DirectionalResponseProbe(ref, section, ref.coordinates, ref.nodal_triads)
                            for ref in references)
        self.responses = tuple(model.evaluate() for model in self.models)
        self.precise_actions = tuple(PreciseReferenceAction(ref, section) for ref in references) if (
            action_backend == "decimal-flexibility") else ()
        self.maps = tuple(np.arange(12*index, 12*index+18) for index in range(len(references)))
        preconditioner = np.zeros((self.size, self.size))
        for response, indices in zip(self.responses, self.maps):
            preconditioner[np.ix_(indices, indices)] += response.tangent
        self.preconditioner = _readonly(preconditioner[6:, 6:])

    def action(self, high, low=None):
        high = _array(high, (self.size,), "displacement high")
        low = np.zeros(self.size) if low is None else _array(low, (self.size,), "displacement low")
        contributions = [[] for _ in range(self.size)]
        for cell, (model, response, indices) in enumerate(zip(self.models, self.responses, self.maps)):
            if self.action_backend == "decimal-flexibility":
                local = self.precise_actions[cell].action(high[indices], low[indices])
                for index, value in zip(indices, local):
                    contributions[index].append(float(value))
                continue
            for values in (high, low):
                if not np.any(values[indices]):
                    continue
                local = model.tangent_action(response, values[indices]).action
                for index, value in zip(indices, local):
                    contributions[index].append(float(value))
        return np.array([math.fsum(values) for values in contributions])

    def solve(self, loads, *, max_iterations=12):
        loads = _array(loads, (self.size,), "nodal loads")
        if (not isinstance(max_iterations, int) or isinstance(max_iterations, bool)
                or not 0 <= max_iterations <= 12):
            raise ValueError("reference refinement limit must be an integer from 0 to 12")
        high, low = np.zeros(self.size), np.zeros(self.size)
        scale = max(1., float(np.linalg.norm(loads[6:], ord=np.inf)))
        for iteration in range(max_iterations+1):
            force = self.action(high, low)
            residual = loads-force
            norm = float(np.linalg.norm(residual[6:], ord=np.inf))
            if norm <= 1e-11*scale:
                reactions = force-loads
                return ChainResponse(_readonly(high), _readonly(low), _readonly(reactions), norm, iteration)
            if iteration == max_iterations:
                break
            try:
                correction = np.linalg.solve(self.preconditioner, residual[6:])
            except np.linalg.LinAlgError as exc:
                raise ChainSolveError("singular dense preconditioner") from exc
            if not np.isfinite(correction).all():
                raise ChainSolveError("nonfinite reference correction")
            high[6:], low[6:] = add_expansion(high[6:], low[6:], correction)
        raise ChainSolveError("reference refinement budget exhausted")
