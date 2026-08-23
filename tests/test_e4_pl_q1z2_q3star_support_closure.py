from __future__ import annotations

import ast
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
sys.path.insert(0, str(REFERENCE_CASES))

import e4_pl_q1z2_bounded_runner as runner  # noqa: E402
from e4_pl_q1z_common import canonical_bytes, read_json, sha256  # noqa: E402


CONTRACT_PATH = REFERENCE_CASES / "e4_pl_q1z2_completion_contract.json"
RESULT_PATH = REFERENCE_CASES / "e4_pl_q1z2_bounded_result.json"


def test_q1z2_contract_is_canonical_and_targeted() -> None:
    raw = CONTRACT_PATH.read_bytes()
    contract = runner.validate_completion_contract(ROOT, CONTRACT_PATH, sha256(raw))
    assert raw == canonical_bytes(contract)
    assert contract["base_commit"] == "d325ea8f787509a056b51aa21b07107a40bdfae0"
    assert contract["coverage"] == {
        "composed_numbering_cases": 56,
        "new_numbering_cases": 8,
        "predecessor_numbering_cases": 48,
        "q3star_checker_replicas": 2,
    }
    assert contract["scope"]["producer_execution"] is False
    assert contract["q1b_execution"] == "UNAUTHORIZED"


def test_q1z2_contract_mutation_and_checker_identity_fail_closed(tmp_path: Path) -> None:
    _, contract = read_json(CONTRACT_PATH)
    contract["parallelism"]["replicas"] = 1
    changed = tmp_path / "contract.json"
    changed.write_bytes(canonical_bytes(contract))
    with pytest.raises(Exception, match="process policy"):
        runner.validate_completion_contract(ROOT, changed, sha256(changed.read_bytes()))
    checker = REFERENCE_CASES / "e4_pl_q1z_support_checker.py"
    row = next(value for value in json.loads(CONTRACT_PATH.read_text())["frozen_repository_inputs"] if value["path"].endswith("support_checker.py"))
    assert checker.stat().st_size == row["bytes"]
    assert sha256(checker.read_bytes()) == row["sha256"]


def test_q1z2_runner_has_no_producer_and_freezes_two_parallel_replicas() -> None:
    source = (REFERENCE_CASES / "e4_pl_q1z2_bounded_runner.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert "e4_pl_q1z_support_producer" not in imports
    assert "--emit-support-proof" not in source
    assert "ThreadPoolExecutor(max_workers=2)" in source
    assert "memory_limit_bytes=8 * 1024**3" in source


def test_q1z2_terminal_precedence() -> None:
    contract = json.loads(CONTRACT_PATH.read_text())
    assert runner.select_terminal(contract, blocked=True, support=True, kkt=True, covariance=True) == "BLOCKED_E4_PL_Q1Z2_PROOF_OR_REVIEW"
    assert runner.select_terminal(contract, blocked=False, support=True, kkt=True, covariance=True) == "NO_GO_E4_PL_Q1Z2_SUPPORT_BOUNDARY"
    assert runner.select_terminal(contract, blocked=False, support=False, kkt=True, covariance=True) == "NO_GO_E4_PL_Q1Z2_KKT_OR_REACTION"
    assert runner.select_terminal(contract, blocked=False, support=False, kkt=False, covariance=True) == "NO_GO_E4_PL_Q1Z2_SUPPORT_COVARIANCE"
    assert runner.select_terminal(contract, blocked=False, support=False, kkt=False, covariance=False) == "UNCLASSIFIED_E4_PL_Q1Z2_SUPPORT_KKT_CLOSED_ONLY"


def test_q1z2_result_is_fail_closed_or_complete() -> None:
    if not RESULT_PATH.exists():
        assert not (ROOT / "docs" / "E4_PL_Q1Z2_Q3STAR_SUPPORT_CLOSURE.md").exists()
        return
    raw = RESULT_PATH.read_bytes()
    result = json.loads(raw)
    assert raw == canonical_bytes(result)
    assert result["schema"] == runner.AGGREGATE_SCHEMA
    if result["terminal"] == "BLOCKED_E4_PL_Q1Z2_PROOF_OR_REVIEW":
        assert result["coverage"] == {
            "case_count": 0,
            "geometry_count": 0,
            "new_case_count": 0,
            "predecessor_case_count": 0,
        }
    else:
        assert result["coverage"] == {
            "case_count": 56,
            "geometry_count": 7,
            "new_case_count": 8,
            "predecessor_case_count": 48,
        }
        assert result["checker_byte_identical"] is True
    assert result["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert result["q1b_execution"] == "UNAUTHORIZED"
