from __future__ import annotations

import itertools
from statistics import median
from time import perf_counter
from typing import Any

import numpy as np
import pytest

from anysolver import (
    FEModel,
    QualifiedE4PLS3ShellElement,
    QualifiedE4PLShellElement,
    assemble_stiffness_matrix,
)
from anysolver.elements import ShellElement
from anysolver.matrix_assembly import AssemblyError
import anysolver.recovery as recovery


def _mixed_model(*, include_legacy: bool = False) -> FEModel:
    model = FEModel("qualified-interface-recovery")
    model.add_material("steel", 210.0e9, 0.3, density=7850.0)
    coordinates = (
        (0.0, 0.0, 0.0),
        (1.1, 0.0, 0.0),
        (1.0, 0.9, 0.0),
        (-0.1, 1.0, 0.0),
        (2.1, 0.0, 0.0),
        (2.0, 1.0, 0.0),
        (3.0, 0.0, 0.0),
        (4.0, 0.0, 0.0),
        (3.0, 1.0, 0.0),
        (5.0, 0.0, 0.0),
        (6.0, 0.0, 0.0),
        (6.0, 1.0, 0.0),
        (5.0, 1.0, 0.0),
    )
    for node_id, point in enumerate(coordinates, start=1):
        model.add_node(node_id, *point)
    model.add_element(
        1,
        QualifiedE4PLShellElement(
            1,
            (1, 2, 3, 4),
            "steel",
            thickness=0.027,
            reference_normal=(0.0, 0.0, 1.0),
        ),
    )
    model.add_element(
        2,
        QualifiedE4PLS3ShellElement(
            2,
            (2, 5, 3),
            "steel",
            thickness=0.027,
            reference_normal=(0.0, 0.0, 1.0),
        ),
    )
    # The numbered triangle winds clockwise and its authoritative owner normal
    # is correspondingly reversed.  Director polarity is independently
    # reversed as well, exercising both physical orientation dispositions.
    model.add_element(
        3,
        QualifiedE4PLS3ShellElement(
            3,
            (7, 9, 8),
            "steel",
            thickness=0.027,
            reference_normal=(0.0, 0.0, -1.0),
            director_polarity=-1,
        ),
    )
    if include_legacy:
        model.add_element(
            4,
            ShellElement(
                4,
                (10, 11, 12, 13),
                "steel",
                thickness=0.027,
            ),
        )
    return model


def _displacements(model: FEModel) -> np.ndarray:
    size = max(dof for node in model.mesh.nodes.values() for dof in node.dofs) + 1
    return np.linspace(-3.75e-4, 5.25e-4, size, dtype=np.float64)


def _assert_same_fields(actual: dict[str, Any], expected: dict[str, Any]) -> None:
    assert tuple(actual) == tuple(expected)
    for name, expected_value in expected.items():
        actual_value = actual[name]
        if isinstance(expected_value, np.ndarray):
            assert isinstance(actual_value, np.ndarray)
            assert actual_value.dtype.str == expected_value.dtype.str
            assert actual_value.shape == expected_value.shape
            assert actual_value.strides == expected_value.strides
            assert actual_value.tobytes(order="C") == expected_value.tobytes(
                order="C"
            )
        else:
            assert actual_value == expected_value


_INTERFACE_FIELDS = (
    "global_xx_top",
    "global_yy_top",
    "global_xy_top",
    "global_xx_bot",
    "global_yy_bot",
    "global_xy_bot",
)


def _assert_interface_matches_direct(
    model: FEModel,
    displacement: np.ndarray,
    element_id: int,
    actual: dict[str, Any],
) -> None:
    direct = recovery._compute_one_element_stress(
        model,
        displacement,
        element_id,
        return_global=True,
    )
    assert direct is not None
    assert tuple(actual) == _INTERFACE_FIELDS
    _assert_same_fields(
        actual,
        {name: direct[1][name] for name in _INTERFACE_FIELDS},
    )


def test_private_interface_batch_is_byte_identical_to_direct_q4_and_s3() -> None:
    model = _mixed_model()
    displacement = _displacements(model)
    assemble_stiffness_matrix(model)

    actual = recovery._recover_qualified_interface_fields(
        model,
        displacement,
        (3, 1, 2, 3),
        return_global=True,
    )

    # Selection is de-duplicated and returned in the model's deterministic
    # element order, matching the established recovery API.
    assert tuple(actual) == (1, 2, 3)
    for element_id in actual:
        _assert_interface_matches_direct(
            model,
            displacement,
            element_id,
            actual[element_id],
        )


def test_narrow_q4_is_byte_identical_for_all_d4_numberings_and_orientation() -> None:
    base = np.asarray(
        (
            (-0.12, 0.06, 0.0),
            (1.24, -0.08, 0.0),
            (1.07, 0.93, 0.0),
            (0.04, 1.12, 0.0),
        ),
        dtype=np.float64,
    )
    cx, sx = np.cos(0.37), np.sin(0.37)
    cy, sy = np.cos(-0.29), np.sin(-0.29)
    rotation = np.asarray(
        (
            (cy, sy * sx, sy * cx),
            (0.0, cx, -sx),
            (-sy, cy * sx, cy * cx),
        ),
        dtype=np.float64,
    )
    coordinates = base @ rotation.T + np.asarray((2.25, -1.75, 0.8))
    owner = rotation @ np.asarray((0.0, 0.0, 1.0))
    numberings = (
        (1, 2, 3, 4),
        (2, 3, 4, 1),
        (3, 4, 1, 2),
        (4, 1, 2, 3),
        (1, 4, 3, 2),
        (4, 3, 2, 1),
        (3, 2, 1, 4),
        (2, 1, 4, 3),
    )
    for case_id, numbering in enumerate(numberings):
        model = FEModel(f"qualified-interface-q4-d4-{case_id}")
        model.add_material("steel", 210.0e9, 0.3, density=7850.0)
        for node_id, point in enumerate(coordinates, start=1):
            model.add_node(node_id, *point)
        model.add_element(
            1,
            QualifiedE4PLShellElement(
                1,
                numbering,
                "steel",
                thickness=0.027,
                reference_normal=owner,
            ),
        )
        assemble_stiffness_matrix(model)
        displacement = _displacements(model)
        actual = recovery._recover_qualified_interface_fields(
            model,
            displacement,
            (1,),
        )
        _assert_interface_matches_direct(
            model,
            displacement,
            1,
            actual[1],
        )


def test_narrow_s3_is_byte_identical_for_all_d3_numberings_and_polarities() -> None:
    base = np.asarray(
        ((0.0, 0.0, 0.0), (1.17, 0.04, 0.0), (0.31, 0.96, 0.0)),
        dtype=np.float64,
    )
    cx, sx = np.cos(-0.31), np.sin(-0.31)
    cy, sy = np.cos(0.23), np.sin(0.23)
    rotation = np.asarray(
        (
            (cy, sy * sx, sy * cx),
            (0.0, cx, -sx),
            (-sy, cy * sx, cy * cx),
        ),
        dtype=np.float64,
    )
    coordinates = base @ rotation.T + np.asarray((-2.0, 1.4, 0.65))
    owner = rotation @ np.asarray((0.0, 0.0, 1.0))
    numberings = tuple(itertools.permutations((1, 2, 3)))
    for case_id, (numbering, polarity) in enumerate(
        entry
        for numbering in numberings
        for entry in ((numbering, 1), (numbering, -1))
    ):
        model = FEModel(f"qualified-interface-s3-d3-{case_id}")
        model.add_material("steel", 210.0e9, 0.3, density=7850.0)
        for node_id, point in enumerate(coordinates, start=1):
            model.add_node(node_id, *point)
        inversions = sum(
            numbering[first] > numbering[second]
            for first in range(3)
            for second in range(first + 1, 3)
        )
        numbered_owner = owner if inversions % 2 == 0 else -owner
        model.add_element(
            1,
            QualifiedE4PLS3ShellElement(
                1,
                numbering,
                "steel",
                thickness=0.027,
                reference_normal=numbered_owner,
                director_polarity=polarity,
            ),
        )
        assemble_stiffness_matrix(model)
        displacement = _displacements(model)
        actual = recovery._recover_qualified_interface_fields(
            model,
            displacement,
            (1,),
        )
        _assert_interface_matches_direct(
            model,
            displacement,
            1,
            actual[1],
        )


def test_narrow_geometry_group_reuse_is_byte_identical_across_translations() -> None:
    model = FEModel("qualified-interface-translated-groups")
    model.add_material("steel", 210.0e9, 0.3, density=7850.0)
    node_id = 1
    element_id = 1
    for family in ("q4", "s3"):
        for copy_index in range(5):
            offset = 4.0 * copy_index + (0.0 if family == "q4" else 22.0)
            points = (
                (
                    (offset, 0.0, 0.0),
                    (offset + 1.0, 0.0, 0.0),
                    (offset + 1.0, 1.0, 0.0),
                    (offset, 1.0, 0.0),
                )
                if family == "q4"
                else (
                    (offset, 0.0, 0.0),
                    (offset + 1.0, 0.0, 0.0),
                    (offset, 1.0, 0.0),
                )
            )
            node_ids = []
            for point in points:
                model.add_node(node_id, *point)
                node_ids.append(node_id)
                node_id += 1
            element_type = (
                QualifiedE4PLShellElement
                if family == "q4"
                else QualifiedE4PLS3ShellElement
            )
            model.add_element(
                element_id,
                element_type(
                    element_id,
                    tuple(node_ids),
                    "steel",
                    thickness=0.027,
                    reference_normal=(0.0, 0.0, 1.0),
                ),
            )
            element_id += 1
    assemble_stiffness_matrix(model)
    q4_keys = {
        object.__getattribute__(model.mesh.elements[current_id], "__dict__")[
            "_qualified_cache_key"
        ]
        for current_id in range(1, 6)
    }
    s3_keys = {
        object.__getattribute__(model.mesh.elements[current_id], "__dict__")[
            "_qualified_cache_key"
        ]
        for current_id in range(6, 11)
    }
    assert len(q4_keys) == 1
    # Barycentric thirds can split translated S3s into two binary64 geometry
    # keys; both groups still reuse their setup exactly.
    assert 1 <= len(s3_keys) < 5
    displacement = _displacements(model)
    selected = tuple(model.mesh.elements)
    actual = recovery._recover_qualified_interface_fields(
        model,
        displacement,
        selected,
    )
    assert tuple(actual) == selected
    for current_id in selected:
        _assert_interface_matches_direct(
            model,
            displacement,
            current_id,
            actual[current_id],
        )


def test_private_interface_batch_preserves_exact_local_field_order() -> None:
    model = _mixed_model()
    displacement = _displacements(model)

    actual = recovery._recover_qualified_interface_fields(
        model,
        displacement,
        (2, 1),
        return_global=False,
    )

    assert tuple(actual) == (1, 2)
    for element_id in actual:
        direct = recovery._compute_one_element_stress(
            model,
            displacement,
            element_id,
            return_global=False,
        )
        assert direct is not None
        _assert_same_fields(actual[element_id], direct[1])


def test_private_interface_batch_retains_scalar_fallback() -> None:
    model = _mixed_model(include_legacy=True)
    displacement = _displacements(model)
    assemble_stiffness_matrix(model)
    direct = recovery._compute_one_element_stress(
        model,
        displacement,
        4,
        return_global=True,
    )
    assert direct is not None
    actual = recovery._recover_qualified_interface_fields(
        model,
        displacement,
        (1, 2, 4),
        return_global=True,
    )

    assert tuple(actual) == (1, 2, 4)
    _assert_same_fields(actual[4], direct[1])


def _forged_closure_code() -> Any:
    forged_result: dict[str, Any] = {}

    def forged(*_args: Any, **_kwargs: Any) -> Any:
        return forged_result

    return forged.__code__


@pytest.mark.parametrize(
    ("target_name", "attribute", "replacement"),
    (
        (
            "_recover_qualified_interface_fields_under_lease_impl",
            "__code__",
            (lambda *_args, **_kwargs: {}).__code__,
        ),
        (
            "_recover_qualified_interface_fields_under_lease_impl",
            "__defaults__",
            (),
        ),
        (
            "_recover_qualified_interface_fields_under_lease_impl",
            "__kwdefaults__",
            {"forged": object()},
        ),
        (
            "_recover_qualified_interface_fields_under_lease_impl",
            "__module__",
            "forged.recovery",
        ),
        (
            "_recover_qualified_interface_fields_under_lease",
            "__code__",
            _forged_closure_code(),
        ),
        (
            "_recover_qualified_interface_fields_under_lease",
            "__defaults__",
            (),
        ),
        (
            "_recover_qualified_interface_fields_under_lease",
            "__kwdefaults__",
            {"return_global": False},
        ),
        (
            "_recover_qualified_interface_fields_under_lease",
            "__module__",
            "forged.recovery",
        ),
    ),
)
def test_private_interface_batch_rejects_operation_metadata_mutation(
    target_name: str,
    attribute: str,
    replacement: Any,
) -> None:
    model = _mixed_model()
    displacement = _displacements(model)
    assemble_stiffness_matrix(model)
    target = getattr(recovery, target_name)
    original = getattr(target, attribute)
    setattr(target, attribute, replacement)
    try:
        with pytest.raises(
            AssemblyError,
            match="interface-recovery operation authority changed",
        ):
            recovery._recover_qualified_interface_fields(
                model,
                displacement,
                (1, 2),
            )
    finally:
        setattr(target, attribute, original)

    recovered = recovery._recover_qualified_interface_fields(
        model,
        displacement,
        (1, 2),
    )
    for element_id in recovered:
        _assert_interface_matches_direct(
            model,
            displacement,
            element_id,
            recovered[element_id],
        )


@pytest.mark.parametrize(
    "target_name",
    (
        "_recover_qualified_interface_fields_under_lease_impl",
        "_recover_qualified_interface_fields_under_lease",
        "_compute_one_element_stress",
    ),
)
def test_private_interface_batch_rejects_module_dispatch_or_global_replacement(
    target_name: str,
) -> None:
    model = _mixed_model()
    displacement = _displacements(model)
    assemble_stiffness_matrix(model)
    original = vars(recovery)[target_name]
    vars(recovery)[target_name] = lambda *_args, **_kwargs: {}
    try:
        with pytest.raises(
            AssemblyError,
            match="interface-recovery operation authority changed",
        ):
            recovery._recover_qualified_interface_fields(
                model,
                displacement,
                (1, 2),
            )
    finally:
        vars(recovery)[target_name] = original


def test_private_interface_batch_rejects_module_name_replacement() -> None:
    model = _mixed_model()
    displacement = _displacements(model)
    assemble_stiffness_matrix(model)
    original = recovery.__name__
    recovery.__name__ = "forged.recovery"
    try:
        with pytest.raises(
            AssemblyError,
            match="interface-recovery operation authority changed",
        ):
            recovery._recover_qualified_interface_fields(
                model,
                displacement,
                (1, 2),
            )
    finally:
        recovery.__name__ = original


def test_private_interface_operation_mutations_fail_before_forged_code() -> None:
    model = _mixed_model()
    displacement = _displacements(model)
    assemble_stiffness_matrix(model)
    reached: list[str] = []
    vars(recovery)["_FORGED_RECOVERY_TRIPWIRE"] = reached

    implementation = recovery._recover_qualified_interface_fields_under_lease_impl
    dispatcher = recovery._recover_qualified_interface_fields_under_lease
    implementation_code = implementation.__code__
    dispatcher_code = dispatcher.__code__

    def forged_implementation(*_args: Any, **_kwargs: Any) -> Any:
        _FORGED_RECOVERY_TRIPWIRE.append("implementation")  # type: ignore[name-defined]
        return {}

    def forged_dispatcher_factory() -> Any:
        marker = "dispatcher"

        def forged_dispatcher(*_args: Any, **_kwargs: Any) -> Any:
            _FORGED_RECOVERY_TRIPWIRE.append(marker)  # type: ignore[name-defined]
            return {}

        return forged_dispatcher

    try:
        implementation.__code__ = forged_implementation.__code__
        with pytest.raises(
            AssemblyError,
            match="interface-recovery operation authority changed",
        ):
            recovery._recover_qualified_interface_fields(
                model,
                displacement,
                (1, 2),
            )
        implementation.__code__ = implementation_code

        dispatcher.__code__ = forged_dispatcher_factory().__code__
        with pytest.raises(
            AssemblyError,
            match="interface-recovery operation authority changed",
        ):
            recovery._recover_qualified_interface_fields(
                model,
                displacement,
                (1, 2),
            )
    finally:
        implementation.__code__ = implementation_code
        dispatcher.__code__ = dispatcher_code
        vars(recovery).pop("_FORGED_RECOVERY_TRIPWIRE", None)
    assert reached == []


def test_private_interface_global_mutation_fails_before_forged_fallback() -> None:
    model = _mixed_model(include_legacy=True)
    displacement = _displacements(model)
    assemble_stiffness_matrix(model)
    reached: list[int] = []
    original = recovery._compute_one_element_stress

    def forged(*args: Any, **_kwargs: Any) -> Any:
        reached.append(int(args[2]))
        return None

    recovery._compute_one_element_stress = forged
    try:
        with pytest.raises(
            AssemblyError,
            match="interface-recovery operation authority changed",
        ):
            recovery._recover_qualified_interface_fields(
                model,
                displacement,
                (4,),
            )
    finally:
        recovery._compute_one_element_stress = original
    assert reached == []


def test_private_interface_batch_rejects_mutate_restore_aba(
) -> None:
    model = _mixed_model()
    displacement = _displacements(model)

    class MutateRestoreArray:
        def __array__(
            self,
            dtype: Any = None,
            copy: Any = None,
        ) -> np.ndarray:
            del copy
            node = model.mesh.nodes[2]
            original_x = node.x
            node.x = original_x + 0.125
            node.x = original_x
            return np.asarray(displacement, dtype=dtype)

    with pytest.raises(
        AssemblyError,
        match="authority changed|inputs changed|incompatible qualified shell",
    ):
        recovery._recover_qualified_interface_fields(
            model,
            MutateRestoreArray(),
            (2,),
            return_global=True,
        )


def test_private_interface_batch_rejects_missing_element() -> None:
    model = _mixed_model()
    with pytest.raises(ValueError, match="element ids not found"):
        recovery._recover_qualified_interface_fields(
            model,
            _displacements(model),
            (999,),
        )


@pytest.mark.parametrize("restore_after_second", (False, True))
def test_private_interface_batch_snapshots_external_displacement_once(
    restore_after_second: bool,
) -> None:
    model = _mixed_model(include_legacy=True)
    displacement = _displacements(model)
    original_values = displacement.copy()
    changed_values = original_values + 0.125

    class MutatingLegacyShell(ShellElement):
        enabled = False

        def __init__(self, *args: Any, action: str, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.action = action

        def get_dof_mapping(self, mesh: Any) -> Any:
            if self.enabled:
                if self.action == "mutate":
                    displacement[:] = changed_values
                else:
                    displacement[:] = original_values
            return super().get_dof_mapping(mesh)

    first = MutatingLegacyShell(
        4,
        (10, 11, 12, 13),
        "steel",
        thickness=0.027,
        action="mutate",
    )
    model.mesh.elements[4] = first
    selected = [4]
    second: MutatingLegacyShell | None = None
    if restore_after_second:
        second = MutatingLegacyShell(
            5,
            (10, 11, 12, 13),
            "steel",
            thickness=0.027,
            action="restore",
        )
        model.add_element(5, second)
        selected.append(5)
    assemble_stiffness_matrix(model)
    expected = {
        element_id: recovery._compute_one_element_stress(
            model,
            original_values,
            element_id,
            return_global=True,
        )
        for element_id in selected
    }

    class ArmMutationOnConversion:
        def __array__(self, dtype: Any = None, copy: Any = None) -> np.ndarray:
            del copy
            first.enabled = True
            if second is not None:
                second.enabled = True
            return np.asarray(displacement, dtype=dtype)

    actual = recovery._recover_qualified_interface_fields(
        model,
        ArmMutationOnConversion(),
        tuple(selected),
    )
    for element_id in selected:
        assert expected[element_id] is not None
        _assert_same_fields(actual[element_id], expected[element_id][1])
    if restore_after_second:
        np.testing.assert_array_equal(displacement, original_values)
    else:
        np.testing.assert_array_equal(displacement, changed_values)


@pytest.mark.parametrize(
    "displacement",
    (
        np.zeros((2, 3), dtype=np.float64),
        np.asarray((0.0, np.nan), dtype=np.float64),
        np.asarray((0.0, np.inf), dtype=np.float64),
    ),
)
def test_private_interface_batch_rejects_malformed_displacement_snapshot(
    displacement: np.ndarray,
) -> None:
    model = _mixed_model()
    with pytest.raises(ValueError, match="finite vector"):
        recovery._recover_qualified_interface_fields(model, displacement, (1,))


def test_private_interface_batch_s3_route_reduces_guarded_dispatch_cost() -> None:
    model = _mixed_model()
    displacement = _displacements(model)
    repetitions = 11
    assemble_stiffness_matrix(model)

    # Warm numerical/component caches before comparing dispatch overhead.
    recovery._recover_qualified_interface_fields(model, displacement, (2, 3))
    for element_id in (2, 3):
        assert recovery._compute_one_element_stress(
            model,
            displacement,
            element_id,
            return_global=True,
        ) is not None

    batch_samples: list[float] = []
    for _ in range(repetitions):
        batch_start = perf_counter()
        recovery._recover_qualified_interface_fields(
            model,
            displacement,
            (2, 3),
            return_global=True,
        )
        batch_samples.append(perf_counter() - batch_start)

    scalar_samples: list[float] = []
    for _ in range(repetitions):
        scalar_start = perf_counter()
        for element_id in (2, 3):
            recovery._compute_one_element_stress(
                model,
                displacement,
                element_id,
                return_global=True,
            )
        scalar_samples.append(perf_counter() - scalar_start)

    # This is a regression guard against accidentally routing S3 back through
    # its complete public wrapper for every selected element.  Keep generous
    # headroom for shared CI hosts while still requiring a material reduction.
    assert median(batch_samples) < 0.9 * median(scalar_samples)
