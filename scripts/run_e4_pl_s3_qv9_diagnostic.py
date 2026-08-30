"""Adjudicate the nonclassifying QV9 diagnostic funnel.

This standard-library-only program never runs mechanics.  It consumes the
hash-bound outputs of the separately frozen targeted nodes, distinguishes
process/reference defects from V1 contradictions, and cannot authorize S3
default activation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence


INPUT_SCHEMA = "anysolver.e4-pl-s3-qv9-diagnostic-input-v1"
OUTPUT_SCHEMA = "anysolver.e4-pl-s3-qv9-diagnostic-result-v1"
PRODUCTION_RESTRICTION = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
PROCESS_REPAIRS = (
    "gitless_execution_copy",
    "portable_ci_support_import",
    "native_trial_support_import",
    "binding_generator_preload",
)
DIAGONALS = ("slash", "backslash", "alternating")
TERMINALS = (
    "BLOCKED_E4_PL_S3_QV9_PROCESS_OR_EVIDENCE",
    "NO_GO_E4_PL_S3_V1_QUALIFICATION",
    "UNCLASSIFIED_E4_PL_S3_QV9_DIAGNOSTIC_REPAIR_COMPLETE",
)


class DiagnosticError(ValueError):
    """The diagnostic record is noncanonical or incomplete."""


def _reject_constant(value: str) -> None:
    raise DiagnosticError(f"nonfinite JSON value is forbidden: {value}")


def _pairs(values: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in values:
        if key in result:
            raise DiagnosticError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )


def read_canonical(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise DiagnosticError("diagnostic input is not a canonical object")
    return raw, value


def _digest(value: object, label: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789ABCDEF" for character in value)
    ):
        raise DiagnosticError(f"{label} is not an uppercase SHA-256")
    return value


def adjudicate(value: dict[str, Any]) -> dict[str, Any]:
    if set(value) != {
        "all_q4_control",
        "evidence_sha256",
        "interface_audit",
        "mixed_sequences",
        "process_repairs",
        "schema",
        "v1_contradictions",
    } or value.get("schema") != INPUT_SCHEMA:
        raise DiagnosticError("diagnostic input fields differ")
    process = value["process_repairs"]
    controls = value["all_q4_control"]
    mixed = value["mixed_sequences"]
    interface = value["interface_audit"]
    contradictions = value["v1_contradictions"]
    hashes = value["evidence_sha256"]
    if (
        not isinstance(process, dict)
        or tuple(sorted(process)) != tuple(sorted(PROCESS_REPAIRS))
        or any(type(item) is not bool for item in process.values())
        or not isinstance(controls, dict)
        or set(controls) != {"locking_reference_valid", "q4_reference_valid"}
        or any(type(item) is not bool for item in controls.values())
        or not isinstance(mixed, dict)
        or tuple(sorted(mixed)) != tuple(sorted(DIAGONALS))
        or any(type(item) is not bool for item in mixed.values())
        or not isinstance(interface, dict)
        or set(interface) != {"component_map_valid", "record_count"}
        or type(interface["component_map_valid"]) is not bool
        or type(interface["record_count"]) is not int
        or interface["record_count"] < 0
        or not isinstance(contradictions, list)
        or any(type(item) is not str or not item for item in contradictions)
        or contradictions != sorted(set(contradictions))
        or not isinstance(hashes, dict)
        or not hashes
    ):
        raise DiagnosticError("diagnostic input values differ")
    for name, digest in hashes.items():
        if type(name) is not str or not name:
            raise DiagnosticError("diagnostic evidence identity differs")
        _digest(digest, f"diagnostic evidence {name}")
    process_closed = all(process.values())
    reference_closed = all(controls.values()) and interface["component_map_valid"]
    targeted_scope_complete = all(mixed.values()) and interface["record_count"] > 0
    blocked = not (process_closed and reference_closed and targeted_scope_complete)
    terminal = (
        TERMINALS[0]
        if blocked
        else TERMINALS[1]
        if contradictions
        else TERMINALS[2]
    )
    return {
        "default_activation_authorized": False,
        "diagnostic_scope_complete": targeted_scope_complete,
        "evidence_sha256": {name: hashes[name] for name in sorted(hashes)},
        "process_repair_closed": process_closed,
        "production_restriction": PRODUCTION_RESTRICTION,
        "reference_control_closed": reference_closed,
        "schema": OUTPUT_SCHEMA,
        "terminal": terminal,
        "v1_contradiction_count": len(contradictions),
        "v2_plan_preparation_authorized": terminal == TERMINALS[1],
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    raw, value = read_canonical(args.input)
    result = adjudicate(value)
    result["input_sha256"] = hashlib.sha256(raw).hexdigest().upper()
    with args.output.open("xb") as stream:
        stream.write(canonical_bytes(result))
    print(result["terminal"])
    return 0 if result["terminal"] == TERMINALS[2] else 2


if __name__ == "__main__":
    raise SystemExit(main())
