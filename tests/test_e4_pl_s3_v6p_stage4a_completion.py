from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs/reference_cases"
PROGRAM = REFERENCE / "e4_pl_s3_v6p_stage4a_completion.py"
CONTRACT = REFERENCE / "e4_pl_s3_v6p_stage4a_completion_contract.json"
REVIEW = REFERENCE / "e4_pl_s3_v6p_stage4a_completion_review.json"


def _module():
    spec = importlib.util.spec_from_file_location("v6p_completion", PROGRAM)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["v6p_completion"] = module
    spec.loader.exec_module(module)
    return module


def _canonical(path: Path):
    raw = path.read_bytes()
    value = json.loads(raw)
    assert raw == (
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    return value


def test_v6p_contract_and_review_are_canonical_and_nonactivating() -> None:
    contract = _canonical(CONTRACT)
    review = _canonical(REVIEW)
    assert contract["production_boundary"] == {
        "activation_authorized": False,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
    }
    assert contract["execution"]["mechanics_execution_forbidden"] is True
    assert review["findings"] == []


def test_v6p_union_is_exactly_69_plus_12_and_deterministic() -> None:
    module = _module()
    first, _plan, _raw, _coordinator = module.build_union_document()
    second, _plan2, _raw2, _coordinator2 = module.build_union_document()
    assert module.canonical_bytes(first) == module.canonical_bytes(second)
    assert first["record_count"] == 81
    sources = [record["source"] for record in first["records"]]
    assert sources.count("V6M_PREDECESSOR") == 69
    assert sources.count("V6O_OPTIMIZED") == 12
    assert len({record["record_id"] for record in first["records"]}) == 81


def test_v6p_strict_json_rejects_duplicates_and_nonfinite(tmp_path: Path) -> None:
    module = _module()
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"a":1,"a":2}\n', encoding="utf-8")
    with pytest.raises(module.V6PError, match="duplicate"):
        module.strict_json(duplicate)
    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_text('{"a":NaN}\n', encoding="utf-8")
    with pytest.raises(module.V6PError, match="nonfinite"):
        module.strict_json(nonfinite)
