from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "docs/reference_cases/e4_pl_s3_v3_equation_authority.py"
MAP_A = ROOT / "docs/reference_cases/e4_pl_s3_v3_misp3_equation_map_a.json"
MAP_B = ROOT / "docs/reference_cases/e4_pl_s3_v3_misp3_equation_map_b.json"
CONTRACT = ROOT / "docs/reference_cases/e4_pl_s3_v3_equation_authority_contract.json"


def _module():
    spec = importlib.util.spec_from_file_location("s3_v3_equation_authority", PROGRAM)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_validator_is_standard_library_only() -> None:
    allowed = {
        "__future__",
        "argparse",
        "hashlib",
        "json",
        "math",
        "os",
        "pathlib",
        "typing",
    }
    tree = ast.parse(PROGRAM.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports <= allowed


def test_maps_reconcile_and_scope_stays_bounded() -> None:
    module = _module()
    result = module.validate()
    assert result["terminal"] == "PASS_E4_PL_S3_V3A_EQUATION_AUTHORITY"
    assert result["assertion_count"] == 17
    assert result["equation_maps_agree"] is True
    assert result["stage4a_rerun_authorized"] is False
    assert result["activation_authorized"] is False


def test_two_exclusive_outputs_are_byte_identical(tmp_path: Path) -> None:
    outputs = [tmp_path / "one" / "result.json", tmp_path / "two" / "result.json"]
    for output in outputs:
        subprocess.run(
            [sys.executable, str(PROGRAM), "--output", str(output)],
            cwd=ROOT,
            check=True,
            timeout=30,
        )
    assert outputs[0].read_bytes() == outputs[1].read_bytes()
    assert hashlib.sha256(outputs[0].read_bytes()).digest() == hashlib.sha256(outputs[1].read_bytes()).digest()
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run(
            [sys.executable, str(PROGRAM), "--output", str(outputs[0])],
            cwd=ROOT,
            check=True,
            timeout=30,
        )


def test_duplicate_and_nonfinite_json_fail_closed(tmp_path: Path) -> None:
    module = _module()
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"a":1,"a":2}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        module.load_canonical(duplicate)
    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_text('{"a":Infinity}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="nonfinite"):
        module.load_canonical(nonfinite)


def test_mutated_equation_claim_is_rejected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _module()
    value = json.loads(MAP_A.read_text(encoding="utf-8"))
    value["reconciliation_claims"][0]["value"] = "H_INVERSE_ONLY"
    mutated = tmp_path / "map-a.json"
    mutated.write_bytes(module.canonical_bytes(value))
    monkeypatch.setattr(module, "MAP_A", mutated)
    with pytest.raises(ValueError, match="disagree"):
        module.validate()


def test_mutated_source_identity_is_rejected(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _module()
    value = json.loads(MAP_B.read_text(encoding="utf-8"))
    value["source_authority"]["sha256"] = "0" * 64
    mutated = tmp_path / "map-b.json"
    mutated.write_bytes(module.canonical_bytes(value))
    monkeypatch.setattr(module, "MAP_B", mutated)
    with pytest.raises(ValueError, match="source hash"):
        module.validate()


def test_contract_preserves_defaults_and_limits() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["validation_execution"]["child_wall_seconds"] == 120
    assert contract["next_screen_execution"]["child_wall_seconds"] == 600
    assert contract["next_screen_execution"]["complete_wave_wall_seconds"] == 1800
    assert contract["production_boundary"]["default_q4_formulation"] == "e4-pl"
    assert contract["production_boundary"]["default_s3_formulation"] == "legacy-s3"
    assert contract["production_boundary"]["anymesh_untouched"] is True
    assert contract["stage4a_rerun_authorized"] is False
