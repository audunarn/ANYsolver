from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs" / "reference_cases"
PROGRAM = REFERENCE / "e4_pl_s3_v4a_preregistration.py"
CONTRACT = REFERENCE / "e4_pl_s3_v4a_preregistration_contract.json"


def _module():
    import importlib.util

    spec = importlib.util.spec_from_file_location("s3_v4a_prereg", PROGRAM)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_validator_uses_only_standard_library() -> None:
    allowed = {"__future__", "argparse", "fractions", "hashlib", "json", "math", "os", "pathlib", "typing"}
    tree = ast.parse(PROGRAM.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports <= allowed


def test_contract_binds_predecessor_q4_and_bounded_execution() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="ascii"))
    for entry in contract["frozen_inputs"]:
        path = ROOT / entry["path"]
        assert path.stat().st_size == entry["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest().upper() == entry["sha256"]
    assert contract["execution"] == {
        "child_wall_seconds": 600,
        "complete_wave_wall_seconds": 1800,
        "maximum_concurrent_workers": 3,
        "memory_limit_gib_per_process_tree": 24,
        "no_automatic_retry": True,
        "numerical_library_threads_per_worker": 1,
        "required_cycle_count": 2,
    }


def test_exact_partition_and_affine_constraint_authorize_only_screen() -> None:
    result = _module().validate()
    assert result["construction"] == {
        "constraint_scalar_rank": 4,
        "covered_area": "1/2",
        "positive_subcell_count": 3,
        "subcell_areas": ["1/6", "1/6", "1/6"],
    }
    assert result["terminal"] == "PROVISIONAL_GO_E4_PL_S3_V4A_BOUNDED_SUBCELL_SCREEN"
    assert result["next_gate_authorized"] is True
    assert result["activation_authorized"] is result["stage4a_rerun_authorized"] is False


def test_two_exclusive_outputs_are_byte_identical(tmp_path: Path) -> None:
    outputs = (tmp_path / "cycle-a.json", tmp_path / "cycle-b.json")
    for output in outputs:
        subprocess.run([sys.executable, str(PROGRAM), "--output", str(output)], cwd=ROOT, check=True, timeout=30)
    assert outputs[0].read_bytes() == outputs[1].read_bytes()
    with pytest.raises(subprocess.CalledProcessError):
        subprocess.run([sys.executable, str(PROGRAM), "--output", str(outputs[0])], cwd=ROOT, check=True, timeout=30)


def test_duplicate_nonfinite_and_hash_mutations_fail_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _module()
    for name, raw in (("duplicate", b'{"a":1,"a":2}\n'), ("nonfinite", b'{"a":NaN}\n')):
        path = tmp_path / f"{name}.json"
        path.write_bytes(raw)
        with pytest.raises(ValueError):
            module.load_canonical(path)
    contract = json.loads(CONTRACT.read_text(encoding="ascii"))
    contract["frozen_inputs"][0]["sha256"] = "0" * 64
    mutated = tmp_path / "contract.json"
    mutated.write_bytes(module.canonical_bytes(contract))
    monkeypatch.setattr(module, "CONTRACT", mutated)
    with pytest.raises(ValueError, match="frozen input mismatch"):
        module.validate()


def test_production_and_holdout_boundary() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="ascii"))
    assert contract["production_boundary"] == {
        "anymesh_untouched": True,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
        "s3_activation_authorized": False,
    }
    assert contract["holdouts"]["executed"] is False
    assert contract["stage4a_rerun_authorized"] is False


def test_closeout_result_and_review_authorize_only_the_bounded_screen() -> None:
    result = json.loads((REFERENCE / "e4_pl_s3_v4a_preregistration_result.json").read_text(encoding="ascii"))
    review = json.loads((REFERENCE / "e4_pl_s3_v4a_preregistration_review.json").read_text(encoding="ascii"))
    assert result["terminal"] == "PROVISIONAL_GO_E4_PL_S3_V4A_BOUNDED_SUBCELL_SCREEN"
    assert result["cycles"][0]["sha256"] == result["cycles"][1]["sha256"]
    assert result["next_gate_authorized"] is True
    assert result["activation_authorized"] is result["stage4a_rerun_authorized"] is False
    assert review["findings"] == {"P0": [], "P1": []}
    assert review["conclusions"]["implementation_screen_authorized"] is True
    assert review["conclusions"]["stage4a_rerun_authorized"] is False
