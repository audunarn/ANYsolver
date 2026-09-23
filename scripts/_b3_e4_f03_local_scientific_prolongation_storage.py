"""Exact bounded storage for each F03 case's nested-space prolongation."""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import numpy as np

from scripts import _b3_e4_f03_local_grid as topology
from scripts import _b3_e4_f03_local_prolongation as transfer
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_exact_storage as exact_storage
from scripts import _b3_e4_f03_local_scientific_storage as storage


PREDECESSOR = {target: source for source, target in cases.NESTED_TRANSITIONS}


def _case(value: cases.ScientificCase) -> cases.ScientificCase:
    if type(value) is not cases.ScientificCase or value not in cases.CASES:
        raise ValueError("frozen F03 scientific case required")
    return value


def predecessor(case: cases.ScientificCase) -> cases.ScientificCase | None:
    case = _case(case)
    case_id = PREDECESSOR.get(case.case_id)
    return None if case_id is None else cases.case_by_id(case_id)


def _capacity(case: cases.ScientificCase) -> int:
    source = predecessor(case)
    return 0 if source is None else case.physical_dofs * (source.degree + 1) ** 2


def array_specs(case: cases.ScientificCase) -> tuple[storage.ArraySpec, ...]:
    capacity = _capacity(_case(case))
    return (
        storage.ArraySpec("present", (1,), np.dtype("|b1"), finite=False),
        storage.ArraySpec("source_dofs", (1,), np.dtype("<i8")),
        storage.ArraySpec("target_dofs", (1,), np.dtype("<i8")),
        storage.ArraySpec("entry_count", (1,), np.dtype("<i8")),
        storage.ArraySpec("integer_bits", (1,), np.dtype("<i8")),
        storage.ArraySpec("rows", (capacity,), np.dtype("<i8")),
        storage.ArraySpec("columns", (capacity,), np.dtype("<i8")),
    )


def fraction_spec(count: int) -> tuple[exact_storage.FractionSpec, ...]:
    if type(count) is not int or count < 0:
        raise ValueError("nonnegative exact F03 prolongation count required")
    return (exact_storage.FractionSpec("weights", (count,)),)


def fraction_limits(case: cases.ScientificCase) -> exact_storage.FractionLimits:
    return exact_storage.FractionLimits(
        max(1, _capacity(_case(case))), transfer.MAX_WEIGHT_BITS,
        cases.ASSEMBLY_BUDGET.max_trace_integer_bits,
        cases.PROLONGATION_WEIGHT_BYTES,
    )


def _group_bound(specs: tuple[storage.ArraySpec, ...]) -> int:
    return sum(spec.nbytes + storage.MAX_ZIP_MEMBER_OVERHEAD for spec in specs)


def _validated(
    value: transfer.ExactProlongation | None, case: cases.ScientificCase,
) -> tuple[int, int, int, int, tuple[Fraction, ...]]:
    case = _case(case)
    source = predecessor(case)
    if source is None:
        if value is not None:
            raise ValueError("coarsest F03 case cannot carry a prolongation")
        return 0, 0, 0, 0, ()
    if type(value) is not transfer.ExactProlongation:
        raise ValueError("validated exact F03 prolongation required")
    count = len(value.weights)
    if (
        value.source_dofs != source.physical_dofs
        or value.target_dofs != case.physical_dofs
        or type(value.rows) is not np.ndarray
        or value.rows.dtype != np.int64
        or value.rows.shape != (count,)
        or not value.rows.flags.c_contiguous
        or type(value.columns) is not np.ndarray
        or value.columns.dtype != np.int64
        or value.columns.shape != (count,)
        or not value.columns.flags.c_contiguous
        or type(value.weights) is not tuple
        or count <= 0
        or count > _capacity(case)
        or any(type(weight) is not Fraction or weight == 0 for weight in value.weights)
        or np.any(value.rows < 0)
        or np.any(value.rows >= value.target_dofs)
        or np.any(value.columns < 0)
        or np.any(value.columns >= value.source_dofs)
        or np.any(value.rows[1:] < value.rows[:-1])
        or len(set(zip(value.rows.tolist(), value.columns.tolist()))) != count
    ):
        raise ValueError("invalid exact F03 prolongation inventory")
    bits = sum(
        weight.numerator.bit_length() + weight.denominator.bit_length()
        for weight in value.weights
    )
    if bits != value.integer_bits or bits > cases.ASSEMBLY_BUDGET.max_trace_integer_bits:
        raise ValueError("F03 prolongation bit count disagrees with exact weights")
    exact_storage._validate_values(
        {"weights": value.weights}, fraction_spec(count), fraction_limits(case),
    )
    return value.source_dofs, value.target_dofs, count, bits, value.weights


def write(
    directory: Path,
    value: transfer.ExactProlongation | None,
    case: cases.ScientificCase,
) -> None:
    directory = Path(directory)
    source_dofs, target_dofs, count, bits, weights = _validated(value, case)
    specs = array_specs(case)
    capacity = _capacity(case)
    rows = np.full(capacity, -1, dtype="<i8")
    columns = np.full(capacity, -1, dtype="<i8")
    if count:
        rows[:count] = np.asarray(value.rows, dtype="<i8")
        columns[:count] = np.asarray(value.columns, dtype="<i8")
    arrays = {
        "present": np.array([value is not None], dtype=np.bool_),
        "source_dofs": np.array([source_dofs], dtype="<i8"),
        "target_dofs": np.array([target_dofs], dtype="<i8"),
        "entry_count": np.array([count], dtype="<i8"),
        "integer_bits": np.array([bits], dtype="<i8"),
        "rows": rows,
        "columns": columns,
    }
    weight_specs = fraction_spec(count)
    limits = fraction_limits(case)
    exact_storage._payload({"weights": weights}, weight_specs, limits)
    storage.write_group(
        directory / "prolongations.npz", arrays, specs, max_raw_bytes=_group_bound(specs),
    )
    exact_storage.write_group(
        directory / "prolongation_weights.json",
        {"weights": weights}, weight_specs, limits=limits,
    )


def read(
    directory: Path, case: cases.ScientificCase,
) -> transfer.ExactProlongation | None:
    directory = Path(directory)
    case = _case(case)
    specs = array_specs(case)
    arrays = storage.read_group(
        directory / "prolongations.npz", specs, max_raw_bytes=_group_bound(specs),
    )
    present = bool(arrays["present"][0])
    source_dofs = int(arrays["source_dofs"][0])
    target_dofs = int(arrays["target_dofs"][0])
    count = int(arrays["entry_count"][0])
    bits = int(arrays["integer_bits"][0])
    capacity = _capacity(case)
    if (
        not 0 <= count <= capacity
        or np.any(arrays["rows"][count:] != -1)
        or np.any(arrays["columns"][count:] != -1)
    ):
        raise ValueError("invalid padded F03 prolongation inventory")
    weights = exact_storage.read_group(
        directory / "prolongation_weights.json", fraction_spec(count),
        limits=fraction_limits(case),
    )["weights"]
    source = predecessor(case)
    if source is None:
        if present or any((source_dofs, target_dofs, count, bits)) or weights:
            raise ValueError("coarsest F03 prolongation evidence must be empty")
        return None
    if not present:
        raise ValueError("nested F03 case is missing exact prolongation evidence")
    result = object.__new__(transfer.ExactProlongation)
    values = (
        source_dofs, target_dofs,
        topology._readonly_int(arrays["rows"][:count]),
        topology._readonly_int(arrays["columns"][:count]),
        weights, bits,
    )
    for name, item in zip(
        ("source_dofs", "target_dofs", "rows", "columns", "weights", "integer_bits"),
        values,
    ):
        object.__setattr__(result, name, item)
    _validated(result, case)
    return result
