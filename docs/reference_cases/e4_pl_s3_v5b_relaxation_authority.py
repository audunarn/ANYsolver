"""Standard-library validator for the S3 V5B MIN3 relaxation authority."""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "docs" / "reference_cases"
SELECTION = REFERENCE / "e4_pl_s3_v5b_relaxation_source_selection.json"
CONTRACT = REFERENCE / "e4_pl_s3_v5b_relaxation_authority_contract.json"


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


def relaxation_from_uhm(alpha: Fraction, c_s: Fraction = Fraction(1, 2)) -> Fraction:
    if alpha <= 0 or c_s <= 0:
        raise ValueError("positive alpha and C_s required")
    return Fraction(1, 1) / (Fraction(1, 1) + c_s * alpha)


def relaxation_from_mystran(alpha: Fraction, cbmin3: Fraction = Fraction(2, 1)) -> Fraction:
    if alpha <= 0 or cbmin3 <= 0:
        raise ValueError("positive alpha and CBMIN3 required")
    psi_hat = Fraction(1, 1) / alpha
    return cbmin3 * psi_hat / (Fraction(1, 1) + cbmin3 * psi_hat)


def validate() -> dict[str, Any]:
    selection = load_canonical(SELECTION)
    contract = load_canonical(CONTRACT)
    if selection.get("schema") != "anysolver.e4-pl-s3-v5b-relaxation-source-selection-v1":
        raise ValueError("source-selection schema mismatch")
    if contract.get("schema") != "anysolver.e4-pl-s3-v5b-relaxation-authority-contract-v1":
        raise ValueError("authority-contract schema mismatch")

    candidate = selection.get("candidate", {})
    if candidate != {
        "formulation_id": "CANDIDATE_E4_PL_S3_V5B_MIN3_RELAXED_FLAT_LINEAR_SCREEN_V1",
        "implementation_status": "NOT_IMPLEMENTED",
        "relaxation_policy": "SOURCE_BOUND_MIN3_DIAGONAL_SUM_RELAXATION",
        "selected_family": "MIN3_ANISOPARAMETRIC_MINDLIN",
    }:
        raise ValueError("candidate identity mismatch")

    equation = selection.get("equation_authority", {})
    if equation != {
        "coefficient_fitting_forbidden": True,
        "complete_for_bounded_relaxed_repair_funnel": True,
        "mystran_cbmin3": "2",
        "uhm_c_s": "1/2",
    }:
        raise ValueError("relaxation equation authority mismatch")

    mapping = selection.get("exact_mapping", {})
    if mapping.get("domain") != ["BENSUM>0", "SHRSUM>0"]:
        raise ValueError("relaxation domain mismatch")
    if mapping.get("mystran") != {
        "phi_squared": "CBMIN3*PSI_HAT/(1+CBMIN3*PSI_HAT)",
        "psi_hat": "BENSUM/SHRSUM",
    }:
        raise ValueError("MYSTRAN equation map mismatch")
    if mapping.get("uhm") != {
        "alpha": "SHRSUM/BENSUM",
        "phi_squared": "1/(1+C_S*ALPHA)",
    }:
        raise ValueError("UHM equation map mismatch")
    for alpha in (Fraction(1, 7), Fraction(1, 1), Fraction(9, 4), Fraction(113, 17)):
        if relaxation_from_uhm(alpha) != relaxation_from_mystran(alpha):
            raise ValueError("exact relaxation mapping failed")

    sources = selection.get("external_sources", [])
    if len(sources) != 3:
        raise ValueError("three external source groups required")
    if {row.get("authority") for row in sources} != {
        "PRIMARY_MIN3_FIELD_AND_RELAXATION_LAW",
        "OFFICIAL_MIN3_RELAXATION_IMPLEMENTATION",
        "OFFICIAL_USER_MANUAL_PARAMETER_AND_REFERENCE_IDENTITY",
    }:
        raise ValueError("source-authority set mismatch")
    for source in sources:
        if not str(source.get("url", source.get("repository", ""))).startswith("https://"):
            raise ValueError("source URL missing")
        files = source.get("files")
        if files is None:
            if source.get("bytes", 0) <= 0 or len(source.get("sha256", "")) != 64:
                raise ValueError("invalid primary source receipt")
            continue
        if not source.get("commit") or not source.get("tree") or not files:
            raise ValueError("incomplete repository identity")
        paths: set[str] = set()
        for item in files:
            path = item.get("path", "")
            digest = item.get("sha256", "")
            if path in paths or not path or item.get("bytes", 0) <= 0:
                raise ValueError("duplicate or incomplete source file")
            paths.add(path)
            if len(digest) != 64 or any(char not in "0123456789ABCDEF" for char in digest):
                raise ValueError("invalid source SHA-256")
            if len(item.get("blob", "")) != 40 or not item.get("role"):
                raise ValueError("invalid source blob binding")

    predecessor = load_canonical(REFERENCE / "e4_pl_s3_v5a_screen_status.json")
    if predecessor.get("terminal") != "UNCLASSIFIED_E4_PL_S3_V5A_RELAXATION_AUTHORITY_REQUIRED":
        raise ValueError("V5A predecessor is not canonically closed")
    if predecessor.get("next_gate") != "V5B_RELAXATION_EQUATION_AUTHORITY":
        raise ValueError("V5A next-gate mismatch")

    execution = contract.get("execution", {})
    if execution != {
        "child_wall_seconds": 600,
        "complete_wave_wall_seconds": 1800,
        "maximum_concurrent_workers": 3,
        "memory_limit_gib_per_process_tree": 24,
        "no_automatic_retry": True,
        "numerical_library_threads_per_worker": 1,
        "required_cycle_count": 2,
    }:
        raise ValueError("execution bounds mismatch")
    production = contract.get("production_boundary", {})
    if production != {
        "anymesh_untouched": True,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
        "s3_activation_authorized": False,
    }:
        raise ValueError("production boundary mismatch")
    if contract.get("stage4a_rerun_authorized") is not False:
        raise ValueError("Stage 4A must remain unauthorized")

    for binding in contract.get("frozen_inputs", []):
        path = ROOT / binding["path"]
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing or invalid frozen input: {path}")
        if path.stat().st_size != binding["bytes"] or sha256_file(path) != binding["sha256"]:
            raise ValueError(f"frozen input mismatch: {path}")

    return {
        "activation_authorized": False,
        "candidate_id": candidate["formulation_id"],
        "contract_sha256": sha256_file(CONTRACT),
        "empirical_coefficient_fitting_authorized": False,
        "exact_parameter_map": {"mystran_cbmin3": "2", "uhm_c_s": "1/2"},
        "next_gate": "BOUNDED_V5B_RELAXED_LOCAL_INTERFACE_THIN_SCREEN",
        "next_gate_authorized": True,
        "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
        "schema": "anysolver.e4-pl-s3-v5b-relaxation-authority-result-v1",
        "source_selection_sha256": sha256_file(SELECTION),
        "stage4a_rerun_authorized": False,
        "terminal": "PROVISIONAL_GO_E4_PL_S3_V5B_RELAXED_REPAIR_FUNNEL",
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
