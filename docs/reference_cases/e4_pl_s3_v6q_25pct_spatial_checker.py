"""Independently check V6Q 25% spatial-response shards."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v6q_25pct_spatial_contract.json"
INDEPENDENT = REFERENCE / "e4_pl_s3_v5d_response_metric_checker.py"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V2D_NATIVE_PARITY_V1"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v6q-25pct-spatial-shard-v1"
CHECK_SCHEMA = "anysolver.e4-pl-s3-v6q-25pct-spatial-check-v1"
DIAGONALS = ("slash", "backslash", "alternating")
MASKS = ("dispersed", "chain")
LEVELS = (20, 40, 80)


class V6QCheckerError(RuntimeError):
    pass


def _load_independent() -> ModuleType:
    spec = importlib.util.spec_from_file_location("_s3_v6q_independent_equations", INDEPENDENT)
    if spec is None or spec.loader is None:
        raise V6QCheckerError("cannot load independent spatial checker")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _contract(module: ModuleType) -> tuple[dict[str, Any], bytes]:
    value, raw = module.load_canonical(CONTRACT), CONTRACT.read_bytes()
    if value.get("schema") != "anysolver.e4-pl-s3-v6q-25pct-spatial-contract-v1":
        raise V6QCheckerError("V6Q contract schema differs")
    for item in value.get("frozen_inputs", []):
        path = Path(str(item["path"]))
        if not path.is_absolute():
            path = ROOT / path
        payload = path.read_bytes()
        if len(payload) != item["bytes"] or module.sha256_bytes(payload) != item["sha256"]:
            raise V6QCheckerError(f"frozen input differs: {path}")
    predecessor_path = REFERENCE / "e4_pl_s3_v5d_response_metric_contract.json"
    predecessor = module.load_canonical(predecessor_path)
    for item in predecessor.get("frozen_inputs", []):
        path = ROOT / str(item["path"])
        payload = path.read_bytes()
        if len(payload) != item["bytes"] or module.sha256_bytes(payload) != item["sha256"]:
            raise V6QCheckerError(f"V5D independent input differs: {path}")
    return value, raw


def _formal_failures(sequence: Mapping[str, Any]) -> list[str]:
    key = f"{sequence['diagonal']}:{sequence['mask']}:25"
    failures = []
    if float.fromhex(str(sequence["spatial_slope_hex"])) < 1.80:
        failures.append(f"{key}:SPATIAL_RESPONSE_SLOPE")
    if float.fromhex(str(sequence["spatial_slope_deficit_hex"])) > 0.15:
        failures.append(f"{key}:SPATIAL_RESPONSE_SLOPE_DEFICIT")
    if float.fromhex(str(sequence["spatial_finest_ratio_hex"])) > 1.50:
        failures.append(f"{key}:SPATIAL_FINEST_ERROR_RATIO")
    if sequence["spatial_successive_passed"] is not True:
        failures.append(f"{key}:SPATIAL_SUCCESSIVE_ERROR")
    return failures


def verify(proof: Mapping[str, Any]) -> dict[str, Any]:
    independent = _load_independent()
    _authority, contract_raw = _contract(independent)
    diagonal = str(proof.get("diagonal"))
    if (
        proof.get("schema") != PROOF_SCHEMA
        or proof.get("candidate_formulation_id") != FORMULATION_ID
        or proof.get("contract_sha256") != independent.sha256_bytes(contract_raw)
        or proof.get("center_metric_classifying") is not False
        or proof.get("response_metric") != "NODAL_UZ_RELATIVE_L2"
        or diagonal not in DIAGONALS
        or proof.get("record_count") != 6
    ):
        raise V6QCheckerError("V6Q proof identity differs")
    checked = [
        independent._state_record(level, 25, mask, diagonal)
        for level in LEVELS
        for mask in MASKS
    ]
    claims = {str(row["record_id"]): row for row in proof.get("records", [])}
    if len(claims) != 6 or set(claims) != {row["record_id"] for row in checked}:
        raise V6QCheckerError("V6Q proof coverage differs")
    worst = max(independent._identity(claims[row["record_id"]], row) for row in checked)
    baseline = [independent._state_record(level, 0, "dispersed", diagonal) for level in LEVELS]
    sequences = []
    failures: list[str] = []
    center_diagnostics: list[str] = []
    for mask in MASKS:
        rows = [row for row in checked if row["mask"] == mask]
        sequence = independent._sequence(rows, baseline)
        sequence["diagonal"] = diagonal
        sequence["response_metric"] = "NODAL_UZ_RELATIVE_L2"
        failures.extend(_formal_failures(sequence))
        if sequence["center_gate_passed"] is not True:
            center_diagnostics.append(f"{diagonal}:{mask}:25")
        sequences.append(sequence)
    failures.sort()
    sequences.sort(key=lambda row: tuple(row["record_ids"]))
    return {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "center_diagnostic_failures": sorted(center_diagnostics),
        "diagonal": diagonal,
        "formal_failure_count": len(failures),
        "formal_failures": failures,
        "independent_baseline_record_count": 3,
        "independent_candidate_record_count": 6,
        "record_identity_passed": worst <= 3.0e-12,
        "record_identity_worst_relative_inf_hex": worst.hex(),
        "response_metric": "NODAL_UZ_RELATIVE_L2",
        "schema": CHECK_SCHEMA,
        "sequence_count": 2,
        "sequence_results": sequences,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-spatial-shard", action="store_true", required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    independent = _load_independent()
    proof = independent.load_canonical(args.proof)
    independent.exclusive_write(args.output, verify(proof))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
