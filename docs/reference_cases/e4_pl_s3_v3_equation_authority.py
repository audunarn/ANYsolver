"""Validate the independently structured MiSP3 V3A equation maps."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
MAP_A = ROOT / "docs/reference_cases/e4_pl_s3_v3_misp3_equation_map_a.json"
MAP_B = ROOT / "docs/reference_cases/e4_pl_s3_v3_misp3_equation_map_b.json"
CONTRACT = ROOT / "docs/reference_cases/e4_pl_s3_v3_equation_authority_contract.json"


def _reject_constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON constant: {value}")


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def canonical_bytes(value: Any) -> bytes:
    def walk(item: Any) -> None:
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("nonfinite value")
        if isinstance(item, dict):
            for child in item.values():
                walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)

    walk(value)
    return (
        json.dumps(value, allow_nan=False, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
        + "\n"
    ).encode("utf-8")


def load_canonical(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_object,
        parse_constant=_reject_constant,
    )
    if not isinstance(value, dict):
        raise ValueError(f"top-level object required: {path}")
    if canonical_bytes(value) != raw:
        raise ValueError(f"noncanonical JSON: {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


EXPECTED_ASSERTIONS = {
    "CONDENSED_BLOCK": "G_TRANSPOSE_H_INVERSE_G",
    "COUPLING_SIGN": "PLUS_M_TRANSPOSE_G_X_IN_FIRST_EQUATION",
    "CURVATURE_ENGINEERING": "THETA_Y_X;NEG_THETA_X_Y;THETA_Y_Y_MINUS_THETA_X_X",
    "DIRECTOR_REVERSAL": "BOUNDED_SCREEN_OBLIGATION",
    "DISCRETE_SHEAR": "GAMMA_H_EQUALS_DIV_H_M_H",
    "EXACT_INTEGRATION_DEGREE": "2",
    "FLEXURAL_NODAL_DIMENSION": "9",
    "GENERALIZED_SECTION": "NOT_AUTHORIZED",
    "LOCAL_ELIMINATION": "ELEMENT_LOCAL_9_BY_9_MOMENT_BLOCK",
    "MOMENT_SIGN": "M_EQUALS_NEGATIVE_D_EPS_BETA",
    "PL_COMPLETION": "SEPARATE_AFTER_PHYSICAL_SCREEN",
    "Q4_COMPATIBILITY": "NOT_PROVEN",
    "REDUCTION_SPACE_DIMENSION": "3",
    "SHEAR_ENGINEERING": "W_X_MINUS_THETA_Y;W_Y_PLUS_THETA_X",
    "SHEAR_SIGN": "GAMMA_EQUALS_LAMBDA_T_MINUS2_GRAD_W_MINUS_BETA",
    "SHELL_BETA_MAP": "BETA_X_EQUALS_THETA_Y;BETA_Y_EQUALS_NEGATIVE_THETA_X",
    "THEOREM_SCOPE": "CLAMPED_ISOTROPIC_REGULAR_TRIANGULAR_MESH_T_IN_0_1",
}


def validate() -> dict[str, Any]:
    map_a = load_canonical(MAP_A)
    map_b = load_canonical(MAP_B)
    contract = load_canonical(CONTRACT)
    if map_a.get("schema") != "anysolver.e4-pl-s3-v3-misp3-equation-map-a-v1":
        raise ValueError("map A schema mismatch")
    if map_b.get("schema") != "anysolver.e4-pl-s3-v3-misp3-equation-map-b-v1":
        raise ValueError("map B schema mismatch")
    if contract.get("schema") != "anysolver.e4-pl-s3-v3-equation-authority-contract-v1":
        raise ValueError("contract schema mismatch")
    authors_a = map_a.get("authorship", {})
    authors_b = map_b.get("authorship", {})
    if authors_a.get("derived_from_other_map") is not False or authors_b.get("derived_from_other_map") is not False:
        raise ValueError("equation maps must be independently derived")
    if authors_a.get("map_id") == authors_b.get("map_id") or authors_a.get("method") == authors_b.get("method"):
        raise ValueError("independent map identities and methods required")
    source_a = map_a.get("source", {})
    source_b = map_b.get("source_authority", {})
    for source in (source_a, source_b):
        if source.get("bytes") != 233802:
            raise ValueError("primary source byte count mismatch")
        if source.get("sha256") != "19F5B2FE37048D84A95995F15BB9289EC14796D77EED0CF90BD266EB4A6C487C":
            raise ValueError("primary source hash mismatch")
        if source.get("version") != "ARXIV_1410_3683_V1":
            raise ValueError("primary source version mismatch")
    claims_a = {row["id"]: row["value"] for row in map_a.get("reconciliation_claims", [])}
    if len(claims_a) != len(map_a.get("reconciliation_claims", [])):
        raise ValueError("duplicate reconciliation claim in map A")
    claims_b = map_b.get("audit_assertions")
    if claims_a != claims_b or claims_a != EXPECTED_ASSERTIONS:
        raise ValueError("independent equation maps disagree")
    required_printed = {"2.3", "2.4", "2.5", "2.6", "2.7-2.8", "2.9", "2.10"}
    if not required_printed <= set(map_a.get("printed_equations", {})):
        raise ValueError("printed equation coverage incomplete")
    required_discrete = {"3.1", "3.2", "3.3", "3.4-3.6", "3.7", "3.8-3.9", "3.10", "3.11", "3.12", "3.13", "3.14"}
    if set(map_a.get("discrete_system", {})) != required_discrete:
        raise ValueError("discrete equation coverage mismatch")
    if set(map_a.get("theorem_map", {})) != {"4.7", "4.10", "limitations"}:
        raise ValueError("theorem coverage mismatch")
    if map_b.get("coordinate_realization", {}).get("exact_integration", {}).get("maximum_degree") != 2:
        raise ValueError("exact integration derivation mismatch")
    if map_b.get("block_construction", {}).get("physical_condensation", {}).get("definition") != "K_FLEX_EQUALS_G_TRANSPOSE_H_INVERSE_G":
        raise ValueError("Schur sign or order mismatch")
    if "MIXED_Q4_COMPATIBILITY_CLAIM" not in map_a.get("scope", {}).get("excluded", []):
        raise ValueError("Q4 compatibility must remain excluded")
    if "STAGE4A_RERUN" not in map_b.get("implementation_boundaries", {}).get("not_authorized", []):
        raise ValueError("Stage 4A must remain unauthorized")
    if contract.get("next_gate") != "BOUNDED_V3A_LOCAL_AND_MACROCELL_IMPLEMENTATION_SCREEN":
        raise ValueError("next gate mismatch")
    if contract.get("next_gate_authorized") is not True or contract.get("stage4a_rerun_authorized") is not False:
        raise ValueError("authority disposition mismatch")
    expected_boundary = {
        "anymesh_untouched": True,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
        "s3_activation_authorized": False,
    }
    if contract.get("production_boundary") != expected_boundary:
        raise ValueError("production boundary mismatch")
    for binding in contract.get("frozen_inputs", []):
        path = ROOT / binding["path"]
        if not path.is_file():
            raise ValueError(f"missing frozen input: {path}")
        if path.stat().st_size != binding["bytes"] or sha256(path) != binding["sha256"]:
            raise ValueError(f"frozen input mismatch: {path}")
    return {
        "activation_authorized": False,
        "assertion_count": len(EXPECTED_ASSERTIONS),
        "candidate_id": "CANDIDATE_E4_PL_S3_V3A_MISP3_HR_FLAT_LINEAR_V1",
        "equation_maps_agree": True,
        "next_gate": contract["next_gate"],
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": "anysolver.e4-pl-s3-v3-equation-authority-validation-v1",
        "stage4a_rerun_authorized": False,
        "terminal": "PASS_E4_PL_S3_V3A_EQUATION_AUTHORITY",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = canonical_bytes(validate())
    if args.output is None:
        os.write(1, payload)
        return 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
