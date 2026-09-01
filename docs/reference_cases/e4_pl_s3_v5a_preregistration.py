"""Standard-library validator for the S3 V5A MIN3 source-authority gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
SELECTION = REFERENCE / "e4_pl_s3_v5a_source_selection.json"
CONTRACT = REFERENCE / "e4_pl_s3_v5a_preregistration_contract.json"


def _reject_constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON constant: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
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
    raw = Path(path).read_bytes()
    value = json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_unique_object,
        parse_constant=_reject_constant,
    )
    if not isinstance(value, dict):
        raise ValueError(f"top-level JSON object required: {path}")
    if raw != canonical_bytes(value):
        raise ValueError(f"noncanonical JSON: {path}")
    return value


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def validate() -> dict[str, Any]:
    selection = load_canonical(SELECTION)
    contract = load_canonical(CONTRACT)
    if selection.get("schema") != "anysolver.e4-pl-s3-v5a-source-selection-v1":
        raise ValueError("source-selection schema mismatch")
    if contract.get("schema") != "anysolver.e4-pl-s3-v5a-preregistration-contract-v1":
        raise ValueError("preregistration-contract schema mismatch")

    candidate = selection.get("candidate", {})
    if candidate != {
        "formulation_id": "CANDIDATE_E4_PL_S3_V5A_MIN3_UNRELAXED_FLAT_LINEAR_SCREEN_V1",
        "implementation_status": "NOT_IMPLEMENTED",
        "relaxation_policy": "PHI_SQUARED_EXACTLY_ONE_FOR_SCREEN_ONLY",
        "selected_family": "MIN3_ANISOPARAMETRIC_MINDLIN",
    }:
        raise ValueError("candidate identity mismatch")

    authority = selection.get("equation_authority", {})
    if authority != {
        "complete_for_unrelaxed_local_interface_screen": True,
        "empirical_coefficient_fitting_forbidden": True,
        "relaxed_or_thin_regime_screen_authorized": False,
        "unresolved_term": "C_S_NUMERICAL_CONSTANT_IN_UHM_EQUATIONS_2_28B_C",
    }:
        raise ValueError("equation-authority disposition mismatch")
    if selection.get("stage") != "SOURCE_EQUATIONS_COMPLETE_FOR_UNRELAXED_SCREEN_ONLY":
        raise ValueError("source-selection stage mismatch")

    sources = selection.get("external_sources", [])
    if len(sources) != 3:
        raise ValueError("three source receipts required")
    required_authorities = {
        "IMPLEMENTATION_EQUATION_AUTHORITY",
        "INDEPENDENT_INTERPOLATION_EQUATION_MAP",
        "NASA_RESEARCH_PROGRAM_IDENTITY_AND_PERFORMANCE_CONTEXT",
    }
    if {row.get("authority") for row in sources} != required_authorities:
        raise ValueError("source-authority set mismatch")
    for row in sources:
        digest = row.get("sha256", "")
        if row.get("bytes", 0) <= 0 or len(digest) != 64 or any(char not in "0123456789ABCDEF" for char in digest):
            raise ValueError("invalid external source byte receipt")
        if not row.get("equation_groups") or not str(row.get("url", "")).startswith("https://"):
            raise ValueError("incomplete external source equation map")

    screen = selection.get("screen_scope", {})
    if screen.get("hard_gate_comparator") != "INDEPENDENT_CONTINUUM_PATCH_ACTION_AND_ENERGY":
        raise ValueError("patch comparator must be continuum-based")
    if screen.get("nonpatch_q4_dirichlet_to_neumann") != "DIAGNOSTIC_ONLY":
        raise ValueError("nonpatch Q4 comparison cannot classify V5A")
    if screen.get("relaxed_thin_regime") is not False or screen.get("isotropic_only") is not True:
        raise ValueError("unrelaxed screening boundary mismatch")

    execution = contract.get("execution", {})
    expected_bounds = {
        "child_wall_seconds": 600,
        "complete_wave_wall_seconds": 1800,
        "maximum_concurrent_workers": 3,
        "memory_limit_gib_per_process_tree": 24,
        "numerical_library_threads_per_worker": 1,
        "required_cycle_count": 2,
    }
    for key, expected in expected_bounds.items():
        if execution.get(key) != expected:
            raise ValueError(f"execution bound mismatch: {key}")
    if execution.get("no_automatic_retry") is not True:
        raise ValueError("automatic retry must remain forbidden")

    production = contract.get("production_boundary", {})
    expected_production = {
        "anymesh_untouched": True,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
        "s3_activation_authorized": False,
    }
    if production != expected_production:
        raise ValueError("production boundary mismatch")
    if contract.get("stage4a_rerun_authorized") is not False:
        raise ValueError("Stage 4A must remain unauthorized")

    for binding in contract.get("frozen_inputs", []):
        path = ROOT / binding["path"]
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing or invalid frozen input: {path}")
        if path.stat().st_size != binding["bytes"] or sha256_file(path) != binding["sha256"]:
            raise ValueError(f"frozen input mismatch: {path}")

    predecessor = load_canonical(REFERENCE / "e4_pl_s3_v4e_shear_diagnosis_status.json")
    if predecessor.get("terminal") != "UNCLASSIFIED_E4_PL_S3_V4E_SHEAR_FORMULATION_REPLACEMENT_REQUIRED":
        raise ValueError("V4E predecessor is not canonically closed")
    return {
        "activation_authorized": False,
        "candidate_id": candidate["formulation_id"],
        "contract_sha256": sha256_file(CONTRACT),
        "empirical_relaxation_authorized": False,
        "next_gate": "BOUNDED_V5A_UNRELAXED_MIN3_LOCAL_INTERFACE_SCREEN",
        "next_gate_authorized": True,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "relaxed_or_thin_regime_screen_authorized": False,
        "schema": "anysolver.e4-pl-s3-v5a-preregistration-result-v1",
        "source_selection_sha256": sha256_file(SELECTION),
        "stage4a_rerun_authorized": False,
        "terminal": "PROVISIONAL_GO_E4_PL_S3_V5A_UNRELAXED_LOCAL_INTERFACE_SCREEN",
    }


def exclusive_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical_bytes(value))
        stream.flush()
        os.fsync(stream.fileno())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    exclusive_write(args.output, validate())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
