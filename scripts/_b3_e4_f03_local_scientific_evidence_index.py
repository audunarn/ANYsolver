"""Canonical byte identity for one complete F03 case-evidence inventory.

The index binds already-written evidence members to the immutable case plan and
start marker.  It does not parse numerical evidence, assemble, factor, solve,
or decide a scientific result.
"""
from __future__ import annotations

from contextlib import ExitStack, contextmanager
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


def _same_directory(info: os.stat_result, retained: os.stat_result) -> bool:
    return (
        stat.S_ISDIR(info.st_mode)
        and stat.S_ISDIR(retained.st_mode)
        and not _is_reparse(info)
        and not _is_reparse(retained)
        and info.st_dev == retained.st_dev
        and info.st_ino == retained.st_ino
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


def _allowed_directories(
    names: tuple[str, ...], infrastructure: frozenset[str],
) -> frozenset[str]:
    result = set()
    for name in (*names, *infrastructure):
        parts = PurePosixPath(name).parts[:-1]
        for count in range(1, len(parts) + 1):
            result.add(PurePosixPath(*parts[:count]).as_posix())
    return frozenset(result)


def _tree(
    directory: Path, names: tuple[str, ...], infrastructure: frozenset[str] = INFRASTRUCTURE,
) -> dict[str, _FileIdentity]:
    root_info = os.lstat(directory)
    if not stat.S_ISDIR(root_info.st_mode) or _is_reparse(root_info):
        raise ValueError("ordinary F03 evidence directory required")
    if type(infrastructure) is not frozenset or any(type(name) is not str for name in infrastructure):
        raise ValueError("exact F03 infrastructure inventory required")
    allowed_files = set(names) | set(infrastructure)
    allowed_directories = _allowed_directories(names, infrastructure)
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
    infrastructure: frozenset[str] = INFRASTRUCTURE,
) -> tuple[_FileIdentity, ...]:
    if type(max_total_bytes) is not int or max_total_bytes <= 0:
        raise ValueError("positive F03 evidence byte limit required")
    observed = _tree(directory, names, infrastructure)
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


def _identities_from_observed(
    observed: dict[str, _FileIdentity], names: tuple[str, ...], max_total_bytes: int,
) -> tuple[_FileIdentity, ...]:
    if type(max_total_bytes) is not int or max_total_bytes <= 0:
        raise ValueError("positive F03 evidence byte limit required")
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


def _open_relative_no_follow(descriptor: int, name: str):
    if os.name == "nt" or type(name) is not str or not name or "/" in name or "\\" in name:
        raise ValueError("valid POSIX F03 evidence member name required")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    return os.fdopen(os.open(name, flags, dir_fd=descriptor), "rb")


@contextmanager
def _open_directory_no_follow(path: Path):
    path = Path(path)
    if os.name != "nt":
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags)
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISDIR(info.st_mode):
                raise ValueError("ordinary F03 evidence directory required")
            yield descriptor
        finally:
            os.close(descriptor)
        return
    import msvcrt
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel32.CreateFileW
    create.argtypes = (
        ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
    )
    create.restype = ctypes.c_void_p
    handle = create(
        str(path), 0, 0x00000001, None, 3,
        0x00200000 | 0x02000000, None,
    )
    invalid = ctypes.c_void_p(-1).value
    if handle == invalid:
        error = ctypes.get_last_error()
        raise OSError(error, os.strerror(error), str(path))
    try:
        descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | getattr(os, "O_BINARY", 0))
    except BaseException:
        kernel32.CloseHandle(ctypes.c_void_p(handle))
        raise
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISDIR(info.st_mode) or _is_reparse(info):
            raise ValueError("ordinary F03 evidence directory required")
        yield descriptor
    finally:
        os.close(descriptor)


@contextmanager
def _open_directory_relative(descriptor: int, name: str):
    if os.name == "nt" or type(name) is not str or not name or "/" in name or "\\" in name:
        raise ValueError("valid POSIX F03 evidence directory name required")
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
    child = os.open(name, flags, dir_fd=descriptor)
    try:
        info = os.fstat(child)
        if not stat.S_ISDIR(info.st_mode) or _is_reparse(info):
            raise ValueError("ordinary F03 evidence directory required")
        yield child
    finally:
        os.close(child)


def _tree_from_open_directories(
    directory: Path,
    names: tuple[str, ...],
    infrastructure: frozenset[str],
    directories: dict[str, tuple[Path, int]],
) -> dict[str, _FileIdentity]:
    if os.name == "nt":
        return _tree(directory, names, infrastructure)
    allowed_files = set(names) | set(infrastructure)
    allowed_directories = _allowed_directories(names, infrastructure)
    result = {}

    def visit(relative: PurePosixPath) -> None:
        key = relative.as_posix() if relative.parts else ""
        descriptor = directories[key][1]
        for entry_name in os.listdir(descriptor):
            info = os.stat(entry_name, dir_fd=descriptor, follow_symlinks=False)
            name = (relative / entry_name).as_posix()
            if stat.S_ISLNK(info.st_mode) or _is_reparse(info):
                raise ValueError(f"linked or reparse F03 evidence path: {name}")
            if stat.S_ISDIR(info.st_mode):
                if name not in allowed_directories or name not in directories:
                    raise ValueError(f"extra F03 evidence directory: {name}")
                child_info = os.fstat(directories[name][1])
                if not _same_directory(info, child_info):
                    raise ValueError(f"changed F03 evidence directory: {name}")
                visit(relative / entry_name)
            elif stat.S_ISREG(info.st_mode):
                if name not in allowed_files or name in result:
                    raise ValueError(f"extra or duplicate F03 evidence file: {name}")
                with _open_relative_no_follow(descriptor, entry_name) as stream:
                    handle_info = os.fstat(stream.fileno())
                if (
                    not stat.S_ISREG(handle_info.st_mode)
                    or _is_reparse(handle_info)
                    or handle_info.st_dev != info.st_dev
                    or handle_info.st_ino != info.st_ino
                ):
                    raise ValueError(f"changed F03 evidence member: {name}")
                result[name] = _FileIdentity(
                    name, handle_info.st_size, handle_info.st_dev, handle_info.st_ino,
                    handle_info.st_mtime_ns, handle_info.st_ctime_ns,
                )
            else:
                raise ValueError(f"unsupported F03 evidence file type: {name}")

    visit(PurePosixPath())
    return result


def _open_snapshot_member(
    directory: Path,
    identity: _FileIdentity,
    directories: dict[str, tuple[Path, int]],
):
    if os.name == "nt":
        return _open_no_follow(_path(directory, identity.name))
    parts = PurePosixPath(identity.name).parts
    parent = PurePosixPath(*parts[:-1]).as_posix() if len(parts) > 1 else ""
    return _open_relative_no_follow(directories[parent][1], parts[-1])


def _stable_directory(first: os.stat_result, second: os.stat_result) -> bool:
    return (
        _same_directory(first, second)
        and first.st_mtime_ns == second.st_mtime_ns
        and first.st_ctime_ns == second.st_ctime_ns
        and first.st_nlink == second.st_nlink
    )


def _hash_open(stream, identity: _FileIdentity) -> str:
    if not _same_file(os.fstat(stream.fileno()), identity):
        raise ValueError("F03 evidence member changed before hashing")
    stream.seek(0)
    digest = hashlib.sha256()
    observed = 0
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
    return digest.hexdigest()


@contextmanager
def _snapshot(
    directory: Path, names: tuple[str, ...], max_total_bytes: int,
    infrastructure: frozenset[str] = INFRASTRUCTURE,
):
    directory = Path(directory)
    with ExitStack() as stack:
        root_descriptor = stack.enter_context(_open_directory_no_follow(directory))
        directories = {"": (directory, root_descriptor)}
        allowed_directories = sorted(
            _allowed_directories(names, infrastructure),
            key=lambda value: (len(PurePosixPath(value).parts), value),
        )
        for name in allowed_directories:
            path = directory.joinpath(*PurePosixPath(name).parts)
            parts = PurePosixPath(name).parts
            parent = PurePosixPath(*parts[:-1]).as_posix() if len(parts) > 1 else ""
            if parent not in directories:
                continue
            try:
                if os.name == "nt":
                    if not path.exists():
                        continue
                    descriptor = stack.enter_context(_open_directory_no_follow(path))
                else:
                    descriptor = stack.enter_context(
                        _open_directory_relative(directories[parent][1], parts[-1])
                    )
            except FileNotFoundError:
                continue
            except OSError as exc:
                raise ValueError(f"invalid F03 evidence directory: {name}") from exc
            directories[name] = (path, descriptor)
        observed = _tree_from_open_directories(directory, names, infrastructure, directories)
        identities = _identities_from_observed(observed, names, max_total_bytes)
        streams = tuple(
            stack.enter_context(_open_snapshot_member(directory, identity, directories))
            for identity in identities
        )
        for stream, identity in zip(streams, identities):
            if not _same_file(os.fstat(stream.fileno()), identity):
                raise ValueError("F03 evidence inventory changed before snapshot")
        try:
            yield identities, streams
        except BaseException:
            raise
        else:
            for stream, identity in zip(streams, identities):
                if not _same_file(os.fstat(stream.fileno()), identity):
                    raise ValueError("F03 evidence inventory changed during snapshot")
            before = {name: os.fstat(item[1]) for name, item in directories.items()}
            observed = _tree_from_open_directories(
                directory, names, infrastructure, directories,
            )
            after = {name: os.fstat(item[1]) for name, item in directories.items()}
            for name, (path, descriptor) in directories.items():
                current = os.stat(path, follow_symlinks=False)
                if (
                    not _stable_directory(before[name], after[name])
                    or not _same_directory(current, after[name])
                ):
                    raise ValueError("F03 evidence directory changed during snapshot")
            for identity in identities:
                if observed.get(identity.name) != identity:
                    raise ValueError("F03 evidence inventory changed after snapshot")


def _hash_member(path: Path, identity: _FileIdentity) -> str:
    with _open_no_follow(path) as stream:
        digest = _hash_open(stream, identity)
    with _open_no_follow(path) as stream:
        if not _same_file(os.fstat(stream.fileno()), identity):
            raise ValueError("F03 evidence member changed after hashing")
    return digest


def _plan_sha256(plan: archive.CaseArchivePlan) -> str:
    return hashlib.sha256(archive._payload(plan)).hexdigest()


def _index_from_snapshot(
    plan: archive.CaseArchivePlan,
    registration_sha256: str,
    start_sha256: str,
    identities: tuple[_FileIdentity, ...],
    streams: tuple,
) -> EvidenceIndex:
    names = expected_members(plan)
    if tuple(item.name for item in identities) != names or len(streams) != len(names):
        raise ValueError("invalid complete F03 evidence snapshot")
    members = tuple(
        EvidenceMember(
            name, _kind(name), identity.bytes, _hash_open(stream, identity),
        )
        for name, identity, stream in zip(names, identities, streams)
    )
    return EvidenceIndex(
        SCHEMA, plan.case_id, plan.source_commit, registration_sha256,
        _plan_sha256(plan), start_sha256, plan.inventory_sha256, plan.topology_sha256,
        sum(item.bytes for item in identities), members,
    )


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
    with _snapshot(directory, names, evidence_limit) as (identities, streams):
        return _index_from_snapshot(
            plan, registration_sha256, start_sha256, identities, streams,
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
    if not _digest(registration_sha256) or not _digest(start_sha256):
        raise ValueError("exact F03 registration and start identities required")
    directory = Path(directory)
    names = expected_members(plan)
    evidence_limit = plan.raw_archive_bytes - MAX_INDEX_BYTES - MAX_CASE_RECEIPT_BYTES
    with _snapshot(directory, names, evidence_limit) as (identities, streams):
        index = _index_from_snapshot(
            plan, registration_sha256, start_sha256, identities, streams,
        )
        payload = _payload(index)
        with (directory / "evidence_index.json").open("xb") as output:
            output.write(payload)
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
    directory = Path(directory)
    path = directory / "evidence_index.json"
    names = expected_members(plan)
    evidence_limit = plan.raw_archive_bytes - MAX_INDEX_BYTES - MAX_CASE_RECEIPT_BYTES
    with _open_directory_no_follow(directory):
        tree = _tree(directory, names)
        identity = tree.get("evidence_index.json")
        if identity is None or identity.bytes > MAX_INDEX_BYTES:
            raise ValueError("F03 evidence index exceeds declared bound")
        with _open_no_follow(path) as index_stream:
            if not _same_file(os.fstat(index_stream.fileno()), identity):
                raise ValueError("F03 evidence index changed before reading")
            payload = index_stream.read(MAX_INDEX_BYTES + 1)
            if len(payload) != identity.bytes or len(payload) > MAX_INDEX_BYTES:
                raise ValueError("F03 evidence index exceeds declared bound")
            index = _decode(payload)
            with _snapshot(directory, names, evidence_limit) as (identities, streams):
                expected = _index_from_snapshot(
                    plan, registration_sha256, start_sha256, identities, streams,
                )
                if _payload(index) != _payload(expected):
                    raise ValueError("stale or mismatched F03 evidence index")
                if not _same_file(os.fstat(index_stream.fileno()), identity):
                    raise ValueError("F03 evidence index changed during verification")
                with _open_no_follow(path) as final_index:
                    if not _same_file(os.fstat(final_index.fileno()), identity):
                        raise ValueError("F03 evidence index changed after verification")
    return index, hashlib.sha256(payload).hexdigest()
