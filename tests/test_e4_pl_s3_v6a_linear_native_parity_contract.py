from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/reference_cases/e4_pl_s3_v6a_v2d_linear_native_parity_contract.json"


def _strict_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    made: dict[str, object] = {}
    for key, value in pairs:
        if key in made:
            raise ValueError(f"duplicate key {key}")
        made[key] = value
    return made


def _contract() -> dict[str, object]:
    return json.loads(
        CONTRACT.read_text(encoding="ascii"),
        object_pairs_hook=_strict_pairs,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"nonfinite {value}")
        ),
    )


def test_v6a_contract_binds_exact_implementation_files() -> None:
    contract = _contract()
    records = contract["implementation_files"]
    assert isinstance(records, list) and len(records) == 4
    for record in records:
        assert isinstance(record, dict)
        path = ROOT / str(record["path"])
        payload = path.read_bytes()
        assert len(payload) == record["bytes"]
        assert hashlib.sha256(payload).hexdigest().upper() == record["sha256"]


def test_v6a_contract_is_implementation_only_and_preserves_defaults() -> None:
    contract = _contract()
    assert contract["candidate"] == {
        "formulation_id": "CANDIDATE_E4_PL_S3_V2D_NATIVE_PARITY_V1",
        "implementation_id": "E4_PL_S3_V2D_MIN3_NATIVE_SECTION_LINEAR_GATE_V1",
        "selector": "e4-pl-s3-v2d",
    }
    assert contract["production_boundary"] == {
        "activation_authorized": False,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
    }
    assert contract["next_gate"] == "V6B_V2D_NATIVE_STATE_AND_COROTATIONAL_PARITY"
    prohibited = set(contract["prohibited_surface"])
    assert {
        "legacy_tri3_mechanics",
        "q4_mechanics_reuse",
        "nonlinear_geometry",
        "restart",
        "default_activation",
    } <= prohibited


def test_v2d_module_does_not_import_rejected_v1_or_q4_mechanics() -> None:
    module = ROOT / "src/anysolver/e4_pl_s3_v2d_element.py"
    tree = ast.parse(module.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    assert "e4_pl_s3_element" not in imports
    assert "anysolver.e4_pl_s3_element" not in imports
    source = module.read_text(encoding="utf-8")
    assert "QualifiedE4PLS3ShellElement" not in source
    assert not any(
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "ShellElement"
        and node.attr.startswith("compute_")
        for node in ast.walk(tree)
    )


def test_v6a_runtime_policy_forbids_long_or_retrying_execution() -> None:
    runtime = _contract()["runtime_policy"]
    assert runtime == {
        "automatic_retry": False,
        "individual_test_command_limit_seconds": 600,
        "long_running_scientific_cycle_authorized": False,
    }
