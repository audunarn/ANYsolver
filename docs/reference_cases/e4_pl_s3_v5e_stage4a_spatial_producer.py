"""Produce complete V5E Stage 4A spatial-response shards."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import e4_pl_s3_v5d_response_metric_producer as v5d


CONTRACT = REFERENCE / "e4_pl_s3_v5e_stage4a_spatial_contract.json"
FORMULATION_ID = v5d.FORMULATION_ID
SCHEMA = "anysolver.e4-pl-s3-v5e-stage4a-spatial-shard-v1"
DIAGONALS = v5d.DIAGONALS
LEVELS = v5d.LEVELS
MASKS = v5d.MASKS
FRACTIONS = (1, 5, 10, 25)


class Stage4ASpatialError(RuntimeError):
    pass


canonical_bytes = v5d.canonical_bytes
sha256_bytes = v5d.sha256_bytes
sha256_file = v5d.sha256_file
exclusive_write = v5d.exclusive_write
load_canonical = v5d.v5c.load_canonical


def validate_authority() -> Mapping[str, Any]:
    contract = load_canonical(CONTRACT)
    if contract.get("schema") != "anysolver.e4-pl-s3-v5e-stage4a-spatial-contract-v1":
        raise Stage4ASpatialError("unexpected V5E contract schema")
    for binding in contract.get("frozen_inputs", []):
        path = ROOT / str(binding["path"])
        raw = path.read_bytes()
        if len(raw) != binding["bytes"] or sha256_bytes(raw) != binding["sha256"]:
            raise Stage4ASpatialError(f"frozen input mismatch: {path}")
    if contract.get("stage4a_execution_authorized") is not True or contract.get("activation_authorized") is not False:
        raise Stage4ASpatialError("V5E authority disposition mismatch")
    return contract


def _record(level: int, fraction: int, mask: str, diagonal: str) -> dict[str, Any]:
    # V5D's accepted implementation is fraction-independent.  Extend only its
    # registered catalog for this process; restore the frozen module state even
    # if reconstruction fails.
    original = v5d.FRACTIONS
    v5d.FRACTIONS = FRACTIONS
    try:
        return v5d._state_record(level, fraction, mask, diagonal)
    finally:
        v5d.FRACTIONS = original


def _specs(diagonal: str) -> list[tuple[int, int, str, str]]:
    if diagonal not in DIAGONALS:
        raise Stage4ASpatialError("unregistered diagonal")
    return [
        spec
        for level in LEVELS
        for spec in (
            (level, 0, "dispersed", diagonal),
            *((level, fraction, mask, diagonal) for mask in MASKS for fraction in FRACTIONS),
        )
    ]


def produce_shard(diagonal: str, progress: Path | None = None) -> dict[str, Any]:
    validate_authority()
    if progress is not None:
        progress.parent.mkdir(parents=True, exist_ok=True)
        progress.touch(exist_ok=False)
    records: list[dict[str, Any]] = []
    for sequence, spec in enumerate(_specs(diagonal), start=1):
        record = _record(*spec)
        records.append(record)
        if progress is not None:
            with progress.open("ab") as stream:
                stream.write(canonical_bytes({"record_id": record["record_id"], "sequence": sequence}))
    records.sort(key=lambda row: row["record_id"])
    ids = [row["record_id"] for row in records]
    return {
        "activation_authorized": False,
        "candidate_formulation_id": FORMULATION_ID,
        "center_metric_classifying": False,
        "contract_sha256": sha256_file(CONTRACT),
        "diagonal": diagonal,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "record_count": 27,
        "record_ids_sha256": sha256_bytes(canonical_bytes(ids)),
        "records": records,
        "response_metric": "NODAL_UZ_RELATIVE_L2",
        "schema": SCHEMA,
        "v5c_reclassified": False,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit-spatial-shard", action="store_true", required=True)
    parser.add_argument("--diagonal", choices=DIAGONALS, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--progress", type=Path)
    args = parser.parse_args(argv)
    exclusive_write(args.output, produce_shard(args.diagonal, args.progress))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
