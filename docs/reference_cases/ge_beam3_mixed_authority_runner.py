"""Validate successor authority and exact reference-linear agreement only."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any

from ge_beam3_mixed_exact_reference import build_certificate as build_reference
from ge_beam3_mixed_independent_checker import reconstruct_certificate as build_independent


ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = Path(__file__).resolve().parent
CANDIDATE_ID = "CANDIDATE_GE_BEAM3_DC_MIXED_K1_MACRO_V2"
STUDY_ID = "study_ge_beam3.dc_mixed_k1_macro_v2"
SCHEMA = "anysolver.ge-beam3-mixed-authority-check-v1"
BASE_COMMIT = "09351645ba17a0a5b130a1c7a48007d36dd08ada"
BASE_TREE = "cfb0cf9a19f6519abf335694253efa264cd2e695"
V1_COMMIT = "cea9cb340f721dc2fcfbb0608576b186478dab45"
SOURCE_ARTIFACTS = {
    "ATTACHED_ORIGINAL_PLAN": (
        Path(r"C:\Users\AudunArnesenNyhus\Downloads\GEOMETRICALLY_EXACT_BEAM_3D3N_IMPLEMENTATION_PLAN.md"),
        40060,
        "78C52EA1D88E5EF2FFB5EF5D2F37E6EFED78D5ADC3E9EF851C186CD83B42215B",
    ),
    "HUMER_STEINBRECHER_PECHSTEIN_2026": (
        Path(r"C:\Users\AudunArnesenNyhus\AppData\Local\Temp\ge-beam-humer-2605.04573.pdf"),
        2646466,
        "76AA9EDDDAE2EE16B47BF4E8255BDAA81678164B899E663E0B882B11C39BDB1E",
    ),
    "MEIER_WALL_POPP_2016": (
        Path(r"C:\Users\AudunArnesenNyhus\AppData\Local\Temp\ge-beam-meier-1609.00119.pdf"),
        2243579,
        "7756A90077B190BA67225758024C68DFCFCEFC29C18C4C473C44F3583105DC8E",
    ),
    "JELENIC_CRISFIELD_1999": (None, None, None),
}
JSON_INPUTS = (
    "ge_beam3_mixed_baseline.json",
    "ge_beam3_mixed_equation_map_a.json",
    "ge_beam3_mixed_equation_map_b.json",
    "ge_beam3_mixed_local_contract.json",
    "ge_beam3_mixed_source_ledger.json",
    "ge_beam3_mixed_status.json",
)

# These raw-file hashes make the authority set closed-world: a field addition,
# deletion, reordering, whitespace rewrite, or value mutation is authority drift.
# The semantic checks below are deliberately redundant so that a blocked record
# explains *which* frozen scientific assertion was altered.
EXPECTED_INPUTS = {
    "ge_beam3_mixed_baseline.json": (
        "anysolver.ge-beam3-mixed-baseline-v1",
        "9B34B3381BB49F7DCA9B99ABD745CDD1195E16EB2A85BB82A97F020B6039DBDF",
        frozenset(("archive_ref", "base", "candidate_id", "production_boundary", "schema", "study_id", "v1_closeout")),
    ),
    "ge_beam3_mixed_equation_map_a.json": (
        "anysolver.ge-beam3-mixed-equation-map-a-v1",
        "1C469B2F10BF8CE5B46237DCE794C27E31913DBC604D768F1F47329E5471DAEB",
        frozenset(("candidate_id", "external_dofs", "fields_per_cell", "linearization", "macro", "mixed_potential", "quadrature", "reference_routes", "reversal", "schema", "study_id")),
    ),
    "ge_beam3_mixed_equation_map_b.json": (
        "anysolver.ge-beam3-mixed-equation-map-b-v1",
        "09CF9F18D9BEEDE64917BAC7FB6F89EDAB80091ABBC390FF196C2DEA61F7B97D",
        frozenset(("authorship", "candidate_id", "constitutive_partial_dual", "degree_of_freedom_audit", "integration_audit", "limitations", "macro_functional", "reversal_audit", "schema", "source_authority", "stationarity_audit", "study_id", "virtual_work_audit")),
    ),
    "ge_beam3_mixed_local_contract.json": (
        "anysolver.ge-beam3-mixed-local-contract-v1",
        "249B9645EC66870D52CD70D7F3BF391DF89F4832B0A9EFA6B3264F0165DC98D4",
        frozenset(("authority_state", "candidate_id", "execution_bounds", "fatal_local_gate", "finite_packet_contract", "production_boundary", "schema", "scientific_execution_authorized", "scope", "study_id", "terminal_precedence")),
    ),
    "ge_beam3_mixed_source_ledger.json": (
        "anysolver.ge-beam3-mixed-source-ledger-v1",
        "A1402EEBB9F6D99DE1BC5F56B8707BA05C01D54D8DF7AC324F0038FFEC5E4964",
        frozenset(("authority_classes", "base", "derived_authority", "internal_base_blobs", "policy", "schema", "sources", "study_id")),
    ),
    "ge_beam3_mixed_status.json": (
        "anysolver.ge-beam3-mixed-status-v1",
        "7068D54E3B391109EC3FED3DE198DDD4E2D17A4D2AE936973C32D899413DF0AF",
        frozenset(("candidate_id", "default_activation_authorized", "implementation_state", "production_restriction", "public_selector_available", "schema", "scientific_execution_authorized", "study_id", "terminal", "v1_terminal_preserved")),
    ),
}

EXPECTED_BASE_BLOBS = (
    ("src/anysolver/__init__.py", "1a59bd7cd1dbe026fef493738acb8908ea46ac52", "PUBLIC_EXPORT_BASELINE"),
    ("src/anysolver/_native_rotation_state.py", "74d15c5de0d5907d624ad091d71e872e63f5ea7e", "NATIVE_ROTATION_TRANSACTION_BASELINE"),
    ("src/anysolver/beam_sections.py", "22a66eb07ff466ec209e9814b5ae2a6dc7915c71", "GENERALIZED_SECTION_ORDERING_BASELINE"),
    ("src/anysolver/corotational.py", "c0b86fae0b1680e52150b07f33a9d01ac457740d", "LEGACY_COROTATIONAL_BYPASS_BASELINE"),
    ("src/anysolver/current_state_tangent.py", "ac1b4192470d4f2710f8f610e78b371cd9d53275", "CURRENT_STATE_TRANSACTION_BASELINE"),
    ("src/anysolver/elements.py", "88ab3b1cc895bb060d3b1841de9789e981f97ee5", "B2_B3_AND_SELECTOR_BASELINE"),
)

EXPECTED_DERIVED_AUTHORITY = (
    (
        "TWO_CELL_K1_MACRO_PACKAGING",
        "D",
        "Apply two source-faithful k=1 cells on vertex pairs 1-2 and 2-3, retaining all three vertex rotations, then statically condense the 18 cell-local moment and rotation variables.",
    ),
    (
        "COUPLED_SECTION_PARTIAL_LEGENDRE_TRANSFORM",
        "D",
        "For SPD C=[[A,B],[B^T,D]], use 0.5*gamma^T*A*gamma-0.5*(M-B^T*gamma)^T*D^-1*(M-B^T*gamma)+kappa^T*M; stationarity recovers M=B^T*gamma+D*kappa and the original 6x6 energy.",
    ),
    (
        "K1_INTEGRATION_MAP",
        "D",
        "On each straight k=1 cell, gamma and the element rotation are constant and M is P1; one Gauss point exactly integrates the force term and two Gauss points exactly integrate the quadratic complementary-moment term.",
    ),
)

EXPECTED_HUMER_ROUTES = (
    ("1-3", (4,), "REFERENCE_CURVE_AND_TRIAD_KINEMATICS"),
    ("5-19", (5, 6), "SO3_MAPS_OBJECTIVE_FORCE_AND_MOMENT_STRAINS"),
    ("20-31", (7, 8), "VIRTUAL_WORK_AND_MIXED_COMPLEMENTARY_POTENTIAL"),
    ("32-43", (9, 10), "DISCRETE_CURVATURE_AND_REFERENCE_RELATIVE_ROTATION"),
    ("44-46", (11, 12), "ELEMENT_FUNCTIONAL_HYBRID_VERTEX_ROTATIONS_LOAD_WORK_AND_MULTIPLICATIVE_SPLIT"),
    ("SECTION_3_3_FIGURES_3_4", (12, 14, 15), "K1_LOCKING_ARGUMENT_AND_REDUCED_FORCE_TERM_INTEGRATION"),
    ("SECTION_4_3", (16, 17, 18), "CURVED_REFERENCE_BENCHMARK_BACKGROUND"),
    ("SECTION_5", (25,), "STATIC_SCOPE_AND_EXPLICIT_DYNAMICS_LIMITATION"),
)

EXPECTED_MAP_B_EQUATION_AUDIT = (
    (30, "PARTIAL_COMPLEMENTARY MOMENT DENSITY INTRODUCES M AS AN INDEPENDENT FIELD"),
    (31, "FIRST VARIATION GIVES FORCE_STRAIN WORK, MOMENT_CURVATURE WORK, AND MOMENT_CONSTITUTIVE STATIONARITY"),
    (43, "GLOBAL DISCRETE_CURVATURE WORK USES CURRENT_MINUS_REFERENCE INTERFACE_RELATIVE_ROTATIONS CONJUGATE TO MATERIAL MOMENT"),
    (44, "PER_ELEMENT MIXED FUNCTIONAL COMBINES THE VOLUME PARTIAL_DUAL DENSITY WITH THE SIGNED ENDPOINT RELATIVE_ROTATION BRACKET"),
    (45, "EXTERNAL WORK COUPLES DISTRIBUTED COUPLES TO ELEMENT_LOCAL ROTATION AND ENDPOINT COUPLES TO VERTEX_ROTATION"),
    (46, "MULTIPLICATIVE LOW_HIGH ROTATION SPLIT DEFINES THE ELEMENT_LOCAL AND VERTEX_ROTATION FACTORS USED BY THE DISCRETIZATION"),
)

EXPECTED_EXECUTION_BOUNDS = {
    "child_wall_seconds": 600,
    "complete_wave_wall_seconds": 1800,
    "inactivity_seconds": 300,
    "maximum_concurrent_workers": 3,
    "memory_limit_gib_per_process_tree": 24,
    "no_automatic_retry": True,
    "numerical_library_threads_per_worker": 1,
    "required_cycle_count_after_freeze": 2,
}
EXPECTED_TERMINAL_PRECEDENCE = (
    "BLOCKED_GE_BEAM3_MIXED_BASELINE_OR_AUTHORITY",
    "BLOCKED_GE_BEAM3_MIXED_PROCESS_OR_EVIDENCE",
    "NO_GO_GE_BEAM3_MIXED_VARIATIONAL_IDENTITY",
    "NO_GO_GE_BEAM3_MIXED_REFERENCE_LINEAR_ALGEBRA",
    "NO_GO_GE_BEAM3_MIXED_FINITE_STATIC",
    "UNCLASSIFIED_GE_BEAM3_MIXED_ROTATION_DOMAIN",
    "PROVISIONAL_GO_GE_BEAM3_MIXED_STRAIGHT_STATIC_CORE",
)
EXPECTED_FORBIDDEN = (
    "CARRY_V1_Q2_ROTATION_INTERPOLATION",
    "CARRY_V1_P1_FORCE_PROJECTION",
    "CARRY_V1_GAUSS5_RULE",
    "EMPIRICAL_STABILIZATION",
    "CLAIM_SINGLE_K2_CELL",
    "CLAIM_PIECEWISE_STRAIGHT_REFERENCE_KINK_QUALIFICATION",
    "CLAIM_CURVED_REFERENCE_QUALIFICATION",
    "CLAIM_DYNAMICS_OR_HISTORY_SECTION_QUALIFICATION",
)
EXPECTED_SOURCE_POLICY = {
    "background_cannot_fill_derivation_gaps": True,
    "candidate_must_be_identified_as_two_cell_macroelement": True,
    "empirical_stabilization_forbidden": True,
    "indispensable_statement_requires_P_or_D": True,
    "paper_static_scope_cannot_authorize_dynamics": True,
    "source_hash_drift_blocks_freeze": True,
}

# The candidate is intentionally a private prototype.  This is the complete
# path extent admitted before a successor authorization binds its commit/tree.
# No existing path may be modified as part of this freeze.
EXPECTED_CANDIDATE_EXTENT = frozenset(
    (
        "docs/reference_cases/ge_beam3_mixed_authority_runner.py",
        "docs/reference_cases/ge_beam3_mixed_baseline.json",
        "docs/reference_cases/ge_beam3_mixed_equation_map_a.json",
        "docs/reference_cases/ge_beam3_mixed_equation_map_b.json",
        "docs/reference_cases/ge_beam3_mixed_exact_reference.py",
        "docs/reference_cases/ge_beam3_mixed_finite_checker.py",
        "docs/reference_cases/ge_beam3_mixed_finite_producer.py",
        "docs/reference_cases/ge_beam3_mixed_independent_checker.py",
        "docs/reference_cases/ge_beam3_mixed_local_contract.json",
        "docs/reference_cases/ge_beam3_mixed_source_ledger.json",
        "docs/reference_cases/ge_beam3_mixed_status.json",
        "src/anysolver/_ge_beam3_mixed_ad.py",
        "src/anysolver/ge_beam3_mixed_element.py",
        "tests/test_ge_beam3_mixed_authority_runner.py",
        "tests/test_ge_beam3_mixed_core.py",
        "tests/test_ge_beam3_mixed_exact_reference.py",
        "tests/test_ge_beam3_mixed_finite_gate.py",
        "tests/test_ge_beam3_mixed_independent_checker.py",
    )
)

# These existing files define the public import/factory and scalar/solver
# assembly routes.  Comparing their *current bytes* with base blobs prevents a
# clean historical base from masking an uncommitted or committed activation.
EXPECTED_CURRENT_PROTECTED_BLOBS = {
    **{path: blob for path, blob, _role in EXPECTED_BASE_BLOBS},
    "pyproject.toml": "16da1c1ca1be9f56de4c0c3505cdfabb8752bd99",
    "src/anysolver/matrix_assembly.py": "bf5216273520acd96c71d78dfa17626f5330cb97",
    "src/anysolver/nonlinear_element_evaluation.py": "74651acaf01356f721d89e1b125cfde62d1f3045",
    "src/anysolver/nonlinear_static.py": "eafe759b76635405961bcc932adcd843c96949e2",
}
PUBLIC_ROUTE_PATHS = (
    "src/anysolver/__init__.py",
    "src/anysolver/elements.py",
    "src/anysolver/matrix_assembly.py",
    "src/anysolver/nonlinear_element_evaluation.py",
    "src/anysolver/nonlinear_static.py",
)
PRIVATE_CANDIDATE_ROUTE_TOKENS = (
    "CANDIDATE_GE_BEAM3_DC_MIXED_K1_MACRO_V2",
    "GE_BEAM3_DC_MIXED_K1_MACRO_V2",
    "GeometricallyExactBeam3D3NElement",
    "ge_beam3_mixed_element",
    '"ge-beam3"',
    "'ge-beam3'",
)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    made: dict[str, Any] = {}
    for key, value in pairs:
        if key in made:
            raise ValueError(f"duplicate JSON key: {key}")
        made[key] = value
    return made


def _load(path: Path) -> dict[str, Any]:
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"nonfinite {value}")),
    )


def _canonical_bytes(value: Any) -> bytes:
    def validate(item: Any) -> None:
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("nonfinite canonical value")
        if isinstance(item, dict):
            for child in item.values():
                validate(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                validate(child)

    validate(value)
    return (json.dumps(value, allow_nan=False, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n").encode()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _git(*arguments: str) -> str:
    return subprocess.check_output(
        ("git", *arguments), cwd=ROOT, text=True, encoding="utf-8", stderr=subprocess.DEVNULL
    ).strip()


def _git_paths(*arguments: str) -> frozenset[str]:
    raw = subprocess.check_output(
        ("git", *arguments, "-z"), cwd=ROOT, stderr=subprocess.DEVNULL
    )
    return frozenset(
        part.decode("utf-8", errors="surrogateescape").replace("\\", "/")
        for part in raw.split(b"\0")
        if part
    )


def _is_pytest_generated_diagnostic(path: str) -> bool:
    # Sandbox-created pytest basetemps can carry Windows ACLs that prevent
    # cleanup.  They are never candidate inputs.  Exclude only data/log files
    # below an untracked top-level .pytest* directory; code-like files still
    # enter the candidate extent and block authority.
    top, separator, _rest = path.partition("/")
    return bool(
        separator
        and top.startswith(".pytest")
        and Path(path).suffix.lower() in {".json", ".log", ".txt", ".out", ".err"}
    )


def _candidate_extent_snapshot() -> tuple[dict[str, frozenset[str]], frozenset[str]]:
    untracked = _git_paths("ls-files", "--others", "--exclude-standard")
    pytest_diagnostics = frozenset(
        path for path in untracked if _is_pytest_generated_diagnostic(path)
    )
    components = {
        "committed_since_base": _git_paths(
            "diff", "--name-only", "--diff-filter=ACDMRTUXB", f"{BASE_COMMIT}...HEAD"
        ),
        "index": _git_paths("diff", "--cached", "--name-only", "--diff-filter=ACDMRTUXB"),
        "working_tree": _git_paths("diff", "--name-only", "--diff-filter=ACDMRTUXB"),
        "untracked": untracked - pytest_diagnostics,
    }
    return components, pytest_diagnostics


def _working_tree_blob(relative_path: str) -> str | None:
    path = ROOT / relative_path
    if not path.is_file() or path.is_symlink():
        return None
    data = path.read_bytes()
    # The repository's Windows checkout uses CRLF for text while committed Git
    # blobs use LF.  Apply the deterministic text clean transform directly,
    # without consulting user/system Git attributes or external filters.
    if b"\0" in data:
        return None
    data = data.replace(b"\r\n", b"\n")
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def _all_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, dict):
        return all(_all_true(child) for child in value.values())
    if isinstance(value, (list, tuple)):
        return all(_all_true(child) for child in value)
    return False


def _routes(rows: Any) -> tuple[tuple[str, tuple[int, ...], str], ...] | None:
    if not isinstance(rows, list):
        return None
    try:
        return tuple(
            (row["equations"], tuple(row["pages"]), row["role"])
            for row in rows
        )
    except (KeyError, TypeError):
        return None


def _equation_audit(rows: Any) -> tuple[tuple[int, str], ...] | None:
    if not isinstance(rows, list):
        return None
    try:
        return tuple((row["equation"], row["role"]) for row in rows)
    except (KeyError, TypeError):
        return None


def _indexed_rows(rows: Any, key: str) -> dict[str, dict[str, Any]] | None:
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        return None
    values = [row.get(key) for row in rows]
    if not all(isinstance(value, str) for value in values) or len(values) != len(set(values)):
        return None
    return {row[key]: row for row in rows}


def build_record(*, verify_external_sources: bool = True) -> dict[str, Any]:
    records = {name: _load(DIRECTORY / name) for name in JSON_INPUTS}
    input_hashes = {name: _sha(DIRECTORY / name) for name in JSON_INPUTS}
    input_validation_checks: dict[str, dict[str, bool]] = {}
    for name, record in records.items():
        expected_schema, expected_hash, expected_keys = EXPECTED_INPUTS[name]
        input_validation_checks[name] = {
            "complete_field_set_and_values": input_hashes[name] == expected_hash,
            "exact_schema": record.get("schema") == expected_schema,
            "exact_top_level_fields": frozenset(record) == expected_keys,
            "strict_json_object": isinstance(record, dict),
        }
    identities = {
        name: (
            record.get("study_id") == STUDY_ID
            and (
                name == "ge_beam3_mixed_source_ledger.json"
                or record.get("candidate_id") == CANDIDATE_ID
            )
        )
        for name, record in records.items()
    }
    base = records["ge_beam3_mixed_baseline.json"]
    map_a = records["ge_beam3_mixed_equation_map_a.json"]
    map_b = records["ge_beam3_mixed_equation_map_b.json"]
    contract = records["ge_beam3_mixed_local_contract.json"]
    source = records["ge_beam3_mixed_source_ledger.json"]
    status = records["ge_beam3_mixed_status.json"]
    reference = build_reference()
    independent = build_independent()
    exact_agreement = {
        "condensed_hash": reference["hashes"]["condensed_operator_sha256"] == independent["hashes"]["condensed_operator_sha256"],
        "counts": (
            reference["counts"]["external_dofs"] == independent["counts"]["external_variables"] == 18
            and reference["counts"]["internal_dofs"] == independent["counts"]["local_variables"] == 18
            and independent["counts"]["full_rank"] == 30
            and independent["counts"]["condensed_rank"] == 12
        ),
        "predicates": all(reference["predicates"].values()) and all(independent["predicates"].values()),
        "section_hash": reference["hashes"]["section_sha256"] == independent["hashes"]["section_sha256"],
    }
    source_rows = _indexed_rows(source.get("sources"), "id")
    expected_source_ids = tuple(SOURCE_ARTIFACTS)
    source_authorities = {
        "ATTACHED_ORIGINAL_PLAN": "B",
        "HUMER_STEINBRECHER_PECHSTEIN_2026": "P",
        "MEIER_WALL_POPP_2016": "B",
        "JELENIC_CRISFIELD_1999": "B",
    }
    ledger_artifacts: dict[str, bool] = {}
    ledger_routes: dict[str, bool] = {}
    ledger_authorities: dict[str, bool] = {}
    for source_id, (path, expected_bytes, expected_hash) in SOURCE_ARTIFACTS.items():
        row = None if source_rows is None else source_rows.get(source_id)
        expected_artifact = (
            None
            if path is None
            else {"bytes": expected_bytes, "sha256": expected_hash}
        )
        ledger_artifacts[source_id] = bool(row is not None and row.get("artifact") == expected_artifact)
        ledger_authorities[source_id] = bool(
            row is not None and row.get("authority") == source_authorities[source_id]
        )
        expected_routes = EXPECTED_HUMER_ROUTES if source_id == "HUMER_STEINBRECHER_PECHSTEIN_2026" else ()
        ledger_routes[source_id] = bool(row is not None and _routes(row.get("equation_routes")) == expected_routes)

    source_checks: dict[str, bool] = {}
    for source_id, (path, expected_bytes, expected_hash) in SOURCE_ARTIFACTS.items():
        if path is None:
            continue
        source_checks[source_id] = bool(
            verify_external_sources
            and path.is_file()
            and path.is_symlink() is False
            and path.stat().st_size == expected_bytes
            and _sha(path) == expected_hash
        )

    ledger_blob_rows = source.get("internal_base_blobs")
    try:
        actual_blob_rows = tuple(
            (row["path"], row["git_blob"], row["role"]) for row in ledger_blob_rows
        )
    except (KeyError, TypeError):
        actual_blob_rows = ()
    base_blob_checks = {
        "ledger_rows_exact": actual_blob_rows == EXPECTED_BASE_BLOBS,
        **{
            path: _git("rev-parse", f"{BASE_COMMIT}:{path}") == blob
            for path, blob, _role in EXPECTED_BASE_BLOBS
        },
    }

    extent_components, _pytest_diagnostics = _candidate_extent_snapshot()
    candidate_extent = frozenset().union(*extent_components.values())
    candidate_boundary_checks = {
        "complete_extent_exact": candidate_extent == EXPECTED_CANDIDATE_EXTENT,
        "every_allowed_path_is_regular": all(
            (ROOT / path).is_file() and not (ROOT / path).is_symlink()
            for path in EXPECTED_CANDIDATE_EXTENT
        ),
        "no_existing_path_in_candidate_extent": all(
            subprocess.run(
                ("git", "cat-file", "-e", f"{BASE_COMMIT}:{path}"),
                cwd=ROOT,
                capture_output=True,
            ).returncode != 0
            for path in EXPECTED_CANDIDATE_EXTENT
        ),
    }
    current_protected_blob_checks = {
        path: _working_tree_blob(path) == blob
        for path, blob in EXPECTED_CURRENT_PROTECTED_BLOBS.items()
    }
    public_route_text = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in PUBLIC_ROUTE_PATHS
        if (ROOT / path).is_file() and not (ROOT / path).is_symlink()
    )
    current_boundary_checks = {
        "all_protected_current_blobs_equal_base": all(current_protected_blob_checks.values()),
        "no_candidate_token_in_public_or_assembly_routes": not any(
            token in public_route_text for token in PRIVATE_CANDIDATE_ROUTE_TOKENS
        ),
        "protected_path_set_complete": frozenset(current_protected_blob_checks)
        == frozenset(EXPECTED_CURRENT_PROTECTED_BLOBS),
    }

    derived_rows = source.get("derived_authority")
    try:
        actual_derived = tuple(
            (row["id"], row["authority"], row["statement"]) for row in derived_rows
        )
    except (KeyError, TypeError):
        actual_derived = ()

    map_b_authority = map_b.get("source_authority", {})
    source_semantic_checks = {
        "authority_classes_exact": source.get("authority_classes") == {
            "B": "BACKGROUND_ONLY_CANNOT_DEFINE_AN_INDISPENSABLE_CANDIDATE_EQUATION",
            "D": "INDEPENDENT_REPOSITORY_DERIVATION_REQUIRING_REVIEW_AND_TEST",
            "P": "PRINTED_PUBLIC_PRIMARY_SOURCE_WITH_HASHED_ARTIFACT_AND_EQUATION_ROUTE",
        },
        "base_exact": source.get("base") == {"commit": BASE_COMMIT, "tree": BASE_TREE},
        "derived_authority_exact": actual_derived == EXPECTED_DERIVED_AUTHORITY,
        "source_ids_unique_and_ordered": (
            source_rows is not None
            and tuple(source_rows) == expected_source_ids
            and len(source_rows) == len(expected_source_ids)
        ),
        "source_artifacts_exact": all(ledger_artifacts.values()),
        "source_authorities_exact": all(ledger_authorities.values()),
        "source_equation_routes_exact": all(ledger_routes.values()),
        "source_policy_exact": source.get("policy") == EXPECTED_SOURCE_POLICY,
    }

    equation_route_checks = {
        "map_a_reference_routes": map_a.get("reference_routes") == [
            {"equations": "30-31", "source": "HUMER_STEINBRECHER_PECHSTEIN_2026"},
            {"equations": "34-46", "source": "HUMER_STEINBRECHER_PECHSTEIN_2026"},
        ],
        "map_b_artifact": map_b_authority.get("artifact") == {
            "bytes": SOURCE_ARTIFACTS["HUMER_STEINBRECHER_PECHSTEIN_2026"][1],
            "sha256": SOURCE_ARTIFACTS["HUMER_STEINBRECHER_PECHSTEIN_2026"][2],
        },
        "map_b_equation_audit": _equation_audit(
            map_b_authority.get("primary_equation_audit")
        ) == EXPECTED_MAP_B_EQUATION_AUDIT,
        "map_b_source_id": map_b_authority.get("source_id") == "HUMER_STEINBRECHER_PECHSTEIN_2026",
        "map_b_reference_jump_route": map_b.get("macro_functional", {}).get(
            "reference_relative_jump", {}
        ).get("source_equation") == 43,
        "map_b_cell_functional_route": map_b.get("macro_functional", {}).get(
            "source_equation"
        ) == 44,
    }

    base_checks = {
        "base_commit_exists": _git("cat-file", "-t", BASE_COMMIT) == "commit",
        "base_tree": _git("rev-parse", f"{BASE_COMMIT}^{{tree}}") == BASE_TREE,
        "baseline_base_exact": base.get("base") == {
            "commit": BASE_COMMIT,
            "subject": "Merge pull request #42 from audunarn/codex/runtime-analysis-context-reuse",
            "tree": BASE_TREE,
        },
        "archive_ref_exact": base.get("archive_ref") == "refs/archive/ge-beam3-sr-p1-straight-v1-nogo-20260904",
        "archive_ref_resolves_to_v1": _git(
            "rev-parse", "refs/archive/ge-beam3-sr-p1-straight-v1-nogo-20260904"
        ) == V1_COMMIT,
        "head_descends_from_base": subprocess.run(
            ("git", "merge-base", "--is-ancestor", BASE_COMMIT, "HEAD"), cwd=ROOT, capture_output=True
        ).returncode == 0,
        "v1_commit_exists": _git("cat-file", "-t", V1_COMMIT) == "commit",
        "v1_closeout_exact": base.get("v1_closeout") == {
            "commit": V1_COMMIT,
            "evidence": {"bytes": 1007, "sha256": "3133BACBAC18292EFF51AA7114223FC5E70335BB7357DB33350F462201393071"},
            "review": {"bytes": 1409, "sha256": "DAB88E333E709DC8D186E35984013102D9202E23D37CBD606DD9CAC353408D86"},
            "status": {"bytes": 2134, "sha256": "E90760A54A8C89022A49FA7EFA6267FEF9CDF58BB6610FE4CCB5C4E895AF2DAD"},
            "terminal": "NO_GO_GE_BEAM3_DISCRETE_VARIATIONAL_IDENTITY",
        },
        "v1_terminal_preserved": base["v1_closeout"]["terminal"] == "NO_GO_GE_BEAM3_DISCRETE_VARIATIONAL_IDENTITY",
    }
    policy_checks = {
        "authority_state_is_draft": contract.get("authority_state") == "PREREGISTERED_DRAFT_NOT_AUTHORIZED",
        "baseline_production_boundary": base.get("production_boundary") == {
            "existing_b2_unchanged": True,
            "existing_b3_unchanged": True,
            "existing_beam_aliases_unchanged": True,
            "qualified_q4_unchanged": True,
            "qualified_s3_v2d_unchanged": True,
            "selector_available": False,
        },
        "candidate_is_two_cell_macro": source.get("policy", {}).get("candidate_must_be_identified_as_two_cell_macroelement") is True,
        "contract_production_boundary": contract.get("production_boundary") == {
            "default_activation_authorized": False,
            "existing_beam_routes_unchanged": True,
            "qualified_q4_unchanged": True,
            "qualified_s3_v2d_unchanged": True,
            "selector_available": False,
        },
        "execution_bounds_exact": contract.get("execution_bounds") == EXPECTED_EXECUTION_BOUNDS,
        "forbidden_set_exact": tuple(contract.get("fatal_local_gate", {}).get("forbidden", ())) == EXPECTED_FORBIDDEN,
        "no_scientific_execution_authority": contract["scientific_execution_authorized"] is False,
        "paper_cannot_authorize_dynamics": source.get("policy", {}).get("paper_static_scope_cannot_authorize_dynamics") is True,
        "selector_absent": contract["production_boundary"]["selector_available"] is False,
        "status_exact": status == {
            "candidate_id": CANDIDATE_ID,
            "default_activation_authorized": False,
            "implementation_state": "PRIVATE_STRAIGHT_STATIC_ELASTIC_CORE_REHEARSAL_PASSED",
            "production_restriction": "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED",
            "public_selector_available": False,
            "schema": "anysolver.ge-beam3-mixed-status-v1",
            "scientific_execution_authorized": False,
            "study_id": STUDY_ID,
            "terminal": "UNCLASSIFIED_GE_BEAM3_MIXED_PREREGISTRATION_IN_PROGRESS",
            "v1_terminal_preserved": "NO_GO_GE_BEAM3_DISCRETE_VARIATIONAL_IDENTITY",
        },
        "terminal_precedence_exact": tuple(contract.get("terminal_precedence", ())) == EXPECTED_TERMINAL_PRECEDENCE,
        "v1_gauss5_forbidden": "CARRY_V1_GAUSS5_RULE" in contract.get("fatal_local_gate", {}).get("forbidden", ()),
    }
    authority_inputs_valid = all(
        (
            _all_true(input_validation_checks),
            _all_true(identities),
            _all_true(base_blob_checks),
            _all_true(candidate_boundary_checks),
            _all_true(current_boundary_checks),
            _all_true(source_semantic_checks),
            _all_true(equation_route_checks),
            _all_true(base_checks),
            _all_true(policy_checks),
        )
    )
    passed = (
        verify_external_sources
        and authority_inputs_valid
        and _all_true(exact_agreement)
        and _all_true(source_checks)
    )
    if passed:
        terminal = "AUTHORITY_CHECK_ONLY_PASS"
    elif not verify_external_sources and authority_inputs_valid and _all_true(exact_agreement):
        terminal = "NONAUTHORITATIVE_AUTHORITY_CHECK_SKIPPED_SOURCES"
    else:
        terminal = "BLOCKED_GE_BEAM3_MIXED_BASELINE_OR_AUTHORITY"
    return {
        "base_checks": base_checks,
        "base_blob_checks": base_blob_checks,
        "candidate_boundary_checks": candidate_boundary_checks,
        "candidate_extent": sorted(candidate_extent),
        "candidate_extent_components": {
            key: sorted(paths) for key, paths in extent_components.items()
        },
        "candidate_id": CANDIDATE_ID,
        "current_boundary_checks": current_boundary_checks,
        "current_protected_blob_checks": current_protected_blob_checks,
        "equation_route_checks": equation_route_checks,
        "exact_agreement": exact_agreement,
        "input_hashes": input_hashes,
        "input_validation_checks": input_validation_checks,
        "policy_checks": policy_checks,
        "pytest_diagnostic_exclusion_policy": (
            "NON_CODE_DATA_OR_LOG_FILES_UNDER_TOP_LEVEL_DOT_PYTEST_DIRECTORIES_ONLY"
        ),
        "record_identity_checks": identities,
        "schema": SCHEMA,
        "source_checks": source_checks,
        "source_semantic_checks": source_semantic_checks,
        "source_verification_mode": (
            "EXTERNAL_FILES_HASHED" if verify_external_sources else "SKIPPED_TEST_ONLY"
        ),
        "study_id": STUDY_ID,
        "terminal": terminal,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--skip-external-source-files", action="store_true")
    args = parser.parse_args()
    payload = _canonical_bytes(build_record(verify_external_sources=not args.skip_external_source_files))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write(payload)
    return 0 if json.loads(payload)["terminal"] == "AUTHORITY_CHECK_ONLY_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
