"""Exclusive start and terminal receipts for the F03 local scientific cases.

Receipts record lifecycle only.  They neither authorize a run nor interpret
mechanical or numerical evidence.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
import re

from scripts import _b3_e4_f03_local_scientific_archive as archive
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
    if path.stat().st_size > MAX_RECEIPT_BYTES:
        raise ValueError("F03 lifecycle receipt exceeds declared bound")
    payload = path.read_bytes()
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
    "start_sha256", "reason", "exit_code", "elapsed_seconds",
    "sampled_peak_tree_rss_bytes", "observed_pids", "terminated_pids", "failure",
}


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
    """Create the child's marker before model construction or allocation."""
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
        _, start_digest = read_start(directory, plan, registration_sha256)
    elif receipt.reason != "launch_failure":
        # A launched child that did not emit its first marker is preserved as
        # a terminal execution failure; absence is explicit in the receipt.
        start_digest = None
    value = {
        "schema": TERMINAL_SCHEMA,
        "case_id": plan.case_id,
        "source_commit": plan.source_commit,
        "registration_sha256": registration_sha256,
        "plan_sha256": plan_sha256(plan),
        "start_sha256": start_digest,
        "reason": receipt.reason,
        "exit_code": receipt.exit_code,
        "elapsed_seconds": float(receipt.elapsed_seconds),
        "sampled_peak_tree_rss_bytes": receipt.sampled_peak_tree_rss_bytes,
        "observed_pids": list(receipt.observed_pids),
        "terminated_pids": list(receipt.terminated_pids),
        "failure": receipt.failure,
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
    try:
        receipt = supervisor.SupervisionReceipt(
            value["reason"], value["exit_code"], value["elapsed_seconds"],
            value["sampled_peak_tree_rss_bytes"], tuple(value["observed_pids"]),
            tuple(value["terminated_pids"]), value["failure"],
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid F03 terminal supervision payload") from exc
    start_path = Path(directory) / "start.json"
    if start_path.exists():
        _, start_digest = read_start(directory, plan, registration_sha256)
        if not isinstance(value["start_sha256"], str) or not hmac.compare_digest(
            value["start_sha256"], start_digest
        ):
            raise ValueError("F03 terminal receipt did not consume its start marker")
    elif value["start_sha256"] is not None:
        raise ValueError("F03 terminal receipt cites a missing start marker")
    return value, digest
