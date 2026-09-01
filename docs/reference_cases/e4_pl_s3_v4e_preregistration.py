"""Standard-library-only validator for the bounded V4E shear diagnosis."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v4e_preregistration_contract.json"


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate key {key!r}")
        value[key] = item
    return value


def load_document(path: Path) -> dict[str, Any]:
    raw = Path(path).read_bytes()
    value = json.loads(raw, object_pairs_hook=_unique, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    if raw != canonical_bytes(value):
        raise ValueError(f"{path.name} is not canonical JSON")
    return value


def validate() -> dict[str, Any]:
    contract = load_document(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v4e-preregistration-contract-v1":
        raise ValueError("unexpected V4E preregistration contract")
    for item in contract["frozen_inputs"]:
        path = ROOT / item["path"]
        if not path.is_file() or path.is_symlink() or path.stat().st_size != item["bytes"] or sha256_file(path) != item["sha256"]:
            raise ValueError(f"frozen input mismatch: {path}")
    predecessor = load_document(REFERENCE / "e4_pl_s3_v4d_screen_status.json")
    if predecessor.get("terminal") != "NO_GO_E4_PL_S3_V4D_MIXED_INTERFACE" or predecessor.get("stage4a_rerun_authorized") is not False:
        raise ValueError("V4D predecessor is not canonically closed")
    diagnosis = contract["diagnostic"]
    complete = bool(
        diagnosis["thickness_ratios"] == ["1", "1/10", "1/100", "1/1000"]
        and diagnosis["diagonals"] == ["slash", "backslash"]
        and diagnosis["trace"] == "LINEAR_ROTATION_W0_THETA_X_X_THETA_Y_Y"
        and diagnosis["pl_work"] == "EXACT_ZERO"
    )
    return {
        "activation_authorized": False,
        "contract_sha256": sha256_file(CONTRACT),
        "diagnostic": diagnosis,
        "next_gate": "BOUNDED_V4E_THICKNESS_SCALED_SHEAR_DIAGNOSIS",
        "next_gate_authorized": complete,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": "anysolver.e4-pl-s3-v4e-preregistration-result-v1",
        "stage4a_rerun_authorized": False,
        "terminal": "PROVISIONAL_GO_E4_PL_S3_V4E_BOUNDED_SHEAR_DIAGNOSIS" if complete else "NO_GO_E4_PL_S3_V4E_DIAGNOSTIC_IDENTITY",
    }


def exclusive_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    exclusive_write(args.output, validate())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
