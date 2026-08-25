"""Focused qualification of the bounded qualified-S3 reference batch."""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np
import pytest

import anysolver.s3_reference_batch as s3_batch_module
from anysolver.activity import ElementActivity
from anysolver.e4_pl_element import QualifiedE4PLShellElement
from anysolver.e4_pl_s3_element import QualifiedE4PLS3ShellElement
from anysolver.fe_core import FEModel
from anysolver.matrix_assembly import assemble_stiffness_matrix
from anysolver.materials import Hill48Yield
from anysolver.recovery import (
    RecoveryConfig,
    ResourceConfig,
    _compute_one_element_stress,
    recover_element_stresses_with_report,
    recover_stress_result,
)
from anysolver.s3_reference_batch import (
    MIN_REFERENCE_S3_RECOVERY_GROUP,
    REFERENCE_S3_BATCH_POLICY_ID,
    REFERENCE_S3_FORMULATION_ID,
    prepare_reference_s3_components,
    reference_s3_eligibility,
)
from anysolver.shell_sections import GeneralizedShellSection


def _build_model(
    count: int,
    *,
    include_q4: bool = False,
    shell_section: GeneralizedShellSection | None = None,
    material_name: str = "steel",
    reverse_winding: bool = False,
    reference_surface_offset: float = 0.0,
) -> FEModel:
    model = FEModel("qualified-s3-reference-batch")
    if material_name == "steel":
        model.add_material("steel", 210.0e9, 0.3, density=7850.0)
    elif material_name == "history":
        model.add_material("history", 210.0e9, 0.3, density=7850.0)
        model.materials["history"].hardening_curve = object()
    elif material_name == "hill":
        model.add_material("hill", 210.0e9, 0.3, density=7850.0)
        model.materials["hill"].hill_yield = Hill48Yield(
            400.0e6,
            350.0e6,
            300.0e6,
            220.0e6,
            210.0e6,
            200.0e6,
        )
    elif material_name == "orthotropic":
        model.add_orthotropic_material(
            "orthotropic",
            150.0e9,
            90.0e9,
            70.0e9,
            0.18,
            0.16,
            0.15,
            48.0e9,
            42.0e9,
            36.0e9,
            density=1600.0,
        )
    else:  # pragma: no cover - helper contract
        raise AssertionError(material_name)

    next_node = 1
    elements = []
    for index in range(int(count)):
        x = float(8 * index)
        node_ids = [next_node, next_node + 1, next_node + 2]
        for node_id, coordinate in zip(
            node_ids,
            ((x, 0.0, 0.0), (x + 3.0, 0.0, 0.0), (x, 3.0, 0.0)),
        ):
            model.add_node(node_id, *coordinate)
        if reverse_winding:
            node_ids = [node_ids[0], node_ids[2], node_ids[1]]
        element_id = index + 1
        elements.append(
            (
                element_id,
                QualifiedE4PLS3ShellElement(
                    element_id,
                    node_ids,
                    material_name,
                    thickness=0.05,
                    shell_section=shell_section,
                    material_direction=(
                        np.asarray((1.0, 0.0, 0.0))
                        if material_name == "orthotropic"
                        else None
                    ),
                    reference_normal=(0.0, 0.0, 1.0),
                    reference_surface_offset=reference_surface_offset,
                ),
            )
        )
        next_node += 3

    if include_q4:
        q4_nodes = [next_node + offset for offset in range(4)]
        x = float(8 * count + 8)
        for node_id, coordinate in zip(
            q4_nodes,
            (
                (x, 0.0, 0.0),
                (x + 3.0, 0.0, 0.0),
                (x + 3.0, 3.0, 0.0),
                (x, 3.0, 0.0),
            ),
        ):
            model.add_node(node_id, *coordinate)
        element_id = int(count) + 1
        elements.append(
            (
                element_id,
                QualifiedE4PLShellElement(
                    element_id,
                    q4_nodes,
                    "steel",
                    thickness=0.05,
                ),
            )
        )
    for element_id, element in elements:
        model.add_element(element_id, element)
    return model


def _payload_bytes_equal(
    actual: Mapping[int, Mapping[str, Any]],
    expected: Mapping[int, Mapping[str, Any]],
) -> None:
    assert tuple(actual) == tuple(expected)
    for element_id in expected:
        assert tuple(actual[element_id]) == tuple(expected[element_id])
        for name, expected_value in expected[element_id].items():
            actual_value = actual[element_id][name]
            if isinstance(expected_value, np.ndarray):
                assert isinstance(actual_value, np.ndarray)
                assert actual_value.dtype == expected_value.dtype
                assert actual_value.shape == expected_value.shape
                assert actual_value.tobytes(order="C") == expected_value.tobytes(
                    order="C"
                )
            else:
                assert actual_value == expected_value


def _section() -> GeneralizedShellSection:
    return GeneralizedShellSection(
        A=np.diag((2.0e8, 2.0e8, 8.0e7)),
        B=np.zeros((3, 3)),
        D=np.diag((2.0e4, 2.0e4, 8.0e3)),
        As=np.diag((6.0e7, 6.0e7)),
        name="test-generalized",
    )


def test_stiffness_batch_uses_one_native_component_evaluation_and_copied_caches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _build_model(8, include_q4=True)
    calls = 0
    original = QualifiedE4PLS3ShellElement.compute_stiffness_components

    def counted(self, mesh, material):
        nonlocal calls
        calls += 1
        return original(self, mesh, material)

    monkeypatch.setattr(
        QualifiedE4PLS3ShellElement,
        "compute_stiffness_components",
        counted,
    )
    stiffness, info = assemble_stiffness_matrix(model)
    assert stiffness.shape == (
        model.mesh.dof_manager.total_dofs,
        model.mesh.dof_manager.total_dofs,
    )
    assert calls == 1
    diagnostics = info["diagnostics"][
        "qualified_s3_reference_elastic_stiffness"
    ]
    assert diagnostics == {
        "policy_id": REFERENCE_S3_BATCH_POLICY_ID,
        "formulation_id": REFERENCE_S3_FORMULATION_ID,
        "scope": "reference_elastic_isotropic_positive_winding",
        "path": "formulation_native_shared_components",
        "candidate_element_count": 8,
        "element_count": 8,
        "translation_group_element_count": 8,
        "exact_element_cache_reuse_count": 0,
        "exact_translation_group_count": 1,
        "component_evaluation_count": 1,
        "element_ids": list(range(1, 9)),
        "group_element_ids": [list(range(1, 9))],
        "fallback_reasons": {},
        "revision_key": [
            model.mesh.revisions["topology"],
            model.mesh.revisions["geometry"],
            model.mesh.revisions["material"],
        ],
        "parallel_kernel": False,
        "legacy_stiffness_batch_eligible": False,
        "legacy_nonlinear_batch_eligible": False,
        "speedup_claimed": False,
        "plan_reused": False,
    }
    first = model.mesh.elements[1]
    second = model.mesh.elements[2]
    assert first._qualified_cache_key == second._qualified_cache_key
    assert first._qualified_components is not second._qualified_components
    assert not np.shares_memory(
        first._qualified_components["total"],
        second._qualified_components["total"],
    )
    np.testing.assert_array_equal(
        first._qualified_components["total"],
        second._qualified_components["total"],
    )
    assert first.legacy_stiffness_batch_eligible is False
    assert first.legacy_nonlinear_batch_eligible is False

    scalar_model = _build_model(8, include_q4=True)
    original_get = s3_batch_module.get_reference_s3_stiffness_components

    def force_scalar(candidate_model, items):
        return (
            prepare_reference_s3_components(
                candidate_model,
                items,
                minimum_group_size=10_000,
            ),
            False,
        )

    monkeypatch.setattr(
        s3_batch_module,
        "get_reference_s3_stiffness_components",
        force_scalar,
    )
    scalar_stiffness, scalar_info = assemble_stiffness_matrix(scalar_model)
    np.testing.assert_array_equal(stiffness.toarray(), scalar_stiffness.toarray())
    assert scalar_info["diagnostics"][
        "qualified_s3_reference_elastic_stiffness"
    ]["element_count"] == 0
    monkeypatch.setattr(
        s3_batch_module,
        "get_reference_s3_stiffness_components",
        original_get,
    )

    # Activity/deletion is applied after the native matrices are prepared.
    activity = ElementActivity(range(1, 10))
    model.set_element_activity(activity)
    activity.set_activity([2], [0.25], reason="batch-qualification")
    activity.hard_delete([8], reason="batch-qualification")
    scaled, scaled_info = assemble_stiffness_matrix(model)
    dofs_2 = np.asarray(model.mesh.elements[2].get_dof_mapping(model.mesh))
    dofs_8 = np.asarray(model.mesh.elements[8].get_dof_mapping(model.mesh))
    baseline = stiffness.toarray()
    made = scaled.toarray()
    np.testing.assert_array_equal(
        made[np.ix_(dofs_2, dofs_2)],
        0.25 * baseline[np.ix_(dofs_2, dofs_2)],
    )
    assert not np.any(made[np.ix_(dofs_8, dofs_8)])
    assert scaled_info["diagnostics"]["element_activity"][
        "zero_contribution_count"
    ] == 1
    assert scaled_info["diagnostics"][
        "qualified_s3_reference_elastic_stiffness"
    ]["plan_reused"] is True


def test_stiffness_batch_is_revision_bound_and_small_groups_fall_back() -> None:
    small = _build_model(7)
    _matrix, small_info = assemble_stiffness_matrix(small)
    small_diagnostics = small_info["diagnostics"][
        "qualified_s3_reference_elastic_stiffness"
    ]
    assert small_diagnostics["element_count"] == 0
    assert small_diagnostics["translation_group_element_count"] == 0
    assert small_diagnostics["exact_element_cache_reuse_count"] == 0
    assert small_diagnostics["component_evaluation_count"] == 0
    assert small_diagnostics["fallback_reasons"] == {
        "group_below_minimum_size": list(range(1, 8))
    }
    assert small_info["diagnostics"]["scalar_shell_element_count"] == 7

    _warm_matrix, warm_info = assemble_stiffness_matrix(small)
    warm_diagnostics = warm_info["diagnostics"][
        "qualified_s3_reference_elastic_stiffness"
    ]
    assert warm_diagnostics["path"] == "formulation_native_exact_cache_reuse"
    assert warm_diagnostics["translation_group_element_count"] == 0
    assert warm_diagnostics["exact_element_cache_reuse_count"] == 7
    cache_groups = [
        group
        for group in warm_info["diagnostics"]["vectorized_shell_groups"]
        if group["kernel"] == "qualified_s3_exact_element_cache_reuse"
    ]
    assert len(cache_groups) == 1
    assert cache_groups[0]["unique_geometry_count"] == 1

    model = _build_model(8)
    _first, first_info = assemble_stiffness_matrix(model)
    first_revision = first_info["diagnostics"][
        "qualified_s3_reference_elastic_stiffness"
    ]["revision_key"]
    for node_id, node in tuple(model.mesh.nodes.items()):
        model.set_node_coordinates(node_id, node.x + 16.0, node.y, node.z)
    _second, second_info = assemble_stiffness_matrix(model)
    second_diagnostics = second_info["diagnostics"][
        "qualified_s3_reference_elastic_stiffness"
    ]
    assert second_diagnostics["element_count"] == 8
    assert second_diagnostics["component_evaluation_count"] == 1
    assert second_diagnostics["revision_key"] != first_revision


def test_warm_plan_reuses_exact_binary64_element_caches_without_rounding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _build_model(8)
    # Decimal grid translations produce distinct binary64 centered-coordinate
    # keys even though the triangles are nominally translated copies.  The
    # cache plan must reuse each element's own exact matrix, never round the
    # geometry or substitute a neighbouring element's matrix.
    for node_id, node in tuple(model.mesh.nodes.items()):
        model.set_node_coordinates(
            node_id,
            0.05 * float(node.x),
            0.05 * float(node.y),
            float(node.z),
        )

    calls = 0
    original = QualifiedE4PLS3ShellElement.compute_stiffness_components

    def counted(self, mesh, material):
        nonlocal calls
        calls += 1
        return original(self, mesh, material)

    monkeypatch.setattr(
        QualifiedE4PLS3ShellElement,
        "compute_stiffness_components",
        counted,
    )
    first, first_info = assemble_stiffness_matrix(model)
    assert calls == 8
    first_diagnostics = first_info["diagnostics"][
        "qualified_s3_reference_elastic_stiffness"
    ]
    assert first_diagnostics["element_count"] == 0
    assert first_diagnostics["fallback_reasons"] == {
        "group_below_minimum_size": list(range(1, 9))
    }

    second, second_info = assemble_stiffness_matrix(model)
    assert calls == 8
    second_diagnostics = second_info["diagnostics"][
        "qualified_s3_reference_elastic_stiffness"
    ]
    assert second_diagnostics["path"].endswith("exact_cache_reuse")
    assert second_diagnostics["element_count"] == 8
    assert second_diagnostics["translation_group_element_count"] == 0
    assert second_diagnostics["exact_element_cache_reuse_count"] == 8
    assert second_diagnostics["component_evaluation_count"] == 0
    assert second_diagnostics["fallback_reasons"] == {}
    assert second_diagnostics["plan_reused"] is False

    third, third_info = assemble_stiffness_matrix(model)
    assert calls == 8
    assert third_info["diagnostics"][
        "qualified_s3_reference_elastic_stiffness"
    ]["plan_reused"] is True
    np.testing.assert_array_equal(first.toarray(), second.toarray())
    np.testing.assert_array_equal(second.toarray(), third.toarray())

    # Direct element-property edits do not advance the mesh revision.  The
    # plan must therefore revalidate the formulation's complete cache key and
    # must never serve the stale pre-edit matrix.
    element = model.mesh.elements[1]
    element.thickness *= 2.0
    changed_thickness, thickness_info = assemble_stiffness_matrix(model)
    assert calls == 9
    assert thickness_info["diagnostics"][
        "qualified_s3_reference_elastic_stiffness"
    ]["plan_reused"] is False
    assert not np.array_equal(third.toarray(), changed_thickness.toarray())

    # The next pass may capture the newly populated exact element cache; only
    # the following pass is a reusable, fully rebound plan.
    rebound, rebound_info = assemble_stiffness_matrix(model)
    assert calls == 9
    assert rebound_info["diagnostics"][
        "qualified_s3_reference_elastic_stiffness"
    ]["plan_reused"] is False
    reused, reused_info = assemble_stiffness_matrix(model)
    assert calls == 9
    assert reused_info["diagnostics"][
        "qualified_s3_reference_elastic_stiffness"
    ]["plan_reused"] is True
    np.testing.assert_array_equal(changed_thickness.toarray(), rebound.toarray())
    np.testing.assert_array_equal(rebound.toarray(), reused.toarray())

    # Eligibility is also live state rather than a mesh revision.  Switching
    # to an oriented material path must evict the element from this narrow
    # isotropic reference plan before evaluation.
    element.material_direction = np.asarray((1.0, 0.0, 0.0))
    _oriented, oriented_info = assemble_stiffness_matrix(model)
    oriented_diagnostics = oriented_info["diagnostics"][
        "qualified_s3_reference_elastic_stiffness"
    ]
    assert oriented_diagnostics["plan_reused"] is False
    assert oriented_diagnostics["fallback_reasons"]["oriented_material"] == [1]

    # Revision invalidation clears the exact element caches and the mesh-owned
    # plan; the next assembly must evaluate every element again.
    node = model.mesh.nodes[1]
    model.set_node_coordinates(1, node.x - 1.0e-4, node.y, node.z)
    _changed, changed_info = assemble_stiffness_matrix(model)
    assert calls == 18
    assert changed_info["diagnostics"][
        "qualified_s3_reference_elastic_stiffness"
    ]["element_count"] == 0


def test_warm_plan_detects_direct_node_edits_without_a_mesh_revision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _build_model(8)
    calls = 0
    original = QualifiedE4PLS3ShellElement.compute_stiffness_components

    def counted(self, mesh, material):
        nonlocal calls
        calls += 1
        return original(self, mesh, material)

    monkeypatch.setattr(
        QualifiedE4PLS3ShellElement,
        "compute_stiffness_components",
        counted,
    )
    baseline, _baseline_info = assemble_stiffness_matrix(model)
    assert calls == 1
    _warm, warm_info = assemble_stiffness_matrix(model)
    assert warm_info["diagnostics"][
        "qualified_s3_reference_elastic_stiffness"
    ]["plan_reused"] is True

    geometry_revision = model.mesh.revisions["geometry"]
    coordinate_revision = model.mesh.nodes[1]._coordinate_revision
    model.mesh.nodes[1].x -= 1.0e-4
    changed, changed_info = assemble_stiffness_matrix(model)
    assert model.mesh.revisions["geometry"] == geometry_revision
    assert model.mesh.nodes[1]._coordinate_revision == coordinate_revision + 1
    assert calls == 2
    assert changed_info["diagnostics"][
        "qualified_s3_reference_elastic_stiffness"
    ]["plan_reused"] is False
    assert not np.array_equal(baseline.toarray(), changed.toarray())

    element = model.mesh.elements[1]
    with pytest.raises(ValueError, match="read-only"):
        element.reference_normal[0] = 0.25


def test_warm_plan_binds_reference_normal_bytes_even_if_writes_are_reenabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _build_model(8)
    baseline, _baseline_info = assemble_stiffness_matrix(model)
    repeated, repeated_info = assemble_stiffness_matrix(model)
    np.testing.assert_array_equal(baseline.toarray(), repeated.toarray())
    assert repeated_info["diagnostics"][
        "qualified_s3_reference_elastic_stiffness"
    ]["plan_reused"] is True

    element = model.mesh.elements[1]
    element.reference_normal.setflags(write=True)
    element.reference_normal[:] = (0.0, 0.0, -1.0)
    assert reference_s3_eligibility(model, element) == (
        False,
        "nonpositive_winding",
    )
    with pytest.raises(ValueError, match="winding opposes"):
        assemble_stiffness_matrix(model)


def test_generalized_orthotropic_history_and_winding_never_enter_batch() -> None:
    cases = (
        (_build_model(1, shell_section=_section()), "generalized_section"),
        (_build_model(1, material_name="orthotropic"), "orthotropic_or_anisotropic_material"),
        (_build_model(1, material_name="hill"), "hill_material"),
        (_build_model(1, material_name="history"), "material_history"),
        (_build_model(1, reverse_winding=True), "nonpositive_winding"),
    )
    for model, expected_reason in cases:
        element = model.mesh.elements[1]
        eligible, reason = reference_s3_eligibility(model, element)
        assert eligible is False
        assert reason == expected_reason
        prepared = prepare_reference_s3_components(
            model,
            [(1, element)],
            minimum_group_size=1,
        )
        assert prepared.matrices == {}
        assert prepared.component_evaluation_count == 0
        assert prepared.fallback_reasons == {expected_reason: (1,)}


def test_reference_surface_offset_never_enters_reference_batch() -> None:
    model = _build_model(1, reference_surface_offset=0.125)
    element = model.mesh.elements[1]

    eligible, reason = reference_s3_eligibility(model, element)
    assert eligible is False
    assert reason == "nonzero_reference_surface_offset"

    prepared = prepare_reference_s3_components(
        model,
        [(1, element)],
        minimum_group_size=1,
    )
    assert prepared.matrices == {}
    assert prepared.component_evaluation_count == 0
    assert prepared.fallback_reasons == {"nonzero_reference_surface_offset": (1,)}


def test_large_mixed_recovery_is_byte_identical_to_scalar_and_reuses_plan() -> None:
    model = _build_model(MIN_REFERENCE_S3_RECOVERY_GROUP, include_q4=True)
    vector = 2.0e-5 * np.sin(
        np.arange(model.mesh.dof_manager.total_dofs, dtype=float) + 0.375
    )
    scalar = {}
    for element_id in model.mesh.elements:
        item = _compute_one_element_stress(
            model,
            vector,
            element_id,
            return_global=True,
        )
        assert item is not None
        scalar[item[0]] = item[1]

    # Force a clean revision-bound batch construction after the independent
    # per-element scalar oracle populated its own caches.
    model.bump_revision("material")
    batched, first_report = recover_element_stresses_with_report(
        model,
        vector,
        RecoveryConfig(),
        return_global=True,
        resource_config=ResourceConfig(recovery_threads=4),
    )
    repeated, second_report = recover_element_stresses_with_report(
        model,
        vector,
        RecoveryConfig(),
        return_global=True,
        resource_config=ResourceConfig(recovery_threads=1),
    )
    _payload_bytes_equal(batched, scalar)
    _payload_bytes_equal(repeated, batched)
    assert list(batched) == list(model.mesh.elements)
    assert first_report.metadata["recovery_backend"] == (
        "hybrid_qualified_s3_reference_thread_pool"
    )
    assert first_report.metadata["qualified_s3_reference_batch_count"] == 1
    assert first_report.metadata["compiled_batch_count"] == 0
    assert first_report.metadata["eligible_element_count"] == (
        MIN_REFERENCE_S3_RECOVERY_GROUP
    )
    assert first_report.metadata["fallback_element_count"] == 1
    assert first_report.metadata["fallback_reasons"] == {
        "batch_below_minimum_size": {
            "element_ids": [MIN_REFERENCE_S3_RECOVERY_GROUP + 1],
            "minimum_size": 100,
        }
    }
    batch_diagnostics = first_report.metadata[
        "qualified_s3_reference_batch"
    ]
    assert batch_diagnostics["policy_id"] == REFERENCE_S3_BATCH_POLICY_ID
    assert batch_diagnostics["formulation_id"] == REFERENCE_S3_FORMULATION_ID
    assert batch_diagnostics["component_evaluation_count"] == 1
    assert batch_diagnostics["exact_translation_group_count"] == 1
    assert batch_diagnostics["speedup_claimed"] is False
    assert batch_diagnostics["legacy_stiffness_batch_eligible"] is False
    assert batch_diagnostics["legacy_nonlinear_batch_eligible"] is False
    assert first_report.metadata["plan_reused"] is False
    assert second_report.metadata["plan_reused"] is True


def test_committed_state_recovery_stays_outside_reference_batch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _build_model(1)
    element = model.mesh.elements[1]
    material = model.get_material("steel")
    state = element.init_model_bound_nonlinear_state(model.mesh, material, 3)
    vector = np.zeros(model.mesh.dof_manager.total_dofs, dtype=float)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("committed recovery entered the reference-elastic batch")

    monkeypatch.setattr("anysolver.recovery.recover_reference_s3", forbidden)
    result = recover_stress_result(
        model,
        vector,
        RecoveryConfig(),
        element_states={1: state},
        return_global=True,
    )
    assert result.provenance.mode == "material_history"
    assert result.provenance.per_element_source == {
        1: "committed_qualified_s3_native_state"
    }
    assert result.execution_report.metadata.get(
        "qualified_s3_reference_batch_count", 0
    ) == 0
