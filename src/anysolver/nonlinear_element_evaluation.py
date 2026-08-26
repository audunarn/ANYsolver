"""Single scalar invocation seam for nonlinear element mechanics.

Legacy and qualified-Q4 elements retain their exact positional call.  Only a
formulation-native total-Lagrangian element receives the solver-owned,
node-shared multiplicative rotation view.  Keeping this dispatch central makes
it impossible for one assembly lane to reconstruct element-owned rotations or
silently fall back to additive coordinates.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional

import numpy as np

from .nonlinear_state import (
    NonlinearStateStore,
    StateTransactionError,
    StateTrialToken,
)


class NativeNonlinearEvaluationError(StateTransactionError):
    """A native element was invoked without its solver-owned trial context."""


def require_legacy_direct_nonlinear_element(
    element: Any,
    *,
    context: str,
) -> None:
    """Guard the few intentionally direct legacy/batch recovery calls."""

    if bool(getattr(element, "formulation_native_total_lagrangian", False)):
        raise NativeNonlinearEvaluationError(
            f"{context} cannot directly evaluate a formulation-native total-"
            "Lagrangian element; route through evaluate_nonlinear_element"
        )


def evaluate_nonlinear_element(
    element: Any,
    mesh: Any,
    material: Any,
    element_displacements: Any,
    committed_state: Any,
    num_layers: int,
    tangent: bool,
    *,
    committed_states: Mapping[int, Any],
    state_token: Optional[StateTrialToken],
    element_id: Any,
) -> tuple[Any, Any, Any]:
    """Evaluate one element while preserving the established Q4 call path."""

    if not bool(getattr(element, "formulation_native_total_lagrangian", False)):
        return element.compute_nonlinear_response(
            mesh,
            material,
            element_displacements,
            committed_state,
            num_layers,
            tangent,
        )

    if not isinstance(committed_states, NonlinearStateStore) or state_token is None:
        raise NativeNonlinearEvaluationError(
            "Formulation-native nonlinear evaluation requires an active "
            "solver-owned state transaction"
        )
    provider = getattr(element, "native_reference_directors", None)
    if not callable(provider):
        raise NativeNonlinearEvaluationError(
            f"Native element {int(element_id)} does not expose reference directors"
        )
    reference_directors = np.asarray(provider(mesh), dtype=np.float64)
    node_ids = tuple(int(value) for value in getattr(element, "node_ids", ()))
    if reference_directors.shape != (len(node_ids), 3):
        raise NativeNonlinearEvaluationError(
            f"Native element {int(element_id)} returned incompatible reference directors"
        )
    native_trial = committed_states.native_element_rotation_view(
        state_token,
        element_id,
        node_ids,
        reference_directors,
    )
    return element.compute_nonlinear_response(
        mesh,
        material,
        element_displacements,
        committed_state,
        num_layers,
        tangent,
        native_rotation_trial=native_trial,
    )


__all__ = [
    "NativeNonlinearEvaluationError",
    "evaluate_nonlinear_element",
    "require_legacy_direct_nonlinear_element",
]
