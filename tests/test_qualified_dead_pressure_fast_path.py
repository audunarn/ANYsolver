from __future__ import annotations

import copy
import itertools
import pickle
from dataclasses import asdict, fields
from typing import Callable

import numpy as np
import pytest

from anysolver import (
    FEModel,
    QualifiedE4PLS3ShellElement,
    QualifiedE4PLShellElement,
)
from anysolver.boundary import LoadCase


def _scalar_pressure_vector(model: FEModel, load: LoadCase) -> np.ndarray:
    """Reproduce the pre-fast-path formulation-native pressure loop."""

    result = np.zeros(model.mesh.dof_manager.total_dofs, dtype=float)
    for element_id, pressure in load.pressure_loads.items():
        element = model.mesh.get_element(element_id)
        assert element is not None
        local = LoadCase._consistent_pressure_load(
            load,
            element,
            model.mesh,
            pressure,
            None,
        )
        for index, dof in enumerate(element.get_dof_mapping(model.mesh)):
            if index < len(local):
                result[dof] += local[index]
    return result


def _fast_pressure_vector(
    model: FEModel,
    load: LoadCase,
    monkeypatch: pytest.MonkeyPatch,
) -> np.ndarray:
    """Require the eligible path to avoid the scalar pressure provider."""

    def forbidden(*_args: object, **_kwargs: object) -> np.ndarray:
        raise AssertionError("eligible dead pressure used the scalar provider")

    monkeypatch.setattr(load, "_consistent_pressure_load", forbidden)
    return load.get_load_vector(
        model.mesh,
        model.mesh.dof_manager,
        model.get_material,
    )


def _q4_model() -> FEModel:
    model = FEModel("qualified-q4-dead-pressure")
    model.add_material("steel", 210.0e9, 0.3, density=7850.0)
    # An irregular planar Q4 exercises the full bilinear pressure rule rather
    # than reducing the comparison to equal nodal shares.
    coordinates = (
        (0.0, 0.0, 0.0),
        (1.4, 0.1, 0.27),
        (1.1, 1.2, 0.10),
        (-0.1, 0.9, -0.11),
    )
    for node_id, point in enumerate(coordinates, start=1):
        model.add_node(node_id, *point)
    model.add_element(
        1,
        QualifiedE4PLShellElement(
            1,
            [1, 2, 3, 4],
            "steel",
            thickness=0.02,
        ),
    )
    return model


def _s3_model(
    node_order: tuple[int, int, int] = (1, 2, 3),
    owner: tuple[float, float, float] = (0.0, 0.0, 1.0),
) -> FEModel:
    model = FEModel("qualified-s3-dead-pressure")
    model.add_material("steel", 210.0e9, 0.3, density=7850.0)
    coordinates = (
        (0.1, -0.2, 0.04),
        (1.3, 0.0, 0.26),
        (0.25, 1.1, -0.06),
    )
    for node_id, point in enumerate(coordinates, start=1):
        model.add_node(node_id, *point)
    model.add_element(
        1,
        QualifiedE4PLS3ShellElement(
            1,
            list(node_order),
            "steel",
            thickness=0.02,
            reference_normal=owner,
        ),
    )
    return model


def _numpy_coordinate_s3_model(
    scalar_type: type[np.generic],
) -> FEModel:
    model = FEModel("qualified-s3-numpy-coordinate-dead-pressure")
    model.add_material("steel", 210.0e9, 0.3, density=7850.0)
    coordinates = (
        (scalar_type(0), scalar_type(0), scalar_type(0)),
        (scalar_type(2), scalar_type(0), scalar_type(0)),
        (scalar_type(0), scalar_type(1), scalar_type(0)),
    )
    for node_id, point in enumerate(coordinates, start=1):
        model.add_node(node_id, *point)
    model.add_element(
        1,
        QualifiedE4PLS3ShellElement(
            1,
            [1, 2, 3],
            "steel",
            thickness=0.02,
            reference_normal=(0.0, 0.0, 1.0),
        ),
    )
    return model


def _mixed_model() -> FEModel:
    model = FEModel("qualified-mixed-dead-pressure")
    model.add_material("steel", 210.0e9, 0.3, density=7850.0)
    coordinates = {
        1: (0.0, 0.0, 0.0),
        2: (1.0, 0.0, 0.0),
        3: (1.0, 1.0, 0.0),
        4: (0.0, 1.0, 0.0),
        5: (2.0, 0.0, 0.0),
    }
    for node_id, point in coordinates.items():
        model.add_node(node_id, *point)
    model.add_element(
        1,
        QualifiedE4PLShellElement(
            1,
            [1, 2, 3, 4],
            "steel",
            thickness=0.02,
        ),
    )
    model.add_element(
        2,
        QualifiedE4PLS3ShellElement(
            2,
            [2, 5, 3],
            "steel",
            thickness=0.02,
            reference_normal=(0.0, 0.0, 1.0),
        ),
    )
    return model


def test_q4_fast_dead_pressure_matches_scalar_bilinear_rule(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _q4_model()
    load = LoadCase("q4-pressure")
    load.add_pressure_load(1, 731.25)
    expected = _scalar_pressure_vector(model, load)

    actual = _fast_pressure_vector(model, load, monkeypatch)

    np.testing.assert_array_equal(actual, expected)


@pytest.mark.parametrize("node_order", tuple(itertools.permutations((1, 2, 3))))
def test_s3_fast_dead_pressure_matches_scalar_for_every_d3_numbering(
    node_order: tuple[int, int, int],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _s3_model(node_order)
    load = LoadCase("s3-pressure")
    load.add_pressure_load(1, -917.5)
    expected = _scalar_pressure_vector(model, load)

    actual = _fast_pressure_vector(model, load, monkeypatch)

    np.testing.assert_array_equal(actual, expected)


@pytest.mark.parametrize("scalar_type", (np.int32, np.int64, np.float32, np.float64))
def test_s3_fast_dead_pressure_matches_scalar_for_numpy_coordinates(
    scalar_type: type[np.generic],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _numpy_coordinate_s3_model(scalar_type)
    load = LoadCase("s3-numpy-coordinate-pressure")
    load.add_pressure_load(1, 347.0)
    expected = _scalar_pressure_vector(model, load)

    actual = _fast_pressure_vector(model, load, monkeypatch)

    np.testing.assert_array_equal(actual, expected)


@pytest.mark.parametrize("node_order", ((1, 2, 3), (1, 3, 2)))
def test_s3_fast_dead_pressure_honours_reversed_owner_normal(
    node_order: tuple[int, int, int],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _s3_model(node_order, owner=(0.0, 0.0, -1.0))
    load = LoadCase("s3-reversed-owner-pressure")
    load.add_pressure_load(1, 503.0)
    expected = _scalar_pressure_vector(model, load)

    actual = _fast_pressure_vector(model, load, monkeypatch)

    np.testing.assert_array_equal(actual, expected)
    resultant = actual.reshape(-1, 6)[:, :3].sum(axis=0)
    assert resultant[2] < 0.0


def test_mixed_fast_dead_pressure_matches_scalar_with_shared_nodes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _mixed_model()
    load = LoadCase("mixed-pressure")
    # Preserve a non-topology ordering to exercise the captured mapping order.
    load.add_pressure_load(2, -419.0)
    load.add_pressure_load(1, 877.0)
    expected = _scalar_pressure_vector(model, load)

    actual = _fast_pressure_vector(model, load, monkeypatch)

    np.testing.assert_array_equal(actual, expected)


class _DerivedLoadCase(LoadCase):
    pass


class _HalfActivity:
    def load_scales(self, element_ids: list[int]) -> np.ndarray:
        return np.full(len(element_ids), 0.5, dtype=float)


@pytest.mark.parametrize(
    "configure, expected_scale",
    (
        (lambda load, _model: setattr(load, "follower_pressure", True), 1.0),
        (
            lambda load, _model: load.add_nodal_load(
                1, forces=np.asarray((2.0, -3.0, 5.0))
            ),
            1.0,
        ),
    ),
    ids=("follower-pressure", "combined-nodal-and-pressure"),
)
def test_ineligible_exact_load_cases_use_scalar_pressure_provider(
    configure: Callable[[LoadCase, FEModel], None],
    expected_scale: float,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _q4_model()
    load = LoadCase("fallback-pressure")
    load.add_pressure_load(1, 619.0)
    configure(load, model)
    scalar_pressure = _scalar_pressure_vector(model, load)
    calls: list[int] = []
    original = load._consistent_pressure_load

    def observed(*args: object, **kwargs: object) -> np.ndarray:
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(load, "_consistent_pressure_load", observed)
    displacement = (
        np.zeros(model.mesh.dof_manager.total_dofs, dtype=float)
        if load.follower_pressure
        else None
    )
    actual = load.get_load_vector(
        model.mesh,
        model.mesh.dof_manager,
        model.get_material,
        displacements=displacement,
    )

    assert calls == [1]
    expected = expected_scale * scalar_pressure
    if load.nodal_loads:
        node = model.mesh.get_node(1)
        assert node is not None
        expected[np.asarray(node.dofs[:3], dtype=np.intp)] += (2.0, -3.0, 5.0)
    np.testing.assert_array_equal(actual, expected)


def test_load_subclass_and_activity_scaling_remain_on_scalar_route(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model = _q4_model()
    load = _DerivedLoadCase("subclass-pressure")
    load.add_pressure_load(1, 283.0)
    expected = 0.5 * _scalar_pressure_vector(model, load)
    calls: list[int] = []
    original = load._consistent_pressure_load

    def observed(*args: object, **kwargs: object) -> np.ndarray:
        calls.append(1)
        return original(*args, **kwargs)

    monkeypatch.setattr(load, "_consistent_pressure_load", observed)
    actual = load.get_load_vector(
        model.mesh,
        model.mesh.dof_manager,
        model.get_material,
        element_activity=_HalfActivity(),
    )

    assert calls == [1]
    np.testing.assert_array_equal(actual, expected)


@pytest.mark.parametrize(
    "field",
    (
        "follower_pressure",
        "gravity",
        "nodal_loads",
        "element_loads",
        "added_node_masses",
        "pressure_loads",
    ),
)
@pytest.mark.parametrize("restore", (False, True), ids=("persistent", "aba"))
def test_fast_dead_pressure_rejects_every_eligibility_field_change(
    field: str,
    restore: bool,
) -> None:
    model = _q4_model()
    load = LoadCase("mutated-fast-pressure")
    load.add_pressure_load(1, 619.0)
    reached: list[str] = []

    def mutate() -> None:
        if field == "follower_pressure":
            load.follower_pressure = True
            if restore:
                load.follower_pressure = False
        elif field == "gravity":
            load.gravity = np.asarray((0.0, 0.0, -9.81), dtype=float)
            if restore:
                load.gravity = None
        elif field == "nodal_loads":
            load.nodal_loads[1] = np.ones(6, dtype=float)
            if restore:
                del load.nodal_loads[1]
        elif field == "element_loads":
            load.element_loads[1] = np.ones(24, dtype=float)
            if restore:
                del load.element_loads[1]
        elif field == "added_node_masses":
            load.added_node_masses[1] = 2.5
            if restore:
                del load.added_node_masses[1]
        else:
            load.pressure_loads[1] = 620.0
            if restore:
                load.pressure_loads[1] = 619.0

    def guard(*, stage: str) -> None:
        if stage == "exact dead-pressure output":
            reached.append(stage)
            mutate()

    with pytest.raises(
        ValueError,
        match="exact qualified dead-pressure inputs changed",
    ):
        load._get_load_vector_under_lease(
            model.mesh,
            model.mesh.dof_manager,
            model.get_material,
            None,
            None,
            qualified_runtime_guard=guard,
        )
    assert reached == ["exact dead-pressure output"]


def test_load_state_epoch_preserves_public_dataclass_and_dict_compatibility() -> None:
    pressure = {3: 19.5}
    masses = {7: 2.25}
    load = LoadCase(
        "compatibility",
        nodal_loads={},
        element_loads={},
        pressure_loads=pressure,
        added_node_masses=masses,
    )

    assert tuple(field.name for field in fields(LoadCase)) == (
        "name",
        "nodal_loads",
        "element_loads",
        "pressure_loads",
        "gravity",
        "added_node_masses",
        "follower_pressure",
    )
    assert all(
        isinstance(mapping, dict)
        for mapping in (
            load.nodal_loads,
            load.element_loads,
            load.pressure_loads,
            load.added_node_masses,
        )
    )
    assert dict(load.pressure_loads) == pressure
    assert dict(load.added_node_masses) == masses
    serialized = asdict(load)
    assert dict(serialized["pressure_loads"]) == pressure
    assert dict(serialized["added_node_masses"]) == masses

    copied = copy.deepcopy(load)
    restored = pickle.loads(pickle.dumps(load))
    assert copied == load
    assert restored == load
    for candidate in (copied, restored):
        token = candidate._qualified_load_state_token
        assert all(
            mapping._qualified_token is token
            for mapping in (
                candidate.nodal_loads,
                candidate.element_loads,
                candidate.pressure_loads,
                candidate.added_node_masses,
            )
        )


def test_tracked_load_mappings_preserve_ordinary_combination_semantics() -> None:
    load = LoadCase("ordinary-combination")
    load.add_nodal_load(4, forces=np.asarray((1.0, 2.0, 3.0)))
    load.add_nodal_load(4, moments=np.asarray((4.0, 5.0, 6.0)))
    load.add_pressure_load(9, -12.5)
    load.add_node_mass(4, 2.0)
    load.add_node_mass(4, 0.5)
    load.set_acceleration(0.1, -0.2, 0.3)

    np.testing.assert_array_equal(
        load.nodal_loads[4],
        np.asarray((1.0, 2.0, 3.0, 4.0, 5.0, 6.0)),
    )
    assert dict(load.pressure_loads) == {9: -12.5}
    assert dict(load.added_node_masses) == {4: 2.5}
    np.testing.assert_array_equal(load.gravity, (0.1, -0.2, 0.3))
