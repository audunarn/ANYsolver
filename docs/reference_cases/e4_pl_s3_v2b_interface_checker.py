"""Independent checker for the bounded S3 V2B mixed-interface proof."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

from e4_pl_s3_v2_independent_checker import _assemble_f, _isotropic_section_f


SCHEMA = "anysolver.e4-pl-s3-v2b-interface-check-v1"
EXPECTED_NOGO_SHA256 = "47CD9DEF9AC306635C16B662ECBF3628324350CCC80803D1AC586BC0A22D60F1"
YOUNG = 210.0e9
POISSON = 0.3
THICKNESS = 0.08


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _reject_duplicate(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key {key!r}")
        result[key] = value
    return result


def load_document(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_reject_duplicate, parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    if raw != canonical_bytes(value):
        raise ValueError("proof is not canonical JSON")
    return value


def decode_array(value: Mapping[str, Any]) -> np.ndarray:
    values = list(value["values_hex"])
    if sha256_bytes(canonical_bytes(values)) != value["sha256"]:
        raise ValueError("matrix payload hash mismatch")
    return np.asarray([float.fromhex(str(item)) for item in values], dtype=np.float64).reshape(tuple(value["shape"]))


def _embed(matrix: np.ndarray, node_ids: Sequence[int]) -> np.ndarray:
    result = np.zeros((24, 24), dtype=np.float64)
    for i, node_i in enumerate(node_ids):
        for j, node_j in enumerate(node_ids):
            result[6 * (node_i - 1) : 6 * node_i, 6 * (node_j - 1) : 6 * node_j] += matrix[6 * i : 6 * i + 6, 6 * j : 6 * j + 6]
    return result


def _independent_pair(diagonal: str) -> dict[str, np.ndarray]:
    xy = {1: (0.0, 0.0), 2: (1.0, 0.0), 3: (1.0, 1.0), 4: (0.0, 1.0)}
    connectivity = ((1, 2, 3), (1, 3, 4)) if diagonal in {"backslash", "alternating"} else ((1, 2, 4), (2, 3, 4))
    section = _isotropic_section_f(YOUNG, POISSON, THICKNESS)
    result = {name: np.zeros((24, 24), dtype=np.float64) for name in ("physical", "pl", "total")}
    for nodes in connectivity:
        made = _assemble_f([xy[node] for node in nodes], section)
        result["physical"] += _embed(np.asarray(made["physical"]), nodes)
        result["pl"] += _embed(np.asarray(made["pl"]), nodes)
        result["total"] += _embed(np.asarray(made["condensed"]), nodes)
    return result


def verify(proof: Mapping[str, Any]) -> dict[str, Any]:
    if proof.get("schema") != "anysolver.e4-pl-s3-v2b-interface-proof-v1":
        raise ValueError("unexpected proof schema")
    worst = 0.0
    mismatch_nonzero = False
    for diagonal in ("slash", "backslash", "alternating"):
        independent = _independent_pair(diagonal)
        matrices = proof["matrices"][diagonal]
        for name in ("physical", "pl", "total"):
            produced = decode_array(matrices[f"s3_{name}"])
            expected = independent[name]
            residual = float(np.linalg.norm(produced - expected, ord=np.inf) / max(np.linalg.norm(expected, ord=np.inf), 1.0))
            worst = max(worst, residual)
        q4 = decode_array(matrices["q4_total"])
        s3 = decode_array(matrices["s3_total"])
        mismatch_nonzero = mismatch_nonzero or not np.array_equal(q4, s3)
    status = json.loads((REFERENCE / "e4_pl_s3_v2_stage4a_nogo_status.json").read_text(encoding="ascii"))
    bound = status["aggregate"]["sha256"] == EXPECTED_NOGO_SHA256 and status["terminal"] == "NO_GO_E4_PL_S3_V2A_MIXED_FLEXURAL_CONVERGENCE"
    development = {row["record_id"]: row for row in proof["development_records"]}
    nonmonotone = False
    if development:
        for fraction in (5, 10):
            coarse = float(development[f"N20:{fraction}PCT:dispersed:slash"]["response"]["relative_error"])
            fine = float(development[f"N40:{fraction}PCT:dispersed:slash"]["response"]["relative_error"])
            nonmonotone = nonmonotone or fine > 1.02 * coarse
    return {
        "development_successive_response_failed": bool(nonmonotone),
        "macrocell_operator_mismatch_nonzero": bool(mismatch_nonzero),
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": SCHEMA,
        "source_equation_agreement": bool(worst <= 3.0e-13),
        "source_equation_worst_relative_inf_hex": worst.hex(),
        "v2a_mixed_no_go_bound": bool(bound),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    report = verify(load_document(args.verify_proof))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(canonical_bytes(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
