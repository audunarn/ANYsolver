"""Static G7 closeout and terminal-precedence checks."""
from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "docs/reference_cases"


def _load(name: str):
    raw = (RECORDS / name).read_bytes()
    seen = []

    def pairs(rows):
        value = {}
        for key, item in rows:
            assert key not in value
            value[key] = item
        seen.append(value)
        return value

    value = json.loads(raw.decode("ascii"), object_pairs_hook=pairs,
                       parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    assert raw == (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode("ascii")
    return raw, value


def test_confirmation_and_five_key_review_are_canonical_and_bound():
    raw, confirmation = _load("b3_ge_g7_confirmation_v1.json")
    _, review = _load("b3_ge_g7_review_v1.json")
    _, status = _load("b3_ge_g7_status_v1.json")
    assert set(review) == {"findings", "reviewer_role", "schema", "subject", "verdict"}
    assert review["findings"] == []
    assert review["subject"]["confirmation_sha256"] == sha256(raw).hexdigest()
    assert confirmation["terminal"] == "PROVISIONAL_GO_B3_GE_PRODUCTION_OPT_IN"
    assert confirmation["archive"]["formal_cycle_1"] == confirmation["archive"]["formal_cycle_2"]
    assert all(confirmation["checks"].values())
    assert confirmation["production_opt_in_qualified"] is True
    assert confirmation["production_default_changed"] is False
    assert status["default_beam"] == "LEGACY_B3"
    assert status["public_default_routing_authorized"] is False


def test_contract_terminal_precedence_and_g6_binding():
    _, contract = _load("b3_ge_g7_contract_v1.json")
    g6 = (RECORDS / "ge_beam3_g6_confirmation_v4.json").read_bytes()
    assert sha256(g6).hexdigest() == contract["g6_confirmation_file_sha256"]
    assert contract["terminal_precedence"] == [
        "BLOCKED_B3_GE_G7_AUTHORITY_OR_EVIDENCE",
        "NO_GO_B3_GE_G7_IDENTITY_OR_PACKAGE",
        "NO_GO_B3_GE_G7_CONSUMER_OR_MIGRATION",
        "PROVISIONAL_GO_B3_GE_PRODUCTION_OPT_IN",
    ]
    assert contract["legacy_b3_default"] is True
    assert contract["default_changed"] is False
