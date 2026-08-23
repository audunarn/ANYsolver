from __future__ import annotations

import ast
import copy
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
sys.path.insert(0, str(REFERENCE_CASES))

import e4_pl_q1e_synthesizer as synthesis  # noqa: E402


CONTRACT = REFERENCE_CASES / "e4_pl_q1e_synthesis_contract.json"
EVIDENCE = REFERENCE_CASES / "e4_pl_q1e_synthesis_evidence.json"
REVIEW = REFERENCE_CASES / "e4_pl_q1e_scientific_review.json"
STATUS = REFERENCE_CASES / "e4_pl_q1e_status.json"
REVIEWED_PATHS = [
    "docs/agent_plans/S4_E4_PL_Q1E_ASSEMBLED_READJUDICATION_PLAN.md",
    "docs/reference_cases/e4_pl_q1e_synthesis_contract.json",
    "docs/reference_cases/e4_pl_q1e_synthesis_evidence.json",
    "docs/reference_cases/e4_pl_q1e_synthesizer.py",
    "tests/test_e4_pl_q1e_assembled_readjudication.py",
]


def _contract() -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    raw = CONTRACT.read_bytes()
    return synthesis.validate_contract(ROOT, CONTRACT, synthesis.sha256(raw))


def test_q1e_complete_authority_hash_dag_and_schemas() -> None:
    raw = CONTRACT.read_bytes()
    contract, inputs = _contract()
    assert raw == synthesis.canonical_bytes(contract)
    assert len(contract["evidence_inputs"]) == 9
    assert len(inputs) == 9
    assert contract["extent"] == {"path_count": 7, "paths": synthesis.EXTENT}
    assert contract["base_nonstage_index"] == synthesis.BASE_NONSTAGE_INDEX
    assert contract["terminals"] == synthesis.TERMINALS
    assert contract["production"] == synthesis.PRODUCTION
    assert contract["q1b_integration"] == "UNAUTHORIZED"
    assert contract["decision_rules"]["domain_coercivity"] == "DOMAIN_WIDE_CERTIFICATE_REQUIRED_FINITE_MESH_SAMPLES_NOT_SUBSTITUTE"


def test_q1e_recomputation_is_complete_deterministic_and_nonmechanical() -> None:
    contract_raw = CONTRACT.read_bytes()
    first = synthesis.synthesize(ROOT, CONTRACT, synthesis.sha256(contract_raw))
    second = synthesis.synthesize(ROOT, CONTRACT, synthesis.sha256(contract_raw))
    evidence_raw, evidence = synthesis.read_json(EVIDENCE)
    assert synthesis.canonical_bytes(first) == synthesis.canonical_bytes(second) == evidence_raw
    assert evidence == first
    assert all(evidence["gates"].values())
    assert evidence["expected_terminal_after_accepted_review"] == "UNCLASSIFIED_E4_PL_Q1E_DOMAIN_COERCIVITY"
    assert evidence["decision"]["historical_q1b_locking_interpretation"] == "SUPERSEDED_IN_Q1E_BY_Q1C_Q1D_BOUNDED_EVIDENCE"
    assert evidence["decision"]["historical_q1b_terminal"] == "NO_GO_E4_PL_Q1B_LOCKING_OR_CATEGORY_DRIFT"
    assert evidence["q1b_integration"] == "UNAUTHORIZED"

    source = (REFERENCE_CASES / "e4_pl_q1e_synthesizer.py").read_text(encoding="utf-8")
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
    allowed = {"__future__", "argparse", "hashlib", "json", "os", "pathlib", "subprocess", "typing"}
    assert imports <= allowed
    assert not any(name.startswith(("numpy", "scipy", "sympy", "mpmath", "e4_pl_")) for name in imports)


def test_q1e_mutations_fail_closed_and_terminal_precedence_is_exact(tmp_path: Path) -> None:
    _, inputs = _contract()
    gates = synthesis.recompute_gates(inputs)
    assert all(gates.values())

    changed = copy.deepcopy(inputs)
    full = next(row for row in changed["Q1D_RESULT"]["common_payload"]["shards"] if row["shard"] == "FULL_BLOCK_LDL")
    full["classification_facts"]["precision_stable"] = False
    changed["Q1D_RESULT"]["common_payload_sha256"] = synthesis.sha256(
        synthesis.canonical_bytes(changed["Q1D_RESULT"]["common_payload"])
    )
    assert synthesis.recompute_gates(changed)["q1d_ultrathin_locking_closed"] is False

    changed = copy.deepcopy(inputs)
    for cycle_role in ("Q1B_CYCLE1", "Q1B_CYCLE2"):
        stability = next(
            row
            for row in changed[cycle_role]["common_payload"]["shards"]
            if row["shard"] == "ASSEMBLED_STABILITY"
        )
        stability["contradictions"] = ["MUTATED_STABILITY"]
        changed[cycle_role]["common_payload_sha256"] = synthesis.sha256(
            synthesis.canonical_bytes(changed[cycle_role]["common_payload"])
        )
    assert synthesis.recompute_gates(changed)["stability_finite_samples_closed"] is False

    assert synthesis.select_terminal(blocked=True, locking=True, solver_equivalence=True, stability_or_nonintrusion=True, domain_unresolved=True) == synthesis.TERMINALS[0]
    assert synthesis.select_terminal(blocked=False, locking=True, solver_equivalence=True, stability_or_nonintrusion=True, domain_unresolved=True) == synthesis.TERMINALS[1]
    assert synthesis.select_terminal(blocked=False, locking=False, solver_equivalence=True, stability_or_nonintrusion=True, domain_unresolved=True) == synthesis.TERMINALS[2]
    assert synthesis.select_terminal(blocked=False, locking=False, solver_equivalence=False, stability_or_nonintrusion=True, domain_unresolved=True) == synthesis.TERMINALS[3]
    assert synthesis.select_terminal(blocked=False, locking=False, solver_equivalence=False, stability_or_nonintrusion=False, domain_unresolved=True) == synthesis.TERMINALS[4]
    assert synthesis.select_terminal(blocked=False, locking=False, solver_equivalence=False, stability_or_nonintrusion=False, domain_unresolved=False) == synthesis.TERMINALS[5]

    duplicate = tmp_path / "duplicate.json"
    duplicate.write_bytes(b'{"schema":"x","schema":"x"}\n')
    with pytest.raises(synthesis.SynthesisError, match="duplicate"):
        synthesis.read_json(duplicate)
    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_bytes(b'{"value":NaN}\n')
    with pytest.raises(synthesis.SynthesisError, match="nonfinite"):
        synthesis.read_json(nonfinite)

    records = synthesis.tracked_index_records(ROOT)
    assert synthesis.index_graph_for_records(records, set(synthesis.EXTENT)) == synthesis.BASE_NONSTAGE_INDEX
    unrelated = b"100644 " + (b"0" * 40) + b" 0\tUNRELATED_ROOT_FILE.txt"
    assert synthesis.index_graph_for_records(records + [unrelated], set(synthesis.EXTENT)) != synthesis.BASE_NONSTAGE_INDEX
    assert synthesis.shallow_fallback_allowed(
        github_actions=True,
        head="HEAD",
        shallow_heads={"HEAD"},
        graph_matches=True,
    )
    assert not synthesis.shallow_fallback_allowed(
        github_actions=True,
        head="HEAD",
        shallow_heads={"HEAD"},
        graph_matches=False,
    )
    assert not synthesis.shallow_fallback_allowed(
        github_actions=False,
        head="HEAD",
        shallow_heads={"HEAD"},
        graph_matches=True,
    )
    assert not synthesis.closed_world_extent_allowed(
        untracked_paths=set(synthesis.AUTHOR_EXTENT) | {"UNRELATED_ROOT_FILE.txt"},
        tracked_q1e_paths=set(),
        dirty_tracked=False,
    )


def test_q1e_exact_research_extent_and_production_boundary() -> None:
    synthesis.validate_repository_boundary(ROOT)
    assert synthesis.tracked_index_graph(ROOT, set(synthesis.EXTENT)) == synthesis.BASE_NONSTAGE_INDEX


def test_q1e_independent_review_and_status_closeout() -> None:
    if not REVIEW.exists():
        assert not STATUS.exists()
        return
    assert STATUS.exists()
    contract, _ = _contract()
    evidence_raw, evidence = synthesis.read_json(EVIDENCE)
    review_raw, _ = synthesis.validate_review(ROOT, contract, REVIEWED_PATHS)
    status_raw, status = synthesis.read_json(STATUS)
    assert status_raw == synthesis.canonical_bytes(status)
    assert set(status) == {
        "candidate_id",
        "contract_sha256",
        "decision",
        "evidence_sha256",
        "production",
        "q1b_integration",
        "q1f_plan_preparation",
        "review_sha256",
        "schema",
        "study_id",
        "terminal",
    }
    assert status["schema"] == synthesis.STATUS_SCHEMA
    assert status["candidate_id"] == synthesis.CANDIDATE_ID and status["study_id"] == synthesis.STUDY_ID
    assert status["contract_sha256"] == synthesis.sha256(CONTRACT.read_bytes())
    assert status["evidence_sha256"] == synthesis.sha256(evidence_raw)
    assert status["review_sha256"] == synthesis.sha256(review_raw)
    assert status["decision"] == evidence["decision"]
    assert status["terminal"] == evidence["expected_terminal_after_accepted_review"]
    assert status["q1f_plan_preparation"] == "AUTHORIZED_SEPARATE_REVIEWED_PLAN_ONLY"
    assert status["q1b_integration"] == "UNAUTHORIZED"
    assert status["production"] == synthesis.PRODUCTION
