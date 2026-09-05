"""Bounded non-resource runner for the GE-B3 P4 curved-reference gate."""

from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import time
from typing import Any


CANDIDATE_ID = "CANDIDATE_GE_BEAM3_DC_MIXED_CURVED_Q2_MACRO_V1"
SCHEMA = "anysolver.ge-beam3-curved-p4-reference-aggregate-v2"
RUNNER_ID = "P4_TWO_CYCLE_BOUNDED_REFERENCE_RUNNER_V2"
PROOF_SCHEMA = "anysolver.ge-beam3-curved-p4-reference-proof-v2"
CHECK_SCHEMA = "anysolver.ge-beam3-curved-p4-reference-check-v2"
AUTHORITY_SCHEMA = "anysolver.ge-beam3-curved-p4-run-authority-manifest-v1"
DISPOSABLE_MODE = "DISPOSABLE_REHEARSAL"
BLOCKED = "BLOCKED_GE_BEAM3_P4_REFERENCE_PROCESS_OR_EVIDENCE"
PASS = "PROVISIONAL_GO_GE_BEAM3_P4_PRIVATE_CURVED_REFERENCE_CORE"
NO_GO_REGULARITY = "NO_GO_GE_BEAM3_P4_REFERENCE_REGULARITY"
NO_GO_FRAME = "NO_GO_GE_BEAM3_P4_REFERENCE_FRAME_IDENTITY"
NO_GO_COVARIANCE = "NO_GO_GE_BEAM3_P4_REFERENCE_REVERSAL_OR_OBJECTIVITY"
RESTRICTION = "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
DEFAULT_CHILD_TIMEOUT_SECONDS = 600.0
DEFAULT_WAVE_TIMEOUT_SECONDS = 1800.0
DEFAULT_INACTIVITY_SECONDS = 300.0
DEFAULT_MEMORY_LIMIT_BYTES = 24 * (1 << 30)
REGISTERED_CASE_IDS = (
    "P2_BASIS_AND_DERIVATIVE_IDENTITY",
    "P2_NODAL_INTERPOLATION",
    "ANALYTIC_INTERVAL_REGULARITY",
    "STRAIGHT_REFERENCE_LIMIT",
    "PLANAR_SHALLOW_ARCH",
    "PLANAR_DEEP_ARCH",
    "ASYMMETRIC_PLANAR_CURVE",
    "TRANSFORMED_AND_SCALED_COPIES",
    "INITIALLY_TWISTED_CURVE",
    "MULTIELEMENT_SPATIAL_CHAIN",
    "CURVED_STIFFENER_SEGMENT",
    "AUTHORITATIVE_ANISOTROPIC_ROLL",
    "RIGID_REFERENCE_OBJECTIVITY",
    "CONNECTIVITY_REVERSAL",
    "FRAME_CONTINUITY",
    "ZERO_INTRINSIC_REFERENCE_STRAINS",
    "COINCIDENT_NODE_REJECTION",
    "ZERO_TANGENT_REJECTION",
    "NEAR_FOLD_REJECTION",
    "HALF_FRAME_BRANCH_CUTOFF_REJECTION",
    "TRIAD_TANGENT_MISMATCH_REJECTION",
    "IMPROPER_TRIAD_REJECTION",
    "RING_SEAM_MISMATCH_REJECTION",
    "CANONICAL_SERIALIZATION_AND_MUTATION",
    "STRAIGHT_CORE_BLOB_FREEZE",
    "PRODUCTION_BOUNDARY",
)
POSITIVE_FIXTURE_IDS = (
    "STRAIGHT_LIMIT",
    "PLANAR_SHALLOW",
    "PLANAR_DEEP",
    "PLANAR_ASYMMETRIC",
    "INITIALLY_TWISTED",
    "EMBEDDED_SPATIAL_PLANE",
)
STATION_SCHEDULE = (
    (-1.0, "VALUE"),
    (-0.75, "VALUE"),
    (-0.25, "VALUE"),
    (0.0, "LEFT"),
    (0.0, "RIGHT"),
    (0.25, "VALUE"),
    (0.75, "VALUE"),
    (1.0, "VALUE"),
)
NEGATIVE_FIXTURE_IDS = (
    "COINCIDENT_1_2",
    "FOLDED_ZERO_TANGENT",
    "NEAR_FOLD_SCALE_1E_NEG8",
    "NEAR_FOLD_SCALE_1",
    "NEAR_FOLD_SCALE_1E8",
    "TANGENT_TURN_0P91_PI",
    "RESIDUAL_ROLL_PI",
    "WRONG_FIRST_AXIS",
    "REFLECTED_TRIAD",
    "NONORTHOGONAL_TRIAD",
    "NONFINITE_TRIAD",
)
REGISTERED_MUTATION_COVERAGE = {
    "AUTHORITY_ARTIFACT_HASH": 18,
    "HALF_ORDERING": 1,
    "NODE": 3,
    "P2_DERIVATIVE_COEFFICIENT": 15,
    "P2_SHAPE_COEFFICIENT": 15,
    "PRODUCTION_SOURCE_HASH": 1,
    "REVERSAL_MAP": 1,
    "ROLL_SIGN": 2,
    "TANGENT_SIGN": 1,
    "TRIAD": 3,
}
REGISTERED_MUTATION_COUNT = 60
REGISTERED_MUTATION_ORDER_SHA256 = (
    "3E5C18031BA051D829E29D905200B82A97B9A49ADE0857B343DC84234674C918"
)
COMMIT_AUTHORITIES = (
    {
        "commit": "5cf0fc884685b454ea645c2052c7cba60c66cbbb",
        "parent": "8ac156cbb7632f2442f904e3ab73d6a7eb867670",
        "role": "PREREGISTRATION",
        "subject": "docs: preregister GE Beam3 curved P4 reference core",
        "tree": "d2a9ccd5db3e4fee25fb1be07a49fceceb887bd5",
    },
    {
        "commit": "214d6de76795bb7d656dc377166bd05cc35c6a3f",
        "parent": "5cf0fc884685b454ea645c2052c7cba60c66cbbb",
        "role": "REFERENCE_CORE_INITIAL",
        "subject": "feat: add private GE Beam3 curved P4 reference core",
        "tree": "4cb6fc861edf721fcb246fb521a64b24aa58eeab",
    },
    {
        "commit": "d59ed224cabae23fac4ef68a74bc53ef5602b3db",
        "parent": "214d6de76795bb7d656dc377166bd05cc35c6a3f",
        "role": "REFERENCE_CORE_CORRECTION",
        "subject": "fix: align GE Beam3 curved frame admission",
        "tree": "2235c5f868384f0122ec5eda766cdf01c0923a1f",
    },
    {
        "commit": "8fcf827b6e5364f0e1bc8221a3f74602e3f39261",
        "parent": "d59ed224cabae23fac4ef68a74bc53ef5602b3db",
        "role": "IMPLEMENTATION_REVIEW",
        "subject": "docs: accept corrected GE Beam3 curved P4 reference core",
        "tree": "61001446006971d32ac3294800f3760ba43df948",
    },
)
AUTHORITY_INPUT_PATHS = (
    "docs/agent_plans/GE_BEAM3_CURVED_P4_REFERENCE_CORE_PLAN.md",
    "docs/reference_cases/ge_beam3_curved_p4_baseline.json",
    "docs/reference_cases/ge_beam3_curved_p4_cases.json",
    "docs/reference_cases/ge_beam3_curved_p4_contract.json",
    "docs/reference_cases/ge_beam3_curved_p4_equation_map_a.json",
    "docs/reference_cases/ge_beam3_curved_p4_equation_map_b.json",
    "docs/reference_cases/ge_beam3_curved_p4_implementation_review.json",
    "docs/reference_cases/ge_beam3_curved_p4_plan_review.json",
    "docs/reference_cases/ge_beam3_curved_p4_reference_checker.py",
    "docs/reference_cases/ge_beam3_curved_p4_reference_producer.py",
    "docs/reference_cases/ge_beam3_curved_p4_reference_runner.py",
    "docs/reference_cases/ge_beam3_curved_p4_reference_schema.json",
    "docs/reference_cases/ge_beam3_curved_p4_source_ledger.json",
    "src/anysolver/ge_beam3_curved_reference.py",
    "tests/test_ge_beam3_curved_p4_formal_runner.py",
    "tests/test_ge_beam3_curved_p4_implementation_review.py",
    "tests/test_ge_beam3_curved_p4_preregistration.py",
    "tests/test_ge_beam3_curved_p4_reference.py",
)
PROTECTED_STRAIGHT_BLOBS = {
    "pyproject.toml": "16da1c1ca1be9f56de4c0c3505cdfabb8752bd99",
    "src/anysolver/__init__.py": "2aa4911f538b6cb08e66dbb4590d0d1545dd7560",
    "src/anysolver/elements.py": "4dfe4212b9ee9947969b087809e72b9973e88e07",
    "src/anysolver/ge_beam3_element.py": "70542da7fea26dcb2da5b5f9da5fc0b0b8d484ab",
    "src/anysolver/ge_beam3_mixed_element.py": "f49062b55b4bf749a1654100cf3a4ed6ffb61d37",
    "src/anysolver/ge_beam3_mixed_state.py": "74caa1814448245f907bd3efdb6c8a1cc1d2269d",
    "src/anysolver/ge_beam3_state.py": "ba8f65761197c62cb2b7ce74bf488e75f2c24818",
}
REFERENCE_BOUNDARY_PATHS = {
    "docs/agent_plans/GE_BEAM3_CURVED_P4_REFERENCE_CORE_PLAN.md",
    "docs/reference_cases/ge_beam3_curved_p4_baseline.json",
    "docs/reference_cases/ge_beam3_curved_p4_cases.json",
    "docs/reference_cases/ge_beam3_curved_p4_contract.json",
    "docs/reference_cases/ge_beam3_curved_p4_equation_map_a.json",
    "docs/reference_cases/ge_beam3_curved_p4_equation_map_b.json",
    "docs/reference_cases/ge_beam3_curved_p4_implementation_review.json",
    "docs/reference_cases/ge_beam3_curved_p4_plan_review.json",
    "docs/reference_cases/ge_beam3_curved_p4_reference_schema.json",
    "docs/reference_cases/ge_beam3_curved_p4_source_ledger.json",
    "src/anysolver/ge_beam3_curved_reference.py",
    "tests/test_ge_beam3_curved_p4_implementation_review.py",
    "tests/test_ge_beam3_curved_p4_preregistration.py",
    "tests/test_ge_beam3_curved_p4_reference.py",
}
class RunnerError(RuntimeError):
    pass


@dataclass(frozen=True)
class ChildResult:
    returncode: int
    status: str
    stdout_sha256: str
    stderr_sha256: str


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("ascii")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def _canonical_file_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    normalized = raw.replace(b"\r\n", b"\n")
    if b"\r" in normalized:
        raise RunnerError(f"noncanonical carriage return in {path}")
    return normalized


def _write_exclusive(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(_canonical_bytes(value))


def _strict_canonical(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, member in pairs:
            if key in result:
                raise RunnerError(f"duplicate JSON key: {key}")
            result[key] = member
        return result

    def reject_constant(value: str) -> None:
        raise RunnerError(f"nonfinite JSON value: {value}")

    value = json.loads(
        raw.decode("ascii"),
        object_pairs_hook=unique,
        parse_constant=reject_constant,
    )
    if not isinstance(value, dict) or raw != _canonical_bytes(value):
        raise RunnerError(f"{path.name} is not canonical JSON")
    return raw, value


def _checker_outputs_agree(paths: list[Path]) -> bool:
    if len(paths) != 2 or not all(path.is_file() for path in paths):
        return False
    payloads = [_strict_canonical(path)[0] for path in paths]
    return payloads[0] == payloads[1]


def _binary64(value: float) -> str:
    made = float(value)
    if made == 0.0:
        made = 0.0
    return made.hex()


def _manifest_input(manifest: dict[str, Any], suffix: str) -> dict[str, Any]:
    rows = [row for row in manifest["inputs"] if str(row["path"]).endswith(suffix)]
    if len(rows) != 1:
        raise RunnerError(f"authority manifest must bind exactly one {suffix}")
    return dict(rows[0])


def _mutation_target(path: tuple[str | int, ...]) -> str:
    made = "$"
    for component in path:
        made += f"[{component}]" if isinstance(component, int) else f".{component}"
    return made


def _registered_mutation_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []

    def add(
        mutation_id: str,
        category: str,
        path: tuple[str | int, ...],
        operation: str,
    ) -> None:
        specs.append(
            {
                "category": category,
                "mutation_id": mutation_id,
                "operation": operation,
                "path": path,
                "target_path": _mutation_target(path),
            }
        )

    for index in range(3):
        add(
            f"NODE_{index + 1}_COORDINATES",
            "NODE",
            ("nodes", index),
            f"ADD_BINARY64_0X1P_MINUS5_TO_COMPONENT_{index}",
        )
    for index in range(3):
        add(
            f"TRIAD_{index + 1}_PHYSICAL_ROLL",
            "TRIAD",
            ("triads", index),
            "LEFT_MULTIPLY_BY_BINARY64_0X1P_MINUS10_RADIAN_FIRST_AXIS_ROTATION",
        )
    for sample in range(5):
        for field, category, label in (
            ("shape_functions", "P2_SHAPE_COEFFICIENT", "N"),
            ("derivatives", "P2_DERIVATIVE_COEFFICIENT", "DN"),
        ):
            for coefficient in range(3):
                add(
                    f"P2_SAMPLE_{sample + 1}_{label}{coefficient + 1}",
                    category,
                    ("p2_basis_samples", sample, field, coefficient),
                    "ADD_BINARY64_0X1P_MINUS20",
                )
    add(
        "TANGENT_ORIENTATION_SIGN",
        "TANGENT_SIGN",
        ("tangent_orientation",),
        "NEGATE_EVERY_TANGENT_COMPONENT",
    )
    for index in range(2):
        add(
            f"HALF_{index + 1}_RESIDUAL_ROLL_SIGN",
            "ROLL_SIGN",
            ("frame_branch_data_by_half_cell", index, "residual_roll_binary64"),
            "NEGATE_CANONICAL_BINARY64_RESIDUAL_ROLL",
        )
    add(
        "HALF_CELL_ORDERING",
        "HALF_ORDERING",
        ("half_cell_order",),
        "SWAP_LEFT_AND_RIGHT_HALF_CELL_RECORDS",
    )
    add(
        "REVERSAL_MAP_DIAGONAL",
        "REVERSAL_MAP",
        ("reversal_map_diagonal", 1),
        "NEGATE_MIDDLE_DIAGONAL_COMPONENT",
    )
    add(
        "PRODUCTION_REFERENCE_SOURCE_SHA256",
        "PRODUCTION_SOURCE_HASH",
        ("production_source_sha256",),
        "REPLACE_FIRST_HEXADECIMAL_NIBBLE",
    )
    for index in range(len(AUTHORITY_INPUT_PATHS)):
        add(
            f"AUTHORITY_ARTIFACT_SHA256_{index + 1:02d}",
            "AUTHORITY_ARTIFACT_HASH",
            ("authority_artifact_hashes", index, "sha256"),
            "REPLACE_FIRST_HEXADECIMAL_NIBBLE",
        )
    return specs


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789ABCDEF" for character in value)
    )


def _validate_mutation_matrix(
    integrity: Any,
    *,
    manifest: dict[str, Any],
) -> None:
    if not isinstance(integrity, dict) or set(integrity) != {
        "first_sha256",
        "mutated_sha256",
        "mutation_detected",
        "mutation_matrix",
        "repeated_sha256",
        "repeat_identical",
    }:
        raise RunnerError("canonical integrity schema differs")
    if not all(
        _is_sha256(integrity[key])
        for key in ("first_sha256", "mutated_sha256", "repeated_sha256")
    ):
        raise RunnerError("canonical integrity hash differs")
    if (
        integrity["mutation_detected"] is not True
        or integrity["repeat_identical"] is not True
        or integrity["first_sha256"] != integrity["repeated_sha256"]
        or integrity["first_sha256"] == integrity["mutated_sha256"]
    ):
        raise RunnerError("canonical repeat or mutation disposition differs")
    matrix = integrity["mutation_matrix"]
    if not isinstance(matrix, dict) or set(matrix) != {
        "baseline_payload",
        "baseline_payload_sha256",
        "coverage",
        "detected_count",
        "mutation_count",
        "mutation_ids",
        "mutation_order_sha256",
        "mutations",
        "passed",
    }:
        raise RunnerError("canonical mutation matrix schema differs")
    baseline = matrix["baseline_payload"]
    if not isinstance(baseline, dict) or set(baseline) != {
        "authority_artifact_hashes",
        "case_id",
        "frame_branch_data_by_half_cell",
        "half_cell_order",
        "nodes",
        "p2_basis_samples",
        "production_source_sha256",
        "reversal_map_diagonal",
        "tangent_orientation",
        "triads",
    }:
        raise RunnerError("canonical mutation baseline schema differs")
    expected_artifacts = [
        {"path": row["path"], "sha256": row["sha256"]}
        for row in sorted(manifest["inputs"], key=lambda row: str(row["path"]))
    ]
    if baseline["authority_artifact_hashes"] != expected_artifacts:
        raise RunnerError("canonical mutation authority artifacts differ")
    if baseline["production_source_sha256"] != _manifest_input(
        manifest, "src/anysolver/ge_beam3_curved_reference.py"
    )["sha256"]:
        raise RunnerError("canonical mutation production source differs")
    baseline_sha256 = _sha256(_canonical_bytes(baseline))
    if matrix["baseline_payload_sha256"] != baseline_sha256:
        raise RunnerError("canonical mutation baseline hash differs")
    specs = _registered_mutation_specs()
    expected_ids = [str(spec["mutation_id"]) for spec in specs]
    rows = matrix["mutations"]
    if (
        len(specs) != REGISTERED_MUTATION_COUNT
        or not isinstance(rows, list)
        or len(rows) != REGISTERED_MUTATION_COUNT
        or matrix["mutation_ids"] != expected_ids
        or matrix["mutation_order_sha256"] != REGISTERED_MUTATION_ORDER_SHA256
        or _sha256(_canonical_bytes(expected_ids)) != REGISTERED_MUTATION_ORDER_SHA256
        or matrix["coverage"] != REGISTERED_MUTATION_COVERAGE
        or matrix["mutation_count"] != REGISTERED_MUTATION_COUNT
        or matrix["detected_count"] != REGISTERED_MUTATION_COUNT
        or matrix["passed"] is not True
    ):
        raise RunnerError("canonical mutation inventory differs")
    observed_coverage: dict[str, int] = {}
    for row, spec in zip(rows, specs):
        if not isinstance(row, dict) or set(row) != {
            "after",
            "before",
            "category",
            "expected_status",
            "mutated_payload_sha256",
            "mutation_id",
            "operation",
            "status",
            "target_path",
        }:
            raise RunnerError("canonical mutation row schema differs")
        for key in ("category", "mutation_id", "operation", "target_path"):
            if row[key] != spec[key]:
                raise RunnerError(f"canonical mutation row {key} differs")
        if (
            row["expected_status"] != "DETECTED"
            or row["status"] != "DETECTED"
            or not _is_sha256(row["mutated_payload_sha256"])
            or row["mutated_payload_sha256"] == baseline_sha256
        ):
            raise RunnerError("canonical mutation row disposition differs")
        mutated = copy.deepcopy(baseline)
        target: Any = mutated
        path = spec["path"]
        for component in path[:-1]:
            target = target[component]
        leaf = path[-1]
        if target[leaf] != row["before"] or row["before"] == row["after"]:
            raise RunnerError("canonical mutation before/after evidence differs")
        target[leaf] = copy.deepcopy(row["after"])
        if _sha256(_canonical_bytes(mutated)) != row["mutated_payload_sha256"]:
            raise RunnerError("canonical mutation payload hash semantics differ")
        category = str(row["category"])
        observed_coverage[category] = observed_coverage.get(category, 0) + 1
    if observed_coverage != REGISTERED_MUTATION_COVERAGE:
        raise RunnerError("canonical mutation category coverage differs")


def _station_rows_are_exact(rows: Any) -> bool:
    if not isinstance(rows, list) or len(rows) != len(STATION_SCHEDULE):
        return False
    return all(
        isinstance(row, dict)
        and float(row.get("xi", float("nan"))) == xi
        and row.get("trace") == trace
        for row, (xi, trace) in zip(rows, STATION_SCHEDULE)
    )


def _validate_proof_envelope(
    proof_path: Path,
    *,
    manifest: dict[str, Any],
    authority_sha256: str,
) -> tuple[bytes, dict[str, Any]]:
    raw, proof = _strict_canonical(proof_path)
    expected_keys = {
        "authority_manifest",
        "authority_manifest_sha256",
        "auxiliary_evidence",
        "candidate_id",
        "cases",
        "cases_definition",
        "contract",
        "coverage_count",
        "negative_fixture_manifest",
        "negative_fixture_manifest_sha256",
        "obligation_order",
        "obligation_order_sha256",
        "obligation_records",
        "payload_sha256",
        "positive_fixture_manifest",
        "positive_fixture_manifest_sha256",
        "producer_id",
        "producer_script_sha256",
        "production_reference_module",
        "production_restriction",
        "reason",
        "schema",
        "station_schedule",
        "terminal",
    }
    if set(proof) != expected_keys:
        raise RunnerError("proof top-level keys differ")
    if proof.get("schema") != PROOF_SCHEMA or proof.get("candidate_id") != CANDIDATE_ID:
        raise RunnerError("proof identity differs")
    if proof.get("production_restriction") != RESTRICTION:
        raise RunnerError("proof production restriction differs")
    payload = dict(proof)
    claimed_payload_sha256 = payload.pop("payload_sha256")
    if claimed_payload_sha256 != _sha256(_canonical_bytes(payload)):
        raise RunnerError("proof payload hash differs")
    if proof.get("authority_manifest") != manifest or proof.get("authority_manifest_sha256") != authority_sha256:
        raise RunnerError("proof authority manifest differs")
    identities = {
        "cases_definition": "ge_beam3_curved_p4_cases.json",
        "contract": "ge_beam3_curved_p4_contract.json",
        "production_reference_module": "ge_beam3_curved_reference.py",
    }
    for field, suffix in identities.items():
        if proof.get(field) != _manifest_input(manifest, suffix):
            raise RunnerError(f"proof {field} identity differs")
    producer_row = _manifest_input(manifest, "ge_beam3_curved_p4_reference_producer.py")
    if proof.get("producer_script_sha256") != producer_row["sha256"]:
        raise RunnerError("proof producer identity differs")
    order = list(REGISTERED_CASE_IDS)
    order_sha256 = _sha256(_canonical_bytes(order))
    if proof.get("obligation_order") != order or proof.get("obligation_order_sha256") != order_sha256:
        raise RunnerError("proof obligation order differs")
    records = proof.get("obligation_records")
    if not isinstance(records, list) or [row.get("case_id") for row in records if isinstance(row, dict)] != order:
        raise RunnerError("proof obligation records differ")
    if any(set(row) != {"case_id", "evidence_sha256", "status"} for row in records):
        raise RunnerError("proof obligation record schema differs")
    if proof.get("coverage_count") != sum(row["status"] == "PASS" for row in records):
        raise RunnerError("proof coverage count differs")
    expected_schedule = [
        {"index": index, "trace": trace, "xi_binary64": _binary64(xi)}
        for index, (xi, trace) in enumerate(STATION_SCHEDULE)
    ]
    if proof.get("station_schedule") != expected_schedule:
        raise RunnerError("proof station schedule differs")
    fixtures = proof.get("positive_fixture_manifest")
    if not isinstance(fixtures, list) or [row.get("case_id") for row in fixtures if isinstance(row, dict)] != list(POSITIVE_FIXTURE_IDS):
        raise RunnerError("positive fixture manifest order differs")
    if proof.get("positive_fixture_manifest_sha256") != _sha256(_canonical_bytes(fixtures)):
        raise RunnerError("positive fixture manifest hash differs")
    cases = proof.get("cases")
    if not isinstance(cases, list) or [row.get("case_id") for row in cases if isinstance(row, dict)] != list(POSITIVE_FIXTURE_IDS):
        raise RunnerError("positive case order differs")
    for case in cases:
        if set(case) != {"base", "case_id", "expected", "objectivity_input", "reversed", "rigidly_transformed"}:
            raise RunnerError("positive case schema differs")
        if not all(_station_rows_are_exact(case[key].get("stations")) for key in ("base", "reversed", "rigidly_transformed")):
            raise RunnerError("case station order or trace differs")
    negatives = proof.get("negative_fixture_manifest")
    if not isinstance(negatives, list) or [row.get("fixture_id") for row in negatives if isinstance(row, dict)] != list(NEGATIVE_FIXTURE_IDS):
        raise RunnerError("negative fixture manifest order differs")
    if proof.get("negative_fixture_manifest_sha256") != _sha256(_canonical_bytes(negatives)):
        raise RunnerError("negative fixture manifest hash differs")
    if set(proof.get("auxiliary_evidence", {})) != {
        "basis_identity",
        "canonical_integrity",
        "curved_stiffener",
        "negative_admission",
        "ring_seam",
        "spatial_chain",
        "static_scope",
        "transformed_scaled",
    }:
        raise RunnerError("auxiliary evidence sections differ")
    _validate_mutation_matrix(
        proof["auxiliary_evidence"]["canonical_integrity"],
        manifest=manifest,
    )
    return raw, proof


def _validate_check_record(
    check_path: Path,
    *,
    proof_sha256: str,
    independent_checker_authority: bool,
) -> tuple[bytes, dict[str, Any]]:
    raw, value = _strict_canonical(check_path)
    if set(value) != {
        "candidate_id",
        "checker_id",
        "checks",
        "coverage_count",
        "obligation_order_sha256",
        "production_restriction",
        "proof_sha256",
        "reason",
        "schema",
        "terminal",
    }:
        raise RunnerError("checker output keys differ")
    if value.get("schema") != CHECK_SCHEMA or value.get("candidate_id") != CANDIDATE_ID:
        raise RunnerError("checker output identity differs")
    if value.get("checker_id") != "P4_INDEPENDENT_REFERENCE_RECONSTRUCTION_V2":
        raise RunnerError("checker implementation identity differs")
    if value.get("proof_sha256") != proof_sha256:
        raise RunnerError("checker proof identity differs")
    if value.get("production_restriction") != RESTRICTION:
        raise RunnerError("checker production restriction differs")
    if value.get("obligation_order_sha256") != _sha256(_canonical_bytes(list(REGISTERED_CASE_IDS))):
        raise RunnerError("checker obligation order differs")
    checks = value.get("checks")
    expected_check_keys = {
        "authority_identity",
        "canonical_proof",
        "complete_coverage",
        "exact_case_and_station_order",
        "independent_reconstruction",
        "scientific_identities",
    }
    if not isinstance(checks, dict) or set(checks) != expected_check_keys or any(type(flag) is not bool for flag in checks.values()):
        raise RunnerError("checker boolean checks differ")
    terminal = value.get("terminal")
    reasons = {
        PASS: "ALL_26_OBLIGATIONS_VERIFIED",
        NO_GO_REGULARITY: "REGULARITY_CONTRADICTION",
        NO_GO_FRAME: "FRAME_IDENTITY_CONTRADICTION",
        NO_GO_COVARIANCE: "REVERSAL_OR_OBJECTIVITY_CONTRADICTION",
        BLOCKED: "CHECKER_BLOCKED",
    }
    if terminal not in reasons or value.get("reason") != reasons[terminal]:
        raise RunnerError("checker terminal or reason differs")
    if terminal == PASS:
        if value.get("coverage_count") != len(REGISTERED_CASE_IDS) or not all(checks.values()):
            raise RunnerError("checker PASS lacks complete successful coverage")
        if not independent_checker_authority:
            raise RunnerError("checker PASS lacks independent checker authority")
    elif terminal in {NO_GO_REGULARITY, NO_GO_FRAME, NO_GO_COVARIANCE}:
        coverage_count = value.get("coverage_count")
        if (
            type(coverage_count) is not int
            or not 1 <= coverage_count <= len(REGISTERED_CASE_IDS)
            or checks["complete_coverage"] is not (
                coverage_count == len(REGISTERED_CASE_IDS)
            )
        ):
            raise RunnerError("checker NO-GO coverage disposition differs")
        if checks["scientific_identities"] is not False:
            raise RunnerError("checker NO-GO lacks a scientific contradiction")
        if not all(
            flag
            for key, flag in checks.items()
            if key not in {"complete_coverage", "scientific_identities"}
        ):
            raise RunnerError("checker NO-GO has a non-scientific failed gate")
        if not independent_checker_authority:
            raise RunnerError("checker NO-GO lacks independent checker authority")
    return raw, value


def _git(repository: Path, *arguments: str, check: bool = True) -> str:
    environment = dict(os.environ)
    environment.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
        }
    )
    result = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        env=environment,
        capture_output=True,
        check=False,
        text=True,
        encoding="utf-8",
    )
    if check and result.returncode != 0:
        raise RunnerError(f"git {' '.join(arguments)} failed")
    return result.stdout.strip()


def _live_protected_blob_rows(repository: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for relative, expected in sorted(PROTECTED_STRAIGHT_BLOBS.items()):
        target = repository / relative
        head_blob = "ABSENT_OR_UNREADABLE"
        working_blob = "ABSENT_OR_UNREADABLE"
        try:
            if target.is_file() and not target.is_symlink():
                head_blob = _git(repository, "rev-parse", f"HEAD:{relative}")
                canonical = _canonical_file_bytes(target)
                header = f"blob {len(canonical)}\0".encode("ascii")
                working_blob = hashlib.sha1(header + canonical).hexdigest()
        except (OSError, RunnerError):
            pass
        rows.append(
            {
                "expected_git_blob": expected,
                "head_git_blob": head_blob,
                "path": relative,
                "status": (
                    "PASS"
                    if head_blob == expected and working_blob == expected
                    else "FAIL"
                ),
                "working_git_blob": working_blob,
            }
        )
    return rows


def _commit_identity(repository: Path, commit: str) -> dict[str, str]:
    fields = _git(repository, "show", "-s", "--format=%H%n%T%n%P%n%s", commit).splitlines()
    if len(fields) != 4:
        raise RunnerError(f"commit identity is malformed: {commit}")
    return {
        "commit": fields[0],
        "parent": fields[2],
        "subject": fields[3],
        "tree": fields[1],
    }


def _build_authority_manifest(
    repository: Path,
    *,
    require_clean_inputs: bool,
) -> dict[str, Any]:
    repository = repository.resolve()
    grafts = Path(_git(repository, "rev-parse", "--git-path", "info/grafts"))
    if not grafts.is_absolute():
        grafts = repository / grafts
    if grafts.is_file() and grafts.stat().st_size:
        raise RunnerError("git grafts are forbidden for P4 authority")
    if _git(repository, "for-each-ref", "--format=%(refname)", "refs/replace"):
        raise RunnerError("git replacement objects are forbidden for P4 authority")
    commits: list[dict[str, str]] = []
    for expected in COMMIT_AUTHORITIES:
        actual = _commit_identity(repository, str(expected["commit"]))
        comparable = dict(actual)
        comparable["role"] = str(expected["role"])
        if comparable != expected:
            raise RunnerError(f"{expected['role']} commit identity differs")
        commits.append(comparable)
    review_commit = str(COMMIT_AUTHORITIES[-1]["commit"])
    if subprocess.run(
        ["git", "merge-base", "--is-ancestor", review_commit, "HEAD"],
        cwd=repository,
        env={**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GIT_NO_REPLACE_OBJECTS": "1", "GIT_OPTIONAL_LOCKS": "0"},
        capture_output=True,
        check=False,
    ).returncode != 0:
        raise RunnerError("accepted implementation-review commit is not an ancestor of HEAD")
    base_commit = str(COMMIT_AUTHORITIES[0]["parent"])
    changed = set(
        filter(None, _git(repository, "diff", "--name-only", f"{base_commit}..{review_commit}").splitlines())
    )
    if changed != REFERENCE_BOUNDARY_PATHS:
        raise RunnerError("reviewed P4 reference-core production boundary differs")
    input_rows: list[dict[str, Any]] = []
    for relative in AUTHORITY_INPUT_PATHS:
        target = (repository / relative).resolve()
        try:
            target.relative_to(repository)
        except ValueError as exc:
            raise RunnerError("authority input escapes repository") from exc
        if not target.is_file():
            raise RunnerError(f"authority input is absent: {relative}")
        raw = _canonical_file_bytes(target)
        input_rows.append({"bytes": len(raw), "path": relative, "sha256": _sha256(raw)})
    if require_clean_inputs:
        dirty = _git(
            repository,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            *AUTHORITY_INPUT_PATHS,
        )
        if dirty:
            raise RunnerError("frozen authority/program inputs are dirty or untracked")
    contract_path = repository / "docs/reference_cases/ge_beam3_curved_p4_contract.json"
    _contract_raw, contract = _strict_canonical(contract_path)
    if contract.get("candidate_id") != CANDIDATE_ID:
        raise RunnerError("contract candidate identity differs")
    registered_rows = contract.get("preregistration_authority")
    if not isinstance(registered_rows, list) or not registered_rows:
        raise RunnerError("contract preregistration authority is absent")
    actual_by_path = {row["path"]: row for row in input_rows}
    for row in registered_rows:
        if not isinstance(row, dict) or set(row) != {"bytes", "path", "sha256"}:
            raise RunnerError("contract preregistration authority row is malformed")
        if actual_by_path.get(row["path"]) != row:
            raise RunnerError(f"contract authority input differs: {row['path']}")
    cases_path = repository / "docs/reference_cases/ge_beam3_curved_p4_cases.json"
    _cases_raw, cases = _strict_canonical(cases_path)
    if tuple(cases.get("case_order", ())) != REGISTERED_CASE_IDS:
        raise RunnerError("registered case IDs or order differ")
    protected: list[dict[str, str]] = []
    for path, expected_blob in sorted(PROTECTED_STRAIGHT_BLOBS.items()):
        observed = _git(repository, "rev-parse", f"{review_commit}:{path}")
        protected.append(
            {
                "expected_git_blob": expected_blob,
                "observed_git_blob": observed,
                "path": path,
                "status": "PASS" if observed == expected_blob else "FAIL",
            }
        )
    if not all(row["status"] == "PASS" for row in protected):
        raise RunnerError("accepted straight GE-B3 blobs differ")
    return {
        "candidate_id": CANDIDATE_ID,
        "commits": commits,
        "inputs": input_rows,
        "production_boundary": {
            "base_commit": base_commit,
            "changed_paths": sorted(changed),
            "independent_checker_authority": True,
            "review_commit": review_commit,
            "status": "PASS",
        },
        "protected_straight_blobs": protected,
        "schema": AUTHORITY_SCHEMA,
    }


def _verify_authority_inputs(
    repository: Path,
    *,
    expected_authority_manifest_sha256: str,
    require_clean_inputs: bool,
) -> tuple[dict[str, Any], str]:
    manifest = _build_authority_manifest(
        repository,
        require_clean_inputs=require_clean_inputs,
    )
    digest = _sha256(_canonical_bytes(manifest))
    if digest != expected_authority_manifest_sha256:
        raise RunnerError("complete authority/program input manifest differs")
    return manifest, digest


def _disposable_contract_sha256(
    *,
    child_timeout_seconds: float,
    wave_timeout_seconds: float,
    inactivity_seconds: float,
    memory_limit_bytes: int,
) -> str:
    return _sha256(
        _canonical_bytes(
            {
                "checker_replicas_per_proof": 2,
                "child_timeout_seconds": child_timeout_seconds,
                "cycles": 2,
                "execution_mode": DISPOSABLE_MODE,
                "inactivity_seconds": inactivity_seconds,
                "memory_limit_bytes": memory_limit_bytes,
                "runner_id": RUNNER_ID,
                "scientific_classification_authorized": False,
                "wave_timeout_seconds": wave_timeout_seconds,
            }
        )
    )


def _one_thread_environment(private_home: Path) -> dict[str, str]:
    environment = dict(os.environ)
    for name in tuple(environment):
        if name.upper().startswith("PYTHON"):
            environment.pop(name)
    private_home.mkdir(parents=False, exist_ok=False)
    private = str(private_home.resolve())
    environment.update(
        {
            "APPDATA": private,
            "HOME": private,
            "LOCALAPPDATA": private,
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "TEMP": private,
            "TMP": private,
            "USERPROFILE": private,
            "XDG_CACHE_HOME": private,
            "XDG_CONFIG_HOME": private,
        }
    )
    return environment


def _single_process_cpu_seconds(pid: int) -> float | None:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class FileTime(ctypes.Structure):
            _fields_ = (("low", wintypes.DWORD), ("high", wintypes.DWORD))

        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return None
        try:
            created, exited, kernel, user = FileTime(), FileTime(), FileTime(), FileTime()
            if not ctypes.windll.kernel32.GetProcessTimes(
                handle,
                ctypes.byref(created),
                ctypes.byref(exited),
                ctypes.byref(kernel),
                ctypes.byref(user),
            ):
                return None
            ticks = (
                (int(kernel.high) << 32)
                + int(kernel.low)
                + (int(user.high) << 32)
                + int(user.low)
            )
            return ticks / 10_000_000.0
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        fields = Path(f"/proc/{pid}/stat").read_text(encoding="ascii").split()
        return (float(fields[13]) + float(fields[14])) / float(os.sysconf("SC_CLK_TCK"))
    except (FileNotFoundError, IndexError, OSError, ValueError):
        return None


def _single_process_memory_bytes(pid: int) -> int | None:
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = (
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            )

        handle = ctypes.windll.kernel32.OpenProcess(0x1000 | 0x0010, False, pid)
        if not handle:
            return None
        try:
            counters = Counters()
            counters.cb = ctypes.sizeof(counters)
            if not ctypes.windll.psapi.GetProcessMemoryInfo(
                handle, ctypes.byref(counters), counters.cb
            ):
                return None
            return int(counters.WorkingSetSize)
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    try:
        for row in Path(f"/proc/{pid}/status").read_text(encoding="ascii").splitlines():
            if row.startswith("VmRSS:"):
                return int(row.split()[1]) * 1024
    except (FileNotFoundError, OSError, ValueError):
        return None
    return None


def _process_parent_pairs() -> list[tuple[int, int]]:
    """Return a best-effort process snapshot without adding a dependency."""

    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class ProcessEntry(ctypes.Structure):
            _fields_ = (
                ("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.c_size_t),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", wintypes.LONG),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", wintypes.WCHAR * 260),
            )

        snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(0x00000002, 0)
        if snapshot == ctypes.c_void_p(-1).value:
            return []
        pairs: list[tuple[int, int]] = []
        try:
            entry = ProcessEntry()
            entry.dwSize = ctypes.sizeof(entry)
            present = ctypes.windll.kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
            while present:
                pairs.append((int(entry.th32ProcessID), int(entry.th32ParentProcessID)))
                present = ctypes.windll.kernel32.Process32NextW(snapshot, ctypes.byref(entry))
        finally:
            ctypes.windll.kernel32.CloseHandle(snapshot)
        return pairs
    pairs = []
    for path in Path("/proc").iterdir():
        if not path.name.isdigit():
            continue
        try:
            raw = (path / "stat").read_text(encoding="ascii")
            remainder = raw[raw.rfind(")") + 2 :].split()
            pairs.append((int(path.name), int(remainder[1])))
        except (FileNotFoundError, IndexError, OSError, ValueError):
            continue
    return pairs


def _process_tree_pids(root_pid: int) -> set[int]:
    selected = {int(root_pid)}
    pairs = _process_parent_pairs()
    changed = True
    while changed:
        changed = False
        for child, parent in pairs:
            if parent in selected and child not in selected:
                selected.add(child)
                changed = True
    return selected


def _process_cpu_seconds(pid: int) -> float | None:
    values = [
        value
        for process_id in _process_tree_pids(pid)
        if (value := _single_process_cpu_seconds(process_id)) is not None
    ]
    return None if not values else float(sum(values))


def _process_memory_bytes(pid: int) -> int | None:
    values = [
        value
        for process_id in _process_tree_pids(pid)
        if (value := _single_process_memory_bytes(process_id)) is not None
    ]
    return None if not values else int(sum(values))


def _terminate_tree(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        tree_pids = _process_tree_pids(process.pid)
        taskkill = shutil.which("taskkill.exe") or shutil.which("taskkill")
        if taskkill is not None:
            subprocess.run(
                [taskkill, "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                check=False,
                timeout=30.0,
            )
            # A child can outlive taskkill /T if its parent exits between the
            # process snapshot and taskkill's own traversal.  Kill every PID
            # from our pre-termination snapshot explicitly as a fail-closed
            # fallback; these workers are forbidden from spawning unrelated
            # processes.
            for descendant_pid in sorted(tree_pids - {process.pid}, reverse=True):
                subprocess.run(
                    [taskkill, "/PID", str(descendant_pid), "/T", "/F"],
                    capture_output=True,
                    check=False,
                    timeout=30.0,
                )
            try:
                process.wait(timeout=1.0)
                return
            except subprocess.TimeoutExpired:
                pass
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
            return
        except (OSError, ProcessLookupError):
            pass
    process.kill()


def _windows_kill_on_close_job(process: subprocess.Popen[bytes]) -> Any | None:
    """Attach a worker to a job that cannot leave orphaned descendants."""

    if os.name != "nt":
        return None
    import ctypes
    from ctypes import wintypes

    class IoCounters(ctypes.Structure):
        _fields_ = tuple(
            (name, ctypes.c_ulonglong)
            for name in (
                "read_operation_count",
                "write_operation_count",
                "other_operation_count",
                "read_transfer_count",
                "write_transfer_count",
                "other_transfer_count",
            )
        )

    class BasicLimitInformation(ctypes.Structure):
        _fields_ = (
            ("per_process_user_time_limit", ctypes.c_longlong),
            ("per_job_user_time_limit", ctypes.c_longlong),
            ("limit_flags", wintypes.DWORD),
            ("minimum_working_set_size", ctypes.c_size_t),
            ("maximum_working_set_size", ctypes.c_size_t),
            ("active_process_limit", wintypes.DWORD),
            ("affinity", ctypes.c_size_t),
            ("priority_class", wintypes.DWORD),
            ("scheduling_class", wintypes.DWORD),
        )

    class ExtendedLimitInformation(ctypes.Structure):
        _fields_ = (
            ("basic_limit_information", BasicLimitInformation),
            ("io_info", IoCounters),
            ("process_memory_limit", ctypes.c_size_t),
            ("job_memory_limit", ctypes.c_size_t),
            ("peak_process_memory_used", ctypes.c_size_t),
            ("peak_job_memory_used", ctypes.c_size_t),
        )

    kernel32 = ctypes.windll.kernel32
    kernel32.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.SetInformationJobObject.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    )
    kernel32.SetInformationJobObject.restype = wintypes.BOOL
    kernel32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel32.CloseHandle.restype = wintypes.BOOL
    handle = kernel32.CreateJobObjectW(None, None)
    if not handle:
        return None
    information = ExtendedLimitInformation()
    information.basic_limit_information.limit_flags = 0x00002000
    configured = kernel32.SetInformationJobObject(
        handle,
        9,
        ctypes.byref(information),
        ctypes.sizeof(information),
    )
    assigned = configured and kernel32.AssignProcessToJobObject(
        handle, wintypes.HANDLE(int(process._handle))  # type: ignore[attr-defined]
    )
    if not assigned:
        kernel32.CloseHandle(handle)
        return None
    return handle


def _close_windows_job(handle: Any | None) -> None:
    if handle is not None and os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        kernel32.CloseHandle.restype = wintypes.BOOL
        kernel32.CloseHandle(handle)


def _terminate_windows_job(handle: Any | None) -> None:
    if handle is not None and os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        kernel32.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
        kernel32.TerminateJobObject.restype = wintypes.BOOL
        kernel32.TerminateJobObject(handle, 1)


def _run_child(
    command: list[str],
    *,
    cwd: Path,
    stdout_path: Path,
    stderr_path: Path,
    timeout_seconds: float,
    inactivity_seconds: float,
    memory_limit_bytes: int,
) -> ChildResult:
    if timeout_seconds <= 0.0 or timeout_seconds > DEFAULT_CHILD_TIMEOUT_SECONDS:
        raise RunnerError("child timeout exceeds the frozen bound")
    if inactivity_seconds <= 0.0 or inactivity_seconds > DEFAULT_INACTIVITY_SECONDS:
        raise RunnerError("inactivity timeout exceeds the frozen bound")
    if memory_limit_bytes <= 0 or memory_limit_bytes > DEFAULT_MEMORY_LIMIT_BYTES:
        raise RunnerError("memory limit exceeds the frozen bound")
    private_home = cwd / f".runtime-{stdout_path.stem}"
    options: dict[str, Any] = {
        "cwd": cwd,
        "env": _one_thread_environment(private_home),
    }
    if os.name == "nt":
        options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        options["start_new_session"] = True
    started = time.monotonic()
    last_activity = started
    last_cpu = 0.0
    last_output_bytes = 0
    status = "EXITED"
    returncode = -1
    with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr, **options)
        job_handle = _windows_kill_on_close_job(process)
        try:
            while process.poll() is None:
                now = time.monotonic()
                cpu = _process_cpu_seconds(process.pid)
                if cpu is not None and cpu > last_cpu + 1.0e-4:
                    last_cpu = cpu
                    last_activity = now
                output_bytes = (
                    os.fstat(stdout.fileno()).st_size
                    + os.fstat(stderr.fileno()).st_size
                )
                if output_bytes > last_output_bytes:
                    last_output_bytes = output_bytes
                    last_activity = now
                memory = _process_memory_bytes(process.pid)
                if memory is not None and memory > memory_limit_bytes:
                    status = "MEMORY_LIMIT"
                    _terminate_windows_job(job_handle)
                    _close_windows_job(job_handle)
                    job_handle = None
                    _terminate_tree(process)
                    break
                if now - started > timeout_seconds:
                    status = "WALL_TIMEOUT"
                    _terminate_windows_job(job_handle)
                    _close_windows_job(job_handle)
                    job_handle = None
                    _terminate_tree(process)
                    break
                if now - last_activity > inactivity_seconds:
                    status = "INACTIVITY_TIMEOUT"
                    _terminate_windows_job(job_handle)
                    _close_windows_job(job_handle)
                    job_handle = None
                    _terminate_tree(process)
                    break
                time.sleep(0.02)
            try:
                returncode = int(process.wait(timeout=30.0))
            except subprocess.TimeoutExpired:
                status = "TERMINATION_FAILED"
                _terminate_tree(process)
                returncode = int(process.wait(timeout=30.0))
        finally:
            if process.poll() is None:
                _terminate_tree(process)
            _close_windows_job(job_handle)
    if status == "EXITED":
        status = "PASS" if returncode == 0 else "NONZERO_EXIT"
    return ChildResult(
        returncode=returncode,
        status=status,
        stdout_sha256=_sha256(stdout_path.read_bytes()),
        stderr_sha256=_sha256(stderr_path.read_bytes()),
    )


def _cycle(
    cycle_dir: Path,
    *,
    reference_module: Path,
    cases_definition: Path,
    contract: Path,
    authority_manifest: Path,
    authority_sha256: str,
    manifest_value: dict[str, Any],
    producer: Path,
    checker: Path,
    independent_checker_authority: bool,
    child_timeout_seconds: float,
    inactivity_seconds: float,
    memory_limit_bytes: int,
    wave_deadline: float,
) -> dict[str, Any]:
    cycle_dir.mkdir(parents=True, exist_ok=False)
    proof = cycle_dir / "proof.json"
    checks = [cycle_dir / "check-1.json", cycle_dir / "check-2.json"]
    reference_sha256 = _manifest_input(manifest_value, reference_module.name)["sha256"]
    producer_sha256 = _manifest_input(manifest_value, producer.name)["sha256"]
    producer_result = _run_child(
        [
            sys.executable,
            "-I",
            "-B",
            str(producer),
            "--reference-module",
            str(reference_module),
            "--cases-definition",
            str(cases_definition),
            "--contract",
            str(contract),
            "--authority-manifest",
            str(authority_manifest),
            "--output",
            str(proof),
            "--expected-reference-sha256",
            reference_sha256,
            "--expected-producer-sha256",
            producer_sha256,
            "--expected-authority-manifest-sha256",
            authority_sha256,
        ],
        cwd=cycle_dir,
        stdout_path=cycle_dir / "producer.stdout.log",
        stderr_path=cycle_dir / "producer.stderr.log",
        timeout_seconds=min(child_timeout_seconds, max(0.001, wave_deadline - time.monotonic())),
        inactivity_seconds=inactivity_seconds,
        memory_limit_bytes=memory_limit_bytes,
    )
    checker_results: list[ChildResult] = []
    proof_raw: bytes | None = None
    proof_valid = False
    if producer_result.status == "PASS" and proof.is_file():
        try:
            proof_raw, _proof_value = _validate_proof_envelope(
                proof,
                manifest=manifest_value,
                authority_sha256=authority_sha256,
            )
            proof_valid = True
        except (RunnerError, OSError, ValueError):
            proof_valid = False
    if proof_valid:
        for replica, check in enumerate(checks, start=1):
            replica_dir = cycle_dir / f"checker-{replica}-runtime"
            replica_dir.mkdir(parents=False, exist_ok=False)
            checker_results.append(
                _run_child(
                    [
                        sys.executable,
                        "-I",
                        "-B",
                        str(checker),
                        "--proof",
                        str(proof.resolve()),
                        "--output",
                        str(check.resolve()),
                    ],
                    cwd=replica_dir,
                    stdout_path=cycle_dir / f"checker-{replica}.stdout.log",
                    stderr_path=cycle_dir / f"checker-{replica}.stderr.log",
                    timeout_seconds=min(
                        child_timeout_seconds,
                        max(0.001, wave_deadline - time.monotonic()),
                    ),
                    inactivity_seconds=inactivity_seconds,
                    memory_limit_bytes=memory_limit_bytes,
                )
            )
    try:
        agreement = _checker_outputs_agree(checks) if len(checker_results) == 2 else False
    except (RunnerError, OSError, ValueError):
        agreement = False
    validated_checks: list[tuple[bytes, dict[str, Any]]] = []
    if (
        proof_raw is not None
        and len(checker_results) == 2
        and all(result.status == "PASS" for result in checker_results)
    ):
        try:
            validated_checks = [
                _validate_check_record(
                    path,
                    proof_sha256=_sha256(proof_raw),
                    independent_checker_authority=independent_checker_authority,
                )
                for path in checks
            ]
        except (RunnerError, OSError, ValueError):
            validated_checks = []
    process_ok = bool(
        producer_result.status == "PASS"
        and proof_valid
        and len(checker_results) == 2
        and all(result.status == "PASS" for result in checker_results)
        and agreement
        and len(validated_checks) == 2
    )
    if process_ok:
        assert proof_raw is not None
        check_raw, check_value = validated_checks[0]
        diagnostic_checker_terminal = str(check_value.get("terminal"))
        terminal = BLOCKED
        status = "COMPLETE"
        counts = {
            "accepted_cases": len(POSITIVE_FIXTURE_IDS),
            "covered_obligations": int(check_value["coverage_count"]),
            "registered_obligations": len(REGISTERED_CASE_IDS),
            "stations": len(POSITIVE_FIXTURE_IDS) * 3 * len(STATION_SCHEDULE),
        }
        proof_sha256 = _sha256(proof_raw)
        check_sha256 = [_sha256(check_raw), _sha256(validated_checks[1][0])]
    else:
        diagnostic_checker_terminal = "UNAVAILABLE"
        terminal = BLOCKED
        if len(checker_results) == 2 and not agreement:
            status = "CHECKER_DISAGREEMENT"
        elif producer_result.status != "PASS" or any(result.status != "PASS" for result in checker_results):
            status = "PROCESS_FAILURE"
        else:
            status = "MALFORMED_EVIDENCE"
        counts = {
            "accepted_cases": 0,
            "covered_obligations": 0,
            "registered_obligations": len(REGISTERED_CASE_IDS),
            "stations": 0,
        }
        proof_sha256 = _sha256(proof.read_bytes()) if proof.is_file() else "ABSENT"
        check_sha256 = [
            _sha256(path.read_bytes()) if path.is_file() else "ABSENT"
            for path in checks
        ]
    record = {
        "candidate_id": CANDIDATE_ID,
        "check_sha256": check_sha256,
        "counts": counts,
        "diagnostic_checker_terminal": diagnostic_checker_terminal,
        "process": {
            "checkers": (
                ["NOT_LAUNCHED", "NOT_LAUNCHED"]
                if not checker_results
                else [result.status for result in checker_results]
            ),
            "fresh_checker_processes": len(checker_results) == 2,
            "producer": producer_result.status,
        },
        "process_log_sha256": {
            "checker_stderr": (
                [result.stderr_sha256 for result in checker_results]
                if checker_results
                else ["ABSENT", "ABSENT"]
            ),
            "checker_stdout": (
                [result.stdout_sha256 for result in checker_results]
                if checker_results
                else ["ABSENT", "ABSENT"]
            ),
            "producer_stderr": producer_result.stderr_sha256,
            "producer_stdout": producer_result.stdout_sha256,
        },
        "production_restriction": RESTRICTION,
        "proof_sha256": proof_sha256,
        "schema": "anysolver.ge-beam3-curved-p4-reference-cycle-v2",
        "status": status,
        "terminal": terminal,
    }
    if process_ok:
        _write_exclusive(cycle_dir / "cycle.json", record)
    return record


def _adjudicate_terminals(
    cycles: list[dict[str, Any]],
    *,
    canonical_cycles_byte_identical: bool,
) -> str:
    # This runner is deliberately nonclassifying.  The arguments are retained
    # so tests and a future separately authorized executor can inspect the
    # complete rehearsal disposition, but no combination can promote it.
    _ = cycles, canonical_cycles_byte_identical
    return BLOCKED


def run_gate(
    output: Path,
    work_root: Path,
    *,
    reference_module: Path | None = None,
    cases_definition: Path | None = None,
    contract: Path | None = None,
    producer: Path | None = None,
    checker: Path | None = None,
    expected_authority_manifest_sha256: str,
    require_clean_inputs: bool = True,
    child_timeout_seconds: float = DEFAULT_CHILD_TIMEOUT_SECONDS,
    wave_timeout_seconds: float = DEFAULT_WAVE_TIMEOUT_SECONDS,
    inactivity_seconds: float = DEFAULT_INACTIVITY_SECONDS,
    memory_limit_bytes: int = DEFAULT_MEMORY_LIMIT_BYTES,
) -> dict[str, Any]:
    output = output.resolve()
    work_root = work_root.resolve()
    if output.exists():
        raise FileExistsError(output)
    if wave_timeout_seconds <= 0.0 or wave_timeout_seconds > DEFAULT_WAVE_TIMEOUT_SECONDS:
        raise RunnerError("wave timeout exceeds the frozen bound")
    if child_timeout_seconds <= 0.0 or child_timeout_seconds > DEFAULT_CHILD_TIMEOUT_SECONDS:
        raise RunnerError("child timeout exceeds the frozen bound")
    here = Path(__file__).resolve().parent
    repository = here.parents[1]
    for label, path in (("output", output), ("work root", work_root)):
        try:
            path.relative_to(repository)
        except ValueError:
            continue
        raise RunnerError(f"disposable {label} must be external to the repository")
    reference_module = (
        reference_module
        if reference_module is not None
        else repository / "src" / "anysolver" / "ge_beam3_curved_reference.py"
    ).resolve()
    producer = (
        producer if producer is not None else here / "ge_beam3_curved_p4_reference_producer.py"
    ).resolve()
    checker = (
        checker if checker is not None else here / "ge_beam3_curved_p4_reference_checker.py"
    ).resolve()
    cases_definition = (
        cases_definition if cases_definition is not None else here / "ge_beam3_curved_p4_cases.json"
    ).resolve()
    contract = (
        contract if contract is not None else here / "ge_beam3_curved_p4_contract.json"
    ).resolve()
    for path in (reference_module, cases_definition, contract, producer, checker):
        if not path.is_file():
            raise RunnerError(f"required frozen input is absent: {path}")
    manifest, authority_sha256 = _verify_authority_inputs(
        repository,
        expected_authority_manifest_sha256=expected_authority_manifest_sha256,
        require_clean_inputs=require_clean_inputs,
    )
    execution_contract_sha256 = _disposable_contract_sha256(
        child_timeout_seconds=child_timeout_seconds,
        wave_timeout_seconds=wave_timeout_seconds,
        inactivity_seconds=inactivity_seconds,
        memory_limit_bytes=memory_limit_bytes,
    )
    work_root.mkdir(parents=True, exist_ok=False)
    authority_manifest_path = work_root / "authority-manifest.json"
    _write_exclusive(authority_manifest_path, manifest)
    deadline = time.monotonic() + wave_timeout_seconds
    cycles: list[dict[str, Any]] = []
    for index in (1, 2):
        cycle = _cycle(
            work_root / f"cycle-{index}",
            reference_module=reference_module,
            cases_definition=cases_definition,
            contract=contract,
            authority_manifest=authority_manifest_path,
            authority_sha256=authority_sha256,
            manifest_value=manifest,
            producer=producer,
            checker=checker,
            independent_checker_authority=True,
            child_timeout_seconds=child_timeout_seconds,
            inactivity_seconds=inactivity_seconds,
            memory_limit_bytes=memory_limit_bytes,
            wave_deadline=deadline,
        )
        cycles.append(cycle)
        if cycle["status"] != "COMPLETE":
            break
    post_cycle_protected_blobs = _live_protected_blob_rows(repository)
    post_cycle_boundary_ok = bool(
        len(post_cycle_protected_blobs) == len(PROTECTED_STRAIGHT_BLOBS)
        and all(row["status"] == "PASS" for row in post_cycle_protected_blobs)
    )
    cycle_bytes = [_canonical_bytes(record) for record in cycles]
    identical = len(cycle_bytes) == 2 and cycle_bytes[0] == cycle_bytes[1]
    complete_coverage = len(cycles) == 2 and all(
        cycle["counts"]["covered_obligations"] == len(REGISTERED_CASE_IDS)
        for cycle in cycles
    )
    terminal = _adjudicate_terminals(
        cycles,
        canonical_cycles_byte_identical=identical,
    )
    aggregate = {
        "candidate_id": CANDIDATE_ID,
        "authority_inputs_sha256": authority_sha256,
        "checks": {
            "all_launched_processes_terminal": True,
            "canonical_cycles_byte_identical": identical,
            "complete_preregistered_coverage": complete_coverage,
            "exclusive_fresh_directories": True,
            "independent_checker_authority": True,
            "one_numerical_thread_per_child": True,
            "post_cycle_live_protected_blobs": post_cycle_boundary_ok,
            "scientific_classification_authorized": False,
            "successor_executor_required": True,
        },
        "counts": {
            "accepted_cases_per_complete_cycle": int(cycles[0]["counts"].get("accepted_cases", 0)),
            "cycles_complete": sum(cycle["status"] == "COMPLETE" for cycle in cycles),
            "cycles_launched": len(cycles),
            "registered_obligations": len(REGISTERED_CASE_IDS),
            "stations_per_complete_cycle": int(cycles[0]["counts"].get("stations", 0)),
        },
        "cycle_sha256": [_sha256(raw) for raw in cycle_bytes],
        "cycle_process_log_sha256": [
            _sha256(_canonical_bytes(cycle.get("process_log_sha256", {})))
            for cycle in cycles
        ],
        "execution_contract_sha256": execution_contract_sha256,
        "execution_mode": DISPOSABLE_MODE,
        "post_cycle_protected_blobs_count": len(post_cycle_protected_blobs),
        "post_cycle_protected_blobs_sha256": _sha256(
            _canonical_bytes(post_cycle_protected_blobs)
        ),
        "production_restriction": RESTRICTION,
        "runner_id": RUNNER_ID,
        "schema": SCHEMA,
        "terminal": terminal,
    }
    aggregate["aggregate_payload_sha256"] = _sha256(_canonical_bytes(aggregate))
    _write_exclusive(output, aggregate)
    return aggregate


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--expected-authority-manifest-sha256", required=True)
    parser.add_argument("--child-timeout-seconds", type=float, default=DEFAULT_CHILD_TIMEOUT_SECONDS)
    parser.add_argument("--wave-timeout-seconds", type=float, default=DEFAULT_WAVE_TIMEOUT_SECONDS)
    parser.add_argument("--inactivity-seconds", type=float, default=DEFAULT_INACTIVITY_SECONDS)
    parser.add_argument("--memory-limit-gib", type=float, default=24.0)
    return parser


def main() -> int:
    arguments = _parser().parse_args()
    run_gate(
        arguments.output.resolve(),
        arguments.work_root.resolve(),
        expected_authority_manifest_sha256=arguments.expected_authority_manifest_sha256,
        child_timeout_seconds=arguments.child_timeout_seconds,
        wave_timeout_seconds=arguments.wave_timeout_seconds,
        inactivity_seconds=arguments.inactivity_seconds,
        memory_limit_bytes=int(arguments.memory_limit_gib * (1 << 30)),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
