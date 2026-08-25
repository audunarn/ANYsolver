"""Read-only assembly of committed formulation-native tangent components."""

from __future__ import annotations

from collections.abc import Mapping
import math
from typing import TYPE_CHECKING, Any, Dict

import numpy as np
from scipy import sparse
from scipy.sparse import linalg as sparse_linalg

from .e4_pl_s3_element import (
    CURRENT_STATE_BUBBLE_PROJECTION_POLICY_ID,
    CURRENT_STATE_TANGENT_DECOMPOSITION_POLICY_ID,
)
from .e4_pl_s3_state import canonical_json_bytes
from .element_capabilities import ElementCapabilityError
from .nonlinear_state import (
    NonlinearStateStore,
    begin_state_evaluation,
    create_model_native_rotation_store,
    discard_active_state_candidate,
)

if TYPE_CHECKING:
    from .fe_core import FEModel


def _positive_layer_count(value: Any) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, np.integer)
    ):
        raise ValueError("current_state_num_layers must be a positive integer")
    made = int(value)
    if made <= 0:
        raise ValueError("current_state_num_layers must be a positive integer")
    return made


def _normalized_exact_states(
    model: "FEModel",
    element_states: Any,
) -> Dict[int, Mapping[str, Any]]:
    if not isinstance(element_states, Mapping):
        raise TypeError(
            "committed current tangent requires an element-state mapping"
        )
    normalized: Dict[int, Mapping[str, Any]] = {}
    for raw_element_id, state in element_states.items():
        element_id = int(raw_element_id)
        if element_id in normalized:
            raise ValueError(
                "committed current tangent element-state IDs are ambiguous"
            )
        if not isinstance(state, Mapping):
            raise TypeError(
                "committed current tangent requires a state mapping for "
                f"element {element_id}"
            )
        normalized[element_id] = state
    expected_ids = {int(value) for value in model.mesh.elements}
    supplied_ids = set(normalized)
    if supplied_ids != expected_ids:
        missing = sorted(expected_ids - supplied_ids)
        unknown = sorted(supplied_ids - expected_ids)
        raise ValueError(
            "committed current tangent requires exactly one model-bound state "
            f"per element; missing={missing}, unknown={unknown}"
        )
    return normalized


def require_committed_tangent_component_api(model: "FEModel", *, context: str) -> None:
    """Fail before mechanics when any element lacks the qualified API."""

    unsupported = [
        int(element_id)
        for element_id, element in sorted(model.mesh.elements.items())
        if not callable(
            getattr(element, "compute_committed_current_tangent_components", None)
        )
    ]
    if unsupported:
        labels = ", ".join(str(value) for value in unsupported)
        raise ElementCapabilityError(
            f"{context} requires a formulation-native committed material/stress-"
            f"Hessian decomposition; unsupported element IDs [{labels}]"
        )


def validate_committed_current_tangent_inputs(
    model: "FEModel",
    displacements: Any,
    element_states: Any,
    num_layers: int,
    *,
    context: str,
) -> None:
    """Validate the complete authority profile without evaluating mechanics."""

    require_committed_tangent_component_api(model, context=context)
    _positive_layer_count(num_layers)
    total_dofs = int(model.mesh.dof_manager.total_dofs)
    full = np.asarray(displacements, dtype=np.float64)
    if full.shape != (total_dofs,) or not np.all(np.isfinite(full)):
        raise ValueError(
            "committed current tangent requires the complete finite committed "
            "displacement vector"
        )
    _normalized_exact_states(model, element_states)


def _relative_sparse_error(left: sparse.spmatrix, right: sparse.spmatrix) -> float:
    denominator = max(float(sparse_linalg.norm(right)), 1.0)
    return float(sparse_linalg.norm(left) / denominator)


def assemble_committed_current_tangent_components(
    model: "FEModel",
    displacements: Any,
    element_states: Any,
    num_layers: int = 5,
) -> tuple[sparse.csr_matrix, sparse.csr_matrix, sparse.csr_matrix, Dict[str, Any]]:
    """Assemble ``Kmaterial``, ``Kgeometric`` and their consistent total.

    ``Kgeometric`` is the internal-force stress/resultant Hessian and is
    tension-positive.  Consequently ``-Kgeometric`` is the compression-positive
    destabilizing operator used by current-state buckling.  The input state is
    copied into a disposable native rotation transaction and is never updated.
    Matrices and bubble sensitivities are returned transiently and are not
    attached to the model, element, state store, or an analysis session.
    """

    validate_committed_current_tangent_inputs(
        model,
        displacements,
        element_states,
        num_layers,
        context="assemble_committed_current_tangent_components",
    )
    layers = _positive_layer_count(num_layers)
    total_dofs = int(model.mesh.dof_manager.total_dofs)
    full = np.asarray(displacements, dtype=np.float64)
    if full.shape != (total_dofs,) or not np.all(np.isfinite(full)):
        raise ValueError(
            "committed current tangent requires the complete finite committed "
            "displacement vector"
        )
    normalized_states = _normalized_exact_states(model, element_states)
    state_bytes_before = {
        element_id: canonical_json_bytes(state)
        for element_id, state in normalized_states.items()
    }

    store = NonlinearStateStore.from_shell_layouts((), normalized_states)
    rotation_store = create_model_native_rotation_store(model, store, full)
    if rotation_store is None:
        raise ElementCapabilityError(
            "committed current tangent requires formulation-native rotation state"
        )
    store.attach_native_rotation_store(rotation_store)
    token = begin_state_evaluation(
        store,
        model=model,
        displacements=full,
    )
    if token is None:
        raise RuntimeError("committed current tangent transaction did not start")

    rows: list[np.ndarray] = []
    columns: list[np.ndarray] = []
    material_data: list[np.ndarray] = []
    geometric_data: list[np.ndarray] = []
    total_data: list[np.ndarray] = []
    element_info: Dict[str, Any] = {}
    try:
        for element_id, element in sorted(model.mesh.elements.items()):
            element_id = int(element_id)
            dofs = np.asarray(element.get_dof_mapping(model.mesh), dtype=np.intp)
            if dofs.shape != (18,):
                raise ElementCapabilityError(
                    "committed current tangent qualified API currently admits "
                    f"18-DOF S3 elements only; element {element_id} has {dofs.size}"
                )
            reference_directors = np.asarray(
                element.native_reference_directors(model.mesh),
                dtype=np.float64,
            )
            native_view = store.native_element_rotation_view(
                token,
                element_id,
                tuple(int(value) for value in element.node_ids),
                reference_directors,
            )
            components = element.compute_committed_current_tangent_components(
                model.mesh,
                model.get_material(element.material_name),
                full[dofs],
                normalized_states[element_id],
                layers,
                native_rotation_trial=native_view,
            )
            material = np.asarray(components.get("material", ()), dtype=np.float64)
            geometric = np.asarray(components.get("geometric", ()), dtype=np.float64)
            total = np.asarray(components.get("total", ()), dtype=np.float64)
            if (
                material.shape != (18, 18)
                or geometric.shape != (18, 18)
                or total.shape != (18, 18)
                or not np.all(np.isfinite(material))
                or not np.all(np.isfinite(geometric))
                or not np.all(np.isfinite(total))
            ):
                raise ValueError(
                    f"committed tangent components for element {element_id} are incompatible"
                )
            rows.append(np.repeat(dofs, dofs.size))
            columns.append(np.tile(dofs, dofs.size))
            material_data.append(material.ravel())
            geometric_data.append(geometric.ravel())
            total_data.append(total.ravel())
            element_info[str(element_id)] = {
                "state_digest": str(components["state_digest"]),
                "relative_decomposition_error": float(
                    components["relative_decomposition_error"]
                ),
                "relative_symmetry_error": float(
                    components["relative_symmetry_error"]
                ),
                "bubble_projection_policy_id": str(
                    components["bubble_projection_policy_id"]
                ),
                "matrix_persistence": "none",
            }
    finally:
        discard_active_state_candidate(store)

    state_bytes_after = {
        element_id: canonical_json_bytes(state)
        for element_id, state in normalized_states.items()
    }
    if state_bytes_after != state_bytes_before:
        raise RuntimeError("committed current tangent mutated an input state")

    if rows:
        row = np.concatenate(rows)
        column = np.concatenate(columns)

        def assembled(values: list[np.ndarray]) -> sparse.csr_matrix:
            return sparse.coo_matrix(
                (np.concatenate(values), (row, column)),
                shape=(total_dofs, total_dofs),
                dtype=np.float64,
            ).tocsr()

        material_matrix = assembled(material_data)
        geometric_matrix = assembled(geometric_data)
        total_matrix = assembled(total_data)
    else:
        material_matrix = sparse.csr_matrix((total_dofs, total_dofs), dtype=float)
        geometric_matrix = sparse.csr_matrix((total_dofs, total_dofs), dtype=float)
        total_matrix = sparse.csr_matrix((total_dofs, total_dofs), dtype=float)

    decomposition_error = _relative_sparse_error(
        total_matrix - material_matrix - geometric_matrix,
        total_matrix,
    )
    symmetry_error = max(
        _relative_sparse_error(matrix - matrix.T, matrix)
        for matrix in (material_matrix, geometric_matrix, total_matrix)
    )
    if (
        not math.isfinite(decomposition_error)
        or not math.isfinite(symmetry_error)
        or decomposition_error > 512.0 * np.finfo(np.float64).eps
        or symmetry_error > 512.0 * np.finfo(np.float64).eps
    ):
        raise ValueError(
            "assembled committed tangent violates its decomposition or symmetry bound"
        )
    material_matrix = (0.5 * (material_matrix + material_matrix.T)).tocsr()
    geometric_matrix = (0.5 * (geometric_matrix + geometric_matrix.T)).tocsr()
    total_matrix = (0.5 * (total_matrix + total_matrix.T)).tocsr()
    state_digests = {
        str(element_id): str(
            state.get(
                "state_digest",
                state.get("state_integrity_sha256", ""),
            )
        )
        for element_id, state in sorted(normalized_states.items())
    }
    return material_matrix, geometric_matrix, total_matrix, {
        "matrix_type": "committed_current_tangent_components",
        "policy_id": CURRENT_STATE_TANGENT_DECOMPOSITION_POLICY_ID,
        "bubble_projection_policy_id": CURRENT_STATE_BUBBLE_PROJECTION_POLICY_ID,
        "geometric_sign_convention": (
            "internal_tension_positive_stress_hessian; negative_is_"
            "compression_positive_destabilizing"
        ),
        "matrix_persistence": "none",
        "factorization_persistence": "none",
        "state_digests": state_digests,
        "state_immutability_verified": True,
        "relative_decomposition_error": decomposition_error,
        "relative_symmetry_error": symmetry_error,
        "num_layers": layers,
        "element_components": element_info,
        "state_storage": store.diagnostics(),
    }


__all__ = [
    "assemble_committed_current_tangent_components",
    "require_committed_tangent_component_api",
    "validate_committed_current_tangent_inputs",
]
