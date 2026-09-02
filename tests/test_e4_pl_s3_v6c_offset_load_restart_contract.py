from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess

import anysolver
from anysolver.e4_pl_s3_v2d_element import (
    BLOCKED_OPERATIONS,
    CAPABILITY_MATRIX,
    FORMULATION_ID,
    FORMULATION_SCHEMA,
    IMPLEMENTATION_ID,
    NATIVE_STATE_LAYOUT_ID,
    NATIVE_STATE_SCHEMA_ID,
    PRESSURE_SURFACE_POLICY_ID,
    SELECTOR,
    SERIALIZATION_POLICY_ID,
    SUPPORTED_OPERATIONS,
)


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs/reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v6c_v2d_offset_load_restart_contract.json"


def _reject_duplicate(pairs: list[tuple[str, object]]) -> dict:
    made: dict[str, object] = {}
    for key, value in pairs:
        if key in made:
            raise ValueError(f"duplicate key {key}")
        made[key] = value
    return made


def _canonical(path: Path) -> tuple[bytes, dict]:
    raw = path.read_bytes()
    value = json.loads(
        raw,
        object_pairs_hook=_reject_duplicate,
        parse_constant=lambda token: (_ for _ in ()).throw(
            ValueError(f"nonfinite token {token}")
        ),
    )
    expected = (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("ascii")
    assert raw == expected
    return raw, value


def test_v6c_contract_binds_v6b_authority_and_current_candidate_identity() -> None:
    _raw, contract = _canonical(CONTRACT)
    assert subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            contract["authority"]["expected_parent"],
            "HEAD",
        ],
        cwd=ROOT,
        check=True,
    ).returncode == 0
    for name, expected in (
        ("contract", contract["authority"]["v6b_contract_sha256"]),
        ("result", contract["authority"]["v6b_result_sha256"]),
        ("review", contract["authority"]["v6b_review_sha256"]),
        ("status", contract["authority"]["v6b_status_sha256"]),
    ):
        raw = (
            REFERENCE
            / f"e4_pl_s3_v6b_v2d_native_state_corotational_{name}.json"
        ).read_bytes()
        assert hashlib.sha256(raw).hexdigest().upper() == expected
    candidate = contract["candidate"]
    assert candidate == {
        "formulation_id": FORMULATION_ID,
        "formulation_schema": FORMULATION_SCHEMA,
        "implementation_id": IMPLEMENTATION_ID,
        "selector": SELECTOR,
        "serialization_policy_id": SERIALIZATION_POLICY_ID,
        "state_layout_id": NATIVE_STATE_LAYOUT_ID,
        "state_schema": NATIVE_STATE_SCHEMA_ID,
    }


def test_v6c_capability_boundary_and_defaults_are_exact() -> None:
    _raw, contract = _canonical(CONTRACT)
    required = {
        "director_polarity_reversal",
        "reference_surface_offset",
        "follower_pressure",
        "distributed_couple",
        "solver_integrated_hot_restart",
    }
    assert required <= SUPPORTED_OPERATIONS
    assert all(CAPABILITY_MATRIX[name] == "SUPPORTED" for name in required)
    assert set(contract["prohibited_scope"]) == {
        "qualified_s3_v1_physical_mechanics",
        "q4_physical_mechanics",
        "activity_or_deletion_state",
        "contact_state",
        "qualified_batch_path",
        "python_pickle_restart",
        "v6b_state_hot_migration",
        "default_activation",
    }
    assert all(
        CAPABILITY_MATRIX[name] == "BLOCKED_PENDING_SUCCESSOR_GATE"
        for name in BLOCKED_OPERATIONS
    )
    assert PRESSURE_SURFACE_POLICY_ID == "ELEMENT_NODAL_REFERENCE_SURFACE_V1"
    assert anysolver.DEFAULT_Q4_FORMULATION == "e4-pl"
    assert anysolver.DEFAULT_S3_FORMULATION == "legacy-s3"


def test_v6c_implementation_is_native_and_restart_route_is_exactly_scoped() -> None:
    element_source = (ROOT / "src/anysolver/e4_pl_s3_v2d_element.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(element_source)
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    assert not any(name.endswith("e4_pl_s3_element") for name in imports)
    assert "QualifiedE4PLS3ShellElement" not in element_source
    assert "compute_native_current_pressure_load" in element_source
    assert "compute_native_current_pressure_tangent" in element_source
    assert "seal_solver_integrated_nonlinear_state" in element_source

    nonlinear_source = (ROOT / "src/anysolver/nonlinear_static.py").read_text(
        encoding="utf-8"
    )
    assert nonlinear_source.count(FORMULATION_ID) == 2
    assert "seal_solver_integrated_nonlinear_state" in nonlinear_source
    boundary_source = (ROOT / "src/anysolver/boundary.py").read_text(
        encoding="utf-8"
    )
    assert boundary_source.count("compute_native_current_pressure_load") == 1
    assert boundary_source.count("compute_native_current_pressure_tangent") == 1


def test_v6c_contract_has_exact_bounded_ten_path_extent_and_terminal_order() -> None:
    _raw, contract = _canonical(CONTRACT)
    assert len(contract["exact_implementation_extent"]) == 10
    assert len(set(contract["exact_implementation_extent"])) == 10
    assert contract["runtime_policy"] == {
        "automatic_retry": False,
        "focused_cycle_limit_seconds": 600,
        "long_running_scientific_cycle_authorized": False,
        "required_focused_cycles": 2,
    }
    assert contract["production_boundary"] == {
        "activation_authorized": False,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
    }
    assert contract["terminal_precedence"][-1] == (
        "PROVISIONAL_GO_E4_PL_S3_V6C_REMAINING_PARITY"
    )
