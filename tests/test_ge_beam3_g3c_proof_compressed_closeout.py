"""Static adjudication guards for the bounded G3c proof-compressed closeout."""
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs/reference_cases/ge_beam3_g3c_proof_compressed_confirmation_v2.json"
REVIEW = ROOT / "docs/reference_cases/ge_beam3_g3c_proof_compressed_confirmation_review_v2.json"
STATUS = ROOT / "docs/reference_cases/ge_beam3_g3c_proof_compressed_status_v2.json"


def _load(path):
    def duplicate(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate key")
            value[key] = item
        return value

    def constant(_):
        raise ValueError("nonfinite value")

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=duplicate,
                      parse_constant=constant)


def _validate(value):
    assert value["schema"] == "GE_BEAM3_G3C_PROOF_COMPRESSED_CONFIRMATION_V2"
    assert value["candidate"] == {
        "commit": "1ebe7ab0ad77c28d01c58423ebb6e7c218042daa",
        "tree": "76538156c6a9cd534fc822d3422321338fe6e096",
    }
    assert value["counts"] == {
        "accepted_events": 3075, "assignments": 3825,
        "executed_histories": 25, "executed_restart_continuations": 120,
        "histories": 375, "restart_prefixes": 3450, "shards_per_cycle": 100,
    }
    assert value["terminal"] == "PROVISIONAL_GO_GE_BEAM3_G3C_COMMON_POSE_ELASTIC_GRAPH_ONLY"
    assert value["production_restriction"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"
    checks = value["checks"]
    assert checks == {
        "active_processes_zero": True, "checker_replicas_byte_identical": True,
        "cycle_science_byte_identical": True,
        "full_assignment_domain_reconstructed": True, "no_automatic_retry": True,
        "production_qualified": False, "registered_elastic_graph_slice_closed": True,
    }
    cycles = value["archive"]
    hashes = [
        cycles[name][field]
        for name in ("cycle_1", "cycle_2")
        for field in ("checker_1_sha256", "checker_2_sha256", "process_sha256",
                      "scientific_sha256", "tree_manifest_sha256")
    ]
    assert all(len(item) == 64 and set(item) <= set("0123456789abcdef")
               for item in hashes)
    assert cycles["cycle_1"]["scientific_sha256"] == cycles["cycle_2"]["scientific_sha256"]
    assert cycles["cycle_1"]["checker_1_sha256"] == cycles["cycle_1"]["checker_2_sha256"]
    assert cycles["cycle_2"]["checker_1_sha256"] == cycles["cycle_2"]["checker_2_sha256"]
    assert cycles["cycle_1"]["files"] == cycles["cycle_2"]["files"] == 1049
    assert all(not isinstance(item, float) or math.isfinite(item)
               for item in _walk(value))


def _walk(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)
    else:
        yield value


def test_closeout_exact_schema_hashes_and_scope():
    value = _load(RECORD)
    _validate(value)
    assert sha256((ROOT / value["plan"]["path"]).read_bytes()).hexdigest() == value["plan"]["sha256"]
    review = value["implementation_review"]
    assert (ROOT / review["path"]).stat().st_size == review["bytes"]
    assert sha256((ROOT / review["path"]).read_bytes()).hexdigest() == review["sha256"]


@pytest.mark.parametrize("field", ("terminal", "science", "count", "scope", "production"))
def test_closeout_decisive_mutations_rejected(field):
    value = deepcopy(_load(RECORD))
    if field == "terminal":
        value["terminal"] = "PROVISIONAL_GO_GE_BEAM3_STRAIGHT_STANDALONE_OPT_IN"
    elif field == "science":
        value["archive"]["cycle_2"]["scientific_sha256"] = "0" * 64
    elif field == "count":
        value["counts"]["assignments"] = 3824
    elif field == "scope":
        value["checks"]["registered_elastic_graph_slice_closed"] = False
    else:
        value["checks"]["production_qualified"] = True
    with pytest.raises(AssertionError):
        _validate(value)


def test_review_and_status_keep_later_gates_open():
    review = _load(REVIEW)
    status = _load(STATUS)
    assert review["findings"] == []
    assert review["reviewer"]["independent"] is True
    assert review["scope"]["production_qualified"] is False
    assert status["confirmation_sha256"] == sha256(RECORD.read_bytes()).hexdigest()
    assert status["review_sha256"] == sha256(REVIEW.read_bytes()).hexdigest()
    assert status["next_gate"] == "G4_S19_S24_MATERIAL_AND_STATE_OWNERSHIP"
    assert status["production_qualified"] is False
    assert "G4_S19_S24" in status["open_obligations"]


def test_parser_rejects_duplicate_and_nonfinite_json(tmp_path):
    duplicate = tmp_path / "duplicate.json"
    duplicate.write_text('{"a":1,"a":2}', encoding="utf-8")
    nonfinite = tmp_path / "nonfinite.json"
    nonfinite.write_text('{"a":NaN}', encoding="utf-8")
    with pytest.raises(ValueError):
        _load(duplicate)
    with pytest.raises(ValueError):
        _load(nonfinite)
