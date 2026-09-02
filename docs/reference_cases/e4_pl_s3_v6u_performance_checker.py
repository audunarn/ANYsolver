"""Independent standard-library checker for V6U measurement proofs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence


SCHEMA = "anysolver.e4-pl-s3-v6u-performance-proof-v1"
PASS = "PASS_MEASURED_REGISTERED_SCOPE"


class CheckerError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise CheckerError(f"duplicate key: {key}")
        made[key] = value
    return made


def load(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(CheckerError(f"nonfinite token: {token}")),
    )
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise CheckerError("noncanonical V6U proof")
    return value


def verify(proof: dict[str, Any]) -> dict[str, Any]:
    if proof.get("schema") != SCHEMA or proof.get("activation_authorized") is not False:
        raise CheckerError("V6U proof identity differs")
    claimed = proof.get("scientific_payload_sha256")
    unsigned = dict(proof)
    unsigned.pop("scientific_payload_sha256", None)
    if hashlib.sha256(canonical_bytes(unsigned)).hexdigest().upper() != claimed:
        raise CheckerError("V6U proof hash differs")
    worker_id = proof.get("worker_id")
    if worker_id not in {"PERFORMANCE_0", "PERFORMANCE_10", "PERFORMANCE_25"}:
        raise CheckerError("V6U worker differs")
    fraction = int(worker_id.rsplit("_", 1)[1])
    if proof.get("payload") != {"fraction_percent": fraction, "measurement_complete": True}:
        raise CheckerError("V6U measurement proof differs")
    if proof.get("gate_status") != PASS:
        raise CheckerError("V6U measurement status differs")
    return {
        "accepted": True,
        "proof_sha256": hashlib.sha256(canonical_bytes(proof)).hexdigest().upper(),
        "schema": "anysolver.e4-pl-s3-v6u-performance-checker-v1",
        "worker_id": worker_id,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-v6u-proof", action="store_true", required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(canonical_bytes(verify(load(args.proof))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
