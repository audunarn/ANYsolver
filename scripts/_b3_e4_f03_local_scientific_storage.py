"""Strict bounded NPZ groups for F03 saved-only scientific evidence."""
from __future__ import annotations

from dataclasses import dataclass
import io
import math
from pathlib import Path
import re
import struct
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
MAX_ZIP_MEMBER_OVERHEAD = 4096
MAX_CENTRAL_DIRECTORY_BYTES_PER_MEMBER = 1024


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
    if sum(spec.nbytes + MAX_ZIP_MEMBER_OVERHEAD for spec in specs) > max_raw_bytes:
        raise ValueError("F03 evidence array specification exceeds raw-byte bound")
    return {spec.name: spec for spec in specs}


def _check_array(value: np.ndarray, spec: ArraySpec) -> None:
    if (
        type(value) is not np.ndarray
        or value.shape != spec.shape
        or value.dtype != spec.dtype
        or not value.flags.c_contiguous
        or (spec.finite and value.dtype.kind == "f" and not np.isfinite(value).all())
    ):
        raise ValueError(f"invalid F03 evidence array: {spec.name}")


def _owned(value: np.ndarray, spec: ArraySpec) -> np.ndarray:
    _check_array(value, spec)
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
    for spec in specs:
        _check_array(arrays[spec.name], spec)
    values = [arrays[spec.name] for spec in specs]
    if any(
        np.shares_memory(first, second)
        for index, first in enumerate(values)
        for second in values[index + 1:]
    ):
        raise ValueError("aliased F03 evidence arrays")
    owned = {spec.name: _owned(arrays[spec.name], spec) for spec in specs}
    path = Path(path)
    with path.open("xb") as raw:
        with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_STORED) as group:
            for spec in specs:
                with group.open(spec.name + ".npy", "w", force_zip64=True) as stream:
                    np.lib.format.write_array(stream, owned[spec.name], allow_pickle=False)
        if raw.tell() > max_raw_bytes:
            raise ValueError("written F03 evidence group exceeded its preflight bound")


def _snapshot(path: Path, max_raw_bytes: int) -> bytes:
    with Path(path).open("rb") as raw:
        payload = raw.read(max_raw_bytes + 1)
    if len(payload) > max_raw_bytes:
        raise ValueError("F03 evidence group exceeds compressed-byte bound")
    return payload


def _preflight_central_directory(payload: bytes, member_count: int) -> None:
    """Reject large/multi-disk/ZIP64 inventories before ZipFile materializes them."""
    tail_start = max(0, len(payload) - (65_535 + 22))
    offset = payload.rfind(b"PK\x05\x06", tail_start)
    if offset < 0 or len(payload) - offset < 22:
        raise ValueError("missing bounded F03 ZIP end record")
    signature, disk, central_disk, disk_entries, entries, size, start, comment = struct.unpack(
        "<4s4H2LH", payload[offset:offset + 22]
    )
    if (
        signature != b"PK\x05\x06"
        or disk != 0
        or central_disk != 0
        or disk_entries != member_count
        or entries != member_count
        or comment != 0
        or offset + 22 != len(payload)
        or size > member_count * MAX_CENTRAL_DIRECTORY_BYTES_PER_MEMBER
        or start + size != offset
        or any(value in (0xFFFF, 0xFFFFFFFF) for value in (disk_entries, entries, size, start))
    ):
        raise ValueError("invalid bounded F03 ZIP central-directory envelope")


def read_group(
    path: Path,
    specs: tuple[ArraySpec, ...],
    *,
    max_raw_bytes: int,
) -> dict[str, np.ndarray]:
    expected = _validate_specs(specs, max_raw_bytes)
    path = Path(path)
    arrays = {}
    payload = _snapshot(path, max_raw_bytes)
    _preflight_central_directory(payload, len(specs))
    with zipfile.ZipFile(io.BytesIO(payload)) as group:
        infos = group.infolist()
        names = [info.filename for info in infos]
        required = [spec.name + ".npy" for spec in specs]
        if (
            names != required
            or len(names) != len(set(names))
            or sum(info.file_size for info in infos) > max_raw_bytes
            or any(
                info.file_size > spec.nbytes + MAX_HEADER_BYTES
                for spec, info in zip(specs, infos)
            )
            or any(
                info.compress_type != zipfile.ZIP_STORED
                or info.compress_size != info.file_size
                or info.flag_bits & 0x1
                for info in infos
            )
        ):
            raise ValueError("invalid F03 evidence group ZIP inventory or size")
        for spec, info in zip(specs, infos):
            member = group.read(info)
            if len(member) != info.file_size:
                raise ValueError("invalid bounded F03 NPY member size")
            stream = io.BytesIO(member)
            version = np.lib.format.read_magic(stream)
            reader = {
                (1, 0): np.lib.format.read_array_header_1_0,
                (2, 0): np.lib.format.read_array_header_2_0,
            }.get(version)
            if reader is None:
                raise ValueError("unsupported F03 evidence NPY header version")
            shape, fortran, dtype = reader(stream, max_header_size=MAX_HEADER_BYTES)
            offset = stream.tell()
            if (
                shape != spec.shape
                or fortran
                or dtype != spec.dtype
                or offset > MAX_HEADER_BYTES
                or len(member) - offset != spec.nbytes
            ):
                raise ValueError("F03 evidence NPY header disagrees with exact schema")
            value = np.frombuffer(member, dtype=spec.dtype, count=math.prod(spec.shape), offset=offset)
            value = value.reshape(spec.shape)
            arrays[spec.name] = _owned(value, spec)
    values = list(arrays.values())
    if any(
        np.shares_memory(first, second)
        for index, first in enumerate(values)
        for second in values[index + 1:]
    ):
        raise ValueError("aliased loaded F03 evidence arrays")
    return arrays
