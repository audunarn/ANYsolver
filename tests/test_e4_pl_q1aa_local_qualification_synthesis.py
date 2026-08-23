from __future__ import annotations

import ast
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
sys.path.insert(0, str(REFERENCE_CASES))

import e4_pl_q1aa_synthesizer as synthesis  # noqa: E402


CONTRACT = REFERENCE_CASES / "e4_pl_q1aa_synthesis_contract.json"
EVIDENCE = REFERENCE_CASES / "e4_pl_q1aa_synthesis_evidence.json"
REVIEW = REFERENCE_CASES / "e4_pl_q1aa_scientific_review.json"
STATUS = REFERENCE_CASES / "e4_pl_q1aa_status.json"


def test_q1aa_contract_and_hash_graph_are_exact() -> None:
    raw = CONTRACT.read_bytes()
    contract = synthesis.validate_contract(ROOT, CONTRACT, synthesis.sha256(raw))
    assert raw == synthesis.canonical_bytes(contract)
    assert len(contract["evidence_inputs"]) == 9
    assert contract["coverage"] == {
        "geometry_count": 7,
        "numbering_case_count": 56,
        "quotient_dimension": 18,
        "rigid_mode_count": 6,
        "station_count": 224,
    }
    assert contract["q1b_execution"] == "UNAUTHORIZED"


def test_q1aa_synthesizer_is_nonmechanical_and_repository_local() -> None:
    path = REFERENCE_CASES / "e4_pl_q1aa_synthesizer.py"
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
    assert not any(name.startswith(("sympy", "numpy", "mpmath", "e4_pl_")) for name in imports)
    assert "AppData" not in source
    assert "producer" not in source.lower()
    assert "checker.py" not in source.lower()


def test_q1aa_synthesis_is_complete_and_deterministic() -> None:
    raw = CONTRACT.read_bytes()
    first = synthesis.synthesize(ROOT, CONTRACT, synthesis.sha256(raw))
    second = synthesis.synthesize(ROOT, CONTRACT, synthesis.sha256(raw))
    assert synthesis.canonical_bytes(first) == synthesis.canonical_bytes(second)
    assert first["evidence_disposition"] == "LOCAL_QUALIFICATION_EVIDENCE_COMPLETE_PENDING_INDEPENDENT_REVIEW"
    assert all(first["gates"].values())
    assert first["expected_terminal_after_accepted_review"] == "PROVISIONAL_GO_E4_PL_Q1AA_Q1B_PLAN"
    assert first["q1b_plan_preparation"] == "PENDING_INDEPENDENT_REVIEW"


def test_q1aa_contract_mutation_and_terminal_precedence(tmp_path: Path) -> None:
    contract = json.loads(CONTRACT.read_text())
    contract["coverage"]["station_count"] = 223
    changed = tmp_path / "contract.json"
    changed.write_bytes(synthesis.canonical_bytes(contract))
    with pytest.raises(synthesis.SynthesisError, match="coverage"):
        synthesis.validate_contract(ROOT, changed, synthesis.sha256(changed.read_bytes()))
    original = json.loads(CONTRACT.read_text())
    assert synthesis.select_terminal(original, blocked=True, local_algebra=True, patch_recovery_support_covariance=True, unresolved=True, review_accepted=False) == "BLOCKED_E4_PL_Q1AA_EVIDENCE_OR_REVIEW"
    assert synthesis.select_terminal(original, blocked=False, local_algebra=True, patch_recovery_support_covariance=True, unresolved=True, review_accepted=True) == "NO_GO_E4_PL_Q1AA_LOCAL_ALGEBRA"
    assert synthesis.select_terminal(original, blocked=False, local_algebra=False, patch_recovery_support_covariance=True, unresolved=True, review_accepted=True) == "NO_GO_E4_PL_Q1AA_PATCH_RECOVERY_SUPPORT_OR_COVARIANCE"
    assert synthesis.select_terminal(original, blocked=False, local_algebra=False, patch_recovery_support_covariance=False, unresolved=True, review_accepted=True) == "UNCLASSIFIED_E4_PL_Q1AA_LOCAL_PLANAR_IDENTITY"
    assert synthesis.select_terminal(original, blocked=False, local_algebra=False, patch_recovery_support_covariance=False, unresolved=False, review_accepted=True) == "PROVISIONAL_GO_E4_PL_Q1AA_Q1B_PLAN"


def test_q1aa_frozen_evidence_review_and_status() -> None:
    if not EVIDENCE.exists():
        assert not REVIEW.exists() and not STATUS.exists()
        return
    evidence_raw, evidence = synthesis.read_json(EVIDENCE)
    assert evidence_raw == synthesis.canonical_bytes(evidence)
    assert all(evidence["gates"].values())
    if not REVIEW.exists():
        assert not STATUS.exists()
        return
    review_raw, review = synthesis.read_json(REVIEW)
    assert set(review) == {"findings", "reviewed_inputs", "reviewer_independence", "schema", "verdict"}
    assert review["findings"] == []
    assert review["verdict"] == "ACCEPT_Q1AA_LOCAL_QUALIFICATION_SYNTHESIS_NO_P0_P1"
    status_raw, status = synthesis.read_json(STATUS)
    assert status_raw == synthesis.canonical_bytes(status)
    assert status["evidence_sha256"] == synthesis.sha256(evidence_raw)
    assert status["review_sha256"] == synthesis.sha256(review_raw)
    assert status["terminal"] == "PROVISIONAL_GO_E4_PL_Q1AA_Q1B_PLAN"
    assert status["q1b_plan_preparation"] == "AUTHORIZED_SEPARATE_REVIEWED_PLAN_ONLY"
    assert status["q1b_execution"] == "UNAUTHORIZED"
    assert status["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
