from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs" / "reference_cases"
AUTHORITY = REFERENCE / "e4_pl_s3_v6o_stage4a_authority.py"
GRAPH = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\s3-v2d-stage4a-v6o-missing-leaves-fb7d1fe\execution-graph.json"
)
CANDIDATE = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\s3-v2d-stage4a-v6n-lease-optimization-c1e2ad9\candidate-source.tar"
)
QUALIFICATION = Path(
    r"C:\Users\AudunArnesenNyhus\AppData\Local\ANYrelease\s3-v2d-stage4a-v6o-missing-leaves-fb7d1fe"
)
REQUESTS = Path(r"C:\Github\.resource-manager\requests")
AUTHORIZATION = REFERENCE / "e4_pl_s3_v6o_stage4a_execution_authorization.json"


def _load():
    spec = importlib.util.spec_from_file_location("_s3_v6o_authority_test", AUTHORITY)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v6o_authority_is_deterministic_fresh_and_four_wave_only() -> None:
    module = _load()
    first = module.generate(GRAPH, CANDIDATE, QUALIFICATION, AUTHORIZATION, REQUESTS)
    second = module.generate(GRAPH, CANDIDATE, QUALIFICATION, AUTHORIZATION, REQUESTS)
    assert module.canonical_bytes(first) == module.canonical_bytes(second)
    assert first["activation_authorized"] is False
    assert first["stage4a_execution_authorized"] is True
    assert len(first["requests"]) == 4
    ids = [row["request"]["request_id"] for row in first["requests"]]
    assert len(set(ids)) == 4
    ledger = Path(r"C:\Github\.resource-manager\ledger.md").read_text(
        encoding="utf-8-sig"
    )
    completed = (REFERENCE / "e4_pl_s3_v6p_stage4a_result.json").is_file()
    for index, (request_id, row) in enumerate(zip(ids, first["requests"])):
        assert request_id == module.request_id(index)
        request_path = REQUESTS / f"{request_id}.json"
        if completed:
            raw_request = request_path.read_bytes()
            assert hashlib.sha256(raw_request).hexdigest().upper() == row["request_sha256"]
            assert ledger.count(f"| {request_id} | APPROVED |") == 1
            assert ledger.count(f"| {request_id} | EXECUTION_STARTED |") == 1
            assert ledger.count(f"| {request_id} | COMPLETED_PASS |") == 1
            assert f"| {request_id} | COMPLETED_FAIL |" not in ledger
        else:
            assert request_id not in ledger
            assert not request_path.exists()
        assert row["request"]["status"] == "PENDING"
        assert "--run-registered-wave" in row["request"]["command"]


def test_v6o_review_is_canonical_five_key_and_empty() -> None:
    path = REFERENCE / "e4_pl_s3_v6o_stage4a_request_review.json"
    raw = path.read_bytes()
    value = json.loads(raw)
    assert raw == (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    assert set(value) == {
        "findings",
        "reviewed_inputs",
        "reviewer_independence",
        "schema",
        "verdict",
    }
    assert value["findings"] == []
    assert value["verdict"].endswith("NO_P0_P1")


def test_v6o_authority_mutation_changes_canonical_bytes() -> None:
    module = _load()
    authority = module.generate(GRAPH, CANDIDATE, QUALIFICATION, AUTHORIZATION, REQUESTS)
    changed = copy.deepcopy(authority)
    changed["requests"][0]["request"]["estimate_minutes"] = 31
    assert module.canonical_bytes(changed) != module.canonical_bytes(authority)
    with pytest.raises(module.V6OAuthorityError):
        module.canonical_bytes({"bad": float("nan")})
