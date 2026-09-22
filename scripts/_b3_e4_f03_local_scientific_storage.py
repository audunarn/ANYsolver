"""Strict bounded NPZ groups for F03 saved-only scientific evidence."""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import re
import zipfile

import numpy as np


NAME = re.compile(r"[a-z][a-z0-9_]{0,63}")
DTYPES = {
    np.dtype("<f8"),
    np.dtype("<i8"),
    np.dtype("|u1"),
    np.dtype("|b1"),
}
MAX_HEADER_BYTES = 4096


@dataclass(frozen=True, slots=True)
class ArraySpec:
    name: str
    shape: tuple[int, ...]
    dtype: np.dtype
    finite: bool = True

    def __post_init__(self):
        dtype = np.dtype(self.dtype)
        if (
            type(self.name) is not str
            or NAME.fullmatch(self.name) is None
            or type(self.shape) is not tuple
            or not 1 <= len(self.shape) <= 4
            or any(type(value) is not int or value < 0 for value in self.shape)
            or math.prod(self.shape) > 100_000_000
            or dtype not in DTYPES
            or type(self.finite) is not bool
            or (self.finite and dtype.kind not in "fiu")
        ):
            raise ValueError("invalid bounded F03 evidence array specification")
        object.__setattr__(self, "dtype", dtype)

    @property
    def nbytes(self) -> int:
        return math.prod(self.shape) * self.dtype.itemsize


def _validate_specs(specs: tuple[ArraySpec, ...], max_raw_bytes: int) -> dict[str, ArraySpec]:
    if (
        type(specs) is not tuple
        or not specs
        or any(type(spec) is not ArraySpec for spec in specs)
        or len({spec.name for spec in specs}) != len(specs)
        or type(max_raw_bytes) is not int
        or max_raw_bytes <= 0
    ):
        raise ValueError("unique bounded F03 evidence array specifications required")
    if sum(spec.nbytes + MAX_HEADER_BYTES for spec in specs) > max_raw_bytes:
        raise ValueError("F03 evidence array specification exceeds raw-byte bound")
    return {spec.name: spec for spec in specs}


def _owned(value: np.ndarray, spec: ArraySpec) -> np.ndarray:
    if (
        type(value) is not np.ndarray
        or value.shape != spec.shape
        or value.dtype != spec.dtype
        or not value.flags.c_contiguous
        or (spec.finite and value.dtype.kind == "f" and not np.isfinite(value).all())
    ):
        raise ValueError(f"invalid F03 evidence array: {spec.name}")
    return np.frombuffer(value.tobytes(order="C"), dtype=spec.dtype).reshape(spec.shape)


def write_group(
    path: Path,
    arrays: dict[str, np.ndarray],
    specs: tuple[ArraySpec, ...],
    *,
    max_raw_bytes: int,
) -> None:
    expected = _validate_specs(specs, max_raw_bytes)
    if type(arrays) is not dict or set(arrays) != set(expected):
        raise ValueError("invalid F03 evidence group inventory")
    owned = {spec.name: _owned(arrays[spec.name], spec) for spec in specs}
    values = [arrays[spec.name] for spec in specs]
    if any(
        np.shares_memory(first, second)
        for index, first in enumerate(values)
        for second in values[index + 1:]
    ):
        raise ValueError("aliased F03 evidence arrays")
    path = Path(path)
    with path.open("xb") as raw:
        with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_DEFLATED) as group:
            for spec in specs:
                with group.open(spec.name + ".npy", "w", force_zip64=True) as stream:
                    np.lib.format.write_array(stream, owned[spec.name], allow_pickle=False)


def read_group(
    path: Path,
    specs: tuple[ArraySpec, ...],
    *,
    max_raw_bytes: int,
) -> dict[str, np.ndarray]:
    expected = _validate_specs(specs, max_raw_bytes)
    path = Path(path)
    arrays = {}
    with path.open("rb") as raw:
        raw.seek(0, 2)
        if raw.tell() > max_raw_bytes:
            raise ValueError("F03 evidence group exceeds compressed-byte bound")
        raw.seek(0)
        with zipfile.ZipFile(raw) as group:
            infos = group.infolist()
            names = [info.filename for info in infos]
            required = [spec.name + ".npy" for spec in specs]
            if (
                names != required
                or len(names) != len(set(names))
                or sum(info.file_size for info in infos) > max_raw_bytes
            ):
                raise ValueError("invalid F03 evidence group ZIP inventory or size")
            for spec, info in zip(specs, infos):
                with group.open(info) as stream:
                    version = np.lib.format.read_magic(stream)
                    reader = {
                        (1, 0): np.lib.format.read_array_header_1_0,
                        (2, 0): np.lib.format.read_array_header_2_0,
                    }.get(version)
                    if reader is None:
                        raise ValueError("unsupported F03 evidence NPY header version")
                    shape, fortran, dtype = reader(stream, max_header_size=MAX_HEADER_BYTES)
                    if (
                        shape != spec.shape
                        or fortran
                        or dtype != spec.dtype
                        or stream.tell() > MAX_HEADER_BYTES
                        or info.file_size - stream.tell() != spec.nbytes
                    ):
                        raise ValueError("F03 evidence NPY header disagrees with exact schema")
                with group.open(info) as stream:
                    value = np.lib.format.read_array(
                        stream, allow_pickle=False, max_header_size=MAX_HEADER_BYTES,
                    )
                arrays[spec.name] = _owned(value, spec)
    values = list(arrays.values())
    if any(
        np.shares_memory(first, second)
        for index, first in enumerate(values)
        for second in values[index + 1:]
    ):
        raise ValueError("aliased loaded F03 evidence arrays")
    return arrays
