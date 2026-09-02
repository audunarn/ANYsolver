"""Independent standard-library checker for V6S Stage 4B worker proofs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Sequence


PASS = "PASS_MEASURED_REGISTERED_SCOPE"
FAIL = "FAIL_MEASURED_CONTRADICTION"
SCHEMA = "anysolver.e4-pl-s3-v6s-stage4b-worker-proof-v1"
CANDIDATE = "CANDIDATE_E4_PL_S3_V2D_NATIVE_PARITY_V1"


class CheckerError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise CheckerError(f"duplicate JSON key: {key}")
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
        raise CheckerError("V6S proof is noncanonical")
    return value


def _clusters(reference: list[float], candidate: list[float]) -> list[list[int]]:
    made = [[0]]
    for index in range(1, len(reference)):
        overlap = all(values[index] * 0.97 <= values[index - 1] * 1.03 for values in (reference, candidate))
        if overlap:
            made[-1].append(index)
        else:
            made.append([index])
    return [row for row in made if row[0] < 5]


def verify(proof: dict[str, Any]) -> dict[str, Any]:
    if (
        proof.get("schema") != SCHEMA
        or proof.get("candidate_formulation_id") != CANDIDATE
        or proof.get("activation_authorized") is not False
    ):
        raise CheckerError("V6S proof identity changed")
    claimed = proof.get("scientific_payload_sha256")
    unsigned = dict(proof)
    unsigned.pop("scientific_payload_sha256", None)
    if hashlib.sha256(canonical_bytes(unsigned)).hexdigest().upper() != claimed:
        raise CheckerError("V6S scientific hash differs")
    worker_id, payload = proof.get("worker_id"), proof.get("payload")
    if not isinstance(worker_id, str) or not isinstance(payload, dict):
        raise CheckerError("V6S worker payload is malformed")
    if worker_id.startswith("MODAL_"):
        error = float.fromhex(payload["frequency_error_max_hex"])
        mac = float.fromhex(payload["minimum_clustered_mac_hex"])
        passed = error <= 0.02 and mac >= 0.95 and payload.get("rigid_gate_passed") is True
        if payload.get("frequency_gate_passed") is not (error <= 0.02):
            raise CheckerError("V6S modal frequency gate differs")
        if payload.get("mac_gate_passed") is not (mac >= 0.95):
            raise CheckerError("V6S modal MAC gate differs")
    elif worker_id.startswith("BUCKLING_"):
        reference = [float.fromhex(value) for value in payload["reference_factors_hex"]]
        candidate = [float.fromhex(value) for value in payload["candidate_factors_hex"]]
        if len(reference) != 8 or len(candidate) != 8:
            raise CheckerError("V6S buckling window differs")
        errors = [abs(candidate[index] - reference[index]) / reference[index] for index in range(5)]
        if payload["factor_relative_errors_hex"] != [float(value).hex() for value in errors]:
            raise CheckerError("V6S factor errors differ")
        records = payload["clusters"]
        if [row["indices_zero_based"] for row in records] != _clusters(reference, candidate):
            raise CheckerError("V6S cluster rule differs")
        scores = []
        for row in records:
            singular = [float.fromhex(value) for value in row["singular_values_hex"]]
            score = min(value * value for value in singular)
            if float.fromhex(row["minimum_subspace_mac_hex"]) != score:
                raise CheckerError("V6S subspace score differs")
            scores.append(score)
        passed = max(errors) <= 0.03 and min(scores) >= 0.95
        if payload.get("factor_gate_passed") is not (max(errors) <= 0.03):
            raise CheckerError("V6S buckling factor gate differs")
        if payload.get("mac_gate_passed") is not (min(scores) >= 0.95):
            raise CheckerError("V6S buckling MAC gate differs")
    elif worker_id.startswith("PERFORMANCE_"):
        fraction = int(worker_id.rsplit("_", 1)[1])
        passed = payload == {"fraction_percent": fraction, "measurement_complete": True}
    else:
        raise CheckerError("unknown V6S worker")
    expected = PASS if passed else FAIL
    if proof.get("gate_status") != expected:
        raise CheckerError("V6S worker status differs")
    return {
        "accepted": True,
        "gate_status": expected,
        "proof_sha256": hashlib.sha256(canonical_bytes(proof)).hexdigest().upper(),
        "schema": "anysolver.e4-pl-s3-v6s-stage4b-checker-v1",
        "worker_id": worker_id,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-v6s-proof", action="store_true", required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(canonical_bytes(verify(load(args.proof))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
