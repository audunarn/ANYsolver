from __future__ import annotations

import copy
import warnings
from types import SimpleNamespace

import numpy as np
import pytest

import anysolver.arc_length as arc_length_module
import anysolver.imperfections as imperfections_module
import anysolver.nonlinear_static as nonlinear_static_module
import anysolver.recovery as recovery_module
import anysolver.results as results_module
from anysolver import (
    ElementCapabilityError,
    FEModel,
    ImperfectionField,
    LegacyS3MigrationWarning,
    LegacyShellElement,
    PatchRecoveryConfig,
    QualifiedE4PLS3ShellElement,
    QualifiedE4PLShellElement,
    RecoveryConfig,
    create_shell_element,
    shell_element_from_dict,
)
from anysolver.assembly import compute_stresses as assembly_compute_stresses
from anysolver.element_capabilities import require_model_element_capabilities


OWNER_NORMAL = np.asarray((0.0, 0.0, 1.0))
S3_ID = 7
Q4_ID = 20


def _mixed_model() -> FEModel:
    model = FEModel("qualified-s3-guard-boundary")
    model.add_material("steel", 210.0e9, 0.3, density=7850.0)
    coordinates = (
        (0.0, 0.0, 0.0),
        (1.0, 0.0, 0.0),
        (0.2, 0.9, 0.0),
        (2.0, 0.0, 0.0),
        (3.0, 0.0, 0.0),
        (3.0, 1.0, 0.0),
        (2.0, 1.0, 0.0),
    )
    for node_id, coordinate in enumerate(coordinates, start=1):
        model.add_node(node_id, *coordinate)
    model.add_element(
        S3_ID,
        QualifiedE4PLS3ShellElement(
            S3_ID,
            [1, 2, 3],
            "steel",
            thickness=0.1,
            reference_normal=OWNER_NORMAL,
        ),
    )
    q4 = create_shell_element(
        Q4_ID,
        [4, 5, 6, 7],
        "steel",
        thickness=0.1,
    )
    assert type(q4) is QualifiedE4PLShellElement
    model.add_element(Q4_ID, q4)
    return model


def _zero_displacements(model: FEModel) -> np.ndarray:
    return np.zeros(model.mesh.dof_manager.total_dofs, dtype=float)


def test_capability_guard_scopes_exact_element_ids_and_orders_failures() -> None:
    model = SimpleNamespace(
        mesh=SimpleNamespace(
            elements={
                11: SimpleNamespace(capability_gaps=("zeta", "alpha")),
                3: SimpleNamespace(capability_gaps=("beta", "alpha")),
            }
        )
    )

    require_model_element_capabilities(
        model,
        ("alpha", "beta", "zeta"),
        context="empty-selection",
        element_ids=(),
    )
    require_model_element_capabilities(
        model,
        "alpha",
        context="unknown-selection",
        element_ids=(99,),
    )

    selected = (value for value in (11, 3, 11, 99))
    with pytest.raises(ElementCapabilityError) as caught:
        require_model_element_capabilities(
            model,
            ("zeta", "beta", "alpha"),
            context="ordered-selection",
            element_ids=selected,
        )
    message = str(caught.value)
    assert message.startswith("ordered-selection is unavailable")
    assert "3 (alpha, beta)" in message
    assert "11 (alpha, zeta)" in message
    assert message.index("3 (alpha, beta)") < message.index("11 (alpha, zeta)")

    with pytest.raises(ElementCapabilityError) as caught_single:
        require_model_element_capabilities(
            model,
            "zeta",
            context="single-selection",
            element_ids=(11,),
        )
    assert "11 (zeta)" in str(caught_single.value)
    assert "3 (" not in str(caught_single.value)


def test_static_nonlinear_rejects_before_any_model_evaluation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _mixed_model()
    calls: list[str] = []

    def forbidden(name: str):
        def fail(*_args, **_kwargs):
            calls.append(name)
            raise AssertionError(f"nonlinear guard evaluated {name}")

        return fail

    monkeypatch.setattr(model, "apply_boundary_conditions", forbidden("boundary"))
    monkeypatch.setattr(
        nonlinear_static_module,
        "_has_follower_pressure",
        forbidden("follower"),
    )
    monkeypatch.setattr(
        nonlinear_static_module,
        "_ensure_nonlinear_acceleration",
        forbidden("acceleration"),
    )
    monkeypatch.setattr(
        nonlinear_static_module,
        "assemble_stiffness_matrix",
        forbidden("stiffness"),
    )
    monkeypatch.setattr(
        nonlinear_static_module,
        "_prepare_initial_states",
        forbidden("initial-state"),
    )

    with pytest.raises(
        ElementCapabilityError,
        match="solve_static_nonlinear.*material_nonlinearity.*nonlinear_geometry",
    ):
        nonlinear_static_module.solve_static_nonlinear(model, num_steps=1)
    assert calls == []


def test_static_nonlinear_state_and_field_guards_are_id_scoped() -> None:
    model = _mixed_model()

    with pytest.raises(ElementCapabilityError, match="initial_fields"):
        nonlinear_static_module.solve_static_nonlinear(
            model,
            num_steps=1,
            initial_fields={S3_ID: object()},
        )
    with pytest.raises(ElementCapabilityError, match="restart_history"):
        nonlinear_static_module.solve_static_nonlinear(
            model,
            num_steps=1,
            initial_element_states={S3_ID: {}},
        )

    with pytest.raises(ElementCapabilityError) as field_for_q4:
        nonlinear_static_module.solve_static_nonlinear(
            model,
            num_steps=1,
            initial_fields={Q4_ID: object()},
        )
    assert "material_nonlinearity" in str(field_for_q4.value)
    assert "initial_fields" not in str(field_for_q4.value)

    with pytest.raises(ElementCapabilityError) as state_for_q4:
        nonlinear_static_module.solve_static_nonlinear(
            model,
            num_steps=1,
            initial_element_states={Q4_ID: {}},
        )
    assert "material_nonlinearity" in str(state_for_q4.value)
    assert "restart_history" not in str(state_for_q4.value)


def test_arc_length_rejects_before_load_copy_boundary_or_stiffness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _mixed_model()
    calls: list[str] = []

    def forbidden(name: str):
        def fail(*_args, **_kwargs):
            calls.append(name)
            raise AssertionError(f"arc-length guard evaluated {name}")

        return fail

    monkeypatch.setattr(
        arc_length_module,
        "_has_follower_pressure",
        forbidden("follower"),
    )
    monkeypatch.setattr(
        arc_length_module,
        "_copy_model_with_imperfection",
        forbidden("copy"),
    )
    monkeypatch.setattr(model, "apply_boundary_conditions", forbidden("boundary"))
    monkeypatch.setattr(
        arc_length_module,
        "assemble_stiffness_matrix",
        forbidden("stiffness"),
    )

    with pytest.raises(
        ElementCapabilityError,
        match="solve_static_arc_length.*material_nonlinearity.*nonlinear_geometry",
    ):
        arc_length_module.solve_static_arc_length(model, None)
    assert calls == []

    with pytest.raises(ElementCapabilityError, match="restart_history"):
        arc_length_module.solve_static_arc_length(
            model,
            None,
            initial_element_states={S3_ID: {}},
        )
    with pytest.raises(ElementCapabilityError, match="initial_fields"):
        arc_length_module.solve_static_arc_length(
            model,
            None,
            imperfection=ImperfectionField({3: (0.0, 0.0, 0.1)}),
        )
    assert calls == []


def test_apply_imperfection_rejects_before_copy_conversion_or_geometry_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _mixed_model()
    coordinates = {
        node_id: node.coords().copy() for node_id, node in model.mesh.nodes.items()
    }
    revisions = model.revision_signature()
    calls: list[str] = []

    def forbidden(name: str):
        def fail(*_args, **_kwargs):
            calls.append(name)
            raise AssertionError(f"imperfection guard evaluated {name}")

        return fail

    monkeypatch.setattr(
        imperfections_module.copy,
        "deepcopy",
        forbidden("deepcopy"),
    )
    monkeypatch.setattr(
        imperfections_module,
        "to_imperfection_field",
        forbidden("conversion"),
    )

    with pytest.raises(
        ElementCapabilityError,
        match="apply_imperfection.*initial_fields",
    ):
        imperfections_module.apply_imperfection(
            model,
            ImperfectionField({3: (0.0, 0.0, 0.1)}),
            copy_model=True,
        )
    assert calls == []
    assert model.revision_signature() == revisions
    for node_id, expected in coordinates.items():
        np.testing.assert_array_equal(model.mesh.nodes[node_id].coords(), expected)


def test_global_recovery_rejects_before_displacement_state_or_worker_evaluation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _mixed_model()
    selected = RecoveryConfig(element_ids=[S3_ID])
    calls: list[str] = []

    def forbidden(name: str):
        def fail(*_args, **_kwargs):
            calls.append(name)
            raise AssertionError(f"recovery guard evaluated {name}")

        return fail

    monkeypatch.setattr(
        recovery_module,
        "_recovery_worker_count",
        forbidden("worker-count"),
    )
    monkeypatch.setattr(
        recovery_module,
        "get_recovery_batch_plan",
        forbidden("batch-plan"),
    )
    monkeypatch.setattr(
        recovery_module,
        "_compute_one_element_stress",
        forbidden("element-stress"),
    )

    with pytest.raises(
        ElementCapabilityError,
        match="recover_element_stresses_with_report.*global_recovery",
    ):
        recovery_module.recover_element_stresses_with_report(
            model,
            object(),
            selected,
            return_global=True,
        )

    monkeypatch.setattr(
        recovery_module,
        "_recovery_displacements",
        forbidden("displacements"),
    )
    monkeypatch.setattr(
        recovery_module,
        "_recover_generalized_committed_state",
        forbidden("generalized-state"),
    )
    with pytest.raises(
        ElementCapabilityError,
        match="recover_stress_result.*global_recovery",
    ):
        recovery_module.recover_stress_result(
            model,
            object(),
            selected,
            return_global=True,
        )
    with pytest.raises(
        ElementCapabilityError,
        match="recover_stress_result.*patch_recovery",
    ):
        recovery_module.recover_stress_result(
            model,
            object(),
            selected,
            patch_config=PatchRecoveryConfig(),
        )
    assert calls == []


def test_recovery_state_history_guard_is_selection_scoped() -> None:
    model = _mixed_model()

    with pytest.raises(
        ElementCapabilityError,
        match="recover_stress_result.*restart_history",
    ):
        recovery_module.recover_stress_result(
            model,
            object(),
            RecoveryConfig(element_ids=[S3_ID]),
            element_states={S3_ID: {}},
        )

    recovered = recovery_module.recover_stress_result(
        model,
        _zero_displacements(model),
        RecoveryConfig(element_ids=[Q4_ID]),
        element_states={S3_ID: {}},
        return_global=True,
    )
    assert tuple(recovered.element_stresses) == (Q4_ID,)
    assert recovered.committed_element_states == {}


def test_disabled_global_recovery_preserves_noop_semantics(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _mixed_model()

    def forbidden(*_args, **_kwargs):
        raise AssertionError("disabled recovery evaluated mechanics")

    monkeypatch.setattr(recovery_module, "_compute_one_element_stress", forbidden)
    stresses, report = recovery_module.recover_element_stresses_with_report(
        model,
        object(),
        RecoveryConfig(element_ids=[S3_ID], include_stresses=False),
        return_global=True,
    )
    assert stresses == {}
    assert report.backend == "disabled"
    assert report.item_count == 0

    result = recovery_module.recover_stress_result(
        model,
        _zero_displacements(model),
        RecoveryConfig(element_ids=[S3_ID], include_stresses=False),
        return_global=True,
    )
    assert result.element_stresses == {}
    assert result.provenance.mode == "disabled"
    assert result.execution_report is not None
    assert result.execution_report.backend == "disabled"


def test_patch_and_nodal_recovery_reject_before_preparation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _mixed_model()
    calls: list[str] = []

    def forbidden(name: str):
        def fail(*_args, **_kwargs):
            calls.append(name)
            raise AssertionError(f"patch guard evaluated {name}")

        return fail

    monkeypatch.setattr(
        recovery_module,
        "_prepare_shell_patch_elements",
        forbidden("patch-preparation"),
    )
    with pytest.raises(
        ElementCapabilityError,
        match="recover_shell_patch_stresses.*patch_recovery",
    ):
        recovery_module.recover_shell_patch_stresses(
            model,
            {S3_ID: {}},
            element_ids=[S3_ID],
        )

    monkeypatch.setattr(
        results_module,
        "_gauss_to_node_extrapolation",
        forbidden("extrapolation"),
    )
    with pytest.raises(
        ElementCapabilityError,
        match="recover_nodal_stresses.*global_recovery.*patch_recovery",
    ):
        results_module.recover_nodal_stresses(
            model,
            object(),
            element_ids=[S3_ID],
        )
    assert calls == []


def test_assembly_global_guard_precedes_displacement_dof_and_material_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _mixed_model()
    calls: list[str] = []

    def forbidden(name: str):
        def fail(*_args, **_kwargs):
            calls.append(name)
            raise AssertionError(f"assembly recovery guard evaluated {name}")

        return fail

    monkeypatch.setattr(
        QualifiedE4PLS3ShellElement,
        "get_dof_mapping",
        forbidden("dof-mapping"),
    )
    monkeypatch.setattr(model, "get_material", forbidden("material"))
    with pytest.raises(
        ElementCapabilityError,
        match="compute_stresses.*global_recovery",
    ):
        assembly_compute_stresses(
            model,
            object(),
            return_global=True,
            element_ids=[S3_ID],
        )
    assert calls == []


def test_recovery_selection_does_not_block_unselected_s3_and_local_s3_works() -> None:
    model = _mixed_model()
    displacements = _zero_displacements(model)
    q4_only = RecoveryConfig(element_ids=[Q4_ID])

    element_stresses, _report = recovery_module.recover_element_stresses_with_report(
        model,
        displacements,
        q4_only,
        return_global=True,
    )
    assert tuple(element_stresses) == (Q4_ID,)

    stress_result = recovery_module.recover_stress_result(
        model,
        displacements,
        q4_only,
        return_global=True,
    )
    assert tuple(stress_result.element_stresses) == (Q4_ID,)

    assembly_stresses = assembly_compute_stresses(
        model,
        displacements,
        return_global=True,
        element_ids=[Q4_ID],
    )
    assert tuple(assembly_stresses) == (Q4_ID,)

    nodal = results_module.recover_nodal_stresses(
        model,
        displacements,
        element_ids=[Q4_ID],
    )
    assert tuple(nodal["element_nodal"]) == (Q4_ID,)

    local_s3, _local_report = recovery_module.recover_element_stresses_with_report(
        model,
        displacements,
        RecoveryConfig(element_ids=[S3_ID]),
        return_global=False,
    )
    assert tuple(local_s3) == (S3_ID,)
    assert local_s3[S3_ID]["recovery_scope"] == "qualified_s3_local_physical_only"


def test_historical_tri3_warns_once_stays_legacy_and_preserves_input() -> None:
    historical = {
        "type": "ShellElement",
        "element_id": 91,
        "node_ids": [1, 2, 3],
        "material_name": "steel",
        "thickness": 0.07,
        "drilling_stabilization": 1.0e-3,
        "hourglass_stabilization": 1.0e-8,
        "reduced_integration": False,
    }
    before = copy.deepcopy(historical)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        rebuilt = shell_element_from_dict(historical)

    migration = [
        item for item in caught if issubclass(item.category, LegacyS3MigrationWarning)
    ]
    assert len(migration) == 1
    message = str(migration[0].message)
    assert "LEGACY_S3_MISSING_FORMULATION_ID" in message
    assert "loaded as legacy-s3" in message
    assert "qualified-s3 was not inferred" in message
    assert "qualified-s3 hot restart" in message
    assert type(rebuilt) is LegacyShellElement
    assert historical == before


def test_explicit_legacy_and_qualified_records_do_not_emit_migration_warning() -> None:
    qualified = QualifiedE4PLS3ShellElement(
        92,
        [1, 2, 3],
        "steel",
        thickness=0.07,
        reference_normal=OWNER_NORMAL,
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        explicit_legacy = create_shell_element(
            93,
            [1, 2, 3],
            "steel",
            formulation="legacy-s3",
        )
        rebuilt = shell_element_from_dict(qualified.to_dict())
    assert type(explicit_legacy) is LegacyShellElement
    assert type(rebuilt) is QualifiedE4PLS3ShellElement
    assert not any(
        issubclass(item.category, LegacyS3MigrationWarning) for item in caught
    )

    historical_q4 = {
        "type": "ShellElement",
        "element_id": 94,
        "node_ids": [1, 2, 3, 4],
        "material_name": "steel",
        "thickness": 0.07,
    }
    missing_identity = qualified.to_dict()
    missing_identity.pop("formulation_id")
    with warnings.catch_warnings(record=True) as deserialization_warnings:
        warnings.simplefilter("always")
        historical_q4_element = shell_element_from_dict(historical_q4)
        with pytest.raises(ValueError, match="missing formulation_id"):
            shell_element_from_dict(missing_identity)
    assert type(historical_q4_element) is LegacyShellElement
    assert not any(
        issubclass(item.category, LegacyS3MigrationWarning)
        for item in deserialization_warnings
    )
