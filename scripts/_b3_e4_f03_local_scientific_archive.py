"""Strict archive-plan schema for the bounded F03 local scientific screen.

Only the immutable plan is stored here.  Numerical arrays will be admitted by
the later producer schema; this module cannot assemble, factor, or solve.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
from pathlib import Path
import re
import zipfile

from scripts import _b3_e4_f03_local_scientific_cases as cases


SCHEMA = "f03_local_scientific_archive_plan_v1"
MAX_PLAN_BYTES = cases.ARCHIVE_PLAN_BYTES
BLOCK_COLUMNS = 4
COMMIT = re.compile(r"[0-9a-f]{40}")

GROUP_MEMBERS = (
    "operators_primary.npz",
    "operators_alternate.npz",
    "scaled_state.npz",
    "positivity.npz",
    "inverse_index.json",
    "ports.npz",
    "numerical_index.json",
    "prolongations.npz",
    "prolongation_weights.json",
    "saved_interface.npz",
    "saved_work.npz",
    "saved_norm.npz",
    "saved_composition.npz",
    "balances.npz",
    "evidence_index.json",
    "case_receipt.json",
)


@dataclass(frozen=True, slots=True)
class InverseBlock:
    start: int
    columns: int
    rows: int
    bytes: int

    def __post_init__(self):
        if (
            any(type(value) is not int for value in (self.start, self.columns, self.rows, self.bytes))
            or self.start < 0
            or not 1 <= self.columns <= BLOCK_COLUMNS
            or self.rows <= 0
            or self.bytes != 8 * self.rows * self.columns
        ):
            raise ValueError("invalid F03 inverse-block plan")

    @property
    def name(self) -> str:
        return f"inverse/block_{self.start:04d}_{self.columns}.npy"


@dataclass(frozen=True, slots=True)
class CaseArchivePlan:
    schema: str
    source_commit: str
    case_id: str
    topology_sha256: str
    inventory_sha256: str
    kkt_order: int
    resource_limits: tuple[tuple[str, int], ...]
    raw_archive_bytes: int
    inverse_blocks: tuple[InverseBlock, ...]
    group_members: tuple[str, ...]

    def __post_init__(self):
        if (
            self.schema != SCHEMA
            or type(self.source_commit) is not str
            or COMMIT.fullmatch(self.source_commit) is None
            or type(self.case_id) is not str
            or type(self.topology_sha256) is not str
            or type(self.inventory_sha256) is not str
            or any(
                len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value)
                for value in (self.topology_sha256, self.inventory_sha256)
            )
            or type(self.kkt_order) is not int
            or self.kkt_order <= 0
            or type(self.resource_limits) is not tuple
            or any(
                type(item) is not tuple
                or len(item) != 2
                or type(item[0]) is not str
                or type(item[1]) is not int
                or item[1] <= 0
                for item in self.resource_limits
            )
            or self.resource_limits != cases.resource_contract()
            or type(self.raw_archive_bytes) is not int
            or self.raw_archive_bytes != cases.ARCHIVE_BYTES
            or type(self.inverse_blocks) is not tuple
            or type(self.group_members) is not tuple
            or self.group_members != GROUP_MEMBERS
        ):
            raise ValueError("invalid F03 case archive plan")
        cursor = 0
        names = []
        for block in self.inverse_blocks:
            if type(block) is not InverseBlock or block.start != cursor or block.rows != self.kkt_order:
                raise ValueError("noncontiguous F03 inverse-block plan")
            cursor += block.columns
            names.append(block.name)
        if cursor != self.kkt_order or len(names) != len(set(names)):
            raise ValueError("incomplete F03 inverse-block plan")
        if sum(block.bytes for block in self.inverse_blocks) != 8 * self.kkt_order**2:
            raise ValueError("invalid F03 inverse evidence size")

    @property
    def members(self) -> tuple[str, ...]:
        return self.group_members + tuple(block.name for block in self.inverse_blocks)


def make_case_plan(
    record: cases.CasePreflight,
    records: tuple[cases.CasePreflight, ...],
    source_commit: str,
) -> CaseArchivePlan:
    if type(record) is not cases.CasePreflight or record not in records:
        raise ValueError("admitted F03 preflight record required")
    inventory = cases.inventory_sha256(records)
    order = record.case.kkt_order
    blocks = tuple(
        InverseBlock(start, min(BLOCK_COLUMNS, order - start), order,
                     8 * order * min(BLOCK_COLUMNS, order - start))
        for start in range(0, order, BLOCK_COLUMNS)
    )
    return CaseArchivePlan(
        SCHEMA,
        source_commit,
        record.case.case_id,
        record.topology_sha256,
        inventory,
        order,
        cases.resource_contract(),
        cases.ARCHIVE_BYTES,
        blocks,
        GROUP_MEMBERS,
    )


def _payload(plan: CaseArchivePlan) -> bytes:
    if type(plan) is not CaseArchivePlan:
        raise ValueError("validated F03 case archive plan required")
    value = {
        "schema": plan.schema,
        "source_commit": plan.source_commit,
        "case_id": plan.case_id,
        "topology_sha256": plan.topology_sha256,
        "inventory_sha256": plan.inventory_sha256,
        "kkt_order": plan.kkt_order,
        "resource_limits": {name: value for name, value in plan.resource_limits},
        "raw_archive_bytes": plan.raw_archive_bytes,
        "group_members": list(plan.group_members),
        "inverse_blocks": [
            {"start": block.start, "columns": block.columns, "rows": block.rows,
             "bytes": block.bytes, "name": block.name}
            for block in plan.inverse_blocks
        ],
    }
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")


def write_plan(path: Path, plan: CaseArchivePlan) -> None:
    path = Path(path)
    payload = _payload(plan)
    digest = hashlib.sha256(payload).hexdigest().encode("ascii") + b"\n"
    if len(payload) + len(digest) > MAX_PLAN_BYTES:
        raise ValueError("F03 archive plan exceeds declared bound")
    with path.open("xb") as raw:
        with zipfile.ZipFile(raw, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("plan.json", payload)
            archive.writestr("plan.sha256", digest)


def _decode(payload: bytes) -> CaseArchivePlan:
    if type(payload) is not bytes or len(payload) > MAX_PLAN_BYTES:
        raise ValueError("invalid bounded F03 archive plan payload")
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid F03 archive plan JSON") from exc
    if set(value) != {
        "schema", "source_commit", "case_id", "topology_sha256", "inventory_sha256",
        "kkt_order", "resource_limits", "raw_archive_bytes", "group_members", "inverse_blocks",
    } or type(value["inverse_blocks"]) is not list or type(value["resource_limits"]) is not dict:
        raise ValueError("invalid F03 archive plan inventory")
    if set(value["resource_limits"]) != {name for name, _ in cases.resource_contract()}:
        raise ValueError("invalid F03 archive resource inventory")
    resource_limits = tuple(
        (name, value["resource_limits"][name]) for name, _ in cases.resource_contract()
    )
    blocks = []
    for item in value["inverse_blocks"]:
        if type(item) is not dict or set(item) != {"start", "columns", "rows", "bytes", "name"}:
            raise ValueError("invalid F03 inverse-block inventory")
        block = InverseBlock(item["start"], item["columns"], item["rows"], item["bytes"])
        if item["name"] != block.name:
            raise ValueError("stale F03 inverse-block name")
        blocks.append(block)
    return CaseArchivePlan(
        value["schema"], value["source_commit"], value["case_id"],
        value["topology_sha256"], value["inventory_sha256"], value["kkt_order"],
        resource_limits, value["raw_archive_bytes"], tuple(blocks), tuple(value["group_members"]),
    )


def read_plan(
    path: Path,
    record: cases.CasePreflight,
    records: tuple[cases.CasePreflight, ...],
    source_commit: str,
) -> CaseArchivePlan:
    path = Path(path)
    if path.stat().st_size > MAX_PLAN_BYTES:
        raise ValueError("F03 archive plan exceeds declared bound")
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if (
            len(infos) != 2
            or [item.filename for item in infos] != ["plan.json", "plan.sha256"]
            or sum(item.file_size for item in infos) > MAX_PLAN_BYTES
            or any(item.compress_size < 0 or item.file_size < 0 for item in infos)
        ):
            raise ValueError("invalid F03 archive plan ZIP inventory")
        payload = archive.read("plan.json")
        stated = archive.read("plan.sha256")
    actual = hashlib.sha256(payload).hexdigest().encode("ascii") + b"\n"
    if not hmac.compare_digest(stated, actual):
        raise ValueError("F03 archive plan digest mismatch")
    plan = _decode(payload)
    expected = make_case_plan(record, records, source_commit)
    if plan != expected:
        raise ValueError("stale or mismatched F03 archive plan")
    return plan
