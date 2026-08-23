from __future__ import annotations

import ast
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
sys.path.insert(0, str(REFERENCE_CASES))

import e4_pl_q1v_reference as reference  # noqa: E402
import e4_pl_q1z_bounded_runner as runner  # noqa: E402
import e4_pl_q1z_common as common  # noqa: E402
import e4_pl_q1z_support_producer as producer  # noqa: E402


CONTRACT_PATH = REFERENCE_CASES / "e4_pl_q1z_support_contract.json"
RESULT_PATH = REFERENCE_CASES / "e4_pl_q1z_bounded_result.json"


def test_q1z_contract_authority_coverage_and_boundary() -> None:
    raw = CONTRACT_PATH.read_bytes()
    contract = common.validate_contract(ROOT, CONTRACT_PATH, common.sha256(raw))
    assert raw == common.canonical_bytes(contract)
    assert contract["base_commit"] == "795ae1b44748cd6896a49079f82c947b96260aea"
    assert [row["geometry_id"] for row in contract["q1y3_proofs"]] == list(common.GEOMETRY_IDS)
    assert contract["coverage"] == {
        "base_support_systems": 7,
        "derived_numbering_cases": 56,
        "drill_coordinates": 4,
        "kkt_dimension": 44,
        "physical_support_rows": 20,
    }
    assert contract["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert contract["q1b_execution"] == "UNAUTHORIZED"
    changed = {
        path.as_posix()
        for path in ROOT.rglob("e4_pl_q1z_*")
        if path.is_file()
    }
    assert all("/src/" not in f"/{path}/" for path in changed)


def test_q1z_producer_is_reduction_only_and_four_coordinate_inverse_is_exact() -> None:
    source_path = REFERENCE_CASES / "e4_pl_q1z_support_producer.py"
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    called = {
        node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, (ast.Attribute, ast.Name))
    }
    assert not {"assemble", "_assemble", "_solve_internal", "_stationary_internal"} & called
    assert "_local_drill_block" in source
    field = reference.Field(())
    matrix = reference.zeros(field, 24, 24)
    for index, value in zip((5, 11, 17, 23), (2, 3, 5, 7), strict=True):
        matrix[index][index] = field.rational(value)
    drill = producer._local_drill_block(matrix)
    inverse = reference.matrix_inverse(drill)
    assert reference.matmul(drill, inverse) == reference.eye(field, 4)
    assert reference.matmul(inverse, drill) == reference.eye(field, 4)


def test_q1z_checker_is_independent_exact_domain_code() -> None:
    path = REFERENCE_CASES / "e4_pl_q1z_support_checker.py"
    source = path.read_text(encoding="utf-8")
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
    assert "e4_pl_q1v_reference" not in imports
    assert "QQ.algebraic_field" in source
    assert "evalf(" not in source
    assert "simplify(" not in source
    assert "float(" not in source


def test_q1z_terminal_precedence_and_frozen_process_policy() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert runner.select_terminal(contract, blocked=True, support=True, kkt=True, covariance=True) == contract["terminals"]["blocked"]
    assert runner.select_terminal(contract, blocked=False, support=True, kkt=True, covariance=True) == contract["terminals"]["support_boundary"]
    assert runner.select_terminal(contract, blocked=False, support=False, kkt=True, covariance=True) == contract["terminals"]["kkt_reaction"]
    assert runner.select_terminal(contract, blocked=False, support=False, kkt=False, covariance=True) == contract["terminals"]["support_covariance"]
    assert runner.select_terminal(contract, blocked=False, support=False, kkt=False, covariance=False) == contract["terminals"]["success"]
    assert contract["parallelism"] == {
        "checker_workers": 4,
        "global_timeout_seconds": 300,
        "memory_limit_gib_per_process": 8,
        "numerical_threads_per_process": 1,
        "producer_workers": 7,
        "replicas_per_geometry": 2,
        "timeout_seconds_per_process": 180,
        "weighted_process_slots": 8,
    }


def test_q1z_formal_result_hash_dag_and_fail_closed_terminal() -> None:
    raw = RESULT_PATH.read_bytes()
    result = json.loads(raw)
    assert raw == common.canonical_bytes(result)
    assert result["schema"] == common.AGGREGATE_SCHEMA
    assert result["contract_sha256"] == common.sha256(CONTRACT_PATH.read_bytes())
    assert result["coverage"] == {
        "case_count": 0,
        "geometry_count": 0,
        "kkt_dimension": 0,
        "physical_support_rows": 0,
    }
    assert len(result["shards"]) == 7
    assert [row["geometry_id"] for row in result["shards"]] == list(common.GEOMETRY_IDS)
    assert sum(row["checker_byte_identical"] for row in result["shards"]) == 6
    assert all(row["producer_status"] == "COMPLETE" for row in result["shards"])
    assert all(
        row["checker_statuses"] == ["COMPLETE", "COMPLETE"]
        for row in result["shards"][:-1]
    )
    assert result["shards"][-1]["checker_statuses"] == ["TIMEOUT", "TIMEOUT"]
    assert result["shards"][-1]["geometry_id"] == "Q3_TAPERED_SKEW_RSTAR_TRANSLATED"
    assert result["support_boundary_contradiction"] is False
    assert result["kkt_reaction_contradiction"] is False
    assert result["support_covariance_contradiction"] is False
    assert result["q3_proper_global_support_identity"] is False
    assert result["terminal"] == "BLOCKED_E4_PL_Q1Z_PROOF_OR_REVIEW"
    assert result["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert result["q1b_execution"] == "UNAUTHORIZED"
