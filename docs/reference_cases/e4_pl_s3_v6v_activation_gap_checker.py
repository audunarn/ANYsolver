"""Independent standard-library checker for the V6V audit common record."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence


PASS = "PASS_BOUND_REGISTERED_SCOPE"
FAIL = "FAIL_BOUND_REGISTERED_SCOPE"
NO_GO = "NO_GO_E4_PL_S3_V6V_PACKAGE_RESTART_OR_BATCH"
GO = "PROVISIONAL_GO_E4_PL_S3_V6V_FINAL_QUALIFICATION_PREPARATION"
GATES = {
    "batching",
    "migration",
    "package_isolation",
    "provenance",
    "restart",
    "stage4a_spatial",
    "stage4b",
}


class CheckerError(RuntimeError):
    pass


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise CheckerError(f"duplicate key: {key}")
        value[key] = item
    return value


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("ascii")


def load(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(
            CheckerError(f"nonfinite token: {token}")
        ),
    )
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise CheckerError("noncanonical V6V common record")
    return raw, value


def verify(raw: bytes, value: dict[str, Any]) -> dict[str, Any]:
    if value.get("schema") != "anysolver.e4-pl-s3-v6v-activation-gap-common-v1":
        raise CheckerError("V6V common schema differs")
    if value.get("activation_authorized") is not False:
        raise CheckerError("V6V cannot activate S3")
    gates = value.get("gate_status")
    if not isinstance(gates, dict) or set(gates) != GATES:
        raise CheckerError("V6V gate set differs")
    if not set(gates.values()).issubset({PASS, FAIL}):
        raise CheckerError("V6V gate value differs")
    passed = set(gates.values()) == {PASS}
    if passed:
        if value.get("terminal") != GO or value.get("next_gate") != (
            "V6W_FINAL_QUALIFICATION_EVIDENCE_COMPOSITION"
        ):
            raise CheckerError("V6V PASS terminal differs")
    elif value.get("terminal") != NO_GO or value.get("next_gate") is not None:
        raise CheckerError("V6V NO-GO terminal differs")
    boundary = value.get("production_boundary")
    if boundary != {
        "anymesh_untouched": True,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
    }:
        raise CheckerError("V6V production boundary differs")
    return {
        "accepted": True,
        "common_sha256": hashlib.sha256(raw).hexdigest().upper(),
        "schema": "anysolver.e4-pl-s3-v6v-activation-gap-checker-v1",
        "terminal": value["terminal"],
    }
    package = value.get("package")
    if (
        not isinstance(package, dict)
        or package.get("import_from_target") is not True
        or package.get("round_trip_exact") is not True
        or package.get("wheel_bytes", 0) <= 0
        or len(str(package.get("wheel_sha256", ""))) != 64
    ):
        raise CheckerError("V6V package witness differs")
    return {
        "accepted": True,
        "common_sha256": hashlib.sha256(raw).hexdigest().upper(),
        "schema": "anysolver.e4-pl-s3-v6v-activation-gap-check-v1",
        "terminal": GO,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-v6v-common", action="store_true", required=True)
    parser.add_argument("--common", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    raw, value = load(args.common)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(canonical_bytes(verify(raw, value)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
