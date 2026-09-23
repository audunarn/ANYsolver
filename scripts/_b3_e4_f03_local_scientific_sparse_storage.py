"""Canonical sparse-matrix adapters for bounded F03 evidence groups."""
from __future__ import annotations

from dataclasses import dataclass
import math
import re

import numpy as np
from scipy import sparse

from scripts import _b3_e4_f03_local_scientific_storage as storage


NAME = re.compile(r"[a-z][a-z0-9_]{0,47}")


@dataclass(frozen=True, slots=True)
class SparseSpec:
    name: str
    shape: tuple[int, int]
    nnz: int
    format: str

    def __post_init__(self):
        if (
            type(self.name) is not str
            or NAME.fullmatch(self.name) is None
            or type(self.shape) is not tuple
            or len(self.shape) != 2
            or any(type(value) is not int or value <= 0 for value in self.shape)
            or type(self.nnz) is not int
            or not 0 <= self.nnz <= math.prod(self.shape)
            or self.format not in ("csr", "csc")
        ):
            raise ValueError("invalid bounded F03 sparse specification")

    @property
    def outer(self) -> int:
        return self.shape[0] if self.format == "csr" else self.shape[1]

    @property
    def inner(self) -> int:
        return self.shape[1] if self.format == "csr" else self.shape[0]


def array_specs(specs: tuple[SparseSpec, ...]) -> tuple[storage.ArraySpec, ...]:
    if (
        type(specs) is not tuple
        or not specs
        or any(type(spec) is not SparseSpec for spec in specs)
        or len({spec.name for spec in specs}) != len(specs)
    ):
        raise ValueError("unique bounded F03 sparse specifications required")
    result = []
    for spec in specs:
        result.extend((
            storage.ArraySpec(spec.name + "_data", (spec.nnz,), np.dtype("<f8")),
            storage.ArraySpec(spec.name + "_indices", (spec.nnz,), np.dtype("<i8")),
            storage.ArraySpec(spec.name + "_indptr", (spec.outer + 1,), np.dtype("<i8")),
        ))
    return tuple(result)


def _check_matrix(value, spec: SparseSpec) -> None:
    expected = sparse.csr_matrix if spec.format == "csr" else sparse.csc_matrix
    if (
        type(value) is not expected
        or value.shape != spec.shape
        or value.nnz != spec.nnz
        or type(value.data) is not np.ndarray
        or value.data.dtype != np.float64
        or not value.data.flags.c_contiguous
        or type(value.indices) is not np.ndarray
        or value.indices.dtype not in (np.dtype("int32"), np.dtype("int64"))
        or not value.indices.flags.c_contiguous
        or type(value.indptr) is not np.ndarray
        or value.indptr.dtype not in (np.dtype("int32"), np.dtype("int64"))
        or not value.indptr.flags.c_contiguous
        or value.data.shape != (spec.nnz,)
        or value.indices.shape != (spec.nnz,)
        or value.indptr.shape != (spec.outer + 1,)
        or not np.isfinite(value.data).all()
        or value.indptr[0] != 0
        or value.indptr[-1] != spec.nnz
        or np.any(value.indptr < 0)
        or np.any(value.indptr[1:] < value.indptr[:-1])
        or np.any(value.indices < 0)
        or np.any(value.indices >= spec.inner)
    ):
        raise ValueError(f"invalid canonical F03 sparse matrix: {spec.name}")
    for left, right in zip(value.indptr, value.indptr[1:]):
        if np.any(value.indices[int(left) + 1:int(right)] <= value.indices[int(left):int(right) - 1]):
            raise ValueError(f"invalid canonical F03 sparse matrix: {spec.name}")


def encode(
    matrices: dict[str, object],
    specs: tuple[SparseSpec, ...],
) -> dict[str, np.ndarray]:
    array_specs(specs)
    if type(matrices) is not dict or set(matrices) != {spec.name for spec in specs}:
        raise ValueError("invalid F03 sparse-matrix inventory")
    for spec in specs:
        _check_matrix(matrices[spec.name], spec)
    arrays = {}
    for spec in specs:
        value = matrices[spec.name]
        arrays[spec.name + "_data"] = _little_float_copy(value.data)
        arrays[spec.name + "_indices"] = np.asarray(value.indices, dtype="<i8").copy()
        arrays[spec.name + "_indptr"] = np.asarray(value.indptr, dtype="<i8").copy()
    return arrays


def _little_float_copy(value: np.ndarray) -> np.ndarray:
    return np.asarray(value, dtype="<f8").copy()


def _native_float_copy(value: np.ndarray) -> np.ndarray:
    return np.asarray(value, dtype=np.float64).copy()


def _check_saved_structure(
    arrays: dict[str, np.ndarray],
    spec: SparseSpec,
    expected_by_name: dict[str, storage.ArraySpec],
) -> None:
    data = arrays[spec.name + "_data"]
    indices = arrays[spec.name + "_indices"]
    indptr = arrays[spec.name + "_indptr"]
    for value, expected_spec in zip(
        (data, indices, indptr),
        (
            expected_by_name[spec.name + "_data"],
            expected_by_name[spec.name + "_indices"],
            expected_by_name[spec.name + "_indptr"],
        ),
    ):
        storage._check_array(value, expected_spec)
    if (
        indptr[0] != 0
        or indptr[-1] != spec.nnz
        or np.any(indptr < 0)
        or np.any(indptr[1:] < indptr[:-1])
        or np.any(indices < 0)
        or np.any(indices >= spec.inner)
    ):
        raise ValueError(f"invalid saved F03 sparse structure: {spec.name}")
    for left, right in zip(indptr, indptr[1:]):
        if np.any(indices[int(left) + 1:int(right)] <= indices[int(left):int(right) - 1]):
            raise ValueError(f"invalid saved F03 sparse structure: {spec.name}")


def _construct_matrix(
    arrays: dict[str, np.ndarray], spec: SparseSpec,
):
    cls = sparse.csr_matrix if spec.format == "csr" else sparse.csc_matrix
    value = cls(
        (
            _native_float_copy(arrays[spec.name + "_data"]),
            arrays[spec.name + "_indices"].copy(),
            arrays[spec.name + "_indptr"].copy(),
        ),
        shape=spec.shape,
        copy=False,
    )
    _check_matrix(value, spec)
    return value


def decode(
    arrays: dict[str, np.ndarray],
    specs: tuple[SparseSpec, ...],
) -> dict[str, object]:
    expected = array_specs(specs)
    if type(arrays) is not dict or set(arrays) != {spec.name for spec in expected}:
        raise ValueError("invalid F03 sparse-array inventory")
    result = {}
    expected_by_name = {item.name: item for item in expected}
    for spec in specs:
        _check_saved_structure(arrays, spec, expected_by_name)
    for spec in specs:
        result[spec.name] = _construct_matrix(arrays, spec)
    return result
