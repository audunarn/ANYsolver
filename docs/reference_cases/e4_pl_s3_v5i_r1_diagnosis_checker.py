"""Independent standard-library checker for the V5I-R1 diagnosis proof."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs/reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v5i_r1_diagnosis_contract.json"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v5i-r1-diagnosis-proof-v1"
CHECK_SCHEMA = "anysolver.e4-pl-s3-v5i-r1-diagnosis-check-v1"
PASS = "DIAGNOSED_E4_PL_S3_V5I_R1_PAIR_SUBSPACE_AND_ASSEMBLY_ROUTE_GAP"
GENUINE = "NO_GO_E4_PL_S3_V5I_R1_GENUINE_BUCKLING_SHAPE"
INCOMPLETE = "UNCLASSIFIED_E4_PL_S3_V5I_R1_DIAGNOSIS_INCOMPLETE"


class DiagnosisCheckError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("ascii")


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in items:
        if key in made:
            raise DiagnosisCheckError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def load_canonical(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    value = json.loads(
        raw,
        object_pairs_hook=_pairs,
        parse_constant=lambda token: (_ for _ in ()).throw(
            DiagnosisCheckError(f"nonfinite JSON token: {token}")
        ),
    )
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise DiagnosisCheckError(f"noncanonical JSON: {path}")
    return raw, value


def _floats(values: Any) -> Any:
    if isinstance(values, list):
        return [_floats(value) for value in values]
    if not isinstance(values, str):
        raise DiagnosisCheckError("expected hexadecimal float")
    made = float.fromhex(values)
    if not math.isfinite(made):
        raise DiagnosisCheckError("nonfinite hexadecimal float")
    return made


def _minimum_singular_squared(cross: list[list[float]]) -> float:
    if len(cross) != 2 or any(len(row) != 2 for row in cross):
        raise DiagnosisCheckError("pair cross matrix must be 2x2")
    a, b = cross[0]
    c, d = cross[1]
    ata00 = a * a + c * c
    ata01 = a * b + c * d
    ata11 = b * b + d * d
    trace = ata00 + ata11
    discriminant = max(0.0, (ata00 - ata11) ** 2 + 4.0 * ata01 * ata01)
    return 0.5 * (trace - math.sqrt(discriminant))


def verify_proof(proof: dict[str, Any]) -> dict[str, Any]:
    if proof.get("schema") != PROOF_SCHEMA:
        raise DiagnosisCheckError("unexpected proof schema")
    if proof.get("activation_authorized") is not False:
        raise DiagnosisCheckError("diagnosis proof must not activate S3")
    claimed = proof.get("scientific_payload_sha256")
    payload = dict(proof)
    payload.pop("scientific_payload_sha256", None)
    if claimed != sha256_bytes(canonical_bytes(payload)):
        raise DiagnosisCheckError("scientific payload hash mismatch")
    if proof.get("contract_sha256") != sha256_bytes(CONTRACT.read_bytes()):
        raise DiagnosisCheckError("contract binding mismatch")
    buckling = proof.get("buckling")
    if not isinstance(buckling, dict) or buckling.get("mode_count") != 8:
        raise DiagnosisCheckError("buckling window is incomplete")
    reference = _floats(buckling["reference_factors_hex"])
    candidate = _floats(buckling["candidate_factors_hex"])
    errors = _floats(buckling["factor_relative_errors_hex"])
    dots = _floats(buckling["diagonal_inner_products_hex"])
    macs = _floats(buckling["diagonal_mac_hex"])
    if not all(len(values) == 8 for values in (reference, candidate, errors, dots, macs)):
        raise DiagnosisCheckError("buckling vector coverage changed")
    recomputed_errors = [abs(c - r) / r for r, c in zip(reference, candidate)]
    if any(abs(a - b) > 8.0e-15 for a, b in zip(errors, recomputed_errors)):
        raise DiagnosisCheckError("factor errors disagree")
    if any(abs(mac - dot * dot) > 8.0e-15 for mac, dot in zip(macs, dots)):
        raise DiagnosisCheckError("diagonal MAC values disagree")
    if abs(max(errors[:5]) - float.fromhex(buckling["first_five_factor_error_max_hex"])) > 8.0e-15:
        raise DiagnosisCheckError("first-five factor maximum disagrees")
    reference_gap = (reference[5] - reference[4]) / reference[4]
    candidate_gap = (candidate[5] - candidate[4]) / candidate[4]
    if (
        abs(reference_gap - float.fromhex(buckling["pair_reference_relative_gap_hex"])) > 8.0e-15
        or abs(candidate_gap - float.fromhex(buckling["pair_candidate_relative_gap_hex"])) > 8.0e-15
    ):
        raise DiagnosisCheckError("pair gap disagrees")
    cross = _floats(buckling["pair_orthonormal_cross_hex"])
    pair_mac = _minimum_singular_squared(cross)
    if abs(pair_mac - float.fromhex(buckling["pair_subspace_mac_hex"])) > 8.0e-15:
        raise DiagnosisCheckError("pair subspace MAC disagrees")

    assembly = proof.get("assembly")
    if not isinstance(assembly, list) or [row.get("fraction_percent") for row in assembly] != [0, 10, 25]:
        raise DiagnosisCheckError("assembly coverage changed")
    matrix_equal = all(row.get("matrix_byte_identical_cold_warm") is True for row in assembly)
    route_gap = bool(
        assembly[0].get("s3_element_count") == 0
        and assembly[0].get("scalar_shell_element_count") == 0
        and all(
            row.get("s3_element_count", 0) > 0
            and row.get("scalar_shell_element_count") == row.get("s3_element_count")
            and row.get("vectorized_shell_element_count") == row.get("q4_element_count")
            for row in assembly[1:]
        )
    )
    factor_gate = max(errors[:5]) <= 0.03
    individual_failure = macs[4] < 0.95
    pair_pass = pair_mac >= 0.95
    if factor_gate and individual_failure and pair_pass and route_gap and matrix_equal:
        terminal = PASS
    elif factor_gate and individual_failure and not pair_pass:
        terminal = GENUINE
    else:
        terminal = INCOMPLETE
    return {
        "assembly_route_gap": route_gap,
        "candidate_formulation_id": proof["candidate_formulation_id"],
        "factor_gate_passed": factor_gate,
        "individual_mode_five_failed": individual_failure,
        "matrix_byte_identity_passed": matrix_equal,
        "pair_subspace_mac_hex": pair_mac.hex(),
        "pair_subspace_passed": pair_pass,
        "passed": terminal == PASS,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": CHECK_SCHEMA,
        "scientific_payload_sha256": claimed,
        "terminal": terminal,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-v5i-r1-diagnosis", action="store_true", required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    _raw, proof = load_canonical(args.proof)
    checked = verify_proof(proof)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(canonical_bytes(checked))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
