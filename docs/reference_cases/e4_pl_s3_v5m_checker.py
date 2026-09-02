"""Independent standard-library checker for V5M worker proofs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence


WORKER_IDS = ("BATCH_4096", "SERIALIZATION_RESTART", "PACKAGE_WHEEL")
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V2C_FLAT_LINEAR_PARITY_V1"
FROZEN_NORMALIZED_MODULE_SHA256 = {
    "e4_pl_s3_v2c_element.py": "89D3E26DC7B242BFB15D050F20DB8FDBE96FDF4B27F04DBA76A5078FF1F27B69",
    "elements.py": "032002A3BF6C5448C99CD0A231D8EFCE678B9B5F26C748360E1B3C318854A943",
    "matrix_assembly.py": "410D68A9ED0E839E75FE56FA16C86BC7BD3906312DA506A9A9D2CB23E8A89289",
    "s3_v2c_fast_assembly.py": "D6373C3BA879BE51EEBFD32732674EEE580EB9F32410F7523E16243C15342B3A",
}
PASS = "PASS_MEASURED_REGISTERED_SCOPE"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v5m-worker-proof-v1"


class V5MCheckerError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise V5MCheckerError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=lambda token: (_ for _ in ()).throw(V5MCheckerError(f"nonfinite token: {token}")))
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V5MCheckerError("proof is not strict canonical JSON")
    return value


def _batch(payload: dict[str, Any]) -> bool:
    return bool(
        payload.get("element_count") == 4096
        and payload.get("cold_scalar_csr_byte_identical") is True
        and payload.get("cold_warm_csr_byte_identical") is True
        and payload.get("hashes_identical") is True
        and payload.get("warm_global_plan_reused") is True
        and payload.get("cold_element_plan_reused") is False
        and payload.get("scalar_shell_element_count_warm") == 0
        and payload.get("vectorized_shell_element_count_warm") == 4096
        and isinstance(payload.get("csr_sha256"), str)
        and len(payload["csr_sha256"]) == 64
    )


def _serialization(payload: dict[str, Any]) -> bool:
    return bool(
        payload.get("default_q4_formulation") == "e4-pl"
        and payload.get("default_s3_formulation") == "legacy-s3"
        and payload.get("formulation_id") == FORMULATION_ID
        and payload.get("mutation_count") == 11
        and payload.get("mutations_rejected") == 11
        and payload.get("public_export_matches") is True
        and payload.get("restart_operation_count") == 6
        and payload.get("restart_operations_rejected") == 6
        and payload.get("roundtrip_case_count") == 6
        and payload.get("roundtrips_identical") is True
        and isinstance(payload.get("canonical_payload_sha256"), str)
        and len(payload["canonical_payload_sha256"]) == 64
    )


def _package(payload: dict[str, Any]) -> bool:
    probe = payload.get("probe")
    return bool(
        isinstance(probe, dict)
        and probe == {
            "candidate_class": "StrictFlatLinearE4PLS3V2CShellElement",
            "candidate_formulation_id": FORMULATION_ID,
            "default_q4_formulation": "e4-pl",
            "default_s3_formulation": "legacy-s3",
            "installed_origin_under_target": True,
            "installed_module_normalized_sha256": FROZEN_NORMALIZED_MODULE_SHA256,
            "public_export_matches": True,
            "roundtrip_identical": True,
            "source_root_absent_from_sys_path": True,
        }
        and isinstance(payload.get("anysolver_wheel_bytes"), int)
        and payload["anysolver_wheel_bytes"] > 0
        and isinstance(payload.get("anyfileio_wheel_bytes"), int)
        and payload["anyfileio_wheel_bytes"] > 0
        and all(isinstance(payload.get(name), str) and len(payload[name]) == 64 for name in ("anysolver_wheel_sha256", "anyfileio_wheel_sha256"))
    )


def verify(proof: dict[str, Any]) -> dict[str, Any]:
    required = {"activation_authorized", "candidate_formulation_id", "gate_status", "payload", "production_restriction", "schema", "scientific_payload_sha256", "worker_id"}
    if set(proof) != required:
        raise V5MCheckerError("proof schema keys mismatch")
    worker_id = proof.get("worker_id")
    if worker_id not in WORKER_IDS or proof.get("schema") != PROOF_SCHEMA:
        raise V5MCheckerError("proof identity mismatch")
    claimed = dict(proof)
    claimed.pop("scientific_payload_sha256")
    if hashlib.sha256(canonical_bytes(claimed)).hexdigest().upper() != proof.get("scientific_payload_sha256"):
        raise V5MCheckerError("scientific payload hash mismatch")
    payload = proof.get("payload")
    if not isinstance(payload, dict):
        raise V5MCheckerError("worker payload is not an object")
    passed = _batch(payload) if worker_id == "BATCH_4096" else _serialization(payload) if worker_id == "SERIALIZATION_RESTART" else _package(payload)
    accepted = bool(
        passed
        and proof.get("gate_status") == PASS
        and proof.get("activation_authorized") is False
        and proof.get("candidate_formulation_id") == FORMULATION_ID
        and proof.get("production_restriction") == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    )
    return {
        "accepted": accepted,
        "proof_sha256": hashlib.sha256(canonical_bytes(proof)).hexdigest().upper(),
        "schema": "anysolver.e4-pl-s3-v5m-check-v1",
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
    return 0 if result["accepted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
