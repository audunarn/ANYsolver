from __future__ import annotations

import ast
import copy
import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "docs" / "reference_cases"
sys.path.insert(0, str(CASES))

common = importlib.import_module("e4_pl_q1g_common")
producer = importlib.import_module("e4_pl_q1g_domain_producer")
checker = importlib.import_module("e4_pl_q1g_domain_checker")
runner = importlib.import_module("e4_pl_q1g_bounded_runner")

CONTRACT = CASES / "e4_pl_q1g_contract.json"
CONTRACT_RAW = CONTRACT.read_bytes()
CONTRACT_SHA = common.sha256(CONTRACT_RAW)


def test_q1g_contract_q1f_authority_and_strict_json() -> None:
    contract = common.validate_contract(ROOT, CONTRACT, CONTRACT_SHA)
    assert common.canonical_bytes(contract) == CONTRACT_RAW
    assert contract["authority"]["base_commit"] == "c9d75eaed17e658e84879085a01ecca823dd32cd"
    assert contract["authority"]["q1f_closeout_commit"] == "ace68489b9061450c06250ccc3573515c39382f7"
    assert len(contract["rejected_drafts"]) == 8
    assert len({row["sha256"] for row in contract["rejected_drafts"]}) == 8
    with pytest.raises(common.Q1GError, match="duplicate"):
        common.strict_json_bytes(b'{"a":1,"a":2}\n')
    with pytest.raises(common.Q1GError, match="non-finite"):
        common.strict_json_bytes(b'{"a":NaN}\n')
    with pytest.raises(common.Q1GError, match="caller hash"):
        common.validate_contract(ROOT, CONTRACT, "0" * 64)


def test_q1g_exact_rigid_basis_change_and_mutations() -> None:
    cases = [producer._case(index, *transform) for index, transform in enumerate(common.sample_transforms())]
    assert all(checker._verify_case(row) for row in cases)
    for row in cases:
        c = common.matrix_from_record(row["parameter_map"], 6, 6, "C")
        b = common.matrix_from_record(row["basis_change"], 6, 6, "B")
        scale = common.rational(row["scale"])
        assert common.matrix_equal(common.multiply(c, b), common.identity(6))
        assert common.determinant(c) == scale**3
        assert common.determinant(b) == 1 / scale**3
    mutated = copy.deepcopy(cases[1])
    mutated["parameter_map"][0][5] = common.token(common.rational(mutated["parameter_map"][0][5]) + 1)
    with pytest.raises(common.Q1GError, match="parameter map"):
        checker._verify_case(mutated)
    reflected = copy.deepcopy(cases[0])
    reflected["rotation"] = [["1", "0"], ["0", "-1"]]
    with pytest.raises(common.Q1GError, match="proper"):
        checker._verify_case(reflected)


def test_q1g_producer_checker_replicas_and_two_cycle_determinism(tmp_path: Path) -> None:
    first = runner.run_cycle(ROOT, CONTRACT, CONTRACT_SHA, tmp_path / "cycle_1")
    second = runner.run_cycle(ROOT, CONTRACT, CONTRACT_SHA, tmp_path / "cycle_2")
    assert common.canonical_bytes(first) == common.canonical_bytes(second)
    assert first["terminal"] == "UNCLASSIFIED_E4_PL_Q1G_DOMAIN_COVERAGE"
    assert first["classification"] == "UNCLASSIFIED"
    assert first["local_reduction"] == {
        "basis_change_nonsingular": True,
        "coercivity_certified": False,
        "h_kernel_certified": False,
        "rigid_range_exact": True,
    }
    assert first["checker_agreement"]["byte_identical_pairs"] is True
    assert first["coverage"]["shards_completed"] == 3
    for cycle in ("cycle_1", "cycle_2"):
        diagnostics = common.strict_json_bytes((tmp_path / cycle / "run_diagnostics.json").read_bytes())
        assert diagnostics["producer_overlap"] is True
        for shard in ("ROOT_P0", "ROOT_P1", "ROOT_P2"):
            left = tmp_path / cycle / "checkers" / shard / "replica_1" / "check.json"
            right = tmp_path / cycle / "checkers" / shard / "replica_2" / "check.json"
            assert left.read_bytes() == right.read_bytes()


def test_q1g_timeout_removes_partial_canonical_output(tmp_path: Path) -> None:
    directory = tmp_path / "slow"
    output = directory / "canonical.json"
    specification = runner.ProcessSpec(
        "slow",
        (sys.executable, "-c", "import pathlib,time; time.sleep(2); pathlib.Path(r'%s').write_text('{}')" % output),
        directory,
        output,
    )
    result = runner._run_wave([specification], 0, 24 * 1024**3, __import__("time").monotonic() + 5)
    assert result[0].state == "TIMEOUT"
    assert not output.exists()


def test_q1g_independence_extent_and_production_boundary() -> None:
    checker_tree = ast.parse((CASES / "e4_pl_q1g_domain_checker.py").read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(checker_tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or ""
        for node in ast.walk(checker_tree)
        if isinstance(node, ast.ImportFrom)
    }
    assert "e4_pl_q1g_domain_producer" not in imports
    assert not ({"numpy", "scipy", "sympy", "mpmath"} & imports)
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT, text=True, encoding="utf-8", stdout=subprocess.PIPE, check=True,
    ).stdout.splitlines()
    changed = {line[3:].replace("\\", "/") for line in status if not line[3:].startswith((".q1g_smoke/", "docs/reference_cases/__pycache__/", "tests/__pycache__/", ".pytest"))}
    allowed = {
        "docs/E4_PL_Q1G_COMPLETION.md",
        "docs/E4_PL_Q1G_DOMAIN_COERCIVITY.md",
        "docs/agent_plans/S4_E4_PL_Q1G_RIGID_RANGE_COERCIVITY_PLAN.md",
        "docs/reference_cases/e4_pl_q1g_bounded_runner.py",
        "docs/reference_cases/e4_pl_q1g_common.py",
        "docs/reference_cases/e4_pl_q1g_contract.json",
        "docs/reference_cases/e4_pl_q1g_domain_checker.py",
        "docs/reference_cases/e4_pl_q1g_domain_producer.py",
        "docs/reference_cases/e4_pl_q1g_evidence.json",
        "docs/reference_cases/e4_pl_q1g_execution_review.json",
        "docs/reference_cases/e4_pl_q1g_implementation_manifest.json",
        "docs/reference_cases/e4_pl_q1g_implementation_review.json",
        "docs/reference_cases/e4_pl_q1g_plan_review.json",
        "docs/reference_cases/e4_pl_q1g_scientific_review.json",
        "docs/reference_cases/e4_pl_q1g_status.json",
        "tests/test_e4_pl_q1g_closeout.py",
        "tests/test_e4_pl_q1g_rigid_range_coercivity.py",
    }
    assert changed <= allowed
    assert not any(path == ".gitattributes" or path == "pyproject.toml" or path.startswith(("src/", ".github/")) for path in changed)
    plan = (ROOT / "docs" / "agent_plans" / "S4_E4_PL_Q1G_RIGID_RANGE_COERCIVITY_PLAN.md").read_text(encoding="utf-8")
    assert "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED" in plan
    assert "Q1B execution and integration remain unauthorized" in plan
