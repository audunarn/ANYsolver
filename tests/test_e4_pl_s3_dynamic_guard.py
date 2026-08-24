from __future__ import annotations

import numpy as np
import pytest

from anysolver import (
    ElementCapabilityError,
    FEModel,
    QualifiedE4PLS3ShellElement,
    RigidSphereImpact,
    TransientConfig,
    solve_transient_sphere_impact,
)


def _model() -> FEModel:
    model = FEModel("guarded-qualified-s3")
    for node_id, coordinate in enumerate(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.2, 0.9, 0.0)), start=1
    ):
        model.add_node(node_id, *coordinate)
    model.add_element(
        7,
        QualifiedE4PLS3ShellElement(
            7,
            [1, 2, 3],
            "steel",
            reference_normal=np.asarray((0.0, 0.0, 1.0)),
        ),
    )
    return model


def test_linear_transient_is_no_longer_a_qualified_s3_capability_gap() -> None:
    element = _model().mesh.elements[7]
    assert "transient_algebraic_dynamics" not in element.capability_gaps
    assert element.capability_matrix()["transient_algebraic_dynamics"] == (
        "PARITY_REPLACED"
    )


def test_contact_rejects_before_contact_resolution_or_state_creation() -> None:
    model = _model()
    sphere = RigidSphereImpact(
        "guard",
        radius=0.1,
        mass=1.0,
        start_point=(0.3, 0.3, 0.2),
        travel_direction=(0.0, 0.0, -1.0),
        speed=1.0,
    )

    with pytest.raises(ElementCapabilityError, match="sphere-impact.*7"):
        solve_transient_sphere_impact(
            model,
            TransientConfig(dt=0.01, t_end=0.01),
            sphere,
        )


def test_guard_diagnostics_are_sorted_and_bounded() -> None:
    model = FEModel("guard-order")
    for node_id, coordinate in enumerate(
        (
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (2.0, 0.0, 0.0),
            (3.0, 0.0, 0.0),
            (2.0, 1.0, 0.0),
        ),
        start=1,
    ):
        model.add_node(node_id, *coordinate)
    for element_id, node_ids in ((11, [1, 2, 3]), (3, [4, 5, 6])):
        model.add_element(
            element_id,
            QualifiedE4PLS3ShellElement(
                element_id,
                node_ids,
                "steel",
                reference_normal=np.asarray((0.0, 0.0, 1.0)),
            ),
        )

    sphere = RigidSphereImpact(
        "guard-order",
        radius=0.1,
        mass=1.0,
        start_point=(0.3, 0.3, 0.2),
        travel_direction=(0.0, 0.0, -1.0),
        speed=1.0,
    )
    with pytest.raises(ElementCapabilityError) as caught:
        solve_transient_sphere_impact(
            model,
            TransientConfig(dt=0.01, t_end=0.01),
            sphere,
        )

    message = str(caught.value)
    assert message.index("3 (") < message.index("11 (")
