"""Independent checker for complete V5E Stage 4A spatial-response shards."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import e4_pl_s3_v5d_response_metric_checker as v5d_check


CONTRACT = REFERENCE / "e4_pl_s3_v5e_stage4a_spatial_contract.json"
FORMULATION_ID = v5d_check.FORMULATION_ID
PROOF_SCHEMA = "anysolver.e4-pl-s3-v5e-stage4a-spatial-shard-v1"
CHECK_SCHEMA = "anysolver.e4-pl-s3-v5e-stage4a-spatial-check-v1"
DIAGONALS = v5d_check.DIAGONALS
LEVELS = v5d_check.LEVELS
MASKS = v5d_check.MASKS
FRACTIONS = (1, 5, 10, 25)


class Stage4ASpatialCheckerError(RuntimeError):
    pass


canonical_bytes = v5d_check.canonical_bytes
sha256_bytes = v5d_check.sha256_bytes
sha256_file = v5d_check.sha256_file
load_canonical = v5d_check.load_canonical
exclusive_write = v5d_check.exclusive_write


def validate_authority() -> Mapping[str, Any]:
    contract = load_canonical(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v5e-stage4a-spatial-contract-v1":
        raise Stage4ASpatialCheckerError("unexpected V5E contract schema")
    for binding in contract.get("frozen_inputs", []):
        path = ROOT / str(binding["path"])
        raw = path.read_bytes()
        if len(raw) != binding["bytes"] or sha256_bytes(raw) != binding["sha256"]:
            raise Stage4ASpatialCheckerError(f"frozen input mismatch: {path}")
    return contract


def _record(level: int, fraction: int, mask: str, diagonal: str) -> dict[str, Any]:
    original = v5d_check.FRACTIONS
    v5d_check.FRACTIONS = FRACTIONS
    try:
        return v5d_check._state_record(level, fraction, mask, diagonal)
    finally:
        v5d_check.FRACTIONS = original


def _specs(diagonal: str) -> list[tuple[int, int, str, str]]:
    return [
        spec
        for level in LEVELS
        for spec in (
            (level, 0, "dispersed", diagonal),
            *((level, fraction, mask, diagonal) for mask in MASKS for fraction in FRACTIONS),
        )
    ]


def _formal_failures(sequence: Mapping[str, Any]) -> list[str]:
    key = f"{sequence['diagonal']}:{sequence['mask']}:{sequence['fraction_percent']}"
    limit = 1.50 if sequence["fraction_percent"] == 25 else 1.25
    failures = []
    if float.fromhex(str(sequence["spatial_slope_hex"])) < 1.80:
        failures.append(f"{key}:SPATIAL_RESPONSE_SLOPE")
    if float.fromhex(str(sequence["spatial_slope_deficit_hex"])) > 0.15:
        failures.append(f"{key}:SPATIAL_RESPONSE_SLOPE_DEFICIT")
    if float.fromhex(str(sequence["spatial_finest_ratio_hex"])) > limit:
        failures.append(f"{key}:SPATIAL_FINEST_ERROR_RATIO")
    if sequence["spatial_successive_passed"] is not True:
        failures.append(f"{key}:SPATIAL_SUCCESSIVE_ERROR")
    if float.fromhex(str(sequence["energy_slope_lower_95_hex"])) < 0.90:
        failures.append(f"{key}:ENERGY_SLOPE_LOWER_95")
    return failures


def verify(proof: Mapping[str, Any]) -> dict[str, Any]:
    validate_authority()
    if proof.get("schema") != PROOF_SCHEMA or proof.get("candidate_formulation_id") != FORMULATION_ID:
        raise Stage4ASpatialCheckerError("V5E proof identity mismatch")
    if proof.get("contract_sha256") != sha256_file(CONTRACT):
        raise Stage4ASpatialCheckerError("V5E contract mismatch")
    if proof.get("center_metric_classifying") is not False or proof.get("response_metric") != "NODAL_UZ_RELATIVE_L2":
        raise Stage4ASpatialCheckerError("V5E response metric mismatch")
    diagonal = str(proof.get("diagonal"))
    if diagonal not in DIAGONALS or proof.get("record_count") != 27:
        raise Stage4ASpatialCheckerError("V5E proof coverage mismatch")
    checked = [_record(*spec) for spec in _specs(diagonal)]
    claims = {str(row["record_id"]): row for row in proof.get("records", [])}
    if len(claims) != 27 or set(claims) != {row["record_id"] for row in checked}:
        raise Stage4ASpatialCheckerError("V5E record catalog mismatch")
    worst = max(v5d_check._identity(claims[row["record_id"]], row) for row in checked)
    baseline = [row for row in checked if row["s3_area_fraction_percent"] == 0]
    sequences: list[dict[str, Any]] = []
    failures: list[str] = []
    center_diagnostic_failures: list[str] = []
    for mask in MASKS:
        for fraction in FRACTIONS:
            rows = [row for row in checked if row["mask"] == mask and row["s3_area_fraction_percent"] == fraction]
            sequence = v5d_check._sequence(rows, baseline)
            sequence["diagonal"] = diagonal
            sequence["response_metric"] = "NODAL_UZ_RELATIVE_L2"
            failures.extend(_formal_failures(sequence))
            if sequence["center_gate_passed"] is not True:
                center_diagnostic_failures.append(f"{diagonal}:{mask}:{fraction}")
            sequences.append(sequence)
    failures.sort()
    center_diagnostic_failures.sort()
    sequences.sort(key=lambda row: tuple(row["record_ids"]))
    return {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "center_diagnostic_failures": center_diagnostic_failures,
        "diagonal": diagonal,
        "formal_failure_count": len(failures),
        "formal_failures": failures,
        "independent_record_count": 27,
        "record_identity_passed": worst <= 3.0e-12,
        "record_identity_worst_relative_inf_hex": worst.hex(),
        "response_metric": "NODAL_UZ_RELATIVE_L2",
        "schema": CHECK_SCHEMA,
        "sequence_count": 8,
        "sequence_results": sequences,
        "v5c_reclassified": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-spatial-shard", action="store_true", required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    exclusive_write(args.output, verify(load_canonical(args.proof)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
