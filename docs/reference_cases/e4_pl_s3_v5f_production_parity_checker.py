"""Independent V5F checker; never imports production or producer mechanics."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import e4_pl_s3_v5b_relaxed_screen_checker as independent


CONTRACT = REFERENCE / "e4_pl_s3_v5f_production_parity_contract.json"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v5f-production-parity-proof-v1"
CHECK_SCHEMA = "anysolver.e4-pl-s3-v5f-production-parity-check-v1"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V2B_FLAT_LINEAR_V1"
COMPONENTS = ("membrane", "bending", "shear", "physical", "pl", "total")
RELATIVE_LIMIT = 3.0e-12


class ProductionParityCheckError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise ProductionParityCheckError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load_canonical(path: Path) -> Any:
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=lambda token: (_ for _ in ()).throw(ProductionParityCheckError(f"nonfinite JSON token: {token}")))
    if canonical_bytes(value) != raw:
        raise ProductionParityCheckError(f"noncanonical JSON: {path}")
    return value


def decode_array(value: Mapping[str, Any]) -> np.ndarray:
    shape = tuple(value.get("shape", ()))
    entries = value.get("hex")
    if not isinstance(entries, list) or not all(isinstance(item, str) for item in entries):
        raise ProductionParityCheckError("malformed encoded array")
    made = np.asarray([float.fromhex(item) for item in entries], dtype=np.float64)
    if not np.all(np.isfinite(made)) or int(np.prod(shape, dtype=np.int64)) != made.size:
        raise ProductionParityCheckError("invalid encoded array")
    return made.reshape(shape)


def _relative(left: Any, right: Any) -> float:
    left_array = np.asarray(left, dtype=np.float64)
    right_array = np.asarray(right, dtype=np.float64)
    return float(np.linalg.norm(left_array - right_array, ord=np.inf) / max(float(np.linalg.norm(right_array, ord=np.inf)), 1.0))


def _expected(case: Mapping[str, Any]) -> dict[str, Any]:
    coordinates = decode_array(case["coordinates"])
    order = tuple(case["connectivity_order"])
    if sorted(order) != [0, 1, 2]:
        raise ProductionParityCheckError("invalid D3 connectivity")
    expected = independent.reconstruct(coordinates[np.asarray(order)], thickness=0.01)
    if case["case_id"] == "DIRECTOR_REVERSAL":
        expected = dict(expected)
        expected["pressure_load"] = -np.asarray(expected["pressure_load"])
    return expected


def verify_proof(proof: Mapping[str, Any]) -> dict[str, Any]:
    if proof.get("schema") != PROOF_SCHEMA or proof.get("candidate_formulation_id") != FORMULATION_ID:
        raise ProductionParityCheckError("proof identity mismatch")
    if proof.get("activation_authorized") is not False or proof.get("stage4b_execution_authorized") is not False:
        raise ProductionParityCheckError("proof authority overreach")
    payload = dict(proof)
    claimed_payload_hash = payload.pop("scientific_payload_sha256", None)
    if claimed_payload_hash != sha256_bytes(canonical_bytes(payload)):
        raise ProductionParityCheckError("scientific payload hash mismatch")
    catalog = proof.get("catalog")
    catalog_cases = proof.get("catalog_cases")
    cases = proof.get("cases")
    if not isinstance(catalog, list) or len(catalog) != 81 or proof.get("catalog_record_count") != 81:
        raise ProductionParityCheckError("V5F catalog must contain 81 records")
    if not isinstance(catalog_cases, list) or len(catalog_cases) != 162 or not isinstance(cases, list) or len(cases) != 169:
        raise ProductionParityCheckError("V5F case coverage mismatch")
    if len({case.get("case_id") for case in cases}) != len(cases):
        raise ProductionParityCheckError("duplicate V5F case ID")
    catalog_case_ids = {item.get("case_id") for item in catalog_cases}
    if len(catalog_case_ids) != 162:
        raise ProductionParityCheckError("duplicate catalog case binding")

    component_worst = 0.0
    pressure_worst = 0.0
    force_worst = 0.0
    work_worst = 0.0
    phi_worst = 0.0
    rank_failures: list[str] = []
    for case in cases:
        if case.get("formulation_id") != FORMULATION_ID or case.get("selector") != "e4-pl-s3-v2b":
            raise ProductionParityCheckError("production selector identity mismatch")
        expected = _expected(case)
        matrices = {name: decode_array(case["components"][name]) for name in COMPONENTS}
        for name in COMPONENTS:
            component_worst = max(component_worst, _relative(matrices[name], expected[name]))
        actual_phi = float.fromhex(case["phi_squared_hex"])
        phi_worst = max(phi_worst, abs(actual_phi - float(expected["phi_squared"])) / max(abs(float(expected["phi_squared"])), 1.0))
        pressure_worst = max(pressure_worst, _relative(decode_array(case["pressure_load"]), expected["pressure_load"]))
        displacement = decode_array(case["displacement"])
        force_worst = max(force_worst, _relative(decode_array(case["internal_force"]), matrices["total"] @ displacement))
        resultants = {name: decode_array(value) for name, value in case["resultants"].items()}
        weights = resultants["physical_weights"][:, None]
        for component, strain_name, resultant_name in (
            ("membrane", "membrane_strain", "membrane_resultants"),
            ("bending", "curvature", "bending_resultants"),
            ("shear", "transverse_shear_strain", "transverse_shear_resultants"),
        ):
            recovered_work = float(np.sum(weights * resultants[strain_name] * resultants[resultant_name]))
            matrix_work = float(displacement @ matrices[component] @ displacement)
            work_worst = max(work_worst, abs(recovered_work - matrix_work) / max(abs(matrix_work), 1.0))
        ranks = {name: int(np.linalg.matrix_rank(matrices[name], tol=max(float(np.linalg.norm(matrices[name], ord=2)), 1.0) * 1.0e-10)) for name in ("physical", "pl", "total")}
        if ranks != {"physical": 9, "pl": 3, "total": 12}:
            rank_failures.append(str(case["case_id"]))
    passed = not rank_failures and max(component_worst, pressure_worst, force_worst, work_worst, phi_worst) <= RELATIVE_LIMIT
    return {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "case_count": len(cases),
        "catalog_record_count": len(catalog),
        "component_worst_hex": component_worst.hex(),
        "force_worst_hex": force_worst.hex(),
        "passed": passed,
        "phi_worst_hex": phi_worst.hex(),
        "pressure_worst_hex": pressure_worst.hex(),
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "rank_failure_case_ids": sorted(rank_failures),
        "schema": CHECK_SCHEMA,
        "scientific_payload_sha256": claimed_payload_hash,
        "stage4b_execution_authorized": False,
        "work_worst_hex": work_worst.hex(),
    }


def exclusive_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-production-parity-proof", action="store_true", required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    proof = load_canonical(args.proof)
    exclusive_write(args.output, verify_proof(proof))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
