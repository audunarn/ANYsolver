from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import ast
import copy
from fractions import Fraction
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
sys.path.insert(0, str(REFERENCE_CASES))

import e4_pl_q1v_reference as reference
import e4_pl_q1y_algebra_checker as checker
import e4_pl_q1y_algebra_producer as producer
import e4_pl_q1y_bounded_runner as runner
import e4_pl_q1y_common as common


CONTRACT = REFERENCE_CASES / "e4_pl_q1y_local_algebra_contract.json"
CONTRACT_SHA = common.sha256(CONTRACT.read_bytes())
RESULT = REFERENCE_CASES / "e4_pl_q1y_bounded_result.json"


def test_q1y_contract_exact_backend_and_research_boundary() -> None:
    raw, value = common.read_json(CONTRACT)
    assert raw == common.canonical_bytes(value)
    checked = common.validate_contract(ROOT, CONTRACT, CONTRACT_SHA)
    assert checked["geometry_ids"] == list(common.GEOMETRY_IDS)
    assert checked["operation_ids"] == list(common.OPERATION_IDS)
    assert checked["scope"] == {
        "base_factorizations": 7, "derived_numbering_cases": 56, "global_kkt": False,
        "internal_fields": 38, "physical_dofs": 24, "quotient_dimension": 18,
        "support_solve": False,
    }

    field = reference.Field(())
    field, root2 = field.with_sqrt(field.rational(2))
    radicand = field.rational(3) + root2
    field, nested = field.with_sqrt(radicand)
    root2 = root2.lift(field); radicand = radicand.lift(field)
    x = field.rational(5) + root2 + nested
    y = field.rational(7) - root2 + 2 * nested
    z = field.rational(2) + root2 * nested
    assert root2 * root2 == field.rational(2)
    assert nested * nested == radicand
    assert x * y == y * x
    assert (x * y) * z == x * (y * z)
    assert x * (y + z) == x * y + x * z
    assert x * x.inverse() == field.rational(1) == x.inverse() * x
    assert common.canonical_bytes({"z": 0, "a": [1, 2]}) == b'{"a":[1,2],"z":0}\n'

    checker_tree = ast.parse((REFERENCE_CASES / "e4_pl_q1y_algebra_checker.py").read_text(encoding="utf-8"))
    imports = {
        alias.name for node in ast.walk(checker_tree) if isinstance(node, ast.Import) for alias in node.names
    } | {node.module or "" for node in ast.walk(checker_tree) if isinstance(node, ast.ImportFrom)}
    assert "e4_pl_q1y_algebra_producer" not in imports
    assert not any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {"evalf", "simplify"}
        for node in ast.walk(checker_tree)
    )
    changed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=ROOT,
        text=True, stdout=subprocess.PIPE, check=True,
    ).stdout.splitlines()
    changed_paths = [row[3:].replace("\\", "/") for row in changed]
    assert not any(path == "pyproject.toml" or path == ".gitattributes" or path.startswith(("src/", ".github/")) for path in changed_paths)


def test_q1y_exact_witness_mutations_are_detected() -> None:
    field = reference.Field.for_radicands([Fraction(2)])
    root = field.sqrt(Fraction(2))
    d = [[field.rational(3), root], [root, field.rational(2)]]
    inverse = reference.matrix_inverse(d)
    identity = reference.eye(field, 2)
    assert reference.matmul(d, inverse) == identity == reference.matmul(inverse, d)
    bad_inverse = copy.deepcopy(inverse); bad_inverse[0][0] += field.rational(1)
    assert reference.matmul(d, bad_inverse) != identity

    coupling = [[field.rational(1), root], [field.rational(0), field.rational(1)]]
    stiffness = reference.mscale(reference.matmul(reference.matmul(coupling, inverse), reference.transpose(coupling)), -1)
    bad_stiffness = copy.deepcopy(stiffness); bad_stiffness[0][1] += field.rational(1)
    assert bad_stiffness != stiffness and bad_stiffness != reference.transpose(bad_stiffness)

    rigid = [[field.rational(1)], [field.rational(1)]]
    complement = reference.lexicographic_nullspace(reference.transpose(rigid))
    assert complement == [[field.rational(-1)], [field.rational(1)]]
    rank_one = [[field.rational(1), field.rational(-1)], [field.rational(-1), field.rational(1)]]
    quotient = reference.matmul(reference.matmul(reference.transpose(complement), rank_one), complement)
    lower, pivots = producer._ldl(quotient)
    diagonal = [[pivots[0]]]
    assert quotient == reference.matmul(reference.matmul(lower, diagonal), reference.transpose(lower))
    bad_pivots = [pivots[0] + field.rational(1)]
    assert quotient != reference.matmul(reference.matmul(lower, [[bad_pivots[0]]]), reference.transpose(lower))

    encoded = list(producer.INTERNAL_MAPS["R90"])
    actual = producer._operator_maps(
        type("AssemblyStub", (), {"field": field})(),
        type("OperationStub", (), {"id": "R90", "A": ((0, -1), (1, 0)), "det": 1, "permutation": (1, 2, 3, 0)})(),
    )[0]
    assert reference.matmul(reference.transpose(actual), actual) == reference.eye(field, 38)
    encoded[0] = 0
    assert encoded != list(producer.INTERNAL_MAPS["R90"])
    payload = {"inverse": [[value.token() for value in row] for row in inverse]}
    digest = common.sha256(common.canonical_bytes(payload))
    payload["inverse"][0][0][0] = "99"
    assert common.sha256(common.canonical_bytes(payload)) != digest
def test_q1y_parallel_bounds_and_partial_output_cleanup(tmp_path: Path) -> None:
    environment = os.environ.copy()

    def sleep_job(index: int):
        directory = tmp_path / f"worker-{index}"; directory.mkdir()
        return runner.run_bounded_process(
            [sys.executable, "-c", "import time; time.sleep(0.25)"], cwd=ROOT, environment=environment,
            stdout_path=directory / "stdout.log", stderr_path=directory / "stderr.log",
            timeout_seconds=2, memory_limit_bytes=1024**3, rss_reader=lambda _pid: 1,
        )

    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=3) as pool:
        rows = list(pool.map(sleep_job, range(3)))
    assert time.monotonic() - started < 0.75
    assert all(row.status == "COMPLETE" for row in rows)
    assert all((tmp_path / f"worker-{index}" / "stdout.log").is_file() for index in range(3))
    assert len({(tmp_path / f"worker-{index}").resolve() for index in range(3)}) == 3

    for label, timeout, memory, rss in (("timeout", 0.1, 1024**3, 1), ("memory", 2, 10, 11)):
        directory = tmp_path / label; directory.mkdir(); output = directory / "canonical.json"
        result = runner.run_bounded_process(
            [sys.executable, "-c", f"from pathlib import Path; import time; Path({str(output)!r}).write_text('partial'); time.sleep(2)"],
            cwd=ROOT, environment=environment, stdout_path=directory / "stdout.log", stderr_path=directory / "stderr.log",
            timeout_seconds=timeout, memory_limit_bytes=memory, rss_reader=lambda _pid, value=rss: value,
        )
        runner.discard_incomplete_output(output, result)
        assert result.status == ("TIMEOUT" if label == "timeout" else "MEMORY_LIMIT")
        assert not output.exists()


def test_q1y_terminal_precedence_and_order_are_exact() -> None:
    contract = common.validate_contract(ROOT, CONTRACT, CONTRACT_SHA)
    terminals = contract["terminals"]
    assert runner.select_terminal(blocked=True, local_contradictions=["L"], operator_contradictions=["O"], ordered_unresolved=True, terminals=terminals) == terminals["blocked"]
    assert runner.select_terminal(blocked=False, local_contradictions=["L"], operator_contradictions=["O"], ordered_unresolved=True, terminals=terminals) == terminals["local_algebra"]
    assert runner.select_terminal(blocked=False, local_contradictions=[], operator_contradictions=["O"], ordered_unresolved=True, terminals=terminals) == terminals["operator_covariance"]
    assert runner.select_terminal(blocked=False, local_contradictions=[], operator_contradictions=[], ordered_unresolved=True, terminals=terminals) == terminals["ordered_sign"]
    assert runner.select_terminal(blocked=False, local_contradictions=[], operator_contradictions=[], ordered_unresolved=False, terminals=terminals) == terminals["success"]
    assert [f"{g}::{o}" for g in common.GEOMETRY_IDS for o in common.OPERATION_IDS] == [
        f"{g}::{o}" for g in contract["geometry_ids"] for o in contract["operation_ids"]
    ]


def test_q1y_bounded_outcome_is_fail_closed_and_nonqualifying() -> None:
    raw, result = common.read_json(RESULT)
    assert raw == common.canonical_bytes(result)
    assert result["contract_sha256"] == CONTRACT_SHA
    assert result["terminal"] == "BLOCKED_E4_PL_Q1Y_PROOF_OR_REVIEW"
    assert result["attempt"] == {
        "canonical_aggregate_created": False,
        "checker_process_count": 0,
        "cycle_2_started": False,
        "cycle_id": "Q1Y_CYCLE_1",
        "diagnostic_proof_count_after_ceiling": 7,
        "formal_retry_performed": False,
        "overall_ceiling_seconds": 600,
        "producer_complete_count_at_ceiling": 5,
        "producer_incomplete_at_ceiling": ["Q5_HOSTILE_ASYMMETRIC_2", "Q3_TAPERED_SKEW_RSTAR_TRANSLATED"],
        "reason": "OVERALL_TEN_MINUTE_CEILING_EXCEEDED_BEFORE_PRODUCER_WAVE_COMPLETED",
        "terminal_process_states_complete": True,
    }
    assert result["coverage"] == {
        "canonical_case_count": 0, "canonical_geometry_count": 0, "canonical_station_count": 0,
        "diagnostic_producer_geometry_count": 7, "expected_case_count": 56, "expected_geometry_count": 7,
    }
    assert not result["local_algebra_contradiction_established"]
    assert not result["operator_covariance_contradiction_established"]
    assert result["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert result["q1b_execution"] == "UNAUTHORIZED"
