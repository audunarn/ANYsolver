"""Inert guards for the frozen G4a heterogeneous-station contract."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "docs/reference_cases/ge_beam3_g4a_station_transaction_contract_v1.json"


def load(raw=None):
    def pairs(rows):
        out = {}
        for key, value in rows:
            if key in out:
                raise ValueError("duplicate key")
            out[key] = value
        return out

    return json.loads(PATH.read_text(encoding="utf-8") if raw is None else raw,
                      object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def validate(value):
    assert value["schema"] == "GE_BEAM3_G4A_STATION_TRANSACTION_CONTRACT_V1"
    assert value["candidate_id"] == "GE_BEAM3_G4A_MIXED_STATION_TRANSACTION_V1"
    fixture = value["fixture"]
    assert fixture["history_multipliers"] == [0.0, 1.0, 0.4, 0.0, -0.8, 0.0]
    assert [row["station_id"] for row in fixture["stations"]] == [
        "ELASTIC_0", "GENERALIZED_0", "FIBRE_0"]
    assert [row["capability"] for row in fixture["stations"]] == [
        "RESULTANT_ONLY_NO_FIBRE_STRESSES", "RESULTANT_ONLY_NO_FIBRE_STRESSES",
        "PHYSICAL_FIBRE_STRESSES_AVAILABLE"]
    assert value["gate_scope"]["closes"] == []
    assert set(value["gate_scope"]["implements_foundation_for"]) == {"S19", "S20", "S24"}
    assert set(("S19", "S20", "S21", "S22", "S23", "S24", "G4")) <= set(
        value["gate_scope"]["leaves_open"])
    assert value["execution"] == {
        "automatic_retry": False, "child_seconds": 600, "inactivity_seconds": 120,
        "max_workers": 1, "memory_gib": 24, "numerical_threads": 1,
        "required_cycles": 2, "wave_seconds": 1800,
    }
    assert len(value["failure_matrix"]) == len(set(value["failure_matrix"])) == 16
    assert value["terminal_precedence"][-1] == "PROVISIONAL_GO_GE_BEAM3_G4A_STATION_TRANSACTION_ONLY"
    assert value["production_restriction"] == "NO_GO_PRODUCTION_RESTRICTION_UNCHANGED"


def test_exact_contract_and_bound_sources():
    value = load(); validate(value)
    for relative, expected in value["bindings"].items():
        raw = (ROOT / relative).read_bytes()
        assert len(raw) == expected["bytes"]
        assert sha256(raw).hexdigest() == expected["sha256"]


@pytest.mark.parametrize("field", ("candidate", "order", "history", "capability", "scope", "limit", "terminal"))
def test_decisive_contract_mutations_rejected(field):
    value = deepcopy(load())
    if field == "candidate": value["candidate_id"] = "FOREIGN"
    elif field == "order": value["fixture"]["stations"].reverse()
    elif field == "history": value["fixture"]["history_multipliers"][-1] = 1.0
    elif field == "capability": value["fixture"]["stations"][0]["capability"] = "PHYSICAL_FIBRE_STRESSES_AVAILABLE"
    elif field == "scope": value["gate_scope"]["closes"] = ["G4"]
    elif field == "limit": value["execution"]["automatic_retry"] = True
    else: value["terminal_precedence"].reverse()
    with pytest.raises(AssertionError):
        validate(value)


def test_duplicate_and_nonfinite_rejected():
    with pytest.raises(ValueError): load('{"a":1,"a":2}')
    with pytest.raises(ValueError): load('{"a":NaN}')
