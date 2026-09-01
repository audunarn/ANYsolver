"""Independent checker for one canonical V5K worker proof."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Sequence


SCHEMA = "anysolver.e4-pl-s3-v5k-worker-proof-v1"
PASS = "PASS_MEASURED_REGISTERED_SCOPE"
FAIL = "FAIL_MEASURED_CONTRADICTION"


class V5KCheckerError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise V5KCheckerError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=lambda token: (_ for _ in ()).throw(V5KCheckerError(f"nonfinite token: {token}")))
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V5KCheckerError("proof is not canonical JSON")
    return value


def _clusters(reference: list[float], candidate: list[float]) -> list[list[int]]:
    made: list[list[int]] = [[0]]
    for index in range(1, len(reference)):
        overlap = all(
            values[index] * 0.97 <= values[index - 1] * 1.03
            for values in (reference, candidate)
        )
        if overlap:
            made[-1].append(index)
        else:
            made.append([index])
    return [cluster for cluster in made if cluster[0] < 5]


def verify(proof: dict[str, Any]) -> dict[str, Any]:
    if proof.get("schema") != SCHEMA or proof.get("activation_authorized") is not False:
        raise V5KCheckerError("proof identity changed")
    claimed_hash = proof.get("scientific_payload_sha256")
    unsigned = dict(proof)
    unsigned.pop("scientific_payload_sha256", None)
    if hashlib.sha256(canonical_bytes(unsigned)).hexdigest().upper() != claimed_hash:
        raise V5KCheckerError("scientific payload hash mismatch")
    worker_id = proof.get("worker_id")
    payload = proof.get("payload")
    if not isinstance(worker_id, str) or not isinstance(payload, dict):
        raise V5KCheckerError("worker payload is malformed")
    if worker_id.startswith("SPECTRAL_"):
        reference = [float.fromhex(value) for value in payload["reference_factors_hex"]]
        candidate = [float.fromhex(value) for value in payload["candidate_factors_hex"]]
        if len(reference) != 8 or len(candidate) != 8 or any(not math.isfinite(value) or value <= 0.0 for value in (*reference, *candidate)):
            raise V5KCheckerError("spectral window is invalid")
        errors = [abs(candidate[index] - reference[index]) / reference[index] for index in range(5)]
        if payload["factor_relative_errors_hex"] != [float(value).hex() for value in errors]:
            raise V5KCheckerError("factor errors differ")
        expected_clusters = _clusters(reference, candidate)
        records = payload["clusters"]
        if [record["indices_zero_based"] for record in records] != expected_clusters:
            raise V5KCheckerError("spectral cluster construction differs")
        scores = []
        for record in records:
            singular = [float.fromhex(value) for value in record["singular_values_hex"]]
            if len(singular) != len(record["indices_zero_based"]) or any(not 0.0 <= value <= 1.0 + 1.0e-12 for value in singular):
                raise V5KCheckerError("subspace singular values are invalid")
            score = min(value * value for value in singular)
            if float.fromhex(record["minimum_subspace_mac_hex"]) != score:
                raise V5KCheckerError("subspace MAC differs")
            scores.append(score)
        passed = max(errors) <= 0.03 and min(scores) >= 0.95
        if payload["factor_gate_passed"] is not (max(errors) <= 0.03) or payload["mac_gate_passed"] is not (min(scores) >= 0.95):
            raise V5KCheckerError("spectral gate claim differs")
    elif worker_id.startswith("ASSEMBLY_"):
        if not isinstance(payload.get("matrix_sha256"), str) or len(payload["matrix_sha256"]) != 64:
            raise V5KCheckerError("assembly matrix hash is invalid")
        passed = bool(
            payload.get("cold_warm_scalar_byte_identical") is True
            and payload.get("v2c_route_present") is True
            and payload.get("scalar_shell_element_count") == 0
            and payload.get("vectorized_shell_element_count", 0) > payload.get("v2c_element_count", 0) > 0
        )
    elif worker_id.startswith("PERFORMANCE_"):
        passed = payload == {
            "fraction_percent": int(worker_id.rsplit("_", 1)[1]),
            "measurement_complete": True,
        }
    else:
        raise V5KCheckerError("unknown worker proof")
    expected_status = PASS if passed else FAIL
    if proof.get("gate_status") != expected_status:
        raise V5KCheckerError("worker gate status differs")
    return {
        "accepted": True,
        "gate_status": expected_status,
        "proof_sha256": hashlib.sha256(canonical_bytes(proof)).hexdigest().upper(),
        "schema": "anysolver.e4-pl-s3-v5k-checker-v1",
        "worker_id": worker_id,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-proof", action="store_true", required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = verify(load(args.proof))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(canonical_bytes(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
