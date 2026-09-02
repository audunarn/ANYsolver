from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs/reference_cases"
RESULT = REFERENCE / "e4_pl_s3_v6w_final_qualification_result.json"
REVIEW = REFERENCE / "e4_pl_s3_v6w_final_qualification_result_review.json"
STATUS = REFERENCE / "e4_pl_s3_v6w_final_qualification_status.json"
GO = "PROVISIONAL_GO_E4_PL_S3_V2D_OPT_IN_QUALIFIED"


def _load(path: Path) -> tuple[bytes, dict[str, object]]:
    raw = path.read_bytes()
    value = json.loads(raw)
    assert isinstance(value, dict)
    assert raw == (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("ascii")
    return raw, value


def test_final_result_review_and_status_are_canonical_and_hash_bound() -> None:
    result_raw, result = _load(RESULT)
    review_raw, review = _load(REVIEW)
    _status_raw, status = _load(STATUS)
    assert len(result_raw) == status["result"]["bytes"]
    assert hashlib.sha256(result_raw).hexdigest().upper() == status["result"]["sha256"]
    assert len(review_raw) == status["review"]["bytes"]
    assert hashlib.sha256(review_raw).hexdigest().upper() == status["review"]["sha256"]
    assert review["findings"] == []
    assert review["reviewed_inputs"]["replica_1_sha256"] == status["result"]["sha256"]
    assert review["reviewed_inputs"]["replica_2_sha256"] == status["result"]["sha256"]


def test_explicit_v2d_selector_is_qualified_but_defaults_are_not_activated() -> None:
    _raw, result = _load(RESULT)
    assert result["terminal"] == GO
    assert result["qualified_selector"] == "e4-pl-s3-v2d"
    assert result["default_activation_authorized"] is False
    assert set(result["checks"].values()) == {True}
    assert result["production_boundary"] == {
        "anymesh_untouched": True,
        "default_q4_formulation": "e4-pl",
        "default_s3_formulation": "legacy-s3",
        "q4_mechanics_unchanged": True,
    }


def test_historical_terminals_are_preserved_by_the_successor_decision() -> None:
    _raw, result = _load(RESULT)
    assert result["historical_disposition"] == {
        "v6p_nogo_preserved": True,
        "v6q_block_preserved": True,
        "v6r_spatial_successor_accepted": True,
        "v6s_nogo_preserved": True,
        "v6t_v6u_performance_successor_accepted": True,
        "v6v_block_preserved": True,
    }
    assert result["next_gate"] == "S3_V2D_ECOSYSTEM_DEFAULT_ACTIVATION_CANDIDATE"
