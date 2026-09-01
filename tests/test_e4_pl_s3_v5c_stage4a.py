from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs" / "reference_cases"
CONTRACT = REFERENCE / "e4_pl_s3_v5c_stage4a_contract.json"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


@pytest.fixture(scope="module")
def producer():
    return _load("_v5c_stage4a_producer", REFERENCE / "e4_pl_s3_v5c_stage4a_producer.py")


@pytest.fixture(scope="module")
def checker():
    return _load("_v5c_stage4a_checker", REFERENCE / "e4_pl_s3_v5c_stage4a_checker.py")


@pytest.fixture(scope="module")
def coordinator():
    return _load("_v5c_stage4a_coordinator", REFERENCE / "e4_pl_s3_v5c_stage4a_coordinator.py")


def test_contract_is_canonical_and_binds_exact_authority_extent():
    raw = CONTRACT.read_bytes()
    value = json.loads(raw)
    assert raw == (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    assert value["authority_commit"] == {
        "expected_parent": "db8ac3c3fad705bd781516038c068a5308297a1b",
        "expected_path_set": [
            "docs/agent_plans/S3_E4_PL_V5C_STAGE4A_REAUTHORIZATION_PLAN.md",
            "docs/reference_cases/e4_pl_s3_v5c_stage4a_checker.py",
            "docs/reference_cases/e4_pl_s3_v5c_stage4a_contract.json",
            "docs/reference_cases/e4_pl_s3_v5c_stage4a_coordinator.py",
            "docs/reference_cases/e4_pl_s3_v5c_stage4a_producer.py",
            "tests/test_e4_pl_s3_v5c_stage4a.py",
        ],
        "expected_subject": "docs: reauthorize S3 V5C Stage 4A mixed flexural execution",
    }
    assert value["stage4a_execution_authorized"] is True
    assert value["activation_authorized"] is False


def test_contract_frozen_hash_dag():
    value = json.loads(CONTRACT.read_text(encoding="ascii"))
    for binding in value["frozen_inputs"]:
        raw = (ROOT / binding["path"]).read_bytes()
        assert len(raw) == binding["bytes"]
        assert hashlib.sha256(raw).hexdigest().upper() == binding["sha256"]


def test_exact_81_record_manifest(producer):
    catalog = [spec for diagonal in producer.DIAGONALS for spec in producer._specs(diagonal)]
    assert len(catalog) == 81
    assert len(set(catalog)) == 81
    assert all(len(producer._specs(diagonal)) == 27 for diagonal in producer.DIAGONALS)


def test_independent_record_reconstruction_is_exact(producer, checker):
    made = producer._record(20, 10, "dispersed", "slash")
    independent = checker._record(20, 10, "dispersed", "slash")
    assert checker._record_identity(made, independent) == 0.0
    assert float.fromhex(made["solve_residual_relative_inf_hex"]) <= 1.0e-8


def test_record_mutations_are_detected(producer, checker):
    made = producer._record(20, 10, "dispersed", "slash")
    changed = dict(made)
    changed["response_center_hex"] = (float.fromhex(made["response_center_hex"]) + 1.0e-6).hex()
    assert checker._record_identity(changed, made) > 3.0e-12
    changed = dict(made)
    changed["connectivity_sha256"] = "0" * 64
    with pytest.raises(checker.CheckerError):
        checker._record_identity(changed, made)


def test_terminal_precedence_and_cycle_identity(coordinator):
    assert coordinator.BLOCKED == "BLOCKED_E4_PL_S3_V5C_STAGE4A_PROCESS_OR_EVIDENCE"
    assert coordinator.NO_GO == "NO_GO_E4_PL_S3_V5C_STAGE4A_MIXED_FLEXURAL_CONVERGENCE"
    assert coordinator.PASS == "PROVISIONAL_GO_E4_PL_S3_V5C_STAGE4B_PREPARATION"
    cycle = {
        "formal_failure_count": 0,
        "formal_failures": [],
        "record_count": 81,
        "sequence_count": 24,
        "sequence_results_sha256": "1" * 64,
        "shards": [],
    }
    assert coordinator._cycle_identity(cycle) == cycle


def test_production_boundary_is_unchanged():
    contract = json.loads(CONTRACT.read_text(encoding="ascii"))
    assert contract["production_boundary"] == {
        "activation_authorized": False,
        "anymesh_untouched": True,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
    }
    assert contract["stage4b_preparation_authorized"] is False
