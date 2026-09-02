from __future__ import annotations

import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "docs/reference_cases/e4_pl_s3_v3_preregistration.py"
SELECTION = ROOT / "docs/reference_cases/e4_pl_s3_v3_source_selection.json"
CONTRACT = ROOT / "docs/reference_cases/e4_pl_s3_v3_screening_contract.json"


def _load_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location("s3_v3_prereg", PROGRAM)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_validator_uses_only_standard_library() -> None:
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


def test_preregistration_is_canonical_and_bounded() -> None:
    module = _load_module()
    result = module.validate()
    assert result["terminal"] == "PROVISIONAL_GO_E4_PL_S3_V3A_BOUNDED_IMPLEMENTATION_SCREEN"
    assert result["default_activation_authorized"] is False
    assert result["stage4a_rerun_authorized"] is False
    selection = module.load_canonical(SELECTION)
    contract = module.load_canonical(CONTRACT)
    assert selection["candidate"]["implementation_status"] == "NOT_IMPLEMENTED"
    assert contract["execution"]["child_wall_seconds"] == 600
    assert contract["execution"]["complete_wave_wall_seconds"] == 1800
    assert contract["holdouts"]["executed"] is False


def test_two_exclusive_runs_are_byte_identical(tmp_path: Path) -> None:
    outputs = [tmp_path / "a" / "result.json", tmp_path / "b" / "result.json"]
    for output in outputs:
        subprocess.run(
            [sys.executable, str(PROGRAM), "--output", str(output)],
            cwd=ROOT,
            check=True,
            timeout=30,
        )
    assert outputs[0].read_bytes() == outputs[1].read_bytes()
    assert hashlib.sha256(outputs[0].read_bytes()).hexdigest().upper() == hashlib.sha256(outputs[1].read_bytes()).hexdigest().upper()
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run(
            [sys.executable, str(PROGRAM), "--output", str(outputs[0])],
            cwd=ROOT,
            check=True,
            timeout=30,
        )


def test_duplicate_and_nonfinite_json_are_rejected(tmp_path: Path) -> None:
    module = _load_module()
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"a":1,"a":2}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        module.load_canonical(duplicate)
    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_text('{"a":NaN}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="nonfinite"):
        module.load_canonical(nonfinite)


def test_mutations_fail_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_module()
    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    selection["candidate"]["implementation_status"] = "IMPLEMENTED"
    mutated_selection = tmp_path / "selection.json"
    mutated_selection.write_bytes(module.canonical_bytes(selection))
    monkeypatch.setattr(module, "SELECTION", mutated_selection)
    with pytest.raises(ValueError, match="implemented mechanics"):
        module.validate()


def test_terminal_precedence_and_production_boundary() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["terminal_precedence"] == [
        "BLOCKED_E4_PL_S3_V3_SOURCE_OR_EVIDENCE",
        "NO_GO_E4_PL_S3_V3_SOURCE_IDENTITY",
        "NO_GO_E4_PL_S3_V3A_LOCAL_OPERATOR",
        "NO_GO_E4_PL_S3_V3A_MIXED_INTERFACE",
        "UNCLASSIFIED_E4_PL_S3_V3_FORMULATION_REPLACEMENT_REQUIRED",
        "PROVISIONAL_GO_E4_PL_S3_V3A_STAGE4A_RERUN",
    ]
    assert contract["production_boundary"]["default_q4_formulation"] == "e4-pl"
    assert contract["production_boundary"]["default_s3_formulation"] == "legacy-s3"
    assert contract["production_boundary"]["anymesh_untouched"] is True
