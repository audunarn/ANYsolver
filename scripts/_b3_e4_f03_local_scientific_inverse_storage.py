"""Single-write inverse blocks and their canonical F03 index."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import io
import json
import os
from pathlib import Path

import numpy as np

from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_evidence_index as evidence
from scripts import _b3_e4_f03_local_scientific_storage as storage


SCHEMA = "f03_local_scientific_inverse_index_v1"
MAX_INDEX_BYTES = cases.INVERSE_INDEX_BYTES
DIGEST = frozenset("0123456789abcdef")


@dataclass(frozen=True, slots=True)
class BlockRecord:
    start: int
    columns: int
    rows: int
    raw_bytes: int
    file_bytes: int
    name: str
    sha256: str

    def __post_init__(self):
        if (
            any(type(value) is not int for value in (
                self.start, self.columns, self.rows, self.raw_bytes, self.file_bytes,
            ))
            or self.start < 0
            or not 1 <= self.columns <= archive.BLOCK_COLUMNS
            or self.rows <= 0
            or self.raw_bytes != 8 * self.rows * self.columns
            or not self.raw_bytes < self.file_bytes <= self.raw_bytes + storage.MAX_HEADER_BYTES
            or type(self.name) is not str
            or type(self.sha256) is not str
            or len(self.sha256) != 64
            or set(self.sha256) - DIGEST
        ):
            raise ValueError("invalid F03 inverse-block record")


@dataclass(frozen=True, slots=True)
class InverseIndex:
    schema: str
    case_id: str
    source_commit: str
    plan_sha256: str
    total_raw_bytes: int
    total_file_bytes: int
    blocks: tuple[BlockRecord, ...]

    def __post_init__(self):
        if (
            self.schema != SCHEMA
            or type(self.case_id) is not str
            or type(self.source_commit) is not str
            or len(self.source_commit) != 40
            or set(self.source_commit) - DIGEST
            or type(self.plan_sha256) is not str
            or len(self.plan_sha256) != 64
            or set(self.plan_sha256) - DIGEST
            or type(self.total_raw_bytes) is not int
            or type(self.total_file_bytes) is not int
            or type(self.blocks) is not tuple
            or not self.blocks
            or any(type(item) is not BlockRecord for item in self.blocks)
            or self.total_raw_bytes != sum(item.raw_bytes for item in self.blocks)
            or self.total_file_bytes != sum(item.file_bytes for item in self.blocks)
        ):
            raise ValueError("invalid F03 inverse index")


def _plan_sha256(plan: archive.CaseArchivePlan) -> str:
    return hashlib.sha256(archive._payload(plan)).hexdigest()


def _block(plan: archive.CaseArchivePlan, start: int) -> archive.InverseBlock:
    if type(plan) is not archive.CaseArchivePlan or type(start) is not int:
        raise ValueError("validated F03 inverse plan and integer start required")
    found = tuple(item for item in plan.inverse_blocks if item.start == start)
    if len(found) != 1:
        raise ValueError("unplanned F03 inverse block start")
    return found[0]


def _path(directory: Path, block: archive.InverseBlock) -> Path:
    return Path(directory).joinpath(*Path(block.name).parts)


def write_block(
    directory: Path, plan: archive.CaseArchivePlan, start: int, value: np.ndarray,
) -> Path:
    block = _block(plan, start)
    if (
        type(value) is not np.ndarray
        or value.dtype != np.dtype(np.float64)
        or value.shape != (block.rows, block.columns)
        or not value.flags.c_contiguous
        or not np.isfinite(value).all()
    ):
        raise ValueError("finite native float64 F03 inverse block required")
    canonical = np.asarray(value, dtype="<f8").copy()
    path = _path(directory, block)
    with evidence._open_directory_no_follow(path.parent):
        with path.open("xb") as stream:
            np.lib.format.write_array(stream, canonical, allow_pickle=False)
            if stream.tell() > block.bytes + storage.MAX_HEADER_BYTES:
                raise ValueError("written F03 inverse block exceeds exact bound")
    return path


def prepare_directory(directory: Path) -> Path:
    directory = Path(directory)
    with evidence._open_directory_no_follow(directory):
        inverse = directory / "inverse"
        inverse.mkdir()
    with evidence._open_directory_no_follow(inverse):
        pass
    return inverse


def _read_block_payload(path: Path, block: archive.InverseBlock) -> tuple[bytes, int]:
    maximum = block.bytes + storage.MAX_HEADER_BYTES
    with evidence._open_no_follow(path) as stream:
        info = os.fstat(stream.fileno())
        identity = evidence._FileIdentity(
            block.name, info.st_size, info.st_dev, info.st_ino,
            info.st_mtime_ns, info.st_ctime_ns,
        )
        if not evidence._same_file(info, identity) or not block.bytes < info.st_size <= maximum:
            raise ValueError("F03 inverse block file identity or size is invalid")
        payload = stream.read(maximum + 1)
        if not evidence._same_file(os.fstat(stream.fileno()), identity):
            raise ValueError("F03 inverse block changed while reading")
    if len(payload) > maximum:
        raise ValueError("F03 inverse block exceeds exact bound")
    stream = io.BytesIO(payload)
    try:
        version = np.lib.format.read_magic(stream)
    except ValueError as exc:
        raise ValueError("invalid F03 inverse NPY magic") from exc
    reader = {
        (1, 0): np.lib.format.read_array_header_1_0,
        (2, 0): np.lib.format.read_array_header_2_0,
    }.get(version)
    if reader is None:
        raise ValueError("unsupported F03 inverse NPY header version")
    shape, fortran, dtype = reader(stream, max_header_size=storage.MAX_HEADER_BYTES)
    offset = stream.tell()
    if (
        shape != (block.rows, block.columns)
        or fortran
        or dtype != np.dtype("<f8")
        or offset > storage.MAX_HEADER_BYTES
        or len(payload) - offset != block.bytes
    ):
        raise ValueError("F03 inverse NPY header disagrees with exact plan")
    return payload, offset


def _validate_open_block(stream, identity, block: archive.InverseBlock) -> None:
    maximum = block.bytes + storage.MAX_HEADER_BYTES
    if (
        not evidence._same_file(os.fstat(stream.fileno()), identity)
        or not block.bytes < identity.bytes <= maximum
    ):
        raise ValueError("F03 inverse block file identity or size is invalid")
    stream.seek(0)
    payload = stream.read(maximum + 1)
    if len(payload) != identity.bytes or len(payload) > maximum:
        raise ValueError("F03 inverse block exceeds exact bound")
    if not evidence._same_file(os.fstat(stream.fileno()), identity):
        raise ValueError("F03 inverse block changed while validating")
    encoded = io.BytesIO(payload)
    try:
        version = np.lib.format.read_magic(encoded)
    except ValueError as exc:
        raise ValueError("invalid F03 inverse NPY magic") from exc
    reader = {
        (1, 0): np.lib.format.read_array_header_1_0,
        (2, 0): np.lib.format.read_array_header_2_0,
    }.get(version)
    if reader is None:
        raise ValueError("unsupported F03 inverse NPY header version")
    shape, fortran, dtype = reader(encoded, max_header_size=storage.MAX_HEADER_BYTES)
    offset = encoded.tell()
    if (
        shape != (block.rows, block.columns)
        or fortran
        or dtype != np.dtype("<f8")
        or offset > storage.MAX_HEADER_BYTES
        or len(payload) - offset != block.bytes
    ):
        raise ValueError("F03 inverse NPY header disagrees with exact plan")
    values = np.frombuffer(
        payload, dtype="<f8", count=block.rows * block.columns, offset=offset,
    )
    if not np.isfinite(values).all():
        raise ValueError("nonfinite F03 inverse block")
    stream.seek(0)


def read_block(
    directory: Path, plan: archive.CaseArchivePlan, start: int,
) -> np.ndarray:
    block = _block(plan, start)
    payload, offset = _read_block_payload(_path(directory, block), block)
    value = np.frombuffer(
        payload, dtype="<f8", count=block.rows * block.columns, offset=offset,
    ).reshape(block.rows, block.columns)
    if not np.isfinite(value).all():
        raise ValueError("nonfinite F03 inverse block")
    return np.asarray(value, dtype=np.float64).copy()


def make_index(directory: Path, plan: archive.CaseArchivePlan) -> InverseIndex:
    if type(plan) is not archive.CaseArchivePlan:
        raise ValueError("validated F03 archive plan required")
    inverse = Path(directory) / "inverse"
    names = tuple(Path(block.name).name for block in plan.inverse_blocks)
    maximum = sum(block.bytes + storage.MAX_HEADER_BYTES for block in plan.inverse_blocks)
    with evidence._snapshot(inverse, names, maximum, frozenset()) as (identities, streams):
        return _index_from_snapshot(plan, identities, streams)


def _index_from_snapshot(plan, identities, streams) -> InverseIndex:
    if len(identities) != len(plan.inverse_blocks) or len(streams) != len(identities):
        raise ValueError("incomplete F03 inverse snapshot")
    records = []
    for block, identity, stream in zip(plan.inverse_blocks, identities, streams):
        if (
            identity.name != Path(block.name).name
            or not block.bytes < identity.bytes <= block.bytes + storage.MAX_HEADER_BYTES
        ):
            raise ValueError("F03 inverse block file size or order disagrees with plan")
        _validate_open_block(stream, identity, block)
        records.append(BlockRecord(
            block.start, block.columns, block.rows, block.bytes, identity.bytes,
            block.name, evidence._hash_open(stream, identity),
        ))
    return InverseIndex(
        SCHEMA, plan.case_id, plan.source_commit, _plan_sha256(plan),
        sum(item.bytes for item in plan.inverse_blocks),
        sum(item.file_bytes for item in records), tuple(records),
    )


def _payload(index: InverseIndex) -> bytes:
    if type(index) is not InverseIndex:
        raise ValueError("validated F03 inverse index required")
    value = {
        "schema": index.schema,
        "case_id": index.case_id,
        "source_commit": index.source_commit,
        "plan_sha256": index.plan_sha256,
        "total_raw_bytes": index.total_raw_bytes,
        "total_file_bytes": index.total_file_bytes,
        "blocks": [
            {
                "start": item.start,
                "columns": item.columns,
                "rows": item.rows,
                "raw_bytes": item.raw_bytes,
                "file_bytes": item.file_bytes,
                "name": item.name,
                "sha256": item.sha256,
            }
            for item in index.blocks
        ],
    }
    payload = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "ascii"
    )
    if len(payload) > MAX_INDEX_BYTES:
        raise ValueError("F03 inverse index exceeds declared bound")
    return payload


def write_index(directory: Path, plan: archive.CaseArchivePlan) -> tuple[InverseIndex, str]:
    directory = Path(directory)
    inverse = directory / "inverse"
    names = tuple(Path(block.name).name for block in plan.inverse_blocks)
    maximum = sum(block.bytes + storage.MAX_HEADER_BYTES for block in plan.inverse_blocks)
    with evidence._snapshot(inverse, names, maximum, frozenset()) as (identities, streams):
        index = _index_from_snapshot(plan, identities, streams)
        payload = _payload(index)
        with evidence._open_directory_no_follow(directory):
            with (directory / "inverse_index.json").open("xb") as output:
                output.write(payload)
    return index, hashlib.sha256(payload).hexdigest()


def _decode(payload: bytes) -> InverseIndex:
    if type(payload) is not bytes or len(payload) > MAX_INDEX_BYTES:
        raise ValueError("invalid bounded F03 inverse index payload")
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid F03 inverse index JSON") from exc
    keys = {
        "schema", "case_id", "source_commit", "plan_sha256", "total_raw_bytes",
        "total_file_bytes", "blocks",
    }
    if type(value) is not dict or set(value) != keys or type(value["blocks"]) is not list:
        raise ValueError("invalid F03 inverse index inventory")
    blocks = []
    block_keys = {
        "start", "columns", "rows", "raw_bytes", "file_bytes", "name", "sha256",
    }
    for item in value["blocks"]:
        if type(item) is not dict or set(item) != block_keys:
            raise ValueError("invalid F03 inverse block inventory")
        blocks.append(BlockRecord(
            item["start"], item["columns"], item["rows"], item["raw_bytes"],
            item["file_bytes"], item["name"], item["sha256"],
        ))
    index = InverseIndex(
        value["schema"], value["case_id"], value["source_commit"], value["plan_sha256"],
        value["total_raw_bytes"], value["total_file_bytes"], tuple(blocks),
    )
    if _payload(index) != payload:
        raise ValueError("noncanonical F03 inverse index encoding")
    return index


def read_index(directory: Path, plan: archive.CaseArchivePlan) -> tuple[InverseIndex, str]:
    directory = Path(directory)
    path = directory / "inverse_index.json"
    inverse = directory / "inverse"
    names = tuple(Path(block.name).name for block in plan.inverse_blocks)
    maximum = sum(block.bytes + storage.MAX_HEADER_BYTES for block in plan.inverse_blocks)
    with evidence._open_directory_no_follow(directory):
        with evidence._open_no_follow(path) as stream:
            info = os.fstat(stream.fileno())
            identity = evidence._FileIdentity(
                "inverse_index.json", info.st_size, info.st_dev, info.st_ino,
                info.st_mtime_ns, info.st_ctime_ns,
            )
            if not evidence._same_file(info, identity) or identity.bytes > MAX_INDEX_BYTES:
                raise ValueError("F03 inverse index identity or size is invalid")
            payload = stream.read(MAX_INDEX_BYTES + 1)
            if len(payload) != identity.bytes:
                raise ValueError("F03 inverse index changed while reading")
            index = _decode(payload)
            with evidence._snapshot(
                inverse, names, maximum, frozenset(),
            ) as (identities, streams):
                expected = _index_from_snapshot(plan, identities, streams)
                if _payload(index) != _payload(expected):
                    raise ValueError("stale or mismatched F03 inverse index")
                if not evidence._same_file(os.fstat(stream.fileno()), identity):
                    raise ValueError("F03 inverse index changed during verification")
                with evidence._open_no_follow(path) as final:
                    if not evidence._same_file(os.fstat(final.fileno()), identity):
                        raise ValueError("F03 inverse index changed after verification")
    return index, hashlib.sha256(payload).hexdigest()
