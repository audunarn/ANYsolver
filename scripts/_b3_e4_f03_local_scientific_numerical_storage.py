"""Exact schemas for F03 operator, scaled-state, and positivity evidence."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import sparse

from scripts import _b3_e4_f03_local_primal_assembly as assembly
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_sparse_storage as sparse_storage
from scripts import _b3_e4_f03_local_scientific_storage as storage


@dataclass(frozen=True, slots=True)
class OperatorCounts:
    shell: int
    beam: int
    root: int

    def __post_init__(self):
        if any(type(value) is not int or value <= 0 for value in (self.shell, self.beam, self.root)):
            raise ValueError("positive exact F03 operator counts required")


@dataclass(frozen=True, slots=True)
class ScaledCounts:
    kbar: int
    cbar: int
    h: int
    kbar_alternate: int
    cbar_alternate: int
    h_alternate: int

    def __post_init__(self):
        if any(
            type(value) is not int or value <= 0
            for value in (
                self.kbar, self.cbar, self.h,
                self.kbar_alternate, self.cbar_alternate, self.h_alternate,
            )
        ):
            raise ValueError("positive exact F03 scaled-system counts required")


@dataclass(frozen=True, slots=True)
class PositivityCounts:
    kbar: int
    lower: int
    upper: int

    def __post_init__(self):
        if any(type(value) is not int or value <= 0 for value in (self.kbar, self.lower, self.upper)):
            raise ValueError("positive exact F03 positivity counts required")


@dataclass(frozen=True, slots=True)
class OperatorEvidence:
    shell: object
    beam: object
    root: object
    load: np.ndarray


@dataclass(frozen=True, slots=True)
class ScaledEvidence:
    kbar: object
    cbar: object
    h: object
    kbar_alternate: object
    cbar_alternate: object
    h_alternate: object
    d: np.ndarray
    r: np.ndarray
    b: np.ndarray
    b_alternate: np.ndarray
    z: np.ndarray
    q: np.ndarray
    eta: np.ndarray
    h_z: np.ndarray


@dataclass(frozen=True, slots=True)
class PositivityEvidence:
    kbar: object
    lower: object
    upper: object
    diagonal: np.ndarray
    row_map: np.ndarray
    column_map: np.ndarray
    inverse_gather: np.ndarray


def _case(value: cases.ScientificCase) -> cases.ScientificCase:
    if type(value) is not cases.ScientificCase or value not in cases.CASES:
        raise ValueError("frozen F03 scientific case required")
    return value


def _assembly_limits(case: cases.ScientificCase) -> dict:
    return assembly.preflight(cases.compile_case(_case(case)), cases.ASSEMBLY_BUDGET)


def _operator_counts(value: OperatorEvidence, case: cases.ScientificCase) -> OperatorCounts:
    case = _case(case)
    if (
        type(value) is not OperatorEvidence
        or type(value.shell) is not sparse.csr_matrix
        or value.shell.shape != (case.physical_dofs, case.physical_dofs)
        or type(value.beam) is not sparse.csr_matrix
        or value.beam.shape != (case.physical_dofs, case.physical_dofs)
        or type(value.root) is not sparse.csr_matrix
        or value.root.shape != (3, case.physical_dofs)
    ):
        raise ValueError("typed canonical F03 operator evidence required")
    return OperatorCounts(value.shell.nnz, value.beam.nnz, value.root.nnz)


def _scaled_counts(value: ScaledEvidence, case: cases.ScientificCase) -> ScaledCounts:
    case = _case(case)
    n, order = case.physical_dofs, case.kkt_order
    expected = (
        (value.kbar, sparse.csr_matrix, (n, n)),
        (value.cbar, sparse.csr_matrix, (3, n)),
        (value.h, sparse.csc_matrix, (order, order)),
        (value.kbar_alternate, sparse.csr_matrix, (n, n)),
        (value.cbar_alternate, sparse.csr_matrix, (3, n)),
        (value.h_alternate, sparse.csc_matrix, (order, order)),
    ) if type(value) is ScaledEvidence else ()
    if len(expected) != 6 or any(type(item) is not cls or item.shape != shape for item, cls, shape in expected):
        raise ValueError("typed canonical F03 scaled evidence required")
    return ScaledCounts(*(item.nnz for item, _, _ in expected))


def _positivity_counts(
    value: PositivityEvidence, case: cases.ScientificCase,
) -> PositivityCounts:
    case = _case(case)
    n = case.physical_dofs
    expected = (
        (value.kbar, sparse.csr_matrix),
        (value.lower, sparse.csc_matrix),
        (value.upper, sparse.csc_matrix),
    ) if type(value) is PositivityEvidence else ()
    if len(expected) != 3 or any(type(item) is not cls or item.shape != (n, n) for item, cls in expected):
        raise ValueError("typed canonical F03 positivity evidence required")
    return PositivityCounts(*(item.nnz for item, _ in expected))


def operator_specs(
    case: cases.ScientificCase, counts: OperatorCounts,
) -> tuple[tuple[sparse_storage.SparseSpec, ...], tuple[storage.ArraySpec, ...]]:
    case = _case(case)
    if type(counts) is not OperatorCounts:
        raise ValueError("exact F03 operator counts required")
    limits = _assembly_limits(case)
    if (
        counts.shell > limits["shell_triplets"]
        or counts.beam > limits["beam_triplets"]
        or counts.root > limits["root_triplets_envelope"]
    ):
        raise ValueError("F03 operator count exceeds topology envelope")
    n = case.physical_dofs
    sparse_specs = (
        sparse_storage.SparseSpec("shell", (n, n), counts.shell, "csr"),
        sparse_storage.SparseSpec("beam", (n, n), counts.beam, "csr"),
        sparse_storage.SparseSpec("root", (3, n), counts.root, "csr"),
    )
    return sparse_specs, (storage.ArraySpec("load", (n,), np.dtype("<f8")),)


def scaled_specs(
    case: cases.ScientificCase, counts: ScaledCounts,
) -> tuple[tuple[sparse_storage.SparseSpec, ...], tuple[storage.ArraySpec, ...]]:
    case = _case(case)
    if type(counts) is not ScaledCounts:
        raise ValueError("exact F03 scaled-system counts required")
    limits = _assembly_limits(case)
    primal_limit = limits["shell_triplets"] + limits["beam_triplets"]
    values = (
        counts.kbar, counts.cbar, counts.h,
        counts.kbar_alternate, counts.cbar_alternate, counts.h_alternate,
    )
    if (
        counts.kbar > primal_limit
        or counts.kbar_alternate > primal_limit
        or counts.cbar > limits["root_triplets_envelope"]
        or counts.cbar_alternate > limits["root_triplets_envelope"]
        or counts.h > case.kkt_nnz
        or counts.h_alternate > case.kkt_nnz
        or any(value > cases.SYSTEM_BUDGET.max_nnz for value in values)
    ):
        raise ValueError("F03 scaled-system count exceeds registered envelope")
    n = case.physical_dofs
    order = case.kkt_order
    sparse_specs = (
        sparse_storage.SparseSpec("kbar", (n, n), counts.kbar, "csr"),
        sparse_storage.SparseSpec("cbar", (3, n), counts.cbar, "csr"),
        sparse_storage.SparseSpec("h", (order, order), counts.h, "csc"),
        sparse_storage.SparseSpec(
            "kbar_alternate", (n, n), counts.kbar_alternate, "csr",
        ),
        sparse_storage.SparseSpec(
            "cbar_alternate", (3, n), counts.cbar_alternate, "csr",
        ),
        sparse_storage.SparseSpec(
            "h_alternate", (order, order), counts.h_alternate, "csc",
        ),
    )
    arrays = (
        storage.ArraySpec("d", (n,), np.dtype("<f8")),
        storage.ArraySpec("r", (3,), np.dtype("<f8")),
        storage.ArraySpec("b", (order,), np.dtype("<f8")),
        storage.ArraySpec("b_alternate", (order,), np.dtype("<f8")),
        storage.ArraySpec("z", (order,), np.dtype("<f8")),
        storage.ArraySpec("q", (n,), np.dtype("<f8")),
        storage.ArraySpec("eta", (3,), np.dtype("<f8")),
        storage.ArraySpec("h_z", (order,), np.dtype("<f8")),
    )
    return sparse_specs, arrays


def positivity_specs(
    case: cases.ScientificCase, counts: PositivityCounts,
) -> tuple[tuple[sparse_storage.SparseSpec, ...], tuple[storage.ArraySpec, ...]]:
    case = _case(case)
    if type(counts) is not PositivityCounts:
        raise ValueError("exact F03 positivity counts required")
    limits = _assembly_limits(case)
    if (
        counts.kbar > limits["shell_triplets"] + limits["beam_triplets"]
        or counts.lower > cases.FACTOR_VALIDATION_BUDGET.max_nnz
        or counts.upper > cases.FACTOR_VALIDATION_BUDGET.max_nnz
        or counts.lower + counts.upper > cases.MAX_COMBINED_FACTOR_NNZ
    ):
        raise ValueError("F03 positivity count exceeds registered envelope")
    n = case.physical_dofs
    sparse_specs = (
        sparse_storage.SparseSpec("kbar", (n, n), counts.kbar, "csr"),
        sparse_storage.SparseSpec("lower", (n, n), counts.lower, "csc"),
        sparse_storage.SparseSpec("upper", (n, n), counts.upper, "csc"),
    )
    arrays = (
        storage.ArraySpec("diagonal", (n,), np.dtype("<f8")),
        storage.ArraySpec("row_map", (n,), np.dtype("<i8")),
        storage.ArraySpec("column_map", (n,), np.dtype("<i8")),
        storage.ArraySpec("inverse_gather", (n,), np.dtype("<i8")),
    )
    return sparse_specs, arrays


def _array_values(
    value: object, specs: tuple[storage.ArraySpec, ...],
) -> tuple[np.ndarray, ...]:
    result = []
    for spec in specs:
        item = getattr(value, spec.name, None)
        native = np.dtype(np.float64) if spec.dtype.kind == "f" else np.dtype(np.int64)
        if (
            type(item) is not np.ndarray
            or item.shape != spec.shape
            or item.dtype != native
            or not item.flags.c_contiguous
            or (spec.dtype.kind == "f" and not np.isfinite(item).all())
        ):
            raise ValueError(f"invalid F03 numerical evidence array: {spec.name}")
        result.append(item)
    return tuple(result)


def _group_bound(specs: tuple[storage.ArraySpec, ...]) -> int:
    return sum(spec.nbytes + storage.MAX_ZIP_MEMBER_OVERHEAD for spec in specs)


def _write(
    path: Path,
    value: object,
    sparse_specs: tuple[sparse_storage.SparseSpec, ...],
    array_specs: tuple[storage.ArraySpec, ...],
) -> None:
    matrices = {spec.name: getattr(value, spec.name, None) for spec in sparse_specs}
    arrays = _array_values(value, array_specs)
    for spec in sparse_specs:
        sparse_storage._check_matrix(matrices[spec.name], spec)
    encoded = sparse_storage.encode(matrices, sparse_specs)
    encoded.update(
        {
            spec.name: np.asarray(item, dtype=spec.dtype).copy()
            for spec, item in zip(array_specs, arrays)
        }
    )
    specs = sparse_storage.array_specs(sparse_specs) + array_specs
    storage.write_group(path, encoded, specs, max_raw_bytes=_group_bound(specs))


def _read(
    path: Path,
    sparse_specs: tuple[sparse_storage.SparseSpec, ...],
    array_specs: tuple[storage.ArraySpec, ...],
) -> tuple[dict[str, object], dict[str, np.ndarray]]:
    specs = sparse_storage.array_specs(sparse_specs) + array_specs
    encoded = storage.read_group(path, specs, max_raw_bytes=_group_bound(specs))
    matrix_names = {spec.name for spec in sparse_storage.array_specs(sparse_specs)}
    matrices = sparse_storage.decode(
        {name: value for name, value in encoded.items() if name in matrix_names}, sparse_specs,
    )
    arrays = {
        spec.name: np.asarray(
            encoded[spec.name],
            dtype=np.float64 if spec.dtype.kind == "f" else np.int64,
        ).copy()
        for spec in array_specs
    }
    return matrices, arrays


def write_operators(
    path: Path, value: OperatorEvidence, case: cases.ScientificCase,
) -> OperatorCounts:
    counts = _operator_counts(value, case)
    sparse_specs, arrays = operator_specs(case, counts)
    _write(path, value, sparse_specs, arrays)
    return counts


def read_operators(
    path: Path, case: cases.ScientificCase, counts: OperatorCounts,
) -> OperatorEvidence:
    sparse_specs, array_specs = operator_specs(case, counts)
    matrices, arrays = _read(path, sparse_specs, array_specs)
    return OperatorEvidence(matrices["shell"], matrices["beam"], matrices["root"], arrays["load"])


def write_scaled(
    path: Path, value: ScaledEvidence, case: cases.ScientificCase,
) -> ScaledCounts:
    counts = _scaled_counts(value, case)
    sparse_specs, arrays = scaled_specs(case, counts)
    _write(path, value, sparse_specs, arrays)
    return counts


def read_scaled(
    path: Path, case: cases.ScientificCase, counts: ScaledCounts,
) -> ScaledEvidence:
    sparse_specs, array_specs = scaled_specs(case, counts)
    matrices, arrays = _read(path, sparse_specs, array_specs)
    return ScaledEvidence(**matrices, **arrays)


def write_positivity(
    path: Path, value: PositivityEvidence, case: cases.ScientificCase,
) -> PositivityCounts:
    counts = _positivity_counts(value, case)
    sparse_specs, arrays = positivity_specs(case, counts)
    _write(path, value, sparse_specs, arrays)
    return counts


def read_positivity(
    path: Path, case: cases.ScientificCase, counts: PositivityCounts,
) -> PositivityEvidence:
    sparse_specs, array_specs = positivity_specs(case, counts)
    matrices, arrays = _read(path, sparse_specs, array_specs)
    return PositivityEvidence(**matrices, **arrays)
