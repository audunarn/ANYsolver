"""Canonical byte identity for one complete F03 case-evidence inventory.

The index binds already-written evidence members to the immutable case plan and
start marker.  It does not parse numerical evidence, assemble, factor, solve,
or decide a scientific result.
"""
from __future__ import annotations

from dataclasses import dataclass
import ctypes
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat

from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_cases as cases


SCHEMA = "f03_local_scientific_evidence_index_v1"
MAX_INDEX_BYTES = cases.EVIDENCE_INDEX_BYTES
MAX_CASE_RECEIPT_BYTES = cases.CASE_RECEIPT_BYTES
CHUNK_BYTES = 1024 * 1024
DIGEST = frozenset("0123456789abcdef")
EXCLUDED = frozenset(("evidence_index.json", "case_receipt.json"))
INFRASTRUCTURE = frozenset(
    ("start.json", "terminal.json", "plan.zip", "evidence_index.json", "case_receipt.json")
)


def _digest(value: object) -> bool:
    return type(value) is str and len(value) == 64 and set(value) <= DIGEST


def _kind(name: str) -> str:
    suffix = PurePosixPath(name).suffix
    result = {".npz": "npz", ".npy": "npy", ".json": "json"}.get(suffix)
    if result is None:
        raise ValueError("unsupported F03 evidence member type")
    return result


@dataclass(frozen=True, slots=True)
class EvidenceMember:
    name: str
    kind: str
    bytes: int
    sha256: str

    def __post_init__(self):
        if (
            type(self.name) is not str
            or self.kind != _kind(self.name)
            or type(self.bytes) is not int
            or self.bytes <= 0
            or not _digest(self.sha256)
        ):
            raise ValueError("invalid F03 evidence member identity")


@dataclass(frozen=True, slots=True)
class EvidenceIndex:
    schema: str
    case_id: str
    source_commit: str
    registration_sha256: str
    plan_sha256: str
    start_sha256: str
    inventory_sha256: str
    topology_sha256: str
    total_bytes: int
    members: tuple[EvidenceMember, ...]

    def __post_init__(self):
        if (
            self.schema != SCHEMA
            or type(self.case_id) is not str
            or type(self.source_commit) is not str
            or len(self.source_commit) != 40
            or set(self.source_commit) - DIGEST
            or any(
                not _digest(value)
                for value in (
                    self.registration_sha256,
                    self.plan_sha256,
                    self.start_sha256,
                    self.inventory_sha256,
                    self.topology_sha256,
                )
            )
            or type(self.total_bytes) is not int
            or self.total_bytes <= 0
            or type(self.members) is not tuple
            or not self.members
            or any(type(item) is not EvidenceMember for item in self.members)
            or len({item.name for item in self.members}) != len(self.members)
            or self.total_bytes != sum(item.bytes for item in self.members)
        ):
            raise ValueError("invalid F03 evidence index")


@dataclass(frozen=True, slots=True)
class _FileIdentity:
    name: str
    bytes: int
    device: int
    inode: int
    modified_ns: int
    changed_ns: int


def _is_reparse(info: os.stat_result) -> bool:
    mask = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(getattr(info, "st_file_attributes", 0) & mask)


def _same_file(info: os.stat_result, identity: _FileIdentity) -> bool:
    return (
        stat.S_ISREG(info.st_mode)
        and not _is_reparse(info)
        and info.st_size == identity.bytes
        and info.st_dev == identity.device
        and info.st_ino == identity.inode
        and info.st_mtime_ns == identity.modified_ns
        and info.st_ctime_ns == identity.changed_ns
    )


def expected_members(plan: archive.CaseArchivePlan) -> tuple[str, ...]:
    if type(plan) is not archive.CaseArchivePlan:
        raise ValueError("validated F03 archive plan required")
    names = tuple(name for name in plan.members if name not in EXCLUDED)
    if (
        not names
        or any(name in EXCLUDED for name in names)
        or len(names) != len(set(names))
    ):
        raise ValueError("invalid F03 evidence member plan")
    tuple(_kind(name) for name in names)
    return names


def _path(directory: Path, name: str) -> Path:
    parts = PurePosixPath(name).parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        raise ValueError("invalid F03 evidence member path")
    return directory.joinpath(*parts)


def _allowed_directories(names: tuple[str, ...]) -> frozenset[str]:
    result = set()
    for name in (*names, *INFRASTRUCTURE):
        parts = PurePosixPath(name).parts[:-1]
        for count in range(1, len(parts) + 1):
            result.add(PurePosixPath(*parts[:count]).as_posix())
    return frozenset(result)


def _tree(
    directory: Path, names: tuple[str, ...],
) -> dict[str, _FileIdentity]:
    root_info = os.lstat(directory)
    if not stat.S_ISDIR(root_info.st_mode) or _is_reparse(root_info):
        raise ValueError("ordinary F03 evidence directory required")
    allowed_files = set(names) | set(INFRASTRUCTURE)
    allowed_directories = _allowed_directories(names)
    result = {}

    def visit(current: Path, relative: PurePosixPath) -> None:
        with os.scandir(current) as entries:
            for entry in entries:
                info = entry.stat(follow_symlinks=False)
                name = (relative / entry.name).as_posix()
                if entry.is_symlink() or _is_reparse(info):
                    raise ValueError(f"linked or reparse F03 evidence path: {name}")
                if stat.S_ISDIR(info.st_mode):
                    if name not in allowed_directories:
                        raise ValueError(f"extra F03 evidence directory: {name}")
                    visit(Path(entry.path), relative / entry.name)
                elif stat.S_ISREG(info.st_mode):
                    if name not in allowed_files or name in result:
                        raise ValueError(f"extra or duplicate F03 evidence file: {name}")
                    with _open_no_follow(Path(entry.path)) as stream:
                        handle_info = os.fstat(stream.fileno())
                    if not stat.S_ISREG(handle_info.st_mode) or _is_reparse(handle_info):
                        raise ValueError(f"linked or reparse F03 evidence path: {name}")
                    result[name] = _FileIdentity(
                        name, handle_info.st_size, handle_info.st_dev, handle_info.st_ino,
                        handle_info.st_mtime_ns, handle_info.st_ctime_ns,
                    )
                else:
                    raise ValueError(f"unsupported F03 evidence file type: {name}")

    visit(directory, PurePosixPath())
    return result


def _preflight(
    directory: Path, names: tuple[str, ...], max_total_bytes: int,
) -> tuple[_FileIdentity, ...]:
    if type(max_total_bytes) is not int or max_total_bytes <= 0:
        raise ValueError("positive F03 evidence byte limit required")
    observed = _tree(directory, names)
    if any(name not in observed for name in names):
        raise ValueError("missing F03 evidence member file")
    identities = []
    total = 0
    for name in names:
        identity = observed[name]
        if identity.bytes <= 0:
            raise ValueError(f"invalid F03 evidence member file: {name}")
        total += identity.bytes
        if total > max_total_bytes:
            raise ValueError("F03 evidence inventory exceeds archive byte limit")
        identities.append(identity)
    return tuple(identities)


def _sizes(
    directory: Path, names: tuple[str, ...], max_total_bytes: int,
) -> tuple[int, ...]:
    return tuple(item.bytes for item in _preflight(directory, names, max_total_bytes))


def _open_no_follow(path: Path):
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    if os.name != "nt":
        return os.fdopen(os.open(path, flags), "rb")
    # OPEN_REPARSE_POINT prevents the final component from being followed.
    import msvcrt
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel32.CreateFileW
    create.argtypes = (
        ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
    )
    create.restype = ctypes.c_void_p
    handle = create(
        str(path), 0x80000000, 0x00000001, None, 3,
        0x00200000 | 0x08000000, None,
    )
    invalid = ctypes.c_void_p(-1).value
    if handle == invalid:
        error = ctypes.get_last_error()
        raise OSError(error, os.strerror(error), str(path))
    try:
        descriptor = msvcrt.open_osfhandle(handle, flags)
    except BaseException:
        kernel32.CloseHandle(ctypes.c_void_p(handle))
        raise
    return os.fdopen(descriptor, "rb")


def _hash_member(path: Path, identity: _FileIdentity) -> str:
    digest = hashlib.sha256()
    observed = 0
    with _open_no_follow(path) as stream:
        info = os.fstat(stream.fileno())
        if not _same_file(info, identity):
            raise ValueError("F03 evidence member changed before hashing")
        while observed < identity.bytes:
            block = stream.read(min(CHUNK_BYTES, identity.bytes - observed))
            if not block:
                raise ValueError("truncated F03 evidence member")
            observed += len(block)
            digest.update(block)
        if stream.read(1):
            raise ValueError("F03 evidence member grew while hashing")
        if not _same_file(os.fstat(stream.fileno()), identity):
            raise ValueError("F03 evidence member changed while hashing")
    with _open_no_follow(path) as stream:
        if not _same_file(os.fstat(stream.fileno()), identity):
            raise ValueError("F03 evidence member changed after hashing")
    return digest.hexdigest()


def _plan_sha256(plan: archive.CaseArchivePlan) -> str:
    return hashlib.sha256(archive._payload(plan)).hexdigest()


def make_index(
    directory: Path,
    plan: archive.CaseArchivePlan,
    registration_sha256: str,
    start_sha256: str,
) -> EvidenceIndex:
    if not _digest(registration_sha256) or not _digest(start_sha256):
        raise ValueError("exact F03 registration and start identities required")
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError("F03 evidence directory required")
    names = expected_members(plan)
    evidence_limit = plan.raw_archive_bytes - MAX_INDEX_BYTES - MAX_CASE_RECEIPT_BYTES
    identities = _preflight(directory, names, evidence_limit)
    members = tuple(
        EvidenceMember(
            name,
            _kind(name),
            identity.bytes,
            _hash_member(_path(directory, name), identity),
        )
        for name, identity in zip(names, identities)
    )
    return EvidenceIndex(
        SCHEMA,
        plan.case_id,
        plan.source_commit,
        registration_sha256,
        _plan_sha256(plan),
        start_sha256,
        plan.inventory_sha256,
        plan.topology_sha256,
        sum(item.bytes for item in identities),
        members,
    )


def _payload(index: EvidenceIndex) -> bytes:
    if type(index) is not EvidenceIndex:
        raise ValueError("validated F03 evidence index required")
    value = {
        "schema": index.schema,
        "case_id": index.case_id,
        "source_commit": index.source_commit,
        "registration_sha256": index.registration_sha256,
        "plan_sha256": index.plan_sha256,
        "start_sha256": index.start_sha256,
        "inventory_sha256": index.inventory_sha256,
        "topology_sha256": index.topology_sha256,
        "total_bytes": index.total_bytes,
        "members": [
            {
                "name": item.name,
                "kind": item.kind,
                "bytes": item.bytes,
                "sha256": item.sha256,
            }
            for item in index.members
        ],
    }
    payload = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "ascii"
    )
    if len(payload) > MAX_INDEX_BYTES:
        raise ValueError("F03 evidence index exceeds declared bound")
    return payload


def write_index(
    directory: Path,
    plan: archive.CaseArchivePlan,
    registration_sha256: str,
    start_sha256: str,
) -> tuple[EvidenceIndex, str]:
    index = make_index(directory, plan, registration_sha256, start_sha256)
    payload = _payload(index)
    with (Path(directory) / "evidence_index.json").open("xb") as stream:
        stream.write(payload)
    return index, hashlib.sha256(payload).hexdigest()


def _decode(payload: bytes) -> EvidenceIndex:
    if type(payload) is not bytes or len(payload) > MAX_INDEX_BYTES:
        raise ValueError("invalid bounded F03 evidence index payload")
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid F03 evidence index JSON") from exc
    keys = {
        "schema", "case_id", "source_commit", "registration_sha256", "plan_sha256",
        "start_sha256", "inventory_sha256", "topology_sha256", "total_bytes", "members",
    }
    if type(value) is not dict or set(value) != keys or type(value["members"]) is not list:
        raise ValueError("invalid F03 evidence index inventory")
    members = []
    for item in value["members"]:
        if type(item) is not dict or set(item) != {"name", "kind", "bytes", "sha256"}:
            raise ValueError("invalid F03 evidence member inventory")
        members.append(EvidenceMember(item["name"], item["kind"], item["bytes"], item["sha256"]))
    index = EvidenceIndex(
        value["schema"], value["case_id"], value["source_commit"],
        value["registration_sha256"], value["plan_sha256"], value["start_sha256"],
        value["inventory_sha256"], value["topology_sha256"], value["total_bytes"],
        tuple(members),
    )
    if _payload(index) != payload:
        raise ValueError("noncanonical F03 evidence index encoding")
    return index


def read_index(
    directory: Path,
    plan: archive.CaseArchivePlan,
    registration_sha256: str,
    start_sha256: str,
) -> tuple[EvidenceIndex, str]:
    path = Path(directory) / "evidence_index.json"
    tree = _tree(Path(directory), expected_members(plan))
    identity = tree.get("evidence_index.json")
    if identity is None or identity.bytes > MAX_INDEX_BYTES:
        raise ValueError("F03 evidence index exceeds declared bound")
    with _open_no_follow(path) as stream:
        if not _same_file(os.fstat(stream.fileno()), identity):
            raise ValueError("F03 evidence index changed before reading")
        payload = stream.read(MAX_INDEX_BYTES + 1)
        if not _same_file(os.fstat(stream.fileno()), identity):
            raise ValueError("F03 evidence index changed while reading")
    if len(payload) != identity.bytes or len(payload) > MAX_INDEX_BYTES:
        raise ValueError("F03 evidence index exceeds declared bound")
    with _open_no_follow(path) as stream:
        if not _same_file(os.fstat(stream.fileno()), identity):
            raise ValueError("F03 evidence index changed after reading")
    index = _decode(payload)
    expected = make_index(directory, plan, registration_sha256, start_sha256)
    if _payload(index) != _payload(expected):
        raise ValueError("stale or mismatched F03 evidence index")
    digest = hashlib.sha256(payload).hexdigest()
    return index, digest
