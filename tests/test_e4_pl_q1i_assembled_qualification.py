from __future__ import annotations

import ast
import copy
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "docs" / "reference_cases"
sys.path.insert(0, str(CASES))
synthesis = importlib.import_module("e4_pl_q1i_synthesizer")
CONTRACT = CASES / "e4_pl_q1i_synthesis_contract.json"
EVIDENCE = CASES / "e4_pl_q1i_synthesis_evidence.json"
CONTRACT_SHA256 = "2B939C4B2F45DAF3F44CB31D0B20AD23B4ED8071CDF4DB958188EF21F1666FDB"
EVIDENCE_SHA256 = "E913ED19FA253B93CA9FF54F5FE01B802DC3D8AF14FA66328724BFA58021BCDD"


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest().upper()


def test_q1i_contract_and_complete_predecessor_hash_dag() -> None:
    raw, contract = synthesis.read_json(CONTRACT)
    assert _sha256(raw) == CONTRACT_SHA256
    validated, values = synthesis.validate_contract(ROOT, CONTRACT, CONTRACT_SHA256)
    assert validated == contract
    assert set(values) == {
        "Q1E_CONTRACT", "Q1E_EVIDENCE", "Q1E_REVIEW", "Q1E_STATUS",
        "Q1H_CONTRACT", "Q1H_EVIDENCE", "Q1H_STATUS",
    }
    q1e_rows = values["Q1E_CONTRACT"]["evidence_inputs"]
    assert len(q1e_rows) == 9
    for row in q1e_rows:
        source = (ROOT / row["path"]).read_bytes()
        assert len(source) == row["bytes"]
        assert _sha256(source) == row["sha256"]
        assert subprocess.run(
            ["git", "rev-parse", f"HEAD:{row['path']}"], cwd=ROOT,
            check=True, stdout=subprocess.PIPE, text=True, encoding="utf-8",
        ).stdout.strip() == row["git_blob"]
    with pytest.raises(synthesis.SynthesisError, match="duplicate"):
        path = ROOT / ".pytest_q1i_duplicate.json"
        path.write_bytes(b'{"a":1,"a":2}\n')
        try:
            synthesis.read_json(path)
        finally:
            path.unlink()
    with pytest.raises(synthesis.SynthesisError, match="non-finite"):
        path = ROOT / ".pytest_q1i_nonfinite.json"
        path.write_bytes(b'{"a":NaN}\n')
        try:
            synthesis.read_json(path)
        finally:
            path.unlink()


def test_q1i_recomputes_q1e_and_q1h_gates_without_mechanics() -> None:
    _contract, inputs = synthesis.validate_contract(ROOT, CONTRACT, CONTRACT_SHA256)
    q1e = synthesis.recompute_q1e(ROOT, inputs)
    q1h = synthesis.recompute_q1h(ROOT, inputs)
    assert q1e == {
        "domain_coercivity_unresolved": True,
        "historical_q1b_locking_was_coarse_row_triggered": True,
        "historical_q1b_terminal_preserved": True,
        "nonintrusion_recovery_closed": True,
        "production_boundary_unchanged": True,
        "q1b_resolved_finest_rows_below_limit": True,
        "q1c_resolved_range_locking_closed": True,
        "q1d_solver_equivalence_closed": True,
        "q1d_ultrathin_locking_closed": True,
        "stability_finite_samples_closed": True,
    }
    assert q1h == {
        "alpha_exact": True,
        "control_invertible": True,
        "coverage_complete": True,
        "h_kernel_exact": True,
        "partition_bound": True,
        "two_cycle_deterministic": True,
    }
    assert synthesis.select_terminal(q1e, q1h) == "PROVISIONAL_GO_E4_PL_Q1I_DORMANT_IMPLEMENTATION_PLAN"
    raw, evidence = synthesis.read_json(EVIDENCE)
    assert _sha256(raw) == EVIDENCE_SHA256
    assert evidence == synthesis.synthesize(ROOT, CONTRACT, CONTRACT_SHA256)


def test_q1i_two_fresh_synthesis_runs_are_byte_identical(tmp_path: Path) -> None:
    program = CASES / "e4_pl_q1i_synthesizer.py"
    outputs = []
    for cycle in ("cycle_1", "cycle_2"):
        output = tmp_path / cycle / "evidence.json"
        result = subprocess.run(
            [
                sys.executable, str(program), "--synthesize-assembled-qualification",
                "--repository-root", str(ROOT), "--contract", str(CONTRACT),
                "--contract-sha256", CONTRACT_SHA256, "--output", str(output),
            ],
            cwd=ROOT, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        outputs.append(output.read_bytes())
    assert outputs[0] == outputs[1] == EVIDENCE.read_bytes()


def test_q1i_terminal_precedence_rejects_mutated_scientific_gates() -> None:
    _contract, inputs = synthesis.validate_contract(ROOT, CONTRACT, CONTRACT_SHA256)
    q1e = synthesis.recompute_q1e(ROOT, inputs)
    q1h = synthesis.recompute_q1h(ROOT, inputs)
    mutation = copy.deepcopy(q1e)
    mutation["q1d_solver_equivalence_closed"] = False
    assert synthesis.select_terminal(mutation, q1h) == "NO_GO_E4_PL_Q1I_LOCKING_OR_SOLVER_EQUIVALENCE"
    mutation = copy.deepcopy(q1e)
    mutation["nonintrusion_recovery_closed"] = False
    assert synthesis.select_terminal(mutation, q1h) == "NO_GO_E4_PL_Q1I_STABILITY_OR_NONINTRUSION"
    h_mutation = copy.deepcopy(q1h)
    h_mutation["h_kernel_exact"] = False
    assert synthesis.select_terminal(q1e, h_mutation) == "NO_GO_E4_PL_Q1I_DOMAIN_COERCIVITY"


def test_q1i_standard_library_only_closed_extent_and_production_boundary() -> None:
    tree = ast.parse((CASES / "e4_pl_q1i_synthesizer.py").read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert not ({"numpy", "scipy", "sympy", "mpmath"} & imports)
    assert "e4_pl_q1h_interval" not in imports
    assert "e4_pl_q1h_point_mechanics" not in imports
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT,
        check=True, stdout=subprocess.PIPE, text=True, encoding="utf-8",
    ).stdout.splitlines()
    changed = {
        row[3:].replace("\\", "/")
        for row in status
        if not row[3:].replace("\\", "/").startswith((".pytest", "docs/reference_cases/__pycache__", "tests/__pycache__"))
    }
    assert changed <= synthesis.EXTENT
    assert not any(path == ".gitattributes" or path == "pyproject.toml" or path.startswith(("src/", ".github/")) for path in changed)
    assert synthesis.PRODUCTION == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
