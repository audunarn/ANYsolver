"""Canonical transport and authority helpers for the bounded Q1W study."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1w-bounded-proof-contract-v1"
PROOF_SCHEMA = "anysolver.s4.e4-pl-q1w-proof-v1"
PROOF_WRAPPER_SCHEMA = "anysolver.s4.e4-pl-q1w-proof-wrapper-v1"
CHECK_SCHEMA = "anysolver.s4.e4-pl-q1w-proof-check-v1"
AGGREGATE_SCHEMA = "anysolver.s4.e4-pl-q1w-bounded-aggregate-v1"


class Q1WError(RuntimeError):
    """Fail-closed Q1W validation error."""


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def _pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in rows:
        if key in result:
            raise Q1WError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise Q1WError(f"non-finite JSON value: {value}")


def strict_json_bytes(raw: bytes, *, canonical: bool = True) -> Any:
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw:
        raise Q1WError("JSON must be UTF-8, LF-only, and BOM-free")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Q1WError("invalid strict JSON") from exc
    if canonical and raw != canonical_bytes(value):
        raise Q1WError("JSON is not canonical sorted compact UTF-8/LF")
    return value


def read_json(path: Path, *, canonical: bool = True) -> tuple[bytes, Any]:
    resolved = path.resolve(strict=True)
    if resolved.is_symlink() or not resolved.is_file():
        raise Q1WError(f"not a regular nonsymlink file: {path}")
    raw = resolved.read_bytes()
    return raw, strict_json_bytes(raw, canonical=canonical)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def verify_file(path: Path, *, size: int, digest: str) -> bytes:
    resolved = path.resolve(strict=True)
    if resolved.is_symlink() or not resolved.is_file():
        raise Q1WError(f"not a regular nonsymlink file: {path}")
    raw = resolved.read_bytes()
    if len(raw) != size or sha256(raw) != digest.upper():
        raise Q1WError(f"file identity mismatch: {path}")
    return raw


def validate_contract(
    repository_root: Path,
    contract_path: Path,
    contract_sha256: str,
) -> dict[str, Any]:
    root = repository_root.resolve(strict=True)
    raw, contract = read_json(contract_path)
    if sha256(raw) != contract_sha256.upper():
        raise Q1WError("proof contract caller hash mismatch")
    expected_keys = {
        "candidate_id",
        "checker",
        "exact_environment",
        "frozen_inputs",
        "historical_reference",
        "parallelism",
        "production",
        "q1b_execution",
        "schema",
        "shards",
        "study_id",
        "terminals",
    }
    if not isinstance(contract, dict) or set(contract) != expected_keys:
        raise Q1WError("proof contract exact-key schema mismatch")
    if contract["schema"] != CONTRACT_SCHEMA:
        raise Q1WError("proof contract schema mismatch")
    if contract["shards"] != ["Q0_SQUARE::R90", "Q0_SQUARE::R180", "Q0_SQUARE::R270"]:
        raise Q1WError("proof shard order mismatch")
    parallel = contract["parallelism"]
    if parallel != {
        "checker_workers": 6,
        "memory_limit_gib_per_producer": 24,
        "numerical_threads_per_process": 1,
        "producer_workers": 3,
        "timeout_seconds_per_process": 600,
    }:
        raise Q1WError("bounded parallel policy mismatch")
    rows = contract["frozen_inputs"]
    if not isinstance(rows, list) or len(rows) != 6:
        raise Q1WError("frozen input inventory mismatch")
    for row in rows:
        if set(row) != {"bytes", "path", "sha256"}:
            raise Q1WError("frozen input row schema mismatch")
        verify_file(root / row["path"], size=int(row["bytes"]), digest=str(row["sha256"]))
    environment = contract["exact_environment"]
    if set(environment) != {
        "bytes",
        "extracted_file_count",
        "extracted_file_hash_graph_sha256",
        "path",
        "sha256",
        "sympy_version",
    }:
        raise Q1WError("exact environment authority schema mismatch")
    verify_file(root / environment["path"], size=int(environment["bytes"]), digest=str(environment["sha256"]))
    return contract


def validate_environment(repository_root: Path, environment_root: Path, contract: dict[str, Any]) -> None:
    authority = contract["exact_environment"]
    record_raw, record = read_json(repository_root.resolve(strict=True) / authority["path"])
    if len(record_raw) != authority["bytes"] or sha256(record_raw) != authority["sha256"]:
        raise Q1WError("exact environment record identity mismatch")
    rows = record.get("extracted_file_hash_graph")
    if not isinstance(rows, list) or len(rows) != authority["extracted_file_count"]:
        raise Q1WError("exact environment file graph count mismatch")
    if record.get("extracted_file_hash_graph_sha256") != authority["extracted_file_hash_graph_sha256"]:
        raise Q1WError("exact environment file graph authority mismatch")
    root = environment_root.resolve(strict=True)
    if root.is_symlink() or not root.is_dir():
        raise Q1WError("exact environment root is invalid")
    for row in rows:
        if set(row) != {"bytes", "path", "sha256"}:
            raise Q1WError("exact environment graph row schema mismatch")
        relative = Path(row["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise Q1WError("unsafe exact environment graph path")
        candidate = (root / relative).resolve(strict=True)
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise Q1WError("exact environment path escapes root") from exc
        verify_file(candidate, size=int(row["bytes"]), digest=str(row["sha256"]))


def write_exclusive(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError as exc:
        raise Q1WError(f"refusing to overwrite existing output: {path}") from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        try:
            path.unlink(missing_ok=True)
        finally:
            raise
    if path.read_bytes() != raw:
        raise Q1WError("exclusive output verification failed")
