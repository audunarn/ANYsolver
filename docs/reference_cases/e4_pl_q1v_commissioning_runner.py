#!/usr/bin/env python3
"""Guarded, nonclassifying Q1V implementation-commissioning launcher.

This standard-library-only launcher runs one exact implementation twice in
fresh external processes, rejects scientific content recursively, proves byte
identity, and can create the backend-neutral construction agreement.  It does
not import either exact backend or compute a scientific terminal.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from typing import Any, Iterable, Mapping, Sequence

from e4_pl_q1v_authority_guard import (
    AuthorityGuardError,
    canonical_bytes,
    sha256_bytes,
    strict_json_bytes,
    validate_commissioning_authority,
)


CANDIDATE_ID = "candidate_e4_pl_q1v.wg2020_numbered_frame_surface_pl_planar_linear_iso_v1"
STUDY_ID = "study_e4_pl_q1v.q1u_backend_repair_and_local_completion_v1"
RECORD_KIND = "NONCLASSIFYING_IMPLEMENTATION_COMMISSIONING"
CONTRACT_SCHEMA = "anysolver.s4.e4-pl-q1v-commissioning-contract-v1"
AGREEMENT_SCHEMA = "anysolver.s4.e4-pl-q1v-commissioning-agreement-v1"
BLOCKED_TERMINAL = "BLOCKED_E4_PL_Q1V_IMPLEMENTATION_IDENTITY"

GEOMETRY_IDS = (
    "Q0_SQUARE",
    "Q1_AFFINE_SKEW",
    "Q2_TRAPEZOID",
    "Q3_TAPERED_SKEW",
    "Q4_HOSTILE_ASYMMETRIC_1",
    "Q5_HOSTILE_ASYMMETRIC_2",
    "Q3_TAPERED_SKEW_RSTAR_TRANSLATED",
)
D4_IDS = ("E", "R90", "R180", "R270", "MR", "MS", "MD", "MA")
GAUSS_IDS = ("GP_MM", "GP_PM", "GP_PP", "GP_MP")
CASE_IDS = tuple(f"{geometry}::{operation}" for geometry in GEOMETRY_IDS for operation in D4_IDS)
STATION_IDS = tuple(f"{case_id}::{station}" for case_id in CASE_IDS for station in GAUSS_IDS)
CENTRE_IDS = tuple(f"{case_id}::CENTRE" for case_id in CASE_IDS)

TOP_DIMENSIONS = {
    "case_records": 56,
    "centre_ids": 56,
    "geometry_groups": 7,
    "station_ids": 224,
}
CASE_DIMENSIONS = {
    "centre_taylor": [3, 24],
    "compatible": [8, 20],
    "frame": [3, 3],
    "gauss_stations": 4,
    "independent_strain": [8, 21],
    "independent_stress": [8, 14],
    "load": 24,
    "qd": [24, 4],
    "reaction": [24, 20],
    "support": [20, 24],
    "support_system": [44, 44],
    "t5": [24, 20],
}
IMPLEMENTATIONS = {
    "reference": {
        "implementation_id": "Q1V_REFERENCE_STDLIB_FIELD_ALG",
        "runner_id": "REFERENCE_COMMISSIONING_RUNNER",
        "schema": "anysolver.s4.e4-pl-q1v-reference-commissioning-v1",
        "script": "docs/reference_cases/e4_pl_q1v_reference.py",
    },
    "oracle": {
        "implementation_id": "Q1V_ORACLE_SYMPY_ALGEBRAIC_FIELD",
        "runner_id": "ORACLE_COMMISSIONING_RUNNER",
        "schema": "anysolver.s4.e4-pl-q1v-oracle-commissioning-v1",
        "script": "docs/reference_cases/e4_pl_q1v_oracle.py",
    },
}
IMPLEMENTATION_KEYS = {
    "candidate_id",
    "case_records",
    "centre_ids",
    "construction_completed",
    "determinism_payload_sha256",
    "dimensions",
    "exception_status",
    "implementation_id",
    "record_kind",
    "schema",
    "schema_valid",
    "station_ids",
    "study_id",
}
CASE_KEYS = {
    "case_id",
    "construction_completed",
    "dimensions",
    "exception_status",
    "schema_valid",
}
AGREEMENT_KEYS = {
    "candidate_id",
    "case_id_order_sha256",
    "centre_id_order_sha256",
    "exception_status",
    "oracle_construction_sha256",
    "record_kind",
    "reference_construction_sha256",
    "schema",
    "station_id_order_sha256",
    "study_id",
}


class CommissioningError(RuntimeError):
    """Raised before nonclassifying evidence can be accepted."""


def _is_link(path: Path) -> bool:
    try:
        attributes = path.lstat().st_file_attributes
    except (AttributeError, OSError):
        attributes = 0
    return path.is_symlink() or bool(
        attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _require_keys(value: Any, keys: set[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != keys:
        raise CommissioningError(f"{label} keys differ from frozen schema")
    return value


def _normalized_token_text(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_")


def recursive_forbidden_matches(
    value: Any,
    forbidden: Iterable[str],
    *,
    path: str = "$",
) -> list[str]:
    """Return every recursively encountered exact underscore-token match."""
    vocabulary = tuple(_normalized_token_text(token) for token in forbidden)
    matches: list[str] = []

    def inspect_text(text: str, location: str) -> None:
        normalized = _normalized_token_text(text)
        padded = f"_{normalized}_"
        for token in vocabulary:
            if f"_{token}_" in padded:
                matches.append(f"{location}:{token}")

    def walk(item: Any, location: str) -> None:
        if isinstance(item, Mapping):
            for key, nested in item.items():
                inspect_text(str(key), f"{location}.<key>")
                walk(nested, f"{location}.{key}")
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            for index, nested in enumerate(item):
                walk(nested, f"{location}[{index}]")
        elif isinstance(item, str):
            inspect_text(item, location)

    walk(value, path)
    return matches


def _order_sha256(values: Sequence[str]) -> str:
    return hashlib.sha256(("\n".join(values) + "\n").encode("utf-8")).hexdigest().upper()


def _payload_sha256(record: Mapping[str, Any]) -> str:
    payload = {
        "case_records": record["case_records"],
        "centre_ids": record["centre_ids"],
        "dimensions": record["dimensions"],
        "station_ids": record["station_ids"],
    }
    return sha256_bytes(canonical_bytes(payload))


def load_commissioning_contract(path: Path, expected_sha256: str) -> Mapping[str, Any]:
    if _is_link(path) or not path.is_file():
        raise CommissioningError("commissioning contract must be a regular nonsymlink file")
    raw = path.read_bytes()
    if sha256_bytes(raw) != expected_sha256.upper():
        raise CommissioningError("commissioning contract SHA-256 mismatch")
    value = strict_json_bytes(raw)
    if not isinstance(value, Mapping) or value.get("schema") != CONTRACT_SCHEMA:
        raise CommissioningError("commissioning contract schema drift")
    return value


def validate_implementation_record(
    record: Any,
    contract: Mapping[str, Any],
    implementation: str,
) -> Mapping[str, Any]:
    """Validate a closed, nonclassifying commissioning implementation record."""
    if implementation not in IMPLEMENTATIONS:
        raise CommissioningError("unknown commissioning implementation")
    forbidden = contract.get("forbidden_content")
    if not isinstance(forbidden, list):
        raise CommissioningError("commissioning forbidden vocabulary is absent")
    matches = recursive_forbidden_matches(record, (str(token) for token in forbidden))
    if matches:
        raise CommissioningError(f"forbidden commissioning content: {matches[0]}")
    record = _require_keys(record, IMPLEMENTATION_KEYS, "commissioning implementation record")
    profile = IMPLEMENTATIONS[implementation]
    if (
        record["candidate_id"] != CANDIDATE_ID
        or record["study_id"] != STUDY_ID
        or record["record_kind"] != RECORD_KIND
        or record["schema"] != profile["schema"]
        or record["implementation_id"] != profile["implementation_id"]
        or record["construction_completed"] is not True
        or record["schema_valid"] is not True
        or record["exception_status"] != "NONE"
    ):
        raise CommissioningError("commissioning implementation identity/status drift")
    if record["dimensions"] != TOP_DIMENSIONS:
        raise CommissioningError("commissioning top-level dimensions drift")
    if record["centre_ids"] != list(CENTRE_IDS):
        raise CommissioningError("commissioning centre-ID order drift")
    if record["station_ids"] != list(STATION_IDS):
        raise CommissioningError("commissioning station-ID order drift")
    case_records = record["case_records"]
    if not isinstance(case_records, list) or len(case_records) != 56:
        raise CommissioningError("commissioning case-record count drift")
    for expected_id, row in zip(CASE_IDS, case_records, strict=True):
        row = _require_keys(row, CASE_KEYS, "commissioning case record")
        if (
            row["case_id"] != expected_id
            or row["construction_completed"] is not True
            or row["schema_valid"] is not True
            or row["exception_status"] != "NONE"
            or row["dimensions"] != CASE_DIMENSIONS
        ):
            raise CommissioningError(f"commissioning case drift: {expected_id}")
    expected_payload_sha = _payload_sha256(record)
    if record["determinism_payload_sha256"] != expected_payload_sha:
        raise CommissioningError("commissioning construction-payload hash drift")
    return record


def validate_implementation_bytes(
    raw: bytes,
    contract: Mapping[str, Any],
    implementation: str,
) -> Mapping[str, Any]:
    return validate_implementation_record(strict_json_bytes(raw), contract, implementation)


def build_agreement(
    reference: Mapping[str, Any],
    oracle: Mapping[str, Any],
) -> dict[str, Any]:
    for key in ("case_records", "centre_ids", "dimensions", "station_ids"):
        if reference[key] != oracle[key]:
            raise CommissioningError(f"cross-implementation commissioning drift: {key}")
    if reference["determinism_payload_sha256"] != oracle["determinism_payload_sha256"]:
        raise CommissioningError("cross-implementation construction hash drift")
    result = {
        "candidate_id": CANDIDATE_ID,
        "case_id_order_sha256": _order_sha256(CASE_IDS),
        "centre_id_order_sha256": _order_sha256(CENTRE_IDS),
        "exception_status": "NONE",
        "oracle_construction_sha256": oracle["determinism_payload_sha256"],
        "record_kind": RECORD_KIND,
        "reference_construction_sha256": reference["determinism_payload_sha256"],
        "schema": AGREEMENT_SCHEMA,
        "station_id_order_sha256": _order_sha256(STATION_IDS),
        "study_id": STUDY_ID,
    }
    _require_keys(result, AGREEMENT_KEYS, "commissioning agreement")
    return result


def _write_exclusive_verified(path: Path, raw: bytes) -> None:
    try:
        with path.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        if path.read_bytes() != raw:
            raise CommissioningError("exclusive commissioning output reopen mismatch")
    except OSError as exc:
        raise CommissioningError("exclusive commissioning output write failed") from exc


def _fresh_attempt_path(attempt_root: Path, name: str) -> Path:
    path = attempt_root / name
    if path.exists() or path.is_symlink():
        raise CommissioningError("commissioning attempt output already exists")
    return path


def _commission_command(
    root: Path,
    implementation: str,
    contract_path: Path,
    contract_sha256: str,
    environment_root: Path,
    environment_record: Path,
    environment_sha256: str,
    output: Path,
) -> list[str]:
    profile = IMPLEMENTATIONS[implementation]
    return [
        sys.executable,
        str(root / str(profile["script"])),
        "--commission",
        "--commissioning-contract",
        str(contract_path),
        "--commissioning-contract-sha256",
        contract_sha256,
        "--environment-root",
        str(environment_root),
        "--environment-record",
        str(environment_record),
        "--environment-sha256",
        environment_sha256,
        "--runner-id",
        str(profile["runner_id"]),
        "--output",
        str(output),
    ]


def run_twice(
    *,
    root: Path,
    implementation: str,
    contract_path: Path,
    contract_sha256: str,
    environment_root: Path,
    environment_record: Path,
    environment_sha256: str,
    attempt_root: Path,
    output: Path,
) -> bytes:
    profile = IMPLEMENTATIONS[implementation]
    guard = validate_commissioning_authority(
        repository_root=root,
        runner_id=str(profile["runner_id"]),
        commissioning_contract_path=contract_path,
        commissioning_contract_sha256=contract_sha256,
        environment_root=environment_root,
        environment_record_path=environment_record,
        environment_sha256=environment_sha256,
        output_path=output,
    )
    contract = guard.contract
    attempt_root = attempt_root.resolve(strict=True)
    if _is_link(attempt_root) or not attempt_root.is_dir():
        raise CommissioningError("attempt root must be a nonsymlink directory")
    if any(attempt_root.iterdir()):
        raise CommissioningError("attempt root must be empty")
    environment = os.environ.copy()
    environment.update(
        {
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
        }
    )
    raws: list[bytes] = []
    for index in (1, 2):
        attempt = _fresh_attempt_path(attempt_root, f"{implementation}-{index}.json")
        completed = subprocess.run(
            _commission_command(
                root,
                implementation,
                contract_path,
                contract_sha256,
                environment_root,
                environment_record,
                environment_sha256,
                attempt,
            ),
            cwd=root,
            env=environment,
            check=False,
            capture_output=True,
        )
        if completed.returncode != 0:
            message = completed.stderr.decode("utf-8", errors="replace").strip()
            raise CommissioningError(f"fresh commissioning process {index} failed: {message}")
        if completed.stdout:
            raise CommissioningError("commissioning implementation stdout must be empty")
        if _is_link(attempt) or not attempt.is_file():
            raise CommissioningError("commissioning process did not create its output")
        raw = attempt.read_bytes()
        validate_implementation_bytes(raw, contract, implementation)
        raws.append(raw)
    if raws[0] != raws[1]:
        raise CommissioningError("fresh commissioning processes are not byte-identical")
    _write_exclusive_verified(guard.output_path, raws[0])
    return raws[0]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--run", choices=sorted(IMPLEMENTATIONS))
    modes.add_argument("--agree", action="store_true")
    modes.add_argument("--validate", choices=sorted(IMPLEMENTATIONS))
    parser.add_argument("--commissioning-contract", required=True, type=Path)
    parser.add_argument("--commissioning-contract-sha256", required=True)
    parser.add_argument("--environment-root", type=Path)
    parser.add_argument("--environment-record", type=Path)
    parser.add_argument("--environment-sha256")
    parser.add_argument("--attempt-root", type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--oracle", type=Path)
    parser.add_argument("--record", type=Path)
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        root = Path(__file__).resolve().parents[2]
        contract = load_commissioning_contract(
            args.commissioning_contract,
            args.commissioning_contract_sha256,
        )
        if args.run:
            required = (
                args.environment_root,
                args.environment_record,
                args.environment_sha256,
                args.attempt_root,
                args.output,
            )
            if any(value is None for value in required):
                raise CommissioningError("--run requires environment, attempt-root, and output")
            run_twice(
                root=root,
                implementation=args.run,
                contract_path=args.commissioning_contract,
                contract_sha256=args.commissioning_contract_sha256,
                environment_root=args.environment_root,
                environment_record=args.environment_record,
                environment_sha256=args.environment_sha256,
                attempt_root=args.attempt_root,
                output=args.output,
            )
        elif args.agree:
            if args.reference is None or args.oracle is None or args.output is None:
                raise CommissioningError("--agree requires reference, oracle, and output")
            reference = validate_implementation_bytes(
                args.reference.read_bytes(), contract, "reference"
            )
            oracle = validate_implementation_bytes(args.oracle.read_bytes(), contract, "oracle")
            _write_exclusive_verified(args.output, canonical_bytes(build_agreement(reference, oracle)))
        else:
            if args.record is None:
                raise CommissioningError("--validate requires --record")
            validate_implementation_bytes(args.record.read_bytes(), contract, args.validate)
            sys.stdout.buffer.write(
                canonical_bytes(
                    {
                        "implementation": args.validate,
                        "mode": "STATIC_NONCLASSIFYING_RECORD_VALIDATION",
                        "status": "PASS",
                    }
                )
            )
        return 0
    except (AuthorityGuardError, CommissioningError, OSError) as exc:
        sys.stderr.write(f"{BLOCKED_TERMINAL}: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
