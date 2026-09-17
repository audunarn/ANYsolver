from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Callable

import pytest

import anysolver.current_state_tangent as tangent
from anysolver import QualifiedE4PLShellElement
from anysolver.element_capabilities import ElementCapabilityError


def _q4(element_id: int) -> QualifiedE4PLShellElement:
    return QualifiedE4PLShellElement(
        element_id,
        (1, 2, 3, 4),
        "steel",
        thickness=0.02,
        reference_normal=(0.0, 0.0, 1.0),
    )


def _model(*elements: QualifiedE4PLShellElement) -> SimpleNamespace:
    return SimpleNamespace(
        mesh=SimpleNamespace(
            elements={element.element_id: element for element in elements}
        )
    )


def _delete_material_name(element: QualifiedE4PLShellElement) -> None:
    object.__delattr__(element, "material_name")


def _replace_connectivity(element: QualifiedE4PLShellElement) -> None:
    object.__setattr__(element, "node_ids", [1, 2, 3, 4])


def _shadow_formulation(element: QualifiedE4PLShellElement) -> None:
    object.__setattr__(
        element,
        "formulation_id",
        tangent.QUALIFIED_Q4_FORMULATION_ID,
    )


def _add_callable_override(element: QualifiedE4PLShellElement) -> None:
    object.__setattr__(element, "attacker_callback", lambda: None)


def test_captured_class_names_are_exact_for_every_immutable_profile() -> None:
    for formulation_id, profile in tangent._QUALIFIED_PROFILES.items():
        expected = frozenset().union(
            *(
                frozenset(namespace)
                for namespace in profile["class_namespace_authority"].values()
            )
        )
        assert (
            tangent._QUALIFIED_PROFILE_CAPTURED_CLASS_NAMES[formulation_id]
            == expected
        )


@pytest.mark.parametrize(
    "mutate",
    (
        None,
        _delete_material_name,
        _replace_connectivity,
        _shadow_formulation,
        _add_callable_override,
    ),
    ids=(
        "clean",
        "missing-data",
        "bad-connectivity",
        "identity-shadow",
        "callable-shadow",
    ),
)
def test_prepared_class_names_preserve_standalone_instance_predicate(
    mutate: Callable[[QualifiedE4PLShellElement], None] | None,
) -> None:
    profile = tangent._QUALIFIED_PROFILES[
        tangent.QUALIFIED_Q4_FORMULATION_ID
    ]
    element = _q4(1)
    if mutate is not None:
        mutate(element)

    standalone = tangent._qualified_profile_api_failure(element, profile)
    prepared = tangent._qualified_profile_api_failure(
        element,
        profile,
        _captured_class_names=(
            tangent._QUALIFIED_PROFILE_CAPTURED_CLASS_NAMES[
                tangent.QUALIFIED_Q4_FORMULATION_ID
            ]
        ),
    )

    assert prepared == standalone


def test_prepared_class_names_preserve_standalone_class_mutation_predicate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = tangent._QUALIFIED_PROFILES[
        tangent.QUALIFIED_Q4_FORMULATION_ID
    ]
    element = _q4(1)
    monkeypatch.setattr(
        QualifiedE4PLShellElement,
        "compute_mass_matrix",
        lambda self, mesh, material: None,
    )

    standalone = tangent._qualified_profile_api_failure(element, profile)
    prepared = tangent._qualified_profile_api_failure(
        element,
        profile,
        _captured_class_names=(
            tangent._QUALIFIED_PROFILE_CAPTURED_CLASS_NAMES[
                tangent.QUALIFIED_Q4_FORMULATION_ID
            ]
        ),
    )

    assert prepared == standalone
    assert standalone is not None
    assert "CRITICAL_API_MISMATCH=compute_mass_matrix" in standalone


def test_guard_rechecks_class_authority_between_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _model(_q4(1), _q4(2))
    assert tangent.require_exact_qualified_component_lifecycle_api(
        model,
        context="first validation",
    ) == {"qualified_element_ids": [1, 2], "guarded": True}

    monkeypatch.setattr(
        QualifiedE4PLShellElement,
        "compute_mass_matrix",
        lambda self, mesh, material: None,
    )

    with pytest.raises(
        ElementCapabilityError,
        match="CLASS_NAMESPACE_MISMATCH.*compute_mass_matrix",
    ):
        tangent.require_exact_qualified_component_lifecycle_api(
            model,
            context="class mutation revalidation",
        )


def test_guard_validates_elements_added_after_an_earlier_success() -> None:
    model = _model(_q4(1))
    assert tangent.require_exact_qualified_component_lifecycle_api(
        model,
        context="initial element",
    )["qualified_element_ids"] == [1]

    model.mesh.elements[2] = _q4(2)
    assert tangent.require_exact_qualified_component_lifecycle_api(
        model,
        context="late valid element",
    )["qualified_element_ids"] == [1, 2]

    object.__setattr__(model.mesh.elements[2], "element_id", 99)
    with pytest.raises(
        ElementCapabilityError,
        match="2 .*ELEMENT_MAPPING_ID_MISMATCH",
    ):
        tangent.require_exact_qualified_component_lifecycle_api(
            model,
            context="late mutated element",
        )


def test_guard_rejects_late_exact_class_substitution() -> None:
    class Q4Subclass(QualifiedE4PLShellElement):
        pass

    model = _model(_q4(1))
    substituted = _q4(2)
    object.__setattr__(substituted, "__class__", Q4Subclass)
    model.mesh.elements[2] = substituted

    with pytest.raises(
        ElementCapabilityError,
        match="2 .*FORMULATION_ID_CLASS_MISMATCH",
    ):
        tangent.require_exact_qualified_component_lifecycle_api(
            model,
            context="late subclass",
        )


def test_custom_profile_failure_callback_keeps_per_element_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _model(_q4(1), _q4(2))
    calls: list[int] = []

    def mutating_failure(element: Any, profile: Any) -> str | None:
        calls.append(element.element_id)
        failure = tangent._qualified_profile_api_failure(element, profile)
        if element.element_id == 1:
            monkeypatch.setattr(
                QualifiedE4PLShellElement,
                "compute_mass_matrix",
                lambda self, mesh, material: None,
            )
        return failure

    with pytest.raises(
        ElementCapabilityError,
        match="2 .*CRITICAL_API_MISMATCH=compute_mass_matrix",
    ):
        tangent._require_exact_qualified_component_lifecycle_api_implementation(
            model,
            context="callback boundary",
            _profile_failure=mutating_failure,
        )

    assert calls == [1, 2]
