"""Single-write inverse blocks and their canonical F03 index."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import io
import json
import math
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
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        np.lib.format.write_array(stream, canonical, allow_pickle=False)
        if stream.tell() > block.bytes + storage.MAX_HEADER_BYTES:
            raise ValueError("written F03 inverse block exceeds exact bound")
    return path


def _read_block_payload(path: Path, block: archive.InverseBlock) -> tuple[bytes, int]:
    maximum = block.bytes + storage.MAX_HEADER_BYTES
    with evidence._open_no_follow(path) as stream:
        payload = stream.read(maximum + 1)
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
    tree = evidence._tree(inverse, names, frozenset())
    records = []
    for block, name in zip(plan.inverse_blocks, names):
        identity = tree.get(name)
        if identity is None:
            raise ValueError("missing F03 inverse block")
        if not block.bytes < identity.bytes <= block.bytes + storage.MAX_HEADER_BYTES:
            raise ValueError("F03 inverse block file size disagrees with plan")
        digest = evidence._hash_member(inverse / name, identity)
        records.append(BlockRecord(
            block.start, block.columns, block.rows, block.bytes, identity.bytes,
            block.name, digest,
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
    index = make_index(directory, plan)
    payload = _payload(index)
    with (Path(directory) / "inverse_index.json").open("xb") as stream:
        stream.write(payload)
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
    path = Path(directory) / "inverse_index.json"
    with evidence._open_no_follow(path) as stream:
        payload = stream.read(MAX_INDEX_BYTES + 1)
    if len(payload) > MAX_INDEX_BYTES:
        raise ValueError("F03 inverse index exceeds declared bound")
    index = _decode(payload)
    expected = make_index(directory, plan)
    if _payload(index) != _payload(expected):
        raise ValueError("stale or mismatched F03 inverse index")
    return index, hashlib.sha256(payload).hexdigest()
