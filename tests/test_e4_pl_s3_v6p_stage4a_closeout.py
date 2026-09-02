from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "docs/reference_cases"
RESULT = REFERENCE / "e4_pl_s3_v6p_stage4a_result.json"
REVIEW = REFERENCE / "e4_pl_s3_v6p_stage4a_result_review.json"
STATUS = REFERENCE / "e4_pl_s3_v6p_stage4a_status.json"


def _canonical(path: Path):
    raw = path.read_bytes()
    value = json.loads(raw)
    assert raw == (
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    return value


def test_v6p_closeout_is_canonical_deterministic_and_nonactivating() -> None:
    result = _canonical(RESULT)
    review = _canonical(REVIEW)
    status = _canonical(STATUS)
    assert result["record_coverage"] == {
        "diagonal_proofs": 3,
        "optimized": 12,
        "predecessor": 69,
        "sequences": 24,
        "total": 81,
    }
    assert result["determinism"] == {
        "canonical_results_byte_identical": True,
        "canonical_unions_byte_identical": True,
        "checker_replicas_byte_identical_per_diagonal": True,
    }
    assert result["activation_authorized"] is False
    assert result["stage4b_extension_authorized"] is False
    assert review["findings"] == []
    assert status["terminal"] == result["terminal"]


def test_v6p_external_cycles_match_registered_hashes() -> None:
    result = _canonical(RESULT)
    for cycle in result["cycles"]:
        root = Path(cycle["root"])
        for name, key in (
            ("completion-union.json", "completion_union"),
            ("completion-result.json", "completion_result"),
        ):
            raw = (root / name).read_bytes()
            assert len(raw) == cycle[key]["bytes"]
            assert hashlib.sha256(raw).hexdigest().upper() == cycle[key]["sha256"]
    assert result["cycles"][0]["completion_result"] == result["cycles"][1]["completion_result"]
    assert result["cycles"][0]["completion_union"] == result["cycles"][1]["completion_union"]


def test_v6p_no_go_is_scoped_to_registered_25_percent_subgates() -> None:
    result = _canonical(RESULT)
    assert len(result["formal_failures"]) == 9
    assert all(":25:" in failure for failure in result["formal_failures"])
    assert {failure.rsplit(":", 1)[1] for failure in result["formal_failures"]} == {
        "RESPONSE_SLOPE",
        "RESPONSE_SLOPE_DEFICIT",
        "SUCCESSIVE_RESPONSE_ERROR",
    }
