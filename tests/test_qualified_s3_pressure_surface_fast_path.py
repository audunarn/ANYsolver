"""Exact-system-lease coverage for qualified S3 pressure metadata."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pytest

import anysolver.matrix_assembly as matrix_module
from anysolver import (
    FEModel,
    QualifiedE4PLS3ShellElement,
    QualifiedE4PLShellElement,
)
from anysolver.boundary import LoadCase
from anysolver.matrix_assembly import (
    _CAPTURE_QUALIFIED_ASSEMBLY_RUNTIME_LEASE,
    _TRY_QUALIFIED_S3_PRESSURE_SURFACE_COLD_RECORDS,
    _qualified_s3_pressure_surface_records,
    assemble_load_vector,
    assemble_system,
)


def _mixed_model(group_count: int) -> FEModel:
    model = FEModel("qualified-s3-pressure-surface-fast-path")
    model.add_material("steel", 210.0e9, 0.3, density=7850.0)
    node_id = 1
    element_id = 1
    for group in range(group_count):
        offset = float(3 * group)
        node_ids: list[int] = []
        for x, y in (
            (0.0, 0.0),
            (1.0, 0.0),
            (1.0, 1.0),
            (0.0, 1.0),
            (2.0, 0.0),
        ):
            model.add_node(node_id, offset + x, y, 0.0)
            node_ids.append(node_id)
            node_id += 1
        model.add_element(
            element_id,
            QualifiedE4PLShellElement(
                element_id,
                node_ids[:4],
                "steel",
                thickness=0.02,
            ),
        )
        element_id += 1
        model.add_element(
            element_id,
            QualifiedE4PLS3ShellElement(
                element_id,
                [node_ids[1], node_ids[4], node_ids[2]],
                "steel",
                thickness=0.02,
                reference_normal=(0.0, 0.0, 1.0),
                reference_surface_offset=float((group % 3) - 1) * 0.002,
            ),
        )
        element_id += 1
    return model


def _pressure_case(model: FEModel) -> LoadCase:
    load = LoadCase("mixed-pressure-surface")
    # Deliberately use reverse S3 order and interleave Q4 records.  The output
    # must retain pressure-map order while omitting Q4 metadata.
    element_ids = tuple(model.mesh.elements)
    for element_id in reversed(element_ids[1::2]):
        load.add_pressure_load(element_id, -300.0 - element_id)
    for element_id in element_ids[::2]:
        load.add_pressure_load(element_id, 500.0 + element_id)
    return load


def _scalar_records(model: FEModel, load: LoadCase) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for raw_element_id in load.pressure_loads:
        element_id = int(raw_element_id)
        element = model.mesh.get_element(element_id)
        if not isinstance(element, QualifiedE4PLS3ShellElement):
            continue
        offset = float(element.reference_surface_offset)
        result.append(
            {
                "element_id": element_id,
                "pressure_surface_id": "ELEMENT_NODAL_REFERENCE_SURFACE_V1",
                "reference_surface_offset": offset,
                "resultant_and_reaction_reference": (
                    "GLOBAL_NODAL_REFERENCE_COORDINATES"
                ),
                "section_origin_offset_from_reference": -offset,
                "virtual_work": "TRANSLATIONAL_NODAL_REFERENCE_SURFACE_ONLY",
            }
        )
    return result


def _canonical(value: object) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=False,
        ).encode("ascii")
        + b"\n"
    )


def test_mixed_system_pressure_records_match_scalar_bytes_and_order() -> None:
    model = _mixed_model(32)
    load = _pressure_case(model)
    expected_records = _scalar_records(model, load)

    _stiffness, system_load, system_info = assemble_system(model, load)
    scalar_load, scalar_info = assemble_load_vector(model, load)

    np.testing.assert_array_equal(system_load, scalar_load)
    actual_records = system_info["load"]["qualified_s3_pressure_surfaces"]
    assert _canonical(actual_records) == _canonical(expected_records)
    assert _canonical(actual_records) == _canonical(
        scalar_info["qualified_s3_pressure_surfaces"]
    )
    assert [record["element_id"] for record in actual_records] == list(
        reversed(tuple(model.mesh.elements)[1::2])
    )


def test_pressure_record_cold_authority_rejects_node_aba() -> None:
    model = _mixed_model(32)
    load = _pressure_case(model)
    lease = _CAPTURE_QUALIFIED_ASSEMBLY_RUNTIME_LEASE(
        model,
        context="pressure-record ABA preflight",
        allow_q4_cached_stiffness=True,
    )
    admitted, _records = _TRY_QUALIFIED_S3_PRESSURE_SURFACE_COLD_RECORDS(
        lease,
        model,
        load,
    )
    assert admitted is True
    node = model.mesh.nodes[1]
    original_x = node.x
    node.x = original_x + 0.125
    node.x = original_x

    with pytest.raises((RuntimeError, ValueError), match="qualified|changed|mutation"):
        _qualified_s3_pressure_surface_records(
            model,
            load,
            qualified_runtime_guard=lease,
        )


def test_small_mixed_pressure_model_retains_scalar_fallback() -> None:
    model = _mixed_model(2)
    load = _pressure_case(model)
    lease = _CAPTURE_QUALIFIED_ASSEMBLY_RUNTIME_LEASE(
        model,
        context="pressure-record scalar fallback preflight",
        allow_q4_cached_stiffness=True,
    )
    admitted, _records = _TRY_QUALIFIED_S3_PRESSURE_SURFACE_COLD_RECORDS(
        lease,
        model,
        load,
    )
    assert admitted is False

    actual = _qualified_s3_pressure_surface_records(
        model,
        load,
        qualified_runtime_guard=lease,
    )
    lease(model, context="pressure-record scalar fallback output", final=True)
    assert _canonical(actual) == _canonical(_scalar_records(model, load))


@pytest.mark.parametrize(
    "name",
    (
        "_TRY_QUALIFIED_S3_PRESSURE_SURFACE_COLD_RECORDS",
        "_qualified_s3_pressure_surface_records",
    ),
)
def test_pressure_metadata_rejects_module_provider_replacement_before_call(
    name: str,
) -> None:
    model = _mixed_model(32)
    load = _pressure_case(model)
    original = getattr(matrix_module, name)
    reached: list[str] = []

    def forged(*_args: Any, **_kwargs: Any) -> Any:
        reached.append(name)
        raise AssertionError("forged pressure metadata provider executed")

    setattr(matrix_module, name, forged)
    try:
        with pytest.raises(
            (RuntimeError, ValueError),
            match="authority|qualified|changed",
        ):
            assemble_load_vector(model, load)
    finally:
        setattr(matrix_module, name, original)
    assert reached == []


@pytest.mark.parametrize(
    ("name", "attribute", "replacement"),
    (
        (
            "_TRY_QUALIFIED_S3_PRESSURE_SURFACE_COLD_RECORDS",
            "__defaults__",
            (),
        ),
        (
            "_TRY_QUALIFIED_S3_PRESSURE_SURFACE_COLD_RECORDS",
            "__kwdefaults__",
            {},
        ),
        (
            "_qualified_s3_pressure_surface_records",
            "__defaults__",
            (),
        ),
        (
            "_qualified_s3_pressure_surface_records",
            "__kwdefaults__",
            {},
        ),
    ),
)
def test_pressure_metadata_rejects_provider_default_metadata_change(
    name: str,
    attribute: str,
    replacement: Any,
) -> None:
    model = _mixed_model(32)
    load = _pressure_case(model)
    provider = getattr(matrix_module, name)
    original = getattr(provider, attribute)
    setattr(provider, attribute, replacement)
    try:
        with pytest.raises(
            (RuntimeError, ValueError),
            match="authority|qualified|changed",
        ):
            assemble_load_vector(model, load)
    finally:
        setattr(provider, attribute, original)


def test_pressure_metadata_rejects_cold_helper_code_replacement() -> None:
    model = _mixed_model(32)
    load = _pressure_case(model)
    helper = matrix_module._TRY_QUALIFIED_S3_PRESSURE_SURFACE_COLD_RECORDS
    original = helper.__code__

    def forged_factory() -> Any:
        exact_dict_get = exact_dict_items = exact_error = object()
        exact_int = exact_len = exact_list_getitem = object()
        exact_lookup = exact_s3_type = exact_type = object()

        def forged(*_args: Any, **_kwargs: Any) -> Any:
            _ = (
                exact_dict_get,
                exact_dict_items,
                exact_error,
                exact_int,
                exact_len,
                exact_list_getitem,
                exact_lookup,
                exact_s3_type,
                exact_type,
            )
            raise AssertionError("forged pressure metadata helper executed")

        return forged

    forged = forged_factory()
    assert forged.__code__.co_freevars == original.co_freevars
    helper.__code__ = forged.__code__
    try:
        with pytest.raises(
            (RuntimeError, ValueError),
            match="authority|qualified|changed",
        ):
            assemble_load_vector(model, load)
    finally:
        helper.__code__ = original


def test_pressure_metadata_rejects_module_global_aba_under_captured_lease() -> None:
    model = _mixed_model(32)
    load = _pressure_case(model)
    lease = _CAPTURE_QUALIFIED_ASSEMBLY_RUNTIME_LEASE(
        model,
        context="pressure-record provider ABA preflight",
        allow_q4_cached_stiffness=True,
    )
    original = matrix_module._TRY_QUALIFIED_S3_PRESSURE_SURFACE_COLD_RECORDS
    reached: list[str] = []

    def forged(*_args: Any, **_kwargs: Any) -> Any:
        reached.append("forged")
        raise AssertionError("forged pressure metadata helper executed")

    setattr(
        matrix_module,
        "_TRY_QUALIFIED_S3_PRESSURE_SURFACE_COLD_RECORDS",
        forged,
    )
    setattr(
        matrix_module,
        "_TRY_QUALIFIED_S3_PRESSURE_SURFACE_COLD_RECORDS",
        original,
    )
    with pytest.raises(
        (RuntimeError, ValueError),
        match="authority|qualified|changed",
    ):
        _qualified_s3_pressure_surface_records(
            model,
            load,
            qualified_runtime_guard=lease,
        )
    assert reached == []
