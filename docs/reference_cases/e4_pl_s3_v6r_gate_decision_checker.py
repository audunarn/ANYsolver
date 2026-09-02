"""Check V6Q proofs by cross-implementation scientific decision agreement."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v6r_gate_decision_contract.json"
V6Q_CHECKER = REFERENCE / "e4_pl_s3_v6q_25pct_spatial_checker.py"
SCHEMA = "anysolver.e4-pl-s3-v6r-gate-decision-check-v1"
DIAGONALS = ("slash", "backslash", "alternating")
MASKS = ("dispersed", "chain")
LEVELS = (20, 40, 80)


class V6RCheckerError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _reject_constant(value: str) -> None:
    raise V6RCheckerError(f"nonfinite JSON constant: {value}")


def _reject_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise V6RCheckerError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def strict_json(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = json.loads(raw, parse_constant=_reject_constant, object_pairs_hook=_reject_pairs)
    if not isinstance(value, dict) or raw != canonical_bytes(value):
        raise V6RCheckerError(f"noncanonical JSON: {path}")
    return value, raw


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise V6RCheckerError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_authority(proof_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    contract, _ = strict_json(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v6r-gate-decision-contract-v1":
        raise V6RCheckerError("V6R contract schema differs")
    for item in contract["frozen_inputs"]:
        path = Path(item["path"])
        if not path.is_absolute():
            path = ROOT / path
        raw = path.read_bytes()
        if len(raw) != item["bytes"] or sha256(raw) != item["sha256"]:
            raise V6RCheckerError(f"frozen input differs: {path}")
    proof, proof_raw = strict_json(proof_path)
    diagonal = str(proof.get("diagonal"))
    expected = contract["proofs"].get(diagonal)
    if (
        expected is None
        or proof_path.resolve() != Path(expected["path"]).resolve()
        or len(proof_raw) != expected["bytes"]
        or sha256(proof_raw) != expected["sha256"]
    ):
        raise V6RCheckerError("V6R proof binding differs")
    return contract, proof


def _failures(v6q: ModuleType, sequence: Mapping[str, Any]) -> list[str]:
    return sorted(v6q._formal_failures(sequence))


def verify(proof_path: Path) -> dict[str, Any]:
    contract, proof = validate_authority(proof_path)
    v6q = _load(V6Q_CHECKER, "_s3_v6r_bound_v6q_checker")
    independent_report = v6q.verify(proof)
    independent = v6q._load_independent()
    diagonal = str(proof["diagonal"])
    claims = {str(row["record_id"]): row for row in proof["records"]}
    baseline = [independent._state_record(level, 0, "dispersed", diagonal) for level in LEVELS]
    producer_sequences = []
    producer_failures: list[str] = []
    for mask in MASKS:
        rows = [claims[f"N{level}:25PCT:{mask}:{diagonal}"] for level in LEVELS]
        sequence = independent._sequence(rows, baseline)
        sequence["diagonal"] = diagonal
        sequence["response_metric"] = "NODAL_UZ_RELATIVE_L2"
        producer_failures.extend(_failures(v6q, sequence))
        producer_sequences.append(sequence)
    independent_failures = sorted(independent_report["formal_failures"])
    producer_failures.sort()
    producer_sequences.sort(key=lambda row: tuple(row["record_ids"]))
    independent_sequences = sorted(
        independent_report["sequence_results"], key=lambda row: tuple(row["record_ids"])
    )
    producer_residuals = [
        float.fromhex(str(row["solve_residual_relative_inf_hex"])) for row in claims.values()
    ]
    if any(not math.isfinite(value) for value in producer_residuals):
        raise V6RCheckerError("nonfinite producer residual")
    decision_agreement = producer_failures == independent_failures
    return {
        "activation_authorized": False,
        "center_metric_classifying": False,
        "decision_agreement": decision_agreement,
        "diagonal": diagonal,
        "independent_formal_failure_count": len(independent_failures),
        "independent_formal_failures": independent_failures,
        "independent_sequence_results_sha256": sha256(canonical_bytes(independent_sequences)),
        "producer_formal_failure_count": len(producer_failures),
        "producer_formal_failures": producer_failures,
        "producer_sequence_results_sha256": sha256(canonical_bytes(producer_sequences)),
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "raw_metric_identity_disposition": "NONCLASSIFYING_DERIVED_BINARY_REPRODUCTION_DIAGNOSTIC",
        "raw_metric_identity_passed": independent_report["record_identity_passed"],
        "raw_metric_identity_worst_relative_inf_hex": independent_report["record_identity_worst_relative_inf_hex"],
        "record_count": 6,
        "residual_bound_passed": max(producer_residuals) <= 1.0e-8,
        "response_metric": "NODAL_UZ_RELATIVE_L2",
        "schema": SCHEMA,
        "scientific_gate_passed": decision_agreement and not producer_failures and not independent_failures,
        "sequence_count": 2,
        "thresholds": contract["thresholds"],
    }


def _exclusive(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-gate-decision", action="store_true", required=True)
    parser.add_argument("--proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    _exclusive(args.output, verify(args.proof))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
