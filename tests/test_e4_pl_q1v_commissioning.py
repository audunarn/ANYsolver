from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_CASES = ROOT / "docs" / "reference_cases"
RUNNER_PATH = REFERENCE_CASES / "e4_pl_q1v_commissioning_runner.py"
CONTRACT_PATH = REFERENCE_CASES / "e4_pl_q1v_commissioning_contract.json"


def _load_runner():
    sys.path.insert(0, str(REFERENCE_CASES))
    try:
        spec = importlib.util.spec_from_file_location("q1v_commissioning_runner_test", RUNNER_PATH)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(REFERENCE_CASES))


def _record(module, implementation: str) -> dict[str, object]:
    profile = module.IMPLEMENTATIONS[implementation]
    case_records = [
        {
            "case_id": case_id,
            "construction_completed": True,
            "dimensions": copy.deepcopy(module.CASE_DIMENSIONS),
            "exception_status": "NONE",
            "schema_valid": True,
        }
        for case_id in module.CASE_IDS
    ]
    result: dict[str, object] = {
        "candidate_id": module.CANDIDATE_ID,
        "case_records": case_records,
        "centre_ids": list(module.CENTRE_IDS),
        "construction_completed": True,
        "determinism_payload_sha256": "",
        "dimensions": copy.deepcopy(module.TOP_DIMENSIONS),
        "exception_status": "NONE",
        "implementation_id": profile["implementation_id"],
        "record_kind": module.RECORD_KIND,
        "schema": profile["schema"],
        "schema_valid": True,
        "station_ids": list(module.STATION_IDS),
        "study_id": module.STUDY_ID,
    }
    result["determinism_payload_sha256"] = module._payload_sha256(result)
    return result


def test_q1v_nonclassifying_commissioning_all_56_cases_224_stations_deterministic():
    module = _load_runner()
    contract = json.loads(CONTRACT_PATH.read_bytes())
    reference = _record(module, "reference")
    oracle = _record(module, "oracle")

    assert len(module.CASE_IDS) == 56
    assert len(module.STATION_IDS) == 224
    assert len(module.CENTRE_IDS) == 56
    assert module.CASE_IDS[0] == "Q0_SQUARE::E"
    assert module.CASE_IDS[-1] == "Q3_TAPERED_SKEW_RSTAR_TRANSLATED::MA"
    assert module.STATION_IDS[:4] == (
        "Q0_SQUARE::E::GP_MM",
        "Q0_SQUARE::E::GP_PM",
        "Q0_SQUARE::E::GP_PP",
        "Q0_SQUARE::E::GP_MP",
    )
    assert module.CENTRE_IDS[0] == "Q0_SQUARE::E::CENTRE"

    assert module.validate_implementation_record(reference, contract, "reference") is reference
    assert module.validate_implementation_record(oracle, contract, "oracle") is oracle
    reference_raw = module.canonical_bytes(reference)
    assert reference_raw == module.canonical_bytes(copy.deepcopy(reference))
    assert module.validate_implementation_bytes(reference_raw, contract, "reference") == reference

    agreement = module.build_agreement(reference, oracle)
    assert set(agreement) == module.AGREEMENT_KEYS
    assert agreement["exception_status"] == "NONE"
    assert agreement["record_kind"] == "NONCLASSIFYING_IMPLEMENTATION_COMMISSIONING"
    assert agreement["reference_construction_sha256"] == agreement["oracle_construction_sha256"]

    forbidden = contract["forbidden_content"]
    for token in forbidden:
        assert module.recursive_forbidden_matches({"outer": [{"value": token}]}, forbidden)
    assert module.recursive_forbidden_matches({"outer": {"strain_energy": 0}}, forbidden)
    assert module.recursive_forbidden_matches({"outer": ["STIFFNESS_SIGN"]}, forbidden)
    assert not module.recursive_forbidden_matches(reference, forbidden)

    hostile_key = copy.deepcopy(reference)
    hostile_key["case_records"][0]["energy"] = 0
    with pytest.raises(module.CommissioningError, match="forbidden"):
        module.validate_implementation_record(hostile_key, contract, "reference")

    hostile_value = copy.deepcopy(reference)
    hostile_value["case_records"][0]["exception_status"] = "STIFFNESS_SIGN"
    with pytest.raises(module.CommissioningError, match="forbidden"):
        module.validate_implementation_record(hostile_value, contract, "reference")

    wrong_order = copy.deepcopy(reference)
    wrong_order["station_ids"][0], wrong_order["station_ids"][1] = (
        wrong_order["station_ids"][1],
        wrong_order["station_ids"][0],
    )
    wrong_order["determinism_payload_sha256"] = module._payload_sha256(wrong_order)
    with pytest.raises(module.CommissioningError, match="station-ID order"):
        module.validate_implementation_record(wrong_order, contract, "reference")

    wrong_hash = copy.deepcopy(reference)
    wrong_hash["determinism_payload_sha256"] = "0" * 64
    with pytest.raises(module.CommissioningError, match="payload hash"):
        module.validate_implementation_record(wrong_hash, contract, "reference")
