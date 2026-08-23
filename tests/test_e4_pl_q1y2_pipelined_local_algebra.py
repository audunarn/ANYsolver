from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import ast
import copy
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys
import threading
import time


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
sys.path.insert(0, str(REFERENCE_CASES))

import e4_pl_q1v_reference as reference
import e4_pl_q1y2_bounded_runner as runner
import e4_pl_q1y_algebra_producer as producer
import e4_pl_q1y_common as common


CONTRACT = REFERENCE_CASES / "e4_pl_q1y2_local_algebra_contract.json"
CONTRACT_SHA = common.sha256(CONTRACT.read_bytes())
RESULT = REFERENCE_CASES / "e4_pl_q1y2_bounded_result.json"


def test_q1y2_contract_inputs_and_research_boundary_are_exact() -> None:
    raw, value = common.read_json(CONTRACT)
    assert raw == common.canonical_bytes(value)
    checked = runner.validate_successor_contract(ROOT, CONTRACT, CONTRACT_SHA)
    assert checked["base_commit"] == "38cdb7ad5c240b43d6f478cb10631820f3ee9b0c"
    assert checked["coverage"] == {
        "base_factorizations": 7,
        "derived_numbering_cases": 56,
        "internal_fields": 38,
        "physical_dofs": 24,
        "quotient_dimension": 18,
        "rigid_modes": 6,
    }
    assert len(checked["diagnostic_proofs"]) == 7
    assert all(row["classification"] == "NONCANONICAL_SCHEDULING_DIAGNOSTIC_ONLY" for row in checked["diagnostic_proofs"])
    changed = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=ROOT, text=True, stdout=subprocess.PIPE, check=True,
    ).stdout.splitlines()
    changed_paths = [row[3:].replace("\\", "/") for row in changed]
    assert not any(
        path == "pyproject.toml" or path == ".gitattributes" or path.startswith(("src/", ".github/"))
        for path in changed_paths
    )


def test_q1y2_checker_reconstructs_base_once_and_never_imports_producer() -> None:
    path = REFERENCE_CASES / "e4_pl_q1y2_algebra_checker.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    } | {
        node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
    }
    assert "e4_pl_q1y_algebra_producer" not in imports
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"evalf", "simplify"}
        for node in ast.walk(tree)
    )
    block_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "prior"
        and node.func.attr == "_blocks"
    ]
    assert len(block_calls) == 1
    assert "NO_NUMBERED_STATIONARY_REASSEMBLY" in json.loads(CONTRACT.read_bytes())["checker"]["numbered_operator_policy"]


def test_q1y2_exact_witness_mutations_and_serialization() -> None:
    field = reference.Field.for_radicands([Fraction(2)])
    root = field.sqrt(Fraction(2))
    d38 = [[field.rational(3), root], [root, field.rational(2)]]
    inverse = reference.matrix_inverse(d38)
    identity = reference.eye(field, 2)
    assert reference.matmul(d38, inverse) == identity == reference.matmul(inverse, d38)
    bad_inverse = copy.deepcopy(inverse)
    bad_inverse[0][0] += field.rational(1)
    assert reference.matmul(d38, bad_inverse) != identity
    rigid = [[field.rational(1)], [field.rational(1)]]
    complement = reference.lexicographic_nullspace(reference.transpose(rigid))
    quotient = reference.matmul(
        reference.matmul(reference.transpose(complement), [[field.rational(1), field.rational(-1)], [field.rational(-1), field.rational(1)]]),
        complement,
    )
    lower, pivots = producer._ldl(quotient)
    assert quotient == reference.matmul(reference.matmul(lower, [[pivots[0]]]), reference.transpose(lower))
    assert quotient != reference.matmul(
        reference.matmul(lower, [[pivots[0] + field.rational(1)]]), reference.transpose(lower)
    )
    payload = {"z": 0, "a": [1, 2]}
    assert common.canonical_bytes(payload) == b'{"a":[1,2],"z":0}\n'
    digest = common.sha256(common.canonical_bytes(payload))
    payload["a"][0] = 9
    assert common.sha256(common.canonical_bytes(payload)) != digest


def test_q1y2_weighted_admission_preserves_replica_pairs_and_96_gib_limit() -> None:
    admission = runner.WeightedAdmission(8)
    lock = threading.Lock()
    active = 0
    maximum = 0
    pair_intervals: list[tuple[float, float]] = []

    def job(weight: int, delay: float) -> None:
        nonlocal active, maximum
        with admission.hold(weight):
            started = time.monotonic()
            with lock:
                active += weight
                maximum = max(maximum, active)
            time.sleep(delay)
            with lock:
                active -= weight
            if weight == 2:
                pair_intervals.append((started, time.monotonic()))

    with ThreadPoolExecutor(max_workers=9) as pool:
        futures = [pool.submit(job, 1, 0.12) for _ in range(7)]
        futures.extend(pool.submit(job, 2, 0.04) for _ in range(2))
        for future in futures:
            future.result()
    assert maximum <= 8
    assert len(pair_intervals) == 2
    assert all(end > start for start, end in pair_intervals)


def test_q1y2_terminal_precedence_and_controls_are_fail_closed() -> None:
    contract = runner.validate_successor_contract(ROOT, CONTRACT, CONTRACT_SHA)
    assert runner.select_terminal(contract, blocked=True, local=True, covariance=True, unresolved=True) == contract["terminals"]["blocked"]
    assert runner.select_terminal(contract, blocked=False, local=True, covariance=True, unresolved=True) == contract["terminals"]["local_algebra"]
    assert runner.select_terminal(contract, blocked=False, local=False, covariance=True, unresolved=True) == contract["terminals"]["operator_covariance"]
    assert runner.select_terminal(contract, blocked=False, local=False, covariance=False, unresolved=True) == contract["terminals"]["ordered_sign"]
    assert runner.select_terminal(contract, blocked=False, local=False, covariance=False, unresolved=False) == contract["terminals"]["success"]
    assert contract["parallelism"] == {
        "checker_workers": 4,
        "global_timeout_seconds": 600,
        "memory_admission_gib": 96,
        "memory_limit_gib_per_process": 12,
        "numerical_threads_per_process": 1,
        "producer_workers": 7,
        "replicas_per_geometry": 2,
        "weighted_process_slots": 8,
    }
    raw, result = common.read_json(RESULT)
    assert raw == common.canonical_bytes(result)
    assert result["contract_sha256"] == CONTRACT_SHA
    assert result["terminal"] == contract["terminals"]["blocked"]
    assert len(result["shards"]) == 7
    assert sum(row["case_count"] for row in result["shards"]) == 56
    assert all(row["producer_status"] == "COMPLETE" for row in result["shards"])
    assert all(row["checker_statuses"] == ["COMPLETE", "COMPLETE"] for row in result["shards"])
    assert all(row["checker_byte_identical"] for row in result["shards"])
    assert [row["geometry_id"] for row in result["shards"] if row["proof_disagreement"]] == [
        "Q2_TRAPEZOID",
        "Q3_TAPERED_SKEW",
        "Q5_HOSTILE_ASYMMETRIC_2",
        "Q3_TAPERED_SKEW_RSTAR_TRANSLATED",
    ]
    assert result["q3_proper_global_local_identity"]
    assert not result["local_algebra_contradiction"]
    assert not result["operator_covariance_contradiction"]
    assert result["production"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    assert result["q1b_execution"] == "UNAUTHORIZED"
