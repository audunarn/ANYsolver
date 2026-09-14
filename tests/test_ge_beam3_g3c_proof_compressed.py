"""Inert tests for the proof-compressed G3c completion inventory."""
from copy import deepcopy
from hashlib import sha256
import ast
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts" / "ge_beam3_g3c_proof_compressed.py"
SPEC = importlib.util.spec_from_file_location("g3c_proof_compressed", PATH)
PC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PC)


def test_proof_compressed_inventory_and_order():
    value = PC.validate(PC.manifest())
    body = value["body"]
    assert body["counts"] == {
        "histories": 375, "executed_histories": 25,
        "accepted_events": 3075, "restart_prefixes": 3450,
        "executed_restart_continuations": 120, "assignments": 3825,
    }
    assert len(body["executed_case_ids"]) == 25
    assert len(set(body["executed_case_ids"])) == 25
    assert body["cases"][0]["case_id"] == "J_B2_PAIR::BASE::S0::NONE"
    assert body["cases"][-1]["case_id"] == (
        "J_MULTIFAMILY_LOOP::PROPER_GLOBAL_TRANSFORM::S2::CM3")
    assert body["assignments"][0]["assignment_index"] == 0
    assert body["assignments"][-1]["assignment_index"] == 3824


def test_proof_compressed_truthful_provenance_and_roots():
    body = PC.manifest()["body"]
    executed = set(body["executed_case_ids"])
    assert sum(row["provenance"] == "EXECUTED" for row in body["derivations"]) == 25
    for row in body["derivations"]:
        assert row["root_case_id"] in executed
        if row["provenance"] == "EXECUTED":
            assert row["case_id"] == row["root_case_id"]
            assert row["transforms"] == []
        else:
            assert row["transforms"]


def test_proof_compressed_restarts_are_genuine_bounded_basis():
    plan = PC.restart_plan()
    assert len(plan) == 25
    assert sum(len(row["prefixes"]) for row in plan) == 120
    assert all(row["prefixes"] == list(range(6)) for row in plan[:15])
    assert all(len(row["prefixes"]) == 3 for row in plan[15:])


@pytest.mark.parametrize("mutation", (
    "case", "assignment", "root", "holdout", "provenance", "hash", "count", "type"))
def test_proof_compressed_mutations_rejected(mutation):
    value = deepcopy(PC.manifest())
    if mutation == "case":
        value["body"]["cases"][0]["graph"] = "FOREIGN"
    elif mutation == "assignment":
        value["body"]["assignments"][-1]["assignment_index"] = 0
    elif mutation == "root":
        value["body"]["derivations"][1]["root_case_id"] = value["body"]["executed_case_ids"][-1]
    elif mutation == "holdout":
        value["body"]["derivations"][1]["holdout_case_id"] = "FOREIGN"
    elif mutation == "provenance":
        value["body"]["derivations"][1]["provenance"] = "EXECUTED_BY_ASSERTION"
    elif mutation == "hash":
        value["body"]["prerequisites"][0]["sha256"] = "0" * 64
    elif mutation == "count":
        value["body"]["counts"]["histories"] = 374
    else:
        value["body"]["counts"]["histories"] = 375.0
    value["self_sha256"] = sha256(PC.canonical(value["body"])).hexdigest()
    with pytest.raises(ValueError):
        PC.validate(value)


def test_checker_is_standard_library_only_and_mechanics_independent():
    tree = ast.parse(PATH.read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add((node.module or "").split(".")[0])
    assert imports <= {"hashlib", "json"}
    assert imports.isdisjoint({"anysolver", "numpy", "scipy", "sympy"})


def test_manifest_is_deterministic():
    first = PC.canonical(PC.manifest())
    second = PC.canonical(PC.manifest())
    assert first == second
    assert sha256(first).hexdigest() == sha256(second).hexdigest()


def test_proof_compressed_projection_matches_frozen_source_inventory():
    """Join the independent literals to the original inert authority."""
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    import ge_beam3_g3c_physical_history_owner as source

    original = source.history_matrix()
    assert sha256(PC.canonical(original)).hexdigest() == PC.SOURCE_HISTORY_INVENTORY_SHA256
    projected = [{key: row[key] for key in (
        "case_id", "graph", "variant", "force_scale", "common_motion",
        "accepted_stages")} for row in original]
    independent = [{key: row[key] for key in (
        "case_id", "graph", "variant", "force_scale", "common_motion",
        "accepted_stages")} for row in PC.cases()]
    assert projected == independent

    assignments = source.work_inventory("formal")
    assert sha256(PC.canonical(assignments)).hexdigest() == PC.SOURCE_ASSIGNMENT_INVENTORY_SHA256
    projected_assignments = []
    for index, row in enumerate(assignments):
        projected_assignments.append(dict(
            assignment_index=index, kind=row["kind"],
            case_id=row["case"]["case_id"], prefix=row.get("prefix")))
    assert projected_assignments == PC.assignment_plan()
