"""Independent checker for the research-only V4B drill-release screen."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
if str(REFERENCE) not in sys.path:
    sys.path.insert(0, str(REFERENCE))

import e4_pl_s3_v4a_screen_checker as independent_q4


CONTRACT = REFERENCE / "e4_pl_s3_v4b_screen_contract.json"
FORMULATION_ID = "CANDIDATE_E4_PL_S3_V4B_Q4_SUBCELL_DRILL_RELEASE_FLAT_LINEAR_V1"
PROOF_SCHEMA = "anysolver.e4-pl-s3-v4b-drill-release-screen-proof-v1"
CHECK_SCHEMA = "anysolver.e4-pl-s3-v4b-drill-release-screen-check-v1"

canonical_bytes = independent_q4.canonical_bytes
sha256_file = independent_q4.sha256_file
load_document = independent_q4.load_document
_decode = independent_q4._decode
_relative_inf = independent_q4._relative_inf
_rank = independent_q4._rank


def reconstruct(vertices: np.ndarray, normal: np.ndarray) -> dict[str, np.ndarray]:
    points = np.empty((7, 3), dtype=np.float64)
    points[:3] = vertices
    points[3] = 0.5 * (vertices[0] + vertices[1])
    points[4] = 0.5 * (vertices[1] + vertices[2])
    points[5] = 0.5 * (vertices[2] + vertices[0])
    points[6] = (vertices[0] + vertices[1] + vertices[2]) / 3.0
    assembled = {name: np.zeros((42, 42), dtype=np.float64) for name in ("physical", "pl", "hourglass", "total")}
    for connectivity in ((0, 3, 6, 5), (1, 4, 6, 3), (2, 5, 6, 4)):
        local = independent_q4._q4(points[np.asarray(connectivity)], normal)
        for name, matrix in assembled.items():
            independent_q4._scatter(matrix, local[name], connectivity)
    restriction = np.zeros((42, 27), dtype=np.float64)
    for node in range(3):
        restriction[6 * node : 6 * node + 6, 6 * node : 6 * node + 6] = np.eye(6)
    for edge, endpoints in enumerate(((0, 1), (1, 2), (2, 0))):
        point = edge + 3
        for component in range(5):
            restriction[6 * point + component, 6 * endpoints[0] + component] = 0.5
            restriction[6 * point + component, 6 * endpoints[1] + component] = 0.5
        restriction[6 * point + 5, 18 + edge] = 1.0
    restriction[36:42, 21:27] = np.eye(6)
    restricted = {name: restriction.T @ matrix @ restriction for name, matrix in assembled.items()}
    internal_block = restricted["total"][18:, 18:]
    internal_map = -np.linalg.solve(internal_block, restricted["total"][18:, :18])
    transform = np.vstack((np.eye(18), internal_map))
    condensed: dict[str, np.ndarray] = {}
    for name, matrix in restricted.items():
        value = transform.T @ matrix @ transform
        condensed[name] = 0.5 * (value + value.T)
    return condensed | {"internal_block": internal_block, "internal_map": internal_map, "restriction": restriction}


def verify(proof: Mapping[str, Any]) -> dict[str, Any]:
    if proof.get("schema") != PROOF_SCHEMA or proof.get("candidate_formulation_id") != FORMULATION_ID:
        raise ValueError("unexpected V4B proof identity")
    contract = load_document(CONTRACT)
    if proof.get("contract_sha256") != sha256_file(CONTRACT):
        raise ValueError("proof contract hash mismatch")
    if proof.get("production_boundary") != {
        "anymesh_untouched": True,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
    }:
        raise ValueError("production boundary mismatch")
    if proof.get("stage4a_rerun_authorized") is not False:
        raise ValueError("proof improperly authorizes Stage 4A")
    vertices = np.asarray(((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.2, 0.9, 0.0)))
    expected = reconstruct(vertices, np.asarray((0.0, 0.0, 1.0)))
    payloads = proof["local"]["payloads"]
    worst = 0.0
    for name, value in expected.items():
        worst = max(worst, _relative_inf(_decode(payloads[name]), value))
    internal_rank = _rank(expected["internal_block"], 1.0e-12)
    physical_rank = _rank(expected["physical"], 1.0e-10)
    total_rank = _rank(expected["total"], 1.0e-10)
    rigid_residual = float(
        np.linalg.norm(expected["total"] @ independent_q4._rigid(vertices), ord=np.inf)
        / max(np.linalg.norm(expected["total"], ord=np.inf), 1.0)
    )
    component_sum = _relative_inf(expected["physical"] + expected["pl"] + expected["hourglass"], expected["total"])
    symmetry = _relative_inf(expected["total"], expected["total"].T)
    construction = bool(internal_rank == 9 and worst <= 3.0e-13 and component_sum <= 3.0e-13)
    local_passed = bool(construction and physical_rank == 9 and total_rank == 12 and rigid_residual <= 3.0e-12 and symmetry <= 3.0e-13)
    later_stages_absent = bool(
        proof.get("later_stages") == "NOT_EXECUTED_LOCAL_GATE_FAILED"
        and proof.get("macrocell") == {}
        and proof.get("development_records") == []
    )
    return {
        "authority_complete": contract.get("schema") == "anysolver.e4-pl-s3-v4b-drill-release-screen-contract-v1",
        "candidate_formulation_id": FORMULATION_ID,
        "construction_identity_passed": construction,
        "independent_component_sum_relative_inf_hex": component_sum.hex(),
        "independent_internal_total_block_rank": internal_rank,
        "independent_local_identity_worst_relative_inf_hex": worst.hex(),
        "independent_physical_rank": physical_rank,
        "independent_rigid_residual_relative_inf_hex": rigid_residual.hex(),
        "independent_symmetry_relative_inf_hex": symmetry.hex(),
        "independent_total_rank": total_rank,
        "later_stages_absent": later_stages_absent,
        "local_operator_passed": local_passed,
        "mixed_interface_passed": False,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": CHECK_SCHEMA,
    }


def exclusive_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-proof", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    exclusive_write(args.output, verify(load_document(args.verify_proof)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
