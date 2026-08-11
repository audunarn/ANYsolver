"""Qualification tests for incremental impact-damage matrix updates."""

from __future__ import annotations

import numpy as np

from anysolver.contact import _assemble_damaged_linear_matrices, _linear_element_matrix_terms
from anysolver.damage_matrix_performance import DamageMatrixPlan
from anysolver.elements import ShellElement
from anysolver.fe_core import FEModel


def _panel(nx: int = 2, ny: int = 2) -> FEModel:
    model = FEModel("damage_matrix_panel")
    model.add_material("steel", 2.1e11, 0.3, density=7850.0)
    node_ids: dict[tuple[int, int], int] = {}
    node_id = 1
    for j in range(ny + 1):
        for i in range(nx + 1):
            model.add_node(node_id, float(i), float(j), 0.0)
            node_ids[(i, j)] = node_id
            node_id += 1
    element_id = 1
    for j in range(ny):
        for i in range(nx):
            model.add_element(
                element_id,
                ShellElement(
                    element_id,
                    [
                        node_ids[(i, j)],
                        node_ids[(i + 1, j)],
                        node_ids[(i + 1, j + 1)],
                        node_ids[(i, j + 1)],
                    ],
                    "steel",
                    thickness=0.02,
                ),
            )
            element_id += 1
    model.add_point_mass(node_ids[(1, 1)], 7.25)
    return model


def _assert_matrix_parity(candidate, reference) -> None:
    np.testing.assert_allclose(
        candidate.toarray(),
        reference.toarray(),
        rtol=5.0e-14,
        atol=1.0e-8,
    )


def test_incremental_damage_sequence_matches_scalar_and_keeps_csr_identity() -> None:
    model = _panel()
    terms = _linear_element_matrix_terms(model)
    plan = DamageMatrixPlan.build(model, terms)
    stiffness_identity = (id(plan.stiffness), id(plan.stiffness.data), id(plan.stiffness.indices))
    mass_identity = (id(plan.mass), id(plan.mass.data), id(plan.mass.indices))
    sequences = (
        {},
        {1: 0.75},
        {1: 0.5, 3: 0.0},
        {3: 0.25},  # Element 1 is omitted and must reset to an exact scale of one.
        {1: 1.4, 2: -0.2, 4: 0.6},  # Preserve the legacy [0, 1] scale clamp.
        {},
        {4: 0.6},
        {4: 0.6},  # No-change update must not touch matrix storage.
    )

    for scales in sequences:
        reference_k, reference_m = _assemble_damaged_linear_matrices(model, scales, cached_terms=terms)
        candidate_k, candidate_m = _assemble_damaged_linear_matrices(model, scales, cached_terms=plan)
        assert candidate_k is plan.stiffness
        assert candidate_m is plan.mass
        assert (id(candidate_k), id(candidate_k.data), id(candidate_k.indices)) == stiffness_identity
        assert (id(candidate_m), id(candidate_m.data), id(candidate_m.indices)) == mass_identity
        _assert_matrix_parity(candidate_k, reference_k)
        _assert_matrix_parity(candidate_m, reference_m)

    diagnostics = plan.diagnostics()
    assert diagnostics["fast_path_name"] == "incremental_damage_csr_updates"
    assert diagnostics["eligible_element_count"] == len(model.mesh.elements)
    assert diagnostics["update_count"] == len(sequences)
    assert diagnostics["no_change_count"] >= 2
    assert diagnostics["changed_element_count"] > 0
    assert diagnostics["fallback_count"] == 0
    assert diagnostics["retained_bytes"] > 0


def test_zero_element_scales_preserve_point_mass_and_reset_to_one() -> None:
    model = _panel()
    terms = _linear_element_matrix_terms(model)
    plan = DamageMatrixPlan.build(model, terms)
    all_zero = {element_id: 0.0 for element_id in model.mesh.elements}

    zero_k, zero_m = plan.update(model, all_zero)
    reference_zero_k, reference_zero_m = _assemble_damaged_linear_matrices(
        model,
        all_zero,
        cached_terms=terms,
    )
    _assert_matrix_parity(zero_k, reference_zero_k)
    _assert_matrix_parity(zero_m, reference_zero_m)
    center = model.mesh.get_node(5)
    assert center is not None
    np.testing.assert_allclose(
        zero_m.diagonal()[np.asarray(center.dofs[:3], dtype=int)],
        np.full(3, 7.25),
        rtol=0.0,
        atol=1.0e-12,
    )

    reset_k, reset_m = plan.update(model, {})
    reference_k, reference_m = _assemble_damaged_linear_matrices(model, {}, cached_terms=terms)
    _assert_matrix_parity(reset_k, reference_k)
    _assert_matrix_parity(reset_m, reference_m)
    assert plan.diagnostics()["active_scaled_element_count"] == 0


def test_model_revision_invalidates_plan_and_helper_falls_back_to_scalar() -> None:
    model = _panel()
    plan = DamageMatrixPlan.build(model, _linear_element_matrix_terms(model))
    plan.update(model, {1: 0.5})
    model.bump_revision("geometry")

    fallback_k, fallback_m = _assemble_damaged_linear_matrices(
        model,
        {1: 0.4, 2: 0.8},
        cached_terms=plan,
    )
    current_terms = _linear_element_matrix_terms(model)
    reference_k, reference_m = _assemble_damaged_linear_matrices(
        model,
        {1: 0.4, 2: 0.8},
        cached_terms=current_terms,
    )

    assert fallback_k is not plan.stiffness
    assert fallback_m is not plan.mass
    _assert_matrix_parity(fallback_k, reference_k)
    _assert_matrix_parity(fallback_m, reference_m)
    diagnostics = plan.diagnostics()
    assert diagnostics["invalidation_count"] == 1
    assert diagnostics["fallback_count"] == 1
    assert diagnostics["fallback_reason"] == "model_revision_changed"

    replacement = DamageMatrixPlan.build(model, current_terms)
    replacement_k, replacement_m = replacement.update(model, {1: 0.4, 2: 0.8})
    _assert_matrix_parity(replacement_k, reference_k)
    _assert_matrix_parity(replacement_m, reference_m)
