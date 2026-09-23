"""Exclusive start and terminal receipts for the F03 local scientific cases.

Receipts record lifecycle only.  They neither authorize a run nor interpret
mechanical or numerical evidence.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat

from scripts import _b3_e4_f03_local_scientific_archive as archive
from scripts import _b3_e4_f03_local_scientific_cases as cases
from scripts import _b3_e4_f03_local_scientific_evidence_index as evidence_index
from scripts import _b3_e4_f03_local_scientific_supervisor as supervisor


START_SCHEMA = "f03_local_scientific_start_v1"
TERMINAL_SCHEMA = "f03_local_scientific_terminal_v1"
DIGEST = re.compile(r"[0-9a-f]{64}")
MAX_RECEIPT_BYTES = 64 * 1024


def _canonical(value: object) -> bytes:
    try:
        payload = (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
                   + "\n").encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise ValueError("invalid bounded F03 lifecycle receipt") from exc
    if len(payload) > MAX_RECEIPT_BYTES:
        raise ValueError("F03 lifecycle receipt exceeds declared bound")
    return payload


def _write_new(path: Path, value: object) -> str:
    payload = _canonical(value)
    digest = hashlib.sha256(payload).hexdigest()
    with Path(path).open("xb") as stream:
        stream.write(payload)
    return digest


def _read_exact(path: Path, keys: set[str]) -> tuple[dict, str]:
    path = Path(path)
    with path.open("rb") as stream:
        payload = stream.read(MAX_RECEIPT_BYTES + 1)
    if len(payload) > MAX_RECEIPT_BYTES:
        raise ValueError("F03 lifecycle receipt exceeds declared bound")
    try:
        value = json.loads(payload.decode("ascii"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid F03 lifecycle receipt JSON") from exc
    if type(value) is not dict or set(value) != keys or _canonical(value) != payload:
        raise ValueError("invalid F03 lifecycle receipt inventory or encoding")
    return value, hashlib.sha256(payload).hexdigest()


START_KEYS = {
    "schema", "case_id", "source_commit", "registration_sha256", "plan_sha256",
    "inventory_sha256", "topology_sha256", "pid",
}
TERMINAL_KEYS = {
    "schema", "case_id", "source_commit", "registration_sha256", "plan_sha256",
    "start_sha256", "reason", "exit_code", "root_pid", "elapsed_seconds",
    "sampled_peak_tree_rss_bytes", "observed_pids", "terminated_pids", "failure",
    "stdout_log_bytes", "stdout_log_sha256", "stderr_log_bytes", "stderr_log_sha256",
}


def _log_identity(directory: Path, name: str) -> tuple[int, str]:
    path = Path(directory) / name
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or evidence_index._is_reparse(info)
            or info.st_nlink != 1 or info.st_size > cases.LOG_BYTES_PER_STREAM):
        raise ValueError(f"invalid bounded F03 {name} file")
    digest = hashlib.sha256()
    with evidence_index._open_no_follow(path) as stream:
        opened = os.fstat(stream.fileno())
        if not evidence_index._same_file(opened, evidence_index._FileIdentity(
            name, info.st_size, info.st_dev, info.st_ino, info.st_mtime_ns, info.st_ctime_ns,
        )):
            raise ValueError(f"changed F03 {name} file")
        count = 0
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            count += len(block)
            if count > cases.LOG_BYTES_PER_STREAM:
                raise ValueError(f"F03 {name} exceeds byte cap")
            digest.update(block)
        if count != info.st_size or os.fstat(stream.fileno()).st_size != info.st_size:
            raise ValueError(f"changed F03 {name} file")
    after = path.lstat()
    if (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) != (
        info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
    ):
        raise ValueError(f"changed F03 {name} file")
    return count, digest.hexdigest()


def plan_sha256(plan: archive.CaseArchivePlan) -> str:
    if type(plan) is not archive.CaseArchivePlan:
        raise ValueError("validated F03 archive plan required")
    return hashlib.sha256(archive._payload(plan)).hexdigest()


def write_start(
    directory: Path,
    plan: archive.CaseArchivePlan,
    registration_sha256: str,
    pid: int,
) -> str:
    """Create the child marker after envelope validation and before model work."""
    directory = Path(directory)
    if (
        not directory.is_dir()
        or type(plan) is not archive.CaseArchivePlan
        or DIGEST.fullmatch(registration_sha256) is None
        or type(pid) is not int
        or pid <= 0
        or (directory / "terminal.json").exists()
    ):
        raise ValueError("validated F03 start-marker inputs required")
    value = {
        "schema": START_SCHEMA,
        "case_id": plan.case_id,
        "source_commit": plan.source_commit,
        "registration_sha256": registration_sha256,
        "plan_sha256": plan_sha256(plan),
        "inventory_sha256": plan.inventory_sha256,
        "topology_sha256": plan.topology_sha256,
        "pid": pid,
    }
    return _write_new(directory / "start.json", value)


def read_start(
    directory: Path,
    plan: archive.CaseArchivePlan,
    registration_sha256: str,
) -> tuple[dict, str]:
    if type(plan) is not archive.CaseArchivePlan or DIGEST.fullmatch(registration_sha256) is None:
        raise ValueError("validated F03 start-marker identity required")
    value, digest = _read_exact(Path(directory) / "start.json", START_KEYS)
    expected = {
        "schema": START_SCHEMA,
        "case_id": plan.case_id,
        "source_commit": plan.source_commit,
        "registration_sha256": registration_sha256,
        "plan_sha256": plan_sha256(plan),
        "inventory_sha256": plan.inventory_sha256,
        "topology_sha256": plan.topology_sha256,
    }
    if (
        any(value[name] != expected[name] for name in expected)
        or type(value["pid"]) is not int
        or value["pid"] <= 0
    ):
        raise ValueError("stale or invalid F03 start marker")
    return value, digest


def write_terminal(
    directory: Path,
    plan: archive.CaseArchivePlan,
    registration_sha256: str,
    receipt: supervisor.SupervisionReceipt,
) -> str:
    directory = Path(directory)
    if (
        not directory.is_dir()
        or type(plan) is not archive.CaseArchivePlan
        or DIGEST.fullmatch(registration_sha256) is None
        or type(receipt) is not supervisor.SupervisionReceipt
    ):
        raise ValueError("validated F03 terminal-receipt inputs required")
    start_path = directory / "start.json"
    start_digest = None
    if start_path.exists():
        start, start_digest = read_start(directory, plan, registration_sha256)
        if receipt.root_pid != start["pid"]:
            raise ValueError("F03 terminal process does not own its start marker")
    elif receipt.reason != "launch_failure":
        # A launched child that did not emit its first marker is preserved as
        # a terminal execution failure; absence is explicit in the receipt.
        start_digest = None
    stdout_count, stdout_digest = _log_identity(directory, "stdout.log")
    stderr_count, stderr_digest = _log_identity(directory, "stderr.log")
    value = {
        "schema": TERMINAL_SCHEMA,
        "case_id": plan.case_id,
        "source_commit": plan.source_commit,
        "registration_sha256": registration_sha256,
        "plan_sha256": plan_sha256(plan),
        "start_sha256": start_digest,
        "reason": receipt.reason,
        "exit_code": receipt.exit_code,
        "root_pid": receipt.root_pid,
        "elapsed_seconds": float(receipt.elapsed_seconds),
        "sampled_peak_tree_rss_bytes": receipt.sampled_peak_tree_rss_bytes,
        "observed_pids": list(receipt.observed_pids),
        "terminated_pids": list(receipt.terminated_pids),
        "failure": receipt.failure,
        "stdout_log_bytes": stdout_count,
        "stdout_log_sha256": stdout_digest,
        "stderr_log_bytes": stderr_count,
        "stderr_log_sha256": stderr_digest,
    }
    return _write_new(directory / "terminal.json", value)


def read_terminal(
    directory: Path,
    plan: archive.CaseArchivePlan,
    registration_sha256: str,
) -> tuple[dict, str]:
    if type(plan) is not archive.CaseArchivePlan or DIGEST.fullmatch(registration_sha256) is None:
        raise ValueError("validated F03 terminal-receipt identity required")
    value, digest = _read_exact(Path(directory) / "terminal.json", TERMINAL_KEYS)
    expected = {
        "schema": TERMINAL_SCHEMA,
        "case_id": plan.case_id,
        "source_commit": plan.source_commit,
        "registration_sha256": registration_sha256,
        "plan_sha256": plan_sha256(plan),
    }
    if any(value[name] != expected[name] for name in expected):
        raise ValueError("stale F03 terminal receipt")
    for name in ("stdout", "stderr"):
        count, observed = _log_identity(directory, f"{name}.log")
        if (value[f"{name}_log_bytes"] != count
                or type(value[f"{name}_log_sha256"]) is not str
                or not hmac.compare_digest(value[f"{name}_log_sha256"], observed)):
            raise ValueError(f"F03 terminal {name} log identity changed")
    try:
        receipt = supervisor.SupervisionReceipt(
            value["reason"], value["exit_code"], value["root_pid"], value["elapsed_seconds"],
            value["sampled_peak_tree_rss_bytes"], tuple(value["observed_pids"]),
            tuple(value["terminated_pids"]), value["failure"],
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid F03 terminal supervision payload") from exc
    start_path = Path(directory) / "start.json"
    if start_path.exists():
        start, start_digest = read_start(directory, plan, registration_sha256)
        if not isinstance(value["start_sha256"], str) or not hmac.compare_digest(
            value["start_sha256"], start_digest
        ):
            raise ValueError("F03 terminal receipt did not consume its start marker")
        if receipt.root_pid != start["pid"]:
            raise ValueError("F03 terminal process does not own its start marker")
    elif value["start_sha256"] is not None:
        raise ValueError("F03 terminal receipt cites a missing start marker")
    return value, digest
